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
| Schichthöhe | **0.16 mm** Hülse, Kappe, Kragen, Wanne, Deckel; **0.12 mm** Taste, Klemmring, Teller, Stössel, Fenster | Logo-Strich 0.83 mm (Sensor) / 1.14 mm (Gateway) |
| Wände | **4** (≈ 1.7 mm) → Wände 1.6/2.0 mm werden massiv | |
| Deck-/Bodenschichten | 6 / 5 | |
| Füllung | **100 %** (Kleinteile), sonst 40 % Gyroid (nur Gateway-Dome) | Sensorwände sind ohnehin massiv |
| Naht | **hinten** („Back“), Naht verbergen; auf den O-Ring-Gleitflächen (Hülse innen z 2–8 und 30–37) Naht mit 600er-Papier glätten | Leckkanal quer zur Dichtung vermeiden (Mechanikbericht 2.1) |
| Elefantenfuss | 0.15 mm | Hülse, Kragen, Wanne |
| XY-Lochkompensation | 0.0 (zuerst Passungsprobe drucken, dann ggf. +0.05) | Kap. 4 |
| Geschwindigkeit | Standard „Optimal“, Aussenwand ≤ 120 mm/s | TDS < 250 mm/s |
| Stützen | **keine** (alle Teile stützenfrei, Kap. 3) | |
| Rand (Brim) | Hülse 3 mm Mausohren an den Ecken, Wanne/Deckel 3 mm | Verzug ASA |

## 3 Teile und Druckausrichtung

### Sensor (`mechanical/sensor/print/`, Masse in mm)

| Datei | Teil | Farbe | Ausrichtung (wie exportiert) | Kritische Stellen | g |
|---|---|---|---|---|---|
| `huelse_grau` | Hülse | Warmgrau | stehend, Boden auf dem Bett | Logo-Relief 0.25 auf senkrechter Wand; Warnsymbol innen vertieft 0.3; Kerbe oben offen; Furchlippe Ø 1.7 in den ersten 3 Schichten | 5.3 |
| `kappe_blau` | Kappe mit Zapfen, Schott, Biegezunge | Hellblau | **kopfüber** (Decke auf dem Bett) | Tastentasche im Bett; Schott = Brücke 5.5 mm; O-Ring-Nut-Flanke 1.35 mm Überhang (ohne Stütze druckbar, Probedruck); Zunge 0.8 mm = 2 Bahnen, wächst vom Block | 2.3 |
| `kragen` | Kragen (Vergussform) | beliebig | stehend | Mutterntasche von vorne = Brücke 4.6 mm; Nutflanke 1.35 mm | 0.8 |
| `fenster_tropfen` | Lichtfenster Sensor | natur transluzent | Tropfenfläche auf dem Bett, Schaft nach oben | Aussenfläche matt (Bettstruktur Engineering Plate = Diffusor) | 0.1 |
| `taste_blau` | Taste 9 × 6 | Hellblau | Oberseite auf dem Bett | Hals Ø 3.0 | 0.1 |
| `klemmring` | Klemmring Membran | Hellblau | Platte auf dem Bett | Rand 0.4 | < 0.1 |
| `tastenteller` | Teller (auf den Tastenhals gepresst) | Hellblau | flach | 0.4 mm dick = 3 Schichten | < 0.1 |
| `stoessel` | Stössel mit Finger und 30°-Keil | beliebig | flach auf der D-Fläche | Finger 1.15 × 1.2 mm | < 0.1 |
| `schottkeil` | Schottkeil | beliebig | flach | | < 0.1 |
| `distanzlehre_23p5` | Montage-Lehre (2 Stück, wiederverwendbar) | beliebig | stehend | | |
| `passprobe_huelse_unten/_oben` | Passungsproben (vor der ersten Hülse) | Warmgrau | stehend | Gleitsitz Kragen/Zapfen, O-Ring-Verpressung, Furchlippe | |

ASA pro Sensor ≈ **9 g** (≈ CHF 0.25, **ANNAHME** CHF 25/kg), kein AMS-Farbwechsel (jedes Teil einfarbig). Druckzeit-Schätzung nach Slicen eintragen.

### Gateway (`mechanical/gateway/print/`)

| Datei | Teil | Farbe | Ausrichtung | Kritische Stellen | g |
|---|---|---|---|---|---|
| `wanne_grau` | Wanne | Warmgrau | Boden auf dem Bett | Bodenschlitze (Lüftung), USB-C-Ausschnitt = Brücke 12 mm, Innenfacette 45° | 10.4 |
| `deckel_blau` | Deckel mit Facette, Steg, Domen, Lichtschacht | Hellblau | **kopfüber** | Facette = 45°-Überhang; Lichtschacht 45° | 6.8 |
| `fenster_tropfen_gw` | Lichtfenster Gateway | natur transluzent | Aussenfläche auf dem Bett | | 0.1 |

## 4 Toleranzen (FDM P1S, 0.4 mm) – im CAD umgesetzt

| Fügung | Spiel je Seite | Herkunft |
|---|---|---|
| Hülse innen ↔ Zapfen / Kragen (Gleitsitz) | 0.20 | Mechanikbericht 2.6 |
| O-Ring-Einbauraum radial | 1.35 ± 0.10 → Verpressung 15–33 % (AS568-017, Schnur 1.78 ± 0.08) | `check_sensor.txt` Pkt. 7 |
| Dachziegelrand Hülse (0.7) im Kappenschlitz (1.0) | 0.10 aussen, 0.20 innen | S3-W3 |
| Sondenschlitz Boden | 0.4 (Sonde inkl. Beschichtung ≤ 2.0 × 20.4) | |
| Platine im Kragen / Schott | 0.15 / 0.2 (mit Epoxid gefüllt) | |
| Fenster in Kappe, Lichtschaft in Zapfen | 0.10 Klebespalt | |
| Taste in Tasche | 0.40 (Sichtspalt, Design) | D-010 |
| Stössel in Rohr | 0.10 | |
| Gateway Deckelsteg in Wanne | 0.15 | |
| Gewindeeinsatz M2.5 (Gateway) | Bohrung Ø 3.2 (**ANNAHME** Einsatz Ø 3.5 × 4) | |

**Vor der ersten Serie:** `passprobe_huelse_unten` + `kragen` + O-Ring und `passprobe_huelse_oben` + `kappe_blau` drucken
und prüfen: Hülse gleitet mit Silikonfett ohne Klemmen, O-Ring sichtbar verpresst, Schraube M2 × 4 furcht durch die Lippe und
dreht danach frei. Bei Bedarf XY-Lochkompensation anpassen, nicht die Geometrie.

## 5 Nacharbeit und Montage-Hilfsstoffe

- Hülse: Gleitflächen innen (z 2–8, 30–37) glätten, Kerbe innen entgraten (O-Ring läuft darüber).
- Fenster: Aussenseite matt lassen; Kleben mit transparentem 2K-Epoxid oder UV-Kleber (**ANNAHME** Typ, Welle 2), Klebstoff nicht auf die Sichtfläche.
- O-Ringe mit Silikonfett (Mechanikbericht 2.1), Werkstoff ohne Russ.
- Gateway: Gewindeeinsätze M2.5 mit Lötkolben 220 °C einsetzen (**ANNAHME**), FPC innen an die linke Stirnwand kleben.
