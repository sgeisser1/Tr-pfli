# Phase 4 Welle 3 – Abgleich Firmware/Energie mit Layout Rev B

| | |
|---|---|
| Stand | 2026-11-07, Firmware/Energie |
| Geprueft | `hardware/sensor/fluidi_sensor.kicad_pcb` (pcbnew), `hardware/sensor/out/fluidi_sensor.net` (Rev B, 21:27), `LAYOUT_REV_B.md`, `fluidi_sensor_bom_jlc.csv`/`_extra.csv`, `docs/interfaces/PINMAP_SENSOR.md` Rev B, `firmware/sensor` (`config/fluidi_board.h`, `syscfg/fluidi_sensor.syscfg`, `platform/cc23/fl_hw.c`, `core/fl_ui.c`, `core/fl_settings.c`), `scripts/energy_budget.py`, `scripts/concept_energy.py`, `docs/manuals/ENERGIEMESSUNG.md` |
| Werkzeuge | Netzliste mit eigenem S-Ausdruck-Parser, Layout mit `pcbnew` (KiCad 10.0.8), Datenblaetter mit `pdftotext`, Firmware-Build `make clean && make` und `make check` (TI-Toolchain `~/fluidi-tools`) |
| Status | nichts committet |

## 1 Pinabgleich Netzliste/Layout ↔ PINMAP ↔ fluidi_board.h ↔ SysConfig

Pin → DIO aus `TI_CC2340R5_Datasheet_SWRS272F.pdf` S.9–12 Tab. 6-1 (Spalte RGE). Netze von U1 aus der Netzliste und
identisch aus den Pads der Platine (pcbnew).

| Pin | DIO (DS) | Netz Netzliste = Layout | PINMAP Rev B | fluidi_board.h | SysConfig / Mux | Ergebnis |
|---|---|---|---|---|---|---|
| 3 | DIO8 | CREF1_CTL (C22 → PROBE_SENSE) | CREF1_CTL | `FLUIDI_DIO_CREF1 8` | GPIO | ok |
| 4 | DIO11 | OSC_EN_N (Q2 Gate, R13 → VDD) | OSC_EN_N | `FLUIDI_DIO_OSC_EN_N 11` (Rev B) | GPIO | ok |
| 5 | DIO12 | SENS_PWR (U3 V+, C24, R4/R5) | SENS_PWR | `FLUIDI_DIO_SENS_PWR 12` | GPIO, High-Drive (DS S.6 Liste RGE) | ok |
| 6 | DIO13 | LED_G (R7 → D1 Pin 3) | LED_G | `FLUIDI_DIO_LED_G 13` | GPIO | ok |
| 7 | DIO16 | I2C_SDA (U3 Pin 6, R4) | I2C_SDA | `FLUIDI_DIO_I2C_SDA 16` | `sdaPin = DIO16_SWDIO` (I2C0SDA Mux 3, DS S.10) | ok |
| 8 | DIO17 | I2C_SCL (U3 Pin 1, R5) | I2C_SCL | `FLUIDI_DIO_I2C_SCL 17` | `sclPin = DIO17_SWDCK` (I2C0SCL Mux 3, DS S.10) | ok |
| 9 | DIO20 | LED_B_UART_RX (R8 → D1 Pin 4, R11/R12 → TP2) | LED_B_UART_RX | `FLUIDI_DIO_LED_B 20` | GPIO | ok |
| 10 | DIO21 | BTN_BOOT_N (SW1 → GND) | BTN_BOOT_N | `FLUIDI_DIO_BUTTON 21` | GPIO Pull-up, Flanke, Shutdown-Wake low | ok |
| 12 | DIO24 | MEAS_CLK (U6 Q̅/D, TP4) | MEAS_CLK | `FLUIDI_DIO_MEAS_CLK 24` | `FLUIDI_MUX_MEAS_CLK_T3C0 3` (DS S.11: DIO24 T3C0 = 3) | ok |
| 14/15 | DIO3/DIO4 | X32P/X32N (Y2, C14/C15) | X32P/X32N | `FLUIDI_DIO_X32P/N 3/4` | `srcClkLF = "LF XOSC"` | ok |
| 19 | DIO6 | LED_R_UART_TX (R6 → D1 Pin 2, R9/R10 → TP1) | LED_R_UART_TX | `FLUIDI_DIO_LED_R 6` | GPIO | ok |

Weitere Pruefungen an der Netzliste: Q2 G/S/D = OSC_EN_N/VDD/OSC_PWR; U2 SN74LVC1G14 A = PROBE_SENSE, Y = OSZ_OUT,
R3 1 kΩ Rueckkopplung; U4–U6 SN74LVC1G80 Pin 1 D = Pin 4 Q̅ (Teiler ÷2, `TI_SN74LVC1G80_Datasheet_SCES221T.pdf` S.3,
Q invertiert) → ÷8 = `FLUIDI_OSC_DIVIDER 8`; U3 TMP1075NDRLR Pin 1 SCL, 2 GND, 3 ALERT (offen, Open-Drain), 4 A0 = GND,
5 V+, 6 SDA (`TI_TMP1075_Datasheet_SBOS854F.pdf` S.3–4 Abb. 5-4) → Adresse 0x48 (S.14 Tab. 7-3); D1 Pin 1 Anode = VDD,
2/3/4 = R/G/B (TUOZHAN-Datenblatt S.4); Bootpins: DIO21 low = ROM-Bootloader (Taster), DIO11 (SPI-CS im Bootloader)
durch R13 hochgezogen → Messkette bleibt aus. E1 (Sonde) ist nicht mehr Teil der Netzliste/Platine, PROBE_SENSE haengt
nur an U2, R3, C22, TP5 – fuer die Firmware ohne Folge.

**Ergebnis: keine Pin-Abweichung.** `make check-pins` prueft ab jetzt zusaetzlich PINMAP Kap. 1 gegen die
Datenblatt-Pinliste (RGE) und gegen U1 in `hardware/sensor/out/fluidi_sensor.net` (Negativtest: vertauschtes Netz
und falsche DIO-Nummer werden gemeldet).

## 2 Energiebudget Rev B

Neu: `scripts/energy_budget.py --revb [--out hardware/sensor/out/ENERGIE_REV_B.md]` (bauteilgenau, alle Werte mit
Quelle in `PARAMS` unter `rb.*`). Die Phase-2-Ausgabe und `concept_energy.py` sind byte-gleich geblieben (Diff geprueft).

Ruhestrom (FW-8) je Pfad, 3.0 V [µA], real / pess. A / pess. DS (Datenblattgrenze):

| Pfad | real | pess. A | pess. DS | Quelle |
|---|---|---|---|---|
| U1 Standby LFXT | 0.74 | 1.83 | 1.83 | DS S.19/20 Tab. 7.9, ×1.5 × Sonnenprofil |
| Q1 Verpolschutz IGSS | 0.02 | 0.10 | 0.10 | `AOS_AO3401A_Datasheet_Rev3.1.pdf` S.2 |
| **Q2 (neu Rev B) IDSS** | 0.01 | 0.10 | **1.67** | ebd. S.2: 1 µA (25 °C) / 5 µA (55 °C) bei −30 V |
| C1–C4 4 × 100 µF | 0.20 | 0.50 | **12.0** | `Samsung_CL31A107MQHNNNE_Catalog_2015-11.pdf` S.53, 100 MΩ·µF |
| C5/C9 10 µF | 0.01 | 0.05 | 0.96 | `Samsung_CL05A106MQ5NUNC_Datasheet_LCSC-2022-08.pdf` S.2, 50 MΩ·µF |
| U2, U4–U6 (OSC_PWR = 0), U3 + R4/R5 (SENS_PWR low), R13, R1, D1, SW1 | 0 | 0 | 0 | keine Spannung an den Pfaden (FW-8); Ioff nur bei angelegter Spannung (`TI_SN74LVC1G14_Datasheet_SCES218AA.pdf` S.7, LVC1G80 S.6) |
| UART-Barriere TP1/TP2, Leiterplatte | 0.05 | 0.26 | 0.26 | ANNAHME |
| **Summe** | **1.03** | **2.84** | **16.8** | REQ-ENE-09 Schlaf ≤ 3 µA: pess. A erfuellt (knapp) |

Messung Rev B (je Messung): Kettenstrom aus Cpd (LVC1G14 22 pF S.8 Tab. 5.8, LVC1G80 25 pF S.8 Tab. 5.11) + Knotenlasten +
Sonde + Querstrom: 7.3 mA bei 24 MHz (real) / 10.4 mA bei 36 MHz (pess.; MESSKETTE_SALZ: 10.2 mA). Mit CPU, R13,
TMP1075N (Wandlung 15 ms, `SBOS854F` S.7) und I²C: **37 µC real / 289 µC pess.** (pess. mit Idle 0.8–1.2 mA statt Standby in
den 105 ms Pausen). Anteil am Tag < 1 % – die Messung ist fuer die Laufzeit unerheblich.

Laufzeit CR2032 (225 mAh, nutzbar 90 %/75 % × 0.90 fuer die Abschaltung bei 2.4 V), 4 × 100 µF (D-013), Reaktionszeit 1 min:

| Messungen/Tag | real | pess. A | pess. DS (REQ-ENE-02) |
|---|---|---|---|
| 4 + 2 manuell | 1.66 µA → 130 Mt. (10.9 J.) | 5.46 µA → 34.8 Mt. | 22.2 µA → **9.2 Mt.** |
| 5 + 2 | 1.67 µA → 130 Mt. | 5.48 µA → 34.7 Mt. | 22.3 µA → **9.1 Mt.** |
| 6 + 2 (Standardprofil) | 1.67 µA → 130 Mt. | 5.49 µA → 34.6 Mt. | 22.3 µA → **9.1 Mt.** |
| 6 + 2, **2 × 100 µF** | 137 Mt. | 36.5 Mt. | **13.4 Mt.** |

Alt (Modell Phase 2/3, `concept_energy.py`, 1 min, 6 + 2): 4 × 100 µF und 2.4 V real 1.64 µA → 132 Mt., pess. A 36.9 Mt.,
pess. DS 10.7 Mt.; 2 × 100 µF (A-32 v0.3, in MESSKETTE_SALZ zitiert) pess. DS **17.0 Mt.** → neu 13.4 Mt.
Unterschied: Q2-Leckgrenze (+1.67 µA), 10-µF-Leckgrenzen (+0.96 µA), Bauteilsumme statt pauschal 0.2 µA.
Die Anzahl Messungen (4–6/Tag) aendert die Laufzeit kaum; es dominieren Schlaf, Advertising (27.5 s: 51/128 mC/Tag)
und im DS-Fall der Puffer-Leckstrom.

**Ziel ≥ 1 Jahr:** real und pess. A klar erfuellt (≥ 2.9 Jahre). Im Nachweisfall REQ-ENE-02 (alle Lecks an der
Datenblattgrenze) nur mit 2 × 100 µF (13.4 Mt.), mit 4 × 100 µF nicht (9.1 Mt.) – bekannt aus D-013, jetzt mit
Rev-B-Bauteilen bestaetigt.

Pulslast (RC-Modell, 100 Ω, 4 × 100 µF × 0.5 DC-Bias × 0.8 = 160 µF): Messung nach FW-2 63 mV, ohne FW-2 (16 × 0.6 ms
am Stueck) 654 mV, TX 0 dBm GLDO 60 mV, LED 3 mA 5 ms 81 mV, **LED 3 mA 30 ms 254 mV** (SPICE `supply_report.txt`
mit DCDC und Ereignisformen bestaetigt die Groessenordnung).

## 3 Firmware-Build und Tests

`make clean && make`: 0 Fehler, 4 bekannte Linker-Hinweise #10325 (NVS); Slot 0 206 804 B Code (90 %), signiertes Image
207 235 B in Slot 1 (90 %), RAM 33 658 B (91 %), alle Groessenpruefungen ok. `make check`: Layout ok, Pins ok (inkl.
Netzlisten-Abgleich), 1503 C-Pruefungen bestanden, 17 Tests Flash-Werkzeug ok, 3 Tests Kopplungsangriff ok.
Nach der Aenderung von `fluidi_board.h` neu gebaut und geprueft (gleiches Ergebnis). Protokoll `firmware/sensor/build/build.log`.

## 4 Befunde

| Nr | Stufe | Befund | Begruendung | Vorschlag | Stand |
|---|---|---|---|---|---|
| EP-1 | **wichtig** | Mit 4 × 100 µF erfuellt Rev B REQ-ENE-02 im Datenblatt-Fall nicht (9.1 Mt.); 2 × 100 µF 13.4 Mt., dafuer ADV-Einbruch 246 mV pess. (D-013) | C1–C4-Leckgrenze 12 µA dominiert (Samsung S.53); Q2 bringt neu bis 1.67 µA | Prototyp: Leckstrom C1–C4 bei 3.0 V und 40 °C messen (ENERGIEMESSUNG E1 mit/ohne C3/C4); Serie danach 2 oder 4 (D-013). Alternativ Typ mit Leckangabe bei Betriebsspannung | offen (Projektleitung/Auftraggeber) |
| EP-2 | **wichtig** | LED-Muster laufen ungeteilt 20 ms … 1 s (L1 2 × 30 ms, L3 20 ms, L6/L14 1 s; `core/fl_ui.c`), FW-4 verlangt Pulse ≤ 5 ms mit Pausen | RC-Rechnung 30 ms × 3 mA → 254 mV > 0.2 V bei 100 Ω; SPICE LED 250–336 mV. PWM (FW-O3) fehlt | in `fl_port_led` bzw. `fl_led_tick` Schrittdauern > 5 ms in 5 ms an / 5 ms aus zerlegen (Software, ohne Timer) oder LGPT-PWM (FW-O3) umsetzen; bis dahin LED nur bei VDD_Last ≥ 2.4 V + 0.3 V | offen (Firmware, nicht Teil dieser Pin-Welle) |
| EP-3 | **wichtig** | Pull-up-Strom der GPIOs zu tief angegeben: PINMAP (DIO21, DIO16), PROTOCOL 10.3 und ENERGIEMESSUNG nennen 39–109 µA (DS S.31 gilt fuer VDDS 1.8 V); bei 3.8 V 170–393 µA (DS S.32) | betrifft Taster-klemmt-Fall (30 s × bis ~300 µA ≈ 9 mC) und den SWD-Pull-up-Fehlerfall FW-6 („≈ 66 µA“) | PINMAP/PROTOCOL: „39–109 µA @1.8 V, 170–393 µA @3.8 V (DS S.31–32), bei 3.0 V dazwischen“; ENERGIEMESSUNG E1/E2 angepasst | ENERGIEMESSUNG umgesetzt; PINMAP/PROTOCOL an Elektronik/Projektleitung |
| EP-4 | klein | Pausen der Messung (3 × 30 ms + 15 ms TMP) halten `Power_setDependency(LGPT3)` bzw. das offene I²C-Handle; ob das Standby erlaubt, ist am Muster offen | pess. 189 µC je Messung, Tagesanteil < 2 mC – energetisch unkritisch | ENERGIEMESSUNG E5: Strom in den Pausen messen (Erwartung ≈ 1 µA, sonst 0.8 mA Idle); falls Idle: Abhaengigkeit pro Burst setzen/loesen | PROTOTYP-PRUEFUNG |
| EP-5 | klein | Burst-Dauer 50 + 2 × 250 µs + Batteriemonitor + GPIO-Umschaltung liegt nahe an der FW-2-Grenze 0.6 ms | Reserve ≈ 50 µs | E5 am Oszilloskop (DIO11); falls > 0.6 ms: `FLUIDI_BURST_CFG_US` 250 → 225 | PROTOTYP-PRUEFUNG |
| EP-6 | klein | Blau (R8 100 Ω) kann bei frischer Zelle > 3 mA ziehen | VF Blau 2.6–3.0 V @5 mA (TUOZHAN S.4): (3.3 − 2.6 V)/(100 Ω + Ausgangswiderstand ~100 Ω) ≈ 3.5 mA; Rot ≤ 2.7 mA, Gruen ≤ 3 mA | mit EP-2 (Tastgrad) erledigt; Strom je Farbe in E6 messen | offen |
| EP-7 | klein | `fluidi_board.h` zitierte fuer die Adresse 0x48 Tab. 7-2 (TMP1075, A2..A0) statt Tab. 7-3 (TMP1075N, nur A0) | Kommentar/Quelle | korrigiert | umgesetzt |
| EP-8 | klein | `check-pins` verglich nur PINMAP ↔ Header ↔ SysConfig, nicht die Netzliste | Schaltplanaenderungen (wie in dieser Welle) waeren unbemerkt geblieben | `tools/check_config.py`: PINMAP ↔ DS-Pinliste RGE ↔ Netzliste U1 | umgesetzt |
| EP-9 | klein | PINMAP DIO12: „TMP1075N IDD ≤ 10 µA aktiv (Tab. 6.6)“ – das ist IDD_AVG bei aktivem Bus 400 kHz; Wandlungsstrom fuer N nicht angegeben | Energie vernachlaessigbar | Formulierung bei naechster PINMAP-Revision anpassen | an Elektronik |
| EP-10 | klein | Feuchte im Zellfach: LED_R/LED_B (Schlaf high) treiben ueber 200 kΩ auf TP1/TP2 → bis 15 µA je Pad bei Kurzschluss nach TP3/GND | Ruhestrom-Fehlerbild, kein Sicherheitsproblem (Barriere begrenzt) | in E1 als Fehlerbild aufnehmen; Dichtung Zellfach (REQ-SAF-05) | Hinweis |

## 5 Geaenderte / neue Dateien

- `scripts/energy_budget.py` – Rev-B-Modell (`--revb`, `--out`), Phase-2-Teil unveraendert
- `hardware/sensor/out/ENERGIE_REV_B.md` – neu, erzeugt mit `.venv/bin/python scripts/energy_budget.py --revb --out hardware/sensor/out/ENERGIE_REV_B.md`
- `firmware/sensor/config/fluidi_board.h` – Quellenangabe TMP1075N-Adresse (keine Pin-/Wertaenderung)
- `firmware/sensor/tools/check_config.py` – Netzlisten-/Datenblatt-Abgleich in `check-pins`
- `docs/manuals/ENERGIEMESSUNG.md` – Erwartungen E1, E2, E5 auf Rev B, Schritt 5 (`rb.*`)
- `firmware/sensor/build/` – neu gebaut (nicht versioniert)
