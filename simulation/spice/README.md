# SPICE – Sensor Rev B (ngspice 42, Batch)

Stand 2026-11-07, Schaltplan `hardware/sensor/fluidi_sensor.kicad_sch` (**Rev B**: Messkette D3 nach D-018, Lastschalter
Q2 an DIO11, TMP1075N im Kragen, 4 × 100 µF im Prototyp). Alle Läufe per Skript reproduzierbar:

```
.venv/bin/python simulation/spice/supply/supply_burst.py > simulation/spice/supply/supply_report.txt   # (a) ca. 2 min
.venv/bin/python simulation/spice/osc/osc_sim.py                  # (b) ca. 8 min, schreibt osc/osc_report.txt
.venv/bin/python simulation/spice/uart_backfeed/uart_backfeed.py  # (c) < 10 s
.venv/bin/python simulation/spice/programmer/prog_uart.py          # (d) ca. 15 s, Erstprogrammierung (2026-11-08)
```

Jedes Skript schreibt die Netzliste (`*.cir`, letzter Fall), eine CSV mit allen Fällen und PNG-Plots in seinen Ordner.
Modellannahmen und Datenblattstellen stehen im Kopf des jeweiligen Skripts. `led_rgb/` stammt aus Phase 3,
`probe_osc/` aus der Entscheidungsvorlage Messkette (MESSKETTE_SALZ.md).

## (a) Versorgung: CR2032 + Puffer bei Funk-/Messlast (REQ-ENE-06, E1, OP-K6)

Modell: Zelle Vocv 2.7 V (Lebensende, TI SWRA349 S.11) mit R_int 20…1000 Ω, AO3401A + Halter 0.135 Ω, Puffer C_eff
200 / 100 / 80 / 160 µF (2 × 100 µF nominal / DC-Bias 50 % **ANNAHME** / zusätzlich −20 % / 4 × 100 µF mit DC-Bias und −20 %),
CC2340 mit DCDC (konstante Leistung, **ANNAHME**) und GLDO unter 2.2 V. Ereignisse: Advertising 3 Kanäle (ADV),
Verbindung 50 ms im 7.5-ms-Intervall (VERB), **Messung Rev B** (MESS: 4 Bursts × 0.6 ms, Messkette 10.2 mA direkt an VDD
über Q2 + CPU 2.6 mA, dazwischen 30 ms Schlaf; MESSD: 9.6 ms am Stück), LED 20 ms × 3 mA, Flash-Notspeichern.
Funk-/CPU-Zeiten pessimistisch × 1.5 bzw. nominal. Messkettenstrom 10.2 mA aus MESSKETTE_SALZ Kap. 5; (b) ergibt
≤ 8.6 mA → konservativ.

**Einbruch bei R_int = 100 Ω** (pess. / nom., Kriterium ≤ 0.2 V), Auszug (`supply/supply_report.txt`):

| Ereignis | 2 × 100 µF nominal | 2 × 100 µF DC-Bias 50 %, −20 % (80 µF) | 4 × 100 µF DC-Bias 50 %, −20 % |
|---|---|---|---|
| ADV 0 dBm | 118 / 82 mV ✔ | **246 / 178 mV** ✘ / ✔ | 143 / 100 mV ✔ |
| ADV +4 dBm | 142 / 98 mV ✔ | **298 / 214 mV** ✘ | 172 / 119 mV ✔ |
| VERB +4 dBm | 120 / 80 mV ✔ | 157 / 105 mV ✔ | 129 / 86 mV ✔ |
| **MESS Rev B** (4 × 0.6 ms, 30 ms Pause) | 72 / 49 mV ✔ | 136 / 92 mV ✔ | 82 / 56 mV ✔ |
| MESSD (9.6 ms am Stück, Regelverletzung) | 697 / 503 mV ✘ | **1159 / 952 mV** ✘ | 812 / 603 mV ✘ |
| LED 20 ms × 3 mA | 219 mV ✘ | 336 mV ✘ | 250 mV ✘ |

Einbruch MESS über R_int (80 µF, pess.): 108 / 136 / 143 / 169 / 255 / 354 mV bei 20 / 100 / 130 / 220 / 500 / 1000 Ω,
also ab 100 Ω immer kleiner als VERB +4 dBm (157 … 661 mV). MESSD erreicht 1.16 … 2.47 V.

Bewertung:
- **REQ-ENE-06 (Senden)**: unverändert gegenüber Rev A. Verbindungen erfüllt in allen Fällen; Advertising mit
  **4 × 100 µF** (Rev B Prototyp bestückt, D-013) in allen Fällen.
- **Neue Last Messkette D3** (P-FET Q2): ≈ 12.8 mA statt 3 mA. Am Stück gemessen (MESSD, so in MESSKETTE_SALZ
  Kap. 5 mit 16 × 0.6 ms angenommen) wäre das mit Abstand das schwerste Ereignis (1.16–2.47 V Einbruch bei
  R_int 100–1000 Ω → VDDS unter 1.71 V, Reset); Regel B würde es nicht abdecken. **Firmware-Regel FW-2 (PINMAP):** Burst ≤ 0.6 ms, ≥ 30 ms Schlaf, ≤ 4
  Bursts. Damit bleibt MESS ab R_int 100 Ω unter VERB +4 dBm, und **Regel B** (Unterspannung in der Verbindung messen)
  deckt sie mit ab: VDDS bleibt in allen gerechneten Fällen **≥ 2.25 V**, kein Reset.
- Einschalten von Q2: C21 + C25 (200 nF) laden aus dem Puffer, Ladungsteilung ≈ 3 V × 0.2/160 µF ≈ 4 mV (Handrechnung).
  DIO12 (SENS_PWR) trägt nur noch den TMP1075N (≤ 10 µA + Pull-ups).
- Fallende Flanke VDD max. **0.16 mV/µs** < 1 mV/µs (DS S.18 Tab. 7.3 Fussnote 3).

Folgerungen: (1) Prototyp mit 4 × 100 µF; am Muster mit 2 und 4 messen (OP-K6). (2) Firmware: FW-2 Burstregel,
Unterspannung während der Verbindung messen (Regel B), LED-Pulse ≤ 5 ms mit Pausen, CPU-Arbeit nicht unmittelbar
vor/nach dem Advertising (PINMAP Kap. 3). (3) R_int-Werte abgelesen (**ANNAHME**), Pulsverhalten am Lebensende nur am
Muster prüfbar (**PROTOTYP-PRÜFUNG**).

Plots: `supply/supply_waveforms.png`, `supply/supply_drop.png`.

## (b) Messkette D3: RC-Oszillator SN74LVC1G14 + Teiler ÷8 (3 × SN74LVC1G80), Speisung über Q2

Modell (`osc/osc_sim.py`): Schmitt-Inverter mit Schwellen aus LVC1G14-DS S.7 Tab. 5.5 (5 Ecken), tpd 1.6–5.5 ns (S.8),
Cpd 22 pF, R_out 40 Ω; OSC_PWR über Q2 (0.1 Ω **ANNAHME**) mit C21 + C25; Knoten 10 pF + TP5 0.5 pF (**ANNAHME**),
Cref1 22 pF im Aus-Zustand in Serie mit 6 pF Pinkapazität; Ausgang belastet mit U4-CLK 3.5 pF + 1 pF.
**Sonde nach `docs/interfaces/PROBE_CAPACITANCE.md` Kap. 3** (C0 7.05 pF ‖ Ci 99 pF – (ε'·1.72 pF ‖ Rs)).
**Teiler in SPICE** als XSPICE `d_dff` (D an /Q, CLK→Q 3 ns **ANNAHME**, DS S.7: 1.3–4.2 ns bei 3.3 V).
360 Fälle (R3 1 k / 10 k, VDD 3.0 / 2.4 V, 9 Sondenzustände, 5 Ecken, f0/f1), alle schwingen.

| Sonde (typ, VDD 3.0 V) | **R3 1 kΩ** f_osc [MHz] (Ecken 3.0 V) | MEAS_CLK = f/8 max [MHz] | **R3 10 kΩ** f_osc [MHz] (Ecken) |
|---|---|---|---|
| Luft | **27.4** (20.3–36.1) | 4.51 | 4.11 (3.21–5.18) |
| trocken (ε' 4) | **24.2** (18.0–31.7) | 3.96 | 3.46 (2.71–4.36) |
| Mitte, Leitungswasser | 20.3 (15.1–26.3) | 3.29 | 1.42 (0.92–2.24) |
| nass, Leitungswasser | **14.9** (10.9–19.5) | 2.44 | 0.94 (0.72–1.24) |
| nass, gedüngt low / normal | 9.1 / 8.1 | 1.60 / 1.34 | 0.86 / 0.86 |
| Wasser verlustfrei / Leitungswasser | **10.8 / 9.8** | 1.73 / 1.62 | 1.28 / 0.87 |

- **Zählgrenze:** MEAS_CLK ≤ **4.51 MHz** in allen Fällen (1 kΩ), Grenze ≈ 10–12 MHz (**ANNAHME**, CONCEPTS 2.3)
  → Faktor ≥ 2.2 Reserve. Minimum 0.59 MHz (nass gedüngt, Ecke, 2.4 V). Mit 10 kΩ ≤ 0.65 MHz.
- **Teiler:** SPICE-Teilerausgang = f_osc/8 auf ≤ 0.34 % (Mittelungsfehler über wenige Perioden) in 180 Fällen;
  fclock ≤ 36.1 MHz ≪ 160 MHz, kürzester Puls OSZ_OUT 12.4 ns ≥ tw 2.5 ns (LVC1G80 S.6 Tab. 5.6).
- **Abweichung zur Entscheidungsvorlage:** MESSKETTE_SALZ (D3) rechnet 36.1 / 17.4 MHz (Luft / nass). Mit den
  Rev-B-Parasitics (Cref1-Aus-Kapazität 4.7 pF, Cpd, Ausgangslast) liegt typ **27.4 / 14.9 MHz** (−24 / −14 %).
  Die Salzbewertung dort ist damit etwas zu günstig (tiefere Frequenz = mehr Leitfähigkeitseinfluss) → am Muster
  im Becherversuch prüfen (OP-K3, **PROTOTYP-PRÜFUNG**). Option R3 kleiner (0.68 kΩ, MESSKETTE Kap. 5) erst
  nach dem Becherversuch; Zählgrenze und tw dann neu rechnen.
- **tpd-Einfluss** (typ, f0): df/f je ns = −8.3 % (Luft) … −4.2 % (nass) bei 1 kΩ, −1.3 … −0.3 % bei 10 kΩ.
  Ohne Ratiometrie verschiebt +1 ns den Index in der Mitte um **+12.6 %-Punkte** (1 kΩ) bzw. +0.3 (10 kΩ).
- **Ratiometrie** C_x = dC·T0/(T1−T0) − C_basis (dC 17.29 pF, C_basis 15.21 pF): Die Spanne trocken→nass bleibt
  23.4–24.3 pF über alle Ecken (wahr 23.0 pF), aber ein Offset von ≈ +19 pF (Laufzeit) und **VDD 3.0 → 2.4 V
  verschiebt C_x um −3.2 pF ≈ 13 % der Spanne** (10 kΩ: −0.27 pF). Exemplarstreuung (Ecken 7 pF) kalibriert die
  Zwei-Punkt-Kalibrierung weg; der **VDD-Gang muss korrigiert werden** (FW-3, Batteriemonitor), Temperatur ebenso
  (tpd-Drift im Modell nicht über VDD/T variiert → **PROTOTYP-PRÜFUNG**).
- **Strom:** Oszillator ≤ 3.4 mA (SPICE) + Teiler ≤ 5.2 mA (Cpd 25 pF je FF, LVC1G80 S.8) = **≤ 8.6 mA** bei 3.0 V
  (1 kΩ); OSC_PWR sinkt ≤ 0.5 mV (Q2). Mit 10 kΩ ≤ 1.2 mA.

Plots: `osc/osc_waveforms.png` (OSZ_OUT, PROBE_SENSE, MEAS_CLK), `osc/osc_freq.png` (Frequenz je Sonde, beide R3).

## (c) Rückstrom über die UART-Pads (R2-A1, R2-A4)

Modell: Quelle an Pad TX/RX bzw. beiden → 2 × 100 kΩ (Einzelfehler: ein Widerstand überbrückt) → ESD-Diode nach VDD
(Vf ≈ 0 V konservativ bzw. Diodenmodell) → AO3401A (Kanal leitet bei VDD > |VTH|) → Zelle 3.0 / 2.0 / 0 V, Gerätelast 0.

| Fall (ESD ideal) | Zelle 3.0 V | Zelle 2.0 V | Zelle 0 V | Zeit bis 1 % C (0 V) |
|---|---|---|---|---|
| 5.5 V an 1 Pad | 12.5 µA | 17.5 µA | 23.0 µA | 98 h |
| 5.5 V an 1 Pad, ein R kurz | 24.9 µA | 34.9 µA | 45.9 µA | 49 h |
| 5.5 V an beiden Pads, ein R kurz | 37.4 µA | 52.4 µA | **68.9 µA** | **33 h** |
| 3.3-V-Adapter an 1 Pad | 1.5 µA | 6.5 µA | 12.0 µA | 188 h |
| 1.8-V-UART an 1 Pad | 0 | 0 | 4.5 µA | 504 h |

Grösster Ladestrom 68.9 µA = **1/145 der Grenze 10 mA** (Maxell S.2). Die Grenze ≤ 1 % C (2.25 mAh) wird erst nach ≥ 33 h
Dauerfehlbedienung erreicht. Das bestätigt die Handrechnung in CONCEPTS 2.7: Sie rechnet mit VDD = 0 V und ist dort
konservativer (82.5 µA), weil der AO3401A in Wirklichkeit erst ab VDD ≈ |VTH| leitet. Der Injektionsstrom in die
ESD-Struktur ist gleich gross wie der Padstrom (≤ 46 µA je Pin). Das Datenblatt nennt dafür keinen Grenzwert, deshalb bleibt
das eine PROTOTYP-PRÜFUNG nach R2-A4.

Plot: `uart_backfeed/uart_backfeed.png`.

## (d) Erstprogrammierung: UART-Pegel und Flanken mit Programmieradapter Rev 1 (Red-Team W-4, B-4)

Modell und Quellen im Kopf von `programmer/prog_uart.py`; Adapter `hardware/programmer/README.md`, Ablauf
`docs/manuals/PROGRAMMIEREN_SENSOR.md`. CH343-Pull-up als abregelnde Stromquelle nach VIO, Waveshare-RXD-LED (2 kΩ),
LED-Modelle aus `led_rgb/led_models.inc`. Kapazitäten (**ANNAHME**): R9/R10-Knoten 1–3 pF, TP1 2–3 pF, Stift + Draht +
Puffer 5–10 pF, DIO20 7–9 pF, blaue LED 0–30 pF. Bericht `programmer/prog_uart_report.txt`.

| Fall | Ergebnis | Grenze |
|---|---|---|
| A0 ohne Puffer (bisheriges Konzept), CH343-RXD an TP1 | Low 0.64 V (Pull-up 3 µA, 1.8 V) bis 1.99 V (Pull-up typ/max) | 0.5 V → **nicht lesbar** |
| A1 SN74AUP1G17 am Federstift, R1 10 MΩ, Leck ±0.5 µA, 1.96–2.04 V | Low 0.331–0.369 V, High 1.862–1.942 V | VT− ≥ 0.47 V, VT+ ≤ 1.77 V (Hülle 1.65/2.3 V): Reserve **+101 / +92 mV** |
| A2 Behelf, CH343-RXD an R9 Pad 1 (DIO6), 2.0 / 2.2 V | Low 0.253 / 0.359 V | 0.5 V |
| A3 Behelf am falschen Pad (R9 Pad 2) | Low 0.43 V (3 µA) bis 1.97 V (30 µA) | **nicht lesbar** |
| B Sensor-RX DIO20 (blaue LED VF-min), 1.96 / 2.04 / 2.2 V | Low 0.136 / 0.190 / 0.313 V | VIL 0.2 × VDDS: Reserve +256 / +218 / +127 mV |
| Zeitverhalten TX (Puffer am Stift), 57600 Baud | t10–90 3.1 µs (nominal) / 6.0 µs (schlecht); Reserve 0.290 / 0.216 Bit | ≥ 0.20 Bit (**ANNAHME**) |
| Zeitverhalten TX, Puffer am Kabelende (40 pF) | 18.2 µs; 57600 Baud: Bytes falsch | → Puffer muss am Stift sitzen |
| Zeitverhalten RX (DIO20), 57600 Baud | t10–90 3.2/2.4 µs (LED 0 pF) bis 17.5/13.3 µs (LED 30 pF); Reserve ≥ 0.300 Bit | ≥ 0.20 Bit |

## Offene Punkte

| Nr | Punkt | Art |
|---|---|---|
| SP-1 | DC-Bias-Kurve CL31A107MQHNNNE (bzw. Ersatztyp mit Kurve) beschaffen; Puffer am Muster mit 2 und 4 × 100 µF messen | Datenblatt, PROTOTYP-PRÜFUNG (OP-K6) |
| SP-2 | Reale Stromprofile CC2340 (Advertising, Verbindung, Flash) am LaunchPad oder Muster messen, Faktor 1.5 ersetzen | PROTOTYP-PRÜFUNG |
| SP-3 | Messkette D3 am Muster: f_osc trocken/nass/Wasser, Strom OSC_PWR, VDD- und Temperaturgang von C_x (tpd), Vergleich R3 1 k / 10 k im Becherversuch (OP-K3); Abweichung zur Entscheidungsvorlage (Frequenz −14…−24 %) bewerten | PROTOTYP-PRÜFUNG |
| SP-4 | Firmware-Regeln FW-1…FW-8 (PINMAP Kap. 3), insbesondere Burstregel FW-2 und Unterspannung in der Verbindung | Firmware |
| SP-5 | R2-A4: Injektionsstrom in die ESD-Struktur bei 5.5 V an allen Pads, Funktionstest danach | PROTOTYP-PRÜFUNG |
| SP-6 | Zählgrenze LGPT (≈ 10–12 MHz ANNAHME) am LaunchPad bestätigen; Reserve zu MEAS_CLK max 4.5 MHz | PROTOTYP-PRÜFUNG |
