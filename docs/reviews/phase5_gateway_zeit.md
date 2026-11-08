# Phase 5 – Gateway-Zeit ohne RTC (Befund W-8): Entscheidungsvorlage

Stand 2026-11-08 · Verfasser: Software-Agent · Status: **Vorlage für den Auftraggeber**

## 1 Ausgangslage

| Punkt | Beleg |
|---|---|
| REQ-GW-09: Zeitquelle im LAN (Firmen-NTP, Browserzeit) oder interne Uhr; Gang ≤ ±2 min/Monat; Zeit bleibt nach Stromausfall ≥ 24 h erhalten, **sonst keine Zeitverteilung an Sensoren und Werte markiert**; öffentlicher NTP zulässig und abschaltbar | `docs/requirements/REQUIREMENTS.md` Z. 273, REQ-SYS-01 Z. 87, OP-08 Z. 345, D-Freigabe `DECISIONS.md` Z. 54 |
| Pi Zero 2 W hat keine RTC | `docs/datasheets/INDEX.csv` Zeile GW-SBC1 (Product Brief), Red-Team W-8 (`phase4_redteam_gesamt.md` Z. 185 ff.) |
| RTC-Baustein: Stand Phase 4 offen (OP-GW-3). **Parallel in Phase 5** hat die Hardware lokal abgelegt: `docs/datasheets/Maxim_DS3231_Datasheet_19-5170Rev10.pdf`, Adafruit PiRTC 4282 (Schaltplan + `hardware/gateway/check_rtc_schematic.py`: VBAT nur an der CR1220, kein Ladepfad), Adafruit-Anleitung `docs/appnotes/Adafruit_AddingRTC-RaspberryPi_Guide_2026-04-07.pdf`, Preise `docs/references/pi-shop_Gateway-Teile_Auszug_2026-11-08.txt`. Auswahl/BOM/Kosten: Hardware (W-8, `phase5_kosten_final.md`) | `INDEX.csv` GW-RTC (Stand beim Lesen noch „offen“), ARCHITECTURE Z. 331 |
| Sensor hat keine Uhrzeit, nur `boot_id` + `uptime` (32.768-kHz-Quarz, Budget 48 ppm); Gateway rechnet mit Synchronpunkten um | `firmware/PROTOCOL.md` Kap. 7 |
| Ohne RTC stellt `systemd-timesyncd` die Uhr beim Start auf die zuletzt gespeicherte Zeit (`/var/lib/systemd/timesync/clock`, Speicherung alle `SaveIntervalSec` = 60 s); sie läuft also „ungefähr monoton“, ist aber nach einem Ausfall um die Ausfalldauer zu spät | `man systemd-timesyncd`, `man timesyncd.conf` (systemd 255 in WSL). **ANNAHME:** Raspberry Pi OS verhält sich gleich (dort andere systemd-Version) → **PROTOTYP-PRÜFUNG T-Z1** |

## 2 Verhalten des Codes (geprüft)

**Datenpfad – robust:** Die Zeitstempel der Messwerte hängen nicht an der Gateway-Uhr zum Empfangszeitpunkt,
sondern an der **Sensor-Laufzeit** (`timesync.py`). Nach einem Stromausfall ohne NTP:

1. Gateway startet, `TimeService` meldet `valid=false` (`timedatectl NTPSynchronized=no`), Quelle `none`.
2. Sensoren puffern weiter (Ring, PROTOCOL 6); das Gateway holt Daten ab, speichert Synchronpunkte mit
   `valid=false`, quittiert. Werte, deren `boot_id` vor dem Ausfall einen gültigen Synchronpunkt hat, bekommen
   bereits eine korrekte extrapolierte Zeit, tragen aber Flag 2 „Zeit unsicher“ (`model.store_records`).
3. **Kein TIME_SET** an Sensoren (`model.on_session_info`: `time_set` nur bei `time.valid`) – REQ-GW-09 erfüllt.
4. Sobald eine gültige Zeit vorliegt (NTP oder Browser), entsteht beim nächsten Kontakt ein gültiger Synchronpunkt;
   `retime_uncertain` rechnet alle unsicheren Werte der letzten 90 Tage derselben `boot_id` zurück und löscht Flag 2.
   Test: `tests/test_time.py::AfterPowerLoss`, bestehend `test_protocol.TimeSync.*`.

**Gefundene Mängel (vor dieser Prüfung):**

| Nr. | Befund | Schwere | Status |
|---|---|---|---|
| Z-1 | GATEWAY_API 5.7 sagt „die angemeldete PWA sendet die Browserzeit“; die PWA tat das nur per Knopf auf der Seite System. Nach Stromausfall ohne Internet blieb die Zeit ungültig, bis jemand diese Seite öffnet | wichtig | **umgesetzt**: `app/js/api.js` `offerTime()` nach Anmeldung/Einrichtung und beim Start (angemeldet); Gateway übernimmt nur ohne gültige Zeit |
| Z-2 | Browserzeit wurde als Versatz zur Systemuhr gespeichert; ein späterer Sprung der Systemuhr (NTP kommt nach) verfälschte die Zeit bis zur nächsten Prüfung (≤ 60 s) doppelt | klein | **umgesetzt**: Anker an `time.monotonic()` (`timesvc.py`) |
| Z-3 | Zwei Zeitbasen: `model.now()`, Ereignisse, Klima, Empfangszeit (`rx`), Kopplungsfenster nutzten die Systemuhr, Messwerte die Browserzeit. Folge bei 3 Tagen Rückstand: „zuletzt gesehen vor 3 Tagen“, Kopplungsfenster in der PWA sofort abgelaufen (`pair.js` vergleicht mit `Date.now()`), Klimawerte am falschen Tag | wichtig | **umgesetzt**: `timesvc.wall()` als gemeinsame Zeit; `model.now`, `store`, `climate`, `central`, `service`, `backup` umgestellt |
| Z-4 | Keine Plausibilitätsprüfung der Browserzeit (Handy im Werkszustand 1970/2000 wäre übernommen und per TIME_SET an alle Sensoren verteilt worden) | wichtig | **umgesetzt**: nur 2026-01-01 ≤ t < 2100, sonst API 400 + Ereignis |
| Z-5 | `openapi.yaml` verlangt `epoch_ms`, Gateway las nur `t`/`now` → ein spezifikationstreuer Client wurde still ignoriert | klein | **umgesetzt**: beide Felder, 400/409 dokumentiert |
| Z-6 | Zeitsprung durch Browserzeit liess bestehende Sitzungen sofort ablaufen (Admin nach dem Zeitabgleich abgemeldet) | klein | **umgesetzt**: Sitzungsfristen werden um den Sprung verschoben (`api.system_time`, Test `test_system_time_browser`) |
| Z-7 | Klimawerte (SHT4x im Gateway) haben vor dem Zeitabgleich die Systemzeit (Rückstand = Ausfalldauer) und **keine** Markierung „unsicher“; sie werden nicht nachträglich korrigiert | klein | offen → Vorschlag V-3 |
| Z-8 | `retime_uncertain` sucht nur Werte mit `rx` ≥ jetzt − 90 d. Lag die Systemuhr beim Empfang > 90 d zurück (z. B. fehlende Clock-Datei), werden diese Werte nie korrigiert | klein | offen → Vorschlag V-4 |
| Z-9 | REQ-GW-09 „Zeit bleibt nach Stromausfall ≥ 24 h erhalten“ ist **ohne NTP und ohne geöffnete PWA nicht erfüllt** | wichtig | Entscheid nötig (Kap. 4) |
| Z-10 | Mit RTC würde der Kernel die Uhr beim Start aus der RTC stellen (`dtoverlay=i2c-rtc,ds3231`, Adafruit-Anleitung S. 11), `timedatectl NTPSynchronized` bliebe aber „no“ → `TimeService` meldete trotzdem `valid=false`, `rtc_ok` ist fest `false` (`timesvc.status`) | wichtig (nur falls RTC eingeplant) | offen → V-6 |

## 3 Optionen

| Option | Wirkung | Kosten | Bewertung |
|---|---|---|---|
| A NTP öffentlich (Werk `pool.ntp.org`) | Zeit Sekunden nach dem Start, wenn Internet; Firmen-WLAN kann UDP 123 sperren (`research_gateway.md` Z. 176) | 0 | zulässig (OP-08), bereits umgesetzt, abschaltbar |
| B NTP im LAN (Firmen-NTP, Router) | wie A ohne Internet; Server in App → Einstellungen → Zeit (`helper.py` `do_ntp`) | 0 | umgesetzt; ob das Firmennetz einen NTP-Server hat: **beim Auftraggeber erfragen** |
| C Browserzeit automatisch (Z-1) | Zeit, sobald der Admin die App öffnet; Handyuhr ist i. d. R. netzsynchron (**ANNAHME**) | 0 | jetzt umgesetzt; hängt an einer Person |
| D Zeit aus den Sensoren zurückgewinnen (neu) | Sensoren sind batteriegespeist und laufen beim Netzausfall weiter. Aus dem letzten gültigen Synchronpunkt vor dem Ausfall und der `uptime` der nächsten SESSION_INFO (AES-CCM-authentisiert, PROTOCOL 4.4) folgt die Gateway-Zeit. Fehler ≤ 48 ppm × Ausfalldauer: 24 h → ≤ 4.1 s, 30 d → ≤ 2.1 min (Budget PROTOCOL 7 Nr. 5). Mehrere Sensoren gegeneinander prüfen | 0 (Software, ≈ 80 Zeilen + Tests) | **empfohlen** als Quelle zwischen RTC und Browser; erfüllt REQ-GW-09 „≥ 24 h“ ohne Hardware, solange ≥ 1 Sensor seit dem letzten Abgleich nicht neu gestartet hat |
| E RTC-Modul DS3231 (z. B. Adafruit PiRTC 4282, CR1220, kein Ladepfad lt. Schaltplanprüfung der Hardware) | unabhängig von Netz, Personen und Sensoren; Gang ±2 ppm bei 0–40 °C (`Maxim_DS3231_Datasheet_19-5170Rev10.pdf` S. 1) ≈ ±5 s/Monat ≪ ±2 min/Monat (REQ-GW-09) | Preis/BOM: Hardware-Agent (`hardware/gateway/BOM_GATEWAY.csv`, `phase5_kosten_final.md`); hier nicht wiederholt | erfüllt REQ-GW-09 vollständig. **Software dafür noch nicht bereit** (Z-10, V-6) |

## 4 Empfehlung (Entscheidungsvorlage)

1. **Zeitquellen-Reihenfolge:** NTP (öffentlich oder LAN) → RTC (falls verbaut) → Sensor-Zeit (D) → Browserzeit (C) → keine.
   A/B/C sind umgesetzt.
2. **Variante 1 (ohne RTC, 0 CHF):** D als nächster Software-Schritt (V-1); REQ-GW-09 um „oder Zeitrückgewinnung aus
   gepufferten Sensor-Laufzeiten“ ergänzen. Grenze: versagt, wenn alle Sensoren seit dem letzten Abgleich neu gestartet haben.
3. **Variante 2 (mit RTC DS3231):** erfüllt REQ-GW-09 ohne Einschränkung; Kosten laut Hardware-BOM; Software V-6 nötig
   (klein, ≈ 30 Zeilen + Test), D trotzdem als Plausibilitätsprüfung der RTC sinnvoll.
4. **Empfehlung Software:** Variante 2, **wenn** die Hardware-Kosten (W-8) im Rahmen bleiben – die RTC ist die einzige
   Lösung ohne Abhängigkeit von Personen oder Sensorzustand und die Software-Arbeit ist klein. Sonst Variante 1.
   Für die Muster genügt Variante 1 (Zeitabgleich über NTP/App).

**Entscheid des Auftraggebers:** ☐ Variante 1 ☐ Variante 2 ☐ anders: ______ (Eintrag in `DECISIONS.md`)

## 5 Vorschläge (grössere Änderungen, nicht umgesetzt)

| Nr. | Vorschlag |
|---|---|
| V-1 | Quelle `sensor` in `timesvc.py`: nach jedem SESSION_INFO bei `valid=false` aus Sensoren mit gültigem Synchronpunkt derselben `boot_id` (Alter ≤ 30 d) die Zeit schätzen; übernehmen, wenn ≥ 2 Sensoren innerhalb 10 s übereinstimmen (bei nur einem gekoppelten Sensor: 1). Zeitstatus-Enum in `openapi.yaml` um `sensor` erweitern, PWA-Text „aus den Sensoren“. Tests: Ausfall 24 h/30 d, ein Sensor neu gestartet, widersprüchliche Sensoren |
| V-2 | Sensor-Uptime auch für Gang-Schätzung nutzen (Drift-Rate je Sensor ist schon in `timesync._rate`) |
| V-3 | Klimawerte vor dem Zeitabgleich mit Monotonzeit puffern und nach Abgleich umrechnen, sonst Flag „unsicher“ |
| V-4 | `retime_uncertain` über Sequenznummern seit dem letzten gültigen Synchronpunkt statt über `rx` eingrenzen (Z-8) |
| V-6 | RTC im Zeitdienst: `/sys/class/rtc/rtc0` vorhanden und Zeit plausibel (≥ letzte gespeicherte Zeit, DS3231-Oszillator-Stopp-Flag nicht gesetzt – Registerbeschreibung im Datenblatt prüfen) → `valid=true, source=rtc, rtc_ok=true`; nach NTP-Sync RTC nachstellen (`hwclock -w` über Root-Helfer bzw. Kernel-Sync; **ANNAHME**, am Gerät prüfen). Installationsskript: Overlay `i2c-rtc,ds3231` nur wenn RTC bestellt |
| V-5 | Systemuhr nach Browser-/Sensorzeit über den Root-Helfer stellen (`timedatectl set-time` bei abgeschaltetem NTP), damit auch die Clock-Datei von timesyncd und Fremdprozesse stimmen; nur mit Sicherheitsprüfung (Root-Aktion) |

## 6 Prüfungen am Gerät (PROTOTYP-PRÜFUNG)

| Nr. | Prüfung |
|---|---|
| T-Z1 | Pi ohne Netz 1 h und 25 h stromlos; danach `timedatectl`, `GET /system` (`time.valid=false`, `source=none`), Systemzeit ≈ letzte Speicherung |
| T-Z2 | App öffnen und anmelden → `source=browser`, Ereignis „Zeit von der PWA übernommen“, Werte der Ausfallzeit nach der nächsten Sitzung ohne Flag 2, Abweichung zu einer Referenzuhr ≤ 2 s je Sensor |
| T-Z3 | (nach V-1) wie T-Z1 ohne App: `source=sensor` nach dem ersten Sensorkontakt, Abweichung ≤ 5 s nach 25 h |
| T-Z4 | Handyuhr auf 2001 stellen → API 400, Ereignis `time_browser_rejected`, kein TIME_SET |

## 7 Geänderte Dateien und Tests

- `firmware/gateway/fluidi_gw/timesvc.py` (Anker, `wall()`, `plausible()`), `api.py` (`/system/time`: `epoch_ms`,
  Plausibilität, Sitzungsfristen), `model.py`, `store.py`, `climate.py`, `central.py`, `service.py`, `backup.py` (gemeinsame Zeit)
- `app/js/api.js` (`offerTime`), `app/js/main.js`, `app/sw.js` (Shell-Version v2), `app/api/openapi.yaml`
- `docs/interfaces/GATEWAY_API.md` 5.7, `docs/manuals/GATEWAY_SETUP.md` Kap. 9
- Neue Tests: `firmware/gateway/tests/test_time.py` (7), `test_api.GatewayApi.test_system_time_browser`.
  Gateway 70/70 OK, App node 11/11, unittest test_calc+test_pwa 24/24, test_mock_api+test_analysis 36/36 OK.
