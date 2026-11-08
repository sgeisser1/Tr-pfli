# Phase 5 – Testplan-Beitrag Sicherheit (REQ-DOC-03)

| | |
|---|---|
| Verfasser | Sicherheits-Agent |
| Datum | 2026-11-08 |
| Zweck | Alle sicherheitsrelevanten **PROTOTYP-PRÜFUNGEN** für den Testplan der Projektleitung, mit Aufbau, Kriterium und Herkunft (FMEA-Nr. bzw. Befund) |
| Allgemein | Umgebung 20–25 °C (REQ-SAF-01). Zellstrom über Shunt bzw. Amperemeter im Mess-Zwischenadapter, **nie eine Quelle in Serie zur Zelle** (R2-A2). Temperatur mit Thermoelement an Zelle bzw. Bauteil. Abbruch bei Rauch, Geruch, Aufblähen oder > 60 °C an der Zelle (ANNAHME Abbruchgrenze, unter 85 °C Datenblatt). Neue Zellen ≥ 3.0 V; Zellen nach Fehlertests entsorgen. Zerstörende Tests nur an den Mustern, die die Projektleitung dafür bestimmt. |

## 1 Eingangsprüfung (vor der ersten Zelle, jedes Muster)

| ID | Test | Aufbau | Kriterium | Herkunft |
|---|---|---|---|---|
| ST-E1 | Sichtprüfung VIP-Pads im Fach | Lupe ≥ 10×, 4 Pads | keine Delle/Öffnung; ein Querschliff VBAT-VIP an der Opferplatine ohne Lunker | A-3 |
| ST-E2 | Stromaufnahme und Verpolung mit Labornetzteil | 3.0 V, Strombegrenzung **10 mA**, an Dummy-Scheibe; danach verpolt | richtig gepolt: Strom plausibel (≤ einige mA beim Start), kein Erwärmen; verpolt: ≤ 1 µA (AO3401A I_DSS) | F-03, F-64, B-3 |
| ST-E3 | Isolation VBAT–GND, TX/RX–GND ohne Zelle | 3 V, Pikoamperemeter bzw. Multimeter-Bereich | Wert protokolliert (Referenz für ST-W2) | A-4, F-61 |

## 2 Zelle, Clip, Versorgungspfad (REQ-SAF-01, -CC-01…03)

| ID | Test | Aufbau | Kriterium | Herkunft |
|---|---|---|---|---|
| ST-Z1 | **Verpolung 24 h** | Zelle verkehrt im Clip, Zellstrom und -temperatur | Strom ≤ 5 µA; keine Erwärmung; Funktion danach ok | REQ-SAF-CC-01, F-02 |
| ST-Z2 | **Schräg, halb, verkehrt, CR2025** | Zelle in jeder Fehllage, Zellstrom messen, Kontaktbild fotografieren | kein Kurzschluss (Strom ≤ Betriebsstrom), Becherrand berührt kein GND | R2-W01 Nr. 3, LS-W3, K-6, F-01 |
| ST-Z3 | **Kurzschluss am Zellausgang** | Clip-VBAT–GND hinter dem Clip kurzgeschlossen, 1 h | keine Flamme/kein Rauch/kein Aufblähen; Zelltemperatur 65 °C + ΔT ≤ 85 °C | REQ-SAF-01 |
| ST-Z4 | **Kurzschluss je Bauteil im Pfad** | nacheinander C1–C4 (Draht über das Bauteil), Q1 D–S | wie ST-Z3; Gehäusetemperatur 65 °C + ΔT ≤ HDT − 10 K | REQ-SAF-01, F-04 |
| ST-Z5 | **Rückstrom über TP1/TP2** | 3.3 V und 5 V an je einem Pad, ein 100 kΩ überbrückt; 5.5 V an beiden Pads; Zelle 3.0 V und entladene Zelle | ≤ 55 µA je Pad (CONCEPTS 2.7), Grenze 10 mA; Funktion danach | R2-A4, F-05 |
| ST-Z6 | Unterspannung | Quelle 2.0–2.4 V über R_int 100–300 Ω | definierte Abschaltung < 2.4 V, kein NV-Schreiben unter UV | FW-5, F-14 |

## 3 Verschluckschutz und Batteriewechsel (REQ-SAF-CC-04)

| ID | Test | Aufbau | Kriterium | Herkunft |
|---|---|---|---|---|
| ST-K1 | **Drehmoment ohne Werkzeug** | Hülse/Schraube mit Fingern, Drehmomentschlüssel 0.5 Nm | Fach öffnet nicht ohne Werkzeug | UL 4200A-Werte, `phase3_sleeve_sicherheit.md` |
| ST-K2 | **Zug 72 N** an der Hülse, geschlossen | Federwaage | Fach bleibt zu | ebd. |
| ST-K3 | **Druck 136 N** auf das Fach | Kraftmessung | kein Öffnen, kein Bruch, Zelle unzugänglich | ebd. |
| ST-K4 | Schraube vergessen | Hülse ohne Schraube aufgeschoben, Sensor schütteln und stecken | Ergebnis protokollieren; Anleitungstext entsprechend | F-21 |
| ST-K5 | Zelle im Clip beim Abziehen und Schütteln | Hülse ab, Sensor kopfüber, schütteln | Zelle bleibt im Clip | S3-W2, F-22 |
| ST-K6 | **50 Zellwechsel** | Standardablauf nach Anleitung | Clip-Lötstellen ohne Riss (Lupe), Kontakt ok, Schraube unverlierbar | K-4, F-24 |
| ST-K7 | Nach 65 °C / 168 h und 10 Wechseln: ST-K1…K3 wiederholen | Wärmeschrank | Kriterien weiter erfüllt | S3-W1 |
| ST-K8 | **Schraube M2 × 3 verliersicher** (Runde 3, R3-W1) | Schraube aus der Mutter drehen, Umdrehungen zählen bis Hülse frei; dann Hülse kopfüber schütteln; nach 50 Wechseln (ST-K6) wiederholen; zusätzlich: wie viele weitere Umdrehungen bis die Schraube aus der Lippe fällt | Hülse frei nach ≈ 3.5 U; Schraube bleibt beim Schütteln in der Lippe; Zahl der Umdrehungen bis zum Herausfallen protokolliert und in BATTERIEWECHSEL Schritt 2 übernommen | F-20, F-28 |

## 4 Wasser und Dichtung (REQ-SAF-05, REQ-MECH-08/13)

| ID | Test | Aufbau | Kriterium | Herkunft |
|---|---|---|---|---|
| ST-W1 | **Spritzwasser** | 1 l aus 20 cm, 10 ×, mit Zelle; auch nach 10 Wechseln | kein Wasser im Kopf (Sichtprüfung, Kondensat) | REQ-MECH-13, S3-W3, F-09, F-62 |
| ST-W2 | **Fach geflutet 24 h mit Zelle** | Leitungswasser, Zellstrom protokolliert | REQ-SAF-01-Kriterien; Isolation VBAT–GND, TX/RX–GND vorher/nachher | REQ-SAF-05, A-4, F-08 |
| ST-W3 | **Elektronikraum geflutet 24 h** (Opfermuster) | gezielt geöffnet | wie ST-W2 | REQ-SAF-05, F-09 |
| ST-W4 | **Kragen** | 50 Zyklen −10/+65 °C, 168 h 65 °C, je 24 h tauchen und Fach fluten; SENS_PWR dauernd high (Testfirmware); Schliff | Leckstrom SENS_PWR–GND ≤ 1 µA (ANNAHME); I²C ok; keine Lunker/Ablösung | K-7, F-10, F-60, F-63 |
| ST-W5 | Feuchteindikator im Kopf, 30 Tage nass | Sonde in nasser Erde | Indikator unverändert | REQ-MECH-08, F-11 |
| ST-W6 | **Taste/Membran und Zapfenwand** (Runde 3, R3-W2/W3) | (a) 10 ml Wasser auf die Taste, 20 × drücken, 1 h stehen lassen; (b) Fach bis über die Zapfen-O-Ring-Nut geflutet 24 h (Opfermuster: Kappe vorher mit Indikatorpapier im Elektronikraum über dem Schott bzw. nachher aufgeschnitten) | Elektronikraum trocken (Indikator unverändert); Ergebnis für O-4 (Klemmring-Befestigung) und die 0.54-mm-Wand protokollieren | F-65, F-66, REQ-UI-06 |

## 5 Mechanische Belastung

| ID | Test | Aufbau | Kriterium | Herkunft |
|---|---|---|---|---|
| ST-M1 | Axial 50 N mit geführter Spitze, seitlich 10 N, Zug 30 N | Kraftmessung | kein Bruch, keine bleibende Verformung | REQ-MECH-10, D-016 |
| ST-M2 | Tastendruck-Kraftfluss | Taster 100 × drücken, Zelle beobachten | Kraft nicht über die Zelle (REQ-SAF-LI-05 sinngemäss) | M-4 |
| ST-M3 | **Fall 1 m** (Kopf voran und flach), mit Zelle | harter Boden; Zellstrom vor/nach | Fach zu, Zelle im Clip, **Zellstrom unverändert** (kein MLCC-Riss) | REQ-MECH-10, F-04 |

## 6 Firmware, Funk, OTA

| ID | Test | Aufbau | Kriterium | Herkunft |
|---|---|---|---|---|
| ST-S1 | **MITM-Kopplung** mit Relais-Angreifer | Host-Test ≥ 10 000 Läufe und ein Funkversuch mit zwei Geräten | Erfolgsrate ≤ 1 %; jeder Fehlversuch rot sichtbar | F-K1, F-30 |
| ST-S2 | **Kopplung ohne Taster** | Gateway sendet PAIR_REQ an ungekoppelten Sensor ohne Tastendruck; zweiter Versuch nach Abbruch ohne Taster | Ablehnung (ERROR), kein Schlüssel gespeichert | REQ-RF-05, F-31 |
| ST-S3 | Lock mit DEV-Schlüssel bzw. falschem Fingerabdruck | `flash_sensor.py program --lock` | Werkzeug bricht vor dem Schreiben ab | F-W1, F-34 |
| ST-S4 | Replay und RNG-Fehler | aufgezeichnete Sitzung wiederholen; `port_sim` RNG-Fehler | Abweisung bzw. Abbruch | F-W4, F-32 |
| ST-S5 | **OTA mit falscher Signatur** | Image mit fremdem Schlüssel signiert, Bit im Image gekippt | Gateway lehnt ab (`signature_invalid`); direkt am Sensor eingespielt: MCUboot bootet es nicht, alte Version läuft | REQ-FW-04, F-33 |
| ST-S6 | OTA ohne konfigurierten Schlüssel | `fw_pubkey` leer | Gateway nimmt kein Image an | F-33 |
| ST-S7 | Downgrade | älteres Image mit gleichem bzw. kleinerem SEC_CNT | abgelehnt | F-L1, F-36 |
| ST-S8 | OTA-Abbruch | Funk trennen bei 50 %; Unterspannung während OTA | Sensor läuft weiter mit alter Version; Rückfall nach 24 h ohne Bestätigung | REQ-FW-03, F-37 |
| ST-S9 | Serien-CCFG (PP-9) | nach `--lock`: SWD/SACI-Programmierversuch, ROM-Bootloader mit Taster | scheitert; OTA und Sicherheitszähler funktionieren weiter | F-W2, F-38 |
| ST-F6 | Reset-/Weckschleifen (PP-11) | EOL-Quelle mit Einbruch unter POR, Taster dauernd gedrückt, fataler Fehler | Mittelstrom ≤ 10 × Ruhestrom (ANNAHME), NV-Schreibzahl je Zyklus protokolliert, Abschaltung nach 3 Resets | F-W3, N-2 |

## 7 Gateway und LAN

| ID | Test | Aufbau | Kriterium | Herkunft |
|---|---|---|---|---|
| ST-N1 | Schreibrouten ohne Sitzung | Skript: alle `POST/PUT/PATCH/DELETE` aus `api.ROUTES` ohne Cookie/CSRF | 401/403, keine Änderung | REQ-SAF-NET-01, F-40 |
| ST-N2 | Brute Force | 10 falsche Passwörter | Sperre ab dem 5. Versuch | F-41 |
| ST-N3 | **Portscan** im Auslieferungszustand | `nmap -p-` vom LAN | nur dokumentierte Ports (HTTPS, Dashboard 8080 falls an), kein SSH | REQ-SAF-NET-02, F-42 |
| ST-N4 | Name Constraint | mit dem Zertifikat einen anderen Namen signieren lassen bzw. prüfen | Handy/Browser lehnt ab | REQ-SAF-NET-04, F-43 |
| ST-N5 | Dashboard nur lesen | Schreibversuch über Port 8080 | abgelehnt | D-022 |
| ST-G1 | **RTC-Pufferzelle: kein Ladestrom** | Amperemeter in Serie zur RTC-Zelle, Gateway an | Strom in die Zelle ≤ 0 (nur Entladung) | F-45 |
| ST-G2 | Gateway-Temperatur 24 h im Gehäuse | Volllast, Raum 25 °C; **zusätzlich Thermoelement an der CR1220** (Runde 3) | Pi ohne Drosselung, Netzteil handwarm; CR1220 innerhalb des Temperaturbereichs ihres Datenblatts mit ≥ 10 K Reserve (ANNAHME Reserve) | F-46, F-49 |
| ST-G3 | **CR1220 im Deckel gesichert** (Runde 3) | Gateway geschlossen 1 m Fall auf Holz; Deckel abnehmen und kopfüber schütteln | Zelle bleibt im Halter; Deckel nur mit Innensechskant-Schlüssel zu öffnen | F-48 |

## 8 Programmieradapter und Behelf

| ID | Test | Aufbau | Kriterium | Herkunft |
|---|---|---|---|---|
| ST-P1 | **Einteiligkeit / Zwangsfolge** (Runde 3: Bügel + unverlierbare Schwinge) | Adapter mit und ohne Zelle ansetzen; Dummy verkehrt; Dummy 2, 4, 6 mm vor der Endlage; mit eingesetzter CR2032 versuchen, die Stifte von Hand auf TP1/TP2 zu bringen; Schwinge und Gegenhalter ohne Werkzeug abzuziehen versuchen (Zug 20 N, ANNAHME) | (a) Stifte erreichen TP1/TP2 nur mit Dummy ganz im Clip, Gegenhalter schliesst vorher nicht; (b) mit Adapter passt keine Zelle; (c) verkehrt kein Kontakt; (d) Schott unbelastet; (e) mit Zelle im Clip kein Stiftkontakt und keine Berührung Dummy ↔ Zelle/Clip; (f) Schwinge/Gegenhalter nicht abnehmbar; (g) in Offenstellung ≥ 1 mm Luft Stift ↔ Clip | PS-W1, F-07, Runde 3 |
| ST-P2 | Dummy-Dicke und Isolation | Messschieber; Ober-/Unterseite | 3.0–3.2 mm; > 10 MΩ | PS-W3, README Kap. 7 |
| ST-P3 | Kurzschluss VDD_DUT 60 s | Dummy-Flächen überbrückt | U1/U2-Temperatur protokolliert; kein Rauch | PS-L1, F-50 |
| ST-P4 | VIO-Fehler | Jumper H3 gesteckt, ohne Sensor | Prüfschritt 2 erkennt den Fehler (VIO ≠ 2.0 V) | PS-L2, F-51 |
| ST-P5 | Weg B Ablauf | nach PS-K1: Scheibe im Clip, Reihenfolge Netzteil weg → Scheibe raus → Draht weg → Zelle | Draht entfernt (Foto), VIP-Pads unversehrt (ST-E1) | PS-K1, PS-W2, PS-W4 |
| ST-P6 | **Bootloader-Strom** | Zelle bzw. 3.0 V mit Taster beim Einschalten, Strom messen | Wert dokumentiert; daraus Zeit bis leer; Entscheid PS-W5 | W-10, F-16 |

## 9 Reihenfolge (Vorschlag)

1. ST-E1…E3 an allen Mustern; ST-P1/P2/P5 vor der ersten Programmierung.
2. Nicht zerstörend an allen Mustern: ST-Z1, ST-Z2, ST-Z5, ST-K1…K6, ST-S*, ST-N*.
3. Ein Opfermuster: ST-Z3, ST-Z4, ST-W3, ST-W4 (Schliff), ST-M3.
4. Langzeit: ST-W5 (30 Tage), ST-K7.
