# fluidi – FEM der Sonde (REQ-MECH-10), Phase 4b

| | |
|---|---|
| Stand | 2026-11-07, Schnittstelle PCB-Kontur Rev A; Nachträge Rev B (Kap. 4) und Rev C / V-K (Kap. 5, 2026-11-08) |
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

## 5 Nachtrag Rev C / V-K (2026-11-08, D-023)

**Was sich an der Sonde ändert:**
- Mit V-K (Fach 0.7 mm länger) liegen Kragen und Vergusskante 0.7 mm tiefer: Kragen z 1.3 … 6.6, Vergusskante **z 1.3**, Hülsenboden 1.3 statt 2.0 mm.
- Damit ist die freie Sondenlänge (Spitze bis Vergusskante) 106.3 statt 107.0 mm. Die Schulter (Tangente z 7.67) liegt jetzt 1.07 mm über dem Kragen, vorher 0.37.
- Schott (Einspannung z 32.0), Querschnitt und Werkstoffe bleiben.

**Lauf und Auswertung:**
- `fem_probe.py` liest die Geometrie aus `fluidi_params.py` und wurde unverändert neu gerechnet.
- Neu sind nur die Auswertungsgrössen relativ zur Kante:
  - `sigma_zz_hot`: 0.5 mm vor der Vergusskante, Fenster ± 0.35, wie Rev B bei z 1.5 / Kante 2.0
  - `sigma_zz_edge_m1`: 1.0 mm vor der Kante
- `fem_eval.py` wertet `sigma_zz_hot` aus. Der Hebelarm der Sondenmasse folgt der Kante.
- Rev-B-Rohdaten: Kap. 4. Neue Rohdaten: `results.json`, `summary.json`, `fem_log.txt`.

| Lastfall | Rev B | **Rev C / V-K** | Handrechnung (L = 106.3) | SF V-K | Bewertung |
|---|---|---|---|---|---|
| LC1 seitlich 10 N, 0.5 mm vor der Kante / max. an der Kante | 151 / 168 MPa | **149.4 / 167.1 MPa** (Kt 1.21; Konvergenz 1.0/0.5/0.25 mm → 139.2/151.0/149.4 MPa, 298 k Knoten) | 124.6 MPa; u 29.3 mm (FEM 30.2) | **2.31** (2.06 an der Kante, 3.78 typ. längs) | ✅ ≥ 2 (REQ-MECH-10) |
| LC1b ohne Kragenstütze | 150 / 191 MPa | **148.6 / 175.0 MPa** | – | 1.97 (Max. Schulter) | ⚠ Grenzfall, besser als Rev B (1.81) |
| LC2 in der Ebene | 13 MPa | 12.7 MPa | 10.0 MPa | 27.3 | ✅ |
| LC3 Druck 50 N / LC4 Zug 30 N | 2.3 / 1.4 MPa | 2.3 / 1.4 MPa | 1.6 / 0.9 | 150 / 250 | ✅ |
| LC5 Knicken frei | 29.0 N | 29.3 N | 29.8 N | 0.59 | ❌ wie bisher, D-016 |
| **LC6 Knicken geführt** | 236 N | **238.4 N** | 244 N | 4.77 | ✅ ≥ 50 N (REQ-MECH-10) |
| Fall 1 m, obere Schranke (27.9 g) | 202 MPa | 201.3 MPa | – | 1.71 (2.81 typ.) | ⚠ wie Rev B, PROTOTYP-PRÜFUNG |
| Fall 1 m, nur Sonde | 96 MPa | 95.6 MPa | – | 3.61 | ✅ |

**Bedingung D-023 erfüllt:** REQ-MECH-10 bleibt erfüllt. LC1 hat SF 2.31 ≥ 2, LC6 Knicklast 238 N ≥ 50 N. FEM und Handrechnung:
- Spannung bei z −20 / −5 / 0: +1.9 / +2.6 / +3.7 %
- Durchbiegung: +2.9 %
- Knicklast: −1.7 / −2.3 %

**Hülsenboden 1.3 mm (Handrechnung, im FEM nicht modelliert):**
- **Einspannung im FEM:** Der Kragen ist an seinen Aussenflächen fest eingespannt (Hülsenwände), der Boden kommt nicht vor. Das ist zulässig: Der Kragen steht vollflächig auf dem Boden, der Boden trägt nur Druck und Schub an der Wand und keine Biegung. Spalt Kragen–Wand 0.2 mm.
- **Werkstoff:** `BambuLab_ASA_TechnicalDataSheet_V2.0.pdf` S. 2: Zugfestigkeit X-Y 52 ± 5 MPa, Z 35 ± 4 MPa. Schubfestigkeit ≈ 0.5 × Zug X-Y = 26 MPa (**ANNAHME**).
- **Einstecken über die Hülse, 50 N** (Hand an der Hülse, Weg Wand → Boden → Kragen → Verguss → Sonde):
  - Auflagefläche Kragen/Boden ≈ 271 mm² (LAND) − 67 (Schlitz mit Hohlkehle) − 4.5 (Schraube) − 5.5 (Tasche) ≈ 194 mm² → Pressung 0.26 MPa.
  - Schub im Boden an der Wand: 50 N / (73.7 mm Umfang × 1.3 mm) = **0.52 MPa** → SF ≈ 50.
- **Abziehen über die Hülse, 50 N:**
  - Der Boden drückt den Kragen nach oben (gleiche Pressung wie oben).
  - Die Wand zieht über die Lagenfugen am Boden: 50 N / (73.7 × 1.6) = 0.42 MPa gegen 35 MPa (Z) → SF ≈ 80.
  - Rev B (2.0 mm): 0.34 MPa Schub. Der dünnere Boden ändert die Reserve praktisch nicht.
- **Kippen aus LC1** (10 N an der Spitze, falls die Hülsenwände den Kragen nicht stützen und er sich auf den Boden abstützt):
  - Moment 10 × 106.3 = 1063 Nmm, Hebel Kragentiefe 9.4 mm → 113 N als Linienlast nahe der Vorder- bzw. Hinterwand.
  - Schub im Boden 113 / (30.4 × 1.3) = **2.9 MPa** → SF ≈ 9.
- **Schraube M2 × 3:** Der Kopf drückt den Boden gegen den Kragen. Das ist reine Pressung, der Boden ist hinterlegt.
  - Pressung unter dem Kopf: Kopf Ø 3.8 auf Ø 1.7 → 9.1 mm². Bei 100 N Vorspannkraft 11 MPa (**ANNAHME** Handanzug; Anzug „fest von Hand“ in die Montageanleitung).
  - Einschraubtiefe 1.40 mm = 3.5 Gänge. Für eine Klemmschraube ohne Betriebslast reicht das (**ANNAHME**, PROTOTYP-PRÜFUNG: Ausreissen der Mutter beim Anziehen).
- **Druck:** Der Boden 1.3 mm = 6.5 Lagen à 0.2 ist mit 5 Bodenlagen voll ausgefüllt (`mechanical/PRINT_SETTINGS.md`).

Fazit: Der Hülsenboden 1.3 mm ist kein kritischer Querschnitt (SF ≥ 9 in allen Lastwegen). Kein FEM-Modell nötig.
