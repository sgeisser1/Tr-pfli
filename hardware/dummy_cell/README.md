# fluidi Dummy-Scheibe Rev 1 – CR2032-Ersatz für Weg B (Programmieren vor dem Verguss)

| | |
|---|---|
| Stand | 2026-11-09, Rev 1, **Entwurf Elektronik**. Freigabe Orchestrator/Auftraggeber offen; Prüfung durch `sicherheit` (PS-K1, PS-W2/W3/W4) und `mechanik` (Freiraum der Lasche, Kap. 6) offen |
| Anlass | Red-Team Phase 6 W-1 (`docs/reviews/phase6_redteam_paket.md`): Weg B verlangte eine **selbstgebaute** Scheibe (FR-4 schleifen), nichts davon war bestellbar |
| Grundlage | `docs/manuals/PROGRAMMIEREN_SENSOR.md` v1.2 Regel 1, Kap. 2, Kap. 5; Veto PS-K1 und Auflagen PS-W2…W4 (`docs/reviews/phase5_programmer_sicherheit.md`); `hardware/programmer/README.md` Kap. 4 (Dummy-Zelle) |
| Platinen | `fluidi_dummy_plus.kicad_pcb` (oben, +, **1.0 mm**), `fluidi_dummy_minus.kicad_pcb` (unten, −, **2.0 mm**) |
| Generator | `gen/gen_dummy.py`, alles neu mit `bash hardware/dummy_cell/gen/run_all.sh` (DRC, Gerber, PDF/SVG, Kosten) |
| DRC | KiCad 10.0.8 WSL **und** Windows, je Platine: **0 Verstösse, 0 nicht verbundene Pads, 0 Footprint-Fehler** (`out/drc_*_wsl.rpt`, `out/drc_*_win.rpt`); Regeldateien `fluidi_dummy_*.kicad_dru` (JLC 2 Lagen + Projektregeln) |
| Fertigungsdaten | `out/fluidi_dummy_plus_gerber_jlc.zip`, `out/fluidi_dummy_minus_gerber_jlc.zip` (Gerber ohne X2, Excellon PTH/NPTH getrennt), Hashes `out/SHA256SUMS`; Ansichten `out/*_layout.pdf`, `out/*_oben.svg`, `out/*_unten.svg` |
| Kosten | **≈ 4.3–14.4 CHF** Mehrkosten in der JLC-Prototypbestellung (Kap. 5, `gen/cost_dummy.py`, `out/kosten.txt`) |
| Sensor | **unverändert** (Rev C bytegleich). Gegenstück: BT1 Keystone 3034TR (C5213768), Footprint `hardware/sensor/lib/fluidi.pretty/BatteryHolder_Keystone_3034_1x20mm_NegPad4mm_W23p1.kicad_mod` |

## 1 Entscheid in Kürze

**Entwurf: ja.** Die Scheibe passt als zwei kleine, unbestückte 2-Lagen-Platinen in dieselbe JLC-Bestellung. Damit
entfällt der Eigenbau (FR-4 schleifen, Kupfer wegschaben), der laut Red-Team W-1 kein Laienweg ist.

| Variante | Dicke | Bewertung |
|---|---|---|
| 2 × 1.6 mm gestapelt | 3.2 + Kleber, Toleranz ± 10 % je Platine → bis 3.6 mm | **verworfen**: Nennwert schon über 3.2 mm, verletzt PS-W3 (Clip spreizen) |
| eine Platine 3.2 mm | – | **nicht verfügbar**: JLC FR-4 0.4/0.6/0.8/1.0/1.2/1.6/2.0 mm (`docs/references/JLCPCB_NOTES.md` Kap. 3, abgerufen 2026-11-06) |
| Platine + gedruckte/aufgeklebte Distanz | 1.6 + 1.4 | **verworfen**: Plus oben **und** Minus unten brauchen beide Kupfer; mit einer Platine liegt eine Kontaktfläche auf der Distanz, der Kontakt Kupfer–Kupfer über Druck wäre unsicher |
| **1.0 mm (PLUS) + 2.0 mm (MINUS), isolierend verklebt** | **3.0 + Kleber ≈ 3.05–3.15 mm nominal** | **gewählt**: beide Dicken JLC-Standard; jede Platine trägt genau einen Pol auf ihrer Aussenfläche; die Klebefuge isoliert die Pole voneinander |

## 2 Aufbau und Nachbildung der Zelle

| Fläche | Zelle CR2032 | Dummy-Scheibe | Quelle / Grund |
|---|---|---|---|
| Durchmesser | 20.0 mm max. | **19.8 mm** (JLC-Kontur ± 0.2 → 19.6–20.0) | `Panasonic_CR2032_Datasheet_2026-02.pdf` S. 1 „Diameter (Max.) 20.0mm“; `JLCPCB_NOTES.md` Kap. 3 Konturtoleranz |
| Höhe | 3.2 mm max. | **3.0–3.2 mm** gemessen | Panasonic S. 1 „Height (Max.) 3.2mm“; Auflage PS-W3 |
| Oberseite = **+** | Becher + (der Clip drückt oben) | PLUS: Kupferscheibe **Ø 19.0 mm offen** (HASL), 0.4 mm zur Kontur | Keystone 3034: Haltefeder über der Zelle, H 4.1 mm (`Keystone_3034_Catalog_M65.pdf` S. 1, Fig. 1, Zeile 3034) |
| Unterseite = **−** | Deckel − mittig | MINUS: **Mittelinsel Ø 8.0 mm** offen, Rest Lötstopplack | Minuspad 4 × 4 mm in der Zellmitte (Footprint BT1; Katalog „NEG. CONTACT (PAD) .156 [3.96] SQ. MIN.“, S. 1); Ø 8 deckt die Paddiagonale 5.66 mm plus ± 1.17 mm Lage |
| Rand | Becher + | FR-4, kein Kupfer am Rand und keine Plusfläche unten | R2-W01 (kein Plusrand unten), README Programmer Kap. 4 |
| Verbindung − nach oben | – | 4 Vias auf r 3.4 mm (ausserhalb der Padfläche 4 × 4, Ecke r 2.83) → Leitung 1.0 mm auf der MINUS-Oberseite, **unter** PLUS (Lack + Klebefuge + 1.0 mm FR-4) → Lötpad „−“ | Projektregel: Scheibenunterseite nur Insel und Vias (`.kicad_dru`, Regelfläche `SCHEIBE_UNTEN`) |
| Lasche | – | Lasche in **+x** (offenes Clip-Ende): Breite 8 mm im Clip-Bereich, ausserhalb der Sensorplatine (ab x 11 ab Scheibenmitte) MINUS 18 mm breit | Clip-Enden vorn bei |y| ≈ 6.1 mm (Footprint BT1, F.Fab); Platinenkante = Zellrand x +13.0 (`docs/interfaces/PCB_OUTLINE.md` Zeile XBT1/Z4) |

Lötpads (Litze von oben anlöten):

| Pad | Platine | Netz | Anschluss |
|---|---|---|---|
| J3 „+“ 4.5 × 5 mm SMD | PLUS (Lasche, x 12.6–17.1) | + (Kupferscheibe oben) | Netzteil + (rote Litze). Kein Loch: PLUS hat unten **kein** Kupfer |
| J4 „−“ 3.5 × 5 mm, Bohrung 1.2 | MINUS (x 19.25–22.75, frei hinter PLUS) | − (Mittelinsel) | Netzteil − (schwarze Litze) |
| J5 „GND“ Ø 2.2, Bohrung 1.0 | MINUS | − | GND des USB-UART-Boards |
| J6 „TP1“, J7 „VIO“, J8 „RXD“ | MINUS | Variante B2 | Kap. 3 |

**Verpolt eingesetzt** (Insel oben): Die Plusfläche liegt dann auf dem Minuspad, die Insel trifft die Haltefeder höchstens
zufällig. Der Verpolschutz Q1 (AO3401A) des Sensors sperrt (hardware/programmer/README.md Kap. 2.3, CONCEPTS 2.7). Die
Lasche zeigt dann zur falschen Seite bzw. die Beschriftung „+“ ist unten; das ist sichtbar.

## 3 Variante B2 (optional): Weg B ohne Draht an R9

Ein Pad am Sensor ist **ohne Änderung der Sensorplatine nicht möglich** (Rev C bleibt bytegleich). Der Knoten DIO6
(`LED_R_UART_TX`) ist nur an U1 Pin 19, R9 Pad 1 und R6 Pad 1 erreichbar (PROGRAMMIEREN Kap. 5); TP1 liegt hinter
2 × 100 kΩ. Der Grund für den Draht an R9 ist, dass das Low über 200 kΩ den USB-UART-Eingang nicht erreicht
(SPICE A0, `hardware/programmer/README.md` Kap. 3). Genau dieses Problem löst der Programmieradapter Rev 1 mit dem
Schmitt-Puffer U4 direkt am Federstift TP1.

Die MINUS-Platine trägt deshalb **unbestückte** Footprints für diese Schaltung (gleiche Teile wie Adapter U4/R1/C5,
bereits in der Einkaufsliste P3/P5/P6):

| Ref | Teil | Netz | Quelle |
|---|---|---|---|
| U1 | TI SN74AUP1G17DBVR, SOT-23-5 (1 NC, 2 A, 3 GND, 4 Y, 5 VCC) | A = TX_PROBE, Y = RXD_HOST, VCC = VIO | `TI_SN74AUP1G17_Datasheet_SCES579J.pdf` S. 3 Kap. 5 (DBV), geprüft |
| R1 | 10 MΩ 1 % 0402 (UNI-ROYAL 0402WGF1005TCE) | TX_PROBE → VIO | Adapter README Kap. 3 (Wahl R1, SPICE A1/A1z) |
| C1 | 100 nF 0805 (Samsung CL21B104KBCNNNC) | VIO – GND | Adapter README Kap. 2.1 |

Anschluss B2: J6 „TP1“ → Prüfspitze (flacher/gerundeter Kopf, PS-W2) auf **TP1**; J8 „RXD“ → RXD des USB-UART;
J7 „VIO“ → Netzteil + (gleiche 2.0 V wie J3 und wie VIO/VCCIO des USB-UART, Regel 3); J5 → GND des USB-UART. TP2
wie bisher mit Prüfspitze. Pegel und Zeitverhalten entsprechen SPICE A1 des Adapters (VDD = VIO 1.96–2.04 V);
**Baudrate 19200** (`--baud 19200`): Mit Puffer am Kabelende (40 pF) bleibt die Reserve bei 19200 noch 0.213 Bit, bei
57600 nicht (`simulation/spice/programmer/prog_uart_report.txt`, Fall „Puffer am Kabelende“). Prüfspitzenleitung
TP1–J6 so kurz wie möglich (**ANNAHME** ≤ 10 cm).

Vorteile: keine Lötstelle am bestückten Sensor, kein vergessener Draht (PS-W4 entfällt), beide 100-kΩ-Barrieren
bleiben im TX-Pfad. Nachteil: zwei Prüfspitzen (TP1, TP2, Abstand 3.0 mm) müssen ≈ 2–3 min ruhig sitzen (dritte Hand
oder zwei Federstifte P8 in einem Halter, **ANNAHME**). **B2 ist ein Vorschlag**: Aufnahme in PROGRAMMIEREN Kap. 5 erst
nach Prüfung durch `sicherheit` und einem Versuch am ersten Muster (**PROTOTYP-PRÜFUNG**).

## 4 Herstellung und Prüfung (je Scheibe)

JLC-Bestelloptionen (beide Designs, `docs/references/JLCPCB_NOTES.md` Kap. 3/5):

| Option | PLUS | MINUS |
|---|---|---|
| Datei | `out/fluidi_dummy_plus_gerber_jlc.zip` | `out/fluidi_dummy_minus_gerber_jlc.zip` |
| Lagen / Material | 2 / FR-4 Standard | 2 / FR-4 Standard |
| **Dicke** | **1.0 mm** | **2.0 mm** |
| Grösse (Kontur) | 27.9 × 19.8 mm | 44.4 × 19.8 mm |
| Menge | 5 (Mindestmenge) | 5 |
| Kupfer / Oberfläche | 1 oz / HASL bleifrei | 1 oz / HASL bleifrei |
| Farbe | grün (Standard; andere Farbe = Aufpreis **ANNAHME**, `cost_model.SURCHARGE_COLOR_USD`) | grün |
| Via Covering | – (keine Vias) | **Tented** (Standard); die Inselvias sind unten offen (Lötstopp offen über der Insel) |
| Bestückung | **keine** (kein „PCB Assembly“) | **keine** |
| Markierung | „No mark“ (JLC setzt standardmässig keine, `JLCPCB_HowToMarkOnPCB_Auszug_2026-11-08.txt`) | gleich |

Zusammenbau (einmal, ≈ 30 min + Aushärtezeit):
1. Je 5 PLUS und 5 MINUS mit dem Messschieber an 3 Stellen der Scheibe messen; Paare so wählen, dass PLUS + MINUS
   **2.95–3.10 mm** ergibt (Kleber ≈ 0.05–0.10 mm, **ANNAHME**). JLC-Toleranz ± 10 % (`JLCPCB_NOTES.md` Kap. 3) →
   schlechtester Fall 2.7–3.3 mm; zu dünn: 1 Lage Kaptonband (≈ 0.06 mm) **in** die Klebefuge, nie auf Kontaktflächen;
   zu dick: anderes Paar.
2. Entgraten: Scheibenrand mit Schleifpapier 400 leicht fasen (wie eine Zelle), Staub mit Isopropanol entfernen.
3. Kleben: **isolierender** Zweikomponenten-Epoxidkleber dünn auf die MINUS-Oberseite im Scheibenbereich, nicht auf
   J4/J5–J8. Zwei Stifte Ø 1.0 mm (z. B. Bohrerschaft) durch die Passlöcher H1/H2 beider Platinen, Ränder bündig,
   zwischen zwei glatten Flächen leicht pressen; Stifte vor dem Aushärten ziehen; Kleberreste am Rand entfernen.
4. Prüfen: Gesamtdicke an 3 Stellen **3.0–3.2 mm**, Wert mit Stift ins Feld „d = ___ mm“ (MINUS unten) schreiben
   (PS-W3). Isolation + ↔ − **> 10 MΩ** (Multimeter, Programmer README Kap. 4). Durchgang J3 ↔ Kupferscheibe und
   J4 ↔ Mittelinsel (< 1 Ω).
5. Litzen: rot an J3 (+), schwarz an J4 (−), 0.14–0.25 mm², 20–30 cm, Lötstellen flach; Litzen mit einem Tropfen
   Kleber oder Kaptonband auf der Lasche zugentlasten; freie Enden mit Krokodilklemme/4-mm-Stecker an das Netzteil.
   Optional B2: U1, R1, C1 von Hand bestücken (Kap. 3).
6. Probesitz am Sensor (ohne Speisung): Scheibe sitzt ohne Kraftaufwand, Clip nicht sichtbar gespreizt; Durchgang
   J3 ↔ Clip (VBAT) und J4 ↔ Minuspad (GND) < 1 Ω (**PROTOTYP-PRÜFUNG**: Kontakt der Insel am Minuspad mit der
   Haltekraft des Clips).

## 5 Kosten (Kostenmodell `scripts/cost_model.py`, Skript `gen/cost_dummy.py`)

| Fall | PLUS | MINUS | JLC zusammen | + Kurs/Karte, MWST 8.1 %, DHL 2 % | **Mehrkosten** |
|---|---|---|---|---|---|
| Obergrenze: Rechnerpreis 2 L, 5 Stk (22 × 150 mm, 6.90 USD) + Entgraten 0.02 USD/Stk; 2.0 mm × 1.30 (**ANNAHME**) | 7.00 USD | 9.07 USD | 16.07 USD | 13.36 + 1.07 + 0.02 CHF | **14.44 CHF** |
| Untergrenze: Promo „$2“ je Design (≤ 100 × 100 mm, **ANNAHME** gilt neben der 4-Lagen-Bestellung) | 2.10 USD | 2.70 USD | 4.80 USD | 3.99 + 0.32 + 0.01 CHF | **4.31 CHF** |

- Einmalkosten, nicht Stückkosten (Werkzeug, D-005); die Seriensumme des Sensors ändert sich nicht.
- Versand und DHL-Verzollungspauschale (19 CHF) fallen **nur einmal** an, weil die Platinen in derselben Bestellung wie
  die Sensor-Platine liegen. Getrennt bestellt kämen 7.63 USD Versand (GSDL) und Post-Gebühren dazu.
- Die Teile für B2 (U1/R1/C1) sind schon in der Einkaufsliste (P3/P5/P6, Programmieradapter): 0 CHF zusätzlich.
- Werkstatt (Kap. 7): Kleber, Litze, Kaptonband **ANNAHME** Werkstattbestand; Einkauf entscheidet.

## 6 Sicherheit (Abstimmung `sicherheit`) und Schnittstelle zur Mechanik

| Punkt | Umsetzung |
|---|---|
| PS-K1: Netzteil nur über die Scheibe, nie mit Zelle | Die Scheibe belegt den einzigen Clip (Höhe 3.0–3.2 mm = Zellhöhe); die Litzen sind **fest** an die Scheibe gelötet → Speisung ohne Scheibe ist mit diesem Werkzeug nicht vorgesehen. Regeln 1–4 und Schritt 8 (Netzteil aus und ab → Scheibe heraus → Draht/Spitzen weg → erst dann Zelle) bleiben **unverändert** |
| Verwechslung mit einer Zelle | **Lasche** (eine Zelle hat keine), angelötete Litzen, Aufdruck „DUMMY“ (oben und unten), „KEINE ZELLE“, „max 2.1 V / 10 mA“, „+2.0V“ am Pluspad; Dicke von Hand eingetragen. Die Scheibe ist kein Energiespeicher; eingesetzt in ein fremdes Gerät liefert sie nichts |
| PS-W3 Dicke | 1.0 + 2.0 mm + Kleber, Paarung nach Messung, Prüfmass 3.0–3.2 mm (Kap. 4) |
| PS-W2 Via-in-Pad im Fach | Keine Lötstelle auf Minuspad/VBAT-Pad/TP1/TP2. Die Insel ist eben (HASL), Vias ausserhalb der Padfläche; keine Lötstelle an der Unterseite der Scheibe |
| R2-W01 kein Plusrand unten | PLUS hat unten kein Kupfer (DRC-Regel), MINUS unten nur die Insel (DRC-Regel) |
| Kurzschluss + ↔ − an der Scheibe | Pole auf verschiedenen Platinen, getrennt durch 1.0 mm FR-4 + Lack + Klebefuge; Pads auf der Lasche ≥ 2 mm auseinander und auf verschiedenen Ebenen; Isolationsprüfung > 10 MΩ; Netzteil 10 mA begrenzt |
| PS-W4 Draht an R9 | bleibt für Weg B unverändert gültig; mit Variante B2 entfällt der Draht (Kap. 3) |
| **Mechanik (offen)** | Die Lasche ragt in +x über die Platinenkante (x +13.0) hinaus: MINUS bis x 37.5 (= Zellmitte + 34.5), Höhe 0…3.2 mm über der F-Seite, Breite 8 mm bis x 14, danach 18 mm. Zu prüfen mit `mechanik`: Ist dieser Raum beim Weg-B-Schritt (Platine offen, ohne Hülse und Verguss, ggf. in Kappe/Gabel bzw. mit Schottkeil) frei? Zellmitte X 3.0 / Y 34.8 (PCB_OUTLINE XBT1) |

## 6a Freiraum (Mechanik) – DC-1

Geprüft 2026-11-09 (Mechanik) im CAD Rev C (`mechanical/sensor/fluidi_sensor.FCStd`, `fluidi_sensor_mit_pcb.step`) mit
den aus den KiCad-Dateien exportierten Scheiben (`kicad-cli pcb export step --subst-models`, KiCad 10.0.8 WSL; Skript im
Scratchpad, nicht im Repo). Lage: Scheibenmitte = Zellmitte X 3.0 / Y 34.8 (CAD x 3.0, z 18.7), MINUS-Unterseite auf der
F-Seite (CAD y 6.6), PLUS darüber nach 0.05 mm Klebefuge; Lasche in +x bis **X 37.5**.

| Gegenstück (Montagezustand) | Abstand Scheibe inkl. Bauteile | Abstand Hüllraum Lasche (x 12.9 … 37.5, 0 … 3.2 über F, 18 breit) |
|---|---|---|
| Kappe blau (mit Gabel/Anschlag, Schott), Schottkeil, Verguss Schott | 2.20 mm | 3.10 mm |
| Kragen, Verguss Kragen | 2.20 mm | 3.10 / 4.14 mm |
| Distanzlehre (Kragenverguss) | 1.64 mm | 11.5 mm |
| Bauteile der Sensorplatine (KiCad-STEP, ausser Clip/Zelle) | keine Überdeckung | keine Überdeckung |
| Clip Keystone 3034 (CAD-Hüllquader) | Überdeckung 27.8 mm³ (s. unten) | **1.20 mm** |
| **Hülse grau** | **Überdeckung 71 mm³** | **Überdeckung 104 mm³** |

- **Ergebnis: passt.** Die Lasche stösst in keinem Zustand vor dem Aufschieben der Hülse an: weder lose Platine noch
  Platine in der Kappe (Gabel, Schottkeil, Schottverguss) noch mit Kragen. Sie ragt in +x durch die Hülsenkontur
  (Kopf ± 17 mm) – Weg B ist darum nur **ohne Hülse** möglich; das gilt ohnehin (Zellfach offen).
- Die Überdeckung mit dem Clip ist ein Artefakt des CAD-Modells (Hüllquader L × W × H des Datenblatts minus Zylinder der
  Zelle, Zelle 0.1 mm über der Platine): die Scheibe liegt auf der Platine und die Lasche läuft durch das offene
  Clip-Ende. Massgebend ist der Footprint: Öffnung am offenen Ende ± 6.1 mm (F.Fab, Bogenenden) gegen Lasche ± 4.0 mm →
  **2.1 mm je Seite**. **PROTOTYP-PRÜFUNG** DC-4: Lasche geht ohne Kontakt zu den Clip-Armen ein und aus.
- Höhe: Die B2-Bauteile auf der MINUS-Lasche stehen bis **3.55 mm** über der F-Seite (lokal x 24 … 32, d. h. ausserhalb
  des Gehäuseumrisses x > 21); innerhalb von x ≤ 17 bleibt alles ≤ 3.2 mm. Kein Einfluss.
- **Montagezustand nach MONTAGE_SENSOR:** Weg B ist Kap. 3b Schritt 1, **vor Kap. 4**. Mit Draht an **R9** (Weg B nach
  PROGRAMMIEREN Kap. 5) muss die Platine **lose** sein: R9 liegt bei X −0.2 / Y 11.95 (z 41.6), also im Bereich der Kappe
  (Kappe ab Schott z 30.8) – mit eingesetzter Platine nicht erreichbar. Gabel, Schottkeil und Kappe sind dann noch nicht
  montiert. Mit **Variante B2** (Prüfspitzen auf TP1/TP2, X −10.6 / z 28.0 und 25.0, unterhalb des Schotts) ginge es
  auch mit eingesetzter Platine; der Freiraum der Lasche ist auch dort gegeben (Tabelle).
- **Keine Änderung** der Montagereihenfolge oder der Laschengeometrie nötig.
- Nachtrag Mechanik ausserhalb DC-1: Die Kontur nach Kap. 2 (Ø 19.8) liegt im Zellraum des CAD (Zelle Ø 20, x −7.0 … 13.0).

## 7 Werkstatt-Voraussetzungen für Weg B (vollständig)

Für **jeden** Weg-B-Platz. „ANNAHME“ = Spezifikation aus den Anforderungen abgeleitet, kein bestimmtes Gerät geprüft.
Die Einkaufsliste ändert der Einkauf; diese Liste ist die Vorgabe dafür.

| Nr | Werkzeug / Material | Mindestanforderung | Wofür (Quelle) |
|---|---|---|---|
| WB-1 | **Labornetzteil** | 0–3 V einstellbar, Anzeige/Auflösung ≤ 10 mV, **Strombegrenzung einstellbar auf 10 mA** (Anzeige in mA), Ausgang schaltbar | Speisung 2.0 V (PL2303: ≤ 2.1 V), 10 mA (höchstens 20 mA), erst einstellen dann anschliessen (PROGRAMMIEREN Regel 2, Schritt 5, PS-L3) |
| WB-2 | **Multimeter** | DC 2 V mit 1 mV Auflösung; Widerstand bis ≥ 20 MΩ; Durchgangsprüfer | VIO/VDD 2.0 V messen (Schritt 5), Polarität vor dem Anschliessen, Isolation Scheibe > 10 MΩ, Kontrolle TP1 ↔ R9 Pad 1 ≈ 200 kΩ (Schritt 9), Zellspannung ≥ 3.0 V |
| WB-3 | **Messschieber** | Auflösung 0.01 mm | Scheibendicke 3.0–3.2 mm (PS-W3) |
| WB-4 | **Lötstation** | temperaturgeregelt, feine Spitze (≤ 0.4 mm, konisch oder Meissel) | Draht an R9 Pad 1 (0402, 0.54 × 0.64 mm), Litzen an der Scheibe, B2-Bestückung |
| WB-5 | Lötzinn + Flussmittel | Lötdraht 0.3–0.5 mm mit Flussmittelseele; No-clean-Flussmittelstift | wenig Zinn am 0402-Pad (Schritt 3) |
| WB-6 | Entlötlitze | 1–1.5 mm | Zinnbrücke an R9/R8/D1 entfernen (Schritt 9) |
| WB-7 | **Kupferlackdraht** | 0.1–0.2 mm, selbstverzinnend (**ANNAHME** Polyurethan-Lack) | Draht R9 Pad 1 → RXD (Schritt 3); entfällt mit B2 |
| WB-8 | Kaptonband | ≈ 0.06 mm | Zugentlastung Draht (Schritt 3), Dickenausgleich Scheibe (Kap. 4) |
| WB-9 | **Lupe oder Stereomikroskop** | ≥ 10× | Sichtprüfung R9/R6/TP2 und VIP-Pads (Schritt 9, PS-W2) |
| WB-10 | Kamera/Smartphone | Makroaufnahme durch die Lupe | Foto je Muster (Schritt 9, PS-W4) |
| WB-11 | Feine Pinzette | antimagnetisch | Draht führen, B2-Teile |
| WB-12 | **Kunststoffpinzette/-spatel** | kein Metall | Zelle und Scheibe entnehmen (Schritt 9: „kein Metallwerkzeug“) |
| WB-13 | Isopropanol ≥ 99 %, Pinsel/Wattestäbchen | – | Flussmittel entfernen (Schritt 9) |
| WB-14 | **Prüfspitze bzw. Federstift mit flachem/gerundetem Kopf** + Kabel zum USB-UART | Kopf Ø ≤ 1.5 mm, keine Krone/Spitze | TP2 (Schritt 4, PS-W2); bei B2 zweite Spitze für TP1 |
| WB-15 | Platinenhalter („dritte Hand“) | mit nicht leitenden Backen oder Schaumstoffauflage | Sensor und Prüfspitze ruhig halten (≈ 1–3 min Programmierdauer) |
| WB-16 | USB-UART-Board | Waveshare CH343 (Jumper H3 ab) **oder** PL2303 type A V2 (Jumper J1 ab, Eingangsprüfung README Programmer Kap. 9.3) | Kap. 2 PROGRAMMIEREN |
| WB-17 | Steckbrücken | Dupont female–female/male, 10–20 cm | USB-UART ↔ Scheibe/Netzteil |
| WB-18 | PC mit WSL2 oder Raspberry Pi | `scripts/flash_sensor.py`, pyserial, intelhex | Kap. 3 PROGRAMMIEREN |
| WB-19 | **Dummy-Scheibe** (dieses Projekt) mit fest angelöteten Litzen rot/schwarz | Kap. 4 geprüft (Dicke, Isolation) | Speisung Weg B (Veto PS-K1) |
| WB-20 | Litze rot/schwarz | 0.14–0.25 mm², je 20–30 cm, Krokodilklemmen oder 4-mm-Stecker zum Netzteil | Kap. 4 Schritt 5 |
| WB-21 | Isolierender 2K-Epoxidkleber, 2 Stifte Ø 1.0 mm, Schleifpapier 400 | dünnflüssig | Scheibe kleben und fasen (Kap. 4) |
| WB-22 | Neue Zellen CR2032 | Leerlauf ≥ 3.0 V | Funktionsprüfung nach Schritt 9 (PS-K1 Bed. 3) |
| WB-23 | Behälter für Altzellen, Klebeband | – | Zellen < 2.6 V abkleben und entsorgen (Schritt 9) |
| WB-24 | Arbeitsplatz | sauber, trocken, keine losen Metallteile, ESD-Unterlage **empfohlen** (**ANNAHME**) | Kurzschlussgefahr am offenen Board und am Zellfach |

## 8 Offene Punkte

| Nr | Punkt | Wer |
|---|---|---|
| DC-1 | Freiraum der Lasche beim Weg-B-Schritt (Kap. 6) – **erledigt** 2026-11-09, passt (Kap. 6a) | mechanik |
| DC-2 | Prüfung Kap. 6 (PS-K1 bleibt erfüllt, Kennzeichnung ausreichend), Freigabe Variante B2 | sicherheit |
| DC-3 | JLC-Preis 1.0/2.0 mm, 2 Lagen, Kleinformat am Bestelltag im Rechner ablesen (ersetzt die Spanne Kap. 5) | Auftraggeber/Einkauf |
| DC-4 | **PROTOTYP-PRÜFUNG**: Sitz im Clip, Kontakt Insel–Minuspad, Dicke nach Kleben, B2 mit 19200 Baud am ersten Muster | Elektronik |
| DC-5 | Verweis in `PROGRAMMIEREN_SENSOR.md` Kap. 2 gesetzt (2026-11-09: Scheibe und Werkstattliste); Kap. 5 Schritt 2 und ggf. B2 erst nach DC-2 | Elektronik |
