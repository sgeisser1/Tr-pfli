#!/usr/bin/env python3
"""fluidi Sensor - Flaechenbilanz Elektronikband und Platzierungsoptionen (Vorschlag PCB_OUTLINE Rev B).

Aufruf (Repo-Wurzel):  .venv/bin/python hardware/sensor/gen/floorplan_options.py
Ausgabe: hardware/sensor/out/floorplan_options.png (massstaeblich) + Tabellen auf stdout
         (Flaechen, Bandhoehen, Kosten) fuer hardware/sensor/out/FLOORPLAN_OPTIONS.md

Quellen:
- Courtyards aus den KiCad-10-Footprints (/usr/share/kicad/footprints) bzw. hardware/sensor/lib/fluidi.pretty,
  per pcbnew gelesen (Courtyard-Huelle = Bauteil + Pads + IPC-Rand, i. d. R. 0.25 mm).
- Zonen Rev A: mechanical/interfaces/pcb_outline.json (Generator mechanical/gen/fluidi_params.py).
- Bauteilliste: hardware/sensor/gen/parts.py (Schaltplan Rev A), D-013 (Prototyp 4 x 100 uF).
- Kosten: scripts/cost_model.py (compute), Preise hardware/sensor/gen/jlc_check.json (JLC-API 2026-11-07),
  Staffeln docs/concepts/bom/bom_A32.csv, neue Kandidaten per JLC-API 2026-11-07 (siehe INDEX.csv).
ANNAHMEN sind im Code markiert.
"""
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "hardware", "sensor", "out")
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, HERE)

import cost_model as cm  # noqa: E402

SYSLIB = "/usr/share/kicad/footprints"
LOCLIB = os.path.join(ROOT, "hardware", "sensor", "lib", "fluidi.pretty")

# ------------------------------------------------------------------ 1 Courtyards aus KiCad
FOOTPRINTS = {
    "QFN24": "Package_DFN_QFN:VQFN-24-1EP_4x4mm_P0.5mm_EP2.45x2.45mm",
    "XT3225": "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm",
    "XT3215": "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm",
    "C1206": "Capacitor_SMD:C_1206_3216Metric",
    "C0402": "Capacitor_SMD:C_0402_1005Metric",
    "C0201": "Capacitor_SMD:C_0201_0603Metric",
    "R0402": "Resistor_SMD:R_0402_1005Metric",
    "L0402": "Inductor_SMD:L_0402_1005Metric",
    "SOT23": "Package_TO_SOT_SMD:SOT-23",
    "SC70_5": "Package_TO_SOT_SMD:SOT-353_SC-70-5",
    "VSSOP8": "Package_SO:VSSOP-8_3x3mm_P0.65mm",
    "SOT563": "Package_TO_SOT_SMD:SOT-563",
    "TS1187": "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A",
    "TS1088": "Button_Switch_SMD:SW_SPST_TS-1088-xR020",
    "LED1615": "fluidi:LED_RGB_TUOZHAN_1615",
    "L2016": "fluidi:L_Sunlord_WPN201610H",
    "TP10": "TestPoint:TestPoint_Pad_D1.0mm",
    "ANT": "RF_Antenna:Texas_SWRA117D_2.4GHz_Left",
}


def courtyards():
    import pcbnew
    res = {}
    for key, fp in FOOTPRINTS.items():
        lib, name = fp.split(":")
        path = LOCLIB if lib == "fluidi" else os.path.join(SYSLIB, lib + ".pretty")
        m = pcbnew.FootprintLoad(path, name)
        xs, ys = [], []
        for g in m.GraphicalItems():
            if g.GetLayer() == pcbnew.F_CrtYd:
                bb = g.GetBoundingBox()
                xs += [bb.GetLeft(), bb.GetRight()]
                ys += [bb.GetTop(), bb.GetBottom()]
        if not xs:
            bb = m.GetCourtyard(pcbnew.F_CrtYd).BBox()
            xs, ys = [bb.GetLeft(), bb.GetRight()], [bb.GetTop(), bb.GetBottom()]
        res[key] = (round(pcbnew.ToMM(max(xs) - min(xs)), 2), round(pcbnew.ToMM(max(ys) - min(ys)), 2))
    return res


CY = courtyards()


def area(key):
    w, h = CY[key]
    return w * h


# ------------------------------------------------------------------ 2 Bauteile im Elektronikband (Rev A)
# (Ref-Gruppe, Footprint-Schluessel, Anzahl). Zelle/Clip, TP1-TP3 (Fachstreifen) und Antenne nicht im Band.
REV_A = [
    ("U1 CC2340", "QFN24", 1), ("Y1 48 MHz", "XT3225", 1), ("Y2 32 kHz", "XT3215", 1),
    ("C1-C4 100uF (D-013 Prototyp 4)", "C1206", 4), ("L1 10uH", "L2016", 1),
    ("Q1 Verpolschutz", "SOT23", 1), ("U2 LVC1G14", "SC70_5", 1), ("U3 TMP1075DGK", "VSSOP8", 1),
    ("SW1 TS-1187A", "TS1187", 1), ("D1 RGB", "LED1615", 1), ("TP4 OSZ_OUT", "TP10", 1),
    ("C 0402 (C5-C24 inkl. DNP C19/C20)", "C0402", 20), ("R 0402 (R1-R12)", "R0402", 12), ("L2 0402", "L0402", 1),
]
# Option (c): gleiche Funktionen, kleinere Gehaeuse, Basic/Extended-Bilanz unveraendert
REV_C = [
    ("U1 CC2340", "QFN24", 1), ("Y1 48 MHz", "XT3225", 1), ("Y2 32 kHz", "XT3215", 1),
    ("C1-C4 100uF (D-013 Prototyp 4)", "C1206", 4), ("L1 10uH", "L2016", 1),
    ("Q1 Verpolschutz", "SOT23", 1), ("U2 LVC1G14", "SC70_5", 1), ("U3 TMP1075NDRL", "SOT563", 1),
    ("SW1 TS-1088-AR02016", "TS1088", 1), ("D1 RGB", "LED1615", 1),
    ("C 0402 (C24 entfaellt, C21 versorgt U2+U3)", "C0402", 19), ("R 0402 (R1-R12)", "R0402", 12),
    ("L2 0402", "L0402", 1),
]                                                    # TP4 -> B-Seite (nur Pad, keine Bestueckung)


def bom_area(lst):
    return sum(area(k) * n for _, k, n in lst)


# ------------------------------------------------------------------ 3 Platzierung (Kopfkoordinaten x, z)
Z_BAND0 = 32.7            # Oberkante Schottzone Rev A
X_MIN, X_MAX = -9.7, 9.7  # ANNAHME 0.3 mm Courtyard-Rand zur gefraesten Kante (JLC Kupfer-Kontur >= 0.2 mm)
ANT_H = 5.7               # AN043 15.2 x 5.7 (S.1, S.4 Abb. 3/Tab. 1)
REV_A_TOP = 44.0          # Platinenoberkante Rev A


def cy(key, rot=False):
    w, h = CY[key]
    return (h, w) if rot else (w, h)


def blk(name, x0, z0, w, h, parts, color, side="F"):
    return dict(name=name, x0=x0, z0=z0, w=w, h=h, parts=parts, color=color, side=side)


def part(name, key, cx=None, cz=None, x0=None, z0=None, rot=False, color="#9ecae1", side="F"):
    w, h = cy(key, rot)
    if cx is not None:
        x0, z0 = cx - w / 2, cz - h / 2
    return blk(name, x0, z0, w, h, [(key, 1)], color, side)


C_PWR, C_SOC, C_RF, C_MEAS, C_UI, C_UART = "#fdae6b", "#9ecae1", "#fb6a4a", "#a1d99b", "#dadaeb", "#fdd0a2"


def plan_recommended():
    """Option (c)+(d): einseitig F, Economic. Bloecke = Cluster mit Flaeche >= 1.1 x Courtyard-Summe (ANNAHME
    packbar). SW1/D1 bleiben auf den Rev-A-Koordinaten (Fuge/Fenster/Zunge unveraendert)."""
    b = []
    b.append(part("SW1 TS-1088", "TS1088", cx=-6.0, cz=35.6, color=C_UI))
    b.append(part("D1", "LED1615", cx=0.0, cz=37.4, color=C_UI))
    w, h = cy("C1206")
    b.append(blk("C1", -2.75, Z_BAND0, w, h, [("C1206", 1)], C_PWR))
    b.append(blk("C2", 2.04, Z_BAND0, w, h, [("C1206", 1)], C_PWR))
    b.append(blk("C3", X_MAX - h, Z_BAND0, h, w, [("C1206", 1)], C_PWR))
    b.append(blk("C4", 2.50, 35.19, w, h, [("C1206", 1)], C_PWR))
    b.append(blk("R6-R8 LED", X_MIN, Z_BAND0 + 0.02, 6.7, 1.03, [("R0402", 3)], C_UI))
    b.append(part("Q1", "SOT23", x0=X_MIN, z0=37.6, color=C_PWR))
    b.append(blk("U2 Messkette\nR3 C21 C22 C23", X_MIN, 41.2, 5.0, 4.4, [("SC70_5", 1), ("R0402", 1), ("C0402", 3)], C_MEAS))
    b.append(blk("U3 TMP\nR4 R5", X_MIN, 45.7, 3.6, 3.0, [("SOT563", 1), ("R0402", 2)], C_MEAS))
    b.append(blk("U1 + C5-C13\nR1 L1", -4.4, 38.85, 8.6, 7.6, [("QFN24", 1), ("C0402", 9), ("R0402", 1), ("L2016", 1)], C_SOC))
    b.append(blk("Y1 Y2\nC14 C15", 5.1, 37.7, 4.6, 7.2, [("XT3225", 1), ("XT3215", 1), ("C0402", 2)], C_SOC))
    b.append(blk("RF C16 L2 C17\nC18 C19 R2 C20", -4.4, 46.6, 8.0, 2.2, [("C0402", 5), ("L0402", 1), ("R0402", 1)], C_RF))
    b.append(blk("R9-R12 UART\n(R2-A3)", 5.1, 45.1, 4.6, 2.2, [("R0402", 4)], C_UART))
    return b


# Kragen (fluidi_params Rev A): Verguss z 2.0 ... 7.3, Mutter M2 x 0, z 2.3 ... 3.9 (Eckmass 4.6),
# Schraubenspitze bis z 4.3. Vorschlag (f): Dichtstreifen z 2.0 ... 4.2 ohne Kupfer/Vias (M-03, 2 mm),
# Bauteile nur z 4.4 ... 6.8 (>= 0.5 mm Epoxid ueber Oberkante), |x| >= 2.6 (Mutter/Schraube), Tasche 1.2 mm tief.
KRAGEN_COMP = (4.4, 6.8)
KRAGEN_SEAL = (2.0, 4.2)


def plan_f():
    """Option (f) = (c)+(d), U3 TMP1075NDRL + eigener Abblock-C (C24) im Kragen; R4/R5 bleiben im Band."""
    b = [x for x in plan_recommended() if not x["name"].startswith("U3 TMP")]
    b.append(blk("R4 R5", X_MIN, 45.7, 2.3, 2.2, [("R0402", 2)], C_MEAS))
    return b


def plan_kragen():
    return [blk("U3 TMP1075N\n+ C24", -9.2, 4.6, 4.4, 2.0, [("SOT563", 1), ("C0402", 1)], C_MEAS)]


def check_kragen(bl):
    e = []
    for b in bl:
        if b["z0"] < KRAGEN_COMP[0] or b["z0"] + b["h"] > KRAGEN_COMP[1] or b["x0"] < X_MIN or b["x0"] + b["w"] > X_MAX:
            e.append("ausserhalb Kragen-Bauteilzone: " + b["name"])
        if b["x0"] < 2.6 and b["x0"] + b["w"] > -2.6:
            e.append("Mutter/Schraube: " + b["name"])
        need = sum(area(k) * n for k, n in b["parts"])
        if b["w"] * b["h"] < 1.1 * need:
            e.append("Block zu klein: " + b["name"])
    return e


def plan_double():
    """Option (b)+(c)+(d): F grosse Teile, B nur 0402 (<= 0.6 mm), Standard-PCBA beidseitig."""
    b = []
    b.append(part("SW1 TS-1088", "TS1088", cx=-6.0, cz=35.6, color=C_UI))
    b.append(part("D1", "LED1615", cx=0.0, cz=37.4, color=C_UI))
    w, h = cy("C1206")
    b.append(blk("C1", -2.75, Z_BAND0, w, h, [("C1206", 1)], C_PWR))
    b.append(blk("C2", 2.04, Z_BAND0, w, h, [("C1206", 1)], C_PWR))
    b.append(blk("C3", X_MAX - h, Z_BAND0, h, w, [("C1206", 1)], C_PWR))
    b.append(blk("C4", 2.50, 35.19, w, h, [("C1206", 1)], C_PWR))
    b.append(part("Q1", "SOT23", x0=X_MIN, z0=37.6, color=C_PWR))
    b.append(part("U2", "SC70_5", x0=X_MIN, z0=41.2, color=C_MEAS))
    b.append(part("U3", "SOT563", x0=X_MIN, z0=43.9, color=C_MEAS))
    b.append(blk("U1 QFN24\n+ Fanout", -3.3, 38.85, 6.4, 6.4, [("QFN24", 1)], C_SOC))
    b.append(part("L1", "L2016", x0=-5.6, z0=41.0, rot=True, color=C_SOC))
    b.append(part("Y1", "XT3225", x0=X_MAX - CY["XT3225"][0], z0=37.7, color=C_SOC))
    b.append(part("Y2", "XT3215", x0=X_MAX - CY["XT3215"][0], z0=41.4, color=C_SOC))
    # B-Seite: 32 x 0402 als Bloecke (Spiegelung beim Zeichnen nicht noetig, Ansicht von vorne durchsichtig)
    b.append(blk("B: C5-C13 R1\nunter U1", -3.3, 38.85, 6.4, 6.4, [("C0402", 9), ("R0402", 1)], C_SOC, "B"))
    b.append(blk("B: RF 7x0402", -9.7, 38.0, 6.0, 3.0, [("C0402", 5), ("L0402", 1), ("R0402", 1)], C_RF, "B"))
    b.append(blk("B: Mess/TMP/LED\n11x0402", 3.4, 33.0, 6.3, 5.4, [("C0402", 5), ("R0402", 6)], C_MEAS, "B"))
    b.append(blk("B: UART R9-R12", -9.7, 33.0, 4.6, 2.2, [("R0402", 4)], C_UART, "B"))
    return b


def check(blocks, z_top_band):
    """Ueberlappung (gleiche Seite) und Lage im Band pruefen; Rueckgabe Liste der Fehler."""
    err = []
    for i, a in enumerate(blocks):
        if a["x0"] < X_MIN - 1e-6 or a["x0"] + a["w"] > X_MAX + 1e-6 or a["z0"] < Z_BAND0 - 1e-6 \
                or a["z0"] + a["h"] > z_top_band + 1e-6:
            err.append("ausserhalb Band: " + a["name"])
        need = sum(area(k) * n for k, n in a["parts"])
        if a["w"] * a["h"] < need * (1.1 if len(a["parts"]) > 1 or a["parts"][0][1] > 1 else 1.0) - 1e-6:
            err.append("Block zu klein: %s (%.1f < 1.1 x %.1f)" % (a["name"].replace("\n", " "), a["w"] * a["h"], need))
        for b2 in blocks[i + 1:]:
            if a["side"] != b2["side"]:
                continue
            if a["x0"] < b2["x0"] + b2["w"] - 1e-6 and b2["x0"] < a["x0"] + a["w"] - 1e-6 and \
                    a["z0"] < b2["z0"] + b2["h"] - 1e-6 and b2["z0"] < a["z0"] + a["h"] - 1e-6:
                err.append("Ueberlappung: %s / %s" % (a["name"].replace("\n", " "), b2["name"].replace("\n", " ")))
    return err


def band_top(blocks, margin=0.3):
    """Bandoberkante = hoechster Block + 0.3 mm (Massekante/Abstand zur AN043-Massegrenze, ANNAHME)."""
    return max(b["z0"] + b["h"] for b in blocks) + margin


# ------------------------------------------------------------------ 4 Kosten (scripts/cost_model.py)
JLC = json.load(open(os.path.join(HERE, "jlc_check.json")))


def tiers_from_a32():
    import csv
    t = {}
    with open(os.path.join(ROOT, "docs", "concepts", "bom", "bom_A32.csv")) as fh:
        for r in csv.DictReader(fh, delimiter=";"):
            for tok in r["part"].split():
                if tok.startswith("C") and tok[1:].isdigit():
                    t[tok] = (r["tiers"], int(r["moq"]), int(r["attrition"]))
    return t


A32T = tiers_from_a32()


def line(desc, lcsc, qty, cat, joints, leadless=False, price=None, tiers=None, moq=5, attr=4):
    if lcsc in A32T and tiers is None:
        ts, moq, attr = A32T[lcsc]
        tiers = tuple((int(a), float(b)) for a, b in (x.split(":") for x in ts.split("|")))
    if price is None:
        price = JLC[lcsc]["price1"][0][1] if lcsc in JLC else tiers[0][1]
    return cm.BomLine(desc + " " + lcsc, qty, price, 0.0, cat, True, joints, moq, attr, "JLC",
                      tiers or (), leadless)


LOKAL = [cm.BomLine("Zelle Panasonic CR2032", 1, 0, 1.38, "none", False, 0, 1, 0, "LOKAL"),
         cm.BomLine("Gehaeuse ASA (ANNAHME)", 1, 0, 0.525, "none", False, 0, 1, 0, "LOKAL"),
         cm.BomLine("Dichtungen (ANNAHME)", 1, 0, 0.3, "none", False, 0, 1, 0, "LOKAL"),
         cm.BomLine("Versiegelung Sonde (ANNAHME)", 1, 0, 0.4, "none", False, 0, 1, 0, "LOKAL"),
         cm.BomLine("Schraube/Mutter (ANNAHME)", 1, 0, 0.2, "none", False, 0, 1, 0, "LOKAL")]


def bom(variant, n100u):
    """variant: 'A' (Rev A), 'C' (kleinere Gehaeuse); Suffix 'h' = Halter lokal beschafft, handgeloetet (Option a)."""
    L = [line("SoC", "C20416850", 1, "extended", 25, leadless=True),
         line("Quarz 48M", "C2925606", 1, "extended", 4), line("Quarz 32k", "C99010", 1, "extended", 2),
         line("L 10u", "C89132", 1, "extended", 2), line("L 2n7", "C27123", 1, "extended", 2),
         line("C 1p5", "C1552", 2, "preferred", 2), line("C 10u", "C15525", 2, "basic", 2),
         line("C 100n", "C1525", 8 if (variant.startswith("A") or variant.endswith("f")) else 7, "basic", 2), line("C 1u", "C52923", 1, "basic", 2),
         line("C 15p", "C1548", 3, "basic", 2), line("C 22p", "C1555", 1, "basic", 2),
         line("C 100p", "C1546", 1, "basic", 2), line("R 0", "C17168", 1, "basic", 2),
         line("R 100", "C25076", 1, "basic", 2, moq=20, attr=10), line("R 200", "C25087", 1, "basic", 2, moq=20, attr=10),
         line("R 470", "C25117", 1, "basic", 2), line("R 4k7", "C25900", 3, "basic", 2),
         line("R 100k", "C25741", 5, "basic", 2), line("LVC1G14", "C35740", 1, "extended", 5),
         line("AO3401A", "C15127", 1, "basic", 3), line("C 100u", "C15008", n100u, "basic", 2),
         line("LED RGB", "C7496855", 1, "extended", 4, moq=5, attr=4)]
    if variant.startswith("A"):
        L += [line("TMP1075DGK", "C2864807", 1, "extended", 8), line("TS-1187A", "C318884", 1, "basic", 4)]
    else:   # JLC-API 2026-11-07
        L += [line("TMP1075NDRL", "C3663690", 1, "extended", 6, tiers=((1, 0.5414), (10, 0.4563)), moq=5, attr=0),
              line("TS-1088-AR02016", "C720477", 1, "basic", 2, tiers=((1, 0.0527), (100, 0.0427)), moq=5, attr=8)]
    if variant.endswith("h"):
        # Halter separat (LCSC 0.39 USD + Versandanteil) -> ANNAHME 0.45 CHF, Handloetung durch Auftraggeber
        L += [cm.BomLine("Halter Keystone 3034 lokal (ANNAHME 0.45 CHF inkl. Versandanteil)", 1, 0, 0.45, "none",
                         False, 0, 1, 0, "LOKAL")]
    else:
        L += [line("Keystone 3034", "C5213768", 1, "extended", 3, moq=2, attr=0)]
    return L + copy.deepcopy(LOKAL)


def run_cost(variant, n100u, pcb_qty, pcba_qty, sensors, mode="economic", double=False, dlen=0.0, asa_g=0.0):
    std_bak, var_bak = dict(cm.STD), dict(cm.PCB_VAR_USD)
    try:
        if double:
            cm.STD["setup"], cm.STD["stencil"] = 51.12, 16.42      # [JLC] beidseitig (JLCPCB_NOTES.md Kap. 1)
        cm.PCB_VAR_USD[(4, 1.6)] = var_bak[(4, 1.6)] * (149.0 + dlen) / 150.0   # ANNAHME Grenzkosten ~ Laenge
        b = bom(variant, n100u)
        if asa_g:
            b.append(cm.BomLine("ASA Mehrmenge %.1f g (ANNAHME 0.035 CHF/g)" % asa_g, 1, 0, 0.035 * asa_g, "none",
                                False, 0, 1, 0, "LOKAL"))
        r = cm.compute(b, 4, 1.6, pcb_qty, pcba_qty, ship="GSDL", pcba=mode, sensors=sensors)
    finally:
        cm.STD.clear(); cm.STD.update(std_bak)
        cm.PCB_VAR_USD.clear(); cm.PCB_VAR_USD.update(var_bak)
    return r


# ------------------------------------------------------------------ 5 Zeichnung
def draw(path, rec, rec_top, dbl, dbl_top, kr=()):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle

    zmin, zmax = 0.0, max(rec_top + ANT_H, 44.0) + 1.0
    fig, axs = plt.subplots(1, 5, figsize=(22, 13.5), sharey=True)

    def frame(ax, title, top, ant=True):
        ax.add_patch(Rectangle((-10, zmin), 20, top - zmin, fill=False, lw=1.5, ec="k"))
        if ant:
            ax.add_patch(Rectangle((-10, top - ANT_H), 20, ANT_H, fc="#c6dbef", ec="#2171b5", hatch="//", lw=0.8))
            ax.text(0, top - ANT_H / 2, "Z1 Antenne AN043\n15.2 x 5.7 + Keepout", ha="center", va="center", fontsize=7)
        ax.add_patch(Rectangle((-10, 30.3), 20, 2.4, fc="#bdbdbd", ec="k", lw=0.5, hatch="xx"))
        ax.text(0, 31.5, "Z3 Schott (Verguss)", ha="center", va="center", fontsize=7)
        ax.add_patch(Rectangle((-10, 1.5), 20, 6.0, fc="#d9d9d9", ec="k", lw=0.5, hatch=".."));
        ax.text(0, 4.5, "Z5 Kragen-Verguss", ha="center", va="center", fontsize=7)
        ax.set_title(title, fontsize=9)
        ax.set_xlim(-11, 11); ax.set_ylim(zmin, zmax); ax.set_aspect("equal")
        ax.set_xlabel("x [mm] (Ansicht von vorne)")
        ax.grid(True, lw=0.3, alpha=0.5)

    def cell(ax, side_note):
        ax.add_patch(Rectangle((-10, 7.5), 16.1, 23.1, fc="#f0f0f0", ec="#636363", lw=0.8))
        ax.add_patch(Circle((0, 19.05), 10, fill=False, ec="#636363", lw=1, ls="--"))
        ax.text(-2, 19, "Z4 Zellfach\n3034 + CR2032\n" + side_note, ha="center", va="center", fontsize=7)
        ax.add_patch(Rectangle((6.6, 7.5), 2.9, 22.8, fc="#ffffcc", ec="#999", lw=0.5))
        ax.text(8.05, 12, "TP1-3", rotation=90, ha="center", va="center", fontsize=6)

    def blocks(ax, bl, side="F", alpha=1.0):
        for b in bl:
            if b["side"] != side:
                continue
            ax.add_patch(Rectangle((b["x0"], b["z0"]), b["w"], b["h"], fc=b["color"], ec="k", lw=0.5, alpha=alpha))
            fs = 5.5 if b["w"] * b["h"] > 12 else 4.5
            ax.text(b["x0"] + b["w"] / 2, b["z0"] + b["h"] / 2, b["name"], ha="center", va="center", fontsize=fs)

    # 1 Rev A
    ax = axs[0]
    frame(ax, "Rev A (Ist): Band F 20 x 5.6 = 112 mm2\nBedarf %.0f mm2 Courtyard -> passt nicht" % bom_area(REV_A), REV_A_TOP)
    cell(ax, "(F, Clip 4.1 mm)")
    ax.add_patch(Rectangle((-10, 32.7), 20, 5.6, fc="#fee0d2", ec="r", lw=1.2))
    ax.text(0, 35.5, "Z2 Band F 112 mm2\n(SW1 allein 43 mm2)", ha="center", va="center", fontsize=7, color="r")

    # 2 Option (a)
    ax = axs[1]
    frame(ax, "(a) Halter auf B (handgeloetet)\nF unter der Zelle = Zellfach -> S3-K1 verletzt", REV_A_TOP)
    ax.add_patch(Rectangle((-10, 7.5), 20, 22.8, fc="none", ec="r", hatch="\\\\", lw=1.0))
    ax.text(0, 19, "F frei, aber im Zellfach\n(nass bei Leck/Flutung,\noffen beim Zellwechsel)\n-> keine Elektronik\nohne Laengsschott\n+ PCB 2 mm nach vorne", ha="center",
            va="center", fontsize=7, color="r", bbox=dict(fc="w", ec="r"))
    ax.add_patch(Rectangle((-10, 32.7), 20, 5.6, fc="#fee0d2", ec="r", lw=1.2))
    ax.text(0, 35.5, "Band F unveraendert 112 mm2", ha="center", va="center", fontsize=7)

    # 3 Option (b)+(c)+(d) F
    ax = axs[2]
    frame(ax, "(b)+(c)+(d) beidseitig, Standard-PCBA\nF-Seite: Band %.1f mm (+%.1f)" % (dbl_top - Z_BAND0, dbl_top - 38.3),
          dbl_top + ANT_H)
    cell(ax, "")
    ax.add_patch(Rectangle((-10, Z_BAND0), 20, dbl_top - Z_BAND0, fc="#f7fcf5", ec="g", lw=1.2))
    blocks(ax, dbl, "F")
    # 4 (b) B-Seite
    ax = axs[3]
    frame(ax, "(b)+(c)+(d) B-Seite (durchsichtig von vorne)\nnur <= 0.6 mm, PCB 0.8 mm nach vorne", dbl_top + ANT_H)
    ax.add_patch(Rectangle((-10, Z_BAND0), 20, dbl_top - Z_BAND0, fc="#f7fcf5", ec="g", lw=1.2))
    blocks(ax, dbl, "B")
    ax.text(0, 19, "Z4 Fach B: Warnsymbol\n(Silk)", ha="center", va="center", fontsize=7)

    # 5 Empfehlung
    ax = axs[4]
    frame(ax, "EMPFEHLUNG (f) = (c)+(d) + U3 im Kragen\nEconomic, Band %.1f mm (+%.1f), Kopf %.1f mm" % (
        rec_top - Z_BAND0, rec_top - 38.3, 48.0 + rec_top - 38.3), rec_top + ANT_H)
    cell(ax, "(unveraendert)")
    ax.add_patch(Rectangle((-10, Z_BAND0), 20, rec_top - Z_BAND0, fc="#f7fcf5", ec="g", lw=1.2))
    blocks(ax, rec, "F")
    ax.add_patch(Rectangle((-10, KRAGEN_SEAL[0]), 20, KRAGEN_SEAL[1] - KRAGEN_SEAL[0], fc="#fff5eb", ec="#d94801",
                           hatch="xx", lw=0.8))
    ax.text(4.5, 3.1, "Dichtstreifen\nkein Cu/Via", ha="center", va="center", fontsize=6, color="#d94801")
    ax.add_patch(Rectangle((-2.3, 2.3), 4.6, 1.6, fc="#969696", ec="k", lw=0.5)); ax.text(0, 3.1, "M2", fontsize=6, ha="center", va="center")
    blocks(ax, list(kr), "F")
    ax.plot([-8.2, -8.2], [6.6, 32.7], color="#31a354", lw=1.2, ls="--")
    ax.text(-8.0, 12, "SENS_PWR SDA SCL GND\nInnenlage, keine Vias im Fach", rotation=90, fontsize=6, color="#31a354", va="bottom")
    ax.axhline(37.0, color="#6baed6", lw=1, ls=":")
    ax.text(10.3, 37.0, "Fuge z 37", fontsize=6, va="center")
    for a in axs:
        a.axhline(38.3, color="r", lw=0.6, ls="--")
    axs[0].set_ylabel("z [mm] ab Kopfunterkante (Rev A); rote Linie = Bandende Rev A (z 38.3)")
    fig.suptitle("fluidi Sensor - Elektronikband: Optionen (massstaeblich, Courtyards KiCad 10, Bloecke >= 1.1 x Courtyard-Summe)",
                 fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=110)


def main():
    print("Courtyards (mm):")
    for k, (w, h) in CY.items():
        print("  %-8s %5.2f x %5.2f = %6.2f mm2" % (k, w, h, w * h))
    for name, lst in (("Rev A", REV_A), ("Option (c)", REV_C)):
        print("\n%s - Courtyard-Summe im Band:" % name)
        for d, k, n in lst:
            print("  %-42s %2d x %-7s %6.1f mm2" % (d, n, k, area(k) * n))
        print("  SUMME %.1f mm2" % bom_area(lst))

    rec = plan_recommended()
    rec_top = band_top(rec)
    pf, kr = plan_f(), plan_kragen()
    f_top = band_top(pf)
    d_f = f_top - 38.3
    print("\n(f) Band ohne U3: z %.1f ... %.1f = %.1f mm (+%.1f); Pruefung Band: %s; Kragen: %s; frei im Band: %.1f mm2 "
          "Courtyard (U3 + R4/R5-Block verkleinert)" % (Z_BAND0, f_top, f_top - Z_BAND0, d_f, check(pf, f_top) or "OK",
                                       check_kragen(kr) or "OK", area("SOT563")))
    dbl = plan_double()
    dbl_top = band_top(dbl)
    for nm, bl, top in (("Empfehlung (c)+(d)", rec, rec_top), ("(b)+(c)+(d)", dbl, dbl_top)):
        e = check(bl, top)
        used = sum(b["w"] * b["h"] for b in bl if b["side"] == "F")
        cyF = sum(area(k) * n for b in bl if b["side"] == "F" for k, n in b["parts"])
        print("\n%s: Band z %.1f ... %.1f = %.1f mm (+%.1f mm gegenueber Rev A 5.6 mm); F-Courtyard %.0f mm2, "
              "Bandflaeche %.0f mm2 -> Faktor %.2f; Pruefung: %s" % (
                  nm, Z_BAND0, top, top - Z_BAND0, top - 38.3, cyF, (top - Z_BAND0) * 20, (top - Z_BAND0) * 20 / cyF,
                  "OK" if not e else e))
    # Faustformel
    for f in (1.3, 1.4, 1.5):
        print("Faktor %.1f: Rev A %.1f mm Band, (c) %.1f mm Band" % (f, bom_area(REV_A) * f / 20, bom_area(REV_C) * f / 20))

    # Kosten
    d_rec = rec_top - 38.3
    d_dbl = dbl_top - 38.3
    asa = lambda d: 1.07 * (28 * 13 - 24.8 * 9.8) * d / 1000.0   # ANNAHME Dichte ASA 1.07 g/cm3, Wand 1.6 mm
    cases = [
        ("Rev A (passt nicht, Referenz)", dict(variant="A")),
        ("(a) Halter lokal/handgeloetet, sonst Rev A", dict(variant="Ah")),
        ("(b)+(c)+(d) beidseitig Standard", dict(variant="C", mode="standard", double=True, dlen=d_dbl, asa_g=asa(d_dbl))),
        ("(c)+(d)", dict(variant="C", dlen=d_rec, asa_g=asa(d_rec))),
        ("(f) = (c)+(d) + TMP im Kragen EMPFEHLUNG", dict(variant="Cf", dlen=d_f, asa_g=asa(d_f))),
    ]
    print("\nKosten CHF (D-005)            | Proto 5/5, 4x100uF: Stueck  Einmal  Voll | Serie 20/16/15, 2x100uF: Stueck  Einmal  Voll")
    for nm, kw in cases:
        p = run_cost(n100u=4, pcb_qty=5, pcba_qty=5, sensors=5, **kw)
        s = run_cost(n100u=2, pcb_qty=20, pcba_qty=16, sensors=15, **kw)
        print("  %-44s %6.2f %7.2f %6.2f | %6.2f %7.2f %6.2f   (%s)" % (
            nm, p["unit_chf"], p["once_chf"], p["full_chf"], s["unit_chf"], s["once_chf"], s["full_chf"], s["mode"]))
    print("  Hinweis Standard-PCBA: Panel >= 70 x 70 mm (3-fach + Raender) nicht modelliert -> Einmalkosten eher hoeher.")
    print("  ASA-Mehrmenge (c)+(d): %.1f g, (b)+(c)+(d): %.1f g" % (asa(d_rec), asa(d_dbl)))

    png = os.path.join(OUT, "floorplan_options.png")
    draw(png, pf, f_top, dbl, dbl_top, kr)
    print("\ngeschrieben:", png)


if __name__ == "__main__":
    main()
