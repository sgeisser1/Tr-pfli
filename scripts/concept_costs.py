#!/usr/bin/env python3
"""fluidi - Kostenvergleich der Konzepte (Phase 2, docs/concepts/CONCEPTS.md v0.2).

Aufruf:  .venv/bin/python scripts/concept_costs.py            (alle Konzepte, Markdown-Tabellen)
         .venv/bin/python scripts/concept_costs.py --detail   (zusaetzlich Einzelberichte cost_model)
         .venv/bin/python scripts/concept_costs.py --csv      (BOM-CSV nach docs/concepts/bom/ schreiben)

Kostendefinition D-005 (Projektleiter 2026-11-06), umgesetzt in scripts/cost_model.py:
  Stueckkosten = alles pro Sensor (Bauteile in der Preisstaffel der Bestellmenge, PCB-Grenzkosten,
  Loetstellen, Roentgen, Zelle, Gehaeusematerial, Kleinteile, Ausschuss, Reserveboard),
  Einmalkosten = PCB-Fixanteil, Setup, Schablone, Extended-Gebuehren, Versand, Verzollung ...
  Vollkosten pro Sensor = Bestellung total / nutzbare Sensoren.

Bauteildaten: docs/concepts/bom/jlc_prices.json (scripts/jlc_price_cache.py, JLC-API, Abruf 2026-11-06):
  Basic/Preferred/Extended, Preisstaffeln, leastPatchNumber -> moq, lossNumber -> attrition.
Loetstellen = Pinzahl inkl. Exposed Pad (ANNAHME bis Footprint). Lokale Teile = ANNAHME, siehe unten.
"""
from __future__ import annotations

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cost_model as cm  # noqa: E402
from cost_model import BomLine as L  # noqa: E402

JLC = json.load(open(os.path.join(HERE, "..", "docs", "concepts", "bom", "jlc_prices.json"), encoding="utf-8"))

# ---------------------------------------------------------------------------------------------
# Lokal beschaffte Teile (CHF inkl. MWST). ANNAHME, wo nicht anders vermerkt.
# ---------------------------------------------------------------------------------------------
ASA_CHF_PER_G = 0.035      # ANNAHME: ASA-Filament ca. CHF 30-35/kg
SCREW_CHF = 0.10           # ANNAHME: unverlierbare Schraube M2 Edelstahl (REQ-SAF-CC-04)
INSERT_CHF = 0.10          # ANNAHME: Gewinde-Einschmelzmutter M2 (RT W-5)
SEAL_CHF = 0.15            # ANNAHME: je Dichtung; 2 Dichtungen (Batteriefach + Sonde, REQ-SAF-05; RT W-5)
POTTING_CHF = 0.40         # ANNAHME: Versiegelung Sonde/Dichtlinie (REQ-MECH-07)
EPOXY_2L_CHF = 0.60        # ANNAHME: Epoxid-Tauchbeschichtung Sonde 2 Lagen (Acryl ungeeignet, RT W-5)
AMS_PURGE_G = 4            # ANNAHME: Spuelabfall AMS fuer Logo, g ASA pro Sensor (RT W-5)
CR2450N_CHF = 4.10         # research_energie.md 1.2: Renata CR2450N CHF 3.70-4.50 (Mitte)
CR2032_RENATA_CHF = 2.65   # research_energie.md 1.2: Renata CR2032 CHF 2.65-3.00
CR2032_PANA_CHF = 1.38     # Panasonic CR2032, galaxus.ch 2er-Pack CHF 1.38/Stk (Suchergebnis 2026-11-06;
                           # 6er 0.54, 48er/120er 0.61 CHF/Stk) -> konservativ 1.38, vor Bestellung pruefen
LIPO_CHF = 6.00            # research_energie.md 2.1: ANNAHME CHF 4-8 (Mitte), Renata ICP401230UPR


def J(lcsc, qty, joints, label, leadless=False):
    """BOM-Zeile aus dem JLC-Cache."""
    d = JLC[lcsc]
    cat = "basic" if d["library"] == "base" else ("preferred" if d["preferred"] else "extended")
    tiers = tuple((int(a), float(b)) for a, b in d["tiers"])
    p20 = cm.part_price(L("x", 1, tiers=tiers), 20)
    return L(f"{label} {d['model']} {lcsc}", qty, p20, 0, cat, True, joints, max(1, int(d["least"])),
             int(d["loss"]), "JLC", tiers, leadless)


def LOK(label, chf):
    return L(label, 1, 0, chf, "none", False, 0, 1, 0, "LOKAL")


def merge(bom):
    """Gleiche LCSC-Nummern zusammenfassen (Pruefbericht Fertigung k-2)."""
    out, idx = [], {}
    for b in bom:
        key = b.part.split()[-1] if b.source == "JLC" else b.part
        if key in idx and b.source == "JLC":
            o = out[idx[key]]
            o.qty_per_board += b.qty_per_board
        else:
            idx[key] = len(out)
            out.append(L(**{**b.__dict__}))
    return out


# ---------------------------------------------------------------------------------------------
def cc2340_core():
    return [
        J("C20416850", 1, 25, "SoC", leadless=True),
        J("C2925606", 1, 4, "Quarz 48 MHz 8 pF"),
        J("C99010", 1, 2, "Quarz 32.768 kHz 9 pF"),
        J("C89132", 1, 2, "L 10uH DCDC"),
        J("C15525", 2, 2, "C 10uF VDDR/VDDS"),
        J("C1525", 7, 2, "C 100nF Abblock (VDDS x3, VDDR, TMP, OSZ, Reserve)"),
        J("C52923", 1, 2, "C 1uF VDDD"),
        J("C25741", 1, 2, "R 100k nRST-Pull-up"),
        J("C27123", 1, 2, "L 2.7nH LC-Filter"),
        J("C1552", 2, 2, "C 1.5pF LC-Filter"),
        J("C1548", 1, 2, "C 15pF DC-Block"),
        J("C17168", 1, 2, "R 0R Pi-Netz"),
    ]


def messkette():
    """RT K-1: Oszillator 2-8 MHz, Speisung High-Drive-GPIO, C-Umschaltung per GPIO (kein Analogschalter)."""
    return [
        J("C35740", 1, 5, "Oszillator Schmitt-Inverter"),
        J("C25900", 1, 2, "R 4.7k Oszillator-Rueckkopplung"),
        J("C1555", 1, 2, "C 22pF C0G Cref1 (Steigung)"),
        J("C1546", 1, 2, "C 100pF C0G Cref2 (f2, Salzdiagnose)"),
    ]


def tmp1075():
    """RT W-2/k-4: TMP1075 + I2C-Pull-ups an einem GPIO (0 uA im Schlaf).
    v0.3 (E2): TMP1075DGKR VSSOP-8 statt DSGR (WSON) -> nicht leadless, keine Roentgengebuehr."""
    return [J("C2864807", 1, 8, "Temp TMP1075 VSSOP-8"), J("C25900", 2, 2, "R 4.7k I2C-Pull-up")]


def ui_prog(lines=2):
    """S2-K01: keine VPROG-Leitung, keine Messbruecke, kein nRST-Pad. v0.3 (E3): nur Pads RX, TX je 2 x 100 kOhm."""
    return [
        J("C2286", 1, 2, "LED rot"), J("C25117", 1, 2, "R 470R LED"),
        J("C318884", 1, 4, "Taster"),
        J("C25741", 2 * lines, 2, "R 100k Pad-Serie (2 je Leitung)"),
    ]


def housing(grams):
    return [
        LOK(f"Gehaeuse ASA {grams} g + {AMS_PURGE_G} g AMS-Spuelung (ANNAHME)", (grams + AMS_PURGE_G) * ASA_CHF_PER_G),
        LOK("2 Dichtungen (ANNAHME)", 2 * SEAL_CHF),
        LOK("Versiegelung Sonde (ANNAHME)", POTTING_CHF),
        LOK("Schraube unverlierbar + Gewindeeinsatz (ANNAHME)", SCREW_CHF + INSERT_CHF),
    ]


BOM_A = merge(cc2340_core() + messkette() + tmp1075() + [
    J("C964809", 1, 2, "Halter CR2450"),
    J("C15127", 1, 3, "P-FET Verpolschutz"),
    J("C15008", 2, 2, "C 100uF Puffer (E1: 2 bestueckt + 2 DNM)"),
] + ui_prog() + [LOK("Zelle Renata CR2450N", CR2450N_CHF)] + housing(15))

BOM_A32 = merge(cc2340_core() + messkette() + tmp1075() + [
    J("C5213768", 1, 3, "Halter CR2032 Keystone 3034 (Minuspol = ENIG-Pad)"),
    J("C15127", 1, 3, "P-FET Verpolschutz"),
    J("C15008", 2, 2, "C 100uF Puffer (E1: 2 bestueckt + 2 DNM)"),
] + ui_prog() + [LOK("Zelle Panasonic CR2032", CR2032_PANA_CHF)] + housing(11))

BOM_A2 = merge(BOM_A + [LOK("Epoxid-Tauchbeschichtung Sonde 2 L (ANNAHME)", EPOXY_2L_CHF)])

BOM_B = merge([
    J("C39831287", 1, 29, "SoC", leadless=True),
    J("C9009", 1, 4, "Quarz 32 MHz"),
    J("C32346", 1, 2, "Quarz 32.768 kHz 12.5 pF"),
    J("C89132", 1, 2, "L 10uH DC-DC"),
    J("C23733", 1, 2, "C 4.7uF VDCID"),
    J("C15525", 1, 2, "C 10uF"),
    J("C1525", 5, 2, "C 100nF"),
    J("C17168", 1, 2, "R 0R Pi-Netz"),
] + tmp1075() + [
    J("C70377", 1, 2, "Halter CR2032"),
    J("C15127", 1, 3, "P-FET Verpolschutz"),
    J("C15008", 3, 2, "C 100uF Puffer (245 uF pess.)"),
] + ui_prog() + [LOK("Zelle Renata CR2032", CR2032_RENATA_CHF)] + housing(10))

BOM_C = merge(cc2340_core() + [
    J("C968585", 1, 13, "CDC FDC2212", leadless=True),
    J("C1035", 2, 2, "L 10uH LC-Tank"),
    J("C1555", 2, 2, "C 22pF LC-Tank"),
] + tmp1075() + [
    J("C202311", 1, 6, "Lader"), J("C25744", 1, 2, "R 10k ISET"),
    J("C77131", 1, 2, "NTC 10k"), J("C27001", 1, 2, "R 237k TS"),
    J("C52923", 4, 2, "C 1uF IN/OUT"),
    J("C183096", 1, 7, "Schutz-IC", leadless=True), J("C908265", 1, 6, "Doppel-N-FET"),
    J("C25117", 1, 2, "R 470R Schutz-IC"), J("C25879", 1, 2, "R 2.2k Schutz-IC"),
    J("C15127", 2, 3, "P-FET Verpol + Teiler"),
    J("C3747031", 1, 5, "LDO 3.0 V"), J("C456012", 1, 10, "USB-C"), J("C25905", 2, 2, "R 5.1k CC"),
    J("C2984676", 1, 2, "PPTC"), J("C148209", 1, 2, "TVS"),
    J("C26083", 2, 2, "R 1M Teiler"), J("C8545", 1, 3, "N-FET Teiler"),
] + ui_prog() + [
    LOK("Akku Renata ICP401230UPR (ANNAHME Preis)", LIPO_CHF),
    LOK("Waermeschutz Zelle + Klebepad (ANNAHME)", 0.30),
    LOK("Abdeckung Ladeport TPU (ANNAHME)", 0.05),
] + housing(14))

LCSC_ALL = {b.part.split()[-1] for bom in (BOM_A, BOM_A32, BOM_B, BOM_C) for b in bom if b.source == "JLC"}

# (BOM, Lagen, ENIG)
CONCEPTS = {
    "A (CR2450N, 4 L)": (BOM_A, 4, False),
    "A-32 (Panasonic CR2032, 4 L, ENIG)": (BOM_A32, 4, True),
    "A2 (CR2450N, 2 L + Epoxid)": (BOM_A2, 2, False),
    "B (CH592F, 4 L)": (BOM_B, 4, False),
    "C (Akku, 4 L)": (BOM_C, 4, False),
}

SCEN = {
    "Prototyp 5 PCB / 5 bestueckt": dict(pcb_qty=5, pcba_qty=5, sensors=5),
    "Prototyp 5 PCB / 2 bestueckt": dict(pcb_qty=5, pcba_qty=2, sensors=2),
    "Serie 20 PCB / 16 bestueckt / 15 Sensoren": dict(pcb_qty=20, pcba_qty=16, sensors=15),
}


def run(bom, layers, enig=False, **kw):
    return cm.compute(bom, layers, 1.6, enig=enig, **kw)


def summarize(bom):
    ext = [b for b in bom if b.jlc_assembled and b.category == "extended"]
    pref = [b for b in bom if b.jlc_assembled and b.category == "preferred"]
    basic = [b for b in bom if b.jlc_assembled and b.category == "basic"]
    lok = sum(b.unit_price_chf for b in bom if b.source == "LOKAL")
    return len(ext), len(pref), len(basic), lok


def write_csv(outdir):
    os.makedirs(outdir, exist_ok=True)
    names = {"A (CR2450N, 4 L)": "A", "A-32 (Panasonic CR2032, 4 L, ENIG)": "A32", "A2 (CR2450N, 2 L + Epoxid)": "A2",
             "B (CH592F, 4 L)": "B", "C (Akku, 4 L)": "C"}
    for old in ("bom_B2.csv", "bom_B_Osz.csv"):
        p = os.path.join(outdir, old)
        if os.path.exists(p):
            os.remove(p)
    fields = ["part", "qty_per_board", "unit_price_usd", "unit_price_chf", "category", "jlc_assembled",
              "joints", "moq", "attrition", "source", "tiers", "leadless"]
    for name, (bom, _, _) in CONCEPTS.items():
        fn = os.path.join(outdir, f"bom_{names[name]}.csv")
        with open(fn, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(fields)
            for b in bom:
                w.writerow([b.part, b.qty_per_board, b.unit_price_usd, round(b.unit_price_chf, 4), b.category,
                            "ja" if b.jlc_assembled else "nein", b.joints, b.moq, b.attrition, b.source,
                            "|".join(f"{a}:{p}" for a, p in b.tiers), "ja" if b.leadless else "nein"])
        print("geschrieben:", os.path.relpath(fn))


def main():
    if "--csv" in sys.argv:
        write_csv(os.path.join(HERE, "..", "docs", "concepts", "bom"))
        return
    print("# fluidi Konzeptkosten - Ausgabe scripts/concept_costs.py (Kostendefinition D-005)\n")
    print(f"USD->CHF {cm.USD_TO_CHF:.4f}; PCB fix/Grenzkosten D-005; Versand GSDL bis 65 USD Warenwert, sonst DHL; "
          f"1.6 mm, PCBA auto; Roentgen ein; Pre-reflow aus (W-2, siehe Abschnitt 4); "
          f"JLC-Teiledaten Abruf {JLC['_abruf']}.\n")
    print("## 1 BOM-Uebersicht\n")
    print("| Konzept | Extended-Typen | Preferred | Basic | lokal CHF/Sensor (ohne Ausschuss) |")
    print("|---|---|---|---|---|")
    for name, (bom, _, _) in CONCEPTS.items():
        e, p, b, lok = summarize(bom)
        print(f"| {name} | {e} | {p} | {b} | {lok:.2f} |")

    print("\n## 2 Stueck-, Einmal- und Vollkosten (CHF)\n")
    print("| Konzept | Szenario | Versand | Stueck CHF | Einmal CHF | Bestellung total CHF | Vollkosten/Sensor CHF |"
          " Warenwert USD (GSDL <= 65) | Abgaben CHF (frei <= 5) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, (bom, layers, enig) in CONCEPTS.items():
        for sn, kw in SCEN.items():
            r = run(bom, layers, enig, **kw)
            ww = r["goods_usd"] - r["once"].get(f"Versand {r['ship']}", 0)
            print(f"| {name} | {sn} | {r['ship']} | **{r['unit_chf']:.2f}** | {r['once_chf']:.2f} | "
                  f"{r['total_chf']:.2f} | {r['full_chf']:.2f} | {ww:.1f} | {r['vat_chf']:.2f} |")

    print("\n## 3 Option Prototyp-Los: zusaetzlich 2-Lagen-Variante A2 (eigene Bestellung)\n")
    for sn in ("Prototyp 5 PCB / 2 bestueckt", "Prototyp 5 PCB / 5 bestueckt"):
        r = run(BOM_A2, 2, False, **SCEN[sn])
        print(f"- A2 {sn}: Bestellung total {r['total_chf']:.2f} CHF (Versand {r['ship']}), "
              f"Einmal {r['once_chf']:.2f} CHF")

    print("\n## 4 Offener Posten 'Pre-reflow soldering' (Fertigung W-2): Serie 20/16/15, Stueckkosten CHF\n")
    print("| Konzept | ohne Pre-reflow | mit 0.016 USD/Loetstelle | Differenz |")
    print("|---|---|---|---|")
    for name, (bom, layers, enig) in CONCEPTS.items():
        a = run(bom, layers, enig, **SCEN["Serie 20 PCB / 16 bestueckt / 15 Sensoren"])["unit_chf"]
        b = run(bom, layers, enig, pre_reflow=True, **SCEN["Serie 20 PCB / 16 bestueckt / 15 Sensoren"])["unit_chf"]
        print(f"| {name} | {a:.2f} | {b:.2f} | +{b - a:.2f} |")

    print("\n## 5 Vergleich 2 vs. 4 Lagen (BOM A ohne Coating), Serie 20/16/15\n")
    r4 = run(BOM_A, 4, False, **SCEN["Serie 20 PCB / 16 bestueckt / 15 Sensoren"])
    r2 = run(BOM_A, 2, False, **SCEN["Serie 20 PCB / 16 bestueckt / 15 Sensoren"])
    print(f"| Lagen | Stueck CHF | Einmal CHF | Vollkosten/Sensor CHF |\n|---|---|---|---|\n"
          f"| 4 L | {r4['unit_chf']:.2f} | {r4['once_chf']:.2f} | {r4['full_chf']:.2f} |\n"
          f"| 2 L | {r2['unit_chf']:.2f} | {r2['once_chf']:.2f} | {r2['full_chf']:.2f} |")

    if "--detail" in sys.argv:
        for name, (bom, layers, enig) in CONCEPTS.items():
            for sn, kw in SCEN.items():
                cm.report(run(bom, layers, enig, **kw), f"{name} - {sn}")


if __name__ == "__main__":
    main()
