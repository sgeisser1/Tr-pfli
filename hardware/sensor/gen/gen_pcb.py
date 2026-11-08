#!/usr/bin/env python3
"""fluidi Sensor Rev B - Layout-Generator (KiCad 10, pcbnew).

Aufruf aus dem Repo-Wurzelordner:
    .venv/bin/python hardware/sensor/gen/gen_pcb.py [--u3 kragen|band] [--out hardware/sensor/fluidi_sensor.kicad_pcb]
    bash hardware/sensor/gen/run_pcb.sh          # Generator + DRC (WSL + Windows) + Exporte

Quellen (verbindlich):
- Kontur, Zonen, feste Lagen: mechanical/interfaces/pcb_outline.json (docs/interfaces/PCB_OUTLINE.md Rev B)
- Netze/Bauteile: hardware/sensor/gen/parts.py (gleiche Quelle wie der Schaltplan)
- Elektroden: simulation/field/REPORT.md Kap. 8 (z_f = -z, KiCad-Y = 53.5 + z_f)
- Antenne: docs/appnotes/TI_AN043_SmallPCBAntenna_SWRA117D.pdf S. 4 Abb. 3 / Tab. 1
  (KiCad-Footprint RF_Antenna:Texas_SWRA117D_2.4GHz_Right, Masse gegen Tab. 1 geprueft, LAYOUT_REV_B.md Kap. 3)
- Sicherheit: CONCEPTS 2.7 (R2-A3), S2-W03/S3-K1 (Fach/Schott), phase4_sicherheit_kragen_firmware.md K-1...K-3
- JLC-Regeln: docs/references/JLCPCB_NOTES.md Kap. 3/4 (Stackup JLC04161H-7628)

Koordinaten: Schnittstelle X = x, Y = 53.5 - z; im KiCad-Dokument um (OX, OY) verschoben, Hilfs-/Bohrursprung dort.
"""
import argparse
import json
import math
import os
import re
import sys

import numpy as np
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "../../.."))
sys.path.insert(0, HERE)
import parts  # noqa: E402
import pcb_place  # noqa: E402
from pcb_router import Router, HARD  # noqa: E402

OX, OY = 150.0, 30.0
STD_FP = "/usr/share/kicad/footprints"
LOC_FP = os.path.join(ROOT, "hardware/sensor/lib/fluidi.pretty")
OUTLINE = json.load(open(os.path.join(ROOT, "mechanical/interfaces/pcb_outline.json")))

# Fertigungs-/Projektregeln (mm)
CLR = 0.15            # Entwurfsabstand (DRC-Grenze 0.10, JLC 0.09)
TW_SIG = 0.15
TW_PWR = 0.2
TW_RF = 0.35          # 50 Ohm Mikrostreifen L1 ueber L2 (Prepreg 0.21, Er 4.4) - ANNAHME, JLC-Rechner pruefen
VIA_D, VIA_DRILL = 0.45, 0.3
EDGE_CLR = 0.3
PROBE_EDGE = 1.25     # Feld Kap. 8 / PCB_OUTLINE Z7
ELEC_X = 10.0 - PROBE_EDGE   # 8.75

# Feldsimulation Kap. 8 (z_f) -> KiCad-Y = 53.5 + z_f
def yf(zf):
    return 53.5 + zf


S_Y0, S_Y1 = yf(10), yf(86)          # S-Elektrode
G_Y1 = yf(90)                        # G bis z_f 90
STEG_Y0 = yf(88)                     # G-Steg z_f 88...90
GUARD_Y1 = yf(8)                     # Guard bis z_f 8
BAND_Y0, BAND_Y1 = 5.7, 20.8
KEEPOUT_Y = 5.2                      # Masseflaeche ab hier (AN043 D4)
SCHOTT_Y0, SCHOTT_Y1 = 20.8, 23.2
FACH_Y1 = 46.7                       # Rev C (V-K): Z4 bis Y 46.7
Z5B_Y1 = 50.0
Z5A_Y1 = 52.7
VERGUSS_SCHOTT_Y, VERGUSS_KRAGEN_Y, VERGUSS_SONDE_Y = 22.70, 46.90, 52.20   # PCB_OUTLINE Rev C Kap. 6.3
ANSCHLAG = (-8.0, 0.0, -3.0, 1.5)     # Platinenanschlag der Kappe: keine Bauteile
Z6_Y1 = 58.5
U3_FIELD = (-9.0, 47.4, -4.6, 49.8)  # x0, y0, x1, y1 (K-2: x >= -9.0; Rev C/V-K Y 47.4 ... 49.8)

POWER_NETS = {"VDD", "VBAT", "VDDR", "DCDC_SW", "OSC_PWR"}


def mm(v):
    return pcbnew.FromMM(float(v))


def P(x, y):
    return pcbnew.VECTOR2I(mm(x + OX), mm(y + OY))


def fp_path(fpid):
    lib, name = fpid.split(":")
    if lib == "fluidi":
        return LOC_FP, name
    return os.path.join(STD_FP, lib + ".pretty"), name


def footprint_id(c):
    fpid = c["fp"]
    if c["ref"] == "AE1":
        fpid = "RF_Antenna:Texas_SWRA117D_2.4GHz_Right"
    return fpid


# ---------------------------------------------------------------- Kontur
def outline_pts():
    return [tuple(p) for p in OUTLINE["board"]["outline_kicad_XY"]]


def draw_outline(board):
    """Gerade Stuecke als Linien, Schulter-Innenecken als Bogen R 2.0 (PCB_OUTLINE Kap. 2)."""
    segs = [((-2.5, 158.5), (2.5, 158.5)), ((2.5, 158.5), (10, 151)), ((10, 151), (10, 45.8284)),
            ((10.5858, 44.4142), (13, 42)), ((13, 42), (13, 0)), ((13, 0), (-13, 0)), ((-13, 0), (-13, 42)),
            ((-13, 42), (-10.5858, 44.4142)), ((-10, 45.8284), (-10, 151)), ((-10, 151), (-2.5, 158.5))]
    for a, b in segs:
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(P(*a))
        s.SetEnd(P(*b))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.05))
        board.Add(s)
    for sx in (1, -1):
        c = (sx * 12.0, 45.8284)
        a = math.radians(202.5)
        mid = (c[0] + sx * 2 * math.cos(a), c[1] + 2 * math.sin(a))
        s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_ARC)
        s.SetArcGeometry(P(sx * 10.0, 45.8284), P(*mid), P(sx * 10.5858, 44.4142))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(mm(0.05))
        board.Add(s)


def board_poly(inset=0.0, ymin=None, ymax=None):
    """Konturpolygon (Bogen als Segmente) eingerueckt um inset; optional in Y beschnitten (fuer Zonen)."""
    pts = outline_pts()
    # Bogen feiner
    sp = pcbnew.SHAPE_POLY_SET()
    sp.NewOutline()
    for x, y in pts:
        sp.Append(mm(x), mm(y))
    if inset:
        sp.Inflate(mm(-inset), pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS, mm(0.005))
    if ymin is not None or ymax is not None:
        y0 = -10 if ymin is None else ymin
        y1 = 200 if ymax is None else ymax
        clip = rect_poly(-20, y0, 20, y1)
        sp.BooleanIntersection(clip)
    return sp


def rect_poly(x0, y0, x1, y1):
    sp = pcbnew.SHAPE_POLY_SET()
    sp.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        sp.Append(mm(x), mm(y))
    return sp


def poly_to_pts(sp, k=0):
    o = sp.Outline(k)
    return [(pcbnew.ToMM(o.CPoint(i).x), pcbnew.ToMM(o.CPoint(i).y)) for i in range(o.PointCount())]


def shifted(sp):
    out = pcbnew.SHAPE_POLY_SET(sp)
    out.Move(pcbnew.VECTOR2I(mm(OX), mm(OY)))
    return out


# ---------------------------------------------------------------- Bauteile
# Ersatz-3D-Modelle (nur fuer STEP/Render und die Kollisionspruefung der Mechanik; Masse vergleichbar):
# U1: KiCad-Bibliothek hat kein Modell fuer EP 2.45 -> TI RGE0024H (gleiches Gehaeuse 4 x 4 VQFN, anderes EP),
# BT1: Original-KiCad-Modell 3034 (gleicher Footprint-Ursprung), L1: Murata DFE201610P (2.0 x 1.6 x 1.0 wie WPN201610H).
MODEL_SUBST = {
    "U1": "${KICAD9_3DMODEL_DIR}/Package_DFN_QFN.3dshapes/Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm.step",
    "BT1": "${KICAD9_3DMODEL_DIR}/Battery.3dshapes/BatteryHolder_Keystone_3034_1x20mm.step",
    "L1": "${KICAD9_3DMODEL_DIR}/Inductor_SMD.3dshapes/L_Murata_DFE201610P.step",
}


def load_fp(board, c, place):
    lib, name = fp_path(footprint_id(c))
    fp = pcbnew.FootprintLoad(lib, name)
    if fp is None:
        raise SystemExit("Footprint fehlt: %s" % footprint_id(c))
    fp.SetFPIDAsString(footprint_id(c))
    fp.SetParent(board)
    if c["ref"] in MODEL_SUBST:
        m = pcbnew.FP_3DMODEL()
        m.m_Filename = MODEL_SUBST[c["ref"]]
        fp.Models().clear()
        fp.Models().push_back(m)
    fp.SetReference(c["ref"])
    fp.SetValue(c["val"])
    x, y, rot, side = place[c["ref"]]
    board.Add(fp)
    if side == "B":
        fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_TOP_BOTTOM)
    fp.SetPosition(P(x, y))
    fp.SetOrientationDegrees(rot)
    if c["dnp"]:
        fp.SetDNP(True)
        fp.SetExcludedFromPosFiles(True)
    if c["key"] == "PCB":
        fp.SetExcludedFromBOM(True)
        fp.SetExcludedFromPosFiles(True)
    # Referenz nur auf Fab (Band zu dicht fuer Silkscreen-Referenzen; Bestueckungsplan aus F.Fab)
    ref = fp.Reference()
    ref.SetLayer(pcbnew.F_Fab if side == "F" else pcbnew.B_Fab)
    ref.SetTextSize(pcbnew.VECTOR2I(mm(0.5), mm(0.5)))
    ref.SetTextThickness(mm(0.08))
    ref.SetPosition(fp.GetPosition())
    fp.Value().SetVisible(False)
    return fp


def build_e1(board):
    """Sonde als Bauteil E1: Innenlagen-Pads in den Elektroden (Netzzuordnung fuer Schaltplan-Paritaet)."""
    fp = pcbnew.FOOTPRINT(board)
    fp.SetFPIDAsString("fluidi:SONDE_PLATZHALTER")
    fp.SetReference("E1")
    fp.SetValue("Sonde_Innenlagen")
    board.Add(fp)
    fp.SetPosition(P(0, 100))
    for num, x in (("1", -4.9), ("2", 4.9)):
        pad = pcbnew.PAD(fp)
        pad.SetNumber(num)
        pad.SetShape(pcbnew.PAD_SHAPE_RECTANGLE)
        pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        pad.SetSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
        ls = pcbnew.LSET()
        ls.AddLayer(pcbnew.In1_Cu)
        pad.SetLayerSet(ls)
        fp.Add(pad)
        pad.SetPosition(P(x, 100))
    fp.SetExcludedFromBOM(True)
    fp.SetExcludedFromPosFiles(True)
    fp.Reference().SetLayer(pcbnew.F_Fab)
    fp.Value().SetVisible(False)
    return fp


def courtyard_boxes(fps):
    out = {}
    for ref, fp in fps.items():
        for lay in (pcbnew.F_CrtYd, pcbnew.B_CrtYd):
            cy = fp.GetCourtyard(lay)
            if cy.OutlineCount():
                b = cy.BBox()
                out[ref] = (pcbnew.ToMM(b.GetX()) - OX, pcbnew.ToMM(b.GetY()) - OY,
                            pcbnew.ToMM(b.GetRight()) - OX, pcbnew.ToMM(b.GetBottom()) - OY, lay)
    return out


def check_placement(fps, u3):
    bx = courtyard_boxes(fps)
    errs = []
    refs = sorted(bx)
    for a in range(len(refs)):
        for b in range(a + 1, len(refs)):
            A, B = bx[refs[a]], bx[refs[b]]
            if A[4] != B[4]:
                continue
            if A[0] < B[2] and B[0] < A[2] and A[1] < B[3] and B[1] < A[3]:
                if {refs[a], refs[b]} & {"BT1", "E1"} and not ({refs[a], refs[b]} <= {"BT1", "TP1", "TP2", "TP3"}):
                    pass
                errs.append("Ueberlappung %s / %s" % (refs[a], refs[b]))
    for r, (x0, y0, x1, y1, lay) in bx.items():
        if r in ("BT1", "E1", "AE1", "TP1", "TP2", "U3", "C24"):
            continue
        if x0 < -12.7 or x1 > 12.7 or y0 < BAND_Y0 or y1 > BAND_Y1:
            errs.append("%s ausserhalb Band: %.2f %.2f %.2f %.2f" % (r, x0, y0, x1, y1))
    return errs, bx


# ---------------------------------------------------------------- Plot (Kontrolle)
def plot_band(fps, rt, fname, title=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Polygon
    fig, ax = plt.subplots(figsize=(16, 10))
    bx = courtyard_boxes(fps)
    for r, (x0, y0, x1, y1, lay) in bx.items():
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="#999" if lay == pcbnew.F_CrtYd else "#c9c",
                               lw=0.6))
        if y0 > 22:
            continue
        ax.text((x0 + x1) / 2, (y0 + y1) / 2, r, fontsize=6, ha="center", va="center", color="#555")
    for fp in fps.values():
        for pad in fp.Pads():
            if pcbnew.ToMM(pad.GetPosition().y) - OY > 22:
                continue
            sp = pcbnew.SHAPE_POLY_SET()
            lay = pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else (pcbnew.B_Cu if pad.IsOnLayer(pcbnew.B_Cu)
                                                                    else pcbnew.In1_Cu)
            pad.TransformShapeToPolygon(sp, lay, 0, mm(0.005), pcbnew.ERROR_INSIDE)
            for k in range(sp.OutlineCount()):
                pts = [(x - OX, y - OY) for x, y in poly_to_pts(sp, k)]
                ax.add_patch(Polygon(pts, closed=True, fc={pcbnew.F_Cu: "#d62728", pcbnew.B_Cu: "#1f77b4"}.get(lay, "#2ca02c"),
                                     alpha=0.6, ec="none"))
            ax.text(pcbnew.ToMM(pad.GetPosition().x) - OX, pcbnew.ToMM(pad.GetPosition().y) - OY,
                    pad.GetNetname()[:6], fontsize=3.2, ha="center", va="center")
    if rt is not None:
        colors = {"F.Cu": "#d62728", "In2.Cu": "#ff7f0e", "B.Cu": "#1f77b4", "In1.Cu": "#2ca02c"}
        for (lay, xa, ya, xb, yb, w, net) in rt.segments:
            ax.plot([xa, xb], [ya, yb], color=colors.get(lay, "k"), lw=w * 28, alpha=0.7, solid_capstyle="round")
        for (x, y, net) in rt.vias:
            ax.add_patch(plt.Circle((x, y), VIA_D / 2, fc="#444", ec="none"))
    ax.set_xlim(-13.5, 13.5)
    ax.set_ylim(21.5, -0.5)
    ax.set_aspect("equal")
    ax.axhline(BAND_Y0, color="g", lw=0.5)
    ax.axhline(BAND_Y1, color="g", lw=0.5)
    ax.axhline(KEEPOUT_Y, color="m", lw=0.5)
    ax.set_title(title)
    ax.grid(True, lw=0.2)
    fig.savefig(fname, dpi=160, bbox_inches="tight")
    plt.close(fig)


def read_netlist():
    """Netzliste des Schaltplans (hardware/sensor/out/fluidi_sensor.net, von check_netlist.py erzeugt):
    Netznamen je Pad, Felder und Symbol-UUID je Bauteil (fuer die Schaltplan-Paritaet im DRC)."""
    import sexpr
    tree = sexpr.parse(open(os.path.join(ROOT, "hardware/sensor/out/fluidi_sensor.net")).read())
    comps = {}
    for c in sexpr.find_all(sexpr.find(tree, "components"), "comp"):
        ref = sexpr.find(c, "ref")[1]
        fields = {}
        fl = sexpr.find(c, "fields")
        for f in (sexpr.find_all(fl, "field") if fl else []):
            fields[sexpr.find(f, "name")[1]] = f[2] if len(f) > 2 else ""
        for k in ("datasheet", "description"):
            v = sexpr.find(c, k)
            if v:
                fields[k.capitalize()] = v[1]
        comps[ref] = dict(fields=fields, uuid=sexpr.find(c, "tstamps")[1])
    pins = {}
    for n in sexpr.find_all(sexpr.find(tree, "nets"), "net"):
        name = sexpr.find(n, "name")[1]
        for node in sexpr.find_all(n, "node"):
            pins[(sexpr.find(node, "ref")[1], sexpr.find(node, "pin")[1])] = name
    return comps, pins


def short(name):
    return name[1:] if name.startswith("/") else name


def build_footprints(board, u3):
    place = pcb_place.placement(u3)
    comps, pins = read_netlist()
    nets = {}

    def net(full):
        k = short(full)
        if k not in nets:
            ni = pcbnew.NETINFO_ITEM(board, full)
            board.Add(ni)
            nets[k] = ni
        return nets[k]

    fps = {}
    for c in parts.COMPONENTS:
        if c["ref"] == "E1":
            continue   # Sonde = Innenlagen-Zonen (Symbol "nicht auf Platine", gen_schematic.py)
        fp = load_fp(board, c, place)
        fps[c["ref"]] = fp
        info = comps[c["ref"]]
        for k, v in info["fields"].items():
            if k == "Footprint":
                continue
            fp.SetField(k, v)
            f = fp.GetField(k)
            f.SetVisible(False)
            f.SetLayer(pcbnew.F_Fab if place[c["ref"]][3] == "F" else pcbnew.B_Fab)
        fp.SetPath(pcbnew.KIID_PATH("/" + info["uuid"]))
        fp.SetSheetname("/")
        fp.SetSheetfile("fluidi_sensor.kicad_sch")
        for pad in fp.Pads():
            full = pins.get((c["ref"], pad.GetNumber()))
            if full is None:
                continue
            want = c["conns"].get(pad.GetNumber())
            if want and short(full) != want and not full.startswith("unconnected"):
                raise SystemExit("Netz-Abweichung %s.%s: %s / %s" % (c["ref"], pad.GetNumber(), full, want))
            pad.SetNet(net(full))   # auch "unconnected-(...)" (Schaltplan-Paritaet)
        if c["ref"] == "BT1":
            fp.SetDuplicatePadNumbersAreJumpers(True)
    return fps, nets, place


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--u3", choices=("kragen", "band"), default="kragen")
    ap.add_argument("--out", default=os.path.join(ROOT, "hardware/sensor/fluidi_sensor.kicad_pcb"))
    ap.add_argument("--place-only", action="store_true")
    ap.add_argument("--plot", default=None)
    ap.add_argument("--seed", type=int, default=0, help="0 = feste Reihenfolge, sonst Mischung der Signalnetze")
    ap.add_argument("--max-it", dest="max_it", type=int, default=900)
    a = ap.parse_args()
    board = pcbnew.CreateEmptyBoard() if hasattr(pcbnew, "CreateEmptyBoard") else pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    fps, nets, place = build_footprints(board, a.u3)
    errs, bx = check_placement(fps, a.u3)
    for e in errs:
        print("PLATZ:", e)
    if a.place_only:
        plot_band(fps, None, a.plot or "/tmp/place.png", "Platzierung")
        return
    import pcb_build
    pcb_build.build(board, fps, nets, place, a)


if __name__ == "__main__":
    main()
