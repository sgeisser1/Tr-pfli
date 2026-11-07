# -*- coding: utf-8 -*-
"""fluidi P3 "Stele" - zentrale Parameter Sensor (Schnittstelle PCB <-> Gehaeuse) und Gateway G1 v3.

Einzige Quelle fuer Masse: mechanical/gen/fluidi_sensor.py, fluidi_gateway.py, fem_probe.py und
mechanical/interfaces/pcb_outline.json (+ .dxf) werden daraus erzeugt.

Lauf (reines Python, kein FreeCAD noetig):  .venv/bin/python mechanical/gen/fluidi_params.py
  -> schreibt mechanical/interfaces/pcb_outline.json und pcb_outline.dxf

Koordinaten KOPF (mm): x = Breite (0 = Mitte, + rechts von vorne gesehen), y = Tiefe (0 = Frontflaeche,
+ nach hinten), z = Hoehe (0 = Kopfunterkante, + nach oben). Rechtshaendig.
Koordinaten KiCad (Layout): X = x, Y = Z_PCB_TOP - z (Ursprung Mitte Platinenoberkante, Y nach unten zur
Sondenspitze). Ansicht von vorne = KiCad-Top-View, F.Cu (bestueckte Seite) zeigt nach vorne (-y, Fenster).

Quellen und Annahmen: docs/interfaces/PCB_OUTLINE.md (Kap. Quellen). ANNAHMEN sind dort markiert.
"""
import json
import math
import os

REV = 'A'
REV_DATE = '2026-11-07'
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# ----------------------------------------------------------------------------- Kopf aussen (D-010, freigegeben)
HEAD = dict(W=28.0, D=13.0, H=48.0, CF=2.5, CB=1.0, TOP_CH=1.0,
            Z_FUGE=37.0, GAP_FUGE=0.3,             # Sichtfuge 36.7 ... 37.0
            WALL=1.6, FLOOR=2.0, CEIL=2.0,
            CLR_SLIDE=0.2,                         # Gleitspalt Zapfen/Kragen zu Huelse innen, je Seite
            SKIRT_T=0.8, RIM_T=0.7, RIM_TOP=38.2, SLOT_TOP=38.4,   # Dachziegel (S3-W3)
            GAP_SOIL=5.0)                          # Kopfunterkante bis Erde (Markierung max. Stecktiefe)

# ----------------------------------------------------------------------------- Leiterplatte
PCB = dict(T=1.6, Y_F=7.4,                         # F.Cu-Flaeche (bestueckt) bei y = 7.4, B-Seite y = 9.0
           W=20.0,                                 # durchgehend 20 mm (Kopf und Sonde)
           Z_TOP=44.0, Z_TIP=-105.0, TIP_FLAT=5.0, # Spitze 45 Grad: flach 5.0 mm breit
           T_COAT_MAX=2.0, W_COAT_MAX=20.4,        # Sonde inkl. Beschichtung max. (ANNAHME, REQ-MECH-07)
           TOL_Z=0.2)                              # Lage der Platine im Kern nach Verguss (Lehre), +-
PCB['Y_B'] = PCB['Y_F'] + PCB['T']
PCB['Z_CHAMF'] = PCB['Z_TIP'] + (PCB['W'] - PCB['TIP_FLAT']) / 2.0   # Beginn 45-Grad-Fase
PCB['LENGTH'] = PCB['Z_TOP'] - PCB['Z_TIP']

# ----------------------------------------------------------------------------- O-Ringe (radial, 2 gleiche)
# AS568-017 (= ISO 3601-1 Klasse A): ID 0.676" = 17.17 mm, Schnur 0.070" = 1.78 +- 0.08 mm
# Quelle: docs/references/GTWeed_AS568_StandardOringSizing.pdf, S. 2 (Tabelle Dash -017)
ORING = dict(DASH='AS568-017', ID=17.17, CS=1.78, CS_TOL=0.08,
             GLAND=1.35,                           # radialer Einbauraum -> Verpressung 24 %
             GROOVE_W=2.4, R_BOTTOM=2.0)           # Nutbreite, Eckradius Nutgrund
# Nutgrund-Kontur (Rechteck mit Radius) und Huelse innen (konzentrisch, gleicher Einbauraum ueberall)
_off_in = HEAD['WALL']
SLEEVE_IN = dict(X=HEAD['W'] / 2 - _off_in, Y0=_off_in, Y1=HEAD['D'] - _off_in,
                 R=ORING['R_BOTTOM'] + ORING['GLAND'])
GROOVE_BOT = dict(X=SLEEVE_IN['X'] - ORING['GLAND'], Y0=SLEEVE_IN['Y0'] + ORING['GLAND'],
                  Y1=SLEEVE_IN['Y1'] - ORING['GLAND'], R=ORING['R_BOTTOM'])
LAND = dict(X=SLEEVE_IN['X'] - HEAD['CLR_SLIDE'], Y0=SLEEVE_IN['Y0'] + HEAD['CLR_SLIDE'],
            Y1=SLEEVE_IN['Y1'] - HEAD['CLR_SLIDE'], R=SLEEVE_IN['R'] - HEAD['CLR_SLIDE'])

# ----------------------------------------------------------------------------- Hoehenstapel (z)
Z = dict(FLOOR0=0.0, FLOOR1=HEAD['FLOOR'],
         COL0=2.0, COL_NUT0=2.3, COL_NUT1=3.9, COL_G0=4.3, COL_G1=6.7, COL1=7.3,   # Kragen + Nut + Mutter
         CLIP0=7.5, CLIP1=30.6,                    # Keystone 3034, W = 23.1 in z (gedreht)
         BULK0=30.8, BULK1=32.0,                   # Schott (Verguss)
         SP_G0=31.3, SP_G1=33.7,                   # O-Ring-Nut am Zapfen
         SP_THIN=34.2,                             # oberhalb: Zapfenwand duenner
         BAND0=32.7, BAND1=38.3,                   # Elektronikband (Bauteile F)
         ANT0=38.3, ANT1=44.0,                     # AN043-Antenne
         SLEEVE_TOP=HEAD['Z_FUGE'] - HEAD['GAP_FUGE'])
Z['CELL_C'] = (Z['CLIP0'] + Z['CLIP1']) / 2.0

# ----------------------------------------------------------------------------- Zapfen / Kappe innen
CAP = dict(SP_IN_OFF_LOW=ORING['GLAND'] + _off_in + 0.8,   # Zapfen innen unten (Wand 0.8 hinter Nutgrund) = 3.75
           SP_IN_OFF_HIGH=2.8,                              # Zapfen innen z 34.2 ... 38.4
           CAV_OFF=1.6,                                     # Kappe innen oberhalb 38.4
           BULK_SLOT=dict(X=10.2, Y0=PCB['Y_F'] - 2.2, Y1=PCB['Y_B'] + 0.2),  # Durchfuehrung inkl. Bauteile 2.0
           KEIL_CLR=0.15)

# ----------------------------------------------------------------------------- Bauteile auf der Platine
CELL = dict(D=20.0, T=3.2)                         # CR2032 Nennmass (Panasonic_CR2032_Datasheet_2026-02.pdf S.1)
CLIP = dict(L=16.1, W=23.1, H=4.1, A=21.2,         # Keystone_3034_Catalog_M65.pdf S.1 Zeile 3034
            X0=-10.0, X1=-10.0 + 16.1)             # geschlossenes Ende -x, offenes Ende +x (Ausschub +x)
LED = dict(X=0.0, Z=37.4, LX=1.6, LZ=1.5, H=0.6,    # TUOZHAN 1615 (Elektronikbericht 1.1: 1.6 x 1.5 x 0.6)
           D_TARGET=(1.5, 2.5))                    # Elektronikbericht 1.9
SW = dict(X=-6.0, Z=35.6, BODY=5.1, H=1.5,         # XKB TS-1187A-B-A-B, Datenblatt S.1: 5.1 x 5.1, H = 1.5 (Code A)
          PAD_SPAN_X=7.0, PAD_Z=4.5, PAD_SPAN_Z=4.5, ACT_D=2.0, TRAVEL=0.25, FORCE_N=1.6)
ANT = dict(W=15.2, H=5.7)                          # AN043 (INDEX.csv ANT-AN043)

# ----------------------------------------------------------------------------- Fenster, Taste, Mechanik
DROP = dict(R=2.5, K=2.4, ZC=37.4, X=0.0, T=1.6,   # Tropfen wie Logo/Render (r 2.5, Spitze 6.0 ueber Mitte)
            BOSS_D=3.0, NOTCH_GAP=0.3, GLUE=0.1)    # Klebespalt Fenster je Seite (FDM)
DROP['BOSS_Y1'] = PCB['Y_F'] - LED['H'] - 2.0      # Lichtschaft-Ende -> d = 2.0 mm
BTN = dict(X=0.0, Y=5.5, W=9.0, D=6.0, CH=1.0, PROUD=0.6, STROKE=0.6, POCKET_GAP=0.4, POCKET_D=1.0,
           AX_X=-2.2, AX_Y=4.6,                    # Achse Hals/Membran/Stoessel
           NECK_D=3.0, CB_D=6.4, MEMB_T=0.5, RING_ID=3.4, SKIRT_ID=5.6, WASHER_D=5.0, WASHER_T=0.4,
           STEM_D=3.0, BORE_D=3.2, TUBE_OD=4.0, TUBE_Z0=42.0, BLOCK_Z0=44.4)
TONGUE = dict(X0=-7.6, X1=-4.4, Y0=4.9, Y1=5.7, Z_TIP=34.0,   # Biegezunge (Kappe), Wurzel am Block z 44.4
              COL_X0=-7.8, COL_X1=-4.2, WEDGE_GAP=0.15, Z_CONTACT=40.0)   # Spalte <= 1.5 mm Bauteilhoehe
SCREW = dict(X=0.0, Y=5.0, D=2.0, L=4.0, HEAD_D=3.8, HEAD_H=1.3, HOLE_D=2.4, LIP_D=1.7, LIP_H=0.5,
             NUT_S=4.0, NUT_M=1.6)                 # ISO 7045 M2x4 A2 PH1, ISO 4032 M2 A2 (Nennmasse, ANNAHME bis Bestellung)
SLOT = dict(X=PCB['W_COAT_MAX'] / 2 + 0.2, Y0=PCB['Y_F'] - 0.4, Y1=PCB['Y_B'] + 0.4)  # Sondenschlitz Boden
LOGO = dict(SVG='docs/design/logo/fluidi_logo_v3a_mono.svg', W=16.0, ZC=14.5, RELIEF=0.25)
WARN = dict(ZC=19.0, TRI_W=8.0, TRI_H=9.0, DEPTH=0.3)

# ----------------------------------------------------------------------------- Sperrzonen (Kopfkoordinaten)
def zones():
    """Zonenliste fuer die Schnittstelle. side: F, B oder FB; hmax: max. Bauteilhoehe ueber Platine (mm)."""
    w2 = PCB['W'] / 2
    return [
        dict(id='Z1_ANTENNE', side='FB', x=(-w2, w2), z=(Z['ANT0'], Z['ANT1']), hmax=0.0,
             rule='AN043-IFA (15.2 x 5.7) inkl. Masse-Keepout nach AN043; keine Bauteile, kein Metall des Gehaeuses. '
                  'Kunststoff vor der F-Seite: Stoesselrohr, Finger, Biegezunge (siehe Kap. 5) -> Elektronik bestaetigt.'),
        dict(id='Z2_BAND_F', side='F', x=(-w2, w2), z=(Z['BAND0'], Z['BAND1']), hmax=2.0,
             rule='Elektronikband. Bauteilhoehe <= 2.0 mm (Durchfuehrung durch das Schott beim Einschieben von unten). '
                  'In Spalte x -7.8...-4.2 (Biegezunge) <= 1.5 mm. LED D1 und Taster SW1 fest (Kap. 4).'),
        dict(id='Z2_BAND_B', side='B', x=(-w2, w2), z=(Z['BULK0'] - 0.5, Z['ANT1']), hmax=0.0,
             rule='B-Seite unbestueckt (Economic PCBA einseitig). Freiraum 2.4 mm bis Kappe innen.'),
        dict(id='Z3_SCHOTT', side='FB', x=(-w2, w2), z=(Z['BULK0'] - 0.5, Z['BAND0']), hmax=0.0,
             rule='Schott-Verguss: keine Bauteile, keine Vias, kein Kupfer auf Aussenlagen, Loetstopplack geschlossen. '
                  'Signale nur Innenlagen (M-03, S3-K1).'),
        dict(id='Z4_FACH_F', side='F', x=(-w2, w2), z=(Z['COL1'] + 0.2, Z['BULK0'] - 0.5), hmax=4.1,
             rule='Zellfach: nur Keystone 3034 (gedreht, Ausschub +x), Minuspad, UART-/Testpads (Streifen x 6.6...9.5). '
                  'Unter der Zelle nur Loetstopplack ausser Minuspad (R2-W01 Nr. 2). Keine Vias im Fach (S2-W03). '
                  '2 x 100 kOhm im Elektronikraum (R2-A3).'),
        dict(id='Z4_FACH_B', side='B', x=(-w2, w2), z=(Z['COL1'] + 0.2, Z['BULK0'] - 0.5), hmax=0.0,
             rule='Silkscreen Warnsymbol Dreieck >= 7 x 9 mm + "CR2032" (S3-W4, zweiter Ort zusaetzlich zur Huelse).'),
        dict(id='Z5_KRAGEN', side='FB', x=(-w2, w2), z=(Z['COL0'] - 0.5, Z['COL1'] + 0.2), hmax=0.0,
             rule='Kragen-Verguss = Sondendichtung (S3-K2, REQ-MECH-08/15): keine Bauteile, keine Vias, kein Kupfer '
                  'auf Aussenlagen. Mutter M2 liegt 0.2 mm vor der F-Seite (eingegossen).'),
        dict(id='Z6_FREI', side='FB', x=(-w2, w2), z=(-HEAD['GAP_SOIL'], Z['COL0'] - 0.5), hmax=0.0,
             rule='Zwischen Erde und Kragen: keine Elektroden (Luftanteil), Silkscreen Logo (F) und "max"/Revision (B).'),
        dict(id='Z7_SONDE', side='FB', x=(-w2, w2), z=(PCB['Z_TIP'], -HEAD['GAP_SOIL']), hmax=0.0,
             rule='Sonde: Elektroden nur Innenlagen, Aussenlagen ohne Kupfer (REQ-MECH-04), Kupfer >= 1.0 mm zur Kontur '
                  '(REQ-MECH-06), keine Vias (REQ-MECH-05). Spitze 45 Grad.'),
    ]


def outline():
    """Platinenkontur (Kopfkoordinaten x, z), geschlossen, im Gegenuhrzeigersinn von vorne."""
    w2, f2 = PCB['W'] / 2, PCB['TIP_FLAT'] / 2
    return [(-f2, PCB['Z_TIP']), (f2, PCB['Z_TIP']), (w2, PCB['Z_CHAMF']), (w2, PCB['Z_TOP']),
            (-w2, PCB['Z_TOP']), (-w2, PCB['Z_CHAMF'])]


def to_kicad(x, z):
    return (round(x, 4), round(PCB['Z_TOP'] - z, 4))


def interface_dict():
    zl = zones()
    d = dict(
        title='fluidi Sensor P3 - Schnittstelle PCB-Kontur <-> Gehaeuse',
        revision=REV, date=REV_DATE, status='verbindlich fuer Layout Welle 2 (Aenderung nur ueber neue Revision)',
        generator='mechanical/gen/fluidi_params.py', doc='docs/interfaces/PCB_OUTLINE.md',
        units='mm',
        coordinate_systems=dict(
            head='x Breite (+ rechts von vorne), y Tiefe (0 = Front, + hinten), z Hoehe (0 = Kopfunterkante)',
            kicad='X = x, Y = %.1f - z (Ursprung Mitte Oberkante, Y nach unten), Top-View = Ansicht von vorne, '
                  'F.Cu = bestueckte Seite zeigt zum Fenster (-y)' % PCB['Z_TOP']),
        board=dict(thickness=PCB['T'], layers=4, width=PCB['W'], length=PCB['LENGTH'],
                   z_top=PCB['Z_TOP'], z_tip=PCB['Z_TIP'], tip='45 Grad, flach %.1f mm' % PCB['TIP_FLAT'],
                   y_front_F=PCB['Y_F'], y_back_B=PCB['Y_B'], assembly='einseitig F (JLC Economic)',
                   z_position_tol=PCB['TOL_Z'],
                   probe_max_incl_coating=dict(thickness=PCB['T_COAT_MAX'], width=PCB['W_COAT_MAX']),
                   outline_head_xz=outline(),
                   outline_kicad_XY=[to_kicad(x, z) for x, z in outline()]),
        markings=dict(
            max_insertion=dict(z=-HEAD['GAP_SOIL'], kicad_Y=to_kicad(0, -HEAD['GAP_SOIL'])[1], sides='F+B',
                               silkscreen='Linie 0.2 mm, x -9...9, Text "max" + Pfeil'),
            logo_silkscreen=dict(side='F', x=(-9.0, 3.0), z=(-4.4, -0.8), file='docs/design/logo/fluidi_logo_v3a_mono.svg',
                                 width=10.0, note='Strich 0.52 mm >= 0.2 (P3_FLUIDI.md Kap. 5)'),
            revision_silkscreen=dict(side='B', x=(-9.0, 9.0), z=(-4.4, -0.8), text='fluidi rev A'),
            warning_silkscreen=dict(side='B', x=(-8.0, 8.0), z=(9.0, 28.0), text='Dreieck ! + CR2032 + Verschluckgefahr')),
        zones=[dict(z_d, kicad_Y=(to_kicad(0, z_d['z'][1])[1], to_kicad(0, z_d['z'][0])[1])) for z_d in zl],
        components=dict(
            D1_LED=dict(part='TUOZHAN P4-1615G2B2R4TS2-06T-001-24 (C7496855)', side='F', center_xz=(LED['X'], LED['Z']),
                        kicad_XY=to_kicad(LED['X'], LED['Z']), height=LED['H'], tol=0.3,
                        window_inner_face_y=DROP['BOSS_Y1'], d_led_to_window=round(PCB['Y_F'] - LED['H'] - DROP['BOSS_Y1'], 2),
                        note='Leuchtflaeche zum Fenster (-y). Lichtschaft Ø3.0 des Fensters endet 2.0 mm vor der LED.'),
            SW1_TASTER=dict(part='XKB TS-1187A-B-A-B (C318884)', side='F', center_xz=(SW['X'], SW['Z']),
                            kicad_XY=to_kicad(SW['X'], SW['Z']), height=SW['H'], tol=0.2,
                            pads='laut Datenblatt S.1 (7.0 x 4.5 Rastermass), Anschluesse in x-Richtung',
                            actuation='Biegezunge der Kappe drueckt senkrecht (+y) auf den Betaetiger Ø2.0; '
                                      'Taste oben -> Membran -> Stoessel -> 30-Grad-Keil -> Zunge'),
            XBT1_CLIP=dict(part='Keystone 3034TR (C5213768)', side='F', rotation='90 Grad: Einschub in x, offenes Ende +x',
                           cell_center_xz=(0.0, Z['CELL_C']), kicad_XY=to_kicad(0.0, Z['CELL_C']),
                           clip_x=(CLIP['X0'], CLIP['X1']), clip_z=(Z['CLIP0'], Z['CLIP1']), height=CLIP['H'],
                           note='Minuspad innerhalb der Minuskappe (R2-W01 Nr. 1); Zelle Ø20 schliesst buendig mit den '
                                'Platinenkanten ab; Ausschub +x frei bei abgezogener Huelse'),
            ANTENNA=dict(part='AN043 IFA', zone='Z1_ANTENNE', z=(Z['ANT0'], Z['ANT1'])),
            SCREW_NUT=dict(screw='ISO 7045 M2x4 A2 PH1 (unverlierbar, Gewindefurch-Lippe Ø1.7 im Huelsenboden)',
                           nut='ISO 4032 M2 A2 SW4 x 1.6, im Kragen eingegossen',
                           axis_xy=(SCREW['X'], SCREW['Y']), nut_z=(Z['COL_NUT0'], Z['COL_NUT1']),
                           dist_to_pcb_F=round(PCB['Y_F'] - (SCREW['Y'] + SCREW['NUT_S'] / 2), 2),
                           dist_to_antenna_z=round(Z['ANT0'] - Z['COL_NUT1'], 1))),
        seals=dict(
            oring=dict(type=ORING['DASH'], material='Silikon oder EPDM ohne Russ (rot/transluzent), Silikonfett',
                       qty=2, places=dict(spigot_z=(Z['SP_G0'], Z['SP_G1']), collar_z=(Z['COL_G0'], Z['COL_G1'])),
                       gland=ORING['GLAND'], squeeze_nom=round((ORING['CS'] - ORING['GLAND']) / ORING['CS'], 3)),
            potting=dict(schott_z=(Z['BULK0'], Z['BULK1']), kragen_z=(Z['COL0'], Z['COL1']),
                         material='Epoxid 2K, thixotrop am Schott (ANNAHME Typ, Phase 4b Welle 2)'),
            window_glue_to_oring_groove=round(DROP['ZC'] - DROP['R'] - Z['SP_G1'], 2)),
        height_limits_summary=dict(F_band=2.0, F_band_under_tongue=1.5, F_fach='nur 3034 (4.1)', B='0 (unbestueckt)'),
        open_points=['KRITISCH Elektronik/Orchestrator: Band F 20 x 5.6 = 112 mm2, Bauteilflaeche laut BOM Rev A ca. 251 mm2 '
                     '(Abschaetzung, Huellen inkl. Pads + 0.25 mm) -> passt nicht. Optionen: beidseitig bestuecken (Band B '
                     '+112 mm2, Standard-PCBA), kleinere Bauteile (0201, kleinerer Taster), Kopf hoeher (+1 mm = +20 mm2 je Seite, '
                     'Auftraggeber), Bauteile im Fach nur mit Freigabe Sicherheit (REQ-SAF-05). Entscheid vor Layout -> Rev B',
                     'Elektronik: Kunststoffteile vor der Antenne (Stoesselrohr, Finger, Zunge, 0.6...2.5 mm vor F) bestaetigen',
                     'Elektronik: Lage SW1/LED gegen Layout bestaetigen (Pads SW1 x -9.5...-2.5)'])
    return d


def write_dxf(path, polylines):
    """Minimales DXF R12 (nur LINE-Entities, Layer je Polylinie) in KiCad-Koordinaten (Y nach unten -> DXF y = -Y)."""
    out = ['0', 'SECTION', '2', 'ENTITIES']
    for layer, pts, closed in polylines:
        seq = list(pts) + ([pts[0]] if closed else [])
        for (x0, y0), (x1, y1) in zip(seq[:-1], seq[1:]):
            out += ['0', 'LINE', '8', layer, '10', '%.4f' % x0, '20', '%.4f' % -y0, '30', '0.0',
                    '11', '%.4f' % x1, '21', '%.4f' % -y1, '31', '0.0']
    out += ['0', 'ENDSEC', '0', 'EOF']
    with open(path, 'w') as f:
        f.write('\n'.join(out) + '\n')


def main():
    od = os.path.join(REPO, 'mechanical', 'interfaces')
    os.makedirs(od, exist_ok=True)
    d = interface_dict()
    with open(os.path.join(od, 'pcb_outline.json'), 'w') as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    polys = [('Edge.Cuts', [to_kicad(x, z) for x, z in outline()], True)]
    for zd in zones():
        x0, x1 = zd['x']; z0, z1 = zd['z']
        polys.append(('Zone_' + zd['id'], [to_kicad(x0, z0), to_kicad(x1, z0), to_kicad(x1, z1), to_kicad(x0, z1)], True))
    # Bauteil-Umrisse (Lage)
    def rect(cx, cz, wx, wz):
        return [to_kicad(cx - wx / 2, cz - wz / 2), to_kicad(cx + wx / 2, cz - wz / 2),
                to_kicad(cx + wx / 2, cz + wz / 2), to_kicad(cx - wx / 2, cz + wz / 2)]
    polys.append(('Comp_D1', rect(LED['X'], LED['Z'], LED['LX'], LED['LZ']), True))
    polys.append(('Comp_SW1_body', rect(SW['X'], SW['Z'], SW['BODY'], SW['BODY']), True))
    polys.append(('Comp_XBT1_clip', [to_kicad(CLIP['X0'], Z['CLIP0']), to_kicad(CLIP['X1'], Z['CLIP0']),
                                     to_kicad(CLIP['X1'], Z['CLIP1']), to_kicad(CLIP['X0'], Z['CLIP1'])], True))
    n = 48
    polys.append(('Comp_Cell', [to_kicad(10 * math.cos(2 * math.pi * i / n), Z['CELL_C'] + 10 * math.sin(2 * math.pi * i / n))
                                for i in range(n)], True))
    polys.append(('Mark_max', [to_kicad(-9, -HEAD['GAP_SOIL']), to_kicad(9, -HEAD['GAP_SOIL'])], False))
    write_dxf(os.path.join(od, 'pcb_outline.dxf'), polys)
    print('geschrieben:', os.path.join(od, 'pcb_outline.json'), os.path.join(od, 'pcb_outline.dxf'))
    print('LED-Fenster-Abstand d = %.2f mm' % d['components']['D1_LED']['d_led_to_window'])
    print('O-Ring Nutgrund-Umfang %.2f mm -> Passung ID %.2f, AS568-017 ID %.2f, Dehnung %.1f %%' % oring_fit())


def oring_fit():
    g = GROOVE_BOT
    per = 2 * (2 * g['X'] + (g['Y1'] - g['Y0'])) - 8 * g['R'] + 2 * math.pi * g['R']
    idfit = per / math.pi
    return per, idfit, ORING['ID'], (idfit / ORING['ID'] - 1) * 100


if __name__ == '__main__':
    main()
