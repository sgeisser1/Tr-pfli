# fluidi – Vergussmasse (Kragen, Schott) und Versiegelung der Sonde (O-1, O-2)

| | |
|---|---|
| Stand | 2026-11-08, Phase 6, Mechanik-Agent. **Entwurf zur Prüfung** (Sicherheit, Elektronik) und Entscheidungsvorlage für den Orchestrator |
| Offene Punkte | O-1 Vergussmasse, O-2 Kantenversiegelung Sonde (`docs/manuals/MONTAGE_SENSOR.md` Kap. 0), REQ-MECH-07, PROJEKTAUFTRAG Techn. Anf. 1 („Versiegelung der Schnittkanten und der Sonde bewerten … mit Anleitung“) |
| Ergebnis | Empfehlung **Electrolube ER2223** (2K-Epoxid, Tg 140 °C, 800 mPa·s) für Schott, Kragen **und** Kantenversiegelung der Sonde; Sondenflächen bleiben unbeschichtet. Abweichung von K-4 („mineralisch gefüllt, niedriger CTE“) → Entscheid Sicherheit (Kap. 9) |
| Rechnung | `simulation/field/coat_epoxy.py` → `simulation/field/results/coat_epoxy.{txt,csv}` (neu), Grundlagen `simulation/field/REPORT.md` |
| Anleitung | `docs/manuals/MONTAGE_SENSOR.md` Kap. 1, 4, 5, 5a (ergänzt) |

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
| Füllstoff / Dichte gehärtet | ungefüllt, 1.10 g/ml (S. 2) | gefüllt, 1.88 g/ml (S. 2) | ungefüllt, 1.1 g/ml (S. 2) | gefüllt, Harz 1.5 g/cm³ (S. 1) |
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

1. **Tg 140 °C** (TDS S. 2), mit Abstand über 80 °C (K-4) und 65 °C Kopftemperatur (RB-03). Weil das TDS die
   Härtebedingung zum Tg nicht nennt, wird **nachgehärtet: 24 h Raumtemperatur, danach 4 h bei 60 °C** (TDS S. 1 „Cure Time
   (60 °C) 4 hours“; S. 3 „post-cure at high temperature if required“). 60 °C liegt 32 K unter der HDT von ASA. Gerät:
   Wärmeschrank oder Filamenttrockner mit separatem Thermometer (**ANNAHME**: in der Werkstatt mit Bambu-Drucker vorhanden).
   Rückfrage an Electrolube (Tg nach 24 h RT) offen; bestätigt Electrolube Tg ≥ 80 °C nach RT-Härtung, entfällt die Nachhärtung.
2. **800 mPa·s** (S. 1): füllt 0.15-mm-Spalte und die Tasche U3/C24, entgast ohne Vakuum, lässt sich als dünne Kantenschicht
   auftragen.
3. **Resin Pack** (S. 1–2): Harz und Härter vorgewogen, Mischen im Beutel, kein Wägefehler bei 3.45 : 1.
4. **Kein CMR-Stoff** (SDB A und B: keine H340/H350/H360), im Gegensatz zu 832HT (H360).
5. Bezug in der Schweiz (Simpex), Datenblatt beim Händler verlinkt.

Nachteile, offen ausgewiesen:
- **Ungefüllt, CTE 70 ppm/K** statt „mineralisch gefüllt, niedriger CTE“ (K-4). FR4 z-Achse 60 ppm/K
  (`Kingboard_KB-6160A_TechnicalInformation.pdf` S. 1), in der Ebene nicht im lokalen Datenblatt (**ANNAHME** 14–17 ppm/K). Die
  Fuge ist dünn (0.15 mm) und das Volumen klein (62 mm³). Nachweis der Dichtheit über Temperaturwechsel ist ohnehin
  K-7 (50 Zyklen −10/+65 °C, Farbeindringprüfung). → Entscheid Sicherheit (Kap. 9).
- **Beutel muss ganz gemischt werden** (250 g für ≈ 0.2 g Bedarf je Sensor); Rest sicher aushärten lassen (Exothermie,
  MONTAGE Kap. 3a). Kosten Kap. 7.
- **Topfzeit 30 min** (S. 1): Sensoren vor dem Mischen vollständig vorbereiten; ≤ 8 Sensoren pro Beutel (**ANNAHME**, am
  Muster Zeit pro Sensor messen).
- Lieferzeit laut Simpex 8 Wochen → früh bestellen.
- Haftung auf ASA nicht im Datenblatt → Anrauen (K-5), **PROTOTYP-PRÜFUNG** V-2.

## 7 Kosten (15–20 Sensoren)

| Posten | Menge | CHF |
|---|---|---|
| ER2223 Resin Pack 250 g, Simpex | 1 Beutel | 38.20 exkl. MWST, 41.29 inkl. 8.1 % MWST, zzgl. Versand (Betrag nicht angegeben) |
| Verbrauch je Sensor | ≈ 0.19 g | ≈ 0.03 (bei 0.165 CHF/g inkl. MWST) |
| Beutel je Bauserie | Schott und Kragen in **getrennten Sitzungen** (Schott muss vor dem Kragen hart sein) | 2 Sitzungen je Gruppe ≤ 8 Sensoren |
| Prototyp (5 Sensoren) | Beutel 1: Vorversuche V-1/V-2/V-3; Beutel 2: Schott aller 5; Beutel 3: Kragen aller 5 + Kanten von 4. Kanten des V-4-Musters nach der Messung in der ersten Serien-Sitzung (sonst 4. Beutel) | 3 Beutel = 123.87 inkl. MWST (4 Beutel: 165.16) |
| Serie 15 Sensoren in 2 Gruppen, rollierend (Sitzung 1: Schott G1; 2: Kragen G1 + Schott G2; 3: Kragen G2) | 3 Beutel | 123.87 inkl. MWST = **8.26 CHF/Sensor** |
| Serie 20 Sensoren, 3 Gruppen rollierend | 4 Beutel | 165.16 inkl. MWST = 8.26 CHF/Sensor |
| Kleinmaterial: Einwegspritzen 1/3 ml Luer-Lock, stumpfe Kanülen 18–20 G, Mischbecher, Alu-Schale, Nitrilhandschuhe, Schutzbrille | – | **ANNAHME** ≈ 20 CHF einmalig, nicht recherchiert |

Bewertung gegen REQ-FAB-04 (D-005): Der Materialverbrauch (0.03 CHF/Sensor) liegt unter der bisherigen ANNAHME 0.40 CHF.
Der Beutelpreis ist aber **pro Sitzung fix** und unabhängig von der Stückzahl, also wie ein Setup-Posten. Zählt man ihn zu den
Stückkosten, steigen sie in der Serie um ≈ 7.9 CHF (8.26 − 0.40) auf ≈ 16 CHF → REQ-FAB-04 **verfehlt**. Als Einmalkosten pro
Bauserie (analog JLC-Setup) bleiben die Stückkosten bei ≈ 8.0 CHF (8.38 − 0.40 + 0.03, ohne 5 % Ausschussaufschlag; `docs/reviews/phase5_kosten_final.md`
Kap. 1, Posten 0.40 in `hardware/sensor/gen/cost_rev_b.py` Z. 59). → **Einordnung entscheidet der Orchestrator bzw. der Auftraggeber** (Vorschlag: Einmalkosten pro Sitzung).
Hebel: grössere Gruppen pro Beutel, wenn die gemessene Zeit pro Sensor es zulässt (z. B. 15 Sensoren in einer Gruppe:
2 Beutel = 82.58 CHF = 5.51 CHF/Sensor). Gebinde unter 250 g bietet Electrolube für ER2223 laut SDB-Produktcodes nicht an
(Pack 250 g, Kit 5 kg: `Electrolube_ER2223-PartA_SDS_Rev0.64-2023-10-27_SV.pdf` S. 1 „EER2223RP250G, EER2223K5K“).

## 8 Sicherheit nach SDB (für MONTAGE Kap. 1/4/5)

| Teil | Einstufung | Quelle |
|---|---|---|
| A (Harz, schwarz) | Achtung; H315 Hautreizung, H317 allergische Hautreaktion, H319 schwere Augenreizung, H411 giftig für Wasserorganismen | `Electrolube_ER2223-PartA_SDS_Rev0-2016-10-19_EN.pdf` S. 1; Stand 2023 gleich: `…_Rev0.64-2023-10-27_SV.pdf` S. 2 |
| B (Härter, farblos–hellbraun) | **Gefahr**; H302 gesundheitsschädlich beim Verschlucken, **H314 schwere Verätzungen der Haut und schwere Augenschäden**, H317, H318, H373 Organschäden bei längerer/wiederholter Exposition; Inhaltsstoff 4,4'-Methylenbis(cyclohexylamin), CAS 1761-71-3, 60–100 % | `Electrolube_ER2223-PartB_SDS_2023-10-02_HU.pdf` S. 2 (Abschn. 2), S. 3 (Abschn. 3) |
| Schutz | P280 Schutzhandschuhe/Schutzkleidung/Augenschutz/Gesichtsschutz; Handschuhe nach EN 374, Material nach Angabe des Handschuhherstellers; dicht schliessende Chemikalien-Schutzbrille nach EN 166; ausreichende Lüftung; nicht essen, trinken, rauchen | A (EN): S. 6 (Abschn. 8); B (HU): S. 2, S. 6 |

- Das SDB nennt **kein Handschuhmaterial**. Nitril-Einweghandschuhe sind **ANNAHME**; bei Kontakt sofort wechseln.
- Härter B ist ätzend und sensibilisierend: Beutel erst nach Anziehen von Brille und Handschuhen öffnen, Ecke über der
  Alu-Schale abschneiden.
- Der deutschsprachige SDB-Stand 2023 für Teil B lag nicht vor (nur Ungarisch; H-Sätze sprachunabhängig). Beim Kauf das SDB
  in einer Landessprache beim Händler anfordern (**offen**).
- 832HT Teil A ist als Repr. 1B (**H360**) eingestuft (`MGChemicals_832HT-Kit_SDS_V6.13-2026-07-17_EN-CA.pdf` S. 2–3,
  Einstufung nach WHMIS/HCS), deshalb nicht empfohlen.

## 9 Abweichung von K-4 und Fragen an die Prüfer

| Nr | Frage | Vorschlag |
|---|---|---|
| F-1 (Sicherheit) | K-4 verlangt „mineralisch gefüllt, niedriger CTE“. ER2223 ist ungefüllt (CTE 70). Kein recherchiertes Produkt erfüllt gleichzeitig: gefüllt, Tg ≥ 80 °C laut Datenblatt, fliessfähig für 0.15-mm-Spalte, kleines Gebinde, CH-Bezug, Kosten | ER2223 zulassen; Gate ist K-7 (Temperaturwechsel + Farbeindringprüfung) am Muster. Rückfall: ER2221 (gefüllt, CTE 30), wenn Electrolube Tg ≥ 80 °C bestätigt |
| F-2 (Elektronik) | Kantenversiegelung ändert C nur am Rand; Kalibrierung danach | Versiegeln **vor** der Vorkonditionierung (≥ 14 d wässern) und vor der 2-Punkt-Kalibrierung; Frequenz in Luft/Wasser vor und nach dem Versiegeln an einem Muster messen (V-4) |
| F-3 (Elektronik) | U3 im Kragen: ER2223 nennt keine Wärmeleitfähigkeit (ungefüllt, **ANNAHME** ≈ 0.2 W/m·K) | Für REQ-TMP-01 (Bodentemperatur) unkritisch, die Schicht über U3 ist 0.5 mm; am Muster prüfen (bestehende PROTOTYP-PRÜFUNG) |

## 10 Entscheidungsvorlage (Vorschlag D-030)

- **Entscheid:** Vergussmasse für Schott und Kragen sowie Kantenversiegelung der Sonde: **Electrolube ER2223** (Resin Pack
  250 g). Sondenflächen bleiben ohne Zusatzschicht (Lötstopplack). Aushärtung 24 h RT + 4 h 60 °C.
- **Alternativen:** ER2221 (gefüllt, Tg unbekannt), MG 832HT (H360, 22 000 cP), Stycast 2651-40/Cat 9 (≈ 300 CHF),
  ER2188/832B (Tg < 80 °C); für die Sonde Acryllack, Epoxid vollflächig, Schrumpfschlauch (Kap. 3).
- **Begründung:** Tg 140 °C, 800 mPa·s, Resin Pack ohne Wägen, kein CMR-Stoff, CH-Bezug; Kantenversiegelung kostet ≈ 1–2 %
  Spanne statt 12–39 % bei Flächenbeschichtung.
- **Auflagen:** F-1 durch Sicherheit; Kosteneinordnung Kap. 7; Vorversuche V-1 … V-3 vor dem ersten Muster-Verguss.
- **Folgeänderungen bei Freigabe:** `docs/interfaces/PCB_OUTLINE.md` Kap. 7 („Epoxid mineralisch gefüllt … ANNAHME Typ“) in
  der nächsten Revision nachführen; `hardware/sensor/gen/cost_rev_b.py` Z. 59 („Versiegelung Sonde/Kragen (ANNAHME)“ 0.40 CHF) und `scripts/cost_final_phase5.py` neu rechnen; INDEX.csv EP-K (vorläufig eingetragen).

## 11 Offene Punkte

1. Tg von ER2223 nach 24 h Raumtemperatur bei Electrolube anfragen (TechnicalSupportTeam, Adresse im TDS-Bulletin); bis dahin
   Nachhärtung 4 h @ 60 °C Pflicht.
2. SDB Teil B in Deutsch/Französisch/Italienisch beim Händler anfordern; SDB ER2221 Teil B und Stycast/Cat 9 nicht beschafft.
3. Preis/Lager Distrelec CH (301-16-965) und Versandkosten Simpex im Warenkorb prüfen; Lieferzeit 8 Wochen → vor Musterankunft bestellen.
4. Kosteneinordnung Beutelpreis (Kap. 7) – Orchestrator/Auftraggeber.
5. Membranrand (W-1), Fensterkleber (O-3) und Klemmring (O-4) sind **nicht** Teil dieser Wahl (ER2223 ist schwarz und so dünn,
   dass es in die Membran laufen würde).
6. Wärmeschrank/Filamenttrockner 60 °C vorhanden? (**ANNAHME**).

## 12 PROTOTYP-PRÜFUNGEN (Ergänzung Testplan)

| Nr | Prüfung | Kriterium |
|---|---|---|
| V-1 | Vergussprobe an Kragen + Schott mit FR4-Reststreifen 1.6 mm bzw. Ausschussplatine (Beutel 1) | Spalt rundum gefüllt, keine Blase in der Tasche (Schnitt), Austritt ≤ 0.3 mm über die Kragen-/Schottkante, Zeit pro Sensor notieren |
| V-2 | Haftung auf angerautem ASA und Lötstopplack: Probekörper 24 h RT + 4 h 60 °C, dann 7 d Wasser | kein Ablösen beim Abhebeln mit Klinge (Kohäsionsbruch im Epoxid oder Kunststoff) |
| V-3 | Härteprobe: Rest im Mischbecher (≥ 5 mm), wie Bauteile gehärtet, 1 h bei 80 °C | bleibt hart (Fingernagel ohne Eindruck), nicht klebrig |
| V-4 | Ein Muster: Kanten erst in der Folgesitzung versiegeln; Messfrequenz in Luft und Wasser vor und nach der Versiegelung (Zelle vor der 60-°C-Nachhärtung entnehmen; MONTAGE Prüfung 5a) | Änderung der Spanne ≤ 3 % (Abschätzung 1–2 %) |
| V-5 | Kantenversiegelung nach 30 d nass (Teil des Drifttests REQ-MES-06) | keine Ablösung an der Kante, kein Aufquellen; Drift mit/ohne Versiegelung vergleichen, falls eine Reserveplatine verfügbar |
| K-7 | wie `phase4_sicherheit_kragen_firmware.md` (unverändert) | Gate für F-1 |
