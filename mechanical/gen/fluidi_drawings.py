# -*- coding: utf-8 -*-
"""fluidi - Fertigungszeichnungen Sensor P3 (Rev C, V-K/M-4, P5-M1) und Gateway G1 v4, FreeCAD 0.21.2 headless.

Lauf:     freecadcmd mechanical/gen/fluidi_drawings.py            (optional FLUIDI_DRAW_PNG=<Ordner> fuer PNG-Vorschauen,
                                                                   FLUIDI_DRAW_ONLY=FL-S-01,FL-S-02 fuer einzelne Blaetter)
Eingaben: mechanical/sensor/fluidi_sensor.FCStd (fluidi_sensor.py), mechanical/sensor/fluidi_sensor_mit_pcb.step
          (fluidi_pcb_collision.py), mechanical/gateway_pi/fluidi_gateway_pi.FCStd (fluidi_gateway_pi.py),
          Masse/Parameter fluidi_params.py bzw. Kopf von fluidi_gateway_pi.py.
Ausgabe:  mechanical/drawings/<Sachnummer>_<teil>.pdf, mechanical/drawings/drawings_check.txt (Pruefprotokoll:
          jede Masszahl mit Messpunkten, Abstand Messpunkt <-> Geometrie).
Methode und Grenzen: fluidi_drawing_lib.py (Kopf).
"""
import datetime
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ['FLUIDI_NO_MAIN'] = '1'

import FreeCAD as App          # noqa: E402
import Part                    # noqa: E402

import fluidi_params as FP     # noqa: E402
import fluidi_sensor as FS     # noqa: E402  (nur PRINT-Tabelle; build() wird nicht ausgefuehrt)
from fluidi_drawing_lib import Sheet, View, V, git_stand, fmt  # noqa: E402

REPO = FP.REPO
OUT = os.path.join(REPO, 'mechanical', 'drawings')
PNGD = os.environ.get('FLUIDI_DRAW_PNG')
ONLY = [s for s in os.environ.get('FLUIDI_DRAW_ONLY', '').split(',') if s]
H, Z, PCB, CAP, BTN = FP.HEAD, FP.Z, FP.PCB, FP.CAP, FP.BTN
STAND = 'Rev %s (%s), V-K/M-4 (D-019, D-023), P5-M1/M3; git %s' % (
    FP.REV, FP.REV_DATE, git_stand(REPO, ['mechanical/gen', 'mechanical/sensor', 'mechanical/gateway_pi']))
DATE = datetime.date.today().isoformat()
ALL_CHECKS = []

ASA = 'Bambu ASA (BambuLab_ASA_TechnicalDataSheet_V2.0.pdf), HDT 92 °C'
NOTE_COMMON = [
    '1  Masse in mm, Dezimalpunkt. Nennmasse = CAD-Modell; alle Masszahlen werden aus Modellpunkten berechnet (drawings_check.txt).',
    '2  Allgemeintoleranz Druckteil ±0.1 mm (ANNAHME FDM P1S 0.4-mm-Düse, wie Toleranzkette check_sensor.txt 2b); ISO 2768 gilt nicht.',
    '3  Passungen nicht durch Geometrieänderung, sondern über Passprobe und XY-Lochkompensation einstellen (PRINT_SETTINGS.md Kap. 4).',
    '4  Profil PRINT_SETTINGS.md Kap. 2 (ASA 260/90 °C, 4 Wände, 100 % Füllung), stützenfrei; Naht hinten, nicht auf Dichtflächen.',
    '5  (Masszahl im Rundrahmen) = Prüfmass (Funktionsmass, am Muster messen). ——·—— breit = Dichtfläche / Funktionsfläche.',
]


def load_sensor():
    d = App.openDocument(os.path.join(REPO, 'mechanical', 'sensor', 'fluidi_sensor.FCStd'))
    S = {o.Name: o.Shape.copy() for o in d.Objects}
    App.closeDocument(d.Name)
    return S


def sheet(fmt_, number, title, subtitle, material, scale, orient, notes=(), source=''):
    return Sheet(fmt_, number, title, subtitle, material, scale, orient, STAND,
                 source or 'mechanical/sensor/fluidi_sensor.FCStd  <-  mechanical/gen/fluidi_sensor.py, fluidi_params.py',
                 NOTE_COMMON + list(notes), date=DATE)


def finish(sh, fname):
    os.makedirs(OUT, exist_ok=True)
    pdf = os.path.join(OUT, fname + '.pdf')
    png = os.path.join(PNGD, fname + '.png') if PNGD else None
    ALL_CHECKS.extend(sh.checks)
    sh.save(pdf, png)
    nbad = sum(1 for c in sh.checks if not c[3])
    print('%-40s %3d Masse, %d Messpunkt-Fehler' % (fname, len(sh.checks), nbad))
    for c in sh.checks:
        if not c[3]:
            print('   FEHLER %s  max d %.3f' % (c[1], c[4]))


# ============================================================================================ Sensor: Huelse
def d_huelse(S):
    sl = S['Huelse_grau']
    sh = sheet('A3', 'FL-S-01', 'Hülse grau (Sichtschale + Zellfach)', 'Batteriefach, Dichtflächen der 2 O-Ringe AS568-019, Sondenschlitz, Furchlippe M2',
               'ASA (Bambu, TDS V2.0), Warmgrau hell #B9B5AC', '2:1, Z 10:1',
               'stehend, Boden auf dem Bett, Mausohren 3 mm; Höhe 44.7; Logo-Relief auf senkrechter Wand',
               notes=['6  Logo-Relief 0.25 erhaben (Front), Warnsymbol innen Rückwand 0.3 vertieft (S3-W4): Form nach CAD, nicht bemasst.'])
    s = 2.0
    W2, D, I = H['W'] / 2, H['D'], FP.SLEEVE_IN
    fr = View(sh, sl, 'front', s).place(100, 185).draw('Vorderansicht', 14)
    aa = View(sh, sl, 'left', s, section=(0, 0, 0)).place(200, 185).draw('A–A', 20)
    bk = View(sh, sl, 'back', s).place(310, 185).draw('Ansicht B (von hinten)', 8)
    tp = View(sh, sl, 'top', s).place(100, 85).draw('Draufsicht', 14)
    z = View(sh, sl, 'left', 10.0, section=(0, 0, 0), clip_model=(-7.0, -1.4, -0.4, 2.2)).place(185, 82).draw('Einzelheit Z (aus A–A, 10:1)', 12)
    fr.cutline((0, 0, -1), (0, 0, H['RIM_TOP'] + 1), 'A', (1, 0, 0))
    y0 = 6.5
    # Vorderansicht
    fr.dim((-W2, y0, 0), (W2, y0, 0), 'h', fr.bottom(1), 'Breite', sl)
    fr.dim((W2, y0, 0), (W2, y0, Z['SLEEVE_TOP']), 'v', fr.right(1), 'Hoehe Huelse bis Sichtfuge', sl, frame=True)
    rx = W2 - H['SKIRT_T'] - 0.1
    fr.dim((W2, y0, 0), (rx, y0, H['RIM_TOP']), 'v', fr.right(2), 'Hoehe mit Dachziegelrand', sl)
    D_ = FP.DROP
    fr.note((D_['X'], 0, D_['ZC'] - D_['R'] - D_['NOTCH_GAP']), 'Kerbe Tropfen r %s (Fenster r %s + %s),\nMitte z %s, oben offen'
            % (fmt(D_['R'] + D_['NOTCH_GAP']), fmt(D_['R']), fmt(D_['NOTCH_GAP']), fmt(D_['ZC'])), -30, -10,
            shape=sl, what='Kerbe Unterkante auf Geometrie')
    fr.note((FP.LOGO['W'] / 2 - 1.0, 0, FP.LOGO['ZC']), 'Logo-Relief 0.25, Breite %s, Mitte z %s' % (fmt(FP.LOGO['W']), fmt(FP.LOGO['ZC'])),
            -20, -50, dot=True)
    # A-A (Schnitt x = 0, von links: Bild rechts = -y)
    aa.dim((0, 0, 0), (0, D, 0), 'h', aa.bottom(1), 'Tiefe', sl)
    aa.dim((0, FP.SLOT['Y0'], 0), (0, FP.SLOT['Y1'], 0), 'h', aa.bottom(2), 'Sondenschlitz Breite y', sl, frame=True)
    aa.dim((0, 0, 12), (0, I['Y0'], 12), 'h', aa.box[2] + 24, 'Wand vorne', sl)
    aa.dim((0, I['Y1'], 12), (0, D, 12), 'h', aa.box[2] + 24, 'Wand hinten', sl, tside=-1)
    aa.dim((0, 2.4, 0), (0, 2.4, H['FLOOR']), 'v', aa.right(1), 'Bodendicke', sl, frame=True)
    zc0, zc1 = Z['COL_G0'], Z['COL_G1']
    zs0, zs1 = Z['SP_G0'], Z['SP_G1']
    aa.dim((0, I['Y1'], 0), (0, I['Y1'], zc1), 'v', aa.left(1), 'Dichtzone Kragen-O-Ring Oberkante ab Boden', sl)
    aa.dim((0, I['Y1'], 0), (0, I['Y1'], zs1), 'v', aa.left(2), 'Dichtzone Zapfen-O-Ring Oberkante ab Boden', sl)
    aa.dim((0, I['Y1'], 0), (0, I['Y1'], zc0), 'v', aa.left(3), 'Dichtzone Kragen-O-Ring Unterkante', sl)
    aa.dim((0, I['Y1'], 0), (0, I['Y1'], zs0), 'v', aa.left(4), 'Dichtzone Zapfen-O-Ring Unterkante', sl)
    aa.thick_chain((0, I['Y1'], zc0), (0, I['Y1'], zc1), off=0.9)
    aa.thick_chain((0, I['Y1'], zs0), (0, I['Y1'], zs1), off=0.9)
    aa.thick_chain((0, I['Y0'], zc0), (0, I['Y0'], zc1), off=-0.9)
    aa.thick_chain((0, I['Y0'], zs0), (0, I['Y0'], zs1), off=-0.9)
    aa.note((0, I['Y0'], (zs0 + zs1) / 2), 'Dichtflächen O-Ring\n(Naht glätten, 600er)', 16, -14)
    ry0, ry1 = D - H['SKIRT_T'] - 0.1, I['Y1']
    aa.dim((0, ry1, H['RIM_TOP']), (0, ry0, H['RIM_TOP']), 'h', aa.top(1, 4), 'Rand Dicke', sl, tside=1)
    aa.dim((0, ry0, Z['SLEEVE_TOP']), (0, ry0, H['RIM_TOP']), 'v', aa.right(1) - 7 + 7, 'Rand Hoehe', sl, tside=1)
    # Einzelheit Z: Furchlippe
    sc = FP.SCREW
    yh = sc['Y']
    z.dim((0, yh - sc['HOLE_D'] / 2, 1.0), (0, yh + sc['HOLE_D'] / 2, 1.0), 'h', z.top(1, 6), 'Bohrung M2 Freibohrung', sl, pre='Ø')
    z.dim((0, yh - sc['LIP_D'] / 2, 0.2), (0, yh + sc['LIP_D'] / 2, 0.2), 'h', z.bottom(1, 6), 'Furchlippe', sl, pre='Ø', frame=True)
    z.dim((0, yh + sc['LIP_D'] / 2, 0), (0, yh + sc['LIP_D'] / 2, sc['LIP_H']), 'v', z.left(1, 8), 'Lippe Hoehe', sl, frame=True)
    z.dim((0, 0, 0), (0, yh, 0), 'h', z.bottom(2, 6), 'Achse Schraube ab Front', sl,
          chk=[(0, 0, 0), (0, yh - sc['LIP_D'] / 2, 0.2), (0, yh + sc['LIP_D'] / 2, 0.2)])
    z.centerline((0, yh, -0.5), (0, yh, H['FLOOR'] + 0.5))
    # Ansicht B: Ablaufschlitze
    dr = FP.DRAIN
    xc = dr['XC'][2]
    bk.dim((xc - dr['W'] / 2, D, Z['STEP_BACK'] + 0.6), (xc + dr['W'] / 2, D, Z['STEP_BACK'] + 0.6), 'h', bk.S((0, D, 39))[1],
           'Ablaufschlitz Breite', sl)
    bk.dim((xc + dr['W'] / 2, D, Z['STEP_BACK']), (xc + dr['W'] / 2, D, Z['STEP_BACK'] + dr['H']), 'v', bk.left(1), 'Ablaufschlitz Hoehe', sl)
    bk.dim((xc - dr['W'] / 2, D, 0), (xc - dr['W'] / 2, D, Z['STEP_BACK']), 'v', bk.left(2), 'Ablaufschlitz Unterkante', sl, frame=True)
    for k, (a, b) in enumerate(((dr['XC'][1], dr['XC'][2]), (dr['XC'][0], dr['XC'][3]))):
        bk.dim((a, D, Z['STEP_BACK']), (b, D, Z['STEP_BACK']), 'h', bk.S((0, D, 20 - 7 * k))[1], 'Ablaufschlitze Mittenabstand', sl,
               chk=[(a - dr['W'] / 2, D, Z['STEP_BACK'] + 0.5), (a + dr['W'] / 2, D, Z['STEP_BACK'] + 0.5),
                    (b - dr['W'] / 2, D, Z['STEP_BACK'] + 0.5), (b + dr['W'] / 2, D, Z['STEP_BACK'] + 0.5)])
        bk.centerline((a, D, 10 - 7 * k), (a, D, Z['STEP_BACK'] + dr['H'] + 1), ext=0.5)
        bk.centerline((b, D, 10 - 7 * k), (b, D, Z['STEP_BACK'] + dr['H'] + 1), ext=0.5)
    bk.note((0, D, Z['STEP_BACK'] + dr['H']), '4 Schlitze, Unterkante = tiefster Punkt\nder Ablaufstufe der Kappe (z %s)'
            % fmt(Z['STEP_BACK']), 25, -20)
    # Draufsicht (in die Huelse)
    zz = 20.0
    tp.dim((-I['X'], y0, zz), (I['X'], y0, zz), 'h', tp.top(1, 5), 'Innenbreite', sl, frame=True)
    tp.dim((8, I['Y0'], 12), (8, I['Y1'], 12), 'v', tp.right(1), 'Innentiefe', sl, frame=True)
    tp.dim((-W2, y0, 0), (W2, y0, 0), 'h', tp.bottom(1), 'Breite aussen', sl, text='(34)')
    cx, cy, r = I['X'] - I['R'], I['Y0'] + I['R'], I['R']
    tp.radial((cx, cy, zz), r, -40, 'Innenradius', sl, pre='R', length=9)
    tp.dim((-FP.SLOT['X'], 7.4, 1.0), (FP.SLOT['X'], 7.4, 1.0), 'h', tp.bottom(2), 'Sondenschlitz Laenge x', sl, frame=True)
    pl = FS.plan(H['W'], H['D'], H['CF'], H['CB'])
    tp.note(((pl[1][0] + pl[2][0]) / 2, (pl[1][1] + pl[2][1]) / 2, 10), 'Fase %s × 45°' % fmt(H['CF']), 10, -14, shape=sl,
            what='Fase vorne auf Geometrie')
    tp.note(((pl[3][0] + pl[4][0]) / 2, (pl[3][1] + pl[4][1]) / 2, 10), 'Fase %s × 45°' % fmt(H['CB']), 10, 10, shape=sl,
            what='Fase hinten auf Geometrie')
    tp.cross((0, yh, 0), 1.6)
    tp.dim((-W2, 0, 10), (0, yh, 1.0), 'v', tp.left(1), 'Schraubenachse ab Front (y)', sl,
           chk=[(-W2 + H['CF'], 0, 10), (0, yh - sc['HOLE_D'] / 2, 1.0), (0, yh + sc['HOLE_D'] / 2, 1.0)])
    finish(sh, 'FL-S-01_huelse_grau')


# ============================================================================================ Sensor: Kappe
def d_kappe(S):
    k = S['Kappe_blau']
    sh = sheet('A3', 'FL-S-02', 'Kappe blau mit Zapfen, Schott, Biegezunge', 'Elektronikraum (dicht), O-Ring-Nut Zapfen, Ablaufstufe, Tastenführung, Platinenanschlag',
               'ASA (Bambu, TDS V2.0), Hellblau, ohne Russ/Metallpigment', '2:1',
               'kopfüber (Decke auf dem Bett), stützenfrei; Trichter 45° (P5-M1); O-Ring-Nutflanke 1.15 Überhang',
               notes=['6  Tropfenausschnitt r %s, Spitze %s über Mitte (drop2, k %s), Mitte x 0 / z %s; Fenster FL-S-04 eingeklebt (Spalt 0.1).'
                      % (fmt(FP.DROP['R']), fmt(FP.DROP['K'] * FP.DROP['R']), fmt(FP.DROP['K']), fmt(FP.DROP['ZC'])),
                      '7  OFFEN P5-M2: 30°-Keil zwischen Stössel-Finger und Zunge ist im CAD nicht modelliert (beide quaderförmig) -> vor dem Druck klären.'])
    s = 2.0
    fr = View(sh, k, 'front', s).place(85, 200).draw('Vorderansicht', 16)
    aa = View(sh, k, 'left', s, section=(0, 0, 0)).place(178, 200).draw('A–A', 16)
    bb = View(sh, k, 'left', s, section=(BTN['AX_X'], 0, 0)).place(250, 200).draw('B–B', 16)
    cc = View(sh, k, 'left', s, section=(-6.0, 0, 0)).place(330, 200).draw('C–C', 16)
    tp = View(sh, k, 'top', s).place(85, 115).draw('Draufsicht', 14)
    dd = View(sh, k, 'top', s, section=(0, 0, 31.4)).place(178, 95).draw('D–D', 10)
    W2, y0 = H['W'] / 2, 6.5
    fr.cutline((0, 0, 30.3), (0, 0, 58), 'A', (1, 0, 0), ext=12)
    fr.cutline((BTN['AX_X'], 0, 30.3), (BTN['AX_X'], 0, 58), 'B', (1, 0, 0), ext=6)
    fr.cutline((-6.0, 0, 30.3), (-6.0, 0, 58), 'C', (1, 0, 0), ext=1)
    fr.cutline((-17.5, 0, 31.4), (17.5, 0, 31.4), 'D', (0, 0, -1), ext=12)
    L, G, SI = FP.LAND, FP.GROOVE_BOT, FP.SP_IN
    fr.dim((-W2, y0, 50), (W2, y0, 50), 'h', fr.top(1, 9), 'Breite Kappe', k)
    fr.dim((-L['X'], y0, 34.2), (L['X'], y0, 34.2), 'h', fr.bottom(2), 'Zapfen Gleitsitz unter Ablaufstufe', k, frame=True)
    fr.dim((-L['X'] + CAP['RECESS'], y0, 40), (L['X'] - CAP['RECESS'], y0, 40), 'h', fr.bottom(3), 'Zapfen ueber Ablaufstufe (Ruecksprung 0.5)', k)
    fr.dim((W2, y0, H['Z_FUGE']), (10, y0, H['H']), 'v', fr.right(1), 'Hoehe Kappe ab Sichtfuge', k)
    fr.dim((L['X'], y0, Z['BULK0']), (10, y0, H['H']), 'v', fr.right(2), 'Hoehe gesamt', k)
    fr.dim((L['X'], y0, Z['BULK0']), (W2, y0, H['Z_FUGE']), 'v', fr.left(1), 'Zapfen bis Sichtfuge', k,
           chk=[(L['X'], y0, Z['BULK0']), (-W2, y0, H['Z_FUGE'])])
    # A-A
    aa.dim((0, L['Y0'], Z['SP_G0']), (0, L['Y0'], Z['SP_G1']), 'v', aa.right(1), 'O-Ring-Nut Breite', k, frame=True)
    aa.dim((0, L['Y0'], Z['BULK0']), (0, L['Y0'], Z['SP_G0']), 'v', aa.right(1), 'Steg unter Nut', k, tside=-1)
    aa.dim((0, L['Y0'], 31.0), (0, G['Y0'], 32.5), 'h', aa.bottom(1), 'Nuttiefe radial', k, frame=True, tside=1)
    aa.dim((0, L['Y0'], 35.0), (0, L['Y0'] + CAP['RECESS'], 40.0), 'h', aa.bottom(2), 'Ruecksprung Ablauf', k, tside=1)
    aa.dim((0, 13, H['Z_FUGE']), (0, 12.0, H['SLOT_TOP']), 'v', aa.left(1), 'Dachziegelschlitz Tiefe', k, tside=1)
    aa.dim((0, L['Y1'] - CAP['RECESS'], 44.2), (0, H['D'] - H['SKIRT_T'], 44.2), 'h', aa.top(1, 5), 'Schlitz Breite (Ablaufspalt)', k, tside=-1)
    aa.dim((0, H['D'] - H['SKIRT_T'], 44.2), (0, H['D'], 44.2), 'h', aa.top(1, 5), 'Schuerze', k, tside=1)
    aa.dim((0, 10, H['H'] - H['CEIL']), (0, 10, H['H']), 'v', aa.left(1), 'Decke', k, tside=-1)
    aa.dim((0, 8.0, H['H'] - BTN['POCKET_D']), (0, 9.5, H['H']), 'v', aa.right(1), 'Tastentasche Tiefe', k, tside=1)
    aa.dim((0, 0, 51), (0, CAP['CAV_OFF'], 51), 'h', aa.top(2, 5), 'Wand Kappe', k, tside=-1)
    aa.dim((0, 3.0, FP.DROP['ZC'] - 1.6), (0, 3.0, FP.DROP['ZC'] + 1.6), 'v', aa.left(2), 'Lichtschaft-Bohrung', k, pre='Ø', tside=-1)
    aa.note((0, 10.0, 46.5), '45° Trichter (P5-M1),\nbis z %s' % fmt(H['SLOT_TOP'] + CAP['FUNNEL']), 18, 12, shape=k, what='Trichterflaeche auf Geometrie')
    aa.note((0, H['D'] - 0.3, Z['STEP_BACK'] - 0.2 + 0.0), 'Ablaufstufe 6.6° nach hinten:\nz %s (y 0) -> %s (y 13)' % (fmt(Z['STEP_FRONT']), fmt(Z['STEP_BACK'])), 14, -32)
    aa.thick_chain((0, L['Y0'], Z['SP_G0']), (0, L['Y0'], Z['SP_G1']), off=-1.5)
    aa.note((0, G['Y1'], 32.5), 'Nutgrund O-Ring AS568-019\n(Naht nicht in die Nut)', 22, -16)
    # B-B: Stoesselfuehrung
    ax_, ay_ = BTN['AX_X'], BTN['AX_Y']
    zpf = H['H'] - BTN['POCKET_D']
    zcb = zpf - 2.3
    bb.dim((ax_, ay_ - BTN['CB_D'] / 2, 55.0), (ax_, ay_ + BTN['CB_D'] / 2, 55.0), 'h', bb.top(1, 5), 'Senkung Membran', k, pre='Ø', frame=True)
    bb.dim((ax_, ay_ - BTN['BORE_D'] / 2, 53.0), (ax_, ay_ + BTN['BORE_D'] / 2, 53.0), 'h', bb.bottom(1), 'Fuehrung Stoessel', k, pre='Ø', frame=True)
    bb.dim((ax_, ay_ + 2.2, zcb), (ax_, ay_ + 3.7, zpf), 'v', bb.right(1), 'Senkung Tiefe', k, tside=1)
    bb.dim((ax_, ay_ + 1.8, BTN['TUBE_Z0']), (ax_, ay_ + 2.2, zcb), 'v', bb.left(1), 'Rohr bis Senkung', k)
    bb.centerline((ax_, ay_, BTN['TUBE_Z0'] - 2), (ax_, ay_, H['H'] + 1))
    # C-C: Zunge + Platinenanschlag
    T_, ps = FP.TONGUE, FP.PSTOP
    cc.dim((-6, T_['Y0'], 48), (-6, T_['Y1'], 48), 'h', cc.bottom(1), 'Zunge Dicke', k, tside=1)
    cc.dim((-6, 4.0, T_['Z_TIP']), (-6, 7.4, PCB['Z_TOP']), 'v', cc.left(1), 'Zungenspitze bis Platinenanschlag', k)
    cc.dim((-6, PCB['Y_F'], 52.8), (-6, PCB['Y_B'] + ps['CLR_B'], 52.8), 'h', cc.top(1, 5), 'Gabel Weite (ohne Rippe)', k, tside=1)
    cc.dim((-6, 6.0, PCB['Z_TOP'] - ps['FORK']), (-6, 7.4, PCB['Z_TOP']), 'v', cc.right(1), 'Gabel Tiefe', k, tside=1)
    cc.dim((-6, 7.4, PCB['Z_TOP']), (-6, 10, H['H']), 'v', cc.right(2), 'Anschlag unter Oberseite', k, frame=True)
    cc.dim((-6, 0, 50.5), (-6, PCB['Y_F'], 52.8), 'h', cc.bottom(2), 'F-Referenz ab Front (Gabelwange vorn)', k, frame=True,
           chk=[(-6, 0, 50.5), (-6, PCB['Y_F'], 52.8)])
    cc.note((-6, T_['Y1'], 45.5), 'SW1-Betätiger: Spalt %s\n(check_sensor.txt 2b)' % fmt(FP.SW['GAP']), 18, -6)
    # Draufsicht
    bw, bd = BTN['W'] + 2 * BTN['POCKET_GAP'], BTN['D'] + 2 * BTN['POCKET_GAP']
    tp.dim((-bw / 2, BTN['Y'], 57), (bw / 2, BTN['Y'], 57), 'h', tp.top(1, 5), 'Tastentasche Breite', k)
    tp.dim((0, BTN['Y'] - bd / 2, 57), (0, BTN['Y'] + bd / 2, 57), 'v', tp.right(1), 'Tastentasche Tiefe y', k)
    tp.dim((0, 0, 56), (0, BTN['Y'] - bd / 2, 57), 'v', tp.right(2), 'Tastentasche ab Front', k)
    tp.dim((-W2, y0, 50), (ax_, ay_ + BTN['CB_D'] / 2, 55), 'h', tp.bottom(1), 'Stoesselachse ab linker Seite', k,
           chk=[(-W2, y0, 50), (ax_ - BTN['CB_D'] / 2, ay_, 55), (ax_ + BTN['CB_D'] / 2, ay_, 55)], text=fmt(W2 + ax_))
    tp.cross((ax_, ay_, 57), 3.2)
    tp.dim((-W2, 0, 50), (0, H['D'], 50), 'v', tp.left(1), 'Tiefe', k, chk=[(-W2 + 3, 0, 50), (0, H['D'], 50)])
    # D-D (z 31.4): Nutgrund, Vergussraum Schott, Quetschrippen
    dd.dim((-G['X'], y0, 31.4), (G['X'], y0, 31.4), 'h', dd.top(1, 5), 'Nutgrund Breite', k, frame=True)
    dd.dim((0, G['Y0'], 31.4), (0, G['Y1'], 31.4), 'v', dd.right(1), 'Nutgrund Tiefe', k, frame=True)
    dd.radial((G['X'] - G['R'], G['Y0'] + G['R'], 31.4), G['R'], -45, 'Nutgrund Eckradius', k, pre='R', length=7)
    dd.dim((-SI['X'], y0, 31.4), (SI['X'], y0, 31.4), 'h', dd.bottom(1), 'Vergussraum Schott Breite', k)
    dd.dim((0, SI['Y0'], 31.4), (0, SI['Y1'], 31.4), 'v', dd.left(1), 'Vergussraum Tiefe', k)
    xr = CAP['RIB_X'][1]
    dd.dim((xr + CAP['RIB_W'] / 2, SI['Y1'], 31.4), (xr, SI['Y1'] - CAP['RIB_H'], 31.4), 'v', dd.right(2), 'Quetschrippe Hoehe', k, tside=1)
    dd.dim((-L['X'], y0, 31.0), (L['X'], y0, 31.0), 'h', dd.bottom(2), 'Steg unter Nut Breite', k, text='(%s)' % fmt(2 * L['X']))
    dd.note((xr, SI['Y1'] - CAP['RIB_H'], 31.4), '2 Quetschrippen x ±%s, %s breit (M-4)' % (fmt(xr), fmt(CAP['RIB_W'])), -40, -22)
    finish(sh, 'FL-S-02_kappe_blau')


# ============================================================================================ Sensor: Kragen
def d_kragen(S):
    k = S['Kragen']
    sh = sheet('A3', 'FL-S-03', 'Kragen (Vergussform Sondenübergang)', 'O-Ring-Nut Kragen, Platinenschlitz, Tasche U3/C24, Muttertasche M2, Hohlkehle',
               'ASA (Bambu, TDS V2.0), Farbe beliebig (Restmaterial)', '5:1',
               'stehend (Unterseite mit Hohlkehle auf dem Bett); Muttertasche = Brücke 4.7',
               notes=['6  Wird auf der Platine vergossen (Epoxid, Kap. Montage), Mutter ISO 4032 M2 von vorne eingeschoben und eingegossen.'],
               )
    s = 5.0
    L, G, sc = FP.LAND, FP.GROOVE_BOT, FP.SCREW
    fr = View(sh, k, 'front', s).place(120, 222).draw('Vorderansicht', 12)
    cc = View(sh, k, 'top', s, section=(0, 0, 4.8)).place(120, 150).draw('C–C (z 4.8)', 9)
    ee = View(sh, k, 'top', s, section=(0, 0, 2.4)).place(318, 150).draw('D–D (z 2.4, Muttertasche)', 9)
    aa = View(sh, k, 'left', s, section=(0, 0, 0)).place(262, 222).draw('A–A', 12)
    bb = View(sh, k, 'left', s, section=(-7.0, 0, 0)).place(345, 222).draw('B–B (Tasche U3/C24)', 12)
    fr.cutline((0, 0, 0.3), (0, 0, 7.6), 'A', (1, 0, 0), ext=3)
    fr.cutline((-7, 0, 0.3), (-7, 0, 7.6), 'B', (1, 0, 0), ext=3)
    y0 = 6.5
    xs, ys0, ys1 = PCB['W'] / 2 + 0.15, PCB['Y_F'] - 0.15, PCB['Y_B'] + 0.15
    fr.dim((-L['X'], y0, 2.0), (L['X'], y0, 2.0), 'h', fr.top(1, 6), 'Breite', k, frame=True)
    fr.dim((L['X'], y0, Z['COL0']), (L['X'], y0, Z['COL1']), 'v', fr.right(1), 'Hoehe', k)
    fr.dim((L['X'], y0, Z['COL0']), (L['X'], y0, Z['COL_G0']), 'v', fr.right(2), 'Nut Unterkante', k)
    fr.dim((L['X'], y0, Z['COL_G0']), (L['X'], y0, Z['COL_G1']), 'v', fr.right(3), 'Nut Breite', k, frame=True)
    rc = (sc['NUT_S'] + 0.1) / 2 / math.cos(math.pi / 6)
    fr.dim((-rc, 2.0, 2.4), (rc, 2.0, 2.4), 'h', fr.bottom(1), 'Muttertasche Einschub Breite', k, nd=2)
    fr.dim((rc, 2.0, Z['COL_NUT0']), (rc, 2.0, Z['COL_NUT1'] + 0.05), 'v', fr.left(1), 'Muttertasche Hoehe', k, tside=-1)
    fr.dim((L['X'], y0, Z['COL0']), (0, 2.0, Z['COL_NUT0']), 'v', fr.left(2), 'Muttertasche Boden', k,
           chk=[(L['X'], y0, Z['COL0']), (0.5, 3.0, Z['COL_NUT0'])])
    # C-C (z 4.8): Nutgrund, Schlitz, Tasche
    cc.dim((-G['X'], y0, 4.8), (G['X'], y0, 4.8), 'h', cc.top(1, 6), 'Nutgrund Breite', k, frame=True)
    cc.dim((8, G['Y0'], 4.8), (8, G['Y1'], 4.8), 'v', cc.right(1), 'Nutgrund Tiefe', k, frame=True)
    cc.dim((8, L['Y0'], 2.0), (8, L['Y1'], 2.0), 'v', cc.right(2), 'Tiefe aussen', k, text='(%s)' % fmt(L['Y1'] - L['Y0']))
    cc.radial((G['X'] - G['R'], G['Y1'] - G['R'], 4.8), G['R'], 45, 'Nutgrund Radius', k, pre='R', length=6)
    cc.dim((-xs, 7.4, 4.8), (xs, 7.4, 4.8), 'h', cc.bottom(1), 'Platinenschlitz Laenge', k, frame=True)
    cc.dim((3, ys0, 4.8), (3, ys1, 4.8), 'v', cc.left(1), 'Platinenschlitz Breite', k, frame=True, tside=-1)
    kp = FP.KPOCKET
    cc.dim((kp['X0'], 6.0, 4.8), (kp['X1'], 6.0, 4.8), 'h', cc.bottom(2), 'Tasche U3 Breite', k)
    cc.dim((-7, PCB['Y_F'] - kp['DEPTH'], 4.8), (-7, PCB['Y_F'], 4.8), 'v', cc.left(2), 'Tasche Tiefe ab F', k, tside=-1,
           chk=[(-7, PCB['Y_F'] - kp['DEPTH'], 4.8), (kp['X0'], ys0, 4.8)])
    cc.dim((-L['X'], y0, 4.0), (kp['X0'], 6.0, 4.8), 'h', cc.bottom(3), 'Tasche Lage x', k,
           chk=[(-L['X'], y0, 2.0), (kp['X0'], 6.0, 4.8)])
    # D-D (z 2.4): Sechskant
    hx = (sc['NUT_S'] + 0.1) / 2
    ee.dim((0, sc['Y'] - hx, 2.4), (0, sc['Y'] + hx, 2.4), 'v', ee.right(1), 'Mutter SW Tasche', k, frame=True,
           chk=[(0.5, sc['Y'] + hx, 2.4)], text='SW' + fmt(2 * hx))
    ee.dim((8, L['Y0'], 2.4), (0, sc['Y'], 2.4), 'v', ee.left(1), 'Schraubenachse ab Vorderseite', k, tside=-1,
           chk=[(8, L['Y0'], 2.4), (0.5, sc['Y'] + hx, 2.4)])
    ee.cross((0, sc['Y'], 2.4), 2.5)
    # A-A (x 0): Mutter, Bohrung, Nut
    aa.dim((0, sc['Y'] - sc['HOLE_D'] / 2, 1.45), (0, sc['Y'] + sc['HOLE_D'] / 2, 1.45), 'h', aa.bottom(1), 'Bohrung unter Mutter', k, pre='Ø')
    aa.dim((0, 5.8, Z['COL_NUT0']), (0, 5.8, Z['COL_NUT1'] + 0.05), 'v', aa.left(1), 'Mutter Tasche Hoehe', k, tside=-1)
    aa.dim((0, L['Y0'], 3.4), (0, G['Y0'], 4.8), 'h', aa.top(1, 6), 'Nuttiefe', k, frame=True, tside=-1)
    aa.dim((0, ys0, 4.8), (0, ys1, 4.8), 'h', aa.top(2, 6), 'Schlitz', k, tside=1)
    aa.centerline((0, sc['Y'], 0.8), (0, sc['Y'], 4.0))
    aa.note((0, ys0 - 0.3, Z['COL0'] + 0.3), 'Hohlkehle 0.6 × 45° um den Schlitz\n(Verguss, Kerbwirkung)', 12, -14, shape=k, what='Hohlkehle auf Geometrie')
    # B-B: Tasche
    bb.dim((-7, PCB['Y_F'] - kp['DEPTH'], Z['COL0']), (-7, 6.0, kp['Z1']), 'v', bb.right(1), 'Tasche Hoehe (unten offen)', k,
           chk=[(-7, PCB['Y_F'] - kp['DEPTH'], Z['COL0']), (-7, 6.0, kp['Z1'])])
    bb.dim((-7, 6.0, kp['Z1']), (-7, 6.0, Z['COL1']), 'v', bb.right(1), 'Deckel ueber Tasche', k, tside=1,
           chk=[(-7, 6.0, kp['Z1']), (-7, 6.0, Z['COL1'])])
    finish(sh, 'FL-S-03_kragen')


# ============================================================================================ Sensor: Kleinteile
def small(S, key, number, fname, title, sub, material, scale, orient, views, dims, notes=(), fmt_='A4'):
    k = S[key]
    sh = sheet(fmt_, number, title, sub, material, '%g:1' % scale, orient, notes=notes)
    vs = {}
    for name, kind, sec, pos, ttl in views:
        vs[name] = View(sh, k, kind, scale, section=sec).place(*pos).draw(ttl, 9)
    dims(vs, k)
    finish(sh, fname)


def d_fenster(S):
    D_ = FP.DROP
    r = D_['R'] - D_['GLUE']

    def dims(v, k):
        f, l = v['f'], v['l']
        f.dim((-r, 0.8, D_['ZC']), (r, 0.8, D_['ZC']), 'h', f.bottom(1), 'Tropfen Breite', k, frame=True)
        f.dim((0, 0.8, D_['ZC'] - r), (0, 0.8, D_['ZC'] + D_['K'] * D_['R']), 'v', f.right(1), 'Tropfen Hoehe', k)
        f.dim((0, 0.8, D_['ZC'] - r), (D_['BOSS_D'] / 2, 2.0, D_['ZC']), 'v', f.left(1), 'Mitte ueber Unterkante', k,
              chk=[(0, 0.8, D_['ZC'] - r), (0, 2.0, D_['ZC'] + D_['BOSS_D'] / 2), (0, 2.0, D_['ZC'] - D_['BOSS_D'] / 2)])
        l.dim((0, 0, 43.0), (0, D_['T'], 41.7), 'h', l.bottom(1), 'Dicke', k, tside=-1)
        l.dim((0, 0, 43.0), (0, D_['BOSS_Y1'], D_['ZC']), 'h', l.bottom(2), 'Lichtschaft Ende', k, frame=True)
        l.dim((0, 2.5, D_['ZC'] - D_['BOSS_D'] / 2), (0, 2.5, D_['ZC'] + D_['BOSS_D'] / 2), 'v', l.right(1), 'Lichtschaft', k, pre='Ø', frame=True)
    small(S, 'Fenster_transluzent', 'FL-S-04', 'FL-S-04_fenster_tropfen', 'Lichtfenster Tropfen (Sensor)',
          'Diffusor + Lichtschaft vor D1, LED-Abstand 2.0 mm', 'ASA natur transluzent (PETG nur mit Nachweis REQ-MECH-12)', 10,
          'Tropfenfläche auf dem Bett (matt = Diffusor), Schaft nach oben, 0.12 mm',
          [('f', 'front', None, (70, 145), 'Vorderansicht'), ('l', 'left', (0, 0, 0), (165, 145), 'A–A')], dims,
          notes=['6  Kleben in Kappe FL-S-02 (Spalt 0.1 je Seite), Klebstoff nicht auf die Sichtfläche (PRINT_SETTINGS Kap. 5).'])


def d_taste(S):
    ax_, ay_ = BTN['AX_X'], BTN['AX_Y']
    zb = H['H'] - BTN['POCKET_D'] + BTN['STROKE']
    zt = H['H'] + BTN['PROUD']
    zn = H['H'] - BTN['POCKET_D'] - 2.3 + BTN['MEMB_T'] + 0.05

    def dims(v, k):
        f, t = v['f'], v['t']
        t.dim((-BTN['W'] / 2, BTN['Y'], zt), (BTN['W'] / 2, BTN['Y'], zt), 'h', t.top(1, 5), 'Taste Breite', k)
        t.dim((3, BTN['Y'] - BTN['D'] / 2, zt), (3, BTN['Y'] + BTN['D'] / 2, zt), 'v', t.right(1), 'Taste Tiefe', k)
        t.dim((-BTN['W'] / 2, BTN['Y'], zt), (ax_ + BTN['NECK_D'] / 2, ay_, zb), 'h', t.bottom(1), 'Halsachse ab linker Kante', k,
              chk=[(-BTN['W'] / 2, BTN['Y'], zt), (ax_ + BTN['NECK_D'] / 2, ay_, 56.0), (ax_ - BTN['NECK_D'] / 2, ay_, 56.0)], text=fmt(BTN['W'] / 2 + ax_))
        t.dim((3, BTN['Y'] - BTN['D'] / 2, zt), (ax_, ay_ - BTN['NECK_D'] / 2, 56.0), 'v', t.left(1), 'Halsachse ab Vorderkante', k,
              chk=[(3, BTN['Y'] - BTN['D'] / 2, zt), (ax_, ay_ - BTN['NECK_D'] / 2, 56.0), (ax_, ay_ + BTN['NECK_D'] / 2, 56.0)],
              text=fmt(ay_ - (BTN['Y'] - BTN['D'] / 2)))
        t.note((-BTN['W'] / 2 + 0.5, BTN['Y'] - BTN['D'] / 2 + 0.5, zt), 'Fasen %s × 45°' % fmt(BTN['CH']), -10, -10, shape=k, what='Fase auf Geometrie')
        f.dim((3, BTN['Y'], zb), (3, BTN['Y'], zt), 'v', f.right(1), 'Tastenplatte Dicke', k)
        f.dim((ax_ + BTN['NECK_D'] / 2, ay_, zn), (ax_ + BTN['NECK_D'] / 2, ay_, zb), 'v', f.right(2), 'Hals Laenge', k,
              chk=[(ax_ + BTN['NECK_D'] / 2, ay_, zn + 0.5), (3, BTN['Y'], zb)])
        f.dim((ax_ - BTN['NECK_D'] / 2, ay_, 56.0), (ax_ + BTN['NECK_D'] / 2, ay_, 56.0), 'h', f.bottom(1), 'Hals', k, pre='Ø', frame=True)
        f.note((ax_, ay_, zn), 'Teller FL-S-07 auf den Hals pressen', 12, -8)
    small(S, 'Taste_blau', 'FL-S-05', 'FL-S-05_taste_blau', 'Taste blau', 'Tastenplatte mit Hals (Hub 0.8, M-4)',
          'ASA (Bambu, TDS V2.0), Hellblau', 5, 'Oberseite auf dem Bett, 0.12 mm',
          [('f', 'front', None, (80, 170), 'Vorderansicht'), ('t', 'top', None, (80, 122), 'Draufsicht')], dims)


def d_klemmring(S):
    ax_, ay_ = BTN['AX_X'], BTN['AX_Y']
    zm1 = H['H'] - BTN['POCKET_D'] - 2.3 + BTN['MEMB_T']
    zpf = H['H'] - BTN['POCKET_D']
    ro = BTN['CB_D'] / 2 - 0.05

    def dims(v, k):
        a = v['a']
        a.dim((ax_, ay_ - ro, 56.0), (ax_, ay_ + ro, 56.0), 'h', a.top(1, 5), 'Aussen', k, pre='Ø', frame=True)
        a.dim((ax_, ay_ - BTN['RING_ID'] / 2, 56.0), (ax_, ay_ + BTN['RING_ID'] / 2, 56.0), 'h', a.top(2, 5), 'Bohrung', k, pre='Ø')
        a.dim((ax_, ay_ - BTN['SKIRT_ID'] / 2, zm1 + 0.5), (ax_, ay_ + BTN['SKIRT_ID'] / 2, zm1 + 0.5), 'h', a.bottom(1), 'Schuerze innen', k, pre='Ø')
        a.dim((ax_, ay_ + ro, zm1), (ax_, ay_ + ro, zpf), 'v', a.right(1), 'Hoehe', k)
        a.dim((ax_, ay_ + 2.0, zm1 + 1.0), (ax_, ay_ + 2.0, zpf), 'v', a.left(1), 'Platte', k, tside=-1)
        a.centerline((ax_, ay_, zm1 - 0.5), (ax_, ay_, zpf + 0.5))
    small(S, 'Klemmring', 'FL-S-06', 'FL-S-06_klemmring', 'Klemmring Membran', 'klemmt Silikonmembran Ø6.4 × 0.5 in der Senkung der Kappe',
          'ASA (Bambu, TDS V2.0), Hellblau', 10, 'Platte auf dem Bett, 0.12 mm',
          [('a', 'left', (ax_, 0, 0), (110, 150), 'A–A (durch Achse)')], dims)


def d_teller(S):
    ax_, ay_ = BTN['AX_X'], BTN['AX_Y']
    zw1 = H['H'] - BTN['POCKET_D'] - 2.3 + BTN['MEMB_T'] + 1.0

    def dims(v, k):
        a = v['a']
        a.dim((ax_, ay_ - BTN['WASHER_D'] / 2, zw1), (ax_, ay_ + BTN['WASHER_D'] / 2, zw1), 'h', a.top(1, 5), 'Teller', k, pre='Ø')
        a.dim((ax_, ay_ - BTN['NECK_D'] / 2, zw1), (ax_, ay_ + BTN['NECK_D'] / 2, zw1), 'h', a.bottom(1), 'Bohrung (Presssitz Hals)', k, pre='Ø', frame=True)
        a.dim((ax_, ay_ + 2.0, zw1 - BTN['WASHER_T']), (ax_, ay_ + 2.0, zw1), 'v', a.right(1), 'Dicke', k)
    small(S, 'Tastenteller', 'FL-S-07', 'FL-S-07_tastenteller', 'Tastenteller', 'Anschlag der Taste am Klemmring (unverlierbar)',
          'ASA (Bambu, TDS V2.0), Hellblau', 10, 'flach, 0.12 mm (3 Schichten)',
          [('a', 'left', (ax_, 0, 0), (110, 150), 'A–A (durch Achse)')], dims,
          notes=['6  Presssitz Ø3.0 auf Hals Ø3.0 (Nennmass gleich): Übermass über FDM-Toleranz, am Muster prüfen (PROTOTYP-PRÜFUNG).'])


def d_stoessel(S):
    ax_, ay_ = BTN['AX_X'], BTN['AX_Y']
    T_ = FP.TONGUE
    fy1 = T_['Y0'] - T_['WEDGE_GAP']
    fy0 = fy1 - 1.15
    z0, z1 = BTN['TUBE_Z0'], H['H'] - BTN['POCKET_D'] - 2.3 - 0.05

    def dims(v, k):
        f, t = v['f'], v['t']
        f.dim((ax_ + 1.0, ay_, z0), (ax_ + 1.0, ay_, z1), 'v', f.right(1), 'Schaft Laenge', k, chk=[(ax_ + 1.0, ay_ + 1.118, z0 + 0.5), (ax_ + 1.0, ay_ + 1.118, z1)])
        f.dim((-5.8, fy1, T_['Z_CONTACT'] - 0.4), (-5.8, fy1, z0), 'v', f.left(1), 'Finger + Arm', k)
        f.dim((-5.8, fy1, 50.0), (-4.6, fy1, 50.0), 'h', f.bottom(1), 'Finger Breite', k)
        f.dim((-5.8, fy1, z0), (ax_ + 1.5, ay_, 52.0), 'h', f.top(1, 5), 'Finger bis Achse', k,
              chk=[(-5.8, fy1, z0 - 0.4), (ax_ + 1.5, ay_, 52.0)], text=fmt(ax_ + 5.8))
        t.dim((-5.8, fy0, 50.0), (-5.8, fy1, 50.0), 'v', t.left(1), 'Finger Dicke', k, tside=-1)
        t.dim((ax_ - 1.5, ay_, 52.0), (ax_ + 1.5, ay_, 52.0), 'h', t.top(1, 5), 'Schaft', k, pre='Ø', frame=True)
        t.dim((ax_, ay_ - 1.0, 52.0), (ax_, ay_ + 1.5, 52.0), 'v', t.right(1), 'D-Flaeche', k)
    small(S, 'Stoessel', 'FL-S-08', 'FL-S-08_stoessel', 'Stössel mit Finger', 'überträgt den Tastenhub auf die Biegezunge der Kappe',
          'ASA (Bambu, TDS V2.0), Farbe beliebig', 10, 'flach auf der D-Fläche, 0.12 mm',
          [('f', 'front', None, (80, 165), 'Vorderansicht'), ('t', 'bottom', None, (80, 112), 'Ansicht von unten')], dims,
          notes=['6  OFFEN P5-M2: 30°-Keilfläche am Finger bzw. Nase an der Zunge fehlt im CAD; Finger berührt die Zunge im Modell nicht.'])


def d_schottkeil(S):
    bs, kc = CAP['BULK_SLOT'], CAP['KEIL_CLR']

    def dims(v, k):
        f, l = v['f'], v['l']
        f.dim((-bs['X'] + kc, 5.0, 31.4), (bs['X'] - kc, 5.0, 31.4), 'h', f.bottom(1), 'Laenge', k, frame=True)
        f.dim((10, 5.0, Z['BULK0']), (10, 5.0, Z['BULK1']), 'v', f.right(1), 'Hoehe', k)
        l.dim((0, bs['Y0'] + kc, 31.4), (0, PCB['Y_F'], 31.4), 'h', l.bottom(1), 'Dicke (Rueckseite = F-Referenz)', k, frame=True)
    small(S, 'Schottkeil', 'FL-S-09', 'FL-S-09_schottkeil', 'Schottkeil', 'füllt den vorderen Durchführungsspalt im Schott, drückt F nach hinten an',
          'ASA (Bambu, TDS V2.0), Farbe beliebig', 5, 'flach, 0.16 mm',
          [('f', 'front', None, (110, 130), 'Vorderansicht'), ('l', 'left', (0, 0, 0), (215, 130), 'A–A')], dims)


def d_lehre(S):
    k = [o for n, o in S.items() if n.startswith('Distanzlehre')][0]
    S2 = dict(S)
    S2['_lehre'] = k
    hgt = Z['BULK0'] - Z['COL1']

    def dims(v, kk):
        f = v['f']
        f.dim((0, 1.0, 0), (0, 1.0, hgt), 'v', f.right(1), 'Lehre Laenge = Fach', kk, frame=True, chk=[(0.5, 0, 0), (0.5, 0, hgt)])
        f.dim((-1.5, 0, 5), (1.5, 0, 5), 'h', f.bottom(1), 'Breite', kk)
        v['l'].dim((0, 0, 5), (0, 2.0, 5), 'h', v['l'].bottom(1), 'Dicke', kk, chk=[(-1.5, 0, 5), (-1.5, 2.0, 5)])
    small(S2, '_lehre', 'FL-S-10', 'FL-S-10_distanzlehre_24p2', 'Distanzlehre Fach %s (Montagehilfe)' % fmt(hgt),
          'Abstand Kragen-Oberkante bis Schott-Unterkante beim Kragenverguss, 2 Stück', 'ASA, Farbe beliebig', 2,
          'stehend, 0.16 mm', [('f', 'front', None, (90, 140), 'Vorderansicht'), ('l', 'left', None, (150, 140), 'Seitenansicht')], dims,
          notes=['6  Kein Produktteil; wiederverwendbar. Länge vor Gebrauch mit Messschieber prüfen (24.2 ±0.1).'])


# ============================================================================================ Zusammenbau Sensor
ASM = [  # (Pos, Schluessel FCStd oder STEP-Gruppe, Menge, Benennung, Sachnummer/Norm, Werkstoff/Bemerkung, Schraffur, Ansicht)
    (1, 'Kappe_blau', '1', 'Kappe blau', 'FL-S-02', 'ASA hellblau', (45, 1.4), 'A'),
    (2, 'Huelse_grau', '1', 'Hülse grau', 'FL-S-01', 'ASA warmgrau', (135, 1.4), 'A'),
    (3, 'Kragen', '1', 'Kragen', 'FL-S-03', 'ASA', (45, 0.8), 'A'),
    (4, 'Fenster_transluzent', '1', 'Lichtfenster Tropfen', 'FL-S-04', 'ASA natur transluzent, geklebt', (135, 0.6), 'A'),
    (5, 'Taste_blau', '1', 'Taste', 'FL-S-05', 'ASA hellblau', (135, 0.6), 'B'),
    (6, 'Klemmring', '1', 'Klemmring', 'FL-S-06', 'ASA hellblau', (45, 0.5), 'B'),
    (7, 'Tastenteller', '1', 'Tastenteller', 'FL-S-07', 'ASA hellblau', (135, 0.4), 'B'),
    (8, 'Stoessel', '1', 'Stössel', 'FL-S-08', 'ASA', (45, 0.5), 'B'),
    (9, 'Schottkeil', '1', 'Schottkeil', 'FL-S-09', 'ASA', (135, 0.5), 'A'),
    (10, 'Membran_Silikon', '1', 'Tastenmembran Ø6.4 × 0.5', 'INDEX MECH-MEM1', 'Silikon, Shore A 40–60 (ANNAHME, Typ offen)', (0, 0.3), 'B'),
    (11, 'ORing_Kragen', '2', 'O-Ring AS568-019 (20.35 × 1.78)', 'INDEX MECH-OR1 (Rev B)', 'Silikon/EPDM ohne Russ, Silikonfett', (0, 0.35), 'A'),
    (12, 'Schraube_M2', '1', 'Linsenschraube M2 × 3 PH1', 'ISO 7045, A2', 'unverlierbar (Furchlippe), V-K D-023', (90, 0.35), 'A'),
    (13, 'Mutter_M2', '1', 'Sechskantmutter M2', 'ISO 4032, A2', 'im Kragen eingegossen', (0, 0.35), 'A'),
    (14, 'Verguss_Kragen', '-', 'Verguss Kragen', 'INDEX EP-K', 'Epoxid 2K mineral. gefüllt, Tg ≥ 80 °C (Typ offen)', (90, 0.3), 'A'),
    (15, 'Verguss_Schott', '-', 'Verguss Schott', 'INDEX EP-K', 'wie Pos. 14', (90, 0.3), 'A'),
    (16, '_pcb', '1', 'Platine fluidi_sensor Rev C, bestückt', 'hardware/sensor (JLC)', 'FR4 4 L 1.6, inkl. XBT1 Keystone 3034', (45, 0.45), 'A'),
    (17, '_cell', '1', 'Knopfzelle CR2032', 'Panasonic CR2032', 'Panasonic_CR2032_Datasheet_2026-02.pdf', (135, 0.45), 'A'),
]
AIDS = 'Hilfsmittel (nicht im Produkt): Distanzlehre FL-S-10 (2 Stk.), Silikonfett O-Ringe, Klebstoff Fenster (Typ ANNAHME), Kapton-Punkt'


def load_pcb_step():
    raw = Part.read(os.path.join(REPO, 'mechanical', 'sensor', 'fluidi_sensor_mit_pcb.step'))
    sols = raw.Solids
    rest = sols[16:]          # fluidi_pcb_collision.py: 16 Gehaeuseteile, dann Platine, Bauteile, Zelle, Antenne
    cell = min(rest, key=lambda so: abs(so.Volume - math.pi * 100 * FP.CELL['T']))
    pcb = [so for so in rest if so is not cell]
    return Part.makeCompound(pcb), cell


def d_assembly(S):
    pcb, cell = load_pcb_step()
    S = dict(S)
    S['_pcb'], S['_cell'] = pcb, cell
    sh = Sheet('A3', 'FL-S-00', 'Sensor fluidi – Zusammenbau', 'Kopf P3 V4 mit Sonde, Positionen und Stückliste',
               'siehe Stückliste', '1:1; 2:1; 3:1', 'Einzelteile siehe FL-S-01 … FL-S-10', STAND,
               'fluidi_sensor.FCStd + fluidi_sensor_mit_pcb.step  <-  fluidi_sensor.py, fluidi_pcb_collision.py',
               ['1  Masse in mm. Montage, Verguss und Batteriewechsel: docs/manuals/MONTAGE_SENSOR.md.',
                '2  Kollisionsfreiheit: mechanical/sensor/collision_pcb_step.txt; Funktionsmasse: check_sensor.txt.',
                '3  ' + AIDS], date=DATE)
    full = Part.makeCompound([S[k] for _, k, *_ in ASM])
    fr = View(sh, [(full, None)], 'front', 1.0).place(60, 125).draw('Vorderansicht 1:1', 8)
    fr.cutline((0, 0, -2), (0, 0, 59), 'A', (1, 0, 0), ext=3)
    fr.cutline((BTN['AX_X'], 0, 40), (BTN['AX_X'], 0, 59), 'B', (1, 0, 0), ext=3)
    fr.dim((0, 0, PCB['Z_TIP']), (0, 0, H['H']), 'v', fr.right(1), 'Gesamtlaenge', full,
           chk=[(0, PCB['Y_F'], PCB['Z_TIP']), (10, 6.5, H['H'])], text=fmt(H['H'] - PCB['Z_TIP']) + ' (ohne Taste)')
    fr.dim((0, 0, PCB['Z_TIP']), (0, 0, -H['GAP_SOIL']), 'v', fr.left(1), 'Stecktiefe max (Markierung)', full,
           chk=[(0, PCB['Y_F'], PCB['Z_TIP'])], text=fmt(PCB['Z_TIP'] * -1 - H['GAP_SOIL']))
    fr.dim((-H['W'] / 2, 6.5, 50), (H['W'] / 2, 6.5, 50), 'h', fr.top(1, 6), 'Kopfbreite', full)
    fr.note((-PCB['W'] / 2, PCB['Y_F'], -H['GAP_SOIL']), 'Silkscreen „max“ (z −5)', -8, -10)
    A = [(S[k], hat) for _, k, *_r, hat, v in ASM]
    aa = View(sh, A, 'left', 2.0, section=(0, 0, 0), clip_model=(-14.0, 0.5, -3.0, 59.5)).place(170, 160).draw('A–A (2:1, Kopf)', 8)
    clipB = (-14.0, 0.5, 40.0, 59.0)
    bb = View(sh, A, 'left', 3.0, section=(BTN['AX_X'], 0, 0), clip_model=clipB).place(330, 232).draw('B–B (3:1, Tastenmechanik)', 6)
    # Positionsnummern: links/rechts von A-A gestaffelt
    xl, xr = aa.box[0] - 22, aa.box[1] + 22
    ya = [aa.box[3] - 5]
    nL = nR = 0
    for i, (pos, k, *_r, hat, v) in enumerate(ASM):
        if v == 'A':
            side_left = pos in (1, 4, 11, 12, 14, 16, 17)
            if side_left:
                y = aa.box[3] - 6 - nL * 11; nL += 1
                aa.balloon(i, pos, (xl, y))
            else:
                y = aa.box[3] - 6 - nR * 11; nR += 1
                aa.balloon(i, pos, (xr, y))
        else:
            bb.balloon(i, pos, (bb.box[0] - 10 - (pos % 2) * 9, bb.box[3] - 4 - (pos - 5) * 8))
    # Stueckliste ueber dem Schriftfeld
    x0, y0, w, h = sh.tb
    rows = [('Pos', 'Menge', 'Benennung', 'Sachnummer / Norm', 'Werkstoff / Bemerkung')] + \
           [(str(p), m, b, n, wk) for p, _k, m, b, n, wk, _h, _v in ASM]
    cw = [9, 12, 50, 38, 71]
    rh = 4.3
    ytop = y0 + h + 14 + rh * len(rows)
    for r_, row in enumerate(rows):
        yy = ytop - (r_ + 1) * rh
        xx = x0
        for c_, (txt, wc) in enumerate(zip(row, cw)):
            sh.ax.add_patch(__import__('matplotlib').patches.Rectangle((xx, yy), wc, rh, fill=False, lw=0.5, zorder=2))
            sh.text(xx + 0.8, yy + 1.1, txt, h=1.75 if r_ else 1.9, weight='bold' if r_ == 0 else 'normal')
            xx += wc
    sh.text(x0, ytop + 1.5, 'Stückliste', h=3.0, weight='bold')
    finish(sh, 'FL-S-00_zusammenbau_sensor')


# ============================================================================================ Gateway G1 v4
def load_gateway():
    path = os.path.join(HERE, 'fluidi_gateway_pi.py')
    src = open(path).read().rsplit('\nmain()', 1)[0]
    ns = {'__file__': path, '__name__': 'fluidi_gateway_pi_params'}
    exec(compile(src, path, 'exec'), ns)
    d = App.openDocument(os.path.join(REPO, 'mechanical', 'gateway_pi', 'fluidi_gateway_pi.FCStd'))
    GS = {o.Name: o.Shape.copy() for o in d.Objects}
    App.closeDocument(d.Name)
    return ns, GS


GW_SRC = 'mechanical/gateway_pi/fluidi_gateway_pi.FCStd  <-  mechanical/gen/fluidi_gateway_pi.py'
GW_NOTES = ['6  Pi-Lage aus RP-008358-DS-1 abgegriffen (±0.2), Bauteilhöhen ANNAHME: vor dem Druck am Pi messen (PRINT_SETTINGS Kap. 3).']


def d_wanne(GN, GS):
    w = GS['Wanne_grau']
    G, PI, T, USB = GN['G'], GN['PI'], GN['TUBE'], GN['USB']
    px, py, ZP = GN['px'], GN['py'], GN['ZP']
    sh = Sheet('A3', 'FL-G-01', 'Gateway G1 v4 – Wanne grau', 'Pi-Abstandshalter, Lichtschacht, Klimakammer, Micro-USB-Fenster (Variante _otg: + OTG-Fenster)',
               'ASA (Bambu, TDS V2.0), Warmgrau hell #B9B5AC', '2:1', 'Boden auf dem Bett, Brim 3 mm; Brücken: USB-Fenster 11.4, Senkungen Ø5.4',
               STAND, GW_SRC, NOTE_COMMON + GW_NOTES, date=DATE)
    s = 2.0
    fr = View(sh, w, 'front', s).place(125, 252).draw('Vorderansicht', 12)
    tp = View(sh, w, 'top', s).place(125, 170).draw('Draufsicht', 13)
    aa = View(sh, w, 'left', s, section=(0, 0, 0)).place(285, 255).draw('A–A', 7)
    hy = py(PI['HOLES'][0][1])
    bb = View(sh, w, 'front', s, section=(0, hy, 0)).place(125, 100).draw('B–B (Achse Befestigung)', 7)
    bk = View(sh, w, 'back', s).place(320, 185).draw('Ansicht C (hinten)', 7)
    tp.cutline((0, -22, 5), (0, 22, 5), 'A', (1, 0, 0), ext=3)
    tp.cutline((-43, hy, 5), (43, hy, 5), 'B', (0, 1, 0), ext=3)
    W2, D2, zt = G['W'] / 2, G['D'] / 2, G['Z_FUGE'] - G['GAP'] / 2
    fr.dim((-W2, -10, 6), (W2, -10, 6), 'h', fr.top(1, 5), 'Breite', w, chk=[(-W2, -10, 6), (W2, -10, 6)])
    fr.dim((W2, -10, 0), (W2, -10, zt), 'v', fr.right(1), 'Hoehe Wanne', w, chk=[(0, D2, 0), (0, D2, zt)])
    hs = [(px(X), py(Y)) for X, Y in PI['HOLES']]
    xs = sorted(set(round(h[0], 3) for h in hs)); ys = sorted(set(round(h[1], 3) for h in hs))
    hr = T['HOLE_D'] / 2
    tp.dim((xs[0], ys[1], 4), (xs[1], ys[1], 4), 'h', tp.top(1, 6), 'Lochabstand x (Pi 58)', w, frame=True,
           chk=[(xs[0] - hr, ys[1], 4), (xs[0] + hr, ys[1], 4), (xs[1] - hr, ys[1], 4), (xs[1] + hr, ys[1], 4)])
    tp.dim((xs[1], ys[0], 4), (xs[1], ys[1], 4), 'v', tp.right(1), 'Lochabstand y (Pi 23)', w, frame=True,
           chk=[(xs[1], ys[0] - hr, 4), (xs[1], ys[0] + hr, 4), (xs[1], ys[1] - hr, 4), (xs[1], ys[1] + hr, 4)])
    tp.dim((-W2, -10, 6), (xs[0], ys[0], 4), 'h', tp.bottom(1), 'Loch ab linker Stirnseite', w,
           chk=[(-W2, -10, 6), (xs[0] - hr, ys[0], 4), (xs[0] + hr, ys[0], 4)])
    tp.dim((0, D2, 6), (xs[1], ys[1], 4), 'v', tp.left(1), 'Loch ab Rueckseite', w,
           chk=[(0, D2, 6), (xs[1], ys[1] - hr, 4), (xs[1], ys[1] + hr, 4)])
    tp.dim((0, -D2, 5), (0, D2, 5), 'v', tp.left(2), 'Tiefe', w)
    for x_, y_ in hs:
        tp.cross((x_, y_, 4), 3.3)
    xp0 = GN['X_PART']
    tp.dim((xp0, 0, 8), (xp0 + GN['CLIMA']['WALL'], 0, 8), 'h', tp.top(2, 6), 'Trennwand Klimakammer', w, tside=1)
    tp.dim((xp0 + GN['CLIMA']['WALL'], 0, 8), (W2, -10, 6), 'h', tp.bottom(2), 'Klimakammer bis Stirnseite', w)
    # A-A
    aa.dim((0, D2 - G['WALL'], 8), (0, D2, 8), 'h', aa.top(1, 5), 'Wand', w, tside=-1)
    aa.dim((0, -D2, 0), (0, -D2, G['H'] - G['FACET']), 'v', aa.right(1), 'Facette Beginn', w)
    aa.note((0, -D2 + 1.0, G['H'] - G['FACET'] + 1.0), 'Facette 45° (Deckel setzt fort)', 18, 14, shape=w, what='Facette auf Geometrie')
    # B-B
    x1 = xs[1]
    bb.dim((x1 - hr, hy, 3.0), (x1 + hr, hy, 3.0), 'h', bb.top(1, 5), 'Bohrung', w, pre='Ø')
    bb.dim((x1 - T['CB_D'] / 2, hy, 0.8), (x1 + T['CB_D'] / 2, hy, 0.8), 'h', bb.bottom(1), 'Senkung Schraubenkopf', w, pre='Ø')
    bb.dim((x1 + T['CB_D'] / 2, hy, 0), (x1 + 2.0, hy, T['CB_H']), 'v', bb.right(1), 'Senkung Tiefe', w, tside=1)
    bb.dim((x1 + 4.5, hy, G['WALL']), (x1 + 2.1, hy, PI['Z0']), 'v', bb.right(2), 'Auflage Pi (Abstandshalter)', w, frame=True)
    bb.dim((x1 - T['R'], hy, 4.0), (x1 + T['R'], hy, 4.0), 'h', bb.top(2, 5), 'Abstandshalter', w, pre='Ø')
    # Ansicht C: Micro-USB
    xu, zc = px(USB['PWR_X']), ZP + USB['ZC_DZ']
    ww, wh = USB['WIN']
    bk.dim((xu - ww / 2, D2, zc), (xu + ww / 2, D2, zc), 'h', bk.top(1, 5), 'Fenster Micro-USB PWR Breite', w, frame=True)
    bk.dim((xu, D2, zc - wh / 2), (xu, D2, zc + wh / 2), 'v', bk.left(1), 'Fenster Hoehe', w, frame=True)
    bk.dim((-W2, -10, 6), (xu - ww / 2, D2, zc), 'h', bk.bottom(1), 'Fenster ab linker Stirnseite', w)
    bk.dim((xu + ww / 2, D2, 0), (xu + ww / 2, D2, zc - wh / 2), 'v', bk.right(1), 'Fenster Unterkante', w, tside=1,
           chk=[(xu + ww / 2 + 1, D2, 0), (xu + ww / 2, D2, zc - wh / 2)])
    bk.note((px(USB['OTG_X']), D2, zc), 'Variante wanne_grau_otg: zweites Fenster\ngleicher Grösse bei OTG (x %s)' % fmt(px(USB['OTG_X'])), -30, -24)
    finish(sh, 'FL-G-01_wanne_grau')


def d_deckel(GN, GS):
    k = GS['Deckel_blau']
    G, PI, T = GN['G'], GN['PI'], GN['TUBE']
    px, py, ZP = GN['px'], GN['py'], GN['ZP']
    sh = Sheet('A3', 'FL-G-02', 'Gateway G1 v4 – Deckel blau', 'Facette mit Tropfenfenster, 4 Niederhalterrohre (Einsatz M2.5), Steg, Kaminschlitze, RTC-Rahmen',
               'ASA (Bambu, TDS V2.0), Hellblau, ohne Russ/Metallpigment', '2:1', 'kopfüber (Decke auf dem Bett); Facette 45°; vordere Rohre stehen auf der Innenfacette',
               STAND, GW_SRC, NOTE_COMMON + GW_NOTES + ['7  Gewindeeinsätze M2.5 Ø3.5 × 4 mit Lötkolben 220 °C einsetzen (ANNAHME, PRINT_SETTINGS Kap. 5).'], date=DATE)
    s = 2.0
    fr = View(sh, k, 'front', s).place(125, 262).draw('Vorderansicht', 4)
    tp = View(sh, k, 'top', s).place(125, 190).draw('Draufsicht', 5)
    bt = View(sh, k, 'bottom', s).place(125, 93).draw('Ansicht von unten (innen)', 5)
    aa = View(sh, k, 'left', s, section=(0, 0, 0)).place(300, 245).draw('A–A', 12)
    hx, hy = px(PI['HOLES'][0][0]), py(PI['HOLES'][0][1])
    bb = View(sh, k, 'left', s, section=(hx, 0, 0)).place(300, 175).draw('B–B (Achse Rohr)', 10)
    tp.cutline((0, -22, 17), (0, 22, 17), 'A', (1, 0, 0), ext=3)
    tp.cutline((hx, -22, 17), (hx, 22, 17), 'B', (1, 0, 0), ext=3)
    W2, D2 = G['W'] / 2, G['D'] / 2
    z0 = G['Z_FUGE'] + G['GAP'] / 2
    fr.dim((-W2, -10, 16.8), (W2, -10, 16.8), 'h', fr.top(1, 5), 'Breite', k)
    aa.dim((0, D2, z0), (0, D2, G['H']), 'v', aa.right(1), 'Hoehe Deckel', k)
    lo = G['WALL'] + G['LIP_CLR']
    aa.dim((0, D2 - lo - G['LIP_T'], 12.5), (0, D2 - lo, 12.5), 'h', aa.bottom(1), 'Steg Dicke', k, tside=1)
    aa.dim((0, D2 - lo, 12.5), (0, D2, 16.0), 'h', aa.bottom(2), 'Steg ab Aussenflaeche (Wand 2 + Spiel 0.15)', k, tside=1)
    aa.dim((0, D2, z0), (0, D2 - lo - 0.6, G['LIP_Z0']), 'v', aa.right(2), 'Steg Ueberstand', k, frame=True)
    rr = T['INS_D'] / 2
    bb.dim((hx, hy - rr, 8), (hx, hy + rr, 8), 'h', bb.top(1, 5), 'Bohrung Einsatz M2.5', k, pre='Ø', frame=True)
    bb.dim((hx, hy - T['R'], 8), (hx, hy + T['R'], 8), 'h', bb.bottom(1), 'Rohr', k, pre='Ø')
    bb.dim((hx, hy + 2.2, ZP), (hx, hy + 1.5, ZP + T['INS_L']), 'v', bb.left(1), 'Bohrtiefe Einsatz', k, frame=True)
    bb.dim((hx, hy + 2.2, ZP), (hx, D2, G['H']), 'v', bb.right(1), 'Rohrunterkante bis Oberseite', k,
           chk=[(hx, hy + 2.2, ZP), (hx + 0.5, D2 - 1, G['H'])])
    hs = [(px(X), py(Y)) for X, Y in PI['HOLES']]
    xs = sorted(set(round(h[0], 3) for h in hs)); ys = sorted(set(round(h[1], 3) for h in hs))
    bt.dim((xs[0], ys[1], ZP), (xs[1], ys[1], ZP), 'h', bt.top(1, 6), 'Rohrabstand x', k, frame=True,
           chk=[(xs[0] + 2.2, ys[1], ZP), (xs[1] + 2.2, ys[1], ZP)])
    bt.dim((xs[1], ys[0], ZP), (xs[1], ys[1], ZP), 'v', bt.right(1), 'Rohrabstand y', k, frame=True,
           chk=[(xs[1] + 2.2, ys[0], ZP), (xs[1] + 2.2, ys[1], ZP)])
    for x_, y_ in hs:
        bt.cross((x_, y_, ZP), 3.3)
    tp.note((G['LED_X'], -D2 + 3.5, G['H'] - G['FACET'] + 3.5 + 1.0), 'Tropfenfenster r %s (FL-G-03 + Spalt %s)\nauf der Facette, x %s'
            % (fmt(FP.DROP['R']), fmt(FP.DROP['GLUE']), fmt(G['LED_X'])), 20, -16)
    finish(sh, 'FL-G-02_deckel_blau')


def d_fenster_gw(GN, GS):
    f = Part.read(os.path.join(REPO, 'mechanical', 'gateway_pi', 'print', 'fenster_tropfen_gw.step'))
    f = f.Solids[0]
    sh = Sheet('A4', 'FL-G-03', 'Gateway – Lichtfenster Tropfen', 'Diffusor vor der LED-Platine, auf der 45°-Facette eingeklebt',
               'ASA natur transluzent', '10:1', 'Aussenfläche auf dem Bett (wie exportiert), 0.12 mm', STAND,
               'mechanical/gateway_pi/print/fenster_tropfen_gw.step (Druckausrichtung)  <-  fluidi_gateway_pi.py', NOTE_COMMON, date=DATE)
    tp = View(sh, f, 'top', 10.0).place(80, 140).draw('Draufsicht (Druckausrichtung)', 7)
    fr = View(sh, f, 'front', 10.0).place(190, 140).draw('Vorderansicht', 7)
    vs = f.Vertexes
    xmn, xmx = min(vs, key=lambda v: v.X), max(vs, key=lambda v: v.X)
    ymn, ymx = min(vs, key=lambda v: v.Y), max(vs, key=lambda v: v.Y)
    zmn, zmx = min(vs, key=lambda v: v.Z), max(vs, key=lambda v: v.Z)
    P = lambda v: (v.X, v.Y, v.Z)
    tp.dim(P(xmn), P(xmx), 'h', tp.bottom(1), 'Tropfen Breite', f, frame=True)
    tp.dim(P(ymn), P(ymx), 'v', tp.right(1), 'Tropfen Hoehe', f)
    fr.dim(P(zmn), P(zmx), 'v', fr.right(1), 'Dicke', f)
    finish(sh, 'FL-G-03_fenster_tropfen_gw')


DRAW = [('FL-S-01', d_huelse), ('FL-S-02', d_kappe), ('FL-S-03', d_kragen), ('FL-S-04', d_fenster),
        ('FL-S-05', d_taste), ('FL-S-06', d_klemmring), ('FL-S-07', d_teller), ('FL-S-08', d_stoessel),
        ('FL-S-09', d_schottkeil), ('FL-S-10', d_lehre), ('FL-S-00', d_assembly)]
GWDRAW = [('FL-G-01', d_wanne), ('FL-G-02', d_deckel), ('FL-G-03', d_fenster_gw)]


def main():
    S = load_sensor()
    for num, fn in DRAW:
        if ONLY and num not in ONLY:
            continue
        fn(S)
    if not ONLY or any(n.startswith('FL-G') for n in ONLY):
        GN, GS = load_gateway()
        for num, fn in GWDRAW:
            if ONLY and num not in ONLY:
                continue
            fn(GN, GS)
    lines = ['fluidi Fertigungszeichnungen - Pruefprotokoll der Masse (erzeugt von mechanical/gen/fluidi_drawings.py, %s)' % DATE,
             'Stand: %s' % STAND,
             'Jede Masszahl ist der Abstand zweier Modellpunkte; Spalte "max d" = groesster Abstand der Messpunkte zur',
             'Geometrie des Teils (Soll < 0.005 mm, sonst FEHLER).', '']
    for num, what, val, ok, dmax in ALL_CHECKS:
        lines.append('%-8s %-70s %-6s max d %.4f' % (num, what, 'ok' if ok else 'FEHLER', dmax))
    nbad = sum(1 for c in ALL_CHECKS if not c[3])
    lines.append('')
    lines.append('Summe: %d Masse/Hinweise geprueft, %d Fehler' % (len(ALL_CHECKS), nbad))
    if not ONLY:
        open(os.path.join(OUT, 'drawings_check.txt'), 'w').write('\n'.join(lines) + '\n')
    print(lines[-1])


main()
