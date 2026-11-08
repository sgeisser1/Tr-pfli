"""Gateway <-> simulierter Sensor über das echte Protokoll: Kopplung, Nachlieferung, Duplikate, Zeitsprünge,
unbekannte Sensoren, Befehle, OTA (PROTOCOL Kap. 4, 6, 7, 9; ARCHITECTURE Kap. 4 Fehlerfälle)."""
import struct
import time
import unittest

from helpers import make_gateway, wait
from fluidi_gw import crypto, mcuboot
from fluidi_gw import protocol as P
from fluidi_gw.simsensor import SimSensor


def readings(gw, addr):
    return gw.store.q("SELECT seq, t, flags FROM reading WHERE sensor=? ORDER BY seq", (addr,))


class Pairing(unittest.TestCase):
    def setUp(self):
        self.gw, _ = make_gateway(sensors=0, http=False)
        self.s = self.gw.radio.add(SimSensor("80:6F:B0:12:AB:CD", speed=0.0005, auto_confirm=False))
        self.s.start_later = None
        self.gw.central.call(self.s.start)

    def tearDown(self):
        self.gw.stop()

    def _pair(self, match=True, press=True):
        M, c = self.gw.model, self.gw.central
        M.pairing.update(active=True, until=time.time() + 60, candidates={})
        self.s.press_button_long()
        self.assertTrue(wait(lambda: M.pairing_out()["candidates"]), "Kandidat erscheint")
        j = M.new_job("pair", self.s.name, None, 60)
        c.pair(self.s.addr, j, {"plant": {"name": "Test", "substrate": "erde"}})
        self.assertTrue(wait(lambda: j["state"] == "awaiting_confirmation"))
        # PWA zeigt dieselbe Farbfolge wie die LED des Sensors (SAS)
        self.assertEqual(j["result"]["sas_codes"], self.s.pair["sas"] if self.s.pair else None)
        if press:
            c.call(self.s.press_short)
        c.confirm_pair(self.s.addr, match)
        wait(lambda: j["state"] in ("done", "failed"))
        return j

    def test_pair_ok_and_key_stored(self):
        j = self._pair()
        self.assertEqual(j["state"], "done", j["message"])
        self.assertEqual(self.gw.store.sensor_key(self.s.addr), self.s.k_link)
        self.assertEqual(self.s.gateway_id, self.gw.model.gateway_id)

    def test_user_rejects_colors(self):
        j = self._pair(match=False)
        self.assertEqual(j["state"], "failed")
        self.assertIsNone(self.gw.store.sensor_key(self.s.addr))
        self.assertIsNone(self.s.k_link)

    def test_unknown_sensor_ignored(self):
        """Fremder Sensor ausserhalb des Kopplungsfensters: kein Verbindungsaufbau, keine Speicherung."""
        other = self.gw.radio.add(SimSensor("11:22:33:44:55:66", speed=0.0005))
        other.k_link, other.gateway_id = bytes(16), bytes(8)   # mit anderem Gateway gekoppelt
        other.measure()
        self.gw.central.call(other.start)
        time.sleep(0.5)
        self.assertEqual(other.links, set())
        self.assertEqual(self.gw.store.count_readings()["n"], 0)
        self.assertEqual(self.gw.model.pairing_out()["candidates"], [])


class SensorRules(unittest.TestCase):
    """Sensorseitige v2-Regeln der Simulation direkt geprüft (Commitment, Fristen ohne Fehlversuch)."""

    def run_async(self, coro):
        import asyncio
        return asyncio.run(coro)

    def test_commitment_violation_counts_as_failure(self):
        from fluidi_gw.transport import SimLink

        async def go():
            s = SimSensor("80:6F:B0:12:AB:CD", auto_confirm=False)
            s.press_button_long()
            link = SimLink(s)
            s.on_connect(link)
            g = crypto.EcdhKey()
            req = P.PairReq.make(bytes(8), g.public_raw, bytes([1] * 16))
            await s.on_write(link, P.pair_frame(P.PAIR_REQ, req.payload()))
            await s.on_write(link, P.pair_frame(P.PAIR_REVEAL, bytes([2] * 16)))   # passt nicht zum Commitment
            frames = []
            while not link.rxq.empty():
                frames.append(link.rxq.get_nowait())
            return s, frames
        s, frames = self.run_async(go())
        self.assertEqual(s.fail_streak, 1)
        self.assertIsNone(s.k_link)
        self.assertIn(P.pair_frame(P.PAIR_DONE, b"\x06"), frames)

    def test_timeouts_do_not_lock_early(self):
        import asyncio
        from fluidi_gw.transport import SimLink

        async def go():
            s = SimSensor("80:6F:B0:12:AB:CD")
            s.k_link, s.gateway_id = bytes(16), bytes(8)
            s.hello_deadline = 0.01
            for _ in range(9):
                s.on_connect(SimLink(s))
                await asyncio.sleep(0.03)
            locked9 = s.clock() < s.locked_until
            s.on_connect(SimLink(s))
            await asyncio.sleep(0.03)
            return locked9, s.clock() < s.locked_until, s.fail_streak
        locked9, locked10, fails = self.run_async(go())
        self.assertFalse(locked9)      # Ä-4: Fristüberschreitungen sind keine Fehlversuche
        self.assertTrue(locked10)      # erst 10 in Folge -> Sperre
        self.assertEqual(fails, 0)


class DataPath(unittest.TestCase):
    def setUp(self):
        self.gw, _ = make_gateway(sensors=1, history_days=40, http=False, speed=0.001)
        self.gw._autopair()
        self.s = self.gw.sims[0]
        self.M = self.gw.model

    def tearDown(self):
        self.gw.stop()

    def test_backfill_ack_and_time(self):
        """Nachlieferung: alle Ringwerte gespeichert, erst danach quittiert; Zeit aus Laufzeit rekonstruiert."""
        n = len(self.s.ring)
        self.assertTrue(wait(lambda: self.s.acked >= self.s.seq - 1 and len(readings(self.gw, self.s.addr)) >= n, 15))
        rows = readings(self.gw, self.s.addr)
        seqs = [r["seq"] for r in rows]
        self.assertEqual(seqs, sorted(set(seqs)))
        # Werte vor der ersten Sitzung: nur Synchronpunkte danach -> Rückrechnung, Abweichung < 2 s
        first = self.s.ring[0]
        t_true = self.s.boot_clock + first.uptime_s
        r0 = next(r for r in rows if r["seq"] == first.seq)
        self.assertLess(abs(r0["t"] - t_true), 2)
        self.assertTrue(r0["flags"] & 8)  # nachgeliefert

    def test_duplicates_after_lost_ack(self):
        """Quittung verloren (Sensor quittiert nicht): Werte kommen nochmals -> keine Duplikate, trotzdem quittiert."""
        wait(lambda: self.s.acked >= self.s.seq - 1, 15)
        before = len(readings(self.gw, self.s.addr))
        self.s.acked = -1   # Sensor hat die Quittungen „vergessen“ -> liefert alles nochmals
        self.assertTrue(wait(lambda: self.s.acked >= self.s.seq - 1, 15))
        rows = readings(self.gw, self.s.addr)
        self.assertEqual(len(rows), len({r["seq"] for r in rows}))
        self.assertGreaterEqual(len(rows), before)

    def test_reboot_without_gateway(self):
        """Batteriewechsel ohne Gateway (neue boot_id, Laufzeit beginnt bei 0): Werte nach Rückrechnung plausibel."""
        wait(lambda: self.s.acked >= self.s.seq - 1, 15)
        self.M.central.call(lambda: setattr(self.s, "links", self.s.links))
        self.s._reboot(0)
        self.s.boot_clock -= 7200          # neuer Start vor 2 h
        rec = self.s.measure(0)            # Messung „vor kurzem“ ohne Gateway-Kontakt
        self.assertTrue(wait(lambda: self.gw.store.q1("SELECT t, flags FROM reading WHERE sensor=? AND seq=?", (self.s.addr, rec.seq)), 15))
        r = self.gw.store.q1("SELECT t, flags FROM reading WHERE sensor=? AND seq=?", (self.s.addr, rec.seq))
        self.assertLess(abs(r["t"] - (self.s.boot_clock + rec.uptime_s)), 2)

    def test_ring_overflow_reported(self):
        wait(lambda: self.s.acked >= self.s.seq - 1, 15)
        self.s.lost = 7
        self.s.measure(0)
        self.assertTrue(wait(lambda: self.M.sensors[self.s.name].get("lost_records") == 7, 15))

    def test_settings_pushed(self):
        self.assertTrue(wait(lambda: self.s.settings_ver > 0, 15))
        self.assertEqual(self.s.settings["adv_interval_ms"], 27500)
        self.assertEqual(self.s.settings["led_weekdays"], 0x7F)               # TLV 0x0F (v2)
        self.assertGreater(self.s.settings["water_raw"], 0)    # Schwelle als Rohwert (REQ-UI-07)
        self.assertTrue(self.s.time_known)                     # TIME_SET gesendet

    def test_measure_command(self):
        j = self.M.new_job("measure", self.s.name, 1)
        got = {}
        self.M.central.submit(self.s.addr, {"kind": "measure", "job": j, "on_done": lambda r: got.update(r) or {}})
        self.assertTrue(wait(lambda: j["state"] == "done", 15), j["message"])
        self.assertEqual(got["records"][0].cause, 2)
        self.assertTrue(wait(lambda: self.s.acked >= got["records"][0].seq, 10))

    def test_measure_async_record_in_next_session(self):
        """Ä-8: Antwort {status, seq}; Messung nach dem Trennen; Auftrag fertig erst mit dem Datensatz `seq`."""
        wait(lambda: self.s.acked >= self.s.seq - 1, 15)
        seq_before = self.s.seq
        j = self.M.new_job("measure", self.s.name, 1)
        states = []
        orig = self.M.job_update

        def spy(job, **kw):
            states.append(kw.get("state"))
            orig(job, **kw)
        self.M.job_update = spy
        self.M.central.submit(self.s.addr, {"kind": "measure", "job": j})
        self.assertTrue(wait(lambda: j["state"] == "done", 15), j["message"])
        self.M.job_update = orig
        self.assertIn("running", states)
        r = self.gw.store.q1("SELECT cause FROM reading WHERE sensor=? AND seq=?", (self.s.addr, seq_before))
        self.assertEqual(r["cause"], 2)
        self.assertTrue(wait(lambda: self.s.acked >= seq_before, 10))

    def test_calibration_capture_multi_session(self):
        got = {}
        j = self.M.new_job("calibration_capture", self.s.name, 1, timeout_s=60)
        self.M.central.submit(self.s.addr, {"kind": "calibration_capture", "job": j, "samples": 3, "purpose": 1,
                                            "on_done": lambda r: got.update(r) or {}})
        self.assertTrue(wait(lambda: j["state"] == "done", 30), j["message"])
        self.assertEqual(len(got["records"]), 3)
        self.assertEqual({r.cause for r in got["records"]}, {3})

    def test_bad_mic_session_dropped(self):
        """Falscher Schlüssel im Gateway: SESSION_INFO-MIC ungültig -> Sitzung abgebrochen, nichts gespeichert."""
        wait(lambda: self.s.acked >= self.s.seq - 1, 15)
        n0 = self.gw.store.count_readings()["n"]
        self.gw.store.save_sensor(self.s.addr, self.s.name, {}, k_link=bytes(16), keep_key=False)
        self.s.measure(0)
        self.assertTrue(wait(lambda: self.gw.central.stats["auth_fail"] > 0, 10))
        self.assertEqual(self.gw.store.count_readings()["n"], n0)

    def test_ota_rollout(self):
        key = crypto.SigningKey()
        img = mcuboot.build(bytes(range(256)) * 200, (1, 1, 0), key=key)
        meta = mcuboot.parse(img, key.public_raw)
        doc = {"version": "1.1.0", "build": 0, "security_counter": meta.security_counter, "size": len(img),
               "sha256": meta.file_sha256.hex(), "signature_ok": True, "hw_compat": "A-32 rev A", "uploaded": "x"}
        p = self.M.image_path("1.1.0")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(img)
        self.M.sensor_images.append(doc)
        self.M.rollout = {"version": "1.1.0", "started": "x", "finished": None,
                          "items": [{"sensor_id": self.s.name, "state": "pending", "progress": 0.0, "message": None}]}
        it = self.M.rollout["items"][0]
        self.assertTrue(wait(lambda: it["state"] in ("done", "failed"), 30), it)
        self.assertEqual(it["state"], "done", it["message"])
        self.assertEqual(self.s.fw, (1, 1, 0))
        self.assertTrue(self.s.slot_confirmed)
        self.assertTrue(wait(lambda: self.M.sensors[self.s.name].get("sec_cnt") == meta.security_counter, 10))

    def test_unpair(self):
        j = self.M.new_job("unpair", self.s.name, None)
        self.M.central.submit(self.s.addr, {"kind": "unpair", "job": j})
        self.assertTrue(wait(lambda: j["state"] == "done", 15))
        self.assertIsNone(self.s.k_link)


class Diagnosis(unittest.TestCase):
    """O-1/O-3: Diagnose über das echte Protokoll, Testfirmware-Kennung (TESTFIRMWARE.md Kap. 3)."""

    def setUp(self):
        self.gw, _ = make_gateway(sensors=2, history_days=1, http=False, speed=0.001, sim_testfw=2)
        self.gw._autopair()
        self.M = self.gw.model
        self.serial, self.tf = self.gw.sims[0], self.gw.sims[1]

    def tearDown(self):
        self.gw.stop()

    def _diag(self, sim):
        sid = P.sensor_name(sim.addr)
        j = self.M.new_job("diag", sid)
        self.M.central.submit(sim.addr, {"kind": "diag", "job": j,
                                         "on_done": lambda r: self.M.diag_received(sim.addr, r.get("info_hex"), r.get("diag_hex"), j["id"])})
        self.assertTrue(wait(lambda: j["state"] in ("done", "failed"), 15), j["message"])
        self.assertEqual(j["state"], "done", j["message"])
        return sid, j["result"]

    def test_testfw_marked(self):
        self.assertEqual(self.tf.name[:7], "fl-tf2-")
        sid, r = self._diag(self.tf)
        self.assertEqual(r["testfw"], 2)
        self.assertEqual(set(r["testfw_sources"]), {"info_tail", "diag_tail", "fw_build", "name"})
        self.assertEqual(len(bytes.fromhex(r["info_hex"])), 72)          # 68 + 'T' 'F' n 1
        self.assertEqual((r["info"]["fw_build"], r["info"]["build_marks_testfw"]), (9201, True))
        self.assertEqual(r["diag"]["tf"]["variant"], 2)
        self.assertEqual(r["decode_errors"], [])
        out = self.M.sensor_out(self.M.sensors[sid])
        self.assertEqual((out["testfw"], out["fw_build"], out["adv_name"]), (2, 9201, self.tf.name))
        self.assertTrue(any(e["code"] == "testfw" for e in self.gw.store.events(50)))
        # gespeichert wie testfw_eval sie liest (Tabelle sensor_diag)
        row = self.gw.store.q1("SELECT info_hex, diag_hex FROM sensor_diag WHERE sensor=? ORDER BY id DESC", (self.tf.addr,))
        self.assertEqual((row["info_hex"], row["diag_hex"]), (r["info_hex"], r["diag_hex"]))

    def test_serial_and_counters(self):
        self.serial.diag_counters.update(wdt=2, brownouts=1)
        sid, r = self._diag(self.serial)
        self.assertEqual((r["testfw"], r["diag"]["wdt_resets"], r["diag"]["brownouts"], r["diag"]["tf"]), (0, 2, 1, None))
        self.assertEqual(self.M.sensor_out(self.M.sensors[sid])["testfw"], 0)

    def test_partial_when_info_rejected(self):
        orig = self.serial._dispatch

        async def no_info(link, msg, rid, pl):
            if msg == P.M_GET_INFO:
                self.serial._send(link, P.M_ERR_RSP, rid, bytes([0x01, msg]))
                return
            await orig(link, msg, rid, pl)
        self.serial._dispatch = no_info
        _sid, r = self._diag(self.serial)
        self.assertIsNone(r["info_hex"])
        self.assertIsNotNone(r["diag"])

    def test_history_kept_after_unpair(self):
        sid, r = self._diag(self.serial)
        from fluidi_gw import api
        api.remove_sensor(self.M, self.M.sensors[sid])
        self.assertEqual(self.gw.store.diags(self.serial.addr)[0]["info_hex"], r["info_hex"])


if __name__ == "__main__":
    unittest.main()
