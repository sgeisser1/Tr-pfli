# Phase 4 – Zusammenfassung und Prüfbericht (zur Freigabe)

| | |
|---|---|
| Datum | 2026-11-08 |
| Stand | git `6b4cbea` (main) |
| Verfasser | Orchestrator |
| Antrag | Freigabe Phase 4, Start Phase 5 (Verifikation und Review) |

## 1 Ergebnis in Kürze

- **Sensor Rev C ist bestellfertig.** Schaltplan, 4-Lagen-Layout, Gerber, BOM, CPL und STEP liegen vor.
  Die Bestellunterlage mit Checklisten ist `hardware/sensor/out/ORDER_JLC_REV_C.md`.
- **Kostenziel erfüllt** (JLC-Angebot vom 2026-11-08): Serie **8.38 CHF** pro Sensor (Ziel < 10 CHF),
  Prototyp-Los 9.23 CHF. Mit Einmalkosten sind es 17.83 bzw. 37.08 CHF. Die Verzollung DHL (23.54 CHF pro Sendung) ist eingerechnet.
- **Kein kritischer Befund offen, kein Veto.** Red-Team-Urteil: „bestellen nach B-1 bis B-4“.
  B-1 und B-4 sind erledigt. B-2 und B-3 lassen sich nur im JLC-Formular erledigen (Kap. 5).
- Gehäuse, Firmware, Gateway, PWA und finale Renderings liegen vor.

## 2 Lieferumfang Phase 4

| Bereich | Ergebnis | Nachweis |
|---|---|---|
| Schaltplan Sensor Rev B/C | Messkette D3 (D-018), TMP1075N im Kragen, Verpolschutz | ERC 0 Fehler, 1 Warnung (pin_to_pin DIO12 ↔ PWR_FLAG, unkritisch) |
| Layout Rev C | 4 Lagen, ENIG, POFV, 8 Via-in-Pad (D-023), Fach 24.2 mm, Regeln K-1..K-3, LS-K1/K2 als DRC | DRC 0/0/0 in WSL (mit und ohne Neufüllung), Windows 0 Fehler (4 Warnungen lib_footprint_mismatch), Parität 0 |
| Fertigungsdaten | Gerber-ZIP, BOM, CPL, sha256 in ORDER Rev C | `order_check.py` (inkl. `--live` Lager) |
| Feldsimulation | Layout Rev B/C: Spanne 23.03 → 22.99 pF (−0.2 %), keine Layoutänderung | `simulation/field/REPORT.md` Kap. 11 |
| FEM Sonde/Kopf | LC1 SF 2.31, LC1b SF 1.97, LC6 238 N, Fall 1 m SF 1.71 | `simulation/fem/REPORT.md` Kap. 5 |
| Gehäuse Sensor V4 / Gateway G1 v4 | STEP/3MF für P1S, Kollision mit Platinen-STEP: keine | `mechanical/sensor/collision_pcb_step.txt` |
| Firmware Sensor | BLE-Protokoll v2, Messung, Ringpuffer, LED (FW-4), MCUboot signiert | 1542 Prüfungen bestanden |
| Gateway + PWA | Pi Zero 2 W, BLE, SQLite, HTTPS, SSE, OTA, Klimasensor; PWA „Frost“ | 62 + 11 + 24 Tests bestanden |
| Energie | Typ. 10.8 a, pessA 34.6 Mt.; pessDS (4 × 100 µF) 9.1 Mt. → Messung am Muster (W-6) | `hardware/sensor/out/ENERGIE_REV_B.md` |
| Erstprogrammierung | Adapter Rev 1 (2.0 V, SN74AUP1G17-Puffer), Behelf für Muster, Anleitung (D-024) | SPICE `simulation/spice/programmer/`, Programmer-ERC 0, Flash-Tests 17 OK |
| Renderings | 6 finale Bilder aus CAD Rev C + KiCad-STEP | `renders/final/`, Skripte in `renders/final/scripts/` |

## 3 Prüfungen (Prüfer ≠ Ersteller)

| Bericht | Prüfer | Ergebnis |
|---|---|---|
| `phase4_sicherheit_kragen_firmware.md` | Sicherheit | VETO F-K1 (Kopplung ohne Commitment) → mit Protokoll v2 aufgehoben (Runde 2) |
| `phase4_protocol_software.md` | Software | Protokoll v2 byte-gleich mit Referenzvektoren |
| `phase4_firmware_response.md` | Firmware | Antworten auf alle Befunde |
| `phase4_layout_revb_sicherheit.md` | Sicherheit | kein Veto; L-1 Via-in-Pad mit Auflagen A-1..A-5 (D-023) |
| `phase4_energie_pins_revb_firmware.md` | Firmware-Energie | Pins korrekt; LED-Pulse FW-4 und Pull-up-Strom umgesetzt |
| `phase4_layout_revb_dfm.md` | Fertigung/DFM | fertigbar; POFV in Kosten, Bestellentwurf |
| `phase4_kollision_mechanik.md` | Mechanik | keine Kollision; Platinenanschlag, Clip nach Datenblatt |
| `phase4_redteam_gesamt.md` | Red Team | keine kritischen Befunde; bestellen nach B-1..B-4 |

Gegenprüfungen durch den Orchestrator: DRC/ERC neu gelaufen, sha256 der Bestellunterlage, Kostenformel,
Flash-Tests, SPICE des Programmieradapters reproduziert, Renderings gesichtet.

## 4 Entscheide Phase 4

D-017 (Raumklima im Gateway) bis D-024 (Erstprogrammierung), siehe `docs/requirements/DECISIONS.md`.
Neu seit der letzten Freigabe: **D-023** (Via-in-Pad mit Auflagen, Fach +0.7 mm, Taster M-4, LED EP-2) und
**D-024** (Programmieradapter 2.0 V mit Puffer; Behelf Labornetzteil + Draht an R9 Pad 1).

## 5 Was der Auftraggeber tun muss

1. **Beim Bestellen im JLC-Formular** (ORDER_JLC_REV_C.md Kap. 2/3):
   - **B-2:** Prüfen, ob Economic PCBA mit ENIG + POFV angeboten wird. Falls nicht: melden, Kosten mit Standard-PCBA werden neu gerechnet.
   - **B-3:** In „Confirm Parts Placement“ Lage/Pin 1 von U1, U2, U3, U4–U6, Q1, Q2, D1, Y1, BT1 einzeln abhaken.
   - Lager BT1 (C5213768) ist knapp (629 Stk am 2026-11-08) – nicht lange warten.
2. **Für die Erstprogrammierung:** CH343-Adapter (Waveshare) und Labornetzteil 2.0 V bereithalten
   (Behelf nach `docs/manuals/PROGRAMMIEREN_SENSOR.md`); Adapter Rev 1 ca. 25–55 CHF.
3. **Später:** WLAN/BLE-Koexistenztest am Pi (W-7).

## 6 Offen für Phase 5 bzw. am Muster

**Dokumente/Prüfungen Phase 5:** Design-Review-Checkliste (alle Fachbereiche), FMEA-light, Testplan Prototyp,
Montage-, Verguss- und Batteriewechselanleitung, finales Energiebudget, Kosten- und Risikoanalyse,
`production/rev-C`, Sicherheitsprüfung Programmieradapter, Mechanik Federstiftkopf, Gateway RTC/BOM/Kosten (W-8),
Untersuchung `osc_sim.py`-Hänger (ngspice, Bericht steht noch auf 10.5 pF; die Werte für 9.9 pF stehen im Feld-REPORT 11.3),
PINMAP-Text „1.8-V-UART“ nachführen.

**PROTOTYP-PRÜFUNG:**
- Leckstrom C1–C4 → Entscheid 2 oder 4 × 100 µF (W-6, REQ-ENE-02 im pessDS-Fall)
- Tastertoleranz (Worst Case −0.20 mm)
- Bootloader-Strom (W-10)
- LED-Sichtbarkeit (E6)
- Koexistenz WLAN/BLE (W-7)
- Frequenzbereich Messkette 4.8–36 MHz am realen Board

**Bekannte Grenzen der Renderings:** Platine ohne Silkscreen (STEP enthält keinen), LED D1 und CR2032 als Platzhalter,
LED-Leuchtpunkt stilisiert.

## 7 Antrag

Freigabe von Phase 4 und Start von Phase 5. Die Musterbestellung kann parallel zu Phase 5 erfolgen
(Fertigung und Versand dauern, Phase 5 braucht die Platinen erst für den Testplan).
