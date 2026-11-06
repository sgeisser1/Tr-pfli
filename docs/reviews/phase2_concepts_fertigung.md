# Prüfbericht Phase 2 – Konzepte, Fokus Fertigung / Bauteile / Kosten

| | |
|---|---|
| Geprüft | `docs/concepts/CONCEPTS.md` v0.1, `docs/concepts/bom/*.csv`, `scripts/cost_model.py`, `scripts/concept_costs.py`, `docs/datasheets/INDEX.csv` |
| Grundlagen | `REQUIREMENTS.md` v1.0 (Kap. 10, RB-09), `CLIENT_INPUT.md` (JLC-Preise, Versand) |
| Prüfer | fertigung-dfm (frischer Kontext) |
| Datum | 2026-11-06 |
| Eigene Rohdaten | Scratchpad `dfm2/` (nicht im Repo): `raw/*.json` (JLC-Teilesuche, alle 47 LCSC-Nummern aller BOMs), `jlc_parts.json`, `own_cost.py` + `own_cost_out.txt`, `web/asm_price.txt` |

## 0 Ergebnis in Kürze

Die BOM-Daten (LCSC-Nummer, Basic/Extended, Lager, Preis @20) stimmen mit der JLC-Teilesuche
überein, die Kostenrechnung ist in sich korrekt und für die Serie (Stückkosten) unabhängig
reproduzierbar (A 10.35 CHF, A2 9.07 CHF). Es gibt aber **1 kritischen Bauteilbefund**
(48-MHz-Quarz mit falscher Lastkapazität) und **mehrere fehlende oder unklare Kostenposten**
(Röntgen, Pre-reflow, Prototyp-Staffelpreise, Preferred-Extended), die die Einmalkosten um bis zu
+22 CHF verschieben und bei ungünstiger Auslegung von „Pre-reflow“ das Stückkostenziel kippen.

## 1 Vorgehen

1. Alle 47 LCSC-Nummern aus `bom_*.csv` (A/A2 vollständig 27, B 19, C 38) über
   `selectSmtComponentList` abgefragt (Abruf 2026-11-06), Felder: Modell, Gehäuse,
   `componentLibraryType`, `preferredComponentFlag`, `stockCount`, `leastPatchNumber`,
   `lossNumber`, `minPurchaseNum`, `encapsulationNumber`, Preisstaffeln, Attribute.
2. Basic-Alternativen gesucht (Stichworte 74LVC1G14, 32.768kHz, 2.7nH, 1.5pF, 10uH, CR2450, 48MHz).
3. Gebührenseite https://jlcpcb.com/help/article/pcb-assembly-price („Last updated on Oct 22, 2026“)
   und https://jlcpcb.com/solutions/pcb-prototype-assembly selbst abgerufen.
4. EZB-Kurs selbst abgerufen: 2026-11-06 EUR/USD 1.1165, EUR/CHF 0.9143 → 0.8189 CHF/USD (bestätigt).
5. Kosten mit eigenem Skript (`own_cost.py`, ohne `cost_model.py`) nachgerechnet; Datenblätter
   (CC2340, TAITIEN, Epson, MYOUNG-Zeichnung) per `pdftotext`/Bild gegengeprüft.

## 2 Befunde

### K-1 (kritisch) 48-MHz-Quarz C5160139 hat CL = 20 pF, CC2340 erlaubt 5–9 pF
- **Beleg:** JLC-Attribut C5160139 „Load Capacitance = 20pF, ±20ppm“ (Abruf 2026-11-06).
  `TI_CC2340R5_Datasheet_SWRS272F.pdf` S.26, Tab. 7.20.3.1: CL min 5 / typ 7 / max 9 pF, ESR ≤ 60 Ω.
  Die lokale Datei `TAITIEN_XXHCELNANF-48MHZ_Datasheet_LCSC-2022-10.pdf` ist ein Seriendatenblatt
  (Standardfrequenzen 16–40 MHz, keine CL-Angabe zu dieser Bestellnummer) und belegt das Teil nicht.
- **Wirkung:** Der interne Kapazitätsabgleich des CC2340 erreicht 20 pF nicht → Frequenzablage
  (BLE-Toleranz ±50 ppm gefährdet) oder schlechter Anschwingen. Betrifft A, A2 und C.
- **Vorschlag:** Ersetzen, z. B. HCI XC32M4-48.000-F08NLDT **C2925606** (3225, 8 pF, ±10 ppm,
  ESR 40 Ω, Lager 8 817, 0.099 USD) oder TKD SX20Y048000B71T014 **C20623612** (2016, 7 pF, ±10 ppm,
  40 Ω, Lager 33 217, 0.118 USD); beide Extended (kein Basic-48-MHz-Quarz gefunden). Das von TI
  validierte Tai-Saw TZ3908AAAO43 (C22367622) hat Lager 0. Herstellerdatenblatt laden und registrieren.

### W-1 (wichtig) Röntgenprüfung (X-ray) fehlt im Kostenmodell
- **Beleg:** JLC-Gebührenseite (Oct 22, 2026): „X-ray Inspection (Component Quantity) 1–10 pcs:
  $1.64/pc, 11–50 pcs: $0.82/pc …“, gleich für Economic und Standard; „required for components
  such as BGA, QFN, and other leadless packages“. In `JLCPCB_NOTES.md` Tab. 1 dokumentiert, in
  `cost_model.py` nicht enthalten.
- **Wirkung (ANNAHME: CC2340 VQFN-24 + TMP1075 WSON-8 = 2 Stk/Board):** Prototyp 5/2: 4 × 1.64 =
  **6.56 USD**; Serie 15/15: 30 × 0.82 = **24.60 USD** (≈ +22 CHF Einmalkosten inkl. MWST).
  Stückkosten nach REQ-FAB-04 unverändert (Einmalposten).
- **Vorschlag:** Posten in `cost_model.py` aufnehmen (Anzahl leadless Bauteile pro Board als
  BOM-Spalte); Anwendbarkeit (Kristalle? WSON?) mit einem echten Warenkorb-Angebot klären.

### W-2 (wichtig) „Pre-reflow Soldering 0.016 USD/Lötstelle“ ungeklärt – Hebel auf REQ-FAB-04
- **Beleg:** gleiche JLC-Seite, beide Spalten; `cost_model.py` Z. 84–87 (`APPLY_PRE_REFLOW = False`).
- **Wirkung:** Würde er auf alle 116 Lötstellen von A angewandt: 1.86 USD/Board ≈ **+1.67 CHF/Sensor**
  (inkl. Kartenaufschlag und MWST) → A 4 L ≈ 12.0 CHF, A2 ≈ 10.7 CHF, beide über dem Ziel.
  Vermutlich betrifft er nur Pin-in-Paste/THT (ANNAHME), belegt ist das nicht.
- **Vorschlag:** Vor der Lagen- und Konzeptfreigabe ein **reales JLC-Angebot** mit Dummy-Gerber,
  BOM und CPL (A, 4 L und 2 L, 2 und 15 Stk) im Warenkorb erzeugen lassen (Auftraggeber, ≈ 10 min).
  Damit lassen sich W-1, W-2, W-3 und die 65-USD-Grenze (W-5) in einem Schritt klären.

### W-3 (wichtig) Prototyp-Stückkosten mit @20-Preisen statt Bestellstaffel
- **Beleg:** `concept_costs.py` nutzt für alle Szenarien `p20`. Bei 2 Boards bestellt JLC 2 + lossNumber
  Stück → Staffel 1–9: CC2340 1.5864 statt 1.3375, TMP1075 0.3995 statt 0.3111, Halter 0.5845 statt
  0.4748 USD.
- **Wirkung:** Bauteile 3.47 statt 3.02 USD/Board; Prototyp-Stück A 4 L **14.35** statt 13.95 CHF,
  A2 **9.76** statt 9.39 CHF. Serie (15 Stk → Staffel 10–49 = p20) korrekt.
- **Vorschlag:** Preis nach Staffel der tatsächlichen Bestellmenge rechnen (Staffeln liegen in der
  API-Antwort vor).

### W-4 (wichtig) Variante A-H (Halter auf der Rückseite) ist mit Economic PCBA nicht bestückbar
- **Beleg:** `JLCPCB_NOTES.md` Tab. 2: Economic „nur eine Seite (SMT/THT)“; CONCEPTS 2.5 „Halter auf
  der Rückseite (Hand-Lötung …)“. Wer lötet, ist offen; JLC Economic lötet nicht auf der Gegenseite.
- **Wirkung:** Entweder Standard PCBA (Setup 51.12 statt 8.18 USD beidseitig, Schablone 16.42,
  Fixture 16.42, min. 70 × 70 mm → Panel, Handling fee ≥ 14.93 USD) oder Halter selbst löten:
  dann Halter aus der JLC-BOM nehmen, separat bei LCSC kaufen (eigener Versand/Zoll) und als LOKAL
  rechnen; die Extended-Gebühr des Halters fällt dann weg (−3.07 USD).
- **Vorschlag:** A-H in CONCEPTS als „Halter vom Auftraggeber gelötet“ kennzeichnen und Kosten
  (Halter LCSC + Lötaufwand, REQ-FAB-03) ausweisen. In der Basisvariante A liegen alle bestückten
  Teile auf einer Seite – in Ordnung.

### W-5 (wichtig) Knappe Grenzen beim 2-Lagen-Prototyp (GSDL 65 USD, MWST-Freigrenze 5 CHF)
- **Beleg (eigene Rechnung):** A2 5/2 Warenwert 52.6 USD (ohne Röntgen) bzw. 59.1 USD (mit) ≤ 65 USD;
  Rechnung 66.75 USD = 54.66 CHF → MWST 4.43 CHF ≤ 5 CHF → frei. Freigrenze wird ab Rechnung
  ≈ 75.4 USD überschritten, dann **Post-Verzollung 16 CHF + 3 %** (deutlich teurer als die MWST).
- **Offen:** Ob die 65-USD-Grenze den Warenwert mit oder ohne Versand meint, ist nicht belegt
  (Modell: ohne). Ob GSDL in CH durch die Post verzollt wird, ist ANNAHME (`cost_model.py` Z. 140).
- **Vorschlag:** Im JLC-Angebot (W-2) prüfen; im Dokument den Abstand zu beiden Grenzen nennen.

### W-6 (wichtig) Ausschuss/Reserve in der Serie nicht vorgesehen
- 15 PCB / 15 bestückt lässt kein Ersatzboard für Bestückungs- oder Inbetriebnahmeausfälle.
  Bauteil-Attrition (lossNumber) ist enthalten, Board-Ausschuss nicht.
- **Vorschlag:** Serie 20 PCB / 16 bestückt rechnen (PCB 4 L 39.0 statt 36.8 USD, + 1 Board Teile
  ≈ 3.2 USD) oder bewusst 0 % Reserve festhalten.

### k-1 (klein) Preferred Extended C1552 kostet keine Extended-Gebühr
- **Beleg:** API `preferredComponentFlag = true` für C1552 (1.5 pF); JLC prototype-assembly-Seite:
  „Preferred extended parts are also fee-free on Economic PCBA.“
- **Wirkung:** A/A2/C: 8 statt 9 gebührenpflichtige Extended-Typen → **24.56 statt 27.63 USD**.
- **Vorschlag:** Kategorie `preferred` in BOM-CSV und Modell einführen.

### k-2 (klein) Doppelte Typen in den BOMs
- C17168 (0 Ω) erscheint in A zweimal (π-Netz, Messbrücke) → 18 statt 19 Basic-Typen; in C ebenso
  C15127, C25117, C25879, C52923. Attrition wird dadurch doppelt gerechnet (Betrag < 0.05 USD).
- **Vorschlag:** In `concept_costs.py` Zeilen nach LCSC-Nummer zusammenfassen; Typenzahl korrigieren.

### k-3 (klein) Registerlücken (Auftrag Punkt 4)
- Alle 27 LCSC-Nummern von A/A2 geprüft. In `docs/datasheets/INDEX.csv` **fehlen C1548**
  (FH 0402CG150J500NT, 15 pF) und **C1555** (FH 0402CG220J500NT, 22 pF). Die 25 übrigen haben einen
  Eintrag mit vorhandener lokaler Datei (Serien-PDFs für R/C).
- Das Seriendatenblatt `FH_0402CG-Serie_Datasheet_LCSC-2023-04.pdf` deckt die Werte vermutlich ab;
  dann die LCSC-Nummern in der C1552-Zeile ergänzen.
- C5160139: lokale Datei belegt das Teil nicht (siehe K-1).
- CONCEPTS Kopf/OP-K11 sagt „Register in `_staging`, Übernahme offen“, `INDEX.csv` enthält die
  Konzeptteile aber bereits, `_staging/INDEX_konzepte.csv` dagegen nicht alle (fehlen dort u. a.
  C20416850, C2870250, C35740, C964809). → Stand im Dokument nachführen.

### k-4 (klein) Halter-Kontaktoberfläche
- MYOUNG-Zeichnung `MYOUNG_BS-24-B4AA016_Drawing_A0.pdf`: Kontakte Phosphorbronze, „Au 1u\"“ (1 µinch
  ≈ 0.025 µm Flash) über Nickel; Gehäuse LCP UL94V-0; Betrieb −25…85 °C. „Vergoldet“ stimmt, ist
  aber nur ein Flash – für Kontaktsicherheit/Korrosion (REQ-SAF-CC-02) am Muster prüfen
  (PROTOTYP-PRÜFUNG). Gehäuse in BOM (SMD, 2 Pads, 37 × 16 mm, 2 Lötstellen) = Zeichnung.

### k-5 (klein) Lagerstände knapp bei einzelnen Teilen
- Kleinster Lagerstand A: C5160139 1 804 (ohnehin zu ersetzen), Halter C964809 2 042, B: C89132 5 075;
  C: **FDC2212 C968585 nur 310 Stk**. Für 15 + Ausschuss reicht alles; vor der Bestellung neu abfragen.

## 3 Teileprüfung Konzept A/A2 (alle 27 LCSC-Nummern, JLC 2026-11-06)

Übereinstimmung Modell, Gehäuse, B/E, Lager und Preis @20 mit CONCEPTS 2.2 und `bom_A.csv`: **ja für
alle 27**. Keine Reel-Mindestmenge (`minPurchaseNum = 1` bei allen), kein Pre-order/Global Sourcing.
Mindestmengen (`leastPatchNumber`) und Attrition (`lossNumber`) stimmen mit den BOM-Spalten moq/attrition.

| LCSC | Teil | Gehäuse JLC | B/E | Lager | p1 / p20 USD | least / loss | Bemerkung |
|---|---|---|---|---|---|---|---|
| C20416850 | CC2340R52E0RGER | VQFN-24 4×4 | E | 9 278 | 1.5864 / 1.3375 | 0 / 0 | Pitch 0.5 mm ≥ 0.4 (Economic ok) |
| C5160139 | XXHCELNANF-48MHZ | SMD3225-4P | E | 1 804 | 0.143 / 0.143 | 5 / 2 | **CL 20 pF → K-1** |
| C99010 | Q13FC13500003 | SMD3215-2P | E | 33 692 | 0.204 / 0.204 | 5 / 2 | CL 9 pF ok (6–12 pF) |
| C89132 | WPN201610H100MT | 0806 | E | 5 075 | 0.0418 | 5 / 4 | kein Basic-Leistungsinduktor (C1035 3 mA, C1046 15 mA) |
| C27123 | SDCL1005C2N7STDF | 0402 | E | 110 991 | 0.0031 | 20 / 10 | kein Basic 2.7 nH gefunden |
| C1552 | 0402CG1R5C500NT | 0402 | E **preferred** | 171 054 | 0.0045 | 20 / 10 | gebührenfrei → k-1 |
| C35740 | SN74LVC1G14DCKR | SC-70-5 | E | 98 074 | 0.0567 | 5 / 4 | kein Basic-LVC1G14 |
| C2870250 | TMP1075DSGR | WSON-8-EP 2×2 | E | 34 641 | 0.3995 / 0.3111 | 0 / 0 | leadless → W-1 |
| C964809 | BS-24-B4AA016 | SMD | E | 2 042 | 0.5845 / 0.4748 | 2 / 0 | SMT-Reflow-Typ, 2 Pads |
| C15525, C1525, C52923, C15008 | Samsung MLCC | 0402 / 1206 | B | Mio. | wie BOM | 20/10 bzw. 5/4 | ok |
| C1548, C1555 | FH C0G 15 / 22 pF | 0402 | B | 1.2 / 1.7 Mio | wie BOM | 20 / 10 | Register fehlt → k-3 |
| C17168, C25741, C25879, C25768, C25900, C25117, C25076, C11702 | UNI-ROYAL 0402 | 0402 | B | ≥ 1 Mio | wie BOM | 20 / 10–15 | ok |
| C15127 | AO3401A | SOT-23 | B | 1.70 Mio | 0.0829 | 5 / 4 | ok |
| C2286 | KT-0603R | 0603 | B | 6.65 Mio | 0.0077 | 20 / 10 | ok |
| C318884 | TS-1187A-B-A-B | SMD-4P 5.1×5.1 | B | 968 132 | 0.0207 | 5 / 8 | ok |
| C2128 | 1N4148WS | SOD-323 | B | 2.9 Mio | 0.0112 | 20 / 12 | ok |

Stichproben B/C (≥ 5): C39831287 CH592F (QFN-28, E, 27 866, 0.6696 ✓), C9009 32 MHz (E, 296 728,
CL 12 pF), C32346 (B ✓), C70377 CR2032-BS-6-1 (E, 57 793 ✓; API `componentProductType = 2` –
Bedeutung unklar, im Angebot prüfen, ob als SMT akzeptiert), C968585 FDC2212 (E, **310** ✓ Preis),
C456012 USB-C (E ✓), C2984676 PPTC 1206 (E ✓), C27001 237 k (E, 2 437 ✓). Alle Werte = BOM.

**Bestückbarkeit Economic:** kleinste Bauform 0402, kleinster Pitch 0.5 mm (VQFN/WSON) – innerhalb der
Economic-Grenzen (0402, 0.4 mm). Platine 22 × 150 mm ≥ 10 × 10 mm, 1.6 mm, 2 oder 4 Lagen, 2–50 Stk:
zulässig. Basisvariante A: alle Teile einseitig. A-H: siehe W-4.

## 4 Kostenrechnung – unabhängig nachgerechnet (`own_cost.py`)

Annahmen wie Dokument: 0.8189 CHF/USD (EZB, bestätigt), Kartenaufschlag 1.5 % (ANNAHME), MWST 8.1 %
auf Rechnung inkl. Versand, Freigrenze 5 CHF, DHL-Gebühr max(3 CHF; 2 %), Post 16 CHF + 3 %, Zoll 0.
Abweichend: Teilepreise nach Bestellstaffel, 8 statt 9 Extended-Gebühren (k-1), Röntgen wahlweise.

| Szenario | Dokument Stück / Einmal / Total CHF | Eigen ohne Röntgen | Eigen mit Röntgen (ANNAHME 2 Stk/Board) |
|---|---|---|---|
| A 4 L Prototyp 5/2 (DHL) | 13.95 / 78.63 / 106.53 | 14.35 / 75.86 / 104.56 | 14.35 / 81.74 / **110.45** |
| A 4 L Serie 15/15 (DHL) | **10.35** / 60.50 / 215.80 | **10.35** / 57.73 / 213.03 | **10.35** / 79.81 / **235.11** |
| A2 2 L Prototyp 5/2 (GSDL, MWST-frei) | 9.39 / 44.23 / 63.01 | 9.76 / 41.66 / 61.18 | 9.76 / 47.12 / **66.63** |
| A2 2 L Serie 15/15 (DHL) | **9.07** / 60.50 / 196.60 | **9.07** / 57.73 / 193.84 | **9.07** / 79.81 / **215.92** |

Vollkosten pro Sensor (Total / 15) in der Serie: A 14.2–15.7 CHF, A2 12.9–14.4 CHF.
Nicht enthalten: Pre-reflow (W-2, bis +1.67 CHF/Stück), Board-Reserve (W-6), Versand der lokal
gekauften Zellen/Halter, USB-UART-Adapter (einmalig).

Geprüft und korrekt: Setup 8.18, Schablone 1.53, SMT 0.0016 USD × 116 Lötstellen = 0.19 USD/Board,
PCB-Preise = CLIENT_INPUT (4 L 32.3/36.8, 2 L 6.9/10.4), GSDL nur ≤ 65 USD (nur 2-L-Prototypen),
MWST/Freigrenze, DHL-Gebühr, Wechselkurs, Mindestabnahme-/Attritionsüberschuss (2.83 USD Serie).

## 5 Prototyp-Strategie (beide Lagenvarianten)

- **Sinnvoll:** REQ-MECH-04 verlangt den dokumentierten Vergleich; der Mehrpreis 4 L → 2 L
  (1.58 CHF/Sensor) ist gross genug, um ihn am Muster zu entscheiden. Zwei getrennte Bestellungen
  sind nötig (unterschiedliche Lagenzahl, kein gemeinsames Panel). Gemeinsamer Versand bringt nichts
  (Summe > 65 USD → DHL statt GSDL, dann MWST auch auf A2).
- **Richtig gerechnet:** im Prinzip ja; Summe Dokument 169.54 CHF, eigen 165.74 (ohne) bzw.
  **177.08 CHF** (mit Röntgen). Setup, Schablone und Extended-Gebühren fallen zweimal an – korrekt
  im Dokument so (zwei Rechnungen).
- **Verbesserung:** Nur 2 bestückte Boards je Variante sind für Becherversuch, 30-Tage-Wassertest,
  Funk-/Reichweitentest und Strommessung knapp, und die 3 übrigen Platinen sind mit VQFN/WSON in der
  Werkstatt kaum bestückbar. 5/5 statt 5/2 kostet bei JLC nur ≈ 3 × 3.7 USD Teile + SMT + Attrition
  (lokale Teile nur bei Bedarf) → **Empfehlung 5/5 je Variante** (bzw. mindestens 5/3).
- **Reihenfolge:** K-1 (Quarz) vor jeder Bestellung beheben; W-2 per realem Angebot klären.

## 6 Zusammenfassung der Vorschläge an den Ersteller

| Nr. | Stufe | Vorschlag |
|---|---|---|
| K-1 | kritisch | 48-MHz-Quarz mit CL 7–9 pF (z. B. C2925606 / C20623612), Datenblatt registrieren |
| W-1 | wichtig | Röntgengebühr ins Modell |
| W-2 | wichtig | Reales JLC-Angebot (Pre-reflow, Röntgen, Grenzen) vor Lagenentscheid |
| W-3 | wichtig | Staffelpreise nach Bestellmenge |
| W-4 | wichtig | A-H: Lötweg und Kosten ausweisen |
| W-5 | wichtig | Abstand zu 65-USD- und 5-CHF-Grenze ausweisen |
| W-6 | wichtig | Board-Reserve in der Serie |
| k-1…k-5 | klein | Preferred-Kategorie, Duplikate, Register C1548/C1555, Halter-Flash, Lagerstände |
