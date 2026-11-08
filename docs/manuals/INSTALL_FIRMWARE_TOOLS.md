# fluidi – Firmware-Werkzeuge installieren (WSL2 Ubuntu 24.04 + Windows)

| | |
|---|---|
| Dokument | `docs/manuals/INSTALL_FIRMWARE_TOOLS.md` |
| Version | 1.2 (Phase 4; 1.1: Gateway = Pi Zero 2 W nach D-014, Flasher `scripts/flash_sensor.py`, Programmieren → `PROGRAMMIEREN_SENSOR.md`; 1.2: PL2303-Board als Alternative, Elektronik) |
| Datum | 2026-11-07, nachgeführt 2026-11-08 und 2026-11-09 |
| Skript | `scripts/install_firmware_tools.sh` (installiert), `scripts/toolcheck.sh` (prüft nur) |
| Ersteller | Firmware/Energie |

Alle Download-Adressen wurden am **2026-11-07** per HTTP-HEAD geprüft (Antwort 200, Datei statt
Login-Seite). Die SHA-256-Prüfsummen der TI-Dateien stammen von den TI-Downloadseiten (gleicher Tag)
und stehen im Skript. Installiert wurde beim Erstellen **nichts**.

---

## 1 Überblick

| Was | Wofür | Wo | Download | Platz installiert (ANNAHME, ausser markiert) |
|---|---|---|---|---|
| TI SimpleLink Low Power F3 SDK **9.23.00.27** (Linux-ZIP) | BLE-Stack, Treiber, MCUboot, Beispiele für CC2340R52 | `~/fluidi-tools/ti/simplelink_lowpower_f3_sdk_9_23_00_27` | 903 MB (gemessen, Content-Length) | ≈ 3–4 GB inkl. gebauter Bibliotheken |
| TI Arm Clang **4.0.4.LTS** | Compiler (der einzige für den BLE-Stack unter Linux, Kap. 2) | `~/fluidi-tools/ti/ti-cgt-armllvm_4.0.4.LTS` | 241 MB (gemessen) | ≈ 1 GB |
| TI SysConfig **1.28.2** | erzeugt Treiber-/Stack-Konfiguration aus `.syscfg` (Pflicht im SDK-Build) | `~/fluidi-tools/ti/sysconfig_1.28.2` | 168 MB (gemessen) | ≈ 0.5 GB |
| Python-venv: **imgtool** (aus dem SDK), **pyserial 3.5**, intelhex 2.3.0 | MCUboot-Signatur, Flashen mit `scripts/flash_sensor.py` über den ROM-UART-Bootloader | `~/fluidi-tools/venv` | ≈ 20 MB | ≈ 0.1 GB |
| ~~ESP-IDF v6.1 + Werkzeuge esp32s3~~ **veraltet** (D-014: Gateway = Raspberry Pi Zero 2 W, Python) | früher Gateway XIAO ESP32-S3 Plus; nicht mehr nötig, `all` installiert es nicht mehr | `~/esp/esp-idf`, `~/esp/.espressif` | Repo ≈ 0.5 GB + Submodule, Werkzeuge 0.65 GB (aus `tools/tools.json` v6.1) | ≈ 4–5 GB |
| apt-Pakete (cmake, ninja, gcc, picocom …) | Build-Werkzeuge, serielles Terminal | System (sudo) | ≈ 0.2 GB | ≈ 0.6 GB |
| optional: TI CC2340 Linux SBL (C-Quelltext) | Referenz für den eigenen Flasher | `~/fluidi-tools/ti/TI_CC2340_Linux_SBL` | < 1 MB | – |
| Windows: **usbipd-win 5.3.0** | USB-Seriell-Adapter an WSL durchreichen | Windows | 5 MB | – |

**Speicherbedarf gesamt ≈ 10–12 GB** (Stand 1.0 mit ESP-IDF; ohne ESP-IDF ≈ 5–7 GB, **ANNAHME**) (+ 1.3 GB Downloads in `~/fluidi-tools/downloads`, nach
erfolgreicher Installation löschbar). Das Skript verlangt **≥ 15 GB frei** im Home.
**Dauer ≈ 45–90 min** (ANNAHME): Downloads ≈ 2.5 GB (bei 100 Mbit/s ≈ 5 min), ESP-IDF-Klon und
`install.sh` ≈ 10–20 min, Bau der SDK-Bibliotheken 15–60 min (läuft ohne Eingaben).

**Login-Pflicht: keine.** TI-SDK, Compiler und SysConfig liegen auf `dr-download.ti.com` ohne
Anmeldung (Prüfung siehe oben). Falls TI das ändert, lädt man die Datei im Browser (Kap. 6).

---

## 2 Begründung der Auswahl

| Punkt | Entscheid | Beleg |
|---|---|---|
| SDK-Version | 9.23.00.27 = aktuell (Release 2026-10-09); unterstützt **CC2340R5RGE** (QFN24, OPN CC2340R52E0RGER), Migration von LP-EM-CC2340R5 per SysConfig | Release Notes 9.23.00.27, „Device Support“ (`release_notes_simplelink_lowpower_f3_sdk_9_23_00_27.html` im SDK); ti.com/tool/download/SIMPLELINK-LOWPOWER-F3-SDK |
| Bezugsquelle SDK | **ZIP von ti.com**, nicht GitHub: Das GitHub-Repo `TexasInstruments/simplelink-lowpower-f3-sdk` (Tag `lpf3-9.23.00.27`) enthält **keine Beispiele und keine Doku**; die BLE-Beispiel-Repos enthalten für LPF3 keine CC2340-Boards (geprüft per GitHub-API 2026-11-07). Wir brauchen die Beispiele `basic_ble` und `mcuboot` als Vorlage | README des Repos, Abschnitt „About this Repository“ |
| Compiler | **TI Arm Clang 4.0.4.LTS**, die vom SDK getestete Version. **GCC scheidet für den Sensor aus:** Die BLE-Stack-Bibliotheken liegen nur für `ticlang` und `iar` vor (`source/ti/ble/lib/CC2340R5/{OneLib,StackWrapper,ControllerLib}/lib/{ticlang,iar}`), nicht für `gcc`. IAR ist kostenpflichtig | Release Notes „Dependencies“: TI ARM Clang 4.0.4.LTS, GCC 12.3.Rel1-0 (nur Nicht-BLE-Teile); SDK-Baum per GitHub-API |
| SysConfig | nötig: Alle SDK-Beispiele erzeugen Treiber-, BLE- und MCUboot-Konfiguration aus `.syscfg`. SDK verlangt **≥ 1.26.4** (`.metadata/product.json`, `minToolVersion`); auf ti.com ist nur noch **1.28.2** ladbar → neuere Version, laut TI „often compatible“ (**ANNAHME**, Build-Test entscheidet) | SDK-README „Build Examples“; ti.com/tool/download/SYSCONFIG |
| Build-System | GNU make (SDK-Makefiles je Beispiel, `imports.mak` im SDK-Wurzelordner), CMake für SDK-Bibliotheken | SDK-README „Setup Instructions“ |
| MCUboot / Signatur | MCUboot liegt im SDK (`source/third_party/mcuboot`, Beispiel `source/ti/common/mcuboot`), **imgtool 2.2.0rc1** im SDK → genau diese Version wird ins venv installiert (PyPI hätte 2.5.0) | `source/third_party/mcuboot/scripts/imgtool/__init__.py` |
| Flashen über ROM-UART-Bootloader | **Eigenes Python-Skript `scripts/flash_sensor.py`** (vorhanden, Tests `scripts/test_flash_sensor.py`; der frühere Arbeitsname `cc23_bsl.py` ist **veraltet**) nach TRM Kap. 8.5: Autobaud 0x55 0x55 → ACK 0x00 0xCC; Befehle PING 0x20, GET_STATUS 0x21, GET_PART_ID 0x22, RESET 0x23, CHIP_ERASE 0x24, CRC32 0x25, DOWNLOAD 0x26, DOWNLOAD_CRC 0x27, SEND_DATA 0x28; 8N1; RX = DIO20, TX = DIO6 | `TI_CC23xx_TechnicalReferenceManual_SWCU193A.pdf` S. 464–467, Tab. 8-38/8-39/8-40 |
| Warum nicht TI-Werkzeuge? | **UniFlash** 9.5 programmiert den CC2340 über XDS110/SWD; ein reiner UART-Weg ist laut TI-Forum nicht vorgesehen (Sekundärquelle) – wir haben keine SWD-Pads (E3). Der **TI Linux-SBL** (C, BSD-Lizenz) setzt die Baudrate fest auf **1 152 000** (`Source/Linux_Serial.c`, Aufruf `setBaudRate(B_1152000)` Z. 148) und nimmt nur `.bin`. Über 2 × 100 kΩ je Leitung sind nur ≤ 57 600 Baud sicher (`CONCEPTS.md` 2.7) → nur als Referenz (Teil `sbl`) | github.com/TexasInstruments-Sandbox/ble_examples, Branch `simplelink_low_power_f3_sdk-7.40`, `tools/TI_CC2340_Linux_SBL` |
| ESP-IDF (**veraltet**, D-014) | **v6.1** = neueste stabile Version (GitHub-Release 2026-08-27; danach nur v6.0.3/v5.x-Wartung). Installation „legacy“ mit `git clone` + `install.sh` **ohne sudo** im Home; der neue Installer EIM nutzt eine apt-Quelle mit `[trusted=yes]` (ohne Signaturprüfung) → nicht verwendet | docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/linux-macos-setup-legacy.html |
| esptool (**veraltet**, D-014) | kommt mit ESP-IDF (in dessen Python-Umgebung); PyPI aktuell 5.6.0 | pypi.org/project/esptool |
| usbipd-win | 5.3.0 (aktuelles Release), winget-Paket `dorssel.usbipd-win`; WSL-Kernel hier 6.18.54.1 ≥ 5.10.60.1, Treiber `cdc_acm`, `ch341`, `cp210x`, `ftdi_sio` als Module vorhanden (geprüft mit `/proc/config.gz`) | learn.microsoft.com/de-de/windows/wsl/connect-usb |

---

## 3 Schritt für Schritt – WSL (Ubuntu)

Voraussetzung: Ubuntu-Terminal, Repo unter `~/git/Tr-pfli`. Das Skript **nicht** mit `sudo` starten;
es fragt selbst einmal nach dem sudo-Passwort (nur für apt und die Gruppe `dialout`).

1. **Alles in einem Durchgang** (empfohlen):
   ```bash
   cd ~/git/Tr-pfli
   bash scripts/install_firmware_tools.sh
   ```
   Ablauf (`all`): apt-Pakete → TI-Downloads mit Prüfsumme → TI Arm Clang und SysConfig unbeaufsichtigt
   installieren → SDK entpacken, `imports.mak` auf die eigenen Pfade setzen (Original bleibt als
   `imports.mak.orig`) → Python-venv → Versionscheck. SDK-Bibliotheken (`sdklibs`) bei Bedarf separat.
   ESP-IDF gehört seit D-014 nicht mehr dazu.
2. Alternativ in Teilen (jeder Teil ist wiederholbar und überspringt Erledigtes):
   ```bash
   bash scripts/install_firmware_tools.sh apt      # sudo: Pakete + Gruppe dialout
   bash scripts/install_firmware_tools.sh ti       # TI-SDK, Compiler, SysConfig
   bash scripts/install_firmware_tools.sh py       # imgtool, pyserial (nach 'ti')
   bash scripts/install_firmware_tools.sh sdklibs  # SDK-Bibliotheken bauen (lange)
   bash scripts/install_firmware_tools.sh esp      # VERALTET (D-014): ESP-IDF v6.1, nur noch auf ausdrücklichen Wunsch
   bash scripts/install_firmware_tools.sh sbl      # optional: TI-Referenz-Flasher
   bash scripts/install_firmware_tools.sh check    # nur prüfen
   ```
3. **WSL neu starten**, damit die Gruppe `dialout` wirkt: in Windows-PowerShell `wsl --shutdown`,
   dann Ubuntu wieder öffnen.
4. Kontrolle: `bash scripts/toolcheck.sh` (Abschnitt „Firmware-Werkzeuge“ – alle Zeilen `[OK]`,
   ausser „serieller Port“, der erst mit angestecktem Adapter erscheint).
5. Umgebung in jeder neuen Shell: `source ~/fluidi-tools/env.sh` (setzt `FLUIDI_TI_SDK`,
   `FLUIDI_TICLANG`, `FLUIDI_SYSCONFIG`, PATH mit `tiarmclang`, `imgtool`). `fluidi_idf` (ESP-IDF) ist
   **veraltet** (D-014).

Hinweis: Die TI-Installer laufen mit `--mode unattended --prefix ~/fluidi-tools/ti`. Hängt einer
(bei älteren TI-Installern beobachtet, Sekundärquelle), Abbruch mit Ctrl-C und interaktiv starten:
`~/fluidi-tools/downloads/<datei> --prefix ~/fluidi-tools/ti`.

---

## 4 Schritt für Schritt – Windows (USB an WSL durchreichen)

Nur nötig, sobald der USB-UART-Adapter (CH343 oder PL2303) am PC hängt. Das Gateway (Pi Zero 2 W) wird nicht per USB geflasht
(`docs/manuals/GATEWAY_SETUP.md`).

1. **usbipd-win installieren** (PowerShell, einmalig):
   ```powershell
   winget install --interactive --exact dorssel.usbipd-win
   ```
   (`--interactive`, sonst startet winget den PC eventuell ohne Rückfrage neu.) Alternativ das MSI
   `usbipd-win_5.3.0_x64.msi` von github.com/dorssel/usbipd-win/releases.
2. Adapter einstecken, Ubuntu-Fenster offen halten. **PowerShell als Administrator**:
   ```powershell
   usbipd list                      # BUSID des Adapters suchen (z. B. 2-3, "USB-SERIAL CH343")
   usbipd bind --busid 2-3          # einmalig je Gerät/Anschluss (Admin)
   ```
3. Anhängen (normale PowerShell genügt):
   ```powershell
   usbipd attach --wsl --busid 2-3
   ```
   Meldet sich das Board neu an (z. B. nach einem Spannungseinbruch an VIO), hilft
   `usbipd attach --wsl --busid 2-3 --auto-attach` in einem eigenen Fenster.
4. In Ubuntu: `lsusb` und `ls /dev/ttyACM* /dev/ttyUSB*`. Der CH343 erscheint als
   `/dev/ttyACM0` (Treiber `cdc_acm`), CH340/CP210x/FTDI und das **PL2303-Board** (VID/PID 067B:23A3, Treiber
   `pl2303`, im WSL-Kernel 6.18.54.1 enthalten, geprüft 2026-11-09) als `/dev/ttyUSB0`.
5. Lösen: `usbipd detach --busid 2-3` oder Kabel ziehen. Solange das Gerät an WSL hängt, sieht
   Windows es nicht. `detach` schaltet die USB-Speisung nicht ab. **PL2303-Board:** Kabel erst ziehen, wenn VCCIO
   spannungslos ist (Netzteil aus bzw. Dummy-Zelle heraus, `hardware/programmer/README.md` Kap. 9.4).
6. Test: `picocom -b 115200 /dev/ttyACM0` (Beenden: Ctrl-A, Ctrl-X).

Rückfall, falls usbipd nicht will: `scripts/flash_sensor.py` läuft auch unter Windows-Python oder auf dem
Raspberry Pi (pyserial + intelhex, `docs/manuals/PROGRAMMIEREN_SENSOR.md` Kap. 3).

---

## 5 Benötigte Hardware zum Programmieren

**Verbindlicher Ablauf: `docs/manuals/PROGRAMMIEREN_SENSOR.md`** (Weg A Programmieradapter, Weg B Behelf am offenen
Board, Bootloader-Falle W-10). Adapter: `hardware/programmer/README.md`.

| Teil | Zweck | Bezug / Preis (Abruf 2026-11-07) | Status |
|---|---|---|---|
| **USB-UART mit externem VIO**: Waveshare **CH343 USB UART Board** (CH343G, Micro/Mini/Type-A/Type-C, SKU 21440–21443), Jumper H3 entfernt, **oder** Waveshare **PL2303 USB UART Board (type A) V2** (PL2303GS), Jumper J1 entfernt | Sensor über ROM-UART-Bootloader flashen, Log lesen | CH343: waveshare.com **USD 3.49** (Micro, SKU 21441); eckstein-shop.de **EUR 4.15** (Type-C, „ca. 3 Wochen“); kein CH-Händler, Auslandsversand nicht ablesbar (**ANNAHME** 10–25 CHF). PL2303: pi-shop.ch Art. 11757, **CHF 8.90**, Sofort-Versand (Abruf 2026-11-09), ohne Zusatzversand mit den Gateway-Teilen | PL2303 **elektrisch freigegeben mit Bedingungen B1–B6** (Elektronik 2026-11-09, `hardware/programmer/README.md` Kap. 9); Bezug Auftraggeber |
| Programmieradapter Rev 1 (Dummy-Zelle 2.0 V, Federstifte TP1/TP2, Schmitt-Puffer SN74AUP1G17 am TX-Stift) | speist den Sensor statt der Zelle (R2-A2), Pegelanpassung TX | `hardware/programmer/README.md` Kap. 6: ≈ CHF 25–55 | Schaltplan Rev 1 (ERC 0), Mechanik offen (PA-1) |
| Behelf (nur Muster vor dem Verguss): Labornetzteil 2.0 V/10 mA (höchstens 20 mA; mit PL2303 höchstens 2.1 V), RXD des USB-UART an **R9 Pad 1** | erste Muster ohne Adapter | Werkstatt | `PROGRAMMIEREN_SENSOR.md` Kap. 5 |
| ~~USB-C-Datenkabel für Gateway XIAO ESP32-S3 Plus~~ | **veraltet** (D-014: Gateway = Pi Zero 2 W) | – | – |

**Pegel 2.0 V statt 1.8 V:** VIO des CH343 1.7–5.5 V (`docs/datasheets/WCH_CH343_Datasheet_V1E.pdf` S. 8 Tab. 6.2),
kein Rückstrom aus VIO (S. 4 Kap. 5.2). Bei 1.8 V blieben am Sensor nur 40–70 mV Reserve zu VDDS min 1.71 V (Red-Team
W-4); der Adapter speist 1.960–2.040 V (XC6206P202). VIO kommt immer aus derselben 2.0-V-Speisung wie der Sensor.

**Pull-up des CH343 (Befund aus 1.0, jetzt gelöst):** RXD hat 3–21 µA Pull-up bei VIO 1.8 V, VIL ≤ 0.5 V (S. 8), und
das Waveshare-Board hängt zusätzlich eine LED mit 2 kΩ an RXD. Über die 2 × 100 kΩ des Sensors entsteht kein Low
(SPICE `simulation/spice/programmer/prog_uart_report.txt`, Fall A0: 0.64 V bis fast VIO). Der Programmieradapter
puffert TX direkt am Federstift (Fall A1: Low ≤ 0.37 V, Schwelle ≥ 0.47 V); im Behelf wird RXD vor den Widerständen an
DIO6 (R9 Pad 1) angeschlossen (Fall A2: 0.25 V bei 2.0 V). **PROTOTYP-PRÜFUNG:** 20 × Flashen bei 57600 und 19200 Baud.

**PL2303-Board (Alternative, Prüfung 2026-11-09):** VDD_IO 1.8 V … VIN + 0.3 V, abs. max ebenso
(`docs/datasheets/Prolific_PL2303GS_Datasheet_Rev1.0.4.pdf` S. 39 Tab. 11-1/11-2a), VIL ≤ 0.4 V, VOL/VOH ohne
Strom-Testbedingung (Tab. 11-2b), RXD-Pull-up ohne Wert (S. 13), RXD-/TXD-LED je 1 kΩ an VCCIO (Board-Schaltplan).
SPICE `simulation/spice/programmer/prog_uart_pl2303.py`: Puffer → RXD 0.06–0.09 V (Grenze 0.40 V); Weg B an R9 Pad 1
0.27–0.29 V bei 2.0 V, bei 2.2 V nur +1 mV Reserve → Weg B **höchstens 2.1 V**; ohne Puffer kein Low (wie CH343).
Freigabe mit Bedingungen: Eingangsprüfung des Boards (VCCIO offen ≤ 0.10 V, RXD → GND ≤ 0.69 mA, TXD high ≥ 1.90 V,
TXD low ≤ 0.10 V), **VCCIO nie ohne gesteckte USB** (Weg B: USB zuerst ein, zuletzt aus; Weg A: Dummy-Zelle vor dem
Ziehen der USB heraus), Port `/dev/ttyUSB0`. Einzelheiten `hardware/programmer/README.md` Kap. 9.

Nicht nötig: TI-LaunchPad oder XDS110 (keine SWD-Pads, E3), ARM-GCC, IAR, CCS, UniFlash, ESP-IDF.
Optional für frühe Entwicklung ohne eigene Platine wäre ein LaunchPad LP-EM-CC2340R5 (Preis nicht
geprüft, > 10 CHF) – nur nach Freigabe.

---

## 6 Falls ein Download eine Anmeldung verlangt

Das Skript bricht mit „Prüfsumme falsch“ ab, wenn statt der Datei eine HTML-Seite kommt. Dann:

1. Im Windows-Browser die Seite öffnen und die **Linux-Datei** laden:
   - SDK: https://www.ti.com/tool/download/SIMPLELINK-LOWPOWER-F3-SDK/9.23.00.27 →
     `simplelink_lowpower_f3_sdk_9_23_00_27__linux.zip`
   - Compiler: https://www.ti.com/tool/download/ARM-CGT-CLANG/4.0.4.LTS →
     `ti_cgt_armllvm_4.0.4.LTS_linux-x64_installer.bin`
   - SysConfig: https://www.ti.com/tool/download/SYSCONFIG → `sysconfig-1.28.2_4845-setup.run`
2. Datei nach `~/fluidi-tools/downloads/` kopieren, z. B.
   `cp /mnt/c/Users/steph/Downloads/<datei> ~/fluidi-tools/downloads/`
3. Skript erneut starten – es prüft die SHA-256-Summe und macht weiter.

SHA-256 (ti.com, 2026-11-07):

| Datei | SHA-256 |
|---|---|
| simplelink_lowpower_f3_sdk_9_23_00_27__linux.zip | `651ce15880fd1c049b94b24be5738942fbf97a358036f58a856299c3f946733b` |
| ti_cgt_armllvm_4.0.4.LTS_linux-x64_installer.bin | `98c60ecc259a07a54be6fcc0f55990332f493bfe5dad460c0ba83963f5dcb06f` |
| sysconfig-1.28.2_4845-setup.run | `86707095714ba9422a8e1523516fba17bdc3cc96ccc21ddad2deaabdd67b4da6` |

---

## 7 Deinstallation

`rm -rf ~/fluidi-tools ~/esp` entfernt alles ausser den apt-Paketen; die Gruppe `dialout` bleibt
(unschädlich). usbipd-win unter Windows über „Apps“ entfernen.

---

## 8 Offene Punkte

| Nr. | Punkt | Wer |
|---|---|---|
| FW-T1 | Build-Test mit SysConfig 1.28.2 statt 1.26.x (`basic_ble` für CC2340R5, ticlang) nach der Installation | Firmware |
| FW-T2 | ~~Puffer am TX-Federstift~~ **entworfen** 2026-11-08: `hardware/programmer` (SN74AUP1G17, 2.0 V, VIO aus eigenem 2.0-V-Regler); Mechanik und Sicherheitsprüfung offen | Elektronik, Mechanik, Sicherheit |
| FW-T3 | Bezug CH343-Board mit Versand in die Schweiz ≤ 10 CHF bestätigen. **Stand 2026-11-09:** CH343 nur aus dem Ausland (Versand nicht belegt); **PL2303-Board (pi-shop.ch, 8.90 CHF) von der Elektronik freigegeben mit Bedingungen B1–B6** (SPICE `prog_uart_pl2303.py`, J1-Belegung, Eingangsprüfung, Reihenfolge USB/VCCIO; `hardware/programmer/README.md` Kap. 9). Offen: Kaufentscheid; Entladewiderstand 470 Ω an VIO (PA-6) | Auftraggeber (Kauf), Orchestrator (PA-6) |
| FW-T4 | ~~`scripts/cc23_bsl.py`~~ **erledigt** als `scripts/flash_sensor.py` (Baudrate ≤ 57 600, `--sim`, `--dry-run`, `--lock`) | Firmware |

## Quellen (Abruf 2026-11-07)
- TI F3 SDK Download: https://www.ti.com/tool/download/SIMPLELINK-LOWPOWER-F3-SDK ; GitHub: https://github.com/TexasInstruments/simplelink-lowpower-f3-sdk (Tag `lpf3-9.23.00.27`, README, `imports.mak`, Release Notes, `.metadata/product.json`)
- TI Arm Clang: https://www.ti.com/tool/download/ARM-CGT-CLANG/4.0.4.LTS
- SysConfig: https://www.ti.com/tool/download/SYSCONFIG
- TI Linux SBL: https://github.com/TexasInstruments-Sandbox/ble_examples/tree/simplelink_low_power_f3_sdk-7.40/tools/TI_CC2340_Linux_SBL ; Hinweise im TI-Forum: https://e2e.ti.com/support/wireless-connectivity/bluetooth-group/bluetooth/f/bluetooth-forum/1539273/lp-em-cc2340r53-programming-cc2340r53-via-serial-bootloader
- ESP-IDF v6.1 Linux (legacy): https://docs.espressif.com/projects/esp-idf/en/v6.1/esp32s3/get-started/linux-macos-setup-legacy.html ; Releases: https://github.com/espressif/esp-idf/releases
- usbipd-win / WSL USB: https://learn.microsoft.com/de-de/windows/wsl/connect-usb ; https://github.com/dorssel/usbipd-win/releases
- Waveshare CH343: https://www.waveshare.com/wiki/CH343_USB_UART_Board_(micro) ; https://www.waveshare.com/ch343-usb-uart-board.htm?sku=21441 ; https://eckstein-shop.de/WaveShare-USB-C-To-UART-Module-High-Baud-Rate-Transmission-EN
- pi-shop.ch Suche „usb ttl“: https://www.pi-shop.ch/catalogsearch/result/?q=usb+ttl
- Lokal: `docs/datasheets/TI_CC23xx_TechnicalReferenceManual_SWCU193A.pdf` S. 464–467; `docs/datasheets/WCH_CH343_Datasheet_V1E.pdf` S. 4, 8
