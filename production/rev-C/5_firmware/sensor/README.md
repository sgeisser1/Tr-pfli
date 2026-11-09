# fluidi Sensor-Firmware (CC2340R52, Rev B)

| | |
|---|---|
| Stand | 2026-11-07, Phase 4c Welle 2, Firmware/Energie – **Runde 1 ueberarbeitet** (Protokoll v2, PROTOCOL.md 0.2; Antworten `docs/reviews/phase4_firmware_response.md`) |
| Chip | CC2340R52E0RGER (QFN24 RGE) → SysConfig-Device `CC2340R5RGE`, **kein LaunchPad-Board** |
| Werkzeuge | TI SimpleLink Low Power F3 SDK 9.23.00.27, TI Arm Clang 4.0.4.LTS, SysConfig 1.28.2, imgtool 2.2.0rc1 (`~/fluidi-tools`) |
| Grundlagen | `firmware/PROTOCOL.md` v0.1, `docs/interfaces/PINMAP_SENSOR.md` **Rev B** (Regeln FW-1…FW-10), D-010, D-013, D-018, CONCEPTS 2.7/2.8, MESSKETTE_SALZ.md |

Kennzeichnungen wie im Projekt: **ANNAHME**, **PROTOTYP-PRUEFUNG** (erst am Muster nachweisbar).

## 1 Bauen und Pruefen (ohne IDE)

```sh
source ~/fluidi-tools/env.sh
cd firmware/sensor
make            # MCUboot + Anwendung + signiertes Image + Werks-Hex + Groessenbericht  (~30 s)
make check      # Flash-Layout- und Pin-Konsistenz + Host-Unit-Tests (C, Serie + TF-1..TF-4) + Python-Tests
make clean
```

Optionen: `HW_REV=A|B` (Default B), `VERSION=0.1.0 BUILD_NO=1 SEC_CNT=0`, `SIGN_KEY=<pem>` (Default DEV-Schluessel,
siehe `keys/README.md`), `VERBOSE=1`.
**Serie:** `make release SIGN_KEY=~/fluidi-keys/fluidi_prod_ec-p256.pem` – bricht ab bei DEV-Schluessel oder Schluessel
im Repository; gibt den Schluessel-Fingerabdruck aus, den `scripts/flash_sensor.py program --lock --expect-key-fp <fp>`
verlangt (F-W1).

Images tragen das geschuetzte TLV `0xA0 hw_rev` (PROTOCOL 0.2 Ae-10).

**Testfirmware (Testplan Anhang A, EP-15):** `make TESTFW=1|2|3|4 VERSION=<hoeher als laufend>` → `build-tf<n>/`,
nur DEV-signiert, Name `fl-tf<n>-XXXX`, Build-Nummer `9<n><bb>`; Code nur mit `FLUIDI_TESTFW` (`core/fl_testfw.c`),
Serien-Image ohne `TESTFW` bitgleich. Anleitung und Datenformate: `docs/manuals/TESTFIRMWARE.md`.

| Ergebnis (`build/`) | Inhalt |
|---|---|
| `fluidi-sensor-<ver>+<build>.bin` | signiertes MCUboot-Image fuer OTA (Kopf 0x100, SHA-256, ECDSA-P256, Sicherheitszaehler) |
| `fluidi-sensor-factory-<ver>-key<fp>.hex` | Erstprogrammierung: MCUboot + CCFG + bestaetigtes Image in Slot 0 → `scripts/flash_sensor.py`; `<fp>` = Fingerabdruck des eingebauten oeffentlichen Schluessels |
| `size_report.txt` | Belegung Flash/RAM gegen die Aufteilung, mit Pruefungen |
| `build.log` | Build-Protokoll (0 Fehler; 4 Linker-Hinweise #10325 zu NVS-Puffern, s. u.) |

Nachweis 2026-11-07 nach Runde 1 (sauberer Neubau): **0 Fehler**, Signatur mit `tools/verify_image.py` geprueft
(imgtool 2.2.0rc1 `verify` ist defekt: `KeyError 'SIG_PURE'`), `make check`: 1499 C-Pruefungen, 17 Tests Flash-Werkzeug,
3 Tests Kopplungsangriff (MITM v2: 0.39 % in 10 000 Laeufen) bestanden.
Die Linker-Hinweise #10325 entstehen, weil der NVS-Treiber seine Flash-Bereiche als `NOBITS` an feste Adressen bindet;
sie belegen keinen Inhalt im Image (Sektionen werden beim Signieren nicht kopiert).
Reproduzierbarkeit: unsigniertes Binaerbild ist bit-gleich; die ECDSA-Signatur ist randomisiert (Laenge ±1 Byte).

## 2 Aufbau

| Pfad | Inhalt | Test |
|---|---|---|
| `config/fluidi_board.h` | **einzige** Stelle fuer Pinnummern/Mux/Zeiten (PINMAP Rev B), Rev A per `HW_REV=A` | `make check-pins` (gegen PINMAP und SysConfig) |
| `config/fluidi_flash_layout.h` | Flash-Aufteilung | `make check-layout` (gegen MCUboot-/App-SysConfig, Linker) |
| `core/` | plattformneutral (C99): Krypto, Protokoll, Einstellungen, Messauswertung, Ringspeicher, NV-Speicher, LED/Taster, OTA, Anwendungslogik | Host-Tests `tests/` mit `-fsanitize=address,undefined` |
| `platform/cc23/` | CC2340-Port: BLE (BLEAppUtil, GATT, Advertising), Messkette (LGPT3), TMP1075N (I²C), Batteriemonitor, LED, Taster, NVS, MCUboot, Watchdog, Shutdown | nur Build (Hardware: PROTOTYP-PRUEFUNG) |
| `syscfg/`, `mcuboot/`, `linker/`, `mk/` | SysConfig, MCUboot-Konfiguration, Linker, Teil-Makefiles (aus SDK-Beispielen `basic_ble`, `mcuboot` abgeleitet) | – |
| `tools/` | Groessenbericht, Konsistenzpruefung, Image-Pruefung, Werks-Hex | – |
| `../tools/fluidi_proto.py` | **Python-Referenz des Protokolls** (unabhaengig, `cryptography`); Testvektoren `tests/gen_vectors.py` | Grundlage fuer Gateway |
| `../../scripts/flash_sensor.py` | ROM-UART-Bootloader-Werkzeug (TRM 8.5) mit `--sim`/`--dry-run`/`--lock` | `scripts/test_flash_sensor.py` |

Ausfuehrungsmodell: Der ganze Kern laeuft im BLEAppUtil-Task (ein Kontext, keine Sperren). Taster-ISR → FreeRTOS-Timer-
Task → `BLEAppUtil_invokeFunction`. Nach jedem Ereignis liefert `fl_app_process()` die naechste Frist (max. 5 min,
Watchdog 10 min); dazwischen Standby.

## 3 Flash-Aufteilung und Groessen (512 kB, Sektor 2 kB, DS S.20 Tab. 7.11)

| Bereich | Start | Groesse | belegt (Build 0.1.0+1) |
|---|---|---|---|
| MCUboot (letzter Sektor 0x05800 = BIMINFO/Sicherheitszaehler) | 0x00000 | 24 kB | 17.2 kB von 22 kB (76 %) |
| Slot 0 primaer (Kopf 0x100, Code ab 0x06100, 4 kB Trailer-Reserve) | 0x06000 | 228 kB | 206.7 kB Code (90 % der 224 kB) |
| Slot 1 sekundaer (OTA) | 0x3F000 | 226 kB | signiertes Image 207.1 kB (89 %) |
| BLE-Stack-NV (nvocmp, 2 Seiten) | 0x77800 | 4 kB | – |
| fluidi-NV (`core/fl_nvstore`, A/B, stromausfallsicher) | 0x78800 | 4 kB | Einstellungen, Kopplung, Zaehler, Fehlerprotokoll |
| Ringspeicher (`core/fl_ringlog`) | 0x79800 | 24 kB | ≥ 840 Datensaetze garantiert |
| Reserve | 0x7F800 | 2 kB | – |
| RAM | 0x20000000 | 36 kB | 33.7 kB (91 %), Rest 3.2 kB |

Abweichung zu PROTOCOL.md 6.4: Der Bereich „Einstellungen/Schluessel 8 kB“ ist in BLE-Stack-NV (4 kB) und fluidi-NV
(4 kB) geteilt (Kunden-NV-IDs des Stacks sind zu knapp). Ringspeicher-Kapazitaet garantiert 840 statt 1122 (24-Byte-
Eintrag mit CRC, ein Sektor stets frei): 8 Messungen/Tag → ≥ 105 Tage (REQ-LOG-01 erfuellt).
Reserve knapp: Anwendung 89 % des Slots. Der Grossteil ist BLE-Stack (`lib_opt`: CS, PAwR, PAST, Scanner usw. werden
mitgelinkt). **Offen FW-O1:** ungenutzte Stack-Funktionen ueber `build_components.opt`/SysConfig abwaehlen (Ziel < 170 kB).

## 4 Umsetzung der Anforderungen (Kurzuebersicht)

| Thema | Umsetzung | Quelle / Test |
|---|---|---|
| Funk waehrend Messung (F-W5) | Messung nur ohne Verbindung (MEASURE und Taster waehrend Verbindung → nach dem Trennen), Advertising fuer die Messdauer aus | Host-Test |
| Messung (FW-1/FW-2) | TMP1075N One-Shot (Konfig 0x01 ← 0x81, 15 ms Schlaf, Register 0x00), dann SENS_PWR aus, SDA/SCL low; erst danach Messkette. **Max. 4 Bursts** (DIO11 low, 50 µs, f0 250 µs, f1 250 µs mit DIO8 low, DIO11 high) ≤ 0.6 ms, **30 ms Schlaf** dazwischen, LED aus | `platform/cc23/fl_hw.c` `fl_port_measure`; SBOS854F S.21-22 Tab. 7-8 |
| Zaehlung ÷8 | LGPT3 C0 (T3C0, DIO24 Mux 3), „Periode-und-Pulsbreite“ (CCACT 8, TRM 10.3.6.1) bei 48 MHz; Mittel vieler Perioden mit zufaelliger Phase → Aufloesung ≪ 1 Takt. Pinperiode/8 = Oszillatorperiode | **PROTOTYP-PRUEFUNG** (Aufloesung, Max.-Frequenz 4.51 MHz, Ereignisrate) |
| Kapazitaet (FW-3) | ratiometrisch C = dC·(T0−td)/(T1−T0) − C_basis, danach VDD-Offset c_kv·(3.0 V−VDD) mit VDD **vor** dem Burst (ohne Funk/LED); Startwerte aus SPICE `osc_report.txt`: dC 17.29 pF, C_basis 15.21 pF, c_kv 5.33 pF/V (−3.2 pF bei 2.4 V); td-Pfad (tpd) und Temperaturkoeffizient vorbereitet (0) | `core/fl_meas.c`; neue TLV 0x10–0x16 |
| Mittelung/Ausreisser (REQ-MES-10) | Teilbloecke je Konfiguration (≤ 16), Median + MAD, Verwerfen > 4σ, Flags b0/b1 | Host-Test |
| Plausibilitaet (REQ-MES-12) | `air_raw`/`flood_raw` → Flags b2/b3; Messkette gestoert → b5 + Fehler 0x20/0x21 | Host-Test |
| Feuchteindex | Referenzformel ‰ ohne Begrenzung (> 100 % = Duenger-Hinweis, D-018); massgebend Gateway | Host-Test |
| Ringspeicher | 24-B-Eintraege mit CRC16, Sektorkopf, seq aus Eintrag, Quittung/`lost_records`/Werkseinstellung im NV; ≤ 11 Schreibvorgaenge je 256-B-Zeile (DS: ≤ 83) | Host-Test inkl. Stromausfall |
| BLE / GATT | Dienst/RX/TX nach PROTOCOL 3, Legacy-ADV 29 Byte, `fluidi-XXXX`, oeffentliche Adresse, kein SMP-Pairing (`GAPBOND_PAIRING_MODE_NO_PAIRING`) | Host-Test (Kodierung) |
| Kopplung/Sitzung (v2) | ECDH P-256 (TI ECDH-Treiber), HKDF/HMAC/SHA-256 (Kern), AES-CCM-8 mit Hardware-AES; **Commitment/Reveal** vor der Farbfolge (F-K1); RNG-Fehler → Abbruch (F-W4); Sperre nach 3 kryptografischen Fehlversuchen, Fristueberschreitungen separat (10); Fristen ab CCCD-Write (K-1/K-2) | Host-Tests gegen Python-Referenz, Angriffstest |
| Befehle | alle aus PROTOCOL 5.4 inkl. Datensatzstrom, TX-Warteschlange (3 Frames) | Host-Gesamttest (simulierte Plattform) |
| Zeit | uptime + boot_id, TIME_SET → Lokalzeit fuer LED-Fenster und Messraster (Versatz addr mod 300 s) | Host-Test |
| LED (FW-4, D-010) | Muster L1–L17, Blau nur ab 2.65 V sonst Gelb, keine LED unter 2.4 V (ausser Taster), L8 1×/min, ohne Zeit 2 min, Vorrang Fehler > Batterie > Giessen; L8-Puls 5 ms | Host-Test |
| Taster | kurz/lang/sehr lang + Bestaetigung, Trennbereiche, Klemmen > 30 s → Pull-up aus, Pruefung je 60 s | Host-Test |
| Reset-Schleifen (F-W3) | Start: zuerst VDD und Neustartgrund lesen, Flash erst danach; Brownout/UV → weiter erst ab 2.6 V; abnormale Neustarts (WDT, Brownout, Absturz, ungeplanter SW-Reset) im Retention-Register PMCTL.AONRSTA1 gezaehlt, ab 3 ohne 10 min stabilen Betrieb Abschaltung; Shutdown bei gedruecktem Taster ohne Tasterwecken | Host-Tests `test_resets` |
| Unterspannung (FW-5) | VDD-Minimum waehrend Verbindung (Verbindungsereignis-Callback) und unter Messlast; < 2.4 V zweimal oder < 2.3 V → Notspeichern, Fehler 0x55, Shutdown mit Wake-on-DIO21; Neustart erst ab 2.6 V Ruhe (ANNAHME) | Host-Test |
| Watchdog | 10 min (TI Watchdog), Kern weckt ≤ 5 min; MCUboot 60 s | – |
| Ausnahmen (O-5) | HardFault, NMI, nicht registrierter Interrupt → `fl_fault_handler` (SysConfig `/freertos/exception` Custom): Retention-Bit `FL_RET_FAULT` (PMCTL.AONRSET1, Bit 13), `PLANNED` loeschen, sofort Systemreset (PMCTL.RSTCTL.SYSRST); kein Flash, kein Stack. Start meldet `reset_reason` 5 (hardfault), zaehlt als abnormal (F-W3). Fault im Handler/Stapelfehler → Lockup → Hardware-Reset LOCKUP = ebenfalls 5. BLE-Stack-Assert (alle Ursachen) und FreeRTOS-Stackueberlauf: `platform/cc23/fl_assert.c` → `fl_fault_handler` (SDK-`main_freertos.c` ersetzt durch `fl_main.c`). Nicht abgedeckt: MCUboot (`faultISR`/`nmiISR` Schleife → MCUboot-Watchdog 60 s), SDK-Schleifen `util.c` Z. 306, `NVOCMP_ASSERT1` (→ Watchdog 10 min) | Host-Tests `test_fault`, `test_assert`, TF-2 9 x; Build: `tools/check_fault_vectors.py` |
| Schlaf (FW-6/FW-8) | sofort beim Start: DIO16/17 Ausgang low (SWD-Pulls aus), DIO11 high, DIO12 low, DIO8/24 Puffer aus, LEDs high | `fl_platform_early_init` |
| OTA (REQ-FW-02…05) | Empfang in Slot 1 (Sektor erst vor Schreiben loeschen, Go-back-N, SHA-256, Fortsetzung 24 h), `boot_set_pending(0)` → Test-Swap; Bestaetigung erst nach Selbsttest **und** authentisierter Sitzung, sonst nach 24 h Neustart → Rueckfall; Ergebnis 0x44/0x49 aus Slot-1-Inhalt | Host-Test (Empfang); Swap/Rueckfall **PROTOTYP-PRUEFUNG** (FW-P2) |
| Anti-Rollback | MCUboot `MCUBOOT_HW_ROLLBACK_PROT` + Downgrade-Schutz, Zaehler im BIMINFO-Sektor; `SEC_CNT` beim Signieren; Sensor lehnt Version ≤ laufend ab (0x45) | Zusammenspiel mit Swap **PROTOTYP-PRUEFUNG** |

## 5 MCUboot, CCFG und Sicherheit

- MCUboot aus dem SDK (`swapUsingMove`, ECDSA-P256, Anti-Rollback), eigene LED-Datei (`mcuboot/fluidi_led_debug.c`:
  das SDK-Original blinkt LaunchPad-Pins DIO14/15 und wartet bei jedem Start 3 s). CCFG-CRCs mit SDK `crc_tool`
  (Gegenprobe im Python-Test).
- **Entwicklung** (Default): ROM-Seriell-Bootloader aktiv, nur mit gedruecktem Taster DIO21 beim Start, UART RX DIO20 /
  TX DIO6 (TRM S.464-465). SWD erlaubt (keine Pads, E3).
- **Serie**: `scripts/flash_sensor.py program --lock --expect-key-fp <fp>` (nur mit Produktionsschluessel, DEV wird
  abgelehnt) schreibt CCFG mit `pBldrVtor = FORBID`, `bldrEnabled = 0`, `allowDebugPort`/`allowFlashProgram`/
  `allowToolsClientMode`/`allowReturnToFactory = FORBID`, Debug-Autorisierung verboten, **WEPRA Sektoren 0–10
  (MCUboot) und CCFG-Sektor schreibgeschuetzt**, Sektor 11 (BIMINFO) frei (TRM S.460 Tab. 8-35; `hw_ccfg.h`).
  Danach nur noch OTA. Wirksamkeit **PROTOTYP-PRUEFUNG** PP-9.
- **Prototyp-Hinweis (F-L3):** Taster beim Einsetzen der Zelle nicht druecken, sonst laeuft der ROM-Bootloader mit
  aktiver CPU (Entwicklungs-CCFG). Restrisiko ROM-CRC32 auf Schluesselsektoren entfaellt in der Serie (Bootloader aus);
  im Entwicklungszustand ist der Schluesselbereich mit Zufallsbyte aufgefuellt (PROTOCOL 4.6).
- Schluessel: `keys/README.md`.

## 6 Kalibrierung der Messkette (Werk, PROTOTYP-PRUEFUNG)

1. **Referenz-C**: Sonde in Luft und mit 2 bekannten C0G-Kondensatoren (z. B. 10/47 pF) an TP5 → `MEASURE purpose 3`
   bei 3.0 V; `cref_eff` (0x10) und `cpar` (0x11) per Ausgleichsrechnung, Rest-tpd ggf. `td0_ps` (0x12).
2. **VDD**: dieselbe Messung bei 3.0/2.7/2.4 V (Labornetzteil statt Zelle, Dummy-Adapter) → `c_kv` (0x15).
3. **Temperatur**: 10/25/35 °C → `c_kt` (0x16), optional `td_kt` (0x14).
4. Gateway kalibriert danach trocken/nass pro Topf (PROTOCOL 1) – unabhaengig von 1–3.

## 7 PROTOTYP-PRUEFUNG (Firmware)

| Nr | Pruefung |
|---|---|
| PP-1 | Zaehlverfahren LGPT3: Aufloesung (Ziel ≤ 0.1 pF Streuung), Funktion bis 4.51 MHz MEAS_CLK, keine verlorenen Captures |
| PP-2 | Burstdauer ≤ 0.6 ms, Pause ≥ 30 ms, VDD-Einbruch waehrend Burst (Oszilloskop an DIO11/VDD, ENERGIEMESSUNG.md) |
| PP-3 | TMP1075N: Einzelbyte-Schreiben, Wandlungszeit, I²C bei 100 kHz ueber 30 mm Leitung |
| PP-4 | Advertising-Umschaltung (`GapAdv_disable` → Parameter → `loadByHandle` → `advStart`) ohne Fehlzustand; ADV_END-Zaehlung |
| PP-5 | Benachrichtigungen bei MTU 247, TX-Warteschlange, HCI-„Completed Packets“-Ereignis |
| PP-6 | ECDH-Format (0x04‖X‖Y big-endian) und Rechenzeit (ANNAHME ≤ 3 s); Z = x-Koordinate |
| PP-7 | MCUboot Swap-using-Move, Rueckfall ohne Bestaetigung, Sicherheitszaehler, `boot_set_pending` aus der Anwendung waehrend BLE |
| PP-8 | Batteriemonitor-Werte im Verbindungsereignis (FW-5); Shutdown/Wake DIO21 |
| PP-9 | CCFG Serie (`--lock`): Bootloader wirklich gesperrt, OTA funktioniert weiter |
| PP-11 | Reset-Schleife (F-W3): Quelle 2.0–2.4 V ueber 100–300 Ω, Taster gedrueckt; Mittelstrom, NV-Schreibzahl, Retention-Register nach Brownout; **EOL-Quelle mit Einbruch unter die POR-Schwelle**: gemeldeter Neustartgrund (POWER_ON statt Brownout?), NV-Schreibzahl je Zyklus (Soll 0 bis zur ersten bestandenen Lastmessung, N-2), Ladung je Boot inkl. MCUboot-ECDSA |
| PP-12 | MCUboot akzeptiert das zusaetzliche geschuetzte TLV 0xA0; Verbindungsparameter-Anfrage des Sensors wird von BlueZ angenommen |
| PP-10 | Ruhestrom nach FW-8 (Ziel lt. Energiebudget), Ladung je Ereignis → `Q_ADV_UC`, `Q_CONN_UC`, `Q_MEAS_UC` in `core/fl_app.c` |

## 8 Offene Punkte

| Nr | Punkt |
|---|---|
| FW-O1 | Stack-Umfang reduzieren (Slot 89 % belegt, RAM 91 %) |
| FW-O3 | LED-Dimmung `led_level` per LGPT0/1-PWM (derzeit nur Ein/Aus; Vorwiderstaende begrenzen bereits ≤ 3 mA) |
| FW-O4 | Messung jetzt nur ohne Verbindung und mit angehaltenem Advertising (F-W5); Restrisiko: Stack-interne Funkereignisse – Messung PP-2 |
| FW-O5 | Gateway auf Protokoll v2 umstellen (Software-Agent; Aenderungsliste PROTOCOL.md Kap. 0) |
| FW-O6 | `scripts/energy_budget.py` mit Q_MEAS Rev B (4 Bursts ≈ 31 µC + TMP ≈ 50 µC) und Messwerten nachfuehren (FW-P5) |
