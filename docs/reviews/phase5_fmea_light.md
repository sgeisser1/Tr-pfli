# Phase 5 – FMEA-light System fluidi (REQ-SAF-02, REQ-SAF-01)

| | |
|---|---|
| Verfasser | Sicherheits-Agent |
| Datum | 2026-11-08, Stand git `b77b29a`; **Runde 3** (Stand `cedccd5`, Anleitungen, Rev-C-Schraube, Kappe P5, Gateway-RTC): Änderungen mit „R3“ markiert, Bericht `phase5_sicherheit_runde3.md` |
| Umfang | Sensor Rev C (CR2032, Clip Keystone 3034, Q1 AO3401A), Gateway Pi Zero 2 W, Firmware/Funk/OTA, Programmieradapter Rev 1 und Behelf, Montage/Verguss, Batteriewechsel, Nutzung im Haushalt |
| Grundlage | `docs/reviews/phase1…phase4_*sicherheit*`, `phase4_redteam_gesamt.md`, `phase5_programmer_sicherheit.md`, `docs/requirements/DECISIONS.md`, `REQUIREMENTS.md` v1.1, `docs/concepts/CONCEPTS.md` 2.7/2.8 |
| Hinweis | S/O/D sind **Expertenschätzungen (ANNAHME)**. Sie werden am Muster mit den Tests aus `phase5_testplan_beitrag_sicherheit.md` überprüft. Diese Datei ersetzt den in Phase 2 genannten Platzhalter `docs/reviews/FMEA.md`. |

## 1 Skalen

**S – Schwere der Folge**

| S | Bedeutung |
|---|---|
| 10 | Brand, Explosion oder Verletzung ohne Vorwarnung |
| 9 | Verschlucken einer Knopfzelle möglich; Brand/Leck einer Zelle mit Vorwarnung; Laden einer Primärzelle > 10 mA |
| 8 | Zelle wird geladen (≤ 10 mA) oder überhitzt ohne Flamme; Schutzfunktion umgangen (fremde Firmware läuft) |
| 7 | Unbefugter steuert Sensor/Gateway; dauerhafter Geräteschaden mit Restgefahr |
| 6 | Sensor dauerhaft defekt, Austausch nötig; Datenverlust |
| 5 | Ausfall, behebbar durch Zellwechsel bzw. Neuprogrammierung; falscher Giesshinweis über Tage |
| 4 | Funktionsminderung (Messdrift, Reichweite) |
| 3 | Komforteinbusse |
| 2 | kosmetisch |
| 1 | keine Auswirkung |

**O – Auftreten** (je Sensor und Nutzungsjahr bzw. je Vorgang wie Wechsel oder Programmierung)

| O | Bedeutung |
|---|---|
| 1 | konstruktiv ausgeschlossen, nachgewiesen |
| 2 | nur als Doppelfehler bzw. < 1 : 10 000 |
| 3 | < 1 : 1000 |
| 4 | < 1 : 200 |
| 5 | < 1 : 50 |
| 6 | < 1 : 20 |
| 7 | < 1 : 10 |
| 8 | < 1 : 3 |
| 9–10 | fast sicher |

**D – Entdeckung, bevor die Folge eintritt**

| D | Bedeutung |
|---|---|
| 1 | sicher, automatisch (Werkzeug bricht ab, Firmware verweigert) |
| 2–3 | sehr wahrscheinlich (Pflichtmessung in der Anleitung, Selbsttest mit Anzeige) |
| 4–5 | wahrscheinlich (Sichtprüfung, Funktionstest mit L11) |
| 6–7 | unwahrscheinlich (nur indirekt, z. B. kurze Laufzeit) |
| 8–9 | kaum (verborgen im Verguss, Nutzer bemerkt nichts) |
| 10 | nicht erkennbar |

**RPZ = S × O × D.** Eine zusätzliche Massnahme ist Pflicht bei RPZ ≥ 100 **oder** S ≥ 9 mit O ≥ 3. Bei S ≥ 9 ist
das Restrisiko immer einzeln zu begründen.

Fachbereiche: **SI** Sicherheit, **EL** Elektronik/Layout, **ME** Mechanik, **FW** Firmware Sensor, **GW**
Gateway/Software, **FE** Fertigung, **PL** Projektleitung/Anleitungen, **AG** Auftraggeber.

## 2 FMEA

### 2.1 Sensor – Energiequelle und Versorgungspfad

| Nr | Fehlerart | Ursache | Folge | S | O | D | RPZ | Bestehende Massnahme (Nachweis) | Zusätzliche Massnahme | FB |
|---|---|---|---|---|---|---|---|---|---|---|
| F-01 | Kurzschluss der Zelle im Clip | Zelle schräg, halb oder verkehrt eingesetzt; Becherrand (+) berührt GND | Zellerwärmung, Leck | 8 | 3 | 6 | 144 | TP3 entfällt, im Fach nur Minuspad 4 × 4 mittig (`phase4_layout_revb_sicherheit.md` A-1, LS-W2); B-Seite ohne Pads (PCB_OUTLINE Z4) | Test ST-Z2 (schräg, halb, verkehrt, CR2025; Zellstrom, Red-Team K-6); Bild zur Einschubrichtung in der Anleitung | SI/ME/PL |
| F-02 | Zelle verpolt eingesetzt | Bedienfehler | Rückstrom in die Elektronik | 6 | 4 | 4 | 96 | Q1 AO3401A G = GND, S = VDD, D = VBAT (`phase4_layout_revb_sicherheit.md` Kap. 4, `AOS_AO3401A_Datasheet_Rev3.1.pdf` S. 1) | Verpoltest 24 h (ST-Z1, REQ-SAF-CC-01) | SI |
| F-03 | Verpolschutz wirkungslos | Q1 von JLC um 180° bzw. 90° verdreht bestückt (Rotation nur aus Drittquelle) | Verpolte Zelle speist Elektronik rückwärts | 7 | 3 | 4 | 84 | Abhakliste „Confirm Parts Placement“ (`ORDER_JLC_REV_C.md` Kap. 5, B-3) | Eingangsprüfung je Muster: Verpolung mit Labornetzteil 3.0 V / 10 mA vor der ersten Zelle (ST-E2) | FE/SI |
| F-04 | Kurzschluss hinter Q1 | Biegeriss eines 1206-MLCC (C1–C4) nach Fall oder Sondenbiegung | Zelle über Q1 (leitend) kurzgeschlossen, Erwärmung im Band | 8 | 3 | 7 | **168** | FEM Fall 1 m SF 1.71 (`simulation/fem/REPORT.md` Kap. 5); Platzierungsregeln S2-W02 (CONCEPTS) | Falltest mit Zellstrommessung vor/nach (ST-M3); Rev D prüfen: MLCC mit Soft-Termination bzw. Ausrichtung quer zur Biegelinie | EL/ME |
| F-05 | Zelle wird über TP1/TP2 geladen | fremde Quelle an den Pads, ein Widerstand überbrückt | ≤ 55 µA Ladestrom (Grenze 10 mA, 1 % C) | 8 | 2 | 8 | 128 | 2 × 100 kΩ je Leitung im Band, R2-A3 (CONCEPTS 2.7 Tab., `simulation/spice/README.md` (c)) | Test R2-A4 (ST-Z5); Restrisiko akzeptiert (Faktor ≥ 180 zur Grenze) | SI |
| F-06 | Zelle wird vom Labornetzteil geladen (Behelf Weg B) | Zelle eingesetzt, während das Netzteil noch am Clip hängt; Zelle tiefentladen bzw. Netzteil falsch eingestellt | bis 20 mA Ladestrom > 10 mA (Maxell S. 2) → Leck, Brand | 9 | 5 | 7 | **315** | Regel 1 in `PROGRAMMIEREN_SENSOR.md` (nur Verhalten) | **VETO PS-K1**: Weg B nur mit Dummy-Scheibe (Clip belegt), Reihenfolge Netzteil weg → Scheibe raus → Zelle; tiefe Zellen entsorgen. Danach O = 1 → RPZ 63 | PL/SI |
| F-07 | Zelle und Adapter gleichzeitig (Weg A) | Adapter nicht einteilig gebaut | Laden über U2 (2.0 V, 130 mA) | 9 | 2 | 5 | 90 | Konzept R2-A2, Dummy belegt den einzigen Clip (`hardware/programmer/README.md` 2.3); R3: Konstruktion „Bügel fest am Dummy + unverlierbare Schwinge mit Gegenhalter“ (README Kap. 4) als Erfüllung von PS-W1 **unter Auflagen PS-W1/A1…A5** akzeptiert | Nachweis ST-P1 (a)–(g) vor Freigabe des Adapters | ME/SI |
| F-08 | Leckstrom VBAT–GND im Fach | Wasser im Fach (Flutung), CAF entlang der Kante | Zellentladung, Korrosion | 6 | 4 | 6 | 144 | POFV-Via-in-Pad (D-023, A-2), Innenlagen ≥ 1.0 mm zur Kante (K-3), Abstand VBAT–GND 0.30 mm (LS-K2) | Flutung 24 h mit Zelle und Isolationsmessung (ST-W2, A-4); LS-K2 (VBAT ≥ 0.5 mm) für Rev D | EL/SI |
| F-09 | Wasser im Elektronikband | Schottverguss undicht, O-Ring fehlt oder ist verdreht | Leckströme hinter Q1, Korrosion, Ausfall | 6 | 3 | 7 | 126 | Schott als fester Verguss (S3-K1), zwei radiale Dichtungen (S3-W3) | Spritzwasser nach REQ-MECH-13 mit Zelle (ST-W1); Flutung Elektronikraum (ST-W3) | ME |
| F-10 | Wasser im Kragen | Lunker oder Ablösung an U3/Taschenwand | TMP-Ausfall, Leckstrom SENS_PWR | 4 | 4 | 5 | 80 | K-1…K-7 (`phase4_sicherheit_kragen_firmware.md`), am Board verifiziert (`phase4_layout_revb_sicherheit.md` Kap. 3) | Kragentest K-7 (ST-W4), Schliff | ME |
| F-11 | Feuchte kriecht entlang der Sonde | Schnittkante unversiegelt (REQ-MECH-07 offen) | Drift, Feuchte im Kopf | 5 | 5 | 6 | **150** | Keine Vias im Nassbereich, Kupfer ≥ 1.25 mm zur Kante (Red-Team Kap. 2) | Versiegelungsverfahren wählen und belegen (W-5), Feuchteindikator im Kopf (REQ-MECH-08, ST-W5) | ME/PL |
| F-12 | Zelle zu warm | Fensterbank, Sonne, Heizkörper (65 °C) | Selbstentladung, Leck | 7 | 2 | 3 | 42 | CR2032 −30…+85 °C, ab 70 °C Rücksprache (`Panasonic_CR2032_Datasheet_2026-02.pdf` S. 1); ASA HDT ≥ 80 °C (REQ-MECH-12) | Anleitung: nicht auf den Heizkörper, keine direkte Sonne (R3: fehlt noch in `BATTERIEWECHSEL.md`, R3-K2); OP-K7 (Panasonic-Anfrage) offen | PL |
| F-13 | Zelle am Lebensende im Gerät | Nutzer wechselt nicht | Tiefentladung, Leck im Fach | 6 | 3 | 5 | 90 | UV-Abschaltung < 2.4 V (FW-5), App-Warnung bei < 30 Tagen (Red-Team Kap. 5); R3: `BATTERIEWECHSEL.md` „Wann wechseln?“ | – (umgesetzt) | PL |
| F-14 | Reset-/Weckschleife am Zellende | Brownout, klemmender Taster | Zelle schnell leer, NV-Verschleiss | 5 | 3 | 6 | 90 | F-W3 umgesetzt: AON-Zähler, 2.6-V-Schwelle, Taster-Wecken aus (`phase4_sicherheit_kragen_firmware.md` Runde 2) | PP-11 mit Einbruch unter POR (N-2), ST-F6 | FW |
| F-15 | Spannungseinbruch beim Senden | R_int der Zelle hoch, Puffer zu klein | Brownout, Datenverlust | 4 | 4 | 5 | 80 | 4 × 100 µF im Prototyp, 143 mV (D-013) | Leckmessung C1–C4 und Entscheid 2/4 (W-6) | EL |
| F-16 | Bootloader-Fehlstart (Muster) | Taster beim Einsetzen der Zelle gedrückt (W-10) | Zelle in 2–12 Tagen leer, Muster wirkt tot | 5 | 6 | 4 | 120 | Anleitung Kap. 6 und L11-Kontrolle (`PROGRAMMIEREN_SENSOR.md`); Serie: `--lock` | Strom messen (ST-P6); L11-Prüfung in der Musterliste; Option Trigger-Pin (PS-W5) | FW/PL |

### 2.2 Batteriewechsel und Nutzung im Haushalt

| Nr | Fehlerart | Ursache | Folge | S | O | D | RPZ | Bestehende Massnahme (Nachweis) | Zusätzliche Massnahme | FB |
|---|---|---|---|---|---|---|---|---|---|---|
| F-20 | Kind gelangt an die Zelle | Fach ohne Werkzeug geöffnet | Verschlucken | 9 | 2 | 8 | 144 | R3: Schraube **ISO 7045 M2 × 3 A2 PH1** (Rev C, V-K/D-023; `docs/datasheets/INDEX.csv` MECH-SCR1 (Rev C); ersetzt M2 × 4) in eingegossener Mutter ISO 4032 M2 (K-6), Einschraubtiefe 1.4 mm = 3.5 Gänge ≥ 2 Gänge (`mechanical/sensor/check_sensor.txt` 5c; Massstab S3-W1); Furchlippe Ø 1.7 × 0.5 im Hülsenboden (`fluidi_params.py` SCREW); Warnsymbol innen (`docs/design/P3_FLUIDI.md`, S3-W4) | Prüfung 0.5 Nm / 90°, Zug 72 N, Druck 136 N (UL 4200A-Werte aus `phase3_sleeve_sicherheit.md`), ST-K1…K3; Verliersicherheit ST-K8 (F-28) | ME/SI |
| F-21 | Schraube nicht angezogen | Nutzer vergisst sie nach dem Wechsel | Hülse lose, Zelle zugänglich | 9 | 2 | 6 | 108 | Schraube verliersicher (F-28); R3: Pflichtschritt umgesetzt (`BATTERIEWECHSEL.md` Schritt 10/11, `MONTAGE_SENSOR.md` Prüfung 7) → O 3 → 2 | Test, ob die Hülse ohne Schraube abfällt bzw. hält (ST-K4) | PL/ME |
| F-22 | Zelle fällt beim Abziehen heraus | Clip hält nicht, Noppe fehlt | Zelle rollt weg, Verschlucken, Kurzschluss auf Metall | 9 | 3 | 5 | **135** | Haltenoppe, Einschub +X (S3-W2); R3: Schale in `BATTERIEWECHSEL.md` Schritt 2 umgesetzt | Schütteltest ST-K5 (danach O = 2 → 90) | ME/PL |
| F-23 | Ersatz- bzw. Altzellen lose gelagert | Nutzer ignoriert die Anleitung | Verschlucken, Kurzschluss | 9 | 2 | 8 | 144 | R3: `BATTERIEWECHSEL.md` „Zuerst lesen“: Lagerung in Originalverpackung, ausser Reichweite, Altzelle sofort abkleben und zur Sammelstelle, ärztliche Hilfe bei Verdacht (Renata Safety Guidelines Rev. 10/02 S. 1) → O 4 → 2 (vorher 288) | Notrufnummern 144 / Tox Info Suisse 145 ergänzen (R3-K1). Restrisiko (S 9, O 2): Verhalten des Nutzers, Eigengebrauch Büro, vertretbar | PL |
| F-24 | Clip-Lötstelle reisst | Pads am Katalogminimum (K-4), Hebeln mit Werkzeug, zu dicker Dummy (PS-W3) | Clip lose, Wackelkontakt, Kurzschluss | 7 | 3 | 6 | 126 | Pad-Spanne 23.10 mm (LS-W1) | 50 Wechsel (ST-K6); Dummy 3.0–3.2 mm; Anleitung: kein Metallwerkzeug (S3-L1) | ME/FE |
| F-25 | Haustier zerbeisst den Kopf | Hund, Katze | Zelle zugänglich | 9 | 2 | 7 | 126 | ASA, Zelle hinter Schraube; R3: Hinweis in `BATTERIEWECHSEL.md` umgesetzt | Restrisiko akzeptiert (Eigengebrauch Büro) | PL |
| F-26 | Verletzung an der Sondenspitze | spitzer Stab 100 mm | Stichverletzung | 4 | 3 | 2 | 24 | R3: Hinweis in `BATTERIEWECHSEL.md` | – | PL |
| F-28 | **R3:** Schraube geht verloren | ISO 7045 ist vollgewindig: nach 3.5 U aus der Mutter steckt sie noch in der 0.5-mm-Furchlippe (z 0…0.5, Schaft z −1.4…1.6); weiteres Drehen (≈ 4 U, Rechnung aus `fluidi_params.py` SCREW, `check_sensor.txt` 5c) schraubt sie aus der Lippe. `BATTERIEWECHSEL.md` Schritt 2 „lösen, bis sie frei dreht“ führt genau dahin; Lippe verschleisst über Wechsel | Betrieb ohne Schraube (→ F-21), Kleinteil lose | 9 | 3 | 5 | **135** | Furchlippe Ø 1.7 | Text ändern (R3-W1): „etwa 4 Umdrehungen, bis sich die Hülse abziehen lässt; nicht weiter drehen“; Ersatzschraube beilegen, Anleitung: ohne Schraube Sensor nicht benutzen; ST-K8. Danach O = 2 → 90 | PL/ME |
| F-27 | Falscher Giesshinweis | Kalibrierung ANNAHME, Salz, Sensor tot ohne Meldung | Pflanze leidet | 4 | 5 | 5 | 100 | Ausbleibende Werte → Warnung; D-018 Salzhinweis | Kalibrierung am Muster (Testplan) | GW |

### 2.3 Firmware, Funk und OTA

| Nr | Fehlerart | Ursache | Folge | S | O | D | RPZ | Bestehende Massnahme (Nachweis) | Zusätzliche Massnahme | FB |
|---|---|---|---|---|---|---|---|---|---|---|
| F-30 | MITM bei der Kopplung | Angreifer im Funkbereich | Fremder steuert Sensor, falsche Werte | 7 | 2 | 6 | 84 | Protokoll v2 mit Commitment, 1/243 je Versuch (VETO F-K1 aufgehoben, `phase4_sicherheit_kragen_firmware.md` Runde 2); Gateway v2 (`firmware/gateway/fluidi_gw/central.py` PAIR_REVEAL) | ST-S1 Relais-Test; Interop G-1 in der Gateway-Sicherheitsprüfung bestätigen | FW/GW |
| F-31 | Kopplung ohne Taster | Firmwarefehler | ungewollte Kopplung | 7 | 2 | 3 | 42 | Schlüssel nur bei Taster **und** CONFIRM_G (Runde 1 2.1) | ST-S2 | FW |
| F-32 | Replay einer Sitzung | RNG liefert Fehler | Befehle wiederholbar | 6 | 2 | 3 | 36 | F-W4 umgesetzt | ST-S4 (RNG-Fehler in `port_sim`) | FW |
| F-33 | Fremde Firmware wird installiert | falsche Signatur, Schlüssel geleakt | Schutzfunktionen (UV, LED-Pulse) ausser Kraft | 8 | 2 | 2 | 32 | MCUboot EC256, Prüfung auch im Gateway (`fluidi_gw/mcuboot.py` Z. 97–108) | ST-S5/ST-S6 | FW/GW |
| F-34 | Serie mit DEV-Schlüssel gesperrt | Bedienfehler | jeder kann signieren, dauerhaft | 8 | 2 | 1 | 16 | `check_lock_key`, Fingerabdruck im Hex-Namen (F-W1) | ST-S3 | FW |
| F-35 | Produktionsschlüssel gelangt ins Repo | Datei im Arbeitsbaum, `git add -A` | Signierschlüssel öffentlich | 8 | 3 | 4 | 96 | `firmware/sensor/.gitignore` `*.pem` ausser `DEV_ONLY_*`; `make release` weist Schlüssel im Repo ab (F-W1) | Globale `.gitignore`-Regel (`*.pem`, `*.key`, `*.p8`, `*.p12`) im Wurzelverzeichnis; Schlüssel nur offline (Checkliste CK-L1) | FW/PL |
| F-36 | Downgrade auf alte Version | altes signiertes Image | bekannte Lücke wieder offen | 6 | 2 | 2 | 24 | Sicherheitszähler, `ih_ver`-Prüfung (F-L1) | ST-S7 | FW |
| F-37 | OTA-Abbruch | Funkabriss, Unterspannung | Sensor ohne Firmware | 5 | 3 | 2 | 30 | Swap-using-move, Rückfall nach 24 h, Abbruch bei UV (Runde 1 2.1) | ST-S8 | FW |
| F-38 | SWD/SACI-Zugriff in der Serie | CCFG-Sperre wirkt nicht | Firmware auslesbar oder änderbar | 6 | 2 | 6 | 72 | F-W2 umgesetzt (PERM, WEPRA) | PP-9 (ST-S9) | FW |

### 2.4 Gateway

| Nr | Fehlerart | Ursache | Folge | S | O | D | RPZ | Bestehende Massnahme (Nachweis) | Zusätzliche Massnahme | FB |
|---|---|---|---|---|---|---|---|---|---|---|
| F-40 | Schreibzugriff ohne Anmeldung | Route ohne Auth | Fremder ändert Einstellungen, startet OTA | 7 | 2 | 4 | 56 | Route-Standard `auth="write"`, OTA/Netz/Backup `elevated` (`fluidi_gw/api.py` Z. 29 ff.) | ST-N1 (alle Schreibrouten ohne Sitzung → 401/403) | GW |
| F-41 | Passwort erraten | Brute Force | wie F-40 | 7 | 2 | 4 | 56 | Sperre nach 5 Fehlversuchen, global 20/min (`fluidi_gw/server.py` Z. 42) | ST-N2 | GW |
| F-42 | SSH bleibt offen | Installationsschritt ausgelassen | Fernzugang | 7 | 3 | 4 | 84 | SSH nur bei der Einrichtung (D-022) | Portscan (ST-N3, REQ-SAF-NET-02) | GW |
| F-43 | CA missbraucht | CA-Schlüssel erhalten, keine Namensbeschränkung | Handy vertraut fremden Seiten | 7 | 2 | 5 | 70 | CA nur im RAM, danach verworfen; Name Constraint `fluidi.local` (`fluidi_gw/pki.py` Z. 36–57) | ST-N4 (Zertifikat für anderen Namen wird abgelehnt) | GW |
| F-44 | Gateway-Netzteil überhitzt | ungeprüftes Netzteil | Brand am Netzteil | 9 | 2 | 6 | 108 | – (REQ-SAF-DOC-02, Einkaufsliste fehlt, W-8) | Einkaufsliste mit geprüftem Netzteil (CE, Hersteller) | GW/PL |
| F-45 | RTC-Pufferzelle wird geladen | RTC-Breakout mit Ladeschaltung (bei billigen DS3231-Modulen verbreitet, **ANNAHME**) | Knopfzelle (CR1220) wird geladen → Leck, Brand | 9 | 1 | 6 | 54 | Vorgabe „RTC ohne Ladepfad“ (OP-GW-3, S2-W06). Kandidat **Adafruit 4282**: Netz VBAT nur B1(+) und IC2 VBAT, keine Diode, kein Widerstand von 3.3 V/5 V (von mir aus `docs/datasheets/Adafruit_4282_PiRTC-DS3231_Schematic_2021-02-22.sch` ausgewertet); DS3231 „UL recognized to ensure against reverse charging“, IBATLKG 25/100 nA (`Maxim_DS3231_Datasheet_19-5170Rev10.pdf` S. 9 Pin 14, S. 2) | Nur diesen Typ verwenden, keine Nachbauten; ST-G1. Bei einem Typwechsel O = 4, RPZ 216 → neue Prüfung | GW/SI |
| F-46 | Pi überhitzt im Gehäuse | geschlossenes Gehäuse, Sonne | Abschaltung, SD-Schaden | 4 | 4 | 4 | 64 | belüftete Kammer Klima (D-017) | Temperaturtest 24 h (ST-G2) | ME/GW |
| F-47 | Datenverlust | SD-Karte defekt | Historie weg | 4 | 5 | 4 | 80 | Backup/Restore (REQ-GW-06) | Backup-Erinnerung | GW |
| F-48 | **R3:** Kind gelangt an die RTC-Zelle CR1220 | Deckel geöffnet, Zelle beim Wechsel oder lose Ersatzzelle | Verschlucken (Ø 12 mm, kleiner als CR2032) | 9 | 2 | 8 | 144 | Deckel nur mit Werkzeug: 4 × M2.5 × 8 ISO 7380 (Innensechskant) von unten in Einsätze (`mechanical/gen/fluidi_gateway_pi.py` Z. 32, 213; `check_gateway_pi.txt` 3) | Auflagen G-R1…G-R5 (`phase5_sicherheit_runde3.md`): Warnhinweise in `GATEWAY_SETUP.md`, Zelle beim Öffnen gesichert (ST-G3), Wechsel ohne Lösen der Klebung | PL/ME/GW |
| F-49 | **R3:** CR1220 zu warm | Gateway-Innenraum ΔT 11–34 K bei 1–3 W (`check_gateway_pi.txt` 8, ANNAHME h), RTC oben im Deckel; Temperaturbereich der Zelle **unbekannt** (kein Datenblatt, INDEX GW-RTC-CELL) | Selbstentladung, Leck | 7 | 3 | 6 | 126 | – | Marke festlegen und Datenblatt ablegen (G-R1); Temperatur an der Zelle messen (ST-G2) | GW/SI |

### 2.5 Programmieradapter und Behelf

| Nr | Fehlerart | Ursache | Folge | S | O | D | RPZ | Bestehende Massnahme (Nachweis) | Zusätzliche Massnahme | FB |
|---|---|---|---|---|---|---|---|---|---|---|
| F-50 | Kurzschluss VDD_DUT | Dummy-Flächen überbrückt, Litze beschädigt | U2 0.43 W > Pd 250 mW (Torex S. 3/5), heisses SOT-23 | 4 | 3 | 5 | 60 | Foldback U2 | ST-P3, ggf. PTC (PS-L1) | EL |
| F-51 | VIO 3.3/5 V | Jumper H3 gesteckt, J1 vertauscht | U4 > 4.6 V zerstört, Pegel am Sensor > VDDS | 4 | 5 | 3 | 60 | Prüfschritt VIO messen (README Kap. 7) | kodierte Steckverbindung (PS-L2) | EL |
| F-52 | Behelfsdraht bleibt nach dem Programmieren | Nacharbeit vergessen | Barriere 2 auf TX dauerhaft überbrückt | 8 | 3 | 5 | 120 | Schritt 9 (Sichtprüfung) | Foto- und Listennachweis je Muster (PS-W4) | PL |
| F-53 | VIP-Kappe beschädigt | spitzer Federstift, Löten auf Pads | offener Wasserpfad im Fach | 6 | 4 | 6 | 144 | – | flache Stifte, keine Lötung auf Fach-Pads, Sichtprüfung (PS-W2) | ME/PL |
| F-54 | Dummy zu dick | 2 × 1.6 mm FR4 + Cu + Kleber | Clip überdehnt → F-24 | 6 | 4 | 5 | 120 | – | Dicke 3.0–3.2 mm messen (PS-W3) | ME |

### 2.6 Montage und Verguss

| Nr | Fehlerart | Ursache | Folge | S | O | D | RPZ | Bestehende Massnahme (Nachweis) | Zusätzliche Massnahme | FB |
|---|---|---|---|---|---|---|---|---|---|---|
| F-60 | Lunker im Schott- bzw. Kragenverguss | Vergussmasse ohne Datenblatt, Luft | Wasserpfad zu Elektronik bzw. Zelle | 6 | 3 | 6 | 108 | Vergussreihenfolge (PCB_OUTLINE Kap. 7), K-4 ein Epoxid | ~~Vergussmasse mit Datenblatt wählen (W-5)~~ **erledigt Phase 6:** ER2223 mit TDS/SDB (Vorschlag D-030, `docs/concepts/vergussmasse_versiegelung.md`), 800 mPa·s, Vorversuch V-1 (Schnitt); **neu bewertet S6/O3/D6 = RPZ 108** (Sicherheit Runde 2, 2026-11-09, `phase6_vergussmasse_sicherheit.md` R2.3; vorher O5 = 180), nach V-1 erneut bewerten; Montageanleitung Kap. 3a/4/5; Schliff am Opfermuster (ST-W4, A-2) | ME/PL |
| F-61 | Flussmittelreste unter dem Verguss | keine Reinigung | Kriechstrom, Ablösung | 5 | 4 | 6 | 120 | K-5 (Reinigung) | Reinigungsschritt in der Montageanleitung mit Prüfung (Isolationsmessung ST-E3) | PL |
| F-62 | O-Ring falsch montiert | verdreht, ungefettet | Spritzwasser im Kopf | 6 | 4 | 5 | 120 | Silikonfett (PRINT_SETTINGS Kap. 5) | Sichtprüfung „O-Ring verpresst“ in der Anleitung; ST-W1 nach 10 Wechseln | ME |
| F-63 | Verguss reisst bei Wärme | Tg zu tief, CTE-Unterschied | Wasserpfad | 6 | 4 | 4 | 96 | **S6/O4/D4 = RPZ 96** (Sicherheit Runde 2, 2026-11-09, `phase6_vergussmasse_sicherheit.md` R2.3; vorher O3/D6 = 108; O → 3, RPZ 72 nach Tg-Nachweis W-2). ER2223 ungefüllt (CTE 70), **Abweichung K-4 nach D-030** (Sicherheit: zulässig unter A-1…A-5); Tg 140 °C laut TDS, Härtebedingung unbekannt | Zyklentest K-7 an ≥ 2 Mustern (A-1), Schliff/Farbeindringprüfung an der Kragenunterkante (A-2), Rückfallmasse (A-3); Tg-Nachweis vor Serie (W-2: Electrolube bzw. Kriechprobe V-6). O/D-Neubewertung durch Sicherheit nach Rückmeldung (A-4) | ME |
| F-64 | Bauteil verdreht bestückt | Rotation aus Drittquelle (W-3) | Kurzschluss V+/GND (U3 180°), Ausfall | 6 | 3 | 4 | 72 | Abhakliste B-3; R3: `BESTELLEN_JLC.md` Schritt 8 (ORDER Kap. 5 Teil für Teil, Q1 Zeile 121) | Stromaufnahme bei 3.0 V / 10 mA vor der ersten Zelle (ST-E2); in `BESTELLEN_JLC.md` Schritt 13 ausdrücklich nennen (R3-K5) | FE |
| F-65 | **R3:** Wasser über die Taste in den Elektronikraum | Nach P5-M3 ist die Senkung dicht; einzige Barriere ist die Membran, geklemmt durch den Klemmring, dessen Befestigung offen ist (`MONTAGE_SENSOR.md` O-4). Weg: Membranrand → Senkungsgrund → Führungsrohr Ø 3.2 (Stössel) → Elektronikraum | Leckstrom hinter Q1, Korrosion (wie F-09) | 6 | 4 | 7 | **168** | Membran, Taste in Tasche (REQ-UI-06) | O-4 festlegen (Klebung bzw. Presssitz mit Nachweis), ST-W6 (a) | ME |
| F-66 | **R3:** Zapfenwand porös | dünnste Zapfenwand 0.54 mm hinter den hinteren Nutecken (`check_sensor.txt` 9, `PRINT_SETTINGS.md` Kap. 3), FDM 1–2 Bahnen; trennt die O-Ring-Nut (nass) vom Elektronikraum über dem Schott | Wasser im Elektronikraum am Schott vorbei | 6 | 3 | 8 | 144 | – | ST-W6 (b); Druck dort mit voller Füllung bzw. Rev D Wand ≥ 0.8 mm (2 Bahnen 0.4) | ME |

## 3 Zusammenfassung

| Priorität | Einträge | Wesentliche zusätzliche Massnahme |
|---|---|---|
| **sofort (Veto)** | F-06 (RPZ 315) – **Veto PS-K1 in Runde 2 aufgehoben** | Weg B nur mit Dummy-Scheibe (PS-K1) |
| **R3 neu/geändert** | F-23 288 → 144 (Anleitung), F-21 162 → 108; neu F-65 (168), F-66 (144), F-28 (135), F-48 (144), F-49 (126) | Klemmring O-4; Zapfenwand; Schraubentext; Gateway-Zelle G-R1…G-R5 |
| vor Übergabe/Gebrauch der Muster | F-60 (108, Phase 6 neu bewertet), F-04 (168), F-65 (168), F-11 (150), F-53/F-08/F-01/F-66 (144), F-22/F-28 (135); erledigt R3: F-23, F-21 (Anleitung) | Vergussmasse; Falltest mit Zellstrom; Klemmring O-4; Versiegelung Sonde; Federstifte flach; Schraubentext |
| Gateway | F-44 (108), F-45 (54, nur mit Adafruit 4282), F-48 (144), F-49 (126) | geprüftes Netzteil (BOM_GATEWAY G2 Original-Netzteil, CE beim Eingang prüfen); RTC-Typ festschreiben; CR1220-Auflagen G-R1…G-R5 |
| Testplan | alle mit „ST-…“ | `phase5_testplan_beitrag_sicherheit.md` |

**Restrisiko:** Nach Umsetzung der zusätzlichen Massnahmen bleibt kein Eintrag mit S ≥ 9 und O ≥ 3. Das gilt
unter der Bedingung, dass die Tests ST-Z, ST-K und ST-W am Muster bestanden werden. Die Einträge mit S = 9 und O = 2
(F-07, F-20, F-25, F-44) sind für den Eigengebrauch ohne Inverkehrbringen vertretbar. REQ-SAF-01 (keine Flamme,
kein Rauch) ist für die Einzelfehler F-01, F-02, F-04, F-05, F-08 und F-09 **am Muster nachzuweisen** (Testplan).
Analytisch wird es erwartet, weil eine CR2032 im Kurzschluss nur einen begrenzten Strom liefert. Das ist eine
**ANNAHME**: Ein Kurzschlussstrom bzw. Innenwiderstand steht nicht im lokalen Datenblatt; OP-K7 ist offen. Die Zelle
ist bis 85 °C spezifiziert.
