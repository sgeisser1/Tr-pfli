#!/usr/bin/env python3
"""fluidi - Lageplan fuer die Behelfs-Erstprogrammierung am offenen Board (Red-Team W-4).

Liest hardware/sensor/fluidi_sensor.kicad_pcb (pcbnew) und zeichnet die F-Seite im Bereich Elektronikband + Zellfach:
Pads mit Netz, Referenzen, Platinenkontur. Hervorgehoben: R9-Pad 1 (LED_R_UART_TX = DIO6, Anschluss CH343-RXD im Behelf),
R9-Pad 2 (UART_TX_MID, FALSCH), TP1/TP2, Clip-Pads (VBAT), Minuspad (GND), SW1.
Aufruf: .venv/bin/python hardware/programmer/gen/behelf_pads.py
Ausgabe: hardware/programmer/out/behelf_lageplan.png und Koordinatentabelle auf stdout
         (KiCad-Koordinaten; Mechanik-Koordinaten X = x - 150, Y = y - 30 nach docs/interfaces/PCB_OUTLINE.md Kap. 5).
"""
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
PCB = os.path.join(REPO, "hardware", "sensor", "fluidi_sensor.kicad_pcb")
OUT = os.path.join(REPO, "hardware", "programmer", "out", "behelf_lageplan.png")
X0, X1, Y0, Y1 = 135.5, 164.5, 33.0, 80.0

MARK = {("R9", "1"): ("tab:green", "R9-Pad 1 = DIO6 (RICHTIG)"),
        ("R9", "2"): ("tab:red", "R9-Pad 2 = UART_TX_MID (falsch)"),
        ("R6", "1"): ("tab:olive", "R6-Pad 1 = DIO6 (gleiches Netz)"),
        ("TP1", "1"): ("tab:orange", "TP1 UART_TX_PAD"),
        ("TP2", "1"): ("tab:blue", "TP2 UART_RX_PAD (CH343-TXD)"),
        ("BT1", "1"): ("tab:purple", "Clip-Pad VBAT (+)"),
        ("BT1", "2"): ("black", "Minuspad GND (-)"),
        ("SW1", "1"): ("tab:cyan", "SW1 (Taster DIO21)")}


def mm(v):
    return pcbnew.ToMM(v)


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    b = pcbnew.LoadBoard(PCB)
    fig, ax = plt.subplots(figsize=(7.5, 11))
    for d in b.GetDrawings():
        if d.GetLayer() == pcbnew.Edge_Cuts and d.GetClass() in ("PCB_SHAPE", "DRAWSEGMENT"):
            if d.GetShape() == pcbnew.SHAPE_T_SEGMENT:
                s, e = d.GetStart(), d.GetEnd()
                ax.plot([mm(s.x), mm(e.x)], [mm(s.y), mm(e.y)], "k-", lw=1.2)
            elif d.GetShape() == pcbnew.SHAPE_T_ARC:
                pts = [d.GetStart(), d.GetArcMid(), d.GetEnd()]
                ax.plot([mm(p.x) for p in pts], [mm(p.y) for p in pts], "k-", lw=1.2)
    rows = []
    used = set()
    for fp in b.GetFootprints():
        if fp.IsFlipped():
            continue
        ref = fp.GetReference()
        p = fp.GetPosition()
        if not (X0 <= mm(p.x) <= X1 and Y0 <= mm(p.y) <= Y1):
            continue
        for pad in fp.Pads():
            q, s = pad.GetPosition(), pad.GetBoundingBox()
            x, y = mm(q.x), mm(q.y)
            w, h = mm(s.GetWidth()), mm(s.GetHeight())
            key = (ref, pad.GetNumber())
            col, lab = MARK.get(key, ("0.75", None))
            ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=col, ec="k", lw=0.3,
                                   alpha=0.9 if lab else 0.6, zorder=3 if lab else 2))
            if lab and lab not in used:
                used.add(lab)
                ax.plot([], [], "s", color=col, label=lab)
                rows.append((ref, pad.GetNumber(), pad.GetNetname(), x, y, w, h))
        if ref in ("R9", "R6", "R8", "R10", "R11", "R12", "D1", "SW1", "TP1", "TP2", "C1", "Q1", "U1", "BT1"):
            ax.text(mm(p.x), mm(p.y) - 1.0, ref, fontsize=6, ha="center", zorder=4)
    ax.set_xlim(X0, X1)
    ax.set_ylim(Y1, Y0)
    ax.set_aspect("equal")
    ax.grid(alpha=0.25)
    ax.set_xlabel("x [mm] (KiCad), Mechanik X = x - 150")
    ax.set_ylabel("y [mm] (KiCad), Mechanik Y = y - 30; oben = Antenne")
    ax.set_title("fluidi Sensor Rev C, F-Seite: Anschlusspunkte Behelfs-Erstprogrammierung")
    ax.legend(fontsize=7, loc="lower left")
    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=160)
    print("| Ref | Pad | Netz | x [mm] | y [mm] | Pad b x h [mm] |")
    print("|---|---|---|---|---|---|")
    for r in sorted(rows):
        print(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]:.2f} | {r[4]:.2f} | {r[5]:.2f} x {r[6]:.2f} |")
    print("Bild:", os.path.relpath(OUT, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
