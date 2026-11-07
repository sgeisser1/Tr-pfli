# fluidi Sensor Rev B – Bestellparameter JLCPCB / JLC PCBA (ENTWURF)

| | |
|---|---|
| Stand | 2026-11-07, Fertigung (DFM-Prüfung `docs/reviews/phase4_layout_revb_dfm.md`) |
| Status | **Entwurf, keine Bestellung.** Freigabe durch den Auftraggeber nötig. Feldnamen im JLC-Formular sind **ANNAHME** (Rechner nur per JavaScript, nicht skriptbar, `docs/references/JLCPCB_NOTES.md` Kap. 7) |
| Daten | `hardware/sensor/out/fluidi_sensor_gerber_jlc.zip`, `fluidi_sensor_bom_jlc.csv`, `fluidi_sensor_cpl_jlc.csv` (aus Commit 425174d bzw. Neulauf `gen/run_pcb.sh`) |
| Kosten | `hardware/sensor/out/COSTS_REV_B.md` (`gen/cost_rev_b.py`) |

## 1 Leiterplatte

| Parameter | Wert | Begründung / Quelle |
|---|---|---|
| Base Material | FR-4 | JLCPCB_NOTES Kap. 3 |
| Layers | **4** | Layout Rev B (`LAYOUT_REV_B.md` Kap. 1) |
| Dimensions | 26.0 × 158.5 mm (aus Gerber, automatisch) | `out/gerber/fluidi_sensor-Edge_Cuts.gm1`; Job-Datei 26.05 × 158.55 inkl. Linienbreite |
| PCB Qty | Prototyp **5**, Serie **20** | `COSTS_REV_B.md`; PCB-Mindestmenge 5 (JLCPCB_NOTES Kap. 2) |
| Product Type | Industrial/Consumer electronics | – |
| Different Design | 1 | – |
| Delivery Format | Single PCB (kein Nutzen) | Economic PCBA braucht keinen Nutzen/Randstreifen (JLCPCB_NOTES Kap. 2) |
| PCB Thickness | **1.6 mm** | Economic PCBA 0.8–1.6 mm (JLCPCB_NOTES Kap. 2) |
| Impedance Control / Layer Stackup | **JLC04161H-7628** (= Standard „No requirement“); Impedanzkontrolle **nein** | JLCPCB_NOTES Kap. 4; Economic: „Standard stack-up only“. 50-Ω-Leitung 0.35 mm über 0.2104 mm Prepreg, Er 4.4: ≈ 50.5 Ω (Hammerstad, ohne Lötstopp), ± 10 % Dicke → 47.5–53 Ω; genügt für AN043-Speisung, Abgleich ohnehin am Prototyp (PROTOTYP-PRÜFUNG) |
| Material / TG | Standard der Vorlage (laut Stackup-Daten NP-155F, TG 150, DRITTQUELLE) | JLCPCB_NOTES Kap. 4 |
| PCB Color | **Grün** | Economic-Tabelle: 1.6 mm ENIG nur grün (JLCPCB_NOTES Kap. 2) |
| Silkscreen | Weiss | – |
| Surface Finish | **ENIG** (1 µ") | Minuspad der Zelle auf der Leiterplatte (A-32, `phase2_concepts_sicherheit.md` S2-L06); Kosten +11.9 USD bei 5 Stk (CLIENT_INPUT). **Achtung:** Platinendatei steht noch auf „HAL lead-free“ (Befund DFM-W3) |
| Outer / Inner Copper | 1 oz / 0.5 oz | Stackup 0.035 / 0.0152 mm (`.kicad_pcb` setup) |
| Via Covering | **Epoxy Filled & Capped** (POFV) | **zwingend**: 5 Via-in-Pad im Zellfach (L-1, REQ-MECH-05), 1 im Clip-Pad mit Lotpaste, 4 im EP von U1; ohne Füllung Lotabfluss (JLC FAQ Q17). Aufpreis 4 L: +20.3 USD bei 5 Stk (CLIENT_INPUT 2026-11-06). Vias 0.45/0.30 mm, Restring 0.075 = JLC „preferred“ für POFV (JLCPCB_NOTES Kap. 8) |
| Min via hole size / diameter | 0.3 mm / 0.45 mm | kein Aufpreis (JLCPCB_NOTES Kap. 3, Kap. 8) |
| Board Outline Tolerance | ± 0.2 mm (Standard) | Sonde und Kragen: Toleranz in der Mechanik berücksichtigt (PCB_OUTLINE) |
| Mark on PCB / Order number | „Specify a location“ oder „Remove“ (**ANNAHME**: Option und Preis im Formular prüfen) | Platine hat **keinen** Platzhalter „JLCJLCJLCJLC“ (Befund DFM-K4); sonst setzt JLC die Nummer frei, ggf. auf Zellfach/Sonde |
| Electrical Test | Flying Probe (Standard) | – |
| Gold Fingers / Castellated / Edge plating | nein | – |
| Confirm Production File | **ja** (erste Bestellung) | Gerber-Vorschau von JLC gegen `out/pdf/fluidi_sensor_layout_lagen.pdf` prüfen; Kosten ANNAHME gering |
| Remark (Kommentar) | „Via-in-pad by design (battery contact pads, QFN EP). All vias epoxy filled and copper capped, flat. Inner layers only on probe section, no outer copper beyond Y −49 mm.“ | Rückfragen von JLC vermeiden |

## 2 Bestückung (PCBA)

| Parameter | Wert | Begründung / Quelle |
|---|---|---|
| PCBA Type | **Economic** | 4 L, 1.6 mm, 2–50 Stk, nur Oberseite (JLCPCB_NOTES Kap. 2); Kombination mit POFV/ENIG **nicht belegt** → BESTELL-PRÜFUNG |
| Assembly Side | **Top Side** | CPL: alle 50 Teile „Top“; B.Paste leer; TP4/TP5 auf B sind nur Pads |
| PCBA Qty | Prototyp **5** (alle), Serie **16** von 20 | `COSTS_REV_B.md` (D-013, 15 Sensoren + 1 Reserve) |
| Tooling holes / Fiducials | nicht nötig (Economic) | JLCPCB_NOTES Kap. 2 |
| Confirm Parts Placement | **ja** (0.45 USD) | Rotationen sind nur DRITTQUELLE (Kap. 3 unten) |
| Photo / X-ray | Röntgen für U1 (VQFN) wird automatisch berechnet | cost_model W-1 |
| Dateien | BOM `fluidi_sensor_bom_jlc.csv` (Spalten Comment/Designator/Footprint/LCSC Part #), CPL `fluidi_sensor_cpl_jlc.csv` (Designator/Mid X/Mid Y/Layer/Rotation, Ursprung = Hilfsursprung wie Gerber) | – |
| Nicht bestücken | C19, C20 (DNM, nicht in BOM/CPL); AE1, E1, TP1–TP5 (Leiterplattenstrukturen) | `fluidi_sensor_bom_extra.csv` |
| Lokal beschafft | Knopfzelle Panasonic CR2032 (D-006) – **nicht** von JLC | `fluidi_sensor_bom_extra.csv` |
| Programmierung / Coating | nein (nur Standard-PCBA möglich) | JLCPCB_NOTES Kap. 2 |

## 3 BESTELL-PRÜFUNG (vor dem Bezahlen, im JLC-Formular/Vorschau)

1. **Preise ablesen** (26 × 158.5 mm, 4 L, 1.6 mm, grün, ENIG, Epoxy Filled & Capped) für **5 und 20 Stk** und in
   `scripts/cost_model.py` / `gen/cost_rev_b.py` eintragen. Entscheidend: wachsen ENIG- und POFV-Aufpreis mit der
   Stückzahl? Grenzfall „mengenproportional“ → 15.91 CHF/Sensor (`COSTS_REV_B.md`, Ziel < 10 CHF verfehlt).
2. Wird **Economic PCBA** mit ENIG + Epoxy Filled & Capped angeboten (Option nicht ausgegraut)?
3. **Rotation/Polarität jedes Teils** in „Confirm Parts Placement“ (Pin-1-Lage gegen `out/pdf/fluidi_sensor_bestueckung_F.pdf`):
   - **U3 TMP1075N (SOT-563): keine Korrektur in der CPL, verdächtig** – gleiche Pinanordnung wie SOT-363 (Tabelle: +180°)
     und gleiche Tape-Lage wie U2/U4–U6 (TI Q3, `TI_TMP1075_Datasheet_SBOS854F.pdf` S. 34; `TI_SN74LVC1G14_…` / `TI_SN74LVC1G80_…`
     Pack Materials). Bei 180°-Fehler liegen V+ (Pin 5) und GND (Pin 2) vertauscht.
   - U1 (VQFN-24, +270°), U2/U4/U5/U6 (SOT-353, +180°), Q1/Q2 (SOT-23, −90°): Korrektur aus DRITTQUELLE-Tabelle.
   - D1 (LED 1615, Pin 1 = Anode unten links, Datenblatt S. 4), Y1 (Pin 1/3 Quarz, 2/4 GND; 90°-Fehler schliesst den Quarz
     gegen GND), BT1 (Clip-Lage), SW1, L1, Y2: ohne Korrektur.
4. Lagerbestand am Bestelltag (Abfrage 2026-11-07: BT1 C5213768 **654 Stk**, L1 C89132 4839, U4–U6 C473331 8059,
   Y1 C2925606 8817, U1 C20416850 9278 – knapp, aber ausreichend).
5. Gerber-Vorschau: 4 Kupferlagen in der Reihenfolge GTL/G1/G2/GBL, Kontur geschlossen, Elektroden nur auf L2/L3.
