# fluidi – Entscheidungsvorlage Messkette und Salz/Dünger (REQ-MES-11)

| | |
|---|---|
| Stand | 2026-11-07, Phase 4a, Elektronik. Entwurf zur Prüfung |
| Anforderungen | REQ-MES-01…12 (insbesondere REQ-MES-11 Soll ≤ 5 %-Punkte), REQ-ENE-09, REQ-FAB-04 |
| Grundlagen | `simulation/field/REPORT.md` Kap. 5, `docs/interfaces/PROBE_CAPACITANCE.md`, CONCEPTS 2.3, `research_elektronik.md` 6.3/6.4, `hardware/sensor/out/FLOORPLAN_OPTIONS.md`, `docs/interfaces/PINMAP_SENSOR.md` |
| Rechnung | `.venv/bin/python simulation/spice/probe_osc/messkette_salz.py` → `simulation/spice/probe_osc/messkette_salz.txt` (alle Tabellen) und `.json`. Laufzeit ≈ 25 s |
| Modell | `simulation/spice/probe_osc/oscmodel.py`: Schmitt-RC-Oszillator, exakt stückweise gelöst, mit Laufzeit tpd im Regelkreis. Bei tpd = 0 weicht es ≤ 0.02 % von ngspice ab (`probe_osc.py`/`results.csv`, Teil 0) |
| Neue Bauteile | `docs/datasheets/_staging/INDEX_salz.csv` (4 Zeilen, 3 neue Datenblätter) |

## 0 Kurzfassung

- **Die heutige Messkette (A, 2–6 MHz) misst vor allem die Leitfähigkeit und weniger die Feuchte.** Schon mit
  Leitungswasser macht die Leitfähigkeit den grössten Teil der Spanne aus: C_mess trocken/nass 13.3/83.8 pF, ohne
  Leitfähigkeit wären es 13.3/37.0 pF. Gedüngt meldet der Sensor „Giessen nötig“ erst, wenn die Erde fast trocken ist
  (Leitungs-Index 1–3 % statt 30 %, ≈ 50–60 % später im Trocknungszyklus). Leitungswasser mit 721 µS/cm
  (Einzelprobe KLZH) verschiebt den Hinweis bereits auf 5 %. Im physikalisch plausiblen Szenario „Salz konzentriert
  sich beim Austrocknen“ kommt der Hinweis sogar mit reinem Leitungswasser erst bei θ 0.106 statt 0.197.
  Eine Nass-Kalibrierung im eigenen Topf hilft nicht.
- **B (mehrere Frequenzen + Inversion):** In gedüngter Erde ist das Gleichungssystem schlecht konditioniert. Schon
  2 % Modellunsicherheit von Ci ergeben an der Giess-Schwelle ≥ 56 %-Punkte Fehler (1 σ). **Verworfen.**
- **C (LC 70–100 MHz):** Mit idealer C-Messung wären es bei 70 MHz ≤ 4 %-Punkte in der Mitte. Ein realer
  Pierce-Oszillator mit Logikgatter wird aber durch die verlustreiche Sonde (Güte ≈ 2) „gezogen“: −25…+34 %-Punkte,
  je nach tpd und Ausgangswiderstand. Dazu kommen +4.4 mm Band, 3 neue Extended-Typen, 24 mA und Abstrahlung im
  UKW-Band. **Hohes Risiko, nicht jetzt.**
- **D3 (neu): RC-Oszillator schneller (R3 1 kΩ, 17–36 MHz) + Teiler ÷8 (3 × SN74LVC1G80) vor dem Timer.**
  Die Leitungswasser-Kennlinie wird nahezu verlustfrei und linear (Mitte 34 % statt 36 % ideal, heute 31 %, aber stark
  S-förmig). Der Salzfehler an der Giess-Schwelle sinkt von −25…−30 auf **−11…+14 %-Punkte**. Ausnahme: „normal“
  gedüngt und konzentrierend, dort −23. Der Hinweis kommt bei θ 0.089–0.226 statt 0.059–0.106 (Bedarf 0.197).
  Kosten +0.62 CHF/Stk und +3.07 USD je Bestellung, Band +3.4 mm (ohne P-FET +2.2 mm), keine neuen Pins.
  REQ-MES-11 (≤ 5) ist damit nicht sicher erfüllt.
- **Empfehlung:** D3 in Rev A übernehmen. R3 bleibt per Umlöten auf 10 kΩ (= A) umstellbar, so lassen sich beide
  Messketten im Becherversuch am selben Muster vergleichen. Dazu die Firmware-/App-Massnahmen A+ (Kap. 6). C nur
  weiterverfolgen, wenn der Prototyp D3 widerlegt. **Freigabe durch den Auftraggeber:** Kopfhöhe (+2.2…3.4 mm zusätzlich
  zu FLOORPLAN-Option f) und Abweichung von REQ-MES-11 (Soll) bis zum Nachweis am Muster.

## 1 Annahmen (zusätzlich zu REPORT Kap. 1/3, PROBE_CAPACITANCE)

| Nr. | ANNAHME | Wirkung |
|---|---|---|
| A-1 | Substrat nach Topp (mineralisch); Torf und Granulat weichen ab, für Granulat liegen keine Daten vor | Kurvenform, PROTOTYP-PRÜFUNG |
| A-2 | σ_b = σ_p·(ε'−4)/80 (Hilhorst Gl. 4.16, ε_off = 4). Mit ε_off = 3 ist der Trockenpunkt nicht mehr salzfrei: A, normal gedüngt, +64 %-Punkte | Fehler im trockenen Bereich |
| A-3 | σ_p: Leitungswasser 0.031–0.036 S/m (KLZH), gedüngt „low“ 0.18 bzw. „normal“ 0.37 S/m (Purdue PourThru, Gewächshaus). Gelegentlich gedüngte Zimmerpflanzen liegen vermutlich dazwischen (0.07–0.10 als Szenario) | Fallauswahl |
| A-4 | Zeitliche Änderung: Szenario „konzentrierend“ σ_p ∝ θ_nass/θ (Ionen bleiben beim Austrocknen erhalten); Verdünnung durch Giessen über die Matrix A3/A5 | Szenarien |
| A-5 | Giess-Schwelle 30 % (20–40 % geprüft) des Leitungswasser-kalibrierten Index; „wirkliche“ Feuchte = Anzeige bei Leitungswasser am selben θ. Trocknung linear in θ (nur für die Zeitangabe) | Bewertung Nutzen |
| A-6 | Oszillator: VT± Mittelwerte bei 3 V, Ausgang 30 Ω, Cpar 10 pF, tpd 3 ns je Flanke im Regelkreis (LVC1G14 1.5–4.6 ns bei 3.3 V, 1.6–5.5 ns bei 2.5 V: `TI_SN74LVC1G14_Datasheet_SCES218AA.pdf` S.8 Tab. 5.6). Schaltschwellen-Dynamik und Flankensteilheit über 20 MHz sind nicht modelliert | D3/C quantitativ unsicher |
| A-7 | Ersatzschaltbild quasistatisch. Gegen die komplexe 2D-FEM bei 70 MHz: +5.2/+21.8 statt +5.1/+20.9 %-Punkte (Teil 0). Leitungseffekte (Elektrode 76 mm, λ/4 im nassen Substrat ≈ 0.2–0.4 m bei 50–100 MHz) und Induktivität der Zuleitung fehlen. Über ≈ 50 MHz ist das Modell daher optimistisch | C |
| A-8 | Maxwell-Wagner-Dispersion im Substrat ist nicht modelliert (REPORT Kap. 9) und verschärft alle Varianten bei niedriger Frequenz | alle |

## 2 Variante A – Status quo 2–6 MHz (R 10 kΩ, ratiometrisch mit Cref1)

**A1 Anzeige über der Feuchte** (Kalibrierung: trocken θ 0.05, nass θ 0.398 mit Leitungswasser):

| θ | Index verlustfrei | Leitung | low | normal | low konz. | normal konz. |
|---|---|---|---|---|---|---|
| 0.05 (trocken) | 0 | 0 | 0 | 0 | 0 | 0 |
| 0.10 | 9 | 3 | 44 | 87 | 108 | 120 |
| 0.15 | 22 | 7 | 96 | 114 | 118 | 125 |
| 0.198 (Mitte, ε' 10) | 36 | 31 | 111 | 121 | 121 | 127 |
| 0.30 | 68 | 81 | 122 | 127 | 124 | 128 |
| 0.398 (nass) | 100 | 100 | 126 | 129 | 126 | 129 |

- Salzfehler trocken/Mitte/nass (low/normal): **0/0 · +80/+91 · +26/+29 %-Punkte**. Spanne C_mess 13.3 → 83.8 pF,
  davon ≈ 2/3 aus der Leitfähigkeit. Auch mit Leitungswasser ist der trockene Bereich gestaucht: θ 0.05–0.15 ergibt nur 0–7 %.
- **A2 Giess-Schwelle 30 %:**

  | Fall | Hinweis bei θ | Leitungs-Index dort | Zeitpunkt im Trocknungszyklus (A-5) |
  |---|---|---|---|
  | Leitungswasser 0.035 | 0.197 | 30 % | 1.00 |
  | Leitungswasser 0.031 / 0.036 | 0.210 / 0.194 | 39 / 28 % | – |
  | 0.072 (KLZH-Einzelprobe) / 0.10 | 0.137 / 0.118 | 5 / 4 % | – |
  | low / normal | 0.094 / 0.076 | 2 / 1 % | **1.51 / 1.60** |
  | low / normal konzentrierend | 0.063 / 0.059 | 0 / 0 % | ≈ 1.7 |
  | **Leitungswasser konzentrierend** | **0.106** | 3 % | 1.45 |

  Die Schwellen 20 % und 40 % zeigen dasselbe Bild (1–3 %). Der Fehler wirkt also **genau dort, wo die Giess-Schwelle
  liegt**: Der Hinweis kommt erst bei fast trockener Erde, und Trend/Prognose sehen bis dahin eine flache Kurve über 100 %.
- **A3 Nass-Kalibrierung im eigenen gedüngten Topf hilft nicht:** Nach einer Kalibrierung mit „low“ oder „normal“ löst
  der Hinweis bei Leitungswasser-Zustand bei 38–39 % aus, bei gedüngtem Zustand weiterhin bei 1–3 %. Auch die
  automatische Nachführung des Nasspunkts nach jedem Giessen (Diagonale) ergibt 2–3 %.
- **A5 Gelernte Schwelle** („gegossen“-Taste speichert die Anzeige): Sie stimmt nur, solange der Salzzustand gleich bleibt.
  Gelernt bei „normal“ und gemessen bei „low“ löst der Hinweis bei θ 0.29 aus, also zu früh (Gefahr Übergiessen).
  Gelernt bei „low“ und gemessen nach Auswaschen mit Leitungswasser löst er dauernd aus.
- **A4 Salzerkennung über f2 (Cref2):** Das Verhältnis C(T0,T2)/C(T0,T1) ist nicht eindeutig. Mitte: Leitung 1.154,
  low 1.024, normal 1.011. Gesättigte, salzige Erde sieht damit „verlustfrei“ aus. **Cref2 bringt keinen Nutzen.**
  Brauchbar ist nur die Zeitreihe: C_mess > 65 pF (über dem verlustfreien Maximum Wasser 64.6 pF) mehrere Tage nach
  dem Giessen bedeutet salzig.
- Energie, Kosten, Fläche, Pins: unverändert. Aufwand: keiner.

## 3 Variante B – mehrere Frequenzen + Ersatzschaltbild-Inversion

- Unbekannte: k (R, Schwellen), ε', σ_b. Die Unsicherheiten nach der Kalibrierung (ANNAHME) werden linear fortgepflanzt:
  Ci/C0/Cg je 2 % (Fit-Residuum 1–2 %), Cpar 0.3 pF, Cref 1 %, VT± 1 %, 2 tpd 1 ns. Strukturfehler (A-7, A-8) fehlen,
  das Ergebnis ist also eine Untergrenze.

| Fall (1 σ Indexfehler, %-Punkte) | B1 vorhandene HW (R10k, +Cref1, +Cref2) | B2 + SN74LVC1G66 (R10k, +Cref1, R5k) |
|---|---|---|
| θ 0.08, Leitung / low / normal | 1.9 / 1.9 / 10 | 1.9 / 1.9 / 2.6 |
| θ 0.12 (Schwelle), Leitung / low / normal | 2.0 / **56 / 323** | 2.0 / **128 / 306** |
| Mitte, Leitung / low / normal | 4.5 / 577 / 2554 | 2.2 / 482 / 1820 |
| nass, Leitung / low / normal | 173 / 5076 / 21524 | 351 / 3390 / 13744 |

- Ursache: Bei f ≪ f_rel = σ_b/(2π ε0 ε') steckt ε' nur noch mit (f/f_rel)² im Messwert (low/normal: f_rel 24–70 MHz).
  Der grösste Beitrag ist überall Ci. Selbst mit 0.2 % Ci blieben bei „normal“ an der Schwelle ≈ 30 %-Punkte.
- B2: +0.17 USD/Stk, +3.07 USD je Bestellung (1 Extended), Band +0.8 mm, DIO11 statt Cref2.
  Analogschalter `TI_SN74LVC1G66_Datasheet_SCES323R.pdf` S.7 Tab. 5.5 (ron 7.5/15 Ω bei 3 V). **Verworfen.**

## 4 Variante C – hohe Messfrequenz 50–100 MHz

**C1 Physikalische Obergrenze** (ideale Messung C_eff = Im(Y)/ω, Ersatzschaltbild 3D):

| f [MHz] | Mitte low / normal | nass low / normal | Güte Sonde nass, normal |
|---|---|---|---|
| 6 | +69 / +163 | +147 / +187 | 5.6 |
| 20 | +10 / +41 | +57 / +148 | 2.1 |
| 50 | +1.8 / +7.5 | +11 / +44 | 1.9 |
| 70 | **+0.9 / +3.9** | +5.9 / +24 | 2.2 |
| 100 | +0.4 / +1.9 | +2.9 / +12 | 2.9 |

**C2 Realisierung** (Pierce: SN74LVC1GU04 + 220 nH + 47 pF + Sonde, ratiometrisch mit Cref1, ÷16):

| ro [Ω] | tpd [ns] | f Luft/trocken/nass [MHz] | Mitte low / normal | nass low / normal |
|---|---|---|---|---|
| 30 | 0 / 1.1 / 3.7 | 99/92/78 · 88/81/65 · 74/68/53 | −9/−25 · −1/−1 · +12/+30 | −31/−50 · −6/−5 · +16/+43 |
| 100 | 0 / 1.1 / 3.7 | 94/87/73 · 89/82/67 · 69/66/55 | 0/−5 · 0/0 · +17/+34 | −12/−17 · +4/+16 · +30/+65 |

- Ursache: Bei einer Güte der Sonde ≈ 2 verschiebt jeder Phasenfehler φ im Regelkreis die Frequenz um ≈ tan φ/Q.
  Für ≤ 5 %-Punkte müsste φ ≲ 4° bleiben, und zwar über VDD 2.4–3.0 V und 10–35 °C. tpd 1.1–3.7 ns entspricht bei
  100 MHz 40–130° (`TI_SN74LVC1GU04_Datasheet_SCES215Y.pdf` S.7 Tab. 6.6). Mit Logikgattern ist das nicht erreichbar.
  Ein diskreter HF-Oszillator wäre denkbar, ist aber nicht recherchiert.
- **Bauteile (JLC 2026-11-07):** SN74LVC1GU04DCKR C485082 Ext, Lager 3895, 0.082 USD @50 · SDCL1005CR22JTDF 220 nH
  C18834 Ext, Lager 17 641, 0.014 USD (Q min 8 bei 100 MHz, SRF ≥ 450 MHz, `Sunlord_SDCL1005-Serie…` S.2) ·
  4 × SN74LVC1G80DCKR C473331 Ext, Lager 8059, 0.211/0.169 USD @1/@50 (fclock ≤ 160 MHz, S.6 Tab. 5.6; Cpd 25 pF, S.8) ·
  AO3401A C15127 Basic als Lastschalter.
- **Strom × Zeit:** Teiler 15.2 mA + Oszillator 8.5 mA (davon 5 mA Querstrom ANNAHME, nicht spezifiziert) = **24 mA**,
  24 × 0.6 ms → 341 µC je Messung. Laufzeit 17.0 → 16.9 Monate (pess. DS). Einbruch 71 mV je Burst an 200 µF.
  DIO12 ist nur für 10 mA spezifiziert, daher ist ein Lastschalter nötig.
- **Fläche/Kosten:** Courtyard +58 mm² → **Band +4.4 mm**, +1.04 USD/Stk, +9.21 USD je Bestellung (3 neue Extended-Typen).
  Pins: keine neuen (DIO11 als Gate, Cref2 entfällt).
- **Linearität:** f ∝ 1/√(C·C2/(C+C2)). Luft→nass nur −21 % Frequenz, die Auflösung genügt trotzdem (Reziprokzählung 48 MHz).
- **Layout/EMV:** Die 76-mm-Elektrode mit Zuleitung strahlt bei 65–99 MHz, also im UKW-Rundfunkband.
  Störaussendung nach RED/EN 301 489 = PROTOTYP-PRÜFUNG. Die Messung dauert nur ms. Leitungseffekte siehe A-7.

## 5 Variante D – weitere Ideen

| Idee | Ergebnis | Urteil |
|---|---|---|
| D1 dickere Isolation 7628C / Interdigital / GSG-7628C (FEM, 2 MHz) | Mitte +64/+74 · +52/+59 · +46/+51 %-Punkte; Spanne −38 % (7628C), FR4-Drift Interdigital 19.6 % | reicht bei weitem nicht |
| D2 Nasspunkt nach jedem Giessen nachführen | Hinweis bei Leitungs-Index 2–3 % (A3, Diagonale) | wirkungslos |
| **D3 RC schneller + Teiler** (R3 kleiner, ÷2…÷16 SN74LVC1G80) | siehe Tabelle unten | **empfohlen** |
| D4 Leitfähigkeit über separaten DC-/NF-Pfad | ohne freiliegendes Metall nur kapazitiv möglich. Unterhalb von f_rel misst jede Isolationskopplung nur noch „Ci kurzgeschlossen“ und liefert keine zusätzliche Information (Kap. 3) | verworfen |

**D3 Sweep** (tpd im Regelkreis, Schwelle 30 %, Leitungs-Index beim Auslösen; Soll 30):

| R3 | Teiler | f Luft / nass [MHz] | Mitte Leit./low/normal [%] | low | normal | 0.072 / 0.10 / low konz. / normal konz. | tpd-Drift [%-P/ns] |
|---|---|---|---|---|---|---|---|
| 10 k (= A) | – | 5.3 / 1.0 | 31 / 111 / 121 | 2 | 1 | 5 / 3 / 0 / 0 | +0.2 |
| 2.2 k | ÷4 | 20.3 / 7.5 | 34 / 133 / 282 | 22 | 11 | 36 / 34 / 5 / 3 | +2.8 |
| 1.5 k | ÷4…÷8 | 27.2 / 11.7 | 35 / 45 / 222 | 32 | 16 | 35 / 40 / 10 / 4 | +4.4 |
| **1.0 k** | **÷8** | **36.1 / 17.4** | **34 / 19 / 119** | **43** | **24** | **33 / 38 / 19 / 7** | **+6.4** |
| 0.68 k | ÷16 | 45.8 / 24.0 | 34 / 19 / 27 | 51 | 34 | 33 / 37 / 36 / 11 | +8.8 |

**D3b Szenario konzentrierend** (A-4, physikalisch plausibel): θ beim Auslösen der 30-%-Schwelle, Bedarf θ 0.197:

| R3 | Leitung | 0.072 | 0.10 | low | normal | Spannweite |
|---|---|---|---|---|---|---|
| 10 k (A) | 0.106 | 0.076 | 0.070 | 0.063 | 0.059 | 0.059–0.106, **immer viel zu spät** |
| **1.0 k** | 0.195 | 0.226 | 0.223 | 0.145 | 0.089 | 0.089–0.226 |
| 0.68 k | 0.195 | 0.223 | 0.244 | 0.205 | 0.112 | 0.112–0.244 |

- R3 1 kΩ: Salzfehler trocken/Mitte/nass (low/normal) **0/0 · −15/+85 · +133/+239 %-Punkte**. An der Schwelle
  −11…+14 %-Punkte, bei „normal konzentrierend“ −23. Der Hinweis kommt im Trocknungszyklus bei 0.82 (low) bzw.
  1.09 (normal) statt 1.51/1.60. Das ist besser als A, erfüllt das Soll aber nicht; bei starker Düngung bleibt der
  Hinweis zu spät.
  C_mess trocken/nass mit Leitungswasser 22.7/44.1 pF (Spanne 21.4 pF, verlustfrei 23.7 pF): Die Kennlinie ist fast
  linear, das nützt Trend und Prognose auch ganz ohne Dünger.
- Nebeneffekt: Bei „low“/„normal“ liegt die Anzeige direkt nach dem Giessen bei 233/339 % statt 100 %. Das ist ein
  **Indikator für starke Düngung**, anders als bei A (Kap. 2, A4). Bei σ_p 0.072/0.10 sind es nur 93/114 %.
- Die Fehler wechseln je nach R und tpd das Vorzeichen. Auch C2 zeigt diese Empfindlichkeit, die Zahlen sind also
  modellabhängig (A-6) → **PROTOTYP-PRÜFUNG**.
- tpd-Drift +6.4 %-Punkte/ns: Über die Lebensdauer (VDD 3.0 → 2.4 V) verschiebt sich tpd bis ≈ 1 ns je Flanke
  (Datenblatt-Grenzen S.8). Nötig ist eine Korrektur über VDD (Batteriemonitor) und Temperatur (TMP1075),
  Koeffizienten am Muster bestimmen → **PROTOTYP-PRÜFUNG**. REQ-MES-05: Bei ≈ 0.01 ns/K (ANNAHME) bleibt das klein.
- Strom 10.2 mA (Cpd LVC1G14 22 pF S.8 Tab. 5.8, LVC1G80 25 pF S.8 Tab. 5.11), 16 × 0.6 ms → 98 µC je Messung,
  Laufzeit 17.0 Monate (unverändert). Wegen der DIO12-Grenze von 10 mA empfiehlt sich ein P-FET (AO3401A, Basic, gleicher
  Typ wie Q1) mit Gate an DIO11 und 100 kΩ Pull-up. Cref2/C23 entfällt (bringt nichts, A4), DIO11 wird damit frei.
  DIO11 ist im ROM-Bootloader SPI-CS (TRM S.464); der Pull-up hält den FET aus.
- Teiler: SN74LVC1G80DCKR C473331 (Extended, Lager 8059), Q ist invertiert (S.13 Tab. 7-1) → D an Q = ÷2 je Stufe.
  Pins D1/CLK2/GND3/Q4/VCC5 (S.3), fclock ≤ 160 MHz (S.6). 36 MHz/8 = 4.5 MHz am Timer, schnelle Ecke (tpd min)
  ≈ 5.5 MHz → ≤ 8 MHz eingehalten. Statische ICC bis 10 µA (S.6) → nur geschaltet versorgen.
- Fläche/Kosten: Courtyard +45 mm² → **Band +3.4 mm** (ohne P-FET +2.2 mm); +0.756 USD (+0.62 CHF)/Stk,
  +3.07 USD je Bestellung (1 neuer Extended-Typ). Serie ≈ 7.34 → 7.96 CHF (REQ-FAB-04 erfüllt).
  Flächenspar-Alternative: R3 1.5 kΩ mit ÷4 (2 FF), −0.7 mm, dafür Schwellenfehler −20…+10 %-Punkte.
- EMV: 17–36 MHz plus Oberwellen, nur in ms-Bursts → PROTOTYP-PRÜFUNG wie bei C, aber unterhalb des UKW-Bands.

## 6 Vergleich und Empfehlung

| | A Status quo | B1/B2 Inversion | C LC 70–100 MHz | **D3 RC 1 k + ÷8** |
|---|---|---|---|---|
| Salzfehler trocken (low/normal) | 0 / 0 (ε_off 3: bis +64) | – | 0 / 0 | 0 / 0 |
| Salzfehler Mitte | +80 / +91 | 1 σ ≥ 480 | ideal +1/+4, real −25…+34 | −15 / +85 |
| Salzfehler nass | +26 / +29 | 1 σ ≥ 3000 | ideal +6/+24, real −50…+65 | +133 / +239 |
| **Giess-Schwelle 30 %** (Leitungs-Index beim Auslösen) | **0–5 %** (Leitung konz.: 3 %) | unbrauchbar | modellabhängig | **19–44 %** (normal konz.: 7 %) |
| Linearität Leitungswasser | S-förmig, trocken gestaucht | wie A | gut | **fast linear** |
| Spanne / f | 13→84 pF / 5.3→1.0 MHz | wie A | 99→78 MHz | 23→44 pF / 36→17 MHz |
| Energie/Messung, Laufzeit pess. DS | 30 µC, 17.0 Mt. | 30–62 µC, 17.0 | 341 µC, 16.9 | 98 µC, 17.0 |
| Stückkosten-Delta | 0 | 0 / +0.14 CHF | +0.85 CHF | **+0.62 CHF** |
| Einmal-Delta je Bestellung | 0 | 0 / +3.07 USD | +9.21 USD | +3.07 USD |
| Band (Kopf) | 0 | 0 / +0.8 mm | +4.4 mm | +3.4 mm (+2.2 ohne FET) |
| Pins | – | – / DIO11 | DIO11 (Gate) | DIO11 (Gate), Cref2 entfällt |
| Risiko | Nutzen bei Dünger stark eingeschränkt | Physik verhindert es | Pulling, UKW-EMV, Layout | Modell > 20 MHz, tpd-Drift |
| Aufwand | – | Firmware | Schaltung + HF-Layout + EMV | 4 Teile, Firmware-Korrektur |

**Empfehlung: D3 in Rev A, A-Modus per R3 umrüstbar, dazu A+ in Firmware und App.**

Begründung aus Sicht des Auftraggebers:
1. **„Giessen nötig“:** Mit A kommt der Hinweis bei gedüngten Pflanzen um ≈ 50–60 % des Trocknungszyklus zu spät.
   Schon härteres Leitungswasser oder Salzanreicherung über Monate verschiebt ihn. Das trifft genau den Hauptnutzen.
   Mit D3 kommt der Hinweis bei θ 0.145–0.226 (Bedarf 0.197), nur bei starker Düngung mit Aufkonzentration bei 0.089.
   A liegt in diesem Szenario bei 0.059–0.106, also immer viel zu spät.
2. **Trends und Prognose:** D3 macht die Leitungswasser-Kennlinie linear. A hat im trockenen Drittel kaum
   Auflösung (θ 0.05–0.15 → 0–7 %). Bei A ist die Kurve gedüngt flach über 100 %, eine Prognose erkennt dann nichts.
3. **Gelegentliche Düngung:** Mit D3 zeigt starke Düngung (≥ „low“) direkt nach dem Giessen eindeutig an
   (Anzeige 233–339 % statt 100 %). Die App kann dann den Hinweis „Dünger erkannt – Anzeige im nassen Bereich unsicher“
   geben. Leichte Düngung (σ_p 0.07–0.10: 93–114 %) ist nicht sicher erkennbar.
4. **Kosten/Energie:** +0.62 CHF/Stk, Laufzeit unverändert. Im Budget (7.96 von 10 CHF).
5. **Granulat:** Für keine Variante liegen Daten vor. D3 und A lassen sich am selben Muster vergleichen.

**A+ (Firmware/App, für jede Variante, 0 CHF):** Taste „gedüngt“ im Giess-Tagebuch. Salz-Hinweis aus der Zeitreihe
(A: C_mess > 65 pF noch Tage nach dem Giessen; D3: Spitze nach dem Giessen > 130 %, ANNAHME-Schwelle, am Muster festlegen). Gelernte Schwelle nur innerhalb
desselben Salzzustands verwenden (A5). Empfehlung in der App: gelegentlich mit klarem Wasser durchspülen.
Messung in Bursts ≤ 0.6 ms mit Pausen.

**Offene Prüfungen (PROTOTYP-PRÜFUNG, Becherversuch OP-K3 früh):** REQ-MES-11 mit Leitungswasser/low/normal bei
3 Feuchten in Erde und Granulat, je R3 1 kΩ und 10 kΩ. tpd-Drift über VDD 2.4–3.0 V und 10–35 °C. Strom und
VOH an DIO12. Störaussendung. Empfehlung zusätzlich: ein **Testpad PROBE_SENSE** (B-Seite) für eine VNA-Messung der
echten Sonde 1–150 MHz (prüft Ersatzschaltbild, Maxwell-Wagner und den Nutzen von C), ≈ +0.5 pF Cpar.

**Freigaben:** Auftraggeber: Kopfhöhe (+3.4 mm, bzw. +2.2 mm ohne FET, zusätzlich zur Option f in FLOORPLAN_OPTIONS)
sowie REQ-MES-11 (Soll) bis zum Nachweis „nicht erfüllt“. Mechanik: Band-Höhe. Firmware: PINMAP-Änderung
DIO11 (OSC_EN_N statt CREF2_CTL), Zählung über ÷8, tpd-Korrektur. Nach dem Entscheid PINMAP, `parts.py`, CONCEPTS 2.3
und PROBE_CAPACITANCE Kap. 4 nachführen.

## 7 Quellen (lokal)
- Neu: `docs/datasheets/TI_SN74LVC1G80_Datasheet_SCES221T.pdf`, `TI_SN74LVC1GU04_Datasheet_SCES215Y.pdf`,
  `TI_SN74LVC1G66_Datasheet_SCES323R.pdf`. Register: `docs/datasheets/_staging/INDEX_salz.csv`.
- Bestehend: `TI_SN74LVC1G14_Datasheet_SCES218AA.pdf` S.8, `Sunlord_SDCL1005-Serie_Datasheet_LCSC-2023-10.pdf` S.2,
  `AOS_AO3401A_Datasheet_Rev3.1.pdf`, `TI_CC2340R5_Datasheet_SWRS272F.pdf` S.31 (VOH), TRM S.464/481.
- Preise und Lager: `docs/concepts/bom/jlc_prices.json` (neue Einträge C473331, C485082, C18834, C113518; JLC 2026-11-07).
- Energie: `scripts/energy_budget.py`, `scripts/concept_energy.py` (A-32, CR2032, 2 × 100 µF, 1 min, Q_MEAS gepatcht).
- Fläche: Courtyards aus `hardware/sensor/gen/floorplan_options.py` (KiCad 10), Faktor 1.5.
