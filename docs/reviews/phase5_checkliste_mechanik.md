# Phase 5 – Design-Review-Checkliste Mechanik (Sensor P3 V4 Rev C, Gateway G1 v4)

| | |
|---|---|
| Ersteller | Mechanik-Agent, 2026-11-08 |
| Stand | Basis git `b77b29a` + Arbeitsstand Phase 5 (P5-M1, P5-M3, Kollisionsskript, Zeichnungen) |
| Anforderungen | `docs/requirements/REQUIREMENTS.md` v1.1 |
| Status | **ok** = nachgewiesen (Datei/Prüfung) · **offen** = Nachweis oder Entscheid fehlt · **PROTOTYP-PRÜFUNG** = nur am Muster prüfbar (Testfall in `phase5_testplan_beitrag_mechanik.md`) |

## A Befunde dieser Prüfrunde (Phase 5, selbst gefunden)

| Nr | Stufe | Befund | Massnahme | Status |
|---|---|---|---|---|
| **P5-M1** | **kritisch** | **Kappe = 2 getrennte Körper.** Der Kappen-Innenraum P(1.6) begann direkt bei SLOT_TOP z 44.9; Zapfen (Aussenversatz 1.8) und Kappenwand (Innenversatz 1.6) hatten 0.2 mm Luft. `kappe_blau.step/.stl` enthielt 2 Körper (2360.5 + 1785.4 mm³, Abstand 0.20 mm). Der Zapfen mit O-Ring-Nut und Schott wäre beim Kopfüber-Druck ab 12.6 mm Höhe frei in der Luft begonnen → Druck unmöglich, Elektronikraum nicht geschlossen (S3-K1). Keine bisherige Prüfung zählte die Körper. | 45°-Trichter von SP_IN (z 44.9) auf P(1.6) (bis z 48.7), Zungentasche durch den Trichter verlängert (`fluidi_params.py` CAP FUNNEL, `fluidi_sensor.py`). Neue Prüfung 11 „Anzahl Körper je Druckteil“ in `check_sensor.txt`. | behoben, **Prüfung durch zweiten Agenten** |
| **P5-M3** | **kritisch** | **Membran-Senkung Ø 6.4 offen zum Elektronikraum.** Die Senkung (Achse x −2.2) ragte 0.2 mm seitlich aus dem Tastenblock (x 0.8 … 1.0, z 54.2 … 55.5), ihr Boden war für y > 6.2 offen (Block unten nur bis y 6.2). Ring 0.3 mm um Senkung nur 92 % Kunststoff. Wasser über der Membran (Taste, Klemmring-Spalt) gelangt am Membranrand vorbei in den Elektronikraum → REQ-MECH-13, S3-K1. Gefunden über die Messpunktprüfung der Zeichnung FL-S-02. | Mantel Ø 8.0 (Wand 0.8) um die Senkung von z 53.9 bis zur Decke. Neue Prüfung 12 (Ring + Boden 100 % Kunststoff). | behoben, **Prüfung durch zweiten Agenten** |
| **P5-M2** | **wichtig** | 30°-Keil zwischen Stössel und Biegezunge fehlte im CAD. Runde 1 (Nase 45°) vom Red Team widerlegt: Stössel frei drehbar (C-1), Überhub überlastet die Zunge (C-2), Toleranzkette unvollständig (W-2), Stössel-Drucklage (W-3). | Runde 2: 60°-Keil am Finger auf einer Nase in Höhe SW1, Führungsrippe + D-Bohrung (Verdrehung ±1.5°), Arm 1.5 hoch, D-Fläche bündig. `check_sensor.txt`: 2a SW1 schaltet nominal bei 0.3 mm Hub; 2b worst (inkl. Rippenspiel, Verdrehung, Hubverlust Arm, +50 gf) Reserve +0.17, Schaltpunkt worst 0.65 mm; 2c Tastenkraft 8.3/11.6 N; 2d Überlast 20 N: Zunge SF 1.63 nominal / 1.15 worst bei μ 0.3, < 1 bei μ ≤ 0.2 | CAD umgesetzt; **Überlast offen** (Antwort C-2 in `phase5_mechanik_redteam.md`), PROTOTYP-PRÜFUNG M-T1/M-T2/M-T5 |
| P5-M7 | wichtig | Membransitz (W-1) Boden 0.3, Klemmring ohne Befestigung (R3-W2/O-4) | Boden 0.8 ausser Sektor zur Platine/Antenne (0.3, `check_sensor.txt` 12b); Klemmring Presssitz 0.05 + Membranverpressung 0.1 (2e) | umgesetzt; PROTOTYP-PRÜFUNG M-W3 |
| P5-M8 | wichtig | Zapfenwand 0.54 an den hinteren Nutecken (R3-W3) | geometrisch ≥ 0.8 nicht ohne Platinen-/Nutänderung möglich (≤ 0.64); Druckvorgabe PRINT_SETTINGS Kap. 3, Durchleuchten | Druckvorgabe; Rev D |
| P5-M9 | klein | Mantel ragte 0.2 aus der Front (K-1); Schriftfeld-Stand (K-5) | Mantel auf Aussenkontur geschnitten (12c: 0 mm³); Schriftfeld mit Generator-SHA256 | umgesetzt |
| P5-M4 | wichtig | `fluidi_pcb_collision.py` verschob U3/C24 fest um −0.70 mm (V-K), obwohl Layout Rev C (03341e8) die Lage schon enthält → doppelte Verschiebung, Feld K-2 scheinbar verletzt (Lauf 2026-11-08). | Verschiebung nur noch, wenn die Pads über dem Feld liegen; Lauf neu: keine Kollision, U3 z 4.10 … 5.70, Pads im Feld. | behoben |
| P5-M5 | klein | Gateway-Deckel G1 v4: Splitter 0.07 mm³ (0.01 mm dick, z 14.15) als 2. Körper in `deckel_blau`. | Körper < 1 mm³ im Generator entfernt, Prüfung 12 in `check_gateway_pi.txt`. | behoben |
| P5-M6 | klein | Register/Doku nannten noch Schraube M2 × 4 (INDEX MECH-SCR1, PRINT_SETTINGS Kap. 4, FMEA F-20). | INDEX-Zeile „MECH-SCR1 (Rev C) M2 × 3“, PRINT_SETTINGS korrigiert; FMEA F-20 durch Sicherheit nachführen. | teilweise (FMEA offen) |

Folgen von P5-M1/M3: Kappe 4145.9 → 4434.0 mm³ (+0.31 g, Sensor 28.2 g). Kleinster Abstand Kunststoff ↔ Antennenkupfer
0.76 → **0.70 mm** (Mantel über dem Speisepunkt, 0.7 mm über der Kupferoberkante) – Bestätigung durch `elektronik`
nötig (RSSI/S11, bereits PROTOTYP-PRÜFUNG). Kollision mit dem KiCad-STEP: **keine**, Einschieben der Platine und Abziehen
der Hülse frei (`mechanical/sensor/collision_pcb_step.txt`). FEM: Kappe ist nicht Teil des Sondenmodells; die Masse
geht nur in die Fall-Schranke ein: 201.3 MPa × √(28.2/27.9) ≈ 202 MPa, SF 1.71 → 1.70 (unverändert „PROTOTYP-PRÜFUNG“).

## B Checkliste Anforderungen

| Punkt | Anforderung | Nachweis / Datei | Status |
|---|---|---|---|
| Sondenlänge ≈ 100 mm, Spitze, Markierung Stecktiefe | REQ-MECH-01 | Spitze z −105, Markierung z −5 → 100 mm (`PCB_OUTLINE.md` Kap. 2, FL-S-00) | ok |
| Kopfgrösse | REQ-MECH-02 (Soll) | 34 × 13 × 57.5 (D-019, Auftraggeber); Höhe über Erde 62.5 > 45 Zielwert | ok (abweichend nach D-019) |
| Kein freiliegendes Metall Sonde | REQ-MECH-03 | Aussenlagen Sonde ohne Kupfer (Z7), Schraube/Mutter im Kopf | ok |
| Kupfer ≥ 1.0 zur Kontur, keine Vias nass | REQ-MECH-05/06 | Zonen Z6/Z7 (`PCB_OUTLINE.md`), DRC (Elektronik) | ok (Elektronik) |
| Sonde versiegelt, Verfahren mit Anleitung | REQ-MECH-07 | Verfahren nicht gewählt (Red-Team W-5) | **offen** |
| Dichtlinie, kein Kriechwasser | REQ-MECH-08 | Kragenverguss z 1.3 … 6.6, Dichtstreifen kupfer-/vialos (K-1), MONTAGE Kap. 5; Vergussmasse Typ offen (EP-K) | **offen** (Masse) / PROTOTYP-PRÜFUNG M-W4 |
| Robustheit Sonde SF ≥ 2 | REQ-MECH-10 | `simulation/fem/REPORT.md` Kap. 5: LC1 SF 2.31, Knicken 238 N, Zug SF 250; LC1b 1.97, Fall obere Schranke 1.70 | ok (FEM) / PROTOTYP-PRÜFUNG M-F1, M-F2 |
| FDM, ASA, HDT ≥ 80 °C | REQ-MECH-12 | `PRINT_SETTINGS.md` Kap. 1 (HDT 92 °C, TDS V2.0); Fenster PETG nur mit Nachweis | ok |
| Druckbarkeit ohne Stützen | REQ-MECH-12 | PRINT_SETTINGS Kap. 3; P5-M1 behoben (Trichter 45°); Körperzahl je Teil = 1 (`check_sensor.txt` 11, `check_gateway_pi.txt` 12) | ok / PROTOTYP-PRÜFUNG M-D1 |
| Spritzwasser Kopf, mit Zelle | REQ-MECH-13 | Dachziegel-Fuge, Ablaufstufe + 4 Schlitze, O-Ringe, Membran (P5-M3 behoben), Fenster geklebt | PROTOTYP-PRÜFUNG M-W1 |
| Sonde dauerhaft nass | REQ-MECH-14 | 30-Tage-Test | PROTOTYP-PRÜFUNG |
| Batteriefach dicht, ohne Spezialwerkzeug, Wechsel ohne Lösen der Sondendichtung | REQ-MECH-15 | PH1-Schraube, 2 radiale O-Ringe AS568-019 (Verpressung 15–33 %, Nutfüllung 77 %, `check_sensor.txt` 7); Kragen bleibt beim Wechsel unberührt; `BATTERIEWECHSEL.md` | ok / PROTOTYP-PRÜFUNG M-W2, M-B1 |
| Logo/Name Gehäuse | REQ-MECH-16 | Logo-Relief 0.25 Hülse (FL-S-01), Gateway-Front | ok |
| Standfestigkeit | REQ-MECH-17 (Soll) | 28.2 g, Schwerpunkt im Kopf | PROTOTYP-PRÜFUNG M-S1 |
| Kein Kondensat | REQ-MECH-18 (Soll) | – | PROTOTYP-PRÜFUNG |
| Fach getrennt vom Elektronikraum und Sondenübergang | REQ-SAF-05, S3-K1/K2 | Schott-Verguss + Schottkeil, Kragenverguss; Kappe jetzt einteilig (P5-M1), Senkung dicht (P5-M3) | ok (CAD) / PROTOTYP-PRÜFUNG (ST-W2/W3) |
| Test-/Programmierpads im abgedichteten Raum, Zugang Adapter | REQ-SAF-06, REQ-FW-06, PS-W1…W3 | TP1/TP2 im Fach; Federstiftkopf nur Konzept (`hardware/programmer/README.md` Kap. 4), **Federstift-Datenblatt fehlt** (INDEX P-J3) | **offen** |
| Sicherer Halter, Zelle fällt nicht heraus | REQ-SAF-CC-02, S3-W2 | Clip 3034 gedreht, Ausschub +x, in der Hülse 2.4 mm bis Wand (`check_sensor.txt` 4) | PROTOTYP-PRÜFUNG M-F2, M-B2 |
| Verschluckschutz, Warnsymbol | REQ-SAF-CC-04, S3-W1/W4 | unverlierbare Schraube M2 × 3 (Furchlippe), 3.5 Gänge; Warnsymbol innen vertieft (FL-S-01) | ok (CAD) / PROTOTYP-PRÜFUNG (ST-K1…K7) |
| Zelltemperatur 65 °C | REQ-SAF-CC-05 | Elektronik/Sicherheit | – (nicht Mechanik) |
| Kraftfluss nicht über die Zelle | REQ-SAF-LI-05 sinngemäss | Taste → Zunge → SW1; Einstecken → Kappe/Schott/Platine (`phase3_sleeve_mechanik.md`) | PROTOTYP-PRÜFUNG M-T2 |
| Antenne oben, kein Metall | REQ-RF-04 | Metall ≥ 17 mm von der Antenne, Kunststoff ≥ 0.70 mm (`check_sensor.txt` 6) | ok / Bestätigung `elektronik` (0.70 statt 0.76) |
| Eine LED, ein Taster; LED sichtbar, Taster mit einem Finger | REQ-UI-01/05 | Tropfenfenster d = 2.0 mm zur LED; Taste 9 × 6, Hub 0.8, Mechanik P5-M2 (`check_sensor.txt` 2a–2c) | ok (CAD) / PROTOTYP-PRÜFUNG M-T1 |
| Keine Fehlbetätigung durch Giesswasser | REQ-UI-06 | Taste in Tasche (Spalt 0.4, 0.6 über Oberseite), Silikonmembran | PROTOTYP-PRÜFUNG M-T3 |
| Gateway-Gehäuse druckbar, passend | REQ-GW-08 | `check_gateway_pi.txt` (keine Kollision, 1 Körper je Teil), FL-G-01…03; Pi-Höhen ANNAHME | ok (CAD) / PROTOTYP-PRÜFUNG M-G1 |
| Fertigungsdaten per Skript | REQ-FAB-08 | Generatoren `mechanical/gen/*.py`, Zeichnungen `fluidi_drawings.py` | ok |
| Fertigungszeichnungen mit Bemassung | Auftrag Phase 5 | `mechanical/drawings/FL-S-00 … FL-S-10, FL-G-01 … FL-G-03` (14 Blätter); 170 Masse/Hinweise, jeder Messpunkt auf der Geometrie (`drawings_check.txt`, 0 Fehler) | ok |
| Montage-/Verguss-/Batteriewechselanleitung | REQ-DOC-02, REQ-SAF-DOC-01, FMEA F-21/F-22/F-23 | `docs/manuals/MONTAGE_SENSOR.md`, `docs/manuals/BATTERIEWECHSEL.md` | ok (Inhalt), Vergussmasse offen |
| Testplan mechanisch | REQ-DOC-03 | `docs/reviews/phase5_testplan_beitrag_mechanik.md` | ok |

## C Prüfvorschlag für den zweiten Agenten

1. `freecadcmd mechanical/gen/fluidi_sensor.py` und `fluidi_pcb_collision.py` neu laufen lassen; `check_sensor.txt`
   Punkte 11 und 12, `collision_pcb_step.txt` Kap. C/K/L.
2. Selbst zählen: `Part.read('mechanical/sensor/print/kappe_blau.step').Solids` → 1. Mit dem Stand `b77b29a` → 2.
3. Trichter auf Druckbarkeit (45°, kopfüber) und Zungenfreiheit prüfen (Schnitt C–C in FL-S-02).
4. Drei Masse je Zeichnung mit dem Messschieber-Ersatz im CAD nachmessen (distToShape) – `drawings_check.txt` enthält
   die Messpunkte.
