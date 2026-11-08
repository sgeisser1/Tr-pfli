# Phase 5 – Red Team: Geometrieänderungen Sensorgehäuse Rev C (P5-M1/M2/M3), Druckdateien, Zeichnungen, Anleitungen

| | |
|---|---|
| Prüfer | Red Team (frischer Kontext, ohne Begründungskette) |
| Datum | 2026-11-08 |
| Stand | Mechanik git `cedccd5` (seither unverändert); Anleitungen auf HEAD `6f269dd` (enthält a579a7c: R3-W1/K1–K4 eingearbeitet) |
| Geprüft | `git diff 7f369c7 cedccd5 -- mechanical/gen`, `fluidi_sensor.py`, `fluidi_params.py`, `check_sensor.txt`, `collision_pcb_step.txt`, `mechanical/sensor/print/*`, `mechanical/drawings/FL-S-00/02/08` + `drawings_check.txt`, `MONTAGE_SENSOR.md`, `BATTERIEWECHSEL.md`, `phase5_sicherheit_runde3.md`, REQUIREMENTS (REQ-UI-04/05, REQ-MECH-12/13/15), `PCB_OUTLINE.md` Kap. 6, `FLOORPLAN_OPTIONS.md` Kap. 5 |
| Werkzeuge | freecadcmd 0.21.2 (Part) headless, eigene Skripte im Scratchpad (nicht im Repo): `build()` mit `FLUIDI_NO_MAIN=1` geladen, alte Version 7f369c7 aus `git archive`, Kollisionsprüfung `fluidi_pcb_collision.py` in einer Kopie neu gerechnet |
| Ergebnis | **2 kritisch, 3 wichtig, 5 klein.** Behauptung 3 (P5-M2) **widerlegt**; 1, 2, 4, 5 bestätigt (2 mit Einschränkung); 6 mit kleinen Mängeln |

## 1 Behauptungen

| Nr | Behauptung | Urteil | Eigener Nachweis |
|---|---|---|---|
| 1 | P5-M1: Kappe war 2 Körper, jetzt 1 Körper, kopfüber stützenfrei | **bestätigt** | 7f369c7: `Kappe_blau` 2 Solids (2360.5 + 1785.4 mm³). cedccd5: 1 Solid 4426.9 mm³. Überhangsuche (Flächen mit n_z > cos 45° ausser Bett): die alte Ringfläche z 44.9 (120.8 mm²) ist weg, Trichter 45°, keine Stufe bei z 48.7. Verbleibende Überhänge: O-Ring-Nutflanke 1.15 (in FL-S-02 vermerkt), Ablaufstufe 0.5, Tastentaschenboden (Brücke 6.8), **Membransitz z 54.2 (Brücke, siehe W-1)**, Zungentaschen-Absatz 1.0 |
| 2 | P5-M3: Senkung Ø6.4 war offen, jetzt 0.8 mm Mantel, dicht | **bestätigt mit Einschränkung** | Seitenwand gemessen 0.81 (+x, −y), sonst 1.2–2.0. Aber: Boden unter dem Membransitz nur **0.3 mm** (z 53.9…54.2, Sektor +x/+y, r 2.0…3.2), als Brücke gedruckt (W-1); Mantel ragt 0.2 mm aus der Front (K-1) |
| 3 | P5-M2: Kinematik, Worst Case +0.14 mm, Biegespannung worst 26.2 MPa, SF 1.34 | **widerlegt** | Stössel ist frei drehbar (C-1); Toleranzkette ohne Führungsspiel und Nachgiebigkeit (W-2); Festigkeit nur im Schaltmoment, nicht im Überhub (C-2). Materialwerte selbst geprüft: `docs/references/BambuLab_ASA_TechnicalDataSheet_V2.0.pdf` S. 2: E(Z) 2120 ± 260, Zug(Z) 35 ± 4, **Biegefestigkeit(Z) 42 ± 3, Biegemodul(Z) 1650 MPa** – Zitat korrekt, lokal vorhanden. Taster: `XUNPU_TS-1088-AR02016_Datasheet_LCSC-2022-06.pdf` S. 1: Hub 0.2 ± 0.1, Kraft **160 ± 50 gf** (Rechnung nutzt nur 160 gf) |
| 4 | Keine Kollision mit Platinen-STEP; Kunststoff–Antenne 0.70 mm | **bestätigt** | `fluidi_pcb_collision.py` in Scratch-Kopie neu gerechnet: Ausgabe identisch mit `collision_pcb_step.txt` (ausser Pfadzeile), keine Kollision. 0.70 mm = Unterkante des neuen Mantels Ø8.0 (z 53.9) über dem Antennenkupfer bei x −2.2 (Speise-/Kurzschlussende). Keine Anforderung nennt einen Mindestabstand; `FLOORPLAN_OPTIONS.md` Kap. 5 (AN043 S. 5/6): zulässig, solange das offene Ende (x 12.2) frei bleibt – erfüllt. S11/RSSI bleibt PROTOTYP-PRÜFUNG. `PCB_OUTLINE.md` nennt noch 0.76 (K-4) |
| 5 | Druckdateien = Generator, je 1 Körper; Zeichnungen = Modell | **bestätigt** | Alle 9 Druckteile: STEP 1 Solid, symmetrische Differenz zum Generator (gleiche Drehung/Lage) 0.0000 mm³; STL geschlossen, Volumen ±0.1 %; 3MF je 1 Objekt. Selbst gemessen und mit FL-S-02/08 verglichen: Kappe 34 × 26.7 (Bounding Box), Zunge 0.6 (y 3.75…4.35), Nase 1.0 / Flanke 45° (z 48.0 → y 3.16), Zungenspitze–Nasenoberkante 5.1, Senkung Ø6.4 / Tiefe 2.3 / Rohr bis Senkung 2.7, Stössel 3.6 / 2.9 / 2.65 / 1.15 / 1.2 / 2.5 – alle stimmen. Die Zeichnung zeigt die 0.2-mm-Beule (K-1) und den 0.3-mm-Boden (W-1) nicht |
| 6 | Anleitungen vollständig, widerspruchsfrei, laientauglich | **weitgehend bestätigt** | Sicherheitsinhalte nach R3 vollständig (R3-W1, K1–K4 in a579a7c umgesetzt). Mängel: Prüfung 7 erwartet ein Verhalten, das die Mechanik nicht hat (C-2), Lageangaben beim Wechsel missverständlich (K-3) |

## 2 Befunde

### Kritisch

**C-1 · kritisch · REQ-UI-04 – Stössel dreht frei im runden Führungsrohr; der Finger weicht der Nase aus, SW1 schaltet nicht.**
Der Stössel hat ein D-Profil (`fluidi_sensor.py` Z. 247), die Bohrung im Rohr ist rund Ø3.2 (Z. 223). Es gibt keine
Verdrehsicherung. Die Querkraft der Nase am Finger (≈ 2.5 N, Hebel 3.0 mm zur Achse) erzeugt ≈ 7.5 N·mm und dreht den
Stössel im Gegenuhrzeigersinn (von oben); der Finger wandert nach vorn (−y), weg von der Nase. Nichts stellt ihn zurück:
Die Verdrehung **summiert sich** über die Betätigungen. Reibung an Membran und Rohr bremst allenfalls.
Nachweis am Modell (Stössel um die eigene Achse gedreht, Kollision mit Kappe/PCB/SW1/Fenster/Membran):
- frei drehbar **+15°** (bis der Finger an der Kappenfront y 1.6 anliegt), −1° blockiert;
- Zungenauslenkung bei vollem Hub 0.8: 0° 0.694 · 3° 0.558 · 6° 0.429 · 10° 0.262 · **15° 0.057 mm**;
- nötig sind 0.45 / 1.66 = 0.27 mm (nominal) bzw. 0.85 / 1.66 = 0.51 mm (worst) → **Ausfall ab ≈ 4° (worst) bzw. ≈ 10° (nominal).**
Die CAD-Kinematik in `check_sensor.txt` 2a verschiebt den Stössel nur in −z und kann das nicht zeigen. Kappe, Platine
und Schott sind nach dem Verguss nicht trennbar (MONTAGE Kap. 9): Ein dauerhaft verdrehter Stössel heisst Sensor ohne Taste
(kein Pairing, kein Werksreset).
*Vorschlag:* Verdrehsicherung, z. B. Bohrung im Rohr mit gleichem D-Profil (Fläche bei y = ay − 1.0, Spiel 0.1) oder eine
Längsnut/Feder; Kinematik 2a zusätzlich mit ±Verdrehung im Spiel rechnen; Prüfung 3 der Montage um „Stössel lässt sich
nicht verdrehen“ ergänzen.

**C-2 · kritisch · REQ-UI-04/05 – Überhub nach dem Schalten überlastet die Zunge; 2c rechnet nur den Schaltmoment.**
SW1 hat nur 0.2 ± 0.1 mm Hub (Datenblatt S. 1), danach ist er ein fester Anschlag. Die Taste läuft aber weiter: Der Teller
setzt nach 0.6 mm auf die Membran (0.5 mm Silikon, im Check 2 ausgeklammert), der feste Anschlag ist der Taschenboden bei
0.8 mm. Der Finger erzwingt dann an der Nase 0.49…0.69 mm, während SW1 die Zunge bei 0.35…0.55 mm abstützt
(gestützter Kragbalken, 3.2 × 0.6, Last bei a = 5.9…6.1, Stütze bei 8.8 mm). Eigene Rechnung, Finger starr:

| Tastenhub | Kraft an der Nase | Kraft auf SW1 | σ max (E 2120) | σ max (E 1650, Biegemodul Z) |
|---|---|---|---|---|
| 0.6 | 4–6 N | 1.8–3.0 N | 41–50 MPa | 32–39 MPa |
| 0.7 | 6–8 N | 2.9–4.2 N | 53–62 MPa | 41–48 MPa |
| 0.8 | 8–10 N | 4.2–5.6 N | 65–78 MPa | 51–61 MPa |

Das liegt über der Biegefestigkeit Z 42 ± 3 MPa (TDS S. 2), und zwar quer zu den Schichten. An der Taste braucht es dafür
nur ≈ 1.9 × Nasenkraft, also 8–19 N: ein normaler fester Daumendruck. Die Formel in 2c (`sig(dsw)`) enthält ausserdem die
Schaltkraft von SW1 nicht (bis 2.06 N, Moment an der Laststelle ≈ 5.6 N·mm ≈ 29 MPa allein). „SF 1.34“ gilt nur für den
Moment des Durchschaltens. MONTAGE Prüfung 7 („Taste stoppt nach dem Klick, nicht erst am Taschenboden“) beschreibt ein
Verhalten, das die Geometrie nicht hat, und verleitet beim Prüfen zu festem Drücken.
*Vorschlag:* Harter Tastenanschlag knapp nach dem Schaltpunkt: Hub so wählen, dass der Finger bei Worst-Case-Schalten
gerade noch reicht und danach am Kunststoff anschlägt (z. B. Taschenboden bzw. Teller auf Klemmring bei ≈ 0.55 mm), statt
über SW1 und die Zunge. Alternativ eine nachgiebige Überhubstufe im Stössel. 2c um den Lastfall „Taste am Anschlag,
SW1 am Anschlag“ erweitern (Schaltkraft 160 + 50 gf). Prüfung 7 neu formulieren.

### Wichtig

**W-1 · wichtig · REQ-MECH-13, R3-W2 – Membransitz: Boden 0.3 mm, als Brücke gedruckt.**
Der Senkungsgrund z 54.2 liegt nur 0.3 mm über der Blockunterkante z 53.9 (gemessen bei r 2.3…3.1 in +x und +y:
Material nur z 53.9…54.2). Beim Druck kopfüber ist diese Fläche die Unterseite einer Ringbrücke über der Senkung, und sie
ist zugleich die **Dichtfläche der Membran**, nach P5-M3 die einzige Barriere oben (R3-W2). Check 12 prüft genau 0.3 mm
und ist damit konstruktionsbedingt erfüllt. 1–2 Lagen auf einer hängenden Fläche sind weder eben noch sicher dicht.
*Vorschlag:* Boden ≥ 0.8 mm (Senkung flacher oder Block tiefer, soweit der Abstand zur Platine reicht) oder den Sitz als
45°-Kegel ausführen; Membran rundum kleben (vgl. O-4). PROTOTYP-PRÜFUNG ST-W6 mit Farbeindringprüfung am Sitz.

**W-2 · wichtig · Toleranzkette 2b unvollständig – Worst Case +0.14 mm ist nicht belastbar.**
Es fehlen: (a) das Spiel des Stössels im Rohr (Ø3.0 in Ø3.2, gemessen: Verschiebung −y 0.1 kollisionsfrei, ab 0.2
Kollision). Allein das ergibt 0.1 × 1.66 = −0.17 mm am Betätiger, Worst Case danach ≈ −0.03 mm. (b) Die Nachgiebigkeit
des Stössels: Arm 0.8 × 1.15 mm, ≈ 2.5 mm frei auskragend, unter ≈ 4.7 N senkrecht und 2.5 N quer. Grob geschätzt
0.1–0.3 mm Verlust am Finger aus Biegung und Torsion (Handrechnung, **ANNAHME** ohne FEM). (c) Schaltkraft +50 gf.
(d) Die Kippung im Rohr (Führungslänge 2.4 mm).
*Vorschlag:* Stössel in 2a/2b mit Spiel und Kippung rechnen und als Feder modellieren (FEM mit CalculiX ist vorhanden) oder
Arm massiv verstärken bzw. Finger unter dem Rohr führen. Mit C-1 und C-2 zusammen neu auslegen.

**W-3 · wichtig · Stössel nicht stützenfrei in der angegebenen Lage.**
FL-S-08 und `PRINT` drehen 90° um x: „flach auf der D-Fläche“. Auf dem Bett liegt aber die Front von Arm und Finger
(y 2.5). Die D-Fläche (y 2.8) schwebt 0.3 mm darüber; der Schaft Ø3 (2.65 mm lang) hängt frei aus. Der Schaft ist
Führungsfläche, Durchhang klemmt im Rohr Ø3.2.
*Vorschlag:* Armfront bündig mit der D-Fläche (fy0 = ay − 1.0), andere Drucklage oder Zeichnung/Notiz korrigieren.

### Klein

| Nr | Befund | Vorschlag |
|---|---|---|
| K-1 | Der P5-M3-Mantel Ø8.0 (y −0.2…7.8) ragt **0.2 mm aus der Frontfläche** der Kappe (x −3.45…−0.95, z 53.9…55.5): Bounding Box y −0.2, Druckdatei 34 × **13.2** × 26.7. Das ist eine sichtbare Beule unter der Deckfase. Ohne Beule wäre die Frontwand vor der Senkung nur 0.6 mm (nicht 0.8) | Mantel mit `prism(P(0))` schneiden und die Frontwand an der Senkung bewusst festlegen (≥ 0.8 → Senkung oder Achse 0.2 nach hinten); Check „Kappe innerhalb P(0)“ |
| K-2 | Zungentaschen-Verlängerung im Trichter erzeugt einen horizontalen Absatz z 44.89 (3.6 mm², 1.0 mm tief) | unkritisch, ggf. 45° anfasen |
| K-3 | BATTERIEWECHSEL Schritt 2/3: „Spitze nach oben halten“, dann „Schraube **unten** am Kopf“ und „Hülse **nach unten** über die Sonde abziehen“. In dieser Haltung zeigen beide nach oben. Für Laien widersprüchlich | „Schraube an der Kopfunterseite neben der Sonde“; „Hülse Richtung Sondenspitze abziehen“ |
| K-4 | `PCB_OUTLINE.md` Kap. 6 (Z. 108/110/174) noch auf dem alten Stand: Zunge y 3.55…4.35, „Keil-Vorspalt, Hebel 2.5 → 0.90 mm“, Kappe–Antenne 0.76, Stössel z 49.1 | auf P5-M2 nachführen (Zunge 0.6, Nase, 0.70 mm) |
| K-5 | Zeichnungs-Schriftfeld „git fba2057 + Arbeitsstand“, eingecheckt in cedccd5: Stand nicht eindeutig rückverfolgbar | Zeichnungen nach dem Commit mit sauberem Hash neu erzeugen (Release-Skript) |

Am Rand (nicht Gegenstand, ergänzend zu R3-W1): Die vollgewindige M2 × 3 steckt in der Endlage gleichzeitig in der
Furchlippe und in der Mutter. Die Phasenlage beider Gewinde ist beim Wiederverschrauben zufällig, also wird die Lippe beim
Anziehen bis ±0.2 mm axial verspannt. ST-K8 (Lippe nach 50 Wechseln) deckt das ab; bitte dort auf Ausreissen der Lippe
achten.

## 3 Alternative (geprüft, einfacher)

Statt Nase, Zunge und Überhub über SW1: **Stössel wirkt direkt in y auf SW1 über einen 45°-Keil am Stössel gegen eine
kurze, steife Wippe mit festem Tastenanschlag** – oder einfacher: SW1 als seitlich betätigter Taster (Betätiger in z)
an der Platinenoberkante, direkt unter dem Stössel. Dann entfallen Zunge, Hebelübersetzung, Verdrehsicherung und
Überhubproblem. Das ändert das Layout (Rev D) und gehört deshalb nicht in Rev C. Für Rev C genügen C-1/C-2 mit
D-Bohrung und hartem Anschlag; beides lässt sich drucken, ohne die Platine anzufassen.

## 4 Was ohne Befund geprüft wurde

Kappe einteilig und Trichter 45° (Flächenanalyse), Seitenwand der Senkung ≥ 0.81, Kollisionsfreiheit mit dem KiCad-STEP
(neu gerechnet, identisch), Antennenabstand und Lage zum offenen Ende, Druckdateien = Generator (9 Teile,
Volumendifferenz 0), 13 Masse aus FL-S-02/FL-S-08 am Modell, ASA- und SW1-Datenblattwerte (lokal, Seite zitiert),
Sicherheitsinhalt der Anleitungen gegen R3 (umgesetzt), Polung/Einschubrichtung in Anleitung = Modell (+x offen).

## 5 Antwort an die Ersteller

Bitte je Befund *umgesetzt* / *abgelehnt (Grund)*: C-1, C-2, W-1…W-3, K-1, K-2, K-4, K-5 → `mechanik`; K-3 → Anleitungen.
C-1 und C-2 blockieren aus Sicht des Red Teams den Druck der Kappe/Stössel für die Muster nicht, wohl aber die Aussage
„Tastermechanik ausgelegt“. Vor dem Verguss des ersten Musters sollten sie behoben sein, weil die Kappe danach nicht mehr
tauschbar ist.

Hinweis: Während der Prüfung hat ein anderer Agent `hardware/sensor/out/fluidi_sensor.step` und das Layout im
Arbeitsbaum geändert (nicht committet). Die Kollisionsprüfung oben lief auf der Kopie zum Prüfzeitpunkt (Ergebnis identisch
mit `collision_pcb_step.txt`). Nach dem Commit der Layoutänderung bitte `fluidi_pcb_collision.py` neu laufen lassen.

## Antwort Ersteller (Mechanik, 2026-11-08, Runde 2)

Nachweise: `freecadcmd mechanical/gen/fluidi_sensor.py` → `mechanical/sensor/check_sensor.txt` (Punkte 2, 2a–2e, 11, 12, 12b,
12c); `freecadcmd mechanical/gen/fluidi_pcb_collision.py` → `collision_pcb_step.txt` (mit dem aktuellen
`hardware/sensor/out/fluidi_sensor.step`); Zeichnungen `freecadcmd mechanical/gen/fluidi_drawings.py`.

| Befund | Antwort | Umsetzung / Nachweis |
|---|---|---|
| **C-1** Stössel drehbar | **umgesetzt** | Führungsrippe an der Kappenfront vor dem Finger (y ≤ 2.3, Spiel 0.1) und D-Bohrung im Rohr (Fläche y 2.3, Spiel 0.1 zur D-Fläche y 2.4). Freie Verdrehung im CAD **+1.50° / −1.50°** (vorher +15°). Zunge bei vollem Hub: 1.100 nominal, 1.035 verdreht, 1.000 mit Finger an der Rippe. Die Querkraft der Nase geht in die Rippe, nicht in Arm und Schaft (2a). Montage-Prüfung 3 „Stössel lässt sich nicht verdrehen“, Test M-T5 |
| **C-2** Überhub überlastet Zunge | **teilweise umgesetzt, harter Anschlag abgelehnt** | Abgelehnt: Ein fester Tastenanschlag kann nicht beides. Der Schaltpunkt streut über die Toleranzkette von ≈ 0.05 bis 0.65 mm Tastenhub (2b). Ein Anschlag nach dem Worst-Case-Schaltpunkt verhindert die Last nach dem Schalten im Nominalfall nicht; ein früherer Anschlag verhindert das Schalten im Worst Case. Umgesetzt: Lastpunkt an SW1 verlegt (Nase in Höhe SW1, Lastmitte 1.15 mm über der Betätigerachse statt 6 mm Hebel), 60°-Keil (Querkraft = Tastenkraft / tan(60° + Reibwinkel)). Lastfall 20 N gerechnet (2d, Kragbalken mit Stütze in SW1, Vorspannung aus der Auslenkung bis zum Anschlag, Schaltkraft 160 + 50 gf in 2b/2c): μ 0.3 Zunge 25.8 MPa nominal (SF 1.63) / 36.5 MPa worst (SF 1.15) gegen Biegefestigkeit Z 42 MPa (TDS S. 2); **μ ≤ 0.2 worst SF < 1**. SW1 trägt dann 4.7–11.5 N (Grenzlast nicht im Datenblatt). **Restrisiko offen:** Bruch der Zunge = Ausfall der Taste (keine Gefahr). Vorschlag für Rev D: Ihre Alternative Kap. 3 (Taster mit Betätiger in z unter dem Stössel). Prüfung 7 neu formuliert (normale Fingerkraft, nicht nachdrücken), M-T2 mit 20 N |
| **W-1** Membransitz 0.3 | **teilweise umgesetzt** | Boden unter dem Sitz 0.8 mm, ausser im Sektor 60–90° (zur Platinenoberkante und zum Antennenkupfer, 0.3 mm); dort würde ein tieferer Boden die Platine (z 53.5) treffen bzw. dem Antennenkupfer näher als 0.70 kommen (bestätigter Wert d8dfac7). `check_sensor.txt` 12b. Dichtung neu: Klemmring Presssitz 0.05 je Seite + Membranverpressung 0.1 mm (2e). Wasser von oben muss damit zwischen Klemmring-Schürze (oberste Drucklage) und Membran durch, nicht über die gebrückte Sitzfläche. M-W3 mit Farbeindringprüfung |
| **W-2** Toleranzkette | **umgesetzt** | 2b: Spalt ±0.3, Schaltweg ±0.1, Vorspalt +0.1, Rippenspiel 0.1 und Verdrehung geometrisch im CAD; Hubverlust durch Armbiegung (Arm 1.5 hoch, 0.017 mm bei 11.6 N) gerechnet; Schaltkraft 160 + 50 gf. Worst-Reserve +0.17 mm am Betätiger, Schaltpunkt worst 0.65 mm Hub (≤ 0.8). Kippung im Rohr ist durch Rippe und Zunge auf ±0.1 am Finger begrenzt (im Rippenspiel enthalten). Keine FEM des Stössels (Handrechnung Arm, ANNAHME starrer Finger, da an der Rippe abgestützt) |
| **W-3** Stössel-Drucklage | **umgesetzt** | D-Fläche y 2.4 = Front von Arm und Finger, liegt vollflächig auf dem Bett (FL-S-08, PRINT_SETTINGS) |
| K-1 Beule Front | **umgesetzt** | Mantel auf die Aussenkontur P(0) geschnitten, 12c: 0.0000 mm³ ausserhalb. Frontwand vor der Senkung bleibt 0.6 mm; beidseitig nass (Senkung liegt über der Membran), also keine Dichtwand |
| K-2 Absatz Zungentasche | **abgelehnt** | Der Platz vor der Zunge wird für Nase, Finger und Rippe gebraucht; eine 45°-Fase würde in die Nase laufen. Absatz liegt kopfüber als kurzer Überhang (≤ 1.2 mm) |
| K-3 BATTERIEWECHSEL Haltung | **umgesetzt** | Schritt 2/3: „Schraube an der Kopfunterseite neben der Sonde“, „Hülse Richtung Sondenspitze abziehen“ |
| K-4 PCB_OUTLINE Kap. 6 | **umgesetzt** | Zunge 0.6, Nase, Rippe, D-Bohrung, Schaltpunkt; Kappe–Antenne 0.70 (bestätigt d8dfac7) |
| K-5 Schriftfeld-Stand | **umgesetzt** | Schriftfeld nennt die SHA-256 der Generatorquellen (10 Stellen, auch in `drawings_check.txt`), unabhängig vom Commit-Zeitpunkt; git-Basis nur informativ |
