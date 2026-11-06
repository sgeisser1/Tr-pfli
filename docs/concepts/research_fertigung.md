# Tröpfli – Recherche Fertigung und Kosten (Phase 2)

| | |
|---|---|
| Datum | 2026-11-06 |
| Ersteller | Agent fertigung-dfm |
| Grundlagen | `REQUIREMENTS.md` v1.0 (Kap. 10, RB-07, RB-09, REQ-MECH-04/05/06/11/16, REQ-DES-03), `CLIENT_INPUT.md` |
| Quellen-Details | `docs/references/JLCPCB_NOTES.md` (alle URLs mit Abrufdatum) |
| Kostenmodell | `scripts/cost_model.py` (`.venv/bin/python scripts/cost_model.py`) |
| Status | Entwurf zur Prüfung |

Kennzeichnung: **[JLC]** offizielle JLC-Seite, **[OFFIZIELL]** Behörde/Kurier, **[DRITTQUELLE]**,
**ANNAHME** (unbelegt). Wechselkurs: **1 USD = 0.8189 CHF** (EZB-Referenzkurse 2026-11-06,
EUR/USD 1.1165, EUR/CHF 0.9143).

## 1 Kernaussagen für die Konzepte

1. **Kleinstes Prototyp-Los (RB-09):** 5 Leiterplatten (PCB-Mindestmenge [JLC]), davon **mindestens 2
   bestückt** (PCBA-Mindestmenge 2 [JLC]). Dass 3 Platinen unbestückt mitgeliefert werden, belegen nur
   Drittquellen sowie die JLC-Montagebedingungen (Fall „five PCBs and two PCBA“). Ja: man muss mehr
   Leiterplatten abnehmen als bestücken lässt (5 statt 2).
2. **Economic PCBA nur 0.8–1.6 mm, 2–50 Stk, einseitig bestückt** [JLC]. Eine **2.0-mm-Platine erzwingt
   Standard PCBA**: Setup 25.56 statt 8.18 USD, Schablone 8.21 statt 1.53 USD, Fixture 16.42 USD,
   Feeder 1.53 USD je Teiletyp (auch Basic), Mindestmass 70 × 70 mm → Panel mit Rändern nötig. Mehrkosten
   rund **+45 USD einmalig pro Bestellung** plus Panelaufwand (Beispiel siehe Abschnitt 6). Für REQ-MECH-11
   (1.6 vs. 2.0 mm) ist das ein Kostenargument für **1.6 mm**.
3. **Programmieren und Conformal Coating bietet JLC nur bei Standard PCBA** [JLC]. Programmieren nur nach der
   Bestückung über eine Schnittstelle (kein Vorprogrammieren von Chips), ca. 8 USD + 8 USD/h. → Konzept soll
   das Programmieren selbst lösen (RB-08: USB/UART-Bootloader oder günstiger Adapter), Versiegelung der Sonde
   selbst (REQ-MECH-07).
4. **Kosten Extended Parts:** Economic 3.07 USD je Extended-Teiletyp und Bestellung, Basic gratis [JLC].
   Bei ~3–5 Extended-Typen ≈ 9–15 USD je Bestellung → nur Einmalkosten, nicht Stückkosten.
5. **Epoxy filled & capped Vias** bei 4 Lagen kostenpflichtig (gratis erst ab 6 Lagen [JLC]); Preis nicht
   abrufbar. Billiger und sicherer: **keine Vias im nassen Bereich** (REQ-MECH-05), Innenlagen-Elektroden
   über Vias im Kopfbereich anbinden.
6. **Kupfer–Kontur:** JLC verlangt ≥ 0.2 mm (gefräst); REQ-MECH-06 fordert ≥ 1.0 mm → unsere Regel ist
   strenger und bestimmt die DRC-Einstellung.
7. **Logo auf Silkscreen (REQ-DES-03/MECH-16):** Linien ≥ 0.15 mm, Text ≥ 1.0 mm hoch, Verhältnis
   Strichbreite:Höhe 1:6, Abstand zu Pads ≥ 0.15 mm [JLC]. Empfehlung: Logo-Strich ≥ 0.2 mm, Schrift „Tröpfli“
   ≥ 1.5 mm hoch (Reserve; „ö“-Punkte als eigene Flächen ≥ 0.2 mm).
8. **Isolationsdicke über Innenlagen-Elektroden (REQ-MECH-04/11):** Standard-Stackup 4 Lagen hat bei
   **1.6 mm und 2.0 mm dasselbe Prepreg L1–L2: 0.210 mm (7628, Er 4.4)** [JLC, 2.0 mm DRITTQUELLE]. Die
   Dicke 2.0 mm kommt nur aus einem dickeren Kern. Dünner (0.076–0.12 mm) oder dicker (bis 0.646 mm,
   3 × 7628) geht über andere JLC-Vorlagen; ob diese mit Economic PCBA kombinierbar sind, ist offen.
9. **Import CH:** kein Zoll (Industriezölle seit 1.1.2024 aufgehoben), MWST 8.1 % auf Warenwert inkl.
   Versand, **nicht erhoben, wenn der Steuerbetrag ≤ 5 CHF ist** (≈ 62 CHF Warenwert). Darüber kommt die
   Verzollungsgebühr des Zustellers dazu: Post 16 CHF + 3 % des Werts, DHL Express max(3 CHF, 2 % der
   Abgaben). Bei Serienbestellungen ist damit **DHL trotz höherem Porto ähnlich teuer oder billiger** als
   Post-Zustellung (Beispiel Abschnitt 6).

## 2 Mindestmengen [JLC]

| Was | Mindestmenge | Quelle |
|---|---|---|
| Leiterplatte FR-4 (2 und 4 Lagen) | 5 Stk (Stufen 5/10/15/20/25/30/50 …) | jlcpcb.com/pcb-fabrication/fr4-pcb |
| PCBA Economic | 2–50 Stk (je nach Dicke/Farbe 2–30, 5–30 oder 2–50) | capabilities/pcb-assembly-capabilities |
| PCBA Standard | 2–80 000 Stk | ebd. |
| Bestückte ≤ gelieferte PCB | 5 PCB / 2 bestückt möglich, Rest unbestückt (DRITTQUELLE; JLC-Bedingungen erwähnen den Fall) | assembly terms, EasyEDA-Forum, Hack Club |
| Bauteile | LCSC-Mindestabnahme pro Teil (z. B. 0402 oft 50–100 Stk) → Teilesuche, je Teil prüfen | – |

**Empfehlung Prototyp-Los:** 5 PCB, **5 bestückt** wenn die Bauteilkosten klein sind (Einmalkosten bleiben
gleich, 3 zusätzliche Sensoren kosten nur Bauteile + Bestückung), sonst 2 bestückt. Entscheid nach Konzeptwahl.

## 3 Preisbausteine

### 3.1 PCBA (belegt) [JLC, Stand Oct 22, 2026]

| Posten | Economic | Standard | Art |
|---|---|---|---|
| Setup | 8.18 USD | 25.56 USD (einseitig) | einmalig |
| Schablone | 1.53 USD | 8.21 USD | einmalig |
| Extended-Teiletyp (Feeder) | 3.07 USD je Typ | 1.53 USD je Typ (auch Basic) | einmalig |
| Fixture | – | 16.42 USD (1–29 Stk) | einmalig |
| Handlöt-Pauschale (THT) | 3.58 USD | 3.58 USD | einmalig |
| Confirm Parts Placement (optional) | 0.45 USD | 0.45 USD | einmalig |
| SMT pro Lötstelle | 0.0016 USD | 0.0016 USD (min. 0.48 USD/Board) | Stück |
| Handlötung pro Lötstelle | 0.0164 USD | 0.0164 USD | Stück |
| Basic-Parts | Bauteilpreis LCSC, **keine** Ladegebühr | Feeder 1.53 USD je Typ | Stück |
| Pre-reflow Soldering | 0.016 USD/Lötstelle | gleich | **unklar**, im Modell abschaltbar (aus) |
| Programmieren | nicht verfügbar | ca. 8 USD + 8 USD/h | einmalig |
| Conformal Coating (Acryl 50–200 µm) | nicht verfügbar | 6.42 USD Eng. + 0.16 USD/Stk + 0.0048 USD/cm² | gemischt |

### 3.2 Leiterplatte 22 × 150 mm (ANNAHME – im Rechner ablesen)
Der JLC-Rechner ist nicht skriptbar (nur JavaScript, nicht dokumentiert). Belegt ist nur, dass der
Promopreis („$2/5 pcs“) auf ≤ 100 × 100 mm beschränkt ist und 22 × 150 mm daher zum Normalpreis läuft,
dass 4 Lagen 10 × 10 cm „ab 7 USD“ kosten und dass 2.0 mm nicht zu den aufpreisfreien Dicken gehört
(DRITTQUELLE). Die Werte im Kostenmodell sind **Platzhalter (ANNAHME)**:

| Lagen / Dicke | 5 Stk | 10 Stk | 15 Stk | 20 Stk | Status |
|---|---|---|---|---|---|
| 2 L / 1.6 mm | 7 | 9 | 11 | 13 | ANNAHME (USD) |
| 2 L / 2.0 mm | ×1.3 | ×1.3 | ×1.3 | ×1.3 | ANNAHME |
| 4 L / 1.6 mm | 15 | 20 | 25 | 30 | ANNAHME (USD) |
| 4 L / 2.0 mm | ×1.3 | ×1.3 | ×1.3 | ×1.3 | ANNAHME |
| ENIG statt HASL | +10 | | | | ANNAHME |
| Epoxy filled & capped (4 L) | +25 | | | | ANNAHME (DRITTQUELLE nennt 15–25 USD, unbelegt) |
| Farbe ≠ grün | Aufpreis | | | | unbelegt; Economic: nur grün/schwarz bei 1.6 mm ohne Mindestmenge 5 |

**Aufgabe an den Auftraggeber/Orchestrator:** Diese 16 Werte im Rechner (jlcpcb.com/quote, Grösse 22 × 150 mm,
grün, HASL bleifrei, Standardoptionen) ablesen und mit Datum in `PCB_PRICE_USD` und den Aufpreis-Konstanten
eintragen. Dauer ca. 10 min.

### 3.3 Designregeln für das Board (Auszug, Details JLCPCB_NOTES.md §3)

| Regel | 2 Lagen | 4 Lagen | Tröpfli-Vorgabe |
|---|---|---|---|
| Leiterbahn/Abstand min. | 0.10/0.10 mm | 0.09/0.09 mm | ≥ 0.15/0.15 mm (Reserve, kein Aufpreis) |
| Bohrung/Via-Ø min. | 0.15/0.25 mm | 0.15/0.25 mm | ≥ 0.3/0.6 mm (kein Aufpreis, ANNAHME „preferred ≥ 0.2 mm“ genügt) |
| Restring | ≥ 0.18 (empf. 0.25) mm | ≥ 0.15 (empf. 0.20) mm | ≥ 0.15 mm |
| Kupfer–Kontur | ≥ 0.2 mm | ≥ 0.2 mm | **≥ 1.0 mm im Sondenbereich** (REQ-MECH-06) |
| Silkscreen | Linie ≥ 0.15 mm, Text ≥ 1.0 mm | gleich | Logo-Strich ≥ 0.2 mm |
| Konturtoleranz | ± 0.2 mm | gleich | für Gehäusepassung berücksichtigen |
| Dickentoleranz | ± 10 % | gleich | 1.6 mm → 1.44–1.76 mm (Gehäuseschlitz!) |

### 3.4 Lagenaufbau 4 Lagen – Isolationsdicke über Innenlagen

| Dicke | Vorlage | Dielektrikum L1–L2 | Kern | Quelle |
|---|---|---|---|---|
| 1.6 mm | **JLC04161H-7628 (Standard)** | **0.210 mm** 7628, Er 4.4 | 1.065 mm | [JLC] jlcpcb.com/impedance |
| 1.6 mm | JLC04161H-3313 | 0.099 mm, Er 4.1 | 1.265 mm | [JLC] |
| 1.6 mm | JLC04161H-1080 | 0.076 mm, Er 3.91 | 1.265 mm | [JLC] |
| 1.6 mm | JLC04161H-7628E / -7628C | 0.428 / 0.646 mm | 0.600 / 0.150 mm | [DRITTQUELLE] (JLC-API-Abzug 2025-05) |
| 2.0 mm | **JLC04201H-7628 (Standard)** | **0.210 mm** 7628 | 1.465 mm | [DRITTQUELLE] |
| 2.0 mm | JLC04201H-3313 / -1080 | 0.099 / 0.076 mm | 1.665 mm | [DRITTQUELLE] |
| 2.0 mm | JLC04201H-7628A | 0.646 mm (3 × 7628) | 0.600 mm | [DRITTQUELLE] |

Plus Lötstopplack (Dicke von JLC nicht angegeben, ANNAHME 10–30 µm). Prepreg-Werte sind Nenndicken;
ohne Aussenkupfer kann die gepresste Dicke abweichen (ANNAHME, PROTOTYP-PRÜFUNG: Querschliff oder
Kapazitätsmessung). Die vollständige Liste steht in JLCPCB_NOTES.md §4. Für die Feldsimulation (REQ-MECH-11)
empfehle ich die Bandbreite 0.08 / 0.21 / 0.43 / 0.65 mm zu rechnen.

## 4 Versand Schweiz, MWST, Zoll

| Punkt | Wert | Quelle |
|---|---|---|
| Zoll auf PCB/PCBA | 0 (Industriezölle seit 1.1.2024 aufgehoben) | [OFFIZIELL] BAZG |
| MWST | 8.1 % auf Warenwert + Versand (alle Kosten bis Bestimmungsort) | [OFFIZIELL] ESTV, BAZG |
| Freigrenze | Abgaben ≤ 5 CHF werden nicht erhoben (≈ 62 CHF Warenwert inkl. Versand) | [OFFIZIELL] BAZG; JLC nennt „5CHF“ |
| Post-Verzollung | 16 CHF (Nicht-EU) + 3 % des Werts, max. 70 CHF; −1.50 bei Online-Zahlung | [OFFIZIELL] post.ch |
| DHL Express | max(3 CHF; 2 % der Abgaben) ohne ZAZ-Konto | [OFFIZIELL] mydhl.express.dhl, ab 1.1.2026 |
| FedEx | 2.5 % der Abgaben, min. 25 CHF | [DRITTQUELLE] |
| UPS | nicht ermittelt | – |
| JLC erhebt MWST für CH vorab? | nein (nur EU/UK erwähnt) | [JLC] customs-Seite |
| Versand Global Standard Direct Line | **ANNAHME 12 USD** (0.2–0.5 kg), Zustellung in CH vermutlich durch Post (ANNAHME) | JLC-Versandrechner nicht abrufbar |
| Versand DHL Express | **ANNAHME 25 USD**; DRITTQUELLE (EU 2025): 21.50 USD rabattiert / 29.51 USD regulär | chiptron.eu |
| Gewicht | ANNAHME 0.15 kg Verpackung + 0.02 kg/Platine → 0.25 kg (5 Stk), 0.45 kg (15 Stk) | – |

## 5 Kostenmodell `scripts/cost_model.py`
- Nur Standardbibliothek. Alle Parameter als Konstanten mit Quelle/Datum oben im Skript, ANNAHMEN markiert.
- Eingabe: BOM als CSV (Teil, Menge/Board, Stückpreis USD bzw. CHF, basic/extended/tht/none,
  von JLC bestückt ja/nein, Lötstellen, LCSC-Mindestabnahme, Verlustzugabe, Quelle JLC/LOKAL),
  Lagen, Dicke, PCB-Menge, bestückte Menge, Versandart, PCBA-Art (auto/economic/standard), ENIG, Epoxy-Vias.
- Ausgabe: **Stückkosten pro Sensor** (PCB-Anteil, Bauteile, Bestückung, MWST-Anteil, lokale Teile wie
  Energiequelle/Gehäusematerial) und **Einmalkosten pro Bestellung** (Setup, Schablone, Extended/Feeder,
  Fixture, Handlöt-Pauschale, unbestückte Mehr-PCB, Mindestabnahme-Überschuss, Versand, MWST-Anteil,
  Verzollungsgebühr), in USD und CHF.
- Logik: Economic automatisch, wenn Dicke ≤ 1.6 mm und 2–50 Stk, sonst Standard. MWST auf die gesamte
  JLC-Rechnung, anteilig auf Stück- und Einmalkosten verteilt. Kartenaufschlag 1.5 % (ANNAHME).
- Nicht modelliert: Panel für Standard PCBA (Hinweis wird ausgegeben), Expressfertigung, Coupons.

## 6 Beispielergebnis (BEISPIEL-BOM, fiktiv – nur zur Demonstration)
BOM: 3 Extended-Typen (MCU 49 Lötstellen, Sensor, Taster), 5 Basic-Typen, 1 THT-Halter von JLC handgelötet,
Knopfzelle und Gehäusematerial lokal (2.20 CHF). PCB-Preise und Versand = ANNAHMEN aus 3.2/4.

| Szenario | PCBA | Stückkosten CHF | Einmalkosten CHF | Bestellung total CHF |
|---|---|---|---|---|
| Prototyp 4 L 1.6 mm, 5 PCB / 2 bestückt, GSDL | economic | 6.98 | 36.89 | 50.84 |
| Prototyp 4 L 1.6 mm, 5 PCB / 5 bestückt, GSDL | economic | 6.98 | 29.33 | 64.21 |
| Serie 4 L 1.6 mm, 15/15, GSDL | economic | 6.16 | 49.93 | 142.32 |
| Serie 4 L 2.0 mm, 15/15, GSDL | **standard** | 6.90 | **90.83** | 194.39 |
| Serie 2 L 1.6 mm, 15/15, GSDL | economic | 5.32 | 49.58 | 129.41 |
| Serie 4 L 1.6 mm, 15/15, DHL | economic | 6.16 | 46.11 | 138.50 |

Ablesbar: (a) Prototyp-Bestellungen bleiben knapp unter der 5-CHF-Abgabengrenze → keine MWST/Verzollung;
(b) bei der Serie kostet die Post-Verzollung (≈ 18 CHF) mehr als der Portounterschied zu DHL;
(c) 2.0 mm kostet wegen Standard PCBA ≈ 41 CHF mehr Einmalkosten; (d) 2 statt 4 Lagen spart bei den
ANNAHME-Preisen ≈ 0.85 CHF pro Sensor. Die Zahlen sind wegen der PCB-/Versand-ANNAHMEN **nicht** belastbar,
nur die Struktur.

## 7 Unsicherheiten und offene Punkte
| # | Punkt | Wirkung | Vorgehen |
|---|---|---|---|
| U1 | PCB-Preise 22 × 150 mm und Aufpreise (2.0 mm, ENIG, Farbe, Epoxy-Vias) unbelegt | Stückkosten ± 1–2 CHF | Rechner ablesen (3.2) |
| U2 | Versandkosten CH unbelegt | Einmalkosten ± 10 CHF; beeinflusst 62-CHF-Grenze | Rechner/Checkout ablesen |
| U3 | „Pre-reflow Soldering 0.016 USD/Lötstelle“ unklar | ≤ 1 USD/Board bei ~70 Lötstellen | im Checkout prüfen |
| U4 | Economic-Tabelle: Zuordnung 2/4 Lagen fehlt im HTML | Farbwahl/ENIG bei 4 Lagen | Rechner |
| U5 | Economic mit Nicht-Standard-Stackup? | Wahl der Isolationsdicke | Rechner/Support |
| U6 | 5 PCB / 2 bestückt nur Drittquelle | Prototyp-Los | Rechner |
| U7 | Stackup-Werte 2.0 mm nur Drittquelle (Stand 2025-05) | Feldsimulation | jlcpcb.com/impedance mit 2.0 mm prüfen |
| U8 | Zustellung GSDL durch Post (Verzollungsgebühr 16 CHF + 3 %) ist ANNAHME | Einmalkosten Serie | erste Lieferung dokumentieren |
| U9 | Extended-Gebühr: Preisseite 3.07 USD vs. FAQ „$3“ | gering | neuere Preisseite verwendet |
| U10 | LCSC-Mindestabnahmen und Verlustzugaben je Teil | Einmalkosten | bei Bauteilwahl je LCSC-Nummer erfassen |
