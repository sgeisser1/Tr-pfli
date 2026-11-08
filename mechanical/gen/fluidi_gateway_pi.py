# -*- coding: utf-8 -*-
"""fluidi Gateway G1 v4 "Sockel" fuer Raspberry Pi Zero 2 W (D-014) - parametrisches CAD, FreeCAD 0.21.2 headless.

Formsprache wie freigegebenes G1 v3 (D-011, docs/design/P3_FLUIDI.md Kap. V2.1, renders/gen/render_p3v3.py):
Wanne Warmgrau hell #B9B5AC z 0 ... 13.85, Deckel Hellblau z 14.15 ... 20, 45-Grad-Frontfacette (9 mm), 3-mm-Fasen
an den Stirnseiten, LED-Tropfen an der Fuge auf der Facette, Logo-Relief Ton in Ton auf der Front, keine Antenne aussen.
Gegenueber v3 nur groesser (84 x 42 x 20 statt 62 x 40 x 20), alle Profile/Fasen/Fuge/Tropfen identisch.
Rechts eine thermisch getrennte Klimakammer (Luft-T/rF-Breakout, Auftrag 2026-11-07).

Lauf:  freecadcmd -c "exec(open('mechanical/gen/fluidi_gateway_pi.py').read())"   (oder: freecadcmd <datei>)
Ausgabe: mechanical/gateway_pi/fluidi_gateway_pi.FCStd, fluidi_gateway_pi_assembly.step, print/*.{step,stl,3mf},
         check_gateway_pi.txt, preview.png

Koordinaten: x Breite (-42 ... 42), y Tiefe (-21 = Front mit Facette, +21 = Rueckseite mit USB), z Hoehe (0 = Boden).
Pi-Koordinaten (X, Y) wie Masszeichnung (Draufsicht, Bauteilseite oben): X = 0 Stirnkante bei Mini-HDMI/microSD,
Y = 0 Laengskante mit den Buchsen, Y = 30 Header-Kante. Im Gehaeuse um 180 Grad gedreht (Buchsen hinten):
x = XR - X, y = YB - Y.

QUELLEN (lokal):
  docs/datasheets/RaspberryPi_Zero2W_MechanicalDrawing_RP-008358-DS-1.pdf (= Product Brief 2024-04, S. 4):
    65 x 30, Bohrungen 3.5 vom Rand (Raster 58 x 23), Mitten Mini-HDMI X 12.4, USB-OTG X 41.4, USB-PWR X 54.
  Weitere Lagen in der Ebene aus derselben Zeichnung ABGEGRIFFEN (Vektor-PDF bei 600 dpi, Massstab 23.63 px/mm
  aus 65/30 mm, Genauigkeit ca. +-0.2 mm): Bohrung Ø ~2.7, Freihaltekreis Ø 6.0; HDMI X 6.9-17.9 / Y -0.6-7.0;
  OTG X 37.6-45.2, PWR X 50.2-57.8 (Kragen 0.3 breiter), Y -0.9 ... 4.7; microSD-Halter X 1.6-13.1 / Y 10.9-22.9
  (Karte von der Stirnkante X = 0); SiP X 19.8-34.9 / Y 6.5-21.6; Abschirmhaube X 37.6-49.9 / Y 7.4-19.7;
  Kamerabuchse X 61.6-65.0 / Y 7.5-22.5; Ecken R 3.0; Header-Footprint X 7.0-58.9 / Y 24.0-29.0.
ANNAHMEN (Zeichnung enthaelt KEINE Hoehen, keine Lage von ACT-LED und Antenne -> am vorhandenen Board messen):
  PCB 1.0 mm; Bauteilhoehen ueber PCB: HDMI 3.5, Micro-USB 3.0 (Mitte 1.5), microSD-Halter 2.0, SiP 1.4, Haube 1.8,
  Kamerabuchse 2.0, uebrige Bauteile <= 1.2 (Huelle); Unterseite <= 1.2; Karte steht 2.5 ueber die Kante;
  Micro-USB-Steckerumspritzung <= 10.6 x 7.0; GPIO-Header NICHT bestueckt (bestueckt: Stifte 8.5 hoch, Option pruefen);
  LED-Platine 8 x 8.2 x 1.0 (eigene Mini-Platine, RGB wie Sensor, an GPIO-Pads geloetet, auf Lichtschacht geklebt); RTC-Modul Adafruit 4282 21.3 x 20.0 (ohne Buchsenleiste, Hoehe am Modul messen);
  Gewindeeinsatz M2.5 Ø 3.5 x 4 (Bohrung 3.2), Schraube M2.5 x 8 Linsenkopf ISO 7380 (dk 4.7, k 1.4).
"""
import math
import os
import sys

try:
    _HERE = os.path.dirname(os.path.abspath(__file__))
except NameError:   # Aufruf ueber exec()
    _HERE = os.path.join(os.getcwd(), 'mechanical', 'gen')
sys.path.insert(0, _HERE)
import FreeCAD as App
import Part

import fluidi_params as FP
from fluidi_cadlib import V, box, cyl, drop2, logo_solid, collide, export_part

OUT = os.path.join(FP.REPO, 'mechanical', 'gateway_pi')
G = dict(W=84.0, D=42.0, H=20.0, FACET=9.0, CH_END=3.0, Z_FUGE=14.0, GAP=0.3, WALL=2.0,
         LIP_CLR=0.15, LIP_T=1.2, LIP_Z0=11.5, LED_X=24.0)
# Klimakammer (Lufttemperatur/-feuchte, I2C-Breakout, Modul folgt Welle 2): rechte Stirnseite, eigene Kammer
CLIMA = dict(WI=8.0, WALL=2.0, MW=24.0, MH=14.0, MT=1.6, PART_F=2.5, PART_B=1.0, YC=2.0, Z0=3.0, X_PCB=36.0,
             HOLE_D=3.0, HOLE_Y=-3.5, HOLE_Z=10.5, BOSS_R=2.5, BOSS_L=2.5, BUNDLE_D=2.6)
# GPIO-Loetaugen fuer die Klimasensor-Leitungen (keine Stiftleiste, Leitungen direkt eingeloetet).
# Lage aus RP-008358-DS-1 abgegriffen: Quadratpad (= Pin 1) Mitte X 8.39 / Y 25.25, Raster 2.54 (X) x 2.54 (Y),
# ungerade Pins in der Reihe Y 25.25, gerade in Y 27.79. Belegung 3V3 = 1, SDA/GPIO2 = 3, SCL/GPIO3 = 5, GND = 6 oder 9
# laut Auftrag (Pinbelegung steht NICHT in der Masszeichnung; Elektronik prueft gegen RP-008360-DS-1).
PIN1 = (8.39, 25.25)
def pin_xy(n):
    col, row = (n - 1) // 2, (n - 1) % 2
    return PIN1[0] + 2.54 * col, PIN1[1] + 2.54 * row
# Pi Zero 2 W (siehe Kopf: Zeichnung + ANNAHMEN)
PI = dict(L=65.0, B=30.0, R=3.0, T=1.0, HOLE_D=2.7, KEEP_D=6.0, HOLES=[(3.5, 3.5), (61.5, 3.5), (3.5, 26.5), (61.5, 26.5)],
          Z0=5.0,                     # Unterseite PCB (Abstandshalter 3.0 ueber Boden)
          CLR_BACK=0.4, CLR_CAM=1.0, SD_SPACE=4.0, CARD_OUT=2.5, ENV_TOP=1.2, ENV_BOT=1.2)
PARTS = {   # Name: (X0, X1, Y0, Y1, Hoehe ueber PCB)   Lage abgegriffen, Hoehe ANNAHME
    'HDMI': (6.9, 17.9, -0.6, 7.0, 3.5),
    'USB_OTG': (37.3, 45.5, -0.9, 4.7, 3.0),
    'USB_PWR': (49.9, 58.1, -0.9, 4.7, 3.0),
    'SD_Halter': (1.6, 13.1, 10.9, 22.9, 2.0),
    'SiP': (19.8, 34.9, 6.5, 21.6, 1.4),
    'Haube_WLAN': (37.6, 49.9, 7.4, 19.7, 1.8),
    'Kamerabuchse': (61.6, 65.0, 7.5, 22.5, 2.0),
}
USB = dict(PWR_X=54.0, OTG_X=41.4, ZC_DZ=1.5, WIN=(11.4, 7.8), PLUG=(10.6, 7.0), RELIEF=1.2)
HEADER = dict(X0=7.0, X1=58.9, Y0=24.0, Y1=29.0, H=8.5)
TUBE = dict(R=2.8, INS_D=3.2, INS_L=4.6, HOLE_D=2.8, CB_D=5.4, CB_H=1.6, SCREW_L=8.0, HEAD_D=4.7, HEAD_K=1.4)
# Phase 5 (Befund Fertigung): RTC Adafruit 4282 PiRTC 21.3 x 20.0 x 13.6 mm inkl. Buchsenleiste
# (docs/references/Adafruit_4282_PiRTC-DS3231_Produktseite_Auszug_2026-11-08.txt, Z. 130). Mit Leiste passt es nicht (Pi ohne
# Stiftleiste, Bauraum ueber dem Pi < 13.6). Variante mit RTC: Modul OHNE Buchsenleiste, Litzen in die Loetaugen (wie Klima),
# flach unter die Deckeldecke geklebt. H = Grenzhoehe des Bauraums (0.5 Luft ueber Haube/SiP), KEIN Modulmass -> am Modul
# messen. Variante ohne RTC: Rahmen bleibt leer. Lage: zwischen Haube/SiP und HDMI, vor dem Steg, neben den Klima-Litzen.
RTC = dict(LX=21.3, LY=20.0, H=9.7, H_SRC=13.6, X=29.0, Y=15.4)   # Lage (Mitte) in Pi-Koordinaten
LEDB = dict(S=8.0, V0=-5.0, V1=3.2, T=1.0, DIST=1.6)   # Platine 8 breit, entlang Facette V0..V1 um Fensterachse
LOG = []

X_PART = G['W'] / 2 - G['WALL'] - CLIMA['WI'] - CLIMA['WALL']   # Trennwand Klimakammer x X_PART ... X_PART + 2
XR = X_PART - PI['SD_SPACE']                          # x der Pi-Kante X = 0
YB = G['D'] / 2 - G['WALL'] - PI['CLR_BACK']          # y der Pi-Kante Y = 0
ZP = PI['Z0'] + PI['T']                               # Oberseite PCB


def log(*a):
    s = ' '.join(str(x) for x in a); print(s); LOG.append(s)


def px(X):
    return XR - X


def py(Y):
    return YB - Y


def pbox(X0, X1, Y0, Y1, z0, z1):
    return box(px(X1), px(X0), py(Y1), py(Y0), z0, z1)


def shell_solid(off):
    """Aussenkontur um off nach innen versetzt (Profil y-z mit Facette, extrudiert in x, Stirnkanten gefast) - wie v3."""
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


def pi_outline(z0, z1):
    """Platinenumriss 65 x 30 mit Eckradius 3.0 (aus der Zeichnung abgegriffen)."""
    r = PI['R']
    b = pbox(0, PI['L'], 0, PI['B'], z0, z1)
    e = [ed for ed in b.Edges if abs(ed.Vertexes[0].Point.z - ed.Vertexes[1].Point.z) > 1e-6]
    return b.makeFillet(r, e)


def pi_model():
    """Vereinfachtes Pi-Zero-2-W-Modell (Huellkoerper)."""
    S = {}
    z0, zp = PI['Z0'], ZP
    pcb = pi_outline(z0, zp)
    keep = None
    for X, Y in PI['HOLES']:
        pcb = pcb.cut(cyl(PI['HOLE_D'] / 2, z0 - 1, zp + 1, px(X), py(Y)))
        k = cyl(PI['KEEP_D'] / 2, z0 - 3, zp + 10, px(X), py(Y))
        keep = k if keep is None else keep.fuse(k)
    S['Pi_PCB'] = pcb
    env_t = pi_outline(zp, zp + PI['ENV_TOP']).cut(keep)
    for k, (X0, X1, Y0, Y1, h) in PARTS.items():
        env_t = env_t.fuse(pbox(X0, X1, Y0, Y1, zp, zp + h))
    S['Pi_Bauteile_oben'] = env_t.removeSplitter()
    S['Pi_Bauteile_unten'] = pi_outline(z0 - PI['ENV_BOT'], z0).cut(keep)
    S['microSD_Karte'] = pbox(-PI['CARD_OUT'], 13.0, 11.4, 22.4, zp + 0.5, zp + 1.5)
    return S


def build():
    S = {}
    outer = shell_solid(0.0)
    inner = shell_solid(G['WALL'])
    cavity = shell_solid(G['WALL'] - 0.01)
    shell = outer.cut(inner)
    zf, g2 = G['Z_FUGE'], G['GAP'] / 2
    big = 200
    wanne = shell.common(box(-big, big, -big, big, -1, zf - g2))
    deckel = shell.common(box(-big, big, -big, big, zf + g2, 50))
    # Deckel-Steg (Zentrierung, lichtdicht) in die Wanne
    lip = shell_solid(G['WALL'] + G['LIP_CLR']).cut(shell_solid(G['WALL'] + G['LIP_CLR'] + G['LIP_T']))
    lip = lip.common(box(-big, big, -big, big, G['LIP_Z0'], zf + g2 + 0.01))
    deckel = deckel.fuse(lip).removeSplitter()
    # ---- Tropfenfenster wie v3 (Deckel exakt, Kerbe 0.3 groesser in der Wanne)
    D = FP.DROP
    c_up = 0.4 * math.sqrt(2)
    dp = drop2(0, c_up, D['R'], D['K'])
    notch = drop2(0, c_up, D['R'] + D['NOTCH_GAP'], (D['K'] * D['R'] + D['NOTCH_GAP']) / (D['R'] + D['NOTCH_GAP']))
    deckel = deckel.cut(facet_prism(dp, -4.5, 1.0))
    wanne = wanne.cut(facet_prism(notch, -4.5, 1.0))
    S['Fenster_transluzent'] = facet_prism(drop2(0, c_up, D['R'] - D['GLUE'], D['K'] * D['R'] / (D['R'] - D['GLUE'])),
                                           -G['WALL'], 0.0)
    o, u, v, n = facet_frame()
    # Lichtschacht gehoert zur WANNE (liegt unter der Wannen-Facette; im Deckel waere er nicht montierbar),
    # Stirnflaeche = Auflage der LED-Platine (geklebt)
    L = LEDB['DIST']
    tube_o = Part.makeCylinder(3.1, L, o + v * c_up - n * (G['WALL'] + L), n)
    tube_i = Part.makeCylinder(2.3, L + 1.0, o + v * c_up - n * (G['WALL'] + L + 0.5), n)
    shaft = tube_o.cut(tube_i).common(cavity).cut(deckel)
    wanne = wanne.fuse(shaft).cut(facet_prism(notch, -4.5, 1.0)).removeSplitter()
    s2 = LEDB['S'] / 2
    sq = [(-s2, LEDB['V0'] + c_up), (s2, LEDB['V0'] + c_up), (s2, LEDB['V1'] + c_up), (-s2, LEDB['V1'] + c_up)]
    S['LED_Platine'] = facet_prism(sq, -(G['WALL'] + L + LEDB['T']), -(G['WALL'] + L))
    S['LED_RGB'] = facet_prism([(-0.8, -0.75 + c_up), (0.8, -0.75 + c_up), (0.8, 0.75 + c_up), (-0.8, 0.75 + c_up)],
                               -(G['WALL'] + L), -(G['WALL'] + L - 0.6))
    # Halteklammern LED-Platine (2 Haken am Lichtschacht-Rohr waeren unsicher -> 2 Rippen am Deckel, Platine geklebt)
    # ---- Logo-Relief Ton in Ton auf der Front
    lg, s_logo = logo_solid(os.path.join(FP.REPO, FP.LOGO['SVG']), 22.0, -16.0, 5.4, -G['D'] / 2, 0.25)
    wanne = wanne.fuse(lg)
    log('Logo Gateway: Strich %.2f mm' % (2.0 * s_logo))
    # ---- Pi-Befestigung: 4 Abstandshalter (Wanne) + 4 Niederhalterrohre mit Einsatz (Deckel), M2.5 von unten
    T = TUBE
    # Freiraum 0.3 der Rohre zur Wannenwand (vorne laufen die Rohre unter der Facette bis unter die Fuge)
    wclear = outer.cut(shell_solid(G['WALL'] + 0.3)).common(box(-big, big, -big, big, -1, zf - g2 + 0.25))
    for X, Y in PI['HOLES']:
        x, y = px(X), py(Y)
        wanne = wanne.fuse(cyl(T['R'], G['WALL'] - 0.01, PI['Z0'], x, y))
        wanne = wanne.cut(cyl(T['HOLE_D'] / 2, -1, PI['Z0'] + 1, x, y)).cut(cyl(T['CB_D'] / 2, -1, T['CB_H'], x, y))
        tube = cyl(T['R'], ZP, G['H'], x, y).common(cavity).cut(wclear)
        deckel = deckel.fuse(tube).cut(cyl(T['INS_D'] / 2, ZP - 0.1, ZP + T['INS_L'], x, y))
        deckel = deckel.cut(cyl(1.4, ZP + T['INS_L'] - 0.1, ZP + T['INS_L'] + 2.0, x, y))   # Spanraum Schraubenspitze
    # ---- Rueckwand: Ausschnitte Micro-USB (Steckerumspritzung) + innere Freistiche (Pi senkrecht einlegen)
    zc = ZP + USB['ZC_DZ']
    ww, wh = USB['WIN']
    yin = G['D'] / 2 - G['WALL']
    win_pwr = box(px(USB['PWR_X']) - ww / 2, px(USB['PWR_X']) + ww / 2, yin - 0.5, G['D'] / 2 + 1, zc - wh / 2, zc + wh / 2)
    win_otg = box(px(USB['OTG_X']) - ww / 2, px(USB['OTG_X']) + ww / 2, yin - 0.5, G['D'] / 2 + 1, zc - wh / 2, zc + wh / 2)
    wanne = wanne.cut(win_pwr)
    for k in ('HDMI', 'USB_OTG', 'USB_PWR'):
        X0, X1, Y0, Y1, h = PARTS[k]
        wanne = wanne.cut(box(px(X1) - 0.3, px(X0) + 0.3, yin - 0.5, yin + USB['RELIEF'], ZP - 0.3, zf))
    # ---- Lueftung: Bodenschlitze unter SiP, Kaminschlitze in der Deckel-Rueckwand
    sx0, sx1 = px(34.9), px(19.8)
    sy0, sy1 = py(21.6), py(6.5)
    nsl = 5
    for k in range(nsl):
        x = sx0 + 0.6 + k * (sx1 - sx0 - 1.2 - 1.2) / (nsl - 1)
        wanne = wanne.cut(box(x, x + 1.2, sy0 + 1.0, sy1 - 1.0, -1, G['WALL'] + 0.5))
    for k in range(4):
        x = sx0 + 1.0 + k * 4.0
        deckel = deckel.cut(box(x, x + 1.2, G['D'] / 2 - G['WALL'] - 1, G['D'] / 2 + 1, zf + 1.6, G['H'] - 1.8))
    # ---- Option RTC-Modul: Rahmen 1.5 hoch an der Deckelinnenseite (Modul geklebt)
    R = RTC
    rx0, rx1 = px(R['X']) - R['LX'] / 2, px(R['X']) + R['LX'] / 2
    ry0, ry1 = py(R['Y']) - R['LY'] / 2, py(R['Y']) + R['LY'] / 2
    ztop = G['H'] - G['WALL']
    fr = box(rx0 - 1.2, rx1 + 1.2, ry0 - 1.2, ry1 + 1.2, ztop - 1.5, ztop + 0.01)
    fr = fr.cut(box(rx0 - 0.2, rx1 + 0.2, ry0 - 0.2, ry1 + 0.2, 0, 30))
    deckel = deckel.fuse(fr)
    # ---- Klimakammer rechts: Trennwand (Wanne) + Gegenrippe (Deckel, Spalt 0.3 = Fuge), Kabeldurchfuehrung,
    #      Halter (2 Nutpfosten, Modul steht in der y-z-Ebene, Sensorseite +x zur Stirnwand), Schlitze Boden/Stirn
    C = CLIMA
    xp0, xp1 = X_PART, X_PART + C['WALL']
    wanne = wanne.fuse(box(xp0, xp1, -big, big, 0, zf - g2).common(cavity))
    deckel = deckel.cut(box(xp0 - G['LIP_CLR'], big, -big, big, 0, zf + g2 + 0.02))     # kein Steg an Trennwand/in der Kammer
    deckel = deckel.fuse(box(xp0, xp1, -big, big, zf + g2, 50).common(cavity))
    # Kabeldurchfuehrung mit Zugentlastung: Kanal Ø 3.0, 4.5 lang (Trennwand + Buchse auf der Pi-Seite), nach dem
    # Einfaedeln mit Silikon/Heisskleber vergossen (dichtet zugleich die Kammer gegen Pi-Warmluft ab)
    wanne = wanne.fuse(Part.makeCylinder(C['BOSS_R'], C['BOSS_L'] + 0.01, V(xp0 - C['BOSS_L'], C['HOLE_Y'], C['HOLE_Z']),
                                         V(1, 0, 0)))
    wanne = wanne.cut(Part.makeCylinder(C['HOLE_D'] / 2, 10, V(xp0 - 5, C['HOLE_Y'], C['HOLE_Z']), V(1, 0, 0)))
    xm0, xm1 = C['X_PCB'] - C['MT'] / 2, C['X_PCB'] + C['MT'] / 2
    ym0, ym1 = C['YC'] - C['MW'] / 2, C['YC'] + C['MW'] / 2
    for sgn, ye in ((-1, ym0), (1, ym1)):
        post = box(xm0 - 1.2, xm1 + 1.2, min(ye - sgn * 1.2, ye + sgn * 2.3), max(ye - sgn * 1.2, ye + sgn * 2.3),
                   G['WALL'] - 0.01, C['Z0'] + 9.0)
        groove = box(xm0 - 0.15, xm1 + 0.15, min(ye - sgn * 1.5, ye + sgn * 0.3), max(ye - sgn * 1.5, ye + sgn * 0.3),
                     C['Z0'], 30)
        wanne = wanne.fuse(post.cut(groove))
    for xs in (xp1 + 1.0, G['W'] / 2 - G['WALL'] - 2.2):
        wanne = wanne.cut(box(xs, xs + 1.2, ym0 + 4.0, ym1 - 4.0, -1, G['WALL'] + 0.5))
    for zs in (4.0, 7.0, 10.0):
        wanne = wanne.cut(box(G['W'] / 2 - G['WALL'] - 1, G['W'] / 2 + 1, ym0 + 2.0, ym1 - 2.0, zs, zs + 1.2))
    deckel = deckel.cut(box(G['W'] / 2 - G['WALL'] - 1, G['W'] / 2 + 1, ym0 + 4.0, ym1 - 2.0, zf + 1.1, zf + 2.3))
    S['Klima_Modul_Option'] = box(xm0, xm1, ym0, ym1, C['Z0'], C['Z0'] + C['MH']).fuse(
        box(xm1, xm1 + C['PART_F'], ym0 + 1.5, ym1 - 1.5, C['Z0'] + 1.5, C['Z0'] + C['MH'] - 1.5)).fuse(
        box(xm0 - C['PART_B'], xm0, ym0 + 1.5, ym1 - 1.5, C['Z0'] + 1.5, C['Z0'] + C['MH'] - 1.5))
    # ---- Montierbarkeit: Deckel senkrecht aufsetzbar -> nichts vom Deckel unter der ueberhaengenden Wannen-Facette
    #      (+3 mm: Steg vorne ganz weg, sonst streift er beim Aufsetzen Lichtschacht und Facetten-Stirnfasen)
    S['_Y_SHADOW'] = (zf - g2) - (G['H'] - G['FACET']) + G['WALL'] * math.sqrt(2) - G['D'] / 2 + 0.3 + 3.0
    deckel = deckel.cut(box(-big, big, -big, S['_Y_SHADOW'], -1, zf + g2))
    S['Wanne_grau'] = wanne.removeSplitter()
    S['Wanne_grau_OTG'] = wanne.cut(win_otg).removeSplitter()
    # Phase 5: Der Steg-Schnitt am Lichtschacht liess einen Splitter (0.07 mm3, 0.01 mm dick, z 14.15) als zweiten Koerper
    # stehen -> nur Koerper > 1 mm3 behalten (Pruefung in checks(): Anzahl Koerper je Druckteil).
    sl = [so for so in deckel.Solids if so.Volume > 1.0]
    if len(sl) != len(deckel.Solids):
        log('Deckel_blau: %d Splitter < 1 mm3 entfernt (%.3f mm3)' % (len(deckel.Solids) - len(sl),
            sum(so.Volume for so in deckel.Solids if so.Volume <= 1.0)))
        deckel = sl[0] if len(sl) == 1 else Part.makeCompound(sl)
    S['Deckel_blau'] = deckel          # removeSplitter() macht diesen Koerper ungueltig (OCC 7.6) -> weglassen
    S['RTC_Modul_Option'] = box(rx0, rx1, ry0, ry1, ztop - R['H'], ztop)
    # ---- Pi + Schrauben + Einsaetze
    S.update(pi_model())
    for i, (X, Y) in enumerate(PI['HOLES']):
        x, y = px(X), py(Y)
        z_head = T['CB_H']
        S['Schraube_M2p5_%d' % i] = cyl(T['HEAD_D'] / 2, z_head - T['HEAD_K'], z_head, x, y).fuse(
            cyl(1.25, z_head, z_head + T['SCREW_L'], x, y))
        S['Einsatz_%d' % i] = cyl(1.75, ZP + 0.2, ZP + 4.2, x, y).cut(cyl(1.25, 0, 30, x, y))
    for i, (fx, fy) in enumerate([(-16, -8), (16, -8), (-16, 8), (16, 8)]):
        S['Fuss_%d' % i] = cyl(4.0, -1.5, 0.0, fx, fy)
    # Leitungsbuendel (Platzhalter, 4 x Litze AWG28, ANNAHME Ø 2.6): Pin 5 senkrecht hoch, nach hinten, durch den Kanal
    rb = C['BUNDLE_D'] / 2
    xw, yw = px(pin_xy(5)[0]), py(pin_xy(5)[1])
    zh = C['HOLE_Z']
    wire = cyl(rb, ZP, zh, xw, yw).fuse(Part.makeSphere(rb, V(xw, yw, zh)))
    wire = wire.fuse(Part.makeCylinder(rb, C['HOLE_Y'] - yw, V(xw, yw, zh), V(0, 1, 0)))
    wire = wire.fuse(Part.makeSphere(rb, V(xw, C['HOLE_Y'], zh)))
    wire = wire.fuse(Part.makeCylinder(rb, xp1 + 1.0 - xw, V(xw, C['HOLE_Y'], zh), V(1, 0, 0)))
    S['Leitungen_Klima'] = wire
    global PINS_XY
    PINS_XY = [(n, px(pin_xy(n)[0]), py(pin_xy(n)[1])) for n in (1, 3, 5, 6, 9)]
    S.pop('_Y_SHADOW')
    return S


ASSY_SKIP = ('Wanne_grau_OTG',)


def checks(S):
    log('=== fluidi Gateway G1 v4 (Raspberry Pi Zero 2 W) ===')
    log('Aussenmasse %.0f x %.0f x %.0f mm (B x T x H), Wand %.1f, Fuge z %.2f ... %.2f'
        % (G['W'], G['D'], G['H'], G['WALL'], G['Z_FUGE'] - G['GAP'] / 2, G['Z_FUGE'] + G['GAP'] / 2))
    log('Pi: X=0 bei x %.1f, Y=0 bei y %.1f, PCB z %.1f ... %.1f (ANNAHME T %.1f)' % (XR, YB, PI['Z0'], ZP, PI['T']))
    A = {k: v for k, v in S.items() if k not in ASSY_SKIP}
    allowed = set()
    for i in range(4):
        allowed |= {('Deckel_blau', 'Einsatz_%d' % i), ('Einsatz_%d' % i, 'Schraube_M2p5_%d' % i)}
    allowed |= {('LED_Platine', 'LED_RGB'), ('Pi_PCB', 'Pi_Bauteile_oben'), ('Pi_PCB', 'Pi_Bauteile_unten'),
                ('Pi_Bauteile_oben', 'microSD_Karte'), ('Deckel_blau', 'RTC_Modul_Option'),
                ('Pi_PCB', 'Leitungen_Klima'), ('Pi_Bauteile_oben', 'Leitungen_Klima')}   # Leitungen in die Loetaugen
    hits = collide(A, allowed)
    for a, b, vol in hits:
        bb = A[a].common(A[b]).BoundBox
        log('   Lage %s/%s: x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f' % (a, b, bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    log('1 Kollisionen montiert: %s' % ('keine' if not hits else ', '.join('%s/%s %.3f' % h for h in hits)))
    # RTC-Modul sitzt im Rahmen (Rahmen-Innenmass 0.2 groesser) -> Volumenueberschneidung muss 0 sein
    v = S['Deckel_blau'].common(S['RTC_Modul_Option']).Volume
    log('   RTC-Modul im Rahmen: Ueberschneidung %.3f mm3' % v)
    # Phase 5: Modulmasse aus den Quellen gegen den Bauraum
    R = RTC
    ztop = G['H'] - G['WALL']
    rb = S['RTC_Modul_Option'].BoundBox
    below = S['Pi_Bauteile_oben'].common(box(rb.XMin, rb.XMax, rb.YMin, rb.YMax, 0, 30))
    zpi = below.BoundBox.ZMax if below.Volume > 1e-6 else ZP
    log('13 RTC Adafruit 4282 (21.3 x 20.0 x 13.6 inkl. Buchsenleiste, Produktseite Z. 130): Grundriss im Rahmen %.1f x %.1f '
        'unter der Decke z %.1f; hoechstes Pi-Bauteil darunter z %.1f -> Bauraum %.1f mm. Mit Buchsenleiste (13.6) passt es NICHT '
        '(und der Pi hat keine Stiftleiste); ohne Leiste zulaessig bis %.1f mm Modulhoehe (am Modul messen, ANNAHME bis dahin). '
        'Abstand zu Klima-Litzen %.1f, HDMI %.1f mm'
        % (R['LX'] + 0.4, R['LY'] + 0.4, ztop, zpi, ztop - zpi, R['H'], S['RTC_Modul_Option'].distToShape(S['Leitungen_Klima'])[0],
           S['RTC_Modul_Option'].distToShape(pbox(*PARTS['HDMI'][:4], ZP, ZP + PARTS['HDMI'][4]))[0]))
    C = CLIMA
    ci = (G['W'] / 2 - G['WALL'] - (X_PART + C['WALL']), G['D'] - 2 * G['WALL'], G['H'] - 2 * G['WALL'])
    fits = []
    for o in ((20.0, 40.0), (40.0, 20.0)):
        for ax_ in ('xy', 'yz', 'xz'):
            dims = {'xy': (o[0], o[1], 1.6), 'yz': (1.6, o[0], o[1]), 'xz': (o[0], 1.6, o[1])}[ax_]
            if all(d + 0.4 <= c for d, c in zip(dims, ci)):
                fits.append(ax_)
    log('14 Grove SHT41 (20 x 40 mm, docs/references/Seeed_Grove-SHT4x_Wiki_Auszug_2026-11-08.txt; Hoehe nicht angegeben, '
        'hier nur Platine 1.6): Klimakammer innen %.1f x %.1f x %.1f (x, y, z) -> %s'
        % (ci[0], ci[1], ci[2], ('passt (%s)' % ', '.join(fits)) if fits else 'passt in KEINER Lage (40 > %.1f innen)' % max(ci)))
    # Mindestabstaende
    def d(a, b):
        return S[a].distToShape(S[b])[0]
    log('2 Mindestabstaende (Spiel, Ziel >= 0.3 FDM bzw. >= 1.0 zu Waenden):')
    inner_wall = shell_solid(0).cut(shell_solid(G['WALL']))
    for k in ('Pi_PCB', 'Pi_Bauteile_oben', 'Pi_Bauteile_unten', 'microSD_Karte', 'LED_Platine', 'RTC_Modul_Option',
              'Klima_Modul_Option', 'Leitungen_Klima'):
        log('   %-18s - Wanne %.2f   - Deckel %.2f' % (k, d(k, 'Wanne_grau'), d(k, 'Deckel_blau')))
    log('   (Pi_PCB 0.00 = Auflage auf Abstandshaltern / Niederhalterrohren, gewollt; Bauteilhuelle 0.20 nur innerhalb')
    log('    des Freihaltekreises Ø 6 der Zeichnung, dort keine Bauteile)')
    log('   Pi_PCB - Wand (ohne Freistiche) %.2f' % S['Pi_PCB'].distToShape(inner_wall)[0])
    for k in ('LED_Platine', 'LED_RGB'):
        log('   %-18s - Pi_Bauteile_oben %.2f  - Pi_PCB %.2f' % (k, d(k, 'Pi_Bauteile_oben'), d(k, 'Pi_PCB')))
    # Rohre/Abstandshalter zu den Aussenwaenden (gleichmaessige Wand, kein Masseanhaeufung)
    dmin = 99
    for X, Y in PI['HOLES']:
        t = cyl(TUBE['R'], G['WALL'], G['Z_FUGE'] + 0.5, px(X), py(Y)).common(S['Deckel_blau'])
        dmin = min(dmin, t.distToShape(S['Wanne_grau'])[0])
    log('3 Niederhalterrohre (R %.1f, Deckel) zur Wanne min. %.2f mm (keine Anbindung an die Wand) -> Wand ueberall %.1f mm' % (TUBE['R'], dmin, G['WALL']))
    log('   Rohr Ø %.1f innerhalb Freihaltekreis Ø %.1f der Zeichnung: %s' % (2 * TUBE['R'], PI['KEEP_D'],
        'ja' if 2 * TUBE['R'] <= PI['KEEP_D'] else 'NEIN'))
    eng = ZP + TUBE['INS_L'] - 0.4
    tip = TUBE['CB_H'] + TUBE['SCREW_L']
    log('   Schraube M2.5 x %.0f: Spitze z %.1f, Einsatz z %.1f ... %.1f -> Einschraubtiefe %.1f mm' %
        (TUBE['SCREW_L'], tip, ZP + 0.2, ZP + 4.2, min(tip, ZP + 4.2) - (ZP + 0.2)))
    # Stecker
    zc = ZP + USB['ZC_DZ']
    pw, ph = USB['PLUG']
    face = py(PARTS['USB_PWR'][2])
    for nm, X, wn in (('PWR', USB['PWR_X'], 'Wanne_grau'), ('OTG', USB['OTG_X'], 'Wanne_grau_OTG')):
        plug = box(px(X) - pw / 2, px(X) + pw / 2, face + 0.2, G['D'] / 2 + 15, zc - ph / 2, zc + ph / 2)
        log('4 Micro-USB-%s: Buchsenfront %.1f mm hinter Aussenflaeche, Umspritzung %.1f x %.1f -> Spiel zur %s %.2f mm'
            % (nm, G['D'] / 2 - face, pw, ph, wn, plug.distToShape(S[wn])[0]))
    # Header-Optionen
    hd = pbox(HEADER['X0'], HEADER['X1'], HEADER['Y0'], HEADER['Y1'], ZP, ZP + HEADER['H'])
    hh = [k for k in ('Deckel_blau', 'LED_Platine', 'Wanne_grau') if hd.common(S[k]).Volume > 1e-3]
    log('5 GPIO: Auftraggeber-Pi ohne Stiftleiste, Leitungen direkt in die Loetaugen (Lage aus Zeichnung, Pin 1 = Quadratpad):')
    for n, x, y in PINS_XY:
        log('   Pin %d  X %.2f Y %.2f  -> x %.2f y %.2f' % (n, pin_xy(n)[0], pin_xy(n)[1], x, y))
    (x1, y1), (x9, y9) = pin_xy(1), pin_xy(9)
    h5 = pbox(x1 - 1.27, x9 + 1.27, y1 - 1.27, y1 + 1.27, ZP, ZP + 2.5).fuse(
        pbox(x1 - 1.27, x9 + 1.27, y1 - 1.27, y1 + 1.27, ZP + 2.5, ZP + 2.5 + 14.0))
    hk = [k for k in ('Deckel_blau', 'LED_Platine', 'Wanne_grau', 'Leitungen_Klima') if h5.common(S[k]).Volume > 1e-3]
    log('   Option 1x5-Stiftleiste gerade (Pins 1-3-5-7-9, Pin 7 frei) + Buchsengehaeuse, Huelle 2.5 + 14 mm hoch (ANNAHME):'
        ' Kollision mit %s' % (', '.join(hk) if hk else 'nichts'))
    log('   Option gewinkelte Leiste: Stifte zeigen in Y (zur Front) -> Steckergehaeuse ~14 mm passt nicht (Front %.1f mm)'
        % (py(PI['B']) + G['D'] / 2 - G['WALL']))
    log('   volle 40-pol. Leiste (8.5 mm, ANNAHME): Kollision mit %s -> nicht vorgesehen' % (', '.join(hh) if hh else 'nichts'))
    # Antenne/Metall
    log('6 Metall im Gehaeuse: 4 Schrauben/Einsaetze nur in den 4 Befestigungsbohrungen des Pi (Herstellerbohrungen),')
    log('   LED-Platine (Kupfer) Abstand zur Pi-Platine %.1f mm; keine weiteren Metallteile. Lage der Onboard-Antenne'
        % d('LED_Platine', 'Pi_PCB'))
    log('   ist in den offiziellen Unterlagen nicht angegeben -> RSSI offen/geschlossen messen (PROTOTYP-PRUEFUNG).')
    for k in ('Wanne_grau', 'Wanne_grau_OTG', 'Deckel_blau', 'Fenster_transluzent'):
        log('7 %-20s %.1f cm3 -> %.1f g ASA' % (k, S[k].Volume / 1000, S[k].Volume * 1.07e-3))
    Aa = shell_solid(0).Area * 1e-6
    for P in (1.0, 2.0, 3.0):
        log('8 Verlustleistung %.1f W: dT Gehaeuse ~ %.0f K (h = 8 W/m2K, A = %.4f m2, ANNAHME; Leistung Pi nicht im '
            'Product Brief)' % (P, P / (8 * Aa), Aa))
    # Montierbarkeit (senkrechtes Einlegen/Aufsetzen)
    W_ = S['Wanne_grau'].fuse(S['LED_Platine'])
    res = []
    for t in (0.3, 1, 2, 4, 8, 15):
        P_ = S['Pi_PCB'].fuse(S['Pi_Bauteile_oben']).fuse(S['Pi_Bauteile_unten'])
        P_.translate(V(0, 0, t))
        D_ = S['Deckel_blau'].copy(); D_.translate(V(0, 0, t))
        cD = D_.common(W_.fuse(S['Klima_Modul_Option']))
        res.append((t, P_.common(W_).Volume, cD.Volume))
        if cD.Volume > 1e-3:
            bb = cD.BoundBox
            log('   Deckel t %.1f: x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f' % (t, bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    log('10 Montage senkrecht: Pi in Wanne (mit Lichtschacht/LED-Platine) und Deckel auf Wanne, Ueberschneidung beim '
        'Anheben um t: ' + ', '.join('t %.1f: Pi %.2f / Deckel %.2f mm3' % r for r in res))
    # Klimakammer
    C = CLIMA
    sip = pbox(19.8, 34.9, 6.5, 21.6, ZP, ZP + 1.4)
    pwr = pbox(*PARTS['USB_PWR'][:4], ZP, ZP + 3)
    km = S['Klima_Modul_Option']
    log('11 Klimakammer rechts: Innenraum x %.1f ... %.1f (%.1f mm), Trennwand %.1f mm + %.1f mm Luftspalt (SD-Raum) zum Pi;'
        % (X_PART + C['WALL'], G['W'] / 2 - G['WALL'], C['WI'], C['WALL'], PI['SD_SPACE']))
    log('   Modul (ANNAHME max. %.0f x %.0f mm, steht in Nuten, Sensorseite zur Stirnwand): Abstand zu SiP %.1f mm, zu '
        'Micro-USB-PWR (Einspeisung, Regler vermutl. nahe) %.1f mm, zur Pi-Platine %.1f mm'
        % (C['MW'], C['MH'], km.distToShape(sip)[0], km.distToShape(pwr)[0], km.distToShape(S['Pi_PCB'])[0]))
    log('   Zuluft 2 Bodenschlitze + 3 Stirnschlitze (Wanne), Abluft 1 Stirnschlitz (Deckel); Kabelkanal Ø %.1f x %.1f mm '
        'bei y %.1f z %.1f, vergossen' % (C['HOLE_D'], C['BOSS_L'] + C['WALL'], C['HOLE_Y'], C['HOLE_Z']))
    log('12 Druckteile, Anzahl Koerper (Soll je 1): %s' % ', '.join('%s %d' % (k, len(S[k].Solids)) for k in PRINT))
    nslots = 5
    log('9 Lueftung: %d Bodenschlitze 1.2 mm unter dem SiP, 4 Kaminschlitze 1.2 x %.1f mm in der Deckel-Rueckwand'
        % (nslots, G['H'] - 1.8 - G['Z_FUGE'] - 1.6))


PRINT = {'Wanne_grau': ('wanne_grau', [], 'ASA Warmgrau hell'),
         'Wanne_grau_OTG': ('wanne_grau_otg', [], 'ASA Warmgrau hell (Variante mit OTG-Ausschnitt)'),
         'Deckel_blau': ('deckel_blau', [((1, 0, 0), 180)], 'ASA Hellblau'),
         'Fenster_transluzent': ('fenster_tropfen_gw', [((1, 0, 0), 135)], 'ASA/PETG natur transluzent')}

COLORS = {'Wanne_grau': '#B9B5AC', 'Deckel_blau': '#59ADDD', 'Fenster_transluzent': '#7CFC9A',
          'Pi_PCB': '#1F6B3A', 'Pi_Bauteile_oben': '#8A8F94', 'Pi_Bauteile_unten': '#5E6A60', 'microSD_Karte': '#202020',
          'LED_Platine': '#2E5E2E', 'LED_RGB': '#F0F0F0', 'RTC_Modul_Option': '#3060A0',
          'Klima_Modul_Option': '#7A3FA0', 'Leitungen_Klima': '#D04020'}


def preview(S, path):
    """Kontrollansicht ohne GUI: Netz -> eigener Z-Buffer (numpy) -> matplotlib-PNG."""
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.colors import to_rgb

    def tris(shape, dx=0.0, dz=0.0):
        pts, fac = shape.tessellate(0.08)
        P = np.array([[p.x + dx, p.y, p.z + dz] for p in pts])
        return P[np.array(fac)] if len(fac) else np.zeros((0, 3, 3))

    def view(ax, items, az, el, title, res=10.0):
        """Z-Buffer-Rasterung (res Pixel/mm), Lambert + Umgebungslicht, Kanten durch Tiefenspruenge."""
        a, e = math.radians(az), math.radians(el)
        right = np.array([math.cos(a), math.sin(a), 0.0])
        fwd = np.array([math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)])   # zum Betrachter
        up = np.cross(fwd, right)
        light = fwd * 0.55 + up * 0.7 + right * 0.35
        light /= np.linalg.norm(light)
        allT = np.concatenate([T for T, c in items if len(T)])
        u_all, v_all = allT.reshape(-1, 3) @ right, allT.reshape(-1, 3) @ up
        u0, v0 = u_all.min() - 2, v_all.min() - 2
        Wp, Hp = int((u_all.max() + 2 - u0) * res), int((v_all.max() + 2 - v0) * res)
        zb = np.full((Hp, Wp), -1e9)
        img = np.ones((Hp, Wp, 3))
        for T, c in items:
            if len(T) == 0:
                continue
            nrm = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
            ln = np.linalg.norm(nrm, axis=1); ln[ln == 0] = 1
            nrm = nrm / ln[:, None]
            base = np.array(to_rgb(c))
            sh = 0.30 + 0.70 * np.abs(nrm @ light)
            U = (T @ right - u0) * res
            Vv = (T @ up - v0) * res
            Z = T @ fwd
            for k in range(len(T)):
                x, y, z = U[k], Vv[k], Z[k]
                xa, xb = int(max(x.min(), 0)), int(min(x.max() + 1, Wp))
                ya, yb = int(max(y.min(), 0)), int(min(y.max() + 1, Hp))
                if xb <= xa or yb <= ya:
                    continue
                gx, gy = np.meshgrid(np.arange(xa, xb) + 0.5, np.arange(ya, yb) + 0.5)
                d = (y[1] - y[2]) * (x[0] - x[2]) + (x[2] - x[1]) * (y[0] - y[2])
                if abs(d) < 1e-12:
                    continue
                l0 = ((y[1] - y[2]) * (gx - x[2]) + (x[2] - x[1]) * (gy - y[2])) / d
                l1 = ((y[2] - y[0]) * (gx - x[2]) + (x[0] - x[2]) * (gy - y[2])) / d
                l2 = 1 - l0 - l1
                m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
                if not m.any():
                    continue
                zz = l0 * z[0] + l1 * z[1] + l2 * z[2]
                sub = zb[ya:yb, xa:xb]
                m &= zz > sub
                sub[m] = zz[m]
                img[ya:yb, xa:xb][m] = np.clip(base * sh[k], 0, 1)
        # Konturen: Tiefenspruenge > 0.8 mm dunkel
        dz = np.zeros_like(zb)
        dz[1:, :] = np.maximum(dz[1:, :], np.abs(zb[1:, :] - zb[:-1, :]))
        dz[:, 1:] = np.maximum(dz[:, 1:], np.abs(zb[:, 1:] - zb[:, :-1]))
        img[dz > 0.8] *= 0.45
        ax.imshow(img[::-1], interpolation='lanczos')
        ax.axis('off'); ax.set_title(title, fontsize=9)

    closed = ['Wanne_grau', 'Deckel_blau', 'Fenster_transluzent']
    T = {k: tris(S[k]) for k in COLORS}
    fig, axs = plt.subplots(2, 2, figsize=(13, 9), dpi=130)
    view(axs[0, 0], [(T[k], COLORS[k]) for k in closed], 30, 25, 'G1 v4 vorne (Facette, Tropfen-LED an der Farbfuge, Logo)')
    view(axs[0, 1], [(T[k], COLORS[k]) for k in closed], 150, 25, 'G1 v4 hinten rechts (Micro-USB PWR, Kaminschlitze, Klimakammer-Schlitze)')
    inside = ['Wanne_grau', 'Pi_PCB', 'Pi_Bauteile_oben', 'microSD_Karte', 'LED_Platine', 'LED_RGB', 'Fenster_transluzent',
              'Klima_Modul_Option', 'Leitungen_Klima']
    view(axs[1, 0], [(T[k], COLORS[k]) for k in inside], 25, 50, 'Wanne: Pi Zero 2 W (Huellmodell), rechts Klimakammer mit Modul, Leitungen rot')
    lid = tris(S['Deckel_blau'].copy().rotate(V(0, 0, 0), V(1, 0, 0), 180))
    rtc = tris(S['RTC_Modul_Option'].copy().rotate(V(0, 0, 0), V(1, 0, 0), 180))
    view(axs[1, 1], [(lid, COLORS['Deckel_blau']), (rtc, COLORS['RTC_Modul_Option'])], 25, 55,
         'Deckel innen (Niederhalterrohre mit Einsatz M2.5, Steg, Lichtschacht, RTC-Rahmen)')
    fig.suptitle('fluidi Gateway G1 v4 - %.0f x %.0f x %.0f mm - Raspberry Pi Zero 2 W (Kontrollansicht, kein Rendering)'
                 % (G['W'], G['D'], G['H']), fontsize=11)
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def main():
    os.makedirs(os.path.join(OUT, 'print'), exist_ok=True)
    S = build()
    checks(S)
    doc = App.newDocument('fluidi_gateway_pi')
    for k, s in S.items():
        o = doc.addObject('Part::Feature', k); o.Shape = s
        if k in ASSY_SKIP:
            o.Visibility = False
    doc.recompute()
    fc = os.path.join(OUT, 'fluidi_gateway_pi.FCStd')
    doc.saveAs(fc)
    Part.export([o for o in doc.Objects if o.Name not in ASSY_SKIP], os.path.join(OUT, 'fluidi_gateway_pi_assembly.step'))
    for k, (fn, rot, mtl) in PRINT.items():
        export_part(S[k], os.path.join(OUT, 'print', fn), rot)
    App.closeDocument(doc.Name)
    for f in os.listdir(OUT):
        if f.endswith('.FCBak'):
            os.remove(os.path.join(OUT, f))
    preview(S, os.path.join(OUT, 'preview.png'))
    open(os.path.join(OUT, 'check_gateway_pi.txt'), 'w').write('\n'.join(LOG) + '\n')
    print('gespeichert:', fc)


main()
