#!/usr/bin/env python3
"""fluidi Sensor Rev B - SPICE (a): Versorgung CR2032 + Puffer bei Funk-/Messlast (REQ-ENE-06, E1, OP-K6).

Aufruf: .venv/bin/python simulation/spice/supply/supply_burst.py
Ausgabe: supply_<Ereignis>.cir (R_int 100 Ohm, pessimistisch, Puffer 4x100uF), supply_results.csv, supply_waveforms.png, supply_drop.png (in diesem Ordner)

Modell (Schaltplan hardware/sensor/fluidi_sensor.kicad_sch, Netze VBAT/VDD):
  Zelle    Vocv in Serie mit R_int (konstant waehrend des Ereignisses).
           R_int-Faelle: 100 Ohm = Nachweisfall REQ-ENE-06; 130 / 220 Ohm = aus Panasonic CR2032 Datenblatt S.1
           "Operating voltage vs. load resistance (50 % DoD)" abgelesen: 20 degC 1 kOhm -> ca. 2.65 V, -10 degC -> ca. 2.42 V,
           Leerlauf ca. 2.97 V -> R = (2.97 - V)/(V/1 kOhm) (ANNAHME Ablesung); 1000 Ohm = Lebensende-Dimensionierung
           TI SWRA349 S.10 (Ri = 1 kOhm); 500 Ohm Zwischenwert; 20 Ohm neue Zelle (ANNAHME).
           Vocv 3.0 V (neu) bzw. 2.7 V (Lebensende, SWRA349 S.11 "2.7 V good starting point").
  Pfad     AO3401A R_DS(on) <= 85 mOhm @ VGS -2.5 V (AOS DS S.2), Halterkontakt 50 mOhm (ANNAHME).
  Puffer   2 bzw. 4 x 100 uF CL31A107MQHNNNE (C1-C4; Rev B Prototyp 4 bestueckt, D-013) + 10 uF (C5); DC-Bias: keine lokale Kurve
           (Register: Murata/Samsung-Kurve nicht ladbar) -> ANNAHME Restkapazitaet 50 % bei 3 V (wie scripts/energy_budget.py
           DCBIAS) und Toleranz -20 % (Katalog: M = +-20 %). ESR 5 mOhm je Kondensator (ANNAHME).
  Last     CC2340R52 mit DCDC ab VDDS >= 2.2 V, darunter automatisch GLDO (DS S.18 Tab. 7.4 Fussnote 1).
           Stroeme bei VDDS 3.0 V (DS S.19/20 Tab. 7.9/7.10): CPU 2.6 mA (GLDO 4.1), TX 0 dBm 5.1 (9.0), TX +4 dBm 7.9
           (GLDO: ANNAHME x 9.0/5.1 = 13.9), RX 5.3 (9.0). DCDC-Eingangsleistung konstant -> I = I_3V * 3.0 V / VDD
           (ANNAHME). HFXO-Start 0.4 mA 0.36 ms (energy_budget.py, ANNAHME). Flash schreiben/loeschen 8.3 mA 1.7 ms +
           2.2 mA 1.2 ms je 2 kB (energy_budget.py nach DS S.21 Tab. 7.11).
           Zeiten pessimistisch x 1.5 (PESS_EVENT in scripts/energy_budget.py, ANNAHME).
  Profile  ADV: verbindbares Advertising auf 3 Kanaelen (TX 47 B = 376 us, RX-Fenster 250 us + Kanalwechsel 150 us),
           CPU 1.5 ms davor/danach (E1: CPU nicht gleichzeitig mit Funk, aber ohne Pause).
           VERB: Verbindung 50 ms (T_CONN, ANNAHME) als Ereigniszug im 7.5-ms-Intervall (kleinstes BLE-Intervall),
           je Ereignis RX 0.3 ms + TX 0.4 ms (ANNAHME), CPU davor/danach.
           MESS (Rev B, Messkette D3 ueber P-FET Q2 an VDD, nicht ueber den DCDC): CPU/Timer 2.6 mA (DCDC) waehrend
           der ganzen Messung (ANNAHME, CPU wach) + Messkette 10.2 mA (Oszillator + Teiler, MESSKETTE_SALZ Kap. 5;
           SPICE osc_sim.py liefert <= Wert, konservativ) als Konstantstrom an VDD:
             MESS: 4 Bursts x 0.6 ms (Kette ein, f0 + f1), dazwischen 30 ms Schlaf (Regel PINMAP FW-2);
             MESSD: 16 x 0.6 ms = 9.6 ms am Stueck (wie MESSKETTE_SALZ Kap. 5 gerechnet, verletzt FW-2).
           Einschaltstoss Q2: C21 + C25 (200 nF) aus dem Puffer, Ladungsteilung -> ca. 3 V x 0.2/160 = 4 mV (Handrechnung).
           LED: Blink 20 ms bei 3 mA (Regel Phase-3-Review 1.8).
           FLASH: Notspeichern nach Unterspannung (2 kB loeschen + schreiben, x 1.5).
Kriterien: REQ-ENE-06 Einbruch <= 0.2 V bei R_int 100 Ohm; E1 Abschaltung 2.4 V unter Last, VDDS bleibt >= 2.2 V (DCDC);
           kein Reset: VDDS >= 1.71 V (DS S.18 Tab. 7.3), BOD 1.67 V (DS S.18 Tab. 7.5); fallende Flanke <= 1 mV/us
           (DS S.18 Tab. 7.3 Fussnote 3).
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import spicetools  # noqa: E402

PESS_T = 1.5
I = dict(sleep=(1.15e-6, 1.15e-6), hfxo=(0.4e-3, 0.4e-3), cpu=(2.6e-3, 4.1e-3), tx0=(5.1e-3, 9.0e-3),
         tx4=(7.9e-3, 7.9e-3 * 9.0 / 5.1), rx=(5.3e-3, 9.0e-3), meas=(3.0e-3, 3.0e-3), led=(3.0e-3, 3.0e-3),
         fl_w=(8.3e-3, 8.3e-3), fl_e=(2.2e-3, 2.2e-3), mcpu=(2.6e-3, 4.1e-3))
ICHAIN = {"mcpu": 10.2e-3}   # Messkette D3 an VDD (nicht DCDC), nur im Zustand mcpu
RINT = [20, 100, 130, 220, 500, 1000]
CBUF = {"2x100uF nominal": 200e-6, "2x100uF DC-Bias 50%": 100e-6, "2x100uF DC-Bias 50%, -20%": 80e-6,
        "4x100uF DC-Bias 50%, -20%": 160e-6}
VOCV = [2.7]
KINDS = [("ADV", "tx0"), ("ADV", "tx4"), ("VERB", "tx0"), ("VERB", "tx4"), ("MESS", "-"), ("MESSD", "-"),
         ("LED", "-"), ("FLASH", "-")]
MODES = {"pess": PESS_T, "nom": 1.0}
T0 = 1e-3  # Beginn des Ereignisses


def profile(kind, txkey="tx0", p=PESS_T):
    """Liste (Dauer, Zustand). Funk-/CPU-Zeiten x p (pessimistisch 1.5, nominal 1.0)."""
    if kind == "ADV":
        seq = [(0.36e-3 * p, "hfxo"), (1.0e-3 * p, "cpu")]
        for _ in range(3):
            seq += [(376e-6 * p, txkey), ((250e-6 + 150e-6) * p, "rx")]
        seq += [(0.5e-3 * p, "cpu")]
    elif kind == "VERB":
        seq = [(0.36e-3 * p, "hfxo"), (1.0e-3 * p, "cpu")]
        t_int, t_conn = 7.5e-3, 50e-3
        for _ in range(int(round(t_conn / t_int))):
            busy = (0.3e-3 + 0.4e-3) * p
            seq += [(0.3e-3 * p, "rx"), (0.4e-3 * p, txkey), (t_int - busy, "sleep")]
        seq += [(0.5e-3 * p, "cpu")]
    elif kind == "MESS":
        seq = []
        for k in range(4):
            seq += [(0.6e-3 * p, "mcpu")] + ([(30e-3, "sleep")] if k < 3 else [])
    elif kind == "MESSD":
        seq = [(16 * 0.6e-3 * p, "mcpu")]
    elif kind == "LED":
        seq = [(20e-3, "led")]
    elif kind == "FLASH":
        seq = [(0.5e-3 * p, "cpu"), (1.2e-3 * p, "fl_e"), (1.7e-3 * p, "fl_w"), (0.5e-3 * p, "cpu")]
    else:
        raise ValueError(kind)
    return seq


def pwl(seq, which):
    """PWL-Punkte fuer DCDC- (0) bzw. GLDO-Strom (1) bzw. Messkette an VDD ("ch") mit 1-us-Flanken."""
    val = (lambda st: ICHAIN.get(st, 0.0)) if which == "ch" else (lambda st: I[st][which])  # noqa: E731
    pts = [(0.0, val("sleep")), (T0, val("sleep"))]
    t = T0
    for dur, st in seq:
        pts.append((t + 1e-6, val(st)))
        t += dur
        pts.append((t, val(st)))
    pts.append((t + 1e-6, val("sleep")))
    return pts, t


def netlist(seq, vocv, rint, cbuf):
    p_dc, t_end = pwl(seq, 0)
    p_ldo, _ = pwl(seq, 1)
    p_ch, _ = pwl(seq, "ch")
    fmt = lambda pts: " ".join(f"{t:.7g} {v:.6g}" for t, v in pts)  # noqa: E731
    c_each = cbuf / 2
    L = ["* fluidi supply_burst - erzeugt von supply_burst.py",
         f"VOC ocv 0 DC {vocv}",
         f"RINT ocv vbat {rint}",
         "RHLD vbat vbat2 0.05",
         "RFET vbat2 vdd 0.085",
         f"CB1 vdd cb1 {c_each:.6g} IC={vocv}", "RESR1 cb1 0 5m",
         f"CB2 vdd cb2 {c_each:.6g} IC={vocv}", "RESR2 cb2 0 5m",
         f"C5 vdd 0 5u IC={vocv}",
         f"VPDC pdc 0 PWL({fmt(p_dc)})",
         f"VPLDO pldo 0 PWL({fmt(p_ldo)})",
         f"VPCH pch 0 PWL({fmt(p_ch)})",
         "BCH vdd 0 I = v(pch)",
         "BLOAD vdd 0 I = (1/(1+exp(-(v(vdd)-2.2)/0.005))) * v(pdc)*3.0/max(v(vdd),1.0)"
         " + (1-1/(1+exp(-(v(vdd)-2.2)/0.005))) * v(pldo)"]
    tstop = t_end + 0.05
    return "\n".join(L), tstop


def simulate(kind, txkey, vocv, rint, cbuf, p=PESS_T, keep=False):
    seq = profile(kind, txkey if txkey != "-" else "tx0", p)
    net, tstop = netlist(seq, vocv, rint, cbuf)
    name = f"supply_{kind}{'_' + txkey if txkey != '-' else ''}.cir" if keep else "supply_tmp.cir"
    cir = os.path.join(HERE, name)
    d = spicetools.run(net, cir, ["v(vdd)", "v(vbat)", "i(VOC)"], f"tran 2u {tstop:.4g} uic", keep_cir=keep)
    t, v = d["time"], d["v(vdd)"]
    v0 = v[t < T0 * 0.9][-1]
    vmin = v.min()
    dvdt = np.diff(v) / np.diff(t)
    return dict(t=t, v=v, vbat=d["v(vbat)"], v0=v0, vmin=vmin, dv=v0 - vmin,
                slew=-dvdt.min() * 1e-3, t_end=T0 + sum(s[0] for s in seq))


def main():
    rows = []
    wave = {}
    for mode, p in MODES.items():
        for kind, tx in KINDS:
            for cname, cbuf in CBUF.items():
                for vocv in VOCV:
                    for rint in RINT:
                        r = simulate(kind, tx, vocv, rint, cbuf, p, keep=(rint == 100 and mode == "pess"))
                        rows.append(dict(mode=mode, burst=kind, tx=tx, cbuf=cname, c_eff_uF=cbuf * 1e6, vocv=vocv,
                                         rint=rint, v_start=round(r["v0"], 4), v_min=round(r["vmin"], 4),
                                         drop=round(r["dv"], 4), slew_mV_per_us=round(r["slew"], 5)))
                        if rint in (100, 1000) and mode == "pess" and cname == "2x100uF DC-Bias 50%, -20%":
                            wave[(kind, tx, rint)] = r
    out = os.path.join(HERE, "supply_results.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    def sel(**k):
        return [r for r in rows if all(r[a] == b for a, b in k.items())]

    def drop(mode, kind, tx, cname, ri):
        return sel(mode=mode, burst=kind, tx=tx, cbuf=cname, rint=ri)[0]["drop"]
    print("## REQ-ENE-06: Einbruch beim Senden, R_int = 100 Ohm, Vocv 2.7 V, Kriterium <= 0.2 V")
    print("(Zellen: Funk-/CPU-Zeiten pessimistisch x1.5 / nominal x1.0)\n")
    print("| Ereignis | " + " | ".join(CBUF) + " |")
    print("|---|" + "---|" * len(CBUF))
    for kind, tx in KINDS:
        cells = []
        for cname in CBUF:
            dp, dn = drop("pess", kind, tx, cname, 100), drop("nom", kind, tx, cname, 100)
            cells.append(f"{dp*1000:.0f} / {dn*1000:.0f} mV {'ok' if dp <= 0.2 else ('(ok nom.)' if dn <= 0.2 else 'X')}")
        print(f"| {kind} {tx} | " + " | ".join(cells) + " |")

    cp = "2x100uF DC-Bias 50%, -20%"
    print(f"\n## Einbruch [mV] je R_int, pessimistisch, Puffer {cp}, Vocv 2.7 V\n")
    print("| Ereignis | " + " | ".join(f"{r} Ohm" for r in RINT) + " |")
    print("|---|" + "---|" * len(RINT))
    for kind, tx in KINDS:
        print(f"| {kind} {tx} | " + " | ".join(f"{drop('pess', kind, tx, cp, ri)*1000:.0f}" for ri in RINT) + " |")

    print("\n## E1: Abschaltung bei VDD < 2.4 V unter Last -> tiefster VDDS danach (pessimistisch)\n")
    print("Regel A: Firmware misst VDD am Ende jedes ADV-Ereignisses (0 dBm). Regel B: Messung waehrend des schwersten")
    print("regulaeren Ereignisses (Verbindung +4 dBm) und LED nur, wenn der letzte Wert >= 2.4 V + Einbruch_LED.")
    print("Danach kann ein schwereres Ereignis hoechstens um (Einbruch_schwer - Einbruch_Mess) tiefer fallen.\n")
    print("| Puffer | R_int | VDDS min Regel A (schwerstes) | Regel B: VDDS min (FLASH nach Abschaltung) | DCDC >= 2.2 V (A/B) | kein Reset >= 1.71 V (A/B) |")
    print("|---|---|---|---|---|---|")
    regular = [("ADV", "tx0"), ("ADV", "tx4"), ("VERB", "tx0"), ("VERB", "tx4"), ("MESS", "-"), ("LED", "-")]
    # MESSD (Messung am Stueck) ist eine Regelverletzung (FW-2) und nicht "regulaer"; Ausgabe nur in den Tabellen
    for cname in CBUF:
        for ri in RINT:
            adv = drop("pess", "ADV", "tx0", cname, ri)
            worst_k = max(regular + [("FLASH", "-")], key=lambda k: drop("pess", k[0], k[1], cname, ri))
            worst = drop("pess", worst_k[0], worst_k[1], cname, ri)
            va = 2.4 - max(worst - adv, 0)
            ref = drop("pess", "VERB", "tx4", cname, ri)
            vb = 2.4 - max(drop("pess", "FLASH", "-", cname, ri) - ref, 0)
            print(f"| {cname} | {ri} | {va:.2f} V ({worst_k[0]} {worst_k[1]}) | {vb:.2f} V | "
                  f"{'ja' if va >= 2.2 else 'nein'} / {'ja' if vb >= 2.2 else 'nein'} | "
                  f"{'ja' if va >= 1.71 else 'NEIN'} / {'ja' if vb >= 1.71 else 'NEIN'} |")
    smax = max(r["slew_mV_per_us"] for r in rows)
    print(f"\nGroesste fallende Flanke VDD (alle Faelle): {smax:.4f} mV/us (Grenze 1 mV/us, DS S.18 Tab. 7.3 Fn. 3)")
    print(f"Ergebnisse: {os.path.relpath(out)}")
    plot(rows, wave)


def plot(rows, wave):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 3, figsize=(15, 4.5))
    for ax, (kind, tx) in zip(axs, [("ADV", "tx0"), ("VERB", "tx4"), ("LED", "-")]):
        for ri, col in ((100, "C0"), (1000, "C3")):
            r = wave[(kind, tx, ri)]
            m = r["t"] < r["t_end"] + 0.04
            ax.plot(r["t"][m] * 1e3, r["v"][m], col, label=f"VDD, R_int {ri} Ohm")
        ax.axhline(2.5, color="grey", ls=":", lw=0.8, label="Vocv - 0.2 V")
        ax.axhline(2.2, color="k", ls="--", lw=0.8, label="DCDC-Grenze 2.2 V")
        ax.set_title(f"{kind} {tx}, Vocv 2.7 V, C_eff 80 uF, pess.")
        ax.set_xlabel("t [ms]")
        ax.set_ylabel("V [V]")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "supply_waveforms.png"), dpi=120)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for cname, mk in zip(CBUF, "osd^"):
        for (kind, tx), ls in ((("ADV", "tx0"), "-"), (("VERB", "tx4"), "--")):
            ys = [next(r for r in rows if r["burst"] == kind and r["tx"] == tx and r["cbuf"] == cname
                       and r["mode"] == "pess" and r["rint"] == ri)["drop"] * 1000 for ri in RINT]
            ax.plot(RINT, ys, ls, marker=mk, label=f"{kind} {tx}, {cname}")
    ax.axhline(200, color="k", ls=":", label="REQ-ENE-06 0.2 V")
    ax.axvline(100, color="grey", lw=0.8)
    ax.set_xscale("log")
    ax.set_xlabel("R_int Zelle [Ohm]")
    ax.set_ylabel("Einbruch VDD [mV]")
    ax.set_title("Einbruch je Ereignis, Vocv 2.7 V, pessimistisch")
    ax.grid(alpha=0.3, which="both")
    ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "supply_drop.png"), dpi=120)


if __name__ == "__main__":
    main()
