#!/usr/bin/env python3
"""Troepfli - Kostenmodell Sensor-PCB/PCBA bei JLCPCB inkl. Versand und Import Schweiz.

Aufruf:  .venv/bin/python scripts/cost_model.py            (Beispiel-BOM, alle Szenarien)
         .venv/bin/python scripts/cost_model.py --bom datei.csv --layers 4 --thickness 1.6 \
             --pcb-qty 5 --pcba-qty 2 --ship GSDL

Nur Standardbibliothek. Alle Parameter stehen oben als Konstanten mit Quelle und Abrufdatum.
Recherche und Begruendungen: docs/concepts/research_fertigung.md, docs/references/JLCPCB_NOTES.md

Kennzeichnung:
  [JLC]        offizielle JLCPCB-Seite (URL + Abrufdatum)
  [OFFIZIELL]  Behoerde / Kurierdienst, offizielle Seite
  [DRITTQUELLE] nicht von JLC/Behoerde, nur Orientierung
  [ANNAHME]    nicht belegt -> vor Bestellung durch Wert aus dem JLC-Online-Rechner ersetzen

Ergebnisse (Kostendefinition D-005, Projektleiter 2026-11-06):
  - Stueckkosten pro Sensor (REQ-FAB-04): alles, was pro Sensor anfaellt = Bauteile (Preisstaffel der
    tatsaechlichen Bestellmenge), PCB-Grenzkosten pro Platine, Bestueckung/Loetstellen, Roentgen pro
    leadless Bauteil, MWST-Anteil, lokale Teile (Zelle, Gehaeusematerial, Kleinteile) inkl. Ausschuss,
    Reserveboard(s) auf die nutzbaren Sensoren verteilt.
  - Einmalkosten pro Bestellung (REQ-FAB-05): PCB-Fixanteil, Setup, Schablone, Extended-Gebuehren,
    Mindestabnahme-Ueberschuss, unbestueckte Reserveplatinen, Versand, MWST-Anteil, Verzollung.
  - Vollkosten pro Sensor = Bestellung total / Anzahl nutzbare Sensoren.

BOM-CSV-Format (Kopfzeile, Semikolon oder Komma):
  part;qty_per_board;unit_price_usd;unit_price_chf;category;jlc_assembled;joints;moq;attrition;source
    category      : basic | preferred | extended | tht | none   (none = nicht von JLC bestueckt;
                    preferred = "Preferred Extended", Economic gebuehrenfrei [JLC prototype-assembly])
    tiers         : optional, Preisstaffel "start:preis|start:preis" (USD, JLC-API)
    leadless      : optional ja/nein (QFN/WSON/DFN -> Roentgengebuehr)
    jlc_assembled : ja/nein
    joints        : Loetstellen pro Bauteil (Pins)
    moq           : Mindestabnahme LCSC pro Bestellung (Stueck), Ueberschuss = Einmalkosten
    attrition     : Zusatzmenge pro Bestellung fuer Verlust (Stueck), [ANNAHME] JLC-Praxis
    source        : JLC (im JLC-Paket, USD) | LOKAL (selbst beschafft, CHF inkl. MWST)
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from dataclasses import dataclass

# =============================================================================
# 1) Wechselkurs
# =============================================================================
# [OFFIZIELL] EZB-Referenzkurse vom 2026-11-06, https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml
# (abgerufen 2026-11-06): EUR/USD 1.1165, EUR/CHF 0.9143 -> USD/CHF = 0.9143/1.1165
ECB_EUR_USD = 1.1165
ECB_EUR_CHF = 0.9143
USD_TO_CHF = ECB_EUR_CHF / ECB_EUR_USD  # = 0.8189 CHF pro USD
FX_DATE = "2026-11-06 (EZB-Referenzkurs, Kreuzkurs)"
# [ANNAHME] Zoll rechnet mit eigenem Tageskurs; Kreditkarte/PayPal schlagen ca. 1-2 % auf.
FX_CARD_MARKUP = 0.015

# =============================================================================
# 2) JLCPCB PCBA-Gebuehren
# =============================================================================
# [JLC] https://jlcpcb.com/help/article/pcb-assembly-price  ("Last updated on Oct 22, 2026"),
#       abgerufen 2026-11-06. Werte in USD.
ECON = {
    "setup": 8.18,                 # pro Bestellung
    "stencil": 1.53,
    "smt_per_joint": 0.0016,       # 1-100'000 Loetstellen
    "manual_per_joint": 0.0164,    # Handloetung/THT, 1-10'000 Loetstellen
    "hand_solder_labor": 3.58,     # pro Bestellung, sobald Handloetung anfaellt
    "feeder_extended": 3.07,       # pro Extended-Teiletyp (Basic: 0)
    "feeder_basic": 0.0,
    "confirm_placement": 0.45,     # optional "Confirm Parts Placement"
    "packing": 0.0,
    "fixture": 0.0,
    "single_board_min_smt": 0.0,
}
STD = {
    "setup": 25.56,                # einseitig (beidseitig 51.12)
    "stencil": 8.21,               # einseitig (beidseitig 16.42)
    "smt_per_joint": 0.0016,       # 1-50'000 Loetstellen
    "manual_per_joint": 0.0164,
    "hand_solder_labor": 3.58,
    "feeder_extended": 1.53,       # Standard: Basic UND Extended je Teiletyp
    "feeder_basic": 1.53,
    "confirm_placement": 0.45,
    "packing_base": 0.50,          # + 0.00003 USD/cm2 PCB-Flaeche [JLC]; Bezug (pro Bestellung?) unklar
    "packing_per_cm2": 0.00003,
    "fixture": 16.42,              # 2 Fixtures fuer 1-29 Stk (8.21/Fixture)
    "single_board_min_smt": 0.48,  # min. SMT-Gebuehr pro Board ("bulk orders") [JLC]
}
# [JLC] "Pre-reflow Soldering 1-1,000,000 joints: $0.016/joint" ist auf derselben Seite gelistet,
# Anwendungsfall nicht erklaert -> standardmaessig NICHT eingerechnet (Unsicherheit, siehe Doku).
PRE_REFLOW_PER_JOINT = 0.016
APPLY_PRE_REFLOW = False

# [JLC] https://jlcpcb.com/capabilities/pcb-assembly-capabilities (abgerufen 2026-11-06)
ECON_MAX_THICKNESS_MM = 1.6     # Economic: 0.8-1.6 mm -> 2.0 mm nur Standard-PCBA
ECON_QTY_RANGE = (2, 50)
STD_MIN_SIZE_MM = (70.0, 70.0)  # Standard-PCBA: Einzelplatine/Panel min. 70 x 70 mm -> Panel noetig
PCBA_MIN_QTY = 2

# [JLC] Programmier-Service, https://jlcpcb.com/help/article/pcba-programming-service
# ("Last updated Sep 09, 2026"): nur Standard-PCBA, ca. 8 USD Engineering + ca. 8 USD/h.
PROG_ENGINEERING = 8.0
PROG_PER_HOUR = 8.0
# [JLC] Conformal Coating, https://jlcpcb.com/help/article/conformal-coating-spray-service
# (Sep 09, 2026): nur Standard-PCBA, Acryl, 50-200 um.
COAT_CLEAN_PER_PCS = 0.16
COAT_ENGINEERING_1S = 6.42
COAT_ENGINEERING_2S = 9.64
COAT_PER_CM2 = 0.0048           # pro beschichteter Seite

# =============================================================================
# 3) JLCPCB Leiterplatte (Fertigung)
# =============================================================================
# Der JLC-Online-Rechner (cart.jlcpcb.com/quote) ist nicht skriptbar. Die Preise unten hat der
# Auftraggeber am 2026-11-06 im Rechner abgelesen (22 x 150 mm, FR-4, gruen, LeadFree HASL, 1 oz,
# Standardoptionen). Promo "$2 / 5 pcs" gilt nur bis 100 x 100 mm [JLC] und ist nicht enthalten.
BOARD_W_MM = 22.0   # [ANNAHME] Kontur
BOARD_L_MM = 150.0  # [ANNAHME] Kontur
# [JLC-RECHNER] Preise ab 2026-11-06 BELEGT: "JLCPCB-Rechner, vom Auftraggeber abgelesen 2026-11-06",
# 22 x 150 mm, gruen, LeadFree HASL, Standardoptionen. USD gesamt pro Bestellung (inkl. aller Platinen).
PCB_PRICE_USD = {   # (Lagen, Stueck) -> USD fuer 1.6 mm
    (2, 5): 6.9, (2, 10): 8.7, (2, 15): 10.4, (2, 20): 12.3,
    (4, 5): 32.3, (4, 10): 34.5, (4, 15): 36.8, (4, 20): 39.0,
}
PCB_PRICE_2MM_USD = {  # (Lagen, Stueck) -> USD fuer 2.0 mm  [JLC-RECHNER 2026-11-06, Auftraggeber]
    (4, 5): 73.8, (4, 10): 76.6, (4, 15): 79.4, (4, 20): 82.1,
}
SURCHARGE_2MM_FACTOR = 1.30       # [ANNAHME] nur noch fuer 2 Lagen / 2.0 mm (nicht abgelesen)
# [JLC-RECHNER 2026-11-06] 4 L 1.6 mm 5 Stk: HASL 32.3, ENIG 44.2 (+11.9), ENIG + Epoxy filled & capped 64.5 (+20.3)
SURCHARGE_ENIG_USD = {2: 11.9, 4: 11.9}   # 4 L belegt (5 Stk); 2 L [ANNAHME] gleich; Mengenabhaengigkeit [ANNAHME] keine
SURCHARGE_EPOXY_VIA_USD = {2: 20.3, 4: 20.3}  # 4 L belegt (5 Stk); 2 L [ANNAHME]; [JLC] gratis erst ab 6 Lagen
SURCHARGE_COLOR_USD = 0.0         # gruen = Standard; andere Farben [ANNAHME] Aufpreis, im Rechner pruefen

# D-005 (Projektleiter 2026-11-06): PCB-Preis linear = Fixanteil pro Bestellung (-> Einmalkosten)
# + Grenzkosten pro Platine (-> Stueckkosten); lineare Regression ueber 5/10/15/20 Stk der Tabellen oben.
PCB_FIX_USD = {(2, 1.6): 5.10, (4, 1.6): 30.05, (4, 2.0): 71.05}
PCB_VAR_USD = {(2, 1.6): 0.358, (4, 1.6): 0.448, (4, 2.0): 0.554}
# ENIG/Epoxy-Vias als Fixaufschlag pro Bestellung [ANNAHME: Mengenabhaengigkeit nicht abgelesen]

# [JLC] https://jlcpcb.com/help/article/pcb-assembly-price ("Last updated on Oct 22, 2026"), Pruefbericht
# docs/reviews/phase2_concepts_fertigung.md W-1: "X-ray Inspection (Component Quantity) 1-10 pcs: $1.64/pc,
# 11-50 pcs: $0.82/pc ..." fuer BGA/QFN/leadless; ueber 50 Stk [ANNAHME] 0.82 USD/Stk (Staffel nicht erfasst).
XRAY_TIERS = [(1, 1.64), (11, 0.82)]
# [ANNAHME] Ausschuss lokal beschaffter Teile/Druck (AMS-Spuelung, Fehldrucke) 5 %
LOCAL_SCRAP = 0.05

# =============================================================================
# 4) Versand nach CH und Import
# =============================================================================
# [JLC] Versand in die Schweiz, JLC-Seite (Screenshot Auftraggeber, 2026-11-06), BELEGT:
#   DHL Express 23.44 USD (2-4 Tage), UPS Express Saver 25.36, FedEx Express 31.15,
#   Global Standard Direct Line (GSDL) 7.63 USD (10-12 Tage), nur bis 1.5 kg UND Warenwert <= 65 USD.
# Im Modell rechenbar: GSDL und DHL (Verzollungsgebuehren nur fuer Post/DHL belegt). UPS/FedEx nur dokumentiert.
SHIPPING_USD = {"GSDL": 7.63, "DHL": 23.44}
SHIPPING_OTHER_USD = {"UPS": 25.36, "FEDEX": 31.15}
GSDL_MAX_GOODS_USD = 65.0   # Warenwert (ohne Versand) [JLC, Screenshot Auftraggeber]
GSDL_MAX_KG = 1.5
# GSDL: Zustellung in CH [ANNAHME] durch Die Post. Ueber den Grenzen faellt das Modell auf DHL zurueck.

# [OFFIZIELL] ESTV https://www.estv.admin.ch/de/mwst-steuersaetze-schweiz (abgerufen 2026-11-06):
# Normalsatz 8.1 % (seit 1.1.2024), keine beschlossene Aenderung auf der Seite.
CH_VAT = 0.081
# [OFFIZIELL] BAZG https://www.bazg.admin.ch/de/empfangen-von-briefen-und-paketen (2026-11-06):
# Abgaben bis 5 CHF werden nicht erhoben; Bemessungsgrundlage = Warenwert + alle Kosten bis Bestimmungsort.
CH_TAX_MIN_CHF = 5.0
# [OFFIZIELL] Industriezoelle seit 1.1.2024 aufgehoben (Kap. 25-97), BAZG/SECO
# https://www.bazg.admin.ch/de/aufhebung-industriezolle-januar-2024 -> Zoll 0.
CH_DUTY = 0.0
# Verzollungsgebuehren Kurier, nur wenn Abgaben erhoben werden:
# [OFFIZIELL] DHL Express CH, ab 1.1.2026, https://mydhl.express.dhl/ch/de/ship/customs-services.html
#   ohne ZAZ-Konto: max(3.00 CHF, 2 % der verauslagten Einfuhrabgaben)
DHL_FEE_MIN_CHF = 3.0
DHL_FEE_PCT = 0.02
# [OFFIZIELL] Post CH, https://www.post.ch/de/empfangen/importverzollung (2026-11-06):
#   Grundpreis 16.00 CHF (Herkunft ausserhalb EU) + 3 % des Warenwerts inkl. Versand; max. 70 CHF
POST_FEE_BASE_CHF = 16.0
POST_FEE_PCT = 0.03
POST_FEE_MAX_CHF = 70.0
# [ANNAHME] Gewicht: ca. 20 g pro bestueckter Platine + 150 g Verpackung (fuer Info, Preis ist pauschal).
WEIGHT_PER_BOARD_KG = 0.02
WEIGHT_PACKAGING_KG = 0.15


# =============================================================================
@dataclass
class BomLine:
    part: str
    qty_per_board: float
    unit_price_usd: float = 0.0
    unit_price_chf: float = 0.0
    category: str = "basic"         # basic | extended | tht | none
    jlc_assembled: bool = True
    joints: int = 2
    moq: int = 1
    attrition: int = 0
    source: str = "JLC"             # JLC | LOKAL
    tiers: tuple = ()               # ((start_qty, usd), ...) aus JLC-API; leer -> unit_price_usd
    leadless: bool = False          # Roentgenpflichtig (QFN/WSON/DFN) [JLC W-1]


def part_price(b: "BomLine", order_qty: int) -> float:
    """Stueckpreis in der Staffel der tatsaechlichen Bestellmenge (Pruefbericht Fertigung W-3)."""
    if not b.tiers:
        return b.unit_price_usd
    price = sorted(b.tiers)[0][1]
    for start, p in sorted(b.tiers):
        if order_qty >= start:
            price = p
    return price


def xray_rate(n_total: int) -> float:
    rate = XRAY_TIERS[0][1]
    for start, r in XRAY_TIERS:
        if n_total >= start:
            rate = r
    return rate


# BEISPIEL-BOM -- NUR ZUR DEMONSTRATION DES SKRIPTS. Keine echten Teile, keine LCSC-Nummern,
# Preise frei gewaehlte Groessenordnungen. NICHT als Kostenschaetzung eines Konzepts verwenden.
EXAMPLE_BOM = [
    BomLine("BEISPIEL Funk-MCU QFN (extended)", 1, 1.80, 0, "extended", True, 49, 1, 0),
    BomLine("BEISPIEL Temperatursensor (extended)", 1, 0.40, 0, "extended", True, 6, 1, 0),
    BomLine("BEISPIEL LDO/Schutz (basic)", 1, 0.08, 0, "basic", True, 5, 1, 0),
    BomLine("BEISPIEL Kondensator 0402 (basic)", 8, 0.002, 0, "basic", True, 2, 100, 10),
    BomLine("BEISPIEL Widerstand 0402 (basic)", 6, 0.001, 0, "basic", True, 2, 100, 10),
    BomLine("BEISPIEL LED 0603 (basic)", 1, 0.01, 0, "basic", True, 2, 20, 2),
    BomLine("BEISPIEL Taster SMD (extended)", 1, 0.10, 0, "extended", True, 4, 1, 0),
    BomLine("BEISPIEL Knopfzellenhalter THT (von JLC handgeloetet)", 1, 0.15, 0, "tht", True, 2, 1, 0),
    BomLine("BEISPIEL Knopfzelle (lokal)", 1, 0, 1.00, "none", False, 0, 1, 0, "LOKAL"),
    BomLine("BEISPIEL Gehaeuse ASA-Filament + Dichtung (lokal)", 1, 0, 1.20, "none", False, 0, 1, 0, "LOKAL"),
]


def _bool(s: str) -> bool:
    return str(s).strip().lower() in ("1", "ja", "yes", "true", "y", "j")


def load_bom(path: str) -> list[BomLine]:
    with open(path, newline="", encoding="utf-8") as f:
        sample = f.read(2048)
        f.seek(0)
        dialect = csv.Sniffer().sniff(sample, delimiters=";,")
        rows = list(csv.DictReader(f, dialect=dialect))
    out = []
    for r in rows:
        out.append(BomLine(
            part=r["part"],
            qty_per_board=float(r["qty_per_board"]),
            unit_price_usd=float(r.get("unit_price_usd") or 0),
            unit_price_chf=float(r.get("unit_price_chf") or 0),
            category=(r.get("category") or "basic").strip().lower(),
            jlc_assembled=_bool(r.get("jlc_assembled", "ja")),
            joints=int(float(r.get("joints") or 0)),
            moq=int(float(r.get("moq") or 1)),
            attrition=int(float(r.get("attrition") or 0)),
            source=(r.get("source") or "JLC").strip().upper(),
            tiers=tuple((int(a), float(b)) for a, b in (t.split(":") for t in (r.get("tiers") or "").split("|") if t)),
            leadless=_bool(r.get("leadless", "nein")),
        ))
    return out


def pcb_price_usd(layers: int, thickness: float, qty: int, enig: bool, epoxy_vias: bool) -> float:
    """PCB-Fertigungspreis pro Bestellung (USD). Tabelle aus dem JLC-Rechner (2026-11-06),
    Interpolation fuer Zwischenmengen; 2.0 mm aus eigener Tabelle, sonst Faktor [ANNAHME]."""
    thick = thickness > 1.6 + 1e-9
    table = PCB_PRICE_2MM_USD if thick and any(l == layers for (l, _) in PCB_PRICE_2MM_USD) else PCB_PRICE_USD
    keys = sorted(q for (l, q) in table if l == layers)
    if not keys:
        raise ValueError(f"keine Preisangabe fuer {layers} Lagen")
    if qty <= keys[0]:
        base = table[(layers, keys[0])]
    elif qty >= keys[-1]:
        # linear extrapolieren mit letzter Steigung
        q1, q2 = keys[-2], keys[-1]
        p1, p2 = table[(layers, q1)], table[(layers, q2)]
        base = p2 + (p2 - p1) / (q2 - q1) * (qty - q2)
    else:
        for q1, q2 in zip(keys, keys[1:]):
            if q1 <= qty <= q2:
                p1, p2 = table[(layers, q1)], table[(layers, q2)]
                base = p1 + (p2 - p1) * (qty - q1) / (q2 - q1)
                break
    if thick and table is PCB_PRICE_USD:
        base *= SURCHARGE_2MM_FACTOR
    if enig:
        base += SURCHARGE_ENIG_USD[layers]
    if epoxy_vias:
        base += SURCHARGE_EPOXY_VIA_USD[layers]
    return base + SURCHARGE_COLOR_USD


def choose_pcba(thickness: float, pcba_qty: int, want: str) -> str:
    econ_ok = thickness <= ECON_MAX_THICKNESS_MM + 1e-9 and ECON_QTY_RANGE[0] <= pcba_qty <= ECON_QTY_RANGE[1]
    if want == "economic" and not econ_ok:
        raise ValueError("Economic PCBA nicht moeglich (Dicke > 1.6 mm oder Menge ausserhalb 2-50)")
    if want == "auto":
        return "economic" if econ_ok else "standard"
    return want


def compute(bom: list[BomLine], layers: int, thickness: float, pcb_qty: int, pcba_qty: int,
            ship: str = "GSDL", pcba: str = "auto", enig: bool = False, epoxy_vias: bool = False,
            confirm_placement: bool = True, programming_hours: float = 0.0,
            coating_cm2_per_side: float = 0.0, coating_sides: int = 0, sensors: int | None = None,
            pre_reflow: bool | None = None, xray: bool = True, local_scrap: float = LOCAL_SCRAP) -> dict:
    sensors = sensors or pcba_qty
    pre_reflow = APPLY_PRE_REFLOW if pre_reflow is None else pre_reflow
    if pcba_qty < PCBA_MIN_QTY:
        raise ValueError("PCBA-Mindestmenge 2")
    if pcb_qty < pcba_qty:
        raise ValueError("PCB-Menge < bestueckte Menge")
    mode = choose_pcba(thickness, pcba_qty, pcba)
    fee = ECON if mode == "economic" else STD
    notes = []
    if mode == "standard":
        notes.append("Standard-PCBA: min. 70x70 mm -> Panel (z. B. 3-fach + Raender) noetig; "
                     "Panelpreis im Rechner pruefen [ANNAHME: hier nicht modelliert].")
    if (programming_hours or coating_sides) and mode != "standard":
        raise ValueError("Programmierung/Coating nur mit Standard-PCBA")

    once, unit = {}, {}  # USD; unit = pro bestuecktem Board

    # --- Leiterplatte (D-005: Fixanteil -> einmalig, Grenzkosten -> Stueck)
    key = (layers, 2.0 if thickness > 1.6 + 1e-9 else 1.6)
    if key not in PCB_FIX_USD:
        raise ValueError(f"kein PCB-Fix/Grenzkostenwert fuer {key}")
    pcb_fix = PCB_FIX_USD[key] + (SURCHARGE_ENIG_USD[layers] if enig else 0.0) \
        + (SURCHARGE_EPOXY_VIA_USD[layers] if epoxy_vias else 0.0) + SURCHARGE_COLOR_USD
    unit["PCB Grenzkosten pro Platine"] = PCB_VAR_USD[key]
    once["PCB Fixanteil pro Bestellung (D-005)"] = pcb_fix
    if pcb_qty > pcba_qty:
        once["PCB unbestueckte Reserveplatinen"] = PCB_VAR_USD[key] * (pcb_qty - pcba_qty)

    # --- Bauteile (nur JLC-Paket) + Mindestabnahmen
    comp_unit_usd = 0.0
    surplus_usd = 0.0
    lokal_unit_chf = 0.0
    for b in bom:
        if b.source == "LOKAL":
            lokal_unit_chf += b.qty_per_board * b.unit_price_chf
            continue
        need = b.qty_per_board * pcba_qty
        order = max(math.ceil(need) + b.attrition, b.moq)
        price = part_price(b, order)
        comp_unit_usd += b.qty_per_board * price
        surplus_usd += (order - need) * price
    unit["Bauteile JLC/LCSC"] = comp_unit_usd
    once["Bauteile Mindestabnahme/Verlust-Ueberschuss"] = surplus_usd

    # --- Bestueckung
    smt_joints = sum(b.joints * b.qty_per_board for b in bom
                     if b.jlc_assembled and b.category in ("basic", "preferred", "extended"))
    tht_joints = sum(b.joints * b.qty_per_board for b in bom if b.jlc_assembled and b.category == "tht")
    smt_unit = smt_joints * fee["smt_per_joint"]
    if mode == "standard":
        smt_unit = max(smt_unit, fee["single_board_min_smt"])
    unit["SMT-Bestueckung"] = smt_unit
    if pre_reflow:
        unit["Pre-reflow soldering (unklar, W-2)"] = smt_joints * PRE_REFLOW_PER_JOINT
    n_leadless = sum(b.qty_per_board for b in bom if b.jlc_assembled and b.leadless)
    if xray and n_leadless:
        unit[f"Roentgen ({n_leadless:g} leadless/Board)"] = n_leadless * xray_rate(int(n_leadless * pcba_qty))
    if tht_joints:
        unit["Handloetung THT"] = tht_joints * fee["manual_per_joint"]
        once["Handloet-Pauschale"] = fee["hand_solder_labor"]
    once["PCBA Setup"] = fee["setup"]
    once["Schablone"] = fee["stencil"]
    types_ext = {b.part for b in bom if b.jlc_assembled and b.category == "extended"}
    types_pref = {b.part for b in bom if b.jlc_assembled and b.category == "preferred"}
    types_basic = {b.part for b in bom if b.jlc_assembled and b.category in ("basic", "tht")}
    once[f"Feeder/Extended ({len(types_ext)} ext., {len(types_pref)} pref., {len(types_basic)} basic Typen)"] = (
        len(types_ext) * fee["feeder_extended"]
        + len(types_pref) * (0.0 if mode == "economic" else fee["feeder_basic"])
        + len(types_basic) * fee["feeder_basic"])
    if confirm_placement:
        once["Confirm Parts Placement"] = fee["confirm_placement"]
    if mode == "standard":
        once["Fixture"] = fee["fixture"]
        once["Verpackung (Standard)"] = fee["packing_base"] + fee["packing_per_cm2"] * (
            BOARD_W_MM * BOARD_L_MM / 100.0) * pcba_qty
    if programming_hours:
        once["Programmierung Engineering"] = PROG_ENGINEERING
        once["Programmierung Arbeit"] = PROG_PER_HOUR * programming_hours
    if coating_sides:
        once["Coating Engineering"] = COAT_ENGINEERING_1S if coating_sides == 1 else COAT_ENGINEERING_2S
        unit["Coating"] = COAT_CLEAN_PER_PCS + COAT_PER_CM2 * coating_cm2_per_side * coating_sides

    # --- Versand ([JLC] 2026-11-06); GSDL nur bis Warenwert 65 USD und 1.5 kg, sonst DHL
    unit_usd = sum(unit.values())
    goods_wo_ship = unit_usd * pcba_qty + sum(once.values())
    weight = WEIGHT_PACKAGING_KG + WEIGHT_PER_BOARD_KG * pcb_qty
    if ship == "GSDL" and (goods_wo_ship > GSDL_MAX_GOODS_USD or weight > GSDL_MAX_KG):
        notes.append(f"GSDL nicht zulaessig (Warenwert {goods_wo_ship:.2f} USD > {GSDL_MAX_GOODS_USD} USD "
                     f"oder Gewicht > {GSDL_MAX_KG} kg) -> DHL Express gerechnet.")
        ship = "DHL"
    once[f"Versand {ship}"] = SHIPPING_USD[ship]

    # --- Summen USD
    once_usd = sum(once.values())
    goods_usd = unit_usd * pcba_qty + once_usd  # Rechnungsbetrag JLC inkl. Versand
    fx = USD_TO_CHF * (1 + FX_CARD_MARKUP)

    # --- Import CH (auf gesamte JLC-Rechnung)
    base_chf = goods_usd * USD_TO_CHF  # Zoll rechnet ohne Kartenaufschlag [ANNAHME]
    vat = base_chf * CH_VAT
    duty = base_chf * CH_DUTY
    abgaben = vat + duty
    if abgaben <= CH_TAX_MIN_CHF:
        abgaben = 0.0
        vat = 0.0
        carrier_fee = 0.0
    elif ship == "DHL":
        carrier_fee = max(DHL_FEE_MIN_CHF, DHL_FEE_PCT * abgaben)
    else:
        carrier_fee = min(POST_FEE_MAX_CHF, POST_FEE_BASE_CHF + POST_FEE_PCT * base_chf)
    # MWST anteilig: Stueckanteil -> Stueckkosten, Rest -> Einmalkosten
    share_unit = (unit_usd * pcba_qty) / goods_usd if goods_usd else 0.0
    vat_unit_chf = abgaben * share_unit / pcba_qty
    vat_once_chf = abgaben * (1 - share_unit)

    board_chf = unit_usd * fx + vat_unit_chf                 # JLC-Anteil pro bestuecktem Board
    lokal_sensor_chf = lokal_unit_chf * (1 + local_scrap)    # lokale Teile inkl. Ausschuss
    unit_chf = board_chf * pcba_qty / sensors + lokal_sensor_chf
    once_chf = once_usd * fx + vat_once_chf + carrier_fee
    total_chf = board_chf * pcba_qty + lokal_sensor_chf * sensors + once_chf
    return {
        "mode": mode, "layers": layers, "thickness": thickness, "pcb_qty": pcb_qty,
        "pcba_qty": pcba_qty, "ship": ship, "unit": unit, "once": once,
        "unit_usd": unit_usd, "once_usd": once_usd, "goods_usd": goods_usd,
        "lokal_unit_chf": lokal_unit_chf, "base_chf": base_chf, "vat_chf": vat,
        "carrier_fee_chf": carrier_fee, "vat_unit_chf": vat_unit_chf, "vat_once_chf": vat_once_chf,
        "unit_chf": unit_chf, "once_chf": once_chf, "sensors": sensors, "board_chf": board_chf,
        "lokal_sensor_chf": lokal_sensor_chf, "full_chf": total_chf / sensors,
        "total_chf": total_chf, "notes": notes,
        "weight_kg": WEIGHT_PACKAGING_KG + WEIGHT_PER_BOARD_KG * pcb_qty,
    }


def report(r: dict, title: str) -> None:
    print(f"\n=== {title} ===")
    print(f"{r['layers']} Lagen, {r['thickness']} mm, PCB {r['pcb_qty']} Stk, bestueckt {r['pcba_qty']} Stk, "
          f"nutzbare Sensoren {r['sensors']}, "
          f"PCBA {r['mode']}, Versand {r['ship']}, Gewicht ca. {r['weight_kg']:.2f} kg [ANNAHME]")
    print("  JLC-Anteil pro bestuecktem Board (USD):")
    for k, v in r["unit"].items():
        print(f"    {k:<52s} {v:8.2f}")
    print(f"    {'Summe JLC-Anteil':<52s} {r['unit_usd']:8.2f} USD")
    print(f"    {'+ MWST-Anteil CH':<52s} {r['vat_unit_chf']:8.2f} CHF")
    print(f"    {'= JLC-Anteil pro Board':<52s} {r['board_chf']:8.2f} CHF")
    print(f"    {'x Boards / Sensoren':<52s} {r['pcba_qty']}/{r['sensors']}")
    print(f"    {'+ lokal beschaffte Teile inkl. Ausschuss':<52s} {r['lokal_sensor_chf']:8.2f} CHF")
    print(f"    {'= STUECKKOSTEN pro Sensor (D-005)':<52s} {r['unit_chf']:8.2f} CHF")
    print("  Einmalkosten pro Bestellung (USD):")
    for k, v in r["once"].items():
        print(f"    {k:<52s} {v:8.2f}")
    print(f"    {'Summe JLC-Rechnung einmalig':<52s} {r['once_usd']:8.2f} USD")
    print(f"    {'+ MWST-Anteil CH (einmalig)':<52s} {r['vat_once_chf']:8.2f} CHF")
    print(f"    {'+ Verzollungsgebuehr Kurier/Post':<52s} {r['carrier_fee_chf']:8.2f} CHF")
    print(f"    {'= EINMALKOSTEN':<52s} {r['once_chf']:8.2f} CHF")
    print(f"  JLC-Rechnung total {r['goods_usd']:.2f} USD = {r['base_chf']:.2f} CHF; "
          f"MWST {r['vat_chf']:.2f} CHF; Bestellung total {r['total_chf']:.2f} CHF; "
          f"VOLLKOSTEN pro Sensor {r['full_chf']:.2f} CHF")
    for n in r["notes"]:
        print("  Hinweis:", n)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--bom", help="BOM-CSV (ohne: BEISPIEL-BOM)")
    p.add_argument("--layers", type=int, choices=(2, 4))
    p.add_argument("--thickness", type=float, choices=(1.6, 2.0))
    p.add_argument("--pcb-qty", type=int)
    p.add_argument("--pcba-qty", type=int)
    p.add_argument("--ship", choices=tuple(SHIPPING_USD), default="GSDL")
    p.add_argument("--pcba", choices=("auto", "economic", "standard"), default="auto")
    p.add_argument("--enig", action="store_true")
    p.add_argument("--epoxy-vias", action="store_true")
    a = p.parse_args(argv)

    print(f"Troepfli Kostenmodell | USD->CHF {USD_TO_CHF:.4f} ({FX_DATE}), Kartenaufschlag "
          f"{FX_CARD_MARKUP:.1%} [ANNAHME] | MWST CH {CH_VAT:.1%}")
    print("PCB-Preise und Versand: JLC-Rechner/JLC-Seite, vom Auftraggeber abgelesen 2026-11-06 (2.0 mm/2 L, ENIG 2 L = ANNAHME).")
    bom = load_bom(a.bom) if a.bom else EXAMPLE_BOM
    if not a.bom:
        print(">>> BEISPIEL-BOM (fiktiv, nur Demonstration) <<<")

    if a.layers:
        r = compute(bom, a.layers, a.thickness or 1.6, a.pcb_qty or 5, a.pcba_qty or 2, a.ship,
                    a.pcba, a.enig, a.epoxy_vias)
        report(r, "Benutzerdefiniert")
        return 0

    scen = [
        ("Prototyp 4L 1.6 mm: 5 PCB / 2 bestueckt", dict(layers=4, thickness=1.6, pcb_qty=5, pcba_qty=2)),
        ("Prototyp 4L 1.6 mm: 5 PCB / 5 bestueckt", dict(layers=4, thickness=1.6, pcb_qty=5, pcba_qty=5)),
        ("Serie 4L 1.6 mm: 20 PCB / 16 bestueckt / 15 Sensoren",
         dict(layers=4, thickness=1.6, pcb_qty=20, pcba_qty=16, sensors=15)),
        ("Serie 4L 2.0 mm: 20/16/15 (nur Standard-PCBA)",
         dict(layers=4, thickness=2.0, pcb_qty=20, pcba_qty=16, sensors=15)),
        ("Serie 2L 1.6 mm: 20/16/15", dict(layers=2, thickness=1.6, pcb_qty=20, pcba_qty=16, sensors=15)),
    ]
    rows = []
    for t, kw in scen:
        r = compute(bom, **kw)
        report(r, t)
        rows.append((t, r))
    print("\n=== Uebersicht (CHF) ===")
    print(f"  {'Szenario':<52s} {'PCBA':>9s} {'Stueck':>8s} {'Einmal':>8s} {'Total':>8s} {'Voll':>8s}")
    for t, r in rows:
        print(f"  {t:<52s} {r['mode']:>9s} {r['unit_chf']:8.2f} {r['once_chf']:8.2f} {r['total_chf']:8.2f} "
              f"{r['full_chf']:8.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
