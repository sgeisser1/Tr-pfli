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
| USB-UART | Waveshare **CH343 USB UART Board** (Micro-USB, SKU 21441; Type-C geht auch, Stiftbelegung am Board prüfen), Jumper H3 **entfernt**, VIO von aussen | VIO 1.7–5.5 V (`WCH_CH343_Datasheet_V1E.pdf` S. 8 Tab. 6.2), kein Rückstrom aus VIO (S. 4 Kap. 5.2) |
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
| J1 | Steckbrücken zum Waveshare-Board | – | 1 = H3.3 **+5V** (Jumper-Stiftleiste, Jumper H3 weg!), 2 = H2.2 **GND**, 3 = H3.2 **VIO**, 4 = H2.4 **RXD**, 5 = H2.3 **TXD**; +5V alternativ H1.1, falls die 4-polige Leiste H1 bestückt ist (**ANNAHME**, am Board prüfen) | `docs/references/Waveshare_CH343-USB-UART-Board_Schematic_2026-11-08.pdf` (H1/H2/H3, Micro-Variante) |
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

**Dummy-Zelle:** zwei Scheiben Ø 20.0 mm aus FR4 1.6 mm, einseitig kupferkaschiert, verklebt (zusammen 3.2 mm):
- Oberseite: Kupfer ganzflächig = **+** (Clip drückt darauf), Litze von der Seite in einer Nut zwischen den Scheiben.
- Unterseite: Kupfer bis auf eine **Mittelinsel Ø 8 mm** entfernt = **−** (deckt das 4 × 4-Pad samt ±1 mm Lage ab). Litze
  durch eine Bohrung Ø 1 mm von innen anlöten, Lötstelle plan schleifen (keine Erhebung, die das Minuspad zerkratzt).
- Rand und übrige Unterseite isolierend (FR4). Damit ist der Dummy sicherer als eine echte Zelle: Er hat keinen
  Plusrand auf der Unterseite (R2-W01).
- Isolation Ober-/Unterseite vor dem ersten Einsatz messen (> 10 MΩ).

**Federstiftkopf:** zwei Federkontaktstifte im Abstand 3.0 mm über TP1/TP2, Spitzen mit Krone oder Spitze für die
gefüllten Via-in-Pad-Flächen. Der Kopf ist **starr mit der Dummy-Zelle verbunden** (R2-A2), z. B. als Bügel aus ASA
(3D-Druck), der von der +X-Seite über den Clip (Höhe 4.1 mm, Abstand ≥ 1 mm) zu X −10.6 greift. Ein Gegenhalter
greift unter die Platinenkante bei X −13 auf der B-Seite und nimmt die Federkraft auf. Die Elektronik (U4, R1, C5)
sitzt auf dem Bügel, **≤ 3 cm** Draht vom Stift TP1 bis U4-Pin 2 (SPICE: mit 40 pF am Kabelende fällt 57600 Baud aus).
Federkraft, Hub und Stifttyp: **ANNAHME**, mit `mechanik` festlegen. Der Kopf darf das Schott nicht belasten und muss
ohne Hülse passen (`docs/reviews/phase3_sleeve_sicherheit.md`).

Offene Geometriefrage (**mit `mechanik`**): Kommt man an den Anschlaglappen am geschlossenen Clip-Ende (X ≈ −4.4…−7)
vorbei, kann der Bügel auch flach auf der −X-Seite der Scheibe ansetzen. Das geht nur mit dem 3D-Modell des Clips.

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
2. Waveshare: **Jumper H3 abziehen**. J1 anschliessen. USB einstecken. Messen: +3V3 = 3.2–3.4 V, **VDD_DUT und VIO =
   1.96–2.04 V**. Erst dann weiter.
3. Dummy-Zelle: Widerstand Oberseite ↔ Mittelinsel > 10 MΩ ohne Speisung; mit Speisung 1.96–2.04 V, richtige Polarität.
4. **Schleifentest mit Prüfstecker:** Zwei 100-kΩ-Widerstände in Serie zwischen Stift TP2 und Stift TP1 (bildet die
   Barriere des Sensors nach). `picocom -b 57600 /dev/ttyACM0`, Zeichen tippen → Echo. Danach mit 19200. Damit sind
   CH343-TXD, 200 kΩ, Puffer und CH343-RXD gemeinsam geprüft.
5. Ruhestrom ohne Sensor: < 1 mA aus USB (XC6206 IDD typ 1 µA, AUP ICC ≤ 0.5 µA; der Hauptteil ist das Waveshare-Board).

## 8 Offene Punkte

| Nr | Punkt | Art |
|---|---|---|
| PA-1 | Bügel/Gegenhalter und Federstifttyp konstruieren (Geometrie Kap. 4, Clip-3D-Modell, ohne Hülse, Schott unbelastet) | `mechanik` |
| PA-2 | Sicherheitsprüfung des Adapters (R2-A2 einteilig, R2-L02 Einzelfehler Kap. 2.3) | `sicherheit` |
| PA-3 | 20 × Flashen bei 57600 und 19200 Baud, Flanke an U4 messen (Kap. 5) | PROTOTYP-PRÜFUNG |
| PA-4 | VDDS am Sensor während Chip-Erase messen (Erwartung ≥ 1.95 V) | PROTOTYP-PRÜFUNG |
| PA-5 | Bezug Waveshare-Board mit Versand in die Schweiz (FW-T3) | Auftraggeber |
