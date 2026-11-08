#!/usr/bin/env python3
"""fluidi – Auswertung der TESTFIRMWARE (Testplan docs/reviews/phase5_testplan_prototyp.md Anhang A, TF-1..TF-4).

Dekodiert die Rohdaten, die die Testfirmware liefert, und prueft die Kriterien des Testplans:

  info    GET_INFO-Antwort (0x90) als Hex: 68 Byte (PROTOCOL 5.5) + Anhang "TF" <n> <fmt>
  diag    GET_DIAG-Antwort (0x98) als Hex: Fehlerprotokoll (PROTOCOL 5.7) + TF-4-Anhang (68 Byte, fl_testfw.c)
          --expect tf1 | tf2-late | tf2-early | tf2-hf | tf3   -> Kriterien PT5.12 / PT11.07 / PT11.19
  tf3     TF-3-Datensaetze (cause 0x83) aus der Gateway-Datenbank (--db fluidi.sqlite --sensor <addr|id>)
          oder als Hex (20-Byte-Datensaetze, PROTOCOL 5.6, --hex)

Woher die Hex-Daten kommen: Gateway `central.execute({"kind": "diag"})` liefert die GET_DIAG-Nutzlast als Hex;
ein API-Aufruf dafuer fehlt noch (offen, Software). Die Host-Tests (`make -C firmware/sensor/tests`) legen echte
Nutzlasten der simulierten Testfirmware unter firmware/sensor/tests/build/tf<n>_*.hex ab.

Ohne Hardware: `--sim` erzeugt synthetische Nutzlasten (Python-Nachbildung) und wertet sie aus.
Aufruf: .venv/bin/python scripts/testfw_eval.py diag --file tf2.hex --expect tf2-late
"""
import argparse
import json
import sqlite3
import struct
import sys

RESET = {0: "power_on", 1: "pin", 2: "watchdog", 3: "software", 4: "brownout", 5: "hardfault", 6: "undervoltage"}
ERR = {0x09: "TIMEOUT", 0x22: "TEMP_FAIL", 0x30: "FLASH_FAIL", 0x31: "LOG_OVERWRITTEN", 0x32: "NVS_RESTORED",
       0x50: "WDT_RESET", 0x51: "BROWNOUT", 0x52: "HARDFAULT", 0x53: "BUTTON_STUCK", 0x55: "UNDERVOLTAGE"}
TF2_MODE = {0: "aus", 1: "spaet (5 x)", 2: "frueh vor Lastmessung (7 x)", 3: "HardFault (9 x)"}
TF3_STAGE = {0: "-", 1: "I2C_open", 2: "Schreiben (Konfig)", 3: "Lesen (Temperatur)"}
CAUSE_TF3 = 0x83
TAIL_LEN = 68
INFO_LEN = 68

# TF-4-Anhang (fl_testfw.c fl_tf_diag_tail, little-endian)
_TAIL = struct.Struct("<2sBBIIIIIBBIHHHHHHHHHBBBBIIhhhBB")
_TAIL_FIELDS = ("magic variant fmt meas adv conn led_ms charge_uc reset_reason abn_now ret_boot vdd_min vbat_rest "
                "vdd_min_ever boot_id flash_ops_boot flash_ops_ready backoffs tf1_trig tf2_trig tf2_mode tf2_cycles "
                "tf2_max_ops tf2_sd_ops tf3_reads tf3_err tf3_last tf3_min tf3_max tf3_stage sens_pwr_hold").split()
assert _TAIL.size == TAIL_LEN


class EvalError(Exception):
    pass


def _hex(s: str) -> bytes:
    s = "".join(s.split())
    try:
        return bytes.fromhex(s)
    except ValueError as e:
        raise EvalError(f"kein gueltiges Hex: {e}") from e


# ----------------------------------------------------------------------------------------------- Dekodieren
def parse_info(p: bytes) -> dict:
    if len(p) < INFO_LEN:
        raise EvalError(f"INFO zu kurz ({len(p)} < {INFO_LEN})")
    d = {"fw": "%d.%d.%d" % (p[1], p[2], struct.unpack_from("<H", p, 3)[0]),
         "fw_build": struct.unpack_from("<I", p, 5)[0], "hw_rev": p[9], "state": p[10],
         "boot_id": struct.unpack_from("<H", p, 11)[0], "uptime_s": struct.unpack_from("<I", p, 13)[0],
         "vbat_load_mv": struct.unpack_from("<H", p, 27)[0], "vbat_rest_mv": struct.unpack_from("<H", p, 29)[0],
         "charge_uc": struct.unpack_from("<I", p, 31)[0], "reset_reason": RESET.get(p[37], p[37]),
         "last_error": p[38], "sec_cnt": struct.unpack_from("<I", p, 48)[0]}
    d["meas"], d["adv"], d["conn"], d["led_ms"] = struct.unpack_from("<IIII", p, 52)
    d["testfw"] = 0
    if len(p) >= INFO_LEN + 4 and p[68:70] == b"TF":
        d["testfw"], d["tf_fmt"] = p[70], p[71]
    b = d["fw_build"]
    d["build_marks_testfw"] = 9000 <= b <= 9999 and (b // 100) % 10 == d["testfw"]
    return d


def parse_diag(p: bytes) -> dict:
    if not p:
        raise EvalError("GET_DIAG leer")
    n = p[0]
    if n > 16 or len(p) < 1 + 8 * n + 8:
        raise EvalError(f"GET_DIAG: {n} Eintraege, aber nur {len(p)} Byte")
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
        raise EvalError(f"GET_DIAG: {len(p) - k} Byte Anhang ohne Kennung 'TF' (Serienfirmware liefert keinen)")
    return d


def parse_records(p: bytes) -> list:
    if len(p) % 20:
        raise EvalError(f"Datensaetze: Laenge {len(p)} kein Vielfaches von 20")
    out = []
    for i in range(0, len(p), 20):
        seq, boot, up, c, cd, temp, vb, cause, fl = struct.unpack_from("<IHIHHhHBB", p, i)
        out.append({"seq": seq, "boot_id": boot, "uptime": up, "raw": None if c == 0xFFFF else c, "c_diag": cd,
                    "temp": None if temp == -32768 or fl & 0x10 else temp / 100.0, "vbat": vb, "cause": cause, "sflags": fl})
    return out


def records_from_db(db: str, sensor: str) -> list:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        row = con.execute("SELECT addr FROM sensor WHERE addr=? OR id=?", (sensor, sensor)).fetchone()
        addr = row[0] if row else sensor
        q = ("SELECT seq, boot_id, uptime, raw, c_diag, temp, vbat, cause, sflags, t FROM reading "
             "WHERE sensor=? AND cause=? ORDER BY seq")
        cols = ("seq", "boot_id", "uptime", "raw", "c_diag", "temp", "vbat", "cause", "sflags", "t")
        return [dict(zip(cols, r)) for r in con.execute(q, (addr, CAUSE_TF3))]
    finally:
        con.close()


# ----------------------------------------------------------------------------------------------- Kriterien
def check_diag(d: dict, expect: str) -> list:
    """Liste (ok, Text) nach Testplan; nur Firmware-seitige Kriterien (Messwerte am Aufbau separat)."""
    t = d["tf"]
    res = []
    if t is None:
        return [(False, "kein TF-Anhang: keine Testfirmware")]
    codes = {e["code"] for e in d["entries"]}
    res.append((t["flash_ops_ready"] in (0, 0xFFFF), f"N-2: Flash-Ops vor der ersten Lastmessung = {t['flash_ops_ready']} (Soll 0)"))
    if expect == "tf1":
        res.append((t["variant"] == 1, f"Variante TF-{t['variant']} (Soll TF-1)"))
        res.append((t["tf1_trig"] >= 1, f"TF-1 ausgeloest: {t['tf1_trig']} x"))
        res.append((d["wdt_resets"] >= t["tf1_trig"] >= 1, f"wdt_resets = {d['wdt_resets']} >= Ausloesungen (Zaehler bleibt ueber Neustart)"))
        res.append((0x50 in codes, "Fehlerprotokoll enthaelt 0x50 WDT_RESET"))
        res.append((t["reset_reason"] == 2, f"Neustartgrund = {t['reset_reason_txt']} (Soll watchdog)"))
    elif expect.startswith("tf2"):
        want = {"tf2-late": 1, "tf2-early": 2, "tf2-hf": 3}[expect]
        res.append((t["variant"] == 2, f"Variante TF-{t['variant']} (Soll TF-2)"))
        res.append((t["tf2_mode"] == want, f"Modus {t['tf2_mode_txt']} (Soll {TF2_MODE[want]})"))
        res.append((t["tf2_cycles"] == 3, f"abnormale Neustarts bis Abschaltung = {t['tf2_cycles']} (Soll 3, ST-F6)"))
        res.append((t["backoffs"] >= 1, f"Abschaltungen wegen Reset-Schleife (backoffs) = {t['backoffs']}"))
        res.append((t["tf2_sd_ops"] == 0, f"Flash-Ops im abschaltenden Start = {t['tf2_sd_ops']} (Soll 0, F-W3a)"))
        if want == 2:
            res.append((t["tf2_max_ops"] == 0, f"Flash-Ops je Zyklus (frueh) = {t['tf2_max_ops']} (Soll 0, N-2)"))
        else:
            res.append((True, f"Flash-Ops je Zyklus (spaet) max. = {t['tf2_max_ops']}{'+' if t['tf2_max_ops'] == 31 else ''} (Information, PP-11)"))
        if want == 3:
            res.append((d["wdt_resets"] >= 2, f"HardFault -> Watchdog-Neustarts = {d['wdt_resets']} (Serie: Exception_handlerSpin)"))
    elif expect == "tf3":
        res.append((t["variant"] == 3 and t["sens_pwr_hold"] == 1, "Variante TF-3, SENS_PWR dauernd high"))
        res.append((t["tf3_reads"] > 0, f"TMP1075N-Lesungen = {t['tf3_reads']}"))
        res.append((t["tf3_err"] == 0, f"I2C-Fehler = {t['tf3_err']} (letzte Stelle: {t['tf3_stage_txt']}) (Soll 0, ST-W4)"))
    else:
        raise EvalError(f"unbekanntes --expect {expect}")
    return res


def eval_tf3(recs: list, period_s: int = 60) -> dict:
    if not recs:
        raise EvalError("keine TF-3-Datensaetze (cause 0x83)")
    temps = [r["temp"] for r in recs if r["temp"] is not None]
    seqs = [r["seq"] for r in recs]
    gaps = []
    for a, b in zip(recs, recs[1:]):
        if a["boot_id"] == b["boot_id"] and b["uptime"] - a["uptime"] > 1.5 * period_s:
            gaps.append((a["seq"], b["seq"], b["uptime"] - a["uptime"]))
    return {"n": len(recs), "seq_first": seqs[0], "seq_last": seqs[-1], "temp_invalid": len(recs) - len(temps),
            "i2c_err_max": max(r["c_diag"] or 0 for r in recs), "t_min": min(temps) if temps else None,
            "t_max": max(temps) if temps else None, "gaps": gaps,
            "ok": len(temps) == len(recs) and max(r["c_diag"] or 0 for r in recs) == 0}


# ----------------------------------------------------------------------------------------------- Simulation
def sim_diag(variant: int, **kw) -> bytes:
    """Synthetische GET_DIAG-Nutzlast wie fl_testfw.c (fuer --sim und Tests)."""
    entries = kw.get("entries", [])
    p = bytes([len(entries)]) + b"".join(struct.pack("<BBHI", *e) for e in entries)
    p += struct.pack("<HHHH", kw.get("wdt", 0), 0, 0, 0)
    t = {f: 0 for f in _TAIL_FIELDS}
    t.update(magic=b"TF", variant=variant, fmt=1, vdd_min=2950, vbat_rest=2980, vdd_min_ever=2950, boot_id=3,
             tf3_last=-32768, tf3_min=32767, tf3_max=-32768, sens_pwr_hold=1 if variant == 3 else 0)
    t.update({k: v for k, v in kw.items() if k in t})
    return p + _TAIL.pack(*(t[f] for f in _TAIL_FIELDS))


def sim_info(variant: int, build: int) -> bytes:
    p = bytearray(68)
    p[0] = 1; p[1:5] = bytes([0, 1]) + struct.pack("<H", 1); p[5:9] = struct.pack("<I", build); p[9] = 0x0B
    return bytes(p) + b"TF" + bytes([variant, 1])


def sim_records(n: int, err_at: int = -1) -> bytes:
    out = b""
    err = 0
    for i in range(n):
        bad = i == err_at
        err += bad
        out += struct.pack("<IHIHHhHBB", 100 + i, 3, 60 * (i + 1), 0xFFFF, err, -32768 if bad else 2150 + i,
                           2950, CAUSE_TF3, 0x10 if bad else 0)
    return out


# ----------------------------------------------------------------------------------------------- Ausgabe
def _print_checks(checks) -> bool:
    ok = True
    for good, txt in checks:
        print(f"  [{'ok' if good else 'NOK'}] {txt}")
        ok &= good
    return ok


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sim", action="store_true", help="synthetische Daten statt Eingabe (ohne Hardware)")
    ap.add_argument("--json", action="store_true", help="Ergebnis als JSON")
    sp = ap.add_subparsers(dest="cmd")
    for name in ("info", "diag"):
        s = sp.add_parser(name)
        s.add_argument("hex", nargs="?", help="Nutzlast als Hex")
        s.add_argument("--file", help="Datei mit Hex")
        if name == "diag":
            s.add_argument("--expect", choices=["tf1", "tf2-late", "tf2-early", "tf2-hf", "tf3"])
    s = sp.add_parser("tf3")
    s.add_argument("--db", help="Gateway-Datenbank fluidi.sqlite (nur lesend)")
    s.add_argument("--sensor", help="Adresse AA:BB:.. oder fluidi-/fl-tf3-Name")
    s.add_argument("--hex", help="Datei mit 20-Byte-Datensaetzen als Hex")
    a = ap.parse_args(argv)
    if not a.cmd:
        a.cmd = "diag" if a.sim else None
        if not a.cmd:
            ap.print_help()
            return 2
        a.hex = a.file = None
        a.expect = "tf2-late"

    def payload():
        if a.file:
            with open(a.file) as f:
                return _hex(f.read())
        if a.hex:
            return _hex(a.hex)
        raise EvalError("Hex oder --file angeben (oder --sim)")

    try:
        if a.cmd == "info":
            d = parse_info(sim_info(1, 9101) if a.sim else payload())
            print(json.dumps(d, indent=1) if a.json else
                  f"fw {d['fw']}+{d['fw_build']}  hw 0x{d['hw_rev']:02X}  boot {d['boot_id']}  reset {d['reset_reason']}  "
                  f"Testfirmware: {'TF-%d' % d['testfw'] if d['testfw'] else 'nein (Serie)'}"
                  f"{'' if not d['testfw'] or d['build_marks_testfw'] else '  WARNUNG: Build-Nummer ohne 9<n>xx-Kennung'}")
            return 0
        if a.cmd == "diag":
            if a.sim:
                p = sim_diag(2, entries=[(0x52, 0xBF, 4, 1)], tf2_trig=1, tf2_mode=1, tf2_cycles=3, tf2_max_ops=7,
                             tf2_sd_ops=0, backoffs=1, flash_ops_boot=5)
            else:
                p = payload()
            d = parse_diag(p)
            if a.json:
                print(json.dumps(d, indent=1))
            else:
                for e in d["entries"]:
                    print(f"  {e['name']:<16} detail {e['detail']:3d}  boot {e['boot_id']:5d}  t {e['uptime_s']} s")
                print(f"  wdt_resets {d['wdt_resets']}  brownouts {d['brownouts']}  auth_fail {d['auth_fail']}  button_stuck {d['button_stuck']}")
                t = d["tf"]
                if t:
                    print(f"  TF-{t['variant']}: meas {t['meas']} adv {t['adv']} conn {t['conn']} led_ms {t['led_ms']} charge_uc {t['charge_uc']}")
                    print(f"        reset {t['reset_reason_txt']} abn {t['abn_now']} ret 0x{t['ret_boot']:05X}  VDD min {t['vdd_min']} / Ruhe {t['vbat_rest']} / min gesamt {t['vdd_min_ever']} mV")
                    print(f"        Flash-Ops seit Start {t['flash_ops_boot']}, bis 1. Lastmessung {t['flash_ops_ready']}, backoffs {t['backoffs']}")
                    print(f"        TF-1 {t['tf1_trig']} x | TF-2 {t['tf2_trig']} x, {t['tf2_mode_txt']}, Neustarts {t['tf2_cycles']}, Ops/Zyklus max {t['tf2_max_ops']}, Ops Abschaltstart {t['tf2_sd_ops']}")
                    print(f"        TF-3 Lesungen {t['tf3_reads']}, I2C-Fehler {t['tf3_err']} ({t['tf3_stage_txt']}), T {t['tf3_min_c']}..{t['tf3_max_c']} degC, SENS_PWR dauernd {t['sens_pwr_hold']}")
            if a.expect:
                return 0 if _print_checks(check_diag(d, a.expect)) else 1
            return 0
        if a.cmd == "tf3":
            if a.sim:
                recs = parse_records(sim_records(10, err_at=4))
            elif a.db:
                if not a.sensor:
                    raise EvalError("--sensor angeben")
                recs = records_from_db(a.db, a.sensor)
            elif a.hex:
                with open(a.hex) as f:
                    recs = parse_records(_hex(f.read()))
            else:
                raise EvalError("--db/--sensor oder --hex angeben (oder --sim)")
            r = eval_tf3(recs)
            if a.json:
                print(json.dumps(r, indent=1))
            else:
                print(f"  {r['n']} Datensaetze seq {r['seq_first']}..{r['seq_last']}, T {r['t_min']}..{r['t_max']} degC, "
                      f"ungueltig {r['temp_invalid']}, I2C-Fehler max {r['i2c_err_max']}, Luecken > 90 s: {len(r['gaps'])}")
                print(f"  [{'ok' if r['ok'] else 'NOK'}] I2C ok (ST-W4): keine ungueltige Lesung")
            return 0 if r["ok"] else 1
    except EvalError as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
