"""Dekodierung GET_INFO/GET_DIAG (fluidi_gw/sensordiag.py), gemeinsam mit scripts/testfw_eval.py.

Gegenprobe mit den echten Nutzlasten des C-Kerns (firmware/sensor/tests/build/tf<n>_*.hex), falls vorhanden.
"""
import struct
import unittest
from pathlib import Path

from helpers import ROOT
from fluidi_gw import protocol as P
from fluidi_gw import sensordiag as SD

DUMPS = ROOT.parent / "sensor" / "tests" / "build"


class Decode(unittest.TestCase):
    def test_info_matches_session_info_layout(self):
        si = P.SessionInfo(fw_ver=(1, 2, 300), fw_build=42, hw_rev=0x0A, boot_id=7, uptime_s=99, reset_reason=2,
                           last_error=0x50, lost_records=3, sec_cnt=5, counters={"meas": 11, "adv": 12, "conn": 13, "led_ms": 14})
        d = SD.parse_info(si.pack(with_counters=True))
        self.assertEqual((d["fw"], d["fw_build"], d["hw_rev"], d["boot_id"], d["uptime_s"]), ("1.2.300", 42, 0x0A, 7, 99))
        self.assertEqual((d["reset_reason"], d["last_error_name"], d["lost_records"], d["sec_cnt"]), ("watchdog", "WDT_RESET", 3, 5))
        self.assertEqual((d["meas"], d["adv"], d["conn"], d["led_ms"], d["testfw"]), (11, 12, 13, 14, 0))
        self.assertEqual(P.RESET_REASONS, [SD.RESET[i] for i in range(7)])     # gleiche Namen wie das Gateway

    def test_short_and_bad(self):
        with self.assertRaises(SD.DecodeError):
            SD.parse_info(bytes(52))                 # SESSION_INFO ist kein INFO
        with self.assertRaises(SD.DecodeError):
            SD.parse_diag(bytes([2]) + bytes(8))     # 2 Einträge angekündigt, keine geliefert
        with self.assertRaises(SD.DecodeError):
            SD.parse_diag(bytes(9) + b"XY")          # Anhang ohne 'TF'

    def test_decode_keeps_raw_and_reports(self):
        r = SD.decode("zz", SD.sim_diag(0).hex())
        self.assertIsNone(r["info"])
        self.assertEqual(r["diag"]["entries"], [])
        self.assertTrue(r["errors"][0].startswith("info:"))
        self.assertEqual(r["testfw"], 0)

    def test_testfw_markers(self):
        self.assertEqual([SD.testfw_from_build(b) for b in (1, 8999, 9101, 9401, 9501, 9999, None)], [0, 0, 1, 4, 0, 0, 0])
        self.assertEqual([SD.testfw_from_name(n) for n in ("fl-tf3-AB12", "fluidi-AB12", "fl-tf3-AB1", None)], [3, 0, 0, 0])
        r = SD.decode(SD.sim_info(3, 9301).hex(), SD.sim_diag(3).hex(), "fl-tf3-AB12")
        self.assertEqual((r["testfw"], r["errors"]), (3, []))
        r = SD.decode(SD.sim_info(3, 9201).hex(), None, None)        # Build sagt TF-2, Anhang TF-3
        self.assertEqual(r["testfw"], 3)
        self.assertIn("widersprechen", r["errors"][0])
        r = SD.decode(SD.sim_info(0, 12).hex(), None, "fl-tf1-AB12")  # nur der Name kennzeichnet: trotzdem markieren
        self.assertEqual(r["testfw"], 1)

    def test_diag_entries(self):
        p = SD.sim_diag(0, entries=[(0x52, 0xBF, 4, 1), (0x31, 7, 4, 99)], wdt=3)
        d = SD.parse_diag(p)
        self.assertEqual([(e["name"], e["detail"]) for e in d["entries"]], [("HARDFAULT", 0xBF), ("LOG_OVERWRITTEN", 7)])
        self.assertEqual(d["wdt_resets"], 3)
        self.assertEqual(struct.unpack_from("<H", p, 17)[0], 3)


class FromFirmware(unittest.TestCase):
    def _dump(self, name):
        f = DUMPS / name
        if not f.exists():
            self.skipTest(f"{name} fehlt (make -C firmware/sensor/tests)")
        return SD.from_hex(f.read_text())

    def test_c_core_payloads(self):
        for n in (1, 2, 3, 4):
            r = SD.decode(self._dump(f"tf{n}_info.hex").hex(), self._dump(f"tf{n}_diag_boot.hex").hex(), f"fl-tf{n}-ABCD")
            self.assertEqual((r["testfw"], r["errors"]), (n, []), r)
            # Host-Simulation baut mit fw_build 1 (Build-Nummer 9<n>xx setzt erst das Makefile): Anhänge + Name genügen
            self.assertEqual(r["testfw_sources"], ["diag_tail", "info_tail", "name"])


if __name__ == "__main__":
    unittest.main()
