# Phase 6 – Fertigungspaket: Zusammenfassung und Prüfbericht (zur Freigabe)

| | |
|---|---|
| Datum | 2026-11-09 |
| Stand | git `108c9af` (main), Release-Paket `production/rev-C` (125 Dateien, `--check`: aktuell) |
| Verfasser | Orchestrator |
| Antrag | Freigabe Phase 6 (Projektabschluss Entwicklung), danach Musterbestellung durch den Auftraggeber |

## 1 Ergebnis in Kürze

- **Release-Paket vollständig** nach Projektauftrag: JLC-Upload (Sensor bytegleich `bf1902ea…`, dazu Dummy-Scheibe),
  Bestellanleitung, Einkaufsliste, Druckdateien + Zeichnungen, Gateway, Firmware (Quellarchiv baubar, DEV-Muster-Hex),
  PWA, alle Anleitungen, Programmieradapter, Renderings, `0_SICHERHEIT.md` mit Sicherheitsdatenblättern.
- **Kein Veto, kein offener kritischer Befund.** Gefunden und behoben wurden u. a. ein kritischer, schon länger
  bestehender Firmwarefehler (IO-Latches nach Shutdown, C-1) und eine Reset-Schleife vor der BLE-Initialisierung.
- **Kosten:** Stückkosten Serie **8.69 CHF** (< 10 CHF erfüllt; 10.91 CHF falls JLC „Pre-reflow“ berechnet →
  Stopp-Kriterium). Bar zu bezahlen (Zubehör vorhanden): **Muster 621.52 CHF**, Serie danach 274.87 CHF, gesamt 896.39 CHF
  (`docs/reviews/phase5_kosten_final.md` Kap. 4a).

## 2 Lieferumfang Phase 6

| Thema | Ergebnis | Datei |
|---|---|---|
| Vergussmasse/Versiegelung | ER2223, Kanten statt Flächen (Simulation), Variante M-A (abfüllen/wägen) | D-030, `docs/concepts/vergussmasse_versiegelung.md`, MONTAGE Kap. 3a |
| Testfirmware | TF-1…TF-4 nach Testplan Anhang A, getrennt von der Serie, Gerätename `fl-tf<n>-…` | `docs/manuals/TESTFIRMWARE.md` |
| Firmware-Korrekturen | HardFault/Assert → sofortiger Neustart; Latch-Freigabe nach Shutdown; Frühstart-Zähler | `firmware/sensor` (make check 1589/1589) |
| Gateway/PWA | ohne RTC (D-028), Status-LED (D-027), Diagnose abrufen, Testfirmware-Sperre, Kalibrierlauf bleibt erhalten | Gateway 114 Tests, App 17 + 63 |
| Einkauf | Einkaufsliste nach Händlern, Muster/Serie getrennt, Zubehör „vorhanden“ | `docs/manuals/EINKAUFSLISTE.md` |
| Klimasensor | DFRobot SHT40 SEN0428, Kammer angepasst (D-029) | `mechanical/gateway_pi` |
| Programmierplatz | PL2303 statt CH343 (D-031), Adapter mit R2, Dummy-Scheibe als JLC-Platine, Variante B2 | `hardware/programmer`, `hardware/dummy_cell`, PROGRAMMIEREN v1.3 |
| Mechanik | Torx-Schraube, Gewindeeinsätze, LED-Fenster (D-032/D-033), Gateway-LED-Rohr, EPDM-O-Ringe, Etikett | `mechanical/`, PRINT_SETTINGS |
| Anleitungen neu | Inbetriebnahme, Pairing/Kalibrierung, Fehlersuche, Testfirmware, Einkaufsliste | `docs/manuals/` |

## 3 Prüfungen (Prüfer ≠ Ersteller)

| Prüfung | Ergebnis |
|---|---|
| Sicherheit Vergussmasse (2 Runden) | kein Veto, Auflagen A-1…A-5, MA-1…MA-6 umgesetzt |
| Sicherheit Schlussprüfung + Dummy-Scheibe + Handschuhe + Schraube | kein Veto; W-1…W-7, DS-B1…B5, HS-1…HS-5, SR-1…SR-4 umgesetzt bzw. im Testplan |
| Elektronik prüft Firmware | **C-1 kritisch** (IO-Latches) → behoben; W-1…W-3, K-1…K-4 umgesetzt |
| Red Team Fertigungspaket | K-1 (Firmware aus Paket nicht baubar) → behoben; W-1…W-8 umgesetzt |
| Orchestrator selbst | make check, Gateway-/App-Tests, Release `--check`, `sha256sum -c`, Quellarchiv nur mit DEV-Schlüssel |

Abgelehnt mit Begründung: Drosselung „Jetzt messen“ (Sicherheit K-4, normale Nutzung); Bambu-Profile in 3MF
einbetten (Mechanik, nicht prüfbar → Anleitung Kap. 2a).

## 4 Entscheide Phase 6

D-027 Gateway-LED · D-028 ohne RTC · D-029 SHT40 SEN0428 · D-030 Vergussmasse ER2223 · D-031 PL2303 ·
D-032 Kaufteile Mechanik (TX6, Einsätze, Filament) · D-033 LED-Fenster · D-034 Schraube verliersicher.

## 5 Was der Auftraggeber tun muss

1. **Bestellreihenfolge** (Einkaufsliste Kap. 1):
   1. **Vergussmasse** zuerst (8 Wochen Lieferzeit). Dabei beim Händler das **Sicherheitsdatenblatt Teil B auf Deutsch**
      anfordern (Textvorlage Konzept Anhang B) – ohne dieses kein Öffnen des Beutels.
   2. **JLC** nach `BESTELLEN_JLC.md`: Sensor-Muster + 25 Batteriehalter in den eigenen Bestand + 2 Dummy-Platinen;
      Stopp-Regeln beachten. Der Batteriehalter-Lagerbestand sinkt täglich.
   3. Rest nach Einkaufsliste (bastelgarage, pi-shop, galaxus, 3djake, LCSC). Filament: **ASA, Farbe frei**, Fenster ASA natur.
2. Anfrage an Electrolube (Tg, Umfüllen; Vorlage Anhang A) – optional, M-B gilt sonst.
3. **Vor der Inbetriebnahme im Geschäft:** WLAN-Vorprüfung nach `GATEWAY_SETUP.md` Kap. 1.1 (Client-Isolation, mDNS).

## 6 Offen (am Muster bzw. für Serie / Rev D)

- PROTOTYP-PRÜFUNGEN laut Testplan, neu u. a.: Latch-Freigabe, Frühstart-Abschaltung, Brownout-Retention (TF-4),
  Dichtheit Verguss (≥ 2 Muster), Kriechprobe V-6, LED-Sichtbarkeit Fenster, Sitz Dummy-Scheibe, Schraube SR-1/SR-2.
- Lieferanten offen: O-Ringe EPDM, Normteile, einige Einwegartikel (ANNAHME-Preise in der Einkaufsliste).
- Serie/Rev D: Taster mit Betätiger in z (C-2), Taillenschaft-Schraube, Tg-Nachweis Vergussmasse.

## 7 Antrag

Freigabe Phase 6. Damit ist die Entwicklung auf dem Papier abgeschlossen; es folgen Bestellung, Musterbau und Mustertest
nach `docs/reviews/phase5_testplan_prototyp.md`.
