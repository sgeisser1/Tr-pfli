# Phase 5 – Sicherheitsprüfung Runde 3 (Anleitungen, Adapter-Mechanik, Kappe P5, Gateway-RTC)

| | |
|---|---|
| Prüfer | Sicherheits-Agent (frischer Kontext) |
| Datum | 2026-11-08, Stand git `cedccd5` |
| Geprüft | `docs/manuals/MONTAGE_SENSOR.md`, `docs/manuals/BATTERIEWECHSEL.md`, `docs/manuals/BESTELLEN_JLC.md`, `hardware/programmer/README.md` Kap. 4/8 (PA-1), `docs/reviews/phase5_checkliste_mechanik.md` (P5-M1…M6), `mechanical/sensor/check_sensor.txt`, `mechanical/gen/fluidi_params.py` (SCREW), `mechanical/gen/fluidi_sensor.py` Z. 130–131, 262–265, `mechanical/gen/fluidi_gateway_pi.py`, `mechanical/gateway_pi/check_gateway_pi.txt`, `hardware/gateway/BOM_GATEWAY.csv`, `docs/datasheets/INDEX.csv` (MECH-SCR1, GW-RTC*), `docs/appnotes/Renata_3VLithium_SafetyGuidelines.pdf` |
| Nachgeführt | `phase5_fmea_light.md` (F-07, F-12, F-13, F-20…F-26, neu F-28, F-48, F-49, F-64…F-66, Zusammenfassung), `phase5_checkliste_sicherheit.md` (K-01, K-05, K-07, M-07, M-08, CK-W1, CK-W3), `phase5_testplan_beitrag_sicherheit.md` (ST-K8, ST-W6, ST-G2/G3, ST-P1 erweitert) |
| Ergebnis | **0 kritisch, 4 wichtig, 5 klein. Kein Veto.** PS-W1: Konzept „Bügel + unverlierbare Schwinge“ **unter Auflagen akzeptiert**, Freigabe Weg A weiter erst nach ST-P1. |

## 1 Anleitungen

**BATTERIEWECHSEL.md** erfüllt REQ-SAF-DOC-01 (Verschlucken, Lagerung in Originalverpackung, Abkleben, Entsorgung,
Wasser im Kopf, kein Metallwerkzeug, Kinder/Haustiere, Pflichtkontrolle Hülse). Die Aussagen decken sich mit
`Renata_3VLithium_SafetyGuidelines.pdf` (Rev. 10/02, S. 1). Polung (Pluspol nach vorne, Einschub von rechts) stimmt mit
`MONTAGE_SENSOR.md` Kap. 7.1 und `fluidi_params.py` (Einschub +x) überein. **FMEA F-23 288 → 144**, CK-W1 erledigt.

**MONTAGE_SENSOR.md**: Reinigung K-5, eine Vergussmasse K-4, „ohne Datenblatt kein Verguss am Serienteil“, Prüfung 7
(Pflicht, F-21/F-62), Schutzausrüstung für Epoxid, Zelle erst nach dem Programmieren. In Ordnung bis auf R3-W1, R3-K4.

**BESTELLEN_JLC.md**: Stopp-Regel POFV (A-2), Abhakliste ORDER Kap. 5 mit Q1 (Verpolschutz, Zeile 121) und U1-180°-Kurzschlussfall,
Prüfung der Produktionsdatei (Lage `sk`, 8 VIP inkl. Minuspad, TP1, TP2). Sicherheitlich vollständig bis auf R3-K5.

## 2 Entscheid PS-W1 (Programmieradapter, PA-1)

**Entscheid: Die Konstruktion „Bügel fest am Dummy, Stiftträger als unverlierbare Schwinge, Gegenhalter schliesst erst
in Endlage“ erfüllt PS-W1 / R2-A2 – unter den Auflagen A1–A5.** Die zweiteilige Alternative (Stiftträger auf Zapfen
stecken) ist **abgelehnt**.

Begründung: Schutzziel von R2-A2 ist nicht „ein Werkstück“, sondern dass (1) die Programmierkontakte nur wirken können,
wenn der Dummy den einzigen Clip belegt, und (2) es keine losen Teile gibt, mit denen man Stifte und Speisung getrennt
ansetzen kann. Eine unlösbare Baugruppe mit Zwangsfolge erfüllt beides. Die Schwinge ist nötig, weil ein starrer Stift
auf Pad-Höhe beim Einschieben über den Clipkörper läuft (README Kap. 4, Geometrie Clip y bis 2.5, Pads y 6.6). Die
Federkraft geht über Platine und Gegenhalter, nicht über Schott oder Zelle.

| Auflage | Inhalt |
|---|---|
| A1 | Bügel mit dem Dummy **verklebt und verstiftet**; Schwingenachse ohne Werkzeug nicht lösbar (eingepresst oder verklebt, **keine Rast-/Schnappverbindung**). |
| A2 | Gegenhalter ist Teil der Baugruppe (an Schwinge oder Bügel unverlierbar), kein loses Teil. |
| A3 | Zwangsfolge geometrisch: Die Schwinge kann erst schliessen, wenn der Bügel an der Platinenkante (Dummy in Endlage) anliegt. Ruhelage per Feder **offen**; in Offenstellung ≥ 1 mm Luft Stift ↔ Clip, Schwinge an der Clipseite isolierend. |
| A4 | Mit eingesetzter CR2032 lassen sich die Stifte nicht auf TP1/TP2 bringen, und der Dummy kann Zelle bzw. Clip nicht berühren (Bügel stösst an die Zelle). |
| A5 | Litzen von Dummy und Stiften gemeinsam zugentlastet an der Baugruppe; keine Steckverbindung zwischen Dummy und Stiftträger. |

Nachweis: ST-P1 (a)–(g) im Testplan (erweitert). Weg A bleibt bis dahin **nicht freigegeben**; F-07 unverändert RPZ 90.

## 3 Befunde

### Wichtig

**R3-W1 · wichtig · F-20/F-21 – Schraube ist nur bedingt unverlierbar, Anleitung führt zum Herausdrehen.**
ISO 7045 M2 × 3 ist vollgewindig. Furchlippe Ø 1.7 im Hülsenboden z 0…0.5 (`fluidi_sensor.py` Z. 265,
`fluidi_params.py` SCREW LIP_H 0.5), Mutter z 1.6…3.2, Schaft z 0…3.0 (`check_sensor.txt` 5c). Nach 1.4 mm
(3.5 U) ist die Schraube aus der Mutter; ihr Gewinde steckt dann noch in der Lippe (Schaft z −1.4…1.6). Erst nach
weiteren ≈ 1.6 mm (≈ 4 U, eigene Rechnung, P 0.4) fällt sie heraus. Sie „dreht“ also nie „frei“.
`BATTERIEWECHSEL.md` Schritt 2 („lösen, bis sie frei dreht. Sie bleibt in der Hülse“) und `MONTAGE_SENSOR.md` 7.4
(„danach unverlierbar“) lassen den Nutzer weiterdrehen → Schraube lose, Sensor danach ohne Schraube (F-21), Kleinteil.
Vorschlag: Schritt 2: „Schraube etwa 4 Umdrehungen lösen, bis sich die Hülse abziehen lässt. Nicht weiter drehen, sonst
fällt die Schraube heraus. Fehlt die Schraube: Sensor nicht benutzen, Ersatzschraube einsetzen.“ Ersatzschraube je
Muster vorhalten. Test ST-K8 (Umdrehungen zählen, Lippe nach 50 Wechseln). Neu FMEA F-28 (RPZ 135 → 90).

**R3-W2 · wichtig · S3-K1, REQ-UI-06 – Membranklemmung ist nach P5-M3 die einzige Barriere oben, Befestigung offen.**
P5-M3 schliesst die Senkung (`check_sensor.txt` 12, 100 % Kunststoff) – richtig. Damit führt der Wasserweg von oben aber
nur noch über den Membranrand → Senkungsgrund → Führungsrohr Ø 3.2 (Stössel) in den Elektronikraum. Die Dichtung hängt
an der Klemmung durch den Klemmring, deren Befestigung „Presssitz/Kleber nicht festgelegt“ ist (`MONTAGE_SENSOR.md` O-4,
Spiel 0.05 je Seite). Giesswasser trifft genau diese Stelle. Vorschlag: O-4 vor dem Musterbau festlegen (Klebung des
Klemmrings rundum, Kleber mit Datenblatt, oder Presssitz mit Nachweis), Prüfung 3 der Montage um „Membran rundum
geklemmt“ ergänzen, Test ST-W6 (a). FMEA F-65 (RPZ 168).

**R3-W3 · wichtig · S3-K1 – Zapfenwand 0.54 mm zwischen O-Ring-Nut und Elektronikraum.**
`check_sensor.txt` 9 (z 32.5/33.0: Wand min 0.54) und `PRINT_SETTINGS.md` („dünnste Zapfenwand 0.54 mm hinter den
hinteren Nutecken“). Über dem Schott (z 30.8…32.0) trennt diese Wand die nasse Nut vom Elektronikraum. Eine FDM-Wand aus
1–2 Bahnen ist nicht sicher dicht; der Schott-Verguss wird umgangen. Nicht neu in Phase 5, aber bisher nicht bewertet.
Vorschlag: für die Muster an dieser Stelle volle Füllung/Wandzahl vorschreiben (PRINT_SETTINGS), Test ST-W6 (b);
Rev D Wand ≥ 0.8 mm (2 Bahnen bei Düse 0.4, ANNAHME Düse). FMEA F-66 (RPZ 144).

**R3-W4 · wichtig · REQ-SAF-CC-04 sinngemäss, REQ-SAF-DOC-01 – Gateway-Knopfzelle CR1220 (Adafruit 4282).**
Positiv: kein Ladepfad (F-45, eigene Schaltplanprüfung Runde 2), Deckel nur mit Werkzeug (4 × M2.5 × 8 ISO 7380
Innensechskant von unten, `fluidi_gateway_pi.py` Z. 32/213). Offen: CR1220 ohne Hersteller und Datenblatt (INDEX
GW-RTC-CELL, BOM G5), RTC sitzt oben im Deckel bei ΔT 11–34 K (`check_gateway_pi.txt` 8, ANNAHME), Modul in den Rahmen
geklebt (Z. 244), Lage des Zellhalters zur Klebefläche nicht festgelegt, `GATEWAY_SETUP.md` enthält nichts zur Zelle.
Auflagen:
- **G-R1** Marke festlegen (z. B. gleicher Hersteller wie CR2032), Datenblatt nach `docs/datasheets/`, Temperaturbereich gegen ST-G2 (Thermoelement an der Zelle) prüfen.
- **G-R2** Modul so kleben, dass die Zelle ohne Lösen der Klebung wechselbar ist und **nicht gegen den Deckel gepresst** wird (keine mechanische Last auf die Zelle); Zelle zeigt zum Gehäuseinneren, Halter hält sie bei kopfüber gehaltenem Deckel (ST-G3).
- **G-R3** `GATEWAY_SETUP.md`: Abschnitt „RTC-Zelle“ mit Verschluckwarnung, Polung laut Halter, Lagerung/Entsorgung wie `BATTERIEWECHSEL.md`, Gateway nur geschlossen betreiben, Wechselintervall.
- **G-R4** Nur Original Adafruit 4282 (F-45: bei Typwechsel neue Prüfung).
- **G-R5** Litzen nur an die Pins, die das Modul braucht (Versorgung, SDA, SCL, GND; Zuordnung am Schaltplan bzw. `Adafruit_AddingRTC-RaspberryPi_Guide_2026-04-07.pdf` prüfen, von mir nicht pinweise verifiziert). +5 V ist laut Schaltplanauswertung nicht mit IC2 verbunden (`Adafruit_4282_PiRTC-DS3231_Produktseite_Auszug_2026-11-08.txt` Z. 5) → nicht anschliessen.
FMEA F-48 (144), F-49 (126).

### Klein

| Nr | Befund | Vorschlag |
|---|---|---|
| R3-K1 | `BATTERIEWECHSEL.md` nennt bei Verschlucken nur „ärztliche Hilfe“, keine Nummer. | „Notruf 144, Tox Info Suisse 145 (24 h)“ ergänzen; Quelle als Auszug nach `docs/references/` (Websuche 2026-11-08: toxinfo.ch). |
| R3-K2 | Aufstellort fehlt: Renata S. 1 „Do not expose batteries to high temperatures, moisture or direct sunlight“; FMEA F-12. | Satz „Nicht auf Heizkörper oder in pralle Sonne stellen“. |
| R3-K3 | Schritt 7 „kein Signal“ nennt nur die Bootloader-Falle, nicht die verpolte Zelle; kein Hinweis zu beschädigten/ausgelaufenen Zellen. | „Polung prüfen (Pluspol vorne)“; „Zelle mit Flecken, Beulen oder ausgelaufener Flüssigkeit nicht einsetzen, Hautkontakt vermeiden, Hände waschen“. |
| R3-K4 | `MONTAGE_SENSOR.md` Kap. 6 verlangt Weg A, der noch nicht freigegeben ist (PS-W1/ST-P1); Isopropanol ohne Hinweis auf Entzündlichkeit. | „Weg A erst nach ST-P1, bis dahin Weg B mit Dummy-Scheibe nach PROGRAMMIEREN Kap. 5“; Tabelle Kap. 1: „Isopropanol leicht entzündlich: lüften, keine offene Flamme, Lötkolben aus“. |
| R3-K5 | `BESTELLEN_JLC.md` Schritt 13 nennt „Verpolschutz“ nur als Stichwort. | Auf ST-E2 verweisen: vor der ersten Zelle Labornetzteil 3.0 V / 10 mA, richtig und verpolt. |

## 4 Kappe Phase 5 (Frage 4) – Bewertung

| Änderung | Sicherheitsfolge | Bewertung |
|---|---|---|
| P5-M1 Trichter 45°, Kappe 1 Körper | Ohne Korrektur wäre der Elektronikraum nicht geschlossen (S3-K1). Jetzt 1 Körper (`check_sensor.txt` 11). Zapfenwand bleibt 0.54 mm → R3-W3 | positiv; PROTOTYP-PRÜFUNG ST-W1/W3/W6 |
| P5-M3 Senkung dicht | Leckpfad am Membranrand geschlossen; Dichtung hängt jetzt an der Klemmung → R3-W2 | positiv, Folgepunkt O-4 |
| P5-M2 Tastermechanik | Kein Kraftfluss über die Zelle (Taste → Zunge → SW1). Klemmender Taster → F-14/F-16 (Bootloader beim Zelleinsetzen); Anleitung warnt in Schritt 4/6. Zunge SF 1.34 worst: Bruch = Funktionsausfall, keine Gefahr | ohne neuen Befund; M-T1/M-T4 |
| Schraube M2 × 3 statt M2 × 4 (V-K) | 3.5 Gänge ≥ 2 (Massstab S3-W1); Spitze 0.2 mm unter Mutteroberkante, 0.3 mm zur O-Ring-Nut (`check_sensor.txt` 5c) – kein Eingriff in die Dichtung | Kindersicherung unverändert; Verliersicherheit → R3-W1 |
| Batteriefach/Kindersicherung | Hülse, Schraube, Warnsymbol, Ausschub 2.4 mm in der Hülse (`check_sensor.txt` 4) unverändert | keine Verschlechterung |

## 5 Antwort an die Ersteller

Bitte je Befund *umgesetzt* / *abgelehnt (Grund)*: R3-W1, R3-K1…K4 → Projektleitung/Anleitungen; R3-W2, R3-W3 →
`mechanik`; R3-W4 (G-R1…G-R5) → `gateway`/`mechanik`/Projektleitung; PS-W1-Auflagen A1–A5 → `mechanik` bei PA-1.

## Nachtrag (2026-11-08): Entscheid WS-13 – Quelle an TP1/TP2 im Test ST-Z5 / PT11.06

**Entscheid: ST-Z5 bleibt als ausdrückliche, einzige Ausnahme von Regel 1** (`PROGRAMMIEREN_SENSOR.md` Regel 1,
Elektronik-Grundregel, ENERGIEMESSUNG). Der Test ist der einzige Nachweis der Rückstrombarriere (REQ-SAF-CC-03,
R2-A4, FMEA F-05). Ohne ihn bleibt die SPICE-Rechnung (`simulation/spice/README.md` (c): ≤ 45.9 µA je Pad bei 5.5 V und
überbrücktem R) unbestätigt. Regel 1 gilt unverändert für Programmieren, Energiemessung und jeden anderen Betrieb.

Bedingungen (alle Pflicht):

| Nr | Bedingung |
|---|---|
| Z5-1 | Nur an den von der Projektleitung bestimmten Prüfmustern, nur durch den benannten Prüfer, auf nicht brennbarer Unterlage, beaufsichtigt. Nicht zusammen mit Programmieren oder Energiemessung. |
| Z5-2 | Quelle = Labornetzteil, Strombegrenzung **≤ 1 mA** vor dem Anschliessen eingestellt und am offenen Ausgang kontrolliert (Faktor ≥ 10 unter der Ladegrenze 10 mA, Maxell S. 2; Faktor ≈ 20 über dem Erwartungswert). Strommessung in der Pad-Leitung. |
| Z5-3 | Zellstrom nur über den Mess-Zwischenadapter (Shunt/Amperemeter), keine Quelle in Serie zur Zelle. |
| Z5-4 | **Fall „Zelle 0 V“ ohne Zelle:** Clip-Kontakte über den Shunt verbinden (misst denselben Strom ohne Ladegefahr). Fall „entladene Zelle“ nur mit Zelle **2.0–2.6 V** (keine Zelle < 2.0 V, keine beschädigte Zelle). |
| Z5-5 | Dauer je Fall ≤ 10 min (ANNAHME; bei 55 µA ≈ 9 µAh, < 0.01 % der Kapazität). |
| Z5-6 | Abbruch: Pad-Strom > 100 µA **oder** Strombegrenzung des Netzteils spricht an **oder** Erwärmung/Geruch/Aufblähen; dann Quelle zuerst abklemmen, Zelle danach entfernen. |
| Z5-7 | Überbrückung des 100-kΩ-Widerstands nur als Draht für den Test, nach dem Test entfernen und per Foto/Widerstandsmessung (≈ 200 kΩ) nachweisen; Muster als „Fehlertest“ kennzeichnen. Zellen aus dem Test entsorgen. |

Textvorschlag für Regel 1 (Projektleitung): „… keine Speisung über TP1/TP2. Einzige Ausnahme: Sicherheitstest
PT11.06/ST-Z5 nach den Bedingungen Z5-1…Z5-7 in `docs/reviews/phase5_sicherheit_runde3.md`.“
