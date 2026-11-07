# -*- coding: utf-8 -*-
"""fluidi Gateway G1 v3 "Sockel" - parametrisches Fertigungs-CAD (Phase 4b, Welle 1), FreeCAD 0.21.2 headless.

Design D-011 (docs/design/P3_FLUIDI.md Kap. V2.1, renders/gen/render_p3v3.py): 62 x 40 x 20 mm, Wanne Warmgrau hell
z 0 ... 13.85, Deckel Hellblau z 14.15 ... 20, 45-Grad-Frontfacette z 11 ... 20, 3-mm-Fasen an den Stirnseiten,
LED-Tropfen (r 2.5, Spitze 6.0) an der Fuge auf der Facette bei x = +21, Logo-Relief 22 mm auf der Front.
Innen: Seeed XIAO ESP32-S3 Plus (21 x 17.8, USB-C hinten), RTC-Modul (Platzhalter), FPC-Antenne innen an der
linken Stirnwand mit >= 15 mm Freiraum (Elektronikbericht phase3_rgb_antenne_elektronik.md Kap. 2.4, GW-4).

Lauf:  freecadcmd mechanical/gen/fluidi_gateway.py
Ausgabe: mechanical/gateway/fluidi_gateway.FCStd, fluidi_gateway_assembly.step, print/*.{step,stl,3mf},
         mechanical/gateway/check_gateway.txt

Koordinaten: x Breite (-31 ... 31), y Tiefe (-20 = Front, +20 = Rueckseite mit USB-C), z Hoehe (0 = Boden).
ANNAHMEN (Masse ohne lokales Datenblatt, am Muster messen): XIAO-Platine 1.2 mm dick, Bauteilhuelle oben 3.8 mm,
USB-C-Buchse Mitte 1.6 mm ueber Platine, Steckerumspritzung <= 12.0 x 6.5 mm; RTC-Modul 15 x 12 x 4 mm;
FPC-Antenne 30 x 7 x 0.2 mm (Seeed A-02, Masszeichnung fehlt); LED-Platine 10 x 10 x 1.6 mm + LED 0.6 mm;
Gewindeeinsatz M2.5 Aussen-Ø 3.5 x 4 mm (Bohrung 3.2).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import FreeCAD as App
import Part

import fluidi_params as FP
from fluidi_cadlib import V, box, cyl, drop2, logo_solid, collide, export_part

OUT = os.path.join(FP.REPO, 'mechanical', 'gateway')
G = dict(W=62.0, D=40.0, H=20.0, FACET=9.0, CH_END=3.0, Z_FUGE=14.0, GAP=0.3, WALL=2.0,
         LIP_CLR=0.15, LIP_T=1.2, LIP_Z0=11.5, LED_X=21.0)
XIAO = dict(LX=17.8, LY=21.0, T=1.2, H_TOP=3.8, X0=4.0, Y1=17.6, Z0=4.0, USB_DZ=1.6, PLUG=(12.0, 6.8))
RTC = dict(LX=15.0, LY=12.0, H=4.0, X0=-9.0, Y0=-16.0, Z0=2.0)
FPC = dict(L=30.0, W=7.0, T=0.2, YC=0.6, ZC=7.4)
SCREWS = [(25.5, 15.5), (25.5, -5.0)]
LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a); print(s); LOG.append(s)


def shell_solid(off):
    """Aussenkontur um off nach innen versetzt (Profil y-z mit Facette, extrudiert in x, Stirnkanten gefast)."""
    r2 = math.sqrt(2)
    D2, Hh = G['D'] / 2, G['H']
    z_f = Hh - G['FACET']
    prof = [(-D2 + off, off), (D2 - off, off), (D2 - off, Hh - off),
            (-D2 + G['FACET'] - off + off * r2, Hh - off), (-D2 + off, z_f + off - off * r2)]
    x0, x1 = -G['W'] / 2 + off, G['W'] / 2 - off
    pts = [V(x0, y, z) for y, z in prof] + [V(x0, prof[0][0], prof[0][1])]
    s = Part.Face(Part.makePolygon(pts)).extrude(V(x1 - x0, 0, 0))
    edges = [e for e in s.Edges if all(abs(v.Point.x - x0) < 1e-6 for v in e.Vertexes)
             or all(abs(v.Point.x - x1) < 1e-6 for v in e.Vertexes)]
    c = G['CH_END'] - off * (2 - r2)
    return s.makeChamfer(c, edges) if c > 0.2 else s


def facet_frame():
    """Ursprung auf der Facette an der Fuge bei x = LED_X; Einheitsvektoren u (x), v (Facette hinauf), n (aussen)."""
    zf = G['Z_FUGE']
    o = V(G['LED_X'], -G['D'] / 2 + (zf - (G['H'] - G['FACET'])), zf)
    u = V(1, 0, 0)
    v = V(0, 1, 1); v.normalize()
    n = V(0, -1, 1); n.normalize()
    return o, u, v, n


def facet_prism(poly_uv, w0, w1, vshift=0.0):
    o, u, v, n = facet_frame()
    def P(a, b, w):
        return o + u * a + v * (b + vshift) + n * w
    pts = [P(a, b, w0) for a, b in poly_uv] + [P(poly_uv[0][0], poly_uv[0][1], w0)]
    return Part.Face(Part.makePolygon(pts)).extrude(n * (w1 - w0))


def build():
    S = {}
    outer = shell_solid(0.0)
    inner = shell_solid(G['WALL'])
    shell = outer.cut(inner)
    zf, g2 = G['Z_FUGE'], G['GAP'] / 2
    big = 100
    low_cut = box(-big, big, -big, big, -1, zf - g2)
    up_cut = box(-big, big, -big, big, zf + g2, 50)
    wanne = shell.common(low_cut)
    deckel = shell.common(up_cut)
    # Deckel-Steg (Zentrierung, lichtdicht) in die Wanne
    lip = shell_solid(G['WALL'] + G['LIP_CLR']).cut(shell_solid(G['WALL'] + G['LIP_CLR'] + G['LIP_T']))
    lip = lip.common(box(-big, big, -big, big, G['LIP_Z0'], zf + g2 + 0.01))
    deckel = deckel.fuse(lip).removeSplitter()
    # Tropfenfenster: exakt im Deckel, Kerbe 0.3 groesser in der Wanne (wie Sensor)
    D = FP.DROP
    c_up = 0.4 * math.sqrt(2)
    dp = [(a, b) for a, b in drop2(0, c_up, D['R'], D['K'])]
    notch = drop2(0, c_up, D['R'] + D['NOTCH_GAP'], (D['K'] * D['R'] + D['NOTCH_GAP']) / (D['R'] + D['NOTCH_GAP']))
    deckel = deckel.cut(facet_prism(dp, -4.5, 1.0))
    wanne = wanne.cut(facet_prism(notch, -4.5, 1.0))
    win = facet_prism(drop2(0, c_up, D['R'] - D['GLUE'], D['K'] * D['R'] / (D['R'] - D['GLUE'])), -G['WALL'], 0.0)
    S['Fenster_transluzent'] = win
    # Lichtschacht (Deckel) und LED-Platine (Platzhalter) hinter dem Fenster, d = 2.0 mm
    o, u, v, n = facet_frame()
    tube_o = Part.makeCylinder(3.6, 2.2, o + v * c_up - n * (G['WALL'] + 2.2), n)
    tube_i = Part.makeCylinder(2.8, 3.0, o + v * c_up - n * (G['WALL'] + 2.6), n)
    shaft = tube_o.cut(tube_i)
    deckel = deckel.fuse(shaft.cut(wanne)).removeSplitter()
    sq = [(-5, -5 + c_up), (5, -5 + c_up), (5, 5 + c_up), (-5, 5 + c_up)]
    S['LED_Platine'] = facet_prism(sq, -(G['WALL'] + 2.6 + 1.6), -(G['WALL'] + 2.6))
    S['LED_RGB'] = facet_prism([(-0.8, -0.75 + c_up), (0.8, -0.75 + c_up), (0.8, 0.75 + c_up), (-0.8, 0.75 + c_up)],
                               -(G['WALL'] + 2.6), -(G['WALL'] + 2.0))
    # Logo-Relief Ton in Ton auf der Front (22 mm, Mitte x -12, z 5.4)
    lg, s_logo = logo_solid(os.path.join(FP.REPO, FP.LOGO['SVG']), 22.0, -12.0, 5.4, -G['D'] / 2, 0.25)
    wanne = wanne.fuse(lg)
    log('Logo Gateway: Strich %.2f mm' % (2.0 * s_logo))
    # XIAO: Auflageleisten, Front-Anschlag; USB-C-Ausschnitt hinten
    X = XIAO
    xa, xb = X['X0'], X['X0'] + X['LX']
    ya, yb = X['Y1'] - X['LY'], X['Y1']
    for xx in (xa - 0.3, xb - 1.0 + 0.3):
        wanne = wanne.fuse(box(xx, xx + 1.0, ya + 1, yb, G['WALL'] - 0.01, X['Z0']))
    wanne = wanne.fuse(box(xa + 3, xb - 3, ya - 1.2, ya - 0.2, G['WALL'] - 0.01, X['Z0'] + X['T'] + 1.0))
    zu = X['Z0'] + X['T'] + X['USB_DZ']
    xc = (xa + xb) / 2
    pw, ph = X['PLUG']
    wanne = wanne.cut(box(xc - pw / 2, xc + pw / 2, G['D'] / 2 - G['WALL'] - 0.5, G['D'] / 2 + 1, zu - ph / 2, zu + ph / 2))
    # Lueftung: Bodenschlitze unter dem XIAO, Schlitze in der Deckel-Rueckwand (Kamin)
    for k in range(4):
        x = xa + 3.0 + k * 3.6
        wanne = wanne.cut(box(x, x + 1.2, ya + 3.0, yb - 4.0, -1, G['WALL'] + 0.5))
    for k in range(4):
        x = -14.0 + k * 4.0
        deckel = deckel.cut(box(x, x + 1.2, G['D'] / 2 - G['WALL'] - 1, G['D'] / 2 + 1, zf + 1.6, G['H'] - 1.8))
    # RTC-Halter (Rahmen 1.5 hoch)
    R = RTC
    fr = box(R['X0'] - 1.2, R['X0'] + R['LX'] + 1.2, R['Y0'] - 1.2, R['Y0'] + R['LY'] + 1.2, G['WALL'] - 0.01, G['WALL'] + 1.5)
    fr = fr.cut(box(R['X0'] - 0.2, R['X0'] + R['LX'] + 0.2, R['Y0'] - 0.2, R['Y0'] + R['LY'] + 0.2, 0, 10))
    wanne = wanne.fuse(fr)
    # Niederhalter XIAO am Deckel (2 Rippen auf den Platinenraendern)
    for xx in (xa + 0.2, xb - 1.0):
        deckel = deckel.fuse(box(xx, xx + 0.8, ya + 4, yb - 4, X['Z0'] + X['T'] + 0.2, G['H'] - G['WALL'] + 0.01))
    # Verschraubung: 2 x M2.5 von unten (rechts), Gewindeeinsatz im Deckel; links 2 Rastnasen
    for (sx, sy) in SCREWS:
        boss_w = cyl(3.0, G['WALL'] - 0.01, zf - G['GAP'] / 2, sx, sy).cut(cyl(1.4, -1, 30, sx, sy))
        wanne = wanne.fuse(boss_w).cut(cyl(1.4, -1, 30, sx, sy)).cut(cyl(2.6, -1, 1.6, sx, sy))
        boss_d = cyl(3.0, zf + G['GAP'] / 2, G['H'] - G['WALL'] + 0.01, sx, sy)
        deckel = deckel.cut(cyl(3.3, 0, zf + G['GAP'] / 2, sx, sy))          # Steg am Dom aussparen
        deckel = deckel.fuse(boss_d).cut(cyl(1.6, zf, zf + 4.6, sx, sy))
    xs = -G['W'] / 2 + G['WALL'] + G['LIP_CLR']
    for sy in (-12.0, 12.0):   # Rastnase am Deckelsteg (0.35 in die Wand) + Tasche in der Wanne
        deckel = deckel.fuse(box(xs, xs + G['LIP_T'], sy - 2, sy + 2, G['LIP_Z0'] - 0.5, G['LIP_Z0'] + 0.01))
        deckel = deckel.fuse(box(xs - 0.5, xs + 0.01, sy - 2, sy + 2, G['LIP_Z0'] - 0.5, G['LIP_Z0']))
        wanne = wanne.cut(box(xs - G['LIP_CLR'] - 0.6, xs, sy - 2.3, sy + 2.3, G['LIP_Z0'] - 0.7, G['LIP_Z0'] + 0.2))
    S['Wanne_grau'] = wanne.removeSplitter()
    S['Deckel_blau'] = deckel.removeSplitter()
    # Elektronik (Platzhalter)
    S['XIAO_PCB'] = box(xa, xb, ya, yb, X['Z0'], X['Z0'] + X['T'])
    S['XIAO_Bauteile'] = box(xa + 1.2, xb - 1.2, ya + 0.5, yb - 3.5, X['Z0'] + X['T'], X['Z0'] + X['T'] + X['H_TOP'])
    S['USB_C'] = box(xc - 4.5, xc + 4.5, yb - 7.4, yb + 0.6, X['Z0'] + X['T'], X['Z0'] + X['T'] + 3.2)
    S['RTC_Modul'] = box(R['X0'], R['X0'] + R['LX'], R['Y0'], R['Y0'] + R['LY'], R['Z0'], R['Z0'] + R['H'])
    xf = -G['W'] / 2 + G['WALL']
    S['FPC_Antenne'] = box(xf, xf + FPC['T'], FPC['YC'] - FPC['L'] / 2, FPC['YC'] + FPC['L'] / 2,
                           FPC['ZC'] - FPC['W'] / 2, FPC['ZC'] + FPC['W'] / 2)
    S['Schraube_M2p5_1'] = cyl(2.25, -0.0, 1.6, *SCREWS[0]).fuse(cyl(1.25, 1.6, 17.6, *SCREWS[0]))
    S['Schraube_M2p5_2'] = cyl(2.25, -0.0, 1.6, *SCREWS[1]).fuse(cyl(1.25, 1.6, 17.6, *SCREWS[1]))
    S['Einsatz_1'] = cyl(1.75, zf + 0.2, zf + 4.2, *SCREWS[0]).cut(cyl(1.25, 0, 30, *SCREWS[0]))
    S['Einsatz_2'] = cyl(1.75, zf + 0.2, zf + 4.2, *SCREWS[1]).cut(cyl(1.25, 0, 30, *SCREWS[1]))
    for i, (fx, fy) in enumerate([(-24, -14), (24, -14), (-24, 14), (24, 14)]):
        S['Fuss_%d' % i] = cyl(4.0, -1.5, 0.0, fx, fy)
    return S


def checks(S):
    log('=== fluidi Gateway G1 v3 ===')
    allowed = {('Deckel_blau', 'Einsatz_1'), ('Deckel_blau', 'Einsatz_2'), ('Einsatz_1', 'Schraube_M2p5_1'),
               ('Einsatz_2', 'Schraube_M2p5_2'), ('Deckel_blau', 'Schraube_M2p5_1'), ('Deckel_blau', 'Schraube_M2p5_2'),
               ('LED_Platine', 'LED_RGB'), ('XIAO_PCB', 'XIAO_Bauteile'), ('XIAO_Bauteile', 'USB_C')}
    hits = collide(S, allowed)
    for a, b, v in hits:
        bb = S[a].common(S[b]).BoundBox
        log('   Lage %s/%s: x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f' % (a, b, bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    log('1 Kollisionen montiert: %s' % ('keine' if not hits else ', '.join('%s/%s %.3f' % h for h in hits)))
    metal = ['XIAO_PCB', 'XIAO_Bauteile', 'USB_C', 'RTC_Modul', 'Schraube_M2p5_1', 'Schraube_M2p5_2', 'Einsatz_1',
             'Einsatz_2', 'LED_Platine']
    log('2 Freiraum FPC-Antenne (Ziel >= 15 mm, Elektronikbericht 2.4):')
    ok = True
    for k in metal:
        d = S['FPC_Antenne'].distToShape(S[k])[0]
        ok &= d >= 15.0
        log('   %-16s %.1f mm %s' % (k, d, '' if d >= 15 else '<-- < 15'))
    # USB-C-Kabel: Stecker 15 mm hinter der Rueckwand als Huelle
    X = XIAO
    zu = X['Z0'] + X['T'] + X['USB_DZ']
    xc = X['X0'] + X['LX'] / 2
    plug = box(xc - 6, xc + 6, G['D'] / 2, G['D'] / 2 + 15, zu - 3.25, zu + 3.25)
    log('   USB-C-Stecker   %.1f mm' % S['FPC_Antenne'].distToShape(plug)[0])
    fpc_in = S['FPC_Antenne'].common(shell_solid(G['WALL'] - 0.01)).Volume / S['FPC_Antenne'].Volume
    log('3 FPC liegt innen an der Stirnwand: %.0f %% des FPC-Volumens im Innenraum' % (fpc_in * 100))
    d_led = 2.0
    log('4 LED-Fenster: LED %.1f mm hinter der Fensterinnenflaeche (Lichtschacht Ø5.6)' % d_led)
    log('5 Fuge z %.2f ... %.2f, Facette: Tropfen von %.2f bis %.2f mm schraeg ueber Facettenunterkante (Facette %.2f)'
        % (G['Z_FUGE'] - G['GAP'] / 2, G['Z_FUGE'] + G['GAP'] / 2, (G['Z_FUGE'] - 11) * math.sqrt(2) + 0.4 * math.sqrt(2) - 2.5,
           (G['Z_FUGE'] - 11) * math.sqrt(2) + 0.4 * math.sqrt(2) + 6.0, G['FACET'] * math.sqrt(2)))
    for k in ('Wanne_grau', 'Deckel_blau', 'Fenster_transluzent'):
        log('6 %-20s %.1f cm3 -> %.1f g ASA' % (k, S[k].Volume / 1000, S[k].Volume * 1.07e-3))
    # Waermeabschaetzung
    A = shell_solid(0).Area * 1e-6
    for P in (0.5, 1.0, 2.0):
        log('7 Verlustleistung %.1f W: dT Gehaeuse ~ %.0f K (h = 8 W/m2K, A = %.4f m2, ANNAHME)' % (P, P / (8 * A), A))
    return ok


PRINT = {'Wanne_grau': ('wanne_grau', [], 'ASA Warmgrau hell'),
         'Deckel_blau': ('deckel_blau', [((1, 0, 0), 180)], 'ASA Hellblau'),
         'Fenster_transluzent': ('fenster_tropfen_gw', [((1, 0, 0), 135)], 'ASA/PETG natur transluzent')}


def main():
    os.makedirs(os.path.join(OUT, 'print'), exist_ok=True)
    S = build()
    checks(S)
    doc = App.newDocument('fluidi_gateway')
    for k, s in S.items():
        o = doc.addObject('Part::Feature', k); o.Shape = s
    doc.recompute()
    fc = os.path.join(OUT, 'fluidi_gateway.FCStd')
    doc.saveAs(fc)
    Part.export(doc.Objects, os.path.join(OUT, 'fluidi_gateway_assembly.step'))
    for k, (fn, rot, mtl) in PRINT.items():
        export_part(S[k], os.path.join(OUT, 'print', fn), rot)
    App.closeDocument(doc.Name)
    for f in os.listdir(OUT):
        if f.endswith('.FCBak'):
            os.remove(os.path.join(OUT, f))
    open(os.path.join(OUT, 'check_gateway.txt'), 'w').write('\n'.join(LOG) + '\n')
    print('gespeichert:', fc)


main()
