# Phase 4, Welle 3 – Kollisions- und Schnittstellenprüfung Mechanik ↔ Platine Rev B

| | |
|---|---|
| Datum | 2026-11-08 |
| Prüfer | Mechanik |
| Eingaben | `hardware/sensor/out/fluidi_sensor.step` (KiCad 10.0.8), `hardware/sensor/fluidi_sensor.kicad_pcb` (über `pcbnew`), `hardware/sensor/out/LAYOUT_REV_B.md` (L-2, L-4, L-5), `docs/reviews/phase4_layout_revb_sicherheit.md` (LS-W1, LS-W3, A-1), `mechanical/gen/fluidi_params.py`, `fluidi_sensor.py` |
| Werkzeug | `freecadcmd mechanical/gen/fluidi_pcb_collision.py` (neu, FreeCAD 0.21.2 + pcbnew) → `mechanical/sensor/collision_pcb_step.txt`, Baugruppe `mechanical/sensor/fluidi_sensor_mit_pcb.step`; `freecadcmd mechanical/gen/fluidi_sensor.py` → `check_sensor.txt` |
| Ergebnis | **Keine Kollision in Endlage** (Schnittvolumen 0 für alle 52 Bauteile, Zelle, Antennenkupfer und Platine gegen 16 Gehäuseteile). Kleinster Abstand Metall ↔ Gehäuse/Verguss 0.13 mm (Clip-Pads, L-2). Die Lage der Platine in z war in Rev B nicht festgelegt (Befund M-1, behoben). PCB_OUTLINE Rev C ohne Konturänderung erstellt |

## 1 Koordinatenbezug (Ergebnis Kap. A)

- KiCad-Hilfsursprung `aux_axis_origin` (150, 30) = Mitte Platinenoberkante: `x = X_Seite − 150`, `z = 53.5 − (Y_Seite − 30)`.
- KiCad-STEP (`kicad-cli pcb export step` ohne Ursprungsoption) hat Seitenkoordinaten mit gespiegeltem Y, Z = Höhe über der B-Seite:
  `x = X_s − 150`, `y = 8.2 − Z_s`, `z = 83.5 + Y_s`. Das ist eine Drehung um +90° um x und eine Verschiebung um (−150, 8.2, 83.5).
- Nachgeprüft: Die STEP-Platine liegt nach der Transformation bei x ±13.000 und z −105.000…53.500. Die Bauteile sitzen auf y = 6.60 (F).
  Die Kontur aus dem STEP und `fluidi_params.outline()` weichen um 0.076 mm² ab (Bogen R 2 als 8-Eck). Der STEP-Platinenkörper ist
  1.52 mm dick, weil KiCad nur die Dielektrika zählt. Für die Prüfung wird die Generatorplatte mit 1.6 mm verwendet.
- Zuordnung STEP-Körper → Referenz über die Courtyards aus `pcbnew`. Ersatz und Ergänzungen nach Datenblatt:
  - D1: Hülle 1.7 × 1.7 × 0.7 (`TUOZHAN_…_A0.pdf` S. 4)
  - U1: Hülle 4 × 4 × 1.0 (`TI_CC2340R5_Datasheet_SWRS272F.pdf` S. 77, RGE0024B „1 MAX“; STEP-Ersatz 0.8)
  - CR2032: Ø 20 × 3.2
  - Antennenkupfer: Polygon aus F.Cu des Footprints AE1
  - L1: Ersatzmodell DFE201610P, 1.0 hoch = WPN201610H „C max 1.0“ (`Sunlord_…_LCSC-2023-10.pdf` S. 2)
  - BT1: KiCad-Modell 4.0 hoch, Katalog H 4.1 (`Keystone_3034_Catalog_M65.pdf` S. 1). Der Unterschied von 0.1 ist nur nach vorne relevant (Hülse 0.95 → 0.85 mm).

## 2 Ergebnisse

| Prüfung | Ergebnis (Rev C, `collision_pcb_step.txt`) |
|---|---|
| Kollision in Endlage | **keine** (Volumen > 1e-4 mm³). Gewollte Überdeckungen: Clipfeder ↔ Zelle (Modell ungespannt), U3/C24 im Verguss |
| Bauteilhöhen | Band: alle ≤ 2.0 (SW1 nominal 2.0, Datenblatt ± 0.1). Fach: BT1 4.0/4.1. Kragen: U3 0.63 (DS 0.6), C24 0.5 ≤ 0.7. B-Seite: nur TP4/TP5 |
| Kleinste Abstände | Clip ↔ Kragen / Schottkeil / Verguss **0.13**. SW1 ↔ Zunge 0.20. U3 ↔ Kragen 0.40. C1–C4 ↔ Kappe 0.60. C24 0.70. Q1 0.76. Antennenkupfer ↔ Kappe 0.76 |
| Einschieben der Platine von unten (STEP-Bauteile, mit Clip) | frei |
| Hülse 160 mm abziehen (mit Zelle) | frei |
| Zelle 30 mm nach +x aus- und einschieben | frei, auch gegen alle Bauteile ausser dem Clip. In der Hülse 2.40 mm bis zur Wand |
| Lage der Platine in z | Rev B: 0.70 mm frei bis zum Tastenblock. **Rev C: Anschlag, 0.00** |
| LED D1 | Mitte (0, 43.90) = Tropfenmitte. LED ↔ Lichtschaft 2.00 (Datenblatt-Höhe max.: 1.90). Im Kreis r 1.8 nur R6/R7/R8, h 0.35 |
| SW1 | (−6.0, 45.1) unrotiert. Pads in x (x −8.75…−7.70 / −4.30…−3.25). Betätiger Ø 1.8 liegt 0.70 mm innerhalb der Zunge (seitlich und unten). Spalt 0.20 (H 2.1: 0.10) |
| Antenne | `Texas_SWRA117D_2.4GHz_Right`, Kupfer x −2.2…12.2, z 47.8…53.2. Kunststoff: Kappe 0.76, Membran 1.00, Stössel 1.26, Klemmring 1.50, Taste 2.00 mm. Metall: SW1-Deckblech 2.28, Clip 17.1, Zelle 18.9, Mutter/Schraube M2 43.8 mm |
| Kragen | Nur U3 und C24 unter z 7.5. Pads im Feld K-2 (x −9.0…−4.6, z 4.4…6.8). Epoxid über U3 0.57 (DS: 0.60), über C24 0.70. Abstand zur Mutter 4.3 mm |
| Schott | Pads in Z3: nur BT1-Pad (bis z 30.67). Tiefstes Bandbauteil C1 1.50 mm über dem Schott |

## 3 Befunde

| Nr | Stufe | Befund | Vorschlag / Antwort |
|---|---|---|---|
| M-1 | **wichtig** | **Lage der Platine in z war in Rev B nicht festgelegt.** Die Oberkante hatte 0.4/0.7 mm Luft zum Tastenblock, und es gab keinen Anschlag. Beim Schott-Verguss liegt die Kappe kopfüber, die Platine rutscht dann +0.7 mm auf den Block. Mit dem STEP gerechnet: bei dz +0.70 kollidieren **U3 mit dem Taschendach des Kragens (0.16 mm³)** und der Clipfuss mit dem Schottkeil (0.58 mm³). Die LED steht dann 0.7 mm neben der Tropfenmitte (Toleranz ± 0.3). Bei dz +0.25 trifft der Clipfuss den Keil, bei −0.25 den Kragen. Die angenommene Toleranz „± 0.2“ war nicht konstruktiv abgesichert | **Umgesetzt:** Anschlag und Gabel in der Kappe (`PSTOP`, x −8.0…−3.0). Die Anschlagfläche liegt bei z 53.5, die Gabel reicht 1.5 tief, Luft F 0.05 / B 0.15, Wand 0.8. Sie liegt links neben dem Antennen-Keepout (0.8 mm zum Kupfer). Gedruckt wird kopfüber ohne Stützen (senkrechte Wände). Montage: Platine bis zum Anschlag einschieben, beim Verguss liegt sie durch ihr Gewicht an. Die Lage hat dann ± 0.22 (RSS) Toleranz statt 0…+0.7 |
| M-2 | **wichtig** (L-2, LS-W1) | **Clip-Pads an beiden Vergusskanten.** Pads z 7.43…30.67 (Spanne 23.24). Fach 23.50 (Kragen z 7.30 bis Schott z 30.80) → 0.13 je Seite. Die Pads liegen schon mittig. **„Zelle 0.4 mm nach unten“ ist abgelehnt:** Das untere Pad läge 0.27 mm im Kragen (rechnerisch nachgewiesen, Kap. E). Mit der Pad-Spanne auf dem Katalogminimum W 23.1 bleiben 0.20 je Seite. Die Forderung „≥ 0.3 inkl. Toleranz“ braucht 23.1 + 2 × 0.3 + 0.22 + 0.25 = **24.17 mm**, also 0.67 mm mehr Fach | Sofort (Rev C): Pad-Spanne 23.1 (unten). **Entscheidvorschlag V-K** (Projektleitung, Kap. 4): Hülsenboden 2.0 → 1.3, Kragen 0.7 tiefer, Zelle/Clip 0.35 tiefer → 0.55 je Seite nominal, ≥ 0.30 (RSS), ≥ 0.15 (worst case). Alternativ JLC „high precision“ ± 0.1 und Boden 1.4. DRC (LS-W1 c): Regel „Pad-Rand ≥ 0.2 (Rev C) bzw. ≥ 0.5 (V-K) zur Vergusskante“ in `pcb_rules.py` (Elektronik) |
| M-3 | **wichtig** (L-2-Teil 2, LS-W3) | **Clip-Geometrie:** Der Footprint stimmt, das Mechanikmodell Rev B (x −7.0…9.1) war falsch. Katalog: B 7.4, L 16.1. Footprint: Quersteg 7.39 ab Zellmitte → x −4.4. Das KiCad-3D-Modell bestätigt die Annahme der Sicherheit, dass B ab Zellmitte bemasst ist: Die **Anschlaglappen reichen bis 0.4 mm über F und liegen bei x −4.76…−1.62** (−x = geschlossenes Ende). Auf der +x-Seite gibt es keine Lappen. Einschub und Ausschub also +x. Die Zelle (x −7.0…13.0) ragt 2.6 mm über den Quersteg hinaus, die Lappen halten sie trotzdem (Lappenecke 8.7 mm von der Zellmitte < r 10). Einschubweg: Die Zelle kommt von +x, ihr linker Rand erreicht höchstens x −7.0. TP1/TP2 (x ≤ −9.85) werden **nie überstrichen**, Abstand 2.85 mm. Halt in der Hülse: max. 2.40 mm Weg nach +x, die Zellmitte bleibt unter dem Clipblech (Vorderkante x 11.65) | Umgesetzt in `fluidi_params.py` (`CLIP` X0 −4.4, X1 11.7, B 7.4), DXF `Comp_XBT1_clip`/`_pads`, PCB_OUTLINE Kap. 3/5. **PROTOTYP-PRÜFUNG** R2-W01 Nr. 3 (schräg, verkehrt, halb, CR2025) mit dem echten Clip |
| M-4 | **wichtig** | **SW1 Toleranzkette in y.** Der Spalt Zunge ↔ Betätiger ist nominal 0.20. Er hängt ab von der Höhe H 2.0 ± 0.1 (XUNPU S. 1), von der F-Lage (Gabel 6.55…8.35, Dicke 1.6 ± 10 % laut JLCPCB_NOTES → F 6.55…6.91) und von der Zunge (FDM ± 0.1). Spalt also **0.05…0.61**. Der Keil liefert 0.49 mm am Betätiger, nötig sind Spalt + Hub 0.2 (+0.1). Ab einem Spalt von 0.29 schaltet der Taster nicht sicher | Vorschlag (nicht umgesetzt, betrifft Membran/Taste): Quetschrippe 0.1 an der hinteren Gabelwange (F liegt an der vorderen Wange, F 6.55…6.6) und Tastenhub 0.6 → 0.8 (Keilweg 0.31 → 0.78 am Betätiger). **PROTOTYP-PRÜFUNG** Schaltpunkt mit Dickenstreuung |
| M-5 | klein | L-5: Footprint `…_Right` ist richtig (Einspeisung/Kurzschluss links, offenes Ende rechts). Kunststoff vor dem Kupfer: Kappe 0.76, Membran 1.00, Stössel 1.26 mm, alle am linken (Kurzschluss-)Ende. Am offenen Ende rechts liegt nur die Kappenwand (≥ 3 mm). Metall: Das Edelstahl-Deckblech von SW1 liegt 2.28 mm unter dem Kurzschluss-Ende (Lage fest seit Rev B). M2-Schraube/Mutter 43.8 mm | Elektronik: S11/RSSI im Gehäuse (**PROTOTYP-PRÜFUNG**, OP-K9). Kein Handlungsbedarf Mechanik |
| M-6 | klein | L-4 (K-1/K-2/K-3) und A-1 (TP3 entfällt, 4 VIP im Fach) standen noch nicht in PCB_OUTLINE | Umgesetzt in Rev C, Kap. 3 und 5 |
| M-7 | klein | STEP: D1 fehlt, U1/BT1/L1 sind Ersatzmodelle. Die Höhen sind gegen die Datenblätter geprüft (Tabelle Kap. 2). Die Datenblätter für C1–C4 (1206, 100 µF) fehlen lokal, daher Modellhöhe 1.6 = **ANNAHME** | Elektronik: Datenblatt C1–C4 ablegen (Höhe ≤ 2.0 belegen) |
| M-8 | klein | `collision_placeholder.txt` und `check_sensor.txt` rechneten mit einem mittigen Antennenblock und dem falschen Clip | Umgesetzt: Antenne an der Layout-Lage, Clip nach Datenblatt. Neue STEP-Prüfung als eigenes Skript |

**Kollisionen: nein** (in Endlage 0 mm³; Mindestabstand 0.13 mm Clip-Pad ↔ Kragen/Schott). Bei der Rev-B-Lagestreuung
(0…+0.7 mm) gäbe es Kollisionen. Rev C schliesst das mit dem Anschlag aus.

## 4 Entscheidvorschlag L-2 / LS-W1 und Masse für das Layout

**Sofort, Rev C (ohne Gehäuseänderung, ohne Konturänderung):**

| Mass | Wert (KiCad X/Y, Hilfsursprung) |
|---|---|
| Zellmitte / Footprint-Ursprung BT1 | **(3.000, 34.450)**, 90°, unverändert |
| Plus-Pads (2 ×, VBAT) | 5.08 (X) × 1.27 (Y), X 0.46 … 5.54; **Padmitten Y 23.535 und 45.365** (Footprint lokal ± 10.915 statt ± 10.985) → Aussenkanten Y 22.900 / 46.000, Spanne 23.10 = Katalog W min |
| Minuspad | 4 × 4 in der Zellmitte, Via-in-Pad gefüllt |
| Clipkörper (Fab/Hülle) | X −4.4 … 11.7 (Datenblatt), Höhe 4.1 |
| Abstand Pad ↔ Vergusskante | 0.20 / 0.20 nominal (Rev-B-Footprint 0.13) |
| TP1, TP2 | im Streifen X −12.7 … −7.5, Y 23.5 … 41.5; TP3 entfällt |

**Empfehlung V-K (Entscheid Projektleitung; erfüllt LS-W1 b):**
- **Mechanik:** Hülsenboden FLOOR 2.0 → 1.3. Kragen samt Tasche, Mutter, O-Ring-Nut und Hohlkehle 0.7 mm tiefer: Kragen z 1.3…6.6, Vergusskante Sonde z 1.3. Fach z 6.6…30.8 = 24.2 mm. Distanzlehre 23.5 → 24.2.
- **Layout:** Zellmitte z 18.70 → **BT1 (3.000, 34.800)**. Plus-Pads Y 23.250…24.520 und 45.080…46.350 (Spanne 23.1), Abstand je Seite **0.55** nominal. Die Pads liegen ganz in Z4 (Z3 ab Y 23.2, Z5B ab Y 46.7), es braucht keine Ausnahme mehr.
- **Folgen für die Zonen:** Kragenfeld U3/C24 0.7 mm tiefer (Y 47.4…49.8), U3 → Y 48.60, C24 → Y 48.70. Z5A Y 50.0…52.7, Z6 bis Y 52.7.
- **Folgen für Feld und FEM:** Elektroden bleiben (bezogen auf die Erde). Zwischen Verguss und Erde liegen 6.3 statt 7 mm, Feld Kap. 8 bleibt konservativ. FEM Hülsenboden/Kragen neu rechnen (Boden 1.3 mm ASA, Schlitz 20.8 × 2.4). Schraube M2 × 4 → M2 × 3 prüfen (Spitze 0.8 mm über der Mutter).
- **Toleranz:** Lage Pad zur Vergusskante ± 0.22 (Schott) / ± 0.25 (Kragen) RSS. Grundlage: JLC-Kontur ± 0.2 (`docs/references/JLCPCB_NOTES.md` Kap. 3), FDM ± 0.1, Lehre ± 0.1. Damit bleiben ≥ 0.30 mm.
- **Kosten:** keine (gleiche Teile, weniger ASA).

Alternativen:

| Variante | Ergebnis | Bewertung |
|---|---|---|
| Schott höher | Band 15.1 mm schrumpft, Fläche fehlt | verworfen |
| O-Ring-Steg 0.6 → 0.3 | spart nur 0.3 mm, FDM-Steg 1–2 Lagen | verworfen |
| Zelle ± 0.4 | eine Seite −0.27 | verworfen |
| JLC „high precision“ ± 0.1 + Boden 1.4 | ebenfalls ≥ 0.3 | Aufpreis offen |

## 5 Geänderte Dateien

- `mechanical/gen/fluidi_params.py`:
  - Rev C, Datum 2026-11-08
  - `CLIP` nach Datenblatt (B 7.4, X0/X1, PAD_D), `CELL['XC']` entkoppelt
  - `ANT` an der Layout-Lage, `PSTOP` (Anschlag/Gabel), `TMP` Feld K-2
  - Zonenregeln Z1/Z3/Z4/Z5A/Z5B (L-4, L-5, K-1…K-3, A-1, Ausnahmen Clip-Pads)
  - JSON-Felder `kicad_page`, `kicad_step`, `pads_plus`, `PCB_STOP`, `field_K2`; offene Punkte
  - DXF-Layer `Comp_XBT1_pads`, `Mech_Anschlag_Platine`, `Zone_Z5B_Feld_K2`
- `mechanical/gen/fluidi_sensor.py`: Anschlag und Gabel in der Kappe, Antenne an der Layout-Lage, Prüfung 5b (z-Anschlag, Pad-Luft), `main()` nur ohne `FLUIDI_NO_MAIN`.
- `mechanical/gen/fluidi_pcb_collision.py` (neu).
- Neu erzeugt:
  - `mechanical/sensor/`: `fluidi_sensor.FCStd`, `fluidi_sensor_assembly.step`, `print/*.{step,stl,3mf}`, `check_sensor.txt`, `collision_placeholder.txt`
  - `mechanical/sensor/`, neu: `collision_pcb_step.txt`, `fluidi_sensor_mit_pcb.step`
  - `mechanical/interfaces/`: `pcb_outline.json`, `.dxf`, `pcb_rev_b_floorplan.png` (Kontur geprüft unverändert)
- `docs/interfaces/PCB_OUTLINE.md` → Rev C.

## 6 Nachtrag Runde 2 (2026-11-08): V-K und M-4 umgesetzt (D-023)

### 6.1 Änderungen (Generator `fluidi_params.py` / `fluidi_sensor.py`)

| Punkt | Rev C (Runde 1) | **Rev C mit V-K/M-4** |
|---|---|---|
| Hülsenboden | 2.0 | **1.3** |
| Kragen / Vergusskante Sonde | z 2.0 … 7.3 | **z 1.3 … 6.6** (Mutter 1.6 … 3.2, O-Ring-Nut 3.6 … 6.0, Tasche 1.3 … 6.1) |
| Fach (Kragen → Schott) | 23.5 | **24.2**; Distanzlehre `print/distanzlehre_24p2` (alt `_23p5` gelöscht) |
| Zellmitte | z 19.05 (Y 34.45) | **z 18.70 (Y 34.80)** |
| Schraube | M2 × 4 | **M2 × 3**: Einschraubtiefe 1.40 mm (3.5 Gänge), Spitze 0.2 unter der Mutteroberkante; Freibohrung bis z 3.3, 0.30 mm unter der O-Ring-Nut (M2 × 4 hätte 0.8 über die Mutter geragt, 0.05 mm neben dem Nutgrund) |
| F-Referenz der Platine (M-4) | Gabel F 0.05 / B 0.15, Keil 0.15 Luft | vordere Gabelwange und Schottkeil-Rückseite **genau bei y 6.6**. Quetschrippen bis y 7.95: 1 an der hinteren Gabelwange (x −5.5), 2 an der Schott-Rückwand (x ± 9), alle mit Einlauffase. Überdeckung bei Dicke 1.44 … 1.76: 0.09 … 0.41 |
| Taster (M-4) | Hub 0.6, Spalt 0.20, Keilvorspalt 0.15 | **Hub 0.8, Spalt 0.25, Keilvorspalt 0.10** |

### 6.2 Ergebnisse

- `check_sensor.txt`:
  - Kollisionen in Ruhe: keine. Platine/Kappe ohne Rippen 0.0000 mm³, Rippen 0.435 mm³ (gewollt gequetscht).
  - Taste gedrückt (Hub 0.8): keine Überdeckung. Hülse abziehen, Zelle ausschieben, Platine einschieben: frei.
  - Anschlag: 0.00 mm.
- **Clip-Pads (Layoutvorgabe W 23.1):** z 7.15 … 30.25, Luft zu beiden Vergusskanten **0.55 mm**.
  - Mit Toleranz: Schott ≥ 0.33 (RSS) / 0.25 (worst), Kragen ≥ 0.31 (RSS) / 0.15 (worst) → **LS-W1 erfüllt (RSS)**.
  - Die Pads liegen ausserhalb Z3 und Z5B.
  - Der heutige Rev-B-Footprint (23.24) an der V-K-Lage hätte 0.48 je Seite.
- **Taster-Toleranzkette (2b):**
  - Weg am Betätiger 0.90 mm, nötig 0.45 (Spalt 0.25 + Hub 0.2). Reserve nominal 0.45.
  - Toleranzen RSS ± 0.32 → Reserve **+0.13** (vorher Rev C: Spalt 0.05 … 0.61, Reserve negativ ab Spalt 0.29). Worst case −0.20.
  - Spalt in Ruhe min. 0.08 (RSS) bzw. −0.05 (worst; kleiner als der Mindesthub 0.1, also kein Dauerbetätigen).
  - Nach dem Schaltpunkt bleiben 0.45 mm Überhub. Den nimmt die Biegung des Fingers auf (**PROTOTYP-PRÜFUNG** Schaltgefühl, Tasterbelastung).
- **STEP-Prüfung** (`collision_pcb_step.txt`; BT1 −0.35, U3/C24 −0.70 an die Layoutvorgabe verschoben):
  - Kollision: keine.
  - Kleinste Abstände:
    - Clip ↔ Kragen / Schottkeil 0.48 (Rev-B-Footprint)
    - SW1 ↔ Zunge 0.25
    - U3 ↔ Kragen 0.40, C24 0.70
    - Epoxid über U3 0.57 (DS 0.60)
  - U3/C24 liegen im Feld z 3.7 … 6.1.
  - Lage in z: dz −0.25 kollisionsfrei, dz > 0 sperrt der Anschlag.
  - Antenne: Kappe 0.76, Stössel 1.26, M2 44.6 mm.
  - Einschieben und Hülse abziehen: frei.

### 6.3 Masstabelle für das Layout (KiCad, Hilfsursprung (150, 30))

| Element | Vorgabe |
|---|---|
| BT1 (Footprint-Ursprung = Zellmitte) | **(3.000, 34.800)**, 90° |
| Plus-Pads 2 × | 5.08 (X) × 1.27 (Y), X 0.46 … 5.54; **Padmitten Y 23.885 / 45.715** (lokal ± 10.915), Aussenkanten Y 23.250 / 46.350 (Spanne 23.10) |
| Minuspad | 4 × 4, Mitte (3.000, 34.800), Via-in-Pad gefüllt |
| Clipkörper (Fab) | X −4.4 … 11.7, Y 23.25 … 46.35, H 4.1 |
| Vergusskanten | Schott Y 22.70, Kragen Y 46.90, Sonde Y 52.20 |
| DRC | Pad-Rand ≥ 0.5 mm zu Y 22.70 und Y 46.90 (Regelflächen Y 22.2 … 23.2 und 46.4 … 47.4 ohne Pads) |
| U3 | (−6.69, **48.60**), C24 (−8.45, **48.70**) (je +0.70) |
| Kragenfeld K-2 | X −9.0 … −4.6, **Y 47.4 … 49.8** |
| Zonen | Z3 Y 20.8 … 23.2; Z4 Y 23.2 … 46.7; Z5B Y 46.7 … 50.0; Z5A Y 50.0 … 52.7; Z6 Y 52.7 … 58.5 |
| Testpads Fach | nur TP1, TP2 (X −10.6, Y 25.5 / 28.5, Via-in-Pad); TP3 entfällt (A-1) → 4 VIP: VBAT, Minus, TP1, TP2 |
| Platinenanschlag | X −8.0 … −3.0 an der Oberkante (Y 0 … 1.5 Gabel): keine Bauteile, Kupfer erlaubt |
- **FEM** (`simulation/fem/REPORT.md` Kap. 5), Vergusskante z 1.3:
  - LC1: 149.4 MPa 0.5 mm vor der Kante, SF **2.31**; 167 MPa an der Kante, SF 2.06.
  - LC6: **238 N**.
  - LC1b: 175 MPa, SF 1.97 (Rev B 1.81).
  - Fall 1 m: SF 1.71, unverändert.
  - REQ-MECH-10 erfüllt (Bedingung D-023).
  - Hülsenboden 1.3 von Hand gerechnet: Schub 0.52 MPa (Einstecken 50 N), 2.9 MPa (Kippen LC1), SF ≥ 9.
