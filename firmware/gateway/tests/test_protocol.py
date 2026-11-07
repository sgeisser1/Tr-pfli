"""Rahmen, Nachrichten und Zeitrekonstruktion gegen PROTOCOL.md v1 (Layouts, Längen, Regeln)."""
import struct
import unittest

import helpers  # noqa: F401
from fluidi_gw import crypto, mcuboot
from fluidi_gw import protocol as P
from fluidi_gw import timesync as T


class Layout(unittest.TestCase):
    def test_sizes(self):
        self.assertEqual(len(P.hello(bytes(8), bytes(8))), 18)                  # 5.2
        self.assertEqual(len(P.hello_rsp(1, bytes(8))), 10)
        self.assertEqual(len(P.SessionInfo().pack()), 48)                       # 5.5
        self.assertEqual(len(P.SessionInfo().pack(True)), 64)
        self.assertEqual(len(P.Record(1, 2, 3, 4, 5, 6, 7, 8, 9).pack()), 20)   # 5.6
        self.assertEqual(P.records_per_frame(247), 11)                          # 5.6: MTU 247 -> 11
        self.assertEqual(len(P.PairReq(bytes(8), bytes(64), bytes(16)).payload()), 88)
        self.assertEqual(len(P.PairRsp(bytes(6), 0, bytes(4), bytes(64), bytes(16)).payload()), 91)

    def test_vt_and_version(self):
        self.assertEqual(P.hello(bytes(8), bytes(8))[0], 0x10)
        self.assertEqual(P.frame_type(bytes([0x12])), P.FT_SECURE)
        with self.assertRaises(P.ProtocolError) as e:
            P.frame_type(bytes([0x22]))
        self.assertEqual(e.exception.code, 0x08)

    def test_name_and_addr(self):
        self.assertEqual(P.sensor_name("80:6F:B0:12:AB:CD"), "fluidi-ABCD")      # 2.3 Beispiel
        self.assertEqual(P.addr_to_bytes("80:6F:B0:12:AB:CD"), bytes.fromhex("CDAB12B06F80"))
        self.assertEqual(P.bytes_to_addr(P.addr_to_bytes("80:6F:B0:12:AB:CD")), "80:6F:B0:12:AB:CD")

    def test_adv(self):
        mfr = P.build_mfr(P.ST_PAIRED | P.ST_DATA_PENDING, 2950, 0x1234, 0xBEEF)
        self.assertEqual(len(mfr) + 2, 11)                                      # 11 Byte inkl. Company-ID
        a = P.parse_adv("AA:BB:CC:DD:EE:FF", "fluidi-EEFF", {0xFFFF: mfr}, -60)
        self.assertTrue(a.has(P.ST_DATA_PENDING))
        self.assertEqual((a.vbat_mv, a.seq_lo, a.gw_hint), (2950, 0x1234, 0xBEEF))
        self.assertIsNone(P.parse_adv("x", None, {0xFFFF: b"xx" + mfr[2:]}))   # falsches Magic
        self.assertIsNone(P.parse_adv("x", None, {0x004C: mfr}))               # andere Firma

    def test_settings_tlv(self):
        v = {"meas_interval_s": 14400, "led_window": (420, 1140), "tx_power_dbm": -4, "air_flood_raw": (1000, 4500)}
        b = P.encode_settings(v)
        d, bad = P.decode_settings(b)
        self.assertEqual(bad, 0)
        self.assertEqual(d["led_window"], (420, 1140))
        self.assertEqual(d["tx_power_dbm"], -4)
        self.assertEqual(P.decode_settings(b + bytes([0x77, 1, 0]))[1], 0x77)    # unbekannte id -> abgelehnt
        self.assertEqual(P.decode_settings(bytes([0x01, 4]) + struct.pack("<I", 60))[1], 0x01)  # Bereich 900…

    def test_adv_interval_formula(self):
        self.assertEqual(P.adv_interval_ms(1), 27500)                           # Tab. 2.2
        self.assertEqual(P.adv_interval_ms(2), 57500)
        self.assertEqual(P.adv_interval_ms(5), 147500)


class Crypto(unittest.TestCase):
    def test_pairing_both_sides(self):
        g, s = crypto.EcdhKey(), crypto.EcdhKey()
        req = P.PairReq(bytes(range(8)), g.public_raw, bytes(16))
        rsp = P.PairRsp(P.addr_to_bytes("80:6F:B0:12:AB:CD"), 0x0A, b"\x01\x00\x03\x00", s.public_raw, bytes([1] * 16))
        kg = P.pair_keys(g.shared(s.public_raw), req, rsp)
        ks = P.pair_keys(s.shared(g.public_raw), req, rsp)
        self.assertEqual(kg, ks)
        self.assertEqual(len(kg[3]), 5)
        self.assertTrue(all(d in (0, 1, 2) for d in kg[3]))                     # nur Rot/Grün/Gelb, kein Blau

    def test_sas_digits(self):
        tr = bytes(32)
        h = crypto.sha256(b"fluidi-sas" + tr)
        n = (h[0] | h[1] << 8) % 243
        d = P.sas_digits(tr)
        self.assertEqual(d[0] * 81 + d[1] * 27 + d[2] * 9 + d[3] * 3 + d[4], n)

    def test_secure_channel_replay_and_tamper(self):
        k, a = bytes(16), P.addr_to_bytes("80:6F:B0:12:AB:CD")
        gw, se = P.SecureChannel(k, a, True), P.SecureChannel(k, a, False)
        f0 = gw.seal(P.M_GET_INFO, 1)
        self.assertEqual(se.open(f0), (P.M_GET_INFO, 1, b""))
        with self.assertRaises(P.ProtocolError) as e:   # Replay: ctr bereits verbraucht
            se.open(f0)
        self.assertEqual(e.exception.code, 0x07)
        f1 = bytearray(gw.seal(P.M_MEASURE, 2, b"\x00\x01"))
        f1[-1] ^= 0xFF
        with self.assertRaises(P.ProtocolError) as e:
            se.open(bytes(f1))
        self.assertEqual(e.exception.code, 0x06)
        # Richtung zählt: ein Gateway-Frame ist kein gültiger Sensor-Frame
        g2 = P.SecureChannel(k, a, True)
        with self.assertRaises(P.ProtocolError):
            g2.open(P.SecureChannel(k, a, True).seal(1, 1))
        self.assertEqual(len(gw.seal(1, 1, bytes(10))), 15 + 10)                 # Overhead 15 Byte (5.3)


class TimeSync(unittest.TestCase):
    def test_interpolation_and_drift(self):
        pts = [T.SyncPoint(3, 1000, 1_000_000), T.SyncPoint(3, 1000 + 86400, 1_000_000 + 86400 * 1.0001)]
        t, fl = T.reconstruct(3, 1000 + 43200, pts, 2e6)
        self.assertAlmostEqual(t, 1_000_000 + 43200 * 1.0001, places=3)
        self.assertEqual(fl, 0)
        t, fl = T.reconstruct(3, 1000 + 86400 + 3600, pts, 2e6)                 # Extrapolation mit Drift
        self.assertAlmostEqual(t, 1_000_000 + 86400 * 1.0001 + 3600 * 1.0001, places=2)

    def test_after_battery_change_only_later_point(self):
        # Sensor startete neu (boot 4) während das Gateway aus war: nur Punkt danach -> Rückrechnung, Flag 1
        pts = [T.SyncPoint(3, 50, 900_000), T.SyncPoint(4, 10_000, 2_000_000)]
        t, fl = T.reconstruct(4, 2_800, pts, 2e6)
        self.assertEqual(t, 2_000_000 - 7_200)
        self.assertTrue(fl & T.FLAG_RECONSTRUCTED)

    def test_unknown_boot_upper_bound(self):
        pts = [T.SyncPoint(5, 100, 3_000_000)]
        t, fl = T.reconstruct(4, 500, pts, 3e6)
        self.assertEqual(t, 3_000_000 - 100)
        self.assertTrue(fl & T.FLAG_UNSYNCED)

    def test_invalid_points_ignored(self):
        pts = [T.SyncPoint(1, 100, 5, valid=False)]
        _t, fl = T.reconstruct(1, 50, pts, 1e6)
        self.assertTrue(fl & T.FLAG_UNSYNCED)


class McuBoot(unittest.TestCase):
    def setUp(self):
        self.k = crypto.SigningKey()

    def test_valid_image(self):
        img = mcuboot.build(b"\x01" * 5000, (1, 2, 3), build_num=7, sec_cnt=4, key=self.k)
        im = mcuboot.parse(img, self.k.public_raw)
        self.assertEqual((im.version, im.build, im.security_counter, im.hw_rev), ((1, 2, 3), 7, 4, 0x0A))

    def test_rejections(self):
        img = mcuboot.build(b"\x01" * 5000, key=self.k)
        other = crypto.SigningKey()
        for data, key in ((img, other.public_raw), (img[:100] + b"\x00" + img[101:], self.k.public_raw),
                          (mcuboot.build(b"x" * 100, key=None), self.k.public_raw), (img, None),
                          (b"\x00" * 64, self.k.public_raw)):
            with self.assertRaises(mcuboot.ImageError):
                mcuboot.parse(data, key)
        with self.assertRaises(mcuboot.ImageError) as e:
            mcuboot.parse(mcuboot.build(b"\x00" * 240_000, key=self.k), self.k.public_raw)
        self.assertEqual(e.exception.code, "too_large")


if __name__ == "__main__":
    unittest.main()
