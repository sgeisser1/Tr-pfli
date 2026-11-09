#!/usr/bin/env python3
"""Unit-Tests fuer scripts/flash_sensor.py ohne Hardware (simuliertes ROM-Bootloader-Geraet).
Aufruf: python3 -m unittest scripts/test_flash_sensor.py   (oder make test in firmware/sensor)"""
import os
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import flash_sensor as fs  # noqa: E402

import glob  # noqa: E402
_f = sorted(glob.glob(os.path.join(HERE, "..", "firmware", "sensor", "build", "fluidi-sensor-factory-*.hex")))
FACTORY = _f[-1] if _f else "/nonexistent"
MCUBOOT_HEX = os.path.join(HERE, "..", "firmware", "sensor", "build", "mcuboot", "mcuboot.hex")


def spki(key):
    from cryptography.hazmat.primitives import serialization
    return key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)


def prod_key():
    from cryptography.hazmat.primitives.asymmetric import ec
    return ec.derive_private_key(0x1234567, ec.SECP256R1())


def dev_key():
    from cryptography.hazmat.primitives import serialization
    return serialization.load_pem_private_key(open(fs.DEV_KEY, "rb").read(), None)


def make_hex(path, with_ccfg=True, key=None, build=None):
    from intelhex import IntelHex
    ih = IntelHex()
    boot = bytearray((i * 7) & 0xFF for i in range(5000))
    if key is not None:
        boot[0x800:0x800 + 91] = spki(key)                 # eingebauter oeffentlicher Schluessel (wie fluidi_keys.c)
    ih.frombytes(bytes(boot), offset=0)
    slot0 = bytearray((i * 3 + 1) & 0xFF for i in range(3000))
    if build is not None:                                  # MCUboot-Kopf: Magic, ih_ver (0.1.1+build) ab +20
        struct.pack_into("<I", slot0, 0, 0x96F3B83D)
        struct.pack_into("<BBHI", slot0, 20, 0, 1, 1, build)
    ih.frombytes(bytes(slot0), offset=0x6000)
    if with_ccfg:
        c = bytearray(b"\xff" * fs.CCFG_SIZE)
        struct.pack_into("<IIII", c, 0, 0xFFFFFFF0, 0x00150003, 0, 0)
        struct.pack_into("<I", c, fs.CCFG_PERM, 0xAAAAAAAA)
        c[fs.CCFG_DBG] = 0x5A
        fs.ccfg_fix_crcs(c)
        ih.frombytes(bytes(c), offset=fs.CCFG_BASE)
    ih.write_hex_file(path)


class TestPacket(unittest.TestCase):
    def test_trm_example_checksum(self):
        # TRM Abb. 8-7: Daten 48 6f 6c 61 -> Groesse 0x06, Pruefsumme 0x84
        dev = fs.SimDevice()
        link = fs.Link(dev)
        sent = []
        orig = dev.write
        dev.write = lambda b: (sent.append(bytes(b)), orig(b))[1]
        link.sync()
        link.port.inp.clear()
        frame = bytes([6, 0x84, 0x48, 0x6F, 0x6C, 0x61])
        self.assertEqual(bytes([4 + 2, sum(b"\x48\x6f\x6c\x61") & 0xFF]) + b"\x48\x6f\x6c\x61", frame)

    def test_sync_ping_status(self):
        link = fs.Link(fs.SimDevice())
        link.sync()
        link.ping()
        self.assertEqual(link.part_id(), b"\x3b\x5a\xd0\x0b")

    def test_nack_retry(self):
        dev = fs.SimDevice(fault={"nack_once": True})
        link = fs.Link(dev)
        link.sync()
        link.ping()                      # erster Versuch NACK, zweiter ACK

    def test_needs_chip_erase(self):
        link = fs.Link(fs.SimDevice())
        link.sync()
        with self.assertRaises(fs.BootloaderError) as e:
            link.download(0, b"\x00" * 16)
        self.assertIn("NEEDS_CHIP_ERASE", str(e.exception))

    def test_crc_alignment_rule(self):
        link = fs.Link(fs.SimDevice())
        link.sync()
        with self.assertRaises(fs.BootloaderError):
            link.verify(0x10, b"\xff" * 0x800)       # Adresse nicht sektorausgerichtet -> INVALID_ADR


class TestProgram(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.hex = os.path.join(self.tmp, "t.hex")
        make_hex(self.hex)

    def test_program_and_verify(self):
        dev = fs.SimDevice()
        msgs = []
        fs.program(fs.Link(dev), self.hex, lock=False, out=msgs.append)
        flash, used, ccfg = fs.load_hex(self.hex)
        self.assertEqual(dev.flash[:0x8000], flash[:0x8000])
        self.assertEqual(dev.ccfg, ccfg)
        self.assertTrue(dev.reset_done)
        self.assertTrue(any("verifiziert" in m for m in msgs))

    def test_corruption_detected(self):
        dev = fs.SimDevice(fault={"corrupt_byte": 0x6010})
        with self.assertRaises(fs.BootloaderError):
            fs.program(fs.Link(dev), self.hex, lock=False, out=lambda m: None)

    def test_lock_disables_bootloader(self):
        h = os.path.join(self.tmp, "p.hex")
        make_hex(h, key=prod_key())
        fp = fs.key_fp(spki(prod_key()))
        dev = fs.SimDevice()
        fs.program(fs.Link(dev), h, lock=True, out=lambda m: None, expect_fp=fp)
        c = bytes(dev.ccfg)
        self.assertEqual(struct.unpack_from("<I", c, 0)[0], fs.PBLDR_FORBID)
        self.assertEqual(struct.unpack_from("<I", c, 4)[0] & 1, 0)
        perm = struct.unpack_from("<I", c, fs.CCFG_PERM)[0]
        self.assertEqual(perm >> 28, 0)                       # SWD
        self.assertEqual((perm >> 16) & 0xF, 0)               # FlashProgram (SACI)
        self.assertEqual((perm >> 8) & 0xF, 0)                # ToolsClientMode
        self.assertEqual(perm & 0xF, 0)                       # ReturnToFactory
        self.assertEqual((perm >> 12) & 0xF, 0xA)             # ChipErase bleibt (loescht Schluessel)
        wepra = struct.unpack_from("<I", c, fs.CCFG_WEPRA)[0]
        self.assertEqual(wepra & 0x7FF, 0)                    # Sektoren 0-10 (MCUboot) geschuetzt
        self.assertEqual((wepra >> 11) & 1, 1)                # Sektor 11 BIMINFO beschreibbar
        self.assertEqual(wepra >> 12, 0xFFFFF)                # Slots/NV beschreibbar (OTA)
        self.assertEqual(struct.unpack_from("<I", c, fs.CCFG_WEPRAUX)[0] & 1, 0)   # CCFG-Sektor geschuetzt
        for a, b, at in fs.CRC_RANGES:                       # CRCs konsistent
            self.assertEqual(struct.unpack_from("<I", c, at)[0], fs.crc32(c[a:b]))
        link = fs.Link(dev)                                  # nach Reset: Bootloader nimmt nichts mehr an
        link.sync()
        with self.assertRaises(fs.BootloaderError):
            link.chip_erase()

    def test_lock_refuses_dev_key(self):
        h = os.path.join(self.tmp, "d.hex")
        make_hex(h, key=dev_key())
        with self.assertRaises(fs.BootloaderError) as e:
            fs.program(fs.Link(fs.SimDevice()), h, lock=True, out=lambda m: None, expect_fp=fs.dev_key_fp())
        self.assertIn("DEV", str(e.exception))

    def test_lock_requires_matching_fingerprint(self):
        h = os.path.join(self.tmp, "p2.hex")
        make_hex(h, key=prod_key())
        for fp in (None, "0123456789abcdef"):
            dev = fs.SimDevice()
            with self.assertRaises(fs.BootloaderError):
                fs.program(fs.Link(dev), h, lock=True, out=lambda m: None, expect_fp=fp)
            self.assertFalse(dev.erased)                      # vor jedem Schreiben abgebrochen

    def test_missing_ccfg_refused(self):
        h = os.path.join(self.tmp, "n.hex")
        make_hex(h, with_ccfg=False)
        with self.assertRaises(fs.BootloaderError):
            fs.program(fs.Link(fs.SimDevice()), h, lock=False, out=lambda m: None)

    def test_baud_limit(self):
        with self.assertRaises(SystemExit):
            fs.main(["info", "--sim", "--baud", "115200"])

    def test_cli_sim_and_dry_run(self):
        self.assertEqual(fs.main(["program", "--sim", "--hex", self.hex]), 0)
        self.assertEqual(fs.main(["program", "--dry-run", "--hex", self.hex, "--lock"]), 2)   # ohne Fingerabdruck


class TestTestfirmware(unittest.TestCase):
    """Sicherheit W-2: Testfirmware-Hex nur mit ausdruecklicher Bestaetigung --testfw n, nie mit --lock."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def _hex(self, name, build):
        p = os.path.join(self.tmp, name)
        make_hex(p, build=build)
        return p

    def test_detect(self):
        flash, _, _ = fs.load_hex(self._hex("a.hex", 9201))
        self.assertEqual(fs.image_version(flash), (0, 1, 1, 9201))
        self.assertEqual(fs.testfw_variant(flash), 2)
        flash, _, _ = fs.load_hex(self._hex("b.hex", 1))
        self.assertIsNone(fs.testfw_variant(flash))
        self.assertEqual(fs.testfw_variant(flash, "/x/fluidi-sensor-tf3-factory-0.1.1+9301-keyab.hex"), 3)  # Dateiname
        flash, _, _ = fs.load_hex(self._hex("c.hex", None))       # ohne Kopf
        self.assertIsNone(fs.image_version(flash))

    def test_program_requires_confirmation(self):
        h = self._hex("tf.hex", 9401)
        with self.assertRaises(fs.BootloaderError):
            fs.program(fs.Link(fs.SimDevice()), h, lock=False, out=lambda m: None)
        with self.assertRaises(fs.BootloaderError):                      # falsche Nummer
            fs.program(fs.Link(fs.SimDevice()), h, lock=False, out=lambda m: None, testfw=2)
        msgs = []
        dev = fs.SimDevice()
        fs.program(fs.Link(dev), h, lock=False, out=msgs.append, testfw=4)
        self.assertTrue(dev.reset_done and any("TESTFIRMWARE TF-4" in m for m in msgs))

    def test_lock_and_serial_confirm_refused(self):
        h = self._hex("tf.hex", 9101)
        with self.assertRaises(fs.BootloaderError):
            fs.check_testfw(fs.load_hex(h)[0], h, 1, lock=True)
        s = self._hex("serie.hex", 1)
        with self.assertRaises(fs.BootloaderError):                      # --testfw an einer Serien-Datei
            fs.check_testfw(fs.load_hex(s)[0], s, 1, lock=False)
        self.assertIsNone(fs.check_testfw(fs.load_hex(s)[0], s, None, lock=False))

    def test_cli(self):
        h = self._hex("tf.hex", 9201)
        self.assertEqual(fs.main(["program", "--sim", "--yes", "--hex", h]), 2)        # --yes genuegt nicht
        self.assertEqual(fs.main(["program", "--sim", "--hex", h, "--testfw", "2"]), 0)
        self.assertEqual(fs.main(["program", "--dry-run", "--hex", h]), 0)             # Plan zeigt nur die Warnung


@unittest.skipUnless(os.path.exists(MCUBOOT_HEX), "MCUboot-Build fehlt (make in firmware/sensor)")
class TestRealBuild(unittest.TestCase):
    def test_ccfg_crc_matches_sdk_crc_tool(self):
        """Unser CRC32 muss die von SDK crc_tool eingetragenen CCFG-CRCs reproduzieren (Algorithmus-Gegenprobe)."""
        _, _, c = fs.load_hex(MCUBOOT_HEX)
        for a, b, at in fs.CRC_RANGES:
            self.assertEqual(struct.unpack_from("<I", c, at)[0], fs.crc32(bytes(c[a:b])), "CRC bei %#x" % at)

    def test_dev_ccfg_bootloader_settings(self):
        _, _, c = fs.load_hex(MCUBOOT_HEX)
        pb, bp = struct.unpack_from("<II", c, 0)
        self.assertEqual(bp & 1, 1)                       # bldrEnabled
        self.assertEqual((bp >> 1) & 1, 1)                # Pin-Trigger
        self.assertEqual((bp >> 2) & 1, 0)                # aktiv low
        self.assertEqual((bp >> 16) & 0x3F, 21)           # DIO21 (Taster)
        self.assertEqual((bp >> 24) & 7, 0)               # UART RX DIO20 / TX DIO6

    @unittest.skipUnless(os.path.exists(FACTORY), "Werks-Hex fehlt")
    def test_factory_with_dev_key_cannot_be_locked(self):
        flash, _, _ = fs.load_hex(FACTORY)
        if fs.dev_key_fp() not in fs.mcuboot_key_fps(flash):
            # make release SIGN_KEY=<eigener Schluessel>: Hex traegt den Produktionsschluessel -> DEV-Sperrtest entfaellt
            # (Schutz fuer den DEV-Fall bleibt in allen DEV-Builds; Produktionsschluessel prueft test_lock_* synthetisch)
            self.skipTest("Werks-Hex nicht mit dem DEV-Schluessel signiert (MCUboot-Schluessel %s)"
                          % ", ".join(fs.mcuboot_key_fps(flash)))
        self.assertEqual(fs.mcuboot_key_fps(flash), [fs.dev_key_fp()])
        self.assertIn(fs.dev_key_fp(), os.path.basename(FACTORY))          # Fingerabdruck im Dateinamen
        with self.assertRaises(fs.BootloaderError):
            fs.check_lock_key(flash, fs.dev_key_fp())

    @unittest.skipUnless(os.path.exists(FACTORY), "Werks-Hex fehlt")
    def test_program_factory_hex_in_sim(self):
        dev = fs.SimDevice()
        fs.program(fs.Link(dev), FACTORY, lock=False, out=lambda m: None)
        self.assertEqual(struct.unpack_from("<I", dev.flash, 0x6000)[0], 0x96F3B83D)   # MCUboot-Kopf in Slot 0

    @unittest.skipUnless(os.path.exists(FACTORY), "Werks-Hex fehlt")
    def test_real_factory_is_not_testfw(self):
        flash, _, _ = fs.load_hex(FACTORY)
        v = fs.image_version(flash)
        self.assertTrue(v is not None and v[3] < 9000)
        self.assertIsNone(fs.testfw_variant(flash, FACTORY))

    def test_real_tf_factory_detected(self):
        tf = sorted(glob.glob(os.path.join(HERE, "..", "firmware", "sensor", "build-tf*", "fluidi-sensor-tf*-factory-*.hex")))
        if not tf:
            self.skipTest("kein TF-Build (make TESTFW=n)")
        for p in tf:
            flash, _, _ = fs.load_hex(p)
            n = int(os.path.basename(os.path.dirname(p))[-1])
            self.assertEqual(fs.testfw_variant(flash), n, p)                       # aus dem Kopf, nicht dem Namen
            self.assertEqual(fs.testfw_variant(flash, ""), n)


if __name__ == "__main__":
    unittest.main()
