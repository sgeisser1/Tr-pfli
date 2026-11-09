# fluidi Sensor – Montage, Verguss und Batteriewechsel (mechanischer Teil)

| | |
|---|---|
| Stand | 2026-11-08, Phase 5, Gehäuse Rev C mit V-K/M-4 (D-019, D-023) und P5-M1/M2/M3; **Phase 6: Vergussmasse und Kantenversiegelung (Kap. 3a, 4, 5, 5a) nach `docs/concepts/vergussmasse_versiegelung.md` – D-030 gültig mit Auflagen: Verguss nur nach den Vorbedingungen Kap. 3a (D-030 Bed. 1–5) und nach Programmieren + Funktionsprüfung + OTA-Update am Muster (Kap. 3b)**; Mechanik-Nachträge Phase 6 (R W-1/W-8/K-l2/K-l5, S K-5) 2026-11-09 |
| Zeichnungen | `mechanical/drawings/FL-S-00_zusammenbau_sensor.pdf` (Positionen 1–17), Einzelteile FL-S-01 … FL-S-10 |
| Bilder | `renders/final/fluidi_03_explosion.png` (alle Teile), `renders/final/fluidi_04_batteriewechsel.png` (Hülse abgezogen) |
| Grundlage | `docs/interfaces/PCB_OUTLINE.md` Kap. 7, `mechanical/PRINT_SETTINGS.md` Kap. 4–5, `docs/reviews/phase4_sicherheit_kragen_firmware.md` K-4/K-5/K-7, `docs/reviews/phase3_sleeve_sicherheit.md`, `docs/reviews/phase5_fmea_light.md` |
| Programmieren | `docs/manuals/PROGRAMMIEREN_SENSOR.md` (eigene Anleitung; Behelf Weg B steht unter Veto PS-K1) |
| Batteriewechsel für Nutzer | `docs/manuals/BATTERIEWECHSEL.md` |

Positionsnummern (Pos.) wie Stückliste FL-S-00. Koordinaten: x Breite (+ rechts von vorne), y Tiefe (0 = Front),
z Höhe (0 = Kopfunterkante). **Offen** markiert, was die Dokumentation noch nicht festlegt; dort nichts improvisieren,
sondern die Projektleitung fragen.

## 0 Offene Punkte, die die Montage betreffen

| Nr | Punkt | Stand |
|---|---|---|
| O-1 | **Vergussmasse** (Kragen, Schott): Epoxid 2K, Tg ≥ 80 °C, *ein* Material für den ganzen Kragen | **Electrolube ER2223 (D-030, gültig mit Auflagen; Abweichung von K-4 „mineralisch gefüllt, niedriger CTE“)** – Tg 140 °C laut TDS (Härtebedingung unbekannt), ungefüllt (**ANNAHME**); `docs/concepts/vergussmasse_versiegelung.md` Kap. 10, INDEX.csv EP-K. Abweichung zulässig unter A-1 … A-5 (`docs/reviews/phase6_vergussmasse_sicherheit.md`). **Vorbedingungen, keine offene Freigabe:** D-030 Bed. 1–5, abzuhaken in Kap. 3a („Vor dem ersten Beutel“, „Vor dem Musterverguss“, „Vor der Serie“). Mischen: **M-B (ganzer Beutel), bis M-A nach Bed. 2 bestätigt ist** (Kap. 3a). Zusätzlich Reihenfolge Kap. 3b (erst programmieren, prüfen, OTA, dann vergiessen). Ohne Datenblatt und SDB keine andere Masse verwenden. |
| O-2 | **Kantenversiegelung der Sonde** (REQ-MECH-07) | ER2223 nur auf Schnittkante und Spitze, Flächen frei (D-030; Kap. 5a; Feldsimulation `simulation/field/results/coat_epoxy.txt`). Vorbedingungen wie O-1 |
| O-3 | Klebstoff Lichtfenster | **Vorschlag Mechanik (2026-11-09): UHU plus endfest 300** (2K-Epoxid, Tuben 33 g, INDEX MAT-ADH1). Transparenz nicht nötig: Klebstoff nur im Spalt 0.1 mm an Tropfenrand und Schaftmantel, nicht im Lichtweg (PRINT_SETTINGS Kap. 5). Haftung auf ASA im TDS nicht belegt → **PROTOTYP-PRÜFUNG** Klebeprobe und Dichtheit nach 7 d 65 °C. **Härter ätzend (H314/H318)**, Schutzmassnahmen Kap. 3 Schritt 1. Freigabe Orchestrator offen |
| O-4 | Klemmring (Pos. 6): **Presssitz** 0.05 je Seite in der Senkung Ø 6.4, Schürze verpresst die Membran um 0.1 mm (20 %) – Phase 5 R3-W2 (`check_sensor.txt` 2e) | Auszugskraft und Dichtheit am Muster: PROTOTYP-PRÜFUNG ST-W6 (a), M-W3; Klebung nur, wenn ein Kleber mit Datenblatt gewählt ist |
| O-5 | Tastermechanik (P5-M2, Runde 2): 60°-Keil am Finger auf einer Nase der Zunge in Höhe SW1, Führungsrippe und D-Bohrung gegen Verdrehen. SW1 schaltet im CAD nominal bei 0.3 mm Tastenhub, worst bei 0.65 mm (Reserve +0.17); Tastenkraft nominal ≈ 8 N, worst ≈ 12 N (+ Membran, μ 0.3 ANNAHME) (`check_sensor.txt` 2a–2e) | **Überlast:** nach dem Schalten trägt SW1 die Tastenkraft; bei 20 N und μ ≥ 0.3 Zunge SF ≥ 1.15, bei kleinerer Reibung < 1 → PROTOTYP-PRÜFUNG M-T2; Taste nicht mit Kraft drücken |
| O-6 | Anzugsmoment Schraube M2 × 3 in ASA/Mutter | nicht festgelegt; „handfest mit TX6“ (**ANNAHME**), am Muster prüfen (ST-K1) |

## 1 Teile, Werkzeuge, Hilfsstoffe

Teile: Pos. 1–17 laut Stückliste FL-S-00 (gedruckt nach `PRINT_SETTINGS.md`, Passproben vorher bestanden).

| Werkzeug / Hilfsstoff | Zweck |
|---|---|
| Torx-Schraubenzieher **TX6** | Schraube M2 × 3 Torx TX6, A2 (Pos. 12, bastelgarage 422191, D-032) |
| Messschieber 0.01 mm | Distanzlehre, Passungen, Dicke Dummy-Zelle |
| Lupe ≥ 10× | Sichtprüfungen (VIP-Pads, Verguss, Lötstellen; ST-E1) |
| 2 × Distanzlehre 24.2 (FL-S-10) | Abstand Kragen ↔ Schott beim Kragenverguss |
| Isopropanol (**leicht entzündlich**: keine offene Flamme, Lötkolben aus, lüften), fusselfreie Tücher | Flussmittelreste im Kragenbereich entfernen (K-5) |
| 600er Schleifpapier | FDM-Naht auf den O-Ring-Gleitflächen der Hülse glätten (PRINT_SETTINGS Kap. 5) |
| Silikonfett (S6) – nur **dünner Film**; O-Ringe aus **EPDM** (S2, Kap. 7 Schritt 2) | O-Ringe (Pos. 11) |
| Etikettendrucker mit **laminiertem Schriftband 9 mm** (z. B. Brother TZe, schwarz auf weiss, **ANNAHME** Werkstattbestand, Einkaufsliste S12), Isopropanol | Kennungsetikett (Kap. 7a) |
| Fensterkleber **UHU plus endfest 300** (Tuben Binder + Härter 33 g, O-3), SDB Binder und Härter ausgedruckt am Arbeitsplatz; Zahnstocher, PE-Folie (Gefrierbeutel), 120er Schleifpapier, Mischunterlage (PE-Deckel) | Lichtfenster (Pos. 4) in die Kappe kleben (Kap. 3 Schritt 1) |
| Kapton-Punkt (Ø ≈ 3 mm) | Gewinde der Mutter vor Epoxid schützen (PCB_OUTLINE Kap. 7) |
| Dosierspritzen + Kanülen, Mischbecher, Spatel, **Waage 0.01 g** | Verguss (Mengen siehe Kap. 4/5), Variante M-A (Kap. 3a) |
| Vergussmasse **Electrolube ER2223, Resin Pack 250 g** (Vorschlag O-1), TDS und SDB A/B (**B in DE/EN/FR/IT**, Kap. 3a) ausgedruckt am Arbeitsplatz | Schott, Kragen, Sondenkanten (Kap. 3a) |
| Variante M-A: Laborflaschen mit **kindergesichertem Verschluss** – B: HDPE ≈ 60 ml (kein Glas), A: HDPE/Glas ≈ 250 ml; Farbmarkierung rot/blau; Etiketten nach MA-2; 2 PE-Trichter; Einweg-Pipetten; **Prüfgewichte 1 g und 5 g** (F/M1); **abschliessbarer Sekundärbehälter** mit Saugmaterial (Vermiculit/Katzenstreu); Auffangwanne ≥ 20 × 15 cm | Harz A und Härter B nach dem Abfüllen (Kap. 3a, MA-1 … MA-5) |
| Einwegspritzen 1 ml und 3 ml Luer-Lock, stumpfe Dosierkanülen 18–20 G, feiner Synthetikpinsel (≤ 3 mm), Wattestäbchen, kleiner Spiegel | Dosieren, Kanten auftragen, Austritt kontrollieren |
| Einweg-Alu-Schale (**≥ 20 × 15 cm** oder zwei), Schere, **nicht brennbare Unterlage** (Fliese, Blech) | Beutelrest flach aushärten lassen (Variante M-B), Abfüllen (M-A), Kap. 3a |
| Wärmeschrank oder Filamenttrockner mit separatem Thermometer, einstellbar 60 °C (**ANNAHME** vorhanden) | Nachhärtung 4 h bei 60 °C (Kap. 3a) |
| Vakuumkammer (falls vorhanden) | blasenfreier Verguss (K-4), sonst kopfüber mit Entlüftung; bei ER2223 (800 mPa·s) nicht nötig |
| Nitrilhandschuhe **MAPA Solo 977** (0.13 mm, EN ISO 374-1 Typ B; Einkaufsliste V-Z7; freigegeben als Spritzschutz unter HS-1 … HS-5, Kap. 3a), zwei Paar übereinander; für M-A empfohlen Butyl-/Laminat-Überhandschuh (HS-4), **dicht schliessende Chemikalien-Schutzbrille (EN 166)** und **Gesichtsschutz (Visier)**, langärmlige Kleidung, **Kunststoffschürze**, **Augenspülflasche**, Halbmaske mit **Filter A (EN 14387)** bereit, Ventilator | Epoxid: Härter B ist **ätzend (H314) und hautsensibilisierend (H317)**, Harz A reizend und sensibilisierend (Kap. 3a) |
| Halter „kopfüber“ (z. B. Lochplatte, Schraubstock mit Schutzbacken) | Kappe bzw. Sensor beim Aushärten senkrecht halten |

## 2 Vorbereitung der Druckteile

1. Teile auf Druckfehler prüfen: keine Fäden in Nuten und Schlitzen, Ablaufschlitze der Hülse (4 × 3.0 × 1.2) frei,
   Brücken (Muttertasche Kragen, USB/Schott) ohne Durchhang.
2. Hülse innen: Gleitflächen z 1.3 … 7 und 30 … 35 mit 600er Papier glätten (Naht quer zur Dichtung ist ein Leckkanal).
   Kerbe innen entgraten.
3. **Kappe (P5-M1):** Prüfen, dass der Zapfen fest mit der Kappe verbunden ist (Rev-C-Druckdatei hatte einen losen
   Zapfen; ab Phase 5 einteilig). Membran-Senkung Ø 6.4 rundum geschlossen (P5-M3, keine Öffnung zum Innenraum).
4. Masskontrolle der Prüfmasse (in den Zeichnungen gerahmt) stichprobenweise, mindestens: Hülse innen 30.8 × 9.8,
   Kappe/Zapfen 30.4 (Gleitsitz) und Nutgrund 28.1 × 7.1, Kragen 30.4 und Nutgrund, Distanzlehre 24.2 ± 0.1.

**Prüfung 2:** Passprobe (`passprobe_huelse_unten/oben`) mit Kragen bzw. Kappe und O-Ring: gleitet mit Silikonfett ohne
Klemmen, O-Ring sichtbar verpresst (PRINT_SETTINGS Kap. 4). Bei Abweichung XY-Lochkompensation anpassen, nicht die
Geometrie.

## 3 Kappe vormontieren (Pos. 1, 4–8, 10)

1. **Lichtfenster (Pos. 4)** von aussen in den Tropfenausschnitt kleben, Lichtschaft nach innen (Spalt 0.1 je Seite).
   Klebstoff nur auf den Rand, nicht auf die Sichtfläche und nicht in den Innenraum (O-3).
   - **Schutz (UHU plus endfest 300):** Der **Härter ist ätzend** (SDB Härter V35, PDF S. 14: H314, H318, H317, Signalwort
     „Gefahr“), der Binder reizend und sensibilisierend (SDB Binder V62, S. 1–2: H315, H317, H319, H411, EUH205). Darum gilt
     dieselbe Grundausrüstung wie Kap. 3a: Nitrilhandschuhe **> 0.12 mm** (SDB Härter PDF S. 18; zwei Paar übereinander),
     **dicht schliessende Schutzbrille**, Augenspülflasche bereit, gelüfteter Raum, keine Kinder/Haustiere im Raum, Tuben nach
     Gebrauch sofort verschliessen und wie Kap. 3a unter Verschluss lagern. Hände mit Wasser und Seife, **nie mit Lösungsmittel**
     reinigen (TDS S. 5). Erste Hilfe wie Kap. 3a (Augen ≥ 15 min spülen, Arzt; SDB Härter PDF S. 15: P305+P351+P338,
     P301+P330+P331), Tox Info Suisse 145. Flüssige Reste und angebrochene Tuben nicht in Hausmüll oder Abfluss (SDB Binder
     S. 9, Abschn. 13) → Sammelstelle Sonderabfälle; Mischreste auf der Unterlage aushärten lassen, dann wie Kap. 3a
     (**ANNAHME**).
   - Klebeflächen (Tropfenrand und Schaftmantel am Fenster, Wand des Tropfenausschnitts und der Bohrung Ø 3.2 in der Kappe) mit
     120er Papier leicht anrauen, mit Isopropanol entfetten, ablüften. **Kein Aceton** (löst ASA an, **ANNAHME**).
   - Gleich lange Stränge Binder und Härter (1 : 1 Volumen, TDS S. 5) auf der PE-Unterlage gut mischen (gleichmässige Farbe),
     Raum ≥ 18 °C (TDS S. 2). Mit dem Zahnstocher eine **dünne** Schicht nur auf den Tropfenrand des Fensters und rundum auf den
     Schaftmantel (nicht auf die Schaft-Stirnfläche = Lichteintritt) auftragen; Topfzeit ≈ 90 min (TDS S. 1).
   - Kappe mit der Front nach unten auf PE-Folie legen (UHU haftet nicht auf PE, TDS S. 1), Fenster von aussen einsetzen → Sichtfläche
     bündig und sauber. Ausgetretenen Kleber innen an der Schaft-Stirnfläche mit Zahnstocher entfernen; die Fuge muss rundum
     geschlossen sein (Dichtlinie).
   - Liegend aushärten: ≥ 24 h bei Raumtemperatur (Endfestigkeit, TDS S. 1), danach erst Kap. 3 Schritt 2 ff. Optional
     45 min bei 70 °C (TDS S. 2) im Wärmeschrank – unbelastet unter der HDT der Kappe (Bambu ASA 92 °C bei 1.8 MPa).
2. **Stössel (Pos. 8)** von unten in die D-Bohrung des Führungsrohrs stecken (D-Fläche nach vorne, passt nur so),
   Finger links zwischen Führungsrippe (vorne) und Zungennase (hinten).
3. **Membran (Pos. 10)** flach auf den Grund der Senkung Ø 6.4 legen.
4. **Taste (Pos. 5)** mit dem Hals von oben durch den Klemmring (Pos. 6) stecken, **Tastenteller (Pos. 7)** von unten
   auf den Hals pressen. Die Einheit Taste + Klemmring + Teller in die Senkung setzen und den Klemmring (Presssitz) bis
   auf die Membran einpressen (flaches Werkzeug, gleichmässig, O-4).

**Prüfung 3:** Taste federt zurück (Membran), Stössel gleitet ohne Klemmen und lässt sich **nicht verdrehen** (C-1).
Membran rundum unter dem Klemmring geklemmt, Klemmring sitzt bündig und fest (R3-W2). Ohne Platine: beim Drücken bewegt
sich die Zunge sichtbar nach hinten (Nase), in Ruhe ist sie nicht vorgespannt. Fenster bündig, keine Kleberspuren auf
Sichtfläche und Schaft-Stirnfläche, Klebefuge aussen rundum geschlossen (Lupe); gegen eine Taschenlampe von innen
leuchtet der Tropfen gleichmässig.

## 3a Vergussmasse: Schutzmassnahmen, Sitzungsplan, Mischen, Aushärten (gilt für Kap. 4, 5, 5a)

Grundlage: `docs/references/Electrolube_ER2223_TDS_Rev4-2019-03.pdf` (TDS), SDB Teil A
`Electrolube_ER2223-PartA_SDS_Rev0-2016-10-19_EN.pdf` (Stand 2023: `…_Rev0.64-2023-10-27_SV.pdf`), SDB Teil B
`Electrolube_ER2223-PartB_SDS_2023-10-02_HU.pdf`. Auswahl und Begründung: `docs/concepts/vergussmasse_versiegelung.md`;
Sicherheitsprüfung `docs/reviews/phase6_vergussmasse_sicherheit.md`.

**Geltung (K-2):** Gefahren, Schutzmassnahmen, Erste Hilfe, Lagerung und Entsorgung gelten **ab dem ersten Beutel, auch
für die Vorversuche V-1 … V-3**. D-030 ist gültig mit Auflagen: Verguss an Mustern nur, wenn die Abhakliste unten bis
„Vor dem Musterverguss“ vollständig erfüllt ist **und** Kap. 3b am betreffenden Muster bestanden ist.

**Abhakliste D-030 (Freigabebedingungen 1–5, `docs/concepts/vergussmasse_versiegelung.md` Kap. 10; ausdrucken, abhaken,
in der Musterliste ablegen):**

*Vor dem Öffnen des ersten Beutels (Bed. 1) – auch für V-1 … V-3:*
- [ ] SDB Teil B in Deutsch, Englisch, Französisch oder Italienisch unter `docs/references/` abgelegt und ausgedruckt am
  Arbeitsplatz; SDB Teil A und TDS ebenfalls ausgedruckt.
- [ ] Handschuhe **MAPA Solo 977** vorhanden, Datenblatt und Beständigkeitstabelle abgelegt
  (`docs/references/MAPA_Solo977_TechnicalSheet_DE_2026-09.pdf`, `…_Bestaendigkeitstabelle_2024-04-11.pdf`) – von der
  Sicherheit als Spritzschutz unter HS-1 … HS-5 freigegeben, Bed. 1 damit erfüllt (`docs/reviews/phase6_sicherheit_schluss.md`,
  Abschnitt „Handschuhe V-Z7“). Andere Handschuhe nur mit gleicher Prüfung.
- [ ] Schutzausrüstung nach Kap. 1 vorhanden (Korbbrille EN 166, Visier, Augenspülflasche, Schürze, Halbmaske A bereit,
  Auffangwanne, abschliessbarer Sekundärbehälter); **zwei PE-Trichter** (je einer für A und B; kein Silikontrichter mit
  Filter für Teil B, Sicherheit Schlussprüfung W-4).

*Mischvariante (Bed. 2):*
- [ ] **M-B (ganzer Beutel je Sitzung)** ist der Weg, solange M-A nicht bestätigt ist.
- [ ] M-A erst, wenn MA-1 … MA-5 umgesetzt sind **und** entweder Electrolube keine Einwände hat (Konzept Anhang A) oder
  nach MA-6 V-3 an jedem Ansatz und V-6 einmal mit einem gewogenen Ansatz bestanden sind – **Bestätigung durch den
  Orchestrator** in der Musterliste vermerkt.

*Vor dem Musterverguss (Bed. 3):*
- [ ] V-1 … V-3 bestanden (Protokoll in der Musterliste).
- [ ] Am betreffenden Muster Kap. 3b bestanden (Programmieren, Funktionsprüfung, OTA-Update).

*Vor der Serie (Bed. 4):*
- [ ] PT11.19 an ≥ 2 Mustern und PT11.23 bestanden (A-1/A-2), sonst Rückfallmasse (Konzept Kap. 9a, A-3).
- [ ] Tg-Nachweis erbracht (Electrolube schriftlich oder V-6).

*FMEA (Bed. 5):* F-60 und F-63 nachgeführt – erledigt (`docs/reviews/phase5_fmea_light.md`).

**Voraussetzung vor dem Öffnen des ersten Beutels (W-3):** Das SDB Teil B liegt in **Deutsch, Englisch, Französisch oder
Italienisch** vor (abgelegt unter `docs/references/`, ausgedruckt am Arbeitsplatz). Heute liegt Teil B nur ungarisch vor.
Der Auftraggeber fordert es beim Händler an (Textvorlage: Konzept Anhang B). Ohne dieses SDB keinen Beutel öffnen.

**Gefahren (SDB):** Teil A (Harz, schwarz): Achtung – H315 Hautreizung, H317 kann allergische Hautreaktion verursachen,
H319 schwere Augenreizung, H411 giftig für Wasserorganismen (SDB A S. 1). Teil B (Härter): **Gefahr – H314 schwere
Verätzungen der Haut und schwere Augenschäden**, H302, H317, H318, H373 (SDB B S. 2). Gemischt bis zur Aushärtung wie A + B behandeln.

**Schutzausrüstung (SDB A S. 6, SDB B S. 2/6, P280):**
1. **Chemikalien-Schutzbrille** (dicht schliessend, EN 166) und darüber ein **Gesichtsschutz (Visier)** beim Aufschneiden,
   Ausdrücken, Abfüllen und Kneten (SDB B Abschn. 8.2, S. 6).
2. **Handschuhe** (K-3): **MAPA Solo 977** (Nitril 0.13 mm, EN ISO 374-1 Typ B, Datenblatt S. 1–2), freigegeben **nur als
   Spritzschutz** unter den Auflagen der Sicherheit (`docs/reviews/phase6_sicherheit_schluss.md`, „Handschuhe V-Z7“):
   - **HS-1:** **zwei Paar übereinander.** Das äussere Paar **sofort** wechseln bei sichtbarem Kontakt, spätestens nach
     **15 min** Arbeit mit offener Masse oder offenem Härter; danach Hände waschen.
   - **HS-2:** **kein Vollkontakt** – nicht eintauchen, Härter nicht mit dem Handschuh abwischen; Verschüttetes nur mit
     Saugmaterial und Spatel aufnehmen (V-Z4).
   - **HS-3:** Reinigen **nur mit Isopropanol** (Beständigkeit 48 min); **kein Aceton und kein anderes Keton**.
   - **HS-4:** Bei grösserem Verschütten (z. B. platzender Beutel beim Abfüllen M-A) zuerst Handschuhe wechseln. Für das
     Abfüllen **M-A** wird ein **Butyl- oder Laminat-Überhandschuh empfohlen** (nicht Pflicht).
   - **HS-5:** Bei MAPA (bzw. Electrolube) die Permeationsdaten für **CAS 1761-71-3** (Härter B) anfragen (Textvorlage wie
     Konzept Anhang B). Liefert MAPA eine Durchbruchzeit < 10 min, wird der Überhandschuh nach HS-4 **Pflicht**. Die
     Anfrage ist keine Voraussetzung für den ersten Beutel.
   Nicht mit Handschuhen ins Gesicht fassen. Für Harz A (CAS 25068-38-6) und den UHU-Härter gelten dieselben Auflagen.
3. Langärmlige Kleidung und **chemikalienbeständige Kunststoffschürze**; geschlossene Schuhe.
4. **Augenspülflasche** (oder fliessendes Wasser in Griffnähe) am Arbeitsplatz (SDB A S. 6 „eyewash“).
5. Wer bereits auf Epoxid allergisch reagiert, verarbeitet die Masse nicht (H317).

**Arbeitsplatz und Lüftung (W-4, SDB B Abschn. 7.1 S. 5):**
1. Nicht in Wohn- oder Schlafräumen arbeiten. Am **geöffneten Fenster**, möglichst mit einem Ventilator, der **nach aussen**
   bläst (behelfsmässige Absaugung). Unterlage auslegen. **Kein Essen, Trinken, Rauchen.** Kinder, Unbeteiligte und
   Haustiere fernhalten.
2. Schale mit Resten (Variante M-B) und den Trockner zum Nachhärten in einen belüfteten Raum stellen, **nicht in Wohn- oder
   Schlafräume**, ausser Reichweite von Kindern und Haustieren.
3. Bei Geruch oder Reizung abbrechen und lüften. Wer regelmässig vergiesst: **Halbmaske mit Filter A (EN 14387)** bereithalten
   (SDB A S. 6).
4. Den Filamenttrockner nach der Nachhärtung geöffnet auslüften lassen, bevor er wieder für Filament verwendet wird (**ANNAHME**).
5. Isopropanol (Kap. 2/5) ist leicht entzündlich: Gebinde geschlossen und weg vom Wärmeschrank halten.

**Erste Hilfe (W-3; SDB B Abschn. 4.1 S. 3, SDB A 2023 S. 3):** Notfall Schweiz: Tox Info Suisse **145**, Rettung **144**;
SDB zum Arzt mitnehmen.
- **Augen:** sofort mit viel Wasser, auch unter den Lidern, **mindestens 15 min** spülen, Lider offen halten, Kontaktlinsen
  entfernen; **immer sofort Arzt**.
- **Haut:** verunreinigte Kleidung **und Schuhe** sofort ausziehen, Haut sofort mit Seife und viel Wasser waschen (kein
  Lösungsmittel, auch kein Isopropanol auf der Haut); nach Kontakt mit Härter oder frischer Mischung **Arzt**.
- **Einatmen:** an die frische Luft, bei Beschwerden Arzt; Hinweis an den Arzt: **verzögertes Lungenödem möglich**.
- **Verschlucken:** Mund ausspülen, **kein Erbrechen** herbeiführen, sofort Arzt (P301 + P330 + P331).

**Lagerung (SDB B Abschn. 7.2 S. 5, TDS S. 1):** dicht verschlossen, trocken, 15–35 °C, gut belüftet, **unter Verschluss und
für Kinder unzugänglich**; nicht neben Lebensmitteln. Ablaufdatum auf dem Beutel (Haltbarkeit 12 Monate, TDS S. 1).

**Entsorgung:** ausgehärtete Reste, leere Beutel/Flaschen, Spritzen und Handschuhe erst nach vollständiger Aushärtung in
den Kehricht (**ANNAHME**, Abschn. 13 der SDB beachten); **flüssige Reste nie in den Ausguss** (H411). Ungemischte Beutel und
Restmengen A/B bei der Sammelstelle für Sonderabfälle abgeben.

**Vorbedingung jeder Vergusssitzung (W-1): Clip leer** – keine Zelle, keine Dummy-Scheibe im Clip, an jedem Sensor vor dem
Mischen kontrolliert und in der Musterliste abgehakt. Gilt für Schott (Kap. 4), Kragen (Kap. 5), Kanten (Kap. 5a), jede
Nacharbeit (Kap. 8) und die Nachhärtung.

**Sitzungsplan:** Schott und Kragen brauchen getrennte Sitzungen (Schott muss hart sein, bevor der Kragen gesetzt wird).
Gemischte Masse ist **30 min verarbeitbar** (20 °C, TDS S. 1), Gelzeit 90 min. Bedarf je Sensor ≈ 0.2 g. Pro Ansatz eine
Gruppe von **≤ 8 Sensoren** (**ANNAHME**, Zeit pro Sensor beim Vorversuch V-1 messen). **Alles, was nicht mit Masse zu tun
hat (Clip leer, Einspannen, Lehren, Kapton, Reinigen), vor dem Mischen erledigen.**

**Vorversuche vor dem ersten Muster (PROTOTYP-PRÜFUNG, Konzept Kap. 12):** V-1 Vergussprobe Kragen und Schott mit
FR4-Reststreifen 1.6 mm (Füllung, Blasen, Austritt, Zeit pro Sensor), V-2 Haftprobe auf angerautem ASA, V-3 Härteprobe
(Becherrest 1 h bei 80 °C bleibt hart), V-6 Kriechprobe 80 °C (Tg-Ersatznachweis, Konzept Kap. 12). Muster erst
vergiessen, wenn V-1 … V-3 bestanden sind (V-6 vor der Serie).

**Mischen – zwei Varianten. Bis zur Bestätigung von M-A (Abhakliste Bed. 2) gilt M-B.** Variante **M-A (abfüllen und wägen)** ist sicherheitlich zulässig unter MA-1 … MA-5
(`docs/reviews/phase6_vergussmasse_sicherheit.md` Runde 2). Sie gilt, sobald Electrolube keine Einwände hat (Anfrage
Konzept Anhang A) **oder** – ohne Antwort, nach Entscheid des Orchestrators (MA-6) – MA-1, MA-2, MA-4 umgesetzt und V-3
an jedem Ansatz sowie V-6 einmal mit einem gewogenen Ansatz bestanden sind. Sonst **Variante M-B**.

*Gemeinsam:* Raum und Material 20–25 °C (Lagerung über 15 °C, TDS S. 1). Ablaufdatum prüfen. Uhrzeit des Mischens notieren:
**Ende der Verarbeitung = Mischzeit + 30 min.** Masse, die bereits zieht (Fäden, deutlich zäher), nicht mehr verwenden. Von
jedem Ansatz einen Becherrest (≥ 5 mm hoch) für V-3 behalten.

*Variante M-A – Beutel einmal abfüllen, Kleinmengen wägen (TDS S. 3 „Bulk Mixing“):*

Gebinde und Lagerung (MA-1, MA-2):
- **Nie Lebensmittel- oder Getränkeflaschen** verwenden, auch nicht gereinigt; nur Laborflaschen.
- **Flasche B (Härter): HDPE, ≈ 60 ml, mit kindergesichertem Verschluss** (Drück-Dreh), **kein Glas**. Flasche A (Harz):
  HDPE oder Glas, ≈ 250 ml, ebenfalls kindergesichert (**ANNAHME** Verfügbarkeit; HDPE-Beständigkeit gegen den Härter mit
  der Beständigkeitsliste des Flaschenherstellers prüfen).
- Deckel und Flaschen **farbig markieren: A rot, B blau**; Deckel nie tauschen.
- **Etikett je Flasche:** „ER2223 Teil A – Harz“ bzw. „ER2223 Teil B – Härter“; Signalwort (A **Achtung**, B **Gefahr**);
  GHS-Piktogramme und H-Sätze nach SDB Abschn. 2.2 (A: H315, H317, H319, H411; B: H302, H314, H317, H373); P-Sätze P280,
  P305+P351+P338, bei B zusätzlich P301+P330+P331 und P303+P361+P353; „**Kein Lebensmittel – nicht trinken**“; „Unter
  Verschluss, für Kinder unzugänglich“; Abfülldatum, Ablaufdatum des Beutels, **Verbrauchen bis = Abfülldatum + 3 Monate**;
  Name und Telefon der verantwortlichen Person; Notruf Tox Info Suisse **145**.
- Beide Flaschen stehen in einem **dicht schliessenden Kunststoff-Sekundärbehälter mit Saugmaterial** (Vermiculit oder
  Katzenstreu, SDB B Abschn. 6.3), **abgeschlossen** (Vorhängeschloss oder abschliessbarer Schrank), nicht bei Lebensmitteln,
  nicht im Kühlschrank. **Nur ein angebrochener Satz A/B** gleichzeitig.
- **Haltbarkeit (MA-3):** höchstens **3 Monate** nach dem Abfüllen (**ANNAHME** bis zur Antwort von Electrolube, Anhang A;
  SDB B Abschn. 10.4: Luft und Feuchte meiden). Härter, der trüb wird oder eine Kruste bildet, nicht verwenden. Kristallisierten
  Härter (Schmelzbereich 17.7–65.4 °C, SDB B Abschn. 9) in der **geschlossenen** Flasche im **Wasserbad bei 40 °C** anwärmen
  (TDS S. 3), mit Visier öffnen; **nie Mikrowelle, nie im Trockner** zusammen mit Sensoren.

1. **Abfüllen (MA-5)**, einmal je Beutel, volle Schutzausrüstung inkl. Visier, in einer **Auffangwanne** (≥ 20 × 15 cm) auf
   nicht brennbarer Unterlage, Saugmaterial bereit: Clip **nicht** entfernen. **Zuerst A:** Ecke der Harzkammer abschneiden,
   über einen **PE-Trichter** in Flasche A ausdrücken, Flasche schliessen. **Dann B:** Ecke der Härterkammer abschneiden,
   **langsam** über einen zweiten Trichter in Flasche B ausdrücken (der Beutel kann an der Clip-Kante platzen), schliessen.
   Danach am leeren Beutel den Clip entfernen und die **Reste von A und B im Beutel verkneten**, im belüfteten Raum
   aushärten lassen, erst dann in den Kehricht (**ANNAHME**, siehe „Entsorgung“). Trichter ebenso aushärten lassen oder
   als Sonderabfall abgeben.
2. **Waage prüfen (MA-4):** vor jeder Sitzung mit den **Prüfgewichten 1 g und 5 g** (Klasse F/M1) kontrollieren, Anzeige in
   die Musterliste. Abweichung > 0.02 g → nicht wägen, Waage justieren bzw. ersetzen (**ANNAHME** Grenze).
3. **Ansatz wägen:** Flasche A vor der Entnahme gründlich aufrühren (Sediment, TDS S. 3). Mischbecher tarieren.
   **Mindestansatz 8 g: 6.90 g A + 2.00 g B** (3.45 : 1 nach Gewicht, TDS S. 1). Je Komponente eine **eigene, beschriftete
   Einweg-Pipette oder Spritze** (rot A, blau B), nicht aus der Flasche giessen. **Reihenfolge: A wägen, Flasche A
   schliessen; dann B wägen, Flasche B schliessen – nie beide Flaschen gleichzeitig offen.** Bei Überschiessen nicht
   zurückgeben, sondern den Partner nachrechnen und nachwägen. Beide Werte in die Musterliste schreiben.
4. Mit einem Spatel **2 min** langsam rühren, Wand und Boden abstreifen, bis gleichmässig schwarz ohne Schlieren; ≈ 2 min
   stehen lassen, Blasen steigen auf. Spritzen von unten befüllen (Kolben ziehen), Kanüle aufsetzen, Luft ausstossen.
5. Flaschengewinde mit einem Tuch abwischen, Flaschen in den Sekundärbehälter, abschliessen. **V-3 an jedem Ansatz**
   (Becherrest).

*Variante M-B – ganzer Beutel (TDS S. 1–2, Resin Pack):*
0. Kristallisierter Härter: geschlossenen Beutel im Wasserbad bei 40 °C anwärmen, bis die Kristalle geschmolzen sind
   (TDS S. 3), dann auf Raumtemperatur abkühlen lassen.
1. Beide Endkappen abnehmen, Clip durch vorsichtiges Auseinanderziehen entfernen; Harz und Härter im Beutel **3–4 min**
   durchkneten, mit dem Clip das Material aus den Ecken streichen, bis die Farbe gleichmässig schwarz ohne Schlieren ist.
2. Eine Ecke abschneiden und sofort 3–5 Spritzen à 1–3 ml füllen. **Den Rest sofort ausgiessen (K-1):** in eine Alu-Schale
   **≥ 20 × 15 cm** (≈ 227 ml → ≈ 7.5 mm Schichtdicke) oder zwei Schalen, auf eine **nicht brennbare Unterlage** (Fliese,
   Blech, nicht Karton), im belüfteten Raum aushärten lassen. **Den Rest nicht in den Trockner stellen** (TDS S. 3: „Do not
   heat cure large volumes immediately“; dieselbe Seite: „Small volumes (250ml) may be heat cured immediately“ – die
   Selbsterwärmung der Beutelmenge ist also beherrschbar).

**Aushärten:** kopfüber im Halter **24 h bei 20–25 °C**, danach **4 h bei 60 °C** (TDS S. 1 „Cure Time (60 °C)“, S. 3
„post-cure … if required“) im Wärmeschrank/Filamenttrockner. Temperatur mit eigenem Thermometer prüfen, **nie über 65 °C**
(ASA, Fenster, Membran). **Clip leer** (W-1, siehe oben). Die Nachhärtung entfällt nur, wenn Electrolube schriftlich
einen Tg ≥ 80 °C nach Raumtemperatur-Härtung bestätigt (offen). Erst danach Lehren entfernen, prüfen, weiter.

## 3b Reihenfolge: erst programmieren, prüfen und ein OTA-Update, dann vergiessen (R W-1)

Nach dem Verguss (Schott Kap. 4, Kragen Kap. 5) gibt es **keinen Rückweg über Weg B** (Lötdraht an R9, Dummy-Scheibe im
Clip; `PROGRAMMIEREN_SENSOR.md` Kap. 5), und Weg A (Federstiftkopf) ist noch nicht gebaut (`hardware/programmer/README.md`
Kap. 4). Ein Muster mit einer Firmware, die BLE oder OTA nicht beherrscht, wäre nach dem Verguss verloren. Darum gilt für
**jedes Muster vor Kap. 4**:

1. **Programmieren nach Weg B** (`PROGRAMMIEREN_SENSOR.md` Kap. 5, nur mit Dummy-Scheibe `hardware/dummy_cell/`).
   Mit Draht an R9 (z 41.6, im Kappenbereich) nur an der **losen** Platine, also vor Kap. 4 (Kappe, Gabel, Schottkeil noch
   nicht montiert). Die Lasche der Scheibe hat in jedem Zustand ohne Hülse Platz (`hardware/dummy_cell/README.md` Kap. 6a).
2. **Funktionsprüfung mit Zelle** (`PROGRAMMIEREN_SENSOR.md` Kap. 5 Schritt 9): L11-Startsignal, Advertising
   `fluidi-XXXX`, Taster, Messung.
3. **Ein erfolgreiches OTA-Update:** Muster mit dem Gateway koppeln (`PAIRING_KALIBRIERUNG.md`), ein signiertes Abbild
   mit **höherer Version** (z. B. `make VERSION=0.1.1`, Tabelle `TESTFIRMWARE.md` Kap. 4) in der App unter *Sensoren &
   Firmware* hochladen und an genau dieses Muster verteilen. **Bestanden**, wenn der Sensor danach die neue Version meldet,
   eine Messung liefert und gekoppelt bleibt. Zellspannung ≥ 3.0 V (OTA-Schwelle 2.7 V, `ENERGIEMESSUNG.md`, FW-P6).
   Ein Downgrade per OTA ist nicht möglich (MCUboot); der Stand nach dem Test bleibt drauf oder wird vor dem Verguss
   nochmals nach Weg B geflasht.
4. **Zelle wieder entnehmen** (kein Metallwerkzeug), **Clip leer** kontrollieren (W-1), Kennung für das Etikett notieren
   (Kap. 7a). Eintrag in der Musterliste: Version, OTA bestanden, Datum.

Fällt 2 oder 3 durch: **nicht vergiessen**, melden (Firmware/Elektronik). Erst wenn 1–4 bestanden sind und die Abhakliste
Kap. 3a bis „Vor dem Musterverguss“ erfüllt ist, weiter mit Kap. 4.

## 4 Platine einsetzen und Schott vergiessen (Pos. 9, 15, 16)

**Vor dem ersten Kappenverguss (Pflicht, Auflagen Red Team Runde 3, D-026):** (1) Tastenkraft bis zum Klick am
unvergossenen Kern messen (Gewichte/Kraftmesser): ≤ 12 N, über 15 N nicht vergiessen und melden (N-2, REQ-UI-05);
(2) Klemmring-Passprobe (Presssitz hält, Membran rundum verpresst) und Membranrand zusätzlich abdichten (W-1; Dichtmittel
nach Wahl der Mechanik, ANNAHME bis Datenblatt); (3) Gleitfläche der Nase nach dem Druck glätten (N-3);
(4) Farbeindringprüfung der Membranabdichtung an den ersten 3 Mustern (M-W3).

0. **Clip leer (W-1):** keine Zelle, keine Dummy-Scheibe im Clip – kontrollieren und in der Musterliste abhaken.
1. Platine (Pos. 16, Zelle **nicht** eingesetzt) mit der bestückten Seite F **zum Fenster** von unten durch den
   Schottschlitz (26.4 × 4.0) einschieben, bis die Platinenoberkante am **Anschlag der Kappe** liegt (z 53.5). Die
   Quetschrippen (Gabel und Schott-Rückwand) drücken die Platine nach vorn an die F-Referenz.
2. Kappe **kopfüber** einspannen (Sonde zeigt nach oben). Die Platine bleibt durch ihr Gewicht am Anschlag
   (PCB_OUTLINE Kap. 2, Lage z ± 0.22).
3. **Schottkeil (Pos. 9)** in den vorderen Spalt zwischen Platine F und Schott schieben (Rückseite an F).
4. **Schott vergiessen (Pos. 15):** Epoxid (O-1, Kap. 3a) in den Schottschlitz um die Platine, Volumen ≈ **12 mm³** (CAD,
   `check_sensor.txt` Pkt. 8). Nicht überfüllen: kein Epoxid ins Zellfach (Clip-Pads liegen 0.55 mm unter der
   Vergusskante z 30.8). Aushärten kopfüber nach Kap. 3a.
   Mit ER2223 (dünnflüssig, 800 mPa·s): mit 1-ml-Spritze und Kanüle 20 G in 2–3 kleinen Tropfen rund um die Platine
   dosieren und jeweils ≈ 30 s warten, bis die Masse in den Spalt gezogen ist (≈ 0.01 ml je Tropfen, **ANNAHME**).
   Die Austrittsseite im Elektronikraum (Bauteilband ab z 32.7, 0.7 mm über der Schott-Oberseite) ist nicht einsehbar;
   deshalb nur die Menge aus dem Vorversuch V-1 dosieren (dort im Schnitt geprüft). Aufsteigende Blasen an der
   Oberfläche mit der Kanülenspitze öffnen. Überschuss auf der Platine **trocken** mit dem Wattestäbchen abnehmen (kein
   Isopropanol auf frische Masse).

**Prüfung 4:** Verguss rundum lückenlos (Lupe), keine Blasen an der Platinenkante, nichts auf den Clip-Pads. Platine sitzt
weiterhin am Anschlag (Spalt Oberkante–Anschlag 0; Sicht durch das Fenster: LED mittig hinter dem Tropfen). Masse nach dem
Aushärten (Kap. 3a) hart und nicht klebrig; Becherrest der Sitzung gleich (V-3).

## 5 Kragen setzen und vergiessen (Pos. 3, 13, 14) – Sondenübergang, Dichtlinie

Der Kragenverguss ist die **Sondendichtung** (S3-K2, REQ-MECH-08). Er wird nie wieder gelöst.

0. **Clip leer (W-1):** keine Zelle, keine Dummy-Scheibe im Clip (auch nach Programmieren Weg B, Kap. 6) – kontrollieren
   und abhaken.
1. **Reinigen (K-5):** Platine im Bereich z 0 … 8 (Dichtstreifen und Feld U3/C24) **und die ganze Sonde bis zur Spitze**
   (Kanten für Kap. 5a) mit Isopropanol von Flussmittel und Fett befreien, ≥ 15 min trocknen lassen; danach die Sonde
   nur noch mit Handschuhen anfassen. Ein Primer ist für ER2223 im TDS nicht vorgesehen. Schlitz und Taschenwände des
   Kragens mit 600er Papier bzw. Nadelfeile leicht anrauen, Staub ausblasen, mit Isopropanol abwischen, trocknen.
   Die Reinigung vor dem Mischen erledigen (Kap. 3a, Topfzeit).
2. **Mutter M2 (Pos. 13)** von vorne in die Muttertasche des Kragens schieben, **Kapton-Punkt** auf die Gewindeöffnung
   (unten) kleben, damit kein Epoxid ins Gewinde läuft.
3. Kragen von der Sondenspitze her über die Sonde schieben (Schlitz 20.3 × 1.9, Tasche U3/C24 auf der F-Seite).
4. Die **2 Distanzlehren 24.2 (FL-S-10)** auf der B-Seite zwischen Kragen-Oberkante und Schott-Unterkante stellen und den
   Kragen dagegen halten. Der Kragen sitzt mittig um die Platine.
5. Sensor **kopfüber** (Sondenspitze oben) einspannen. **Kragen vergiessen (Pos. 14)** von der Hohlkehle an der
   Kragenunterseite her, bis Spalt, Hohlkehle und Tasche U3/C24 gefüllt sind; Volumen ≈ **62 mm³** (CAD). Die Tasche ist
   unten offen und entlüftet nach oben (PCB_OUTLINE Kap. 7). **Nur eine Masse, kein weicher Vorverguss auf U3/C24
   (K-4).** Blasenfrei: Vakuum oder langsam füllen und entlüften.
   Mit ER2223 (Kap. 3a): 3-ml-Spritze, Kanüle 18–20 G. Zuerst die **Tasche U3/C24** füllen: Kanüle 20 G (Ø 0.9 mm, Tasche 1.2 mm
   tief) durch die oben liegende Öffnung neben U3 bis zum Taschengrund führen, langsam dosieren und die Kanüle dabei
   zurückziehen, bis die Tasche bis zur Öffnung voll ist (Luft entweicht nach oben; U3 und C24 nicht berühren), dann rundum den Spalt um die Platine und zuletzt
   die Hohlkehle bis knapp an die Kragenunterseite. In Portionen dosieren und jeweils warten, bis der Spalt die Masse
   aufgenommen hat. Mit dem Spiegel die **Kragen-Oberseite (z 6.6, zum Zellfach)** kontrollieren: Masse darf aus dem
   Schlitz höchstens als Wulst ≤ 0.3 mm austreten; was weiter Richtung Clip-Pads (0.55 mm) kriecht, sofort trocken mit
   dem Wattestäbchen abnehmen. Kein Epoxid in die O-Ring-Nut. Nach 5–10 min Blasen an der Oberfläche öffnen und, wenn
   der Spiegel gesunken ist, nachdosieren.
6. **Kanten der Sonde versiegeln** (Kap. 5a) in **derselben Sitzung**, solange der Kragenverguss noch flüssig ist.
7. Aushärten nach Kap. 3a (24 h kopfüber, dann 4 h 60 °C). Danach Lehren entfernen.

**Prüfung 5:**
- Abstand Kragen-Oberkante ↔ Schott-Unterkante 24.2 ± 0.1 an beiden Seiten (Messschieber).
- Hohlkehle rundum gefüllt, kein Spalt Epoxid ↔ Platine im Dichtstreifen z 1.3 … 3.5 (Lupe), keine Lunker.
- Kein Epoxid in der O-Ring-Nut des Kragens und nicht auf den Clip-Pads (Abstand 0.55).
- Mutter fest eingegossen, Gewinde frei (Kapton entfernen, Schraube probeweise 2 Gänge eindrehen, wieder lösen).
- Sonde: Kantenversiegelung nach Kap. 5a geprüft (Prüfung 5a), Stecktiefen-Markierung z −5 sichtbar.
- Masse hart, nicht klebrig; Becherrest der Sitzung bestanden (V-3).
- Für ein Opfermuster: Schliff bzw. Farbeindringprüfung durch den Kragen (K-7, Testplan ST-W4).

## 5a Kantenversiegelung der Sonde (O-2, REQ-MECH-07)

Ziel: Die gefräste Schnittkante (offenes Glasgewebe) und die Spitze dicht verschliessen, **ohne** die Sondenflächen zu
beschichten. Eine Schicht auf den Flächen senkt die Messspanne stark (50 µm ≈ −6 … −9 %, 100 µm ≈ −12 … −17 %,
`simulation/field/results/coat_epoxy.txt`); die Kante allein kostet ≈ 1–2 % (**ANNAHME**, PROTOTYP-PRÜFUNG V-4). Kupfer
liegt ≥ 1.25 mm innerhalb der Kontur und ist von aussen nicht zugänglich (4 Lagen). Gleiche Masse wie der Kragen (K-4:
ein Material im Leckpfad), gleiche Sitzung wie Kap. 5 (Masse noch nicht über 30 min alt).

1. Sensor bleibt kopfüber eingespannt (Spitze oben), **Clip leer** (W-1). Sonde ist nach Kap. 5 Schritt 1 sauber und trocken.
2. Mit dem feinen Pinsel (oder der Kanüle, Masse als Raupe ziehen und mit dem Pinsel verstreichen) die Masse auf
   **beide Längskanten, die Fasen der Spitze und die Stirnfläche der Spitze** auftragen, von der Spitze nach unten bis in
   die noch flüssige Hohlkehle des Kragens: Kante und Kragen bilden so eine durchgehende Schicht ohne Fuge.
3. Auf den Flächen höchstens **1 mm** von der Kante her überlappen; was weiter auf die Fläche läuft, sofort trocken mit
   dem Wattestäbchen abnehmen. Die Stecktiefen-Markierung bleibt frei.
4. Nach ≈ 10 min nachsehen: Abtropfnasen an der Spitze und Läufer auf den Flächen abnehmen; dünne Stellen (Glasfaser
   sichtbar) ein zweites Mal überstreichen, solange die Masse noch flüssig ist (Gelzeit 90 min).
5. Aushärten mit dem Kragen (Kap. 3a).

**Prüfung 5a:**
- Lupe ≥ 10×: Kante und Spitze rundum geschlossen glänzend schwarz, keine sichtbaren Glasfasern, keine Blasen/Krater,
  lückenloser Übergang in die Hohlkehle des Kragens.
- Nach der Nachhärtung **nicht klebrig** (K-5): ein Wattestäbchen, über Kante und Spitze gestrichen, lässt keine Faser
  zurück. Sensoren mit klebriger Kante **nicht** in Erde einsetzen (ungehärtete Reste laugen aus, H411/H314) und melden.
- Messschieber: Sondenbreite an 3 Stellen 0.1 … 0.4 mm grösser als vor dem Versiegeln (Schicht 0.05 … 0.2 mm je Kante,
  **ANNAHME**). Flächen ausserhalb des 1-mm-Randes ohne Masse.
- Nur **ein** Muster (PROTOTYP-PRÜFUNG V-4): Kanten erst in der **nächsten** Sitzung versiegeln (Kragen dann schon hart).
  Vorher Messfrequenz in Luft und in Wasser notieren (Testfirmware, Zelle eingesetzt, Hülse montiert). Dann Hülse ab,
  **Zelle entnehmen, Clip leer** (W-1), erst danach Masse auftragen und nachhärten. Nachher Zelle wieder einsetzen
  (Kap. 7) und gleich messen. Kriterium: Spanne um ≤ 3 % geändert. Dieses Muster hat am Übergang
  Kante/Hohlkehle eine Fuge „nass auf hart“ und ist für K-7 nicht repräsentativ.
- Kalibrierung (2-Punkt) und Vorkonditionierung (≥ 14 Tage wässern, `simulation/field/REPORT.md` Kap. 7) erst **nach**
  dem Versiegeln und Aushärten.

## 6 Programmieren

Nach Kap. `docs/manuals/PROGRAMMIEREN_SENSOR.md`, **Weg A** (Programmieradapter, Hülse abgezogen, Zugang zu TP1/TP2 im
Zellfach). Keine Zelle im Clip. Danach Dummy-Zelle entnehmen.

**Solange Weg A nicht freigegeben ist** (Test ST-P1, Sicherheitsauflagen PS-W1/A1–A5): Muster **vor dem Verguss**
nach Weg B (Kap. 5 der Programmieranleitung, nur mit Dummy-Scheibe) programmieren, d. h. diesen Schritt **vor Kap. 4**
dieser Anleitung ausführen (R3-K4), zusammen mit Funktionsprüfung und OTA-Update nach **Kap. 3b**. **Nach der Funktionsprüfung mit Zelle (PROGRAMMIEREN Kap. 5 Schritt 9) die Zelle
wieder entnehmen** (kein Metallwerkzeug); erst mit leerem Clip vergiessen (W-1). Eine geprüfte Zelle ≥ 3.0 V darf in
Kap. 7 wieder eingesetzt werden, Zellen < 2.6 V entsorgen (PROGRAMMIEREN Kap. 6).

## 7 Zelle einsetzen, O-Ringe, Hülse schliessen (Pos. 2, 11, 12, 17)

1. **Zelle (Pos. 17)** einsetzen: Pluspol zur Front (−y), von der offenen Clip-Seite (+x, von vorne gesehen rechts)
   flach einschieben bis zum Anschlag. **Taste dabei nicht berühren** (sonst startet der ROM-Bootloader, W-10).
   Erwartet: LED-Startsignal L11 (Grün 200 ms; Fehler Rot 3 × 100 ms; PROGRAMMIEREN Kap. 6/7).
2. **O-Ringe AS568-019 (Pos. 11), Werkstoff EPDM** (Einkaufsliste S2) mit einem **dünnen Film** Silikonfett versehen
   (Fingerspitze, Ring glänzt, keine Fettwülste) und in die Nut am Kragen und am Zapfen legen. Nicht verdrehen, nicht über
   scharfe Kanten ziehen. Begründung: `docs/references/Parker_ORD5700_ORingHandbook_2007.pdf` PDF-S. 206 (Verträglichkeit
   „Silicone Greases“: EPDM **1** = zufriedenstellend, Silikon VMQ **3** = zweifelhaft; Legende S. 162 ff.) und S. 68 (Abschn. 3.14.2: Silikonöle
   und -fette mit allen Dichtwerkstoffen ausser Silikon); S. 50 (Tab. 3-1, Hinweis: Montagefett immer sparsam, ein leichter
   Film genügt). **Keine Silikon-O-Ringe** mit Silikonfett verwenden; kein Vaseline/Mineralfett an EPDM (S. 16: EPDM nicht
   verträglich mit Mineralölprodukten).
3. **Hülse (Pos. 2)** mit gereinigter Sonde von der Sondenspitze her aufschieben, bis der Rand im Dachziegelschlitz der
   Kappe sitzt. Gleichmässig schieben, nicht auf die Taste drücken.
4. **Schraube M2 × 3 (Pos. 12)** von unten durch den Hülsenboden eindrehen. Beim ersten Mal furcht sie durch die
   Lippe Ø 1.7 (die Lippe hält sie beim Lösen fest, sie ist aber **nicht unverlierbar**: weiter herausgedreht fällt sie
   heraus, S K-5), dann in die Mutter. Handfest anziehen (O-6). Einschraubtiefe 1.4 mm = 3.5 Gänge
   (`check_sensor.txt` 5c; UL-4200A-Massstab ≥ 2 volle Gänge, `phase3_sleeve_sicherheit.md`).

**Prüfung 7 (Pflicht, FMEA F-21/F-62):**
- Hülse lässt sich von Hand nicht abziehen, Sichtfuge rundum gleich (0.3 mm), Kerbe um den Tropfen gleichmässig.
- O-Ringe sichtbar verpresst bzw. nicht aus der Nut gequetscht (vor dem Aufschieben kontrollieren).
- Ablaufschlitze hinten frei.
- Funktion: Taste **mit normaler Fingerkraft** kurz drücken (≈ 8 N, klickt nach ≈ 0.3 mm) → Messung/Statusanzeige
  (REQ-UI-04). Nicht mit Kraft nachdrücken: nach dem Klick trägt SW1 die Tastenkraft (O-5). L11 war nach dem Einsetzen sichtbar.
- Eintrag in der Musterliste: Seriennummer `fluidi-XXXX`, Prüfungen 2–7, Datum.

## 7a Kennungsetikett (R K-l5)

Die Anleitungen für Nutzer verlangen den Vergleich der Kennung in der App mit dem **Aufkleber am Sensor**
(`INBETRIEBNAHME.md` Kap. 5 Schritt 3 und Kap. 6 Schritt 3, `PAIRING_KALIBRIERUNG.md` Kap. 2.1 Schritt 3).

- **Kennung:** `fluidi-XXXX` = Gerätename im Advertising (zwei niederwertigste Bytes der BLE-Adresse,
  `firmware/sensor/core/fl_proto.c` `fl_device_name`). Ablesen nach Kap. 3b Schritt 2/3: in der App beim Koppeln oder mit
  einer BLE-Scanner-App am Telefon (**ANNAHME** beliebige App). **Nur von der Werksfirmware** ablesen – Testfirmware heisst
  `fl-tf<n>-XXXX` und darf nie auf ein Etikett.
- **Herstellung:** Etikettendrucker mit **laminiertem** Kunststoff-Schriftband 9 mm, schwarz auf weiss (z. B. Brother TZe,
  **ANNAHME** Typ und Werkstattbestand; Einkaufsliste S12). Text einzeilig `fluidi-XXXX`, Schrift ≈ 4 mm hoch,
  Bandlänge ≤ 26 mm (Rand des Druckers so klein wie möglich einstellen), Ecken rund schneiden. Kein metallisiertes oder
  Silber-Etikett (Antenne in der Kappe). Ersatz ohne Drucker: wetterfestes Laser-Folienetikett (Polyester/PP),
  **ANNAHME**, Haftung wie unten prüfen.
- **Ort:** **Rückseite der blauen Kappe** (y = 13, gegenüber dem Tropfenfenster), mittig in x, zwischen Sichtfuge
  (z 43.5) und Oberkante (z 57.5) im Feld z ≈ 46 … 55 (≥ 2 mm über der Fuge, damit Giesswasser an der Fuge nicht unter
  die Kante zieht). Die Kappe gehört fest zum Sensor (vergossen), die Hülse ist ein Tauschteil → **nicht** auf die Hülse
  kleben. Antennenkupfer liegt innen auf der Platine (Abstand > 4 mm, Etikett ohne Metall, **ANNAHME** ohne Einfluss).
- **Kleben:** Fläche mit Isopropanol entfetten, ablüften, Etikett ohne Blasen andrücken, 30 s fest reiben.
- **PROTOTYP-PRÜFUNG:** Haftung auf der gedruckten ASA-Oberfläche nach 7 d 65 °C und nach dem Giesstest (Kanten heben
  nicht ab), Lesbarkeit; RSSI mit/ohne Etikett gleich (Elektronik).
- Eintrag in der Musterliste: Kennung = Etikett (zweite Person liest gegen).

## 8 Batteriewechsel (Werkstatt / Muster)

Ablauf für Nutzer: `docs/manuals/BATTERIEWECHSEL.md` (mit Sicherheitshinweisen). Zusätzlich für die Werkstatt:

1. Sonde reinigen, über einer Schale arbeiten (FMEA F-22). Schraube lösen (TX6), Hülse nach unten über die Sonde
   abziehen (`renders/final/fluidi_04_batteriewechsel.png`).
   Dabei Kantenversiegelung (Kap. 5a) und Hohlkehle des Kragens unter der Lupe ansehen: abgeplatzte Stellen oder
   sichtbare Glasfasern in der Musterliste notieren und melden.
2. Zelle zur offenen Clip-Seite (+x) herausschieben, **kein Metallwerkzeug** (S3-L1, F-24). Clip-Lötstellen unter der
   Lupe prüfen (Pads am Katalogminimum, Red-Team K-4).
3. Nur neue Markenzellen (Panasonic CR2032) mit **≥ 3.0 V Leerlauf** einsetzen; Zellen < 2.6 V nicht wieder verwenden,
   abkleben, entsorgen (PS-K1 Bed. 3). Taste nicht berühren, L11 beobachten.
4. O-Ringe prüfen, mit dünnem Film Silikonfett versehen (nur EPDM-Ringe, Kap. 7 Schritt 2), beschädigte oder
   gequollene ersetzen. Hülse aufschieben, Schraube handfest.
5. Prüfung 7 wiederholen. Wechsel in der Musterliste zählen (Testplan: 50 Wechsel ST-K6, Spritzwasser nach 10 Wechseln).

**Nacharbeit an Kantenversiegelung oder Hohlkehle (W-1):** nur nach Rücksprache mit der Projektleitung (eigener Ansatz,
Fuge „nass auf hart“). Ablauf: Zelle nach Schritt 2 entnehmen, **Clip leer** kontrollieren, dann Kap. 3a und 5a, Nachhärtung
ohne Zelle; erst danach Schritt 3–5.

## 9 Demontage / Reparatur

Kappe, Platine, Schott und Kragen bilden nach dem Verguss eine Einheit und sind nicht zerstörungsfrei trennbar
(S3-K1/K2). Zugänglich bleiben nur Zellfach, O-Ringe, Hülse und Schraube.
