# fluidi Sensor Rev B – Pinplan CC2340R52E0RGER (Schnittstelle Hardware ↔ Firmware)

| | |
|---|---|
| Stand | 2026-11-07, Schaltplan **Rev B** (`hardware/sensor/fluidi_sensor.kicad_sch`), ersetzt Rev A. **Gilt unverändert für Rev C** (Pins/Netze gleich; Rev C: TP3 entfällt, Programmierpegel 2.0 V nach D-024; nachgeführt 2026-11-08, Phase 5) |
| Quelle der Netze | `hardware/sensor/gen/parts.py` (Generator), geprüft mit `check_netlist.py` gegen die KiCad-Netzliste |
| Grundlagen | D-018 (Messkette D3), D-019 / FLOORPLAN_OPTIONS Option (f) (TMP1075N im Sondenkragen, TS-1088), `docs/concepts/MESSKETTE_SALZ.md` Kap. 5, CONCEPTS 2.2/2.3/2.7, Phase-3-Review RGB 1.6, E3 (keine SWD-Pads) |
| Datenblatt | `docs/datasheets/TI_CC2340R5_Datasheet_SWRS272F.pdf` (DS), TRM `docs/datasheets/TI_CC23xx_TechnicalReferenceManual_SWCU193A.pdf` |

Firmware-Namen sind Vorschläge für `board.h`/SysConfig (`FLUIDI_PIN_*`). Änderungen nur gemeinsam mit Elektronik
(Schaltplan neu generieren, Tabelle nachführen).

## 0 Änderungen gegenüber Rev A (für die Firmware)

| Pin | Rev A | **Rev B** | Folge für die Firmware |
|---|---|---|---|
| 4 / DIO11 | `CREF2_CTL` (Cref2 100 pF) | **`OSC_EN_N`** – Gate P-FET Q2 (Messkette ein, **aktiv low**), 100 kΩ Pull-up R13 nach VDD | Cref2/f2-Messung entfällt. Ruhe: high bzw. hochohmig (R13 hält aus) |
| 5 / DIO12 | `SENS_PWR` für Oszillator **und** TMP1075 | `SENS_PWR` nur noch für **TMP1075N** (U3 im Sondenkragen) + C24 + I²C-Pull-ups R4/R5 | Last < 0.1 mA (statt bis 10 mA) |
| 12 / DIO24 | `OSZ_OUT` 2–6 MHz | **`MEAS_CLK` = f_osc / 8** (Teiler 3 × SN74LVC1G80) | f_osc = 8 × gezählte Frequenz; Bereich siehe Kap. 1 |
| – | TMP1075DGKR (VSSOP-8) | **TMP1075NDRLR** (SOT-563), Adresse unverändert **0x48** | tCONV One-Shot **10–15 ms** statt 4.5–7 ms |
| – | Taster TS-1187A | TS-1088-AR02016 | keine |

## 1 GPIO

| Pin | DIO | Netz | Funktion im Betrieb | Firmware-Name | Konfiguration | Besonderheiten (Quelle) |
|---|---|---|---|---|---|---|
| 4 | DIO11 | `OSC_EN_N` | Lastschalter Messkette: Gate von Q2 (AO3401A), Source VDD, Drain `OSC_PWR` → U2 SN74LVC1G14 (Oszillator) + U4–U6 SN74LVC1G80 (Teiler ÷8), C21/C25 | `FLUIDI_PIN_OSC_EN_N` | Ausgang; **low = Messkette an**, high = aus. Im Schlaf high oder Eingang ohne Pull (R13 100 kΩ hält Q2 aus) | Strom der Messkette ≈ 10 mA (MESSKETTE_SALZ Kap. 5) > DIO12-Spezifikation 10 mA (DS S.31, 7.21.4.1) → deshalb FET. Während „an“ fliessen 24–30 µA über R13. Q2 VGS(th) −0.5…−1.3 V, RDS(on) < 85 mΩ bei −2.5 V (`AOS_AO3401A_Datasheet_Rev3.1.pdf` S.2) → bei VDD ≥ 2.4 V voll durchgeschaltet. Im ROM-Bootloader SPI-CS-Eingang (TRM S.464): R13 hält die Kette aus |
| 12 | DIO24 | `MEAS_CLK` | Messfrequenz **f_osc / 8** → Timer-Capture/Zählung | `FLUIDI_PIN_MEAS_CLK` | Eingang, **kein Pull während der Messung**; bei Kette aus: Eingangspuffer aus oder Pull-down (U6-Ausgang ist dann hochohmig, Ioff, `TI_SN74LVC1G80_Datasheet_SCES221T.pdf` S.1) | Mux: T1C0 (2), **T3C0 (3)**, T0PE (4) (DS S.11 Tab. 6-1; Tab. 6-15, 6-18). Empfehlung **T3C0**. SPICE (`simulation/spice/README.md` (b), R3 1 kΩ): f_osc typ 27.4 (Luft) / 24.2 (trocken) / 14.9 (nass) / 9.8 MHz (Wasser) → MEAS_CLK typ **1.0–3.4 MHz**, alle Ecken/Zustände **0.59–4.51 MHz**; mit R3 10 kΩ (Umlötvariante) 0.07–0.65 MHz. Zählgrenze ≈ 10–12 MHz (**ANNAHME**, CONCEPTS 2.3). Reziprokzählung mit 48 MHz. Testpad TP4 (B-Seite) |
| 3 | DIO8 | `CREF1_CTL` | Cref1 22 pF (C22) zuschalten | `FLUIDI_PIN_CREF1` | Ausgang **low** = Cref1 wirkt; sonst Eingang hochohmig, **Eingangspuffer aus**, kein Pull | Ratiometrie C_Sonde = Cref1·T0/(T1−T0) − Cpar (CONCEPTS 2.3). Im ROM-Bootloader SPI-CLK-Eingang (TRM S.464), floatend (OP-K19). „Aus“-Kapazität ≈ C_pin 5–7 pF in Serie (DS S.32) |
| 5 | DIO12 | `SENS_PWR` | Speisung **TMP1075N** (U3, im Sondenkragen) mit C24 und I²C-Pull-ups R4/R5 | `FLUIDI_PIN_SENS_PWR` | Ausgang, High-Drive; Ruhe: **low** | VOH ≥ 2.47 V @ 10 mA (DS S.31). Last: TMP1075N IDD ≤ 10 µA aktiv (`TI_TMP1075_Datasheet_SBOS854F.pdf` S.7 Tab. 6.6) + Pull-up-Strom bei I²C-Low. Nach dem Einschalten ≥ 1 ms warten (C24 100 nF, **ANNAHME**, am Muster messen) |
| 7 | DIO16 | `I2C_SDA` | I²C SDA zum TMP1075N (Adresse **0x48**: A0 = GND, `TI_TMP1075_Datasheet_SBOS854F.pdf` S.14 Tab. 7-3) | `FLUIDI_PIN_I2C_SDA` | I2C0SDA (Mux 3); bei SENS_PWR aus: **Ausgang low** oder Eingang ohne Pull | Nach Reset SWDIO mit internem Pull-up (TRM S.22) → **früh im Boot SWD abschalten und Pull aus** (E3), sonst fliesst der Pull-up-Strom über R4 in den abgeschalteten TMP: bis **393 µA** (GPIO-Pull-up-Strom (Vpad = 0 V): 39–109 µA bei VDDS 1.8 V (`TI_CC2340R5_Datasheet_SWRS272F.pdf` S.31), **170–393 µA bei VDDS 3.8 V** (S.32, Tab. 7.21.4.1 Fortsetzung); Rechenwert = Wert bei 3.8 V) |
| 8 | DIO17 | `I2C_SCL` | I²C SCL | `FLUIDI_PIN_I2C_SCL` | I2C0SCL (Mux 3); sonst wie SDA | Nach Reset SWDCK mit Pull-down (TRM S.22) → abschalten (E3). I²C max. 400 kHz (DS S.31). Leitung ≈ 30 mm über die Innenlagen bis in den Kragen → 100 kHz empfohlen (**ANNAHME**, Kapazität im Layout prüfen) |
| 19 | DIO6 | `LED_R_UART_TX` | LED rot (Kathode über R6 470 Ω) | `FLUIDI_PIN_LED_R` | Ausgang; **low = an**, high = aus | Im ROM-Bootloader **UART TX** (TRM S.464 Tab. 8-38). Pad TP1 über R9+R10 (2 × 100 kΩ). PWM: T1C2 (Mux 3); UART0TXD (Mux 5) für Log |
| 6 | DIO13 | `LED_G` | LED grün (R7 200 Ω) | `FLUIDI_PIN_LED_G` | Ausgang, low = an | PWM: T0C0N (Mux 4). Im ROM-Bootloader SPI-PICO-Eingang |
| 9 | DIO20 | `LED_B_UART_RX` | LED blau (R8 100 Ω) | `FLUIDI_PIN_LED_B` | Ausgang, low = an | Im ROM-Bootloader **UART RX** (TRM S.464). Pad TP2 über R11+R12. Programmieren nur **ohne Zelle mit VDD 2.0 V und UART-Pegel 2.0 V** (D-024, `docs/manuals/PROGRAMMIEREN_SENSOR.md`; Behelf Labornetzteil höchstens 2.2 V; ersetzt „1.8 V“ aus Phase-3-Review 1.6). PWM: T1C0 (Mux 4) |
| 10 | DIO21 | `BTN_BOOT_N` | Taster SW1 (TS-1088) nach GND | `FLUIDI_PIN_BUTTON` | Eingang, **interner Pull-up**, Flanken-Wakeup | Bootloader-Trigger aktiv low (TRM S.465). Pull-up-Strom bei gedrücktem Taster bis **393 µA** (GPIO-Pull-up-Strom (Vpad = 0 V): 39–109 µA bei VDDS 1.8 V (`TI_CC2340R5_Datasheet_SWRS272F.pdf` S.31), **170–393 µA bei VDDS 3.8 V** (S.32, Tab. 7.21.4.1 Fortsetzung); Rechenwert = Wert bei 3.8 V) → nach > 30 s Dauerdruck Pull-up aus, zyklisch prüfen |
| 14 | DIO3_X32P | `X32P` | 32.768-kHz-Quarz Y2 | – | LFXT (Mux 6) | Last 2 × 15 pF (C14/C15), CL ≈ 9 pF (**ANNAHME** C_par 1.5 pF) |
| 15 | DIO4_X32N | `X32N` | 32.768-kHz-Quarz Y2 | – | LFXT (Mux 6) | – |

Freie DIO: **keine** (QFN24).

## 2 Versorgung, Reset, HF

| Pin | Name | Netz | Beschaltung | Quelle |
|---|---|---|---|---|
| 11, 18, 24 | VDDS | `VDD` | je 100 nF (C6–C8) + 10 µF (C5) + Puffer **4 × 100 µF (C1–C4 bestückt im Prototyp, D-013)** | HW-Guide S.5 Abb. 3-1; DS S.18 Fussnote 3 |
| 2, 20 | VDDR | `VDDR` | je 100 nF (C10/C11) + 10 µF (C9) an L1 | HW-Guide S.5; DS S.18 Tab. 7.4 Fussnote 2 |
| 17 | DCDC | `DCDC_SW` | L1 10 µH (WPN201610H) nach VDDR | DS S.18 Tab. 7.4 |
| 16 | VDDD | `VDDD` | 1 µF (C12) | HW-Guide S.5 |
| 13 | RSTN | `RSTN` | 100 kΩ nach VDD (R1) + 100 nF (C13), **kein Pad** | CONCEPTS 2.2 |
| 21, 22 | X48P/N | `X48P/X48N` | Y1 48 MHz 8 pF, **keine externen C** (Cap-Array in SysConfig) | DS S.26 Fussnote 1 |
| 1 | ANT | `RF_PIN` | 1.5 pF – 2.7 nH – 1.5 pF – 15 pF – Pi (0 Ω, 2 × DNM) – Antenne AN043 | HW-Guide S.5; OP-K9 |
| 23, 25 (EP) | GND | `GND` | Massefläche, EP mit Vias | DS S.77–78 |

## 3 Verbindliche Firmware-Regeln (Rev B)

| Nr | Regel | Begründung / Quelle |
|---|---|---|
| FW-1 | **Kein I²C-Verkehr während der Feuchtemessung.** Ablauf: SENS_PWR an → TMP1075N One-Shot → nach ≥ 15 ms lesen → TMP in Shutdown → **SENS_PWR low, SDA/SCL Ausgang low** (oder hochohmig ohne Pull) → erst dann Messkette ein | I²C-Leitungen laufen ≈ 25–30 mm neben PROBE_SENSE (Innenlagen) in den Kragen; statische Leitungen = konstante Parasitärkapazität, wird kalibriert (FLOORPLAN_OPTIONS 2f (3)). tCONV 10–15 ms: `TI_TMP1075_Datasheet_SBOS854F.pdf` S.7 Tab. 6.6 |
| FW-2 | **Messkette nur in Bursts:** je Burst DIO11 low → ≥ 50 µs warten (OSC_PWR lädt C21/C25, **ANNAHME**, am Muster messen) → f0 (DIO8 hochohmig, Puffer aus) → f1 (DIO8 low) → DIO11 high; **Burst (Kette an) ≤ 0.6 ms, danach ≥ 30 ms Schlaf, höchstens 4 Bursts je Messung**. Nie am Stück messen. Während eines Bursts **LEDs aus, kein Funk, kein Flash-Schreiben** | Kette + CPU ≈ 12.8 mA. SPICE `simulation/spice/README.md` (a): mit dieser Regel Einbruch ≤ VERB +4 dBm (136 mV bei R_int 100 Ω, 80 µF); 16 × 0.6 ms am Stück dagegen 1.16 V → VDDS bis < 1.71 V (Reset) |
| FW-3 | f_osc = 8 × f(MEAS_CLK). Ratiometrie C = dC·T0/(T1−T0) − C_basis, dann **Offset-Korrektur über VDD** (Batteriemonitor) und Temperatur (TMP1075N): SPICE VDD 3.0 → 2.4 V verschiebt C um −3.2 pF ≈ 13 % der Spanne (R3 1 kΩ; 10 kΩ: −0.3 pF); Koeffizienten am Muster bestimmen. VDD-Wert dafür aus der letzten Messung **ohne** Funk-/LED-Last | `simulation/spice/README.md` (b); MESSKETTE_SALZ Kap. 5; **PROTOTYP-PRÜFUNG** |
| FW-4 | **LED-Pulse ≤ 5 ms** mit Pausen, mittlerer LED-Strom je Blink ≤ 3 mA; Blink nur, wenn der letzte Lastwert über der Schwelle liegt; Farbtabelle nach VDD (Blau ab ≈ 2.65–2.85 V) | Phase-3-Review 1.4/1.8; SPICE README (a): 20 ms × 3 mA fällt fast ganz über R_int ab |
| FW-5 | **Unterspannung in der Verbindung messen** (schwerstes reguläres Ereignis), nicht nur nach dem Advertising; geordnete Abschaltung (Notspeichern, Shutdown), wenn VDD **unter Last < 2.4 V** (E1) | SPICE README (a), Regel B: VDDS bleibt in allen gerechneten Fällen ≥ 2.25 V |
| FW-6 | **SWD abschalten und Pulls an DIO16/17 aus**, früh im Boot (vor dem ersten Schlaf); Serie: CCFG sperrt Bootloader/SWD | E3; TRM S.22 (Reset-Zustand SWDIO Pull-up, SWDCK Pull-down) |
| FW-7 | CPU-Arbeit nicht unmittelbar vor/nach dem Advertising (Puffer erholt sich mit τ ≈ R_int·C ≈ 8–16 ms) | SPICE README (a) |
| FW-8 | **Schlafzustand:** DIO11 high (oder hochohmig, R13), DIO12 low, DIO16/17 low oder hochohmig ohne Pull, DIO8 hochohmig + Puffer aus, DIO24 Puffer aus oder Pull-down, LED-Pins high, DIO21 Pull-up (ausser Dauerdruck) | Ruhestrom; LVC-Eingänge Ioff (keine Rückspeisung bei OSC_PWR = 0) |
| FW-9 | Batteriemessung über den internen Batteriemonitor (kein Teiler) | DS S.19 Tab. 7.7 |
| FW-10 | Bootloader/Debug: ROM-UART-Bootloader (RX DIO20, TX DIO6, Trigger DIO21); keine SWD-Pads | CONCEPTS 2.2/2.8 |

**Timer-Zuordnung (Vorschlag):** Timer 3 (T3C0, DIO24) = Messung; Timer 1 (T1C2 DIO6, T1C0 DIO20) und Timer 0
(T0C0N DIO13) = LED-PWM (DS Tab. 6-1, 6-15, 6-16).

## 4 Testpads (nur messen, keine Quelle; Abstimmung sicherheit)

| Pad | Netz | Lage | Zweck |
|---|---|---|---|
| TP1 / TP2 | `UART_TX_PAD` / `UART_RX_PAD` | Zellfach, ausserhalb der Zellfläche | Programmierung (Barriere 2 × 100 kΩ, R2-A3) |
| ~~TP3~~ | – | – | **entfällt ab Rev C** (D-023, Auflage A-1); Adapter-/Mess-GND über das Minuspad von BT1 |
| TP4 | `MEAS_CLK` (f_osc/8) | **B-Seite Elektronikband** | Oszilloskop/Zähler, nur vor dem Einschieben zugänglich |
| TP5 | `PROBE_SENSE` | **B-Seite Elektronikband**, nahe der Durchführung | VNA-Messung der Sonde 1–150 MHz (MESSKETTE_SALZ Kap. 6), ≈ +0.5 pF Cpar (**ANNAHME**) |
