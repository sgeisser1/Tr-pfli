# Phase 5 – Risikoanalyse Projekt fluidi

| | |
|---|---|
| Verfasser | Sicherheits-Agent (Beitrag zur Projektrisikoanalyse; Projektleitung ergänzt Termine) |
| Datum | 2026-11-08, Stand git `b77b29a` |
| Grundlage | `phase4_redteam_gesamt.md`, `phase4_zusammenfassung.md`, `hardware/sensor/out/ORDER_JLC_REV_C.md`, `DECISIONS.md`, `CLIENT_INPUT.md`, `phase5_fmea_light.md`, `phase5_programmer_sicherheit.md` |

**Skalen:** Wahrscheinlichkeit **W** 1 (sehr unwahrscheinlich) … 5 (fast sicher); Auswirkung **A** 1 (vernachlässigbar)
… 5 (Projektziel verfehlt: Sicherheit, < 10 CHF oder Funktion). **Risiko = W × A**: ≥ 12 hoch, 6–11 mittel, ≤ 5 tief.
Die Werte sind Einschätzungen (**ANNAHME**).

## 1 Lieferkette und Fertigung

| Nr | Risiko | W | A | R | Gegenmassnahme | Verantwortlich |
|---|---|---|---|---|---|---|
| R-01 | **BT1 Keystone 3034 (C5213768, Extended) geht aus:** Lager 629 Stk am 2026-11-08, Vortag 654 (`ORDER_JLC_REV_C.md` Kap. 7). Der Halter ist mechanisch festgelegt (Fach 24.2 mm, Pad-Spanne 23.10, D-023). Ein Ersatz erzwingt Layout, Mechanik und eine neue Sicherheitsprüfung (Clip-Kurzschluss R2-W01) | 3 | 4 | **12** | Prototyp bald bestellen; den Bedarf der Serie (16 + 4 Reserve) gleich mit dem Prototyp als „Parts pre-order“ bzw. privaten Bestand sichern (Red-Team K-5); Bestand am Bestelltag prüfen (`order_check.py --live`); einen zweiten Halter mit Datenblatt nur vormerken (nicht ungeprüft tauschen) | AG/FE |
| R-02 | **Rotationen nur aus Drittquelle** (JLCKicadTools, für D1, BT1, Y1, L1, SW1 keine Regel). Ein Fehler bei U1 macht alle 5 Platinen unbrauchbar; bei U3 werden V+ und GND vertauscht, bei Q1 fehlt der Verpolschutz (FMEA F-03/F-64) | 3 | 4 | **12** | Abhakliste B-3 mit Screenshot je Teil; Eingangsprüfung mit Strombegrenzung 3.0 V / 10 mA vor der ersten Zelle (ST-E2); bei Zweifel JLC-Support vor der Freigabe der Bestückung fragen | AG/FE |
| R-03 | **Economic PCBA mit ENIG + POFV nicht belegt** (W-2). Fehlt die Kombination, gilt Standard-PCBA (Setup, Nutzen) und das Kostenmodell stimmt nicht mehr. Ohne POFV wird nicht bestellt (A-2) | 3 | 3 | 9 | Checkliste Nr. 4/5 in `ORDER_JLC_REV_C.md`; POFV hat Vorrang; Standard-PCBA mit `cost_rev_b.py` nachrechnen und vorlegen. Mehrkosten überwiegend einmalig (ANNAHME) | AG/FE |
| R-04 | POFV-Qualität (Lunker, Delle) im Fach | 2 | 4 | 8 | A-3 Sichtprüfung und Querschliff an einer Opferplatine | FE/SI |
| R-05 | Teile für den Adapter gering an Lager: XC6206P202 C2891260 (1963), SN74AUP1G17 C183012 (1280) (`hardware/programmer/README.md` 2.1) | 2 | 2 | 4 | Mit Reserve bestellen (2–5 Adapter) | EL |
| R-06 | Waveshare CH343 mit Versand in die Schweiz nicht bestätigt (PA-5/FW-T3) | 3 | 3 | 9 | Jetzt bestellen; Alternative mit VIO-Pin und Datenblatt vormerken | AG |
| R-07 | Zoll, Versand, Lieferzeit (DHL 23.54 CHF je Sendung eingerechnet, Phase-4-Zusammenfassung) | 3 | 2 | 6 | Termine mit 2–3 Wochen Puffer planen | PL |

## 2 Technik

| Nr | Risiko | W | A | R | Gegenmassnahme | Verantwortlich |
|---|---|---|---|---|---|---|
| R-10 | **Laufzeit Serie nicht nachgewiesen** (pessDS 9.1 Mt. mit 4 × 100 µF; 2 × 100 µF verfehlt REQ-ENE-06), W-6 | 3 | 4 | **12** | Leckmessung C1–C4 bei 3.0 V/45 °C am Muster; Alternativen (3 × 100 µF, TX −4 dBm, Intervall); Entscheid Auftraggeber pessA vs. pessDS | EL/AG |
| R-11 | **Dichtigkeit (Spritzwasser, Flutung, Kragen) am Muster nicht bestanden** → Gehäuseänderung | 3 | 4 | **12** | Tests früh und zuerst an einem Opfermuster; Vergussmasse mit Datenblatt (W-5); Rückfallebene U3 ins Band (K-Teil) | ME |
| R-12 | **Erstprogrammierung scheitert** (Pegel, Timing, Bootloader-Trigger) bzw. Weg B durch Veto PS-K1 blockiert | 3 | 4 | **12** | Dummy-Scheibe sofort bauen (hebt PS-K1 auf und dient Weg A); Weg B testen, sobald die Platinen da sind; 19200 Baud als Rückfall; SWD-Pads für Rev D vormerken | EL/PL |
| R-13 | Vergussmasse und Kantenversiegelung nicht gewählt (W-5, REQ-MECH-07) | 4 | 3 | **12** | Auswahl mit Datenblatt nach `docs/references/` bis zur Lieferung; Montageanleitung | ME |
| R-14 | BLE/WLAN-Koexistenz Pi Zero 2 W (W-7) → verpasste Advertisings, kürzeres Intervall nötig, mehr Energie | 3 | 3 | 9 | 24-h-Test mit XIAO als Sender; XIAO nRF52840 als USB-Empfänger einplanen | GW/AG |
| R-15 | Bootloader-Falle bei Mustern (W-10) → tote Muster, ungültige Langzeittests | 3 | 3 | 9 | L11-Kontrolle; Strommessung; Option Trigger-Pin (PS-W5) | FW |
| R-16 | Taster-Toleranz (M-4) → klemmender Taster, Weckschleife bzw. Bootloader | 3 | 3 | 9 | Toleranzprüfung am Muster, Hub 0.8 mm | ME |
| R-17 | Firmware-Reserven: Slot 0 90 %, RAM 3.2 kB frei (K-7 Red-Team) → spätere OTA passt nicht | 3 | 3 | 9 | FW-O1 vor dem ersten Muster-Flash | FW |
| R-18 | Gateway-RTC: Breakout mit Ladepfad zur Pufferzelle (FMEA F-45) bzw. RTC fehlt (W-8, REQ-GW-09) | 2 | 4 | 8 | Kandidat Adafruit 4282 ohne Ladepfad (Schema von Sicherheit geprüft, FMEA F-45); Typ in der Gateway-Stückliste festschreiben, keine Nachbauten | GW/SI |
| R-19 | Startkalibrierung 13.3/40 pF und Frequenzbereich 4.8–36 MHz nur simuliert | 3 | 2 | 6 | Becherversuch am Muster (OP-K3) | EL |
| R-20 | FR4-Wasseraufnahme (+0.7/+3.4 pF) → Drift im 30-Tage-Test | 3 | 3 | 9 | 30-Tage-Test, Versiegelung | EL/ME |
| R-21 | Antennenabgleich ohne VNA (K-9) | 3 | 2 | 6 | RSSI-Abgleich mit 0 Ω und 2–3 Werten | EL |
| R-22 | Werkzeug: KiCad 11 entfernt `pcbnew`-SWIG | 2 | 2 | 4 | Projekt bleibt auf KiCad 10 (D-002) | PL |

## 3 Kosten

| Nr | Risiko | W | A | R | Gegenmassnahme | Verantwortlich |
|---|---|---|---|---|---|---|
| R-30 | Stückkosten Serie > 10 CHF (heute 8.38 CHF; Treiber: Standard-PCBA statt Economic, Halterersatz, Wechselkurs) | 2 | 4 | 8 | R-01/R-03 entschärfen; Kostenmodell bei jeder Änderung neu rechnen | FE |
| R-31 | Vollkosten (Serie 17.83 CHF/Sensor inkl. Einmalkosten) werden mit Stückkosten verwechselt (K-3) | 2 | 2 | 4 | Beide Zahlen nebeneinander zeigen | PL |
| R-32 | Zusätzliche Muster-Iteration (Rev D) nach Testbefunden | 3 | 3 | 9 | Tests mit hohem Änderungsrisiko zuerst (Dichtigkeit, Programmierung, Strom) | PL |

## 4 Termine und Organisation

| Nr | Risiko | W | A | R | Gegenmassnahme | Verantwortlich |
|---|---|---|---|---|---|---|
| R-40 | Muss-Dokumente fehlen bei Lieferung: Testplan, Montage/Verguss, Batteriewechsel- und Sicherheitsanleitung, `production/rev-C` (W-5, REQ-DOC-01…03, REQ-SAF-DOC-01) | 4 | 3 | **12** | In Phase 5 vor Ankunft der Platinen fertigstellen; Muster erst danach an Dritte geben | PL |
| R-41 | Externe Antworten offen: Panasonic/Renata zu Ladegrenze und 65 °C (OP-K7) | 3 | 2 | 6 | Bis dahin gilt die strengere Maxell-Grenze 10 mA / 1 % C | AG |
| R-42 | Freigaben durch einen einzigen Auftraggeber → Wartezeiten | 2 | 2 | 4 | Entscheidvorlagen gebündelt pro Phase | PL |

## 5 Hohe Risiken (≥ 12) – Reihenfolge

1. **R-01** Halter BT1 sichern (Serienbedarf mitbestellen).
2. **R-02** Rotationen abhaken und Eingangsprüfung mit Strombegrenzung.
3. **R-12** Dummy-Scheibe bauen (hebt das Veto PS-K1 auf).
4. **R-13 / R-11** Vergussmasse wählen, Dichtigkeitstests früh.
5. **R-40** Anleitungen und Testplan vor der Musternutzung.
6. **R-10** Leckmessung C1–C4.
