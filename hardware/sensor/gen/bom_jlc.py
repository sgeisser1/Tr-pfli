#!/usr/bin/env python3
"""fluidi Sensor Rev B - BOM im JLC-Format aus dem Schaltplan erzeugen (kicad-cli sch export bom).

Ausgabe (hardware/sensor/out/):
  fluidi_sensor_bom_raw.csv   je Symbol (kicad-cli, alle Felder)
  fluidi_sensor_bom_jlc.csv   JLC-Format: Comment,Designator,Footprint,LCSC Part #  (ohne DNP, ohne Leiterplattenstrukturen)
  fluidi_sensor_bom_extra.csv nicht von JLC bestueckt: DNP-Positionen, Leiterplattenstrukturen, lokale Teile (Zelle)
Optional: --register schreibt docs/datasheets/_staging/INDEX_schaltplan_b.csv (Kopf aus HEADER.csv), mit JLC-Status
aus hardware/sensor/gen/jlc_check.json.
Aufruf: .venv/bin/python hardware/sensor/gen/bom_jlc.py [--register] [kicad-cli]
"""
import collections
import csv
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parts  # noqa: E402

PRJ = os.path.normpath(os.path.join(HERE, ".."))
ROOT = os.path.normpath(os.path.join(PRJ, "..", ".."))
OUT = os.path.join(PRJ, "out")
FIELDS = ["Reference", "Value", "Footprint", "LCSC", "MPN", "Hersteller", "JLC", "${DNP}", "${EXCLUDE_FROM_BOM}"]


def export_raw(cli):
    raw = os.path.join(OUT, "fluidi_sensor_bom_raw.csv")
    subprocess.run([cli, "sch", "export", "bom", "-o", raw, "--fields", ",".join(FIELDS),
                    "--labels", "Ref,Value,Footprint,LCSC,MPN,Hersteller,JLC,DNP,ExclBOM",
                    "--ref-range-delimiter", "", os.path.join(PRJ, "fluidi_sensor.kicad_sch")],
                   check=True, capture_output=True)
    with open(raw, newline="") as fh:
        return list(csv.DictReader(fh))


def ref_key(r):
    import re
    m = re.match(r"([A-Z]+)(\d+)", r)
    return (m.group(1), int(m.group(2))) if m else (r, 0)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    cli = args[0] if args else "kicad-cli"
    os.makedirs(OUT, exist_ok=True)
    rows = export_raw(cli)
    groups = collections.OrderedDict()
    extra = []
    for r in rows:
        dnp = r["DNP"].strip() not in ("", "0", "No", "no")
        excl = r["ExclBOM"].strip() not in ("", "0", "No", "no")
        if dnp or excl or not r["LCSC"]:
            extra.append((r["Ref"], r["Value"], r["Footprint"], r["LCSC"],
                          "DNP" if dnp else ("Leiterplattenstruktur/Pad" if excl else "ohne LCSC")))
            continue
        k = (r["Value"], r["Footprint"], r["LCSC"])
        groups.setdefault(k, []).append(r["Ref"])
    for c in parts.COMPONENTS:
        if c["key"] == "PCB":
            extra.append((c["ref"], c["val"], c["fp"], "", "Leiterplattenstruktur/Pad (nicht in BOM)"))
    jlc = os.path.join(OUT, "fluidi_sensor_bom_jlc.csv")
    with open(jlc, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Comment", "Designator", "Footprint", "LCSC Part #"])
        for (val, fp, lcsc), refs in sorted(groups.items(), key=lambda kv: ref_key(sorted(kv[1], key=ref_key)[0])):
            w.writerow([val, ",".join(sorted(refs, key=ref_key)), fp.split(":")[-1], lcsc])
    with open(os.path.join(OUT, "fluidi_sensor_bom_extra.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Value", "Footprint", "LCSC", "Grund"])
        for e in sorted(extra, key=lambda e: ref_key(e[0])):
            w.writerow(e)
        w.writerow(["-", "Panasonic CR2032", "-", "-", "lokal beschafft (D-006), nicht von JLC bestueckt"])
    n_place = sum(len(v) for v in groups.values())
    print(f"BOM JLC: {len(groups)} Positionen, {n_place} Bauteile bestueckt; {len(extra)} nicht bestueckt/Struktur "
          f"-> {os.path.relpath(jlc, ROOT)}")
    if "--register" in sys.argv:
        write_register(groups)


def write_register(groups):
    chk = json.load(open(os.path.join(HERE, "jlc_check.json")))
    head = open(os.path.join(ROOT, "docs", "datasheets", "_staging", "HEADER.csv")).read().strip()
    by_lcsc = collections.OrderedDict()
    for (val, fp, lcsc), refs in groups.items():
        by_lcsc.setdefault(lcsc, dict(refs=[], fp=fp, val=val))["refs"] += refs
    key_of = {v[2]: k for k, v in parts.PARTDB.items() if v[2]}
    lines = [head]

    def q(s):
        s = str(s)
        return '"' + s.replace('"', "'") + '"' if (";" in s or "," in s) else s
    for lcsc, d in by_lcsc.items():
        hst, mpn, _, cat, ds, descr = parts.PARTDB[key_of[lcsc]]
        j = chk.get(lcsc, {})
        refs = sorted(d["refs"], key=ref_key)
        stat = (f"JLC-Abfrage {chk.get('_abruf', '?')}: {j.get('library', '?')}{' preferred' if j.get('preferred') else ''}, "
                f"Lager {j.get('stock', '?')}, {j.get('price1', [[0, '?']])[0][1]} USD @1") if j else "JLC nicht abgefragt"
        lines.append(";".join(q(x) for x in [
            " ".join(refs), descr, hst, mpn, lcsc, cat, d["fp"], "siehe INDEX (bestehender Eintrag)", "-",
            "2026-11-07", ds, f"Schaltplan Rev B, Wert {d['val']}, {len(refs)} Stk; {stat}"]))
    path = os.path.join(ROOT, "docs", "datasheets", "_staging", "INDEX_schaltplan_b.csv")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"Register: {len(lines) - 1} Zeilen -> {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    main()
