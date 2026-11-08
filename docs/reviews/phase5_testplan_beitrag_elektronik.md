# Phase 5 – Testplan-Beitrag Elektronik (Sensor Rev C, Inbetriebnahme Muster)

| | |
|---|---|
| Verfasser | Elektronik-Agent |
| Datum | 2026-11-08 |
| Gegenstand | Sensor Rev C, 5 Muster (JLC, Economic PCBA, ENIG, POFV), noch **ohne** Verguss und Gehäuse, Firmware nach T-P1 |
| Grundlagen | `docs/requirements/REQUIREMENTS.md` v1.1, `docs/interfaces/PINMAP_SENSOR.md`, `hardware/sensor/out/LAYOUT_REV_B.md` (Rev C), `docs/manuals/PROGRAMMIEREN_SENSOR.md`, `docs/manuals/ENERGIEMESSUNG.md` (E1–E15), `docs/reviews/phase4_zusammenfassung.md` Kap. 6 |
| Abgrenzung | Sicherheitstests (Verpolung 24 h, Kurzschluss, Flutung, Verschluckschutz) stehen in `phase5_testplan_beitrag_sicherheit.md` (ST-…), Energie- und Firmwaretests in `phase5_testplan_beitrag_firmware.md` (E…, T-…). Hier: elektrische Inbetriebnahme in fester Reihenfolge und die elektronischen PROTOTYP-PRÜFUNGEN; wo ein Test dort schon definiert ist, wird er referenziert und nicht doppelt beschrieben. |
| Ablage | Protokoll je Muster (Nr. 1–5, Datum, Temperatur, Messmittel, Messwert, OK/NOK, Foto) unter `docs/reviews/phase5_inbetriebnahme/` |

**Grundregel (R2-A2, REQ-SAF-CC-03):** Fremdspeisung nur über die Dummy-Scheibe bzw. den Dummy-Zellen-Adapter in der
Zellposition **ohne Zelle**, Strombegrenzung ≤ 10 mA (bei Programmierung ≤ 20 mA). Nie eine Quelle in Serie zu einer
echten Zelle, nie Speisung über TP1/TP2. Abbruch bei Erwärmung, Geruch oder Strom an der Begrenzung.

## 1 Messmittel

Rahmen: Werkstatt vorhanden, **keine Anschaffung ≥ 100 CHF** (RB-08). Dass die folgenden Geräte vorhanden sind, ist eine
**ANNAHME** (Auftraggeber bestätigt, gleich wie Firmware-Beitrag Kap. 1).

| Mittel | Zweck | Mindestanforderung |
|---|---|---|
| Labornetzteil mit einstellbarer Strombegrenzung | Speisung über Dummy-Scheibe | 0–3.3 V, Begrenzung 1–20 mA einstellbar |
| Digitalmultimeter (DMM) | Widerstand, Spannung, µA über Shunt | Bereich 200 mV mit 0.1 mV Auflösung (1 kΩ-Shunt: 0.1 µA) |
| Shunts 1 Ω, 10 Ω, 1 kΩ (1 %), Kurzschlussbrücke | Ruhe- und Ereignisstrom | wie ENERGIEMESSUNG Aufbau A/C |
| Oszilloskop mit Frequenzmessung, Tastkopf 10:1 | MEAS_CLK, I²C-Flanken, Einbruch | ≥ 20 MHz Bandbreite (MEAS_CLK ≤ 4.6 MHz Grundwelle, Kap. 3.6) |
| Federstift (Pogo) oder feine Messspitze, Lupe ≥ 10× | TP4/TP5 auf B, Sichtprüfung | – |
| Referenzthermometer (Thermoelement oder geeichtes Digitalthermometer) | Temperatursensor | Unsicherheit ≤ ±0.3 °C (**ANNAHME**, damit ±1 °C prüfbar ist) |
| Gateway (Pi Zero 2 W) mit Log, Handy mit BLE-Scanner-App | RSSI, Funktion | – |
| Becher 500 ml, Leitungswasser, trockenes Substrat | Oszillator trocken/nass | – |

## 2 Messpunkte (Lage aus der Platine, pcbnew, Koordinaten X/Y in mm ab Hilfsursprung Mitte Oberkante, Y nach unten)

Plan: `hardware/sensor/out/pdf/fluidi_sensor_masszeichnung.pdf` Blatt 2 (Höhenzonen, TP) und Blatt 3 (Bestückung 5:1).

| Messpunkt | Netz | Seite | X / Y | Zugang / Bemerkung |
|---|---|---|---|---|
| BT1 Clip-Pad oben (Via-in-Pad) | /VBAT | F | 3.00 / 23.89 | unter dem Clip, Messung an der Clip-Lasche; Clip-Pad unten 3.00 / 45.72 |
| BT1 Minuspad (Via-in-Pad) | GND | F | 3.00 / 34.80 | Bezug für alle Messungen; auch Adapter-GND (A-1, TP3 entfällt) |
| C1 Pad 1 / Pad 2 | VDD / GND | F | −11.82 / 19.20 ; −8.88 / 19.20 | VDD hinter dem Verpolschutz Q1 |
| Q1 Pad 3 / 2 / 1 | VBAT / VDD / GND (= Gate) | F | −10.95 / 6.96 ; −10.00 / 8.84 ; −11.90 / 8.84 | Spannungsabfall Verpolschutz |
| C21 Pad 1 | /OSC_PWR | F | −3.08 / 14.58 | Messkette ein/aus (Q2) |
| TP4 | /MEAS_CLK (f_osc / 8) | **B** | −8.00 / 13.60 | Pad Ø 1.0; Frequenzmessung |
| TP5 | /PROBE_SENSE | **B** | −2.30 / 17.90 | Pad Ø 1.0; nur VNA/hochohmig, Tastkopf verstimmt die Messung (≈ 10 pF ≈ Knoten 9.9 pF) |
| TP1 / TP2 | /UART_TX_PAD / /UART_RX_PAD | F | −10.60 / 25.50 ; −10.60 / 28.50 | nur Programmierung (D-024), keine Quelle |
| R9 Pad 1 | /LED_R_UART_TX (DIO6) | F | −0.71 / 11.95 | nur Behelf Weg B (Draht, vor Zelle entfernen) |
| R4 Pad 2 / R5 Pad 2 | /I2C_SDA / /I2C_SCL | F | −1.79 / 18.60 ; −1.79 / 19.65 | I²C-Flanken an den Pull-ups |
| R4 Pad 1 | /SENS_PWR | F | −2.81 / 18.60 | Speisung TMP1075N (DIO12) |
| SW1 Pad 1 | /BTN_BOOT_N (DIO21) | F | −8.22 / 8.40 | Taster, low = gedrückt |
| D1 Pad 1 / 2 / 3 / 4 | VDD / R_K / G_K / B_K | F | 0.6 / 9.1 ; 0.6 / 10.1 ; −0.6 / 10.1 ; −0.6 / 9.1 | LED, Kathoden über R6/R7/R8 |

## 3 Inbetriebnahme Schritt für Schritt (jedes Muster, Reihenfolge verbindlich)

### 3.1 Sichtprüfung (ohne Speisung)

| ID | Prüfung | Abnahme | Quelle |
|---|---|---|---|
| EI-1 | Lage/Pin 1 von U1, U2, U3, U4–U6, Q1, Q2, D1, Y1, SW1, BT1 gegen Masszeichnung Blatt 3 (Pad 1 rot) und Bestückungsplan | alle richtig; Abweichung → Muster sperren | B-3 (ORDER Kap. 2), LAYOUT Kap. 8 |
| EI-2 | Lötbrücken U3 (Pad–Pad 0.20 mm), U1 (QFN), SC-70 | keine Brücke (Lupe ≥ 10×) | K-1/K-6, LAYOUT Kap. 10 |
| EI-3 | 4 Via-in-Pad im Fach (VBAT, Minus, TP1, TP2) | eben, keine Öffnung | **ST-E1** (A-3) |
| EI-4 | DNP C19, C20 unbestückt; Silkscreen „rev C“, Stecktiefenlinie | wie Plan | REQ-MECH-16, REQ-MECH-01 |

### 3.2 Kurzschlussmessung vor der ersten Speisung

| ID | Messung (DMM, ohne Zelle) | Abnahme | Begründung |
|---|---|---|---|
| EI-5 | VDD–GND an C1 (beide Polungen) | Anzeige steigt beim Laden von 4 × 100 µF; nach ≥ 10 s **> 1 kΩ** (**ANNAHME**-Grenze); < 10 Ω = Kurzschluss → sperren | C1–C4 direkt auf VDD |
| EI-6 | VBAT (Clip-Pad) – GND (Minuspad) | wie EI-5. Plus an VBAT: über die Body-Diode von Q1 (D → S) werden C1–C4 mitgeladen, der Wert steigt langsam; Minus an VBAT: hochohmig sofort | Q1 G = GND, S = VDD, D = VBAT (Platine Pad 1/2/3) |
| EI-7 | VBAT–VDD (Diodenprüfung, Plus an VBAT) | Durchlass einer Diode (Body-Diode Q1), Gegenrichtung sperrt | Verpolschutz-Topologie |
| EI-8 | TP1–GND, TP2–GND | ≥ 200 kΩ + Pinwiderstand (2 × 100 kΩ in Serie) | Barriere R2-A3 |
| EI-9 | Isolation VBAT–GND, TX/RX–GND mit 3 V | Wert protokollieren (Referenz für Flutung) | **ST-E3** (A-4) |

### 3.3 Erste Speisung strombegrenzt

| ID | Schritt | Abnahme | Quelle |
|---|---|---|---|
| EI-10 | Netzteil 3.0 V, Begrenzung **10 mA**, über Dummy-Scheibe; Strom beim Einschalten und nach 10 s ablesen | Begrenzung nicht erreicht; kein Bauteil warm (Finger/Thermometer). Unprogrammiert ist der Strom unbekannt (ROM-Bootloader, W-10) → Wert protokollieren | **ST-E2**; W-10 |
| EI-11 | VDD an C1, Spannungsabfall VBAT–VDD an Q1 | VDD ≈ VBAT; Abfall über Q1 mit RDS(on) < 85 mΩ bei −2.5 V (`AOS_AO3401A_Datasheet_Rev3.1.pdf` S.2) bei mA-Strömen < 5 mV | Verpolschutz leitet |
| EI-12 | **Verpolschutz kurz:** gleiche Speisung verpolt (Minus an Clip-Pad), 10 s | Strom ≤ 1 µA (Bereich µA über 1 kΩ-Shunt), keine Erwärmung, danach normaler Start | **ST-E2**; Dauertest 24 h mit Zelle = **ST-Z1** (REQ-SAF-CC-01, ≤ 5 µA) |
| EI-13 | Programmieren (Behelf Weg B, 2.0 V, ≤ 20 mA) | Programmieren + Verifizieren OK, Neustart zeigt L11 | **T-P1**, D-024, `PROGRAMMIEREN_SENSOR.md` |
| EI-14 | **Bootloader-Strom (W-10)**: Taster beim Einschalten gehalten, Strom über 60 s mitteln, bei 3.0 V und 2.0 V | Wert in PROGRAMMIEREN_SENSOR Kap. 6 eintragen; nach ≥ 10 s ohne Speisung startet das Muster ohne Taster mit L11 | **E15** (Firmware-Beitrag 2.2) |

### 3.4 Ruhestrom und Leckstrom C1–C4

| ID | Schritt | Abnahme | Quelle |
|---|---|---|---|
| EI-15 | Ruhestrom ungekoppelt 3.0 V, 25 °C, Shunt 1 kΩ (1 mV = 1 µA), nach ≥ 1 h | **≤ 3 µA** (Muss), Erwartung ≤ 1.5 µA; > 10 µA → Pin-Zustände prüfen (FW-6/FW-8) | REQ-ENE-09, **E1** |
| EI-16 | **Leckstrom C1–C4 (W-6):** E14a–c nach Firmware-Beitrag Kap. 2.1 (2 Muster: C3/C4 ablöten, Einzelmessung 25/50 °C) | I_eff max ≤ 1.24 µA → 4 × 100 µF; 1.24–2.49 µA → 2 × 100 µF nur wenn EI-17 ≤ 0.2 V; > 2.49 µA → Auftraggeber | **E14**, `phase5_energiebudget_final.md` Kap. 5 (REQ-ENE-02 pessDS) |
| EI-17 | Einbruch bei Advertising/Messung/LED über R_int 100 Ω, 4 und 2 × 100 µF | ≤ 0.2 V | REQ-ENE-06, **E3/E5/E6** |

### 3.5 Takt und Versorgung der Messkette

| ID | Schritt | Abnahme | Quelle |
|---|---|---|---|
| EI-18 | OSC_PWR an C21 während eines Messbursts (Oszilloskop, Trigger auf OSC_PWR) | steigt nach DIO11 low; Ladezeit bis 90 % ≤ 50 µs (FW-2 Wartezeit, **ANNAHME** – Messwert ersetzt sie); im Schlaf 0 V | PINMAP FW-2/FW-8 |
| EI-19 | 32-kHz-Quarz: Gangabweichung der Sensorzeit gegen Gateway über ≥ 24 h | ≤ 99 ppm (= ±2 min in 14 Tagen) | REQ-SYS-07; LAYOUT Kap. 10 |

### 3.6 Oszillatorfrequenz trocken / nass (TP4 = f_osc / 8)

Firmware im Testmodus mit Dauer-Burst ist **nicht** zulässig (FW-2: Burst ≤ 0.6 ms). Gemessen wird deshalb mit dem
Oszilloskop im Einzeltrigger auf TP4 während der regulären Bursts (Frequenz aus ≥ 10 Perioden) **und** über den Rohwert
in der PWA/`GET_INFO` (f0 und f1). TP4 trägt nur den Teilerausgang; der Tastkopf belastet PROBE_SENSE nicht.

| ID | Zustand (VDD 3.0 V, 22 ± 3 °C) | Erwartung f_osc typ (Bereich über Ecken, R3 1 kΩ), MEAS_CLK = f/8 | Abnahme |
|---|---|---|---|
| EI-20 | Luft, Sonde frei hängend, ≥ 10 cm zu Gegenständen | f_osc 27.72 MHz (20.47–36.44), MEAS_CLK 3.47 MHz (2.56–4.55) | im Bereich; Rohwert = Trockenpunkt-Referenz |
| EI-21 | trockenes Substrat (Becher) bis Stecktiefenlinie | f_osc 24.47 MHz (18.19–32.01), MEAS_CLK 3.06 MHz (2.27–4.00) | im Bereich, < Luft |
| EI-22 | Leitungswasser bis Stecktiefenlinie | f_osc 9.80 MHz (7.11–12.99), MEAS_CLK 1.23 MHz (0.89–1.62) | im Bereich, deutlich < trocken |
| EI-23 | wie EI-20…22 bei VDD 2.4 V und mit Cref1 (f1) | Rohwerte protokollieren | Ratiometrie: Abweichung VDD 3.0 → 2.4 V wird mit FW-3 korrigiert (Koeffizient bestimmen) |
| EI-24 | alle Muster EI-20/22 | Streuung protokollieren | REQ-MES-07 (Startkalibrierung ±15 %-Punkte) |

Quelle der Erwartung: `simulation/spice/osc/osc_report.txt` (Neulauf Phase 5) und `simulation/field/REPORT.md` Kap. 11.3.
Plausibilitätsgrenzen der Firmware 0.048–12 MHz am Pin (`firmware/sensor/core/fl_meas.h`). Liegt eine Messung ausserhalb
der Simulation, aber innerhalb der Firmwaregrenzen: Knotenkapazität (Feld-REPORT 11.3, 9.9 pF) und tpd sind die ersten
Verdächtigen (**PROTOTYP-PRÜFUNG** „Frequenzbereich Messkette 4.8–36 MHz am realen Board“, phase4_zusammenfassung Kap. 6).
Messvolumen (Becher mit stufenweiser Füllhöhe, REQ-MES-08) und Salz (REQ-MES-11) folgen im Kalibrier-/Messteil des Testplans.

### 3.7 Funk und Antenne

| ID | Schritt | Abnahme | Quelle |
|---|---|---|---|
| EI-25 | Advertising sichtbar als `fluidi-XXXX` (BLE-Scanner) in 1 m | Name korrekt, RSSI protokollieren | REQ-SYS-08 |
| EI-26 | RSSI am Gateway aus 1 m, 5 m und vom ungünstigsten Platz im Raum (bis ca. 18 m), Platine **mit** Kappe/Gehäuse (Kunststoff verstimmt die IFA) | Linkreserve ≥ 10 dB: RSSI ≥ **−86.5 dBm** bei LE 1M (Empfindlichkeit −96.5 dBm, `TI_CC2340R5_Datasheet_SWRS272F.pdf` S.22 Tab. 7.14; Gateway-Empfänger entsprechend seinem Datenblatt) | REQ-RF-03 (Soll) |
| EI-27 | Bei schwacher Reserve: Pi-Netz abstimmen (R2 0 Ω, C19/C20 DNM), Vergleich ohne Gehäuse | Verbesserung dokumentieren; Werte nur mit Messung (VNA oder RSSI-Vergleich) | LAYOUT Kap. 10, OP-K9 |
| EI-28 | 7-Tage-Test im Raum | ≥ 99 % innert 1 h, 100 % nach Nachlieferung | REQ-RF-02, **T-R1/T-R2** |
| EI-29 | Koexistenz WLAN/BLE am Pi | Paketverlust protokollieren | W-7 (Software/Gateway) |

### 3.8 Temperatursensor

| ID | Schritt | Abnahme | Quelle |
|---|---|---|---|
| EI-30 | I²C-Flanken SDA/SCL an R4/R5 Pad 2 bei 100 kHz | Anstiegszeit Daten ≤ 1000 ns (SCL ≤ 100 kHz), Takt ≤ 300 ns (`TI_TMP1075_Datasheet_SBOS854F.pdf` S.9 Tab. 6.8); Adresse 0x48 antwortet | LAYOUT Kap. 10, PINMAP Pin 7 |
| EI-31 | Sonde bis Stecktiefe in gerührtes Wasserbad bei ≈ 10, 22, 35 °C, Referenzthermometer an der Sonde, Kopf im Schatten, je ≥ 15 min warten | \|T_Sensor − T_Ref\| ≤ **1.0 °C** (Sensor allein ±1 °C −10…60 °C, DS S.7 Tab. 6.6 – der Rest der Kette hat **keine** Reserve; Abweichung über 1 °C → Wärmekopplung Kopf über Guard-Flächen, L-6) | REQ-TMP-01 |
| EI-32 | Wie EI-31 bei 22 °C Wasser, Kopf mit Lampe auf 40–50 °C | Abweichung dokumentieren (REQ-TMP-01 verlangt nur Dokumentation bei Sonne) | REQ-TMP-01, RB-03 |
| EI-33 | Kein I²C während der Messung | Oszilloskop: SDA/SCL statisch low während OSC_PWR hoch | FW-1 |

### 3.9 LED

| ID | Schritt | Abnahme | Quelle |
|---|---|---|---|
| EI-34 | Jede Farbe einzeln (R, G, B) und Muster L1/L3/L8 bei 3.0 V | leuchtet, Pulse ≤ 5 ms, Strom ≤ 3 mA je Farbe | FW-4, **E6** (Firmware-Beitrag) |
| EI-35 | **Sichtbarkeit (E6, D-023 EP-2):** im hellen Büro am Fenster, Betrachter stehend 1–2 m, schräg von oben, Muster mit 5-ms-Pulsen; 3 Personen | jede Farbe von allen erkannt; Blau bei 2.8 V und 2.6 V prüfen (unter 2.65 V Ersatzfarbe, Farbtabelle) | REQ-UI-05; Schwellen „voll ≥ 10 mcd / erkennbar ≥ 3 mcd“ **ANNAHME** (`phase3_rgb_antenne_elektronik.md` Kap. 1.4) |
| EI-36 | Bei schlechter Sichtbarkeit: Vorwiderstände R6/R7/R8 bzw. Pulslänge anpassen | nur mit Nachrechnung Einbruch (EI-17) und LED-Budget ≤ 5 % (REQ-UI-03) | D-023 EP-2 |

### 3.10 Taster

| ID | Schritt | Abnahme | Quelle |
|---|---|---|---|
| EI-37 | Pegel SW1 Pad 1: offen ≈ VDD (interner Pull-up), gedrückt < 0.3 V | Prellen protokollieren (Oszilloskop) | PINMAP Pin 10 |
| EI-38 | kurz / lang (≥ 3 s) / sehr lang (≥ 10 s) | Messung, Pairing, Werkseinstellung | REQ-UI-04, **T-…** Firmware |
| EI-39 | Dauerdruck > 30 s | Pull-up nach 30 s aus, Strom wieder ≈ EI-15 | **E2**, PROTOCOL 10.3 |
| EI-40 | **Tastertoleranz (Worst Case −0.20 mm):** im Gehäuse mit Stössel, Muster mit kleinster und grösster Kappe | auslösen mit einem Finger, kein Dauerdruck im Ruhezustand | REQ-UI-05, M-4 (Mechanik) |

## 4 PROTOTYP-PRÜFUNGEN aus `phase4_zusammenfassung.md` Kap. 6 (Zuordnung)

| Prüfung | Hier | Kriterium / Entscheid |
|---|---|---|
| Leckstrom C1–C4 → 2 oder 4 × 100 µF (W-6, REQ-ENE-02 pessDS) | EI-16 (+ EI-17) | Entscheidungsregel E14 (Firmware-Beitrag 2.1); D-Eintrag vorher |
| Tastertoleranz (Worst Case −0.20 mm) | EI-40 | Mechanik misst, Elektronik prüft Pegel (EI-37) |
| Bootloader-Strom (W-10) | EI-14 | Wert in PROGRAMMIEREN_SENSOR Kap. 6 |
| LED-Sichtbarkeit (E6) | EI-35/36 | alle Farben erkannt, sonst Vorwiderstände/Pulse |
| Koexistenz WLAN/BLE (W-7) | EI-29 | Gateway/Software |
| Frequenzbereich Messkette 4.8–36 MHz am realen Board | EI-20…24 | im Simulationsbereich, innerhalb Firmwaregrenzen |

Weitere elektronische PROTOTYP-PRÜFUNGEN aus `LAYOUT_REV_B.md` Kap. 10: Antenne/Pi-Netz (EI-26/27), 48-MHz-Abgleich
(indirekt über stabile Verbindung EI-28; Frequenzfehler mit Funkmessgerät nur falls vorhanden), 32 kHz (EI-19),
I²C-Flanken (EI-30), VDD-Einbruch (EI-17), Isolationswiderstand (EI-9/ST-W2), Querschliff VIP (ST-E1).

## 5 Reihenfolge und Freigabe für Verguss

1. EI-1…EI-9 an allen 5 Mustern (ohne Speisung). 2. EI-10…EI-14 (erste Speisung, Programmierung).
3. EI-15, EI-18…EI-25, EI-30, EI-34, EI-37…EI-39 am offenen Board. 4. EI-16 an 2 Opfermustern (C3/C4 ablöten).
5. Erst danach Verguss/Gehäuse; dann EI-26…EI-29, EI-31/32, EI-35, EI-40 und die Sicherheits-/Wassertests.

**Freigabe für Verguss je Muster:** EI-1…EI-15 und EI-20/22 bestanden, Behelf-Draht an R9 entfernt (PROGRAMMIEREN Kap. 5).
