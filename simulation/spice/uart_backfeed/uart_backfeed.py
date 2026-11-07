#!/usr/bin/env python3
"""fluidi Sensor Rev A - SPICE (c): Rueckstrom in die Zelle ueber die UART-Pads (Auflagen R2-A1, R2-A4).

Aufruf: .venv/bin/python simulation/spice/uart_backfeed/uart_backfeed.py
Ausgabe: uart_backfeed_results.csv, uart_backfeed.png, uart_backfeed.cir (letzter Fall)

Schaltung (Schaltplan Rev A): Pad TP1 (TX) -> R10 100 k -> R9 100 k -> DIO6 (+ LED rot ueber R6 470 Ohm nach VDD);
Pad TP2 (RX) -> R12 100 k -> R11 100 k -> DIO20 (+ LED blau ueber R8 100 Ohm nach VDD). Pin -> ESD-Struktur nach VDDS
(CC2340 DS S.18 Tab. 7.1: nur "VDDS + 0.3 V", kein Strom-Grenzwert). VDD -> AO3401A (S = VDD, D = Zelle+, G = GND)
-> Zelle (Vcell, R_int 10 Ohm ANNAHME; kleiner R_int = mehr Strom).
  ESD-Diode: (1) "ideal" IS 1e-14, N 0.01 (Vf < 10 mV, konservativ wie CONCEPTS 2.7), (2) IS 1e-14, N 1 (ANNAHME).
  AO3401A: PMOS Level 1, VTO -0.9 V (VGS(th) -0.5...-1.3 V, AOS DS S.2), KP so dass R_DS(on) ca. 60 mOhm @ -2.5 V;
           Body-Diode Drain -> Source (DS S.1 Schaltbild). Bei VDD > |VTO| leitet der Kanal in beide Richtungen.
  Geraetelast: 0 A (konservativ, CONCEPTS 2.7). LED-Sperrstrom vernachlaessigt (Pin liegt hoechstens ca. Vf ueber VDD).
Faelle: Quelle 5.5 V (USB-Fehler) / 3.3 V / 1.8 V an einem bzw. beiden Pads; Einzelfehler: je ein 100 k ueberbrueckt;
        Zelle 3.0 V (neu), 2.0 V (CONCEPTS 2.7), 0 V (entladen, R2-L01).
Grenzen (R2-A1): Fehlerfall <= 10 mA (Maxell CR2032, docs/references/Maxell_CR_Warnings_12e_2012.pdf S.2);
        Ladung <= 1 % C_nenn = 2.25 mAh (Panasonic CR2032 225 mAh) -> Zeit bis 1 % = 2.25 mAh / I.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import spicetools  # noqa: E402

CAP_1PCT_MAH = 2.25
I_LIMIT = 10e-3


def netlist(vsrc, pads, short, vcell, esd):
    """pads: 'TX', 'RX' oder 'beide'; short: None, 'TX_R10', 'TX_R9', 'RX_R12', 'RX_R11'."""
    r = {k: (1e-3 if short == k else 100e3) for k in ("TX_R10", "TX_R9", "RX_R12", "RX_R11")}
    L = ["* fluidi uart_backfeed - erzeugt von uart_backfeed.py",
         f"VCELL cellp 0 DC {vcell}", "RINT cellp bat 10",
         # AO3401A: D = bat, S = vdd, G = 0, Bulk = S
         "M1 bat 0 vdd vdd PFET W=1 L=1",
         ".model PFET PMOS(LEVEL=1 VTO=-0.9 KP=10)",
         "DBODY bat vdd DBD", ".model DBD D(IS=1e-12 N=1.0)",
         "RLEAK vdd 0 1e12",
         f".model DESD D(IS=1e-14 N={0.01 if esd == 'ideal' else 1.0})"]
    for pad, r1, r2, pin in (("TX", "TX_R10", "TX_R9", "dio6"), ("RX", "RX_R12", "RX_R11", "dio20")):
        drive = pads in (pad, "beide")
        L.append(f"V{pad} pad{pad} 0 DC {vsrc if drive else 0}")
        L.append(f"RS{pad} pad{pad} pin{pad}a {'1e-3' if drive else '1e12'}")
        L.append(f"R{r1} pin{pad}a mid{pad} {r[r1]}")
        L.append(f"R{r2} mid{pad} {pin} {r[r2]}")
        L.append(f"DESD{pad} {pin} vdd DESD")
        L.append(f"DESDN{pad} 0 {pin} DESD")
    return "\n".join(L)


def main():
    rows = []
    cases = []
    for vsrc in (5.5, 3.3, 1.8):
        for pads in ("TX", "RX", "beide"):
            for short in (None, "TX_R10", "RX_R11"):
                if short and not (pads == "beide" or short.startswith(pads)):
                    continue
                for vcell in (3.0, 2.0, 0.0):
                    for esd in ("ideal", "diode"):
                        cases.append((vsrc, pads, short, vcell, esd))
    for vsrc, pads, short, vcell, esd in cases:
        d = spicetools.run(netlist(vsrc, pads, short, vcell, esd), os.path.join(HERE, "uart_backfeed.cir"),
                           ["i(VCELL)", "v(vdd)", "i(VTX)", "i(VRX)"], "op")
        i_cell = d["i(VCELL)"][0]  # in den Pluspol der Quelle hinein = Ladestrom der Zelle (positiv)
        i_pads = -(d["i(VTX)"][0] + d["i(VRX)"][0])
        h1 = CAP_1PCT_MAH * 1e-3 / i_cell if i_cell > 1e-9 else float("inf")
        rows.append(dict(v_quelle=vsrc, pads=pads, einzelfehler=short or "-", v_zelle=vcell, esd=esd,
                         i_pads_uA=round(i_pads * 1e6, 3), i_zelle_uA=round(i_cell * 1e6, 3),
                         v_vdd=round(d["v(vdd)"][0], 3), stunden_bis_1pct=round(h1, 1) if h1 != float("inf") else "-",
                         abstand_10mA=round(I_LIMIT / i_cell) if i_cell > 1e-9 else "-"))
    out = os.path.join(HERE, "uart_backfeed_results.csv")
    with open(out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("## Ladestrom in die Zelle [uA] (ESD ideal 0 V / Diodenmodell), Grenze 10 mA, 1 % C = 2.25 mAh\n")
    print("| Quelle | Pads | Einzelfehler | Zelle 3.0 V | Zelle 2.0 V | Zelle 0 V | h bis 1 % C (0 V, ideal) |")
    print("|---|---|---|---|---|---|---|")
    for vsrc in (5.5, 3.3, 1.8):
        for pads in ("TX", "RX", "beide"):
            for short in ("-", "TX_R10", "RX_R11"):
                sub = [r for r in rows if r["v_quelle"] == vsrc and r["pads"] == pads and r["einzelfehler"] == short]
                if not sub:
                    continue
                cells = []
                for vc in (3.0, 2.0, 0.0):
                    a = next(r for r in sub if r["v_zelle"] == vc and r["esd"] == "ideal")["i_zelle_uA"]
                    b = next(r for r in sub if r["v_zelle"] == vc and r["esd"] == "diode")["i_zelle_uA"]
                    cells.append(f"{a:.1f} / {b:.1f}")
                h = next(r for r in sub if r["v_zelle"] == 0.0 and r["esd"] == "ideal")["stunden_bis_1pct"]
                print(f"| {vsrc} V | {pads} | {short} | " + " | ".join(cells) + f" | {h} |")
    imax = max(r["i_zelle_uA"] for r in rows)
    print(f"\nGroesster Ladestrom aller Faelle: {imax:.1f} uA = 1/{I_LIMIT / (imax * 1e-6):.0f} der Grenze 10 mA; "
          f"Zeit bis 1 % C bei diesem Strom: {CAP_1PCT_MAH * 1e-3 / (imax * 1e-6):.0f} h")
    print("Injektionsstrom in die ESD-Struktur je Pin = Padstrom (gleiche Groesse); DS nennt keinen Grenzwert "
          "-> PROTOTYP-PRUEFUNG R2-A4")
    print(f"Ergebnisse: {os.path.relpath(out)}")
    plot(rows)


def plot(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 4.5))
    labels, vals = [], []
    for vsrc in (5.5, 3.3):
        for pads, short in (("TX", "-"), ("TX", "TX_R10"), ("beide", "-"), ("beide", "TX_R10")):
            r = next(x for x in rows if x["v_quelle"] == vsrc and x["pads"] == pads and x["einzelfehler"] == short
                     and x["v_zelle"] == 0.0 and x["esd"] == "ideal")
            labels.append(f"{vsrc} V\n{pads}\n{short}")
            vals.append(r["i_zelle_uA"])
    ax.bar(range(len(vals)), vals, color="C0")
    ax.set_xticks(range(len(vals)))
    ax.set_xticklabels(labels, fontsize=7)
    ax.set_ylabel("Ladestrom Zelle [uA] (Zelle 0 V, ESD ideal)")
    ax.set_title("UART-Pads: Rueckstrom-Worst-Case (Grenze Fehlerfall 10 mA = 10000 uA)")
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:.1f}", ha="center", va="bottom", fontsize=7)
    ax.grid(alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "uart_backfeed.png"), dpi=120)


if __name__ == "__main__":
    main()
