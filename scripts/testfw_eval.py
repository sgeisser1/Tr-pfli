#!/usr/bin/env python3
"""fluidi – Auswertung der TESTFIRMWARE (Testplan docs/reviews/phase5_testplan_prototyp.md Anhang A, TF-1..TF-4).

Dekodiert die Rohdaten, die die Testfirmware liefert, und prueft die Kriterien des Testplans:

  info    GET_INFO-Antwort (0x90) als Hex: 68 Byte (PROTOCOL 5.5) + Anhang "TF" <n> <fmt>
  diag    GET_DIAG-Antwort (0x98) als Hex: Fehlerprotokoll (PROTOCOL 5.7) + TF-4-Anhang (68 Byte, fl_testfw.c)
          --expect tf1 | tf2-late | tf2-early | tf2-hf | tf3   -> Kriterien PT5.12 / PT11.07 / PT11.19
  tf3     TF-3-Datensaetze (cause 0x83) aus der Gateway-Datenbank (--db fluidi.sqlite --sensor <addr|id>)
          oder als Hex (20-Byte-Datensaetze, PROTOCOL 5.6, --hex)

Woher die Daten kommen: PWA Sensoren > "Diagnose abrufen" bzw. `POST /api/v1/sensors/{id}/diag` (Gateway fragt beim
naechsten Kontakt GET_INFO + GET_DIAG ab und speichert die Rohdaten in der Tabelle `sensor_diag`). Eingabe dann
  --db fluidi.sqlite --sensor <addr|fluidi-XXXX|fl-tf<n>-XXXX>   (neueste gespeicherte Diagnose, nur lesend)
  --file diagnose.json                                          (JSON-Download der PWA / GET /sensors/{id}/diag)
  --file x.hex | <hex>                                          (Rohdaten als Hex)
Die Host-Tests (`make -C firmware/sensor/tests`) legen echte Nutzlasten der simulierten Testfirmware unter
firmware/sensor/tests/build/tf<n>_*.hex ab.

Dekodierung: firmware/gateway/fluidi_gw/sensordiag.py (dieselbe wie im Gateway, hier nur importiert).

Ohne Hardware: `--sim` erzeugt synthetische Nutzlasten (Python-Nachbildung) und wertet sie aus.
Aufruf: .venv/bin/python scripts/testfw_eval.py diag --file tf2.hex --expect tf2-late
       .venv/bin/python scripts/testfw_eval.py diag --db /var/lib/fluidi/fluidi.sqlite --sensor fl-tf2-ABCD --expect tf2-late
"""
import argparse
import json
import os
import sqlite3
import sys

# Dekodierung NICHT hier duplizieren: einzige Quelle ist das Gateway-Modul fluidi_gw/sensordiag.py (nur stdlib)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "firmware", "gateway"))
from fluidi_gw import sensordiag as D  # noqa: E402

RESET, ERR, TF2_MODE, TF3_STAGE = D.RESET, D.ERR, D.TF2_MODE, D.TF3_STAGE
TF2_MAX_SAT = 15   # fl_testfw.h FL_TF_RET_MAX_SAT (4 bit; Bit 13 = FL_RET_FAULT, O-5)
CAUSE_TF3, TAIL_LEN, INFO_LEN = D.CAUSE_TF3, D.TAIL_LEN, D.INFO_LEN
EvalError = D.DecodeError
_hex = D.from_hex
parse_info, parse_diag, parse_records = D.parse_info, D.parse_diag, D.parse_records
sim_diag, sim_info, sim_records = D.sim_diag, D.sim_info, D.sim_records


def _sensor_key(sensor: str) -> str:
    """fl-tf<n>-XXXX (Name der Testfirmware) -> fluidi-XXXX (Kennung im Gateway, aus der Adresse gebildet)."""
    return "fluidi-" + sensor[-4:].upper() if D.testfw_from_name(sensor) else sensor


def _addr(con, sensor: str) -> str:
    key = _sensor_key(sensor)
    row = con.execute("SELECT addr FROM sensor WHERE addr=? OR id=?", (key.upper(), key)).fetchone()
    if row:
        return row[0]
    # entkoppelter Sensor: Kennung aus den gespeicherten Diagnosen
    row = con.execute("SELECT sensor FROM sensor_diag WHERE sensor=? OR json_extract(doc, '$.sensor_id')=? "
                      "ORDER BY id DESC LIMIT 1", (key.upper(), key)).fetchone() if _has_table(con, "sensor_diag") else None
    return row[0] if row else key


def _has_table(con, name) -> bool:
    return con.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def diag_from_db(db: str, sensor: str, nth: int = 0) -> dict:
    """Gespeicherte Diagnose (POST /sensors/{id}/diag) aus der Gateway-Datenbank, nth = 0 neueste."""
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        if not _has_table(con, "sensor_diag"):
            raise EvalError("Datenbank ohne Tabelle sensor_diag (Gateway zu alt?)")
        addr = _addr(con, sensor)
        row = con.execute("SELECT info_hex, diag_hex, t FROM sensor_diag WHERE sensor=? ORDER BY id DESC LIMIT 1 OFFSET ?",
                          (addr, nth)).fetchone()
        if not row:
            raise EvalError(f"keine Diagnose fuer {sensor} gespeichert (PWA: Sensoren > Diagnose abrufen)")
        return {"info_hex": row[0], "diag_hex": row[1], "t": row[2]}
    finally:
        con.close()


def diag_from_json(text: str) -> dict:
    """JSON-Download der PWA bzw. GET /sensors/{id}/diag (Objekt oder Liste, neueste zuerst)."""
    try:
        js = json.loads(text)
    except ValueError as e:
        raise EvalError(f"kein JSON: {e}") from e
    if isinstance(js, list):
        if not js:
            raise EvalError("JSON-Liste leer")
        js = js[0]
    if not isinstance(js, dict) or not ("info_hex" in js or "diag_hex" in js):
        raise EvalError("JSON ohne info_hex/diag_hex (Format SensorDiag, app/api/openapi.yaml)")
    return js


def records_from_db(db: str, sensor: str) -> list:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        addr = _addr(con, sensor)
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
            res.append((True, f"Flash-Ops je Zyklus (spaet) max. = {t['tf2_max_ops']}{'+' if t['tf2_max_ops'] == TF2_MAX_SAT else ''} (Information, PP-11)"))
        if want == 3:
            # O-5: fl_fault_handler -> Systemreset, Grund hardfault -> Eintraege 0x52 mit detail = abn (1, 2);
            # 0x52/0xBF = Abschaltung wegen Reset-Schleife, zaehlt nicht. Alter Watchdog-Umweg haette 0x50 erzeugt.
            hf = [e for e in d["entries"] if e["code"] == 0x52 and e["detail"] != 0xBF]
            res.append((len(hf) >= 2, f"HardFault-Neustarts mit Grund hardfault (0x52) = {len(hf)} (Soll >= 2, O-5: "
                                      f"sofortiger Neustart statt Watchdog; wdt_resets gesamt = {d['wdt_resets']})"))
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
        s.add_argument("--file", help="Datei mit Hex oder JSON (Download der PWA)")
        s.add_argument("--db", help="Gateway-Datenbank fluidi.sqlite (nur lesend): neueste gespeicherte Diagnose")
        s.add_argument("--sensor", help="mit --db: Adresse AA:BB:.., fluidi-XXXX oder fl-tf<n>-XXXX")
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
        a.hex = a.file = a.db = a.sensor = None
        a.expect = "tf2-late"

    def payload():
        key = "info_hex" if a.cmd == "info" else "diag_hex"
        if a.db:
            if not a.sensor:
                raise EvalError("--sensor angeben")
            hx = diag_from_db(a.db, a.sensor)[key]
        elif a.file:
            with open(a.file) as f:
                text = f.read()
            if not text.lstrip().startswith(("{", "[")):
                return _hex(text)
            hx = diag_from_json(text).get(key)
        elif a.hex:
            return _hex(a.hex)
        else:
            raise EvalError("Hex, --file oder --db/--sensor angeben (oder --sim)")
        if not hx:
            raise EvalError(f"{key} fehlt (Sensor hat {'GET_INFO' if a.cmd == 'info' else 'GET_DIAG'} nicht beantwortet)")
        return _hex(hx)

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
