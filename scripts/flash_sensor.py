#!/usr/bin/env python3
"""fluidi – Erstprogrammierung des Sensors ueber den ROM-UART-Bootloader des CC2340R52.

Protokoll nach docs/datasheets/TI_CC23xx_TechnicalReferenceManual_SWCU193A.pdf Kap. 8.5 (S. 461-467):
  - Paket: Groesse (= Daten + 2), Pruefsumme (Summe der Datenbytes, 8 bit), Daten; Antwort ACK 0xCC / NACK 0x33,
    davor duerfen 0x00-Bytes kommen (S. 462-463, Tab. 8-37).
  - UART 8N1, Autobaud: 2 x 0x55 -> Antwort 0x00 0xCC (S. 464).
  - Befehle (Tab. 8-39): PING 0x20, GET_STATUS 0x21, GET_PART_ID 0x22, RESET 0x23, CHIP_ERASE 0x24, CRC32 0x25,
    DOWNLOAD 0x26, DOWNLOAD_CRC 0x27, SEND_DATA 0x28 (max. 253 Datenbyte, hier 248). Statuscodes Tab. 8-40.
  - Ablauf wie TRM 8.5.4: Chip-Erase -> Hauptflash (DOWNLOAD_CRC + SEND_DATA) -> CCFG 0x4E020000 (2048 B) -> Reset.
  - Bootloader-Start: Taster (DIO21) beim Einsetzen des Dummy-Zellen-Adapters gedrueckt halten (TRM S.465).

Sicherheit (CONCEPTS 2.7, Auflagen R2-A1..A4): nur mit Dummy-Zellen-Adapter (keine Zelle im Halter), UART-Pegel
1.8-2.0 V (PINMAP Rev B, DIO20), 2 x 100 kOhm je Pad -> hoechstens 57600 Baud (Werkzeug erzwingt das).

Serie (--lock): schreibt die CCFG mit gesperrtem Bootloader (pBldrVtor = FORBID, bldrEnabled = 0) und gesperrtem
SWD (allowDebugPort = FORBID, debugCfg.authorization = FORBID), CRCs neu berechnet (TRM Tab. 8-35, S. 460;
hw_ccfg.h im SDK). Danach ist eine Neuprogrammierung ueber die Pads NICHT mehr moeglich (nur OTA). PROTOTYP-PRUEFUNG.

Ohne Hardware: --sim (simuliertes Geraet, gleicher Bytestrom) bzw. --dry-run (nur Plan ausgeben).
Unit-Tests: scripts/test_flash_sensor.py.
"""
from __future__ import annotations

import argparse
import struct
import sys
import time
import zlib

ACK, NACK = 0xCC, 0x33
CMD_PING, CMD_GET_STATUS, CMD_GET_PART_ID, CMD_RESET = 0x20, 0x21, 0x22, 0x23
CMD_CHIP_ERASE, CMD_CRC32, CMD_DOWNLOAD, CMD_DOWNLOAD_CRC, CMD_SEND_DATA = 0x24, 0x25, 0x26, 0x27, 0x28
STATUS = {0x40: "SUCCESS", 0x41: "UNKNOWN_CMD", 0x42: "INVALID_CMD", 0x43: "INVALID_ADR", 0x44: "FLASH_FAIL",
          0x45: "CRC_FAIL", 0x46: "NEEDS_CHIP_ERASE"}
FLASH_SIZE, SECTOR = 0x80000, 0x800                   # CC2340R52: 512 kB, 2-kB-Sektoren (DS S.20 Tab. 7.11)
CCFG_BASE, CCFG_SIZE = 0x4E020000, 0x800
MAX_BAUD = 57600                                      # CONCEPTS 2.7 Punkt 3
CHUNK = 248

# CCFG-Offsets (SDK source/ti/devices/cc23x0r5/inc/hw_ccfg.h)
CCFG_PBLDR, CCFG_BLDRPARAM, CCFG_BOOT_CRC = 0x000, 0x004, 0x00C
CCFG_PERM, CCFG_MAIN_CRC = 0x018, 0x74C
CCFG_DBG, CCFG_DBG_CRC = 0x7D0, 0x7FC
CRC_RANGES = [(0x000, 0x00C, CCFG_BOOT_CRC), (0x010, 0x74C, CCFG_MAIN_CRC), (0x7D0, 0x7FC, CCFG_DBG_CRC)]
PBLDR_FORBID = 0xFFFFFFFC


class BootloaderError(Exception):
    pass


def crc32(data: bytes) -> int:
    """CRC-32 (IEEE 802.3, wie zlib). Gegenprobe: gleicher Wert wie SDK crc_tool fuer die CCFG (Unit-Test)."""
    return zlib.crc32(data) & 0xFFFFFFFF


# ----------------------------------------------------------------------------------------------------------
# Paketschicht
# ----------------------------------------------------------------------------------------------------------
class Link:
    """Paketprotokoll ueber ein Port-Objekt mit write(bytes) und read(n) -> bytes (Timeout liefert weniger)."""

    def __init__(self, port, retries: int = 3, log=None):
        self.port, self.retries, self.log = port, retries, log

    def _read_nonzero(self, timeout_bytes: int = 64) -> int:
        for _ in range(timeout_bytes):
            b = self.port.read(1)
            if not b:
                raise BootloaderError("Zeitueberschreitung (keine Antwort)")
            if b[0] != 0:
                return b[0]
        raise BootloaderError("nur 0x00 empfangen")

    def sync(self):
        self.port.write(b"\x55\x55")
        if self._read_nonzero() != ACK:
            raise BootloaderError("Autobaud: kein ACK")

    def send_packet(self, data: bytes):
        if not 1 <= len(data) <= 253:
            raise ValueError("Paketlaenge")
        frame = bytes([len(data) + 2, sum(data) & 0xFF]) + data
        for attempt in range(self.retries):
            self.port.write(frame)
            r = self._read_nonzero()
            if r == ACK:
                return
            if r != NACK:
                raise BootloaderError("unerwartete Antwort %#04x" % r)
        raise BootloaderError("NACK nach %d Versuchen" % self.retries)

    def recv_packet(self) -> bytes:
        size = self._read_nonzero()
        chk = self.port.read(1)
        data = self.port.read(size - 2)
        if len(chk) != 1 or len(data) != size - 2 or (sum(data) & 0xFF) != chk[0]:
            self.port.write(bytes([NACK]))
            raise BootloaderError("Antwortpaket fehlerhaft")
        self.port.write(bytes([ACK]))
        return data

    # ---- Befehle ----
    def status(self) -> int:
        self.send_packet(bytes([CMD_GET_STATUS]))
        return self.recv_packet()[0]

    def cmd(self, data: bytes, what: str):
        self.send_packet(data)
        st = self.status()
        if st != 0x40:
            raise BootloaderError("%s: Status %#04x %s" % (what, st, STATUS.get(st, "?")))

    def ping(self):
        self.cmd(bytes([CMD_PING]), "PING")

    def part_id(self) -> bytes:
        self.send_packet(bytes([CMD_GET_PART_ID]))
        return self.recv_packet()

    def chip_erase(self):
        self.cmd(bytes([CMD_CHIP_ERASE]), "CHIP_ERASE")

    def download(self, addr: int, data: bytes, progress=None):
        self.cmd(bytes([CMD_DOWNLOAD_CRC]) + struct.pack(">III", addr, len(data), crc32(data)), "DOWNLOAD_CRC %#x" % addr)
        for i in range(0, len(data), CHUNK):
            self.cmd(bytes([CMD_SEND_DATA]) + data[i:i + CHUNK], "SEND_DATA %#x" % (addr + i))
            if progress:
                progress(i + min(CHUNK, len(data) - i))

    def verify(self, addr: int, data: bytes) -> bool:
        self.send_packet(bytes([CMD_CRC32]) + struct.pack(">III", addr, len(data), crc32(data)))
        st = self.status()
        if st == 0x45:
            return False
        if st != 0x40:
            raise BootloaderError("CRC32: Status %#04x %s" % (st, STATUS.get(st, "?")))
        return True

    def reset(self):
        self.send_packet(bytes([CMD_RESET]))


# ----------------------------------------------------------------------------------------------------------
# Abbild aufbereiten
# ----------------------------------------------------------------------------------------------------------
def load_hex(path: str):
    from intelhex import IntelHex
    ih = IntelHex(path)
    flash = bytearray(b"\xff" * FLASH_SIZE)
    used = set()
    ccfg = None
    for start, end in ih.segments():
        if start >= CCFG_BASE and end <= CCFG_BASE + CCFG_SIZE:
            if ccfg is None:
                ccfg = bytearray(b"\xff" * CCFG_SIZE)
            ccfg[start - CCFG_BASE:end - CCFG_BASE] = ih.tobinstr(start, end - 1)
        elif end <= FLASH_SIZE:
            flash[start:end] = ih.tobinstr(start, end - 1)
            used.update(range(start // SECTOR, (end - 1) // SECTOR + 1))
        else:
            raise ValueError("Segment %#x..%#x ausserhalb Flash/CCFG" % (start, end))
    return flash, sorted(used), ccfg


def sector_runs(used):
    """zusammenhaengende Sektorfolgen -> [(addr, size)] (sektorausgerichtet, fuer CRC32-Pruefung)"""
    runs = []
    for s in used:
        if runs and runs[-1][1] == s:
            runs[-1][1] = s + 1
        else:
            runs.append([s, s + 1])
    return [(a * SECTOR, (b - a) * SECTOR) for a, b in runs]


def ccfg_fix_crcs(c: bytearray):
    for a, b, at in CRC_RANGES:
        struct.pack_into("<I", c, at, crc32(bytes(c[a:b])))


def ccfg_lock(c: bytearray) -> bytearray:
    """Serie: ROM-Bootloader und SWD sperren (TRM Tab. 8-35; hw_ccfg.h)."""
    c = bytearray(c)
    struct.pack_into("<I", c, CCFG_PBLDR, PBLDR_FORBID)
    p = struct.unpack_from("<I", c, CCFG_BLDRPARAM)[0] & ~0x1            # bldrEnabled = 0
    struct.pack_into("<I", c, CCFG_BLDRPARAM, p)
    perm = struct.unpack_from("<I", c, CCFG_PERM)[0] & 0x0FFFFFFF        # allowDebugPort (31:28) = FORBID
    struct.pack_into("<I", c, CCFG_PERM, perm)
    c[CCFG_DBG] = 0x00                                                   # debugCfg.authorization = DBGFORBID
    c[CCFG_DBG + 1] = 0x00                                               # allowBldr = FORBID
    ccfg_fix_crcs(c)
    return c


def ccfg_describe(c: bytes) -> str:
    pb, bp = struct.unpack_from("<II", c, 0)
    perm = struct.unpack_from("<I", c, CCFG_PERM)[0]
    return "pBldrVtor=%#010x bldrEnabled=%d pinTrig=%d DIO%d SWD=%s dbgAuth=%#04x" % (
        pb, bp & 1, (bp >> 1) & 1, (bp >> 16) & 0x3F, "erlaubt" if (perm >> 28) == 0xA else "GESPERRT", c[CCFG_DBG])


# ----------------------------------------------------------------------------------------------------------
# Simuliertes Geraet (ROM-Bootloader-Verhalten nach TRM 8.5) – fuer --sim und Unit-Tests
# ----------------------------------------------------------------------------------------------------------
class SimDevice:
    def __init__(self, part_id: bytes = b"\x3b\x5a\xd0\x0b", fault=None):
        self.flash = bytearray(b"\xff" * FLASH_SIZE)
        self.ccfg = bytearray(b"\xff" * CCFG_SIZE)
        self.part = part_id
        self.out = bytearray()
        self.inp = bytearray()
        self.synced = False
        self.last = 0x40
        self.dl = None            # [addr, remaining, crc, start, size]
        self.erased = False
        self.reset_done = False
        self.fault = fault or {}  # z. B. {"nack_once": True, "corrupt_byte": addr}
        self.bldr_enabled = True

    # Port-Schnittstelle
    def write(self, b: bytes):
        self.inp += b
        self._process()

    def read(self, n: int) -> bytes:
        r, self.out[:] = bytes(self.out[:n]), self.out[n:]
        return r

    def _process(self):
        while True:
            if not self.synced:
                if len(self.inp) >= 2 and self.inp[:2] == b"\x55\x55":
                    del self.inp[:2]
                    self.synced = True
                    self.out += b"\x00\xcc"
                    continue
                return
            if not self.inp:
                return
            if self.inp[0] in (ACK, NACK):           # Quittung des Hosts auf unser Antwortpaket
                del self.inp[0]
                continue
            size = self.inp[0]
            if len(self.inp) < size:
                return
            chk, data = self.inp[1], bytes(self.inp[2:size])
            del self.inp[:size]
            if self.fault.pop("nack_once", False) or (sum(data) & 0xFF) != chk:
                self.out += b"\x00" + bytes([NACK])
                continue
            self.out += b"\x00" + bytes([ACK])
            self._cmd(data)

    def _reply(self, data: bytes):
        self.out += bytes([len(data) + 2, sum(data) & 0xFF]) + data

    def _region(self, addr, size):
        if addr == CCFG_BASE and size <= CCFG_SIZE:
            return self.ccfg, 0
        if 0 <= addr and addr + size <= FLASH_SIZE:
            return self.flash, addr
        return None, None

    def _cmd(self, d: bytes):
        c = d[0]
        if c == CMD_GET_STATUS:
            self._reply(bytes([self.last]))
            return
        if not self.bldr_enabled:
            self.last = 0x42
            return
        self.last = 0x40
        if c == CMD_PING:
            pass
        elif c == CMD_GET_PART_ID:
            self._reply(self.part)
        elif c == CMD_RESET:
            self.reset_done = True
            # nach Reset: CCFG wirkt (gesperrter Bootloader nimmt nichts mehr an)
            self.bldr_enabled = struct.unpack_from("<I", self.ccfg, 0)[0] != PBLDR_FORBID
            self.synced = False
        elif c == CMD_CHIP_ERASE:
            self.flash[:] = b"\xff" * FLASH_SIZE
            self.ccfg[:] = b"\xff" * CCFG_SIZE
            self.erased = True
        elif c in (CMD_DOWNLOAD, CMD_DOWNLOAD_CRC):
            addr, size = struct.unpack(">II", d[1:9])
            mem, off = self._region(addr, size)
            if mem is None or size == 0:
                self.last = 0x43
                return
            if not self.erased:
                self.last = 0x46
                return
            crc = struct.unpack(">I", d[9:13])[0] if c == CMD_DOWNLOAD_CRC else None
            self.dl = [mem, off, size, crc, off, size]
        elif c == CMD_SEND_DATA:
            if not self.dl:
                self.last = 0x42
                return
            mem, off, rem, crc, start, size = self.dl
            data = bytearray(d[1:])
            if len(data) > rem:
                self.last = 0x42
                return
            bad = self.fault.get("corrupt_byte")
            if bad is not None and mem is self.flash and off <= bad < off + len(data):
                data[bad - off] ^= 0x01
            for i, b in enumerate(data):
                mem[off + i] &= b                                # Flash: nur 1 -> 0
            self.dl = [mem, off + len(data), rem - len(data), crc, start, size]
            if rem - len(data) == 0:
                if crc is not None and crc32(bytes(mem[start:start + size])) != crc:
                    mem[start:start + size] = b"\xff" * size     # TRM: Inhalt wird sofort geloescht
                    self.last = 0x45
                self.dl = None
        elif c == CMD_CRC32:
            addr, size, crc = struct.unpack(">III", d[1:13])
            mem, off = self._region(addr, size)
            if mem is None or addr % SECTOR or not (size % SECTOR == 0 or size % SECTOR == SECTOR - 4):
                self.last = 0x43
                return
            self.last = 0x40 if crc32(bytes(mem[off:off + size])) == crc else 0x45
        else:
            self.last = 0x41


# ----------------------------------------------------------------------------------------------------------
# Ablauf
# ----------------------------------------------------------------------------------------------------------
def program(link: Link, hexfile: str, lock: bool, out=print, do_reset: bool = True):
    flash, used, ccfg = load_hex(hexfile)
    if ccfg is None:
        raise BootloaderError("Hex enthaelt keine CCFG (MCUboot-Build pruefen)")
    if lock:
        ccfg = ccfg_lock(ccfg)
    runs = sector_runs(used)
    total = sum(s for _, s in runs)
    out("[flash] Plan: %d Bereich(e), %d Byte Hauptflash, CCFG %s" % (len(runs), total, ccfg_describe(ccfg)))
    link.sync()
    link.ping()
    out("[flash] verbunden, Part-ID %s" % link.part_id().hex())
    link.chip_erase()
    out("[flash] Chip-Erase ok")
    for a, s in runs:
        link.download(a, bytes(flash[a:a + s]))
        if not link.verify(a, bytes(flash[a:a + s])):
            raise BootloaderError("Verifikation %#x fehlgeschlagen" % a)
        out("[flash] %#07x..%#07x geschrieben und per CRC32 verifiziert" % (a, a + s - 1))
    link.download(CCFG_BASE, bytes(ccfg))
    if not link.verify(CCFG_BASE, bytes(ccfg)):
        raise BootloaderError("Verifikation CCFG fehlgeschlagen")
    out("[flash] CCFG geschrieben und verifiziert%s" % (" – BOOTLOADER/SWD GESPERRT" if lock else ""))
    if do_reset:
        link.reset()
        out("[flash] Reset – Taster loslassen, Sensor startet (L11)")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("action", choices=["info", "erase", "program", "verify"])
    ap.add_argument("--hex", default="firmware/sensor/build/fluidi-sensor-factory.hex")
    ap.add_argument("--port", help="serielle Schnittstelle, z. B. /dev/ttyUSB0")
    ap.add_argument("--baud", type=int, default=57600)
    ap.add_argument("--lock", action="store_true", help="Serie: Bootloader und SWD per CCFG sperren (irreversibel)")
    ap.add_argument("--sim", action="store_true", help="simuliertes Geraet statt Hardware")
    ap.add_argument("--dry-run", action="store_true", help="nur Plan anzeigen, nichts senden")
    ap.add_argument("--yes", action="store_true", help="Sicherheitsabfrage ueberspringen")
    a = ap.parse_args(argv)
    if a.baud > MAX_BAUD:
        ap.error("hoechstens %d Baud (2 x 100 kOhm je Pad, CONCEPTS 2.7)" % MAX_BAUD)
    if a.dry_run:
        flash, used, ccfg = load_hex(a.hex)
        for addr, size in sector_runs(used):
            print("[plan] DOWNLOAD_CRC %#07x %6d B crc32=%08x" % (addr, size, crc32(bytes(flash[addr:addr + size]))))
        if ccfg:
            c = ccfg_lock(ccfg) if a.lock else ccfg
            print("[plan] CCFG %s crc32=%08x" % (ccfg_describe(c), crc32(bytes(c))))
        return 0
    if a.sim:
        port = SimDevice()
    else:
        if not a.port:
            ap.error("--port fehlt (oder --sim / --dry-run)")
        if not a.yes:
            print("Sicherheit (CONCEPTS 2.7): KEINE Zelle im Halter, Dummy-Zellen-Adapter 1.8-2.0 V, UART 1.8 V,")
            print("Taster beim Einsetzen gedrueckt halten (ROM-Bootloader). Weiter mit 'ja': ", end="")
            if input().strip().lower() != "ja":
                return 1
        import serial  # pyserial
        port = serial.Serial(a.port, a.baud, timeout=2.0)
        time.sleep(0.05)
    link = Link(port)
    try:
        if a.action == "info":
            link.sync(); link.ping()
            print("[info] Bootloader antwortet, Part-ID %s" % link.part_id().hex())
        elif a.action == "erase":
            link.sync(); link.chip_erase(); print("[erase] ok")
        elif a.action == "program":
            program(link, a.hex, a.lock)
        elif a.action == "verify":
            flash, used, ccfg = load_hex(a.hex)
            link.sync()
            ok = all(link.verify(addr, bytes(flash[addr:addr + s])) for addr, s in sector_runs(used))
            print("[verify] %s" % ("ok" if ok else "ABWEICHUNG"))
            return 0 if ok else 2
    except BootloaderError as e:
        print("[flash] FEHLER:", e)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
