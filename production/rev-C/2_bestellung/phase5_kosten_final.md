# Phase 5 – Kostenrechnung final (Sensor, Gateway, System)

| | |
|---|---|
| Stand | 2026-11-08, erzeugt von `.venv/bin/python scripts/cost_final_phase5.py` (nicht von Hand ändern) |
| Kurs | 1 USD = 0.8189 CHF, 2026-11-06 (EZB-Referenzkurs, Kreuzkurs); + 1.5 % Kartenaufschlag (ANNAHME) = 0.8312 CHF; 2026-11-08 ist ein Sonntag, neuester EZB-Kurs = 2026-11-06 |
| Sensor | `hardware/sensor/gen/cost_rev_b.py` → `scripts/cost_model.compute` (D-005), Teilepreise `docs/concepts/bom/jlc_prices.json` (Abruf 2026-11-07), Lager live 2026-11-08 13:06 (`order_check.py --live`) |
| Gateway | `hardware/gateway/BOM_GATEWAY.csv` (Preise pi-shop.ch, Abruf 2026-11-08, `docs/references/pi-shop_Gateway-Teile_Auszug_2026-11-08.txt`) |
| Bestellunterlage | `hardware/sensor/out/ORDER_JLC_REV_C.md`, Anleitung `docs/manuals/BESTELLEN_JLC.md` |

## 0 Fazit

- **Stückkosten nach D-005** (REQ-FAB-04, Grenzkosten pro Sensor ohne Einmalkosten): Serie **8.38 CHF** → < 10 CHF erfüllt, **unter Vorbehalt**: Berechnet JLC „Pre-reflow Soldering“ (0.016 USD/Lötstelle), steigen sie auf **10.60 CHF** → REQ-FAB-04 **verfehlt** (Kap. 2.1, Stopp-Kriterium im Warenkorb).
- **Vollkosten** (ganze Bestellung inkl. Einmalkosten / Sensoren): Serie **17.84 CHF/Sensor**; mit Prototyp-Los und Gateway 35.63 CHF/Sensor (15 Sensoren). Das ist, was ein Sensor real kostet.
- D-005 (Definition Stückkosten) hat Status „zur Kenntnis“; der Auftraggeber sollte ausdrücklich bestätigen, dass REQ-FAB-04 die Stückkosten nach D-005 meint und nicht die Vollkosten.
- Gateway: kauffertig 22.77 CHF, offen/nicht lieferbar 58.70 CHF, geplant total 81.47 CHF.

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
| Prototyp 5 PCB / 5 bestückt (4 × 100 µF) | economic | **9.23** | 139.34 | 185.47 | 37.09 | 163.23 |
| Serie 20 PCB / 16 bestückt / 15 Sensoren (4 × 100 µF) | economic | **8.38** | 141.85 | 267.58 | 17.84 | 220.33 |
| Serie 20 PCB / 16 bestückt / 15 Sensoren (2 × 100 µF) | economic | **8.17** | 141.85 | 264.36 | 17.62 | 216.74 |
| ALT Standard-PCBA Serie 7 Paneele = 21 PCB / 18 bestückt / 15 Sensoren | standard | **9.31** | 186.13 | 325.80 | 21.72 | 285.20 |
| ALT Standard-PCBA Prototyp 2 Paneele = 6 PCB / 6 bestückt / 5 Sensoren | standard | **10.72** | 184.26 | 237.86 | 47.57 | 221.61 |

REQ-FAB-04 (< 10 CHF Stückkosten bei 10–15 Stück, D-005): Serie **8.38 CHF** (4 × 100 µF) bzw. **8.17 CHF** (2 × 100 µF) → **erfüllt unter Vorbehalt** „Pre-reflow Soldering“ (falls berechnet: 10.60 CHF, **verfehlt**, Kap. 2.1); mit Standard-PCBA 9.31 CHF (erfüllt, Paneelpreis ANNAHME).

### 2.1 Versteckte Kosten und Empfindlichkeiten

| Punkt | Wirkung | Behandlung |
|---|---|---|
| Extended-Gebühr je Teiletyp | 10 × 3.07 = 30.70 USD je Bestellung | im Modell (Einmalkosten) |
| Mindestabnahmen/Verlust LCSC | Prototyp 3.13 / Serie 2.97 USD | im Modell (Einmalkosten) |
| Ausschuss lokale Teile | 5 % (ANNAHME) | im Modell |
| Reserveboard Serie | 16 bestückt für 15 Sensoren | im Modell (Stückkosten × 16/15) |
| „Pre-reflow Soldering“ 0.016 USD/Lötstelle (JLC-Preisseite, Anwendung nicht erklärt) – Prototyp 5 PCB / 5 bestückt (4 × 100 µF) | +10.41 CHF je Bestellung, Stückkosten 9.23 → **11.31 CHF** (D-005: pro Lötstelle = Stückkosten) | **nicht** im Modell; **Stopp-Kriterium** im Warenkorb (Anleitung Schritt 9, ORDER Kap. 4 Nr. 11) |
| „Pre-reflow Soldering“ 0.016 USD/Lötstelle (JLC-Preisseite, Anwendung nicht erklärt) – Serie 20 PCB / 16 bestückt / 15 Sensoren (4 × 100 µF) | +33.32 CHF je Bestellung, Stückkosten 8.38 → **10.60 CHF** (D-005: pro Lötstelle = Stückkosten) | **nicht** im Modell; **Stopp-Kriterium** im Warenkorb (Anleitung Schritt 9, ORDER Kap. 4 Nr. 11) |
| Confirm Production File = Yes | Preis unbekannt | ANNAHME 0 USD, am Bestelltag ablesen |
| Coupons 2 × 20 USD | bis −35.90 CHF | nicht abgezogen (Bedingungen unbekannt) |
| Lager BT1 C5213768 (629 Stk, sinkend) | Ausfall → Ersatzteil/Layout | Bestand am Bestelltag prüfen |
| Verzollung DHL | 19 CHF + max(3 CHF; 2 %) je Sendung (K-2) | im Modell |
| Versand mit PCBA | Serie geschätzt ≈ 0.55 kg; DHL-Stufe über 0.5 kg evtl. einige USD teurer (ANNAHME) | pauschal 23.52 USD; im 10-%-Stoppkriterium enthalten |
| Zahlungsweg | Modell +1.5 % (ANNAHME); PayPal-Umrechnung meist teurer (ANNAHME, < 3 CHF je Bestellung) | Karte ohne Fremdwährungsgebühr empfohlen |

## 3 Gateway (W-8, REQ-FAB-06 separat ausgewiesen)

RTC-Entscheid (Vorschlag, OP-GW-3): **Adafruit PiRTC Precise DS3231** mit CR1220-Primärzelle. Belege: DS3231 ±2 ppm 0–40 °C (`docs/datasheets/Maxim_DS3231_Datasheet_19-5170Rev10.pdf` S. 1) ≙ 5 s/Monat (REQ-GW-09 ±2 min/Monat); Pufferstrom IBATT ≤ 3.0 µA (S. 3) → ≥ 24 h Haltezeit weit erfüllt; **kein Ladepfad**: VBAT nur Zelle + IC (`hardware/gateway/check_rtc_schematic.py` auf dem Adafruit-Schaltplan), VBAT-Pin UL-anerkannt gegen Rückladung einer Lithium-Primärzelle (S. 9). Linux-Treiber: `dtoverlay=i2c-rtc,ds3231` (`docs/appnotes/Adafruit_AddingRTC-RaspberryPi_Guide_2026-04-07.pdf`).

| Pos | Teil | Typ | Menge | CHF/Stk | Summe CHF | Status | Lager (Abruf) | Quelle |
|---|---|---|---|---|---|---|---|---|
| G1 | Einplatinenrechner Gateway (D-014) | Raspberry Pi Zero 2 W | 1 | 17.15 | 17.15 | vorhanden | nicht an Lager | pi-shop.ch |
| G2 | Netzteil 5 V 2.5 A Micro-USB (REQ-SAF-DOC-02 gepruefte Speisung) | Raspberry Pi Ltd, Original 12.5 W Micro-USB Steckernetzteil | 1 | 11.90 | 11.90 | kauffertig | Sofort-Versand ab Lager | pi-shop.ch |
| G3 | microSD Industrial 16 GB (Stromausfall/Schreibzyklen, ARCHITECTURE Kap. 14.4) | Kingston microSDHC Industrial UHS-I 16 GB | 1 | 27.90 | 27.90 | nicht an Lager | nicht an Lager | pi-shop.ch |
| G4 | Echtzeituhr mit Pufferung ohne Ladepfad (REQ-GW-09, OP-GW-3, W-8) | Adafruit PiRTC Precise DS3231 (Adafruit 4282) | 1 | 18.90 | 18.90 | Entscheid offen | Sofort-Versand ab Lager | pi-shop.ch |
| G5 | Pufferzelle RTC (Primaerzelle, nicht wiederaufladbar) | CR1220 Lithium 3 V (Hersteller offen) | 1 | 3.00 | 3.00 | Entscheid offen | - | ANNAHME (kein Angebot abgefragt, pi-shop.ch fuehrt keine CR1220, Suche 2026-11-08) |
| G6 | Raumklima-Sensor-Breakout (D-017, SHT4x an I2C 0x44) | Seeed Grove SHT41 (Grove-SHT4x) | 1 | 8.90 | 8.90 | Entscheid offen | nicht an Lager | pi-shop.ch |
| G7 | Gehaeuse G1 v4 ASA (Wanne grau + Deckel blau + Fenster) | Eigendruck Bambu (mechanical/gateway_pi/print) | 1 | 0.97 | 0.97 | Eigenfertigung | - | ANNAHME ASA 0.035 CHF/g (scripts/concept_costs.py ASA_CHF_PER_G) |
| G8 | Gewindeeinsaetze M2.5 (4) + Schrauben M2.5 x 8 ISO 7380 (4) | Handelsware | 1 | 2.00 | 2.00 | kauffertig | - | ANNAHME (kein Angebot abgefragt) |
| G9 | Status-LED-Platine 8 x 8.2 mm (RGB wie Sensor) | nicht entworfen | 1 | 0.00 | 0.00 | offen | - | - |
| G10 | Litze AWG 28, Schrumpfschlauch | Werkstattbestand | 1 | 0.00 | 0.00 | vorhanden | - | ANNAHME |
| G11 | Zusatz-BLE-Empfaenger (nur falls Koexistenz W-7 nicht genuegt) | Seeed XIAO nRF52840 Sense | 1 | 0.00 | 0.00 | vorhanden (optional) | - | - |
| V1 | Versand pi-shop.ch (B-Post Economy) | Schweizer Post | 1 | 7.90 | 7.90 | kauffertig | - | pi-shop.ch |

- **Kauffertig: 22.77 CHF** (Netzteil, Schrauben/Einsätze, Gehäusedruck, Versand), davon 2.97 CHF ANNAHME. **Noch nicht kaufen: 58.70 CHF** (G4/G5 RTC-Montage ohne Buchsenleiste offen, G6 SHT41-Variante a/b/c offen, G3 microSD nicht an Lager). Geplant total 81.47 CHF (Systemsumme rechnet damit).
- Neuwert inkl. Pi Zero 2 W: 98.62 CHF.
- Offen, nicht enthalten: Status-LED-Platine 8 x 8.2 mm (RGB wie Sensor).
- Nicht an Lager (pi-shop.ch 2026-11-08): Pi Zero 2 W (nicht nötig), microSD Industrial, Grove SHT41.

## 4 System (15 Sensoren + Gateway)

| Weg | Inhalt | CHF |
|---|---|---|
| A: direkt Serie | Serie 20 PCB / 16 bestückt / 15 Sensoren + Gateway (geplant total) | **349.05** |
| B: Prototyp + Serie (geplant) | Prototyp 5 + Serie 15 Sensoren + Gateway (geplant total) | **534.52** |
| B + Programmieradapter | wie B + Adapter Rev 1 (25–55 CHF, ANNAHME) | 559.52 – 589.52 |

- Pro Sensor (Weg A, inkl. Gateway-Anteil): 23.27 CHF; Weg B: 35.63 CHF (die 5 Prototypen sind zusätzlich nutzbar, falls sie die Prüfungen bestehen → dann 20 Sensoren: 26.73 CHF).
- Nicht enthalten: Arbeitszeit, Werkzeug, Verguss-/Dichtmittel über die Sensor-Pauschalen hinaus, Status-LED-Platine Gateway, Ersatzzellen.

## 5 Annahmen und offene Punkte

- PCB 5 Stk (65.21 USD) stammt aus dem Angebot vom 2026-11-08 (CLIENT_INPUT), nicht aus dem Screenshot.
- Economic PCBA + ENIG + POFV + 4 Lagen: JLC-Doku sagt dazu nichts (`docs/references/JLCPCB_NOTES.md` Kap. 10) → BESTELL-PRÜFUNG; Ausweichen auf Standard-PCBA kostet Serie +58.22 CHF je Bestellung.
- Versandpreis mit PCBA (Gewicht höher) erst am Checkout sichtbar (ANNAHME pauschal 23.52 USD).
- Gateway: Netzteil-Konformität, microSD-Datenblatt, SHT41-Breakout-Schaltplan und CR1220-Datenblatt nicht lokal; Mechanik passt für RTC (21.3 × 20.0 mm) und Grove SHT41 (20 × 40 mm) nicht in die CAD-Platzhalter (15 × 12 bzw. 24 × 14 mm) → Befund an Mechanik.

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
    + lokal beschaffte Teile inkl. Ausschuss                 3.09 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        9.23 CHF
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
    = EINMALKOSTEN                                         139.34 CHF
  JLC-Rechnung total 163.23 USD = 133.67 CHF; MWST 12.37 CHF; Bestellung total 185.47 CHF; VOLLKOSTEN pro Sensor 37.09 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 139.71 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
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
    + lokal beschaffte Teile inkl. Ausschuss                 3.09 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        8.38 CHF
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
    = EINMALKOSTEN                                         141.85 CHF
  JLC-Rechnung total 220.33 USD = 180.43 CHF; MWST 16.15 CHF; Bestellung total 267.58 CHF; VOLLKOSTEN pro Sensor 17.84 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 196.81 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
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
    + lokal beschaffte Teile inkl. Ausschuss                 3.09 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        8.17 CHF
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
    = EINMALKOSTEN                                         141.85 CHF
  JLC-Rechnung total 216.74 USD = 177.49 CHF; MWST 15.92 CHF; Bestellung total 264.36 CHF; VOLLKOSTEN pro Sensor 17.62 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 193.22 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
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
    + lokal beschaffte Teile inkl. Ausschuss                 3.09 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        9.31 CHF
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
    = EINMALKOSTEN                                         186.13 CHF
  JLC-Rechnung total 285.20 USD = 233.55 CHF; MWST 20.46 CHF; Bestellung total 325.80 CHF; VOLLKOSTEN pro Sensor 21.72 CHF
  Hinweis: Standard-PCBA: min. 70x70 mm -> Panel (z. B. 3-fach + Raender) noetig; Panelpreis im Rechner pruefen [ANNAHME: hier nicht modelliert].
  Hinweis: GSDL nicht zulaessig (Warenwert 261.68 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
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
    + lokal beschaffte Teile inkl. Ausschuss                 3.09 CHF
    = STUECKKOSTEN pro Sensor (D-005)                       10.72 CHF
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
    = EINMALKOSTEN                                         184.26 CHF
  JLC-Rechnung total 221.61 USD = 181.47 CHF; MWST 16.24 CHF; Bestellung total 237.86 CHF; VOLLKOSTEN pro Sensor 47.57 CHF
  Hinweis: Standard-PCBA: min. 70x70 mm -> Panel (z. B. 3-fach + Raender) noetig; Panelpreis im Rechner pruefen [ANNAHME: hier nicht modelliert].
  Hinweis: GSDL nicht zulaessig (Warenwert 198.09 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
```

