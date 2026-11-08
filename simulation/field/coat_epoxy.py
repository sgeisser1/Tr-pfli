"""Einfluss einer Epoxid-Beschichtung der Sonde (O-2, Phase 6) auf Spanne und Drift.

Geometrie: 4 Lagen 7628, SG gap 2 (Layout Rev B/C, REPORT.md Kap. 8), Lötstopplack 30 um.
Beschichtung rundum (Flächen + Kanten) mit Dicke t_coat und Er (ANNAHME-Band, siehe unten).
Das ist der ungünstige Fall: die Anleitung (MONTAGE_SENSOR.md Kap. 5a) verlangt nur Kanten + Spitze;
auf den Kanten liegt ≈ 1 % der Feldenergie (REPORT.md Kap. 4), dort ist der Einfluss vernachlässigbar.

Er-Band: 2.8 (MG 832HT TDS S. 3, 1 MHz) ... 4.5 (ANNAHME, ungefüllte Epoxide; ER2223-TDS nennt keine
Permittivität; Stycast 2651-40 W1/Cat 9 TDS S. 1: 3.9 @ 1 MHz, ER2188 TDS S. 2: 4.0 @ 50 Hz).

Aufruf: .venv/bin/python simulation/field/coat_epoxy.py   (ca. 1-2 min)
Ausgabe: results/coat_epoxy.csv, results/coat_epoxy.txt
"""
import csv
import multiprocessing as mp
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import xsec2d as X  # noqa: E402
from study2d import evaluate  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")

T_COAT = (0.0, 0.05, 0.1, 0.2, 0.3, 0.5)   # mm
ER_COAT = (2.8, 4.5)
KEYS = ("C_air", "C_dry", "C_wet", "C_water", "span", "fr4_moist", "lack_moist", "share_fr4_air")


def variants():
    V = []
    for er in ER_COAT:
        for t in T_COAT:
            g = X.Geometry(X.topo_sg(2), layers=4, t_coat=t, er_coat=er)
            V.append((f"4L SG gap2 coat{t} er{er}", g, {"t_coat": t, "er_coat": er, "gaps": False}))
    return V


def main():
    with mp.Pool(min(12, os.cpu_count() or 2)) as pool:
        rows = pool.map(evaluate, variants())
    base = {r["er_coat"]: r for r in rows if r["t_coat"] == 0.0}
    for r in rows:
        r["span_rel"] = 100 * (r["span"] / base[r["er_coat"]]["span"] - 1)
    os.makedirs(RES, exist_ok=True)
    cols = ["name", "t_coat", "er_coat"] + list(KEYS) + ["span_rel"]
    with open(os.path.join(RES, "coat_epoxy.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, delimiter=";", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    lines = ["Epoxid-Beschichtung rundum, 4L SG gap2 (pro m Elektrodenlaenge)",
             "t_coat[mm] Er   C_air  C_dry  C_wet  Spanne[pF/m] dSpanne[%] FR4-Drift[%Sp] Coat-Drift(Er+10%)[%Sp]"]
    for r in sorted(rows, key=lambda r: (r["er_coat"], r["t_coat"])):
        lines.append(f"{r['t_coat']:9.2f} {r['er_coat']:4.1f} {r['C_air']:6.1f} {r['C_dry']:6.1f} {r['C_wet']:6.1f}"
                     f" {r['span']:10.1f} {r['span_rel']:+10.1f} {r['fr4_moist']:12.2f} {r['lack_moist']:12.2f}")
    txt = "\n".join(lines)
    with open(os.path.join(RES, "coat_epoxy.txt"), "w") as f:
        f.write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
