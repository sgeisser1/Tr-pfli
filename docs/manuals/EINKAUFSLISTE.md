# fluidi – Einkaufsliste (alles ausser JLC)

| | |
|---|---|
| Stand | 2026-11-09, erzeugt von `.venv/bin/python scripts/einkaufsliste.py` aus `docs/manuals/EINKAUFSLISTE.csv` (nicht von Hand ändern) |
| Umfang | Sensor (Prototyp 5 + Serie 15), Gateway (D-028 ohne RTC, D-029 SHT40-Breakout), Werkstatt (USB-UART, Testzellen) |
| Belege | `docs/references/Haendler_Einkauf_Auszug_2026-11-09.txt`, `docs/references/pi-shop_Gateway-Teile_Auszug_2026-11-08.txt`, Register `docs/datasheets/INDEX.csv` |
| Nicht abrufbar | digitec/galaxus, mouser.ch, distrelec.ch, digikey.ch, conrad.ch, brack.ch, toppreise.ch (Bot-Sperre/403) → Preise von dort sind **ANNAHME** |
| Hinweis | Keine Bestellung ausgelöst. Preise inkl. MWST, Lager = Anzeige am Abruftag |

## 1 Fazit

- Warenwert geplant **220.93 CHF** + Versand **27.80 CHF** = **248.73 CHF** (davon 68.84 CHF Preis-ANNAHME; ohne Vergussmasse S8 = Platzhalter, ohne Programmieradapter-Teile W2, ohne JLC).
- **Händler mit Bestellung: 5** (bastelgarage.ch, pi-shop.ch, galaxus.ch, offen (Normteile-/Dichtungs-Fachhandel), Digi-Key CH (laut phase5_gateway_led.md)). Kern sind **zwei** CH-Händler: bastelgarage.ch und pi-shop.ch.
- Ein Händler weniger möglich: Zellen bei bastelgarage.ch (Varta statt Panasonic, Entscheid Auftraggeber, S1).
- Offen: Quelle O-Ringe AS568-019 Silikon, Schrauben ISO 7045 M2×3 PH1 und ISO 7380 M2.5×8, Silikonplatte, Silikonfett (ein Normteile-/Dichtungshändler, Kap. 6); Filament grau nicht an Lager; microSD nicht an Lager.

## 2 Klimasensor-Breakout Gateway (D-029, G6)

Platz (CAD `mechanical/gen/fluidi_gateway_pi.py`, Konstante `CLIMA`, Prüfung 11/14 in
`mechanical/gateway_pi/check_gateway_pi.txt`): Klimakammer innen **x 8.0 × y 38.0 × z 16.0 mm** (x 32…40, Wand 2 mm).
Das Modul steht hochkant in der y-z-Ebene in zwei Nutpfosten (Nut 1.6 + 0.3 mm, 1.5 mm tief), Sensorseite +x zur
Stirnwand; Platzhalter `MW` 24 (y) × `MH` 14 (z), Unterkante z 3.0, Bauteile vorn ≤ 2.5 mm (`PART_F`), hinten ≤ 1.0 mm
(`PART_B`). Hochkant ist z ≤ 14 nutzbar (z 3…17 in 2…18), flach liegend nur 8 mm (x).

| Kandidat | Masse (Quelle) | Elektrik (Quelle) | Bezug CH (Abruf 2026-11-09) | Passt? |
|---|---|---|---|---|
| **DFRobot Fermion SHT40 SEN0428** | **14.0 × 17.0 mm**, 2 × Ø2.0 im Raster 10.0, 4 Lötaugen VCC/GND/SCL/SDA an einer 14-mm-Kante (`docs/datasheets/DFRobot_SEN0428_Dimensions_V0.1.png`; Wiki „Dimension 14×17mm“) | VCC 3.3–5 V (Wiki); LDO → „3V“, Pegelwandler 2 × 2N7002, 10 kΩ Pull-ups beidseitig (`docs/datasheets/DFRobot_SEN0428_Schematic_V0.1.pdf`); SHT40 VDD 1.08–3.6 V (`docs/datasheets/Sensirion_SHT4x_Datasheet_V7.3.pdf` S. 9); Adresse 0x44 (DFRobot-Bibliothek `DFRobot_SHT40.h` Z. 20, SHT40-AD1B; Sensirion S. 21/22) | bastelgarage.ch Art. 421989, **CHF 11.90, lagernd** | **ja**, hochkant 17 (y) × 14 (z) |
| Adafruit SHT41 STEMMA QT (5776) | 25.4 × 17.8 mm (1.00 × 0.70 in, `docs/datasheets/Adafruit_5776_SHT41_FabPrint_2023-07.png`) | Regler + Pegelwandler (`…_Schematic_2023-07.png`) | play-zone.ch Art. ada-5776, CHF 9.90, > 10 an Lager (Versand ab 300 CHF frei, Tarif nicht abgelesen) | nein: 17.8 > 16 (hochkant), > 8 (flach) |
| Seeed Grove SHT41 (bisher G6) | 20 × 40 mm (`docs/references/Seeed_Grove-SHT4x_Wiki_Auszug_2026-11-08.txt`) | Schaltplan nicht lokal | pi-shop.ch Art. 12042, CHF 8.90, nicht an Lager | nein: 40 > 38 |

Gesucht, aber ohne CH-Quelle: 7Semi SHT40/SHT41-Kleinstbreakouts (nur indische Händler), Generika ohne Schaltplan.
pi-shop.ch führt kein weiteres SHT4x-Breakout (Suche „sht40“ 2026-11-09: nur CO2-Sensor/E-Paper-Kit, Beleg im Auszug).

**Empfehlung: DFRobot SEN0428** – einziges gefundenes SHT4x-Breakout mit Herstellermass und Schaltplan, das in die
Kammer passt, ab Lager in der Schweiz, beim selben Händler wie Muttern/Einsätze/Kleber (kein zusätzlicher Versand).

**Masse für die Mechanik (CAD nicht geändert):** Platine 14.0 × 17.0 mm; hochkant **17.0 in y, 14.0 in z** → `CLIMA['MW']`
24 → 17 (Nutpfosten nachführen), `MH` 14 bleibt; Bohrungen Ø2.0 im Abstand 10.0 an der Kante gegenüber den Lötaugen
(alternativ Befestigung M2 statt Nut); Lötaugenreihe an einer 14-mm-Kante → die Litzen verlassen das Modul an einem
y-Ende (Kabelkanal y −3.5/z 10.5 → Lötaugen zur Kammermitte bzw. zum Kanal legen). **Platinendicke und Bauteilhöhe
sind nicht angegeben** (Händler „0.5 mm“ unplausibel) → am Muster messen, bis dahin Platzhalter 1.6 mm + 2.5 mm
Bauteile behalten. Bauteile laut Masszeichnung nur auf der Sensorseite.

**Befund (klein):** Der vom DFRobot-Wiki für SEN0428 verlinkte Schaltplan trägt Titel und Bauteil „SHTC3“
(SKU-D008, Schwesterprodukt SEN0414). Topologie (LDO, 2N7002, 10 kΩ) plausibel, die Sensor-Pinbelegung im Plan gilt
nicht für den SHT40. **PROTOTYP-PRÜFUNG:** 3V-Schiene messen, Pull-ups messen, `i2cdetect -y 1` zeigt 0x44, Messwerte
plausibel (Treiber `climate.py`, D-017). Anschluss: VCC an Pi-3V3 (Pin 1), GND, SDA/SCL Pins 3/5.

## 3 USB-UART für den Programmieradapter (FW-T3)

Anforderung (`docs/manuals/INSTALL_FIRMWARE_TOOLS.md`, `hardware/programmer/README.md`): VIO extern 2.0 V aus dem
Adapter, kein Rückstrom, ROM-Bootloader 19 200–57 600 Baud, +5 V vom USB für die Adapterregler.

| Option | Bezug (Abruf) | Kosten inkl. Versand | Bewertung |
|---|---|---|---|
| A Waveshare **CH343 USB UART Board** SKU 21440–21443 (TOOL-UART1, bisher geplant) | waveshare.com USD 3.49 (2026-11-07), Seite JS-basiert, Lager/Versand nicht ablesbar; eckstein-shop.de Art. WS21443 EUR 4.15, „ca. 3 Wochen“, Seite meldet „nicht in Ihr Lieferland“ (Land nicht erkennbar); kein CH-Händler gefunden (pi-shop.ch „ch343“: nur Geräte mit CH343-Chip, z. B. Industrial USB TO TTL mit festem 3.3/5-V-Pegel; bastelgarage.ch, play-zone.ch: keine Treffer) | ≈ 3–4 CHF + Auslandsversand **ANNAHME 10–25 CHF** (programmer/README Kap. 6) | elektrisch belegt (CH343-Datenblatt), aber eigener Auslandsversand |
| **B Waveshare PL2303 USB UART Board (type A) V2** (PL2303GS, TOOL-UART2) | **pi-shop.ch Art. 11757, CHF 8.90, Sofort-Versand** (2026-11-09) | **8.90 CHF, kein Zusatzversand** (mit G2/G3 bei pi-shop.ch) | **freigegeben mit Bedingungen** (Elektronik 2026-11-09), siehe unten |
| C Adafruit CH9102F Friend / Waveshare Industrial USB TO TTL (CH343G) | pi-shop.ch CHF 7.90 / 12.90 | – | **ungeeignet**: Pegel fest 3.3/5 V per Schalter, kein externes VIO |

Begründung B gegen Datenblatt (`docs/datasheets/Prolific_PL2303GS_Datasheet_Rev1.0.4.pdf`):
VDD_IO 1.8 V … VIN + 0.3 V (S. 39 Tab. 11-2a) → 2.0 V zulässig; 6 Mbit/s bei 1.8 V (S. 40); VIL ≤ 0.4 V, VIH ≥ 0.7 × VDD_IO
= 1.4 V, VOL ≤ 0.4 V (S. 39 Tab. 11-2b); I/O 5-V-tolerant, externe VDD_IO-Speisung vorgesehen (S. 33). Board
(`docs/references/Waveshare_PL2303-USB-UART-Board-TypeA-V2_Schematic_2026-11-08.pdf`): Jumper J1 5V/VCCIO/3.3V offen
= VCCIO von aussen; +5 V an J1 abgreifbar; P2 = VCCIO/GND/TXD/RXD.

Prüfung Elektronik 2026-11-09 (`hardware/programmer/README.md` Kap. 9, SPICE `simulation/spice/programmer/prog_uart_pl2303.py`):
1. **Abs. max VDD_IO ≤ VIN + 0.3 V** (S. 39 Tab. 11-1): Einstecken unkritisch (0.000 V); Weg B nur mit Reihenfolge
   „USB zuerst ein, zuletzt aus“; Weg A beim Ziehen der USB ohne Gegenmassnahme bis 1.06 V (Ladung der VIO-Kondensatoren)
   → Entladewiderstand R2 470 Ω an VIO im Adapter (D-031/PA-6): ≤ 0.015 V.
2. VIL ≤ 0.4 V, RXD-LED 1 kΩ: mit Puffer U4 0.06–0.09 V (+311 mV); Weg B an R9 Pad 1 +113 mV bei 2.0 V, **höchstens 2.1 V**.
   VOL/VOH ohne Stromangabe → Eingangsprüfung des Boards (TXD high ≥ 1.90 V, TXD low ≤ 0.10 V, RXD → GND ≤ 0.69 mA,
   VCCIO offen ≤ 0.10 V).
3. J1 des Adapters: 1 = Board-J1 Stift „5V“ (VCC5V), 2 = P2.2 GND, 3 = P2.1 VCCIO, 4 = P2.4 RXD, 5 = P2.3 TXD; Jumper J1 ab.
   Port `/dev/ttyUSB0` (Treiber `pl2303`, VID/PID 067B:23A3, S. 22).

**Empfehlung:** Variante B (ein Händler weniger, 8.90 CHF) unter den Bedingungen B1–B6 (README Kap. 9.5); A nur noch,
falls ohnehin eine Auslandsbestellung bei waveshare.com nötig ist.

## 4 microSD Industrial (G3)

`GATEWAY_SETUP.md` Kap. 1: Industrial/pSLC, ≥ 8 GB. Bisher Kingston SDCIT2/16GB, Datenblatt jetzt lokal
(`docs/datasheets/Kingston_SDCIT2_Datasheet_MKD-02122026.pdf` S. 1: TLC im pSLC-Modus, bis 3840 TBW / 30K P/E,
−40…85 °C; Kapazitäten 8–128 GB).

| Quelle (Abruf 2026-11-09) | Artikel | Preis | Lager |
|---|---|---|---|
| pi-shop.ch Art. 10951 | SDCIT2/16GB | CHF 27.90 | nicht an Lager (Benachrichtigung möglich) |
| alltron.ch (Grosshandel, Brack-Gruppe, **ANNAHME** nur Geschäftskunden) | SDCIT2/16GB | – | 0, **100 Stk bestellt auf 23.11.2026**; 8 GB: 12 an Lager |
| mediamarkt.ch Marktplatz (Ultimus.ch) | SDCIT2/8GB | CHF 56.95, versandfrei | an Lager, Lieferung 27.11.–01.12. |
| mediamarkt.ch Marktplatz (Ultimus.ch) | SDCIT2/16GB | CHF 63.95, versandfrei | an Lager, Lieferung 19.–23.11. |

Nicht abrufbar (Bot-Sperre): digitec/galaxus, brack.ch, distrelec.ch (führt SDCIT2/8GBSP, Art. 302-48-289 laut Suchmaschine),
mouser.ch. Andere Industrial-Serien (SanDisk Industrial, Swissbit) ohne CH-Angebot mit abrufbarem Preis.

**Empfehlung:** bei pi-shop.ch auf Lagereingang warten (Grosshandel meldet Lieferung 23.11.) und G2 + W1 + G3 in **einer**
Sendung bestellen. Nur wenn der Termin drängt: SDCIT2/8GB über mediamarkt.ch (gleiche Serie, +29 CHF).

## 5 Liste

| ID | Teil | Soll | Bedarf | Händler | Art.-Nr. | Angebot | Pack. × Inhalt | CHF/Pack. | Summe CHF | Lager | Abruf | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | Knopfzelle CR2032 (Sensor 20 + Tests 28) | Panasonic CR2032 (D-006) | 48 | [galaxus.ch](https://www.galaxus.ch/en/s1/product/panasonic-cr2032-lithium-48-knopfbatterien-48-pcs-cr2032-225-mah-batteries-61927007) | 61927007 | Panasonic CR2032 Lithium 48 Knopfbatterien | 1 × 48 | 39.84 | 39.84 (A) | ANNAHME (Auszug: wenige Packungen, Drittanbieter) | 2026-11-08 | Preis pruefen |
| S2 | O-Ring Huelse/Kragen + Zapfen | AS568-019 = ID 20.35 x CS 1.78 mm, Silikon oder EPDM ohne Russ (rot/transluzent) | 50 | offen (Normteile-/Dichtungs-Fachhandel) | - | - | 50 × 1 | 0.15 | 7.50 (A) | - | 2026-11-09 | Quelle offen |
| S3 | Schraube unverlierbar Batteriefach | ISO 7045 M2 x 3 A2 Linsenkopf PH1 (Kopf Ø3.8 x 1.3) | 25 | offen (Normteile-/Dichtungs-Fachhandel) | - | - | 25 × 1 | 0.10 | 2.50 (A) | - | 2026-11-09 | Quelle offen |
| S4 | Mutter im Kragen eingegossen | ISO 4032 M2 A2 SW4 x 1.6 | 30 | [bastelgarage.ch](https://www.bastelgarage.ch/10-stuck-m2-mutter-set-rostfrei) | 422198 | 10 Stueck M2 Mutter Set rostfrei (A2, SW4, Hoehe 1.6) | 3 × 10 | 2.90 | 8.70 | Lagernd | 2026-11-09 | kauffertig |
| S5 | Tastenmembran | Silikonplatte 0.5 mm Shore A 40-60, Ø6.4 gestanzt | 1 | offen (Normteile-/Dichtungs-Fachhandel) | - | - | 1 × 1 | 10.00 | 10.00 (A) | - | 2026-11-09 | Quelle offen |
| S6 | Silikonfett fuer O-Ringe | silikonbasiert, fuer Silikon/EPDM vertraeglich | 1 | offen (Normteile-/Dichtungs-Fachhandel) | - | - | 1 × 1 | 8.00 | 8.00 (A) | - | 2026-11-09 | Quelle offen |
| S7 | Kleber Lichtfenster | 2K-Epoxid transparent oder UV-Kleber (PRINT_SETTINGS Kap. 5, ANNAHME Typ) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/uhu-plus-endfest-zweikomponenten-epoxidkleber-33g) | 422137 | UHU Plus Endfest 2K-Epoxid 33 g (-40...+100 C laut Shop) | 1 × 1 | 12.90 | 12.90 | Lagernd | 2026-11-09 | Typ durch Mechanik bestaetigen |
| S8 | Vergussmasse Kragen/Schott/Sondenkante | Epoxid 2K Tg >= 80 C (Vorschlag EP-K Electrolube ER2223, Wahl parallel durch anderen Agenten) | 1 | offen (Platzhalter) | - | - | 1 × 1 | 0.00 | – | - | 2026-11-09 | Platzhalter |
| S9 | Filament ASA grau (Huelse, Wanne) | Bambu ASA (MAT-ASA, TDS lokal), Farbton Warmgrau nach Musterdruck, Pigment ohne Russ | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/asa-grau-filament-1-75mm-1kg-esun) | 424233 | eSun ASA+ Grau 1.75 mm 1 kg | 1 × 1 | 19.90 | 19.90 | Ausverkauft | 2026-11-09 | nicht an Lager |
| S10 | Filament ASA blau (Kappe, Taste, Deckel) | wie S9, Hellblau, Pigment ohne Russ/Metall (Antennenbereich) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/asa-blau-filament-1-75mm-1kg-esun) | 424238 | eSun ASA+ Blau 1.75 mm 1 kg | 1 × 1 | 19.90 | 19.90 | Lagernd | 2026-11-09 | Freigabe Mechanik |
| S11 | Filament Lichtfenster transluzent natur | ASA natur bevorzugt, PETG nur mit Nachweis 7 d 65 C (PRINT_SETTINGS Kap. 1) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/petg-natural-transparent-filament-1-75mm-1kg-esun) | 421094 | eSun PETG Natural Transparent 1.75 mm 1 kg | 1 × 1 | 13.90 | 13.90 | Lagernd | 2026-11-09 | Entscheid Mechanik |
| G2 | Netzteil 5 V 2.5 A Micro-USB | Raspberry Pi 12.5 W Micro-USB Original | 1 | [pi-shop.ch](https://www.pi-shop.ch/raspberry-pi-12-5w-micro-usb-power-supply-2254) | 11715 | Raspberry Pi 12.5W Micro USB Power Supply | 1 × 1 | 11.90 | 11.90 | Sofort-Versand ab Lager | 2026-11-09 | kauffertig |
| G3 | microSD Industrial | Industrial/pSLC >= 8 GB (GATEWAY_SETUP Kap. 1) | 1 | [pi-shop.ch](https://www.pi-shop.ch/kingston-microsdhc-karte-industrial-uhs-i-16-gb) | 10951 | Kingston microSDHC Industrial UHS-I 16 GB (SDCIT2/16GB) | 1 × 1 | 27.90 | 27.90 | nicht an Lager | 2026-11-09 | nicht an Lager |
| G6 | Klimasensor-Breakout (D-029) | SHT40/41/45, I2C 0x44, 3.3 V, <= 24 x 14 mm hochkant | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/fermion-temperatur-und-feuchtigkeitssensor-sht40) | 421989 | DFRobot Fermion SHT40 Breakout SEN0428 (14 x 17 mm) | 1 × 1 | 11.90 | 11.90 | Lagernd | 2026-11-09 | kauffertig |
| G8a | Gewindeeinsaetze M2.5 (4 je Gateway) | M2.5, CAD-ANNAHME Ø3.5 x 4 (Bohrung 3.2) | 4 | [bastelgarage.ch](https://www.bastelgarage.ch/m2-5-4mm-gewindeeinsatze-messing-heat-insert-100stk) | 425681 | Gewindeeinsaetze Messing M2.5 x 4 x Ø4.6, 100 Stk | 1 × 100 | 15.90 | 15.90 | Lagernd | 2026-11-09 | Freigabe Mechanik |
| G8b | Schrauben M2.5 x 8 (4 je Gateway) | ISO 7380 Linsenkopf M2.5 x 8 A2 (Nylon als Option, PRINT_SETTINGS Kap. 4) | 4 | offen (Normteile-/Dichtungs-Fachhandel) | - | - | 4 × 1 | 0.25 | 1.00 (A) | - | 2026-11-09 | Quelle offen |
| G9 | Status-LED 3 mm gruen + Vorwiderstand 470 Ohm (D-027) | Kingbright WP710A10GD + YAGEO MFR-25FBF52-470R | 1 | [Digi-Key CH (laut phase5_gateway_led.md)](https://www.digikey.ch) | 754-1603-ND / MFR-25FBF52-470R | docs/reviews/phase5_gateway_led.md Kap. 4 | 1 × 1 | 0.29 | 0.29 | Lager 24503 / 19960 (2026-11-08) | 2026-11-08 | buendeln |
| G10 | Litze AWG 28, Schrumpfschlauch | - | 1 | Werkstattbestand | - | - | 1 × 1 | 0.00 | – | vorhanden | 2026-11-08 | vorhanden |
| W1 | USB-UART mit externem VIO 2.0 V (FW-T3) | VIO extern 1.8-2.0 V, kein Rueckstrom, ROM-Bootloader 19200-57600 Baud | 1 | [pi-shop.ch](https://www.pi-shop.ch/pl2303-usb-to-uart-ttl-communication-module-v2) | 11757 | Waveshare PL2303 USB UART Board (type A) V2 (PL2303GS) | 1 × 1 | 8.90 | 8.90 | Sofort-Versand ab Lager | 2026-11-09 | kauffertig |
| W2 | Programmieradapter Rev 1 Teile | hardware/programmer/README.md Kap. 6 (LCSC, Federstifte, Platine) | 1 | LCSC + Fachhandel (siehe README) | - | - | 1 × 1 | 0.00 | – | - | 2026-11-08 | separat |

(A) = Preis ANNAHME bzw. Quelle offen. Bedarf-Herleitung, Register-Ref und Bemerkungen: Spalten in der CSV.

Bemerkungen:

- **S1** (5 Prototyp + 15 Serie + 28 Testzellen (Auftrag ca. 30)): Datenblatt docs/datasheets/Panasonic_CR2032_Datasheet_2026-02.pdf. Ausweichen ohne eigenen Haendler: bastelgarage.ch Varta CR2032 5 Stk Art. 424382 CHF 8.90 lagernd (10 Packungen = 89.00) - weicht von D-006 ab, Varta-Datenblatt fehlt, Energiebudget mit Panasonic gerechnet -> Entscheid Auftraggeber
- **S2** (2 je Sensor x 20 + 10 Passproben/Reserve): Mass belegt docs/references/GTWeed_AS568_StandardOringSizing.pdf S. 2 (Dash -019 0.801 in). Kein CH-Angebot fuer 20.35 x 1.78 Silikon gefunden (Suche 2026-11-09). Werkstoffdatenblatt des Lieferanten ablegen
- **S3** (1 je Sensor x 20 + 5 Reserve): bastelgarage.ch Art. 422191 (10 Stk M2x3 A2 Linsenkopf CHF 3.90, lagernd) ist Torx TX6 mit Kopfhoehe 1.6 mm -> weicht ab (PH1, 1.3 mm, Werkzeug REQ-MECH-15) -> nur nach Freigabe Mechanik
- **S4** (1 je Sensor x 20 + Reserve): Masse laut Shop = Nennmasse ISO 4032 (SW4 x 1.6)
- **S5** (1 Platte fuer 20 + Reserve): Betaetigungskraft PROTOTYP-PRUEFUNG
- **S6** (1 Tube): Datenblatt beim Kauf ablegen
- **S7** (1 Packung): TDS/SDS nicht lokal -> beim Kauf ablegen. Klebefuge dicht nach 7 d 65 C = PROTOTYP-PRUEFUNG
- **S8** (Platzhalter): Wahl, Menge, Haendler und Preis durch den Material-Agenten (Phase 6)
- **S9** (20 x 13 g + Gateway 14 g + Passproben, < 1 kg): Zuerst Werkstattbestand pruefen (ANNAHME vorhanden). Bambu ASA Gray (45102) im Bambu Lab EU Store 14.99 EUR, nicht an Lager (ld+json 2026-11-09), Gratisversand CH erst ab 119 EUR. eSun ASA+ ist ein anderes Material als MAT-ASA -> TDS ablegen, HDT >= 80 C belegen (REQ-MECH-12)
- **S10** (20 x ca. 5 g + Gateway 10 g, < 1 kg): Nur falls kein Bambu ASA blau vorhanden. Farbton/Pigment und TDS (HDT) vor dem Kauf pruefen
- **S11** (wenige g): ASA natur bei bastelgarage/pi-shop nicht gefunden. PETG nur mit PROTOTYP-PRUEFUNG
- **G2** (1 Gateway): Konformitaet beim Wareneingang (Sicherheits-Agent), Datenblatt fehlt (F-8)
- **G3** (1 Gateway): Datenblatt docs/datasheets/Kingston_SDCIT2_Datasheet_MKD-02122026.pdf. Grosshandel alltron.ch: 100 Stk auf 23.11.2026 bestellt. Sofort-Alternative gleicher Serie: mediamarkt.ch Marktplatz Ultimus.ch SDCIT2/8GB CHF 56.95 (Lieferung 27.11.-01.12.) bzw. 16 GB CHF 63.95, versandkostenfrei
- **G6** (1 Gateway): Masszeichnung/Schaltplan lokal (docs/datasheets/DFRobot_SEN0428_*). Mechanik: Nutpfosten 17 mm
- **G8a** (4 je Gateway): Aussen-Ø 4.6 statt 3.5 -> Bohrung im Deckel anpassen (Mechanik). Kleinere Packung nicht gefunden
- **G8b** (4 je Gateway): bastelgarage M2.5-Sortiment DIN 912 ausverkauft (2026-11-09) und Zylinderkopf statt Linsenkopf
- **G9** (1 Gateway): Digi-Key-Versand unter 70 CHF = 23 CHF -> nicht einzeln bestellen: mit LCSC-Bestellung Programmieradapter buendeln (LCSC-Teile durch Elektronik waehlen) oder Werkstattbestand. BOM_GATEWAY G9 nachfuehren = Elektronik
- **G10** (Werkstatt): bastelgarage Schrumpfschlauch-Set 140 Stk ausverkauft (2026-11-09)
- **W1** (1 Programmierplatz): Elektronik 2026-11-09: freigegeben mit Bedingungen B1-B6 (hardware/programmer/README.md Kap. 9, EINKAUFSLISTE.md Kap. 3). Original CH343 (TOOL-UART1): waveshare.com USD 3.49 + Versand (nicht ablesbar) bzw. eckstein-shop.de EUR 4.15 (ca. 3 Wochen) -> eigener Auslandsversand
- **W2** (1 Adapter): Nicht in dieser Summe (Werkzeugbudget). G9-LED in dieselbe LCSC-Bestellung legen

## 6 Händlergruppierung und Versand

| Händler | Positionen | Ware CHF | Versand CHF | Total CHF | davon jetzt lieferbar | Versandregel |
|---|---|---|---|---|---|---|
| bastelgarage.ch | S4, S7, S9, S10, S11, G6, G8a | 103.10 | 0.00 | 103.10 | 83.20 (+0.00 Versand) | bastelgarage.ch/lieferung-versandkosten (2026-11-09): PostPac Economy 6.90, Priority 8.90, ab CHF 80 Warenwert gratis (docs/references/Haendler_Einkauf_Auszug_2026-11-09.txt) |
| pi-shop.ch | G2, G3, W1 | 48.70 | 7.90 | 56.60 | 20.80 (+7.90 Versand) | pi-shop.ch/versandkosten (2026-11-08): B-Post 7.90, A-Post 9.90 (docs/references/pi-shop_Gateway-Teile_Auszug_2026-11-08.txt) |
| galaxus.ch | S1 | 39.84 | 9.90 | 49.74 | 39.84 (+9.90 Versand) | ANNAHME (Versandseite nicht abrufbar, Bot-Sperre) |
| offen (Normteile-/Dichtungs-Fachhandel) | S2, S3, S5, S6, G8b | 29.00 | 10.00 | 39.00 | 0.00 (+0.00 Versand) | ANNAHME (Haendler offen, eine Sammelbestellung S2/S3/S5/S6/G8b) |
| Digi-Key CH (laut phase5_gateway_led.md) | G9 | 0.29 | 0.00 | 0.29 | 0.29 (+0.00 Versand) | nicht einzeln bestellen (23 CHF Versand unter 70 CHF, docs/reviews/phase5_gateway_led.md): mit LCSC-Bestellung Programmieradapter buendeln |
| **Summe** | | **220.93** | **27.80** | **248.73** | | |

- bastelgarage.ch: geplant 103.10 CHF → versandkostenfrei; jetzt lieferbar 83.20 CHF (ohne ausverkauftes Grau) → frei. Ohne S11 (PETG) fällt die Bestellung unter 80 CHF.
- pi-shop.ch: G2 + W1 + G3 in **einer** Sendung, sobald G3 an Lager ist; getrennt bestellt kostet die zweite Sendung nochmals 7.90 CHF.
- Normteile/Dichtungen (S2, S3, S5, S6, G8b): **ein** Fachhändler für alles; noch keiner mit abrufbarem Angebot (Versand ANNAHME 10 CHF).
- G9 (Gateway-LED, D-027): nicht bei Digi-Key einzeln bestellen (23 CHF Versand), sondern in die LCSC-Bestellung des Programmieradapters legen (Teilewahl Elektronik).
- JLC (PCBA Sensor) und Verguss (S8) sind separat (ORDER_JLC_REV_C.md bzw. Material-Agent).

## 7 Prüfhinweise (`scripts/einkaufsliste.py --check`)

- S1: Preis ANNAHME/Quelle offen (39.84 CHF)
- S2: Preis ANNAHME/Quelle offen (7.50 CHF)
- S3: Preis ANNAHME/Quelle offen (2.50 CHF)
- S5: Preis ANNAHME/Quelle offen (10.00 CHF)
- S6: Preis ANNAHME/Quelle offen (8.00 CHF)
- S9: bastelgarage.ch Ausverkauft (Abruf 2026-11-09)
- G3: pi-shop.ch nicht an Lager (Abruf 2026-11-09)
- G8b: Preis ANNAHME/Quelle offen (1.00 CHF)
