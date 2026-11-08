# Schnittstelle Sonde ↔ Schaltplan/SPICE: Sondenkapazität und Ersatzschaltbild

| | |
|---|---|
| Stand | 2026-11-07, Phase 4a Welle 1 (Feldsimulation); nachgeführt 2026-11-08 auf Layout Rev B/C (REPORT Kap. 11): C0 7.3 pF, Knoten ≈ 9.9 pF |
| Quelle | `simulation/field/` (Skripte `probe3d.py`, `probe3d_post.py`, `study2d.py`, `salt.py`); Werte reproduzierbar |
| Geometrie | Empfehlung `sg` (S/G koplanar 7.75/2/7.75 mm auf L2+L3, S z = 10…86 mm, G-Steg 88…90, Guard bis 8 mm), Skizze `simulation/field/plots/sketch_electrodes.png` |
| Gilt für | JLC04161H-7628, 1.6 mm, Lötstopplack 30 µm, Sonde 20 mm breit, 105 mm unter der Dichtlinie |

## 1 Anschluss
Zweipol zwischen **S** (Eingang Schmitt-Inverter, Knoten mit R und Cref) und **GND**. Die Werte enthalten **nicht**
die Pin-/Leiterbahnkapazität im Kopf (Layout Rev B/C: ≈ 9.9 pF, Kap. 3; vorher CONCEPTS 2.3: 10 pF **ANNAHME**) und keine Cref.

## 2 Kapazitäten (verlustfrei, σ = 0)

| Zustand (Substrat ab Stecktiefenmarke z = 5 mm) | **C_Sonde [pF] Bestwert** (h → 0) | 3D h = 0.8 / 1.0 / 1.4 |
|---|---|---|
| Luft | **8.7** | 9.05 / 9.26 / 9.85 |
| trocken (ε' 4) | **13.6** | 14.06 / 14.30 / 14.97 |
| Mitte (ε' 10) | ≈ 21.7 | – / 22.56 / 23.34 |
| nass (ε' 25) | **36.7** | 37.29 / 37.65 / 38.59 |
| Wasser (ε' 80) | **64.9** | 65.65 / 66.10 / 67.28 |
| überflutet bis Dichtlinie (ε' 25) | ≈ 37.7 | – / 38.67 / 39.65 |
| FR4 feuchtegesättigt (Er +10 %): Δ Luft / Δ Wasser | +0.7 / +3.4 | (h = 1.0) |

Bestwert = Richardson-Extrapolation aus drei Netzen (Konvergenzordnung p ≈ 2, `simulation/field/conv3d.py`,
`results/probe3d_convergence.json`); h = 1.0 liegt 2–7 % darüber. Der Mittelteil stimmt mit dem validierten
2D-Modell überein. Modellunsicherheit der Absolutwerte (Material, Kopf vereinfacht, Prepreg ± 10 %) **≈ ± 10 %**.
Für R/Cref zusätzlich Exemplar- und Steckstreuung berücksichtigen (Luftspalt 0.1 mm → Spanne −37 %).

## 3 Ersatzschaltbild mit Leitfähigkeit (für SPICE)

```
 S ──┬───────── C0 ─────────┬── GND
     └── Ci ──┬── Cs ──┬────┘
              └── Rs ──┘
 C0 = 7.3 pF   Ci = 99 pF   Cs = ε'·Cg   Cg = 1.71 pF   Rs = ε0/(σ_b·Cg) = 5.15 Ω·m / σ_b
```
**Stand Layout Rev B/C (2026-11-08, `simulation/field/REPORT.md` Kap. 11.3):** C0 7.30 pF, Ci 99.1 pF, Cg 1.711 pF
(bisher 7.05 / 99.0 / 1.719, Wirkung der beiden S-Zuleitungen L2/L3 im Guard). Knotenkapazität PROBE_SENSE ausserhalb
der Sonde **≈ 9.9 pF** (U2 4.5 + TP5 0.5 + Band-Bahnen 0.89 + 4 Vias 0.6 **ANNAHME** + Zuleitung z_f < −15 3.25 +
Breite/Verguss 0.16) statt 10 pF **ANNAHME** + 0.5 pF.
Fit an die Bestwerte (Luft/4/25/80, max. Abweichung 1.1 %, `results/probe_lumped_3d_extrap.json`); die Struktur
ist durch die komplexe 2D-FEM bestätigt (rms 1–2 %). σ_b = Bulk-Leitfähigkeit des Substrats:

| Fall | ε' | σ_b [S/m] | Rs [Ω] |
|---|---|---|---|
| trocken | 4 | ≈ 0 | ∞ |
| nass, Leitungswasser (σ_p 0.035 S/m) | 25 | 0.0092 | 560 |
| nass, gedüngt PourThru „low“ (σ_p 0.18 S/m) | 25 | 0.047 | 109 |
| nass, gedüngt „normal“ (σ_p 0.37 S/m) | 25 | 0.097 | 53 |
| Mitte, Leitungswasser / „low“ | 10 | 0.0026 / 0.0135 | 1960 / 381 |

σ_b = σ_p·(ε' − 4)/80 nach Hilhorst 1998 Gl. 4.16 (`docs/references/WUR_Hilhorst_DielectricCharacterisationOfSoil_Thesis_1998.pdf`,
Druckseite 87), ε_off = 4 **ANNAHME**; Leitungswasser `docs/references/KantonalesLaborZH_Trinkwasser_Aesch_2026-02.pdf` S.2–3;
PourThru-Bereiche Purdue HO-237 Tab. 2 (Webseite).

## 4 Folgen für die Oszillatorauslegung (Verhaltensmodell `simulation/spice/probe_osc/`)
- Mit R = 4.7 kΩ und 10 pF Cpar: Luft ≈ 12 MHz → **über der Zählgrenze** (≈ 10–12 MHz, CONCEPTS 2.3).
  **R ≈ 10 kΩ** (Vorschlag, Welle 2 prüfen): Luft 5.6 MHz, trocken 4.5 MHz, nass ohne Salz 2.2 MHz.
- Mit Leitfähigkeit schwingt der Oszillator im nassen Substrat bei ≈ 0.9–1.0 MHz und misst ≈ C0 + Ci
  (84–104 pF) statt 37 pF; gedüngtes Substrat mittlerer Feuchte erscheint als „nass“ (Index 111 % statt 31 %).
  REQ-MES-11 ist mit dieser Messkette nicht erreichbar (Entscheid offen).
- Cref1 = 22 pF liegt in der Grössenordnung der Spanne (23 pF) – passend. Cref2 = 100 pF entspricht der
  „Salz-Sättigung“ C0 + Ci; als Messbereichsgrenze verwendbar.
- SPICE-Nachweis (Verhaltensmodell, ohne tpd): `simulation/spice/probe_osc/probe_osc.py` → `results.csv`.
