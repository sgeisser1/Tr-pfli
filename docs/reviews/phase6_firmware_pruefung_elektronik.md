# Phase 6 – Prüfung Firmware-Änderungen gegen die Hardware (Prüfer: elektronik)

| | |
|---|---|
| Datum | 2026-11-09 |
| Prüfer | Elektronik-Agent, frischer Kontext |
| Stand | `f047cf5` (main, sauber); Prüfgegenstand `git log b2c05d9..HEAD -- firmware/sensor`: `4f2f32d` (TF-1…TF-4), `eb2a5ff` (O-5 Ausnahmevektoren), `21cef8d` (Assert/Stacküberlauf) |
| Grundlagen | `docs/interfaces/PINMAP_SENSOR.md` (Rev B/C), `hardware/sensor/gen/parts.py`, `docs/reviews/phase5_testplan_prototyp.md` Anhang A, `docs/manuals/TESTFIRMWARE.md`, `docs/manuals/ENERGIEMESSUNG.md` |
| Datenblätter (lokal) | TRM `docs/datasheets/TI_CC23xx_TechnicalReferenceManual_SWCU193A.pdf` (= [TRM]), `docs/datasheets/TI_CC2340R5_Datasheet_SWRS272F.pdf` (= [DS]), `docs/datasheets/TI_TMP1075_Datasheet_SBOS854F.pdf` (= [TMP]); SDK 9.23.00.27 (`~/fluidi-tools/ti/simplelink_lowpower_f3_sdk_9_23_00_27`) |

## 1 Selbst ausgeführt

| Was | Ergebnis |
|---|---|
| `make` und `make check` im Repo (`source ~/fluidi-tools/env.sh`, seriell) | RC 0; nichts neu übersetzt (Stand aktuell) |
| **Sauberer Neubau** aus `git archive HEAD` im Scratchpad: `make`, `make TESTFW=1..4`, `make check` | alle RC 0. Host-Tests: Serie 1569, TF-1 24, TF-2 77, TF-3 25, TF-4 14 Prüfungen bestanden; `test_testfw_eval.py` 13, `test_flash_sensor.py` 17, `test_pairing_mitm.py` 3 OK. Größe Serie: Slot 0 90 %, RAM 91 % (Reserve 3198 B ≥ 2 kB). `check_fault_vectors.py` in allen 5 Builds [ok]. **1 Compiler-Warnung** in allen Builds: `fl_hw.c:529: function declared 'noreturn' should not return` (K-1) |
| Serie bit-gleich durch TF-Einführung? Neubau `b2c05d9` und `4f2f32d` aus `git archive`, `cmp` von `build/app/fluidi_sensor_noheader.bin` | **identisch** (206 956 B); MCUboot-Hex `b2c05d9` = `4f2f32d` = `HEAD` identisch |
| Disassemblierung `fl_fault_handler`, `PMCTLResetSystem`, `AssertHandler`, `vApplicationStackOverflowHook` (`tiarmobjdump`, Serie HEAD) | `ldr r0,=0x40000040; movs r1,#0x10; str r1,[r0,#4]` (AONRCLR1 = 0x10) ; `movs r1,#1; lsls r1,#13; str r1,[r0]` (AONRSET1 = 0x2000); `bl PMCTLResetSystem` = `cpsid i; ldr r0,=0x4000002C; ldr; orrs #1; str; b .`. Kein `push`, kein `sp`. Assert/Stacküberlauf = je nur `bl fl_fault_handler` |
| Vektortabelle `.resetVecs` (Serie HEAD) | Index 2–10, 12, 13, 16 ff. → `fl_fault_handler`; 11 `vPortSVCHandler`, 14 `xPortPendSVHandler`, 15 `xPortSysTickHandler` (FreeRTOS unverändert) |
| `diff` SDK `examples/.../Startup/main_freertos.c` ↔ `platform/cc23/fl_main.c` | Z. 1–147 identisch, nur Kommentar ergänzt; AssertHandler/StackOverflowHook entfernt (→ `fl_assert.c`) |
| SDK-`grep` nach `AONRSET1/AONRCLR1/AONRSTA1` | ausserhalb `hw_pmctl.h`/SVD nur CC27xx-Treiber → kein CC23x0-Treiber und kein MCUboot benutzt REG3V3 |
| SDK-/Projekt-`grep` nach `SLPCTL`, `SLPN`, `PowerLPF3_releaseLatches` | **nirgends aufgerufen** (nur Definition `PowerCC23X0.h` Z. 446 und SDK-Beispiel `gpioshutdown.c` Z. 63–69) → Befund **C-1** |

## 2 Ergebnis je Prüffrage

### 2.1 Testfirmware TF-1…TF-4 gegen Schaltplan/PINMAP

- **Pins** (`config/fluidi_board.h` ↔ PINMAP Kap. 1 ↔ `gen/parts.py`): SENS_PWR DIO12 (Pin 5), SDA DIO16 (Pin 7), SCL DIO17 (Pin 8),
  OSC_EN_N DIO11, LEDs DIO6/13/20, Taster DIO21 – stimmen. U3 TMP1075NDRLR: Netzliste `{6: SDA, 1: SCL, 3: NC, 4: GND, 2: GND, 5: SENS_PWR}`
  = [TMP] S.4 Tab. 5-1 (SOT563: SCL 1, GND 2, ALERT 3, A0 4, V+ 5, SDA 6); A0 = GND → 0x48 wie `FLUIDI_TMP1075_I2C_ADDR`.
  R4/R5 4.7 kΩ SENS_PWR→SDA/SCL, C24 100 nF an SENS_PWR (`parts.py` Z. 199–203). ALERT offen ist zulässig (Open-Drain-Ausgang).
- **TF-3 elektrisch korrekt:** SENS_PWR dauernd high (High-Drive-Ausgang), SDA/SCL `GPIO_CFG_NO_DIR` = Ein- und Ausgangspuffer aus, kein Pull
  (SDK `GPIO.h` Z. 393). R4/R5 ziehen beide Leitungen auf SENS_PWR ≈ VDD → **kein Querstrom** über R4/R5 (wäre bei „Ausgang low“
  VDD/4.7 kΩ ≈ 0.64 mA je Leitung bei 3.0 V). Kein Pfad im Rev-B-Code schaltet SENS_PWR ausserhalb von TF-3 zurück (die
  `GPIO_write(SENS_PWR, 0)` in der Messkette Z. 289 ist nur `HW_REV=A`). In `fl_port_shutdown` setzt TF-3 vor dem Shutdown
  wieder SENS_PWR low und SDA/SCL low (Serienzustand FW-8) – richtig, Reihenfolge SENS_PWR zuerst. TMP1075N wird nach jeder
  Lesung mit 0x81 (OS = 1, SD = 1) in Shutdown versetzt, auch durch die Serienmessung beim Start.
  V+ = VDD ≤ 3.6 V ([TMP] S.7 Tab. 6.6) bei Zelle/Netzteil 3.0 V eingehalten.
- **Ruhestrom-Messung TF-3** grundsätzlich sinnvoll (Aufbau C misst Standby zwischen Ereignissen), aber Auswertung „Differenz −
  0.35 µA = Leck“ ist zu eng → Befund **W-3**.
- **TF-1:** Endlosschleife im Anwendungstask, CPU dauernd aktiv: 2.6 mA typ ([DS] S.19 Tab. 7.9, CoreMark 48 MHz, DCDC) × 600 s
  ≈ 1.6 C ≈ 0.43 mAh – energetisch unkritisch. Unterspannungsüberwachung läuft in dieser Zeit nicht (App-Task blockiert) → K-3.
- **Retention-Bitbelegung** gegen [TRM] S.352–354 (6.11.13–15, `FLAG` Bit 17–0, W1S/W1C) und S.460 (8.4.2, „18b assigned to user“):
  Bit 0–3 ABN, 4 PLANNED, 5 UV, 6 BACKOFF, 7–8 TF-Modus (0x180), 9–12 TF-max (0x1E00), 13 FAULT (0x2000), 14–15 TF-cyc (0xC000),
  16–17 TF-sd (0x30000): **lückenlos, ohne Überlappung, alle innerhalb `PMCTL_AONRSTA1_FLAG_M = 0x3FFFF`** (SDK `hw_pmctl.h` Z. 650).
  Adressen PMCTL_BASE 0x40000000 + 0x3C/0x40/0x44 = [TRM] Offsets (S.352–354). `fl_port_retained_set` (CLR ~v, dann SET v) korrekt.

### 2.2 Fault-/Assert-Pfad

- Registeradressen und Bitsemantik **korrekt** (siehe Disassemblierung Kap. 1): AONRCLR1 0x40000044 ← 0x10 (PLANNED löschen),
  AONRSET1 0x40000040 ← 0x2000 (FAULT setzen), RSTCTL 0x4000002C |= SYSRST (Bit 0) = [TRM] S.349 Tab. 6-82. Ergebnis
  RSTSTA = SYSSRC 4 / RESETSRC 6 = `PMCTL_RESET_SYSTEM` → `FL_RR_SOFTWARE` → mit FAULT-Bit `FL_RR_HARDFAULT`.
- **Überlebt FAULT den Systemreset?** Ja: [TRM] S.265 Kap. 6.8 „AON Register Bank … directly supplied by VDDS and only reset on POR …
  retained in shutdown and across all resets, except POR“; [TRM] S.420 Tab. 8-1 „System reset request (SYSSRC 4) … REG3V3 registers
  retained“, ebenso CPU-Lockup (SYSSRC 2), Watchdog (3), Pin-Reset, VDDR-Brownout (S.419).
- **Lockup im Handler / zerstörter Stack:** Handler nutzt keinen Stack; scheitert schon das Hardware-Stacking → Lockup → Systemreset
  LOCKUP ([TRM] S.420 Tab. 8-1 SYSSRC 2) → `fl_port_reset_reason` = `FL_RR_HARDFAULT`. Korrekt.
- **Brown-out während des Pfads:** Fenster vom Eintritt bis SYSRST ≈ 10 Befehle (< 1 µs bei 48 MHz). (a) VDDR-Brownout: REG3V3
  bleibt, Grund `FL_RR_BROWNOUT` (abnormal), FAULT-Bit wird beim nächsten Start mit `newret` gelöscht → konservativ, richtig.
  (b) VDDS-Brownout (1.67 V fallend, [DS] S.19 Tab. 7.6): Grund `FL_RR_BROWNOUT`, ebenfalls abnormal. **Aber** [TRM] Tab. 8-1
  S.419 nennt für VDDS-Brownout „Memory/state retention: None“ im Widerspruch zu Kap. 6.8 → Befund **W-1** (betrifft weniger den
  Handler als die Brownout-Zählung allgemein).
- Vektortabelle, `AssertHandler`, `vApplicationStackOverflowHook`: korrekt, vom Build geprüft und von mir nachvollzogen. Die
  SDK-Empfehlung für `HAL_ASSERT_CAUSE_LL_INIT_RNG_NOISE_FAILURE` („Power_reset() MUST be called“) ist durch den Systemreset erfüllt.
- **Lücke:** Fehler vor `fl_app_init` (Board_init, BLE-Stack-Init) → Befund **W-2**.

### 2.3 Serie unverändert ausser O-5/Assert?

**Ja.** `b2c05d9` → `4f2f32d` Serienbinärdatei bit-gleich (selbst gebaut und verglichen). `4f2f32d` → `HEAD` ungeschützte
Änderungen nur: `FL_RET_FAULT` (fl_app.h), Umsetzung SOFTWARE+FAULT → HARDFAULT (fl_app.c Z. 765–766), `fl_fault_handler`
(fl_hw.c), SysConfig-Modul `/freertos/exception` (NMI/HardFault/Default „Custom“), `fl_main.c` + `fl_assert.c` statt SDK-
`main_freertos.c` (app.mk), `check_fault_vectors.py` im Ziel `size`. `TF_COUNT(c)` ist in der Serie `((void)0)`. Alles Übrige
steht unter `#if FLUIDI_TESTFW`. Makefile verhindert TESTFW mit Nicht-DEV-Schlüssel und `release` mit TESTFW, Serien-Build-
Nummern ≥ 9000 gesperrt.

## 3 Befunde

### C-1 kritisch – IO-Latches werden nach dem Wecken aus Shutdown nie freigegeben (Serienfirmware, vorbestehend; trifft TF-2 und F-W3)

**Befund.** Nach Shutdown bleiben alle I/Os verriegelt: [TRM] S.261 Kap. 6.4.2 „The device goes through a full boot when exiting
shutdown, but I/Os remain latched“; [TRM] S.343 Tab. 6-76 `PMCTL.SLPCTL.SLPN`: „The boot code will set this bit … automatically
**unless waking up from a SHUTDOWN (RSTSTA.SDDET is set)**. Application software must reconfigure the state for all IO's before
setting this bit“. [TRM] S.350 Tab. 6-83: `SDDET`/`IOWUSD` „will be cleared when SLPCTL.SLPN is asserted“. SDK: `PowerLPF3_releaseLatches()`
(`PowerCC23X0.h` Z. 433–449) wird von keinem Treiber aufgerufen; das SDK-Beispiel `examples/rtos/LP_EM_CC2340R5/drivers/gpioshutdown/gpioshutdown.c`
Z. 66–69: „Application code must always disable the IO latches when coming out of shutdown“. In `firmware/sensor` (und MCUboot)
gibt es **keinen** Zugriff auf `SLPCTL` bzw. `releaseLatches` (grep).

**Folgen** nach jedem Wecken per Taster aus Unterspannungs- oder Reset-Schleifen-Abschaltung (`fl_port_shutdown`):
1. Ausgänge bleiben im Shutdown-Zustand eingefroren: LEDs aus (high), DIO11 high (Messkette aus), SENS_PWR low, SDA/SCL low →
   **keine Feuchte- und Temperaturmessung, keine LED-Anzeige**, bis zum Power-on (Zellwechsel). Funk und Taster (Eingang
   transparent) laufen weiter → Sensor wirkt verbunden, liefert aber nur Fehlwerte.
2. `SDDET`/`IOWUSD` bleiben stehen, auch über spätere Systemresets (Boot-Code setzt SLPN nicht, solange SDDET gesetzt ist).
   Dann ist `RSTSTA` z. B. `0x30046` statt `0x46` → `fl_port_reset_reason` (Gleichheitsvergleich) liefert **`FL_RR_POWER_ON`** für
   Watchdog, Absturz, Software-Reset usw. → Zähler abnormaler Neustarts wird genullt (F-W3 wirkungslos), `FL_RET_FAULT` wird
   ignoriert, `charge_uc` wird genullt (S-5).
3. **TF-2 (PT11.07):** Erste Runde (5 ×) endet korrekt mit Taster-Wecken. Ab der zweiten Runde (7 × / 9 ×) meldet der erste fatale
   Neustart `POWER_ON` → `fl_tf_boot` wertet ihn als Testende → `tf2_cycles` = 1 statt 3 → `testfw_eval.py --expect` schlägt
   fehl, obwohl die Serienreaktion (nach Behebung) richtig wäre. Ausserdem fehlt das Startsignal (LEDs eingefroren).

Die Host-Simulation (`tests/port_sim.c`) bildet das nicht nach, daher bestehen alle Tests.

**Vorschlag.** In `fl_platform_early_init` (vor dem ersten Ändern der Pins): `RSTSTA` **einmal** lesen und in einer statischen
Variablen ablegen; `pins_sleep_state()` ausführen; dann `PowerLPF3_releaseLatches()` (SDK) aufrufen. `fl_port_reset_reason()`
liefert danach den gespeicherten Wert (wird in `fl_app_init` zweimal aufgerufen, Z. 763 und Z. 830 – beide müssen den
gespeicherten Wert sehen, weil das Freigeben `SDDET/IOWUSD` löscht, `PowerCC23X0.h` Z. 439–441). Host-Test um „Latch nach
Shutdown-Wecken“ ergänzen (Sim: Ausgänge gesperrt bis Freigabe, RSTSTA-Bits klebend). **PROTOTYP-PRÜFUNG:** am Muster
Unterspannungs-Shutdown auslösen, per Taster wecken, prüfen: L11 sichtbar, Messung gültig, danach `REBOOT` → `reset_reason` =
Software (nicht Power-on).

### W-1 wichtig – REG3V3 bei VDDS-Brownout laut TRM widersprüchlich; Brownout-Schleifen evtl. nicht gezählt

**Befund.** [TRM] S.265 Kap. 6.8: REG3V3 „only reset on POR“. [TRM] S.419 Tab. 8-1: VDDS-Brownout (RESETSRC 2) „Memory/state retention:
**None**“ (Pin-Reset und VDDR-Brownout dagegen ausdrücklich „REG3V3 registers retained“). Gilt die Tabelle, gehen bei einem
VDDS-Brownout **alle** Retention-Bits verloren (ABN-Zähler, UV, BACKOFF, FAULT, TF-Bits). Dann startet jede VDDS-Brownout-Folge
mit `abn = 1`; die Reset-Schleifen-Abschaltung (F-W3, ≥ 3) greift für Brownout-Schleifen nie. Schutz bleibt nur die
Ruhespannungsschwelle `UV_RECOVER_MV` 2.6 V nach Brownout (fl_app.c Z. 37, 785). Eine Schleife mit gesunder Ruhespannung, aber
Einbruch unter Last (kalte Zelle, hoher R_int) schreibt bei jedem Start Diag/Zähler ins Flash (Verschleiss) und verbraucht Energie.
Für den Fault-Handler selbst ist das unkritisch (Fenster < 1 µs; Ergebnis „Brownout“ = ebenfalls abnormal).

**Vorschlag.** (1) Kommentare in `fl_app.h` Z. 38 und `fl_hw.c` Z. 460 auf „überlebt Reset, Shutdown, VDDR-Brownout; VDDS-
Brownout unklar (TRM 6.8 vs. Tab. 8-1)“ ändern. (2) **PROTOTYP-PRÜFUNG** mit TF-4 (liefert `ret_boot`): Labornetzteil, ein
Retention-Bit gesetzt (z. B. per TF-2-Auslöser oder geplantem Neustart), VDD langsam von 3.0 V auf 1.60 V (unter BOD 1.67 V,
über POR 1.45 V, [DS] S.19 Tab. 7.6) und zurück → `ret_boot` und `reset_reason` lesen. (3) Fällt REG3V3 dabei weg: Brownout-
Zähler zusätzlich gedrosselt im NV führen (nur nach bestandener Lastmessung, N-2) oder nach Brownout das Flash-Schreiben im
Start bis 10 min stabil aufschieben. Entscheid Firmware/sicherheit.

### W-2 wichtig – Absturz/Assert vor `fl_app_init` ergibt schnelle Endlos-Resetschleife ohne Abschaltung

**Befund.** `FL_RET_FAULT` wird nur in `fl_app_init` ausgewertet und gezählt; dieses läuft erst nach Board_init und BLE-Stack-Init
(`fl_ble.c` Z. 247–253: `appMain` → `fl_platform_early_init` → `BLEAppUtil_init` → … → `fl_platform_start_app`). Ein
deterministischer Fehler davor (z. B. Stack-Assert bei beschädigtem BLE-NV, Speichermangel, RNG-Fehler) → `fl_fault_handler` →
Systemreset → MCUboot (Signaturprüfung des ganzen Images) → wieder Fehler … ohne Zähler, ohne Abschaltung, CPU fast dauernd aktiv
(Grössenordnung mA, ANNAHME; 2.6 mA typ aktiv [DS] S.19 Tab. 7.9). Vorher (Spin + MCUboot-Watchdog 60 s) war der Strom ähnlich –
**keine Verschlechterung**, aber die O-5-Aussage „Abschaltung nach 3 abnormalen Neustarts“ gilt nur für Fehler nach `fl_app_init`.

**Vorschlag.** Auswertung Neustartgrund/Retention (Teil 1 von `fl_app_init`, ohne Flash) an den Anfang von `main()` bzw. in
`fl_platform_early_init` **vor** `BLEAppUtil_init` verlegen, inkl. Abschaltung bei `abn ≥ 3` (Pins in Ruhe, Shutdown mit
Tastenwecken). Alternativ den ABN-Zähler im Handler selbst registerweise erhöhen (kein Stack nötig) und früh im `main()`
prüfen. Host-Test: Fehler vor Init dreimal → Abschaltung.

### W-3 wichtig – TF-3-Leckauswertung (PT11.19) kann bei datenblattkonformen Bauteilen falsch NOK ergeben

**Befund.** `TESTFIRMWARE.md` Kap. 7.1: „Differenz − 0.35 µA = Leck SENS_PWR–GND (Kriterium ≤ 1 µA)“. Dabei:
(a) `IDD_SD` 0.15/0.35 µA gilt nur bei **TA = 25 °C** ([TMP] S.7 Tab. 6.6, Kopfzeile „At TA = 25 °C“; temperaturabhängig, [TMP]
Abb. 6-5). (b) Mit SENS_PWR high liegen SDA/SCL über R4/R5 auf V+; der Eingangsleckstrom des TMP1075N ist mit **IIN ≤ 1 µA**
je Pin spezifiziert ([TMP] S.7 Tab. 6.6), dazu der Pad-Leckstrom von DIO16/17 des CC2340. Ein datenblattkonformer TMP darf damit
bis ≈ 2.35 µA Mehrstrom ohne jedes Feuchteleck haben (Grenzwerte, typisch nA). (c) Die TF-3-Ereignisse je Minute (Wecken, I²C,
Ringspeicher-Schreiben) laden über den 1-kΩ-Shunt von Aufbau C nach (τ ≈ 1 kΩ · 400 µF = 0.4 s); wer über ein Fenster mittelt,
das ein Ereignis enthält, misst sie mit (Grössenordnung 0.1 µA, ANNAHME). Weil PT11.19/A-3 über die Serie entscheidet, ist ein
falsches NOK teuer.

**Vorschlag.** Kriterium auf eine **Änderung** umstellen: am selben Muster Referenzmessung TF-3 minus Serie **nach dem Verguss,
vor den Klimazyklen** (t0), bei 25 °C; nach den Zyklen erneut bei 25 °C (Muster ≥ 2 h akklimatisiert und abgetrocknet bzw.
definiert feucht, wie im Plan); Leck = Δ(nach) − Δ(t0) ≤ 1 µA (ANNAHME bleibt). Auswertung nur im flachen Abschnitt ≥ 2 s nach
einem Ereignis und ≥ 2 s vor dem nächsten (Aufbau C, Oszilloskop mit Mittelung). Text in `TESTFIRMWARE.md` 7.1 und PT11.19
nachführen.

### K-1 klein – Compiler-Warnung `-Winvalid-noreturn` in `fl_fault_handler`

`fl_hw.c:529`: `fl_fault_handler` ist `noreturn`, `PMCTLResetSystem` (SDK) nicht. Der erzeugte Code ist richtig (`b .` in
`PMCTLResetSystem`), aber Builds sollen warnungsfrei sein. **Vorschlag:** nach dem Aufruf `for (;;) { }` ergänzen (bleibt
stackfrei; `check_fault_vectors.py` erlaubt Rückwärtssprung im Handler prüfen/anpassen) oder `__builtin_unreachable()`.

### K-2 klein – `sleep_ms(15)` kann kürzer als tCONV max 15 ms sein (Serie und TF-3)

`configTICK_RATE_HZ` = 1000 (`build/app/FreeRTOSConfig.h` Z. 99); `vTaskDelay(15)` wartet 14–15 ms, [TMP] S.7 Tab. 6.6 tCONV
max 15 ms. Folge: gelegentlich wird der vorherige Wert gelesen (kein Fehler, aber in TF-3 um 60 s veraltet, in der Serie um ein
Messintervall). **Vorschlag:** `FLUIDI_TMP_CONV_MS` 16 (oder `sleep_ms(ms + 1)`).

### K-3 klein – TF-1: während der Endlosschleife keine Unterspannungsüberwachung

App-Task blockiert, `check_battery` läuft nicht; BLE-Advertising läuft weiter. Bei schwacher Zelle kann statt des
Watchdog-Resets ein Brownout eintreten (`reset_reason` 3 statt 2) und PT5.12 falsch NOK werden. **Vorschlag:** in
`TESTFIRMWARE.md` PT5.12 mit frischer Zelle oder Netzteil 3.0 V durchführen; Grund „Brownout“ als „Versorgung prüfen,
wiederholen“ werten.

### K-4 klein – `fl_port_retained_set` nicht atomar gegenüber Ausnahmen

Zwischen `AONRCLR1 = ~v` und `AONRSET1 = v` sind kurz alle Bits gelöscht; tritt genau dort eine Ausnahme ein, setzt der
Handler nur FAULT → ABN-Zähler verloren (Abschaltung einen Zyklus später). Fenster 1–2 Befehle, Aufrufe nur aus dem App-Kontext.
**Vorschlag:** erst SET (v), dann CLR (~v & alt), oder Interrupts für die zwei Schreibzugriffe sperren. Nur dokumentieren reicht.

## 4 Zusammenfassung

- Testfirmware: Pinbelegung, TF-3-Beschaltung (kein Querstrom über R4/R5, Serienzustand vor Shutdown), Retention-Bitbelegung
  (18 bit, ohne Überlappung) und Build-Trennung sind **korrekt**; Serie durch die TF-Einführung nachweislich bit-gleich.
- O-5-Fault-Pfad: Adressen, W1S/W1C-Semantik, Systemreset, Retention über SYSRST/Lockup/VDDR-Brownout **korrekt** und stackfrei.
- **C-1** (IO-Latch nach Shutdown nie freigegeben) ist vorbestehend in der Serienfirmware, macht aber nach jedem
  Taster-Wecken Messung/LEDs funktionslos, verfälscht Neustartgründe und lässt TF-2 ab der zweiten Runde falsch NOK enden →
  vor dem Flashen der Muster beheben. W-1…W-3 vor bzw. bei der Musterprüfung klären.

| Befund | Stufe | Antwort Ersteller |
|---|---|---|
| C-1 IO-Latches nach Shutdown | kritisch | umgesetzt |
| W-1 REG3V3 bei VDDS-Brownout | wichtig | umgesetzt (1, 2); (3) nach Messergebnis |
| W-2 Fehler vor `fl_app_init` | wichtig | umgesetzt |
| W-3 TF-3-Leckauswertung | wichtig | umgesetzt |
| K-1 noreturn-Warnung | klein | umgesetzt |
| K-2 tCONV 15 ms | klein | umgesetzt |
| K-3 TF-1 ohne UV-Überwachung | klein | umgesetzt |
| K-4 Retention-Schreiben nicht atomar | klein | umgesetzt |

## Antwort Ersteller (Firmware, 2026-11-09, Stand nach `42fb7cd`, nicht committet)

Nachweis: `make`, `make TESTFW=1..4`, `make check` seriell, alle RC 0, **keine Compiler-Warnung** mehr. Host-Tests Serie
1589 (vorher 1569; neu `[latch]` und `[early]`), TF-1 24, TF-2 77, TF-3 25, TF-4 14; `test_flash_sensor.py` 23,
`test_testfw_eval.py` 13, `test_pairing_mitm.py` 3. `check_fault_vectors.py` in allen 5 Builds [ok].

| Befund | Antwort | Umsetzung / Beleg |
|---|---|---|
| **C-1** | **umgesetzt** | `fl_platform_early_init` (`platform/cc23/fl_hw.c`): RSTSTA zuerst einmal lesen und speichern (`fl_port_reset_reason` gibt danach immer den gespeicherten Wert zurück), dann `GPIO_init`, `pins_sleep_state`, `BatteryMonitor_init`, dann `fl_app_early()` (`core/fl_app.c`). Dieses liest den Grund **vor** `fl_port_io_release()` = `PowerLPF3_releaseLatches()` (SDK `PowerCC23X0.h` Z. 446–449, schreibt SLPCTL 0x4000000C ← 1, im Disassemblat geprüft; TRM S. 343 Tab. 6-76, S. 350 Tab. 6-83). Die Freigabe läuft bei jedem Start; ohne vorherigen Shutdown hat der Boot-Code SLPN schon gesetzt. **MCUboot:** greift nicht auf die Latches zu (grep `SLPCTL`/`releaseLatches` im SDK-MCUboot und in `firmware/sensor/mcuboot`: keine Treffer) und darf es nicht: Sonst fielen DIO11/SENS_PWR/LEDs schon vor der Pin-Konfiguration der Anwendung in den Reset-Zustand (Glitch, TRM S. 343 „reconfigure … before setting“). Folge: Die rote Fehler-LED von MCUboot (`fluidi_led_debug.c`) bleibt im Start direkt nach einem Shutdown-Wecken unsichtbar; das ist hingenommen und dokumentiert. **Host-Test** `test_latch`: Die Simulation bildet nach, dass Ausgänge eingefroren bleiben und SDDET klebt (dann liefert jeder Systemreset POWER_ON). Geprüft: Grund vor der Freigabe gelesen, LED (L11) und Messung nach dem Wecken, danach Absturz → hardfault, REBOOT → software. Gegenprobe: Ohne den Aufruf schlagen 8 Prüfungen fehl. **PROTOTYP-PRÜFUNG:** Testplan PT11.07a, TESTFIRMWARE O-8 |
| **W-1** | **umgesetzt** (Punkte 1 und 2); Punkt 3 entscheidet sich nach dem Messergebnis | (1) Kommentare `fl_app.h` (Retention-Bits) und `fl_hw.c` (`fl_port_retained_*`): „VDDS-Brownout unklar (TRM S. 265 gegen Tab. 8-1 S. 419)“; die TRM-Stellen habe ich selbst nachgelesen. (2) PROTOTYP-PRÜFUNG mit TF-4 (`ret_boot`, `reset_reason`): TESTFIRMWARE O-9, Testplan PT11.07c. (3) NV-Zähler bzw. aufgeschobenes Schreiben erst, wenn die Messung den Verlust von REG3V3 zeigt (Entscheid Firmware/Sicherheit) |
| **W-2** | **umgesetzt** | Zählung und Abschaltung in `fl_app_early` (`core/fl_app.c`), aufgerufen aus `fl_platform_early_init` **vor** `BLEAppUtil_init` (`fl_ble.c` `appMain`), nur Register und Pins, kein Flash, keine RTOS-Dienste. Abnormale Neustarts (Watchdog, Brownout, hardfault/FAULT-Bit, ungeplanter Software-Reset) werden sofort im Retention-Register gezählt; beim 3. Start Abschaltung (BACKOFF, Tasterwecken). `fl_app_init` übernimmt das Ergebnis ohne Doppelzählung (ruft `fl_app_early` selbst nur auf, wenn es noch nicht lief, z. B. in den Host-Tests). Gegenüber dem Vorschlag „Handler erhöht den Zähler“ deckt das auch Watchdog- und Lockup-Neustarts vor der Initialisierung ab. **Host-Test** `test_early`: 3 Abstürze nur mit Frühstart → Abschaltung, 0 NV-, Flash-Schreib- und Löschvorgänge; Früh- plus Spätstart zählen einmal; Watchdog plus Absturz gemischt. FMEA F-67 (`phase5_fmea_light.md`). PROTOTYP-PRÜFUNG PT11.07b, TESTFIRMWARE O-10: TF-2 hat keinen freien Modus, daher Prüfung mit SWD am offenen Muster. `Power_shutdown` vor dem Scheduler ist erst am Muster belegt (Teil von PT11.07b) |
| **W-3** | **umgesetzt** | TESTFIRMWARE 7.1 und Kap. 7 sowie Testplan PT11.19: Leck = Δ(nach) − Δ(t0) am selben Muster, t0 nach dem Verguss vor den Zyklen, beide bei 25 °C; Auswertung nur im flachen Abschnitt (≥ 2 s nach bzw. vor einem Ereignis); Begründung mit IIN ≤ 1 µA und IDD_SD bei 25 °C ([TMP] S. 7 Tab. 6.6) |
| **K-1** | **umgesetzt** | `__builtin_unreachable()` nach `PMCTLResetSystem()` (das in `pmctl.h` Z. 171 mit `while (1)` endet). Code unverändert und stackfrei, Warnung weg |
| **K-2** | **umgesetzt** | `FLUIDI_TMP_CONV_MS` 16 (`config/fluidi_board.h`), gilt für Serie und TF-3 |
| **K-3** | **umgesetzt** | TESTFIRMWARE Kap. 7 PT5.12 und Testplan PT5.12: frische Zelle bzw. 3.0 V über die Dummy-Scheibe; Grund „brownout“ = Versorgung prüfen und wiederholen |
| **K-4** | **umgesetzt** | `fl_port_retained_set`: erst AONRSET1 = v, dann AONRCLR1 = ~v. Damit ist zu keinem Zeitpunkt ein Bit gelöscht, das bleiben soll |

