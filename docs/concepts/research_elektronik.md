# Tröpfli – Phase 2: Recherche Sensor-Elektronik

| | |
|---|---|
| Dokument | `docs/concepts/research_elektronik.md` |
| Rolle | Elektronik (`.claude/agents/elektronik.md`) |
| Stand | 2026-11-06, Entwurf zur Prüfung |
| Grundlage | `docs/requirements/REQUIREMENTS.md` v1.0, `CLIENT_INPUT.md` |
| Register | `docs/datasheets/_staging/INDEX_elektronik.csv` (noch nicht in `INDEX.csv` übernommen) |
| Rechnung | `scripts/phase2_salt_loss.py` (Leitfähigkeitsverlust gegen Messfrequenz) |

Dieses Dokument trifft keine Entscheidung. Es liefert belegte Vergleichsdaten für die
Konzeptvarianten und am Schluss eine begründete Empfehlung.

**Zitierweise:** `Datei, S. x` bedeutet die PDF-Seite (Seitenzähler des PDF-Viewers, nicht die
aufgedruckte Seitenzahl). Alle JLC-Daten stammen aus der JLC-API
(`selectSmtComponentList`), Abruf **2026-11-06**. Preise sind JLC-Stückpreise in USD in der
Staffel, die 20 Stück enthält (meist „10+“). Lagerstände ändern sich täglich.

---

## 0 Kurzfazit

1. **Bester Kandidat nach lokal belegten Daten: TI CC2340R52 (QFN24, C20416850).**
   Schlafstrom 0.71–1.15 µA mit RTC und vollem RAM-Erhalt, 1.71–3.8 V, 512 KB Flash,
   **UART-Bootloader im ROM** (USB-UART-Adapter genügt, REQ-FW-06), 1.34 USD, 9278 an Lager.
2. **Günstigste Alternative: WCH CH592F (C39831287)**, 0.67 USD, 27 866 an Lager, Touch-Key-Modul
   für 10–100 pF mit Shield-Ausgang. Aber: Schlafstrom mit BLE-RAM-Erhalt 2.0–2.5 µA typ.
   Mit dem Faktor 1.5 nach REQ-ENE-08 sind das 3.0–3.75 µA, also knapp über REQ-ENE-09 (≤ 3 µA).
   Dazu kommen ein geschlossener BLE-Stack (Binärbibliothek) und ein wenig dokumentierter
   Programmierweg.
3. **Nordic nRF52 und Silicon Labs EFR32BG22** sind bei JLC lieferbar. Die
   **Herstellerdatenblätter ließen sich aber nicht laden** (Cloudflare bzw. HTTP 403). Nach
   Projektregel lassen sie sich deshalb noch nicht empfehlen. Der Auftraggeber müsste sie manuell
   herunterladen.
4. **Messprinzip: externer RC-Oszillator mit Schmitt-Trigger (SN74LVC1G14)**, aus einem GPIO
   gespeist, Frequenz per Timer gezählt, Zielbereich **≈ 5–20 MHz**. Er ist billig (0.06 USD),
   läuft ab 1.65 V und erreicht eine deutlich höhere Messfrequenz als die MCU-internen Verfahren
   oder der FDC1004 (25 kHz). Das ist wichtig für REQ-MES-11 (Salz/Dünger).
   FDC1004/FDC2212 brauchen ≥ 3.0 V bzw. ≥ 2.7 V und passen nicht direkt an eine Knopfzelle.
5. **Bodentemperatur:** digitaler Sensor **TMP1075** (±1 °C max., 0.31 USD) oder **TMP117**
   (±0.3 °C max., 0.91 USD), beide mit lokalem Datenblatt. Ein NTC ist billiger, das
   Murata-Datenblatt ließ sich aber nicht laden, und der geläufige Typ NCP18XH103F03RB ist laut
   Sekundärquellen NRND.
6. Für alle Varianten ist ein **32.768-kHz-Quarz Pflicht**, wegen der Zeitstempel-Genauigkeit
   REQ-SYS-07. Bei JLC gibt es einen **Basic**-Typ (Epson C32346). Die Lastkapazität ist noch
   zu prüfen.

---

## 1 Relevante Anforderungen (Auszug)

| Anforderung | Folge für die Elektronik |
|---|---|
| REQ-ENE-06 Abschaltung 2.0 V unter Last | SoC und Messschaltung müssen bis mindestens 2.0 V sicher arbeiten, mit Reserve gegen Brown-out |
| REQ-ENE-09 [CC] Mittelstrom ≤ 8 µA, Schlaf ≤ 3 µA | Schlafstrom mit RTC und RAM-Erhalt × 1.5 (REQ-ENE-08) muss deutlich unter 3 µA liegen |
| REQ-FW-03 Flash ≥ 2 Abbilder + Puffer | ≥ 512 KB Flash bzw. externer Flash |
| REQ-FW-06 Programmierung ohne teuren Adapter | ROM-Bootloader (UART/USB) oder Adapter ≤ 10 CHF; ohne Ladung der Zelle (REQ-SAF-CC-03) |
| REQ-SYS-07 ±2 min nach 14 d | ±2 min/14 d ≙ **≈ 99 ppm** (Rechnung: 120 s / 1 209 600 s). RC-Oszillatoren reichen nicht, siehe 3.4 |
| REQ-MES-11 Salz ≤ 5 %-Punkte | Messfrequenz möglichst hoch (siehe 6.4) |
| REQ-TMP-01 ±1 °C | Sensor mit garantiertem Maximalfehler ≤ ±1 °C oder kalibrierfähige Kette |
| REQ-RF-04, REQ-MECH-02 | Antenne am oberen Ende, Kopf ≤ 35 × 20 mm, also PCB-Breite ca. 20–25 mm |
| REQ-FAB-02 | Basic Parts bevorzugt. **Alle SoCs, CDCs und Logik-ICs sind Extended.** Basic sind nur Passive und der 32-kHz-Quarz |

---

## 2 JLC-Verfügbarkeit der BLE-SoCs (Abruf 2026-11-06)

| SoC (Bestellnr.) | LCSC | Basic/Ext | Lager | USD @20 | Gehäuse | Bemerkung |
|---|---|---|---|---|---|---|
| **TI CC2340R52E0RGER** | **C20416850** | Ext | 9 278 | 1.34 | VQFN-24 4×4 | 512 KB/36 KB, 12 DIO |
| TI CC2340R52E0RKPR | C5914214 | Ext | 283 | 1.55 | QFN-40 5×5 | 26 DIO, wenig Lager |
| TI CC2340R53E0RKPR | C43088469 | Ext | 85 | 4.30 | VQFN-40 | 64 KB RAM |
| TI CC2340R22E0RKPR | C35938918 | Ext | 10 | 3.53 | QFN-40 | 256 KB Flash, kaum Lager |
| TI CC2340R21N0RGER | C35681563 | Ext | 0 | – | VQFN-24 | 256 KB, kein Lager |
| **WCH CH592F** | **C39831287** | Ext | 27 866 | 0.67 | QFN-28 4×4 | 1.75 V min |
| WCH CH592X | C42442063 | Ext | 2 144 | 0.63 | QFN-32 4×4 | |
| WCH CH592D | C41417128 | Ext | 3 733 | 0.68 | QFN-20 3×3 | |
| WCH CH591F | C42400560 | Ext | 410 | 0.64 | QFN-28 | ohne Touch-Key, 256 KB |
| WCH CH591D | C20606919 | Ext | 5 347 | 0.47 | QFN-20 | **VDD min 2.3 V**, verworfen |
| WCH CH582F | C3001175 | Ext | 1 479 | 0.96 | QFN-28 4×4 | **VDD min 2.3 V**, verworfen |
| Nordic nRF52805-CAAA-R | C1512175 | Ext | 6 089 | 3.09 | WLCSP-28 2.5×2.5 | nur WLCSP |
| Nordic nRF52810-QCAA-R | C519278 | Ext | 2 207 | 3.18 | QFN-32 5×5 | 192 KB Flash (ANNAHME, DS fehlt) |
| Nordic nRF52810-QFAA-R | C141828 | Ext | 34 347 | 4.56 | QFN-48 6×6 | |
| Nordic nRF52832-QFAA-R | C77540 | Ext | 30 111 | 4.61 | QFN-48 6×6 | |
| Nordic nRF52833-QDAA-R | C2895249 | Ext | 18 422 | 5.63 | QFN-40 5×5 | |
| Nordic nRF52820-QDAA-R | C3015612 | Ext | 7 732 | 3.83 | QFN-40 5×5 | |
| Nordic nRF54L05-QFAA-R | C45022042 | Ext | 1 136 | 3.02 | QFN-48 | neue Generation |
| SiLabs EFR32BG22C224F512GM32-C | C1015253 | Ext | 3 880 | 2.02 | QFN-32 4×4 | übrige BG22-Typen < 20 Stk. |
| Phyplus PHY6222 | C2925787 / C2836482 | Ext | 0 | – | QFN-32 | **kein Lager**, verworfen |
| Telink TLSR8250/8253 (Chip) | C2926851 u. a. | Ext | 0 | – | QFN-32 | **kein Lager**; nur Module (Ai-Thinker TB-04, 20 Stk.), verworfen |

Quelle: JLC-API, Rohdaten aus dem Scratchpad der Recherchesitzung. Bei der Bestellung erneut abfragen.

---

## 3 Elektrische Eckdaten der SoCs

### 3.1 Vergleichstabelle (nur lokal belegte Werte)

| Größe | **CC2340R52** | **CH592F** | CH582F | nRF52832 / nRF528xx / BG22 |
|---|---|---|---|---|
| Datenblatt | `TI_CC2340R5_Datasheet_SWRS272F.pdf` | `WCH_CH592_Datasheet_V1.9.pdf` | `WCH_CH583_Datasheet_V1.9.pdf` | **nicht geladen** (siehe 9) |
| Versorgung | 1.71–3.8 V (S.18, Tab. 7.3) | 1.75–3.6 V (S.152, Tab. 20-2) | **2.3**–3.6 V (S.138, Tab. 20-2; 1.75 V nur CH583M) | – |
| DC/DC | ≥ 2.2 V; darunter automatisch GLDO (S.18, Tab. 7.4) | ja, Spule 10 µH (4.7–22 µH) (S.5, Pin VSW) | ja | – |
| Brown-out | 1.67 V fallend (S.19, Tab. 7.6) | LVR 1.3–1.75 V (S.153) | – | – |
| **Schlaf mit RTC und RAM-Erhalt** | **0.71 µA** (LFOSC, DCDC), **0.74 µA** (LFXT, DCDC); 1.1/1.15 µA mit GLDO (S.19–20, Tab. 7.9) | RAM2K+Kern+RTC: 1.1 µA (LSI)/1.3 µA (LSE); RAM24K+Kern+RTC: **2.0 µA (LSI)/2.2 µA (LSE)**; zusätzlich RF-Konfig: 2.3/2.5 µA (S.43, Tab. 5-3) | RAM30K+Kern+RTC 2.1 µA; mit RF 2.4 µA (S.40, Tab. 5-3) | Sekundärquelle: nRF52832 1.9 µA „System ON, RTC“ [W5] |
| Shutdown | 165 nA (S.20) | 0.3–1.3 µA (S.153, Tab. 20-3) | 0.2–2.3 µA | – |
| TX 0 dBm | **5.1 mA** (DCDC), 9.0 mA (ohne DCDC) (S.20, Tab. 7.10) | **3.5 mA** (DC-DC), 7.5 mA (direkt) (S.154, Tab. 20-4) | 4.5 mA / 10 mA (S.140) | – |
| RX 1 Mbit/s | **5.3 mA** (DCDC), 9 mA (ohne) (S.20) | 3.4 mA (DC-DC), 7.1 mA (direkt) (S.154) | 6.5 / 13.5 mA (S.140) | – |
| Empfindlichkeit 1 Mbit/s | −96.5 dBm (S.1) | −95 dBm (S.151) | −98 dBm (S.1) | – |
| Bedingungen | 3.0 V, 25 °C | 3.3 V, 25 °C, „for reference only“ | 3.3 V | – |
| Flash / RAM | 512 KB / 36 KB (S.3, Device Information) | 448 KB Code + 32 KB DataFlash + 24 KB Boot / 26 KB (S.1, S.12) | 448 KB + 32 KB / 32 KB | – |
| Bootloader | **ROM: UART (2 Pins) oder SPI** (S.45; `TI_CC23xx_HWDesignGuide_SWRA834A.pdf` S.6–7, Tab. 3-2, Trigger-Pin DIO21 Tab. 3-4) | 24 KB System-Bootloader im Flash, „ICP, ISP, IAP“ (S.1, S.12). **Schnittstelle (USB/UART) im DS nicht spezifiziert** | wie CH592 | Nordic: kein ROM-UART-Bootloader, nur SWD (**ANNAHME**, DS fehlt) |
| Debug | SWD (DIO16/17) | 2-Draht-Debug (PB14/15), per ISP-Tool aktivierbar (S.9) | dto. | SWD |
| OTA | „Supports over-the-air upgrade“ (S.1) | „support OTA wireless upgrade“ (S.1) | dto. | – |
| Temperatursensor intern | ±10 °C bzw. −15/+9 °C roh (S.19, Tab. 7.8). **Unbrauchbar** für REQ-TMP-01 | ±10 °C (S.155, Tab. 20-9). Unbrauchbar | – | – |
| HF-Quarz | **48 MHz**, interne Lastkapazitäten (S.27; SWRA834 S.5) | **32 MHz** (S.5, Pins X32MI/MO) | 32 MHz | – |
| LF-Takt | LFXT 32.768 kHz, CL 6–12 pF (S.27) oder LFOSC (Einschränkungen laut Errata, SWRA834 S.5) | LSE oder LSI; LSI nach Kalibrierung ±0.04–0.2 % bei 0–60 °C (S.155, Tab. 20-6) | dto. | – |
| Peripherie für die Feuchtemessung | 12-bit-ADC (267 ksps intern), **LPCOMP 32-kHz-getaktet** (Entscheid 1–3 Takte, 370 nA; S.35, Kap. 7.21.6.1), LGPT-Timer mit Flankenzählung über TICKEN (`TI_CC23xx_TechnicalReferenceManual_SWCU193A.pdf` S.480, S.506 PRECFG.TICKSRC) | **Touch-Key-Modul 12 Kanäle, 10–100 pF, Shield-Treiberausgang** (S.132, Kap. 16.1), 0.1 mA (S.154); 4 Capture-Kanäle (S.2), 12-bit-ADC | Touch-Key ja | – |
| Antenne | 50-Ω-Single-ended, integrierter Balun; LC-Filter und π-Netz empfohlen (SWRA834 S.5–6, S.10) | ANT-Pin, „antenna directly“ (S.5), Anpassnetz integriert (S.151) | dto. | – |
| BLE-Stack/Lizenz | TI SimpleLink Low Power F3 SDK (**ANNAHME**: TI-Lizenz, Nutzung nur auf TI-Chips) | Binärbibliothek; Register „nicht beschrieben“, Zugriff nur über Bibliothek (S.151); SDK auf GitHub `openwch/ch592` unter Apache-2.0 (Repo-Metadaten 2026-11-06) | dto. | Nordic nRF Connect SDK (Zephyr, **ANNAHME**) |

### 3.2 Bewertung je Kandidat

**TI CC2340R52 (RGE, QFN24)**
- + Niedrigster belegter Schlafstrom. Mit Faktor 1.5: 0.74 × 1.5 = 1.1 µA (DCDC) bzw. 1.15 × 1.5 =
  1.7 µA (GLDO). Das lässt Reserve unter 3 µA für den Temperatursensor im Shutdown und Leckströme.
- + Funktioniert bis 1.71 V, das Brown-out liegt bei 1.67 V. Zwischen der Abschaltschwelle 2.0 V
  und dem BOD bleibt also Reserve.
- + ROM-UART-Bootloader: Erstprogrammierung mit einem USB-UART-Adapter. Zu prüfen ist, dass der
  Adapter die Zelle nicht speist (REQ-SAF-CC-03).
- + 512 KB Flash: zwei Abbilder möglich. **ANNAHME:** Ein BLE-Peripheriebild mit TI-Stack ist
  deutlich kleiner als 256 KB; am Build prüfen.
- − Unter 2.2 V schaltet der DCDC auf GLDO um. Ströme im Funkbetrieb dann ca. 9 mA statt 5 mA
  (S.18, S.20). Bei einer Knopfzelle am Lebensende ist das der relevante Fall für REQ-ENE-06.
- − QFN24 hat nur 12 DIO (S.7). 2 davon gehen an den 32-kHz-Quarz, 2 an SWD (nachher als GPIO
  nutzbar). Mit LED, Taster, I²C (2), Oszillator-Speisung und Oszillator-Eingang wird es eng, aber
  machbar (**ANNAHME**, Pinplan Phase 3). Die QFN40-Variante (C5914214) hat nur 283 an Lager.
- − LPCOMP mit 32-kHz-Takt (S.35) ist zu langsam für eine feine Lade-/Entladezeitmessung.

**WCH CH592F (QFN28)**
- + Sehr billig (0.67 USD), viel Lager, Touch-Key für 10–100 pF mit Shield-Ausgang (S.132).
  Passt zur Größenordnung einer PCB-Sonde (**ANNAHME**: Sondenkapazität 10–100 pF, Feldsimulation
  Phase 4).
- + Niedrigste Funkströme (3.5 mA TX 0 dBm mit DC-DC, S.154). Werte aber bei 3.3 V und „for
  reference only“.
- − Schlaf mit BLE-tauglichem RAM-Erhalt 2.2–2.5 µA typ. (LSE). Nach REQ-ENE-08 (× 1.5) ergibt
  das 3.3–3.75 µA > 3 µA (REQ-ENE-09). **Nur machbar, wenn der Stack mit RAM2K-Erhalt (1.3 µA)
  auskommt**, was zu prüfen ist.
- − Geschlossener BLE-Stack, keine Registerdokumentation (S.151). Signierte Updates und
  Rollback-Schutz (REQ-FW-04) müssen selbst gebaut werden (**ANNAHME**).
- − Programmierweg: Bootloader vorhanden, die Schnittstelle steht aber nicht im Datenblatt.
  **ANNAHME** (nicht belegt): USB-ISP über WCH-Tool bzw. WCH-LinkE für 2-Draht-Debug. Vor einer
  Empfehlung mit dem WCH-Referenzhandbuch belegen.
- − Zusätzlich nötig: 32-MHz-Quarz und DC-DC-Spule 10 µH.

**CH582F**: VDD min 2.3 V (S.138) erfüllt REQ-ENE-06 (2.0 V) nicht. **Verworfen.**
**CH591D**: VDD min 2.3 V (CH592-DS S.152, Tab. 20-2). **Verworfen.** CH591F hat 1.75 V, aber kein
Touch-Key (S.2) und nur 410 an Lager.

**Nordic nRF52805/810/832/833/820, nRF54L05; SiLabs EFR32BG22**: bei JLC lieferbar, Werte aber
**nicht lokal belegbar**. Nordic-Server (`docs-be.nordicsemi.com`, `infocenter.nordicsemi.com`)
liefern eine Cloudflare-Challenge, SiLabs liefert HTTP 403 (Akamai). Hinweise aus
Sekundärquellen: nRF52832 1.9 µA System ON mit RTC laut Nordic-DevZone mit Verweis auf PS v1.1
[W5]. Nordic hat nach allgemeiner Kenntnis keinen ROM-UART-Bootloader, die Erstprogrammierung
läuft über SWD (**ANNAHME**). SWD-Adapter ≤ 10 CHF wären z. B. ein Raspberry Pi Pico mit
CMSIS-DAP-Firmware (**ANNAHME** Preis und Eignung). nRF52805 gibt es nur als WLCSP, was für Rev. A
ungeeignet ist. nRF52832/833 kosten 4.6–5.6 USD, beim Kostenziel < 10 CHF ein großer Posten.

### 3.3 Externe Teile je SoC (Typ laut Datenblatt, LCSC-Vorschläge ungeprüft gegen Spezifikation)

| | CC2340R52 | CH592F |
|---|---|---|
| HF-Quarz | 48 MHz (z. B. TAITIEN XXHCELNANF-48MHZ C5160139, 3225, 1 804 Lager, 0.14 USD, Ext). Von TI validiert: Tai-Saw TZ3908AAAO43 (S.27 Fußnote 4). Toleranz und ESR prüfen | 32 MHz (z. B. YXC X322532MOB4SI C9009, 3225, 296 728 Lager, 0.10 USD, Ext) |
| LF-Quarz | 32.768 kHz, CL 6–12 pF (S.27). Kandidat **Epson Q13FC13500004 C32346 Basic** (483 710 Lager, 0.17 USD); **CL noch prüfen** | 32.768 kHz an PA10/PA11 (S.152 VXCK) |
| DC/DC | 10 µH + 10 µF an VDDR (S.18, Fußnote 2) | 10 µH an VSW, 4.7 µF an VDCID (S.5) |
| HF | LC-Filter + π-Anpassnetz (SWRA834 S.5–6, S.10) | direkt an die Antenne (S.5); π-Netz-Footprints trotzdem vorsehen (**ANNAHME**) |
| Bulk-C für Knopfzelle | 10 µF an VDDS wegen Slew-Rate bei Knopfzellen (S.18, Fußnote 3) | – |

### 3.4 Zeitbasis (REQ-SYS-07)
±2 min nach 14 d ≙ ≈ 99 ppm. CH592-LSI: ±0.04–0.2 % nach Softwarekalibrierung (0–60 °C,
S.155) ≙ 400–2000 ppm, **reicht nicht**. CC2340-LFOSC: Genauigkeit im DS nicht spezifiziert
(S.27), Einschränkungen laut Errata (SWRA834 S.5). **Folge: 32.768-kHz-Quarz in allen Varianten.**
Quarztoleranz und Temperaturgang (Parabel) gehen ins Fehlerbudget. Ein Abgleich gegen die
Gateway-Zeit bei jedem Kontakt ist ohnehin vorgesehen. Die Restabweichung bei 60 Tagen ohne
Gateway (±5 min ≙ 58 ppm) ist mit typischen ±20 ppm plus Temperaturgang bei 5–45 °C knapp
(**ANNAHME**, Quarzdatenblatt fehlt noch).

---

## 4 Antenne

- **Referenz CC23xx:** TI verweist bei allen LaunchPads auf die „2.4 GHz Inverted F Antenna“
  (SWRA834 S.3–4) und empfiehlt π-Anpassnetz + LC-Filter (S.10, Abb. 5-1).
- **Kompakte PCB-Antenne TI AN043** (`TI_AN043_SmallPCBAntenna_SWRA117D.pdf`):
  Meander-IFA, **15.2 × 5.7 mm**, VSWR < 2 im ISM-Band (S.1). Exakte Maße in Tab. 1 (S.4: L1–L6,
  W1–W2, D1–D6). „Exact copy“ wird dringend empfohlen (S.4). Die Groundplane-Größe beeinflusst die
  Leistung (S.6). **Passt auf eine 20–25 mm breite Platine**: Die Antenne liegt quer am oberen
  Rand, darunter folgt die Groundplane. Die Keepout-Fläche (kein Kupfer auf allen Lagen, keine
  Bauteile, kein Kunststoff mit hoher εr direkt anliegend) ist im Layout aus der Referenz zu
  übernehmen. **PROTOTYP-PRÜFUNG:** Verstimmung durch das ASA-Gehäuse und die Hand; π-Netz zum
  Nachstimmen bestücken.
- **CH592:** Referenzlayout im Datenblatt nicht enthalten. WCH-Evaluationsboards im
  GitHub-Ordner `openwch/ch592` (HDK) sind noch nicht ausgewertet. Die AN043-Antenne ist
  grundsätzlich auch hier nutzbar, braucht aber ein eigenes Anpassnetz (**ANNAHME**).
- Chipantenne: Die bei JLC gefundenen Typen haben kein Lager (Johanson 2450AT18A100E C89334:
  Lager 0). Eine PCB-Antenne kostet nichts und ist vorzuziehen.

---

## 5 Programmierung und OTA (REQ-FW-02/03/04/06)

| | CC2340R52 | CH592F | nRF52 (ANNAHME) |
|---|---|---|---|
| Erstprogrammierung | ROM-Bootloader UART (2 Pins) oder SPI; Trigger per Pin (Default DIO21) oder unbedingt (SWRA834 S.6–7) → **USB-UART-Adapter (~3 CHF, ANNAHME)** | Bootloader „ISP“; Schnittstelle nicht im DS. **ANNAHME:** USB-ISP oder WCH-LinkE (~5 USD) | SWD; Adapter z. B. Pi Pico als CMSIS-DAP |
| JLC-Vorprogrammierung | möglich (**ANNAHME**, JLC-Dienst prüfen) | dto. | dto. |
| 2 Abbilder | 512 KB Flash → ja (Größe am Build prüfen) | 448 KB Code-Flash → **ANNAHME** ja (WCH-OTA-Beispiele teilen in A/B) | nRF52832 512 KB (**ANNAHME**) |
| Signierte Updates | **ANNAHME:** TI-SDK bringt Bootloader-Unterstützung mit (MCUboot), zu belegen | selbst zu bauen (**ANNAHME**) | MCUboot im nRF Connect SDK (**ANNAHME**) |

REQ-SAF-CC-03: Die UART-Pads speisen keine Energie in die Zelle zurück. Das wird konstruktiv
gelöst: Programmieren nur ohne Zelle, der Adapter versorgt über eine getrennte Diode+Widerstand-Kette.
Detail in Phase 3 mit dem Sicherheitsagenten abstimmen.

---

## 6 Messprinzip Feuchte

### 6.1 (i) MCU-intern

| Verfahren | Schaltung | Bauteile | Bewertung |
|---|---|---|---|
| Lade-/Entladezeit | GPIO lädt Sondenkapazität über R, Eingang bzw. ADC misst die Zeit bis zur Schwelle | 1 R (Basic, z. B. 0402 10 kΩ UNI-ROYAL C25744 Basic) | billigste Lösung. Messfrequenz äquivalent ≈ 1/(2πRC). Bei C ≈ 50 pF und R = 10 kΩ ≈ 300 kHz (**Rechnung, C ANNAHME**). Hohe Empfindlichkeit für Leitfähigkeit (6.4). Auflösung: CC2340-Timer 48 MHz → 20.8 ns pro Zählschritt; für 1 % von ΔC sind viele Mittelungen nötig |
| Touch-Peripherie | CH592 Touch-Key + Shield-Ausgang (S.132) | keine | ausgelegt für 10–100 pF; Ladezeit in ADC-Takten (S.132 R8_TKEY_COUNT: Ladung (n+4)·Tadc). Effektive Frequenz im 100-kHz–MHz-Bereich (**ANNAHME**). Auflösung und Temperaturgang am Muster prüfen |
| Komparator-RC-Oszillator | LPCOMP + R-Rückkopplung | 1–2 R | CC2340-LPCOMP ist mit 32 kHz getaktet (S.35) → Oszillator ≤ ~10 kHz. **Ungeeignet** |

### 6.2 (ii) Dedizierter Kapazitäts-Digital-Wandler

| IC | LCSC | Ext | Lager | USD @20 | Versorgung | Strom | Messfrequenz | Bewertung |
|---|---|---|---|---|---|---|---|---|
| TI FDC1004DGSR | C2865994 | Ext | 7 082 | 2.85 | **3.0–3.6 V** (S.4) | 750 µA aktiv, **29 µA Standby** (S.5) | **25 kHz** fest (S.5) | 0.5 fF Auflösung, ±15 pF Bereich + 100 pF CAPDAC (S.1, S.5), Shield-Treiber. Nachteile: 3.3-V-Versorgung (Boost bei Knopfzelle), Standby-Strom → Lastschalter nötig, **25 kHz sehr salzempfindlich** |
| TI FDC2212DNTR | C968585 | Ext | 310 | 6.02 | **2.7–3.6 V** (S.7) | 2.1 mA, Shutdown 0.2 µA (S.7) | **0.01–10 MHz** LC-Resonanz (S.7) | höhere Frequenz möglich, braucht L+C-Schwingkreis (Spule im Sondenkreis), teuer, wenig Lager, Mindestspannung über der Abschaltschwelle 2.0 V |
| TI FDC2112DNTR | C544400 | Ext | 73 | 5.34 | 2.7–3.6 V (gl. DS) | gl. | gl. | 12 bit, kaum Lager |

Folge: CDCs erfüllen die Spannungsanforderung einer Knopfzelle (bis 2.0 V) nur mit Boost-Wandler.
Das bedeutet Mehrkosten (IC + Spule, **ANNAHME** ≥ 0.5 USD) und Ruhestrom. In der Akku-Variante
[LI] wären 3.0–3.6 V über einen LDO verfügbar.

### 6.3 (iii) Externer Oszillator

- **Schaltung:** SN74LVC1G14 (Schmitt-Inverter) mit R vom Ausgang auf den Eingang, Sonde von
  Eingang nach GND (bzw. Referenzelektrode). Versorgung aus einem GPIO oder Lastschalter, damit im
  Schlaf 0 µA fließen. Ausgang auf den Timer-Eingang (CC2340: LGPT mit TICKEN-Flanken, TRM S.506;
  CH592: Capture-Kanal).
- **Datenblatt:** VCC 1.65–5.5 V (S.6, Tab. 5.3), Schwellen bei 3 V: VT+ 1.5–1.87 V, VT− 0.84–1.14 V,
  Hysterese 0.56–0.87 V (S.7, Tab. 5.5), ICC ≤ 10 µA statisch (S.7), Cpd 22 pF bei 3.3 V (S.8).
- **Frequenz:** T = RC·[ln((V−VT−)/(V−VT+)) + ln(VT+/VT−)]. Mit Mittelwerten bei 3 V
  (VT+ ≈ 1.68 V, VT− ≈ 0.99 V) gilt T ≈ 0.95·RC (**Rechnung**). Beispiel C = 50 pF (**ANNAHME**),
  R = 2 kΩ → f ≈ 10 MHz. Die Frequenz ist über R im Bereich 1–20 MHz wählbar.
- **Strom:** ≈ (Cpd + C)·V·f ≈ 72 pF · 3 V · 10 MHz ≈ 2 mA während der Messung (**Rechnung**).
  Bei 10 ms pro Messung und ≤ 100 Messungen pro Tag (inkl. Mittelung) ist der Tagesmittelwert
  < 0.03 µA, also vernachlässigbar.
- **Exemplarstreuung:** Die Schwellen streuen stark (s. o.) und hängen von VCC ab. **Abhilfe:**
  ratiometrisch messen, entweder mit einem zweiten Kanal gleichen Typs gegen einen
  Referenzkondensator (C0G) oder mit demselben Gatter und umschaltbarer Referenz. Versorgung über
  ein festes Rail (ANNAHME: LDO 1.8 V oder 2.5 V, bzw. Messung VDD-kompensiert). Das unterstützt
  REQ-MES-07 (±15 %-Punkte ohne Einzelkalibrierung).
- **Zählgrenze:** CC2340-LGPT zählt TICKEN-Flanken, die vermutlich mit dem 48-MHz-Systemtakt
  synchronisiert werden → **ANNAHME:** fmax ≈ 24 MHz. **PROTOTYP-PRÜFUNG.** Bei Bedarf hilft ein
  Teiler (z. B. 74LVC1G80-Flipflop, nicht recherchiert).
- **Bauteile:** SN74LVC1G14DCKR **C35740** (TI, SC-70-5, Ext, 98 074 Lager, 0.057 USD) bzw.
  SN74LVC1G14DBVR **C7835** (SOT-23-5, Ext, 227 396 Lager, 0.058 USD). R und C0G-Referenz: Basic.
  Alternative TLC555 (C6986, SOIC-8, 0.23 USD). Mehr Fläche und Strom, ohne Vorteil.

### 6.4 Messfrequenz und Salz/Dünger (REQ-MES-11)

**Physik:** Ionenleitung erzeugt einen Verlustanteil ε''σ = σ/(2πf·ε0). Solange ε''σ ≫ ε'
(ca. 10–30 für feuchte Erde), dominiert die Leitfähigkeit. Bei isolierten Elektroden (Innenlagen,
REQ-MECH-04) sättigt die gemessene Kapazität dann gegen die Isolationskapazität. Die Anzeige wird
salzabhängig und bei hoher Feuchte unempfindlich. Rechnung (`scripts/phase2_salt_loss.py`,
ε' = 25, σ als **ANNAHME**):

| f | σ = 0.01 S/m | σ = 0.05 S/m | σ = 0.2 S/m |
|---|---|---|---|
| 25 kHz (FDC1004) | ε''/ε' = 288 | 1 440 | 5 750 |
| 1 MHz | 7.2 | 36 | 144 |
| 10 MHz | 0.72 | 3.6 | 14 |
| 20 MHz | 0.36 | 1.8 | 7.2 |
| 70 MHz (ECH2O) | 0.10 | 0.51 | 2.1 |

Grenzfrequenz (ε'' = ε'): 7.2 MHz (0.01 S/m), 36 MHz (0.05 S/m), 144 MHz (0.2 S/m).

**Literatur:**
- [L1] Kizito, F. et al. (2008): *Frequency, electrical conductivity and temperature analysis of a
  low-cost capacitance soil moisture sensor*. J. Hydrology 352, 367–378,
  doi:10.1016/j.jhydrol.2008.01.021. Untersucht 5–150 MHz. Bei **70 MHz** genügt eine einzige
  Kalibrierkurve für mineralische Böden, **unabhängig vom Salzgehalt**; ca. 2 % Fehler bis zu
  einer Bodenlösungs-EC von ≈ 12 dS/m. Quelle der Zusammenfassung: CZO-Archiv
  (czo-archive.criticalzone.org, abgerufen 2026-11-06); Volltext nicht geladen (Verlag).
- [L2] dos Santos, C. P. (2022): *Performance of the capacitive moisture sensor under different
  saline conditions*. Rev. Ciência Agronômica 53. Ein RC-basierter Sensor (kHz–MHz) reagierte in
  KCl-Lösungen bis 4 dS/m empfindlich auf Salz; andere Widerstände im RC-Glied brachten keine
  signifikante Verbesserung. (periodicos.ufc.br/revistacienciaagronomica/article/view/88914,
  abgerufen 2026-11-06)
- [L3] Campbell, J. E. (1990): *Dielectric properties and influence of conductivity in soils at
  one to 50 megahertz*. Soil Sci. Soc. Am. J. Nur als Referenz in [L1] gesehen, nicht gelesen.

**Bewertung:** Mit vertretbarem Aufwand erreichbar sind ≈ 10–20 MHz mit LVC1G14 bzw. ≤ 10 MHz
mit FDC2212. Das liegt unter den 70 MHz aus [L1], aber 2–3 Größenordnungen über FDC1004 (25 kHz)
und der Touch-/RC-Ladezeitmessung. Für gedüngte Topferde (RB-02) ist das Ziel ≤ 5 %-Punkte damit
**nicht gesichert**. Maßnahmen:
1. Messfrequenz so hoch wie zählbar wählen (Ziel ≥ 10 MHz).
2. Isolationsdicke und Elektrodengeometrie in der Feldsimulation Phase 4 mit **komplexer
   Permittivität** (σ-Variation) rechnen.
3. Optional Zwei-Frequenz-Messung (R umschaltbar, z. B. 1 MHz und 15 MHz). Die Differenz zeigt
   den Leitfähigkeitseinfluss und kann für REQ-MES-12 (Überflutung) bzw. eine Korrektur dienen
   (**ANNAHME**, Konzept).
4. Becherversuch REQ-MES-11 früh am ersten Muster (**PROTOTYP-PRÜFUNG**).

### 6.5 Vergleich Messprinzipien

| Kriterium | (i) RC-Ladezeit / Touch | (ii) FDC1004 | (ii) FDC2212 | (iii) LVC1G14-Oszillator |
|---|---|---|---|---|
| Kosten (USD @20) | ≈ 0.01 (R) | 2.85 + Boost + Lastschalter | 6.02 + L/C + Boost | ≈ 0.06 + 2 R + C0G |
| Min. Versorgung | SoC (1.71/1.75 V) | 3.0 V | 2.7 V | 1.65 V |
| Schlafstrom | 0 | 29 µA ohne Schalter | 0.2 µA (Shutdown) | 0 (GPIO-gespeist) |
| Messfrequenz | ~0.1–1 MHz (ANNAHME) | 25 kHz | ≤ 10 MHz | 1–20 MHz (wählbar) |
| Salzrobustheit | schlecht | schlecht | mittel | mittel bis gut |
| Auflösung | mittel (Mittelung nötig) | sehr hoch | sehr hoch | hoch (Zählzeit) |
| Basic/Extended | Basic | Ext | Ext | Ext (1 Typ) |
| JLC-Lager | – | 7 082 | 310 | > 98 000 |

**Empfehlung Messprinzip:** (iii) LVC1G14-Oszillator als Hauptvariante. (i) als Rückfallebene
ohne Zusatzbauteil (für CH592 das Touch-Key-Modul) zum Vergleich auf dem Prototyp mit vorsehen,
wenn ein Pin frei bleibt. CDCs nur in der Akku-Variante sinnvoll, wegen der Frequenz aber auch
dort nicht vorteilhaft.

---

## 7 Bodentemperatur (REQ-TMP-01, ±1 °C bei 10–35 °C)

Position: auf der Leiterplatte **direkt oberhalb der Dichtlinie, im vergossenen bzw. versiegelten
Bereich**, thermisch über eine Kupferfläche (Innenlage) zur Sonde gekoppelt und vom Kopf
(Sonne, RB-03) möglichst entkoppelt (Schlitz/Fräsung, **ANNAHME**, Feldsimulation/Muster).

| Sensor | LCSC | Ext | Lager | USD @20 | Versorgung | Genauigkeit (max.) | Ruhestrom | Bewertung |
|---|---|---|---|---|---|---|---|---|
| **TI TMP1075DSGR** | C2870250 | Ext | 34 641 | 0.31 | 1.7–5.5 V (S.6) | **±1 °C** −40–75 °C (DSG, S.6 Tab. 6.5) | 0.37 µA Shutdown (S.1) | erfüllt knapp, ohne Reserve für Gradienten |
| TI TMP1075NDRLR | C3663690 | Ext | 20 063 | 0.54 | 1.62–3.6 V (S.5) | ±1 °C −10–60 °C (S.3) | dto. | SOT-563, gut lötbar |
| **TI TMP117AIDRVR** | C699536 | Ext | 11 588 | 0.91 | (DS; ab 1.7 V laut Revisionshinweis S.2, prüfen) | **±0.3 °C** −55–150 °C (S.1) | 150 nA Shutdown (S.1) | Reserve für thermische Fehler; teurer |
| TI TMP102AIDRLR | C99269 | Ext | 27 601 | 0.54 | 1.4–3.6 V | **±2 °C** −25–85 °C (S.5) | – | **erfüllt REQ-TMP-01 nicht garantiert** |
| NTC 10 k 1 % (Murata NCP15XH103F03RC, 0402) | C77131 | Ext | 302 530 | 0.017 | ADC ratiometrisch | abhängig von R25-/B-Toleranz und Referenzwiderstand | 0 (Teiler per GPIO) | billig; **Datenblatt nicht ladbar**, Fehlerbudget offen |
| NTC Murata NCP18XH103F03RB (0603) | C13564 | Ext | 333 724 | 0.051 | – | – | – | laut Octopart/RS **NRND/abgekündigt** (Sekundärquelle) → nicht verwenden |
| Sunlord SDNT1005X103F3950FTF | C95939 | Ext | 193 579 | 0.015 | – | – | – | Datenblatt nicht gesucht |

Weder ein Basic-NTC noch ein Basic-Temperatursensor wurde gefunden. Der Teilerwiderstand 10 kΩ 1 %
ist Basic (C25744).

**Empfehlung:** digitaler I²C-Sensor. **TMP117**, wenn das Budget 0.6 USD Aufpreis erlaubt, sonst
**TMP1075**. Gründe: garantierter Maximalfehler ohne Kalibrierung, Shutdown < 0.4 µA, kein ADC-
und Referenzfehler. NTC nur, wenn nach Ladung des Datenblatts ein Fehlerbudget ≤ ±0.7 °C (Reserve
für Gradienten) nachgewiesen ist. Der interne SoC-Temperatursensor ist unbrauchbar (±10 °C).
**PROTOTYP-PRÜFUNG:** Abweichung zur Bodentemperatur in 5 cm Tiefe und bei Sonne auf dem Kopf.

---

## 8 Hinweise zur Sondengeometrie (nur Vorbereitung Phase 4)

- TI SNOA927A (`TI_FDC1004_CapSensingBasics_SNOA927A.pdf`): Topologien Parallelplatte und
  „Parallel Fingers“ (Kap. 6.1–6.2, S.7–9). Die Empfindlichkeit wächst nichtlinear mit der
  Elektrodengröße. Ein **Shield auf der Rückseite** richtet das Feld aus (S.8); aktive Abschirmung
  in Kap. 7.2.3 (S.10–11). Für die Sonde heißt das: die Guard-Struktur zwischen Kopfelektronik und
  Sonde (REQ-MECH-09) als getriebenes Shield auslegen, wenn das Messprinzip einen Shield-Ausgang
  hat (FDC1004, CH592 Touch-Key). Beim LVC1G14 ist es ein Massering.
- Isolation in Serie zur Erde: Je dünner und je höher εr der Isolation, desto größer die
  Empfindlichkeit, desto größer aber auch der Leitfähigkeitseinfluss bei tiefer Frequenz (6.4).
  In Phase 4 als Parameter rechnen: Prepreg-Dicke Innenlage–Außenkante, Coating.
- Messvolumen 10–90 mm (REQ-MES-08): Elektroden im Bereich 0–10 mm unter der Dichtlinie
  abschirmen bzw. aussparen.
- Erwartete Sondenkapazität (10–100 pF, **ANNAHME**) bestimmt R im Oszillator bzw. den
  CAPDAC-Bereich. Erster Wert aus der 2D-Simulation.

---

## 9 Abgelegte Dokumente und Lücken

Abgelegt (alle mit `file` als PDF geprüft, Register `_staging/INDEX_elektronik.csv`):

| Datei | Inhalt |
|---|---|
| `docs/datasheets/TI_CC2340R5_Datasheet_SWRS272F.pdf` | CC2340R2/R5, Rev. F 05/2026 |
| `docs/datasheets/TI_CC23xx_TechnicalReferenceManual_SWCU193A.pdf` | CC23xx TRM, Rev. A 08/2024 |
| `docs/appnotes/TI_CC23xx_HWDesignGuide_SWRA834A.pdf` | HW-Design-Guide, Rev. A 02/2026 |
| `docs/appnotes/TI_AN043_SmallPCBAntenna_SWRA117D.pdf` | PCB-Antenne 15.2 × 5.7 mm |
| `docs/datasheets/WCH_CH592_Datasheet_V1.9.pdf` | CH592/CH591 V1.9 (aus offiziellem GitHub `openwch/ch592`) |
| `docs/datasheets/WCH_CH583_Datasheet_V1.9.pdf` | CH583/CH582 V1.9 (GitHub `openwch/ch583`) |
| `docs/datasheets/TI_FDC1004_Datasheet_SNOSCY5C.pdf` | FDC1004 |
| `docs/appnotes/TI_FDC1004_CapSensingBasics_SNOA927A.pdf` | Grundlagen kapazitive Messung |
| `docs/datasheets/TI_FDC2212_Datasheet_SNOSCZ5B.pdf` | FDC2112/2114/2212/2214 |
| `docs/datasheets/TI_SN74LVC1G14_Datasheet_SCES218AA.pdf` | Schmitt-Inverter |
| `docs/datasheets/TI_TMP1075_Datasheet_SBOS854F.pdf` | TMP1075 |
| `docs/datasheets/TI_TMP117_Datasheet_SNOSD82D.pdf` | TMP117 |
| `docs/datasheets/TI_TMP102_Datasheet_SBOS397I.pdf` | TMP102 (verworfen) |

**Nicht herunterladbar** (im Register vermerkt):
- Nordic nRF52805/810/832/833 (und nRF54L): Cloudflare-Challenge auf `docs-be.nordicsemi.com` und
  `infocenter.nordicsemi.com`. Ein Umgehungsversuch mit Browser-Kennung wurde vom
  Berechtigungssystem gesperrt und nicht weiter verfolgt.
- Silicon Labs EFR32BG22-Datenblatt: HTTP 403 (Akamai).
- Murata NTC (NCP15/NCP18): PDF-API liefert HTML.
- Sensirion STS4x: Link lieferte XML-Fehler (nicht weiter verfolgt, STS40 nicht empfohlen).
- Epson 32-kHz-Quarz C32346, 48/32-MHz-Quarze: noch nicht gesucht.

---

## 10 Empfohlene Kombinationen für die Konzeptvarianten

### Variante A (Empfehlung): CC2340R52 + LVC1G14-Oszillator + TMP1075/TMP117
- SoC C20416850 (1.34) + 48-MHz-Quarz (~0.14) + 32-kHz-Quarz Basic (0.17) + 10 µH (Basic
  C1035, 0.03) + LVC1G14 (0.06) + TMP1075 (0.31) ≈ **2.1 USD** für die Kernteile ohne Passive,
  Antenne = PCB.
- Begründung: niedrigster belegter Schlafstrom (Reserve zu REQ-ENE-09), Betrieb bis 1.71 V,
  UART-ROM-Bootloader (REQ-FW-06 ohne Spezialadapter), 512 KB für A/B-Update, hohe Messfrequenz.
- Risiken: GPIO-Knappheit QFN24, Funkstrom unter 2.2 V (GLDO), SDK-Größe und signierter
  Bootloader noch nicht belegt, 32-kHz-Quarz-CL prüfen.

### Variante B (Kostenminimum): CH592F + LVC1G14-Oszillator (alternativ Touch-Key) + TMP1075
- SoC C39831287 (0.67) + 32-MHz-Quarz (0.10) + 32-kHz-Quarz (0.17) + 10 µH (0.03) + LVC1G14
  (0.06) + TMP1075 (0.31) ≈ **1.3 USD**.
- Begründung: billigster Chip mit 1.75 V und Touch-Key (Vergleichsmessung ohne Zusatzteil).
- Risiken: Schlafstrom-Budget (2.2–2.5 µA typ. → × 1.5 über 3 µA), geschlossener Stack,
  Programmierweg und Sicherheitsfunktionen (signierte OTA) unbelegt, Datenblattwerte „for
  reference only“ bei 3.3 V.

### Variante C (bewährtes Ökosystem, bedingt): nRF52832/nRF52833 + LVC1G14 + TMP1075
- Nur zulässig, wenn der Auftraggeber die Nordic-Datenblätter manuell bereitstellt. Kosten
  ≈ 4.6–5.6 USD nur für den SoC. SWD-Adapter ≤ 10 CHF nötig (ANNAHME Pi Pico).
- Vorteil: großes Ökosystem (Zephyr/MCUboot), viel Lager. Nachteil: Preis gegen das
  10-CHF-Ziel, Programmierweg nur SWD (ANNAHME).

Variante [LI] (Akku): Die Kombinationen A–C gelten unverändert. Dort wäre zusätzlich FDC2212 an
3.0 V möglich, bringt aber keinen Frequenzvorteil gegenüber (iii).

---

## 11 Offene Risiken und nächste Schritte

| # | Risiko / offener Punkt | Schritt |
|---|---|---|
| R1 | Salzeinfluss bei ≤ 20 MHz nicht gesichert (REQ-MES-11) | Feldsimulation mit komplexer Permittivität (Phase 4), Becherversuch am ersten Muster, Zwei-Frequenz-Option im Schaltplan |
| R2 | Timer-Zählgrenze CC2340 für externe Flanken (ANNAHME 24 MHz) | TRM-Kapitel LGPT/Event Fabric genauer lesen, Testaufbau |
| R3 | CH592-Schlafstrom über Budget mit Faktor 1.5 | nur Variante B; WCH-Stack-RAM-Bedarf klären |
| R4 | Nordic/SiLabs-Datenblätter fehlen | Auftraggeber lädt manuell herunter (Browser), Ablage nach Namensschema |
| R5 | 32-kHz-Quarz: Lastkapazität und Temperaturgang gegen REQ-SYS-07 (58 ppm nach 60 d) | Epson-Datenblatt laden, Fehlerbudget mit dem Firmware/Energie-Agenten |
| R6 | CC2340 QFN24: nur 12 DIO | Pinplan in Phase 3; Fallback QFN40 (Lager 283) |
| R7 | Funkströme der CC2340 unter 2.2 V (GLDO, 9 mA) → Spannungseinbruch REQ-ENE-06 | SPICE mit Zellinnenwiderstand 100 Ω, Pufferkondensator |
| R8 | Exemplarstreuung des Oszillators (Schwellen ±) | Referenzkanal (C0G) vorsehen, ratiometrisch auswerten |
| R9 | Alle Halbleiter Extended → Extended-Gebühr pro Typ | mit Fertigung/Kosten in Phase 2 aufrechnen (REQ-FAB-05) |
| R10 | NTC-Datenblätter fehlen, NCP18 NRND | bei Wunsch NTC: NCP15XH103F03RC-Datenblatt manuell laden |

---

## 12 Webquellen

- [W1] JLC-API `https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList`, Abruf 2026-11-06
- [W2] Kizito et al. 2008, Zusammenfassung: https://czo-archive.criticalzone.org/sierra/publications/pub/kizito-et-al-2008-frequency-electrical-conductivity-and-temperature-analysi/
- [W3] dos Santos 2022: https://periodicos.ufc.br/revistacienciaagronomica/article/view/88914
- [W4] TI SWRA834 (Suchtreffer und PDF): https://www.ti.com/lit/pdf/swra834
- [W5] Nordic DevZone (Sekundärquelle nRF52832-Schlafstrom): https://devzone.nordicsemi.com/f/nordic-q-a/10943/how-much-current-consumption-nrf52-in-sleep-mode-and-rtc-on/40904
- [W6] NRND-Hinweis NCP18XH103F03RB (Sekundärquelle): https://octopart.com/part/murata/NCP18XH103F03RB
- [W7] WCH SDK/Datenblätter: https://github.com/openwch/ch592, https://github.com/openwch/ch583
