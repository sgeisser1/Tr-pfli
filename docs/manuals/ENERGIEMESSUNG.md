# fluidi – Energiemessplan Sensor-Prototyp (Rev B)

| | |
|---|---|
| Stand | 2026-11-07, Firmware/Energie, Entwurf |
| Zweck | Modellwerte aus `scripts/energy_budget.py` / `firmware/PROTOCOL.md` Kap. 12 am Muster ersetzen (REQ-ENE-01…08, OP-K6, FW-P3), Firmware-Regeln FW-2/FW-4/FW-5/FW-8 aus `docs/interfaces/PINMAP_SENSOR.md` nachweisen |
| Werkstattmittel | Labornetzteil (0–5 V, Strombegrenzung), Oszilloskop ≥ 2 Kanaele (≥ 20 MHz, Mittelwert-/Integralfunktion), Shunts 1 Ω / 10 Ω / 1 kΩ (0.1–1 %, Metallfilm), Digitalmultimeter mit µA-Bereich und Aufzeichnung, CR2032 (frisch und teilentladen), Widerstand 100 Ω (Zell-Innenwiderstand EOL, REQ-ENE-06) |
| Firmware | Build `firmware/sensor` (Rev B), Zaehler aus `GET_INFO` (meas/adv/conn/led_ms, charge_uc) zur Gegenprobe |

**Sicherheit (CONCEPTS 2.7, Auflage R2-A2):** Strommessung nur ueber den **Mess-Zwischenadapter im Zellhalter
(nur Amperemeter/Shunt, keine Quelle in Serie zur Zelle)**. Speisung aus dem Labornetzteil nur ueber den
Dummy-Zellen-Adapter **ohne** Zelle. Strombegrenzung des Netzteils ≤ 20 mA. Keine Speisung ueber TP1/TP2.

## 1 Messaufbauten

| Aufbau | Quelle | Shunt (Lage: Minuspol Zelle → Adapter) | Messgeraet | Wofuer |
|---|---|---|---|---|
| **A Ereignisform** | Netzteil 3.0 V (bzw. 2.7/2.4 V) ueber Dummy-Adapter | **10 Ω** (13 mA → 130 mV; Netzteil um den Spannungsabfall hoeher einstellen oder Fernfuehlung an Adapter) | Oszilloskop Kanal 1 am Shunt (DC, 10–50 mV/Div), Kanal 2 an VDD (Testpunkt C1), Trigger auf Kanal 1 | Ladung je Ereignis (Integral), Dauer, Spitzenstrom |
| **B Zellen-Nachbildung** | Netzteil 3.0 V **+ 100 Ω in Serie** (R_int EOL) | 1 Ω (Spannungsabfall vernachlaessigbar) | Oszilloskop: VDD-Einbruch an C1 | REQ-ENE-06 ≤ 0.2 V, FW-2 (Burst), Advertising/Verbindung, 4 × 100 µF (D-013) |
| **C Ruhestrom** | Netzteil 3.0 V | **1 kΩ** (1 µA → 1 mV) mit **Kurzschlussbruecke**, die waehrend Start/Ereignissen geschlossen ist | DMM (mV) bzw. Oszilloskop mit 20-MHz-Bandbegrenzung und Mittelung | Standby-Strom zwischen Ereignissen |
| **D Mittelwert** | echte CR2032 im Mess-Zwischenadapter | 10 Ω parallel 1000 µF (Tiefpass τ = 10 s) | DMM mV-Bereich mit Aufzeichnung ≥ 24 h, Mittelwert | Tagesmittel im Standardprofil |

Auswertung Aufbau A: Q = (1/R_S) · ∫ U_S dt ueber das Ereignis (Oszilloskop-Mathematik „Area“ bzw. Mittelwert × Fensterbreite),
Grundlinie (Ruhestrom) abziehen. Mindestens 10 Ereignisse mitteln, Streuung angeben.
Aufbau D: I_mittel = U_mittel / 10 Ω; Tiefpass glaettet Pulse, der Kondensator muss vor Beginn ≥ 5 τ eingeschwungen sein.
Gegenprobe: `charge_uc` aus `GET_INFO` zu Beginn/Ende vs. gemessene Ladung (Abweichung > 30 % → Konstanten
`Q_ADV_UC`, `Q_CONN_UC`, `Q_MEAS_UC`, `I_SLEEP_NA` in `firmware/sensor/core/fl_app.c` anpassen).

## 2 Messfaelle

| Nr | Fall (Firmware-Zustand) | Aufbau | Erwartung (Modell, Quelle) | Kriterium / Ergebnis traegt in |
|---|---|---|---|---|
| E1 | Ruhestrom ungekoppelt (kein Advertising, LEDs aus, FW-8) bei 3.0 V und 25 °C | C | 0.74 µA Standby LFXT DCDC (`TI_CC2340R5_Datasheet_SWRS272F.pdf` S.19 Tab. 7.9) + Leck ≈ 0.2 µA (ANNAHME `energy_budget.py` oth.real) | ≤ 1.5 µA; > 10 µA → Pin-Zustand pruefen (SWD-Pull an DIO16 ≈ 66 µA, PINMAP FW-6) |
| E2 | wie E1, Taster dauernd gedrueckt > 30 s | C | vor Abschaltung 39–109 µA (DS S.31), danach Pull-up aus | nach 30 s wieder ≈ E1 (PROTOCOL 10.3) |
| E3 | Advertising-Ereignis (gekoppelt, 27.5 s, 0 dBm) | A, B | 16.2 µC real / 40.9 µC pess (`energy_budget.py` `adv_event_charge`) | Ladung; VDD-Einbruch an B ≤ 0.2 V (REQ-ENE-06) |
| E4 | Datensitzung (HELLO, TIME_SET, READ 1–2 Datensaetze, ACK, Trennen) | A, B | 299 µC real / 767 µC pess (`conn_charge`, 50 ms ANNAHME) | Dauer und Ladung → `T_CONN`; Anzahl Verbindungsereignisse ≤ 12 (PROTOCOL 2.5) |
| E5 | Messung (Taster kurz, gekoppelt ohne Gateway) | A, B | 4 Bursts × 0.6 ms × 12.8 mA ≈ 31 µC + TMP-Wandlung/I²C ≈ 10–20 µC (README Kap. 4; PINMAP FW-2) | **Burst ≤ 0.6 ms, Pause ≥ 30 ms, max. 4** (Kanal 2 an DIO11 statt VDD); Einbruch an B ≤ 0.2 V; ersetzt `Q_MEAS` |
| E6 | LED-Muster L8 (Giessen, 5 ms), L1 (2 × 30 ms), L3 (20 ms) bei 3.0 und 2.6 V | A, B | ≤ 3 mA × Dauer (PROTOCOL 10.2): L8 15 µC | Strom je Farbe ≤ 3 mA; bei 2.6 V Gelb statt Blau; Einbruch an B |
| E7 | Kopplung (Taster 4 s, Advertising 500 ms, ECDH, SAS) | A | ≈ 0.03 mAh (PROTOCOL 12; ECDH ≤ 3 s × 2.6 mA ANNAHME) | ECDH-Rechenzeit (FW-P3/PP-6) |
| E8 | Schnelles Advertising nach Tastendruck (20 × 100 ms) | A | 0.32 mC real (PROTOCOL 12) | Ladung |
| E9 | OTA 200 kB (Gateway), inkl. Neustart/Swap | A (mA-Bereich) | 0.056 mAh real (`ota_charge`) + Swap 5.7 mC | ≤ 2 % von 225 mAh (REQ-FW-05); Dauer Swap |
| E10 | Fremdverbindung ohne gueltiges HELLO (0.5-s-Frist), 3× → Sperre | A | ≈ 0.25 mC je Versuch (PROTOCOL 4.5, ANNAHME) | Sperre greift; Ladung |
| E11 | Unterspannung: Netzteil langsam 2.6 → 2.3 V, Verbindungen laufen | B (100 Ω) | Abschaltung, wenn VDD unter Last < 2.4 V (FW-5, CONCEPTS E1) | Abschaltschwelle, Shutdown-Strom (Ziel < 0.2 µA, DS Shutdown), Wecken nur per Taster |
| E12 | Tagesprofil (6 auto + 2 Taster, Giessen-LED 12 h, Reaktionszeit 1 min) | D | real ≈ 0.6 µA Ereignisse + Ruhestrom (PROTOCOL 12; `concept_energy.py` A-32) | Tagesmittel → Laufzeit real/pess neu rechnen (REQ-ENE-01) |
| E13 | Temperatur 10 / 25 / 35 °C (Kuehlschrank/Waermeschrank) fuer E1, E3 | C, A | Standby steigt mit T (`energy_budget.py` Sonnenprofil) | Temperaturfaktor ersetzen |

Jede Messung bei **3.0 V** (frische Zelle) und **2.4 V** (Abschaltschwelle), E3/E5/E6 zusaetzlich mit 2 statt 4 × 100 µF
(Entscheid Serie, D-013).

## 3 Vorgehen und Protokoll

1. Firmware-Stand und Hardware-Revision notieren (`GET_INFO`: fw_ver/fw_build, hw_rev).
2. Aufbau pruefen: Shunt-Wert nachmessen, Nullpunkt Oszilloskop, Spannung am Adapter (nicht am Netzteil) einstellen.
3. Messfall ausloesen (Taster, Gateway-Befehl oder Wartezeit), 10 Wiederholungen aufzeichnen (Oszilloskop-Bilder ablegen
   unter `docs/reviews/phase5_energie_messung/`, ASCII-Export der Kurven).
4. Tabelle je Fall: Ladung (µC) Mittel/Min/Max, Dauer, Spitzenstrom, VDD-Minimum, Temperatur.
5. Werte in `scripts/energy_budget.py` eintragen (Parameter `ble.t_cpu`, `prof.t_conn`, `prof.q_meas`, `led.i`, Standby)
   und Laufzeit real/pessimistisch neu berechnen; Ergebnis vom Pruefer nachrechnen lassen (CLAUDE.md Pruefregeln).
6. Firmware-Konstanten (`core/fl_app.c`) und Schwellen (2.55 V Batterie tief, 2.7 V OTA, 2.6 V Wiederanlauf: FW-P6)
   anhand der Entladekennlinie unter Pulslast festlegen.

## 4 Grenzen

- Die Shunt-Spannung von Aufbau A senkt VDD um bis zu 130 mV; fuer Einbruchmessungen immer Aufbau B verwenden.
- Ein Oszilloskop mit 8-bit-Wandler loest bei 10 mV/Div ≈ 0.4 mV ≈ 40 µA (10 Ω) auf: Ruhestrom nur mit Aufbau C/D.
- Ruhestromwerte < 1 µA sind empfindlich auf Leckstroeme des Aufbaus (Feuchte, Flussmittelreste): Platine reinigen,
  Leerwert ohne Sensor messen und abziehen.
