# Phase 5 – Kostenrechnung final (Sensor, Gateway, System)

| | |
|---|---|
| Stand | Sensor 2026-11-08, Vergussmasse 2026-11-09 (Kap. 2.0), Gateway 2026-11-09 (D-028/D-029), erzeugt von `.venv/bin/python scripts/cost_final_phase5.py` (nicht von Hand ändern) |
| Kurs | 1 USD = 0.8189 CHF, 2026-11-06 (EZB-Referenzkurs, Kreuzkurs); + 1.5 % Kartenaufschlag (ANNAHME) = 0.8312 CHF; 2026-11-08 ist ein Sonntag, neuester EZB-Kurs = 2026-11-06 |
| Sensor | `hardware/sensor/gen/cost_rev_b.py` → `scripts/cost_model.compute` (D-005), Teilepreise `docs/concepts/bom/jlc_prices.json` (Abruf 2026-11-07), Lager live 2026-11-08 13:06 (`order_check.py --live`) |
| Gateway | `hardware/gateway/BOM_GATEWAY.csv` (Preise pi-shop.ch/bastelgarage.ch, Abruf 2026-11-08/09, `docs/references/pi-shop_Gateway-Teile_Auszug_2026-11-08.txt`, `docs/references/Haendler_Einkauf_Auszug_2026-11-09.txt`; D-028/D-029) |
| Bestellunterlage | `hardware/sensor/out/ORDER_JLC_REV_C.md`, Anleitung `docs/manuals/BESTELLEN_JLC.md` |

## 0 Fazit

- **Stückkosten nach D-005** (REQ-FAB-04, Grenzkosten pro Sensor ohne Einmalkosten): Serie **8.31 CHF** → < 10 CHF erfüllt, **unter Vorbehalt**: Berechnet JLC „Pre-reflow Soldering“ (0.016 USD/Lötstelle), steigen sie auf **10.53 CHF** → REQ-FAB-04 **verfehlt** (Kap. 2.1, Stopp-Kriterium im Warenkorb).
- **Vollkosten** (ganze Bestellung inkl. Einmalkosten / Sensoren): Serie **20.17 CHF/Sensor**; mit Prototyp-Los und Gateway 55.07 CHF/Sensor (15 Sensoren). Das ist, was ein Sensor real kostet.
- D-005 (Definition Stückkosten) hat Status „zur Kenntnis“; der Auftraggeber sollte ausdrücklich bestätigen, dass REQ-FAB-04 die Stückkosten nach D-005 meint und nicht die Vollkosten.
- Gateway: kauffertig 41.86 CHF, offen/nicht lieferbar 27.90 CHF, geplant total 69.76 CHF.

## 1 Abgleich JLC-Screenshot ↔ Modell (Sensor-PCB, 2026-11-08)

| Position (Screenshot, 20 Stk) | USD |
|---|---|
| Engineering fee | 25.00 |
| Via Covering (Epoxy Filled & Capped) | 18.59 |
| Surface Finish (ENIG 1 U") | 18.50 |
| Deburring/Edge rounding | 0.50 |
| Board | 10.20 |
| Via Plating Method (Horizontal Electroless Copper Plating) | 3.51 |
| **Summe = Web Price** | **76.30** |

| Grösse | Screenshot | Modell | Ergebnis |
|---|---|---|---|
| PCB 20 Stk | 76.30 USD | `QUOTE_USD[20]` = 76.30 USD | gleich |
| PCB 5 Stk | nicht im Screenshot | 65.21 USD (Angebot 2026-11-08, CLIENT_INPUT) | am Bestelltag ablesen |
| DHL Express | 23.52 USD | `SHIPPING_USD['DHL']` = 23.52 USD (bis 2026-11-07: 23.44) | nachgeführt (+0.08 USD) |
| Gewicht | 0.41 kg (20 PCB, unbestückt) | 0.55 kg (ANNAHME, nur Info) | Modell konservativ; Preis pauschal angenommen |
| Confirm Production File | No (Screenshot) | Soll **Yes** (ORDER Kap. 2) | Preis nicht belegt → **ANNAHME 0 USD**, am Bestelltag ablesen |
| Deburring/Edge rounding | Yes, 0.50 USD | im PCB-Preis | JLC: Pflicht-Aufpreis für Platinen mit einer Seite 1.5–3 cm (0.02 USD/Stk, `docs/references/JLCPCB_ExtraCharges_Auszug_2026-11-08.txt` Nr. 6) |
| Coupons | 2 × „Save $20.00“ | nicht abgezogen | Bedingungen unbekannt (ANNAHME); je Coupon −17.95 CHF |

Die Aufschlüsselung bestätigt die Modellannahme D-005: Fixanteil (Engineering 25.00 + Via Covering + ENIG + Via Plating) dominiert, die Platine selbst kostet 10.20 USD für 20 Stück.

## 2 Sensor

| Szenario | PCBA | Stück CHF (D-005) | Einmal CHF | Bestellung total CHF | Vollkosten/Sensor CHF | JLC-Rechnung USD |
|---|---|---|---|---|---|---|
| Prototyp 5 PCB / 5 bestückt (4 × 100 µF) | economic | **9.15** | 178.90 | 224.66 | 44.93 | 163.23 |
| Serie 20 PCB / 16 bestückt / 15 Sensoren (4 × 100 µF) | economic | **8.31** | 177.94 | 302.57 | 20.17 | 220.33 |
| Serie 20 PCB / 16 bestückt / 15 Sensoren (2 × 100 µF) | economic | **8.09** | 177.94 | 299.35 | 19.96 | 216.74 |
| ALT Standard-PCBA Serie 7 Paneele = 21 PCB / 18 bestückt / 15 Sensoren | standard | **9.24** | 222.22 | 360.79 | 24.05 | 285.20 |
| ALT Standard-PCBA Prototyp 2 Paneele = 6 PCB / 6 bestückt / 5 Sensoren | standard | **10.65** | 223.82 | 277.05 | 55.41 | 221.61 |

REQ-FAB-04 (< 10 CHF Stückkosten bei 10–15 Stück, D-005): Serie **8.31 CHF** (4 × 100 µF) bzw. **8.09 CHF** (2 × 100 µF) → **erfüllt unter Vorbehalt** „Pre-reflow Soldering“ (falls berechnet: 10.53 CHF, **verfehlt**, Kap. 2.1); mit Standard-PCBA 9.24 CHF (erfüllt, Paneelpreis ANNAHME).

### 2.0 Vergussmasse (Phase 6, D-030-Vorschlag, Variante M-A)

Electrolube ER2223 Resin Pack 250 g, Simpex CH CHF 38.20 exkl. MWST = **41.29 CHF** inkl. MWST (Abruf 2026-11-08). Variante M-A (abfüllen, 8-g-Ansätze wägen, `docs/manuals/MONTAGE_SENSOR.md` Kap. 3a): **1 Beutel je Bestellung** (angebrochen max. 3 Monate, ANNAHME). Stückkosten = Verbrauch 2 g/Sensor = 0.33 CHF (+5 % Ausschuss); Einmalkosten = Beutelrest (Prototyp 39.56, Serie 36.09 CHF), Einordnung nach D-005 durch den Orchestrator. Zubehör/Schutzausrüstung einmalig je Projekt **229.00 CHF** (ANNAHME-Preise, in der Systemsumme Kap. 4). Hinweis M-B (ganzer Beutel je Sitzung): Prototyp 3 + Serie 3 Beutel = 247.74 CHF statt 82.58 CHF.

### 2.1 Versteckte Kosten und Empfindlichkeiten

| Punkt | Wirkung | Behandlung |
|---|---|---|
| Extended-Gebühr je Teiletyp | 10 × 3.07 = 30.70 USD je Bestellung | im Modell (Einmalkosten) |
| Mindestabnahmen/Verlust LCSC | Prototyp 3.13 / Serie 2.97 USD | im Modell (Einmalkosten) |
| Ausschuss lokale Teile | 5 % (ANNAHME) | im Modell |
| Reserveboard Serie | 16 bestückt für 15 Sensoren | im Modell (Stückkosten × 16/15) |
| „Pre-reflow Soldering“ 0.016 USD/Lötstelle (JLC-Preisseite, Anwendung nicht erklärt) – Prototyp 5 PCB / 5 bestückt (4 × 100 µF) | +10.41 CHF je Bestellung, Stückkosten 9.15 → **11.23 CHF** (D-005: pro Lötstelle = Stückkosten) | **nicht** im Modell; **Stopp-Kriterium** im Warenkorb (Anleitung Schritt 9, ORDER Kap. 4 Nr. 11) |
| „Pre-reflow Soldering“ 0.016 USD/Lötstelle (JLC-Preisseite, Anwendung nicht erklärt) – Serie 20 PCB / 16 bestückt / 15 Sensoren (4 × 100 µF) | +33.32 CHF je Bestellung, Stückkosten 8.31 → **10.53 CHF** (D-005: pro Lötstelle = Stückkosten) | **nicht** im Modell; **Stopp-Kriterium** im Warenkorb (Anleitung Schritt 9, ORDER Kap. 4 Nr. 11) |
| Confirm Production File = Yes | Preis unbekannt | ANNAHME 0 USD, am Bestelltag ablesen |
| Coupons 2 × 20 USD | bis −35.90 CHF | nicht abgezogen (Bedingungen unbekannt) |
| Lager BT1 C5213768 (629 Stk, sinkend) | Ausfall → Ersatzteil/Layout | Bestand am Bestelltag prüfen |
| Verzollung DHL | 19 CHF + max(3 CHF; 2 %) je Sendung (K-2) | im Modell |
| Versand mit PCBA | Serie geschätzt ≈ 0.55 kg; DHL-Stufe über 0.5 kg evtl. einige USD teurer (ANNAHME) | pauschal 23.52 USD; im 10-%-Stoppkriterium enthalten |
| Zahlungsweg | Modell +1.5 % (ANNAHME); PayPal-Umrechnung meist teurer (ANNAHME, < 3 CHF je Bestellung) | Karte ohne Fremdwährungsgebühr empfohlen |

## 3 Gateway (W-8, REQ-FAB-06 separat ausgewiesen)

Stand Phase 6 (2026-11-09): **D-028** Gateway ohne RTC (G4 PiRTC DS3231 und G5 CR1220 gestrichen, Zeit per NTP, Rückfall `phase5_gateway_zeit.md`); **D-029** Klimasensor = DFRobot Fermion SHT40 SEN0428 (14 × 17 mm, passt in die Klimakammer; Auswahl und Belege `docs/manuals/EINKAUFSLISTE.md` Kap. 2). Bezugsquellen und Versand: Einkaufsliste.

| Pos | Teil | Typ | Menge | CHF/Stk | Summe CHF | Status | Lager (Abruf) | Quelle |
|---|---|---|---|---|---|---|---|---|
| G1 | Einplatinenrechner Gateway (D-014) | Raspberry Pi Zero 2 W | 1 | 17.15 | 17.15 | vorhanden | nicht an Lager | pi-shop.ch |
| G2 | Netzteil 5 V 2.5 A Micro-USB (REQ-SAF-DOC-02 gepruefte Speisung) | Raspberry Pi Ltd, Original 12.5 W Micro-USB Steckernetzteil | 1 | 11.90 | 11.90 | kauffertig | Sofort-Versand ab Lager | pi-shop.ch |
| G3 | microSD Industrial 16 GB (Stromausfall/Schreibzyklen, ARCHITECTURE Kap. 14.4) | Kingston SDCIT2/16GB (microSDHC Industrial UHS-I 16 GB, pSLC) | 1 | 27.90 | 27.90 | nicht an Lager | nicht an Lager | pi-shop.ch |
| G6 | Raumklima-Sensor-Breakout (D-017/D-029, SHT40 an I2C 0x44) | DFRobot Fermion SHT40 Breakout (SEN0428) | 1 | 11.90 | 11.90 | kauffertig | Lagernd | bastelgarage.ch Art. 421989 |
| G7 | Gehaeuse G1 v4 ASA (Wanne grau + Deckel blau + Fenster) | Eigendruck Bambu (mechanical/gateway_pi/print) | 1 | 0.97 | 0.97 | Eigenfertigung | - | ANNAHME ASA 0.035 CHF/g (scripts/concept_costs.py ASA_CHF_PER_G) |
| G8 | Gewindeeinsaetze M2.5 (4) + Schrauben M2.5 x 8 ISO 7380 (4) | Handelsware | 1 | 2.00 | 2.00 | kauffertig | - | ANNAHME (kein Angebot abgefragt) |
| G9 | Status-LED Gateway (D-027 vorlaeufig): 3-mm-LED gruen + Vorwiderstand 470 Ohm an GPIO17, ohne Platine | Kingbright WP710A10GD + YAGEO MFR-25FBF52-470R | 1 | 0.29 | 0.29 | kauffertig | 24503 / 19960 | Digi-Key CH 0.20 + 0.09 (docs/reviews/phase5_gateway_led.md Kap. 4) |
| G10 | Litze AWG 28, Schrumpfschlauch | Werkstattbestand | 1 | 0.00 | 0.00 | vorhanden | - | ANNAHME |
| G11 | Zusatz-BLE-Empfaenger (nur falls Koexistenz W-7 nicht genuegt) | Seeed XIAO nRF52840 Sense | 1 | 0.00 | 0.00 | vorhanden (optional) | - | - |
| V1 | Versand pi-shop.ch (B-Post Economy, Sammelbestellung G2, G3, Werkstatt) | Schweizer Post | 1 | 7.90 | 7.90 | kauffertig | - | pi-shop.ch |
| V2 | Versand bastelgarage.ch (PostPac Economy, entfaellt ab CHF 80 Warenwert der Sammelbestellung, docs/manuals/EINKAUFSLISTE.md) | Schweizer Post | 1 | 6.90 | 6.90 | kauffertig | - | bastelgarage.ch |

- **Kauffertig: 41.86 CHF** (Netzteil, SHT40-Breakout, Status-LED, Schrauben/Einsätze, Gehäusedruck, Versand pi-shop.ch und bastelgarage.ch), davon 2.97 CHF ANNAHME. **Noch nicht kaufbar: 27.90 CHF** (G3 microSD Industrial bei pi-shop.ch nicht an Lager; Alternative gleicher Serie sofort lieferbar, aber 56.95–63.95 CHF, Einkaufsliste). Geplant total 69.76 CHF (Systemsumme rechnet damit).
- Neuwert inkl. Pi Zero 2 W: 86.91 CHF.
- Offen, nicht enthalten: .
- Nicht an Lager (pi-shop.ch 2026-11-09): Pi Zero 2 W (vorhanden, nicht nötig), microSD Industrial (G3).

## 4 System (15 Sensoren + Gateway)

| Weg | Inhalt | CHF |
|---|---|---|
| A: direkt Serie | Serie 20 PCB / 16 bestückt / 15 Sensoren + Gateway (geplant total) | **601.33** |
| B: Prototyp + Serie (geplant) | Prototyp 5 + Serie 15 Sensoren + Gateway (geplant total) | **825.99** |
| davon Verguss-Zubehör/Schutz (A und B je einmal) | Kap. 2.0, ANNAHME-Preise | 229.00 |
| B + Programmieradapter | wie B + Adapter Rev 1 (25–55 CHF, ANNAHME) | 850.99 – 880.99 |

- Pro Sensor (Weg A, inkl. Gateway-Anteil): 40.09 CHF; Weg B: 55.07 CHF (die 5 Prototypen sind zusätzlich nutzbar, falls sie die Prüfungen bestehen → dann 20 Sensoren: 41.30 CHF).
- Nicht enthalten: Arbeitszeit, Werkzeug (ausser Verguss-Zubehör Kap. 2.0), Dichtmittel über die Sensor-Pauschalen hinaus, Status-LED-Platine Gateway, Ersatzzellen.

## 5 Annahmen und offene Punkte

- PCB 5 Stk (65.21 USD) stammt aus dem Angebot vom 2026-11-08 (CLIENT_INPUT), nicht aus dem Screenshot.
- Economic PCBA + ENIG + POFV + 4 Lagen: JLC-Doku sagt dazu nichts (`docs/references/JLCPCB_NOTES.md` Kap. 10) → BESTELL-PRÜFUNG; Ausweichen auf Standard-PCBA kostet Serie +58.22 CHF je Bestellung.
- Versandpreis mit PCBA (Gewicht höher) erst am Checkout sichtbar (ANNAHME pauschal 23.52 USD).
- Gateway: Netzteil-Konformität nicht lokal (Sicherheits-Agent beim Wareneingang); microSD-Datenblatt (`Kingston_SDCIT2_Datasheet_MKD-02122026.pdf`) und SHT40-Breakout-Schaltplan/Masse (`DFRobot_SEN0428_*`) seit 2026-11-09 lokal; RTC/CR1220 entfallen (D-028). Klimakammer: Nutpfosten auf 17 mm Modulbreite nachführen (Mechanik).

## 6 Einzelposten Sensor (cost_model.report)

```
=== Prototyp 5 PCB / 5 bestückt (4 × 100 µF) ===
4 Lagen, 1.6 mm, PCB 5 Stk, bestueckt 5 Stk, nutzbare Sensoren 5, PCBA economic, Versand DHL, Gewicht ca. 0.25 kg [ANNAHME]
  JLC-Anteil pro bestuecktem Board (USD):
    PCB Grenzkosten pro Platine                              0.74
    Bauteile JLC/LCSC                                        4.23
    SMT-Bestueckung                                          0.23
    Roentgen (1 leadless/Board)                              1.64
    Summe JLC-Anteil                                         6.84 USD
    + MWST-Anteil CH                                         0.45 CHF
    = JLC-Anteil pro Board                                   6.14 CHF
    x Boards / Sensoren                                  5/5
    + lokal beschaffte Teile inkl. Ausschuss                 3.01 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        9.15 CHF
  Einmalkosten pro Bestellung (USD):
    PCB Fixanteil pro Bestellung (D-005)                    61.51
    Bauteile Mindestabnahme/Verlust-Ueberschuss              3.13
    PCBA Setup                                               8.18
    Schablone                                                1.53
    Feeder/Extended (10 ext., 1 pref., 15 basic Typen)      30.70
    Confirm Parts Placement                                  0.45
    Versand DHL                                             23.52
    Summe JLC-Rechnung einmalig                            129.02 USD
    + MWST-Anteil CH (einmalig)                             10.10 CHF
    + Verzollungsgebuehr Kurier/Post                        22.00 CHF
    = EINMALKOSTEN                                         178.90 CHF
  JLC-Rechnung total 163.23 USD = 133.67 CHF; MWST 12.37 CHF; Bestellung total 224.66 CHF; VOLLKOSTEN pro Sensor 44.93 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 139.71 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
  Hinweis: EINMALKOSTEN enthalten lokal Vergussmasse ER2223 (1 Beutel 41.29 CHF minus Verbrauch in den Stueckkosten) = 39.56 CHF
```

```
=== Serie 20 PCB / 16 bestückt / 15 Sensoren (4 × 100 µF) ===
4 Lagen, 1.6 mm, PCB 20 Stk, bestueckt 16 Stk, nutzbare Sensoren 15, PCBA economic, Versand DHL, Gewicht ca. 0.55 kg [ANNAHME]
  JLC-Anteil pro bestuecktem Board (USD):
    PCB Grenzkosten pro Platine                              0.74
    Bauteile JLC/LCSC                                        3.74
    SMT-Bestueckung                                          0.23
    Roentgen (1 leadless/Board)                              0.82
    Summe JLC-Anteil                                         5.53 USD
    + MWST-Anteil CH                                         0.37 CHF
    = JLC-Anteil pro Board                                   4.96 CHF
    x Boards / Sensoren                                  16/15
    + lokal beschaffte Teile inkl. Ausschuss                 3.01 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        8.31 CHF
  Einmalkosten pro Bestellung (USD):
    PCB Fixanteil pro Bestellung (D-005)                    61.51
    PCB unbestueckte Reserveplatinen                         2.96
    Bauteile Mindestabnahme/Verlust-Ueberschuss              2.97
    PCBA Setup                                               8.18
    Schablone                                                1.53
    Feeder/Extended (10 ext., 1 pref., 15 basic Typen)      30.70
    Confirm Parts Placement                                  0.45
    Versand DHL                                             23.52
    Summe JLC-Rechnung einmalig                            131.82 USD
    + MWST-Anteil CH (einmalig)                             10.28 CHF
    + Verzollungsgebuehr Kurier/Post                        22.00 CHF
    = EINMALKOSTEN                                         177.94 CHF
  JLC-Rechnung total 220.33 USD = 180.43 CHF; MWST 16.15 CHF; Bestellung total 302.57 CHF; VOLLKOSTEN pro Sensor 20.17 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 196.81 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
  Hinweis: EINMALKOSTEN enthalten lokal Vergussmasse ER2223 (1 Beutel 41.29 CHF minus Verbrauch in den Stueckkosten) = 36.09 CHF
```

```
=== Serie 20 PCB / 16 bestückt / 15 Sensoren (2 × 100 µF) ===
4 Lagen, 1.6 mm, PCB 20 Stk, bestueckt 16 Stk, nutzbare Sensoren 15, PCBA economic, Versand DHL, Gewicht ca. 0.55 kg [ANNAHME]
  JLC-Anteil pro bestuecktem Board (USD):
    PCB Grenzkosten pro Platine                              0.74
    Bauteile JLC/LCSC                                        3.52
    SMT-Bestueckung                                          0.23
    Roentgen (1 leadless/Board)                              0.82
    Summe JLC-Anteil                                         5.31 USD
    + MWST-Anteil CH                                         0.35 CHF
    = JLC-Anteil pro Board                                   4.76 CHF
    x Boards / Sensoren                                  16/15
    + lokal beschaffte Teile inkl. Ausschuss                 3.01 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        8.09 CHF
  Einmalkosten pro Bestellung (USD):
    PCB Fixanteil pro Bestellung (D-005)                    61.51
    PCB unbestueckte Reserveplatinen                         2.96
    Bauteile Mindestabnahme/Verlust-Ueberschuss              2.97
    PCBA Setup                                               8.18
    Schablone                                                1.53
    Feeder/Extended (10 ext., 1 pref., 15 basic Typen)      30.70
    Confirm Parts Placement                                  0.45
    Versand DHL                                             23.52
    Summe JLC-Rechnung einmalig                            131.82 USD
    + MWST-Anteil CH (einmalig)                             10.28 CHF
    + Verzollungsgebuehr Kurier/Post                        22.00 CHF
    = EINMALKOSTEN                                         177.94 CHF
  JLC-Rechnung total 216.74 USD = 177.49 CHF; MWST 15.92 CHF; Bestellung total 299.35 CHF; VOLLKOSTEN pro Sensor 19.96 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 193.22 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
  Hinweis: EINMALKOSTEN enthalten lokal Vergussmasse ER2223 (1 Beutel 41.29 CHF minus Verbrauch in den Stueckkosten) = 36.09 CHF
```

```
=== ALT Standard-PCBA Serie 7 Paneele = 21 PCB / 18 bestückt / 15 Sensoren ===
4 Lagen, 1.6 mm, PCB 21 Stk, bestueckt 18 Stk, nutzbare Sensoren 15, PCBA standard, Versand DHL, Gewicht ca. 0.57 kg [ANNAHME]
  JLC-Anteil pro bestuecktem Board (USD):
    PCB Grenzkosten pro Platine                              0.74
    Bauteile JLC/LCSC                                        3.74
    SMT-Bestueckung                                          0.48
    Roentgen (1 leadless/Board)                              0.82
    Summe JLC-Anteil                                         5.78 USD
    + MWST-Anteil CH                                         0.38 CHF
    = JLC-Anteil pro Board                                   5.19 CHF
    x Boards / Sensoren                                  18/15
    + lokal beschaffte Teile inkl. Ausschuss                 3.01 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        9.24 CHF
  Einmalkosten pro Bestellung (USD):
    PCB Fixanteil pro Bestellung (D-005)                    61.51
    PCB unbestueckte Reserveplatinen                         2.22
    Bauteile Mindestabnahme/Verlust-Ueberschuss              2.97
    PCBA Setup                                              25.56
    Schablone                                                8.21
    Feeder/Extended (10 ext., 1 pref., 15 basic Typen)      39.78
    Confirm Parts Placement                                  0.45
    Fixture                                                 16.42
    Verpackung (Standard)                                    0.52
    Versand DHL                                             23.52
    Summe JLC-Rechnung einmalig                            181.16 USD
    + MWST-Anteil CH (einmalig)                             13.56 CHF
    + Verzollungsgebuehr Kurier/Post                        22.00 CHF
    = EINMALKOSTEN                                         222.22 CHF
  JLC-Rechnung total 285.20 USD = 233.55 CHF; MWST 20.46 CHF; Bestellung total 360.79 CHF; VOLLKOSTEN pro Sensor 24.05 CHF
  Hinweis: Standard-PCBA: min. 70x70 mm -> Panel (z. B. 3-fach + Raender) noetig; Panelpreis im Rechner pruefen [ANNAHME: hier nicht modelliert].
  Hinweis: GSDL nicht zulaessig (Warenwert 261.68 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
  Hinweis: EINMALKOSTEN enthalten lokal Vergussmasse ER2223 (1 Beutel 41.29 CHF minus Verbrauch in den Stueckkosten) = 36.09 CHF
```

```
=== ALT Standard-PCBA Prototyp 2 Paneele = 6 PCB / 6 bestückt / 5 Sensoren ===
4 Lagen, 1.6 mm, PCB 6 Stk, bestueckt 6 Stk, nutzbare Sensoren 5, PCBA standard, Versand DHL, Gewicht ca. 0.27 kg [ANNAHME]
  JLC-Anteil pro bestuecktem Board (USD):
    PCB Grenzkosten pro Platine                              0.74
    Bauteile JLC/LCSC                                        4.23
    SMT-Bestueckung                                          0.48
    Roentgen (1 leadless/Board)                              1.64
    Summe JLC-Anteil                                         7.09 USD
    + MWST-Anteil CH                                         0.47 CHF
    = JLC-Anteil pro Board                                   6.36 CHF
    x Boards / Sensoren                                  6/5
    + lokal beschaffte Teile inkl. Ausschuss                 3.01 CHF
    = STUECKKOSTEN pro Sensor (D-005)                       10.65 CHF
  Einmalkosten pro Bestellung (USD):
    PCB Fixanteil pro Bestellung (D-005)                    61.51
    Bauteile Mindestabnahme/Verlust-Ueberschuss              3.11
    PCBA Setup                                              25.56
    Schablone                                                8.21
    Feeder/Extended (10 ext., 1 pref., 15 basic Typen)      39.78
    Confirm Parts Placement                                  0.45
    Fixture                                                 16.42
    Verpackung (Standard)                                    0.51
    Versand DHL                                             23.52
    Summe JLC-Rechnung einmalig                            179.07 USD
    + MWST-Anteil CH (einmalig)                             13.42 CHF
    + Verzollungsgebuehr Kurier/Post                        22.00 CHF
    = EINMALKOSTEN                                         223.82 CHF
  JLC-Rechnung total 221.61 USD = 181.47 CHF; MWST 16.24 CHF; Bestellung total 277.05 CHF; VOLLKOSTEN pro Sensor 55.41 CHF
  Hinweis: Standard-PCBA: min. 70x70 mm -> Panel (z. B. 3-fach + Raender) noetig; Panelpreis im Rechner pruefen [ANNAHME: hier nicht modelliert].
  Hinweis: GSDL nicht zulaessig (Warenwert 198.09 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
  Hinweis: EINMALKOSTEN enthalten lokal Vergussmasse ER2223 (1 Beutel 41.29 CHF minus Verbrauch in den Stueckkosten) = 39.56 CHF
```

