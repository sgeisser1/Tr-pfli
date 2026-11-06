# Tröpfli – Recherche Energiequelle und Versorgungspfad (Phase 2)

| | |
|---|---|
| Dokument | `docs/concepts/research_energie.md` |
| Zweck | Grundlage für den Variantenvergleich REQ-ENE-01 (Knopfzelle vs. LiPo) |
| Ersteller | firmware-energie |
| Datum | 2026-11-06 (alle Preise/Lagerbestände: Abruf 2026-11-06) |
| Grundlagen | `docs/requirements/REQUIREMENTS.md` v1.0 (5.4, 6.2, 6.3, RB-03), Prüfbericht `docs/reviews/phase1_requirements_firmware-energie.md` |
| Rechnung | `scripts/energy_budget.py` (`.venv/bin/python scripts/energy_budget.py`, Parametertabelle mit `--params`) |
| Register | `docs/datasheets/_staging/INDEX_energie.csv` |
| Status | Entwurf zur Prüfung, keine Entscheidung |

Seitenangaben beziehen sich auf die PDF-Seite. **ANNAHME** heisst: nicht aus einem Datenblatt belegt. **PROTOTYP-PRÜFUNG** heisst: erst am Muster nachweisbar.

---

## 0 Kurzfazit

1. **Knopfzelle erfüllt die Laufzeit mit allen vier SoCs.** Pessimistisch nach REQ-ENE-08 erreicht die CR2032 mit 1 min Reaktionszeit 27–40 Monate (Muss: 12). Die CR2450N erreicht 60–86 Monate. Der LiPo erreicht 5.7–6.4 Monate pro Ladung (Muss: 3) (Tabelle 4.3).
2. **Die 65-°C-Kopftemperatur (RB-03) schliesst den LiPo faktisch aus.** Die Renata-LiPo-Packs erlauben Entladen nur bis **60 °C**, Lagern bis **45 °C** und Laden von 0–45 °C (z. B. `Renata_ICP401230UPR_Datasheet_V02.pdf`, S.1). REQ-SAF-LI-09 verlangt deshalb eine konstruktive Massnahme mit Messnachweis. Bei den Knopfzellen erlauben Renata CR2450N/CR2477N **85 °C** und verlangen eine Rücksprache erst **über 70 °C**. Bei der Renata CR2032 MFR beginnt diese Rücksprachezone schon **über 60 °C**, 65 °C liegt also darin.
3. **Neuer Konflikt beim Pufferkondensator (wichtig).** REQ-ENE-06 verlangt einen Einbruch ≤ 0.2 V bei 100 Ω. Pessimistisch braucht das 84–225 µF *effektiv* (Tabelle 4.5), je nach DC-Bias also 170–450 µF nominal. Die Datenblattgrenze des Isolationswiderstands (Murata: > 50 Ω·F) entspricht bei 3 V einem zulässigen Leckstrom von **6 µA je 100 µF**. Wendet man REQ-ENE-08 wörtlich an (Maximalwert), reisst die CR2032 das 8-µA-Budget (REQ-ENE-09) immer. Bei grossem C sinkt sie auch unter 12 Monate. CR2450N/CR2477N bleiben auch dann über 12 Monate. Der reale Leckstrom liegt vermutlich weit tiefer, ist aber nur am Muster messbar.
4. **Empfehlung (vorläufig):** Knopfzelle **Renata CR2450N** mit SMD-Halter mit vergoldeten Kontakten. Dazu ein P-MOSFET als Verpolschutz, keramischer Puffer und ein Batteriefachdeckel mit unverlierbarer Schraube. Die **CR2032** bleibt die Option für einen kleineren Kopf, falls der Muster-Leckstrom des Puffers ≤ 1 µA gemessen wird. Die LiPo-Variante wird nach REQ-SAF-03 nicht empfohlen: Sie ist weniger sicher (Temperatur, Laden), teurer, braucht mehr Teile und hält das Ruhestromziel ≤ 5 µA nur mit Typwerten.

---

## 1 Knopfzellen

### 1.1 Datenblattwerte

| Zelle | Kapazität (Bedingung) | Max. Dauerstrom | Temperatur | Selbstentl. | Masse | Mass | Quelle |
|---|---|---|---|---|---|---|---|
| **Renata CR2032 MFR** | 225 mAh, Standardentladung 0.4 mA, 2.0 V | 3.0 mA (70 % Ausbeute, 2.0 V, 23 °C) | −30…+85 °C, **> 60 °C Renata konsultieren** | < 1 %/a (23 °C) | ~2.8 g | Ø20 × 3.2 | `Renata_CR2032MFR_Datasheet_Rev07.pdf` S.1 |
| **Renata CR2450N** | 540 mAh, 0.8 mA | 3.0 mA | −40…+85 °C, > 70 °C konsultieren | < 1 %/a | ~5.9 g | Ø24.5 × 5.0 | `Renata_CR2450N_Datasheet_Rev08.pdf` S.1 |
| **Renata CR2477N** | 950 mAh, 1.0 mA | 2.5 mA | −40…+85 °C, > 70 °C konsultieren | < 1 %/a | ~8.3 g | Ø24.5 × 7.7 | `Renata_CR2477N_Datasheet_Rev08.pdf` S.1 |
| Panasonic CR2032 | 225 mAh, 0.2 mA | – | −30…+85 °C, ≥ 70 °C konsultieren | – | 2.8 g | Ø20 × 3.2 | `Panasonic_CR2032_Datasheet_2026-02.pdf` S.1 |
| Panasonic CR2450 | 620 mAh, 0.2 mA | – | −30…+85 °C, ≥ 70 °C konsultieren | – | 6.2 g | Ø24.5 × 5.0 | `Panasonic_CR2450_Datasheet_2026-02.pdf` S.1 |
| Panasonic CR2477 | 1000 mAh, 0.2 mA | – | −30…+85 °C, ≥ 70 °C konsultieren | – | 10.5 g | Ø24.5 × 7.7 | `Panasonic_CR2477_Datasheet_2024-07.pdf` S.1 |
| Maxell CR2450HR | 550 mAh, 0.2 mA | – | **−40…+125 °C** | – | 6.8 g | Ø24.5 × 5.0 | `Maxell_CR2450HR_Datasheet_table.pdf` S.1 |
| Varta CR2450 (6450) | 570 mAh, 5.6 kΩ, 2.0 V | – | Entladung −20…**65 °C**, Lager bis 70 °C | – | 6.2 g | Ø24.5 × 5.0 | `Varta_CR2450-6450_Datasheet_2014-09.pdf` S.1 |
| Ansmann CR2450 | 630 / **550 min** mAh, 0.4 mA | 5 mA, Puls 20 mA | −20…**60 °C** | – | 6.4 g | Ø24.5 × 5.0 | `Ansmann_CR2450_Datasheet_5020112.pdf` S.1 |
| Energizer CR2032 | 254 mAh, 15 kΩ, 2.0 V | Puls 6.8 mA (Diagramm) | – | ~1 %/a (21 °C) | 3.0 g | Ø20 × 3.2 | `Energizer_CR2032_Datasheet_EU0920.pdf` S.1 |

**Pulsbelastbarkeit und Innenwiderstand.** Renata nennt für alle drei Zellen nur den Dauerstrom (Fussnote **: „70 % Ausbeute bis 2.0 V bei 23 °C“), keinen Pulsstrom und keinen Innenwiderstand. Die Pulsdaten stammen aus TI SWRA349 (`docs/appnotes/TI_SWRA349_WhitePaper.pdf`, S.3 Tab. 1, S.5 Fig. 6, S.7–8). Dort steigt der Innenwiderstand einer CR2032 gegen Entladeende auf > 30–100 Ω. Mit Pufferkondensator erreicht die schlechteste Zelle 82 % der Kapazität, ohne Puffer liefern einzelne Marken nur etwa 50 %. Das deckt sich mit der Annahme von REQ-ENE-08 (75 % mit Puffer). **Für die CR2450N/CR2477N gibt es keine Pulsmessung** (ANNAHME: gleicher Faktor; PROTOTYP-PRÜFUNG).

**Kälte.** Ist für ein Büro nicht relevant (Betrieb 5–45 °C). Die Renata-Kurven „Cell capacity at various loads“ zeigen bei −20 °C deutlich weniger Kapazität, bei 0 °C wenig Verlust (S.1, nur Diagramm, nicht abgelesen).

**Wärme.** Die Kapazitätskurven von Renata zeigen bei 70 °C mindestens so viel Kapazität wie bei 23 °C (S.1, Diagramm „Cell capacity at various loads“). Für die Selbstentladung bei 50 °C fehlt ein Datenblattwert. Im Modell gilt pessimistisch **2 %/a** (ANNAHME). Renata schreibt allgemein: „Do not expose batteries to high temperatures, moisture or direct sunlight“ (`docs/appnotes/Renata_3VLithium_SafetyGuidelines.pdf`, S.1).

### 1.2 Preise Schweiz (Händler-Einzelpreis inkl. MWST; Quelle: Suchergebnis-Auszug vom 2026-11-06, Seiten selbst blockiert (HTTP 403) → **vor Bestellung prüfen**)

| Zelle | Preis | Händler |
|---|---|---|
| Renata CR2032 | CHF 2.65 bzw. CHF 3.00 pro Stück (ab 2 Stk) | galaxus.ch Art. 10677225; digitec.ch Art. 10677225 |
| Renata CR2450N | CHF 3.70 bis 4.50 pro Stück | galaxus.ch / digitec.ch Art. 24168676 |
| Renata CR2477N | CHF 5.70 bis 5.90 pro Stück | galaxus.ch / digitec.ch Art. 19860483 |
| Varta CR2032 (10er) | CHF 1.70 pro Stück | digitec.ch Art. 45270472 |

Maxell CR2450HR: LCSC C115412 hat **Lager 0** (USD 1.45). Maxell liefert laut Webseite nur an Gerätehersteller. Damit fällt die Zelle für das Projekt praktisch aus.

### 1.3 Halter (LCSC, JLC-bestückbar; es gibt **keine Basic-Halter**, alle Extended)

| Zelle | LCSC | Teil | Typ | Lager | Preis USD (Menge) | Kontakte | Datenblatt |
|---|---|---|---|---|---|---|---|
| CR2032 | **C7501066** | TE BAT-HLD-001 | SMD-Clip, Minuspol = PCB-Pad | 1683 | 0.96 (1) / 0.70 (30) | Phosphorbronze vernickelt | `TE_BAT-HLD-001_Drawing_RevE1.pdf` S.1 (0.761 g; 22.9 × 15.3 × 4.2 mm; Rev. E: „increase battery retention“) |
| CR2032 | C70377 | Q&J CR2032-BS-6-1 | SMD | 57793 | 0.14 (1) / 0.11 (1000) | Phosphorbronze | `QJ_CR2032-BS-6-1_Drawing.pdf` (nur Zeichnung) |
| CR2032 | C5213768 | Keystone 3034TR | SMD-Clip | 664 | 0.39 / 0.36 | Phosphorbronze (Katalog) | `Keystone_3034_Catalog_M65.pdf` |
| CR2450 | **C964809** | MYOUNG BS-24-B4AA016 | SMD, LCP-Gehäuse | 2042 | 0.58 / 0.40 (50) | Phosphorbronze **vergoldet** | `MYOUNG_BS-24-B4AA016_Drawing_A0.pdf` S.1 (−25…85 °C; Pads 37 mm Spannweite, H 7.5 mm) |
| CR2450 | C964813 | MYOUNG BS-24-B4AK014 | SMD | 1158 | 0.59 / 0.41 | Phosphorbronze vernickelt | (nur JLC-Attribute) |
| CR2477 | **C2979175** | MYOUNG MY-2477-02 | SMD-Clip, Minuspol = PCB-Pad | 4727 | 0.37 / 0.24 (250) | C5191 vernickelt | `MYOUNG_MY-2477-02_Drawing_A0.pdf` S.1 (1.315 g; 37 × 22.9 mm, H 8.3 mm) |

**Verschluckschutz (REQ-SAF-CC-04).** Keiner der Halter verlangt Werkzeug: Clip-Halter lassen die Zelle mit dem Fingernagel herausschieben. Der Schutz muss also vom **Gehäusedeckel mit unverlierbarer Schraube** kommen. Der Deckel soll die Zelle zusätzlich in den Halter drücken (Fallfestigkeit REQ-SAF-CC-02, z. B. Elastomer-Noppe; ANNAHME, Mechanik). Die Halterauswahl allein erfüllt die Anforderung nicht.

**Kontaktmaterial (REQ-SAF-CC-02).** Die vergoldete Variante (C964809) ist gegen Feuchte im Kopf die robusteste. Bei Clip-Haltern (BAT-HLD-001, MY-2477-02) ist der Minuspol ein **Leiterplatten-Pad**: Oberfläche **ENIG** (vergoldet) wählen, nicht HASL (ANNAHME: Kosten bei JLC prüfen).

**Kurzschluss im Halter.** Bei Clip-Haltern kann eine Zelle schräg eingesetzt werden und dann mit dem Rand Clip und Pad berühren. Das ist am Muster zu prüfen (PROTOTYP-PRÜFUNG). Ein Halter mit Kunststoffgehäuse (C964809) führt die Zelle besser.

### 1.4 Verpolschutz (REQ-SAF-CC-01)

Eine verkehrt eingelegte Zelle liegt bei Clip-Haltern mit dem Pluspol (Becher) auf dem Minus-Pad. Damit liegt **Verpolung elektrisch an**, ein elektrischer Schutz ist nötig.

| Variante | Teil (LCSC, Typ) | Verlust im Betrieb | Leckstrom | Bewertung |
|---|---|---|---|---|
| **P-MOSFET** im Plus-Pfad, Gate an GND | **AO3401A C15127 Basic**, USD 0.08 | RDS(on) < 85 mΩ @ −2.5 V → 15 mA × 0.085 Ω ≈ 1.3 mV (`AOS_AO3401A_Datasheet_Rev3.1.pdf` S.1–2); VGS(th) −0.5…−1.3 V | Betrieb: IGSS ≤ 100 nA (@ ±12 V, S.2); verpolt: IDSS ≤ 1 µA (25 °C) / 5 µA (55 °C) (S.2) | **empfohlen** (Basic). Bei 2.0 V Zellspannung ist RDS(on) nicht spezifiziert (nur ab −2.5 V); Ausweichteil siehe nächste Zeile |
| P-MOSFET mit tiefem VGS(th) | DMG2305UX-7 C150470 Extended, USD 0.57 | RDS(on) ≤ 200 mΩ @ −1.8 V (`Diodes_DMG2305UX_Datasheet_DS36196Rev8.pdf` S.2) | IDSS ≤ 1 µA, IGSS ≤ 100 nA (S.2) | technisch besser bei Zellende, Extended |
| Schottky in Serie | RB751S-40 C8524 Extended | VF 0.37 V @ 1 mA (`CJ_RB751S-40_Datasheet.pdf` S.1), bei 10 mA mehr | IR 0.5 µA @ 30 V | **ungeeignet**: 0.4 V Verlust verletzt die Abschaltschwelle 2.0 V (REQ-ENE-06) |
| Halterbauform | – | 0 | 0 | kein Halter auf LCSC mit nachweislichem mechanischem Verpolschutz gefunden |

**Hinweis zu REQ-SAF-CC-03 (keine Ladung).** Ein eingeschalteter P-MOSFET leitet in **beide** Richtungen. Er schützt die Zelle also **nicht** gegen Einspeisung über Programmier- oder Messpads. Vorschlag für die Hardware: Programmierpads so platzieren, dass sie **nur bei entnommener Zelle** zugänglich sind (z. B. unter der Zelle bzw. im Halterbereich). Damit ist REQ-SAF-CC-03 konstruktiv erfüllt. Alternativ zwei Rückstromsperren (Diode und Widerstand) im Pfad jeder externen Quelle, die Ladung nicht über den VDD-Knoten in die Zelle gelangen lassen. Das entscheidet der Hardware-Agent.

### 1.5 Pufferkondensator (REQ-ENE-06)

| LCSC | Teil | Typ | Preis USD | Lager | Leckgrenze (Datenblatt) |
|---|---|---|---|---|---|
| **C15008** | Samsung CL31A107MQHNNNE 100 µF 6.3 V X5R 1206 | **Basic** | 0.11 / 0.07 (300) | 1.6 Mio | Katalog: IR nach Dauerprüfung ≥ 25 MΩ·µF (`Samsung_CL31A107MQHNNNE_Catalog_2015-11.pdf` S.55); typenspezifisches Datenblatt nicht gefunden |
| C77085 | Murata GRM31CR60J107ME39L 100 µF 6.3 V X5R 1206 | Extended | 0.13 / 0.09 | 72160 | **IR > 50 Ω·F** (`Murata_GRM31CR60J107ME39L_Datasheet.pdf` S.2 Pos. 5) → bei 3 V max. **6 µA** pro 100 µF |
| C96123 | Samsung CL31A476MPHNNNE 47 µF 10 V 1206 | Basic | 0.17 | 468647 | – |
| C400951 | Samsung CL32A227MQVNNNE 220 µF 6.3 V 1210 | Extended | 0.80 | 20625 | – |

- **DC-Bias.** Die lokale Murata-Spezifikation enthält keine DC-Bias-Kurve, SimSurfing ist nicht erreichbar. Im Modell bleiben bei 3 V **50 %** der Nennkapazität (ANNAHME, PROTOTYP-PRÜFUNG mit LCR-Messung oder Entladekurve).
- **Bedarf** (Skript, Tabelle 4.5): realistisch 15–66 µF *effektiv* (30–130 µF nominal), pessimistisch 84–225 µF effektiv. Am kleinsten ist der Bedarf beim EFR32BG22 und beim CH592 mit DC-DC.
- **Leckstrom.** Die Datenblattgrenze ist ein Abnahmekriterium und kein typischer Wert. Sie wäre aber nach REQ-ENE-08 („Maximalwert“) zu verwenden. Vorschlag für die Anforderungen: Leckstrom des Puffers **am Muster messen** (Ziel ≤ 0.5 µA bei 45 °C) und bis dahin die Datenblattgrenze als Sensitivitätsfall rechnen (Fall B im Skript).
- **Temperatur.** X5R ist bis 85 °C spezifiziert. Die Kapazität sinkt bei 65 °C weiter (ANNAHME −10 %).

---

## 2 LiPo-Variante

### 2.1 Zellen (Renata, Schweiz; alle mit Schutzschaltung „Safety Circuit“)

| Zelle | Kapazität min/nom | Masse | Mass (max) | Laden | Entladen | Lagern | Quelle |
|---|---|---|---|---|---|---|---|
| ICP501022UPM | 75 / 80 mAh | ~2.6 g | 24 × 10 × 5.5 mm | 0…45 °C, 4.2 V, 0.5 C | −20…**60 °C** | −20…**45 °C** | `Renata_ICP501022UPM_Datasheet_V02.pdf` S.1 |
| ICP390831PR | 80 / 85 mAh | ~2.8 g | 33 × 8.7 × 4.3 | 0…45 °C | −20…60 °C | −20…45 °C | `Renata_ICP390831PR_Datasheet_V01.pdf` S.1 |
| **ICP401230UPR** | 125 / 130 mAh | ~3.5 g | 31 × 12.7 × 4.5 | 0…45 °C | −20…60 °C | −20…45 °C | `Renata_ICP401230UPR_Datasheet_V02.pdf` S.1 |
| ICP501230PS-03 | 130 / 135 mAh | ~3.3 g | 31.5 × 12 × 5.5 | 0…45 °C | −20…60 °C | −20…45 °C | `Renata_ICP501230PS-03_Datasheet_V04.pdf` S.1 |
| ICP402025PC-01 | 150 / 155 mAh | ~4.0 g | 27.5 × 20.5 × 4.3 | 0…45 °C | −20…60 °C | −20…45 °C | `Renata_ICP402025PC-01_Datasheet_V02.pdf` S.1 |

- **Schutzschaltung.** Die Datenblätter enthalten keine Schwellen und keinen Ruhestrom der Schutzschaltung (ICP501230: „Safety Circuit – On request“). **Bei Renata anfragen.**
- **Temperatur (RB-03, REQ-SAF-LI-09).** 65 °C Kopftemperatur liegt **über** der Entladegrenze (60 °C) und **weit über** der Lagergrenze (45 °C). Das Fenstersims-Szenario ist damit ausserhalb der Spezifikation. Nach REQ-SAF-LI-09 braucht es eine konstruktive Massnahme (Wärmedämmung, Zelle im Schatten des Kopfes) mit Messnachweis, sonst ist die Variante nicht zulässig. Mit diesen Datenblättern ist das **nicht erfüllbar ohne Zusatzmassnahme**.
- **Bezug und Preis.** Renata LiPo-Packs werden über Distributoren (Future Electronics u. a.) vertrieben. Einen CHF-Preis habe ich nicht gefunden. ANNAHME: CHF 4–8 pro Stück. No-Name-Packs mit 100 mAh kosten ca. EUR 4 (z. B. soldered.com), REQ-ENE-08 verlangt aber Markenzellen.
- **Selbstentladung.** Kein Datenblattwert. Im Modell 2 %/Monat realistisch, 3 %/Monat pessimistisch (ANNAHME).

### 2.2 Lade-, Schutz- und Versorgungsschaltung (LCSC, Abruf 2026-11-06)

| Funktion | LCSC | Teil | Typ | Lager | USD (1/10–30) | Ruhestrom aus Akku | Schlüsselwerte | Bewertung |
|---|---|---|---|---|---|---|---|---|
| **Lader** | **C202311** | TI BQ21040DBVR SOT-23-6 | Ext | 2346 | 0.41 / 0.30 (150) | IOUT(PDWN) ≤ **1 µA** (VIN = 0) (`TI_BQ21040_Datasheet_RevD.pdf` S.5) | IN abs. max **30 V** (S.3), **OVP 6.5–6.8 V** (S.4), Ladestrom per ISET-Widerstand (KISET 540 AΩ typ., S.5) → Hardwaregrenze; Vorladung 20 % (S.5); TS 10-k-NTC: Laden nur **0–45 °C** (S.6, Kap. 8.3) | **empfohlen**. Achtung: TS offen → „TTDM“-Modus ohne Temperaturüberwachung (S.3). **237 kΩ von TS nach GND** ist Pflicht (S.3), damit ein offener NTC als „kalt“ gilt und nicht lädt. TS auf GND → IC aus |
| Lader alt. | C81080 | TI BQ24040DSQR WSON-10 | Ext | 111696 | 0.42 / 0.30 | ≤ 1 µA (`TI_BQ24040_Datasheet_RevH.pdf` S.7) | 30 V, OVP; **JEITA**: lädt 45–60 °C mit 4.1 V weiter (S.9 VTS-45°C/VTS-60°C) | ungeeignet für Renata (Laden nur bis 45 °C) |
| Lader alt. | C527572 / C2871905 | TI BQ25100(B)YFPR DSBGA-6 | Ext | 0 / 6 | 1.66–3.10 | **75 nA** max (`TI_BQ25100_Datasheet_RevC.pdf` S.5) | 30 V, OVP 6.52–6.82 V (S.5), 10–250 mA, lädt 45–60 °C reduziert weiter (S.5) | technisch gut, aber kein Lager, WLCSP |
| verworfen | C424093 | Microchip MCP73831T-2ACI/OT | Ext | 5968 | 0.76 | IDISCHARGE 0.15 typ / 2 µA (`Microchip_MCP73831_Datasheet_RevH.pdf` S.4) | **kein NTC-Eingang**, VDD abs. max **7 V** (S.3) | verletzt REQ-SAF-LI-02 und -08 |
| verworfen | C16581 | TOPPOWER TP4056 ESOP-8 | Ext (Preferred) | 110459 | 0.19 | Sleep −1/−2 µA (`TOPPOWER_TP4056_Datasheet.pdf` S.5) | VCC abs. max **8 V** (S.2), kein OVP | nur mit externem OVP-IC; verworfen |
| **Schutz-IC** | **C183096** | TI BQ29700DSER WSON-6 | Ext | 3239 | 0.55 / 0.36 | INORMAL **4 µA typ / 5.5 µA max** (`TI_BQ2970_Datasheet_RevI.pdf` S.5) | Überladung, Tiefentladung, Überstrom; externe Doppel-N-FET nötig | empfohlen (TI-Original, Max-Wert spezifiziert) |
| Schutz-IC alt. | C351410 | PUOLOP DW01A SOT-23-6 | Ext | 95973 | 0.05 | ICC **3.0 typ / 6.0 µA max** (`PUOLOP_DW01A_Datasheet.pdf` S.4) | VOC 4.25–4.35 V, VOD 2.4–2.6 V (S.4) | günstig, Max-Wert höher |
| Doppel-N-FET | C908265 | FUXINSEMI FS8205A SOT-23-6 | Ext | 21975 | 0.07 | IDSS ≤ 1 µA @ 20 V (`FUXINSEMI_FS8205A_Datasheet.pdf` S.2) | zu Schutz-IC | – |
| Schutz-IC + FET | C80628 | XySemi XB5353A SOT-23-5 | Ext | 934 | 0.09 | IOPE 2.8 typ / 6 µA max (`XySemi_XB5353A_Datasheet.pdf` S.3) | integrierter FET 54 mΩ | Alternative, wenig Lager |
| **LDO** | **C3747031** | TI TPS7A0230PDBVR (3.0 V) | Ext | 27756 | 0.32 / 0.26 | IGND **25 nA typ / 60 nA max** (`TI_TPS7A02_Datasheet_RevC.pdf` S.6) | VIN 1.5–6.0 V (S.5) | **empfohlen** (LiPo 4.2 V > VDD max der SoCs 3.6/3.8 V) |
| LDO alt. | C5446 | Torex XC6206P332MR-G | **Basic** | 498663 | 0.15 | IDD 1.0 typ / 3.0 µA max (`Torex_XC6206_Datasheet_ETR0305-004b.pdf` S.4) | VIN ≤ 6 V | Basic, aber 3 µA max frisst das LiPo-Budget |
| LDO alt. | C14289 | Holtek HT7533-1 SOT-89 | **Basic** | 244565 | 0.14 | ISS 2.5 typ / 4.0 µA max (`Holtek_HT7533_Datasheet_V2.80.pdf` S.5) | VIN ≤ 30 V | Basic, Ruhestrom zu hoch |
| LDO alt. | C841192 | Richtek RT9080-33GJ5 | Ext | 23773 | 0.12 | 2 µA (Titel, `Richtek_RT9080_Datasheet_DS9080-05.pdf` S.1) | VIN 1.2–5.5 V | – |
| USB-C | C456012 | SHOU HAN TYPE-C 6P (nur VBUS/CC/GND) | Ext | 1.0 Mio | 0.04 | – | Rating 5 V 3 A, −30…85 °C (`SHOUHAN_TYPE-C-6P_Datasheet.pdf` S.3) | Senke mit 2 × 5.1 kΩ an CC (keine PD-Aushandlung) |
| TVS VBUS | C148209 | Littelfuse SMAJ20A | Ext | 2267 | 0.10 | IR ≤ 1 µA @ 20 V (nur bei VBUS) | VR 20 V, VBR 22.2–24.5 V, VC 32.4 V (`Littelfuse_SMAJ_Datasheet.pdf` S.2) | 20 V spannungsfest, klemmt unter 30 V abs. max des BQ21040 bei kleinen Strömen |
| PPTC VBUS | C2984676 | DOWO 1206 500 mA/24 V | Ext | 10119 | 0.09 | – | Vmax 24 V (`DOWO_PPTC1206-500mA-24V_Datasheet.pdf` S.1) | REQ-SAF-LI-08 |
| NTC | C77131 | Murata NCP15XH103F03RC 0402 | Ext | 302530 | 0.02 | – | 10 kΩ, B 3380 | thermische Kopplung an Zelle (Kleber/Federkontakt, Mechanik) |

**Ruhestrom Lade- und Schutzschaltung (REQ-ENE-09 [LI] ≤ 5 µA).** Typ: 25 nA + 0.2 µA (ANNAHME) + 4.0 µA = **4.2 µA**. Max: 60 nA + 1.0 µA + 5.5 µA = **6.6 µA**. Dazu kommt die unbekannte Schutzschaltung im Zellpack (Skript Abschnitt 7). → **Nur mit Typwerten erfüllbar, nach REQ-ENE-08 (Max-Werte) nicht.** Ohne zweite Schutzschaltung auf der Platine wäre es erfüllbar. REQ-SAF-LI-04 verlangt diese aber.

**Tiefentladung.** Der DW01A schaltet erst bei 2.4–2.6 V ab, der BQ29700 bei 2.8 V (`TI_BQ2970_Datasheet_RevI.pdf` S.3, Device Comparison). Renata nennt 3.0 V als Entladeschluss. Die Firmware muss deshalb bei ≥ 3.0 V abschalten, und die Hardwareschwelle liegt darunter. Ob das REQ-SAF-LI-04 genügt, beurteilt der Sicherheits-Agent.

---

## 3 Spannungsregelung

| SoC | VDD-Bereich | Interner Regler | Externer Regler bei Knopfzelle | bei LiPo (4.2 V) |
|---|---|---|---|---|
| CC2340R5 | 1.71–3.8 V ([CC] S.18) | DC-DC ab 2.2 V, darunter automatisch GLDO ([CC] S.18) | **nein** | ja (> 3.8 V) |
| nRF52832 | 1.7–3.6 V ([N52] S.17) | LDO oder DC-DC (+ L/C) ([N52] S.76) | **nein** | ja |
| EFR32BG22 | 1.71–3.8 V ([BG22] S.18) | DC-DC, in Regelung erst ab 2.2 V, darunter Bypass ([BG22] S.18) | **nein** | ja |
| CH592F | 1.75–3.6 V ([CH] S.152) | DC-DC optional ([CH] Kap. 5.4) | **nein** | ja |

Die Knopfzelle (3.0–2.0 V) speist alle vier SoCs direkt. Ein externer Regler würde nur Ruhestrom und Verlust bringen. Beim LiPo ist ein LDO nötig, empfohlen der **TPS7A02** (25 nA). Basic-LDOs (XC6206, HT7533) kosten 1–4 µA und damit 20–80 % des LiPo-Ruhestrombudgets.

SoC-Datenblätter für diese Rechnung: [CC] `docs/datasheets/TI_CC2340R5_Datasheet_SWRS272F.pdf` (inhaltsgleich mit meiner Scratchpad-Kopie, md5 geprüft); [CH] `docs/datasheets/WCH_CH592_Datasheet_V1.9.pdf` (englisch; Werte gleich wie die chinesische V1.8 aus LCSC, die ich zuerst benutzt habe); nur im Scratchpad `.../scratchpad/energy2/soc/`: [N52] Nordic nRF52832 PS **v1.0** (v1.9 hinter Cloudflare nicht ladbar) und [BG22] SiLabs EFR32BG22C112 Data Sheet **Preliminary Rev. 0.5** (via LCSC; silabs.com „Access Denied“).

---

## 4 Energiemodell und Laufzeit (`scripts/energy_budget.py`)

### 4.1 Modell

- **Profil REQ-ENE-04:** 6 automatische und 2 manuelle Messungen pro Tag, jeweils mit Verbindung (50 ms, ANNAHME). LED-Standardmuster 6 × 20 ms bei 2 mA. Pessimistisch kommt das Muster „Giessen nötig“ dazu (1×/min, 12 h/Tag, 5 ms; REQ-UI-07). 1 OTA pro Jahr (200 kB, ANNAHME).
- **Erreichbarkeit:** verbindbares Advertising auf 3 Kanälen. Das Intervall folgt aus der Reaktionszeit mit 2 Chancen (10 % Fehlrate je Fenster, 5 s Aufbau, ANNAHME): **27.5 s (1 min), 57.5 s (2 min), 147.5 s (5 min)**.
- **Sonnenprofil RB-03:** 4 h/Tag bei 50 °C. Der Ruhestrom-Faktor bei 50 °C ist **1.35** (aus [CC] S.35 Fig. 7-7 abgelesen, ~0.75 → ~1.0 µA). Der Tagesmittelfaktor 1.058 gilt für alle SoCs (ANNAHME).
- **Pessimistisch (REQ-ENE-08):** Ruhestrom-Typwert × 1.5 × Temperaturfaktor (die SoC-Datenblätter nennen keine Max-Werte). Funkströme ohne DC-DC (GLDO/LDO/Direktbetrieb), Ereignisladung × 1.5 (ANNAHME), Gesamtzuschlag +20 %. Nutzbar 75 % (Knopfzelle mit Puffer) bzw. 80 % (LiPo, ANNAHME). Selbstentladung Knopfzelle 2 %/a, LiPo 3 %/Monat (ANNAHME).
- **Board-Ruhestrom** ausser SoC: 0.5 µA pessimistisch (ANNAHME, bis zum Schaltplan), Verpol-FET 0.1 µA (IGSS), MLCC 0.5 µA (Fall A, ANNAHME) bzw. 6 µA (Fall B, Datenblattgrenze 100 µF).
- **SoC-Werte** (Typwerte, Tabelle in `--params`):

| SoC | Schlaf (RTC + LFXO + RAM) | TX 0 dBm | RX | CPU | Quelle |
|---|---|---|---|---|---|
| CC2340R5 | 0.74 µA (DC-DC) / 1.15 µA (GLDO) | 5.1 / 9.0 mA | 5.3 / 9.0 mA | 2.6 / 4.1 mA | [CC] S.19–20 Tab. 7.9, 7.10 |
| nRF52832 | 2.2 µA (1.9 µA ohne RAM + 0.3 µA RAM-Erhalt, abgeleitet) | 7.1 (System, DC-DC) / 11.6 mA (LDO) | 6.5 / 11.7 mA | 3.7 mA | [N52] S.74–75, S.19, S.226 |
| EFR32BG22 | 1.40 µA (EM2, alle RAM, LFXO) | 4.1 mA | 3.6 mA | 1.46 mA | [BG22] S.23 Tab. 4.5, S.29 |
| CH592F | 2.2 µA (Sleep, RAM24K + LSE-RTC; „Stichprobe Raumtemperatur“) | 3.5 (DC-DC) / 7.5 mA | 3.4 / 7.1 mA | 2.6 / 3.2 mA | [CH] S.43 Tab. 5-3, S.152, S.154 |

### 4.2 Mittelstrom Knopfzelle (CR2032), µA – REQ-ENE-09 ≤ 8 µA, Schlaf ≤ 3 µA

| SoC | Reaktionszeit | real | pess. A | pess. B (MLCC-Grenze) | Schlaf pess. |
|---|---|---|---|---|---|
| CC2340R5 | 1 min | 1.64 | **5.49** | 12.09 | 2.93 |
| CC2340R5 | 5 min | 1.16 | 4.04 | 10.64 | 2.93 |
| nRF52832 | 1 min | 3.30 | **8.07** | 14.67 | **4.59** |
| nRF52832 | 5 min | 2.66 | 6.17 | 12.77 | 4.59 |
| EFR32BG22 | 1 min | 2.11 | **5.26** | 11.86 | 3.32 |
| EFR32BG22 | 5 min | 1.78 | 4.36 | 10.96 | 3.32 |
| CH592F | 1 min | 2.94 | **7.13** | 13.73 | **4.59** |
| CH592F | 5 min | 2.58 | 5.96 | 12.56 | 4.59 |

Die Spalte „Schlaf pess.“ ist eine pessimistische Rechnung (Typ × 1.5 × Temperaturfaktor plus Board-Annahmen) und keine Messgrösse. REQ-ENE-09 (Schlaf ≤ 3 µA) wird am Muster bei Raumtemperatur gemessen. Rechnerisch halten nur CC2340 und, knapp darüber, EFR32BG22 die 3 µA auch pessimistisch. Bei nRF52832 und CH592 liegt schon der **Typwert** des SoC (2.2 µA) nahe an der Grenze.

### 4.3 Laufzeit in Monaten (realistisch / **pessimistisch A**) – Standardprofil

| SoC | Reakt. | CR2032 | CR2450N | CR2477N | LiPo 125 mAh | LiPo 75 mAh |
|---|---|---|---|---|---|---|
| CC2340R5 | 1 min | >120 / **38.5** | >120 / **82.5** | >120 / **>120** | 15.1 / **6.4** | 10.4 / **4.2** |
| CC2340R5 | 2 min | >120 / **45.6** | >120 / **95.8** | >120 / **>120** | 15.5 / **6.7** | 10.8 / **4.4** |
| CC2340R5 | 5 min | >120 / **50.8** | >120 / **105.2** | >120 / **>120** | 15.8 / **6.8** | 11.0 / **4.6** |
| nRF52832 | 1 min | 78.0 / **27.0** | >120 / **59.7** | >120 / **95.4** | 13.0 / **5.7** | 8.8 / **3.7** |
| nRF52832 | 2 min | 88.1 / **31.4** | >120 / **68.7** | >120 / **108.3** | 13.4 / **6.0** | 9.1 / **4.0** |
| nRF52832 | 5 min | 95.0 / **34.6** | >120 / **75.0** | >120 / **117.1** | 13.7 / **6.2** | 9.4 / **4.1** |
| EFR32BG22 | 1 min | 117.2 / **40.1** | >120 / **85.5** | >120 / **>120** | 14.4 / **6.4** | 9.9 / **4.3** |
| EFR32BG22 | 2 min | >120 / **44.5** | >120 / **93.8** | >120 / **>120** | 14.7 / **6.6** | 10.1 / **4.4** |
| EFR32BG22 | 5 min | >120 / **47.5** | >120 / **99.2** | >120 / **>120** | 14.9 / **6.7** | 10.3 / **4.5** |
| CH592F | 1 min | 86.8 / **30.3** | >120 / **66.4** | >120 / **105.0** | 13.4 / **5.9** | 9.1 / **3.9** |
| CH592F | 2 min | 93.5 / **33.5** | >120 / **72.9** | >120 / **114.2** | 13.6 / **6.1** | 9.3 / **4.0** |
| CH592F | 5 min | 97.7 / **35.7** | >120 / **77.2** | >120 / **>120** | 13.8 / **6.2** | 9.4 / **4.1** |

Werte über 10 Jahre sind durch die Lagerfähigkeit begrenzt und haben keine Aussagekraft. Grenz-Mittelstrom für 12 Monate pessimistisch: CR2032 **18.8 µA**, CR2450N 45.0 µA, CR2477N 79.2 µA.

### 4.4 Sensitivität Fall B: Puffer 100 µF mit Datenblatt-Leckgrenze (6 µA)

| SoC | CR2032 1 min / 5 min | CR2450N 1 / 5 min | CR2477N 1 / 5 min |
|---|---|---|---|
| CC2340R5 | 18.3 / 20.7 | 41.7 / 46.7 | 68.5 / 76.2 |
| nRF52832 | 15.2 / 17.4 | 34.9 / 39.6 | 58.0 / 65.4 |
| EFR32BG22 | 18.7 / 20.2 | 42.4 / 45.5 | 69.6 / 74.4 |
| CH592F | 16.2 / 17.7 | 37.1 / 40.2 | 61.4 / 66.3 |

Die 12 Monate bleiben erfüllt, REQ-ENE-09 (8 µA) nicht mehr. Bei einem Puffer nach pessimistischem Bedarf (170–450 µF nominal → 10–27 µA Leckgrenze) fällt die CR2032 unter 12 Monate (Grenze 18.8 µA). Die CR2450N (45 µA) bleibt darüber.

### 4.5 Pufferkondensator-Bedarf (REQ-ENE-06: ΔV ≤ 0.2 V bei 100 Ω)

| SoC | Fall | Spitze Funk | Einbruch ohne C | Ladung Ereignis | C_eff | C_nenn (50 % DC-Bias) | Leckgrenze C_nenn @ 3 V |
|---|---|---|---|---|---|---|---|
| CC2340R5 | real / pess | 5.3 / 9.0 mA | 0.53 / 0.90 V | 16 / 41 µC | 39 / 162 µF | 78 / 325 µF | 4.7 / 19.5 µA |
| nRF52832 | real / pess | 7.1 / 11.7 mA | 0.71 / 1.17 V | 22 / 53 µC | 66 / 225 µF | 131 / 450 µF | 7.9 / 27.0 µA |
| EFR32BG22 | real / pess | 4.1 / 6.2 mA | 0.41 / 0.62 V | 11 / 25 µC | 15 / 84 µF | 29 / 169 µF | 1.7 / 10.1 µA |
| CH592F | real / pess | 3.5 / 7.5 mA | 0.35 / 0.75 V | 12 / 33 µC | 18 / 123 µF | 37 / 245 µF | 2.2 / 14.7 µA |

Modell: Die Zelle liefert während des Ereignisses (4.2 ms) höchstens ΔV/R = 2 mA, den Rest liefert der Kondensator. Die Ereignisdauer ist in mehreren Teilen ANNAHME. Eine SPICE-Simulation mit realem Stromprofil folgt in der Konzeptphase (REQ-ENE-06 Verif. S).

### 4.6 Budgetanteile (pess. A, CR2032, 1 min)

Den Hauptanteil machen Ruhestrom (SoC 40–59 %, Board und MLCC 15–22 %) und Erreichbarkeit (20–32 %) aus. Messungen kosten 1–2 %, LED ≤ 2 % (REQ-UI-03 ≤ 5 % erfüllt), OTA < 0.5 %.

---

## 5 Vergleich Knopfzelle vs. LiPo

| Kriterium | CR2032 | CR2450N | CR2477N | LiPo 80–130 mAh |
|---|---|---|---|---|
| **Sicherheit** | Primärzelle, keine Ladung; Verschlucken → Deckel mit Schraube | wie CR2032 | wie CR2032 | Laden, Wärme, Aufblähen; VBUS-Schutz, NTC, Schutz-IC, Wasser am Port (REQ-SAF-LI-01…09) |
| **65 °C (RB-03)** | Spezifikation bis 85 °C, **> 60 °C Rücksprache Renata** | **bis 85 °C, Rücksprache erst > 70 °C** | wie CR2450N | **Entladen max. 60 °C, Lagern max. 45 °C** → ausserhalb |
| Laufzeit pess. 1 min | 27–40 Monate | 60–86 Monate | 95 bis > 120 Monate | 5.7–6.4 Monate/Ladung (125 mAh) |
| Robust gegen Puffer-Leckgrenze | nein (REQ-ENE-09 verletzt) | ja (12 Monate) | ja | n/a (kleiner Puffer) |
| Zellmasse | 2.8 g | 5.9 g | 8.3 g | 2.6–4.0 g + Elektronik |
| Halter (Masse, Fläche) | BAT-HLD-001 0.76 g, 22.9 × 15.3 × 4.2 mm | BS-24-B4AA016 37 × ~27 mm, H 7.5 mm | MY-2477-02 1.3 g, 37 × 22.9 mm, H 8.3 mm | Kabel/Stecker; USB-C-Buchse 6P + Abdeckung |
| **Kopfgrösse** (Ziel ≤ 35 × 20 mm, H ≤ 45 mm) | passt gut: Zelle Ø20 auf der senkrechten Kopf-PCB, Tiefe ≈ 1.6 + 4.2 mm | passt, wenn die 37-mm-Achse des Halters in der Kopfhöhe liegt; Tiefe ≈ 1.6 + 7.5 mm | wie CR2450N, Tiefe ≈ 1.6 + 8.3 mm | Zelle 31 × 12.7 × 4.5 passt; USB-C-Port mit Dichtung braucht Platz an der Kopfseite |
| Kosten Energiequelle/Sensor (ANNAHME 1 USD ≈ 0.85 CHF) | Zelle 2.65–3.00 + Halter 0.60 (TE) bzw. 0.10 (Q&J) + FET 0.06 + MLCC 0.1–0.2 ≈ **CHF 3–4** | 3.70–4.50 + 0.40 + 0.3 ≈ **CHF 4.5–5.2** | 5.70–5.90 + 0.25 + 0.3 ≈ **CHF 6.3–6.5** | Zelle 4–8 (ANNAHME) + Lader 0.30 + Schutz 0.40 + FET 0.06 + LDO 0.25 + USB-C 0.04 + TVS/PPTC/NTC 0.2 ≈ **CHF 5.5–9.5**, dazu ca. 7 Extended-Teile (Rüstgebühr) |
| Aufwand | gering | gering | gering | hoch (Ladetests REQ-SAF-LI-08, Nasstest, NTC-Kopplung, FMEA) |
| Betrieb | Wechsel alle ≥ 2–3 Jahre | ≥ 5 Jahre | ≥ 8 Jahre | Laden alle ~6 Monate, nur beaufsichtigt |

**Empfehlung nach REQ-SAF-03:** Die nicht wiederaufladbare Lösung ist sicherer und günstiger und erfüllt die Laufzeit, deshalb **Knopfzelle**. Bevorzugt die **Renata CR2450N**: Schweizer Fabrikat, Temperaturreserve bis 70 °C ohne Rücksprache, Laufzeit robust auch bei der Datenblattgrenze des Puffer-Leckstroms. Dazu Halter **MYOUNG BS-24-B4AA016 (C964809, vergoldet)**, Verpolschutz **AO3401A (C15127, Basic)**, Puffer **Samsung CL31A107MQHNNNE (C15008, Basic)**, 1–2 Stück je nach SoC. Ein SoC mit kleiner Funkspitze (EFR32BG22, CH592 mit DC-DC, CC2340) senkt den Pufferbedarf. Die **CR2032** bleibt als Option für einen kleineren Kopf, falls Muster-Messungen den Leckstrom des Puffers (≤ 0.5 µA) und den Spannungseinbruch bestätigen und Renata 65 °C freigibt.

---

## 6 Probleme und offene Punkte

| Nr. | Stufe | Punkt | Vorschlag |
|---|---|---|---|
| E-01 | wichtig | MLCC-Leckstrom laut Datenblatt (Murata > 50 Ω·F → 6 µA/100 µF @ 3 V) und REQ-ENE-08 (Max-Wert) machen REQ-ENE-09 für jede Zelle unerfüllbar. Der reale Wert ist unbekannt | Orchestrator: Regel für Leckströme passiver Teile festlegen (Messung am Muster statt Datenblattgrenze). PROTOTYP-PRÜFUNG Leckstrom bei 25 und 50 °C |
| E-02 | wichtig | Pufferbedarf pessimistisch 170–450 µF nominal; DC-Bias-Kurve fehlt lokal (Murata SimSurfing gesperrt) | SPICE mit realem Stromprofil; DC-Bias am Muster messen; SoC-Wahl berücksichtigt Spitzenstrom |
| E-03 | wichtig | Renata CR2032 MFR: „> 60 °C Renata konsultieren“ – 65 °C liegt in diesem Bereich | Bei Renata anfragen (CH-Hersteller) oder CR2450N/CR2477N (Grenze 70 °C) |
| E-04 | wichtig | LiPo: Datenblattgrenzen 60 °C (Entladen) / 45 °C (Lagern) < 65 °C; Ruhestrom Lade-/Schutzschaltung max. 6.6 µA > 5 µA; Schutzschaltung im Pack ohne Daten | LiPo-Variante nicht weiterverfolgen (REQ-SAF-03, -LI-09) |
| E-05 | wichtig | BQ21040: offener TS-Pin → TTDM, d. h. Laden **ohne** Temperaturüberwachung (S.3) | falls LiPo: 237 kΩ TS–GND Pflicht, Einzelfehler „NTC offen“ testen |
| E-06 | klein | P-MOSFET leitet im eingeschalteten Zustand rückwärts → schützt nicht vor Ladung über Pads (REQ-SAF-CC-03) | Programmierpads nur bei entnommener Zelle zugänglich (konstruktiv) |
| E-07 | klein | Kein Halter mit Verschlusswerkzeug; Clip-Halter haben einen Minus-Pad auf der PCB | Deckel mit unverlierbarer Schraube und Andrückelement; ENIG-Oberfläche |
| E-08 | klein | Keine Pulsdaten/IR für Renata-Zellen; CR2450N/CR2477N nur aus der Kapazitätskurve bewertet | Muster: Einbruch an vorentladener Zelle messen (Phase-1-Messplan) |
| E-09 | klein | Preise CH nur aus Suchergebnis-Auszügen (Shops blockieren automatisierte Abrufe) | vor Bestellung manuell prüfen |
| E-10 | klein | SoC-Datenblätter: nRF52832 nur PS v1.0, EFR32BG22 nur Preliminary Rev. 0.5, CH592 nur mit „Stichprobenwerten“ bei Raumtemperatur | aktuelle Fassungen durch den Datenblatt-Agenten beschaffen; Werte dann im Skript aktualisieren |
| E-11 | klein | Nicht herunterladbar: Murata CR2032 (Bot-Sperre), Energizer CR2450 (HTML statt PDF), Murata SimSurfing, Renata-Schutzschaltungsdaten („on request“) | im Register vermerkt |

---

## Anhang A – Parametertabelle (`.venv/bin/python scripts/energy_budget.py --params`)

| Schluessel | Wert | Einheit | Quelle |
|---|---|---|---|
| CC.sleep | 7.4e-07 | A | [CC] S.19 Tab. 7.9 Standby LFXT, DCDC, 25 C, typ (kein Max) |
| CC.sleep_ldo | 1.15e-06 | A | [CC] S.20 Tab. 7.9 Standby LFXT, GLDO, typ |
| CC.tx | 0.0051 | A | [CC] S.20 Tab. 7.10 TX 0 dBm, DCDC |
| CC.tx_ldo | 0.009 | A | [CC] S.20 Tab. 7.10 TX 0 dBm, DCDC off |
| CC.rx | 0.0053 | A | [CC] S.20 Tab. 7.10 RX 1 Mbps, DCDC |
| CC.rx_ldo | 0.009 | A | [CC] S.20 Tab. 7.10 RX, DCDC off |
| CC.cpu | 0.0026 | A | [CC] S.19 Tab. 7.9 CoreMark 48 MHz, DCDC |
| CC.cpu_ldo | 0.0041 | A | [CC] S.20 Tab. 7.9 CoreMark, GLDO |
| CC.vmin | 1.71 | V | [CC] S.18 Rec. Op. Cond. VDDS 1.71-3.8 V |
| CC.vmax | 3.8 | V | [CC] S.18 |
| CC.price | 1.59 | USD | JLC C20416850 CC2340R52E0RGER, 1 Stk, Abruf 2026-11-06 |
| N52.sleep | 2.2e-06 | A | [N52] S.75 ION_RAMOFF_RTC 1.9 uA + RAM-Erhalt 0.3 uA (S.75 Differenz, ANNAHME-Ableitung) |
| N52.sleep_ldo | 2.2e-06 | A | wie oben (Ruhestrom unabh. von DCDC, ANNAHME) |
| N52.tx | 0.0071 | A | [N52] S.74 IRADIO_TX0 0 dBm, DCDC, System |
| N52.tx_ldo | 0.0116 | A | [N52] S.226 ITX,0dBM (LDO, Radio only) |
| N52.rx | 0.0065 | A | [N52] S.74 IRADIO_RX0, DCDC, System |
| N52.rx_ldo | 0.0117 | A | [N52] S.226 IRX,1M (LDO, Radio only) |
| N52.cpu | 0.003707 | A | [N52] S.19 CMFLASH 215 / CMFLASH/mA 58 (DCDC 3 V) = 3.7 mA |
| N52.cpu_ldo | 0.00556 | A | ANNAHME x1.5 fuer LDO-Betrieb (kein DS-Wert) |
| N52.vmin | 1.7 | V | [N52] S.17 VDD 1.7-3.6 V (independent of DCDC) |
| N52.vmax | 3.6 | V | [N52] S.17 |
| N52.price | 5.1 | USD | JLC C77540 NRF52832-QFAA-R, 1 Stk, Abruf 2026-11-06 |
| BG.sleep | 1.4e-06 | A | [BG22] S.23 Tab. 4.5 EM2 full RAM, RTC LFXO, typ |
| BG.sleep_ldo | 1.4e-06 | A | wie oben (ANNAHME: kein Wert ohne DC-DC im DS) |
| BG.tx | 0.0041 | A | [BG22] S.29 ITX 0 dBm, System, DC-DC 3 V |
| BG.tx_ldo | 0.00615 | A | ANNAHME x1.5 (kein Wert ohne DC-DC) |
| BG.rx | 0.0036 | A | [BG22] S.29 IRX_ACTIVE 1 Mbit/s, System |
| BG.rx_ldo | 0.0054 | A | ANNAHME x1.5 |
| BG.cpu | 0.001459 | A | [BG22] S.23 Tab. 4.5 EM0 CoreMark 38 uA/MHz x 38.4 MHz |
| BG.cpu_ldo | 0.002189 | A | ANNAHME x1.5 |
| BG.vmin | 1.71 | V | [BG22] S.18 VREGVDD 1.71-3.8 V (DC-DC in Regelung erst ab 2.2 V) |
| BG.vmax | 3.8 | V | [BG22] S.18 |
| BG.price | 1.94 | USD | JLC C1864138 EFR32BG22C112F352GM32-CR, 1 Stk, Abruf 2026-11-06 |
| CH.sleep | 2.2e-06 | A | [CH] S.43 Tab. 5-3 Sleep, RAM24K + RTC(LSE) + Kern erhalten, 2.2 uA (Stichprobe Raumtemp.) |
| CH.sleep_ldo | 2.2e-06 | A | wie oben |
| CH.tx | 0.0035 | A | [CH] S.154 BLE TX 0 dBm, DC-DC |
| CH.tx_ldo | 0.0075 | A | [CH] S.154 BLE TX 0 dBm, Direktversorgung |
| CH.rx | 0.0034 | A | [CH] S.154 BLE RX, DC-DC |
| CH.rx_ldo | 0.0071 | A | [CH] S.154 BLE RX, Direktversorgung |
| CH.cpu | 0.0026 | A | [CH] S.152 IDDC8 Flash 2.6 mA (DC-DC, 8 MHz) |
| CH.cpu_ldo | 0.0032 | A | [CH] S.152 ICC8 Flash 3.2 mA (direkt) |
| CH.vmin | 1.75 | V | [CH] S.152 VDD33 CH592X/F/D 1.75-3.6 V |
| CH.vmax | 3.6 | V | [CH] S.152 |
| CH.price | 0.83 | USD | JLC C39831287 CH592F, 1 Stk, Abruf 2026-11-06 |
| sun.h | 4 | h/Tag | RB-03 Sonnenprofil (ANNAHME des Auftraggebers) |
| sleep.t50 | 1.35 | - | [CC] S.35 Fig. 7-7 abgelesen: Standby ~0.75 uA @25 C, ~1.0 uA @50 C -> Faktor 1.35; fuer alle SoCs uebernommen (ANNAHME) |
| pess.sleep | 1.5 | - | REQ-ENE-08: Typwert x 1.5 (kein Max-Wert in den SoC-Datenblaettern) |
| pess.total | 1.2 | - | REQ-ENE-08: Zuschlag +20 % auf Gesamtverbrauch |
| pess.event | 1.5 | - | ANNAHME: Zuschlag auf Ereignisladung (Stack-Overhead, Streuung), wie Phase 1 |
| ble.t_adv | 0.000376 | s | BLE 1 Mbit/s, 47 B ADV_IND voll (Rechnung) |
| ble.t_rx | 0.00025 | s | ANNAHME: T_IFS 150 us + Lauschfenster je Kanal |
| ble.t_ch | 0.00015 | s | ANNAHME: Kanalwechsel je Kanal (bei RX-Strom gerechnet) |
| ble.t_cpu | 0.0015 | s | ANNAHME: CPU je Funkereignis |
| ble.hfxo | 1.44e-07 | C | [N52] S.106 ISTART_HFXO 0.4 mA x 0.36 ms, fuer alle SoCs (ANNAHME) |
| ble.t_setup | 5 | s | ANNAHME: Verbindungsaufbau + Messung + Anzeige PWA |
| ble.p_miss | 0.1 | - | ANNAHME: Gateway verpasst ein Erreichbarkeitsfenster mit 10 % |
| prof.n_auto | 6 | 1/Tag | REQ-ENE-04 Standardprofil |
| prof.n_man | 2 | 1/Tag | REQ-ENE-04 Standardprofil |
| prof.q_meas | 3e-05 | C | ANNAHME: Messung inkl. Mittelung 10 ms bei 3 mA |
| prof.t_conn | 0.05 | s | ANNAHME: Verbindung + Daten + Abbau, Funk/CPU aktiv |
| led.i | 0.002 | A | ANNAHME (REQ-UI-03, FE-11) |
| led.std | 0.12 | s/Tag | ANNAHME Standardmuster: 6 Blinks x 20 ms pro Tag |
| led.water | 3.6 | s/Tag | REQ-UI-07 Giessen-noetig 1x/min, 12 h/Tag, 5 ms (ANNAHME; nur pessimistisch dauernd aktiv) |
| ota.img | 2e+05 | B | ANNAHME Image-Groesse; 1 Update/Jahr (REQ-ENE-04) |
| ota.flash | 1.675e-05 | C | [CC] S.21 Tab. 7.11 Schreiben+Loeschen 2 kB (fuer alle SoCs ANNAHME) |
| oth.real | 2e-07 | A | ANNAHME: Sensor-Frontend aus, Teiler geschaltet, Taster offen |
| oth.pess | 5e-07 | A | ANNAHME pess. (bis Schaltplan: Pull-ups, ESD-Dioden, Temp.-Sensor) |
| cc.pfet | 1e-07 | A | [AO] S.2 IGSS max 100 nA @ +-12 V (Gate an GND, Verpolschutz) |
| mlcc.rc | 50 | Ohm*F | [GRM] S.2 Pos. 5 Insulation Resistance > 50 Ohm*F (Raumtemp., Nennspannung) |
| mlcc.c | 0.0001 | F | Kandidat GRM31CR60J107ME39L / CL31A107MQHNNNE (Basic C15008), 100 uF 6.3 V |
| mlcc.real | 5e-08 | A | ANNAHME (typisch weit unter Grenzwert; PROTOTYP-PRUEFUNG) |
| mlcc.pess | 5e-07 | A | ANNAHME pessimistisch fuer Fall A; Fall B = Datenblattgrenze |
| mlcc.dcbias | 0.5 | - | ANNAHME: Restkapazitaet 50 % bei 3 V (6.3-V-X5R-1206); Kurve fehlt lokal |
| cc.r_eol | 100 | Ohm | REQ-ENE-06 Nachweisfall Zellinnenwiderstand 100 Ohm |
| cc.dv | 0.2 | V | REQ-ENE-06 Einbruch <= 0.2 V |
| cell.cr2032 | 225 | mAh | [RC32] S.1 Rated Capacity 225 mAh (0.4 mA... 2.0 V) |
| cell.sd_cc | 0.01 | 1/a | [RC32]/[RC45]/[RC77] S.1 Self Discharge < 1 %/a @23 C |
| cell.sd_cc_p | 0.02 | 1/a | ANNAHME pess. (Sonnenprofil 50 C) |
| cell.util_real | 0.9 | - | ANNAHME realistisch mit Puffer-C |
| cell.util_pess | 0.75 | - | REQ-ENE-08: <= 75 % mit Puffer-C |
| cell.cr2450 | 540 | mAh | [RC45] S.1 Rated Capacity 540 mAh |
| cell.cr2477 | 950 | mAh | [RC77] S.1 Rated Capacity 950 mAh |
| cell.li130 | 125 | mAh | [RL4012] S.1 Minimum Capacity 125 mAh (0.2C, 3.0 V) |
| cell.sd_li | 0.24 | 1/a | ANNAHME 2 %/Monat (kein DS-Wert) |
| cell.sd_li_p | 0.36 | 1/a | ANNAHME 3 %/Monat pess. |
| cell.li_util | 0.9 | - | ANNAHME realistisch bis 3.0 V |
| cell.li_util_p | 0.8 | - | ANNAHME pess. (Abschaltung > 3.0 V, Alterung) |
| cell.li80 | 75 | mAh | [RL5010] S.1 Minimum Capacity 75 mAh |
| li.ldo | 2.5e-08 | A | [TPS] S.6 IGND typ 25 nA (25 C) |
| li.ldo_max | 6e-08 | A | [TPS] S.6 IGND max 60 nA (-40..85 C) |
| li.chg | 2e-07 | A | ANNAHME typ (DS nennt nur Max) |
| li.chg_max | 1e-06 | A | [B21] S.5 IOUT(PDWN) max 1 uA, VIN = 0 |
| li.prot | 4e-06 | A | [B29] S.5 INORMAL typ 4 uA (BQ2970, BAT 3.8 V) |
| li.prot_max | 5.5e-06 | A | [B29] S.5 INORMAL max 5.5 uA |
| li.pcm | 1e-06 | A | ANNAHME: zelleninterne Schutzschaltung (Renata: kein Wert) |
| li.pcm_p | 3e-06 | A | ANNAHME pess. |
