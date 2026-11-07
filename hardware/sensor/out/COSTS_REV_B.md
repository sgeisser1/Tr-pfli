# fluidi Sensor Rev B – Kosten aus der Schaltplan-BOM

| | |
|---|---|
| Stand | 2026-11-08 (PCB-Preis aus JLC-Angebot), Schaltplan Rev B (`hardware/sensor/fluidi_sensor.kicad_sch`), Layout Rev B (Commit 425174d), nachgeführt in der DFM-Prüfung (`docs/reviews/phase4_layout_revb_dfm.md`) |
| Skript | `.venv/bin/python hardware/sensor/gen/cost_rev_b.py` (erzeugt diese Datei) |
| Modell | `scripts/cost_model.compute` (D-005), USD→CHF 0.8189 + 1.5 % Karte; 4 Lagen 1.6 mm, **ENIG**, **Epoxy Filled & Capped (POFV)**, Economic PCBA, Versand GSDL (falls zulässig) |
| Teiledaten | `docs/concepts/bom/jlc_prices.json`, JLC-API Abruf 2026-11-07 (Kategorie, Staffeln, Mindestmenge, Verlust) |
| BOM | `hardware/sensor/out/fluidi_sensor_bom_jlc.csv`; Lötstellen = Pads mit Lotpaste je Footprint (pcbnew) |

## 1 Ergebnis

| Szenario | PCBA | Versand | **Stück CHF** | Einmal CHF | Bestellung total CHF | Vollkosten/Sensor CHF |
|---|---|---|---|---|---|---|
| Prototyp 5 PCB / 5 bestueckt, 4 x 100 uF (D-013) | economic | DHL | **9.23** | 118.73 | 164.86 | 32.97 |
| Serie 20 PCB / 16 bestueckt / 15 Sensoren, 4 x 100 uF | economic | DHL | **8.38** | 121.24 | 246.97 | 16.46 |
| Serie 20 PCB / 16 bestueckt / 15 Sensoren, 2 x 100 uF | economic | DHL | **8.17** | 121.24 | 243.75 | 16.25 |

REQ-FAB-04 (< 10 CHF Stückkosten bei 10–15 Stück): Serie **8.38 / 8.17 CHF** (4 / 2 × 100 µF) → **erfüllt**. PCB-Preis aus dem JLC-Angebot (5 Stk 65.21 USD, 20 Stk 76.30 USD): Aufpreise ENIG/POFV sind überwiegend fix (Befund DFM W-2 erledigt).

BOM-Typen: 10 Extended, 1 Preferred, 15 Basic; 50 Bauteile, 145 Lötstellen je Board.

## 2 Annahmen

- **PCB (Angebot):** JLC-Rechner, abgelesen vom Auftraggeber 2026-11-08: 26 × 158.5 mm, 4 L, 1.6 mm, ENIG, Epoxy Filled & Capped (POFV) → 5 Stk 65.21 USD, 20 Stk 76.30 USD (`docs/requirements/CLIENT_INPUT.md`). Linear: Fixanteil 61.51 USD/Bestellung (D-005, einmalig), Grenzkosten 0.7393 USD/Platine. Andere Mengen interpoliert (ANNAHME linear).
- **POFV** gilt für die ganze Platine (alle Vias), daher gleich für 4 oder 2 Via-in-Pad im Zellfach (L-1, D-023). **ANNAHME:** Kombination mit Economic PCBA zulässig (BESTELL-PRÜFUNG).
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
    + lokal beschaffte Teile inkl. Ausschuss                 3.09 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        9.23 CHF
  Einmalkosten pro Bestellung (USD):
    PCB Fixanteil pro Bestellung (D-005)                    61.51
    Bauteile Mindestabnahme/Verlust-Ueberschuss              3.13
    PCBA Setup                                               8.18
    Schablone                                                1.53
    Feeder/Extended (10 ext., 1 pref., 15 basic Typen)      30.70
    Confirm Parts Placement                                  0.45
    Versand DHL                                             23.44
    Summe JLC-Rechnung einmalig                            128.94 USD
    + MWST-Anteil CH (einmalig)                              8.55 CHF
    + Verzollungsgebuehr Kurier/Post                         3.00 CHF
    = EINMALKOSTEN                                         118.73 CHF
  JLC-Rechnung total 163.15 USD = 133.60 CHF; MWST 10.82 CHF; Bestellung total 164.86 CHF; VOLLKOSTEN pro Sensor 32.97 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 139.71 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
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
    Versand DHL                                             23.44
    Summe JLC-Rechnung einmalig                            131.74 USD
    + MWST-Anteil CH (einmalig)                              8.74 CHF
    + Verzollungsgebuehr Kurier/Post                         3.00 CHF
    = EINMALKOSTEN                                         121.24 CHF
  JLC-Rechnung total 220.25 USD = 180.36 CHF; MWST 14.61 CHF; Bestellung total 246.97 CHF; VOLLKOSTEN pro Sensor 16.46 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 196.81 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
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
    Versand DHL                                             23.44
    Summe JLC-Rechnung einmalig                            131.74 USD
    + MWST-Anteil CH (einmalig)                              8.74 CHF
    + Verzollungsgebuehr Kurier/Post                         3.00 CHF
    = EINMALKOSTEN                                         121.24 CHF
  JLC-Rechnung total 216.66 USD = 177.42 CHF; MWST 14.37 CHF; Bestellung total 243.75 CHF; VOLLKOSTEN pro Sensor 16.25 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 193.22 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
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
