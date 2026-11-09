# fluidi Sensor Rev B/C – Kosten aus der Schaltplan-BOM

| | |
|---|---|
| Stand | 2026-11-08 (PCB-Preis aus JLC-Angebot; Verzollung DHL nach K-2), Schaltplan/Layout **Rev C** (Commit 03341e8, BOM-Teile wie Rev B), Red-Team-Befunde K-2/K-3/W-2 (`docs/reviews/phase4_redteam_gesamt.md`) |
| Bestellunterlage | `hardware/sensor/out/ORDER_JLC_REV_C.md` |
| Skript | `.venv/bin/python hardware/sensor/gen/cost_rev_b.py` (erzeugt diese Datei) |
| Modell | `scripts/cost_model.compute` (D-005), USD→CHF 0.8189 + 1.5 % Karte; 4 Lagen 1.6 mm, **ENIG**, **Epoxy Filled & Capped (POFV)**, Economic PCBA, Versand GSDL (falls zulässig, sonst DHL) |
| Verzollung DHL | 19.00 CHF Abwicklung (in der MWST-Bemessung) + Vorlagegebühr max(3.00 CHF; 2 % der Abgaben); Quelle DHL Express CH, gültig ab 2026-01-01, abgerufen 2026-11-08, `docs/references/DHL-Express-CH_Customs-Services_Gebuehren_Auszug_2026-11-08.txt` und `…_Zollinformationen-Privatkunden_Auszug_2026-11-08.txt`; **ANNAHME** Empfänger ohne eigenes ZAZ-Konto |
| Teiledaten | `docs/concepts/bom/jlc_prices.json`, JLC-API Abruf 2026-11-07 (Kategorie, Staffeln, Mindestmenge, Verlust) |
| BOM | `hardware/sensor/out/fluidi_sensor_bom_jlc.csv`; Lötstellen = Pads mit Lotpaste je Footprint (pcbnew) |

## 1 Ergebnis

| Szenario | PCBA | Versand | **Stück CHF** | Einmal CHF | Bestellung total CHF | Vollkosten/Sensor CHF |
|---|---|---|---|---|---|---|
| Prototyp 5 PCB / 5 bestueckt, 4 x 100 uF (D-013) | economic | DHL | **9.53** | 178.90 | 226.57 | 45.31 |
| Serie 20 PCB / 16 bestueckt / 15 Sensoren, 4 x 100 uF | economic | DHL | **8.69** | 177.94 | 308.29 | 20.55 |
| Serie 20 PCB / 16 bestueckt / 15 Sensoren, 2 x 100 uF | economic | DHL | **8.48** | 177.94 | 305.07 | 20.34 |

REQ-FAB-04 (< 10 CHF Stückkosten bei 10–15 Stück): Serie **8.69 / 8.48 CHF** (4 / 2 × 100 µF) → **erfüllt**. PCB-Preis aus dem JLC-Angebot (5 Stk 65.21 USD, 20 Stk 76.30 USD): Aufpreise ENIG/POFV sind überwiegend fix (Befund DFM W-2 erledigt).

### 1.1 Stückkosten und Vollkosten (K-3)

Die Stückkosten nach D-005 enthalten alles, was pro Sensor anfällt (Bauteile, PCB-Grenzkosten, Bestückung, Röntgen, MWST-Anteil, lokale Teile, Reserveboard). Die Vollkosten verteilen die ganze Bestellung inkl. Einmalkosten (PCB-Fixanteil mit ENIG/POFV, Setup, Feeder, Versand, Verzollung) auf die nutzbaren Sensoren. REQ-FAB-04 (< 10 CHF) bezieht sich auf die Stückkosten (D-005); was ein Sensor real kostet, zeigt die Vollkosten-Spalte.

| Szenario | Sensoren | Stückkosten CHF (D-005) | Einmalkosten CHF | Vollkosten CHF/Sensor | Anteil Einmalkosten an Vollkosten |
|---|---|---|---|---|---|
| Prototyp 5 PCB / 5 bestueckt, 4 x 100 uF (D-013) | 5 | 9.53 | 178.90 | **45.31** | 79 % |
| Serie 20 PCB / 16 bestueckt / 15 Sensoren, 4 x 100 uF | 15 | 8.69 | 177.94 | **20.55** | 58 % |
| Serie 20 PCB / 16 bestueckt / 15 Sensoren, 2 x 100 uF | 15 | 8.48 | 177.94 | **20.34** | 58 % |

### 1.2 Verzollung alt / neu (K-2)

Bis 2026-11-08 rechnete das Modell nur die DHL-Vorlagegebühr (max(3 CHF; 2 %)). Laut DHL Express CH (gültig ab 2026-01-01) kommen 19.00 CHF Abwicklung/Kontoabwicklung je Sendung ohne ZAZ-Konto dazu; sie sind Teil des steuerbaren Warenwerts (MWST 8.1 %). Die Stückkosten ändern sich nicht.

| Szenario | Verzollung alt CHF | neu CHF (inkl. MWST darauf) | Einmal alt | Einmal neu | Vollkosten alt | Vollkosten neu |
|---|---|---|---|---|---|---|
| Prototyp 5 PCB / 5 bestueckt, 4 x 100 uF (D-013) | 3.00 | 23.54 | 158.36 | 178.90 | 41.21 | 45.31 |
| Serie 20 PCB / 16 bestueckt / 15 Sensoren, 4 x 100 uF | 3.00 | 23.54 | 157.40 | 177.94 | 19.18 | 20.55 |
| Serie 20 PCB / 16 bestueckt / 15 Sensoren, 2 x 100 uF | 3.00 | 23.54 | 157.40 | 177.94 | 18.97 | 20.34 |

### 1.3 Alternative Standard-PCBA (W-2, nur falls Economic + ENIG + POFV nicht bestellbar)

Standard-PCBA verlangt mindestens 70 × 70 mm je Einzelplatine oder Paneel sowie Randstreifen mit Fiducials (`docs/references/JLCPCB_NOTES.md` Kap. 2). Die Platine (26 × 158.5 mm) muss deshalb als Paneel 3 × 1 (78 × 158.5 mm + Ränder) bestellt werden. **ANNAHME:** JLC bestückt nur ganze Paneele; der PCB-Preis folgt dem Angebot pro Platine (Paneelpreis mit Rändern **nicht** abgelesen, im Rechner prüfen). Feeder 1.53 USD für jeden Teiletyp, Setup 25.56 USD, Schablone 8.21 USD, Fixture 16.42 USD (JLCPCB_NOTES Kap. 1).

| Szenario | PCBA | Versand | Stück CHF | Einmal CHF | Bestellung total CHF | Vollkosten/Sensor CHF | Δ Stück ggü. Economic | Δ Bestellung ggü. Economic |
|---|---|---|---|---|---|---|---|---|
| ALT W-2 Standard-PCBA Prototyp: 2 Paneele = 6 PCB / 6 bestueckt / 5 Sensoren | standard | DHL | **11.03** | 223.82 | 278.96 | 55.79 | +1.50 | +52.39 |
| ALT W-2 Standard-PCBA Serie: 7 Paneele = 21 PCB / 18 bestueckt / 15 Sensoren | standard | DHL | **9.62** | 222.22 | 366.51 | 24.43 | +0.93 | +58.22 |

REQ-FAB-04 bleibt auch mit Standard-PCBA erfüllt, solange der Paneelpreis nicht deutlich über dem Angebot pro Platine liegt; die Mehrkosten sind überwiegend einmalig (Setup, Schablone, Fixture, Feeder für Basic-Teile). Freigabe durch den Auftraggeber nötig.

BOM-Typen: 10 Extended, 1 Preferred, 15 Basic; 50 Bauteile, 145 Lötstellen je Board.

## 2 Annahmen

- **PCB (Angebot):** JLC-Rechner, abgelesen vom Auftraggeber 2026-11-08: 26 × 158.5 mm, 4 L, 1.6 mm, ENIG, Epoxy Filled & Capped (POFV) → 5 Stk 65.21 USD, 20 Stk 76.30 USD (`docs/requirements/CLIENT_INPUT.md`). Linear: Fixanteil 61.51 USD/Bestellung (D-005, einmalig), Grenzkosten 0.7393 USD/Platine. Andere Mengen interpoliert (ANNAHME linear).
- **POFV** gilt für die ganze Platine (alle Vias), daher gleich für 4 oder 2 Via-in-Pad im Zellfach (L-1, D-023). **ANNAHME:** Kombination mit Economic PCBA zulässig (BESTELL-PRÜFUNG, ORDER_JLC_REV_C.md Kap. 3; Alternative Standard-PCBA Kap. 1.3).
- **Verzollung (K-2):** DHL Express CH, siehe Kopf. **ANNAHME:** kein eigenes ZAZ-Konto, vereinfachte Verzollung (MWST-Wert < 1000 CHF). Zoll 0 (Industriezölle seit 2024-01-01 aufgehoben), MWST 8.1 %.
- **ANNAHME Gehäuse:** Kopf V4 (D-019) braucht ≈ 3.8 g ASA mehr (Oberflächenverhältnis), 0.035 CHF/g; Masse aus dem CAD der Mechanik übernehmen.
- Lokale Teile wie FLOORPLAN_OPTIONS (Zelle Panasonic CR2032 1.38 CHF, Dichtungen, Versiegelung, Schraube), Ausschuss 5 %.
- Nicht enthalten: Programmieradapter (einmalig, CONCEPTS 2.7), Werkzeug, Arbeitszeit, Gateway.

## 3 Einzelposten

```
=== Prototyp 5 PCB / 5 bestueckt, 4 x 100 uF (D-013) ===
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
    + lokal beschaffte Teile inkl. Ausschuss                 3.39 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        9.53 CHF
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
  JLC-Rechnung total 163.23 USD = 133.67 CHF; MWST 12.37 CHF; Bestellung total 226.57 CHF; VOLLKOSTEN pro Sensor 45.31 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 139.71 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
  Hinweis: EINMALKOSTEN enthalten lokal Vergussmasse ER2223 (1 Beutel 41.29 CHF minus Verbrauch in den Stueckkosten) = 39.56 CHF
```

```
=== Serie 20 PCB / 16 bestueckt / 15 Sensoren, 4 x 100 uF ===
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
    + lokal beschaffte Teile inkl. Ausschuss                 3.39 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        8.69 CHF
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
  JLC-Rechnung total 220.33 USD = 180.43 CHF; MWST 16.15 CHF; Bestellung total 308.29 CHF; VOLLKOSTEN pro Sensor 20.55 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 196.81 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
  Hinweis: EINMALKOSTEN enthalten lokal Vergussmasse ER2223 (1 Beutel 41.29 CHF minus Verbrauch in den Stueckkosten) = 36.09 CHF
```

```
=== Serie 20 PCB / 16 bestueckt / 15 Sensoren, 2 x 100 uF ===
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
    + lokal beschaffte Teile inkl. Ausschuss                 3.39 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        8.48 CHF
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
  JLC-Rechnung total 216.74 USD = 177.49 CHF; MWST 15.92 CHF; Bestellung total 305.07 CHF; VOLLKOSTEN pro Sensor 20.34 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 193.22 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
  Hinweis: EINMALKOSTEN enthalten lokal Vergussmasse ER2223 (1 Beutel 41.29 CHF minus Verbrauch in den Stueckkosten) = 36.09 CHF
```

```
=== ALT W-2 Standard-PCBA Prototyp: 2 Paneele = 6 PCB / 6 bestueckt / 5 Sensoren ===
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
    + lokal beschaffte Teile inkl. Ausschuss                 3.39 CHF
    = STUECKKOSTEN pro Sensor (D-005)                       11.03 CHF
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
  JLC-Rechnung total 221.61 USD = 181.47 CHF; MWST 16.24 CHF; Bestellung total 278.96 CHF; VOLLKOSTEN pro Sensor 55.79 CHF
  Hinweis: Standard-PCBA: min. 70x70 mm -> Panel (z. B. 3-fach + Raender) noetig; Panelpreis im Rechner pruefen [ANNAHME: hier nicht modelliert].
  Hinweis: GSDL nicht zulaessig (Warenwert 198.09 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
  Hinweis: EINMALKOSTEN enthalten lokal Vergussmasse ER2223 (1 Beutel 41.29 CHF minus Verbrauch in den Stueckkosten) = 39.56 CHF
```

```
=== ALT W-2 Standard-PCBA Serie: 7 Paneele = 21 PCB / 18 bestueckt / 15 Sensoren ===
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
    + lokal beschaffte Teile inkl. Ausschuss                 3.39 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        9.62 CHF
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
  JLC-Rechnung total 285.20 USD = 233.55 CHF; MWST 20.46 CHF; Bestellung total 366.51 CHF; VOLLKOSTEN pro Sensor 24.43 CHF
  Hinweis: Standard-PCBA: min. 70x70 mm -> Panel (z. B. 3-fach + Raender) noetig; Panelpreis im Rechner pruefen [ANNAHME: hier nicht modelliert].
  Hinweis: GSDL nicht zulaessig (Warenwert 261.68 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
  Hinweis: EINMALKOSTEN enthalten lokal Vergussmasse ER2223 (1 Beutel 41.29 CHF minus Verbrauch in den Stueckkosten) = 36.09 CHF
```

## 4 BOM mit Kostendaten

| Teil | Stk/Board | Kat. | Lötstellen | USD @20 | MOQ | Verlust |
|---|---|---|---|---|---|---|
| CR2032 / Keystone 3034TR (BT1) C5213768 | 1 | extended | 2 | 0.3615 | 2 | 0 |
| 100uF (C1 C2 C3 C4) C15008 | 4 | basic | 2 | 0.1090 | 5 | 4 |
| 10uF (C5 C9) C15525 | 2 | basic | 2 | 0.0257 | 20 | 10 |
| 100nF (C6 C7 C8 C10 C11 C13 C21 C24 C25) C1525 | 9 | basic | 2 | 0.0031 | 20 | 10 |
| 1uF (C12) C52923 | 1 | basic | 2 | 0.0058 | 20 | 12 |
| 15pF (C14 C15 C18) C1548 | 3 | basic | 2 | 0.0026 | 20 | 10 |
| 1.5pF (C16 C17) C1552 | 2 | preferred | 2 | 0.0045 | 20 | 10 |
| 22pF (C22) C1555 | 1 | basic | 2 | 0.0019 | 20 | 10 |
| RGB 1615 (D1) C7496855 | 1 | extended | 4 | 0.0131 | 10 | 5 |
| 10uH (L1) C89132 | 1 | extended | 2 | 0.0418 | 5 | 4 |
| 2.7nH (L2) C27123 | 1 | extended | 2 | 0.0031 | 20 | 10 |
| AO3401A (Q1 Q2) C15127 | 2 | basic | 3 | 0.0828 | 5 | 4 |
| 100k (R1 R9 R10 R11 R12 R13) C25741 | 6 | basic | 2 | 0.0012 | 20 | 12 |
| 0R (R2) C17168 | 1 | basic | 2 | 0.0012 | 20 | 10 |
| 1k (R3) C11702 | 1 | basic | 2 | 0.0013 | 20 | 10 |
| 4.7k (R4 R5) C25900 | 2 | basic | 2 | 0.0017 | 20 | 10 |
| 470 (R6) C25117 | 1 | basic | 2 | 0.0010 | 20 | 10 |
| 200 (R7) C25087 | 1 | basic | 2 | 0.0029 | 20 | 10 |
| 100 (R8) C25076 | 1 | basic | 2 | 0.0012 | 20 | 15 |
| TS-1088 (SW1) C720477 | 1 | basic | 2 | 0.0527 | 5 | 4 |
| CC2340R52E0RGER (U1) C20416850 | 1 | extended | 25 | 1.2217 | 1 | 0 |
| SN74LVC1G14DCKR (U2) C35740 | 1 | extended | 5 | 0.0566 | 5 | 4 |
| TMP1075NDRLR (U3) C3663690 | 1 | extended | 6 | 0.4563 | 2 | 0 |
| SN74LVC1G80DCKR (U4 U5 U6) C473331 | 3 | extended | 5 | 0.2110 | 5 | 2 |
| 48MHz 8pF (Y1) C2925606 | 1 | extended | 4 | 0.0992 | 5 | 2 |
| 32.768kHz 9pF (Y2) C99010 | 1 | extended | 2 | 0.2038 | 5 | 2 |
