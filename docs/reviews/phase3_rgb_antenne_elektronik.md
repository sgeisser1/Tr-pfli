# Phase 3 – Machbarkeit RGB-Status-LED (Sensor A-32) und interne Gateway-Antenne

Ersteller: Elektronik · Datum 2026-11-07 · Bezug: D-006 (A-32), D-009 (P3 „Stele“, RGB-LED, Antenne intern),
REQ-UI-01…07, REQ-ENE-02/-08/-09, REQ-FAB-04, REQ-RF-02/-03, `docs/concepts/CONCEPTS.md` 2.2/2.4/2.5/2A/5.1,
`docs/concepts/research_gateway.md`.

Neue bzw. geänderte Dateien:
- Datenblätter: `docs/datasheets/TUOZHAN_P4-1615G2B2R4TS2-06T-001-24_Datasheet_A0.pdf`,
  `docs/datasheets/XINGLIGHT_XL-1615RGBC-RF_Datasheet_LCSC-2024-10.pdf`,
  `docs/datasheets/NationStar_FC-B1010RGBT-HG_Datasheet_A1.pdf`, `docs/datasheets/TI_LM2664_Datasheet_SNVS005E.pdf`,
  `docs/appnotes/Espressif_ESP32-S3_HardwareDesignGuidelines_master-2026-11.pdf`
- Register: `docs/datasheets/_staging/INDEX_rgb.csv` (8 Zeilen, Kopf aus `HEADER.csv`)
- SPICE: `simulation/spice/led_rgb/fit_led_models.py` (erzeugt `led_models.inc`),
  `simulation/spice/led_rgb/led_rgb_drive.py` (erzeugt `led_rgb_drive.cir`, `led_rx_conflict.cir`, ruft `ngspice -b`)

Neu erzeugen:
```
.venv/bin/python simulation/spice/led_rgb/fit_led_models.py
.venv/bin/python simulation/spice/led_rgb/led_rgb_drive.py
```

---

## Kurzfassung

| Frage | Ergebnis |
|---|---|
| RGB machbar? | **Ja, mit Einschränkung bei Blau.** Rot und Gelb (R+G) leuchten über die ganze Lebensdauer (VDD 2.4–3.0 V), Grün auch bei Exemplaren mit maximaler VF ab 2.5 V voll und bei 2.4 V noch erkennbar. **Blau** ist bei typischen Exemplaren ab ≈ 2.75 V voll hell (≈ 80 % der Zelllebensdauer, **ANNAHME** aus der Entladekurve), bei Exemplaren mit maximaler VF erst ab ≈ 2.95 V. Lösung ohne Zusatzbauteil: **Farbtabelle in der Firmware nach gemessener VDD**, blau-codierte Zustände bekommen eine Ausweichfarbe. Eine Ladungspumpe lohnt nicht. |
| Teil | **TUOZHAN P4-1615G2B2R4TS2-06T-001-24, LCSC C7496855**, Extended, Lager 74 324, 0.0131 USD (JLC 2026-11-07), 1.6 × 1.5 × 0.6 mm, gemeinsame Anode. Zweitquelle XINGLIGHT XL-1615RGBC-RF (C965840, Lager 715 582). **Es gibt keine Basic-RGB-LED** (JLC-Suche 2026-11-07, alle RGB-Treffer „expand“). |
| Vorwiderstände (Basic) | R 470 Ω C25117, G 200 Ω C25087, B 100 Ω C25076 |
| Pins | Für 3 Kanäle **müssen 2 Pins dazukommen** (bisher 1). Vorschlag: TMP_PWR auf DIO12 (zusammen mit OSZ_PWR) legen → DIO13 wird frei für Grün; Blau auf DIO20 (UART RX, bisher Reserve). Damit Blau die Programmierung nicht stört, muss der Dummy-Zellen-Adapter mit **VDD ≤ 2.0 V** (1.8-V-UART-Pegel) programmieren. Danach ist **kein Reservepin** mehr frei. |
| Kosten | Stückkosten Serie **+0.02 CHF** (7.07 → 7.09), Einmal **+2.79 CHF** (Extended-Gebühr), Vollkosten/Sensor +0.20 CHF (13.52 → 13.73). REQ-FAB-04 bleibt erfüllt. |
| Energie | LED-Anteil von 2.0 % auf **≤ 3.0 %** (Firmware-Regel: mittlerer LED-Strom je Blink ≤ 3 mA) → REQ-UI-03 (≤ 5 %) erfüllt; Laufzeit pess. DS 17.0 → 16.9 Monate. |
| Gateway-Antenne | **Empfehlung: XIAO ESP32-S3 Plus beibehalten, statt der Stabantenne eine FPC-Klebeantenne (U.FL) innen auf die Gehäusewand**, ≥ 15 mm Freiraum zu USB-C, XIAO-Masse und RTC. Gewinn ≤ 2.81 dBi (z. B. Seeed A-02, 1.16 dBi), sonst Sendeleistung begrenzen. Linkbudget bei 18 m: nominal ≈ 18 dB Reserve (Stab ≈ 21 dB), pessimistisch 7 dB → am schlechtesten Platz Sensor auf +4 dBm. Board mit PCB-Antenne (ESP32-S3-WROOM-1) nicht empfohlen, weil es 15 mm Freiraum in alle Richtungen braucht und das Gehäuse grösser würde. |

---

## 1 RGB-Status-LED für A-32

### 1.1 Teilewahl (JLC-Abfrage 2026-11-07)

Gesucht wurde mit „RGB LED“, „RGB 1010/1615/2020/0606/0404/3528“: 1871 Treffer, **keine Basic-RGB-LED**.
Basic sind nur Einfarb-LEDs: KT-0603R rot C2286, KT-0805G grün C2297, KT-0805Y gelb C2296, KT-0603W/-0805W
weiss C2290/C34499. Blau gibt es nicht als Basic. Getrennte grüne/blaue 0603-LEDs (C72043, C72041) sind Extended
und haben Lager 0. LEDs mit eingebautem IC (WS2812/SK6812) scheiden aus, weil sie dauernd Ruhestrom ziehen
(Datenblätter nicht ausgewertet).

| Kandidat | LCSC | Kat. | Lager | USD @1 | VF Grün / Blau laut Datenblatt | Iv Blau | Bewertung |
|---|---|---|---|---|---|---|---|
| **TUOZHAN P4-1615G2B2R4TS2-06T-001-24** (1615, gemeinsame Anode) | **C7496855** | E | 74 324 | 0.0131 (0.0114 @500) | **G 2.5–2.9 V, B 2.6–3.0 V bei 5 mA**; R 1.8–2.2 V (S.5, Tab. CHARACTERISTICS) | 60–80 mcd @5 mA (S.5) | **gewählt**: engste VF-Spezifikation bei kleinem Strom, hell, günstig |
| XINGLIGHT XL-1615RGBC-RF (1615, gem. Anode) | C965840 | E | 715 582 | 0.0197 | G/B 2.6–3.4 V bei 20 mA (S.4) | 120–180 mcd @20 mA (S.4) | Zweitquelle (grosses Lager); VF nur bei 20 mA spezifiziert; Pinbelegung vor Einsatz gegen S.8 prüfen |
| NationStar FC-B1010RGBT-HG (1010) | C158099 | E | 11 466 | 0.027 | G 2.2–3.2 V (typ 2.6), B 2.3–3.2 V (typ 2.7) bei **2 mA** (Datenblatt-S. 2/13) | 3–10 mcd @2 mA | nicht gewählt (Blau dunkel, VF-Streuung bis 3.2 V); **liefert die I-U-Kennlinie 1–10 mA** (S. 3/13) für das SPICE-Modell |
| MEIHUA MHPA1010RGBDT | C404280 | E | 39 445 | 0.0776 | G/B 2.5–3.5 V bei 3 mA | 5.9–11.6 mcd @3 mA | nicht gewählt (teurer, VF bis 3.5 V); Datenblatt nicht abgelegt |

**Gewähltes Teil C7496855** (`TUOZHAN_P4-1615G2B2R4TS2-06T-001-24_Datasheet_A0.pdf`):
- Pinbelegung S.4 (Schema rechts oben): **Pin 1 = + (gemeinsame Anode), Pin 2 = R (SR), Pin 3 = G, Pin 4 = B**.
  Gehäuse 1.5 × 1.6 × 0.6 mm, Pads 0.5 × 0.8 mm, Abstand 0.7 mm (S.4, „Recommended Solder Pad Design“).
  Footprint im Generator nach S.4 anlegen; JLC-Bezeichnung „SMD-4P,1.6x1.5mm“.
- Grenzwerte (S.5): IF 30 mA DC, IFP 40 mA, **VR 5 V**, Pd R 60 / G,B 90 mW, Betrieb −40…85 °C, ESD R 2500 V / G,B 2000 V (HBM).
- Abstrahlwinkel 2θ½ = **120°** (S.5).
- Hinweise: MSL-Handhabung (innerhalb 7 Tagen nach Öffnen verarbeiten, S.11), nicht in Flüssigkeit (S.11).
- Datenblatt Revision A0 von 2021 und nur über LCSC verfügbar; Iv-Bins 60–80 mcd deuten auf eine Sortierung hin.
  Das gilt laut Hinweis S.10 nur als „typical, for reference“ → **PROTOTYP-PRÜFUNG** an 10 Exemplaren.

### 1.2 Durchlassspannung bei kleinem Strom

Kein lokales Datenblatt nennt VF unter 1 mA. Vorgehen (Skript `fit_led_models.py`):
1. Die I-U-Kennlinie der NationStar-LED (S. 3/13, InGaN für G/B, AlGaInP für R) wird bei 1/2/5/10 mA abgelesen.
   Die Y-Achse hat 9 gleiche Teilungen und ist nur mit „1“ und „10“ beschriftet. Gelesen wird sie **linear** (ANNAHME).
   Das ist die konservative Lesart, denn bei 2–5 mA ergibt sie 0.1–0.12 V weniger VF-Abfall zwischen 5 mA und 1 mA.
2. Daran wird ein Diodenmodell gefittet (IS, N, RS; Fitfehler ≤ 9.5 mV).
3. Die Kurve wird starr verschoben, sodass VF bei 5 mA = min / Mitte / max des TUOZHAN-Datenblatts (S.5) ist (ANNAHME: gleiche Steigung).

Typische Kurvenform (vor Verschiebung): VF bei 1 mA = **R 1.80 V, G 2.35 V, B 2.63 V** (NationStar S. 3/13,
lesartunabhängig, weil 1 mA auf der Achsenlinie liegt). Abgeleitete VF für C7496855 bei 1 mA: **G 2.21–2.61 V, B 2.39–2.79 V**.
Unter 1 mA ist das Modell eine Extrapolation (**ANNAHME**). **PROTOTYP-PRÜFUNG:** I-U-Kennlinie 0.05–5 mA an
10 Exemplaren messen und `led_models.inc` damit ersetzen.

### 1.3 Schaltung und SPICE-Ergebnis

Schaltung: gemeinsame Anode an **VDD**, jede Kathode über einen Vorwiderstand an einen GPIO, der GPIO zieht auf low.
Vorteile: keine Zusatzbauteile, kein Ruhestrom (LED aus = GPIO high oder hochohmig → 0 V an der LED), die
Sperrspannung bleibt ≤ VDD < VR 5 V. GPIO-Widerstand: Standard-Drive VOL ≤ 0.20 V bei 2 mA, VDDS 3.0 V
(`TI_CC2340R5_Datasheet_SWRS272F.pdf` S.31, 7.21.4.1) → ≤ 100 Ω, für den ganzen Bereich als Grenzwert verwendet
(bei VDDS < 3.0 V nicht spezifiziert, **ANNAHME**).

`ngspice -b` (`led_rgb_drive.py`), LED-Strom in mA, R_on = 100 Ω (Grenzwert):

| Farbe | R_ser | VF-Exemplar | 2.4 V | 2.5 V | 2.6 V | 2.7 V | 2.8 V | 2.9 V | 3.0 V | 3.3 V (Adapter alt) |
|---|---|---|---|---|---|---|---|---|---|---|
| R | 470 Ω | min | 1.38 | 1.54 | 1.71 | 1.88 | 2.05 | 2.21 | 2.38 | 2.89 |
| R | 470 Ω | mitte | 1.05 | 1.21 | 1.38 | 1.54 | 1.71 | 1.88 | 2.05 | 2.55 |
| R | 470 Ω | max | 0.72 | 0.88 | 1.05 | 1.21 | 1.38 | 1.54 | 1.71 | 2.21 |
| G | 200 Ω | min | 0.75 | 0.98 | 1.22 | 1.47 | 1.72 | 1.98 | 2.25 | 3.05 |
| G | 200 Ω | mitte | 0.36 | 0.54 | 0.75 | 0.98 | 1.22 | 1.47 | 1.72 | 2.51 |
| G | 200 Ω | max | 0.10 | 0.20 | 0.36 | 0.54 | 0.75 | 0.98 | 1.22 | 1.98 |
| B | 100 Ω | min | 0.42 | 0.70 | 1.03 | 1.38 | 1.75 | 2.13 | 2.52 | 3.74 |
| B | 100 Ω | mitte | 0.08 | 0.21 | 0.42 | 0.70 | 1.03 | 1.38 | 1.75 | 2.92 |
| B | 100 Ω | max | 0.01 | 0.03 | 0.08 | 0.21 | 0.42 | 0.70 | 1.03 | 2.13 |

Das Skript rechnet zusätzlich R 200 Ω, G 470/100 Ω, B 0 Ω und R_on 40 Ω (ANNAHME typisch). Mit 40 Ω liegen die
Ströme 5–30 % höher. Gewählt sind die Werte oben: R wie bisher, G 200 Ω (Grün ist sehr effizient), B 100 Ω.
Spitzenstrom bei frischer Zelle (3.0 V, min-Exemplar, R_on typ) bis 3.3 mA, spezifiziert ist der Pin bei 2 mA.
Einen Grenzwert pro Pin nennt das Datenblatt nicht (S.18, Tab. 7.1, nur Spannungen) → **ANNAHME** zulässig.
Die Firmware begrenzt den Mittelwert per PWM.

### 1.4 Sichtbarkeit und verfügbare Farben

Helligkeit linear aus Iv-min bei 5 mA (S.5) geschätzt: **R 14, G 50, B 12 mcd/mA** (**ANNAHME**: Die NationStar-Kurve
„Relative Luminous Intensity vs Forward Current“, S. 3/13, ist konkav, linear ist daher bei kleinem Strom konservativ).
Bezugswert ist die bisher geplante rote KT-0603R mit 470 Ω an 3.0 V: ≈ 2 mA × 145 mcd/20 mA ≈ **15 mcd**
(`KENTO_KT-0603R_Datasheet_LCSC-2018-10.pdf`, Iv 145–300 mcd @20 mA, linear skaliert, ANNAHME).
Schwellen (**ANNAHME, PROTOTYP-PRÜFUNG** mit Fenster im hellen Büro): „voll“ ≥ 10 mcd, „erkennbar“ ≥ 3 mcd.

| VDD beim Blinken | Rot | Grün | Gelb (R+G) | Blau (typ. Exemplar) | Blau (VF-max-Exemplar) | Cyan/Magenta/Weiss |
|---|---|---|---|---|---|---|
| ≥ 2.95 V | voll | voll | voll | voll | voll | voll |
| 2.75–2.95 V | voll | voll | voll | voll | erkennbar (3–10 mcd) | eingeschränkt |
| 2.55–2.75 V | voll | voll | voll | erkennbar | ab ≈ 2.72 V erkennbar, darunter aus | nicht verwenden |
| 2.40–2.55 V | voll | voll (VF-max: 2.4 V ≈ 5 mcd) | voll | aus/sehr schwach | aus | nicht verwenden |

Zellspannung über die Lebensdauer (`Panasonic_CR2032_Datasheet_2026-02.pdf` S.1, abgelesen, **ANNAHME**):
Bei 190 µA Dauerlast und 20 °C liegt die Spannung bis ≈ 900 h von ≈ 1150 h bei ≈ 2.9–3.0 V, 2.6 V wird bei ≈ 1050 h
erreicht (gleiche Lesart wie `scripts/concept_energy.py`, CUTOFF_FACTOR). Bei 1 mA Dauerlast und 50 % Entladung
sind es ≈ 2.8 V („Operating voltage vs. load resistance“, 3 kΩ). Ein Blink von 20 ms wird vom 200-µF-Puffer gestützt,
VDD liegt dann dazwischen. Folgerung: **Blau ist bei typischen Exemplaren während ≈ 80 % der Lebensdauer voll
sichtbar**, in den letzten ≈ 10–20 % wird es schwach, Rot, Grün und Gelb bleiben bis zur Abschaltung (2.4 V) verfügbar.
Bei Kälte sinkt die Zellspannung und VF steigt – für den Innenraum nicht massgebend.

**Firmware-Farbtabelle (Vorschlag für REQ-UI-02):**
1. VDD mit dem Batteriemonitor (`TI_CC2340R5_Datasheet_SWRS272F.pdf` Abschn. 8.8) unter LED-Last messen, gleitend mitteln.
2. ≥ 2.85 V: alle Farben, Helligkeitsabgleich per PWM (Grün ≈ ¼ Tastgrad gegenüber R/B).
   2.65–2.85 V: Blau mit 100 % Tastgrad, blau-codierte Zustände zusätzlich am Blinkmuster erkennbar.
   < 2.65 V: kein Blau; Ausweichfarben (z. B. Pairing = gelb schnell, verbunden = grün doppelt).
3. Batterie tief und Fehler immer **rot**, Messung bestätigt **grün**. Kritische Zustände hängen also nie von Blau ab.
   Für „Giessen nötig“ ist Blau naheliegend (Wasser). Dann gilt unter der Schwelle eine Ausweichfarbe (z. B. gelb/orange).
   Das entscheidet der Auftraggeber.
4. Mittlerer LED-Strom je Blink ≤ 3 mA (Mischfarben per PWM), LEDs während der Feuchtemessung aus.
5. Schwellen nach der Kennlinienmessung (1.2) festlegen. Optional: DIO6/DIO20 sind analogfähig
   (`TI_CC2340R5_Datasheet_SWRS272F.pdf` S.7). Eine Messung der LED-VF pro Exemplar wäre denkbar (**ANNAHME**, nicht ausgearbeitet).

### 1.5 Geprüfte Alternativen

| Lösung | Bewertung |
|---|---|
| **Firmware-Farbtabelle nach VDD (empfohlen)** | 0 Bauteile, 0 µA, deckt die ganze Lebensdauer für R/G/Y und den grössten Teil für B ab |
| Nur Rot/Grün (Gelb gemischt), Blau unbeschaltet | gleiche RGB-LED, nur 1 zusätzlicher Pin (DIO20, siehe 1.6) oder 2 Basic-LEDs (KT-0603R C2286 + KT-0805G C2297, ohne Extended-Gebühr, aber 2 Lichtquellen hinter dem Fenster, Mischung schlechter). Rückfallebene, falls der Pinumbau (1.6) abgelehnt wird |
| Ladungspumpe nur für die LED, z. B. TI LM2664 (C108573, Extended, 0.334 USD, Lager 162 442) als Invertierer: Kathoden auf −VDD | V+ 1.8–5.5 V, IQ 220 µA typ/500 µA max, **Shutdown 1 µA typ** (`TI_LM2664_Datasheet_SNVS005E.pdf` S.5, 6.5, bei V+ = 5 V) → +1 µA auf ein Schlafbudget von 3 µA (REQ-ENE-09), sonst Speisung über einen weiteren GPIO (es ist keiner frei); + 2 Kondensatoren 3.3 µF, ≈ +0.35 CHF + Extended-Gebühr, Schaltstörungen nahe Messkette und Antenne. **Verworfen.** Ein Boost-Wandler hätte zusätzlich eine Spule – ebenfalls verworfen |
| Bootstrap-Kondensator (GPIO hebt die Anode über VDD) | braucht einen weiteren Pin und eine Diode, Helligkeit schwer reproduzierbar → verworfen |

### 1.6 Pinplan CC2340R52 QFN24 (Ergänzung zu CONCEPTS.md 2.2)

Ausgangslage: 10 freie DIO, alle belegt ausser **DIO20** (Reserve, im Bootloader UART RX). Die LED belegt DIO6 (=
UART TX). Drei Kanäle brauchen **2 zusätzliche Pins**.

| Pin | DIO | bisher | neu | Begründung / Konflikt |
|---|---|---|---|---|
| 19 | DIO6 | LED rot + UART TX | **LED_R** + UART TX | unverändert; TX wird vom CC2340 getrieben, die LED stört nicht (TRM S.464 Tab. 8-38) |
| 6 | DIO13 | TMP_PWR | **LED_G** | wird frei, weil TMP_PWR auf DIO12 wandert. Im ROM-Bootloader ist DIO13 SPI_PICO (Eingang, TRM S.464). Ohne Takt auf DIO8 wird SPI nicht ausgewählt → unkritisch. PWM-fähig: T0C0N (DS S.9) |
| 5 | DIO12 | OSZ_PWR | **SENS_PWR** = OSZ_PWR + TMP_PWR | High-Drive, VOH ≥ 2.47 V bei 10 mA (DS S.31). Last: LVC1G14 ≈ 0.9 mA + TMP1075 + Pull-ups 2 × 0.64 mA bei low-Pegel → < 3 mA. Folgen: Oszillator läuft während der TMP-Wandlung (4.5–7 ms one-shot, `TI_TMP1075_Datasheet_SBOS854F.pdf` S.6) → < 0.001 µA im Tagesmittel. Ablauf in der Firmware: zuerst TMP lesen, dann Feuchtemessung (TMP im Shutdown, I²C ruhig). **PROTOTYP-PRÜFUNG:** Einfluss auf die Ratiometrie |
| 9 | DIO20 | Reserve / UART RX | **LED_B** + UART RX | PWM-fähig: T1C0 (DS S.11). Konflikt: Der Adapter treibt RX über 2 × 100 kΩ, die LED zieht den Pin von VDD hoch, siehe unten |
| – | – | – | kein Reservepin mehr | Folge: Für Erweiterungen bleibt nur QFN40 (C5914214, laut CONCEPTS 2.2 wenig Lager) |

**UART-RX-Konflikt (SPICE Teil 2, `led_rx_conflict.cir`):** Pinspannung bei RX = 0 V über 200 kΩ, blaue LED + 100 Ω an der Adapterspannung:

| VDD Adapter | VF-min | VF-mitte | VF-max | Schaltschwelle high→low (DS S.31/32) |
|---|---|---|---|---|
| 1.8 V | 0.05 V | 0.01 V | 0.00 V | 0.59–0.91 V (VDDS 1.8 V) |
| 2.0 V | 0.16 V | 0.05 V | 0.01 V | – |
| 2.5 V | 0.57 V | 0.40 V | 0.24 V | – |
| 3.3 V | **1.31 V** | 1.12 V | 0.93 V | 1.26–1.79 V (VDDS 3.0 V) |

Mit dem bisher geplanten 3.3-V-Adapter erkennt RX ein Low **nicht sicher** (das min-Exemplar liegt über 1.26 V).
**Auflage:** Der Dummy-Zellen-Adapter speist **VDD = 1.8–2.0 V** (CC2340 ab 1.71 V, DS S.18, Tab. 7.3; Flash-Grenzen
nur bei VDDS = 3.0 V angegeben, eine Mindestspannung für das Schreiben ist nicht genannt, S.20–21 – **ANNAHME** zulässig)
und arbeitet mit **1.8-V-UART-Pegeln**: TX des CC2340 erreicht dann nur 1.8 V, und 3.3-V-Pegel vom Adapter würden
„VDDS + 0.3 V“ überschreiten (DS S.18). Betrifft nur das Werkzeug, nicht die Kosten pro Sensor. Grün an DIO20 wäre
schlechter (0.22 V bei 1.8 V, VF-min), deshalb Blau an RX. Die Extrapolation unter 1 mA ist eine **ANNAHME** →
**PROTOTYP-PRÜFUNG:** 20 × Programmieren mit bestückter LED, 1.8 V und 2.0 V. Die Messbarkeit des Stroms
(REQ-ENE-07) und das Schutzkonzept (S2-K01) ändern sich nicht. Die Adapterspannung mit `sicherheit` abstimmen.

**Rückfallebene**, falls der TMP_PWR-Umbau abgelehnt wird: nur R (DIO6) + G (DIO20, gleiche Adapter-Auflage, knapperer
Abstand), Blau unbeschaltet → Farben Rot/Grün/Gelb.

Layout: LED_x-Leitungen weg vom Sondenknoten und von den Cref-Leitungen (DIO8/DIO11). LED, Vorwiderstände und
Leitungen ausserhalb des AN043-Antennen-Keepouts. Das P3-Fenster liegt bei z ≈ 29.6–38 mm
(`docs/design/DESIGN_PROPOSALS.md` Kap. 3) und damit nahe am oberen Antennenbereich → Lage mit `mechanik` und im Layout festlegen.

### 1.7 Kosten (Kostenmodell `scripts/concept_costs.py`, BOM-Variante im Scratch gerechnet, JLC-Daten 2026-11-07)

Änderung gegenüber BOM_A32: LED rot C2286 (2 Lötstellen) + 470 Ω → C7496855 (4 Lötstellen) + 470 Ω C25117 + 200 Ω C25087 + 100 Ω C25076.

| Szenario | A-32 Basis | A-32 RGB (C7496855) | Differenz |
|---|---|---|---|
| Serie 20/16/15: Stück CHF | 7.071 | 7.089 | **+0.018** |
| Serie: Einmal CHF | 96.77 | 99.56 | **+2.79** (Extended-Gebühr 3.07 USD) |
| Serie: Bestellung total CHF | 202.83 | 205.89 | +3.06 |
| Serie: Vollkosten/Sensor CHF | 13.52 | 13.73 | **+0.20** |
| Prototyp 5/5: total CHF | 134.64 | 137.49 | +2.85 |

Zweitquelle C965840: Stück 7.095 CHF, total Serie 206.07 CHF. REQ-FAB-04 (≤ 10 CHF) bleibt mit Reserve erfüllt.
Die Basiswerte stimmen mit CONCEPTS.md 2A überein (7.07 / 202.83 / 134.64) → das Modell ist unverändert.

### 1.8 Energie (`scripts/energy_budget.py` / `concept_energy.py`, LED_I variiert, A-32, 1 min)

| LED-Strom während Blink | LED-Anteil pess. A (Definition wie CONCEPTS 2.5, vor +20 %) | Laufzeit pess. DS |
|---|---|---|
| 2 mA (bisher) | 2.0 % | 17.0 Mt. |
| 3 mA (**Regel RGB**) | 3.0 % | 16.9 Mt. |
| 4 mA | 3.9 % | 16.9 Mt. |
| 6 mA (Weiss ohne PWM) | 5.8 % → **verletzt REQ-UI-03** | 16.7 Mt. |

→ Firmware-Regel „mittlerer LED-Strom je Blink ≤ 3 mA“ hält REQ-UI-03 ein. Der Schlafstrom ändert sich nicht (LED-Pins
high bzw. hochohmig, 0 V an der LED). Blinkmuster wie bisher (6 × 20 ms/Tag + „Giessen nötig“ 1×/min, 5 ms).
Längere oder häufigere Farbanzeigen müssen neu gerechnet werden.

### 1.9 LED-Position, Abstrahlwinkel, Lichtleiter (Empfehlung an `mechanik`)

- 1615 strahlt nach oben ab (Top-View), 2θ½ = 120° (S.5). Die LED liegt auf der Platinenseite zum Fenster, ihr Mittelpunkt
  hinter dem Schwerpunkt des Tropfens (unterer, bauchiger Teil).
- Ausleuchtung ohne Lichtleiter: Durchmesser des Halbwertkegels ≈ 2·d·tan 60° ≈ 3.5·d. Für das P3-Fenster 5.2 × 8.4 mm
  → **d ≈ 1.5–2.5 mm** von der LED-Oberseite bis zur Innenfläche des Fenstereinsatzes (Rechnung; **ANNAHME** zur Wirkung).
- Bis d ≈ 5 mm: Lichtschacht mit hellen/weissen Wänden um die LED, damit kein Licht ins Gehäuse streut und der
  Kopf nicht von innen leuchtet. Bei grösserem Abstand Lichtleiter (transluzentes PETG/ASA, D-009). Für lange Leiter wurde
  bei P4 schon wenig Helligkeit befürchtet (`phase3_design_mechanik.md` M-Befund P4).
- **Mischung:** Die drei Chips liegen im Gehäuse ≈ 0.5–1 mm auseinander (S.4, Zeichnung). Gelb, Cyan und Weiss
  wirken nur mit **Diffusor** einheitlich: transluzentes, mattes Fenster ≥ 1 mm oder raue Innenseite. **PROTOTYP-PRÜFUNG**
  mit Muster (Farbsäume, Helligkeit von schräg oben, REQ-UI-05).
- Fenster und Lichtschacht nicht in den Antennen-Keepout ragen lassen (Kunststoff mit hoher εr direkt an der Antenne vermeiden, AN043).

---

## 2 Gateway-Antenne intern

### 2.1 Ausgangslage

Seeed XIAO ESP32-S3 Plus (CHF 8.90, pi-shop.ch, an Lager, 2026-11-07): Das Board hat **keine Antenne auf der Platine**.
Es gibt nur einen U.FL-Anschluss (Seeed Wiki „Getting Started with XIAO ESP32S3 Series“, Pinbelegung „U.FL-R-SMT1“).
Laut Shop gehört eine „2.4GHz Rod antenna“ dazu, die Stückliste im Shop nennt aber nur das Board → Lieferumfang am
Muster prüfen. Seeed-Stabantenne: 2.81 dBi Spitze, 134 mm lang (Händlerangabe openelab.io, kein Herstellerdatenblatt
lokal). Seeed FPC-Antenne A-02 für XIAO ESP32-S3: 2400–2500 MHz, **1.16 dBi Spitze**, VSWR ≤ 4.5 (Händlerangaben
unmannedtechshop.co.uk / pakronics.com.au, **kein Herstellerdatenblatt lokal**).

### 2.2 Optionen

| Option | Gewinn | Kosten CH | Bewertung |
|---|---|---|---|
| a) Stabantenne aussen (bisher) | 2.81 dBi | im Lieferumfang (prüfen) | vom Auftraggeber nicht gewünscht |
| **b) XIAO S3 Plus + FPC A-02 innen aufgeklebt** | 1.16 dBi | **Preis CH nicht gefunden** (ANNAHME CHF 2–4, Bezug Seeed/EU-Händler) | **empfohlen**: Gewinn ≤ Stabantenne → EIRP nicht höher als mit der Stabantenne |
| c) XIAO S3 Plus + TE Linx ANT-2.4-FPC-LV100UF innen | 4.3 dBi (DigiKey) | **CHF 3.77** @1, 3.643 @10, Lager 944 (digikey.ch, 2026-11-07) | gut erhältlich. Gewinn > Stabantenne → WLAN-Sendeleistung in der Firmware um ≥ 1.5 dB begrenzen (EIRP-Grenze, **ANNAHME**, mit `sicherheit`/Konformität klären). Datenblatt **nicht ladbar** (te.com „Access Denied“) → gemeldet |
| d) Board mit PCB-Antenne, z. B. ESP32-S3-DevKitC-1 (WROOM-1) | keine Angabe im lokalen Modul-Datenblatt | N8R8 CHF 12.42, **Lager 0** (digikey.ch); N16R8 bei CH-Händlern nicht gefunden | **nicht empfohlen**: Espressif verlangt für die PCB-Antenne „a clearance of at least 15 mm … in all directions“ im Gehäuse (`Espressif_ESP32-S3_HardwareDesignGuidelines_master-2026-11.pdf` Abschn. 1.4.7, Doku-S. 30 / PDF-S. 33) und die Antenne am Platinenrand. G1 ist nur 20 mm hoch (DESIGN_PROPOSALS Kap. 5) → Gehäuse wird grösser; Board grösser und teurer; N8R8 hat nur 8 MB Flash statt 16 MB |
| e) XIAO ESP32-C6 (Keramikantenne auf dem Board) | – | CHF 7.00–7.90 | 4 MB Flash zu knapp (`research_gateway.md` Tab. Varianten) |

Für ESP32-S3-WROOM-1U mit externer Antenne empfiehlt Espressif „maximum gain does not exceed 2.33 dBi“ (Gewinn der
zertifizierten Antenne; `Espressif_ESP32-S3-WROOM-1_Datasheet_v1.8.pdf` S.44). Für die XIAO-Zulassung ist die
zugrunde gelegte Antenne nicht belegt → Regel: **Antennengewinn ≤ mitgelieferte Antenne**, sonst Sendeleistung begrenzen.

### 2.3 Linkbudget grob (Sensor → Gateway; der Rückweg ist unkritisch, ESP32-S3 sendet BLE mit bis +20 dBm, WROOM-1 DS S.34 Tab. 7-7)

Annahmen: Raum 10 × 15 m, ungünstigster Abstand 18 m (RB-01, REQ-RF-02). Ausbreitung nach ITU-R P.1238, Büro,
L = 20 log f[MHz] + N log d − 28 mit **N = 30** (tabelliert für 1.8–2.0 GHz, auf 2.44 GHz übertragen = **ANNAHME**)
→ **L(18 m) = 77.4 dB**, L(10 m) = 69.8 dB. Empfindlichkeit ESP32-S3 BLE 1 Mbit/s **−96.5 dBm**
(`Espressif_ESP32-S3-WROOM-1_Datasheet_v1.8.pdf` S.36 Tab. 7-12; gleicher Chip auf dem XIAO = ANNAHME).
Sensor: 0 dBm, CC2340 einstellbar bis +8 dBm (`TI_CC2340R5_Datasheet_SWRS272F.pdf` S.1). Antennengewinn
Sensor: AN043-IFA 4.5–5.3 dB auf dem Dongle (`TI_AN043_SmallPCBAntenna_SWRA117D.pdf` Abschn. 6, Tab. 6). Im Topf
nahe Erde und Blättern als **ANNAHME** 0 dBi nominal / −6 dBi pessimistisch. Gateway: FPC-Gewinn −2 dB durch Gehäuse und
Umgebung (ANNAHME), U.FL-Kabel 0.5 dB (ANNAHME), pessimistisch zusätzlich −5 dB durch ungünstige Ausrichtung (ANNAHME).

| Fall | P_rx bei 18 m | Reserve über −96.5 dBm | REQ-RF-03 (≥ 10 dB, Soll) |
|---|---|---|---|
| Stab, nominal | −75.1 dBm | 21.4 dB | ✔ |
| **FPC A-02 innen, nominal** | −78.8 dBm | **17.8 dB** | ✔ |
| Linx 4.3 dBi innen, nominal | −75.6 dBm | 20.9 dB | ✔ |
| Stab, pessimistisch | −86.1 dBm | 10.4 dB | knapp ✔ |
| **FPC A-02 innen, pessimistisch** | −89.8 dBm | **6.8 dB** | ✘ → Sensor auf +4 dBm: 10.8 dB ✔ |

Der Unterschied Stab ↔ FPC innen beträgt ≈ 3.6 dB (ANNAHME). Bei N = 30 entspricht das bei gleicher Reserve ≈ 25 %
weniger Reichweite. Bei 18 m reicht es nominal deutlich. Am schlechtesten Platz hilft die Sendeleistungsregelung
(REQ-RF-03 „Sendeleistung anpassbar“): +4 dBm (7.9 mA statt 5.1 mA, DS S.20 Tab. 7.10) verkürzt die Laufzeit eines
solchen Sensors pess. DS von 17.0 auf **16.5 Monate** (Energiemodell, TX-Ströme × 1.55, ANNAHME für den GLDO-Fall).
Dämpfung durch Schatten, Möbel und Personen ist hier nicht modelliert und muss in die 10-dB-Reserve passen → **PROTOTYP-PRÜFUNG**.

### 2.4 Platzierungsregeln (Empfehlung an `mechanik`)

1. FPC auf die **Innenseite einer Kunststoffwand kleben** (oben bzw. Front, gegenüber der USB-C-Rückwand). Der strahlende
   Teil hat **≥ 15 mm Freiraum** zu USB-C-Buchse/-Kabel, XIAO-Platine (Masse), RTC-Modul, Schrauben, Gewindeeinsätzen
   und Netzteilkabel. Die 15-mm-Regel stammt aus der Espressif-Richtlinie für PCB-Antennen (HDG Abschn. 1.4.7) und gilt
   hier als **ANNAHME** sinngemäss. Händlerhinweis A-02: „keep the radiating FPC section away from metal and large ground planes“.
2. Nicht parallel über oder unter einer Massefläche, nicht zwischen XIAO und Wand einklemmen. Kabel ohne scharfe
   Knicke, U.FL einseitig aufsetzen (Seeed Wiki). Kabel mit Zugentlastung, damit der U.FL-Stecker nicht abzieht.
3. ASA-Wand direkt an der FPC ist üblich, aber die Wanddicke verstimmt leicht (εr, **ANNAHME**). Keine metallischen
   oder russhaltigen Farben/Inlays im Antennenbereich (Gateway in Grau/Hellblau, D-009: Pigment prüfen, **ANNAHME**).
4. Ausrichtung: Die Sensor-IFA steht senkrecht im Topf. FPC am Gateway ebenfalls senkrecht ausrichten (**ANNAHME**, am Muster
   mit RSSI in 2 Lagen vergleichen). Gateway erhöht und möglichst zentral im Raum aufstellen (Bedienungsanleitung).
5. Nähe zum WLAN-Access-Point beachten: Das ESP32-S3 teilt sich Radio und Antenne für WLAN und BLE (CONCEPTS 5.1 Koexistenz).

**PROTOTYP-PRÜFUNG Gateway:** RSSI und Paketverlust eines Sensors an der ungünstigsten Stelle (18 m), Stab gegen FPC
innen, 2 Ausrichtungen. Danach REQ-RF-03 nachweisen und die Werkseinstellung der Sensor-Sendeleistung festlegen.

### 2.5 Empfehlung Gateway

**XIAO ESP32-S3 Plus beibehalten, Stabantenne durch eine innen aufgeklebte FPC-Antenne mit Gewinn ≤ 2.81 dBi ersetzen
(Seeed A-02).** Ist A-02 nicht beschaffbar, Linx ANT-2.4-FPC-LV100UF (CHF 3.77) mit begrenzter WLAN-Sendeleistung.
Mehrkosten ≈ CHF 2–4 pro Gateway (ANNAHME für A-02). Kein Boardwechsel.

---

## 3 Offene Punkte und Abstimmungen

| Nr. | Punkt | Mit | Art |
|---|---|---|---|
| RGB-1 | I-U-Kennlinie C7496855 0.05–5 mA (10 Stück), `led_models.inc` ersetzen, Farbtabellen-Schwellen festlegen | Elektronik | PROTOTYP-PRÜFUNG |
| RGB-2 | Pinumbau TMP_PWR → DIO12 (SENS_PWR), Einfluss auf die Ratiometrie | Elektronik/Firmware | PROTOTYP-PRÜFUNG, Entscheid Projektleiter |
| RGB-3 | Dummy-Zellen-Adapter: VDD 1.8–2.0 V, 1.8-V-UART; 20 × Programmieren mit bestückter blauer LED | Elektronik, **sicherheit** (Adapter = Schutzkonzept S2-K01) | PROTOTYP-PRÜFUNG |
| RGB-4 | Zuordnung Zustand → Farbe inkl. Ausweichfarben (REQ-UI-02), Farbe „Giessen nötig“ | Auftraggeber/Firmware | Entscheid |
| RGB-5 | Fenster/Lichtschacht/Diffusor, d = 1.5–2.5 mm, Lage zum Antennen-Keepout | **mechanik** | Abstimmung |
| GW-1 | Lieferumfang XIAO S3 Plus (Stab/FPC?), Bezugsquelle und CH-Preis Seeed A-02 | Einkauf/Orchestrator | offen |
| GW-2 | Datenblatt Linx ANT-2.4-FPC-LV nicht ladbar (te.com Access Denied); A-02 ohne Herstellerdatenblatt | Orchestrator | gemeldet |
| GW-3 | EIRP/Konformität bei Fremdantenne (Gewinn > mitgelieferte Antenne) | **sicherheit** | Abstimmung |
| GW-4 | FPC-Lage im Gateway-Gehäuse G1 (≥ 15 mm zu USB-C, XIAO, RTC) | **mechanik** | Abstimmung |

Nicht gemacht: keine Änderung an `CONCEPTS.md`, `scripts/concept_costs.py`, `scripts/energy_budget.py` (Varianten nur im
Scratch gerechnet, Ergebnisse oben). Die Zeilen in `INDEX_rgb.csv` sind noch nicht in `INDEX.csv` übernommen. Kein Commit.

## Quellen (Web, Abruf 2026-11-07)
- pi-shop.ch XIAO ESP32-S3 Plus CHF 8.90 – https://www.pi-shop.ch/seeed-studio-xiao-esp32-s3-plus
- Seeed Wiki XIAO ESP32S3 – https://wiki.seeedstudio.com/xiao_esp32s3_getting_started/
- Seeed FPC A-02 (Händler) – https://www.unmannedtechshop.co.uk/blogs/knowledge-base/xiao-fpc-antenna-a01-vs-a02-esp32-c3-c5-s3 ;
  https://www.pakronics.com.au/products/2-4ghz-fpc-antenna-1-16dbi-for-xiao-esp32-s3-ss318020968
- Seeed Stabantenne 2.81 dBi (Händler) – https://openelab.io/es/products/seeed-103990623-2-4ghz-rod-antenna-xiao
- DigiKey CH Linx ANT-2.4-FPC-LV100UF – https://www.digikey.ch/en/products/detail/te-connectivity-linx/ANT-2-4-FPC-LV100UF/16570602
- DigiKey CH ESP32-S3-DevKitC-1 – https://www.digikey.ch/en/products/result?keywords=ESP32-S3-DevKitC-1
- ITU-R P.1238 (Büro N = 30 bei 1.8–2.0 GHz) – https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.1238-3-200304-S!!MSW-E.doc ;
  Übersicht https://Www.Wikipedia.org/wiki/ITU_model_for_indoor_attenuation
- JLC-Teilesuche (API selectSmtComponentList) für C7496855, C965840, C158099, C404280, C25076, C25087, C25117, C2286, C2297, C108573
