# fluidi – Druckeinstellungen Sensor P3 und Gateway G1 v3 (Bambu Lab P1S)

Stand 2026-11-07, Phase 4b Welle 1. Druckdateien werden von den Generatoren erzeugt und liegen bereits in
**Druckausrichtung** (auf z = 0, mittig):

```
.venv/bin/python mechanical/gen/fluidi_params.py      # Schnittstelle + Masse
freecadcmd mechanical/gen/fluidi_sensor.py           # mechanical/sensor/print/*.{3mf,stl,step}
freecadcmd mechanical/gen/fluidi_gateway.py          # mechanical/gateway/print/*.{3mf,stl,step}
```

## 1 Werkstoff

| | Wahl | Beleg |
|---|---|---|
| Gehäuse (alle tragenden Teile) | **Bambu ASA** (UV- und feuchtebeständig, kein PLA) | `docs/references/BambuLab_ASA_TechnicalDataSheet_V2.0.pdf` S.1–2: HDT **92 °C** (ISO 75, 1.8 MPa) / 100 °C (0.45 MPa), Vicat 106 °C, E 2450 MPa (XY) / 2120 MPa (Z), Zugfestigkeit 52 / 35 MPa (XY / Z) → REQ-MECH-12 (HDT ≥ 80 °C) **erfüllt** |
| Farben | Hülse/Wanne Warmgrau hell #B9B5AC, Kappe/Taste/Deckel Hellblau (D-010/D-011) | Filamentton nach Musterdruck wählen (P3_FLUIDI.md Kap. 6). **Pigment ohne Russ/Metall** im Antennenbereich (Kappe, Deckel) – **ANNAHME**, beim Filamentkauf prüfen (Elektronikbericht 2.4 Pkt. 3) |
| Lichtfenster | transluzentes, mattes Filament **natur**, ≥ 1 mm (Diffusor) | bevorzugt ASA natur/transluzent (**ANNAHME** Verfügbarkeit). PETG transluzent nur mit Nachweis (REQ-MECH-12): 7 d bei 65 °C ohne Verformung und Klebefuge dicht (PROTOTYP-PRÜFUNG) |
| Kragen, Stössel, Schottkeil, Lehren | ASA, Farbe beliebig (Reste) | im Gehäuse unsichtbar |
| Trocknen | 80 °C, 8 h vor dem Druck, Lagerung < 20 % rF | TDS S.1 |

## 2 Profil (Bambu Studio, Basis: Systemprofil „Bambu ASA“ + „0.16mm Optimal @BBL P1S“)

| Parameter | Wert | Bemerkung |
|---|---|---|
| Drucker / Düse | P1S, 0.4 mm gehärtet oder Standard | |
| Druckplatte | Engineering Plate oder High Temperature Plate, **Klebestift** | TDS S.1 |
| Düsentemperatur | **260 °C** (erste Schicht 265 °C) | TDS-Bereich 240–270, Prüfkörper bei 260 |
| Betttemperatur | **90 °C** | TDS 80–100 |
| Bauraum | **Haube geschlossen**, 10 min mit Bett 90 °C vorheizen (Ziel 45 °C, TDS 45–60), Deckel/Oberseite zu | P1S hat keine Kammerheizung |
| Bauteillüfter | 10 % (ab Schicht 3), max. 30 % für Kleinteile (< 10 s/Schicht), Hilfslüfter **aus** | TDS 0–80 %; ASA verzieht bei starker Kühlung |
| Schichthöhe | **0.16 mm** Hülse, Kappe, Kragen, Wanne, Deckel; **0.12 mm** Taste, Klemmring, Teller, Stössel, Fenster | Logo-Strich 1.00 mm (Sensor V4) / 1.14 mm (Gateway) |
| Wände | **4** (≈ 1.7 mm) → Wände 1.6/2.0 mm werden massiv | |
| Deck-/Bodenschichten | 6 / 5 | |
| Füllung | **100 %** (Kleinteile), sonst 40 % Gyroid (nur Gateway-Dome) | Sensorwände sind ohnehin massiv |
| Naht | **hinten** („Back“), Naht verbergen; auf den O-Ring-Gleitflächen (Hülse innen z 2–8 und 30–35, Rev B) Naht mit 600er-Papier glätten | Leckkanal quer zur Dichtung vermeiden (Mechanikbericht 2.1) |
| Elefantenfuss | 0.15 mm | Hülse, Kragen, Wanne |
| XY-Lochkompensation | 0.0 (zuerst Passungsprobe drucken, dann ggf. +0.05) | Kap. 4 |
| Geschwindigkeit | Standard „Optimal“, Aussenwand ≤ 120 mm/s | TDS < 250 mm/s |
| Stützen | **keine** (alle Teile stützenfrei, Kap. 3) | |
| Rand (Brim) | Hülse 3 mm Mausohren an den Ecken, Wanne/Deckel 3 mm | Verzug ASA |

## 3 Teile und Druckausrichtung

### Sensor (`mechanical/sensor/print/`, Masse in mm)

| Datei | Teil | Farbe | Ausrichtung (wie exportiert) | Kritische Stellen | g |
|---|---|---|---|---|---|
| `huelse_grau` | Hülse | Warmgrau | stehend, Boden auf dem Bett | Logo-Relief 0.25 auf senkrechter Wand (19.4 mm); Warnsymbol innen vertieft 0.3; Kerbe oben offen; 4 Ablaufschlitze 3 × 1.2 hinten (Brücke 3 mm); Furchlippe Ø 1.7 in den ersten 3 Schichten; Höhe 44.7 | 7.5 |
| `kappe_blau` | Kappe mit Zapfen, Schott, Biegezunge | Hellblau | **kopfüber** (Decke auf dem Bett) | Tastentasche im Bett; Schott = Brücke 5.5 mm; O-Ring-Nut-Flanke 1.35 mm Überhang (ohne Stütze druckbar, Probedruck); Zunge 0.6 mm (P5-M2, 1–2 Bahnen, Arachne) mit Nase; **Nasen-Oberseite 30° zur Waagrechten = kopfüber 60° Überhang auf 1.2 mm** (ohne Stütze, Probedruck; hängt sie durch, Fläche mit 600er nacharbeiten); Führungsrippe vor dem Finger; D-Bohrung Stössel; Boden unter dem Membransitz 0.8 (Sektor zur Platine 0.3, W-1); Ablaufstufe am Zapfen = 0.5 mm Überhang (kopfüber ohne Stütze); dünnste Zapfenwand 0.54 mm hinter den hinteren Nutecken; **Phase 5: 45°-Trichter verbindet Zapfen und Kappenwand (P5-M1, vorher 2 getrennte Körper), Mantel 0.8 um die Membran-Senkung (P5-M3)**; Massbild `mechanical/drawings/FL-S-02_kappe_blau.pdf` | 4.7 |
| `kragen` | Kragen (Vergussform) | beliebig | stehend | Mutterntasche von vorne = Brücke 4.6 mm; Nutflanke 1.35 mm | 0.8 |
| `fenster_tropfen` | Lichtfenster Sensor | natur transluzent | Tropfenfläche auf dem Bett, Schaft nach oben | Aussenfläche matt (Bettstruktur Engineering Plate = Diffusor) | 0.1 |
| `taste_blau` | Taste 9 × 6 | Hellblau | Oberseite auf dem Bett | Hals Ø 3.0 | 0.1 |
| `klemmring` | Klemmring Membran, **Presssitz 0.05 je Seite** in der Senkung, verpresst die Membran 0.1 mm (R3-W2) | Hellblau | Platte auf dem Bett | Rand 0.4; Unterseite der Schürze = Dichtfläche zur Membran (oberste Lage, nicht nacharbeiten) | < 0.1 |
| `tastenteller` | Teller (auf den Tastenhals gepresst) | Hellblau | flach | 0.4 mm dick = 3 Schichten | < 0.1 |
| `stoessel` | Stössel mit Finger, 60°-Keil unten (P5-M2 Runde 2) | beliebig | flach auf der D-Fläche; Arm und Finger bündig mit der D-Fläche → vollflächig auf dem Bett, stützenfrei (W-3) | Finger 1.25 × 1.2 mm, Keil scharfkantig; Schaft Ø3 D-Profil | < 0.1 |
| `schottkeil` | Schottkeil | beliebig | flach | | < 0.1 |
| `distanzlehre_24p2` | Montage-Lehre Kragen–Schott 24.2 mm (2 Stück, wiederverwendbar; V-K, D-023) | beliebig | stehend | | |
| `passprobe_huelse_unten/_oben` | Passungsproben (vor der ersten Hülse) | Warmgrau | stehend | Gleitsitz Kragen/Zapfen, O-Ring-Verpressung, Furchlippe | |

ASA pro Sensor ≈ **13 g** (Kopf V4, Rev B; Rev A ≈ 9 g) (≈ CHF 0.25, **ANNAHME** CHF 25/kg), kein AMS-Farbwechsel (jedes Teil einfarbig). Druckzeit-Schätzung nach Slicen eintragen.

### Gateway (`mechanical/gateway/print/`)

| Datei | Teil | Farbe | Ausrichtung | Kritische Stellen | g |
|---|---|---|---|---|---|
| `wanne_grau` | Wanne | Warmgrau | Boden auf dem Bett | Bodenschlitze (Lüftung), USB-C-Ausschnitt = Brücke 12 mm, Innenfacette 45° | 10.4 |
| `deckel_blau` | Deckel mit Facette, Steg, Domen, Lichtschacht | Hellblau | **kopfüber** | Facette = 45°-Überhang; Lichtschacht 45° | 6.8 |
| `fenster_tropfen_gw` | Lichtfenster Gateway | natur transluzent | Aussenfläche auf dem Bett | | 0.1 |

### Gateway G1 v4 für Raspberry Pi Zero 2 W (`mechanical/gateway_pi/print/`, D-014)

Erzeugen: `freecadcmd mechanical/gen/fluidi_gateway_pi.py` (schreibt auch `check_gateway_pi.txt` und `preview.png`).
Aussen 84 × 42 × 20 mm, Profil, Facette, Fuge und Tropfen wie G1 v3; Profil und Material wie Kap. 1–2.

| Datei | Teil | Farbe | Ausrichtung | Kritische Stellen | g |
|---|---|---|---|---|---|
| `wanne_grau` | Wanne mit Pi-Abstandshaltern, Lichtschacht, Trennwand Klimakammer, Nutpfosten, Kabelkanal | Warmgrau | Boden auf dem Bett | Senkkopfbohrungen unten (Brücke über Ø 5.4); Micro-USB-Fenster 11.4 × 7.8 (Brücke 11.4); Lichtschacht hängt 45° an der Innenfacette (ohne Stütze, Probedruck); Kabelkanal Ø 3.0 waagrecht; Stirnschlitze 1.2 hoch (Brücken 20 mm) | 14.0 |
| `wanne_grau_otg` | wie oben, zusätzlich Micro-USB-OTG-Fenster (XIAO-Empfänger extern, D-014) | Warmgrau | wie oben | Steg zwischen den Fenstern 1.2 mm | 13.8 |
| `deckel_blau` | Deckel mit 4 Niederhalterrohren (Einsatz M2.5), Steg, Gegenrippe Klimakammer, RTC-Rahmen | Hellblau | **kopfüber** | Facette 45°; vordere Rohre stehen auf der Innenfacette; Steg vorne bewusst weggelassen (sonst nicht senkrecht montierbar) | 9.7 |
| `fenster_tropfen_gw` | Lichtfenster | natur transluzent | Aussenfläche auf dem Bett | | 0.1 |

Montage: Pi auf die 4 Abstandshalter legen (Buchsen in die inneren Freistiche der Rückwand), Klimasensor-Leitungen
(3V3 Pin 1, SDA Pin 3, SCL Pin 5, GND Pin 6 oder 9) **direkt in die Lötaugen** löten (Pi ohne Stiftleiste), Bündel
durch den Kanal Ø 3.0 in der Trennwand führen, Modul in die Nuten stecken, Kanal mit Silikon vergiessen (Zugentlastung
und Luftsperre). LED-Platine auf den Lichtschacht kleben. Deckel senkrecht aufsetzen, umdrehen, 4 × M2.5 × 8 (ISO 7380,
**ANNAHME**) von unten durch Abstandshalter und Pi-Bohrung in die Einsätze (Ø 3.5 × 4, Bohrung 3.2, Lötkolben 220 °C,
**ANNAHME**) – die 4 Schrauben halten Pi und Deckel zugleich. Nylonschrauben als Option, falls die RSSI-Messung mit
Stahlschrauben schlechter ist (PROTOTYP-PRÜFUNG). microSD bleibt innen (Zugang nach Lösen der 4 Schrauben).

**Vor dem ersten Druck am vorhandenen Pi messen** und in `PI`/`PARTS` des Generators eintragen: Platinendicke
(ANNAHME 1.0), Höhen HDMI/Micro-USB/microSD-Halter/Kamerabuchse, Überstand der microSD-Karte (ANNAHME 2.5),
Umspritzung des Netzteilsteckers (ANNAHME ≤ 10.6 × 7.0).

### Druckvorgabe Zapfenwand an den hinteren Nutecken (Sicherheit R3-W3)

Zwischen O-Ring-Nut (Zapfen, z 31.3 … 33.7) und Elektronikraum bleiben an den hinteren Nutecken nur **0.54 mm** Wand
(`check_sensor.txt` 9). Geometrisch ist ≥ 0.8 mm in Rev C nicht möglich: Die Wand liegt zwischen Nutgrund-Ecke (R 3.0,
O-Ring-Dehnung 2.1 %) und der Platinenecke (x 13.0, y 8.2); ein grösserer Innenradius des Zapfens würde die Platinenecke
schneiden (Ecke darf höchstens R 0.68 haben → Wand ≤ 0.64 mm). Darum für die Kappe:
- Wände 4, Füllung 100 %, „Lücken füllen“ **ein**, Linienbreite Wand 0.42, keine Naht an den hinteren Ecken (Naht hinten-Mitte).
- Nach dem Druck: Kappe gegen eine Lampe halten, die Ecken dürfen kein Licht durchlassen; Prüfung ST-W6 (b).
- Rev D: Wand ≥ 0.8 mm (Platine oder Nut ändern).

## 4 Toleranzen (FDM P1S, 0.4 mm) – im CAD umgesetzt

Fertigungszeichnungen aller Druckteile (Phase 5): `mechanical/drawings/FL-*.pdf`, erzeugt mit
`freecadcmd mechanical/gen/fluidi_drawings.py` (Prüfprotokoll `mechanical/drawings/drawings_check.txt`).

| Fügung | Spiel je Seite | Herkunft |
|---|---|---|
| Hülse innen ↔ Zapfen / Kragen (Gleitsitz) | 0.20 | Mechanikbericht 2.6 |
| O-Ring-Einbauraum radial | 1.35 ± 0.10 → Verpressung 15–33 % (Rev B: AS568-019, Schnur 1.78 ± 0.08, Dehnung 2.1 %) | `check_sensor.txt` Pkt. 7 |
| Dachziegelrand Hülse (0.7) im Kappenschlitz | 0.10 aussen, 0.70 innen (Rev B: Ablaufspalt) | S3-W3 |
| Sichtschale ↔ Zapfen oberhalb der Ablaufstufe (Rev B) | 0.70 (kein Kapillarspalt) | PCB_OUTLINE.md Kap. 7 |
| Sondenschlitz Boden | 0.4 (Sonde inkl. Beschichtung ≤ 2.0 × 20.4) | |
| Platine im Kragen / Schott | 0.15 / 0.2 (mit Epoxid gefüllt) | |
| Fenster in Kappe, Lichtschaft in Zapfen | 0.10 Klebespalt | |
| Taste in Tasche | 0.40 (Sichtspalt, Design) | D-010 |
| Stössel in Rohr | 0.10 | |
| Gateway Deckelsteg in Wanne | 0.15 | |
| Gewindeeinsatz M2.5 (Gateway) | Bohrung Ø 3.2 (**ANNAHME** Einsatz Ø 3.5 × 4) | |
| G1 v4: Pi-Platine zu Wänden / microSD-Karte zur Trennwand | 0.4 (Buchsenseite) bzw. ≥ 1.0 / 1.5 | `check_gateway_pi.txt` |
| G1 v4: Micro-USB-Umspritzung im Fenster | 0.4 je Seite | |
| G1 v4: Klimamodul-Platine in Nut | 0.15 je Seite (Nut 1.9 für 1.6) | Modul Welle 2 |
| G1 v4: Deckel-Gegenrippe zur Trennwand | 0.3 (= Fuge) | |

**Vor der ersten Serie:** `passprobe_huelse_unten` + `kragen` + O-Ring und `passprobe_huelse_oben` + `kappe_blau` drucken
und prüfen: Hülse gleitet mit Silikonfett ohne Klemmen, O-Ring sichtbar verpresst, Schraube M2 × 3 (V-K, D-023) furcht durch die Lippe und
dreht danach frei. Bei Bedarf XY-Lochkompensation anpassen, nicht die Geometrie.

## 5 Nacharbeit und Montage-Hilfsstoffe

- Hülse: Gleitflächen innen (z 2–8, 30–35) glätten, Ablaufschlitze frei halten, Kerbe innen entgraten (O-Ring läuft darüber).
- Fenster: Aussenseite matt lassen; Kleben mit transparentem 2K-Epoxid oder UV-Kleber (**ANNAHME** Typ, Welle 2), Klebstoff nicht auf die Sichtfläche.
- O-Ringe mit Silikonfett (Mechanikbericht 2.1), Werkstoff ohne Russ.
- Gateway: Gewindeeinsätze M2.5 mit Lötkolben 220 °C einsetzen (**ANNAHME**), FPC innen an die linke Stirnwand kleben.
