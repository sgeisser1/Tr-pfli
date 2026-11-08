#!/usr/bin/env python3
"""KiCad-Positionsdatei -> JLC-CPL (Designator, Mid X, Mid Y, Layer, Rotation).

Rotationskorrektur: Tabelle docs/references/matthewlai_JLCKicadTools_cpl_rotations_db_2026-11-07.csv
(DRITTQUELLE, github.com/matthewlai/JLCKicadTools, abgerufen 2026-11-07; erste passende Regex gewinnt,
Rotation_JLC = (Rotation_KiCad + Korrektur) mod 360, nur Oberseite).
Die Korrekturen sind NICHT von JLC belegt: in der JLC-Bestellung "Confirm Parts Placement" (Vorschau) je Teil pruefen.
Ausgabe zusaetzlich: <out>_rotationen.csv mit KiCad-Rotation, Korrektur und Quelle.
"""
import csv
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
DB = os.path.join(ROOT, "docs/references/matthewlai_JLCKicadTools_cpl_rotations_db_2026-11-07.csv")


# Projektregeln (nicht in der Drittquelle), vor der Tabelle gepruefte Reihenfolge; jede ist eine BESTELL-PRUEFUNG
# in der JLC-Vorschau ("Confirm Parts Placement"):
# - SOT-563 (U3, auch der abgeleitete fluidi-Footprint SOT-563_TI_DRL0006A): +180 wie SOT-363/SOT-353 mit gleicher
#   Pinanordnung und TI-Tape (DFM-Bericht phase4_layout_revb_dfm.md W-3). Bei 180-Grad-Fehler waeren V+ und GND vertauscht.
PROJECT_RULES = [(re.compile(r"^SOT-563"), 180.0, "PROJEKTREGEL W-3 (BESTELL-PRUEFUNG)")]


def load_db():
    rules = []
    for row in csv.reader(open(DB)):
        if not row or row[0].startswith("#") or row[0].lower().startswith("footprint"):
            continue
        try:
            rules.append((re.compile(row[0]), float(row[1])))
        except (ValueError, re.error):
            continue
    return rules


def main(src, dst):
    rules = load_db()
    rows = list(csv.DictReader(open(src)))
    rep = []
    with open(dst, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for r in rows:
            pkg = r["Package"]
            corr, pat = 0.0, ""
            for rx, c, why in PROJECT_RULES:
                if rx.search(pkg):
                    corr, pat = c, why
                    break
            for rx, c in ([] if pat else rules):
                if rx.search(pkg):
                    corr, pat = c, rx.pattern
                    break
            rot = (float(r["Rot"]) + corr) % 360
            layer = "Top" if r["Side"].lower().startswith("top") else "Bottom"
            w.writerow([r["Ref"], "%.4fmm" % float(r["PosX"]), "%.4fmm" % float(r["PosY"]), layer, "%.0f" % rot])
            rep.append([r["Ref"], pkg, r["Rot"], "%.0f" % corr, "%.0f" % rot, pat])
    with open(dst[:-4] + "_rotationen.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Ref", "Footprint", "Rot_KiCad", "Korrektur", "Rot_JLC", "Regel (DRITTQUELLE)"])
        w.writerows(rep)
    print("CPL: %d Teile, %d mit Korrektur" % (len(rep), sum(1 for x in rep if x[3] != "0")))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
