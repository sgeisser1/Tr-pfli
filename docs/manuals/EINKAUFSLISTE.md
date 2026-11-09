# fluidi – Einkaufsliste (alles ausser JLC)

| | |
|---|---|
| Stand | 2026-11-09, erzeugt von `.venv/bin/python scripts/einkaufsliste.py` aus `docs/manuals/EINKAUFSLISTE.csv` (nicht von Hand ändern) |
| Umfang | Sensor (Prototyp 5 + Serie 15), Gateway (D-028 ohne RTC, D-029 SHT40-Breakout), Werkstatt (USB-UART, Testzellen) |
| Belege | `docs/references/Haendler_Einkauf_Auszug_2026-11-09.txt`, `docs/references/pi-shop_Gateway-Teile_Auszug_2026-11-08.txt`, Register `docs/datasheets/INDEX.csv` |
| Nicht abrufbar | digitec/galaxus, mouser.ch, distrelec.ch, digikey.ch, conrad.ch, brack.ch, toppreise.ch (Bot-Sperre/403) → Preise von dort sind **ANNAHME** |
| Hinweis | Keine Bestellung ausgelöst. Preise inkl. MWST, Lager = Anzeige am Abruftag |

## 1 Fazit

- Warenwert geplant **587.81 CHF** + Versand **81.70 CHF** = **669.51 CHF** (davon 292.64 CHF Preis-ANNAHME; ohne JLC, ohne Werkstattbestand; Summen je Bereich Kap. 8).
- **Händler mit Bestellung: 8** (galaxus.ch, bastelgarage.ch, offen (Labor-/Arbeitsschutz-Fachhandel), Simpex Electronic AG, pi-shop.ch, offen (Normteile-/Dichtungs-Fachhandel), 3djake.ch, LCSC (mit JLC-Bestellung buendeln, ANNAHME)). Kern sind **zwei** CH-Händler: bastelgarage.ch und pi-shop.ch; dazu Simpex (Verguss, 8 Wochen Lieferzeit) und LCSC (mit JLC bündeln).
- Ein Händler weniger möglich: Zellen bei bastelgarage.ch (Varta statt Panasonic, Entscheid Auftraggeber, S1).
- Bestellreihenfolge (Red Team W-3d): **zuerst Verguss** (V-M1, 8 Wochen; Distrelec/RS von Hand vergleichen), dann JLC (mit BT1-Vorrat 25 Stk, ORDER Kap. 4 Nr. 8a) und LCSC, dann der Rest.
- Offen: Quelle O-Ringe AS568-019 Silikon, ISO 7380 M2.5×8, Silikonplatte, Federstifte (Normteile-/Dichtungshändler) und Prüfgewichte, Flaschen, Sekundärbehälter, PE-Trichter, Spritzen, Thermometer (Laborhändler); Filament grau und microSD nicht an Lager. Werkstatt Weg B (WB-1…WB-24) in Kap. 8a, entfällt, falls vorhanden; Dummy-Platinen über JLC (ORDER Kap. 4 Nr. 8b).

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
mit Schweizer Shopbeleg bei bastelgarage.ch (ohnehin in der Liste) Feinwaage, Mischbecher, Rührstäbe, Pinsel. Nach Red Team W-3
liegen Handschuhe (MAPA Solo 977, 0.13 mm, EN ISO 374-1, TDS und Beständigkeitstabelle lokal), Korbbrille + Visier,
Augenspülflasche/Schürze und Halbmaske A bei **galaxus.ch** (ohnehin für die Zellen in der Liste; Listings per Suchmaschine,
Seiten gesperrt → Preise teils **ANNAHME**). Ohne gefundene Quelle bleiben Prüfgewichte, kindergesicherte Flaschen,
Sekundärbehälter, 2 PE-Einwegtrichter, Spritzen/Kanülen und Thermometer bis 80 °C (Laborhändler, **ANNAHME** Kap. 7.1).

**Pflicht vor dem Öffnen des ersten Beutels (D-030 Bed. 1, Sicherheit K-7):** V-Z7 Handschuhe mit Beständigkeitsliste,
V-Z8 Korbbrille nach **EN 166 mit Kennzeichnung 3** (Flüssigkeiten) **und** Visier – eine vorhandene Brille zählt nur mit
dieser Kennzeichnung –, V-Z9 Augenspülflasche und Schürze, V-Z10 Halbmaske mit Filter A (EN 14387) bzw. Absaugung
(SDB B Abschn. 7.1/8.2). Der Silikontrichter mit Feinfilter ist gestrichen (Sicherheit W-4), stattdessen 2 PE-Einwegtrichter
(A/B getrennt, V-Z5d). **Entfällt, falls vorhanden:** Feinwaage (V-Z1), Wärmeschrank (V-Z12), TX6-Schraubenzieher (W3).
Waage ohne Justiergewicht → Prüfgewichte V-Z2 nötig.

**Programmieradapter:** Teile nach `hardware/programmer/README.md` Kap. 2.1/6 (inkl. R2 470 Ω C17710, D-031/PA-6) bei LCSC,
Preise der JLC/LCSC-Teilesuche umgerechnet mit dem Kurs aus `scripts/cost_model.py`; LCSC-Mindestmengen und Versand
**ANNAHME** (README: 10–25 CHF) – mit der JLC-Bestellung im selben Warenkorb prüfen. USB-UART = W1 (PL2303, pi-shop.ch).

## 6 Liste

| ID | Teil | Soll | Bedarf | Händler | Art.-Nr. | Angebot | Pack. × Inhalt | CHF/Pack. | Summe CHF | Lager | Abruf | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 | Knopfzelle CR2032 (Sensor 20 + Tests 28) | Panasonic CR2032 (D-006) | 48 | [galaxus.ch](https://www.galaxus.ch/en/s1/product/panasonic-cr2032-lithium-48-knopfbatterien-48-pcs-cr2032-225-mah-batteries-61927007) | 61927007 | Panasonic CR2032 Lithium 48 Knopfbatterien | 1 × 48 | 39.84 | 39.84 (A) | ANNAHME (Auszug: wenige Packungen, Drittanbieter) | 2026-11-08 | Preis pruefen |
| S2 | O-Ring Huelse/Kragen + Zapfen | AS568-019 = ID 20.35 x CS 1.78 mm, EPDM (nicht Silikon), nicht schwarz/ohne Russ bevorzugt, Werkstoffdatenblatt Lieferant | 50 | offen (Normteile-/Dichtungs-Fachhandel) | - | - | 50 × 1 | 0.15 | 7.50 (A) | - | 2026-11-09 | Quelle offen |
| S3 | Batteriefachschraube (nicht unverlierbar) | M2 x 3 A2 Linsenkopf Torx TX6, Kopfhoehe 1.6 (D-032, ersetzt ISO 7045 PH1) | 25 | [bastelgarage.ch](https://www.bastelgarage.ch/10-stuck-m2x3mm-linsenkopfschrauben-set-rostfrei) | 422191 | 10 Stueck M2x3mm Linsenkopfschrauben Set rostfrei (A2, Torx TX6, Kopfhoehe 1.6) | 3 × 10 | 3.90 | 11.70 | Lagernd | 2026-11-09 | kauffertig |
| S4 | Mutter im Kragen eingegossen | ISO 4032 M2 A2 SW4 x 1.6 | 30 | [bastelgarage.ch](https://www.bastelgarage.ch/10-stuck-m2-mutter-set-rostfrei) | 422198 | 10 Stueck M2 Mutter Set rostfrei (A2, SW4, Hoehe 1.6) | 3 × 10 | 2.90 | 8.70 | Lagernd | 2026-11-09 | kauffertig |
| S5 | Tastenmembran | Silikonplatte 0.5 mm Shore A 40-60, Ø6.4 gestanzt | 1 | offen (Normteile-/Dichtungs-Fachhandel) | - | - | 1 × 1 | 10.00 | 10.00 (A) | - | 2026-11-09 | Quelle offen |
| S6 | Silikonfett fuer O-Ringe | Silikonfett fuer EPDM-O-Ringe (S2), duenner Film; mit Datenblatt | 1 | [galaxus.ch](https://www.galaxus.ch) | E-coll Silikonfett (Kategorie Dichtmittel) | E-coll Silikonfett, -45...+200 C (Suchtreffer) | 1 × 1 | 9.90 | 9.90 (A) | - | 2026-11-09 | Quelle offen |
| S7 | Kleber Lichtfenster | 2K-Epoxid, hochviskos, -40...+100 C, Transparenz nicht noetig (Fuge 0.1 mm nicht im Lichtweg, PRINT_SETTINGS Kap. 5) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/uhu-plus-endfest-zweikomponenten-epoxidkleber-33g) | 422137 | UHU Plus Endfest 2K-Epoxid 33 g (-40...+100 C laut Shop) | 1 × 1 | 12.90 | 12.90 | Lagernd | 2026-11-09 | Freigabe Orchestrator |
| S9 | Filament ASA grau (Huelse, Wanne) | Vorgabe Bambu ASA (MAT-ASA, TDS lokal), Warmgrau nach Musterdruck (D-010), Pigment ohne Russ, bedingte Alternative eSun ASA+ (MAT-ASA2, D-032) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/asa-grau-filament-1-75mm-1kg-esun) | 424233 | eSun ASA+ Grau 1.75 mm 1 kg | 1 × 1 | 19.90 | 19.90 | Ausverkauft | 2026-11-09 | nicht an Lager |
| S10 | Filament ASA blau (Kappe, Taste, Deckel) | Vorgabe Bambu ASA Hellblau (MAT-ASA), Pigment ohne Russ/Metall (Antennenbereich), bedingte Alternative eSun ASA+ Blau (MAT-ASA2, D-032) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/asa-blau-filament-1-75mm-1kg-esun) | 424238 | eSun ASA+ Blau 1.75 mm 1 kg | 1 × 1 | 19.90 | 19.90 | Lagernd | 2026-11-09 | bedingt (D-032) |
| S11 | Filament Lichtfenster ASA natur | ASA unpigmentiert natur (PRINT_SETTINGS Kap. 1), HDT >= 80 C mit TDS, kein PETG, kein deckendes Weiss | 1 | [3djake.ch](https://www.3djake.ch/de-CH/polymaker/polymaker-asa-natur) | PM-PF01006 | Polymaker ASA Natural 1.75 mm 1 kg (PF01006) | 1 × 1 | 23.75 | 23.75 | Lagernd (1 Stk) | 2026-11-09 | Freigabe Orchestrator |
| S12 | Kennungsetikett (laminiertes Schriftband 9 mm) + Etikettendrucker | laminiertes Kunststoff-Schriftband 9 mm schwarz auf weiss (z. B. Brother TZe, ANNAHME Typ), kein Metall; Ersatz wetterfestes Laser-Folienetikett (MONTAGE Kap. 7a) | 1 | Werkstattbestand | - | - | 1 × 1 | 0.00 | – | vorhanden | 2026-11-09 | vorhanden |
| G2 | Netzteil 5 V 2.5 A Micro-USB | Raspberry Pi 12.5 W Micro-USB Original | 1 | [pi-shop.ch](https://www.pi-shop.ch/raspberry-pi-12-5w-micro-usb-power-supply-2254) | 11715 | Raspberry Pi 12.5W Micro USB Power Supply | 1 × 1 | 11.90 | 11.90 | Sofort-Versand ab Lager | 2026-11-09 | kauffertig |
| G3 | microSD Industrial | Industrial/pSLC >= 8 GB (GATEWAY_SETUP Kap. 1) | 1 | [pi-shop.ch](https://www.pi-shop.ch/kingston-microsdhc-karte-industrial-uhs-i-16-gb) | 10951 | Kingston microSDHC Industrial UHS-I 16 GB (SDCIT2/16GB) | 1 × 1 | 27.90 | 27.90 | nicht an Lager | 2026-11-09 | nicht an Lager |
| G6 | Klimasensor-Breakout (D-029) | SHT40/41/45, I2C 0x44, 3.3 V, hochkant <= 17 x 14 mm (Bodenschiene + Deckelrippe, D-032) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/fermion-temperatur-und-feuchtigkeitssensor-sht40) | 421989 | DFRobot Fermion SHT40 Breakout SEN0428 (14 x 17 mm) | 1 × 1 | 11.90 | 11.90 | Lagernd | 2026-11-09 | kauffertig |
| G8a | Gewindeeinsaetze M2.5 (4 je Gateway) | M2.5 x 4 x Ø4.6 Messing, Bohrung 3.9 (Haendlerangabe, D-032) | 4 | [bastelgarage.ch](https://www.bastelgarage.ch/m2-5-4mm-gewindeeinsatze-messing-heat-insert-100stk) | 425681 | Gewindeeinsaetze Messing M2.5 x 4 x Ø4.6, 100 Stk | 1 × 100 | 15.90 | 15.90 | Lagernd | 2026-11-09 | kauffertig |
| G8b | Schrauben M2.5 x 8 (4 je Gateway) | ISO 7380 Linsenkopf M2.5 x 8 A2 (Nylon als Option, PRINT_SETTINGS Kap. 4) | 4 | offen (Normteile-/Dichtungs-Fachhandel) | - | - | 4 × 1 | 0.25 | 1.00 (A) | - | 2026-11-09 | Quelle offen |
| G9 | Status-LED 3 mm gruen + Vorwiderstand 470 Ohm (D-027) | Kingbright WP710A10GD (3 mm gruen, D-027) + Vorwiderstand 470 Ohm 1/4 W | 1 | [LCSC (mit JLC-Bestellung buendeln, ANNAHME)](https://www.lcsc.com/search?q=C6001420) | C6001420 / C119317 | WP710A10GD USD 0.0813 + CCO MF1/4W-470R 1 % USD 0.0112 | 1 × 1 | 0.08 | 0.08 | 71 / 16455 (2026-11-09) | 2026-11-09 | kauffertig |
| G10 | Litze AWG 28, Schrumpfschlauch | - | 1 | Werkstattbestand | - | - | 1 × 1 | 0.00 | – | vorhanden | 2026-11-08 | vorhanden |
| W1 | USB-UART mit externem VIO 2.0 V (FW-T3) | VIO extern 1.8-2.0 V, kein Rueckstrom, ROM-Bootloader 19200-57600 Baud | 1 | [pi-shop.ch](https://www.pi-shop.ch/pl2303-usb-to-uart-ttl-communication-module-v2) | 11757 | Waveshare PL2303 USB UART Board (type A) V2 (PL2303GS) | 1 × 1 | 8.90 | 8.90 | Sofort-Versand ab Lager | 2026-11-09 | kauffertig |
| W3 | Schraubenzieher Torx TX6 (Batteriefach, D-032) | TX6 / T6 Feinschraubendreher | 1 | [galaxus.ch](https://www.galaxus.ch/de/s4/product/wiha-torx-schraubenzieher-torx-tx-schraubenzieher-9979617) | Wiha Torx-Schraubenzieher T6 (9979617) | Wiha Torx T6, Klinge 35 mm, CHF 6.50 (Suchtreffer) | 1 × 1 | 6.50 | 6.50 (A) | - | 2026-11-09 | entfaellt, falls vorhanden |
| V-M1 | Vergussmasse Schott/Kragen/Sondenkante (D-030) | Electrolube ER2223 Resin Pack 250 g (EER2223RP250G) | 2 | [Simpex Electronic AG](https://www.simpex.ch) | EER2223RP250G | ER2223 Resin Pack 250 g, CHF 38.20 exkl. MWST | 2 × 1 | 41.29 | 82.58 | In stock: available to order, LIEFERZEIT 8 WOCHEN | 2026-11-08 | kauffertig (frueh bestellen) |
| V-Z1 | Feinwaage (MA-4) | 0.01 g Aufloesung, >= 200 g (Konzept 7.1 V-Z1) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/digitale-feinwaage-mh-500-0-01g-500g) | 424394 | Digitale Feinwaage MH-500 0.01-500 g (Mindestgewicht 0.05 g, ohne Justiergewicht) | 1 × 1 | 17.90 | 17.90 | Lagernd | 2026-11-09 | entfaellt, falls vorhanden |
| V-Z2 | Pruefgewichte 1 g und 5 g (MA-4) | Klasse F1 oder M1 | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 20.00 | 20.00 (A) | - | 2026-11-09 | Quelle offen |
| V-Z3 | Laborflaschen kindergesichert, Etiketten, Farbmarker (MA-1/MA-2) | B: HDPE ca. 60 ml, A: HDPE/Glas ca. 250 ml | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 15.00 | 15.00 (A) | - | 2026-11-09 | Quelle offen |
| V-Z4 | Sekundaerbehaelter abschliessbar + Saugmaterial (MA-1) | dichte Kunststoffbox, Vorhaengeschloss, Vermiculit/Katzenstreu | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 25.00 | 25.00 (A) | - | 2026-11-09 | Quelle offen |
| V-Z5a | Mischbecher PP 50 ml (MA-5) | Einweg-Mischbecher | 20 | [bastelgarage.ch](https://www.bastelgarage.ch/pp-einweg-mischbecher-50ml) | 421219 | PP Einweg-Mischbecher 50 ml | 20 × 1 | 0.30 | 6.00 | Lagernd | 2026-11-09 | kauffertig |
| V-Z5b | Ruehrstaebe (MA-5) | Einweg, Holz | 100 | [bastelgarage.ch](https://www.bastelgarage.ch/ruhrstabe-buche-100-stk) | 421217 | Ruehrstaebe Buche 100 Stk | 1 × 100 | 6.90 | 6.90 | Lagernd | 2026-11-09 | kauffertig |
| V-Z5d | 2 PE-Einwegtrichter (A und B getrennt) + Auffangwanne/Alu-Schalen, Pipetten, Spatel (MA-5) | 2 PE-Einwegtrichter beschriftet A/B, nach dem Abfuellen mit dem Beutel entsorgen; Alu-Schalen >= 20 x 15 cm, Einweg-Pipetten, Spatel | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 6.00 | 6.00 (A) | - | 2026-11-09 | Quelle offen |
| V-Z6a | Feiner Pinsel Kantenversiegelung | feiner Pinsel (Konzept 7.1 V-Z6) | 1 | [bastelgarage.ch](https://www.bastelgarage.ch/synthetik-tabletop-pinsel-grosse-0) | 425342 | Synthetik-Tabletop-Pinsel Groesse 0 (AK Interactive) | 1 × 1 | 6.90 | 6.90 | Lagernd | 2026-11-09 | kauffertig |
| V-Z6b | Einwegspritzen 1/3 ml Luer-Lock, stumpfe Kanuelen 18/20 G | Konzept 7.1 V-Z6 | 1 | offen (Labor-/Arbeitsschutz-Fachhandel) | - | - | 1 × 1 | 8.00 | 8.00 (A) | - | 2026-11-09 | Quelle offen |
| V-Z7 | Nitrilhandschuhe (K-3) | Nitril >= 0.1 mm, Box, Bestaendigkeitsliste anfordern | 100 | [galaxus.ch](https://www.galaxus.ch) | MAPA Solo 977 (Galaxus-Listing Groesse 9) | MAPA Solo 977 Einweg-Nitril, 0.13 mm, EN ISO 374-1 Typ B, EN ISO 374-5 | 1 × 100 | 25.00 | 25.00 (A) | - | 2026-11-09 | freigegeben (Sicherheit, Spritzschutz) |
| V-Z8 | Chemikalien-Schutzbrille EN 166 (dicht) + Visier | EN 166, dicht schliessend | 1 | [galaxus.ch](https://www.galaxus.ch/de/s4/product/3m-2890sa-vollschutzbrille-schutzbrille-gesichtsschutz-44076729) | 3M 2890SA Vollschutzbrille (44076729) + BGS Gesichtsschutzschild (37517649) | gasdichte Korbbrille Acetat + Visier | 1 × 1 | 30.00 | 30.00 (A) | - | 2026-11-09 | PFLICHT vor dem ersten Beutel |
| V-Z9 | Kunststoffschuerze, Augenspuelflasche 500 ml | Konzept 7.1 V-Z9 | 1 | [galaxus.ch](https://www.galaxus.ch/en/s6/product/first-aid-only-eye-wash-bottle-first-aid-set-accessories-first-aid-8933524) | First Aid Only Eye wash bottle 500 ml (8933524) + Kunststoffschuerze | Augenspuelflasche 500 ml NaCl 0.9 % CHF 22.90 (Suchtreffer) + Schuerze | 1 × 1 | 32.90 | 32.90 (A) | - | 2026-11-09 | PFLICHT vor dem ersten Beutel |
| V-Z10 | Halbmaske mit Filter A (EN 14387) | Konzept 7.1 V-Z10 | 1 | [galaxus.ch](https://www.galaxus.ch/de/s4/product/3m-halbmaske-mit-wechselfiltern-a2p2-atemschutzmaske-9744120) | 3M Halbmaske mit Wechselfiltern A2P2 (9744120) | Halbmaske mit Filter A2P2 (EN 14387) | 1 × 1 | 40.00 | 40.00 (A) | - | 2026-11-09 | PFLICHT vor dem ersten Beutel |
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
| WB-1 | Labornetzteil | 0-3 V, Aufloesung <= 10 mV, Strombegrenzung einstellbar 10 mA, Ausgang schaltbar | 1 | Werkstattbestand | - | - | 1 × 1 | 60.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-2 | Multimeter | DC 2 V mit 1 mV, Widerstand >= 20 MOhm, Durchgang | 1 | Werkstattbestand | - | - | 1 × 1 | 40.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-3 | Messschieber | Aufloesung 0.01 mm | 1 | Werkstattbestand | - | - | 1 × 1 | 20.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-4 | Loetstation | temperaturgeregelt, Spitze <= 0.4 mm | 1 | Werkstattbestand | - | - | 1 × 1 | 60.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-5 | Loetzinn + Flussmittel | 0.3-0.5 mm mit Seele, No-clean-Flussmittelstift | 1 | Werkstattbestand | - | - | 1 × 1 | 15.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-6 | Entloetlitze | 1-1.5 mm | 1 | Werkstattbestand | - | - | 1 × 1 | 5.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-7 | Kupferlackdraht | 0.1-0.2 mm selbstverzinnend | 1 | Werkstattbestand | - | - | 1 × 1 | 8.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-8 | Kaptonband | ca. 0.06 mm | 1 | Werkstattbestand | - | - | 1 × 1 | 8.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-9 | Lupe oder Stereomikroskop | >= 10x | 1 | Werkstattbestand | - | - | 1 × 1 | 25.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-10 | Kamera/Smartphone | Makro durch die Lupe | 1 | Werkstattbestand | - | - | 1 × 1 | 0.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-11 | Feine Pinzette | antimagnetisch | 1 | Werkstattbestand | - | - | 1 × 1 | 8.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-12 | Kunststoffpinzette/-spatel | kein Metall | 1 | Werkstattbestand | - | - | 1 × 1 | 5.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-13 | Isopropanol >= 99 %, Pinsel/Wattestaebchen | - | 1 | Werkstattbestand | - | - | 1 × 1 | 10.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-14 | Pruefspitze/Federstift flacher Kopf + Kabel | Kopf Ø <= 1.5 mm, keine Krone | 1 | Werkstattbestand | - | - | 1 × 1 | 10.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-15 | Platinenhalter (dritte Hand) | nicht leitende Backen | 1 | Werkstattbestand | - | - | 1 × 1 | 15.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-16 | USB-UART-Board | PL2303 type A V2 = W1 (oder CH343) | 1 | Werkstattbestand | - | - | 1 × 1 | 0.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-17 | Steckbruecken | Dupont 10-20 cm | 1 | Werkstattbestand | - | - | 1 × 1 | 5.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-18 | PC mit WSL2 oder Raspberry Pi | flash_sensor.py, pyserial, intelhex | 1 | Werkstattbestand | - | - | 1 × 1 | 0.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-19 | Dummy-Scheibe PLUS 1.0 + MINUS 2.0 mm | hardware/dummy_cell (JLC, je 5 Stk, ORDER Kap. 4 Nr. 8b) | 1 | Werkstattbestand | - | - | 1 × 1 | 0.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-20 | Litze rot/schwarz + Krokodilklemmen/4-mm-Stecker | 0.14-0.25 mm2, 20-30 cm | 1 | Werkstattbestand | - | - | 1 × 1 | 5.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-21 | Isolierender 2K-Epoxidkleber, 2 Stifte Ø 1.0 mm, Schleifpapier 400 | duennfluessig | 1 | Werkstattbestand | - | - | 1 × 1 | 5.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-22 | Neue Zellen CR2032 | Leerlauf >= 3.0 V | 1 | Werkstattbestand | - | - | 1 × 1 | 0.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-23 | Behaelter fuer Altzellen, Klebeband | - | 1 | Werkstattbestand | - | - | 1 × 1 | 0.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |
| WB-24 | ESD-Unterlage (empfohlen) | sauberer trockener Arbeitsplatz | 1 | Werkstattbestand | - | - | 1 × 1 | 20.00 | – | - | 2026-11-09 | entfaellt, falls vorhanden (Werkstatt) |

(A) = Preis ANNAHME bzw. Quelle offen. Bedarf-Herleitung, Register-Ref und Bemerkungen: Spalten in der CSV.

Bemerkungen:

- **S1** (5 Prototyp + 15 Serie + 28 Testzellen (Auftrag ca. 30)): Datenblatt docs/datasheets/Panasonic_CR2032_Datasheet_2026-02.pdf. Ausweichen ohne eigenen Haendler: bastelgarage.ch Varta CR2032 5 Stk Art. 424382 CHF 8.90 lagernd (10 Packungen = 89.00) - weicht von D-006 ab, Varta-Datenblatt fehlt, Energiebudget mit Panasonic gerechnet -> Entscheid Auftraggeber. WARENEINGANG (Sicherheit W-6): bevorzugt Haendler-Eigenware in Blisterpackung statt Marktplatz; pruefen: Panasonic-Originalverpackung, Los-/Datumscode, Stichprobe 3 Zellen Dicke <= 3.2 mm (Panasonic_CR2032_Datasheet_2026-02.pdf S. 1) und Leerlaufspannung, keine Beschaedigung. Lose oder nicht kindergesicherte Zellen in abschliessbarer Box lagern (Box V-Z4 mitbenutzen oder eigene)
- **S2** (2 je Sensor x 20 + 10 Passproben/Reserve): Mass belegt docs/references/GTWeed_AS568_StandardOringSizing.pdf S. 2 (Dash -019 0.801 in). Werkstoff EPDM statt Silikon (R K-l2, Mechanik 2026-11-09): Parker ORD 5700 PDF-S. 206 Silicone Greases EPDM 1 / VMQ 3 (doubtful), S. 68 Silikonfette mit allen Werkstoffen ausser Silikon; EPDM -57...+121 C allgemein (S. 206 Tabelle), bis 150 C (S. 16), Wasser, nicht Mineraloel (S. 16); Duenger-Salze EPDM 1: Ammoniumnitrat/-phosphat/-sulfat S. 165, Kaliumnitrat/-chlorid S. 203, Wasser S. 215. Kein CH-Angebot fuer 20.35 x 1.78 gefunden (Suche 2026-11-09). Nur schwarzes (russgefuelltes) EPDM lieferbar -> RSSI-Vergleich mit Elektronik (Russ = ANNAHME HF-Verlust) vor Verwendung
- **S3** (1 je Sensor x 20 + 5 Reserve): D-032: TX6 handelsueblich (REQ-MECH-15), CAD Kopfhoehe 1.6 nachgefuehrt, Werkzeug TX6 in BATTERIEWECHSEL/MONTAGE. S K-5: Furchlippe haelt die Schraube beim Loesen, sie kann aber herausfallen -> nicht unverlierbar; lose Schrauben wie Zellen kindersicher aufbewahren (BATTERIEWECHSEL)
- **S4** (1 je Sensor x 20 + Reserve): Masse laut Shop = Nennmasse ISO 4032 (SW4 x 1.6)
- **S5** (1 Platte fuer 20 + Reserve): Betaetigungskraft PROTOTYP-PRUEFUNG
- **S6** (1 Tube): Kandidat bei galaxus.ch (Red Team W-3a, Haendler buendeln). Entscheid Mechanik 2026-11-09 (R K-l2): O-Ringe EPDM (S2); Silikonfett mit EPDM vertraeglich (Parker ORD 5700 PDF-S. 206: EPDM 1), mit Silikon-O-Ringen zweifelhaft (VMQ 3) -> keine Silikon-O-Ringe. Nur duenner Film (Parker S. 50, Tab. 3-1 Hinweis). Kein Mineralfett/Vaseline an EPDM (S. 16). Datenblatt beim Kauf ablegen
- **S7** (1 Packung (Tuben, je Fenster < 0.05 g)): Entscheid Mechanik 2026-11-09 (Freigabe Orchestrator offen): UHU plus endfest 300. Opak (TDS S. 1) zulaessig, Klebstoff nur an Tropfenrand/Schaftmantel; hochviskos, minimales Laufbestreben (TDS S. 1-2). ER2223 fuer Fenster abgelehnt (schwarz, 800 mPa s, kriecht auf Stirnflaechen). HAERTER AETZEND H314/H318 (SDB-PDF S. 14), Binder H315/H317/H319/H411 -> Schutz MONTAGE_SENSOR Kap. 3 Schritt 1. Haftung ASA im TDS nicht belegt, Klebefuge dicht nach 7 d 65 C = PROTOTYP-PRUEFUNG. Typgleichheit 300 beim Wareneingang pruefen
- **S9** (20 x 13 g + Gateway 14 g + Passproben, < 1 kg): Vorgabe Bambu ASA: Werkstattbestand pruefen (ANNAHME vorhanden), Bambu Lab EU Store ASA Gray (45102) 14.99 EUR nicht an Lager (2026-11-09), Gratisversand CH ab 119 EUR. Bedingte Alternative eSun ASA+ (TDS docs/references/eSUN_ASAplus_TDS_V1.0-2024-06.pdf, HDT 95.5 C bei 0.45 MPa, erst nach PROTOTYP-PRUEFUNG 7 d 65 C, mechanical/PRINT_SETTINGS.md Kap. 1): Grau 424233 ausverkauft, Kaltweiss 424234 lagernd = Abweichung D-010 -> Auftraggeber
- **S10** (20 x ca. 5 g + Gateway 10 g, < 1 kg): Nur falls kein Bambu ASA blau vorhanden (Bambu EU Store Blue 45600 nicht an Lager 2026-11-09). eSun ASA+ erst nach PROTOTYP-PRUEFUNG 7 d 65 C (PRINT_SETTINGS Kap. 1), Farbton/Pigment pruefen
- **S11** (wenige g (Sensor 0.1 g, Gateway 0.1 g je Fenster + Proben)): Entscheid Mechanik 2026-11-09 (Freigabe Orchestrator offen): statt eSun ASA+ Kaltweiss (deckend, Lichtweg Fenster 4.0 mm massiv) und PETG natur (HDT 64 C). TDS V6.0 lokal: HDT 100 C (1.8 MPa). Transluzenz im TDS nicht angegeben (N/A) -> LED-Sichtbarkeit PROTOTYP-PRUEFUNG. Nur 1 Stk an Lager; Ausweichquelle digitec.ch (Polymaker PolyLite ASA Natural, nicht abrufbar, ANNAHME)
- **S12** (1 Etikett je Sensor (20), ca. 26 mm Band je Etikett, < 1 m): R K-l5: Etikett mit Kennung fluidi-XXXX auf der Kappenrueckseite (MONTAGE Kap. 7a). ENTFAELLT, FALLS VORHANDEN (ANNAHME vorhanden, nicht gerechnet), sonst Beschaffung klaeren (Etikettendrucker + Band oder wetterfeste Laser-Folienetiketten)
- **G2** (1 Gateway): Konformitaet beim Wareneingang (Sicherheits-Agent), Datenblatt fehlt (F-8)
- **G3** (1 Gateway): Datenblatt docs/datasheets/Kingston_SDCIT2_Datasheet_MKD-02122026.pdf. Grosshandel alltron.ch: 100 Stk auf 23.11.2026 bestellt. Sofort-Alternative gleicher Serie: mediamarkt.ch Marktplatz Ultimus.ch SDCIT2/8GB CHF 56.95 (Lieferung 27.11.-01.12.) bzw. 16 GB CHF 63.95, versandkostenfrei
- **G6** (1 Gateway): Masszeichnung/Schaltplan lokal (docs/datasheets/DFRobot_SEN0428_*). Halter im Gehaeuse: Bodenschiene Nut 1.90 + Deckelrippe (mechanical/gateway_pi/check_gateway_pi.txt Pkt. 14). Platinendicke 1.6 ANNAHME -> am Muster messen
- **G8a** (4 je Gateway): D-032: Rohr Ø7.0 mit Fuss Ø5.6, Bohrung 3.9, Tiefe 5.2 (check_gateway_pi.txt Pkt. 33). Kleinere Packung nicht gefunden
- **G8b** (4 je Gateway): bastelgarage M2.5-Sortiment DIN 912 ausverkauft (2026-11-09) und Zylinderkopf statt Linsenkopf
- **G9** (1 Gateway): Red Team W-3c: LED = gleicher Typ wie D-027 (Datenblatt Kingbright V10B lokal), ueber LCSC mit den Adapterteilen P1-P7 (kein Digi-Key-Versand). YAGEO MFR-25FBF52-470R bei LCSC C1369905 Lager 0 -> Ersatz CCO MF1/4W 470R 1 % C119317, Datenblatt bei LCSC nicht ladbar (Bot-Sperre) -> beim Wareneingang ablegen. bastelgarage/pi-shop fuehren keine einzelne 3-mm-LED mit Datenblatt (nur Sortiment)
- **G10** (Werkstatt): bastelgarage Schrumpfschlauch-Set 140 Stk ausverkauft (2026-11-09)
- **W1** (1 Programmierplatz): Elektronik 2026-11-09: freigegeben mit Bedingungen B1-B6 (hardware/programmer/README.md Kap. 9, EINKAUFSLISTE.md Kap. 3). Original CH343 (TOOL-UART1): waveshare.com USD 3.49 + Versand (nicht ablesbar) bzw. eckstein-shop.de EUR 4.15 (ca. 3 Wochen) -> eigener Auslandsversand
- **W3** (1 je Standort (BATTERIEWECHSEL, INBETRIEBNAHME)): Red Team K-l4: ENTFAELLT, FALLS VORHANDEN. Alternative Wera 2067 TX 6 x 40 CHF 7.25 (Mindestmenge 5 laut Auszug)
- **V-M1** (1 Beutel je Bauserie (Prototyp, Serie), Haltbarkeit 3 Monate nach Abfuellen (MA-3)): LIEFERZEIT 8 WOCHEN -> sofort nach Freigabe bestellen. Vor dem ersten Beutel SDB Teil B in DE/EN/FR/IT anfordern (D-030 Bed. 1). Versand Simpex nicht angegeben (ANNAHME 15 CHF). simpex.ch fuer automatischen Abruf gesperrt (403, 2026-11-09). Red Team W-3b: Alternativen distrelec.ch Art. 30116965 und RS 1526879 - Lager/Lieferzeit nicht abrufbar (Radware-Captcha bzw. HTTP 403, 2026-11-09) -> beim Bestellen von Hand pruefen, kuerzere Lieferzeit bevorzugen
- **V-Z1** (1 Arbeitsplatz): ENTFAELLT, FALLS VORHANDEN. Kein Justiergewicht im Lieferumfang -> Kontrolle mit Pruefgewichten V-Z2 vor jeder Sitzung (MA-4), Genauigkeit nicht angegeben
- **V-Z2** (1 Satz): Keine CH-Quelle mit abrufbarem Preis (bastelgarage: Kalibriergewicht nur im Set der ausverkauften CX-Waage)
- **V-Z3** (1 Satz): -
- **V-Z4** (1 Satz): -
- **V-Z5a** (ca. 10 Ansaetze + Abfuellen + Reserve): Shop: nicht loesungsmittelbestaendig
- **V-Z5b** (1 Packung): -
- **V-Z5d** (1 Satz): Sicherheit W-4: Silikontrichter mit Feinfilter (bastelgarage 424244) gestrichen. PE-Trichter bei galaxus/bastelgarage nicht gefunden (Suche 2026-11-09) -> Quelle offen
- **V-Z6a** (1 Stk): -
- **V-Z6b** (1 Satz): -
- **V-Z7** (1 Box): Sicherheit W-5 / D-030 Bed. 1: Hersteller MAPA, Staerke 0.13 mm (TDS S. 1), EN ISO 374-1 Typ B, CE 0075/014/162/08/18/1659; Bestaendigkeitstabelle lokal (MAPA_Solo977_Bestaendigkeitstabelle_2024-04-11.pdf): Ammoniak 25 % 16 min, keine Werte fuer CAS 1761-71-3/25068-38-6 -> Sicherheit bewertet, doppelt tragen (K-3), bei Kontakt wechseln. Bezug auch bul.ch (CH, Datenblaetter). bastelgarage 421782 nur fuer Arbeiten ohne Vergussmasse. Freigabe Sicherheit (phase6_sicherheit_schluss.md, Handschuhe V-Z7) als Spritzschutz unter HS-1...HS-5: 2 Paar uebereinander, aeusseres sofort bei Kontakt bzw. nach 15 min wechseln; kein Vollkontakt; nur Isopropanol, kein Aceton/Keton; Butyl-/Laminat-Ueberhandschuh beim Abfuellen M-A empfohlen; Anfrage MAPA Permeation CAS 1761-71-3 (bei < 10 min wird Ueberhandschuh Pflicht). MONTAGE Kap. 3a
- **V-Z8** (1 Satz): Sicherheit K-7 / D-030 Bed. 1: Pflicht vor dem Oeffnen des ersten Beutels. Eine vorhandene Brille gilt nur als Korbbrille nach EN 166 mit Kennzeichnung 3 (Fluessigkeiten), dazu Visier. Kennzeichnung 3 am gelieferten Artikel pruefen (Listing nennt sie nicht)
- **V-Z9** (1 Satz): Sicherheit K-7: Pflicht vor dem ersten Beutel (SDB B Abschn. 4/8). Alternative Plum pH-neutral DUO 500 ml CHF 24.50 (Suchtreffer)
- **V-Z10** (1 Stk): Sicherheit K-7: Pflicht vor dem ersten Beutel, ersatzweise Absaugung (SDB B Abschn. 7.1/8.2). EN 14387 am Filter pruefen
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
- **WB-1** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Speisung 2.0 V/10 mA (PROGRAMMIEREN Regel 2). ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-2** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: VIO/VDD, Isolation Scheibe > 10 MOhm, R9-Kontrolle. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-3** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Scheibendicke 3.0-3.2 mm (PS-W3). ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-4** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Draht an R9 (0402), Litzen Scheibe. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-5** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: 0402-Pad. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-6** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Zinnbruecken entfernen. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-7** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Draht R9 -> RXD (entfaellt mit B2). ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-8** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Zugentlastung, Dickenausgleich Scheibe. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-9** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Sichtpruefung R9/R6/TP2, VIP-Pads. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-10** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Foto je Muster. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8). Bezug Werkstattbestand
- **WB-11** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Draht fuehren, B2-Teile. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-12** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Zelle und Scheibe entnehmen. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-13** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Flussmittel entfernen. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-14** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: TP2 (PS-W2), bei B2 auch TP1. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-15** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Sensor/Pruefspitze halten. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-16** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: PROGRAMMIEREN Kap. 2. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8). Bezug = W1 (pi-shop 11757)
- **WB-17** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: USB-UART <-> Scheibe/Netzteil. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-18** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: PROGRAMMIEREN Kap. 3. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8). Bezug Werkstattbestand
- **WB-19** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Speisung Weg B (Veto PS-K1). ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8). Bezug = JLC-Bestellung (Dummy-Platinen)
- **WB-20** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Scheibe -> Netzteil. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-21** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Scheibe kleben/fasen (Kleber ggf. S7 UHU, isolierend laut TDS nicht belegt). ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)
- **WB-22** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Funktionspruefung = S1 (Testzellen). ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8). Bezug = S1
- **WB-23** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Zellen < 2.6 V abkleben, entsorgen. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8). Bezug Werkstattbestand
- **WB-24** (1 je Weg-B-Platz (hardware/dummy_cell/README.md Kap. 7)): Wofuer: Kurzschlussgefahr am offenen Board. ENTFAELLT, FALLS VORHANDEN; nicht in der Bestellsumme, Neukauf-Richtwert separat (EINKAUFSLISTE Kap. 8)

## 7 Händlergruppierung und Versand

| Händler | Positionen | Ware CHF | Versand CHF | Total CHF | davon jetzt lieferbar | Versandregel |
|---|---|---|---|---|---|---|
| galaxus.ch | S1, S6, W3, V-Z7, V-Z8, V-Z9, V-Z10 | 184.14 | 9.90 | 194.04 | 174.24 (+9.90 Versand) | ANNAHME (Versandseite nicht abrufbar, Bot-Sperre) |
| bastelgarage.ch | S3, S4, S7, S9, S10, G6, G8a, V-Z1, V-Z5a, V-Z5b, V-Z6a | 138.60 | 0.00 | 138.60 | 118.70 (+0.00 Versand) | bastelgarage.ch/lieferung-versandkosten (2026-11-09): PostPac Economy 6.90, Priority 8.90, ab CHF 80 Warenwert gratis (docs/references/Haendler_Einkauf_Auszug_2026-11-09.txt) |
| offen (Labor-/Arbeitsschutz-Fachhandel) | V-Z2, V-Z3, V-Z4, V-Z5d, V-Z6b, V-Z11 | 84.00 | 10.00 | 94.00 | 0.00 (+0.00 Versand) | ANNAHME (Haendler offen, eine Sammelbestellung V-Z2/V-Z3/V-Z4/V-Z5d/V-Z6b/V-Z11) |
| Simpex Electronic AG | V-M1 | 82.58 | 15.00 | 97.58 | 82.58 (+15.00 Versand) | ANNAHME (Versandbetrag laut Konzept Kap. 7 nicht angegeben) |
| pi-shop.ch | G2, G3, W1 | 48.70 | 7.90 | 56.60 | 20.80 (+7.90 Versand) | pi-shop.ch/versandkosten (2026-11-08): B-Post 7.90, A-Post 9.90 (docs/references/pi-shop_Gateway-Teile_Auszug_2026-11-08.txt) |
| offen (Normteile-/Dichtungs-Fachhandel) | S2, S5, G8b, P8 | 24.50 | 10.00 | 34.50 | 0.00 (+0.00 Versand) | ANNAHME (Haendler offen, eine Sammelbestellung S2/S5/G8b/P8) |
| 3djake.ch | S11 | 23.75 | 8.90 | 32.65 | 23.75 (+8.90 Versand) | 3djake.ch/de-CH/hilfe/versandkosten (2026-11-09): Standardversand Schweiz 8.90, ab CHF 69.90 gratis (docs/references/3DJake_PolymakerASA-Natural_Auszug_2026-11-09.txt) |
| LCSC (mit JLC-Bestellung buendeln, ANNAHME) | G9, P1, P2, P3, P4, P5, P6, P7 | 1.54 | 20.00 | 21.54 | 1.54 (+20.00 Versand) | ANNAHME (README Kap. 6: 10-25 CHF), Kombination mit der JLC-Sendung im Warenkorb pruefen |
| **Summe** | | **587.81** | **81.70** | **669.51** | | |

- bastelgarage.ch: geplant 138.60 CHF → versandkostenfrei; jetzt lieferbar 118.70 CHF (ohne ausverkauftes Grau) → frei.
- pi-shop.ch: G2 + W1 + G3 in **einer** Sendung, sobald G3 an Lager ist; getrennt bestellt kostet die zweite Sendung nochmals 7.90 CHF.
- Normteile/Dichtungen (S2, S5, G8b, P8): **ein** Fachhändler für alles; noch keiner mit abrufbarem Angebot (Versand ANNAHME 10 CHF).
- G9 (Gateway-LED, D-027): WP710A10GD C6001420 + 470 Ω C119317 bei LCSC zusammen mit den Adapterteilen (kein Digi-Key-Versand).
- JLC (PCBA Sensor) und Verguss (S8) sind separat (ORDER_JLC_REV_C.md bzw. Material-Agent).

## 8 Summen je Bereich (Ware, ohne Versand)

| Bereich | Positionen | Ware CHF | davon ANNAHME CHF |
|---|---|---|---|
| Sensor | 6 | 60.70 | 27.40 |
| Sensor+Werkstatt | 1 | 39.84 | 39.84 |
| Sensor+Gateway | 3 | 63.55 | 0.00 |
| Gateway | 6 | 68.68 | 1.00 |
| Werkstatt | 2 | 15.40 | 6.50 |
| Verguss | 15 | 332.18 | 211.90 |
| Programmieradapter | 8 | 7.46 | 6.00 |

Verguss-Zubehör (V-Z…) ohne Beutel: **249.60 CHF** (geht als Einmalkosten in `scripts/cost_final_phase5.py`); Programmieradapter (P…, W1, LCSC-Versand ANNAHME) siehe Kap. 7.

## 8a Werkstatt-Voraussetzungen Weg B (entfällt, falls vorhanden)

Vorgabe `hardware/dummy_cell/README.md` Kap. 7 (WB-1…WB-24), je Weg-B-Platz. **Nicht in der Bestellsumme**: in der Regel Werkstattbestand. Fehlt etwas, gilt der Neukauf-Richtwert (**ANNAHME**, kein Angebot geprüft).

| ID | Werkzeug/Material | Mindestanforderung | Richtwert CHF |
|---|---|---|---|
| WB-1 | Labornetzteil | 0-3 V, Aufloesung <= 10 mV, Strombegrenzung einstellbar 10 mA, Ausgang schaltbar | 60.00 |
| WB-2 | Multimeter | DC 2 V mit 1 mV, Widerstand >= 20 MOhm, Durchgang | 40.00 |
| WB-3 | Messschieber | Aufloesung 0.01 mm | 20.00 |
| WB-4 | Loetstation | temperaturgeregelt, Spitze <= 0.4 mm | 60.00 |
| WB-5 | Loetzinn + Flussmittel | 0.3-0.5 mm mit Seele, No-clean-Flussmittelstift | 15.00 |
| WB-6 | Entloetlitze | 1-1.5 mm | 5.00 |
| WB-7 | Kupferlackdraht | 0.1-0.2 mm selbstverzinnend | 8.00 |
| WB-8 | Kaptonband | ca. 0.06 mm | 8.00 |
| WB-9 | Lupe oder Stereomikroskop | >= 10x | 25.00 |
| WB-10 | Kamera/Smartphone | Makro durch die Lupe | 0.00 |
| WB-11 | Feine Pinzette | antimagnetisch | 8.00 |
| WB-12 | Kunststoffpinzette/-spatel | kein Metall | 5.00 |
| WB-13 | Isopropanol >= 99 %, Pinsel/Wattestaebchen | - | 10.00 |
| WB-14 | Pruefspitze/Federstift flacher Kopf + Kabel | Kopf Ø <= 1.5 mm, keine Krone | 10.00 |
| WB-15 | Platinenhalter (dritte Hand) | nicht leitende Backen | 15.00 |
| WB-16 | USB-UART-Board | PL2303 type A V2 = W1 (oder CH343) | 0.00 |
| WB-17 | Steckbruecken | Dupont 10-20 cm | 5.00 |
| WB-18 | PC mit WSL2 oder Raspberry Pi | flash_sensor.py, pyserial, intelhex | 0.00 |
| WB-19 | Dummy-Scheibe PLUS 1.0 + MINUS 2.0 mm | hardware/dummy_cell (JLC, je 5 Stk, ORDER Kap. 4 Nr. 8b) | 0.00 |
| WB-20 | Litze rot/schwarz + Krokodilklemmen/4-mm-Stecker | 0.14-0.25 mm2, 20-30 cm | 5.00 |
| WB-21 | Isolierender 2K-Epoxidkleber, 2 Stifte Ø 1.0 mm, Schleifpapier 400 | duennfluessig | 5.00 |
| WB-22 | Neue Zellen CR2032 | Leerlauf >= 3.0 V | 0.00 |
| WB-23 | Behaelter fuer Altzellen, Klebeband | - | 0.00 |
| WB-24 | ESD-Unterlage (empfohlen) | sauberer trockener Arbeitsplatz | 20.00 |
| | **Summe, falls nichts vorhanden (ANNAHME)** | | **324.00** |

## 9 Prüfhinweise (`scripts/einkaufsliste.py --check`)

- S1: Preis ANNAHME/Quelle offen (39.84 CHF)
- S2: Preis ANNAHME/Quelle offen (7.50 CHF)
- S5: Preis ANNAHME/Quelle offen (10.00 CHF)
- S6: Preis ANNAHME/Quelle offen (9.90 CHF)
- S9: bastelgarage.ch Ausverkauft (Abruf 2026-11-09)
- G3: pi-shop.ch nicht an Lager (Abruf 2026-11-09)
- G8b: Preis ANNAHME/Quelle offen (1.00 CHF)
- W3: Preis ANNAHME/Quelle offen (6.50 CHF)
- V-Z2: Preis ANNAHME/Quelle offen (20.00 CHF)
- V-Z3: Preis ANNAHME/Quelle offen (15.00 CHF)
- V-Z4: Preis ANNAHME/Quelle offen (25.00 CHF)
- V-Z5d: Preis ANNAHME/Quelle offen (6.00 CHF)
- V-Z6b: Preis ANNAHME/Quelle offen (8.00 CHF)
- V-Z7: Preis ANNAHME/Quelle offen (25.00 CHF)
- V-Z8: Preis ANNAHME/Quelle offen (30.00 CHF)
- V-Z9: Preis ANNAHME/Quelle offen (32.90 CHF)
- V-Z10: Preis ANNAHME/Quelle offen (40.00 CHF)
- V-Z11: Preis ANNAHME/Quelle offen (10.00 CHF)
- P8: Preis ANNAHME/Quelle offen (6.00 CHF)
