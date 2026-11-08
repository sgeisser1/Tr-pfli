# Phase 5 – Sicherheitsprüfung Programmieradapter Rev 1 und Behelf (D-024)

| | |
|---|---|
| Prüfer | Sicherheits-Agent (mit Veto), frischer Kontext |
| Datum | 2026-11-08 |
| Stand | git `b77b29a` (main) |
| Geprüft | `hardware/programmer/README.md`, `fluidi_programmer.kicad_sch`, `simulation/spice/programmer/prog_uart_report.txt`, `docs/manuals/PROGRAMMIEREN_SENSOR.md`, D-024; Anforderungen REQ-SAF-CC-01…04, REQ-SAF-06, REQ-FW-06; Auflagen R2-A1…A4 (`phase2_concepts_sicherheit.md`), A-1…A-5 (`phase4_layout_revb_sicherheit.md`), W-10 (`phase4_redteam_gesamt.md`) |
| Ergebnis | **1 kritisch (VETO, nur Weg B), 5 wichtig, 4 klein.** Weg A (Adapter) ist im Prinzip sicher; Freigabe erst nach Nachweis der Einteiligkeit (PS-W1). |

## 1 Selbst geprüft

| Prüfung | Methode / Quelle | Ergebnis |
|---|---|---|
| ERC Adapter | `kicad-cli sch erc --severity-all` (KiCad 10.0.8, WSL), Ausgabe im Scratchpad | **0 Fehler, 0 Warnungen** |
| Netzliste | `kicad-cli sch export netlist`, ausgewertet | 8 Netze + 1 NC (U4.1): +5V {J1.1, U1.3, C1}; +3V3 {U1.2, U2.3, U3.3, C2}; VDD_DUT {U2.2, J2.1, C3}; VIO {U3.2, J1.3, U4.5, R1, C4, C5}; TX_PAD {J3.1, U4.2, R1}; RXD_HOST {U4.4, J1.4}; TXD_HOST {J1.5, J3.2}; GND. **Stimmt mit README Kap. 2.1 überein.** Keine Verbindung zwischen VDD_DUT und VIO ausser über GND. |
| XC6206P202 Ausgang | `Torex_XC6206_Datasheet_ETR0305-004b.pdf` S. 5 Tab. E-1 | 1.960–2.040 V ✓ |
| XC6206 Kurzschluss | ebd. S. 5 Tab. E-6: Ishort **typ** 130 mA (kein Max-Wert); S. 3 Abs. max.: Pd SOT-23 **250 mW** | Dauerkurzschluss an VDD_DUT: 3.3 V × 0.13 A ≈ **0.43 W > 250 mW** (PS-L1). Thermische Abschaltung im Datenblatt nicht genannt (nur Foldback, S. 1) |
| Einzelfehler U2 durchlegiert | VDD_DUT = 3.3 V ≤ VDDS max 3.8 V (`TI_CC2340R5_Datasheet_SWRS272F.pdf` S. 18 Tab. 7.3) | ✓ wie README 2.3 |
| SN74AUP1G17 | `TI_SN74AUP1G17_Datasheet_SCES579J.pdf` S. 4 Kap. 6.1: VCC, VI abs. max. **4.6 V** | +5 V auf VIO (Steckfehler J1) zerstört U4 (PS-L2) |
| CH343 VIO | `WCH_CH343_Datasheet_V1E.pdf` S. 4 Kap. 5.2: „VIO will not flow backwards current …“ | ✓ Behauptung README belegt |
| Ladegrenze CR2032 | `docs/references/Maxell_CR_Warnings_12e_2012.pdf` S. 2: CR2032 **max. 10 mA** im Fehlerfall, Ladung ≤ **1 %** der Nennkapazität; S. 1 „Never charge … explosion, or fire“, „Never use different batteries together“ | Massstab für PS-K1 |
| Q1-Verpolschutz | `phase4_layout_revb_sicherheit.md` Kap. 4 (G = GND, S = VDD, D = VBAT) | Q1 leitet bei VDD > VBAT **in beide Richtungen** (Kanal ein, V_GS ≈ −VDD). Er ist **keine** Rückstromsperre gegen eine Quelle an VDD/Clip. |

## 2 Szenarien

| Szenario | Weg A (Adapter) | Weg B (Behelf) |
|---|---|---|
| Dummy-Zelle 2.0 V | Speist über Clip → Q1 → VDD; 2.0 V < jede brauchbare Zelle | Labornetzteil 2.0–2.2 V, 20 mA |
| Rückspeisung USB → Zelle | Keine Zelle im Kreis, solange Dummy und Federstiftkopf einteilig sind (R2-A2) → **PS-W1** | Clip **frei**, wenn ohne Dummy-Scheibe gespeist wird → **PS-K1** |
| Rückspeisung Zelle → USB | entfällt | Bei eingesetzter Zelle (3 V) und Netzteil 2.0 V: Zelle entlädt sich ins Netzteil/über DIO6 in den CH343-RXD (Board-LED 2 kΩ nach VIO). Kein Brand, aber Parallelschaltung verschiedener Quellen (Maxell S. 1) |
| Kurzschluss | VDD_DUT–GND: U2 im Foldback, 0.43 W (PS-L1). Keine Zelle beteiligt | Netzteil-Strombegrenzung 20 mA |
| Verpolung | Dummy verkehrt: Clip auf Mittelinsel (−), Minuspad auf Oberseite (+) → Sensor-GND +2 V, VBAT 0 V; Q1 sperrt, Body-Diode in Sperrrichtung; Federstifte erreichen TP1/TP2 nicht (Kopf liegt dann auf B) | Netzteil verpolt am Clip: Q1 sperrt (24-h-Fall REQ-SAF-CC-01) |
| Gleichzeitig echte Zelle | konstruktiv ausgeschlossen, **nur wenn** PA-1 so gebaut wird | **möglich** (PS-K1) |
| Bootloader-Fehlstart | nach `program` Reset mit gedrücktem Taster → nur Dummy, kein Schaden | – |
| Bootloader-Fehlstart mit Zelle (W-10) | Zelle in ≈ 2–12 Tagen leer (PROGRAMMIEREN Kap. 6, ANNAHME 0.8–4.1 mA) → PS-W5 | gleich |

## 3 Befunde

### Kritisch

**PS-K1 · kritisch · REQ-SAF-CC-03 · VETO (nur Weg B in der heutigen Fassung)**

`PROGRAMMIEREN_SENSOR.md` Kap. 5 Schritt 2 erlaubt die Speisung **ohne Dummy-Scheibe**: „+ mit einer
Mikro-Prüfklemme am Clip-Quersteg, − mit einem angelöteten Draht am Rand des Minuspads“. Dann ist der Clip frei,
und eine Zelle lässt sich bei angeschlossenem Netzteil einsetzen. Schritt 9 lädt sogar dazu ein („Erst dann Zelle
einsetzen (Funktionsprüfung …)“), Schritt 8 verlangt nur „Netzteil aus, Drähte ab“, ohne Kontrolle.

- REQ-SAF-CC-03 verlangt: „Programmieren nur ohne eingesetzte Zelle …, **konstruktiv sichergestellt**.“ Ohne
  Scheibe ist das nur eine Verhaltensregel (Regel 1).
- Q1 schützt nicht: Das Netzteil liegt direkt am Clip (VBAT), also parallel zur Zelle.
- Eine Zelle **unter 2.0–2.2 V** wird mit bis zu **20 mA** geladen. Das sind das Doppelte der Maxell-Grenze 10 mA,
  und 1 % C (2.25 mAh) sind nach ≈ 7 min erreicht. Solche Zellen entstehen im Projekt selbst: Die Bootloader-Falle
  (W-10) entlädt Musterzellen ohne UV-Abschaltung bis zur BOD-Schwelle und darunter. Zellen aus dem Prüfaufbau
  „EOL-Quelle 2.0–2.4 V“ (F-W3) sind ebenfalls tief.
- Eine volle Zelle (3 V) wird nicht geladen, aber parallel zu einer fremden Quelle betrieben (Maxell S. 1, „Never
  use different batteries together“). Ein Fehler beim Einstellen (Drehknopf auf 3.3 V oder mehr) führt auch bei
  einer vollen Zelle zum Laden.
- Folge: Laden einer Lithium-Primärzelle → Gas, Leck, Überhitzung, im Extremfall Brand (Maxell S. 1). Schwere
  hoch, Auftreten im Musteralltag plausibel (Einzelfehler: Netzteil nicht getrennt). Deshalb kritisch.

**VETO:** Weg B darf in der heutigen Fassung nicht angewendet werden.

**Bedingungen zur Aufhebung (alle Änderungen in `PROGRAMMIEREN_SENSOR.md`, Prüfung durch Sicherheit):**
1. Weg B speist **ausschliesslich über die Dummy-Scheibe** im Clip (zwei Litzen ans Netzteil). Die Variante
   „Prüfklemme am Quersteg + Draht am Minuspad“ wird gestrichen. In Kap. 2 wird die Scheibe für Weg B von
   „empfohlen“ auf **Pflicht** geändert.
2. Schritt 8/9 in dieser Reihenfolge: Netzteil **aus**, Litzen vom Netzteil **abziehen**, Scheibe **entnehmen**,
   Draht an R9 entfernen und prüfen (PS-W4), **erst dann** Zelle einsetzen. Eine Zelle wird nie eingesetzt, solange
   eine Litze am Netzteil hängt.
3. Neuer Satz bei Regel 2: „Nur neue Zellen ≥ 3.0 V Leerlauf einsetzen. Zellen unter 2.6 V (z. B. nach
   Bootloader-Falle) nicht wieder verwenden, abkleben und entsorgen.“

Weg A und alle anderen Teile von D-024 sind vom Veto **nicht** betroffen.

### Wichtig

**PS-W1 · wichtig · REQ-SAF-CC-03, R2-A2 – Einteiligkeit ist nicht nachgewiesen.**
Die ganze Rückspeise-Argumentation des Adapters (README 2.3 „Kein Rückspeisen in eine Zelle“) hängt an der starren
Verbindung von Dummy-Zelle und Federstiftkopf. Bügel, Gegenhalter und Stifttyp sind offen (PA-1, ANNAHME).
Vorschlag: Freigabe des Adapters erst nach Konstruktion (mit `mechanik`) und diesen Nachweisen am Muster
(PROTOTYP-PRÜFUNG, Testplan ST-P1): (a) Die Stifte berühren TP1/TP2 nur, wenn der Dummy ganz im Clip sitzt; (b) mit
gestecktem Adapter passt keine CR2032 in den Clip; (c) Dummy verkehrt eingesetzt: Stifte erreichen TP1/TP2 nicht;
(d) der Gegenhalter belastet das Schott nicht.

**PS-W2 · wichtig · REQ-MECH-05, A-3 – Federstifte und Lötstellen auf den Via-in-Pad-Flächen im Fach.**
- TP1, TP2, Minuspad und VBAT-Pad sind POFV-gefüllt und überkupfert (D-023). README Kap. 4 nennt „Krone oder
  Spitze“. Eine spitze Krone mit Federkraft kann die dünne Kupferkappe verletzen. Dann liegt die Epoxidfüllung offen,
  in einem Fach, das geflutet wird (REQ-SAF-05).
- Weg B lötet einen Draht an TP2 und (ohne Scheibe) am Minuspad. Das belastet die VIP-Kappe thermisch. Ein Lotrest
  auf dem Minuspad hebt die Zelle an; Schrägsitz ist der Kurzschlussfall aus R2-W01.
- Vorschlag: Federstifte mit **flachem oder gerundetem Kopf**, Federkraft so klein wie möglich (Wert mit `mechanik`
  festlegen, ANNAHME ≤ 1 N). Keine Lötung auf Minuspad, VBAT-Pad, TP1 und TP2. TP2 in Weg B mit Prüfspitze oder
  Federstift. Nach jeder Programmierung Sichtprüfung der 4 VIP-Pads (Lupe ≥ 10×, wie A-3).

**PS-W3 · wichtig · REQ-SAF-CC-02, K-4 – Dummy-Zelle zu dick.**
Zwei Scheiben FR4 1.6 mm, dazu zwei Kupferlagen und Kleber, ergeben mehr als 3.2 mm. Die CR2032 ist höchstens 3.2 mm
hoch (`Panasonic_CR2032_Datasheet_2026-02.pdf` S. 1). FR4 hat eine Dickentoleranz (ANNAHME ±10 %). Ein zu dicker Dummy
spreizt den Clip auf. Dessen Lötstellen liegen genau auf dem Katalogminimum (Red-Team K-4) und sind die schwächste
Stelle. Ein angerissener Clip sitzt lose, was zu Kurzschluss bzw. Wackelkontakt führen kann (R2-W01 Nr. 4).
Vorschlag: Gesamtdicke **3.0–3.2 mm** messen und festschreiben (z. B. 1.6 + 1.5 mm oder Scheibe abschleifen). Kante
wie bei einer Zelle leicht fasen. Prüfmass in README Kap. 7 Schritt 3 aufnehmen.

**PS-W4 · wichtig · REQ-SAF-CC-03 – Behelfsdraht an R9 Pad 1 umgeht beide Barrieren auf dem TX-Pfad.**
R9 Pad 1 liegt vor R9 **und** R10 (PROGRAMMIEREN Kap. 5), also ohne Barriere. Ein vergessener Draht bleibt nach dem
Verguss als Antenne bzw. Kontaktpunkt im Elektronikraum. Die Kontrollmessung in Schritt 9 („TP1 ↔ R9 Pad 1 ≈ 200 kΩ“)
prüft R9/R10, erkennt aber einen **verbliebenen Draht nicht**. Ein Ladepfad entsteht erst mit weiteren Fehlern (Draht
herausgeführt, CH343 mit VIO > VBAT, z. B. Jumper H3 gesteckt): ≤ 21 µA + LED-Pfad, also deutlich unter 10 mA.
Vorschlag: Schritt 9 um „Draht vollständig entfernt (Foto unter Lupe, je Muster in der Musterliste vermerkt)“
ergänzen. Den Draht nicht durch das Schott bzw. den späteren Vergussraum führen.

**PS-W5 · wichtig · Energie, W-10 – Bootloader-Fehlstart leert die Musterzelle.**
Die Analyse in PROGRAMMIEREN Kap. 6 ist richtig. Die Firmware-Schutzfunktionen (UV-Abschaltung FW-5, Reset-Zähler
F-W3) wirken im ROM-Bootloader **nicht**. Folgen: Zelle tiefentladen, Muster wirkt tot, Langzeittests (30 Tage nass)
werden ungültig, und die tiefentladene Zelle wird zur Gefahr in Weg B (PS-K1). Ein Brand entsteht nicht, weil eine
einzelne Zelle nicht umgepolt werden kann.
Vorschlag:
- Prüfpunkt „L11 nach jedem Zusammenbau“ in die Musterliste aufnehmen. Bootloader-Strom messen (PROTOTYP-PRÜFUNG,
  Testplan ST-P6).
- Tiefentladene Zellen nicht weiterverwenden (PS-K1 Bed. 3).
- Firmware prüft, ob der Bootloader-Trigger für die Muster auf einen Pin gelegt werden kann, den nur der Adapter
  setzt. Beispiel: TP2/DIO20 low beim Start, wobei der Adapter beim Einsetzen ein Break sendet. Das ist eine
  **ANNAHME**; Ruhepegel von DIO20 mit LED und TRM S. 465 prüfen. Sonst bleibt die Anleitungsregel.

### Klein

**PS-L1 · klein – Kurzschluss an VDD_DUT überlastet U2.** Foldback 130 mA typ (Max nicht spezifiziert), 0.43 W gegen
Pd 250 mW (Torex S. 3/S. 5). Ohne Zelle besteht keine Brandgefahr für die Zelle. Ein SOT-23 auf Lochraster kann aber
heiss werden. Zulässige Wege: Mittelinsel und Litzen isoliert führen. **PROTOTYP-PRÜFUNG** ST-P3: Kurzschluss 60 s,
Gehäusetemperatur U1/U2 messen. Wird es zu heiss, eine PTC-Sicherung oder einen Widerstand vor U2 vorsehen.

**PS-L2 · klein – Steckbrücken J1 verwechselbar.** +5 V auf VIO (J1.3) übersteigt die 4.6 V von U4 (SCES579J S. 4)
und drückt 5 V auf den U3-Ausgang. Vorschlag: 5-polige Buchsenleiste mit Kodierung oder Farbcode. README Kap. 7
Schritt 2 (VIO messen) deckt den Fehler vor dem Anschluss des Sensors auf.

**PS-L3 · klein – Labornetzteil Weg B.** Manche Netzteile schwingen beim Einschalten über. Vorschlag: Spannung ohne
Last einstellen und messen, dann mit Ausgang „aus“ anschliessen und erst danach einschalten (Schritt 5/6 so
formulieren). Strombegrenzung wenn möglich **10 mA** (Bootloader-Bedarf ≤ 7 mA, README 2.4, ANNAHME); 20 mA bleibt
zulässig, sobald PS-K1 umgesetzt ist.

**PS-L4 · klein – Serie `--lock`.** Unumkehrbar. `check_lock_key` lehnt den DEV-Schlüssel ab und verlangt
`--expect-key-fp` (Runde 2 F-W1, `phase4_sicherheit_kragen_firmware.md`). Kein neuer Befund, nur Hinweis: Den Fingerabdruck
des Produktionsschlüssels getrennt vom Schlüssel festhalten (Testplan ST-S3).

## 4 Bestätigt ohne Befund

- Zwei getrennte 2.0-V-Regler: VIO bleibt beim Laden des Sensorpuffers stabil. Anstieg ≤ 0.32 mV/µs (README 2.2).
- Einzelfehler U1, U2 und U3 einzeln: kein Schaden am Sensor, keine Zelle im Kreis (README 2.3, nachgerechnet).
- Doppelfehler U1 und U2: 5 V am Sensor führen zu einem Geräteschaden, aber ohne Zelle zu keinem Brand (R2-L02 akzeptiert).
- TP2 bleibt hinter 2 × 100 kΩ (Barriere 2 auf RX intakt). Der Adapter verbindet TP1 nur mit einem CMOS-Eingang und
  10 MΩ nach VIO. Das ergibt ≤ 0.2 µA und keinen Ladepfad.
- Pegel/Timing: SPICE-Bericht nachvollzogen. A1z (Ruhepegel im Hysteresebereich) ist ein Funktions- und kein
  Sicherheitsthema.

## 5 Ergebnis

**VETO PS-K1** gegen Weg B in der heutigen Fassung. Aufhebung durch die drei Textänderungen oben. Weg A ist unter
PS-W1 freigebbar. Sicherheitstests ST-P1…ST-P6 gehen in den Testplan
(`phase5_testplan_beitrag_sicherheit.md`).
