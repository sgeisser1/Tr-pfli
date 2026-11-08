# Phase 5 – Testplan Prototyp (konsolidiert, REQ-DOC-03)

| | |
|---|---|
| Dokument | `docs/reviews/phase5_testplan_prototyp.md` |
| Stand | 2026-11-08, Entwurf 2 mit Entscheiden der Projektleitung (Konsolidierung durch Firmware/Energie im Auftrag des Orchestrators) |
| Gegenstand | Sensor Rev C, **5 Muster S1–S5** (JLC Economic PCBA, ENIG, POFV, 4 × 100 µF), Gehäuse P3 V4 (ASA, P1S), Gateway G1 v4 (Pi Zero 2 W), Firmware `fluidi-sensor-0.1.0+1` (DEV-Schlüssel) |
| Quellen (Beiträge) | `phase5_testplan_beitrag_elektronik.md` (EI-…), `phase5_testplan_beitrag_firmware.md` (E…, T-…), `phase5_testplan_beitrag_mechanik.md` (M-…), `phase5_testplan_beitrag_sicherheit.md` (ST-…), `phase5_testplan_beitrag_software.md` (TS-…), `docs/manuals/ENERGIEMESSUNG.md` (E1–E15, Aufbau A–D), `phase4_zusammenfassung.md` Kap. 6 (PROTOTYP-PRÜFUNG), `docs/manuals/PROGRAMMIEREN_SENSOR.md` v1.1 |
| Anforderungen | `docs/requirements/REQUIREMENTS.md` v1.1 (alle REQ-IDs dieses Plans dort vorhanden, per `grep` geprüft) |
| Status | Alle Tests sind **PROTOTYP-PRÜFUNG**. Widersprüche zwischen den Beiträgen sind in Kap. 9 aufgelistet; die **Entscheide der Projektleitung** dazu stehen in Kap. 10 und sind in die Tests eingearbeitet (Entwurf 2). |
| Ablage Ergebnisse | Protokoll je Test und Muster (Datum, Temperatur, FW-Stand `GET_INFO`, SW-Stand `GET /system`, Messmittel, Messwert, OK/NOK, Foto/Log): Elektronik `docs/reviews/phase5_inbetriebnahme/`, Energie `docs/reviews/phase5_energie_messung/`, übrige `docs/reviews/phase5_testprotokolle/` (**ANNAHME** Ordnername) |

## 0 Lesehilfe

- **ID** `PTx.yy`: x = Phase des Ablaufs (Kap. 3), yy = laufende Nummer. Die Ursprungs-IDs der Beiträge stehen in Spalte
  „Ursprung“; zusammengeführte Doppelungen tragen alle Ursprungs-IDs.
- **Muster**: S1–S5 nach Zuteilung Kap. 2, „alle“ = S1–S5, G = Gateway, A = Programmieradapter/Dummy-Scheibe.
- **Entscheidungs-Tests** sind mit **[D-n]** markiert; die Entscheidungsregel steht in Kap. 5.
- **Ergebnis**: je Muster ausfüllen, `OK / NOK / Wert …`; NOK → Abweichung mit Foto/Log und Befundnummer.
- Aufbauten A–D nach `ENERGIEMESSUNG.md` Kap. 1, E = Kondensator-Leck (Firmware-Beitrag Kap. 1).

**Grundregeln (gelten für jeden Test, R2-A2, REQ-SAF-CC-03, REQ-ENE-07, REQ-SAF-06):**
1. Fremdspeisung nur über die Dummy-Scheibe bzw. den Dummy-Zellen-Adapter im Clip **ohne Zelle**, nie eine Quelle in Serie
   zu einer echten Zelle, keine Speisung über TP1/TP2. Einzige Ausnahme: Fehlertest PT11.06 unter den Bedingungen Z5-1…Z5-7
   (`docs/reviews/phase5_sicherheit_runde3.md`, EP-13).
2. Strombegrenzung (EP-03): erste Speisung (unprogrammiert) 10 mA; Programmieren Weg B 2.0 V (höchstens 2.2 V) mit
   **10 mA** (PS-L3); Funktions- und Energietests mit Funk **3.0 V, 30 mA, nur über die Dummy-Scheibe, nie mit Zelle im
   Clip**; PT11.06 ≤ 1 mA (Z5-2).
3. Zellstrom mit echter Zelle nur über den Mess-Zwischenadapter (nur Shunt/Amperemeter).
4. Abbruch bei Erwärmung, Geruch, Rauch, Aufblähen, Strom an der Begrenzung oder > 60 °C an der Zelle (ANNAHME
   Abbruchgrenze, Sicherheits-Beitrag Kopf). Zellen nach Fehlertests und Zellen < 2.6 V entsorgen (PROGRAMMIEREN Kap. 5/6).
5. **Nach jedem Zusammenbau L11 prüfen** (Bootloader-Falle W-10, PROGRAMMIEREN Kap. 6, PS-W5): Zelle einsetzen und Fach
   schliessen, **bevor** Kappe/Taster berührt werden.

## 1 Benötigte Messmittel und Material

Rahmen: Werkstatt gut ausgerüstet, **keine 100 CHF für Messgeräte** (`CLIENT_INPUT.md` Nr. 10). Kein Power-Profiler,
kein µCurrent, kein VNA. Spalte „Status“: **ANNAHME** = vom Auftraggeber zu bestätigen; **Eigenbau** = im Projekt zu
fertigen; **beschaffen** = Kleinmaterial/Verbrauch; **fehlt** = mit Werkstattmitteln nicht abgedeckt, Ersatzmethode nötig.

| Nr | Mittel / Material | Anforderung | Für | Status |
|---|---|---|---|---|
| MM-01 | Labornetzteil mit einstellbarer Strombegrenzung | 0–5 V, Begrenzung **≤ 1 mA** (PT11.06) bis 30 mA einstellbar, Fernfühlung wünschenswert | PT3, PT4, PT6, PT11 | ANNAHME vorhanden |
| MM-02 | Digitalmultimeter mit µA-Bereich und **Aufzeichnung** | 200 mV-Bereich mit 0.1 mV; R_i 10 MΩ (Aufbau E); Logging ≥ 24 h | PT3, PT6, PT8.11 | ANNAHME vorhanden (Aufzeichnung unsicher) |
| MM-03 | Oszilloskop ≥ 2 Kanäle | ≥ 20 MHz, Mittelwert-/Integral-(„Area“-)Funktion, ASCII-Export, Frequenzmessung | PT5, PT6 | ANNAHME vorhanden |
| MM-04 | Tastkopf 10:1 | – | PT5, PT6 | ANNAHME vorhanden |
| MM-05 | Shunts 1 Ω, 10 Ω, 1 kΩ, 100 kΩ (0.1–1 %, Metallfilm), Widerstand 100 Ω (R_int EOL), Kurzschlussbrücke, Kondensator 1000 µF (Aufbau D) | – | PT6, PT8.11 | beschaffen (Kleinteile) |
| MM-06 | **Dummy-Scheibe** (Dummy-Zelle Ø 20, Dicke 3.0–3.2 mm, Unterseite Mittelinsel Ø 8) | `hardware/programmer/README.md` Kap. 4 (PS-W3) | PT3, PT4, PT6 | **Eigenbau** (Pflicht für Weg B, Veto PS-K1) |
| MM-07 | **Mess-Zwischenadapter** in der Zellposition (echte CR2032 + Shunt/Amperemeter, keine Quelle) | ENERGIEMESSUNG „Sicherheit“ | PT8.11, PT10.14, PT11 (ST-Z*, ST-W2, ST-M3) | **fehlt: nicht konstruiert** (keine Zeichnung/Beschreibung im Repo) |
| MM-08 | Waveshare CH343 USB-UART-Board, Kupferlackdraht 0.1–0.2 mm, Kaptonband, Lötstation fein, Isopropanol | PROGRAMMIEREN Kap. 2 | PT4 | beschaffen (Auftraggeber, `phase4_zusammenfassung.md` Kap. 5 Nr. 2) |
| MM-09 | Programmieradapter Rev 1 (Weg A) | ≈ 25–55 CHF (`phase4_zusammenfassung.md` Kap. 5) | PT0.08/09, PT4.01, nach Verguss | optional; ohne ihn nach dem Verguss **keine** Neuprogrammierung ausser OTA |
| MM-10 | Federstift (Pogo) oder feine Messspitze, Lupe/Mikroskop ≥ 10× | – | PT2, PT4, PT5 | ANNAHME vorhanden |
| MM-11 | Referenzthermometer (Thermoelement oder Digitalthermometer) | Unsicherheit ≤ ±0.3 °C (ANNAHME) | PT8.09/10, PT11 | ANNAHME vorhanden (±0.3 °C unsicher) |
| MM-12 | Thermoelement für Zelle/Bauteil | bis 100 °C | PT11 | ANNAHME vorhanden |
| MM-13 | Wärmeschrank 50 °C / 65 °C, ≥ 168 h | Backofen nur mit Thermometer (ANNAHME) | PT6.03, PT6.15, PT10.12, PT11.19 | **ANNAHME** (nicht belegt) |
| MM-14 | Kühlschrank (≈ 8–10 °C), Tiefkühler (−10 °C) | Zyklen −10/+65 °C | PT6.15, PT8.07, PT11.19 | ANNAHME (Haushaltsgeräte) |
| MM-15 | Kraftmesser/Federwaage 0–100 N; für 72 N und 136 N **Gewichte** (z. B. Wasserkanister an Schnur, Masse auf der Waage gewogen: 7.34 kg bzw. 13.86 kg, m = F / 9.81 m/s²) | – | PT8.01, PT10.10, PT11.04/05 | Kraftmesser ANNAHME vorhanden; Gewichte Werkstatt (EP-14) |
| MM-16 | Drehmomentschlüssel | – | – | **entfällt** (EP-14): „handfest“ mit Markierung, ANNAHME bis Anzugsmoment festgelegt |
| MM-17 | Messschieber 0.01, Fühlerlehren 0.05–0.5, Winkelmesser, Massstab, Waage 0.01 g, Stoppuhr, PH1 | – | PT1, PT7, PT10 | ANNAHME vorhanden |
| MM-18 | Feuchteindikator-Papier | – | PT10, PT11, PT12.05 | beschaffen (Verbrauch) |
| MM-19 | CR2032 neu (≥ 3.0 V), 1 × CR2025 | ≈ 30 Stück (**ANNAHME**: Fehlertests verbrauchen je 1 Zelle) | PT8–PT12 | beschaffen |
| MM-20 | Becher 500 ml, Leitungswasser, Salz, Flüssigdünger (übliche Dosierung), Blumenerde, Granulat, Gefrierbeutel, Giesskanne 1 l | – | PT5, PT8, PT10, PT12 | beschaffen/vorhanden |
| MM-21 | Gateway Pi Zero 2 W + geprüftes Netzteil, 2 SD-Karten, Steckdosenleiste mit Schalter | GATEWAY_SETUP | PT0, PT9, PT12 | vorhanden (Pi), SD/Netzteil ANNAHME |
| MM-22 | Handys: Android (Pixel 10) mit BLE-Scanner-App, iPhone (falls verfügbar), Desktop-Browser, PC mit Repo, `nmap` | – | PT0, PT5, PT9, PT11 | Pixel vorhanden; iPhone ANNAHME |
| MM-23 | Zweiter BLE-Sender XIAO nRF52840 | 27.5 s Intervall | PT0.06 | **ANNAHME** (alternativ ein Sensormuster, dann erst nach PT4) |
| MM-24 | USB-Leistungsmessgerät | ≤ 2 W ablesbar | PT12.02 | ANNAHME (günstig, nicht belegt) |
| MM-25 | Pikoamperemeter | – | – | **entfällt** (EP-18): DMM über Shunt, Methode PT3.05 |
| MM-26 | VNA bzw. Funkmessgerät (EI-27, 48-MHz-Abgleich, TP5) | – | PT9.03 | **fehlt**; Ersatz RSSI-Vergleich (EI-27 erlaubt das) |
| MM-27 | Säge/Schleifmittel für Querschliff, Lupe | – | PT11.23/24 | ANNAHME vorhanden |
| MM-28 | Testfirmware (TF-1…TF-4) | Spezifikation **Anhang A** | PT5.12, PT11.07, PT11.19 | **fehlt**; Erstellung Firmware vor Musterankunft (EP-15) |

## 2 Zuteilung der 5 Muster

| Muster | Rolle | Wichtigste Tests | Zerstörend? |
|---|---|---|---|
| **S1** | Referenz Funktion/Energie (4 × 100 µF), danach Feld und 30-Tage-Nasstest | PT5, PT6 (E2–E13), PT8, PT9, PT12.05 | nein |
| **S2** | W-6-Muster A (C3/C4 ab, E14b/c, Einbruch mit 2 × 100 µF), danach Firmware/OTA/Kopplung, Watchdog-Debug-Build | PT6.02–6.04, PT5.12, PT9.12–9.14, PT11.09–11.11 | nein (Nacharbeit C3/C4) |
| **S3** | W-6-Muster B (wie S2), danach Mechanik nicht zerstörend (Taster, Wechsel, Spritzwasser) | PT6.02–6.04, PT8.01, PT10.01–10.07, PT10.09, PT10.14, PT11.03–11.05 | nein (Verschleiss möglich) |
| **S4** | Alterung und Fehlerfälle, die das Muster überleben soll | PT10.10, PT10.12, PT10.14, PT11.06/07, PT11.17, PT11.19 (ohne Schliff) | möglich |
| **S5** | **Opfermuster** (= Mechanik M0, Sicherheit „Opfermuster/Opferplatine“) | PT10.13, PT11.08, PT11.18, PT11.19–11.24 zum Schluss, Querschliff zuletzt | **ja** |

Anmerkungen:
- Zuteilung von der Projektleitung bestätigt, ein Opfermuster S5 (EP-08). Falltest PT10.14 an S3, S4, S5, nicht an
  S1/S2 (EP-07).
- S2/S3: C3/C4 nach PT6.04 wieder bestücken (dieselben Teile nach der Einzelmessung; **ANNAHME** Planung, kein Beitrag
  legt das fest), ausser der W-6-Entscheid fällt auf 2 × 100 µF.
- Alle Muster nehmen an PT12.01 (7-Tage-Reichweite) teil, soweit noch funktionsfähig; deshalb laufen S4/S5-Fehlertests
  **nach** PT12.01 (Zeitplan Kap. 4).
- Weg B (Behelf) ist nur vor dem Verguss möglich. Testfirmware (Anhang A) wird entweder vor dem Verguss per Weg B
  geflasht oder als DEV-signiertes Image per OTA eingespielt (Versionszähler beachten, Anhang A); ohne beides setzt sie
  den Adapter Rev 1 (MM-09) voraus.

## 3 Tests in Ablaufreihenfolge

### Phase 0 – Vorbereitung (vor Eintreffen der Muster)

| ID | Ziel / REQ | Aufbau / Mittel | Durchführung | Abnahme (Quelle) | Muster | Ursprung | Ergebnis |
|---|---|---|---|---|---|---|---|
| PT0.01 | Messmittel tauglich (ENERGIEMESSUNG Kap. 3/4) | MM-01…05 | Shunts nachmessen, Oszilloskop-Nullpunkt, Leerwert Aufbau C ohne Sensor | Shunt ±1 %, Leerwert notiert und später abgezogen (ENERGIEMESSUNG Kap. 4) | – | E-Plan Kap. 3 | |
| PT0.02 | Gateway-Installation, REQ-GW-02/07 | MM-21, GATEWAY_SETUP Kap. 2–4 | SD schreiben, `install_gateway.sh`, Prüfung 4.3, `--finish`, Zeit stoppen | Skript fehlerfrei; Dienst `active`; nach `--finish` Port 22 zu (TS-1) | G | TS-1 | |
| PT0.03 | Anmeldung, Brute Force, REQ-SAF-NET | Browser | Einrichtungscode, Passwort; 10 falsche Passwörter | Sperre ab dem 5. Versuch, Retry-Zeit angezeigt; An-/Abmelden ok (TS-4, ST-N2) | G | TS-4, ST-N2 | |
| PT0.04 | `fluidi.local` (W-9) | Android, iPhone, PC; Heim- und Firmen-WLAN | `https://fluidi.local` aufrufen | Name aufgelöst; sonst Gerät/Netz notieren (TS-2) | G | TS-2 | |
| PT0.05 | HTTPS, PWA, Name Constraint, REQ-SAF-NET-04 | Browser, CA | CA installieren, Fingerabdruck vergleichen, PWA installieren, Flugmodus; Zertifikat für anderen Namen prüfen | kein Zertifikatsfehler; Fingerabdruck gleich; fremder Name abgelehnt; PWA offline startbar (TS-3, ST-N4) | G | TS-3, ST-N4 | |
| PT0.06 | **[D-6] Koexistenz WLAN/BLE Teil 1** (W-7) | Pi im Zielraum, WLAN-Last, XIAO (MM-23) 27.5 s in 18 m, 24 h | `missed_pct` ablesen | P_MISS protokolliert; Regel D-6 (TS-14) | G | TS-14, W-7 | |
| PT0.07 | Dummy-Scheibe: Dicke, Isolation (PS-W3) | Messschieber, DMM | Dicke an 3 Stellen, Isolation Ober-/Unterseite | 3.0–3.2 mm; > 10 MΩ (ST-P2, M-B5) | A | ST-P2, M-B5 | |
| PT0.08 | Adapter Rev 1: Kurzschluss VDD_DUT 60 s (nur falls MM-09 gebaut) | Thermoelement | Dummy-Flächen überbrücken | U1/U2-Temperatur protokolliert, kein Rauch (ST-P3) | A | ST-P3 | |
| PT0.09 | Adapter Rev 1: VIO-Fehler (nur falls MM-09) | Jumper H3 gesteckt, ohne Sensor | Prüfschritt 2 README Kap. 7 | Fehler erkannt (VIO ≠ 2.0 V) (ST-P4) | A | ST-P4 | |
| PT0.10 | Flash-Werkzeug ohne Hardware, REQ-FW-06 | PC/WSL | `test_flash_sensor.py`, `program --sim` | 17 Tests OK, Probelauf OK (PROGRAMMIEREN Kap. 3) | – | PROGRAMMIEREN Kap. 3 | |

### Phase 1 – Wareneingang

| ID | Ziel / REQ | Aufbau / Mittel | Durchführung | Abnahme (Quelle) | Muster | Ursprung | Ergebnis |
|---|---|---|---|---|---|---|---|
| PT1.01 | Lieferung vollständig | Lieferschein, ORDER_JLC_REV_C | Anzahl, Transportschäden, Nummerierung S1–S5 (Silkscreen-nah, wasserfest), Foto beidseitig | 5 Platinen unbeschädigt, Fotos abgelegt (Konsolidierung; Protokollpflicht Elektronik-Beitrag Kopf) | alle | neu (Ablauf) | |
| PT1.02 | Druckteile: Druckbarkeit, Körperzahl | Lupe | alle Teile nach PRINT_SETTINGS; Kappe 1 Körper, Trichter 45° | je Teil 1 Körper, keine Fehlstellen an Nuten/Brücken/Zunge (`check_sensor.txt` 11, P5-M1) | Druckteile | M-D1 | |
| PT1.03 | Prüfmasse Zeichnungen | Messschieber | gerahmte Masse FL-S-01…FL-G-03 | Nennmass ± 0.1 (Allgemeintoleranz, ANNAHME FDM) | Druckteile | M-D2 | |
| PT1.04 | Passprobe Hülse/Kragen/Kappe | Silikonfett | Passproben unten/oben mit O-Ring | gleitet ohne Klemmen, O-Ring verpresst (PRINT_SETTINGS Kap. 4) | Druckteile | M-D3 | |
| PT1.05 | O-Ring-Verpressung | Messschieber | Einbauraum radial an 4 Stellen | 1.25…1.45 mm → 15–33 % (`check_sensor.txt` 7, `GTWeed_AS568_StandardOringSizing.pdf` S. 2) | Druckteile | M-D4 | |
| PT1.06 | Gateway-Passung Pi | Messschieber | Pi einlegen, Deckel, 4 × M2.5 | PWR/OTG steckbar, microSD zugänglich, kein Klemmen (`check_gateway_pi.txt` 2/4/10) | G | M-G1 | |

### Phase 2 – Sichtprüfung (ohne Speisung, alle Muster)

| ID | Ziel / REQ | Aufbau / Mittel | Durchführung | Abnahme (Quelle) | Muster | Ursprung | Ergebnis |
|---|---|---|---|---|---|---|---|
| PT2.01 | Bestückung, Pin 1 | Lupe ≥ 10×, Masszeichnung Blatt 3 | U1, U2, U3, U4–U6, Q1, Q2, D1, Y1, SW1, BT1 | alle richtig, sonst Muster sperren (B-3, LAYOUT Kap. 8) | alle | EI-1 | |
| PT2.02 | Lötbrücken | Lupe | U3 (0.20 mm), U1 QFN, SC-70 | keine Brücke (K-1/K-6) | alle | EI-2 | |
| PT2.03 | Via-in-Pad im Fach (A-3) | Lupe | 4 Pads VBAT, Minus, TP1, TP2 | eben, keine Delle/Öffnung (Querschliff → PT11.24) | alle | EI-3, ST-E1 | |
| PT2.04 | DNP, Silkscreen, REQ-MECH-16/01 | Sicht | C19/C20 unbestückt; „rev C“, Stecktiefenlinie | wie Plan | alle | EI-4 | |

### Phase 3 – Inbetriebnahme ohne Zelle

| ID | Ziel / REQ | Aufbau / Mittel | Durchführung | Abnahme (Quelle) | Muster | Ursprung | Ergebnis |
|---|---|---|---|---|---|---|---|
| PT3.01 | Kurzschluss VDD | DMM | VDD–GND an C1, beide Polungen, ≥ 10 s | > 1 kΩ (ANNAHME-Grenze); < 10 Ω → sperren (EI-5) | alle | EI-5 | |
| PT3.02 | Kurzschluss VBAT | DMM | Clip-Pad – Minuspad | wie PT3.01; Plus an VBAT steigt langsam (Body-Diode lädt C1–C4) (EI-6) | alle | EI-6 | |
| PT3.03 | Verpolschutz-Topologie | DMM Diodenprüfung | VBAT → VDD | eine Durchlassdiode, Gegenrichtung sperrt (EI-7) | alle | EI-7 | |
| PT3.04 | Barriere TP1/TP2, REQ-SAF-CC-03 | DMM | TP1–GND, TP2–GND | ≥ 200 kΩ + Pinwiderstand (R2-A3) | alle | EI-8 | |
| PT3.05 | Isolation Referenz (A-4) | 3.0 V über Shunt 100 kΩ (MM-05) in Serie, DMM (R_i 10 MΩ, ≈ 1 % Fehler) über dem Shunt | Spannung U_S über dem Shunt nach ≥ 10 min (stabil) ablesen; I = U_S / 100 kΩ (0.1 mV ≙ 1 nA); R = (3.0 V − U_S) / I. TX/RX–GND ungespeist; VBAT–GND enthält den Ruhestrom der Schaltung (nur Vergleichswert, ANNAHME) | Werte protokolliert (Referenz für PT11.17/PT11.20 vorher/nachher) (EI-9, ST-E3, EP-18) | alle | EI-9, ST-E3 | |
| PT3.06 | Erste Speisung | MM-01 3.0 V, **10 mA**, Dummy-Scheibe | Strom beim Einschalten und nach 10 s | Begrenzung nicht erreicht, keine Erwärmung; Wert protokollieren (unprogrammiert, W-10) (EI-10, ST-E2) | alle | EI-10, ST-E2 | |
| PT3.07 | Verpolschutz leitet | DMM | VDD an C1, Abfall VBAT–VDD | < 5 mV bei mA-Strom (RDS(on) < 85 mΩ, `AOS_AO3401A_Datasheet_Rev3.1.pdf` S. 2) | alle | EI-11 | |
| PT3.08 | Verpolung kurz, REQ-SAF-CC-01 | 3.0 V verpolt, 1 kΩ-Shunt, 10 s | Minus an Clip-Pad | ≤ 1 µA (AO3401A I_DSS), keine Erwärmung, danach normaler Start (EI-12, ST-E2) | alle | EI-12, ST-E2 | |

### Phase 4 – Programmierung (PROGRAMMIEREN_SENSOR.md v1.1)

| ID | Ziel / REQ | Aufbau / Mittel | Durchführung | Abnahme (Quelle) | Muster | Ursprung | Ergebnis |
|---|---|---|---|---|---|---|---|
| PT4.01 | Adapter einteilig (nur Weg A) | Adapter Rev 1, Zelle, Lupe | mit/ohne Zelle ansetzen, Dummy verkehrt | Stifte nur mit Dummy ganz im Clip auf TP1/TP2; mit Adapter keine Zelle; verkehrt kein Kontakt; VIP ohne Abdruck (ST-P1, PS-W1) | 1 Muster | ST-P1, M-B5 | |
| PT4.02 | Erstprogrammierung, REQ-FW-06 | Weg B: 2.0 V (höchstens 2.2 V), Begrenzung **10 mA** (PS-L3, EP-03), Dummy-Scheibe, CH343 (H3 ab) an R9 Pad 1, TP2 nur Prüfspitze | PROGRAMMIEREN Kap. 5 Schritte 1–7, Taster ≈ 1 s | Programmieren + Verifizieren OK (T-P1, D-024) | alle | T-P1, EI-13 | |
| PT4.03 | Weg-B-Abschluss (Veto PS-K1) | Lupe, Foto, DMM | Reihenfolge Netzteil weg → Scheibe raus → Draht weg; reinigen | Draht entfernt (Foto R9/R6/TP2), VIP unversehrt, TP1 ↔ R9 Pad 1 ≈ 200 kΩ (PROGRAMMIEREN Kap. 5 Schritt 9, ST-P5) | alle | ST-P5 | |
| PT4.04 | Erststart | 3.0 V über Dummy oder Zelle (ohne Taster) | einschalten | L11 (Grün 200 ms, dann Gelb 2 × 50 ms) (PROTOCOL 10.2) | alle | T-P1, EI-13 | |
| PT4.05 | **[D-2] Bootloader-Strom** (W-10) | Aufbau A (10 Ω) + DMM mA, 3.0 V und 2.0 V, nur Dummy-Scheibe, Begrenzung 30 mA | Taster halten, einschalten, nach ≈ 1 s loslassen (PROGRAMMIEREN Kap. 4/5); 60 s mitteln; Speisung ≥ 10 s weg, ohne Taster einschalten | Wert I_BL in PROGRAMMIEREN Kap. 6 eingetragen, Zeit bis leer = 152 mAh / I_BL (bis zur Messung 1.5–8 d, `phase5_energiebudget_final.md`); L11 nach Neustart; Regel D-2 (E15, EP-10) | S1, S2 | E15, EI-14, ST-P6 | |
| PT4.06 | Lock-Schutz Werkzeug (F-W1) | `flash_sensor.py program --lock` mit DEV-Schlüssel bzw. falschem Fingerabdruck | ausführen | Werkzeug bricht **vor** dem Schreiben ab (ST-S3) | 1 Muster | ST-S3 | |

### Phase 5 – Funktion am offenen Board

| ID | Ziel / REQ | Aufbau / Mittel | Durchführung | Abnahme (Quelle) | Muster | Ursprung | Ergebnis |
|---|---|---|---|---|---|---|---|
| PT5.01 | Advertising, REQ-SYS-08 | BLE-Scanner 1 m | Name lesen | `fluidi-XXXX`, RSSI notiert | alle | EI-25 | |
| PT5.02 | Kopplung, REQ-RF-05 | Gateway, PWA | Taster 3–8 s, PWA bestätigen, SAS-Farbfolge; Gegenprobe „stimmt nicht“ | nur mit beiden Schritten; falsche Farbfolge → Abbruch L7, kein Schlüssel gespeichert (T-K1, TS-5) | alle | T-K1, TS-5 | |
| PT5.03 | Messkette ein/aus (FW-2/FW-8) | Oszilloskop an C21 | Trigger OSC_PWR | Anstieg bis 90 % ≤ 50 µs (ANNAHME, Messwert ersetzt sie); Schlaf 0 V (EI-18) | S1 | EI-18 | |
| PT5.04 | **[D-8] Frequenzbereich Messkette** | Oszilloskop TP4 (f/8), Einzeltrigger, `GET_INFO` | Luft / trockenes Substrat / Leitungswasser bis Stecktiefenlinie, 3.0 V, 22 ± 3 °C | im Bereich nach EI-20…22 (f_osc 7.11–36.44 MHz), **MEAS_CLK max 4.55 MHz** (`simulation/spice/osc/osc_report.txt` Z. 11/21, EP-09), innerhalb Firmwaregrenzen 0.048–12 MHz am Pin; keine verlorenen Captures | alle | EI-20…22, T-M1 | |
| PT5.05 | Ratiometrie | wie PT5.04 bei 2.4 V, mit Cref1 | Rohwerte f0/f1 | protokolliert, Koeffizient FW-3 bestimmt (EI-23) | S1 | EI-23 | |
| PT5.06 | Exemplarstreuung, REQ-MES-07 | wie PT5.04 | Luft/Wasser an allen Mustern | Streuung protokolliert; Bewertung ±15 %-Punkte in PT8.04 | alle | EI-24 | |
| PT5.07 | I²C-Flanken | Oszilloskop R4/R5 Pad 2 | 100 kHz | Daten ≤ 1000 ns, Takt ≤ 300 ns (`TI_TMP1075_Datasheet_SBOS854F.pdf` S. 9 Tab. 6.8); 0x48 antwortet (EI-30) | S1 | EI-30 | |
| PT5.08 | Kein I²C während Messung (FW-1) | Oszilloskop | OSC_PWR + SDA/SCL | SDA/SCL statisch low bei OSC_PWR hoch (EI-33) | S1 | EI-33 | |
| PT5.09 | LED-Funktion, REQ-UI-02 | 3.0 V, Shunt | R, G, B einzeln, alle Muster L1–L17 | leuchtet; Farben/Zeiten nach PROTOCOL 10.2; Pulse ≤ 5 ms (FW-4) (EI-34, T-U1) | alle | EI-34, T-U1 | |
| PT5.10 | Tasterpegel | Oszilloskop SW1 Pad 1 | offen/gedrückt | offen ≈ VDD, gedrückt < 0.3 V; Prellen notiert (EI-37) | S1 | EI-37 | |
| PT5.11 | Tasterfunktionen, REQ-UI-04/06 | – | kurz / 3 s / 10 s + Bestätigung; 10 s ohne Bestätigung | Messung, Pairing, Werkseinstellung nur mit „lang–loslassen–kurz“ (PROTOCOL 10.3) (EI-38, T-U2) | S1 | EI-38, T-U2 | |
| PT5.12 | Watchdog, REQ-FW-07 | Debug-Build (MM-28), nur vor Verguss | Endlosschleife auslösen, danach Werks-Hex zurück | Neustart, Grund in GET_DIAG (T-W1) | S2 | T-W1 | |
| PT5.13 | 32-kHz-Gang, REQ-SYS-07 | gekoppelt, Gateway | Sensorzeit gegen Gateway ≥ 24 h | ≤ 99 ppm (EI-19) | S1 | EI-19 | |

### Phase 6 – Energie am offenen Board (ENERGIEMESSUNG E1–E15)

Speisung nur über die Dummy-Scheibe, nie mit Zelle im Clip, Begrenzung 30 mA (EP-03). Jede Messung bei 3.0 V und 2.4 V
(Firmware-Beitrag Kap. 2), **E6/LED bei 3.0 V und 2.6 V** (EP-16); 10 Ereignisse mitteln, Bilder/CSV ablegen.
Leckmessung PT6.03 bei 25 °C und **50 °C** (Sonnenprofil, `phase5_energiebudget_final.md`, EP-17).
E1/E14a darf direkt nach PT4 laufen (Platine noch sauber, Firmware-Beitrag Kap. 4); vorher reinigen.

| ID | Ziel / REQ | Aufbau / Mittel | Durchführung | Abnahme (Quelle) | Muster | Ursprung | Ergebnis |
|---|---|---|---|---|---|---|---|
| PT6.01 | **Ruhestrom**, REQ-ENE-09 | C (1 kΩ + Brücke), ≥ 1 h an 3.0 V, 25 °C | ungekoppelt, LEDs aus | **≤ 3 µA** (Muss), Erwartung ≤ 1.5 µA; > 10 µA → Pin-Zustände FW-6/FW-8 (E1) | alle | E1, E14a, EI-15 | |
| PT6.02 | **[D-1] Leck C1–C4, Schritt b** (W-6) | C | C3/C4 ablöten, PT6.01 wiederholen | Differenz = Leck 2 Kondensatoren (E14b) | S2, S3 | E14b, EI-16 | |
| PT6.03 | **[D-1] Leck Einzelkondensator, Schritt c** | E (100 kΩ, DMM), MM-13 | 4 Kondensatoren je bei 25 °C und 50 °C; 1 min, 10 min, **1 h**, 24 h | I_eff = (20·I_25 + 4·I_50)/24, Maximum → Regel D-1 (E14c) | S2, S3 (Teile) | E14c, EI-16 | |
| PT6.04 | **[D-1] Einbruch**, REQ-ENE-06 | B (100 Ω + 1 Ω), Oszilloskop an C1 | Advertising, Datensitzung, Messung, LED, mit 4 × (S1) und 2 × 100 µF (S2/S3) | **≤ 0.2 V** (E3/E4/E5/E6, EI-17) | S1, S2, S3 | E3–E6 (B), EI-17 | |
| PT6.05 | Advertising-Ladung | A (10 Ω) | gekoppelt, 27.5 s, 0 dBm | Ladung (Modell 16.2/40.9 µC) (E3) | S1 | E3 | |
| PT6.06 | Datensitzung, PROTOCOL 2.5 | A | HELLO … Trennen | ≤ 12 Verbindungsereignisse; Ladung ersetzt T_CONN (E4) | S1 | E4 | |
| PT6.07 | Messung (FW-2) | A, Kanal 2 an DIO11 | Taster kurz, gekoppelt ohne Gateway | Burst ≤ 0.6 ms, Pause ≥ 30 ms, ≤ 4 Bursts; Ladung ersetzt Q_MEAS (E5) | S1 | E5 | |
| PT6.08 | LED-Energie (FW-4), REQ-UI-03 | A | L8, L1, L3 bei 3.0 V und 2.6 V | ≤ 3 mA je Farbe; Pulse ≤ 5 ms, Pause ≥ 5 ms; < 2.65 V Gelb statt Blau (E6) | S1 | E6, EI-34 | |
| PT6.09 | Taster dauernd | C | > 30 s drücken | nach 30 s wieder ≈ PT6.01; Pull-up-Strom notiert (E2, PROTOCOL 10.3) | S1 | E2, EI-39 | |
| PT6.10 | Kopplung | A | Werkseinstellung, neu koppeln | ECDH ≤ 3 s (ANNAHME PP-6) (E7) | S1 | E7 | |
| PT6.11 | Schnelles Advertising | A | 20 × 100 ms nach Taste | Ladung (Modell 0.32 mC) (E8) | S1 | E8 | |
| PT6.12 | OTA-Energie, REQ-FW-05 | A (mA-Bereich) | OTA 200 kB inkl. Swap | ≤ 2 % von 225 mAh = 4.5 mAh (E9) | S1 | E9 | |
| PT6.13 | Fremdverbindung | A, zweites Gerät | 3 × ohne gültiges HELLO | Sperre greift; Ladung je Versuch (E10) | S1 | E10 | |
| PT6.14 | Unterspannung, REQ-ENE-06 | B, Netzteil langsam 2.6 → 2.3 V (bzw. 2.0–2.4 V über 100–300 Ω) | Verbindungen laufen | Abschaltung bei **VDD < 2.4 V unter Last** (FW-5; Auslegung D-025, EP-06), sauber gespeichert, kein NV-Schreiben unter UV, kein Reset-Zyklus, Wecken per Taster (E11, ST-Z6) | S1 | E11, ST-Z6 | |
| PT6.15 | Temperaturfaktor (RB-03) | C, A; MM-13/14 | E1, E3 bei 10/25/35 °C (50 °C wenn möglich) | Faktor ersetzt Annahme 1.35 (E13) | S1 | E13 | |
| PT6.16 | **Auswertung Laufzeit**, REQ-ENE-02/09, REQ-UI-03 | `scripts/energy_budget.py` | Messwerte eintragen (`rb.*`, `ble.t_cpu`, `prof.t_conn`), `--revb --out` neu, Prüfer rechnet nach | REQ-ENE-02 ≥ 12 Mt. (pess.), REQ-ENE-09 ≤ 8 µA, LED ≤ 5 %; `charge_uc`-Abweichung > 30 % → Konstanten `fl_app.c` anpassen | – | Firmware Kap. 4 Nr. 6, E-Plan Kap. 3 | |

**Tor G1 – Freigabe für Verguss je Muster** (Elektronik-Beitrag Kap. 5): PT2.01–PT6.01 und PT5.04 (Luft/Wasser)
bestanden, Behelf-Draht entfernt (PT4.03), S2/S3: C3/C4-Zustand nach D-1 festgelegt, ggf. Testfirmware für PT11.19
geflasht (S4/S5).

### Phase 7 – Verguss und Montage (MONTAGE_SENSOR.md)

| ID | Ziel / REQ | Aufbau / Mittel | Durchführung | Abnahme (Quelle) | Muster | Ursprung | Ergebnis |
|---|---|---|---|---|---|---|---|
| PT7.01 | Furchlippe / Schraube unverlierbar | PH1 | M2 × 3 erstmals eindrehen, lösen, Hülse kopfüber | Schraube fällt nicht heraus (S3-W1) | alle | M-D5 | |
| PT7.02 | Lage Platine, Tasterspalt (Messvorschrift M-D6) | Fühlerlehre 0.05 | nach Einschieben: Spalt Anschlag und Spalt Zunge–SW1 messen | Spalt Anschlag 0; Spalt Zunge–SW1 gemessen und gegen `check_sensor.txt` 2b dokumentiert (EP-01) | alle | M-D6 | |
| PT7.03 | Kragenlage (D-023 V-K, LS-W1) | Messschieber | nach Verguss, 2 Seiten | 24.2 ± 0.1 mm | alle | M-D7 | |
| PT7.04 | L11 nach Zusammenbau (W-10, PS-W5) | Zelle | Zelle einsetzen, Fach zu, erst dann Kappe berühren | L11 sichtbar; sonst Zelle ≥ 10 s raus (PROGRAMMIEREN Kap. 6) | alle, jedes Mal | PS-W5 | |

### Phase 8 – Funktion und Energie am montierten Sensor

| ID | Ziel / REQ | Aufbau / Mittel | Durchführung | Abnahme (Quelle) | Muster | Ursprung | Ergebnis |
|---|---|---|---|---|---|---|---|
| PT8.01 | **[D-3] Tastertoleranz / Schaltfunktion**, REQ-UI-04/05 | Kraftmesser, Messschieber-Tiefenmass, LED-Rückmeldung | mittig und 4 Ecken je 20 ×; Schaltpunkt (Tastenhub bis Schalten) und Resthub (Schaltpunkt bis Endanschlag) messen | SW1 schaltet bei **jedem Muster vor dem Endanschlag**; Schaltpunkt/Resthub dokumentiert gegen `check_sensor.txt` 2b (Schaltpunkt nominal 0.40 mm, voller Hub 1.15, nötig 0.45, worst Reserve +0.14, P5-M2); jede Betätigung erkannt, Kraft ≤ 5 N (ANNAHME), kein Dauerdruck im Ruhezustand (Ruhestrom ≈ PT6.01) (M-T1, EI-40, EP-01) | alle | M-T1, EI-40 | |
| PT8.02 | **[D-4] LED-Sichtbarkeit**, REQ-UI-05 | helles Büro am Fenster, 3 Personen stehend 1–2 m schräg von oben | Farben und Muster mit 5-ms-Pulsen; Blau bei 2.8 V und 2.6 V | jede Farbe von allen erkannt (EI-35); Schwellen ≥ 10 / ≥ 3 mcd ANNAHME | S1, S3 | EI-35, EI-36, T-U1, E6 | |
| PT8.03 | Kalibrierung trocken, REQ-MES-02/04/07 | Luft, PWA | 10 Messungen, „Trockenpunkt übernehmen“, danach erneut messen | Index am Kalibrierpunkt **0 % ± 3 %-Punkte** bei erneuter Messung, Wiederholbarkeit **σ ≤ 1 %-Punkt** (REQ-MES-04, EP-04); nahe Startkalibrierung 13.3 pF (Erde)/12.5 pF (Granulat), ±15 %-Punkte ohne Einzelkalibrierung (T-M2) | alle | T-M2, TS-7 | |
| PT8.04 | Kalibrierung nass, REQ-MES-02/03/09 | Leitungswasser bzw. gesättigtes Substrat bis Dichtlinie | 10 Messungen, „Nasspunkt übernehmen“, danach erneut messen | Index am Kalibrierpunkt **100 % ± 3 %-Punkte** bei erneuter Messung, **σ ≤ 1 %-Punkt** (REQ-MES-04, EP-04); nahe 40.0/36.0 pF; Auflösung ≤ 1 % | alle | T-M3, TS-7 | |
| PT8.05 | Plausibilität, REQ-MES-12 | – | Luft unter Trockenpunkt, Überflutung | Meldung `air` / `flooded` (T-M4) | S1 | T-M4 | |
| PT8.06 | Dünger/Salz, REQ-MES-11 | Becher, Dünger, Salzwasser | gleiche Feuchte, Leitungswasser vs. Düngerlösung; Salzwasser für Frequenzbereich | Δ Index ≤ 5 %-Punkte (T-M5); MEAS_CLK im Bereich (T-M1) | S1 | T-M5, T-M1 | |
| PT8.07 | Temperatureinfluss Feuchte, REQ-MES-05 | Substrat im Beutel 8/22/35 °C | je Messung | ≤ 0.3 %-Punkte/K nach Kompensation (T-M6) | S1 | T-M6 | |
| PT8.08 | Messvolumen, REQ-MES-08 | Becher, stufenweise Füllhöhe | Rohwert je 10 mm Füllhöhe | ≥ 80 % der Änderung aus 10–90 mm unter der Dichtlinie (REQ-MES-08) | S1 | **Lücke** (kein Beitrag; Elektronik verweist auf „Kalibrierteil“) | |
| PT8.09 | Bodentemperatur, REQ-TMP-01 | gerührtes Wasserbad ≈ 10/22/35 °C, MM-11, Kopf im Schatten, ≥ 15 min | Vergleich | \|ΔT\| ≤ 1.0 °C (`TI_TMP1075_Datasheet_SBOS854F.pdf` S. 7 Tab. 6.6) (EI-31) | S1, S2 | EI-31 | |
| PT8.10 | Sonne auf Kopf, REQ-TMP-01 | Lampe, Kopf 40–50 °C, Wasser 22 °C | Vergleich | Abweichung dokumentiert (EI-32) | S1 | EI-32 | |
| PT8.11 | Tagesprofil, REQ-ENE-09 | D (echte Zelle, MM-07), ≥ 24 h | Standardprofil | Tagesmittel **≤ 8 µA** (E12) | S1 | E12 | |

### Phase 9 – Funk und Gateway

| ID | Ziel / REQ | Aufbau / Mittel | Durchführung | Abnahme (Quelle) | Muster | Ursprung | Ergebnis |
|---|---|---|---|---|---|---|---|
| PT9.01 | RSSI über Abstand (nur Information) | montierter Sensor, Gateway-Log | 1 m, 5 m, ungünstigster Platz (bis ≈ 18 m) | RSSI protokolliert, **kein Abnahmekriterium** (EP-02; EI-26-Grenze aus der Sensor-Empfindlichkeit gestrichen) | S1 | EI-26 | |
| PT9.02 | **[D-5] Linkreserve**, REQ-RF-03 | schlechtester Platz | `tx_power_dbm` 0 → −20 dBm schrittweise bis Ausfall von Advertising/Sitzungen | Reserve = Betriebsleistung − Ausfallleistung **≥ 10 dB** (T-R2, EP-02) | S1 | T-R2 | |
| PT9.03 | Pi-Netz abstimmen (bedingt) | R2/C19/C20, RSSI-Vergleich (MM-26) | nur bei Reserve < 10 dB | Verbesserung dokumentiert (EI-27, OP-K9) | S1 | EI-27 | |
| PT9.04 | Gateway-Deckel | RSSI offen/geschlossen | – | Verlust protokolliert; Nylonschrauben bei Bedarf (M-G3) | G | M-G3 | |
| PT9.05 | Reaktionszeit, REQ-SYS-05 | PWA, Werkseinstellung | 20 × „Jetzt messen“ | **95 % ≤ 5 min (Muss), ≤ 1 min (Soll)** bei Werkseinstellung (REQ-SYS-05, EP-05); 100-%-Wert nur protokolliert; P_MISS bestimmt (T-R3, TS-7) | S1 | T-R3, TS-7 | |
| PT9.06 | **[D-6] Koexistenz Teil 2** (W-7) | Pi mit WLAN-Last, Sensoren | T-R3 unter Last; 1000 × „Jetzt messen“ (GATEWAY_SETUP Kap. 10 Nr. 2) | wie PT9.05 (REQ-SYS-05); P_MISS ≤ `p_miss` (Regel D-6) (T-R4, TS-14, EI-29) | S1, S2 | T-R4, TS-14, EI-29 | |
| PT9.07 | Datenempfang, Nachlieferung, REQ-LOG-01…03 | Gateway 6 h aus | 24 h Betrieb | seq lückenlos, keine Duplikate, Flag 8, **Messwert-Zeitstempel ±5 s** gegen Referenz (TS-6, EP-11) | S1 | TS-6 | |
| PT9.08 | Mehrere Sensoren | 5 Muster + 30 simuliert | 5 gleichzeitige „Jetzt messen“ | max. 3 Verbindungen, alle Werte da, Timeout nicht als Fehlversuch (TS-9) | alle | TS-9 | |
| PT9.09 | Stromausfall Gateway, REQ-GW-05/09 | Schaltleiste, Router-WAN getrennt | (a) 1 min während Sitzung; (b) 25 h stromlos; Handyuhr 2001 (GZ-1…GZ-4) | (a) Dienst startet, `integrity_check` ok; (b) `time.valid=false`, kein TIME_SET, danach `source=browser`, **Gateway-Zeitabgleich ≤ 2 s** (GZ-2), **Messwert-Zeitstempel ±5 s** (TS-8); 2001 abgelehnt (EP-11) | G, S1 | TS-8, GZ-1…GZ-4 | |
| PT9.10 | CSV-Export | LibreOffice/Excel | 1 und alle Pflanzen, 30 Tage | Lokalzeit inkl. Zeitumstellung, Zeilenzahl, Flags (TS-10) | G | TS-10 | |
| PT9.11 | Backup/Restore, REQ-GW-06 | zweite SD | Backup, Neuinstallation, Restore | Daten/Kopplungen vorhanden, Sensoren ohne Neukopplung; falsche Passphrase abgelehnt (TS-12) | G | TS-12 | |
| PT9.12 | OTA normal, REQ-FW-02/08 | Gateway | Image +1 verteilen | neue Version in der PWA, L17 grün (T-O1, TS-13) | S2 | T-O1, TS-13 | |
| PT9.13 | OTA abgebrochen, REQ-FW-03 | Gateway/Zelle | Gateway aus während Übertragung und Swap; Funk trennen bei 50 %; Zelle raus; Unterspannung | alte Version läuft bzw. Rückfall nach 24 h ohne Bestätigung; erneuter Versuch klappt (T-O2, ST-S8, TS-13) | S2 | T-O2, ST-S8, TS-13 | |
| PT9.14 | OTA unzulässig, REQ-FW-02/04 | fremd signiert, Bit gekippt, unsigniert, SEC_CNT kleiner/gleich, falsches `hw_rev`, VBAT < 2.7 V | einspielen über Gateway und direkt | Gateway lehnt ab (`signature_invalid`, 422/409); MCUboot bootet nicht; Fehlercode 0x4A (T-O3, ST-S5, ST-S7, TS-13) | S2 | T-O3, ST-S5, ST-S7, TS-13 | |
| PT9.15 | Gateway-Update, REQ-GW-11 | `install_gateway.sh`, signiertes Update | Update, defekte Signatur, nicht startende Version | Daten erhalten; abgelehnt; Rückfall nach 60 s (TS-15) | G | TS-15 | |

### Phase 10 – Mechanik und Dichtheit

| ID | Ziel / REQ | Aufbau / Mittel | Durchführung | Abnahme (Quelle) | Muster | Ursprung | Ergebnis |
|---|---|---|---|---|---|---|---|
| PT10.01 | **[D-7] Spritzwasser Kopf**, REQ-MECH-13 | 1 l aus 20 cm, 10 ×, **mit Zelle**, Indikator im Fach | Giessen, öffnen, Sichtprüfung | kein Wasser/Kondensat; Ablauf aus 4 Schlitzen (M-W1, ST-W1) | S3 (S5: Indikator auch im Elektronikraum, PT11.20) | M-W1, ST-W1 | |
| PT10.02 | Fehlbetätigung Giesswasser, REQ-UI-06 | Firmware-Log während PT10.01 | – | kein Tastenereignis, keine Werkseinstellung (M-T3, T-U2) | S3 | M-T3, T-U2 | |
| PT10.03 | Batteriewechsel, REQ-MECH-15 | BATTERIEWECHSEL.md, Person ohne Vorwissen | Stoppuhr | ≤ 5 min, nur PH1, Kragenverguss unberührt, L11 (M-B1) | S3 | M-B1 | |
| PT10.04 | Zelle hält im Clip | Hülse ab, kopfüber | schütteln | Zelle bleibt (M-B2, ST-K5) | S3 | M-B2, ST-K5 | |
| PT10.05 | Hülse ohne Schraube | aufschieben | schütteln, stecken | Ergebnis protokolliert, Anleitung angepasst (M-B4, ST-K4) | S3 | M-B4, ST-K4 | |
| PT10.06 | **[D-7] Spritzwasser nach 10 Wechseln** | wie PT10.01 | nach 10 Wechseln | wie PT10.01 (M-W2, S3-W3) | S3 | M-W2, ST-W1 | |
| PT10.07 | Taster Dauerhaltbarkeit | Zähler | 1000 Betätigungen, danach PT10.01 | Funktion wie PT8.01, Membran dicht (M-T4) | S3 | M-T4 | |
| PT10.08 | Standfestigkeit, REQ-MECH-17 | Granulat, Erde, 24 h | Winkelmesser | Neigung ≤ 10° (ANNAHME) (M-S1) | S1 | M-S1 | |
| PT10.09 | 50 Zellwechsel, REQ-SAF-CC-04 | Standardablauf | Lupe | Clip-Lötstellen ohne Riss, Kontakt ok, O-Ringe ohne Schnitt, Schraube unverlierbar, Gewinde fasst (M-B3, ST-K6) | S3 | M-B3, ST-K6 | |
| PT10.10 | Seitlast/Zug/axial, REQ-MECH-10 | Kraftmesser (MM-15) | 10 N seitlich an der Spitze, 30 N Zug, 50 N axial mit geführter Spitze | kein Bruch, keine bleibende Verformung (< 0.5 mm an der Spitze, ANNAHME), keine Risse am Kragen (M-F2, ST-M1) | S4 | M-F2, ST-M1 | |
| PT10.11 | Gateway-Wärme | Dauerlast 24 h, Raum 25 °C | Oberfläche messen | Gehäuse ≤ 82 °C; Pi ohne Drosselung, Netzteil handwarm (M-G2, ST-G2) | G | M-G2, ST-G2 | |
| PT10.12 | Alterung 65 °C / 168 h, REQ-MECH-12 | MM-13 | 65 °C 7 d, dann 10 Wechsel, dann PT11.03–05 und PT10.01 wiederholen | keine Verformung, Fenster dicht, ST-K1…K3 weiter erfüllt (M-W5, ST-K7) | S4 | M-W5, ST-K7 | |
| PT10.13 | Membran/Senkung (P5-M3) | 5 mm Wassersäule über der Taste 1 h, Indikator innen | – | trocken (M-W3) | S5 | M-W3 | |
| PT10.14 | Fall 1 m, REQ-MECH-10, REQ-SAF-CC-02/04 | harter Boden, mit Zelle, MM-07 | Kopf voran, flach (Mechanik zusätzlich seitlich auf die Spitze), je 3 ×; S3 nach PT10.09, S4 nach PT10.12, S5 vor PT11.17 ff. | kein Bruch, Fach zu, Zelle im Clip, **Zellstrom unverändert** (kein MLCC-Riss), Funktion ok (M-F1, ST-M3) | **S3, S4, S5** (EP-07) | M-F1, ST-M3 | |

### Phase 11 – Sicherheit (nicht zerstörend zuerst, zerstörend zuletzt auf S5)

| ID | Ziel / REQ | Aufbau / Mittel | Durchführung | Abnahme (Quelle) | Muster | Ursprung | Ergebnis |
|---|---|---|---|---|---|---|---|
| PT11.01 | Verpolung 24 h, REQ-SAF-CC-01 | Zelle verkehrt, MM-07, MM-12 | 24 h | Strom ≤ 5 µA, keine Erwärmung, danach Funktion ok (ST-Z1) | alle (Sicherheit Kap. 9.2) | ST-Z1 | |
| PT11.02 | Fehllagen, REQ-SAF-CC-02 | schräg, halb, verkehrt, CR2025 | Strom, Foto Kontaktbild | kein Kurzschluss (Strom ≤ Betriebsstrom), Becherrand ohne GND-Kontakt (ST-Z2) | alle | ST-Z2 | |
| PT11.03 | Verschluckschutz ohne Werkzeug, REQ-SAF-CC-04 | PH1, Markierstift | Schraube **handfest** anziehen, Kopf/Hülse markieren; mit Fingern öffnen versuchen | Fach öffnet nicht ohne Werkzeug, Markierung unverändert; Lösemoment-Prüfung **entfällt** (ANNAHME bis Anzugsmoment festgelegt, EP-14) (ST-K1) | S3, S4 | ST-K1 | |
| PT11.04 | Zug 72 N | Gewicht 7.34 kg (gewogen) an Schnur | Hülse geschlossen, Sensor fixiert, Gewicht langsam anhängen, 10 s | Fach bleibt zu (ST-K2, EP-14) | S3, S4 | ST-K2 | |
| PT11.05 | Druck 136 N | Gewicht 13.86 kg (gewogen), z. B. Wasserkanister auf Druckstück | auf das Fach, 10 s | kein Öffnen, kein Bruch, Zelle unzugänglich (ST-K3, EP-14) | S3, S4 | ST-K3 | |
| PT11.06 | Rückstrom TP1/TP2, REQ-SAF-CC-03, REQ-SAF-06 — **einzige Ausnahme von Grundregel 1** | Labornetzteil, Begrenzung **≤ 1 mA** vor dem Anschliessen am offenen Ausgang kontrolliert (Z5-2); Strom in der Pad-Leitung; Zellstrom nur über MM-07 (Z5-3) | 3.3 V und 5 V an je einem Pad, ein 100 kΩ als Draht überbrückt; 5.5 V an beiden Pads; Zelle 3.0 V; „Zelle 0 V“ **ohne Zelle**, Clip-Kontakte über den Shunt (Z5-4); „entladen“ nur Zelle 2.0–2.6 V; **≤ 10 min je Fall** (Z5-5); beaufsichtigt, nicht brennbare Unterlage, benannter Prüfer, nicht zusammen mit Programmieren/Energiemessung (Z5-1) | ≤ 55 µA je Pad (CONCEPTS 2.7); **Abbruch** bei Pad-Strom > 100 µA, Ansprechen der Begrenzung oder Erwärmung/Geruch/Aufblähen – Quelle zuerst abklemmen, dann Zelle (Z5-6); danach Brücke entfernt, Foto + ≈ 200 kΩ, Muster als „Fehlertest“ gekennzeichnet, Zellen entsorgt (Z5-7); Funktion danach (ST-Z5; Bedingungen `phase5_sicherheit_runde3.md` Z5-1…Z5-7) | S4 (benanntes Prüfmuster) | ST-Z5 | |
| PT11.07 | Reset-/Weckschleifen (PP-11) | EOL-Quelle unter POR, Taster dauernd, fataler Fehler (MM-28) | Mittelstrom, NV-Schreibzahl | ≤ 10 × Ruhestrom (ANNAHME), Abschaltung nach 3 Resets (ST-F6) | S4 | ST-F6 | |
| PT11.08 | Kraftfluss Taster, REQ-SAF-LI-05 sinngemäss | Kraftmesser, Lupe | 100 × mit 20 N, danach 10 × 50 N (Einstecklast REQ-MECH-10) und Fall 1 m Kopf voran (D-026) | Kraft nicht über die Zelle; kein Weissbruch an Zunge/Nase, SW1 schaltet weiter (M-T2, ST-M2); Bruch bei 50 N/Fall → Rev D Taster mit Betätiger in z (C-2) | S5 | M-T2, ST-M2 | |
| PT11.09 | Kopplung ohne Taster, REQ-RF-05 | Gateway PAIR_REQ | ohne Tastendruck; zweiter Versuch nach Abbruch | ERROR, kein Schlüssel (ST-S2) | S2 | ST-S2 | |
| PT11.10 | MITM-Kopplung (F-K1) | Host-Test ≥ 10 000 Läufe + Funkversuch mit 2 Geräten | – | Erfolgsrate ≤ 1 %, Fehlversuch rot sichtbar (ST-S1) | S2 | ST-S1 | |
| PT11.11 | Fremdes Gateway, Replay, RNG-Fehler, REQ-RF-06 | zweites Gerät, aufgezeichnete Sitzung, `port_sim` | verbinden, wiederholen | abgelehnt, Sperre nach 3 Versuchen, Abbruch bei RNG-Fehler (T-K2, ST-S4) | S2 | T-K2, ST-S4 | |
| PT11.12 | OTA ohne Schlüssel | `fw_pubkey` leer | Image hochladen | nicht angenommen (ST-S6) | G | ST-S6 | |
| PT11.13 | Schreibrouten ohne Sitzung, REQ-SAF-NET-01 | Skript über `api.ROUTES` | ohne Cookie/CSRF | 401/403, keine Änderung (ST-N1) | G | ST-N1 | |
| PT11.14 | Ports, REQ-SAF-NET-02 | `nmap -p-` und `nmap -sU --top-ports 100` vom LAN, Auslieferungszustand (nach `--finish`) | einmal mit Dashboard aus, einmal freigegeben | **TCP 80, 443 offen; TCP 8080 nur offen, wenn das Dashboard in der PWA freigegeben ist** (sonst kein Dienst); **UDP 5353** (mDNS); TCP 22 **nicht** offen; alles übrige gefiltert (policy drop; DHCP 68/546 nur als Antwort von 67/547) (TS-11, ST-N3, EP-12; Quelle `firmware/gateway/install/nftables-fluidi.conf` Z. 7–17, `install/gateway.toml` Z. 6–8, `fluidi_gw/server.py` Z. 454–461, `install/install_gateway.sh` Z. 53–56) | G | TS-11, ST-N3 | |
| PT11.15 | Dashboard nur lesen (D-022) | Port 8080 | Schreibversuch | abgelehnt (ST-N5) | G | ST-N5 | |
| PT11.16 | RTC-Pufferzelle ohne Ladestrom | Amperemeter in Serie zur RTC-Zelle | Gateway an | Strom in die Zelle ≤ 0 (ST-G1) | G | ST-G1 | |
| PT11.17 | Fach geflutet 24 h, REQ-SAF-05 | Leitungswasser, Zelle, MM-07 | 24 h | REQ-SAF-01-Kriterien; Isolation vorher/nachher (Ref. PT3.05) (ST-W2) | S4 | ST-W2 | |
| PT11.18 | Lock Serie (PP-9) | `--lock --expect-key-fp` Testschlüssel; danach SWD/SACI und ROM-Bootloader mit Taster | – | Bootloader antwortet nicht; OTA und Sicherheitszähler gehen weiter (T-P2, ST-S9) | S5 | T-P2, ST-S9 | |
| PT11.19 | **[D-7] Kragen**, REQ-MECH-08 | 50 Zyklen −10/+65 °C, 168 h 65 °C, je 24 h tauchen bis z +3 und Fach fluten; SENS_PWR dauernd high (MM-28) | Leckstrom, I²C | Leck SENS_PWR–GND ≤ 1 µA (ANNAHME), I²C ok, Indikator trocken (ST-W4, M-W4) | S4 (ohne Schliff), S5 | ST-W4, M-W4 | |
| PT11.20 | **[D-7] Elektronikraum geflutet 24 h**, REQ-SAF-05 | gezielt geöffnet, Zelle, MM-07 | 24 h | wie PT11.17 (ST-W3); vorher M-W1 mit Indikator im Elektronikraum (M-W1 Opfermuster) | S5 | ST-W3, M-W1 | |
| PT11.21 | Kurzschluss je Bauteil, REQ-SAF-01 | Draht über C1–C4, Q1 D–S; Zelle, MM-12 | nacheinander | keine Flamme/Rauch/Aufblähen; 65 °C + ΔT ≤ 85 °C Zelle, ≤ HDT − 10 K Gehäuse (ST-Z4) | S5 | ST-Z4 | |
| PT11.22 | Kurzschluss Zellausgang, REQ-SAF-01 | Clip-VBAT–GND hinter dem Clip, 1 h | – | keine Flamme/Rauch/Aufblähen; 65 °C + ΔT ≤ 85 °C (ST-Z3) | S5 | ST-Z3 | |
| PT11.23 | Schliff Kragen | Säge, Lupe | nach PT11.19 | keine Lunker, keine Ablösung an Platine/Tasche (ST-W4, M-W4, K-7) | S5 | ST-W4, M-W4 | |
| PT11.24 | Querschliff VBAT-VIP (A-3) | Säge/Schliff | **zuletzt** | ohne Lunker (ST-E1) | S5 | ST-E1 | |

### Phase 12 – Dauer und Feld

| ID | Ziel / REQ | Aufbau / Mittel | Durchführung | Abnahme (Quelle) | Muster | Ursprung | Ergebnis |
|---|---|---|---|---|---|---|---|
| PT12.01 | Reichweite 7 Tage, REQ-RF-02 | alle Sensoren an ihren Plätzen (bis 18 m) | 7 d | ≥ 99 % innert 1 h, 100 % nach Nachlieferung (T-R1, EI-28) | alle funktionsfähigen | T-R1, EI-28 | |
| PT12.02 | Gateway-Dauerlauf, REQ-GW-04 | MM-24, `GET /system` | parallel zu PT12.01 | kein Watchdog-Neustart, SD-Schreibmenge/CPU-Temp notiert, ≤ 2 W (TS-16) | G | TS-16 | |
| PT12.03 | Pufferung ohne Gateway, REQ-LOG | Gateway 7 d aus | danach einschalten | alle Datensätze lückenlos nachgeliefert (T-Z2) | S1–S3 | T-Z2 | |
| PT12.04 | Zeit ohne Gateway, REQ-SYS-07 | Gateway 14 d aus (60 d Stichprobe) | Zeitstempel vergleichen | ≤ ±2 min nach 14 d, ≤ ±5 min nach 60 d (T-Z1) | S1–S3 | T-Z1 | |
| PT12.05 | Langzeit nass, REQ-MES-06, REQ-MECH-14, REQ-MECH-08 | Becher bis Dichtlinie bzw. nasse Erde, Indikator im Kopf | Rohwert Luft/Wasser vor, nach 1, 7, 14, 30 d | Δ ≤ 3 % der Kalibrierspanne; Indikator unverändert (REQ-MES-06, ST-W5) | S1 | ST-W5, Firmware Kap. 4 Nr. 5 | |
| PT12.06 | Gateway-Gang ohne Referenz, REQ-GW-09 | RTC, ohne NTP | 30 d gegen Referenzuhr | ≤ ±2 min/Monat (REQ-GW-09) | G | **Lücke** (kein Beitrag) | |

## 4 Zeitplan (Vorschlag)

| Woche | Tätigkeit |
|---|---|
| vor Lieferung | Phase 0 (PT0.06 Koexistenz 24 h mit XIAO, falls vorhanden), Druckteile PT1.02–1.06, Dummy-Scheibe, Mess-Zwischenadapter bauen |
| 1 | PT1.01, Phase 2–4 an allen Mustern; PT6.01 direkt nach Programmierung; PT5 |
| 2 | Phase 6 (PT6.03 braucht 24 h je Temperatur), Entscheid D-1, Tor G1, Debug-/Testfirmware flashen; Verguss (Aushärtezeit nach MONTAGE_SENSOR) |
| 3 | Phase 7–9; PT12.05 (30 d) auf S1 starten |
| 4 | Phase 10 nicht zerstörend (S3), PT10.12 Alterung S4 (7 d) parallel; PT12.01 + PT12.02 (7 d, alle Muster) |
| 5–7 | PT12.03 (7 d), PT12.04 (14 d); parallel Phase 11 nicht zerstörend |
| 8 | Phase 11 zerstörend auf S4/S5 (PT11.17–PT11.24), Abschluss PT12.05, Auswertung PT6.16 |

## 5 Entscheidungs-Tests und Entscheidungsregeln

| Nr | Thema (Quelle) | Tests | Entscheidungsregel (Quelle) | Offen |
|---|---|---|---|---|
| **D-1** | **W-6 Kondensatoren** 2 oder 4 × 100 µF (`phase4_zusammenfassung.md` Kap. 6, D-013, REQ-ENE-02 pessDS) | PT6.01–PT6.04 | I_eff = (20·I_25 + 4·I_50)/24, Maximum aller Kondensatoren: **≤ 1.24 µA → 4 × 100 µF**; **1.24–2.49 µA → 2 × 100 µF nur wenn** Einbruch PT6.04 mit 2 Kondensatoren ≤ 0.2 V, sonst Vorlage Auftraggeber; **> 2.49 µA → Vorlage Auftraggeber** (`ENERGIE_REV_B.md` Kap. 3e, Firmware-Beitrag 2.1, ENERGIEMESSUNG E14). **Vorher D-Eintrag:** Messwert × 1.5 ersetzt den Katalog-Grenzwert (Auslegung REQ-ENE-08) | D-Eintrag noch nicht angelegt |
| **D-2** | **W-10 Bootloader-Strom** | PT4.05 | Wert I_BL dokumentieren, Zeit bis leer = 152 mAh / I_BL (Firmware-Beitrag 2.2); L11 nach Neustart ohne Taster muss erscheinen, sonst NOK. **Leert I_BL die Zelle in < 7 Tagen** (152 mAh / 168 h ⇒ I_BL > 0.90 mA) → Trigger-Änderung für die Serie prüfen (PS-W5); sonst bleibt die Anleitungsregel (EP-L02) | – |
| **D-3** | **Tastertoleranz** (M-4, P5-M2) | PT7.02, PT8.01, PT10.07, PT11.08 | Jede Betätigung (mittig + 4 Ecken, 20 ×) erkannt **und** Kraft ≤ 5 N (ANNAHME) **und** kein Dauerdruck im Ruhezustand (Ruhestrom ≈ PT6.01, kein Bootloader-Fehlstart beim Zusammenbau) → Taster freigegeben. SW1 muss bei jedem Muster vor dem Endanschlag schalten; Schaltpunkt/Resthub gegen `check_sensor.txt` 2b dokumentiert (EP-01). **Nicht bestanden → Mechanikänderung vor der Serie** (EP-L03) | – |
| **D-4** | **LED-Sichtbarkeit E6** (D-023 EP-2) | PT8.02, PT6.08 | Alle Farben von allen 3 Personen erkannt → EP-2 bleibt. Sonst Vorwiderstände R6/R7/R8 oder Pulslänge anpassen, **nur** mit Nachrechnung Einbruch (PT6.04 ≤ 0.2 V) und LED-Budget ≤ 5 % (REQ-UI-03) (EI-35/36) | – |
| **D-5** | **Antennenabstand / RSSI** (REQ-RF-03 Soll, LAYOUT Kap. 10, OP-K9) | PT9.01–PT9.04 | Linkreserve am schlechtesten Platz nach Methode T-R2 (PT9.02) **≥ 10 dB** → keine Änderung; RSSI (PT9.01) nur Information (EP-02). < 10 dB → PT9.03 (Pi-Netz abstimmen), Gateway-Standort/Deckel (PT9.04) prüfen. Ergebnis fliesst auch in W-6-Alternative „TX 0 → −4 dBm“ (Red Team W-6) | – |
| **D-6** | **Koexistenz WLAN/BLE W-7** (OP-K12, OP-GW-4) | PT0.06, PT9.05, PT9.06 | P_MISS ≤ `p_miss` in der Gateway-Konfiguration (0.10, `firmware/gateway/fluidi_gw/config.py` Z. 36, ANNAHME bis Test) → kein Handlungsbedarf; sonst Messwert eintragen und Energiebudget neu rechnen (PT6.16). Reaktionszeit nach REQ-SYS-05 (EP-05). Den Koexistenztest führt der **Auftraggeber** durch; **fällt er durch** (P_MISS > `p_miss` oder REQ-SYS-05 nicht erfüllt) → Entscheid **XIAO nRF52840 als BLE-Empfänger** (D-014, EP-L04) | – |
| **D-7** | **Dichtheit** (REQ-MECH-08/13, REQ-SAF-05) | PT10.01, PT10.06, PT10.13, PT11.17, PT11.19, PT11.20, PT12.05 | Jeder Test „trocken/kein Wasser im Kopf“ bzw. REQ-SAF-01-Kriterien erfüllt → Dichtkonzept freigegeben. Ein NOK in PT11.17/PT11.20 (Sicherheit) ist ein **kritischer Befund** mit Veto-Möglichkeit (REQ-SAF-04); NOK in PT10.01/10.06/10.13 → Befund Mechanik, Wiederholung nach Korrektur | – |
| **D-8** | **Frequenzbereich Messkette 4.8–36 MHz** (`phase4_zusammenfassung.md` Kap. 6) | PT5.04–PT5.06, PT8.06 | Messwerte im Simulationsbereich und in den Firmwaregrenzen → keine Änderung. Obergrenze MEAS_CLK 4.55 MHz (EP-09). Ausserhalb Simulation, innerhalb Firmwaregrenzen → Knotenkapazität (9.9 pF) und tpd untersuchen (EI-Beitrag 3.6) | – |

## 6 Abdeckung REQ-DOC-03

| Gefordert | Tests |
|---|---|
| Kalibrierung | PT8.03–PT8.08, PT5.04–5.06 |
| Langzeit-Wassertest | PT12.05 |
| Laufzeit | PT6.01–PT6.16, PT8.11 (rechnerisch aus Messwerten; eine Laufzeitmessung über 12 Monate ist am Prototyp nicht vorgesehen) |
| Funkreichweite | PT9.01–9.06, PT12.01 |
| Batterie | PT10.03–10.05, PT10.09, PT11.01/02 |
| Temperatur | PT8.07, PT8.09/10, PT6.15 |
| Sicherheit inkl. REQ-SAF-05, -CC-03/04 | Phase 11, PT3.04, PT3.08, PT10.14; **REQ-SAF-LI-07/08** entfallen (Variante CR2032, keine LiPo-Tests) |

## 7 Lücken (von der Projektleitung übernommen, Regeln siehe EP-L02…L04)

| Nr | Lücke | Vorschlag zur Klärung |
|---|---|---|
| L-01 | REQ-MES-08 Messvolumen (Becherversuch) und REQ-GW-09 Gangabweichung Gateway hat kein Beitrag als Test definiert; hier aus dem REQ-Text als PT8.08/PT12.06 übernommen | Methode durch Elektronik bzw. Software bestätigen |
| L-02 | W-10: Ab welchem Bootloader-Strom wird PS-W5 (Trigger-Pin) umgesetzt? | Firmware/Sicherheit legen Schwelle fest |
| L-03 | Tastertoleranz: Folgemassnahme bei NOK (Nase/Zunge ändern, neuer Druck) | Mechanik |
| L-04 | W-7: Schwelle für „XIAO-Empfänger fest einplanen“ | Software/Orchestrator |
| L-05 | Mess-Zwischenadapter (MM-07) ist nicht konstruiert, wird aber für E12, ST-Z*, ST-W2/W3, ST-M3, ST-P6 mit Zelle gebraucht | Mechanik/Elektronik konstruieren (wie Dummy-Scheibe, mit isolierender Zwischenlage) |
| L-06 | Testfirmware (MM-28) für PT5.12, PT11.07, PT11.19 existiert nicht; Firmware-Beitrag sieht keinen Testbefehl im Protokoll vor | Firmware: Build-Varianten definieren und vor dem Verguss flashen |

## 8 Zusammenfassung der Zählung

| Phase | Tests |
|---|---|
| 0 Vorbereitung | 10 |
| 1 Wareneingang | 6 |
| 2 Sichtprüfung | 4 |
| 3 Inbetriebnahme ohne Zelle | 8 |
| 4 Programmierung | 6 |
| 5 Funktion offenes Board | 13 |
| 6 Energie | 16 |
| 7 Verguss/Montage | 4 |
| 8 Funktion/Energie montiert | 11 |
| 9 Funk/Gateway | 15 |
| 10 Mechanik/Dichtheit | 14 |
| 11 Sicherheit | 24 |
| 12 Dauer/Feld | 6 |
| **Summe** | **137** (aus 167 Ursprungs-Tests: EI 40, E 15, T- 22, M- 27, ST- 47, TS 16, ohne die 6 PROTOTYP-PRÜFUNGEN aus Phase 4, die alle zugeordnet sind; davon 8 Entscheidungs-Testgruppen D-1…D-8) |

## 9 Widersprüche zwischen den Beiträgen (Entscheide in Kap. 10)

| Nr | Gewicht | Widerspruch | Fundstellen | Betroffene Tests |
|---|---|---|---|---|
| WS-01 | wichtig | **Tastertoleranz:** „Worst Case −0.20 mm“ (Phase 4 Kap. 6, Elektronik EI-40) gegen „worst **+0.14** mm, RSS-Reserve 0.44“ nach P5-M2 (`mechanical/sensor/check_sensor.txt` 2b, `phase5_checkliste_mechanik.md` P5-M2) gegen Mechanik-Beitrag M-D6 „Spalt 0.25 (−0.30/+0.30, RSS ≥ 0.08)“. Welcher Sollwert ist die Abnahme in PT7.02? | EI-40, M-D6, check_sensor 2b | PT7.02, PT8.01, D-3 |
| WS-02 | wichtig | **Linkreserve:** EI-26 setzt RSSI ≥ −86.5 dBm aus der **Sensor**-Empfindlichkeit (CC2340R5 DS S. 22 Tab. 7.14); der Empfänger ist aber der Pi. T-R2 bestimmt die Reserve per Sendeleistungsabsenkung, weil die Pi-Empfindlichkeit lokal fehlt. | EI-26, T-R2 | PT9.01, PT9.02, D-5 |
| WS-03 | wichtig | **Strombegrenzung:** Elektronik-Grundregel ≤ 10 mA (Programmierung ≤ 20 mA) für jede Fremdspeisung, ENERGIEMESSUNG/Firmware ≤ 20 mA; Aufbau A erwartet TX-Spitzen ≈ 13 mA (ENERGIEMESSUNG Kap. 1). Mit 10 mA würde die Begrenzung die Ereignismessung verfälschen. | Elektronik Kopf, ENERGIEMESSUNG „Sicherheit“/Aufbau A | PT6.04–PT6.15 |
| WS-04 | wichtig | **Kalibriergenauigkeit nass:** T-M3 „Index 100 % ± 1 %-Punkt“ gegen TS-7 „0/100 % an den Punkten ± 3 pp“. | T-M3, TS-7 | PT8.03, PT8.04 |
| WS-05 | wichtig | **Reaktionszeit:** REQ-SYS-05 = 95 % ≤ 5 min (Muss), ≤ 1 min (Soll); T-R3 ergänzt „100 % ≤ 5 min (Muss)“; TS-7/TS-14 verwenden „eingestellte Reaktionszeit + 30 s (95 %)“. | REQ-SYS-05, T-R3, TS-7, TS-14 | PT9.05, PT9.06, D-6 |
| WS-06 | wichtig | **Abschaltschwelle:** REQ-ENE-06 nennt „2.0 V unter Last an der Zellklemme (ANNAHME bis Chipwahl)“, Firmware/Sicherheit prüfen 2.4 V VDD unter Last (FW-5, E11, ST-Z6). Abnahme von PT6.14 gegen welchen Wert? | REQ-ENE-06, PINMAP FW-5, E11, ST-Z6 | PT6.14 |
| WS-07 | wichtig | **Falltest:** Mechanik M-F1 an M1–M3 (3 Muster, je 3 ×, zusätzlich „seitlich auf die Spitze“), Sicherheit ST-M3 am **Opfermuster**, REQ-MECH-10 nennt nur „Kopf voran und flach“. Hier vorläufig S4/S5. | M-F1, ST-M3, REQ-MECH-10 | PT10.14 |
| WS-08 | wichtig | **Musterzuteilung:** Sicherheit will ST-Z1/Z2/Z5, ST-K1…K6 „an allen Mustern“ und 1 Opfermuster; Mechanik M1–M3 + M0; Elektronik 2 „Opfermuster“ für C3/C4-Ablöten (EI-16). Mit 5 Mustern nicht alles gleichzeitig erfüllbar; Zuteilung Kap. 2 ist ein Vorschlag. | Sicherheit Kap. 9, Mechanik Kopf, Elektronik Kap. 5 | Kap. 2 |
| WS-09 | klein | **Frequenzbereich:** Phase 4 „4.8–36 MHz“, T-M1 „MEAS_CLK 0.59–4.51 MHz (f ≈ 4.7–36 MHz)“, EI-20…22 „MEAS_CLK 0.89–4.55 MHz (f 7.11–36.44 MHz)“ für Wasser…Luft; Obergrenze 4.51 vs. 4.55 MHz, untere Grenze je nach Medium (T-M1 schliesst Salzwasser ein). | EI-20…22, T-M1, Phase 4 Kap. 6 | PT5.04, PT8.06, D-8 |
| WS-10 | klein | **Bootloader:** Zeit bis Zelle leer 1.5–8 d (152 mAh pess., Firmware 2.2) vs. 2–12 d (225 mAh, PROGRAMMIEREN Kap. 6, PS-W5); Taster nach 2 s (E15) vs. ≈ 1 s (PROGRAMMIEREN Kap. 4/5) loslassen; ST-P6 misst „mit Zelle bzw. 3.0 V“, E15 bei 3.0 und 2.0 V. | E15, PROGRAMMIEREN Kap. 6, ST-P6 | PT4.05 |
| WS-11 | klein | **Gateway-Zeit:** TS-6/TS-8 „±5 s gegen Referenz“, `phase5_gateway_zeit.md` T-Z2 „≤ 2 s“. Zudem ID-Kollision: T-Z1/T-Z2 bedeuten im Firmware-Beitrag (Sensorzeit 14 d, Pufferung 7 d) und in `phase5_gateway_zeit.md` (Gateway-Neustart) Verschiedenes. | TS-6, TS-8, gateway_zeit T-Z1…T-Z4, Firmware T-Z1/T-Z2 | PT9.07, PT9.09, PT12.03/04 |
| WS-12 | klein | **Portliste:** ST-N3 „HTTPS, Dashboard 8080 falls an, kein SSH“, TS-11 „80, 443, 5353/udp (8080 nur mit Dashboard)“. | ST-N3, TS-11 | PT11.14 |
| WS-13 | wichtig | **Quelle an TP1/TP2:** Elektronik-Grundregel, ENERGIEMESSUNG und PROGRAMMIEREN Regel 1 verbieten Quellen an TP1/TP2; ST-Z5 legt bewusst 3.3–5.5 V an TP1/TP2 bei eingesetzter Zelle (ein 100 kΩ überbrückt). Ausnahme und Abbruchkriterien muss die Sicherheit ausdrücklich freigeben. | Elektronik Kopf, ENERGIEMESSUNG, PROGRAMMIEREN Kap. 1, ST-Z5 | PT11.06 |
| WS-14 | wichtig | **Kraftmesser:** Mechanik nennt 0–100 N, ST-K3 verlangt 136 N; ST-K1 Drehmomentschlüssel 0.5 Nm widerspricht dem Rahmen „keine 100 CHF für Messgeräte“ möglicherweise (Preis nicht belegt). | Mechanik Kopf, ST-K1/K3, CLIENT_INPUT Nr. 10 | PT11.03, PT11.05 |
| WS-15 | wichtig | **Testfirmware:** ST-W4 verlangt „SENS_PWR dauernd high (Testfirmware)“, ST-F6 „fataler Fehler“, T-W1 „Debug-Build“; der Firmware-Beitrag sieht keinen Testbefehl vor, im Repo gibt es keine solche Build-Variante (`grep` in `firmware/sensor` ohne Treffer). Nach dem Verguss nur mit Adapter Rev 1 flashbar. | ST-W4, ST-F6, T-W1 | PT5.12, PT11.07, PT11.19 |
| WS-16 | klein | **Spannungen E6/LED:** Firmware „jede Energiemessung bei 3.0 V und 2.4 V“, ENERGIEMESSUNG E6 „3.0 und 2.6 V“, EI-35 „2.8 und 2.6 V“; bei 2.4 V liegt die Firmware an der Abschaltschwelle (FW-5). | Firmware Kap. 2, ENERGIEMESSUNG E6, EI-35 | PT6.08, PT8.02 |
| WS-17 | klein | **Prüftemperatur Leckstrom:** Beiträge 50 °C (E14c), Red-Team-Vorschlag W-6 45 °C (`phase4_redteam_gesamt.md`). | E14c, Red Team W-6 | PT6.03 |
| WS-18 | klein | **Isolationsmessung:** ST-E3 verlangt „Pikoamperemeter“, Rahmen CLIENT_INPUT Nr. 10 schliesst teure Geräte aus; Ersatzmethode (DMM über Shunt) hat kein Kriterium. | ST-E3, EI-9 | PT3.05, PT11.17 |

## 10 Entscheide Projektleitung (2026-11-08)

Entscheide des Orchestrators zu Kap. 9 und Kap. 7; in die Tests eingearbeitet (Spalte „Tests“). EP-n gehört zu WS-n.

| Nr | Entscheid | Begründung | Tests |
|---|---|---|---|
| EP-01 | Massgebend ist P5-M2 (`mechanical/sensor/check_sensor.txt` 2b, Worst Case **+0.14 mm**); der Wert −0.20 mm (EI-40, Phase 4 Kap. 6) ist überholt. Abnahme: SW1 schaltet bei jedem Muster vor dem Endanschlag; Schaltpunkt und Resthub messen und gegen 2b (nominal 0.40 mm) dokumentieren; M-D6 gilt als Messvorschrift. | aktueller CAD-Stand mit Nase 45° an der Zunge (P5-M2) | PT7.02, PT8.01, D-3 |
| EP-02 | Linkreserve nach Methode T-R2 (Sendeleistung stufenweise senken); EI-26-Kriterium aus der Empfindlichkeit des Sensor-Chips gestrichen, RSSI nur Information. | Empfänger ist der Pi; seine Empfindlichkeit ist lokal nicht belegt | PT9.01, PT9.02, D-5 |
| EP-03 | Programmieren Weg B **10 mA** (PS-L3). Funktions- und Energietests mit Funk: **3.0 V, Begrenzung 30 mA, nur über die Dummy-Scheibe, nie mit Zelle im Clip**. | TX-Spitzen ≈ 13 mA (ENERGIEMESSUNG Aufbau A) würden bei 10/20 mA die Messung verfälschen; die Dummy-Scheibe belegt den Clip (Veto PS-K1). `ENERGIEMESSUNG.md` („≤ 20 mA“) und Elektronik-Grundregel sind entsprechend nachzuführen. | Grundregel 2, PT4.02, PT4.05, Phase 6 |
| EP-04 | Abnahme am Kalibrierpunkt ±3 %-Punkte bei erneuter Messung, zusätzlich Wiederholbarkeit σ ≤ 1 %-Punkt (REQ-MES-04). | ±1 %-Punkt (T-M3) liegt in der Grössenordnung der Wiederholbarkeit selbst | PT8.03, PT8.04 |
| EP-05 | Reaktionszeit wörtlich nach REQ-SYS-05: 95 % ≤ 5 min (Muss), ≤ 1 min (Soll) bei Werkseinstellung; 100-%-Wert aus T-R3 nur protokollieren. | Anforderung ist massgebend, Beiträge dürfen sie nicht verschärfen | PT9.05, PT9.06, D-6 |
| EP-06 | Abnahme gegen FW-5 (**2.4 V VDD unter Last**). Projektleitung trägt die Auslegung als **D-025** ein (dem Auftraggeber vorgelegt). | REQ-ENE-06 führt 2.0 V ausdrücklich als ANNAHME bis zur Chipwahl | PT6.14 |
| EP-07 | Falltest an **S3, S4, S5** (je nach ihren übrigen Tests), nicht an S1/S2. | S1/S2 tragen Referenz-, Langzeit- und Firmwaretests | PT10.14, Kap. 2 |
| EP-08 | Zuteilung S1–S5 wie in Kap. 2 bestätigt, ein Opfermuster (S5). | – | Kap. 2 |
| EP-09 | Obergrenze MEAS_CLK **4.55 MHz**. | Neulauf Phase 5 `simulation/spice/osc/osc_report.txt` Z. 11/21 (f_osc 4.76–36.44 MHz) | PT5.04, D-8 |
| EP-10 | Bootloader: bis zur Messung E15 gilt **1.5–8 Tage** (`phase5_energiebudget_final.md`, 152 mAh pess.); Taster **≈ 1 s** halten (PROGRAMMIEREN_SENSOR.md). | pessimistische Kapazität ist der Nachweisfall | PT4.02, PT4.05 |
| EP-11 | Zwei verschiedene Grössen: Gateway-Zeitabgleich ≤ 2 s (`phase5_gateway_zeit.md`), Messwert-Zeitstempel ±5 s (TS-6/TS-8). ID-Kollision aufgelöst: Gateway-Zeittests heissen jetzt **GZ-1…GZ-4** (umbenannt in `phase5_gateway_zeit.md`, `phase5_checkliste_software.md` P-7, `phase5_testplan_beitrag_software.md` TS-8); T-Z1/T-Z2 bleiben die Sensortests. | – | PT9.07, PT9.09, PT12.03/04 |
| EP-12 | Portliste aus dem Code: TCP 80/443, TCP 8080 nur bei freigegebenem Dashboard, UDP 5353, SSH 22 nur bis `--finish`, sonst policy drop. | `install/nftables-fluidi.conf` Z. 7–17, `install/gateway.toml` Z. 6–8, `fluidi_gw/server.py` Z. 454–461, `install_gateway.sh` Z. 53–56 | PT11.14 |
| EP-13 | ST-Z5 bleibt **einzige Ausnahme** von Grundregel 1 unter den Bedingungen **Z5-1…Z5-7** (u. a. Begrenzung ≤ 1 mA, ≤ 10 min je Fall, Abbruch > 100 µA, nur benannte Prüfmuster). | Entscheid Sicherheit, `docs/reviews/phase5_sicherheit_runde3.md` | Grundregel 1/2, PT11.06 |
| EP-14 | ST-K2/K3 mit **Gewicht** statt Kraftmesser (72 N ≙ 7.34 kg, 136 N ≙ 13.86 kg, Masse gewogen). Drehmoment: bis das Anzugsmoment festgelegt ist, „handfest“ mit Markierung; Lösemoment-Prüfung entfällt (**ANNAHME**). | keine Messgeräte-Anschaffung (CLIENT_INPUT Nr. 10) | PT11.03–11.05, MM-15/16 |
| EP-15 | Testfirmware fehlt → Spezifikation der benötigten Testfunktionen in **Anhang A**; Erstellung ist Aufgabe Firmware **vor Musterankunft**. | – | PT5.12, PT11.07, PT11.19, MM-28 |
| EP-16 | E6/LED bei **3.0 V und 2.6 V**. | 2.4 V liegt an der Abschaltschwelle FW-5 | PT6.08, PT8.02 |
| EP-17 | Leckmessung bei **50 °C**. | Sonnenprofil RB-03, `phase5_energiebudget_final.md` | PT6.03 |
| EP-18 | Isolation mit DMM über Shunt (Methode PT3.05); Pikoamperemeter entfällt. | Werkstattmittel | PT3.05, MM-25 |
| EP-L01 | L-01…L-06 übernommen (PT8.08, PT12.06 bleiben im Plan; MM-07 und Anhang A sind zu erstellen). | – | Kap. 7 |
| EP-L02 | W-10: Leert der gemessene Bootloader-Strom die Zelle in **< 7 Tagen** → Trigger-Änderung für die Serie prüfen (PS-W5). | – | PT4.05, D-2 |
| EP-L03 | Tastertest nicht bestanden → **Mechanikänderung vor der Serie**. | – | PT8.01, D-3 |
| EP-L04 | W-7: Koexistenztest führt der Auftraggeber durch; bei Nichtbestehen Entscheid **XIAO als BLE-Empfänger**. | – | PT0.06, PT9.06, D-6 |

## Anhang A – Spezifikation Testfirmware (EP-15, Aufgabe Firmware vor Musterankunft)

Gemeinsam für alle Varianten: eigener Build-Schalter (z. B. `make TESTFW=TF-n`), **nur mit DEV-Schlüssel signiert**,
nie mit dem Produktionsschlüssel; Kennung in `GET_INFO` (fw_build mit Suffix `-tf<n>`) und Startsignal Rot/Grün
abwechselnd 3 × (ANNAHME, Muster in PROTOCOL 10.2 noch festzulegen), damit ein Testmuster nicht mit Werksfirmware
verwechselt wird. Einspielen vor dem Verguss per Weg B oder danach per OTA; weil OTA keine Downgrades annimmt (SEC_CNT,
ST-S7), braucht die Rückkehr zur Normalfirmware ein Image mit höherer Version (beide Images vorab bauen).

| Nr | Funktion | Für | Anforderungen an die Variante |
|---|---|---|---|
| TF-1 | **Watchdog-Test:** nach Tastersequenz (z. B. 5 × kurz) Endlosschleife ohne Watchdog-Bedienung | PT5.12 (T-W1, REQ-FW-07) | Neustart durch Watchdog; Grund in GET_DIAG; Zähler bleibt über den Neustart erhalten |
| TF-2 | **Fataler Fehler / Reset-Schleife:** auslösbarer fataler Fehler (Assert) nach Tastersequenz | PT11.07 (ST-F6, PP-11) | Firmware-Reaktion wie Serie (Abschaltung nach 3 Resets); NV-Schreibzahl je Zyklus in GET_DIAG |
| TF-3 | **SENS_PWR dauernd high:** DIO12 dauerhaft high, TMP1075N alle 60 s lesen, Ergebnis + Fehlerzähler I²C im Ringpuffer | PT11.19 (ST-W4) | sonst Normalbetrieb (Advertising, Messung) für die Datenübertragung; Ruhestrom-Mehrbedarf dokumentieren (Leck SENS_PWR–GND über Aufbau C) |
| TF-4 | **Diagnose-Ausgabe** (optional): Zähler meas/adv/conn/led_ms, charge_uc, Resetgrund, VDD-Minimum in GET_DIAG | PT6.16, PT11.07 | falls im Werks-Build schon vorhanden: entfällt |

Ausdrücklich **keine** Testfunktion für einen Dauer-Burst der Messkette (FW-2, Elektronik-Beitrag 3.6) und keine
Testbefehle im Funkprotokoll der Werksfirmware (Firmware-Beitrag T-W1).
