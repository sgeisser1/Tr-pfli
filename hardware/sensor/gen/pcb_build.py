"""fluidi Sensor Rev B - Aufbau des Layouts (von gen_pcb.py aufgerufen).

Schritte: Designregeln -> feste Kupferstrukturen (HF-Kette, Speisevias, Innenlagen-Leitungen Fach/Kragen,
Kragenfeld U3) -> Raster-Router (GND-Fanout, dann Netze nach Prioritaet) -> Zonen (Masseflaechen, Elektroden,
Guard) -> Regelflaechen (Keepouts, Projektregeln) -> Silkscreen -> Speichern, Stackup, Projektregeln.
"""
import json
import math
import os
import re
import time

import numpy as np
import pcbnew

import gen_pcb as G
import pcb_place as PL
from pcb_router import Router, HARD, simplify

mm, P = G.mm, G.P

ROUTE_ORDER = ["X48N", "X48P", "X32P", "X32N", "DCDC_SW", "VDDD", "VDDR", "RSTN",
               "OSZ_OUT", "PROBE_SENSE", "DIV2", "DIV4", "MEAS_CLK", "OSC_PWR", "CREF1_CTL", "OSC_EN_N",
               "VBAT", "SENS_PWR", "I2C_SDA", "I2C_SCL",
               "LED_R_K", "LED_G_K", "LED_B_K", "LED_R_UART_TX", "LED_G", "LED_B_UART_RX", "BTN_BOOT_N",
               "UART_TX_MID", "UART_RX_MID", "UART_TX_PAD", "UART_RX_PAD"]
REV = "C"
FIXED_NETS = {"RF_PIN", "RF_FILT", "RF_ANT_DC", "ANT_FEED", "X48P", "X48N"}
TW_XTAL = 0.15


# ---------------------------------------------------------------- Board-Objekte
LAYER_IDS = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu,
             "F.SilkS": pcbnew.F_SilkS, "B.SilkS": pcbnew.B_SilkS, "F.Fab": pcbnew.F_Fab, "B.Fab": pcbnew.B_Fab,
             "User.2": pcbnew.User_2}


def lid(board, name):
    return LAYER_IDS[name]

def add_track(board, nets, layer, pts, width, net):
    layer_id = lid(board, layer)
    for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(P(xa, ya))
        t.SetEnd(P(xb, yb))
        t.SetWidth(mm(width))
        t.SetLayer(layer_id)
        t.SetNet(nets[net])
        board.Add(t)


def add_via(board, nets, x, y, net, filled=False):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(P(x, y))
    v.SetWidth(mm(G.VIA_D))
    v.SetDrill(mm(G.VIA_DRILL))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(nets[net])
    if filled:
        # Via-in-Pad im Zellfach: Epoxid gefuellt und ueberkupfert (JLC POFV), REQ-MECH-05
        try:
            v.SetFillingMode(pcbnew.FILLING_MODE_FILLED)
            v.SetCappingMode(pcbnew.CAPPING_MODE_CAPPED)
        except Exception:
            pass
    else:
        try:
            v.SetFrontTentingMode(pcbnew.TENTING_MODE_TENTED)
            v.SetBackTentingMode(pcbnew.TENTING_MODE_TENTED)
        except Exception:
            pass
    board.Add(v)
    return v


def add_zone(board, nets, layer, sp, net, prio=0, clr=0.2, minw=0.2, name=None, full=True):
    z = pcbnew.ZONE(board)
    z.SetLayer(lid(board, layer))
    z.Outline().Append(G.shifted(sp))
    if net:
        z.SetNet(nets[net])
    z.SetAssignedPriority(prio)
    z.SetLocalClearance(mm(clr))
    z.SetMinThickness(mm(minw))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if full else pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    if name:
        z.SetZoneName(name)
    board.Add(z)
    return z


def add_rule_area(board, name, sp, layers, tracks=False, vias=False, pads=False, pour=False, fps=False):
    z = pcbnew.ZONE(board)
    z.SetIsRuleArea(True)
    ls = pcbnew.LSET()
    for l in layers:
        ls.AddLayer(lid(board, l))
    z.SetLayerSet(ls)
    z.Outline().Append(G.shifted(sp))
    z.SetZoneName(name)
    z.SetDoNotAllowTracks(tracks)
    z.SetDoNotAllowVias(vias)
    z.SetDoNotAllowPads(pads)
    z.SetDoNotAllowZoneFills(pour)
    z.SetDoNotAllowFootprints(fps)
    board.Add(z)
    return z


def silk_text(board, text, x, y, h, layer, thick=0.18, mirror=False, rot=0, just=None, wf=0.9):
    t = pcbnew.PCB_TEXT(board)
    t.SetText(text)
    t.SetPosition(P(x, y))
    t.SetLayer(lid(board, layer))
    t.SetTextSize(pcbnew.VECTOR2I(mm(h * wf), mm(h)))
    t.SetTextThickness(mm(thick))
    t.SetMirrored(mirror)
    t.SetTextAngleDegrees(rot)
    if just == "left":
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
    board.Add(t)
    return t


def silk_line(board, a, b, w, layer):
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(P(*a))
    s.SetEnd(P(*b))
    s.SetWidth(mm(w))
    s.SetLayer(lid(board, layer))
    board.Add(s)


def silk_poly(board, outlines, layer, holes=()):
    sp = pcbnew.SHAPE_POLY_SET()
    for k, pts in enumerate(outlines):
        sp.NewOutline()
        for x, y in pts:
            sp.Append(mm(x + G.OX), mm(y + G.OY))
    for (oi, pts) in holes:
        sp.NewHole(oi)
        for x, y in pts:
            sp.Append(mm(x + G.OX), mm(y + G.OY), oi, 0)
    s = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_POLY)
    s.SetPolyShape(sp)
    s.SetFilled(True)
    s.SetWidth(0)
    s.SetLayer(lid(board, layer))
    board.Add(s)


# ---------------------------------------------------------------- Logo (SVG, nur M/L/Z)
def logo_polys(svg_path, x0, y0, width):
    txt = open(svg_path).read()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', txt).group(1).split()]
    d = re.search(r' d="([^"]+)"', txt).group(1)
    s = width / vb[2]
    polys = []
    cur = []
    for tok in re.findall(r"[MLZ]|-?[\d.]+,-?[\d.]+", d):
        if tok == "M":
            cur = []
        elif tok == "L":
            pass
        elif tok == "Z":
            polys.append(cur)
            cur = []
        else:
            a, b = tok.split(",")
            cur.append((x0 + float(a) * s, y0 + float(b) * s))
    return polys, s


def poly_area(p):
    a = 0
    for (x1, y1), (x2, y2) in zip(p, p[1:] + p[:1]):
        a += x1 * y2 - x2 * y1
    return a / 2


def point_in(pt, poly):
    from matplotlib.path import Path
    return Path(poly).contains_point(pt)


# ---------------------------------------------------------------- Hauptablauf
def build(board, fps, nets, place, args):
    t0 = time.time()
    u3 = args.u3
    G.draw_outline(board)
    ds = board.GetDesignSettings()
    ds.m_MinClearance = mm(0.1)
    ds.m_TrackMinWidth = mm(0.1)
    ds.m_ViasMinSize = mm(0.45)
    ds.m_MinThroughDrill = mm(0.2)
    ds.m_ViasMinAnnularWidth = mm(0.075)
    ds.m_HoleToHoleMin = mm(0.25)
    ds.m_CopperEdgeClearance = mm(G.EDGE_CLR)
    ds.m_HoleClearance = mm(0.2)
    ds.m_MinSilkTextHeight = mm(1.0)
    ds.m_MinSilkTextThickness = mm(0.15)
    ds.SetAuxOrigin(P(0, 0))
    tb = board.GetTitleBlock()
    tb.SetTitle("fluidi Sensor")
    tb.SetRevision(REV)              # DFM K-5: Revision im Gerber-Job
    tb.SetDate("2026-11-08")
    tb.SetCompany("fluidi")
    tb.SetComment(0, "PCB_OUTLINE Rev C (D-023), JLC04161H-7628, ENIG, Via-in-Pad POFV")
    ds.SetGridOrigin(P(0, 0))

    # Silkscreen der Bibliotheks-Footprints auf JLC-Mindestbreite 0.15 mm
    for fp in fps.values():
        for it in fp.GraphicalItems():
            if it.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS) and isinstance(it, pcbnew.PCB_SHAPE):
                if it.GetWidth() < mm(0.15):
                    it.SetWidth(mm(0.15))

    # ---------- Router-Raster
    rt = Router(-13.0, 5.0, 13.0, 21.0, 0.05, ["F.Cu", "B.Cu"], G.CLR)
    nid = {}

    def NID(n):
        if n not in nid:
            nid[n] = len(nid) + 1
        return nid[n]

    for n in nets:
        NID(n)
    # harte Bereiche: Antennen-Keepout, Schott, Rand
    for L in range(rt.nl):
        rt.own[L][rt.ys < G.KEEPOUT_Y, :] = HARD
        rt.own[L][rt.ys > G.BAND_Y1, :] = HARD
        rt.own[L][:, np.abs(rt.xs) > 13.0 - G.EDGE_CLR - 0.05] = HARD
    rt.via_ok[:] = False
    jj = (rt.ys >= 5.65) & (rt.ys <= G.BAND_Y1 - 0.25)
    ii = np.abs(rt.xs) <= 12.4
    rt.via_ok[np.ix_(jj, ii)] = True

    # Pads malen
    pad_cells = {}   # net -> Liste Masken
    nc_id = 10000
    pad_mask_all = np.zeros((rt.ny, rt.nx), bool)
    lay_of = {"F.Cu": 0, "B.Cu": 1}
    for ref, fp in fps.items():
        for pad in fp.Pads():
            net = G.short(pad.GetNetname())
            if not net:
                nc_id += 1
                val = nc_id
            else:
                val = NID(net)
            layers = []
            for lname, li in lay_of.items():
                if pad.IsOnLayer(lid(board, lname)):
                    layers.append(li)
            if not layers:
                continue
            sp = pcbnew.SHAPE_POLY_SET()
            pad.TransformShapeToPolygon(sp, lid(board, "F.Cu") if 0 in layers else lid(board, "B.Cu"),
                                        0, mm(0.005), pcbnew.ERROR_OUTSIDE)
            m = np.zeros((rt.nl, rt.ny, rt.nx), bool)
            hit = False
            for k in range(sp.OutlineCount()):
                pts = [(x - G.OX, y - G.OY) for x, y in G.poly_to_pts(sp, k)]
                for li in layers:
                    r = rt.poly_mask(pts)
                    if r is None:
                        continue
                    (j0, j1, i0, i1), msk = r
                    if not msk.any():
                        continue
                    hit = True
                    rt.own[li, j0:j1, i0:i1][msk] = val
                    m[li, j0:j1, i0:i1] |= msk
                    pad_mask_all[j0:j1, i0:i1] |= msk
            if hit and net and not net.startswith("unconnected"):
                pad_cells.setdefault(net, []).append((ref, pad.GetNumber(), m))
    from scipy import ndimage
    dpad = ndimage.distance_transform_edt(~pad_mask_all) * rt.res
    rt.no_via = dpad <= 0.225 + 0.08

    def fixed_track(layer, pts, w, net, paint=True):
        add_track(board, nets, layer, pts, w, net)
        if layer in lay_of and paint:
            for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
                rt.paint_seg(lay_of[layer], xa, ya, xb, yb, w / 2, NID(net))

    exits = []

    def exit_track(x, y, length, net):
        """Ausgang eines Uebergabevias auf B.Cu reservieren; ins Board kommt nach dem Routing nur der benutzte Teil."""
        rt.paint_seg(lay_of["B.Cu"], x, y, x, y - length, TW_XTAL / 2, NID(net))
        exits.append((x, y, length, net))

    def fixed_via(x, y, net, filled=False):
        add_via(board, nets, x, y, net, filled)
        if rt.y0 <= y <= rt.y0 + rt.ny * rt.res:
            rt.paint_via(x, y, G.VIA_D / 2, NID(net))

    # ---------- HF-Kette (HW-Guide SWRA834A Kap. 4.2: Quer-C direkt an den Knoten)
    def padxy(ref, num):
        for p in fps[ref].Pads():
            if p.GetNumber() == num:
                return pcbnew.ToMM(p.GetPosition().x) - G.OX, pcbnew.ToMM(p.GetPosition().y) - G.OY
        raise KeyError(ref + num)

    ry = PL.RF_Y
    fixed_track("F.Cu", [padxy("C20", "1"), (PL.ANT_X, ry)], G.TW_RF, "ANT_FEED")
    fixed_track("F.Cu", [(PL.ANT_X, PL.ANT_Y), (PL.ANT_X, ry)], G.TW_RF, "ANT_FEED")
    fixed_track("F.Cu", [(PL.ANT_X, ry), padxy("R2", "2")], G.TW_RF, "ANT_FEED")
    fixed_track("F.Cu", [padxy("R2", "1"), padxy("C18", "2")], G.TW_RF, "RF_ANT_DC")
    fixed_track("F.Cu", [padxy("C18", "1"), padxy("L2", "2")], G.TW_RF, "RF_FILT")
    u1p1 = padxy("U1", "1")
    fixed_track("F.Cu", [padxy("L2", "1"), (PL.PIN1_X, ry), (PL.PIN1_X, u1p1[1] - 0.75)], G.TW_RF, "RF_PIN")
    fixed_track("F.Cu", [(PL.PIN1_X, u1p1[1] - 0.75), u1p1], 0.25, "RF_PIN")

    # ---------- U1 EP: 4 Massevias (DS S.77-78, thermisch/HF)
    ux, uy = padxy("U1", "25")
    for dx in (-0.6, 0.6):
        for dy in (-0.6, 0.6):
            fixed_via(ux + dx, uy + dy, "GND", filled=True)   # Via-in-Pad im EP: POFV (DFM W-6)
    # Antennen-Massepunkt (Pad 2 ist THT im Footprint) -> zusaetzlich 2 Vias neben dem Massearm (AN043 Abb. 3)
    # (Pad 2 = Via to ground)

    # U1 Pin 23 (GND) direkt an das EP (kurz, kein eigenes Via neben den Quarzleitungen)
    p23 = padxy("U1", "23")
    fixed_track("F.Cu", [p23, (ux, p23[1])], 0.2, "GND")

    # 48-MHz-Quarz: feste, kurze Leitungen (X48P zwischen den Pads von Y1 hindurch, DS S.26: keine externen C)
    p21, p22 = padxy("U1", "21"), padxy("U1", "22")
    y1p1, y1p3 = padxy("Y1", "1"), padxy("Y1", "3")
    xe = p21[0] + 0.2
    xm = (y1p1[0] + y1p3[0]) / 2
    fixed_track("F.Cu", [p22, (xe + 0.4, p22[1]), (y1p3[0] - 0.2, y1p3[1] + 0.25), y1p3], TW_XTAL, "X48N")
    fixed_track("F.Cu", [p21, (xe + 0.35, p21[1]), (xe + 0.6, p21[1] - 0.25), (xm, p21[1] - 0.25),
                         (xm, y1p1[1] - 0.4), (y1p1[0] - 0.3, y1p1[1])], TW_XTAL, "X48P")
    fixed_track("F.Cu", [(y1p1[0] - 0.3, y1p1[1]), y1p1], TW_XTAL, "X48P")

    # ---------- Speisevias S-Elektrode und Innenlagen-Zuleitungen (Feld Kap. 8, angepasst)
    fixed_via(PL.FEED_L2_X, PL.FEED_VIA_Y, "PROBE_SENSE")
    fixed_via(PL.FEED_L3_X, PL.FEED_VIA_Y, "PROBE_SENSE")
    fixed_track("In1.Cu", [(PL.FEED_L2_X, PL.FEED_VIA_Y), (PL.FEED_L2_X, G.S_Y0 + 0.5)], 0.3, "PROBE_SENSE")
    fixed_track("In2.Cu", [(PL.FEED_L3_X, PL.FEED_VIA_Y), (PL.FEED_L3_X, G.S_Y0 + 0.5)], 0.3, "PROBE_SENSE")

    # ---------- Zellfach: Via-in-Pad (gefuellt + ueberkupfert), Leitungen nur In2, Uebergabevia am Bandende
    stubs = {}   # net -> (x, y) Uebergabevia im Band (Y = PL.STUB_VIA_Y)
    vip = []
    bt_pads = sorted([p for p in fps["BT1"].Pads() if p.GetNumber() == "1"], key=lambda p: p.GetPosition().y)
    bx, by = pcbnew.ToMM(bt_pads[0].GetPosition().x) - G.OX, pcbnew.ToMM(bt_pads[0].GetPosition().y) - G.OY
    vy = max(by, G.SCHOTT_Y1 + 0.45)
    vip.append((bx, vy, "VBAT"))
    minus = [p for p in fps["BT1"].Pads() if p.GetNumber() == "2"][0]
    mx, my = pcbnew.ToMM(minus.GetPosition().x) - G.OX, pcbnew.ToMM(minus.GetPosition().y) - G.OY
    vip.append((mx, my, "GND"))
    for tp, net in (("TP1", "UART_TX_PAD"), ("TP2", "UART_RX_PAD")):   # TP3 entfaellt (A-1)
        x, y = padxy(tp, "1")
        vip.append((x, y, net))
    for (x, y, n) in vip:
        add_via(board, nets, x, y, n, filled=True)
    sy = PL.STUB_VIA_Y
    # VBAT auf In2: im Fach nach rechts (Kante >= 1.0, K-3), im Band am rechten und oberen Rand (VDD-Flaeche
    # bleibt zusammenhaengend) bis zum Uebergabevia neben Q1 (Verpolschutz oben links)
    # Stueck bei Y 20.5 getrennt: die Regel VBAT-GND >= 0.5 (LS-K2) gilt nur fuer die Stuecke in Schott/Fach
    vbat_pts = [(bx, vy), (PL.VBAT_X, vy), (PL.VBAT_X, PL.STUB_VIA_Y), (PL.VBAT_X, PL.VBAT_Y), PL.VBAT_VIA]
    fixed_track("In2.Cu", vbat_pts, 0.3, "VBAT")
    stubs["VBAT"] = PL.VBAT_VIA
    for (xa, ya), (xb, yb) in zip(vbat_pts[:-1], vbat_pts[1:]):
        (j0, j1, i0, i1), msk = rt.seg_mask(xa, ya, xb, yb, 0.15 + 0.225 + 0.25)
        rt.no_via[j0:j1, i0:i1] |= msk
    t1 = padxy("TP1", "1")
    t2 = padxy("TP2", "1")
    fixed_track("In2.Cu", [t1, (t1[0], sy)], 0.2, "UART_TX_PAD")
    stubs["UART_TX_PAD"] = (t1[0], sy)
    fixed_track("In2.Cu", [t2, (t2[0] - 1.0, t2[1] - 1.0), (t2[0] - 1.0, sy)], 0.2, "UART_RX_PAD")
    stubs["UART_RX_PAD"] = (t2[0] - 1.0, sy)

    # ---------- Kragenfeld U3 (Option kragen): Vias tented, x >= -9.0 (K-2), Leitungen In2 ins Band
    if u3 == "kragen":
        vx = PL.U3_VIA_X
        for n, y in PL.U3_VIA_Y.items():
            add_via(board, nets, vx, y, n)
        p = {k: padxy("U3", k) for k in "123456"}
        c24 = {k: padxy("C24", k) for k in "12"}
        w = 0.15
        add_track(board, nets, "F.Cu", [p["2"], (vx, PL.U3_VIA_Y["GND"])], 0.2, "GND")
        add_track(board, nets, "F.Cu", [p["1"], (vx, PL.U3_VIA_Y["I2C_SCL"])], w, "I2C_SCL")
        gx = (p["6"][0] + p["1"][0]) / 2
        add_track(board, nets, "F.Cu", [p["6"], (gx, p["6"][1]), (gx, G.U3_FIELD[1] + 0.15), (vx - 0.3, G.U3_FIELD[1] + 0.15),
                                        (vx, PL.U3_VIA_Y["I2C_SDA"])], w, "I2C_SDA")
        add_track(board, nets, "F.Cu", [p["4"], (c24["2"][0] + 0.45, p["4"][1]), c24["2"]], 0.2, "GND")
        add_via(board, nets, PL.U3_GND_VIA2[0], PL.U3_GND_VIA2[1], "GND")
        add_track(board, nets, "F.Cu", [PL.U3_GND_VIA2, c24["2"]], 0.2, "GND")
        add_track(board, nets, "F.Cu", [p["5"], (p["5"][0] - 0.45, p["5"][1]), c24["1"]], w, "SENS_PWR")
        add_track(board, nets, "F.Cu", [c24["1"], (c24["1"][0], G.U3_FIELD[3] - 0.15), (vx - 0.4, G.U3_FIELD[3] - 0.15),
                                        (vx, PL.U3_VIA_Y["SENS_PWR"])], w, "SENS_PWR")
        # Innenlage In2 (L3) nach oben ins Band, Abstand Kante >= 1.0 (K-3)
        for n in ("I2C_SDA", "I2C_SCL", "SENS_PWR"):
            x = PL.U3_LINE_X[n]
            y0 = PL.U3_VIA_Y[n]
            fixed_track("In2.Cu", [(vx, y0), (x, y0), (x, sy)], 0.2, n)
            stubs[n] = (x, sy)

    # Uebergabevias und Speisevias als Pads fuer den Router
    def via_cells(x, y):
        m = np.zeros((rt.nl, rt.ny, rt.nx), bool)
        (j0, j1, i0, i1), msk = rt.seg_mask(x, y, x, y, 0.2)
        m[:, j0:j1, i0:i1] = msk
        return m
    for n, (x, y) in stubs.items():
        fixed_via(x, y, n)
        if n != "VBAT":
            # Ausgang auf B.Cu freihalten (sonst kann der Fanout das Uebergabevia einschliessen)
            ex = 2.4 if n.startswith("UART") else 1.5
            exit_track(x, y, ex, n)
        pad_cells.setdefault(n, []).append(("VIA", n, via_cells(x, y)))
    for x in (PL.FEED_L2_X, PL.FEED_L3_X):
        exit_track(x, PL.FEED_VIA_Y, 1.5, "PROBE_SENSE")
        pad_cells.setdefault("PROBE_SENSE", []).append(("VIA", "S", via_cells(x, PL.FEED_VIA_Y)))

    # ---------- Fanout GND (In1) und VDD (In2 im Band): jedes Pad eigenes Via (HW-Guide Kap. 4.3)
    from scipy import ndimage as _nd
    foreign_pads = {}

    def fanout(netname, skip):
        nn = NID(netname)
        # Abstand zu fremden Pads (Signale), gekappt 0.8 mm: Vias nicht vor fremde Pads setzen
        fp_mask = np.zeros((rt.ny, rt.nx), bool)
        for nname, lst in pad_cells.items():
            if nname in (netname, "GND", "VDD"):
                continue
            for (_r, _n, mm_) in lst:
                fp_mask |= mm_[0]
        fan_score = np.minimum(_nd.distance_transform_edt(~fp_mask) * rt.res, 0.8)
        fl = []
        free_g = rt.free_masks(nn, 0.1)
        for (ref, num, m) in pad_cells.get(netname, []):
            if ref in ("AE1", "BT1", "VIA", "E1") or (ref, num) in skip:
                continue
            if u3 == "kragen" and ref in ("U3", "C24"):
                continue
            vf = rt.via_mask(nn, G.VIA_D / 2)
            ls, js, is_ = np.nonzero(m)
            if not len(js):
                continue
            win = (max(0, js.min() - 50), min(rt.ny, js.max() + 50), max(0, is_.min() - 50),
                   min(rt.nx, is_.max() + 50))
            src = m.copy()
            src[1:] = False
            path = rt.fanout_path(nn, 0.1, src, win, free_g, vf, fan_score)
            if path is None:
                path = rt.astar(nn, 0.1, src, None, window=win, goal_is_via=True, free=free_g, vfree=vf, max_len=2.5)
            if path is None:
                fl.append("%s.%s" % (ref, num))
                continue
            rt.commit_path(path, nn, 0.2 if netname == "GND" else 0.25, end_via=True)
            free_g = rt.free_masks(nn, 0.1)
        print("Fanout %s: %d Pads, Fehlschlag: %s" % (netname, len(pad_cells.get(netname, [])), fl or "keine"))
        return fl
    gfail = fanout("GND", {("U1", "25"), ("U1", "23")})
    vdd_u1 = [(r, n, m) for (r, n, m) in pad_cells["VDD"] if r == "U1"]
    gfail += fanout("VDD", {("U1", n) for (_, n, _) in vdd_u1})
    # VDDS-Pins an "ihren" Kondensator (DS/HW-Guide: Strom erst in den C, dann in den Pin)
    vdd_pairs = {"11": "C6", "18": "C7", "24": "C8"}
    vdd_cells = {}
    for (r, n, m) in pad_cells["VDD"]:
        vdd_cells[(r, n)] = m
    for pin, cref in vdd_pairs.items():
        f, _ = rt.route_net(NID("VDD"), G.TW_PWR / 2, [vdd_cells[("U1", pin)], vdd_cells[(cref, "1")]],
                            layer_cost=[1.0, 1.2])
        if f:
            gfail.append("VDD U1.%s-%s" % (pin, cref))

    # ---------- Netze routen: gierig in Prioritaetsreihenfolge, danach Rip-up & Reroute
    order = [n for n in ROUTE_ORDER if n in pad_cells]
    order += sorted(n for n in pad_cells if n not in order and n not in FIXED_NETS and n not in ("GND", "VDD"))
    if getattr(args, "seed", 0):
        import random
        rnd = random.Random(args.seed)
        head, tail = order[:4], order[4:]
        rnd.shuffle(tail)
        order = head + tail
    rt.set_base()
    inv0 = {v: k for k, v in nid.items()}
    cellsof = {NID(n): [m for (_, _, m) in pad_cells[n]] for n in order}
    rips = {}
    queue = [NID(n) for n in order]
    fails = {}
    best_state = None
    it = 0
    max_it = getattr(args, "max_it", 700)
    while queue and it < max_it:
        it += 1
        n = queue.pop(0)
        name = inv0[n]
        cells = cellsof[n]
        if len(cells) < 2:
            continue
        rt.rip(n)
        hw = (G.TW_PWR if name in G.POWER_NETS else G.TW_SIG) / 2
        allow = rips.get(n, 0) < 40 and it > len(order)
        if it % 50 == 0:
            print("   Iteration %d, offen %d, Warteschlange %d (%.0f s)" % (it, len(fails), len(queue), time.time() - t0))
        f, ripped = rt.route_net(n, hw, cells, layer_cost=[1.0, 1.2], rr=allow)
        if f and name in G.POWER_NETS:
            rt.rip(n)
            f, r2 = rt.route_net(n, 0.1, cells, layer_cost=[1.0, 1.2], rr=allow)
            ripped |= r2
        for v in ripped:
            rips[v] = rips.get(v, 0) + 1
            if v not in queue:
                queue.append(v)
            fails.pop(v, None)
        if f:
            fails[n] = f
            if rips.get(n, 0) < 40:
                queue.append(n)   # spaeter mit Rip-up erneut
        else:
            fails.pop(n, None)
        score = len(set(queue) | set(fails))
        if best_state is None or score < best_state[0]:
            best_state = (score, rt.own.copy(), list(rt.segments), list(rt.vias), list(rt.holes), dict(fails),
                          list(queue))
        if score == 0:
            break
    if best_state is not None and best_state[0] < len(set(queue) | set(fails)):
        _, own_b, seg_b, via_b, hol_b, fails, queue = best_state
        rt.own[:] = own_b
        rt.segments[:], rt.vias[:], rt.holes[:] = seg_b, via_b, hol_b
    for n in queue:
        fails[n] = fails.get(n, 0) or -1
    fails = {inv0[k]: v for k, v in fails.items()}
    # Endkontrolle: jedes Netz vollstaendig?
    print("Routing: %d Netze, %d Iterationen, offen: %s (%.0f s)" % (len(order), it, fails or "keine",
                                                                    time.time() - t0))

    # Router-Ergebnis ins Board
    inv = {v: k for k, v in nid.items()}
    for (lay, xa, ya, xb, yb, w, n) in rt.segments:
        if (xa, ya) == (xb, yb):
            continue
        add_track(board, nets, lay, [(xa, ya), (xb, yb)], w, inv[n])
    fixed_xy = set()
    for (x, y, n) in rt.vias:
        key = (round(x, 3), round(y, 3))
        if key in fixed_xy:
            continue
        fixed_xy.add(key)
        # feste Vias (EP, Speisung) wurden schon angelegt -> nur Router-Vias
    router_vias = rt.vias[len([1 for _ in []]):]
    # reservierte Via-Ausgaenge auf den benutzten Teil kuerzen (sonst offene Bahnenden)
    for (x, y, length, net) in exits:
        nn = NID(net)
        ys = []
        for (lay, xa, ya, xb, yb, w, n2) in rt.segments:
            if n2 != nn or lay != "B.Cu":
                continue
            for (px, py) in ((xa, ya), (xb, yb)):
                if abs(px - x) < 0.03 and y - length - 0.03 <= py <= y + 0.03:
                    ys.append(py)
        if ys and min(ys) < y - 0.03:
            add_track(board, nets, "B.Cu", [(x, y), (x, min(ys))], TW_XTAL, net)
    return_state = dict(rt=rt, nid=nid, fails=fails, gfail=gfail, stubs=stubs, vip=vip)
    _finish(board, fps, nets, place, args, rt, nid, return_state)


def _finish(board, fps, nets, place, args, rt, nid, st):
    inv = {v: k for k, v in nid.items()}
    # Router-Vias anlegen (feste Vias sind schon im Board; Router kennt sie als gemalte Kreise, nicht in rt.vias)
    for (x, y, n) in rt.vias:
        add_via(board, nets, x, y, inv[n])
    u3 = args.u3

    # ---------- GND-Stitching im Kopf (Rand des Bandes und Antennen-Masskante)
    gnd = nid["GND"]
    vm = rt.via_mask(gnd, G.VIA_D / 2, hole_clr=0.25)
    cand = []
    for x in np.arange(-12.3, 12.31, 1.0):
        cand.append((x, 5.65))
    for y in np.arange(6.5, 20.4, 1.0):
        cand += [(-12.35, y), (12.35, y)]
    nst = 0
    for (x, y) in cand:
        j, i = rt.ij(x, y)
        if 0 <= j < rt.ny and 0 <= i < rt.nx and vm[j, i]:
            xx, yy = rt.xy(j, i)
            add_via(board, nets, xx, yy, "GND")
            rt.paint_via(xx, yy, G.VIA_D / 2, gnd)
            vm = rt.via_mask(gnd, G.VIA_D / 2, hole_clr=0.25)
            nst += 1
    print("Stitching-Vias:", nst)

    # ---------- Zonen
    band = G.board_poly(inset=G.EDGE_CLR, ymin=G.KEEPOUT_Y, ymax=G.BAND_Y1)
    for lay in ("F.Cu", "B.Cu"):
        add_zone(board, nets, lay, band, "GND", prio=0, clr=0.2, minw=0.2, name="GND_" + lay[0])
    # Innenlagen: drei GND-Zonen je Lage (Regeln greifen je Zone): Band, Schott/Fach (Kante >= 1.0, K-3; Polygon
    # 1.05, weil die gespeicherte Fuellung an Boegen sonst 0.998 mm ergibt und die Gerber daraus entstehen),
    # Kragen/Guard/G-Elektrode/Steg (Kante >= 1.25). Ueberlappung 0.05 mm verbindet die Zonen.
    band_in = G.board_poly(inset=G.EDGE_CLR, ymin=G.KEEPOUT_Y, ymax=G.BAND_Y1 - 0.02)
    fach = G.board_poly(inset=1.05, ymin=G.BAND_Y1 - 0.06, ymax=G.FACH_Y1 + 0.05)
    sonde = G.rect_poly(-G.ELEC_X, G.FACH_Y1, G.ELEC_X, G.GUARD_Y1)
    sonde.BooleanAdd(G.rect_poly(1.0, G.GUARD_Y1 - 0.01, G.ELEC_X, G.G_Y1))
    sonde.BooleanAdd(G.rect_poly(-G.ELEC_X, G.STEG_Y0, G.ELEC_X, G.G_Y1))
    sonde.Simplify()
    s_el = G.rect_poly(-G.ELEC_X, G.S_Y0, -1.0, G.S_Y1)
    for lay in ("In1.Cu", "In2.Cu"):
        k = lay[:3]
        # Band: In1 = GND-Bezugsflaeche (HF, Antenne), In2 = VDD-Flaeche
        add_zone(board, nets, lay, band_in, "GND" if lay == "In1.Cu" else "VDD", prio=0, clr=0.3 if lay == "In1.Cu"
                 else 0.25, minw=0.25, name=("GND_BAND_" if lay == "In1.Cu" else "VDD_BAND_") + k)
        add_zone(board, nets, lay, fach, "GND", prio=1, clr=0.3, minw=0.25, name="GND_FACH_" + k)
        add_zone(board, nets, lay, sonde, "GND", prio=2, clr=0.3, minw=0.25, name="GUARD_G_" + k)
        add_zone(board, nets, lay, s_el, "PROBE_SENSE", prio=3, clr=0.3, minw=0.25, name="S_" + k)

    # ---------- Regelflaechen (Keepouts + benannte Flaechen fuer .kicad_dru)
    cu_all = ["F.Cu", "In1.Cu", "In2.Cu", "B.Cu"]
    outer = ["F.Cu", "B.Cu"]
    a0 = PL.ANT_X - 3.05
    add_rule_area(board, "Z1_ANTENNE", G.rect_poly(-13.5, -0.5, 13.5, G.KEEPOUT_Y), cu_all, tracks=True, vias=True,
                  pour=True)
    add_rule_area(board, "Z3_SCHOTT", G.rect_poly(-13.5, G.SCHOTT_Y0, 13.5, G.SCHOTT_Y1), outer, tracks=True, pads=True,
                  vias=True, pour=True)
    add_rule_area(board, "Z4_FACH", G.rect_poly(-13.5, G.SCHOTT_Y1, 13.5, G.FACH_Y1), outer, tracks=True,
                  pour=True)
    # K-3 / LS-K1: Innenlagen >= 1.0 zur Kante in Schott, Fach und Kragen bis zum Dichtstreifen (Y 50.0)
    add_rule_area(board, "Z3_Z4_INNEN", G.rect_poly(-13.5, G.SCHOTT_Y0 + 0.02, 13.5, G.Z5B_Y1), cu_all)
    # Rev C: Pad-Rand >= 0.5 mm zu den Vergusskanten Schott (Y 22.70) und Kragen (Y 46.90) -> Sperrstreifen ohne Pads
    add_rule_area(board, "VERGUSS_SCHOTT_PADSPERRE", G.rect_poly(-13.5, G.VERGUSS_SCHOTT_Y - 0.5, 13.5,
                  G.VERGUSS_SCHOTT_Y + 0.5), outer, pads=True)
    add_rule_area(board, "VERGUSS_KRAGEN_PADSPERRE", G.rect_poly(-13.5, G.VERGUSS_KRAGEN_Y - 0.5, 13.5,
                  G.VERGUSS_KRAGEN_Y + 0.5), outer, pads=True)
    # Platinenanschlag der Kappe (Rev C Kap. 6): keine Bauteile, Kupfer erlaubt
    add_rule_area(board, "ANSCHLAG_KAPPE", G.rect_poly(*G.ANSCHLAG), outer, fps=True)
    for (x, y, n) in st["vip"]:
        add_rule_area(board, "VIP_FACH", G.rect_poly(x - 0.3, y - 0.3, x + 0.3, y + 0.3), cu_all)
    kragen = G.rect_poly(-11, G.FACH_Y1, 11, G.Z5A_Y1)
    if u3 == "kragen":
        fx0, fy0, fx1, fy1 = G.U3_FIELD
        kragen.BooleanSubtract(G.rect_poly(fx0, fy0, fx1, fy1))
        add_rule_area(board, "Z5B_FELD", G.rect_poly(fx0, fy0, fx1, fy1), cu_all)
    add_rule_area(board, "Z5_KRAGEN", kragen, outer, tracks=True, vias=True, pads=True, pour=True)
    add_rule_area(board, "Z5A_DICHT", G.rect_poly(-11, G.Z5B_Y1, 11, G.Z5A_Y1), cu_all)
    add_rule_area(board, "Z6_Z7_NASS", G.rect_poly(-11, G.Z5A_Y1, 11, 159.0), outer, tracks=True, vias=True, pads=True,
                  pour=True)
    add_rule_area(board, "Z5A_Z7_SONDE", G.rect_poly(-11, G.Z5B_Y1, 11, 159.0), cu_all, vias=True)

    # ---------- Silkscreen
    polys, s = logo_polys(os.path.join(G.ROOT, "docs/design/logo/fluidi_logo_v3a_mono.svg"), -8.0, 0, 10.0)
    ymin = min(y for p in polys for _, y in p)
    ymax = max(y for p in polys for _, y in p)
    dy = (54.3 + 57.9) / 2 - (ymin + ymax) / 2
    polys = [[(x, y + dy) for x, y in p] for p in polys]
    outers, holes = [], []
    for p in polys:
        inside = [k for k, q in enumerate(polys) if q is not p and point_in(p[0], q) and abs(poly_area(q)) > abs(poly_area(p))]
        if inside:
            holes.append((inside[0], p))
        else:
            outers.append(p)
    # Loecher den Aussenkonturen zuordnen
    out_idx = {id(p): k for k, p in enumerate(outers)}
    hole_list = [(out_idx[id(polys[i])], h) for i, h in holes]
    for k, o in enumerate(outers):   # eine Flaeche je Buchstabe (mehrere Aussenkonturen je Form werden nicht geplottet)
        silk_poly(board, [o], "F.SilkS", [(0, h) for (oi, h) in hole_list if oi == k])
    # Stecktiefe max z -5 (Y 58.5), F und B
    for lay, mir in (("F.SilkS", False), ("B.SilkS", True)):
        silk_line(board, (-9.0, 58.5), (9.0, 58.5), 0.2, lay)
        xs = 6.2 if not mir else -6.2
        silk_text(board, "max", xs, 59.9, 1.0, lay, thick=0.18, mirror=mir)
        ax = 8.3 if not mir else -8.3
        silk_poly(board, [[(ax - 0.5, 59.6), (ax + 0.5, 59.6), (ax, 58.75)]], lay)
        silk_line(board, (ax, 59.6), (ax, 60.6), 0.2, lay)
    silk_text(board, "fluidi rev " + REV, 0.0, 56.1, 1.5, "B.SilkS", thick=0.22, mirror=True)
    silk_text(board, "rev " + REV, 6.0, 56.1, 1.2, "F.SilkS", thick=0.18)
    # LS-K3 / S3-W4: Warnsymbol (Dreieck 9 x 8 mm mit "!") und Text auf B im Fach (x -8...8, Y 25.5...42.5)
    tri = [(-4.5, 34.0), (4.5, 34.0), (0.0, 26.0), (-4.5, 34.0)]
    for a, b in zip(tri[:-1], tri[1:]):
        silk_line(board, a, b, 0.4, "B.SilkS")
    silk_line(board, (0.0, 28.6), (0.0, 31.6), 0.6, "B.SilkS")
    silk_poly(board, [[(-0.35, 32.4), (0.35, 32.4), (0.35, 33.1), (-0.35, 33.1)]], "B.SilkS")
    silk_text(board, "CR2032", 0.0, 36.0, 1.5, "B.SilkS", thick=0.25, mirror=True)
    silk_text(board, "Verschluckgefahr", 0.0, 38.2, 1.2, "B.SilkS", thick=0.2, mirror=True, wf=0.8)
    silk_text(board, "keep away from children", 0.0, 40.2, 1.0, "B.SilkS", thick=0.17, mirror=True, wf=0.65)
    # DFM K-4 (Platzhalter JLC-Auftragsnummer) entfernt 2026-11-08: JLC "Order Number is not available since May 2026.
    # Please DO NOT add JLCJLCJLCJLC" (docs/references/JLCPCB_HowToMarkOnPCB_Auszug_2026-11-08.txt); Rev bleibt C.
    for tp, lab in (("TP1", "TX"), ("TP2", "RX")):
        x, y = [pcbnew.ToMM(v) for v in (fps[tp].GetPosition().x, fps[tp].GetPosition().y)]
        silk_text(board, lab, x - G.OX + 1.2, y - G.OY, 1.0, "F.SilkS", thick=0.15, just="left")
    for tp, lab in (("TP4", "CLK"), ("TP5", "S")):
        x, y = [pcbnew.ToMM(v) for v in (fps[tp].GetPosition().x, fps[tp].GetPosition().y)]
    # Elektrodenumrisse auf Fab/User (Dokumentation)
    for (x0, y0, x1, y1) in ((-G.ELEC_X, G.S_Y0, -1.0, G.S_Y1), (1.0, G.GUARD_Y1, G.ELEC_X, G.G_Y1)):
        for a, b in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
            silk_line(board, a, b, 0.1, "User.2")

    # ---------- Fuellen und speichern
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    out = args.out
    pcbnew.SaveBoard(out, board)
    postprocess(out)
    import pcb_rules
    pcb_rules.write(out[:-len(".kicad_pcb")] + ".kicad_dru")
    write_project(out)
    print("gespeichert:", out)
    st["out"] = out
    json.dump({"fails": st["fails"], "gnd_fanout_fail": st["gfail"], "tracks": len(rt.segments),
               "vias": len(rt.vias)}, open(os.path.join(G.ROOT, "hardware/sensor/out/route_status.json"), "w"), indent=1)
    if args.plot:
        G.plot_band(fps, rt, args.plot, "Routing")


STACKUP = """\t\t(stackup
\t\t\t(layer "F.SilkS" (type "Top Silk Screen"))
\t\t\t(layer "F.Paste" (type "Top Solder Paste"))
\t\t\t(layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
\t\t\t(layer "F.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "dielectric 1" (type "prepreg") (thickness 0.2104) (material "FR4 7628") (epsilon_r 4.4) (loss_tangent 0.02))
\t\t\t(layer "In1.Cu" (type "copper") (thickness 0.0152))
\t\t\t(layer "dielectric 2" (type "core") (thickness 1.065) (material "FR4") (epsilon_r 4.5) (loss_tangent 0.02))
\t\t\t(layer "In2.Cu" (type "copper") (thickness 0.0152))
\t\t\t(layer "dielectric 3" (type "prepreg") (thickness 0.2104) (material "FR4 7628") (epsilon_r 4.4) (loss_tangent 0.02))
\t\t\t(layer "B.Cu" (type "copper") (thickness 0.035))
\t\t\t(layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
\t\t\t(layer "B.Paste" (type "Bottom Solder Paste"))
\t\t\t(layer "B.SilkS" (type "Bottom Silk Screen"))
\t\t\t(copper_finish "ENIG")
\t\t\t(dielectric_constraints no)
\t\t)
"""


def postprocess(path):
    s = open(path).read()
    if "(stackup" not in s:
        s = s.replace("\t(setup\n", "\t(setup\n" + STACKUP, 1)
    s = re.sub(r'\(paper "[^"]*"( portrait)?\)', '(paper "A4" portrait)', s, 1)
    open(path, "w").write(s)


def write_project(pcb_path):
    pro = pcb_path[:-len(".kicad_pcb")] + ".kicad_pro"
    d = json.load(open(pro)) if os.path.exists(pro) else {}
    board = d.setdefault("board", {})
    dset = board.setdefault("design_settings", {})
    dset["rules"] = {
        "min_clearance": 0.1, "min_connection": 0.0, "min_copper_edge_clearance": G.EDGE_CLR,
        "min_hole_clearance": 0.2, "min_hole_to_hole": 0.25, "min_microvia_diameter": 0.2,
        "min_microvia_drill": 0.1, "min_resolved_spokes": 1, "min_silk_clearance": 0.0,
        "min_text_height": 1.0, "min_text_thickness": 0.15, "min_through_hole_diameter": 0.2,
        "min_track_width": 0.1, "min_via_annular_width": 0.075, "min_via_diameter": 0.45,
        "solder_mask_to_copper_clearance": 0.0, "use_height_for_length_calcs": True}
    dset["track_widths"] = [0.0, G.TW_SIG, G.TW_PWR, 0.3, G.TW_RF]
    dset["via_dimensions"] = [{"diameter": 0.0, "drill": 0.0}, {"diameter": G.VIA_D, "drill": G.VIA_DRILL}]
    d["net_settings"] = {
        "classes": [{"name": "Default", "clearance": 0.1, "track_width": G.TW_SIG, "via_diameter": G.VIA_D,
                     "via_drill": G.VIA_DRILL, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                     "diff_pair_width": 0.2, "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "wire_width": 6,
                     "bus_width": 12, "line_style": 0, "pcb_color": "rgba(0, 0, 0, 0.000)",
                     "schematic_color": "rgba(0, 0, 0, 0.000)", "priority": 2147483647}],
        "meta": {"version": 4}, "net_colors": None, "netclass_assignments": None, "netclass_patterns": []}
    json.dump(d, open(pro, "w"), indent=2)
