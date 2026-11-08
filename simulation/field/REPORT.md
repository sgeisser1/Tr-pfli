# Feldsimulation Sonde fluidi – Phase 4a, Welle 1

Bearbeiter: Elektronik-Agent, 2026-11-07 (Datei vom Projektleiter aus dem Endbericht des Agenten abgelegt).
Status: Entwurf zur Prüfung. Anforderungen: REQ-MECH-04/06/08/11, REQ-MES-03/06/08/11.
Schnittstelle zum Schaltplan: `docs/interfaces/PROBE_CAPACITANCE.md`. Skizze: `plots/sketch_electrodes.png`.

## 1 Annahmen
- Sonde 20 mm breit (D-010), 1.6 mm dick (D-016).
- L = 105 mm unter der Dichtlinie (z = 0 = Unterkante Kragen, ANNAHME): 5 mm frei, 100 mm im Substrat; Stecktiefen-Markierung bei z = 5.
- Spitze 45°, auf 4 mm abgestumpft (ANNAHME, mit Mechanik prüfen).
- Messung als Zweipol S–GND. Topf r = 50 mm, Rand Neumann (r = 200 mm ändert C' um −0.7 %).
- Elektro-quasistatisch: Wellenlänge 9 m, Skintiefe 0.37 m bei 0.3 S/m, beides ≫ 0.1 m.

## 2 Methode und Validierung
- **2D:** scikit-fem, P2-Elemente, Elektroden als Linien. Gegen konforme Abbildung (koplanare Streifen) −0.01…+0.08 %; 4× feineres Netz ändert C' < 0.03 % (`results/validate2d.txt`).
- **3D:** Elmer StatElecSolveVec, Halbmodell, 26 Substratscheiben für die Füllstandskurve. Netze h = 1.4 / 1.0 / 0.8 mm (0.9 Mio. Knoten), Richardson-Extrapolation p = 2.0–2.1 (`conv3d.py`). Elmer gegen Plattenkondensator: exakt.
- **Achtung:** ElmerGrid nummeriert die Körper fortlaufend; Prüfung jetzt in `probe3d.py`. Ein früher Lauf (`gsg_h2`) war deshalb falsch und ist verworfen und aus dem Repository entfernt.
- **Reproduktion:** `.venv/bin/python simulation/field/{validate2d,study2d [--salt-only],salt,plots2d,probe3d --geo sg --h 1.0,probe3d_post,conv3d,sketch}.py`, `simulation/spice/probe_osc/probe_osc.py`. Elmer nur über `scripts/elmer.sh`.

## 3 Materialwerte
| Grösse | Wert | Quelle |
|---|---|---|
| Prepreg / Kern (Standard 7628) | 0.2104 / 1.065 mm, Er 4.4 | `docs/references/JLCPCB_NOTES.md` Kap. 4 |
| Er Kern | 4.4 | ANNAHME |
| Weitere Prepregs | 1080: 0.076 mm, 2116: 0.116, 7628C: 0.646 | JLCPCB_NOTES Kap. 4 |
| FR4 Df | 0.012–0.015 (1–10 MHz) | DuPont/Khan 1999 S. 5 Tab. 1 |
| FR4 Feuchtesättigung (85/85, 0.68 %) | Dk 4.83 → 5.38 (+11 %, 1 MHz), +9.8 % (10 MHz) | DuPont/Khan 1999 S. 5 Tab. 1 |
| FR4 Temperatur | ≈ +0.1 %/K | DuPont/Khan 1999 S. 5 Tab. 1 |
| Lötstopplack | Er 3.8; 30 µm auf Laminat, 15 µm auf Kupfer | JLC Impedance Guide (2026-09-16) |
| Lack Df | 0.02 | ANNAHME |
| Coating (nur Vergleich) | Er 3.3, 50–125 µm | MG Chemicals 4200UV TDS S. 2 |
| Substrat ε' | Topp: θ 0.05 → 3.8, θ 0.40 → 25.2 | Topp 1980, doi:10.1029/WR016i003p00574 (nicht lokal) |
| Leitungswasser | 307–359 µS/cm | Kantonales Labor ZH 2026-02 S. 2–3 |
| Porenwasser Topf (PourThru) | low 1.0–2.6, normal 2.7–4.6 mS/cm | Purdue HO-237 Tab. 2 (Web) |
| Bulk-Leitfähigkeit | σ_b = σ_p(ε'−4)/80 → nass 0.009 / 0.047 / 0.097 S/m | Hilhorst 1998 Gl. 4.16/4.17, Druckseite 87 |

## 4 Ergebnisse 2D (pro Meter Elektrodenlänge, 4 Lagen 7628, Lack 30 µm)
| Variante | C' Luft / trocken / nass [pF/m] | Spanne [pF/m] | (Cn−CL)/CL | d50 / d90 nass [mm] | Spalt 0.1 / 0.5 mm | FR4 +10 % Luft / Wasser [% Spanne] |
|---|---|---|---|---|---|---|
| **SG 2 mm, Rand 1.25** | 45.6 / 99.5 / 362 | 263 | 6.9 | 1.6 / 8.2 | −37 / −77 % | 1.0 / 12.8 |
| SG 4 mm | 30.6 / 76 / 308 | 231 | 9.0 | 1.9 / 9.1 | −34 / −75 % | 0.6 / 12.2 |
| GSG S 6 / 2 mm | 79 / 153 / 473 | 320 | 5.0 | 0.9 / 3.6 | −46 / −85 % | 1.6 / 14.6 |
| versetzt L2/L3 | 38 / 81 / 249 | 167 | 5.5 | 1.8 / 9.3 | −31 / −71 % | 1.3 / 14.4 |
| Kreuz | 647 / 707 / 996 | 289 | 0.5 | 1.2 / 4.6 | −41 / −82 % | 21.6 / 33.7 |
| Interdigital 6 | 276 / 410 / 828 | 419 | 2.0 | 0.4 / 1.7 | −60 / −92 % | 5.2 / 19.6 |

- Rand zur Kontur 1.0 / 1.25 / 1.5 / 2.0 mm: Spanne 267 / 263 / 259 / 251 pF/m → 1.25 mm (1.0 mm Pflicht + Toleranz).
- FR4-Schnittkante (1 mm Randstreifen): Energieanteil ≈ 1 %.
- Isolationsdicke (SG): Spanne 321 / 303 / 263 / 164 pF/m für 1080 / 2116 / 7628 / 7628C; FR4-Drift 4.6 / 5.5 / 6.9 / 9.1 %. 50 µm Coating zusätzlich: −7 % Spanne. 7628 Standard bleibt (Economic PCBA).
- **2 Lagen + Coating** 20 / 50 / 100 µm: Spanne 373 / 343 / 306 pF/m, FR4-Drift < 1 %, Lackdrift 3.3–5.8 % (ANNAHME), Salzfehler 4 MHz +266 statt +155 %-Punkte, bei Lackschaden freies Kupfer (REQ-MECH-03). **→ 4 Lagen innen bestätigt (REQ-MECH-04).**

## 5 Salz / Dünger (REQ-MES-11)
- Komplexe 2D-FEM, 11 Varianten × ε' {1, 4, 10, 25, 80} × σ_b 0–0.3 S/m × f 1–70 MHz.
- Physik: Oberhalb σ_b ≈ 2πfε0ε'(1 + Ci/Cs) schliesst das leitfähige Substrat seine Kapazität kurz; die Messung sieht dann nur noch die Isolationskapazität Ci (≈ 1300 pF/m, ganze Sonde 99 pF).
- Index-Fehler gegen Leitungswasser-Kalibrierung, nass, gedüngt low / normal [%-Punkte] (`results/salt_index_2d.csv`):

| Variante | 2 MHz | 4 MHz | 6 MHz | 10 MHz | 20 MHz | 70 MHz |
|---|---|---|---|---|---|---|
| SG | +85/+93 | +155/+193 | +164/+236 | +123/+234 | +51/+144 | +5/+21 |
| GSG | +42/+45 | +92/+104 | +113/+141 | +106/+162 | +55/+128 | +6/+25 |
| SG 7628C | +24/+26 | +57/+62 | +76/+89 | +82/+111 | +52/+102 | +7/+26 |
| SG 1080 | +198/+238 | +250/+389 | +202/+396 | +115/+300 | +39/+132 | +4/+15 |
| Interdigital | +18/+19 | +41/+44 | +56/+64 | +65/+83 | +46/+82 | +7/+25 |
| 2L Coating 20 µm | +412/+721 | +266/+671 | +162/+475 | +75/+248 | +22/+84 | +2/+8 |

- Zeitbereich (ngspice, Schmitt-Inverter VT+ 1.68 V / VT− 0.99 V, R 10 kΩ, Cpar 10 pF, Cref1 22 pF, ratiometrisch, 3D-Ersatzschaltbild):

| Fall | f0 [MHz] | C_mess [pF] | Index [%] |
|---|---|---|---|
| Luft | 5.61 | 8.7 | −7 |
| trocken | 4.47 | 13.5 | 0 |
| nass ohne Salz | 2.23 | 37.0 | – |
| nass, Leitungswasser | 1.02 | 83.8 | 100 |
| nass, gedüngt low / normal | 0.92 / 0.91 | 101.9 / 104.0 | 126 / 129 |
| Mitte, Leitungswasser | 1.65 | 35.1 | 31 |
| Mitte, gedüngt low / normal | 0.98 / 0.94 | 91.4 / 98.9 | 111 / 121 |

- **Folgerung:** Keine Geometrie und keine Isolationsdicke erreicht ≤ 5 %-Punkte bei 1–6 MHz. Optionen: (a) Messfrequenz ≥ 50–70 MHz (Kizito 2008) – Konzeptänderung; (b) 7628C bei 2 MHz ≈ +25 %-Punkte, −38 % Spanne, kein Standard-Stackup; (c) Abweichung akzeptieren, Salz über Frequenzabhängigkeit erkennen; (d) früher Becherversuch OP-K3. → Bewertung durch den Projektleiter (Phase 4, offen).

## 6 Ergebnisse 3D (Geometrie SG)
| Fall | h 1.4 / 1.0 / 0.8 [pF] | h → 0 [pF] |
|---|---|---|
| Luft | 9.85 / 9.26 / 9.05 | 8.69 |
| trocken | 14.97 / 14.30 / 14.06 | 13.63 |
| Mitte ε 10 (h = 1.0) | 22.56 | – |
| nass | 38.59 / 37.65 / 37.29 | 36.67 |
| Wasser | 67.28 / 66.10 / 65.65 | 64.87 |
| überflutet bis Dichtlinie (h = 1.0) | 38.67 (+4.4 % Spanne) | – |

- **REQ-MES-08:** 93.2 % aus 10–90 mm (extrapoliert 93.3 %), 6.4 % aus 5–10 mm, 0.4 % unter 90 mm; Füllstandskurve linear ≈ 0.33 pF/mm (`plots/3d_fill.png`). ✅
- Varianten (h = 1.4): sg_long +5 % Spanne, 87 % REQ-MES-08; gsg +16 % Spanne, 96 %, FR4-Drift 3.4 / 16 %.
- Ersatzschaltbild (h → 0): C0 7.0 pF, Ci 99 pF, Cg 1.72 pF pro ε-Einheit; Rs = 5.15 Ω·m / σ_b. Absolutwerte ±10 %.

## 7 Drift
- FR4-Feuchte (Er +10 %): Luft +0.70 pF (3.0 % Spanne), Wasser +3.4 pF (14.5 %), nasses Substrat (2D) 4.2 % → REQ-MES-06 ohne Vorkonditionierung verletzt.
- Massnahmen: vor der Kalibrierung ≥ 14 Tage wässern (PROTOTYP-PRÜFUNG: Sättigung, Reversibilität), Kanten versiegeln, REQ-MES-06 nach Vorkonditionierung messen.
- Temperatur: FR4-Anteil 0.04 %-Punkte/K, klein gegen 0.3 %-Punkte/K (REQ-MES-05).

## 8 Layoutvorgaben (Empfehlung SG)
| Element | Lage | Masse [mm] |
|---|---|---|
| S | L2 + L3 | x −8.75…−1, z 10…86 |
| G | L2 + L3 | x +1…+8.75, z Kopf…90 |
| G-Steg | L2 + L3 | volle Breite (±8.75), z 88…90 |
| Guard | L2 + L3 | volle Breite, Kopf…z 8, Kanal für die S-Zuleitung |
| S-Zuleitung | Empfehlung: nur L2, L3 darunter GND. **Layout Rev B/C: L2 x −8.0 + L3 x −7.0** (zweite Zuleitung für S auf L3, Kap. 11) | je 0.3 breit, Kanal zum Guard 0.3 |

- Vias zwischen L2 und L3 nur im Kopf (z < −3); z 0–2 ohne Vias; für z > 0 L1/L4 ohne Kupfer, keine Vias.
- Kupfer ≥ 1.25 mm von der Kontur, auch an der Spitze. Silkscreen Stecktiefe bei z = 5.
- Oszillator: R ≈ 10 kΩ (mit 4.7 kΩ läge f in Luft bei ≈ 12 MHz, über der Zählgrenze); in Welle 2 mit tpd/Cpd nachrechnen. `simulation/spice/osc/` rechnet noch mit 30/100 pF → auf PROBE_CAPACITANCE.md umstellen.

## 9 Unsicherheiten / PROTOTYP-PRÜFUNGEN
- Topp gilt für mineralische Böden; Torf/Granulat weichen ab. Maxwell-Wagner-Effekt (Hilhorst Kap. 2.4) nicht modelliert – verschärft Kap. 5.
- σ-Werte sind eine Spanne. FR4-Feuchte nur 85/85-Messung statt Wasserlagerung. Prepregdicke ±10 % (→ Spanne ±3 %).
- Kopf vereinfacht, Cpar 10 pF ANNAHME, SPICE ohne tpd.
- Becherversuche REQ-MES-08 und REQ-MES-11, Mehrfachstecken (Luftspalt) am ersten Muster.

## 10 Quellen
- `docs/references/JLCPCB_NOTES.md`; JLC Impedance Calculator Guide (https://jlcpcb.com/help/article/User-Guide-to-the-JLCPCB-Impedance-Calculator)
- `docs/references/DuPont_Khan_DkDf_Aramid-vs-GlassFR4_1999.pdf`
- Topp et al. 1980, doi:10.1029/WR016i003p00574 (nicht lokal)
- `docs/references/WUR_Hilhorst_DielectricCharacterisationOfSoil_Thesis_1998.pdf` (https://edepot.wur.nl/202070)
- `docs/references/KantonalesLaborZH_Trinkwasser_Aesch_2026-02.pdf`
- Purdue HO-237 (https://ag.purdue.edu/department/hla/extension/extension-publications-library/ext-pubs/ho-237-w.html)
- `docs/references/MGChemicals_4200UV_TDS.pdf`; Kizito et al. 2008 (siehe `docs/concepts/research_elektronik.md` [L1])
- Register: INDEX.csv REF-FLD1…4

## 11 Nachtrag Layout Rev B – S-Zuleitungen (Befund L-3)

Bearbeiter: Elektronik, 2026-11-08. Status: Entwurf zur Prüfung. Anlass: `hardware/sensor/out/LAYOUT_REV_B.md` Kap. 3/9 (L-3, L-6).
**Reproduktion:** `.venv/bin/python simulation/field/probe3d_revb.py --var {alt,revb} --h {1.4,1.0}` (Elmer über
`scripts/elmer.sh`, je 2.5 bzw. ≈ 8 min), danach `.venv/bin/python simulation/field/leads_revb.py` (≈ 7 min inkl. ngspice)
→ `results/leads_revb.txt` (alle Tabellen), `results/leads_revb.json`, `results/probe3d_revb_*.json`.

### 11.1 Geometrie aus der Platine (pcbnew, nicht aus dem Bericht)
- Zuleitungen /PROBE_SENSE: **L2 (In1) x −8.000, L3 (In2) x −7.000**, je 0.300 breit, Kanal zum Guard 0.300,
  Y 20.50 (Band-Via) … 64.00 (in der S-Fläche), je 43.5 mm. Elektroden, Guard (±8.75 bis Y 61.5), Steg unverändert wie Kap. 8.
- Querschnitte alle 0.05 mm aus den gefüllten Zonen, Bahnen, Pads und Vias (alle Netze ausser PROBE_SENSE = AC-Masse,
  **ANNAHME**: niederohmig während der Messung; U3 ALERT schwebend, nicht modelliert): 196 verschiedene Querschnitte
  zwischen Bandkante und Guard-Ende. Im Fach Guard als Fläche bis ±11.95 (L-6), im Kragenfeld GND-/SENS_PWR-Kupfer
  von U3/C24 auf F über der L2-Zuleitung (SENS_PWR kreuzt bei Y 48.95), Kragen-Vias x −5.0/−8.7.
- Jede Zuleitung liegt seitlich im GND-Kanal, zur anderen Innenlage hin unter/über voller GND-Fläche, **zur Aussenfläche
  hin aber nur unter 0.21 mm Prepreg + Lack** (Aussenlagen sind in Schott/Fach/Kragen/Sonde kupferfrei). Das war im
  bisherigen 3D-Modell genauso: Das Halbmodell (Spiegelung an der Kernmitte) enthielt die Zuleitung bei x −4.875 auf
  **L2 und L3**, nicht „nur L2“ wie in der Tabelle Kap. 8.

### 11.2 Methode und Kontrolle
- 2D (xsec2d, P2) je Querschnitt: C' der Zuleitung(en) für Aussenmedium ε 1/3/4/6/10/25/80 und „leitend“ (ε 1e4, schwebend),
  dazu FR4-Empfindlichkeit. Medien je Zone: Schott Y 20.8–23.2 (Verguss), Fach 23.2–46.0 (Luft), Kragen 46.0–51.5
  (Verguss ε 4, **ANNAHME**, Typ offen INDEX EP-K, Band 3–6), frei 51.5–58.5 (z_f −2…5), Erde 58.5–61.5 (Guard im Substrat).
- 3D-**Vollmodell** (`probe3d_revb.py`, ohne Symmetrie in der Dicke, sonst Netz/Fälle wie `probe3d.py`): Variante `alt`
  reproduziert das Halbmodell Kap. 6 (h 1.4: Luft 9.853 statt 9.852, nass 38.598 statt 38.593 pF). Neue Werte =
  Richardson-Werte Kap. 6 + Differenz revb − alt bei h 1.0 (h 1.4 und 1.0 stimmen auf ≤ 0.015 pF überein).
- Anteile ausserhalb des 3D-Modells (Kopf z_f < −15, reale Breite 26 mm, Verguss) aus 2D → Knotenkapazität.

### 11.3 Ergebnisse alt vs. neu
| Grösse | bisher | Rev B | Bemerkung |
|---|---|---|---|
| C' beide Zuleitungen im Guard, Luft [pF/m] | 170.4 (Modell L2+L3 x −4.875); 92.5 (Kap. 8, nur L2) | **180.2** (Fach 180.8) | 2D |
| Kopplung nach aussen ε 1 → 80 [pF/m] | 73.2 (Modell); 36.0 (Kap. 8) | **70.4** | Mass für Fehlerquelle 11.4 |
| Zuleitung Y 20.8–61.5, Betrieb (Fach Luft, Verguss ε 4) [pF] | 7.08 (Modell-Lage); 3.84 (Kap. 8) | **7.54** | Verguss ε 3/6: 7.56/7.65 |
| Sonde C Luft / trocken / nass / Wasser [pF] (ab z_f −15) | 8.69 / 13.63 / 36.67 / 64.87 | **8.93 / 13.86 / 36.84 / 65.04** | +0.18…0.24 pF |
| Spanne trocken → nass [pF] | 23.03 | **22.99 (−0.2 %)** | |
| Ersatzschaltbild C0 / Ci / Cg [pF] | 7.05 / 99.0 / 1.719 | **7.30 / 99.1 / 1.711** | Fit max 1.1 % |
| REQ-MES-08 Anteil 10–90 mm (h 1.0) | 93.2 % | **93.3 %** | ✅ |
| FR4 +10 %: Luft / Wasser [% Spanne] (h 1.0) | 2.99 / 14.46 | 3.11 / 14.57 | Kap. 7 unverändert |
| Knoten PROBE_SENSE [pF] | 10.5 (U2 4.5 + Leiterbahn/Durchführung 5.5 **ANNAHME** + TP5 0.5) | **9.9** = U2 4.5 + TP5 0.5 + Band-Bahnen 0.89 (2D, 10.7 mm) + 4 Vias 0.6 (**ANNAHME** 0.15 je Via) + Zuleitung z_f < −15 3.25 + Breite/Verguss 0.16 | Zuleitung alte Lage dort 3.06 |
| Anteil Zuleitungen (Y 20.8–61.5) an der Gesamt-C Knoten+Sonde | – | **40 % Luft, 32 % trocken, 16 % nass** (7.5 von 18.8 / 23.7 / 46.7 pF) | konstant → Offset, Kalibrierung |

**Messkette D3** (`osc_sim.py`-Netzliste mit neuem C0/Ci/Cg und Knoten 9.9 pF, ngspice; Repo-Dateien unverändert):
| Fall (R3 1 kΩ) | f_osc bisher [MHz] | f_osc Rev B [MHz] | MEAS_CLK Rev B [MHz] |
|---|---|---|---|
| Luft / trocken / Mitte / nass / Wasser (typ, 3.0 V, Leitungswasser) | 27.43 / 24.24 / 20.25 / 14.91 / 9.75 | **27.72 / 24.47 / 20.43 / 15.02 / 9.80** | 3.47 … 1.22 |
| schnellste Ecke Luft (hyst_min, 3.0 V) | 36.05 | **36.44** | **4.56** |
| langsamste Ecke (nass gedüngt normal, hyst_max, 2.4 V, mit Cref1) | 4.75 | **4.76** | **0.595** |
| R3 10 kΩ: Luft schnell / gedüngt langsam | 5.18 / 0.52 | 5.26 / 0.52 | 0.657 / 0.065 |

Alles im zählbaren Bereich: Firmware-Plausibilität 0.048–12 MHz am Pin (`firmware/sensor/core/fl_meas.h`, `fl_meas.c`),
Zählgrenze ≈ 10–12 MHz (**ANNAHME**, PINMAP), LVC1G80 fclock ≤ 160 MHz. Die Frequenz steigt leicht (+0.2…+1.4 %), weil die
gerechneten Band-/Fach-Anteile kleiner sind als die bisherige 5.5-pF-Annahme. Startkalibrierung (D-022, 13.3/40 pF)
verschiebt sich um ≈ −0.4 pF (≈ 2 % der Spanne), REQ-MES-07 nicht berührt.

### 11.4 Feldkopplung der Zuleitungen ausserhalb der Messzone (Fehlerquelle)
| Fall | Zusatz-C Rev B | % Spanne | bisheriges Modell |
|---|---|---|---|
| Erde nass im Guardbereich z_f 5–8 (normal gesteckt), nur Zuleitung | +0.11 pF (ε 4 → 25) | 0.5 | gleich |
| Zu tief gesteckt / Erde nass bis Vergusskante (z_f −2…5, ε 25), gesamt | +1.08 pF (davon Zuleitung z_f −2…0: 0.11; Zuleitung z_f −2…5 ≈ 0.37) | 4.7 | 4.4 (nur z_f 0…5) |
| Wasser stehend bis Vergusskante (ε 80 / leitend), gesamt | +2.20 / +2.23 pF (Zuleitung z_f −2…5 ≈ 0.49 / 0.60) | 9.4 / 9.6 | 9.1 (nur z_f 0…5) |
| Kragen: Verguss ε 3 … 6 (Typ offen) | ±0.05 pF, konstant | – | – |
| **Fach geflutet** (REQ-SAF-05 Einzelfehler), Wasser / leitend | **+1.65 / +1.98 pF** | **7.2 / 8.6** | +1.69 / +2.02 |
| Kopf-FR4 Feuchte (Zuleitung Schott/Fach/Kragen) je +10 % Dk | +0.53 pF | 2.3 | – |

- Die Zuleitungen verlaufen nirgends ausserhalb des Guards, ausser im Spalt Guard-Ende → S-Elektrode (z_f 8–10), der zum
  Messfeld gehört (im 3D enthalten, REQ-MES-08 93.3 %). Aussenfeld koppeln sie aber über die kupferfreie Aussenfläche
  ein: 70 pF/m für ε 1 → 80. Das ist **gleich wie im bisherigen Modell** (73 pF/m), aber doppelt so viel wie die Tabelle
  Kap. 8 („nur L2“) unterstellte. Die zweite Zuleitung ist ohne Via im nassen Bereich nicht vermeidbar.
- Bewertung: Oberflächenwasser/Überflutung bis zur Vergusskante ist ein Bedienfehler mit +5…10 % Spanne, davon ≈ ¼ aus den
  Zuleitungen; die Überflutungserkennung (REQ-MES-12, über Nasspunkt) bleibt möglich. Fach geflutet zeigt ≈ +7…9 % „nasser“ –
  Einzelfehlerfall, nur im Testplan vermerken. Kopf-FR4-Feuchte: bei Raumklima nur ein Bruchteil der Sättigung
  (**ANNAHME**) → ≤ 1 % Spanne, **PROTOTYP-PRÜFUNG** Luftpunkt bei 30/60 % rF.
- SENS_PWR/C24/U3 über der L2-Zuleitung (Kragenfeld): Kopplung konstant, weil SENS_PWR in den Bursts statisch low ist
  (`firmware/sensor/platform/cc23/fl_hw.c` Burstschleife, Rev B). Diese Regel beibehalten.
- **Option Rev C** (nicht nötig): Zuleitungen 0.15 mm mit Kanal 0.2 mm (JLC ≥ 0.10) senken die Aussenkopplung auf
  30 pF/m (−58 %), C' 176 pF/m; Fach geflutet +0.69 statt +1.65 pF, Zuleitungsanteil bei Wasser bis zur Vergusskante 0.21 statt 0.49 pF (−58 %).

### 11.5 Bewertung
**Layout Rev B ist aus Feldsicht in Ordnung, keine Layoutänderung nötig.** Spanne −0.2 %, Empfindlichkeit (Cg) −0.4 %,
Messvolumen unverändert, Frequenzbereich der Messkette im zählbaren Bereich. Der Guard als Fläche im Fach (L-6) schirmt
die Zuleitungen seitlich vollständig; feldseitig kein Nachteil. Nachzuführen (klein): `docs/interfaces/PROBE_CAPACITANCE.md`
C0 7.0 → 7.3 pF und Knoten 10 → ≈ 9.9 pF (Zuleitung im Fach getrennt ausweisen), `simulation/spice/osc/osc_sim.py` C_NODE,
Tabelle Kap. 8 („S-Zuleitung“: Rev B = L2 x −8.0 + L3 x −7.0, je im Kanal 0.3).
