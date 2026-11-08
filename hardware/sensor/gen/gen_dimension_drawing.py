#!/usr/bin/env python3
"""fluidi Sensor Rev C - Masszeichnung der Platine (PDF), nur Ausgabe, die Platine wird NICHT veraendert.

Aufruf (Repo-Wurzel):  .venv/bin/python hardware/sensor/gen/gen_dimension_drawing.py
Ausgabe:               hardware/sensor/out/pdf/fluidi_sensor_masszeichnung.pdf (A4 hoch, 3 Seiten)
  Seite 1  Massstab 1:1 - Kontur, Hauptmasse, Zonengrenzen (Y), Stecktiefe, Vergusskanten, Elektrodenumriss,
           Bohrungen (aus der Excellon-Datei), Toleranzen.
  Seite 2  Massstab 3:1 - Kopf Y -1 ... 60: Bauteilhoehen-Zonen F/B, Bauteilumrisse (Courtyard) mit Hoehen,
           Regelflaechen (Antennen-Keepout, Kappenanschlag, Kragenfeld), Testpads.
  Seite 3  Massstab 5:1 - Bestueckungsplan Kopf F (Pads, Courtyard, Referenz, Pin 1 rot, DNP gekreuzt) als
           lesbare Vergroesserung zu out/pdf/fluidi_sensor_bestueckung_F.pdf (1:1).

Quellen (alle Geometrie aus der Platine bzw. den Bohrdaten, nichts abgetippt):
  hardware/sensor/fluidi_sensor.kicad_pcb (pcbnew, nur gelesen), Hilfsursprung = Mitte Oberkante, Y nach unten
  hardware/sensor/out/gerber/fluidi_sensor-PTH.drl / -NPTH.drl (Bohrungen wie bestellt)
  Hoehengrenzen je Zone: docs/interfaces/PCB_OUTLINE.md Kap. 3 und Kap. 8 (Rev C)
  Bauteilhoehen: PCB_OUTLINE.md Kap. 8 (dort mit Datenblatt-Seite); C1-C4 = KiCad-Modell (ANNAHME, dort vermerkt)
  Toleranzen: docs/references/JLCPCB_NOTES.md Kap. 3 (Kontur +-0.2 mm, Dicke +-10 %)
  Vergusskanten Y 22.7 / 46.9 / 52.2: hardware/sensor/out/LAYOUT_REV_B.md Kap. 4 (PCB_OUTLINE Rev C)
"""
import datetime
import hashlib
import os
import re

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402
from matplotlib.patches import Arc, Rectangle, Polygon  # noqa: E402
import numpy as np  # noqa: E402
import pcbnew  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
PCB = os.path.join(ROOT, "hardware", "sensor", "fluidi_sensor.kicad_pcb")
GERBER = os.path.join(ROOT, "hardware", "sensor", "out", "gerber")
OUT = os.path.join(ROOT, "hardware", "sensor", "out", "pdf", "fluidi_sensor_masszeichnung.pdf")
A4 = (210.0, 297.0)
MM = 1 / 25.4

# Zonen (KiCad-Y) und max. Bauteilhoehe F / B  - PCB_OUTLINE.md Kap. 3 / Kap. 8 (Rev C)
ZONES = [("Z1 Antenne", 0.0, 5.7, "0", "0"),
         ("Z2 Band", 5.7, 20.8, "2.0", "0 (Pads)"),
         ("Z3 Schott", 20.8, 23.2, "0", "0"),
         ("Z4 Fach", 23.2, 46.7, "4.1 (nur BT1)", "0"),
         ("Z5B Kragen", 46.7, 50.0, "0.7 (nur Feld)", "0"),
         ("Z5A Dichtstreifen", 50.0, 52.7, "0", "0"),
         ("Z6 frei", 52.7, 58.5, "0", "0"),
         ("Z7 Sonde", 58.5, 158.5, "0", "0")]
ZONE_COL = {"0": "#f2f2f2", "2.0": "#cfe8ff", "4.1 (nur BT1)": "#ffe0b3", "0.7 (nur Feld)": "#e0f0d0"}
# Bauteilhoehen [mm] - PCB_OUTLINE.md Kap. 8 (Quelle je Zeile dort; C1-C4 KiCad-Modell = ANNAHME)
HEIGHTS = {"SW1": "2.0", "BT1": "4.1", "L1": "1.0", "D1": "0.6", "U1": "1.0", "U3": "0.6", "C24": "0.55",
           "C1": "1.6*", "C2": "1.6*", "C3": "1.6*", "C4": "1.6*"}
LINES = [(22.7, "Vergusskante Schott Y 22.7"), (46.9, "Vergusskante Kragen Y 46.9"),
         (52.2, "Vergusskante Sonde Y 52.2"), (58.5, "max. Stecktiefe Y 58.5 (Silk F+B)")]


def board():
    b = pcbnew.LoadBoard(PCB)
    o = b.GetDesignSettings().GetAuxOrigin()

    def p(v):
        return pcbnew.ToMM(v.x - o.x), pcbnew.ToMM(v.y - o.y)
    return b, p


def outline(b, p):
    segs = []
    for d in b.GetDrawings():
        if d.GetLayerName() != "Edge.Cuts":
            continue
        if d.GetShapeStr() == "Arc":
            c, s, e = p(d.GetCenter()), p(d.GetStart()), p(d.GetEnd())
            segs.append(("arc", c, s, e, pcbnew.ToMM(d.GetRadius())))
        else:
            segs.append(("line", p(d.GetStart()), p(d.GetEnd())))
    return segs


def draw_outline(ax, segs, lw=0.5):
    for s in segs:
        if s[0] == "line":
            ax.plot([s[1][0], s[2][0]], [s[1][1], s[2][1]], "k-", lw=lw)
        else:
            _, c, a, e, r = s
            ang = sorted([np.degrees(np.arctan2(a[1] - c[1], a[0] - c[0])),
                          np.degrees(np.arctan2(e[1] - c[1], e[0] - c[0]))])
            if ang[1] - ang[0] > 180:
                ang = [ang[1], ang[0] + 360]
            ax.add_patch(Arc(c, 2 * r, 2 * r, theta1=ang[0], theta2=ang[1], lw=lw, color="k"))


def outline_polygon(segs):
    """Kontur als geschlossenes Polygon (Segmente verketten, Boegen mit 12 Punkten)."""
    pieces = []
    for sg in segs:
        if sg[0] == "line":
            pieces.append([sg[1], sg[2]])
        else:
            _, c, a, e, r = sg
            a0, a1 = np.arctan2(a[1] - c[1], a[0] - c[0]), np.arctan2(e[1] - c[1], e[0] - c[0])
            d = (a1 - a0 + np.pi) % (2 * np.pi) - np.pi          # kurzer Bogen
            pieces.append([(c[0] + r * np.cos(a0 + d * t), c[1] + r * np.sin(a0 + d * t)) for t in np.linspace(0, 1, 12)])
    poly = pieces.pop(0)
    while pieces:
        end = poly[-1]
        for i, pc in enumerate(pieces):
            if np.hypot(pc[0][0] - end[0], pc[0][1] - end[1]) < 1e-3:
                poly += pc[1:]
                break
            if np.hypot(pc[-1][0] - end[0], pc[-1][1] - end[1]) < 1e-3:
                poly += pc[::-1][1:]
                break
        else:
            raise RuntimeError("Kontur nicht geschlossen")
        pieces.pop(i)
    return poly


def zone_fill(ax, segs, ymax=None):
    clip = Polygon(outline_polygon(segs), closed=True, fc="none", ec="none")
    ax.add_patch(clip)
    for name, y1, y2, hf, hb in ZONES:
        y2c = y2 if ymax is None else min(y2, ymax)
        r = Rectangle((-13, y1), 26, y2c - y1, color=ZONE_COL.get(hf, "#f2f2f2"), lw=0, zorder=0)
        ax.add_patch(r)
        r.set_clip_path(clip)


def drills():
    res = {}
    for kind in ("PTH", "NPTH"):
        txt = open(os.path.join(GERBER, f"fluidi_sensor-{kind}.drl")).read()
        tools = dict(re.findall(r"^T(\d+)C([\d.]+)", txt, re.M))
        cur, pts = None, []
        for line in txt.splitlines():
            m = re.match(r"^T(\d+)$", line)
            if m:
                cur = m.group(1)
            m = re.match(r"^X(-?[\d.]+)Y(-?[\d.]+)", line)
            if m and cur:
                pts.append((float(m.group(1)), -float(m.group(2)), float(tools[cur])))
        res[kind] = pts
    return res


def page_axes(fig, x0, y0, xmin, xmax, ymin, ymax, scale):
    """Achse so platzieren, dass 1 Dateneinheit = scale mm auf dem Papier (x0/y0 = linke obere Ecke in mm)."""
    w, h = (xmax - xmin) * scale, (ymax - ymin) * scale
    ax = fig.add_axes([x0 / A4[0], 1 - (y0 + h) / A4[1], w / A4[0], h / A4[1]])
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymax, ymin)        # Y nach unten wie KiCad
    ax.set_aspect("equal")
    ax.axis("off")
    return ax


def dim_v(ax, x, y1, y2, text, fs=5, side=1):
    ax.annotate("", (x, y1), (x, y2), arrowprops=dict(arrowstyle="<->", lw=0.4, shrinkA=0, shrinkB=0))
    ax.text(x + side * 0.6, (y1 + y2) / 2, text, rotation=90, va="center", ha="left" if side > 0 else "right",
            fontsize=fs)


def dim_h(ax, y, x1, x2, text, fs=5, above=True):
    ax.annotate("", (x1, y), (x2, y), arrowprops=dict(arrowstyle="<->", lw=0.4, shrinkA=0, shrinkB=0))
    ax.text((x1 + x2) / 2, y - 0.6 if above else y + 0.6, text, ha="center", va="bottom" if above else "top",
            fontsize=fs)


def title(fig, page, sub, sha):
    import textwrap
    fig.text(10 / A4[0], 1 - 8 / A4[1], "fluidi Sensor - Masszeichnung Platine Rev C", fontsize=11,
             weight="bold", va="top")
    fig.text(10 / A4[0], 1 - 14 / A4[1], page, fontsize=8, va="top")
    fig.text(10 / A4[0], 1 - 18 / A4[1], textwrap.fill(sub, 150), fontsize=6, va="top")
    fig.text(10 / A4[0], 9 / A4[1], textwrap.fill(
             f"Quelle: hardware/sensor/fluidi_sensor.kicad_pcb (sha256 {sha}), Bohrdaten hardware/sensor/out/gerber/*.drl. "
             f"Erzeugt {datetime.date.today().isoformat()} mit hardware/sensor/gen/gen_dimension_drawing.py "
             f"(KiCad {pcbnew.Version()}). Masse in mm. Nur Ausgabe, Platine unveraendert.", 170), fontsize=5,
             va="top")


def page1(pdf, b, p, segs, dr, sha):
    fig = plt.figure(figsize=(A4[0] * MM, A4[1] * MM))
    title(fig, "Blatt 1/3, Massstab 1:1 bei A4-Druck ohne Skalierung",
          "Ansicht von F (bestueckte Seite). Ursprung (0,0) = Hilfsursprung Mitte Platinenoberkante, X nach rechts, "
          "Y nach unten zur Spitze (= Gerber/Bohrdaten; Kopf: z = 53.5 - Y, PCB_OUTLINE Kap. 1).", sha)
    ax = page_axes(fig, 62, 24, -40, 52, -8, 165, 1.0)
    zone_fill(ax, segs)
    draw_outline(ax, segs, lw=0.6)
    # Elektrodenumriss (User.2)
    for d in b.GetDrawings():
        if d.GetLayerName() == "User.2":
            (x1, y1), (x2, y2) = p(d.GetStart()), p(d.GetEnd())
            ax.plot([x1, x2], [y1, y2], color="tab:green", lw=0.3, ls="--")
    for y, t in LINES:
        xw = 13 if y < 44 else 10
        ax.plot([-xw, xw], [y, y], color="tab:red" if "Steck" in t else "tab:purple", lw=0.35, ls="-.")
        ax.text(xw + 1, y, t, fontsize=4.0, va="center")
    for name, y1, y2, *_ in ZONES:
        ax.plot([-15.5, -13.5], [y1, y1], "k-", lw=0.25)
        ax.text(-16, (y1 + y2) / 2 if y2 - y1 > 4 else y1 + 0.2, f"{name}  Y {y1:g}-{y2:g}", fontsize=3.8,
                ha="right", va="center")
    # Bohrungen
    for kind, pts in dr.items():
        for x, y, d in pts:
            ax.add_patch(plt.Circle((x, y), max(d / 2, 0.15), color="k" if kind == "PTH" else "tab:red", lw=0))
    # Masse
    for y in (0, 42.0, 151.0, 158.5):
        ax.plot([13.5 if y < 44 else 10.5, 49], [y, y], color="0.6", lw=0.2)
    dim_v(ax, 48, 0, 158.5, "158.50 (Gesamtlaenge)")
    dim_v(ax, 43, 0, 42.0, "42.00", side=1)
    dim_v(ax, 43, 151.0, 158.5, "7.50", side=1)
    dim_h(ax, -2.5, -13, 13, "26.00 (Kopf)")
    dim_h(ax, 100, -10, 10, "20.00 (Kragen/Sonde)")
    dim_h(ax, 161.5, -2.5, 2.5, "5.00", above=False)
    ax.text(12.0, 43.6, "Schulter 45 deg, Innenecke R 2.0 (je 2x)", fontsize=4.0, ha="left", va="center")
    ax.text(6.8, 156.0, "45 deg (2x)", fontsize=4.0, ha="left")
    ax.plot([0], [0], "r+", ms=6, mew=0.6)
    ax.text(0.8, -0.8, "(0,0)", fontsize=4.5, color="r")
    # Tabelle links
    pth = dr["PTH"]
    dsz = sorted({d for *_, d in pth})
    via_cnt = sum(1 for f in [b] for _ in b.GetTracks() if _.GetClass() == "PCB_VIA")
    rows = [
        "Kontur: Edge.Cuts, gefraest (JLC Konturtoleranz +-0.2 mm,",
        "  JLCPCB_NOTES Kap. 3)",
        "Dicke 1.6 mm, 4 Lagen (+-10 %: 1.44-1.76 mm, ebd.)",
        "Kopf 26.0 breit (Y 0-42), Schulter 45 deg mit R 2.0,",
        "  Kragen/Sonde 20.0 breit, Spitze 45 deg, Flaeche 5.0",
        "",
        f"Bohrungen PTH: {len(pth)} x Durchm. {', '.join(f'{d:.2f}' for d in dsz)} mm",
        f"  = {via_cnt} Vias + 1 Masse-Via der Antenne (AE1 Pad 2)",
        "  davon 8 Via-in-Pad gefuellt + ueberkupfert (POFV)",
        f"Bohrungen NPTH: {len(dr['NPTH'])} (keine Montageloecher;",
        "  Lage im Gehaeuse ueber Kontur, Kappenanschlag Y 0",
        "  X -8.0...-3.0, Kragen-Distanzlehre, PCB_OUTLINE Kap. 2)",
        "Vias nur Y <= 50 (Band, Fach-VIP, Kragenfeld);",
        "  Y > 50 ohne Vias (DRC Z5A_Z7_SONDE, REQ-MECH-05)",
        "",
        "Gruen gestrichelt: Elektroden S/G (In1/In2, User.2)",
        "Kupfer >= 1.25 zur Kontur ab Y 50 (DRC, REQ-MECH-06)",
        "Farbflaechen = Bauteilhoehen-Zonen (Blatt 2)",
    ]
    fig.text(8 / A4[0], 1 - 40 / A4[1], "\n".join(rows), fontsize=5.2, va="top", family="monospace")
    # Massstabsbalken
    sb = page_axes(fig, 10, 250, 0, 50, -4, 2, 1.0)
    for i in range(5):
        sb.add_patch(Rectangle((i * 10, 0), 10, 1.5, color="k" if i % 2 == 0 else "w", ec="k", lw=0.3))
    sb.text(0, -1.0, "Kontrollmass 50 mm (1:1)", fontsize=5)
    pdf.savefig(fig)
    plt.close(fig)


def courtyard_bbox(fp, p):
    pts = []
    for g in fp.GraphicalItems():
        if g.GetLayerName() in ("F.Courtyard", "B.Courtyard", "F.CrtYd", "B.CrtYd"):
            bb = g.GetBoundingBox()
            pts += [p(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop())), p(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))]
    if not pts:
        bb = fp.GetBoundingBox(False, False)
        pts = [p(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop())), p(pcbnew.VECTOR2I(bb.GetRight(), bb.GetBottom()))]
    xs, ys = zip(*pts)
    return min(xs), min(ys), max(xs), max(ys)


def page2(pdf, b, p, segs, sha):
    fig = plt.figure(figsize=(A4[0] * MM, A4[1] * MM))
    title(fig, "Blatt 2/3, Kopf Y -1...60, Massstab 3:1",
          "Bauteilhoehen-Zonen (max. Hoehe ueber F / B, PCB_OUTLINE Kap. 3/8) und Bauteilumrisse (Courtyard) mit "
          "Hoehe [mm]; * = KiCad-Modell (ANNAHME, PCB_OUTLINE Kap. 8). Testpads B gestrichelt.", sha)
    sc = 3.0
    ax = page_axes(fig, 45, 22, -16, 25, -1.5, 60, sc)
    zone_fill(ax, segs, ymax=60)
    for name, y1, y2, hf, hb in ZONES:
        y2c = min(y2, 60)
        ax.plot([13.2, 24.5], [y1, y1], color="0.5", lw=0.25)
        ax.text(13.6, (y1 + y2c) / 2, f"{name}\nY {y1:g}-{y2:g}\nF max {hf}\nB max {hb}", fontsize=4.2,
                va="center")
    draw_outline(ax, segs, lw=0.7)
    for z in b.Zones():
        if not z.GetIsRuleArea():
            continue
        n = z.GetZoneName()
        if n in ("Z1_ANTENNE", "ANSCHLAG_KAPPE", "Z5B_FELD"):
            bb = z.GetBoundingBox()
            (x1, y1), (x2, y2) = p(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop())), p(pcbnew.VECTOR2I(bb.GetRight(),
                                                                                                bb.GetBottom()))
            x1, x2 = max(x1, -13), min(x2, 13)
            y1 = max(y1, 0)
            ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, ec="tab:red", lw=0.5, ls="--"))
            lab = {"Z1_ANTENNE": "Antennen-Keepout alle Lagen (AN043)", "ANSCHLAG_KAPPE": "Kappenanschlag",
                   "Z5B_FELD": "Kragenfeld U3/C24"}[n]
            ax.text(x1 + 0.2, y2 - 0.25, lab, fontsize=3.6, color="tab:red", va="bottom")
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        x1, y1, x2, y2 = courtyard_bbox(fp, p)
        if y1 > 60:
            continue
        back = fp.IsFlipped()
        ax.add_patch(Rectangle((x1, y1), x2 - x1, y2 - y1, fill=False, ec="tab:blue" if not back else "tab:orange",
                               lw=0.3, ls="--" if back else "-"))
        h = HEIGHTS.get(ref)
        lab = ref + (f"\n{h}" if h else "") + (" (B)" if back else "")
        if ref == "BT1":
            lab = "BT1 Keystone 3034 + CR2032\n(Courtyard inkl. Zelle)\nH 4.1 (Clip)"
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, lab, fontsize=2.6 if not h else 3.0, ha="center", va="center",
                color="k" if not back else "tab:orange", weight="bold" if h else "normal")
    for y, t in LINES[:3]:
        xw = 13 if y < 44 else 10
        ax.plot([-xw, xw], [y, y], color="tab:purple", lw=0.4, ls="-.")
        ax.text(-xw - 0.3, y, t.replace("Vergusskante", "Verguss"), fontsize=3.6, ha="right", va="center",
                color="tab:purple")
    rows = ["Hoehen (PCB_OUTLINE Kap. 8, dort mit Datenblattseite):",
            "SW1 TS-1088 2.0 (bestimmend Z2), BT1 Keystone 3034 4.1,",
            "U1 RGE 1.0 max, L1 1.0, D1 1615 0.6, U3 DRL 0.6 max,",
            "C24 0402 0.55; C1-C4 1206 1.6* (KiCad-Modell, ANNAHME);",
            "uebrige 0402/SC-70/SOT-23/Quarze <= 1.2 (Modelle) < 2.0.",
            "B-Seite unbestueckt: nur Testpads TP4 MEAS_CLK, TP5 PROBE_SENSE",
            "(Pogo-Zugang nur vor dem Einschieben), Silkscreen.",
            "Testpads F: TP1 UART_TX, TP2 UART_RX im Fach (Via-in-Pad).",
            "Kein Bauteil in Z1, Z3, Z5A, Z6, Z7 (DRC-Regelflaechen)."]
    fig.text(10 / A4[0], 1 - 214 / A4[1], "\n".join(rows), fontsize=5.4, va="top", family="monospace")
    sb = page_axes(fig, 10, 268, 0, 10, -1.4, 0.6, sc)
    for i in range(5):
        sb.add_patch(Rectangle((i * 2, 0), 2, 0.5, color="k" if i % 2 == 0 else "w", ec="k", lw=0.3))
    sb.text(0, -0.4, "Kontrollmass 10 mm (3:1 = 30 mm)", fontsize=5)
    pdf.savefig(fig)
    plt.close(fig)


def page3(pdf, b, p, segs, sha):
    fig = plt.figure(figsize=(A4[0] * MM, A4[1] * MM))
    title(fig, "Blatt 3/3, Bestueckungsplan Kopf F (Y -0.5...30), Massstab 5:1",
          "Pads F.Cu (grau), Courtyard (blau), Pad 1 rot gefuellt (Lage/Polaritaet fuer 'Confirm Parts Placement', "
          "ORDER_JLC_REV_C B-3), DNP rot gekreuzt. Testpads B (TP4, TP5) orange gestrichelt, Sicht von F. "
          "Rotationen der CPL: out/fluidi_sensor_cpl_jlc.csv.", sha)
    sc = 5.0
    ax = page_axes(fig, 25, 30, -14, 18, -0.6, 30, sc)
    draw_outline(ax, segs, lw=0.8)
    for fp in b.GetFootprints():
        x1, y1, x2, y2 = courtyard_bbox(fp, p)
        if y1 > 30:
            continue
        back = fp.IsFlipped()
        for pad in fp.Pads():
            bb = pad.GetBoundingBox()
            (px1, py1), (px2, py2) = p(pcbnew.VECTOR2I(bb.GetLeft(), bb.GetTop())), p(pcbnew.VECTOR2I(bb.GetRight(),
                                                                                                    bb.GetBottom()))
            if py1 > 30 and fp.GetReference() == "BT1":
                continue
            one = pad.GetNumber() == "1"
            ax.add_patch(Rectangle((px1, py1), px2 - px1, py2 - py1,
                                   fc=("tab:red" if one else "0.8") if not back else "none",
                                   ec="tab:orange" if back else "0.4", lw=0.2, ls="--" if back else "-"))
        ref = fp.GetReference()
        if ref == "BT1":
            ax.text(3.0, 26.0, "BT1 Keystone 3034 (Clip-Pad VBAT oben,\nMinuspad Mitte Y 34.8 ausserhalb)", fontsize=4,
                    ha="center")
            continue
        ax.add_patch(Rectangle((x1, y1), x2 - x1, min(y2, 30) - y1, fill=False,
                               ec="tab:orange" if back else "tab:blue", lw=0.3, ls="--" if back else "-"))
        if fp.IsDNP():
            ax.plot([x1, x2], [y1, y2], color="tab:red", lw=0.4)
            ax.plot([x1, x2], [y2, y1], color="tab:red", lw=0.4)
        ax.text((x1 + x2) / 2, (y1 + y2) / 2, ref + (" DNP" if fp.IsDNP() else ""), fontsize=4.2 if ref != "AE1" else 5,
                ha="center", va="center", weight="bold", color="tab:orange" if back else "k",
                bbox=dict(fc="white", ec="none", alpha=0.6, pad=0.3))
    rows = ["Bauteile laut CPL (50, alle Top). D1 180 deg gedreht (Kathoden G/B links, LAYOUT Kap. 5),",
            "U1 270 deg (Pin 1 oben zur HF-Kette), U3 im Kragenfeld (Blatt 2). C19/C20 DNM (Pi-Netz Antenne).",
            "Pad-1-Kennzeichnung aus den Footprints; massgebend fuer die Lage sind CPL + Footprint-Datenblatt."]
    fig.text(10 / A4[0], 1 - 192 / A4[1], "\n".join(rows), fontsize=6, va="top")
    sb = page_axes(fig, 10, 268, 0, 10, -1.4, 0.6, sc)
    for i in range(5):
        sb.add_patch(Rectangle((i * 2, 0), 2, 0.5, color="k" if i % 2 == 0 else "w", ec="k", lw=0.3))
    sb.text(0, -0.4, "Kontrollmass 10 mm (5:1 = 50 mm)", fontsize=5)
    pdf.savefig(fig)
    plt.close(fig)


def main():
    sha = hashlib.sha256(open(PCB, "rb").read()).hexdigest()
    b, p = board()
    segs = outline(b, p)
    dr = drills()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with PdfPages(OUT, metadata={"Title": "fluidi Sensor Rev C Masszeichnung", "Creator": "gen_dimension_drawing.py",
                                 "CreationDate": None, "ModDate": None}) as pdf:
        page1(pdf, b, p, segs, dr, sha)
        page2(pdf, b, p, segs, sha)
        page3(pdf, b, p, segs, sha)
    after = hashlib.sha256(open(PCB, "rb").read()).hexdigest()
    assert after == sha, "Platine veraendert!"
    xs = [x for s in segs for x in ([s[1][0], s[2][0]] if s[0] == "line" else [s[2][0], s[3][0]])]
    ys = [y for s in segs for y in ([s[1][1], s[2][1]] if s[0] == "line" else [s[2][1], s[3][1]])]
    print(f"Kontur {len(segs)} Elemente, X {min(xs):.3f}...{max(xs):.3f}, Y {min(ys):.3f}...{max(ys):.3f}; "
          f"PTH {len(dr['PTH'])}, NPTH {len(dr['NPTH'])}; Platine sha256 unveraendert {sha[:16]}")
    print(f"geschrieben: {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
