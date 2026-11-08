# fluidi Sensor – Montage, Verguss und Batteriewechsel (mechanischer Teil)

| | |
|---|---|
| Stand | 2026-11-08, Phase 5, Gehäuse Rev C mit V-K/M-4 (D-019, D-023) und P5-M1/M2/M3; **Phase 6: Vergussmasse und Kantenversiegelung (Kap. 3a, 4, 5, 5a) nach `docs/concepts/vergussmasse_versiegelung.md` – Vorschlag, Freigabe offen** |
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
| O-1 | **Vergussmasse** (Kragen, Schott): Epoxid 2K, Tg ≥ 80 °C, *ein* Material für den ganzen Kragen (K-4) | **Vorschlag Electrolube ER2223** (Tg 140 °C, ungefüllt; `docs/concepts/vergussmasse_versiegelung.md`, INDEX.csv EP-K). **Freigabe offen:** Abweichung von K-4 „mineralisch gefüllt“ (F-1, Sicherheit), Kosteneinordnung (Orchestrator). Bis zur Freigabe nur Vorversuche V-1 … V-3 (Kap. 3a), **kein Verguss an Mustern**. Ohne Datenblatt und SDB keine andere Masse verwenden. |
| O-2 | **Kantenversiegelung der Sonde** (REQ-MECH-07) | **Vorschlag:** ER2223 nur auf Schnittkante und Spitze, Flächen frei (Kap. 5a; Feldsimulation `simulation/field/results/coat_epoxy.txt`). Freigabe wie O-1 |
| O-3 | Klebstoff Lichtfenster | **ANNAHME** transparentes 2K-Epoxid oder UV-Kleber (PRINT_SETTINGS Kap. 5) |
| O-4 | Klemmring (Pos. 6): **Presssitz** 0.05 je Seite in der Senkung Ø 6.4, Schürze verpresst die Membran um 0.1 mm (20 %) – Phase 5 R3-W2 (`check_sensor.txt` 2e) | Auszugskraft und Dichtheit am Muster: PROTOTYP-PRÜFUNG ST-W6 (a), M-W3; Klebung nur, wenn ein Kleber mit Datenblatt gewählt ist |
| O-5 | Tastermechanik (P5-M2, Runde 2): 60°-Keil am Finger auf einer Nase der Zunge in Höhe SW1, Führungsrippe und D-Bohrung gegen Verdrehen. SW1 schaltet im CAD nominal bei 0.3 mm Tastenhub, worst bei 0.65 mm (Reserve +0.17); Tastenkraft nominal ≈ 8 N, worst ≈ 12 N (+ Membran, μ 0.3 ANNAHME) (`check_sensor.txt` 2a–2e) | **Überlast:** nach dem Schalten trägt SW1 die Tastenkraft; bei 20 N und μ ≥ 0.3 Zunge SF ≥ 1.15, bei kleinerer Reibung < 1 → PROTOTYP-PRÜFUNG M-T2; Taste nicht mit Kraft drücken |
| O-6 | Anzugsmoment Schraube M2 × 3 in ASA/Mutter | nicht festgelegt; „handfest mit PH1“ (**ANNAHME**), am Muster prüfen (ST-K1) |

## 1 Teile, Werkzeuge, Hilfsstoffe

Teile: Pos. 1–17 laut Stückliste FL-S-00 (gedruckt nach `PRINT_SETTINGS.md`, Passproben vorher bestanden).

| Werkzeug / Hilfsstoff | Zweck |
|---|---|
| Kreuzschlitz-Schraubenzieher **PH1** | Schraube ISO 7045 M2 × 3 PH1 (Pos. 12) |
| Messschieber 0.01 mm | Distanzlehre, Passungen, Dicke Dummy-Zelle |
| Lupe ≥ 10× | Sichtprüfungen (VIP-Pads, Verguss, Lötstellen; ST-E1) |
| 2 × Distanzlehre 24.2 (FL-S-10) | Abstand Kragen ↔ Schott beim Kragenverguss |
| Isopropanol (**leicht entzündlich**: keine offene Flamme, Lötkolben aus, lüften), fusselfreie Tücher | Flussmittelreste im Kragenbereich entfernen (K-5) |
| 600er Schleifpapier | FDM-Naht auf den O-Ring-Gleitflächen der Hülse glätten (PRINT_SETTINGS Kap. 5) |
| Silikonfett | O-Ringe (Pos. 11) |
| Kapton-Punkt (Ø ≈ 3 mm) | Gewinde der Mutter vor Epoxid schützen (PCB_OUTLINE Kap. 7) |
| Dosierspritzen + Kanülen, Mischbecher, Waage | Verguss (Mengen siehe Kap. 4/5) |
| Vergussmasse **Electrolube ER2223, Resin Pack 250 g** (Vorschlag O-1), TDS und SDB A/B ausgedruckt am Arbeitsplatz | Schott, Kragen, Sondenkanten (Kap. 3a) |
| Einwegspritzen 1 ml und 3 ml Luer-Lock, stumpfe Dosierkanülen 18–20 G, feiner Synthetikpinsel (≤ 3 mm), Wattestäbchen, kleiner Spiegel | Dosieren, Kanten auftragen, Austritt kontrollieren |
| Einweg-Alu-Schale (≥ 15 × 10 cm), Schere, Unterlage (Karton/Folie) | Beutelrest flach aushärten lassen (Exothermie, Kap. 3a) |
| Wärmeschrank oder Filamenttrockner mit separatem Thermometer, einstellbar 60 °C (**ANNAHME** vorhanden) | Nachhärtung 4 h bei 60 °C (Kap. 3a) |
| Vakuumkammer (falls vorhanden) | blasenfreier Verguss (K-4), sonst kopfüber mit Entlüftung; bei ER2223 (800 mPa·s) nicht nötig |
| Nitrilhandschuhe (Einweg, **ANNAHME** Material: das SDB nennt nur „EN 374, Material nach Angabe des Handschuhherstellers“), **dicht schliessende Chemikalien-Schutzbrille (EN 166)**, langärmlige Kleidung | Epoxid: Härter B ist **ätzend (H314) und hautsensibilisierend (H317)**, Harz A reizend und sensibilisierend (Kap. 3a) |
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
2. **Stössel (Pos. 8)** von unten in die D-Bohrung des Führungsrohrs stecken (D-Fläche nach vorne, passt nur so),
   Finger links zwischen Führungsrippe (vorne) und Zungennase (hinten).
3. **Membran (Pos. 10)** flach auf den Grund der Senkung Ø 6.4 legen.
4. **Taste (Pos. 5)** mit dem Hals von oben durch den Klemmring (Pos. 6) stecken, **Tastenteller (Pos. 7)** von unten
   auf den Hals pressen. Die Einheit Taste + Klemmring + Teller in die Senkung setzen und den Klemmring (Presssitz) bis
   auf die Membran einpressen (flaches Werkzeug, gleichmässig, O-4).

**Prüfung 3:** Taste federt zurück (Membran), Stössel gleitet ohne Klemmen und lässt sich **nicht verdrehen** (C-1).
Membran rundum unter dem Klemmring geklemmt, Klemmring sitzt bündig und fest (R3-W2). Ohne Platine: beim Drücken bewegt
sich die Zunge sichtbar nach hinten (Nase), in Ruhe ist sie nicht vorgespannt. Fenster bündig, keine Kleberspuren.

## 3a Vergussmasse: Schutzmassnahmen, Sitzungsplan, Mischen, Aushärten (gilt für Kap. 4, 5, 5a)

Grundlage: `docs/references/Electrolube_ER2223_TDS_Rev4-2019-03.pdf` (TDS), SDB Teil A
`Electrolube_ER2223-PartA_SDS_Rev0-2016-10-19_EN.pdf` (Stand 2023: `…_Rev0.64-2023-10-27_SV.pdf`), SDB Teil B
`Electrolube_ER2223-PartB_SDS_2023-10-02_HU.pdf`. Auswahl und Begründung: `docs/concepts/vergussmasse_versiegelung.md`.
**Gilt erst nach Freigabe von O-1/O-2**; vorher nur die Vorversuche (unten).

**Gefahren (SDB):** Teil A (Harz, schwarz): Achtung – H315 Hautreizung, H317 kann allergische Hautreaktion verursachen,
H319 schwere Augenreizung, H411 giftig für Wasserorganismen (SDB A S. 1). Teil B (Härter): **Gefahr – H314 schwere
Verätzungen der Haut und schwere Augenschäden**, H302, H317, H318, H373 (SDB B S. 2). Gemischt bis zur Aushärtung wie A + B behandeln.

**Schutzmassnahmen (SDB A S. 6, SDB B S. 2/6, P280):**
1. Arbeitsplatz gut lüften, Unterlage auslegen, **kein Essen, Trinken, Rauchen**; Kinder und Unbeteiligte fernhalten.
2. Vor dem Öffnen des Beutels: **Chemikalien-Schutzbrille** (dicht schliessend, EN 166), Nitrilhandschuhe, lange Ärmel.
   Handschuhe nach Kontakt mit der Masse sofort wechseln, nicht mit Handschuhen ins Gesicht fassen. Wer bereits auf
   Epoxid allergisch reagiert, verarbeitet die Masse nicht (H317).
3. **Haut:** verunreinigte Kleidung ausziehen, Haut sofort mit viel Wasser und Seife waschen (kein Lösungsmittel, auch
   kein Isopropanol auf der Haut). **Augen:** sofort mehrere Minuten mit Wasser spülen, Kontaktlinsen entfernen, Arzt
   (SDB B S. 2, P305 + P351 + P338). **Verschlucken:** Mund ausspülen, **kein Erbrechen** herbeiführen, Arzt (P301 + P330 + P331).
   Notfall Schweiz: Tox Info Suisse **145**.
4. Isopropanol (Kap. 2/5) ist leicht entzündlich: Gebinde geschlossen und weg vom Wärmeschrank halten.
5. **Rest im Beutel nicht liegen lassen:** sofort nach dem Abfüllen den Beutelinhalt in die Alu-Schale ausdrücken und
   **flach (≤ 10 mm)** im gelüfteten Raum aushärten lassen. Grund: Ein 250-g-Paket erwärmt sich beim Aushärten selbst;
   das TDS gibt für ER2223 keine Exothermie an (**ANNAHME** flach ausgiessen; vgl. MG-TDS „Mixing > 500 g … flash cure“).
6. Entsorgung: ausgehärtete Reste, leere Beutel, Spritzen und Handschuhe erst nach vollständiger Aushärtung in den
   Kehricht (**ANNAHME**, Abschn. 13 der SDB beachten); **flüssige Reste nie in den Ausguss** (H411). Ungemischte
   Beutel bei der Sammelstelle für Sonderabfälle abgeben.

**Sitzungsplan:** Ein Beutel (250 g) wird immer ganz gemischt und ist **30 min verarbeitbar** (20 °C, TDS S. 1), Gelzeit
90 min. Bedarf je Sensor ≈ 0.2 g. Schott und Kragen brauchen getrennte Sitzungen (Schott muss hart sein, bevor der
Kragen gesetzt wird). Deshalb pro Beutel höchstens eine Gruppe von **≤ 8 Sensoren** (**ANNAHME**, Zeit pro Sensor beim
Vorversuch V-1 messen) und rollierend arbeiten: Sitzung 1 Schott Gruppe 1; Sitzung 2 Kragen + Kanten Gruppe 1 und Schott
Gruppe 2; usw. **Alles, was nicht mit Masse zu tun hat (Einspannen, Lehren, Kapton, Reinigen), vor dem Mischen erledigen.**

**Vorversuche vor dem ersten Muster (Beutel 1, PROTOTYP-PRÜFUNG, Konzept Kap. 12):** V-1 Vergussprobe Kragen und Schott
mit FR4-Reststreifen 1.6 mm (Füllung, Blasen, Austritt, Zeit pro Sensor), V-2 Haftprobe auf angerautem ASA, V-3 Härteprobe
(Becherrest 1 h bei 80 °C bleibt hart). Muster erst vergiessen, wenn V-1 … V-3 bestanden sind.

**Mischen (TDS S. 1–2, Resin Pack):**
1. Raum und Beutel 20–25 °C (Lagerung über 15 °C, TDS S. 1; kristallisierter Härter: Beutel bei 40 °C anwärmen, TDS S. 3).
   Ablaufdatum prüfen (Haltbarkeit 12 Monate).
2. Beide Endkappen abnehmen, Clip durch vorsichtiges Auseinanderziehen entfernen; Harz und Härter im Beutel **3–4 min**
   durchkneten, mit dem Clip das Material aus den Ecken streichen, bis die Farbe gleichmässig schwarz ohne Schlieren ist.
   Nicht von Hand Teilmengen abwiegen (Mischverhältnis 3.45 : 1 nach Gewicht ist im Beutel vorgegeben).
3. Eine Ecke abschneiden und sofort 3–5 Spritzen à 1–3 ml füllen (Kolben ziehen, Spritze von unten befüllen), Kanüle
   aufsetzen, Luft nach oben ausstossen. Den Rest sofort in die Alu-Schale (Schutzmassnahme 5). Uhrzeit notieren:
   **Ende der Verarbeitung = Mischzeit + 30 min.** Masse, die bereits zieht (Fäden, deutlich zäher), nicht mehr verwenden.

**Aushärten:** kopfüber im Halter **24 h bei 20–25 °C**, danach **4 h bei 60 °C** (TDS S. 1 „Cure Time (60 °C)“, S. 3
„post-cure … if required“) im Wärmeschrank/Filamenttrockner. Temperatur mit eigenem Thermometer prüfen, **nie über 65 °C**
(ASA, Fenster, Membran). **Zelle nie eingesetzt** (Kap. 4 Schritt 1). Die Nachhärtung entfällt nur, wenn Electrolube
einen Tg ≥ 80 °C nach Raumtemperatur-Härtung schriftlich bestätigt (offen). Erst danach Lehren entfernen, prüfen, weiter.

## 4 Platine einsetzen und Schott vergiessen (Pos. 9, 15, 16)

**Vor dem ersten Kappenverguss (Pflicht, Auflagen Red Team Runde 3, D-026):** (1) Tastenkraft bis zum Klick am
unvergossenen Kern messen (Gewichte/Kraftmesser): ≤ 12 N, über 15 N nicht vergiessen und melden (N-2, REQ-UI-05);
(2) Klemmring-Passprobe (Presssitz hält, Membran rundum verpresst) und Membranrand zusätzlich abdichten (W-1; Dichtmittel
nach Wahl der Mechanik, ANNAHME bis Datenblatt); (3) Gleitfläche der Nase nach dem Druck glätten (N-3);
(4) Farbeindringprüfung der Membranabdichtung an den ersten 3 Mustern (M-W3).

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

1. Sensor bleibt kopfüber eingespannt (Spitze oben). Sonde ist nach Kap. 5 Schritt 1 sauber und trocken.
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
- Messschieber: Sondenbreite an 3 Stellen 0.1 … 0.4 mm grösser als vor dem Versiegeln (Schicht 0.05 … 0.2 mm je Kante,
  **ANNAHME**). Flächen ausserhalb des 1-mm-Randes ohne Masse.
- Nur **ein** Muster (PROTOTYP-PRÜFUNG V-4): Kanten erst in der **nächsten** Sitzung versiegeln (Kragen dann schon hart).
  Vorher und nachher Messfrequenz in Luft und in Wasser notieren (Testfirmware, Zelle eingesetzt, Hülse montiert); vor
  der Nachhärtung 60 °C die **Zelle entnehmen**. Kriterium: Spanne um ≤ 3 % geändert. Dieses Muster hat am Übergang
  Kante/Hohlkehle eine Fuge „nass auf hart“ und ist für K-7 nicht repräsentativ.
- Kalibrierung (2-Punkt) und Vorkonditionierung (≥ 14 Tage wässern, `simulation/field/REPORT.md` Kap. 7) erst **nach**
  dem Versiegeln und Aushärten.

## 6 Programmieren

Nach Kap. `docs/manuals/PROGRAMMIEREN_SENSOR.md`, **Weg A** (Programmieradapter, Hülse abgezogen, Zugang zu TP1/TP2 im
Zellfach). Keine Zelle im Clip. Danach Dummy-Zelle entnehmen.

**Solange Weg A nicht freigegeben ist** (Test ST-P1, Sicherheitsauflagen PS-W1/A1–A5): Muster **vor dem Verguss**
nach Weg B (Kap. 5 der Programmieranleitung, nur mit Dummy-Scheibe) programmieren, d. h. diesen Schritt vor Kap. 5
dieser Anleitung ausführen (R3-K4).

## 7 Zelle einsetzen, O-Ringe, Hülse schliessen (Pos. 2, 11, 12, 17)

1. **Zelle (Pos. 17)** einsetzen: Pluspol zur Front (−y), von der offenen Clip-Seite (+x, von vorne gesehen rechts)
   flach einschieben bis zum Anschlag. **Taste dabei nicht berühren** (sonst startet der ROM-Bootloader, W-10).
   Erwartet: LED-Startsignal L11 (Grün 200 ms; Fehler Rot 3 × 100 ms; PROGRAMMIEREN Kap. 6/7).
2. **O-Ringe AS568-019 (Pos. 11)** dünn mit Silikonfett einreiben und in die Nut am Kragen und am Zapfen legen. Nicht
   verdrehen, nicht über scharfe Kanten ziehen.
3. **Hülse (Pos. 2)** mit gereinigter Sonde von der Sondenspitze her aufschieben, bis der Rand im Dachziegelschlitz der
   Kappe sitzt. Gleichmässig schieben, nicht auf die Taste drücken.
4. **Schraube M2 × 3 (Pos. 12)** von unten durch den Hülsenboden eindrehen. Beim ersten Mal furcht sie durch die
   Lippe Ø 1.7 (danach unverlierbar), dann in die Mutter. Handfest anziehen (O-6). Einschraubtiefe 1.4 mm = 3.5 Gänge
   (`check_sensor.txt` 5c; UL-4200A-Massstab ≥ 2 volle Gänge, `phase3_sleeve_sicherheit.md`).

**Prüfung 7 (Pflicht, FMEA F-21/F-62):**
- Hülse lässt sich von Hand nicht abziehen, Sichtfuge rundum gleich (0.3 mm), Kerbe um den Tropfen gleichmässig.
- O-Ringe sichtbar verpresst bzw. nicht aus der Nut gequetscht (vor dem Aufschieben kontrollieren).
- Ablaufschlitze hinten frei.
- Funktion: Taste **mit normaler Fingerkraft** kurz drücken (≈ 8 N, klickt nach ≈ 0.3 mm) → Messung/Statusanzeige
  (REQ-UI-04). Nicht mit Kraft nachdrücken: nach dem Klick trägt SW1 die Tastenkraft (O-5). L11 war nach dem Einsetzen sichtbar.
- Eintrag in der Musterliste: Seriennummer `fluidi-XXXX`, Prüfungen 2–7, Datum.

## 8 Batteriewechsel (Werkstatt / Muster)

Ablauf für Nutzer: `docs/manuals/BATTERIEWECHSEL.md` (mit Sicherheitshinweisen). Zusätzlich für die Werkstatt:

1. Sonde reinigen, über einer Schale arbeiten (FMEA F-22). Schraube lösen (PH1), Hülse nach unten über die Sonde
   abziehen (`renders/final/fluidi_04_batteriewechsel.png`).
   Dabei Kantenversiegelung (Kap. 5a) und Hohlkehle des Kragens unter der Lupe ansehen: abgeplatzte Stellen oder
   sichtbare Glasfasern in der Musterliste notieren und melden (Nachbessern nur nach Kap. 3a/5a mit frischer Masse).
2. Zelle zur offenen Clip-Seite (+x) herausschieben, **kein Metallwerkzeug** (S3-L1, F-24). Clip-Lötstellen unter der
   Lupe prüfen (Pads am Katalogminimum, Red-Team K-4).
3. Nur neue Markenzellen (Panasonic CR2032) mit **≥ 3.0 V Leerlauf** einsetzen; Zellen < 2.6 V nicht wieder verwenden,
   abkleben, entsorgen (PS-K1 Bed. 3). Taste nicht berühren, L11 beobachten.
4. O-Ringe prüfen und fetten, beschädigte ersetzen. Hülse aufschieben, Schraube handfest.
5. Prüfung 7 wiederholen. Wechsel in der Musterliste zählen (Testplan: 50 Wechsel ST-K6, Spritzwasser nach 10 Wechseln).

## 9 Demontage / Reparatur

Kappe, Platine, Schott und Kragen bilden nach dem Verguss eine Einheit und sind nicht zerstörungsfrei trennbar
(S3-K1/K2). Zugänglich bleiben nur Zellfach, O-Ringe, Hülse und Schraube.
