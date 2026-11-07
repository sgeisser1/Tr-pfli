# Schnittstelle PCB-Kontur ↔ Gehäuse – fluidi Sensor P3

| | |
|---|---|
| Revision | **C** (2026-11-08), ersetzt Rev B; **Kontur unverändert** (siehe Kap. 11 Revisionsvermerk) |
| Status | **verbindlich für das Layout Rev C**. Z5B freigegeben unter K-1…K-7 (`docs/reviews/phase4_sicherheit_kragen_firmware.md`). **Offen:** LS-W1 (Clip-Pad ≥ 0.3 mm zu den Vergusskanten inkl. Toleranz) verlangt eine Fachverlängerung um 0.7 mm – Entscheid Projektleitung, Vorschlag Kap. 9. Änderungen nur über eine neue Revision (Mechanik + Elektronik) |
| Maschinenlesbar | `mechanical/interfaces/pcb_outline.json`, `mechanical/interfaces/pcb_outline.dxf` (Edge.Cuts, Zonen, feste Bauteile, Mechanik-Referenzen und Blockplan `Plan_*` als Layer, KiCad-Koordinaten) |
| Blockplan | `mechanical/interfaces/pcb_rev_b_floorplan.png` (massstäblich, Ansicht von vorne = KiCad-Top) |
| Erzeugt von | `.venv/bin/python mechanical/gen/pcb_rev_b_floorplan.py` (ruft `fluidi_params.main()`; `fluidi_params.py` ist die einzige Quelle aller Masse, auch für CAD und FEM) |
| Geprüft mit | `freecadcmd mechanical/gen/fluidi_sensor.py` → `mechanical/sensor/check_sensor.txt`, `collision_placeholder.txt`; mit dem KiCad-STEP: `freecadcmd mechanical/gen/fluidi_pcb_collision.py` → `mechanical/sensor/collision_pcb_step.txt`, Baugruppe `fluidi_sensor_mit_pcb.step` |
| Grundlage | D-019 (Kopf V4 34 × 13 × 57.5, Kappe 14 mm, Fuge z 43.5, Platine im Kopf ≈ 26 mm), D-018 (Messkette D3), `hardware/sensor/out/FLOORPLAN_OPTIONS.md` Option (f), `docs/design/PROPORTIONEN.md`, `docs/reviews/phase3_sleeve_sicherheit.md` (S3-K1/K2, W1–W4), `simulation/field/REPORT.md` Kap. 8 |

## 1 Koordinaten

- **Kopf:** x = Breite (0 = Mitte, + rechts, von vorne gesehen), y = Tiefe (0 = Frontfläche, + nach hinten), z = Höhe (0 = Kopfunterkante).
- **KiCad:** `X = x`, `Y = 53.5 − z` (Ursprung Mitte Platinenoberkante, Y nach unten zur Spitze). Top-View = Ansicht von vorne.
  In `fluidi_sensor.kicad_pcb` liegt dieser Ursprung als Hilfsursprung (`aux_axis_origin`) bei Seite (150, 30):
  `x = X_Seite − 150`, `z = 53.5 − (Y_Seite − 30)`. Gerber/Bohrdaten nutzen den Hilfsursprung.
- **KiCad-STEP** (`kicad-cli pcb export step` ohne Ursprungsoption, `hardware/sensor/out/fluidi_sensor.step`):
  `X_s = X_Seite`, `Y_s = −Y_Seite`, `Z_s` = Höhe über der B-Seite (Bauteile auf F bei `Z_s = 1.6`). In Kopfkoordinaten:
  `x = X_s − 150`, `y = 8.2 − Z_s`, `z = 83.5 + Y_s` (= Drehung +90° um x, dann Verschiebung (−150, 8.2, 83.5)).
  Nachgeprüft (`collision_pcb_step.txt` Kap. A): STEP-Platine x ±13.000, z −105.000…53.500, Bauteile auf y 6.60,
  Kontur STEP ↔ `fluidi_params.outline()` 0.08 mm² Abweichung (Bogen R 2 als Polygon). Der STEP-Platinenkörper ist
  1.52 mm dick (KiCad zählt nur die Dielektrika), die Bauteile sitzen richtig bei 1.6.
- **F-Seite (F.Cu, bestückt) zeigt nach vorne zum Fenster (−y)**, Oberfläche bei **y = 6.6** (Rev A 7.4). B-Seite y = 8.2, **unbestückt** (JLC Economic einseitig).
- **Feldsimulation** (`simulation/field/REPORT.md` Kap. 8): z_f = −z (z_f = 0 an der Kopfunterkante, positiv zur Spitze).
  Beispiel: S-Elektrode z_f 10…86 → z −10…−86 → KiCad Y 63.5…139.5. Die dortige ANNAHME „z = 0 = Unterkante Kragen“
  ist 2 mm zu tief: die Vergusskante liegt bei z = 2.0 (z_f = −2). Die Elektrodenlage bezieht sich auf die Erde
  (Stecktiefe z_f = 5 ↔ z = −5) und bleibt gültig.

## 2 Platine

| Mass | Wert |
|---|---|
| Dicke, Lagen | 1.6 mm, 4 Lagen (REQ-MECH-04/11) |
| Breite | **Kopf 26.0 mm** (z ≥ 11.5), **Sonde und Kragen 20.0 mm** (z ≤ 7.67), Schulter 45° dazwischen |
| Länge | **158.5 mm**: Oberkante z = 53.5 (KiCad Y 0), Spitze z = −105.0 (Y 158.5) |
| Spitze | 45° beidseitig, Spitzenfläche 5.0 mm; Fasenbeginn z = −97.5 (Y 151.0) |
| Kontur (KiCad X/Y) | (−2.5/158.5) (2.5/158.5) (10/151) (10/45.83) ⌒ R 2.0 ⌒ (10.59/44.41) (13/42) (13/0) (−13/0) (−13/42) (−10.59/44.41) ⌒ R 2.0 ⌒ (−10/45.83) (−10/151); Bogen in DXF/JSON als 8 Segmente – in KiCad als Bogen R 2.0 zeichnen |
| Innenecken Schulter | **R 2.0** (Tangente ab z 7.67, 0.37 mm über dem Kragen). Grund: FEM LC1b (ohne Kragenstütze): scharfe Ecke 284 MPa, mit R 2.0 191 MPa (`simulation/fem/REPORT.md` Kap. 4) |
| Sonde inkl. Beschichtung | max. 20.4 × 2.0 mm (Bodenschlitz der Hülse 20.8 × 2.4) – **ANNAHME** Schichtdicke (REQ-MECH-07) |
| Lage im Kern | **z: Platinenoberkante liegt am Anschlag der Kappe** (z 53.5, x −8.0…−3.0, Kap. 6), Toleranz Pad ↔ Vergusskante ± 0.22 (RSS: JLC-Kontur ± 0.2, FDM ± 0.1). Rev B hatte keinen Anschlag (0.7 mm Luft zum Tastenblock → Lage 0…+0.7). Kragen mit Distanzlehre 23.5 am Schott (Kap. 7). y: Gabel am Anschlag (F 0.05, B 0.15 Luft), Schottkeil |
| Max. Stecktiefe | Silkscreen-Linie bei **z = −5.0 (Y 58.5)** auf F und B, x −9…9, Text „max“ + Pfeil (REQ-MECH-01) |

**Herleitung 26 mm (aus V4 34 mm aussen):** Hülsenwand 1.6 + O-Ring-Einbauraum 1.35 + Zapfenwand hinter der Nut 0.8
+ Spiel 0.25 je Seite → 34 − 2 × 4.0 = 26.0 mm. Der Schottschlitz (x ± 13.2) und der Zapfen-Innenraum (x ± 13.2)
lassen die Platine von unten einschieben (0.2 mm Spiel).

**Warum 0.8 mm nach vorne (y_F 6.6):** Mit 26 mm Breite liegt die hintere Platinenkante in den Ecken der O-Ring-Nut.
Bei y_F 7.4 bliebe dort keine Zapfenwand. Mit y_F 6.6 bleibt hinter dem Nutgrund ≥ 0.54 mm Wand (CAD-Prüfung 9,
Rev A ≈ 0.5). Folgen im CAD nachgeführt: Lichtschaft (d bleibt 2.0), Mutter M2 auf y 4.2, Zunge, Stössel, Schottschlitz.

## 3 Zonen (KiCad-Y in Klammern)

| Zone | z (Y) | x | Seite | Max. Höhe | Regel |
|---|---|---|---|---|---|
| Z1 Antenne | 47.8 … 53.5 (0 … 5.7) | ±13 | F+B | 0 | AN043-IFA 15.2 × 5.7, Footprint **`RF_Antenna:Texas_SWRA117D_2.4GHz_Right`** (Einspeisung/Kurzschluss links, offenes Ende rechts; Rev B nannte fälschlich „…_Left“, L-5). Lage Layout Rev B: Speisepunkt X 0.35, Kupfer **x −2.2…12.2, z 47.8…53.2**, Keepout alle Lagen x −2.7…12.5. Ganze Zone ohne Bauteile, neben und über der Antenne kein Kupfer (AN043). Kein Metall des Gehäuses. **Platinenanschlag der Kappe x −8.0…−3.0** (Kunststoff, Kap. 6): dort Kupfer erlaubt (ausserhalb Keepout), keine Bauteile |
| Z2 Band F | 32.7 … 47.8 (5.7 … 20.8) | ±13 | F | **2.0** | Elektronikband 26 × 15.1 = **392.6 mm²**. Höhe ≤ 2.0 überall (Einschieben durch das Schott; Zunge 0.2 vor SW1). Courtyards ≥ 0.3 zur Kontur. D1/SW1 fest (Kap. 5). Im Kreis r 1.8 um D1 nur Teile ≤ 0.6 (Lichtschaft) |
| Z2 Band B | 30.3 … 47.8 (5.7 … 23.2) | ±13 | B | 0 | unbestückt; **Kupfer und Testpads erlaubt** (TP4 OSZ_OUT, TP5 PROBE_SENSE, GND). Pogo-Zugang nur vor dem Einschieben. Hinter B 0.2 mm Spiel (Zapfen) |
| Z3 Schott | 30.3 … 32.7 (20.8 … 23.2) | ±13 | F+B | 0 | Schott-Verguss z 30.8 … 32.0: keine Bauteile, **keine Vias, kein Kupfer auf Aussenlagen**, Lötstopp geschlossen. Signale nur Innenlagen, ≥ 1.0 mm zur Kante (S3-K1, M-03, K-3). **Ausnahme Rev C:** oberes Clip-Pad XBT1 bis z 30.60 (Y 22.90), Kap. 5 – Abstand zum Verguss nominal 0.20 (LS-W1 offen, Kap. 9) |
| Z4 Fach F | 7.5 … 30.3 (23.2 … 46.0) | ±13 (Schulter) | F | 4.1 | **Nur** Keystone 3034 (Clipkörper **x −4.4 … 11.7** nach Datenblatt, Zelle x −7.0 … 13.0) und Minuspad 4 × 4. **Testpads nur TP1 (TX) und TP2 (RX)** im Streifen x −12.7 … −7.5, z 12 … 30 (nur Pads, ausserhalb des Ein-/Ausschubwegs +x). **TP3 entfällt** (Auflage A-1, Adapter-GND über das Minuspad). **Genau 4 Via-in-Pad, gefüllt und überkupfert (POFV):** VBAT-Clip-Pad, Minuspad, TP1, TP2; sonst keine Vias (S2-W03, L-1/A-1). Unter der Zelle nur Lötstopp ausser Minuspad (R2-W01). Leitungen zu Kragen und Sonde nur Innenlagen, ≥ 1.0 mm zur Kante (K-3). Schulter z 7.67 … 11.5 ohne Aussenkupfer |
| Z4 Fach B | 7.5 … 30.3 | ±13 | B | 0 | Silkscreen Warnsymbol ≥ 7 × 9 mm + „CR2032 Verschluckgefahr“ (S3-W4, x −8…8, z 11…28). Keine Testpads (Fach wird geflutet, REQ-SAF-05) |
| Z5B Kragen Bauteile | 4.2 … 7.5 (46.0 … 49.3) | ±10 | F | **0.7 im Feld**, sonst 0 | Im Kragen-Verguss, freigegeben unter K-1…K-7. **Nur U3 TMP1075N + C24 im Feld x −9.0 … −4.6, z 4.4 … 6.8** (Y 46.7 … 49.1; K-2, Rev B −9.4; Tasche 1.2 tief, ≥ 0.5 mm Epoxid darüber). Vias nur in diesem Feld, **tented oder gefüllt, ≥ 1.0 mm zur Platinenkante** (K-2). Sonst keine Bauteile, keine Vias, kein Aussenkupfer. Innenlagen ≥ 1.0 mm zur Kante (LS-K1). |x| ≥ 2.6 (Mutter). **Ausnahme Rev C:** unteres Clip-Pad XBT1 ab z 7.50 (Y 46.00) – das ist die Zonengrenze, also kein Eingriff (Rev-B-Footprint: 7.43) |
| Z5A Kragen Dichtstreifen | 1.5 … 4.2 (49.3 … 52.0) | ±10 | F+B | 0 | **Sondendichtung** (S3-K2, REQ-MECH-08/15), Vergusskante z 2.0: keine Bauteile, keine Vias, kein Aussenkupfer, Lötstopp geschlossen. **Innenlagen nur GND/Guard und die Sondennetze** (K-1); SENS_PWR, SDA, SCL enden über z 4.4 |
| Z6 frei | −5.0 … 1.5 (52.0 … 58.5) | ±10 | F+B | 0 | zwischen Erde und Kragen: **keine Elektroden**; Guard L2/L3 erlaubt (Feld Kap. 8), keine Vias. F: Logo, B: „max“ + „fluidi rev B“ |
| Z7 Sonde | −105 … −5 (58.5 … 158.5) | ±10 | F+B | 0 | Elektroden nur L2/L3 (REQ-MECH-04), Aussenlagen ohne Kupfer, **Kupfer ≥ 1.25 mm zur Kontur inkl. Spitze** (Feld Kap. 8; REQ-MECH-06 ≥ 1.0), keine Vias (REQ-MECH-05). Elektrodenlage nach Feld Kap. 8 mit z_f = −z |

**O-Ring-Bereiche** (keine Auflage an die Platine): Zapfen z 31.3 … 33.7, Kragen z 4.3 … 6.7, beide **AS568-019**.

## 4 Flächenbilanz Elektronikband (Nachweis)

Courtyards aus KiCad 10 (`pcbnew`, über `hardware/sensor/gen/floorplan_options.py`), Stückliste abgeglichen mit
`hardware/sensor/gen/parts.py` (Stand 2026-11-07).

| Gruppe | mm² |
|---|---|
| Option (f) im Band (= Option c ohne U3): U1, Y1, Y2, C1–C4 1206, L1, Q1, U2, SW1 TS-1088, D1, 19 × C0402, 12 × R0402, L2 | 211.6 |
| D3: U4–U6 SN74LVC1G80 (3 × SC-70-5) + C25 + Q2 AO3401A + R13, − C23 (Cref2 entfällt) | +43.3 |
| **Courtyard im Band** | **254.9** |
| × Leiterbahn-/Fanout-Faktor 1.5 (**ANNAHME**, FLOORPLAN_OPTIONS Kap. 1) = **Bedarf** | **382.3** |
| **Band brutto 26.0 × 15.1** | **392.6** (Faktor effektiv 1.54) |
| Kragen: U3 SOT-563 + C24 0402 im Feld 4.4 × 2.0 | 6.6 Courtyard |

Der Blockplan (`pcb_rev_b_floorplan.png`, DXF-Layer `Plan_*`) ist überlappungsfrei geprüft. Jeder Block ist
≥ 1.1 × die Courtyard-Summe seiner Teile, die Oberkante liegt 0.3 mm unter der Antennenzone. Der Plan ist ein
Machbarkeitsnachweis, keine Platzierungsvorgabe (ausser D1/SW1). Grobe Ordnung: unten C1–C4 quer, links
Messkette (Q2, Teiler, U2 nahe der S-Zuleitung x −4.9), Mitte U1, rechts Y1/Y2, oben RF-Kette unter der
Antennenspeisung, UART R9–R12 links unten (kurzer Weg zum Testpad-Streifen).

## 5 Bauteile mit fester Lage (Toleranz: Mitte ± 0.2 mm, LED ± 0.3 mm in z)

| Ref | Teil | Mitte (x, z) | KiCad (X, Y) | Höhe | Festlegung |
|---|---|---|---|---|---|
| D1 | RGB 1615 TUOZHAN C7496855 | **(0, 43.9)** | (0, 9.6) | 0.6 | 0.4 mm über der Sichtfuge z 43.5, direkt hinter dem Tropfenfenster. Lichtschaft Ø 3.0 endet bei y = 4.0 → **d = 2.0 mm** (Ziel 1.5 … 2.5). Kein Lichtleiter nötig |
| SW1 | XUNPU TS-1088-AR02016 C720477 | **(−6.0, 45.1)** | (−6.0, 8.4) | 2.0 | Footprint `SW_SPST_TS-1088-xR020` unrotiert: Pads 2 × (1.05 in x × 2.0 in z), Mittenabstand 4.45 in x. Betätiger Ø 1.8, Hub 0.2, 1.57 N (`XUNPU_TS-1088-AR02016_Datasheet_LCSC-2022-06.pdf` S.1). Betätigung senkrecht (+y) durch die Biegezunge der Kappe |
| XBT1 | Keystone 3034TR C5213768 | Zelle **(3.0, 19.05)** | (3.0, 34.45) | 4.1 | 90° gedreht: Einschub in x, **geschlossenes Ende −x** (Quersteg + Anschlaglappen), **offenes Ende +x** (Ein-/Ausschub). **Clipkörper x −4.4 … 11.7** (Katalog B 7.4 ab Zellmitte, L 16.1; KiCad-Footprint −4.44 … 11.9, 3D-Modell −4.76 … 11.65); Zelle Ø 20 x −7.0 … 13.0, bündig mit der rechten Kante. **Plus-Pads (VBAT): 2 × 5.08 (x) × 1.27 (z), x 0.46 … 5.54, Spanne W 23.1 = z 7.50 … 30.60 (Y 22.90 … 46.00), Padmitten Y 23.535 und 45.365** (Katalogminimum, Rev-B-Footprint 23.24: je 0.07 kürzen, LS-W1 a). Minuspad 4 × 4 in der Zellmitte |
| U3, C24 | TMP1075NDRLR C3663690 + 100 nF | **Feld x −9.0 … −4.6, z 4.4 … 6.8** (K-2) | Y 46.7 … 49.1 | ≤ 0.7 | Kragen-Tasche (Z5B), freigegeben unter K-1…K-7. Layout Rev B: U3 (−6.69, 5.60), C24 (−8.45, 5.50), Pads innerhalb |
| TP1, TP2 | Pads (Via-in-Pad) | Streifen x −12.7 … −7.5, z 12 … 30 | X −12.7 … −7.5, Y 23.5 … 41.5 | 0 | nur Pads; **TP3 entfällt** (A-1) |
| TP4, TP5 | Pads | B-Seite im Band | | 0 | OSZ_OUT, PROBE_SENSE (D3) |
| ANT | AN043 `…_Right` | Kupfer x −2.2 … 12.2, z 47.8 … 53.2 | Speisepunkt (0.35, 5.45) | – | Layout Rev B (L-5) |
| Logo | Wortmarke v3a mono | F, x −9 … 3, z −4.4 … −0.8 | | Silk | 10 mm breit (Strich 0.52 mm), REQ-MECH-16 |
| Rev | „fluidi rev B“ | B, z −4.4 … −0.8 | | Silk | REQ-MECH-16 |

## 6 Gehäuseteile nahe der Platine (CAD-Lauf `check_sensor.txt`)

| Teil | Lage | Abstand |
|---|---|---|
| Biegezunge (Kappe) | x −7.6 … −4.4, y 3.6 … 4.4, z 43.5 … 53.9 | 0.2 mm zu SW1 (Ruhe, KiCad-Modell 2.0; mit H 2.1 max. 0.1); Betätiger Ø 1.8 liegt 0.7 mm innerhalb der Zunge (x und unten); Hebel 2.5 → 0.49 mm Weg am Betätiger, nötig 0.40 |
| **Platinenanschlag + Gabel (Kappe, Rev C)** | x −8.0 … −3.0; Anschlagfläche z 53.5; Gabel z 52.0 … 53.5, y 5.75 … 6.55 (vor F) und 8.35 … 9.15 (hinter B) | Platinenoberkante liegt an (beim Schott-Verguss kopfüber durch das Eigengewicht). 0.8 mm neben dem Antennenkupfer (x −2.2) |
| Stössel Ø 3 / Rohr Ø 4, Finger, Tastenblock | Achse (−2.2, 3.8), z 49.1 … 56 | zum echten Antennenkupfer (STEP): Stössel **1.26 mm**, Kappe 0.76 mm, Membran 1.00, Klemmring 1.50, Taste 2.00 |
| Fenster-Lichtschaft Ø 3.0 | x 0, z 42.4 … 45.4, bis y 4.0 | 3.5 mm zum Antennenkupfer |
| Zapfen innen | x ± 13.2, y 4.4 … 8.4 (z 32 … 44.9) | 0.2 mm zur Bauteilhülle 2.0 und zur B-Seite |
| Schott-Durchführung | x ± 13.2, y 4.4 … 8.4 | danach mit Schottkeil + Epoxid verschlossen |
| Mutter / Schraube M2 (Metall) | Achse x 0, **y 4.2**, z −1.3 … 4.0 | 43.9 mm zur Antenne, 0.4 mm vor F (vergossen) |
| Zelle / Clip (Metall) | | 18.85 / 17.13 mm zur Antenne (STEP) |
| Clip ↔ Kragen / Schottkeil / Verguss | Clip-Pads z 7.43 … 30.67 (Rev-B-Footprint) | **0.13 mm** je Seite (Rev C mit W 23.1: 0.20); Zelle 1.75 mm |

## 7 Dichtungen, Sichtschale und Verguss

- **Elektronikraum** = Kern über dem Schott (z ≥ 32.0): Kappe + Zapfen, dauerhaft geschlossen (S3-K1). Öffnungen:
  Fenster (geklebt), Taste (Silikonmembran), Schott (Verguss + Schottkeil).
- **Sichtfuge z 43.5** ist **nicht** dicht: Oberhalb des Zapfen-O-Rings ist die graue Hülse nur Sichtschale
  (Wand 1.6) über dem Kern. Wasser, das an der Fuge oder der Tropfenkerbe eindringt, läuft im Spalt **0.7 mm**
  (Gleitspalt 0.2 + Rücksprung 0.5 des Zapfens) auf eine **nach hinten geneigte Stufe** (z 36.2 vorne → 34.7 hinten,
  6.6°) und durch **4 Schlitze 3.0 × 1.2 mm** in der Hülsenrückwand ab (Unterkante = tiefster Punkt). Die Fuge selbst
  bleibt Dachziegel (Kappenschürze 0.8 aussen über dem Hülsenrand, 1.2 mm Überdeckung).
- **Zellfach** = zwischen Kragen und Schott, zwei radiale **O-Ringe AS568-019** (ID 20.35, CS 1.78,
  `GTWeed_AS568_StandardOringSizing.pdf` S. 2), Nutgrund-Eckradius 3.0 → Dehnung 2.1 %, Verpressung 21–27 %
  (FDM ± 0.1: 15–33 %), Nutfüllung 77 %. Klebefuge Fenster → O-Ring-Nut 7.7 mm.
- **Sondenübergang** = Kragen-Verguss z 2.0 … 7.3 (Dichtstreifen Platine z 2.0 … 4.2), wird nie gelöst (S3-K2).
  Tasche für U3 + C24 vor F (x −9.6 … −4.4, 1.2 tief, z 2.0 … 6.8, **unten offen**: der Verguss erfolgt kopfüber
  von der Hohlkehle aus, die Tasche entlüftet nach oben). Vergussvolumen Kragen 62 mm³ (Rev A 43).
  Epoxid mineralisch gefüllt, Tg ≥ 80 °C (**ANNAHME** Typ, FLOORPLAN 2f).
- Montage: Kappe + Fenster + Stössel → Platine von unten **bis zum Anschlag** einschieben (Rev C) → Schottkeil + Epoxid (Kappe kopfüber)
  → Kragen mit 2 Distanzlehren 23.5 mm auf der B-Seite gegen das Schott setzen, Mutter von vorne einschieben,
  vergiessen (Kapton-Punkt auf die Mutter) → Lehren entfernen.

## 8 Bauteilhöhen je Zone (Übersicht)

| Zone | F | B |
|---|---|---|
| Z1 Antenne | 0 | 0 |
| Z2 Band | **2.0** (überall, auch unter der Zunge) | 0 (Pads erlaubt) |
| Z3 Schott | 0 | 0 |
| Z4 Fach | nur 3034 (4.1), Pads im Streifen | 0 (Silk) |
| Z5B Kragen | **0.7** nur im Feld U3/C24 | 0 |
| Z5A, Z6, Z7 | 0 | 0 |

Bauteile laut Schaltplan Rev B (`hardware/sensor/out/fluidi_sensor_bom_jlc.csv`, 2026-11-07; deckt sich mit Kap. 4:
4 × 1206, 17 + 2 DNM × C0402 im Band, 13 × R0402, 4 × SC-70-5, 2 × SOT-23, SOT-563 im Kragen) und ihre Höhe gegen die Grenzen:

| Teil | Höhe | Quelle | Zone, Grenze |
|---|---|---|---|
| SW1 TS-1088-AR02016 | 2.0 | XUNPU-Datenblatt S.1 | Z2, 2.0 (bestimmend; Zunge 0.2 davor) |
| XBT1 Keystone 3034 | 4.1 | Keystone_3034_Catalog_M65.pdf S.1 | Z4, 4.1 |
| L1 WPN201610H | 1.0 | INDEX L1 (2.0 × 1.6 × 1.0) | Z2, 2.0 |
| D1 1615 | 0.6 | Elektronikbericht 1.1 | Z2, Lichtschaft 2.0 davor |
| U3 SOT-563 / C24 0402 | 0.6 / 0.55 | FLOORPLAN_OPTIONS 2f | Z5B, 0.7 |
| U1 CC2340R5 RGE0024B | 1.0 max | `TI_CC2340R5_Datasheet_SWRS272F.pdf` S. 77 („1 MAX“; STEP-Ersatzmodell 0.8) | Z2, 2.0 |
| U3 TMP1075N DRL0006A | 0.6 max | `TI_TMP1075_Datasheet_SBOS854F.pdf` S. 36 („0.6 MAX“; KiCad-Modell 0.63) | Z5B, 0.7 |
| D1 1615 (nachgeprüft) | 0.6 ± 0.1 | `TUOZHAN_…_Datasheet_A0.pdf` S. 4 (1.6 × 1.5 ± 0.1) | Z2 |
| SW1 (Toleranz) | 2.0 ± 0.1 | XUNPU S. 1, Allgemeintoleranz 0.5…2: ± 0.10 → Zungenspalt 0.1 … 0.3 | Z2, 2.0 |
| C1–C4 1206 100 µF, Y1/Y2, SC-70, SOT-23, 0402 | KiCad-Modelle 1.6 / 0.64, 0.93 / 1.1 / 1.2 / ≤ 0.5 | **ANNAHME** Modell = Datenblatt (Datenblätter C1–C4 nicht lokal) | Z2, 2.0 |

Hinweis Kosten: `COSTS_REV_B.md` rechnet mit 26 × 160 mm; die Kontur Rev B ist 26 × 158.5 mm (Sonde 20 mm), die Annahme
liegt also auf der sicheren Seite.

## 9 Offene Punkte

1. **Projektleitung (LS-W1):** Clip-Pad zu den Vergusskanten ≥ 0.3 mm inkl. Toleranz geht im Fach 23.5 nicht
   (W 23.1 → 0.20 je Seite nominal, ± 0.22 Lage). Nötig 23.1 + 2 × 0.3 + 0.22 + 0.25 = 24.17 mm. **Vorschlag V-K:** Hülsenboden 2.0 → 1.3, Kragen samt
   Tasche, Mutter, O-Ring-Nut und Feld 0.7 mm tiefer (Kragen z 1.3 … 6.6), Zelle/Clip 0.35 mm tiefer (Zellmitte z 18.70,
   Y 34.80; Pads z 7.15 … 30.25, Y 23.25 … 46.35) → je Seite 0.55 nominal, ≥ 0.30 (RSS) bzw. ≥ 0.15 (worst); die Pads liegen
   dann ausserhalb Z3 und Z5B (keine Ausnahme mehr). Folgen: Z5A/Z5B/Z6 und Feld U3/C24 0.7 mm tiefer (Layout),
   FEM Hülsenboden 1.3, Feld: Vergusskante z 1.3. Details
   `docs/reviews/phase4_kollision_mechanik.md`. Bis zum Entscheid gilt Rev C.
2. **Elektronik:** Kunststoff vor der Antenne (Kappe 0.76, Membran 1.0, Stössel 1.26 mm) bestätigen; S11/RSSI im Gehäuse (**PROTOTYP-PRÜFUNG**).
3. **Elektronik:** Footprint 3034 auf Pad-Spanne 23.1 (Kap. 5), TP3 streichen (A-1).
4. **Mechanik:** Abfluss an der Sichtfuge und Kragen-Verguss mit Tasche am Muster prüfen (REQ-MECH-13, **PROTOTYP-PRÜFUNG**);
   dünnste Zapfenwand 0.54 mm hinter den hinteren Nutecken (FDM: 2 Linien 0.42 mit Überlappung, Passprobe oben drucken).

## 10 Quellen

- Masse Kopf: D-019, `docs/design/PROPORTIONEN.md` (V4); Courtyards: KiCad-10-Footprints (`/usr/share/kicad/footprints`, `hardware/sensor/lib/fluidi.pretty`).
- `docs/references/GTWeed_AS568_StandardOringSizing.pdf` S. 2 (AS568-019); `docs/datasheets/XUNPU_TS-1088-AR02016_Datasheet_LCSC-2022-06.pdf` S. 1;
  `Keystone_3034_Catalog_M65.pdf` S. 1; `TI_TMP1075_Datasheet_SBOS854F.pdf`; `TI_SN74LVC1G80_Datasheet_SCES221T.pdf`; `docs/appnotes/TI_AN043_SmallPCBAntenna_SWRA117D.pdf`.
- Register: `docs/datasheets/_staging/INDEX_mech_b.csv`.

## 11 Revisionsvermerk

| Rev | Datum | Änderung |
|---|---|---|
| A | 2026-11-07 | Erstausgabe: Kopf 28 × 13 × 48, Platine 20 × 149, Band 5.6 mm (passte nicht, Kap. 7 Rev A) |
| B | 2026-11-07 | Kopf V4 34 × 13 × 57.5 (D-019): Platine Kopf 26 / Sonde 20 (Schulter 45°, Innenecke R 2), Länge 158.5, Oberkante z 53.5 (KiCad-Ursprung verschoben!); Band z 32.7 … 47.8 (15.1 mm), Antenne z 47.8 … 53.5; F-Fläche y 7.4 → 6.6; D1 (0, 37.4) → (0, 43.9); SW1 TS-1187A → TS-1088 bei (−6, 45.1); Clip x −10 … 6.1 → −7 … 9.1, Testpads links; Z5 geteilt (Z5A Dichtstreifen, Z5B U3-Feld); Kupfer Sonde ≥ 1.25; B-Seite Band: Pads erlaubt; O-Ring AS568-017 → -019; Sichtschale mit Ablauf. Unverändert: Sonde 20 × 1.6, Spitze, Stecktiefe z −5, Kragen z 2.0 … 7.3, Fach z 7.5 … 30.6, Schott z 30.8 … 32.0 |
| **C** | 2026-11-08 | **Kontur unverändert.** Clip 3034 nach Datenblatt x −4.4 … 11.7 (Rev B −7 … 9.1 falsch, LS-W3/L-2), Plus-Pads Spanne 23.1 (z 7.50 … 30.60), Ausnahmen Z3/Z5B für die Clip-Pads; Antenne `…_Right` an Layout-Lage (L-5); Feld Z5B x −9.0 … −4.6, Vias tented ≥ 1.0 zur Kante (K-2, L-4); Z5A Innenlagen nur GND/Guard + Sonde (K-1); K-3; TP3 entfällt, 4 VIP im Fach (A-1); Platinenanschlag + Gabel in der Kappe (Lage z definiert); STEP-Koordinatenbezug (Kap. 1); Bauteilhöhen nach Datenblatt (Kap. 8). Nachweis `mechanical/sensor/collision_pcb_step.txt` |
