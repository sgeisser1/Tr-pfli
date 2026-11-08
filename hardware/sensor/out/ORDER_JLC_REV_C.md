# fluidi Sensor Rev C – Bestellunterlage JLCPCB / JLC PCBA

| | |
|---|---|
| Stand | 2026-11-08, Fertigung; Grundlage Red-Team-Prüfung `docs/reviews/phase4_redteam_gesamt.md` (B-1, B-2, B-3, W-1, W-2, W-3, K-2, K-3, K-5). **Nachtrag 2026-11-08 (Phase 5):** Feldnamen PCB-Teil aus dem JLC-Screenshot des Auftraggebers (Standard PCB, nicht eingeloggt), Mark on PCB, Confirm Production File, Deburring, Material Type, Via Plating Method, Versand 23.52 USD, Remark (Kap. 2, 4, 8, 9) |
| Layout | **Rev C**, Commit `03341e8` (`hardware/sensor/out/LAYOUT_REV_B.md` Kap. 11), Gerber-Job „Revision: C“ |
| Status | **Keine Bestellung ausgelöst.** Bestellen erst nach Freigabe durch den Auftraggeber und nach Abarbeiten von Kap. 4 und 5. Feldnamen und Optionen des **PCB-Teils** sind am Screenshot vom 2026-11-08 belegt (`docs/references/JLCPCB_NOTES.md` Kap. 10); die Felder **nach dem Einschalten von „PCB Assembly“** hat noch niemand gesehen → **ANNAHME**. Schritt-für-Schritt-Anleitung: `docs/manuals/BESTELLEN_JLC.md` |
| Kosten | `hardware/sensor/out/COSTS_REV_B.md` (erzeugt von `hardware/sensor/gen/cost_rev_b.py`, Stand 2026-11-08 inkl. K-2, DHL 23.52 USD); Abgleich mit dem Screenshot und Gateway/System: `docs/reviews/phase5_kosten_final.md` (`scripts/cost_final_phase5.py`) |
| Prüfskript | `.venv/bin/python hardware/sensor/gen/order_check.py --live` (Platine, Gerber-Job, Via-in-Pad, Platzhalter, sha256, Lager); Ausgabe vom 2026-11-08 10:51 in Kap. 1, 2, 7 übernommen |
| Ersetzt | `ORDER_JLC_REV_B.md` (nur noch Verweis) |

## 1 Dateien für den Upload

Erzeugt mit `hardware/sensor/gen/run_pcb.sh` (Layout Rev C ohne Platzhalter, Phase 5 W-4). Vor dem Upload mit `sha256sum` vergleichen.

**Nachtrag W-4 (2026-11-08):** Der Platzhalter `JLCJLCJLCJLC` ist aus dem Layout entfernt (nur B.Silkscreen, Revision bleibt C). Gerber geometrisch verglichen mit `scripts/gerber_geom_diff.py`: einzige Änderung B.Silkscreen (88 Elemente weniger), alle anderen Lagen/Bohrdaten/Kontur gleich; BOM und CPL bytegleich; DRC 0, Parität 0; `order_check.py` Exit 0. Die sha256 unten sind der gültige Stand.

| Datei | Inhalt | sha256 |
|---|---|---|
| `hardware/sensor/out/fluidi_sensor_gerber_jlc.zip` | 11 Gerber (F/In1/In2/B Cu, F/B Mask, F/B Paste, F/B Silkscreen, Edge.Cuts), `PTH.drl`, `NPTH.drl`, Job-Datei | `bf1902ea4bab83d96f385f557575d8311886acf2bacee7aa743d88eef47883d0` |
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
| Material Type | **FR4 TG135** (Vorgabe des Rechners, nicht ändern) | Screenshot 2026-11-08: Default TG135; Optionen FR4 TG155, Nan Ya NP-140F, KB6164-TG135, Nan Ya NP-155F, KB-6165-TG155. JLC nennt für TG135 kein Datenblatt und keine Er-Werte (`docs/references/JLCPCB_BaseMaterial_Auszug_2026-11-08.txt`; offene Kundenfrage `…QA592-TG135…`). FEM rechnet bereits mit TG-135-Laminat (`Kingboard_KB-6160A_TechnicalInformation.pdf` S. 1: Tg 135, T260 > 10 min, Td 305 °C → bleifreies Reflow 255 °C einmalig zulässig, **ANNAHME** JLC-TG135 ≈ KB-6160-Klasse). Er der Sondenisolation: **PROTOTYP-PRÜFUNG** (Kalibrierung am Muster) |
| PCB Color (Lötstopp) | **Grün** | Economic-Tabelle: 1.6 mm mit ENIG nur grün (JLCPCB_NOTES Kap. 2, erneut abgerufen 2026-11-08). Die Platine trägt keine Farbangabe, J auch nicht |
| Silkscreen | Weiss | – |
| Surface Finish | **ENIG** (1 µ") | P: `copper_finish "ENIG"` (Z. 104); J: `Finish ENIG`. Grund: Minuspad der Zelle ist Leiterplattenkupfer (A-32) |
| Outer / Inner Copper Weight | 1 oz / 0.5 oz | P/J: 0.035 / 0.0152 mm |
| Via Covering | **Epoxy Filled & Capped (POFV)** – **verbindlich**. Ohne POFV keine Bestellung (Auflage A-2, D-023) | P: 145 Vias 0.45/0.30 mm; **8 Via-in-Pad**, alle mit Attribut gefüllt + überkupfert: 4 im EP von U1 (GND), BT1-Clip-Pad (VBAT, Y −23.89), Minuspad BT1 (GND, Y −34.80), TP1 (Y −25.50), TP2 (Y −28.50); Via-in-Pad ohne Füllattribut: 0. Im Fach genau 4 (A-1, TP3 entfällt). Die Gerber tragen kein Füllattribut (ohne X2) → nur das Formular legt POFV fest |
| Via Plating Method | **Horizontal Electroless Copper Plating** (vom Rechner erzwungen, 3.51 USD bei 20 Stk) | Screenshot: „Epoxy-filled or copper-paste-filled vias require Horizontal Electroless Copper Plating“ |
| Min via hole size/diameter | **0.3mm/(0.4/0.45mm)** | P/G: einzige Via-Grösse 0.45/0.30; G: `PTH.drl` 146 Bohrungen 0.30 mm (145 Vias + AE1 Pad 2). Kein Aufpreis (JLCPCB_NOTES Kap. 3/8) |
| Min track / spacing | 0.15 mm genutzt / 0.10 mm | P: kleinste Leiterbahn 0.15 mm; J: Abstände 0.10 mm (JLC 4 L: 0.09/0.09) |
| Board Outline Tolerance | ± 0.2 mm (Standard) | PCB_OUTLINE |
| Mark on PCB | **Remove Mark** (Formular bietet nur „Remove Mark“ und „2D barcode (Serial Number)“). **Platzhalter wird aus dem Layout entfernt** (W-4, Projektleitung; Prüfung `order_check.py`: kein Platzhalter) | JLC: „Order Number is not available since May 2026. Please DO NOT add "JLCJLCJLCJLC" in your silkscreen layer“; ohne Auswahl wird keine Markierung gesetzt (`docs/references/JLCPCB_HowToMarkOnPCB_Auszug_2026-11-08.txt`, „Last updated on May 22, 2026“). Der Platzhalter `JLCJLCJLCJLC` (B.Silkscreen, X 6.00 / Y −19.70) ist damit überholt und wird vor der Bestellung aus dem Layout gelöscht (W-4); Kontrolle in der Produktionsdatei Lage `bo` (Kap. 4 Nr. 2). „2D barcode“ **nicht** wählen: ohne Positionsquadrat setzt JLC den Code „in an empty area“, also evtl. auf Sonde, Schott oder Dichtstreifen |
| Electrical Test | Flying Probe Fully Test (Vorgabe) | Screenshot |
| Gold Fingers / Castellated / Edge Plating, übrige Optionen | No | Economic PCBA: Gold Fingers/Castellated/Edge Plating „Not Support“ (`…PCBA-Capabilities_Auszug…`) |
| Confirm Production File | **Yes** (Screenshot stand auf „No“) | JLC empfiehlt die Option ausdrücklich für gefüllte Vias und Markierungen (`…ViaCovering_Auszug…`, `…HowToMarkOnPCB_Auszug…`); Produktionsdatei enthält Lage `sk` = zu füllende Vias (`docs/references/JLCPCB_ConfirmProductionFile_Auszug_2026-11-08.txt`). Preis nicht belegt → **ANNAHME 0 USD**, beim Umschalten ablesen (Kap. 4 Nr. 6) |
| Deburring/Edge rounding | **Yes** (Vorgabe, 0.50 USD bei 20 Stk) | JLC verlangt Entgraten/Ecken runden bei Einzelplatinen mit einer Seite 1.5–3 cm, 0.02 USD/Stk (`docs/references/JLCPCB_ExtraCharges_Auszug_2026-11-08.txt` Nr. 6); Platine 26 mm breit. Nutzen: glatte Kanten an Sonde und Kopf (Einschub durch das Schott, Hülse). **ANNAHME:** Feld lässt sich ohnehin nicht abwählen |
| Specify Stackup | **No** (= Standard-Lagenaufbau) | Economic PCBA: „Standard stack-up only“ (`…PCBA-Capabilities_Auszug…`). Gerber-Job/Platine: 0.2104/1.065/0.2104 mm = JLC04161H-7628 (JLCPCB_NOTES Kap. 4) |
| Remark | siehe Kap. 8 | – |

## 3 Bestückung (PCBA)

| Parameter | Wert | Begründung / Quelle |
|---|---|---|
| PCB Assembly (Schalter unter den PCB-Optionen) | **einschalten** | Screenshot 2026-11-08: Schalter aus; die Wahl Economic/Standard erscheint erst danach. Alle Feldnamen dieses Kapitels: **ANNAHME** bis zum ersten Einschalten (Anleitung `docs/manuals/BESTELLEN_JLC.md` Schritt 6) |
| PCBA Type | **Economic** (Alternative Standard nur nach Kap. 4 Nr. 5 und Kap. 6) | 4 L, 1.6 mm, 2–50 Stk, eine Seite (JLCPCB_NOTES Kap. 2, erneut abgerufen 2026-11-08: `docs/references/JLCPCB_PCBA-Capabilities_Auszug_2026-11-08.txt`). Zu Via Covering/POFV sagt JLC für Economic nichts (Kap. 10 JLCPCB_NOTES) → Kap. 4 Nr. 5 |
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
| 2 | Gerber-Vorschau beim Upload und **Produktionsdatei** („Confirm Production File“, nach der Zahlung per E-Mail; Ordner `ok` mit Gerber-Viewer öffnen, nicht nur das Bild) | 4 Kupferlagen in der Reihenfolge GTL/G1/G2/GBL; Kontur geschlossen 26 × 158.5; Sondenelektroden nur auf L2/L3, Aussenkupfer endet bei Y −49.8 (die letzten ≈ 109 mm der Sonde ohne Aussenkupfer); AE1 Pad 2 erscheint als Via (DFM K-2). Lage **`sk`** (gefüllte Vias) enthält **alle 146** Bohrungen 0.30 mm, mindestens die 8 Via-in-Pad (4 im U1-EP, BT1-Clip-Pad, Minuspad, TP1, TP2). Lage **`bo`**: keine Auftragsnummer, kein Barcode, kein Text `JLCJLCJLCJLC`. Erst dann „Yes, please proceed to production“ | [ ] | |
| 3 | PCB-Parameter wie Kap. 2 eingestellt | 4 L, 1.6 mm, Specify Stackup No, FR4 TG135, grün, Silk weiss, ENIG 1 U", 1 oz / 0.5 oz, Single PCB, Deburring Yes, Via Plating Horizontal Electroless, Min via 0.3mm/(0.4/0.45mm), Outline ±0.2, Flying Probe Fully Test | [ ] | |
| 4 | **Via Covering = Epoxy Filled & Capped** ausgewählt | Option aktiv, im Preis enthalten. **Ohne POFV keine Bestellung** (A-2 D-023) | [ ] | |
| 5 | **Economic PCBA zusammen mit ENIG und POFV wählbar?** (Option nicht ausgegraut, kein Hinweis „not supported“) | ja → weiter mit Nr. 6. **Nein** → nicht bestellen; Standard-PCBA nach Kap. 6 dem Auftraggeber vorlegen. POFV hat Vorrang vor Economic | [ ] ja [ ] nein | |
| 6 | PCB-Preis (ohne PCBA/Versand) gegen Angebot 2026-11-08 | 5 Stk 65.21 USD; 20 Stk 76.30 USD = Engineering 25.00 + Via Covering 18.59 + Surface Finish 18.50 + Deburring 0.50 + Board 10.20 + Via Plating 3.51 (Screenshot, Confirm Production File = No). **Aufpreis für Confirm Production File = Yes notieren** (ANNAHME 0). Abweichung > 5 % → `cost_rev_b.py` / `cost_final_phase5.py` nachführen | [ ] | Preis: |
| 7 | Mark on PCB | **„Remove Mark“** gewählt (nicht „2D barcode (Serial Number)“); Preis 0 | [ ] | |
| 8 | Lagerbestand am Bestelltag (K-5), v. a. **BT1 C5213768** | ≥ 5 (Prototyp) bzw. ≥ 16 (Serie); Abfrage 2026-11-08 10:51: **629 Stk** (2026-11-07: 654), Kap. 7 | [ ] | Bestand heute: |
| 9 | BOM-Zuordnung in JLC | 26 Zeilen, alle LCSC-Nummern erkannt, keine Zeile „not matched“; Basic/Extended wie Kap. 7 | [ ] | |
| 10 | **Confirm Parts Placement** | Abhakliste Kap. 5 vollständig | [ ] | |
| 11 | Gesamtbetrag vor dem Bezahlen | Prototyp ≈ 163.23 USD, Serie ≈ 220.33 USD JLC-Rechnung inkl. DHL (`docs/reviews/phase5_kosten_final.md` Kap. 2); Abweichung > 10 % klären. **Stopp:** Posten „Pre-reflow Soldering“ vorhanden (0.016 USD/Lötstelle) → nicht bezahlen, Projektleitung: Serie dann ≈ 10.60 CHF/Stück > REQ-FAB-04 (W-3, `phase5_kosten_final.md` Kap. 0) | [ ] | Betrag: |
| 12 | Versand | GSDL ist ab Warenwert 65 USD nicht zulässig → **DHL Express** (Screenshot 2026-11-08: 23.52 USD, 2–4 Tage, 0.41 kg für 20 unbestückte PCB; mit PCBA am Checkout ablesen). Bei Ankunft erwartet: MWST ≈ 12.4 CHF + Verzollung DHL 19 CHF + Vorlagegebühr 3 CHF (K-2) | [ ] | |
| 13 | Auftragsnummer JLC | | [ ] | Auftragsnr.: ________ |

## 5 Abhakliste „Confirm Parts Placement“ (W-3, B-3)

**Feste Regel (Red Team W-2): Nie selbst drehen.** Weicht ein Teil ab oder ist die Lage unklar: Screenshot, **nicht
bezahlen**, Projektleitung fragen. Der rote Punkt in der JLC-Vorschau ist **nicht** Pin 1: „we do not call the red dot
pin 1, but a marking only“ (JLC PCBA-FAQ Teil 2, Q1, Sep 09, 2026; `docs/references/JLCPCB_NOTES.md` Kap. 8). Pin 1 am
Gehäusemerkmal des Bauteilbilds beurteilen (Fase, Kerbe, Pin-1-Punkt auf dem Gehäuse, Kathodenmarke) bzw. an der
Pad-Lage des Footprints.

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
PCB-Preislogik wie Angebot 2026-11-08 (nicht verändert). Beträge mit DHL 23.52 USD (Stand 2026-11-08, `COSTS_REV_B.md`).

| Szenario | PCBA | Stück CHF | Einmal CHF | Bestellung total CHF | Vollkosten/Sensor CHF |
|---|---|---|---|---|---|
| Prototyp 5 PCB / 5 bestückt | Economic | **9.23** | 139.34 | 185.47 | 37.09 |
| Prototyp 2 Paneele = 6 PCB / 6 bestückt / 5 Sensoren | Standard | **10.72** | 184.26 | 237.86 | 47.57 |
| Serie 20 PCB / 16 bestückt / 15 Sensoren | Economic | **8.38** | 141.85 | 267.58 | 17.84 |
| Serie 7 Paneele = 21 PCB / 18 bestückt / 15 Sensoren | Standard | **9.31** | 186.13 | 325.80 | 21.72 |

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

Nachgeführt 2026-11-08 (Phase 5): JLC verlangt bei gefüllten Vias die Angabe, welche Vias gefüllt werden („leave a note …
Alternatively, you can specify to fill all vias of a particular diameter“, `docs/references/JLCPCB_ViaCovering_Auszug_2026-11-08.txt`);
die Auftragsnummer gibt es seit Mai 2026 nicht mehr (Kap. 2, Mark on PCB). Text unverändert ins Feld „Remark“ kopieren – **aus der Textdatei** `hardware/sensor/out/REMARK_JLC_REV_C.txt`
(eine Zeile, 563 Zeichen, ohne Markdown; Feldlänge im Formular ist nicht belegt → ANNAHME, bei Kürzung Projektleitung
fragen). Inhalt: alle 146 Bohrungen 0.30 mm füllen und überkupfern (8 davon Via-in-Pad, flach), Mark on PCB = Remove
Mark, Sonde (letzte ≈ 109 mm, Ende gegenüber der Antenne) ohne Aussenkupfer beabsichtigt. Der Satz zum Platzhalter
entfällt, weil der Platzhalter aus dem Layout entfernt wird (W-4).

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

**Nachtrag 2026-11-08 (Phase 5, Screenshot JLC-Rechner des Auftraggebers):**

| Punkt vorher | jetzt | Grund / Quelle |
|---|---|---|
| Mark on PCB „Order Number (Specify a location)“ | **Remove Mark** | Option existiert nicht mehr (JLC seit Mai 2026); Platzhalter auf B überholt, Layout unverändert (Befund an Layout für die nächste Revision) |
| Confirm Production File „ja“ (ohne Preis) | **Yes**, Preis ANNAHME 0, ablesen; Prüfung Lagen `sk`/`bo` | JLC-Hilfe Produktionsdatei |
| Deburring, Material Type, Via Plating Method, Specify Stackup fehlten | ergänzt (Yes / FR4 TG135 / Horizontal Electroless / No) | Screenshot |
| Versand DHL 23.44 USD | **23.52 USD**, 0.41 kg (20 PCB unbestückt) | Screenshot; `scripts/cost_model.py` nachgeführt |
| Remark „All vias epoxy filled … Order number at the JLCJLCJLCJLC placeholder“ | Füllung aller 0.30-mm-Bohrungen ausdrücklich, Platzhalter löschen | JLC Via-Covering-Hilfe; Mark on PCB |
| PCBA-Felder | weiter **ANNAHME** (Schalter „PCB Assembly“ war aus) | Kap. 3 |
| Red Team Phase 5 (`docs/reviews/phase5_bestellung_kosten_redteam.md`) | Platzhalter aus Layout (W-4, Hashes folgen), Rotationsregel „nie selbst drehen“ + roter Punkt (W-2), Pre-reflow als Stopp (W-3), Kap. 6 Beträge (K-1), Remark als Textdatei ohne Projektkoordinate (K-4) | Antwort Ersteller im Bericht |
