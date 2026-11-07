"""Schnelles Zeitbereichsmodell des RC-Schmitt-Oszillators mit verlustbehafteter Sonde.

Gleiche Schaltung und Annahmen wie probe_osc.py (ngspice-Verhaltensmodell): idealer Schmitt-Inverter
(VT+ 1.68 V, VT- 0.99 V bei 3 V, TI_SN74LVC1G14_Datasheet_SCES218AA.pdf S.7 Tab. 5.5 Mittelwerte laut
research_elektronik.md 6.3), Ausgangswiderstand 30 Ohm (ANNAHME), tpd = 0, R vom Ausgang an den Eingang,
am Eingang Cpar + Cref + Sonde (C0 || (Ci in Serie mit (Cs || Rs))).

Zwischen zwei Schaltflanken ist die Schaltung linear: M x' = A x + b mit x = (v_in, v_n1). Die Loesung ist
eine Summe aus zwei Exponentialfunktionen; die Schaltzeit wird mit brentq exakt bestimmt.
Validierung gegen ngspice: messkette_salz.py Teil 0 (Abweichung der Periode < 0.3 %).
"""
import math

import numpy as np
from scipy.optimize import brentq

VDD = 3.0
VTP, VTN = 1.68, 0.99
R_OUT = 30.0


def _segment(x0, vout, R, Ca, Ci, Cs, Rs):
    """Liefert Funktion v_in(t), x(t) fuer einen Abschnitt mit konstantem Ausgang vout."""
    M = np.array([[Ca + Ci, -Ci], [-Ci, Ci + Cs]])
    A = np.array([[-1.0 / R, 0.0], [0.0, -1.0 / Rs]])
    b = np.array([vout / R, 0.0])
    Mi = np.linalg.inv(M)
    F = Mi @ A
    g = Mi @ b
    xeq = -np.linalg.solve(F, g)
    lam, V = np.linalg.eig(F)
    lam = lam.real
    V = V.real
    c = np.linalg.solve(V, np.asarray(x0) - xeq)

    def x(t):
        return xeq + V @ (c * np.exp(lam * t))
    return x


def period(Ca, Ci, Cs, Rs, R=10e3, vdd=VDD, vtp=VTP, vtn=VTN, n_half=80, n_avg=20, rout=R_OUT, tpd=0.0):
    """Periodendauer im eingeschwungenen Zustand [s]. Ca = Cpar + Cref + C0 (direkt am Eingang).
    tpd: Laufzeit je Flanke; der Ausgang kippt erst tpd nach dem Erreichen der Schwelle (Ueberschwingen des
    Eingangsknotens wird damit korrekt abgebildet)."""
    Rt = R + rout
    x = np.array([0.0, 0.0])
    t_edges = []
    t = 0.0
    out_high = True
    tau_max = Rt * (Ca + Ci + Cs) * 50
    for _ in range(n_half):
        vout = vdd if out_high else 0.0
        thr = vtp if out_high else vtn
        xf = _segment(x, vout, Rt, Ca, Ci, Cs, Rs)
        f = (lambda tt: xf(tt)[0] - thr) if out_high else (lambda tt: thr - xf(tt)[0])
        # Klammer suchen
        hi = Rt * Ca * 0.01 + 1e-12
        while f(hi) < 0:
            hi *= 1.6
            if hi > tau_max:
                raise RuntimeError("keine Schwellenueberschreitung")
        dt = brentq(f, 0.0, hi, xtol=1e-15, rtol=1e-12) + tpd
        x = xf(dt)
        t += dt
        if out_high:
            t_edges.append(t)  # Ausgang kippt nach low bei Erreichen VT+
        out_high = not out_high
    te = np.array(t_edges[-(n_avg + 1):])
    return float((te[-1] - te[0]) / n_avg)


def probe_params(fit, eps, sig_b, scale=1.0):
    """Ersatzschaltbild Sonde (PROBE_CAPACITANCE.md Kap. 3). scale: Anteil der Sondenlaenge im Substrat (1 = voll)."""
    c0, ci, cg = fit["C0_pF"] * 1e-12, fit["Ci_pF"] * 1e-12, fit["Cg_pF"] * 1e-12
    cs = eps * cg
    rs = 8.8541878128e-12 / (sig_b * cg) if sig_b > 0 else 1e15
    return c0, ci, cs, rs


def y_probe(fit, eps, sig_b, f):
    """Komplexe Admittanz der Sonde (Ersatzschaltbild)."""
    c0, ci, cs, rs = probe_params(fit, eps, sig_b)
    w = 2 * math.pi * f
    ys = 1.0 / rs + 1j * w * cs
    return 1j * w * c0 + 1.0 / (1.0 / (1j * w * ci) + 1.0 / ys)
