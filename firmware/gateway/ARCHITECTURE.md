# fluidi – Gateway-Architektur (plattformneutral)

| | |
|---|---|
| Dokument | `firmware/gateway/ARCHITECTURE.md` |
| Version | 0.1 (Entwurf zur Prüfung) |
| Datum | 2026-11-07 |
| Autor | Software-Agent (Phase 4d, Welle 1) |
| Grundlagen | `REQUIREMENTS.md` v1.0 (Kap. 4, 6.4, 7, 8), `CONCEPTS.md` Kap. 5, `research_gateway.md`, D-006…D-012 |
| Schnittstellen | PWA: `docs/interfaces/GATEWAY_API.md` + `app/api/openapi.yaml`; Funk: `firmware/PROTOCOL.md` (parallel) |
| Status | **Plattform offen** (Projektleiter 2026-11-07): ESP32-S3 (Konzept E6) oder Raspberry Pi Zero 2 W. Kap. 1–10 gelten für beide, Kap. 11/12 skizzieren je eine Umsetzung, Kap. 13 vergleicht. |

Kennzeichnungen: **ANNAHME**, **PROTOTYP-PRÜFUNG**, **ABGLEICH PROTOCOL** (mit `firmware/PROTOCOL.md` abzustimmen).

---

## 1 Aufgaben und Grenzen

Das Gateway ist dauernd versorgt, steht im Firmen-WLAN (RB-04) und ist die einzige Stelle, die mit den Sensoren
funkt (BLE-Central) und die PWA ausliefert. Es

1. empfängt Messwerte und Pufferinhalte der Sensoren (REQ-LOG-02), dedupliziert und speichert sie dauerhaft
   (REQ-GW-01, ≥ 2 Jahre volle Auflösung bei 30 Sensoren im Standardprofil),
2. verwaltet Sensoren: Kopplung mit Schlüsselvereinbarung (REQ-RF-05), Konfiguration, Entkopplung (REQ-GW-03),
3. synchronisiert die Zeit der Sensoren (REQ-SYS-07, REQ-GW-09),
4. verteilt signierte Sensor-Firmware (REQ-FW-02/04, UC-08),
5. bietet PWA + REST-API + Server-Sent Events über HTTPS (REQ-GW-02, REQ-APP-02), optional MQTT (REQ-SYS-10),
6. erstellt und spielt Backups ein (REQ-GW-06) und lässt sich selbst sicher aktualisieren (REQ-GW-11).

Nicht im Gateway: private Signierschlüssel (Firmware, CA), Cloud-Dienste, Fernwartungsdienste (REQ-SAF-NET-02).

## 2 Komponenten (logisch, für beide Plattformen gleich)

```
              ┌──────────────────────────── Gateway ────────────────────────────┐
 Sensoren ◄──►│ BLE-Central ─► Protokoll/Krypto ─► Ingest (Dedupe, Zeit) ─► Speicher │
  (BLE)       │      ▲               │                       │            (Messwerte,│
              │      │        Befehlswarteschlange ◄── Jobs ◄─┤             Konfig,    │
              │      │        (Messen, Konfig, Zeit, OTA)     │             Schlüssel) │
              │  OTA-Verteiler ◄── Abbild-Ablage (Signatur geprüft)                   │
              │                                                                       │
 PWA/Browser ◄┼─ HTTPS-Server ─ REST-API ─ Auth/Sitzungen ─ SSE-Broker ◄── Ereignisse │
  (WLAN)      │      │ statische PWA (im Software-Abbild)                            │
              │  Zeitdienst (NTP → RTC → Browser)   Backup/Restore   MQTT (optional)  │
              │  mDNS fluidi.local                  Ereignisprotokoll  Watchdog       │
              └───────────────────────────────────────────────────────────────────────┘
```

| Komponente | Aufgabe | Schnittstelle |
|---|---|---|
| BLE-Central | Scannen, Verbinden, GATT-Austausch, max. 3 parallele Verbindungen | PROTOCOL |
| Protokoll/Krypto | Sitzungsschlüssel je Sensor, Integrität, Replay-Schutz (REQ-RF-06) | PROTOCOL |
| Ingest | Duplikate, Zeitrekonstruktion, Plausibilität, Quittung erst nach dauerhaftem Schreiben | Kap. 4 |
| Speicher | Messwerte (Ringpuffer/Tabelle), Konfiguration, Schlüssel | Kap. 3 |
| Jobs + Befehlswarteschlange | asynchrone Aufträge der API, ausstehende Befehle je Sensor | API Kap. 5 |
| OTA-Verteiler | Signaturprüfung, Übertragung, Fortschritt | Kap. 7 |
| HTTPS/REST/SSE | PWA, API, Live-Ereignisse | GATEWAY_API.md |
| Auth | Passwort, Sitzungen, CSRF, Sperre, elevate | API Kap. 3 |
| Zeitdienst | Gateway-Zeit, Gültigkeit, Verteilung an Sensoren | Kap. 5 |
| Backup | Export/Import aller Daten inkl. Schlüssel | Kap. 8 |
| MQTT (optional) | Veröffentlichen + Home-Assistant-Discovery, nur ausgehend zu einem LAN-Broker | Kap. 10 |

Die **Referenzimplementierung der API** ist `app/dev/mock_server.py` (Python). Sie ist so geschnitten, dass sie
für die Pi-Variante weiterverwendet werden kann (Kap. 12.6).

## 3 Datenmodell und Speicherbedarf

### 3.1 Logisch
- `gateway` (ID, Version, Einstellungen), `auth` (Passwort-Hash, Salt, Sitzungen)
- `sensor` (ID `fluidi-XXXX`, Slot-Nr., Schlüsselmaterial, HW/FW-Version, Batterie, RSSI, letzte Sequenznummer,
  Zeitbasis, Konfiguration inkl. ausstehender Änderungen)
- `plant` (ID, Name, Substrat, Schwelle, Giessen-LED, Notiz) und `assignment` (sensor, plant, von, bis) → UC-11
- `calibration` (sensor, substrat, dry/wet Rohwert+Temperatur+n+σ, k, Quelle, Zeit) — mit Historie
- `reading` (sensor, seq, t, raw, temp, batt_mv, rssi, flags) — **nur Rohwerte**; Feuchteindex wird beim Lesen
  berechnet (API Kap. 7), dadurch rückwirkende Kalibrierung möglich
- `event_log` (Ringpuffer, z. B. 1000 Einträge), `job` (nur im RAM), `sensor_image` (Metadaten + Datei)

### 3.2 Binärer Messwert-Datensatz (für beide Plattformen als Austausch-/Backupformat)
24 Byte, little-endian: `t u32` (Unix-s UTC) · `seq u32` (Sensor-Sequenz, ABGLEICH PROTOCOL) · `raw u32` ·
`slot u16` · `temp i16` (0.01 °C) · `batt_mv u16` · `rssi i8` · `flags u8` · `crc16 u16` (CRC-16/CCITT über
Byte 0–21) · `res u16`.

### 3.3 Menge (REQ-GW-01)
30 Sensoren × (6 + 2 manuell) = 240 Werte/Tag → 2 Jahre = 175 200 Datensätze.

| Format | 2 Jahre | 5 Jahre (Soll) | 96/Tag, 2 Jahre |
|---|---|---|---|
| 24-B-Datensatz (Ringpuffer, ESP32) | 4.2 MB | 10.5 MB | 30 × 98 × 730 × 24 B = 51.5 MB |
| SQLite (ANNAHME ≈ 60 B/Zeile inkl. Index, Pi) | ≈ 10.5 MB | ≈ 26 MB | ≈ 129 MB |

Rechnung: 175 200 × 24 B = 4 204 800 B; × 2.5 = 10.5 MB. Folgerung: ESP32 (9 MB Datenpartition, Kap. 11.2)
erfüllt das Muss; das Soll 5 Jahre nur mit Verdichtung (Tagesmittel/-min/-max je Sensor: 30 × 365 × 3 J × 16 B
≈ 0.5 MB). Pi (SD-Karte) hält alle Fälle in voller Auflösung. Die API meldet `storage.forecast_days`; die PWA
warnt, wenn die Reserve bei hohem Intervall unter 2 Jahre fällt.

## 4 Datenpfad Sensor → Speicher (Fehlerfälle)

| Fall | Behandlung |
|---|---|
| **Duplikat** (gleiche `seq` nochmals, z. B. Quittung verloren) | Schlüssel `(sensor, seq)` eindeutig; Gateway führt je Sensor die höchste lückenlos quittierte `seq` und eine Bitmaske der letzten 1024 `seq` → Duplikat verwerfen, trotzdem quittieren |
| **Nachlieferung Puffer** (UC-10, bis 60 Tage) | Blockweise holen, je Block dauerhaft schreiben, **erst dann quittieren** (Sensor löscht erst nach Quittung, REQ-LOG-02); SSE nur für den neuesten Wert; Flag 3 |
| **Zeitsprung Sensor** (Batteriewechsel ohne Gateway: nur relative Zeit seit Boot, REQ-SYS-07) | Sensor liefert `boot_id` + Relativzeit; Gateway rechnet `t = t_gw_jetzt − (rel_jetzt − rel_wert)`; Flag 1; Driftkorrektur nur, wenn Sensor beide Zeitbasen kennt (ABGLEICH PROTOCOL) |
| **Zeitsprung Gateway** (NTP korrigiert stark, RTC leer) | Gateway-Zeit gilt erst nach gültiger Quelle; bis dahin Flag 2 und keine Zeitverteilung; Sprünge > 10 min ins Ereignisprotokoll |
| **Werte in der Zukunft / weit zurück** | > 5 min Zukunft oder vor Kopplungsdatum → speichern mit Flag 4, nicht für „letzter Wert“ verwenden |
| **Unbekannter Sensor** | Nur im Kopplungsfenster als Kandidat sichtbar; sonst ignorieren (kein Verbindungsaufbau, keine Speicherung); Häufung ins Ereignisprotokoll (Rate-Limit) |
| **Ungültige Signatur/MAC, Replay** | Verwerfen, Zähler im Ereignisprotokoll, Verbindung trennen (REQ-RF-06) |
| **Stromausfall beim Schreiben** | ESP32: LittleFS ist stromausfallfest (research_gateway [Q8]) + CRC je Datensatz; Pi: SQLite WAL + `synchronous=FULL`; in beiden Fällen Quittung erst nach Persistenz → kein Verlust (REQ-GW-05) |
| **Sensor entkoppelt, Werte kommen noch** | Schlüssel gelöscht → wie unbekannt |

Ablauf je Kontakt (ABGLEICH PROTOCOL): verbinden → authentisieren → Werte/Puffer holen → speichern → quittieren →
ausstehende Befehle senden (Messen, Konfig, Schwelle als Rohwert, LED-Fenster, Zeit) → trennen.
Für den Giessen-Hinweis an der LED (REQ-UI-07) rechnet das Gateway die Schwelle in einen **Rohwert-Schwellwert**
mit der aktuellen Kalibrierung um; der Sensor braucht so keine Kalibriermathematik (ANNAHME, ABGLEICH PROTOCOL).

## 5 Zeit (REQ-GW-09, REQ-SYS-07)

Reihenfolge: **NTP** (öffentlich oder Firmen-NTP, abschaltbar, OP-08) → **RTC** mit Pufferung ohne Ladepfad
(OP-K14, S2-W06; Baustein offen) → **Browserzeit** einer angemeldeten PWA, nur wenn sonst keine gültige Zeit.
Ohne gültige Zeit: keine Zeitverteilung an Sensoren, Werte mit Flag 2. RTC wird bei jeder NTP-Synchronisation
nachgestellt. Gangabweichung ±2 min/Monat ≈ ±46 ppm muss die RTC ohne Referenz einhalten (Baustein so wählen).
Zeitzone für LED-Fenster und Tagesmittel: IANA-Name (`Europe/Zurich`), Umrechnung im Gateway.

## 6 BLE-Strategie

- Dauerhaftes **passives Scannen** (Scan-Fenster = Scan-Intervall), Filter auf fluidi-Dienst/Herstellerdaten;
  Sensoren senden verbindbares Advertising (Takt = Reaktionszeit, ABGLEICH PROTOCOL).
- Verbindung nur, wenn (a) der Sensor Daten anzeigt (Flag im Advertising), (b) ein Befehl aussteht oder (c) im
  Kopplungsfenster. Max. 3 gleichzeitige Verbindungen, sonst Warteschlange (research_gateway 2.4).
- Schlüssel auf Anwendungsebene in der eigenen Datenbank (nicht BLE-Bonding) → plattformunabhängig und im Backup.
- Koexistenz WLAN/BLE (ESP32: ein Funkteil) bzw. BT-4.2-Chip (Pi) → **PROTOTYP-PRÜFUNG** OP-K12:
  1000 × „Jetzt messen“ unter WLAN-Last, 95-%-Quantil der Reaktionszeit, Anteil verpasster Advertisings.

## 7 OTA zum Sensor (REQ-FW-02/03/04)

- Sensor: CC2340R52 mit MCUboot (CONCEPTS 5.3, OP-K8). Abbilder signiert (ECDSA), Sicherheitszähler gegen
  Rückfall; privater Schlüssel nur offline beim Entwickler.
- Gateway: prüft beim Hochladen Signatur (öffentlicher Schlüssel im Gateway-Abbild), Format, HW-Kennung,
  Zähler ≥ installiert; speichert maximal 2 Abbilder.
- Übertragung nur über den authentisierten Kanal: Anwendungsbefehl „OTA-Fenster öffnen“ → Sensor prüft Batterie-
  schwelle → Blöcke mit Bestätigung/Wiederaufnahme → Sensor prüft Signatur im Bootloader → Test-Boot → Bestätigung.
  Abbruch an jeder Stelle lässt die alte Version lauffähig (REQ-FW-03). Ein Sensor gleichzeitig.
- Transportprotokoll (TI-OAD oder eigener GATT-Dienst, SMP-ähnlich): ABGLEICH PROTOCOL.

## 8 Backup / Restore (REQ-GW-06, UC-14)

Format `.fbk` v1: `"FLUIDIBK"` · Version u16 · Gateway-ID · Erstellzeit · KDF-Parameter (PBKDF2-HMAC-SHA256,
Salt 16 B, Iterationen) · Nonce 12 B · AES-256-GCM-Chiffrat · Tag 16 B. Klartext = Tar-ähnlicher Container:
`manifest.json`, `config.json` (Pflanzen, Zuordnungen, Kalibrierungen, Einstellungen), `keys.bin`
(Sensorschlüssel), `readings.bin` (Datensätze 3.2), `events.json`. Nicht enthalten: TLS-Schlüssel, WLAN-Daten,
Passwort-Hash (neues Gerät behält eigene). Gleiches Format für beide Plattformen → **Plattformwechsel ESP32 ↔ Pi
per Backup möglich**. Streaming (kein vollständiges Laden in den RAM).

## 9 Sicherheitskonzept (REQ-SAF-NET-01…04, REQ-RF-06, REQ-FW-04)

| Thema | Massnahme |
|---|---|
| Offene Ports (NET-02) | TCP 443 (HTTPS), TCP 80 (nur Weiterleitung + `ca.crt`), UDP 5353 (mDNS); ausgehend NTP (UDP 123) und optional MQTT. **Keine** Fernwartung (kein SSH/Telnet/Debug-Port im Auslieferungszustand). Nachweis per Portscan (`nmap -p- -sU --top-ports 100 fluidi.local`) |
| HTTPS (APP-02, NET-04) | Einmal-CA mit Name Constraints `fluidi.local`, CA-Schlüssel nur im RAM des PC erzeugt und verworfen; Gateway erzeugt eigenen Schlüssel, PC signiert nur den CSR; Zertifikat ≤ 825 Tage, Warnung 60 Tage vorher |
| Anmeldung (NET-01) | kein Standardpasswort, Einrichtungscode nur über USB, PBKDF2, Sperre, CSRF, elevate (API Kap. 3) |
| Firmennetz (NET-03) | ein WLAN-Client, feste Datenflüsse: LAN-Browser → 443; Gateway → NTP; optional Gateway → LAN-MQTT. Kein eingehender Verkehr aus dem Internet |
| Gateway-Software | nur signierte Updates; A/B mit Rückfall (GW-11); Details je Plattform Kap. 11/12 |
| Geheimnisse | Sensorschlüssel, TLS-Schlüssel, WLAN-Passwort, Passwort-Hash verschlüsselt bzw. geschützt gespeichert (Kap. 11/12) |
| Sensor-Firmware | Signatur Pflicht, Signierschlüssel nie auf dem Gateway (FW-04) |
| Physischer Zugang | USB-Konsole erlaubt: ID/CSR lesen, Zertifikat setzen, WLAN setzen, **Passwort-Reset** (neuer Einrichtungscode, Daten bleiben, UC-16). Rest-Risiko: wer das Gateway in der Hand hat, kann das Passwort zurücksetzen und ein Backup (mit Sensorschlüsseln) ziehen. Akzeptiert für Eigengebrauch im Büro; Gateway nicht frei zugänglich aufstellen |

### 9.1 Erstinbetriebnahme ohne Display (UC-01) – Bewertung

| Variante | Ablauf | + | − | Bewertung |
|---|---|---|---|---|
| **A USB + Einrichtungsprogramm am PC** | Gateway per USB an PC; Programm liest ID + CSR, erzeugt Einmal-CA im RAM, signiert, schreibt Zertifikat + WLAN, zeigt **Einrichtungscode** und CA-Fingerabdruck | physischer Zugang = Vertrauensanker; löst HTTPS, WLAN und Erstpasswort in einem Schritt; deckt UC-16 ab | braucht einen PC; Programm muss auf Windows laufen | **empfohlen** |
| A1 als Web-Serial-Seite (Chrome/Edge Desktop) | wie A, im Browser: WebCrypto (CA-Schlüssel `extractable:false`, verschwindet mit dem Tab) | keine Installation, Schlüssel garantiert nur im RAM | nur Chromium-Desktop; Web Serial braucht sicheren Kontext (z. B. `http://localhost`) – Auslieferung der Seite (Datei/kleiner lokaler Server) **ANNAHME, prüfen**; X.509-Erzeugung in JS selbst schreiben | Favorit für Windows-Nutzer, Aufwand mittel |
| A2 als Python-Skript (CLI) | `fluidi-setup` mit `cryptography` + `pyserial` | schnell gebaut, testbar | Python + 2 Pakete auf dem PC nötig (Installation durch Auftraggeber) | Entwicklungs-/Rückfallweg |
| B Einrichtungs-AP + Captive Portal | Gateway öffnet `fluidi-setup-XXXX`, Handy verbindet, gibt WLAN ein | kein PC | **kein HTTPS** möglich (CA noch nicht da) → WLAN-Passwort im offenen/gemeinsamen AP; Zertifikat trotzdem über PC; Android verlässt WLAN ohne Internet | nur als **Notfallmodus** (WLAN neu setzen), nicht für Erstinbetriebnahme |
| C BLE-Provisionierung (z. B. Espressif-App / Improv) | WLAN per Handy-App | bequem | fremde App, löst HTTPS nicht | verworfen |
| D Pi: SD-Karte am PC vorbereiten | Konfigurationsdatei auf die Boot-Partition | Pi-üblich | Geheimnisse liegen auf der Karte; CA-Prozess trotzdem nötig | nur Pi, ergänzend zu A |

Empfehlung: **A** (zuerst A2 für die Entwicklung, A1 für den Auftraggeber), **B** nur als Notfall-WLAN-Modus
nach Tastendruck/USB-Befehl, 10 min begrenzt, WPA2 mit zufälligem Schlüssel aus der USB-Ausgabe.

## 10 MQTT / Home Assistant (REQ-SYS-10, Kann)
Nur ausgehend zu einem Broker im LAN, TLS optional, Zugangsdaten im geschützten Speicher. Topics
`fluidi/<sensor>/state` (JSON: Feuchte, Temperatur, Batterie, RSSI, Zustand) mit `retain`; Discovery unter
`homeassistant/sensor/fluidi_<id>_<grösse>/config`. Kein Abonnieren von Befehlen in v1 (keine zusätzliche
Angriffsfläche). Standardmässig aus.

---

## 11 Umsetzung A: ESP32-S3 (Seeed XIAO ESP32-S3 Plus)

### 11.1 Hardware-Eckdaten (belegt)
- SoC **ESP32-S3R8**, **8 MB PSRAM** (Octal, im Gehäuse), **16 MB Flash** extern: Wiki-Auszug
  `docs/references/Seeed_XIAO-ESP32S3_Wiki_Auszug_2026-11-07.txt` („On-chip 8MB PSRAM & 16MB Flash“, Prozessor
  ESP32-S3R8); Schaltplan `docs/datasheets/Seeed_XIAO-ESP32S3-Plus_Schematic_V1.1-260115.pdf` S. 3 (Block
  „Internal PSRAM“, „External Flash“) und S. 4 (Flash-Baustein **PY25Q128HA**). ESP32-S3R8: 8 MB Octal-PSRAM,
  Umgebung −40…65 °C (`docs/datasheets/Espressif_ESP32-S3_Datasheet_v2.2.pdf`, S. 13, Tab. 1-1 „ESP32-S3 Series Comparison“).
- 512 KB SRAM, 16 KB RTC-SRAM, 4096 bit eFuse (ebd. S. 4).
- Secure Boot (RSA-PSS, Hardware-Vertrauensanker) S. 48 Abschn. 4.1.4.4; Flash-Verschlüsselung XTS-AES
  S. 49 Abschn. 4.1.4.7; SHA-Beschleuniger S. 47 Abschn. 4.1.4.1.
- Board hat eine Li-Ladeschaltung (BAT-Pads): im Gateway **unbeschaltet** lassen (S2-W06).

### 11.2 Partitionsschema (16 MB = 0x1000000)

| Name | Typ | Offset | Grösse | Zweck |
|---|---|---|---|---|
| bootloader | – | 0x0 | bis 0x10000 | 2nd-Stage-Bootloader (mit Secure Boot V2 grösser, daher Tabelle verschoben, ANNAHME → Build prüfen) |
| partition table | – | 0x10000 | 0x1000 | `CONFIG_PARTITION_TABLE_OFFSET=0x10000` |
| nvs | data/nvs | 0x11000 | 0x6000 (24 KB) | Einstellungen, Sensorschlüssel, Passwort-Hash, WLAN (NVS-Verschlüsselung) |
| nvs_keys | data/nvs_keys | 0x17000 | 0x1000 | Schlüssel der NVS-Verschlüsselung (flash-verschlüsselt) |
| otadata | data/ota | 0x18000 | 0x2000 | aktive App |
| phy_init | data/phy | 0x1A000 | 0x1000 | Funk-Kalibrierung |
| ota_0 | app | 0x20000 | 0x300000 (3 MB) | Gateway-Firmware **inkl. PWA** (gzip, ≈ 0.1 MB, research_gateway 5) |
| ota_1 | app | 0x320000 | 0x300000 (3 MB) | A/B-Update (REQ-GW-11) |
| sensorfw | data/0x40 | 0x620000 | 0x100000 (1 MB) | 2 Sensor-Abbilder à ≤ 512 KB (CC2340R52 hat 512 KB Flash) |
| coredump | data/coredump | 0x720000 | 0x10000 | Absturzanalyse (REQ-FW-07) |
| data | data/littlefs | 0x730000 | 0x8D0000 (9 240 576 B) | Messwerte, Konfig-Dateien, Ereignisse, TLS-Zertifikat |

Summe: 0x730000 + 0x8D0000 = 0x1000000 ✔. 4.2 MB Messwerte (2 Jahre) + Verdichtung passen mit ≈ 50 % Reserve.

### 11.3 Speicherorganisation (LittleFS)
Monatsdateien `/m/YYYY-MM.fld` (Kopf 32 B + Datensätze 3.2), Anhängen nur; nachgelieferte Werte gehen in die Datei
ihres Monats. Verdichtung ältester Monate in `/sum/YYYY.fls` (Tagesstatistik), wenn freier Platz < 10 %.
Beim Start wird im PSRAM ein Tages-Index je Sensor aufgebaut (30 × 730 × 16 B ≈ 350 KB) → Jahresansicht ohne
Dateiscan; Tag/Woche/Monat lesen nur 1–2 Monatsdateien (≈ 180 KB/Monat). Schreiblast ≈ 6 KB/Tag → Verschleiss
vernachlässigbar (Flash ≥ 100 000 Zyklen, `Espressif_ESP32-S3-WROOM-1_Datasheet_v1.8.pdf` S. 30 Tab. 6-8,
gilt für das WROOM-Modul; PY25Q128HA-Datenblatt **fehlt lokal** → OP-GW-1).

### 11.4 RAM-Budget (ANNAHME, Messung mit `heap_caps_get_info` am Muster)

| Block | intern (512 KB SRAM) | PSRAM (8 MB) |
|---|---|---|
| ESP-IDF, FreeRTOS, Tasks-Stacks | ≈ 60–80 KB | – |
| WLAN-Treiber | ≈ 50–70 KB | Puffer teilweise |
| BLE (NimBLE, 3 Verbindungen) | ≈ 50–70 KB | – |
| TLS: 2–4 Sitzungen à 40–50 KB Handshake (research_gateway [Q10]) | – | 200 KB |
| HTTP-Server + SSE (4 Streams) | ≈ 20 KB | 64 KB |
| Tages-Index, Caches, Jobs | – | ≈ 0.5 MB |
| Reserve | ≥ 100 KB | > 7 MB |

### 11.5 Software
ESP-IDF (C), NimBLE, `esp_https_server`, LittleFS, SNTP, mDNS, `esp_https_ota` mit Rollback. Rechenregeln aus
`app/tests/vectors/calc_vectors.json` als Unit-Test (Host-Build). Watchdog + Coredump (REQ-FW-07).
Sicherheit: **Secure Boot V2 + Flash-Verschlüsselung** im Release-Modus für das ausgelieferte Gateway, im
Entwicklungsmodus für Muster (eFuses irreversibel → Entscheid OP-GW-2). Danach funktioniert der ROM-Download per
USB nur noch eingeschränkt; Provisionierung läuft über die eigene USB-Konsole der Firmware.

### 11.6 Bewertung
+ günstig (≈ CHF 30–40), < 1 W, Start < 2 s, minimale Angriffsfläche, kein Dateisystem-Verschleiss-Thema.
− C-Entwicklung aufwendig (BLE-Client, OTA-Client, HTTPS, Speicher selbst), begrenzt erweiterbar (Analyse,
grössere Datenmengen), Koexistenz WLAN/BLE im selben Funkteil.

---

## 12 Umsetzung B: Raspberry Pi Zero 2 W (Linux, Python, SQLite)

### 12.1 Hardware-Eckdaten (belegt)
512 MB LPDDR2, 2.4 GHz 802.11 b/g/n, Bluetooth 4.2 mit BLE, microSD, USB-OTG
(`docs/datasheets/RaspberryPi_Zero2W_ProductBrief_2024-04.pdf`, S. 2); Versorgung 5 V DC 2.5 A, Betrieb
−20…70 °C, Produktion zugesichert (S. 3). Keine RTC (S. 2: nicht aufgeführt) → externe RTC wie bei A.

### 12.2 Software-Stapel (Vorschlag)
| Schicht | Wahl | Bemerkung |
|---|---|---|
| OS | Raspberry Pi OS Lite (64 bit), minimal | nur benötigte Pakete, keine Desktop-Dienste |
| Dienst | Python 3, ein Prozess `fluidi-gateway` unter **systemd** (eigener Benutzer, `ProtectSystem=strict`, `NoNewPrivileges`, `CapabilityBoundingSet` nur `CAP_NET_BIND_SERVICE` + BLE) | Watchdog `WatchdogSec` (REQ-FW-07) |
| BLE | **bleak** (BlueZ über D-Bus) | Central, Scan, GATT |
| HTTP | asyncio-Server (z. B. aiohttp) oder der Mock-Kern erweitert; TLS über Python `ssl` | gleiche Routen wie `mock_server.py` |
| Datenbank | **SQLite**, WAL, `synchronous=FULL`, Tabellen nach 3.1, Index `(sensor, t)`, eindeutig `(sensor, seq)` | Backup-Export im Format Kap. 8 |
| Zeit | `systemd-timesyncd` oder chrony (NTP, abschaltbar), RTC per Device-Tree-Overlay (`hwclock`) | Browserzeit wie A |
| mDNS | Avahi, Hostname `fluidi` | |
| OTA Sensor | Python-Client für das gewählte Transportprotokoll (MCUboot/SMP-ähnlich bzw. TI-OAD), Referenz `smpclient` (Apache-2.0, research_gateway [Q12]) | Signaturprüfung mit `cryptography` |
| MQTT | paho-mqtt (optional) | |

### 12.3 Schutz gegen SD-Verschleiss und Stromausfall (REQ-GW-05)
- **Read-only-Root mit overlayfs** (raspi-config „Overlay File System“), Schreibzugriffe nur auf eigene
  Datenpartition (ext4, `noatime`, `commit=60`) oder ein USB-Stick/SSD.
- Schreibrate klein halten: Messwerte in Transaktionen bündeln (Quittung an den Sensor erst nach `COMMIT`);
  Logs nur ins RAM (`journald Storage=volatile`) plus Ereignistabelle in SQLite; kein Swap.
- Industrial-microSD (pSLC) empfohlen (CONCEPTS 5.1); tägliche lokale Sicherung der Datenbank auf die zweite
  Partition (rotierend) + Backup über die PWA.
- Abschätzung Schreiblast: 240 Werte/Tag ≈ 15–60 KB/Tag inkl. WAL (ANNAHME) → vernachlässigbar; Hauptrisiko ist
  Korruption bei Stromausfall → WAL + Read-only-Root.

### 12.4 Sicherheit
- Kein SSH im Auslieferungszustand (Dienst deaktiviert; für Entwicklung nur per USB-Gadget-Konsole), Firewall
  (nftables) nur 80/443/5353 eingehend, Updates nur als signiertes Paket bzw. Image über die PWA/USB, nie
  automatisch aus dem Internet (REQ-SYS-01).
- Geheimnisse (Sensorschlüssel, TLS-Schlüssel) in Dateien mit Rechten 0600 des Dienstbenutzers; optional
  verschlüsselte Datenpartition (LUKS, Schlüssel auf dem Gerät → schützt nur gegen Diebstahl der Karte allein).
  Kein Secure Boot gleichwertig zum ESP32 auf dem Pi Zero 2 W (ANNAHME, nicht recherchiert) → physischer Zugang
  zur SD-Karte = Zugriff auf alle Daten. Rest-Risiko dokumentieren.
- A/B-Update: zwei Root-Partitionen oder Python-Paket mit Versionsordnern + Symlink-Umschaltung und Rückfall bei
  fehlgeschlagenem Start (systemd `OnFailure`). Daten getrennt (REQ-GW-11).

### 12.5 Bewertung
+ schnelle Entwicklung in Python, SQLite, beliebig erweiterbar (Analyse, Tracking, weitere Dienste), viel Speicher,
Auftraggeber hat Pi-Erfahrung, fertige Bibliotheken (bleak, smpclient, cryptography).
− teurer (≈ CHF 75–80 inkl. Netzteil, RTC, Industrial-SD; research_gateway 2.1), Lieferbarkeit schwankend,
Linux-Pflege (Sicherheitsupdates ohne Internetzugang nur manuell als Image/Paket), SD-Karte, Start 20–40 s,
grössere Angriffsfläche, BT 4.2 (Reichweite/Koexistenz **PROTOTYP-PRÜFUNG**), Leistung ≈ 0.5–1 W (ANNAHME).

### 12.6 Vom Mock zum Pi-Backend
`app/dev/mock_server.py` implementiert bereits alle Routen, Auth (PBKDF2, Sitzungen, CSRF, Sperre, elevate),
Jobs, SSE, CSV und Kalibrierungsrechnung (`fluidi_calc.py`). Ausbau-Schritte:
1. `State` in **Repository** (SQLite) und **Simulation** trennen; Testdaten-Generator nur im Mock.
2. Routen-Tabelle (`ROUTES`) behalten, Server auf asyncio umstellen (BLE und HTTP im selben Ereignis-Loop).
3. `run_measure`/Pairing/Rollout gegen einen echten **BLE-Adapter** (bleak) mit Schnittstelle
   `SensorLink.request(sensor, command)` austauschen; Mock-Adapter bleibt für Tests.
4. Die Tests `app/tests/test_mock_api.py` laufen unverändert gegen das echte Backend (Konformität).

---

## 13 Vergleich und offene Entscheide

| Kriterium | ESP32-S3 | Pi Zero 2 W |
|---|---|---|
| Kosten Gateway | ≈ CHF 30–40 | ≈ CHF 75–80 |
| Speicher 2 J./5 J. Standardprofil | 4.2 MB ✔ / nur verdichtet | ✔ / ✔ |
| 96/Tag über 2 Jahre | ✘ (51.5 MB) | ✔ |
| Erweiterbarkeit (Analyse, Tracking) | gering | hoch |
| Entwicklungsaufwand | hoch (C) | niedrig–mittel (Python) |
| Robustheit Stromausfall | sehr gut (LittleFS) | gut mit Overlay + WAL |
| Angriffsfläche / Pflege | minimal | grösser, Linux-Pflege |
| Firmware-Schutz | Secure Boot + Flash-Verschlüsselung | eingeschränkt |
| PWA/API/Tests | identisch | identisch |

| Nr. | Offener Punkt | Wer |
|---|---|---|
| OP-GW-0 | **Plattformentscheid** ESP32-S3 vs. Pi Zero 2 W | Auftraggeber |
| OP-GW-1 | PY25Q128HA-Datenblatt (Zyklenfestigkeit) lokal ablegen | Software/Projektleitung |
| OP-GW-2 | ESP32: eFuses Release-Modus (irreversibel) ja/nein | Auftraggeber + Sicherheit |
| OP-GW-3 | RTC-Baustein ohne Ladepfad (OP-K14) für beide Varianten | Elektronik |
| OP-GW-4 | Koexistenz-/Reichweitentest (OP-K12) mit der gewählten Plattform | Prototyp |
| OP-GW-5 | Einrichtungsprogramm A1 (Web Serial) vs. A2 (Python) | Software, nach Plattformentscheid |
| OP-GW-6 | Abgleich mit `firmware/PROTOCOL.md` (Kap. 4, 6, 7) | Firmware + Software |
