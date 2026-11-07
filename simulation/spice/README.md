# SPICE – Sensor Rev A (ngspice 42, Batch)

Stand 2026-11-07, Schaltplan `hardware/sensor/fluidi_sensor.kicad_sch` (Rev A). Alle Läufe per Skript reproduzierbar:

```
.venv/bin/python simulation/spice/supply/supply_burst.py          # (a) ca. 2 min
.venv/bin/python simulation/spice/osc/osc_sim.py                  # (b) ca. 2 min
.venv/bin/python simulation/spice/uart_backfeed/uart_backfeed.py  # (c) < 10 s
```

Jedes Skript schreibt die Netzliste (`*.cir`, letzter Fall), eine CSV mit allen Fällen und PNG-Plots in seinen Ordner.
Modellannahmen und Datenblattstellen stehen im Kopf des jeweiligen Skripts. `led_rgb/` stammt aus Phase 3.

## (a) Versorgung: CR2032 + Puffer bei Funk-/Messlast (REQ-ENE-06, E1, OP-K6)

Modell: Zelle Vocv 2.7 V (Lebensende, TI SWRA349 S.11) mit R_int 20…1000 Ω, AO3401A + Halter 0.135 Ω, Puffer C_eff
200 / 100 / 80 / 160 µF (2 × 100 µF nominal / DC-Bias 50 % **ANNAHME** / zusätzlich −20 % / 4 × 100 µF mit DC-Bias und −20 %),
CC2340 mit DCDC (konstante Leistung, **ANNAHME**) und GLDO unter 2.2 V. Ereignisse: Advertising 3 Kanäle (ADV),
Verbindung 50 ms im 7.5-ms-Intervall (VERB), Messung 10 ms × 3 mA (MESS), LED 20 ms × 3 mA, Flash-Notspeichern.
Funk-/CPU-Zeiten pessimistisch × 1.5 bzw. nominal.

**Einbruch bei R_int = 100 Ω** (pess. / nom., Kriterium ≤ 0.2 V), Auszug:

| Ereignis | 2 × 100 µF nominal | 2 × 100 µF DC-Bias 50 %, −20 % (80 µF) | 4 × 100 µF DC-Bias 50 %, −20 % |
|---|---|---|---|
| ADV 0 dBm | 118 / 82 mV ✔ | **246 / 178 mV** ✘ / ✔ | 143 / 100 mV ✔ |
| ADV +4 dBm | 142 / 98 mV ✔ | **298 / 214 mV** ✘ | 172 / 119 mV ✔ |
| VERB +4 dBm | 120 / 80 mV ✔ | 157 / 105 mV ✔ | 129 / 86 mV ✔ |
| MESS 10 ms × 3 mA | 180 / 132 mV ✔ | 302 / 246 mV ✘ | 210 / 157 mV |
| LED 20 ms × 3 mA | 219 mV ✘ | 336 mV ✘ | 250 mV ✘ |

Bewertung:
- **REQ-ENE-06 (Senden)**: Verbindungen erfüllt in allen Fällen. Das Advertising-Ereignis erfüllt 0.2 V mit 2 × 100 µF
  nur, wenn der DC-Bias-Verlust kleiner ist als angenommen oder die Zeiten nominal sind; mit **4 × 100 µF** (C3/C4 bestückt)
  in allen Fällen. Der Puffer-Bedarf wird von der CPU-Zeit direkt vor/nach dem Funk bestimmt (E1-Annahme).
- MESS und LED sind lange Lasten (≫ τ = R·C ≈ 8 ms): Der Einbruch ist praktisch I·R_int, der Puffer hilft kaum.
  Sie sind kein „Senden“, bestimmen aber die Abschaltlogik.
- **E1, Abschaltung 2.4 V unter Last**: Misst die Firmware VDD nur nach dem Advertising (Regel A), kann ein späteres
  LED-/Messereignis VDDS bis 2.01 V drücken (GLDO statt DCDC, aber kein Reset ≥ 1.71 V). Misst sie während der
  Verbindung (schwerstes reguläres Ereignis) und gibt die LED nur über der Schwelle frei (Regel B), bleibt VDDS in allen
  Fällen (R_int bis 1 kΩ, alle Puffer) **≥ 2.25 V**, das Notspeichern im Flash eingeschlossen. Ein Reset (1.71 V / BOD 1.67 V)
  tritt in keinem gerechneten Fall auf.
- Fallende Flanke VDD max. **0.16 mV/µs** < 1 mV/µs (DS S.18 Tab. 7.3 Fussnote 3).

Folgerungen: (1) Prototyp Rev A mit **C3/C4 bestückt** aufbauen und am Muster mit 2 und 4 Kondensatoren messen (OP-K6),
DC-Bias-Kurve CL31A107MQHNNNE beschaffen. (2) Firmware: Unterspannung während der Verbindung messen (Regel B), LED-Pulse
≤ 5 ms mit Pausen, CPU-Arbeit nicht unmittelbar vor/nach dem Advertising. (3) R_int-Werte aus der Panasonic-Kurve sind
abgelesen (**ANNAHME**); Pulsverhalten am Lebensende nur am Muster prüfbar (PROTOTYP-PRÜFUNG).

Plots: `supply/supply_waveforms.png` (ADV, VERB, LED bei 100 / 1000 Ω), `supply/supply_drop.png` (Einbruch über R_int).

## (b) Messoszillator SN74LVC1G14, Speisung über DIO12

Modell: Schmitt-Inverter mit Schwellen aus LVC-DS S.7 Tab. 5.5 (5 Ecken innerhalb der Grenzen), tpd 1.6–5.5 ns (S.8),
Cpd 22 pF, R_out 40 Ω; SENS_PWR über 53 Ω (DIO12 High-Drive, CC2340-DS S.31) mit 2 × 100 nF; Knoten 10 pF + Cref im
Aus-Zustand in Serie mit 6 pF Pinkapazität (DS S.32). Sonde **ANNAHME** bis Feldsimulation: trocken 30 pF, nass 100 pF,
nass leitfähig (20 pF + 100 pF Isolation in Serie mit 1 kΩ bzw. 300 Ω).

| Sonde | f0 VDD 3.0 V (Ecken, typ) | f0 VDD 2.4 V | f1 / f2 typ 3.0 V |
|---|---|---|---|
| trocken 30 pF | 3.23–5.22 (4.14) MHz | 2.88–4.78 (3.72) | 3.15 / 1.54 |
| nass 100 pF | 1.41–2.25 (1.79) MHz | 1.25–2.06 (1.60) | 1.58 / 1.03 |
| nass leitfähig 1 kΩ | 1.53–3.46 (2.26) MHz | 1.28–2.89 (1.87) | 1.84 / 1.06 |
| nass leitfähig 300 Ω | 1.28–2.19 (1.68) MHz | 1.12–1.97 (1.48) | 1.47 / 0.97 |

- Schwingt in allen 120 Fällen (+ 6 Fälle R3-Variation); Bereich 0.66–5.22 MHz, also unter der Zählgrenze (≈ 10–12 MHz, CONCEPTS 2.3).
  Der Nassfall liegt mit R3 = 4.7 kΩ bei **1.8 MHz typ, also unter den geplanten 2 MHz**, weil die Aus-Kapazität der
  beiden Cref-Zweige (≈ 10.4 pF) dazukommt. R3 = 3.9 kΩ ergäbe 4.93 / 2.15 MHz (typ). Dafür gibt es aber nur ein Extended-Teil
  (C51721, JLC 2026-11-07), deshalb bleibt R3 auf 4.7 kΩ, bis die Feldsimulation die Sondenkapazität liefert.
- Pegel an DIO24: high ≥ 2.98 / 2.39 V (VIH 0.8·VDDS erfüllt), low ≤ 9 mV. SENS_PWR sinkt um ≤ 20 mV, Strom ≤ 0.6 mA.
- Ratiometrie (C_x aus f0/f1 mit festen Konstanten): systematisch +4 pF (Laufzeit tpd); Streuung über Schwellen-Ecken
  und VDD zusammen ±0.7 pF trocken / ±0.75 pF nass, davon VDD 3.0 → 2.4 V allein ≈ 0.6 pF ≈ **0.9 % der Kalibrierspanne** → VDD-abhängige
  Korrektur (CONCEPTS 2.3) nötig für REQ-MES-04/05. Leitfähige Erde verschiebt f deutlich (Salzthema REQ-MES-11, OP-K3).

Plots: `osc/osc_waveforms.png`, `osc/osc_freq.png`.

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

## Offene Punkte

| Nr | Punkt | Art |
|---|---|---|
| SP-1 | DC-Bias-Kurve CL31A107MQHNNNE (bzw. Ersatztyp mit Kurve) beschaffen; Puffer am Muster mit 2 und 4 × 100 µF messen | Datenblatt, PROTOTYP-PRÜFUNG (OP-K6) |
| SP-2 | Reale Stromprofile CC2340 (Advertising, Verbindung, Flash) am LaunchPad oder Muster messen, Faktor 1.5 ersetzen | PROTOTYP-PRÜFUNG |
| SP-3 | Sondenkapazität aus `simulation/field`, danach R3 und Cref festlegen (Arbeitsbereich 2–6 MHz). Vorläufiges, **ungeprüftes** Feldergebnis `simulation/field/results/probe3d_gsg_h2.json` (Luft 12 / trocken 16 / nass 33 pF) ergibt mit R3 4.7 kΩ (Handlauf `osc_sim.netlist`, VDD 3.0 V): Luft 6.25 MHz typ (4.85–7.92), nass 3.93 MHz (3.07–4.95) → über 6 MHz, Spanne nur 21 pF ≈ Cref1; dann R3 grösser (z. B. 6.8 kΩ) und Cref1 kleiner wählen | Feldsimulation, Entscheid Elektronik |
| SP-4 | Firmware-Regeln: Unterspannung während der Verbindung messen, LED-Pulse ≤ 5 ms, CPU nicht direkt am Funkburst | Firmware |
| SP-5 | R2-A4: Injektionsstrom in die ESD-Struktur bei 5.5 V an allen Pads, Funktionstest danach | PROTOTYP-PRÜFUNG |
