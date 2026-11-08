# Phase 5 – Design-Review-Checkliste Sicherheit

| | |
|---|---|
| Verfasser | Sicherheits-Agent |
| Datum | 2026-11-08, Stand git `b77b29a` (main; im Arbeitsbaum laufende, nicht versionierte Änderungen anderer Fachbereiche) |
| Status | ✓ erfüllt (Nachweis genannt) · **T** nur am Muster nachweisbar (PROTOTYP-PRÜFUNG, Testplan) · **O** offen · ✗ nicht erfüllt |

## 1 Energiequelle CR2032 (REQ-SAF-CC-*, REQ-SAF-01…06)

| Nr | Prüfpunkt | Status | Nachweis / Bemerkung |
|---|---|---|---|
| C-01 | Nicht wiederaufladbare Quelle gewählt (REQ-SAF-03) | ✓ | D-006 (A-32) |
| C-02 | Verpolschutz Q1 richtig verdrahtet (G = GND, S = VDD, D = VBAT) | ✓ / T | `phase4_layout_revb_sicherheit.md` Kap. 4; `AOS_AO3401A_Datasheet_Rev3.1.pdf` S. 1; Verpoltest 24 h (ST-Z1) |
| C-03 | Q1 richtig bestückt (Rotation) | T | B-3, ST-E2 |
| C-04 | Zwei Rückstrombarrieren je externer Quelle (TP1/TP2: 2 × 100 kΩ im Band) | ✓ / T | CONCEPTS 2.7, R2-A3; ST-Z5 (R2-A4) |
| C-05 | Programmieren nur ohne Zelle, **konstruktiv** | ✗ / O | Weg B ohne Scheibe verletzt das → **VETO PS-K1**; Weg A hängt an PS-W1 (`phase5_programmer_sicherheit.md`) |
| C-06 | Ladegrenze belegt (≤ 10 mA Fehlerfall, ≤ 1 % C) | ✓ | `docs/references/Maxell_CR_Warnings_12e_2012.pdf` S. 2; Renata/Panasonic offen (OP-K7) |
| C-07 | Kein GND-Ziel neben dem Zellrand im Fach (TP3 entfällt) | ✓ | A-1, `ORDER_JLC_REV_C.md` (4 VIP im Fach) |
| C-08 | Vias im Fach nur als POFV-Via-in-Pad | ✓ / T | D-023 A-2 (Bestellung), A-3 (Querschliff) |
| C-09 | Clip-Pads ≥ 0.3 mm zu den Vergusskanten | ✓ | D-023 V-K, LS-W1 |
| C-10 | Kurzschluss im Clip bei schräger/verkehrter Zelle | T | ST-Z2, Red-Team K-6 |
| C-11 | Zelltemperatur bei 65 °C im Datenblattbereich | ✓ | `Panasonic_CR2032_Datasheet_2026-02.pdf` S. 1 (−30…85 °C; ≥ 70 °C Rücksprache) |
| C-12 | Fach getrennt abgedichtet; Flutung Fach/Elektronikraum 24 h mit Zelle | T | REQ-SAF-05, A-4; ST-W2/W3 |
| C-13 | REQ-SAF-01 Einzelfehler (Kurzschluss, Verpolung, Wasser, Kurzschluss je Bauteil im Pfad) | T | FMEA F-01…F-09; Tests ST-Z, ST-W |
| C-14 | FMEA-light vorhanden (REQ-SAF-02) | ✓ | `phase5_fmea_light.md` |

## 2 Verschluckschutz und Batteriewechsel (REQ-SAF-CC-04, REQ-SAF-DOC-01)

| Nr | Prüfpunkt | Status | Nachweis / Bemerkung |
|---|---|---|---|
| K-01 | Öffnen nur mit Werkzeug, Schraube unverlierbar | ✓ (Konstruktion) / T | M2 × 4 A2 in eingegossener Mutter (K-6), `docs/design/P3_FLUIDI.md`; Masse aus `mechanical/gen/fluidi_params.py` (ANNAHME bis Bestellung) |
| K-02 | UL-4200A-Prüfwerte (0.5 Nm/90°, 72 N, 136 N) | T | Werte aus `phase3_sleeve_sicherheit.md`; ST-K1…K3 |
| K-03 | Falltest 1 m: Fach bleibt zu, Zelle bleibt im Clip | T | ST-M3, ST-K5 |
| K-04 | Warnsymbol am Fach, beim Öffnen sichtbar | ✓ | vertieft innen auf der Hülse (P3_FLUIDI, PRINT_SETTINGS `huelse_grau`); LS-K3 (zusätzlich Silkscreen B) offen, klein |
| K-05 | Sicherheits-/Batteriewechselanleitung (Verschlucken, Lagerung, Entsorgung, Wasser im Kopf) | **✗** | fehlt (W-5, FMEA F-23 RPZ 288) |
| K-06 | Clip-Lötstellen für Wechselzyklen | T | K-4 Red-Team; ST-K6 (50 Wechsel) |

## 3 Mechanik, Dichtung, Verguss

| Nr | Prüfpunkt | Status | Nachweis / Bemerkung |
|---|---|---|---|
| M-01 | Schott und Kragen als fester Verguss (S3-K1/K2) | ✓ | `phase3_sleeve_sicherheit.md`, `phase4_sicherheit_kragen_firmware.md` Teil 1 |
| M-02 | Dichtstreifen und Feld nach K-1…K-3 | ✓ | am Board verifiziert, `phase4_layout_revb_sicherheit.md` Kap. 3 |
| M-03 | Vergussmasse mit Datenblatt (Tg ≥ 80 °C, gefüllt, Haftung ENIG/Lötstopp/ASA) | **O** | `mechanical/PRINT_SETTINGS.md` „ANNAHME Typ“ (W-5, K-4) |
| M-04 | Kantenversiegelung Sonde (REQ-MECH-07) | **O** | Verfahren nicht gewählt (W-5) |
| M-05 | Gehäusematerial HDT ≥ 80 °C | ✓ | ASA, `docs/references/BambuLab_ASA_TechnicalDataSheet_V2.0.pdf` |
| M-06 | Spritzwasser REQ-MECH-13 mit Zelle | T | ST-W1 |
| M-07 | Montage-/Vergussanleitung mit Reinigung (K-5) | **✗** | fehlt (W-5) |

## 4 Firmware und Funk (REQ-FW-04, REQ-RF-05/06)

| Nr | Prüfpunkt | Status | Nachweis / Bemerkung |
|---|---|---|---|
| F-01 | Kopplung nur mit Taster und PWA-Bestätigung, Commitment (v2) | ✓ / T | VETO F-K1 aufgehoben (`phase4_sicherheit_kragen_firmware.md` Runde 2); ST-S1/S2 |
| F-02 | Gateway auf Protokoll v2 (Auflage G-1) | ✓ (Stichprobe) | `firmware/gateway/fluidi_gw/protocol.py` PROTO_VERSION 2, `central.py` Z. 220 REVEAL nach PAIR_RSP; volle Gateway-Sicherheitsprüfung steht aus |
| F-03 | Nur signierte Images (MCUboot EC256), Anti-Rollback | ✓ / T | `phase4_sicherheit_kragen_firmware.md` 2.1, F-L1; ST-S5…S7 |
| F-04 | Gateway nimmt Images nur mit gültiger Signatur an; ohne Schlüssel gar nicht | ✓ | `fluidi_gw/mcuboot.py` Z. 97–108, `server.py` Z. 519–530 |
| F-05 | Signierschlüssel nicht auf dem Gateway (REQ-FW-04) | ✓ | Gateway kennt nur `fw_pubkey`/`gw_update_pubkey` (`fluidi_gw/config.py` Z. 45–46) |
| F-06 | Serien-CCFG sperrt Bootloader, SWD, FlashProgram; WEPRA | ✓ / T | F-W2; PP-9 (ST-S9) |
| F-07 | `--lock` verweigert DEV-Schlüssel | ✓ | F-W1, `scripts/flash_sensor.py` `check_lock_key` |
| F-08 | Reset-/Weckschleifen begrenzt | ✓ / T | F-W3; ST-F6 |
| F-09 | RNG-Fehler führt zum Abbruch | ✓ | F-W4 |

## 5 LAN, OTA und Schlüssel (REQ-SAF-NET-*)

| Nr | Prüfpunkt | Status | Nachweis / Bemerkung |
|---|---|---|---|
| N-01 | Schreibende Routen nur mit Anmeldung; OTA, Netz und Backup zusätzlich `elevated` | ✓ / T | `fluidi_gw/api.py` (Standard `auth="write"`; Ausnahmen nur `GET` mit `read`, `/auth/*`, `/dashboard` public); ST-N1 |
| N-02 | Kein Standardpasswort, Sperre nach Fehlversuchen | ✓ / T | Einrichtungscode (D-022); `server.py` Z. 42 (5 Versuche, global 20/min); ST-N2 |
| N-03 | Keine Fernwartung im Auslieferungszustand, Portliste | T | SSH nur bei der Einrichtung (D-022); Portscan ST-N3 |
| N-04 | Öffentliches Dashboard nur lesend, abschaltbar, `public_read` ab Werk aus | ✓ | D-020/D-022 |
| N-05 | CA mit Name Constraint, CA-Schlüssel nie dauerhaft gespeichert | ✓ | `fluidi_gw/pki.py` Z. 36–57 (RAM, `del ca_key`); im Sinne von S2-L04 akzeptiert |
| N-06 | **Produktionsschlüssel nie im Repo** | ✓ (Stand heute) | siehe Kap. 6 |
| N-07 | Signierte Gateway-Updates | ✓ | `server.py` Z. 519–530 (ohne Schlüssel kein Update) |

## 6 Prüfung Schlüssel im Repository (selbst ausgeführt, 2026-11-08)

| Befehl | Ergebnis |
|---|---|
| `git ls-files \| grep -iE '\.(pem\|key\|der\|p12\|pfx\|p8\|jks\|crt\|csr)$\|id_rsa\|id_ed25519\|secret\|private'` | nur `firmware/sensor/keys/DEV_ONLY_fluidi_signing_ec-p256.pem` |
| `git grep -l -E 'BEGIN( [A-Z]+)? PRIVATE KEY'` | nur dieselbe DEV-Datei |
| `git log --all --diff-filter=A --name-only` (78 Commits, alle je hinzugefügten Pfade) mit demselben Muster | nur die DEV-Datei, eingeführt in `489a984` |
| `git log --all -p -S'PRIVATE KEY'` | nur Commit `489a984`, DEV-Datei |
| `git grep -l -E 'BEGIN CERTIFICATE\|BEGIN OPENSSH\|BEGIN RSA'` | keine Treffer |
| Fest codierte Passwörter (`password=…` in `.py/.js/.json/.sh`) | nur `app/dev/mock_server.py` Z. 2185 `fluidi-demo-2026` (Entwicklungs-Mock, bindet an 127.0.0.1) |
| `git check-ignore -v` | `firmware/sensor/keys/prod.pem` → ignoriert (`firmware/sensor/.gitignore` Z. 5); **`firmware/gateway/x.key`, `app/ca.key`, `secrets.pem` (Wurzel) → nicht ignoriert** |

**Ergebnis:** Kein Produktions- oder privater Schlüssel im Repo oder in der Historie. Der DEV-Schlüssel ist
öffentlich gewollt und wird von `--lock` und `make release` abgewiesen (F-W1).

## 7 Befunde aus dieser Checkliste

| Nr | Stufe | Befund | Vorschlag |
|---|---|---|---|
| CK-K1 | **kritisch (VETO)** | = PS-K1: Weg B ohne Dummy-Scheibe erlaubt eine Zelle bei angeschlossenem Netzteil | siehe `phase5_programmer_sicherheit.md` |
| CK-W1 | wichtig | Sicherheits-, Batteriewechsel- und Montageanleitung fehlen (K-05, M-07; REQ-SAF-DOC-01, REQ-DOC-02) | vor der Nutzung der Muster ausserhalb des Labors erstellen; Prüfung durch Sicherheit |
| CK-W2 | wichtig | Vergussmasse und Kantenversiegelung offen (M-03, M-04) | Auswahl mit Datenblatt, dann Sicherheitsprüfung K-4/K-5 |
| CK-W3 | wichtig | Gateway-Netzteil nicht in einer Einkaufsliste festgelegt (FMEA F-44; REQ-SAF-DOC-02). RTC: Kandidat Adafruit 4282 ohne Ladepfad (von Sicherheit geprüft, FMEA F-45), Typ noch festzuschreiben | Gateway-Stückliste mit geprüftem Netzteil und RTC-Typ; ST-G1 |
| CK-L1 | klein | Nur `firmware/sensor/.gitignore` sperrt `*.pem`. Schlüssel für Gateway-Updates oder eine Rückfall-CA ausserhalb von `firmware/sensor/` würden nicht ignoriert | Wurzel-`.gitignore`: `*.pem`, `*.key`, `*.p8`, `*.p12`, `*.pfx` mit Ausnahme `!firmware/sensor/keys/DEV_ONLY_*.pem`; optional pre-commit-Hook mit `git grep 'PRIVATE KEY'` |
| CK-L2 | klein | Silkscreen-Warnung auf B im Fach (LS-K3) nicht umgesetzt bzw. nicht entschieden | für Rev D vormerken oder Entscheid dokumentieren |
