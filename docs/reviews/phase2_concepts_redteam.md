# Tröpfli – Phase 2: Red-Team-Prüfung der technischen Konzepte

| | |
|---|---|
| Geprüft | `docs/concepts/CONCEPTS.md` v0.1, `docs/concepts/bom/*.csv`, `scripts/{energy_budget,cost_model,concept_costs,concept_energy}.py` |
| Grundlagen | `REQUIREMENTS.md` v1.0, `CLIENT_INPUT.md`, `PROJEKTAUFTRAG.md`, Datenblätter `docs/datasheets/` |
| Prüfer | Red Team (frischer Kontext, ohne Begründungskette der Ersteller) |
| Datum | 2026-11-06 |
| Eigene Rechnung | `/tmp/claude-1000/-home-sgeisser-git-Tr-pfli/8b053e22-18f3-446f-bac7-d1e0173ecf11/scratchpad/rt2/rt_energy_A.py` (Scratchpad, nicht im Repo; bei Bedarf nach `scripts/` übernehmen) |

Seitenangaben = PDF-Seite der lokalen Datei. Was ich nicht selbst belegen konnte, ist als **ANNAHME (RT)** markiert.

## 0 Urteil in Kürze

Die Wahl **CC2340R52 + Knopfzelle + ESP32-S3-Gateway** trägt. Sicherheit, OTA-Signatur und Laufzeit
sprechen dafür, und die Laufzeit hält auch im schlechtesten Fall, den ich gerechnet habe (≥ 28 Monate).
**Drei Punkte im Dokument halten der Prüfung nicht stand:**

1. Die **Messkette RC-Oszillator** lässt sich so nicht bauen: Die Zählgrenze liegt beim CC2340 und nicht beim
   LVC1G14, für die Umschaltung von Referenz und f1/f2 fehlt ein Schalter, und die Versorgung aus einem GPIO ist
   ungeregelt (K-1).
2. Die **Kostenaussage „4 L verfehlt um 0.35 CHF“** hängt nur daran, wie man die Kosten zuordnet (K-2).
3. Die **Zellwahl CR2450N** stützt sich auf ein Temperaturargument, das nur für Renata gilt. Die lokal
   vorhandene **Panasonic CR2032** erlaubt 65 °C ohne Rücksprache. Damit wird die Variante „A-32“ zur
   ernsthaften Alternative: Sie erfüllt REQ-MECH-02 und REQ-FAB-04 auch mit 4 Lagen (W-1).

## 1 Die drei tragenden Annahmen und ihre Prüfung

| # | Tragende Annahme | Eigene Prüfung | Ergebnis |
|---|---|---|---|
| T1 | Das RC-Oszillator-Messprinzip (LVC1G14, 1–20 MHz, ratiometrisch, f1/f2) funktioniert mit der Stückliste A | TRM, Datenblätter LVC1G14 und CC2340 | **nicht tragfähig wie beschrieben** → K-1 |
| T2 | A erfüllt die Energieziele mit grosser Reserve (82.5 Monate, Schlaf 2.93 µA, Mittelstrom 5.49 µA) | eigenes Skript mit Datenblattwerten | Laufzeit **bestätigt** (72 Monate pess., ≥ 28 Monate im ungünstigsten Fall). Schlaf ≤ 3 µA ist **rechnerisch verfehlt**, der Mittelstrom ≤ 8 µA **nicht belegt** → W-2 |
| T3 | Kosten: 4 L = 10.35 CHF (verfehlt), 2 L + Coating = 9.07 CHF (erfüllt) | `cost_model.py` nachgerechnet, Varianten gerechnet | Rechnung **korrekt**, Aussage **nicht robust** → K-2, W-5 |

Zusätzlich geprüft: Das Sicherheitsargument A gegen B (MCUboot/ECDSA beim CC2340, Quelle [Q24] in
`research_gateway.md`) ist plausibel, lokal aber nicht durch ein TI-Dokument belegt. Es bleibt OP-K8.

## 2 Unabhängige Energierechnung Konzept A

Ich habe die Rechnung neu aufgesetzt und nicht aus `energy_budget.py` abgeleitet. Datenblattwerte:

| Grösse | Wert | Quelle |
|---|---|---|
| Standby LFXT, DCDC / GLDO, typ | 0.74 / 1.15 µA | `TI_CC2340R5_Datasheet_SWRS272F.pdf` S.19/S.20 Tab. 7.9 |
| Standby bei 50 °C | ≈ 1.0 µA (Faktor ≈ 1.33) | dto. S.35 Abb. 7-7 (abgelesen) |
| TX 0 dBm DCDC / GLDO; RX | 5.1 / 9.0 mA; 5.3 / 9.0 mA | dto. S.20 Tab. 7.10 |
| HFXT-Anlauf | 200 µs typ | dto. S.27 |
| DCDC erst ab 2.2 V, darunter GLDO | – | dto. S.18 |
| Batteriemonitor intern (22 mV, 1.7–3.8 V) | → **kein Spannungsteiler nötig, 0 µA** | dto. S.19 Tab. 7.7 |
| GPIO-Pull-up 39–109 µA, VOH 2.52 V @ 2 mA (Standard-Pin) | – | dto. S.31 |
| TMP1075 Shutdown | **0.37 typ / 0.65 max (25 °C) / 3.5 max (−55…125 °C)** | `TI_TMP1075_Datasheet_SBOS854F.pdf` S.7 |
| TMP1075 Wandlung | 52 typ / 85 max µA, 4.5–7 ms | dto. S.6/S.7 |
| LVC1G14 Cpd; ICC; Ioff | 22 pF; ≤ 10 µA; ±10 µA | `TI_SN74LVC1G14_Datasheet_SCES218AA.pdf` S.8, S.7 |
| MLCC-Isolationswiderstand Samsung (Stücklistenteil!) | ≥ 100 MΩ·µF → ≤ 3 µA je 100 µF bei 3 V | `Samsung_CL31A107MQHNNNE_Catalog_2015-11.pdf` S.53 |
| AO3401A IGSS | ≤ 100 nA bei ±12 V | `AOS_AO3401A_Datasheet_Rev3.1.pdf` S.2 |
| CR2450N | 540 mAh, < 1 %/a, max. Dauerstrom 3 mA | `Renata_CR2450N_Datasheet_Rev08.pdf` S.1 |

Berücksichtigt wurden:

- **Puffer-Leckstrom:** Fall A = 0.5 µA (Annahme wie im Dokument), Fall DS = Datenblattgrenze.
- **Oszillator-Messstrom:** ≈ 1.0 mA bei 10 MHz (Cpd·V·f + R-Last), 3 Konfigurationen × 16 Mittelungen × 1 ms.
- **TMP1075:** im Shutdown, oder per GPIO geschaltet.
- **I²C-Pull-ups:** 0 µA, solange der Bus im Ruhezustand high ist. Wird der TMP1075 abgeschaltet, müssen die
  Pull-ups mit abgeschaltet werden, siehe k-4.
- **Spannungsteiler:** keiner; der interne Batteriemonitor genügt.
- **GPIO-Leckströme:** 0.1 µA (**ANNAHME (RT)**, das Datenblatt nennt keinen IIL).
- **Pessimistische Rechnung nach REQ-ENE-08:** Typwert × 1.5 bzw. Maximalwert, +20 %, 75 % nutzbare Kapazität, 2 %/a.

| Fall (1 min Reaktionszeit) | Schlafboden [µA] | Mittelstrom [µA] | Laufzeit [Monate] |
|---|---|---|---|
| realistisch | 1.31 | 1.98 | > 120 |
| pess., MLCC 0.5 µA (wie Dokument, aber mit TMP1075 0.65 µA) | 3.24 | **6.45** | **72.3** (Dokument: 5.49 / 82.5) |
| pess., TMP1075 per GPIO geschaltet | 2.52 | 5.59 | 81.4 |
| pess., MLCC 1 × 100 µF an der Samsung-Grenze | 5.74 | 9.45 | 52.0 |
| pess., MLCC 2 × 100 µF an der Samsung-Grenze | 8.74 | 13.05 | 38.9 |
| pess., Gateway-Scanausbeute 50 % (Advertising alle 7.9 s) **ANNAHME (RT)** | 3.24 | 10.86 | 45.9 |
| pess., +6 dBm statt 0 dBm | 3.24 | 6.77 | 69.4 |
| pess., ungünstigste Kombination | 8.74 | 18.59 | **28.0** |

**Ergebnis:** Für ein Advertising-Ereignis komme ich auf 40.5 µC pess. (Dokument: 40.9 µC). Das ist
deckungsgleich. Der Messzyklus ist energetisch unerheblich (< 0.02 µA im Mittel). Die Laufzeit (REQ-ENE-02) ist
in allen Fällen erfüllt. **Schlaf bei 25 °C pess.: 3.07 µA > 3 µA** (SoC 1.725 + TMP1075 0.65 + MLCC 0.5 +
FET 0.1 + GPIO 0.1). Erfüllt wird der Wert nur, wenn der TMP1075 per GPIO geschaltet wird (2.42 µA).

## 3 Befunde

### Kritisch

**K-1 Die Messkette RC-Oszillator ist nicht baubar wie beschrieben (betrifft REQ-MES-07/-11, BOM, Pins, Kosten).**

- *Zählgrenze:* Die asynchronen IO-Eingänge der LGPT werden **mit dem 48-MHz-Systemtakt synchronisiert**
  (`TI_CC23xx_TechnicalReferenceManual_SWCU193A.pdf` S.481, Abschn. 10.3.4). Die Ereignisse laufen zudem über
  die doppelt synchronisierte Event-Fabric (S.120). Theoretisch liegt die Grenze damit unter 24 MHz. Jede
  Halbperiode muss aber mindestens zwei Systemtakte lang sein, sicher zählbar sind also nur etwa **≤ 10–12 MHz**
  (**ANNAHME (RT)**, PROTOTYP-PRÜFUNG). Das Dokument verortet die Grenze beim LVC1G14 („24 MHz“, Kap. 2.6). Das
  ist der falsche Engpass. Der Bereich „1–20 MHz“ ist oben nicht erreichbar, und REQ-MES-11 (Salz) wird damit
  noch unsicherer. Nach `phase2_salt_loss.py` gilt bei σ = 0.05 S/m und 10 MHz: ε''/ε' = 3.6.
- *Fehlender Schalter:* Für die „ratiometrische Messung gegen die C0G-Referenz“ und „zwei Frequenzen über
  R f1/f2“ braucht es einen Umschalter (Analogschalter oder zweites Gatter). Die Stückliste A enthält **keinen**.
  Wie geschaltet wird, ist nicht beschrieben.
- *Versorgung:* Der Oszillator wird ungeregelt aus einem GPIO gespeist. Ein Standard-Pin liefert VOH = 2.52 V bei
  2 mA (CC2340 S.31). Die Speisung sackt also last- und frequenzabhängig ab. Die Schwellen streuen stark:
  VT+ 1.5–1.87 V, VT− 0.84–1.14 V bei 3 V (LVC S.7). Die Verzögerung tpd liegt bei 1.5–4.6 ns (3.3 V) bis
  2.8–9.9 ns (1.8 V) (LVC S.8). Diese tpd geht **additiv** in die Periode ein: bei 10–20 MHz sind das 5–20 %, mit
  Batteriespannung und Temperatur veränderlich. Ein Verhältnis zur Referenz kompensiert additive Fehler
  **nicht**. Die Elektronik-Recherche selbst fordert „festes Rail (LDO)“ (`research_elektronik.md` 6.3). Das
  Konzept übernimmt das ohne Begründung nicht.

*Vorschlag:*
- Arbeitspunkt auf 2–8 MHz legen.
- Speisung über einen High-Drive-Pin (DIO12/DIO24, CC2340 S.7) mit 100 nF vor Ort oder über einen P-FET (Basic
  AO3401A).
- Referenz-C und Zusatz-C für f2 über GPIO nach GND zuschalten (statt R umzuschalten), dann ist kein
  Analogschalter nötig.
- tpd über zwei Messungen mit verschiedenem R oder C herausrechnen (Periode = k·R·C + 2·tpd).
- Becherversuch (OP-K3) und Zählversuch am **ersten Muster**.
- Stückliste, Pinplan und Kosten nachführen.

**K-2 Die Kostenaussage „4 Lagen verfehlt REQ-FAB-04 um 0.35 CHF“ ist ein Zuordnungsartefakt.**

- `cost_model.py` rechnet den ganzen PCB-Preis in die Stückkosten (2.45 USD/Stk bei 15 Platinen). Setup,
  Schablone, Extended-Gebühren und Versand rechnet es dagegen zu den Einmalkosten. Die Grenzkosten einer
  4-Lagen-Platine betragen aber nur **0.45 USD** ((39.0 − 32.3)/15). Der Rest ist faktisch Werkzeug- bzw.
  Einrichtekosten.
- Nachgerechnet: **20 Platinen bestellen und 15 bestücken** ergibt nach demselben Modell **9.90 CHF**, Ziel
  erfüllt, bei nur +8.75 CHF Einmalkosten.
- Konsequent marginal gerechnet liegt A mit 4 L bei ≈ 8.6 CHF. Konsequent „Bestellung total / 15“ gerechnet sind
  es 14.39 CHF (4 L) bzw. 13.11 CHF (2 L).

*Vorschlag:* Dem Auftraggeber beide Sichten zeigen (Grenzkosten pro Stück **und** Total pro Los) und die
Definition „Stückkosten“ für REQ-FAB-04 einmal festlegen. Erst danach über die Lagen entscheiden. Der
Lagenentscheid sollte technisch fallen (Lebensdauer der Beschichtung, REQ-MES-06), nicht über 0.35 CHF.

### Wichtig

**W-1 Panasonic CR2032 übersehen. „A-32“ ist eine bessere Variante als A und gehört gerechnet.**

- `Panasonic_CR2032_Datasheet_2026-02.pdf` S.1: −30…+85 °C, Rücksprache **erst ab 70 °C**. Damit ist 65 °C
  (REQ-SAF-CC-05) ohne Rücksprache zulässig. Dasselbe gilt für die Panasonic CR2450 (620 mAh, S.1).
- Das Gegenargument „CR2032 in der Rücksprachezone“ (Kap. 3.6, 6.1, 7) gilt also nur für Renata.
- A mit CR2032: Meine Rechnung ergibt ≈ 34 Monate pess. und auch im ungünstigsten Fall (18.6 µA) ≈ 12 Monate.
  Das Dokument nennt 38.5 Monate nach `energy_budget.py` Tab. 3.
- Kopf ≈ 28 × 12 × 45 mm, Zelle −1.45 CHF. Für den TE-Halter kommen ENIG (+11.9 USD je Los) und +0.3 USD dazu.
  Grob gerechnet ≈ 9.7 CHF mit 4 Lagen (**ANNAHME (RT)**, nicht mit dem Skript gerechnet). Damit wären
  REQ-MECH-02 **und** REQ-FAB-04 erfüllt.
- Restrisiko: Mit dem Puffer an der Leckstromgrenze wird es eng (Leckstrommessung OP-K5).

*Vorschlag:* A-32 mit Panasonic CR2032 als gleichwertige Hauptvariante rechnen (BOM, Kosten, Energie) und am
Muster parallel aufbauen. Die Kosten der Panasonic-Zelle in der Schweiz belegen.

**W-2 Die Energie-Nachweise zu REQ-ENE-09 sind zu optimistisch formuliert.**

- **Schlaf:** Das Dokument nennt 2.93 µA, „knapp erfüllt“. Der TMP1075 allein braucht aber 0.37 typ / 0.65 max µA
  (S.7). Das ist mehr als die ganze Board-Annahme von 0.5 µA. Pessimistisch komme ich auf 3.07 µA, also
  **verfehlt**.
- **Mittelstrom ≤ 8 µA:** Nach REQ-ENE-08 gilt der Maximalwert. Für den Puffer kennt man nur die
  IR-Grenze, und mit ihr wird das Ziel verfehlt (9.5–13 µA). Ebenso, wenn das ESP32-Gateway wegen der
  WLAN/BLE-Koexistenz nur etwa 50 % Scanausbeute hat (10.9 µA). Das Modell nimmt `P_MISS` = 10 % ohne Beleg an
  (`energy_budget.py`). Die Gateway-Recherche führt genau das als Risiko R2.
- **REQ-ENE-06:** Pessimistisch sind 325 µF nominal nötig (`energy_budget.py` Tab. 6). Bestückt sind 2 × 100 µF.
  Pessimistisch ist die Anforderung damit nicht erfüllt.

*Vorschlag:*
- TMP1075 und seine Pull-ups an einen GPIO hängen (0 µA im Schlaf).
- REQ-ENE-09 als „rechnerisch nur mit Annahme X erfüllt, Nachweis Messung“ kennzeichnen.
- `P_MISS` an die Koexistenzmessung koppeln und die Werkseinstellung Reaktionszeit danach festlegen
  (REQ-SYS-05 erlaubt 2 min).

**W-3 Das GPIO-Budget des QFN24 ist falsch gezählt.**

- 12 DIO gibt es nur, wenn man DIO3 und DIO4 (32-kHz-Quarz) mitzählt (CC2340 S.7). Nutzbar sind **10**.
- UART-Bootloader und Trigger belegen DIO20, DIO6 und DIO21 (`TI_CC23xx_HWDesignGuide_SWRA834A.pdf` S.6–7,
  Tab. 3-2/3-4).
- Für Oszillator-Speisung, Oszillator-Eingang, Referenz, f2, SDA, SCL, LED, Taster und TMP-Speisung bleiben
  7 Pins für 9 Funktionen.

*Vorschlag:* Den Pinplan jetzt erstellen (OP-K8 vorziehen). Mehrfachnutzung festlegen (UART-Pins nach dem Boot,
Trigger = Taster) oder ein grösseres Gehäuse (RKP, 5 × 5 mm) prüfen.

**W-4 Kopfhöhe: Es gibt bessere Anordnungen als im Dokument.**

| Variante | Höhe | B × T | Kosten/Sicherheit |
|---|---|---|---|
| A (Dokument) | 62 | 30 × 17 | – |
| A-H, Halter hinten (Dokument) | 52 | 30 × 17 | Handlötung |
| **A-K:** Keystone-Halter **3009** (THM, CR2450, Länge **26.9 mm** statt 37) hinten | ≈ 42 | ≈ 30 × 16 | `Keystone_3034_Catalog_M65.pdf` S.1. Minuspol = PCB-Pad (ENIG nötig), Kontakte Sn-Ni statt Au, LCSC-Verfügbarkeit **nicht geprüft** |
| **A-F:** Zelle in einer Gehäusetasche hinter der PCB, Minuspol = ENIG-Pad, Pluspol = Federkontakt | ≈ 41 | ≈ 29 × 15 | +11.9 USD ENIG je Los, Halter (0.47 USD + 3.07 USD Gebühr) entfällt. Pad kleiner als die Minuskappe und Tasche mit ≤ 0.5 mm Spiel, damit kein Kurzschluss zum Plusrand entsteht. Verpolung fängt der AO3401A ab. Falltest PROTOTYP-PRÜFUNG |
| Halter quer (37 mm horizontal), T-förmige PCB | ≈ 40 | ≈ 41 × 17 | Querschnitt gleich gross wie Soll, aber 35 mm Breite verfehlt. Grössere PCB-Hüllfläche verteuert die Platine |
| **A-32** (W-1) | 38–45 | 28 × 12 | siehe W-1 (Keystone 3034 SMT: 23.1 mm) |

*Vorschlag:* A-F oder A-32 in der Designphase per CAD bewerten. Den Sicherheitsagenten zur pad-basierten
Kontaktierung anhören (REQ-SAF-CC-02).

**W-5 Die Kostenrechnung ist unvollständig. Unterschätzt sind ca. +0.5…1.2 CHF/Stück.**

- **Zweite Dichtung:** Sonde/Gehäuse und Batteriefach werden getrennt abgedichtet (REQ-SAF-05). Gerechnet ist nur
  eine Dichtung zu 0.15 CHF.
- **Gewindeeinsatz** für die unverlierbare Schraube fehlt.
- **Analogschalter bzw. Zusatzteile** aus K-1 fehlen.
- **AMS-Spülabfall** für das mehrfarbige Logo fehlt. Kommentar im Skript: „inkl. Fehldrucke nicht“.
- **Kein Ausschuss** für PCBA oder Druck. Bei 15 Stück macht 1 Ausschussstück +7 % aus.
- Die **PCB-Länge** ist mit 22 × 150 mm angesetzt. A braucht etwa 100 mm Sonde + 5 mm Dichtzone + ≈ 55 mm Kopf,
  also ≈ 160 mm. Den Preis neu ablesen lassen.
- **Coating für 2 L zu 0.30 CHF:** Acryl-Schutzlack eignet sich nicht für 30 Tage Dauerimmersion (REQ-MES-06).
  Gebraucht wird ein Epoxid-Tauchverfahren; Kosten, Zeit (REQ-FAB-03) und Exemplarstreuung der Schichtdicke
  (REQ-MES-07) sind offen.
- **Korrekt** sind: MWST, DHL-Verzollung, 3.07 USD pro Extended-Typ, Mindestabnahmen, Kartenaufschlag,
  GSDL-Grenze.

*Vorschlag:* Die Punkte als Zeilen in `concept_costs.py` aufnehmen (ANNAHME) und eine Zuschlagsspalte
„Ausschuss/Reserve 5 %“ einführen.

**W-6 Das Gateway-Risiko Koexistenz ist im Konzept nicht bewertet.**

Die Gateway-Recherche nennt die WLAN/BLE-Koexistenz (R2), Kap. 5 des Konzepts übernimmt sie nicht. Sie wirkt
auf REQ-SYS-05 und auf die Sensorenergie (W-2).

*Vorschlag:* Einen BLE-Koprozessor als Option budgetieren (z. B. ESP32-C3-Board über UART, **ANNAHME (RT)**
≈ CHF 5) und den Koexistenztest am Gateway-Muster zuerst durchführen.

### Klein

- **k-1** Die Pufferleck-Grenze stammt von Murata (50 Ω·F). Bestückt ist Samsung (≥ 100 MΩ·µF, S.53):
  3 µA statt 6 µA je 100 µF. Der Fall „pess. B“ ist damit doppelt so pessimistisch wie nötig.
- **k-2** Halter BS-24: Die Beschichtung ist „Au 1u"“, also eine Goldschicht von nur ≈ 0.025 µm über Ni
  (`MYOUNG_BS-24-B4AA016_Drawing_A0.pdf` S.1). „✔ Au“ in der Matrix relativieren.
- **k-3** Taster mit internem Pull-up: 39–109 µA, solange er gedrückt ist (CC2340 S.31). Ein dauernd gedrückter
  Taster (Gegenstand am Kopf) leert die Zelle in Monaten. Firmware: nach langem Druck den Pull-up abschalten.
- **k-4** Wird der TMP1075 abgeschaltet, müssen die I²C-Pull-ups am selben GPIO hängen. Sonst speisen sie den
  Sensor über SDA/SCL zurück (≈ 0.5 mA).
- **k-5** Den internen Batteriemonitor (S.19 Tab. 7.7) für REQ-ENE-05 im Konzept nennen. Er ist ein Vorteil:
  kein Teiler, kein Leckstrom.
- **k-6** Der BS-24 ist ein Einschiebehalter. Beim Kopf mit 0.5 mm Wandspiel ist zu prüfen, ob sich die Zelle
  überhaupt einsetzen lässt (CAD, PROTOTYP-PRÜFUNG).
- **k-7** Das Epson-Fehlerbudget rechnet mit 25 K statt ±20 K Abstand zum Umkehrpunkt (5–45 °C). Das ist
  konservativ und in Ordnung. Der Offset von ±20 ppm lässt sich zudem beim Gateway-Kontakt kalibrieren.

## 4 Ernsthafte Alternativen (Frage 6)

1. **A-32 (Panasonic CR2032)**: siehe W-1. Das ist die stärkste nicht betrachtete Variante.
2. **A-F (Zelle ohne SMD-Halter)**: siehe W-4. Sie hält die CR2450N-Reserve und erfüllt die Kopfhöhe.
3. **Funkmodul statt Chip-down:** Das würde das HF-Filter (2.7 statt 2.8 nH, OP-K9), die Quarze und die
   Spule ersetzen, also 4–5 Extended-Typen und das Abstimmrisiko. Verfügbarkeit und Preis eines CC2340- oder
   BG22-Moduls bei JLC habe ich **nicht geprüft**. Empfehlung: in Phase 3 kurz recherchieren.
4. **EFR32BG22** (C1864138, 1.94 USD, `energy_budget.py`): geringere Funkströme, ausgereifter signierter
   Gecko-Bootloader. Lokal fehlt das Datenblatt (OP-K2). Einen klaren Vorteil gegenüber A sehe ich nicht.

## 5 Stichproben ohne Befund

Diese Angaben habe ich gegen das Datenblatt bzw. per Nachrechnung geprüft und richtig gefunden:

- CC2340: VDDS 1.71–3.8 V, DCDC ab 2.2 V, LFXT-Last 6–12 pF (S.18/19/27), TX/RX- und Standby-Werte (S.19/20).
- TMP1075 DSG: ±1 °C von −40 bis 75 °C (S.6).
- CR2450N: 540 mAh, −40 bis +85 °C, Rücksprache > 70 °C (S.1).
- BS-24: 32.8 × 16 mm, Pads 37 mm, H 7.5 mm, −25 bis +85 °C (S.1).
- AO3401A: IDSS 1 µA / 5 µA bei 55 °C (S.2; die Einheit wird im PDF-Text als „mA“ dargestellt, Fontfehler).
- LVC1G14: Werte S.7/8.
- Kostenrechnung 10.35 CHF: nachvollzogen (5.66 USD × 0.8189 × 1.015 + 0.38 + 5.28).
- Extended-Zahl 9, Advertising-Intervalle 27.5 / 57.5 / 147.5 s.
- LCSC C964809 = MYOUNG BS-24-B4AA016 (lcsc.com, abgerufen 2026-11-06). Lagerbestand und Preis wurden auf der
  Seite nicht angezeigt.

Nicht geprüft: die übrigen LCSC-Lagerbestände und JLC-Basic-Status (keine API-Abfrage), MCUboot auf dem CC2340
(Phase 3), Koexistenz am ESP32-S3.

---

## Runde 2

| | |
|---|---|
| Geprüft | `CONCEPTS.md` v0.2, `phase2_concepts_response.md`, `DECISIONS.md` D-005, `scripts/{cost_model,concept_costs,concept_energy}.py` (selbst ausgeführt), `docs/concepts/bom/bom_A*.csv` |
| Eigene Rechnung | Scratchpad `/tmp/claude-1000/-home-sgeisser-git-Tr-pfli/8b053e22-18f3-446f-bac7-d1e0173ecf11/scratchpad/rt3/rt3_buffer.py` (nutzt `concept_energy.calc` und `energy_budget`) |
| Datum | 2026-11-06 |

### R2.0 Urteil in Kürze

K-1 und K-2 sind **sachgerecht gelöst**. Die Skripte rechnen 11.19 / 8.08 CHF reproduzierbar, und die
D-005-Regression stimmt. **Neu und wichtig:** (1) Die SWD-Pads funktionieren mit 2 × 100 kΩ grundsätzlich nicht.
(2) Der Puffer ist mit 4 × 100 µF inkonsistent dimensioniert. Mit 2 × 100 µF erfüllt **A-32** REQ-ENE-02 auch an
der Datenblatt-Leckgrenze, und damit kippt die Begründung „A vor A-32“. (3) Die Aussage „A erfüllt mit
CR2450 ≤ CHF 2.97“ ist eine korrekte Bedingung, aber kein Beleg, und sie hat 0 Reserve. Nichts Kritisches.

### R2.1 Messkette (K-1) – Prüfung gegen die Datenblätter

| Punkt | Prüfung | Ergebnis |
|---|---|---|
| Zählgrenze 2–6 MHz | 48-MHz-Synchronisation (TRM S.481). Bei 6 MHz entfallen ≥ 8 Systemtakte auf eine Periode | ✔ plausibel; f2 = 1.6 MHz liegt unter dem Bereich, ist aber unkritisch |
| Speisung DIO12 | High-Drive auf RGE-Pin 5 (DS S.7); VOH ≥ 2.47 V @ 10 mA (DS S.31) | ✔ |
| Pegel am Zähleingang | VIH = 0.8·VDDS (DS S.32). Das LVC-Ausgangssignal reicht bis zur Speisung (DIO12 ≈ VDDS) | ✔ Das 1.8-V-Rail wurde zu Recht verworfen |
| Ratiometrie | VT±/VCC driftet: 0.50–0.62 bei 3 V, 0.48–0.68 bei 2.3 V (LVC S.7). Die Steigung wird **je Messung** über Cref1 neu bestimmt, damit kürzen sich VT± und R | ✔ |
| tpd | In T1 − T0 fällt tpd heraus, in T0 bleibt es. Ohne Korrektur liegt der Fehler bei 2–10 % der Periode. Kalibrierung + VDD/T-Tabelle ist richtig, denn tpd lässt sich mit C-Umschaltung grundsätzlich **nicht** vom Sonden-C trennen (dafür wäre eine R-Umschaltung nötig). Den Rest schätze ich auf ≈ 1 % der Periode über VDD 3.0 → 2.2 V (**ANNAHME (RT)**) | ✔ mit PROTOTYP-PRÜFUNG |
| Strom | 0.9 mA ohne Querstrom: Der Schmitt-Eingang liegt dauernd zwischen den Schwellen, ΔICC ≤ 500 µA (LVC S.7) → ≈ 1.5 mA | klein, energetisch ohne Bedeutung |

**r2-k1 (klein):** Ist Cref „aus“ (GPIO hochohmig), bleibt Cref in Serie mit der Pinkapazität (≈ 5–7 pF,
DS S.32 CI GPIO, Wert der Analogpins). Die Aus-Kapazität beträgt damit ≈ 4–5 pF. Sie hängt von Spannung und
Temperatur ab, und die Gleichspannungslage des Pins ist undefiniert. Ausserdem sind DIO8 und DIO11 im ROM-Bootloader
**SPI-CLK/CS-Eingänge** (TRM Tab. 8-38, S.464) und floaten dort. Eine Fehldetektion von SPI statt UART ist denkbar.
*Vorschlag:* Den Eingangspuffer der Cref-Pins abschalten. Bootloader-Start und Aus-Kapazität über die Temperatur
als PROTOTYP-PRÜFUNG aufnehmen.

### R2.2 Pinplan QFN24 – Stichproben

Gegen DS S.7 und S.9–12 (Tab. 6-1) und TRM S.464–465 geprüft, alle **korrekt**: DIO8 = Pin 3, DIO11 = 4,
DIO12 = 5, DIO13 = 6, DIO16 = 7, DIO17 = 8, DIO20 = 9, DIO21 = 10, DIO24 = 12, RSTN = 13, DIO3/DIO4 = 14/15,
DIO6 = 19. High-Drive DIO12/16/17/24 ✔. I2C0SDA auf DIO16 (Mux 3) und I2C0SCL auf DIO17 (Mux 3) ✔.
DIO24 als T1C0 bzw. T0PE ✔. Bootloader serialIoCfgIndex 0: RX DIO20, TX DIO6, Trigger DIO21 aktiv low ✔.

**R2-W2 (wichtig): SWD über die Pads funktioniert nicht, und an DIO16 droht ein Ruhestromleck.**
- SWDIO hat einen internen Pull-up, SWCLK einen Pull-down, beide „enabled by default“ („On-chip
  pullup/pulldown resistors for SWDIO and SWCLK“, TRM S.22). Die Ströme liegen bei 39–109 µA (Pull-up) bzw.
  10–40 µA (Pull-down) bei 1.8 V (DS S.31) und sind bei 3 V höher.
- Über 200 kΩ Serienwiderstand fallen damit 8–20 V ab. Die Sonde kann die Leitung nicht umschalten. Dazu kommen
  die I²C-Pull-ups von 4.7 kΩ am selben Netz: Sie halten die Leitung fest, wenn TMP_PWR high oder low ist.
- Die Angabe „SWD nur langsam, ≤ 50 kHz“ (Kap. 2.2/2.7) ist daher falsch. SWD fehlt ganz.
- **Energiefalle:** Bleibt der interne Pull-up auf DIO16 nach dem Boot aktiv, speist er bei abgeschaltetem
  TMP_PWR über 4.7 kΩ den TMP1075 zurück. Das sind ≈ 66 µA, gegenüber einem Schlafbudget von 3 µA.
- *Vorschlag:*
  - SWD-Pads streichen. Programmiert wird nur über UART (REQ-FW-06 bleibt erfüllt), Debugging am LaunchPad.
  - Firmware-Regel: früh im Boot SWDCEN löschen und die Pulls an DIO16 und DIO17 abschalten (TRM S.952).
    Ob das bei einem per CCFG gesperrten Debugport geht, ist Phase 3 bzw. PROTOTYP-PRÜFUNG.
  - Alternative: I²C auf DIO8 (SDA, Mux 4) und DIO24 (SCL, Mux 5) legen, den Zähleingang auf DIO11 (T0C0).
    Das ist dann neu zu prüfen.

### R2.3 Kosten nach D-005 (selbst gerechnet)

`concept_costs.py --detail` liefert **A 11.19 / A-32 8.08 CHF** (Serie 20/16/15). Von Hand nachgerechnet:
(5.48 USD × 0.8189 × 1.015 + 0.36) × 16/15 + 5.67 × 1.05 = 5.24 + 5.95 = **11.19** ✔. Die D-005-Regression
über 5/10/15/20 Stk ergibt 30.05 USD + 0.448 USD/Platine ✔.

Dominante Posten bei A (CHF je Sensor, Faktor 0.8866 für Kurs, Karte und 16/15):

| Posten | CHF |
|---|---|
| Zelle CR2450N inkl. 5 % | **4.31** |
| Gehäuse, Dichtungen, Versiegelung, Schraube inkl. 5 % | 1.64 |
| Röntgen (2 leadless × 0.82 USD) | **1.45** |
| CC2340R52 | 1.19 |
| Halter | 0.42 |
| PCB-Grenzkosten | 0.40 |
| 4 × 100 µF | 0.39 |
| MWST-Anteil | 0.38 |
| TMP1075 | 0.28 |
| Rest | ≈ 0.7 |

**R2-W3 (wichtig): „A erfüllt REQ-FAB-04 mit CR2450 ≤ CHF 2.97“ ist rechnerisch richtig
((11.19 − 10)/1.05 = 1.13 CHF), aber nicht belegt.**
- Der einzige Preis ist ein unbestätigtes Suchergebnis für einen **300er-Pack**. Für 15 Sensoren bezahlt man
  den Pack.
- Die Reserve liegt bei 0.00 CHF. Jeder offene OP-K1-Posten kippt die Aussage: Pre-reflow +1.93 CHF, Röntgen
  1.45 CHF unsicher, PCB 167 statt 150 mm. Auch A-32 liegt mit Pre-reflow bei 10.03 CHF > 10.
- *Hebel:*
  - TMP1075 im **VSSOP-8 (DGK)**: ±1 °C von −40 bis 110 °C, also besser als DSG, und nicht leadless
    (`TI_TMP1075_Datasheet_SBOS854F.pdf` S.4 Tab. 4-1). Das spart Röntgen ≈ 0.73 CHF. LCSC-Nummer und Preis habe
    ich **nicht geprüft**.
  - 2 statt 4 Puffer (R2-W1) sparen 0.19 CHF.
  - Zusammen ergibt das A ≈ 10.27 CHF mit der Renata-Zelle. Das Ziel wird dann ab einem Zellpreis ≤ CHF 3.85
    erreicht.

### R2.4 Laufzeit und Puffer

Der Rückgang von 82 auf 27.5 Monate ist **rechnerisch korrekt**. 400 µF an der Samsung-Grenze von 100 MΩ·µF
(Katalog S.53) ergeben 12 µA und 18.9 µA Mittelstrom pess. Er folgt aber aus zwei Verschärfungen zugleich: dem
Puffer von 2 auf 4 × 100 µF und der Leckgrenze statt 0.5 µA. Die Grenze gilt für eine Messung nach 60–120 s bei
**Nennspannung** (S.53). Der Dauerleckstrom bei 3 V liegt real um Grössenordnungen tiefer (**ANNAHME (RT)**). Als
Nachweisfall ist die Grenze zulässig, aber sehr konservativ.

**R2-W1 (wichtig): Die Pufferdimensionierung ist in sich widersprüchlich.**

`energy_budget.py` Tab. 6 rechnet den Prüffall (100 Ω, Einbruch ≤ 0.2 V) mit GLDO-Strömen (9 mA, DCDC aus) und
mit 1.5 ms CPU **innerhalb** des Funkbursts. Bleibt VDDS über 2.2 V, läuft aber der DCDC (DS S.18). Eigene
Rechnung (`rt3_buffer.py`):

| Dimensionierungsfall | C_eff [µF] | C_nenn [µF] (50 % DC-Bias) |
|---|---|---|
| Dokument (GLDO, CPU im Burst) | 162 | 325 → 4 × 100 |
| DCDC, Strom × 3.0/2.6 | 98 | 196 → 2 × 100 |
| DCDC, CPU vor/nach dem Burst | 79 | 158 → 2 × 100 mit Reserve |
| GLDO, CPU vor/nach dem Burst | 131 | 263 → 3 × 100 |

Laufzeit pess. DS bei 1 min (Klammer: mit 50 % Koexistenzverlust):

| Puffer | A [Monate] | A-32 [Monate] |
|---|---|---|
| 4 × 100 µF | 27.5 (22.5) | 11.9 (9.7) |
| 3 × 100 µF | 33.5 (26.4) | 14.6 (11.4) |
| **2 × 100 µF** | 42.8 (31.9) | **18.9 (13.8)** |
| 1 × 100 µF | 59.3 (40.2) | 26.7 (17.6) |

**Einfache Lösung für Leckstrom und Kosten zugleich:**
- Die Firmware erledigt die CPU-Arbeit vor oder nach dem Funkburst.
- Die Unterspannungsabschaltung liegt so, dass der DCDC unter Last aktiv bleibt: VDDS ≥ 2.2 V, also Abschaltung
  an der Klemme ≈ 2.4 V statt 2.0 V. Das ist eine Änderung von REQ-ENE-06 und braucht einen PL-Entscheid. Der
  Kapazitätsverlust ist bei Lithium-Knopfzellen wegen der flachen Kurve klein (**ANNAHME (RT)**).
- Dann genügen **2 × 100 µF**, nachzuweisen per SPICE (OP-K6). Das spart 0.19 CHF und halbiert die Leckgrenze.

Weitere Hebel und ihr Nutzen:

| Hebel | Nutzen |
|---|---|
| Kleinere TX-Leistung | **kaum**: RX 5.3 mA ≥ TX 5.1 mA (DS S.20), RX bestimmt die Spitze |
| Anderer Kondensatortyp | Tantal und Polymer haben schlechtere Leckgrenzen. Nur ein MLCC ohne „*“-Markierung (500 statt 100 MΩ·µF, S.53) oder mit höherer Nennspannung (weniger DC-Bias-Verlust) bringt etwas; Datenblatt je Teil nötig |
| Zuschaltbarer Puffer | bringt bei Grenz-Leck wenig: τ = 100 s gegenüber 27.5 s Intervall, Nachladeverlust ≈ 10.5 statt 12 µA. Dazu kommen FET, Pin und Einschaltstrom → **nicht empfohlen** |

**R2-W4 (wichtig): Die Empfehlung A vor A-32 ist so nicht tragfähig.**
- Ihr Hauptargument, die Laufzeit, hängt allein an der 4-×-100-µF-Dimensionierung. Mit 2 × 100 µF erfüllt A-32
  REQ-ENE-02 bei 1 min und Datenblatt-Leckgrenze, auch mit Koexistenzverlust (13.8 Monate).
- A-32 erfüllt REQ-FAB-04 mit Reserve (≈ 7.9 CHF) und REQ-MECH-02. A erfüllt REQ-FAB-04 nur unter einer
  unbelegten Bedingung.
- Übrig bleibt der „leichte“ Sicherheitsvorteil von A (Clip-Halter, S2-L06).
- *Vorschlag:* Nach Prioritäten entscheidet der Sicherheits-Agent über die Clip-Kurzschlussgefahr. Ohne Einwand
  wird **A-32 Hauptvariante**, sonst A mit TMP1075-DGK und belegtem Zellpreis. Der Prototyp sollte
  2 × 100 µF + 2 Reserve-Footprints haben, damit OP-K5/K6 den Entscheid am Muster liefern.

### R2.5 Antworten auf die Runde-1-Befunde

| Befund | Urteil |
|---|---|
| K-1 Messkette | **akzeptiert** (Rest r2-k1, Strom/tpd klein) |
| K-2 Kostenzuordnung | **akzeptiert** (D-005 korrekt umgesetzt) |
| W-1 A-32 | **akzeptiert**; meine 34 Monate galten nur mit der Leck-ANNAHME, zu Recht korrigiert. Die Schlussfolgerung ist **strittig** → R2-W4 |
| W-2 Energie-Nachweise | **akzeptiert** (TMP geschaltet, Schlaf 2.63 µA pess. A); REQ-ENE-06-Dimensionierung **strittig** → R2-W1 |
| W-3 GPIO-Budget | **akzeptiert** (Pinplan stimmt); neu R2-W2 (SWD) |
| W-4 Kopf | **akzeptiert** (Keystone 3008/3009-Lager plausibel begründet) |
| W-5 Kostenposten | **akzeptiert**; PCB-Länge 167 mm bleibt offen (OP-K1b) |
| W-6 Koexistenz | **akzeptiert** |
| k-1…k-7 | **akzeptiert** |
| Funkmodul (Kap. 4) | **akzeptiert** als zurückgestellt |

Nicht geprüft: LCSC-Nummer und Preis TMP1075DGK, JLC-Röntgenpflicht (OP-K1), Panasonic-Zellpreise, SPICE.
