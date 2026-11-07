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
