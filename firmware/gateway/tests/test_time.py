"""Zeitdienst ohne RTC/NTP (REQ-GW-09, docs/reviews/phase5_gateway_zeit.md): Browserzeit, Plausibilität,
Bindung an die monotone Uhr, gemeinsame Zeitbasis wall()."""
import time
import unittest
from unittest import mock

from fluidi_gw import model, timesvc, timesync

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
