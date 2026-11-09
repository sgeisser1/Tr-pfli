# fluidi – Vergussmasse (Kragen, Schott) und Versiegelung der Sonde (O-1, O-2)

| | |
|---|---|
| Stand | 2026-11-09, Phase 6, Mechanik-Agent. Runde 2 nach Sicherheitsprüfung `docs/reviews/phase6_vergussmasse_sicherheit.md` (kein Veto, Auflagen A-1 … A-5, W-1 … W-5, K-1 … K-6 – Antworten dort am Ende). Entscheidungsvorlage für den Orchestrator |
| Offene Punkte | O-1 Vergussmasse, O-2 Kantenversiegelung Sonde (`docs/manuals/MONTAGE_SENSOR.md` Kap. 0), REQ-MECH-07, PROJEKTAUFTRAG Techn. Anf. 1 („Versiegelung der Schnittkanten und der Sonde bewerten … mit Anleitung“) |
| Ergebnis | Empfehlung **Electrolube ER2223** (2K-Epoxid, Tg 140 °C, 800 mPa·s) für Schott, Kragen **und** Kantenversiegelung der Sonde; Sondenflächen bleiben unbeschichtet. Abweichung von K-4 („mineralisch gefüllt, niedriger CTE“): Sicherheit **zulässig unter A-1 … A-5** (Kap. 9). Kosten: Beutel einmal abfüllen und Kleinmengen wägen (Variante M-A) → **2 Beutel (je Bauserie) statt 6** (Kap. 7); M-A von der Sicherheit in Runde 2 unter MA-1 … MA-5 zugelassen |
| Rechnung | `simulation/field/coat_epoxy.py` → `simulation/field/results/coat_epoxy.{txt,csv}` (neu), Grundlagen `simulation/field/REPORT.md` |
| Anleitung | `docs/manuals/MONTAGE_SENSOR.md` Kap. 0, 1, 3a, 4, 5, 5a, 6, 8; `docs/manuals/PROGRAMMIEREN_SENSOR.md` Kap. 5 Schritt 9 (Zelle vor dem Verguss entnehmen) |

Zitierweise: Datei, Seite. Alle Dateien unter `docs/references/`, Abruf 2026-11-08.

## 1 Anforderungen

| Nr | Anforderung | Wert / Kriterium | Quelle |
|---|---|---|---|
| A1 | Dichtfunktion Kragen = Sondendichtung, wird nie gelöst | Vollständige Füllung Spalt 0.15 mm je Seite (Kragen), 0.2 mm (Schott), Tasche U3/C24 blasenfrei | `docs/interfaces/PCB_OUTLINE.md` Kap. 7; `mechanical/PRINT_SETTINGS.md` Z. 117 |
| A2 | Ein Material für den ganzen Kragen, kein weicher Vorverguss | „mineralisch gefülltes Epoxid (Tg ≥ 80 °C, niedriger CTE)“ | `docs/reviews/phase4_sicherheit_kragen_firmware.md` K-4 |
| A3 | Temperatur | Betrieb 5–45 °C, Kopf bis **65 °C**, Lagerung −10–50 °C; Prüfung 50 Zyklen −10/+65 °C + 168 h 65 °C | `docs/requirements/REQUIREMENTS.md` RB-03; K-7 |
| A4 | Dauerkontakt nasse, gedüngte Erde; Giesswasser von oben | Wasseraufnahme klein, Haftung bleibt nass erhalten; Dünger: Salze, schwach sauer/basisch (**ANNAHME**) | RB-02, REQ-MECH-07/08 |
| A5 | Haftung | FR4-Laminat, Lötstopplack (Dichtstreifen ohne Kupfer), ENIG (nur in der Tasche U3/C24), **ASA** (Kragen, Schott, Keil; REQ-MECH-12; PETG nicht verwendet) | PCB_OUTLINE Kap. 3 Z5A/Z5B; K-5 |
| A6 | Dielektrikum über den Elektroden | Jede Schicht auf den Sondenflächen senkt die Spanne (Kap. 3); Schichtdicke reproduzierbar oder Flächen frei | `simulation/field/REPORT.md` Kap. 4 |
| A7 | Aushärtung | Raumtemperatur; Nachhärtung höchstens 60 °C (ASA HDT 92 °C @ 1.8 MPa, `BambuLab_ASA_TechnicalDataSheet_V2.0.pdf` S. 2; Zelle beim Verguss nicht eingesetzt) | REQ-MECH-12 |
| A8 | Werkstatt ohne Spezialgerät | Keine Dosieranlage, Vakuum nur „falls vorhanden“; Mischen von Hand; Waage 0.01 g vorhanden (**ANNAHME**, MONTAGE Kap. 1) | RB-08, MONTAGE Kap. 1 |
| A9 | Topfzeit | ≥ 30 min für eine Gruppe vorbereiteter Sensoren (Kap. 6) | – |
| A10 | Sicherheit | Keine CMR-Stoffe, wenn eine Alternative besteht (Sicherheit > Kosten); Schutzmassnahmen nach SDB | CLAUDE.md Prioritäten |
| A11 | Kosten | 15–20 Sensoren; Kostenmodell rechnet bisher 0.40 CHF/Sensor „Versiegelung“ (**ANNAHME**) | `hardware/sensor/gen/cost_rev_b.py` Z. 59 (Phase-5-Kostenmodell); REQ-FAB-04 |
| A12 | Bezug | Händler in der Schweiz, Datenblatt und SDB verfügbar | Auftrag |
| A13 | Temperaturfühler U3 im Kragen | ≥ 0.5 mm Masse über U3; Masse wird zum thermischen Pfad zum Boden | PCB_OUTLINE Z5B, REQ-TMP-01 |

Volumen pro Sensor (CAD): Schott ≈ 12 mm³, Kragen ≈ 62 mm³ (MONTAGE Kap. 4/5); Kanten der Sonde ≈ 240 mm Kantenlänge × (1.6 + 2 × 0.5) mm × 0.15 mm ≈ 94 mm³ (**ANNAHME** Schichtdicke). Summe ≈ **0.17 ml ≈ 0.19 g pro Sensor**.

## 2 Ausgangslage Sonde

Die Sonde ist 4-lagig, Elektroden nur auf L2/L3, Aussenlagen ab z > 0 ohne Kupfer und ohne Vias, Kupfer ≥ 1.25 mm von der
Kontur (REPORT.md Kap. 8; PROJEKTAUFTRAG: „kein freiliegendes Metall im Sondenbereich“). Die Flächen sind mit Lötstopplack
(≈ 30 µm, REPORT.md Kap. 3) bedeckt. Offen liegt nur die **gefräste Schnittkante** (Glasgewebe + Harz, 1.6 mm). Über sie
nimmt das Laminat schneller Wasser auf als über die Flächen (Kapillarwirkung entlang der Glasfasern, **ANNAHME**, nicht
quantifiziert). Die FR4-Feuchtedrift beträgt bis 6.8 % der Spanne (Er +10 % bei Sättigung, REPORT.md Kap. 4 und 7;
Ursprung `DuPont_Khan_DkDf_Aramid-vs-GlassFR4_1999.pdf` S. 5 Tab. 1). REPORT.md Kap. 7 nennt als Massnahme „Kanten
versiegeln“ und Vorkonditionierung ≥ 14 Tage vor der Kalibrierung.

## 3 Verfahren Sonde: Vergleich (REQ-MECH-07)

Feldsimulation 2D (scikit-fem, Geometrie SG gap 2 = Layout Rev B/C), Beschichtung **rundum** (Flächen + Kanten), Er 2.8
(MG 832HT, `MGChemicals_832HT_TDS_V6.2-2026-06-18.pdf` S. 3, 1 MHz) bis 4.5 (**ANNAHME** obere Grenze; ER2223-TDS nennt keine
Permittivität; Stycast 2651-40 W1: 3.9 @ 1 MHz, `Henkel_LoctiteStycast2651-40W1-Cat9_TDS_2019-05.pdf` S. 1).
Quelle: `simulation/field/results/coat_epoxy.txt`.

| Schicht rundum | Spanne Er 2.8 | Spanne Er 4.5 | FR4-Drift [% Spanne] | Drift durch Feuchte der Schicht (Er +10 %, ANNAHME) |
|---|---|---|---|---|
| keine (nur Lack 30 µm) | 266.7 pF/m (Referenz) | 266.7 pF/m | 6.8 | 0.9 |
| 50 µm | −9.4 % | −6.2 % | 5.9 / 6.2 | 2.0–2.5 |
| 100 µm | −17.1 % | −11.6 % | 5.3 / 5.7 | 2.8–3.5 |
| 200 µm | −29.4 % | −20.9 % | 4.6 / 5.1 | 4.0–4.8 |
| 300 µm | −38.7 % | −28.6 % | 4.3 / 4.7 | 4.9–5.7 |
| 500 µm | −52.0 % | −40.5 % | 4.2 / 4.4 | 6.2–7.0 |
| Luftspalt 0.1 mm rundum (z. B. unter Schrumpfschlauch) | −36.6 % | | | (`results/study2d.csv`, „4L SG gap2“, gap01) |

Folgerung: Eine Schicht auf den **Flächen** kostet viel Spanne, verringert die FR4-Drift nur wenig (6.8 → 5.7 % bei 100 µm)
und bringt eine eigene Feuchtedrift mit. Ungleichmässige Dicke (Pinsel, Tauchen) streut die Empfindlichkeit von Sensor zu
Sensor; die 2-Punkt-Kalibrierung gleicht das statisch aus, die Drift nicht.

| Verfahren | Wirkung | Spanne | Werkstatt | Bewertung |
|---|---|---|---|---|
| Acryl-/UV-Schutzlack vollflächig (z. B. `MGChemicals_4200UV_TDS.pdf`, 50–125 µm, S. 2) | Feuchteschutz, nicht für Dauer-Eintauchen (Red Team W-5, CONCEPTS Kap. 6.2) | −6 … −17 % | UV-Lampe nötig | **nein** |
| Epoxid vollflächig (Tauchen/Pinsel 0.1–0.3 mm) | dicht, abriebfest | −12 … −39 % | einfach, Dicke schlecht reproduzierbar | **nein** (Spanne, Streuung, eigene Drift) |
| Schrumpfschlauch mit Kleber | dicht, wenn vollflächig verklebt; Wand + Kleber ≥ 0.3 mm (**ANNAHME**, kein Produkt gewählt) | ≥ −29 %, mit Luftblasen ≈ −37 % je 0.1 mm Spalt | flache 20-mm-Sonde mit Spitze: Falten und Lufteinschlüsse an den Flächen (**ANNAHME**) | **nein** |
| **Epoxid nur auf Kante und Spitze** (Überlappung ≤ 1 mm auf die Flächen, ausserhalb des Kupfers ab 1.25 mm) | dichtet den schnellen Pfad (Schnittkante), schliesst lückenlos an die Hohlkehle des Kragens an | Kanten tragen ≈ 1 % der Feldenergie (REPORT.md Kap. 4) → Spanne **≈ −1 … −2 %** (**ANNAHME**, nicht simuliert) | Pinsel/Kanüle, gleiche Masse wie Kragen | **gewählt** |

Begründung: Die Sondenflächen haben kein Kupfer (4 Lagen, REQ-MECH-04); eine Flächenschicht schützt also kein Metall,
kostet aber Empfindlichkeit. Der Lötstopplack bleibt die Flächenschicht. Die Stecktiefen-Markierung (Bestückungsdruck z −5)
bleibt sichtbar.

## 4 Produktvergleich Vergussmasse

Vorauswahl: 2K-Epoxide für Elektronikverguss mit Datenblatt, in kleinen Gebinden, mit Bezug in der Schweiz. PU und Silikon
scheiden nach K-4 aus (weiche, schlecht haftende Grenzfläche im Leckpfad).

| Eigenschaft | **Electrolube ER2223** | Electrolube ER2221 | MG Chemicals 832HT | Henkel Loctite Stycast 2651-40 W1 + Cat 9 |
|---|---|---|---|---|
| Typ | 2K-Epoxid, „high Tg, low viscosity“ (TDS S. 1) | 2K-Epoxid, gefüllt, wärmeleitend (TDS S. 1) | 2K-Epoxid, schwarz (TDS S. 1) | 2K-Epoxid, gefüllt (Füllstoff setzt sich ab, TDS S. 2) |
| Füllstoff / Dichte gehärtet | ungefüllt (**ANNAHME**: TDS sagt es nicht; Dichte 1.10 g/ml, S. 2, und SDB A Abschn. 3 nur organische Stoffe) | gefüllt, 1.88 g/ml (S. 2) | ungefüllt, 1.1 g/ml (S. 2) | gefüllt, Harz 1.5 g/cm³ (S. 1) |
| **Tg** | **140 °C** (S. 2; Härtebedingung nicht angegeben) | **nicht angegeben** | **89 °C** (S. 2, ASTM E1545) | **117 °C** TMA (S. 1; mit Nachhärtung empfohlen) |
| CTE | 70 ppm/K (S. 2) | **30** ppm/K (S. 2) | 86 ppm/K unter Tg (S. 2) | 60 ppm/K unter Tg (S. 1) |
| Viskosität gemischt | **800 mPa·s** @ 23 °C (S. 1) | 6000 (S. 1) | 22 000 cP @ 25 °C (S. 2) | nicht angegeben (Harz 33 000, S. 1) |
| Mischverhältnis | 3.45 : 1 Gewicht, 2.90 : 1 Volumen (S. 1) | 13.91 : 1 Gewicht (S. 1) | 2 : 1 Gewicht, 1.6 : 1 Volumen (S. 2) | 100 : 9 Gewicht (S. 1) |
| Topfzeit / Gelzeit | 30 min (20 °C) / 90 min (S. 1) | 60 min / 6 h (S. 1) | 1 h (S. 2) | 45 min (100 g, S. 1) |
| Aushärtung | 24 h @ 23 °C, 4 h @ 60 °C, 1 h @ 100 °C (S. 1) | 24 h @ 23 °C, 2 h @ 60 °C (S. 1) | 24 h RT, 1 h @ 65 °C (S. 1) | 16–24 h @ 25 °C, Nachhärtung 4–6 h bei max. Einsatztemperatur (S. 1) |
| Einsatztemperatur | −40 … +180 °C (S. 2) | −40 … +150 °C (S. 2) | −40 … 225 °C (S. 2) | −40 … +130 °C (S. 1) |
| Wasseraufnahme | < 0.25 % (10 d @ 20 °C, S. 2) | < 0.5 % (S. 2) | 0.3 % (30 d, S. 3) | 0.07 % (7 d, S. 1) |
| Permittivität | nicht angegeben | 6.0 @ 50 Hz (S. 2) | 2.8 @ 1 MHz (S. 3) | 3.9 @ 1 MHz (S. 1) |
| Haftung Kunststoff | „excellent adhesion to a wide range of substrates“ (S. 1), keine Werte | keine Angabe | 3.5 N/mm² auf ABS (S. 3) | „excellent adhesion“ (S. 1) |
| Gebinde | **Resin Pack 250 g** (Beutel, Mischen ohne Waage, S. 1) | Resin Pack 250 g | Flaschen 340 ml (S. 1) | 1 kg + Cat 9 |
| Gefahren (SDB) | A: H315, H317, H319, H411, „Achtung“; B: H302, **H314**, H317, H318, H373, „Gefahr“ | A: H315 … (Warning); B: SDB nicht beschafft | A: H315, H317, H319, **H360** (Repr. 1B), H411; B: **H314**, H317, H411 | SDB nicht beschafft |
| CH-Bezug, Preis (2026-11-08) | Simpex (CH), EER2223RP250G, **CHF 38.20** exkl. MWST + Versand, „In stock: available to order“, Lieferzeit 8 Wochen; Distrelec CH Art. 301-16-965 (Preis nicht abrufbar) | nicht bei Simpex gefunden; RS UK: Auslauf | RS CH 918-4999: CHF 76.25 (nur Suchtreffer, Seite nicht abrufbar → **unbestätigt**) | CHF ≈ 160 (Harz 1 kg) + Cat 9 (Angebot eines CH-Händlers an CERN, undatiert, **unbestätigt**) |
| Urteil | **empfohlen** | Variante B, nur wenn K-4 „gefüllt“ zwingend und Electrolube den Tg ≥ 80 °C bestätigt | nein: H360 (CMR) und zähflüssig | nein: Kosten (≈ 300 CHF, > 10 CHF/Sensor), Wägen 100 : 9 |

Ausgeschieden ohne Detailvergleich (Tg/Formbeständigkeit < 80 °C):
Electrolube ER2188 (HDT 50 °C, `Electrolube_ER2188_TDS_Rev3-2015-12.pdf` S. 2; sonst geeignet: gefüllt, CTE 40, 9000 mPa·s, Simpex CHF 19.40),
MG 832B (Tg 49 °C, `MGChemicals_832B_TDS_V5.4-2026-04-29.pdf` S. 2), MG 832HD/832HDA/832TC/832C (Tg 41/51/50/53 °C, TDS S. 2,
nur gesichtet, nicht abgelegt).

Quellen der Tabelle: `Electrolube_ER2223_TDS_Rev4-2019-03.pdf`, `Electrolube_ER2221_TDS_Rev8-2019-03.pdf`,
`MGChemicals_832HT_TDS_V6.2-2026-06-18.pdf`, `Henkel_LoctiteStycast2651-40W1-Cat9_TDS_2019-05.pdf` (Mischviskosität mit
Cat 9M: 9733 mPa·s, Tg 78 °C, `Henkel_LoctiteStycast2651-40-Cat9M_TDS_2022-03.pdf` S. 1); SDB siehe Kap. 8.

## 5 Verarbeitbarkeit (Abschätzung)

Kapillares Füllen des Spalts h = 0.15 mm über die Kragenhöhe L = 5.3 mm (z 1.3 … 6.6): t ≈ 3 μ L² / (h γ cos θ)
mit γ cos θ ≈ 0.03 N/m (**ANNAHME**, benetzendes Epoxid) → t ≈ 18 s pro Pa·s. Aufstieg einer Luftblase d = 0.5 mm
(Stokes): v ≈ Δρ g d² / (18 μ).

| Masse | μ [Pa·s] | Spalt füllen | Blase steigt 5 mm |
|---|---|---|---|
| ER2223 | 0.8 | ≈ 15 s | ≈ 30 s |
| ER2221 | 6 | ≈ 2 min | ≈ 3.5 min |
| ER2188 | 9 | ≈ 3 min | ≈ 5 min |
| 832HT | 22 | ≈ 7 min | ≈ 12 min |

ER2223 füllt Spalt und Tasche U3/C24 zügig und entgast **ohne Vakuumkammer** innerhalb der Gelzeit (90 min). Kehrseite:
Die dünne Masse läuft am Spaltaustritt (Kragen-Oberseite z 6.6 bzw. Schott-Oberseite z 32.0) leicht über die Platine weiter.
Der Kapillarmeniskus bleibt an einer scharfen Kante hängen (Laplace-Druck ≈ 2γ/h ≈ 500 Pa ≫ hydrostatisch ≈ 60 Pa bei 5 mm
Füllhöhe), entlang der benetzten Platine kann die Masse aber kriechen. Abstand zu den Clip-Pads 0.55 mm (PCB_OUTLINE Kap. 6).
→ Dosieren in kleinen Portionen, Austrittsseite mit Spiegel kontrollieren, Überschuss trocken abnehmen (MONTAGE Kap. 4/5);
Vergussprobe vor dem ersten Muster (**PROTOTYP-PRÜFUNG** V-1).

## 6 Empfehlung

**Electrolube ER2223, ein Material für Schott, Kragen und Kantenversiegelung der Sonde.**

1. **Tg 140 °C laut TDS** (S. 2), **Härtebedingung unbekannt**. Bei aminisch gehärteten Epoxiden begrenzt die Härtetemperatur
   den erreichbaren Tg; ob nach 60-°C-Härtung Tg ≥ 80 °C (K-4) erreicht wird, ist **offen** (W-2). Nachweis: Anfrage an
   Electrolube (Anhang A) oder Kriechprobe V-6 (Kap. 12); für die Prototypen genügt K-7 nach A-1 (168 h bei 65 °C ohne
   Erweichen/Ablösen), für die **Serie ist der Tg-Nachweis Pflicht**. Es wird **nachgehärtet: 24 h Raumtemperatur, danach 4 h bei 60 °C** (TDS S. 1 „Cure Time
   (60 °C) 4 hours“; S. 3 „post-cure at high temperature if required“). 60 °C liegt 32 K unter der HDT von ASA. Gerät:
   Wärmeschrank oder Filamenttrockner mit separatem Thermometer (**ANNAHME**: in der Werkstatt mit Bambu-Drucker vorhanden).
   Rückfrage an Electrolube (Tg nach 24 h RT und nach 24 h RT + 4 h 60 °C, Anhang A) offen.
2. **800 mPa·s** (S. 1): füllt 0.15-mm-Spalte und die Tasche U3/C24, entgast ohne Vakuum, lässt sich als dünne Kantenschicht
   auftragen.
3. **Resin Pack** (S. 1–2): Harz und Härter vordosiert. Für kleine Ansätze wird der Beutel einmal in zwei Flaschen
   abgefüllt und je Ansatz 3.45 : 1 auf 0.01 g gewogen (Variante M-A, TDS S. 3 „Bulk Mixing“; Kap. 7); Mischen des ganzen
   Beutels bleibt Rückfall (M-B).
4. **Kein CMR-Stoff** (SDB A und B: keine H340/H350/H360), im Gegensatz zu 832HT (H360).
5. Bezug in der Schweiz (Simpex), Datenblatt beim Händler verlinkt.

Nachteile, offen ausgewiesen:
- **Ungefüllt, CTE 70 ppm/K** statt „mineralisch gefüllt, niedriger CTE“ (K-4). FR4 z-Achse 60 ppm/K
  (`Kingboard_KB-6160A_TechnicalInformation.pdf` S. 1), in der Ebene nicht im lokalen Datenblatt (**ANNAHME** 14–17 ppm/K). Die
  Fuge ist dünn (0.15 mm) und das Volumen klein (62 mm³). Nachweis der Dichtheit über Temperaturwechsel ist ohnehin
  K-7 (50 Zyklen −10/+65 °C, Farbeindringprüfung). → Entscheid Sicherheit (Kap. 9).
- **Kleinste Gebinde 250 g** (Beutel; sonst 5-kg-Kit). Ohne Abfüllen müsste je Sitzung ein Beutel ganz gemischt werden
  (250 g für ≈ 0.2 g je Sensor). Abfüllen (M-A) ist vom Hersteller für Resin Packs nicht beschrieben → Anfrage Anhang A,
  Sicherheit Runde 2: zulässig unter MA-1 … MA-5; V-3 je Ansatz. Kosten Kap. 7.
- **Topfzeit 30 min** (S. 1): Sensoren vor dem Mischen vollständig vorbereiten; ≤ 8 Sensoren pro Ansatz (**ANNAHME**, am
  Muster Zeit pro Sensor messen).
- Lieferzeit laut Simpex 8 Wochen → früh bestellen.
- Haftung auf ASA nicht im Datenblatt → Anrauen (K-5), **PROTOTYP-PRÜFUNG** V-2.
- Eine neuere TDS-Fassung „ER2223-Encapsulation-Resins-EN-09Aug23-TB.pdf“ (MacDermid Alpha) ist im Netz verzeichnet, die
  URL liefert aber nichts Lesbares (Abruf 2026-11-08/09). Abgelegt ist Rev. 4 (Mar 2019). Neuere Fassung beim Hersteller
  anfordern (Anhang A) und Tg, CTE, Härtung vergleichen.

## 7 Kosten (15–20 Sensoren)

**Gebinde (Recherche 2026-11-09):** ER2223 gibt es nur als Resin Pack 250 g (EER2223RP250G) und als Kit 5 kg (EER2223K5K)
(Produktcodes `Electrolube_ER2223-PartA_SDS_Rev0.64-2023-10-27_SV.pdf` S. 1). Eine Doppelkartusche oder kleinere Beutel wurden
nicht gefunden (Suche Simpex, Distrelec, RS; RS UK listet nur den 250-g-Beutel, £ 34.23 für 1–5 Stück, Suchtreffer). Die 5 kg
sind für 20 Sensoren unsinnig (Haltbarkeit 12 Monate, TDS S. 1). Doppelkartuschen 50 ml anderer Hersteller mit Tg ≥ 80 °C und
niedriger Viskosität wurden nicht gefunden (MG 832HD 50 ml: Tg 41 °C; 832FXT: Tg 20 °C; Loctite E-60NC: 13 000 cP, Tg nicht
angegeben). Der Kostenhebel ist deshalb das **Abfüllen und Wägen kleiner Ansätze** (Variante M-A, MONTAGE Kap. 3a): Das TDS
beschreibt neben dem Resin Pack ausdrücklich „Bulk Mixing“ im richtigen Verhältnis (S. 3) und das Verhältnis 3.45 : 1 nach
Gewicht (S. 1). Wegen der Waagengenauigkeit (Auflösung ≠ Genauigkeit) gilt nach Sicherheit Runde 2 (MA-4) ein **Mindestansatz von 8 g
(6.90 g A + 2.00 g B)** und eine Kontrolle mit Prüfgewichten vor jeder Sitzung. Neu ist nur das Umfüllen aus dem Beutel in dicht schliessende Flaschen.

Sicherheit Runde 2 (`docs/reviews/phase6_vergussmasse_sicherheit.md` R2.2): **M-A ist zulässig unter MA-1 … MA-5**
(Gebinde kindergesichert, HDPE für den Härter, abgeschlossener Sekundärbehälter, nur ein angebrochener Satz; Etikett mit
Signalwort, Piktogrammen, H-/P-Sätzen, „Kein Lebensmittel – nicht trinken“, Daten, verantwortlicher Person, 145; Farbdeckel,
eigene Pipetten, nie beide Flaschen offen; Haltbarkeit 3 Monate (**ANNAHME**), Härter im 40-°C-Wasserbad anwärmen;
Prüfgewicht, Mindestansatz 8 g; Abfüllen in Auffangwanne mit Trichter, Beutelreste verkneten und aushärten). Umgesetzt in
`docs/manuals/MONTAGE_SENSOR.md` Kap. 1 und 3a. **MA-6:** Ohne Antwort von Electrolube ist M-A trotzdem zulässig, wenn MA-1,
MA-2, MA-4 umgesetzt und V-3 an jedem Ansatz sowie V-6 einmal mit einem gewogenen Ansatz bestanden sind (Entscheid
Orchestrator).

**Mengen M-A:** je Sensor 2 Ansätze (Schott; Kragen + Kanten) à 8 g auf Gruppen von 8 Sensoren (**ANNAHME**) → 2 g je Sensor.
Prototyp (5 Sensoren, Vorversuche V-1 … V-3, V-6) ≈ 6 Ansätze ≈ 48 g; Serie 15 (2 Gruppen) 4 Ansätze ≈ 32 g. Ein Beutel
(250 g) reicht je Bauserie mengenmässig; wegen der Haltbarkeit von 3 Monaten nach dem Abfüllen (MA-3) wird **je Bauserie
(Prototyp, Serie) ein Beutel** gerechnet → **2 Beutel**.

| Posten | **M-A (gerechnet)** | M-B (nur Hinweis) |
|---|---|---|
| Beutel ER2223 250 g, Simpex, CHF 38.20 exkl. / **41.29 inkl. 8.1 % MWST**, zzgl. Versand (Betrag nicht angegeben), Lieferzeit 8 Wochen | 1 je Bauserie | 1 je Sitzung |
| Prototyp 5 + Serie 15 | **2 Beutel = 82.58 CHF** | 6 Beutel = 247.74 CHF |
| Stückkosten (Verbrauch 2 g × 0.165 CHF/g, im Modell + 5 % Ausschuss) | **0.33 CHF/Sensor** | – |
| Einmalkosten je Bestellung (Beutel minus gerechneter Verbrauch) | Prototyp 39.56 CHF, Serie 36.09 CHF | – |
| Zubehör und Schutzausrüstung (Kap. 7.1), einmalig je Projekt | 229 CHF (**ANNAHME**) | gleich (ohne Flaschen/Prüfgewichte ≈ 194 CHF) |

**Neue Kostenzahlen** (`hardware/sensor/gen/cost_rev_b.py` mit Position „Verguss ER2223 Verbrauch“ statt „Versiegelung
(ANNAHME) 0.40“ und lokaler Einmalposition Beutel; `scripts/cost_final_phase5.py` neu gerechnet → `docs/reviews/phase5_kosten_final.md`,
`hardware/sensor/out/COSTS_REV_B.md`), Einordnung als Einmalkosten nach D-005 (Orchestrator):

| Szenario | Stückkosten (D-005) vorher → neu | Einmalkosten vorher → neu | Vollkosten/Sensor vorher → neu |
|---|---|---|---|
| Prototyp 5 / 5 | 9.23 → **9.15 CHF** | 139.34 → 178.90 CHF | 37.09 → **44.93 CHF** |
| Serie 20 / 16 / 15 (4 × 100 µF) | 8.38 → **8.31 CHF** | 141.85 → 177.94 CHF | 17.84 → **20.17 CHF** |
| Serie (2 × 100 µF) | 8.17 → 8.09 CHF | 141.85 → 177.94 CHF | 17.62 → 19.96 CHF |
| Serie mit „Pre-reflow“ (Vorbehalt) | 10.60 → 10.53 CHF | | |
| System A (Serie + Gateway + Zubehör 229) | – | – | 601.33 CHF total, 40.09 CHF/Sensor |
| System B (Prototyp + Serie + Gateway + Zubehör) | – | – | 825.99 CHF total, 55.07 CHF/Sensor (15) |

REQ-FAB-04 (< 10 CHF Stückkosten) bleibt erfüllt (Vorbehalt „Pre-reflow“ wie bisher). Die Systemsummen enthalten auch die
seit Phase 5 nachgeführten Gateway-Zahlen (D-028/D-029, anderer Agent); der Verguss-Anteil daran ist 229 + 2 × ≈ 38 CHF.

### 7.1 Einkaufspositionen Zubehör (für die Einkaufsliste des Orchestrators; Preise **ANNAHME**, nicht recherchiert)

| Pos | Artikel | Spezifikation | CHF (ANNAHME) |
|---|---|---|---|
| V-Z1 | Feinwaage | 0.01 g Auflösung, ≥ 200 g, Justiergewicht; **nur falls nicht vorhanden** | 25 |
| V-Z2 | Prüfgewichte | 1 g und 5 g, Klasse F1 oder M1 (MA-4) | 20 |
| V-Z3 | Laborflaschen | B: HDPE ≈ 60 ml, A: HDPE/Glas ≈ 250 ml, je **kindergesicherter Verschluss** (MA-1); Etiketten, Farbmarker rot/blau (MA-2) | 15 |
| V-Z4 | Sekundärbehälter | dicht schliessende Kunststoffbox, abschliessbar (Vorhängeschloss), Saugmaterial Vermiculit/Katzenstreu (MA-1) | 25 |
| V-Z5 | Auffang/Abfüllen | Auffangwanne bzw. Alu-Schalen ≥ 20 × 15 cm, 2 PE-Trichter, Einweg-Pipetten, Spatel, Mischbecher (MA-5) | 12 |
| V-Z6 | Dosieren | Einwegspritzen 1/3 ml Luer-Lock, stumpfe Kanülen 18/20 G, feiner Pinsel | 15 |
| V-Z7 | Handschuhe | Nitril ≥ 0.1 mm, Box (K-3; Beständigkeitsliste anfordern) | 12 |
| V-Z8 | Augen/Gesicht | Chemikalien-Schutzbrille EN 166 (dicht) + Visier | 30 |
| V-Z9 | Körper/Erste Hilfe | Kunststoffschürze, Augenspülflasche 500 ml | 25 |
| V-Z10 | Atemschutz | Halbmaske mit Filter A (EN 14387) | 40 |
| V-Z11 | Thermometer | für Trockner/Wärmeschrank (≤ 65 °C Kontrolle, 80 °C für V-3/V-6) | 10 |
| | **Summe** | | **229** |
| V-M1 | Vergussmasse | Electrolube ER2223 Resin Pack 250 g, Simpex EER2223RP250G, 2 Stück (Prototyp, Serie) | 82.58 (inkl. MWST, Preis belegt) |

Nicht enthalten: Ventilator, Wärmeschrank/Filamenttrockner, Wärmeschrank ≥ 80 °C (**ANNAHME** vorhanden).

## 8 Sicherheit nach SDB (für MONTAGE Kap. 1/4/5)

| Teil | Einstufung | Quelle |
|---|---|---|
| A (Harz, schwarz) | Achtung; H315 Hautreizung, H317 allergische Hautreaktion, H319 schwere Augenreizung, H411 giftig für Wasserorganismen | `Electrolube_ER2223-PartA_SDS_Rev0-2016-10-19_EN.pdf` S. 1; Stand 2023 gleich: `…_Rev0.64-2023-10-27_SV.pdf` S. 2 |
| B (Härter, farblos–hellbraun) | **Gefahr**; H302 gesundheitsschädlich beim Verschlucken, **H314 schwere Verätzungen der Haut und schwere Augenschäden**, H317, H318, H373 Organschäden bei längerer/wiederholter Exposition; Inhaltsstoff 4,4'-Methylenbis(cyclohexylamin), CAS 1761-71-3, 60–100 % | `Electrolube_ER2223-PartB_SDS_2023-10-02_HU.pdf` S. 2 (Abschn. 2), S. 3 (Abschn. 3) |
| Schutz | P280 Schutzhandschuhe/Schutzkleidung/Augenschutz/Gesichtsschutz; Handschuhe nach EN 374, Material nach Angabe des Handschuhherstellers; dicht schliessende Chemikalien-Schutzbrille nach EN 166; ausreichende Lüftung; nicht essen, trinken, rauchen | A (EN): S. 6 (Abschn. 8); B (HU): S. 2, S. 6 |

- Das SDB nennt **kein Handschuhmaterial**. Nitril-Einweghandschuhe sind **ANNAHME**; bei Kontakt sofort wechseln.
- Härter B ist ätzend und sensibilisierend: Beutel erst nach Anziehen von Brille, Visier, Handschuhen und Schürze öffnen,
  Ecke über der Alu-Schale abschneiden. Erste Hilfe, Lüftung und Lagerung nach SDB B Abschn. 4/7/8 (S. 3/5/6) vollständig in
  MONTAGE Kap. 3a übernommen (W-3, W-4).
- **SDB Teil B in DE/EN/FR/IT ist Voraussetzung vor dem ersten Beutel** (auch Vorversuche). Heute nur Ungarisch (H-Sätze
  sprachunabhängig; die Datei enthält ab S. 14 zusätzlich Teil A). Der Auftraggeber fordert es beim Händler an (Anhang B).
- 832HT Teil A ist als Repr. 1B (**H360**) eingestuft (`MGChemicals_832HT-Kit_SDS_V6.13-2026-07-17_EN-CA.pdf` S. 2–3,
  Einstufung nach WHMIS/HCS), deshalb nicht empfohlen.

## 9 Abweichung von K-4 und Fragen an die Prüfer

| Nr | Frage | Vorschlag |
|---|---|---|
| F-1 (Sicherheit) | K-4 verlangt „mineralisch gefüllt, niedriger CTE“. ER2223 ist ungefüllt (CTE 70). Kein recherchiertes Produkt erfüllt gleichzeitig: gefüllt, Tg ≥ 80 °C laut Datenblatt, fliessfähig für 0.15-mm-Spalte, kleines Gebinde, CH-Bezug, Kosten | **Antwort Sicherheit (phase6_vergussmasse_sicherheit.md Kap. 1): zulässig unter A-1 … A-5.** A-1/A-2 im Testplan PT11.19/PT11.23, A-3 Kap. 9a, A-4 in der FMEA F-60/F-63 eingetragen, A-5: PCB_OUTLINE und O-1-Wortlaut erst nach D-030 |
| F-2 (Elektronik) | Kantenversiegelung ändert C nur am Rand; Kalibrierung danach | Versiegeln **vor** der Vorkonditionierung (≥ 14 d wässern) und vor der 2-Punkt-Kalibrierung; Frequenz in Luft/Wasser vor und nach dem Versiegeln an einem Muster messen (V-4) |
| F-3 (Elektronik) | U3 im Kragen: ER2223 nennt keine Wärmeleitfähigkeit (ungefüllt, **ANNAHME** ≈ 0.2 W/m·K) | Für REQ-TMP-01 (Bodentemperatur) unkritisch, die Schicht über U3 ist 0.5 mm; am Muster prüfen (bestehende PROTOTYP-PRÜFUNG) |

## 9a Rückfallmasse (A-3)

Fällt K-7 an den ≥ 2 Mustern (A-1) oder der Schliff (A-2) durch, wird **keine Serie** mit ER2223 gebaut. Rückfall in dieser
Reihenfolge:
1. **Electrolube ER2221** (gefüllt, CTE 30 ppm/K, 6000 mPa·s, −40 … +150 °C; `Electrolube_ER2221_TDS_Rev8-2019-03.pdf`
   S. 1–2), **Bedingung:** Electrolube bestätigt schriftlich Tg ≥ 80 °C nach 24 h RT + ≤ 4 h 60 °C (oder V-6 bestanden),
   SDB A und B in DE/EN/FR/IT liegen vor, Vorversuche V-1 … V-3 mit ER2221 bestanden. Verarbeitung: höhere Viskosität →
   Vakuum oder längere Entlüftung (Kap. 5: Blase 5 mm in ≈ 3.5 min), Mischverhältnis 13.91 : 1 nach Gewicht nur als ganzer
   Beutel (Wägen von 0.27 g Härter auf 4 g ist mit 0.01 g zu ungenau, ± 3.7 %). CH-Bezug offen (nicht bei Simpex gefunden,
   RS UK Auslauf) → vor dem Rückfall Bezug klären.
2. Gleichwertige gefüllte Masse mit Datenblatt (Tg ≥ 80 °C nach Härtung ≤ 60 °C belegt, CTE ≤ 40 ppm/K, ≤ 10 000 mPa·s,
   kein CMR-Stoff), neue Auswahl mit Prüfung durch die Sicherheit.

## 10 Entscheidungsvorlage (Vorschlag D-030)

- **Entscheid:** Vergussmasse für Schott und Kragen sowie Kantenversiegelung der Sonde: **Electrolube ER2223** (Resin Pack
  250 g). Verarbeitung **M-A** (Beutel abfüllen, 8-g-Ansätze wägen; MONTAGE Kap. 3a), Rückfall M-B (ganzer Beutel je Sitzung).
  Sondenflächen bleiben ohne Zusatzschicht (Lötstopplack). Aushärtung 24 h RT + 4 h 60 °C. Abweichung von K-4 („gefüllt,
  niedriger CTE“) unter A-1 … A-5.
- **Kosten (D-005, Einordnung Orchestrator):** Vergussmasse als **Einmalkosten je Bauserie** (1 Beutel 41.29 CHF minus Verbrauch),
  Stückkosten nur Verbrauch 0.33 CHF/Sensor; Zubehör/Schutz 229 CHF einmalig je Projekt (**ANNAHME**). Serie: Stückkosten
  **8.31 CHF**, Vollkosten **20.17 CHF/Sensor** (Kap. 7).
- **Alternativen:** ER2221 (gefüllt, Tg unbekannt; Rückfall Kap. 9a), MG 832HT (H360, 22 000 cP), Stycast 2651-40/Cat 9
  (≈ 300 CHF), ER2188/832B (Tg < 80 °C); für die Sonde Acryllack, Epoxid vollflächig, Schrumpfschlauch (Kap. 3).
- **Begründung:** Tg 140 °C laut TDS (Härtebedingung unbekannt; Tg nach 60-°C-Härtung offen, W-2), 800 mPa·s, kein CMR-Stoff,
  CH-Bezug; Kantenversiegelung kostet ≈ 1–2 % Spanne statt 12–39 % bei Flächenbeschichtung. Sicherheit: kein Veto (Runden 1 und 2).
- **Freigabebedingungen** (Sicherheit Runde 2, R2.4):
  1. **Vor dem Öffnen des ersten Beutels** (auch V-1 … V-3): SDB Teil B in DE/EN/FR/IT liegt vor und ist abgelegt;
     Beständigkeitsliste der Handschuhe abgelegt (K-3); Schutzausrüstung nach MONTAGE Kap. 1/3a vorhanden.
  2. **Variante M-A** nur mit MA-1 und MA-2 sowie MA-3 … MA-5 (umgesetzt in MONTAGE Kap. 3a); ohne Electrolube-Antwort nach
     MA-6 (V-3 je Ansatz, V-6 einmal mit gewogenem Ansatz; Entscheid Orchestrator). Sonst M-B.
  3. **Vor dem Musterverguss:** V-1 … V-3 bestanden.
  4. **Vor der Serie:** PT11.19 an ≥ 2 Mustern und PT11.23 bestanden (A-1/A-2), sonst Rückfall Kap. 9a (A-3); Tg-Nachweis
     (Electrolube schriftlich oder V-6) erbracht (W-2).
  5. FMEA F-63 (S6/O4/D4 = RPZ 96) und F-60 (S6/O3/D6 = RPZ 108) nachgeführt – **erledigt** (`phase5_fmea_light.md`).
- **Folgeänderungen bei Freigabe:** `docs/interfaces/PCB_OUTLINE.md` Kap. 7 („Epoxid mineralisch gefüllt … ANNAHME Typ“) in
  der nächsten Revision nachführen (A-5); MONTAGE O-1 auf „ER2223 (Abweichung K-4, D-030)“; Kostenmodell bereits umgestellt
  (`hardware/sensor/gen/cost_rev_b.py`, `scripts/cost_final_phase5.py`); INDEX.csv EP-K; Einkaufsliste um Kap. 7.1 ergänzen
  (Orchestrator).

## 11 Offene Punkte

1. Anfrage an Electrolube (Anhang A, versendet der Auftraggeber bzw. Orchestrator): Tg/CTE nach 24 h RT und nach 24 h RT + 4 h
   60 °C, Umfüllen aus dem Resin Pack, aktuelle TDS-Fassung. Nachhärtung 4 h @ 60 °C bleibt Pflicht. Ohne Antwort: V-6 vor der Serie.
2. **SDB Teil B in DE/EN/FR/IT beim Händler anfordern (Anhang B) – Voraussetzung vor dem ersten Beutel.** SDB ER2221 Teil B und
   Stycast/Cat 9 nicht beschafft. Beständigkeitsliste Handschuhe (CAS 1761-71-3, 25068-38-6) beim Handschuhhersteller holen.
3. Preis/Lager Distrelec CH (301-16-965) und Versandkosten Simpex im Warenkorb prüfen; Lieferzeit 8 Wochen → vor Musterankunft bestellen.
4. Kosteneinordnung: Einmalkosten nach D-005 (Vorgabe Orchestrator), Kap. 7; im Kostenmodell umgesetzt. Zubehör (Kap. 7.1) in die Einkaufsliste übernehmen (Orchestrator).
7. Wärmeschrank ≥ 80 °C für V-3/V-6 vorhanden? (**ANNAHME**; Filamenttrockner reichen oft nicht bis 80 °C, sonst DSC im Labor).
5. Membranrand (W-1), Fensterkleber (O-3) und Klemmring (O-4) sind **nicht** Teil dieser Wahl (ER2223 ist schwarz und so dünn,
   dass es in die Membran laufen würde).
6. Wärmeschrank/Filamenttrockner 60 °C vorhanden? (**ANNAHME**).

## 12 PROTOTYP-PRÜFUNGEN (Ergänzung Testplan)

| Nr | Prüfung | Kriterium |
|---|---|---|
| V-1 | Vergussprobe an Kragen + Schott mit FR4-Reststreifen 1.6 mm bzw. Ausschussplatine (Beutel 1) | Spalt rundum gefüllt, keine Blase in der Tasche (Schnitt), Austritt ≤ 0.3 mm über die Kragen-/Schottkante, Zeit pro Sensor notieren |
| V-2 | Haftung auf angerautem ASA und Lötstopplack: Probekörper 24 h RT + 4 h 60 °C, dann 7 d Wasser | kein Ablösen beim Abhebeln mit Klinge (Kohäsionsbruch im Epoxid oder Kunststoff) |
| V-3 | Härteprobe: Rest im Mischbecher (≥ 5 mm), wie Bauteile gehärtet, 1 h bei 80 °C | bleibt hart (Fingernagel ohne Eindruck), nicht klebrig |
| V-4 | Ein Muster (nicht S4/S5, A-1): Kanten erst in der Folgesitzung versiegeln; Messfrequenz in Luft und Wasser vor und nach der Versiegelung (Zelle **vor dem Auftragen** entnehmen, W-1; MONTAGE Prüfung 5a) | Änderung der Spanne ≤ 3 % (Abschätzung 1–2 %) |
| V-5 | Kantenversiegelung nach 30 d nass (Teil des Drifttests REQ-MES-06) | keine Ablösung an der Kante, kein Aufquellen; Drift mit/ohne Versiegelung vergleichen, falls eine Reserveplatine verfügbar |
| V-6 | **Kriechprobe 80 °C (Tg-Ersatznachweis, W-2), Pflicht vor der Serie** ohne schriftliche Tg-Angabe von Electrolube: Stab ≈ 4 × 10 × 60 mm (in Kapton-ausgekleideter Rinne gegossen, gehärtet wie die Bauteile), flach auf 2 Auflagen, Stützweite 50 mm, Mittellast **≈ 1.0 N (≈ 100 g)** → Randfaserspannung σ = 3FL/(2bh²) ≈ 0.45 MPa; 1 h bei 80 °C, unter Last auf Raumtemperatur abkühlen, entlasten, bleibende Durchbiegung mit Haarlineal und Fühlerlehre messen. Abschätzung: glasig (E ≈ 3 GPa, **ANNAHME**) elastisch ≈ 0.02 mm, oberhalb Tg (E ≈ 30 MPa, **ANNAHME**) ≈ 1.6 mm, die beim Abkühlen einfriert | bleibende Durchbiegung **< 0.2 mm** (**ANNAHME** Kriterium, an der Probe bestätigen); sonst Tg < 80 °C → Rückfall Kap. 9a bzw. DSC im Labor |
| K-7 | wie `phase4_sicherheit_kragen_firmware.md`, **mit A-1** (≥ 2 vollständige Muster nach freigegebenem Verfahren) und **A-2** (Schliff an Kragenunterkante z 1.3 … 3.5, Taschenwand U3, Kragenoberseite/Clip; Eindringen ≤ 0.5 mm); Testplan PT11.19/PT11.23 | Gate für F-1; Fail → A-3 (Kap. 9a) |

## Anhang A – Textvorlage Anfrage an Electrolube (Englisch)

An: Electrolube Technical Support (TechnicalSupportTeam@hkw.co.uk laut TDS-Bulletin; Adresse vor dem Versand auf
electrolube.com prüfen). Versand durch den Auftraggeber bzw. Orchestrator.

> Subject: ER2223 – Tg after low-temperature cure, decanting of resin packs, current TDS/SDS
>
> Dear Electrolube Technical Support,
>
> we intend to use ER2223 (EER2223RP250G) to pot a small sensor (approx. 0.2 g per unit, FR4 PCB with solder mask, ASA
> housing; ASA limits the cure temperature to 60 °C). Could you please answer the following:
>
> 1. The TDS (Revision 4, Mar 2019) states Tg 140 °C. Under which cure schedule was this measured? What Tg (and CTE below Tg)
>    is reached after (a) 24 h at 23 °C and (b) 24 h at 23 °C followed by 4 h at 60 °C? Is a Tg of at least 80 °C reached?
> 2. We need only small quantities per session (approx. 8 g). Is it acceptable to transfer part A and part B from an
>    unopened resin pack into separate, tightly closed containers (HDPE or glass) and to mix small batches by weight at
>    3.45 : 1 (balance resolution 0.01 g)? Which mix-ratio tolerance is acceptable, and how long may the opened components
>    be stored (15–35 °C, dry)?
> 3. Please send the current TDS (we found a reference to "ER2223 Encapsulation Resins EN 09Aug23") and the current Safety
>    Data Sheets for part A and part B in German or English.
>
> Thank you and kind regards

## Anhang B – Textvorlage Anforderung SDB beim Händler (Deutsch)

An: Simpex Electronic AG (Kontakt laut simpex.ch) bzw. Distrelec Schweiz. Versand durch den Auftraggeber.

> Betreff: Sicherheitsdatenblatt Electrolube ER2223 Teil B (Härter) – Artikel EER2223RP250G / Distrelec 301-16-965
>
> Guten Tag
>
> Wir möchten die Epoxid-Vergussmasse Electrolube ER2223, Resin Pack 250 g (EER2223RP250G), bestellen. Für die Verarbeitung
> benötigen wir vorab die aktuellen Sicherheitsdatenblätter für **Teil A (Harz) und Teil B (Härter)** in **Deutsch**
> (ersatzweise Französisch, Italienisch oder Englisch). Auf Ihrer Website bzw. bei Distrelec ist für Teil B nur eine
> ungarische Fassung (Stand 2023-10-02) verfügbar. Zusätzlich bitten wir um das aktuelle technische Datenblatt und um die
> aktuelle Lieferzeit.
>
> Freundliche Grüsse
