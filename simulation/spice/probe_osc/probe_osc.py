"""Verhaltensmodell RC-Schmitt-Oszillator mit verlustbehafteter Sonde (Salz, REQ-MES-11).

Zweck: Abschaetzung, wie das Ersatzschaltbild der Sonde aus der Feldsimulation
(simulation/field/results/lumped_fit.json bzw. docs/interfaces/PROBE_CAPACITANCE.md) die
Oszillatorfrequenz und den ratiometrisch bestimmten Kapazitaetswert veraendert.
KEIN Ersatz fuer die SPICE-Simulation mit dem Herstellermodell SN74LVC1G14 (Welle 2):
Schmitt-Inverter ideal mit Schwellen-Mittelwerten bei 3 V (VT+ 1.68 V, VT- 0.99 V,
TI_SN74LVC1G14_Datasheet_SCES218AA.pdf S.7 Tab. 5.5 laut research_elektronik.md 6.3),
Ausgangswiderstand 30 Ohm (ANNAHME), tpd = 0 (Verhaltensmodell).
Schaltung laut CONCEPTS.md 2.3: R = 4.7 kOhm Ausgang->Eingang, Sonde Eingang->GND, Cpar 10 pF (ANNAHME),
Cref1 = 22 pF zuschaltbar; C_mess = Cref1 * T0 / (T1 - T0) - Cpar.

Aufruf: .venv/bin/python simulation/spice/probe_osc/probe_osc.py
Ausgabe: simulation/spice/probe_osc/results.csv (+ Netzlisten *.cir)
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "simulation", "field"))
import params as P  # noqa: E402

VDD = 3.0
VTP, VTN = 1.68, 0.99
R_OSC = 4.7e3
C_PAR = 10e-12
C_REF = 22e-12

NET = """* fluidi Sonde: Schmitt-RC-Oszillator (Verhaltensmodell), Fall {case}
VDD vdd 0 {vdd}
Ecu cu 0 vdd in 1
S1 vdd out cu 0 swup
S2 out 0 in 0 swdn
.model swup sw vt={vtu} vh={vh} ron=30 roff=1e10
.model swdn sw vt={vtd} vh={vh} ron=30 roff=1e10
R1 out in {r}
Cpar in 0 {cpar}
{cref}
* Sonde (Ersatzschaltbild aus der Feldsimulation)
C0 in 0 {c0}
Ci in n1 {ci}
Cs n1 0 {cs}
Rs n1 0 {rs}
.ic v(in)=0 v(n1)=0
.tran 0.2n {tstop} 0 0.2n
.meas tran ta when v(in)={vm} rise=10
.meas tran tb when v(in)={vm} rise=40
.end
"""


def period(case, c0, ci, cs, rs, cref):
    vh = (VTP - VTN) / 2
    vtd = (VTP + VTN) / 2
    vtu = VDD - vtd
    f_est = 1 / (0.95 * R_OSC * (C_PAR + c0 + cs + (cref or 0)))
    tstop = 50 / f_est
    txt = NET.format(case=case, vdd=VDD, vtu=vtu, vtd=vtd, vh=vh, r=R_OSC, cpar=C_PAR,
                     cref=f"Cref in 0 {cref}" if cref else "", c0=c0, ci=ci, cs=cs, rs=rs,
                     tstop=tstop, vm=(VTP + VTN) / 2)
    p = os.path.join(HERE, f"{case}.cir")
    open(p, "w").write(txt)
    out = subprocess.run(["ngspice", "-b", p], capture_output=True, text=True).stdout
    ta = float(re.search(r"ta\s*=\s*([-+0-9.eE]+)", out).group(1))
    tb = float(re.search(r"tb\s*=\s*([-+0-9.eE]+)", out).group(1))
    return (tb - ta) / 30


def main():
    fit = json.load(open(os.path.join(ROOT, "simulation", "field", "results", "probe_lumped_3d.json")))
    c0, ci, cg = fit["C0_pF"] * 1e-12, fit["Ci_pF"] * 1e-12, fit["Cg_pF"] * 1e-12
    rows = []

    def meas(case, eps, sig):
        cs = eps * cg
        rs = P.EPS0 / (sig * cg) if sig > 0 else 1e15
        t0 = period(case + "_t0", c0, ci, cs, rs, None)
        t1 = period(case + "_t1", c0, ci, cs, rs, C_REF)
        c_meas = C_REF * t0 / (t1 - t0) - C_PAR
        return t0, t1, c_meas

    pts = {}
    pts["dry"] = meas("dry", P.EPS_DRY, 0.0)
    pts["wet_tap"] = meas("wet_tap", P.EPS_WET, P.sigma_bulk(0.035, P.EPS_WET))
    for name, sp in (("fert_low", 0.18), ("fert_normal", 0.37)):
        pts["wet_" + name] = meas("wet_" + name, P.EPS_WET, P.sigma_bulk(sp, P.EPS_WET))
    pts["mid_tap"] = meas("mid_tap", 10.0, P.sigma_bulk(0.035, 10.0))
    for name, sp in (("fert_low", 0.18), ("fert_normal", 0.37)):
        pts["mid_" + name] = meas("mid_" + name, 10.0, P.sigma_bulk(sp, 10.0))
    pts["air"] = meas("air", 1.0, 0.0)
    pts["wet_nosalt"] = meas("wet_nosalt", P.EPS_WET, 0.0)
    cd, cw = pts["dry"][2], pts["wet_tap"][2]
    with open(os.path.join(HERE, "results.csv"), "w") as f:
        f.write("case;f0_MHz;f1_MHz;C_meas_pF;index_pct\n")
        for k, (t0, t1, cm) in pts.items():
            idx = 100 * (cm - cd) / (cw - cd)
            f.write(f"{k};{1e-6/t0:.4f};{1e-6/t1:.4f};{cm*1e12:.3f};{idx:.2f}\n")
            print(f"{k:16s} f0 {1e-6/t0:7.3f} MHz  f1 {1e-6/t1:7.3f} MHz  C_mess {cm*1e12:7.2f} pF  Index {idx:7.1f} %")


if __name__ == "__main__":
    main()
