# Phase 5 – Gateway-Status-LED: Entscheidungsvorlage

Ersteller: Elektronik · Datum 2026-11-08 · Anlass: Befund Fertigung F-6 (`docs/reviews/phase5_checkliste_fertigung.md`):
„LED-Platine 8 × 8.2“ im Gateway-CAD (`mechanical/gen/fluidi_gateway_pi.py` Z. 31, 85, 197–207), aber weder entworfen
noch in `hardware/gateway/BOM_GATEWAY.csv` (G9 = 0.00, „offen“).

## 1 Was die LED tun soll – Stand der Doku

| Quelle | Aussage |
|---|---|
| D-010 (Änderungswunsch 1), D-011 | Gateway hat eine **LED als Tropfen**, der wie am Sensor an der Farbfuge „heraustropft“ (G1 v3 freigegeben). Nur Optik, keine Funktion festgelegt |
| `docs/design/P3_FLUIDI.md` Kap. Gateway | „Status-LED: Board-LED oder eigene LED über Lichtleiter (Phase 4)“; Renders zeigen den Tropfen **grün** |
| D-014, D-017, D-022, `GATEWAY_SETUP.md`, `SOFTWARE_CONCEPT.md`, `firmware/gateway/` | **keine** Funktion der Gateway-LED. LED-Hinweise (Giessen, Kopplung, Farben D-010) betreffen nur die **Sensor**-LED. `fluidi_gw` steuert keinen GPIO |

→ Die Funktion ist **nicht festgelegt**. Vorschlag (Entscheid Auftraggeber, Umsetzung Software), bewusst einfarbig:

| Zustand | Muster | Umsetzung |
|---|---|---|
| Pi startet | Herzschlag | Kernel-Trigger `heartbeat` über `dtoverlay=gpio-led,gpio=17,label=fluidi,trigger=heartbeat` (overlays README, Abschnitt gpio-led, Auszug Z. 1606–1658) – ohne Programm |
| Dienst `fluidi-gateway` läuft, alles in Ordnung | kurzer Blitz alle ≈ 5 s | Dienst schreibt `/sys/class/leds/fluidi/…` (Trigger `none`/`timer`) |
| Kopplungsfenster offen (≤ 300 s, GATEWAY_API Kap. Kopplung) | schnelles Blinken | Dienst |
| Dienst gestoppt/abgestürzt, Gateway aus | aus (bzw. Herzschlag nach Neustart) | systemd `ExecStopPost` → LED aus |
| Nacht | aus | gleiches Zeitfenster wie die Sensor-LED (`led_window`) – **ANNAHME**, Auftraggeber fragen |

Farbcodes wie am Sensor (Gelb/Blau/Rot) bräuchten eine RGB-LED (Variante C).

## 2 Varianten

| | A: Pi-eigene ACT-LED über Lichtleiter | **B: grüne 3-mm-LED + Widerstand an GPIO17, Litzen (Vorschlag)** | C: LED-Platine 8 × 8.2, RGB 1615 wie Sensor |
|---|---|---|---|
| Teile | keine | Kingbright WP710A10GD + YAGEO MFR-25FBF52-470R | eigene Leiterplatte, D1 TUOZHAN 1615 (Extended, C7496855) + 3 R, 4 Litzen |
| Neue Teile/Datenblatt | – | lokal abgelegt, INDEX GW-LED1/GW-R1 | D1-Datenblatt lokal vorhanden; Leiterplatte, Schaltplan, Layout, Bestellung fehlen |
| Kosten Teile | 0 | **0.29 CHF** (Digi-Key CH, 1 Stk: 0.20 + 0.09, Abruf 2026-11-08) | nicht erhoben (eigene Leiterplattenbestellung + Bestückung + Extended-Teil) |
| Aufwand | Lichtleiter bis zur ACT-LED | 2 Lötstellen am Pi, 1 Lötstelle in der Litze | Entwurf, DRC, Bestellung, Handlöten an 4 GPIO-Pads |
| Problem | Lage der ACT-LED in der Zeichnung **nicht** angegeben (`fluidi_gateway_pi.py` Z. 27); Lichtschacht sitzt fest bei LED_X 24 | einfarbig | 3 GPIO + 3V3, Kosten, Termin; kein Mehrwert, solange keine Farbfunktion festgelegt ist |
| Bewertung | verworfen (Geometrie unbekannt) | **empfohlen** | nur falls Farben ausdrücklich gewünscht |

## 3 Variante B im Detail

**Schaltung:** Pi J8 Pin 11 (GPIO17) → R1 470 Ω → Anode LED, Kathode (kurzes Bein, Abflachung) → Pi J8 GND Pin 14
(Pin 9 ist für Klimasensor/RTC vorgesehen, `fluidi_gateway_pi.py` Z. 57; Pin 14 ist frei).
Pinbelegung J8: `docs/datasheets/RaspberryPi_Zero2W_ReducedSchematics_RP-008360-DS-1.pdf` (Block J8: Pin 11 = GPIO17).

**Warum GPIO17:** nach dem Reset Eingang mit **Pull-Down** (`Broadcom_BCM2835_ARM-Peripherals_Datasheet_2012-02.pdf`
S. 102, Tab. 6-31: GPIO17 „Low“) → LED bleibt bis zum Overlay dunkel, kein Glimmen. Nicht belegt durch I²C (GPIO2/3),
UART (GPIO14/15). Alternativfunktion SPI1_CE1/SPI0_CE1 – SPI wird nicht genutzt (**ANNAHME**, `config.txt` prüfen).

**Strom (nachgerechnet):**
- VOH ≥ 3.0 V bei 2 mA (Default-Treiberstärke 8 mA; die Spezifikation gilt bis zum eingestellten Strom, Auszug Z. 15/36), IOH ≥ 17 mA bei VO 2.3 V nur bei maximaler Treiberstärke 16 mA (Fussnote c, Z. 466; Korrektur Elektronik 2026-11-09); Pi-3V3 ausgelegt für **≈ 3 mA je GPIO**, 16 mA je Pad unschädlich
  (`docs/references/RaspberryPi_GPIO-Doku_Auszug_2026-11-08.txt`, Z. 423 ff. und Z. 42/46 gpio-pad-controls).
- VF ≈ 1.9 V bei 3 mA (Kennlinie `Kingbright_WP710A10GD_Datasheet_V10B.pdf` S. 3, abgelesen, **ANNAHME** ±0.05 V);
  VF typ 2.0 / max 2.4 V bei 10 mA (S. 2).
- Typisch: I = (3.3 − 1.9) / 470 = **3.0 mA** → P_LED 5.7 mW (abs. max 62.5 mW, IF max 25 mA, S. 2), P_R 4.2 mW
  (1/4 W, `Yageo_MFR_Datasheet_V4.pdf` S. 3).
- Ungünstig: (3.0 − 2.3) / 470 = 1.5 mA; mit VF max 2.4 V (S. 2) und R +1 %: 1.26 mA. Höchstwert mit 3.3 V + 5 % (**ANNAHME**), VF 1.9 V − 0.1 V Toleranz (S. 2 Note 2) − 0.03 V (40 °C, −2 mV/°C) und R −1 %: 3.7 mA (Nachrechnung Elektronik 2026-11-09, 470 Ω bestätigt).
- Helligkeit proportional zu IF (S. 3): typ 25 mcd × 0.30 ≈ **7 mcd**, ungünstig 10 mcd × 0.15 ≈ 1.5 mcd hinter dem
  transluzenten Fenster. **PROTOTYP-PRÜFUNG** Sichtbarkeit im hellen Raum; zu dunkel → R1 330 Ω (≈ 4 mA typ., über der
  3-mA-Auslegung, unter dem 16-mA-Wert) oder Variante C.

**Mechanik (Abstimmung `mechanik`):** LED statt Platine in den Lichtschacht (Innen-Ø 4.6, `fluidi_gateway_pi.py` Z. 200);
LED Bund Ø 3.2, Körper Ø 2.9 × 5.4 mm (Datenblatt S. 1) → zentrieren (Klebstoff oder Ring). Der Körper ragt ≈ 3.8 mm
hinter den 1.6 mm langen Schacht, dazu die abgewinkelten Beine. Abstand zur Pi-Platine im CAD prüfen (bisher LED-Platine
5.7 mm). Im CAD `LED_Platine`/`LED_RGB` durch LED-Körper ersetzen.

**Montage:** R1 direkt am Anodenbein (≤ 10 mm), beide Lötstellen mit Schrumpfschlauch; Litze AWG 28 aus G10 (vorhanden),
Länge ≈ 40 mm (Pin 11 bei x 4.9 nach Rechnung wie `check_gateway_pi.txt` Nr. 5, LED bei x 24). Keine Gefährdung
(3.3 V, ≤ 4 mA); Kurzschluss GPIO–GND nur bei fehlendem R1 → R1 vor dem Einschalten messen.

**Software (Umsetzung `software`, nicht Teil dieser Vorlage):** Zeile `dtoverlay=gpio-led,gpio=17,label=fluidi,trigger=heartbeat`
in `config.txt` (Installationsskript), Zustandslogik im Dienst ≈ 20 Zeilen, GATEWAY_SETUP Kap. 5 ergänzen.

## 4 Kosten und BOM

| Pos. (Vorschlag G9 neu) | Teil | Menge | CHF | Quelle |
|---|---|---|---|---|
| G9a | Kingbright WP710A10GD | 1 | 0.20 | Digi-Key CH, Abruf 2026-11-08, Lager 24 503 |
| G9b | YAGEO MFR-25FBF52-470R | 1 | 0.09 | Digi-Key CH, Abruf 2026-11-08, Lager 19 960 |
| | **Summe Teile** | | **0.29** | |

Versand Digi-Key CH unter 70 CHF: 23 CHF (Shopseite, 2026-11-08) → mit einer anderen Bestellung bündeln oder
gleichwertige 3-mm-LED grün + 470 Ω aus Werkstattbestand/Elektronikladen (dann VF/Iv am Teil prüfen).
`BOM_GATEWAY.csv` G9 erst nach Entscheid nachführen (Elektronik).

## 5 Entscheid nötig (Auftraggeber)

1. Variante **B** (einfarbig grün, 0.29 CHF, keine Platine) – empfohlen – oder C (RGB-Platine, Farben wie Sensor).
2. LED-Funktion nach Tab. Kap. 1 (inkl. Nacht aus) bestätigen.

Quellen: `docs/datasheets/Kingbright_WP710A10GD_Datasheet_V10B.pdf`, `docs/datasheets/Yageo_MFR_Datasheet_V4.pdf`,
`docs/datasheets/Broadcom_BCM2835_ARM-Peripherals_Datasheet_2012-02.pdf`, `docs/datasheets/RaspberryPi_Zero2W_ReducedSchematics_RP-008360-DS-1.pdf`,
`docs/references/RaspberryPi_GPIO-Doku_Auszug_2026-11-08.txt`; Digi-Key CH Produktseiten WP710A10GD und MFR-25FBF52-470R (2026-11-08).
