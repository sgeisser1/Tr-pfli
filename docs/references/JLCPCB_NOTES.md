# JLCPCB – Notizen zu Regeln, Preisen und Lagenaufbau (Stand 2026-11-06)

Zusammenfassung von HTML-Seiten (keine PDF-Version verfügbar). Jede Angabe mit URL und
Abrufdatum. Kennzeichnung: **[JLC]** offizielle JLC-Seite, **[OFFIZIELL]** Behörde/Kurier,
**[DRITTQUELLE]** nur Orientierung, **ANNAHME** unbelegt.
Auswertung für fluidi: `docs/concepts/research_fertigung.md`. Kostenmodell: `scripts/cost_model.py`.

PDF-Ablage: JLC bietet die Capability- und Preisseiten nur als HTML an; es gibt kein PDF zum
Ablegen. Der JLC-Online-Preisrechner (`cart.jlcpcb.com/quote`) und der Versandrechner
(`jlcpcb.com/shipping`) laufen nur per JavaScript und sind nicht dokumentiert; sie wurden **nicht**
automatisiert abgefragt. Die Werte daraus fehlen hier (siehe Abschnitt 7).

---

## 1 PCBA-Gebühren [JLC]
Quelle: https://jlcpcb.com/help/article/pcb-assembly-price („Last updated on Oct 22, 2026“), abgerufen 2026-11-06.
Hinweis der Seite: „Prices may vary slightly due to exchange rate fluctuations.“

| Posten | Economic PCBA | Standard PCBA |
|---|---|---|
| Setup | 8.18 USD | 25.56 USD einseitig / 51.12 USD beidseitig |
| Panel mit mehreren Designs | 8.18 × (Designs − 1) | 25.56 bzw. 51.12 × (Designs − 1) |
| Schablone (Stencil) | 1.53 USD | 8.21 USD einseitig / 16.42 USD beidseitig |
| Pre-reflow Soldering | 0.016 USD/Lötstelle | 0.016 USD/Lötstelle (Bedeutung auf der Seite nicht erklärt) |
| SMT-Bestückung | 0.0016 USD/Lötstelle (1–100 000) | 0.0016 (1–50 000), 0.0013, 0.0012 USD/Lötstelle |
| Manuelle Bestückung (Handlöten, z. B. THT) | 0.0164 USD/Lötstelle (1–10 000) | gleich |
| Handlöt-Pauschale („Hand-soldering Labor“) | 3.58 USD pro Bestellung | 3.58 USD pro Bestellung |
| Feeder Loading | 3.07 USD je **Extended**-Teiletyp | 1.53 USD je Teiletyp (Basic **und** Extended) |
| Grossformat (> 650 cm²) | 57.46 USD | 57.46 USD |
| Verpackung | gratis | 0.50 USD + 0.00003 USD × PCB-Fläche (cm²) |
| Röntgen (BGA/QFN usw.) | 1.64 USD/Stk (1–10 Stk) … 0.082 USD | gleich |
| Handling fee | – | wenn Economic auch möglich wäre: Differenz mind. 14.93 USD |
| Mindest-SMT-Gebühr pro Board | – | 0.48 USD („bulk orders“) |
| Confirm Parts Placement | 0.45 USD | 0.45 USD |
| Schablonen-/Fixture-Lagerung | – | je 4.93 USD |
| Fixture (starre PCB) | – | 8.21 USD/Fixture; 1–29 Stk: 2 Fixtures = 16.42 USD |

Widerspruch: Die ältere FAQ https://jlcpcb.com/help/article/pcb-assembly-faqs (Sep 09, 2026) nennt
„$3 per extended component“. Die Preisseite (Oct 22, 2026) ist neuer → 3.07 USD verwendet.
[DRITTQUELLE] techoverflow.net (Update 2025-12-19) nannte 1.50 USD → überholt bzw. nicht bestätigt.

Bauteilpreise: „Per system“, also LCSC-Preis zum Bestellzeitpunkt (Teilesuche, nicht Teil dieses Auftrags).

## 2 PCBA-Fähigkeiten und Mindestmengen [JLC]
Quelle: https://jlcpcb.com/capabilities/pcb-assembly-capabilities, abgerufen 2026-11-06;
https://jlcpcb.com/solutions/pcb-prototype-assembly („The minimum order quantity is 2 boards“), abgerufen 2026-11-06.

| | Economic PCBA | Standard PCBA |
|---|---|---|
| Bestückung | nur eine Seite (SMT/THT) | ein- und beidseitig |
| Lagen | 2, 4, 6 | 1–32 |
| **Dicke** | **0.8–1.6 mm** | ohne Einschränkung |
| Grösse Einzel-PCB | 10 × 10 bis 470 × 500 mm | **70 × 70** bis 460 × 500 mm |
| Panel | 10 × 10 bis 250 × 250 mm | 70 × 70 bis 250 × 250 mm |
| **Menge** | **2–50 Stk** | 2–80 000 Stk |
| Lagenaufbau | „Standard stack-up only, special stack-up is not supported“ | alle |
| Randstreifen / Fiducials | nicht nötig | **nötig** |
| Kleinste Bauform | 0402 | 01005 |
| Min. IC-Pinabstand | 0.4 mm | 0.35 mm |
| Reflow | 255 ± 5 °C (fest) | 240 ± 5 °C |
| Bauzeit | 1–3 Tage | ≥ 4 Tage |

Economic-Tabelle „PCB Specs for Economic PCB Assembly“ (Spalte „Layer“ ist im HTML leer, Zuordnung
der Zeilen zu 2/4 Lagen daher **nicht eindeutig**; vermutlich Zeilen 1–7 = 2 Lagen, 8–11 = 4 Lagen):

| Dicke | Farbe | Oberfläche | Menge |
|---|---|---|---|
| 0.8 | grün | HASL (bleifrei/bleihaltig) | 2–30 |
| 1.0 | grün/schwarz | HASL | 2–30 |
| 1.2 | grün/schwarz | HASL | 2–30 |
| 1.6 | grün | HASL / ENIG | 2–50 |
| 1.6 | schwarz | HASL | 2–50 |
| 1.6 | blau/violett | HASL | 5–30 |
| 1.6 | rot/weiss | HASL bleihaltig | 5–30 |
| 1.0 | grün | HASL | 2–30 |
| 1.2 | grün | HASL | 2–50 |
| 1.6 | grün | HASL / ENIG | 2–50 |
| 1.6 | grün | ENIG | 2–30 |

**Folge: 2.0 mm ist mit Economic PCBA nicht möglich → Standard PCBA (Setup, Schablone, Fixture,
Feeder für alle Teiletypen, Panel ≥ 70 × 70 mm mit Rändern).**

PCB-Menge vs. bestückte Menge: Die PCB-Mindestmenge ist **5 Stk** ([JLC] https://jlcpcb.com/pcb-fabrication/fr4-pcb,
Mengen 5, 10, 15, 20, 25, 30, 50, …). Dass man 5 PCB bestellt und nur **2** bestücken lässt (3 unbestückt
geliefert), ist auf JLC-Seiten nicht explizit beschrieben, nur [DRITTQUELLE] (EasyEDA-Forum,
Hack Club „JLC cost optimizing“). Die JLC-Montagebedingungen
(https://jlcpcb.com/help/article/terms-and-conditions-of-jlcpcb-assembly-service) erwähnen den Fall „five PCBs and
two PCBA“ (unbestückte Platinen können verzinnt/reflowed sein).

Programmier-Service [JLC] https://jlcpcb.com/help/article/pcba-programming-service (Sep 09, 2026):
nur **Standard PCBA**, nur **nach** der Bestückung über eine Schnittstelle auf der Platine
(kein Vorprogrammieren von Chips), ca. 8 USD Engineering + ca. 8 USD/h Arbeit; benötigt
Hersteller-Teilenummer, Schnittstellenbeschreibung, Foto, HEX/BIN.

Conformal Coating [JLC] https://jlcpcb.com/help/article/conformal-coating-spray-service (Sep 09, 2026):
**ja, nur Standard PCBA**; Acryl, 50–200 µm; Reinigung 0.16 USD/Stk, Engineering 6.42 USD (einseitig) /
9.64 USD (beidseitig), 0.0048 USD/cm² beschichtete Fläche (201–300 µm: 0.0064, 301–400 µm: 0.008);
min. Sprühfläche 17 × 17 mm; keine 100 % Abdeckung zugesichert, keine Reklamation ausser Lötfehler.

THT: Economic und Standard, Handlötung/Wellenlöten; Kosten s. Abschnitt 1.

## 3 Leiterplatte – Designregeln [JLC]
Quelle: https://jlcpcb.com/capabilities/pcb-capabilities, abgerufen 2026-11-06.

| Regel | 2 Lagen | 4 Lagen |
|---|---|---|
| Min. Leiterbahn/Abstand (1 oz) | 0.10 / 0.10 mm | 0.09 / 0.09 mm (3–3.5 mil kostet +20 % Auftragswert, s. Abschnitt 5) |
| Min. Bohrung / Via-Durchmesser | 0.15 / 0.25 mm (empfohlen Bohrung ≥ 0.2 mm) | gleich |
| Kleine Vias kosten mehr | 0.1/0.15 mm Bohrung, oder 0.2/0.25 mm mit Via-Ø < 0.45 mm | gleich |
| Restring PTH (1 oz) | empf. 0.25 mm, absolut 0.18 mm | empf. 0.20 mm, absolut 0.15 mm |
| Restring NPTH-Pad | ≥ 0.45 mm | gleich |
| Min. NPTH | 0.50 mm | gleich |
| Kupfer – gefräste Kontur | ≥ 0.2 mm | ≥ 0.2 mm (Innenlagen nicht separat genannt) |
| Kupfer – V-Cut | ≥ 0.4 mm | gleich |
| Konturtoleranz | ± 0.2 mm (± 0.1 mm „high precision“) | gleich |
| Innenlage Via-Bohrung – Kupfer | – | 0.2 mm |
| Innenlage PTH-Bohrung – Kupfer | – | 0.3 mm |
| Pad – Leiterbahn | 0.1 mm | 0.1 mm |
| SMD-Pad – Pad (versch. Netze) | 0.15 mm | 0.15 mm |
| Via-Bohrung – Leiterbahn | 0.2 mm | 0.2 mm |
| PTH – Leiterbahn | 0.28 mm (empf. 0.35 mm) | gleich |
| **Silkscreen** min. Linienbreite | **0.15 mm** | gleich |
| **Silkscreen** min. Texthöhe | **1.0 mm**, Verhältnis Breite:Höhe 1:6 | gleich |
| Pad – Silkscreen | 0.15 mm | gleich |
| Dicken FR-4 | 0.4/0.6/0.8/1.0/1.2/1.6/2.0 mm | gleich |
| Dickentoleranz (≥ 1.0 mm) | ± 10 % (1.6 mm → 1.44–1.76 mm) | gleich |
| Kupfer aussen / innen | 1 oz Standard | aussen 1 oz, innen 0.5 oz Standard |
| Oberflächen | HASL (bleifrei/bleihaltig), ENIG, OSP | gleich |
| Er laut Seite | FR-4 2 Lagen 4.5 | 7628: 4.4, 3313: 4.1, 2116: 4.16 |

Via-Abdeckung [JLC] https://jlcpcb.com/help/article/pcb-via-covering und Capability-Seite:
- **Tented** (Lötstopp über Via): Standard, Bohrung ideal ≤ 0.4 mm, max. 0.5 mm.
- **Plugged** (mit Lötstopplack gefüllt): Bohrung ≤ 0.5 mm, beidseitig keine Lötstopp-Öffnung,
  ≥ 0.35 mm zu anderen Öffnungen; „Complex process, high cost“ (kein Preis).
- **Epoxy filled & capped** (Epoxid gefüllt, überkupfert): Via-Ø 0.15–0.55 mm; **gratis erst ab 6 Lagen**
  ([JLC] https://jlcpcb.com/ – „Free POFV for 6+ layers“; JLC-Blog: 4 Lagen kostenpflichtig). Preis für
  4 Lagen nur im Rechner sichtbar → **offen**.
- Copper-paste filled & capped: wie Epoxid, leitend.

Lötstopplack-Dicke: auf der Capability-Seite **nicht** angegeben → für Isolationsrechnung ANNAHME.

## 4 Lagenaufbau 4 Lagen (Stackup)
Primär [JLC] https://jlcpcb.com/impedance (abgerufen 2026-11-06), 1.6-mm-Familie, Kupfer aussen 0.035 mm,
innen 0.0152 mm (0.5 oz). Werte = **Prepreg zwischen Aussenlage (L1/L4) und Innenlage (L2/L3)**.

| Vorlage | Prepreg L1–L2 (mm) | Kern L2–L3 (mm) | Er Prepreg | Quelle |
|---|---|---|---|---|
| **JLC04161H-7628 (= Standard „No requirement“)** | **0.2104** (7628) | 1.065 | 4.4 | [JLC] |
| JLC04161H-3313 | 0.0994 | 1.265 | 4.1 | [JLC] |
| JLC04161H-1080 | 0.0764 | 1.265 | 3.91 | [JLC] |
| JLC04161H-3313A | 0.107 / 0.0994 (asym.) | 1.065 | 4.1 | [JLC] |
| JLC04161H-1080A | 0.084 / 0.0764 (asym.) | 1.065 | – | [JLC] |
| JLC04161H-2116C | 0.124 / 0.0764 (asym.) | 1.065 | – | [JLC] |

Weitere 1.6-mm-Vorlagen und alle 2.0-mm-Vorlagen: **[DRITTQUELLE]** github.com/gsuberland/jlcpcb_autogenerated_stackups
(aus der JLC-Impedanz-API gezogen, Stand **2025-05-09**, letzter Commit 2025-05-20; Datei
`normalised_json/jlcpcb_4L_<Dicke>_outer1oz_inner0.5oz_<Vorlage>.json`), abgerufen 2026-11-06.
Dielektrikum L1–L2 = Summe der Prepreg-Lagen zwischen L1 und L2:

| Dicke | Vorlage | Prepreg-Aufbau L1–L2 | Summe L1–L2 (mm) | Kern (mm) | Summe Aufbau (mm) |
|---|---|---|---|---|---|
| 1.6 | NOREQ (Standard) | 7628 | 0.210 | 1.065 | 1.586 |
| 1.6 | 2116 | 2116 | 0.116 | 1.265 | 1.598 |
| 1.6 | 7628A | 7628 + 1080 | 0.294 | 0.865 | 1.554 |
| 1.6 | 2116B / 2116D | 2116 + 7628 | 0.334 | 0.865 / 0.700 | 1.634 / 1.469 |
| 1.6 | 7628E | 7628 + 7628 | 0.428 | 0.600 | 1.557 |
| 1.6 | 2116A | 2116 + 7628 + 2116 | 0.458 | 0.600 | 1.617 |
| 1.6 | 7628B | 7628 + 7628 + 2116 | 0.552 | 0.400 | 1.605 |
| 1.6 | 7628C | 3 × 7628 | 0.646 | 0.150 | 1.543 |
| 2.0 | **NOREQ (Standard)** = JLC04201H-7628 | 7628 | **0.210** | 1.465 | 1.986 |
| 2.0 | JLC04201H-3313 | 3313 | 0.099 | 1.665 | 1.964 |
| 2.0 | JLC04201H-1080 | 1080 | 0.076 | 1.665 | 1.918 |
| 2.0 | JLC04201H-7628A | 3 × 7628 | **0.646** | 0.600 | 1.993 |
| 2.0 | JLC04201H-7628B | 7628 | 0.210 | 1.665 | 2.186 (Daten wirken unplausibel) |

Hinweise:
- Isolationsdicke über einer Innenlagen-Elektrode im Sondenbereich (ohne Aussenkupfer) ≈ Prepreg
  L1–L2 + Lötstopplack. Die Prepreg-Werte sind **gepresste Nenndicken mit Kupfer**; ohne Aussenkupfer
  und bei wenig Innenkupfer kann sich die Dicke durch Harzfluss ändern (ANNAHME, ± 10 % Dickentoleranz
  der Platine). Für die Feldsimulation Bandbreite rechnen.
- Material 4 Lagen: Nan Ya NP-155F (TG 150) laut Stackup-Daten; [DRITTQUELLE] Hinweis, dass der Rechner bei
  4/6 Lagen standardmässig „FR4 TG135-140“ vorschlägt.
- Ob eine Nicht-Standard-Vorlage (z. B. 7628C) mit **Economic** PCBA kombinierbar ist, ist unklar
  („Standard stack-up only“). Sicher ist nur NOREQ/7628. Im Rechner prüfen.

## 5 Leiterplatte – Preise und Aufpreise
- [JLC] https://jlcpcb.com/pcb-fabrication/fr4-pcb: „FR4 PCBs starting from just $2“, Mindestmenge 5 Stk,
  Mengenstufen 5/10/15/20/25/30/50/75/100…; max. 670 × 600 mm; min. 3 × 3 mm.
- [JLC] https://jlcpcb.com/help/article/7-pcb-fabrication-services-and-production-time (Sep 09, 2026):
  Promopreis nur für **≤ 100 × 100 mm** → 22 × 150 mm fällt **nicht** darunter.
- [JLC] https://jlcpcb.com/features/prototype-pcb-way: „4-layer PCBs (10x10cm) start at just $7“, Coupon
  7 USD für 1–4 Lagen (30 Tage, Neukunden).
- [JLC] https://jlcpcb.com/help/article/in-what-cases-will-there-be-charged-extra (Sep 09, 2026):
  ENIG > 30 % Fläche: 0.8992 USD/m² je % über 30 % (1 µ"); „Special process“ (nicht standardmässige
  Kombination) wird automatisch berechnet; Feinleiter 3.0–3.5 mil bei 4–8 Lagen +20 % des Auftrags;
  Einzelplatinen ≤ 102 × 102 mm verlieren den Sonderpreis, wenn panelisiert;
  Ecken-/Entgratung kleine Platinen 0.02–0.05 USD/Stk; Länge ≥ 60 cm 31.43 USD.
- [DRITTQUELLE] techoverflow.net 2024-11-26: Dicken 0.8/1.0/1.2/1.6 mm ohne Aufpreis nur mit grünem
  Lötstopp; 2.0 mm kostet Aufpreis (Betrag nicht genannt).
- **Konkrete Preise 22 × 150 mm (2/4 Lagen, 1.6/2.0 mm, 5–20 Stk), Aufpreise 2.0 mm, Farbe, ENIG,
  Epoxy-Vias: nicht belegt** → im Rechner ablesen (Vorlage in research_fertigung.md, Abschnitt 3.2).

## 6 Versand und Import Schweiz
- [JLC] https://jlcpcb.com/help/article/customs,-duties-and-taxes: „All duties and taxes for international
  shipments are the responsibility of the customer.“ Schwelle Schweiz „5CHF“. Kein DDP/MWST-Vorabbezug für CH
  erwähnt (nur EU/UK).
- [JLC] https://jlcpcb.com/shipping: Rechner zeigt Werte nur interaktiv („for reference only. The final
  shipping cost will be confirmed at checkout“). Keine Zahlen abrufbar.
- [DRITTQUELLE] chiptron.eu (2025, Slowakei): DHL Express 21.50 USD (rabattiert, regulär 29.51 USD) für kleine
  PCB-Bestellung; Aktion auch für Global Standard Direct Line / EuroPacket (EU).
- [OFFIZIELL] ESTV https://www.estv.admin.ch/de/mwst-steuersaetze-schweiz (aktualisiert 5. Nov. 2026):
  Normalsatz **8.1 %** (seit 1.1.2024); keine beschlossene Änderung genannt.
- [OFFIZIELL] BAZG https://www.bazg.admin.ch/de/empfangen-von-briefen-und-paketen: „Aus verwaltungsökonomischen
  Gründen werden Zollabgaben bis 5 Schweizerfranken nicht erhoben“ (gilt auch für die MWST →
  bei 8.1 % ca. **62 CHF** Warenwert inkl. Versand); Bemessungsgrundlage inkl. „alle Kosten bis zum
  Bestimmungsort in der Schweiz“. Kurier-Verzollungsgebühren sind Sache des Kuriers.
- [OFFIZIELL] BAZG https://www.bazg.admin.ch/de/aufhebung-industriezolle-januar-2024: Industriezölle (Kap. 25–97)
  seit **1.1.2024 aufgehoben** → kein Zoll auf PCB/PCBA.
- [OFFIZIELL] Post CH https://www.post.ch/de/empfangen/importverzollung: Grundpreis Verzollung 16.00 CHF
  (Herkunft ausserhalb EU), 13.00 CHF (EU), −1.50 CHF bei Online-Zahlung, + 3 % des Warenwerts inkl. Versand,
  max. 70 CHF (exkl. MWST).
- [OFFIZIELL] DHL Express CH https://mydhl.express.dhl/ch/de/ship/customs-services.html (gültig ab 1.1.2026):
  Zoll-/Steuerabwicklung ohne ZAZ-Konto max(3.00 CHF; 2 % der verauslagten Abgaben); bei behördlichen Auflagen
  19.00 CHF; Vollverzollung 39.50 CHF.
- FedEx: [DRITTQUELLE, Suchtreffer fedex.com/de-ch] 2.5 % der Abgaben, min. 25 CHF (Seite nicht direkt abrufbar).
  UPS: keine belastbare Zahl gefunden.
- Wechselkurs [OFFIZIELL] EZB 2026-11-06 https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml:
  EUR/USD 1.1165, EUR/CHF 0.9143 → **1 USD = 0.8189 CHF**.

## 7 Offen (im JLC-Rechner bzw. Checkout ablesen, mit Datum nachtragen)
1. PCB-Preis 22 × 150 mm für 2/4 Lagen × 1.6/2.0 mm × 5/10/15/20 Stk (grün, HASL bleifrei).
2. Aufpreise: 2.0 mm, ENIG, Farbe, Epoxy filled & capped (4 Lagen), Nicht-Standard-Stackup.
3. Ob Economic PCBA mit 4 Lagen 1.6 mm und Stackup ≠ NOREQ bestellbar ist.
4. Versandkosten CH für 0.2–0.5 kg (Global Standard Direct Line, DHL Express, ggf. weitere).
5. Ob bei 5 PCB die Option „2 bestückt“ weiterhin angeboten wird.
