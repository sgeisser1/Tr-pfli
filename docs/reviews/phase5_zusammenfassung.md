# Phase 5 – Verifikation und Review: Zusammenfassung und Prüfbericht (zur Freigabe)

| | |
|---|---|
| Datum | 2026-11-08 |
| Stand | git `7f1bf66` (main), Release-Paket `production/rev-C` (Stand `16a1c84`, `--check`: aktuell) |
| Verfasser | Orchestrator |
| Antrag | Freigabe Phase 5; Entscheide Kap. 5; Musterbestellung |

## 1 Ergebnis in Kürze

- **Platine Rev C bestellfertig, final:** Platzhalter `JLCJLCJLCJLC` entfernt (JLC verlangt das seit Mai 2026), sonst
  geometrisch identisch (Gerber-Geometrievergleich, DRC 0, Parität 0, BOM/CPL bytegleich). Gerber-ZIP `bf1902ea…`.
  Bestellanleitung Feld für Feld: `docs/manuals/BESTELLEN_JLC.md`.
- **Kein kritischer Befund offen für den Musterbau, kein Veto.** Ein Veto (PS-K1, Programmier-Behelf) wurde gezogen und
  nach Textänderung aufgehoben. Ein Befund (C-2 Tastenüberlast) bleibt **offen für die Serie** (D-026).
- Beim Zeichnen und Prüfen wurden **vier echte Konstruktionsfehler** im freigegebenen Gehäuse gefunden und behoben
  (Kappe aus 2 Körpern, Leck an der Membran, Taste hätte SW1 nicht ausgelöst, Stössel verdrehbar).
- Kosten: Sensor Serie **8.38 CHF** Stückkosten (10.60 CHF falls JLC „Pre-reflow Soldering“ berechnet → Stopp-Kriterium),
  Vollkosten 17.84 CHF; System 15 Sensoren + Gateway 349 CHF (direkt Serie) bzw. 535 CHF (mit Prototyp-Los).

## 2 Lieferumfang Phase 5 (Projektauftrag)

| Auftrag | Ergebnis | Datei |
|---|---|---|
| Design-Review-Checklisten | Elektronik, Mechanik, Firmware/Energie, Fertigung, Sicherheit, Software | `docs/reviews/phase5_checkliste_*.md` |
| Finales Energiebudget | typ 129.5 Mt., pessA 34.6 Mt., pessDS 9.1 Mt. (4 × 100 µF) → Entscheid W-6 am Muster (E14) mit Regel | `docs/reviews/phase5_energiebudget_final.md` |
| Kostenrechnung | Sensor, Gateway (Status je Teil), System; reproduzierbar | `docs/reviews/phase5_kosten_final.md` |
| Risikoanalyse, FMEA-light | 28 Risiken; FMEA mit S/O/D, RPZ, Massnahmen | `phase5_risikoanalyse.md`, `phase5_fmea_light.md` |
| Testplan Prototyp | 137 Tests, Musterzuteilung S1–S5, Entscheidungstests D-1…D-8, Entscheide EP-01…18, Testfirmware-Spezifikation | `docs/reviews/phase5_testplan_prototyp.md` |
| Fertigungszeichnungen | 14 Blätter (Sensor FL-S-00…10, Gateway FL-G-01…03), alle Masse aus dem Modell, 178 automatische Prüfungen; Masszeichnung Platine (3 Blätter) | `mechanical/drawings/`, `hardware/sensor/out/pdf/fluidi_sensor_masszeichnung.pdf` |
| Anleitungen | Montage/Verguss, Batteriewechsel (Endnutzer), Programmieren v1.1, Bestellen | `docs/manuals/` |
| Release-Paket | Upload-Dateien, Bestellung, Druckdateien, Gateway, Firmware-Hinweis, sha256 | `production/rev-C/` |
| Platinenansichten | 3D-Renderings der Platine | `renders/pcb/` |

Weitere Ergebnisse: osc_sim-Hänger behoben (Zeitlimit + Rückfall, 390 Fälle, 4.76–36.44 MHz = Feld-REPORT);
Gateway-Zeit vereinheitlicht und Handyzeit plausibilisiert (70 Gateway-Tests); Antennenabstand 0.70 mm bestätigt
(≈ −0.2 MHz); Gateway-LED-Vorschlag.

## 3 Prüfungen (Prüfer ≠ Ersteller, max. 3 Runden)

| Prüfung | Prüfer | Ergebnis |
|---|---|---|
| Programmieradapter | Sicherheit | **Veto PS-K1** (Zelle parallel zum Netzteil möglich) → Behelf nur mit Dummy-Scheibe, feste Abbaureihenfolge → **aufgehoben** (Runde 2) |
| Anleitungen, Federstiftkopf, Kappe, Gateway-RTC | Sicherheit Runde 3 | kein Veto; R3-W1…W4 umgesetzt bzw. als Druckvorgabe; Federstiftkopf unter Auflagen A1–A5, Weg A bis Test ST-P1 gesperrt |
| Bestellung, Kosten, Release | Red Team | 0 kritisch; W-1…W-5, K-1…K-7 umgesetzt (Drehregel, Stopp-Kriterien, `--check`, Platzhalter) |
| Mechanik-Änderungen | Red Team, 3 Runden | Runde 1: 2 kritisch (Stössel verdrehbar, Zungenüberlast); Runde 3: **Muster drucken ja, mit Auflagen**; C-2 offen für Serie (D-026) |
| Antennenabstand | Elektronik | zulässig, Feldrechnung `simulation/field/ant_kappe_p5.py` |

Gegenprüfung durch den Orchestrator: Körperzählung alt/neu, Gerber-Geometrievergleich, DRC/ERC, sha256, Energiebudget
reproduziert, Gateway-/App-Tests (70 + 11 + 24 + 36), Release `--check` (Fehler im Prüfskript selbst behoben).

## 4 Entscheide Phase 5

- **D-025** (Freigabe Auftraggeber ausstehend): Abschaltschwelle für den Test 2.4 V statt 2.0 V (REQ-ENE-06 war
  ANNAHME vor Chipwahl); Leckgrenze REQ-ENE-08 = gemessener Höchstwert × 1.5.
- **D-026:** Tastermechanik Rev C für die Muster mit Auflagen (Tastenkraft vor dem Verguss messen, Membran zusätzlich
  abdichten, 50-N-/Falltest); für Rev D Taster mit Betätiger in z.
- Projektleitung: Platzhalter aus dem Layout entfernt (W-4); Testplan-Widersprüche EP-01…EP-18.

## 5 Was der Auftraggeber entscheiden bzw. tun muss

**Entscheide:**
1. **D-005 bestätigen:** Das Ziel „< 10 CHF/Sensor“ gilt für die Stückkosten (ohne Einmalkosten).
2. **D-025** freigeben (Kap. 4).
3. **RTC im Gateway** ja/nein (Adafruit 4282 DS3231, ohne Buchsenleiste in den Deckel geklebt). Ohne RTC: nach
   Stromausfall ohne Internet keine gültige Zeit, bis die App geöffnet wird; Werte werden nachträglich korrigiert.
   Empfehlung Software: RTC für die Serie, Muster ohne.
4. **Klimasensor im Gateway:** Grove SHT41 (20 × 40 mm) passt nicht in die Kammer. (a) aussen am Kabel, (b) Gateway
   grösser (≈ 97 × 46 × 20 mm), (c) kleineres SHT4x-Breakout (Quelle noch zu suchen).
5. **Gateway-LED:** Funktion (Vorschlag: Blitz alle 5 s = ok, schnelles Blinken = Kopplung, aus = Fehler/Nacht) und
   Umsetzung als 3-mm-LED an GPIO17 ohne Platine (0.29 CHF).

**Tun:**
6. **Muster bestellen** nach `docs/manuals/BESTELLEN_JLC.md` (Stopp-Regeln beachten; Lager BT1 knapp).
7. **Messmittel bestätigen** (Testplan Kap. „Messmittel“): Labornetzteil, DMM, Oszilloskop, Thermometer ±0.3 °C,
   Ofen 50/65 °C, Tiefkühler; zu beschaffen: CH343-Board, ≈ 30 CR2032.
8. Später: WLAN/BLE-Koexistenztest am Pi (W-7).

## 6 Offen (Phase 6 bzw. am Muster)

- **Vergussmasse** und Sondenversiegelung nicht gewählt (O-1, kein Datenblatt) – vor dem ersten Verguss nötig.
- Federstift-Datenblatt fehlt (Programmieradapter Weg A); Behelf Weg B genügt für die Muster.
- Testfirmware nach Testplan Anhang A erstellen (vor Musterankunft).
- microSD Industrial nicht an Lager (Gateway); CR1220-Datenblatt.
- PROTOTYP-PRÜFUNGEN: W-6 Leckstrom (E14), W-10 Bootloader-Strom (E15), Tastenkraft/Überlast (M-T2, C-2), Dichtheit,
  LED-Sichtbarkeit, Reichweite/Linkreserve, Koexistenz.
- Rev D (nach Mustertest): Taster mit Betätiger in z, Zapfenwand ≥ 0.8 mm.

## 7 Antrag

Freigabe Phase 5, Entscheide Kap. 5 (1–5) und Freigabe der Musterbestellung. Phase 6 beginnt nach Freigabe und übernimmt die offenen Punkte aus Kap. 6.
