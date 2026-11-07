# Phase 4 – Layout Sensor Rev B: Fertigbarkeit/DFM und Kosten (JLCPCB / JLC PCBA)

| | |
|---|---|
| Prüfer | Fertigung (frischer Kontext, nicht Ersteller) |
| Datum | 2026-11-07 |
| Geprüft | Commit 425174d, `hardware/sensor/` (Platine, `.kicad_dru`, `gen/run_pcb.sh`, `gen/cpl_jlc.py`, `out/…`), Rotationstabelle `docs/references/matthewlai_JLCKicadTools_cpl_rotations_db_2026-11-07.csv`, `docs/datasheets/INDEX.csv`, `docs/references/JLCPCB_NOTES.md`, `docs/concepts/bom/jlc_prices.json`, `scripts/cost_model.py`, `gen/cost_rev_b.py`, D-005 |
| Werkzeuge | KiCad 10.0.8 (WSL) `kicad-cli`, `pcbnew`-Python, eigene Skripte im Scratchpad, JLC-Teilesuche (API), WebFetch JLC-Seiten |
| Ergebnis | **Keine kritischen Befunde.** 7 wichtig, 7 klein. Fertigbar bei JLC als 4 L / 1.6 mm / ENIG / POFV / Economic PCBA, sofern die BESTELL-PRÜFUNGEN in `hardware/sensor/out/ORDER_JLC_REV_B.md` Kap. 3 bestanden werden |
| Geändert durch den Prüfer | `hardware/sensor/gen/cost_rev_b.py` und `hardware/sensor/out/COSTS_REV_B.md` (POFV, echte Kontur, Sensitivität), `docs/references/JLCPCB_NOTES.md` Kap. 8 (neu), `hardware/sensor/out/ORDER_JLC_REV_B.md` (neu, Entwurf). Nichts committet, nichts bestellt |

## 1 Gerber, Bohrdaten, DRC (Aufgabe 1)

**DRC selbst gelaufen** (Kopie der Platine im Scratchpad, KiCad 10.0.8 WSL,
`kicad-cli pcb drc --schematic-parity --severity-all`, einmal mit und einmal ohne `--refill-zones`):
**0 Verletzungen, 0 ungeroutet, 0 Paritätsfehler**, in beiden Läufen. Die Regeln in `.kicad_pro`/`.kicad_dru` sind
gleich streng wie JLC oder strenger (Tabelle unten). Damit gilt die DRC als Prüfung gegen die JLC-Regeln.

**Reproduzierbarkeit:** Die Gerber- und Bohrdaten habe ich mit den Optionen aus `run_pcb.sh` neu erzeugt. Ohne die
Datumszeilen sind alle 14 Dateien **byte-gleich** mit `out/gerber/`. Der Inhalt der ZIP-Datei ist identisch mit
`out/gerber/`.

**Vollständigkeit/Reihenfolge:** F_Cu `.gtl` (TF.FileFunction Copper,L1,Top), In1 `.g1` (L2), In2 `.g2` (L3),
B_Cu `.gbl` (L4), F/B_Mask `.gts/.gbs`, F/B_Paste `.gtp/.gbp` (B leer), F/B_Silkscreen `.gto/.gbo`, Kontur `.gm1`,
`PTH.drl` (Vias T1 0.30, Bauteilbohrung T2 0.30 = AE1 Pad 2), `NPTH.drl` (leer), `job.gbrjob` (4 Lagen, 1.6 mm,
Stackup 0.2104/1.065/0.2104). Das ist vollständig.

**Kontur:** Die Kontur ist geschlossen: 13 Segmente, Lücken < 0.1 µm an den zwei R2-Bögen. Masse 26.0 × 158.5 mm.
Die Sonde ist 20 mm breit, die Spitze 45° gefast, die Innenecken haben R 2 mm (fräsbar).

**Lageninhalt:** In der Sonde (Y < −60) gibt es nur Kupfer auf In1/In2 (Elektroden bis Y −143.5). F_Cu und B_Cu enden
bei Y −48.95 (Kragenfeld). Das Aussenkupfer hält 0.30 mm zur Kante ein (X ±12.70 bei Kante ±13.0).

| Grösse | Platine (gemessen mit pcbnew) | JLC 4 Lagen (Quelle) | ok |
|---|---|---|---|
| Bahnbreite min | 0.15 (F/B), 0.20 (In2), 0.30 (In1) | 0.09 (JLCPCB_NOTES Kap. 3) | ja |
| Abstand min (Regel) | 0.10 | 0.09 | ja |
| SMD-Pad–Pad versch. Netze | **0.150** (nur U3 SOT-563, KiCad-Bibliothek); sonst ≥ 0.20 | 0.15 (Kap. 8) | ja, am Limit (K-6) |
| Vias | 146 Stk, alle Ø 0.45 / Bohrung 0.30, Durchgang | Ø ≥ 0.45 / ≥ 0.3 ohne Aufpreis; 0.15–0.55 POFV-fähig (Kap. 3, 8) | ja |
| Via-Restring | 0.075 | 0.05 min, 0.075 „preferred“ für POFV (Kap. 8) | ja |
| PTH-Bauteilbohrung AE1.2 | 0.30 in Pad 0.9 × 0.5 → Restring 0.10 | PTH 0.15 absolut (Kap. 3); als Via gelesen 0.05 | K-2 |
| Bohrabstand | Regel 0.25 | Via–Via 0.2 (Kap. 8) | ja |
| Innenlage Bohrung–Kupfer | Regel 0.20; AE1.2 zu VDD auf In2 1.29 mm | Via 0.2, PTH 0.3 (Kap. 8) | ja |
| Kupfer–Kontur | ≥ 0.30, ab Z5A ≥ 1.25, Innenlage Fach ≥ 1.0 | ≥ 0.2 gefräst (Kap. 3, 8) | ja |
| Lötstoppsteg | Maskenexpansion 0; kleinster Steg 0.15 (U3) | 0.10 grün (Kap. 8) | ja |
| Silkscreen | Linien ≥ 0.15, Text ≥ 1.0 (DRC-Regel) | 0.15 / 1.0 (Kap. 3) | ja |
| Bauteile zur Kante | Courtyards ≥ 0.3 (LAYOUT Kap. 5) | Economic: > 0.3 empfohlen (FAQ Q14, Kap. 8) | ja |

**Via-in-Pad:** Gemessen habe ich **9** Vias in SMD-Pads, nicht nur die 5 aus L-1:
5 im Fach (BT1.1 Clip-Pad VBAT, BT1.2 Minuspad, TP1, TP2, TP3) und **4 im EP von U1** (±0.6 mm, unter den Pastenfenstern).
Siehe W-6.

## 2 BOM ↔ CPL ↔ Platine (Aufgabe 2)

- **Referenzen:** BOM 50, CPL 50, Platine 58. Jede BOM-Referenz steht in der CPL und umgekehrt. Nicht in BOM/CPL sind
  AE1 und TP1–TP5 (ExclBOM + ExclPos, richtig) und C19/C20 (DNP, richtig). E1 ist Schaltplan-Platzhalter ohne
  Footprint auf der Platine.
- **Footprints:** Für alle 50 Teile ist der Footprint in Platine und BOM gleich, und das LCSC-Feld in der Platine
  stimmt mit der BOM. Alle Teile liegen auf F.Cu. Die CPL-Koordinaten stimmen auf 1 µm mit den Footprint-Ursprüngen
  (Hilfsursprung 150/30, Y gespiegelt wie im Gerber).
- **LCSC selbst abgefragt** (JLC-Teilesuche, API `selectSmtComponentList`, **2026-11-07**, Rohdaten im Scratchpad):
  alle 26 Nummern gefunden. Kategorie, Modell, Gehäuse und Preisstaffeln sind identisch mit `jlc_prices.json`.
  Ergebnis: 15 Basic, C1552 Preferred-Extended, 10 Extended (BT1, D1, L1, L2, U1, U2, U3, U4–U6, Y1, Y2).
  Lager knapp, aber ausreichend: **C5213768 (BT1) 654**, C89132 4839, C473331 8059, C2925606 8817, C20416850 9278.
- **Gehäuse ↔ Datenblatt** (Stichproben):
  - D1: Footprint `fluidi:LED_RGB_TUOZHAN_1615` gegen `TUOZHAN_…_Datasheet_A0.pdf` S. 4 geprüft: Draufsicht
    1 unten links (Anode), 2 oben links, 3 oben rechts, 4 unten rechts; Pads 0.5 × 0.8, Lücke 0.7/0.2. Das stimmt.
    Die Pin-1-Marke liegt unten links.
  - Y1: KiCad `Crystal_SMD_3225-4Pin` gegen `HCI_XC32M4-48.000-F08NLDT_Datasheet_LCSC-2022-05.pdf` S. 1:
    Pin 1/3 Quarz, 2/4 GND, Pin 1 unten links. Das stimmt. In der Platine liegen X48P an 1, X48N an 3, GND an 2/4.
  - U2/U4–U6 (DCK), U3 (DRL), U1 (RGE): Gehäuse in BOM, JLC-Teilesuche (SC-70-5, SOT-563, VQFN-24 4 × 4) und
    TI-Datenblatt (Pack Materials) gleich.
- **DNP:** C19/C20 sind korrekt als DNP gesetzt (`--exclude-dnp`).

### Rotationen (DRITTQUELLE-Tabelle, nicht von JLC)

JLC schreibt nur vor: „Zero orientation … should match the component orientation in the packaging (tape/reel)“, und
die Nullorientierung kann je Bauteil abweichen (FAQ Q2/Q3, `JLCPCB_NOTES.md` Kap. 8). Die Footprintdaten der
JLC/EasyEDA-Bibliothek waren aus WSL nicht abrufbar (HTTP 403). Deshalb lässt sich **keine** Korrektur lokal
beweisen. Die TI-Tape-Quadranten (DCK Q3, DRL Q3, RGE Q2; Datenblätter Pack Materials, z. B.
`TI_TMP1075_Datasheet_SBOS854F.pdf` S. 34) lassen sich nicht widerspruchsfrei auf die Tabellenwerte abbilden
(DCK +180° ↔ RGE +270°). Die JLC-Bibliothek folgt also nicht einfach dem TI-Tape. Verwertbar ist nur der Vergleich
ähnlicher Gehäuse untereinander:

| Teil | KiCad-Footprint (lokal geprüft) | Korrektur | Beurteilung |
|---|---|---|---|
| Q1, Q2 SOT-23 | Pin 1/2 links, 3 rechts | −90 | üblich, plausibel; Fehlbestückung wäre sichtbar (1 vs 2 Pads) → Vorschau |
| U2, U4–U6 SOT-353 | Pin 1 oben links, 1–3 links | +180 | plausibel (Tabelle), Vorschau |
| **U3 SOT-563** | Pin 1 oben links, 1–3 links (**gleich wie SOT-353/SOT-363**) | **0 (keine Regel)** | **verdächtig**: Die Tabelle hat für SOT-363 +180, und das TI-Tape liegt wie bei DCK (Q3). Ein 180°-Fehler vertauscht V+ (Pin 5) und GND (Pin 2). → W-3 |
| U1 VQFN-24 | Pin 1 links oben | +270 | Regex trifft „VQFN-24-…“; plausibel, Vorschau |
| D1 LED 1615 (eigener FP) | Pin 1 unten links | 0 | unbekannt (eigener Footprint, JLC-Nullage unbekannt) → Vorschau, Polarität |
| Y1 3225-4 | Pin 1 unten links | 0 | 180° harmlos (symmetrisch); **90° schliesst den Quarz gegen GND** → Vorschau |
| BT1, SW1, L1, L2, Y2, C, R | 2-polig bzw. symmetrisch | 0 | nur 0/90 relevant, in der Vorschau sofort sichtbar |

## 3 Via-in-Pad im Zellfach, POFV (Aufgabe 3)

- **Fertigbarkeit:** Ja. Epoxy Filled & Capped ist für Via-Ø 0.15–0.55 mm verfügbar, ab 6 Lagen Standard, bei 4 Lagen
  „still requires charges“. Die Vias 0.45/0.30 entsprechen der JLC-POFV-Tabelle, der Restring 0.075 dem Wert
  „preferred“ (JLCPCB_NOTES Kap. 8, Web 2026-11-07, dort abgelegt).
- **Aufpreis (lokal belegt):** JLC-Rechner, vom Auftraggeber abgelesen 2026-11-06 (`docs/requirements/CLIENT_INPUT.md`):
  4 L 1.6 mm 5 Stk ENIG 44.2 → ENIG + Epoxy filled & capped 64.5 USD = **+20.3 USD**. Der Wert steht schon in
  `scripts/cost_model.py` (`SURCHARGE_EPOXY_VIA_USD`), wurde aber in `cost_rev_b.py` **nicht eingeschaltet** (W-1).
  **ANNAHME:** fix pro Bestellung. Bei 20 Stk und 26 × 158.5 mm wurde der Aufpreis nicht abgelesen.
- **Variante 2 VIP** (TP1–TP3 auf B ins Band): POFV ist eine Option für die ganze Platine, keine Gebühr je Via
  (JLC-Formular; ANNAHME, da nur Rechnerwert). Die Variante kostet also **gleich viel** (+20.3 USD/Bestellung,
  ≈ 18.2 CHF inkl. MWST, ≈ 1.21 CHF Vollkosten je Sensor bei 15 Stk). Ganz ohne POFV ginge es nur ohne jedes
  Via-in-Pad mit Lotpaste bzw. im Fach. Das geht nicht: Das Minuspad BT1.2 und das Clip-Pad BT1.1 lassen sich ohne
  Via nicht anschliessen (Z4 verbietet Aussenkupferbahnen). Der Entscheid L-1 (5 oder 2 VIP) ist deshalb **kostenneutral**
  und eine reine Frage von Sicherheit und Funktion.

## 4 Kosten Rev B (Aufgabe 4)

Ich habe `cost_model` unabhängig nachgerechnet (Serie 20/16/15, 4 × 100 µF):
- PCB-Grenzkosten 0.448 × 1.25 = 0.56 USD
- Bauteile ≈ 3.74 USD (U1 1.22, U4–U6 3 × 0.169 bei 50 Stk, U3 0.456, BT1 0.36, C1–C4 0.44, Y2 0.20 …)
- SMT 145 Lötstellen × 0.0016 = 0.23 USD
- Röntgen 0.82 USD
- Summe 5.36 USD × 0.8189 × 1.015 + MWST 0.36 = 4.81 CHF; × 16/15 + lokal 3.09 = **8.21 CHF**

Das stimmt mit dem Skript überein. Zählung: 10 Extended-Typen × 3.07 = 30.70 USD; 50 Teile; 145 Lötstellen, auch von
Hand nachgezählt.

Ergebnis nach der Nachführung (`COSTS_REV_B.md`, neu erzeugt):

| Szenario | Stück CHF | Einmal CHF | Voll/Sensor CHF |
|---|---|---|---|
| Prototyp 5/5 | 9.06 | 119.39 (vorher 101.17) | 32.94 |
| Serie 20/16/15, 4 × 100 µF | **8.21** | 121.26 (vorher 103.06) | 16.29 |
| Serie 20/16/15, 2 × 100 µF | **7.99** | 121.26 | 16.08 |
| Sensitivität: ENIG + POFV mengenproportional (Grenzfall) | **15.91** | 121.23 | 23.99 |

CHF-Kurs: 1 USD = 0.8189 CHF (EZB-Kreuzkurs 2026-11-06) + 1.5 % Karte (ANNAHME). Teilepreise: JLC-API 2026-11-07.
Ziel < 10 CHF: **erfüllt, wenn** die Aufpreise für ENIG und POFV fix pro Bestellung sind. Belegt ist das nicht (W-2).

## 5 Bestellparameter (Aufgabe 5)

Den Entwurf habe ich nach `hardware/sensor/out/ORDER_JLC_REV_B.md` geschrieben: 4 L, 1.6 mm, JLC04161H-7628, keine
Impedanzkontrolle, grün, ENIG, Epoxy Filled & Capped, 0.3/0.45 mm, Economic PCBA, nur Oberseite, Confirm Parts
Placement, BESTELL-PRÜFUNGEN.

50-Ω-Kontrolle: Breite 0.35 mm über 0.2104 mm Prepreg, Er 4.4, 35 µm → **≈ 50.5 Ω** (Hammerstad-Jensen, ohne
Lötstopp, eigene Rechnung). Bei ± 10 % Dicke liegt der Wert bei 47.5–53 Ω. Das bestätigt die ANNAHME aus LAYOUT Kap. 2,
eine Impedanzkontrolle ist nicht nötig.

## 6 Befunde

### Kritisch
Keine.

### Wichtig

| Nr | Befund | Begründung | Vorschlag |
|---|---|---|---|
| W-1 | **POFV-Aufpreis fehlte im Kostenmodell Rev B** | `cost_rev_b.py` rief `compute(…, enig=True)` ohne `epoxy_vias=True` auf, obwohl das Layout ohne POFV nicht fertigbar ist (9 Via-in-Pad). Einmalkosten waren um 20.3 USD (≈ 18.2 CHF) zu tief | **Vom Prüfer umgesetzt** (`POFV = True`, Quelle im Kopf). Ersteller bitte bestätigen |
| W-2 | Ziel < 10 CHF hängt an unbelegter Mengenunabhängigkeit von ENIG- und POFV-Aufpreis | Beide Aufpreise sind nur bei 5 Stk, 22 × 150 mm abgelesen. Wachsen sie proportional mit der Stückzahl, steigen die Stückkosten auf 15.91 CHF (Grenzfall). Die Wahrheit liegt dazwischen | Auftraggeber liest im JLC-Rechner 26 × 158.5 mm, 4 L, ENIG, POFV bei 5 und 20 Stk ab, dann Werte in `cost_model.py` eintragen (ORDER Kap. 3 Nr. 1). Rückfallebene bei hohem Aufpreis: OSP/HASL prüfen (Minuspad, Sicherheit) |
| W-3 | **U3 (SOT-563) ohne Rotationskorrektur, vermutlich falsch** | Die Tabelle hat keine SOT-563-Regel. Die gleiche Pinanordnung SOT-363 bekommt +180 (SOT-353 auch), und das TI-Tape liegt wie bei DCK (Q3). Bei einem 180°-Fehler liegen V+ und GND vertauscht (Teil defekt, SENS_PWR belastet). LAYOUT Kap. 8 führt SOT-563 ohne Begründung als „ohne Korrektur“ | In der JLC-Vorschau zwingend prüfen. Vorsorglich `"^SOT-563",180` als **eigene, markierte Projektregel** (nicht in der Drittquelle) in `cpl_jlc.py` ergänzen, wenn die Vorschau das bestätigt |
| W-4 | Oberfläche in der Platine HASL, im Kostenmodell und für das Minuspad ENIG | `.kicad_pcb` setup `copper_finish "HAL lead-free"`, Gerber-Job „Finish: HAL lead-free“. Die Kosten rechnen mit ENIG (A-32 Minuspad, S2-L06). Gefahr einer Fehlbestellung bzw. einer falschen Dokumentation | `pcb_build.py`/`gen_pcb.py`: `copper_finish "ENIG"` setzen, Gerber neu erzeugen. Im Formular ENIG wählen (ORDER) |
| W-5 | Economic PCBA zusammen mit POFV + ENIG ist nicht belegt | Economic: „Standard stack-up only“. Ob Sonderoptionen der Leiterplatte erlaubt sind, steht auf keiner JLC-Seite. Ohne Economic: Standard-PCBA mit Setup 25.56, Schablone 8.21, Fixture 16.42, Feeder auch für Basic, Mindestgrösse 70 × 70 mm (Nutzen nötig) → deutlich teurer | BESTELL-PRÜFUNG (ORDER Kap. 3 Nr. 2) vor der Freigabe Phase 5. Fallback mit `cost_model` (pcba="standard" + Nutzen) rechnen, falls nötig |
| W-6 | 9 statt 5 Via-in-Pad; 4 im EP von U1 nicht in L-1 dokumentiert | U1-EP-Vias liegen unter den Pastenfenstern. Ohne Füllung fliesst Lot ab, und es entstehen Lunker (JLC FAQ Q17). Mit POFV ist das unkritisch. Die DRC-Regel `VIP_FACH` betrifft nur das Fach | In LAYOUT Kap. 9 (L-1) ergänzen: „POFV zwingend für ganze Platine, auch U1-EP“. In der Platine Via-Attribut Filling/Capping setzen (KiCad 10 setup `filling`/`capping` stehen auf `no`), damit die Fertigungsdaten das ausweisen |
| W-7 | Bauteilregister nicht auf Rev-B-Referenzen nachgeführt | Alle 26 LCSC-Nummern haben eine Zeile und ein lokales Datenblatt (ok). Die Ref-Spalte widerspricht aber der BOM: „C1 C2“ (Rev B: C1–C4), „C6 … C24“ ohne C25, „R1 R9–R12“ ohne R13, **„R3 R4 R5 = 4.7k“ widerspricht „R3 = 1k“**, Zeile C23 (100 pF) für ein Teil, das in Rev B fehlt, R7 nur als „R-LED-G“. U1, U2, U4–U6, Y1, Q2, L2, C5/C9, C16/C17 sind nur über Konzeptnamen (U-SOC1, U-OSC1, U-DIV, Y-HF1 …) auffindbar, und „U2/U3/U4“ verweisen dort auf andere Teile (Konzept LI) | Block „Rev B“ mit einer Zeile je BOM-Position (Ref-Liste wie `fluidi_sensor_bom_jlc.csv`, LCSC, Footprint, Datenblattpfad) anlegen und veraltete Rev-A-Zeilen als „Rev A“ markieren. Abgleich per Skript aus `bom_raw.csv` |

### Klein

| Nr | Befund | Begründung | Vorschlag |
|---|---|---|---|
| K-1 | DRC-Regel Pad–Pad 0.15 fehlt | Die globale Regel (0.10) erlaubt SMD-Pads verschiedener Netze bis 0.10, JLC verlangt 0.15. Heute ist das Minimum 0.150 (U3, Bibliothek). Neue Footprints würden aber nicht geprüft | In `pcb_rules.py`: `(rule "JLC SMD Pad-Pad" (condition "A.Type=='Pad' && B.Type=='Pad'") (constraint clearance (min 0.15mm)))` |
| K-2 | AE1 Pad 2 (PTH 0.30 in Pad 0.9 × 0.5): Restring 0.10 < PTH-Minimum 0.15 | Pad aus der KiCad-Bibliothek, als Bauteilbohrung exportiert. JLC dürfte die 0.30-Bohrung als Via behandeln (0.05 min); mit POFV wird sie gefüllt | Akzeptieren oder das Pad durch ein GND-Via 0.45/0.30 ersetzen. In der Gerber-Vorschau prüfen |
| K-3 | Rotationsquelle ist DRITTQUELLE, für KiCad-5/6-Footprints | Die Footprint-Geometrie von KiCad 10 ist für SOT-23/SOT-353/VQFN geprüft und unverändert (Pin 1 oben links). D1 ist ein eigener Footprint | ORDER Kap. 3 Nr. 3. Nach der ersten Bestellung die bestätigten Rotationen als Projekttabelle unter `docs/references/` ablegen |
| K-4 | Kein Platzhalter für die JLC-Auftragsnummer | Ohne Vorgabe setzt JLC die Nummer selbst, möglicherweise in den Fachbereich oder unter die Wortmarke | „JLCJLCJLCJLC“ auf B.Silkscreen im Band setzen und „Specify a location“ wählen (Option/Preis ANNAHME, im Formular prüfen) |
| K-5 | Gerber-Job „Revision: rev?“ | Titelblock der Platine ohne Revision (Projektvariable REV = B ist gesetzt, wird aber nicht übernommen) | `title_block (rev "B")` im Generator setzen |
| K-6 | U3-Padabstand genau am JLC-Minimum (0.150) | Toleranz null. Der Lötstoppsteg (0.15 ≥ 0.10) ist ok | Keine Änderung. In der Vorschau auf Lötbrücken achten (PROTOTYP-PRÜFUNG Sichtkontrolle U3) |
| K-7 | CPL/Gerber-Ursprung oben in der Mitte → negative Y-Koordinaten | Gerber und CPL sind konsistent (Hilfsursprung). JLC richtet in der Vorschau an den Pads aus. Negative Werte sind bei JLC nicht ausdrücklich dokumentiert | Beibehalten. Bei Versatz in der Vorschau den Ursprung unten links setzen (`aux_axis_origin`) |

## 7 Offene BESTELL-/PROTOTYP-PRÜFUNGEN

- BESTELL-PRÜFUNG (ORDER Kap. 3): Preise 5/20 Stk mit ENIG + POFV; Economic mit POFV/ENIG; Rotation aller Teile in
  „Confirm Parts Placement“ (U3, U1, Q1/Q2, U2/U4–U6, D1, Y1 besonders); Lager BT1 (654 Stk).
- PROTOTYP-PRÜFUNG: Lötbild U1-EP und Clip-Pad BT1 (POFV eben?), Sichtkontrolle U3 auf Brücken, Planität des
  Minuspads (Kontakt der Zelle).

## Quellen (Web, abgerufen 2026-11-07, in `docs/references/JLCPCB_NOTES.md` Kap. 8 abgelegt)

- [JLCPCB PCB Capabilities](https://jlcpcb.com/capabilities/pcb-capabilities)
- [JLCPCB Blog: Free Via-in-Pad on 6-20 Layer PCBs with POFV](https://jlcpcb.com/blog/Free-Via-in-Pad-on-6-20-Layer-PCBs-with-POFV)
- [JLCPCB Blog: Via filling guide](https://jlcpcb.com/blog/via-filling-guide)
- [JLCPCB PCB Assembly FAQs Part 2](https://jlcpcb.com/help/article/pcb-assembly-faqs-part-2)
- [EEVblog: Vias on the pads of a BGA](https://www.eevblog.com/forum/microcontrollers/vias-on-the-pads-of-a-bga/) (DRITTQUELLE)
