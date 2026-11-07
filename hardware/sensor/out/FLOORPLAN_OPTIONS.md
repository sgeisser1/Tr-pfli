# fluidi Sensor – Flächenbilanz Elektronikband und Optionen (Vorschlag für PCB_OUTLINE Rev B)

| | |
|---|---|
| Stand | 2026-11-07, Elektronik |
| Anlass | PCB_OUTLINE.md Rev A, Kap. 7 Nr. 1 (KRITISCH): Platz im Elektronikband |
| Skript | `.venv/bin/python hardware/sensor/gen/floorplan_options.py` (Flächen, Platzierungsprüfung, Kosten, PNG) |
| Skizze | `hardware/sensor/out/floorplan_options.png` (massstäblich, Ansicht von vorne, z ab Kopfunterkante Rev A) |
| Status | Vorschlag. PCB_OUTLINE Rev B erstellt die Mechanik. Die Kopfhöhe muss der Auftraggeber freigeben (D-010) |

## 1 Flächenbilanz (Courtyards aus KiCad 10)

Die Courtyards hat das Skript per `pcbnew` aus den Footprints des Schaltplans gelesen (`/usr/share/kicad/footprints`,
`hardware/sensor/lib/fluidi.pretty`). Der Courtyard umfasst Körper, Pads und den IPC-Rand von 0.25 mm.

| Gruppe | Rev A mm² | Option (c) mm² |
|---|---|---|
| U1 QFN24 4×4 | 28.2 | 28.2 |
| Y1 3225 + Y2 3215 | 24.6 | 24.6 |
| C1–C4 100 µF 1206 (D-013: Prototyp 4 Stück) | 43.7 | 43.7 |
| L1 2016, Q1 SOT-23, U2 SC-70-5 | 28.8 | 28.8 |
| U3 TMP1075 | 22.8 (VSSOP-8) | 4.8 (SOT-563) |
| SW1 | 42.7 (TS-1187A) | 21.5 (TS-1088) |
| D1 1615 | 5.8 | 5.8 |
| TP4 | 4.2 | 0 (Pad auf B) |
| 0402 (33 bzw. 32 Stück inkl. DNP C19/C20) | 60.9 | 59.1 |
| **Summe** | **261.5** | **216.3** |

- Das Band F Rev A misst 20 × 5.6 = **112 mm²**. Allein SW1 belegt 43 mm², und mit 5.65 mm Courtyard ist er höher als das Band.
- Für Leiterbahnen, QFN-Fanout und Vias braucht man erfahrungsgemäss einen Faktor 1.3–1.5 (**ANNAHME**). Damit ergibt sich
  für 20 mm Breite eine Bandhöhe von 17–19.6 mm (Rev A) bzw. **14.1–16.2 mm** (Option c).
- Zur Kontrolle hat das Skript eine konkrete Blockplatzierung gerechnet und auf Überlappung geprüft. Jeder Block ist
  ≥ 1.1 × die Courtyard-Summe seiner Teile. SW1 und D1 liegen auf den Rev-A-Koordinaten. Ergebnis: **Band z 32.7 … 49.1 = 16.4 mm**
  (Faktor 1.52). Dieser Wert ist der Planwert.
- Antenne (Z1, unverändert): Der KiCad-Footprint `Texas_SWRA117D_2.4GHz_Left` hat einen Courtyard von 15.6 × 6.0 mm. AN043 S.1
  nennt „15.2 x 5.7 mm“, S.4 Abb. 3/Tab. 1 zeigt Masse ab der Platinenkante (D2 0.3) und Massefläche nur unterhalb der Antenne.
  Neben und über der Antenne darf kein Kupfer und kein Bauteil liegen. Unter der Antenne liegt die Masse des Bands.
  Das CC23xx-HW-Guide (SWRA834A Kap. 4.7/5) verlangt das Pi-Netz nahe der Antenne, das ist berücksichtigt (RF-Block oben).

## 2 Optionen

Kosten aus `scripts/cost_model.compute` (D-005). Prototyp: 5 PCB, 5 bestückt, 4 × 100 µF. Serie: 20 PCB, 16 bestückt,
15 Sensoren, 2 × 100 µF. Zusätzlich im Skript: Grenzkosten der PCB proportional zur Länge (**ANNAHME**) und ASA 0.035 CHF/g (**ANNAHME**).

| Option | Band / Kopf | Stück Proto / Serie CHF | Einmal Serie CHF | Voll Serie CHF | Sicherheit | Fertigung | Urteil |
|---|---|---|---|---|---|---|---|
| Rev A (Referenz) | 5.6 / 48 | 8.11 / 7.10 | 88.85 | 13.03 | ok | Economic | **passt nicht** |
| (a) Halter B, handgelötet | Band unverändert | 8.22 / 7.22 | 86.09 | 12.96 | **verletzt S3-K1** | Economic + 3 Handlötstellen (≈ 2–3 min, REQ-FAB-03 ok) | verworfen |
| (b)+(c)+(d) beidseitig | 13.4 / ≈ 56 | 8.56 / 7.59 | **165.80** | 18.64 | ok | Standard-PCBA, Panel ≥ 70 × 70 (nicht modelliert), PCB 0.8 mm nach vorn | Rückfallebene |
| (c) allein | 16.4 nötig | – | – | – | ok | Economic | reicht nicht allein |
| (c)+(d) | 16.4 / ≈ 59 | 8.33 / 7.34 | 89.19 | 13.28 | ok | Economic, einseitig | gut, aber REQ-TMP-01 offen |
| **(f) = (c)+(d) + U3 im Kragen** | **16.4 / ≈ 59** | **8.34 / 7.34** | **89.19** | **13.29** | ok, Freigabe Sicherheit (S3-K2) nötig | Economic, einseitig; Tasche im Kragen | **empfohlen** |

### (a) Zellhalter auf der B-Seite
- Die F-Seite unter der Zelle (z 7.5–30.3) wird frei, sie liegt aber **im Zellfach**. Das Fach wird beim Zellwechsel geöffnet
  und im Einzelfehlertest geflutet (REQ-SAF-05). Elektronik dort verletzt S3-K1 („beim Öffnen liegt nur das Zellfach frei“,
  `phase3_sleeve_sicherheit.md` Kap. 5).
- Variante Verguss bzw. Coating: Das ginge laut Sicherheit nur mit einer Anforderungsänderung. Coating allein ist kein Ersatz (ebd. Kap. 1).
- Variante „Längsschott“ (die Platine trennt F trocken von B nass, Frontschale auf die Platinenkanten geklebt):
  - Hinter der Platine sind nur 2.4 mm frei (y 9.0 → Hülse innen 11.4), der 3034 ist aber 4.1 mm hoch. Die Platine müsste also ≈ 2 mm nach vorne. Das kollidiert mit Mutter/Schraube M2 (heute 0.4 mm vor F), dem Zapfen und dem LED-Abstand.
  - VBAT/GND vom B-Pad zur F-Elektronik brauchen Vias im Fach. Das widerspricht S2-W03, ausser mit Epoxy-filled-Vias (+20.3 USD je Bestellung).
  - Dazu käme eine neue Klebedichtung von ≈ 66 mm Länge entlang der Glasfaserkanten.
  - **Neukonstruktion, nicht empfohlen.**
- Handlöten des Halters allein bringt keine Fläche. Es spart nur 3.07 USD Extended-Gebühr je Bestellung.

### (b) Beidseitige Bestückung (Standard-PCBA)
- Die B-Seite im Band ist kleiner, als Rev A angibt. Unterhalb von z 34.2 liegt die Zapfenwand hinten bei y 9.25, also nur
  **0.25 mm** hinter B (`fluidi_params.py`: `SP_IN_OFF_LOW` 3.75). Zwischen z 34.2 und 38.4 sind es 1.2 mm. Die 2.4 mm gelten erst über z 38.4.
  Beim Einschieben von unten müssten die B-Teile zudem durch Schott und Zapfen.
- **Machbar nur so:** Platine 0.8 mm nach vorne (y_F 6.6), Schottschlitz hinten bis y 9.0, auf B nur Teile ≤ 0.6 mm (0402).
  Folgen: Der LED-Abstand sinkt von 2.0 auf 1.2 mm (Ziel 1.5–2.5, Lichtschaft kürzen) und die Mutter M2 kollidiert (Achse verschieben). Beides entscheidet die Mechanik.
- Auch dann muss das Band auf 13.4 mm wachsen (+7.9 mm), weil die grossen Teile auf F bleiben (Quarze, 1206, SW1, QFN).
- Kosten: Einmalkosten **+77 CHF je Bestellung** (Setup 51.12 + Schablone 16.42 + Fixture 16.42 USD + Feeder für alle Typen).
  Das Panel ist nicht eingerechnet. Vollkosten Serie +5.4 CHF je Sensor.

### (c) Kleinere Bauteile, Basic/Extended-Bilanz unverändert (9 Extended, 1 Preferred, 15 Basic)
| Änderung | Gewinn | Teil (JLC-API 2026-11-07) | Beleg |
|---|---|---|---|
| SW1 → **TS-1088-AR02016** | −21.2 mm² | C720477, **Basic**, Lager 748 832, 0.053 USD | `docs/datasheets/XUNPU_TS-1088-AR02016_Datasheet_LCSC-2022-06.pdf` S.1: 3.9 × 3.0, Lotbild 5.50 × 2.00 (2 Pads), **H 2.0**, Hub 0.2, 160 gf. KiCad `SW_SPST_TS-1088-xR020` (Padhülle 5.5 × 2.0 = Datenblatt) |
| U3 → **TMP1075NDRLR** SOT-563 | −18.0 mm² | C3663690, Extended (ersetzt Extended), Lager 20 063, 0.456 USD @10 (+0.14) | `TI_TMP1075_Datasheet_SBOS854F.pdf` S.3 Tab. 4-1: ±1 °C −10…60 °C (REQ-TMP-01 10–35 °C erfüllt); S.5 Tab. 6.3: V+ 1.62–3.6 V; Abb. 5-4: SCL 1, GND 2, ALERT 3, A0 4, V+ 5, SDA 6; Tab. 7-3: A0 = GND → **0x48** wie Rev A; One-Shot Kap. 7.4.2; tCONV ≤ 15 ms (S.7) statt 7. Nicht leadless (E2 bleibt) |
| C24 entfällt (C21 versorgt U2 + U3 an SENS_PWR, nebeneinander) | −1.8 mm² | – | TMP1075 verlangt ≥ 0.01 µF (Kommentar parts.py) |
| TP4 als Pad auf B (keine Bestückung) | −4.2 mm² | – | – |

- **0201 ist nicht möglich:** Economic bestückt minimal 0402 (`JLCPCB_NOTES.md` Kap. 2). 0201 erzwingt Standard-PCBA.
- Kleinerer P-FET (SOT-323/SOT-883) gibt es nur als Extended (DMG1013UW C3040603, LP0404N3T5G C172433) → verworfen, weil das die Bilanz verschlechtert.
- Optionen mit Funktionsverlust, **nicht empfohlen**:
  - Y2 weglassen und LFOSC nutzen (−13.6 mm², −1 Extended). DS S.19 zeigt Standby 0.71 statt 0.74 µA, aber der BLE-Sleep-Takt wird ungenauer. Erst nach Energierechnung und Firmware.
  - In der Serie 2 statt 4 Footprints 100 µF (−21.9 mm²). Entscheid erst nach D-013.
- TS-1088 ist 2.0 mm hoch, Rev A erlaubt in der Zungenspalte 1.5 mm. Die Mechanik muss die Zunge 0.5 mm nach vorne setzen.
  Geht das nicht, bleibt TS-1187A und das Band wird +1.1 mm höher.

### (d) Kopf höher
- Mit (c): Band **16.4 mm statt 5.6 → +10.8 mm**, Kopf **48 → ≈ 59 mm**. Ohne (c) wären es ≈ +13.5 mm.
- Wachsen soll nur die blaue Kappe oberhalb z 38.3. Fuge (z 37), Fenster/LED (z 37.4), SW1 (z 35.6), Schott, Zellfach, Kragen und Hülse **bleiben unverändert**.
- Platinenlänge 149 → ≈ 160 mm.
- Stückkosten +0.24 CHF gegenüber Rev A: TMP N, Taster, längere PCB, 1.4 g ASA.

### (e) Eigene Ideen, geprüft und verworfen bzw. Nebengewinn
- Pi-Netz neben die Antennen-Speisung (x −10 … −5 in Z1): spart ≈ 1 mm Band, verändert aber die AN043-Massegeometrie.
  Nur als Rückfallebene, nach Messung (**PROTOTYP-PRÜFUNG**).
- Bauteile im Fachstreifen x 6.6–9.5: Dort liegt der Ausschubweg der Zelle (+x), dazu kommt S3-K1 → nein.
- Breitere Platine im Band: Der Schottschlitz x ± 10.2 begrenzt auf 20 mm, weil die Platine von unten eingeschoben wird → nein.
- **Nebenbefund REQ-TMP-01** (gelöst durch Option f, Kap. 2f): Gefordert ist die Bodentemperatur „nahe der Dichtlinie unter der Versiegelung“. U3 liegt im Band,
  ≈ 30 mm über dem Kragen, und misst Kopf- bzw. Lufttemperatur. Der Kragen (Z5) und die Sonde (Z7) erlauben keine Bauteile.
  → Abweichung dem Orchestrator melden: Anforderung präzisieren oder am Muster die Abweichung Kopf–Boden ermitteln (**PROTOTYP-PRÜFUNG**).

### (f) Temperatursensor im Sondenkragen (Folgeauftrag Projektleiter)

Vorschlag: U3 TMP1075NDRLR + eigener Abblock-C24 (100 nF, ≥ 0.01 µF verlangt) auf F im Kragen, vollständig im Epoxid.
R4/R5 (Pull-ups an SENS_PWR) bleiben im Band. Die Leitungen SENS_PWR, SDA, SCL und GND laufen über die Innenlagen L2/L3
durch Schott und Fach, ohne Via und ohne Aussenkupfer im Fach (Z4, S2-W03, S3-K1). Vias gibt es nur im Band und in der Bauteilzone des Kragens.

**(1) Fläche und Kopfhöhe:** Im Band werden nur 4.8 mm² Courtyard frei (U3, C24 wandert mit; R4/R5 bleiben).
Mit dem Faktor 1.5 wären das rechnerisch −0.4 mm Band. In der geprüften Platzierung bestimmen aber RF-Block und U1 die
Oberkante, deshalb bleibt das **Band bei 16.4 mm und der Kopf bei ≈ 58.8 mm**. (f) ist eine Entscheidung für die
Messqualität (REQ-TMP-01) und keine Flächenlösung. Kosten wie (c)+(d) (+1 × 100 nF): Serie 7.34 CHF Stück, 89.19 CHF einmalig.

**(2) Platz im Kragen** (`fluidi_params.py` Rev A, `fluidi_sensor.py` Z. 69–95):
- Ist-Zustand: Verguss z 2.0–7.3. Der ASA-Kragen umschliesst die Platine mit nur 0.15 mm Spalt (Schlitz y 7.25–9.15),
  heute ist dort also **kein** Bauteilraum.
- Nötig ist eine **Tasche 1.2 mm tief** vor F (y 6.2–7.4). Bis zum Nutgrund des Kragen-O-Rings (y 2.95, z 4.3–6.7) bleiben ≥ 3 mm ASA.
- Mutter M2 (x ± 2.3, z 2.3–3.9, Rückseite y 7.0) und Schraubenspitze (bis z 4.3) → Bauteile nur bei **|x| ≥ 2.6**.
- **Dichtstreifen z 2.0–4.2** ohne Kupfer und Vias auf allen Lagen (M-03: 2 mm). Dieser Streifen bleibt die eigentliche Sondendichtung (S3-K2).
- Bauteilzone **z 4.4–6.8**: 2.4 mm hoch, darüber ≥ 0.5 mm Epoxid bis z 7.3.
- Platz je Seite 7.1 × 2.4 = 17 mm². Der Block U3 + C24 braucht 4.4 × 2.0 = 8.8 mm² (≥ 1.1 × 6.6 mm² Courtyard,
  Skriptprüfung OK) bei x −9.2 … −4.8. SOT-563 ist 0.6 mm hoch, 0402 0.55 mm → passt in 1.2 mm.
- Abstand zu den Elektroden: Die Sonde (Z7) beginnt bei z −5.0, Abstand also ≥ 9.4 mm (Z6 dazwischen elektrodenfrei).
  Abstand zum O-Ring: radial ≥ 3 mm ASA.
- Die Zone Z5 von Rev A („keine Bauteile, keine Vias“) muss dafür geändert werden → **Freigabe Sicherheit (S3-K2) nötig**.

**(3) Thermik, Lötstellen, Feldmessung:**
- Thermik (grobe Abschätzung, **ANNAHME**, nur Wärmeleitung, ohne Konvektion in der Hülse):
  - Zur Erde: Innenlagen-GND/Guard als „Wärmefinger“ von U3 durch Z6 bis zur Sonde, 2 × 0.5 oz × 20 mm, L ≈ 10.5 mm
    → G ≈ 390 · 0.61 mm² / 10.5 mm ≈ **0.023 W/K**.
  - Zum Kopf: nur 4 Leiterbahnen 0.15 mm + FR4 über ≈ 25 mm → G ≈ **0.0005 W/K**, sofern im Fach **keine** durchgehende
    Masseebene zum Band läuft (GND als schmale Bahn ausführen).
  - Gewichtung damit ≈ 98 % Erde (heute im Band ≈ 0 %). Bei Kopf 65 °C und Boden 25 °C ergäbe das ≈ 1 K Fehler, Konvektion
    in der Hülse nicht eingerechnet → **PROTOTYP-PRÜFUNG** (Sonne/Heizlampe, Referenzfühler im Boden).
  - Der GND-Finger in Z6 (über der Erde) muss in der Feldsimulation geprüft werden (Luftanteil Messvolumen, `simulation/field/`).
- Lötstellen im Epoxid:
  - Ausdehnung: Epoxid ungefüllt 50–70 ppm/K, FR4 14–17, Lot ≈ 22 (**ANNAHME**, keine lokale Quelle). Die Kopftemperatur
    erreicht bis 65 °C (RB-03), also nahe an einer niedrigen Tg.
  - Empfehlung: mineralisch gefülltes, hartes Epoxid mit **Tg ≥ 80 °C** für die ganze Kragenvergussmasse, damit die
    Dichtfestigkeit bleibt (Zug 750 N laut Mechanikstudie 2.8).
  - Bauteile vorab mit einem dünnen, weichen Tropfen (Silikon-Gel/PU) abdecken (**nur** in der Bauteilzone, nicht im Dichtstreifen).
  - SOT-563 mit flachen Beinen und 0402 sind klein, das Risiko gering bis mittel. **PROTOTYP-PRÜFUNG**: 50 Zyklen −10/+65 °C, danach I²C-Funktion und Flutung Kragen.
- Feldmessung:
  - Die I²C-Leitungen laufen ≈ 25 mm neben PROBE_SENSE (Innenlage). Ablauf laut PINMAP: TMP lesen → TMP-Shutdown → Oszillator.
    Während der Messung liegen SDA/SCL über R4/R5 statisch an SENS_PWR (über C21/C24 wechselspannungsmässig an Masse).
    Sie sind dann eine konstante Parasitärkapazität und werden in der Zweipunktkalibrierung herausgerechnet.
  - Firmware-Regel: **kein I²C-Verkehr während der Oszillatormessung.**
  - Layout: PROBE_SENSE und I²C auf verschiedenen Innenlagen oder ≥ 1 mm Abstand mit GND-Bahn dazwischen.
  - Der Einfluss des U3-Kupfers bei ≥ 9 mm über der ersten Elektrode ist vernachlässigbar (**ANNAHME**, Feldsimulation).

**(4) Weitere Bauteile im Kragen:**
- Die Messkette (U2, R3, Cref) näher an der Sonde würde C_par senken. Ihre Pads im Epoxid hätten aber eine εr(T)-abhängige
  Kapazität am hochohmigen Knoten, und DIO8/DIO11 (Cref-Schaltung) liefen 30 mm lang → **nicht unkritisch, nicht empfohlen** (eventuell spätere Feldstudie).
- R9–R12 müssen im Elektronikraum bleiben (R2-A3). HF-Teile, LED und Taster kommen nicht in Frage.
- → Nur U3 + C24.

## 3 Empfehlung: (f) = (c)+(d) + U3 im Sondenkragen, einseitig, JLC Economic

- Sicherheit: S3-K1, R2-A3 und R2-W01 sind unverändert erfüllt. R9…R12 liegen als getrennter Block im Elektronikraum.
  R9/R10 bzw. R11/R12 bekommen je eine eigene Lötstopp-Öffnung und Abstand, TP1/TP2 bleiben im Fachstreifen.
- Kosten: Die Einmalkosten bleiben auf Economic-Niveau (89 CHF), die Serie kostet 7.34 CHF je Stück.
- Preis dafür: **Kopf +10.8 mm, braucht die Freigabe des Auftraggebers**. Lehnt er die Höhe ab, ist (b)+(c)+(d) die Rückfallebene: +7.9 mm, +77 CHF je Bestellung, Mechanikänderungen wie oben.

Kragen: U3 + C24 bei x −9.2 … −4.8, z 4.6 … 6.6 (Tasche), Dichtstreifen z 2.0 … 4.2 kupferfrei. Freigabe Sicherheit (S3-K2) nötig.

Grober Platzierungsplan (Skizze, rechtes Feld; z = Kopfkoordinate):
- **z 32.7–35.1:** C1/C2 (1206 quer) Mitte rechts, C3 hochkant am rechten Rand, R6–R8 als Streifen unter SW1.
- **z 33.8–37.6:** SW1 (−6, 35.6), D1 (0, 37.4), C4.
- **z 37.6–46.5:**
  - links: Q1, Messkette (U2, R3, C21–C23), R4/R5 (U3 im Kragen). Die Messkette sitzt nahe der Durchführung PROBE_SENSE (Innenlage) und weit weg vom HF-Teil.
  - Mitte: U1 mit C5–C13, R1, L1.
  - rechts: Y1/Y2 mit C14/C15.
- **z 45–48.8:** HF-Kette C16–C20/L2/R2 direkt unter der Antennenspeisung, UART-Barriere R9–R12 rechts.
- **z 49.1–54.8:** Antenne AN043. **z 54.8:** Platinenoberkante.

## 4 Vorschlag Änderungen PCB_OUTLINE Rev B (setzt die Mechanik um)

1. `Z['BAND1']` 38.3 → **49.1**. `ANT0/ANT1` → 49.1/54.8. `PCB Z_TOP` 44.0 → **54.8**, Länge 149 → **159.8**.
   Kopf H 48 → **58.8**. Alle Teile oberhalb der Fuge (Stössel, Block, Zunge) verschieben sich um +10.8.
2. `Z2_BAND_F`: hmax 2.0 bleibt. Zungenspalte **≤ 2.0** statt 1.5 (TS-1088 H 2.0), Zunge +0.5 mm nach vorne.
3. SW1: Teil TS-1088-AR02016 (C720477), Mitte bleibt (−6.0, 35.6), Pads **2 × (1.05 × 2.0), Abstand 4.45 in x**.
   Betätiger Ø 1.8, Hub 0.2 (vorher 0.25).
4. `Z2_BAND_B`: weiterhin unbestückt, **Kupfer/Testpads erlaubt** (TP4 OSZ_OUT, TP3 GND optional). Pogo-Zugang nur vor dem Einschieben.
5. Unverändert: D1, Zelle/Clip, Schott, Kragen, Hülse, Fachstreifen.
6. **Z5 Kragen aufteilen:** Dichtstreifen z 2.0–4.2 (alle Lagen ohne Kupfer und Vias, wie heute) und Bauteilzone z 4.4–6.8,
   nur F, nur |x| ≥ 2.6, Höhe ≤ 0.7 mm, Vias dort zulässig. Kragen-Tasche 1.2 mm tief vor F, Epoxid Tg ≥ 80 °C, gefüllt.
   Fach Z4: Innenlagen-Leitungen zum Kragen (4 Netze), weiterhin ohne Vias. Erst nach Freigabe Sicherheit (S3-K2).
7. Kap. 7 Nr. 1 schliessen. Neuer offener Punkt: Kopfhöhe 58.8 mm durch den Auftraggeber.

Nur falls (b) gewählt wird: y_F 7.4 → 6.6, Schottschlitz Y1 → 9.0, B-Teile ≤ 0.6 mm im Band, LED-Lichtschaft und Mutterachse anpassen, Band 13.4 mm.

## 5 Kunststoff 0.5–1.3 mm vor dem Antennenkupfer

**Urteil: unkritisch unter Bedingungen, aber nicht vernachlässigbar.**
- Quelle: AN043 S.5 Abb. 4. Ein vollständiges Kunststoffgehäuse verschiebt die Resonanz von ≈ 2.48 auf ≈ 2.40 GHz (≈ −80 MHz, −3 %).
  Die Bandbreite (VSWR < 2) beträgt im Freiraum ≈ 250 MHz (S.6). TI empfiehlt, die Antenne leicht zu kürzen (S.6).
- Die ASA-Kappe umschliesst die Antenne ohnehin ringsum wie das Dongle-Gehäuse. Die lokalen Teile kommen dazu:
  - Stössel Ø 4 in 1.3 mm Abstand, über ≈ 4 mm von ≈ 25 mm Antennenlänge.
  - Der Kappenblock liegt über der Platinenkante, nicht vor dem Kupfer.
- Störungsabschätzung (**ANNAHME** εr ASA ≈ 3, keine lokale Quelle; ≤ 30 % der Luftseiten-Feldenergie jenseits 1.3 mm):
  - lokal εeff 2.7 → 3.7 (−15 %)
  - × Längenanteil 0.16 × 0.3 → **≈ −0.7 % ≈ −17 MHz**
  - Zusammen mit der Kappe also ≈ −100 MHz, das liegt innerhalb der Bandbreite und ist mit dem Pi-Netz (C19/R2/C20) bzw. einer kürzeren Antenne abstimmbar.
- Bedingungen:
  - Das offene Ende der IFA (Arm L1, höchstes E-Feld) liegt **nicht** hinter Stössel oder Block. Bei der „Left“-Variante ist es rechts, Stössel bei x −2.2 → ok.
  - Kein russgefülltes oder metallisiertes Material vor der Antenne (hellblaues ASA ok).
  - Pi-Netz bestückbar lassen.
  - **PROTOTYP-PRÜFUNG:** S11 mit VNA bzw. RSSI im montierten Gehäuse, gegebenenfalls Antenne kürzen.
- Option (d) ändert daran nichts: Die Teile wandern mit.
