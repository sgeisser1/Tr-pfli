# Antwort auf Prüfrunde 1 – Konzepte (CONCEPTS.md v0.1 → v0.2)

| | |
|---|---|
| Dokument | `docs/reviews/phase2_concepts_response.md` |
| Datum | 2026-11-06 |
| Ersteller | Konzeptredaktor |
| Geprüft wurde | `docs/concepts/CONCEPTS.md` v0.1 |
| Ergebnis | `docs/concepts/CONCEPTS.md` **v0.2**; Skripte `cost_model.py`, `concept_costs.py`, `concept_energy.py`, neu `jlc_price_cache.py`; BOMs `docs/concepts/bom/`; Register `_staging/INDEX_konzepte.csv` |
| Prüfberichte | `phase2_concepts_sicherheit.md` (S2-…), `phase2_concepts_fertigung.md` (K-/W-/k- „DFM“), `phase2_concepts_redteam.md` (K-/W-/k- „RT“) |
| Vorgaben Projektleiter | Entscheide 1–11 vom 2026-11-06 (D-005 Kostendefinition, 4 Lagen, VETO-Lösung, Quarz, Messkette, Pinplan, Energie, Kopf/A-32, Gateway, FW-04, übrige) |

Stellenangaben beziehen sich auf CONCEPTS.md v0.2.

## Sicherheit (`phase2_concepts_sicherheit.md`)

| Befund | Stufe | Antwort | Stelle |
|---|---|---|---|
| S2-K01 Ladeschutz falsch (Diode Richtung Zelle, 100 Ω einzige Begrenzung, Pads nicht konstruktiv geschützt) – **VETO** | kritisch | **umgesetzt**: VPROG-Leitung und Diode entfernt; Programmieren nur über **Dummy-Zellen-Adapter** im Halter (Zelle und Adapter schliessen sich physisch aus = Barriere 1); Pads RX/TX/SWDIO/SWDCK je **2 × 100 kΩ** (Barriere 2, bei Kurzschluss eines Widerstands noch 100 kΩ), Baudrate ≤ 57 600 begründet; kein nRST-/BOOT-Pad. Worst-Case 5.5 V/2.0 V: 17.5 µA je Pad, 35 µA mit Einzelfehler, 87.5 µA alle Pads. Renata-Grenzwert fehlt → OP-K7 (Anfrage Auftraggeber). Matrix auf „~“ korrigiert, Testplanpunkt genannt. Veto-Aufhebung liegt beim Sicherheits-Agenten | 2.1, 2.7, 6.1, OP-K7 |
| S2-W01 Fehlerreserve nur 5 K (REQ-SAF-01 a) | wichtig | **umgesetzt**: Matrix „~“, Renata-Anfrage (65 °C Dauer, Kurzschlusstemperatur) und Kurzschlussversuch mit ΔT_Zelle als PROTOTYP-PRÜFUNG; gilt analog für A-32 | 2.10, 2A, 6.1, OP-K7 |
| S2-W02 MLCC-Biegeriss als Kurzschluss | wichtig | **umgesetzt**: Platzierung im steifen Kopfbereich, Längsachse parallel zur Biegelinie, fern von Sondenwurzel/Schraubdom; Soft-Termination-Typ als offener Punkt (kein Datenblatt vorhanden), FMEA-Eintrag | 2.1, 2.10, OP-K16 |
| S2-W03 REQ-SAF-05 nur Absicht | wichtig | **umgesetzt** (Regeln): keine Vias/Bauteile in der Dichtzone, keine Vias im Batteriefach (sonst epoxy-gefüllt +20.3 USD), Platinenkante im Elektronikraum oder umlaufend gedichtet, Flutungstest beider Räume mit Zellstrom. Konstruktion folgt in Phase 3/4 | 2.10 |
| S2-W04 Messbrücke als Speisepunkt | wichtig | **umgesetzt**: Messbrücke entfernt; REQ-ENE-07 über Mess-Zwischenadapter im Halter (vor dem Verpolschutz) | 2.1, 2.7 |
| S2-W05 REQ-FW-04 Anti-Rollback unbelegt, ROM-Bootloader unsigniert | wichtig | **umgesetzt**: TRM recherchiert – ROM-Bootloader sperrbar (pBldrVtor FORBID oder MCUboot, TRM S.460), allowFlashProgram, WEPR-Sektorschutz, SWD-Sperre/Passwort (S.425–426, S.379, S.234); **kein Hardware-Monotonzähler** gefunden → Anti-Rollback per MCUboot-Software, Bewertung „~“ | 2.8, 6.1, OP-K8 |
| S2-W06 DS3231-Modul mit Ladepfad, lose Knopfzelle im Gateway | wichtig | **umgesetzt**: RTC ohne Ladepfad (Superkondensator, z. B. RV-3028-C7, oder Modul mit lokal belegtem Schaltplan ohne Ladepfad, Zelle hinter Schraube); Datenblatt RV-3028 nicht ladbar → OP-K14 | 5.1, OP-K14 |
| S2-W07 Gateway-Firmware/Zugangsdaten ungeschützt | wichtig | **umgesetzt**: Secure Boot (RSA-PSS) und Flash-Verschlüsselung ESP32-S3 belegt (DS S.48/49); signierte Gateway-Updates, Schlüssel offline; eFuse-Abwägung Phase 3 | 5.1 |
| S2-L01 Verpolschutz-Pinbelegung, Kontaktbild | klein | **umgesetzt**: Pinbelegung (Drain = Zelle+, Source = VDD, Gate = GND) festgehalten, Verpoltest 24 h + Kontaktbild | 2.4, 2.10 |
| S2-L02 Halter nur Au-Flash | klein | **umgesetzt**: „Au-Flash 1 µ″“ statt „vergoldet“, Fall-/Schrägsitz-/Korrosionstest | 2.4, 2.10, 6.1 |
| S2-L03 Verschluckschutz Ausführung offen | klein | **umgesetzt**: Gewindeeinsatz in BOM, Belege UL 4200A in Phase 4 | 2.10, `concept_costs.py` |
| S2-L04 CA-Schlüssel auf SSD, IP-SAN widerspricht Constraints | klein | **umgesetzt**: CA-Schlüssel nur RAM/tmpfs; IP-SAN-Rückfall gestrichen; Rückfall nur neue Einmal-CA mit genau einem Namen | 5.2 |
| S2-L05 Renata: keine direkte Sonne | klein | **umgesetzt**: helles Gehäuse, Hinweis Anleitung, in Renata-Anfrage | 2.10, OP-K7 |
| S2-L06 A-32 Clip-Risiken | klein | **umgesetzt**: in A-32-Sicherheitszeile und Empfehlung (leichter Vorteil A) | 2A, 7 |
| S2-L07 Hinweise C (KISET < 60 mA, BQ29700 2.8 V, SMAJ20A VC 32.4 V) | klein | **abgelehnt (zurückgestellt)**: C ist ausgeschlossen; nur bei Wiederaufnahme lösen (wie vom Prüfer vorgeschlagen) | – |

## Fertigung (`phase2_concepts_fertigung.md`)

| Befund | Stufe | Antwort | Stelle |
|---|---|---|---|
| DFM K-1 48-MHz-Quarz CL 20 pF | kritisch | **umgesetzt**: HCI XC32M4-48.000-F08NLDT **C2925606** (8 pF, ESR < 40 Ω, ±10 ppm), gegen CC2340 DS S.26 (CL 5–9 pF, ESR ≤ 60 Ω) geprüft; Datenblatt abgelegt, Register; C5160139 als verworfen registriert. TKD C20623612 (7 pF) nicht gewählt: Seriendatenblatt nennt 7 pF nicht | 1, 2.4, Register |
| DFM W-1 Röntgengebühr fehlt | wichtig | **umgesetzt**: `cost_model.py` (XRAY_TIERS, Spalte leadless), 2 leadless/Board (CC2340, TMP1075) als Stückkosten (proportional zur Menge, D-005) | `cost_model.py`, 2.6 |
| DFM W-2 Pre-reflow unklar | wichtig | **umgesetzt** als offener Punkt mit beiden Werten (A +1.93 CHF); reales JLC-Angebot OP-K1 | 6.3, OP-K1 |
| DFM W-3 Staffelpreise | wichtig | **umgesetzt**: Preis nach Staffel der tatsächlichen Bestellmenge (Preisdaten aus JLC-API in `jlc_prices.json`) | `cost_model.part_price` |
| DFM W-4 A-H nicht Economic-fähig | wichtig | **umgesetzt**: A-H entfällt | 2.9 |
| DFM W-5 Abstand zu 65-USD- und 5-CHF-Grenze | wichtig | **umgesetzt**: Spalten Warenwert und Abgaben je Szenario; mit/ohne Versand bleibt im JLC-Angebot zu klären | 2.6, `concept_costs.py` 2, OP-K1 |
| DFM W-6 keine Board-Reserve | wichtig | **umgesetzt**: Serie 20 PCB / 16 bestückt / 15 Sensoren (Entscheid PL) | alle Kostentabellen |
| DFM k-1 C1552 Preferred | klein | **umgesetzt**: Kategorie `preferred` (Economic gebührenfrei) | `cost_model.py`, 2.4 |
| DFM k-2 BOM-Duplikate | klein | **umgesetzt**: Zusammenfassung nach LCSC (`merge`) | `concept_costs.py` |
| DFM k-3 Registerlücken C1548/C1555, Stand Staging | klein | **umgesetzt**: FH-Serienzeile mit C1548/C1555/C1546 im Staging; Stand im Dokument nachgeführt (INDEX enthält v0.1-Teile, v0.2-Zeilen im Staging) | Register, OP-K11 |
| DFM k-4 Halter nur Au-Flash | klein | **umgesetzt** (wie S2-L02) | 2.4, 2.10 |
| DFM k-5 knappe Lager | klein | **umgesetzt**: Lager in Tabellen; FDC2212 (310), Keystone 3034 (664) genannt; vor Bestellung neu abfragen (`jlc_price_cache.py`) | 2.4, 2A, 4.2 |
| DFM Kap. 5 Prototyp 5/5 statt 5/2 | Empfehlung | **umgesetzt**: Prototyp 5/5 empfohlen, 5/2 gezeigt; 2-L-Option mit Kosten | 2.6, 6.2, 7 |

## Red Team (`phase2_concepts_redteam.md`)

| Befund | Stufe | Antwort | Stelle |
|---|---|---|---|
| RT K-1 Messkette nicht baubar (Zählgrenze, Schalter, Speisung, tpd) | kritisch | **umgesetzt**: Arbeitsbereich 2–6 MHz (LGPT-Synchronisation 48 MHz, TRM S.481), Speisung über High-Drive-DIO12 ratiometrisch (geregeltes 1.8-V-Rail verworfen wegen VIH = 0.8·VDDS, DS S.31), Cref1/Cref2 per GPIO nach GND (kein Analogschalter), Steigung je Messung aus zwei Messungen, tpd-Kompensation über Kalibrierung + VDD/T-Korrektur, Strom ≈ 0.9 mA, BOM/Pins/Kosten nachgeführt | 2.3, 2.2, 2.4 |
| RT K-2 Kostenzuordnung Artefakt | kritisch | **umgesetzt**: D-005 (PCB fix/Grenzkosten, Vollkosten je Szenario) in `cost_model.py`; Lagenentscheid technisch begründet | 1, 2.6, 6.2 |
| RT W-1 Panasonic CR2032 / A-32 | wichtig | **umgesetzt**: A-32 voll gerechnet (Kosten 8.08 CHF, Laufzeit pess. DS 11.9 Mt. bei 1 min, Kopf 28 × 12 × 45, Sicherheit); Empfehlung A vs. A-32 begründet. Die RT-Schätzung „≈ 34 Monate“ gilt nur mit Leck-ANNAHME (pess. A: 41 Mt.), nicht mit Datenblattgrenze | 2A, 7 |
| RT W-2 REQ-ENE-09 zu optimistisch; Puffer pess. nicht erfüllt; Koexistenz | wichtig | **umgesetzt**: TMP1075 + Pull-ups geschaltet; Puffer 4 × 100 µF (≥ 325 µF); Laufzeitnachweis mit Samsung-Leckgrenze (pess. DS); REQ-ENE-09 als „Nachweis Messung“ gekennzeichnet; Koexistenz 50 % als Sensitivität | 2.5, 6.1 |
| RT W-3 GPIO-Budget QFN24 | wichtig | **umgesetzt**: Pinplan mit DS-Seiten, passt ohne QFN40 (Pins geteilt: TX/LED, Taster/Trigger, SWD/I²C), Einschränkungen genannt | 2.2 |
| RT W-4 bessere Kopfanordnungen | wichtig | **teilweise umgesetzt**: Keystone 3008/3009 bei JLC nicht lieferbar (4/21 Stk); A-H entfällt (Economic einseitig); A-F als CAD-Aufgabe; A-32 gerechnet; Halter quer verworfen (Breite > 35 mm) | 2.9, OP-K15 |
| RT W-5 Kostenposten fehlen | wichtig | **umgesetzt**: 2. Dichtung, Gewindeeinsatz, AMS-Spülung, Ausschuss 5 % lokal + Reserveboard, Messkettenteile, Epoxid statt Acryl für 2 L (A2); PCB-Länge ≈ 167 mm als OP-K1b | 1, `concept_costs.py`, OP-K1 |
| RT W-6 Koexistenz Gateway | wichtig | **umgesetzt**: Risiko bewertet, BLE-Koprozessor (ANNAHME CHF 5–8) budgetiert, Test zuerst | 5.1, OP-K12 |
| RT k-1 Leckgrenze Samsung statt Murata | klein | **umgesetzt**: 100 MΩ·µF (Samsung S.53) | 2.5 |
| RT k-2 Au-Flash relativieren | klein | **umgesetzt** | 6.1 |
| RT k-3 Taster-Pull-up bei Dauerdruck | klein | **umgesetzt**: Firmware-Regel | 1 |
| RT k-4 Pull-ups am TMP-GPIO | klein | **umgesetzt** | 2.2, 2.5 |
| RT k-5 interner Batteriemonitor | klein | **umgesetzt** | 1 |
| RT k-6 Einsetzbarkeit BS-24 im Kopf | klein | **umgesetzt** als CAD-/Prototyppunkt (Spiel 0.5 mm in Kopfrechnung; Prüfung Phase 4) | 2.9 |
| RT k-7 Epson-Fehlerbudget konservativ | klein | **umgesetzt**: Hinweis „konservativ, Offset kalibrierbar“ | 1 |
| RT Kap. 4 Funkmodul statt Chip-down | Anregung | **abgelehnt für v0.2 (zurückgestellt)**: keine Recherche im Auftrag; als Phase-3-Kurzrecherche sinnvoll, wenn die HF-Abstimmung am Prototyp Probleme macht | – |
