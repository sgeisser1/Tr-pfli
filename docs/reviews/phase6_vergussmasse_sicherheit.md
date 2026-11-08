# Phase 6 – Prüfung Vergussmasse ER2223 / Kantenversiegelung (Vorschlag D-030) – Sicherheit

| | |
|---|---|
| Datum | 2026-11-09 |
| Prüfer | Sicherheits-Agent (frischer Kontext, Prüfer ≠ Ersteller, Vetorecht) |
| Gegenstand | Commit fe5adac: `docs/concepts/vergussmasse_versiegelung.md` (Vorschlag D-030), `docs/manuals/MONTAGE_SENSOR.md` Kap. 0, 1, 3a, 4, 5, 5a, 8; `simulation/field/coat_epoxy.py` |
| Grundlagen | `docs/reviews/phase4_sicherheit_kragen_firmware.md` K-1…K-7; `docs/reviews/phase5_fmea_light.md` F-10/F-60/F-63; `docs/reviews/phase5_testplan_beitrag_sicherheit.md` ST-W4; `docs/manuals/PROGRAMMIEREN_SENSOR.md` Kap. 5; TDS/SDB unter `docs/references/` (selbst gelesen, `pdftotext`) |
| Ergebnis | **Kein Veto.** 0 kritisch, 5 wichtig, 6 klein. Die Abweichung von K-4 („mineralisch gefüllt, niedriger CTE“) ist **unter den Auflagen A-1…A-5 (Kap. 1) zulässig**. W-1…W-4 sind vor dem ersten Öffnen eines Beutels (auch für die Vorversuche V-1…V-3) umzusetzen, W-5 vor der Serienfreigabe. |

Zitierweise: Datei unter `docs/references/` bzw. `docs/datasheets/`, Seite. Übersetzungen aus dem ungarischen SDB Teil B
stammen vom Prüfer (**keine amtliche Übersetzung**, nur bis zum Vorliegen eines SDB in Landessprache).

## 1 K-4: Abweichung „ungefüllt, CTE 70“ – zulässig mit Nachweis über K-7?

**Quelle K-4:** `docs/reviews/phase4_sicherheit_kragen_firmware.md` Kap. 1.2, K-4 (wichtig): „ein einziges, mineralisch
gefülltes Epoxid (Tg ≥ 80 °C, niedriger CTE) für den ganzen Kragen, blasenfrei“. Übernommen in `docs/interfaces/PCB_OUTLINE.md`
Z. 133 („Epoxid mineralisch gefüllt, Tg ≥ 80 °C (ANNAHME Typ)“) und FMEA F-63 („K-4 (Tg ≥ 80 °C, gefüllt)“).

Der Kern von K-4 war: **eine** harte, haftende Masse im Leckpfad, kein weiches Gel; Tg über der Kopftemperatur; wenig
thermische Dehnungsdifferenz zum FR4. ER2223 erfüllt die ersten beiden Punkte (Typ, eine Masse). Den dritten erfüllt es nicht.

**Risikobetrachtung (selbst):**

| Risiko | Bewertung |
|---|---|
| Dehnungsdifferenz zu FR4 in der Ebene | CTE 70 ppm/K (`Electrolube_ER2223_TDS_Rev4-2019-03.pdf` S. 2) gegen FR4 in-plane ≈ 14–17 ppm/K (**ANNAHME**, nicht im lokalen Datenblatt; z-Achse 60 ppm/K, `Kingboard_KB-6160A_TechnicalInformation.pdf` S. 1). Spannungsfrei ist die Masse etwa bei der Nachhärtetemperatur (60 °C). Bis −10 °C (K-7, Lagerung RB-03): Δε ≈ 55 ppm/K × 70 K ≈ 3.9 ‰. Bei E ≈ 2.5–3.5 GPa (**ANNAHME**, ungefülltes Epoxid, Shore D80 laut TDS S. 2) ergibt das am Rand der Fuge Schubspannungen in der Grössenordnung von 5–10 MPa. Das liegt im Bereich typischer Haftfestigkeiten auf Lötstopplack (**ANNAHME**). Gefährdet ist die **untere Kragenkante (z 1.3 … 3.5, Grenzfläche FR4/Epoxid)**, also genau der Eintritt des Leckpfads (Dichtlänge auf F nur 2.2 mm, phase4 Kap. 1.1). Eine gefüllte Masse (CTE ≈ 30) hätte etwa ein Drittel der Dehnungsdifferenz. |
| Grenzfläche zu ASA | CTE von ASA steht nicht im lokalen TDS (`BambuLab_ASA_TechnicalDataSheet_V2.0.pdf`, nur HDT S. 2). Typisch liegt er über 70 ppm/K (**ANNAHME**). Dann liegt ER2223 näher am ASA als eine gefüllte Masse, und der Kragenring schrumpft beim Abkühlen auf die Fuge (Druck quer zur Fuge). Das spricht eher für ER2223. Diese Grenzfläche ist aber nicht der kritische Pfad. |
| Spannung auf CR2032-Clip / Platine | Kein Clip-Pad im Verguss (Abstand 0.55 mm, `PCB_OUTLINE.md` Kap. 6). Ein Risiko besteht nur, wenn die dünnflüssige Masse (800 mPa·s, TDS S. 1) auf die Clip-Pads kriecht. Ein starrer Verguss über den Lötfahnen, die am Katalogminimum liegen (FMEA F-24), würde beim Zyklieren und beim Zellwechsel zusätzlich hebeln. Dagegen helfen die Anleitung (Wulst ≤ 0.3 mm, Spiegel, Prüfung 4/5) und V-1. U3/C24: Das Volumen ist klein (Tasche 1.2 mm). Unkritisch, wird in K-7 geprüft. |
| Wasser im Batterieraum | Ein Riss im Kragen öffnet den Pfad Erde → Zellfach. Laut phase4 Kap. 1.1 liegt im Kragen kein Netz der Energiequelle, also gibt es keine Erwärmung durch den Kragen selbst. Im Zellfach liegt dann aber die CR2032 im Wasser. Der Fall ist durch REQ-SAF-05 (Fach fluten, ST-W4) bereits abgedeckt: Kurzschlussstrom einer CR2032 im Wasser, Korrosion, kein Brand. Die Folge ist ein Funktions- und Korrosionsschaden, **kein kritisches Sicherheitsrisiko**. |
| Thermik | Exothermie im Bauteil vernachlässigbar (≈ 74 mm³ je Sensor). Tg siehe W-2: Die 140 °C sind für die vorgesehene Härtung **nicht belegt**. Nachhärtung 60 °C: ASA HDT 92 °C @ 1.8 MPa / 100 °C @ 0.45 MPa (`BambuLab_ASA_TechnicalDataSheet_V2.0.pdf` S. 2), ok. |
| Auslaugung im Pflanztopf | Nur bei unvollständiger Härtung (falsches Mischen, ohne Nachhärtung). Teil A H411, Teil B ätzendes Amin. Abgedeckt durch das Resin Pack (kein Wägefehler) und V-3 je Sitzung, siehe K-5. |

**Urteil F-1:** Die Abweichung ist **zulässig**. Die Folge eines Versagens bleibt beherrscht (kein Energiepfad im Kragen, REQ-SAF-05
geprüft), und das Risiko ist am Muster mit K-7 messbar. Die Alternativen sind schlechter: 832HT hat H360 (CMR) und
22 000 cP und füllt den 0.15-mm-Spalt schlecht, was Lunker gibt (F-60, RPZ 180). Bei ER2221 ist der Tg unbekannt. Weil
das Risiko gezielt an der unteren Kragenkante liegt und nur **ein** Opfermuster vorgesehen ist, gelten folgende Auflagen:

| Nr | Auflage |
|---|---|
| A-1 | K-7/ST-W4 an **mindestens 2 vollständigen Mustern** (Tauchen, Fluten, Leckstrom), die exakt mit dem freigegebenen Verfahren gebaut sind (ER2223, 24 h RT + 4 h 60 °C, gleiche Sitzung Kragen + Kanten). Das V-4-Muster zählt nicht (Fuge „nass auf hart“, Konzept Kap. 12). |
| A-2 | Schliff bzw. Farbeindringprüfung am Opfermuster **nach** den 50 Zyklen und 168 h: ausdrücklich die Grenzfläche FR4/Epoxid an der Kragenunterkante z 1.3 … 3.5 (beide Seiten), die Taschenwand U3 und die Kragenoberseite zum Clip (Masse auf Clip-Pads?). Kriterium: keine Ablösung, kein Eindringen über 0.5 mm. |
| A-3 | Rückfall definieren: Fällt A-1/A-2 durch, kommt eine gefüllte Masse (ER2221 nach Tg-Bestätigung oder gleichwertig) mit Vakuum bzw. längerer Entlüftung. Bis dahin keine Serie. |
| A-4 | FMEA nachführen: F-63 Massnahme „K-4 (Tg ≥ 80 °C, gefüllt)“ → „ER2223 ungefüllt, Abweichung K-4 nach D-030, Gate A-1/A-2“; O/D neu bewerten. F-60 Massnahme „Vergussmasse mit Datenblatt wählen“ als erledigt markieren. |
| A-5 | `PCB_OUTLINE.md` Z. 133 und die O-1-Zeile in MONTAGE erst **nach** dem Entscheid D-030 auf „ER2223 (Abweichung K-4, D-030)“ ändern. Bis dahin den Wortlaut von K-4 stehen lassen (siehe K-6). |

## 2 Stichprobe Zahlen und Zitate (selbst gegen die lokalen Dateien)

| Angabe (Konzept/Anleitung) | Lokale Quelle | Befund |
|---|---|---|
| Viskosität gemischt 800 mPa·s @ 23 °C, S. 1 | `Electrolube_ER2223_TDS_Rev4-2019-03.pdf` S. 1 | stimmt |
| Mischverhältnis 3.45 : 1 Gew., 2.90 : 1 Vol., S. 1 | dto. S. 1 | stimmt |
| Topfzeit 30 min (20 °C), Gelzeit 90 min (23 °C), S. 1 | dto. S. 1 | stimmt |
| Härtung 24 h @ 23 °C, 4 h @ 60 °C, 1 h @ 100 °C, S. 1 | dto. S. 1 | stimmt |
| Tg 140 °C, CTE 70, Wasseraufnahme < 0.25 %, Dichte 1.10, −40…+180 °C, S. 2 | dto. S. 2 | Werte stimmen. Die Härtebedingung zum Tg fehlt im TDS, richtig ausgewiesen. Aussage „mit Abstand über 80 °C“ siehe W-2 |
| „post-cure … if required“, S. 3 | dto. S. 3 | stimmt. Dort steht auch: „**Small volumes (250ml) may be heat cured immediately**“ (für die Exothermie verwertbar, K-1) |
| Lagerung über 15 °C, Härter kristallisiert, 40 °C anwärmen | dto. S. 1, S. 3 | stimmt (TDS: 15–35 °C) |
| Teil A: Warning, H315/H317/H319/H411 | `Electrolube_ER2223-PartA_SDS_Rev0-2016-10-19_EN.pdf` S. 1; 2023: `…_Rev0.64-2023-10-27_SV.pdf` S. 2 | stimmt |
| Teil B: Gefahr, H302/H314/H317/H318/H373; 4,4'-Methylenbis(cyclohexylamin) CAS 1761-71-3, 60–100 % | `Electrolube_ER2223-PartB_SDS_2023-10-02_HU.pdf` S. 1–3 | stimmt (H318 in der Einstufung, nicht im Etikett, korrekt). Kein CMR-Stoff in A und B: bestätigt (Abschn. 11: Mutagenität, Karzinogenität, Reproduktionstoxizität „Kriterien nicht erfüllt“, S. 8–9) |
| 832HT A: H360 Repr. 1B | `MGChemicals_832HT-Kit_SDS_V6.13-2026-07-17_EN-CA.pdf` S. 2–3 | stimmt |
| 832HT Tg 89 °C, CTE 86, 22 000 cP; „Mixing > 500 g … flash cure“ | `MGChemicals_832HT_TDS_V6.2-2026-06-18.pdf` S. 2/3 | stimmt |
| ER2221 CTE 30, 6000 mPa·s, Tg nicht angegeben | `Electrolube_ER2221_TDS_Rev8-2019-03.pdf` | stimmt |
| Feldsimulation `coat_epoxy.txt` | `simulation/field/results/coat_epoxy.txt` | Tabellenwerte im Konzept Kap. 3 stimmen mit der Ergebnisdatei überein. **Nicht neu gerechnet** (das Skript überschreibt Dateien im Repo, Auftrag „keine anderen Dateien ändern“); nicht sicherheitsrelevant |

Fazit: In der Stichprobe stimmen alle Zahlen und Seitenangaben.

## 3 Werden bestehende Sicherheitsregeln in MONTAGE_SENSOR.md abgeschwächt?

Diff fe5adac geprüft:
- „Ohne Datenblatt kein Verguss am Serienteil“ ist ersetzt durch „kein Verguss an Mustern bis zur Freigabe; ohne Datenblatt
  und SDB keine andere Masse“. Das ist **strenger**, ok.
- Die Regeln K-4 „nur eine Masse, kein weicher Vorverguss“, K-5 (Reinigen, Anrauen), „Zelle nicht eingesetzt“ (Kap. 4),
  „kein Metallwerkzeug“ (Kap. 8) und die Pflichtprüfungen sind erhalten bzw. ergänzt (Isopropanol entzündlich, Schutzausrüstung).
- **Abgeschwächt:** In der O-1-Zeile fehlt jetzt „mineralisch gefüllt, niedriger CTE“, bevor der Entscheid gefallen ist (K-6).
- **Vakuum:** „bei ER2223 nicht nötig“ stützt sich auf eine Stokes-Abschätzung (Konzept Kap. 5). Kopfüber mit Entlüftung
  bleibt Pflicht, V-1 prüft im Schnitt. Das ist keine Abschwächung von K-4 („Vakuum **oder** kopfüber mit Entlüftung“).
- **Widerspruch zur Programmieranleitung** (W-1): Die Regel „Zelle nie eingesetzt“ wird über Kap. 6 / Weg B ausgehebelt.

## 4 Befunde

### W-1 · wichtig · Zelle beim Verguss und bei der 60-°C-Nachhärtung: Ablauf widersprüchlich

**Befund:** MONTAGE Kap. 3a sagt „Zelle nie eingesetzt (Kap. 4 Schritt 1)“. Aber:
1. MONTAGE Kap. 6 verlangt, solange Weg A nicht freigegeben ist, die Programmierung nach **Weg B vor Kap. 5**.
   `PROGRAMMIEREN_SENSOR.md` Kap. 5 Schritt 9 endet mit: „Erst dann Zelle einsetzen (Funktionsprüfung wie Weg A
   Schritt 7) **und vergiessen**.“ Wer beiden Anleitungen folgt, vergiesst den Kragen mit eingesetzter Zelle und härtet sie
   4 h bei 60 °C nach.
2. Kap. 5a / V-4: Gemessen wird mit eingesetzter Zelle und montierter Hülse. Danach werden die Kanten versiegelt (Hülse ab),
   und erst „vor der Nachhärtung“ wird die Zelle entnommen. Während des Auftragens liegt die Zelle also im offenen Fach
   neben der flüssigen Masse.
3. Kap. 8 Schritt 1 „Nachbessern nur nach Kap. 3a/5a mit frischer Masse“ steht **vor** Schritt 2 (Zelle entnehmen).

**Bewertung:** Für die Zelle sind 60 °C zulässig: Panasonic CR2032 „Operating temperature −30 °C to +85 °C“
(`docs/datasheets/Panasonic_CR2032_Datasheet_2026-02.pdf` S. 1). Renata empfiehlt über 60 °C eine Rücksprache
(`Renata_CR2032MFR_Datasheet_Rev07.pdf` S. 1). Deshalb kein kritischer Befund. Trotzdem widerspricht es
`BATTERIEWECHSEL.md` Z. 23 („nicht erwärmen“). Bei Überschwingen eines Filamenttrockners fehlt die Reserve. Masse, die mit
eingesetzter Zelle auf die Clip-Pads kriecht, sieht man nicht. Ausserdem läuft der Sensor während des Vergusses.

**Vorschlag:**
- In MONTAGE Kap. 3a „Aushärten“, Kap. 4 Schritt 1, Kap. 5 (neuer Schritt 0) und Kap. 5a Schritt 1 je die Vorbedingung
  „**Clip leer (keine Zelle, keine Dummy-Scheibe)**, kontrolliert“ setzen.
- MONTAGE Kap. 6: Nach Weg B die **Zelle nach der Funktionsprüfung wieder entnehmen**, erst dann Kap. 5.
  `PROGRAMMIEREN_SENSOR.md` Kap. 5 Schritt 9 entsprechend ändern: „… Funktionsprüfung, **Zelle wieder entnehmen**, dann
  vergiessen“. Gemäss PROGRAMMIEREN Kap. 6 sind Zellen < 2.6 V zu entsorgen, eine geprüfte Zelle darf wieder eingesetzt werden.
- Kap. 5a V-4: Die Zelle **vor dem Auftragen** entnehmen, nicht erst vor der Nachhärtung.
- Kap. 8: „Nachbessern“ in einen eigenen Schritt nach dem Entnehmen der Zelle verschieben und nur nach Rücksprache mit der
  Projektleitung zulassen (ein ganzer Beutel, Fuge „nass auf hart“).

### W-2 · wichtig · Tg 140 °C gilt nicht für die vorgesehene Härtung; Tg ≥ 80 °C (K-4) ist nicht belegt

**Befund:** Das TDS nennt Tg 140 °C ohne Härtebedingung (S. 2). Die einzige mögliche Härtung ist 24 h RT + 4 h 60 °C,
denn 100 °C sind wegen ASA ausgeschlossen. Bei aminisch gehärteten Epoxiden begrenzt die Härtetemperatur den erreichbaren
Tg. Ein Tg von 140 °C nach 60 °C Härtung ist unwahrscheinlich (**ANNAHME**, Fachwissen, kein lokales Datenblatt). Die
Aussage im Konzept Kap. 6 Nr. 1 „mit Abstand über 80 °C“ ist damit nicht belegt. Die offene Rückfrage an Electrolube
bezieht sich nur auf „Tg nach 24 h RT“. V-3 („Fingernagel, 1 h bei 80 °C“) ist kein Tg-Nachweis.

**Vorschlag:**
- Rückfrage an Electrolube erweitern: Tg (und CTE) **nach 24 h RT + 4 h 60 °C**.
- Ohne schriftliche Antwort: Tg per DSC/TMA an einer V-3-Probe bestimmen lassen (externes Labor, Kosten ANNAHME), oder
  als Werkstatt-Ersatz eine Kriechprobe: gegossener Stab ≈ 4 × 10 × 60 mm, Stützweite 50 mm, Mittellast für ≈ 0.45 MPa
  Randfaserspannung, 1 h bei 80 °C, bleibende Durchbiegung < 0.2 mm (**ANNAHME**, Kriterium an der Probe festlegen).
- Für die **Prototypen** genügt es, wenn die 168 h bei 65 °C aus K-7 ohne Erweichen bzw. Ablösen bestanden werden (A-1).
  Für die **Serienfreigabe** ist der Tg-Nachweis Pflicht.
- Konzept Kap. 6 Nr. 1 und D-030-Begründung umformulieren: „Tg 140 °C laut TDS (Härtebedingung unbekannt); Tg nach
  60-°C-Härtung offen“.

### W-3 · wichtig · SDB Teil B nur ungarisch; der Auszug in MONTAGE Kap. 3a lässt Pflichtangaben aus

**Befund:** Die H-Sätze sind sprachunabhängig und richtig übernommen. In den Abschnitten 4, 7 und 8 von SDB B stehen
aber Massnahmen, die in Kap. 3a fehlen oder schwächer formuliert sind (Prüfer-Übersetzung):

| SDB B (HU), Stelle | Inhalt | MONTAGE Kap. 3a heute |
|---|---|---|
| S. 3, Abschn. 4.1 Augen | „sofort mit viel Wasser, auch unter den Lidern, **mindestens 15 Minuten**; Lider offen halten; **sofort ärztliche Hilfe**“ (ebenso SDB A 2023, SV S. 3: „minst 15 minuter“) | „mehrere Minuten“, Arzt |
| S. 3, Abschn. 4.1 Haut | „sofort mit Seife und viel Wasser, verunreinigte Kleidung **und Schuhe** ausziehen, **sofort ärztliche Hilfe**“ | waschen, kein Arzt |
| S. 3, Abschn. 4.1 Einatmen | frische Luft, sofort Arzt, „**verzögertes Lungenödem möglich**“ | fehlt |
| S. 6, Abschn. 8.2 | dicht schliessende Schutzbrille **und Gesichtsschutz** („Arcvédő maszk“); dicht schliessende Handschuhe; langärmlige Kleidung, **chemikalienbeständige Schürze** | Brille, Handschuhe, lange Ärmel |
| S. 5, Abschn. 7.1 | „Nur im geschlossenen System oder mit **geeigneter Absaugung**; bei unzureichender Lüftung geeigneten Atemschutz“ | „gut lüften“ (siehe W-4) |
| S. 5, Abschn. 7.2 | dicht verschlossen, trocken, kühl, gut belüftet; **für Kinder unzugänglich; unter Verschluss** | fehlt (Beutel liegen wegen 8 Wochen Lieferzeit lange im Lager) |
| SDB A S. 6, Abschn. 8.2 | „Provide eyewash station“ | fehlt |

Für einen Musterbau genügt das ungarische SDB **nicht**. Der Ausführende kann es nicht lesen, und am Arbeitsplatz muss
das SDB in einer verständlichen Sprache ausliegen (MONTAGE Kap. 1 verlangt das selbst: „SDB A/B ausgedruckt am
Arbeitsplatz“). Ob eine rechtliche Pflicht zur Landessprache besteht (Lieferantenpflicht in der Schweiz), ist **ANNAHME**
und nicht geprüft.

**Vorschlag:**
- **Bedingung vor dem Öffnen des ersten Beutels (auch V-1…V-3):** SDB Teil B auf Deutsch (oder EN/FR/IT) beim Händler
  (Simpex/Distrelec) bzw. bei Electrolube anfordern und ablegen. Eine Websuche fand am 2026-11-09 keine EN-Fassung von
  Teil B. Der Distrelec-Pfad mit `ger_de`/`eng_en` statt `hun_hu` gibt 404.
- Kap. 3a ergänzen, sofort und unabhängig vom SDB:
  - Augen **≥ 15 min** spülen (Lider offen), **immer Arzt**.
  - Haut: sofort waschen, Kleidung und Schuhe ausziehen, bei Härter-Kontakt Arzt.
  - Einatmen: frische Luft, bei Beschwerden Arzt, Hinweis auf verzögertes Lungenödem.
  - **Augenspülflasche** (oder fliessendes Wasser in Griffnähe) am Platz.
  - **Gesichtsschutz** (Visier über der Brille) beim Aufschneiden, Ausdrücken und Kneten des Beutels.
  - Kunststoffschürze.
  - Lagerung verschlossen, für Kinder unzugänglich, trocken, 15–35 °C (TDS S. 1).

### W-4 · wichtig · Werkstatt ohne Abzug: „gut lüften“ ist zu unbestimmt

**Befund:** SDB B Abschn. 7.1 (S. 5) verlangt ein geschlossenes System oder eine Absaugung, sonst Atemschutz. Abschn. 8.2
(S. 6) hält Atemschutz bei normaler Verwendung für unnötig. Der Dampfdruck des Härters ist klein (0.0549 Pa @ 20 °C, S. 6),
bei Raumtemperatur ist das Risiko also gering. Beim Aushärten des ≈ 227-ml-Rests erwärmt sich die Masse aber, ebenso bei
der Nachhärtung im Trockner. Dabei steigt die Ausgasung. H373 (wiederholte Exposition) passt zu wiederholten Sitzungen.

**Vorschlag (Kap. 3a, Schutzmassnahme 1):**
- Am geöffneten Fenster arbeiten, wenn möglich mit einem Ventilator, der **nach aussen** bläst (Absaugung behelfsmässig).
- Die Schale mit dem Beutelrest und den Trockner zum Nachhärten in einen belüfteten Raum stellen, **nicht in Wohn- oder
  Schlafräume**, ausser Reichweite von Kindern und Haustieren.
- Bei Geruch oder Reizung abbrechen und lüften. Wer regelmässig vergiesst: Halbmaske mit Filter A (EN 14387) bereithalten
  (SDB A S. 6 nennt EN 14387).
- Den Filamenttrockner nach dem Nachhärten offen auslüften lassen und erst danach wieder für Filament verwenden (**ANNAHME**).

### W-5 · wichtig · Auflagen A-1…A-5 zur K-4-Abweichung in Testplan und FMEA übernehmen

**Befund:** Die Freigabe der Abweichung (Kap. 1) stützt sich ganz auf K-7. Heute gibt es dafür ein Opfermuster ohne
festgelegte Prüfstellen, und F-63 trägt noch „gefüllt“ als Massnahme.

**Vorschlag:** A-1…A-3 als Ergänzung zu ST-W4 bzw. M-W4 in `phase5_testplan_prototyp.md` aufnehmen, A-4 in der FMEA.
Erst danach D-030 freigeben.

### K-1 · klein · Exothermie: Masse der Alu-Schale passt nicht zur Schichtdicke; Unterlage

Schale „≥ 15 × 10 cm“ und „flach (≤ 10 mm)“ widersprechen sich: 250 g / 1.10 g/ml ≈ 227 ml ergeben auf 150 cm²
≈ 15 mm. **Vorschlag:**
- Schale ≥ 20 × 15 cm (≈ 7.5 mm) oder zwei Schalen.
- Schale auf eine **nicht brennbare** Unterlage stellen (Fliese, Blech, nicht Karton), den Rest **nicht** in den Trockner
  stellen (TDS S. 3: „Do not heat cure large volumes immediately“).
- Als Beleg TDS S. 3 zitieren („Small volumes (250ml) may be heat cured immediately“). Das zeigt, dass die Exothermie
  der Beutelmenge beherrschbar ist, und ersetzt die Fremdreferenz MG/ANNAHME.

### K-2 · klein · Gilt der Schutz schon für die Vorversuche?

„Gilt erst nach Freigabe von O-1/O-2; vorher nur die Vorversuche“ lässt sich so lesen, als gälten die Schutzmassnahmen
erst nach der Freigabe. **Vorschlag:** „Gefahren, Schutzmassnahmen, Erste Hilfe, Lagerung und Entsorgung gelten ab dem
ersten Beutel, auch für V-1…V-3.“

### K-3 · klein · Handschuhe

Nitril ist als **ANNAHME** richtig gekennzeichnet. SDB B Abschn. 8.2: dicht schliessende Handschuhe. **Vorschlag:**
- Nitril ≥ 0.1 mm, zwei Paar übereinander, das äussere bei Kontakt sofort wechseln.
- Die Beständigkeitsliste des Handschuhherstellers für CAS 1761-71-3 (Härter) und 25068-38-6 (Harz) ablegen.

### K-4 · klein · „ungefüllt“ ist eine Folgerung; neuere TDS-Revision

Das TDS sagt nicht „unfilled“. Die Folgerung aus der Dichte 1.10 g/ml ist plausibel, und SDB A listet nur organische
Inhaltsstoffe (S. 2–3). TDS S. 3 erwähnt allerdings „Sedimentation of the resin“. Das Konzept sollte „ungefüllt
(**ANNAHME**, Dichte 1.10, SDB A Abschn. 3)“ schreiben. Eine Websuche (2026-11-09) zeigt eine neuere TDS-Fassung
„ER2223-Encapsulation-Resins-EN-09Aug23-TB.pdf“ (MacDermid Alpha), deren URL 404 liefert. Nach CLAUDE.md gilt die
aktuellste Version: beim Händler bzw. Hersteller beschaffen und Tg, CTE und Härtung vergleichen.

### K-5 · klein · Unvollständig gehärtete Kantenversiegelung im Pflanztopf

Die Kante liegt dauerhaft in nasser Erde. Ungehärtete Reste (Teil A H411, Teil B ätzend) würden auslaugen. Die
Massnahmen (Resin Pack, V-3 je Sitzung, Nachhärtung) genügen. **Vorschlag:** In Prüfung 5a ergänzen: „Kantenschicht
nach der Nachhärtung nicht klebrig (Wattestäbchen bleibt ohne Faser haften)“. Sensoren mit klebriger Kante nicht
einsetzen.

### K-6 · klein · Wortlaut K-4 in MONTAGE O-1 vorzeitig geändert; Dateiinhalt SDB HU

- Die O-1-Zeile nennt K-4 nur noch als „Epoxid 2K, Tg ≥ 80 °C, ein Material“. Bis D-030 den Originalwortlaut stehen lassen
  und die Abweichung daneben nennen (A-5).
- `Electrolube_ER2223-PartB_SDS_2023-10-02_HU.pdf` enthält ab S. 14 zusätzlich Teil A (HU, 2023-10-27). Das in der
  INDEX-Bemerkung vermerken.

## 5 Was gut ist

- Wahl gegen 832HT wegen H360 ist richtig (Sicherheit > Kosten).
- Das Resin Pack verhindert Mischfehler beim Wägen 3.45 : 1, ein Vorteil für Härtung und Auslaugung.
- Die Sondenflächen bleiben ohne Schicht, keine Schrumpfschlauch-Lufttaschen. Das Kupfer liegt ≥ 1.25 mm innen, also
  kein freiliegendes Metall.
- „Kein Isopropanol auf der Haut“, Isopropanol weg vom Trockner, „nie über 65 °C“ mit eigenem Thermometer, Beutelrest
  sofort flach ausgiessen, flüssige Reste nicht in den Ausguss (H411), ungemischte Beutel zum Sonderabfall: alles richtig.

## 6 Freigabe

**Kein Veto.** D-030 kann freigegeben werden, wenn:
1. W-1, W-3 und W-4 sowie K-1 und K-2 in MONTAGE (und W-1 in PROGRAMMIEREN Kap. 5) umgesetzt sind, **bevor ein Beutel
   geöffnet wird** (auch für V-1…V-3), und das SDB Teil B in DE/EN/FR/IT vorliegt;
2. W-5 / A-1…A-5 im Testplan bzw. in der FMEA stehen;
3. W-2 (Tg-Nachweis) vor der **Serien**freigabe erbracht ist. Für die Prototypen genügt K-7 nach A-1.

Bitte je Befund *umgesetzt* / *abgelehnt (Grund)*: W-1 → Mechanik + Elektronik (PROGRAMMIEREN); W-2, W-5, K-1…K-6 → Mechanik;
W-3, W-4 → Mechanik (Anleitung); A-4 → Sicherheit (FMEA) nach Rückmeldung.

Quellen Websuche (2026-11-09): https://macdermidalpha.com/sites/default/files/2023-08/ER2223-Encapsulation-Resins-EN-09Aug23-TB.pdf (404 beim Abruf);
https://res.cloudinary.com/electrolube/image/upload/v1573042102/044-ER2223A-SDS532_n9s3vc.pdf (Teil A EN, bereits lokal).

## Antwort Ersteller (Mechanik-Agent, 2026-11-09)

| Befund | Antwort | Umsetzung |
|---|---|---|
| A-1 | *umgesetzt* | Testplan PT11.19: ≥ 2 vollständige Muster nach freigegebenem Verfahren, V-4-Muster zählt nicht (V-4 nicht an S4/S5); Konzept Kap. 12 K-7 |
| A-2 | *umgesetzt* | Testplan PT11.23: Schliff/Farbeindringprüfung nach 50 Zyklen + 168 h an Kragenunterkante z 1.3 … 3.5 (F, B), Taschenwand U3/C24, Kragenoberseite/Clip; Eindringen ≤ 0.5 mm |
| A-3 | *umgesetzt* | Konzept Kap. 9a: ohne Bestehen keine Serie; Rückfall 1 ER2221 unter Bedingungen (Tg ≥ 80 °C schriftlich oder V-6, SDB A/B in Landessprache, V-1 … V-3, ganzer Beutel wegen 13.91 : 1, Vakuum/längere Entlüftung, CH-Bezug klären); Rückfall 2 gleichwertige gefüllte Masse mit neuer Prüfung |
| A-4 | *umgesetzt* (Text), O/D-Neubewertung bleibt bei der Sicherheit | `phase5_fmea_light.md` F-60: „Vergussmasse mit Datenblatt wählen“ erledigt (ER2223, D-030-Vorschlag); F-63: Massnahme „ER2223 ungefüllt, Abweichung K-4 nach D-030, Gate A-1/A-2, Rückfall A-3, Tg-Nachweis vor Serie“. RPZ-Zahlen nicht verändert |
| A-5 | *umgesetzt* | `PCB_OUTLINE.md` nicht geändert; MONTAGE O-1 trägt wieder den vollen K-4-Wortlaut („mineralisch gefüllt, … niedriger CTE“, gilt bis D-030), Abweichung daneben |
| W-1 | *umgesetzt* | MONTAGE Kap. 3a (Vorbedingung jeder Sitzung und der Nachhärtung „Clip leer, kontrolliert, abgehakt“), Kap. 4 Schritt 0, Kap. 5 Schritt 0, Kap. 5a Schritt 1, V-4 (Zelle **vor dem Auftragen** entnehmen), Kap. 6 (nach Weg B Zelle nach der Funktionsprüfung wieder entnehmen), Kap. 8 (Nacharbeit eigener Absatz nach Zellentnahme, nur nach Rücksprache Projektleitung). `PROGRAMMIEREN_SENSOR.md` Kap. 5 Schritt 9: „Funktionsprüfung, danach Zelle wieder entnehmen, mit leerem Clip vergiessen“; übrige Regeln dort unverändert (Reihenfolge Schritt 8, Zellen < 2.6 V entsorgen) |
| W-2 | *umgesetzt* | Konzept Kap. 6 Nr. 1 und D-030: „Tg 140 °C laut TDS, Härtebedingung unbekannt; Tg nach 60-°C-Härtung offen“; Anfrage an Electrolube als Textvorlage (Konzept Anhang A: Tg/CTE nach 24 h RT und nach 24 h RT + 4 h 60 °C); Kriechprobe **V-6** (Stab 4 × 10 × 60, Stützweite 50, ≈ 1.0 N → 0.45 MPa, 1 h 80 °C, bleibend < 0.2 mm) als Pflicht vor der Serie ohne schriftlichen Tg; Prototypen über K-7/A-1 |
| W-3 | *umgesetzt* | MONTAGE Kap. 3a: Augen ≥ 15 min, Lider offen, immer Arzt; Haut: Kleidung **und Schuhe** aus, Arzt nach Härter-/Mischungskontakt; Einatmen: verzögertes Lungenödem; Visier, Schürze, Augenspülflasche; Lagerung unter Verschluss, für Kinder unzugänglich, 15–35 °C. **Voraussetzung vor dem ersten Beutel (auch V-1 … V-3): SDB Teil B in DE/EN/FR/IT**; Textvorlage für die Händleranfrage im Konzept Anhang B (versendet der Auftraggeber) |
| W-4 | *umgesetzt* | MONTAGE Kap. 3a „Arbeitsplatz und Lüftung“: offenes Fenster mit Ventilator nach aussen, nicht in Wohn-/Schlafräumen (auch Restschale und Trockner), abbrechen bei Geruch/Reizung, Halbmaske Filter A (EN 14387) bereit, Trockner auslüften (**ANNAHME**) |
| W-5 | *umgesetzt* | siehe A-1 … A-4 |
| K-1 | *umgesetzt* | Alu-Schale ≥ 20 × 15 cm oder zwei (≈ 7.5 mm), nicht brennbare Unterlage, Rest nicht in den Trockner; Beleg TDS S. 3 statt MG-Fremdreferenz (Variante M-B) |
| K-2 | *umgesetzt* | Kap. 3a „Geltung“: Schutz, Erste Hilfe, Lagerung, Entsorgung ab dem ersten Beutel, auch für V-1 … V-3 |
| K-3 | *umgesetzt* | Nitril ≥ 0.1 mm, zwei Paar, äusseres sofort wechseln; Beständigkeitsliste für CAS 1761-71-3 und 25068-38-6 ablegen (offen, vor dem ersten Beutel) |
| K-4 | *umgesetzt* | „ungefüllt (**ANNAHME**, Dichte 1.10, SDB A Abschn. 3)“ im Konzept und INDEX.csv; neuere TDS-Fassung 09Aug23 nicht abrufbar → in der Anfrage an Electrolube (Anhang A) angefordert |
| K-5 | *umgesetzt* | Prüfung 5a: Kante nach Nachhärtung nicht klebrig (Wattestäbchen ohne Faser), sonst nicht in Erde einsetzen |
| K-6 | *umgesetzt* | O-1-Wortlaut wiederhergestellt (A-5); INDEX.csv REF-VG4: Datei enthält ab S. 14 Teil A (HU) |

**Neu seit Runde 1 (bitte mitprüfen):** Zur Kostensenkung schlage ich die Variante **M-A** vor (MONTAGE Kap. 3a, Konzept
Kap. 7): Den Beutel einmal ohne Mischen in zwei dicht schliessende, etikettierte Flaschen abfüllen, dann je Sitzung kleine
Ansätze wägen (3.45 g A + 1.00 g B, Waage 0.01 g, TDS S. 3 „Bulk Mixing“). Sie gilt erst, wenn Electrolube keine Einwände hat
(Anhang A) und die Sicherheit den Abfüllschritt geprüft hat (zusätzlicher Umgang mit dem ätzenden Härter, Visier, Lagerung
unter Verschluss). Bis dahin gilt M-B (ganzer Beutel).

---

## Runde 2 (Sicherheits-Agent, 2026-11-09)

Geprüft: Commit 11aa3e3, selbst gelesen:
- `MONTAGE_SENSOR.md` Kap. 0, 1, 3a, 4, 5, 5a, 6, 8
- `PROGRAMMIEREN_SENSOR.md` Kap. 5 Schritt 9
- Konzept Kap. 7, 9a, 12 (V-6), Anhang A/B
- `phase5_testplan_prototyp.md` PT11.19/PT11.23
- `phase5_fmea_light.md` F-60/F-63

**Ergebnis: kein Veto.** Alle Befunde aus Runde 1 sind richtig umgesetzt. Variante M-A ist **zulässig unter den
Bedingungen MA-1…MA-3 (wichtig)**. Neu: 0 kritisch, 2 wichtig, 4 klein.

### R2.1 Kontrolle der Umsetzung Runde 1

| Befund | Stelle | Urteil |
|---|---|---|
| W-1 | MONTAGE 3a „Vorbedingung jeder Vergusssitzung: Clip leer … abgehakt“; Kap. 4 Schritt 0; Kap. 5 Schritt 0 (mit Verweis auf Weg B); Kap. 5a Schritt 1; V-4 „Zelle entnehmen, Clip leer, erst danach Masse auftragen“; Kap. 6 „Zelle wieder entnehmen“; Kap. 8 Nacharbeit als eigener Absatz nach Zellentnahme, nur nach Rücksprache; PROGRAMMIEREN Kap. 5 Schritt 9 „danach die Zelle wieder entnehmen … mit leerem Clip vergiessen“ | **erledigt**. Der Widerspruch Weg B ↔ 3a ist aufgelöst |
| W-2 | Konzept Kap. 6/10 „Tg nach 60-°C-Härtung offen“; Anhang A Frage 1 (a)/(b); V-6 | **erledigt**. V-6 nachgerechnet: σ = 3·1.0·50/(2·10·4²) = 0.47 MPa, elastische Durchbiegung F·L³/(48·E·I) mit I = 53.3 mm⁴: 0.016 mm bei E = 3 GPa bzw. 1.6 mm bei E = 30 MPa. Die Probe trennt glasig von gummielastisch sicher. Offener Punkt 7 (Ofen ≥ 80 °C) ist richtig ausgewiesen |
| W-3 | 3a: Voraussetzung SDB B in DE/EN/FR/IT vor dem ersten Beutel; Erste Hilfe (≥ 15 min, Lider, immer Arzt; Kleidung und Schuhe; Lungenödem; Verschlucken); Visier, Schürze, Augenspülflasche; Lagerung unter Verschluss; Notruf 145/144; Anhang B | **erledigt**, deckt sich mit SDB B Abschn. 4.1/7/8 |
| W-4 | 3a „Arbeitsplatz und Lüftung“ 1–5 | **erledigt** |
| W-5 / A-1…A-3 | PT11.19 (≥ 2 vollständige Muster, V-4 nicht an S4/S5), PT11.23 (Prüfstellen, Kriterium ≤ 0.5 mm, A-3 keine Serie), Konzept Kap. 9a | **erledigt**. Kap. 9a ER2221: Die Begründung „13.91 : 1 nur als ganzer Beutel, ± 3.7 % Wägefehler“ ist richtig (0.01/0.27) |
| A-4 | FMEA F-60 erledigt-Vermerk, F-63 Massnahmentext | **erledigt** (Text). O/D-Neubewertung siehe R2.3 |
| A-5 / K-6 | O-1 trägt wieder den vollen K-4-Wortlaut, Abweichung daneben; PCB_OUTLINE unverändert; INDEX REF-VG4 | **erledigt** |
| K-1 | M-B Schritt 2: Schale ≥ 20 × 15 cm, nicht brennbare Unterlage, nicht in den Trockner, TDS S. 3 zitiert | **erledigt** |
| K-2, K-3, K-4, K-5 | 3a „Geltung“; Handschuhe; „ungefüllt (ANNAHME)“; Prüfung 5a „nicht klebrig“ | **erledigt** |

Keine Abschwächung bestehender Regeln gefunden. Kap. 6 und PROGRAMMIEREN Kap. 5 erlauben eine geprüfte Zelle ≥ 3.0 V
wieder einzusetzen. Das passt zu PROGRAMMIEREN Kap. 6 (< 2.6 V entsorgen) und betrifft die Sicherheit nicht.

### R2.2 Variante M-A (Abfüllen, Wägen kleiner Ansätze)

**Grundsätzliche Bewertung:**
- **Grundlage:** Das TDS beschreibt „Bulk Mixing“ im richtigen Verhältnis und verlangt dicht verschlossene Gebinde
  „to prevent the ingress of moisture“ (`Electrolube_ER2223_TDS_Rev4-2019-03.pdf` S. 3).
- **Was M-A mehr kostet:** einmal je Beutel das Umfüllen des ätzenden Härters B (H314) und je Sitzung das Entnehmen von
  ≈ 1 g B aus einer Flasche. Gefährdet sind dabei Augen und Haut.
- **Lagerung:** Statt eines verschweissten Beutels steht eine angebrochene Flasche mit ätzendem, farblosem Härter
  (SDB B Abschn. 9: farblos, S. 6) über Monate im Haushalt. Das bringt Verwechslungsgefahr und Kinderzugang.
- **Was M-A spart:**
  - Kein 227-ml-Rest mehr je Sitzung: weniger Exothermie und Ausgasung (W-4), weniger Abfall.
  - Weniger Beutel, die über 8 Wochen Lieferzeit gelagert werden.
  - Die Ansätze sind ≥ 4 g klein, ihre Exothermie ist vernachlässigbar.
- **Mischfehler:** Ein falsches Verhältnis gibt eine unvollständige Härtung (TDS S. 3 „erratic or partial curing“), mit
  den Folgen K-5 (Auslaugung im Topf) und W-2 (Tg). Das fangen V-3 je Ansatz und Prüfung 5a ab.

**Urteil:** Sicherheitlich etwa gleichwertig mit M-B, wenn die folgenden Bedingungen erfüllt sind. Kein Veto.

#### MA-1 · wichtig · Gebinde: kindergesichert, nicht verwechselbar, Sekundärbehälter

**Befund:** MONTAGE 3a M-A Schritt 1 nennt „Weithalsflasche HDPE oder Glas mit dicht schliessendem Deckel“. Teil B ist
farblos und ätzend (H314, H302). In einer unauffälligen Flasche im Haushalt kann er mit Wasser oder Getränken verwechselt
oder von Kindern geöffnet werden. Der Beutel hatte diesen Schutz durch die Kappen, den Clip und die Herstelleretikette.

**Vorschlag (in Kap. 3a M-A Schritt 1 und Kap. 1 aufnehmen):**
- **Nie Lebensmittel- oder Getränkeflaschen** verwenden, auch nicht gereinigt. Nur Laborflaschen.
- **Flasche B: HDPE** mit **kindergesichertem Verschluss** (Drück-Dreh-Verschluss), kein Glas (Bruch bei ätzendem Inhalt).
  Flasche A: HDPE oder Glas, ebenfalls mit kindergesichertem Verschluss (**ANNAHME** Verfügbarkeit im Laborhandel;
  HDPE-Beständigkeit gegen das Amin anhand der Beständigkeitsliste des Flaschenherstellers prüfen).
- Beide Flaschen stehen in einem **dicht schliessenden Kunststoff-Sekundärbehälter** mit etwas Saugmaterial (z. B.
  Vermiculit oder Katzenstreu, SDB B Abschn. 6.3 „mechanisch aufnehmen“). Der Behälter ist **abgeschlossen** (Vorhängeschloss
  oder abschliessbarer Schrank) und steht nicht bei Lebensmitteln und nicht im Kühlschrank.
- Gleichzeitig nur **ein** angebrochener Satz A/B.

#### MA-2 · wichtig · Etikettierung und Verwechslung A/B

**Befund:** Schritt 1 verlangt nur „Produkt, Piktogramme und H-Sätze wie oben, Abfülldatum, Ablaufdatum“. Es fehlen das
Signalwort, die P-Sätze, die Unterscheidung der Deckel und ein Hinweis für Dritte. Vertauschte Deckel verkleben das Gewinde
(Härtung im Gewinde), und die Flasche lässt sich dann nur noch mit Kraft öffnen.

**Vorschlag:** Etikett je Flasche:
- Inhalt: „ER2223 Teil A – Harz“ bzw. „ER2223 Teil B – Härter“.
- Signalwort (A „Achtung“, B „**Gefahr**“), GHS-Piktogramme und H-Sätze nach SDB Abschn. 2.2.
- P-Sätze P280, P305+P351+P338, P301+P330+P331 (B) und P303+P361+P353 (B).
- „**Kein Lebensmittel – nicht trinken**“, „Unter Verschluss, für Kinder unzugänglich“.
- Abfülldatum und Ablaufdatum des Beutels, Name und Telefon des Verantwortlichen, Notruf 145.

Dazu:
- Deckel und Flaschen **farblich unterschiedlich markieren** (z. B. A rot, B blau) und Deckel nie tauschen.
- **Je Komponente eine eigene, beschriftete Einweg-Pipette oder Spritze** zum Entnehmen, nicht aus der Flasche giessen.
- Reihenfolge: A wägen, Flasche A schliessen; dann B wägen, Flasche B schliessen. Nie beide Flaschen gleichzeitig offen.

#### MA-3 · klein · Haltbarkeit der angebrochenen Komponenten, kristallisierter Härter

SDB B Abschn. 10.4 nennt als zu vermeidende Bedingung, „längere Zeit Luft und Feuchte ausgesetzt“ (S. 7). Laut Abschn. 9
liegt der Schmelzbereich bei 17.7–65.4 °C (S. 6). Die Haltbarkeit nach dem Öffnen ist unbekannt; sie ist in Anhang A
erfragt (richtig).

**Vorschlag:** Bis zur Antwort höchstens **3 Monate** nach dem Abfüllen verwenden (**ANNAHME**), das Kriterium „trüb oder
Kruste“ bleibt. Kristallisierten Härter in der **geschlossenen** Flasche im Wasserbad bei 40 °C anwärmen (TDS S. 3), mit
Visier öffnen, nie in der Mikrowelle und nie im Trockner zusammen mit Sensoren.

#### MA-4 · klein · Waage: Auflösung ist nicht Genauigkeit

0.01 g ist die Anzeigeauflösung. Die Genauigkeit einfacher Feinwaagen liegt oft bei ± 0.02–0.05 g (**ANNAHME**). Damit ist
die ± 1 %-Aussage bei 1.00 g Härter nicht gesichert.

**Vorschlag:**
- Vor jeder Sitzung mit einem **Prüfgewicht** (z. B. 1 g und 5 g, Klasse F oder M1, **ANNAHME** Kosten) kontrollieren
  und den Messwert in die Musterliste schreiben.
- Mindestansatz auf **8 g (6.90 g A + 2.00 g B)** anheben, solange die Toleranz von Electrolube fehlt. Die Kosten sind
  vernachlässigbar (≈ 0.66 CHF Masse je Ansatz).
- V-3 an jedem Ansatz bleibt Pflicht (bereits so).

#### MA-5 · klein · Abfüllschritt: Auffangen und Restbeutel

**Vorschlag:**
- Abfüllen in einer **Auffangwanne** (Schale ≥ 20 × 15 cm), mit PE-Trichter, **zuerst A, dann B**, B langsam
  ausdrücken (der Beutel kann an der Clip-Kante platzen).
- Danach am leeren Beutel den Clip entfernen und die Reste von A und B im Beutel verkneten, damit sie aushärten. Erst dann
  in den Kehricht (**ANNAHME** wie Kap. 3a „Entsorgung“). So bleibt kein flüssiger Härter im Abfall.
- Saugmaterial für Verschüttetes bereithalten (SDB B Abschn. 6.3).

#### MA-6 · klein · Verfahren M-A erst nach Electrolube-Antwort

Die Bedingung (1) im Konzept Kap. 7 („Electrolube hat keine Einwände“) ist richtig. Ergänzung: Kommt keine Antwort, ist
M-A **trotzdem zulässig**, wenn MA-1, MA-2 und MA-4 umgesetzt sind und V-3 an jedem Ansatz sowie V-6 einmal mit einem
gewogenen Ansatz bestanden sind. Das TDS deckt „Bulk Mixing“ ab (S. 3). Diese Regel entscheidet der Orchestrator.

### R2.3 FMEA F-63 – Neubewertung O/D (A-4)

Skala der FMEA 1–10 (wie in `phase5_fmea_light.md`).

| | alt | neu | Begründung |
|---|---|---|---|
| S | 6 | **6** | unverändert: Wasserpfad zum Zellfach, kein Energiepfad im Kragen (Runde 1 Kap. 1) |
| O | 3 | **4** | ungefüllt, CTE 70 statt ≈ 30. Dehnungsdifferenz zu FR4 ≈ 3.9 ‰ bei −10 °C, Spannung an der Kragenunterkante im Bereich der Haftfestigkeit (**ANNAHME**). Tg nach 60-°C-Härtung nicht belegt. Mit belegtem Tg ≥ 80 °C (Electrolube oder V-6) → O 3 |
| D | 6 | **4** | gezielter Nachweis vor der Serie: K-7 an ≥ 2 vollständigen Mustern (PT11.19), Schliff bzw. Farbeindringprüfung genau an der kritischen Grenzfläche (PT11.23), V-6. Nur 2 Muster, also statistisch schwach → nicht besser als 4 |
| **RPZ** | 108 | **96** (nach Tg-Nachweis 72) | |

Vorschlag Eintrag F-63: „S 6 / O 4 / D 4 / RPZ 96 (Sicherheit Runde 2, 2026-11-09); O → 3 nach Tg-Nachweis (W-2)“.
Eintragen soll der Ersteller bzw. Orchestrator; ich ändere die FMEA hier nicht (Auftrag: nur dieser Bericht).

F-60 (Lunker, RPZ 180): Masse mit Datenblatt, 800 mPa·s und V-1 im Schnitt senken O plausibel von 5 auf 3. Vorschlag
S 6 / O 3 / D 6 = **108**, neu bewerten nach V-1.

### R2.4 Freigabebedingungen D-030 (aktualisiert)

**Kein Veto.** D-030 (ER2223 für Schott, Kragen und Kantenversiegelung, Flächen frei, 24 h RT + 4 h 60 °C) ist aus Sicht
der Sicherheit **freigabefähig**. Bedingungen:

1. **Vor dem Öffnen des ersten Beutels** (auch V-1…V-3):
   - SDB Teil B in DE/EN/FR/IT liegt vor und ist abgelegt.
   - Die Beständigkeitsliste der Handschuhe ist abgelegt (K-3).
   - Die Schutzausrüstung nach MONTAGE Kap. 1/3a ist vorhanden.
2. **Variante M-A** nur mit MA-1 und MA-2 (wichtig) sowie MA-3…MA-5. Bis dahin M-B.
3. **Vor dem Musterverguss:** V-1…V-3 bestanden.
4. **Vor der Serie:**
   - PT11.19 an ≥ 2 Mustern und PT11.23 bestanden (A-1/A-2), sonst Rückfall Kap. 9a (A-3).
   - Tg-Nachweis (Electrolube schriftlich oder V-6) erbracht (W-2).
5. FMEA F-63 (und F-60) mit den Werten aus R2.3 nachführen.

Bitte je Befund MA-1…MA-6 *umgesetzt* / *abgelehnt (Grund)*. Ist MA-1/MA-2 umgesetzt, genügt eine Sichtprüfung durch den
Orchestrator; eine Runde 3 der Sicherheit ist dafür nicht nötig.
