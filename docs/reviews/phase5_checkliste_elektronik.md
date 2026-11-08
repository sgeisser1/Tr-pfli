# Phase 5 – Design-Review-Checkliste Elektronik (Sensor Rev C)

| | |
|---|---|
| Verfasser | Elektronik-Agent |
| Datum | 2026-11-08, Stand git `b77b29a` (main) plus Arbeitsbaum dieser Phase |
| Gegenstand | `hardware/sensor/fluidi_sensor.kicad_sch` / `.kicad_pcb` Rev C, Bestellunterlage `hardware/sensor/out/ORDER_JLC_REV_C.md` |
| Status | **ok** = Nachweis liegt vor und wurde in dieser Phase neu geprüft · **PROTOTYP-PRÜFUNG** = nur am Muster nachweisbar (Testplan `phase5_testplan_beitrag_elektronik.md`) · **offen** = Nachweis fehlt |
| Platine | **unverändert** (sha256 `909e17c5…54723`, `order_check.py` am Ende dieser Phase: Gerber/BOM/CPL-sha256 wie ORDER Kap. 1) |

## 0 Tool-Läufe dieser Prüfung (2026-11-08, selbst ausgeführt)

| Lauf | Befehl | Ergebnis |
|---|---|---|
| ERC WSL | `kicad-cli sch erc --severity-all` (KiCad 10.0.8 WSL) | **0 Fehler**, 1 Warnung `pin_to_pin` U1 Pin 5 (DIO12, Bidirectional) ↔ `#FLG55` (Power output) – bekannt, unkritisch (SENS_PWR wird vom GPIO gespeist, das Flag markiert nur die Quelle) |
| ERC Windows | `kicad-cli.exe sch erc --severity-all` (KiCad 10.0.8 Windows) | 0 Fehler, 1 Warnung (gleich) |
| Netzliste | `gen_schematic.py` + `check_netlist.py` | 57 Bauteile, 153 Pins, 37 Netze = Soll (`intended_netlist.json`) |
| DRC WSL | `kicad-cli pcb drc --severity-all --schematic-parity` ohne und mit `--refill-zones` (ohne `--save-board`) | **0 Verletzungen, 0 ungeroutet, 0 Parität** (beide Läufe) |
| DRC Windows | `kicad-cli.exe pcb drc --severity-all --schematic-parity` | 0 Fehler, 4 Warnungen `lib_footprint_mismatch` SOT-353 (U2, U4–U6; neuere Windows-Bibliothek, Pads gleich, LAYOUT Kap. 7); 0 ungeroutet, 0 Parität |
| DRC ignoriert | Bericht „Ignored checks“ | kein Courtyard (TP/AE1), Bahnende nicht auf Via-Mitte, Tuning-Profile, Footprint-Filter, Footprint-Typ – keine Fertigungsregel betroffen |
| Platinengeometrie | pcbnew-Skript (nur lesen) | 145 Vias, max. Y 49.57 → **0 Vias bei Y > 50**; **0 Bahnen/Pads auf F/B bei Y > 50**; Silkscreen „rev C“, „fluidi rev C“, „max“ F+B bei Y 59.9, Warnungen im Fach B |
| Bauteilregister | Skript BOM ↔ `docs/datasheets/INDEX.csv` | **26/26** BOM-Positionen mit LCSC-Nr. im Register, je lokales Datenblatt vorhanden |
| Bestellunterlage | `.venv/bin/python hardware/sensor/gen/order_check.py` | sha256 Gerber-ZIP `7da2269d…`, BOM `3d99ffca…`, CPL `b01ba147…` = ORDER Kap. 1; 8 Via-in-Pad gefüllt; BOM = CPL 50 Designatoren |
| SPICE Messkette | `timeout 3600 .venv/bin/python simulation/spice/osc/osc_sim.py` | siehe Punkt E-20 (Hänger behoben, Kap. 3) |

## 1 Schaltung und Bauteile

| Nr | Punkt | Anforderung | Nachweis | Status |
|---|---|---|---|---|
| E-01 | ERC ohne Fehler, Schaltplan per Generator | REQ-FAB-08 | Kap. 0; `hardware/sensor/gen/gen_schematic.py` deterministisch (zweimal erzeugt, byte-gleich) | ok |
| E-02 | Jedes Bauteil mit LCSC-Nr., lokalem Datenblatt, Registereintrag | REQ-FAB-07, REQ-DOC-04 | Kap. 0 (26/26); Block „REV C“ in `INDEX.csv` (W-7) | ok |
| E-03 | Verfügbarkeit geprüft | REQ-FAB-07 | `order_check.py --live` 2026-11-08 10:51 (ORDER Kap. 7); BT1 C5213768 knapp (629 Stk) | ok (vor Bestellung erneut `--live`) |
| E-04 | Basic Parts bevorzugt, Extended begründet | REQ-FAB-02 | 15 Basic, 1 Preferred, 10 Extended (`COSTS_REV_B.md` Z. 54); Begründungen im Register (Bemerkung) | ok |
| E-05 | Pinbelegung SoC gegen Datenblatt | – | `docs/interfaces/PINMAP_SENSOR.md` (DS S.7 Abb. 6-2), Prüfbericht `phase4_energie_pins_revb_firmware.md` („Pins korrekt“) | ok |
| E-06 | Pinbelegung Logik/Sensor stichprobenweise neu geprüft | – | U2 SN74LVC1G14 DCK: 1 NC, 2 A = PROBE_SENSE, 3 GND, 4 Y = OSZ_OUT, 5 VCC = OSC_PWR (`TI_SN74LVC1G14_Datasheet_SCES218AA.pdf` PDF-S. 4 Tab. 4-1). U4–U6 SN74LVC1G80: 1 D = /Q (4), 2 CLK, 3 GND, 5 VCC (`TI_SN74LVC1G80_Datasheet_SCES221T.pdf` PDF-S. 3 „Pin Functions“). U3 TMP1075N DRL: 1 SCL, 2 GND, 4 A0 = GND, 5 V+ = SENS_PWR, 6 SDA (`TI_TMP1075_Datasheet_SBOS854F.pdf` Abb. 5-4/Tab. 5-1, Register) – alle Pads in der Platine gleich | ok |
| E-07 | Absolute-Maximum-Werte | – | CR2032 ≤ 3.3 V gegen CC2340 VDDS (DS S.18 Tab. 7.1), TMP1075N V+ abs. 4 V (S.5 Tab. 6.1), LVC 6.5 V; keine Quelle > Zellspannung im Betrieb; Programmierung 2.0 V (D-024) | ok |
| E-08 | Entkopplung nach HW-Guide | – | Schaltplan-Notiz (HW-Guide SWRA834A S.5 Abb. 3-1), je C ein eigenes Via (LAYOUT Kap. 2) | ok |
| E-09 | Pull-ups, Reset, Bootpins | – | RSTN 100 k + 100 nF; I²C 4.7 k an SENS_PWR (aus im Schlaf); DIO21 Bootloader-Trigger mit internem Pull-up; R13 hält Q2 im Bootloader aus (PINMAP Pin 4/10) | ok |
| E-10 | Verpolschutz | REQ-SAF-CC-01 | Q1 AO3401A G = GND, S = VDD, D = VBAT (Platine: Pad 1 GND, Pad 2 VDD, Pad 3 VBAT); Sicherheit C-02 | ok (A) / PROTOTYP-PRÜFUNG (24 h, ST-Z1) |
| E-11 | Keine Lademöglichkeit, zwei Barrieren je Pad | REQ-SAF-CC-03, REQ-SAF-06 | R9+R10 (TX), R11+R12 (RX), je 2 × 100 k, > 10 mm getrennt; SPICE `uart_backfeed`: grösster Ladestrom 68.9 µA = 1/145 von 10 mA (`simulation/spice/README.md`) | ok (A, S) / PROTOTYP-PRÜFUNG ST-Z5 |
| E-12 | Spannungseinbruch ≤ 0.2 V bei 100 Ω | REQ-ENE-06 | SPICE `supply/supply_report.txt` mit FW-2/FW-4: VDDS ≥ 2.25 V, MESS 136 mV @ 100 Ω | ok (S) / PROTOTYP-PRÜFUNG E3–E6 |
| E-13 | Ruhestrom ≤ 3 µA, Mittelstrom ≤ 8 µA | REQ-ENE-09 | `phase5_energiebudget_final.md`: pessA 2.84 / 5.51 µA (knapp) | PROTOTYP-PRÜFUNG (E1, E12) |
| E-14 | Laufzeit ≥ 12 Monate pessimistisch | REQ-ENE-02 | pessA 34.6 Mt.; **pessDS (Leckstrom C1–C4 nach Katalog) 9.1 Mt. – nicht erfüllt** | **PROTOTYP-PRÜFUNG W-6 (E14)** |
| E-15 | Energiemesspunkt ohne Umgehung einer Schutzfunktion | REQ-ENE-07 | Mess-Zwischenadapter in der Zellposition (`docs/manuals/ENERGIEMESSUNG.md`), Strom fliesst weiter durch Q1 | ok (I) |
| E-16 | Erstprogrammierung ohne teuren Adapter, ohne Zelle | REQ-FW-06 | ROM-UART-Bootloader mit USB-UART (CH343) + Labornetzteil 2.0 V (Behelf) bzw. Adapter Rev 1 (D-024); SPICE `programmer/prog_uart_report.txt` | ok (A, S) / PROTOTYP-PRÜFUNG T-P1, W-10 |
| E-17 | Programmierpegel in allen Unterlagen 2.0 V | D-024 | **in dieser Phase nachgeführt:** PINMAP Pin 9 und Kopf, Schaltplan-Notiz (`gen_schematic.py`), TP3 in PINMAP Kap. 4 als entfallen markiert | ok |
| E-18 | Temperatursensor nahe Dichtlinie unter Verguss | REQ-TMP-01 | U3 im Kragenfeld Y 48.6 (Z5B), ±1 °C −10…60 °C (`TI_TMP1075_Datasheet_SBOS854F.pdf` S.7 Tab. 6.6); Kopplung über Guard-Flächen an den Kopf (L-6) | PROTOTYP-PRÜFUNG |
| E-19 | I²C über ≈ 30 mm Innenlage | – | 4.7 k, 100 kHz; TMP1075N tRD ≤ 1000 ns bei SCL ≤ 100 kHz, tRC ≤ 300 ns (`TI_TMP1075_Datasheet_SBOS854F.pdf` S.9 Tab. 6.8) | PROTOTYP-PRÜFUNG (Flanken messen) |
| E-20 | Messkette D3 zählbar über alle Sondenzustände | REQ-MES-03, REQ-MES-11 | `simulation/spice/osc/osc_report.txt` (Neulauf Phase 5, Knoten 9.89 pF, Sonde Rev B/C), Vergleich Feld-REPORT 11.3: siehe Kap. 3 | ok (S) / PROTOTYP-PRÜFUNG Frequenz am Board |
| E-21 | Status-LED, Taster | REQ-UI-01, -05 | D1 RGB 1615, SW1 TS-1088; Pulse ≤ 5 ms (FW-4, D-023 EP-2) | ok (I) / PROTOTYP-PRÜFUNG E6 Sichtbarkeit, Tastertoleranz −0.20 mm |

## 2 Layout und Sonde

| Nr | Punkt | Anforderung | Nachweis | Status |
|---|---|---|---|---|
| L-01 | DRC 0 Fehler, JLC-Regeln als DRC-Datei | REQ-FAB-01 | Kap. 0; `fluidi_sensor.kicad_dru` 17 Regeln (`pcb_rules.py`) | ok |
| L-02 | Elektroden auf Innenlagen, Aussenlagen im Sondenbereich ohne Kupfer | REQ-MECH-04 | LAYOUT Kap. 1/3; Regelfläche `Z6_Z7_NASS`; Skript: 0 Bahnen/Pads auf F/B bei Y > 50 | ok |
| L-03 | Vergleich 4 Lagen vs. 2 Lagen + Coating | REQ-MECH-04 | `simulation/field/REPORT.md` Kap. 4 (2 L + Coating: Lackdrift, Salzfehler, freies Kupfer bei Lackschaden → 4 L), D-006 | ok |
| L-04 | Keine Vias im nassen Bereich | REQ-MECH-05 | DRC `Z5A_Z7_SONDE`; Skript: max. Via-Y 49.57 (Kragenfeld, tented, K-2) | ok |
| L-05 | Kupfer ≥ 1.0 mm zur Kontur im Sondenbereich | REQ-MECH-06 | DRC-Regel ≥ 1.25 mm ab Z5A (Feld Kap. 8) | ok |
| L-06 | Guard/Masse zwischen Elektronik und Sonde | REQ-MECH-09 | Guard L2/L3 Kragen Y 46…61.5, GND-Flächen Fach (LAYOUT Kap. 3) | ok |
| L-07 | Dichtlinie, Markierung max. Stecktiefe | REQ-MECH-01, -08 | Vergusskante Sonde Y 52.2, Linie + „max“ Y 58.5 F+B (Silkscreen, Masszeichnung Blatt 1) | ok (I) / PROTOTYP-PRÜFUNG Dichtheit |
| L-08 | Antenne oben, Keepout nach Hersteller | REQ-RF-04 | AN043 lokal `docs/appnotes/TI_AN043_SmallPCBAntenna_SWRA117D.pdf`, Masse gegen S.4 Tab. 1 nachgerechnet, Keepout `Z1_ANTENNE` alle Lagen (LAYOUT Kap. 2) | ok (I) / PROTOTYP-PRÜFUNG RSSI, Pi-Netz C19/C20 |
| L-09 | Testpunkte und Programmierzugang | REQ-FAB-09 | TP1/TP2 F im Fach (VIP), TP4 MEAS_CLK / TP5 PROBE_SENSE B im Band; Lage Masszeichnung Blatt 2/3 | ok |
| L-10 | Revision und Produktname auf Silkscreen | REQ-MECH-16 | „rev C“ F, „fluidi rev C“ B, Wortmarke F (LAYOUT Kap. 6) | ok |
| L-11 | Leiterplattendicke festgelegt | REQ-MECH-11 | 1.6 mm, 4 L JLC04161H-7628 (D-006, LAYOUT Kap. 1) | ok |
| L-12 | Fertigungsdaten reproduzierbar, sha256 | REQ-FAB-08 | `run_pcb.sh`, `order_check.py` (Kap. 0) | ok |
| L-13 | Via-in-Pad gefüllt (POFV), nur im Fach/EP | D-023 A-2 | `order_check.py`: 8 VIP mit Füllattribut, 0 ohne | ok / BESTELL-PRÜFUNG (Formular) |
| L-14 | Rotationen/Pin 1 in der JLC-Vorschau | REQ-FAB-01 | CPL-Rotationen Drittquelle + Projektregel SOT-563 (LAYOUT Kap. 8) | **offen bis Bestellung (B-3)** |
| L-15 | Masszeichnung Platine (Kontur, Bohrungen, Höhenzonen) | LS-K4 / OP-K7 | **neu:** `hardware/sensor/out/pdf/fluidi_sensor_masszeichnung.pdf` (Generator `gen_dimension_drawing.py`): 146 PTH Ø 0.30, 0 NPTH | ok |
| L-16 | Leitungsführung von Hand optimiert | – | Router-Ergebnis DRC-sauber, nicht handoptimiert (LAYOUT Kap. 10) | offen (spätere Revision) |

## 3 Simulation

| Nr | Punkt | Anforderung | Nachweis | Status |
|---|---|---|---|---|
| S-01 | Messvolumen ≥ 80 % aus 10–90 mm | REQ-MES-08 | Feld-REPORT Kap. 11.3: 93.3 % | ok (S) / PROTOTYP-PRÜFUNG Becher |
| S-02 | Einfluss Isolationsdicke | REQ-MECH-11 | Feld-REPORT Kap. 4 (1080/2116/7628: Spanne 321/303/263 pF/m) | ok (S) |
| S-03 | FR4-Feuchteaufnahme | REQ-MES-06 | Feld-REPORT Kap. 7/11.3: +10 % Dk → Luft 3.1 %, Wasser 14.6 % der Spanne → Vorkonditionierung | ok (S) / PROTOTYP-PRÜFUNG 30 Tage |
| S-04 | Versorgung/Pufferung | REQ-ENE-06 | `simulation/spice/supply/` (E-12) | ok |
| S-05 | Messkette D3 | REQ-MES-11 | E-20, Kap. 3 unten | ok |

### 3.1 Messkette D3: Neulauf und Vergleich mit Feld-REPORT 11.3

**Ursache des Hängers (reproduziert, 2026-11-08):** Mit dem Mischstand aus Rev-A-Sondenfit und Knoten 9.9 pF blieb
ngspice 42 im Fall *R3 1 kΩ, VDD 3.0 V, Mitte Leitungswasser, Ecke hyst_max, Cref aus* stehen: Laufzeit 0.5 s bis
t = 1.2 µs, ab t = 1.25 µs kein Ende (Abbruch nach 20/100/120 s); die Fortschrittsanzeige von ngspice („Reference value“)
steht unverändert bei **t = 1.24954 µs**, CPU 99 %. Es ist **keine Endlosschleife im Skript** und kein Konvergenzabbruch
(kein „timestep too small“), sondern ein Stillstand der Zeitschrittsteuerung im Mixed-Mode: Gegenproben im selben Fall
laufen durch **ohne den XSPICE-Teiler** (0.7 s), mit **CST 10 fF statt 1 fF** (Knoten RST/CST mit τ = 1 fs, 0.8 s) oder mit
**halbem Maximalschritt tmax 0.01 ns** (1.6 s). Der Hänger hängt also an einer zufälligen zeitlichen Koinzidenz von
Schaltereignis (hysteretischer Schalter, extrem steifer 1-fs-Knoten) und XSPICE-Ereignis des Teilers; er tritt nur
in einzelnen Parameterkombinationen auf (im Probelauf 1 von 390 Fällen; der Orchestrator-Lauf hing in einem anderen Fall).

**Behebung:** `simulation/spice/spicetools.py` `run(..., timeout=)` beendet ngspice nach Ablauf und meldet `SpiceTimeout`;
`osc_sim.py` `sim()` setzt 60 s je Lauf und wiederholt mit tmax/2 und tmax/4 (gleiche Netzliste). Jede Wiederholung steht
im Bericht (Kap. 0). Nachweis: der reproduzierte Hängerfall läuft mit Zeitlimit 20 s im zweiten Versuch (tmax 0.01 ns)
durch, f_osc 15.31 MHz. Einfluss tmax/2 auf f_osc in vier Vergleichsfällen ≤ 0.015 % (vernachlässigbar). Zusätzlich
Mischstand behoben (EP5-2): Sondenfit Rev B/C (C0 7.297 / Ci 99.13 / Cg 1.7114 pF) und Knoten 9.889 pF aus
`simulation/field/results/leads_revb.json`.

**Neulauf** `timeout 3600 .venv/bin/python simulation/spice/osc/osc_sim.py`: 360 Fälle + 30 tpd-Fälle in 601 s,
**keine Wiederholung nötig**, Schwingung in 360/360 Fällen. `osc_report.txt`, `osc_results.csv`, `osc_freq.png`,
`osc_waveforms.png` aktualisiert.

| Grösse (R3 1 kΩ) | osc_report.txt bisher (10.5 pF, Fit Rev A) | **osc_report.txt neu** (9.889 pF, Fit Rev B/C) | Feld-REPORT 11.3 | Übereinstimmung |
|---|---|---|---|---|
| Luft / trocken / Mitte / nass / Wasser (typ, 3.0 V, Leitungswasser) [MHz] | 27.43 / 24.24 / 20.25 / 14.90 / 9.75 | **27.72 / 24.47 / 20.43 / 15.02 / 9.80** | 27.72 / 24.47 / 20.43 / 15.02 / 9.80 | gleich |
| schnellste Ecke (Luft, hyst_min, 3.0 V) [MHz] | 36.05 | **36.44** (MEAS_CLK 4.55) | 36.44 (4.56) | gleich (MEAS_CLK: SPICE-Teiler vs. f/8 gerechnet) |
| langsamste Ecke (gedüngt normal, hyst_max, 2.4 V, Cref1) [MHz] | 4.75 | **4.76** (MEAS_CLK 0.595) | 4.76 (0.595) | gleich |
| Gesamtbereich f_osc [MHz] | 4.75–36.05 | **4.76–36.44** | 4.76–36.44 | gleich |
| R3 10 kΩ Luft schnell / gedüngt langsam [MHz] | 5.18 / 0.52 | **5.26 / 0.52** | 5.26 / 0.52 | gleich |
| kürzester Puls OSZ_OUT, fclock | 12.44 ns, 36.1 MHz | 12.30 ns ≥ 2.5 ns, 36.4 MHz ≤ 160 MHz | – | ok |
| Strom Kette 3.0 V (Oszillator SPICE + Teiler Cpd) | 8.60 mA | 8.68 mA | – | ok |

Bewertung: MEAS_CLK ≤ 4.55 MHz bleibt unter der Zählgrenze 10 MHz (**ANNAHME**, PINMAP) und in der Firmware-Plausibilität
0.048–12 MHz. Keine Änderung an Schaltung oder Firmware nötig. Der Frequenzbereich am realen Board bleibt
**PROTOTYP-PRÜFUNG** (Testplan EI-20…24).

## 4 Befunde dieser Prüfung

| Nr | Stufe | Befund | Vorschlag / Umsetzung |
|---|---|---|---|
| EP5-1 | wichtig | `osc_sim.py` hing in ngspice (Mixed-Mode-Zeitschrittsteuerung mit XSPICE-Teiler, Zeit bleibt stehen, kein Abbruch) | *umgesetzt*: Zeitlimit je Lauf + Wiederholung mit halbem Maximalschritt (`spicetools.run(timeout=)`, `osc_sim.sim()`), Kap. 3.1 |
| EP5-2 | wichtig | `osc_sim.py` hatte Knoten 9.9 pF, aber noch den Rev-A-Sondenfit (C0 7.05/Ci 99.0/Cg 1.719) – Mischstand, nicht der Stand von Feld-REPORT 11.3 | *umgesetzt*: Fit aus `simulation/field/results/leads_revb.json` (`lumped_new`), Knoten 9.889 pF aus derselben Datei; `leads_revb.py` vergleicht weiterhin gegen Rev A |
| EP5-3 | klein | PINMAP „1.8-V-UART“, TP3 noch gelistet; Schaltplan-Notiz „VDD 1.8-2.0 V, 1.8-V-UART“ | *umgesetzt* (E-17); Schaltplan neu erzeugt, ERC/Parität unverändert, Platine unverändert |
| EP5-4 | klein | `PCB_OUTLINE.md` Kap. 8: „Datenblätter C1–C4 nicht lokal“ – im Register steht inzwischen `Samsung_CL31A107MQHNNNE_Catalog_2015-11.pdf` | Mechanik/Elektronik: Höhe 1206 aus dem Katalog nachtragen (nur Dokument) |
| EP5-5 | klein | Bestückungsplan `fluidi_sensor_bestueckung_F.pdf` ist 1:1 auf A4, Band (26 × 15 mm) kaum lesbar | *umgesetzt*: Masszeichnung Blatt 3 = Bestückungsplan Kopf 5:1 mit Pin 1 und DNP |
