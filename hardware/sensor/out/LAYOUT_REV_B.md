# fluidi Sensor – Layout Rev B (Phase 4a Welle 2)

| | |
|---|---|
| Stand | 2026-11-07, Elektronik |
| Platine | `hardware/sensor/fluidi_sensor.kicad_pcb` (KiCad 10.0.8), Regeln `fluidi_sensor.kicad_dru`, Projekt `fluidi_sensor.kicad_pro` |
| Erzeugung | `bash hardware/sensor/gen/run_pcb.sh` (Generator, DRC in WSL und Windows, Exporte). Module: `gen_pcb.py` (Footprints, Netze/Felder/Symbol-UUID aus der Schaltplan-Netzliste), `pcb_place.py` (Platzierung), `pcb_build.py` (Kupfer, Zonen, Regelflächen, Silkscreen), `pcb_router.py` (eigener Raster-Router mit Rip-up), `pcb_rules.py` (DRC-Regeln), `cpl_jlc.py` (CPL), `drc_summary.py` |
| Option | `--u3 band`: Rückfallebene ohne Kragenfeld (U3/C24 rechts oben im Band, ganzes Z5 nach Z5A-Regel) |
| Grundlage | `docs/interfaces/PCB_OUTLINE.md` Rev B, `mechanical/interfaces/pcb_outline.json`, `simulation/field/REPORT.md` Kap. 8, AN043 (`docs/appnotes/TI_AN043_SmallPCBAntenna_SWRA117D.pdf`), `docs/appnotes/TI_CC23xx_HWDesignGuide_SWRA834A.pdf`, `docs/references/JLCPCB_NOTES.md`, `docs/reviews/phase4_sicherheit_kragen_firmware.md` (K-1 … K-7) |
| Status | Entwurf zur Prüfung durch einen anderen Agenten. Kein Commit |

## 1 Lagenaufbau und Lagennutzung

JLC04161H-7628 (Standard „No requirement“, `JLCPCB_NOTES.md` Kap. 4), 1.6 mm, als `(stackup …)` in der Platinendatei:

| Lage | Dicke | Band (Kopf) | Fach/Schott | Kragen, Z6, Sonde |
|---|---|---|---|---|
| F.Cu (L1) | 35 µm | Bauteile, Signale, HF-Kette, GND-Fläche | nur Pads (Clip, Minuspad, TP1–TP3) | U3/C24 im Feld (Option kragen), sonst kein Kupfer |
| Prepreg 7628 | 0.2104 mm, Er 4.4 | | | Isolation über den Elektroden |
| In1.Cu (L2) | 15.2 µm | **GND-Bezugsfläche** (HF, Antenne), nur die S-Zuleitung L2 | GND (Kante ≥ 1.0 mm) + S-Zuleitung | Guard, G-Elektrode, G-Steg, S-Elektrode |
| Kern | 1.065 mm, Er 4.5 (KiCad-Standard, von JLC nicht belegt) | | | |
| In2.Cu (L3) | 15.2 µm | **VDD-Fläche** | GND + Leitungen VBAT, UART-Pads, S-Zuleitung L3, U3-Leitungen | wie L2 |
| Prepreg 7628 | 0.2104 mm | | | |
| B.Cu (L4) | 35 µm | Signale, GND-Fläche, TP4/TP5 | kein Kupfer | kein Kupfer |

Begründung In2 = VDD: Mit drei Signallagen (F, In2, B) und geroutetem VDD blieben in allen Läufen 6–10 Verbindungen offen.
VDD als Fläche mit einem Via je Pad (wie GND) gibt F und B frei. Die HF-Referenz (In1) bleibt unter Antennenspeisung
und HF-Kette geschlossen.

## 2 Antenne AN043 und HF

- Footprint `RF_Antenna:Texas_SWRA117D_2.4GHz_Right` (Einspeisung links, offenes Ende rechts, wie PCB_OUTLINE Kap. 3
  verlangt; die dort genannte Variante „…_Left“ hat das offene Ende links). Schaltplan-Footprint angepasst
  (`parts.py`, `gen_lib.py`).
- Masse des Footprints gegen AN043 S. 4, Abb. 3 / Tab. 1 nachgerechnet (Koordinaten relativ zur Speisung):
  W1 0.90 (−2.55…−1.65), W2 0.50, D5 1.40, D6 1.70, L6 4.90, L3 5.00, L4 2.64, L5 2.00, L2 2.70 (zweimal), L1 3.94,
  D1/D2/D3 0.50/0.30/0.30, D4 0.50 – alle gleich Tab. 1. Gesamt 15.2 × 5.7 mm (AN043 S. 1).
- Lage: Speisepunkt X 0.35, Y 5.45; Keepout X −2.70…12.50, Y 0…5.20 auf **allen** Kupferlagen (Regelfläche `Z1_ANTENNE`:
  keine Bahnen, Vias, Flächen); ganzes Z1 ohne Bauteile. Antennenkupfer X −2.20…12.20, 0.8 mm zur rechten Kante.
  Massekante (Ende Keepout) Y 5.20 = AN043 D4. Masse-Pad 2 (Via) des Footprints verbindet mit In1.
- HF-Kette nach HW-Guide Kap. 4.2 (Quer-C mit dem Pad direkt am Knoten): C20 (DNM) – R2 0 Ω – C19 (DNM) – C18 15 pF –
  C17 1.5 pF – L2 2.7 nH – C16 1.5 pF – U1 Pin 1. Leitung 0.35 mm auf L1 über In1 (**ANNAHME** ≈ 50 Ω bei Prepreg
  0.21 mm, Er 4.4; im JLC-Impedanzrechner bestätigen). Länge Speisepunkt – Pin 1 ≈ 12 mm.
- 48-MHz-Quarz Y1 direkt rechts von U1, Leitungen fest im Skript (X48P zwischen den Pads von Y1 hindurch), keine
  externen C (DS S. 26 Fn. 1). 32-kHz-Quarz Y2 links unter U1 mit C14/C15.
- Jeder Abblock-C hat ein eigenes Via (HW-Guide Kap. 4.3); VDDS-Pins 11/18/24 laufen erst in „ihren“ C (C6/C7/C8).
  EP mit 4 Vias, Pin 23 direkt ans EP. GND-Stitching am Bandrand und an der Antennen-Massekante.

## 3 Sonde, Guard, Zuleitungen (Feld Kap. 8)

z-Bezug: Feld z_f = −z, KiCad-Y = 53.5 + z_f. Die Elektrodenlage bezieht sich auf die Erdoberfläche (Stecktiefe
z_f = 5, Y 58.5) und bleibt wie simuliert. Die Vergusskante liegt 2 mm höher (z = 2.0, Y 51.5) als im Feld
angenommen: zwischen Verguss und Erde liegen also 7 statt 5 mm, dort nur Guard (keine Elektrode) – konservativ für
den Luftanteil (PCB_OUTLINE Kap. 1).

| Element | Lage | X [mm] | Y [mm] (z_f) |
|---|---|---|---|
| S (PROBE_SENSE) | L2 + L3 | −8.75 … −1.00 | 63.5 … 139.5 (10 … 86) |
| G (GND) | L2 + L3 | +1.00 … +8.75 | 61.5 … 143.5 (8 … 90) |
| G-Steg | L2 + L3 | −8.75 … +8.75 | 141.5 … 143.5 (88 … 90) |
| Guard (GND) | L2 + L3 | −8.75 … +8.75 | Kragen 46.0 … 61.5 (… 8), darüber GND-Flächen Fach/Band |
| S-Zuleitung L2 | In1 | −8.0, 0.3 breit, Kanal 0.3 | Band-Via Y 20.5 … 64; In2 darunter GND |
| S-Zuleitung L3 | In2 | −7.0, 0.3 breit, Kanal 0.3 | Band-Via Y 20.5 … 64; In1 darüber GND |

- **Abweichung von Kap. 8:** Die S-Elektrode auf L3 lässt sich ohne Via im nassen Bereich nicht von L2 aus speisen.
  Deshalb zwei Zuleitungen: L2-Zuleitung über GND auf L3 (wie Kap. 8), L3-Zuleitung unter GND auf L2 (symmetrisch).
  Lage x −8.0/−7.0 statt −4.9, weil die U3-Leitungen (In2) vom Kragenfeld nach rechts laufen und die Zuleitungen
  nicht kreuzen dürfen. Die Zusatzkapazität der zweiten Zuleitung ist konstant (Kalibrierung); **PROTOTYP-PRÜFUNG**
  bzw. Nachrechnung Feld (Cpar).
- Vias zwischen L2 und L3 nur im Band (Y ≤ 20.7). Kragen, Z6 und Sonde ohne Vias und ohne Aussenkupfer;
  Kupfer ≥ 1.25 mm zur Kontur ab Z5A (DRC-Regel), auch an der Spitze (Elektroden enden 7.5 mm vor dem Fasenbeginn).
- Guard im Fach als volle GND-Flächen auf L2/L3 statt „schmaler GND-Bahn“ (FLOORPLAN 2f): Schirmung der beiden
  S-Zuleitungen über 40 mm (REQ-MECH-09). Folge: U3 ist thermisch über die Innenlagen an den Kopf gekoppelt
  (**PROTOTYP-PRÜFUNG** Temperaturfehler gegen Erdtemperatur).

## 4 Zonen, Regeln (DRC) und Sicherheitsauflagen

Regelflächen (in der Platine, Namen für `.kicad_dru`): `Z1_ANTENNE` (alle Lagen: keine Bahnen/Vias/Flächen),
`Z3_SCHOTT` und `Z4_FACH` (F/B: keine Bahnen/Flächen; Schott auch keine Vias), `Z5_KRAGEN` (F/B: nichts ausser dem
Feld), `Z6_Z7_NASS` (F/B: keine Bahnen/Pads/Vias/Flächen), `Z5A_Z7_SONDE` (alle Lagen: keine Vias),
benannt ohne Sperre: `Z3_Z4_INNEN`, `VIP_FACH`, `Z5B_FELD`, `Z5A_DICHT`.

`fluidi_sensor.kicad_dru` (erzeugt von `pcb_rules.py`):

| Regel | Wert | Quelle |
|---|---|---|
| Abstand / Bahnbreite | ≥ 0.10 / ≥ 0.10 (Entwurf 0.15) | JLC 4 L 0.09 (JLCPCB_NOTES Kap. 3) |
| Via | Ø ≥ 0.45, Bohrung ≥ 0.20 (verwendet 0.45/0.30), Restring ≥ 0.075 | JLC, Ø < 0.45 kostet Aufpreis |
| Bohrabstand / Bohrung–Kupfer | ≥ 0.25 / ≥ 0.20 | JLC |
| Kupfer–Kontur | ≥ 0.30 allgemein, **≥ 1.25 ab Z5A** (Sonde, Spitze) | JLC 0.2; Feld Kap. 8, REQ-MECH-06 |
| K-3 | Innenlagen in Schott/Fach ≥ 1.0 zur Kante | Sicherheit Phase 4 |
| K-1 | Dichtstreifen Z5A Innenlagen nur GND und /PROBE_SENSE | Sicherheit Phase 4 |
| K-2 | Vias im Kragenfeld ≥ 1.0 zur Kante; Feld x −9.0 … −4.6 (statt −9.4); alle Vias tented | Sicherheit Phase 4 |
| Fach | Vias nur als Via-in-Pad (Regelfläche `VIP_FACH`) | S2-W03, REQ-MECH-05 |
| Schott, Kragen ausser Feld, nass | keine Vias | S3-K1, REQ-MECH-05 |
| Silkscreen | Text ≥ 1.0 mm hoch, ≥ 0.15 Strich; Bibliotheks-Silk auf 0.15 verbreitert | JLC |

Kragenfeld (Option kragen): U3 TMP1075N (180°) und C24 im Feld; 4 Vias in der Spalte x −5.0 (SDA, GND, SCL,
SENS_PWR) + 1 GND-Via x −8.7 (Kante 1.08 mm), alle tented. Die U3-Leitungen enden im Feld (z ≥ 4.4, K-1).

## 5 Platzierung und Routing

- Feste Lagen nach PCB_OUTLINE Kap. 5 eingehalten: D1 (0, 9.6) – **180° gedreht** (Kathoden G/B links zu R7/R8,
  gleiche Leuchtfläche), SW1 (−6.0, 8.4) unrotiert, BT1 Zelle (3.0, 34.45) 90°, TP1–TP3 im Streifen x −10.6.
  Alle Courtyards im Band Y 5.7…20.8, ≥ 0.3 zur Kontur, überlappungsfrei (Generator prüft). Höhen ≤ 2.0 (Bibliothek).
- U1 (6.0, 12.6) rot 270 (Pin 1 oben → HF), Q1 oben links (VBAT über In2 am rechten/oberen Rand), Messkette links,
  Puffer C1–C4 unten quer (Biegelinie), I²C-Pull-ups R4/R5 unten Mitte bei den Übergabevias der U3-Leitungen.
- UART-Barrieren (R2-A3): R9/R11 (2a) oben Mitte, R10/R12 (2b) unten links, getrennte Bauteile > 10 mm auseinander,
  alle im Elektronikraum.
- Testpads: TP1 TX, TP2 RX, TP3 GND (F, Fach, beschriftet), TP4 MEAS_CLK und TP5 PROBE_SENSE auf B im Band.
- Router: Raster 0.05 mm, Lagen F/B, Entwurfsabstand 0.15, Bahnen 0.15 (Signal) / 0.20 (DCDC_SW, VDDR, OSC_PWR,
  VBAT), Vias 0.45/0.30; GND- und VDD-Fanout je Pad (Via-Lage weg von fremden Pads), danach Netze mit Rip-up/
  Reroute und Verlaufskosten. Reihenfolge per Startwert: **Seed 7** (kragen) bzw. **8** (band) routen vollständig
  (andere Startwerte liessen 1–3 Verbindungen offen). 1371 Bahnstücke, 104 Router-Vias + feste Vias.
  Kein Handrouting, keine Restliste. Übersicht: `out/layout_band_routing.png`.

## 6 Silkscreen

F: Wortmarke „fluidi“ v3a (10 mm breit, Strich 0.52 mm) und „rev B“ in Z6, Stecktiefenlinie Y 58.5 (z −5) mit
„max“ und Pfeil, TX/RX/GND an den Pads; Pin-1-/Polaritätsmarken aus den Bibliotheks-Footprints (auf 0.15 mm).
B: „fluidi rev B“, Linie und „max“. Referenzen nur auf F.Fab/B.Fab (Band zu dicht), Bestückungsplan daraus.
Kein Warnsymbol (laut Auftrag am Gehäuse).

## 7 DRC-Ergebnis (2026-11-07, `run_pcb.sh`, mit `--schematic-parity --refill-zones --severity-all`)

| | Verletzungen | Ungeroutet | Parität |
|---|---|---|---|
| KiCad 10.0.8 WSL (`out/drc_wsl.rpt`, `.json`) | **0** | **0** | 0 |
| KiCad 10.0.8 Windows (`out/drc_win.rpt`) | **0 Fehler**, 4 Warnungen `lib_footprint_mismatch` (U2, U4–U6) | **0** | 0 |
| Option `--u3 band` (Seed 8, WSL, Prüflauf im Scratchpad) | 0 | 0 | 0 |

Die 4 Windows-Warnungen: Die Windows-Bibliothek hat eine neuere `SOT-353_SC-70-5` (Version 20260206) mit anderer
Silk/Courtyard-Linie; Pads gleich (Diff geprüft). Schaltplan neu erzeugt: ERC 0 Fehler, 1 Warnung (unverändert,
pin_to_pin SENS_PWR-Flag).

**Gegenprüfung Projektleitung (2026-11-07):** DRC ohne `--refill-zones` (gespeicherte Füllung, aus der die Gerber
entstehen) ergab im ersten Stand 2 × `copper_edge_clearance` (K-3, 0.9977 mm an einem Bogen, Zonen GND_FACH_In1/In2).
Korrektur: Fach-Zonenpolygon mit 1.05 mm Abstand statt 1.0 mm (`pcb_build.py`). Nach Neulauf (`run_pcb.sh kragen 7`)
DRC mit und ohne Neufüllung: 0 Verletzungen, 0 ungeroutet, 0 Parität (WSL); Windows 0 Fehler, 4 Warnungen wie oben.

## 8 Exporte (`hardware/sensor/out/`)

| Datei | Inhalt |
|---|---|
| `gerber/`, `fluidi_sensor_gerber_jlc.zip` | Gerber 4 Lagen (Protel-Endungen, ohne X2), Excellon mm PTH/NPTH, Hilfsursprung = Schnittstellen-Ursprung |
| `pdf/fluidi_sensor-PTH-drl_map.pdf`, `…NPTH…` | Bohrplan |
| `pdf/fluidi_sensor_layout_lagen.pdf` | alle Lagen (Cu, Silk, Mask, Fab, Elektrodenumriss User.2), je Seite |
| `pdf/fluidi_sensor_bestueckung_F.pdf` / `_B.pdf` | Bestückungsplan F, Testpads B |
| `fluidi_sensor_cpl_jlc.csv` (+ `_rotationen.csv`), `fluidi_sensor_pos_kicad.csv` | CPL JLC-Format (ohne DNP, ohne Antenne/Testpads) |
| `fluidi_sensor_bom_jlc.csv` | BOM (aus dem Schaltplan, `run_all.sh`) |
| `fluidi_sensor.step` | 3D für die Kollisionsprüfung; Ersatzmodelle U1 (TI RGE0024H), BT1 (KiCad 3034), L1 (Murata DFE201610P); **D1 ohne Modell** (0.6 mm) |
| `render/fluidi_sensor_top.png`, `_bottom.png`, `_kopf_top.png` | Renderbilder |
| Lagenaufbau | Kap. 1 (in der Platine als `stackup`) |

**JLC-Rotationen** (Tabelle `docs/references/matthewlai_JLCKicadTools_cpl_rotations_db_2026-11-07.csv`,
DRITTQUELLE, nicht von JLC): SOT-23 −90 (Q1, Q2), QFN-24 +270 (U1), SOT-353 +180 (U2, U4–U6) sind in der CPL
angewendet. Ohne Korrektur: 0402, 1206, SOT-563 (U3), 3225/3215, TS-1088, 1615, WPN2016, 3034. **Alle Rotationen in
der JLC-Vorschau („Confirm Parts Placement“) Teil für Teil prüfen**, besonders U1 (Pin 1), Q1/Q2, U3, D1, Y1.

## 9 Befunde an Schnittstellen (Abstimmung nötig)

| Nr | Stufe | Befund | Vorschlag |
|---|---|---|---|
| L-1 | **kritisch** (Sicherheit/Projektleitung) | Pads im Zellfach (Clip-VBAT, Minuspad, TP1–TP3) lassen sich ohne Via nicht anschliessen: Schott verbietet Aussenkupfer. Umgesetzt: 5 **Via-in-Pad, gefüllt und überkupfert** (JLC POFV, bei 4 Lagen kostenpflichtig, Preis offen), DRC-Regel „nur in `VIP_FACH`“. Widerspricht wörtlich „keine Vias im Fach“ (S2-W03, R2-W01 Nr. 2), entspricht REQ-MECH-05 („gefüllt und abgedeckt mit Begründung“) | Entscheid Sicherheit. Variante: TP1–TP3 auf B ins Band (dann nur 2 VIP; Programmieren nur vor dem Einschieben) |
| L-2 | wichtig (Mechanik) | Clip-Pads (KiCad-Footprint 3034, Lage aus Kap. 5) ragen 0.37 mm in Z3 (bis Y 22.83, Schott-Verguss beginnt Y 22.7 – 0.13 mm Luft) und 0.07 mm in Z5B (bis Y 46.07). Clipkörper laut Footprint x −4.4…11.8 statt −7.0…9.1 | Mechanik prüft mit `fluidi_sensor.step` (KiCad-Modell 3034); ggf. Zelle 0.4 mm nach unten |
| L-3 | wichtig (Feld) | S-Zuleitungen x −8.0 (L2) / −7.0 (L3) statt −4.9, zweite Zuleitung auf L3 nötig | Cpar/Spanne in der Feldsimulation nachrechnen |
| L-4 | wichtig (Sicherheit) | K-2 umgesetzt: Feld x −9.0…−4.6, Vias tented, Kante ≥ 1.08 mm; K-1/K-3 als DRC-Regeln. PCB_OUTLINE Z5A/Z5B-Text (−9.4, „4 Netze“) auf Rev C nachführen | Mechanik/Sicherheit: PCB_OUTLINE Rev C |
| L-5 | klein | Footprint der Antenne „…_Right“ statt „…_Left“ (Kap. 2) | PCB_OUTLINE Kap. 3 korrigieren |
| L-6 | klein | Guard im Fach als Fläche statt schmaler Bahn (Kap. 3) | PROTOTYP-PRÜFUNG Temperatur |

## 10 Offen / PROTOTYP-PRÜFUNG

- Antenne im Gehäuse: S11 bzw. RSSI messen, Pi-Netz C19/C20 (DNM) und R2 abstimmen (OP-K9); Kunststoff vor der
  Antenne (Stössel/Kappenblock) verstimmt die IFA. 50-Ω-Breite 0.35 mm im JLC-Rechner bestätigen.
- 48-MHz-Abgleich über das Cap-Array (SysConfig), 32-kHz-Frequenz messen (C14/C15 15 pF, CL-Annahme).
- I²C über ≈ 30 mm Innenlage: Flanken messen (100 kHz empfohlen, PINMAP).
- Cpar der Messkette (zwei Zuleitungen, TP5) und Kalibrierung; FR4-Feuchte (Feld Kap. 7).
- Kragenverguss: Tasche, Lunker, Leckstrom (K-7); Zellfach-VIP: Flutung REQ-SAF-05.
- VDD-Fläche auf In2: Einbruch beim Funken mit SPICE-Annahme vergleichen (Messung VDDS).
- Router-Ergebnis ist DRC-sauber, aber nicht von Hand optimiert (lange Umwege einzelner Signale, viele Vias):
  Review der Leitungsführung von LED/UART/Messkette, ggf. Nachbesserung in Rev C.

