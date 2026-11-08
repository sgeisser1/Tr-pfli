# Red Team – Gesamtprüfung fluidi am Ende von Phase 4 (vor der Musterbestellung)

| | |
|---|---|
| Prüfer | Red Team (frischer Kontext, ohne Begründungsketten der Ersteller) |
| Datum | 2026-11-08 |
| Stand | git HEAD `1b1d76c` (main); im Arbeitsbaum zusätzlich `simulation/spice/osc/osc_last.cir` geändert, `renders/final/` nicht versioniert |
| Leitfrage | „Würde ich das mit meinem eigenen Geld bestellen?“ |
| Urteil | **Ja, nach den Punkten B-1 bis B-4** (Kap. 1). Ich habe keinen Fehler gefunden, der die Bestellung wertlos macht. |

## 1 Urteil

Ich würde das **Prototyp-Los (5 PCB, 5 bestückt, ENIG, POFV, Economic PCBA)** mit eigenem Geld bestellen. Vorher
müssen diese Punkte erledigt sein:

- **B-1:** `ORDER_JLC_REV_B.md` auf Rev C nachführen (W-1).
- **B-2:** Im JLC-Formular bestätigen, dass Economic PCBA zusammen mit ENIG und POFV angeboten wird. Wenn nicht, die
  Kosten für Standard-PCBA neu rechnen und dem Auftraggeber vorlegen (W-2).
- **B-3:** In „Confirm Parts Placement“ Pin 1 bzw. die Lage von U1, U2, U3, U4–U6, Q1, Q2, D1, Y1 und BT1 einzeln
  abhaken. Die Liste steht in ORDER Kap. 3 und bleibt verbindlich (W-3).
- **B-4:** Den Weg zur Erstprogrammierung festlegen, bevor die Platinen ankommen. Entweder der Dummy-Zellen-Adapter
  mit TX-Puffer ist gebaut, oder es gibt einen dokumentierten Behelf mit Labornetzteil und gelöteten Drähten (W-4).

Wichtige, aber nicht bestellrelevante Lücken: FMEA-light, Testplan, Montage- und Versiegelungsanleitung (W-5),
RTC und Kosten des Gateways (W-8).

## 2 Was ich selbst geprüft habe (mit Ergebnis)

| Prüfung | Methode | Ergebnis |
|---|---|---|
| ERC | `kicad-cli 10.0.8 sch erc --severity-all` (Ausgabe im Scratchpad) | 0 Fehler, 2 Warnungen: `lib_symbol_mismatch` U3, `pin_to_pin` DIO12 ↔ PWR_FLAG (unkritisch, K-1) |
| DRC | `kicad-cli pcb drc --severity-all --schematic-parity` auf einer Kopie | **0 Verstösse, 0 offene Verbindungen, 0 Paritätsfehler** |
| Gerber-ZIP = Platine? | Gerber F/In1/In2/B Cu, F.Paste, F.Mask, Edge neu erzeugt, ohne Kopf-/Datumszeilen mit dem ZIP verglichen (md5) | **identisch** |
| Bohrdaten vs. Gerber-Ursprung | `PTH.drl` und `Edge_Cuts.gm1` gelesen | gleicher Ursprung (Hilfsursprung, x −13…13, y 0…−158.5), kein Versatz |
| Pinbelegung U1 CC2340R52 RGE | `TI_CC2340R5_Datasheet_SWRS272F.pdf` Abb. 6-2 / Tab. 6-1 gegen pcbnew-Pads | alle 24 Pins + EP korrekt (1 ANT, 2/20 VDDR, 11/18/24 VDDS, 16 VDDD, 17 DCDC, 21/22 X48, 14/15 X32, 13 RSTN, 23 GND) |
| UART-Bootloader-Pins | TRM `SWCU193A` S. 464–465 Tab. 8-38, bldrParam | Index 0 (QFN24): RX DIO20 = Pin 9, TX DIO6 = Pin 19, Trigger DIO21 = Pin 10 (Taster) → **korrekt**; SPI-CS DIO11 durch R13 high → kein SPI-Fehlstart |
| Q1/Q2 AO3401A | `AOS_AO3401A_Datasheet_Rev3.1.pdf` S. 1 (G 1, S 2, D 3) gegen KiCad SOT-23 | Q1: D = VBAT, S = VDD, G = GND (Verpolschutz richtig); Q2: S = VDD, D = OSC_PWR, G = OSC_EN_N |
| D1 RGB 1615 | `TUOZHAN_…_Datasheet_A0.pdf` S. 4 (1 = +, 2 = R, 3 = G, 4 = B; Draufsicht 1 unten links, 2 oben links, 3 oben rechts, 4 unten rechts) gegen Footprint (Pads nach 180°-Rückdrehung) | Lage und Masse (0.5 × 0.8, Abstand 0.7/0.2) korrekt |
| U3 TMP1075N DRL | `TI_TMP1075_Datasheet_SBOS854F.pdf` Tab. 5-1 | 1 SCL, 2 GND, 3 ALERT (offen), 4 A0 = GND, 5 V+, 6 SDA → korrekt |
| U2 LVC1G14 / U4–U6 LVC1G80 | SCES218AA Tab. 4-1, SCES221T Pin Functions | korrekt (Teiler: D an Q̄, CLK vom Vorgänger) |
| Y1 48 MHz | `HCI_XC32M4…pdf` S. 1 (1/3 Quarz, 2/4 GND) gegen KiCad 3225-4Pin; CL 8 pF, ESR < 40 Ω gegen DS S. 26 (CL 5–9 pF, ESR ≤ 60 Ω) | korrekt |
| BT1 Keystone 3034 | Katalog M65 S. 9, Fig. 1: Pads ≥ 1.27 × 5.08 (.050 × .200), W min 23.1, Minuspad ≥ 3.96² | Footprint 1.27 × 5.08, Aussenspanne 23.10, Minuspad 4.0 × 4.0 ohne Paste → **entspricht dem Minimum** (K-4) |
| Antennen-Sperrfläche | pcbnew: Regelfläche `Z1_ANTENNE` y 29.5…35.2 auf F/B/In1/In2 ohne Kupfer; AE1 x 147.1…162.7 | Kupfer auf allen 4 Lagen frei; GND-Bezug ab y 35.2 |
| Nassbereich | pcbnew: Vias bis y 79.57, Sonde ab y 80 (`Z5A_Z7_SONDE`); Innenlagen-Guard x 141.25…158.75 bei Sondenkante 140/160 | keine Vias im Nassbereich; Kupfer zur Kante 1.25 mm (≥ 1.0, REQ-MECH-06) |
| LCSC-Lager (live, 2026-11-08) | JLC-API über `scripts/jlc_price_cache.query` | alle vorhanden; knapp: **BT1 C5213768 629 Stk** (gestern 654), L1 4829, U4–U6 8064, Y1 8817, U1 9278 |
| Rotationstabelle | lokale Kopie gegen github.com/matthewlai/JLCKicadTools (`cpl_rotations_db.csv`) | identisch (SOT-23 −90, SOT-353 180, QFN 270); keine Regel für SOT-563 (Projektregel +180) |
| Kosten Serie | nachgerechnet: (5.53 USD × 0.8189 × 1.015 + 8.1 % MWST) × 16/15 + 3.09 CHF | **8.39 CHF** (Dok.: 8.38) ✓; lokale Teile 2.94 × 1.05 = 3.09 ✓ |
| Knicklast Sonde | Euler, FR4 E ≈ 20 GPa (ANNAHME), 22 × 1.6 mm, L 108 mm: frei π²EI/(4L²) ≈ 32 N; geführt 2.05 π²EI/L² ≈ 260 N | passt zu FEM 29 N / 236 N (D-016) ✓ |
| Oszillatorfrequenz D3 | Schmitt-RC 1 kΩ, VT+/VT− ≈ 1.7/1.0 V bei 3 V (ANNAHME), tpd ≈ 3.5 ns je Flanke | 23 pF → ≈ 34 MHz, 44 pF → ≈ 20 MHz; passt zu 17–36 MHz ✓ |
| Energie | pessA 6+2: 5.51 µA → 34.6 Mt.; Kontrolle 225 mAh × 0.75 × 0.9 / 5.51 µA ≈ 3.5 a vor Selbstentladung ✓ | REQ-ENE-02 mit pessA erfüllt, mit pessDS (Prototyp 4 × 100 µF) **nicht** (9.1 Mt., W-6) |
| Startkalibrierung ↔ Firmware | `fl_meas.c` (c = cref·t0/(t1−t0) − cpar), `fl_settings.c` (cpar 15.21 pF inkl. tpd), Gateway `config.py` 13.3/40 pF, PROBE_CAPACITANCE trocken 13.6 / nass 36.7 pF | konsistent (Rohwert ≈ Sondenkapazität) |
| Protokollversion | `fl_proto.h` FL_PROTO_VERSION 2, `protocol.py` PROTO_VERSION 2, PROTOCOL.md 0.2 | konsistent |
| LED-Farben | D-010 ↔ PROTOCOL 10.1 ↔ `app/js/pair.js` ↔ GATEWAY_SETUP/APP.md | konsistent (Gelb = Kopplung, Blau = Giessen, Rot = Batterie/Fehler) |
| Software-Tests | Gateway `unittest` (62 Tests), App `node --test` (11) + `unittest test_calc test_pwa` (24) | alle bestanden. Firmware `make check` **nicht** ausgeführt (schreibt in `build/`) |

## 3 Die drei tragenden Annahmen und meine Prüfung

1. **„JLC baut genau das, was in Gerber/BOM/CPL steht.“** Gerber, Footprints und Pins habe ich stichprobenweise gegen
   die Datenblätter geprüft: sie stimmen. Offen bleiben die Rotationen (Drittquelle, nicht von JLC belegt) und die
   Frage, ob Economic PCBA mit ENIG und POFV kombinierbar ist (W-2, W-3). Beides lässt sich nur im Bestellformular
   klären.
2. **„Die CR2032 hält ≥ 12 Monate.“** Mit Typwerten und pessA klar ja (10.8 bzw. 2.9 Jahre). Die wörtliche Lesart von
   REQ-ENE-08 („oder Maximalwert“, MLCC-Leckgrenze aus dem Datenblatt) ergibt 9.1 Monate (4 × 100 µF) bzw. 13.3
   Monate (2 × 100 µF). Mit 2 × 100 µF verfehlt der Puffer aber REQ-ENE-06 (246 mV > 200 mV, D-013). Die Serie hängt
   also an einer Messung am Muster (W-6).
3. **„Die erste Firmware kommt ohne teuren Adapter auf das Board, auch wenn es vergossen ist.“** Das Konzept ist
   schlüssig: TP1/TP2 liegen im Zellfach und bleiben nach dem Verguss erreichbar, ein leerer Chip startet den
   ROM-Bootloader, und DIO21 (Taster) ist als Trigger gesetzt (`mcuboot.syscfg` Z. 34–39). **Gebaut und gezeigt
   ist der Weg aber nicht.** Der Adapter ist „offen“, und der TX-Puffer gegen den CH343-Pull-up fehlt (W-4).

## 4 Befunde

### Kritisch

**Keine.** Ich habe keinen Befund gefunden, der die Musterbestellung wertlos macht. Geprüft habe ich Pins,
Footprints, Polung von Q1, D1, BT1 und Y1, Gerber-Konsistenz, Antennensperrfläche, Vias im Nassbereich und
Lagerbestand (Kap. 2).

### Wichtig

**W-1 – Bestellunterlage ist nicht auf Rev C nachgeführt.**
- **Begründung:** `hardware/sensor/out/ORDER_JLC_REV_B.md` trägt Stand 2026-11-07, Rev B. Mehrere Angaben sind veraltet:
  - „5 Via-in-Pad im Zellfach“: Rev C hat 4 (D-023 A-1, TP3 entfällt).
  - „Platinendatei steht noch auf HAL lead-free“: In `fluidi_sensor.kicad_pcb` Z. 104 und in der Job-Datei steht `ENIG`.
  - „Platine hat keinen Platzhalter JLCJLCJLCJLC“: Er existiert auf B.SilkS bei (156, 49.7) (pcb Z. 13668).
  - Die U3-Zeile in Kap. 3.3 sagt „keine Korrektur, verdächtig“. Die CPL enthält inzwischen die Projektregel +180 (U3 → 0°).
  - Kap. 3.1 fragt nach Preisen, die laut `CLIENT_INPUT.md` vom 2026-11-08 schon abgelesen sind.

  Wer am Bestelltag dieser Unterlage folgt, trifft falsche Annahmen. Für „Mark on PCB“ heisst das konkret: JLC
  setzt die Nummer an den Platzhalter, nicht frei.
- **Vorschlag:** Die Unterlage als `ORDER_JLC_REV_C.md` neu erzeugen: Datum, Commit, 4 VIP, Platzhalter-Lage,
  Option „Specify a location“, aktueller Lagerbestand. Den Remark-Text an Rev C anpassen.

**W-2 – Die Kombination Economic PCBA + ENIG + POFV ist nicht belegt; die Kosten hängen davon ab.**
- **Begründung:** ORDER Kap. 2 nennt sie selbst „nicht belegt → BESTELL-PRÜFUNG“, COSTS_REV_B.md Kap. 2 „ANNAHME“.
  Ohne Economic gelten die Setup-Kosten und Lagenregeln der Standard-PCBA, und das Kostenmodell stimmt nicht mehr.
  Ohne POFV darf laut D-023 A-2 nicht bestellt werden.
- **Vorschlag:** Vor der Freigabe im Formular prüfen, mit Screenshot unter `docs/references/`. Wenn die Kombination
  fehlt: Standard-PCBA rechnen (`cost_rev_b.py`) und dem Auftraggeber vorlegen. Die Stückkosten bleiben
  voraussichtlich unter 10 CHF, weil die Mehrkosten überwiegend einmalig sind (ANNAHME).

**W-3 – Rotationen stammen nur aus der Drittquelle; für D1, BT1 und Y1 gibt es keine Regel.**
- **Begründung:** `cpl_jlc.py` korrigiert U1 (+270), Q1/Q2 (−90), U2/U4–U6 (+180) nach JLCKicadTools; die Tabelle
  habe ich gegen GitHub geprüft, sie ist identisch. U3 (+180) folgt einer Projektregel.
  - Für **D1, BT1, Y1, L1, SW1** gibt es keine Regel; sie gehen unkorrigiert an JLC.
  - Bei D1 vertauscht ein 90°-/180°-Fehler Anode und Kathoden. Dann leuchtet nichts, Schaden entsteht aber keiner.
  - Bei Y1 legt ein 90°-Fehler X48P/X48N auf GND, der Chip startet nicht.
  - Bei U3 vertauscht ein 180°-Fehler V+ und GND.
  - Ein Fehler bei U1 macht alle 5 Platinen unbrauchbar.
- **Vorschlag:** Die Liste aus ORDER Kap. 3.3 als Abhakliste in die neue Bestellunterlage übernehmen. Je Teil die
  Pin-1-Markierung im JLC-Vorschaubild gegen `out/pdf/fluidi_sensor_bestueckung_F.pdf` vergleichen und das Ergebnis
  (Screenshot) ablegen.

**W-4 – Erstprogrammierung: Der Weg ist geplant, aber kein Teil davon ist gebaut.**
- **Begründung:**
  - `docs/manuals/INSTALL_FIRMWARE_TOOLS.md` Z. 131–157: Programmieren ist „erst mit … Dummy-Zellen-Adapter möglich“.
    Der Adapter ist „offen“, ebenso der TX-Puffer (FW-T2). Der CH343-Bezug in die Schweiz ist nicht bestätigt (FW-T3).
  - Über 2 × 100 kΩ (R9/R10) und den CH343-RXD-Pull-up (3–21 µA) liegt das Low bei ≥ 0.6 V > VIL 0.5 V. Ohne
    Puffer gibt es also keine Antwort vom Bootloader (dort selbst festgestellt).
  - Das Handbuch nennt noch `scripts/cc23_bsl.py („folgt“)`; vorhanden ist `scripts/flash_sensor.py`. Als Gateway
    nennt es den „XIAO ESP32-S3 Plus“, obwohl D-014 den Pi Zero 2 W festlegt.
  - Bei 1.8 V Speisung liegt VDDS nach Q1 und den Federkontakten bei ≈ 1.75–1.78 V. VDDS min ist 1.71 V, die
    BOD-Schwelle fallend 1.67 V (`SWRS272F` S. 17–18, Kap. 7.3/7.6). Beim Flash-Löschen bleiben dann nur ≈ 40–70 mV
    Reserve.
- **Vorschlag:**
  - Adapter jetzt entwerfen: Federstifte auf TP1/TP2, Minuspad als GND, Puffer (z. B. 74LVC1G34-Klasse, Datenblatt
    ablegen) am TX-Stift, 2.0 V statt 1.8 V. Bei 2.0 V leiten die LEDs noch nicht (VF Rot ≥ 1.8 V bei 5 mA; bei
    µA-Strömen tiefer, **PROTOTYP-PRÜFUNG**).
  - **Behelf für das Muster:** Vor dem Verguss am offenen Board programmieren, Labornetzteil 2.0–2.2 V mit
    Strombegrenzung an Clip/Minuspad, CH343-RXD direkt an R9-Pad (Knoten LED_R_UART_TX, also vor den 100 kΩ). Den
    Behelf in einer Kurzanleitung „Erstprogrammierung Muster“ festhalten. Ohne Zelle, REQ-SAF-CC-03 bleibt gewahrt.
  - Das Handbuch auf D-014 und `flash_sensor.py` nachführen.

**W-5 – Für ein bestellfertiges Paket fehlen Muss-Dokumente (Projektauftrag, REQ-DOC-01…03, REQ-SAF-02, REQ-MECH-07).**
- **Begründung:**
  - Es gibt **kein `production/rev-X/`**.
  - Es gibt **keine FMEA-light**. Sie wird in CONCEPTS Z. 310/761 und in LAYOUT_REV_B Z. 228 (LS-K4) nur angekündigt;
    REQ-SAF-02 ist Muss, und laut REQ-SAF-04 blockiert ein offener Sicherheitsbefund.
  - Es gibt **keinen Testplan** (REQ-DOC-03). Die Prüfungen sind auf LAYOUT Kap. 10, ENERGIEMESSUNG und CONCEPTS
    verteilt.
  - Es gibt **keine Montage-, Versiegelungs-, Batteriewechsel- und Sicherheitsanleitung** für den Sensor
    (REQ-DOC-02, REQ-SAF-DOC-01). In `docs/manuals/` liegen nur APP, ENERGIEMESSUNG, GATEWAY_SETUP und
    INSTALL_FIRMWARE_TOOLS.
  - Das Verfahren für Sondenkanten und Coating ist nicht gewählt (REQ-MECH-07; `simulation/field/REPORT.md` nennt
    4200UV nur „zum Vergleich“).
  - Die Vergussmasse ist offen: `PRINT_SETTINGS.md` Z. 122 „ANNAHME Typ“, ohne Datenblatt, ohne Topfzeit und ohne
    Haftung auf ENIG/Lötstopp/ASA.
  - Das Gateway-Gehäuse ist dagegen druckfertig (`mechanical/gateway_pi/print/*.3mf`), das Sensorgehäuse ebenfalls.
- **Vorschlag:** Für die Musterbestellung blockiert das nicht, für den **Zusammenbau** schon. Bis zur Lieferung (≈ 2
  Wochen) erstellen:
  1. FMEA-light aus den vorhandenen Einzelfehleranalysen (`phase4_layout_revb_sicherheit.md`, CONCEPTS 2.10)
     zusammenführen.
  2. Testplan mit allen PROTOTYP-PRÜFUNGEN (Liste, Reihenfolge, zerstörende Tests auf welchem der 5 Muster).
  3. Montageanleitung mit Vergussreihenfolge (Distanzlehre 24.2 mm, Schottkeil), Vergussmasse mit Datenblatt,
     Kantenversiegelung.

**W-6 – Die Serienbestückung ist durch einen Zielkonflikt Laufzeit ↔ Spannungseinbruch blockiert.**
- **Begründung:**
  - Mit 4 × 100 µF: pessDS 9.1 Monate (`ENERGIE_REV_B.md` Kap. 3), dominiert durch das MLCC-Leck an der
    Datenblattgrenze (12 µA).
  - Mit 2 × 100 µF: 13.3 Monate, aber 246 mV Einbruch > 200 mV (REQ-ENE-06, D-013).
  - REQ-ENE-08 verlangt „Typwert × 1.5 **oder Maximalwert**“. Für MLCC gibt es nur den Grenzwert, die wörtliche
    Lesart trifft also pessDS. D-013 verschiebt den Entscheid auf die Messung. Das ist vernünftig, aber
    REQ-ENE-02 (Muss) ist damit für die Serie **noch nicht nachgewiesen**.
- **Vorschlag:**
  - Am Muster je Board das Leck von C1–C4 bei 3.0 V und 45 °C messen (ENERGIEMESSUNG E1, C3/C4 abgelötet und
    bestückt).
  - Falls das Leck hoch ist, Alternativen prüfen: 3 × 100 µF; den TX-Spitzenstrom senken (0 dBm → −4 dBm, wenn die
    Linkreserve es erlaubt); Advertising-Intervall bzw. Reaktionszeit 2 min (REQ-SYS-05 lässt 1–5 min zu).
  - Den Auftraggeber entscheiden lassen, ob pessA oder pessDS der Nachweisfall ist.

**W-7 – Reaktionszeit und Empfang hängen an der BLE/WLAN-Koexistenz des Pi Zero 2 W. Das ist ungeprüft und
überträgt sich auf das Energiebudget.**
- **Begründung:**
  - Der Sensor sendet Advertising alle 27.5 s (`fl_settings.c`, ENERGIE Kap. 5 `rb.adv_iv`). Für 95 % der Auslösungen
    innert 1 min (REQ-SYS-05 Soll) muss das Gateway fast jedes Advertising sehen.
  - Der CYW43436 im Pi Zero 2 W teilt Funkteil und Antenne zwischen WLAN und BT. Bei aktivem WLAN sinkt der
    effektive Scan-Tastgrad (ANNAHME, kein Datenblattwert lokal).
  - OP-GW-4/OP-GW-8 und OP-K12 sind offen. Der XIAO nRF52840 ist als Ausweg genannt (D-014), aber nicht eingeplant.
- **Vorschlag:** Den Koexistenztest **jetzt** mit dem vorhandenen Pi und einem beliebigen BLE-Sender machen, zum
  Beispiel dem XIAO nRF52840 mit 27.5 s Intervall in 18 m Abstand, bei laufendem WLAN-Verkehr, 24 h lang; dabei die
  Fangquote protokollieren. Das kostet nichts und entscheidet, ob der XIAO-Empfänger fest eingeplant wird. Ein
  schlechteres Ergebnis zwingt zu kürzerem Intervall und damit zu mehr Energie.

**W-8 – Gateway: RTC, Stückliste und Kosten sind nicht abgeschlossen (REQ-GW-09, REQ-FAB-06).**
- **Begründung:**
  - Der Pi Zero 2 W hat keine RTC. `ARCHITECTURE.md` Z. 331 OP-GW-3 „RTC-Baustein ohne Ladepfad“ ist offen.
    REQ-GW-09 verlangt, dass die Zeit nach einem Stromausfall ≥ 24 h erhalten bleibt; ohne RTC verteilt das Gateway
    nach einem Neustart ohne NTP keine Zeit.
  - Kosten nennt nur ARCHITECTURE Z. 316 („≈ CHF 75–80“), mit veraltetem Stand: OP-GW-0 „Plattformentscheid offen“,
    obwohl D-014 entschieden hat.
  - Eine Einkaufsliste mit geprüftem Netzteil (REQ-SAF-DOC-02), SD-Karte, RTC-Breakout und SHT4x-Breakout fehlt.
- **Vorschlag:**
  - RTC-Breakout wählen (Datenblatt, kein Ladepfad zur Pufferzelle) und Gehäuse-Platz prüfen.
  - Eine Gateway-Stückliste mit Preisen unter `hardware/gateway/` anlegen.
  - ARCHITECTURE.md auf D-014 bereinigen.

**W-9 – HTTPS hängt allein an mDNS (`fluidi.local`) im Firmen-WLAN.**
- **Begründung:**
  - Das Zertifikat hat nur den SAN `DNSName(fluidi.local)`, die CA ist per Name Constraint darauf beschränkt
    (`fluidi_gw/pki.py` Z. 45/52).
  - Firmen-WLANs filtern Multicast/mDNS häufig (ANNAHME). Der Test aus CLIENT_INPUT („Geräte sehen sich“) belegt
    nur Unicast.
  - Fällt mDNS aus, funktioniert die PWA über IP nicht mehr (Zertifikatsfehler, kein Service Worker). GATEWAY_SETUP
    Z. 42 verweist dann nur auf „IP im Router suchen“.
- **Vorschlag:**
  - Mit dem vorhandenen Pi heute auf dem Pixel 10 im Firmen-WLAN prüfen, ob `fluidi.local` aufgelöst wird.
  - Als Rückfall einen DNS-Eintrag beim Firmen-IT oder eine feste DHCP-Reservierung mit IP-SAN dokumentieren.
    Die IP-SAN müsste in die Name Constraints aufgenommen werden (iPAddress-Subtree), Sicherheitsagent einbeziehen.

**W-10 – Musterphase: Ein gedrückter Taster beim Einsetzen der Zelle startet den ROM-Bootloader, der die Zelle leert.**
- **Begründung:**
  - Die Muster-CCFG setzt `pinTriggerEnabled = true`, DIO21 LOW (`mcuboot/mcuboot.syscfg` Z. 37–39). Laut TRM
    S. 465 startet der Bootloader dann vor der Anwendung und wartet. Ein Timeout ist im Kapitel 8.5 nicht beschrieben.
  - Beim Zusammenbau (Hülse von unten hochschieben) drückt man leicht oben auf Kappe und Taster. Der Sensor wirkt
    dann tot und zieht Strom bei aktivem CPU-Takt (ANNAHME mA-Bereich) → die CR2032 ist in Tagen leer.
  - In der Serie sperrt `flash_sensor.py --lock` den Bootloader; für die 5 Muster über Monate (30-Tage-Wassertest)
    gilt das nicht.
- **Vorschlag:**
  - In die Musteranleitung schreiben: „Beim Einsetzen der Zelle Taste nicht drücken. Ohne L11-Startsignal Zelle
    neu einsetzen.“
  - Am Muster den Strom im ROM-Bootloader messen (ENERGIEMESSUNG ergänzen).

### Klein

**K-1 – ERC-Warnung `lib_symbol_mismatch` U3:** Das Schaltplansymbol weicht von `fluidi.kicad_sym` ab, Pins sind
richtig (geprüft). Vorschlag: `gen_schematic.py` neu laufen lassen und den ERC wieder auf 1 Warnung bringen.

**K-2 – Einmalkosten unterschätzt: Verzollung.**
- **Begründung:** `cost_model` rechnet mit 3.00 CHF Verzollungsgebühr. DHL Express Schweiz verlangt laut eigener
  Seite 19 CHF je Sendung ohne Kundenkonto (Stand 01.2026); eine ältere Privatkundenseite nennt 13 CHF + 3 % des
  Warenwerts. Die Stückkosten ändern sich dadurch nicht, die Einmalkosten steigen um ≈ 16–20 CHF je Bestellung.
- **Vorschlag:** Wert anpassen und Quelle ablegen.

**K-3 – Stückkosten vs. Vollkosten transparent halten.** 8.38 CHF erfüllen REQ-FAB-04 nach der Definition aus
D-005. Was ein Sensor real kostet, sind 16.46 CHF (Serie, Vollkosten). Vorschlag: In der Freigabevorlage an den
Auftraggeber beide Zahlen nebeneinander zeigen; D-005 ist nur „zur Kenntnis“ quittiert.

**K-4 – BT1-Pads genau auf dem Katalogminimum (W 23.10).**
- **Begründung:** Die Lötfahnen enden an der Padkante, eine Zehenkehle fehlt. Das ist bewusst gewählt (LS-W1,
  Vergusskanten), mechanisch ist es die schwächste Lötstelle (Zug beim Zellwechsel).
- **Vorschlag:** Nach der Lieferung die Lötstellen sichtprüfen und eine Abzugs-/Zellwechselprobe (z. B. 50 Wechsel)
  in den Testplan aufnehmen.

**K-5 – Der Lagerbestand des Halters C5213768 sinkt (654 → 629 an einem Tag).** Er ist das einzige mechanisch
festgelegte Extended-Teil. Vorschlag: Am Bestelltag prüfen. Für die Serie (16 Stk) den Halter evtl. mit dem
Prototyp-Los vorziehen („Parts pre-order“/privater Bestand bei JLC).

**K-6 – Verkehrt eingesetzte Zelle im Clip.**
- **Begründung:** Bei der CR2032 ist der gebördelte Rand auf der Minusseite Pluspotential. Liegt die Zelle verkehrt,
  kann der Clip die Minuskappe und den Rand gleichzeitig berühren. Das wäre ein Kurzschluss direkt am Clip, an Q1
  vorbei. Die PROTOTYP-PRÜFUNG R2-W01 Nr. 3 deckt den Fall ab.
- **Vorschlag:** Bei dieser Prüfung ausdrücklich den Zellstrom messen und die Clip-Kontaktstellen anschauen.

**K-7 – Firmware-Reserven knapp.**
- **Begründung:** Slot 0 ist zu 90 % belegt, das OTA-Image nutzt 89 % von Slot 1, im RAM bleiben 3.2 kB frei
  (`firmware/sensor/README.md` Kap. 3). Der Punkt ist offen (FW-O1). Ein späteres OTA mit mehr Funktionen passt
  sonst nicht mehr.
- **Vorschlag:** FW-O1 vor dem ersten Muster-Flash erledigen.

**K-8 – Arbeitsbaum nicht sauber.** `simulation/spice/osc/osc_last.cir` ist geändert, `renders/final/` nicht
versioniert. Vorschlag: Vor dem Freigabe-Commit klären (REQ-FAB-08, REQ-DES-04).

**K-9 – Antennenabgleich ohne Messmittel.**
- **Begründung:** Pi-Netz C19/C20 DNM, R2 0 Ω. Der Auftraggeber hat keinen VNA (RB-08). Das AN043-Layout stammt
  aus einem anderen Lagenaufbau; dazu kommt die ASA-Kappe (εr ≈ 3).
- **Vorschlag:** RSSI-Abgleich beschreiben. Am Gateway oder mit dem Handy (nRF Connect) in festem Abstand den RSSI
  mit 0 Ω und 2–3 Werten für C19/C20 vergleichen; die Basic-0402-Werte vorher im Register aufführen.

## 5 Fehlerszenarien aus dem Gebrauch (Kurzbewertung)

| Szenario | Bewertung |
|---|---|
| Nasse Erde über Monate | Keine Vias im Nassbereich, Innenlagen-Elektroden, Kupfer ≥ 1.25 mm zur Kante. Kantenversiegelung und Vergussmasse nicht festgelegt (W-5). FR4-Sättigung +0.7/+3.4 pF (PROBE_CAPACITANCE) → 30-Tage-Test nötig |
| Giessen über den Kopf | Drei getrennte Räume (Band/Schott, Fach, Kragen), O-Ringe, Membran. Nachweis nur am Muster (REQ-MECH-13) |
| Herunterfallen | FEM vorhanden. Schwächste Stelle vermutlich die BT1-Lötfahnen am Minimum (K-4) und die 1206-MLCC (Biegeriss = Kurzschluss an VDD, hinter Q1). Falltest im Testplan nötig |
| Fensterbank, Sonne 65 °C | CR2032 bis 85 °C (`Panasonic_CR2032_Datasheet_2026-02.pdf` S. 1), ASA ok, LED bis 85 °C, Taster bis 80 °C (XUNPU DS) → ok |
| Leere Batterie im Urlaub | Ringspeicher ≥ 105 Tage (README Kap. 3), Warnung bei < 30 Tagen. Die LED zeigt bei tiefer Zelle Rot; „Giessen“ wechselt von Blau auf Gelb (PROTOCOL 10.1) |
| Gateway-Neustart | Ohne RTC und ohne NTP keine Zeitverteilung (W-8); die Sensoren puffern |
| WLAN-Wechsel | Ohne Neukopplung möglich (REQ-GW-10), hängt aber an mDNS (W-9) |
| Zwei Gateways | Der Sensor nimmt nur Befehle vom gekoppelten Gateway an (PROTOCOL v2); ein zweites Gateway kann nicht übernehmen → ok |
| Kind/Haustier | Fach mit Schraube, Warnaufdruck „Verschluckgefahr / keep away from children“ auf der Platine. Die Sondenspitze ist ein spitzer Stab von 100 mm: Hinweis in die Anleitung |

## 6 Billigere oder einfachere Alternativen, die jetzt noch billig wären

| Alternative | Bewertung |
|---|---|
| Behelfs-Programmierung vor dem Verguss am offenen Board (W-4) | kostet nichts, entkoppelt das Muster vom Adapterbau → **empfohlen** |
| Koexistenztest Pi Zero 2 W jetzt mit vorhandener Hardware (W-7) | kostet nichts, verhindert ein spätes Gateway-Redesign → **empfohlen** |
| 32-kHz-Quarz weglassen (−0.20 USD, −3 USD Extended-Gebühr) | **nicht empfohlen**: REQ-SYS-07 (±2 min / 14 Tage ≈ 100 ppm) ist mit dem RC-Oszillator kaum erreichbar |
| Teiler U4–U6 weglassen (−0.63 USD, −3 USD Gebühr) | **nicht empfohlen**: D-018 (Salzfehler) bewusst entschieden |
| Prototyp nur 2 statt 5 bestücken (≈ −20 USD) | **nicht empfohlen**: zerstörende Tests (Flutung, Fall, 30 Tage nass) brauchen ≥ 4 Muster |
| SWD-Testpads (DIO16/17) im Fach ergänzen | mehr Rettungsweg, aber Programmer > 10 CHF (RB-08) und Layoutänderung → nur vormerken für Rev D |

## 7 Abgleich bisheriger Befunde (Stichprobe)

| Befund | umgesetzt? | Beleg |
|---|---|---|
| DFM W-3 (ENIG statt HASL) | ja | `fluidi_sensor.kicad_pcb` Z. 104, `job.gbrjob` |
| D-023 A-1 (TP3 entfällt, 4 VIP) | ja | keine TP3 in BOM/CPL/Extra; Regelflächen `VIP_FACH` × 4 |
| LS-W1 (Pad-Spanne 23.1, Abstand Vergusskanten) | ja | Footprint `…_W23p1`, Sperrstreifen-Regelflächen |
| DFM K-1 (Pad–Pad ≥ 0.15, U3 TI-Landmuster) | ja | U3-Pads 0.67 × 0.30, DRC 0 |
| DFM K-4 (Platzhalter JLC) | ja, aber ORDER sagt „nein“ | W-1 |
| EP-2 / FW-4 (LED-Pulse ≤ 5 ms) | ja | PROTOCOL 10.2 „Ausgabe nach FW-4“ |

## Quellen (Web)
- [DHL Express Schweiz – Customs Services (Gebühren ab 01.2026)](https://mydhl.express.dhl/ch/en/ship/customs-services.html)
- [DHL Express Schweiz – Zollinformationen für Privatkunden](https://mydhl.express.dhl/ch/de/help-and-support/customs-clearance-advice/duties-and-taxes/customs-information-for-private-customers.html)
- [JLCKicadTools cpl_rotations_db.csv (Abgleich der lokalen Kopie)](https://raw.githubusercontent.com/matthewlai/JLCKicadTools/master/jlc_kicad_tools/cpl_rotations_db.csv)
