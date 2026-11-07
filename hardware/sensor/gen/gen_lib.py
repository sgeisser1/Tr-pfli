#!/usr/bin/env python3
"""fluidi Sensor Rev B - projektspezifische KiCad-Bibliothek erzeugen.

Erzeugt:
  hardware/sensor/lib/fluidi.kicad_sym   (Symbole CC2340R52E0RGER, AO3401A, TMP1075NDRL, ANT_IFA_AN043,
                                          SONDE_ELEKTRODEN)
  hardware/sensor/lib/fluidi.pretty/*.kicad_mod (Footprints LED 1615, Spule WPN201610H, Halter 3034 mit
                                                 kleinem Minuspad, Platzhalter Sonde)

Quellen (lokal, jeweils geprueft):
  CC2340R52 RGE-Pinbelegung   docs/datasheets/TI_CC2340R5_Datasheet_SWRS272F.pdf S.7 Abb. 6-2, S.9-16 Tab. 6-1..6-13,
                              Gehaeuse RGE0024B S.77-78 (Exposed Pad = Pin 25, 2.45 x 2.45 mm)
  AO3401A SOT-23 (1 G, 2 S, 3 D)  docs/datasheets/AOS_AO3401A_Datasheet_Rev3.1.pdf S.1 (SOT23 Top View)
  TMP1075NDRL SOT-563 (1 SCL, 2 GND, 3 ALERT, 4 A0, 5 V+, 6 SDA)
                              docs/datasheets/TI_TMP1075_Datasheet_SBOS854F.pdf S.4 Abb. 5-4 / Tab. 5-1;
                              Land Pattern DRL0006A S.37 (6 x 0.67 x 0.3, Raster 0.5, Reihen 1.48) ~ KiCad SOT-563
                              (0.675 x 0.35, Reihen 1.425)
  LED TUOZHAN 1615 (1 A, 2 R, 3 G, 4 B; Pads 0.5 x 0.8, Abstand 0.7 / 0.2)
                              docs/datasheets/TUOZHAN_P4-1615G2B2R4TS2-06T-001-24_Datasheet_A0.pdf S.4
  Sunlord WPN201610H (Land a 0.7, b 0.7, c 1.7) docs/datasheets/Sunlord_WPN201610H100MT_Datasheet_LCSC-2023-10.pdf S.2
  Keystone 3034 (Clip-Pads W 23.1 min, 5.1 min; Minuspad >= 3.96 mm quadratisch)
                              docs/datasheets/Keystone_3034_Catalog_M65.pdf S.1 Fig. 1; Minuspad 4 x 4 mm nach
                              Auflage R2-W01 Nr. 1 (Pad sicher innerhalb der Minuskappe, Panasonic CR2032 Zeichnung
                              S.1: Minusseite (phi 17.0) "for reference")
Aufruf: .venv/bin/python hardware/sensor/gen/gen_lib.py
"""
import copy
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sexpr  # noqa: E402
from sexpr import Q  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LIBDIR = os.path.normpath(os.path.join(HERE, "..", "lib"))
KICAD_SYM = "/usr/share/kicad/symbols"
KICAD_FP = "/usr/share/kicad/footprints"


# ------------------------------------------------------------------ Symbol-Hilfen
def font(size=1.27):
    return ["effects", ["font", ["size", str(size), str(size)]]]


def prop(name, value, x=0.0, y=0.0, hide=False, justify=None):
    p = ["property", Q(name), Q(value), ["at", f"{x:g}", f"{y:g}", "0"]]
    if hide:
        p.append(["hide", "yes"])
    eff = font()
    if justify:
        eff.append(["justify", justify])
    p.append(eff)
    return p


def pin(etype, x, y, ang, name, num, length=2.54, hide=False):
    p = ["pin", etype, "line", ["at", f"{x:g}", f"{y:g}", str(ang)], ["length", f"{length:g}"]]
    if hide:
        p.append(["hide", "yes"])
    p += [["name", Q(name), font()], ["number", Q(num), font()]]
    return p


def rect(x1, y1, x2, y2, fill="background"):
    return ["rectangle", ["start", f"{x1:g}", f"{y1:g}"], ["end", f"{x2:g}", f"{y2:g}"],
            ["stroke", ["width", "0.254"], ["type", "default"]], ["fill", ["type", fill]]]


def polyline(pts, width=0.254):
    return ["polyline", ["pts"] + [["xy", f"{x:g}", f"{y:g}"] for x, y in pts],
            ["stroke", ["width", f"{width:g}"], ["type", "default"]], ["fill", ["type", "none"]]]


def text(t, x, y, size=1.27):
    return ["text", Q(t), ["at", f"{x:g}", f"{y:g}", "0"], font(size)]


def symbol(name, ref, value, footprint, datasheet, descr, graphics, pins, extra_props=()):
    s = ["symbol", Q(name), ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"],
         prop("Reference", ref, 0, 0), prop("Value", value, 0, -2.54),
         prop("Footprint", footprint, 0, -5.08, hide=True), prop("Datasheet", datasheet, 0, -7.62, hide=True),
         prop("Description", descr, 0, -10.16, hide=True)]
    s += list(extra_props)
    s.append(["symbol", Q(name + "_0_1")] + graphics)
    s.append(["symbol", Q(name + "_1_1")] + pins)
    s.append(["embedded_fonts", "no"])
    return s


def sym_cc2340():
    left = [("VDDS", "11", "power_in"), ("VDDS", "18", "power_in"), ("VDDS", "24", "power_in"),
            ("VDDR", "2", "passive"), ("VDDR", "20", "passive"), ("DCDC", "17", "power_out"),
            ("VDDD", "16", "power_out"), ("RSTN", "13", "input"), None,
            ("X48P", "21", "passive"), ("X48N", "22", "passive"),
            ("DIO3_X32P", "14", "bidirectional"), ("DIO4_X32N", "15", "bidirectional")]
    right = [("ANT", "1", "passive"), None, ("DIO6_A1", "19", "bidirectional"), ("DIO8", "3", "bidirectional"),
             ("DIO11", "4", "bidirectional"), ("DIO12", "5", "bidirectional"), ("DIO13", "6", "bidirectional"),
             ("DIO16_SWDIO", "7", "bidirectional"), ("DIO17_SWDCK", "8", "bidirectional"),
             ("DIO20_A11", "9", "bidirectional"), ("DIO21_A10", "10", "bidirectional"),
             ("DIO24_A7", "12", "bidirectional")]
    pins = []
    y0 = 15.24
    for i, p in enumerate(left):
        if p:
            pins.append(pin(p[2], -17.78, y0 - 2.54 * i, 0, p[0], p[1]))
    for i, p in enumerate(right):
        if p:
            pins.append(pin(p[2], 17.78, y0 - 2.54 * i, 180, p[0], p[1]))
    pins.append(pin("power_in", -2.54, -22.86, 90, "GND", "23"))
    pins.append(pin("power_in", 2.54, -22.86, 90, "EP", "25"))
    g = [rect(-15.24, 17.78, 15.24, -20.32)]
    return symbol("CC2340R52E0RGER", "U", "CC2340R52E0RGER",
                  "Package_DFN_QFN:VQFN-24-1EP_4x4mm_P0.5mm_EP2.45x2.45mm",
                  "docs/datasheets/TI_CC2340R5_Datasheet_SWRS272F.pdf",
                  "BLE-SoC CC2340R52, VQFN-24 RGE; Pinbelegung DS S.7 Abb. 6-2, Tab. 6-1; EP = Pin 25 (GND, S.77)",
                  g, pins)


def sym_ao3401a():
    lib = sexpr.parse(open(os.path.join(KICAD_SYM, "Device.kicad_sym")).read())
    src = next(x for x in lib if isinstance(x, list) and x[0] == "symbol" and x[1] == "Q_PMOS")
    s = copy.deepcopy(src)
    s[1] = Q("AO3401A")
    mapping = {"G": "1", "S": "2", "D": "3"}

    def walk(node):
        for i, x in enumerate(node):
            if isinstance(x, list):
                if x and x[0] == "symbol" and isinstance(x[1], str) and x[1].startswith("Q_PMOS_"):
                    x[1] = Q(x[1].replace("Q_PMOS_", "AO3401A_"))
                if x and x[0] == "number" and x[1] in mapping:
                    x[1] = Q(mapping[x[1]])
                walk(x)
    walk(s)
    for p in sexpr.find_all(s, "property"):
        if p[1] == "Value":
            p[2] = Q("AO3401A")
        elif p[1] == "Footprint":
            p[2] = Q("Package_TO_SOT_SMD:SOT-23")
        elif p[1] == "Datasheet":
            p[2] = Q("docs/datasheets/AOS_AO3401A_Datasheet_Rev3.1.pdf")
        elif p[1] == "Description":
            p[2] = Q("P-MOSFET 30 V SOT-23; Pins 1 G, 2 S, 3 D (DS S.1 SOT23 Top View)")
    # Fussabdruckfilter und Keywords der Vorlage entfernen
    s[:] = [x for x in s if not (isinstance(x, list) and x[0] == "property" and x[1] in ("ki_fp_filters",))]
    return s


def sym_tmp1075n():
    pins = [pin("bidirectional", -10.16, 2.54, 0, "SDA", "6"), pin("input", -10.16, 0, 0, "SCL", "1"),
            pin("input", -10.16, -2.54, 0, "A0", "4"), pin("open_collector", 10.16, 0, 180, "ALERT", "3"),
            pin("power_in", 0, 7.62, 270, "V+", "5"), pin("power_in", 0, -7.62, 90, "GND", "2")]
    g = [rect(-7.62, 5.08, 7.62, -5.08)]
    return symbol("TMP1075NDRL", "U", "TMP1075NDRLR", "Package_TO_SOT_SMD:SOT-563",
                  "docs/datasheets/TI_TMP1075_Datasheet_SBOS854F.pdf",
                  "Temperatursensor I2C TMP1075N, SOT-563 (DRL); Pins DS S.4 Abb. 5-4, Tab. 5-1; V+ 1.62-3.6 V (S.5)",
                  g, pins)


def sym_antenna():
    g = [polyline([(0, 0), (0, 5.08)]), polyline([(-2.54, 5.08), (0, 2.54), (2.54, 5.08), (-2.54, 5.08)]),
         text("AN043 IFA", 6.35, 3.81)]
    pins = [pin("passive", -5.08, 0, 0, "FEED", "1"), pin("passive", 0, -5.08, 90, "GND", "2")]
    # Leitung FEED -> Antennenfuss
    g.append(polyline([(-2.54, 0), (0, 0)]))
    return symbol("ANT_IFA_AN043", "AE", "AN043_IFA", "RF_Antenna:Texas_SWRA117D_2.4GHz_Left",
                  "docs/appnotes/TI_AN043_SmallPCBAntenna_SWRA117D.pdf",
                  "PCB-Antenne (Leiterbahn) nach TI AN043; Platzhalter-Footprint, Geometrie im Layout pruefen",
                  g, pins)


def sym_probe():
    g = [rect(-5.08, 7.62, 5.08, -7.62, fill="none"),
         polyline([(-2.54, 5.08), (-2.54, -5.08)], 0.508), polyline([(2.54, 5.08), (2.54, -5.08)], 0.508)]
    pins = [pin("passive", -7.62, 0, 0, "SENSE", "1"), pin("passive", 7.62, 0, 180, "GND_BAND", "2")]
    return symbol("SONDE_ELEKTRODEN", "E", "Sonde_Innenlagen", "fluidi:SONDE_PLATZHALTER", "",
                  "Sondenelektroden auf Innenlagen (Teil der Leiterplatte); Geometrie aus Feldsimulation",
                  g, pins)


def write_symbols():
    syms = [sym_cc2340(), sym_ao3401a(), sym_tmp1075n(), sym_antenna(), sym_probe()]
    # nicht bestueckbare Leiterplattenstrukturen aus der Stueckliste nehmen
    for s in syms[3:]:
        for i, x in enumerate(s):
            if isinstance(x, list) and x[0] == "in_bom":
                s[i] = ["in_bom", "no"]
    lib = ["kicad_symbol_lib", ["version", "20241209"], ["generator", Q("fluidi_gen_lib")],
           ["generator_version", Q("1.0")]] + syms
    os.makedirs(LIBDIR, exist_ok=True)
    with open(os.path.join(LIBDIR, "fluidi.kicad_sym"), "w") as f:
        f.write(sexpr.dump(lib) + "\n")


# ------------------------------------------------------------------ Footprints
def fp_head(name, descr, attr="smd"):
    return ["footprint", Q(name), ["version", "20241229"], ["generator", Q("fluidi_gen_lib")],
            ["layer", Q("F.Cu")], ["descr", Q(descr)], ["tags", Q("fluidi")],
            ["property", Q("Reference"), Q("REF**"), ["at", "0", "-2", "0"], ["layer", Q("F.SilkS")],
             ["effects", ["font", ["size", "0.6", "0.6"], ["thickness", "0.1"]]]],
            ["property", Q("Value"), Q(name), ["at", "0", "2", "0"], ["layer", Q("F.Fab")],
             ["effects", ["font", ["size", "0.6", "0.6"], ["thickness", "0.1"]]]],
            ["attr"] + attr.split()]


def fp_pad(num, x, y, w, h, shape="rect", layers=("F.Cu", "F.Paste", "F.Mask")):
    return ["pad", Q(num), "smd", shape, ["at", f"{x:g}", f"{y:g}"], ["size", f"{w:g}", f"{h:g}"],
            ["layers"] + [Q(l) for l in layers]]


def fp_line(x1, y1, x2, y2, layer="F.SilkS", w=0.12):
    return ["fp_line", ["start", f"{x1:g}", f"{y1:g}"], ["end", f"{x2:g}", f"{y2:g}"],
            ["stroke", ["width", f"{w:g}"], ["type", "solid"]], ["layer", Q(layer)]]


def fp_rect(x1, y1, x2, y2, layer, w=0.05):
    return ["fp_rect", ["start", f"{x1:g}", f"{y1:g}"], ["end", f"{x2:g}", f"{y2:g}"],
            ["stroke", ["width", f"{w:g}"], ["type", "solid"]], ["fill", "no"], ["layer", Q(layer)]]


def fp_text(t, x, y, layer="F.Fab", size=0.5):
    return ["fp_text", "user", Q(t), ["at", f"{x:g}", f"{y:g}", "0"], ["layer", Q(layer)],
            ["effects", ["font", ["size", f"{size:g}", f"{size:g}"], ["thickness", "0.08"]]]]


def write_fp(node):
    d = os.path.join(LIBDIR, "fluidi.pretty")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, node[1] + ".kicad_mod"), "w") as f:
        f.write(sexpr.dump(node) + "\n")


def fp_led1615():
    # DS S.4 "Recommended Solder Pad Design": Pad 0.5 (x) x 0.8 (y), Luecke 0.7 (x) / 0.2 (y)
    # Top View: Pin 2 oben links, 3 oben rechts, 1 unten links, 4 unten rechts
    px, py = 0.35 + 0.25, 0.1 + 0.4
    n = fp_head("LED_RGB_TUOZHAN_1615", "RGB-LED 1.6 x 1.5 mm, gem. Anode, TUOZHAN P4-1615G2B2R4TS2-06T-001-24 "
                "(LCSC C7496855), Pads nach Datenblatt S.4")
    n += [fp_pad("1", -px, py, 0.5, 0.8), fp_pad("2", -px, -py, 0.5, 0.8),
          fp_pad("3", px, -py, 0.5, 0.8), fp_pad("4", px, py, 0.5, 0.8),
          fp_rect(-0.75, -0.8, 0.75, 0.8, "F.Fab", 0.1), fp_rect(-1.15, -1.2, 1.15, 1.2, "F.CrtYd"),
          fp_line(-1.1, 1.15, -0.2, 1.15), fp_line(-1.1, 1.15, -1.1, 0.95)]  # Markierung bei Pin 1 (Anode)
    write_fp(n)


def fp_wpn201610():
    # DS S.2 Recommended Land Pattern WPN201610H: a = 0.7 (Luecke), b = 0.7 (Padbreite), c = 1.7 (Padlaenge)
    n = fp_head("L_Sunlord_WPN201610H", "Leistungsspule Sunlord WPN201610H 2.0 x 1.6 mm (LCSC C89132), "
                "Land Pattern nach Datenblatt S.2")
    n += [fp_pad("1", -0.7, 0, 0.7, 1.7), fp_pad("2", 0.7, 0, 0.7, 1.7),
          fp_rect(-1.0, -0.8, 1.0, 0.8, "F.Fab", 0.1), fp_rect(-1.3, -1.1, 1.3, 1.1, "F.CrtYd"),
          fp_line(-0.2, -0.95, 0.2, -0.95), fp_line(-0.2, 0.95, 0.2, 0.95)]
    write_fp(n)


def fp_keystone3034():
    src = sexpr.parse(open(os.path.join(KICAD_FP, "Battery.pretty", "BatteryHolder_Keystone_3034_1x20mm.kicad_mod"))
                      .read())
    n = copy.deepcopy(src)
    n[1] = Q("BatteryHolder_Keystone_3034_1x20mm_NegPad4mm")
    for i, x in enumerate(n):
        if isinstance(x, list) and x[0] == "descr":
            n[i] = ["descr", Q("Keystone 3034 (LCSC C5213768), Clip-Pads aus KiCad-Bibliothek (W 23.24 >= 23.1, "
                               "Hoehe 5.08 ~ 5.1 min, Katalog S.1 Fig. 1); Minuspad 4 x 4 mm (>= 3.96 mm SQ min) "
                               "nach Auflage R2-W01 Nr. 1, statt 17.8-mm-Kreis der Bibliothek")]
        if isinstance(x, list) and x[0] == "pad" and x[1] == "2":
            # ohne Lotpaste wie die KiCad-Vorlage: Kontaktflaeche ENIG blank (A-32), kein Lothoecker unter der Zelle
            n[i] = ["pad", Q("2"), "smd", "rect", ["at", "0", "0"], ["size", "4", "4"],
                    ["layers", Q("F.Cu"), Q("F.Mask")]]
        if isinstance(x, list) and x[0] == "generator":
            n[i] = ["generator", Q("fluidi_gen_lib")]
    n.append(fp_text("R2-W01: unter der Zelle nur Loetstopplack", 0, 4, "Cmts.User", 0.8))
    write_fp(n)


def fp_probe():
    n = fp_head("SONDE_PLATZHALTER", "Platzhalter Sondenelektroden (Innenlagen). Echte Geometrie folgt aus "
                "simulation/field; im Layout als Zonen In1/In2.Cu ersetzen", attr="smd exclude_from_pos_files "
                                                                               "exclude_from_bom")
    n += [fp_pad("1", -1.0, 0, 0.6, 0.6), fp_pad("2", 1.0, 0, 0.6, 0.6),
          fp_text("SONDE PLATZHALTER", 0, -1.2, "F.Fab", 0.5), fp_rect(-1.6, -0.6, 1.6, 0.6, "F.CrtYd")]
    write_fp(n)


def main():
    write_symbols()
    fp_led1615()
    fp_wpn201610()
    fp_keystone3034()
    fp_probe()
    print("Bibliothek geschrieben:", LIBDIR)


if __name__ == "__main__":
    main()
