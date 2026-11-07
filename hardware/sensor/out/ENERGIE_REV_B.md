# fluidi Sensor Rev B - Energiebudget (erzeugt von scripts/energy_budget.py --revb)

| | |
|---|---|
| Grundlage | Layout/Netzliste Rev B (`hardware/sensor/out/fluidi_sensor.net`), BOM `fluidi_sensor_bom_jlc.csv`, PINMAP Rev B (FW-1..10), Firmware `firmware/sensor` (Einstellungen, Burst-Konstanten) |
| Zelle | CR2032 225 mAh ([RC32] S.1 / [PAN] S.1), nutzbar real 90 % / pess 75 % (REQ-ENE-08) x 0.90 (Abschaltung 2.4 V unter Last, E1) |
| Faelle | **real** = Typwerte, DCDC; **pess. A** = REQ-ENE-08 (Typ x1.5, Ereignisse x1.5, +20 %), Teile ohne Typwert mit ANNAHME; **pess. DS** = jedes Leck an der Datenblattgrenze (REQ-ENE-08 'Maximalwert', Nachweisfall REQ-ENE-02) |
| Profil | n automatische Messungen/Tag + 2 manuelle (REQ-ENE-04), Advertising 27.5 s (Reaktionszeit 1 min), Datensitzung je Messung, LED L3/L1 (pess. + L8 12 h), OTA 1/Jahr |

## 1 Ruhestrom (Schlaf, FW-8) je Bauteil [uA]

| Bauteil / Pfad | real | pess. A | pess. DS | Quelle / Begruendung |
|---|---|---|---|---|
| U1 CC2340R52 Standby (LFXT, RAM, RTC) | 0.740 | 1.826 | 1.826 | [CC] S.19 Tab. 7.9 0.74 uA (DCDC) real; pess. GLDO 1.15 uA (S.20) x1.5 x Sonnenprofil 1.058 (S.35 Fig. 7-7); DS nennt keinen Max-Wert |
| Q1 AO3401A Verpolschutz (leitend, VGS = -VDD) | 0.020 | 0.100 | 0.100 | [AO] S.2 IGSS <= 100 nA @ VGS +-12 V |
| Q2 AO3401A Messkette aus (VGS = 0, VDS = -VDD) | 0.010 | 0.100 | 1.667 | [AO] S.2; Leckstrom fliesst ueber OSC_PWR in U2/U4-U6 (ICC), zaehlt nur einmal |
| C1-C4 4 x 100 uF X5R 6.3 V (Puffer, D-013) | 0.200 | 0.500 | 12.000 | [SAM] S.53 Insulation Resistance; Messung bei Nennspannung 6.3 V, bei 3 V real deutlich kleiner |
| C5 10 uF (VDD) + C9 10 uF (VDDR) | 0.010 | 0.050 | 0.960 | [S10] S.2; 100 nF/1 uF-Typen (C6-C8, C10-C13, C21, C24, C25) < 1 nA je Stueck (500 MOhm*uF), vernachlaessigt |
| U2 SN74LVC1G14 + U4-U6 SN74LVC1G80 (OSC_PWR = 0) | 0.000 | 0.000 | 0.000 | unversorgt (Q2 aus); Eingang U2 an PROBE_SENSE ohne Quelle (DIO8 hochohmig), Ausgang U6 an DIO24 Puffer aus -> keine Spannung an Ioff-Pins ([G14] S.7, [G80] S.6 Ioff <= 10 uA nur bei angelegter Spannung) |
| U3 TMP1075N + R4/R5 4.7k + C24 (SENS_PWR low) | 0.000 | 0.000 | 0.000 | unversorgt: DIO12 low, DIO16/17 Ausgang low (FW-1/FW-8) -> 0 V an R4/R5 und U3; ISD 0.15/0.35 uA [TMP] S.7 Tab. 6.6 entfaellt |
| R13 100k (Gate Q2), R1 100k (RSTN), D1 RGB, SW1 | 0.000 | 0.000 | 0.000 | beide Enden auf VDD: DIO11 high, RSTN high, LED-Kathoden high (FW-8); Taster offen, Pull-up stromlos |
| R9-R12 UART-Barriere zu TP1/TP2 (Zellfach) | 0.000 | 0.060 | 0.060 | Fehlerfall Feuchte im Zellfach: <= 3 V / 200 kOhm = 15 uA je Pad (nicht im Budget, Sicherheit/Dichtung) |
| GPIO-Leck U1, Leiterplatte, Flussmittel | 0.050 | 0.200 | 0.200 | kein DS-Wert fuer Pad-Leckstrom in [CC] Tab. 7.21.4.1 (S.31-32) -> ANNAHME |
| **Summe Schlaf** | **1.03** | **2.84** | **16.81** | REQ-ENE-09 Schlaf <= 3 uA (am Prototyp gemessen, ENERGIEMESSUNG E1) |

## 2 Messung Rev B (je Messung, ohne Funk) [uC]

Messkettenstrom (U2 + U4-U6, Cpd + Lasten + Sonde + Querstrom): real 7.3 mA bei 24.2 MHz, pess. 10.4 mA bei 36.1 MHz (MESSKETTE_SALZ Kap. 5: 10.2 mA). Dazu CPU und R13 (30 uA) waehrend des Bursts.

| Anteil | real | pess. (x1.5) |
|---|---|---|
| Kette (4 Bursts) | 23.8 | 52.1 |
| TMP1075N + I2C | 4.9 | 10.9 |
| Pausen (Standby real / Idle pess) | 0.0 | 189.0 |
| CPU + Flash | 8.0 | 37.2 |
| **Summe** | **36.7** | **289.3** |

## 3 Tagesbudget und Laufzeit CR2032 (4 x 100 uF, D-013)

| Messungen/Tag (auto + 2 manuell) | Fall | Mittelstrom [uA] | davon Schlaf [uA] | Laufzeit [Monate] | Laufzeit [Jahre] | >= 12 Monate |
|---|---|---|---|---|---|---|
| 4 + 2 | real | 1.66 | 1.03 | 130.2 | 10.9 | ja |
| 4 + 2 | pessA | 5.46 | 2.84 | 34.8 | 2.9 | ja |
| 4 + 2 | pessDS | 22.24 | 16.81 | 9.2 | 0.8 | **nein** |
| 5 + 2 | real | 1.67 | 1.03 | 129.9 | 10.8 | ja |
| 5 + 2 | pessA | 5.48 | 2.84 | 34.7 | 2.9 | ja |
| 5 + 2 | pessDS | 22.25 | 16.81 | 9.1 | 0.8 | **nein** |
| 6 + 2 | real | 1.67 | 1.03 | 129.6 | 10.8 | ja |
| 6 + 2 | pessA | 5.49 | 2.84 | 34.6 | 2.9 | ja |
| 6 + 2 | pessDS | 22.27 | 16.81 | 9.1 | 0.8 | **nein** |

Laufzeiten ueber ca. 120 Monate sind rechnerisch; begrenzend ist dann die Lagerfaehigkeit/Alterung der Zelle (kein Wert in [PAN]/[RC32], ANNAHME ~10 Jahre).

### 3b Serienoption 2 x 100 uF (C3/C4 DNM, D-013)

| Messungen/Tag | real | pess. A | pess. DS |
|---|---|---|---|
| 4 + 2 | 137.4 | 36.7 | **13.4** |
| 5 + 2 | 137.0 | 36.6 | **13.4** |
| 6 + 2 | 136.7 | 36.5 | **13.4** |

### 3c Budgetanteile 6 + 2 Messungen/Tag (vor +20 %-Zuschlag) [mC/Tag]

| Posten | real | pess. A | pess. DS |
|---|---|---|---|
| Schlaf: U1 CC2340R52 Standby (LFXT, RAM, RTC) | 63.94 | 157.73 | 157.73 |
| Schlaf: Q1 AO3401A Verpolschutz (leitend, VGS = -VDD) | 1.73 | 8.64 | 8.64 |
| Schlaf: Q2 AO3401A Messkette aus (VGS = 0, VDS = -VDD) | 0.86 | 8.64 | 144.00 |
| Schlaf: C1-C4 4 x 100 uF X5R 6.3 V (Puffer, D-013) | 17.28 | 43.20 | 1036.80 |
| Schlaf: C5 10 uF (VDD) + C9 10 uF (VDDR) | 0.86 | 4.32 | 82.94 |
| Schlaf: U2 SN74LVC1G14 + U4-U6 SN74LVC1G80 (OSC_PWR = 0) | 0.00 | 0.00 | 0.00 |
| Schlaf: U3 TMP1075N + R4/R5 4.7k + C24 (SENS_PWR low) | 0.00 | 0.00 | 0.00 |
| Schlaf: R13 100k (Gate Q2), R1 100k (RSTN), D1 RGB, SW1 | 0.00 | 0.00 | 0.00 |
| Schlaf: R9-R12 UART-Barriere zu TP1/TP2 (Zellfach) | 0.00 | 5.18 | 5.18 |
| Schlaf: GPIO-Leck U1, Leiterplatte, Flussmittel | 4.32 | 17.28 | 17.28 |
| Messung (TMP, Kette, CPU) | 0.29 | 2.31 | 2.31 |
| Advertising 27.5 s | 50.76 | 128.40 | 128.40 |
| Schnelles Advertising nach Taste | 0.65 | 1.63 | 1.63 |
| Datensitzung je Messung | 2.39 | 6.14 | 6.14 |
| LED | 0.72 | 11.52 | 11.52 |
| OTA 1/Jahr | 0.56 | 0.59 | 0.59 |

## 4 Pulslast (REQ-ENE-06: <= 0.2 V bei R_int 100 Ohm)

RC-Modell: R_int 100 Ohm, C_eff = 4 x 100 uF x 0.5 (DC-Bias, ANNAHME) x 0.8 (Toleranz) = 160 uF, tau = 16 ms. Vollstaendige Rechnung mit DCDC und Ereignisformen: `simulation/spice/supply/supply_report.txt`.

| Ereignis | Strom [mA] | Einbruch [mV] | <= 200 mV |
|---|---|---|---|
| Messung FW-2: 4 x 0.6 ms, Pause 30 ms (pess.) | 14.5 | 63 | ja |
| Messung ohne FW-2: 16 x 0.6 ms am Stueck (pess.) | 14.5 | 654 | **nein** |
| TX 0 dBm GLDO, 3 Kanaele ~0.38 ms (pess.) | 9.0 | 60 | ja |
| LED 3 mA, 5 ms (L8) | 3.0 | 81 | ja |
| LED 3 mA, 30 ms (L1) | 3.0 | 254 | **nein** |

Die LED-Ereignisse > 5 ms ueberschreiten 0.2 V bei 100 Ohm (wie SPICE): FW-4 (Pulse <= 5 ms mit Pausen, Blink nur bei ausreichender Last-Spannung). Zelltemperatur: CR2032 -30...+85 C ([PAN] S.1); Kapazitaet bei Kaelte nicht gesondert reduziert (Innenraum, ANNAHME), Innenwiderstand bei Kaelte ueber R_int 100 Ohm EOL abgedeckt (REQ-ENE-06).

## 5 Parameter (Auszug Rev B)

| Schluessel | Wert | Einheit | Quelle |
|---|---|---|---|
| rb.vdd | 3 | V | Nennspannung CR2032 [PAN] S.1 (Rechenwert fuer Leck-/Laststroeme) |
| rb.q1_real | 2e-08 | A | ANNAHME 20 % der IGSS-Grenze bei |VGS| 3 V statt 12 V |
| rb.q2_real | 1e-08 | A | ANNAHME IDSS bei VDS -3 V (DS nur bei -30 V) |
| rb.q2_pa | 1e-07 | A | ANNAHME 10 % der DS-Grenze (VDS -3 V statt -30 V) |
| rb.q2_ds | 1.667e-06 | A | [AO] S.2 IDSS <= 1 uA (TJ 25 C) / 5 uA (TJ 55 C) @ VDS -30 V, Sonnenprofil 4 h/Tag bei 55 C |
| rb.mlcc_real | 2e-07 | A | ANNAHME 0.05 uA je 100 uF (wie oben mlcc.real), PROTOTYP-PRUEFUNG |
| rb.mlcc_pa | 5e-07 | A | ANNAHME pess. A gesamt (wie concept_energy.py MLCC_PESSA) |
| rb.mlcc_ds | 1.2e-05 | A | [SAM] S.53 IR >= 100 MOhm*uF (markierte Hochkapazitaetstypen) -> 1 MOhm je 100 uF -> 3 uA @3 V, x4 |
| rb.c10_real | 1e-08 | A | ANNAHME |
| rb.c10_pa | 5e-08 | A | ANNAHME |
| rb.c10_ds | 9.6e-07 | A | [S10] S.2 IR >= 50 MOhm*uF -> 5 MOhm je 10 uF; C5 @3.0 V + C9 @VDDR <= 1.8 V (ANNAHME VDDR) |
| rb.uart_real | 0 | A | Pads offen |
| rb.uart_pa | 6e-08 | A | ANNAHME Oberflaechenisolation TP1/TP2-TP3 >= 100 MOhm |
| rb.uart_ds | 6e-08 | A | wie pess. A (kein DS-Wert) |
| rb.board_real | 5e-08 | A | ANNAHME (concept_energy.py BOARD) |
| rb.board_pa | 2e-07 | A | ANNAHME (concept_energy.py BOARD) |
| rb.cpd14 | 2.2e-11 | F | [G14] S.8 Tab. 5.8 Cpd 22 pF @3.3 V, f 10 MHz |
| rb.cpd80 | 2.5e-11 | F | [G80] S.8 Tab. 5.11 Cpd 25 pF @3.3 V, f 10 MHz |
| rb.fosc_real | 2.42e+07 | Hz | simulation/spice/README.md (b): f_osc typ trocken, R3 1 kOhm |
| rb.fosc_pess | 3.61e+07 | Hz | MESSKETTE_SALZ Kap. 5 D3: Luft 36.1 MHz (= 8 x 4.51 MHz, schnelle Ecke) |
| rb.c_node | 5e-12 | F | ANNAHME Last je Teilerknoten (CIN ~3-5 pF + Bahn) |
| rb.c_measclk | 1.5e-11 | F | ANNAHME DIO24 (C_pin 5-7 pF, [CC] S.32) + TP4 + Bahn |
| rb.c_probe | 3e-11 | F | ANNAHME C_Sonde + Cpar (MESSKETTE_SALZ Kap. 5: 22.7-44.1 pF) |
| rb.dv_hyst | 1 | V | ANNAHME Schmitt-Hysterese LVC1G14 bei 3 V (DS-Tabelle VT+/VT-, gerundet) |
| rb.i_shoot | 0.001 | A | ANNAHME Querstrom U2, Eingang laeuft dauernd durch die Schwellen |
| rb.t_burst | 0.0006 | s | FW-2 Grenze (fluidi_board.h: 50 us + 2 x 250 us + Rest) |
| rb.n_burst | 4 | - | FW-2 FLUIDI_BURST_MAX |
| rb.t_pause | 0.105 | s | FW-2 3 Pausen x 30 ms + FW-1 tCONV 15 ms ([TMP] S.7 Tab. 6.6) |
| rb.idle | 0.0008 | A | [CC] S.19 Tab. 7.9 Idle, Flash aus, DCDC |
| rb.idle_ldo | 0.0012 | A | [CC] S.20 Tab. 7.9 Idle, Flash aus, GLDO |
| rb.t_tmp_settle | 0.001 | s | fluidi_board.h FLUIDI_SENS_PWR_SETTLE_US (Busy-Wait, CPU aktiv) |
| rb.t_i2c | 0.0008 | s | 2 Transaktionen 100 kHz (Schreiben 3 B, Zeiger + Lesen 2 B) ~ 80 Takte |
| rb.tmp_conv | 5.2e-05 | A | [TMP] S.7 Tab. 6.5 TMP1075 'during active conversion' typ (TMP1075N Tab. 6.6 nennt nur IDD_AVG 4.8/7.5 uA) -> ANNAHME fuer N |
| rb.tmp_conv_max | 8.5e-05 | A | [TMP] S.7 Tab. 6.5 max (ANNAHME fuer N) |
| rb.r_i2c | 4700 | Ohm | [NET] R4/R5 4.7 kOhm nach SENS_PWR |
| rb.c24 | 1e-07 | F | [NET] C24 100 nF an SENS_PWR (je Messung umgeladen) |
| rb.r13 | 1e+05 | Ohm | [NET] R13 100 kOhm VDD-OSC_EN_N, Strom nur bei Kette ein |
| rb.t_cpu_meas | 0.003 | s | ANNAHME Auswertung, Datensatz, Planung (CPU aktiv) |
| rb.t_cpu_meas_p | 0.006 | s | ANNAHME pess. |
| rb.q_flash_rec | 1.963e-07 | C | 24-B-Datensatz anteilig an [CC] S.21 Tab. 7.11 (2 kB), fl_ringlog.c |
| rb.adv_iv | 27.5 | s | [FW] fl_settings.c adv_interval_ms 27500 (= reach_interval(1 min)) |
| rb.fast_adv | 20 | 1/Taste | [FW] fl_app.c FAST_ADV_MS 2000 / FAST_ADV_INT_MS 100 |
| rb.i_led | 0.003 | A | FW-4 / PROTOCOL 10.1 Obergrenze 3 mA (Rechnung D1 + R6/R7/R8 siehe Bericht) |
| rb.led_l3 | 0.02 | s | PROTOCOL 10.2 L3 Gruen 1 x 20 ms je automatischer Messung (heartbeat_led = 1) |
| rb.led_l1 | 0.06 | s | PROTOCOL 10.2 L1 Gruen 2 x 30 ms je Tastendruck |
| rb.led_l8 | 3.6 | s/Tag | PROTOCOL 10.2 L8 1/min x 5 ms, 12 h (nur pess.) |
| rb.n_man | 2 | 1/Tag | REQ-ENE-04 Standardprofil |
| rb.c_buf | 0.0004 | F | D-013 Prototyp 4 x 100 uF (C1-C4) |
| rb.cutoff | 0.9 | - | concept_energy.py CUTOFF_FACTOR: Abschaltung 2.4 V unter Last (E1, FW-5), [PAN] S.1 Entladekurve abgelesen |
