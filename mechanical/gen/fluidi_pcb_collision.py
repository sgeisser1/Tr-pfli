# -*- coding: utf-8 -*-
"""fluidi Sensor - Kollisions- und Schnittstellenpruefung Gehaeuse <-> Platine (KiCad-STEP), FreeCAD 0.21.2 headless.

Setzt das KiCad-STEP der Platine (hardware/sensor/out/fluidi_sensor.step) in die Sensorbaugruppe aus
fluidi_sensor.build() und rechnet boolesche Schnittmengen, Mindestabstaende und Bewegungsablaeufe (Einschieben der
Platine, Lage der Platine in z, Zelle ein-/ausschieben, Huelse abziehen). Lagen, Pads und Antennenkupfer kommen direkt
aus der Platinendatei (pcbnew, KiCad 10).

Lauf:     freecadcmd mechanical/gen/fluidi_pcb_collision.py
Ausgabe:  mechanical/sensor/collision_pcb_step.txt (Protokoll),
          mechanical/sensor/fluidi_sensor_mit_pcb.step (Baugruppe Gehaeuse + Platine, Kopfkoordinaten)

Koordinatenbezug (docs/interfaces/PCB_OUTLINE.md Kap. 1):
  KiCad-Seite (X_p, Y_p) absolut, Hilfsursprung (aux_axis_origin) A = Mitte Platinenoberkante:
      x = X_p - A_X,   z = Z_TOP - (Y_p - A_Y)
  KiCad-STEP (kicad-cli pcb export step, ohne Ursprungsoption): X_s = X_p, Y_s = -Y_p, Z_s = Hoehe ueber B (F bei T):
      x = X_s - A_X,   y = Y_B - Z_s,   z = Z_TOP + A_Y + Y_s
  = Drehung +90 Grad um x, dann Verschiebung (-A_X, Y_B, Z_TOP + A_Y).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
os.environ['FLUIDI_NO_MAIN'] = '1'

import FreeCAD as App
import Part
import pcbnew

import fluidi_params as FP
import fluidi_sensor as FS
from fluidi_cadlib import V, box, cyl_y, prism_xz

REPO = FP.REPO
STEP = os.path.join(REPO, 'hardware', 'sensor', 'out', 'fluidi_sensor.step')
BOARD = os.path.join(REPO, 'hardware', 'sensor', 'fluidi_sensor.kicad_pcb')
OUT = os.path.join(REPO, 'mechanical', 'sensor')
PCB, Z = FP.PCB, FP.Z
LOG = []
EPS_V = 1e-4                                   # mm3, kleinere Schnittmengen gelten als Beruehrung (numerisch)


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    LOG.append(s)


HOUSING = ['Kappe_blau', 'Huelse_grau', 'Kragen', 'Verguss_Kragen', 'Verguss_Schott', 'Schottkeil', 'Stoessel',
           'Fenster_transluzent', 'Mutter_M2', 'Schraube_M2x4', 'ORing_Kragen', 'ORing_Zapfen', 'Taste_blau',
           'Klemmring', 'Membran_Silikon', 'Tastenteller']
CAST = ('Verguss_Kragen', 'Verguss_Schott')    # werden um die Platine gegossen (nur in Endlage pruefen)
PLASTIC = ['Kappe_blau', 'Huelse_grau', 'Kragen', 'Schottkeil', 'Stoessel', 'Fenster_transluzent', 'Taste_blau',
           'Klemmring', 'Tastenteller', 'Membran_Silikon', 'ORing_Zapfen', 'ORing_Kragen']
METAL_HOUSING = ['Mutter_M2', 'Schraube_M2x4']

# Datenblatt-Hoehen (max.) fuer Bauteile, deren KiCad-Modell ein Ersatz ist oder fehlt
DS_H = {
    'U1': (1.0, 'TI_CC2340R5_Datasheet_SWRS272F.pdf S. 77, RGE0024B "1 MAX" (Ersatzmodell RGE0024H 0.8)'),
    'L1': (1.0, 'Sunlord_WPN201610H100MT_Datasheet_LCSC-2023-10.pdf S. 2, WPN201610H C max 1.0 (Ersatzmodell DFE201610P 1.0)'),
    'D1': (0.7, 'TUOZHAN_P4-1615G2B2R4TS2-06T-001-24_Datasheet_A0.pdf S. 4: 0.6 +-0.1, 1.6 x 1.5 +-0.1 (kein Modell im STEP)'),
    'BT1': (4.1, 'Keystone_3034_Catalog_M65.pdf S. 1: H .160 (4.1) (KiCad-Modell 4.0)'),
    'SW1': (2.1, 'XUNPU_TS-1088-AR02016_Datasheet_LCSC-2022-06.pdf S. 1: H 2.0, Allgemeintoleranz 0.5-2: +-0.10'),
    'U3': (0.6, 'TI_TMP1075_Datasheet_SBOS854F.pdf S. 36, DRL0006A "0.6 MAX" (KiCad-Modell 0.63)'),
}


# ----------------------------------------------------------------------------------------------- Platine einlesen
def read_board():
    b = pcbnew.LoadBoard(BOARD)
    ao = b.GetDesignSettings().GetAuxOrigin()
    AX, AY = pcbnew.ToMM(ao.x), pcbnew.ToMM(ao.y)

    def hz(Xp, Yp):
        return Xp - AX, PCB['Z_TOP'] - (Yp - AY)

    fps = {}
    for fp in b.GetFootprints():
        ref = fp.GetReference()
        p = fp.GetPosition()
        x, z = hz(pcbnew.ToMM(p.x), pcbnew.ToMM(p.y))
        cy = fp.GetCourtyard(pcbnew.F_CrtYd if not fp.IsFlipped() else pcbnew.B_CrtYd)
        if cy.OutlineCount():
            bb = cy.BBox()
            x0, z1 = hz(pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY()))
            x1, z0 = hz(pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))
        else:
            x0 = x1 = x; z0 = z1 = z
        pads = []
        for pd in fp.Pads():
            bb = pd.GetBoundingBox()
            px0, pz1 = hz(pcbnew.ToMM(bb.GetX()), pcbnew.ToMM(bb.GetY()))
            px1, pz0 = hz(pcbnew.ToMM(bb.GetRight()), pcbnew.ToMM(bb.GetBottom()))
            pads.append(dict(num=pd.GetNumber(), x=(px0, px1), z=(pz0, pz1), F=pd.IsOnLayer(pcbnew.F_Cu)))
        cu = []
        for g in fp.GraphicalItems():
            if g.GetLayer() == pcbnew.F_Cu and g.GetShapeStr() == 'Polygon':
                ps = g.GetPolyShape()
                for i in range(ps.OutlineCount()):
                    o = ps.Outline(i)
                    cu.append([hz(pcbnew.ToMM(o.CPoint(j).x), pcbnew.ToMM(o.CPoint(j).y)) for j in range(o.PointCount())])
        fps[ref] = dict(ref=ref, fpid=fp.GetFPIDAsString(), x=x, z=z, rot=fp.GetOrientationDegrees(),
                        side='B' if fp.IsFlipped() else 'F', dnp=fp.IsDNP(), models=len(fp.Models()) > 0,
                        crt=(x0, x1, z0, z1), pads=pads, cu=cu)
    eb = b.GetBoardEdgesBoundingBox()
    ex0, ez1 = hz(pcbnew.ToMM(eb.GetX()), pcbnew.ToMM(eb.GetY()))
    ex1, ez0 = hz(pcbnew.ToMM(eb.GetRight()), pcbnew.ToMM(eb.GetBottom()))
    return AX, AY, fps, (ex0, ex1, ez0, ez1)


def step_placement(AX, AY):
    return App.Placement(V(-AX, PCB['Y_B'], PCB['Z_TOP'] + AY), App.Rotation(V(1, 0, 0), 90))


def bb_dist(a, b):
    """Abstand zweier Huellquader (0 bei Ueberlappung)."""
    dx = max(a.XMin - b.XMax, b.XMin - a.XMax, 0)
    dy = max(a.YMin - b.YMax, b.YMin - a.YMax, 0)
    dz = max(a.ZMin - b.ZMax, b.ZMin - a.ZMax, 0)
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def inter(a, b):
    if bb_dist(a.BoundBox, b.BoundBox) > 0:
        return 0.0
    return a.common(b).Volume


def dist(a, b, cut=3.0):
    if bb_dist(a.BoundBox, b.BoundBox) > cut:
        return None
    return a.distToShape(b)[0]


def moved(sh, dx=0.0, dy=0.0, dz=0.0):
    m = sh.copy()
    m.translate(V(dx, dy, dz))
    return m


# ----------------------------------------------------------------------------------------------- Baugruppe
def build_pcb(AX, AY, fps):
    raw = Part.read(STEP)
    pl = step_placement(AX, AY)
    sols = []
    for so in raw.Solids:
        s2 = so.copy(); s2.Placement = pl.multiply(s2.Placement)
        sols.append(s2)
    board = max(sols, key=lambda s: s.Volume)
    comps = {}
    for so in sols:
        if so is board:
            continue
        c = so.BoundBox.Center
        cand = [f for f in fps.values() if f['models'] and not f['dnp'] and
                f['crt'][0] - 0.05 <= c.x <= f['crt'][1] + 0.05 and f['crt'][2] - 0.05 <= c.z <= f['crt'][3] + 0.05]
        if not cand:
            log('   WARNUNG: STEP-Koerper ohne Footprint bei x %.2f z %.2f' % (c.x, c.z))
            continue
        f = min(cand, key=lambda f: (f['x'] - c.x) ** 2 + (f['z'] - c.z) ** 2)
        comps.setdefault(f['ref'], []).append(so)
    comps = {k: (v[0] if len(v) == 1 else Part.makeCompound(v)) for k, v in comps.items()}
    src = {k: 'KiCad-Modell' for k in comps}
    yf = PCB['Y_F']
    # Ersatz/Ergaenzung nach Datenblatt
    if 'D1' in fps and 'D1' not in comps:
        f = fps['D1']
        comps['D1'] = box(f['x'] - 0.85, f['x'] + 0.85, yf - DS_H['D1'][0], yf, f['z'] - 0.85, f['z'] + 0.85)
        src['D1'] = 'Huelle 1.7 x 1.7 x 0.7 (Datenblatt max.)'
    if 'U1' in comps:
        f = fps['U1']
        comps['U1'] = box(f['x'] - 2.0, f['x'] + 2.0, yf - DS_H['U1'][0], yf, f['z'] - 2.0, f['z'] + 2.0)
        src['U1'] = 'Huelle 4 x 4 x 1.0 (Datenblatt max.)'
    # BT1: KiCad-Modell 4.0 hoch, Datenblatt 4.1 -> Abstaende nach vorn (-y) um 0.1 kleiner (im Protokoll vermerkt).
    # (transformGeometry-Streckung verworfen: erzeugt B-Splines mit unzuverlaessigem Huellquader)
    f = fps['BT1']
    cell = cyl_y(FP.CELL['D'] / 2, yf - FP.CELL['T'], yf, f['x'], f['z'])
    ant = None
    if fps.get('AE1') and fps['AE1']['cu']:
        ant = Part.makeCompound([prism_xz(p, yf - 0.035, yf) for p in fps['AE1']['cu']])
    pcb_gen = FS.prism_xz(FP.outline(), PCB['Y_F'], PCB['Y_B'])
    return board, pcb_gen, comps, src, cell, ant


# ----------------------------------------------------------------------------------------------- Pruefungen
def zone_of(z):
    for zd in FP.zones():
        if zd['side'] in ('F', 'FB') and zd['z'][0] <= z < zd['z'][1] and abs(zd['x'][1]) > 0:
            return zd
    return None


def main():
    S, sl_plain, _ = FS.build()
    AX, AY, fps, ebb = read_board()
    board, pcb_gen, comps, src, cell, ant = build_pcb(AX, AY, fps)
    log('=== fluidi Sensor: Kollisionspruefung Gehaeuse <-> Platine (KiCad-STEP), Schnittstelle Rev %s (%s) ===' % (FP.REV, FP.REV_DATE))
    log('Eingaben: %s, %s; Gehaeuse fluidi_sensor.build()' % (os.path.relpath(STEP, REPO), os.path.relpath(BOARD, REPO)))

    # ---------------------------------------------------------------- A Koordinatenbezug
    log('\nA Koordinatenbezug')
    log('   Hilfsursprung KiCad (aux_axis_origin) X %.3f Y %.3f = Mitte Platinenoberkante (Soll: Kontur x +-13, z %.1f)'
        % (AX, AY, PCB['Z_TOP']))
    log('   Edge.Cuts (pcbnew, Kopfkoord.): x %.3f ... %.3f, z %.3f ... %.3f (mit Strichbreite 0.05)' % ebb)
    bb = board.BoundBox
    log('   STEP-Platine nach Transformation: x %.3f ... %.3f, y %.3f ... %.3f, z %.3f ... %.3f'
        % (bb.XMin, bb.XMax, bb.YMin, bb.YMax, bb.ZMin, bb.ZMax))
    log('   Hinweis: STEP-Platinenkoerper %.2f mm dick (KiCad: Summe der Dielektrika), Bauteile sitzen auf y = %.2f (F, Soll %.2f)'
        % (bb.YLength, min(c.BoundBox.YMax for c in comps.values()), PCB['Y_F']))
    sl = box(-20, 20, PCB['Y_B'] - 0.3, PCB['Y_B'] - 0.1, -120, 60)
    a_step = board.common(sl).Volume / 0.2
    a_gen = pcb_gen.common(sl).Volume / 0.2
    a_com = board.common(pcb_gen).common(sl).Volume / 0.2
    log('   Konturvergleich STEP <-> fluidi_params.outline(): Flaeche %.2f / %.2f mm2, Abweichung (sym. Differenz) %.3f mm2'
        % (a_step, a_gen, a_step + a_gen - 2 * a_com))

    # ---------------------------------------------------------------- B Bauteilhoehen und Zonen
    log('\nB Bauteile: Lage, Hoehe (Modell bzw. Datenblatt), Zone')
    log('   %-5s %-38s %7s %7s %6s %6s  %-26s %s' % ('Ref', 'Footprint', 'x', 'z', 'h_mod', 'h_max', 'Zone (hmax)', 'Befund'))
    rows_bad = []
    for ref in sorted(fps, key=lambda r: (-fps[r]['z'], fps[r]['x'])):
        f = fps[ref]
        h = (PCB['Y_F'] - comps[ref].BoundBox.YMin) if ref in comps else 0.0
        hmax = DS_H.get(ref, (h, ''))[0]
        hmax = max(h, hmax)
        zd = zone_of(f['z'])
        lim = zd['hmax'] if zd else None
        note = ''
        if f['dnp']:
            note = 'DNP'
        elif zd and zd['id'].startswith('Z2'):
            note = ('ok' if hmax <= 2.0 + 0.01 else 'ok nominal, +%.1f Toleranz' % (hmax - 2.0)) if h <= 2.0 + 0.01 else 'ZU HOCH (>2.0)'
        elif ref == 'BT1':
            note = 'ok (Fach 4.1)' if hmax <= 4.1 + 1e-6 else 'ZU HOCH'
        elif ref in ('U3', 'C24'):
            note = 'ok (Feld 0.7)' if hmax <= 0.7 + 1e-6 else 'ZU HOCH'
        elif ref.startswith('TP') or ref == 'AE1':
            note = 'Pad/Kupfer'
        if f['side'] == 'B':
            note = 'B-Seite, Pad'
        if 'ZU HOCH' in note:
            rows_bad.append(ref)
        log('   %-5s %-38s %7.2f %7.2f %6.2f %6.2f  %-26s %s' % (ref, f['fpid'].split(':')[-1][:38], f['x'], f['z'], h, hmax,
                                                               ('%s (%.1f)' % (zd['id'], lim)) if zd else '-', note))
    log('   -> Hoehenueberschreitungen: %s' % (', '.join(rows_bad) or 'keine'))
    log('   Quellen h_max: ' + '; '.join('%s %s' % (k, v[1]) for k, v in DS_H.items()))

    # ---------------------------------------------------------------- C Kollisionen in Endlage
    log('\nC Kollisionen in Endlage (Schnittvolumen > %.0e mm3) und kleinster Abstand je Bauteil' % EPS_V)
    parts = dict(comps)
    parts['CR2032'] = cell
    parts['PCB'] = pcb_gen
    if ant is not None:
        parts['Antenne_Cu'] = ant
    hits = []
    allowed = {('U3', 'Verguss_Kragen'), ('C24', 'Verguss_Kragen')}
    for k, sh in sorted(parts.items()):
        for h in HOUSING:
            if k == 'PCB' and h in CAST:
                continue
            v = inter(sh, S[h])
            if v > EPS_V:
                hits.append((k, h, v, (k, h) in allowed))
    for k, h, v, ok in hits:
        log('   %-12s / %-16s %.4f mm3 %s' % (k, h, v, '(eingegossen, beabsichtigt)' if ok else '<- KOLLISION'))
    n_bad = len([1 for x in hits if not x[3]])
    log('   -> %s' % ('keine Kollision' if not n_bad else '%d Kollisionen' % n_bad))
    if 'BT1' in comps and inter(comps['BT1'], cell) > EPS_V:
        log('   (Clip/Zelle: Kontaktfeder des Modells ungespannt, Ueberdeckung %.2f mm3 beabsichtigt)' % inter(comps['BT1'], cell))
    log('   Kleinste Abstaende (<= 3 mm) Bauteil -> Gehaeuse:')
    mind = {}
    for k in sorted(parts):
        if k == 'PCB':
            continue
        best = []
        for h in HOUSING:
            if (k, h) in allowed:
                continue
            d = dist(parts[k], S[h])
            if d is not None:
                best.append((d, h))
        best.sort()
        mind[k] = best
        if best and best[0][0] < 1.0:
            log('   %-12s %s' % (k, ', '.join('%.2f %s' % b_ for b_ in best[:3])))
    log('   (alle anderen Bauteile >= 1.0 mm zum Gehaeuse)')

    # ---------------------------------------------------------------- D Lage der Platine in z
    log('\nD Lage der Platine in z (Platine + Bauteile + Zelle verschoben, Gehaeuse fest; Kragen per Lehre am Schott)')
    moving = dict(parts)
    fixed = [h for h in HOUSING if h not in CAST]

    def hits_at(dz, names=None):
        out = []
        for k, sh in moving.items():
            m = moved(sh, dz=dz)
            for h in (names or fixed):
                v = inter(m, S[h])
                if v > EPS_V:
                    out.append((k, h, v))
        return out
    up = None
    for i in range(1, 41):
        dz = 0.05 * i
        hh = hits_at(dz, ['Kappe_blau', 'Kragen', 'Schottkeil', 'Fenster_transluzent', 'Stoessel'])
        if hh:
            up = (dz, hh)
            break
    if up:
        log('   freier Weg nach oben bis zum ersten Anschlag: %.2f mm (%s)' % (up[0], ', '.join('%s/%s' % (a, b) for a, b, _ in up[1][:4])))
    else:
        log('   freier Weg nach oben > 2.0 mm (kein Anschlag)')
    for dz in (-0.25, 0.25, 0.4, 0.7):
        hh = hits_at(dz)
        log('   dz %+.2f mm: %s' % (dz, ', '.join('%s/%s %.3f mm3' % x for x in hh) or 'keine Kollision'))

    # ---------------------------------------------------------------- E Clip, Zelle, Schott, Kragen
    log('\nE Batterieclip Keystone 3034 und CR2032')
    f = fps['BT1']
    cb = comps['BT1'].BoundBox
    log('   Footprint %s, Zellmitte (x %.2f, z %.2f), Drehung %.0f Grad' % (f['fpid'], f['x'], f['z'], f['rot']))
    log('   Clipkoerper (Modell): x %.2f ... %.2f, z %.2f ... %.2f, Hoehe %.2f (Schnittstelle Rev B: x %.1f ... %.1f, z %.1f ... %.1f)'
        % (cb.XMin, cb.XMax, cb.ZMin, cb.ZMax, PCB['Y_F'] - cb.YMin, -7.0, 9.1, 7.5, 30.6))
    # Anschlaege (Lappen bis zur Platine) auf der -x-Seite = geschlossenes Ende
    low = comps['BT1'].common(box(-20, 20, PCB['Y_F'] - 1.5, PCB['Y_F'] - 0.4, 0, 40))
    stops = [so.BoundBox for so in low.Solids if so.BoundBox.XMax < f['x'] - 4]
    if stops:
        log('   Anschlaglappen (reichen bis 0.4 mm ueber F): x %.2f ... %.2f -> geschlossenes Ende -x, Einschub/Ausschub +x (bestaetigt)'
            % (min(s.XMin for s in stops), max(s.XMax for s in stops)))
    pz0 = min(p['z'][0] for p in f['pads'] if p['num'] == '1')
    pz1 = max(p['z'][1] for p in f['pads'] if p['num'] == '1')
    log('   Clip-Pads (VBAT): z %.3f ... %.3f; Z3 beginnt z %.2f (Verguss %.2f), Z5B endet z %.2f (Kragen %.2f)'
        % (pz0, pz1, Z['BULK0'] - 0.5, Z['BULK0'], Z['COL1'] + 0.2, Z['COL1']))
    log('     -> Pad ragt %.2f mm in Z3, Luft zum Schott-Verguss %.2f mm; ragt %.2f mm in Z5B, Luft zum Kragen %.2f mm'
        % (pz1 - (Z['BULK0'] - 0.5), Z['BULK0'] - pz1, (Z['COL1'] + 0.2) - pz0, pz0 - Z['COL1']))
    log('     Fach (Kragen-Oberkante bis Schott-Unterkante) %.2f mm, Clip ueber Pads %.2f mm -> Rest %.2f mm (je Seite %.2f)'
        % (Z['BULK0'] - Z['COL1'], pz1 - pz0, Z['BULK0'] - Z['COL1'] - (pz1 - pz0), (Z['BULK0'] - Z['COL1'] - (pz1 - pz0)) / 2))
    for dzc in (-0.4, 0.4):
        log('     Variante Zelle/Clip %+.1f mm in z: Pads z %.2f ... %.2f -> Luft Kragen %.2f, Schott %.2f mm'
            % (dzc, pz0 + dzc, pz1 + dzc, pz0 + dzc - Z['COL1'], Z['BULK0'] - pz1 - dzc))
    zc = f['z']
    w = FP.CLIP['W']
    log('     Pad-Spanne auf Katalogminimum W %.1f (LS-W1 a): Pads z %.2f ... %.2f -> Luft Kragen %.2f, Schott %.2f mm'
        % (w, zc - w / 2, zc + w / 2, zc - w / 2 - Z['COL1'], Z['BULK0'] - zc - w / 2))
    tol = math.sqrt(0.2 ** 2 + 0.1 ** 2)
    log('     Toleranz Lage Pad zur Vergusskante mit Anschlag (Rev C): JLC-Kontur +-0.2 (JLCPCB_NOTES Kap. 3), FDM Anschlag->Schott '
        '+-0.1, Lehre +-0.1 (nur Kragen) -> Schott +-%.2f (RSS) / +-0.30 (worst), Kragen +-%.2f (RSS) / +-0.40 (worst)'
        % (tol, math.sqrt(0.2 ** 2 + 0.1 ** 2 + 0.1 ** 2)))
    log('     Fachlaenge fuer >= 0.3 mm inkl. Toleranz (RSS): %.2f + 2 x 0.30 + %.2f + %.2f = %.2f mm (heute %.2f, fehlt %.2f)'
        % (w, tol, 0.245, w + 0.6 + tol + 0.245, Z['BULK0'] - Z['COL1'], w + 0.6 + tol + 0.245 - (Z['BULK0'] - Z['COL1'])))
    for h in ('Kragen', 'Verguss_Kragen', 'Schottkeil', 'Verguss_Schott', 'Kappe_blau', 'Huelse_grau', 'ORing_Kragen', 'ORing_Zapfen'):
        d1 = dist(comps['BT1'], S[h], 5.0)
        d2 = dist(cell, S[h], 5.0)
        log('   Abstand Clip / Zelle - %-16s %s / %s' % (h, '%.2f' % d1 if d1 is not None else '> 5', '%.2f' % d2 if d2 is not None else '> 5'))
    # Ausschieben +x ohne Huelse
    blk = None
    for d in [0.5 * i for i in range(1, 61)]:
        c = moved(cell, dx=d)
        for h in ('Kragen', 'Kappe_blau', 'Mutter_M2', 'Verguss_Kragen', 'Schottkeil', 'Verguss_Schott'):
            if inter(c, S[h]) > EPS_V:
                blk = (d, h); break
        if not blk:
            for k, sh in comps.items():
                if k != 'BT1' and inter(c, sh) > EPS_V:
                    blk = (d, k); break
        if blk:
            break
    log('   Zelle 30 mm nach +x aus-/einschieben (Huelse abgezogen), gegen Gehaeuse und alle Bauteile ausser Clip: %s'
        % ('frei' if not blk else 'blockiert bei %.1f mm (%s)' % blk))
    log('   Zelle in montierter Huelse: Weg bis Seitenwand %.2f mm (Clip haelt die Zelle)'
        % (FP.SLEEVE_IN['X'] - (f['x'] + FP.CELL['D'] / 2)))
    # Zelle nach -x (geschlossenes Ende): Testpads
    tps = [fps[r] for r in ('TP1', 'TP2', 'TP3') if r in fps]
    if tps:
        log('   Testpads TP1-TP3 x %.2f ... %.2f; Zellrand x %.2f -> Abstand %.2f mm (Ausschub +x)'
            % (min(min(p['x'][0] for p in t['pads']) for t in tps), max(max(p['x'][1] for p in t['pads']) for t in tps),
               f['x'] - FP.CELL['D'] / 2, (f['x'] - FP.CELL['D'] / 2) - max(max(p['x'][1] for p in t['pads']) for t in tps)))

    # ---------------------------------------------------------------- F Taster SW1
    log('\nF Taster SW1 gegen Biegezunge der Kappe')
    f = fps['SW1']
    T = FP.TONGUE
    sb = comps['SW1'].BoundBox
    log('   SW1 %s, Mitte (%.2f, %.2f), Drehung %.0f; Pads %s' % (f['fpid'], f['x'], f['z'], f['rot'],
        ', '.join('x %.2f...%.2f z %.2f...%.2f' % (p['x'] + p['z']) for p in f['pads'])))
    log('   Modell x %.2f ... %.2f, z %.2f ... %.2f, Oberseite y %.2f (h %.2f)' % (sb.XMin, sb.XMax, sb.ZMin, sb.ZMax, sb.YMin, PCB['Y_F'] - sb.YMin))
    a = FP.SW['ACT_D'] / 2
    log('   Betaetiger Ø%.1f: x %.2f ... %.2f, z %.2f ... %.2f; Zunge x %.1f ... %.1f, z ab %.1f -> seitliche Reserve %.2f / %.2f mm, '
        'Reserve unten %.2f mm' % (FP.SW['ACT_D'], f['x'] - a, f['x'] + a, f['z'] - a, f['z'] + a, T['X0'], T['X1'], T['Z_TIP'],
                                   f['x'] - a - T['X0'], T['X1'] - (f['x'] + a), f['z'] - a - T['Z_TIP']))
    gap = sb.YMin - T['Y1']
    log('   Spalt Zunge - Betaetiger (Modell): %.2f mm (Soll 0.20); mit h_max 2.1: %.2f mm' % (gap, PCB['Y_F'] - 2.1 - T['Y1']))
    d = dist(comps['SW1'], S['Kappe_blau'])
    log('   kleinster Abstand SW1 - Kappe: %.2f mm' % d)

    # ---------------------------------------------------------------- G LED D1 unter dem Tropfen
    log('\nG RGB-LED D1 unter dem Tropfenfenster')
    f = fps['D1']
    log('   D1 %s Mitte (%.2f, %.2f), Drehung %.0f; Tropfen-/Lichtschaftmitte (%.2f, %.2f) -> Versatz %.2f mm (Tol. LED +-0.3)'
        % (f['fpid'], f['x'], f['z'], f['rot'], FP.DROP['X'], FP.DROP['ZC'], math.hypot(f['x'] - FP.DROP['X'], f['z'] - FP.DROP['ZC'])))
    log('   Abstand LED-Oberseite (0.6 / max 0.7) - Lichtschaft y %.2f: %.2f / %.2f mm (Ziel 1.5 ... 2.5)'
        % (FP.DROP['BOSS_Y1'], PCB['Y_F'] - 0.6 - FP.DROP['BOSS_Y1'], dist(comps['D1'], S['Fenster_transluzent'])))
    near = []
    for ref, ff in fps.items():
        if ref == 'D1' or ff['side'] != 'F' or ref not in comps:
            continue
        x0, x1, z0, z1 = ff['crt']
        dx = max(x0 - f['x'], f['x'] - x1, 0); dz = max(z0 - f['z'], f['z'] - z1, 0)
        if math.hypot(dx, dz) < 1.8:
            near.append('%s h %.2f' % (ref, PCB['Y_F'] - comps[ref].BoundBox.YMin))
    log('   Bauteile mit Courtyard im Kreis r 1.8 um D1: %s (Regel: nur h <= 0.6)' % (', '.join(near) or 'keine'))
    log('   Lichtschaft Ø3.0 im Zapfen: Abstand zu Bauteilen ausser D1: %.2f mm'
        % min([dist(comps[r], S['Fenster_transluzent']) or 9 for r in comps if r != 'D1']))

    # ---------------------------------------------------------------- H Antenne
    log('\nH Antenne AE1')
    f = fps['AE1']
    xs = [p[0] for poly in f['cu'] for p in poly]; zs = [p[1] for poly in f['cu'] for p in poly]
    log('   Footprint %s, Speisepunkt (%.2f, %.2f); Kupfer x %.2f ... %.2f, z %.2f ... %.2f (Z1 z %.1f ... %.1f)'
        % (f['fpid'], f['x'], f['z'], min(xs), max(xs), min(zs), max(zs), Z['ANT0'], Z['ANT1']))
    log('   %s' % ('Variante _Right: Einspeisung/Kurzschluss links, offenes Ende rechts (wie Schnittstelle verlangt)'
                   if f['fpid'].endswith('_Right') else 'Variante: %s (pruefen)' % f['fpid']))
    for h in PLASTIC + METAL_HOUSING + ['Verguss_Kragen', 'Verguss_Schott']:
        d = dist(ant, S[h], 60.0)
        log('   Abstand Antennenkupfer - %-20s %s' % (h, '%.2f mm' % d if d is not None else '> 60 mm'))
    for k in ('BT1', 'SW1'):
        log('   Abstand Antennenkupfer - %-20s %.2f mm (Metall)' % (k + ' (Bauteil)', ant.distToShape(comps[k])[0]))
    log('   Abstand Antennenkupfer - %-20s %.2f mm (Metall)' % ('CR2032', ant.distToShape(cell)[0]))

    # ---------------------------------------------------------------- I Kragen, Verguss
    log('\nI Kragen und Kragenverguss (Z5A/Z5B)')
    kp = FP.KPOCKET
    low_parts = [r for r, ff in fps.items() if ff['z'] < Z['COL1'] + 0.2 and ff['side'] == 'F' and r not in ('AE1',)]
    log('   Bauteile unterhalb z %.1f: %s' % (Z['COL1'] + 0.2, ', '.join(sorted(low_parts)) or 'keine'))
    for r in ('U3', 'C24'):
        if r not in fps:
            continue
        ff = fps[r]
        b_ = comps[r].BoundBox
        px0 = min(p['x'][0] for p in ff['pads']); px1 = max(p['x'][1] for p in ff['pads'])
        pz0 = min(p['z'][0] for p in ff['pads']); pz1 = max(p['z'][1] for p in ff['pads'])
        log('   %-4s Koerper x %.2f ... %.2f z %.2f ... %.2f h %.2f; Pads x %.2f ... %.2f z %.2f ... %.2f; Courtyard x %.2f ... %.2f z %.2f ... %.2f'
            % (r, b_.XMin, b_.XMax, b_.ZMin, b_.ZMax, PCB['Y_F'] - b_.YMin, px0, px1, pz0, pz1, *ff['crt']))
        log('        Tasche x %.1f ... %.1f, z %.1f ... %.1f, Tiefe %.1f: Rand x %.2f / %.2f, z oben %.2f; Epoxid ueber Koerper %.2f mm (h_max %.2f: %.2f); '
            'Abstand Kragen %.2f, Mutter %.2f mm'
            % (kp['X0'], kp['X1'], kp['Z0'], kp['Z1'], kp['DEPTH'], b_.XMin - kp['X0'], kp['X1'] - b_.XMax, kp['Z1'] - b_.ZMax,
               kp['DEPTH'] - (PCB['Y_F'] - b_.YMin), DS_H.get(r, (PCB['Y_F'] - b_.YMin,))[0],
               kp['DEPTH'] - DS_H.get(r, (PCB['Y_F'] - b_.YMin,))[0], comps[r].distToShape(S['Kragen'])[0],
               comps[r].distToShape(S['Mutter_M2'])[0]))
        log('        Feld K-2 x -9.0 ... -4.6, z 4.4 ... 6.8: Pads %s' %
            ('innerhalb' if px0 >= -9.0 and px1 <= -4.6 and pz0 >= 4.4 and pz1 <= 6.8 else 'AUSSERHALB'))

    # ---------------------------------------------------------------- J Schott
    log('\nJ Schott (Verguss z %.1f ... %.1f, Z3 z %.1f ... %.1f)' % (Z['BULK0'], Z['BULK1'], Z['BULK0'] - 0.5, Z['BAND0']))
    inz3 = []
    for r, ff in fps.items():
        for p in ff['pads']:
            if p['z'][1] > Z['BULK0'] - 0.5 and p['z'][0] < Z['BAND0']:
                inz3.append('%s Pad %s z %.2f ... %.2f' % (r, p['num'], p['z'][0], p['z'][1]))
    log('   Pads in Z3: %s' % (', '.join(inz3) or 'keine'))
    band = [r for r, ff in fps.items() if ff['side'] == 'F' and ff['z'] > Z['BULK1'] and r in comps]
    zlow = min(comps[r].BoundBox.ZMin for r in band)
    rl = min(band, key=lambda r: comps[r].BoundBox.ZMin)
    log('   tiefstes Bauteil im Band: %s Unterkante z %.2f -> %.2f mm ueber Schott-Oberkante (Verguss, Keil)' % (rl, zlow, zlow - Z['BULK1']))

    # ---------------------------------------------------------------- K Einschieben von unten
    log('\nK Platine (STEP, mit Clip, ohne Zelle) 60 mm von unten durch das Schott einschieben')
    mov = {k: v for k, v in parts.items() if k != 'CR2032'}
    tgt = ['Kappe_blau', 'Fenster_transluzent', 'Stoessel']
    hitp = None
    for i in range(120, 0, -1):
        dz = -0.5 * i
        for k, sh in mov.items():
            m = moved(sh, dz=dz)
            for h in tgt:
                if inter(m, S[h]) > EPS_V:
                    hitp = (dz, k, h); break
            if hitp: break
        if hitp: break
    log('   %s' % ('frei' if not hitp else 'Kollision bei dz %.1f mm: %s / %s' % hitp))

    # ---------------------------------------------------------------- L Huelse abziehen
    log('\nL Huelse 160 mm nach unten ueber die Sonde abziehen (mit STEP-Bauteilen und Zelle)')
    first = None
    kern = dict(parts)
    for d in range(1, 161):
        m = moved(sl_plain, dz=-d)
        for k, sh in kern.items():
            if inter(m, sh) > 1e-3:
                first = (d, k); break
        if first: break
    log('   %s' % ('frei' if not first else 'Kollision bei %d mm mit %s' % first))

    # ---------------------------------------------------------------- Export
    housing_c = [S[h] for h in HOUSING]
    asm = Part.makeCompound(housing_c + [pcb_gen] + list(comps.values()) + [cell] + ([ant] if ant else []))
    asm.exportStep(os.path.join(OUT, 'fluidi_sensor_mit_pcb.step'))
    open(os.path.join(OUT, 'collision_pcb_step.txt'), 'w').write('\n'.join(LOG) + '\n')
    print('geschrieben:', os.path.join(OUT, 'collision_pcb_step.txt'))


main()
