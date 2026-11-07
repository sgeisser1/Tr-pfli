# fluidi – FEM der Sonde (REQ-MECH-10), Phase 4b

| | |
|---|---|
| Stand | 2026-11-07, Schnittstelle PCB-Kontur Rev A |
| Ersteller | Mechanik-Agent (Modell, Rechnung); Bericht zusammengestellt vom Projektleiter aus `summary.json`, `results.json` und dem Modellkopf in `fem_probe.py` |
| Werkzeuge | FreeCAD 0.21.2 FEM, Gmsh, CalculiX (headless) |
| Neu rechnen | `freecadcmd simulation/fem/fem_probe.py` (ca. 15 min), dann `.venv/bin/python simulation/fem/fem_eval.py` |

## 1 Modell
- Leiterplatte FR4 20 × 1.6 mm, Spitze 45°, von z = −105 mm (Spitze) bis z = 32.0 mm (Schott, eingespannt).
- Vergusskragen z 2.0 … 7.3 mm um die Platine, mit ihr verbunden; Aussenflächen fest (Hülse stützt über den Zapfen an der Kappe).
  Vergusskante bei z = 2.0 mm. Grenzfall LC1b ohne Kragenstütze (nur Schott).
- Netz C3D10, global 1.6 mm, Verfeinerung z −4 … 3 mm bis 0.25 mm; Konvergenz an LC1 geprüft.
- **Werkstoffe:**
  - FR4-Biegefestigkeit ≥ 345 MPa quer / ≥ 415 MPa längs (typ. 446 / 565 MPa): `docs/references/Kingboard_KB-6160A_TechnicalInformation.pdf` S. 1. Gerechnet mit 345 MPa (Faserrichtung unbekannt). Laminat bei JLC = **ANNAHME** (KB-6160-Klasse).
  - FR4 E = 20 GPa, ν = 0.15: **ANNAHME** (Datenblatt ohne Modul; typisch 18–24 GPa).
  - Kragen E = 3 GPa (Epoxid, **ANNAHME**; ASA 2.45 GPa laut `BambuLab_ASA_TechnicalDataSheet_V2.0.pdf` S. 2) – der steifere Wert ist konservativ für die Kerbspannung.

## 2 Ergebnisse

| Lastfall | FEM | Handrechnung | Sicherheitsfaktor | Bewertung |
|---|---|---|---|---|
| LC1 seitlich 10 N an der Spitze (schwache Achse) | 152 MPa 0.5 mm vor der Vergusskante (Kerbfaktor 1.22, konvergiert); Spitzenwert direkt an der Kante 171 MPa (Singularität) | 125 MPa; Durchbiegung 29.9 mm (FEM 30.7 mm) | 2.27 (2.01 an der Singularität, 3.71 typ. Festigkeit längs) | ✅ ≥ 2 |
| LC1b wie LC1, ohne Kragenstütze | 147 MPa, max. 174 MPa | – | ≈ 2.0 | ✅ Grenzfall |
| LC2 seitlich 10 N in der Plattenebene | 30 MPa | 10 MPa | 11.4 | ✅ |
| LC3 axial 50 N Druck (Festigkeit) | 2.5 MPa | 1.6 MPa | 136 | ✅ |
| LC4 Zug 30 N | 1.5 MPa | 0.9 MPa | 227 | ✅ |
| **LC5 Knicken, Spitze frei** | P_cr = **29.0 N** | 29.4 N (π²EI/4L²) | **0.58** gegen 50 N | ❌ |
| LC6 Knicken, Spitze im Boden geführt | P_cr = 236 N | 241 N (2.046 π²EI/L²) | 4.7 | ✅ |
| Fall 1 m, obere Schranke (ganzer Sensor) | 181 MPa (Ersatzkraft 11.9 N) | – | 1.91 (3.13 typ.) | ✅ knapp |
| Fall 1 m, nur Sondenmasse | 97 MPa | – | 3.56 | ✅ |

Handrechnung: L = 107 mm (Spitze bis Vergusskante), W = 20·1.6²/6 = 8.53 mm³, I = 20·1.6³/12 = 6.83 mm⁴.
FEM und Handrechnung stimmen bei Durchbiegung (3 %) und Knicklast (1–2 %) überein; die höhere FEM-Spannung ist die
Kerbwirkung an der Vergusskante.

## 3 Bewertung und Entscheid
- Alle Festigkeitsfälle erfüllen Sicherheitsfaktor ≥ 2 (Fall aus 1 m knapp, obere Schranke).
- **Knicken mit freier Spitze** (Spitze drückt auf etwas Hartes, bevor sie im Substrat geführt ist) verfehlt 50 N.
  Sobald die Spitze im Substrat geführt ist, beträgt die Knicklast 236 N.
- **Entscheid D-016 (Auftraggeber, 2026-11-07):** REQ-MECH-10 gilt für axial 50 N **mit geführter Spitze**; die
  Bedienungsanleitung verlangt, in fester oder verdichteter Erde vorzustechen (z. B. mit einem Holzstäbchen). Keine
  konstruktive Änderung.
- Offen (PROTOTYP-PRÜFUNG): tatsächliche Einsteckkräfte in Erde und Granulat, Faserrichtung/Laminat bei JLC, Fallversuch.

## 4 Nachtrag Rev B (2026-11-07, Schnittstelle PCB-Kontur Rev B, Kopf V4)

**Was sich an der Sonde ändert:** Länge (Spitze z −105 bis Vergusskante z 2.0 = 107 mm), Querschnitt 20 × 1.6, Kragen
z 2.0 … 7.3 und Schott z 30.8 … 32.0 bleiben. Neu sind die Platine 0.8 mm weiter vorn im Kragen (y_F 6.6), der breitere
Kragen (O-Ring-Nutgrund 28.1 × 7.1 statt 22.1 × 7.1), die Schulter 20 → 26 mm über dem Kragen und die höhere Masse
(28.1 g statt 22.1 g, `mechanical/sensor/check_sensor.txt`). Deshalb wurde `fem_probe.py` unverändert neu gerechnet
(Geometrie aus `fluidi_params.py` Rev B). `fem_eval.py` liest die Masse jetzt aus `check_sensor.txt`.

| Lastfall | Rev A | **Rev B** | Handrechnung | SF Rev B | Bewertung |
|---|---|---|---|---|---|
| LC1 seitlich 10 N (z 1.5 / max. an der Kante) | 152 / 171 MPa | **151 / 168 MPa** (Kt 1.21, 254 k Knoten, konvergiert: 1.0/0.5/0.25 mm → 147/154/151) | 125 MPa; u 29.9 mm (FEM 30.7) | 2.29 (2.06) | ✅ unverändert |
| LC1b ohne Kragenstütze | 147 / 174 MPa | **150 / 191 MPa** | Schulter: 10 N × 112.7 mm / 8.53 mm³ = 132 MPa × Kt ≈ 1.45 | 1.81 | ⚠ Grenzfall (siehe unten) |
| LC2 in der Ebene | 30 MPa | 13 MPa | 10 MPa | 25.8 | ✅ |
| LC3 Druck 50 N / LC4 Zug 30 N | 2.5 / 1.5 | 2.3 / 1.4 MPa | 1.6 / 0.9 | 147 / 241 | ✅ |
| LC5 Knicken frei | 29.0 N | **29.0 N** | 29.4 N | 0.58 | ❌ wie Rev A, D-016 gilt |
| LC6 Knicken geführt | 236 N | **236 N** | 241 N | 4.72 | ✅ |
| Fall 1 m, obere Schranke ganzer Sensor | 181 MPa (22.1 g) | **202 MPa (28.1 g)** | σ ∝ √m: 181 × √(28.1/22.1) = 204 | 1.71 (2.79 typ.) | ⚠ unter 2 |
| Fall 1 m, nur Sondenmasse | 97 MPa | 96 MPa | – | 3.59 | ✅ |

- **Schulter:** Ein erster Rev-B-Lauf mit scharfer 135°-Innenecke bei z 7.5 ergab in LC1b eine Spitze von **284 MPa**
  (SF 1.21) an der Ecke direkt über dem Kragen. Die Kontur hat jetzt eine **Innenecke R 2.0** (Tangente ab z 7.67);
  damit 191 MPa. Mit Kragenstütze (Regelfall, LC1) ist die Schulter unkritisch, das Maximum liegt wie in Rev A an der
  Vergusskante.
- **LC1b** (Hülse stützt den Kragen nicht) bleibt Grenzfall wie in Rev A; SF 1.81 gegen den Mindestwert quer, 2.95 gegen
  typisch längs.
- **Fall 1 m:** Die obere Schranke (gesamte kinetische Energie geht in Biegung der Sonde) sinkt wegen der höheren Masse
  unter 2 (1.71, typisch 2.79). Die Schranke ist sehr konservativ (Kopf trifft in der Praxis zuerst oder Energie geht
  in Rotation/Gehäuse). **PROTOTYP-PRÜFUNG** Fallversuch 1 m (seitlich auf die Spitze, auf den Kopf) an 3 Mustern.
- Rohdaten: `results.json`, `summary.json`, `fem_log.txt` (Rev B). Rev-A-Werte oben in Kap. 2 bleiben als Referenz.
