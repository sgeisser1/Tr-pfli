# Prüfbericht Phase 1 – Anforderungen Tröpfli: Energie, Funk, Firmware

| | |
|---|---|
| Geprüft | `docs/requirements/REQUIREMENTS.md` v0.1 (Entwurf) |
| Grundlagen | `PROJEKTAUFTRAG.md`, `CLIENT_INPUT.md` |
| Prüfer | firmware-energie (frischer Kontext) |
| Datum | 2026-11-06 |
| Methode | Unabhängige Überschlagsrechnung (Skript im Anhang A, Ausgabe Anhang B), Datenblattwerte zitiert |

## 0 Kurzfazit

Die Anforderungen sind **gemeinsam erfüllbar**, wenn ein sparsamer BLE-SoC der Klasse CC2340/nRF52/EFR32BG22
mit **32-kHz-Quarz** und einem **Pufferkondensator** an einer **Marken-Knopfzelle** eingesetzt wird und der
Sensor per periodischem, verbindbarem Advertising erreichbar ist (Variante a/c). Auch die **CR2032** erreicht
rechnerisch-pessimistisch ≥ 12 Monate, und zwar mit dem Soll-Wert 1 min (ca. 47 Monate) und dem Muss-Wert 5 min
(ca. 64 Monate). Die Laufzeit bestimmt der **Ruhestrom**, nicht der Funk. Die CR2032 hält 12 Monate bis zu einem
mittleren Strom von **18.8 µA**. Bei Zellen mit nur 50 % nutzbarer Kapazität ([SW] S.4) sind es noch 12.8 µA.
Nicht erfüllbar sind: ESP32-C3 an der Knopfzelle, der Sensor-„Poll“ durch Scannen (Variante b) bei 1 min und die
Zeitstempel-Anforderung mit RC-Oszillator. Die Anforderung an die Gateway-Uhr (REQ-GW-09) ist knapp. Ausserdem
kollidiert der Programmierweg mit dem Ladeverbot für die Knopfzelle (FE-06).

Wichtigste Folgerungen für die Formulierung:
1. Die Pessimismus-Annahmen von REQ-ENE-02 als Zahlen festschreiben.
2. Den Ruhestrom als eigene Muss-Anforderung aufnehmen.
3. Den 32-kHz-Quarz (oder einen nachgewiesenen gleichwertigen Weg) verlangen.
4. Den Programmierweg mit REQ-SAF-CC-03 (keine Ladung) abstimmen.

## 1 Quellen (lokal im Prüfer-Scratchpad, nicht im Repo)

Die PDFs liegen in `/tmp/claude-1000/-home-sgeisser-git-Tr-pfli/8b053e22-18f3-446f-bac7-d1e0173ecf11/scratchpad/energy_review/dl/`.
Sie wurden nur für diese Prüfung geladen. Für die Konzeptphase sind sie nach `docs/datasheets/` zu übernehmen und
in `INDEX.csv` einzutragen. Seitenangaben = PDF-Seite.

| Kürzel | Datei | Dokument | Verwendete Stellen |
|---|---|---|---|
| [CC] | TI_CC2340R5_DS.pdf | TI CC2340R2/R5 Datasheet SWRS272F (Rev. F, Mai 2026) | S.1 Features (−96.5 dBm, ROM, RAM), S.18 Rec. Op. Cond. (VDDS 1.71–3.8 V, DCDC ab 2.2 V, Abfallrate ≤ 1 mV/µs), S.19–20 Tab. 7.9, S.20 Tab. 7.10, S.21 Tab. 7.11, S.27 Kap. 7.20.3.3/7.20.3.4, S.45 Kap. 8.4 (ROM-Bootloader UART/SPI) |
| [N52] | Nordic_nRF52832_PS_v1.0.pdf | nRF52832 Product Specification v1.0 (Mirror SparkFun; v1.9 bei Nordic hinter Cloudflare nicht ladbar) | S.75 Sleep-Ströme, S.106 Kap. 19.4.2–19.4.4 (HFXO, LFXO, LFRC), S.226–227 Radio |
| [FG22] | SiLabs_EFR32FG22_DS_farnell.pdf | EFR32FG22 Data Sheet, Preliminary Rev. 0.4 (Farnell). BG22-Datenblatt bei silabs.com „Access Denied“; FG22 = gleicher Die, nur Vergleichswert | S.1, S.22 (EM2 1.40 µA), S.28/32 Radio, S.43 Tab. 4.24 (LFRCO ±3 %) |
| [C3] | Espressif_ESP32C3_DS.pdf | ESP32-C3 Series Datasheet v2.4 | S.48 USB Serial/JTAG, S.56 Tab. 5-7, S.57 Tab. 5-8/5-9 |
| [PA32] | Panasonic_CR2032_DS.pdf | Panasonic CR2032 (Stand Feb. 2026) | S.1: 225 mAh, Dauerentladung 0.2 mA, Kapazität vs. Last/Temperatur |
| [PA45] | Panasonic_CR2450_DS.pdf | Panasonic CR2450 (Stand Feb. 2026) | S.1: 620 mAh, Dauerentladung 0.2 mA |
| [EN32] | Energizer_CR2032_kronium.pdf | Energizer CR2032 Ultimate Lithium, Form UltimateCR2032EU0920 | S.1: 254 mAh typ. (15 kΩ, 2.0 V), Selbstentladung ~1 %/a, Pulsdiagramm (6.8 mA, 2 s × 12/Tag), IR-Kurve |
| [RV32] | Rayovac_CR2032_DS.pdf | Rayovac CR2032 Marketing Data Sheet, Issue E | S.1: 220 mAh, IR frisch ≤ 20 Ω (1 kHz, 10 mA), Lagerverlust < 0.3 %/a |
| [JA32] | Jauch_CR2032J_DS.pdf | Jauch CR2032J | S.1: 245 mAh, max. Pulsstrom 15 mA |
| [AN45] | Ansmann_CR2450_DS.pdf | Ansmann CR2450 | S.1: 630 mAh rated, **550 mAh min** (0.4 mA, 2.0 V), max. Puls 20 mA, Dauer 5 mA |
| [VA45] | Varta_CR2450_6450_DS.pdf | Varta CR2450 Typ 6450 (Mirror Hornbach) | S.1: 570 mAh typ. (5.6 kΩ, 2.0 V) |
| [SW] | TI_SWRA349.pdf | TI White Paper SWRA349 „Coin cells and peak current draw“ | S.3 Tab. 1, S.4 Fig. 3, S.5 Fig. 6, S.6–8 Fig. 8–11 |
| [ABS] | Abracon_ABS07_DS.pdf | Abracon ABS07 32.768 kHz | S.1: ±20 ppm @25 °C, −0.036 (max −0.040) ppm/°C², Umkehrpunkt 25 ±5 °C, Alterung ±3 ppm/1. Jahr |

Nicht beschafft: das Nordic nRF52832 PS v1.9 und das nRF54L15-Datenblatt (Cloudflare-Sperre), das SiLabs
EFR32BG22-Datenblatt (Access Denied) und Energizer CR2450 sowie das Lithium-Coin-Handbuch (URL 404). Die
Pulsdaten für die CR2450 fehlen. Ein LiPo-Zellen-, Schutz-IC- oder LDO-Datenblatt wurde nicht geladen; die LiPo-Rechnung
ist deshalb nur grob und vollständig ANNAHME.

## 2 Rechenmodell (Kurzbeschreibung)

- **Basis-SoC CC2340R5** [CC]. Er hat die vollständigsten öffentlichen Werte und einen ROM-Seriell-Bootloader.
  nRF52832 und EFR32 liegen in derselben Grössenordnung ([N52] S.75: 1.9 µA System ON + RTC ohne RAM;
  [FG22] S.22: 1.40 µA EM2). Die Wahl des Chips ist Phase 2 und hier **keine** Empfehlung.
- **Ruhestrom**
  - realistisch: 0.74 µA (Standby, LFXT, DCDC, [CC] S.19 Tab. 7.9) + 0.2 µA andere Bauteile (ANNAHME)
  - pessimistisch: 1.15 µA (GLDO, [CC] S.20) × 1.5 für Temperatur und Streuung (ANNAHME; das Datenblatt nennt
    **keinen Max-Wert**) + 0.6 µA andere Bauteile (ANNAHME) = **2.3 µA**
- **Funkereignis**: TX 5.1 mA bzw. 9.0 mA (GLDO), RX 5.3 bzw. 9.0 mA ([CC] S.20 Tab. 7.10). Dazu:
  - die PDU-Zeit nach BLE 1 Mbit/s (47 B = 376 µs)
  - ein RX-Fenster von 250 µs, der Kanalwechsel und 1.5 ms CPU (ANNAHME)
  - der HFXO-Anlauf mit dem Nordic-Wert ([N52] S.106, ANNAHME als Näherung)
  - pessimistisch: GLDO-Ströme und ×1.5
- **Zelle pessimistisch**: CR2032 225 mAh [PA32], CR2450 **550 mAh (Minimum)** [AN45]. Davon sind 75 % nutzbar
  (ANNAHME). Herleitung: Die schlechteste Zelle mit Pufferkondensator erreicht 181.3/220 mAh = 82 % ([SW] S.7–8),
  abzüglich Temperatur und Abschaltschwelle. Selbstentladung 2 %/a: [EN32] nennt ~1 %/a, wegen der Fensterbank
  verdoppelt. Auf den Gesamtverbrauch kommt ein Zuschlag von +20 % (ANNAHME).
- **Profil REQ-ENE-04**: 6 + 2 Messungen/Tag, LED ereignisgesteuert, OTA separat.
- **Erreichbarkeit**: Die 99-%-Frist braucht 2 Chancen. Angenommen sind eine Fehlrate von 10 % je Fenster und
  5 s für Aufbau, Messung und Anzeige (ANNAHME). Daraus folgt ein Intervall von **≤ 27 s** für 1 min und
  **≤ 147 s** für 5 min.

### 2.1 Ergebnis Laufzeit (Monate, realistisch / pessimistisch)

| Variante | Intervall | Ladung/Ereignis pess. | CR2032 | CR2450 | Funkanteil pess. |
|---|---|---|---|---|---|
| (a) verbindbares Advertising, 3 Kanäle | 147 s (Muss 5 min) | 35.9 µC | > 10 a* / **63.6** | > 10 a* / **129** | 9 % |
| (a) | 27 s (Soll 1 min) | 35.9 µC | > 10 a* / **46.8** | > 10 a* / **99.5** | 36 % |
| (a) | 10 s | | > 8 a* / 30.2 | > 10 a* / 67.3 | 60 % |
| (a) | 1 s | | 17.9 / **5.0** | 42.6 / 12.0 | 94 % |
| (c) Advertising 1 Kanal + RX-Fenster | 27 s | 18.3 µC | > 10 a* / 55.7 | > 10 a* / 115 | 22 % |
| (b) Sensor scannt 30 ms nach Gateway | 147 s | 414 µC | > 8 a* / 34.4 | > 10 a* / 75.7 | 55 % |
| (b) | 27 s | | 38.2 / **10.6** | 88.8 / 25.1 | 87 % |
| (d) Dauerverbindung, Latenz (≤ 16 s) | 10 s | 14.7 µC | > 10 a* / 45.3 | > 10 a* / 96.6 | 38 % |

\* Die realistischen Werte über ca. 5–10 Jahre sind praktisch durch die Lagerfähigkeit der Zelle begrenzt und
haben keine Aussagekraft.

Pessimistisch bei 27 s (Var. a) beträgt der Mittelstrom **4.4 µA**. Der Ruhestrom macht davon 63 % aus, die
Erreichbarkeit 36 %, die Messungen 0.8 % und die LED 0.1 %.

## 3 Befunde

Stufen: **kritisch / wichtig / klein**. Bewertung je Anforderung: *erfüllbar / knapp / nicht erfüllbar*.

| ID | Stufe | REQ | Bewertung | Kernaussage (Zahl, Beleg) | Vorschlag |
|---|---|---|---|---|---|
| FE-01 | wichtig | REQ-ENE-02 | **erfüllbar** (CR2032 und CR2450) | Pessimistisch erreicht die CR2032 46.8 Monate bei 27 s und 63.6 Monate bei 147 s, die CR2450 99.5 bzw. 129 Monate (Anhang B). Für 12 Monate genügen 18.8 µA Mittelstrom (CR2032). „Pessimistisch“ ist im Text aber nicht quantifiziert, und die Zellqualität streut stark: einzelne Marken liefern ohne Puffer-C nur ~50 % ([SW] S.4 Fig. 3). | Die Annahmen festschreiben: Nennkapazität der Marken-Zelle nach Datenblatt, nutzbar ≤ 75 %, Selbstentladung 2 %/a, Ruhestrom-Max (bzw. typ × 1.5), +20 % Zuschlag, Abschaltschwelle 2.0 V unter Last. Ergänzen: „Marken-Zelle gemäss Stückliste; Betrieb mit No-Name-Zellen nicht garantiert.“ |
| FE-02 | kritisch | neu (zu REQ-FW-01/ENE-02) | Lücke | Die Laufzeit bestimmt der Ruhestrom (63–89 % des Budgets). Ein vergessener Pull-up, ein nicht abgeschaltetes Sensor-Frontend oder ein Elko-Leckstrom von wenigen µA halbiert die Reserve. Grenze für 12 Monate: 18.8 µA (CR2032). | Neue Muss-Anforderung: „Mittlerer Ruhestrom des Sensors ≤ **3 µA** bei 25 °C (gemessen nach REQ-ENE-07), Mittelstrom im Standardprofil ≤ **8 µA**.“ Pufferkondensator **keramisch** (kein Elko oder Tantal), Messfrontend vollständig abschaltbar. |
| FE-03 | wichtig | REQ-SYS-05, ENE-04 | Muss **erfüllbar**, Soll **erfüllbar** mit Var. a/c/d | Mit 5 min: Intervall ≤ 147 s, Funkanteil 9 %. Mit 1 min: ≤ 27 s, Funkanteil 36 %, CR2032 trotzdem 47 Monate pess. Variante (b) „Sensor scannt“ ist 11× teurer pro Ereignis (414 vs. 36 µC) und reicht bei 1 min nur knapp (10.6 Monate, CR2032). Das Risiko für die 1-min-Frist liegt beim **Gateway** (Scan-Duty-Cycle bei WLAN/BLE-Koexistenz, 15–30 Sensoren), nicht in der Sensorenergie. Mit 30 % Fehlrate je Fenster: 4 Chancen, 14 s Intervall, CR2032 noch ca. 35 Monate. | Soll ≤ 1 min **zum Muss machen** (energetisch tragbar), 5 min als Rückfallebene streichen oder als Degradationsfall bei tiefer Batterie zulassen. REQ-ENE-04 auf „Erreichbarkeit nach Soll-Wert“ umstellen. Variante (b) ausschliessen. Neue Gateway-Anforderung: Scan-Duty-Cycle ≥ X % bzw. Reaktionszeit am Prototyp messen (PROTOTYP-PRÜFUNG). |
| FE-04 | wichtig | REQ-SYS-07 | Mit RC **nicht erfüllbar**, mit Quarz **erfüllbar** | Zulässig sind 120 s / 7 d = **198 ppm**. Der Quarz ABS07 erreicht im ungünstigsten Fall 39 ppm (±20 ppm Toleranz, Temperaturgang bei 5/45 °C, Alterung) und damit 23.6 s in 7 d bzw. 47 s in 14 d ([ABS] S.1). Der nRF52-LFRC ist auch kalibriert ±250 ppm, also 151 s ([N52] S.106). Der EFR32-LFRCO hat ±3 %, also 5 h ([FG22] S.43). Für den CC2340-LFOSC fehlt die Genauigkeit im Datenblatt ([CC] S.27). Der Quarz kostet am CC2340 nur +0.03 µA (0.74 vs. 0.71 µA, [CC] S.19). | Ergänzen: „32.768-kHz-Quarz am Sensor (Muss), ausser ein RC-Verfahren erreicht ≤ ±2 min nachweislich (Messung über 5–45 °C).“ Den Zeitraum auf **14 Tage** angleichen (konsistent mit REQ-LOG-01); mit Quarz bleibt das < 1 min. |
| FE-05 | wichtig | REQ-GW-09 | **knapp** | ±1 min/Monat entspricht **23 ppm**. Ein Standard-32-kHz-Quarz (±20 ppm + Alterung, [ABS] S.1) liegt schon bei Raumtemperatur bei ~24 ppm. Werden Browser-Zeitstempel nur beim Öffnen der PWA übernommen, ist eine Monatsfrist ohne Öffnen realistisch. | Formulieren: „Gateway-Zeit ≤ ±1 min gegenüber der zuletzt erhaltenen Referenz (Browser, LAN-NTP) und Drift ≤ ±2 min/Monat ohne Referenz“, oder TCXO-RTC verlangen (Gateway-Kosten separat). |
| FE-06 | wichtig | REQ-FW-06 ↔ REQ-SAF-CC-03 | **erfüllbar**, Konflikt | Der CC2340 hat einen ROM-Bootloader für UART/SPI zur Erstprogrammierung ([CC] S.45), also genügt ein USB-UART-Adapter (Preis < 10 CHF: ANNAHME, nicht geprüft). nRF52 und EFR32 sind ab Werk nur über SWD programmierbar. Günstige CMSIS-DAP-Adapter oder ein RP2040 als Debugprobe sind wahrscheinlich < 10 CHF (ANNAHME). Der ESP32-C3 hat USB Serial/JTAG ([C3] S.48), scheidet aber energetisch aus (FE-08). Ob JLC programmieren kann, ist nicht geprüft (ANNAHME). **Konflikt**: Ein Adapter mit 3.3 V speist bei eingelegter Zelle in die Zelle zurück und verletzt damit REQ-SAF-CC-03. Eine Diode im Batteriepfad kostet 0.2–0.4 V Reserve (ANNAHME) und verschärft FE-07. | REQ-FW-06 belassen, ergänzen: „Programmieren nur ohne eingelegte Zelle, Adapter versorgt; konstruktiv sichergestellt (z. B. Programmierpads nur bei offenem Batteriefach zugänglich), **oder** Adapter speist nicht (nur Signale, Zielversorgung aus Zelle).“ Den Bootloader-Auslöser (Pin, leeres Flash) in Phase 2 aus dem Technical Reference Manual belegen. |
| FE-07 | wichtig | REQ-ENE-06 | **erfüllbar** mit Puffer-C | Spitzenstrom pess. 13.1 mA (TX 9.0 + CPU 4.1 mA GLDO, [CC] S.20). IR frisch ≤ 20 Ω ([RV32] S.1), gegen Ende > 30–100 Ω ([SW] S.5 Fig. 6; [EN32] IR-Kurve). Ohne Puffer bricht die Spannung um 0.4–1.3 V ein. Dazu verlangt der CC2340 eine Abfallrate ≤ **1 mV/µs** ([CC] S.18). Ohne Kondensator ist das bei 100 Ω nicht haltbar (sofortiger Sprung von 1.3 V). Mit 100 µF sind es 0.13 mV/µs. Obere Schranke Puffer: 120–240 µF für die ganze Ereignisladung (24 µC, ΔV 0.1–0.2 V). Unter 2.2 V wechselt der Chip automatisch auf GLDO (höhere Ströme, [CC] S.18). Pulsgrenzen der Zellen: CR2032 15 mA ([JA32]), CR2450 20 mA ([AN45]). | Ergänzen: „Spannungsabfall bei Funkspitze ≤ 0.2 V bei Zellen-IR 100 Ω (Simulation SPICE), Puffer-C keramisch; Firmware misst die Spannung unter Last und sperrt OTA/LED unterhalb einer Schwelle.“ „Ende der nutzbaren Kapazität“ = 2.0 V unter Last definieren. |
| FE-08 | wichtig | REQ-ENE-01, RF-01 | ESP32-C3 an Knopfzelle **nicht erfüllbar** | Deep-sleep 5 µA ergibt 44 mAh/a. Für BLE-Erreichbarkeit nötiger Light-sleep 130 µA ergibt **1139 mAh/a** ([C3] S.57 Tab. 5-9). Die Wi-Fi-TX-Spitze von 335 mA ([C3] S.56) ist mit einer Knopfzelle unvereinbar. | In REQ-ENE-01/RF-01 festhalten: WLAN- und ESP32-Klasse nur für die LiPo-Variante bewerten; für die Knopfzelle nur SoCs mit Standby ≤ 2 µA inkl. RTC und RAM-Erhalt. |
| FE-09 | klein | REQ-ENE-03 | **erfüllbar** (grob) | 100-mAh-LiPo (ANNAHME), 80 % nutzbar, 5 µA Schutz-IC + LDO (ANNAHME), 3 %/Monat Selbstentladung (ANNAHME): 8.1 Monate bei 27 s, 5.3 Monate bei 5 s, **2.0 Monate bei 1 s**. Die Schutzschaltung frisst mehr als der Sensor. | Belassen. Ergänzen: Ruhestrom der Schutz- und Ladeschaltung ≤ 5 µA (Datenblattnachweis in Phase 2), Erreichbarkeitsintervall ≥ 5 s. |
| FE-10 | klein | REQ-FW-05 | **erfüllbar**, gross Reserve | 200 kB Image (ANNAHME): ca. 0.07 mAh = 0.03 % CR2032. Im Grenzfall (10 min Dauer-RX 9 mA, [CC] S.20) 1.5 mAh = 0.67 %. Kritisch ist nicht die Energie, sondern der **Spannungseinbruch** bei langer Last an alter Zelle (2 mA × 100 Ω = 0.2 V) sowie der Flash-Platz: Dual-Bank braucht 2× Image. CC2340R5 512 kB passt, CC2340R2 256 kB ist knapp. | REQ-FW-05 umformulieren: „OTA ≤ 1 % Kapazität **und** nur bei Batteriezustand ≥ Schwelle (Spannung unter Last), sonst verschoben und in der PWA gemeldet.“ Flash ≥ 2 × Image + Logbereich als Muss. |
| FE-11 | klein | REQ-UI-03 | **erfüllbar**, wenn ereignisgesteuert | Das Standardmuster (≈ 6 Blinks à 20 ms/2 mA, ANNAHME) braucht 0.1 % des Budgets. Erlaubt wären ca. 280 Blinks/Tag. Ein periodischer „verbunden“-Herzschlag (5 ms alle 10 s) kostet dagegen **27–38 %** des Tagesbudgets. Ein Blinken „Giessen nötig“ (OP-02) muss deshalb selten sein (≤ 1×/min à 5 ms ≈ 4 %). | Ergänzen: „Im Normalbetrieb keine periodischen LED-Signale häufiger als 1×/min; LED-Strom ≤ 2 mA.“ Bei OP-02 diesen Zusammenhang dem Auftraggeber nennen. |
| FE-12 | klein | REQ-LOG-01 | **erfüllbar**, zu schwach | 14 d × 8/Tag × 12 B (ANNAHME Datensatz) = 1.3 kB, also 0.7 Flash-Sektoren à 2 kB ([CC] S.21). 90 d sind 8.4 kB und ebenfalls kostenlos. Hinweis Firmware: maximal 83 Schreibvorgänge pro Zeile vor dem Löschen ([CC] S.21 Fussnote) erfordern ein passendes Ringpuffer-Layout. | Auf **≥ 60 Tage** erhöhen (Urlaub, Gateway-Defekt); persistent im Flash (deckt REQ-LOG-03 als Muss ab). |
| FE-13 | klein | REQ-SYS-04 | **erfüllbar**, Bereich erweiterbar | Eine Messung inkl. Übertragung kostet ca. 0.33 mC pess. (ANNAHME). 6/Tag sind 1 % des Budgets, 96/Tag (alle 15 min) etwa +10 %. | Bereich auf 1–96/Tag erweitern, Laufzeit in der PWA je Einstellung anzeigen. |
| FE-14 | klein | REQ-RF-02/03 | **knapp** (Funkbudget, nicht Energie) | Freiraumdämpfung bei 18 m/2.44 GHz ca. 65 dB (Rechnung). Mit Dämpfung durch Topf, Erde und Personen (ANNAHME 15–20 dB) und einer Empfindlichkeit von −96.5 dBm ([CC] S.1) bleiben bei 0 dBm ca. 10–15 dB, also knapp für REQ-RF-03. +4 dBm kosten 7.9 statt 5.1 mA ([CC] S.20), d. h. den Funkanteil ×1.5 und die CR2032 bei 27 s weiterhin > 35 Monate. | Belassen; Sendeleistung adaptiv (+4–6 dBm zulässig) im Energiebudget berücksichtigen. Antennenmessung in Phase 4. |
| FE-15 | klein | REQ-ENE-05 | **knapp** | Die Li/MnO₂-Kurve ist bis ca. 85 % flach ([EN32] Diagramme), deshalb ist die Spannung allein für eine „Restlaufzeit < 30 Tage“-Warnung ungenau. | „Restlaufzeit aus Ladungszählung (Firmware, Ereigniszähler × kalibrierte Ladung) **und** Spannung unter Last; Warnung spätestens 30 Tage vor Ende (pessimistisch).“ |
| FE-16 | klein | REQ-ENE-04 | Profil unvollständig | Es fehlen: die Temperatur für den Pessimismus (Fensterbank 45 °C, RB-03), die Sendeleistung, die OTA-Dauer und die Zelle. | Ergänzen: „20 °C realistisch, pessimistisch mit Ruhestrom bei 45 °C; Sendeleistung 0 dBm (bzw. gewählt); Marken-Zelle laut Stückliste.“ |

## 4 Zusammenfassung je Anforderung

| REQ | Bewertung | Kurzbegründung |
|---|---|---|
| REQ-SYS-04 | erfüllbar | Messungen machen ca. 1 % des Budgets aus (FE-13) |
| REQ-SYS-05 Muss 5 min | erfüllbar | CR2032 63.6 Monate pess. (FE-03) |
| REQ-SYS-05 Soll 1 min | erfüllbar | CR2032 46.8 Monate pess.; Gateway-Scan ist das Risiko (FE-03) |
| REQ-SYS-07 | nur mit Quarz erfüllbar | 198 ppm zulässig; Quarz 39 ppm, LFRC 250 ppm (FE-04) |
| REQ-ENE-01 | erfüllbar | ESP32-Klasse für Knopfzelle ausschliessen (FE-08) |
| REQ-ENE-02 CR2032 | erfüllbar | Reserve ca. Faktor 4, Voraussetzung Ruhestrom ≤ 3 µA (FE-01/02) |
| REQ-ENE-02 CR2450 | erfüllbar | Reserve ca. Faktor 8 |
| REQ-ENE-03 | erfüllbar (grob) | Schutzschaltungs-Ruhestrom dominiert (FE-09) |
| REQ-ENE-04 | präzisieren | FE-16 |
| REQ-ENE-05 | knapp | flache Entladekurve (FE-15) |
| REQ-ENE-06 | erfüllbar mit Puffer-C | Abfallrate ≤ 1 mV/µs [CC] S.18 (FE-07) |
| REQ-ENE-07 | erfüllbar | Messbrücke ist Layoutfrage; bei 1 µA Ruhestrom ist ein Shunt ≥ 1 kΩ oder eine Mittelwertmessung über einen Kondensator nötig (Messplan Phase 4) |
| REQ-RF-01 | erfüllbar | FE-08 |
| REQ-RF-02/03 | knapp | Funkbudget, nicht Energie (FE-14) |
| REQ-RF-05/06 | erfüllbar | Energetisch vernachlässigbar (Verbindungsaufbau selten) |
| REQ-FW-01 | erfüllbar | Standby 0.74 µA [CC] S.19 |
| REQ-FW-02/03 | erfüllbar | Flash ≥ 2 × Image nötig (FE-10) |
| REQ-FW-05 | erfüllbar | 0.03–0.67 % (FE-10) |
| REQ-FW-06 | erfüllbar, Konflikt mit SAF-CC-03 | FE-06 |
| REQ-UI-03 | erfüllbar | ohne periodische Blinks (FE-11) |
| REQ-LOG-01 | erfüllbar | 1.3 kB; Erhöhung empfohlen (FE-12) |
| REQ-GW-09 | knapp | 23 ppm (FE-05) |

## 5 Offene Punkte für Phase 2 (PROTOTYP-PRÜFUNG)

- Ruhestrom des ganzen Sensors messen (Ziel ≤ 3 µA) und die Ladung pro Advertising-Ereignis messen (Modell 14–36 µC).
- Reaktionszeit Ende-zu-Ende mit 15 Sensoren und realem Gateway-Scan messen.
- Spannungseinbruch an der teilentladenen Zelle (Lastwiderstand oder vorentladene Zelle) messen.
- Die Datenblätter oben nach `docs/datasheets/` übernehmen und das Register nachführen. Nordic- und SiLabs-Originale beschaffen.

---

## Anhang A – Rechenskript `energy_review.py`

Ausgeführt mit `python3 -I energy_review.py` (nur Standardbibliothek).

```python
#!/usr/bin/env python3
"""Troepfli - unabhaengige Ueberschlagsrechnung Energie/Erreichbarkeit (Pruefung Phase 1).

Pruefer: firmware-energie. Nur Pruefrechnung, kein Projektskript (gehoert nicht ins Repo).
Quellen (lokal im Scratchpad .../energy_review/dl/, PDF-Seitenzahl = Seite im PDF-Viewer):
  [CC]   TI_CC2340R5_DS.pdf  (SWRS272F, Rev. F, Mai 2026)
         S.18 Rec. Operating Cond. (VDDS 1.71-3.8 V, DCDC erst ab 2.2 V, Abfallrate max 1 mV/us)
         S.19-20 Tab. 7.9 Power Modes, S.20 Tab. 7.10 Radio Modes, S.21 Tab. 7.11 Flash
  [N52]  Nordic_nRF52832_PS_v1.0.pdf (Product Spec v1.0, Mirror SparkFun; v1.9 nicht ladbar)
         S.75 Sleep-Stroeme, S.106 LFXO/LFRC/HFXO, S.226-227 Radio-Stroeme
  [FG22] SiLabs_EFR32FG22_DS_farnell.pdf (EFR32FG22 Preliminary Rev 0.4, gleicher Die wie BG22;
         BG22-Datenblatt bei silabs.com "Access Denied") S.22 EM2, S.43 Tab. 4.24 LFRCO, S.28/32 Radio
  [C3]   Espressif_ESP32C3_DS.pdf (v2.4) S.56 Tab. 5-7, S.57 Tab. 5-8/5-9
  [PA32] Panasonic_CR2032_DS.pdf (Stand Feb. 2026) S.1: 225 mAh, Dauerentladung 0.2 mA
  [PA45] Panasonic_CR2450_DS.pdf (Stand Feb. 2026) S.1: 620 mAh, Dauerentladung 0.2 mA
  [EN32] Energizer_CR2032_kronium.pdf (Form UltimateCR2032EU0920) S.1: 254 mAh typ. (15 kOhm, 2.0 V),
         Selbstentladung ~1 %/Jahr, Pulsdiagramm 6.8 mA, IR-Kurve
  [RV32] Rayovac_CR2032_DS.pdf S.1: 220 mAh, IR frisch max 20 Ohm (1 kHz), Lagerverlust < 0.3 %/Jahr
  [JA32] Jauch_CR2032J_DS.pdf S.1: 245 mAh, max. Pulsstrom 15 mA
  [AN45] Ansmann_CR2450_DS.pdf S.1: 630 mAh rated / 550 mAh min (0.4 mA, 2.0 V), max Puls 20 mA
  [VA45] Varta_CR2450_6450_DS.pdf S.1: 570 mAh typ. (5.6 kOhm, 2.0 V)
  [SW]   TI_SWRA349.pdf (Coin cells and peak current draw) S.4 Fig.3, S.5 Fig.6, S.6-8 Fig.8
  [ABS]  Abracon_ABS07_DS.pdf S.1: +-20 ppm @25 C, -0.036 ppm/C^2 typ (-0.040 max), Alterung +-3 ppm/1. Jahr

Alle mit ANNAHME markierten Werte sind NICHT aus Datenblaettern und am Prototyp zu messen.
"""

DAY = 86400.0
YEAR_D = 365.0
mAh = 3.6  # 1 mAh = 3.6 C

# ---------------------------------------------------------------- SoC-Werte (CC2340R5, [CC])
I_TX0_DCDC = 5.1e-3     # [CC] S.20 Tab 7.10, 0 dBm, DCDC
I_TX0_GLDO = 9.0e-3     # [CC] S.20 Tab 7.10, 0 dBm, DCDC OFF (unter 2.2 V automatisch GLDO, S.18)
I_RX_DCDC = 5.3e-3      # [CC] S.20 Tab 7.10
I_RX_GLDO = 9.0e-3      # [CC] S.20 Tab 7.10, DCDC OFF
I_ACT_DCDC = 2.6e-3     # [CC] S.19 Tab 7.9, CoreMark 48 MHz
I_ACT_GLDO = 4.1e-3     # [CC] S.20 Tab 7.9 (GLDO)
I_IDLE = 1.2e-3         # [CC] S.19 Tab 7.9, Idle flash enabled/DMA (DCDC); GLDO: 1.7 mA
I_IDLE_GLDO = 1.7e-3
I_SBY_LFXT_DCDC = 0.74e-6  # [CC] S.19 Tab 7.9 typ, 25 C
I_SBY_LFXT_GLDO = 1.15e-6  # [CC] S.20 Tab 7.9 typ, 25 C (kein Max-Wert im Datenblatt!)
I_FLASH_WR, T_FLASH_WR = 1.7e-3, 8.3e-3     # [CC] S.21 Tab 7.11, 2 kB Sektor
I_FLASH_ER, T_FLASH_ER = 1.2e-3, 2.2e-3     # [CC] S.21 Tab 7.11
# HF-Quarz-Anlauf: CC2340 nennt keinen Anlaufstrom -> Wert Nordic [N52] S.106 als Naeherung (ANNAHME)
I_HFXO_START, T_HFXO_START = 0.4e-3, 0.36e-3

# ---------------------------------------------------------------- BLE-Zeiten (Bitrate 1 Mbit/s)
US_PER_BYTE = 8e-6
ADV_PDU_BYTES = 1 + 4 + 2 + 6 + 31 + 3   # Praeambel+AA+Header+AdvA+31 B AdvData+CRC = 47 B (pessimistisch voll)
T_ADV_TX = ADV_PDU_BYTES * US_PER_BYTE   # 376 us
T_RX_AFTER_ADV = 250e-6   # ANNAHME: T_IFS 150 us + Lauschfenster fuer SCAN_REQ/CONNECT_IND
T_CH_SWITCH = 150e-6      # ANNAHME: Kanalwechsel/Synthesizer pro Kanal, bei Idle-Strom
T_CPU_EVENT = 1.5e-3      # ANNAHME: Stack-Vor-/Nachbearbeitung pro Funkereignis (CPU aktiv)
PESS_EVENT_FACTOR = 1.5   # ANNAHME: pessimistischer Zuschlag auf Ereignisladung (Stack-Overhead, Streuung)


def adv_event_charge(channels=3, connectable=True, gldo=False):
    itx = I_TX0_GLDO if gldo else I_TX0_DCDC
    irx = I_RX_GLDO if gldo else I_RX_DCDC
    iact = I_ACT_GLDO if gldo else I_ACT_DCDC
    iidle = I_IDLE_GLDO if gldo else I_IDLE
    q = channels * (T_ADV_TX * itx + T_CH_SWITCH * iidle)
    if connectable:
        q += channels * T_RX_AFTER_ADV * irx
    q += T_CPU_EVENT * iact + T_HFXO_START * I_HFXO_START
    return q


def scan_poll_charge(window=30e-3, gldo=False):
    """Variante b: Sensor scannt selbst nach Gateway-Advertising (Gateway-Intervall 20 ms, ANNAHME)."""
    irx = I_RX_GLDO if gldo else I_RX_DCDC
    iact = I_ACT_GLDO if gldo else I_ACT_DCDC
    return window * irx + T_CPU_EVENT * iact + T_HFXO_START * I_HFXO_START


def conn_event_charge(gldo=False, ww=200e-6):
    """Variante d: bestehende Verbindung, leeres Paket hin/zurueck (2 x 80 us) + Fensteraufweitung ww."""
    itx = I_TX0_GLDO if gldo else I_TX0_DCDC
    irx = I_RX_GLDO if gldo else I_RX_DCDC
    iact = I_ACT_GLDO if gldo else I_ACT_DCDC
    t_empty = 10 * US_PER_BYTE  # Praeambel+AA+Header+CRC
    return (t_empty + ww) * irx + (150e-6 + t_empty) * itx + 0.8e-3 * iact + T_HFXO_START * I_HFXO_START


# ---------------------------------------------------------------- Profil REQ-ENE-04
N_AUTO, N_MANUAL = 6, 2
Q_MEAS = 10e-3 * 3e-3            # ANNAHME: 10 ms Messung inkl. Mittelung bei ~3 mA = 30 uC
Q_XFER_CONN = 50 * 1e-3 * 6e-3   # ANNAHME pess.: Verbindungsaufbau+Daten+Abbau ~50 ms Funk-/CPU-Zeit bei 6 mA = 300 uC
Q_LOG = (T_FLASH_WR * I_FLASH_WR + T_FLASH_ER * I_FLASH_ER) / 100  # 1 Sektor-Zyklus pro ~100 Datensaetze
I_LED = 2e-3                     # ANNAHME: LED-Strom bei sparsamer Ansteuerung
T_LED_BLINK = 20e-3              # ANNAHME
LED_BLINKS_PER_DAY = 2 * 2 + 2   # ANNAHME Standard: 2 Tastendruecke x 2 Blinks + 2 Status-Blinks
Q_OTA = None                     # separat unten

# Ruhestrom-Zuschlaege anderer Bauteile (alles ANNAHME bis Schaltplan existiert)
I_OTHER_REAL = 0.2e-6            # Pufferkondensator-Leckstrom (Keramik), Verpolschutz-FET, Taster-Pull-up offen
I_OTHER_PESS = 0.6e-6
SLEEP_TEMP_STREU = 1.5           # ANNAHME: Faktor auf typ. Standby (bis 45 C, Exemplarstreuung; kein Max im DS)
CONS_MARGIN_PESS = 1.2           # ANNAHME: Zuschlag Bauteilstreuung/Firmware-Ineffizienz auf Gesamtverbrauch

# ---------------------------------------------------------------- Zellen
cells = {
    # name: (nominal mAh, Quelle, pessimistischer Ausnutzungsfaktor, Selbstentl./Jahr pess.)
    "CR2032": (225.0, "[PA32] S.1", 0.75, 0.02),
    "CR2450": (550.0, "[AN45] S.1 (min)", 0.75, 0.02),
}
# Ausnutzung 0.75: [SW] S.7-8: schlechteste Zelle mit Pufferkondensator 181.3/220 mAh = 82 %, ohne Kondensator
# einzelne Marken nur ~50 % (S.4 Fig.3). 0.75 = 82 % minus Temperatur/Abschaltschwelle (ANNAHME).
# Fuer CR2450 liegen keine Pulsmessungen vor -> gleicher Faktor = ANNAHME.
# Selbstentladung: [EN32] ~1 %/Jahr, [RV32] < 0.3 %/Jahr bei 20 C; pess. 2 %/Jahr (Fensterbank bis 45 C, ANNAHME).
CELL_REAL_UTIL = 0.90


def daily_charge(t_reach, variant, pess):
    gldo = pess  # pessimistisch: Zelle teils < 2.2 V unter Last -> GLDO-Werte
    if variant == "a":
        q_ev = adv_event_charge(3, True, gldo)
    elif variant == "b":
        q_ev = scan_poll_charge(30e-3, gldo)
    elif variant == "c":
        q_ev = adv_event_charge(1, True, gldo)
    elif variant == "d":
        q_ev = conn_event_charge(gldo, ww=(400e-6 if pess else 100e-6))
    else:
        raise ValueError(variant)
    if pess:
        q_ev *= PESS_EVENT_FACTOR
    n_ev = DAY / t_reach
    i_sleep = (I_SBY_LFXT_GLDO * SLEEP_TEMP_STREU + I_OTHER_PESS) if pess else (I_SBY_LFXT_DCDC + I_OTHER_REAL)
    parts = {
        "sleep": i_sleep * DAY,
        "reach": n_ev * q_ev,
        "meas": (N_AUTO + N_MANUAL) * (Q_MEAS + Q_XFER_CONN + Q_LOG),
        "led": LED_BLINKS_PER_DAY * I_LED * T_LED_BLINK,
        "ota": 0.0,
    }
    tot = sum(parts.values()) * (CONS_MARGIN_PESS if pess else 1.0)
    return tot, parts, q_ev


def lifetime_days(cap_mAh, util, sd_per_year, q_day_C):
    usable_C = cap_mAh * util * mAh
    # Selbstentladung als Verlust bezogen auf Nennkapazitaet pro Tag
    sd_C_day = cap_mAh * sd_per_year * mAh / YEAR_D
    return usable_C / (q_day_C + sd_C_day)


def reach_interval_for_deadline(deadline_s, t_setup=5.0, p_miss=0.1, target=0.99):
    """Wie oft muss der Sensor erreichbar sein, damit die Frist mit 99 % gehalten wird?
    t_setup: ANNAHME Verbindungsaufbau + Messung + Antwort + PWA-Aktualisierung.
    p_miss: ANNAHME Wahrscheinlichkeit, dass das Gateway ein Erreichbarkeitsfenster verpasst
            (Kollisionen mit 15 Sensoren, WLAN, Gateway scannt evtl. nicht 100 %)."""
    k = 1
    while p_miss ** k > 1 - target:
        k += 1
    return (deadline_s - t_setup) / k, k


def main():
    print("=== Ereignisladungen (uC) ===")
    for v, name in [("a", "connectable Adv 3 Kanaele"), ("c", "Adv 1 Kanal + RX"),
                    ("b", "Sensor scannt 30 ms"), ("d", "Verbindungsereignis")]:
        _, _, q_r = daily_charge(60, v, False)
        _, _, q_p = daily_charge(60, v, True)
        print(f"  {v}: {name:28s} real {q_r*1e6:6.1f} uC   pess {q_p*1e6:6.1f} uC")

    print("\n=== Erreichbarkeitsintervall fuer Frist (99 %) ===")
    for dl in (60, 300):
        t, k = reach_interval_for_deadline(dl)
        print(f"  Frist {dl:3d} s -> {k} Chancen noetig -> Intervall <= {t:.0f} s")

    intervals = [1, 5, 10, 20, 27, 60, 120, 147]
    print("\n=== Laufzeit [Monate] (real / pess) ===")
    hdr = "  Var  T[s] " + "".join(f"{c:>18s}" for c in cells) + "   Tagesladung real/pess [mC]  Anteil Erreichb. pess"
    print(hdr)
    for v in ("a", "c", "b", "d"):
        for T in intervals:
            if v == "d" and T > 16:
                continue  # Supervision-Timeout max 32 s (BLE-Spez., ANNAHME) -> Aufwachintervall <= ~16 s
            qr, pr, _ = daily_charge(T, v, False)
            qp, pp, _ = daily_charge(T, v, True)
            row = f"  {v:3s} {T:5d} "
            for c, (cap, src, util, sd) in cells.items():
                lr = lifetime_days(cap, CELL_REAL_UTIL, sd / 2, qr) / 30.4
                lp = lifetime_days(cap, util, sd, qp) / 30.4
                row += f"   {lr:6.1f} / {lp:5.1f}"
            row += f"      {qr*1e3:7.1f} / {qp*1e3:7.1f}        {pp['reach']*CONS_MARGIN_PESS/qp*100:5.1f} %"
            print(row)

    # Budget-Aufschluesselung fuer Referenzfaelle
    for v, T in (("a", 147), ("a", 27), ("c", 27)):
        qp, pp, _ = daily_charge(T, v, True)
        print(f"\nAufschluesselung pess. Var {v}, T={T} s (vor Zuschlag {CONS_MARGIN_PESS}):")
        for k_, val in pp.items():
            print(f"   {k_:6s} {val*1e3:8.2f} mC/Tag  = {val/ (qp/CONS_MARGIN_PESS) *100:5.1f} %")
        print(f"   Summe inkl. Zuschlag {qp*1e3:.1f} mC/Tag = {qp/mAh*1e3:.1f} uAh/Tag = mittl. {qp/DAY*1e6:.2f} uA")

    # Mindestkapazitaet fuer 12 Monate (pess)
    print("\n=== erforderliche Nennkapazitaet fuer 12 Monate pess. (Ausnutzung 0.75, SD 2 %/a) ===")
    for v, T in (("a", 147), ("a", 27), ("c", 27), ("a", 10), ("a", 1)):
        qp, _, _ = daily_charge(T, v, True)
        cap = qp * YEAR_D / mAh / (0.75 - 0.02)
        print(f"   Var {v} T={T:4d} s: {cap:6.0f} mAh")

    # Empfindlichkeit: ab welchem mittleren Strom faellt CR2032/CR2450 unter 12 Monate (pess. Zelle)?
    print("\n=== Grenz-Mittelstrom fuer 12 Monate (pess. Zelle) ===")
    for c, (cap, src, util, sd) in cells.items():
        i_lim = cap * (util - sd) * mAh / (YEAR_D * DAY)
        print(f"   {c}: {i_lim*1e6:5.1f} uA mittlerer Strom zulaessig ({cap:.0f} mAh x {util-sd:.2f})")
    print("   Halbe Kapazitaet ([SW] S.4: einzelne Marken ~50 % ohne Puffer-C):",
          f"{225*0.5*mAh/(YEAR_D*DAY)*1e6:.1f} uA (CR2032)")

    # LED-Budget
    print("\n=== LED (REQ-UI-03: <= 5 % Tagesbudget) ===")
    for v, T in (("a", 147), ("a", 27)):
        qp, pp, _ = daily_charge(T, v, True)
        q_led_max = 0.05 * qp / CONS_MARGIN_PESS
        print(f"   Var {v} T={T}: Tagesbudget {qp/CONS_MARGIN_PESS*1e3:.1f} mC -> LED max {q_led_max*1e3:.2f} mC/Tag "
              f"= {q_led_max/(I_LED*T_LED_BLINK):.0f} Blinks a 20 ms/2 mA; Standardmuster {pp['led']*1e3:.2f} mC")
        hb = DAY / 10 * I_LED * 5e-3
        print(f"     Gegenbeispiel 'verbunden'-Herzschlag 5 ms alle 10 s: {hb*1e3:.1f} mC/Tag "
              f"= {hb/(qp/CONS_MARGIN_PESS)*100:.0f} % des Budgets")

    # OTA
    print("\n=== OTA (REQ-FW-05: <= 2 % Kapazitaet) ===")
    img = 200e3  # ANNAHME Image-Groesse 200 kB (BLE-Stack + App)
    pkt = 244
    n_pkt = img / pkt
    q_pkt = (pkt + 14) * US_PER_BYTE * I_RX_GLDO + 0.2e-3 * I_TX0_GLDO  # pess. GLDO
    q_flash = (img / 2048) * (T_FLASH_WR * I_FLASH_WR + T_FLASH_ER * I_FLASH_ER)
    t_ota = 120.0  # ANNAHME Dauer 2 min
    q_idle = t_ota * I_IDLE_GLDO * 0.5  # ANNAHME: CPU halbe Zeit idle zwischen Verbindungsereignissen
    q_ota = (n_pkt * q_pkt + q_flash + q_idle) * 2.0  # Faktor 2 ANNAHME (Wiederholungen, Verifikation)
    for c, (cap, *_r) in cells.items():
        print(f"   {c}: OTA ~{q_ota/mAh:.2f} mAh = {q_ota/mAh/cap*100:.2f} % von {cap:.0f} mAh")
    i_ota = q_ota / t_ota
    print(f"   Mittlerer Strom waehrend OTA ~{i_ota*1e3:.1f} mA ueber {t_ota:.0f} s"
          f" -> mittl. Abfall bei IR 30/100 Ohm: {i_ota*30:.2f} / {i_ota*100:.2f} V")
    q_worst = 600 * 9e-3  # Grenzfall: 10 min Dauerempfang GLDO 9 mA [CC] S.20
    print(f"   Grenzfall 10 min bei 9 mA: {q_worst/mAh:.2f} mAh = {q_worst/mAh/225*100:.2f} % CR2032")

    # Pulslast
    print("\n=== Pulslast Knopfzelle ===")
    i_peak = I_TX0_GLDO + I_ACT_GLDO  # Funk + CPU gleichzeitig, pess.
    for ir in (10, 20, 30, 60, 100):
        print(f"   IR {ir:3d} Ohm: Spitzenstrom {i_peak*1e3:.1f} mA ohne Puffer -> Einbruch {i_peak*ir:.2f} V")
    q_burst = adv_event_charge(3, True, True)
    for dv in (0.1, 0.2):
        print(f"   Puffer-C fuer ganze Adv-Ladung {q_burst*1e6:.1f} uC bei dV={dv} V: {q_burst/dv*1e6:.0f} uF "
              f"(Zelle liefert waehrenddessen mit -> obere Schranke)")

    # Zeitbasis
    print("\n=== Zeitstempel REQ-SYS-07 (+-120 s nach 7 d) ===")
    lim_ppm = 120 / (7 * DAY) * 1e6
    print(f"   zulaessig: {lim_ppm:.0f} ppm")
    for T in (5, 20, 45):
        tc = abs(-0.040 * (T - 25) ** 2)  # [ABS] max Koeff., Umkehrpunkt 25 C (typ)
        tot = 20 + tc + 3
        print(f"   Quarz ABS07 bei {T:2d} C: 20 + {tc:4.1f} + 3 = {tot:5.1f} ppm -> {tot*1e-6*7*DAY:5.1f} s in 7 d, "
              f"{tot*1e-6*14*DAY:5.1f} s in 14 d")
    for name, ppm in (("nRF52 LFRC kalibriert [N52] S.106", 250), ("EFR32 LFRCO [FG22] S.43", 30000)):
        print(f"   {name}: +-{ppm} ppm -> {ppm*1e-6*7*DAY:7.0f} s in 7 d")
    print("   CC2340 LFOSC: im Datenblatt S.27 keine Genauigkeit angegeben -> nicht belegbar")
    print(f"   REQ-GW-09 (+-60 s/Monat) entspricht {60/(30*DAY)*1e6:.0f} ppm")

    # Puffer
    print("\n=== Puffer REQ-LOG-01 ===")
    rec = 12  # ANNAHME: 4 B Zeit, 2 B Rohwert, 2 B Index, 2 B Temp, 1 B Batt, 1 B Flags
    for days in (14, 30, 90):
        n = days * (6 + 2)
        print(f"   {days:3d} d x 8/Tag x {rec} B = {n*rec/1024:.1f} kB  ({n*rec/2048:.1f} Flash-Sektoren a 2 kB [CC] S.21)")

    # ESP32-C3 Vergleich
    print("\n=== Vergleich ESP32-C3 [C3] S.57 Tab 5-9 ===")
    for name, i in (("Deep-sleep 5 uA", 5e-6), ("Light-sleep 130 uA (fuer BLE-Erreichbarkeit noetig)", 130e-6)):
        print(f"   {name}: allein {i*DAY*YEAR_D/mAh:.0f} mAh/Jahr")

    # LiPo grob
    print("\n=== LiPo grob (REQ-ENE-03 >= 3 Monate) ===")
    cap_li = 100.0  # ANNAHME kleine Zelle ~100 mAh
    i_li_extra = 5e-6  # ANNAHME: Schutz-IC + LDO + Ladeschaltung Ruhestrom pess.
    sd_li = 0.03  # ANNAHME 3 %/Monat
    for v, T in (("a", 1), ("a", 5), ("a", 27)):
        qp, _, _ = daily_charge(T, v, True)
        qd = qp + i_li_extra * DAY
        days = cap_li * 0.8 * mAh / (qd + cap_li * sd_li * mAh / 30.4)
        print(f"   Var {v} T={T:3d} s: {days/30.4:5.1f} Monate (100 mAh, 80 % nutzbar)")


if __name__ == "__main__":
    main()
```

## Anhang B – Ausgabe

```
=== Ereignisladungen (uC) ===
  a: connectable Adv 3 Kanaele    real   14.3 uC   pess   35.9 uC
  c: Adv 1 Kanal + RX             real    7.5 uC   pess   18.3 uC
  b: Sensor scannt 30 ms          real  163.0 uC   pess  414.4 uC
  d: Verbindungsereignis          real    4.4 uC   pess   14.7 uC

=== Erreichbarkeitsintervall fuer Frist (99 %) ===
  Frist  60 s -> 2 Chancen noetig -> Intervall <= 28 s
  Frist 300 s -> 2 Chancen noetig -> Intervall <= 148 s

=== Laufzeit [Monate] (real / pess) ===
  Var  T[s]             CR2032            CR2450   Tagesladung real/pess [mC]  Anteil Erreichb. pess
  a       1      17.9 /   5.0     42.6 /  12.0       1320.6 /  3970.9         93.8 %
  a       5      67.8 /  19.3    152.0 /  44.5        331.4 /   989.8         75.3 %
  a      10     104.3 /  30.2    223.7 /  67.3        207.8 /   617.2         60.4 %
  a      20     142.6 /  42.1    292.8 /  90.6        145.9 /   430.8         43.2 %
  a      27     157.7 /  46.8    318.3 /  99.5        129.9 /   382.5         36.1 %
  a      60     189.0 /  56.9    368.8 / 117.7        104.7 /   306.6         20.3 %
  a     120     205.7 /  62.5    394.3 / 127.2         94.4 /   275.6         11.3 %
  a     147     209.1 /  63.6    399.4 / 129.1         92.5 /   269.9          9.4 %
  c       1      31.9 /   9.2     74.8 /  21.7        729.2 /  2139.2         88.6 %
  c       5     101.9 /  29.9    219.2 /  66.7        213.1 /   623.5         60.8 %
  c      10     140.4 /  41.8    289.0 /  90.0        148.6 /   434.0         43.7 %
  c      20     173.1 /  52.1    343.6 / 109.1        116.4 /   339.2         27.9 %
  c      27     184.2 /  55.7    361.3 / 115.4        108.0 /   314.7         22.3 %
  c      60     204.9 /  62.4    393.2 / 127.0         94.8 /   276.1         11.4 %
  c     120     214.8 /  65.6    407.9 / 132.5         89.5 /   260.3          6.1 %
  c     147     216.7 /  66.2    410.7 / 133.5         88.5 /   257.4          5.0 %
  b       1       1.7 /   0.5      4.1 /   1.1      14171.1 / 43213.8         99.4 %
  b       5       8.2 /   2.2     19.8 /   5.5       2901.5 /  8838.4         97.2 %
  b      10      15.8 /   4.4     37.9 /  10.5       1492.8 /  4541.4         94.6 %
  b      20      29.6 /   8.2     69.6 /  19.5        788.4 /  2393.0         89.8 %
  b      27      38.2 /  10.6     88.8 /  25.1        605.8 /  1836.0         86.7 %
  b      60      70.3 /  19.9    157.1 /  45.7        318.9 /   960.7         74.5 %
  b     120     107.2 /  30.9    229.2 /  68.7        201.5 /   602.6         59.4 %
  b     147     118.6 /  34.4    250.3 /  75.7        179.9 /   536.8         54.5 %
  d       1      49.7 /  11.0    114.0 /  26.0        460.0 /  1770.8         86.2 %
  d       5     132.1 /  33.6    274.5 /  74.2        159.3 /   549.8         55.5 %
  d      10     166.7 /  45.3    333.2 /  96.6        121.7 /   397.1         38.4 %

Aufschluesselung pess. Var a, T=147 s (vor Zuschlag 1.2):
   sleep    200.88 mC/Tag  =  89.3 %
   reach     21.12 mC/Tag  =   9.4 %
   meas       2.64 mC/Tag  =   1.2 %
   led        0.24 mC/Tag  =   0.1 %
   ota        0.00 mC/Tag  =   0.0 %
   Summe inkl. Zuschlag 269.9 mC/Tag = 75.0 uAh/Tag = mittl. 3.12 uA

Aufschluesselung pess. Var a, T=27 s (vor Zuschlag 1.2):
   sleep    200.88 mC/Tag  =  63.0 %
   reach    115.01 mC/Tag  =  36.1 %
   meas       2.64 mC/Tag  =   0.8 %
   led        0.24 mC/Tag  =   0.1 %
   ota        0.00 mC/Tag  =   0.0 %
   Summe inkl. Zuschlag 382.5 mC/Tag = 106.3 uAh/Tag = mittl. 4.43 uA

Aufschluesselung pess. Var c, T=27 s (vor Zuschlag 1.2):
   sleep    200.88 mC/Tag  =  76.6 %
   reach     58.48 mC/Tag  =  22.3 %
   meas       2.64 mC/Tag  =   1.0 %
   led        0.24 mC/Tag  =   0.1 %
   ota        0.00 mC/Tag  =   0.0 %
   Summe inkl. Zuschlag 314.7 mC/Tag = 87.4 uAh/Tag = mittl. 3.64 uA

=== erforderliche Nennkapazitaet fuer 12 Monate pess. (Ausnutzung 0.75, SD 2 %/a) ===
   Var a T= 147 s:     37 mAh
   Var a T=  27 s:     53 mAh
   Var c T=  27 s:     44 mAh
   Var a T=  10 s:     86 mAh
   Var a T=   1 s:    552 mAh

=== Grenz-Mittelstrom fuer 12 Monate (pess. Zelle) ===
   CR2032:  18.8 uA mittlerer Strom zulaessig (225 mAh x 0.73)
   CR2450:  45.8 uA mittlerer Strom zulaessig (550 mAh x 0.73)
   Halbe Kapazitaet ([SW] S.4: einzelne Marken ~50 % ohne Puffer-C): 12.8 uA (CR2032)

=== LED (REQ-UI-03: <= 5 % Tagesbudget) ===
   Var a T=147: Tagesbudget 224.9 mC -> LED max 11.24 mC/Tag = 281 Blinks a 20 ms/2 mA; Standardmuster 0.24 mC
     Gegenbeispiel 'verbunden'-Herzschlag 5 ms alle 10 s: 86.4 mC/Tag = 38 % des Budgets
   Var a T=27: Tagesbudget 318.8 mC -> LED max 15.94 mC/Tag = 398 Blinks a 20 ms/2 mA; Standardmuster 0.24 mC
     Gegenbeispiel 'verbunden'-Herzschlag 5 ms alle 10 s: 86.4 mC/Tag = 27 % des Budgets

=== OTA (REQ-FW-05: <= 2 % Kapazitaet) ===
   CR2032: OTA ~0.07 mAh = 0.03 % von 225 mAh
   CR2450: OTA ~0.07 mAh = 0.01 % von 550 mAh
   Mittlerer Strom waehrend OTA ~2.0 mA ueber 120 s -> mittl. Abfall bei IR 30/100 Ohm: 0.06 / 0.20 V
   Grenzfall 10 min bei 9 mA: 1.50 mAh = 0.67 % CR2032

=== Pulslast Knopfzelle ===
   IR  10 Ohm: Spitzenstrom 13.1 mA ohne Puffer -> Einbruch 0.13 V
   IR  20 Ohm: Spitzenstrom 13.1 mA ohne Puffer -> Einbruch 0.26 V
   IR  30 Ohm: Spitzenstrom 13.1 mA ohne Puffer -> Einbruch 0.39 V
   IR  60 Ohm: Spitzenstrom 13.1 mA ohne Puffer -> Einbruch 0.79 V
   IR 100 Ohm: Spitzenstrom 13.1 mA ohne Puffer -> Einbruch 1.31 V
   Puffer-C fuer ganze Adv-Ladung 24.0 uC bei dV=0.1 V: 240 uF (Zelle liefert waehrenddessen mit -> obere Schranke)
   Puffer-C fuer ganze Adv-Ladung 24.0 uC bei dV=0.2 V: 120 uF (Zelle liefert waehrenddessen mit -> obere Schranke)

=== Zeitstempel REQ-SYS-07 (+-120 s nach 7 d) ===
   zulaessig: 198 ppm
   Quarz ABS07 bei  5 C: 20 + 16.0 + 3 =  39.0 ppm ->  23.6 s in 7 d,  47.2 s in 14 d
   Quarz ABS07 bei 20 C: 20 +  1.0 + 3 =  24.0 ppm ->  14.5 s in 7 d,  29.0 s in 14 d
   Quarz ABS07 bei 45 C: 20 + 16.0 + 3 =  39.0 ppm ->  23.6 s in 7 d,  47.2 s in 14 d
   nRF52 LFRC kalibriert [N52] S.106: +-250 ppm ->     151 s in 7 d
   EFR32 LFRCO [FG22] S.43: +-30000 ppm ->   18144 s in 7 d
   CC2340 LFOSC: im Datenblatt S.27 keine Genauigkeit angegeben -> nicht belegbar
   REQ-GW-09 (+-60 s/Monat) entspricht 23 ppm

=== Puffer REQ-LOG-01 ===
    14 d x 8/Tag x 12 B = 1.3 kB  (0.7 Flash-Sektoren a 2 kB [CC] S.21)
    30 d x 8/Tag x 12 B = 2.8 kB  (1.4 Flash-Sektoren a 2 kB [CC] S.21)
    90 d x 8/Tag x 12 B = 8.4 kB  (4.2 Flash-Sektoren a 2 kB [CC] S.21)

=== Vergleich ESP32-C3 [C3] S.57 Tab 5-9 ===
   Deep-sleep 5 uA: allein 44 mAh/Jahr
   Light-sleep 130 uA (fuer BLE-Erreichbarkeit noetig): allein 1139 mAh/Jahr

=== LiPo grob (REQ-ENE-03 >= 3 Monate) ===
   Var a T=  1 s:   2.0 Monate (100 mAh, 80 % nutzbar)
   Var a T=  5 s:   5.3 Monate (100 mAh, 80 % nutzbar)
   Var a T= 27 s:   8.1 Monate (100 mAh, 80 % nutzbar)
```
