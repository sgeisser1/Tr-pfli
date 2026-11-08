#!/usr/bin/env python3
"""Tests fuer scripts/testfw_eval.py (Testfirmware-Auswertung, Testplan Anhang A).

1. Synthetische Nutzlasten (Python-Nachbildung) -> Dekodieren und Kriterien.
2. Gegenprobe mit den ECHTEN Nutzlasten der simulierten Testfirmware (C-Kern, firmware/sensor/tests/build/tf*_*.hex,
   erzeugt von `make -C firmware/sensor/tests`); fehlen sie, werden diese Tests uebersprungen.
3. TF-3-Auswertung aus einer Gateway-Datenbank (Schema wie firmware/gateway/fluidi_gw/store.py, temporaer).
"""
import contextlib
import io
import os
import sqlite3
import tempfile
import unittest

import testfw_eval as T

HERE = os.path.dirname(os.path.abspath(__file__))
DUMPS = os.path.join(HERE, "..", "firmware", "sensor", "tests", "build")


def dump(name):
    p = os.path.join(DUMPS, name)
    if not os.path.exists(p):
        raise unittest.SkipTest(f"{name} fehlt (zuerst make -C firmware/sensor/tests)")
    with open(p) as f:
        return T._hex(f.read())


class Synthetic(unittest.TestCase):
    def test_info(self):
        d = T.parse_info(T.sim_info(3, 9301))
        self.assertEqual((d["testfw"], d["fw_build"], d["build_marks_testfw"]), (3, 9301, True))
        d = T.parse_info(T.sim_info(3, 1)[:68])
        self.assertEqual(d["testfw"], 0)

    def test_diag_tf2(self):
        p = T.sim_diag(2, entries=[(0x52, 0xBF, 4, 1)], tf2_mode=2, tf2_cycles=3, tf2_max_ops=0, backoffs=1)
        d = T.parse_diag(p)
        self.assertEqual(d["tf"]["tf2_mode"], 2)
        self.assertTrue(all(ok for ok, _ in T.check_diag(d, "tf2-early")))
        bad = T.parse_diag(T.sim_diag(2, tf2_mode=2, tf2_cycles=2, tf2_max_ops=4, backoffs=1))
        self.assertFalse(all(ok for ok, _ in T.check_diag(bad, "tf2-early")))

    def test_diag_tf2_hf(self):
        # O-5: HardFault -> fl_fault_handler -> Grund hardfault (0x52, detail = abn 1/2), nicht mehr Watchdog (0x50)
        kw = dict(tf2_mode=3, tf2_cycles=3, tf2_max_ops=4, backoffs=1)
        ok = T.parse_diag(T.sim_diag(2, entries=[(0x52, 1, 2, 3), (0x52, 2, 3, 3), (0x52, 0xBF, 5, 1)], **kw))
        self.assertTrue(all(o for o, _ in T.check_diag(ok, "tf2-hf")), T.check_diag(ok, "tf2-hf"))
        old = T.parse_diag(T.sim_diag(2, entries=[(0x50, 1, 2, 600), (0x50, 2, 3, 600), (0x52, 0xBF, 5, 1)], wdt=2, **kw))
        self.assertFalse(T.check_diag(old, "tf2-hf")[-1][0])

    def test_serial_diag_has_no_tail(self):
        p = bytes([0]) + bytes(8)
        self.assertIsNone(T.parse_diag(p)["tf"])
        self.assertFalse(T.check_diag(T.parse_diag(p), "tf1")[0][0])
        with self.assertRaises(T.EvalError):
            T.parse_diag(p + b"XY" + bytes(66))

    def test_records(self):
        r = T.eval_tf3(T.parse_records(T.sim_records(10, err_at=4)))
        self.assertEqual((r["n"], r["temp_invalid"], r["i2c_err_max"], r["ok"]), (10, 1, 1, False))
        self.assertTrue(T.eval_tf3(T.parse_records(T.sim_records(5)))["ok"])

    def test_cli_sim(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(T.main(["--sim", "diag", "--expect", "tf2-late"]), 0)
            self.assertEqual(T.main(["--sim", "info"]), 0)
            self.assertEqual(T.main(["--sim", "tf3"]), 1)      # synthetisch mit einem I2C-Fehler
        self.assertIn("Testfirmware: TF-1", out.getvalue())


class FromFirmware(unittest.TestCase):
    """Nutzlasten aus dem C-Kern der Testfirmware (Host-Simulation)."""

    def test_info_dump(self):
        for n in (1, 2, 3, 4):
            d = T.parse_info(dump(f"tf{n}_info.hex"))
            self.assertEqual(d["testfw"], n)

    def test_tf1(self):
        d = T.parse_diag(dump("tf1_diag_wdt.hex"))
        self.assertTrue(all(ok for ok, _ in T.check_diag(d, "tf1")), T.check_diag(d, "tf1"))

    def test_tf2(self):
        for name, exp in (("late", "tf2-late"), ("early", "tf2-early"), ("hf", "tf2-hf")):
            d = T.parse_diag(dump(f"tf2_diag_tf2_{name}.hex"))
            self.assertTrue(all(ok for ok, _ in T.check_diag(d, exp)), (name, T.check_diag(d, exp)))

    def test_tf3(self):
        d = T.parse_diag(dump("tf3_diag_tf3.hex"))
        chk = T.check_diag(d, "tf3")
        self.assertEqual([ok for ok, _ in chk], [True, True, True, False])   # Simulation enthaelt 1 I2C-Fehler
        self.assertEqual(d["tf"]["tf3_max_c"], 65.12)
        recs = T.parse_records(dump("tf3_records_tf3.hex"))
        self.assertEqual([r["cause"] for r in recs], [0x83] * 3)
        self.assertEqual(recs[1]["temp"], None)
        self.assertEqual(recs[1]["c_diag"], 1)

    def test_boot_n2(self):
        for n in (1, 2, 3, 4):
            d = T.parse_diag(dump(f"tf{n}_diag_boot.hex"))
            self.assertEqual(d["tf"]["flash_ops_ready"], 0)
            self.assertEqual(d["tf"]["variant"], n)


class GatewayDb(unittest.TestCase):
    def test_db(self):
        with tempfile.TemporaryDirectory() as td:
            db = os.path.join(td, "fluidi.sqlite")
            con = sqlite3.connect(db)
            con.execute("CREATE TABLE sensor (addr TEXT PRIMARY KEY, id TEXT NOT NULL UNIQUE, k_link BLOB, doc TEXT NOT NULL)")
            con.execute("CREATE TABLE reading (sensor TEXT NOT NULL, seq INTEGER NOT NULL, t INTEGER NOT NULL, raw INTEGER, "
                        "c_diag INTEGER, temp REAL, vbat INTEGER, cause INTEGER, sflags INTEGER, flags INTEGER, "
                        "boot_id INTEGER, uptime INTEGER, rx REAL, PRIMARY KEY (sensor, seq)) WITHOUT ROWID")
            con.execute("INSERT INTO sensor VALUES ('80:6F:B0:12:AB:CD', 'fluidi-ABCD', NULL, '{}')")
            for i in range(5):
                con.execute("INSERT INTO reading VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            ("80:6F:B0:12:AB:CD", i, 1000 + 60 * i, None, 0, 21.5, 2950, 0x83, 0, 16, 2, 60 * i + (200 if i == 4 else 0), 0))
            con.execute("INSERT INTO reading VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        ("80:6F:B0:12:AB:CD", 9, 2000, 3000, 65535, 21.0, 2950, 0, 0, 0, 2, 900, 0))
            con.commit(); con.close()
            r = T.eval_tf3(T.records_from_db(db, "fluidi-ABCD"))
            self.assertEqual((r["n"], r["ok"], len(r["gaps"])), (5, True, 1))


class GatewayDiag(unittest.TestCase):
    """Diagnose aus dem Gateway: echte Store-Tabelle sensor_diag (fluidi_gw/store.py) und JSON-Download der PWA."""

    def test_db_and_json(self):
        import json
        from fluidi_gw import store
        p = T.sim_diag(1, entries=[(0x50, 0, 3, 5)], wdt=1, tf1_trig=1, reset_reason=2)
        info = T.sim_info(1, 9101)
        with tempfile.TemporaryDirectory() as td:
            db = os.path.join(td, "fluidi.sqlite")
            st = store.Store(db)
            st.save_sensor("80:6F:B0:12:AB:CD", "fluidi-ABCD", {})
            st.add_diag("80:6F:B0:12:AB:CD", 1.0, info.hex(), p.hex(), {"sensor_id": "fluidi-ABCD"})
            st.close()
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(T.main(["diag", "--db", db, "--sensor", "fl-tf1-ABCD", "--expect", "tf1"]), 0)
                self.assertEqual(T.main(["info", "--db", db, "--sensor", "fluidi-ABCD"]), 0)
            self.assertIn("Testfirmware: TF-1", out.getvalue())
            js = os.path.join(td, "d.json")
            with open(js, "w") as f:
                json.dump({"sensor_id": "fluidi-ABCD", "info_hex": info.hex(), "diag_hex": p.hex()}, f)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(T.main(["diag", "--file", js, "--expect", "tf1"]), 0)
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(T.main(["diag", "--db", db, "--sensor", "fluidi-0000"]), 2)


if __name__ == "__main__":
    unittest.main()
