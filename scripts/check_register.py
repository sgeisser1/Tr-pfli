#!/usr/bin/env python3
"""fluidi - Abgleich Bauteilregister docs/datasheets/INDEX.csv mit den Stuecklisten.

Prueft:
  1. JLC-BOM (production/rev-C/1_jlc_upload/fluidi_sensor_bom_jlc.csv): jeder Designator hat >= 1 Registerzeile mit
     gleichem Designator in 'Ref' UND gleicher LCSC-Nummer UND vorhandener lokaler Datei. Zusaetzlich: Footprint der
     BOM im Register-Gehaeusefeld erwaehnt (Hinweis), widerspruechliche Altzeilen (gleicher Designator, andere LCSC).
     Die Kopie hardware/sensor/out/fluidi_sensor_bom_jlc.csv muss inhaltsgleich sein.
  2. bom_extra (hardware/sensor/out/fluidi_sensor_bom_extra.csv): Leiterplattenstrukturen/DNP brauchen keinen
     Registereintrag; zugekaufte Teile (Zeilen ohne Designator, z. B. Zelle) brauchen Register + Datei.
  3. Gateway (hardware/gateway/BOM_GATEWAY.csv): Zuordnung Pos -> Register-Ref (GW_MAP unten); Datei muss existieren.
  4. Einkaufsliste (docs/manuals/EINKAUFSLISTE.csv, falls vorhanden): Spalte 'Register' -> Ref vorhanden.
  5. Format INDEX.csv: 12 Spalten (unquotiertes ';' in der Bemerkung), lokale Pfade vorhanden.
Ausgabe: Konsole + docs/reviews/phase6_register_abgleich.txt (Protokoll, erzeugt)
Aufruf : .venv/bin/python scripts/check_register.py [--strict]   (--strict: Exitcode 1 bei Luecken)
"""
import csv
import datetime
import filecmp
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
INDEX = P("docs", "datasheets", "INDEX.csv")
BOM_JLC = P("production", "rev-C", "1_jlc_upload", "fluidi_sensor_bom_jlc.csv")
BOM_JLC_OUT = P("hardware", "sensor", "out", "fluidi_sensor_bom_jlc.csv")
BOM_EXTRA = P("hardware", "sensor", "out", "fluidi_sensor_bom_extra.csv")
BOM_GW = P("hardware", "gateway", "BOM_GATEWAY.csv")
EINKAUF = P("docs", "manuals", "EINKAUFSLISTE.csv")
LOG = P("docs", "reviews", "phase6_register_abgleich.txt")

# Gateway-Position -> Register-Refs (alle muessen existieren, mind. eine mit lokaler Datei); None = kein Register noetig
GW_MAP = {
    "G1": ["GW-SBC1", "GW-SBC1-MD", "GW-SBC1-SCH"],
    "G2": ["GW-PSU"],
    "G3": ["GW-SD"],
    "G6": ["GW-CLIM1", "GW-CLIM1-BRD2 (Gateway G6, Empfehlung D-029)"],
    "G7": ["MAT-ASA"],
    "G8": None,     # Normteile (Handelsware), Masse ANNAHME im CAD
    "G9": ["GW-LED1 (Gateway, Vorschlag)", "GW-R1 (Gateway, Vorschlag)"],
    "G10": None,    # Werkstattbestand
    "G11": None,    # vorhanden, optional
}
# bom_extra: Gruende, die keinen Registereintrag brauchen
EXTRA_OK = ("Leiterplattenstruktur", "DNP")


def read_index():
    rows, fmt = [], []
    with open(INDEX, encoding="utf-8") as fh:
        for n, x in enumerate(csv.reader(fh, delimiter=";"), 1):
            if n == 1 or not x:
                continue
            if len(x) != 12:
                fmt.append((n, len(x), x[0]))
                x = x[:11] + [";".join(x[11:])]
            rows.append(dict(n=n, ref=x[0].strip(), func=x[1], hst=x[2], tn=x[3], lcsc=x[4].strip(), be=x[5],
                             geh=x[6], path=x[10].strip(), bem=x[11]))
    return rows, fmt


def ref_tokens(ref):
    """'C6 C7 C8 (Kandidat Rev B)' -> {'C6','C7','C8'}; Klammerinhalt ignoriert."""
    return set(re.sub(r"\(.*?\)", " ", ref).replace(",", " ").split())


def paths_ok(path):
    if not path or path == "-" or "NICHT" in path.upper():
        return False, []
    ps = [q.strip() for q in path.split(" + ")]
    miss = [q for q in ps if not os.path.exists(P(q))]
    return not miss, miss


def main():
    out = []
    o = out.append
    gaps = 0
    reg, fmt = read_index()
    by_ref = {}
    for r in reg:
        by_ref.setdefault(r["ref"], []).append(r)
    o(f"fluidi Registerabgleich, {datetime.datetime.now():%Y-%m-%d %H:%M}, scripts/check_register.py")
    o(f"INDEX.csv: {len(reg)} Zeilen")
    o("")

    # 1 JLC-BOM
    o("== 1 JLC-BOM " + os.path.relpath(BOM_JLC, ROOT))
    same = filecmp.cmp(BOM_JLC, BOM_JLC_OUT, shallow=False)
    o(f"   Kopie hardware/sensor/out/fluidi_sensor_bom_jlc.csv inhaltsgleich: {'ja' if same else 'NEIN'}")
    if not same:
        gaps += 1
    bom = list(csv.DictReader(open(BOM_JLC, encoding="utf-8")))
    n_ok = 0
    for b in bom:
        lcsc = b["LCSC Part #"].strip()
        fp = b["Footprint"].strip()
        for d in [x.strip() for x in b["Designator"].split(",")]:
            cand = [r for r in reg if d in ref_tokens(r["ref"])]
            match = [r for r in cand if r["lcsc"] == lcsc]
            good = [r for r in match if paths_ok(r["path"])[0]]
            other = sorted({r["lcsc"] for r in cand if r["lcsc"] not in (lcsc, "", "-")})
            if good:
                n_ok += 1
                fp_hit = any(fp.split(":")[-1] in (r["geh"] + r["bem"]) for r in match)
                note = "" if fp_hit else f"  (Hinweis: Footprint {fp} nicht im Registerfeld Gehaeuse/Bemerkung)"
                alt = f"  (Altzeilen mit anderer LCSC: {', '.join(other)})" if other else ""
                o(f"   ok   {d:4s} {lcsc:10s} Zeile {good[-1]['n']:3d} -> {good[-1]['path']}{note}{alt}")
            else:
                gaps += 1
                if match:
                    o(f"   LUECKE {d} {lcsc}: Registerzeile(n) {[r['n'] for r in match]} ohne vorhandene Datei "
                      f"({[paths_ok(r['path'])[1] or r['path'] for r in match]})")
                elif cand:
                    o(f"   LUECKE {d} {lcsc}: Register nennt nur andere LCSC {other} (Zeilen {[r['n'] for r in cand]})")
                else:
                    o(f"   LUECKE {d} {lcsc}: kein Registereintrag")
    o(f"   -> {n_ok} Designatoren ok")
    o("")

    # 2 bom_extra
    o("== 2 bom_extra " + os.path.relpath(BOM_EXTRA, ROOT))
    for b in csv.DictReader(open(BOM_EXTRA, encoding="utf-8")):
        d, val, why = b["Designator"].strip(), b["Value"].strip(), b["Grund"].strip()
        if any(k in why for k in EXTRA_OK):
            o(f"   n/a  {d:4s} {val} ({why})")
            continue
        # zugekauftes Teil: Hersteller + Teilenummer aus 'Value' (z. B. 'Panasonic CR2032')
        words = val.split()
        hits = [r for r in reg if all(w.lower() in (r["hst"] + " " + r["tn"]).lower() for w in words)]
        good = [r for r in hits if paths_ok(r["path"])[0]]
        if good:
            o(f"   ok   {val}: Zeile {good[0]['n']} -> {good[0]['path']}")
        else:
            gaps += 1
            o(f"   LUECKE {val}: kein Registereintrag mit Datei")
    o("")

    # 3 Gateway
    o("== 3 Gateway " + os.path.relpath(BOM_GW, ROOT))
    for g in csv.DictReader(open(BOM_GW, encoding="utf-8"), delimiter=";"):
        pos = g["Pos"]
        if pos.startswith("V"):
            o(f"   n/a  {pos:4s} {g['Teil'][:60]} (Versand)")
            continue
        if pos not in GW_MAP:
            gaps += 1
            o(f"   LUECKE {pos}: keine Zuordnung in GW_MAP (scripts/check_register.py)")
            continue
        refs = GW_MAP[pos]
        if refs is None:
            o(f"   n/a  {pos:4s} {g['Hersteller_Typ'][:60]} (Handelsware/Bestand, kein Register noetig)")
            continue
        missing_ref = [x for x in refs if x not in by_ref]
        files = [(x, r["path"], paths_ok(r["path"])) for x in refs if x in by_ref for r in by_ref[x]]
        with_file = [f for f in files if f[2][0]]
        if missing_ref:
            gaps += 1
            o(f"   LUECKE {pos}: Register-Ref fehlt: {missing_ref}")
        elif not with_file:
            gaps += 1
            o(f"   LUECKE {pos} {g['Hersteller_Typ'][:50]}: Register {refs} ohne lokale Datei "
              f"({'; '.join(f[1] for f in files)})")
        else:
            o(f"   ok   {pos:4s} {g['Hersteller_Typ'][:50]} -> {', '.join(sorted({f[1] for f in with_file}))}")
            for f in files:
                if not f[2][0]:
                    o(f"        (Hinweis: {f[0]} ohne Datei: {f[1]})")
    o("")

    # 4 Einkaufsliste
    if os.path.exists(EINKAUF):
        o("== 4 Einkaufsliste " + os.path.relpath(EINKAUF, ROOT))
        for e in csv.DictReader(open(EINKAUF, encoding="utf-8"), delimiter=";"):
            refs = [s.strip() for s in e["Register"].split(" + ")] if e["Register"].strip() not in ("", "-") else []
            if not refs:
                o(f"   --   {e['ID']:4s} {e['Teil'][:55]} (kein Register angegeben)")
                continue
            miss = [x for x in refs if x not in by_ref]
            if miss:
                gaps += 1
                o(f"   LUECKE {e['ID']}: Register-Ref fehlt {miss}")
            else:
                hasf = any(paths_ok(r["path"])[0] for x in refs for r in by_ref[x])
                o(f"   ok   {e['ID']:4s} {', '.join(refs)[:70]}{'' if hasf else '  (ohne lokale Datei)'}")
        o("")

    # 5 Format / Pfade
    o("== 5 Format INDEX.csv")
    if fmt:
        o(f"   Hinweis: {len(fmt)} Zeilen mit != 12 Spalten (unquotiertes ';' in der Bemerkung), z. B. "
          + ", ".join(f"Z.{n} {r}" for n, _, r in fmt[:8]) + (" ..." if len(fmt) > 8 else ""))
    else:
        o("   ok: alle Zeilen 12 Spalten")
    bad = [(r["n"], r["ref"], m) for r in reg for m in paths_ok(r["path"])[1]]
    o(f"   Pfade angegeben, Datei fehlt: {len(bad)}" + ("" if not bad else ": " + "; ".join(f"Z.{n} {f} ({m})" for n, f, m in bad)))
    nofile = [r for r in reg if r["path"] in ("", "-") or "NICHT" in r["path"].upper()]
    o(f"   Zeilen ohne lokale Datei (Normteile, nicht herunterladbar, Handelsware): {len(nofile)}")
    o("")
    o(f"ERGEBNIS: {gaps} Luecke(n)")
    txt = "\n".join(out) + "\n"
    print(txt)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    open(LOG, "w", encoding="utf-8").write(txt)
    if "--strict" in sys.argv and gaps:
        sys.exit(1)


if __name__ == "__main__":
    main()
