# Phase 5 – Testplan-Beitrag Firmware/Energie (Sensor Rev C, Muster)

| | |
|---|---|
| Datum | 2026-11-08 |
| Verfasser | Firmware/Energie |
| Grundlagen | `docs/requirements/REQUIREMENTS.md`, `firmware/PROTOCOL.md` 0.2, `docs/interfaces/PINMAP_SENSOR.md` (FW-1…FW-10), `firmware/sensor/README.md` (PP-1…PP-12), **Energiemessplan `docs/manuals/ENERGIEMESSUNG.md` (E1–E15)**, `docs/reviews/phase5_energiebudget_final.md`, `docs/manuals/PROGRAMMIEREN_SENSOR.md` |
| Muster | 5 Sensoren Rev C (4 × 100 µF), Gateway Pi Zero 2 W, Firmware `fluidi-sensor-0.1.0+1` (DEV-Schlüssel) |
| Ablage der Ergebnisse | `docs/reviews/phase5_energie_messung/` (Oszilloskop-Bilder, CSV), Tabelle je Testfall: Muster-Nr., FW-Stand (`GET_INFO`), Temperatur, Messwerte, OK/NOK |

## 1 Messaufbau

**Rahmen:** Der Auftraggeber hat eine gut ausgerüstete Werkstatt, aber **keine 100 CHF für Messgeräte**
(`docs/requirements/CLIENT_INPUT.md` Nr. 10). Ein Power-Profiler (PPK2, Joulescope) oder µCurrent ist deshalb nicht vorgesehen
und lokal nicht belegt. Gemessen wird mit Shunt + Oszilloskop/DMM. Die Mittel sind in ENERGIEMESSUNG „Werkstattmittel“
aufgeführt; dass sie vorhanden sind, ist eine **ANNAHME**, die der Auftraggeber bestätigen muss.

| Aufbau | Zweck | Kurzbeschreibung (Details ENERGIEMESSUNG Kap. 1) |
|---|---|---|
| A Ereignisform | Ladung je Ereignis, Spitzenstrom | Netzteil 3.0/2.4 V über Dummy-Zellen-Adapter, Shunt 10 Ω, Oszilloskop (Integral) |
| B Zellen-Nachbildung | Einbruch REQ-ENE-06 | Netzteil 2.7–3.0 V + **100 Ω** in Serie, Shunt 1 Ω, Oszilloskop an VDD (C1) |
| C Ruhestrom | E1, E14 | Netzteil 3.0 V, Shunt 1 kΩ mit Kurzschlussbrücke, DMM mV (1 mV = 1 µA) |
| D Tagesmittel | E12 | echte CR2032 im Mess-Zwischenadapter, 10 Ω ∥ 1000 µF, DMM-Aufzeichnung ≥ 24 h |
| E Kondensator-Leck | E14c | 3.0 V, 100 kΩ in Serie, DMM über dem Shunt (1 mV = 10 nA). DMM-Innenwiderstand 10 MΩ → 1 % Fehler (**ANNAHME** Gerätewert) |
| F Funk | T-R1/T-R2 | Gateway am Aufstellort; RSSI und Paketverlust aus dem Gateway-Log; Sendeleistung per `tx_power_dbm` (PROTOCOL Kap. 8, −20…+8 dBm) |

**Sicherheit (Auflage R2-A2, ENERGIEMESSUNG):** Speisung nur über den Dummy-Adapter **ohne** Zelle, Strombegrenzung
≤ 20 mA. Keine Quelle in Serie zu einer echten Zelle, keine Speisung über TP1/TP2 (REQ-ENE-07, REQ-SAF-06).
Ausnahme: Programmieren mit 2.0 V nach D-024.

## 2 Testfälle Energie (aus dem Energiemessplan, mit Abnahmekriterium)

| Nr. | Fall | Aufbau | Abnahmekriterium | Quelle |
|---|---|---|---|---|
| E1 | Ruhestrom ungekoppelt, 3.0 V, 25 °C | C | **≤ 3 µA** (Muss); Erwartung ≤ 1.5 µA (Modell real 1.03 µA) | REQ-ENE-09; `ENERGIE_REV_B.md` Kap. 1 |
| E2 | Taster dauernd gedrückt | C | nach 30 s wieder ≈ E1; Pull-up-Strom notieren | PROTOCOL 10.3 |
| E3 | Advertising-Ereignis | A, B | Ladung (Modell 16.2/40.9 µC); **Einbruch ≤ 0.2 V** bei 100 Ω, mit 4 und 2 × 100 µF | REQ-ENE-06; SPICE 143/246 mV |
| E4 | Datensitzung | A, B | ≤ 12 Verbindungsereignisse; Einbruch ≤ 0.2 V; Ladung ersetzt T_CONN | PROTOCOL 2.5; REQ-ENE-06 |
| E5 | Messung (FW-2) | A, B | Burst ≤ 0.6 ms, ≤ 4 Bursts, Pause ≥ 30 ms; Einbruch ≤ 0.2 V | PINMAP FW-2; PP-2 |
| E6 | LED L1/L3/L8 (FW-4) | A, B | Pulse ≤ 5 ms, Pause ≥ 5 ms; Strom ≤ 3 mA je Farbe; Einbruch ≤ 0.2 V; bei VDD < 2.65 V Gelb statt Blau | PROTOCOL 10.1/10.2; `core/fl_ui.c` |
| E7 | Kopplung | A | ECDH-Rechenzeit ≤ 3 s (ANNAHME PP-6) | PROTOCOL 12 |
| E8 | Schnelles Advertising nach Taste | A | Ladung (Modell 0.32 mC) | PROTOCOL 12 |
| E9 | OTA 200 kB inkl. Swap | A | ≤ 2 % von 225 mAh (= 4.5 mAh) | REQ-FW-05 |
| E10 | Fremdverbindung ohne HELLO, Sperre | A | Sperre greift; Ladung je Versuch | PROTOCOL 4.5 |
| E11 | Unterspannung 2.6 → 2.3 V | B | Abschaltung bei 2.4 V unter Last, sauber gespeichert, kein Reset-Zyklus; Wecken per Taster | REQ-ENE-06; FW-5 |
| E12 | Tagesprofil 24 h | D | Tagesmittel **≤ 8 µA** (Muss) | REQ-ENE-09 |
| E13 | Temperatur 10/25/35 °C (wenn möglich 50 °C) | C, A | Temperaturfaktor ersetzt die Annahme 1.35 | RB-03; `energy_budget.py` |
| **E14** | **Leckstrom C1–C4 (W-6)** | C, E | Entscheidungsregel unten | `phase5_energiebudget_final.md` Kap. 5 |
| **E15** | **Bootloader-Strom (W-10)** | A | Wert dokumentieren; Neustart ohne Taster zeigt L11 | W-10; PROGRAMMIEREN_SENSOR Kap. 6 |

Jede Energiemessung bei 3.0 V und 2.4 V. E3/E5/E6 zusätzlich mit 2 statt 4 × 100 µF an den Mustern aus E14b.

### 2.1 W-6: Leckstrom C1–C4 → 2 oder 4 × 100 µF

1. E14a: E1 an allen 5 Mustern, nach ≥ 1 h an 3.0 V.
2. E14b: An 2 Mustern C3/C4 ablöten, E1 wiederholen. Die Differenz ist das Leck von 2 Kondensatoren.
3. E14c: Die 4 abgelöteten Kondensatoren einzeln in Aufbau E messen, je bei 25 °C und 50 °C. Ablesen nach 1 min, 10 min,
   1 h (Auswertewert) und 24 h.
4. Auswertung: I_eff = (20 · I_25 + 4 · I_50) / 24 je Kondensator (Sonnenprofil RB-03). Massgebend ist das Maximum.

| I_eff (Maximum) | Entscheid |
|---|---|
| ≤ **1.24 µA** | **4 × 100 µF** in Serie |
| 1.24–2.49 µA | 2 × 100 µF nur bei E3/E5/E6 ≤ 0.2 V mit 2 Kondensatoren (Aufbau B), sonst Vorlage an den Auftraggeber |
| > 2.49 µA | Vorlage an den Auftraggeber |

Schwellen aus `ENERGIE_REV_B.md` Kap. 3e (Rest des Budgets an den DS-Grenzen, Messwert × 1.5). **Vorher als D-Eintrag
festhalten:** Der gemessene Wert × 1.5 ersetzt den Katalog-Grenzwert, also die Auslegung von REQ-ENE-08.

### 2.2 W-10: Strom im ROM-Bootloader

E15 bei 3.0 V und 2.0 V: Taster beim Einschalten halten und den Strom über 60 s mitteln. Daraus folgt die Zeit, bis die
Zelle leer ist: pess. 152 mAh / I. Bei der Annahme 0.8–4.1 mA sind das 1.5–8 Tage. Den Wert in PROGRAMMIEREN_SENSOR
Kap. 6 eintragen. Abnahme: Nach ≥ 10 s ohne Speisung startet das Muster ohne Taster mit L11.

## 3 Testfälle Firmware-Funktion

| Nr. | Fall | Vorgehen | Abnahmekriterium | Quelle |
|---|---|---|---|---|
| T-P1 | Erstprogrammierung (Behelf) | Labornetzteil 2.0 V, CH343 an R9 Pad 1, `flash_sensor.py program` | Programmieren + Verifizieren OK; L11 nach Neustart | REQ-FW-06; D-024 |
| T-P2 | Serien-Sperre (1 Muster, zuletzt) | `--lock --expect-key-fp` mit Testschlüssel | Bootloader antwortet nicht mehr, OTA geht weiter | PP-9 |
| T-M1 | Messkette Frequenzbereich | MEAS_CLK an TP4 (÷8) in Luft, Wasser und Salzwasser | MEAS_CLK 0.59–4.51 MHz (f_osc ≈ 4.7–36 MHz) wie SPICE; keine verlorenen Captures | `config/fluidi_board.h` Z. 30; MESSKETTE_SALZ Kap. 5; PP-1 |
| T-M2 | Kalibrierung **trocken** | Sonde sauber und trocken in Luft, 10 Messungen; PWA „Trockenpunkt übernehmen“ | Rohwert nahe Startkalibrierung 13.3 pF (Erde) bzw. 12.5 pF (Granulat), ±15 %-Punkte ohne Einzelkalibrierung; σ ≤ 1 %-Punkt | REQ-MES-02/04/07; `firmware/gateway/fluidi_gw/config.py` Z. 53 |
| T-M3 | Kalibrierung **nass** | Sonde bis zur Dichtlinie in Leitungswasser bzw. gesättigtes Substrat, 10 Messungen; „Nasspunkt übernehmen“ | Rohwert nahe 40.0 pF (Erde) / 36.0 pF (Granulat); Index nach Kalibrierung 100 % ± 1 %-Punkt; Auflösung ≤ 1 % | REQ-MES-02/03/09 |
| T-M4 | Plausibilität | Luft unter dem Trockenpunkt, Überflutung über dem Nasspunkt | Meldung `air` / `flooded` | REQ-MES-12; PROTOCOL 8 (0x0B) |
| T-M5 | Dünger | Leitungswasser vs. Düngerlösung bei gleicher Feuchte | Δ Index ≤ 5 %-Punkte | REQ-MES-11 |
| T-M6 | Temperatur | Substrat im Beutel bei 8/22/35 °C | ≤ 0.3 %-Punkte/K nach Kompensation | REQ-MES-05 |
| T-R1 | Reichweite | 7 Tage, alle Sensoren an ihren Plätzen (RB-01, bis 18 m) | ≥ 99 % der Werte innert 1 h, 100 % innert 24 h | REQ-RF-02 |
| T-R2 | Linkreserve | Am schlechtesten Platz `tx_power_dbm` schrittweise senken (0 → −20 dBm), bis Advertising/Sitzungen ausfallen | Reserve = Betriebsleistung − Ausfallleistung **≥ 10 dB**. Die Methode braucht keinen Empfindlichkeitswert des Pi; dieser fehlt lokal | REQ-RF-03 |
| T-R3 | Reaktionszeit | 20 manuelle Messungen aus der PWA | 95 % ≤ 1 min (Soll), 100 % ≤ 5 min (Muss) → P_MISS bestimmen | REQ-SYS-05; FW-P8 |
| T-R4 | Koexistenz WLAN/BLE | Pi mit WLAN-Last, T-R3 wiederholen | wie T-R3 | W-7 |
| T-K1 | Kopplung | Taster 3–8 s, PWA bestätigt, SAS-Farbfolge vergleichen | Kopplung nur mit beiden Schritten; falsche Farbfolge → Abbruch L7 | REQ-RF-05; PROTOCOL 4.2 |
| T-K2 | Fremdes Gateway / Replay | zweites Gerät verbindet sich; altes Frame erneut senden | abgelehnt, Sperre nach 3 Versuchen | REQ-RF-06; PROTOCOL 4.5 |
| T-O1 | OTA normal | Image +1 über Gateway | neue Version in der PWA, L17 grün | REQ-FW-02/08 |
| T-O2 | OTA abgebrochen | Gateway während der Übertragung und während des Swaps ausschalten | alter Stand läuft weiter bzw. Rückfall; kein unbrauchbarer Sensor | REQ-FW-03; PP-7 |
| T-O3 | OTA unzulässig | falsche Signatur, kleinerer `sec_cnt`, falsches `hw_rev`, VBAT < 2.7 V | jeweils abgelehnt (Fehlercode PROTOCOL 11, 0x4A) | REQ-FW-02/04; PP-12 |
| T-U1 | LED-Muster | alle Muster L1–L17 auslösen, aus 1 m schräg von oben betrachten | Farben und Zeiten nach PROTOCOL 10.2; erkennbar | REQ-UI-02/05; E6 |
| T-U2 | Taster | kurz / 3 s / 10 s + Bestätigung; 10 s ohne Bestätigung; Wasser auf den Taster | Aktionen nach PROTOCOL 10.3; keine Werkseinstellung ohne „lang–loslassen–kurz“ | REQ-UI-04/06 |
| T-Z1 | Zeit ohne Gateway | Gateway 14 Tage aus, dann wieder ein | Zeitstempelfehler ≤ ±2 min (60 Tage ≤ ±5 min, Stichprobe) | REQ-SYS-07 |
| T-Z2 | Pufferung | Gateway 7 Tage aus | alle Datensätze lückenlos nachgeliefert (Sequenznummern) | REQ-LOG; PROTOCOL 6 |
| T-W1 | Watchdog | Debug-Build mit Endlosschleife (nur Entwicklung; ein Testbefehl im Protokoll ist nicht vorgesehen) | Neustart, Grund in GET_DIAG | REQ-FW-07 |

## 4 Reihenfolge

1. T-P1 an allen Mustern, dann E1/E14a (Ruhestrom zuerst, Platinen noch sauber).
2. E14b/E14c an 2 Mustern, danach mit diesen E3/E5/E6 mit 2 × 100 µF → **Entscheid W-6**.
3. E15 (W-10).
4. Danach E3–E13 an einem Muster mit 4 × 100 µF und T-M/T-K/T-O/T-U.
5. T-R/T-Z am Aufstellort (≥ 7 bzw. 14 Tage), parallel zum 30-Tage-Wassertest (REQ-MES-06).
6. Messwerte in `scripts/energy_budget.py` eintragen (`rb.*`, `ble.t_cpu`, `prof.t_conn`), `--revb --out` neu erzeugen und
   von einem anderen Agenten nachrechnen lassen.
