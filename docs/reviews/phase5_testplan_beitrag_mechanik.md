# Phase 5 – Testplan-Beitrag Mechanik (REQ-DOC-03)

| | |
|---|---|
| Verfasser | Mechanik-Agent, 2026-11-08 |
| Gegenstand | Sensor P3 V4 (Rev C, V-K/M-4, P5-M1/M3), Gateway G1 v4; Zeichnungen `mechanical/drawings/` |
| Abgrenzung | Sicherheitstests (Verschluckschutz ST-K*, Flutung ST-W2/W3, Kurzschluss ST-Z*) stehen in `phase5_testplan_beitrag_sicherheit.md`; hier nur Querverweise. Alle Tests sind **PROTOTYP-PRÜFUNG**. |
| Muster | mind. 3 Sensoren (M1–M3) + 1 Opfermuster (M0) für zerstörende Prüfungen; Druckteile aus einer Charge ASA |
| Messmittel | Messschieber 0.01, Fühlerlehren 0.05–0.5, Lupe ≥ 10×, Federwaage/Kraftmesser 0–100 N, Drehmomentschrauber 0.1–1 Nm (für ST-K1), Waage 0.01 g, Giesskanne 1 l, Massstab, Wärmeschrank 65 °C, Feuchteindikator-Papier |

## 1 Druckteile und Passung

| ID | Testfall | Methode | Mittel | Abnahmekriterium | Quelle |
|---|---|---|---|---|---|
| M-D1 | Druckbarkeit, Körperzahl | alle Teile nach PRINT_SETTINGS drucken, Sichtprüfung; Kappe: Zapfen fest mit Kappe, Trichter 45° ohne Durchhang | Lupe | jedes Teil 1 Körper, keine Fehlstellen an Nuten, Brücken, Zunge | `check_sensor.txt` 11, P5-M1 |
| M-D2 | Prüfmasse | gerahmte Masse der Zeichnungen messen (je Teil alle Prüfmasse) | Messschieber | Nennmass ± 0.1 (Allgemeintoleranz Zeichnung, ANNAHME FDM) | FL-S-01 … FL-G-03, Hinweis 2 |
| M-D3 | Passprobe Hülse unten/oben | `passprobe_huelse_unten` + Kragen + O-Ring, `…_oben` + Kappe + O-Ring | Hand, Silikonfett | gleitet ohne Klemmen, O-Ring sichtbar verpresst; sonst XY-Lochkompensation anpassen | PRINT_SETTINGS Kap. 4 |
| M-D4 | O-Ring-Verpressung | Einbauraum radial an 4 Stellen messen (Hülse innen − Nutgrund) / 2 | Messschieber | 1.25 … 1.45 → Verpressung 15–33 % mit Schnur 1.78 ± 0.08 | `check_sensor.txt` 7, `GTWeed_AS568_StandardOringSizing.pdf` S. 2 |
| M-D5 | Furchlippe / Schraube | Schraube M2 × 3 erstmals eindrehen, lösen, Hülse abziehen | PH1 | Schraube furcht, bleibt danach in der Hülse (fällt bei Hülse kopfüber nicht heraus) | S3-W1, UL 4200A 5.6 (`phase3_sleeve_sicherheit.md`) |
| M-D6 | Lage Platine | nach Einschieben: Oberkante am Anschlag, F an Gabel/Schottkeil | Fühlerlehre 0.05 | Spalt Anschlag 0; Spalt Zunge–SW1 0.25 (−0.30/+0.30, RSS ≥ 0.08) | PCB_OUTLINE Kap. 2/6, `check_sensor.txt` 2b |
| M-D7 | Kragenlage | nach Verguss Abstand Kragen-Oberkante ↔ Schott-Unterkante, 2 Seiten | Messschieber | 24.2 ± 0.1 → Clip-Pads ≥ 0.30 zu beiden Vergusskanten | D-023 V-K, LS-W1 |

## 2 Taster

| ID | Testfall | Methode | Mittel | Abnahmekriterium | Quelle |
|---|---|---|---|---|---|
| M-T1 | Schaltfunktion | Taste mittig und an den 4 Ecken drücken, je 20 × | LED/Firmware-Rückmeldung, Kraftmesser | jede Betätigung erkannt; Betätigungskraft ≤ 5 N (**ANNAHME** Bedienbarkeit, REQ-UI-05) | REQ-UI-04/05; Soll aus CAD: Schaltpunkt ≈ 0.4 mm Hub, Kraft ≈ 4.7 N + Membran (`check_sensor.txt` 2a/2c) |
| M-T2 | Kraftfluss, Überlast | 100 × mit 20 N (**ANNAHME** Fehlbedienung) drücken, danach Sicht auf Zunge/Nase/Finger, SW1 und Lötstellen | Kraftmesser, Lupe | kein Weissbruch an Zunge (Schichtgrenzen!), SW1 schaltet weiter, Zelle unbelastet | M-4, `check_sensor.txt` 2b (Überhub 0.45), ST-M2 |
| M-T3 | Fehlbetätigung Giesswasser | während M-W1 Tasterereignisse protokollieren | Firmware-Log | kein Tastenereignis durch Wasser, keine Werkseinstellung | REQ-UI-06 |
| M-T4 | Dauerhaltbarkeit | 1000 Betätigungen (**ANNAHME** Lebensdauer-Stichprobe) | Zähler | Funktion wie M-T1, Membran dicht (danach M-W1) | REQ-UI-05 |

## 3 Dichtigkeit

| ID | Testfall | Methode | Mittel | Abnahmekriterium | Quelle |
|---|---|---|---|---|---|
| M-W1 | Spritzwasser Kopf | 1 l aus 20 cm über den Kopf, 10 Wiederholungen, **mit Zelle**; Feuchteindikator im Fach und (Opfermuster) im Elektronikraum | Giesskanne, Indikator | kein Wasser/Kondensat in Fach und Elektronikraum; Ablauf aus den 4 Schlitzen beobachtet | REQ-MECH-13 (= ST-W1) |
| M-W2 | Spritzwasser nach Wechseln | M-W1 nach 10 Batteriewechseln (M-B1) | wie M-W1 | wie M-W1 | S3-W3 |
| M-W3 | Membran/Senkung | Opfermuster M0: Kappe mit Taste, 5 mm Wassersäule über der Taste 1 h, Innenraum mit Indikator | Indikator | trocken (Nachweis P5-M3) | REQ-MECH-13, P5-M3 |
| M-W4 | Kragen / Sondenübergang | Kragen bis z +3 tauchen 24 h, nach 50 Zyklen −10/+65 °C; M0: Schliff durch den Kragen | Indikator, Säge, Lupe | trocken; keine Lunker, keine Ablösung an Platine/Tasche | REQ-MECH-08, K-7 (= ST-W4) |
| M-W5 | Fenster-Klebung | 65 °C / 7 d, danach M-W1 | Wärmeschrank | keine Verformung, dicht | REQ-MECH-12 (PETG-Nachweis), PRINT_SETTINGS Kap. 1 |

## 4 Fall und Robustheit

| ID | Testfall | Methode | Mittel | Abnahmekriterium | Quelle |
|---|---|---|---|---|---|
| M-F1 | Fall 1 m | mit Zelle auf harten Boden: Kopf voran, flach, seitlich auf die Spitze; je 3 × an M1–M3 | Massstab, Zellstrom vor/nach | kein Bruch, Sonde ohne bleibende Verformung, Fach geschlossen, Zelle im Clip, Funktion ok | REQ-MECH-10, REQ-SAF-CC-02/04 (= ST-M3); FEM-Schranke SF 1.70 |
| M-F2 | Seitlast / Zug / Einstecken | 10 N seitlich an der Spitze, 30 N Zug am Kopf, 50 N axial mit geführter Spitze | Kraftmesser | keine bleibende Verformung (< 0.5 mm an der Spitze, **ANNAHME**), keine Risse am Kragen | REQ-MECH-10, D-016, `simulation/fem/REPORT.md` Kap. 5 (= ST-M1) |
| M-S1 | Standfestigkeit | Sensor in lockerem Granulat und in Erde, 24 h | Winkelmesser | keine Neigung > 10° (**ANNAHME**) | REQ-MECH-17 |

## 5 Batteriewechsel

| ID | Testfall | Methode | Mittel | Abnahmekriterium | Quelle |
|---|---|---|---|---|---|
| M-B1 | Wechsel nach Anleitung | `BATTERIEWECHSEL.md` von einer Person ohne Vorwissen | Stoppuhr | ≤ 5 min, ohne Spezialwerkzeug (PH1), Kragenverguss unberührt, L11 sichtbar | REQ-MECH-15, REQ-FAB-03 (sinngemäss) |
| M-B2 | Zelle hält beim Abziehen | Hülse ab, Sensor kopfüber, schütteln | – | Zelle bleibt im Clip | S3-W2 (= ST-K5) |
| M-B3 | 50 Wechsel | Standardablauf | Lupe | Clip-Lötstellen ohne Riss, O-Ringe ohne Schnitt, Schraube unverlierbar, Gewinde fasst (Hülse von Hand nicht abziehbar) | K-4, F-24 (= ST-K6) |
| M-B4 | Hülse ohne Schraube | Hülse nur aufgeschoben, Sensor schütteln und stecken | – | Ergebnis protokollieren (fällt/hält), Anleitung anpassen | F-21 (= ST-K4) |
| M-B5 | Programmieradapter | Dummy einsetzen, Stifte auf TP1/TP2, Gegenhalter | Lupe | PS-W1 a–d; VIP-Pads ohne Abdruck; Dummy 3.0–3.2 mm | PS-W1…W3 (= ST-P1) |

## 6 Gateway G1 v4

| ID | Testfall | Methode | Mittel | Abnahmekriterium | Quelle |
|---|---|---|---|---|---|
| M-G1 | Passung Pi | Pi-Höhen vorab messen (PRINT_SETTINGS Kap. 3), Pi einlegen, Deckel senkrecht aufsetzen, 4 × M2.5 | Messschieber | Stecker PWR/OTG steckbar (Spiel 0.4), microSD zugänglich nach Lösen, kein Klemmen | `check_gateway_pi.txt` 2/4/10, ANNAHMEN Kopf `fluidi_gateway_pi.py` |
| M-G2 | Wärme | Dauerbetrieb 24 h, Gehäuse-Oberfläche messen | Thermometer | Gehäuse ≤ HDT − 10 K (≤ 82 °C) | REQ-MECH-12/SAF-01 sinngemäss, `check_gateway_pi.txt` 8 |
| M-G3 | Funk durch Deckel | RSSI offen/geschlossen | App/Gateway-Log | Verlust protokolliert; Nylonschrauben-Variante bei Bedarf | `check_gateway_pi.txt` 6 |
