#!/usr/bin/env python3
"""fluidi - Diodenmodelle fuer die RGB-Status-LED (Phase 3, Machbarkeit RGB).

Aufruf:  .venv/bin/python simulation/spice/led_rgb/fit_led_models.py
Schreibt simulation/spice/led_rgb/led_models.inc und gibt die Fit-Parameter aus.

Quelle der Kurvenform: NationStar FC-B1010RGBT-HG, Volt-Ampere-Kennlinie
  docs/datasheets/NationStar_FC-B1010RGBT-HG_Datasheet_A1.pdf, Datenblatt-S. 3/13 (PDF-S. 4).
  Digitalisiert bei 1, 2, 5, 10 mA. Die Y-Achse ist nur mit "1" und "10" beschriftet und hat 9 gleiche
  Teilungen -> als LINEAR 1..10 mA gelesen (ANNAHME). Diese Lesart ergibt bei 1 mA hoehere VF als die
  logarithmische Lesart (konservativ). Werte bei 1 mA und 10 mA sind von der Lesart unabhaengig.
Lage der Kennlinie (Exemplarstreuung): gewaehltes Teil TUOZHAN P4-1615G2B2R4TS2-06T-001-24 (C7496855),
  VF bei IF = 5 mA: R(SR) 1.8-2.2 V, G 2.5-2.9 V, B 2.6-3.0 V
  docs/datasheets/TUOZHAN_P4-1615G2B2R4TS2-06T-001-24_Datasheet_A0.pdf, S. 5, Tab. CHARACTERISTICS.
  Die NationStar-Kurvenform wird starr auf min/mitte/max bei 5 mA verschoben (ANNAHME: gleiche Chip-
  technologie, gleiche Steigung). Unter 1 mA ist jedes Modell eine Extrapolation (ANNAHME) ->
  PROTOTYP-PRUEFUNG: I-U-Kennlinie 0.05-5 mA an 10 Exemplaren messen.
"""
import math
import os

import numpy as np
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
VT = 0.025852  # kT/q bei 27 degC (ngspice-Standardtemperatur)

# (I [A], VF [V]) digitalisiert, lineare Achsen-Lesart
PTS = {
    "R": [(1e-3, 1.805), (2e-3, 1.830), (5e-3, 1.900), (10e-3, 1.974)],
    "G": [(1e-3, 2.354), (2e-3, 2.440), (5e-3, 2.650), (10e-3, 2.894)],
    "B": [(1e-3, 2.628), (2e-3, 2.688), (5e-3, 2.840), (10e-3, 2.994)],
}
# TUOZHAN VF bei 5 mA (min, mitte, max), S. 5
TZ5 = {"R": (1.8, 2.0, 2.2), "G": (2.5, 2.7, 2.9), "B": (2.6, 2.8, 3.0)}


def fit(points):
    I = np.array([p[0] for p in points])
    V = np.array([p[1] for p in points])

    def res(x):
        ln_is, n, rs = x
        return n * VT * (np.log(I) - ln_is) + I * rs - V

    r = least_squares(res, x0=[math.log(1e-20), 2.0, 20.0],
                      bounds=([math.log(1e-45), 1.0, 0.0], [math.log(1e-8), 20.0, 200.0]))
    ln_is, n, rs = r.x
    return math.exp(ln_is), n, rs, float(np.max(np.abs(r.fun)))


def vf(i, is_, n, rs):
    return n * VT * math.log(i / is_) + i * rs


def main():
    lines = ["* fluidi RGB-LED-Modelle, erzeugt von fit_led_models.py (nicht von Hand aendern)",
             "* Kurvenform NationStar FC-B1010RGBT-HG S.3/13, verschoben auf TUOZHAN C7496855 VF@5mA (S.5)"]
    print("| Farbe | IS [A] | N | RS [Ohm] | max. Fitfehler [mV] | VF(5 mA) Kurve | Offsets min/mitte/max [V] |")
    print("|---|---|---|---|---|---|---|")
    for c, pts in PTS.items():
        is_, n, rs, err = fit(pts)
        v5 = vf(5e-3, is_, n, rs)
        offs = [t - v5 for t in TZ5[c]]
        print(f"| {c} | {is_:.3e} | {n:.2f} | {rs:.1f} | {err*1e3:.1f} | {v5:.3f} | "
              + " / ".join(f"{o:+.3f}" for o in offs) + " |")
        lines.append(f".model D{c} D(IS={is_:.4e} N={n:.4f} RS={rs:.3f} BV=5 IBV=10u)")
        for name, o in zip(("MIN", "MID", "MAX"), offs):
            lines.append(f".param OFF_{c}_{name}={o:.4f}")
    for c, pts in PTS.items():
        is_, n, rs, _ = fit(pts)
        print(f"{c}: VF(0.1/0.5/1/2 mA) Kurvenform = " +
              ", ".join(f"{vf(i, is_, n, rs):.3f}" for i in (0.1e-3, 0.5e-3, 1e-3, 2e-3)) + " V")
    with open(os.path.join(HERE, "led_models.inc"), "w") as f:
        f.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
