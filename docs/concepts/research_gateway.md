# Tröpfli – Recherche Gateway, PWA-Auslieferung, sicherer Kontext (Phase 2)

| | |
|---|---|
| Dokument | `docs/concepts/research_gateway.md` |
| Version | 0.1 (Entwurf zur Prüfung) |
| Datum | 2026-11-06 |
| Autor | Software-Agent |
| Grundlagen | `REQUIREMENTS.md` v1.0 (Kap. 4, 6.4, 7, 8), `CLIENT_INPUT.md`, `DECISIONS.md` |
| Status | Recherche, **keine Entscheidung**. Entscheid durch Orchestrator/Auftraggeber nach Prüfung. |

Kennzeichnungen: **ANNAHME** = nicht belegt; **PROTOTYP-PRÜFUNG** = erst am Muster nachweisbar.
Quellen am Ende mit Nummer [Qn], alle abgerufen am **2026-11-06**. Lokale Datenblätter:
`docs/datasheets/…`, Register-Einträge in `docs/datasheets/_staging/INDEX_gateway.csv`.

---

## 0 Kurzfassung

1. **Empfehlung Gateway:** fertiges **ESP32-S3-Board mit 16 MB Flash + PSRAM und externer Antenne**
   (z. B. Seeed XIAO ESP32-S3 Plus, CHF 8.90) + **gepufferte RTC** + USB-C-Netzteil, im Firmen-WLAN.
   Kosten ≈ **CHF 30–40**, Leistung ≈ **0.5–0.8 W** (ANNAHME, messen). Kein Raspberry Pi nötig
   (RB-05), sofern das OTA-Protokoll des gewählten Sensor-SoC auf dem ESP32 nachgebaut wird
   (Aufwand siehe Kap. 3). **Rückfallebene:** Raspberry Pi Zero 2 W (Python/BlueZ, fertige
   OTA-Bibliotheken), ≈ CHF 75.
2. **Sensor-SoC aus OTA-Sicht:** **nRF52 (Zephyr/NCS + MCUboot + SMP)** oder **EFR32BG22
   (Gecko Bootloader, signiertes GBL)** gut; **CC2340** machbar (MCUboot-OAD, weniger
   Fremd-Implementierungen); **CH592 nicht empfohlen** (keine Signaturprüfung im Hersteller-OTA
   gefunden → Eigenbau eines sicheren Bootloaders, Risiko für REQ-FW-04).
3. **HTTPS:** Name `troepfli.local` (mDNS) + **Einmal-CA mit Namensbeschränkung**, auf dem PC
   erzeugt; Serverzertifikat ECDSA P-256, Laufzeit ≤ 825 Tage; **CA-Schlüssel wird nach dem
   Signieren gelöscht** → erfüllt REQ-SAF-NET-04 auch dann, wenn ein Gerät Name Constraints nicht
   durchsetzt. Let's-Encrypt-Variante verworfen (Internet-Abhängigkeit, 45-Tage-Zertifikate ab 2028).
4. **Hauptrisiko** ist das Firmen-WLAN (Client-Isolation, Multicast/mDNS gefiltert, NTP gesperrt):
   früh vor Ort testen (Kap. 4.6). Rückfall: eigener Access Point des Gateways oder LAN-Variante.
5. **PWA-Grösse:** mit uPlot ≈ 60–120 kB gzip gesamt → passt problemlos ins ESP32-Flash.

---

## 1 Datenmenge (REQ-GW-01)

Annahmen: 30 Sensoren (REQ-SYS-03), Standardprofil 6 automatische + 2 manuelle Messungen/Tag
(REQ-ENE-04), 2 Jahre = 730 Tage.

Datensatz binär (Vorschlag, **ANNAHME** bis Protokollspezifikation): Zeitstempel u32 (4 B),
Sensorindex u16 (2), Rohwert u16 (2), Feuchteindex u16 0.1 % (2), Temperatur i16 0.01 °C (2),
Batterie mV u16 (2), RSSI i8 (1), Flags u8 (1) = **16 B**.

| Fall | Datensätze 2 Jahre | Binär 16 B | SQLite (ANNAHME ≈ 50 B/Zeile inkl. Index) |
|---|---|---|---|
| 30 Sensoren × 6/Tag | 131 400 | 2.1 MB | ≈ 6.6 MB |
| 30 × 8/Tag (inkl. manuell) | 175 200 | **2.8 MB** | ≈ 8.8 MB |
| 30 × 96/Tag (Maximum REQ-SYS-04) | 2 102 400 | 33.6 MB | ≈ 105 MB |

Folgerung: Für das Muss (Standardintervall) reichen **≈ 3 MB**; ein 16-MB-ESP32 mit ≈ 8 MB
Datenpartition hält das Standardprofil ≈ 5 Jahre (Soll REQ-GW-01) bei ≈ 20 % Dateisystem-Overhead
(ANNAHME). Bei Dauerbetrieb mit 96/Tag reicht internes Flash nicht für 2 Jahre volle Auflösung →
entweder Verdichtung älterer Daten (zulässig per REQ-GW-01 „ältere Daten verdichtet“ erst nach
2 Jahren – also **nicht** zulässig im Muss-Zeitraum) oder microSD. Vorschlag: In der PWA warnen,
wenn die eingestellte Rate die 2-Jahres-Kapazität überschreitet (**offen für Orchestrator**:
gilt REQ-GW-01 nur für das Standardintervall? Wortlaut sagt „Standardintervall“ → ja).

Schreiblast ESP32-Flash: 30 × 8 × 16 B ≈ 3.8 kB/Tag ≈ 1 Sektor (4 kB)/Tag + Metadaten. Flash im
ESP32-S3-WROOM-1: ≥ 100 000 Lösch-/Schreibzyklen, ≥ 20 Jahre Datenerhalt
(`docs/datasheets/Espressif_ESP32-S3-WROOM-1_Datasheet_v1.8.pdf`, S. 30, Tab. 6-8). Mit
Wear-Leveling über ~2000 Sektoren ist Verschleiss vernachlässigbar (A).

---

## 2 Gateway-Varianten

### 2.1 Übersicht

| Kriterium | (a) ESP32-S3 im Firmen-WLAN | (b) Raspberry Pi Zero 2 W | (c1) ESP32 als eigener AP | (c2) ESP32-S3 mit LAN-Kabel | (d) ESP32-C6 statt S3 |
|---|---|---|---|---|---|
| Board (Beispiel) | Seeed XIAO ESP32-S3 Plus (16 MB Flash, 8 MB PSRAM, U.FL + Stabantenne) [Q20] | Pi Zero 2 W [Q19] | wie (a) | Waveshare ESP32-S3-ETH (RJ45) [Q18] | Seeed XIAO ESP32-C6 (4 MB Flash) [Q17] |
| Preis Board | CHF 8.90, pi-shop.ch, an Lager [Q17] | CHF 17.15, pi-shop.ch, **nicht an Lager** [Q16] | CHF 8.90 | CHF 17.80, pi-shop.ch [Q18] | CHF 7.00–7.90 [Q17] |
| Netzteil | RPi 15 W USB-C CHF 9.90 [Q18] | RPi 5 V/2.5 A Micro-USB CHF 11.90 [Q16] | CHF 9.90 | CHF 9.90 (oder PoE) | CHF 9.90 |
| Speicher | internes Flash (LittleFS) | microSD; Industrial 16 GB CHF 27.90 [Q17] | internes Flash | internes Flash (+ ggf. SD) | 4 MB Flash: **zu knapp** für A/B-Update + 3 MB Daten + PWA |
| RTC (REQ-GW-09) | extern nötig, z. B. DS3231-Modul CHF 9.90–18.90 [Q17] | extern nötig (Adafruit PiRTC DS3231 CHF 18.90) [Q17] | extern nötig | extern nötig | extern nötig |
| **Summe ca.** | **CHF 30–40** (+ Gehäusedruck) | **CHF 75–80** | CHF 30–40 | CHF 40–50 | CHF 30–40 |
| Leistung | ≈ 0.5–0.8 W (ANNAHME, s. 2.3) | ≈ 0.5–1 W (s. 2.3) | ≈ 0.5–0.8 W | + Ethernet-PHY, ≈ 0.7–1 W (ANNAHME) | ≈ 0.4–0.7 W (ANNAHME) |
| BLE-Verbindungen gleichzeitig | NimBLE ≤ 9 (S3), Controller 10 Instanzen inkl. Scan/Adv [Q5] | BlueZ, Chip CYW43436 (BT 4.2); Grenze nicht dokumentiert gefunden | ≤ 9 | ≤ 9 | NimBLE-Controller bis 70 [Q5] |
| Funk-Koexistenz | WLAN/BLE teilen ein Radio (Zeitmultiplex) [Q6] | Kombichip, ebenfalls geteilt (ANNAHME) | entfällt weitgehend (AP-Betrieb, kaum Last) | **keine** (WLAN aus) → bester BLE-Scan | wie (a) |
| Stromausfall / Daten | LittleFS: Copy-on-Write, fällt auf letzten gültigen Stand zurück [Q8] | SD-Korruption möglich; nur mit Read-only-Root + SQLite-WAL vertretbar (ANNAHME) | wie (a) | wie (a) | wie (a) |
| Bootzeit | < 2 s (ANNAHME) | ≈ 20–40 s (ANNAHME) | < 2 s | < 2 s | < 2 s |
| Angriffsfläche (REQ-SAF-NET-02) | minimal (nur 443/80, mDNS) | Linux: Dienste abschalten, Updates nur per Image | minimal, eigenes Netz | minimal | minimal |
| Entwicklung | C/ESP-IDF, eigener Speicher, eigener OTA-Client → **hoch** | Python (bleak, aiohttp, sqlite3), fertige OTA-Clients → **niedrig** | wie (a) + Zeit nur aus RTC/Browser | wie (a) + Ethernet | wie (a), ein Kern |
| Gateway-Update (REQ-GW-11) | A/B-OTA mit Rollback (ESP-IDF), PWA im Image → atomar | Image-/Paket-Update, Daten auf separater Partition | wie (a) | wie (a) | knapp wegen 4 MB |
| Eingriff Firmennetz | 1 WLAN-Client | 1 WLAN-Client | **keiner** | 1 LAN-Port (oft **mehr** Eingriff: IT muss Port freigeben) | 1 WLAN-Client |

### 2.2 Bewertung je Variante

**(a) ESP32-S3 im Firmen-WLAN – empfohlen.**
- Erfüllt RB-05 (kein Pi), REQ-GW-04 (≤ 2 W), REQ-GW-05 (LittleFS stromausfallfest [Q8]).
- 16 MB Flash: Partitionsvorschlag (ANNAHME) Bootloader/NVS 0.1 MB, 2 × App 3 MB (inkl.
  eingebetteter PWA), Sensor-Firmware-Ablage 1 MB, Daten-LittleFS ≈ 8.5 MB.
- PSRAM (8 MB) entlastet mbedTLS (Handshake braucht 40–50 kB Heap [Q10]) und HTTP-Puffer.
- Externe Antenne (U.FL) verbessert Reichweite zu den Sensoren (RB-01, 18 m); PCB-Antennen der
  DevKitC gehen auch, im Gehäuse aber schlechter (ANNAHME).
- Nachteil: höchster Entwicklungsaufwand (SMP-/OTA-Client, Datenablage, HTTPS-Server, Backup
  selbst schreiben).

**(b) Raspberry Pi Zero 2 W – Rückfallebene.**
- Vorteile: Python mit `bleak`, `smpclient` [Q12] bzw. `silabs-ble-ota` [Q13] sofort nutzbar;
  SQLite; schnelle Entwicklung, gute Fehlersuche.
- Nachteile: SD-Karten-Verschleiss und Korruption bei Stromausfall (Gegenmassnahme: Read-only-
  Root mit Overlay, Daten auf eigener Partition, SQLite WAL, Industrial-microSD); Linux muss
  gepflegt werden, aber Internet-Updates widersprechen REQ-SYS-01 → Update nur als Image vom PC;
  Lieferbarkeit schwankt (pi-shop.ch 2026-11-06: nicht an Lager [Q16]); Produktion zugesichert
  bis mind. Januar 2030 (`docs/datasheets/RaspberryPi_Zero2W_ProductBrief_2024-04.pdf`, S. 2).
- Begründung nach RB-05 nur, wenn (i) das OTA-Protokoll des Sensor-SoC auf dem ESP32 nicht mit
  vertretbarem Aufwand umsetzbar ist oder (ii) 96 Messungen/Tag über 2 Jahre in voller Auflösung
  gefordert werden.

**(c1) Gateway als eigener Access Point (ohne Firmen-WLAN).**
- Kein Eingriff ins Firmennetz, mDNS funktioniert sicher im eigenen Netz.
- Nutzbarkeit **schlecht**: Handy muss für jede Abfrage ins WLAN „troepfli“ wechseln und verliert
  dort Internet. Android betrachtet ein WLAN ohne Internet ggf. nicht als Standardnetz und schickt
  Verkehr über Mobilfunk, bis der Nutzer „Verbunden bleiben“ bestätigt (ANNAHME, PROTOTYP-PRÜFUNG).
  Kein NTP → Zeit nur aus RTC und Browser (REQ-GW-09 erlaubt das).
- Sinnvoll als **Notfall-/Einrichtungsmodus** (z. B. nach Tastendruck 10 min AP), nicht als
  Normalbetrieb.

**(c2) LAN-Kabel (ESP32-S3-ETH).**
- Beste BLE-Leistung (WLAN aus), aber im Büro braucht es einen freien, freigegebenen Netzwerkport
  und meist die IT → widerspricht „wenig Eingriff“. Gleiche Softwarebasis wie (a); als Option
  offenhalten (gleiches SoC, gleicher Code + Ethernet-Treiber).

**(d) Weitere geprüfte Varianten**
- **ESP32-C6:** BLE-Controller mit bis 70 Verbindungen [Q5], geringerer RX-Strom (BLE RX 73 mA,
  `Espressif_ESP32-C6-WROOM-1_Datasheet_v1.4.pdf`, S. 27, Tab. 6-5 vs. 93 mA beim S3,
  `Espressif_ESP32-S3-WROOM-1_Datasheet_v1.8.pdf`, S. 28, Tab. 6-5). Aber gängige Boards mit
  4 MB Flash zu knapp, ein Kern. Nur mit 8–16-MB-Modul interessant.
- **Sensor-SoC als BLE-Coprozessor am ESP32 bzw. Pi** (z. B. nRF52840-Board als HCI/Central):
  bringt bei nRF52-Sensoren nativen SMP-Client (Zephyr), aber zweite Firmware, höhere Kosten.
  Nur falls Koexistenz-Tests (Kap. 2.4) scheitern.
- **Home Assistant/ESPHome-Proxy, altes Android-Handy, PC:** verworfen (Dauer-Rechner nötig,
  RB-05; Handy-Akku im Dauerladebetrieb = Sicherheitsrisiko; Web Bluetooth fehlt auf iOS Safari).

### 2.3 Leistungsaufnahme (REQ-GW-04 ≤ 2 W)
- ESP32-S3-Modul: BLE RX 93 mA, WLAN RX 95–97 mA, TX bis 355 mA Spitze (3.3 V)
  (`Espressif_ESP32-S3-WROOM-1_Datasheet_v1.8.pdf`, S. 28, Tab. 6-4/6-5). Dauerndes BLE-Scannen
  hält das Radio fast immer im RX → Mittel ≈ 100–150 mA @ 3.3 V + Reglerverluste ≈
  **0.5–0.8 W am 5-V-Eingang (ANNAHME, PROTOTYP-PRÜFUNG)**.
- Pi Zero 2 W: gemessen 100 mA (Geerling [Q21]) bzw. 125–127 mA (CNX [Q22]) Leerlauf headless
  @ 5 V mit WLAN ≈ 0.5–0.65 W; mit BLE-Scan und Last ≈ 0.6–1 W (ANNAHME).
- Beide erfüllen ≤ 2 W klar.

### 2.4 BLE-Scan und Reaktionszeit (REQ-SYS-05)
- Sensor sendet alle ≤ 27 s ein verbindbares Advertising. Gateway scannt **dauernd**
  (Scan-Window = Scan-Interval) und verbindet beim nächsten Advertising des Zielsensors.
  30 Sensoren × 1 Adv/27 s ≈ 1.1 Adv/s → Last trivial.
- Gleichzeitige Verbindungen sind nicht kritisch: Sensoren verbinden kurz (Daten holen, Befehl,
  Zeit), ESP32-S3 erlaubt bis 9 (NimBLE) bzw. 8 bei gleichzeitigem Scan+Adv (Bluedroid) [Q5].
  Empfehlung: ≤ 3 parallele Verbindungen, Rest in Warteschlange.
- **Risiko Koexistenz:** WLAN und BLE teilen beim ESP32 das Radio im Zeitmultiplex [Q6]; Espressif
  stuft „BLE Scan/Connected bei WLAN STA connected“ als unterstützt/stabil ein, nennt aber keine
  Scan-Ausbeute. Ein verpasstes Advertising kostet 27 s. Für das Soll ≤ 1 min muss ≥ 1 von 2
  Advertising-Ereignissen erkannt werden. **PROTOTYP-PRÜFUNG:** 1000 „Jetzt messen“-Auslösungen
  mit WLAN-Last, 95-%-Quantil messen; Massnahmen: BLE-Task auf eigenen Kern, WLAN-Sendepausen,
  Advertising auf allen 3 Kanälen, ggf. (c2).
- Bonding-Speicher NimBLE standardmässig 3 Bonds (`CONFIG_BT_NIMBLE_MAX_BONDS`, Default 3 [Q5]) →
  Empfehlung: **Sensor-Schlüssel auf Anwendungsebene** (REQ-RF-05/06, AES-CCM o. ä.) in der
  eigenen Datenbank statt BLE-Bonding; macht das Protokoll unabhängig von Stack und Gateway-Typ.

### 2.5 Zeit nach Stromausfall (REQ-GW-09)
- Weder ESP32-Board noch Pi Zero 2 W haben eine gepufferte Echtzeituhr (Pi: keine RTC im Product
  Brief aufgeführt, S. 2). Anforderung ±2 min/Monat ≈ **±46 ppm**, Zeit ≥ 24 h halten.
- Lösung: I²C-RTC mit Knopfzelle oder Superkondensator (z. B. DS3231-Modul, pi-shop.ch CHF 9.90 bzw.
  18.90 [Q17]). Konkreter Baustein in Phase 3; Datenblatt-Download von analog.com/microcrystal.com
  aus WSL schlug fehl → im Register vermerkt.
- Zeitquellen-Reihenfolge (Vorschlag): öffentlicher NTP (OP-08, abschaltbar) → RTC → Browserzeit
  beim Anmelden (nur übernommen, wenn RTC ungültig und Benutzer angemeldet) → sonst keine Zeit an
  Sensoren, Werte markiert.
- **Hinweis:** Firmen-WLAN kann UDP 123 sperren → RTC ist auch mit NTP-Freigabe sinnvoll.

---

## 3 OTA zum Sensor – Schnittstelle Gateway ↔ Sensor-SoC

### 3.1 Kompatibilitätsmatrix

| Sensor-SoC | Hersteller-DFU (BLE) | Signatur/Anti-Rollback nativ | Linux/Python-Client | ESP32-Client | Aufwand / Risiko |
|---|---|---|---|---|---|
| **nRF52** (nRF Connect SDK/Zephyr) | **MCUmgr SMP** über GATT (Service-UUID 8d53dc1d-1db7-4cd3-868b-8a527460aa84) [Q14]; Bootloader MCUboot | MCUboot: ECDSA P-256, Ed25519, RSA [Q11]; Downgrade-Schutz per Software **nur im Overwrite-Modus**, sonst Hardware-Sicherheitszähler `MCUBOOT_HW_ROLLBACK_PROT`; Test-Swap mit automatischem Rückfall [Q11] | `smpclient` (Apache-2.0, v7.3.0 vom 2026-07-06, BLE-Transport) [Q12]; Berichte über Probleme mit Eigenbau-Skripten [Q15] | **kein fertiger Client gefunden** → eigener SMP-Client (CBOR, Image-Upload, Test/Confirm) | Pi: niedrig. ESP32: mittel (ANNAHME ≈ 1 Woche). Risiko niedrig – offenes, dokumentiertes Protokoll |
| nRF52 (altes nRF5 SDK, Secure DFU) | Nordic Legacy/Secure DFU | ECDSA-signierte Pakete | Tools vorhanden | Eigenbau | **Nicht empfohlen:** nRF5 SDK in Wartungsmodus, Nordic empfiehlt NCS [Q23] |
| **TI CC2340** (SimpleLink Low Power F3 SDK) | TI **OAD** mit MCUboot („MCUboot OAD“) [Q24] | OAD-Profil selbst ohne Sicherheit; Authentizität durch MCUboot (ECDSA) [Q24]; Secure Boot laut TI unterstützt (E2E) | kein gepflegter Fremd-Client gefunden → Eigenbau nach TI-Profil | Eigenbau | mittel / mittel (weniger Community-Erfahrung, Doku verteilt) |
| **SiLabs EFR32BG22** | **OTA DFU via AppLoader** (Gecko Bootloader), Reset in OTA-Modus [Q25] | signierte GBL (ECDSA P-256, `commander gbl keygen --type ecc-p256`), optional verschlüsselt; Secure Boot [Q25] | `silabs-ble-ota` (bleak, auch über ESPHome-Proxy; ≈ 58 s für 234 kB auf BG22 im Fast-Modus) [Q13] | Eigenbau (einfaches Protokoll: Control- + Data-Characteristic) | Pi: niedrig. ESP32: niedrig–mittel. AppLoader ohne Flusskontrolle → Fast-Modus vorsichtig [Q13]. Anti-Rollback in Phase 3 prüfen (ANNAHME) |
| **WCH CH592** | WCH-IAP/OTA-Beispiele (proprietär, v. a. chinesische Doku) [Q26] | **keine Signaturprüfung gefunden** → eigener Bootloader mit Ed25519/ECDSA in Software | keiner gefunden | Eigenbau | **hoch / hoch** – sicherheitskritischer Eigenbau (REQ-FW-03/04) |

### 3.2 Sicherheitskonzept OTA (REQ-FW-04, REQ-RF-06) – Vorschlag
1. **Signatur der Firmware-Abbilder** im Bootloader des Sensors (MCUboot bzw. Gecko Bootloader).
   Signierschlüssel nur auf dem Entwickler-PC bzw. offline (Build-Skript), **nie auf dem
   Gateway**; der Sensor kennt nur den öffentlichen Schlüssel.
2. **Anti-Rollback:** MCUboot – Hardware-Sicherheitszähler oder Overwrite-Modus mit Downgrade-Schutz
   [Q11]; Zielkonflikt mit REQ-FW-03 (Rückfall bei Abbruch): Swap-Modus mit Test/Confirm **und**
   Sicherheitszähler kombinieren (Konfiguration in Phase 3 verifizieren).
3. **Transport nur vom gekoppelten Gateway:** Der Hersteller-DFU-Dienst (SMP/AppLoader) ist
   standardmässig nicht an „unser“ Gateway gebunden. Deshalb: DFU-Dienst nur nach einem
   authentisierten Befehl auf Anwendungsebene für ein Zeitfenster aktivieren (bzw. Reset in
   AppLoader), alternativ GATT-Rechte „nur verschlüsselt/authentisiert“ (Zephyr-Option, Name in
   Phase 3 prüfen, ANNAHME). Die Signatur schützt die Integrität ohnehin; die Bindung verhindert
   Missbrauch/Batterieentladung.
4. **Batterieschwelle** (REQ-FW-02) prüft der Sensor selbst vor dem Annehmen.
5. Das Gateway prüft die Signatur zusätzlich vor dem Verteilen (öffentlicher Schlüssel), um
   unnötige Übertragungen zu vermeiden.

### 3.3 Folgerung für die SoC-Wahl
Gateway-seitig sind **nRF52 (SMP)** und **EFR32BG22 (AppLoader)** am günstigsten: offene,
kleine Protokolle, fertige Python-Clients als Referenz/Testwerkzeug, native Signatur. Für den
ESP32 muss in jedem Fall ein eigener Client geschrieben werden; die Python-Clients dienen als
Referenz und für Tests vom PC aus.

---

## 4 Sicherer Kontext (HTTPS) im LAN

### 4.1 Warum
Service Worker und PWA-Installation brauchen einen sicheren Kontext; `http://<LAN-IP>` gilt nicht
als sicher (nur `localhost`) [Q27]. Ohne HTTPS ist REQ-APP-02 nicht erfüllbar.

### 4.2 Optionen

| Option | iOS Safari | Android Chrome | Desktop | REQ-SAF-NET-04 | Bewertung |
|---|---|---|---|---|---|
| **O1 Einmal-CA mit Name Constraints, Schlüssel gelöscht** (empfohlen) | Profil installieren + „Volles Vertrauen“ [Q1] | CA-Zertifikat in Benutzer-Speicher (ANNAHME: Chrome akzeptiert Benutzer-CAs, PROTOTYP-PRÜFUNG) | OS-Speicher (Win/macOS), Firefox eigener Speicher | **erfüllt**: Namensbeschränkung + CA-Schlüssel existiert nicht mehr → kann nichts anderes signieren | sicher, einmaliger Aufwand pro Gerät, Erneuerung nach ≤ 825 Tagen |
| O2 Einmal-CA mit Constraints, Schlüssel offline aufbewahrt (USB-Stick, verschlüsselt) | wie O1 | wie O1 | wie O1 | erfüllt, sofern Constraints durchgesetzt werden; Restrisiko Schlüsseldiebstahl | Komfort bei Erneuerung (kein Neuinstallieren), aber Schutz hängt an Durchsetzung der Constraints (siehe 4.3) |
| O3 Einzelnes selbstsigniertes Serverzertifikat als Vertrauensanker | „Certificate Trust Settings“ listet Root-Zertifikate; Verhalten bei Blatt-Zertifikat (CA:FALSE) unklar (ANNAHME) | unklar, ob Chrome ein Blatt als Anker akzeptiert (ANNAHME) | uneinheitlich | erfüllt (kann nichts signieren) | fragil → nicht empfohlen |
| O4 Öffentliche Domain + Let's Encrypt DNS-01, A-Record auf private IP | ohne Installation | ohne Installation | ohne Installation | erfüllt | **verworfen:** Erneuerung braucht Internet + DNS-API-Schlüssel (REQ-SYS-01: nur NTP erlaubt); Laufzeit ab 2027-02-10 64 Tage, ab 2028-02-16 45 Tage [Q9] → Erneuern alle ~4–6 Wochen; Namensauflösung über öffentliches DNS (Firmen-DNS blockiert oft private Antworten = Rebinding-Schutz, ANNAHME); Hostname in CT-Logs öffentlich; Domainkosten |
| O5 Nur HTTP | keine PWA | keine PWA | – | – | erfüllt REQ-APP-02 nicht |
| O6 Zertifikat auf feste IP (IP-SAN) | möglich | möglich | möglich | wie O1 | IP ändert sich (UC-13, REQ-GW-10) → nur als Zusatz-SAN, wenn IT eine DHCP-Reservierung gibt |

### 4.3 Werden Name Constraints durchgesetzt?
- **Chrome:** Seit Chrome 112 werden Name Constraints auch für vom Benutzer importierte Roots
  durchgesetzt (vorher auf Linux nicht) [Q3]. Chrome nutzt auf Android seit Chrome 115 den eigenen
  „Chrome Certificate Verifier“ und berücksichtigt lokale Vertrauensentscheidungen (für TCP-TLS
  hinzufügen und entfernen) [Q4]. Ausdrückliche Doku „Constraints auf Benutzer-Roots unter
  Android“ nicht gefunden → **ANNAHME**.
- **Apple iOS:** Laut CA/B-Forum-Beitrag unterstützt Apple nameConstraints seit iOS 9 bzw.
  macOS 10.12 [Q7]; offizielle Apple-Doku dazu nicht gefunden → **ANNAHME**.
- RFC 5280 erlaubt Implementierungen ausdrücklich, Constraints in Vertrauensankern zu ignorieren
  (zitiert in [Q3]).
- **Konsequenz:** Darum O1 (Schlüssel löschen): Die Sicherheit hängt dann nicht von der
  Durchsetzung ab. **PROTOTYP-PRÜFUNG (Negativtest):** Mit einer Test-CA (gleiche Constraints)
  ein Zertifikat für `example.com` signieren und auf iOS, Android, Windows prüfen, dass es
  abgelehnt wird – dokumentiert, ob die Geräte Constraints durchsetzen (relevant für O2).

### 4.4 Zertifikatsprofil (Vorschlag)
- **CA** (auf dem PC, Skript `scripts/troepfli_ca.sh` o. ä. in Phase 3, openssl):
  ECDSA P-256, `basicConstraints=critical,CA:TRUE,pathlen:0`,
  `keyUsage=critical,keyCertSign`, **`nameConstraints=critical,permitted;DNS:troepfli.local,`
  `permitted;DNS:.troepfli.local, excluded;IP:0.0.0.0/0.0.0.0, excluded;IP:::/0`** (IP-Namen
  ausschliessen, sonst wären IP-Adressen unbeschränkt; ggf. einen Firmen-DNS-Namen zusätzlich
  zulassen, wenn die IT einen vergibt). Laufzeit z. B. 10 Jahre, Schlüssel nach dem Signieren
  löschen (O1).
- **Serverzertifikat:** ECDSA P-256, SAN `DNS:troepfli.local` (+ `DNS:troepfli-<gw-id>.local` für
  REQ-SYS-11), EKU `serverAuth`, SHA-256, Laufzeit **≤ 825 Tage** (Apple-Pflicht für alle
  TLS-Serverzertifikate seit 2019 [Q2]; die 398-Tage-Regel betrifft Benutzer-Roots **nicht** [Q2b]).
- **Schlüssel des Servers** erzeugt das Gateway selbst (verlässt das Gateway nie); der PC signiert
  nur den CSR.

### 4.5 Ablauf Schritt für Schritt (Skizze)
**Erstinbetriebnahme (UC-01) – Provisionierung per USB-Kabel am PC** (physischer Zugang = sicher,
deckt auch UC-16 „Passwort vergessen“):
1. Gateway per USB an den PC; Skript liest Gateway-ID und CSR (P-256) über die serielle
   Schnittstelle.
2. Skript erzeugt die Einmal-CA, signiert den CSR, schreibt Zertifikat, WLAN-Zugangsdaten und
   Admin-Passwort (bzw. Einmal-Code) aufs Gateway, löscht den CA-Schlüssel, gibt `troepfli-ca.crt`
   und dessen **SHA-256-Fingerabdruck** aus.
3. Zertifikat aufs Handy bringen: per AirDrop/E-Mail an sich selbst oder Download von
   `http://troepfli.local/ca.crt` (dann Fingerabdruck vergleichen; die Datei ist öffentlich,
   Manipulation im LAN würde am Fingerabdruck auffallen).

**iOS (Safari)** [Q1]:
1. `troepfli-ca.crt` in Safari öffnen bzw. antippen → „Profil geladen“.
2. Einstellungen → „Profil geladen“ → Installieren (Code eingeben) → Installieren.
3. Einstellungen → Allgemein → Info → **Zertifikatsvertrauenseinstellungen** → unter „Volles
   Vertrauen für Root-Zertifikate aktivieren“ Tröpfli-CA einschalten. (Ohne diesen Schritt
   vertraut iOS manuell installierten Profilen **nicht** für TLS [Q1].)
4. Safari → `https://troepfli.local` → Teilen → „Zum Home-Bildschirm“.

**Android (Chrome)** (Menüpfad Pixel/Android 14+, herstellerabhängig) [Q28]:
1. `troepfli-ca.crt` herunterladen.
2. Einstellungen → Sicherheit & Datenschutz → Weitere Sicherheitseinstellungen →
   Verschlüsselung & Anmeldedaten → Zertifikat installieren → **CA-Zertifikat** → Warnung
   bestätigen → Datei wählen. Bildschirmsperre ist Voraussetzung [Q28].
3. Chrome → `https://troepfli.local` → Menü → „App installieren“.
4. Hinweis: Apps ab API 24 vertrauen Benutzer-CAs standardmässig nicht [Q29] – betrifft andere
   Apps, nicht die PWA in Chrome (ANNAHME, PROTOTYP-PRÜFUNG).

**Desktop:** Windows „Zertifikate – Aktueller Benutzer → Vertrauenswürdige Stammzertifizierungs-
stellen“ (Chrome/Edge nutzen den OS-Speicher [Q4]); macOS Schlüsselbund → „Immer vertrauen“;
Firefox: eigener Speicher (Einstellungen → Zertifikate importieren).

**Erneuerung (≤ 825 Tage):** PWA warnt 60 Tage vorher; Provisionierungsskript erneut (neue
Einmal-CA), Profil auf den Geräten ersetzen. Bei Gateway-Tausch (UC-14) gleiches Verfahren.

### 4.6 Name `troepfli.local` (mDNS)
- **iOS/macOS:** Bonjour/mDNS nativ (allgemein bekannt; Apple-Primärquelle nicht abgerufen → ANNAHME).
- **Android:** Systemresolver unterstützt `.local` per mDNS **seit November 2021** (DnsResolver-
  Mainline-Modul, faktisch Android 12+, ANNAHME zur Version); **nicht** über VPN und Mobilfunk [Q30].
  Ob Chrome für `.local` den Systemresolver nutzt: ANNAHME (sehr wahrscheinlich), PROTOTYP-PRÜFUNG.
  Firmenhandys mit Always-on-VPN → `.local` geht nicht (privates Handy laut OP-07: unkritisch).
- **Windows 10/11:** mDNS-Namensauflösung seit Windows 10 1703 (Sekundärquelle) [Q31].
- **Firmen-WLAN-Risiko:** Viele Firmen-WLANs filtern Multicast oder isolieren Clients. Dann
  funktionieren weder mDNS noch der direkte Zugriff Handy → Gateway. **Vor dem Bau vor Ort testen**
  (z. B. ein beliebiges mDNS-Gerät oder Laptop mit `troepfli.local`-Testdienst).
  Rückfall in dieser Reihenfolge: (1) IT vergibt DNS-Namen → als zusätzlicher erlaubter Name in die
  Constraints/SAN; (2) DHCP-Reservierung + IP-SAN; (3) Variante (c1) eigener AP.

### 4.7 TLS auf dem ESP32
- **ECDSA P-256 statt RSA-2048:** kürzere Zertifikate (≈ 0.5 kB statt ≈ 1 kB, ANNAHME),
  schnellere Signatur auf Serverseite; Apple verlangt nur bei RSA ≥ 2048 bit [Q2]. ESP-IDF bietet
  Hardware-ECC-Beschleunigung für P-256 auf SoCs mit `SOC_ECC_SUPPORTED`, RSA über
  MPI-Beschleuniger [Q5]; ob der S3 ECC-Hardware hat: ANNAHME „nein“ (Software genügt).
- **RAM:** Handshake ≈ 40–50 kB Heap [Q10]; mit dynamischen TLS-Puffern (`CONFIG_MBEDTLS_DYNAMIC_BUFFER`)
  und PSRAM sind 3–4 gleichzeitige TLS-Verbindungen realistisch (ANNAHME). Session Tickets
  (`CONFIG_MBEDTLS_SERVER_SSL_SESSION_TICKETS`, Default an [Q5]) sparen Folge-Handshakes.
- **Ladezeit:** PWA als wenige, vorkomprimierte Dateien (gzip, `Content-Encoding: gzip`), HTML/CSS/JS
  inline bzw. 2–3 Dateien, Keep-Alive. Erster Aufruf ≈ 1–3 s (ANNAHME, messen), danach aus dem
  Service-Worker-Cache; nur API-Aufrufe gehen ans Gateway.

---

## 5 PWA-Grösse und Speicher

Gemessen (Download von unpkg.com, 2026-11-06, `gzip -9`):

| Bibliothek | Version | minifiziert | gzip |
|---|---|---|---|
| uPlot (`uPlot.iife.min.js` + CSS) | 1.6.32 (aktuell) | 51.1 kB + 1.9 kB | **22.0 kB + 0.8 kB** |
| Chart.js (`chart.umd.js`) | 4.4.9 (aktuell 4.6.1) | 206.7 kB | 69.9 kB |
| Preact (optional UI) | 10.26.9 | 11.2 kB | 4.8 kB |

Schätzung Gesamt-PWA (ANNAHME): eigener Code 20–40 kB gzip, uPlot 23 kB, Icons/Manifest
10–30 kB, Systemschriften (keine Webfonts) → **≈ 60–120 kB gzip**. Mit Chart.js ≈ +50 kB.
Beides passt problemlos in eine 3-MB-App-Partition. **Empfehlung uPlot**: für Zeitreihen
gebaut, klein, kein CDN (REQ-APP-09), Lizenz MIT (ANNAHME, in Phase 3 prüfen).
PWA im Gateway-Firmware-Image einbetten → Gateway- und PWA-Update atomar mit A/B-Rollback
(REQ-GW-11).

---

## 6 Risiken

| Nr. | Risiko | Wirkung | Massnahme |
|---|---|---|---|
| R1 | Firmen-WLAN mit Client-Isolation/Multicast-Filter | PWA/mDNS nicht erreichbar | Vor-Ort-Test vor Phase 3; Rückfall 4.6 / (c1) |
| R2 | WLAN/BLE-Koexistenz ESP32 verschlechtert Scan | Reaktionszeit > 1 min | Prototyp-Messung 2.4; Option (c2) oder BLE-Coprozessor |
| R3 | Kein ESP32-Client für das DFU-Protokoll des SoC | Mehraufwand; Fehler im OTA | SoC mit offenem Protokoll wählen (nRF52/BG22); Python-Client als Referenz/Testorakel |
| R4 | Name Constraints auf iOS/Android nicht durchgesetzt | Schwächung bei O2 | O1 (Schlüssel löschen); Negativtest 4.3 |
| R5 | Benutzer vergisst Zertifikatsvertrauen (iOS-Schritt 3) | „Nicht sicher“, keine PWA | Schritt-Anleitung mit Bildern, Prüfseite in der PWA |
| R6 | Zertifikat läuft nach ≤ 825 Tagen ab | PWA nicht erreichbar | Warnung 60 Tage vorher, Erneuerungsskript |
| R7 | Zeitverlust bei Stromausfall ohne NTP | falsche Zeitstempel | RTC mit Pufferung; Markierung nach REQ-GW-09 |
| R8 | ESP32-Flash zu klein bei 96 Messungen/Tag | < 2 Jahre volle Auflösung | Warnung in PWA; optional microSD; Klärung Wortlaut REQ-GW-01 |
| R9 | Lieferbarkeit Pi Zero 2 W | Rückfall-Variante verzögert | ESP32 als Hauptvariante |
| R10 | Hersteller-DFU-Dienst ohne Bindung an Gateway | Verstoss REQ-RF-06 | DFU nur nach authentisiertem Befehl/Zeitfenster aktivieren (3.2) |
| R11 | CH592 ohne Signatur im Bootloader | Verstoss REQ-FW-04 oder hoher Eigenbau | CH592 aus OTA-Sicht abwerten |

## 7 Offene Punkte für Orchestrator/Auftraggeber
1. Vor-Ort-Test Firmen-WLAN (Client-Isolation, mDNS, NTP) – kann der Auftraggeber mit Laptop +
   Handy in 10 min machen; Anleitung liefert Software-Agent.
2. Bestätigen: REQ-GW-01 (2 Jahre volle Auflösung) gilt für das **Standardintervall**.
3. O1 (CA-Schlüssel löschen, Neuinstallation alle ≈ 2 Jahre) vs. O2 (Schlüssel offline behalten).
4. SoC-Entscheid unter Einbezug der OTA-Matrix (Kap. 3.1).

---

## Quellen (alle abgerufen 2026-11-06)

- [Q1] Apple: Trust manually installed certificate profiles in iOS, iPadOS and visionOS – https://support.apple.com/en-ca/102390
- [Q2] Apple: Requirements for trusted certificates in iOS 13 and macOS 10.15 – https://support.apple.com/103769
- [Q2b] Apple: About upcoming limits on trusted certificates (398 Tage, nicht für Benutzer-Roots) – https://support.apple.com/en-us/102028
- [Q3] A. Sci: „Name (non-)constraint“ – Chrome erzwingt Constraints für Benutzer-Roots ab 112; RFC-5280-Zitat – https://alexsci.com/blog/name-non-constraint/
- [Q4] Chromium: Chrome Root Store FAQ (Android ab Chrome 114/115; lokale Vertrauensentscheidungen) – https://chromium.googlesource.com/chromium/src/+/main/net/data/ssl/chrome_root_store/faq.md
- [Q5] Espressif: ESP-IDF v6.1 Kconfig Reference ESP32-S3 (`BT_NIMBLE_MAX_CONNECTIONS`, `BT_CTRL_BLE_MAX_ACT`, `BT_ACL_CONNECTIONS`, `BT_NIMBLE_MAX_BONDS`, `MBEDTLS_HARDWARE_ECC/MPI`, `MBEDTLS_DYNAMIC_BUFFER`, `MBEDTLS_SERVER_SSL_SESSION_TICKETS`) – https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-reference/kconfig-reference.html
- [Q6] Espressif: RF Coexistence (ESP32-S3) – https://docs.espressif.com/projects/esp-idf/en/stable/esp32s3/api-guides/coexist.html
- [Q7] CA/Browser Forum servercert-wg, Feb. 2020 (Apple nameConstraints seit iOS 9) – https://archive.cabforum.org/pipermail/servercert-wg/2020-February/001684.html
- [Q8] littlefs README (Power-loss resilience, wear leveling) – https://github.com/littlefs-project/littlefs
- [Q9] Let's Encrypt: Certificate Lifetime Rationale and Plans / Ankündigung 2025-12-03 – https://letsencrypt.org/docs/cert-lifetimes/ ; Zusammenfassung https://linuxiac.com/lets-encrypt-to-cut-certificate-lifetimes-to-45-days-by-2028/
- [Q10] Espressif ESP-FAQ mbedTLS (Handshake 40–50 kB Heap) – https://docs.espressif.com/projects/esp-faq/en/latest/software-framework/protocols/mbedtls.html
- [Q11] MCUboot Design (Signaturtypen, Downgrade-Schutz, Test-Swap) – https://docs.mcuboot.com/design.html
- [Q12] PyPI smpclient 7.3.0 – https://pypi.org/project/smpclient/
- [Q13] PyPI silabs-ble-ota (README via Suchergebnis; Seite selbst lud nicht) – https://pypi.org/project/silabs-ble-ota/
- [Q14] SMP-Service-UUID (Drittquelle) – https://embedwise.pages.dev/calculators/smp-dfu ; Nordic DevZone „DFU SMP Client“ – https://devzone.nordicsemi.com/f/nordic-q-a/81334/dfu-smp-client
- [Q15] Nordic DevZone: Issue with BLE FOTA Process Using Python Script – https://devzone.nordicsemi.com/f/nordic-q-a/119780/issue-with-ble-fota-process-using-python-script
- [Q16] pi-shop.ch: Raspberry Pi Zero 2 W (CHF 17.15, nicht an Lager), Netzteil 5 V/2.5 A CHF 11.90 – https://www.pi-shop.ch/raspberry-pi-zero-2-w
- [Q17] pi-shop.ch Suchen (XIAO ESP32-S3 Plus CHF 8.90; XIAO ESP32-C6 CHF 7.00/7.90; DS3231-Module CHF 9.90/18.90; Kingston Industrial microSD 16 GB CHF 27.90) – https://www.pi-shop.ch/catalogsearch/result/?q=xiao+esp32-s3 , …?q=esp32-c6 , …?q=ds3231 , …?q=sd+karte+industrial
- [Q18] pi-shop.ch Suchen (Waveshare ESP32-S3-ETH CHF 17.80; Raspberry Pi 15 W USB-C Netzteil CHF 9.90) – https://www.pi-shop.ch/catalogsearch/result/?q=esp32-s3-eth , …?q=netzteil+usb-c
- [Q19] Raspberry Pi Zero 2 W Product Brief (April 2024) – lokal `docs/datasheets/RaspberryPi_Zero2W_ProductBrief_2024-04.pdf`
- [Q20] XIAO ESP32-S3 Plus Daten (16 MB Flash, 8 MB PSRAM, U.FL) – https://thepihut.com/products/seeed-xiao-esp32s3-plus ; https://ameridroid.com/products/xiao-esp32-s3-plus
- [Q21] J. Geerling: Disabling cores to reduce the Pi Zero 2 W's power consumption – https://www.jeffgeerling.com/blog/2021/disabling-cores-reduce-pi-zero-2-ws-power-consumption-half/
- [Q22] CNX Software: Raspberry Pi Zero 2 W power consumption – https://www.cnx-software.com/2021/12/09/raspberry-pi-zero-2-w-power-consumption/
- [Q23] Nordic DevZone: nRF5 SDK Wartungsmodus, NCS für neue Projekte – https://devzone.nordicsemi.com/f/nordic-q-a/94954/which-ota-dfu-update-solution-going-forward
- [Q24] TI: MCUBoot OAD, SimpleLink Low Power F3 SDK 7.40 – https://dev.ti.com/tirex/content/simplelink_lowpower_f3_sdk_7_40_00_64/docs/ble5stack/ble_user_guide/html/ble-stack-5.x-guide/ble5-oad-index-mcuboot.html ; E2E Secure Boot CC2340R5 – https://e2e.ti.com/support/wireless-connectivity/bluetooth-group/bluetooth/f/bluetooth-forum/1239239/cc2340r5-secure-boot-by-arm-m0-core
- [Q25] Silicon Labs: Secure OTA DFU – https://docs.silabs.com/bluetooth/3.2/bluetooth-general-firmware-upgrade/secure-ota-dfu ; BG22 Secure-OTA-Workshop – https://www.silabs.com/documents/public/training/wireless/bg22-thunderboard-workshop-secure-ota.pdf
- [Q26] CH573/CH582/CH592 IAP-Beispiele (Blog, chinesisch) – https://cnblogs.com/risc5-ble/p/archive/2024/04/11
- [Q27] DZone: iOS PWA offline caching (Service Worker braucht HTTPS, `localhost`-Ausnahme, Zertifikatsvertrauen auf iPhone) – https://dzone.com/articles/ios-pwa-offline-caching
- [Q28] Google Pixel-Hilfe: Zertifikate hinzufügen und entfernen – https://support.google.com/pixelphone/answer/2844832
- [Q29] Android Developers Blog: Changes to Trusted Certificate Authorities in Android Nougat – https://android-developers.googleblog.com/2016/07/changes-to-trusted-certificate.html
- [Q30] AOSP: DNS Resolver (mDNS `.local` seit November 2021) – https://source.android.com/docs/core/ota/modular-system/dns-resolver
- [Q31] ctrl.blog: mDNS and DNS-SD slowly making their way into Windows 10 – https://ctrl.blog/entry/windows-mdns-dnssd

Lokale Datenblätter (Register `docs/datasheets/_staging/INDEX_gateway.csv`):
`Espressif_ESP32-S3-WROOM-1_Datasheet_v1.8.pdf`, `Espressif_ESP32-S3_Datasheet_v2.2.pdf`,
`Espressif_ESP32-C6-WROOM-1_Datasheet_v1.4.pdf`, `RaspberryPi_Zero2W_ProductBrief_2024-04.pdf`.
