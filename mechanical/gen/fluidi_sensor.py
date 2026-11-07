# -*- coding: utf-8 -*-
"""fluidi Sensor P3 "Stele" - parametrisches Fertigungs-CAD (Phase 4b, Welle 2: Kopf V4, Schnittstelle Rev B),
FreeCAD 0.21.2 headless.

Rev B (D-019): Kopf 34 x 13 x 57.5, Kappe 14 mm, Sichtfuge z 43.5. Die graue Huelse ist oberhalb des Zapfen-O-Rings nur
Sichtschale ueber dem dichten Kern (Kappe + Zapfen + Schott). Wasser, das an der Sichtfuge/Tropfenkerbe eindringt,
laeuft im Spalt 0.7 mm auf eine nach hinten geneigte Stufe und durch 4 Schlitze in der Huelsenrueckwand ab.
Kragen mit Tasche fuer U3 TMP1075N (Option f), Platine 26 mm im Kopf, 20 mm in der Sonde.

Konstruktion A1 (Kern + Huelse, M2 von unten) nach docs/reviews/phase3_sleeve_mechanik.md, ueberarbeitet:
  - beide Dichtungen radial, gleicher O-Ring AS568-017 (S3-W3), Dachziegel-Fuge (Kappe ueberlappt Huelse 1.4 mm)
  - Platine einseitig bestueckt (F zum Fenster), Clip 3034 gedreht (S-01), Mutter M2 vor der F-Seite im Kragen
  - Taste oben: Silikonmembran (Dichtung) -> Stoessel -> 30-Grad-Keil -> Biegezunge der Kappe -> TS-1187A
  - Tropfenfenster transluzent mit Lichtschaft (d = 2.0 mm zur LED), Klebefuge >= 1 mm ueber der O-Ring-Nut
Alle Masse: mechanical/gen/fluidi_params.py (Schnittstelle docs/interfaces/PCB_OUTLINE.md, Rev C).
Rev C: Anschlag + Gabel fuer die Platinenoberkante in der Kappe (Lage in z), Clip 3034 nach Datenblatt (B 7.4),
Antenne an der Layout-Lage. Pruefung mit dem KiCad-STEP: fluidi_pcb_collision.py -> collision_pcb_step.txt.
V-K (D-023): Huelsenboden 1.3, Kragen/Tasche/Mutter/O-Ring-Nut 0.7 tiefer, Fach 24.2, Distanzlehre 24.2, Schraube M2x3.
M-4 (D-023): Tastenhub 0.8, Zunge 0.25 vor SW1, F-Referenz an Gabel und Schottkeil, Quetschrippen (Gabel + Schott).

Lauf:  freecadcmd mechanical/gen/fluidi_sensor.py
Ausgabe: mechanical/sensor/fluidi_sensor.FCStd, fluidi_sensor_assembly.step, print/<Teil>.{step,stl,3mf},
         mechanical/sensor/check_sensor.txt (Pruefprotokoll), mechanical/sensor/collision_placeholder.txt
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import FreeCAD as App
import Part

import fluidi_params as FP
from fluidi_cadlib import (V, prism, prism_xz, box, cyl, cyl_y, plan, rrect, rrect_perimeter, drop2, hexagon,
                           logo_solid, text_solid, collide, export_part)

H, PCB, Z, CAP, BTN = FP.HEAD, FP.PCB, FP.Z, FP.CAP, FP.BTN
OUT = os.path.join(FP.REPO, 'mechanical', 'sensor')
LOG = []
RIBS = {}          # Quetschrippen (M-4): werden beim Einbau gequetscht -> in den Kollisionspruefungen getrennt ausgewiesen


def prism_yz(poly_yz, x0, x1):
    """Polygon in der y-z-Ebene, extrudiert in x von x0 nach x1."""
    pts = [V(x0, y, z) for y, z in poly_yz] + [V(x0, poly_yz[0][0], poly_yz[0][1])]
    return Part.Face(Part.makePolygon(pts)).extrude(V(x1 - x0, 0, 0))


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    LOG.append(s)


def P(off=0.0):
    return plan(H['W'], H['D'], H['CF'], H['CB'], off)


def above_step():
    """Halbraum oberhalb der Ablaufebene: z = STEP_FRONT bei y = 0, STEP_BACK bei y = D (nach hinten fallend)."""
    zf, zb, d = Z['STEP_FRONT'], Z['STEP_BACK'], H['D']
    k = (zb - zf) / d
    pts = [V(-30, -5, zf - 5 * k), V(-30, d + 5, zb + 5 * k), V(-30, d + 5, 80), V(-30, -5, 80), V(-30, -5, zf - 5 * k)]
    return Part.Face(Part.makePolygon(pts)).extrude(V(60, 0, 0))


def build():
    S = {}
    # ------------------------------------------------------------------ Leiterplatte (Platzhalter-Volumenmodell)
    out = FP.outline()
    pcb = prism_xz(out, PCB['Y_F'], PCB['Y_B'])
    S['PCB'] = pcb
    # Antennenkupfer (F, Lage laut Layout Rev B: Texas_SWRA117D_2.4GHz_Right, x -2.2 ... 12.2)
    A_ = FP.ANT
    S['Antenne_AN043'] = box(A_['X0'], A_['X1'], PCB['Y_F'] - 0.035, PCB['Y_F'], A_['Z0'], A_['Z1'])
    # Bauteil-Huelle Elektronikband F: <= 2.0 mm, unter der Biegezunge <= 1.5 mm (Schnittstelle Z2_BAND_F)
    T = FP.TONGUE
    yb = PCB['Y_F']
    h2 = PCB['W_HEAD'] / 2
    h2 -= PCB['EDGE_CLR']                                              # Courtyards >= 0.3 von der Kontur
    S['Band_Huelle_F'] = box(-h2, h2, yb - 2.0, yb, Z['BAND0'], Z['BAND1'])     # Rev B: ueberall <= 2.0
    S['D1_LED'] = box(FP.LED['X'] - FP.LED['LX'] / 2, FP.LED['X'] + FP.LED['LX'] / 2, yb - FP.LED['H'], yb,
                      FP.LED['Z'] - FP.LED['LZ'] / 2, FP.LED['Z'] + FP.LED['LZ'] / 2)
    sw = FP.SW
    S['SW1_Taster'] = box(sw['X'] - sw['BODY_X'] / 2, sw['X'] + sw['BODY_X'] / 2, yb - sw['H'], yb,
                          sw['Z'] - sw['BODY_Z'] / 2, sw['Z'] + sw['BODY_Z'] / 2)
    tm = FP.TMP
    S['U3_TMP_Kragen'] = box(tm['X0'], tm['X1'], yb - tm['H'], yb, tm['Z0'], tm['Z1'])
    # Clip + Zelle (F-Seite, gedreht: geschlossenes Ende -x, Ausschub +x)
    c = FP.CLIP
    cell = cyl_y(FP.CELL['D'] / 2, yb - 0.1 - FP.CELL['T'], yb - 0.1, FP.CELL['XC'], Z['CELL_C'])
    clip = box(c['X0'], c['X1'], yb - c['H'], yb, Z['CLIP0'], Z['CLIP1']).cut(cell)   # Huelle nach Datenblatt (L, W, H, B)
    S['CR2032'] = cell
    S['Keystone3034'] = clip

    # ------------------------------------------------------------------ Kragen (Vergussform, Kern)
    L, G = FP.LAND, FP.GROOVE_BOT
    col = rrect(L, Z['COL0'], Z['COL1'])
    col = col.cut(rrect(L, Z['COL_G0'], Z['COL_G1'], grow=0.5).cut(rrect(G, Z['COL_G0'] - 1, Z['COL_G1'] + 1)))
    xs, ys0, ys1 = PCB['W'] / 2 + 0.15, PCB['Y_F'] - 0.15, PCB['Y_B'] + 0.15
    col = col.cut(box(-xs, xs, ys0, ys1, Z['COL0'] - 1, Z['COL1'] + 1))
    # Tasche fuer U3 + C24 vor F (Option f), unten offen -> Verguss kopfueber entlueftet
    kp = FP.KPOCKET
    pocket = box(kp['X0'], kp['X1'], PCB['Y_F'] - kp['DEPTH'], ys0 + 0.01, kp['Z0'] - 1, kp['Z1'])
    col = col.cut(pocket)
    sc = FP.SCREW
    # Mutter seitlich von vorne eingeschoben (Tasche unterhalb der O-Ring-Nut, offen zur nassen Seite, vergossen)
    rc = (sc['NUT_S'] + 0.1) / 2 / math.cos(math.pi / 6)
    col = col.cut(prism(hexagon(sc['NUT_S'] + 0.1, sc['X'], sc['Y']), Z['COL_NUT0'], Z['COL_NUT1'] + 0.05))
    col = col.cut(box(sc['X'] - rc, sc['X'] + rc, 0.0, sc['Y'], Z['COL_NUT0'], Z['COL_NUT1'] + 0.05))
    col = col.cut(cyl(sc['HOLE_D'] / 2, Z['COL0'] - 1, Z['COL_NUT0'] + 0.01, sc['X'], sc['Y']))
    col = col.cut(cyl(sc['D'] / 2 + 0.2, Z['COL_NUT1'], sc['L'] + 0.3, sc['X'], sc['Y']))   # Freiraum Schraubenspitze
    # Hohlkehle fuer den Verguss an der Unterkante (Kerbwirkung, FEM): 0.8 x 45 Grad um den Schlitz
    ch = 0.6
    w0 = Part.makePolygon([V(-xs - ch, ys0 - ch, Z['COL0']), V(xs + ch, ys0 - ch, Z['COL0']), V(xs + ch, ys1 + ch, Z['COL0']),
                           V(-xs - ch, ys1 + ch, Z['COL0']), V(-xs - ch, ys0 - ch, Z['COL0'])])
    w1 = Part.makePolygon([V(-xs, ys0, Z['COL0'] + ch), V(xs, ys0, Z['COL0'] + ch), V(xs, ys1, Z['COL0'] + ch),
                           V(-xs, ys1, Z['COL0'] + ch), V(-xs, ys0, Z['COL0'] + ch)])
    col = col.cut(Part.makeLoft([w0, w1], True))
    S['Kragen'] = col
    nut = prism(hexagon(sc['NUT_S'], sc['X'], sc['Y']), Z['COL_NUT0'], Z['COL_NUT1']).cut(
        cyl(sc['D'] / 2 * 0.8, Z['COL_NUT0'] - 1, Z['COL_NUT1'] + 1, sc['X'], sc['Y']))
    S['Mutter_M2'] = nut
    # Verguss Kragen (Epoxid): Spalt + Hohlkehle, ohne Platine
    vk = box(-xs, xs, ys0, ys1, Z['COL0'], Z['COL1'])
    vk = vk.fuse(Part.makeLoft([w0, w1], True)).fuse(pocket.common(box(-20, 20, -5, 20, Z['COL0'], Z['COL1'])))
    vk = vk.cut(pcb).cut(S['U3_TMP_Kragen'])
    S['Verguss_Kragen'] = vk.removeSplitter()

    # ------------------------------------------------------------------ Schraube M2x4 (unverlierbar)
    scr = cyl(sc['HEAD_D'] / 2, -sc['HEAD_H'], 0.0, sc['X'], sc['Y']).fuse(cyl(sc['D'] / 2, 0.0, sc['L'], sc['X'], sc['Y']))
    S['Schraube_M2'] = scr

    # ------------------------------------------------------------------ O-Ringe (verpresst: radial = Einbauraum)
    SI = FP.SLEEVE_IN
    def oring(z0, z1):
        zc = (z0 + z1) / 2
        return rrect(SI, zc - 0.95, zc + 0.95).cut(rrect(G, zc - 2, zc + 2))
    S['ORing_Kragen'] = oring(Z['COL_G0'], Z['COL_G1'])
    S['ORing_Zapfen'] = oring(Z['SP_G0'], Z['SP_G1'])

    # ------------------------------------------------------------------ Kappe blau (Kern) mit Schott, Zunge
    cap = prism(P(0), H['Z_FUGE'], H['H'])
    top_edges = [e for e in cap.Edges if all(abs(v.Point.z - H['H']) < 1e-6 for v in e.Vertexes)]
    cap = cap.makeChamfer(H['TOP_CH'], top_edges)
    cap = cap.fuse(rrect(L, Z['BULK0'], H['SLOT_TOP'] + 0.01)).removeSplitter()
    # Ablaufstufe: Zapfen oberhalb einer nach hinten geneigten Ebene um RECESS zurueckgesetzt (Spalt 0.7 zur Huelse)
    rec = rrect(L, Z['STEP_BACK'] - 0.5, H['SLOT_TOP']).cut(rrect(L, Z['STEP_BACK'] - 1, H['SLOT_TOP'] + 1, grow=-CAP['RECESS']))
    cap = cap.cut(rec.common(above_step()))
    # Dachziegel-Schlitz fuer den Huelsenrand (aussen Schuerze 0.8, innen Zapfen)
    cap = cap.cut(prism(P(H['SKIRT_T']), H['Z_FUGE'] - 0.5, H['SLOT_TOP']).cut(rrect(L, H['Z_FUGE'] - 1, H['SLOT_TOP'] + 1)))
    # O-Ring-Nut im Zapfen
    cap = cap.cut(rrect(L, Z['SP_G0'], Z['SP_G1'], grow=0.5).cut(rrect(G, Z['SP_G0'] - 1, Z['SP_G1'] + 1)))
    # Innenraum (Elektronikraum)
    cap = cap.cut(rrect(FP.SP_IN, Z['BULK1'], H['SLOT_TOP'] + 0.01))
    T_ = FP.TONGUE                                                    # Tasche fuer die Zungenspitze im Zapfen
    cap = cap.cut(box(T_['COL_X0'], T_['COL_X1'], T_['Y0'] - 0.3, FP.SP_IN['Y0'] + 0.1, T_['Z_TIP'] - 1.0, H['SLOT_TOP'] + 0.01))
    cap = cap.cut(prism(P(CAP['CAV_OFF']), H['SLOT_TOP'], H['H'] - H['CEIL']))
    bs = CAP['BULK_SLOT']
    cap = cap.cut(box(-bs['X'], bs['X'], bs['Y0'], bs['Y1'], Z['BULK0'] - 1, Z['BULK1'] + 0.01))
    # Tropfenfenster-Ausschnitt und Lichtschaft-Bohrung
    D = FP.DROP
    dpoly = drop2(D['X'], D['ZC'], D['R'], D['K'])
    cap = cap.cut(prism_xz(dpoly, -1.0, D['T']))
    cap = cap.cut(cyl_y(D['BOSS_D'] / 2 + D['GLUE'], D['T'] - 0.1, D['BOSS_Y1'] + 0.5, D['X'], D['ZC']))
    # Tastenblock, Fuehrungsrohr, Biegezunge (alles einteilig mit der Kappe; Druck kopfueber)
    ax, ay = BTN['AX_X'], BTN['AX_Y']
    blk = box(-8.0, 0.8, CAP['CAV_OFF'], PCB['Y_F'] - 0.4, BTN['BLOCK_Z0'], H['H'] - H['CEIL'] + 0.01)
    blk = blk.fuse(box(-8.0, 0.8, CAP['CAV_OFF'], PCB['Y_B'] + 0.6, BTN['BLOCK_Z0'] + 0.3, H['H'] - H['CEIL'] + 0.01))  # 0.7 ueber Oberkante
    blk = blk.fuse(cyl(BTN['TUBE_OD'] / 2, BTN['TUBE_Z0'], BTN['BLOCK_Z0'] + 0.01, ax, ay))
    tg = box(FP.TONGUE['X0'], FP.TONGUE['X1'], FP.TONGUE['Y0'], FP.TONGUE['Y1'], FP.TONGUE['Z_TIP'], BTN['BLOCK_Z0'] + 0.01)
    # Rev C: Anschlag + Gabel fuer die Platinenoberkante (links der Antenne), definiert die Lage der Platine in z und y.
    # M-4: vordere Wange = F-Referenz (Luft 0, Einlauffase), hintere Wange mit Quetschrippe (drueckt F an die vordere Wange)
    ps = FP.PSTOP
    yf0, yb1 = PCB['Y_F'] - ps['CLR_F'], PCB['Y_B'] + ps['CLR_B']
    zb, zt = PCB['Z_TOP'] - ps['FORK'], PCB['Z_TOP'] + 0.01
    stop = box(ps['X0'], ps['X1'], yf0 - ps['T'], yb1 + ps['T'], PCB['Z_TOP'], BTN['BLOCK_Z0'] + 0.31)
    stop = stop.fuse(prism_yz([(yf0 - ps['T'], zb), (yf0 - ps['LEAD'], zb), (yf0, zb + ps['LEAD']), (yf0, zt),
                               (yf0 - ps['T'], zt)], ps['X0'], ps['X1']))
    stop = stop.fuse(box(ps['X0'], ps['X1'], yb1, yb1 + ps['T'], zb, zt))
    xr = (ps['X0'] + ps['X1']) / 2
    rib_f = prism_yz([(yb1 + 0.01, zb), (yb1 + 0.01, zt), (ps['RIB_Y'], zt), (ps['RIB_Y'], zb + 0.5)],
                     xr - ps['RIB_W'] / 2, xr + ps['RIB_W'] / 2)
    # Quetschrippen an der Rueckwand des Schottschlitzes (y 8.4 -> 7.95), Einlauffase unten
    bs = CAP['BULK_SLOT']
    rib_s = [prism_yz([(bs['Y1'] + 0.01, Z['BULK0']), (bs['Y1'] + 0.01, Z['BULK1']), (bs['Y1'] - CAP['RIB_H'], Z['BULK1']),
                       (bs['Y1'] - CAP['RIB_H'], Z['BULK0'] + CAP['RIB_H'])], xc - CAP['RIB_W'] / 2, xc + CAP['RIB_W'] / 2)
             for xc in CAP['RIB_X']]
    cap = cap.fuse(blk).fuse(tg).fuse(stop).removeSplitter()
    # Tastentasche (sichtbar 9.8 x 6.8), Senkung fuer Membran + Klemmring, Bohrung Stoessel
    btn_poly = [(x + BTN['X'], y + BTN['Y']) for x, y in plan(BTN['W'], BTN['D'], BTN['CH'], BTN['CH'], 0.0)]
    btn_poly = [(x, y - BTN['D'] / 2) for x, y in btn_poly]
    pocket = [(x + BTN['X'], y + BTN['Y'] - (BTN['D'] + 2 * BTN['POCKET_GAP']) / 2)
              for x, y in plan(BTN['W'] + 2 * BTN['POCKET_GAP'], BTN['D'] + 2 * BTN['POCKET_GAP'], BTN['CH'], BTN['CH'], 0.0)]
    z_pf = H['H'] - BTN['POCKET_D']                                  # Taschenboden 56.5
    cap = cap.cut(prism(pocket, z_pf, H['H'] + 1))
    z_cb = z_pf - 2.3                                                # Senkungsgrund 54.2
    cap = cap.cut(cyl(BTN['CB_D'] / 2, z_cb, z_pf + 0.01, ax, ay))
    cap = cap.cut(cyl(BTN['BORE_D'] / 2, BTN['TUBE_Z0'] - 1, z_cb + 0.01, ax, ay))
    RIBS['Kappe_ohne_Rippen'] = cap
    ribs = rib_f.fuse(rib_s[0]).fuse(rib_s[1])
    RIBS['Rippen'] = ribs
    cap = cap.fuse(ribs).removeSplitter()
    S['Kappe_blau'] = cap
    # Schottkeil (fuellt den vorderen Durchfuehrungsspalt nach dem Einschieben); M-4: Rueckseite = F-Referenz
    kc = CAP['KEIL_CLR']
    S['Schottkeil'] = box(-bs['X'] + kc, bs['X'] - kc, bs['Y0'] + kc, PCB['Y_F'] - CAP['KEIL_REAR'], Z['BULK0'], Z['BULK1'])
    S['Verguss_Schott'] = box(-bs['X'], bs['X'], bs['Y0'], bs['Y1'], Z['BULK0'], Z['BULK1']).cut(pcb).cut(S['Schottkeil']).cut(ribs)

    # ------------------------------------------------------------------ Taste, Membran, Klemmring, Stoessel
    z_m0, z_m1 = z_cb, z_cb + BTN['MEMB_T']
    S['Membran_Silikon'] = cyl(BTN['CB_D'] / 2 - 0.02, z_m0, z_m1, ax, ay)
    ring = cyl(BTN['CB_D'] / 2 - 0.05, z_m1 + 1.0, z_pf, ax, ay).cut(cyl(BTN['RING_ID'] / 2, z_m1, z_pf + 1, ax, ay))
    ring = ring.fuse(cyl(BTN['CB_D'] / 2 - 0.05, z_m1, z_m1 + 1.0, ax, ay).cut(cyl(BTN['SKIRT_ID'] / 2, z_m1 - 1, z_m1 + 2, ax, ay)))
    S['Klemmring'] = ring.removeSplitter()
    z_bt0 = z_pf + BTN['STROKE']                                     # Taste unten in Ruhe
    taste = prism(btn_poly, z_bt0, H['H'] + BTN['PROUD'])
    taste = taste.fuse(cyl(BTN['NECK_D'] / 2, z_m1 + 0.05, z_bt0 + 0.01, ax, ay)).removeSplitter()
    S['Taste_blau'] = taste
    z_w1 = z_m1 + 1.0                                                # Teller liegt in Ruhe am Ring an
    S['Tastenteller'] = cyl(BTN['WASHER_D'] / 2, z_w1 - BTN['WASHER_T'], z_w1, ax, ay).cut(
        cyl(BTN['NECK_D'] / 2, z_w1 - 1, z_w1 + 1, ax, ay))
    st = cyl(BTN['STEM_D'] / 2, BTN['TUBE_Z0'], z_m0 - 0.05, ax, ay).common(box(-20, 20, ay - 1.0, 20, 0, 80))  # D-Profil
    fy1 = FP.TONGUE['Y0'] - FP.TONGUE['WEDGE_GAP']
    fy0 = fy1 - 1.15
    st = st.fuse(box(-5.8, ax, fy0, fy1, BTN['TUBE_Z0'] - 0.8, BTN['TUBE_Z0']))       # Arm
    st = st.fuse(box(-5.8, -4.6, fy0, fy1, FP.TONGUE['Z_CONTACT'] - 0.4, BTN['TUBE_Z0'] - 0.8 + 0.01))  # Finger mit Keil (30 Grad)
    S['Stoessel'] = st.removeSplitter()

    # ------------------------------------------------------------------ Tropfenfenster transluzent
    win = prism_xz(drop2(D['X'], D['ZC'], D['R'] - D['GLUE'], D['K'] * D['R'] / (D['R'] - D['GLUE'])), 0.0, D['T'])
    win = win.fuse(cyl_y(D['BOSS_D'] / 2, D['T'] - 0.01, D['BOSS_Y1'], D['X'], D['ZC'])).removeSplitter()
    S['Fenster_transluzent'] = win

    # ------------------------------------------------------------------ Huelse grau
    sl = prism(P(0), 0.0, Z['SLEEVE_TOP']).fuse(prism(P(H['SKIRT_T'] + 0.1), Z['SLEEVE_TOP'] - 0.01, H['RIM_TOP']))
    sl = sl.removeSplitter().cut(rrect(SI, H['FLOOR'], H['RIM_TOP'] + 1))
    slot = FP.SLOT
    sl = sl.cut(box(-slot['X'], slot['X'], slot['Y0'], slot['Y1'], -1, H['FLOOR'] + 1))
    sl = sl.cut(cyl(sc['HOLE_D'] / 2, sc['LIP_H'], H['FLOOR'] + 1, sc['X'], sc['Y']))
    sl = sl.cut(cyl(sc['LIP_D'] / 2, -1, sc['LIP_H'] + 0.01, sc['X'], sc['Y']))           # Furchlippe (unverlierbar)
    g = D['NOTCH_GAP']
    notch = prism_xz(drop2(D['X'], D['ZC'], D['R'] + g, (D['K'] * D['R'] + g) / (D['R'] + g)), -1, SI['Y0'] + 0.3)
    notch = notch.fuse(box(D['X'] - D['R'] - g, D['X'] + D['R'] + g, -1, SI['Y0'] + 0.3, D['ZC'], H['RIM_TOP'] + 1))
    sl = sl.cut(notch)
    # Ablaufschlitze in der Rueckwand, Unterkante = tiefster Punkt der Ablaufstufe
    dr = FP.DRAIN
    for xc in dr['XC']:
        sl = sl.cut(box(xc - dr['W'] / 2, xc + dr['W'] / 2, SI['Y1'] - 0.5, H['D'] + 1, Z['STEP_BACK'], Z['STEP_BACK'] + dr['H']))
    sl_plain = sl.copy()
    # Logo-Relief Ton in Ton (Wortmarke v3a mono), 16 mm, 0.25 mm erhaben
    lg, s_logo = logo_solid(os.path.join(FP.REPO, FP.LOGO['SVG']), FP.LOGO['W'], 0.0, FP.LOGO['ZC'], 0.0, FP.LOGO['RELIEF'])
    sl = sl.fuse(lg)
    # Warnsymbol innen an der Rueckwand, vertieft 0.3 mm (S3-W4)
    W_ = FP.WARN
    yi = SI['Y1']
    zc = W_['ZC'] + 4.0
    tri = [(-W_['TRI_W'] / 2, zc - W_['TRI_H'] / 2), (W_['TRI_W'] / 2, zc - W_['TRI_H'] / 2), (0, zc + W_['TRI_H'] / 2)]
    tin = [(-W_['TRI_W'] / 2 + 1.55, zc - W_['TRI_H'] / 2 + 0.8), (W_['TRI_W'] / 2 - 1.55, zc - W_['TRI_H'] / 2 + 0.8),
           (0, zc + W_['TRI_H'] / 2 - 1.75)]
    wcut = prism_xz(tri, yi - 0.1, yi + W_['DEPTH']).cut(prism_xz(tin, yi - 1, yi + 1))
    wcut = wcut.fuse(text_solid('!', 4.2, 0.0, zc - 3.6, yi - 0.1, yi + W_['DEPTH']))
    wcut = wcut.fuse(text_solid('CR2032', 2.0, 0.0, zc - 7.6, yi - 0.1, yi + W_['DEPTH']))
    wcut = wcut.fuse(text_solid('Verschluckgefahr', 1.4, 0.0, zc - 10.0, yi - 0.1, yi + W_['DEPTH']))
    sl = sl.cut(wcut)
    S['Huelse_grau'] = sl
    return S, sl_plain, s_logo


def checks(S, sl_plain):
    log('=== fluidi Sensor P3, Schnittstelle Rev %s (%s) ===' % (FP.REV, FP.REV_DATE))
    allowed = {('PCB', 'Antenne_AN043'), ('Band_Huelle_F', 'D1_LED'), ('Band_Huelle_F', 'SW1_Taster'),
               ('Keystone3034', 'CR2032'),
               ('Mutter_M2', 'Schraube_M2'),       # Gewindeeingriff (Nennmass-Zylinder)
               ('Schraube_M2', 'Huelse_grau'),
               ('Mutter_M2', 'Verguss_Kragen'),
               ('Band_Huelle_F', 'U3_TMP_Kragen'),        # Mutter eingegossen, Furchlippe Ø1.7 im Boden (unverlierbar)
               ('PCB', 'Kappe_blau')}                    # Quetschrippen (M-4), unten getrennt geprueft
    log('1 Kollisionen montiert (Ruhe):')
    hits = collide(S, allowed)
    log('  -> %s' % ('keine' if not hits else '%d Kollisionen' % len(hits)))
    for a, b, v in hits:
        log('     %s / %s %.4f mm3' % (a, b, v))
    v_rest = S['PCB'].common(RIBS['Kappe_ohne_Rippen']).Volume
    v_rib = S['PCB'].common(RIBS['Rippen']).Volume
    log('   Platine / Kappe: ohne Quetschrippen %.4f mm3; Rippen-Ueberdeckung %.3f mm3 (gewollt, 3 Rippen, Dicke 1.6: je '
        '%.2f mm gequetscht)' % (v_rest, v_rib, PCB['Y_B'] - FP.PSTOP['RIB_Y']))
    # 2 Taste gedrueckt: Taste/Teller/Stoessel um Hub nach unten, Membran nicht modelliert (elastisch)
    st = BTN['STROKE']
    zg = (PCB['Y_F'] - FP.SW['H']) - FP.TONGUE['Y1']
    moved = {}
    for k in ('Taste_blau', 'Tastenteller', 'Stoessel'):
        m = S[k].copy(); m.translate(V(0, 0, -st)); moved[k] = m
    fixed = {k: S[k] for k in S if k not in moved and k not in ('Membran_Silikon',)}
    hits2 = []
    for a, A in moved.items():
        for b, B in fixed.items():
            if A.BoundBox.intersect(B.BoundBox):
                v = A.common(B).Volume
                if v > 1e-3:
                    hits2.append((a, b, v))
    log('2 Taste gedrueckt (Hub %.1f): Ueberdeckungen %s' % (st, ', '.join('%s/%s %.3f' % h for h in hits2) or 'keine'))
    T = FP.TONGUE
    lat = st * math.tan(math.radians(30)) - T['WEDGE_GAP']          # netto seitlich nach Schliessen des Vorspalts
    a = BTN['BLOCK_Z0'] - T['Z_CONTACT']
    xs = BTN['BLOCK_Z0'] - FP.SW['Z']
    ratio = 1 + 1.5 * (xs - a) / a
    log('   Keil 30 Grad: seitlicher Netto-Weg an der Zunge %.2f mm -> am Betaetiger x%.2f = %.2f mm; '
        'noetig %.2f (Spalt %.2f + Hub %.2f)' % (lat, ratio, lat * ratio, zg + FP.SW['TRAVEL'], zg, FP.SW['TRAVEL']))
    log('   Zunge-Taster Spalt in Ruhe: %.2f mm; Keil-Vorspalt %.2f mm' % (zg, T['WEDGE_GAP']))
    # 2b Toleranzkette M-4: F liegt an Keil-Rueckseite und vorderer Gabelwange (Quetschrippen dahinter), F +-0.1 (FDM);
    #    Tasterhoehe 2.0 +-0.1 (XUNPU S.1, Allgemeintoleranz), Zunge +-0.1 (FDM), Keilvorspalt +-0.1 (FDM, wirkt x Hebel),
    #    Tasterhub bis Schaltpunkt 0.2 +-0.1 (XUNPU S.1)
    have = lat * ratio
    need = zg + FP.SW['TRAVEL']
    res = have - need
    rss = math.sqrt(3 * 0.1 ** 2 + (0.1 * ratio) ** 2 + 0.1 ** 2)
    wc = 3 * 0.1 + 0.1 * ratio + 0.1
    log('2b Toleranzkette Taster (M-4): Weg am Betaetiger %.2f, noetig %.2f (Spalt %.2f + Hub %.2f) -> Reserve nominal %.2f; '
        'Toleranz F/H/Zunge je +-0.1, Keilvorspalt +-0.1 (x%.2f), Hub +-0.1: RSS +-%.2f -> Reserve %.2f (>= 0), worst +-%.2f -> %.2f'
        % (have, need, zg, FP.SW['TRAVEL'], res, ratio, rss, res - rss, wc, res - wc))
    g_min = zg - 3 * 0.1
    log('   Spalt in Ruhe nominal %.2f, worst min %.2f, RSS min %.2f mm (Vorspannung < Mindesthub 0.1 -> kein Dauerbetaetigen); '
        'Ueberhub nach Schaltpunkt nominal %.2f mm (Finger biegt aus, PROTOTYP-PRUEFUNG)'
        % (zg, g_min, zg - math.sqrt(3) * 0.1, res))
    # 3 Huelse abziehen (vereinfacht ohne Logo/Text), O-Ringe gleiten (nicht geprueft)
    kern = ['PCB', 'Kragen', 'CR2032', 'Keystone3034', 'Kappe_blau', 'Mutter_M2', 'Fenster_transluzent',
            'Verguss_Kragen', 'Band_Huelle_F', 'U3_TMP_Kragen']
    first = None
    for d in range(1, 161):
        m = sl_plain.copy(); m.translate(V(0, 0, -d))
        for k in kern:
            if m.BoundBox.intersect(S[k].BoundBox) and m.common(S[k]).Volume > 1e-3:
                first = (d, k); break
        if first:
            break
    log('3 Huelse 160 mm nach unten ueber die Sonde abziehen: %s' % ('frei' if not first else 'Kollision bei %d mm mit %s' % first))
    # 4 Zelle seitlich +x
    blk = None
    for d in range(1, 26):
        c = S['CR2032'].copy(); c.translate(V(d, 0, 0))
        for k in ('Kragen', 'Kappe_blau', 'Mutter_M2', 'Band_Huelle_F', 'Verguss_Kragen', 'Schottkeil'):
            if c.common(S[k]).Volume > 1e-3:
                blk = (d, k); break
        if blk:
            break
    log('4 Zelle seitlich 25 mm (+x) herausschieben (ohne Huelse): %s' % ('frei' if not blk else 'blockiert bei %d mm (%s)' % blk))
    c = S['CR2032'].copy(); c.translate(V(3.0, 0, 0))
    log('   Zelle in montierter Huelse: Weg bis Seitenwand %.2f mm (Clip haelt Zelle, Ausschub begrenzt)'
        % (FP.SLEEVE_IN['X'] - FP.CELL['XC'] - FP.CELL['D'] / 2))
    # 5 PCB von unten durch das Schott einschieben (Kappe mit Fenster, Zunge, Stoessel montiert)
    mov = ['PCB', 'Band_Huelle_F', 'D1_LED', 'SW1_Taster', 'Antenne_AN043', 'Keystone3034', 'CR2032', 'U3_TMP_Kragen']
    hitp = None
    for d in range(60, -1, -1):
        for a_ in mov:
            m = S[a_].copy(); m.translate(V(0, 0, -d))
            for b in ('Kappe_blau', 'Fenster_transluzent', 'Stoessel'):   # Keil wird erst nach dem Einschieben gesetzt
                B_ = RIBS['Kappe_ohne_Rippen'] if b == 'Kappe_blau' else S[b]   # Rippen werden beim Einschieben gequetscht
                if m.BoundBox.intersect(B_.BoundBox) and m.common(B_).Volume > 1e-3:
                    hitp = (d, a_, b); break
            if hitp: break
        if hitp: break
    log('5 Platine (mit Bauteilhuelle) 60 mm von unten durch das Schott einschieben: %s'
        % ('frei' if not hitp else 'Kollision %d mm vor Endlage: %s/%s' % hitp))
    # 5b Lage der Platine in z: freier Weg nach oben bis zum ersten Anschlag in der Kappe
    up = None
    for i in range(0, 41):
        dz = 0.05 * i + 0.01
        m = S['PCB'].copy(); m.translate(V(0, 0, dz))
        if m.common(RIBS['Kappe_ohne_Rippen']).Volume > 1e-3:
            up = dz; break
    log('5b Platine in Endlage: freier Weg nach oben bis Anschlag %s (Rev B: 0.70 bis Tastenblock)'
        % ('%.2f mm' % (up - 0.01) if up is not None else '> 2 mm, KEIN ANSCHLAG'))
    pz0, pz1 = Z['CELL_C'] - FP.CLIP['W'] / 2, Z['CELL_C'] + FP.CLIP['W'] / 2
    log('   Clip-Pads (Spanne W %.2f): z %.2f ... %.2f -> Luft zum Kragen-Verguss (z %.2f) %.2f mm, zum Schott-Verguss (z %.2f) %.2f mm; '
        'Lagetoleranz Platine +-%.2f' % (FP.CLIP['W'], pz0, pz1, Z['COL1'], pz0 - Z['COL1'], Z['BULK0'], Z['BULK0'] - pz1, PCB['TOL_Z']))
    sc = FP.SCREW
    eng = min(sc['L'], Z['COL_NUT1']) - Z['COL_NUT0']
    log('5c Schraube ISO 7045 M2x%g: Schaft z 0 ... %.1f, Mutter z %.1f ... %.1f -> Einschraubtiefe %.2f mm (%.1f Gaenge P 0.4), '
        'Ueberstand ueber Mutter %.2f; Freibohrung bis z %.1f, O-Ring-Nut ab z %.1f (Abstand %.2f)'
        % (sc['L'], sc['L'], Z['COL_NUT0'], Z['COL_NUT1'], eng, eng / 0.4, sc['L'] - Z['COL_NUT1'], sc['L'] + 0.3,
           Z['COL_G0'], Z['COL_G0'] - (sc['L'] + 0.3)))
    # 6 Abstaende
    d_led = PCB['Y_F'] - FP.LED['H'] - FP.DROP['BOSS_Y1']
    log('6 LED-Oberseite bis Fenster-Lichtschaft: %.2f mm (Ziel 1.5-2.5)' % d_led)
    log('   Klebefuge Fenster (Tropfen-Unterkante z %.2f) bis O-Ring-Nut oben z %.2f: %.2f mm (>= 1.0); '
        'Lichtschaft-Unterkante %.2f mm' % (FP.DROP['ZC'] - FP.DROP['R'], Z['SP_G1'], FP.DROP['ZC'] - FP.DROP['R'] - Z['SP_G1'],
                                            FP.DROP['ZC'] - FP.DROP['BOSS_D'] / 2 - Z['SP_G1']))
    log('   U3 (Kragen) - Kragen-ASA: %.2f mm, Epoxid ueber U3: %.2f mm (>= 0.5), U3 - Mutter: %.2f mm'
        % (S['U3_TMP_Kragen'].distToShape(S['Kragen'])[0], FP.KPOCKET['DEPTH'] - FP.TMP['H'],
           S['U3_TMP_Kragen'].distToShape(S['Mutter_M2'])[0]))
    for k in ('Mutter_M2', 'Schraube_M2', 'CR2032', 'Keystone3034'):
        log('   Abstand %-14s - Antenne: %.1f mm' % (k, S[k].distToShape(S['Antenne_AN043'])[0]))
    for k in ('Stoessel', 'Kappe_blau', 'Fenster_transluzent'):
        log('   Abstand Kunststoff %-20s - Antennenkupfer: %.2f mm' % (k, S[k].distToShape(S['Antenne_AN043'])[0]))
    log('   Abstand Mutter - Platine F: %.2f mm; Mutter - O-Ring Kragen: %.2f mm (Kragenwerkstoff dazwischen)'
        % (S['Mutter_M2'].distToShape(S['PCB'])[0], S['Mutter_M2'].distToShape(S['ORing_Kragen'])[0]))
    # 7 O-Ring
    O = FP.ORING
    per = rrect_perimeter(FP.GROOVE_BOT)
    log('7 O-Ring %s: Nutgrundumfang %.2f -> Dehnung %.1f %%' % (O['DASH'], per, (per / math.pi / O['ID'] - 1) * 100))
    for tg in (-0.2, 0.0, 0.2):
        for cs in (O['CS'] - O['CS_TOL'], O['CS'] + O['CS_TOL']):
            gl = O['GLAND'] + tg / 2 * 2 / 2
            log('   Einbauraum %.2f (FDM %+.1f) Schnur %.2f -> Verpressung %.0f %%' % (gl, tg / 2, cs, (cs - gl) / cs * 100))
    fill = math.pi / 4 * O['CS'] ** 2 / (O['GLAND'] * O['GROOVE_W'])
    log('   Nutfuellung %.0f %% (< 85 %%)' % (fill * 100))
    # 9 Wandstaerken Kern (Zapfen) und Sichtschale, Ablauf
    cap = S['Kappe_blau']
    T_ = FP.TONGUE
    for z in (32.5, 33.0, 34.0, 35.5, 40.0, 43.0, 44.0):
        slab = box(-30, 30, -5, 20, z - 0.05, z + 0.05)
        inner = rrect(FP.SP_IN, z - 0.05, z + 0.05)
        if z >= T_['Z_TIP'] - 1.0:
            inner = inner.fuse(box(T_['COL_X0'], T_['COL_X1'], T_['Y0'] - 0.3, FP.SP_IN['Y0'] + 0.1, z - 0.05, z + 0.05))
        outside = slab.cut(cap).cut(inner)
        if z > FP.DROP['ZC'] - 2.5:                                   # Fensterbohrung (geklebt) nicht als Wand werten
            outside = outside.cut(box(FP.DROP['X'] - 2.0, FP.DROP['X'] + 2.0, -5, 20, z - 1, z + 1))
        # Bereiche, die mit dem Innenraum verbunden sind (Fensterbohrung), nicht als Aussenraum zaehlen
        outside = Part.makeCompound([so for so in outside.Solids if so.distToShape(inner)[0] > 1e-4 or
                                     so.BoundBox.XLength > 20])
        log('9 Zapfen z %.1f: Wand min %.2f mm' % (z, inner.distToShape(outside)[0]))
    log('   Sichtschale (Huelse oberhalb Zapfen-O-Ring): Wand %.1f mm, Spalt zum Kern %.1f mm (Gleitspalt %.1f + Ruecksprung %.1f)'
        % (H['WALL'], H['CLR_SLIDE'] + CAP['RECESS'], H['CLR_SLIDE'], CAP['RECESS']))
    k = (Z['STEP_FRONT'] - Z['STEP_BACK']) / H['D']
    log('   Ablaufstufe: z %.1f vorn -> %.1f hinten, Gefaelle %.1f Grad; Schlitze %d x (%.1f x %.1f) Rueckwand ab z %.1f; '
        'Steg ueber Nut hinten %.1f mm'
        % (Z['STEP_FRONT'], Z['STEP_BACK'], math.degrees(math.atan(k)), len(FP.DRAIN['XC']), FP.DRAIN['W'], FP.DRAIN['H'],
           Z['STEP_BACK'], Z['STEP_BACK'] - Z['SP_G1']))
    # Ablaufpruefung: Huelse und Kern im Bereich der Stufe duerfen sich nicht beruehren; Schlitz-Unterkante <= Stufe hinten
    gap = S['Huelse_grau'].distToShape(S['Kappe_blau'].common(box(-30, 30, -5, 20, Z['STEP_FRONT'] + 0.3, H['Z_FUGE'] - 0.6)))[0]
    log('   kleinster Abstand Huelse - Kern zwischen Stufe und Fuge: %.2f mm' % gap)
    # 10 Tropfenfenster/Kerbe
    log('10 Tropfen: Mitte z %.1f (Fuge %.1f), Kerbe in der Sichtschale z %.1f ... Rand %.1f; Fenster-Unterkante bis Stufe vorn %.1f mm'
        % (FP.DROP['ZC'], H['Z_FUGE'], FP.DROP['ZC'] - FP.DROP['R'] - FP.DROP['NOTCH_GAP'], H['RIM_TOP'],
           FP.DROP['ZC'] - FP.DROP['R'] - Z['STEP_FRONT']))
    # 8 Volumen/Masse
    rho = {'ASA': 1.07e-3, 'FR4': 1.85e-3, 'Epoxid': 1.15e-3, 'Stahl': 7.9e-3, 'Silikon': 1.2e-3}
    mat = {'U3_TMP_Kragen': 'Epoxid', 'Kappe_blau': 'ASA', 'Huelse_grau': 'ASA', 'Kragen': 'ASA', 'Fenster_transluzent': 'ASA', 'Taste_blau': 'ASA',
           'Tastenteller': 'ASA', 'Klemmring': 'ASA', 'Stoessel': 'ASA', 'Schottkeil': 'ASA', 'PCB': 'FR4',
           'Verguss_Kragen': 'Epoxid', 'Verguss_Schott': 'Epoxid', 'Mutter_M2': 'Stahl', 'Schraube_M2': 'Stahl',
           'ORing_Kragen': 'Silikon', 'ORing_Zapfen': 'Silikon', 'Membran_Silikon': 'Silikon'}
    tot = 0
    log('8 Volumen / Masse (ASA 1.07, FR4 1.85, Epoxid 1.15, Stahl 7.9, Silikon 1.2 g/cm3; ANNAHME Dichten):')
    for k, mtl in mat.items():
        m_ = S[k].Volume * rho[mtl]
        tot += m_
        log('   %-20s %-7s %8.1f mm3 %6.2f g' % (k, mtl, S[k].Volume, m_))
    log('   + CR2032 2.9 g (ANNAHME), Clip 0.6 g, Bestueckung 0.5 g -> Sensor gesamt ca. %.1f g' % (tot + 4.0))
    return tot + 4.0


def placeholder_collision(S):
    """Platzhalter-Kollisionspruefung mit vereinfachtem PCB-Volumenmodell (Bauteilhoehen aus BOM/Datenblaettern)."""
    rows = [
        ('XBT1 Keystone 3034 (gedreht)', 'Keystone_3034_Catalog_M65.pdf S.1: H 4.1, W 23.1, L 16.1', 'Keystone3034'),
        ('BT1 CR2032', 'Panasonic_CR2032_Datasheet_2026-02.pdf S.1: Ø20 x 3.2', 'CR2032'),
        ('D1 RGB 1615', 'Elektronikbericht 1.1 / TUOZHAN DS S.4: 1.6 x 1.5 x 0.6', 'D1_LED'),
        ('SW1 TS-1088-AR02016', 'XUNPU DS S.1: 3.9 x 3.0, H 2.0, Hub 0.2', 'SW1_Taster'),
        ('Band F (CC2340 QFN 4x4, Quarze, L, C 1206, SC70, SOT-23, 0402)',
         'Huelle 26 x 15.1 x 2.0 (Zonengrenze hmax 2.0)', 'Band_Huelle_F'),
        ('U3 TMP1075N + C24 im Kragen', 'Huelle 4.4 x 2.0 x 0.7 (SOT-563 0.6, 0402 0.55 laut FLOORPLAN 2f)', 'U3_TMP_Kragen'),
        ('AN043-Antenne', 'INDEX ANT-AN043: 15.2 x 5.7, Kupfer', 'Antenne_AN043')]
    lines = ['Kollisionspruefung mit vereinfachtem PCB-Modell, fluidi Sensor (Schnittstelle Rev %s), erzeugt von fluidi_sensor.py' % FP.REV,
             'Modell: Kontur (Rev B = Rev C) + Bauteilhuellen je Zone + feste Bauteile. Pruefung mit dem KiCad-STEP: collision_pcb_step.txt (fluidi_pcb_collision.py).', '']
    housing = ['Kappe_blau', 'Huelse_grau', 'Kragen', 'Verguss_Kragen', 'Stoessel', 'Fenster_transluzent', 'Schottkeil', 'Mutter_M2',
               'Schraube_M2', 'ORing_Kragen', 'ORing_Zapfen', 'Taste_blau', 'Klemmring', 'Membran_Silikon', 'Tastenteller']
    for name, src, key in rows:
        mins = []
        for h in housing:
            d = S[key].distToShape(S[h])[0]
            mins.append((d, h))
        mins.sort()
        hs = [h for h in housing if not (key == 'U3_TMP_Kragen' and h == 'Verguss_Kragen')]
        mins = [m for m in mins if m[1] in hs]
        coll = [h for h in hs if S[key].BoundBox.intersect(S[h].BoundBox) and S[key].common(S[h]).Volume > 1e-3]
        lines.append('%-70s | %s' % (name, src))
        lines.append('    Kollision: %s | kleinster Abstand %.2f mm zu %s, %.2f mm zu %s'
                     % (', '.join(coll) or 'keine', mins[0][0], mins[0][1], mins[1][0], mins[1][1]))
    open(os.path.join(OUT, 'collision_placeholder.txt'), 'w').write('\n'.join(lines) + '\n')
    log('\n'.join(lines))


PRINT = {  # Teil: (Datei, Rotationen in Druckausrichtung, Material)
    'Huelse_grau': ('huelse_grau', [], 'ASA Warmgrau hell'),
    'Kappe_blau': ('kappe_blau', [((1, 0, 0), 180)], 'ASA Hellblau'),
    'Kragen': ('kragen', [], 'ASA (Rest, beliebig)'),
    'Fenster_transluzent': ('fenster_tropfen', [((1, 0, 0), 90)], 'ASA/PETG natur transluzent'),
    'Taste_blau': ('taste_blau', [((1, 0, 0), 180)], 'ASA Hellblau'),
    'Tastenteller': ('tastenteller', [], 'ASA Hellblau'),
    'Klemmring': ('klemmring', [((1, 0, 0), 180)], 'ASA Hellblau'),
    'Stoessel': ('stoessel', [((1, 0, 0), 90)], 'ASA (beliebig)'),
    'Schottkeil': ('schottkeil', [], 'ASA (beliebig)'),
}


def main():
    os.makedirs(os.path.join(OUT, 'print'), exist_ok=True)
    S, sl_plain, s_logo = build()
    log('Logo: Massstab %.4f mm/u -> Strich %.2f mm (2.0 u)' % (s_logo, 2.0 * s_logo))
    mass = checks(S, sl_plain)
    placeholder_collision(S)
    # Distanzlehre (Montage Kragen: Abstand Kragen-Oberkante bis Schott-Unterkante), 2 Stueck
    lehre = box(-1.5, 1.5, 0, 2.0, 0, Z['BULK0'] - Z['COL1'])
    doc = App.newDocument('fluidi_sensor')
    for k, s in S.items():
        o = doc.addObject('Part::Feature', k); o.Shape = s
    LN = 'distanzlehre_%s' % ('%.1f' % (Z['BULK0'] - Z['COL1'])).replace('.', 'p')
    o = doc.addObject('Part::Feature', LN.capitalize()); o.Shape = lehre
    doc.recompute()
    fc = os.path.join(OUT, 'fluidi_sensor.FCStd')
    doc.saveAs(fc)
    Part.export([o for o in doc.Objects if o.Name != LN.capitalize()], os.path.join(OUT, 'fluidi_sensor_assembly.step'))
    for k, (fn, rot, mtl) in PRINT.items():
        export_part(S[k], os.path.join(OUT, 'print', fn), rot)
    export_part(lehre, os.path.join(OUT, 'print', LN), [])
    # Passungsprobe: Huelse unten (Boden, Schlitz, Furchlippe, Kragensitz) und oben (Zapfensitz, Rand) -> mit Kragen
    # und O-Ring Gleitsitz, Verpressung und Schraube pruefen, bevor die ganze Huelse gedruckt wird
    probe = sl_plain.common(box(-20, 20, -5, 20, -1, 9.0))
    export_part(probe, os.path.join(OUT, 'print', 'passprobe_huelse_unten'), [])
    top = sl_plain.common(box(-20, 20, -5, 20, Z['BULK0'] - 2.0, H['RIM_TOP'] + 1))
    export_part(top, os.path.join(OUT, 'print', 'passprobe_huelse_oben'), [])
    App.closeDocument(doc.Name)
    for f in os.listdir(OUT):
        if f.endswith('.FCBak'):
            os.remove(os.path.join(OUT, f))
    open(os.path.join(OUT, 'check_sensor.txt'), 'w').write('\n'.join(LOG) + '\n')
    print('gespeichert:', fc)


if not os.environ.get('FLUIDI_NO_MAIN'):        # fluidi_pcb_collision.py importiert build() ohne Neuerzeugung
    main()
