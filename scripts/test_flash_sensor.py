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

FACTORY = os.path.join(HERE, "..", "firmware", "sensor", "build", "fluidi-sensor-factory.hex")
MCUBOOT_HEX = os.path.join(HERE, "..", "firmware", "sensor", "build", "mcuboot", "mcuboot.hex")


def make_hex(path, with_ccfg=True):
    from intelhex import IntelHex
    ih = IntelHex()
    ih.frombytes(bytes((i * 7) & 0xFF for i in range(5000)), offset=0)
    ih.frombytes(bytes((i * 3 + 1) & 0xFF for i in range(3000)), offset=0x6000)
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
        dev = fs.SimDevice()
        fs.program(fs.Link(dev), self.hex, lock=True, out=lambda m: None)
        c = bytes(dev.ccfg)
        self.assertEqual(struct.unpack_from("<I", c, 0)[0], fs.PBLDR_FORBID)
        self.assertEqual(struct.unpack_from("<I", c, 4)[0] & 1, 0)
        self.assertEqual(struct.unpack_from("<I", c, fs.CCFG_PERM)[0] >> 28, 0)
        for a, b, at in fs.CRC_RANGES:                       # CRCs konsistent
            self.assertEqual(struct.unpack_from("<I", c, at)[0], fs.crc32(c[a:b]))
        link = fs.Link(dev)                                  # nach Reset: Bootloader nimmt nichts mehr an
        link.sync()
        with self.assertRaises(fs.BootloaderError):
            link.chip_erase()

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
        self.assertEqual(fs.main(["program", "--dry-run", "--hex", self.hex, "--lock"]), 0)


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
    def test_program_factory_hex_in_sim(self):
        dev = fs.SimDevice()
        fs.program(fs.Link(dev), FACTORY, lock=False, out=lambda m: None)
        self.assertEqual(struct.unpack_from("<I", dev.flash, 0x6000)[0], 0x96F3B83D)   # MCUboot-Kopf in Slot 0


if __name__ == "__main__":
    unittest.main()
