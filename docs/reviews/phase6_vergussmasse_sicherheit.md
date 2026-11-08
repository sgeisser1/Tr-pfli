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
