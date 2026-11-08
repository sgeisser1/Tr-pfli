"""Abschaetzung: Verstimmung der AN043-IFA (AE1) durch die Kappe Phase 5 (P5-M1/M3), Abstand 0.76 -> 0.70 mm.

Fragestellung (Phase 5, Mechanik check_sensor.txt Pkt. 6): Der neue Mantel um die Membran-Senkung
(fluidi_sensor.py, Wand 0.8, Achse x -2.2) liegt 0.70 mm ueber der Kupferoberkante des oberen Arms L3
(W2 = 0.5 mm, Abstand D2 = 0.3 mm zur Platinenkante, AN043 S. 4 Abb. 3 / Tab. 1).

Methode (nachvollziehbar, bewusst einfach):
1) 2D-elektrostatischer Querschnitt (scikit-fem, Tensor-Dreiecksnetz) senkrecht zum Arm L3:
   Leiter L3 auf F (phi = 1), Masseflaeche ab 4.9 mm unter der Kupferkante auf allen Lagen (phi = 0,
   Keepout-Ende Y 5.20 laut LAYOUT_REV_B.md Kap. 2; Kupferoberkante 0.3 mm unter der Platinenkante).
   C' = eps0 * Energie. Relevant ist nur das Verhaeltnis dC'/C' zwischen den Kunststoff-Varianten.
2) Stoerungsrechnung: df/f ~ -1/2 * w * dC'/C', w = Anteil der elektrischen Feldenergie der Antenne im
   ueberdeckten Stueck von L3. ANNAHME: IFA als lambda/4-Leitung ab Kurzschluss, Spannung ~ sin(pi s / 2L),
   Energie ~ sin^2; Leiterlaenge L aus AN043 Tab. 1 entlang des Pfads.

Materialwerte:
- FR4 eps_r 4.25 @ 1 GHz: docs/references/Kingboard_KB-6160A_TechnicalInformation.pdf S. 1 (Dielectric Constant).
- ASA eps_r: im lokalen TDS (BambuLab_ASA_TechnicalDataSheet_V2.0.pdf) NICHT angegeben -> ANNAHME 3.0,
  Sweep 2.5 ... 3.7 (Redteam K-9 nannte ~3, ebenfalls ohne Quelle). FDM 100 % Infill (TDS S. 2) -> obere Schranke.

Ausfuehren: .venv/bin/python simulation/field/ant_kappe_p5.py
"""
from __future__ import annotations

import math

import numpy as np
from skfem import Basis, BilinearForm, ElementTriP0, ElementTriP1, MeshTri, condense, solve, asm
from skfem.helpers import dot, grad

EPS0 = 8.854e-12
ER_FR4 = 4.25           # Kingboard KB-6160A S. 1, @1 GHz
T_PCB = 1.6             # fluidi_params.py PCB T
T_CU = 0.035
W_L3 = 0.50             # AN043 Tab. 1 W2
D2 = 0.30               # AN043 Tab. 1 D2 (Kupfer -> Platinenkante)
GND_EDGE = -4.9         # Massekante relativ zur Kupferoberkante (53.2 - 48.3)


def axis(a, b, fine_regions, h_fine=0.02, h_coarse=0.25):
    """Nichtuniforme Stuetzstellen: fein in fine_regions [(lo, hi)], sonst grob."""
    pts = [a]
    x = a
    while x < b:
        h = h_coarse
        for lo, hi in fine_regions:
            if lo - 0.6 <= x <= hi + 0.6:
                h = h_fine
        x = min(b, x + h)
        pts.append(x)
    return np.array(pts)


# Koordinaten: u = senkrecht zur Platinenkante (u = 0 Kupferoberkante, u = D2 Platinenkante, u > 0 Kappe),
#              v = Dicke (v = 0 F-Oberflaeche, v = T_PCB B-Seite, v < 0 vor der bestueckten Seite)
U = axis(-8.0, 6.0, [(-W_L3, 1.2), (GND_EDGE, GND_EDGE)])
V = axis(-6.0, 7.6, [(-T_CU, 1.6)])
mesh = MeshTri.init_tensor(U, V)


def eps_field(plastic, er_asa):
    """plastic: Liste von Rechtecken (u0, u1, v0, v1) mit ASA."""
    b0 = Basis(mesh, ElementTriP0())
    c = mesh.p[:, mesh.t].mean(axis=1)
    u, v = c
    er = np.ones(mesh.t.shape[1])
    for (u0, u1, v0, v1) in plastic:
        er[(u >= u0) & (u <= u1) & (v >= v0) & (v <= v1)] = er_asa
    er[(u <= D2) & (v >= 0) & (v <= T_PCB)] = ER_FR4
    return b0, er


def capacitance(plastic, er_asa):
    basis = Basis(mesh, ElementTriP1())
    b0, er = eps_field(plastic, er_asa)
    erf = b0.interpolate(er)

    @BilinearForm
    def a(u, v, w):
        return w['er'] * dot(grad(u), grad(v))

    K = asm(a, basis, er=erf)
    x, y = mesh.p
    sig = (x >= -W_L3 - 1e-9) & (x <= 1e-9) & (y >= -T_CU - 1e-9) & (y <= 1e-9)
    gnd = (x <= GND_EDGE + 1e-9) & (((y >= -T_CU - 1e-9) & (y <= 1e-9)) | ((y >= T_PCB - 1e-9) & (y <= T_PCB + T_CU)) |
                                    (np.abs(y - 0.21) < 0.011) | (np.abs(y - T_PCB + 0.21) < 0.011))
    bnd = mesh.boundary_nodes()
    phi = np.zeros(mesh.p.shape[1])
    phi[sig] = 1.0
    D = np.unique(np.concatenate([np.where(sig)[0], np.where(gnd)[0], bnd]))
    phi = solve(*condense(K, x=phi, D=D))
    return EPS0 * phi @ (K @ phi) * 1e12   # pF/m (2D: 1/2 C V^2 = 1/2 eps0 int er |grad|^2)


BIG = 50.0
VARIANTS = {
    "ohne Kunststoff": [],
    # Rev C (vor P5-M3): Tastenblock vor F (v <= -0.4) ab 0.70 ueber Kupfer, ueber ganzer Dicke ab 1.00
    "Rev C Block (0.70 vor F, 1.00 ueber Kante)": [(0.70, BIG, -BIG, -0.4), (1.00, BIG, -BIG, BIG)],
    # Phase 5: Mantel 0.8 Wand ueber dem Arm (v -0.87 ... 0.28 am Speisepunkt x 0.35) ab 0.70, Rest wie Rev C
    "P5 Mantel (0.70 bis v +0.28)": [(0.70, BIG, -BIG, 0.28), (1.00, BIG, -BIG, BIG)],
    # Schranken: Halbraum ASA ab Abstand g ueber der ganzen Dicke
    "Halbraum ab 0.76": [(0.76, BIG, -BIG, BIG)],
    "Halbraum ab 0.70": [(0.70, BIG, -BIG, BIG)],
}


def path_weight():
    """Energieanteil des ueberdeckten L3-Stuecks (ANNAHME sin^2-Spannungsverteilung ab Kurzschluss)."""
    seg = [4.90, 5.00, 2.64, 2.00, 2.64, 2.70, 2.64, 2.00, 2.64, 2.70, 3.94]  # L6 L3 L4 L5 L4 L2 L4 L5 L4 L2 L1
    L = sum(seg)
    # Mantel aussen R 4.0 um x -2.2, bei y = F: halbe Sehne sqrt(4^2 - 2.8^2) -> x -5.06 ... 0.66; L3 ab x -2.2
    half = math.sqrt(4.0 ** 2 - 2.8 ** 2)
    s0 = seg[0]
    s1 = seg[0] + (-2.2 + half) - (-2.2)
    s = np.linspace(0, L, 20001)
    e = np.sin(math.pi * s / (2 * L)) ** 2
    m = (s >= s0) & (s <= s1)
    return L, s0, s1, np.trapz(e[m], s[m]) / np.trapz(e, s)


def main():
    L, s0, s1, w = path_weight()
    print(f"Netz: {mesh.p.shape[1]} Knoten, {mesh.t.shape[1]} Dreiecke")
    print(f"Leiterpfad AN043 (Tab. 1) L = {L:.2f} mm; ueberdeckt s = {s0:.2f} ... {s1:.2f} mm; Energieanteil w = {w:.3f} (ANNAHME sin^2)")
    f0 = 2.44e9
    for er_asa in (2.5, 3.0, 3.7):
        print(f"\nASA eps_r = {er_asa} (ANNAHME)")
        C = {k: capacitance(p, er_asa) for k, p in VARIANTS.items()}
        c0 = C["ohne Kunststoff"]
        for k, c in C.items():
            print(f"  {k:45s} C' = {c:8.3f} pF/m  dC'/C'(ohne) = {100 * (c / c0 - 1):6.3f} %")
        for a_, b_ in (("Rev C Block (0.70 vor F, 1.00 ueber Kante)", "P5 Mantel (0.70 bis v +0.28)"),
                       ("Halbraum ab 0.76", "Halbraum ab 0.70")):
            d = C[b_] / C[a_] - 1
            print(f"  Aenderung {a_} -> {b_}: dC'/C' = {100 * d:.3f} %;"
                  f" df lokal (w=1, obere Schranke) = {-0.5 * d * f0 / 1e6:.2f} MHz; mit w: {-0.5 * w * d * f0 / 1e6:.3f} MHz")
        dfull = C["Halbraum ab 0.70"] / c0 - 1
        print(f"  Vergleich: ganzer L3-Querschnitt ASA ab 0.70 gegen ohne: dC'/C' = {100 * dfull:.2f} %,"
              f" w=1 -> {-0.5 * dfull * f0 / 1e6:.1f} MHz")


if __name__ == "__main__":
    main()
