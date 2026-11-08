# Phase 5 – Design-Review-Checkliste Firmware/Energie (Sensor Rev C)

| | |
|---|---|
| Datum | 2026-11-08 |
| Verfasser | Firmware/Energie |
| Stand | git `b77b29a` plus Arbeitskopie (energy_budget.py Kap. 3d/3e, ENERGIEMESSUNG E14/E15) |
| Status | **ok** = belegt (Build, Test, Rechnung oder Dokument). **offen** = Arbeit/Entscheid fehlt. **PROTOTYP-PRÜFUNG** = erst am Muster nachweisbar |

## A Build, Speicher, Tests (neu gelaufen am 2026-11-08)

| Nr. | Punkt | Anforderung | Nachweis | Status |
|---|---|---|---|---|
| A1 | Sauberer Neubau ohne IDE | Reproduzierbarer Build (Auftrag) | `source ~/fluidi-tools/env.sh; make clean && make` → RC 0, 0 Fehler. Es bleiben 4 Linker-Hinweise #10325 (NVS-BOUND-Sektionen, im README erklärt). Protokoll `firmware/sensor/build/build.log` | ok |
| A2 | Flash-Aufteilung inkl. OTA | REQ-FW-03 (2 Abbilder + Puffer) | `build/size_report.txt`: MCUboot 17 164 B (76 %), Slot 0 Code 206 948 B (90 %, frei 22 172 B), signiertes Image 207 380 B in Slot 1 (90 %, frei 24 044 B), Swap-using-Move (Slot 0 = Slot 1 + 1 Sektor); alle 6 Prüfungen [ok] | ok (Reserve ≈ 22 kB, Befund K-2) |
| A3 | RAM | – | 33 666 B von 36 864 B (91 %), 3 198 B frei, Prüfung RAM-Reserve ≥ 2 kB erfüllt | ok (knapp, K-2) |
| A4 | Host-Tests Kern | REQ-SYS-09, REQ-RF-05/06, REQ-LOG | `make check`: Layout ok, Pins ok, **1542 Prüfungen bestanden, 0 fehlgeschlagen** (ASan/UBSan) | ok |
| A5 | Flash-Werkzeug | REQ-FW-06 | `~/fluidi-tools/venv/bin/python -m unittest discover -s scripts -p test_flash_sensor.py -v`: **17 Tests OK**, darunter CCFG-CRC gegen SDK-crc_tool, Sperre nur mit passendem Schlüssel-Fingerabdruck und Werks-Hex in der Simulation | ok |
| A6 | Kopplungsangriff MITM v2 | REQ-RF-05 | `tools/test_pairing_mitm.py` 3 Tests OK (in `make check`) | ok |
| A7 | Signatur und Sicherheitszähler | REQ-FW-04 | Signiertes Image + Werks-Hex (Schlüssel-Fingerabdruck 86e66310969bdc7d = **DEV-Schlüssel**). `make release` verweigert den DEV-Schlüssel (README Kap. 1). Test `test_factory_with_dev_key_cannot_be_locked` OK | ok (Muster), Serie: Produktionsschlüssel offen |
| A8 | Prüfsummen dieses Builds | Reproduzierbarkeit | sha256 `fluidi-sensor-0.1.0+1.bin` 76c88e3c…578d, Werks-Hex 7a3e74ed…e524. Die ECDSA-Signatur ist randomisiert, das unsignierte Bild ist laut README bitgleich | ok |

## B Pinbelegung, Bootpins, Pegel

| Nr. | Punkt | Anforderung | Nachweis | Status |
|---|---|---|---|---|
| B1 | Firmware ↔ Netzliste, Pin für Pin | PINMAP Rev B | Netzliste `fluidi_sensor.net` (2026-11-08) U1 eigens ausgelesen und mit `config/fluidi_board.h` verglichen: DIO8/P3 CREF1_CTL, DIO11/P4 OSC_EN_N, DIO12/P5 SENS_PWR, DIO13/P6 LED_G, DIO16/P7 SDA, DIO17/P8 SCL, DIO20/P9 LED_B_UART_RX, DIO21/P10 BTN_BOOT_N, DIO24/P12 MEAS_CLK, DIO3/4 P14/15 X32, DIO6/P19 LED_R_UART_TX. Alle **identisch** | ok |
| B2 | Netzliste ↔ Datenblatt-Pinout | – | `TI_CC2340R5_Datasheet_SWRS272F.pdf` S. 7 Fig. 6-2 (RGE): Pins 1–24 stimmen mit der Netzliste überein, auch VDDS 11/18/24, VDDR 2/20, DCDC 17, VDDD 16, RSTN 13; DIO12 ist High-Drive (S. 7) und dient als SENS_PWR | ok |
| B3 | Wake-fähiger Taster | REQ-FW-01, FW-5 | DS S. 47: alle DIOs sind interrupt- und wakeup-fähig. S. 49: „Wake-up on pin edge“ aus Standby und Shutdown | ok |
| B4 | SWD-Pulls DIO16/17 früh aus | FW-6 (Ruhestrom) | `platform/cc23/fl_hw.c` Z. 442 (Ausgang low), Aufruf früh in `fl_ble.c` Z. 252 | ok (Wirkung: E1 PROTOTYP-PRÜFUNG) |
| B5 | Bootloader-Trigger DIO21 (Muster) | FW-10, REQ-FW-06 | `mcuboot/mcuboot.syscfg` Z. 35–39 (bldrEnabled, DIO21 LOW). Serie: `--lock` (pBldrVtor FORBID) | ok; Strom im Bootloader **W-10: PROTOTYP-PRÜFUNG E15** |
| B6 | Ruhepegel FW-8 | REQ-ENE-09 | `fl_hw.c` Z. 59: DIO11 high, DIO12 low, DIO16/17 low, Puffer aus, LED high. Budget Kap. 1: R13/R1/D1/SW1 stromlos | ok (Rechnung), E1 PROTOTYP-PRÜFUNG |
| B7 | UART-Pads TP1/TP2 im Zellfach | REQ-SAF-06 | R9–R12 100 kΩ als Barriere. Rev C: TP3 entfällt (D-023 A-1), GND über das Minuspad | ok |

## C Energie

| Nr. | Punkt | Anforderung | Nachweis | Status |
|---|---|---|---|---|
| C1 | Laufzeit pess. (Typ × 1.5) | REQ-ENE-02 | `phase5_energiebudget_final.md`: pessA 34.6 Mt. (4 × 100 µF) | ok |
| C2 | Laufzeit pess. mit DS-Grenzwerten | REQ-ENE-02/-08 | pessDS 9.1 Mt. (4 ×) bzw. 13.3 Mt. (2 ×) | **offen → W-6, Entscheid nach E14** (Regel in Kap. 5 des Finalberichts) |
| C3 | Reaktionszeit 1/2/5 min ausgewiesen | REQ-ENE-04 | `ENERGIE_REV_B.md` Kap. 3d (neu) | ok |
| C4 | Spannungseinbruch ≤ 0.2 V bei 100 Ω | REQ-ENE-06 | SPICE `supply_report.txt`: 143 mV (4 ×); FW-2 Burst und FW-4 LED-Pulse im Code | ok (Rechnung), E3/E5/E6 PROTOTYP-PRÜFUNG |
| C5 | Abschaltung bei Unterspannung | REQ-ENE-06 (2.0 V) | `UV_MV 2400` (`core/fl_app.c` Z. 34), Wiederanlauf 2600 mV | ok (konservativ); E11 PROTOTYP-PRÜFUNG |
| C6 | Mittel- und Ruhestrom | REQ-ENE-09 | gerechnet pessA 5.51 µA / Schlaf 2.84 µA | PROTOTYP-PRÜFUNG E1/E12 |
| C7 | Batteriestand und 30-Tage-Warnung | REQ-ENE-05 | `charge_uc` + `vbat_load`; Rückfall 2.55 V (ANNAHME) | PROTOTYP-PRÜFUNG (FW-P6, Entladekennlinie) |
| C8 | Messpunkt ohne Umgehung einer Schutzfunktion | REQ-ENE-07 | ENERGIEMESSUNG „Sicherheit“: Mess-Zwischenadapter im Zellhalter, keine Quelle in Serie zur Zelle | ok |
| C9 | LED-Anteil ≤ 5 %, ≤ 1×/min | REQ-UI-03 | pessA 3.2 %; Vorrangregel in PROTOCOL 10.2 | ok |
| C10 | OTA ≤ 2 % Kapazität | REQ-FW-05 | 0.06 mAh ≈ 0.03 % | ok (Rechnung), E9 PROTOTYP-PRÜFUNG |
| C11 | Selbstentladung nach Herstellerangabe | REQ-ENE-08 | Renata < 1 %/a; Panasonic ohne Wert → ANNAHME | offen (klein, E-2) |

## D Funk, Protokoll, Bedienung

| Nr. | Punkt | Anforderung | Nachweis | Status |
|---|---|---|---|---|
| D1 | Gerätename `fluidi-XXXX` | REQ-SYS-08 | `core/fl_proto.c` Z. 36, Host-Test | ok |
| D2 | Datenformat versioniert | REQ-SYS-09 | PROTOCOL 0.2, `FL_PROTO_VERSION 2` = Gateway `PROTO_VERSION 2` (Red Team Kap. 2) | ok |
| D3 | Kopplung nur nach Tastendruck + PWA, Schlüssel je Sensor | REQ-RF-05 | Protokoll v2 Commitment/SAS. VETO F-K1 aufgehoben (`phase4_sicherheit_kragen_firmware.md`), MITM-Test A6 | ok; ECDH-Rechenzeit PP-6 PROTOTYP-PRÜFUNG |
| D4 | Befehle nur vom gekoppelten Gateway, Replay-Schutz | REQ-RF-06 | AES-CCM SECURE-Frames, Host-Tests | ok |
| D5 | Zwei-Wege: Messung, Kalibrierung, Einstellungen, Zeit, OTA | REQ-SYS-06 | PROTOCOL Kap. 5.4/8/9, Gateway byte-gleich (`phase4_protocol_software.md`) | ok |
| D6 | Reaktionszeit 1 min (95 %) | REQ-SYS-05 | adv 27.5 s mit P_MISS 10 % (ANNAHME) | PROTOTYP-PRÜFUNG (FW-P8, Koexistenz W-7) |
| D7 | Zeitstempel ±2 min/14 d, ±5 min/60 d | REQ-SYS-07 | Quarzbudget 48 ppm → 1.0 / 4.2 min (PROTOCOL 7) | PROTOTYP-PRÜFUNG |
| D8 | Pufferung ohne Gateway | REQ-LOG | Ringspeicher 24 kB (0x79800, 0x6000), ≥ 105 Tage (README) | ok |
| D9 | OTA, Rückfall, Sicherheitszähler, TLV hw_rev | REQ-FW-02/03/04 | MCUboot Swap-using-Move, `ota_min_mv` 2700 | PROTOTYP-PRÜFUNG PP-7, PP-12 |
| D10 | Reichweite und Linkreserve | REQ-RF-02/03 | Rechnung Phase 3 (ESP32-S3-Empfindlichkeit, vor dem Wechsel auf Pi D-014) | PROTOTYP-PRÜFUNG (Methode im Testplan T-R2) |
| D11 | Blinkmuster, Taster kurz/lang/sehr lang, Schutz vor Fehlbedienung | REQ-UI-02/04/06/07 | PROTOCOL 10.2/10.3, `core/fl_ui.c`, Host-Tests | ok; Sichtbarkeit E6 PROTOTYP-PRÜFUNG |
| D12 | Watchdog | REQ-FW-07 | `fl_hw.c` Watchdog-Treiber, Frist 10 min | ok (Code), Wirkung PROTOTYP-PRÜFUNG |
| D13 | Messkette FW-2 (Burst ≤ 0.6 ms, ≤ 4, Pause ≥ 30 ms), Mittelung | REQ-MES-10, REQ-ENE-06 | `fluidi_board.h`, `fl_hw.c` | PROTOTYP-PRÜFUNG PP-1/PP-2 |

## E Befunde (Ersteller-Selbstprüfung, für den Prüfer)

| Nr. | Gewicht | Befund | Vorschlag |
|---|---|---|---|
| K-1 | klein | README Kap. 1 nennt `build/build.log` als Ergebnis, der Makefile erzeugt die Datei aber nicht. Das Protokoll stand nur auf der Konsole. Für diesen Lauf habe ich es von Hand nach `build/` kopiert | `make` soll das Protokoll mit `tee` nach `build/build.log` schreiben, oder den README-Satz streichen |
| K-2 | klein | Speicherreserve: Flash ≈ 22 kB in Slot 0, RAM 3.2 kB | Bei neuen Funktionen `size_report` beachten; keine weitere Bibliothek ohne Grössenprüfung |
| K-3 | klein | Die einfache RC-Pulstabelle in `ENERGIE_REV_B.md` zeigte für Advertising 60 mV, SPICE dagegen 143 mV | Erledigt: Zeile beschriftet („nur 3 TX-Pulse … SPICE 143 mV“) |
| K-4 | klein | Laufzeit für 2 und 5 min fehlte im Rev-B-Budget (REQ-ENE-04) | Erledigt: Kap. 3d |
| W-1 | wichtig | REQ-ENE-02 im Fall pessDS mit 4 × 100 µF nicht erfüllt (W-6) | Entscheidungsregel und Messung E14, Auslegung von REQ-ENE-08 als D-Eintrag (`phase5_energiebudget_final.md` Kap. 5) |
| W-2 | wichtig | Die Linkbudget-Rechnung aus Phase 3 nutzt die Empfindlichkeit des ESP32-S3. Das Gateway ist inzwischen ein Pi Zero 2 W (D-014). Ein Empfindlichkeitswert für dessen BLE liegt lokal nicht vor (Product Brief ohne Wert) | REQ-RF-03 messtechnisch über die TX-Leistungsabsenkung nachweisen (Testplan T-R2). Das braucht keinen Empfindlichkeitswert |
