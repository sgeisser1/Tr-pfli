# fluidi – Gateway-API (Gateway ↔ PWA)

| | |
|---|---|
| Dokument | `docs/interfaces/GATEWAY_API.md` |
| Version | **1.1-Entwurf** (API-Version `v1`, abwärtskompatibel erweitert in Phase 4 Welle 2) |
| Datum | 2026-11-07 |
| Autor | Software-Agent (Phase 4d, Welle 1) |
| Maschinenlesbar | `app/api/openapi.yaml` (OpenAPI 3.1, normativ für Schemas) |
| Implementierungen | Gateway `firmware/gateway/fluidi_gw/` (Pi, D-014); Mock `app/dev/mock_server.py` (Entwicklung). Beide gegen `openapi.yaml` getestet |
| Plattform | **neutral**: gilt für ESP32-S3 und Raspberry Pi Zero 2 W (siehe `firmware/gateway/ARCHITECTURE.md`) |
| Status | zur Prüfung; Gateway↔Sensor-Funkprotokoll: `firmware/PROTOCOL.md` (Firmware-Agent, parallel) |

Kennzeichnungen: **ANNAHME** = nicht belegt; **PROTOTYP-PRÜFUNG** = erst am Muster nachweisbar;
**ABGLEICH PROTOCOL** = muss mit `firmware/PROTOCOL.md` abgestimmt werden.

---

## 1 Grundsätze

- Basis-URL `https://fluidi.local/api/v1`; PWA und API kommen vom **gleichen Ursprung** (keine CORS-Freigaben).
- JSON (UTF-8). Zeitpunkte in Objekten **ISO 8601 UTC** (`2026-11-07T14:03:00Z`), in Zeitreihen **Unix-Sekunden**.
  Lokalzeit wird nur in der PWA und im CSV gebildet (Zeitzone aus `settings.time.timezone`, Werk `Europe/Zurich`).
- Fehler immer als `{"error": {"code", "message", "field?", "retry_after_s?"}}`, `message` deutsch für die Anzeige
  (Codes Kap. 8).
- Versionierung im Pfad (`/v1`). Erweiterungen sind abwärtskompatibel (neue Felder dürfen hinzukommen; Clients
  ignorieren Unbekanntes). Inkompatible Änderung → `/v2` (REQ-SYS-09).
- Lange Vorgänge (Messen, Kalibrierpunkt, Koppeln, Entkoppeln) sind **asynchron**: `202` + **Job**, Fortschritt
  über `GET /jobs/{id}` und Server-Sent Events (Kap. 6).
- Strikt lokal: die API ruft keine fremden Dienste auf. Einzige Ausnahme im Gateway: NTP (abschaltbar, REQ-SYS-01).

## 2 Datenmodell (fachlich)

```
Pflanze 1 ── 0..1 Sensor (aktuelle Zuordnung)
Pflanze 1 ── * Zuordnungsintervall (sensor_id, von, bis)   ← UC-11: Historie bleibt bei der Pflanze
Sensor  1 ── * Messwert (seq, t, Rohwert, Temperatur, Batterie, RSSI, Flags)
Sensor  1 ── 2 Kalibrierung (erde, granulat)                ← REQ-MES-09
```

- **Messwerte gehören dem Sensor**, die Pflanzenansicht ist die Vereinigung der Zuordnungsintervalle. So bleibt die
  Historie beim Umstecken korrekt; `move_history=true` verschiebt auf Wunsch die Intervalle mit (UC-11).
- **Feuchteindex wird beim Lesen berechnet** (aus Rohwert, Temperatur, aktueller Kalibrierung). Eine neue
  Kalibrierung wirkt dadurch auch rückwirkend; gespeichert werden nur Rohwerte (Platz, Nachvollziehbarkeit).
- Sensor-ID `fluidi-XXXX` (REQ-SYS-08). Gateway-ID `fluidi-gw-XXXX` (REQ-SYS-11, für spätere Mehr-Gateway-Fälle).

### 2.1 Flags eines Messwerts (Bitfeld, auch im CSV)

| Bit | Bedeutung |
|---|---|
| 0 | manuell ausgelöst (PWA oder Taste) |
| 1 | Zeitstempel rekonstruiert (Sensor hatte nur relative Zeit, z. B. nach Batteriewechsel ohne Gateway, REQ-SYS-07) |
| 2 | Zeit unsicher (Gateway hatte bei Empfang keine gültige Zeit, REQ-GW-09) |
| 3 | nachgeliefert aus dem Sensorpuffer (UC-10) |
| 4 | Plausibilitätswarnung des Sensors (Ausreisser, Messfehler) |
| 5–7 | reserviert |

### 2.2 Zustände (`moisture_state`)

| Wert | Bedingung (Kap. 7) | PWA | Tropfen/LED (D-010) |
|---|---|---|---|
| `ok` | Index ≥ Schwelle | „Feucht genug“ | grün |
| `dry` | Index < Schwelle | „Giessen nötig“ | blau |
| `air` | Index < −10 %-Punkte | „Sensor nicht in der Erde?“ (REQ-MES-12, UC-15) | rot |
| `flooded` | Index > 110 % | „Zu nass / überflutet?“ | rot |
| `uncalibrated` | keine Kalibrierung vorhanden | – | aus |
| `invalid` | Kalibrierspanne < 2 % | „Kalibrierung ungültig“ | rot |

`status.stale` = kein Wert seit mehr als 3 Messintervallen (mind. 2 h); Tropfen grau.

## 3 Sicherheit

### 3.1 Transport
Nur HTTPS (Zertifikat für `fluidi.local`, Einmal-CA mit Namensbeschränkung, CONCEPTS 5.2). Port 80 liefert nur
eine Weiterleitung auf HTTPS sowie `/ca.crt` und eine Seite mit dem SHA-256-Fingerabdruck (Ersteinrichtung).

### 3.2 Anmeldung (REQ-SAF-NET-01)
- **Kein Standardpasswort.** Im Werkszustand ist `setup_required=true`. `POST /auth/setup` braucht den
  **Einrichtungscode** (6 Ziffern), den das Gateway nur über **USB** ausgibt (Provisionierung bzw. Passwort-Reset
  UC-16, ARCHITECTURE Kap. 9). Damit kann niemand im LAN das Gateway vor dem Besitzer „übernehmen“.
- Passwort ≥ 10 Zeichen, gespeichert als PBKDF2-HMAC-SHA256 mit Salt (Iterationszahl plattformabhängig,
  ≥ 100 000 als Ziel; Rechenzeit auf dem ESP32 **PROTOTYP-PRÜFUNG**).
- Sitzung: Cookie `fluidi_sid` (128 Bit Zufall, `HttpOnly; Secure; SameSite=Strict; Path=/`), 12 h bzw. 30 Tage
  mit „angemeldet bleiben“. Höchstens 8 Sitzungen, älteste fällt weg.
- **CSRF:** jede schreibende Anfrage braucht `X-CSRF-Token` (aus Login-Antwort bzw. `GET /auth/status`);
  zusätzlich wird ein vorhandener `Origin`-Header mit dem Host verglichen. JSON-Bodies nur mit
  `Content-Type: application/json`.
- **Sperre:** pro Client-IP nach 5 Fehlversuchen 60 s, danach verdoppelt bis max. 15 min; zusätzlich global
  max. 20 Fehlversuche/min (Schutz gegen IP-Wechsel). Antwort `429` + `Retry-After`. Während der Sperre wird
  auch das richtige Passwort abgewiesen. Rechnung: 20 Versuche/min ≈ 10.5 Mio./Jahr; bei 10 Zeichen aus
  ≥ 36 Zeichen ist Online-Raten aussichtslos. Eine absichtliche Aussperrung des Besitzers durch Dritte im LAN
  ist möglich (Rest-Risiko, Abhilfe: USB-Reset, Ereignisprotokoll zeigt die Quelle).

### 3.3 Erhöhte Bestätigung („elevate“)
Heikle Aktionen (`x-fluidi-elevated: true` in der OpenAPI) verlangen zusätzlich eine Passworteingabe innerhalb der
letzten 5 min (`POST /auth/elevate`): Passwort ändern, WLAN wechseln, Firmware hochladen/verteilen, Gateway-Update,
Backup erstellen, Backup einspielen. Antwort sonst `403 elevation_required`; die PWA fragt dann das Passwort ab und
wiederholt die Anfrage.

### 3.4 Lesen ohne Anmeldung
`settings.public_read` (Gateway-Werk **aus** seit Welle 2: F-8, Kollegen nutzen das öffentliche Dashboard D-020; Mock: ein): Übersicht, Verlauf, CSV, Systemstatus
sind im LAN ohne Anmeldung lesbar (REQ-SAF-NET-01 fordert Schutz nur für schreibende Aktionen; die Daten sind
nicht vertraulich). Nie öffentlich: Kopplung, Firmware, Ereignisprotokoll, WLAN-Daten, Kalibrierläufe, Backups.
Ist `public_read=false`, verlangen alle Endpunkte ausser `/auth/*` eine Sitzung.

### 3.5 Antwort-Header
`Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:;
connect-src 'self'; manifest-src 'self'; worker-src 'self'; object-src 'none'; frame-ancestors 'none';
base-uri 'none'; form-action 'self'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`,
API mit `Cache-Control: no-store`. **Kein HSTS** (bei abgelaufenem Zertifikat sperrte HSTS sonst jede
Ausweichmöglichkeit). Die PWA verwendet deshalb keine Inline-Skripte und keine `style`-Attribute.

## 4 Endpunkte (Übersicht)

Legende Zugriff: **L** = lesen (öffentlich, wenn `public_read`), **S** = Sitzung, **W** = Sitzung + CSRF,
**E** = W + elevate. Schemas: `app/api/openapi.yaml`.

| Methode | Pfad | Zugriff | Zweck | Anforderung |
|---|---|---|---|---|
| GET | `/auth/status` | – | Einrichtung nötig?, angemeldet?, CSRF, Sperre | SAF-NET-01 |
| POST | `/auth/setup` | – | erstes Passwort mit Einrichtungscode | SAF-NET-01 |
| POST | `/auth/login` · `/auth/logout` | – · S | Sitzung | SAF-NET-01 |
| POST | `/auth/elevate` | W | Passwort bestätigen (5 min) | |
| POST | `/auth/password` | E | Passwort ändern, andere Sitzungen beenden | |
| GET/POST | `/plants` | L / W | Übersicht / Pflanze anlegen | APP-03, APP-05 |
| GET/PATCH/DELETE | `/plants/{id}` | L / W / W | lesen, Name/Substrat/Schwelle/Giessen-LED, löschen | APP-05, UI-07 |
| PUT | `/plants/{id}/sensor` | W | Sensor zuordnen/wechseln/lösen, `move_history` | UC-11 |
| GET | `/plants/{id}/series` | L | Zeitreihe `from`,`to`,`res=auto|raw|hour|day` | APP-04 |
| POST | `/plants/{id}/measure` | W | „Jetzt messen“ → Job | APP-06, SYS-05 |
| GET | `/sensors`, `/sensors/{sid}` | L | Batterie, Signal, Firmware, Puffer, Fehler | APP-03, FW-08, ENE-05 |
| PATCH | `/sensors/{sid}` | W | Intervall-Übersteuerung, LED | SYS-04 |
| DELETE | `/sensors/{sid}` | W | entkoppeln → Job | GW-03 |
| POST | `/sensors/{sid}/identify` | W | LED blinken (Sensor finden) | |
| GET | `/sensors/{sid}/calibration` | L | Kalibrierung je Substrat | MES-09 |
| PUT/DELETE | `/sensors/{sid}/calibration/{substrate}` | W | Fachmodus / zurück auf Startkalibrierung | |
| POST | `/sensors/{sid}/calibration-runs` | W | geführte Kalibrierung starten | APP-07 |
| GET/DELETE | `/calibration-runs/{id}` | S / W | Stand / abbrechen | |
| POST | `/calibration-runs/{id}/capture` | W | Punkt `dry`/`wet` messen → Job | |
| POST | `/calibration-runs/{id}/commit` | W | übernehmen | |
| GET | `/jobs/{id}` | L | Auftragsstatus | |
| GET | `/pairing` | S | Kopplungsmodus, Kandidaten | RF-05 |
| POST | `/pairing/start` · `/pairing/stop` | W | Fenster öffnen (≤ 300 s) / schliessen | RF-05 |
| POST | `/pairing/candidates/{dev}/accept` | W | bestätigen + Pflanze → Job | RF-05, UC-02 |
| GET/PATCH | `/settings` | L / W | Intervall, Reaktionszeit, Schwelle, LED-Fenster, Zeit, MQTT, `public_read` | SYS-04/05, UI-07 |
| GET/PUT | `/settings/network` | S / E | WLAN anzeigen / wechseln mit Rückfall | GW-10, UC-13 |
| GET | `/firmware` | S | Gateway-Stand, Sensor-Abbilder, Verteilung | FW-08 |
| POST | `/firmware/sensor-images` | E | signiertes Abbild hochladen (octet-stream) | FW-04 |
| DELETE | `/firmware/sensor-images/{ver}` | W | entfernen | |
| POST/DELETE | `/firmware/rollout` | E / W | Verteilung starten / abbrechen | UC-08, FW-02 |
| POST | `/firmware/gateway` | E | Gateway+PWA-Update, A/B mit Rückfall | GW-11 |
| GET | `/export.csv` | L | CSV `fluidi-csv v1` | APP-08, SYS-09 |
| POST | `/backup` | E | verschlüsseltes Vollbackup | GW-06 |
| POST | `/backup/restore` | E | einspielen (`dry_run` zuerst) | GW-06, UC-14 |
| GET | `/system` | L | Zeit, Speicher, WLAN, Zertifikat, Sensoren online | GW-09 |
| POST | `/system/time` | W | Browserzeit, nur wenn Gateway keine gültige Zeit hat | GW-09 |
| POST | `/system/reboot` | W | Neustart | |
| GET | `/system/events` | S | Ereignisprotokoll | FW-07, UC-12 |
| GET | `/stream` | L | Server-Sent Events | |

## 5 Abläufe

### 5.1 Manuelle Messung (UC-04, REQ-SYS-05)
Protokoll v2 (Ä-8): Der Sensor bestätigt MEASURE mit `{status, seq}`, misst erst **nach dem Trennen** und meldet
den Wert mit dem nächsten Funkkontakt (schnelles Advertising). Job: `waiting_for_sensor` → `running` („Sensor
misst“) → `done`, sobald der Datensatz `seq` gespeichert ist. Kalibrierpunkte: `samples` Messungen = `samples` Kontakte.

1. `POST /plants/{id}/measure` → `202 Job{state: queued}`. Läuft für den Sensor schon eine Messung, kommt derselbe
   Job zurück (keine Doppelaufträge).
2. Gateway setzt einen **ausstehenden Befehl** für den Sensor. `waiting_for_sensor`: der Sensor meldet sich
   spätestens nach der eingestellten Reaktionszeit (Advertising/Abfrage, ABGLEICH PROTOCOL).
3. `running` → Sensor misst → `done` mit `result.reading` und SSE `measurement` + `plant`.
4. Frist (`deadline`) = Reaktionszeit + 30 s Reserve; danach `timeout` (PWA: „Sensor hat nicht geantwortet“).

### 5.2 Geführte Kalibrierung (UC-05, REQ-APP-07)
`calibration-runs` → `await_dry` → `capture{dry}` (Job; Sensor misst `samples` Einzelwerte, Gateway bildet den
robusten Mittelwert mit Ausreisserverwurf, Kap. 7.3) → `await_wet` → `capture{wet}` → `ready` (oder `failed`,
wenn die Spanne < 2 %) → `commit` speichert `source=guided`. Ein neuer Lauf bricht offene Läufe desselben Sensors
ab; Läufe verfallen nach 6 h. Punkte können wiederholt werden.

### 5.3 Koppeln (UC-02, REQ-RF-05)
1. PWA `POST /pairing/start` (Gateway sucht ≤ 300 s), Nutzer drückt die Sensortaste ≥ 3 s (LED gelb).
2. Kandidaten erscheinen in `GET /pairing` bzw. SSE `pairing` mit Kennung, RSSI, Firmware.
3. `accept` mit neuer oder bestehender Pflanze → Job `pair` (Schlüsselaustausch, ABGLEICH PROTOCOL) → `done` mit
   `sensor_id`, `plant_id`. Ausserhalb des Fensters gibt es keine Kandidaten (404).
4. Neue Sensoren starten mit der **Startkalibrierung** (`calibration: default`, REQ-MES-07).

### 5.3a Farbfolge bestätigen (SAS, PROTOCOL 4.2) – neu
Nach `accept` geht der Job `pair` in `awaiting_confirmation`; `result.sas` = fünf Farben (`rot|grün|gelb`), dieselben
wie an der Sensor-LED. Der Nutzer drückt kurz die Sensortaste **und** ruft
`POST /pairing/candidates/{device}/confirm {match: true}` auf (W). `match: false` bricht ab. Frist 60 s nach Anzeige.
Das Gateway speichert den Schlüssel erst nach beiden Bestätigungen und gültigem `PAIR_CONFIRM_S`.

### 5.4 Firmware-Verteilung (UC-08, REQ-FW-02/04)
1. Upload `POST /firmware/sensor-images` (E): Gateway prüft **Signatur mit dem öffentlichen Projektschlüssel**,
   Abbildformat, Hardware-Kompatibilität und Sicherheitszähler (Anti-Rollback). Fehler → `422 signature_invalid`
   bzw. `409 downgrade`. Der private Signierschlüssel ist nie auf dem Gateway.
2. `POST /firmware/rollout` (E) mit Sensorliste. Je Sensor: `pending → transferring → verifying → rebooting → done`;
   `failed` (z. B. Batterie unter Schwelle, Sensor lehnt ab), `waiting_for_sensor` (später erneut).
   Der Sensor prüft die Signatur selbst nochmals (Bootloader). Fortschritt per SSE `rollout`.
3. Gleichzeitig höchstens **ein** Sensor in Übertragung (Funkzeit, Koexistenz).

### 5.5 WLAN-Wechsel (UC-13, REQ-GW-10)
`PUT /settings/network` (E) → Gateway verbindet neu; ohne Erfolg innert 120 s Rückfall auf die alten Daten.
Erreichbarkeit bleibt über `fluidi.local`; Sensoren sind nicht betroffen.

### 5.6 Backup und Wiederherstellung (UC-14, REQ-GW-06)
- `POST /backup {passphrase}` (E) → Datei `.fbk`: Kopf (Magic, Format-Version, Gateway-ID, Datum) + Inhalt
  (Datenbank/Messwerte, Einstellungen, Kopplungsschlüssel), **verschlüsselt** mit einem aus der Passphrase
  abgeleiteten Schlüssel (PBKDF2-HMAC-SHA256 → AES-256-GCM; Format-Details ARCHITECTURE Kap. 8). Der Mock
  liefert ein **unverschlüsseltes** Testformat.
- `POST /backup/restore?dry_run=true` mit Header `X-Backup-Passphrase` prüft und zeigt die Zusammenfassung;
  ohne `dry_run` wird eingespielt und neu gestartet. TLS-Schlüssel/Zertifikat und WLAN-Daten des Zielgeräts
  bleiben erhalten (das neue Gateway hat eigene).

### 5.7 Zeit (REQ-GW-09)
`GET /system` liefert `time.valid` und `time.source` (`ntp|browser|none`; das Gateway hat keine RTC, D-028). Hat das Gateway keine gültige Zeit,
sendet die angemeldete PWA die Browserzeit (`POST /system/time`, `t` ISO 8601 oder `epoch_ms`; die PWA bietet sie nach
Anmeldung und beim Start automatisch an); mit gültiger Zeit wird sie nur mit
`force=true` + elevate übernommen. Zeiten vor 2026-01-01 oder ab 2100 → 400. Die Browserzeit wird an die monotone
Uhr gebunden (Sprünge der Systemuhr wirken nicht) und gilt bis NTP synchronisiert oder bis zum Neustart. Ohne gültige Zeit verteilt das Gateway keine Zeit an Sensoren; empfangene
Werte bekommen Flag 2. Raumklimawerte ohne gültige Zeit bleiben im RAM und werden erst nach dem Zeitabgleich mit
umgerechneter Zeit gespeichert (Neustart vorher verwirft sie).

### 5.8 Raumklima (D-017) – neu
`GET /climate?from&to` (L): `latest {t, temp_c, rh_pct}`, Verlauf (bis 3 Tage Rohwerte im 5-min-Raster, darüber
Stundenmittel), `source` = `sht4x|sim|off`. Auch im Dashboard (`climate`).

### 5.9 Profile, Pflege, Salz – neu
`Species` enthält die Artenprofile aus `app/data/species.json` (Regime A–D, Abtrocknungsgrad mit Quellen,
Winterfaktor; D-021). `Plant.care` liefert die wirksame Schwelle (Winterfaktor), Trockenphase (Regime A) und Hinweise;
„zu nass“ (`care.too_wet`, Alert `too_wet`) erst **48 h nach der letzten Giessung** (D-021). `Plant.salt` =
Dünger-/Salzhinweis aus der Zeitreihe (D-018). `PlantCreate/PlantPatch` akzeptieren `regime`, `winter_factor`,
`winter`. Journal-Typ `fertilizing` = Taste „Gedüngt“.

## 6 Server-Sent Events (`GET /stream`)

`text/event-stream`, `retry: 5000`, Kommentar-Ping alle 15 s. Ereignisse (`data` = JSON):

| `event` | Daten | wann |
|---|---|---|
| `measurement` | `{plant_id, sensor_id, reading}` | neuer Messwert (auch nachgeliefert, dann nur der neueste je Sensor) |
| `plant` | `Plant` | Änderung an Pflanze, Status oder letztem Wert |
| `plant_deleted` | `{id}` | Pflanze gelöscht |
| `job` | `Job` | jeder Zustandswechsel eines Jobs |
| `calibration` | `CalibrationRun` | Kalibrierlauf geändert |
| `pairing` | `PairingState` | Kandidaten geändert |
| `rollout` | `Rollout` | Fortschritt Verteilung |
| `system` | `SystemStatus` (Auszug) | Zeitquelle, WLAN, Speicherwarnung |

Höchstens 4 gleichzeitige Streams (ESP32-RAM, ANNAHME); weitere Clients bekommen `503` und pollen. iOS schliesst
SSE im Hintergrund → die PWA verbindet bei `visibilitychange` neu und pollt Jobs zusätzlich alle 4 s.

## 7 Rechenvorschriften (Referenz `app/js/calc.js` = `app/dev/fluidi_calc.py`)

Alle Implementierungen (PWA, Mock, Gateway) prüfen gegen `app/tests/vectors/calc_vectors.json`.

### 7.1 Feuchteindex
```
raw_comp = raw / (1 + k · (T − T_ref))        k = temp_coeff_per_k (Werk 0), T_ref = 20 °C
index    = (raw_comp − raw_dry) / (raw_wet − raw_dry) · 100      (unbegrenzt, Richtung beliebig)
pct      = runden_0.1( begrenzt(index, 0, 100) )                 nur bei ok/dry, sonst null
```
- **Temperaturkompensation = Platzhalter** (REQ-TMP-02, REQ-MES-05): Modell relativ-linear; `k` wird aus dem
  Prototyp-Versuch (8/22/35 °C) bestimmt (**PROTOTYP-PRÜFUNG**). Fehlt T oder ist der Faktor ausserhalb 0.5…1.5,
  wird nicht kompensiert. Die Kalibrierpunkte werden mit ihrer eigenen Temperatur auf `T_ref` normiert.
- Gültige Kalibrierung: `|raw_wet − raw_dry| / max(|raw_dry|, |raw_wet|) ≥ 2 %`.
- Runden: halb weg von null (nicht Bankers-Rounding), damit Python, JS und C gleich runden.
- Auflösung 0.1 % ≤ 1 % (REQ-MES-03), Test `calc.test.js`.

### 7.2 Plausibilität und Zustand
`air` bei index < −10, `flooded` bei index > 110, `dry` bei index < Schwelle, sonst `ok` (REQ-MES-12).

### 7.3 Mehrfachmessung (REQ-MES-10)
Median und MAD; verworfen wird, wer mehr als 3.5 · 1.4826 · MAD vom Median abweicht (robuster z-Wert);
Mittelwert und Stichproben-Standardabweichung der übrigen. Ob der Sensor oder das Gateway mittelt:
ABGLEICH PROTOCOL (Kalibrierung: Gateway mittelt die gelieferten Einzelwerte).

### 7.4 Aggregation und Auflösung
- `res=auto`: feinste Stufe mit ≤ 800 Punkten bei (Intervall + 2) Werten/Tag: raw → hour → day.
  Standardprofil: Tag/Woche/Monat = Einzelwerte, Jahr = Tagesmittel.
- `hour`/`day`: Eimer nach **Ortszeit** (Tage mit Zeitumstellung haben 23/25 h), Mittel, Min, Max des Index;
  Werte `air/flooded/invalid` zählen nicht. Eimer ohne gültigen Wert → `null`.

### 7.5 Signal und Batterie
Signalqualität 0–4 aus RSSI am Gateway: ≥ −70 / −80 / −88 / −95 dBm (ANNAHME, am Prototyp justieren, REQ-RF-03).
Batterie: `mv` unter Last vom Sensor, `pct` und `days_left` schätzt das Gateway aus Spannung und Ereigniszählung
(REQ-ENE-05, Modell ABGLEICH PROTOCOL/Energie); `low` bei < 30 Tagen, `critical` bei < 7 Tagen.

## 8 Fehlercodes

| HTTP | `code` | Bedeutung |
|---|---|---|
| 400 | `bad_request`, `validation`, `calibration_span` | Eingabe ungültig (`field` nennt das Feld) |
| 401 | `auth_required`, `auth_failed` | nicht angemeldet / Passwort oder Code falsch |
| 403 | `csrf`, `forbidden`, `elevation_required` | Token fehlt, fremder Origin, Passwort erneut nötig |
| 404 | `not_found` | unbekannte Ressource oder Kandidat nicht mehr im Kopplungsmodus |
| 405 | `bad_request` | Methode nicht erlaubt |
| 409 | `conflict`, `busy`, `setup_done`, `setup_required`, `downgrade` | Zustand passt nicht |
| 413 | `too_large` | Upload zu gross |
| 415 | `bad_request` | falscher Content-Type |
| 422 | `signature_invalid`, `calibration_span` | Datei/Kalibrierung abgelehnt |
| 429 | `locked` | Sperre, `Retry-After` |
| 503 | `busy` | zu viele Streams/Verbindungen |

## 9 CSV-Format `fluidi-csv v1` (REQ-APP-08, REQ-SYS-09)

- UTF-8 mit BOM (Excel), Zeilenende `\n`. Trenner `;` (Werk) oder `,`; Dezimalpunkt (Werk) oder -komma
  (nur mit `;`). Felder mit Trenner/Anführungszeichen werden in `"` gesetzt.
- Zeile 1: `# fluidi-csv v1; gateway=…; erzeugt=…; zeitzone=…; aufloesung=raw|hour|day`.
- `raw`: `pflanze_id;pflanze;sensor;zeit_utc;zeit_lokal;feuchte_pct;feuchte_zustand;rohwert;temperatur_c;quelle;flags`
- `hour|day`: `pflanze_id;pflanze;zeit_utc;zeit_lokal;feuchte_mittel_pct;feuchte_min_pct;feuchte_max_pct;temperatur_mittel_c`
- Leere Felder = kein Wert. Das Gateway streamt den Export (kein Zwischenpuffer im RAM).

## 10 Offene Punkte

| Nr. | Punkt | Wer |
|---|---|---|
| API-1 | ~~Abgleich mit `firmware/PROTOCOL.md`~~ erledigt: Gateway setzt PROTOCOL 0.2 / Protokoll v2 um (byte-gleich mit `firmware/tools/fluidi_proto.py`); Befunde `docs/reviews/phase4_protocol_software.md` | Firmware + Software |
| API-2 | `public_read` Werk ein? (Komfort vs. Sicherheit) | Auftraggeber |
| API-3 | Signalschwellen, Temperaturkoeffizient `k`, Startkalibrierung je Substrat | Prototyp |
| API-4 | ~~UTC-Minuten~~ geklärt: PROTOCOL 8 `led_window` in Lokalzeit + `TIME_SET.tz_min`; Gateway sendet TIME_SET bei Wechsel des Versatzes (Zeitumstellung). Wochentage: Emulation über `water_led` (Befund W-7) | Firmware |
| API-5 | Benachrichtigungen ohne Hersteller-Push (REQ-APP-10): vorerst nur PWA + LED, optional MQTT → Home Assistant | Auftraggeber (Software-Konzeptschritt) |
