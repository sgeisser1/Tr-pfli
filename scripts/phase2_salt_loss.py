#!/usr/bin/env python3
"""Phase 2, Recherche Elektronik: Leitfaehigkeitsverlust vs. Messfrequenz.

Imaginaerteil der Permittivitaet durch Ionenleitung: eps''_sigma = sigma / (2*pi*f*eps0).
Verhaeltnis eps''/eps' > 1 heisst: die Messung wird von der Leitfaehigkeit (Salz/Duenger)
dominiert statt von der Permittivitaet (Wasser). Grenzfrequenz f_c = sigma/(2*pi*eps0*eps').
Werte fuer sigma (Bulk-Leitfaehigkeit des feuchten Substrats) sind ANNAHMEN zur Illustration.
Aufruf: .venv/bin/python scripts/phase2_salt_loss.py
"""
import math

EPS0 = 8.854e-12
SIGMAS = [0.01, 0.05, 0.2]          # S/m (= 0.1, 0.5, 2 dS/m) ANNAHME
EPS_R = 25.0                        # eps' feuchtes Substrat, ANNAHME
FREQS = [25e3, 100e3, 1e6, 5e6, 10e6, 20e6, 70e6]

print("f [Hz]      " + "  ".join(f"sigma={s:5.2f} S/m" for s in SIGMAS) + "   (Werte: eps''/eps')")
for f in FREQS:
    row = [s / (2 * math.pi * f * EPS0) / EPS_R for s in SIGMAS]
    print(f"{f:10.3g}  " + "  ".join(f"{r:16.3g}" for r in row))
print()
for s in SIGMAS:
    fc = s / (2 * math.pi * EPS0 * EPS_R)
    print(f"sigma={s:5.2f} S/m: Grenzfrequenz f_c (eps''=eps') = {fc/1e6:8.2f} MHz")
