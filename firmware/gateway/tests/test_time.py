"""Zeitdienst ohne RTC (D-028) und ohne NTP (REQ-GW-09, docs/reviews/phase5_gateway_zeit.md): Browserzeit,
Plausibilität, Bindung an die monotone Uhr, gemeinsame Zeitbasis wall(), Raumklima vor dem Zeitabgleich (V-3),
Rückrechnung auch bei weit zurückliegender Systemuhr (V-4)."""
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from fluidi_gw import climate, model, store, timesvc, timesync

T_OK = 1793000000.0      # 2026-10-26 (innerhalb der Plausibilitätsgrenzen)


class BrowserTime(unittest.TestCase):
    def setUp(self):
        self._prev = timesvc._ACTIVE
        self.ts = timesvc.TimeService("invalid")

    def tearDown(self):
        timesvc._ACTIVE = self._prev

    def test_invalid_without_source(self):
        self.assertFalse(self.ts.valid)
        self.assertEqual(self.ts.source, "none")

    def test_implausible_rejected(self):
        for t in (0, 946684800, timesvc.PLAUSIBLE_MIN - 1, timesvc.PLAUSIBLE_MAX, float("nan")):
            self.assertFalse(self.ts.set_browser_time(t), t)
        self.assertFalse(self.ts.valid)

    def test_accepted_when_invalid_not_when_valid(self):
        self.assertTrue(self.ts.set_browser_time(T_OK))
        self.assertEqual((self.ts.valid, self.ts.source), (True, "browser"))
        self.assertAlmostEqual(self.ts.now(), T_OK, delta=1)
        self.assertFalse(self.ts.set_browser_time(T_OK + 3600))          # schon gültig: ohne force nicht
        self.assertAlmostEqual(self.ts.now(), T_OK, delta=1)
        self.assertTrue(self.ts.set_browser_time(T_OK + 3600, force=True))
        self.assertAlmostEqual(self.ts.now(), T_OK + 3600, delta=1)

    def test_anchor_survives_system_clock_jump(self):
        """Systemuhr springt (z. B. NTP kommt nach, Zeit aus timesyncd-Datei): Browserzeit läuft monoton weiter."""
        self.ts.set_browser_time(T_OK)
        real = time.time()
        with mock.patch.object(timesvc.time, "time", return_value=real + 5 * 86400):
            self.assertAlmostEqual(self.ts.now(), T_OK, delta=1)

    def test_wall_and_model_now_use_active_service(self):
        self.ts.set_browser_time(T_OK)
        self.assertAlmostEqual(timesvc.wall(), T_OK, delta=1)
        self.assertAlmostEqual(model.now(), T_OK, delta=1)

    def test_ntp_takes_over(self):
        ts = timesvc.TimeService("system", activate=False)
        with mock.patch.object(timesvc.TimeService, "_ntp_synced", return_value=False):
            ts.refresh(force=True)
            self.assertFalse(ts.valid)
            ts.set_browser_time(T_OK)
            ts.refresh(force=True)
            self.assertEqual(ts.source, "browser")               # ohne NTP bleibt die Browserzeit
        with mock.patch.object(timesvc.TimeService, "_ntp_synced", return_value=True):
            ts.refresh(force=True)
        self.assertEqual((ts.valid, ts.source), (True, "ntp"))
        self.assertAlmostEqual(ts.now(), time.time(), delta=1)


class NoRtc(unittest.TestCase):
    """D-028: Es gibt keine RTC-Quelle mehr; die nach dem Start gesetzte Systemuhr allein gilt nie als gültig."""

    def test_status_without_rtc(self):
        ts = timesvc.TimeService("system", activate=False)
        with mock.patch.object(timesvc.TimeService, "_ntp_synced", return_value=False):
            ts.refresh(force=True)
        st = ts.status("Europe/Zurich")
        self.assertNotIn("rtc_ok", st)
        self.assertEqual((st["valid"], st["source"]), (False, "none"))

    def test_valid_helper(self):
        prev = timesvc._ACTIVE
        try:
            timesvc._ACTIVE = None
            self.assertTrue(timesvc.valid())
            ts = timesvc.TimeService("invalid")
            self.assertFalse(timesvc.valid())
            ts.set_browser_time(T_OK)
            self.assertTrue(timesvc.valid())
        finally:
            timesvc._ACTIVE = prev


class FakeStore:
    def __init__(self):
        self.rows = []

    def insert_climate(self, rows):
        self.rows += rows


class ClimateBeforeTimeSync(unittest.TestCase):
    """Z-7/V-3: Klimawerte vor dem Zeitabgleich nicht mit falscher Systemzeit speichern."""

    def setUp(self):
        self._prev = timesvc._ACTIVE
        self.ts = timesvc.TimeService("invalid")
        self.st = FakeStore()
        self.logs = []
        self.c = climate.Climate(self.st, "sim", log=lambda *a: self.logs.append(a))

    def tearDown(self):
        timesvc._ACTIVE = self._prev

    def test_held_until_valid_then_retimed(self):
        mono0 = time.monotonic()
        with mock.patch.object(climate.time, "monotonic", side_effect=[mono0, mono0 + 300]):
            self.c.sample()
            self.c.sample()
        self.c.flush()
        self.assertEqual(self.st.rows, [])                 # ohne gültige Zeit nichts gespeichert
        self.assertEqual(len(self.c.buf), 2)
        self.assertEqual(self.c.pending_rows(), [])        # API zeigt sie auch nicht mit falscher Zeit
        self.ts.set_browser_time(T_OK)
        with mock.patch.object(climate.time, "monotonic", return_value=mono0 + 600):   # gleiche Uhr wie timesvc
            wall = timesvc.wall()
            self.c.flush()
        ts = [r[0] for r in self.st.rows]
        self.assertEqual(len(ts), 2)
        self.assertAlmostEqual(ts[0], wall - 600, delta=2)
        self.assertAlmostEqual(ts[1], wall - 300, delta=2)
        self.assertGreater(ts[0], T_OK - 3600)             # Zeitbasis Browserzeit, nicht die (falsche) Systemuhr
        self.assertEqual(self.c.buf, [])

    def test_valid_time_stored_directly(self):
        self.ts.set_browser_time(T_OK)
        self.c.sample()
        self.c.flush()
        self.assertEqual(len(self.st.rows), 1)
        self.assertAlmostEqual(self.st.rows[0][0], T_OK, delta=2)

    def test_stop_without_time_drops_and_logs(self):
        self.c.sample()
        self.c.stop()
        self.assertEqual(self.st.rows, [])
        self.assertTrue(any(a[1] == "climate_time" for a in self.logs))

    def test_bounded(self):
        with mock.patch.object(climate, "MAX_PENDING", 3):
            for _ in range(5):
                self.c.sample()
            self.c.flush()
        self.assertEqual(len(self.c.buf), 3)
        self.assertEqual(self.c.dropped, 2)


class RetimeOldRx(unittest.TestCase):
    """Z-8/V-4: Werte mit Flag „Zeit unsicher“ werden auch dann zurückgerechnet, wenn die Systemuhr beim Empfang
    mehr als 90 Tage zurücklag (keine RTC, fehlende Clock-Datei)."""

    def test_found_by_boot_id(self):
        prev = timesvc._ACTIVE
        timesvc._ACTIVE = None
        try:
            st = store.Store(Path(tempfile.mkdtemp(prefix="fluidi-st-")) / "t.sqlite")
            row = {"seq": 1, "t": 0, "raw": 1500, "flags": timesync.FLAG_RECONSTRUCTED | timesync.FLAG_UNSYNCED,
                   "boot_id": 7, "uptime": 900}
            with mock.patch.object(store.timesvc, "wall", return_value=T_OK - 200 * 86400):   # rx weit zurück
                st.insert_readings("AA", [row])
            since = T_OK - 90 * 86400
            self.assertEqual(st.uncertain_readings("AA", since), [])           # noch kein gültiger Synchronpunkt
            st.add_syncpoint("AA", 7, 5000.0, T_OK, True)
            self.assertEqual([r["seq"] for r in st.uncertain_readings("AA", since)], [1])
            st.add_syncpoint("AA", 8, 10.0, T_OK, True)                        # andere boot_id: kein Einfluss
            st.close()
        finally:
            timesvc._ACTIVE = prev


class AfterPowerLoss(unittest.TestCase):
    """Stromausfall ohne NTP: Werte mit ungültiger Gateway-Zeit werden nach dem ersten gültigen Synchronpunkt
    derselben boot_id korrekt zurückgerechnet (Sensor-Laufzeit ist die Zeitbasis, PROTOCOL 7)."""

    def test_retime_after_browser_time(self):
        wrong = T_OK - 3 * 86400          # Systemuhr nach Neustart (z. B. Stand vor dem Ausfall)
        pts = [timesync.SyncPoint(7, 1000.0, wrong, False)]
        t, fl = timesync.reconstruct(7, 900.0, pts, wrong, gw_time_valid=False)
        self.assertTrue(fl & timesync.FLAG_UNSYNCED)
        pts.append(timesync.SyncPoint(7, 5000.0, T_OK, True))     # Browserzeit übernommen, nächste Sitzung
        t, fl = timesync.reconstruct(7, 900.0, pts, T_OK, gw_time_valid=True)
        self.assertAlmostEqual(t, T_OK - 4100.0, delta=0.5)
        self.assertFalse(fl & timesync.FLAG_UNSYNCED)


if __name__ == "__main__":
    unittest.main()
