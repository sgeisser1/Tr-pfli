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
| S-Zuleitung | nur L2, L3 darunter GND | 0.3 breit bei x −4.9, Abstand zum Guard 0.3 |

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
