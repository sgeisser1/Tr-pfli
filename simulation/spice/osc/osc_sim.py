#!/usr/bin/env python3
"""fluidi Sensor Rev A - SPICE (b): RC-Messoszillator SN74LVC1G14, Speisung ueber GPIO DIO12 (SENS_PWR).

Aufruf: .venv/bin/python simulation/spice/osc/osc_sim.py
Ausgabe: osc_results.csv, osc_waveforms.png, osc_freq.png, osc_last.cir (in diesem Ordner)

Schaltung wie Schaltplan Rev A (U2, R3 4.7 k, C21, C22/C23 an DIO8/DIO11, Sonde E1, DIO24):
  SENS_PWR  VDD -> R_on GPIO High-Drive 53 Ohm (VOH >= 2.47 V @ 10 mA, VDDS 3.0 V: DS CC2340 S.31) -> C21 + C24 (2 x 100 nF)
  Inverter  Schalter mit Hysterese (ngspice SW), R_on 40 Ohm aus VOH-Spezifikation (VOH >= 1.9 V @ -8 mA bei 2.3 V,
            >= 2.4 V @ -16 mA bei 3 V -> <= 50 / 37.5 Ohm; LVC DS S.7), Cpd 22 pF (LVC DS S.8 Tab. 5.8),
            Laufzeit tpd als ideale Verzoegerungsleitung: 1.6 / 3.0 (ANNAHME typ) / 5.5 ns
            (LVC DS S.8 Tab. 5.6, VCC 2.5 V +- 0.2 V, CL 15 pF).
  Schwellen LVC DS S.7 Tab. 5.5 (DCK): VCC 2.3 V: VT+ 1.11-1.56, VT- 0.58-0.87, dVT 0.48-0.77;
            3 V: VT+ 1.5-1.87, VT- 0.84-1.14, dVT 0.56-0.87; dazwischen linear (ANNAHME).
            Ecken: typ (Mitten), hyst_min/hyst_max (dVT-Grenzen um die Mitte), mitte_hoch/mitte_tief (VT+ und VT- an
            einer Grenze), jeweils innerhalb aller Datenblattgrenzen.
  Knoten    Ci LVC 4.5 pF (DS S.7) + Leiterbahnen/Pads 5.5 pF (ANNAHME) = 10 pF (CONCEPTS 2.3); DIO24-Eingang 6 pF
            (CI GPIO 5 typ / 7 max, CC2340 DS S.32) + TP4 1 pF (ANNAHME) am Ausgang.
  Cref      22 pF / 100 pF C0G nach GPIO: "zu" = GPIO low ueber 100 Ohm (VOL <= 0.2 V @ 2 mA, DS S.31);
            "auf" = Serie mit Pinkapazitaet 6 pF (DS S.32) - Eingangspuffer aus.
  Sonde     ANNAHME bis zur Feldsimulation (CONCEPTS 2.3): trocken 30 pF, nass 100 pF; leitfaehig nass:
            20 pF direkt + (100 pF Isolation FR4 in Serie mit R_Boden 1 kOhm bzw. 300 Ohm) - nur zur Plausibilisierung.
Kriterien: Frequenz 2-6 MHz (CONCEPTS 2.3: LGPT sicher bis ca. 10-12 MHz, ANNAHME), Pegel an DIO24 VIH >= 0.8 VDDS,
           VIL <= 0.2 VDDS (DS S.32), Ratiometrie: C_x aus f0/f1 mit festen Konstanten (ohne Kenntnis von R, VT, VDD).
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import spicetools  # noqa: E402

R_FB = 4.7e3
C_NODE = 10e-12
C_PIN = 6e-12
CREF = {"f0": None, "f1": 22e-12, "f2": 100e-12}
PROBES = {"trocken 30 pF": ("C", 30e-12), "nass 100 pF": ("C", 100e-12),
          "nass leitfaehig 1k": ("RC", 1e3), "nass leitfaehig 300R": ("RC", 300.0)}
VDDS = [3.0, 2.4]
TH = {2.3: dict(vtp=(1.11, 1.56), vtn=(0.58, 0.87), dvt=(0.48, 0.77)),
      3.0: dict(vtp=(1.5, 1.87), vtn=(0.84, 1.14), dvt=(0.56, 0.87))}


def thresholds(vcc, corner):
    def lerp(key, i):
        a, b = TH[2.3][key][i], TH[3.0][key][i]
        return a + (b - a) * (min(max(vcc, 2.3), 3.0) - 2.3) / 0.7
    vtp_lo, vtp_hi, vtn_lo, vtn_hi = lerp("vtp", 0), lerp("vtp", 1), lerp("vtn", 0), lerp("vtn", 1)
    dmin, dmax = lerp("dvt", 0), lerp("dvt", 1)
    mid = ((vtp_lo + vtp_hi) / 2 + (vtn_lo + vtn_hi) / 2) / 2
    if corner == "typ":
        return (vtp_lo + vtp_hi) / 2, (vtn_lo + vtn_hi) / 2
    if corner == "hyst_min":
        return mid + dmin / 2, mid - dmin / 2
    if corner == "hyst_max":
        return mid + dmax / 2, mid - dmax / 2
    if corner == "mitte_hoch":
        return vtp_hi, vtn_hi
    if corner == "mitte_tief":
        return vtp_lo, vtn_lo
    raise ValueError(corner)


CORNERS = {"typ": 3.0e-9, "hyst_min": 1.6e-9, "hyst_max": 5.5e-9, "mitte_hoch": 3.0e-9, "mitte_tief": 3.0e-9}


RSWEEP = []


def netlist(vdd, probe, cref, corner, rfb=R_FB):
    tpd = CORNERS[corner]
    vcc = vdd - 0.05  # SENS_PWR unter Last (ca. 1 mA x 53 Ohm), nur fuer die Schwellen
    vtp, vtn = thresholds(vcc, corner)
    L = ["* fluidi osc_sim - erzeugt von osc_sim.py",
         f"VDD vdd 0 DC {vdd}",
         "RGPIO vdd sens 53",
         f"C21 sens 0 100n IC={vdd}", f"C24 sens 0 100n IC={vdd}",
         # Laufzeit: Knotenspannung ueber ideale Leitung verzoegert
         "EIN src 0 node 0 2", "RT1 src t1 1k", f"T1 t1 0 t2 0 Z0=1k TD={tpd:.4g}", "RT2 t2 0 1k",
         # Schmitt-Trigger: ein Schalter mit Hysterese erzeugt den Zustand st (1 = Eingang low)
         "VONE one 0 DC 1", "RST one st 1k", "CST st 0 1f",
         "SHY st 0 t2 0 SWHY",
         f".model SWHY SW(VT={(vtp + vtn) / 2:.4f} VH={(vtp - vtn) / 2:.4f} RON=1 ROFF=1e9)",
         # Ausgangsstufe: Pull-up (st high) bzw. Pull-down (st low), je R_on 40 Ohm
         "VIS sens sensx DC 0", "SUP sensx yint st 0 SWOUT", "SDN yint 0 one st SWOUT",
         ".model SWOUT SW(VT=0.5 VH=0 RON=40 ROFF=1e9)",
         "CPD yint 0 22p", "RY yint y 1m",
         "CDIO24 y 0 6p", "CTP4 y 0 1p",
         f"R3 y node {rfb}",
         f"CNODE node 0 {C_NODE}"]
    kind, val = PROBES[probe]
    if kind == "C":
        L.append(f"CX node 0 {val}")
    else:
        L += ["CXD node 0 20p", "CXI node px 100p", f"RSOIL px 0 {val}"]
    for name, cval, pin in (("C22", 22e-12, "p1"), ("C23", 100e-12, "p2")):
        on = (cref == "f1" and name == "C22") or (cref == "f2" and name == "C23")
        L.append(f"{name} node {pin} {cval}")
        L.append(f"R{pin} {pin} 0 100" if on else f"C{pin} {pin} 0 {C_PIN}")
        if not on:
            L.append(f"RL{pin} {pin} 0 100Meg")
    L.append(".ic v(node)=0")
    return "\n".join(L), vtp, vtn


def measure(d, vdd):
    t, y, sens, i = d["time"], d["v(y)"], d["v(sens)"], d["i(VIS)"]
    th = vdd / 2
    idx = np.where((y[:-1] < th) & (y[1:] >= th))[0]
    tc = t[idx] + (th - y[idx]) / (y[idx + 1] - y[idx]) * (t[idx + 1] - t[idx])
    tc = tc[2:]  # Einschwingen verwerfen
    if len(tc) < 4:
        return None
    per = np.diff(tc)
    m = (t >= tc[0]) & (t <= tc[-1])
    return dict(f=1 / per.mean(), jitter=per.std() / per.mean(), ymax=y[m].max(), ymin=y[m].min(),
                sens_min=sens[m].min(), i_avg=np.trapz(i[m], t[m]) / (t[m][-1] - t[m][0]))


def main():
    rows, waves = [], {}
    for vdd in VDDS:
        for probe in PROBES:
            for corner in CORNERS:
                for cref in CREF:
                    net, vtp, vtn = netlist(vdd, probe, cref, corner)
                    d = spicetools.run(net, os.path.join(HERE, "osc_last.cir"), ["v(y)", "v(node)", "v(sens)", "i(VIS)"],
                                       "tran 0.1n 12u 0 0.1n uic")
                    r = measure(d, vdd)
                    if r is None:
                        rows.append(dict(vdd=vdd, probe=probe, corner=corner, cref=cref, vtp=round(vtp, 3), vtn=round(vtn, 3),
                                         f_MHz="keine Schwingung"))
                        continue
                    rows.append(dict(vdd=vdd, probe=probe, corner=corner, cref=cref, vtp=round(vtp, 3), vtn=round(vtn, 3),
                                     f_MHz=round(r["f"] / 1e6, 4), dio24_high=round(r["ymax"], 3),
                                     dio24_low=round(r["ymin"], 3), sens_pwr_min=round(r["sens_min"], 3),
                                     i_avg_mA=round(r["i_avg"] * 1e3, 3)))
                    if corner == "typ" and vdd == 3.0 and cref == "f0":
                        waves[probe] = d
    for rfb in (4.7e3, 3.9e3, 3.3e3):
        for probe in ("trocken 30 pF", "nass 100 pF"):
            net, vtp, vtn = netlist(3.0, probe, "f0", "typ", rfb)
            d = spicetools.run(net, os.path.join(HERE, "osc_last.cir"), ["v(y)", "v(node)", "v(sens)", "i(VIS)"],
                               "tran 0.1n 12u 0 0.1n uic")
            r = measure(d, 3.0)
            RSWEEP.append((rfb, probe, r["f"] / 1e6))
    out = os.path.join(HERE, "osc_results.csv")
    with open(out, "w", newline="") as fh:
        keys = ["vdd", "probe", "corner", "cref", "vtp", "vtn", "f_MHz", "dio24_high", "dio24_low", "sens_pwr_min",
                "i_avg_mA"]
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    report(rows)
    plot(rows, waves)


def report(rows):
    ok = [r for r in rows if not isinstance(r["f_MHz"], str)]
    bad = [r for r in rows if isinstance(r["f_MHz"], str)]
    print("## Frequenz f0 (Cref aus) [MHz], min-max ueber 5 Schwellen-/tpd-Ecken\n")
    print("| Sonde | VDD 3.0 V | VDD 2.4 V |")
    print("|---|---|---|")
    for probe in PROBES:
        cells = []
        for vdd in VDDS:
            fs = [r["f_MHz"] for r in ok if r["probe"] == probe and r["vdd"] == vdd and r["cref"] == "f0"]
            ft = [r["f_MHz"] for r in ok if r["probe"] == probe and r["vdd"] == vdd and r["cref"] == "f0"
                  and r["corner"] == "typ"]
            cells.append(f"{min(fs):.2f}-{max(fs):.2f} (typ {ft[0]:.2f})" if fs else "-")
        print(f"| {probe} | " + " | ".join(cells) + " |")
    print("\n## f1 (Cref1 22 pF) / f2 (Cref2 100 pF), typ, VDD 3.0 V [MHz]\n")
    print("| Sonde | f0 | f1 | f2 |")
    print("|---|---|---|---|")
    for probe in PROBES:
        v = {r["cref"]: r["f_MHz"] for r in ok if r["probe"] == probe and r["vdd"] == 3.0 and r["corner"] == "typ"}
        print(f"| {probe} | {v.get('f0', '-')} | {v.get('f1', '-')} | {v.get('f2', '-')} |")
    print("\n## Variation R3 (typ, VDD 3.0 V, f0) [MHz]\n")
    print("| R3 | trocken 30 pF | nass 100 pF |")
    print("|---|---|---|")
    for rfb in sorted({x[0] for x in RSWEEP}, reverse=True):
        v = {p: f for r_, p, f in RSWEEP if r_ == rfb}
        print(f"| {rfb/1e3:.1f} k | {v['trocken 30 pF']:.2f} | {v['nass 100 pF']:.2f} |")
    fmin = min(r["f_MHz"] for r in ok)
    fmax = max(r["f_MHz"] for r in ok)
    print(f"\nGesamtbereich aller Faelle: {fmin:.2f} - {fmax:.2f} MHz; keine Schwingung in {len(bad)} Faellen")
    for vdd in VDDS:
        hi = min(r["dio24_high"] for r in ok if r["vdd"] == vdd)
        lo = max(r["dio24_low"] for r in ok if r["vdd"] == vdd)
        sp = min(r["sens_pwr_min"] for r in ok if r["vdd"] == vdd)
        ia = max(r["i_avg_mA"] for r in ok if r["vdd"] == vdd)
        print(f"VDD {vdd} V: DIO24 high >= {hi:.3f} V (VIH {0.8*vdd:.2f} V), low <= {lo:.3f} V (VIL {0.2*vdd:.2f} V), "
              f"SENS_PWR >= {sp:.3f} V, Strom <= {ia:.2f} mA")
    # Ratiometrie: C_x aus f0/f1 mit festen Konstanten (nur verlustfreie Sonde)
    dc = 22e-12 - 22e-12 * C_PIN / (22e-12 + C_PIN)
    cbase = C_NODE + 22e-12 * C_PIN / (22e-12 + C_PIN) + 100e-12 * C_PIN / (100e-12 + C_PIN)
    print("\n## Ratiometrie: C_x = dC * T0/(T1 - T0) - C_basis (dC = 17.3 pF, C_basis = 20.4 pF), ohne tpd-Korrektur\n")
    print("| Sonde | VDD | Ecke | C_x wahr | C_x berechnet | Fehler |")
    print("|---|---|---|---|---|---|")
    errs = []
    for probe, (kind, val) in PROBES.items():
        if kind != "C":
            continue
        for vdd in VDDS:
            for corner in CORNERS:
                v = {r["cref"]: r["f_MHz"] for r in ok if r["probe"] == probe and r["vdd"] == vdd and r["corner"] == corner}
                t0, t1 = 1 / v["f0"], 1 / v["f1"]
                cx = dc * t0 / (t1 - t0) - cbase
                errs.append(cx / val - 1)
                print(f"| {probe} | {vdd} | {corner} | {val*1e12:.0f} pF | {cx*1e12:.1f} pF | {100*(cx/val-1):+.1f} % |")
    print(f"\nRatiometrie-Fehler (ohne Kalibrierung) {100*min(errs):+.1f} ... {100*max(errs):+.1f} % -> wird durch "
          "Zwei-Punkt-Kalibrierung + tpd-Korrektur (CONCEPTS 2.3) aufgefangen; Streuung zwischen Ecken = Restfehler")


def plot(rows, waves):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(len(waves), 1, figsize=(10, 2.2 * len(waves)), sharex=True)
    for ax, (probe, d) in zip(axs, waves.items()):
        m = (d["time"] > 8e-6) & (d["time"] < 10e-6)
        ax.plot(d["time"][m] * 1e6, d["v(y)"][m], label="OSZ_OUT (DIO24)")
        ax.plot(d["time"][m] * 1e6, d["v(node)"][m], label="PROBE_SENSE")
        ax.set_title(f"{probe}, VDD 3.0 V, typ", fontsize=9)
        ax.set_ylabel("V")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7, loc="upper right")
    axs[-1].set_xlabel("t [us]")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "osc_waveforms.png"), dpi=120)
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ok = [r for r in rows if not isinstance(r["f_MHz"], str)]
    xs = list(PROBES)
    for k, (vdd, cref, mk) in enumerate([(3.0, "f0", "o"), (2.4, "f0", "s"), (3.0, "f1", "^"), (3.0, "f2", "v")]):
        for i, p in enumerate(xs):
            fs = [r["f_MHz"] for r in ok if r["probe"] == p and r["vdd"] == vdd and r["cref"] == cref]
            if fs:
                ax.plot([i + 0.1 * k] * 2, [min(fs), max(fs)], "-", color=f"C{k}")
                ax.plot(i + 0.1 * k, np.median(fs), mk, color=f"C{k}", label=f"VDD {vdd} V, {cref}" if i == 0 else None)
    ax.axhspan(2, 6, color="green", alpha=0.08, label="Arbeitsbereich 2-6 MHz")
    ax.set_xticks(range(len(xs)))
    ax.set_xticklabels(xs, fontsize=8)
    ax.set_ylabel("f [MHz]")
    ax.set_title("RC-Oszillator: Frequenz je Sonde (Balken = Ecken min-max)")
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "osc_freq.png"), dpi=120)


if __name__ == "__main__":
    main()
