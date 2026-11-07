# -*- coding: utf-8 -*-
"""fluidi P3 "Stele" - Machbarkeitsstudie Zellwechsel an der Farbfuge (Variante A1: Kern + graue Huelse,
eine M2-Schraube von unten). Vereinfachtes Volumenmodell (Bauteil-Huellen), kein Fertigungs-CAD.

Koordinaten: x = Breite (0 = Mitte), y = Tiefe (0 = Frontflaeche, + nach hinten), z = Hoehe (0 = Kopfunterkante).

Lauf:  freecadcmd mechanical/gen/p3_sleeve_concept.py
Ausgabe: mechanical/p3_sleeve/p3_sleeve_<variante>.FCStd / .step und Pruefprotokoll auf stdout.

Gepruefte Punkte (Skript):
  1. Kollisionsfreiheit aller Teile im montierten Zustand (gemeinsames Volumen = 0).
  2. Huelse laesst sich ueber die Sonde nach unten abziehen (Huelse in 1-mm-Schritten bis 150 mm verschieben).
  3. Zelle laesst sich nach Abziehen der Huelse seitlich (+x) aus dem Clip schieben (Weg 25 mm).
  4. Dichtflaechen: Stegbreiten der Bodendichtung, O-Ring-Verpressung im Toleranzband.
  5. Abstand Metall (Schraube/Mutter) zur Antenne.

ANNAHMEN (im Bericht docs/reviews/phase3_sleeve_mechanik.md begruendet):
  - Sondenbreite 22 mm (CONCEPTS Kap. 2.9/OP-K1b), Platinenbreite im Elektronikband 20 mm.
  - Keystone 3034 um 90 Grad gedreht (Einschubrichtung x): L 16.1 entlang x, W 23.1 entlang z, H 4.1
    (docs/datasheets/Keystone_3034_Catalog_M65.pdf, S. 1, Zeile 3034). Clip-Huelle vereinfacht als Quader.
  - CR2032 D 20 x 3.2 mm (Nennmass); M2-Mutter SW 4 x 1.6; O-Ring Schnur 1.5 mm.
"""
import os
import math
import FreeCAD as App
import Part

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(REPO, 'mechanical', 'p3_sleeve')
V = App.Vector


def prism(poly_xy, z0, z1):
    pts = [V(x, y, z0) for x, y in poly_xy] + [V(poly_xy[0][0], poly_xy[0][1], z0)]
    return Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, z1 - z0))


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def plan(W, D, cf=2.5, cb=1.0, off=0.0):
    """P3-Grundriss (Fasen vorne 2.5, hinten 1.0), optional nach innen versetzt (off > 0).
    Innenkontur: Fasen parallel versetzt -> konstante Wandstaerke auch an den Frontfasen."""
    h = W / 2 - off
    y0, y1 = off, D - off
    k = 0.4142 * off            # Fasenverkuerzung bei Parallelversatz (tan 22.5 Grad)
    a, b = max(cf - k, 0.3), max(cb - k, 0.3)
    return [(-h + a, y0), (h - a, y0), (h, y0 + a), (h, y1 - b), (h - b, y1), (-h + b, y1), (-h, y1 - b), (-h, y0 + a)]


def rrect_wire(x0, x1, y0, y1, z, r):
    """Rechteck mit Eckradius r als geschlossener Draht (O-Ring-Mittellinie)."""
    e = []
    e.append(Part.LineSegment(V(x0 + r, y0, z), V(x1 - r, y0, z)).toShape())
    e.append(Part.ArcOfCircle(Part.Circle(V(x1 - r, y0 + r, z), V(0, 0, 1), r), -math.pi / 2, 0).toShape())
    e.append(Part.LineSegment(V(x1, y0 + r, z), V(x1, y1 - r, z)).toShape())
    e.append(Part.ArcOfCircle(Part.Circle(V(x1 - r, y1 - r, z), V(0, 0, 1), r), 0, math.pi / 2).toShape())
    e.append(Part.LineSegment(V(x1 - r, y1, z), V(x0 + r, y1, z)).toShape())
    e.append(Part.ArcOfCircle(Part.Circle(V(x0 + r, y1 - r, z), V(0, 0, 1), r), math.pi / 2, math.pi).toShape())
    e.append(Part.LineSegment(V(x0, y1 - r, z), V(x0, y0 + r, z)).toShape())
    e.append(Part.ArcOfCircle(Part.Circle(V(x0 + r, y0 + r, z), V(0, 0, 1), r), math.pi, 1.5 * math.pi).toShape())
    return Part.Wire(Part.__sortEdges__(e))


def build(W=30.0, PROBE_W=22.0):
    P = dict(W=W, D=13.0, H=48.0, Z_FUGE=37.0,
             WALL=1.6, FLOOR=2.2, GASKET=0.6,           # Dichtung verpresst (0.8 -> 0.6)
             PCB_T=1.6, PCB_Y0=4.6, PROBE_W=PROBE_W, PCB_W_BAND=20.0, Z_STEP=29.6,
             COLLAR_H=3.2, BULK_T=1.5, SPIGOT_WALL=1.0, CORD=1.5, GLAND=1.1, LAND_CLR=0.2,
             SLOT_CLR=0.3, SCREW_Y=9.0, SCREW_L=4.0, RIB_X0=4.0, RIB_X1=8.0, Z_ANT0=38.3, Z_ANT1=44.0, ANT_W=15.2,
             HOLD_L=16.1, HOLD_W=23.1, HOLD_H=4.1, CELL_D=20.0, CELL_T=3.2)
    p = type('P', (), P)
    py0, py1 = p.PCB_Y0, p.PCB_Y0 + p.PCB_T
    in_x = p.W / 2 - p.WALL              # Huelse innen halbe Breite
    in_y0, in_y1 = p.WALL, p.D - p.WALL
    z_floor = p.FLOOR
    z_col0 = z_floor + p.GASKET
    z_col1 = z_col0 + p.COLLAR_H
    z_top_sleeve = p.Z_FUGE - 0.3        # Sichtfuge 0.3 mm

    S = {}
    # --- Leiterplatte: Sonde (PROBE_W) bis Z_STEP, darueber Elektronikband/Antenne 20 mm
    pcb = box(-p.PROBE_W / 2, p.PROBE_W / 2, py0, py1, -105.0, p.Z_STEP)
    pcb = pcb.fuse(box(-p.PCB_W_BAND / 2, p.PCB_W_BAND / 2, py0, py1, p.Z_STEP, p.Z_ANT1)).removeSplitter()
    S['PCB'] = pcb
    # --- Sondenkragen (Kern, mit PCB dauerhaft verklebt/vergossen = Dichtlinie REQ-MECH-08)
    col = prism(plan(p.W, p.D, off=p.WALL + 0.2), z_col0, z_col1).cut(pcb)
    # Mutter M2 SW 4 x 1.6 (Schluesselflaechen parallel zu x -> Tiefe y 7.0..11.0), im Kragen eingegossen
    import math
    hexp = [(2.0 / math.cos(math.pi / 6) * math.cos(k * math.pi / 3),
             p.SCREW_Y + 2.0 / math.cos(math.pi / 6) * math.sin(k * math.pi / 3)) for k in range(6)]
    nut = prism(hexp, z_col0 + 0.8, z_col0 + 2.4)
    col = col.cut(nut).cut(Part.makeCylinder(1.2, p.COLLAR_H, V(0, p.SCREW_Y, z_col0)))   # Schraubenfreiraum
    # Laengsnut in der Kragenrueckseite, durch die die Zellhaltenoppe der Huelse beim Abziehen gleitet
    col = col.cut(box(p.RIB_X0 - 0.2, p.RIB_X1 + 0.2, p.D - p.WALL - 0.2 - 0.8, p.D, z_col0 - 1, z_col1 + 1))
    S['Kragen'] = col
    S['Mutter_M2'] = nut.cut(Part.makeCylinder(1.0, 2, V(0, p.SCREW_Y, z_col0)))
    # --- Bodendichtung (vollflaechig, Aussparung Sondenschlitz und Schraube)
    slot_x = p.PROBE_W / 2 + p.SLOT_CLR
    slot = box(-slot_x, slot_x, py0 - p.SLOT_CLR, py1 + p.SLOT_CLR, -1, 60)
    gas = prism(plan(p.W, p.D, off=p.WALL + 0.1), z_floor, z_col0).cut(slot)
    gas = gas.cut(Part.makeCylinder(1.2, 2, V(0, p.SCREW_Y, z_floor - 0.5)))
    S['Bodendichtung'] = gas
    # --- Schraube M2 x SCREW_L Linsen-/Zylinderkopf (Kopf in Senkung unter dem Boden, Kopf D 3.8 x 1.2 ANNAHME)
    scr = Part.makeCylinder(1.0, p.SCREW_L, V(0, p.SCREW_Y, 1.3)).fuse(Part.makeCylinder(1.9, 1.2, V(0, p.SCREW_Y, 0.1)))
    S['Schraube_M2'] = scr
    # --- Zelle + Clip (gedreht: Einschub in x, offenes Ende +x), auf der Platinenrueckseite
    z_c = z_col1 + 0.4 + p.HOLD_W / 2
    cell = Part.makeCylinder(p.CELL_D / 2, p.CELL_T, V(0, py1 + 0.1, z_c), V(0, 1, 0))
    clip = box(-p.CELL_D / 2, -p.CELL_D / 2 + p.HOLD_L, py1, py1 + p.HOLD_H, z_c - p.HOLD_W / 2, z_c + p.HOLD_W / 2)
    S['CR2032'] = cell
    S['Keystone3034_Huelle'] = clip.cut(cell)
    z_bulk0 = z_c + p.HOLD_W / 2 + 0.3
    # --- Elektronik-Huelle (Bauteile Rueckseite 1.7 mm hoch, ANNAHME) und Antenne
    z_e0 = z_bulk0 + p.BULK_T
    S['Elektronik_Huelle'] = box(-p.PCB_W_BAND / 2 + 0.5, p.PCB_W_BAND / 2 - 0.5, py1, py1 + 1.7, z_e0 + 0.3, p.Z_ANT0 - 0.3)
    S['Antenne_AN043'] = box(-p.ANT_W / 2, p.ANT_W / 2, py1, py1 + 0.05, p.Z_ANT0, p.Z_ANT1)
    # --- Kappe blau: Band aussen Z_FUGE..H, Zapfen (Spigot) innen bis Schott, O-Ring-Nut
    land = plan(p.W, p.D, off=p.WALL + p.LAND_CLR)
    groove = plan(p.W, p.D, off=p.WALL + p.LAND_CLR + p.GLAND - p.LAND_CLR)  # Nutgrund = Huelse innen - GLAND
    inner = plan(p.W, p.D, off=p.WALL + p.GLAND + p.SPIGOT_WALL)
    cap = prism(plan(p.W, p.D), p.Z_FUGE, p.H).cut(prism(plan(p.W, p.D, off=p.WALL), p.Z_FUGE - 0.1, p.H - 2.0))
    spig = prism(land, z_bulk0, p.Z_FUGE + 0.5).cut(prism(inner, z_bulk0 + p.BULK_T, p.Z_FUGE + 1))
    z_g0 = z_bulk0 + p.BULK_T + 0.2
    ring_out = prism(land, z_g0, z_g0 + 2.0).cut(prism(groove, z_g0 - 1, z_g0 + 3))
    spig = spig.cut(ring_out)
    cap = cap.fuse(spig).removeSplitter()
    # LED-Tropfen als Zunge der Kappe in einer Kerbe der Huelse (vereinfacht Quader 5.2 breit, ab z 34)
    tongue = box(-2.6, 2.6, 0.0, p.WALL, 34.0, p.Z_FUGE)
    cap = cap.fuse(tongue).removeSplitter()
    cap = cap.cut(pcb)
    S['Kappe_blau'] = cap
    # O-Ring (Schnur 1.5) im Nutgrund, vereinfacht mit Rechteckquerschnitt 1.5 x 1.5 (Volumenhuelle, unverpresst
    # -> ueberschneidet Huelse und Nutgrund um die Verpressung; diese Paare sind in check() zugelassen)
    gx = p.W / 2 - (p.WALL + p.GLAND)
    gy0, gy1 = p.WALL + p.GLAND, p.D - (p.WALL + p.GLAND)
    zc_or = z_g0 + 1.0
    def rr(x0, x1, y0, y1, r):
        return Part.Face(rrect_wire(x0, x1, y0, y1, zc_or - p.CORD / 2, r))
    o_out = rr(-gx - p.CORD, gx + p.CORD, gy0 - p.CORD, gy1 + p.CORD, 2.0 + p.CORD).extrude(V(0, 0, p.CORD))
    o_in = rr(-gx, gx, gy0, gy1, 2.0).extrude(V(0, 0, p.CORD))
    S['ORing_1p5'] = o_out.cut(o_in)
    p.oring_len = 2 * (2 * gx + gy1 - gy0) - 8 * 2.0 + 2 * math.pi * (2.0 + p.CORD / 2)
    # --- Huelse grau
    sl = prism(plan(p.W, p.D), 0.0, z_top_sleeve).cut(prism(plan(p.W, p.D, off=p.WALL), z_floor, z_top_sleeve + 1))
    sl = sl.cut(slot)
    sl = sl.cut(Part.makeCylinder(1.1, 5, V(0, p.SCREW_Y, -1)))
    sl = sl.cut(Part.makeCylinder(2.2, 1.4, V(0, p.SCREW_Y, -0.01)))          # Senkung Schraubenkopf
    sl = sl.cut(box(-2.6 - 0.2, 2.6 + 0.2, -1, p.WALL + 0.01, 34.0 - 0.3, p.H))  # Kerbe LED-Zunge
    # Haltenoppe Zelle an der Rueckwand (Auflage R2-W01 Nr. 4), ausserhalb der Mutter (x 4..8)
    sl = sl.fuse(box(p.RIB_X0, p.RIB_X1, in_y1 - 0.6, in_y1 + 0.01, z_c - 3, z_c + 3)).removeSplitter()
    S['Huelse_grau'] = sl
    return p, S, dict(z_floor=z_floor, z_col0=z_col0, z_col1=z_col1, z_c=z_c, z_bulk0=z_bulk0, z_e0=z_e0,
                      z_g0=z_g0, in_x=in_x, slot_x=slot_x, z_top_sleeve=z_top_sleeve)


def check(name, p, S, g):
    print('\n=== Variante %s: Kopf %.1f x %.1f x %.1f, Sonde %.1f mm ===' % (name, p.W, p.D, p.H, p.PROBE_W))
    ok = True
    keys = list(S)
    allowed = {('Bodendichtung', 'Kragen'), ('Schraube_M2', 'Mutter_M2'), ('Kappe_blau', 'ORing_1p5'),
               ('Huelse_grau', 'ORing_1p5'), ('Antenne_AN043', 'PCB')}
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            v = S[a].common(S[b]).Volume
            if v > 1e-3 and (a, b) not in allowed and (b, a) not in allowed:
                print('  KOLLISION %-22s %-22s %.3f mm3' % (a, b, v)); ok = False
    print('  1 Kollisionen montiert:', 'keine' if ok else 'JA')
    # O-Ring-Verpressung
    for tol in (-0.1, 0.0, 0.1):
        gap = p.GLAND + tol * 2 / 2      # Huelse innen +-0.1, Nutgrund +-0.1 -> Spalt +-0.1 (worst case je Seite)
        print('  4 O-Ring %.1f: radialer Spalt %.2f -> Verpressung %.0f %%' % (p.CORD, gap, (p.CORD - gap) / p.CORD * 100))
    land_x = g['in_x'] - g['slot_x']
    land_f = (p.PCB_Y0 - p.SLOT_CLR) - p.WALL
    land_b = (p.D - p.WALL) - (p.PCB_Y0 + p.PCB_T + p.SLOT_CLR)
    print('  4 O-Ring Mittellinie %.1f mm -> ID bei 3 %% Dehnung %.1f mm (Normgroesse waehlen)' % (p.oring_len, p.oring_len / math.pi / 1.03 - p.CORD))
    print('  4 Bodendichtung Stegbreite: seitlich %.2f, vorne %.2f, hinten %.2f mm (Ziel >= 2.0)' % (land_x, land_f, land_b))
    spig_in = p.W / 2 - p.WALL - p.GLAND - p.SPIGOT_WALL
    print('  4 Zapfen innen halbe Breite %.2f -> Platine Band %.1f, Vergussspalt je Seite %.2f' % (spig_in, p.PCB_W_BAND, spig_in - p.PCB_W_BAND / 2))
    print('  Hoehen: Boden 0-%.1f, Dichtung -%.1f, Kragen -%.1f, Zelle/Clip %.1f-%.1f, Schott %.1f-%.1f, O-Ring-Nut %.1f-%.1f, '
          'Elektronikband %.1f-%.1f, Antenne %.1f-%.1f, Fuge %.1f, Kopf %.1f'
          % (g['z_floor'], g['z_col0'], g['z_col1'], g['z_c'] - p.HOLD_W / 2, g['z_c'] + p.HOLD_W / 2, g['z_bulk0'],
             g['z_bulk0'] + p.BULK_T, g['z_g0'], g['z_g0'] + 2, g['z_e0'], p.Z_ANT0, p.Z_ANT0, p.Z_ANT1, p.Z_FUGE, p.H))
    # 2 Huelse abziehen
    kern = [S[k] for k in ('PCB', 'Kragen', 'CR2032', 'Keystone3034_Huelle', 'Kappe_blau', 'Mutter_M2', 'Elektronik_Huelle')]
    first = None
    for d in range(1, 151):
        m = S['Huelse_grau'].copy(); m.translate(V(0, 0, -d))
        hit = sum(m.common(k).Volume for k in kern)  # O-Ring gleitet (verpresst), nicht geprueft
        if hit > 1e-3:
            first = d; break
    print('  2 Huelse nach unten abziehen 150 mm:', 'frei' if first is None else 'Kollision bei %d mm' % first)
    # 3 Zelle seitlich herausschieben (Huelse entfernt)
    path_ok = True
    for d in range(1, 26):
        c = S['CR2032'].copy(); c.translate(V(d, 0, 0))
        for k in ('Kragen', 'Kappe_blau', 'Mutter_M2', 'Elektronik_Huelle'):
            if c.common(S[k]).Volume > 1e-3:
                print('  3 Zelle stoesst bei %d mm an %s' % (d, k)); path_ok = False; break
        if not path_ok:
            break
    print('  3 Zelle seitlich 25 mm herausschieben:', 'frei' if path_ok else 'blockiert')
    dist = S['Mutter_M2'].distToShape(S['Antenne_AN043'])[0]
    print('  5 Abstand Mutter/Schraube - Antenne: %.1f mm' % dist)
    return ok and first is None and path_ok


if __name__ == '__main__' or True:
    os.makedirs(OUT, exist_ok=True)
    res = {}
    for name, W, PW in (('A1_30x13x48_sonde22', 30.0, 22.0), ('A1_28x13x48_sonde20', 28.0, 20.0),
                        ('A1_28x13x48_sonde22', 28.0, 22.0)):
        p, S, g = build(W, PW)
        res[name] = check(name, p, S, g) and (p.W / 2 - p.WALL) - (p.PROBE_W / 2 + p.SLOT_CLR) >= 2.0
        if name.startswith('A1_30') or name == 'A1_28x13x48_sonde20':
            doc = App.newDocument('p3_sleeve_' + name.split('_')[1])
            for k, s in S.items():
                o = doc.addObject('Part::Feature', k); o.Shape = s
            doc.recompute()
            fc = os.path.join(OUT, 'p3_sleeve_%s.FCStd' % name)
            doc.saveAs(fc)
            Part.export([o for o in doc.Objects], os.path.join(OUT, 'p3_sleeve_%s.step' % name))
            print('  gespeichert:', fc)
            App.closeDocument(doc.Name)
            for f in os.listdir(OUT):
                if f.endswith('.FCBak'):
                    os.remove(os.path.join(OUT, f))
    print('\nErgebnis:', res)
