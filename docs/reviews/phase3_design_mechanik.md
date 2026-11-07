# Prüfbericht Phase 3 – Designvorschläge, Sicht Mechanik

Prüfer: Mechanik-Konstrukteur, Stand 2026-11-07, Kurzprüfung (Abschätzung, kein CAD).
Geprüft: `docs/design/DESIGN_PROPOSALS.md` v0.1, `renders/phase3/*.png`, `renders/gen/fluidi_lib.py`
(Profile `head_p1…p4`, `battery_lid`, `GAP_SOIL`), gegen REQ-MECH-01/02/08/10/12/13/15/17, REQ-UI-05/06,
REQ-SAF-CC-04, REQ-SAF-05, RB-03 und CONCEPTS Kap. 2.9/2A (A-32).

Eigene Eingangsdaten:
- Keystone 3034: A 21.2 / L 16.1 / W 23.1 / H 4.1 mm (`docs/datasheets/Keystone_3034_Catalog_M65.pdf`, S. 1, Zeile 3034).
- TS-1187A: 5.1 × 5.1 mm SMD, 1.6 N, Höhe 1.5 mm (`docs/datasheets/INDEX.csv`, SW1; das LCSC-PDF hat
  keinen Textlayer). **ANNAHME:** Betätigung senkrecht zur Platine (Draufsicht-Taster dieser Bauform).
- ASA-Dichte ≈ 1.07 g/cm³, FR4-Biegefestigkeit ≈ 400 MPa (**ANNAHME**, Werte aus Datenblättern in Phase 4 belegen).

## 1 Querschnittsbefunde (gelten für alle Köpfe)

| Nr | Befund | Gewicht | Vorschlag |
|---|---|---|---|
| M-01 | **„Taster oben, axial“ ist mit dem TS-1187A nicht direkt möglich.** Der Taster drückt senkrecht zur Platine; die Platinenoberkante ist von der Antenne AN043 (15.2 × 5.7 mm, z ≈ 35–41) belegt. Eine Taste oben braucht einen Umlenkhebel (Biegezunge aus ASA, Kunststoff im Antennenbereich ist zulässig) oder einen Seitentaster in der Antennenzone (Metall nahe Antenne, nicht empfohlen). | wichtig | Biegehebel: Taste oben drückt auf eine angespritzte ASA-Zunge, die den TS-1187A im Elektronikband (z ≈ 28–33) frontal betätigt. Alternative: Taste auf der Front im Elektronikband, direkt; 1.6 N × 35 mm Hebel = 0.06 Nm ist gegenüber der seitlichen Auslegungslast (10 N an der Spitze) vernachlässigbar → REQ-UI-05 bleibt erfüllt. |
| M-02 | **Teilungsfuge auf der Oberseite.** Zwei Schalen „liegend“ (P1, P4) ergeben eine umlaufende Fuge von ≈ 146 mm, auch über die Oberseite, die beim Giessen direkt getroffen wird (REQ-MECH-13). | wichtig | Kopf als **einteilige Haube** (oben geschlossen, unten offen), Platine von unten einschieben, Boden = Sondenschlitz mit Verguss. Wo Schalen bleiben: Nut/Feder mit Dichtkleber, Fuge nie auf der Oberseite. |
| M-03 | **Getrenntes Batteriefach (REQ-SAF-05) braucht Dichtflächen auf der Platine.** Halter W 23.1 bei ≈ 24 mm Platinenbreite lässt seitlich keinen Platz für eine Dichtrippe auf der Leiterplatte. | wichtig | Fach seitlich durch die Gehäusewand, Platinenkanten in Seitennuten eingeklebt/vergossen; oben (z ≈ 25.5) und unten (z ≈ 4.5) je eine Querrippe mit Dichtraupe über die Platinenoberseite. Freie Kupfer-/Lötstoppfreie Streifen von 2 mm für diese Rippen im Layout vorsehen (an Elektronik). |
| M-04 | **Deckeldichtung.** 0.4-mm-Sichtfuge ist kein Dichtkonzept. Bei 28 mm Aussenbreite und 23 mm Öffnung bleiben 2.5 mm je Seite für Wand + Dichtung. | wichtig | Öffnung auf ≈ 21.5 mm verkleinern (Zelle Ø 20 muss heraus, nicht der ganze Halter), Flachdichtung (TPU 95A separat gedruckt oder Moosgummi) im Deckel, Deckel 2 mm. Zellauswurf: Griffkerbe am offenen Ende des Clips. |
| M-05 | **Schraubdom M2.** Unten im Kopf liegt die Dichtzone 0–5 mm; ein Dom Ø ≈ 6 mm mit Gewindeeinsatz M2 × 3 (**ANNAHME** Einsatz-AD 3.2–3.6 mm) kollidiert mit dem Halter ab z = 5 und darf nicht durch die Platine (Dichtzone ohne Bohrungen). | wichtig | Dom in der Rückschale, auf der Platine aufstehend (nicht durch), in der Ecke neben der Zelle (Kreis Ø 20 lässt Ecken frei) oder Dichtzone auf 7 mm erhöhen (+2 mm Kopfhöhe). Unverlierbar: Gewinde im Deckel (Schraube einmal durchdrehen) oder O-Ring 1.5 × 1 auf dem Schaft. |
| M-06 | **Tiefenstapel** (Front 2 + Luft 0.3 + PCB 1.6 + Halter 4.1 + Noppe/Spiel 0.6 + Deckel 2 + Dichtung 0.5) ≈ 11.1 mm → 12 mm knapp, 13 mm komfortabel. Dom (Höhe ≈ 4.5 zwischen PCB und Deckel) passt in beide. | klein | 13 mm als Standard; P3 mit 12 mm nur, wenn Dichtung im Deckel versenkt. |
| M-07 | **Spritzwasser auf der Taste / REQ-UI-06.** Giesswasser (1 l aus 20 cm) auf eine oben liegende Taste: Dichtung und Fehlauslösung. | wichtig | Taste 0.5 mm unter einem Kragen versenkt, TPU-Membran (separat gedruckt, geklemmt; TPU nicht über AMS) oder O-Ring am Stössel; Werkseinstellung nur per Langdruck (Firmware). |
| M-08 | AMS: ASA über AMS möglich; transluzentes ASA für Lichtleiter (**ANNAHME** Verfügbarkeit/HDT/UV belegen). Inlays in den ersten Schichten liegend: wenig Spülmaterial. | klein | – |
| M-09 | Kopfgewicht (Abschätzung): Schale ≈ 7.5 cm³ × 1.07 ≈ 8 g, Kopfplatine ≈ 3 g, Zelle ≈ 3 g, Verguss/Deckel ≈ 2 g → **≈ 16 g**, Schwerpunkt ≈ 30 mm über Erde. Gegenüber 100 × 22 mm Blatt im Substrat unkritisch (REQ-MECH-17, PROTOTYP-PRÜFUNG in lockerem Granulat). P2/P4 +1–2 g. | klein | – |

## 2 Bewertung je Vorschlag

| Vorschlag | Ampel | Begründung | Wichtigste Änderung |
|---|---|---|---|
| **P1 Facette** | **gelb** | Facetten (≤ 45°, Seitenzug 4.5/19 ≈ 13°) stützenfrei; Innenbreite bei z = 41 ≈ 16.9 mm ≥ 15.2 (Antenne knapp, 0.85 mm je Seite). Zwei liegende Schalen → Fuge über die flache Oberseite; Bodenverjüngung auf 20 mm verhindert das Einschieben der 24-mm-Kopfplatine in eine Haube. | Oberseite fugenlos: Front-Schale greift als Kappe über die Oberseite (Fuge 3 mm unter der Oberkante auf der Rückseite) oder Haube mit verbreitertem Boden (≥ 25 mm); Taste mit Biegehebel (M-01). |
| **P2 Keil** | **gelb** | Bestes Wasserbild (Dach mit Tropfkante, Fuge unter der Dachkante). 48 mm hoch (Soll); Dachplatte separat flach gedruckt ist gut, Körper stehend ohne Stützen. Taste auf 25°-Schräge braucht ebenfalls Umlenkung. | Dachplatte mit umlaufender Klebe-/Dichtnut statt Klipsen; Taste mit Hebel; Höhe durch flacheres Dach (≈ 20°) auf 46 mm. |
| **P3 Stele** | **grün** | Rechteckiger Querschnitt eignet sich ideal als **Haube** stehend gedruckt (oben geschlossen, Deckenbrücke ≈ 8 mm, Deckelöffnung oben 21.5 mm Brücke – beides unkritisch), ein Farbwechsel bei z = 34, fugenlose Oberseite, Innenbreite 24 mm → Antenne mit 4.4 mm Abstand je Seite. 12 mm Tiefe knapp (M-06). | Tiefe 13 mm; Oberseite 2–3° nach vorn neigen, Taste versenkt mit Hebel/Membran. |
| **P4 Gipfel** | **rot** | Mehrere Grundprobleme: Taste auf der Schulter liegt neben/über der Antenne (Metallkuppel in der Antennenzone), geklebte Zickzackfuge der Kappe genau auf der beregneten Oberseite, Lichtleiter von LED (z ≈ 30) bis Gipfel (z ≈ 49) wird mit einer 0603-LED lichtschwach (**ANNAHME**, Muster), 49 mm hoch. | Nur weiterverfolgen mit Taste frontal im Elektronikband und Kappe als eingesetztem Lichtleiter mit gerader, überlappender Fuge (Kappe stülpt über den Körper). |
| **G1 Sockel** | **grün** | Wanne + Deckel, 45°-Frontfase kopfüber stützenfrei; Innenraum 62 × 40 × 20 reicht für XIAO 21 × 17.8 und RTC (Masse **ANNAHME**). Innenraum, kein Spritzwasser. | XIAO in Führungsrippen fixieren, USB-C-Ausschnitt mit 0.3 mm Spiel am gemessenen Muster; Antennen-Durchführung (SMA-Schott) mit Verdrehsicherung. |
| **G2 Gipfel** | **gelb** | 3 Teile, transluzente Kappe als langer Lichtleiter (gleiches Helligkeitsrisiko wie P4), Antenne auf schräger Schulter erschwert die Schottverschraubung. | Nur zusammen mit P4; sonst G1. |

## 3 Höhe über Erde (5 mm Freistrecke)

Sinnvoll, Empfehlung **beibehalten** (3–5 mm, nicht 0):
- Die Dichtlinie (Verguss am Sondenaustritt) soll nicht dauernd im nassen Substrat liegen; Substrat sackt,
  Mulch/Giesswasser steht kurz auf der Oberfläche → 5 mm Puffer schützen Verguss und Kriechweg (REQ-MECH-08/14).
- Mechanik: Das Biegemoment an der Sondenwurzel steigt um nur ≈ 5 % (10 N × 105 statt 100 mm). Handrechnung:
  W = 22 × 1.6² / 6 = 9.39 mm³, M = 10 N × 105 mm = 1.05 Nm → σ ≈ 112 MPa, SF ≈ 3.6 gegen ≈ 400 MPa (**ANNAHME**
  FR4), Kerbwirkung an der Vergusskante noch nicht berücksichtigt → Vergusskante mit Hohlkehle; FEM in Phase 4.
- Bedingung: zwischen Dichtlinie und Markierung keine Elektrodenfläche (sonst Luftanteil in der Messung),
  Markierung als Kupfer-freie Silkscreen-Linie auf beiden Seiten.
- REQ-MECH-02 (Soll) als Kopfhöhe 45 mm lesen; 50 mm über Erde ist vertretbar. Kürzung auf 3 mm nur, wenn die
  Höhe dem Auftraggeber wichtiger ist.

## 4 Empfehlung Mechanik

Mechanisch am robustesten ist **P3 Stele** (Haube ohne Oberseitenfuge, ein Farbwechsel, grösster
Antennenabstand). **P1** ist machbar, wenn die Schalenteilung so geändert wird, dass keine Fuge über die
Oberseite läuft; die Gestaltungsempfehlung P1 kann bleiben (gelb). P2 ist gleichwertig machbar (gelb, Höhe). P4 erst
nach Überarbeitung von Taste, Kappenfuge und Lichtleiter. Gateway **G1**. Unabhängig von der Wahl in
Phase 4 festlegen: Tastenumlenkung (M-01), Fachabdichtung über Seitennuten + Querrippen (M-03), Deckeldichtung
(M-04), Domlage (M-05). Spritzwasser- und Flutungstest (REQ-MECH-13, REQ-SAF-05) als PROTOTYP-PRÜFUNG am ersten Druck.
