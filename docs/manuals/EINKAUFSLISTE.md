# fluidi – Einkaufsliste (alles ausser JLC)

| | |
|---|---|
| Stand | 2026-11-09, erzeugt von `.venv/bin/python scripts/einkaufsliste.py` aus `docs/manuals/EINKAUFSLISTE.csv` (nicht von Hand ändern) |
| Umfang | Sensor (Prototyp 5 + Serie 15), Gateway (D-028 ohne RTC, D-029 SHT40-Breakout), Werkstatt (USB-UART, Testzellen) |
| Belege | `docs/references/Haendler_Einkauf_Auszug_2026-11-09.txt`, `docs/references/pi-shop_Gateway-Teile_Auszug_2026-11-08.txt`, Register `docs/datasheets/INDEX.csv` |
| Nicht abrufbar | digitec/galaxus, mouser.ch, distrelec.ch, digikey.ch, conrad.ch, brack.ch, toppreise.ch (Bot-Sperre/403) → Preise von dort sind **ANNAHME** |
| Hinweis | Keine Bestellung ausgelöst. Preise inkl. MWST, Lager = Anzeige am Abruftag |

## 1 Fazit

- Warenwert geplant **573.52 CHF** + Versand **81.70 CHF** = **655.22 CHF** (davon 251.34 CHF Preis-ANNAHME; ohne JLC, ohne Werkstattbestand; Summen je Bereich Kap. 8).
- **Händler mit Bestellung: 9** (offen (Labor-/Arbeitsschutz-Fachhandel), bastelgarage.ch, Simpex Electronic AG, pi-shop.ch, galaxus.ch, offen (Normteile-/Dichtungs-Fachhandel), 3djake.ch, LCSC (mit JLC-Bestellung buendeln, ANNAHME), Digi-Key CH (laut phase5_gateway_led.md)). Kern sind **zwei** CH-Händler: bastelgarage.ch und pi-shop.ch; dazu Simpex (Verguss, 8 Wochen Lieferzeit) und LCSC (mit JLC bündeln).
- Ein Händler weniger möglich: Zellen bei bastelgarage.ch (Varta statt Panasonic, Entscheid Auftraggeber, S1).
- Offen: Quelle O-Ringe AS568-019 Silikon, ISO 7380 M2.5×8, Silikonplatte, Silikonfett, Federstifte (ein Normteile-/Dichtungshändler) und Labor-/Schutzzubehör Verguss (ein Laborhändler); Filament grau und microSD nicht an Lager.

## 2 Klimasensor-Breakout Gateway (D-029, G6)

Platz (CAD `mechanical/gen/fluidi_gateway_pi.py`, Konstante `CLIMA`, Prüfung 11/14 in
`mechanical/gateway_pi/check_gateway_pi.txt`): Klimakammer innen **x 8.0 × y 38.0 × z 16.0 mm** (x 32…40, Wand 2 mm).
Das Modul steht hochkant in der y-z-Ebene, Sensorseite +x zur Stirnwand. Hochkant ist z ≤ 14 nutzbar (z 3…17 in 2…18),
flach liegend nur 8 mm (x).

| Kandidat | Masse (Quelle) | Elektrik (Quelle) | Bezug CH (Abruf 2026-11-09) | Passt? |
|---|---|---|---|---|
| **DFRobot Fermion SHT40 SEN0428** | **14.0 × 17.0 mm**, 2 × Ø2.0 im Raster 10.0, 4 Lötaugen VCC/GND/SCL/SDA an einer 14-mm-Kante (`docs/datasheets/DFRobot_SEN0428_Dimensions_V0.1.png`; Wiki „Dimension 14×17mm“) | VCC 3.3–5 V (Wiki); LDO → „3V“, Pegelwandler 2 × 2N7002, 10 kΩ Pull-ups beidseitig (`docs/datasheets/DFRobot_SEN0428_Schematic_V0.1.pdf`); SHT40 VDD 1.08–3.6 V (`docs/datasheets/Sensirion_SHT4x_Datasheet_V7.3.pdf` S. 9); Adresse 0x44 (DFRobot-Bibliothek `DFRobot_SHT40.h` Z. 20, SHT40-AD1B; Sensirion S. 21/22) | bastelgarage.ch Art. 421989, **CHF 11.90, lagernd** | **ja**, hochkant 17 (y) × 14 (z) |
| Adafruit SHT41 STEMMA QT (5776) | 25.4 × 17.8 mm (1.00 × 0.70 in, `docs/datasheets/Adafruit_5776_SHT41_FabPrint_2023-07.png`) | Regler + Pegelwandler (`…_Schematic_2023-07.png`) | play-zone.ch Art. ada-5776, CHF 9.90, > 10 an Lager (Versand ab 300 CHF frei, Tarif nicht abgelesen) | nein: 17.8 > 16 (hochkant), > 8 (flach) |
| Seeed Grove SHT41 (bisher G6) | 20 × 40 mm (`docs/references/Seeed_Grove-SHT4x_Wiki_Auszug_2026-11-08.txt`) | Schaltplan nicht lokal | pi-shop.ch Art. 12042, CHF 8.90, nicht an Lager | nein: 40 > 38 |

Gesucht, aber ohne CH-Quelle: 7Semi SHT40/SHT41-Kleinstbreakouts (nur indische Händler), Generika ohne Schaltplan.
pi-shop.ch führt kein weiteres SHT4x-Breakout (Suche „sht40“ 2026-11-09: nur CO2-Sensor/E-Paper-Kit, Beleg im Auszug).

**Empfehlung: DFRobot SEN0428** – einziges gefundenes SHT4x-Breakout mit Herstellermass und Schaltplan, das in die
Kammer passt, ab Lager in der Schweiz, beim selben Händler wie Muttern/Einsätze/Kleber (kein zusätzlicher Versand).

**Umsetzung Mechanik (D-032, `mechanical/gateway_pi/check_gateway_pi.txt` Pkt. 14):** SEN0428 hochkant 17.0 (y) × 14.0 (z),
gehalten von einer **Bodenschiene** (Nut 1.90 breit, Eingriff 1.00) und einer **Deckelrippe** (Eingriff 0.80, 0.30 Luft über
der Oberkante), Endanschläge mit je 0.30 Luft in y; Bauteilfreiheit zur Schiene 0.45 mm, zur Deckelrippe 0.65 mm.
**Platinendicke 1.6 mm und Bauteilhöhen sind ANNAHME** (Hersteller gibt sie nicht an) → am Muster messen.

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

## 5 Verguss (D-030) und Programmieradapter (D-031)

**Verguss:** Electrolube ER2223 Resin Pack 250 g, **2 Beutel** (je Bauserie einer, Haltbarkeit nach dem Abfüllen 3 Monate,
MA-3) bei Simpex, CHF 41.29 inkl. MWST, **Lieferzeit 8 Wochen** → sofort nach Freigabe bestellen; vorher SDB Teil B in
Landessprache anfordern (D-030 Bed. 1). Zubehör nach `docs/concepts/vergussmasse_versiegelung.md` Kap. 7.1 (V-Z1…V-Z11):
mit Schweizer Shopbeleg bei bastelgarage.ch (ohnehin in der Liste) Feinwaage, Mischbecher, Rührstäbe, Trichter, Pinsel,
Nitrilhandschuhe; der Rest (Prüfgewichte, kindergesicherte Flaschen, Sekundärbehälter, Spritzen/Kanülen, Schutzbrille/Visier,
Schürze/Augenspülflasche, Halbmaske A, Thermometer bis 80 °C) hat **keine abrufbare CH-Quelle** (Laborhandel/Baumarkt-Seiten
gesperrt oder JS) und bleibt **ANNAHME** aus Kap. 7.1. **Entfällt, falls vorhanden:** Feinwaage (V-Z1), Schutzbrille/Visier
(V-Z8), Wärmeschrank (V-Z12). Abweichungen zur Freigabe durch die Sicherheit: Silikon- statt PE-Trichter (V-Z5c),
Handschuhe ohne Angabe von Dicke/EN 374 (V-Z7), Waage ohne Justiergewicht (Prüfgewichte V-Z2 nötig).

**Programmieradapter:** Teile nach `hardware/programmer/README.md` Kap. 2.1/6 (inkl. R2 470 Ω C17710, D-031/PA-6) bei LCSC,
Preise der JLC/LCSC-Teilesuche umgerechnet mit dem Kurs aus `scripts/cost_model.py`; LCSC-Mindestmengen und Versand
**ANNAHME** (README: 10–25 CHF) – mit der JLC-Bestellung im selben Warenkorb prüfen. USB-UART = W1 (PL2303, pi-shop.ch).

## 6 Liste

| ID | Teil | Soll | Bedarf | Händler | Art.-Nr. | Angebot | Pack. × Inhalt | CHF/Pack. | Summe CHF | Lager | Abruf | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | Knopfzelle CR2032 (Sensor 20 + Tests 28) | Panasonic CR2032 (D-006) | 48 | [galaxus.ch](https://www.galaxus.ch/en/s1/product/panasonic-cr2032-lithium-48-knopfbatterien-48-pcs-cr2032-225-mah-batteries-61927007) | 61927007 | Panasonic CR2032 Lithium 48 Knopfbatterien | 1 × 48 | 39.84 | 39.84 (A) | ANNAHME (Auszug: wenige Packungen, Drittanbieter) | 2026-11-08 | Preis pruefen |
| S2 | O-Ring Huelse/Kragen + Zapfen | AS568-019 = ID 20.35 x CS 1.78 mm, Silikon oder EPDM ohne Russ (rot/transluzent) | 50 | offen (Normteile-/Dichtungs-Fachhandel) | - | - | 50 × 1 | 0.15 | 7.50 (A) | - | 2026-11-09 | Quelle offen |
| S3 | Schraube unverlierbar Batteriefach | M2 x 3 A2 Linsenkopf Torx TX6, Kopfhoehe 1.6 (D-032, ersetzt ISO 7045 PH1) | 25 | [bastelgarage.ch](https://www.bastelgarage.ch/10-stuck-m2x3mm-linsenkopfschrauben-set-rostfrei) | 422191 | 10 Stueck M2x3mm Linsenkopfschrauben Set rostfrei (A2, Torx TX6, Kopfhoehe 1.6) | 3 × 10 | 3.90 | 11.70 | Lagernd | 2026-11-09 | kauffertig |
| S4 | Mutter im Kragen eingegossen | ISO 4032 M2 A2 SW4 x 1.6 | 30 | [bastelgarage.ch](https://www.bastelgarage.ch/10-stuck-m2-mutter-set-rostfrei) | 422198 | 10 Stueck M2 Mutter Set rostfrei (A2, SW4, Hoehe 1.6) | 3 × 10 | 2.90 | 8.70 | Lagernd | 2026-11-09 | kauffertig |
| S5 | Tastenmembran | Silikonplatte 0.5 mm Shore A 40-60, Ø6.4 gestanzt | 1 | offen (Normteile-/Dichtungs-Fachhandel) | - | - | 1 × 1 | 10.00 | 10.00 (A) | - | 2026-11-09 | Quelle offen |
| S6 | Silikonfett fuer O-Ringe | silikonbasiert, fuer Silikon/EPDM vertraeglich | 1 | offen (Normteile-/Dichtungs-Fachhandel) | - | - | 1 × 1 | 8.00 | 8.00 (A) | - | 2026-11-09 | Quelle offen |
| S7 | Kleber Lichtfenster | 2K-Epoxid, hochviskos, -40...+100 C, Transparenz nicht noetig (Fuge 0.1 mm nicht im Lichtweg, PRINT_SETTINGS Kap. 5) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/uhu-plus-endfest-zweikomponenten-epoxidkleber-33g) | 422137 | UHU Plus Endfest 2K-Epoxid 33 g (-40...+100 C laut Shop) | 1 × 1 | 12.90 | 12.90 | Lagernd | 2026-11-09 | Freigabe Orchestrator |
| S9 | Filament ASA grau (Huelse, Wanne) | Vorgabe Bambu ASA (MAT-ASA, TDS lokal), Warmgrau nach Musterdruck (D-010), Pigment ohne Russ, bedingte Alternative eSun ASA+ (MAT-ASA2, D-032) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/asa-grau-filament-1-75mm-1kg-esun) | 424233 | eSun ASA+ Grau 1.75 mm 1 kg | 1 × 1 | 19.90 | 19.90 | Ausverkauft | 2026-11-09 | nicht an Lager |
| S10 | Filament ASA blau (Kappe, Taste, Deckel) | Vorgabe Bambu ASA Hellblau (MAT-ASA), Pigment ohne Russ/Metall (Antennenbereich), bedingte Alternative eSun ASA+ Blau (MAT-ASA2, D-032) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/asa-blau-filament-1-75mm-1kg-esun) | 424238 | eSun ASA+ Blau 1.75 mm 1 kg | 1 × 1 | 19.90 | 19.90 | Lagernd | 2026-11-09 | bedingt (D-032) |
| S11 | Filament Lichtfenster ASA natur | ASA unpigmentiert natur (PRINT_SETTINGS Kap. 1), HDT >= 80 C mit TDS, kein PETG, kein deckendes Weiss | 1 | [3djake.ch](https://www.3djake.ch/de-CH/polymaker/polymaker-asa-natur) | PM-PF01006 | Polymaker ASA Natural 1.75 mm 1 kg (PF01006) | 1 × 1 | 23.75 | 23.75 | Lagernd (1 Stk) | 2026-11-09 | Freigabe Orchestrator |
| G2 | Netzteil 5 V 2.5 A Micro-USB | Raspberry Pi 12.5 W Micro-USB Original | 1 | [pi-shop.ch](https://www.pi-shop.ch/raspberry-pi-12-5w-micro-usb-power-supply-2254) | 11715 | Raspberry Pi 12.5W Micro USB Power Supply | 1 × 1 | 11.90 | 11.90 | Sofort-Versand ab Lager | 2026-11-09 | kauffertig |
| G3 | microSD Industrial | Industrial/pSLC >= 8 GB (GATEWAY_SETUP Kap. 1) | 1 | [pi-shop.ch](https://www.pi-shop.ch/kingston-microsdhc-karte-industrial-uhs-i-16-gb) | 10951 | Kingston microSDHC Industrial UHS-I 16 GB (SDCIT2/16GB) | 1 × 1 | 27.90 | 27.90 | nicht an Lager | 2026-11-09 | nicht an Lager |
| G6 | Klimasensor-Breakout (D-029) | SHT40/41/45, I2C 0x44, 3.3 V, hochkant <= 17 x 14 mm (Bodenschiene + Deckelrippe, D-032) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/fermion-temperatur-und-feuchtigkeitssensor-sht40) | 421989 | DFRobot Fermion SHT40 Breakout SEN0428 (14 x 17 mm) | 1 × 1 | 11.90 | 11.90 | Lagernd | 2026-11-09 | kauffertig |
| G8a | Gewindeeinsaetze M2.5 (4 je Gateway) | M2.5 x 4 x Ø4.6 Messing, Bohrung 3.9 (Haendlerangabe, D-032) | 4 | [bastelgarage.ch](https://www.bastelgarage.ch/m2-5-4mm-gewindeeinsatze-messing-heat-insert-100stk) | 425681 | Gewindeeinsaetze Messing M2.5 x 4 x Ø4.6, 100 Stk | 1 × 100 | 15.90 | 15.90 | Lagernd | 2026-11-09 | kauffertig |
| G8b | Schrauben M2.5 x 8 (4 je Gateway) | ISO 7380 Linsenkopf M2.5 x 8 A2 (Nylon als Option, PRINT_SETTINGS Kap. 4) | 4 | offen (Normteile-/Dichtungs-Fachhandel) | - | - | 4 × 1 | 0.25 | 1.00 (A) | - | 2026-11-09 | Quelle offen |
| G9 | Status-LED 3 mm gruen + Vorwiderstand 470 Ohm (D-027) | Kingbright WP710A10GD + YAGEO MFR-25FBF52-470R | 1 | [Digi-Key CH (laut phase5_gateway_led.md)](https://www.digikey.ch) | 754-1603-ND / MFR-25FBF52-470R | docs/reviews/phase5_gateway_led.md Kap. 4 | 1 × 1 | 0.29 | 0.29 | Lager 24503 / 19960 (2026-11-08) | 2026-11-08 | buendeln |
| G10 | Litze AWG 28, Schrumpfschlauch | - | 1 | Werkstattbestand | - | - | 1 × 1 | 0.00 | – | vorhanden | 2026-11-08 | vorhanden |
| W1 | USB-UART mit externem VIO 2.0 V (FW-T3) | VIO extern 1.8-2.0 V, kein Rueckstrom, ROM-Bootloader 19200-57600 Baud | 1 | [pi-shop.ch](https://www.pi-shop.ch/pl2303-usb-to-uart-ttl-communication-module-v2) | 11757 | Waveshare PL2303 USB UART Board (type A) V2 (PL2303GS) | 1 × 1 | 8.90 | 8.90 | Sofort-Versand ab Lager | 2026-11-09 | kauffertig |
| V-M1 | Vergussmasse Schott/Kragen/Sondenkante (D-030) | Electrolube ER2223 Resin Pack 250 g (EER2223RP250G) | 2 | [Simpex Electronic AG](https://www.simpex.ch) | EER2223RP250G | ER2223 Resin Pack 250 g, CHF 38.20 exkl. MWST | 2 × 1 | 41.29 | 82.58 | In stock: available to order, LIEFERZEIT 8 WOCHEN | 2026-11-08 | kauffertig (frueh bestellen) |
| V-Z1 | Feinwaage (MA-4) | 0.01 g Aufloesung, >= 200 g (Konzept 7.1 V-Z1) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/digitale-feinwaage-mh-500-0-01g-500g) | 424394 | Digitale Feinwaage MH-500 0.01-500 g (Mindestgewicht 0.05 g, ohne Justiergewicht) | 1 × 1 | 17.90 | 17.90 | Lagernd | 2026-11-09 | entfaellt, falls vorhanden |
| V-Z2 | Pruefgewichte 1 g und 5 g (MA-4) | Klasse F1 oder M1 | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 20.00 | 20.00 (A) | - | 2026-11-09 | Quelle offen |
| V-Z3 | Laborflaschen kindergesichert, Etiketten, Farbmarker (MA-1/MA-2) | B: HDPE ca. 60 ml, A: HDPE/Glas ca. 250 ml | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 15.00 | 15.00 (A) | - | 2026-11-09 | Quelle offen |
| V-Z4 | Sekundaerbehaelter abschliessbar + Saugmaterial (MA-1) | dichte Kunststoffbox, Vorhaengeschloss, Vermiculit/Katzenstreu | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 25.00 | 25.00 (A) | - | 2026-11-09 | Quelle offen |
| V-Z5a | Mischbecher PP 50 ml (MA-5) | Einweg-Mischbecher | 20 | [bastelgarage.ch](https://www.bastelgarage.ch/pp-einweg-mischbecher-50ml) | 421219 | PP Einweg-Mischbecher 50 ml | 20 × 1 | 0.30 | 6.00 | Lagernd | 2026-11-09 | kauffertig |
| V-Z5b | Ruehrstaebe (MA-5) | Einweg, Holz | 100 | [bastelgarage.ch](https://www.bastelgarage.ch/ruhrstabe-buche-100-stk) | 421217 | Ruehrstaebe Buche 100 Stk | 1 × 100 | 6.90 | 6.90 | Lagernd | 2026-11-09 | kauffertig |
| V-Z5c | Trichter Abfuellen (MA-5) | Konzept: 2 PE-Trichter | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/silikon-resin-trichter-mit-edelstahl-feinfilter) | 424244 | Silikon-Resin-Trichter mit Edelstahl-Feinfilter | 1 × 1 | 10.90 | 10.90 | Lagernd | 2026-11-09 | Freigabe Sicherheit |
| V-Z5d | Auffangwanne/Alu-Schalen, Pipetten, Spatel, PE-Trichter (MA-5) | Alu-Schalen >= 20 x 15 cm, Einweg-Pipetten, Spatel, PE-Trichter | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 6.00 | 6.00 (A) | - | 2026-11-09 | Quelle offen |
| V-Z6a | Feiner Pinsel Kantenversiegelung | feiner Pinsel (Konzept 7.1 V-Z6) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/synthetik-tabletop-pinsel-grosse-0) | 425342 | Synthetik-Tabletop-Pinsel Groesse 0 (AK Interactive) | 1 × 1 | 6.90 | 6.90 | Lagernd | 2026-11-09 | kauffertig |
| V-Z6b | Einwegspritzen 1/3 ml Luer-Lock, stumpfe Kanuelen 18/20 G | Konzept 7.1 V-Z6 | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 8.00 | 8.00 (A) | - | 2026-11-09 | Quelle offen |
| V-Z7 | Nitrilhandschuhe (K-3) | Nitril >= 0.1 mm, Box, Bestaendigkeitsliste anfordern | 100 | [bastelgarage.ch](https://www.bastelgarage.ch/nitril-schutzhandschuhe-l-100er-pack) | 421782 | Nitril Schutzhandschuhe L 100er Pack (puderfrei) | 1 × 100 | 15.90 | 15.90 | Lagernd | 2026-11-09 | Freigabe Sicherheit |
| V-Z8 | Chemikalien-Schutzbrille EN 166 (dicht) + Visier | EN 166, dicht schliessend | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 30.00 | 30.00 (A) | - | 2026-11-09 | entfaellt, falls vorhanden |
| V-Z9 | Kunststoffschuerze, Augenspuelflasche 500 ml | Konzept 7.1 V-Z9 | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 25.00 | 25.00 (A) | - | 2026-11-09 | Quelle offen |
| V-Z10 | Halbmaske mit Filter A (EN 14387) | Konzept 7.1 V-Z10 | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 40.00 | 40.00 (A) | - | 2026-11-09 | Quelle offen |
| V-Z11 | Thermometer Trockner/Waermeschrank | Kontrolle <= 65 C und 80 C (V-3/V-6) | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 10.00 | 10.00 (A) | - | 2026-11-09 | Quelle offen |
| V-Z12 | Waermeschrank/Filamenttrockner >= 80 C | Haertung 4 h 60 C, V-3/V-6 80 C | 1 | Werkstattbestand | - | - | 1 × 1 | 0.00 | – | vorhanden | 2026-11-09 | vorhanden |
| P1 | LDO 3.3 V (U1) | Torex XC6206P332MR-G | 2 | [LCSC (mit JLC-Bestellung buendeln, ANNAHME)](https://www.lcsc.com/search?q=C5446) | C5446 | USD 0.15 je Stk | 1 × 2 | 0.25 | 0.25 | Basic, 492937 (2026-11-08) | 2026-11-08 | kauffertig |
| P2 | LDO 2.0 V (U2, U3) | Torex XC6206P202MR-G | 3 | [LCSC (mit JLC-Bestellung buendeln, ANNAHME)](https://www.lcsc.com/search?q=C2891260) | C2891260 | USD 0.21 je Stk | 1 × 3 | 0.52 | 0.52 | Extended, 1963 (2026-11-08) | 2026-11-08 | kauffertig |
| P3 | Schmitt-Puffer (U4) | TI SN74AUP1G17DBVR | 2 | [LCSC (mit JLC-Bestellung buendeln, ANNAHME)](https://www.lcsc.com/search?q=C183012) | C183012 | USD 0.31 je Stk | 1 × 2 | 0.52 | 0.52 | Extended, 1280 (2026-11-08) | 2026-11-08 | kauffertig |
| P4 | MLCC 1 uF 50 V 0805 (C1-C4) | Samsung CL21B105KBFNNNE | 5 | [LCSC (mit JLC-Bestellung buendeln, ANNAHME)](https://www.lcsc.com/search?q=C28323) | C28323 | USD 0.03 je Stk | 1 × 5 | 0.12 | 0.12 | Basic | 2026-11-08 | kauffertig |
| P5 | MLCC 100 nF 0805 (C5) | Samsung CL21B104KBCNNNC | 2 | [LCSC (mit JLC-Bestellung buendeln, ANNAHME)](https://www.lcsc.com/search?q=C1711) | C1711 | USD 0.01 je Stk | 1 × 2 | 0.02 | 0.02 | - | 2026-11-08 | kauffertig |
| P6 | R 10 MOhm 1 % 0402 (R1) | UNI-ROYAL 0402WGF1005TCE | 2 | [LCSC (mit JLC-Bestellung buendeln, ANNAHME)](https://www.lcsc.com/search?q=C26082) | C26082 | USD 0.01 je Stk | 1 × 2 | 0.02 | 0.02 | - | 2026-11-08 | kauffertig |
| P7 | R 470 Ohm 1 % 0805 (R2, D-031/PA-6) | UNI-ROYAL 0805W8F4700T5E | 2 | [LCSC (mit JLC-Bestellung buendeln, ANNAHME)](https://www.lcsc.com/search?q=C17710) | C17710 | USD 0.0048 je Stk | 1 × 2 | 0.01 | 0.01 | Basic, 1871834 (2026-11-09) | 2026-11-08 | kauffertig |
| P8 | Federkontaktstifte TP1/TP2 (J3) | Ø <= 1.5 mm, Hub >= 1 mm (README Kap. 4) | 3 | offen (Normteile-/Dichtungs-Fachhandel) | - | - | 1 × 3 | 6.00 | 6.00 (A) | - | 2026-11-09 | Quelle offen |
| P9 | FR4/Lochraster, SOT-23-Adapter, Litze, Steckbruecken, ASA-Buegel | README Kap. 6 Pos. 9/10 | 1 | Werkstattbestand | - | - | 1 × 1 | 0.00 | – | vorhanden | 2026-11-09 | vorhanden |

(A) = Preis ANNAHME bzw. Quelle offen. Bedarf-Herleitung, Register-Ref und Bemerkungen: Spalten in der CSV.

Bemerkungen:

- **S1** (5 Prototyp + 15 Serie + 28 Testzellen (Auftrag ca. 30)): Datenblatt docs/datasheets/Panasonic_CR2032_Datasheet_2026-02.pdf. Ausweichen ohne eigenen Haendler: bastelgarage.ch Varta CR2032 5 Stk Art. 424382 CHF 8.90 lagernd (10 Packungen = 89.00) - weicht von D-006 ab, Varta-Datenblatt fehlt, Energiebudget mit Panasonic gerechnet -> Entscheid Auftraggeber
- **S2** (2 je Sensor x 20 + 10 Passproben/Reserve): Mass belegt docs/references/GTWeed_AS568_StandardOringSizing.pdf S. 2 (Dash -019 0.801 in). Kein CH-Angebot fuer 20.35 x 1.78 Silikon gefunden (Suche 2026-11-09). Werkstoffdatenblatt des Lieferanten ablegen
- **S3** (1 je Sensor x 20 + 5 Reserve): D-032: TX6 handelsueblich (REQ-MECH-15), CAD Kopfhoehe 1.6 nachgefuehrt, Werkzeug TX6 in BATTERIEWECHSEL/MONTAGE
- **S4** (1 je Sensor x 20 + Reserve): Masse laut Shop = Nennmasse ISO 4032 (SW4 x 1.6)
- **S5** (1 Platte fuer 20 + Reserve): Betaetigungskraft PROTOTYP-PRUEFUNG
- **S6** (1 Tube): Datenblatt beim Kauf ablegen
- **S7** (1 Packung (Tuben, je Fenster < 0.05 g)): Entscheid Mechanik 2026-11-09 (Freigabe Orchestrator offen): UHU plus endfest 300. Opak (TDS S. 1) zulaessig, Klebstoff nur an Tropfenrand/Schaftmantel; hochviskos, minimales Laufbestreben (TDS S. 1-2). ER2223 fuer Fenster abgelehnt (schwarz, 800 mPa s, kriecht auf Stirnflaechen). HAERTER AETZEND H314/H318 (SDB-PDF S. 14), Binder H315/H317/H319/H411 -> Schutz MONTAGE_SENSOR Kap. 3 Schritt 1. Haftung ASA im TDS nicht belegt, Klebefuge dicht nach 7 d 65 C = PROTOTYP-PRUEFUNG. Typgleichheit 300 beim Wareneingang pruefen
- **S9** (20 x 13 g + Gateway 14 g + Passproben, < 1 kg): Vorgabe Bambu ASA: Werkstattbestand pruefen (ANNAHME vorhanden), Bambu Lab EU Store ASA Gray (45102) 14.99 EUR nicht an Lager (2026-11-09), Gratisversand CH ab 119 EUR. Bedingte Alternative eSun ASA+ (TDS docs/references/eSUN_ASAplus_TDS_V1.0-2024-06.pdf, HDT 95.5 C bei 0.45 MPa, erst nach PROTOTYP-PRUEFUNG 7 d 65 C, mechanical/PRINT_SETTINGS.md Kap. 1): Grau 424233 ausverkauft, Kaltweiss 424234 lagernd = Abweichung D-010 -> Auftraggeber
- **S10** (20 x ca. 5 g + Gateway 10 g, < 1 kg): Nur falls kein Bambu ASA blau vorhanden (Bambu EU Store Blue 45600 nicht an Lager 2026-11-09). eSun ASA+ erst nach PROTOTYP-PRUEFUNG 7 d 65 C (PRINT_SETTINGS Kap. 1), Farbton/Pigment pruefen
- **S11** (wenige g (Sensor 0.1 g, Gateway 0.1 g je Fenster + Proben)): Entscheid Mechanik 2026-11-09 (Freigabe Orchestrator offen): statt eSun ASA+ Kaltweiss (deckend, Lichtweg Fenster 4.0 mm massiv) und PETG natur (HDT 64 C). TDS V6.0 lokal: HDT 100 C (1.8 MPa). Transluzenz im TDS nicht angegeben (N/A) -> LED-Sichtbarkeit PROTOTYP-PRUEFUNG. Nur 1 Stk an Lager; Ausweichquelle digitec.ch (Polymaker PolyLite ASA Natural, nicht abrufbar, ANNAHME)
- **G2** (1 Gateway): Konformitaet beim Wareneingang (Sicherheits-Agent), Datenblatt fehlt (F-8)
- **G3** (1 Gateway): Datenblatt docs/datasheets/Kingston_SDCIT2_Datasheet_MKD-02122026.pdf. Grosshandel alltron.ch: 100 Stk auf 23.11.2026 bestellt. Sofort-Alternative gleicher Serie: mediamarkt.ch Marktplatz Ultimus.ch SDCIT2/8GB CHF 56.95 (Lieferung 27.11.-01.12.) bzw. 16 GB CHF 63.95, versandkostenfrei
- **G6** (1 Gateway): Masszeichnung/Schaltplan lokal (docs/datasheets/DFRobot_SEN0428_*). Halter im Gehaeuse: Bodenschiene Nut 1.90 + Deckelrippe (mechanical/gateway_pi/check_gateway_pi.txt Pkt. 14). Platinendicke 1.6 ANNAHME -> am Muster messen
- **G8a** (4 je Gateway): D-032: Rohr Ø7.0 mit Fuss Ø5.6, Bohrung 3.9, Tiefe 5.2 (check_gateway_pi.txt Pkt. 33). Kleinere Packung nicht gefunden
- **G8b** (4 je Gateway): bastelgarage M2.5-Sortiment DIN 912 ausverkauft (2026-11-09) und Zylinderkopf statt Linsenkopf
- **G9** (1 Gateway): Digi-Key-Versand unter 70 CHF = 23 CHF -> nicht einzeln bestellen: mit LCSC-Bestellung Programmieradapter buendeln (LCSC-Teile durch Elektronik waehlen) oder Werkstattbestand. BOM_GATEWAY G9 nachfuehren = Elektronik
- **G10** (Werkstatt): bastelgarage Schrumpfschlauch-Set 140 Stk ausverkauft (2026-11-09)
- **W1** (1 Programmierplatz): Elektronik 2026-11-09: freigegeben mit Bedingungen B1-B6 (hardware/programmer/README.md Kap. 9, EINKAUFSLISTE.md Kap. 3). Original CH343 (TOOL-UART1): waveshare.com USD 3.49 + Versand (nicht ablesbar) bzw. eckstein-shop.de EUR 4.15 (ca. 3 Wochen) -> eigener Auslandsversand
- **V-M1** (1 Beutel je Bauserie (Prototyp, Serie), Haltbarkeit 3 Monate nach Abfuellen (MA-3)): LIEFERZEIT 8 WOCHEN -> sofort nach Freigabe bestellen. Vor dem ersten Beutel SDB Teil B in DE/EN/FR/IT anfordern (D-030 Bed. 1). Versand Simpex nicht angegeben (ANNAHME 15 CHF). simpex.ch fuer automatischen Abruf gesperrt (403, 2026-11-09)
- **V-Z1** (1 Arbeitsplatz): ENTFAELLT, FALLS VORHANDEN. Kein Justiergewicht im Lieferumfang -> Kontrolle mit Pruefgewichten V-Z2 vor jeder Sitzung (MA-4), Genauigkeit nicht angegeben
- **V-Z2** (1 Satz): Keine CH-Quelle mit abrufbarem Preis (bastelgarage: Kalibriergewicht nur im Set der ausverkauften CX-Waage)
- **V-Z3** (1 Satz): -
- **V-Z4** (1 Satz): -
- **V-Z5a** (ca. 10 Ansaetze + Abfuellen + Reserve): Shop: nicht loesungsmittelbestaendig
- **V-Z5b** (1 Packung): -
- **V-Z5c** (1 hier + 1 PE-Trichter in V-Z5d): Silikon statt PE (Konzept) -> Bestaendigkeit gegen Haerter B (Amin) durch Sicherheit bestaetigen, sonst nur PE-Trichter (V-Z5d)
- **V-Z5d** (1 Satz): -
- **V-Z6a** (1 Stk): -
- **V-Z6b** (1 Satz): -
- **V-Z7** (1 Box): Wandstaerke und Norm (EN 374) im Shop nicht angegeben -> Sicherheit pruefen, Groesse L (XL in der Suche ebenfalls gefuehrt)
- **V-Z8** (1 Satz): ENTFAELLT, FALLS VORHANDEN. bastelgarage fuehrt nur Laserschutzbrillen (ungeeignet)
- **V-Z9** (1 Satz): -
- **V-Z10** (1 Stk): -
- **V-Z11** (1 Stk): bastelgarage 422448 misst nur bis 70 C -> ungeeignet fuer 80 C
- **V-Z12** (Werkstatt): ENTFAELLT, FALLS VORHANDEN (ANNAHME vorhanden, nicht gerechnet), sonst Beschaffung klaeren
- **P1** (1 + Reserve): -
- **P2** (2 + Reserve): -
- **P3** (1 + Reserve): -
- **P4** (4 + Reserve): -
- **P5** (1 + Reserve): -
- **P6** (1 + Reserve): -
- **P7** (1 + Reserve): -
- **P8** (2 + Reserve): Typ mit Mechanik festlegen (P-J3)
- **P9** (Werkstatt): ENTFAELLT, FALLS VORHANDEN

## 7 Händlergruppierung und Versand

| Händler | Positionen | Ware CHF | Versand CHF | Total CHF | davon jetzt lieferbar | Versandregel |
|---|---|---|---|---|---|---|
| offen (Labor-/Arbeitsschutz-Fachhandel) | V-Z2, V-Z3, V-Z4, V-Z5d, V-Z6b, V-Z8, V-Z9, V-Z10, V-Z11 | 179.00 | 10.00 | 189.00 | 0.00 (+0.00 Versand) | ANNAHME (Haendler offen, eine Sammelbestellung V-Z2...V-Z11) |
| bastelgarage.ch | S3, S4, S7, S9, S10, G6, G8a, V-Z1, V-Z5a, V-Z5b, V-Z5c, V-Z6a, V-Z7 | 165.40 | 0.00 | 165.40 | 145.50 (+0.00 Versand) | bastelgarage.ch/lieferung-versandkosten (2026-11-09): PostPac Economy 6.90, Priority 8.90, ab CHF 80 Warenwert gratis (docs/references/Haendler_Einkauf_Auszug_2026-11-09.txt) |
| Simpex Electronic AG | V-M1 | 82.58 | 15.00 | 97.58 | 82.58 (+15.00 Versand) | ANNAHME (Versandbetrag laut Konzept Kap. 7 nicht angegeben) |
| pi-shop.ch | G2, G3, W1 | 48.70 | 7.90 | 56.60 | 20.80 (+7.90 Versand) | pi-shop.ch/versandkosten (2026-11-08): B-Post 7.90, A-Post 9.90 (docs/references/pi-shop_Gateway-Teile_Auszug_2026-11-08.txt) |
| galaxus.ch | S1 | 39.84 | 9.90 | 49.74 | 39.84 (+9.90 Versand) | ANNAHME (Versandseite nicht abrufbar, Bot-Sperre) |
| offen (Normteile-/Dichtungs-Fachhandel) | S2, S5, S6, G8b, P8 | 32.50 | 10.00 | 42.50 | 0.00 (+0.00 Versand) | ANNAHME (Haendler offen, eine Sammelbestellung S2/S5/S6/G8b/P8) |
| 3djake.ch | S11 | 23.75 | 8.90 | 32.65 | 23.75 (+8.90 Versand) | 3djake.ch/de-CH/hilfe/versandkosten (2026-11-09): Standardversand Schweiz 8.90, ab CHF 69.90 gratis (docs/references/3DJake_PolymakerASA-Natural_Auszug_2026-11-09.txt) |
| LCSC (mit JLC-Bestellung buendeln, ANNAHME) | P1, P2, P3, P4, P5, P6, P7 | 1.46 | 20.00 | 21.46 | 1.46 (+20.00 Versand) | ANNAHME (README Kap. 6: 10-25 CHF), Kombination mit der JLC-Sendung im Warenkorb pruefen |
| Digi-Key CH (laut phase5_gateway_led.md) | G9 | 0.29 | 0.00 | 0.29 | 0.29 (+0.00 Versand) | nicht einzeln bestellen (23 CHF Versand unter 70 CHF, docs/reviews/phase5_gateway_led.md): mit LCSC-Bestellung Programmieradapter buendeln |
| **Summe** | | **573.52** | **81.70** | **655.22** | | |

- bastelgarage.ch: geplant 165.40 CHF → versandkostenfrei; jetzt lieferbar 145.50 CHF (ohne ausverkauftes Grau) → frei.
- pi-shop.ch: G2 + W1 + G3 in **einer** Sendung, sobald G3 an Lager ist; getrennt bestellt kostet die zweite Sendung nochmals 7.90 CHF.
- Normteile/Dichtungen (S2, S5, S6, G8b, P8): **ein** Fachhändler für alles; noch keiner mit abrufbarem Angebot (Versand ANNAHME 10 CHF).
- G9 (Gateway-LED, D-027): nicht bei Digi-Key einzeln bestellen (23 CHF Versand), sondern in die LCSC-Bestellung des Programmieradapters legen (Teilewahl Elektronik).
- JLC (PCBA Sensor) und Verguss (S8) sind separat (ORDER_JLC_REV_C.md bzw. Material-Agent).

## 8 Summen je Bereich (Ware, ohne Versand)

| Bereich | Positionen | Ware CHF | davon ANNAHME CHF |
|---|---|---|---|
| Sensor | 6 | 58.80 | 25.50 |
| Sensor+Werkstatt | 1 | 39.84 | 39.84 |
| Sensor+Gateway | 3 | 63.55 | 0.00 |
| Gateway | 6 | 68.89 | 1.00 |
| Werkstatt | 1 | 8.90 | 0.00 |
| Verguss | 16 | 326.08 | 179.00 |
| Programmieradapter | 8 | 7.46 | 6.00 |

Verguss-Zubehör (V-Z…) ohne Beutel: **243.50 CHF** (geht als Einmalkosten in `scripts/cost_final_phase5.py`); Programmieradapter (P…, W1, LCSC-Versand ANNAHME) siehe Kap. 7.

## 9 Prüfhinweise (`scripts/einkaufsliste.py --check`)

- S1: Preis ANNAHME/Quelle offen (39.84 CHF)
- S2: Preis ANNAHME/Quelle offen (7.50 CHF)
- S5: Preis ANNAHME/Quelle offen (10.00 CHF)
- S6: Preis ANNAHME/Quelle offen (8.00 CHF)
- S9: bastelgarage.ch Ausverkauft (Abruf 2026-11-09)
- G3: pi-shop.ch nicht an Lager (Abruf 2026-11-09)
- G8b: Preis ANNAHME/Quelle offen (1.00 CHF)
- V-Z2: Preis ANNAHME/Quelle offen (20.00 CHF)
- V-Z3: Preis ANNAHME/Quelle offen (15.00 CHF)
- V-Z4: Preis ANNAHME/Quelle offen (25.00 CHF)
- V-Z5d: Preis ANNAHME/Quelle offen (6.00 CHF)
- V-Z6b: Preis ANNAHME/Quelle offen (8.00 CHF)
- V-Z8: Preis ANNAHME/Quelle offen (30.00 CHF)
- V-Z9: Preis ANNAHME/Quelle offen (25.00 CHF)
- V-Z10: Preis ANNAHME/Quelle offen (40.00 CHF)
- V-Z11: Preis ANNAHME/Quelle offen (10.00 CHF)
- P8: Preis ANNAHME/Quelle offen (6.00 CHF)
