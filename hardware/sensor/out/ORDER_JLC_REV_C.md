# fluidi Sensor Rev C – Bestellunterlage JLCPCB / JLC PCBA

| | |
|---|---|
| Stand | 2026-11-08, Fertigung; Grundlage Red-Team-Prüfung `docs/reviews/phase4_redteam_gesamt.md` (B-1, B-2, B-3, W-1, W-2, W-3, K-2, K-3, K-5) |
| Layout | **Rev C**, Commit `03341e8` (`hardware/sensor/out/LAYOUT_REV_B.md` Kap. 11), Gerber-Job „Revision: C“ |
| Status | **Keine Bestellung ausgelöst.** Bestellen erst nach Freigabe durch den Auftraggeber und nach Abarbeiten von Kap. 4 und 5. Feldnamen im JLC-Formular sind **ANNAHME** (Rechner nur per JavaScript, nicht skriptbar, `docs/references/JLCPCB_NOTES.md` Kap. 7) |
| Kosten | `hardware/sensor/out/COSTS_REV_B.md` (erzeugt von `hardware/sensor/gen/cost_rev_b.py`, Stand 2026-11-08 inkl. K-2) |
| Prüfskript | `.venv/bin/python hardware/sensor/gen/order_check.py --live` (Platine, Gerber-Job, Via-in-Pad, Platzhalter, sha256, Lager); Ausgabe vom 2026-11-08 10:51 in Kap. 1, 2, 7 übernommen |
| Ersetzt | `ORDER_JLC_REV_B.md` (nur noch Verweis) |

## 1 Dateien für den Upload

Erzeugt mit `hardware/sensor/gen/run_pcb.sh` aus Commit `03341e8`. Vor dem Upload mit `sha256sum` vergleichen.

| Datei | Inhalt | sha256 |
|---|---|---|
| `hardware/sensor/out/fluidi_sensor_gerber_jlc.zip` | 11 Gerber (F/In1/In2/B Cu, F/B Mask, F/B Paste, F/B Silkscreen, Edge.Cuts), `PTH.drl`, `NPTH.drl`, Job-Datei | `7da2269dff8755c042cce6fa71d2a57f487c33a3f83389d7f70775ff34791bc0` |
| `hardware/sensor/out/fluidi_sensor_bom_jlc.csv` | BOM, 26 Zeilen / 50 Bauteile (Comment, Designator, Footprint, LCSC Part #) | `3d99ffca7b79abe550a57de4ff7d3228eabe4f532bc46f602e6bcec53f456ea9` |
| `hardware/sensor/out/fluidi_sensor_cpl_jlc.csv` | CPL, 50 Zeilen, alle `Top` (Designator, Mid X, Mid Y, Layer, Rotation) | `b01ba1477406d8c305693567ca70011ccb60892215ccc055ee17d99f6329213f` |

Selbst geprüft (2026-11-08):
- Gerber und Bohrdaten aus einer Kopie der Platine neu erzeugt (gleiche Optionen wie `run_pcb.sh`): alle 14 Dateien inhaltsgleich mit dem ZIP (ohne Kopf-/Datumszeilen).
- CPL neu erzeugt (`kicad-cli pcb export pos` und `cpl_jlc.py`): identisch.
- BOM-Designatoren = CPL-Designatoren (50, keine Differenz).
- DRC auf der Kopie (`kicad-cli 10.0.8 pcb drc --schematic-parity --severity-all`): **0 Verstösse, 0 offene Pads, 0 Footprint-Fehler**.

Hilfsdokumente für die Vorschau (nicht hochladen): `out/pdf/fluidi_sensor_bestueckung_F.pdf` (F.Fab mit Pin-1-Markierung,
Referenzen), `out/pdf/fluidi_sensor_layout_lagen.pdf`, `out/fluidi_sensor_cpl_jlc_rotationen.csv` (KiCad-Rotation, Korrektur, Regel).

## 2 Leiterplatte (PCB)

„Geprüft an“: P = Platine (`fluidi_sensor.kicad_pcb`, pcbnew), J = Gerber-Job-Datei, G = Gerber/Bohrdaten.

| Parameter | Wert | Geprüft an / Quelle |
|---|---|---|
| Base Material | FR-4 | JLCPCB_NOTES Kap. 3 |
| Layers | **4** | P: 4 Kupferlagen; J: `LayerNumber 4`; G: GTL/G1/G2/GBL |
| Dimensions | 26.0 × 158.5 mm (aus dem Gerber) | P: Kontur 26.05 × 158.55 inkl. Linienbreite; J: Size 26.05 × 158.55 |
| PCB Qty | Prototyp **5**, Serie **20** | `COSTS_REV_B.md`; Mindestmenge 5 (JLCPCB_NOTES Kap. 2) |
| Product Type | Industrial/Consumer electronics | – |
| Different Design | 1 | – |
| Delivery Format | **Single PCB** (kein Nutzen) | Economic PCBA braucht keinen Nutzen und keine Ränder (JLCPCB_NOTES Kap. 2). Nur bei Standard-PCBA: Paneel, Kap. 6 |
| PCB Thickness | **1.6 mm** | P: 1.60 mm; J: `BoardThickness 1.6`; Economic 0.8–1.6 mm |
| Impedance Control / Layer Stackup | **JLC04161H-7628** (= Standard „No requirement“), Impedanzkontrolle **nein** | P/J: Dielektrika 0.2104 (FR4 7628) / 1.065 / 0.2104 mm = JLC04161H-7628 (JLCPCB_NOTES Kap. 4). Economic: „Standard stack-up only“ |
| Material / TG | Standard der Vorlage | JLCPCB_NOTES Kap. 4 (NP-155F, TG 150, DRITTQUELLE) |
| PCB Color (Lötstopp) | **Grün** | Economic-Tabelle: 1.6 mm mit ENIG nur grün (JLCPCB_NOTES Kap. 2, erneut abgerufen 2026-11-08). Die Platine trägt keine Farbangabe, J auch nicht |
| Silkscreen | Weiss | – |
| Surface Finish | **ENIG** (1 µ") | P: `copper_finish "ENIG"` (Z. 104); J: `Finish ENIG`. Grund: Minuspad der Zelle ist Leiterplattenkupfer (A-32) |
| Outer / Inner Copper Weight | 1 oz / 0.5 oz | P/J: 0.035 / 0.0152 mm |
| Via Covering | **Epoxy Filled & Capped (POFV)** – **verbindlich**. Ohne POFV keine Bestellung (Auflage A-2, D-023) | P: 145 Vias 0.45/0.30 mm; **8 Via-in-Pad**, alle mit Attribut gefüllt + überkupfert: 4 im EP von U1 (GND), BT1-Clip-Pad (VBAT, Y −23.89), Minuspad BT1 (GND, Y −34.80), TP1 (Y −25.50), TP2 (Y −28.50); Via-in-Pad ohne Füllattribut: 0. Im Fach genau 4 (A-1, TP3 entfällt). Die Gerber tragen kein Füllattribut (ohne X2) → nur das Formular legt POFV fest |
| Min via hole size / diameter | 0.3 mm / 0.45 mm | P/G: einzige Via-Grösse 0.45/0.30; G: `PTH.drl` 146 Bohrungen 0.30 mm (145 Vias + AE1 Pad 2). Kein Aufpreis (JLCPCB_NOTES Kap. 3/8) |
| Min track / spacing | 0.15 mm genutzt / 0.10 mm | P: kleinste Leiterbahn 0.15 mm; J: Abstände 0.10 mm (JLC 4 L: 0.09/0.09) |
| Board Outline Tolerance | ± 0.2 mm (Standard) | PCB_OUTLINE |
| Mark on PCB | **Order Number (Specify a location)** | P: Platzhalter `JLCJLCJLCJLC` auf **B.Silkscreen** bei X 6.00 / Y −19.70 mm (Hilfsursprung, Kopfbereich unten). JLC setzt die Nummer dorthin und nicht frei auf Zellfach oder Sonde. Optionsname und Preis im Formular: **ANNAHME**, prüfen (Kap. 4 Nr. 7) |
| Electrical Test | Flying Probe (Standard) | – |
| Gold Fingers / Castellated / Edge Plating | nein | – |
| Confirm Production File | **ja** | Gerber-Vorschau von JLC prüfen (Kap. 4 Nr. 2) |
| Remark | siehe Kap. 8 | – |

## 3 Bestückung (PCBA)

| Parameter | Wert | Begründung / Quelle |
|---|---|---|
| PCBA Type | **Economic** (Alternative Standard nur nach Kap. 4 Nr. 5 und Kap. 6) | 4 L, 1.6 mm, 2–50 Stk, eine Seite (JLCPCB_NOTES Kap. 2) |
| Assembly Side | **Top Side** | CPL: alle 50 Zeilen `Top`; P: auf B nur TP4/TP5 (Testpads, keine Bauteile); B.Paste ohne Öffnungen |
| PCBA Qty | Prototyp **5** (alle), Serie **16** von 20 | `COSTS_REV_B.md` (D-013: 15 Sensoren + 1 Reserve) |
| Tooling holes / Fiducials | nicht nötig (Economic) | JLCPCB_NOTES Kap. 2 |
| Confirm Parts Placement | **ja** (0.45 USD) | Rotationen nur aus DRITTQUELLE bzw. Projektregel → Abhakliste Kap. 5 |
| X-ray | U1 (VQFN) wird automatisch berechnet | cost_model, JLCPCB_NOTES Kap. 1 |
| Dateien | BOM und CPL aus Kap. 1, Ursprung = Hilfsursprung wie Gerber | – |
| Nicht bestücken | C19, C20 (DNM, nicht in BOM/CPL); AE1, E1, TP1, TP2, TP4, TP5 (Leiterplattenstrukturen) | `out/fluidi_sensor_bom_extra.csv` |
| Lokal beschafft | Knopfzelle Panasonic CR2032 (D-006) – **nicht** von JLC | `out/fluidi_sensor_bom_extra.csv` |
| Programmierung / Coating | nein (nur Standard-PCBA möglich) | JLCPCB_NOTES Kap. 2 |

## 4 Bestell-Checkliste (W-2, B-2) – am Bestelltag abhaken

Screenshots ablegen unter `docs/references/JLC_Bestellung_RevC_<JJJJ-MM-TT>_<Nr>.png`, Nummer in die Spalte „Beleg“ eintragen.
Stimmt ein Punkt nicht, **nicht bezahlen** und Projektleitung informieren.

| Nr. | Prüfpunkt | Erwartung | OK | Beleg (Screenshot-Nr.) / Notiz |
|---|---|---|---|---|
| 1 | sha256 der drei Dateien vor dem Upload | wie Kap. 1 | [ ] | |
| 2 | Gerber-Vorschau („Confirm Production File“) | 4 Kupferlagen in der Reihenfolge GTL/G1/G2/GBL; Kontur geschlossen 26 × 158.5; Sondenelektroden nur auf L2/L3, Aussenkupfer endet bei Y −49.8; AE1 Pad 2 erscheint als Via (DFM K-2) | [ ] | |
| 3 | PCB-Parameter wie Kap. 2 eingestellt | 4 L, 1.6 mm, JLC04161H-7628, grün, ENIG, Single PCB | [ ] | |
| 4 | **Via Covering = Epoxy Filled & Capped** ausgewählt | Option aktiv, im Preis enthalten. **Ohne POFV keine Bestellung** (A-2 D-023) | [ ] | |
| 5 | **Economic PCBA zusammen mit ENIG und POFV wählbar?** (Option nicht ausgegraut, kein Hinweis „not supported“) | ja → weiter mit Nr. 6. **Nein** → nicht bestellen; Standard-PCBA nach Kap. 6 dem Auftraggeber vorlegen. POFV hat Vorrang vor Economic | [ ] ja [ ] nein | |
| 6 | PCB-Preis (5 Stk, ohne PCBA/Versand) gegen Angebot 2026-11-08 | 65.21 USD (20 Stk: 76.30 USD). Abweichung > 5 % → `cost_rev_b.py` nachführen | [ ] | Preis: |
| 7 | Mark on PCB | „Specify a location“ (o. ä.) gewählt, Platzhalter auf B erkannt; Preis notieren (ANNAHME 0 USD) | [ ] | Option/Preis: |
| 8 | Lagerbestand am Bestelltag (K-5), v. a. **BT1 C5213768** | ≥ 5 (Prototyp) bzw. ≥ 16 (Serie); Abfrage 2026-11-08 10:51: **629 Stk** (2026-11-07: 654), Kap. 7 | [ ] | Bestand heute: |
| 9 | BOM-Zuordnung in JLC | 26 Zeilen, alle LCSC-Nummern erkannt, keine Zeile „not matched“; Basic/Extended wie Kap. 7 | [ ] | |
| 10 | **Confirm Parts Placement** | Abhakliste Kap. 5 vollständig | [ ] | |
| 11 | Gesamtbetrag vor dem Bezahlen | Prototyp ≈ 163 USD JLC-Rechnung (`COSTS_REV_B.md` Kap. 3, Einzelposten); Abweichung > 10 % klären | [ ] | Betrag: |
| 12 | Versand | GSDL ist ab Warenwert 65 USD nicht zulässig → DHL Express (23.44 USD). Bei Ankunft erwartet: MWST ≈ 12.4 CHF + Verzollung DHL 19 CHF + Vorlagegebühr 3 CHF (K-2) | [ ] | |
| 13 | Auftragsnummer JLC | | [ ] | Auftragsnr.: ________ |

## 5 Abhakliste „Confirm Parts Placement“ (W-3, B-3)

**Ansicht wie `out/pdf/fluidi_sensor_bestueckung_F.pdf`:** Oberseite, Kopf mit Antenne oben (Y 0), Sonde unten. JLC
zeigt die Platine evtl. gedreht: zuerst die Antenne (Kopf) und das Zellfach (grosses Minuspad) suchen, dann je Teil die
Pin-1-Lage im Bauteilbild (Punkt, Fase, Kerbe, Kathodenmarke) gegen die Spalte „Pin 1 / Lage“ vergleichen. Für jedes
Teil einen Screenshot der JLC-Vorschau ablegen. Bestätigte Rotationen nach der Lieferung als Projekttabelle festhalten
(DFM K-3).

Rotation: CPL = KiCad + Korrektur (`out/fluidi_sensor_cpl_jlc_rotationen.csv`). Korrekturen aus JLCKicadTools
(DRITTQUELLE, `docs/references/matthewlai_JLCKicadTools_cpl_rotations_db_2026-11-07.csv`) bzw. Projektregel; **keine**
davon ist von JLC belegt.

**Kurzschlussfälle sind fett markiert.** Ein Fehler an U1 macht alle 5 Platinen unbrauchbar.

| Teil | LCSC | Lage CPL X/Y (mm), Rot. | Pin 1 / Lage in der Ansicht (aus Platine, pcbnew) | Folge bei falscher Lage | OK | Beleg / Notiz |
|---|---|---|---|---|---|---|
| **U1** CC2340R52 VQFN-24 | C20416850 | 6.00 / −12.60, KiCad −90 → **180** (+270, Regel QFN) | Pin 1 (ANT/RF_PIN) **oben rechts**, Pins 1–6 an der Oberkante von rechts nach links, Pins 7–12 links; Pin-1-Punkt des Gehäuses in der Ecke **oben rechts** | 90°/270°: Versorgungs- und Takt-Pins auf falschen Netzen, Board tot. **180°: Chip-Pin 23 (GND) liegt auf Pad 11 (VDD) → VDD direkt über den Chip an GND, Kurzschluss der Zelle hinter Q1.** Pinbelegung `TI_CC2340R5_Datasheet_SWRS272F.pdf` S. 7, Abb. 6-2 | [ ] | |
| U2 SN74LVC1G14 SC-70-5 | C35740 | −2.60 / −16.40, KiCad 0 → **180** (+180, Regel SOT-353) | Pin 1 (NC) **oben links**; Seite mit 3 Pins (1, 2, 3) **links**, Seite mit 2 Pins (4, 5) rechts | **180°: Chip-Pin 3 (GND) auf Pad 5 (OSC_PWR), Chip-Pin 5 (VCC) auf Pad 3 (GND) → verpolte Versorgung, OSC_PWR über die Substratdiode an GND (Strom über Q2 aus der Zelle).** 90°/270°: Pins neben den Pads. `TI_SN74LVC1G14_Datasheet_SCES218AA.pdf` S. 3 (1 NC, 2 A, 3 GND, 4 Y, 5 VCC) | [ ] | |
| **U3** TMP1075N SOT-563 | C3663690 | −6.69 / −48.60, KiCad 180 → **0** (+180, **Projektregel** W-3, nicht DRITTQUELLE) | Pin 1 (SCL) **unten rechts**; Pins 1–3 rechts von unten nach oben, Pins 4–6 links von oben nach unten | **180°: Chip-Pin 5 (V+) auf Pad 2 (GND), Chip-Pin 2 (GND) auf Pad 5 (SENS_PWR) → SENS_PWR (GPIO von U1) über die Substratdiode von U3 an GND; GPIO von U1 und U3 gefährdet.** I²C ohne Funktion. `TI_TMP1075_Datasheet_SBOS854F.pdf` S. 4, Abb. DRL (1 SCL, 2 GND, 3 ALERT, 4 A0, 5 V+, 6 SDA). Diese Korrektur ist am unsichersten → besonders genau prüfen | [ ] | |
| U4, U5, U6 SN74LVC1G80 SC-70-5 | C473331 | U4 −10.80 / −14.25, U5 −10.80 / −11.60, U6 −6.90 / −15.15; je KiCad 0 → **180** | wie U2: Pin 1 (D) **oben links**, 3-Pin-Seite links | **180°: wie U2, VCC und GND vertauscht → OSC_PWR über die Substratdiode an GND.** Teiler ohne Funktion. `TI_SN74LVC1G80_Datasheet_SCES221T.pdf` S. 3 (1 D, 2 CLK, 3 GND, 4 Q̄, 5 VCC) | [ ] U4 [ ] U5 [ ] U6 | |
| Q1 AO3401A SOT-23 (Verpolschutz) | C15127 | −10.95 / −7.90, KiCad 90 → **0** (−90, Regel SOT-23) | Pin 3 (Drain, VBAT) **oben**; Pin 1 (Gate, GND) unten links, Pin 2 (Source, VDD) unten rechts | Jede Fehldrehung legt Pins neben die Pads (1 Pad oben, 2 unten): keine Versorgung, Board tot. Verpolschutz nur bei richtiger Lage; nach Lieferung mit verkehrter Zelle prüfen (R2-W01, K-6). `AOS_AO3401A_Datasheet_Rev3.1.pdf` S. 1 (G 1, S 2, D 3) | [ ] | |
| Q2 AO3401A SOT-23 (Oszillator-Schalter) | C15127 | −6.95 / −12.05, KiCad 0 → **270** (−90) | Pin 3 (Drain, OSC_PWR) **rechts**; Pin 1 (Gate, OSC_EN_N) links oben, Pin 2 (Source, VDD) links unten | Pins neben den Pads: Messoszillator ohne Versorgung, keine Feuchtemessung. Datenblatt wie Q1 | [ ] | |
| D1 RGB-LED 1615, gem. Anode | C7496855 | 0.00 / −9.60, KiCad 180 → **180** (keine Regel) | Pin 1 (Anode, VDD) **oben rechts**; Pin 2 (R) unten rechts, Pin 3 (G) unten links, Pin 4 (B) oben links. Polaritätsmarke des Gehäuses an Pin 1 (`TUOZHAN_P4-1615G2B2R4TS2-06T-001-24_Datasheet_A0.pdf` S. 4) | 90°/180°/270°: Anode auf einem Kathodennetz, LED leuchtet nicht bzw. falsche Farbe; kein Schaden (Red Team W-3). Der Rot-Kanal teilt das Netz mit UART-TX (LED_R_UART_TX): Statusanzeige über die LED dann nicht verwertbar (PROTOTYP-PRÜFUNG) | [ ] | |
| **Y1** Quarz 48 MHz 3225-4 | C2925606 | 10.80 / −12.60, KiCad 90 → **90** (keine Regel) | Pin 1 (X48P) **unten rechts**, Pin 3 (X48N) oben links; GND-Pads 2 (oben rechts) und 4 (unten links). Pin-1-Marke des Gehäuses unten rechts | **90°/270°: Pins 2/4 (mit dem Metalldeckel verbunden) liegen auf X48P/X48N → X48P und X48N über den Deckel kurzgeschlossen, Quarz zwischen zwei GND-Pads → kein 48-MHz-Takt, U1 startet nicht** (kein Versorgungskurzschluss). 180°: elektrisch gleichwertig (1↔3, 2↔4). `HCI_XC32M4-48.000-F08NLDT_Datasheet_LCSC-2022-05.pdf` S. 1 („Pads 2 and 4 are connected to the metal lid“) | [ ] | |
| BT1 Halter Keystone 3034 | C5213768 | 3.00 / −34.80, KiCad 90 → **90** (keine Regel) | Plus-Pads (VBAT) oben und unten (Y −23.89 / −45.72), Minuspad in der Mitte. **Geschlossenes Ende (Quersteg, Anschlag) links (−X), offenes Ende (Einschub) rechts (+X)**; Clipkörper X −4.4 … 11.7 (`docs/interfaces/PCB_OUTLINE.md` Tab. XBT1) | 90°/270°: Lötfahnen neben den Pads, keine Zelle anschliessbar. **180°: elektrisch gleich, aber Einschub zur falschen Seite → Zelle lässt sich im Gehäuse nicht einsetzen**, Clip muss getauscht werden. `Keystone_3034_Catalog_M65.pdf` S. 1, Fig. 1 | [ ] | |

Ungepolte Teile ohne Prüfpflicht (keine Pin-1-Folge): C1–C25 (MLCC), R1–R13, L1, L2, Y2 (2-Pin-Quarz), SW1 (2 Pads).
Sie nur auf grobe Fehllage prüfen (Teil neben den Pads).

## 6 Alternative Standard-PCBA (nur wenn Kap. 4 Nr. 5 = nein)

Gerechnet mit `scripts/cost_model.py` über `hardware/sensor/gen/cost_rev_b.py` (`COSTS_REV_B.md` Kap. 1.3).
PCB-Preislogik wie Angebot 2026-11-08 (nicht verändert).

| Szenario | PCBA | Stück CHF | Einmal CHF | Bestellung total CHF | Vollkosten/Sensor CHF |
|---|---|---|---|---|---|
| Prototyp 5 PCB / 5 bestückt | Economic | **9.23** | 139.27 | 185.40 | 37.08 |
| Prototyp 2 Paneele = 6 PCB / 6 bestückt / 5 Sensoren | Standard | **10.72** | 184.19 | 237.79 | 47.56 |
| Serie 20 PCB / 16 bestückt / 15 Sensoren | Economic | **8.38** | 141.78 | 267.51 | 17.83 |
| Serie 7 Paneele = 21 PCB / 18 bestückt / 15 Sensoren | Standard | **9.31** | 186.06 | 325.73 | 21.72 |

Mehrkosten Standard: Prototyp +52 CHF, Serie +58 CHF je Bestellung. Sie sind überwiegend einmalig (Setup 25.56 statt
8.18 USD, Schablone 8.21 statt 1.53 USD, Fixture 16.42 USD, Feeder 1.53 USD auch für die 15 Basic-Typen). Stückkosten
Serie 9.31 CHF, REQ-FAB-04 (< 10 CHF) bleibt erfüllt. **Freigabe durch den Auftraggeber nötig.**

**Paneelhinweis:**
- Standard-PCBA verlangt mindestens 70 × 70 mm je Einzelplatine oder Paneel und Randstreifen mit Fiducials und
  Tooling-Löchern (JLCPCB_NOTES Kap. 2).
- Die Platine (26 × 158.5 mm) wird deshalb als Paneel 3 × 1 bestellt (78 × 158.5 mm zuzüglich Ränder, z. B.
  „Panel by JLCPCB“, Randstreifen auf den Längsseiten, Fräsung mit Stegen statt V-Cut, weil die Sondenkontur nicht
  gerade ist).
- **ANNAHME:** JLC bestückt nur ganze Paneele. Der Paneelpreis inkl. Ränder ist nicht abgelesen; das Modell rechnet
  mit dem Angebot pro Platine. Den Preis im Rechner ablesen und `cost_rev_b.py` nachführen.
- Stege und Ausbruch an der Sonde berühren die Kante; Kupfer ≥ 1.25 mm zur Kante ist vorhanden (Red Team Kap. 2).
  Die Steglage im Paneel nicht in den Bereich Z5A/Sonde legen, wenn JLC das anbietet (PROTOTYP-PRÜFUNG:
  Kantenqualität an der Sonde).
- Standard-PCBA bietet ein Reflow-Profil von 240 ± 5 °C statt 255 ± 5 °C (JLCPCB_NOTES Kap. 2); kein Einfluss auf die
  Bauteilwahl erwartet (ANNAHME).

## 7 Lagerbestand (K-5) – Abfrage 2026-11-08 10:51 (JLC-Teilesuche, `order_check.py --live`)

**Den Bestand am Bestelltag erneut prüfen** (Kap. 4 Nr. 8). BT1 C5213768 ist das einzige mechanisch festgelegte
Extended-Teil, und sein Bestand sinkt (2026-11-07: 654, 2026-11-08: **629**). Für die Serie (16 Stk) prüfen, ob sich
der Halter schon mit dem Prototyp-Los vorbestellen lässt („Parts pre-order“/privater Bestand, **ANNAHME** zur
Funktion, im Formular ansehen).

| LCSC | Kat. | Lager | Teil | Ref |
|---|---|---|---|---|
| **C5213768** | extended | **629** | Keystone 3034TR | BT1 |
| C89132 | extended | 4 829 | Sunlord WPN201610H100MT | L1 |
| C473331 | extended | 8 064 | TI SN74LVC1G80DCKR | U4–U6 |
| C2925606 | extended | 8 817 | HCI XC32M4-48.000-F08NLDT | Y1 |
| C20416850 | extended | 9 278 | TI CC2340R52E0RGER | U1 |
| C3663690 | extended | 20 063 | TI TMP1075NDRLR | U3 |
| C99010 | extended | 33 849 | Epson Q13FC13500003 | Y2 |
| C7496855 | extended | 74 324 | TUOZHAN RGB 1615 | D1 |
| C35740 | extended | 97 977 | TI SN74LVC1G14DCKR | U2 |
| C27123 | extended | 110 791 | Sunlord SDCL1005C2N7STDF | L2 |
| C1552 | preferred | 169 219 | FH 0402CG1R5C500NT | C16, C17 |
| 15 Basic-Teile | basic | ≥ 739 622 | MLCC, Widerstände, AO3401A, TS-1088 | übrige |

Kategorien und Gehäuse stimmen mit BOM und Register (`docs/datasheets/INDEX.csv`, Block REV C) überein.

## 8 Remark (Kommentar an JLC)

> Rev C. Via-in-pad by design: 4 vias in QFN exposed pad (U1), 4 vias in pads of battery compartment (BT1 clip pad,
> BT1 negative pad, TP1, TP2). All vias epoxy filled and copper capped (POFV), flat. Order number at the
> JLCJLCJLCJLC placeholder on the bottom side. Inner-layer electrodes in the probe section, no outer copper beyond
> Y −50 mm.

## 9 Was sich gegenüber ORDER_JLC_REV_B.md geändert hat (W-1)

| Punkt Rev B | Rev C |
|---|---|
| 5 Via-in-Pad im Zellfach | 4 (VBAT-Clip-Pad, Minuspad, TP1, TP2), dazu 4 im EP von U1; alle 8 mit Füllattribut (pcbnew geprüft) |
| Platine noch „HAL lead-free“ | `copper_finish ENIG` in Platine und Gerber-Job |
| kein Platzhalter `JLCJLCJLCJLC` | vorhanden auf B.Silkscreen, X 6.00 / Y −19.70; Option „Specify a location“ |
| U3 „keine Korrektur, verdächtig“ | Projektregel +180 in `cpl_jlc.py` → CPL 0°; Kurzschlussfall in Kap. 5 |
| Preise für 5/20 Stk ablesen | Angebot vom 2026-11-08 eingetragen (65.21 / 76.30 USD); am Bestelltag nur noch vergleichen (Kap. 4 Nr. 6) |
| Verzollung 3 CHF | 19 CHF Abwicklung + max(3 CHF; 2 %) Vorlagegebühr, Quelle DHL lokal (K-2) |
| Lagerstand 2026-11-07 | Abfrage 2026-11-08 (Kap. 7) |
