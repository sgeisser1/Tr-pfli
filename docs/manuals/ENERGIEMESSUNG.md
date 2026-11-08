# fluidi – Energiemessplan Sensor-Prototyp (Rev B/C)

| | |
|---|---|
| Stand | 2026-11-08, Firmware/Energie; gilt fuer Rev C (Schaltung/BOM = Rev B). Ergaenzt um E14 (W-6) und E15 (W-10); Einbettung in den Testplan: `docs/reviews/phase5_testplan_beitrag_firmware.md` |
| Zweck | Modellwerte aus `scripts/energy_budget.py` / `firmware/PROTOCOL.md` Kap. 12 am Muster ersetzen (REQ-ENE-01…08, OP-K6, FW-P3), Firmware-Regeln FW-2/FW-4/FW-5/FW-8 aus `docs/interfaces/PINMAP_SENSOR.md` nachweisen |
| Werkstattmittel | Labornetzteil (0–5 V, Strombegrenzung), Oszilloskop ≥ 2 Kanaele (≥ 20 MHz, Mittelwert-/Integralfunktion), Shunts 1 Ω / 10 Ω / 1 kΩ (0.1–1 %, Metallfilm), Digitalmultimeter mit µA-Bereich und Aufzeichnung, CR2032 (frisch und teilentladen), Widerstand 100 Ω (Zell-Innenwiderstand EOL, REQ-ENE-06) |
| Firmware | Build `firmware/sensor` (Rev B), Zaehler aus `GET_INFO` (meas/adv/conn/led_ms, charge_uc) zur Gegenprobe |

**Sicherheit (CONCEPTS 2.7, Auflage R2-A2):** Strommessung nur ueber den **Mess-Zwischenadapter im Zellhalter
(nur Amperemeter/Shunt, keine Quelle in Serie zur Zelle)**. Speisung aus dem Labornetzteil nur ueber den
Dummy-Zellen-Adapter **ohne** Zelle. Strombegrenzung des Netzteils: Programmieren 10 mA, Funktions-/Energietests 3.0 V / 30 mA, nur ueber die Dummy-Scheibe, nie mit Zelle im Clip (Testplan EP-03). Keine Speisung ueber TP1/TP2 (einzige Ausnahme PT11.06/ST-Z5).

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
| E1 | Ruhestrom ungekoppelt (kein Advertising, LEDs aus, FW-8) bei 3.0 V und 25 °C | C | Rev B real 1.03 µA: 0.74 µA Standby LFXT DCDC (`TI_CC2340R5_Datasheet_SWRS272F.pdf` S.19 Tab. 7.9) + Puffer 4 × 100 µF 0.2 µA + Q1/Q2/Leiterplatte ≈ 0.1 µA (ANNAHMEN, `energy_budget.py --revb` Tab. 1; Datenblattgrenzen: C1–C4 12 µA, Q2 IDSS 1 µA) | ≤ 1.5 µA (REQ-ENE-09 ≤ 3 µA); Einzelbeitraege: Messung mit C3/C4 abgeloetet wiederholen (Puffer-Leck, D-013), > 10 µA → Pin-Zustand pruefen (SWD-Pull-up an DIO16 ueber R4 in den abgeschalteten TMP: Pull-up-Strom 39–109 µA bei 1.8 V, bis 170–393 µA bei 3.8 V, DS S.31–32; PINMAP FW-6) |
| E2 | wie E1, Taster dauernd gedrueckt > 30 s | C | vor Abschaltung Pull-up-Strom: DS S.31 39–109 µA bei VDDS 1.8 V, S.32 170–393 µA bei 3.8 V → bei 3.0 V dazwischen (ANNAHME ≈ 100–300 µA), danach Pull-up aus | nach 30 s wieder ≈ E1 (PROTOCOL 10.3); Wert bei 3.0 V notieren |
| E3 | Advertising-Ereignis (gekoppelt, 27.5 s, 0 dBm) | A, B | 16.2 µC real / 40.9 µC pess (`energy_budget.py` `adv_event_charge`) | Ladung; VDD-Einbruch an B ≤ 0.2 V (REQ-ENE-06) |
| E4 | Datensitzung (HELLO, TIME_SET, READ 1–2 Datensaetze, ACK, Trennen) | A, B | 299 µC real / 767 µC pess (`conn_charge`, 50 ms ANNAHME) | Dauer und Ladung → `T_CONN`; Anzahl Verbindungsereignisse ≤ 12 (PROTOCOL 2.5) |
| E5 | Messung (Taster kurz, gekoppelt ohne Gateway) | A, B | Rev B real ≈ 37 µC je Messung: Kette 7.3 mA (Cpd-Rechnung, 24 MHz) + CPU 2.6 mA, 4 × 0.6 ms ≈ 24 µC + TMP1075N/I²C ≈ 5 µC + CPU/Flash ≈ 8 µC; pess. 289 µC, falls in den Pausen nur Idle statt Standby (`energy_budget.py --revb` Tab. 2; PINMAP FW-2) | **Burst ≤ 0.6 ms, Pause ≥ 30 ms, max. 4** (Kanal 2 an DIO11 statt VDD); Einbruch an B ≤ 0.2 V; ersetzt `Q_MEAS` |
| E6 | LED-Muster L8 (Giessen, 5 ms), L1 (2 × 30 ms), L3 (20 ms) bei 3.0 und 2.6 V | A, B | ≤ 3 mA × Dauer (PROTOCOL 10.2): L8 15 µC | Strom je Farbe ≤ 3 mA; bei 2.6 V Gelb statt Blau; Einbruch an B |
| E7 | Kopplung (Taster 4 s, Advertising 500 ms, ECDH, SAS) | A | ≈ 0.03 mAh (PROTOCOL 12; ECDH ≤ 3 s × 2.6 mA ANNAHME) | ECDH-Rechenzeit (FW-P3/PP-6) |
| E8 | Schnelles Advertising nach Tastendruck (20 × 100 ms) | A | 0.32 mC real (PROTOCOL 12) | Ladung |
| E9 | OTA 200 kB (Gateway), inkl. Neustart/Swap | A (mA-Bereich) | 0.056 mAh real (`ota_charge`) + Swap 5.7 mC | ≤ 2 % von 225 mAh (REQ-FW-05); Dauer Swap |
| E10 | Fremdverbindung ohne gueltiges HELLO (0.5-s-Frist), 3× → Sperre | A | ≈ 0.25 mC je Versuch (PROTOCOL 4.5, ANNAHME) | Sperre greift; Ladung |
| E11 | Unterspannung: Netzteil langsam 2.6 → 2.3 V, Verbindungen laufen | B (100 Ω) | Abschaltung, wenn VDD unter Last < 2.4 V (FW-5, CONCEPTS E1) | Abschaltschwelle, Shutdown-Strom (Ziel < 0.2 µA, DS Shutdown), Wecken nur per Taster |
| E12 | Tagesprofil (6 auto + 2 Taster, Giessen-LED 12 h, Reaktionszeit 1 min) | D | real ≈ 0.6 µA Ereignisse + Ruhestrom (PROTOCOL 12; `concept_energy.py` A-32) | Tagesmittel → Laufzeit real/pess neu rechnen (REQ-ENE-01) |
| E13 | Temperatur 10 / 25 / 35 °C (Kuehlschrank/Waermeschrank) fuer E1, E3 | C, A | Standby steigt mit T (`energy_budget.py` Sonnenprofil) | Temperaturfaktor ersetzen |
| E14 | **Leckstrom C1–C4 (W-6, D-013):** (a) E1 an allen Mustern; (b) an 2 Mustern C3/C4 abloeten, E1 wiederholen (Differenz = 2 Kondensatoren); (c) die abgeloeteten Kondensatoren einzeln: 3.0 V, **100 kΩ** in Serie (1 mV = 10 nA; τ = 10 s), DMM ueber dem Shunt; Werte nach 1 min, 10 min, 1 h (Auswertung), 24 h; bei 25 °C und 50 °C (Sonnenprofil RB-03; Waermeschrank **ANNAHME**) | C bzw. eigener Aufbau | real 0.05 µA je 100 µF (ANNAHME), Datenblattgrenze 3 µA bei 3 V ([SAM] S.53, 100 MΩ·µF) | I_eff = (20 h · I_25 + 4 h · I_50)/24 h, Maximum aller Kondensatoren: **≤ 1.24 µA → 4 × 100 µF bleibt**; 1.24–2.49 µA → 2 × 100 µF nur mit E3/E5/E6 ≤ 0.2 V (Aufbau B, 2 Kondensatoren); > 2.49 µA → Vorlage Auftraggeber (`ENERGIE_REV_B.md` Kap. 3e) |
| E15 | **Bootloader-Strom (W-10):** Taster gedrueckt halten, Speisung einschalten, nach 2 s loslassen; Strom 60 s mitteln; bei 3.0 V und 2.0 V; danach Speisung ≥ 10 s weg, ohne Taster einschalten → L11 | A (10 Ω), DMM mA | 0.8–4.1 mA (ANNAHME, DS S.19–20 Idle/CPU) | Wert in `PROGRAMMIEREN_SENSOR.md` Kap. 6 eintragen (Tage bis Zelle leer = 152 mAh / I); L11 nach Neustart ohne Taster muss erscheinen |

Jede Messung bei **3.0 V** (frische Zelle) und **2.4 V** (Abschaltschwelle), E3/E5/E6 zusaetzlich mit 2 statt 4 × 100 µF
(Entscheid Serie, D-013).

## 3 Vorgehen und Protokoll

1. Firmware-Stand und Hardware-Revision notieren (`GET_INFO`: fw_ver/fw_build, hw_rev).
2. Aufbau pruefen: Shunt-Wert nachmessen, Nullpunkt Oszilloskop, Spannung am Adapter (nicht am Netzteil) einstellen.
3. Messfall ausloesen (Taster, Gateway-Befehl oder Wartezeit), 10 Wiederholungen aufzeichnen (Oszilloskop-Bilder ablegen
   unter `docs/reviews/phase5_energie_messung/`, ASCII-Export der Kurven).
4. Tabelle je Fall: Ladung (µC) Mittel/Min/Max, Dauer, Spitzenstrom, VDD-Minimum, Temperatur.
5. Werte in `scripts/energy_budget.py` eintragen (Parameter `ble.t_cpu`, `prof.t_conn`, `led.i`, Rev B: `rb.*` z. B. `rb.mlcc_real`, `rb.q2_real`, `rb.t_cpu_meas`, Standby), Ergebnis mit `--revb --out hardware/sensor/out/ENERGIE_REV_B.md` neu erzeugen
   und Laufzeit real/pessimistisch neu berechnen; Ergebnis vom Pruefer nachrechnen lassen (CLAUDE.md Pruefregeln).
6. Firmware-Konstanten (`core/fl_app.c`) und Schwellen (2.55 V Batterie tief, 2.7 V OTA, 2.6 V Wiederanlauf: FW-P6)
   anhand der Entladekennlinie unter Pulslast festlegen.

## 4 Grenzen

- Die Shunt-Spannung von Aufbau A senkt VDD um bis zu 130 mV; fuer Einbruchmessungen immer Aufbau B verwenden.
- Ein Oszilloskop mit 8-bit-Wandler loest bei 10 mV/Div ≈ 0.4 mV ≈ 40 µA (10 Ω) auf: Ruhestrom nur mit Aufbau C/D.
- Ruhestromwerte < 1 µA sind empfindlich auf Leckstroeme des Aufbaus (Feuchte, Flussmittelreste): Platine reinigen,
  Leerwert ohne Sensor messen und abziehen.
