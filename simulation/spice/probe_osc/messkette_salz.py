"""Entscheidungsvorlage Messkette / Salz (REQ-MES-11): quantitative Bewertung der Varianten A-D.

Grundlagen (alle lokal):
- Ersatzschaltbild Sonde: simulation/field/results/probe_lumped_3d_extrap.json (PROBE_CAPACITANCE.md Kap. 3),
  C0 7.0 pF, Ci 99 pF, Cg 1.72 pF/eps, Rs = eps0/(sigma_b*Cg). Bis 70 MHz gegen die komplexe 2D-FEM geprueft (Teil 0).
- Substrat: Topp 1980 eps'(theta), sigma_b = sigma_p (eps'-4)/80 (Hilhorst 1998 Gl. 4.16), simulation/field/params.py.
- RC-Oszillator: oscmodel.py (exakte stueckweise Loesung, gegen ngspice/probe_osc.py validiert, Teil 0).
- LC-Oszillator (Variante C): Pierce-Netz im Frequenzbereich (unten), Bauteilwerte aus den lokalen Datenblaettern.
- Energie: scripts/energy_budget.py / concept_energy.py (Q_MEAS je Variante gepatcht).
- Flaeche: Courtyards aus KiCad-Footprints (hardware/sensor/gen/floorplan_options.py).
- Preise: docs/concepts/bom/jlc_prices.json (JLC-Abfrage, siehe _staging/INDEX_salz.csv).

Aufruf:  .venv/bin/python simulation/spice/probe_osc/messkette_salz.py
Ausgabe: simulation/spice/probe_osc/messkette_salz.txt (alle Tabellen) und messkette_salz.json
ANNAHMEN sind im Code als ANNAHME markiert.
"""
import io
import json
import math
import os
import sys
from contextlib import redirect_stdout

import numpy as np
from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "simulation", "field"))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import oscmodel as O  # noqa: E402
import params as P  # noqa: E402

FIT = json.load(open(os.path.join(ROOT, "simulation", "field", "results", "probe_lumped_3d_extrap.json")))
FIT2D = json.load(open(os.path.join(ROOT, "simulation", "field", "results", "lumped_fit.json")))
RES = {}

# ------------------------------------------------------------------ Messkette Rev A (CONCEPTS 2.3, probe_osc.py)
R_OSC = 10e3
C_PAR = 10e-12      # ANNAHME (CONCEPTS 2.3)
C_REF1 = 22e-12     # C1555, 0402CG220J500NT
C_REF2 = 100e-12    # C1546, 0402CG101J500NT

# ------------------------------------------------------------------ Substrat
SIG_TAP, SIG_LOW, SIG_NORM = 0.035, 0.18, 0.37   # Porenwasser S/m (params.py: KLZH, Purdue HO-237)
SALT = {"Leitung": SIG_TAP, "low": SIG_LOW, "normal": SIG_NORM}


def theta_of_eps(eps):
    return brentq(lambda t: P.eps_topp(t) - eps, 0.0, 0.6)


TH_DRY = 0.05
TH_WET = theta_of_eps(P.EPS_WET)      # ~0.40
TH_MID = theta_of_eps(10.0)           # ~0.19


def sig_b(sig_p, theta, conc=False, eps_off=P.EPS_OFF):
    """Bulk-Leitfaehigkeit. conc=True: Ionenmenge bleibt beim Austrocknen erhalten -> sigma_p ~ theta_wet/theta
    (ANNAHME, ohne Ausfaellung/Adsorption)."""
    eps = P.eps_topp(theta)
    sp = sig_p * (TH_WET / theta if conc else 1.0)
    return P.sigma_bulk(sp, eps, eps_off)


# ------------------------------------------------------------------ RC-Oszillator (Variante A/B)
def periods(eps, sb, R=R_OSC, crefs=(0.0, C_REF1), cpar=C_PAR, fit=FIT, vtp=O.VTP, vtn=O.VTN, tpd2=0.0):
    c0, ci, cs, rs = O.probe_params(fit, eps, sb)
    return [O.period(cpar + c0 + cr, ci, cs, rs, R=R, vtp=vtp, vtn=vtn, n_half=50, n_avg=12, tpd=tpd2 / 2) for cr in crefs]


def c_ratio(t0, t1, cref=C_REF1, cpar=C_PAR):
    """Firmware-Formel CONCEPTS 2.3: C_Sonde = Cref * T0/(T1-T0) - Cpar."""
    return cref * t0 / (t1 - t0) - cpar


OSC = {"R": R_OSC, "tpd2": 0.0}   # Betriebspunkt RC-Oszillator (Teil D3 aendert ihn voruebergehend)


def c_meas(eps, sb):
    t0, t1 = periods(eps, sb, R=OSC["R"], tpd2=OSC["tpd2"])
    return c_ratio(t0, t1)


def c_lossless(eps):
    c0, ci, cs, _ = O.probe_params(FIT, eps, 0.0)
    return c0 + ci * cs / (ci + cs)


C_DRY = c_meas(P.eps_topp(TH_DRY), 0.0)
C_WET_TAP = c_meas(P.EPS_WET, sig_b(SIG_TAP, TH_WET))


def idx(c, cd=None, cw=None):
    cd = C_DRY if cd is None else cd
    cw = C_WET_TAP if cw is None else cw
    return 100.0 * (c - cd) / (cw - cd)


def idx_true(theta):
    """Verlustfreier Index (Sonde ohne Leitfaehigkeit), Bezug trocken/nass."""
    cd, cw = c_lossless(P.eps_topp(TH_DRY)), c_lossless(P.EPS_WET)
    return 100.0 * (c_lossless(P.eps_topp(theta)) - cd) / (cw - cd)


# ================================================================== Teil 0: Validierung
def part0():
    print("## 0 Validierung der Modelle\n")
    ref = {}
    for line in open(os.path.join(HERE, "results.csv")).read().splitlines()[1:]:
        v = line.split(";")
        ref[v[0]] = (float(v[1]), float(v[3]))
    cases = {"air": (1.0, 0.0), "dry": (4.0, 0.0), "wet_nosalt": (25.0, 0.0),
             "wet_tap": (25.0, P.sigma_bulk(SIG_TAP, 25)), "wet_fert_normal": (25.0, P.sigma_bulk(SIG_NORM, 25)),
             "mid_tap": (10.0, P.sigma_bulk(SIG_TAP, 10)), "mid_fert_low": (10.0, P.sigma_bulk(SIG_LOW, 10))}
    print("| Fall | f0 ngspice [MHz] (results.csv) | f0 oscmodel [MHz] | Abw. [%] |")
    print("|---|---|---|---|")
    worst = 0
    for k, (e, s) in cases.items():
        t0 = O.period(C_PAR + O.probe_params(FIT, e, s)[0], *O.probe_params(FIT, e, s)[1:])
        d = 100 * (1e-6 / t0 / ref[k][0] - 1)
        worst = max(worst, abs(d))
        print(f"| {k} | {ref[k][0]:.4f} | {1e-6/t0:.4f} | {d:+.3f} |")
    print(f"\nMax. Abweichung {worst:.3f} % -> oscmodel ersetzt ngspice fuer Parameterstudien.\n")
    # Ersatzschaltbild gegen komplexe 2D-FEM bei 70 MHz (salt_index_2d.csv)
    fem = {}
    for line in open(os.path.join(ROOT, "simulation", "field", "results", "salt_index_2d.csv")).read().splitlines()[1:]:
        v = line.split(";")
        if v[0] == "4L SG gap2":
            fem[(float(v[1]), v[2], float(v[3]))] = float(v[7])
    lf = FIT2D["4L SG gap2"]
    fit2 = {"C0_pF": lf["C0_pF_per_m"], "Ci_pF": lf["Ci_pF_per_m"], "Cg_pF": lf["Cg_pF_per_m_per_eps"]}
    print("Ersatzschaltbild (2D-Fit bis 20 MHz) gegen komplexe 2D-FEM, Fehler nass gegen Leitungswasser [%-Punkte]:\n")
    print("| f [MHz] | FEM low / normal | Ersatzschaltbild low / normal |")
    print("|---|---|---|")
    for f in (6.0, 20.0, 70.0):
        e_l = ceff_err(fit2, 25.0, SIG_LOW, f * 1e6)
        e_n = ceff_err(fit2, 25.0, SIG_NORM, f * 1e6)
        keys = [k for k in fem if k[0] == f and k[2] == 25.0 and k[1].startswith("geduengt")]
        vals = [fem[k] for k in sorted(keys)]
        print(f"| {f:g} | {' / '.join(f'{v:+.1f}' for v in vals)} | {e_l:+.1f} / {e_n:+.1f} |")
    print("\n(FEM-Werte: results/salt_index_2d.csv; Abweichung Ersatzschaltbild - FEM siehe Tabelle; Fit nur bis 20 MHz.)\n")


def ceff(fit, eps, sb, f):
    return O.y_probe(fit, eps, sb, f).imag / (2 * math.pi * f)


def ceff_err(fit, eps, sig_p, f, eps_cal=25.0):
    cd = ceff(fit, P.EPS_DRY, 0.0, f)
    cw = ceff(fit, eps_cal, P.sigma_bulk(SIG_TAP, eps_cal), f)
    c = ceff(fit, eps, P.sigma_bulk(sig_p, eps), f)
    ct = ceff(fit, eps, P.sigma_bulk(SIG_TAP, eps), f)
    return 100 * (c - ct) / (cw - cd)


# ================================================================== Teil A: Status quo
TH_GRID = [0.05, 0.08, 0.10, 0.12, 0.15, TH_MID, 0.25, 0.30, 0.35, TH_WET]


def reading(theta, sig_p, conc=False, cd=None, cw=None, eps_off=P.EPS_OFF):
    eps = P.eps_topp(theta)
    return idx(c_meas(eps, sig_b(sig_p, theta, conc, eps_off)), cd, cw)


def crossing(sig_p, thr, conc=False, cd=None, cw=None, eps_off=P.EPS_OFF):
    """theta, bei dem die Anzeige beim Austrocknen die Schwelle thr unterschreitet."""
    f = lambda th: reading(th, sig_p, conc, cd, cw, eps_off) - thr  # noqa: E731
    lo, hi = TH_DRY, TH_WET
    if f(lo) > 0:
        return None
    if f(hi) < 0:
        return hi
    return brentq(f, lo, hi, xtol=1e-4)


def partA():
    print("## A Status quo 2-6 MHz (RC-Oszillator R 10 kOhm, ratiometrisch mit Cref1)\n")
    print(f"Kalibrierung trocken theta {TH_DRY} (eps' {P.eps_topp(TH_DRY):.2f}, sigma_b 0) / nass theta {TH_WET:.3f} "
          f"(eps' 25) mit Leitungswasser. Mitte = eps' 10 = theta {TH_MID:.3f}.\n")
    print("### A1 Anzeige [%] ueber der Feuchte (sigma_p konstant | konzentrierend sigma_p ~ theta_nass/theta)\n")
    print("| theta | eps' | Index verlustfrei | Leitung | low | normal | low konz. | normal konz. | Fehler low/normal [%-P] |")
    print("|---|---|---|---|---|---|---|---|---|")
    tab = []
    for th in TH_GRID:
        r = {k: reading(th, s) for k, s in SALT.items()}
        rc = {k: reading(th, s, True) for k, s in SALT.items()}
        tab.append({"theta": th, "eps": P.eps_topp(th), "true": idx_true(th), **{k: r[k] for k in r},
                    **{k + "_konz": rc[k] for k in rc}})
        print(f"| {th:.3f} | {P.eps_topp(th):.1f} | {idx_true(th):.0f} | {r['Leitung']:.0f} | {r['low']:.0f} | "
              f"{r['normal']:.0f} | {rc['low']:.0f} | {rc['normal']:.0f} | "
              f"{r['low']-r['Leitung']:+.0f} / {r['normal']-r['Leitung']:+.0f} |")
    RES["A1"] = tab
    print("\nC_mess [pF] (ratiometrisch) bei Leitung / low / normal; verlustfrei max. = Wasser %.1f pF:\n" % (c_lossless(80.0) * 1e12))
    print("| theta | Leitung | low | normal |")
    print("|---|---|---|---|")
    for th in (TH_DRY, 0.10, 0.15, TH_MID, 0.30, TH_WET):
        cs = [c_meas(P.eps_topp(th), sig_b(sp, th)) * 1e12 for sp in SALT.values()]
        print(f"| {th:.3f} | " + " | ".join(f"{c:.1f}" for c in cs) + " |")
    print("\n### A2 Giess-Schwelle: Bei welcher wirklichen Feuchte meldet der Sensor 'Giessen noetig'?\n")
    print("Schwelle = Anzeige (Leitungswasser-Kalibrierung). 'wirklich' = Anzeige, die der Sensor bei Leitungswasser "
          "am selben theta zeigen wuerde. ANNAHME: Schwelle je Pflanze 20-40 %.\n")
    print("| Schwelle | theta Leitung | theta low / Leitungs-Index dort | theta normal / Leitungs-Index dort | "
          "low konz. | normal konz. |")
    print("|---|---|---|---|---|---|")
    a2 = []
    for thr in (20.0, 30.0, 40.0):
        th_t = crossing(SIG_TAP, thr)
        row = {"thr": thr, "theta_tap": th_t}
        cells = []
        for k, s, conc in (("low", SIG_LOW, False), ("normal", SIG_NORM, False), ("low_konz", SIG_LOW, True),
                           ("normal_konz", SIG_NORM, True)):
            th = crossing(s, thr, conc)
            it = reading(th, SIG_TAP) if th else None
            row[k] = (th, it)
            cells.append("nie" if th is None else f"{th:.3f} / {it:.0f} %")
        a2.append(row)
        print(f"| {thr:.0f} % | {th_t:.3f} | " + " | ".join(cells) + " |")
    RES["A2"] = a2
    print("\nZwischenwerte sigma_p (Schwelle 30 %): theta beim Ausloesen / Leitungs-Index dort\n")
    print("| sigma_p [S/m] | Bedeutung | theta | Leitungs-Index |")
    print("|---|---|---|---|")
    a2b = []
    for sp, txt in ((0.031, "Leitungswasser min. (KLZH)"), (0.036, "Leitungswasser max. (KLZH)"),
                    (0.072, "Einzelprobe 721 uS/cm (KLZH)"), (0.10, "ANNAHME gelegentlich geduengt"),
                    (0.18, "PourThru low (Purdue)")):
        th = crossing(sp, 30.0)
        a2b.append((sp, th, reading(th, SIG_TAP)))
        print(f"| {sp:.3f} | {txt} | {th:.3f} | {reading(th, SIG_TAP):.0f} % |")
    RES["A2b"] = a2b
    # eps_off-Sensitivitaet
    th3 = crossing(SIG_LOW, 30.0, eps_off=3.0)
    print(f"\nSensitivitaet eps_off 3 statt 4 (ANNAHME Hilhorst): Schwelle 30 %, low -> theta "
          f"{th3:.3f} / Leitungs-Index {reading(th3, SIG_TAP):.0f} %. Trockenpunkt: Fehler "
          f"{reading(TH_DRY, SIG_NORM, eps_off=3.0) - reading(TH_DRY, SIG_TAP, eps_off=3.0):+.1f} %-P (normal).\n")

    print("### A3 Nass-Kalibrierung im eigenen gedüngten Topf (Nasspunkt mit Salzzustand 'Kal.'), spaeter anderer "
          "Salzzustand\n")
    print("Eintrag: theta beim Unterschreiten von 30 % / Leitungs-Index an diesem Punkt (Soll: wie Zeile Leitung/Leitung "
          "= 30 %). Diagonale = automatische Nachfuehrung des Nasspunkts nach jedem Giessen (Variante D2).\n")
    hdr = list(SALT)
    print("| Kal. \\ Messung | " + " | ".join(hdr) + " |")
    print("|---|" + "---|" * len(hdr))
    a3 = {}
    for kc, sc in SALT.items():
        cw = c_meas(P.EPS_WET, sig_b(sc, TH_WET))
        cells = []
        for km, sm in SALT.items():
            th = crossing(sm, 30.0, cw=cw)
            it = reading(th, SIG_TAP) if th else None
            a3[(kc, km)] = (th, it)
            cells.append("nie" if th is None else f"{th:.3f} / {it:.0f} %")
        print(f"| {kc} | " + " | ".join(cells) + " |")
    RES["A3"] = {f"{k[0]}->{k[1]}": v for k, v in a3.items()}
    # Index-Fehler in der Mitte nach Eigentopf-Kalibrierung
    print("\nAnzeige bei Mitte (theta %.3f) nach Nass-Kalibrierung mit 'low': Leitung %.0f / low %.0f / normal %.0f %% "
          "(Leitungs-Kalibrierung, Leitung: %.0f %%).\n" % (
              TH_MID, *[reading(TH_MID, s, cw=c_meas(P.EPS_WET, sig_b(SIG_LOW, TH_WET))) for s in SALT.values()],
              reading(TH_MID, SIG_TAP)))
    print("### A5 Gelernte Schwelle (Nutzer giesst bei theta_need = %.3f, App speichert die Anzeige im Salzzustand "
          "'Lern'), spaeter Salzzustand 'Messung'\n" % crossing(SIG_TAP, 30.0))
    print("Eintrag: theta beim Ausloesen (Soll %.3f). Kleiner = zu spaet (trockener), groesser = zu frueh (Uebergiessen).\n"
          % crossing(SIG_TAP, 30.0))
    th_need = crossing(SIG_TAP, 30.0)
    print("| Lern \\ Messung | " + " | ".join(SALT) + " |")
    print("|---|" + "---|" * len(SALT))
    a5 = {}
    for kl, sl in SALT.items():
        thr = reading(th_need, sl)
        cells = []
        for km, sm in SALT.items():
            th = crossing(sm, thr) if thr < reading(TH_WET, sm) else TH_WET
            a5[f"{kl}->{km}"] = (thr, th)
            cells.append("sofort (nass)" if th is None or th >= TH_WET - 1e-3 else
                         ("nie" if th is None else f"{th:.3f}"))
        print(f"| {kl} (Schwelle {thr:.0f} %) | " + " | ".join(cells) + " |")
    RES["A5"] = a5
    print()
    # Salzerkennung aus f2 (Cref2): C aus (T0,T2) gegen C aus (T0,T1)
    print("### A4 Salzerkennung mit vorhandener Hardware: C(T0,T2 mit Cref2) / C(T0,T1 mit Cref1)\n")
    print("| theta | Leitung | low | normal |")
    print("|---|---|---|---|")
    det = []
    for th in (TH_DRY, 0.10, TH_MID, TH_WET):
        cells = []
        for s in SALT.values():
            t0, t1, t2 = periods(P.eps_topp(th), sig_b(s, th), crefs=(0.0, C_REF1, C_REF2))
            q = c_ratio(t0, t2, C_REF2) / c_ratio(t0, t1)
            cells.append(f"{q:.3f}")
        det.append([th] + cells)
        print(f"| {th:.3f} | " + " | ".join(cells) + " |")
    RES["A4"] = det
    print("\nVerlustfrei = 1.000; Abweichung > ~3 % (ANNAHME Messgenauigkeit) = Hinweis 'Salz/Duenger'.\n")


# ================================================================== Teil B: Zwei/drei Frequenzen + Inversion
NUIS = {  # Restunsicherheit nach Kalibrierung, 1 sigma  (ANNAHME, siehe Text)
    "Ci +-2 %": ("ci", 0.02), "C0 +-2 %": ("c0", 0.02), "Cg +-2 %": ("cg", 0.02),
    "Cpar +-0.3 pF": ("cpar", 0.3e-12), "Cref +-1 %": ("cref", 0.01),
    "VT+ +-1 %": ("vtp", 0.01), "VT- +-1 %": ("vtn", 0.01), "2 tpd +-1 ns": ("tpd", 1e-9),
}


def model_logT(u, nu, configs):
    lnk, eps, lnsig = u
    fit = dict(FIT)
    fit["Ci_pF"] *= 1 + nu.get("ci", 0)
    fit["C0_pF"] *= 1 + nu.get("c0", 0)
    fit["Cg_pF"] *= 1 + nu.get("cg", 0)
    out = []
    for R, cr in configs:
        T = periods(eps, math.exp(lnsig), R=R * math.exp(lnk), crefs=(cr * (1 + nu.get("cref", 0)),),
                    cpar=C_PAR + nu.get("cpar", 0), fit=fit, vtp=O.VTP * (1 + nu.get("vtp", 0)),
                    vtn=O.VTN * (1 + nu.get("vtn", 0)), tpd2=6e-9 + nu.get("tpd", 0))[0]
        out.append(math.log(T))
    return np.array(out)


def idx_of_eps(eps):
    cd, cw = c_lossless(P.eps_topp(TH_DRY)), c_lossless(P.EPS_WET)
    return 100.0 * (c_lossless(eps) - cd) / (cw - cd)


def partB():
    print("## B Mehrere Messfrequenzen + Inversion des Ersatzschaltbilds (sigma_b und eps' schaetzen)\n")
    print("Unbekannte: k (R, Schwellen), eps', ln sigma_b. Lineare Fehlerfortpflanzung der Restunsicherheiten "
          "(ANNAHME nach Kalibrierung: Ci/C0/Cg je 2 % (Fit-Residuum 1-2 %, REPORT Kap. 2/6), Cpar 0.3 pF, Cref 1 %, "
          "VT+/VT- je 1 %, 2 tpd 1 ns). Strukturfehler (Maxwell-Wagner im Substrat, Torf) nicht enthalten -> "
          "Ergebnis ist eine **Untergrenze**.\n")
    variants = {
        "B1 vorhandene HW: R10k, +Cref1, +Cref2 (1.0-4.5 MHz)": [(R_OSC, 0.0), (R_OSC, C_REF1), (R_OSC, C_REF2)],
        "B2 +Analogschalter: R10k, R10k+Cref1, R5k (statt Cref2, bis ~11 MHz)": [(R_OSC, 0.0), (R_OSC, C_REF1),
                                                                                 (R_OSC / 2, 0.0)],
    }
    out = {}
    cases = [("trocken+", 0.08), ("Schwelle", 0.12), ("Mitte", TH_MID), ("nass", TH_WET)]
    for vn, cfg in variants.items():
        print(f"### {vn}\n")
        print("| Fall | sigma_p | f [MHz] | 1-sigma Indexfehler [%-P] | groesster Beitrag |")
        print("|---|---|---|---|---|")
        rows = []
        for cn, th in cases:
            for sn, sp in SALT.items():
                eps = P.eps_topp(th)
                sb = max(sig_b(sp, th), 1e-4)
                u0 = np.array([0.0, eps, math.log(sb)])
                y0 = model_logT(u0, {}, cfg)
                J = np.zeros((3, 3))
                for j, h in enumerate((1e-3, 1e-2 * eps, 1e-2)):
                    du = np.zeros(3)
                    du[j] = h
                    J[:, j] = (model_logT(u0 + du, {}, cfg) - y0) / h
                S, sd, names = [], [], []
                for nm, (key, s1) in NUIS.items():
                    S.append((model_logT(u0, {key: s1}, cfg) - y0))
                    names.append(nm)
                S = np.array(S).T   # Spalten = Wirkung einer 1-sigma-Stoerung
                try:
                    G = np.linalg.solve(J, S)       # du je Stoerung
                except np.linalg.LinAlgError:
                    G = np.linalg.lstsq(J, S, rcond=None)[0]
                deps = G[1, :]
                didx = (idx_of_eps(eps + 0.01) - idx_of_eps(eps - 0.01)) / 0.02
                contrib = np.abs(deps * didx)
                tot = float(np.sqrt(np.sum(contrib ** 2)))
                f0 = 1e-6 / math.exp(y0[0])
                big = names[int(np.argmax(contrib))]
                rows.append({"case": cn, "theta": th, "salt": sn, "sigma_idx": tot, "dominant": big,
                             "cond": float(np.linalg.cond(J))})
                print(f"| {cn} (theta {th:.2f}) | {sn} | {f0:.2f} | {tot:.1f} | {big} |")
        out[vn] = rows
        print()
    RES["B"] = out


# ================================================================== Teil C: hohe Messfrequenz
L_TANK = 220e-9     # SDCL1005CR22JTDF (C18834): 220 nH, Q min 8 / typ 12 @100 MHz, SRF >= 450 MHz (Sunlord S.2)
Q_L = 10.0          # ANNAHME zwischen Q min 8 und typ 12 (Sunlord S.2)
C2_TANK = 47e-12    # ANNAHME C0G 0402, Auslegung: nass ~70 MHz
CPAR_HF = 10e-12    # ANNAHME wie RC-Variante


def pierce(fit, eps, sb, ro, tpd, cref=0.0, fgrid=None):
    """Schwingfrequenz des Pierce-Netzes: Inverter (Spannungsquelle -A, Ausgangswiderstand ro, Laufzeit tpd)
    -> Knoten C2 -> L (mit R_L = wL/Q_L) -> Knoten mit Cpar + Cref + Sonde. Schwingbedingung:
    arg(H) - w tpd = 180 Grad. Rueckgabe f, |H| (noetige Kleinsignalverstaerkung = 1/|H|)."""
    def H(f):
        w = 2 * math.pi * f
        y1 = 1j * w * (CPAR_HF + cref) + O.y_probe(fit, eps, sb, f)
        z1 = 1 / y1
        zl = 1j * w * L_TANK + w * L_TANK / Q_L
        z2 = 1 / (1j * w * C2_TANK)
        za = 1 / (1 / z2 + 1 / (zl + z1))
        return za / (ro + za) * z1 / (zl + z1)

    def ph(f):
        return np.angle(H(f) * np.exp(-1j * 2 * math.pi * f * tpd) * -1.0)  # Inverter: -A
    fs = fgrid if fgrid is not None else np.linspace(20e6, 200e6, 1801)
    p = np.array([ph(f) for f in fs])
    cands = [i for i in range(len(fs) - 1) if p[i] * p[i + 1] <= 0 and abs(p[i] - p[i + 1]) < 1]
    if not cands:
        return None, None
    i = cands[0]
    f = brentq(ph, fs[i], fs[i + 1], xtol=1.0)
    return f, abs(H(f))


def c_from_f(f, cref=0.0):
    """Ideale Auswertung (verlustfrei, ro = 0, tpd = 0): C1 aus Serienkapazitaet C1*C2/(C1+C2) = 1/(w^2 L)."""
    w = 2 * math.pi * f
    cs = 1 / (w * w * L_TANK)
    return cs * C2_TANK / (C2_TANK - cs) - CPAR_HF - cref


def c_hf_ratio(f0, f1, cref=C_REF1):
    """Ratiometrisch (L faellt heraus): 1/f^2 ~ L*Cser; Cser0, Cser1 -> C1 aus zwei Gleichungen (numerisch)."""
    a = (f0 / f1) ** 2   # = Cser1/Cser0
    # Cser(C1) = C1*C2/(C1+C2); suche C1 mit Cser(C1+cref)/Cser(C1) = a
    g = lambda c1: ((c1 + cref) * C2_TANK / (c1 + cref + C2_TANK)) / (c1 * C2_TANK / (c1 + C2_TANK)) - a  # noqa
    c1 = brentq(g, 1e-13, 1e-9)
    return c1 - CPAR_HF


def partC():
    print("## C Hohe Messfrequenz\n")
    print("### C1 Ideale Messung von C_eff = Im(Y)/w (Obergrenze der Verbesserung), Fehler gegen Leitungswasser "
          "[%-Punkte] Mitte (eps' 10) | nass (eps' 25), low / normal; Guete Q der Sonde nass/normal\n")
    print("| f [MHz] | Mitte low / normal | nass low / normal | Q Sonde nass normal |")
    print("|---|---|---|---|")
    c1 = []
    for f in (2e6, 6e6, 10e6, 20e6, 50e6, 70e6, 100e6, 150e6):
        em = [ceff_err(FIT, 10.0, s, f) for s in (SIG_LOW, SIG_NORM)]
        ew = [ceff_err(FIT, 25.0, s, f) for s in (SIG_LOW, SIG_NORM)]
        y = O.y_probe(FIT, 25.0, P.sigma_bulk(SIG_NORM, 25.0), f)
        c1.append([f / 1e6, *em, *ew, y.imag / y.real])
        print(f"| {f/1e6:g} | {em[0]:+.1f} / {em[1]:+.1f} | {ew[0]:+.1f} / {ew[1]:+.1f} | {y.imag/y.real:.1f} |")
    RES["C1"] = c1
    print("\n### C2 Realer Pierce-LC-Oszillator (SN74LVC1GU04 + 220 nH + C2 47 pF + Sonde), ratiometrisch mit Cref1, "
          "Teiler 16\n")
    print("Verlust der Sonde + Phasenfehler des Inverters (tpd 1.1-3.7 ns bei 3.3 V, SN74LVC1GU04 S.7 Tab. 6.6; "
          "Ausgangswiderstand ro ANNAHME) verschieben die Frequenz salzabhaengig.\n")
    print("| ro [Ohm] | tpd [ns] | f Luft / trocken / nass [MHz] | f/16 [MHz] | Mitte low / normal [%-P] | "
          "nass low / normal [%-P] | noetige Verstaerkung nass normal |")
    print("|---|---|---|---|---|---|---|")
    c2 = []
    for ro in (30.0, 100.0):
        for tpd in (0.0, 1.1e-9, 3.7e-9):
            def cm(eps, sp):
                sb = P.sigma_bulk(sp, eps)
                f0, h0 = pierce(FIT, eps, sb, ro, tpd)
                f1, _ = pierce(FIT, eps, sb, ro, tpd, cref=C_REF1)
                return c_hf_ratio(f0, f1), f0, h0
            cd = cm(P.EPS_DRY, 0.0)[0]
            cw = cm(25.0, SIG_TAP)[0]
            fa = pierce(FIT, 1.0, 0.0, ro, tpd)[0]
            fd = pierce(FIT, P.EPS_DRY, 0.0, ro, tpd)[0]
            fw = pierce(FIT, 25.0, P.sigma_bulk(SIG_TAP, 25.0), ro, tpd)[0]
            errs = []
            for eps in (10.0, 25.0):
                ct = cm(eps, SIG_TAP)[0]
                for s in (SIG_LOW, SIG_NORM):
                    errs.append(100 * (cm(eps, s)[0] - ct) / (cw - cd))
            gn = 1 / cm(25.0, SIG_NORM)[2]
            c2.append({"ro": ro, "tpd": tpd, "f": (fa, fd, fw), "err": errs, "gain": gn})
            print(f"| {ro:.0f} | {tpd*1e9:.1f} | {fa/1e6:.0f} / {fd/1e6:.0f} / {fw/1e6:.0f} | "
                  f"{fa/16e6:.1f} / {fw/16e6:.1f} | {errs[0]:+.1f} / {errs[1]:+.1f} | {errs[2]:+.1f} / {errs[3]:+.1f} | "
                  f"{gn:.1f} |")
    RES["C2"] = c2
    print()


# ================================================================== Teil D: weitere Ideen (FEM-Tabelle)
def partD():
    print("## D Geometrie/Isolation (komplexe 2D-FEM, results/salt_index_2d.csv), Fehler Mitte | nass "
          "low / normal [%-Punkte]\n")
    rows = {}
    for line in open(os.path.join(ROOT, "simulation", "field", "results", "salt_index_2d.csv")).read().splitlines()[1:]:
        v = line.split(";")
        if v[2].startswith("Leitung"):
            continue
        rows.setdefault((v[0], float(v[1])), {})[(float(v[3]), v[2])] = float(v[7])
    print("| Variante | f [MHz] | Mitte low / normal | nass low / normal |")
    print("|---|---|---|---|")
    for name in ("4L SG gap2", "4L SG gap2 7628C", "4L IDE n6 gap1", "4L GSG ws6 gap2 7628C"):
        for f in (2.0, 4.0, 6.0):
            d = rows[(name, f)]
            ks = sorted(d)
            mid = [d[k] for k in ks if k[0] == 10.0]
            wet = [d[k] for k in ks if k[0] == 25.0]
            print(f"| {name} | {f:g} | {mid[0]:+.0f} / {mid[1]:+.0f} | {wet[0]:+.0f} / {wet[1]:+.0f} |")
    print()


def partD3():
    """RC-Oszillator schneller (kleineres R) + Teiler (SN74LVC1G80) vor dem Timer. 2 tpd = 6 ns (LVC1G14 bei 3.3 V,
    CONCEPTS 2.3) als Konstante eingerechnet; Drift von tpd siehe Text."""
    global C_DRY, C_WET_TAP
    old = (dict(OSC), C_DRY, C_WET_TAP)
    print("## D3 RC-Oszillator schneller (R kleiner) + Teiler vor dem Timer\n")
    print("| R | Teiler | f Luft / nass Leitung [MHz] | Mitte Leitung / low / normal [%] | theta bei 30 %: Leitung | "
          "low (Leitungs-Index) | normal (Leitungs-Index) | sigma_p 0.072 / 0.10 / low konz. / normal konz. (Leitungs-Index) | "
          "tpd-Drift +1 ns [%-P] |")
    print("|---|---|---|---|---|---|---|---|---|")
    out = []
    for R, div in ((10e3, 1), (4.7e3, 2), (2.2e3, 4), (1.5e3, 8), (1.0e3, 8), (0.68e3, 16)):
        OSC.update(R=R, tpd2=6e-9)
        C_DRY = c_meas(P.eps_topp(TH_DRY), 0.0)
        C_WET_TAP = c_meas(P.EPS_WET, sig_b(SIG_TAP, TH_WET))
        f_air = 1e-6 / periods(1.0, 0.0, R=R, crefs=(0.0,), tpd2=6e-9)[0]
        f_wet = 1e-6 / periods(P.EPS_WET, sig_b(SIG_TAP, TH_WET), R=R, crefs=(0.0,), tpd2=6e-9)[0]
        mid = [reading(TH_MID, sp) for sp in SALT.values()]
        cr = {k: crossing(sp, 30.0) for k, sp in SALT.items()}
        it = {k: reading(cr[k], SIG_TAP) for k in cr}
        ex = []
        for sp, conc in ((0.072, False), (0.10, False), (SIG_LOW, True), (SIG_NORM, True)):
            th = crossing(sp, 30.0, conc)
            ex.append("nie" if th is None else f"{reading(th, SIG_TAP):.0f}")
        # tpd-Drift: Kalibrierung mit 6 ns, Messung mit 7 ns (Leitung, Mitte)
        r0 = reading(TH_MID, SIG_TAP)
        OSC["tpd2"] = 7e-9
        r1 = reading(TH_MID, SIG_TAP)
        OSC["tpd2"] = 6e-9
        out.append({"R": R, "div": div, "f_air": f_air, "f_wet": f_wet, "mid": mid, "cross": cr, "idx_tap": it,
                    "extra": ex, "tpd_pp_per_ns": r1 - r0})
        print(f"| {R/1e3:.2f}k | /{div} | {f_air:.1f} / {f_wet:.1f} | " + " / ".join(f"{x:.0f}" for x in mid) +
              f" | {cr['Leitung']:.3f} | {cr['low']:.3f} ({it['low']:.0f} %) | {cr['normal']:.3f} ({it['normal']:.0f} %) | "
              + " / ".join(ex) + f" | {r1 - r0:+.1f} |")
    RES["D3"] = out
    print()
    print("### D3b Szenario konzentrierend (Ionen bleiben beim Austrocknen im Topf, ANNAHME physikalisch plausibel): "
          "theta beim Ausloesen der 30-%-Schwelle; Bedarf der Pflanze theta_need = theta(Leitung konstant, A) = 0.197\n")
    print("| R | Leitung | 0.072 | 0.10 | low | normal | Spannweite theta |")
    print("|---|---|---|---|---|---|---|")
    d3b = []
    for R, t in ((10e3, 0.0), (1.0e3, 6e-9), (0.68e3, 6e-9)):
        OSC.update(R=R, tpd2=t)
        C_DRY = c_meas(P.eps_topp(TH_DRY), 0.0)
        C_WET_TAP = c_meas(P.EPS_WET, sig_b(SIG_TAP, TH_WET))
        ths = [crossing(sp, 30.0, True) for sp in (SIG_TAP, 0.072, 0.10, SIG_LOW, SIG_NORM)]
        d3b.append((R, ths))
        print(f"| {R/1e3:.2f}k | " + " | ".join("nie" if x is None else f"{x:.3f}" for x in ths) +
              f" | {min(ths):.3f}-{max(ths):.3f} |")
    RES["D3b"] = d3b
    print()
    OSC.clear(); OSC.update(old[0]); C_DRY, C_WET_TAP = old[1], old[2]


# ================================================================== Energie, Flaeche, Kosten
def energy():
    import concept_energy as ce
    import energy_budget as eb
    print("## E Energie je Messung und Laufzeit (A-32, CR2032, 2 x 100 uF, Reaktionszeit 1 min)\n")
    # Strom C: Teiler 4 x SN74LVC1G80: Cpd 25 pF @3.3 V (S.8 Tab. 5.11) + Last 5 pF (ANNAHME) bei f, f/2, f/4, f/8
    # Oszillator SN74LVC1GU04: Cpd 13 pF @3.3 V (S.7 Tab. 6.8) + Querstrom im linearen Arbeitspunkt
    # (nicht spezifiziert, ANNAHME 5 mA), U2 LVC1G14 entfaellt.
    v, f = 3.0, 90e6
    i_div = sum((25e-12 + 5e-12) * v * f / 2 ** n for n in range(4))
    i_osc = 13e-12 * v * f + 5e-3
    i_c = i_div + i_osc
    # D3 (R 1 kOhm, /8): LVC1G14 (Cpd 22 pF @3.3 V, CONCEPTS 2.3) + Knoten ~20 pF bei 36 MHz,
    # 3 x SN74LVC1G80 (Cpd 25 pF + 5 pF Last) bei 36/18/9 MHz
    f3 = 36e6
    i_d3 = (22e-12 + 20e-12) * v * f3 + sum((25e-12 + 5e-12) * v * f3 / 2 ** n for n in range(3))
    variants = {
        "A Status quo (energy_budget Q_MEAS)": eb.Q_MEAS,
        "B1 3 Konfigurationen (wie A, Firmware)": eb.Q_MEAS,
        "B2 + 4. Konfiguration (R 5k, ~2 mA)": eb.Q_MEAS + 16 * 1e-3 * 2e-3,
        f"C 70-100 MHz: {i_c*1e3:.0f} mA x 24 x 0.6 ms": i_c * 24 * 0.6e-3,
        f"D3 R 1k /8: {i_d3*1e3:.0f} mA x 16 x 0.6 ms": i_d3 * 16 * 0.6e-3,
    }
    print(f"Strom D3 waehrend der Messung: {i_d3*1e3:.1f} mA (Grenze DIO12 10 mA -> P-FET empfohlen).\n")
    print(f"Strom C waehrend der Messung: Teiler {i_div*1e3:.1f} mA + Oszillator {i_osc*1e3:.1f} mA "
          f"(davon 5 mA ANNAHME) = **{i_c*1e3:.0f} mA** (DIO12 liefert spezifiziert 10 mA, DS S.31 -> Lastschalter).\n")
    print("| Variante | Ladung/Messung [uC] | Mittel pess. A [uA] | Laufzeit pess. A [Mt.] | Mittel pess. DS [uA] | "
          "Laufzeit pess. DS [Mt.] |")
    print("|---|---|---|---|---|---|")
    old = eb.Q_MEAS
    out = []
    for nm, q in variants.items():
        eb.Q_MEAS = q
        ia, ma, _, _ = ce.calc("CC2340R5", "CR2032 (Renata)", 200e-6, 1, "pessA", None, True)
        ib, mb, _, _ = ce.calc("CC2340R5", "CR2032 (Renata)", 200e-6, 1, "pessB", None, True)
        out.append([nm, q, ia, ma, ib, mb])
        print(f"| {nm} | {q*1e6:.0f} | {ia:.2f} | {eb.fmt_m(ma)} | {ib:.2f} | {eb.fmt_m(mb)} |")
    eb.Q_MEAS = old
    RES["E"] = out
    # Spannungseinbruch Puffer bei C: 1 Burst 0.6 ms
    dq = i_c * 0.6e-3
    print(f"\nEinbruch am Puffer 200 uF je 0.6-ms-Burst: {dq/200e-6*1e3:.0f} mV (ohne Nachladung) -> Bursts mit Pausen "
          f"wie LED-Regel (PINMAP Kap. 3).\n")
    RES["I_C"] = i_c


def area_cost():
    sys.path.insert(0, os.path.join(ROOT, "hardware", "sensor", "gen"))
    with redirect_stdout(io.StringIO()):
        import floorplan_options as fo
    cy = fo.CY
    a = lambda k: cy[k][0] * cy[k][1]  # noqa: E731
    prices = json.load(open(os.path.join(ROOT, "docs", "concepts", "bom", "jlc_prices.json")))

    def price(code, qty=20):
        t = prices[code]["tiers"]
        p = t[0][1]
        for n, pr in t:
            if qty >= n:
                p = pr
        return p
    # (Bezeichnung, Footprint-Schluessel, LCSC, Anzahl, Loetstellen je Stueck, Extended?)
    V = {
        "A": [],
        "B1": [],
        "B2": [("SN74LVC1G66DCKR", "SC70_5", "C113518", 1, 5, True), ("R 10k 0402", "R0402", "C25744", 1, 2, False),
               ("C 100 nF 0402", "C0402", "C1525", 1, 2, False), ("- C23 100 pF (Cref2)", "C0402", "C1546", -1, 2, False)],
        "C": [("SN74LVC1GU04DCKR", "SC70_5", "C485082", 1, 5, True), ("SDCL1005CR22JTDF 220 nH", "L0402", "C18834", 1, 2, True),
              ("C2 47 pF C0G (ANNAHME Wert)", "C0402", "C1555", 1, 2, False), ("R Rueckkopplung 1 MOhm", "R0402", "C25744", 1, 2, False),
              ("SN74LVC1G80DCKR (Teiler /16)", "SC70_5", "C473331", 4, 5, True), ("C 100 nF 0402", "C0402", "C1525", 2, 2, False),
              ("Lastschalter P-FET AO3401A (Typ wie Q1)", "SOT23", "C15127", 1, 3, False),
              ("R Gate-Pull-up 100k", "R0402", "C25741", 1, 2, False),
              ("- U2 SN74LVC1G14", "SC70_5", None, -1, 5, True), ("- R3", "R0402", "C25744", -1, 2, False),
              ("- C23 Cref2", "C0402", "C1546", -1, 2, False)],
        "D3 (R3 1k, /8)": [("SN74LVC1G80DCKR (Teiler /8)", "SC70_5", "C473331", 3, 5, True),
                           ("C 100 nF 0402", "C0402", "C1525", 1, 2, False),
                           ("Lastschalter P-FET AO3401A (Typ wie Q1)", "SOT23", "C15127", 1, 3, False),
                           ("R Gate-Pull-up 100k", "R0402", "C25741", 1, 2, False)],
        "D3 ohne P-FET (DIO12 direkt)": [("SN74LVC1G80DCKR (Teiler /8)", "SC70_5", "C473331", 3, 5, True),
                                         ("C 100 nF 0402", "C0402", "C1525", 1, 2, False)],
    }
    print("## F Flaeche und Kosten (Courtyards KiCad, Faktor 1.5 fuer Verdrahtung wie FLOORPLAN_OPTIONS, Band 20 mm "
          "breit; Preise JLC @20 Stk, Loetstelle 0.0016 USD, Extended-Feeder 3.07 USD je Typ und Bestellung)\n")
    print("| Variante | Courtyard-Delta [mm2] | Band-Delta [mm] | Teile-Delta [USD/Stk] | neue Extended-Typen | "
          "Einmal-Delta [USD/Bestellung] |")
    print("|---|---|---|---|---|---|")
    out = {}
    for vn, lst in V.items():
        da = sum(a(k) * n for _, k, _, n, _, _ in lst)
        usd = sum((price(c) if c else 0.057) * n + 0.0016 * j * n for _, _, c, n, j, _ in lst)
        ext = sorted({c for _, _, c, n, _, e in lst if e and n > 0})
        once = 3.07 * len(ext)
        out[vn] = (da, da * 1.5 / 20.0, usd, ext, once)
        print(f"| {vn} | {da:+.1f} | {da*1.5/20:+.1f} | {usd:+.3f} | {', '.join(ext) or '-'} | {once:+.2f} |")
    print("\n(- U2 LVC1G14 mit 0.057 USD aus CONCEPTS 2.3/research 6.3; Extended-Gebuehr U2 entfaellt in C, dafuer 3 neue Typen.)\n")
    RES["F"] = out


def main():
    buf = io.StringIO()
    with redirect_stdout(buf):
        print("# Ausgabe messkette_salz.py (Entscheidungsvorlage Messkette, REQ-MES-11)\n")
        part0()
        partA()
        partB()
        partC()
        partD()
        partD3()
        energy()
        area_cost()
    txt = buf.getvalue()
    open(os.path.join(HERE, "messkette_salz.txt"), "w").write(txt)
    json.dump(RES, open(os.path.join(HERE, "messkette_salz.json"), "w"), indent=1, default=str)
    print(txt)


if __name__ == "__main__":
    main()
