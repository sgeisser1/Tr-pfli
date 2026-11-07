"""Rahmen, Nachrichten und Zeitrekonstruktion gegen PROTOCOL.md v2 (Layouts, Längen, Regeln) und byte-genau gegen
die gemeinsame Referenz firmware/tools/fluidi_proto.py (gleiche Eingaben wie firmware/sensor/tests/gen_vectors.py)."""
import struct
import sys
import unittest
from pathlib import Path

import helpers  # noqa: F401
from fluidi_gw import crypto, mcuboot
from fluidi_gw import protocol as P
from fluidi_gw import timesync as T


class Layout(unittest.TestCase):
    def test_sizes(self):
        self.assertEqual(len(P.hello(bytes(8), bytes(8))), 18)                  # 5.2
        self.assertEqual(len(P.hello_rsp(2, bytes(8))), 10)
        self.assertEqual(len(P.SessionInfo().pack()), 52)                       # 5.5 v2 (sec_cnt, Ä-9)
        self.assertEqual(len(P.SessionInfo().pack(True)), 68)
        si = P.SessionInfo.parse(P.SessionInfo(sec_cnt=7).pack(True))
        self.assertEqual(si.sec_cnt, 7)
        self.assertEqual(len(P.measure_rsp(0, 5)), 5)                           # 5.4 v2 (Ä-8)
        self.assertEqual(len(P.Record(1, 2, 3, 4, 5, 6, 7, 8, 9).pack()), 20)   # 5.6
        self.assertEqual(P.records_per_frame(247), 11)                          # 5.6: MTU 247 -> 11
        self.assertEqual(len(P.PairReq.make(bytes(8), bytes(64), bytes(16)).payload()), 104)   # v2 (Ä-1)
        self.assertEqual(len(P.PairRsp(bytes(6), 0, bytes(4), bytes(64), bytes(16)).payload()), 91)

    def test_vt_and_version(self):
        self.assertEqual(P.hello(bytes(8), bytes(8))[0], 0x20)               # vt = 0x2t (Ä-2)
        self.assertEqual(P.frame_type(bytes([0x22])), P.FT_SECURE)
        with self.assertRaises(P.ProtocolError) as e:
            P.frame_type(bytes([0x12]))                                         # v1-Frame abgelehnt
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
        self.assertEqual(P.decode_settings(P.encode_settings({"led_weekdays": P.weekdays_mask([1, 2, 3, 4, 5])}))[0],
                         {"led_weekdays": 0x1F})                                # TLV 0x0F (W-7)

    def test_adv_interval_formula(self):
        self.assertEqual(P.adv_interval_ms(1), 27500)                           # Tab. 2.2
        self.assertEqual(P.adv_interval_ms(2), 57500)
        self.assertEqual(P.adv_interval_ms(5), 147500)


class Crypto(unittest.TestCase):
    def test_pairing_both_sides(self):
        g, s = crypto.EcdhKey(), crypto.EcdhKey()
        gn = bytes([9] * 16)
        req = P.PairReq.make(bytes(range(8)), g.public_raw, gn)
        rsp = P.PairRsp(P.addr_to_bytes("80:6F:B0:12:AB:CD"), 0x0A, b"\x01\x00\x03\x00", s.public_raw, bytes([1] * 16))
        self.assertTrue(req.check_reveal(gn))
        self.assertFalse(req.check_reveal(bytes(16)))                           # Commitment-Verletzung
        kg = P.pair_keys(g.shared(s.public_raw), req, rsp, gn)
        ks = P.pair_keys(s.shared(g.public_raw), req, rsp, gn)
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
        # OTA (Ä-6): Lücke nur für OTA_DATA zulässig, danach streng monoton
        gw.tx_ctr += 3
        self.assertEqual(se.open(gw.seal(P.M_OTA_DATA, 1, b"x"), ota_gap=64)[0], P.M_OTA_DATA)
        gw.tx_ctr += 2
        with self.assertRaises(P.ProtocolError):
            se.open(gw.seal(P.M_GET_INFO, 1), ota_gap=64)
        # Richtung zählt: ein Gateway-Frame ist kein gültiger Sensor-Frame
        g2 = P.SecureChannel(k, a, True)
        with self.assertRaises(P.ProtocolError):
            g2.open(P.SecureChannel(k, a, True).seal(1, 1))
        self.assertEqual(len(gw.seal(1, 1, bytes(10))), 15 + 10)                 # Overhead 15 Byte (5.3)


TOOLS = Path(__file__).resolve().parents[2] / "tools"
try:
    sys.path.insert(0, str(TOOLS))
    import fluidi_proto as REF  # gemeinsame Referenz (braucht `cryptography`)
    from cryptography.hazmat.primitives.asymmetric import ec as _ec
except ImportError:  # pragma: no cover
    REF = None


@unittest.skipUnless(REF, "firmware/tools/fluidi_proto.py oder cryptography fehlt")
class Reference(unittest.TestCase):
    """Gleiche feste Eingaben wie firmware/sensor/tests/gen_vectors.py -> byte-gleiche Ergebnisse."""

    def setUp(self):
        self.addr = bytes.fromhex("CDAB12B06F80")
        self.gw_id = bytes.fromhex("0102030405060708")
        gp = _ec.derive_private_key(0x1F2E3D4C5B6A79881F2E3D4C5B6A79881F2E3D4C5B6A79881F2E3D4C5B6A7988, _ec.SECP256R1())
        sp = _ec.derive_private_key(0x0A1B2C3D4E5F60710A1B2C3D4E5F60710A1B2C3D4E5F60710A1B2C3D4E5F6071, _ec.SECP256R1())
        self.gw_pub, self.s_pub = REF.pub64(gp), REF.pub64(sp)
        self.z = REF.ecdh(gp, self.s_pub)
        self.gn, self.sn = bytes(range(0xA0, 0xB0)), bytes(range(0xC0, 0xD0))
        self.fw = bytes([0, 1, 0, 0])

    def test_pairing_vectors(self):
        req = P.PairReq.make(self.gw_id, self.gw_pub, self.gn)
        rsp = P.PairRsp(self.addr, 0x0B, self.fw, self.s_pub, self.sn)
        self.assertEqual(req.payload(), REF.pair_req_payload(self.gw_id, self.gw_pub, self.gn))
        self.assertEqual(req.commit, REF.commit(self.gw_id, self.gw_pub, self.gn))
        self.assertEqual(rsp.payload(), REF.pair_rsp_payload(self.addr, 0x0B, self.fw, self.s_pub, self.sn))
        k_link, k_conf, tr, sas = P.pair_keys(self.z, req, rsp, self.gn)
        rtr = REF.transcript(req.payload(), rsp.payload(), self.gn)
        self.assertEqual(tr, rtr)
        self.assertEqual((k_link, k_conf), REF.pair_keys(self.z, self.gn, self.sn, self.gw_id, self.addr))
        self.assertEqual(sas, REF.sas(rtr))
        self.assertEqual(P.confirm_mac(k_conf, b"S", tr), REF.confirm_mac(k_conf, "S", rtr))
        self.assertEqual(P.confirm_mac(k_conf, b"G", tr), REF.confirm_mac(k_conf, "G", rtr))
        self.assertTrue(REF.check_reveal(req.payload(), self.gn))
        # Frames mit Kopf: vt = 0x23, pmsg
        self.assertEqual(P.pair_frame(P.PAIR_REVEAL, self.gn)[:2], bytes([REF.vt(REF.FT_PAIR), REF.PAIR_REVEAL]))

    def test_session_vectors(self):
        k_link, _ = REF.pair_keys(self.z, self.gn, self.sn, self.gw_id, self.addr)
        gn8, sn8 = bytes(range(0x10, 0x18)), bytes(range(0x20, 0x28))
        ks = P.session_key(k_link, gn8, sn8)
        self.assertEqual(ks, REF.session_key(k_link, gn8, sn8))
        sensor = P.SecureChannel(ks, self.addr, i_am_gateway=False)
        sensor.tx_ctr = 7
        f = sensor.seal(0x90, 0x42, bytes(range(30)))
        self.assertEqual(f, REF.seal(ks, REF.DIR_S2G, 7, self.addr, 0x90, 0x42, bytes(range(30))))
        gw = P.SecureChannel(ks, self.addr, i_am_gateway=True)
        gw.rx_ctr = 7
        self.assertEqual(gw.open(f), (0x90, 0x42, bytes(range(30))))

    def test_adv_name_record(self):
        hint = REF.gw_hint(self.gw_id)
        ref = REF.parse_adv(REF.adv_data(self.addr, 0x05, 2950, 0x123456, hint))
        mine = P.build_mfr(0x05, 2950, 0x123456 & 0xFFFF, P.gw_hint(self.gw_id))
        a = P.parse_adv("80:6F:B0:12:AB:CD", ref["name"], {0xFFFF: mine})
        self.assertEqual(ref["name"], P.sensor_name("80:6F:B0:12:AB:CD"))
        self.assertEqual((a.state, a.vbat_mv, a.seq_lo), (ref["state"], ref["vbat_mv"], ref["seq_lo"]))
        self.assertEqual(a.gw_hint.to_bytes(2, "little"), ref["gw_hint"])
        r = REF.Record(5, 2, 3600, 2500, 0xFFFF, 2150, 2950, 2, 0)
        self.assertEqual(P.Record.parse(r.encode()).pack(), r.encode())


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
