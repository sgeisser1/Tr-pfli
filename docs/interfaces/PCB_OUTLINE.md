# Schnittstelle PCB-Kontur ↔ Gehäuse – fluidi Sensor P3

| | |
|---|---|
| Revision | **A** (2026-11-07) |
| Status | **verbindlich für das Layout (Phase 4b, Welle 2)**. Änderungen nur über eine neue Revision (Mechanik + Elektronik) |
| Maschinenlesbar | `mechanical/interfaces/pcb_outline.json`, `mechanical/interfaces/pcb_outline.dxf` (Edge.Cuts + Zonen als Layer, KiCad-Koordinaten) |
| Erzeugt von | `.venv/bin/python mechanical/gen/fluidi_params.py` (einzige Quelle aller Masse, auch für das CAD) |
| Geprüft mit | `freecadcmd mechanical/gen/fluidi_sensor.py` → `mechanical/sensor/check_sensor.txt` |
| Grundlage | D-009/D-010 (P3 28 × 13 × 48, Sonde 20 mm, 5 mm Abstand), `docs/reviews/phase3_sleeve_mechanik.md` (A1), `phase3_sleeve_sicherheit.md` (S3-K1/K2, W1–W4), `phase2_concepts_sicherheit.md` (R2-A2/A3, R2-W01), `phase3_rgb_antenne_elektronik.md` (1.9, RGB-5) |

## 1 Koordinaten

- **Kopf:** x = Breite (0 = Mitte, + rechts, von vorne gesehen), y = Tiefe (0 = Frontfläche, + nach hinten), z = Höhe (0 = Kopfunterkante).
- **KiCad:** `X = x`, `Y = 44.0 − z` (Ursprung Mitte Platinenoberkante, Y nach unten zur Spitze). Top-View = Ansicht von vorne.
- **F-Seite (F.Cu, bestückt) zeigt nach vorne zum Fenster (−y)**, Oberfläche bei y = 7.4. B-Seite y = 9.0, **unbestückt** (JLC Economic einseitig, `phase2_concepts_fertigung.md` W-4).

## 2 Platine

| Mass | Wert |
|---|---|
| Dicke, Lagen | 1.6 mm, 4 Lagen (REQ-MECH-04/11) |
| Breite | **20.0 mm durchgehend** (Kopf und Sonde, keine Schulter) |
| Länge | **149.0 mm**: Oberkante z = 44.0 (KiCad Y 0), Spitze z = −105.0 (Y 149) |
| Spitze | **45°** beidseitig, Spitzenfläche 5.0 mm breit; Fasenbeginn z = −97.5 (Y 141.5) |
| Kontur (KiCad X/Y) | (−2.5/149) (2.5/149) (10/141.5) (10/0) (−10/0) (−10/141.5) |
| Sonde inkl. Beschichtung | max. 20.4 × 2.0 mm (Bodenschlitz der Hülse 20.8 × 2.4) – **ANNAHME** Schichtdicke, mit REQ-MECH-07 festlegen |
| Lage im Kern | z ± 0.2 mm (Montage mit Distanzlehre, Kap. 6) |
| Max. Stecktiefe | Silkscreen-Linie bei **z = −5.0 (Y 49.0)** auf F und B, x −9…9, Text „max“ + Pfeil (REQ-MECH-01). 100 mm im Boden |

## 3 Zonen (alle x −10…10, z von…bis; KiCad-Y in Klammern)

| Zone | z (Y) | Seite | Max. Höhe | Regel |
|---|---|---|---|---|
| Z1 Antenne | 38.3 … 44.0 (0 … 5.7) | F+B | 0 | AN043-IFA 15.2 × 5.7 inkl. Masse-Keepout nach AN043. Kein Metall des Gehäuses. Kunststoff vor F siehe Kap. 5 |
| Z2 Band F | 32.7 … 38.3 (5.7 … 11.3) | F | **2.0 mm** | Elektronikband. ≤ 2.0 mm, weil die Platine von unten durch das Schott geschoben wird. **In Spalte x −7.8 … −4.2 ≤ 1.5 mm** (Biegezunge). D1, SW1 fest (Kap. 4) |
| Z2 Band B | 30.3 … 44.0 | B | 0 | unbestückt |
| Z3 Schott | 30.3 … 32.7 (11.3 … 13.7) | F+B | 0 | Schott-Verguss z 30.8 … 32.0: keine Bauteile, **keine Vias, kein Kupfer auf Aussenlagen**, Lötstopp geschlossen. Signale nur Innenlagen (S3-K1, M-03) |
| Z4 Fach F | 7.5 … 30.3 (13.7 … 36.5) | F | 4.1 | Zellfach: **nur** Keystone 3034, Minuspad, UART-/Testpads (Streifen x 6.6 … 9.5). Unter der Zelle nur Lötstopp ausser Minuspad (R2-W01 Nr. 1/2). Keine Vias (S2-W03). 2 × 100 kΩ im Elektronikraum (R2-A3) |
| Z4 Fach B | 7.5 … 30.3 | B | 0 | Silkscreen-Warnsymbol Dreieck ≥ 7 × 9 mm + „CR2032 Verschluckgefahr“ (S3-W4, zweiter Ort) |
| Z5 Kragen | 1.5 … 7.5 (36.5 … 42.5) | F+B | 0 | Kragen-Verguss z 2.0 … 7.3 = **Sondendichtung** (S3-K2, REQ-MECH-08/15): keine Bauteile, keine Vias, kein Aussenkupfer. Mutter M2 0.4 mm vor F |
| Z6 frei | −5.0 … 1.5 (42.5 … 49.0) | F+B | 0 | zwischen Erde und Kragen: **keine Elektroden** (Luftanteil). F: Logo, B: „max“ + Revision |
| Z7 Sonde | −105 … −5 (49 … 149) | F+B | 0 | Elektroden nur Innenlagen, Aussenlagen ohne Kupfer (REQ-MECH-04), Kupfer ≥ 1.0 mm zur Kontur (REQ-MECH-06), keine Vias (REQ-MECH-05) |

**O-Ring-Bereiche** (zur Information, keine Auflage an die Platine): Zapfen z 31.3 … 33.7, Kragen z 4.3 … 6.7, beide **AS568-017** (Kap. 6).

## 4 Bauteile mit fester Lage (Toleranz: Mitte ± 0.2 mm, LED ± 0.3 mm in z)

| Ref | Teil | Mitte (x, z) | KiCad (X, Y) | Höhe | Festlegung |
|---|---|---|---|---|---|
| D1 | RGB 1615 TUOZHAN C7496855 | (0, 37.4) | (0, 6.6) | 0.6 | Leuchtfläche zum Fenster. Lichtschaft Ø 3.0 des Fensters endet bei y = 4.8 → **d = 2.0 mm** (Ziel 1.5 … 2.5, Elektronikbericht 1.9) |
| SW1 | TS-1187A-B-A-B C318884 | (−6.0, 35.6) | (−6.0, 8.4) | 1.5 | Anschlüsse in x (Pads x −9.5 … −2.5 bei Rastermass 7.0/4.5, `XKB_TS-1187A…pdf` S.1). Betätigung senkrecht (+y) durch die Biegezunge |
| XBT1 | Keystone 3034TR C5213768 | Zelle (0, 19.05) | (0, 24.95) | 4.1 | **90° gedreht**: Einschub in x, geschlossenes Ende −x, offenes Ende +x; Clip x −10.0 … 6.1, z 7.5 … 30.6; Zelle Ø 20 bündig mit den Platinenkanten |
| ANT | AN043 | z 38.3 … 44.0 | Y 0 … 5.7 | – | Lage in x durch die Elektronik |
| Logo | Wortmarke v3a mono | F, x −9 … 3, z −4.4 … −0.8 | | Silk | 10 mm breit (Strich 0.52 mm), REQ-MECH-16 |
| Rev | „fluidi rev A“ | B, z −4.4 … −0.8 | | Silk | REQ-MECH-16 |

## 5 Gehäuseteile nahe der Platine (Abstände aus dem CAD-Lauf)

| Teil | Lage | Abstand |
|---|---|---|
| Biegezunge (Kappe) | x −7.6 … −4.4, y 4.9 … 5.7, z 34.0 … 44.4 | 0.2 mm zu SW1 (Ruhe) |
| Stösselrohr Ø 4, Finger, Tastenblock (Kunststoff) | vor F im Antennenbereich, z 39.6 … 46 | **Stössel 1.3 mm, Kappenblock 0.5 mm** zum Antennenkupfer → **Elektronik bestätigt** |
| Fenster-Lichtschaft Ø 3.0 | x 0, z 35.9 … 38.9, bis y 4.8 | 2.6 mm zum Antennenkupfer, endet unter der Antennenzone (RGB-5) |
| Zapfen innen | y ≥ 3.75 (z < 34.2) | Bauteile ≤ 3.45 mm wären möglich, begrenzend ist das Schott (2.0) |
| Schott-Durchführung | x ± 10.2, y 5.2 … 9.2 | danach mit Schottkeil + Epoxid verschlossen |
| Mutter / Schraube M2 (Metall) | Achse x 0, y 5.0, z −1.3 … 4.0 | 34 mm zur Antenne, 0.4 mm vor F (vergossen) |
| Zelle / Clip (Metall) | | 9.3 / 7.7 mm zur Antenne |

## 6 Dichtungen und Verguss (Bezug für Layout-Sperrzonen)

- **Elektronikraum** = Kappe über dem Schott (z ≥ 32.0): dauerhaft geschlossen (S3-K1). Öffnungen: Fenster (geklebt), Taste (Silikonmembran), Schott (Verguss + Schottkeil).
- **Zellfach** = zwischen Kragen und Schott, abgedichtet durch **zwei radiale O-Ringe AS568-017** (Silikon/EPDM ohne Russ) gegen die Hülse (S3-W3). Klebefuge Fenster → O-Ring-Nut **1.2 mm** (≥ 1 mm).
- **Sondenübergang** = Kragen-Verguss z 2.0 … 7.3, wird nie gelöst (S3-K2, REQ-MECH-15).
- Montage: Kappe + Fenster + Stössel → Platine von unten einschieben → Schottkeil + Epoxid (Kappe kopfüber) → Kragen mit 2 Distanzlehren 23.5 mm auf der B-Seite gegen das Schott setzen, Mutter von vorne einschieben, vergiessen (Kapton-Punkt auf die Mutter) → Lehren entfernen.

## 7 Offene Punkte an Elektronik (vor Layout-Freeze)

1. **KRITISCH – Platz im Elektronikband.** Band F = 20 × 5.6 = **112 mm²**. Die Bauteile laut Schaltplan Rev A
   (`hardware/sensor/out/fluidi_sensor_bom_jlc.csv` + DNP-Footprints C3/C4/C19/C20) brauchen als Footprint-Hülle inkl. Pads
   + 0.25 mm Rand **≈ 251 mm²** (Abschätzung Mechanik: U1 20, Y1/Y2 19, 4 × 1206 38, U3 19, Q1 10, U2 7, L1 5, SW1 42,
   D1 4, 32 × 0402 87 mm²) – ohne Leiterbahnen. **Das passt nicht.** Optionen (kombinierbar), Entscheid vor dem Layout → Rev B:
   (a) **B-Seite im Band mitbestücken** (+112 mm², CAD hat 2.4 mm Freiraum hinter der Platine; Schott-Durchführung hinten
   verbreitern; JLC Standard-PCBA statt Economic, Kosten Fertigung W-4); (b) kleinere Bauteile (0201, kleinerer Taster,
   TMP1075 an die Sondenwurzel?); (c) **Kopf höher**: je +1 mm Band +20 mm² pro Seite (Designänderung, Auftraggeber);
   (d) Bauteile im Fach (Streifen x 6.6 … 9.5, ≈ 60 mm²) nur mit Freigabe Sicherheit (Flutung REQ-SAF-05).
2. Kunststoff vor der Antenne (Kap. 5) und Kappendecke 2 mm über der Oberkante bestätigen.
3. Lage SW1/D1 im Layout bestätigen (Pads SW1 enden 1.7 mm vor D1).
