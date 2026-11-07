# -*- coding: utf-8 -*-
"""Auswertung FEM Sonde: Sicherheitsfaktoren, Konvergenz, Vergleich Handrechnung, Fallabschaetzung 1 m.

Lauf:  .venv/bin/python simulation/fem/fem_eval.py   (liest simulation/fem/results.json, schreibt summary.json)
Festigkeit FR4 (docs/references/Kingboard_KB-6160A_TechnicalInformation.pdf, IPC-TM-650 2.4.4):
  Biegefestigkeit quer >= 345 MPa (Mindestwert), laengs >= 415 MPa; typisch 446 / 565 MPa.
  Gerechnet wird mit dem Mindestwert QUER (Faserrichtung der Sonde im Nutzen unbekannt -> konservativ).
"""
import json
import math
import os

D = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(D, 'results.json')))
SIG_MIN = 345.0
SIG_TYP_L = 565.0
H = R['hand']
runs = {(r['case'], r['h_fine']): r for r in R['runs']}
out = {}

print('Konvergenz LC1 (10 N seitlich, schwache Achse):')
print('  h_fein  Knoten   s(z=-20)  s(z=-5)  s(z=0)  s(z=1)  s(z=1.5)  s_max_frei  s1_max_PCB  u_Spitze')
for h in (1.0, 0.5, 0.25):
    r = runs.get(('LC1_seitlich_y', h))
    if r:
        print('  %5.2f  %7d  %8.1f %8.1f %7.1f %7.1f %8.1f %10.1f %10.1f %8.2f' % (
            h, r['nodes'], r['sigma_zz_at_-20'], r['sigma_zz_at_-5'], r['sigma_zz_at_0'], r['sigma_zz_at_1'],
            r['sigma_zz_at_1.5'], r['sigma_zz_max_free'], r['sigma_1_max_pcb'], r['u_tip']))
fine = runs[('LC1_seitlich_y', 0.25)]
nom = lambda z: 10.0 * (z - (-105.0)) / H['W_weak']
print('Handrechnung LC1: s(z) = F (z + 105) / W, W = %.3f mm3' % H['W_weak'])
for z in (-20, -5, 0, 1, 1.5):
    k = 'sigma_zz_at_%g' % z
    print('  z = %5.1f  Hand %6.1f  FEM %6.1f  Abw. %+5.1f %%' % (z, nom(z), fine[k], (fine[k] / nom(z) - 1) * 100))
s_edge_nom = nom(2.0)
s_hot = fine['sigma_zz_at_1.5']
kt = s_hot / nom(1.5)
print('  Kerbfaktor an der Vergusskante (z = 1.5, 0.5 mm vor der Kante): Kt = %.2f' % kt)
out['LC1'] = dict(sigma_nom_edge=round(s_edge_nom, 1), sigma_hot=round(s_hot, 1), Kt=round(kt, 2),
                  sigma_max_free=fine['sigma_zz_max_free'], SF_min=round(SIG_MIN / s_hot, 2),
                  SF_typ_l=round(SIG_TYP_L / s_hot, 2), SF_max=round(SIG_MIN / fine['sigma_zz_max_free'], 2),
                  u_tip=fine['u_tip'], u_tip_hand=H['u_tip_y'])
r2 = runs[('LC2_seitlich_x', 0.5)]
out['LC2'] = dict(sigma=r2['sigma_zz_max_free'], hand=H['sig_lat_x'], SF_min=round(SIG_MIN / r2['sigma_zz_max_free'], 1))
r3 = runs[('LC3_axial_druck', 0.5)]
r4 = runs[('LC4_zug', 0.5)]
out['LC3'] = dict(sigma=r3['sigma_zz_max_free'], hand=H['sig_axial'], SF_strength=round(SIG_MIN / r3['sigma_zz_max_free'], 0))
out['LC4'] = dict(sigma=r4['sigma_zz_max_free'], hand=H['sig_tension'], SF_strength=round(SIG_MIN / r4['sigma_zz_max_free'], 0))
b5 = runs[('LC5_knick_frei', 0.5)]
b6 = runs[('LC6_knick_gefuehrt', 0.5)]
out['LC5'] = dict(Pcr=b5['P_cr_N'][0], hand=H['Pcr_free'], SF=round(b5['P_cr_N'][0] / 50.0, 2))
out['LC6'] = dict(Pcr=b6['P_cr_N'][0], hand=H['Pcr_guided'], SF=round(b6['P_cr_N'][0] / 50.0, 2))
r1b = runs.get(('LC1b_ohne_Kragenstuetze', 0.5))
if r1b:
    out['LC1b'] = dict(sigma_hot=r1b['sigma_zz_at_1.5'], sigma_max_pcb=r1b['sigma_1_max_pcb'], u_tip=r1b['u_tip'])
# Fall 1 m: obere Schranke, gesamte kinetische Energie geht in Biegung der Sonde (Spitze trifft seitlich auf)
m_total = 0.022          # kg, CAD-Abschaetzung (check_sensor.txt Pkt. 8)
m_probe = 20 * 1.6 * 107 * 1.85e-6    # kg, Sonde unterhalb des Kragens
k = 10.0 / fine['u_tip']               # N/mm aus FEM
s_per_N = s_hot / 10.0
fall = {}
for name, m in (('Sensor_gesamt_obere_Schranke', m_total), ('nur_Sondenmasse', m_probe)):
    E = m * 9.81 * 1.0 * 1000          # N*mm
    F = math.sqrt(2 * k * E)
    s = F * s_per_N
    fall[name] = dict(E_Nmm=round(E, 1), F_equiv_N=round(F, 1), sigma=round(s, 1), SF_min=round(SIG_MIN / s, 2),
                      SF_typ_l=round(SIG_TYP_L / s, 2))
out['fall_1m'] = fall
out['k_tip_N_per_mm'] = round(k, 4)
for kk, v in out.items():
    print(kk, v)
json.dump(out, open(os.path.join(D, 'summary.json'), 'w'), indent=1)
