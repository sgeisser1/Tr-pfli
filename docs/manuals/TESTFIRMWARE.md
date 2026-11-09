# fluidi – Testfirmware Sensor (TF-1…TF-4)

| | |
|---|---|
| Stand | 2026-11-09, Firmware/Energie, Phase 6 – erstellt vor Musterankunft (EP-15) |
| Grundlage | `docs/reviews/phase5_testplan_prototyp.md` **Anhang A** (TF-1…TF-4), Kap. 10 (EP-03, EP-15, EP-16), D-025 (Abschaltung 2.4 V unter Last) |
| Code | `firmware/sensor/core/fl_testfw.c/.h` (nur mit `TESTFW`), Haken in `core/fl_app.c`, `core/fl_ui.c`, `core/fl_proto.c`, `platform/cc23/fl_hw.c` (alle `#if FLUIDI_TESTFW`) |
| Auswertung | `scripts/testfw_eval.py` (Tests: `scripts/test_testfw_eval.py`, mit `--sim` ohne Hardware) |
| Nicht ausliefern | Testfirmware ist **nur DEV-signiert**, heisst `fl-tf<n>-XXXX`, Build-Nummer `9<n><bb>`; `make release` und `flash_sensor.py --lock` lehnen sie ab |

Kennzeichnungen wie im Projekt: **ANNAHME**, **PROTOTYP-PRÜFUNG** (erst am Muster nachweisbar).

## 1 Sicherheitsregeln (gelten für jede Testfirmware-Sitzung)

- Programmieren Weg B: **2.0 V** (höchstens 2.2 V mit dem CH343-Adapter, **höchstens 2.1 V mit dem PL2303-Board**),
  **Strombegrenzung 10 mA** (EP-03, PS-L3), nur mit **Dummy-Scheibe** im Clip, nie mit Zelle (`PROGRAMMIEREN_SENSOR.md`
  v1.2 Kap. 1 Regel 2 und Kap. 5; Sicherheit K-2 Phase 6).
- Funktions- und Energietests mit Funk (TF-1…TF-4): **3.0 V, Strombegrenzung 30 mA, nur über die Dummy-Scheibe, nie mit
  Zelle im Clip** (EP-03). Strommessung nach `ENERGIEMESSUNG.md` (Aufbau A–D).
- Unter **2.4 V unter Last** schaltet auch die Testfirmware ab (FW-5/D-025, Serienlogik unverändert); E6/LED bei 3.0 V
  und 2.6 V (EP-16).
- Keine Speisung über TP1/TP2.

## 2 Bauen

```sh
source ~/fluidi-tools/env.sh
cd firmware/sensor
make TESTFW=1 VERSION=0.1.1            # -> build-tf1/  (TF-1 Watchdog)
make TESTFW=2 VERSION=0.1.1            # -> build-tf2/  (TF-2 Reset-Schleife)
make TESTFW=3 VERSION=0.1.3            # -> build-tf3/  (TF-3 SENS_PWR dauernd)
make TESTFW=4 VERSION=0.1.1            # -> build-tf4/  (nur Diagnose)
make check                             # Host-Tests Serie + TF-1..TF-4 + Auswertung (siehe Kap. 8)
```

Seriell bauen (`make -j` scheitert schon im Serienstand an einer fehlenden Abhängigkeit auf die SysConfig-Ausgabe).

| Ergebnis (`build-tf<n>/`) | Zweck |
|---|---|
| `fluidi-sensor-tf<n>-<ver>+9<n><bb>.bin` | signiertes Image für OTA über das Gateway |
| `fluidi-sensor-tf<n>-factory-<ver>+9<n><bb>-key<fp>.hex` | Erstprogrammierung Weg A/B mit `scripts/flash_sensor.py` |
| `size_report.txt` | Flash/RAM |

Schutz im Makefile (geprüft 2026-11-09): `TESTFW` nur 1…4; mit einem Schlüssel, der nicht `DEV_ONLY_*` heisst,
bricht der Build ab; `make release` bricht mit gesetztem `TESTFW` ab; `BUILD_NO` 0…99 bei Testfirmware, Serien-
`BUILD_NO` ≥ 9000 wird abgelehnt (reserviert). Ohne `TESTFW` ist das Serien-Image **bitgleich** zum Stand vor der
Testfirmware (unsigniertes Binärbild und MCUboot mit `cmp` verglichen, Commit 4f2f32d). Seither einzige Änderung der
Serie: eigene Ausnahmebehandlung `fl_fault_handler` (O-5, +66 B Code) und Assert-/Stackueberlauf-Behandlung über
denselben Weg (`platform/cc23/fl_assert.c`, `fl_main.c` statt SDK-`main_freertos.c`; −178 B, SDK-`AssertHandler` entfällt).

Grössen (Build 2026-11-09 mit O-5 inkl. Asserts und Phase-6-Befunden C-1/W-2, TI Arm Clang 4.0.4, `VERSION=0.1.1`, ohne Compiler-Warnung):

| Build | Slot 0 Code | Anteil | signiertes Image (Slot 1) | RAM | RAM frei |
|---|---|---|---|---|---|
| Serie 0.1.0+1 | 206 946 B | 90 % | 207 377 B | 33 689 B | 3 175 B |
| TF-1 0.1.1+9101 | 208 926 B | 91 % | 209 357 B | 33 805 B | 3 059 B |
| TF-2 0.1.1+9201 | 208 964 B | 91 % | 209 396 B | 33 805 B | 3 059 B |
| TF-3 0.1.1+9301 | 209 412 B | 91 % | 209 844 B | 33 805 B | 3 059 B |
| TF-4 0.1.1+9401 | 208 904 B | 91 % | 209 335 B | 33 805 B | 3 059 B |

Alle Prüfungen des Grössenberichts „ok“ (passt in Slot 0/Slot 1 inkl. Swap-using-Move, RAM-Reserve ≥ 2 kB); dazu
`tools/check_fault_vectors.py` (Ziel `size`): NMI-/HardFault-Vektor → `fl_fault_handler`, ohne Stack, kein
`Exception_handlerSpin` mehr in der Vektortabelle; `AssertHandler`/`vApplicationStackOverflowHook` aus `fl_assert.obj`
rufen nur `fl_fault_handler`, SDK-`main_freertos.obj` nicht gelinkt, `main` registriert `AssertHandler`, Rückfall-
Callbacks der BLE-Bibliothek ohne Schleife (O-5).

## 3 Kennzeichnung (Anhang A „nie mit Werksfirmware verwechseln“)

| Merkmal | Serie | Testfirmware TF-n |
|---|---|---|
| Gerätename im Advertising | `fluidi-XXXX` | `fl-tf<n>-XXXX` (gleiche Länge, 11 Zeichen; das Gateway identifiziert über die Adresse, nicht den Namen) |
| Startsignal | L11 | **Rot/Grün abwechselnd 3 ×** (je 100 ms, Pause 100 ms, ANNAHME; PROTOCOL 10.2 legt es noch nicht fest), danach L11 |
| `fw_build` (SESSION_INFO/INFO, u32) | < 9000 | `9<n><bb>`, z. B. TF-1 Build 1 = **9101** (der Testplan verlangt „Suffix `-tf<n>`“; `fw_build` ist eine Zahl, PROTOCOL 5.5 → Ziffernfolge statt Text) |
| GET_INFO (0x90) | 68 Byte | 72 Byte: Anhang `'T' 'F' <n> <tf_fmt=1>` ab Offset 68 (Gateway ignoriert Zusatzbyte, `protocol.py` `SessionInfo.parse`) |
| GET_DIAG (0x98) | PROTOCOL 5.7 | + 68-Byte-Anhang TF-4 (Kap. 6) |
| Dateiname | `fluidi-sensor-<ver>…` | `fluidi-sensor-tf<n>-<ver>…` |
| Signatur | DEV (Muster) bzw. Produktion | **nur DEV** |

SESSION_INFO (52 Byte, jede Sitzung) bleibt unverändert, damit das Gateway normal arbeitet. Gateway und PWA zeigen
„Firmware x.y.z · Build n“ und eine rote Marke **TESTFIRMWARE TF-n**, sobald Gerätename `fl-tf<n>-`, Build `9<n>xx` oder
der TF-Anhang einer Diagnose sie zeigt (O-3 erledigt, GATEWAY_API 5.10); das Ereignisprotokoll meldet sie. Die Kennung im
Gateway bleibt `fluidi-XXXX` (aus der Adresse).

## 4 Einspielen und Rückkehr zur Normalfirmware

**Weg B (vor dem Verguss, S2: PT5.12):** wie `PROGRAMMIEREN_SENSOR.md` Kap. 5 mit dem Testfirmware-Hex:

```sh
HEX=firmware/sensor/build-tf1/fluidi-sensor-tf1-factory-0.1.1+9101-key*.hex
python scripts/flash_sensor.py program --hex $HEX --sim --yes --testfw 1      # Probelauf
python scripts/flash_sensor.py program --hex $HEX --port /dev/ttyACM0 --testfw 1
```

`flash_sensor.py` erkennt Testfirmware an der Build-Nummer 9000–9999 im MCUboot-Kopf von Slot 0 (bzw. `-tf<n>-` im
Dateinamen) und programmiert sie **nur mit `--testfw <n>`** (passende Nummer; `--yes` genügt nicht); `--lock` mit
Testfirmware wird immer abgelehnt (Sicherheit W-2 Phase 6, Tests `scripts/test_flash_sensor.py` `TestTestfirmware`).

Weg A/B löscht den ganzen Flash (Chip-Erase): Kopplung, Zähler, Fehlerprotokoll und Ringspeicher sind danach leer;
der Sensor muss neu gekoppelt werden, bevor das Gateway GET_DIAG lesen kann. **Ergebnisse (GET_DIAG) vor dem
Zurückflashen auslesen.** Zurück: Werks-Hex der Serie ebenso flashen (Version beliebig, da Chip-Erase).

**OTA (nach dem Verguss, S4: PT11.07, PT11.19):** Das Gateway verteilt nur Images mit **höherer `major.minor.patch`**
(`fluidi_gw/central.py` `ota`: `tuple(vparts) <= cur` → Abbruch; die Build-Nummer zählt dort nicht), der Sensor lehnt
Version+Build ≤ laufend ab (`fl_ota.c` `fl_ver_newer`) und MCUboot verbietet Downgrades (SEC_CNT, ST-S7). Das Gateway
prüft die Signatur mit `fw_pubkey` (`fluidi_gw/config.py`): für die Muster muss dort der **öffentliche DEV-Schlüssel**
eingetragen sein (ANNAHME, wie für die DEV-signierte Werksfirmware), und in `gateway.toml` muss
`allow_testfw = true` stehen (Werk `false`, Sicherheit W-2): erst dann nimmt das Gateway Abbilder mit Build 9xxx an,
markiert sie rot „TESTFIRMWARE“ und verteilt sie nur an einen einzeln gewählten Sensor nach Bestätigung
(GATEWAY_API 5.4). Darum alle Images **vorab** mit steigender
Patch-Nummer bauen, z. B. für S4:

| Schritt | Image | Befehl |
|---|---|---|
| Werk | Serie 0.1.0+1 | `make` |
| 1 | TF-2 0.1.1 | `make TESTFW=2 VERSION=0.1.1` |
| 2 | Serie 0.1.2 (Rückkehr) | `make VERSION=0.1.2 BUILD=$PWD/build/r0.1.2` |
| 3 | TF-3 0.1.3 | `make TESTFW=3 VERSION=0.1.3` |
| 4 | Serie 0.1.4 (Rückkehr) | `make VERSION=0.1.4 BUILD=$PWD/build/r0.1.4` |

Die Testfirmware bestätigt sich nach OTA wie die Serie (Selbsttest + authentisierte Sitzung, PROTOCOL 9.5). Die
Testzähler (NV-id 6) bleiben nach der Rückkehr im Flash liegen und werden von der Serienfirmware ignoriert.

## 5 Bedienung: Tastersequenzen

Eine **Sequenz** = n kurze Drücke (50 ms – 1.5 s, PROTOCOL 10.3), Abstand je ≤ 2 s (ANNAHME); ausgewertet 2 s nach dem
letzten Druck. Jeder kurze Druck löst wie in der Serie eine Messung aus (L1/L2/L15). Erkannt → Quittung
**Rot/Grün/Rot/Grün je 50 ms**, danach die Aktion (erst wenn keine Verbindung besteht). Andere Anzahlen: keine Aktion.
Im Kopplungsschritt „Farben vergleichen“ zählt ein kurzer Druck nicht (Serienbedeutung „Farben stimmen“).

| Variante | Sequenz | Aktion |
|---|---|---|
| TF-1 | 5 × kurz | Endlosschleife im Anwendungs-Task **ohne** Watchdog-Bedienung; BLE-Stack läuft weiter. Erwartung: Neustart nach ≤ 10 min (`CONFIG_WATCHDOG_0` period = 600 000 ms, SysConfig) |
| TF-2 | 5 × kurz | **fataler Fehler über den Serienpfad** (`fl_platform_fatal`, wie `crit_err` des BLE-Stacks) sofort und danach bei **jedem Start nach allen Start-Schreibvorgängen** → Reset-Schleife bis zur Serienreaktion |
| TF-2 | 7 × kurz | wie 5 ×, aber im Start **vor der ersten Lastmessung** (N-2: Soll 0 Flash-Schreibvorgänge je Zyklus) |
| TF-2 | 9 × kurz | **echter HardFault** (undefinierter Befehl, `__builtin_trap`) sofort und bei jedem Start → Serien-Ausnahmebehandlung `fl_fault_handler` (O-5): Bit `FL_RET_FAULT` setzen, sofortiger Systemreset, Neustartgrund **hardfault** (5) |
| TF-3 | – | keine Sequenz; ab Start dauernd aktiv |
| TF-4 | – | keine Sequenz; nur Diagnose |

Serienreaktion TF-2 (F-W3, `fl_app.c`): abnormale Neustarts (Watchdog, Brownout, Absturz, ungeplanter Software-Reset)
werden im Retention-Register gezählt; der **3.** abnormale Start schaltet **ohne Flash-Schreiben** ab (Shutdown,
Wecken nur per Taster). Ablauf 5 ×: Auslöser = 1. Neustart → Start mit Zähler 1 → fatal → Start 2 → fatal → Start 3
→ Abschaltung (Sekunden, auch mit 9 ×: seit O-5 kein Warten auf den Watchdog mehr). **Danach Taster drücken** (nicht die
Speisung trennen: Power-on löscht das Retention-Register und damit das Ergebnis); der Sensor startet normal, speichert
das Ergebnis und beendet den Test.

TF-2 legt seine Daten in den Bits 7–12 und 14–17 von `PMCTL.AONRSTA1` ab (18 bit, SDK `hw_pmctl.h` Z. 650
`PMCTL_AONRSTA1_FLAG_M = 0x0003FFFF`; Bits 0–6 und 13 (`FL_RET_FAULT`, O-5) belegt die Serie, `fl_app.h`; kein
SDK-Treiber für CC23x0R5 nutzt das Register, `grep` im SDK 9.23): Modus, max. Flash-Operationen je Zyklus (≤ 15, seit
O-5 4 bit), Zahl der fatalen Neustarts (≤ 3), Flash-Operationen im abschaltenden Start (≤ 3).

## 6 Datenformate (Testfirmware, `tf_fmt` = 1, little-endian)

**GET_DIAG-Anhang (68 Byte, nach `wdt_resets…button_stuck` aus PROTOCOL 5.7):**

| Off | Typ | Feld | Bedeutung |
|---|---|---|---|
| 0 | 2 × u8 | `'T' 'F'` | Kennung |
| 2 | u8 | `variant` | n von TF-n |
| 3 | u8 | `tf_fmt` | 1 |
| 4 | 4 × u32 | `meas`, `adv`, `conn`, `led_ms` | Zähler seit Start (wie INFO 5.5) |
| 20 | u32 | `charge_uc` | Ladungsschätzung (S-5) |
| 24 | u8 | `reset_reason` | wie SESSION_INFO (2 = Watchdog) |
| 25 | u8 | `abn_now` | Zähler abnormaler Neustarts jetzt (F-W3; nach 10 min stabil 0) |
| 26 | u32 | `ret_boot` | Retention-Register beim Start (roh, 18 bit) |
| 30 | u16 | `vdd_min` | kleinste VDD unter Last seit Start (Messung, Verbindung), mV; 0xFFFF = keine |
| 32 | u16 | `vbat_rest` | Ruhewert beim Start, mV |
| 34 | u16 | `vdd_min_ever` | kleinste VDD seit Einspielen der Testfirmware (nichtflüchtig, stündlich gesichert) |
| 36 | u16 | `boot_id` | Startzähler |
| 38 | u16 | `flash_ops_boot` | Schreib-/Löschvorgänge fluidi-NV + Ringspeicher seit Start (ohne eigene Testdaten) |
| 40 | u16 | `flash_ops_ready` | dito bis zur ersten bestandenen Lastmessung (**N-2: Soll 0**) |
| 42 | u16 | `backoffs` | Abschaltungen wegen Reset-Schleife (Serienzähler, sonst nicht abfragbar) |
| 44 | u16 | `tf1_trig` | TF-1 ausgelöst (nichtflüchtig) |
| 46 | u16 | `tf2_trig` | TF-2 ausgelöst (nichtflüchtig) |
| 48 | u8 | `tf2_mode` | letzter abgeschlossener TF-2-Lauf: 1 spät (5 ×), 2 früh (7 ×), 3 HardFault (9 ×) |
| 49 | u8 | `tf2_cycles` | fatale Neustarts inkl. Auslöser bis zur Abschaltung (**Soll 3**) |
| 50 | u8 | `tf2_max_ops` | max. Flash-Operationen in einem Schleifenzyklus (gesättigt 15) |
| 51 | u8 | `tf2_sd_ops` | Flash-Operationen im abschaltenden Start (**Soll 0**) |
| 52 | u32 | `tf3_reads` | TMP1075N-Lesungen (TF-3) |
| 56 | u32 | `tf3_err` | davon I²C-Fehler |
| 60 | 3 × i16 | `tf3_last`, `tf3_min`, `tf3_max` | 0.01 °C; 0x8000/0x7FFF = keiner |
| 66 | u8 | `tf3_stage` | Stelle des letzten I²C-Fehlers: 1 `I2C_open`, 2 Schreiben, 3 Lesen |
| 67 | u8 | `sens_pwr_hold` | 1 = SENS_PWR dauernd high (TF-3) |

Flash-Operationen zählt die Plattform je NVS-Schreib- bzw. Löschaufruf auf fluidi-NV und Ringspeicher
(`fl_hw.c` `f_write`/`f_erase`; `fl_nvstore` überspringt unveränderte Einträge). Die Host-Simulation zählt NV-Einträge
logisch; absolute Werte daher nur am Muster aussagekräftig.

**TF-3-Datensatz** (PROTOCOL 5.6, alle 60 s): `cause` = **0x83** (nur Testfirmware), `c_probe` = 0xFFFF (kein
Feuchtewert), `c_diag` = kumulierter I²C-Fehlerzähler, `temp` = TMP1075N (0x8000 + `flags` b4 bei Fehler), `vbat_mv` =
letzter Lastwert. Das Gateway speichert die Zeilen unverändert in `reading` (Index `null`, Warnflag 16).

## 6a Auslesen über das Gateway (GET_INFO + GET_DIAG)

Der Sensor muss mit dem Gateway gekoppelt sein (nach Weg A/B neu koppeln).

1. PWA: **Einstellungen → Sensoren & Firmware** (oder Pflanze → Karte „Sensor“) → Textknopf **Diagnose** →
   **Diagnose abrufen**. Das Gateway fragt beim nächsten Funkkontakt (≤ Reaktionszeit; schneller: kurz die Taste drücken,
   ausser in TF-1/TF-2-Sequenzen zählen dabei Drücke mit!) `GET_INFO` und `GET_DIAG` ab. Gleich per API:
   `POST /api/v1/sensors/fluidi-XXXX/diag` (Sitzung + CSRF), dann `GET /api/v1/jobs/{id}`.
2. Ergebnis im Sheet (dekodiert) und als **JSON herunterladen** (`fluidi-diag-<id>-<zeit>.json`, enthält `info_hex`,
   `diag_hex` und die dekodierten Felder). Jede Abfrage wird im Gateway gespeichert (Tabelle `sensor_diag`, 50 je Sensor,
   bleibt nach dem Entkoppeln erhalten).
3. Auswertung nach Testplan, wahlweise:

```sh
.venv/bin/python scripts/testfw_eval.py diag --file fluidi-diag-fluidi-ABCD-20261109T143000Z.json --expect tf1
.venv/bin/python scripts/testfw_eval.py diag --db /var/lib/fluidi/fluidi.sqlite --sensor fl-tf2-ABCD --expect tf2-late
.venv/bin/python scripts/testfw_eval.py info --db /var/lib/fluidi/fluidi.sqlite --sensor fluidi-ABCD
```

`--sensor` akzeptiert Adresse, `fluidi-XXXX` oder den Testfirmware-Namen `fl-tf<n>-XXXX`. Die Datenbank nur lesend
öffnen (Skript tut das) bzw. eine Kopie verwenden. Gateway, PWA-Anzeige und Skript dekodieren mit demselben Modul
(`firmware/gateway/fluidi_gw/sensordiag.py`).

Ablauf für PT5.12 (TF-1): Diagnose **vor** dem Zurückflashen abrufen (Weg B löscht alles), JSON sichern, dann flashen.

## 7 Zuordnung zu den Tests

| Test-ID | Muster | Variante | Durchführung | Auswertung / Kriterium |
|---|---|---|---|---|
| **PT5.12** (T-W1, REQ-FW-07) | S2, vor Verguss | TF-1 (Weg B) | **frische Zelle bzw. Netzteil 3.0 V über die Dummy-Scheibe** (in der Endlosschleife läuft keine Unterspannungsüberwachung, K-3 Elektronik); koppeln, 5 × kurz, ≤ 10 min warten, Sensor startet (Startsignal Rot/Grün). Grund „brownout“ statt „watchdog“ = Versorgung prüfen, wiederholen (kein NOK) | GET_DIAG: `testfw_eval.py diag --expect tf1` → Grund Watchdog, `wdt_resets` ≥ `tf1_trig`, Eintrag 0x50; danach Werks-Hex zurück |
| **PT11.07** (ST-F6, PP-11) | S4 | TF-2 (OTA) | 5 × → Schleife bis Abschaltung (LED aus, kein Advertising), Mittelstrom mit Aufbau D/A, dann Taster; wiederholen mit 7 × und 9 × | `diag --expect tf2-late / tf2-early / tf2-hf` → `tf2_cycles` = 3, `tf2_sd_ops` = 0, früh `tf2_max_ops` = 0, spät Wert notieren; HardFault (9 ×): ≥ 2 Einträge 0x52 mit `detail` ≠ 0xBF (Grund hardfault, O-5), Schleife bis Abschaltung in Sekunden statt ≈ 30 min; Mittelstrom ≤ 10 × Ruhestrom (Testplan, ANNAHME) am Aufbau |
| **PT11.19** (ST-W4, M-W4) | S4, S5 | TF-3 (OTA) | Referenz Δ(t0) nach dem Verguss vor den Klimazyklen, dann Klimazyklen; Gateway in Reichweite (Ringspeicher 840 Datensätze ≈ 14 h bei 1/min); danach Δ(nach) | `testfw_eval.py tf3 --db fluidi.sqlite --sensor <addr>` (keine ungültige Lesung) und `diag --expect tf3`; Leck = Δ(nach) − Δ(t0) mit Aufbau C (Kap. 7.1) |
| **PT6.16 / PT11.07** (TF-4) | alle | jede TF-n | GET_DIAG nach dem Messfall | Zähler `meas/adv/conn/led_ms`, `charge_uc`, Resetgrund, `vdd_min` gegen Messung (ENERGIEMESSUNG Kap. 1 „Gegenprobe“) |

Die Serienfirmware liefert `meas/adv/conn/led_ms`, `charge_uc` und `reset_reason` bereits in GET_INFO (5.5); neu durch
TF-4 sind VDD-Minimum, Flash-Operationen, Retention-Register und `backoffs`.

### 7.1 TF-3: Ruhestrom-Mehrbedarf (zu dokumentieren, Anhang A)

Mit SENS_PWR dauernd high sind TMP1075N, C24 und R4/R5 versorgt; SDA/SCL sind hochohmig ohne Pull (R4/R5 ziehen
auf SENS_PWR, kein Querstrom). Erwarteter Mehrbedarf ohne Leck: TMP1075N im Shutdown **0.15 µA typ / 0.35 µA max**
(`TI_TMP1075_Datasheet_SBOS854F.pdf` S. 7 Tab. 6.6, IDD_SD, serial bus inactive); bis zum ersten One-Shot nach dem Start
(< 1 s) läuft der TMP im Dauerbetrieb (IDD_AVG 4.8 µA typ, ebd.). Der Wandlungsstrom des TMP1075N ist in Tab. 6.6 nicht
angegeben → Mittel aus Aufbau D.

**Kriterium als Änderung am selben Muster (W-3 Elektronik Phase 6):** Ein Absolutvergleich „Differenz − 0.35 µA“ ist zu
eng: IDD_SD gilt nur bei 25 °C (ebd. Kopfzeile, temperaturabhängig Abb. 6-5), und der Eingangsleckstrom des TMP1075N darf
bis IIN ≤ 1 µA je Pin betragen (ebd. Tab. 6.6; SDA/SCL liegen über R4/R5 auf V+), dazu der Pad-Leckstrom DIO16/17 – ein
datenblattkonformes Muster darf ohne jedes Feuchteleck bis ≈ 2.35 µA Mehrstrom zeigen. Darum:

1. **Referenz t0** nach dem Verguss, **vor** den Klimazyklen, bei 25 °C: E1 (Aufbau C) mit Serienfirmware und mit TF-3
   am selben Muster; Δ(t0) = I(TF-3) − I(Serie).
2. **Nach den Klimazyklen** am selben Muster bei 25 °C (≥ 2 h akklimatisiert, Feuchtezustand wie im Testplan): Δ(nach).
3. **Leck SENS_PWR–GND = Δ(nach) − Δ(t0)**, Kriterium PT11.19 ≤ 1 µA (ANNAHME).
4. **Auswertung nur im flachen Abschnitt** zwischen den Ereignissen: ≥ 2 s nach einem Ereignis (Wecken, I²C, Ringspeicher
   jede Minute; Nachladen über den 1-kΩ-Shunt τ ≈ 0.4 s) und ≥ 2 s vor dem nächsten, Oszilloskop mit Mittelung; Fenster,
   die ein Ereignis enthalten, verwerfen.

Für die Ruhestrommessung das Gateway ausschalten: sonst verbindet es wegen `DATA_PENDING` etwa einmal je Minute
(≈ 1440 × 299 µC/Tag ≈ 5 µA, PROTOCOL 12, ANNAHME).

TF-3 weicht bewusst von FW-1 ab (I²C-Leitungen während der Feuchtemessung auf SENS_PWR statt low; TMP versorgt):
Feuchtewerte unter TF-3 sind nur informativ.

## 8 Auswertung und Prüfung ohne Hardware

```sh
.venv/bin/python scripts/testfw_eval.py diag --file diag.hex --expect tf2-late     # Exit 0 = alle Kriterien ok
.venv/bin/python scripts/testfw_eval.py info <hex>
.venv/bin/python scripts/testfw_eval.py tf3 --db /var/lib/fluidi/fluidi.sqlite --sensor fl-tf3-ABCD
.venv/bin/python scripts/testfw_eval.py --sim diag --expect tf2-late               # synthetisch
make -C firmware/sensor test                                                       # Host-Tests inkl. TF
```

Ergebnis 2026-11-09 nach den Phase-6-Befunden (`make check`): Layout/Pins ok; Serie 1589 Prüfungen (davon 19 `[fault]`,
8 `[assert]`, 20 `[latch]`/`[early]`), TF-1 24, TF-2 77, TF-3 25, TF-4 14 Prüfungen bestanden; `test_testfw_eval.py` 13 Tests (davon 5 gegen die echten
GET_DIAG/INFO/Datensatz-Nutzlasten des C-Kerns aus `tests/build/tf<n>_*.hex`), Flash-Werkzeug 23 (davon 6 neu: Testfirmware-Erkennung), Kopplungsangriff 3.
Phase-6-Prüfbefunde (C-1, W-1, W-2): siehe Kap. 9 O-8 bis O-10.

## 9 Offen / PROTOTYP-PRÜFUNG

| Nr | Punkt | Wer |
|---|---|---|
| O-1 | ~~GET_DIAG/GET_INFO am Gateway abrufbar machen~~ erledigt 2026-11-09: `POST /sensors/{id}/diag`, PWA „Diagnose“, Kap. 6a. **PROTOTYP-PRÜFUNG:** 72-Byte-INFO bzw. bis 205-Byte-DIAG passen in einen SECURE-Frame (MTU 247); bei kleinerer ausgehandelter MTU am Muster prüfen | Software |
| O-2 | Startsignal und Sequenz-Zeiten (100 ms, 2 s) sind ANNAHMEN; Muster in PROTOCOL 10.2 festlegen | Firmware/Orchestrator |
| O-3 | ~~Gateway/PWA zeigen `fw_build` nicht an~~ erledigt 2026-11-09 (Kap. 3, GATEWAY_API 5.10) | Software |
| O-4 | Konvention `fw_build` = `9<n><bb>` statt Text-Suffix „-tf<n>“ (Anhang A) bestätigen | Orchestrator |
| O-5 | **Erledigt 2026-11-09 (Prüfung offen):** Befund bestätigt – HardFault/NMI/nicht registrierter Interrupt sprangen in `Exception_handlerSpin` (SDK `kernel/freertos/exception/ExceptionArmV6M.c` Z. 67–72: Interrupts aus, Endlosschleife) → Watchdog nach bis zu 10 min, Grund „watchdog“. Neu: SysConfig `/freertos/exception` `nmiHandler`/`hardFaultHandler`/`defaultHandler` = Custom `fl_fault_handler` (`platform/cc23/fl_hw.c`): PMCTL.AONRCLR1 = `FL_RET_PLANNED`, AONRSET1 = `FL_RET_FAULT` (Bit 13), `PMCTLResetSystem` (RSTCTL.SYSRST; TRM SWCU193A 6.11.10 S. 349, 6.11.14/15 S. 353–354, 8.4.2 S. 460); kein Flash, kein Stack. `fl_app_init` meldet SYSRST + Bit als `reset_reason` 5 (hardfault), zählt abnormal (F-W3: 3 → Abschaltung). **Nachtrag:** BLE-Stack-Asserts (alle Ursachen), out of memory und FreeRTOS-Stacküberlauf (SDK `main_freertos.c` Z. 157–161, 199–274: `HAL_ASSERT_SPINLOCK`) nehmen denselben Weg (`platform/cc23/fl_assert.c`). **Bleibt (dokumentiert, nicht geändert):** MCUboot-`faultISR`/`nmiISR` (NoRTOS-Startup, Schleife → MCUboot-Watchdog 60 s); SDK-Schleifen ohne Assert-Weg (`util.c` Z. 306 bei `mq_open`-Fehler, `nvocmp.c` `NVOCMP_ASSERT1`) → Watchdog 10 min | Firmware |
| O-6 | PROTOTYP-PRÜFUNG: Watchdog-Neustart nach ≤ 10 min trotz laufendem BLE-Stack (TF-1); `__builtin_trap` erzeugt HardFault und `fl_fault_handler` startet **sofort** neu (TF-2 9 ×, Grund hardfault, kein Watchdog-Eintrag 0x50); Retention-Bits 7–17 überleben Reset und Shutdown (TRM 8.4.2); TMP1075N bleibt bei dauernder Speisung im Shutdown zwischen One-Shots | Prüfer am Muster |
| O-7 | Kein UART-Log: Anhang A verlangt keines; DIO6/DIO20 sind LED-Pins und nach dem Verguss nicht erreichbar | – |
| O-8 | **C-1 (Elektronik Phase 6), umgesetzt:** IO-Latches nach dem Wecken aus Shutdown werden freigegeben (`fl_platform_early_init`: RSTSTA festhalten, Pins setzen, `fl_app_early` → `PowerLPF3_releaseLatches`); vorher blieben LEDs/Messkette eingefroren und spätere Neustarts wurden als POWER_ON erkannt (TF-2 ab der 2. Runde falsch NOK). **PROTOTYP-PRÜFUNG:** Unterspannungs-Abschaltung (bzw. TF-2-Abschaltung) auslösen, per Taster wecken: L11 sichtbar, Messung gültig; danach `REBOOT` → `reset_reason` = software (nicht power_on); TF-2 zweimal hintereinander ohne Zellwechsel → beide Runden `tf2_cycles` = 3 | Prüfer am Muster |
| O-9 | **W-1 (Elektronik Phase 6), PROTOTYP-PRÜFUNG mit TF-4:** Überlebt das Retention-Register (REG3V3) einen **VDDS-Brownout**? TRM SWCU193A S. 265 Kap. 6.8 („only reset on POR“) widerspricht S. 419 Tab. 8-1 („retention: None“). Vorgehen: Labornetzteil über die Dummy-Scheibe, Retention-Bit setzen (TF-2-Auslöser 5 × oder `REBOOT` → PLANNED), VDD langsam 3.0 V → 1.60 V (unter BOD 1.67 V, über POR 1.45 V; DS S. 19 Tab. 7.6) → 3.0 V; dann GET_DIAG: TF-4 `ret_boot` (Byte 26) und `reset_reason` (Byte 24). Erwartung bei Erhalt: `ret_boot` ≠ 0, Grund brownout; fällt REG3V3 weg (`ret_boot` = 0), zählt F-W3 Brownout-Schleifen nicht → Entscheid Firmware/Sicherheit (NV-Zähler gedrosselt oder Schreiben nach Brownout aufschieben) | Prüfer am Muster |
| O-10 | **W-2 Elektronik / W-1 Sicherheit (Phase 6), umgesetzt:** Neustartgrund und Reset-Schleifen-Zähler werden in `fl_app_early` (aus `fl_platform_early_init`, **vor** `BLEAppUtil_init`) ausgewertet; 3 abnormale Starts → Abschaltung ohne Flash, auch wenn der Fehler in der Stack-Initialisierung liegt (Host-Test `test_early`). **PROTOTYP-PRÜFUNG (PT11.07b):** am Muster nur mit eigener Auslösung vor `stack_ready` prüfbar; TF-2 hat dafür keinen freien Modus (2-bit-Feld 1–3 belegt, Retention-Bits 7–12/14–17 voll) → offen. Vorschlag: am offenen Muster (S2, Weg B, vor dem Verguss) mit SWD-Debugger Haltepunkt in `BLEAppUtil_init` und `__builtin_trap` erzwingen, 3 × wiederholen; Kriterium Abschaltung beim 3. Start, BLE-NV-Seiten (0x77800, 2 × 4 kB) vorher/nachher gleich, `flash_ops` 0 | Firmware/Prüfer |
