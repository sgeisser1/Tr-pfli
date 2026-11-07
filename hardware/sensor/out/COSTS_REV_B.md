# fluidi Sensor Rev B – Kosten aus der Schaltplan-BOM

| | |
|---|---|
| Stand | 2026-11-07, Elektronik, Schaltplan Rev B (`hardware/sensor/fluidi_sensor.kicad_sch`) |
| Skript | `.venv/bin/python hardware/sensor/gen/cost_rev_b.py` (erzeugt diese Datei) |
| Modell | `scripts/cost_model.compute` (D-005), USD→CHF 0.8189 + 1.5 % Karte; 4 Lagen 1.6 mm, **ENIG**, Economic PCBA, Versand GSDL (falls zulässig) |
| Teiledaten | `docs/concepts/bom/jlc_prices.json`, JLC-API Abruf 2026-11-07 (Kategorie, Staffeln, Mindestmenge, Verlust) |
| BOM | `hardware/sensor/out/fluidi_sensor_bom_jlc.csv`; Lötstellen = Pads mit Lotpaste je Footprint (pcbnew) |

## 1 Ergebnis

| Szenario | PCBA | Versand | **Stück CHF** | Einmal CHF | Bestellung total CHF | Vollkosten/Sensor CHF |
|---|---|---|---|---|---|---|
| Prototyp 5 PCB / 5 bestueckt, 4 x 100 uF (D-013) | economic | DHL | **9.07** | 101.17 | 146.52 | 29.30 |
| Serie 20 PCB / 16 bestueckt / 15 Sensoren, 4 x 100 uF | economic | DHL | **8.21** | 103.06 | 226.28 | 15.09 |
| Serie 20 PCB / 16 bestueckt / 15 Sensoren, 2 x 100 uF | economic | DHL | **8.00** | 103.06 | 223.06 | 14.87 |

REQ-FAB-04 (< 10 CHF Stückkosten bei 10–15 Stück): Serie **8.21 / 8.00 CHF** (4 / 2 × 100 µF) → erfüllt.

BOM-Typen: 10 Extended, 1 Preferred, 15 Basic; 50 Bauteile, 145 Lötstellen je Board.

## 2 Annahmen

- **ANNAHME PCB:** Grenzkosten je Platine × 1.26 (Rechteck 26 × 160 mm statt 22 × 150 mm im JLC-Rechner); Fixanteil unverändert. Vor der Bestellung mit der Kontur aus PCB_OUTLINE Rev B im JLC-Rechner ersetzen.
- **ANNAHME Gehäuse:** Kopf V4 (D-019) braucht ≈ 3.8 g ASA mehr (Oberflächenverhältnis), 0.035 CHF/g; Masse aus dem CAD der Mechanik übernehmen.
- Lokale Teile wie FLOORPLAN_OPTIONS (Zelle Panasonic CR2032 1.38 CHF, Dichtungen, Versiegelung, Schraube), Ausschuss 5 %.
- Nicht enthalten: Programmieradapter (einmalig, CONCEPTS 2.7), Werkzeug, Arbeitszeit, Gateway.

## 3 Einzelposten

```
=== Prototyp 5 PCB / 5 bestueckt, 4 x 100 uF (D-013) ===
4 Lagen, 1.6 mm, PCB 5 Stk, bestueckt 5 Stk, nutzbare Sensoren 5, PCBA economic, Versand DHL, Gewicht ca. 0.25 kg [ANNAHME]
  JLC-Anteil pro bestuecktem Board (USD):
    PCB Grenzkosten pro Platine                              0.56
    Bauteile JLC/LCSC                                        4.23
    SMT-Bestueckung                                          0.23
    Roentgen (1 leadless/Board)                              1.64
    Summe JLC-Anteil                                         6.67 USD
    + MWST-Anteil CH                                         0.44 CHF
    = JLC-Anteil pro Board                                   5.98 CHF
    x Boards / Sensoren                                  5/5
    + lokal beschaffte Teile inkl. Ausschuss                 3.09 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        9.07 CHF
  Einmalkosten pro Bestellung (USD):
    PCB Fixanteil pro Bestellung (D-005)                    41.95
    Bauteile Mindestabnahme/Verlust-Ueberschuss              3.13
    PCBA Setup                                               8.18
    Schablone                                                1.53
    Feeder/Extended (10 ext., 1 pref., 15 basic Typen)      30.70
    Confirm Parts Placement                                  0.45
    Versand DHL                                             23.44
    Summe JLC-Rechnung einmalig                            109.38 USD
    + MWST-Anteil CH (einmalig)                              7.26 CHF
    + Verzollungsgebuehr Kurier/Post                         3.00 CHF
    = EINMALKOSTEN                                         101.17 CHF
  JLC-Rechnung total 142.71 USD = 116.87 CHF; MWST 9.47 CHF; Bestellung total 146.52 CHF; VOLLKOSTEN pro Sensor 29.30 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 119.27 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
```

```
=== Serie 20 PCB / 16 bestueckt / 15 Sensoren, 4 x 100 uF ===
4 Lagen, 1.6 mm, PCB 20 Stk, bestueckt 16 Stk, nutzbare Sensoren 15, PCBA economic, Versand DHL, Gewicht ca. 0.55 kg [ANNAHME]
  JLC-Anteil pro bestuecktem Board (USD):
    PCB Grenzkosten pro Platine                              0.56
    Bauteile JLC/LCSC                                        3.74
    SMT-Bestueckung                                          0.23
    Roentgen (1 leadless/Board)                              0.82
    Summe JLC-Anteil                                         5.36 USD
    + MWST-Anteil CH                                         0.36 CHF
    = JLC-Anteil pro Board                                   4.81 CHF
    x Boards / Sensoren                                  16/15
    + lokal beschaffte Teile inkl. Ausschuss                 3.09 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        8.21 CHF
  Einmalkosten pro Bestellung (USD):
    PCB Fixanteil pro Bestellung (D-005)                    41.95
    PCB unbestueckte Reserveplatinen                         2.26
    Bauteile Mindestabnahme/Verlust-Ueberschuss              2.97
    PCBA Setup                                               8.18
    Schablone                                                1.53
    Feeder/Extended (10 ext., 1 pref., 15 basic Typen)      30.70
    Confirm Parts Placement                                  0.45
    Versand DHL                                             23.44
    Summe JLC-Rechnung einmalig                            111.48 USD
    + MWST-Anteil CH (einmalig)                              7.39 CHF
    + Verzollungsgebuehr Kurier/Post                         3.00 CHF
    = EINMALKOSTEN                                         103.06 CHF
  JLC-Rechnung total 197.20 USD = 161.48 CHF; MWST 13.08 CHF; Bestellung total 226.28 CHF; VOLLKOSTEN pro Sensor 15.09 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 173.76 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
```

```
=== Serie 20 PCB / 16 bestueckt / 15 Sensoren, 2 x 100 uF ===
4 Lagen, 1.6 mm, PCB 20 Stk, bestueckt 16 Stk, nutzbare Sensoren 15, PCBA economic, Versand DHL, Gewicht ca. 0.55 kg [ANNAHME]
  JLC-Anteil pro bestuecktem Board (USD):
    PCB Grenzkosten pro Platine                              0.56
    Bauteile JLC/LCSC                                        3.52
    SMT-Bestueckung                                          0.23
    Roentgen (1 leadless/Board)                              0.82
    Summe JLC-Anteil                                         5.13 USD
    + MWST-Anteil CH                                         0.34 CHF
    = JLC-Anteil pro Board                                   4.61 CHF
    x Boards / Sensoren                                  16/15
    + lokal beschaffte Teile inkl. Ausschuss                 3.09 CHF
    = STUECKKOSTEN pro Sensor (D-005)                        8.00 CHF
  Einmalkosten pro Bestellung (USD):
    PCB Fixanteil pro Bestellung (D-005)                    41.95
    PCB unbestueckte Reserveplatinen                         2.26
    Bauteile Mindestabnahme/Verlust-Ueberschuss              2.97
    PCBA Setup                                               8.18
    Schablone                                                1.53
    Feeder/Extended (10 ext., 1 pref., 15 basic Typen)      30.70
    Confirm Parts Placement                                  0.45
    Versand DHL                                             23.44
    Summe JLC-Rechnung einmalig                            111.48 USD
    + MWST-Anteil CH (einmalig)                              7.39 CHF
    + Verzollungsgebuehr Kurier/Post                         3.00 CHF
    = EINMALKOSTEN                                         103.06 CHF
  JLC-Rechnung total 193.61 USD = 158.54 CHF; MWST 12.84 CHF; Bestellung total 223.06 CHF; VOLLKOSTEN pro Sensor 14.87 CHF
  Hinweis: GSDL nicht zulaessig (Warenwert 170.17 USD > 65.0 USD oder Gewicht > 1.5 kg) -> DHL Express gerechnet.
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
