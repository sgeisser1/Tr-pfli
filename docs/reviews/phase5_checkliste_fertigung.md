# Phase 5 – Design-Review-Checkliste Fertigung (Sensor Rev C, Gateway-Teile)

| | |
|---|---|
| Stand | 2026-11-08, Fertigung/Kosten |
| Prüfgegenstand | Platine Rev C (`hardware/sensor/fluidi_sensor.kicad_pcb`), Gerber/BOM/CPL (sha256 ORDER Kap. 1), Bestellunterlage `hardware/sensor/out/ORDER_JLC_REV_C.md`, Release `production/rev-C/`, Gateway-Stückliste `hardware/gateway/BOM_GATEWAY.csv` |
| Werkzeuge (selbst gelaufen 2026-11-08) | `.venv/bin/python scripts/fab_checks_rev_c.py` (sha256, **DRC auf Kopie**, Register↔BOM, ENIG-Fläche, Silkscreen, Seite, Kante) → „sha ok, drc ok, register ok, board ok“; `.venv/bin/python hardware/sensor/gen/order_check.py --live` (Vias, Via-in-Pad, Platzhalter, Gerber-Job, Lager 13:06); `scripts/cost_final_phase5.py`; `hardware/gateway/check_rtc_schematic.py`; `production/make_release_rev_c.py` + `sha256sum -c SHA256SUMS` (65/65 OK) |
| Nicht geändert | Platine, Gerber, BOM, CPL (sha256 unverändert = ORDER Kap. 1) |

Legende: ✔ erfüllt (Beleg), ✘ nicht erfüllt, ◐ offen / am Bestelltag bzw. am Muster, – nicht anwendbar.

## A Fertigungsdaten

| Nr | Prüfpunkt | Soll | Ist / Beleg | Status |
|---|---|---|---|---|
| A1 | Upload-Dateien unverändert | sha256 = ORDER Kap. 1 | `fab_checks` 1, `order_check`: 7da2269d…/3d99ffca…/b01ba147… | ✔ |
| A2 | Gerber-ZIP = Gerber-Ordner, 14 Dateien, Job „Revision C“ | gleich | `order_check`: identisch, Job Rev C, 4 L, 1.6 mm, ENIG | ✔ |
| A3 | Lagenaufbau = JLC-Standard (Economic „Standard stack-up only“) | 0.2104/1.065/0.2104 mm | Gerber-Job-Dielektrika = JLC04161H-7628 (JLCPCB_NOTES Kap. 4) | ✔ |
| A4 | Bohrdaten | eine Werkzeuggrösse 0.30 mm, kein NPTH | `PTH.drl` T1/T2 0.300, 146 Löcher; `NPTH.drl` 0 | ✔ |
| A5 | Release-Paket nur aus Kopien, Hashes gleich | sha256 Quelle = Kopie | `make_release_rev_c.py` (assert je Datei), `sha256sum -c` 65 OK | ✔ (Arbeitskopie, s. Befund F-10) |

## B Leiterplatte gegen JLC-Regeln

| Nr | Prüfpunkt | JLC-Grenze (Quelle) | Ist | Status |
|---|---|---|---|---|
| B1 | DRC mit Projektregeln (17 Regeln, JLC-Werte) | – | KiCad 10.0.8, Kopie, `--schematic-parity --refill-zones --severity-all`: **0 Verstösse, 0 offen, 0 Parität** | ✔ |
| B2 | Leiterbahn/Abstand | 4 L: 0.09/0.09 mm (JLCPCB_NOTES Kap. 3) | Regel 0.10/0.10; kleinste Bahn 0.15 | ✔ |
| B3 | Via | ohne Aufpreis ≥ 0.45/0.30 (Rechner „0.3mm/(0.4/0.45mm)“) | einzige Grösse 0.45/0.30, 145 Vias | ✔ |
| B4 | Kupfer–Kontur | ≥ 0.2 mm (gefräst) | Regeln 0.30 / 1.0 (Innenlagen Kopf) / 1.25 (Sonde) | ✔ |
| B5 | Silkscreen | ≥ 1.0 mm Höhe, ≥ 0.15 Strich | kleinste 1.00 / 0.15 (`fab_checks` 5) | ✔ |
| B6 | ENIG-Fläche | Aufpreis > 30 % (ExtraCharges Nr. 5) | 3.5 % (Pads mit Maskenöffnung F+B) | ✔ |
| B7 | Via-in-Pad gefüllt | POFV gewählt + Angabe welche Vias (Via-Covering-Hilfe) | 8 VIP mit Füllattribut; Remark nennt „alle 0.30-mm-Bohrungen“ (ORDER Kap. 8, nachgeführt) | ✔ (Kontrolle Lage `sk` ◐) |
| B8 | Dicke / Farbe / Oberfläche für Economic | 0.8–1.6 mm; 1.6 mm ENIG nur grün | 1.6, grün, ENIG 1 U" | ✔ |
| B9 | Material Type | Default FR4 TG135 | belassen; FEM rechnet mit TG-135-Laminat (KB-6160A: T260 > 10 min, Td 305 °C); Er unbekannt → Kalibrierung | ✔ / ◐ Er am Muster |
| B10 | Kleinplatinen-Zuschläge | Entgraten 1.5–3 cm: 0.02 USD/Stk; „Small boards“ erst ≥ 500 Stk | Deburring Yes 0.50 USD (Screenshot); kein Zuschlag „Small boards“ | ✔ |
| B11 | Markierung | keine Auftragsnummer mehr (seit Mai 2026) | Remove Mark; Platzhalter `JLCJLCJLCJLC` noch auf B (Befund F-2) | ◐ |

## C Bestückung (Economic PCBA)

| Nr | Prüfpunkt | Grenze (Quelle) | Ist | Status |
|---|---|---|---|---|
| C1 | nur eine Seite | Economic einseitig (`JLCPCB_PCBA-Capabilities_Auszug…`) | alle 50 CPL-Zeilen `Top`; auf B nur TP4/TP5 (keine Bauteile) | ✔ |
| C2 | kleinste Bauform | ≥ 0402 | 0402, nichts kleiner (`fab_checks` 6) | ✔ |
| C3 | IC-Pinabstand | ≥ 0.4 mm | U1 0.5, U3 0.5, U2/U4–U6 0.65 mm (Pad-Raster pcbnew) | ✔ |
| C4 | Abstand zur Kante | > 0.3 mm empfohlen (FAQ Q14, Nutzentrennung ±0.2) | Pads ≥ 0.53 mm (R10); Courtyards ≥ 0.355 ausser **BT1** (Courtyard = Zellumriss ragt über die Kante; Clipkörper x −4.4…11.7 = 1.3 mm zur Kante, PCB_OUTLINE Tab. XBT1) | ✔ (Befund F-7) |
| C5 | Menge / Grösse | 2–50 Stk, Einzelplatine ≥ 10 × 10 mm | 5 bzw. 16 Stk, 26 × 158.5 mm | ✔ |
| C6 | BOM ↔ CPL ↔ Platine | gleiche Designatoren, Footprints | 50/50, Footprint BOM = Platine (`fab_checks` 3) | ✔ |
| C7 | Rotation / Pin 1 | JLC-Vorschau | nur DRITTQUELLE/Projektregel → Abhakliste ORDER Kap. 5 (Kurzschlussfälle U1, U2, U3, U4–U6, Y1) | ◐ am Bestelltag |
| C8 | Teile ohne JLC-Bestückung separat | Liste | `fluidi_sensor_bom_extra.csv`: C19/C20 DNM, AE1/E1/TP1/TP2/TP4/TP5 Leiterplattenstrukturen, CR2032 lokal | ✔ |
| C9 | Lager | ≥ 5 / 16 je Teil | live 2026-11-08 13:06: alle ≥ 629; **BT1 629**, sinkend | ✔ / ◐ Bestelltag |
| C10 | Economic + ENIG + POFV + 4 L | in JLC-Doku | **nicht belegt** (weder erlaubt noch ausgeschlossen) | ◐ B-2, Formular |

## D Register und Dokumente

| Nr | Prüfpunkt | Ist | Status |
|---|---|---|---|
| D1 | Jede BOM-LCSC-Nummer im Register, Kategorie gleich, Datenblatt lokal | 26/26 (`fab_checks` 3); C1552 im Register „Extended/Preferred“ = JLC „preferred“ | ✔ |
| D2 | Gateway-Teile im Register | GW-RTC (DS3231 Rev 10), GW-RTC-MOD (Schaltplan), GW-RTC-AN, GW-RTC-CELL, GW-CLIM1-BRD, GW-PSU, GW-SD neu/aktualisiert | ✔ (Lücken F-8) |
| D3 | JLC-Regeln lokal | 9 Textauszüge + 1 Tabelle `docs/references/JLCPCB_*_2026-11-08.*`, JLCPCB_NOTES Kap. 10 | ✔ |
| D4 | Bestellanleitung | `docs/manuals/BESTELLEN_JLC.md` (PCBA-Teil ANNAHME) | ✔ |

## E Kosten

| Nr | Prüfpunkt | Ist | Status |
|---|---|---|---|
| E1 | Screenshot-Posten = Modell | 76.30 USD = `QUOTE_USD[20]` (Assertion im Skript) | ✔ |
| E2 | Versand nachgeführt | DHL 23.52 USD (`cost_model.py`), COSTS_REV_B neu erzeugt | ✔ |
| E3 | REQ-FAB-04 | Serie 8.38 / 8.17 CHF (Economic), 9.31 CHF (Standard-Ausweichweg) | ✔ |
| E4 | Versteckte Kosten | Extended-Gebühr, Mindestmengen, Ausschuss, Reserveboard, Verzollung im Modell; Pre-reflow, Confirm Production File, Coupons als Empfindlichkeit | ✔ / ◐ |
| E5 | Gateway separat (REQ-FAB-06) | Kauf 81.47 CHF (5.97 ANNAHME), Neuwert 98.62 CHF | ✔ |

## F Befunde

| Nr | Schwere | Befund | Begründung | Vorschlag |
|---|---|---|---|---|
| F-1 | **wichtig** | Economic PCBA mit 4 L + ENIG + POFV ist in keiner JLC-Quelle belegt (B-2 bleibt) | Capability-Seite, PCBA-FAQ, Preisseite und Websuche 2026-11-08 schweigen zu Via Covering; Schalter „PCB Assembly“ war im Screenshot aus | Am Bestelltag prüfen (ORDER Kap. 4 Nr. 5, Anleitung Schritt 6); sonst Standard-PCBA (Serie +58 CHF, Freigabe Auftraggeber) |
| F-2 | klein | Platzhalter `JLCJLCJLCJLC` auf B.Silkscreen ist überholt; JLC: „DO NOT add“ | Option Order Number seit Mai 2026 weg; Wirkung des Texts nicht dokumentiert. Liegt in Zone Z2 Band B (im Kopf verdeckt), nur Silkscreen | Rev C: Remove Mark + Remark „delete placeholder“ (umgesetzt in ORDER); nächste Layout-Revision: Text entfernen (`pcb_build.py`) |
| F-3 | wichtig | Remark nannte die zu füllenden Vias nicht konkret und verwies auf die Auftragsnummer | JLC verlangt Angabe der zu füllenden Vias oder des Durchmessers | umgesetzt: ORDER Kap. 8 „fill ALL plated holes with 0.30 mm drill (146)“ |
| F-4 | klein | Preis „Confirm Production File = Yes“ unbekannt | JLC-Hilfe ohne Preis; Screenshot mit „No“ | Am Bestelltag ablesen (ORDER Kap. 4 Nr. 6); Option trotzdem wählen (Kontrolle `sk`/`bo`) |
| F-5 | **wichtig** | Gateway: RTC-Modul (21.3 × 20.0 × 13.6 mm) und Grove SHT41 (20 × 40 mm) passen nicht in die CAD-Platzhalter (15 × 12 × 4 bzw. max. 24 × 14 mm) | Masse aus Herstellerseite/Händler, CAD-Annahmen `fluidi_gateway_pi.py` | Mechanik: Rahmen/Klimakammer anpassen oder kleinere Module wählen (RTC ohne Ladepfad bleibt Pflicht) |
| F-6 | wichtig | Gateway-Status-LED-Platine im CAD, aber nicht entworfen, keine Kosten | `fluidi_gateway_pi.py` ANNAHME „LED-Platine 8 × 8.2“ | Elektronik: entwerfen oder streichen; danach BOM_GATEWAY G9 nachführen |
| F-7 | klein | BT1-Courtyard ragt über die Platinenkante | Courtyard = Zellumriss (Zelle x −7.0…13.0), Clip selbst 1.3 mm von der Kante, Pads ≥ 0.53 mm | Kein Handlungsbedarf; JLC-Vorschau kann warnen → in Anleitung Schritt 8 erwartet. Bei nächster Revision Courtyard auf den Clip begrenzen und Zellumriss auf User-Lage |
| F-8 | klein | Datenblätter fehlen: Netzteil (Konformität), microSD Industrial, Grove-SHT41-Schaltplan, CR1220 | Händlerseiten ohne Download | Orchestrator gemeldet (Register-Bemerkung); beim Wareneingang ablegen, Sicherheits-Agent prüft Netzteil |
| F-9 | klein | „Pre-reflow Soldering 0.016 USD/Lötstelle“ auf der JLC-Preisseite, Anwendung unklar | Falls berechnet: Prototyp +10.41 CHF, Serie +33.32 CHF | Im Warenkorb prüfen (Anleitung Schritt 9) |
| F-10 | klein | Release-Paket aus Arbeitskopie erzeugt (Mechanik/Druckteile und Schaltplan-PDF werden in Phase 5 parallel geändert) | README Spalte „geändert“ | Nach dem Commit `production/make_release_rev_c.py` erneut laufen lassen |
| F-11 | wichtig | BT1 C5213768 einziges mechanisch festgelegtes Extended-Teil, Bestand 629 und sinkend | Lagerabfragen 2026-11-07/08 | Prototyp bald bestellen; Serie: Bestand vor Freigabe prüfen |
| F-12 | klein | Gateway-Teile teils nicht an Lager (microSD Industrial, Grove SHT41; Pi nicht nötig) | pi-shop.ch 2026-11-08 | Alternativen gleicher Klasse zulassen (Register/BOM-Bemerkung) |

Keine kritischen Befunde. Freigabeempfehlung für die **Prototypbestellung** unter den Bestell-Prüfungen F-1 und C7
(Abhakliste ORDER Kap. 4/5).
