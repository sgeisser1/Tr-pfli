# Phase 5 – Design-Review-Checkliste Software (Gateway, PWA, Protokoll)

Stand 2026-11-08 · Ersteller: Software-Agent · Prüfung durch einen anderen Agenten (CLAUDE.md Prüfregeln).
Status: **E** = erfüllt und belegt (Test/Code) · **T** = am Gerät zu prüfen (PROTOTYP-PRÜFUNG, siehe
`phase5_testplan_beitrag_software.md`) · **O** = offen (Befund) · **–** = nicht anwendbar.

Testlauf 2026-11-08 (WSL, `.venv/bin/python`): Gateway `python -m unittest discover -s tests` **70/70 OK**;
App `node --test tests/` **11/11**, `unittest tests.test_calc tests.test_pwa` **24/24**,
`tests.test_mock_api tests.test_analysis` **36/36 OK**.

## 1 Protokoll (firmware/PROTOCOL.md v2)

| Nr. | Prüfpunkt | Beleg | Status |
|---|---|---|---|
| P-1 | Testvektoren Kopplung/Sitzung beidseitig identisch | `test_protocol.Reference.*` | E |
| P-2 | Replay/Manipulation SECURE-Frame abgewiesen | `test_secure_channel_replay_and_tamper`, `test_wrong_key…` | E |
| P-3 | Duplikate (Quittung verloren) → keine Doppelspeicherung, trotzdem ACK | `test_session.DataPath` „Quittung verloren“ | E |
| P-4 | ACK erst nach COMMIT, nur bis zur lückenlos gespeicherten seq (6.2 Regel 2) | `model.contiguous_ack`, WAL + `synchronous=FULL` (`store.py` Z. 69–70), Test Nachlieferung | E |
| P-5 | Ring-Überlauf gemeldet (`lost_records`) | `test_ring_overflow_reported` | E |
| P-6 | Zeitsprung Sensor (Batteriewechsel ohne Gateway) | `test_reboot_without_gateway`, `TimeSync.*` | E |
| P-7 | Gateway ohne gültige Zeit: kein TIME_SET, Flag 2, Rückrechnung nach Abgleich | `test_time.py`, `phase5_gateway_zeit.md` | E (Gerät: GZ-1/GZ-2) |
| P-8 | Unbekannter Sensor ausserhalb Kopplungsfenster: kein Verbindungsaufbau | `test_session.Pairing` „Fremder Sensor“ | E |
| P-9 | Klartext-ERROR ändert keinen Zustand (2.5 Nr. 6, Ä-15) | `central.py` Z. 281–288 (nur Anzeige, Kommentar Befund W-8) | E |
| P-10 | Fristen/Sperre (4.5): Fristüberschreitung ≠ Fehlversuch, 10 → Sperre | `test_session.SensorRules.*` | E |
| P-11 | Zeit Verbinden → HELLO unter BlueZ am Pi (OP-GW-8), MTU ≥ 100 | – | T |
| P-12 | Sensor-Firmware (C) gegen dieselben Vektoren | Firmware-Host-Tests (Firmware-Agent) | ausserhalb dieser Liste |

## 2 Gateway-Dienst

| Nr. | Prüfpunkt | Beleg | Status |
|---|---|---|---|
| G-1 | Dienst ohne Root, Watchdog, Neustart nach Absturz | `install/systemd/`, GATEWAY_SETUP Kap. 4 | E (Gerät: T) |
| G-2 | Neustart nach Stromausfall ohne Datenverlust (REQ-GW-05) | WAL/FULL; Testplan TS-8 | T |
| G-3 | SD-Schonung (Journal im RAM, `noatime`, gebündelte Schreibvorgänge) | ARCHITECTURE Z. 400–410, `climate.py` 30-min-Flush | E (Schreibmenge am Gerät: T) |
| G-4 | Speicherbedarf 2 Jahre × 30 Sensoren (REQ-GW-01) | ARCHITECTURE Kap. 3 Rechnung | E (Rechnung), Füllstandsprognose in `GET /system` |
| G-5 | Zeitquellen NTP → (RTC) → Browser, gemeinsame Zeitbasis | `timesvc.py`; Befunde Z-1…Z-6 umgesetzt | E; **Z-9 Entscheid offen** |
| G-6 | Max. 3 gleichzeitige Verbindungen, Warteschlange | `central.py` `max_conn=3`, Semaphore | E (Last am Gerät: T) |
| G-7 | Test-Hygiene: gelegentlich „Cannot operate on a closed database“ aus einer Sitzungs-Task nach Testende (1 von 7 Läufen, Tests trotzdem OK) | Lauf 2026-11-08 | O (klein): Sitzungs-Tasks in `gw.stop()` vor `store.close()` abwarten |

## 3 PWA (app/)

| Nr. | Prüfpunkt | Beleg | Status |
|---|---|---|---|
| A-1 | Manifest vollständig, Icons vorhanden, Grössen stimmen | `test_pwa` | E |
| A-2 | Service Worker: Shell vollständig, API nie aus dem Cache, Version bei Shell-Änderung erhöht | `test_pwa.test_handlers_and_api_policy`, `sw.js` v2 | E |
| A-3 | Keine externen URLs zur Laufzeit, keine Inline-Skripte, kein `innerHTML` mit Daten, CSP | `test_pwa`, `server.py` CSP | E |
| A-4 | Kalibrierung und Berechnungen gegen gemeinsame Vektoren (JS = Python) | `calc.test.js`, `test_calc`, `vectors/calc_vectors.json` | E |
| A-5 | API-Schemas Mock und echtes Gateway gegen `openapi.yaml` | `test_mock_api`, `test_api.test_read_schemas`, `test_routes_match_spec` | E |
| A-6 | iOS Safari / Android Chrome / Desktop: Installation, Offline-Shell, Zertifikat | – | T (TS-3) |
| A-7 | Browserzeit automatisch angeboten (REQ-GW-09) | `api.js offerTime` | E |

## 4 Sicherheit LAN / HTTPS / OTA

| Nr. | Prüfpunkt | Beleg | Status |
|---|---|---|---|
| S-1 | HTTPS mit Einmal-CA, Name Constraint auf `fluidi.local` | `test_model.Tls.test_one_time_ca_with_name_constraint`, `pki.py` | E |
| S-2 | HTTPS hängt an mDNS (W-9); Rückfall IP | Red-Team W-9 | O (Entscheid Orchestrator) |
| S-3 | Cookie HttpOnly/Secure/SameSite=Strict, CSRF-Header, Origin-Prüfung | `server.py` Z. 4–5, 228–233, `test_write_needs_csrf_and_elevate` | E |
| S-4 | Login-Sperre (5 Fehlversuche, steigend bis 15 min, global 20/min) | `server.py` Z. 42, `test_login_lockout` | E |
| S-5 | Elevate (Passwort erneut) für Passwort, WLAN, Firmware, Rollout, Gateway-Update, Backup/Restore | `api.py` `elevated=True` | E |
| S-6 | Sensor-OTA nur signiert (ECDSA P-256), SHA-256, Anti-Rollback (SEC_CNT), ohne Schlüssel keine Annahme | `mcuboot.py`, `test_protocol.McuBoot.*`, `test_firmware_upload` | E |
| S-7 | Gateway-Update signiert (ECDSA), Pfadprüfung im tar, Rückfall wenn Dienst nicht startet | `server.gateway_update`, `helper.do_update` | E; **O (klein): keine Downgrade-Sperre** – ein älteres, signiertes Paket lässt sich einspielen. Vorschlag: Version > aktuelle verlangen (ausser `force` + elevate). `gw_update_pubkey` ist in `install/gateway.toml` nicht gesetzt → Online-Update ab Werk aus (gewollt?) |
| S-8 | Offene Ports nur 443, 80 (Weiterleitung + `ca.crt`), 5353, optional 8080 Dashboard; SSH nur während Einrichtung | `install/nftables-fluidi.conf` | E (Portscan: T, TS-11) |
| S-9 | Öffentliches Dashboard nur lesend, ohne Sensor-IDs | `test_public_dashboard_port` | E |
| S-10 | Browserzeit nur ohne gültige Zeit, plausibel, mit Schreibrecht + CSRF; `force` nur mit elevate | `api.system_time`, `test_system_time_browser` | E |
| S-11 | Root-Helfer: nur feste Aktionen, Eingaben geprüft (NTP-Server, Version, Staging-Pfad) | `helper.py` | E |
| S-12 | MQTT optional, Passwort/TLS möglich, Standard aus | `mqtt.py` | E |

## 5 Backup und Update

| Nr. | Prüfpunkt | Beleg | Status |
|---|---|---|---|
| B-1 | Backup inkl. Kopplungsschlüssel verschlüsselt (AES-256-GCM, PBKDF2-SHA256 200 000 It.) | `backup.py` Z. 4–5, 29 | E |
| B-2 | Restore mit Probelauf, TLS/WLAN des Zielgeräts bleiben | `test_backup_roundtrip`, GATEWAY_API 5.6 | E |
| B-3 | Wiederherstellung auf **frischem** Pi, Sensoren senden ohne Neukopplung weiter | – | T (TS-12) |
| B-4 | Kein automatisches Backup; Erinnerung fehlt | GATEWAY_SETUP Kap. 9 | O (klein): Erinnerung in der PWA, wenn letztes Backup > 30 d |
| B-5 | Gateway-Update über Neuinstallation (`install_gateway.sh`) erhält Daten | GATEWAY_SETUP Kap. 9 | T |

## 6 Ergebnis

Keine kritischen Befunde. Offen: Z-9 (Entscheid Zeitquelle, `phase5_gateway_zeit.md`), S-2 (W-9), S-7
Downgrade-Sperre Gateway-Update, B-4 Backup-Erinnerung, G-7 Test-Hygiene; alle Gerätepunkte (T) im Testplan.
