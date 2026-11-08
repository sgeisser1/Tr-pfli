#!/usr/bin/env python3
"""fluidi Sensor Rev B - SPICE (b): Messkette D3 = RC-Schmitt-Oszillator SN74LVC1G14 + Teiler /8 (3 x SN74LVC1G80),
Speisung OSC_PWR ueber P-FET Q2 (AO3401A, Gate DIO11). Sonde nach docs/interfaces/PROBE_CAPACITANCE.md Kap. 3.

Aufruf: .venv/bin/python simulation/spice/osc/osc_sim.py          (ca. 3-4 min)
Ausgabe: osc_results.csv, osc_report.txt, osc_waveforms.png, osc_freq.png, osc_last.cir (in diesem Ordner)

Schaltung wie Schaltplan Rev B (hardware/sensor/gen/parts.py: Q2, U2, R3, C21, C22, U4-U6, C25, TP4, TP5, E1):
  OSC_PWR   VDD -> Q2 RDS(on) 0.1 Ohm (ANNAHME bei VGS -2.4 V; < 85 mOhm bei -2.5 V, AOS_AO3401A_Datasheet_Rev3.1.pdf
            S.2) -> C21 + C25 (2 x 100 nF)
  Inverter  Schalter mit Hysterese (ngspice SW), R_on 40 Ohm (VOH >= 1.9 V @ -8 mA bei 2.3 V, >= 2.4 V @ -16 mA bei 3 V
            -> <= 50 / 37.5 Ohm; TI_SN74LVC1G14_Datasheet_SCES218AA.pdf S.7), Cpd 22 pF (S.8 Tab. 5.8),
            Laufzeit tpd als ideale Verzoegerungsleitung 1.6 / 3.0 (ANNAHME typ) / 5.5 ns (S.8 Tab. 5.6, 2.5 V, CL 15 pF;
            3.3 V: 1.5-4.6 ns).
  Schwellen S.7 Tab. 5.5 (DCK): VCC 2.3 V: VT+ 1.11-1.56, VT- 0.58-0.87, dVT 0.48-0.77; 3 V: VT+ 1.5-1.87,
            VT- 0.84-1.14, dVT 0.56-0.87; dazwischen linear (ANNAHME). 5 Ecken innerhalb der Grenzen (wie Rev A).
  Ausgang   OSZ_OUT: R3 + U4-CLK Ci 3.5 pF (TI_SN74LVC1G80_Datasheet_SCES221T.pdf S.6) + Leiterbahn 1 pF (ANNAHME).
  Knoten    PROBE_SENSE: Ci LVC1G14 4.5 pF + Leiterbahn/Durchfuehrung 5.5 pF (ANNAHME, CONCEPTS 2.3) + TP5 0.5 pF (ANNAHME).
  Cref1     22 pF C0G nach DIO8: "zu" = GPIO low ueber 100 Ohm (VOL <= 0.2 V @ 2 mA, CC2340 DS S.31);
            "auf" = Serie mit Pinkapazitaet 6 pF (DS S.32), Eingangspuffer aus. Cref2 entfaellt (Rev B).
  Teiler    3 x XSPICE d_dff (D an /Q), CLK->Q 1.5-6 ns bei 2.5 V / 1.3-4.2 ns bei 3.3 V (SN74LVC1G80 S.7 Tab. 5.8),
            Modell 3 ns (ANNAHME), Schwelle 0.5 VCC. Pruefung: MEAS_CLK = f_osc/8, Pulsbreite OSZ_OUT >= tw 2.5 ns
            (S.6 Tab. 5.6), fclock <= 160 MHz (S.6).
  Sonde     PROBE_CAPACITANCE.md Kap. 3: C0 7.05 pF || (Ci 99.0 pF in Serie mit (eps'*Cg || Rs)), Cg 1.719 pF,
            Rs = eps0/(sigma_b*Cg) (simulation/field/results/probe_lumped_3d_extrap.json). sigma_b nach
            simulation/field/params.py (Hilhorst, eps_off 4). Wasser: sigma_b = sigma_Wasser (ANNAHME freies Wasser).
Kriterien: MEAS_CLK <= Zaehlgrenze 10 MHz (CONCEPTS 2.3: LGPT sicher ca. 10-12 MHz, ANNAHME), tw, Ratiometrie,
           tpd-Einfluss (Kalibrierung absorbiert den Konstantanteil, Drift ueber VDD/T bleibt).
"""
import csv
import io
import json
import os
import sys
from contextlib import redirect_stdout

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "simulation", "field"))
import spicetools  # noqa: E402
import params as P  # noqa: E402

EPS0 = 8.8541878128e-12
FIT = json.load(open(os.path.join(ROOT, "simulation", "field", "results", "probe_lumped_3d_extrap.json")))
C_NODE = 9.9e-12           # Layout Rev B/C: U2 4.5 + TP5 0.5 + Bahnen/Vias/Zuleitung (field REPORT Kap. 11.3); vorher 10.5
C_PIN = 6e-12
C_REF1 = 22e-12
C_OUT = 4.5e-12            # U4 CLK 3.5 pF + 1 pF
F_COUNT = 10e6             # Zaehlgrenze DIO24 (ANNAHME, CONCEPTS 2.3)
TW_MIN = 2.5e-9            # SN74LVC1G80 S.6 Tab. 5.6
SIG_TAP, SIG_LOW, SIG_NORM = 0.035, 0.18, 0.37   # Porenwasser S/m (PROBE_CAPACITANCE Kap. 3)

# Sondenzustand: (eps', sigma_b [S/m])
PROBES = {
    "Luft": (1.0, 0.0),
    "trocken": (P.EPS_DRY, 0.0),
    "Mitte Leitung": (10.0, P.sigma_bulk(SIG_TAP, 10.0)),
    "nass verlustfrei": (P.EPS_WET, 0.0),
    "nass Leitung": (P.EPS_WET, P.sigma_bulk(SIG_TAP, P.EPS_WET)),
    "nass gedüngt low": (P.EPS_WET, P.sigma_bulk(SIG_LOW, P.EPS_WET)),
    "nass gedüngt normal": (P.EPS_WET, P.sigma_bulk(SIG_NORM, P.EPS_WET)),
    "Wasser verlustfrei": (80.0, 0.0),
    "Wasser Leitung": (80.0, SIG_TAP),
}
LOSSLESS = {"Luft": FIT["C_air"], "trocken": FIT["C_dry"], "nass verlustfrei": FIT["C_wet"],
            "Wasser verlustfrei": FIT["C_water"]}
R3S = [1e3, 10e3]
VDDS = [3.0, 2.4]
TH = {2.3: dict(vtp=(1.11, 1.56), vtn=(0.58, 0.87), dvt=(0.48, 0.77)),
      3.0: dict(vtp=(1.5, 1.87), vtn=(0.84, 1.14), dvt=(0.56, 0.87))}
CORNERS = {"typ": 3.0e-9, "hyst_min": 1.6e-9, "hyst_max": 5.5e-9, "mitte_hoch": 3.0e-9, "mitte_tief": 3.0e-9}
TPD_SWEEP = [2.0e-9, 3.0e-9, 4.0e-9]
DFF_TPD = 3e-9


def thresholds(vcc, corner):
    def lerp(key, i):
        a, b = TH[2.3][key][i], TH[3.0][key][i]
        return a + (b - a) * (min(max(vcc, 2.3), 3.0) - 2.3) / 0.7
    vtp_lo, vtp_hi, vtn_lo, vtn_hi = lerp("vtp", 0), lerp("vtp", 1), lerp("vtn", 0), lerp("vtn", 1)
    dmin, dmax = lerp("dvt", 0), lerp("dvt", 1)
    mid = ((vtp_lo + vtp_hi) / 2 + (vtn_lo + vtn_hi) / 2) / 2
    return {"typ": ((vtp_lo + vtp_hi) / 2, (vtn_lo + vtn_hi) / 2),
            "hyst_min": (mid + dmin / 2, mid - dmin / 2), "hyst_max": (mid + dmax / 2, mid - dmax / 2),
            "mitte_hoch": (vtp_hi, vtn_hi), "mitte_tief": (vtp_lo, vtn_lo)}[corner]


def probe_lines(eps, sig):
    c0, ci, cg = FIT["C0_pF"] * 1e-12, FIT["Ci_pF"] * 1e-12, FIT["Cg_pF"] * 1e-12
    L = [f"CP0 node 0 {c0:.5g}", f"CPI node pm {ci:.5g}", f"CPS pm 0 {eps * cg:.5g}"]
    L.append(f"RPS pm 0 {EPS0 / (sig * cg):.5g}" if sig > 0 else "RPS pm 0 1e12")
    return L


def netlist(vdd, probe, cref, corner, rfb, tpd=None, divider=True):
    tpd = CORNERS[corner] if tpd is None else tpd
    vtp, vtn = thresholds(vdd, corner)
    L = ["* fluidi osc_sim Rev B (D3) - erzeugt von osc_sim.py",
         f"VDD vdd 0 DC {vdd}",
         "RQ2 vdd opwr 0.1",
         f"C21 opwr 0 100n IC={vdd}", f"C25 opwr 0 100n IC={vdd}",
         "EIN src 0 node 0 2", "RT1 src t1 1k", f"T1 t1 0 t2 0 Z0=1k TD={tpd:.4g}", "RT2 t2 0 1k",
         "VONE one 0 DC 1", "RST one st 1k", "CST st 0 1f",
         "SHY st 0 t2 0 SWHY",
         f".model SWHY SW(VT={(vtp + vtn) / 2:.4f} VH={(vtp - vtn) / 2:.4f} RON=1 ROFF=1e9)",
         "VIS opwr opx DC 0", "SUP opx yint st 0 SWOUT", "SDN yint 0 one st SWOUT",
         ".model SWOUT SW(VT=0.5 VH=0 RON=40 ROFF=1e9)",
         "CPD yint 0 22p", "RY yint y 1m", f"COUT y 0 {C_OUT:.4g}",
         f"R3 y node {rfb:g}", f"CNODE node 0 {C_NODE:.4g}"]
    L += probe_lines(*PROBES[probe])
    on = cref == "f1"
    L += ["C22 node p1 22p", "Rp1 p1 0 100" if on else f"Cp1 p1 0 {C_PIN:.4g}"]
    if not on:
        L.append("RLp1 p1 0 100Meg")
    if divider:
        L += ["ABR1 [y] [dclk] adcb",
              f".model adcb adc_bridge(in_low={vdd / 2 - 0.01:.3f} in_high={vdd / 2 + 0.01:.3f})",
              "AFF1 qn1 dclk null null q1 qn1 dff", "AFF2 qn2 qn1 null null q2 qn2 dff",
              "AFF3 qn3 qn2 null null q3 qn3 dff",
              f".model dff d_dff(clk_delay={DFF_TPD:.3g} set_delay=1n reset_delay=1n)",
              "ABR2 [qn3] [meas] dacb",
              f".model dacb dac_bridge(out_low=0 out_high={vdd} t_rise=0.5n t_fall=0.5n)"]
    L.append(".ic v(node)=0")
    return "\n".join(L)


def crossings(t, y, th, rising=True):
    if rising:
        idx = np.where((y[:-1] < th) & (y[1:] >= th))[0]
    else:
        idx = np.where((y[:-1] >= th) & (y[1:] < th))[0]
    return t[idx] + (th - y[idx]) / (y[idx + 1] - y[idx]) * (t[idx + 1] - t[idx])


def measure(d, vdd):
    t, y, i = d["time"], d["v(y)"], d["i(VIS)"]
    tr = crossings(t, y, vdd / 2, True)[3:]
    tf = crossings(t, y, vdd / 2, False)
    if len(tr) < 4:
        return None
    per = np.diff(tr)
    m = (t >= tr[0]) & (t <= tr[-1])
    tf = tf[(tf > tr[0]) & (tf < tr[-1])]
    hi = min(tf[k] - tr[k] for k in range(min(len(tf), len(tr) - 1)))
    lo = min(per) - hi
    r = dict(f=1 / per.mean(), tw=min(hi, lo), i_avg=np.trapz(i[m], t[m]) / (t[m][-1] - t[m][0]),
             vmin=d["v(opwr)"][m].min())
    if "v(meas)" in d:
        tm = crossings(t, d["v(meas)"], vdd / 2, True)[1:]
        r["f8"] = 1 / np.diff(tm).mean() if len(tm) >= 3 else float("nan")
    return r


def sim(vdd, probe, cref, corner, rfb, tpd=None):
    fast = rfb < 5e3
    divider = fast
    tstop = "4u" if fast else "16u"
    step = "0.02n" if fast else "0.1n"
    net = netlist(vdd, probe, cref, corner, rfb, tpd, divider)
    sig = ["v(y)", "v(node)", "v(opwr)", "i(VIS)"] + (["v(meas)"] if divider else [])
    d = spicetools.run(net, os.path.join(HERE, "osc_last.cir"), sig, f"tran {step} {tstop} 0 {step} uic")
    return measure(d, vdd), d


def i_divider(f, vdd):
    """Dynamischer Strom Teiler: Cpd 25 pF je FF bei seiner Taktfrequenz (SN74LVC1G80 S.8 Tab. 5.11, 3.3 V) + 5 pF
    Last je Ausgang (ANNAHME)."""
    return vdd * (25e-12 * (f + f / 2 + f / 4) + 5e-12 * (f / 2 + f / 4 + f / 8))


def main():
    rows, waves = [], {}
    for rfb in R3S:
        for vdd in VDDS:
            for probe in PROBES:
                for corner in CORNERS:
                    for cref in ("f0", "f1"):
                        r, d = sim(vdd, probe, cref, corner, rfb)
                        row = dict(R3=rfb, vdd=vdd, probe=probe, corner=corner, cref=cref)
                        if r is None:
                            row["f_MHz"] = "keine Schwingung"
                        else:
                            row.update(f_MHz=round(r["f"] / 1e6, 4), f8_MHz=round(r.get("f8", r["f"] / 8) / 1e6, 4),
                                       f8_sim="ja" if "f8" in r else "f/8 gerechnet", tw_ns=round(r["tw"] * 1e9, 2),
                                       i_osc_mA=round(r["i_avg"] * 1e3, 3),
                                       i_div_mA=round(i_divider(r["f"], vdd) * 1e3, 3),
                                       osc_pwr_min=round(r["vmin"], 4))
                        rows.append(row)
                        if corner == "typ" and vdd == 3.0 and cref == "f0" and probe in ("trocken", "nass Leitung") \
                                and rfb == 1e3:
                            waves[probe] = d
    # tpd-Einfluss (typ-Schwellen, VDD 3.0 V, f0)
    tpdrows = []
    for rfb in R3S:
        for probe in ("Luft", "trocken", "Mitte Leitung", "nass Leitung", "Wasser Leitung"):
            fs = [sim(3.0, probe, "f0", "typ", rfb, tpd)[0]["f"] for tpd in TPD_SWEEP]
            tpdrows.append(dict(R3=rfb, probe=probe, f=fs))
    with open(os.path.join(HERE, "osc_results.csv"), "w", newline="") as fh:
        keys = ["R3", "vdd", "probe", "corner", "cref", "f_MHz", "f8_MHz", "f8_sim", "tw_ns", "i_osc_mA", "i_div_mA",
                "osc_pwr_min"]
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    buf = io.StringIO()
    with redirect_stdout(buf):
        report(rows, tpdrows)
    txt = buf.getvalue()
    print(txt)
    with open(os.path.join(HERE, "osc_report.txt"), "w") as fh:
        fh.write(txt)
    plot(rows, waves)


def report(rows, tpdrows):
    ok = [r for r in rows if not isinstance(r["f_MHz"], str)]
    bad = [r for r in rows if isinstance(r["f_MHz"], str)]
    for rfb in R3S:
        print(f"## R3 = {rfb/1e3:g} kOhm: f_osc (Cref aus) [MHz], min-max ueber 5 Schwellen-/tpd-Ecken (typ); "
              f"MEAS_CLK = f/8\n")
        print("| Sonde | VDD 3.0 V | VDD 2.4 V | MEAS_CLK max [MHz] | f1 (Cref1) typ 3.0 V |")
        print("|---|---|---|---|---|")
        for probe in PROBES:
            cells = []
            for vdd in VDDS:
                fs = [r["f_MHz"] for r in ok if r["R3"] == rfb and r["probe"] == probe and r["vdd"] == vdd
                      and r["cref"] == "f0"]
                ft = [r["f_MHz"] for r in ok if r["R3"] == rfb and r["probe"] == probe and r["vdd"] == vdd
                      and r["cref"] == "f0" and r["corner"] == "typ"]
                cells.append(f"{min(fs):.2f}-{max(fs):.2f} ({ft[0]:.2f})" if fs else "-")
            f8 = max(r["f8_MHz"] for r in ok if r["R3"] == rfb and r["probe"] == probe)
            f1 = [r["f_MHz"] for r in ok if r["R3"] == rfb and r["probe"] == probe and r["vdd"] == 3.0
                  and r["cref"] == "f1" and r["corner"] == "typ"]
            print(f"| {probe} | " + " | ".join(cells) + f" | {f8:.2f} | {f1[0]:.2f} |")
        sub = [r for r in ok if r["R3"] == rfb]
        print(f"\nGesamt R3 {rfb/1e3:g} k: f_osc {min(r['f_MHz'] for r in sub):.2f}-{max(r['f_MHz'] for r in sub):.2f} MHz, "
              f"MEAS_CLK max {max(r['f8_MHz'] for r in sub):.2f} MHz (Zaehlgrenze {F_COUNT/1e6:.0f} MHz, ANNAHME), "
              f"tw min {min(r['tw_ns'] for r in sub):.2f} ns (>= {TW_MIN*1e9} ns), fclock max "
              f"{max(r['f_MHz'] for r in sub):.1f} MHz (<= 160)")
        sim8 = [r for r in sub if r["f8_sim"] == "ja"]
        if sim8:
            dev = max(abs(r["f8_MHz"] * 8 / r["f_MHz"] - 1) for r in sim8)
            print(f"Teiler in SPICE (XSPICE d_dff): MEAS_CLK*8/f_osc - 1 max {dev*100:.3f} % ueber {len(sim8)} Faelle")
        for vdd in VDDS:
            s = [r for r in sub if r["vdd"] == vdd]
            io_ = max(r["i_osc_mA"] for r in s)
            idv = max(r["i_div_mA"] for r in s)
            print(f"VDD {vdd} V: Strom Oszillator <= {io_:.2f} mA (SPICE) + Teiler <= {idv:.2f} mA (Cpd-Rechnung) = "
                  f"{io_ + idv:.2f} mA; OSC_PWR >= {min(r['osc_pwr_min'] for r in s):.4f} V")
        print()
    print(f"Keine Schwingung in {len(bad)} von {len(rows)} Faellen\n")

    print("## Ratiometrie C_x = dC * T0/(T1-T0) - C_basis (feste Konstanten, ohne tpd-Korrektur), verlustfreie Sonde\n")
    dc = C_REF1 - C_REF1 * C_PIN / (C_REF1 + C_PIN)
    cbase = C_NODE + C_REF1 * C_PIN / (C_REF1 + C_PIN)
    print(f"dC = {dc*1e12:.2f} pF, C_basis = {cbase*1e12:.2f} pF\n")
    print("| R3 | Sonde | C wahr [pF] | C_x VDD 3.0 typ | Streuung Ecken + VDD [pF] |")
    print("|---|---|---|---|---|")
    for rfb in R3S:
        for probe, ctrue in LOSSLESS.items():
            cx = []
            for vdd in VDDS:
                for corner in CORNERS:
                    v = {r["cref"]: r["f_MHz"] for r in ok if r["R3"] == rfb and r["probe"] == probe
                         and r["vdd"] == vdd and r["corner"] == corner}
                    t0, t1 = 1 / v["f0"], 1 / v["f1"]
                    cx.append((vdd, corner, (dc * t0 / (t1 - t0) - cbase) * 1e12))
            typ = [c for v_, k, c in cx if v_ == 3.0 and k == "typ"][0]
            vals = [c for _, _, c in cx]
            print(f"| {rfb/1e3:g} k | {probe} | {ctrue:.1f} | {typ:.1f} | {min(vals):.1f} ... {max(vals):.1f} "
                  f"({max(vals)-min(vals):.1f}) |")
    print("\nDie Abweichung C_x - C wahr ist der Laufzeitanteil (tpd) + Cout-Kopplung; die Zwei-Punkt-Kalibrierung "
          "absorbiert den Konstantanteil, die Streuung ueber Ecken/VDD bleibt (-> tpd-Korrektur, PROTOTYP-PRUEFUNG).\n")

    print("## tpd-Einfluss (typ-Schwellen, VDD 3.0 V, f0): tpd 2 / 3 / 4 ns\n")
    print("| R3 | Sonde | f [MHz] bei 2 / 3 / 4 ns | df/f je ns | Anteil 2 tpd an der Periode (3 ns) |")
    print("|---|---|---|---|---|")
    for t in tpdrows:
        f2, f3, f4 = t["f"]
        dfdn = (f4 - f2) / 2 / f3
        print(f"| {t['R3']/1e3:g} k | {t['probe']} | {f2/1e6:.2f} / {f3/1e6:.2f} / {f4/1e6:.2f} | {dfdn*100:+.1f} % | "
              f"{2*3e-9*f3*100:.0f} % |")
    # Spanne trocken -> nass Leitung als Bezug (Index)
    print()
    for rfb in R3S:
        d = {t["probe"]: t["f"] for t in tpdrows if t["R3"] == rfb}
        span = d["trocken"][1] - d["nass Leitung"][1]
        shift = (d["Mitte Leitung"][2] - d["Mitte Leitung"][0]) / 2
        print(f"R3 {rfb/1e3:g} k: Frequenzspanne trocken -> nass (Leitung) {span/1e6:.2f} MHz; tpd +1 ns verschiebt "
              f"'Mitte' um {shift/1e6:+.3f} MHz = {-shift/span*100:+.1f} %-Punkte Index (ohne Ratiometrie)")


def plot(rows, waves):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(len(waves), 1, figsize=(10, 2.4 * len(waves)), sharex=True)
    for ax, (probe, d) in zip(np.atleast_1d(axs), waves.items()):
        m = (d["time"] > 2.5e-6) & (d["time"] < 3.2e-6)
        ax.plot(d["time"][m] * 1e6, d["v(y)"][m], lw=0.8, label="OSZ_OUT")
        ax.plot(d["time"][m] * 1e6, d["v(node)"][m], lw=0.8, label="PROBE_SENSE")
        ax.plot(d["time"][m] * 1e6, d["v(meas)"][m] + 0.02, lw=1.0, label="MEAS_CLK (/8, DIO24)")
        ax.set_title(f"R3 1 kOhm, Sonde {probe}, VDD 3.0 V, typ", fontsize=9)
        ax.set_ylabel("V")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7, loc="upper right")
    np.atleast_1d(axs)[-1].set_xlabel("t [us]")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "osc_waveforms.png"), dpi=120)
    ok = [r for r in rows if not isinstance(r["f_MHz"], str)]
    fig, axs = plt.subplots(1, 2, figsize=(13, 4.8))
    xs = list(PROBES)
    for ax, rfb in zip(axs, R3S):
        for k, (vdd, cref, mk) in enumerate([(3.0, "f0", "o"), (2.4, "f0", "s"), (3.0, "f1", "^")]):
            for i, p in enumerate(xs):
                fs = [r["f_MHz"] for r in ok if r["R3"] == rfb and r["probe"] == p and r["vdd"] == vdd
                      and r["cref"] == cref]
                if fs:
                    ax.plot([i + 0.12 * k] * 2, [min(fs), max(fs)], "-", color=f"C{k}")
                    ax.plot(i + 0.12 * k, np.median(fs), mk, color=f"C{k}",
                            label=f"f_osc VDD {vdd} V, {cref}" if i == 0 else None)
        if rfb < 5e3:
            ax.axhline(8 * F_COUNT / 1e6, color="r", ls="--", lw=0.8, label="Zaehlgrenze x 8 (80 MHz)")
        ax.set_xticks(range(len(xs)))
        ax.set_xticklabels(xs, fontsize=7, rotation=30, ha="right")
        ax.set_ylabel("f_osc [MHz]")
        ax.set_title(f"R3 = {rfb/1e3:g} kOhm" + (" (D3, /8 vor DIO24)" if rfb < 5e3 else " (Umloetvariante A)"))
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "osc_freq.png"), dpi=120)


if __name__ == "__main__":
    main()
