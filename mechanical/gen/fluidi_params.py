# -*- coding: utf-8 -*-
"""fluidi P3 "Stele" - zentrale Parameter Sensor (Schnittstelle PCB <-> Gehaeuse) und Gateway G1 v3.

Einzige Quelle fuer Masse: mechanical/gen/fluidi_sensor.py, fluidi_gateway.py, fem_probe.py, pcb_rev_b_floorplan.py
und mechanical/interfaces/pcb_outline.json (+ .dxf) werden daraus erzeugt.

Lauf (reines Python, kein FreeCAD noetig):  .venv/bin/python mechanical/gen/fluidi_params.py
  -> schreibt mechanical/interfaces/pcb_outline.json und pcb_outline.dxf
  (pcb_rev_b_floorplan.py ruft main() mit den Planbloecken auf und ergaenzt die DXF um Layer Plan_*)

Koordinaten KOPF (mm): x = Breite (0 = Mitte, + rechts von vorne gesehen), y = Tiefe (0 = Frontflaeche,
+ nach hinten), z = Hoehe (0 = Kopfunterkante, + nach oben). Rechtshaendig.
Koordinaten KiCad (Layout): X = x, Y = Z_PCB_TOP - z (Ursprung Mitte Platinenoberkante, Y nach unten zur
Sondenspitze). Ansicht von vorne = KiCad-Top-View, F.Cu (bestueckte Seite) zeigt nach vorne (-y, Fenster).

Revision B (2026-11-07): Kopf V4 34 x 13 x 57.5 (D-019), Platine im Kopf 26 mm, Sonde 20 mm, Option (f) aus
hardware/sensor/out/FLOORPLAN_OPTIONS.md (TS-1088, TMP1075N im Kragen) + Messkette D3 (D-018).
Quellen und Annahmen: docs/interfaces/PCB_OUTLINE.md (Kap. 10). ANNAHMEN sind dort markiert.
"""
import json
import math
import os

REV = 'C'
REV_DATE = '2026-11-08'
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# ----------------------------------------------------------------------------- Kopf aussen (D-019, V4)
HEAD = dict(W=34.0, D=13.0, H=57.5, CF=2.5, CB=1.0, TOP_CH=1.0,
            Z_FUGE=43.5, GAP_FUGE=0.3,             # Sichtfuge 43.2 ... 43.5, Kappe 14.0 mm (D-019)
            WALL=1.6, FLOOR=2.0, CEIL=2.0,
            CLR_SLIDE=0.2,                         # Gleitspalt Zapfen/Kragen zu Huelse innen, je Seite
            SKIRT_T=0.8, RIM_T=0.7,                # Dachziegel (S3-W3): Kappenschuerze aussen ueber dem Huelsenrand
            GAP_SOIL=5.0)                          # Kopfunterkante bis Erde (Markierung max. Stecktiefe)
HEAD['RIM_TOP'] = HEAD['Z_FUGE'] + 1.2             # Huelsenrand ragt 1.2 mm in den Kappenschlitz
HEAD['SLOT_TOP'] = HEAD['RIM_TOP'] + 0.2

# ----------------------------------------------------------------------------- Leiterplatte
PCB = dict(T=1.6, Y_F=6.6,                         # F.Cu (bestueckt) bei y = 6.6 (Rev A 7.4: 0.8 nach vorn, Kap. 2)
           W=20.0,                                 # Sonde und Kragen: 20 mm
           W_HEAD=26.0,                            # Kopf (Fach, Schott, Band, Antenne): 26 mm
           Z_SH0=8.5, Z_SH1=11.5, R_SH=2.0,        # Schulter 45 Grad: 20 -> 26 mm, Innenecke R 2.0 (FEM LC1b)
           Z_TOP=53.5, Z_TIP=-105.0, TIP_FLAT=5.0, # Spitze 45 Grad: flach 5.0 mm breit
           T_COAT_MAX=2.0, W_COAT_MAX=20.4,        # Sonde inkl. Beschichtung max. (ANNAHME, REQ-MECH-07)
           TOL_Z=0.2,                              # Lage der Platine im Kern, +- (Rev C: Anschlag; JLC Kontur +-0.2 + FDM)
           EDGE_CLR=0.3,                           # Courtyard-Rand zur Kontur im Kopf (ANNAHME wie FLOORPLAN_OPTIONS)
           CU_EDGE_PROBE=1.25)                     # Kupfer zur Kontur in der Sonde (simulation/field/REPORT.md Kap. 8)
PCB['Y_B'] = PCB['Y_F'] + PCB['T']
PCB['Z_CHAMF'] = PCB['Z_TIP'] + (PCB['W'] - PCB['TIP_FLAT']) / 2.0   # Beginn 45-Grad-Fase
PCB['LENGTH'] = PCB['Z_TOP'] - PCB['Z_TIP']

# ----------------------------------------------------------------------------- O-Ringe (radial, 2 gleiche)
# AS568-019 (= ISO 3601-1 Klasse A): ID 0.801" = 20.35 mm, Schnur 0.070" = 1.78 +- 0.08 mm
# Quelle: docs/references/GTWeed_AS568_StandardOringSizing.pdf, S. 2 (Tabelle Dash -019)
# Nutgrund-Eckradius 3.0 so gewaehlt, dass die Dehnung ~2 % betraegt (wie Rev A mit -017: 1.9 %).
ORING = dict(DASH='AS568-019', ID=20.35, CS=1.78, CS_TOL=0.08,
             GLAND=1.35,                           # radialer Einbauraum -> Verpressung 24 %
             GROOVE_W=2.4, R_BOTTOM=3.0)           # Nutbreite, Eckradius Nutgrund
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
         SEAL0=2.0, SEAL1=4.2,                     # Dichtstreifen Kragen (Platine, Aussenlagen kupferfrei, keine Vias)
         KCOMP0=4.4, KCOMP1=6.8,                   # Bauteilzone Kragen (U3 + C24), F
         CLIP0=7.5, CLIP1=30.6,                    # Keystone 3034, W = 23.1 in z (gedreht)
         BULK0=30.8, BULK1=32.0,                   # Schott (Verguss)
         SP_G0=31.3, SP_G1=33.7,                   # O-Ring-Nut am Zapfen
         SP_THIN=34.2,                             # oberhalb: Zapfen-Innenraum mit Zungentasche
         STEP_BACK=34.7, STEP_FRONT=36.2,          # Ablaufstufe (geneigt nach hinten) ueber der Zapfen-Nut
         BAND0=32.7, BAND1=47.8,                   # Elektronikband (Bauteile F), 15.1 mm
         ANT0=47.8, ANT1=53.5,                     # AN043-Antenne (5.7 mm)
         SLEEVE_TOP=HEAD['Z_FUGE'] - HEAD['GAP_FUGE'])
Z['CELL_C'] = (Z['CLIP0'] + Z['CLIP1']) / 2.0

# ----------------------------------------------------------------------------- Kern: Zapfen / Kappe innen
# Zapfen-Innenraum als Rechteck mit kleinem Radius (Platine 26 mm + Bauteile 2.0 mm + je 0.2 mm Spiel, wie Schottschlitz).
SP_IN = dict(X=PCB['W_HEAD'] / 2 + 0.2, Y0=PCB['Y_F'] - 2.0 - 0.2, Y1=PCB['Y_B'] + 0.2, R=0.5)
CAP = dict(CAV_OFF=1.6,                                     # Kappe innen oberhalb SLOT_TOP (Wand 1.6)
           RECESS=0.5,                                      # Zapfen aussen ueber der Ablaufstufe: Spalt 0.2 + 0.5 = 0.7
           BULK_SLOT=dict(X=PCB['W_HEAD'] / 2 + 0.2, Y0=PCB['Y_F'] - 2.2, Y1=PCB['Y_B'] + 0.2),  # Durchfuehrung
           KEIL_CLR=0.15)
# Ablauf (Spritzwasser zwischen Sichtschale und Kern): Schlitze in der Huelsenrueckwand an der tiefsten Stelle
DRAIN = dict(XC=(-10.0, -4.0, 4.0, 10.0), W=3.0, H=1.2)    # Unterkante = Z['STEP_BACK']

# ----------------------------------------------------------------------------- Bauteile auf der Platine
CELL = dict(D=20.0, T=3.2)                         # CR2032 Nennmass (Panasonic_CR2032_Datasheet_2026-02.pdf S.1)
CELL['XC'] = PCB['W_HEAD'] / 2 - CELL['D'] / 2     # Zellmitte x = 3.0 (Zelle schliesst buendig mit x = 13)
# Keystone_3034_Catalog_M65.pdf S.1 Zeile 3034: L 16.1, W 23.1 (Clipfuesse aussen), H 4.1, B 7.4.
# Rev C: B ist ab Zellmitte bis zum geraden Quersteg (geschlossenes Ende) bemasst - bestaetigt durch KiCad-Footprint
# (Quersteg 7.39 ab Zellmitte) und KiCad-3D-Modell (Anschlaglappen x -4.76 ... -1.6, collision_pcb_step.txt Kap. E).
# Rev B hatte den Clip faelschlich buendig mit dem Zellrand angenommen (x -7.0 ... 9.1).
CLIP = dict(L=16.1, W=23.1, H=4.1, A=21.2, B=7.4,
            PAD_D=1.27)                            # Pad-Tiefe >= .050 (1.27), Pad Layout Fig. 1
CLIP['X0'] = CELL['XC'] - CLIP['B']                # -4.4: geschlossenes Ende (Anschlag) -x
CLIP['X1'] = round(CLIP['X0'] + CLIP['L'], 3)      # 11.7: offenes Ende +x (Ein-/Ausschub +x)
LED = dict(X=0.0, Z=HEAD['Z_FUGE'] + 0.4, LX=1.6, LZ=1.5, H=0.6,   # TUOZHAN 1615 (Elektronikbericht 1.1)
           D_TARGET=(1.5, 2.5))                    # Elektronikbericht 1.9
SW = dict(PART='XUNPU TS-1088-AR02016 (C720477)', X=-6.0, Z=45.1, BODY_X=3.9, BODY_Z=3.0, H=2.0,
          PAD_CC=4.45, PAD_OUT=5.50, PAD_W=1.05, PAD_L=2.0,          # XUNPU_TS-1088-AR02016_Datasheet S.1
          ACT_D=1.8, TRAVEL=0.2, FORCE_N=1.57)                       # Hub 0.2 +-0.1, 160 gf
ANT = dict(W=15.2, H=5.7,                          # AN043 (INDEX.csv ANT-AN043)
           FP='RF_Antenna:Texas_SWRA117D_2.4GHz_Right',   # Einspeisung links, offenes Ende rechts (Layout Rev B, L-5)
           X0=-2.2, X1=12.2, Z0=47.8, Z1=53.2, FEED_X=0.35)   # Kupfer laut Layout Rev B (Speisepunkt X 0.35)
TMP = dict(PART='TI TMP1075NDRLR SOT-563 (C3663690) + C24 100 nF 0402', X0=-9.0, X1=-4.6, Z0=4.6, Z1=6.6, H=0.7)   # Huelle im Feld K-2 (x -9.0...-4.6, z 4.4...6.8)
KPOCKET = dict(X0=-9.6, X1=-4.4, DEPTH=1.2, Z0=Z['COL0'], Z1=Z['KCOMP1'])   # Tasche im Kragen vor F, unten offen
TPSTRIP = dict(X0=-PCB['W_HEAD'] / 2 + PCB['EDGE_CLR'], X1=CELL['XC'] - CELL['D'] / 2 - 0.5, Z0=12.0, Z1=30.0)

# ----------------------------------------------------------------------------- Fenster, Taste, Mechanik
DROP = dict(R=2.5, K=2.4, ZC=LED['Z'], X=0.0, T=1.6,   # Tropfen wie Logo/Render (r 2.5, Spitze 6.0 ueber Mitte)
            BOSS_D=3.0, NOTCH_GAP=0.3, GLUE=0.1)        # Klebespalt Fenster je Seite (FDM)
DROP['BOSS_Y1'] = PCB['Y_F'] - LED['H'] - 2.0      # Lichtschaft-Ende -> d = 2.0 mm
_dz = HEAD['H'] - 48.0                             # Tastenmechanik wie Rev A, an der Kappenoberseite verankert (+9.5)
BTN = dict(X=0.0, Y=5.5, W=9.0, D=6.0, CH=1.0, PROUD=0.6, STROKE=0.6, POCKET_GAP=0.4, POCKET_D=1.0,
           AX_X=-2.2, AX_Y=PCB['Y_F'] - 2.8,       # Achse Hals/Membran/Stoessel
           NECK_D=3.0, CB_D=6.4, MEMB_T=0.5, RING_ID=3.4, SKIRT_ID=5.6, WASHER_D=5.0, WASHER_T=0.4,
           STEM_D=3.0, BORE_D=3.2, TUBE_OD=4.0, TUBE_Z0=42.0 + _dz, BLOCK_Z0=PCB['Z_TOP'] + 0.4)
# Rev C: Anschlag + Gabel fuer die Platinenoberkante in der Kappe (links neben der Antenne, x -8.0 ... -3.0).
# Die Platine liegt beim Schott-Verguss (Kappe kopfueber) durch ihr Gewicht am Anschlag -> Lage in z definiert
# (Rev B: 0.4/0.7 mm Luft zum Tastenblock, Lage 0 ... +0.7 unbestimmt). Gabel fuehrt die Oberkante in y.
PSTOP = dict(X0=-8.0, X1=-3.0, FORK=1.5, T=0.8, CLR_F=0.05, CLR_B=0.15)
_ty1 = PCB['Y_F'] - SW['H'] - 0.2                  # Zunge 0.2 vor dem Betaetiger
TONGUE = dict(X0=-7.6, X1=-4.4, Y0=_ty1 - 0.8, Y1=_ty1, Z_TIP=SW['Z'] - 1.6,   # Biegezunge (Kappe)
              COL_X0=-7.8, COL_X1=-4.2, WEDGE_GAP=0.15, Z_CONTACT=40.0 + _dz)
SCREW = dict(X=0.0, D=2.0, L=4.0, HEAD_D=3.8, HEAD_H=1.3, HOLE_D=2.4, LIP_D=1.7, LIP_H=0.5,
             NUT_S=4.0, NUT_M=1.6)                 # ISO 7045 M2x4 A2 PH1, ISO 4032 M2 A2 (Nennmasse, ANNAHME bis Bestellung)
SCREW['Y'] = PCB['Y_F'] - 0.4 - SCREW['NUT_S'] / 2  # Mutter 0.4 mm vor F (4.2)
SLOT = dict(X=PCB['W_COAT_MAX'] / 2 + 0.2, Y0=PCB['Y_F'] - 0.4, Y1=PCB['Y_B'] + 0.4)  # Sondenschlitz Boden
# Logo waechst mit der Breite (16 mm bei 28 mm) und sitzt bei 39 % der Huelsenhoehe (PROPORTIONEN.md)
LOGO = dict(SVG='docs/design/logo/fluidi_logo_v3a_mono.svg', W=round(16.0 * HEAD['W'] / 28.0, 2),
            ZC=round(14.5 / 37.0 * HEAD['Z_FUGE'], 2), RELIEF=0.25)
WARN = dict(ZC=19.0, TRI_W=8.0, TRI_H=9.0, DEPTH=0.3)


# ----------------------------------------------------------------------------- Sperrzonen (Kopfkoordinaten)
def zones():
    """Zonenliste fuer die Schnittstelle. side: F, B oder FB; hmax: max. Bauteilhoehe ueber Platine (mm)."""
    w2, h2, w2p = PCB['W_HEAD'] / 2, PCB['W_HEAD'] / 2, PCB['W'] / 2
    return [
        dict(id='Z1_ANTENNE', side='FB', x=(-h2, h2), z=(Z['ANT0'], Z['ANT1']), hmax=0.0,
             rule='AN043-IFA 15.2 x 5.7, Footprint RF_Antenna:Texas_SWRA117D_2.4GHz_Right (Einspeisung links, offenes Ende '
                  'rechts; Rev B nannte faelschlich _Left, L-5). Lage Layout Rev B: Speisepunkt X 0.35, Kupfer x -2.2...12.2, '
                  'z 47.8...53.2, Keepout alle Lagen x -2.7...12.5. Ganze Zone ohne Bauteile, neben und ueber der Antenne kein '
                  'Kupfer (AN043). Kein Metall des Gehaeuses. Platinenanschlag der Kappe x -8.0...-3.0 (Kunststoff, 0.8 mm '
                  'neben dem Antennenkupfer), dort Kupfer F/B erlaubt (ausserhalb Keepout).'),
        dict(id='Z2_BAND_F', side='F', x=(-h2, h2), z=(Z['BAND0'], Z['BAND1']), hmax=2.0,
             rule='Elektronikband 26 x 15.1 = 392.6 mm2 (Bedarf 382.3 mm2 = 254.9 Courtyard x 1.5, Kap. 4). Bauteilhoehe <= 2.0 mm ueberall '
                  '(Einschieben von unten durch das Schott; Zunge 0.2 vor SW1). Courtyards >= 0.3 mm zur Kontur. '
                  'D1 und SW1 fest (Kap. 5). Lichtschaft vor D1: Ø3.0, endet 2.0 mm vor der LED-Oberseite.'),
        dict(id='Z2_BAND_B', side='B', x=(-h2, h2), z=(Z['BULK0'] - 0.5, Z['ANT0']), hmax=0.0,
             rule='Unbestueckt (Economic PCBA einseitig). Kupfer und Testpads erlaubt (TP PROBE_SENSE, TP4 OSZ_OUT, GND), '
                  'Zugang nur vor dem Einschieben (Pogo). Freiraum hinter B: 0.2 mm (Zapfen), 3.2 mm (Kappe, z > 44.9).'),
        dict(id='Z3_SCHOTT', side='FB', x=(-h2, h2), z=(Z['BULK0'] - 0.5, Z['BAND0']), hmax=0.0,
             rule='Schott-Verguss z 30.8...32.0: keine Bauteile, keine Vias, kein Kupfer auf Aussenlagen, Loetstopplack '
                  'geschlossen. Signale nur Innenlagen (M-03, S3-K1). Ausnahme Rev C: Clip-Pads XBT1 bis z 30.60 '
                  '(Pad-Spanne 23.1, Kap. 5); Abstand Pad - Verguss nominal 0.20 (LS-W1: >= 0.3 inkl. Toleranz erst mit '
                  'Fachverlaengerung, Entscheid offen).'),
        dict(id='Z4_FACH_F', side='F', x=(-h2, h2), z=(Z['COL1'] + 0.2, Z['BULK0'] - 0.5), hmax=4.1,
             rule='Zellfach: nur Keystone 3034 (gedreht, geschlossenes Ende -x, Ein-/Ausschub +x; Clipkoerper x -4.4...11.7 '
                  'nach Datenblatt B 7.4/L 16.1; Zelle x -7.0...13.0) und Minuspad 4 x 4; Testpads nur TP1 (TX), TP2 (RX) im '
                  'Streifen x -12.7...-7.5, z 12...30 (TP3 entfaellt, Auflage A-1; Adapter-GND ueber das Minuspad). Genau 4 '
                  'Via-in-Pad, gefuellt und ueberkupfert (POFV): VBAT-Clip-Pad, Minuspad, TP1, TP2; sonst keine Vias. Unter '
                  'der Zelle nur Loetstopplack ausser Minuspad (R2-W01 Nr. 2). Leitungen nur Innenlagen, >= 1.0 zur Kante '
                  '(K-3). 2 x 100 kOhm im Elektronikraum (R2-A3). Schulter z 7.7...11.5 (45 Grad, Innenecke R 2) ohne Kupfer aussen.'),
        dict(id='Z4_FACH_B', side='B', x=(-h2, h2), z=(Z['COL1'] + 0.2, Z['BULK0'] - 0.5), hmax=0.0,
             rule='Silkscreen Warnsymbol Dreieck >= 7 x 9 mm + "CR2032 Verschluckgefahr" (S3-W4, zweiter Ort). '
                  'Keine Testpads (Fach wird geflutet, REQ-SAF-05).'),
        dict(id='Z5B_KRAGEN_BAUTEILE', side='FB', x=(-w2p, w2p), z=(Z['SEAL1'], Z['COL1'] + 0.2), hmax=0.0,
             rule='Im Kragen-Verguss (Z5B freigegeben unter K-1...K-7). F: nur U3 TMP1075N + C24 im Feld x -9.0...-4.6, '
                  'z 4.4...6.8 (K-2), Hoehe <= 0.7 (Tasche 1.2 tief, >= 0.5 mm Epoxid darueber); Vias nur in diesem Feld, '
                  'tented oder gefuellt, >= 1.0 mm zur Platinenkante (K-2). Sonst keine Bauteile, keine Vias, kein '
                  'Aussenkupfer. Ausnahme Rev C: Clip-Pads XBT1 ab z 7.50. B: frei. Abstand zur Mutter |x| >= 2.6.'),
        dict(id='Z5A_KRAGEN_DICHTSTREIFEN', side='FB', x=(-w2p, w2p), z=(Z['COL0'] - 0.5, Z['SEAL1']), hmax=0.0,
             rule='Sondendichtung (S3-K2, REQ-MECH-08/15), Vergusskante z 2.0: keine Bauteile, keine Vias, kein Kupfer '
                  'auf Aussenlagen, Loetstopp geschlossen. Innenlagen nur GND/Guard und die Sondennetze (K-1); SENS_PWR, '
                  'SDA, SCL enden ueber z 4.4.'),
        dict(id='Z6_FREI', side='FB', x=(-w2p, w2p), z=(-HEAD['GAP_SOIL'], Z['COL0'] - 0.5), hmax=0.0,
             rule='Zwischen Erde und Kragen: keine Elektroden (Luftanteil), Guard auf L2/L3 erlaubt (Feld Kap. 8), '
                  'keine Vias (Feld: z 0...2 und nasser Bereich). Silkscreen Logo (F) und "max"/Revision (B).'),
        dict(id='Z7_SONDE', side='FB', x=(-w2p, w2p), z=(PCB['Z_TIP'], -HEAD['GAP_SOIL']), hmax=0.0,
             rule='Sonde: Elektroden nur Innenlagen L2/L3, Aussenlagen ohne Kupfer (REQ-MECH-04), Kupfer >= 1.25 mm zur '
                  'Kontur inkl. Spitze (Feld Kap. 8; REQ-MECH-06 >= 1.0), keine Vias (REQ-MECH-05). Spitze 45 Grad.'),
    ]


def outline():
    """Platinenkontur (Kopfkoordinaten x, z), geschlossen, im Gegenuhrzeigersinn von vorne."""
    w2, h2, f2 = PCB['W'] / 2, PCB['W_HEAD'] / 2, PCB['TIP_FLAT'] / 2
    # Innenecke Schulter (x = w2, z = Z_SH0) mit Radius R_SH, als Polygon (8 Segmente) - Kerbwirkung bei Biegung
    r, n = PCB['R_SH'], 8
    t = r * math.tan(math.radians(22.5))
    cx, cz = w2 + r, PCB['Z_SH0'] - t                 # Kreismittelpunkt rechts der Kante
    arc = [(cx - r * math.cos(math.radians(45.0 * i / n)), cz + r * math.sin(math.radians(45.0 * i / n)))
           for i in range(n + 1)]                     # von (w2, Z_SH0 - t) bis Tangentenpunkt auf der 45-Grad-Linie
    right = [(round(x, 4), round(z, 4)) for x, z in arc]
    left = [(-x, z) for x, z in reversed(right)]
    return ([(-f2, PCB['Z_TIP']), (f2, PCB['Z_TIP']), (w2, PCB['Z_CHAMF'])] + right +
            [(h2, PCB['Z_SH1']), (h2, PCB['Z_TOP']), (-h2, PCB['Z_TOP']), (-h2, PCB['Z_SH1'])] + left +
            [(-w2, PCB['Z_CHAMF'])])


def to_kicad(x, z):
    return (round(x, 4), round(PCB['Z_TOP'] - z, 4))


def field_z(z):
    """Feldsimulation (simulation/field/REPORT.md): z_f = 0 an der Kopfunterkante (dort ANNAHME 'Unterkante Kragen'),
    positiv nach unten zur Spitze. Stecktiefe z_f = 5 <-> Kopf z = -5."""
    return -z


def oring_fit():
    g = GROOVE_BOT
    per = 2 * (2 * g['X'] + (g['Y1'] - g['Y0'])) - 8 * g['R'] + 2 * math.pi * g['R']
    idfit = per / math.pi
    return per, idfit, ORING['ID'], (idfit / ORING['ID'] - 1) * 100


def interface_dict(area=None):
    zl = zones()
    ol = outline()
    d = dict(
        title='fluidi Sensor P3 - Schnittstelle PCB-Kontur <-> Gehaeuse',
        revision=REV, date=REV_DATE,
        revision_note='Rev C ersetzt Rev B, Kontur unveraendert: Clip 3034 nach Datenblatt x -4.4...11.7 (Rev B -7...9.1 falsch), '
                      'Clip-Pad-Spanne 23.1 (z 7.50...30.60), Antenne Footprint _Right an Layout-Lage, Feld Z5B x -9.0...-4.6 '
                      '(K-2), Z5A Innenlagen nur GND/Guard + Sonde (K-1), K-3, TP3 entfaellt und 4 VIP im Fach (A-1), '
                      'Platinenanschlag in der Kappe (Lage z), STEP-Koordinatenbezug. Rev B: Kopf V4 (D-019).',
        status='verbindlich fuer Layout Rev C (Aenderung nur ueber neue Revision). Offen: LS-W1 (Pad - Verguss >= 0.3 inkl. '
               'Toleranz) braucht Fachverlaengerung, Entscheid Projektleitung (docs/reviews/phase4_kollision_mechanik.md)',
        generator='mechanical/gen/fluidi_params.py', doc='docs/interfaces/PCB_OUTLINE.md',
        units='mm',
        coordinate_systems=dict(
            head='x Breite (+ rechts von vorne), y Tiefe (0 = Front, + hinten), z Hoehe (0 = Kopfunterkante)',
            kicad='X = x, Y = %.1f - z (Ursprung Mitte Oberkante, Y nach unten), Top-View = Ansicht von vorne, '
                  'F.Cu = bestueckte Seite zeigt zum Fenster (-y)' % PCB['Z_TOP'],
            kicad_page='Hilfsursprung (aux_axis_origin) = Mitte Oberkante, in fluidi_sensor.kicad_pcb bei Seite (150, 30): '
                       'x = X_p - 150, z = %.1f - (Y_p - 30)' % PCB['Z_TOP'],
            kicad_step='kicad-cli pcb export step ohne Ursprungsoption: X_s = X_p, Y_s = -Y_p, Z_s = Hoehe ueber B. '
                       'Kopf: x = X_s - 150, y = %.1f - Z_s, z = %.1f + Y_s (Drehung +90 Grad um x, Verschiebung '
                       '(-150, %.1f, %.1f)); fluidi_pcb_collision.py' % (PCB['Y_B'], PCB['Z_TOP'] + 30, PCB['Y_B'], PCB['Z_TOP'] + 30),
            field='simulation/field/REPORT.md: z_f = -z (0 an der Kopfunterkante, + zur Spitze); Vergusskante liegt bei '
                  'z = 2.0 (z_f = -2.0), d. h. 2 mm hoeher als dort angenommen (konservativ fuer Luftanteil)'),
        head=dict(W=HEAD['W'], D=HEAD['D'], H=HEAD['H'], z_fuge=HEAD['Z_FUGE'], cap_h=HEAD['H'] - HEAD['Z_FUGE'],
                  sleeve_top=Z['SLEEVE_TOP']),
        board=dict(thickness=PCB['T'], layers=4, width_probe=PCB['W'], width_head=PCB['W_HEAD'], length=PCB['LENGTH'],
                   z_top=PCB['Z_TOP'], z_tip=PCB['Z_TIP'], tip='45 Grad, flach %.1f mm' % PCB['TIP_FLAT'],
                   shoulder='45 Grad bis z %.1f (26 mm), Innenecke R %.1f (Tangente ab z %.2f, 8 Segmente)' % (
                       PCB['Z_SH1'], PCB['R_SH'], PCB['Z_SH0'] - PCB['R_SH'] * math.tan(math.radians(22.5))),
                   y_front_F=PCB['Y_F'], y_back_B=PCB['Y_B'], assembly='einseitig F (JLC Economic)',
                   z_position_tol=PCB['TOL_Z'],
                   probe_max_incl_coating=dict(thickness=PCB['T_COAT_MAX'], width=PCB['W_COAT_MAX']),
                   outline_head_xz=ol, outline_kicad_XY=[to_kicad(x, z) for x, z in ol]),
        markings=dict(
            max_insertion=dict(z=-HEAD['GAP_SOIL'], kicad_Y=to_kicad(0, -HEAD['GAP_SOIL'])[1], sides='F+B',
                               silkscreen='Linie 0.2 mm, x -9...9, Text "max" + Pfeil'),
            logo_silkscreen=dict(side='F', x=(-9.0, 3.0), z=(-4.4, -0.8), file='docs/design/logo/fluidi_logo_v3a_mono.svg',
                                 width=10.0, note='Strich 0.52 mm >= 0.2 (P3_FLUIDI.md Kap. 5)'),
            revision_silkscreen=dict(side='B', x=(-9.0, 9.0), z=(-4.4, -0.8), text='fluidi rev B'),
            warning_silkscreen=dict(side='B', x=(-8.0, 8.0), z=(11.0, 28.0), text='Dreieck ! + CR2032 + Verschluckgefahr')),
        zones=[dict(z_d, kicad_Y=(to_kicad(0, z_d['z'][1])[1], to_kicad(0, z_d['z'][0])[1])) for z_d in zl],
        components=dict(
            D1_LED=dict(part='TUOZHAN P4-1615G2B2R4TS2-06T-001-24 (C7496855)', side='F', center_xz=(LED['X'], LED['Z']),
                        kicad_XY=to_kicad(LED['X'], LED['Z']), height=LED['H'], tol=0.3,
                        window_inner_face_y=DROP['BOSS_Y1'], d_led_to_window=round(PCB['Y_F'] - LED['H'] - DROP['BOSS_Y1'], 2),
                        note='Leuchtflaeche zum Fenster (-y), Mitte 0.4 mm ueber der Sichtfuge z %.1f. Lichtschaft Ø3.0 des '
                             'Fensters endet 2.0 mm vor der LED. Kein Bauteil > 0.6 mm im Kreis r 1.8 um D1.' % HEAD['Z_FUGE']),
            SW1_TASTER=dict(part=SW['PART'], side='F', center_xz=(SW['X'], SW['Z']),
                            kicad_XY=to_kicad(SW['X'], SW['Z']), height=SW['H'], tol=0.2,
                            body_xz=(SW['BODY_X'], SW['BODY_Z']),
                            pads='2 x (%.2f in x x %.1f in z), Mittenabstand %.2f in x, aussen %.2f; Footprint '
                                 'Button_Switch_SMD:SW_SPST_TS-1088-xR020 unrotiert' % (SW['PAD_W'], SW['PAD_L'], SW['PAD_CC'], SW['PAD_OUT']),
                            actuator='Ø%.1f, Hub %.1f, %.2f N (XUNPU_TS-1088-AR02016_Datasheet_LCSC-2022-06.pdf S.1)' % (
                                SW['ACT_D'], SW['TRAVEL'], SW['FORCE_N']),
                            actuation='Taste oben -> Silikonmembran -> Stoessel -> 30-Grad-Keil -> Biegezunge der Kappe '
                                      '(Hebel 2.5) -> senkrecht (+y) auf den Betaetiger'),
            XBT1_CLIP=dict(part='Keystone 3034TR (C5213768)', side='F', rotation='90 Grad: Einschub in x, geschlossenes Ende -x, offenes Ende +x',
                           cell_center_xz=(CELL['XC'], Z['CELL_C']), kicad_XY=to_kicad(CELL['XC'], Z['CELL_C']),
                           clip_x=(CLIP['X0'], CLIP['X1']), clip_z=(Z['CLIP0'], Z['CLIP1']), height=CLIP['H'],
                           cell_x=(CELL['XC'] - CELL['D'] / 2, CELL['XC'] + CELL['D'] / 2),
                           pads_plus=dict(span_z=CLIP['W'], z=(Z['CELL_C'] - CLIP['W'] / 2, Z['CELL_C'] + CLIP['W'] / 2),
                                          kicad_Y=(to_kicad(0, Z['CELL_C'] + CLIP['W'] / 2)[1], to_kicad(0, Z['CELL_C'] - CLIP['W'] / 2)[1]),
                                          size_xz=(5.08, CLIP['PAD_D']), x=(round(CELL['XC'] - 2.54, 3), round(CELL['XC'] + 2.54, 3)),
                                          kicad_pad_centers_Y=(round(to_kicad(0, Z['CELL_C'])[1] - (CLIP['W'] - CLIP['PAD_D']) / 2, 3),
                                                               round(to_kicad(0, Z['CELL_C'])[1] + (CLIP['W'] - CLIP['PAD_D']) / 2, 3)),
                                          note='Katalogminimum W 23.1 (Keystone_3034_Catalog_M65.pdf S.1 Fig. 1 Pad Layout); '
                                               'KiCad-Bibliothek 23.24 -> je Seite 0.07 kuerzen (LS-W1 a)'),
                           pad_minus='4 x 4 in der Zellmitte, Via-in-Pad gefuellt',
                           note='B 7.4 ab Zellmitte bis Quersteg (geschlossenes Ende -x, Anschlaglappen x -4.8...-1.6 laut '
                                'KiCad-3D-Modell). Zelle Ø20 buendig mit der rechten Platinenkante x = 13; Ein-/Ausschub +x, '
                                'der Weg fuehrt nicht ueber TP1/TP2 (x <= -7.5). In der Huelse 2.4 mm bis zur Wand (Clip haelt).'),
            PCB_STOP=dict(x=(PSTOP['X0'], PSTOP['X1']), z_stop=PCB['Z_TOP'], fork_depth=PSTOP['FORK'],
                          fork_y=(round(PCB['Y_F'] - PSTOP['CLR_F'], 2), round(PCB['Y_B'] + PSTOP['CLR_B'], 2)),
                          note='Kappe: Anschlag fuer die Platinenoberkante (Lage in z beim Schott-Verguss kopfueber) und '
                               'Gabel (y). Platine dort ohne Bauteile (Z1), Kupfer erlaubt ausserhalb des Antennen-Keepouts.'),
            U3_TMP_KRAGEN=dict(part=TMP['PART'], side='F', x=(TMP['X0'], TMP['X1']), z=(TMP['Z0'], TMP['Z1']),
                               height_max=TMP['H'], kicad_Y=(to_kicad(0, TMP['Z1'])[1], to_kicad(0, TMP['Z0'])[1]),
                               field_K2=dict(x=(-9.0, -4.6), z=(4.4, 6.8), kicad_Y=(46.7, 49.1),
                                             vias='tented oder gefuellt, >= 1.0 mm zur Kante'),
                               pocket=dict(x=(KPOCKET['X0'], KPOCKET['X1']), y=(round(PCB['Y_F'] - KPOCKET['DEPTH'], 2), PCB['Y_F']),
                                           z=(KPOCKET['Z0'], KPOCKET['Z1']), note='unten offen (Verguss kopfueber, entlueftet)'),
                               note='Option (f), FLOORPLAN_OPTIONS.md Kap. 2f; Feld K-2; freigegeben unter K-1...K-7'),
            TESTPAD_STRIP_FACH=dict(side='F', x=(TPSTRIP['X0'], TPSTRIP['X1']), z=(TPSTRIP['Z0'], TPSTRIP['Z1']),
                                    note='nur TP1 (TX), TP2 (RX) als Pads mit Via-in-Pad (gefuellt); TP3 entfaellt (A-1)'),
            ANTENNA=dict(part='AN043 IFA', footprint=ANT['FP'], zone='Z1_ANTENNE', z=(Z['ANT0'], Z['ANT1']),
                         copper_x=(ANT['X0'], ANT['X1']), copper_z=(ANT['Z0'], ANT['Z1']), feed_x=ANT['FEED_X'],
                         keepout_x=(-2.7, 12.5)),
            SCREW_NUT=dict(screw='ISO 7045 M2x4 A2 PH1 (unverlierbar, Gewindefurch-Lippe Ø1.7 im Huelsenboden)',
                           nut='ISO 4032 M2 A2 SW4 x 1.6, im Kragen eingegossen',
                           axis_xy=(SCREW['X'], SCREW['Y']), nut_z=(Z['COL_NUT0'], Z['COL_NUT1']),
                           dist_to_pcb_F=round(PCB['Y_F'] - (SCREW['Y'] + SCREW['NUT_S'] / 2), 2),
                           dist_to_antenna_z=round(Z['ANT0'] - Z['COL_NUT1'], 1))),
        seals=dict(
            oring=dict(type=ORING['DASH'], material='Silikon oder EPDM ohne Russ (rot/transluzent), Silikonfett',
                       qty=2, places=dict(spigot_z=(Z['SP_G0'], Z['SP_G1']), collar_z=(Z['COL_G0'], Z['COL_G1'])),
                       gland=ORING['GLAND'], squeeze_nom=round((ORING['CS'] - ORING['GLAND']) / ORING['CS'], 3),
                       stretch_pct=round(oring_fit()[3], 2)),
            potting=dict(schott_z=(Z['BULK0'], Z['BULK1']), kragen_z=(Z['COL0'], Z['COL1']),
                         material='Epoxid 2K mineralisch gefuellt, Tg >= 80 C (FLOORPLAN_OPTIONS 2f; Typ ANNAHME, offen)'),
            window_glue_to_oring_groove=round(DROP['ZC'] - DROP['R'] - Z['SP_G1'], 2),
            visible_joint='Sichtfuge z %.1f ist NICHT dicht (Huelse dort Sichtschale). Ablauf: Spalt 0.7 mm, Stufe z %.1f '
                          '(vorn) -> %.1f (hinten), 4 Schlitze %.0f x %.1f in der Huelsenrueckwand.' % (
                              HEAD['Z_FUGE'], Z['STEP_FRONT'], Z['STEP_BACK'], DRAIN['W'], DRAIN['H'])),
        height_limits_summary=dict(F_band=2.0, F_kragen_feld=TMP['H'], F_fach='nur 3034 (4.1)', B='0 (unbestueckt, Pads erlaubt im Band)'),
        open_points=['Projektleitung: LS-W1 - Abstand Clip-Pad zu den Vergusskanten >= 0.3 inkl. Toleranz verlangt eine '
                     'Fachverlaengerung um 0.7 mm (Vorschlag V-K: Huelsenboden 2.0 -> 1.3, Kragen und Kragenfeld 0.7 tiefer, Zelle 0.35 tiefer); '
                     'ohne Entscheid gilt Rev C mit 0.20 nominal',
                     'Elektronik: Kunststoff vor der Antenne (Stoessel, Kappe, Anschlag) bestaetigen; S11/RSSI im Gehaeuse '
                     '(PROTOTYP-PRUEFUNG)',
                     'Elektronik: Blockplan Kap. 4 ist ein Machbarkeitsnachweis (Faktor 1.5 ANNAHME), Layout darf umordnen, '
                     'D1/SW1/Zonen nicht',
                     'Mechanik: Verguss Kragen mit Tasche (Volumen, Entlueftung) am Muster pruefen (PROTOTYP-PRUEFUNG)'])
    if area:
        d['area_balance'] = area
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


def rect_k(x0, x1, z0, z1):
    return [to_kicad(x0, z0), to_kicad(x1, z0), to_kicad(x1, z1), to_kicad(x0, z1)]


def main(area=None, plan_polys=()):
    od = os.path.join(REPO, 'mechanical', 'interfaces')
    os.makedirs(od, exist_ok=True)
    d = interface_dict(area)
    with open(os.path.join(od, 'pcb_outline.json'), 'w') as f:
        json.dump(d, f, indent=1, ensure_ascii=False)
    polys = [('Edge.Cuts', [to_kicad(x, z) for x, z in outline()], True)]
    for zd in zones():
        x0, x1 = zd['x']; z0, z1 = zd['z']
        polys.append(('Zone_' + zd['id'], rect_k(x0, x1, z0, z1), True))
    polys.append(('Comp_D1', rect_k(LED['X'] - LED['LX'] / 2, LED['X'] + LED['LX'] / 2, LED['Z'] - LED['LZ'] / 2,
                                    LED['Z'] + LED['LZ'] / 2), True))
    polys.append(('Comp_SW1_body', rect_k(SW['X'] - SW['BODY_X'] / 2, SW['X'] + SW['BODY_X'] / 2,
                                          SW['Z'] - SW['BODY_Z'] / 2, SW['Z'] + SW['BODY_Z'] / 2), True))
    for s in (-1, 1):
        cx = SW['X'] + s * SW['PAD_CC'] / 2
        polys.append(('Comp_SW1_pads', rect_k(cx - SW['PAD_W'] / 2, cx + SW['PAD_W'] / 2, SW['Z'] - SW['PAD_L'] / 2,
                                              SW['Z'] + SW['PAD_L'] / 2), True))
    polys.append(('Comp_XBT1_clip', rect_k(CLIP['X0'], CLIP['X1'], Z['CLIP0'], Z['CLIP1']), True))
    n = 48
    polys.append(('Comp_Cell', [to_kicad(CELL['XC'] + 10 * math.cos(2 * math.pi * i / n),
                                         Z['CELL_C'] + 10 * math.sin(2 * math.pi * i / n)) for i in range(n)], True))
    polys.append(('Comp_U3_Kragen', rect_k(TMP['X0'], TMP['X1'], TMP['Z0'], TMP['Z1']), True))
    for zp in (Z['CELL_C'] - CLIP['W'] / 2, Z['CELL_C'] + CLIP['W'] / 2 - CLIP['PAD_D']):   # Rev C: Clip-Pads, Spanne W 23.1
        polys.append(('Comp_XBT1_pads', rect_k(CELL['XC'] - 2.54, CELL['XC'] + 2.54, zp, zp + CLIP['PAD_D']), True))
    polys.append(('Mech_Anschlag_Platine', rect_k(PSTOP['X0'], PSTOP['X1'], PCB['Z_TOP'] - PSTOP['FORK'], PCB['Z_TOP']), True))
    polys.append(('Zone_Z5B_Feld_K2', rect_k(-9.0, -4.6, 4.4, 6.8), True))
    polys.append(('Mech_Kragentasche', rect_k(KPOCKET['X0'], KPOCKET['X1'], KPOCKET['Z0'], KPOCKET['Z1']), True))
    polys.append(('Pads_Fachstreifen', rect_k(TPSTRIP['X0'], TPSTRIP['X1'], TPSTRIP['Z0'], TPSTRIP['Z1']), True))
    polys.append(('Mech_Lichtschaft', [to_kicad(DROP['X'] + 1.5 * math.cos(2 * math.pi * i / 24),
                                                DROP['ZC'] + 1.5 * math.sin(2 * math.pi * i / 24)) for i in range(24)], True))
    T = TONGUE
    polys.append(('Mech_Zunge', rect_k(T['X0'], T['X1'], T['Z_TIP'], BTN['BLOCK_Z0']), True))
    polys.append(('Mech_Sichtfuge', [to_kicad(-PCB['W_HEAD'] / 2, HEAD['Z_FUGE']), to_kicad(PCB['W_HEAD'] / 2, HEAD['Z_FUGE'])], False))
    polys.append(('Mark_max', [to_kicad(-9, -HEAD['GAP_SOIL']), to_kicad(9, -HEAD['GAP_SOIL'])], False))
    polys += list(plan_polys)
    write_dxf(os.path.join(od, 'pcb_outline.dxf'), polys)
    print('geschrieben:', os.path.join(od, 'pcb_outline.json'), os.path.join(od, 'pcb_outline.dxf'))
    print('LED-Fenster-Abstand d = %.2f mm' % d['components']['D1_LED']['d_led_to_window'])
    print('O-Ring Nutgrund-Umfang %.2f mm -> Passung ID %.2f, %s ID %.2f, Dehnung %.1f %%' % (
        oring_fit()[0], oring_fit()[1], ORING['DASH'], ORING['ID'], oring_fit()[3]))
    return d


if __name__ == '__main__':
    main()
