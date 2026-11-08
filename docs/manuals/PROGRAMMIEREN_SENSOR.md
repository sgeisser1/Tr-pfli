# fluidi – Sensor programmieren (Erstprogrammierung über den ROM-UART-Bootloader)

| | |
|---|---|
| Dokument | `docs/manuals/PROGRAMMIEREN_SENSOR.md` |
| Version | 1.1, 2026-11-08 (Elektronik; Red-Team B-4 / W-4 / W-10; 1.1: Veto PS-K1, Weg B nur mit Dummy-Scheibe) |
| Gilt für | Sensor Rev C (`hardware/sensor/`), Firmware `firmware/sensor` (Werks-Hex), Werkzeug `scripts/flash_sensor.py` |
| Adapter | `hardware/programmer/README.md` (Programmieradapter Rev 1: Dummy-Zelle 2.0 V + TX-Puffer) |
| Ersetzt | `docs/manuals/INSTALL_FIRMWARE_TOOLS.md` Kap. 5 (dort: XIAO-Gateway und `cc23_bsl.py`, beides veraltet) |

Es gibt zwei Wege. **Weg A** (Programmieradapter) ist der Normalfall und funktioniert auch am fertig vergossenen
Sensor, solange das Zellfach offen ist. **Weg B** (Behelf) ist nur für die ersten Muster gedacht, solange der Adapter
fehlt: am **offenen Board vor dem Verguss**, mit Labornetzteil und gelöteten Drähten.

## 1 Sicherheitsregeln (CONCEPTS 2.7, Auflagen R2-A2/R2-A3)

1. **Nie mit eingesetzter Zelle programmieren.** Speisung **nur über die Dummy-Zelle bzw. Dummy-Scheibe im Clip**
   (Weg A und Weg B). Die Scheibe belegt den Clip, so dass keine Zelle parallel zum Netzteil eingesetzt werden kann
   (Veto PS-K1, `docs/reviews/phase5_programmer_sicherheit.md`). Keine Prüfklemme am Clip, kein Draht am Minuspad,
   keine Speisung über TP1/TP2. Einzige Ausnahme: Sicherheitstest PT11.06/ST-Z5 nach den Bedingungen Z5-1…Z5-7
   (`docs/reviews/phase5_sicherheit_runde3.md`, Entscheid WS-13).
2. Labornetzteil (Weg B): **2.0 V** (höchstens 2.2 V), Strombegrenzung **10 mA** (höchstens 20 mA, EP-03), Polarität vor dem Anschliessen messen.
3. Der CH343 bekommt seine I/O-Spannung (VIO) immer aus **derselben 2.0-V-Speisung** (Weg A: Adapter-Regler U3,
   Weg B: dasselbe Labornetzteil). **Jumper H3** auf dem Waveshare-Board **abziehen**. Mit 3.3-V- oder 5-V-Pegeln wird
   das Low am Sensor-RX nicht sicher erkannt, und die Pins würden über VDDS + 0.3 V betrieben
   (`TI_CC2340R5_Datasheet_SWRS272F.pdf` S. 18 Tab. 7.1).
4. Weg B überbrückt auf dem TX-Pfad die 2 × 100 kΩ (Barriere 2). Das ist nur ohne Zelle zulässig. Der Draht wird vor
   dem Einsetzen einer Zelle und vor dem Verguss **entfernt** (Kap. 5, Schritt 9).

## 2 Was man braucht

| Teil | Weg A | Weg B | Hinweis |
|---|---|---|---|
| PC (Windows mit WSL2) **oder** Raspberry Pi (z. B. das Gateway Pi Zero 2 W, D-014) | ✓ | ✓ | Kap. 3 |
| Waveshare CH343 USB UART Board, Jumper H3 abgezogen | ✓ | ✓ | `WCH_CH343_Datasheet_V1E.pdf`; Belegung `docs/references/Waveshare_CH343-USB-UART-Board_Schematic_2026-11-08.pdf` |
| Programmieradapter Rev 1 (Dummy-Zelle + Federstiftkopf + Puffer) | ✓ | – | `hardware/programmer/README.md` |
| Labornetzteil mit Strombegrenzung, Kupferlackdraht 0.1–0.2 mm, Lötstation mit feiner Spitze, Lupe/Mikroskop, Isopropanol | – | ✓ | |
| Dummy-Scheibe (nur die Dummy-Zelle des Adapters, ohne Federstiftkopf; Dicke 3.0–3.2 mm, PS-W3) | – | **Pflicht** | Kap. 5 Schritt 2 (Veto PS-K1) |
| Werks-Hex `firmware/sensor/build/fluidi-sensor-factory-<ver>-key<fp>.hex` | ✓ | ✓ | erzeugt mit `make` in `firmware/sensor` (`firmware/sensor/README.md`) |

## 3 Software vorbereiten

`scripts/flash_sensor.py` braucht Python 3 mit **pyserial** und **intelhex** (für `--lock` zusätzlich *cryptography*).

**PC mit WSL2:** Die Firmware-Umgebung bringt alles mit (`scripts/install_firmware_tools.sh py`, venv
`~/fluidi-tools/venv`: pyserial 3.5, intelhex 2.3.0). Den CH343 nach `docs/manuals/INSTALL_FIRMWARE_TOOLS.md` Kap. 4
mit `usbipd` an WSL durchreichen; er erscheint als `/dev/ttyACM0`.

```bash
source ~/fluidi-tools/env.sh
cd ~/git/Tr-pfli
python scripts/test_flash_sensor.py               # 17 Tests, alle OK
HEX=$(ls firmware/sensor/build/fluidi-sensor-factory-*.hex)
python scripts/flash_sensor.py program --hex "$HEX" --sim --yes     # Probelauf ohne Hardware
```

**Raspberry Pi:** CH343-Board am USB-Datenanschluss (Pi Zero 2 W: Buchse „USB“, mit OTG-Adapter). Treiber `cdc_acm`
ist im Raspberry-Pi-OS-Kernel enthalten (**ANNAHME**, mit `ls /dev/ttyACM*` prüfen).

```bash
python3 -m venv ~/fluidi-flash && ~/fluidi-flash/bin/pip install pyserial intelhex
# flash_sensor.py und das Werks-Hex vom PC kopieren, z. B.:
scp scripts/flash_sensor.py firmware/sensor/build/fluidi-sensor-factory-*.hex pi@fluidi.local:~/
~/fluidi-flash/bin/python ~/flash_sensor.py info --port /dev/ttyACM0
```

Baudrate: Standard **57600** (Maximum, das Werkzeug erzwingt es), Rückfall `--baud 19200`. Der Bootloader erkennt die
Baudrate selbst (Autobaud 9600 bis 1.6 MBaud, TRM `SWCU193A` S. 461/464). Dauer für das aktuelle Werks-Hex
(≈ 250 kB Hauptflash + 2 kB CCFG): ≈ 1 min bei 57600, ≈ 2–3 min bei 19200 (**ANNAHME**, abhängig von der USB-Latenz).

## 4 Weg A: mit Programmieradapter (Normalfall)

1. Adapter prüfen (einmal je Sitzung): USB einstecken, **VDD_DUT und VIO = 1.96–2.04 V** messen
   (`hardware/programmer/README.md` Kap. 7).
2. Sensor: Hülse abziehen, Fachdeckel öffnen, **Zelle entnehmen**. Kontrolle: Clip leer.
3. **Taster drücken und gedrückt halten**, Dummy-Zelle von der offenen Clip-Seite (+X) einschieben, Federstifte auf
   TP1/TP2 setzen, Gegenhalter unter die Platinenkante. Nach ≈ 1 s den **Taster loslassen**. (Der Bootloader prüft den
   Taster nur beim Start, TRM S. 465. Ein leerer Chip startet den Bootloader auch ohne Taster, TRM S. 461.)
4. Verbindung prüfen:
   ```bash
   python scripts/flash_sensor.py info --port /dev/ttyACM0
   ```
   Erwartet: `[info] Bootloader antwortet, Part-ID …`. Sonst Kap. 7.
5. Programmieren (Muster: DEV-Schlüssel, **ohne** `--lock`):
   ```bash
   python scripts/flash_sensor.py program --hex "$HEX" --port /dev/ttyACM0
   ```
   Sicherheitsabfrage mit `ja` bestätigen. Ablauf: Sync → Chip-Erase → Hauptflash in Bereichen mit CRC32-Prüfung → CCFG
   → Reset. Am Schluss: `CCFG geschrieben und verifiziert` und `Reset – Sensor startet die Anwendung`.
6. Bei 2.0 V leuchten die LEDs kaum (VF ≥ 1.8/2.5/2.6 V bei 5 mA, `TUOZHAN_…_Datasheet_A0.pdf` S. 5), und die Firmware
   schaltet unter 2.4 V ab (PINMAP FW-5). **Kein Startsignal zu sehen ist hier normal.** Die Prüfung erfolgt mit der Zelle.
7. Dummy-Zelle herausziehen. **Zelle einsetzen, ohne den Taster zu berühren.** Erwartet: L11-Startsignal
   (Selbsttest ok: Grün 200 ms; Fehler: Rot 3 × 100 ms; danach ungekoppelt Gelb 2 × 50 ms, `firmware/PROTOCOL.md`
   Kap. 10.2, Muster L11) und Advertising als `fluidi-XXXX` (Gateway-Kopplung bzw. App).
8. Optional: `python scripts/flash_sensor.py verify --hex "$HEX" --port /dev/ttyACM0` (vorher wieder Schritt 2–3).

**Serie** (nicht für die Muster): `program --lock --expect-key-fp <fp>` mit dem Produktionsschlüssel sperrt Bootloader
und SWD dauerhaft (`firmware/sensor/README.md`). Danach ist Weg A nicht mehr möglich, nur noch OTA.

## 5 Weg B: Behelf am offenen Board (nur Muster, vor dem Verguss)

**Welches Pad?** Der CH343-RXD muss an den Knoten **LED_R_UART_TX = DIO6** (U1 Pin 19), also **vor** die 100 kΩ.
Das ist **R9 Pad 1** (KiCad x 149.29, y 41.95; Mechanik X −0.71, Y 11.95; 0402, 0.54 × 0.64 mm). R9 sitzt waagrecht
unterhalb der RGB-LED D1; Pad 1 ist das **linke** Pad (F-Seite, Antenne oben), Pad 2 (rechts, Richtung U1) ist
`UART_TX_MID` hinter den ersten 100 kΩ und **falsch**. Gleiches Netz wie Pad 1 hat auch **R6 Pad 1** (KiCad 151.78 /
38.99, oberes Pad von R6 rechts neben D1) als Ausweichpunkt. Lageplan: `hardware/programmer/out/behelf_lageplan.png`
(erzeugt mit `hardware/programmer/gen/behelf_pads.py` direkt aus der Platinendatei).

| Anschluss | Sensor | CH343-Board / Netzteil | Begründung |
|---|---|---|---|
| Speisung + | Dummy-Scheibe im Clip (VBAT, über Q1 auf VDD) | Netzteil + 2.0 V | Speisung wie mit einer Zelle; Q1 bleibt Verpolschutz |
| Speisung − | Dummy-Scheibe auf dem Minuspad (GND) | Netzteil −, CH343 GND (H2.2) | gemeinsame Masse |
| VIO | – | H3 Mittelstift (Jumper weg) an Netzteil + | VIO = VDD, kein Rückspeisen, wenn das Netzteil aus ist |
| Sensor-TX | **R9 Pad 1** (DIO6) | H2.4 **RXD** | direkt, ohne die 200 kΩ |
| Sensor-RX | TP2 (UART_RX_PAD) | H2.3 **TXD** | über die 200 kΩ des Sensors (SPICE B) |

**Warum nicht TP1?** Am TP1 liegen 200 kΩ vor dem CH343-Eingang. Dessen Pull-up (3–21 µA) und die RXD-LED des
Waveshare-Boards (2 kΩ nach VIO) heben das Low auf 0.64 V bis fast VIO (SPICE A0; CH343 VIL ≤ 0.5 V). Am R9 Pad 1 treibt
DIO6 direkt: Low **0.25 V bei 2.0 V**, **0.36 V bei 2.2 V** (SPICE A2, mit Pull-up 30/39 µA und beiden LEDs im
ungünstigsten Fall). Darum gilt für Weg B: **2.0 V einstellen**, 2.2 V ist die Obergrenze (Reserve dann nur 0.14 V am
CH343, 0.13 V am Sensor-RX).

Ablauf:

1. Board liegt offen, Hülse und Verguss fehlen noch, **keine Zelle**.
2. Speisung **nur** mit der **Dummy-Scheibe** des Adapters (`hardware/programmer/README.md` Kap. 4, Dicke 3.0–3.2 mm)
   im Clip und den zwei Litzen ans Netzteil. **Ohne Scheibe kein Weg B** (Veto PS-K1): Eine Prüfklemme am Clip liesse
   den Clip frei, eine Zelle könnte parallel zum Netzteil eingesetzt und geladen werden. Nicht auf dem Minuspad oder
   den gefüllten Via-in-Pad-Flächen im Fach löten (PS-W2).
3. CH343-RXD: Kupferlackdraht 0.1–0.2 mm auf **R9 Pad 1** löten (wenig Zinn, kurz, R9 nicht ablöten), Draht mit
   Kaptonband zugentlasten.
4. CH343-TXD: an TP2 (Ø 1.5 mm) **nur mit Prüfspitze oder Federstift mit flachem/gerundetem Kopf**, nicht löten:
   TP2 ist eine gefüllte Via-in-Pad-Fläche im Fach (PS-W2).
5. Netzteil auf 2.0 V, **10 mA** (höchstens 20 mA) einstellen, **erst dann** anschliessen (PS-L3). VIO am Waveshare-Board messen: 2.0 V.
6. **Taster drücken und halten**, Netzteil einschalten, nach ≈ 1 s loslassen (leerer Chip: Taster unnötig).
7. `flash_sensor.py info …`, dann `program …` wie Weg A Schritt 4–5. Bei Fehlern `--baud 19200`.
8. **Feste Reihenfolge (Veto PS-K1):** (a) Netzteil **aus und abziehen**, (b) **Dummy-Scheibe heraus**,
   (c) Draht an R9 **entfernen**, Prüfspitze von TP2 abnehmen. Erst nach Schritt 9 eine Zelle einsetzen.
9. **Nacharbeit (Pflicht):** Flussmittel mit Isopropanol reinigen, unter der Lupe prüfen: R9 auf beiden Pads gelötet,
   kein Zinn zwischen den Pads oder zu R8/D1, kein Drahtrest. **Foto** von R9/R6/TP2 unter der Lupe ablegen (die
   Widerstandsmessung erkennt einen vergessenen Draht nicht, PS-W4). Kontrollmessung ohne Speisung: TP1 ↔ R9 Pad 1
   ≈ 200 kΩ (R9 + R10). Erst dann Zelle einsetzen (Funktionsprüfung wie Weg A Schritt 7) und vergiessen.
   **Zellen unter 2.6 V** (z. B. nach der Bootloader-Falle, Kap. 6) **nicht wiederverwenden**, sondern entsorgen.

Folgen und Grenzen von Weg B:
- Barriere 2 ist auf dem TX-Pfad während der Programmierung überbrückt; zulässig nur ohne Zelle (Regel 1).
- Thermische Belastung des 0402-Pads; ein abgehobenes Pad zerstört den TX-Pfad (dann R6 Pad 1 nehmen).
- Nach dem Verguss ist Weg B nicht mehr möglich; dann nur noch Weg A über TP1/TP2.

## 6 Achtung: Bootloader-Falle beim Einsetzen der Zelle (W-10)

**Wer beim Einsetzen der Zelle den Taster drückt, startet den ROM-Bootloader statt der Anwendung.** Die Muster-CCFG
erlaubt den Bootloader mit Taster DIO21 low als Auslöser (`firmware/sensor/mcuboot/mcuboot.syscfg` Z. 34–39: bldrEnabled, pinTriggerEnabled, DIO21, LOW; TRM S. 465).
Ein Zeitlimit ist im TRM Kap. 8.5 nicht beschrieben: Der Bootloader wartet, bis die Speisung weg ist. Das passiert
leicht beim Zusammenbau, wenn man beim Hochschieben der Hülse auf die Kappe drückt.

- **Erkennen:** Nach dem Einsetzen kommt **kein L11-Startsignal** (weder Grün 200 ms noch Rot 3 × 100 ms noch Gelb
  2 × 50 ms), der Sensor erscheint nicht als `fluidi-XXXX` und reagiert nicht auf den Taster. Er wirkt tot.
- **Folge:** Die CPU läuft im Bootloader weiter. Strom laut Datenblatt (bei 3.0 V, Kap. 7.9 S. 19–20): Idle 0.8–1.7 mA,
  CPU aktiv 2.6 mA (DCDC) bzw. 4.1 mA (GLDO). Ob der Bootloader zwischen den Flanken schläft, ist nicht dokumentiert;
  **Bereich 0.8–4.1 mA (ANNAHME)**. Eine CR2032 mit 225 mAh (`Panasonic_CR2032_Datasheet_2026-02.pdf` S. 1) ist damit
  nach **≈ 2–12 Tagen leer**. **PROTOTYP-PRÜFUNG:** Strom im Bootloader am Muster messen (Aufbau A/C in
  `docs/manuals/ENERGIEMESSUNG.md`, Taster beim Einschalten gedrückt).
- **Beheben:** Zelle **≥ 10 s** entnehmen, dann **ohne Taster** wieder einsetzen. L11 muss erscheinen. (Der Puffer
  4 × 100 µF muss unter die BOD-Schwelle 1.67 V fallen, DS S. 19; bei ≥ 0.8 mA dauert das < 1 s, 10 s sind Reserve.)
- **Vorbeugen:** Zelle einsetzen und Fach schliessen, **bevor** die Kappe/der Taster berührt wird; nach jedem
  Zusammenbau auf L11 achten. Kommt das Problem ohne Tastendruck, klemmt der Taster (M-4, Hub 0.8 mm): Mechanik prüfen.
- Gleiches gilt nach dem Programmieren: Hält man beim Reset am Ende von `program` den Taster noch, startet wieder der
  Bootloader.
- In der Serie sperrt `--lock` den ROM-Bootloader (pBldrVtor = FORBID, TRM S. 460 Tab. 8-35); die Falle besteht dann nicht.

## 7 Fehlerbilder

| Meldung / Bild | Ursache | Abhilfe |
|---|---|---|
| `Zeitueberschreitung (keine Antwort)` bei `info` | Bootloader nicht aktiv (Taster beim Start nicht gedrückt, Chip schon programmiert) | Speisung weg, Taster halten, neu einschalten |
| `Autobaud: kein ACK` | Störbyte, falscher Pegel, falsches Pad (Weg B: R9 Pad 2!) | VIO = VDD = 2.0 V messen; Pad prüfen; `--baud 19200` |
| `NACK nach 3 Versuchen` / `CRC_FAIL` | Bitfehler auf der Leitung | `--baud 19200`, Federstifte reinigen, Kabel kürzen |
| `/dev/ttyACM0` fehlt | USB nicht an WSL durchgereicht; Board hat sich neu angemeldet | `usbipd attach --wsl --busid …`; VIO-Schiene prüfen (Adapter: U3) |
| Sensor nach Programmierung „tot“ | Bootloader-Falle (Kap. 6) oder Abschaltung < 2.4 V (Kap. 4 Schritt 6) | mit Zelle neu starten, ohne Taster |

## Quellen (lokal)
- `docs/datasheets/TI_CC23xx_TechnicalReferenceManual_SWCU193A.pdf` S. 460 Tab. 8-35, S. 461 Kap. 8.5, S. 464–465 Tab. 8-38
- `docs/datasheets/TI_CC2340R5_Datasheet_SWRS272F.pdf` S. 18 Tab. 7.1/7.3, S. 19 Kap. 7.6, S. 19–20 Kap. 7.9
- `docs/datasheets/WCH_CH343_Datasheet_V1E.pdf` S. 4–5 Kap. 5.2, S. 8 Tab. 6.2
- `docs/references/Waveshare_CH343-USB-UART-Board_Schematic_2026-11-08.pdf`
- `simulation/spice/programmer/prog_uart_report.txt` (Fälle A0, A1, A2, B; Zeitverhalten)
- `hardware/programmer/README.md`, `hardware/programmer/out/behelf_lageplan.png`
