# Prüfbericht Phase 4 – Layout Sensor Rev B, Sicht Sicherheit

| | |
|---|---|
| Prüfer | Sicherheits-Agent (mit Veto), frischer Kontext |
| Datum | 2026-11-07 |
| Geprüft | Commit 425174d: `hardware/sensor/fluidi_sensor.kicad_pcb`, `fluidi_sensor.kicad_dru`, `gen/{gen_pcb,pcb_build,pcb_place,pcb_rules}.py`, `out/LAYOUT_REV_B.md` (Kap. 4, 9), `out/gerber/` |
| Vorgaben | REQ-MECH-05/06, REQ-SAF-01/05/06, `docs/interfaces/PCB_OUTLINE.md` Rev B (Z3, Z4, Z5A/Z5B), eigene Auflagen K-1…K-3 (`phase4_sicherheit_kragen_firmware.md`), S2-W03, R2-W01, R2-A3, S3-K1, S3-W4 |
| Ergebnis | **Kein Veto.** Entscheid L-1: **zulässig mit Auflagen** (TP3 entfällt → 4 Via-in-Pad). K-1…K-3 am Board bestätigt. 4 wichtige, 4 kleine Befunde. |

## 1 Selbst ausgeführt

Alle Läufe auf einer Kopie im Scratchpad (KiCad 10.0.8, WSL):

| Prüfung | Ergebnis |
|---|---|
| `kicad-cli pcb drc --schematic-parity --refill-zones --severity-all` | 0 Verletzungen, 0 ungeroutet, 0 Parität |
| dasselbe **ohne** `--refill-zones` (gespeicherte Füllung = Gerber-Grundlage) | 0 / 0 / 0 |
| Ignorierte Prüfungen im Bericht | nur Courtyard fehlt, Bahnende nicht auf Via-Mitte, Tuning-Profil, Footprint-Filter, Bauteiltyp. Keine sicherheitsrelevante Prüfung abgeschaltet |
| Gerber F/In1/In2/B-Cu, F/B-Mask neu exportiert und mit `out/gerber/` verglichen (ohne Kopfzeilen) | **identisch**. Die Gerber entsprechen dem geprüften Board |
| pcbnew-Analyse (`.venv/bin/python`, Skripte im Scratchpad) | Regelflächen, Netze je Zone und Lage, Via-Maske und Via-Füllattribute, Kantenabstände der Innenlagen, VBAT-Führung und -Abstände, Q1-Pinbelegung |

Koordinaten unten: Schnittstellen-Koordinaten (Hilfsursprung 150/30 abgezogen), wie in PCB_OUTLINE.

## 2 Entscheid L-1 – Via-in-Pad im Zellfach

### 2.1 Befund am Board

| Via | Netz | Lage (X/Y) | Pad | Füllung/Kappe (KiCad) | B-Seite |
|---|---|---|---|---|---|
| VIP 1 | /VBAT | 3.00 / 23.65 | Clip-Pad oben (Y 22.83…24.10) | Filling 1, Capping 1 | Lötstopp zu |
| VIP 2 | GND | 3.00 / 34.45 | Minuspad 4 × 4 | 1 / 1 | zu |
| VIP 3 | /UART_TX_PAD | −10.60 / 25.50 | TP1 Ø 1.5 | 1 / 1 | zu |
| VIP 4 | /UART_RX_PAD | −10.60 / 28.50 | TP2 Ø 1.5 | 1 / 1 | zu |
| VIP 5 | GND | −10.60 / 31.50 | TP3 Ø 1.0 | 1 / 1 | zu |

Das untere Clip-Pad (Y 44.80…46.07) hat kein Via. Es hängt über das Clipblech am oberen Pad. Sonst gibt es im Fach
kein Aussenkupfer (geprüft: F/B, Y 20.8…46.1, nur BT1-Pads, TP1–TP3 und die 5 Via-Ringe). Bohrung 0.30 mm,
Ø 0.45 mm. Das liegt im POFV-Bereich 0.15–0.55 mm (`docs/references/JLCPCB_NOTES.md`, Kap. 3 „Via-Abdeckung“).
Der Kantenabstand der VIPs ist ≥ 2.1 mm.

### 2.2 Bewertung

- **VBAT und Minuspad brauchen ein Via, auch in der Variante.** Das Schott verbietet Aussenkupfer (S3-K1). Ein Via ist
  also nötig, und das Via im Pad ist die beste Lage: Es liegt unter Lötstelle bzw. Kontaktfläche, ist überkupfert und hat
  keine eigene Maskenöffnung. REQ-MECH-05 („gefüllt und abgedeckt mit dokumentierter Begründung“) und S2-W03 („Vias im
  Fach gefüllt und gedeckelt **oder** ganz vermeiden“) lassen das zu. R2-W01 Nr. 2 verbietet Vias unter der Zelle
  „ausser dem Minuspad“. Das VIP liegt im Minuspad, das VBAT-VIP ausserhalb der Zellfläche (Zelle Y 24.45…44.45).
  „Keine Vias im Fach“ war die Wunschlösung ohne Kosten. Sie ist mit Schott und Clip-Pad auf F geometrisch nicht
  erreichbar.
- **Feuchte, Kriechweg, Kurzschluss:** Das Fach ist nach REQ-SAF-05 der Raum, der im Einzelfehler geflutet wird. Seine
  F- und B-Seite liegen im selben Raum. Ein durchgehendes Via verbindet also keine zwei Räume. Den Weg zum
  Elektronikraum sperren Schott-Verguss (Aussenlagen ohne Kupfer) und K-3 (Innenlagen ≥ 1 mm zur Kante). Mit einem
  gefüllten und überkupferten Via bleibt als zusätzlicher Weg nur ein Fehler der Kappe (Lunker, Riss), über den Feuchte
  an die Hülse und von dort entlang der Glasfaser (CAF) zu Innenlagenkupfer gelangt. Die Folge wäre ein
  hochohmiger Leckstrom (Selbstentladung, Korrosion), kein niederohmiger Kurzschluss. VBAT liegt ohnehin offen
  im Fach (Clip, Zelle selbst). Die Zusatzgefahr durch die 4 VIPs ist klein gegenüber dem, was die Zelle im gefluteten Fach
  ohnehin bewirkt.
- **TP1/TP2 (UART) sind unkritisch.** Hinter 2 × 100 kΩ (R9/R10, R11/R12, im Band, > 10 mm getrennt, R2-A3 am Board
  bestätigt) bleibt die Energie vernachlässigbar (R2.1: ≤ 55 µA im Einzelfehler).
- **TP3 (GND) ist ein neues Kurzschlussziel** (Befund W-2). Er ist für die Programmierung unnötig, denn der
  Dummy-Zellen-Adapter bekommt GND über das Minuspad, und laut `docs/manuals/INSTALL_FIRMWARE_TOOLS.md` Z. 139 sind
  die Federstifte nur auf RX/TX vorgesehen.
- **Variante „TP1–TP3 auf B ins Band“:** Sie spart 3 VIPs, aber POFV bleibt wegen VBAT/Minuspad trotzdem nötig. Die
  Kosten ändern sich also nicht, und JLC füllt bei POFV ohnehin alle Vias der Platine. Die Folgen:
  1. Programmieren geht nur vor dem Einschieben.
  2. Nach dem Schott-Verguss ist kein UART-Zugang mehr möglich. Ein Sensor mit defektem Image ist damit nicht mehr
     zu retten, und der Ablauf „Taster halten + Dummy-Adapter einsetzen“ (`scripts/flash_sensor.py` Z. 11) entfällt.

  Der Sicherheitsgewinn gegenüber „TP1/TP2 im Fach, TP3 weg“ ist gering (2 Pads hinter 200 kΩ). Ich verlange die
  Variante deshalb nicht.

### 2.3 Entscheid

**L-1: zulässig mit Auflagen** (die Stufe „kritisch“ in LAYOUT_REV_B Kap. 9 ist damit erledigt, sobald A-1…A-5
umgesetzt sind):

| Nr | Auflage |
|---|---|
| A-1 | **TP3 entfällt** (auch sein VIP). Im Fach bleiben 4 VIPs: VBAT, Minuspad, TP1, TP2. Adapter-GND über das Minuspad. |
| A-2 | **POFV verbindlich in den Fertigungsunterlagen** (Befund W-4): Bestellnotiz/Checkliste „Via Covering: Epoxy filled & capped“, Hinweis in `LAYOUT_REV_B.md` Kap. 8 und im Bestell-README. Ohne POFV wird **nicht** bestellt. |
| A-3 | Eingangsprüfung Musterplatinen: Sichtprüfung der 4 VIP-Pads (keine Delle/Öffnung, Lupe ≥ 10×), an einer Opferplatine ein Querschliff durch das VBAT-VIP (Füllung ohne Lunker). **PROTOTYP-PRÜFUNG** |
| A-4 | Testplan REQ-SAF-05 (Fach geflutet, 24 h, Zelle eingesetzt): zusätzlich Isolationswiderstand VBAT–GND und TX/RX–GND (Platine ohne Zelle, 3 V, vor und nach der Flutung), Zellstrom protokollieren. **PROTOTYP-PRÜFUNG** |
| A-5 | Begründung nach REQ-MECH-05 als Entscheid in `docs/requirements/DECISIONS.md` und in PCB_OUTLINE Rev C, Z4: „Vias nur als Via-in-Pad, POFV, nur VBAT/GND/TX/RX“. Die DRC-Regel `VIP_FACH` bleibt. |

## 3 K-1…K-3 am Board verifiziert

| Auflage | Prüfung (pcbnew, gespeicherte Füllung) | Ergebnis |
|---|---|---|
| **K-1** Dichtstreifen nur GND/Guard + Sonde | Regelfläche `Z5A_DICHT` Y 49.30…52.00, x ±11, alle Cu-Lagen (deckt z 4.2…1.5 und damit den Streifen z 2.0…4.2 ab). Netze im Streifen: In1 `GND`, `/PROBE_SENSE`; In2 `GND`, `/PROBE_SENSE`; F und B **leer** | **erfüllt** |
| | U3-Netze (SENS_PWR, SDA, SCL) enden im Feld. Unterster Via-Rand Y 49.095 (z 4.405 ≥ 4.4) | erfüllt |
| | Regelbedingung nutzt die richtigen Netznamen (`GND`, `/PROBE_SENSE`, im Board so vorhanden) | ok |
| **K-2** Feld, Vias | `Z5B_FELD` x −9.00…−4.60, Y 46.70…49.10 (= z 6.8…4.4). 5 Vias (4 × x −5.0, GND x −8.7), Kantenabstand min **1.075 mm**. C24-Pad bis x −8.76 (1.24 mm) | **erfüllt** |
| | Tenting: **alle 146 Vias** ohne Öffnung in F.Mask und B.Mask (`IsOnLayer(F/B_Mask)` = false, Board-Vorgabe Tenting F/B = ein). Die VIPs liegen in der Pad-Öffnung, B-Seite zu | **erfüllt** |
| **K-3** Innenlagen Schott/Fach ≥ 1.0 | `Z3_Z4_INNEN` Y 20.82…46.10 deckt Z3 (20.8…23.2) und Z4 (23.2…46.0) ab. Kleinster Kantenabstand In1/In2 **1.048 mm** (Fachzone am Bogen der Schulter). VBAT auf In2 bei x 11.8 (1.05 mm) | **erfüllt** |
| Keine Vias im Schott | keine Via mit Y 20.8…23.2. Die nächsten Vias liegen bei Y 20.5 (Rand 20.725, im Band) und Y 23.65 (VBAT-VIP, Rand 23.425) | **erfüllt** |
| Kein Aussenkupfer im Schott | **nicht erfüllt**: Das VBAT-Clip-Pad reicht bis Y 22.83 (0.37 mm in Z3). Die DRC findet das nicht, weil `Z3_SCHOTT` Pads nicht sperrt | → W-1 |
| Sonde/Dichtstreifen ≥ 1.25 | Guard/Elektroden x ±8.75 → 1.25 mm, DRC-Regel `Z5A_Z7_SONDE` aktiv | erfüllt |

Abdeckungslücken der Regelflächen (Befunde W-1, K-1):
- `Z3_SCHOTT` sperrt auf F/B keine Pads.
- `Z4_FACH` endet bei Y 46.1, `Z5_KRAGEN` beginnt erst bei 46.1. PCB_OUTLINE setzt Z5B aber ab 46.0 an. Deshalb geht
  das untere Clip-Pad (bis 46.07) durch.
- Für die Innenlagen im Kragen Y 46.1…49.3 gilt nur die allgemeine Regel 0.3 mm. Heute ist dort alles ≥ 1.075 mm.

## 4 Versorgungspfad

- **Q1 AO3401A, Verpolschutz:**
  - SOT-23, Pin 1 G = GND, Pin 2 S = VDD, Pin 3 D = VBAT.
  - Die Pinbelegung stimmt mit `docs/datasheets/AOS_AO3401A_Datasheet_Rev3.1.pdf` S. 1 (Top View, Pin-1-Punkt bei G)
    überein.
  - Body-Diode D→S leitet in Normalrichtung. Bei verpolter Zelle gilt V_GS = 0, Q1 sperrt.
  - V_GS ≈ −3 V liegt innerhalb ±12 V. R_DS(on) < 85 mΩ bei −2.5 V (DS S. 1).
  - **Richtig.**
- **VBAT-Führung:**
  - Weg: VIP (3.0/23.65) → In2 0.30 mm nach x 11.8 → entlang der rechten Kante durchs Schott → In2 bei Y 6.35 quer
    durch das Band → Via (−12.25/6.6) → F.Cu 0.20 mm → Q1-Drain.
  - Länge 51 mm. R ≈ 0.19 Ω bei 15.2 µm Innenkupfer (gerechnet: ρ_Cu 1.72e-8 Ωm, Querschnitt 0.3 mm × 15.2 µm).
  - Bei CR2032-Strömen (mA) ist das bedeutungslos, die Bahn wirkt auch nicht als Sicherung.
- **Abstände VBAT–GND (gerechnet aus Kupferpolygonen):**

  | Lage | Abstand | Ort |
  |---|---|---|
  | F.Cu | 0.200 mm | bei Q1, Band |
  | B.Cu | 0.202 mm | Via-Ring, Band |
  | In1 | 0.302 mm | |
  | In2 | 0.277 mm | GND-Via-Ring im Band |
  | Fach und Schott | 0.30 mm | Zonenabstand der GND-Fachfläche |

  - Im Band (dichter Elektronikraum, Lötstopp) reicht das für 3 V.
  - Im Fach liegen VBAT und GND 0.30 mm nebeneinander im Laminat, 1.05 mm von einer flutbaren Kante → K-2 (CAF).
  - VBAT–VDD auf In2 0.25 mm (VBAT-Bahn in der VDD-Fläche). Ein Schluss überbrückt nur Q1. Das ist ein Doppelfehler
    zusammen mit einer verpolten Zelle, also zulässig.
- **Kurzschluss beim Einsetzen (L-2):**
  - Die Clip-Pads (VBAT) liegen je **0.13 mm** von den Vergusskanten entfernt (Schott z 31.0 → Y 22.7, Kragen z 7.3 → Y 46.2).
  - Der Clip selbst ist Blech auf VBAT. Ein Kurzschlussziel auf GND gibt es nur im Fach: Minuspad und **TP3**
    (W-2). Siehe W-1 und W-3.

## 5 Befunde

| Nr | Stufe | Befund | Vorschlag |
|---|---|---|---|
| **LS-W1** | wichtig | **Clip-Pads an beiden Vergusskanten.** Pad-Spanne Y 22.83…46.07 (23.24 mm), verfügbar zwischen Schott-Verguss (Y 22.7) und Kragen-Verguss (Y 46.2) sind 23.5 mm. Es bleiben **0.13 mm je Seite**, und die Lage im Kern hat eine Toleranz von ± 0.2 mm (PCB_OUTLINE Kap. 2). Das Pad kann also in den Verguss ragen. Das verkürzt die Dichtlänge des Schotts auf F (1.2 mm Verguss, bis −0.33 mm) bzw. drückt Epoxid/ASA auf die Clip-Lötstelle (Riss → loser Clip, R2-W01 Nr. 4). Der Vorschlag „Zelle 0.4 mm nach unten“ aus L-2 **geht nicht**: Die Spanne ist schon mittig (Mitte 34.45 = Mitte der Lücke), das untere Pad läge dann 0.27 mm im Kragen-Verguss. DRC-Lücke: `Z3_SCHOTT` sperrt keine Pads, `Z5_KRAGEN` beginnt bei 46.1 statt 46.0. | (a) Pad-Spanne auf das Katalogminimum W 23.1 mm kürzen (Aussenkanten je 0.07 mm, Pad-Tiefe ≥ 1.27 mm = .050″, `Keystone_3034_Catalog_M65.pdf` S. 1 Fig. 1 „Pad Layout“). (b) Mechanik: Abstand Pad–Vergusskante **≥ 0.3 mm inkl. Toleranz** (Fach um ≈ 0.4 mm verlängern oder die Toleranz der Lage im Kern einengen), nachweisen in `check_sensor.txt` mit der Footprint-Padgeometrie. (c) DRC: `Z3_SCHOTT` mit `pads=True`, `Z5_KRAGEN` ab Y 46.0 bzw. eine Regel „Pad-Rand ≥ 0.3 mm zu den Vergusskanten“. |
| **LS-W2** | wichtig | **TP3 (GND) neben dem Zellrand.** Die Zellkante (Becher +) liegt laut `Energizer_CR2032_Datasheet_EU0920.pdf` S. 1 nur **≥ 0.10 mm** über der Minus-Kontaktebene („Applies to top edge of gasket or edge of crimp“). Liegt die Zelle beim Wechsel lose oder schräg auf der Platine (Becherrand auf TP3, Minuskappe auf dem Minuspad, z. B. Zellmitte x ≈ −0.5), ist die Zelle kurzgeschlossen. Das widerspricht dem Sinn von R2-W01 Nr. 2. TP3 hat für die Programmierung keinen Zweck (Adapter-GND = Minuspad). | **TP3 und sein VIP streichen** (Auflage A-1). TP1/TP2 bleiben (hinter 200 kΩ, unkritisch). |
| **LS-W3** | wichtig | **Clip-Geometrie Footprint ↔ Mechanik.** Im Footprint liegt der Clipkörper bei x −4.4…11.8. Der gerade Quersteg sitzt 7.39 mm von der Zellmitte, das passt zum Katalogmass B 7.4 (`Keystone_3034_Catalog_M65.pdf` S. 1, Tab. 3034: B .291 (7.4), L 16.1). **ANNAHME:** B ist ab Zellmitte bemasst. Das Mechanikmodell nimmt x −7.0…9.1 an („geschlossenes Ende −x“). Ist der Footprint richtig, ragt die Zelle 2.6 mm über das −x-Ende (Richtung Testpad-Streifen) und 1.2 mm über +x hinaus. Dann gelten der Halteweg „2.40 mm bis Seitenwand“ (`check_sensor.txt` Z. 10) und die Einschubrichtung „+x, ausserhalb der Testpads“ (PCB_OUTLINE Z4) nicht mehr gesichert. | Mechanik mit dem KiCad-3D-Modell (`out/fluidi_sensor.step`) nachrechnen: Einschubrichtung, Ausschubweg, Halt durch die Hülse (R2-W01 Nr. 4). Einschubweg darf nicht über TP1/TP2 führen, sonst die Pads ≥ 3 mm aus dem Überstreichbereich legen. PROTOTYP-PRÜFUNG R2-W01 Nr. 3 (schräg, verkehrt, halb, CR2025; Zellstrom) mit dem echten Clip. |
| **LS-W4** | wichtig | **POFV nirgends in den Fertigungsunterlagen.** Die Gerber sind ohne X2 erzeugt. Füllung/Kappe stehen nur als KiCad-Via-Attribut im Board, `out/` enthält keine Bestellnotiz. `COSTS_REV_B.md` enthält den POFV-Aufpreis nicht (`scripts/cost_model.py` Z. 131: +20.3 USD je Bestellung, ENIG + POFV). Wird ohne POFV bestellt, bleiben offene Bohrungen in Clip-Pad, Minuspad und Testpads. Lot fliesst in das Clip-Via, die Lötstelle wird schwach, und das Fach hat offene Bohrungen (REQ-MECH-05 verletzt). | Auflage A-2 (Bestellnotiz, Checkliste, Hinweis Kap. 8) und Kosten in `COSTS_REV_B.md` nachführen (Projektleitung). Freigabe der Bestellung erst mit POFV. |
| **LS-K1** | klein | K-3 gilt nur bis Y 46.1. Im oberen Kragenbereich (Y 46.1…49.3), dessen Oberkante zum gefluteten Fach zeigt, gilt für Innenlagen nur 0.3 mm. Heute ist alles ≥ 1.075 mm, die Regel schützt aber künftige Änderungen nicht. | `Z3_Z4_INNEN` bis Y 49.3 erweitern (oder eigene Regel „Innenlagen Kragen ≥ 1.0“). |
| **LS-K2** | klein | VBAT–GND im Fach und Schott auf In1/In2 mit 0.30 mm Abstand bzw. ≈ 0.375 mm Bohrungswand VBAT-VIP → GND-Fläche, 1.05 mm von einer flutbaren Kante. Das gibt CAF-Reserve nur knapp. Die Folge wäre Leckstrom, kein Brand. | Netzklassen-Regel VBAT in `Z3_Z4_INNEN`: Abstand ≥ 0.5 mm zu GND (Zonenabstand, Antipad am VBAT-VIP). Kostet nichts. |
| **LS-K3** | klein | Warnsymbol „CR2032 Verschluckgefahr“ ist nicht auf B im Fach (PCB_OUTLINE Z4 B, S3-W4), nur „laut Auftrag am Gehäuse“ (Hülse innen, vertieft). Der Entscheid ist nicht in `DECISIONS.md` belegt. | Entscheid dokumentieren. Silkscreen auf B zusätzlich anbringen (kostenlos, Fläche frei). |
| **LS-K4** | klein | R2-W01 Nr. 1: Belegt ist nur der Höchstwert der Minus-Kontaktfläche, **17.70 mm** (Energizer S. 1), kein Mindestwert. Das 4 × 4-Pad (Halbdiagonale 2.83 mm) liegt bei jeder realen CR2032 innerhalb, die Aussage stützt sich aber auf eine **ANNAHME**. Ausserdem fehlen `docs/reviews/FMEA.md` (REQ-SAF-02) und ein Testplan (REQ-DOC-03). Die Prüfungen aus A-3, A-4, LS-W3 und K-7 haben noch keinen Ort. | Panasonic/Renata-Masszeichnung mit Kappen-Ø anfragen (OP-K7). Den Testplan vor der Musterbestellung anlegen, FMEA-light vor der Fertigungsfreigabe (Sicherheits-Agent). |

Bestätigt ohne Befund:
- DRC 0/0/0 mit und ohne Neufüllung.
- Gerber gleich Board.
- Alle Vias tented.
- K-1, K-2, K-3 erfüllt.
- Keine Vias im Schott.
- Kragen: nur U3/C24 im Feld auf F.
- Q1-Verpolschutz richtig.
- R2-A3 (UART-Widerstände getrennt, im Band) erfüllt.
- VBAT-Bahnbreiten ausreichend.

## 6 Veto

**Kein Veto.** Kein Befund ist kritisch. LS-W1…LS-W4 und die Auflagen A-1…A-5 sind vor der Musterbestellung umzusetzen.
LS-W4 und A-2 blockieren die Bestellung, bis POFV festgeschrieben ist. Wird ohne POFV bestellt, wäre das ein kritischer
Befund mit Veto (REQ-MECH-05).

Bitte je Befund antworten: *umgesetzt* / *abgelehnt (Grund)*.
