# Prüfbericht Phase 3 – Batteriewechsel über die Farbfuge („Hülse“), Sicht Sicherheit

Prüfer: Sicherheits-Agent, Stand 2026-11-07. Prinzipprüfung ohne CAD, unabhängig vom Mechanik-Agenten.
Geprüft: Wunsch des Auftraggebers aus D-009 (kein Batteriefach hinten, kein Warnaufdruck; Kopf an der Farbfuge
blau/grau trennen, Schraube von unten oder Klick, grauen Teil über die Sonde nach unten abziehen) gegen
REQ-SAF-01/05/06, REQ-SAF-CC-02/03/04/05, REQ-MECH-13/15, CONCEPTS Kap. 2.7/2A (Auflagen R2-A1…A4, A-32-Auflagen 1–4,
R2-W01), `docs/reviews/phase2_concepts_sicherheit.md`, `docs/reviews/phase3_design_mechanik.md` (M-03…M-06),
`docs/design/DESIGN_PROPOSALS.md` (P3: Farbwechsel bei z = 34, LED-Tropfen an der Kante).

Lage im Kopf P3 (aus M-03/Kap. 2A, **ANNAHME** bis CAD): Dichtzone/Sondenübergang z ≈ 0–5, Zelle/Halter
Keystone 3034 z ≈ 5–25.5, Querrippe z ≈ 25.5, Elektronikband z ≈ 28–33, **Farbfuge z = 34**, Antenne z ≈ 35–41,
Taste oben. Die Hülse (grau) deckt also nicht nur die Zelle ab, sondern auch das Elektronikband.

## Quellen (extern)

- ANSI/UL 4200A-2023, Änderungsübersicht Intertek „UL 4200A SUN Rev 8-15-2023 and 8-30-2023“, S. 2–5
  (https://intertek.com/siteassets/resources/sun/2024/ul-4200a-sun-rev-8-15-2023-and-8-30-2023-ed-3-19-2025.pdf,
  Abruf 2026-11-07; Normtext selbst nicht lokal, nur Auszug):
  - 5.5 a) Werkzeug (Schraubenzieher, Münze); bei Schraube oder Drehdeckel **≥ 0.5 Nm und ≥ 90°**
    Drehung zum Öffnen **oder ≥ 2 volle Gewindegänge** im Eingriff.
  - 5.5 b) **mindestens zwei unabhängige, gleichzeitige Bewegungen**; diese dürfen sich **nicht zu einer
    einzigen Bewegung mit einem einzigen Finger** kombinieren lassen.
  - 5.6 Schrauben **unverlierbar** an Deckel, Abdeckung oder Gerät.
  - 6.3.4A/B Ist irgendein Teil des Fachgehäuses mit Daumen und Zeigefinger oder mit den Zähnen greifbar:
    Drehtest **0.50 Nm**, Zugtest **72.0 N** (ASTM F963). 6.3.4C Drucktest **136 N**.
  - 7A Warnhinweise und Symbole müssen „prominent, legible, easily discernible … and permanently marked“ sein.
    Kap. 7B Verpackung, 7C Produkt, 9 Anleitung (Details nur in der Norm).
- 16 CFR 1263.3 verweist für Konsumprodukte vollständig auf ANSI/UL 4200A
  (https://www.law.cornell.edu/cfr/text/16/1263.3, Abruf 2026-11-07).
- Sekundärquelle (Seminarfolien „Breaking down Reese's Law“,
  https://pubsumbracoweb.azurewebsites.net/media/23088/breaking-down-reeses-law-webinar-slides.pdf, laut
  Suchergebnis, nicht lokal geprüft): kleines Icon bei kleiner Produktfläche (min. 7 × 9 mm); wenn
  Produktkennzeichnung nicht praktikabel: volle Warnung auf der Verpackung oder Anhänger/Aufkleber am Produkt.
  Weitere Zusammenfassungen: Produktwarnung „if practicable“, Verpackung und Anleitung immer.
  **ANNAHME** bis zum Normtext 7C. Wortlaut von 7C in Phase 4 am UL-Lesezugang prüfen.

Einordnung: fluidi ist Eigengebrauch ohne Inverkehrbringen, UL 4200A/Reese's Law gelten rechtlich nicht.
Das Projekt hat sie in REQ-SAF-CC-04 aber als Massstab festgelegt. Entscheidend ist der Haushalt: Topfpflanzen
stehen in Reichweite von Kindern und Haustieren, und eine verschluckte CR2032 ist eine schwere Verletzung.

## 1 REQ-SAF-05 (getrenntes Fach, Flutungstest)

**Urteil: erfüllbar ohne Anforderungsänderung, aber nur mit fester Innenstruktur.** Wenn man die Hülse
abzieht, darf nur das Zellfach offen sein. Der Elektronikraum und der Sondenübergang bleiben dauerhaft zu.

Mindestmassnahmen:
1. **Fester Innenrahmen bzw. Schott (kritisch):** Kappe, Platine und Innenrahmen bilden eine dauerhaft
   verklebte bzw. vergossene Einheit. Das obere Schott (Querrippe nach M-03, z ≈ 25.5) trennt das Zellfach
   vom Elektronikband. Das Elektronikband z ≈ 26–34 liegt **innerhalb des festen Teils** (Innenrahmen oder
   Kappe). Die graue Hülse darf dort nur eine äussere Sichtschale sein. Alternativ legt man die echte Trennung
   (Fuge) auf die Höhe des Schotts (Fuge bei z ≈ 26, blaues Band grösser). Wo die Fuge optisch liegt, ist
   frei. Sicherheitlich zählt nur, dass beim Öffnen kein Bauteil des Elektronikraums frei liegt.
2. **Unterer Kragen am Sondenübergang (kritisch):** Ein Vergusskragen auf der Platine (z ≈ 0–5) ist die
   Sondendichtung und wird nie gelöst (REQ-MECH-15). Die Hülse dichtet nur **gegen den Kragen** (O-Ring oder
   Lippe), nicht direkt gegen die Sonde.
3. **Zellfach = Hülse + zwei lösbare Dichtungen** (oben gegen den Innenrahmen, unten gegen den Kragen).
   Die Platinenkanten werden im Bereich der Schotts umlaufend eingegossen (Docht entlang der Glasfaser).
4. Im Zellfach gilt beidseitig weiterhin: keine Vias, kein freies Kupfer ausser Minuspad/Clip und den
   UART-Pads (A-32-Auflage 2, R2-A3). Sondenleitungen im Fachbereich nur auf Innenlagen.
5. **LED-Tropfenfenster:** Liegt es in der abnehmbaren Hülse, braucht der Innenrahmen dahinter ein
   geschlossenes, transluzentes Fenster. Ein offener Durchbruch zum Elektronikraum ist nicht zulässig.
6. Flutungstests nach REQ-SAF-05 bleiben unverändert machbar (Zellfach: Hülse mit Wasser montiert;
   Elektronikraum: Prüfmuster mit Füllbohrung).

**Ersatzlösung „Elektronik vergossen statt getrennt“:** Das ginge nur mit einer Anforderungsänderung
(Freigabe Auftraggeber). Sicherheitlich vertretbar wäre allenfalls ein **vollständiger Verguss** des
Elektronikbands (≥ 1 mm über allen Bauteilen und Leitungen, Antenne ausgenommen) mit Flutung des gemeinsamen
Raums für 24 h mit eingesetzter Zelle. Nachteile: Antennenverstimmung, Tastenmechanik, LED, keine Reparatur.
**Conformal Coating allein ist kein Ersatz** (Poren, Kanten, keine Prüfbarkeit im Selbstbau). Empfehlung:
keine Änderung, Lösung mit Schott (Punkt 1).

## 2 Verschluckschutz REQ-SAF-CC-04

**(a) Schraube von unten: erfüllt den Massstab unter Bedingungen (bevorzugt).**
- Die Schraube ist unverlierbar (UL 4200A 5.6): Gewinde in der Hülse einmal durchgedreht oder O-Ring am Schaft.
- Öffnen nur mit Schraubenzieher oder Münze. Dazu ≥ 2 volle Gewindegänge im Eingriff **oder** ≥ 0.5 Nm und
  ≥ 90° (5.5 a). Bei FDM-Gewinde direkt im ASA ist das nicht dauerhaft → Gewindeeinsatz aus Messing oder
  Edelstahl im **festen Teil** (Kragen bzw. Innenrahmen), Schraube aus Edelstahl A2/A4 (Lage nahe Erde).
- Schraube und Einsatz liegen **ausserhalb des Zellfachs** oder hinter einer Kunststoffwand. Kein Metall darf
  Zelle, Clip oder Minuspad berühren können (Kurzschluss, A-32-Auflage 1–3). Der Schraubkanal ist gegen das
  Fach gedichtet (O-Ring unter dem Kopf oder Sackloch). Er führt nicht durch die Platine (Dichtzone, M-05).
- Wenn man den Sensor beim Einstecken an der Hülse hält, drückt das die Hülse in Öffnungsrichtung. Die Hülse
  muss deshalb auf dem Kragen aufsitzen (Kraftfluss Hülse → Kragen → Platine), nicht über die Schraube.

**(b) Klick mit zwei Rastnasen: nur bedingt zulässig.**
Zwei gegenüberliegende Nasen, die man mit Daumen und Zeigefinger einer Hand zusammendrückt, sind nach dem
Wortlaut zwei Bewegungen mit zwei Fingern. Ein Kind kann die Hülse aber genauso greifen und dabei unbeabsichtigt
beide Nasen drücken. Bedingungen:
- Jede Nase allein gibt nicht frei. Die Nasen liegen versenkt, sodass kein einzelner Finger und keine
  einzelne Handfläche beide zugleich trifft. Sie liegen nicht in der Griffzone, mit der man den Kopf beim
  Einstecken und Herausziehen hält.
- Prüfung nach 6.3.4A/B/C: 0.5 Nm, **72 N Zug an der Hülse**, 136 N Druck, Falltest 1 m – nach
  **Lagerung bei 65 °C** (RB-03; ASA-Schnapphaken kriechen) und nach **10 Wechselzyklen** (Ermüdung
  FDM-Haken). Die Dichtkraft darf nicht über die Rasten laufen (radialer O-Ring).
- Alles zusammen ist schwerer nachzuweisen als (a). Empfehlung: **(a)**. (b) nur, wenn der Auftraggeber
  Werkzeugfreiheit ausdrücklich will und die Prüfungen am Muster bestanden sind (PROTOTYP-PRÜFUNG).

## 3 Warnhinweis ohne Aussenaufdruck

UL 4200A verlangt eine Produktkennzeichnung, wo sie praktikabel ist. Bei kleinen Flächen gibt es ein kleines
Icon. Ist auch das nicht praktikabel, genügen nach Sekundärquelle Verpackung oder Anhänger. Eine Verpackung
im Laden gibt es bei fluidi nicht. Ausreichend für den Eigengebrauch ist deshalb:
1. **Warnsymbol innen**, dauerhaft (erhaben bzw. vertieft gedruckt, ≥ 7 × 9 mm, falls Platz, sonst so gross
   wie möglich). Es sitzt an einer Stelle, die beim Öffnen **zwangsläufig** sichtbar wird: auf dem Innenrahmen
   neben dem Clip oder innen in der Hülse an der Öffnung. Text „CR2032 – Kinder: Verschluckgefahr“. Damit
   erreicht der Hinweis genau den Moment des Zellwechsels, und darum geht es dem Normzweck.
2. **Anleitung** (REQ-DOC): Warnung nach 16 CFR 1263/UL 4200A Kap. 9 sinngemäss: Zellen ausser Reichweite von
   Kindern, Altzellen sofort entsorgen, Fach immer vollständig schliessen, nicht schliessende Hülse →
   Zelle entfernen, Arzt sofort bei Verdacht.
3. Optional ein kleines Icon unten auf der Hülsenstirn neben der Schraube (im Stand nicht sichtbar).
   Empfohlen, nicht zwingend.
4. Ersatzzellen in kindergesicherter Originalverpackung aufbewahren (Anleitung).

REQ-SAF-CC-04 „Warnsymbol am Batteriefach“ ist mit Punkt 1 wörtlich erfüllt (das Fach ist innen).
Keine Anforderungsänderung nötig.

## 4 Weitere Risiken des Prinzips

| Risiko | Bewertung | Massnahme |
|---|---|---|
| Zelle fällt beim Abziehen heraus bzw. wird von der Hülse mitgeschleppt (A-32-Auflage 4: Noppe hielt bisher frontal) | wichtig | Einschubrichtung des Clips so wählen, dass die Hülse beim Abziehen die Zelle **in** den Clip schiebt (Richtung im 3034-Massbild prüfen, **ANNAHME**). Haltenoppe mit Einlaufschräge, die erst in Endlage drückt. Test: Hülse ab, Kopf nach unten, schütteln → Zelle bleibt. Eine lose Zelle rollt weg und wird verschluckt. |
| Kurzschluss beim Öffnen | klein | Hülse aus ASA, nicht leitend. Risiko ist ein Metallwerkzeug zum Heraushebeln (Clip + / Pad −). Griffkerbe für den Fingernagel, Anleitung „kein Metallwerkzeug“. Schraube und Einsatz ausserhalb des Fachs (Kap. 2a). |
| Wasser in der Farbfuge läuft zur Zelle | wichtig | Dachziegelprinzip: Der obere (blaue) Teil überlappt den unteren aussen, keine nach oben offene Fuge. Erste Dichtung direkt hinter der Fuge. Leckt sie, darf Wasser nur ins Zellfach gelangen, nie ins Elektronikband (Kap. 1, Punkt 1). Untere Dichtung: Tropfkante, weil 5 mm über der Erde mit stehendem Giesswasser und Schmutz zu rechnen ist. FDM-Naht (Z-Seam) nicht in die Dichtfläche legen. REQ-MECH-13 mit eingesetzter Zelle nach 10 Wechselzyklen (PROTOTYP-PRÜFUNG). |
| Schmutz und Abrieb an der Sonde beim Abziehen über 100 mm | klein (Sicherheit), wichtig (Funktion) | Wechsel nur mit gereinigter Sonde (Anleitung). Hülsenöffnung mit Spiel, Dichtung erst am Kragen. Die Sondenbeschichtung darf nicht schleifen. |
| Dummy-Zellen-Adapter | klein | Barrieren unverändert (Zelle und Adapter schliessen sich im Clip aus, 2 × 100 kΩ im Elektronikraum, R2-A2/A3). Neu: Mit abgezogener Hülse liegen UART-Pads und Clip frei. Fremde UART-Adapter bei eingesetzter Zelle sind durch 2 × 100 kΩ abgedeckt (Kap. 2.7). Der Adapter muss ohne Hülse passen und darf das Schott nicht belasten. |
| Hülse lässt sich ohne Zelle nicht schliessen bzw. schliesst ohne Dichtung | klein | O-Ring unverlierbar in der Nut. Anleitung: Sichtkontrolle des O-Rings. |

## 5 Ergebnis

**Zulässig unter Bedingungen. Kein VETO.** Die Bedingungen K-1/K-2 sind Konstruktionsvorgaben. Eine
Freigabe von Layout oder Fertigung ohne sie gilt als kritischer Befund (REQ-SAF-04).

| Nr | Stufe | Bedingung |
|---|---|---|
| S3-K1 | kritisch | Fester Innenrahmen bzw. Schott: Beim Öffnen liegt nur das Zellfach frei. Elektronikband, LED, Taste und Antenne bleiben dauerhaft abgedichtet (Fuge auf Schotthöhe oder Hülse dort nur Sichtschale). |
| S3-K2 | kritisch | Sondendichtung als fester Vergusskragen. Die Hülse dichtet gegen den Kragen, nie gegen die Sonde. Die Kragendichtung wird beim Wechsel nicht berührt (REQ-MECH-15). |
| S3-W1 | wichtig | Verschluss nach UL 4200A 5.5/5.6: bevorzugt unverlierbare Edelstahlschraube in Metalleinsatz im festen Teil, ≥ 2 Gänge, ausserhalb des Zellfachs. Klick nur nach bestandenen Prüfungen 6.3.4A–C nach 65 °C und 10 Zyklen. |
| S3-W2 | wichtig | Die Zelle bleibt beim Abziehen sicher im Clip (Einschubrichtung, Noppe mit Einlaufschräge); Schütteltest. |
| S3-W3 | wichtig | Fuge im Dachziegelprinzip, zwei lösbare radiale Dichtungen. Spritzwasser- und Flutungstest nach 10 Wechselzyklen. |
| S3-W4 | wichtig | Warnsymbol innen, dauerhaft, beim Öffnen zwangsläufig sichtbar. Warnungen in der Anleitung. Wortlaut UL 4200A 7C/9 in Phase 4 am Normtext prüfen. |
| S3-L1 | klein | Kein Metallwerkzeug (Griffkerbe), O-Ring unverlierbar, Sonde vor dem Wechsel reinigen. Optional ein kleines Icon unten auf der Hülse. |

Für den Testplan (REQ-DOC-03), alles PROTOTYP-PRÜFUNG: Flutung Zellfach bzw. Elektronikraum 24 h mit
Zellstrom (REQ-SAF-05) nach 10 Wechselzyklen; REQ-MECH-13 mit Zelle; Falltest 1 m geschlossen; 72 N Zug und
0.5 Nm Drehung an der Hülse sowie 136 N Druck, jeweils nach 65 °C Lagerung; Schütteltest mit offener Hülse;
Schraubenauszug bzw. Gewindegänge; Prüfung der A-32-Auflage 3 mit montierter Hülse.
