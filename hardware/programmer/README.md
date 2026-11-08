# fluidi Programmieradapter Rev 1 – Dummy-Zelle 2.0 V mit TX-Puffer

| | |
|---|---|
| Stand | 2026-11-08, Rev 1 (Entwurf Elektronik, **Freigabe Orchestrator/Auftraggeber offen**, Mechanik und Sicherheit prüfen) |
| Anlass | Red-Team Phase 4, B-4 / W-4 (`docs/reviews/phase4_redteam_gesamt.md`) |
| Schaltplan | `fluidi_programmer.kicad_sch` (Generator `gen/gen_programmer.py`, `bash hardware/programmer/gen/run_all.sh`), PDF `out/fluidi_programmer_schematic.pdf` |
| Prüfung | ERC KiCad 10.0.8 WSL **und** Windows: **0 Fehler, 0 Warnungen** (`out/erc_wsl.rpt`, `out/erc_win.rpt`); Netzliste gegen Soll (13 Bauteile, 34 Pins, 8 Netze) |
| SPICE | `simulation/spice/programmer/prog_uart.py` (ngspice 42, `-b`), Bericht `prog_uart_report.txt`, Plot `prog_uart_waveforms.png` |
| Anleitung | `docs/manuals/PROGRAMMIEREN_SENSOR.md` (Ablauf mit `scripts/flash_sensor.py`, Behelf ohne Adapter, Bootloader-Falle W-10) |
| Sensor | Schaltplan/Layout Rev C (`hardware/sensor/`), Pinplan `docs/interfaces/PINMAP_SENSOR.md` |

Der Adapter ist ein **Werkzeug**. Er gehört nicht zum Sensor und ändert weder Stückkosten noch Layout.

## 1 Festlegung in Kürze

| Punkt | Festlegung | Grund |
|---|---|---|
| USB-UART | Waveshare **CH343 USB UART Board** (Micro-USB, SKU 21441; Type-C geht auch, Stiftbelegung am Board prüfen), Jumper H3 **entfernt**, VIO von aussen. **Alternative (2026-11-09, mit Bedingungen):** Waveshare **PL2303 USB UART Board (type A) V2**, Jumper J1 **entfernt** (Kap. 9) | VIO 1.7–5.5 V (`WCH_CH343_Datasheet_V1E.pdf` S. 8 Tab. 6.2), kein Rückstrom aus VIO (S. 4 Kap. 5.2); PL2303GS: VDD_IO 1.8 V … VIN + 0.3 V (`Prolific_PL2303GS_Datasheet_Rev1.0.4.pdf` S. 39 Tab. 11-2a) |
| Speisung Sensor | **2.0 V** aus XC6206P202 (U2), über die **Dummy-Zelle** in den Clip; Vorstufe XC6206P332 (U1) aus USB 5 V | 1.960–2.040 V (`Torex_XC6206_Datasheet_ETR0305-004b.pdf` S. 5 Tab. E-1) ⇒ ≥ 250 mV über VDDS min 1.71 V (`TI_CC2340R5_Datasheet_SWRS272F.pdf` S. 18 Tab. 7.3) statt 40–70 mV bei 1.8 V (W-4). Einzelfehler begrenzt auf 3.3 V (Kap. 2.3) |
| VIO des CH343 | eigener 2.0-V-Regler U3 (gleicher Typ) | das Einstecken der Dummy-Zelle lädt die 4 × 100 µF des Sensors; die USB-Brücke bleibt davon unberührt (Kap. 2.2) |
| Sensor → Host (TX) | **Schmitt-Puffer SN74AUP1G17** (U4) direkt am Federstift TP1, Pull-up 10 MΩ (R1) | CH343-RXD hat 3–21 µA Pull-up (S. 8) und auf dem Waveshare-Board eine LED mit 2 kΩ nach VIO: über die 2 × 100 kΩ kommt kein Low an (SPICE A0: 0.64…1.99 V > 0.5 V) |
| Host → Sensor (RX) | CH343-TXD direkt auf Federstift TP2 | treibt die 2 × 100 kΩ des Sensors; DIO20-Low ≤ 0.19 V bei 2.04 V (SPICE B) |
| Baudrate | 57600 (Standard `flash_sensor.py`), Rückfall 19200 | Reserve ≥ 0.216 Bit bei 57600 mit ungünstigen Kapazitäten (Kap. 5) |
| Mechanik | Dummy-Zelle CR2032-Form und Federstiftkopf als **ein starres Teil** (R2-A2), Gegenhalter unter der Platinenkante | CONCEPTS 2.7, Sicherheitsauflage R2-A2; Konstruktion **mit `mechanik`** (Kap. 4) |
| Kosten | ≈ 25–55 CHF inkl. Versand (Kap. 6) | Ziel < 100 CHF |

## 2 Schaltung

### 2.1 Netze und Bauteile

| Ref | Teil (Hersteller, MPN) | LCSC (JLC-Abfrage 2026-11-08) | Funktion, Beschaltung | Quelle |
|---|---|---|---|---|
| J1 | Steckbrücken zum Waveshare-Board | – | **CH343:** 1 = H3.3 **+5V** (Jumper-Stiftleiste, Jumper H3 weg!), 2 = H2.2 **GND**, 3 = H3.2 **VIO**, 4 = H2.4 **RXD**, 5 = H2.3 **TXD**; +5V alternativ H1.1, falls die 4-polige Leiste H1 bestückt ist (**ANNAHME**, am Board prüfen). **PL2303 (type A) V2:** 1 = J1.3 **VCC5V** (Stift auf der Seite „5V“, Jumper J1 weg!), 2 = P2.2 **GND**, 3 = P2.1 **VCCIO**, 4 = P2.4 **RXD**, 5 = P2.3 **TXD** (Kap. 9) | `docs/references/Waveshare_CH343-USB-UART-Board_Schematic_2026-11-08.pdf` (H1/H2/H3, Micro-Variante); `docs/references/Waveshare_PL2303-USB-UART-Board-TypeA-V2_Schematic_2026-11-08.pdf` (J1, P2) |
| U1 | Torex XC6206P332MR-G | C5446 (Basic, Lager 492 937) | 5 V → +3V3; SOT-23: 1 VSS, 2 VOUT, 3 VIN | Torex DS S. 2 „Pin Assignment“; IOUTMAX 200 mA (S. 1) |
| U2 | Torex XC6206P202MR-G | C2891260 (Extended, Lager 1 963) | +3V3 → **VDD_DUT** (Dummy-Zelle) | DS S. 5 Tab. E-1 1.960–2.040 V, Ishort typ 130 mA (E-6) |
| U3 | Torex XC6206P202MR-G | C2891260 | +3V3 → **VIO** (CH343 + U4 + R1) | wie U2 |
| C1–C4 | Samsung CL21B105KBFNNNE, 1 µF 50 V X7R 0805 | C28323 (Basic) | CIN/CL je LDO | XC6206 DS S. 1 „Typical Application Circuit“ (CIN = CL = 1.0 µF Keramik); Samsung-Katalog `Samsung_CL31A107MQHNNNE_Catalog_2015-11.pdf` (Teilenummernsystem, 21 = 0805) |
| U4 | TI SN74AUP1G17DBVR | C183012 (Extended, Lager 1 280) | TX_PAD (Federstift TP1) → RXD_HOST; DBV: 1 NC, 2 A, 3 GND, 4 Y, 5 VCC | `TI_SN74AUP1G17_Datasheet_SCES579J.pdf` S. 3; VCC 0.8–3.6 V (S. 4 Kap. 6.3) |
| C5 | Samsung CL21B104KBCNNNC, 100 nF 0805 | C1711 | Abblock U4 | Samsung-Katalog |
| R1 | UNI-ROYAL 0402WGF1005TCE, 10 MΩ 1 % 0402 | C26082 | schwacher Pull-up TX_PAD → VIO | `UNI-ROYAL_0402WGF-Serie_Datasheet_LCSC-2024-11.pdf` (Seriendatenblatt 01005–2512, Kap. 6 „Resistance Range“: 0402 1 % 1 Ω–10 MΩ; 0805 nur bis < 10 MΩ, deshalb 0402) |
| J2 | Dummy-Zelle (Eigenbau) | – | 1 = Oberseite **+** (Clip), 2 = Mittelinsel **−** (Minuspad) | Kap. 4 |
| J3 | 2 Federkontaktstifte (Handelsware, **ANNAHME**) | – | 1 = TP1 UART_TX_PAD → U4, 2 = TP2 UART_RX_PAD ← CH343-TXD | Kap. 4 |

Verworfen: **SN74LVC1G17** (`TI_SN74LVC1G17_Datasheet_SCES351Y.pdf` S. 6 Tab. 5-1): Eingangsleckstrom bis **±5 µA** →
bis 1.0 V über 200 kΩ, also kein sicheres Low. Der AUP-Typ garantiert **0.1 µA bei 25 °C, 0.5 µA bei −40…85 °C**
(SCES579J S. 7). Ein Puffer **ohne** Schmitt-Eingang scheidet aus, weil die Flanken über 200 kΩ mehrere µs dauern.
Ein Widerstand nach GND statt Puffer scheidet aus: Der CH343-Pull-up streut 3…21 µA (Faktor 7), dafür gibt es keinen
Teiler, der Low und High gleichzeitig sicher trifft.

### 2.2 Speisung

- **Spannung 2.0 V:** VDDS am Chip = U2-Ausgang − Kabel − Clip − Q1. Mit ≤ 10 mA (Bootloader + Flash-Schreiben, Kap. 2.4)
  und Q1 RDS(on) < 85 mΩ bei VGS −2.5 V (`AOS_AO3401A_Datasheet_Rev3.1.pdf` S. 2; bei −2.0 V nicht spezifiziert, die
  Body-Diode begrenzt den Abfall ohnehin) bleiben die Abfälle im mV-Bereich (**ANNAHME** Kabel ≤ 0.3 Ω). Reserve zu
  VDDS min 1.71 V ≥ 240 mV, zur BOD-Schwelle 1.67 V (fallend, DS S. 19 Kap. 7.6) ≥ 280 mV.
- **Obergrenze:** Die blaue LED an DIO20 hebt das RX-Low an (Phase-3-Review RGB 1.6). Bei 2.04 V bleibt es bei 0.19 V
  (VIL 0.41 V, SPICE B). Die LEDs leuchten bei 2.0 V praktisch nicht (VF bei 5 mA: Rot ≥ 1.8, Grün ≥ 2.5, Blau ≥ 2.6 V,
  `TUOZHAN_P4-1615G2B2R4TS2-06T-001-24_Datasheet_A0.pdf` S. 5).
- **Zwei 2.0-V-Regler:** Beim Einsetzen der Dummy-Zelle lädt U2 den Puffer des Sensors (4 × 100 µF + 10 µF) im
  Strombegrenzer (Ishort typ 130 mA, Tab. E-6) in einigen ms. Hinge VIO an derselben Schiene, könnte VIO unter die
  Reset-Schwelle des CH343 fallen (VRVIO 0.8–1.15 V, CH343 DS S. 8): Das Board meldet sich neu am USB an, der Port
  verschwindet. Mit U3 bleibt VIO stabil. Unterschied der Schienen ≤ 80 mV (je ±2 %): unkritisch, die AUP-Eingänge
  vertragen bis 3.6 V unabhängig von VCC (S. 4 Kap. 6.3), und TP2 liegt hinter 200 kΩ.
- **Anstiegsrate:** ≤ 130 mA in ≥ 410 µF ergibt ≤ 0.32 mV/µs, zulässig 100 mV/µs (DS S. 18 Tab. 7.3).

### 2.3 Einzelfehler (R2-L02)

| Fehler | Folge am Sensor | Bewertung |
|---|---|---|
| U2 durchlegiert | VDD_DUT = 3.3 V | ≤ VDDS max 3.8 V (DS S. 18 Tab. 7.3), kein Schaden; RX-Low wird unsicher (blaue LED), Programmieren scheitert sichtbar |
| U3 durchlegiert | VIO = 3.3 V: CH343-TXD 3.3 V über 200 kΩ an DIO20 bei VDDS 2.0 V, ≤ 7 µA Injektion | Strom wie im Fall R2-A4 (`simulation/spice/README.md` (c)), keine Zelle im Kreis |
| U1 durchlegiert | U2/U3 regeln weiter (VIN bis 6.0 V, Torex DS S. 4) | kein Einfluss |
| U1 **und** U2 durchlegiert | 5 V am Sensor > abs. max 4.1 V (DS S. 18 Tab. 7.1) | Doppelfehler, Geräteschaden möglich, keine Brandgefahr (keine Zelle) |
| Jumper H3 vergessen | VIO hart auf 3.3 V oder 5 V, gegen U3 | Kap. 7 Prüfschritt 2 (VIO messen, bevor der Sensor angeschlossen wird) |
| Dummy verpolt eingesetzt | AO3401A sperrt (CONCEPTS 2.7) | kein Strom |

**Kein Rückspeisen in eine Zelle:** Der Adapter enthält keine Zelle, und die Dummy-Zelle belegt den einzigen Clip.
Solange Dummy-Zelle und Federstiftkopf ein starres Teil sind (R2-A2), kann keine echte Zelle gleichzeitig stecken.

### 2.4 Last des Sensors am Adapter

ROM-Bootloader und Flash-Schreiben: CPU aktiv 4.1 mA (GLDO, VDDS < 2.2 V, DS S. 20 Kap. 7.9) + Flash-Schreiben 1.7 mA
bzw. Löschen 1.2 mA (S. 21 Kap. 7.11) + UART 24.5 µA (S. 20) + rote LED bei jedem 0-Bit ≤ 0.5 mA (SPICE A1) ≈
**≤ 7 mA** (Datenblattwerte bei 3.0 V, **ANNAHME** übertragbar auf 2.0 V). U2 liefert bis 120 mA (Tab. E-2).

## 3 Pegel (SPICE, Kurzfassung)

Grenzen: CH343 VIL ≤ 0.5 V (bei VIO 1.8 V, Tab. 6.2; bei 2.0 V **ANNAHME** gleich, steigt mit VIO); AUP1G17 VT− ≥ 0.47 V
(Hülle, Wert bei 1.65 V) bzw. 0.59 V (interpoliert auf 2.0 V, **ANNAHME**), VT+ ≤ 1.77 V (Hülle) bzw. 1.55 V; CC2340
VIL 0.2 × VDDS, VIH 0.8 × VDDS (DS S. 32).

| Fall | Low am Empfänger | Grenze | Reserve |
|---|---|---|---|
| A0 Ist (ohne Puffer, CH343-RXD an TP1), Pull-up min 3 µA | 0.64 V (1.8 V) / 0.73 V (2.0 V) | 0.50 V | **verletzt** |
| A0 Ist, Pull-up typ/max | 1.77…1.99 V (Pin bleibt high) | 0.50 V | **verletzt** |
| A1 Puffer-Eingang, Leck +0.5 µA, R1 10 MΩ, VDD/VIO 1.96–2.04 V | 0.331–0.369 V | 0.47 V (Hülle) / 0.57–0.60 V | **+101 mV** / +208 mV |
| A1 Puffer-Eingang high, Leck −0.5 µA | 1.862–1.942 V | 1.77 V (Hülle) / 1.52–1.58 V | **+92 mV** / +285 mV |
| A1o Puffer-Ausgang → CH343-RXD (Pull-up max, Board-LED) | 0.040–0.047 V | 0.50 V | +453 mV |
| B Sensor-RX DIO20, LED blau VF-min, 1.96 / 2.00 / 2.04 V | 0.136 / 0.162 / 0.190 V | 0.39 / 0.40 / 0.41 V | **+218…+256 mV** |

**Wahl von R1** (SPICE A1/A1z, `prog_uart_report.txt`): R1 hält TP1 high, solange DIO6 noch hochohmig ist (der
Bootloader schaltet TX erst nach dem ersten Zugriff als Ausgang, TRM `SWCU193A` S. 464). Ein kleinerer R1 hebt aber
das Low an: 4.7 MΩ ergibt 0.40 V (Reserve +65 mV) und bei 57600 Baud mit ungünstigen Kapazitäten nur 0.17 Bit, 2.2 MΩ
verletzt die Hülle (0.48 V). Mit 10 MΩ ist der Ruhepegel bei maximalem Leckstrom laut Datenblatt (0.1 µA bei 25 °C)
nur ≈ 1.0 V, also im Hysteresebereich (A1z). Das ist unschädlich: Der Schmitt-Eingang schwingt nicht, ein Low vor dem
Sync erscheint am CH343 als Break (Byte 0x00), und `flash_sensor.py` verwirft den Empfangspuffer vor dem Sync und
überspringt 0x00-Bytes vor dem ACK (TRM S. 462–463 erlaubt führende Nullen). **PROTOTYP-PRÜFUNG:** Ruhepegel am
U4-Ausgang (nicht am hochohmigen Eingang) nach dem Einsetzen messen, Erwartung high.

## 4 Mechanik: Dummy-Zelle und Federstiftkopf (Konstruktion mit `mechanik`)

Masse aus `docs/interfaces/PCB_OUTLINE.md` Kap. 5 (Mechanik-Koordinaten X = x_KiCad − 150, Y = y_KiCad − 30) und dem
Layout Rev C (`hardware/programmer/gen/behelf_pads.py`, Bild `out/behelf_lageplan.png`):

| Merkmal | Mass | Quelle |
|---|---|---|
| Zelle CR2032 | Ø 20.0 mm, Höhe 3.2 mm (max) | `Panasonic_CR2032_Datasheet_2026-02.pdf` S. 1 |
| Zellmitte | X 3.0, Y 34.8; Einschub in **+X** (offenes Clip-Ende), geschlossenes Ende −X | PCB_OUTLINE Kap. 5 Zeile XBT1 |
| Clipkörper | X −4.4 … 11.7, Höhe 4.1 mm | ebd.; `Keystone_3034_Catalog_M65.pdf` S. 1 |
| Minuspad | 4.0 × 4.0 mm in der Zellmitte | Layout Rev C |
| TP1 / TP2 | X −10.6, Y 25.5 / 28.5 (Abstand 3.0 mm), Pad Ø 1.5 mm, Via-in-Pad | Layout Rev C (`behelf_pads.py`) |
| Platinenkante | X ±13.0 im Fach | PCB_OUTLINE Z4 |
| B-Seite Fach | nur Silkscreen, keine Pads | PCB_OUTLINE Z4 Fach B |

**Dummy-Zelle** (Auflage PS-W3, `docs/reviews/phase5_programmer_sicherheit.md`): Scheibe Ø 20.0 mm, **Gesamtdicke
3.0–3.2 mm inkl. Kupfer und Kleber** (CR2032 höchstens 3.2 mm, `Panasonic_CR2032_Datasheet_2026-02.pdf` S. 1; die
Clip-Lötstellen liegen auf dem Katalogminimum, ein dickerer Dummy spreizt den Clip). Zwei FR4-Scheiben 1.6 mm ergeben
mehr als 3.2 mm und sind **nicht zulässig**; z. B. eine Scheibe dünner wählen oder plan schleifen (Plattendicken nach
Lieferant, **ANNAHME**). Dicke an 3 Stellen mit dem Messschieber messen und auf dem Dummy notieren (Kap. 7 Schritt 3).
Rand wie bei einer Zelle leicht fasen.
- Oberseite: Kupfer ganzflächig = **+** (Clip drückt darauf), Litze von der Seite in einer Nut zwischen den Scheiben.
- Unterseite: Kupfer bis auf eine **Mittelinsel Ø 8 mm** entfernt = **−** (deckt das 4 × 4-Pad samt ±1 mm Lage ab). Litze
  durch eine Bohrung Ø 1 mm von innen anlöten, Lötstelle plan schleifen (keine Erhebung, die das Minuspad zerkratzt).
- Rand und übrige Unterseite isolierend (FR4). Kein Plusrand auf der Unterseite (R2-W01).
- Isolation Ober-/Unterseite vor dem ersten Einsatz messen (> 10 MΩ).

**Federstiftkopf – Konzept Mechanik (Phase 5, noch keine druckbare Konstruktion).** Lagen aus dem Layout Rev C
(pcbnew, Pad-Mitten in Kopfkoordinaten x/z, `docs/interfaces/PCB_OUTLINE.md` Kap. 1) und `fluidi_params.py`:

| Merkmal | Lage | Quelle |
|---|---|---|
| TP1 (TX) / TP2 (RX) | x −10.60, z **28.00** / **25.00**, Pad Ø 1.5, auf F (y 6.6) | `fluidi_sensor.kicad_pcb` (pcbnew, Phase 5 ausgelesen) |
| Clipkörper XBT1 | x −4.4 … 11.7, z 7.15 … 30.25, Höhe 4.1 → Oberkante y 2.5 | PCB_OUTLINE Kap. 5 |
| Zelle/Dummy in Endlage | x −7.0 … 13.0, Mitte z 18.70, Einschub von +x nach −x | PCB_OUTLINE Kap. 5 |
| Schott-Unterkante (nicht belasten) | z 30.8 (TP1-Pad-Rand z 28.75 → 2.05 mm Abstand) | `fluidi_params.py` Z['BULK0'] |
| Platinenkante neben TP | x −13.0 (Fach), B-Seite y 8.2, Hülse abgezogen → frei | PCB_OUTLINE Kap. 3 |

Befund aus der Geometrie: Ein **starr** mit dem Dummy verbundener Stift auf Pad-Höhe (y ≈ 6.6) läuft beim Einschieben
(Bewegung −x) über den Clipkörper (x −4.4 … 11.7, bis y 2.5), sobald der Dummy mehr als ≈ 6 mm vor der Endlage steht.
Stifte mit einem Hub ≥ 5 mm gibt es in dieser Bauform kaum (**ANNAHME**). Darum Vorschlag:
1. **Bügel** (ASA, 3D-Druck) fest mit der Dummy-Zelle verklebt bzw. verstiftet, greift von der offenen Clip-Seite
   (+x, x > 13) **vor dem Clip** (y ≤ 1.5, d. h. ≥ 1 mm Luft zur Clip-Oberkante y 2.5) nach −x bis über TP1/TP2.
2. **Stiftträger als Schwinge** am Bügel, unverlierbar gelagert (Achse parallel z), mit Feder nach vorn (−y) gehalten:
   Beim Einschieben stehen die Stiftspitzen vor y 1.5. Erst in Endlage des Dummys schliesst der **Gegenhalter**
   (Klammer um die Platinenkante x −13, Auflage auf B bei TP-Höhe) die Schwinge und drückt die Stifte auf TP1/TP2. Die
   Federkraft schliesst sich über Platine und Gegenhalter, nicht über das Schott (PS-W1 d) und nicht über die Zelle.
3. Der Gegenhalter lässt sich nur schliessen, wenn der Dummy ganz im Clip sitzt (Anschlag am Bügel bei x 13.0 +
   Spiel) → PS-W1 (a). Mit gestecktem Adapter belegt der Dummy den Clip → PS-W1 (b). Dummy verkehrt (Bügel zeigt nach
   hinten) → Schwinge liegt auf B, Stifte erreichen TP1/TP2 nicht → PS-W1 (c).
4. **Stifte (PS-W2): flacher oder gerundeter Kopf, keine Krone/Spitze**, auf den gefüllten VIP-Flächen; Federkraft so
   klein wie möglich (≤ 1 N je Stift, **ANNAHME**), Hub ≥ 1 mm. Kein Löten auf TP1/TP2/Minuspad/VBAT-Pad.
5. U4/R1/C5 auf dem Stiftträger, Draht Stift TP1 → U4-Pin 2 ≤ 3 cm (Kap. 3/5).

**Entscheid Sicherheit (`docs/reviews/phase5_sicherheit_runde3.md` Kap. 2):** „Bügel + unverlierbare Schwinge“ erfüllt
PS-W1 / R2-A2 unter den Auflagen A1–A5; die zweiteilige Alternative (Stiftträger aufstecken) ist **abgelehnt**. Die
Konstruktion (PA-1) setzt um:

| Auflage | Umsetzung in der Konstruktion (Konzept, Prüfung ST-P1) |
|---|---|
| A1 | Bügel mit dem Dummy verklebt **und** verstiftet; Schwingenachse eingepresst oder verklebt, keine Rast-/Schnappverbindung |
| A2 | Gegenhalter unverlierbar an Schwinge bzw. Bügel (kein loses Teil) |
| A3 | Zwangsfolge: Schwinge schliesst erst, wenn der Bügelanschlag an der Platinenkante liegt (Dummy in Endlage); Feder hält die Schwinge offen; offen ≥ 1 mm Luft Stift ↔ Clip, Schwinge an der Clipseite isolierend |
| A4 | Mit eingesetzter CR2032 stösst der Bügel an die Zelle: Stifte erreichen TP1/TP2 nicht, Dummy berührt Zelle/Clip nicht |
| A5 | Litzen von Dummy und Stiften gemeinsam an der Baugruppe zugentlastet; keine Steckverbindung zwischen Dummy und Stiftträger |

Weg A bleibt bis zum Bestehen von ST-P1 (a)–(g) **nicht freigegeben**.

**Warum noch kein Druckteil:** Für die Federstifte liegt **kein Datenblatt lokal** (`docs/datasheets/INDEX.csv` Zeile
P-J3). Für Bohrung/Presssitz, Einbaulänge, Hub und Kraft werden Aussen- und Kopfdurchmesser, Länge, Hub, Federkraft
gebraucht. Benötigt: Datenblatt eines Federkontaktstifts Ø ≤ 1.5 mm Kopf flach oder gerundet (z. B. Raster-1.27-Typ),
Hub ≥ 1 mm, Kraft ≤ 1 N; dazu das Massbild des Keystone 3034 ist vorhanden (`Keystone_3034_Catalog_M65.pdf`). Danach
Generator `mechanical/gen/fluidi_programmer_head.py` (Bügel, Schwinge, Gegenhalter) mit Kollisionsprüfung gegen
`fluidi_sensor_mit_pcb.step` (ohne Hülse). **PROTOTYP-PRÜFUNG** ST-P1 (PS-W1 a–d).

## 5 Zeitverhalten (SPICE)

Bytefolge 0x55 0x55 0x00 0xFF 0x01 0x80 0xCC 0x33, 8N1; Empfänger mit Startflankenerkennung und Abtastung in Bitmitte,
Taktfehler ±1.5 % (CH343 S. 9 Tab. 6.3). Reserve = kleinster Abstand Abtastpunkt–Flanke, ideal 0.357 Bit bei ±1.5 %.
Kriterium ≥ 0.20 Bit (**ANNAHME**). Kapazitäten sind **ANNAHMEN** (Kopf von `prog_uart.py`): nominal 1/2/5 pF
(R9-R10-Knoten / TP1 / Stift + Draht + Puffer), schlecht 3/3/10 pF; DIO20 7…9 pF, blaue LED 0/15/30 pF.

| Richtung | Kapazitäten | t10–90 steigend / fallend | Reserve 19200 / 38400 / 57600 Baud (schlechteste Schwellenecke) |
|---|---|---|---|
| Sensor → Puffer (TP1) | nominal | 3.1 / 3.1 µs | 0.345 / 0.318 / **0.290** |
| Sensor → Puffer (TP1) | schlecht | 6.0 / 6.0 µs | 0.320 / 0.268 / **0.216** |
| Sensor → Puffer am Kabelende (Gegenbeispiel) | 1/2/40 pF | 18.2 / 18.2 µs | 0.213 / 0.040 / **0.002, Bytes falsch** |
| CH343 → DIO20 (2.0 V) | nominal, LED 0 pF | 3.2 / 2.4 µs | 0.357 / 0.356 / **0.356** |
| CH343 → DIO20 (2.0 V) | schlecht, LED 15 pF | 10.9 / 8.3 µs | 0.356 / 0.353 / **0.344** |
| CH343 → DIO20 (2.0 V) | schlecht, LED 30 pF | 17.5 / 13.3 µs | 0.354 / 0.341 / **0.300** |
| CH343 → DIO20 (2.2 V, Behelf) | schlecht, LED 30 pF | 17.5 / 11.1 µs | 0.351 / 0.330 / **0.308** |

Eingeschwungene Pegel im Zeitbereich: TP1 low 0.350 V / high 2.098 V (Leck +0.5 µA), DIO20 low 0.162 V (2.0 V) bzw.
0.313 V (2.2 V). Bitzeit bei 57600 Baud: 17.4 µs.

Alle Fälle mit Puffer am Federstift erfüllen das Kriterium bei allen drei Baudraten. **PROTOTYP-PRÜFUNG:** Flanke am
U4-Eingang mit Tastkopf 10:1 (≈ 10 pF, verfälscht selbst) bzw. am U4-Ausgang messen; 20 × Flashen bei 57600 und 19200
(RGB-3, INSTALL FW-T2).

## 6 Stückliste, Bezug, Kosten

Preise: LCSC/JLC-Teilesuche 2026-11-08 (Stückpreis ab 1, USD), Waveshare/eckstein aus `docs/manuals/INSTALL_FIRMWARE_TOOLS.md`
(Abruf 2026-11-07). Kurs ≈ 0.82 CHF/USD bzw. 0.94 CHF/EUR (**ANNAHME**).

| Pos | Teil | Menge | Bezug | Preis |
|---|---|---|---|---|
| 1 | Waveshare CH343 USB UART Board (Micro, SKU 21441) | 1 | waveshare.com bzw. eckstein-shop.de (Type-C) | USD 3.49 / EUR 4.15 |
| 2 | XC6206P332MR-G | 1 (+ Reserve) | LCSC C5446 | USD 0.15 |
| 3 | XC6206P202MR-G | 2 (+ Reserve) | LCSC C2891260 | USD 0.21 |
| 4 | SN74AUP1G17DBVR | 1 (+ Reserve) | LCSC C183012 | USD 0.31 |
| 5 | CL21B105KBFNNNE 1 µF 0805 | 4 | LCSC C28323 | USD 0.03 |
| 6 | CL21B104KBCNNNC 100 nF 0805 | 1 | LCSC C1711 | USD 0.01 |
| 7 | 0402WGF1005TCE 10 MΩ | 1 | LCSC C26082 | < USD 0.01 |
| 8 | Federkontaktstifte, Ø ≤ 1.5 mm, Hub ≥ 1 mm | 2 (+ Reserve) | Elektronik-Fachhandel | **ANNAHME** CHF 2–10 |
| 9 | FR4 einseitig Cu 1.6 mm, Lochraster- oder Kupferplatine für U1–U4, SOT-23-Adapterplatinen | – | Werkstattbestand / Fachhandel | **ANNAHME** CHF 0–10 |
| 10 | Litze AWG 28–30, Steckbrücken 2.54 mm, ASA für den Bügel | – | Werkstattbestand | **ANNAHME** CHF 0–5 |
| 11 | Versand LCSC in die Schweiz bzw. Waveshare | – | – | **ANNAHME** CHF 10–25 |

LCSC verkauft Kleinteile oft nur in Mindestmengen (5–100 Stück); das ändert den Betrag kaum. **Summe ≈ CHF 25–55**,
deutlich unter 100 CHF. Die Mindestmengen reichen für 2–5 Adapter.

## 7 Aufbau und Inbetriebnahme (ohne Sensor)

1. Bestücken: U1–U3, C1–C4 nahe an die Regler, U4/C5/R1 auf den Federstiftkopf. Leitung Stift TP1 → U4 ≤ 3 cm.
   Flussmittel am TP1-Knoten gründlich entfernen (10 MΩ / 200 kΩ: Kriechströme > 0.1 µA verschieben den Pegel).
2. Waveshare: **Jumper H3 abziehen** (PL2303-Board: **Jumper J1**, vorher Eingangsprüfung Kap. 9.3). J1 anschliessen. USB einstecken. Messen: +3V3 = 3.2–3.4 V, **VDD_DUT und VIO =
   1.96–2.04 V**. Erst dann weiter.
3. Dummy-Zelle: Dicke 3.0–3.2 mm an 3 Stellen (PS-W3); Widerstand Oberseite ↔ Mittelinsel > 10 MΩ ohne Speisung; mit Speisung 1.96–2.04 V, richtige Polarität.
4. **Schleifentest mit Prüfstecker:** Zwei 100-kΩ-Widerstände in Serie zwischen Stift TP2 und Stift TP1 (bildet die
   Barriere des Sensors nach). `picocom -b 57600 /dev/ttyACM0`, Zeichen tippen → Echo. Danach mit 19200. Damit sind
   CH343-TXD, 200 kΩ, Puffer und CH343-RXD gemeinsam geprüft.
5. Ruhestrom ohne Sensor: < 1 mA aus USB (XC6206 IDD typ 1 µA, AUP ICC ≤ 0.5 µA; der Hauptteil ist das Waveshare-Board).

## 8 Offene Punkte

| Nr | Punkt | Art |
|---|---|---|
| PA-1 | Bügel/Schwinge/Gegenhalter konstruieren (Konzept Kap. 4, Phase 5); **blockiert durch fehlendes Federstift-Datenblatt** (INDEX P-J3); Einteiligkeit nach PS-W1 durch Sicherheit bestätigen | `mechanik`, `sicherheit` |
| PA-2 | Sicherheitsprüfung des Adapters (R2-A2 einteilig, R2-L02 Einzelfehler Kap. 2.3) | `sicherheit` |
| PA-3 | 20 × Flashen bei 57600 und 19200 Baud, Flanke an U4 messen (Kap. 5) | PROTOTYP-PRÜFUNG |
| PA-4 | VDDS am Sensor während Chip-Erase messen (Erwartung ≥ 1.95 V) | PROTOTYP-PRÜFUNG |
| PA-5 | Bezug Waveshare-Board mit Versand in die Schweiz (FW-T3); **Alternative PL2303 (pi-shop.ch) elektrisch freigegeben mit Bedingungen** (Kap. 9) | Auftraggeber |
| PA-6 | Entladewiderstand **470 Ω VIO → GND** (0805, parallel C4) gegen VDD_IO > VIN + 0.3 V beim Ziehen der USB (PL2303, Kap. 9.4). Schaltplanänderung Rev 1 → **Rückmeldung Orchestrator** nötig; bis dahin Ablaufregel Kap. 9.4 | Elektronik, Orchestrator |
| PA-7 | Eingangsprüfung PL2303-Board (Kap. 9.3) und 20 × Flashen bei 57600/19200 mit dem PL2303 | PROTOTYP-PRÜFUNG |

## 9 Alternative USB-UART: Waveshare PL2303 USB UART Board (type A) V2 (Prüfung Elektronik 2026-11-09)

Anlass: CH343-Board nur aus dem Ausland (FW-T3); PL2303-Board bei pi-shop.ch Art. 11757, CHF 8.90
(`docs/manuals/EINKAUFSLISTE.md` Kap. 3). **Ergebnis: freigegeben mit Bedingungen B1–B6 (Kap. 9.5)** für Weg A und
Weg B. Nachweis: `simulation/spice/programmer/prog_uart_pl2303.py` (ngspice 42, `-b`), Bericht
`prog_uart_pl2303_report.txt`, Plot `prog_uart_pl2303_pwr.png`. Der Adapter-Schaltplan Rev 1 bleibt unverändert;
J1 hat dieselben fünf Funktionen, nur die Gegenstifte am Board ändern sich (Tab. 2.1).

### 9.1 Datenblatt und Board gegenüber CH343

| Punkt | PL2303GS / Board (Quelle) | CH343 | Folge |
|---|---|---|---|
| I/O-Speisung | VDD_IO 1.8 V … VIN + 0.3 V (`Prolific_PL2303GS_Datasheet_Rev1.0.4.pdf` S. 39 Tab. 11-2a); abs. max VDD_IO −0.3 … VIN + 0.3 V (S. 39 Tab. 11-1); keine Aussage zu Rückstrom | 1.7–5.5 V, kein Rückstrom aus VIO | VCCIO nie ohne USB (Kap. 9.4) |
| Eingang | VIL ≤ 0.4 V, VIH ≥ 0.7 × VDD_IO (S. 39 Tab. 11-2b); RXD mit schwachem Pull-up nach VDD_IO, **Wert fehlt** (S. 13 Tab. 7-2, S. 27) | VIL ≤ 0.5 V, 3–21 µA | Pull-up als Klammer 0/100 µA (**ANNAHME**) |
| Ausgang | VOL ≤ 0.4 V, VOH ≥ 0.7 × VDD_IO, **ohne Strom-Testbedingung** (S. 39 Tab. 11-2b) | VOL ≤ 0.4 V @ 3 mA, VOH ≥ VIO − 0.4 V @ 2 mA | Messkriterien Kap. 9.3 Schritt 4/5 |
| I/O-Pins | 5-V-tolerant, −0.3 … 6.0 V (S. 39 Tab. 11-1; S. 33) | – | Pegel an RXD/TXD ≤ 2.1 V, weit unter 6.0 V (Verhalten ohne VIN im Datenblatt nicht beschrieben) |
| Taktgenauigkeit | keine Angabe | ±1.5 % | **ANNAHME** ±1.5 %; der ROM-Bootloader misst die Baudrate des Hosts (TRM S. 461/464) |
| Board | `Waveshare_PL2303-USB-UART-Board-TypeA-V2_Schematic_2026-11-08.pdf`: P2 1 VCCIO / 2 GND / 3 TXD / 4 RXD; Jumper J1 1 VCC3.3V / 2 VCCIO / 3 VCC5V; RXD-LED D3 und TXD-LED D2 je **1 kΩ** von VCCIO; PWR-LED 1 kΩ an 5 V; C1 4.7 µF an VIN, C4 1 µF an VCCIO; LED-Typ nicht angegeben | RXD-LED 2 kΩ | LED-Modell **ANNAHME** (rote Sensor-LED, Exemplar mit grösstem Strom) |
| Treiber | VID/PID 067B:23A3 (S. 22 Tab. 9-1; vor Rev. 1.0.3 23F3, S. 2) | `cdc_acm` | Linux-Modul `pl2303`; im WSL-Kernel 6.18.54.1 enthalten (`modules.alias`: 067B:23A3 und 23F3, geprüft 2026-11-09). Port **`/dev/ttyUSB0`** statt `/dev/ttyACM0`. Raspberry Pi OS: **ANNAHME** enthalten (`ls /dev/ttyUSB*`) |

### 9.2 Pegel und Zeitverhalten (SPICE, `prog_uart_pl2303_report.txt`)

| Fall | Ergebnis | Grenze | Bewertung |
|---|---|---|---|
| A0p PL2303-RXD direkt an TP1 (ohne Puffer) | 0.59 V (ohne Pull-up) bis 2.0 V (100 µA) | 0.40 V | verletzt → **Puffer U4 bleibt Pflicht** |
| A1 Puffer-Eingang | unabhängig vom Host, `prog_uart_report.txt` gilt: Reserve ≥ +101 mV | – | unverändert |
| A1p U4-Ausgang low → PL2303-RXD (LED 1 kΩ, Pull-up 0/100 µA), VIO 1.96–2.04 V | 0.062–0.089 V | 0.40 V | **+311 mV** |
| A2p Weg B, RXD an R9 Pad 1, VDD = VCCIO 2.0 V | 0.266–0.287 V | 0.40 V | +113 mV |
| A2p dto. 2.1 V / 2.2 V | 0.322–0.343 V / 0.379–0.399 V | 0.40 V | +57 mV / **+1 mV** → Weg B **höchstens 2.1 V** (CH343: 2.2 V) |
| A3p Weg B am falschen Pad (R9 Pad 2) | bis 1.99 V | 0.40 V | wie bisher falsch |
| Bp DIO20 low, TXD-Low 0 V (VDD 1.96 / 2.04 / 2.0 / 2.2 V) | 0.136 / 0.190 / 0.162 / 0.313 V | 0.2 × VDDS | +218 … +256 mV (Weg B 2.2 V: +127 mV) |
| Bp DIO20 low, TXD-Low = Datenblattgrenze 0.4 V | 0.404–0.450 V | 0.2 × VDDS | verletzt → Messkriterium TXD-Low ≤ 0.10 V |
| Bh DIO20 high, TXD-High = Datenblattminimum 0.7 × VDD_IO | 1.37 V (VIO 1.96, VDD 2.04 V) | 1.63 V (0.8 × VDDS) | verletzt → Messkriterium TXD-High ≥ VCCIO − 0.10 V |
| Transient TXD → DIO20, 57600 Baud, LED 30 pF, ±1.5 % | Reserve 0.300 / 0.284 / 0.205 Bit bei TXD-Low 0 / 0.1 / 0.2 V; bei 0.39 V 0.001 Bit, Bytes falsch | ≥ 0.20 Bit | mit TXD-Low ≤ 0.10 V ≥ 0.28 Bit |
| Grenzstrom Board → RXD (Weg A, U4-Ausgang bis 0.40 V) | 2.17 mA | – | Board-Modell: 0.43–0.57 mA |
| Grenzstrom Board → DIO6 (Weg B bis 0.40 V) | 0.69 / 0.53 / 0.35 mA bei 2.0 / 2.1 / 2.2 V | – | Messkriterium ≤ 0.69 mA bei 2.0 V |

### 9.3 Eingangsprüfung des Boards (einmal je Board, vor dem ersten Sensor)

Werkzeug: Labornetzteil 2.0 V / 10 mA, Multimeter. Kein Sensor angeschlossen.

1. Jumper J1 abziehen, USB einstecken (PWR-LED leuchtet). Ohne Draht an P2 messen: J1-Stift auf der Seite „5V“
   ≈ 5 V gegen GND (USB; Lage laut Bestückungsdruck, Schaltplan S. 2, **am Board prüfen**), Stift „3.3V“ 2.97–3.63 V
   (VO_33, PL2303GS S. 39 Tab. 11-2a),
   **VCCIO (P2.1) offen ≤ 0.10 V** (das Board treibt VCCIO nicht zurück; Voraussetzung für Weg B).
2. Erst jetzt das Netzteil (2.0 V, 10 mA, ausgeschaltet) an P2.1/P2.2 und einschalten: Strom ≤ 1 mA (VDD_IO-Ruhestrom
   ist im Datenblatt nicht angegeben; Budget Weg B: Sensor ≤ 7 mA + Board-LEDs ≤ 1 mA + VDD_IO ≤ 1 mA < 10 mA).
3. Strommesser (mA-Bereich) von P2.4 RXD nach GND: **≤ 0.69 mA** (Grenze Weg B bei 2.0 V). 0.69–2.1 mA: nur Weg A.
   Über 2.1 mA: Board ungeeignet.
4. Port öffnen (`picocom -b 57600 /dev/ttyUSB0`), P2.3 TXD gegen GND: **≥ 1.90 V**.
5. Break halten: `python3 -c "import serial,time; s=serial.Serial('/dev/ttyUSB0',57600); s.break_condition=True; time.sleep(30)"`,
   währenddessen TXD **≤ 0.10 V**.
6. **Netzteil aus, dann USB ziehen.** Werte auf dem Board notieren.

### 9.4 VDD_IO > VIN + 0.3 V (Rückspeisung) und Querströme

- **Weg A, USB einstecken:** VIO entsteht aus VIN über U1 und U3 → max(VDD_IO − VIN) = 0.000 V (SPICE (3), auch mit
  angeschlossenem Sensor).
- **Weg A, USB ziehen:** VIN fällt mit IDD max 15 mA (S. 39) schneller als VIO (2.1 µF, Last unbekannt = 0, ANNAHME).
  Unter VIN ≈ 1.8 V regeln U1/U3 nicht mehr (Torex S. 5), die Parasitärdiode des XC6206 leitet nur VOUT → VIN (S. 3).
  Ergebnis ohne Gegenmassnahme: **VDD_IO − VIN bis 1.06 V**, über 0.3 V während 47 ms (Sensor ab) bzw. bis
  Simulationsende 400 ms (Sensor dran; VIO ohne Last). Quelle ist nur die Ladung der VIO-Kondensatoren
  (≈ 2.1 µF × 1 V ≈ 2 µC); kein anderer Pfad speist VIO. Mit Klemmdiode RB751S-40 VIO → +5V: 0.38–0.41 V (VF 0.37 V @
  1 mA, `CJ_RB751S-40_Datasheet.pdf` S. 1) – reicht nicht. Mit **470 Ω VIO → GND: ≤ 0.014 V** in allen Fällen (1 kΩ
  ohne Sensor: 0.45 V). Mehrlast für U3 4.3 mA, unkritisch (Ishort typ 130 mA). → **PA-6** (Schaltplanänderung, Rückmeldung).
  Bis dahin: Dummy-Zelle **vor** dem Ziehen der USB entfernen; **PROTOTYP-PRÜFUNG:** VIO und VIN beim Ziehen mit
  Oszilloskop aufnehmen.
- **Weg B:** VCCIO kommt vom Labornetzteil. Ohne USB läge VDD_IO **dauernd** bei 2.0–2.1 V über VIN = 0 V, Strom nur
  durch die 10-mA-Begrenzung begrenzt. Deshalb feste Reihenfolge (PROGRAMMIEREN_SENSOR Kap. 5): **USB zuerst
  einstecken, Netzteil zuletzt ein; Netzteil zuerst aus, USB zuletzt ziehen**; PC während Weg B nicht in den
  Ruhezustand. Einzelfehler (Reihenfolge vertauscht): Schaden am Board möglich (8.90 CHF); der Sensor bleibt durch die
  10-mA-Begrenzung geschützt, keine Zelle im Kreis (Regel 1). **Sicherheit zur Kenntnis.**
- **Gegenrichtung:** Bei gesteckter USB und offenem VCCIO ≤ 0.10 V (Kap. 9.3 Schritt 1) → das Board speist den Sensor
  nicht über VCCIO.
- **LED-Ströme an 2.0 V:** RXD-LED bei RXD = 0 V 0.43 mA (Modell, mit Pull-up 100 µA 0.53 mA), TXD-LED gleich gross
  bei TXD low; beide aus VCCIO (Weg A: U3, Weg B: Netzteil). PWR-LED aus USB 5 V.

### 9.5 Bedingungen der Freigabe

| Nr | Bedingung |
|---|---|
| B1 | Weg A nur mit Puffer U4 am Federstift; PL2303-RXD nie direkt an TP1 (A0p) |
| B2 | Jumper J1 des Boards entfernt; Anschluss J1 nach Tab. 2.1 |
| B3 | Eingangsprüfung Kap. 9.3 bestanden (VCCIO offen ≤ 0.10 V, RXD-Kurzschlussstrom ≤ 0.69 mA bzw. ≤ 2.1 mA nur Weg A, TXD high ≥ 1.90 V, TXD low ≤ 0.10 V) |
| B4 | Weg B: Netzteil 2.0 V, **höchstens 2.1 V**, 10 mA; Reihenfolge USB/Netzteil nach Kap. 9.4 |
| B5 | Weg A: bis zum Entscheid PA-6 Dummy-Zelle vor dem Ziehen der USB entfernen |
| B6 | Port `/dev/ttyUSB0` (Treiber `pl2303`); 20 × Flashen bei 57600 und 19200 (PA-7) |
