# fluidi – Sensor Rev C bei JLCPCB bestellen (Schritt für Schritt)

| | |
|---|---|
| Dokument | `docs/manuals/BESTELLEN_JLC.md`, Version 1.0, 2026-11-08 (Fertigung/Kosten, Phase 5) |
| Für | Auftraggeber (bestellt selbst; die Agenten bestellen nichts) |
| Grundlage | Bestellunterlage `hardware/sensor/out/ORDER_JLC_REV_C.md` (Sollwerte, Abhaklisten Kap. 4 und 5, Remark Kap. 8); JLC-Screenshot des Auftraggebers vom 2026-11-08; JLC-Hilfeseiten lokal unter `docs/references/JLCPCB_*_Auszug_2026-11-08.txt` |
| Dateien | `production/rev-C/1_jlc_upload/` (Gerber-ZIP, BOM, CPL) – Kopien aus `hardware/sensor/out/` |
| Kosten | `docs/reviews/phase5_kosten_final.md` |

**Was belegt ist und was nicht:**
- Schritte 1–5 (Konto, Upload, PCB-Felder): Feldnamen und Optionen stammen aus Ihrem Screenshot vom 2026-11-08 und aus
  der JLC-Hilfe „How do I place an order“ (`docs/references/JLCPCB_HowToPlaceOrder_Auszug_2026-11-08.txt`).
- **Ab Schritt 6 (PCB Assembly eingeschaltet) hat noch niemand das Formular gesehen.** Feldnamen, Reihenfolge und
  Knöpfe dort sind **ANNAHME** (aus der JLC-Preisseite und früheren Projektnotizen). Weicht etwas ab: nicht raten,
  Screenshot machen, Projektleitung fragen.
- Screenshots jedes Schritts ablegen unter `docs/references/JLC_Bestellung_RevC_<JJJJ-MM-TT>_<Nr>.png` und die Nummer
  in der Abhakliste ORDER Kap. 4 eintragen.

**Stopp-Regeln (nicht bezahlen, Projektleitung informieren):**
1. „Epoxy Filled & Capped“ ist nicht wählbar oder verschwindet nach dem Einschalten von PCB Assembly (Auflage A-2, D-023).
2. „Economic“ ist mit dieser Platine nicht wählbar (B-2) → Ausweichweg Standard-PCBA nach ORDER Kap. 6, braucht Ihre Freigabe.
3. Eine BOM-Zeile wird nicht erkannt oder ein Teil ist nicht an Lager (v. a. BT1 C5213768).
4. Gesamtbetrag weicht mehr als 10 % von Schritt 10 ab.
5. Ein Bauteil liegt in der Vorschau anders als in ORDER Kap. 5 oder die Lage ist unklar (Schritt 8). **Nie selbst drehen.**
6. Im Warenkorb erscheint der Posten „Pre-reflow Soldering“ (Schritt 9).
7. `order_check.py` meldet „FEHLER Platzhalter“ oder das Paket ist veraltet (Schritt 1).

---

## Schritt 1 – Dateien prüfen (vor dem Upload)

Im Ordner `production/rev-C` (WSL/Linux):

```
.venv/bin/python production/make_release_rev_c.py --check     # Paket = aktuelle Quellen und Git-Stand?
.venv/bin/python hardware/sensor/gen/order_check.py           # Platine/Gerber; muss "Platzhalter ... keiner" melden
cd production/rev-C && sha256sum -c SHA256SUMS
```

`--check` muss „Paket aktuell“ melden und der Git-Stand im `README.md` des Pakets muss dem Commit entsprechen, den die
Projektleitung freigegeben hat. `sha256sum -c` allein genügt nicht (prüft nur die Kopien gegen sich selbst).

Unter Windows (PowerShell) für die drei Upload-Dateien: `Get-FileHash .\1_jlc_upload\* -Algorithm SHA256`.
Sollwerte (massgebend ist ORDER Kap. 1; Stand ohne Platzhalter, W-4):

| Datei | sha256 beginnt mit |
|---|---|
| `fluidi_sensor_gerber_jlc.zip` | `bf1902ea…` |
| `fluidi_sensor_bom_jlc.csv` | `3d99ffca…` |
| `fluidi_sensor_cpl_jlc.csv` | `b01ba147…` |

→ ORDER Kap. 4 Nr. 1 abhaken.

## Schritt 2 – Konto

1. https://jlcpcb.com → „Sign up“ (E-Mail, Passwort) bzw. einloggen. JLC: „Register and Login“ ist Schritt 1 der Bestellung.
2. Unter dem Konto die **Lieferadresse in der Schweiz** und eine Telefonnummer eintragen (DHL braucht sie für die
   Verzollung, **ANNAHME**).
3. Eingeloggt können andere Preise oder Coupons erscheinen als im Screenshot (nicht eingeloggt). Preise in Schritt 5 neu ablesen.

## Schritt 3 – Gerber-ZIP hochladen

1. Startseite → „Instant Quote“ bzw. Gerber-Datei ins Feld ziehen: **`fluidi_sensor_gerber_jlc.zip`** (nicht entpacken).
2. JLC erkennt Grösse und Lagen selbst. Erwartet: **4 Layers**, **26 × 158.5 mm** (Screenshot: 26 × 158.5).
3. „Gerber Viewer“ öffnen: 4 Kupferlagen, Kontur geschlossen, Sonde schmaler als Kopf, auf den Aussenlagen der Sonde kein
   Kupfer (Elektroden nur innen). Screenshot ablegen → ORDER Kap. 4 Nr. 2 (erster Teil).

## Schritt 4 – PCB-Felder in der Reihenfolge des Formulars

Spalte „Screenshot“ = Ihr Stand vom 2026-11-08. **Fett** = dort anders einstellen.

| # | Feld | Sollwert Prototyp | Sollwert Serie | Screenshot | Hinweis |
|---|---|---|---|---|---|
| 1 | Base Material | FR-4 | FR-4 | FR-4 | |
| 2 | Layers | 4 | 4 | 4 | aus dem Gerber |
| 3 | Dimensions | 26 × 158.5 mm | gleich | gleich | aus dem Gerber |
| 4 | PCB Qty | **5** | 20 | 20 | Mindestmenge 5 |
| 5 | Product Type | Industrial/Consumer electronics | gleich | gleich | |
| 6 | Deburring/Edge rounding | Yes | Yes | Yes | Pflicht-Aufpreis für 1.5–3 cm breite Platinen (0.02 USD/Stk) |
| 7 | Different Design | 1 | 1 | 1 | |
| 8 | Delivery Format | Single PCB | Single PCB | Single PCB | kein Nutzen (Economic) |
| 9 | PCB Thickness | 1.6 mm | 1.6 mm | 1.6 | Economic nur 0.8–1.6 mm |
| 10 | PCB Color | Green | Green | Grün | Economic + ENIG nur grün |
| 11 | Silkscreen | White | White | weiss | |
| 12 | Material Type | FR4 TG135 (Vorgabe) | gleich | TG135 | nicht ändern (ORDER Kap. 2) |
| 13 | Surface Finish | ENIG, 1 U" | gleich | ENIG 1 U" | Minuspad der Zelle ist Leiterplattenkupfer |
| 14 | Outer / Inner Copper Weight | 1 oz / 0.5 oz | gleich | gleich | |
| 15 | Specify Stackup | No | No | No | Standardaufbau; Economic: „Standard stack-up only“ |
| 16 | **Via Covering** | **Epoxy Filled & Capped** | gleich | gleich | **Pflicht** (A-2). Ohne → nicht bestellen |
| 17 | Via Plating Method | Horizontal Electroless Copper Plating | gleich | gleich | wird bei 16 erzwungen |
| 18 | Min via hole size/diameter | 0.3mm/(0.4/0.45mm) | gleich | gleich | kein Aufpreis |
| 19 | Board Outline Tolerance | ±0.2mm (Regular) | gleich | ±0.2 | |
| 20 | **Confirm Production file** | **Yes** | **Yes** | No | Sie prüfen nach der Zahlung die Produktionsdatei (Schritt 12). Aufpreis ablesen und notieren |
| 21 | **Mark on PCB** | **Remove Mark** | gleich | Remove Mark | **nicht** „2D barcode“ (würde irgendwo auf die Platine gesetzt, evtl. auf die Sonde) |
| 22 | Electrical Test | Flying Probe Fully Test | gleich | gleich | |
| 23 | Gold Fingers, Castellated Holes, Edge Plating, übrige Sonderoptionen | No | No | No | |
| 24 | Remark | Inhalt von `2_bestellung/REMARK_JLC_REV_C.txt` **wörtlich** einfügen (563 Zeichen) | gleich | – | Füllung aller 0.30-mm-Vias, Remove Mark. Wird der Text gekürzt: Projektleitung fragen |

**Feld nicht in der Tabelle** (z. B. Impedance Control, Package Box, UL Marking, Papier-/Verpackungsoptionen): Vorgabe
lassen und Screenshot machen; ändert das Feld den Preis oder ist es ein Pflichtfeld ohne Vorgabe → Projektleitung fragen.

Preis ablesen (PCB allein, noch ohne PCBA): Prototyp 5 Stk erwartet **65.21 USD**, Serie 20 Stk **76.30 USD**
(Engineering 25.00 + Via Covering 18.59 + Surface Finish 18.50 + Deburring 0.50 + Board 10.20 + Via Plating 3.51), jeweils
mit Confirm Production file = No. Mit „Yes“ den Unterschied notieren → ORDER Kap. 4 Nr. 3, 4, 6, 7.

## Schritt 5 – Bauzeit

Build Time: Standard (Screenshot: „3–4 days, 0.00“). Kein Express.

## Schritt 6 – Schalter „PCB Assembly“ einschalten (ab hier ANNAHME)

Der Schalter liegt unter den PCB-Feldern (Screenshot: aus). **Einschalten.** Danach erscheinen die Bestückungsfelder.
**Zuerst kontrollieren, ob Schritt 4 Nr. 16 noch auf „Epoxy Filled & Capped“ steht** (Stopp-Regel 1).

| Feld (ANNAHME) | Sollwert Prototyp | Sollwert Serie | Hinweis |
|---|---|---|---|
| PCBA Type | **Economic** | Economic | Ist „Economic“ ausgegraut oder erscheint „not supported“ → Stopp-Regel 2, ORDER Kap. 4 Nr. 5 „nein“ |
| Assembly Side | **Top Side** | Top Side | alle Bauteile oben |
| PCBA Qty | **5** | **16** | Serie: 15 Sensoren + 1 Reserve, 4 Platinen bleiben unbestückt. Ist 16 nicht wählbar: nächstgrössere Menge (z. B. 20), Mehrkosten notieren (≈ 4 × 5.53 USD JLC-Anteil je Board) und vor dem Bezahlen der Projektleitung melden |
| Tooling holes / Edge rails / Fiducials | nicht hinzufügen bzw. „Added by JLCPCB“, falls Pflichtfeld | gleich | Economic braucht keine (JLC PCBA Capabilities) |
| Confirm Parts Placement | **Yes** | Yes | 0.45 USD; Sie prüfen die Lage der Teile selbst (Schritt 8) |
| übrige Optionen (Programmierung, Coating, Paste/Stencil-Optionen, Packaging) | Vorgabe lassen / No | gleich | Programmierung und Coating gibt es nur bei Standard |

Screenshot dieser Felder ablegen → ORDER Kap. 4 Nr. 5 ankreuzen („ja“ oder „nein“). Bei „nein“ hier aufhören.

„Next“ (bzw. „Confirm“) → JLC zeigt die Platine noch einmal → „Next“.

## Schritt 7 – BOM und CPL hochladen, Bauteile zuordnen (ANNAHME zum Ablauf)

1. „Add BOM File“: **`fluidi_sensor_bom_jlc.csv`**; „Add CPL File“: **`fluidi_sensor_cpl_jlc.csv`**.
2. „Process BOM & CPL“ (o. ä.). JLC fragt evtl. nach der Spaltenzuordnung: Comment, Designator, Footprint,
   „LCSC Part #“ (BOM); Designator, Mid X, Mid Y, Layer, Rotation (CPL). Die Dateien haben genau diese Spaltennamen.
3. Bauteilliste kontrollieren (ORDER Kap. 4 Nr. 8 und 9, Bestand ORDER Kap. 7):
   - **26 Zeilen**, jede mit der LCSC-Nummer aus der BOM „matched“/ausgewählt, keine Zeile „not matched“ oder „shortfall“.
   - 10 Extended, 1 Preferred (C1552), 15 Basic.
   - **Bestand BT1 C5213768** notieren (2026-11-08 13:06: 629 Stk; nötig 5 bzw. 16).
   - Kein Teil mit „Do not place“ markieren. C19/C20 (DNM) sowie Testpads und Antenne sind gar nicht in der BOM –
     JLC meldet evtl. „Designator in CPL/Gerber not in BOM“ für diese: das ist richtig (Liste `fluidi_sensor_bom_extra.csv`).
   - Die Knopfzelle CR2032 kaufen Sie lokal (nicht bei JLC).
4. „Next“.

## Schritt 8 – Component Placements (Lage und Drehung prüfen)

JLC zeigt die Platine mit den Bauteilbildern. **Jetzt die Abhakliste ORDER Kap. 5 vollständig abarbeiten** (U1, U2, U3,
U4–U6, Q1, Q2, D1, Y1, BT1 einzeln; Kurzschlussfälle fett). Vergleichsbild: `production/rev-C/2_bestellung/fluidi_sensor_bestueckung_F.pdf`.
Pro Teil einen Screenshot.

**Feste Regel: nie selbst drehen.** Liegt ein Teil anders als in ORDER Kap. 5 oder ist die Lage unklar: Screenshot,
**nicht bezahlen**, Projektleitung fragen. Grund: Bei U1, U2, U3 und U4–U6 schliesst eine falsche Drehung die Zelle bzw.
GPIOs kurz (ORDER Kap. 5, fett).

**Der rote Punkt in der JLC-Vorschau ist nicht Pin 1.** JLC: „we do not call the red dot pin 1, but a marking only“
(PCBA-FAQ Teil 2, Q1, Stand Sep 09, 2026; `docs/references/JLCPCB_NOTES.md` Kap. 8). Pin 1 am Bauteilbild selbst
beurteilen: Fase, Kerbe oder Punkt auf dem Gehäuse, Kathodenmarke, Pad-Form.

Mit „Confirm Parts Placement = Yes“ prüft JLC zusätzlich vor der Fertigung und meldet sich per E-Mail. → ORDER Kap. 4 Nr. 10.

Erwartete Warnung (**ANNAHME**): Der Umriss von BT1 schliesst die Knopfzelle ein und ragt über die Platinenkante
(Clip selbst 1.3 mm innen, Pads ≥ 0.53 mm). Meldet JLC „component outside board“ o. ä. für BT1, ist das kein Fehler.

„Next“ → „Save to Cart“.

## Schritt 9 – Warenkorb

1. Im Warenkorb den Posten aufklappen und kontrollieren: PCB-Parameter wie Schritt 4, PCBA Economic, Menge, Remark.
2. Posten ablesen und notieren: Setup 8.18 USD, Stencil 1.53 USD, Extended-Gebühr 10 × 3.07 = 30.70 USD, Confirm Parts
   Placement 0.45 USD, X-ray (U1) 1.64 USD/Stk (Prototyp 8.20 USD), Bauteile ≈ 24 USD inkl. Mindestmengen (Prototyp, `phase5_kosten_final.md` Kap. 6).
   **Gibt es einen Posten „Pre-reflow Soldering“? → Stopp, nicht bezahlen, Projektleitung fragen.** (145 Lötstellen ×
   0.016 USD = 2.32 USD je Board; Prototyp +11.60 USD; Serie dann ≈ 10.60 CHF/Sensor statt 8.38 → Kostenziel < 10 CHF
   verfehlt, `docs/reviews/phase5_kosten_final.md` Kap. 2.1.)
3. „Secure Checkout“.

## Schritt 10 – Versand

1. Lieferadresse Schweiz wählen.
2. Versandart **DHL Express** (Screenshot: 23.52 USD, 2–4 Tage). „Global Standard Direct Line“ ist ab 65 USD Warenwert
   nicht zulässig (ORDER Kap. 4 Nr. 12).
3. Gewicht und DHL-Preis notieren (ohne Bestückung: 0.41 kg / 23.52 USD für 20 Stk). Mit Bestückung ist die Sendung
   schwerer (Serie geschätzt ≈ 0.55 kg); liegt sie über 0.5 kg, kann DHL einige USD teurer sein (ANNAHME, nicht abgelesen).
4. **Gesamtbetrag** vergleichen (ORDER Kap. 4 Nr. 11): Prototyp ≈ **163 USD**, Serie ≈ **220 USD** inkl. DHL.
5. Bei Ankunft verlangt DHL Express: MWST 8.1 % + 19 CHF Abwicklung + Vorlagegebühr max(3 CHF; 2 %) (ORDER Kap. 4 Nr. 12,
   Quelle DHL lokal). Zoll auf Leiterplatten: 0.

## Schritt 11 – Coupons und Bezahlung

1. Coupons: Der Screenshot zeigte 2 × „Save $20.00“. Im Checkout das Feld „Coupon“ öffnen und, falls ein Coupon für
   diese Bestellung gilt, anwenden. Die Bedingungen (Mindestbetrag, nur Neukunden, nur PCB/PCBA) sind nicht bekannt
   (**ANNAHME**); die Kostenrechnung zieht keinen Coupon ab.
2. Zahlungsart: JLC bietet „Pay Directly (recommended)“ und „Review Before Payment“. Empfehlung **Pay Directly**:
   JLC sagt „If your file cannot be approved for production after the review, you will receive a full refund“
   (`…HowToPlaceOrder_Auszug…`), und die Teile sind früher bestellt (**ANNAHME** zur Reservierung, wichtig wegen BT1).
3. Bezahlen, wenn möglich mit einer Karte **ohne Fremdwährungsgebühr** in USD (Modell: +1.5 %, ANNAHME). Umrechnung
   über PayPal ist meist teurer (ANNAHME, nicht geprüft; Wirkung < 3 CHF je Bestellung). Auftragsnummer notieren →
   ORDER Kap. 4 Nr. 13.

## Schritt 12 – Nach der Zahlung: Produktionsdatei bestätigen

JLC schickt eine E-Mail „confirm production file“ (`docs/references/JLCPCB_ConfirmProductionFile_Auszug_2026-11-08.txt`):
1. Konto → „Order History“ → „Confirm production file“ → **zuerst „download production file“**, nicht sofort bestätigen.
2. ZIP entpacken, Ordner **`ok`** mit einem Gerber-Viewer öffnen (z. B. KiCad Gerbview):
   - Lage **`sk`** (zu füllende Vias): alle 146 Bohrungen 0.30 mm, sicher die 8 Via-in-Pad (4 im U1-Pad, Clip-Pad,
     Minuspad, TP1, TP2).
   - Lage **`bo`** (Silkscreen unten): keine Auftragsnummer, kein Barcode, kein Text `JLCJLCJLCJLC`.
   - 4 Kupferlagen, Kontur, Sonde ohne Aussenkupfer.
3. Alles richtig → „Yes, please proceed to production“. Sonst „not good, modification needed“ mit kurzer Beschreibung
   und Projektleitung informieren. → ORDER Kap. 4 Nr. 2 (zweiter Teil).
4. „Confirm Parts Placement“: JLC meldet sich evtl. mit Bildern der Bauteillage; mit ORDER Kap. 5 vergleichen.

## Schritt 13 – Nach Lieferung

- Rechnung (PDF) und DHL-Abgabenbeleg ablegen, Beträge in `docs/reviews/phase5_kosten_final.md` nachtragen lassen.
- Bestätigte Rotationen als Projekttabelle festhalten (DFM K-3).
- **Vor dem ersten Einsetzen einer Zelle:** Verpoltest **ST-E2** (`docs/reviews/phase5_testplan_beitrag_sicherheit.md`):
  Labornetzteil 3.0 V, Strombegrenzung 10 mA, an der Dummy-Scheibe; erst richtig gepolt (Strom plausibel, keine
  Erwärmung), dann verpolt (≤ 1 µA). Erst wenn ST-E2 bestanden ist, eine Zelle einsetzen.
- Weitere Prototyp-Prüfungen: `docs/manuals/PROGRAMMIEREN_SENSOR.md`, Querschliff POFV (Auflage A-3).

## Serie (später)

Gleiche Schritte, Mengen aus der Spalte „Serie“ (20 PCB, 16 bestückt). Vorher: Ergebnis der Prototyp-Prüfungen,
Entscheid 2 oder 4 × 100 µF (D-013, BOM ändert sich dann), Bestand BT1 erneut prüfen.
