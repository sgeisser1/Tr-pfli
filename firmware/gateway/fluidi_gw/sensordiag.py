"""Dekodierung der Sensor-Diagnose: GET_INFO (0x90) und GET_DIAG (0x98) inkl. Testfirmware-Anhängen.

EINZIGE Dekodierlogik im Projekt: das Gateway (central.py/api.py: POST /sensors/{id}/diag) und das Host-Skript
scripts/testfw_eval.py importieren dieses Modul. Nur Standardbibliothek (testfw_eval läuft ohne Gateway-Abhängigkeiten).

Quellen (nichts erfunden):
- INFO 68 Byte: firmware/PROTOCOL.md Kap. 5.5 (SESSION_INFO 52 Byte + meas/adv/conn/led_ms ab Offset 52).
- Fehlerprotokoll: PROTOCOL.md Kap. 5.7 (count u8 · count × {code u8, detail u8, boot_id u16, uptime_s u32} ·
  wdt_resets u16, brownouts u16, auth_fail u16, button_stuck u16); Fehlernamen Kap. 11.
- Testfirmware: docs/manuals/TESTFIRMWARE.md Kap. 3 (GET_INFO-Anhang 'T' 'F' <n> <tf_fmt> ab Offset 68,
  fw_build = 9<n><bb>, Gerätename fl-tf<n>-XXXX) und Kap. 6 (68-Byte-GET_DIAG-Anhang, fl_testfw.c fl_tf_diag_tail).
- Datensatz 20 Byte: PROTOCOL.md Kap. 5.6.
Alles little-endian.
"""
from __future__ import annotations

import re
import struct

DECODER = "fluidi-diag 1"     # Kennung der Dekodierung (im gespeicherten Ergebnis, für spätere Formatänderungen)

RESET = {0: "power_on", 1: "pin_reset", 2: "watchdog", 3: "software", 4: "brownout", 5: "hardfault", 6: "undervoltage"}
ERR = {0x00: "OK", 0x01: "UNKNOWN_CMD", 0x02: "BAD_LENGTH", 0x03: "BAD_PARAM", 0x04: "BUSY", 0x05: "NOT_PAIRED",
       0x06: "AUTH_FAIL", 0x07: "BAD_COUNTER", 0x08: "PROTO_VERSION", 0x09: "TIMEOUT", 0x0A: "NOT_ALLOWED",
       0x0B: "LOCKED", 0x20: "MEAS_OSC_FAIL", 0x21: "MEAS_RANGE", 0x22: "TEMP_FAIL", 0x23: "MEAS_NOISY",
       0x24: "MEAS_LOW_BATT", 0x30: "FLASH_FAIL", 0x31: "LOG_OVERWRITTEN", 0x32: "NVS_RESTORED",
       0x40: "OTA_BATT_LOW", 0x41: "OTA_TOO_LARGE", 0x42: "OTA_BAD_OFFSET", 0x43: "OTA_HASH", 0x44: "OTA_SIGNATURE",
       0x45: "OTA_ROLLBACK", 0x46: "OTA_FLASH", 0x47: "OTA_ABORTED", 0x48: "OTA_NOT_STARTED", 0x49: "OTA_REVERTED",
       0x4A: "OTA_HW_MISMATCH", 0x50: "WDT_RESET", 0x51: "BROWNOUT", 0x52: "HARDFAULT", 0x53: "BUTTON_STUCK",
       0x54: "LFXT_FAIL", 0x55: "UNDERVOLTAGE"}
TF2_MODE = {0: "aus", 1: "spaet (5 x)", 2: "frueh vor Lastmessung (7 x)", 3: "HardFault (9 x)"}
TF3_STAGE = {0: "-", 1: "I2C_open", 2: "Schreiben (Konfig)", 3: "Lesen (Temperatur)"}
CAUSE_TF3 = 0x83
TAIL_LEN = 68
INFO_LEN = 68
SI_LEN = 52
DIAG_MAX_ENTRIES = 16
TESTFW_VARIANTS = range(1, 5)          # TF-1..TF-4 (fl_testfw.h: FLUIDI_TESTFW 1..4)

# TF-4-Anhang (fl_testfw.c fl_tf_diag_tail, TESTFIRMWARE.md Kap. 6)
_TAIL = struct.Struct("<2sBBIIIIIBBIHHHHHHHHHBBBBIIhhhBB")
_TAIL_FIELDS = ("magic variant fmt meas adv conn led_ms charge_uc reset_reason abn_now ret_boot vdd_min vbat_rest "
                "vdd_min_ever boot_id flash_ops_boot flash_ops_ready backoffs tf1_trig tf2_trig tf2_mode tf2_cycles "
                "tf2_max_ops tf2_sd_ops tf3_reads tf3_err tf3_last tf3_min tf3_max tf3_stage sens_pwr_hold").split()
assert _TAIL.size == TAIL_LEN
_REC = struct.Struct("<IHIHHhHBB")
_NAME_TF = re.compile(r"^fl-tf([1-9])-[0-9A-Fa-f]{4}$")


class DecodeError(ValueError):
    pass


def from_hex(s: str) -> bytes:
    s = "".join((s or "").split())
    try:
        return bytes.fromhex(s)
    except ValueError as e:
        raise DecodeError(f"kein gueltiges Hex: {e}") from e


# ----------------------------------------------------------------------------------------------- Testfirmware-Kennung
def testfw_from_build(build) -> int:
    """fw_build = 9<n><bb> (TESTFIRMWARE.md Kap. 3) -> n, sonst 0. Serien-Builds sind < 9000 (Makefile)."""
    if not isinstance(build, int) or not 9000 <= build <= 9999:
        return 0
    n = (build // 100) % 10
    return n if n in TESTFW_VARIANTS else 0


_FILE_TF = re.compile(r"-tf([1-9])-")


def testfw_from_filename(name) -> int:
    """Dateiname fluidi-sensor-tf<n>-<ver>… (TESTFIRMWARE.md Kap. 2) -> n, sonst 0."""
    m = _FILE_TF.search(name or "")
    return int(m.group(1)) if m else 0


def testfw_of_image(build, filename=None) -> int:
    """Sensor-Abbild (Sicherheit W-2): Build 9000–9999 im signierten MCUboot-Kopf ist für Testfirmware reserviert
    (Serien-Builds < 9000, Makefile). n aus 9<n>xx; unbekannte Variante -> 9. Zusätzlich Dateiname -tf<n>-."""
    if isinstance(build, int) and 9000 <= build <= 9999:
        return testfw_from_build(build) or 9
    return testfw_from_filename(filename)


def testfw_from_name(name) -> int:
    """Gerätename im Advertising fl-tf<n>-XXXX (Serie: fluidi-XXXX) -> n, sonst 0."""
    m = _NAME_TF.match(name or "")
    return int(m.group(1)) if m else 0


# ----------------------------------------------------------------------------------------------- Dekodieren
def parse_info(p: bytes) -> dict:
    """GET_INFO-Antwort 0x90 (PROTOCOL 5.5, 68 Byte) + optional Testfirmware-Anhang 'TF' <n> <fmt>."""
    if len(p) < INFO_LEN:
        raise DecodeError(f"INFO zu kurz ({len(p)} < {INFO_LEN})")
    u16 = lambda o: struct.unpack_from("<H", p, o)[0]   # noqa: E731
    u32 = lambda o: struct.unpack_from("<I", p, o)[0]   # noqa: E731
    d = {"info_fmt": p[0], "fw": "%d.%d.%d" % (p[1], p[2], u16(3)), "fw_build": u32(5), "hw_rev": p[9], "state": p[10],
         "boot_id": u16(11), "uptime_s": u32(13), "seq_last": u32(19), "seq_oldest_unacked": u32(23),
         "vbat_load_mv": u16(27), "vbat_rest_mv": u16(29), "charge_uc": u32(31), "settings_ver": u16(35),
         "reset_reason": RESET.get(p[37], p[37]), "last_error": p[38],
         "last_error_name": ERR.get(p[38], f"0x{p[38]:02X}"), "ota_result": p[39], "slot_confirmed": bool(p[40] & 1),
         "rec_fmt": p[41], "log_capacity": u16(42), "lost_records": u32(44), "sec_cnt": u32(48)}
    d["meas"], d["adv"], d["conn"], d["led_ms"] = struct.unpack_from("<IIII", p, SI_LEN)
    d["testfw"] = 0
    d["tf_fmt"] = None
    if len(p) >= INFO_LEN + 4 and p[68:70] == b"TF":
        d["testfw"], d["tf_fmt"] = p[70], p[71]
    b = d["fw_build"]
    d["build_marks_testfw"] = 9000 <= b <= 9999 and (b // 100) % 10 == d["testfw"]
    return d


def parse_diag(p: bytes) -> dict:
    """GET_DIAG-Antwort 0x98 (PROTOCOL 5.7) + optional TF-4-Anhang (68 Byte, Kennung 'TF')."""
    if not p:
        raise DecodeError("GET_DIAG leer")
    n = p[0]
    if n > DIAG_MAX_ENTRIES or len(p) < 1 + 8 * n + 8:
        raise DecodeError(f"GET_DIAG: {n} Eintraege, aber nur {len(p)} Byte")
    entries = []
    for i in range(n):
        code, detail, boot, up = struct.unpack_from("<BBHI", p, 1 + 8 * i)
        entries.append({"code": code, "name": ERR.get(code, f"0x{code:02X}"), "detail": detail, "boot_id": boot, "uptime_s": up})
    k = 1 + 8 * n
    wdt, bo, auth, stuck = struct.unpack_from("<HHHH", p, k)
    d = {"entries": entries, "wdt_resets": wdt, "brownouts": bo, "auth_fail": auth, "button_stuck": stuck, "tf": None}
    k += 8
    if len(p) >= k + TAIL_LEN and p[k:k + 2] == b"TF":
        t = dict(zip(_TAIL_FIELDS, _TAIL.unpack_from(p, k)))
        t["reset_reason_txt"] = RESET.get(t["reset_reason"], t["reset_reason"])
        t["tf2_mode_txt"] = TF2_MODE.get(t["tf2_mode"], t["tf2_mode"])
        t["tf3_stage_txt"] = TF3_STAGE.get(t["tf3_stage"], t["tf3_stage"])
        for f in ("tf3_last", "tf3_min", "tf3_max"):
            t[f + "_c"] = None if t[f] in (-32768, 32767) else t[f] / 100.0
        t["magic"] = t["magic"].decode()
        d["tf"] = t
    elif len(p) > k:
        raise DecodeError(f"GET_DIAG: {len(p) - k} Byte Anhang ohne Kennung 'TF' (Serienfirmware liefert keinen)")
    return d


def parse_records(p: bytes) -> list:
    """Datensätze 20 Byte (PROTOCOL 5.6) hintereinander."""
    if len(p) % _REC.size:
        raise DecodeError(f"Datensaetze: Laenge {len(p)} kein Vielfaches von 20")
    out = []
    for i in range(0, len(p), _REC.size):
        seq, boot, up, c, cd, temp, vb, cause, fl = _REC.unpack_from(p, i)
        out.append({"seq": seq, "boot_id": boot, "uptime": up, "raw": None if c == 0xFFFF else c, "c_diag": cd,
                    "temp": None if temp == -32768 or fl & 0x10 else temp / 100.0, "vbat": vb, "cause": cause, "sflags": fl})
    return out


def decode(info_hex: str | None, diag_hex: str | None, adv_name: str | None = None) -> dict:
    """Beide Antworten dekodieren, ohne an einem Teil zu scheitern (Rohdaten bleiben immer erhalten).

    -> {"info": dict|None, "diag": dict|None, "errors": [str], "testfw": n (0 = Serie), "testfw_sources": [...],
        "fw_build": int|None, "decoder": DECODER}
    Testfirmware gilt als erkannt, wenn EIN Merkmal sie zeigt (INFO-Anhang 'TF', DIAG-Anhang, fw_build 9<n>xx,
    Gerätename fl-tf<n>-); widersprechen sich die Merkmale, steht das in `errors` (nie mit Serie verwechseln).
    """
    out = {"info": None, "diag": None, "errors": [], "decoder": DECODER}
    for key, hx, fn in (("info", info_hex, parse_info), ("diag", diag_hex, parse_diag)):
        if hx is None:
            continue
        try:
            out[key] = fn(from_hex(hx))
        except DecodeError as e:
            out["errors"].append(f"{key}: {e}")
    src = {}
    if out["info"]:
        if out["info"]["testfw"]:
            src["info_tail"] = out["info"]["testfw"]
        if testfw_from_build(out["info"]["fw_build"]):
            src["fw_build"] = testfw_from_build(out["info"]["fw_build"])
    if out["diag"] and out["diag"]["tf"]:
        src["diag_tail"] = out["diag"]["tf"]["variant"]
    if testfw_from_name(adv_name):
        src["name"] = testfw_from_name(adv_name)
    vals = set(src.values())
    if len(vals) > 1:
        out["errors"].append(f"Testfirmware-Merkmale widersprechen sich: {src}")
    out["testfw"] = max(vals) if vals else 0
    out["testfw_sources"] = sorted(src)
    out["fw_build"] = out["info"]["fw_build"] if out["info"] else None
    return out


# ----------------------------------------------------------------------------------------------- Simulation
def sim_diag(variant: int = 0, **kw) -> bytes:
    """Synthetische GET_DIAG-Nutzlast wie fl_app.c/fl_testfw.c (Tests, simulierter Sensor). variant 0 = Serie."""
    entries = kw.get("entries", [])
    p = bytes([len(entries)]) + b"".join(struct.pack("<BBHI", *e) for e in entries)
    p += struct.pack("<HHHH", kw.get("wdt", 0), kw.get("brownouts", 0), kw.get("auth_fail", 0), kw.get("button_stuck", 0))
    if not variant:
        return p
    t = {f: 0 for f in _TAIL_FIELDS}
    t.update(magic=b"TF", variant=variant, fmt=1, vdd_min=2950, vbat_rest=2980, vdd_min_ever=2950, boot_id=3,
             tf3_last=-32768, tf3_min=32767, tf3_max=-32768, sens_pwr_hold=1 if variant == 3 else 0)
    t.update({k: v for k, v in kw.items() if k in t})
    return p + _TAIL.pack(*(t[f] for f in _TAIL_FIELDS))


def sim_info(variant: int, build: int, **kw) -> bytes:
    """Synthetische GET_INFO-Nutzlast (68 Byte, PROTOCOL 5.5; mit variant > 0 + Anhang 'T' 'F' <n> 1).
    kw: fw (major, minor, patch), hw_rev, boot_id, uptime_s, vbat_load_mv, vbat_rest_mv, charge_uc, reset_reason,
    last_error, lost_records, sec_cnt, meas, adv, conn, led_ms (Rest 0)."""
    fw = kw.get("fw", (0, 1, 1))
    p = bytearray(INFO_LEN)
    p[0] = 1
    p[1:5] = bytes([fw[0], fw[1]]) + struct.pack("<H", fw[2])
    p[5:9] = struct.pack("<I", build)
    p[9] = kw.get("hw_rev", 0x0B)
    struct.pack_into("<HI", p, 11, kw.get("boot_id", 0), kw.get("uptime_s", 0))
    struct.pack_into("<IIHHI", p, 19, kw.get("seq_last", 0xFFFFFFFF), kw.get("seq_oldest_unacked", 0),
                     kw.get("vbat_load_mv", 0), kw.get("vbat_rest_mv", 0), kw.get("charge_uc", 0))
    p[37], p[38], p[39], p[40], p[41] = kw.get("reset_reason", 0), kw.get("last_error", 0), 0xFF, 1, 1
    struct.pack_into("<HII", p, 42, kw.get("log_capacity", 840), kw.get("lost_records", 0), kw.get("sec_cnt", 0))
    struct.pack_into("<IIII", p, SI_LEN, kw.get("meas", 0), kw.get("adv", 0), kw.get("conn", 0), kw.get("led_ms", 0))
    return bytes(p) + (b"TF" + bytes([variant, 1]) if variant else b"")


def sim_records(n: int, err_at: int = -1) -> bytes:
    """Synthetische TF-3-Datensätze (cause 0x83)."""
    out = b""
    err = 0
    for i in range(n):
        bad = i == err_at
        err += bad
        out += _REC.pack(100 + i, 3, 60 * (i + 1), 0xFFFF, err, -32768 if bad else 2150 + i, 2950, CAUSE_TF3, 0x10 if bad else 0)
    return out
