# Phase 5 – Finales Energiebudget Sensor Rev C

| | |
|---|---|
| Datum | 2026-11-08 |
| Verfasser | Firmware/Energie |
| Gegenstand | Sensor **Rev C** (Bestellstand `hardware/sensor/out/ORDER_JLC_REV_C.md`) |
| Rechnung | `.venv/bin/python scripts/energy_budget.py --revb --out hardware/sensor/out/ENERGIE_REV_B.md` (Ausgabe neu erzeugt, Titel „Rev B/C“) |
| Anforderungen | `docs/requirements/REQUIREMENTS.md` REQ-ENE-02, -04, -06, -08, -09; REQ-UI-03; REQ-FW-05 |
| Status | Rechnung abgeschlossen. **REQ-ENE-02 ist im Fall pessDS mit 4 × 100 µF nicht erfüllt.** Der Entscheid W-6 fällt mit der Messung E14 (Kap. 5). |

## 1 Gilt das Rev-B-Budget für Rev C?

Ja. Ich habe Netzliste und BOM geprüft (`fluidi_sensor.net` vom 2026-11-08, `fluidi_sensor_bom_jlc.csv`). Rev C hat dieselben
Bauteile wie Rev B: C1–C4 sind CL31A107MQHNNNE (C15008), Q1/Q2 AO3401A, U1–U6 unverändert. Rev C ändert nur
Layout und Fach (D-023). TP3 entfällt, im Budget betrifft das nur den Begründungstext beim UART-Leckpfad
(`rb.uart_pa`, nachgeführt). Die Datei heisst weiterhin `ENERGIE_REV_B.md`, weil andere Dokumente sie unter diesem Namen
referenzieren.

**Änderungen am Skript in Phase 5:**
- Kap. 3d: Laufzeit bei 1, 2 und 5 min Reaktionszeit. REQ-ENE-04 verlangt diese Angabe, im Rev-B-Bericht fehlte sie.
- Kap. 3e: Entscheidungsregel W-6 mit Schwellen.
- Kennzeichnung Rev C.
- Hinweis zur Selbstentladung und zur Temperatur.
- Pulstabelle: Die Zeile „TX“ deckt nur die drei TX-Pulse ab. Massgebend ist SPICE.

Die Hauptausgabe ohne `--revb` ist bytegleich geblieben (`diff` geprüft).

## 2 Ergebnis (Standardprofil REQ-ENE-04: 6 + 2 Messungen/Tag, 1 min, LED, OTA 1/Jahr)

| Fall | Definition | Schlaf [µA] | Mittelstrom [µA] | Laufzeit 4 × 100 µF | Laufzeit 2 × 100 µF | REQ-ENE-02 (≥ 12 Mt.) |
|---|---|---|---|---|---|---|
| typ (real) | Typwerte, DCDC, 90 % × 0.9 nutzbar, Selbstentladung 1 %/a | 1.03 | 1.67 | 129.5 Mt. (10.8 a)¹ | 136.6 Mt. | erfüllt |
| pessA | REQ-ENE-08: Typ × 1.5, Ereignisse × 1.5, +20 %, 75 % × 0.9, Selbstentladung 2 %/a; Teile ohne Typwert mit ANNAHME | 2.84 | 5.51 | **34.6 Mt.** | 36.4 Mt. | erfüllt |
| pessDS | wie pessA, aber jedes Leck an der Datenblattgrenze (REQ-ENE-08 „oder Maximalwert“) | 16.81 | 22.28 | **9.1 Mt.** | **13.3 Mt.** | **nicht erfüllt** mit 4 ×, erfüllt mit 2 × |

¹ Ab etwa 120 Monaten begrenzt die Alterung der Zelle, nicht der Verbrauch. Dafür gibt es keinen Datenblattwert (ANNAHME ~10 a).

**Reaktionszeit (Kap. 3d), 4 × 100 µF:**

| Reaktionszeit | real | pessA | pessDS |
|---|---|---|---|
| 1 min | 129.5 | 34.6 | 9.1 |
| 2 min | 154.0 | 40.9 | 9.5 |
| 5 min | 172.2 | 45.5 | 9.8 |

Ein längeres Advertising-Intervall rettet den Fall pessDS nicht. Der Schlafstrom dominiert, und davon tragen C1–C4 allein
12 µA bei.

**Woraus pessDS besteht (Schlaf 16.81 µA, `ENERGIE_REV_B.md` Kap. 1):**

| Bauteil | Wert | Quelle |
|---|---|---|
| C1–C4 | 12 µA | Grenzwert IR ≥ 100 MΩ·µF bei Nennspannung (`Samsung_CL31A107MQHNNNE_Catalog_2015-11.pdf` S. 53, Pos. 2 „Insulation Resistance“) → 1 MΩ je 100 µF → 3 µA bei 3 V, × 4 |
| U1 Standby | 1.83 µA | Typwert GLDO 1.15 µA × 1.5 × Sonnenfaktor 1.058 (`TI_CC2340R5_Datasheet_SWRS272F.pdf` S. 20 Tab. 7.9 und S. 35 Fig. 7-7) |
| Q2 IDSS | 1.67 µA | 1 µA bei 25 °C, 5 µA bei TJ 55 °C, je bei VDS −30 V, mit dem Sonnenprofil gewichtet (`AOS_AO3401A_Datasheet_Rev3.1.pdf` S. 2) |
| C5/C9 | 0.96 µA | `Samsung_CL05A106MQ5NUNC_Datasheet_LCSC-2022-08.pdf` S. 2 |

Mit DS-Grenzwerten verfehlen 4 × 100 µF REQ-ENE-02, mit 2 × 100 µF ist der Einbruch zu gross (REQ-ENE-06). Daraus ergibt sich W-6.

## 3 Einzelnachweise

| Punkt | Ergebnis | Nachweis / Quelle |
|---|---|---|
| Selbstentladung | real 1 %/a, pess 2 %/a (0.51 µA Äquivalent) | `Renata_CR2032MFR_Datasheet_Rev07.pdf` S. 1 „Self Discharge at 23 °C < 1 %/year“. Bestückt wird die Panasonic CR2032 (D-006), deren Datenblatt (`Panasonic_CR2032_Datasheet_2026-02.pdf` S. 1) keinen Wert nennt. Der Renata-Wert dient als Ersatz (**ANNAHME**), pess 2 %/a ebenfalls **ANNAHME** |
| Nennkapazität | 225 mAh | `Panasonic_CR2032_Datasheet_2026-02.pdf` S. 1 (= Renata S. 1) |
| Nutzbare Kapazität | pess 75 % (REQ-ENE-08) × 0.9 (Abschaltung bei 2.4 V unter Last, FW-5; Firmware `UV_MV 2400` in `core/fl_app.c`) = 547 C | Faktor 0.9 aus der Entladekurve abgelesen (**ANNAHME**). Die Abschaltung bei 2.4 V liegt über den 2.0 V aus REQ-ENE-06 und ist damit konservativ |
| Temperatur | Standby U1 mit Sonnenprofil (4 h bei 50 °C, RB-03), Faktor 1.058; Q2 mit der 55-°C-Grenze | Leckstrom der MLCC: Das Datenblatt nennt ihn nur bei Raumtemperatur. Den Temperaturgang misst E14 bei 50 °C (**PROTOTYP-PRÜFUNG**). Kapazitätsverlust bei Kälte ist nicht angesetzt (Innenraum 5–45 °C, **ANNAHME**). Den Innenwiderstand bei Kälte deckt R_int 100 Ω ab (REQ-ENE-06) |
| Pulslast REQ-ENE-06 | Advertising-Einbruch 143 mV (4 × 100 µF) bzw. 246 mV (2 × 100 µF), pessimistisch, DC-Bias 50 % und −20 % | `simulation/spice/supply/supply_report.txt` Z. 6. Die einfache RC-Tabelle in `ENERGIE_REV_B.md` Kap. 4 zeigt für „TX“ nur 60 mV, weil sie nur die drei TX-Pulse rechnet. Massgebend ist SPICE |
| LED (REQ-UI-03 ≤ 5 %) | pessA: 12.7 mC von 397 mC/Tag = 3.2 % | Kap. 3c; LED-Pulse ≤ 5 ms nach FW-4 |
| OTA (REQ-FW-05 ≤ 2 %) | 0.06 mAh pro Jahr ≈ 0.03 % | `ota_charge` |
| REQ-ENE-09 (gerechnet) | Mittelstrom pessA 5.51 µA ≤ 8 µA; Schlaf pessA 2.84 µA ≤ 3 µA (knapp). pessDS 16.8 µA Schlaf liegt über der Grenze | Nachweis verlangt Messung (E1, E12) |

**Eigene Gegenrechnung** (nicht aus dem Skript übernommen):
- pessA: 547 C / ((5.51 + 0.51) µA × 86 400 s) = 1051 d = 34.6 Mt. ✓
- pessDS: 547 C / ((22.28 + 0.51) µA × 86 400 s) = 278 d = 9.1 Mt. ✓
- Schlaf pessDS: 1.826 + 0.1 + 1.667 + 12 + 0.96 + 0.06 + 0.2 = 16.81 µA ✓
- Advertising pess: 40.9 µC × 86 400 / 27.5 = 128.5 mC/Tag ✓ (Kap. 3c: 128.4)

## 4 Bewertung gegen die Anforderungen

| Anforderung | 4 × 100 µF (Prototyp, D-013) | 2 × 100 µF |
|---|---|---|
| REQ-ENE-02 pessA | erfüllt (34.6 Mt.) | erfüllt (36.4 Mt.) |
| REQ-ENE-02 pessDS (wörtlich REQ-ENE-08) | **nicht erfüllt (9.1 Mt.)** | erfüllt (13.3 Mt., knapp) |
| REQ-ENE-06 (≤ 0.2 V bei 100 Ω) | erfüllt (SPICE 143 mV) | **nicht erfüllt (SPICE 246 mV)**; nominal ohne DC-Bias 118 mV, deshalb messen |
| REQ-ENE-08 | angewendet; Selbstentladung als ANNAHME (Panasonic ohne Wert) | dto. |
| REQ-ENE-09 | gerechnet erfüllt (pessA); Messung offen | dto. |

**Fazit:** Für den Prototyp bleibt es bei 4 × 100 µF. Für die Serie ist REQ-ENE-02 erst mit der Messung E14 nachgewiesen.

## 5 Entscheid W-6: Messung und Entscheidungsregel

**Messung:** E14 in `docs/manuals/ENERGIEMESSUNG.md`. Sie wird ergänzt durch E1 (Ruhestrom aller Muster) und E3/E5/E6 an
Aufbau B mit 2 Kondensatoren.

1. **E14a:** E1 an allen Mustern, 3.0 V, 25 °C, nach ≥ 1 h an Spannung. Grund: MLCC-Leckströme klingen nach dem Anlegen
   der Spannung ab. Die DS-Prüfung misst nach 60–120 s (`Samsung_..._Catalog` S. 53), der Wert nach 1 h ist der
   Dauerwert (**ANNAHME**).
2. **E14b:** An 2 Mustern C3/C4 ablöten und E1 wiederholen. Die Differenz ist der Leckstrom von 2 Kondensatoren. Diese
   Muster dienen gleich für E3/E5/E6 mit 2 × 100 µF (Aufbau B: Netzteil 2.7 V + 100 Ω).
3. **E14c:** Die abgelöteten Kondensatoren einzeln messen: 3.0 V, 100 kΩ in Serie, DMM über dem Shunt (1 mV = 10 nA),
   bei 25 °C und 50 °C.

**Auswertung:** I_eff = (20 h · I_25 + 4 h · I_50) / 24 h je Kondensator, nach dem Sonnenprofil RB-03. Massgebend ist der
grösste Wert aller gemessenen Kondensatoren. Der Messwert geht mit × 1.5 ins Budget ein, wie ein Typwert nach REQ-ENE-08.
Die Schwellen stehen in `ENERGIE_REV_B.md` Kap. 3e. Der Rest des Budgets bleibt dabei streng an den DS-Grenzen (pessDS).

| Messwert I_eff je Kondensator (Maximum) | Entscheid Serie |
|---|---|
| **≤ 1.24 µA** | **4 × 100 µF** bleibt. REQ-ENE-02 und REQ-ENE-06 sind erfüllt |
| 1.24 … 2.49 µA | **2 × 100 µF** nur, wenn der gemessene Einbruch bei E3/E5/E6 (Aufbau B, 2 × 100 µF) **≤ 200 mV** beträgt. Sonst Vorlage an den Auftraggeber |
| > 2.49 µA | Keine Variante erfüllt beide Anforderungen. Vorlage an den Auftraggeber (z. B. anderer Kondensatortyp; das wäre ein neues Bauteil mit Datenblatt) |

**Zusatzregel über den Gesamtruhestrom:** Gilt für jedes Muster E1 ≤ 3 µA (REQ-ENE-09) bei Sonnenprofil-Gewichtung, so ist
REQ-ENE-02 mit 4 × 100 µF auch ohne Zerlegung in Einzelbeiträge erfüllt. Zulässig wäre ein Messwert bis 8.18 µA (Kap. 3e,
Ereignisse pessA).

**Voraussetzung (Entscheid Orchestrator/Auftraggeber):** REQ-ENE-08 verlangt wörtlich „Typwert × 1.5 **oder Maximalwert**“.
Die Regel setzt den **gemessenen Maximalwert der Muster × 1.5** an die Stelle des MLCC-Grenzwerts aus dem Katalog. Das
sollte als D-Eintrag festgehalten werden, bevor die Messung ausgewertet wird. Erwartet wird ein Messwert weit unter der
Schwelle (Modell real 0.05 µA je Kondensator, **ANNAHME**). Die Stichprobe ist aber klein: 5 Muster bzw. 4–20 Kondensatoren.

## 6 Offene Punkte

| Nr. | Punkt | Art |
|---|---|---|
| E-1 | E14 (W-6) und Entscheid 2 oder 4 × 100 µF; D-Eintrag zur Auslegung von REQ-ENE-08 vorher | PROTOTYP-PRÜFUNG / Entscheid |
| E-2 | Selbstentladung Panasonic CR2032: kein Wert im lokalen Datenblatt; Renata-Wert als ANNAHME. Falls Panasonic eine Angabe (z. B. Handbuch) liefert: herunterladen und eintragen | Doku |
| E-3 | DC-Bias C15008 (Annahme 50 % Restkapazität bei 3 V): lokal fehlt die Kurve. E3 an Aufbau B misst die Wirkung direkt | PROTOTYP-PRÜFUNG |
| E-4 | Modellwerte für Ereignisse (T_CONN 50 ms, Q_MEAS, P_MISS) durch die Messungen E3–E12 ersetzen, dann Skript neu laufen lassen und vom Prüfer nachrechnen lassen | PROTOTYP-PRÜFUNG |
