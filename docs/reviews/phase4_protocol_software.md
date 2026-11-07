# Prüfung `firmware/PROTOCOL.md` v0.1 aus Gateway-Sicht (Phase 4, Welle 2)

| | |
|---|---|
| Prüfer | Software-Agent (Gateway Pi Zero 2 W + PWA) |
| Datum | 2026-11-07 |
| Geprüft | `firmware/PROTOCOL.md` (Protokollversion 1, Dokumentversion 0.1) gegen `docs/interfaces/GATEWAY_API.md`, `app/api/openapi.yaml`, `firmware/gateway/ARCHITECTURE.md`, D-014, D-018, D-020, D-021 |
| Methode | Gateway-Seite vollständig nach PROTOCOL umgesetzt (`firmware/gateway/fluidi_gw/protocol.py`, `central.py`) und gegen einen simulierten Sensor (`simsensor.py`) getestet: Kopplung mit SAS, Sitzung, Nachlieferung, Duplikate, Zeitrekonstruktion, Befehle, OTA, Fehlerfälle (`firmware/gateway/tests/`, 55 Tests grün). Krypto gegen FIPS-197, RFC 5869 und OpenSSL geprüft. **Nicht** geprüft: echte Funkstrecke (bleak/BlueZ am Pi), Sensor-Firmware (noch nicht vorhanden), `firmware/tools/fluidi_proto.py` (fehlt noch, Kap. 14). |
| Regel | Interface-Regel: Änderungen am Protokoll nimmt der Firmware-Agent vor. Dieses Dokument schlägt nur vor. |
| Antwort | Ersteller (Firmware) je Befund: *umgesetzt* / *abgelehnt (Grund)* |

Bewertung: **kritisch** = Ablauf funktioniert so nicht oder Daten/Sicherheit gefährdet; **wichtig** = Interop-Risiko
oder Anforderung nur mit Umweg erfüllt; **klein** = Klarstellung.

## Kritisch

### K-1 HELLO-Frist 0.5 s + Timeout als Fehlversuch → Gateway sperrt sich selbst aus
- **Befund:** Kap. 3 verlangt HELLO innert **0.5 s** nach Verbindungsaufbau; Kap. 4.5 sperrt den Sensor nach
  **3 fehlgeschlagenen Handshakes** 30 min (`LOCKED`). Unter Linux baut bleak/BlueZ die Verbindung auf, macht bei
  nicht gebondeten Geräten eine GATT-Dienstsuche und schreibt danach den CCCD (Notify) – erst dann kann HELLO
  gesendet werden. Die Dauer ist nicht spezifiziert und hängt vom Verbindungsintervall ab, das das Gateway unter
  BlueZ nicht frei setzen kann (W-1). Ist sie > 0.5 s, scheitert **jede** Sitzung, und nach drei Versuchen ist der
  Sensor für das echte Gateway 30 min gesperrt (in der Zeit verpasste „Jetzt messen“, Daten gepuffert).
- **Vorschlag:** (a) Frist an die Gegenseite anpassen: 0.5 s erst ab **CCCD-Write auf TX** zählen (statt ab
  Verbindungsaufbau), absolute Grenze ab Verbindungsaufbau z. B. 3 s. (b) **Nur kryptografische Fehler** (falscher
  MIC/HMAC, falsche `gateway_id`) als Fehlversuch zählen, Zeitüberschreitungen nicht (Energie bleibt durch die
  absolute Grenze begrenzt). (c) PROTOTYP-PRÜFUNG am Pi Zero 2 W: Zeit Verbinden→HELLO messen (OP-GW-8).
  Gateway-seitig umgesetzt: BlueZ-GATT-Cache `Cache = always` (Installationsskript, ANNAHME), HELLO unmittelbar
  nach `start_notify`.

### K-2 Kopplung scheitert an den allgemeinen Sitzungsfristen
- **Befund:** Kap. 4.2 erlaubt **60 s** nach `PAIR_SHOW` für Tastendruck und PWA-Bestätigung. Kap. 3 trennt aber
  „nach **3 s** ohne gültigen Frame (ausser OTA: 30 s) und spätestens nach **10 s** Sitzungsdauer (ausser OTA)“.
  Während der Nutzer die Farben vergleicht, sendet das Gateway keine Frames → der Sensor trennt nach 3 s, die
  Kopplung ist in der Praxis unmöglich.
- **Vorschlag:** Kap. 3 um „ausser Kopplung: 60 s nach PAIR_SHOW, Gesamtdauer ≤ 90 s“ ergänzen. Gateway-seitig
  umgesetzt: wartet bis 60 s auf `PAIR_CONFIRM_S` und die PWA-Bestätigung (`central.py`, Test
  `test_session.Pairing`).

## Wichtig

### W-1 Verbindungsparameter und MTU sind unter BlueZ/bleak nicht vom Gateway steuerbar
- **Befund:** Kap. 2.5 Regel 4 („Gateway setzt“ 7.5–15 ms, Supervision 1 s, MTU 247, DLE 251) ist für ESP-IDF/NimBLE
  geschrieben. bleak 3.0 bietet dafür keine Schnittstelle (API `BleakClient`, abgerufen 2026-11-07); BlueZ wählt
  Intervall und MTU selbst. Laut bleak-Doku kann `mtu_size` unter BlueZ 23 liefern. Kopf von PROTOCOL.md nennt noch
  „Gateway XIAO ESP32-S3, ESP-IDF, NimBLE“, Kap. 4.1 „mbedTLS/esp_fill_random“ (seit D-014 überholt).
- **Vorschlag:** (a) Der **Sensor** fordert nach der Verbindung selbst ein Connection Parameter Update an
  (Peripheral-Request, 7.5–15 ms); Gateway akzeptiert (BlueZ-Standard, ANNAHME – prüfen). (b) Frames bleiben
  ≤ 100 Byte für alle Nicht-Listen-Nachrichten (so schon festgelegt) und Listen richten sich nach der vom **Sensor**
  ausgehandelten MTU (so schon). (c) Gegenseite im Kopf auf „Raspberry Pi Zero 2 W, BlueZ, bleak, Python
  `cryptography`“ ändern. Energiemodell (`T_CONN`) nach Messung am Pi anpassen (FW-P3).

### W-2 OTA_DATA als Write Without Response verträgt sich nicht mit der strikten `ctr`-Regel
- **Befund:** Kap. 4.4: Empfänger akzeptiert nur `ctr` = erwartet, sonst Sitzungsende. Write Without Response darf
  der GATT-Server bei vollem Puffer verwerfen (Flusskontrolle fehlt). Ein verworfener OTA_DATA-Frame erzeugt eine
  `ctr`-Lücke → der nächste Frame beendet die Sitzung; das Go-back-N über `next_offset` (Kap. 9.3) kommt nie zum Zug.
- **Vorschlag:** Für `msg = 0x21` (OTA_DATA) `ctr > erwartet` zulassen (streng monoton, Replay bleibt
  ausgeschlossen, Nonce nie doppelt), danach Go-back-N über `offset`. Alternative: OTA_DATA mit Write Request
  (langsamer). Gateway sendet `window` Frames und wartet dann auf OTA_PROGRESS (umgesetzt, Test
  `test_session.DataPath.test_ota_rollout`).

### W-3 Byte-Reihenfolge `sensor_addr` und Definition `payload()` nicht festgelegt (Interop)
- **Befund:** `sensor_addr` (6 Byte) geht in PAIR_RSP, HKDF-`info` und die CCM-Nonce ein, die Reihenfolge ist nicht
  definiert (BLE-Luftformat LSB zuerst vs. Schreibweise MSB zuerst). Ebenso, ob `payload(PAIR_REQ)` im Transkript
  `vt`/`pmsg` enthält. Abweichung = Kopplung und jede Sitzung scheitern.
- **Vorschlag:** Festlegen: `sensor_addr` in **Luft-Reihenfolge (LSB zuerst)**, `payload()` = Nutzlast **ohne**
  `vt` und `pmsg` (88 bzw. 91 Byte). So im Gateway umgesetzt (`protocol.py`). Testvektoren dazu in Kap. 14
  (fehlendes `fluidi_proto.py`) mit festen Schlüsseln/Nonces aufnehmen.

### W-4 Ringinhalt bei (Neu-)Kopplung nicht geregelt
- **Befund:** Werte, die der Sensor **vor** der Kopplung (oder für ein früheres Gateway) gespeichert und nicht
  quittiert hat, werden nach der Kopplung an das neue Gateway geliefert. Kap. 6 sagt nichts dazu.
- **Vorschlag:** Regel ergänzen, z. B. „Bei erfolgreicher Kopplung gelten alle Datensätze ≤ `seq_last` als
  quittiert“ **oder** ausdrücklich „werden geliefert“. Gateway heute: speichert sie beim Sensor, ordnet sie aber
  keiner Pflanze zu (Zuordnung ab Kopplungszeit, UC-11).

### W-5 Vergleichsrichtung `water_raw`/`air_raw`/`flood_raw` undefiniert
- **Befund:** Kap. 8 legt die Schwellen als Rohwerte fest, aber nicht, ob „giessen“ bei `c_probe < water_raw` gilt.
  Die Kalibrierung (GATEWAY_API 7.1) erlaubt beide Richtungen; der Mock arbeitet mit trocken > nass.
- **Vorschlag:** Festlegen: Kapazität steigt mit der Feuchte → LED „giessen“ bei `c_probe < water_raw`,
  `air` bei `c_probe < air_raw`, `flooded` bei `c_probe > flood_raw`. Gateway sendet die Schwellen so
  (`model.desired_settings`); die Startkalibrierung des Gateways ist trocken < nass (ANNAHME 13.3/40 pF nach
  MESSKETTE_SALZ Kap. 0, PROTOTYP-PRÜFUNG).

### W-6 Kompatibilität und Sicherheitszähler für die Verteilung
- **Befund:** Kap. 9.6 verlangt passende `hw_rev`, nennt aber kein Feld („optional eigenes TLV, ANNAHME“).
  SESSION_INFO meldet den installierten Sicherheitszähler nicht → das Gateway kann „Zähler ≥ installiert“
  (ARCHITECTURE 7) nicht prüfen.
- **Vorschlag:** MCUboot-TLV **0xA0 = hw_rev (u8)** im geschützten Bereich (`imgtool sign --custom-tlv`; ob imgtool
  diesen Wert zulässt, ist **ANNAHME** bis zum Build-Test); SESSION_INFO um `sec_cnt` u32 erweitern
  (angehängt, Kap. 5.3 Erweiterbarkeit). Gateway prüft 0xA0 schon (`mcuboot.py`) und lehnt Abbilder ab, deren Zähler
  kleiner ist als der höchste bereits verteilte.

### W-7 Wochentage für den Giessen-Hinweis fehlen im Protokoll
- **Befund:** API/PWA erlauben Wochentage (`TimeWindow.weekdays`, z. B. Mo–Fr im Büro), Kap. 8 kennt nur ein
  Tagesfenster.
- **Vorschlag:** TLV **0x0F `led_weekdays`** (u8, Bit 0 = Montag … Bit 6 = Sonntag, Werk 0x7F). Bis dahin
  emuliert das Gateway: an ausgeschlossenen Tagen `water_led = 0` (braucht eine Sitzung nach Mitternacht; fällt das
  Gateway aus, bleibt der letzte Zustand).

### W-8 Unauthentisierte ERROR-Frames
- **Befund:** `ERROR {NOT_PAIRED}` und `LOCKED` sind Klartext; ein Angreifer im Funkbereich kann sie fälschen.
- **Vorschlag:** MUSS-Regel ergänzen: „Das Gateway leitet aus ERROR-Frames keine Zustandsänderung ab (kein Löschen
  von Schlüsseln, keine Entkopplung), nur Anzeige.“ So umgesetzt (`central.Session.run`).

### W-9 Nachlieferung grosser Puffer vs. 10-s-Sitzungsgrenze
- **Befund:** `READ_RECORDS {max = 0}` (alle) bei vollem Ring = 1122 Datensätze = 102 Frames. Mit dem BlueZ-Intervall
  (W-1) kann das die 10-s-Grenze sprengen; der Sensor trennt mitten im Block, nichts ist quittiert.
- **Vorschlag:** Regel „Gateway SOLL `max` ≤ 110 verwenden und je Block quittieren“ (so umgesetzt: 110, COMMIT,
  ACK), oder Nachlieferung von der 10-s-Grenze ausnehmen solange RECORDS fliessen.

## Klein

| Nr. | Befund | Vorschlag |
|---|---|---|
| S-1 | OTA_BEGIN `sha256` „über das ganze signierte Image“ ≠ MCUboot-Hash (Kopf + Abbild + geschützte TLVs) | klarstellen „SHA-256 der ganzen Datei“; so umgesetzt (`mcuboot.Image.file_sha256`) |
| S-2 | Nach MEASURE liegt der Datensatz auch im Ring – Quittung nötig? Sonst bleibt `DATA_PENDING` und es folgt eine unnötige Verbindung | Satz in 6.2: „gilt auch für Datensätze aus MEASURE“ (Gateway quittiert lückenlos) |
| S-3 | SET_SETTINGS: behalten nicht gesendete TLVs ihren Wert? | „nicht enthaltene ids bleiben unverändert“ ergänzen (Gateway sendet Teilmenge) |
| S-4 | TIME_SET nur „> 6 h oder Neustart“; bei Sommer-/Winterzeit ändert `tz_min` | „…und wenn sich `tz_min` ändert“ (umgesetzt) |
| S-5 | `charge_uc` „seit letztem Power-on-Reset“: setzt ein Brownout den Zähler zurück? | nichtflüchtig, Nullung nur bei Zellwechsel (POR mit Zelle neu); sonst ist die Restlaufzeit falsch |
| S-6 | Kap. 13 Export `# fluidi-export v1` widerspricht GATEWAY_API Kap. 9 `fluidi-csv v1` | Verweis auf GATEWAY_API 9 statt eigener Spaltenliste |
| S-7 | Kalibrierung: GATEWAY_API 7.3 „Gateway mittelt Einzelwerte“, PROTOCOL liefert je MEASURE einen gemittelten Datensatz | so lassen; Gateway sendet `samples` × MEASURE (purpose 1/2) und mittelt robust – im Protokoll erwähnen |
| S-8 | Sensor-ID: API nutzt `fluidi-XXXX` (16 bit), Protokoll die 48-bit-Adresse | Gateway speichert intern die Adresse, API zeigt `fluidi-XXXX` + `address`; Kollision zweier Kurz-IDs wird beim Koppeln abgelehnt (Wahrscheinlichkeit bei 15 Sensoren ≈ 15·14/2/65536 ≈ 0.16 %) |
| S-9 | Company-ID 0xFFFF (FW-P7) | Gateway filtert zusätzlich auf Magic „fl“ + `adv_fmt` (umgesetzt); keine weitere Auswirkung |

## Offene Punkte – Stand aus Gateway-Sicht

| Nr. | Stand |
|---|---|
| **API-1 / OP-GW-6** (Abgleich PROTOCOL) | **erledigt** bis auf die Befunde oben: Befehlswege (MEASURE/IDENTIFY/UNPAIR/OTA im SECURE-Kanal), Schlüsselaustausch (ECDH + SAS, neuer API-Schritt `POST /pairing/candidates/{device}/confirm`, Job-Zustand `awaiting_confirmation`), Zeit (boot_id/uptime, Rekonstruktion `timesync.py`), Batteriemodell (`charge_uc` + Spannung, Rückfall D-006), Mittelung im Sensor (`avg_count`), Schwelle als Rohwert (`water_raw`), LED-Fenster in Lokalzeit + `tz_min` (API-4) |
| FW-P1 | Gateway-Sicht: dieses Dokument. Sicherheits-Agent separat (Kap. 4, 2.4, 9) |
| FW-P2 | Gateway: Abbild-Prüfung und OTA-Ablauf inkl. Rückfallmeldung (`ota_result`, `slot`) umgesetzt und gegen Simulation getestet; MCUboot am Muster bleibt Firmware/Prototyp |
| FW-P3 | Gateway wartet 6 s auf PAIR_RSP (3 s Frame-Frist + 3 s ECDH, ANNAHME); nach Messung anpassen |
| FW-P4 | Gateway lehnt Abbilder > 226 kB ab (`mcuboot.parse(max_size)`), nach Build-Test nachführen |
| FW-P5 | Energie-Statistik der PWA nutzt Kap. 12 (Schätzung, gekennzeichnet); nach Messung Werte tauschen |
| FW-P6 | Gateway nutzt dieselbe Rückfallschwelle 2.55 V für „Batterie tief“; Restlaufzeit-Rückfall 17 Monate (D-006) |
| FW-P7 | siehe S-9 |
| FW-P8 | `p_miss` in `/etc/fluidi/gateway.toml`, Formel Kap. 2.2 im Gateway (`protocol.adv_interval_ms`, Test 27.5/57.5/147.5 s); das Gateway misst je Sensor den Anteil verpasster Advertisings (Statistik „verpasst“) als Grundlage für OP-K12 |

---

## Runde 2 – Prüfung PROTOCOL.md 0.2 / Protokoll v2 (2026-11-07)

Grundlage: `firmware/PROTOCOL.md` 0.2 (Kap. 0, Ä-1…Ä-16), Antwort `docs/reviews/phase4_firmware_response.md`,
Referenz `firmware/tools/fluidi_proto.py`, Sensor-Code `firmware/sensor/core/fl_app.c` (gelesen, nicht gebaut).
Gateway (`fluidi_gw`), Simulation und PWA sind auf v2 umgestellt. **Nachweis:** `firmware/gateway/tests/test_protocol.py`
Klasse `Reference` – Commitment, PAIR_REQ/RSP, Transkript, K_link/K_conf, SAS, beide MACs, K_s, SECURE-Frame,
Advertising, Datensatz **byte-gleich** mit `fluidi_proto.py` (gleiche feste Eingaben wie `firmware/sensor/tests/gen_vectors.py`);
dazu Sitzungstests (Commitment-Verletzung = Fehlversuch, 9 Fristüberschreitungen ohne Sperre / 10 mit, MEASURE
asynchron, Kalibrierung über mehrere Kontakte, OTA mit `sec_cnt`), alle grün.

### Stand der Befunde aus Runde 1

| Nr | Antwort Firmware | Prüfung Gateway-Seite | Status |
|---|---|---|---|
| K-1 | umgesetzt | Fristen 1 s ab CCCD-Write / 5 s, Fristen kein Fehlversuch, 10 → Sperre (Kap. 3, 4.5; `fl_app.c`). Gateway sendet HELLO direkt nach `start_notify` | **erledigt** (Zeit am Pi: PROTOTYP-PRÜFUNG OP-GW-8) |
| K-2 | umgesetzt | 15 s bis REVEAL, 60 s Farbvergleich, 90 s gesamt; Gateway: `PAIR_RSP_TIMEOUT` 8 s, 60 s, gesamt 88 s | **erledigt** |
| W-1 | umgesetzt | Sensor fordert Intervall selbst an; Kopf nennt Pi/BlueZ/bleak | erledigt (PROTOTYP-PRÜFUNG PP-12) |
| W-2 | umgesetzt | Lücke ≤ 64 nur für OTA_DATA; Simulation und `SecureChannel.open(ota_gap)` gleich umgesetzt, Test | **erledigt** |
| W-3 | umgesetzt | LSB zuerst, payload ohne `vt`/`pmsg`; byte-gleich mit Referenz | **erledigt** |
| W-4 | „werden geliefert“ | Gateway speichert sie beim Sensor, Pflanzenzuordnung ab Kopplungszeit | **erledigt** |
| W-5 | umgesetzt | Richtungen wie vom Gateway angenommen (`c < water_raw` …) | **erledigt** |
| W-6 | umgesetzt | `sec_cnt` (Offset 48) wird gespeichert und bei der Verteilung geprüft (Abbild-Zähler < installiert → abgelehnt); TLV 0xA0 prüft das Gateway beim Hochladen; Fehler 0x4A in den Klartexten | **erledigt** |
| W-7 | umgesetzt | Gateway sendet TLV 0x0F aus `water_window.weekdays`; Emulation über `water_led` entfernt | **erledigt** |
| W-8 | umgesetzt (MUSS) | so umgesetzt | **erledigt** |
| W-9 | umgesetzt | Gateway liest 110 je Block, quittiert je Block | **erledigt** |
| S-1…S-7 | umgesetzt | geprüft (S-1 Datei-SHA-256, S-2 MEASURE-Datensätze quittiert, S-4 TIME_SET bei `tz_min`) | **erledigt** |
| S-8, S-9 | angenommen | – | erledigt |

### Rest-Befunde (Runde 2)

| Nr | Stufe | Befund | Vorschlag |
|---|---|---|---|
| R-1 | **wichtig** | PROTOCOL Kap. 5.1–5.3 nennen noch v1-Werte: „Frame-Version (**1**)“, HELLO `vt=0x10`, HELLO_RSP `0x11`, ERROR `0x1F`, PAIR `0x13`, SECURE `0x12`. Ä-2, Kap. 13, `fluidi_proto.py` und `fl_proto.h` verwenden **0x2t**. Wer nach Kap. 5 implementiert, ist nicht interoperabel. | Kap. 5.1–5.3 auf `vt = 0x20/0x21/0x22/0x23/0x2F` und Frame-Version 2 korrigieren. Gateway folgt der Referenz (0x2t). |
| R-2 | wichtig | MEASURE: Sensor speichert nur **eine** ausstehende Messung (`meas_pending` bool); ein zweites MEASURE in derselben Sitzung liefert dieselbe `seq` und erzeugt keine zweite Messung. Der Sensor trennt 0.3 s nach der Antwort, wenn kein Frame folgt. Beides steht nicht in Kap. 5.4. | Regel ergänzen: „höchstens ein MEASURE je Sitzung, als letzte Anfrage; der Sensor trennt danach“. Gateway hält sich daran (MEASURE zuletzt, Kalibrierung = `samples` Kontakte). |
| R-3 | klein | Kopf nennt „INFO-Format 2“, Kap. 5.5/13 und `FL_INFO_FMT` sagen 1. | Einheitlich 1 (nur angehängt) oder 2; Gateway wertet `info_fmt` nicht aus. |
| R-4 | klein | Kap. 4.3 „Gateway: `esp_fill_random`“ (Rest ESP32); Kap. 2.5 Nummerierung 4, 6, 5. | Text bereinigen (`os.urandom`/`secrets`). |
| R-5 | klein | `fluidi_proto.SAS_COLORS` „gruen“, PWA zeigt „grün“ (nur Anzeige). Bei Dauerangriff 13 µA statt 0.4 µA (Kap. 4.5) ist eine bewusste Folge von K-1. | keine Änderung nötig; PWA zeigt `LOCKED`/Fehlversuche als Hinweis. |

Keine kritischen Rest-Befunde. Offen bleiben die Prüfungen am Gerät (OP-GW-8: Zeit bis HELLO unter BlueZ,
Annahme des Peripheral-Parameter-Requests, MTU; PP-12 MCUboot mit TLV 0xA0).
