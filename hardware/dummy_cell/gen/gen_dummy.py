#!/usr/bin/env python3
"""fluidi Dummy-Scheibe Rev 1 - Generator fuer zwei Leiterplatten (Weg B, PROGRAMMIEREN_SENSOR.md Kap. 5).

Aufbau (hardware/dummy_cell/README.md):
  PLUS  (oben, FR-4 1.0 mm): Oberseite Kupferscheibe = + (der Clip BT1 Keystone 3034 drueckt darauf), Lasche mit
        Loetpad "+". Keine Vias, keine Unterseiten-Kupferflaeche.
  MINUS (unten, FR-4 2.0 mm): Unterseite Mittelinsel Oe 8 mm = - (liegt auf dem Minuspad 4 x 4 mm von BT1),
        4 Vias -> Leitung auf der Oberseite (unter PLUS, isoliert) -> Loetpad "-" auf der Lasche.
        Optional (Variante B2, Handloeten): TX-Puffer SN74AUP1G17 + R 10 MOhm + C 100 nF wie Programmieradapter
        Rev 1 U4/R1/C5 (hardware/programmer/README.md Kap. 2.1), damit Weg B ohne Draht an R9 ueber TP1 geht.
  Gesamtdicke 1.0 + 2.0 + Kleber = 3.0-3.2 mm (PS-W3), Paarung nach Messung (README Kap. 4).

Koordinaten: Scheibenmitte = (0, 0) + Blattversatz (OX, OY); Lasche in +x (= offenes Clip-Ende, Einschub +X).
Aufruf:  .venv/bin/python hardware/dummy_cell/gen/gen_dummy.py   (aus dem Repo-Wurzelordner; run_all.sh)
"""
import math
import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
LIB = os.path.join(ROOT, "lib", "fluidi_dummy.pretty")
KLIB = "/usr/share/kicad/footprints"
OX, OY = 100.0, 100.0
REV = "1"

# ---------------------------------------------------------------- Masse (README Kap. 2/3)
R_DISC = 9.9            # Oe 19.8 mm; JLC Konturtoleranz +-0.2 -> 19.6-20.0 (CR2032 Oe 20.0, Panasonic DS S. 1)
TAB_W = 4.0             # halbe Laschenbreite im Clip-Bereich (Clip-Enden bei |y| ~ 6.1, Footprint BT1 F.Fab)
PLATE_D = 19.0          # Kupferscheibe PLUS (0.4 mm zur Kontur)
ISLAND_D = 8.0          # Mittelinsel MINUS (deckt Minuspad 4 x 4 = 5.66 mm Diagonale + 1.17 mm Lage)
ISLAND_F_D = 7.0        # Gegenflaeche auf MINUS-Oberseite (Vias), unter PLUS, abgedeckt
PLUS_L = 18.0           # Laschenende PLUS
MINUS_STEP = 11.0       # MINUS: ab hier breit (ausserhalb Sensorplatine, Kante bei x = 10)
MINUS_W = 9.0           # halbe Breite breiter Teil
MINUS_L = 34.5          # Laschenende MINUS
ALIGN = [(11.6, 2.9), (11.6, -2.9)]   # Passloecher Oe 1.0 NPTH (beide Platinen gleich) fuer Klebelehre
VIA_D, VIA_DR = 0.6, 0.3


def mm(v):
    return pcbnew.FromMM(v)


def P(x, y):
    return pcbnew.VECTOR2I(mm(x + OX), mm(y + OY))


# ---------------------------------------------------------------- Footprints (s-expr, eigene Bibliothek)
FP_TMPL = """(footprint "{name}"
	(version 20241229)
	(generator "fluidi_gen_dummy")
	(layer "F.Cu")
	(descr "{descr}")
	(attr {attr})
	(property "Reference" "{ref}" (at 0 {refy} 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))
	(property "Value" "{name}" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 1 1) (thickness 0.15))))
{pads}
)
"""


def write_footprints():
    os.makedirs(LIB, exist_ok=True)
    fps = {
        "PLUS_PLATE": dict(ref="J1", refy=0, attr="smd exclude_from_pos_files exclude_from_bom",
                           descr="Kontaktscheibe + (Clip BT1), Oe %.1f mm, Loetstopp offen" % PLATE_D,
                           pads='\t(pad "1" smd circle (at 0 0) (size {d} {d}) (layers "F.Cu" "F.Mask") '
                                '(solder_mask_margin 0))'.format(d=PLATE_D)),
        "MINUS_ISLAND": dict(ref="J2", refy=0, attr="smd exclude_from_pos_files exclude_from_bom",
                             descr="Mittelinsel - (Minuspad BT1 4 x 4 mm), Oe %.1f mm unten offen, Oe %.1f oben "
                                   "abgedeckt" % (ISLAND_D, ISLAND_F_D),
                             pads='\t(pad "1" smd circle (at 0 0) (size {d} {d}) (layers "B.Cu" "B.Mask") '
                                  '(solder_mask_margin 0))\n'
                                  '\t(pad "1" smd circle (at 0 0) (size {f} {f}) (layers "F.Cu"))'
                                  .format(d=ISLAND_D, f=ISLAND_F_D)),
        "PAD_SMD_4p5x5": dict(ref="J", refy=0, attr="smd exclude_from_pos_files exclude_from_bom",
                              descr="Loetpad fuer Litze, nur Oberseite (keine Unterseiten-Kupferflaeche auf PLUS)",
                              pads='\t(pad "1" smd rect (at 0 0) (size 4.5 5) (layers "F.Cu" "F.Mask"))'),
        "PAD_PTH_3p5x5_D1p2": dict(ref="J", refy=0, attr="through_hole exclude_from_pos_files exclude_from_bom",
                                   descr="Loetpad mit Bohrung 1.2 mm fuer Litze (Netzteil -)",
                                   pads='\t(pad "1" thru_hole rect (at 0 0) (size 3.5 5) (drill 1.2) '
                                        '(layers "*.Cu" "*.Mask"))'),
        "PAD_PTH_D2p2_D1p0": dict(ref="J", refy=0, attr="through_hole exclude_from_pos_files exclude_from_bom",
                                  descr="Loetauge Oe 2.2 mm, Bohrung 1.0 mm fuer Litze",
                                  pads='\t(pad "1" thru_hole circle (at 0 0) (size 2.2 2.2) (drill 1.0) '
                                       '(layers "*.Cu" "*.Mask"))'),
        "HOLE_NPTH_1p0": dict(ref="H", refy=0, attr="exclude_from_pos_files exclude_from_bom",
                              descr="Passloch Oe 1.0 mm (Klebelehre PLUS/MINUS)",
                              pads='\t(pad "" np_thru_hole circle (at 0 0) (size 1.0 1.0) (drill 1.0) '
                                   '(layers "*.Cu" "*.Mask"))'),
    }
    for name, d in fps.items():
        with open(os.path.join(LIB, name + ".kicad_mod"), "w") as f:
            f.write(FP_TMPL.format(name=name, **d))


# ---------------------------------------------------------------- Board-Helfer
class Board:
    def __init__(self, thickness):
        self.b = pcbnew.BOARD()
        self.b.SetCopperLayerCount(2)
        ds = self.b.GetDesignSettings()
        ds.SetBoardThickness(mm(thickness))
        self.nets = {}

    def net(self, name):
        if name not in self.nets:
            n = pcbnew.NETINFO_ITEM(self.b, name)
            self.b.Add(n)
            self.nets[name] = n
        return self.nets[name]

    def fp(self, lib, name, ref, x, y, rot=0, nets=None, val=None):
        f = pcbnew.FootprintLoad(lib, name)
        if f is None:
            sys.exit("Footprint fehlt: %s/%s" % (lib, name))
        f.SetReference(ref)
        f.SetValue(val or name)
        f.SetPosition(P(x, y))
        f.SetOrientationDegrees(rot)
        f.Reference().SetVisible(False)          # Bezeichner als eigene Texte (Platz, JLC-Mindesthoehe)
        self.b.Add(f)
        for pad in f.Pads():
            if nets and pad.GetNumber() in nets:
                pad.SetNet(self.net(nets[pad.GetNumber()]))
        return f

    def pads(self, f):
        out = {}
        for pad in f.Pads():
            q = pad.GetPosition()
            out[pad.GetNumber()] = (pcbnew.ToMM(q.x) - OX, pcbnew.ToMM(q.y) - OY)
        return out

    def track(self, pts, w, net, layer=pcbnew.F_Cu):
        for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
            t = pcbnew.PCB_TRACK(self.b)
            t.SetStart(P(xa, ya))
            t.SetEnd(P(xb, yb))
            t.SetWidth(mm(w))
            t.SetLayer(layer)
            t.SetNet(self.net(net))
            self.b.Add(t)

    def via(self, x, y, net):
        v = pcbnew.PCB_VIA(self.b)
        v.SetPosition(P(x, y))
        v.SetWidth(mm(VIA_D))
        v.SetDrill(mm(VIA_DR))
        v.SetViaType(pcbnew.VIATYPE_THROUGH)
        v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        v.SetNet(self.net(net))
        self.b.Add(v)

    def edge(self, pts, arc=None):
        """Kontur: Polylinie pts (geschlossen ueber arc = (start, mid, end) von pts[-1] nach pts[0])."""
        for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
            s = pcbnew.PCB_SHAPE(self.b, pcbnew.SHAPE_T_SEGMENT)
            s.SetStart(P(xa, ya))
            s.SetEnd(P(xb, yb))
            s.SetLayer(pcbnew.Edge_Cuts)
            s.SetWidth(mm(0.1))
            self.b.Add(s)
        if arc:
            s = pcbnew.PCB_SHAPE(self.b, pcbnew.SHAPE_T_ARC)
            s.SetArcGeometry(P(*arc[0]), P(*arc[1]), P(*arc[2]))
            s.SetLayer(pcbnew.Edge_Cuts)
            s.SetWidth(mm(0.1))
            self.b.Add(s)

    def text(self, s, x, y, h, layer, rot=0, thick=0.18):
        t = pcbnew.PCB_TEXT(self.b)
        t.SetText(s)
        t.SetPosition(P(x, y))
        t.SetLayer(layer)
        t.SetTextSize(pcbnew.VECTOR2I(mm(h * 0.9), mm(h)))
        t.SetTextThickness(mm(thick))
        t.SetTextAngleDegrees(rot)
        if layer in (pcbnew.B_SilkS, pcbnew.B_Fab):
            t.SetMirrored(True)
        self.b.Add(t)

    def save(self, path):
        ds = self.b.GetDesignSettings()
        ds.SetAuxOrigin(P(0, 0))
        ds.SetGridOrigin(P(0, 0))
        pcbnew.SaveBoard(path, self.b)


def disc_outline(b, tab_pts):
    """Scheibe R_DISC mit Lasche; tab_pts von (xt, -TAB_W) bis (xt, +TAB_W) im Uhrzeigersinn ueber +x."""
    xt = math.sqrt(R_DISC ** 2 - TAB_W ** 2)
    pts = [(xt, -TAB_W)] + tab_pts + [(xt, TAB_W)]
    b.edge(pts, arc=((xt, TAB_W), (-R_DISC, 0.0), (xt, -TAB_W)))


def fab_note(b, lines):
    for i, s in enumerate(lines):
        b.text(s, -10.0 + 0.0, -14.0 - 1.6 * (len(lines) - i), 1.0, pcbnew.F_Fab)


# ---------------------------------------------------------------- PLUS (oben, 1.0 mm)
def build_plus(path):
    b = Board(1.0)
    disc_outline(b, [(PLUS_L, -TAB_W), (PLUS_L, TAB_W)])
    b.fp(LIB, "PLUS_PLATE", "J1", 0, 0, nets={"1": "VBAT_DUMMY"}, val="Kontakt +")
    b.fp(LIB, "PAD_SMD_4p5x5", "J3", 14.85, 0, nets={"1": "VBAT_DUMMY"}, val="Netzteil +")
    b.track([(9.2, 0), (12.8, 0)], 3.0, "VBAT_DUMMY")
    for i, (x, y) in enumerate(ALIGN):
        b.fp(LIB, "HOLE_NPTH_1p0", "H%d" % (i + 1), x, y, val="Passloch")
    F = pcbnew.F_SilkS
    b.text("+", 11.0, 0.0, 1.6, F, thick=0.25)
    b.text("DUMMY", 14.85, 3.25, 1.0, F)
    b.text("+2.0V", 14.85, -3.25, 1.0, F)
    fab_note(b, ["fluidi Dummy-Scheibe PLUS Rev %s (oben, +)" % REV,
                 "JLC: FR-4 2 Lagen 1.0 mm, 1 oz, HASL bleifrei, gruen, 5 Stk, ohne Bestueckung",
                 "Kupferscheibe offen (Kontakt Clip), keine Vias, Unterseite ohne Kupfer"])
    b.save(path)


# ---------------------------------------------------------------- MINUS (unten, 2.0 mm)
def build_minus(path):
    b = Board(2.0)
    disc_outline(b, [(MINUS_STEP, -TAB_W), (MINUS_STEP, -MINUS_W), (MINUS_L, -MINUS_W),
                     (MINUS_L, MINUS_W), (MINUS_STEP, MINUS_W), (MINUS_STEP, TAB_W)])
    g = "GND_DUMMY"
    b.fp(LIB, "MINUS_ISLAND", "J2", 0, 0, nets={"1": g}, val="Kontakt -")
    for k in range(4):
        a = math.radians(45 + 90 * k)
        b.via(3.4 * math.cos(a), 3.4 * math.sin(a), g)          # ausserhalb Minuspad 4 x 4 (Ecke r 2.83)
    b.fp(LIB, "PAD_PTH_3p5x5_D1p2", "J4", 21.0, 0, nets={"1": g}, val="Netzteil -")
    b.track([(3.2, 0), (19.6, 0)], 1.0, g)
    for i, (x, y) in enumerate(ALIGN):
        b.fp(LIB, "HOLE_NPTH_1p0", "H%d" % (i + 1), x, y, val="Passloch")

    # Variante B2 (optional, Handloeten): Schmitt-Puffer wie Programmieradapter U4/R1/C5
    j5 = b.fp(LIB, "PAD_PTH_D2p2_D1p0", "J5", 24.2, 5.5, nets={"1": g}, val="GND UART")
    j6 = b.fp(LIB, "PAD_PTH_D2p2_D1p0", "J6", 24.2, -5.5, nets={"1": "TX_PROBE"}, val="TP1-Pruefspitze")
    j7 = b.fp(LIB, "PAD_PTH_D2p2_D1p0", "J7", 31.5, -5.5, nets={"1": "VIO"}, val="VIO (Netzteil +)")
    j8 = b.fp(LIB, "PAD_PTH_D2p2_D1p0", "J8", 32.0, 4.5, nets={"1": "RXD_HOST"}, val="RXD USB-UART")
    u = b.fp(KLIB + "/Package_TO_SOT_SMD.pretty", "SOT-23-5_HandSoldering", "U1", 27.5, 0,
             nets={"2": "TX_PROBE", "3": g, "4": "RXD_HOST", "5": "VIO"}, val="SN74AUP1G17DBVR")
    r = b.fp(KLIB + "/Resistor_SMD.pretty", "R_0402_1005Metric_Pad0.72x0.64mm_HandSolder", "R1", 24.7975, -3.0,
             nets={"1": "TX_PROBE", "2": "VIO"}, val="10M")
    c = b.fp(KLIB + "/Capacitor_SMD.pretty", "C_0805_2012Metric_Pad1.18x1.45mm_HandSolder", "C1", 31.0, -2.2,
             rot=90, nets={}, val="100n")
    cp = b.pads(c)
    c_vio, c_gnd = sorted(cp.items(), key=lambda kv: kv[1][1])          # oberes Pad (kleineres y) = VIO
    for pad in c.Pads():
        pad.SetNet(b.net("VIO" if pad.GetNumber() == c_vio[0] else g))
    up, rp = b.pads(u), b.pads(r)
    tw = 0.3
    b.track([up["3"], (22.4, up["3"][1])], tw, g)                                   # GND -> Pad -
    b.track([(24.2, 5.5), (22.2, 5.5), (22.2, 2.0)], tw, g)                         # GND UART -> Pad -
    b.track([up["2"], (24.2, up["2"][1]), (24.2, -5.5)], tw, "TX_PROBE")             # Puffer A -> TP1-Pad (R1 Pad 1)
    b.track([rp["2"], (up["5"][0], rp["2"][1])], tw, "VIO")                         # R1 -> VCC
    b.track([up["5"], (up["5"][0], -5.5), (31.5, -5.5)], tw, "VIO")                 # VCC -> VIO-Pad
    b.track([(up["5"][0], c_vio[1][1]), c_vio[1]], tw, "VIO")                       # VCC -> C1
    b.track([up["4"], (32.0, up["4"][1]), (32.0, 4.5)], tw, "RXD_HOST")             # Y -> RXD-Pad
    vx = 32.6
    b.track([c_gnd[1], (vx, c_gnd[1][1])], tw, g)
    b.via(vx, c_gnd[1][1], g)
    b.track([(vx, c_gnd[1][1]), (21.0, c_gnd[1][1])], 0.4, g, layer=pcbnew.B_Cu)   # C1-GND unten -> Pad -

    # Regelflaeche: Scheiben-Unterseite nur Mittelinsel (keine Leitung/Flaeche), B.Cu
    z = pcbnew.ZONE(b.b)
    z.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    ls.AddLayer(pcbnew.B_Cu)
    z.SetLayerSet(ls)
    ol = z.Outline()
    ol.NewOutline()
    for k in range(72):
        a = 2 * math.pi * k / 72
        q = P((R_DISC + 0.5) * math.cos(a), (R_DISC + 0.5) * math.sin(a))
        ol.Append(q.x, q.y)
    z.SetZoneName("SCHEIBE_UNTEN")
    z.SetDoNotAllowTracks(True)
    z.SetDoNotAllowZoneFills(True)
    z.SetDoNotAllowVias(False)
    z.SetDoNotAllowPads(False)
    z.SetDoNotAllowFootprints(False)
    b.b.Add(z)

    F, B = pcbnew.F_SilkS, pcbnew.B_SilkS
    b.text("-", 21.0, 3.4, 1.6, F, thick=0.25)
    b.text("GND", 24.2, 7.6, 1.0, F)
    b.text("TP1", 24.2, -7.6, 1.0, F)
    b.text("VIO", 31.5, -7.6, 1.0, F)
    b.text("RXD", 32.0, 6.6, 1.0, F)
    b.text("DUMMY", 14.6, 6.5, 1.0, F)
    b.text("Rev " + REV, 14.6, -6.5, 1.0, F)
    b.text("U1 AUP1G17", 27.2, 2.6, 1.0, F)
    b.text("R1", 26.6, -4.2, 1.0, F)
    b.text("C1", 33.3, -2.2, 1.0, F)
    b.text("DUMMY", 15.5, 0.0, 1.5, B, rot=90, thick=0.25)
    b.text("KEINE ZELLE", 18.0, 0.0, 1.0, B, rot=90)
    b.text("max 2.1 V / 10 mA", 26.6, 8.0, 1.0, B)
    b.text("fluidi Dummy Rev " + REV, 26.6, -8.0, 1.0, B)
    b.text("d=_____mm", 28.0, 2.6, 1.0, B)
    fab_note(b, ["fluidi Dummy-Scheibe MINUS Rev %s (unten, -)" % REV,
                 "JLC: FR-4 2 Lagen 2.0 mm, 1 oz, HASL bleifrei, gruen, 5 Stk, ohne Bestueckung",
                 "U1/R1/C1 optional (Variante B2), von Hand: Programmieradapter-Teile P3/P5/P6"])
    b.save(path)


DRU = """(version 1)
# fluidi Dummy-Scheibe - erzeugt von hardware/dummy_cell/gen/gen_dummy.py (nicht von Hand aendern)
# ---------------- JLC 2 Lagen (docs/references/JLCPCB_NOTES.md Kap. 3, abgerufen 2026-11-06), mit Reserve
(rule "JLC Abstand Kupfer >= 0.10 (Entwurf 0.15)"
  (constraint clearance (min 0.15mm)))
(rule "JLC Leiterbahnbreite >= 0.10"
  (condition "A.Type == 'Track'")
  (constraint track_width (min 0.1mm)))
(rule "JLC Via Durchmesser >= 0.45 (ohne Aufpreis), Bohrung >= 0.20"
  (condition "A.Type == 'Via'")
  (constraint via_diameter (min 0.45mm))
  (constraint hole_size (min 0.2mm)))
(rule "JLC Restring Via >= 0.15 (2 L absolut 0.18 PTH, empfohlen 0.25)"
  (condition "A.Type == 'Via'")
  (constraint annular_width (min 0.15mm)))
(rule "JLC Restring PTH-Pad >= 0.25 (empfohlen)"
  (condition "A.Type == 'Pad' && A.Pad_Type == 'Through-hole'")
  (constraint annular_width (min 0.25mm)))
(rule "JLC NPTH >= 0.50"
  (condition "A.Type == 'Pad' && A.Pad_Type == 'NPTH, mechanical'")
  (constraint hole_size (min 0.5mm)))
(rule "JLC Bohrabstand >= 0.25"
  (constraint hole_to_hole (min 0.25mm)))
(rule "JLC Bohrung - Kupfer >= 0.20"
  (constraint hole_clearance (min 0.2mm)))
(rule "JLC Kupfer - Kontur >= 0.30 (gefraest >= 0.2)"
  (constraint edge_clearance (min 0.3mm)))
(rule "JLC SMD-Pad - Pad >= 0.15"
  (condition "A.Type == 'Pad' && B.Type == 'Pad'")
  (constraint clearance (min 0.15mm)))
(rule "JLC Silkscreen Text >= 1.0 / 0.15"
  (layer "?.Silkscreen")
  (condition "A.Type == 'Text' || A.Type == 'Field'")
  (constraint text_height (min 1.0mm))
  (constraint text_thickness (min 0.15mm)))
# ---------------- Projektregeln Dummy-Scheibe (README Kap. 3)
"""
DRU_PLUS = """(rule "PLUS: keine Vias (Kontaktflaeche plan, Unterseite isolierend)"
  (condition "A.Type == 'Via'")
  (constraint disallow via))
(rule "PLUS: Unterseite ohne Kupfer (R2-W01, keine Plusflaeche unten)"
  (layer B.Cu)
  (condition "A.Type == 'Track' || A.Type == 'Zone' || (A.Type == 'Pad' && A.Pad_Type != 'NPTH, mechanical')")
  (constraint disallow track zone pad))
"""
DRU_MINUS = """(rule "MINUS: Scheiben-Unterseite nur Mittelinsel und Vias (keine Leitungen/Flaechen)"
  (layer B.Cu)
  (condition "A.intersectsArea('SCHEIBE_UNTEN') && (A.Type == 'Track' || A.Type == 'Zone')")
  (constraint disallow track zone))
"""


def main():
    write_footprints()
    plus = os.path.join(ROOT, "fluidi_dummy_plus.kicad_pcb")
    minus = os.path.join(ROOT, "fluidi_dummy_minus.kicad_pcb")
    build_plus(plus)
    build_minus(minus)
    for path, extra in ((plus, DRU_PLUS), (minus, DRU_MINUS)):
        with open(path.replace(".kicad_pcb", ".kicad_dru"), "w") as f:
            f.write(DRU + extra)
        # Projektdatei: ohne sie laedt kicad-cli die .kicad_dru nicht (geprueft 2026-11-09, KiCad 10.0.8)
        with open(path.replace(".kicad_pcb", ".kicad_pro"), "w") as f:
            f.write('{\n  "meta": {\n    "filename": "%s",\n    "version": 3\n  }\n}\n'
                    % os.path.basename(path).replace(".kicad_pcb", ".kicad_pro"))
    print("geschrieben:", plus, minus)


if __name__ == "__main__":
    main()
