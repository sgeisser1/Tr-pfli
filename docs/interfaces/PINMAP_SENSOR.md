# fluidi Sensor Rev A – Pinplan CC2340R52E0RGER (Schnittstelle Hardware ↔ Firmware)

| | |
|---|---|
| Stand | 2026-11-07, Schaltplan Rev A (`hardware/sensor/fluidi_sensor.kicad_sch`) |
| Quelle der Netze | `hardware/sensor/gen/parts.py` (Generator), geprüft mit `check_netlist.py` gegen die KiCad-Netzliste |
| Grundlagen | CONCEPTS.md 2.2/2.3 (A-32), Phase-3-Review RGB (`docs/reviews/phase3_rgb_antenne_elektronik.md` 1.6: Pinumbau DIO12/DIO13/DIO20), E3 (keine SWD-Pads) |
| Datenblatt | `docs/datasheets/TI_CC2340R5_Datasheet_SWRS272F.pdf` (DS), TRM `docs/datasheets/TI_CC23xx_TechnicalReferenceManual_SWCU193A.pdf` |

Firmware-Namen sind Vorschläge für `board.h`/SysConfig (`FLUIDI_PIN_*`). Änderungen nur gemeinsam mit Elektronik
(Schaltplan neu generieren, Tabelle nachführen).

## 1 GPIO

| Pin | DIO | Netz | Funktion im Betrieb | Firmware-Name | Konfiguration | Besonderheiten (Quelle) |
|---|---|---|---|---|---|---|
| 5 | DIO12 | `SENS_PWR` | Speisung Messkette (U2 SN74LVC1G14, 100 nF C21) **und** TMP1075 (U3, C24) inkl. I²C-Pull-ups R4/R5 | `FLUIDI_PIN_SENS_PWR` | Ausgang, High-Drive, max. Treiberstufe; Ruhe: **low** | VOH ≥ 2.47 V @ 10 mA, VDDS 3.0 V (DS S.31, 7.21.4.1). Last < 3 mA. Nach Einschalten ≥ 1 ms warten (2 × 100 nF, **ANNAHME**, am Muster messen). Ablauf: zuerst TMP lesen, TMP in Shutdown, dann Feuchte messen |
| 12 | DIO24 | `OSZ_OUT` | Oszillatorflanken (2–6 MHz) → Timer-Capture/Zählung | `FLUIDI_PIN_OSZ_IN` | Eingang, kein Pull | Mux: T1C0 (2), **T3C0 (3)**, T0PE (4) (DS S.11 Tab. 6-1; Tab. 6-15, 6-18). **Empfehlung T3C0**, weil T1C0 auch an DIO20 (LED_B) liegt. Zählverfahren (Reziprok, 48 MHz) = PROTOTYP-PRÜFUNG (OP-K3). Testpunkt TP4 |
| 3 | DIO8 | `CREF1_CTL` | Cref1 22 pF zuschalten | `FLUIDI_PIN_CREF1` | Ausgang **low** = Cref1 wirkt; sonst Eingang hochohmig, **Eingangspuffer aus**, kein Pull | Im ROM-Bootloader SPI-CLK-Eingang (TRM S.464), floatend (OP-K19). „Aus“-Kapazität ≈ C_pin 5–7 pF in Serie (DS S.32 CI GPIO) |
| 4 | DIO11 | `CREF2_CTL` | Cref2 100 pF zuschalten (f2, Salzdiagnose) | `FLUIDI_PIN_CREF2` | wie DIO8 | Im ROM-Bootloader SPI-CS (TRM S.464) |
| 7 | DIO16 | `I2C_SDA` | I²C SDA zum TMP1075 (Adresse **0x48**, A2..A0 = GND, `TI_TMP1075_Datasheet_SBOS854F.pdf` S.14 Tab. 7-2) | `FLUIDI_PIN_I2C_SDA` | I2C0SDA (Mux 3); bei SENS_PWR aus: Ausgang low oder Eingang ohne Pull | Nach Reset SWDIO mit internem Pull-up (TRM S.22) → **früh im Boot SWD abschalten und Pull aus** (E3), sonst ≈ 66 µA über R4 in den abgeschalteten TMP |
| 8 | DIO17 | `I2C_SCL` | I²C SCL | `FLUIDI_PIN_I2C_SCL` | I2C0SCL (Mux 3); sonst wie SDA | Nach Reset SWDCK mit Pull-down (TRM S.22) → abschalten (E3). I²C max. 400 kHz (DS S.31) |
| 19 | DIO6 | `LED_R_UART_TX` | LED rot (Kathode über R6 470 Ω) | `FLUIDI_PIN_LED_R` | Ausgang; **low = an**, high = aus (nie hochohmig lassen ohne Grund) | Im ROM-Bootloader **UART TX** (TRM S.464 Tab. 8-38); LED blinkt beim Programmieren. Pad TP1 über R9+R10 (2 × 100 kΩ). PWM: T1C2 (Mux 3); UART0TXD (Mux 5) für Log |
| 6 | DIO13 | `LED_G` | LED grün (R7 200 Ω) | `FLUIDI_PIN_LED_G` | Ausgang, low = an | PWM: T0C0N (Mux 4). Im ROM-Bootloader SPI-PICO-Eingang (unkritisch ohne Takt auf DIO8) |
| 9 | DIO20 | `LED_B_UART_RX` | LED blau (R8 100 Ω) | `FLUIDI_PIN_LED_B` | Ausgang, low = an | Im ROM-Bootloader **UART RX** (TRM S.464). Pad TP2 über R11+R12. Programmieren nur mit **VDD 1.8–2.0 V / 1.8-V-UART** (Phase-3-Review 1.6). PWM: T1C0 (Mux 4) |
| 10 | DIO21 | `BTN_BOOT_N` | Taster SW1 nach GND | `FLUIDI_PIN_BUTTON` | Eingang, **interner Pull-up**, Flanken-Wakeup | Bootloader-Trigger aktiv low (TRM S.465). Pull-up 39–109 µA bei gedrücktem Taster (DS S.31 @ 1.8 V) → nach > 30 s Dauerdruck Pull-up aus, zyklisch prüfen (CONCEPTS Kap. 1) |
| 14 | DIO3_X32P | `X32P` | 32.768-kHz-Quarz Y2 | – | LFXT (Mux 6) | Last 2 × 15 pF (C14/C15), CL ≈ 9 pF (**ANNAHME** C_par 1.5 pF). Taktausgabe zur Messung nur an DIO19 (HW-Guide S.11) – auf RGE nicht vorhanden → Frequenz am Muster über BLE-Timing prüfen |
| 15 | DIO4_X32N | `X32N` | 32.768-kHz-Quarz Y2 | – | LFXT (Mux 6) | – |

Freie DIO: **keine** (QFN24, Phase-3-Review 1.6).

## 2 Versorgung, Reset, HF

| Pin | Name | Netz | Beschaltung | Quelle |
|---|---|---|---|---|
| 11, 18, 24 | VDDS | `VDD` | je 100 nF (C6–C8) + 10 µF (C5) + Puffer 2 × 100 µF (C1/C2, C3/C4 DNM) | HW-Guide S.5 Abb. 3-1; DS S.18 Fussnote 3 (10 µF VDDS bei Knopfzelle) |
| 2, 20 | VDDR | `VDDR` | je 100 nF (C10/C11) + 10 µF (C9) an L1 | HW-Guide S.5; DS S.18 Tab. 7.4 Fussnote 2 |
| 17 | DCDC | `DCDC_SW` | L1 10 µH (WPN201610H) nach VDDR | DS S.18 Tab. 7.4 (DCDC ab VDDS 2.2 V, darunter GLDO automatisch) |
| 16 | VDDD | `VDDD` | 1 µF (C12) | HW-Guide S.5 |
| 13 | RSTN | `RSTN` | 100 kΩ nach VDD (R1) + 100 nF (C13), **kein Pad** | CONCEPTS 2.2, HW-Guide S.5 |
| 21, 22 | X48P/N | `X48P/X48N` | Y1 48 MHz 8 pF, **keine externen C** (internes Cap-Array, Wert in SysConfig) | DS S.26 Tab. 7.20.3.1 Fussnote 1 |
| 1 | ANT | `RF_PIN` | 1.5 pF – 2.7 nH – 1.5 pF – 15 pF – Pi (0 Ω, 2 × DNM) – Antenne AN043 | HW-Guide S.5; OP-K9 |
| 23, 25 (EP) | GND | `GND` | Massefläche, EP mit Vias | DS S.77–78 |

## 3 Weitere Firmware-relevante Festlegungen

| Thema | Festlegung | Quelle |
|---|---|---|
| Batteriemessung | interner Batteriemonitor (kein Teiler) | DS S.19 Tab. 7.7 |
| Unterspannung | geordnete Abschaltung (Notspeichern, dann Shutdown), wenn VDD **unter Last < 2.4 V** (E1). VDD **während einer Verbindung** messen (schwerstes reguläres Ereignis), nicht nur nach dem Advertising → VDDS bleibt in allen gerechneten Fällen ≥ 2.25 V (Regel B) | CONCEPTS Kap. 1/10 E1; `simulation/spice/README.md` (a) |
| LED | Farbtabelle nach VDD (Blau ab ≈ 2.65–2.85 V), mittlerer LED-Strom je Blink ≤ 3 mA, LEDs während der Feuchtemessung aus. **Pulse ≤ 5 ms** mit Pausen (20 ms × 3 mA fällt fast ganz über R_int ab: 0.34 V bei 100 Ω); Blink nur, wenn der letzte Lastwert über der Schwelle liegt | Phase-3-Review 1.4/1.8; SPICE (a) |
| CPU-Arbeit | nicht unmittelbar vor/nach dem Advertising (Puffer erholt sich mit τ ≈ R_int·C ≈ 8–16 ms) | SPICE (a) |
| Messablauf | SENS_PWR an → TMP lesen → TMP Shutdown → Oszillator: f0 (Cref aus), f1 (Cref1), optional f2 (Cref2) → SENS_PWR low, alle Messpins Eingang ohne Pull, Puffer aus | CONCEPTS 2.3 |
| Schlaf | SENS_PWR low; DIO16/17 low oder hochohmig ohne Pull; DIO8/11 hochohmig, Puffer aus; LED-Pins high; DIO21 Pull-up (ausser Dauerdruck) | E3, DS S.31 |
| Bootloader/Debug | ROM-UART-Bootloader (RX DIO20, TX DIO6, Trigger DIO21); keine SWD-Pads; Serie: CCFG sperrt Bootloader/SWD | CONCEPTS 2.2/2.8 |
| Timer-Zuordnung (Vorschlag) | Timer 3 (T3C0, DIO24) = Messung; Timer 1 (T1C2 DIO6, T1C0 DIO20) und Timer 0 (T0C0N DIO13) = LED-PWM | DS Tab. 6-1, 6-15, 6-16 |
