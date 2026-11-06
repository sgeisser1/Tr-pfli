#!/usr/bin/env python3
"""Troepfli - Kostenvergleich der Konzepte A/B/B2/C (Phase 2, docs/concepts/CONCEPTS.md).

Aufruf:  .venv/bin/python scripts/concept_costs.py            (alle Konzepte, Markdown-Tabellen)
         .venv/bin/python scripts/concept_costs.py --detail   (zusaetzlich Einzelberichte cost_model)
         .venv/bin/python scripts/concept_costs.py --csv      (BOM-CSV nach docs/concepts/bom/ schreiben)

Nutzt scripts/cost_model.py unveraendert (compute/report). Nur Standardbibliothek.

Datenquellen der BOM-Zeilen:
  - JLC-Teilesuche (API selectSmtComponentList), Abruf 2026-11-06: Basic/Extended, Lager,
    Stueckpreis in der Staffel mit 20 Stk ("p20"), leastPatchNumber -> moq, lossNumber -> attrition.
  - LOKAL (CHF inkl. MWST): Zellpreise aus docs/concepts/research_energie.md 1.2/2.1,
    Gehaeuse/Kleinteile = ANNAHME (unten markiert).
Loetstellen (joints) = Pinzahl laut Gehaeuse (inkl. Exposed Pad), ANNAHME bis zum Footprint.
"""
from __future__ import annotations

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cost_model as cm  # noqa: E402
from cost_model import BomLine as L  # noqa: E402

# ---------------------------------------------------------------------------------------------
# ANNAHMEN lokal beschaffter Teile (CHF inkl. MWST)
# ---------------------------------------------------------------------------------------------
ASA_CHF_PER_G = 0.035      # ANNAHME: ASA-Filament ca. CHF 30-35/kg (Bambu), inkl. Fehldrucke nicht
SCREW_CHF = 0.10           # ANNAHME: unverlierbare Schraube M2 Edelstahl (REQ-SAF-CC-04)
SEAL_CHF = 0.15            # ANNAHME: O-Ring/Dichtung Batteriefach bzw. Ladeport (REQ-MECH-13/15)
POTTING_CHF = 0.40         # ANNAHME: Versiegelung Sonde/Dichtlinie (Epoxid/Coating, REQ-MECH-07)
CR2450N_CHF = 4.10         # research_energie.md 1.2: CHF 3.70-4.50 (Mitte), Renata CR2450N
CR2032_CHF = 2.65          # research_energie.md 1.2: CHF 2.65-3.00 (unterer Wert, ab 2 Stk), Renata CR2032
LIPO_CHF = 6.00            # research_energie.md 2.1: ANNAHME CHF 4-8 (Mitte), Renata ICP401230UPR
COAT_2L_CHF = 0.30         # ANNAHME B2: Conformal Coating der Sonde selbst (Spray/Tauchen) pro Sensor


def common_ui_prog():
    """LED, Taster, Programmier-Rueckstromsperre, Strommessbruecke (alle Basic)."""
    return [
        L("LED rot 0603 KT-0603R C2286", 1, 0.0077, 0, "basic", True, 2, 20, 10),
        L("R 470R 0402 LED C25117", 1, 0.0010, 0, "basic", True, 2, 20, 10),
        L("Taster 5.1x5.1 TS-1187A C318884", 1, 0.0207, 0, "basic", True, 4, 5, 8),
        L("Diode 1N4148WS VPROG C2128", 1, 0.0112, 0, "basic", True, 2, 20, 12),
        L("R 100R 0402 VPROG C25076", 1, 0.0012, 0, "basic", True, 2, 20, 15),
        L("R 1k 0402 UART-Serie C11702", 2, 0.0013, 0, "basic", True, 2, 20, 10),
        L("R 0R 0402 Strommessbruecke C17168", 1, 0.0011, 0, "basic", True, 2, 20, 10),
    ]


def cc2340_core(rf_full=False):
    b = [
        L("SoC CC2340R52E0RGER C20416850", 1, 1.3375, 0, "extended", True, 25, 1, 0),
        L("Quarz 48 MHz XXHCELNANF C5160139", 1, 0.1430, 0, "extended", True, 4, 5, 2),
        L("Quarz 32.768 kHz 9 pF Q13FC13500003 C99010", 1, 0.2040, 0, "extended", True, 2, 5, 2),
        L("L 10uH 0806 DCDC WPN201610H100MT C89132", 1, 0.0418, 0, "extended", True, 2, 5, 4),
        L("C 10uF 0402 CL05A106MQ5NUNC C15525", 2, 0.0258, 0, "basic", True, 2, 20, 10),
        L("C 100nF 0402 CL05B104KO5NNNC C1525", 7, 0.0031, 0, "basic", True, 2, 20, 10),
        L("C 1uF 0402 CL05A105KA5NQNC C52923", 1, 0.0058, 0, "basic", True, 2, 20, 12),
        L("R 100k 0402 nRST C25741", 1, 0.0013, 0, "basic", True, 2, 20, 12),
        # HF: LC-Filter nach TI-Referenz (SWRA834A S.5 Abb. 3-1: 2.8 nH -> 2.7 nH 0402, 2 x 1.5 pF, 15 pF)
        L("L 2.7nH 0402 SDCL1005C2N7STDF C27123", 1, 0.0031, 0, "extended", True, 2, 20, 10),
        L("C 1.5pF 0402 C0G 0402CG1R5C500NT C1552", 2, 0.0045, 0, "extended", True, 2, 20, 10),
        L("C 15pF 0402 C0G 0402CG150J500NT C1548", 1, 0.0026, 0, "basic", True, 2, 20, 10),
        # Pi-Netz: Bestueckung 0R (Basic), Querglieder DNM, Abstimmung am Prototyp
        L("R 0R 0402 Pi-Netz C17168", 1, 0.0011, 0, "basic", True, 2, 20, 10),
    ]
    if rf_full:
        b += [L("L 2nH 0402 SDCL1005C2N0STDF C43365", 1, 0.0062, 0, "extended", True, 2, 20, 10),
              L("C 1.2pF 0402 0402CG1R2C500NT C1551", 1, 0.0049, 0, "extended", True, 2, 20, 10)]
    return b


def tmp1075():
    return [
        L("Temp TMP1075DSGR C2870250", 1, 0.3111, 0, "extended", True, 9, 1, 0),
        L("R 4.7k 0402 I2C-Pull-up C25900", 2, 0.0017, 0, "basic", True, 2, 20, 10),
    ]


def housing(grams):
    return [
        L(f"Gehaeuse ASA {grams} g (ANNAHME {ASA_CHF_PER_G} CHF/g)", 1, 0, grams * ASA_CHF_PER_G, "none", False,
          0, 1, 0, "LOKAL"),
        L("Dichtung/O-Ring (ANNAHME)", 1, 0, SEAL_CHF, "none", False, 0, 1, 0, "LOKAL"),
        L("Versiegelung Sonde (ANNAHME)", 1, 0, POTTING_CHF, "none", False, 0, 1, 0, "LOKAL"),
    ]


# ---------------------------------------------------------------------------------------------
# Konzept A "Knopf": CC2340R52 + LVC1G14-Oszillator + TMP1075 + CR2450N
# ---------------------------------------------------------------------------------------------
BOM_A = cc2340_core() + [
    L("Oszillator SN74LVC1G14DCKR C35740", 1, 0.0567, 0, "extended", True, 5, 5, 4),
    L("R 2.2k 0402 Oszillator f1 C25879", 1, 0.0011, 0, "basic", True, 2, 20, 10),
    L("R 22k 0402 Oszillator f2 C25768", 1, 0.0012, 0, "basic", True, 2, 20, 10),
    L("C 22pF 0402 C0G Referenz C1555", 1, 0.0019, 0, "basic", True, 2, 20, 10),
] + tmp1075() + [
    L("Halter CR2450 BS-24-B4AA016 C964809", 1, 0.4748, 0, "extended", True, 2, 2, 0),
    L("P-MOSFET Verpolschutz AO3401A C15127", 1, 0.0829, 0, "basic", True, 3, 5, 4),
    L("C 100uF 1206 Puffer CL31A107MQHNNNE C15008", 2, 0.1091, 0, "basic", True, 2, 5, 4),
] + common_ui_prog() + [
    L("Zelle Renata CR2450N (lokal)", 1, 0, CR2450N_CHF, "none", False, 0, 1, 0, "LOKAL"),
    L("Schraube unverlierbar (ANNAHME)", 1, 0, SCREW_CHF, "none", False, 0, 1, 0, "LOKAL"),
] + housing(15)

# ---------------------------------------------------------------------------------------------
# Konzept B "Spar": CH592F + Touch-Key (LVC1G14 als DNM-Rueckfall) + TMP1075 + CR2032
# ---------------------------------------------------------------------------------------------
BOM_B = [
    L("SoC CH592F C39831287", 1, 0.6696, 0, "extended", True, 29, 1, 0),
    L("Quarz 32 MHz X322532MOB4SI C9009", 1, 0.0957, 0, "extended", True, 4, 5, 4),
    L("Quarz 32.768 kHz 12.5 pF Q13FC13500004 C32346", 1, 0.1715, 0, "basic", True, 2, 5, 1),
    L("L 10uH 0806 DC-DC WPN201610H100MT C89132", 1, 0.0418, 0, "extended", True, 2, 5, 4),
    L("C 4.7uF 0402 VDCID CL05A475MP5NRNC C23733", 1, 0.0118, 0, "basic", True, 2, 20, 10),
    L("C 10uF 0402 CL05A106MQ5NUNC C15525", 1, 0.0258, 0, "basic", True, 2, 20, 10),
    L("C 100nF 0402 CL05B104KO5NNNC C1525", 5, 0.0031, 0, "basic", True, 2, 20, 10),
    L("R 0R 0402 Pi-Netz C17168", 1, 0.0011, 0, "basic", True, 2, 20, 10),
] + tmp1075() + [
    L("Halter CR2032 CR2032-BS-6-1 C70377", 1, 0.1420, 0, "extended", True, 2, 5, 1),
    L("P-MOSFET Verpolschutz AO3401A C15127", 1, 0.0829, 0, "basic", True, 3, 5, 4),
    L("C 100uF 1206 Puffer CL31A107MQHNNNE C15008", 2, 0.1091, 0, "basic", True, 2, 5, 4),
] + common_ui_prog() + [
    L("Zelle Renata CR2032 (lokal)", 1, 0, CR2032_CHF, "none", False, 0, 1, 0, "LOKAL"),
    L("Schraube unverlierbar (ANNAHME)", 1, 0, SCREW_CHF, "none", False, 0, 1, 0, "LOKAL"),
] + housing(10)

# B2: wie B, 2 Lagen, Sonde selbst beschichtet (Elektroden aussen, Coating statt Prepreg)
BOM_B2 = BOM_B + [L("Coating Sonde 2 Lagen (ANNAHME, selbst)", 1, 0, COAT_2L_CHF, "none", False, 0, 1, 0, "LOKAL")]

# A2: wie A, 2 Lagen, Sonde selbst beschichtet (Vergleich 2 vs. 4 Lagen)
BOM_A2 = BOM_A + [L("Coating Sonde 2 Lagen (ANNAHME, selbst)", 1, 0, COAT_2L_CHF, "none", False, 0, 1, 0, "LOKAL")]

# Option: RC-Oszillator in B bestueckt (Rueckfall falls Touch-Key nicht genuegt)
BOM_B_OSC = BOM_B + [
    L("Oszillator SN74LVC1G14DCKR C35740", 1, 0.0567, 0, "extended", True, 5, 5, 4),
    L("R 2.2k 0402 Oszillator f1 C25879", 1, 0.0011, 0, "basic", True, 2, 20, 10),
    L("C 22pF 0402 C0G Referenz C1555", 1, 0.0019, 0, "basic", True, 2, 20, 10),
]

# ---------------------------------------------------------------------------------------------
# Konzept C "Akku": CC2340R52 + FDC2212 + TMP1075 + LiPo 125 mAh + BQ21040 + BQ29700 + TPS7A02
# ---------------------------------------------------------------------------------------------
BOM_C = cc2340_core() + [
    L("CDC FDC2212DNTR C968585", 1, 6.0244, 0, "extended", True, 13, 1, 0),
    L("L 10uH 0603 LC-Tank SDFL1608S100KTF C1035", 2, 0.0279, 0, "basic", True, 2, 20, 10),
    L("C 22pF 0402 C0G LC-Tank C1555", 2, 0.0019, 0, "basic", True, 2, 20, 10),
] + tmp1075() + [
    L("Lader BQ21040DBVR C202311", 1, 0.4137, 0, "extended", True, 6, 5, 0),
    L("R 10k 0402 ISET C25744", 1, 0.0028, 0, "basic", True, 2, 20, 15),
    L("NTC 10k NCP15XH103F03RC C77131", 1, 0.0167, 0, "extended", True, 2, 20, 12),
    L("R 237k 0402 TS C27001", 1, 0.0032, 0, "extended", True, 2, 20, 10),
    L("C 1uF 0402 25V IN/OUT CL05A105KA5NQNC C52923", 4, 0.0058, 0, "basic", True, 2, 20, 12),
    L("Schutz-IC BQ29700DSER C183096", 1, 0.4142, 0, "extended", True, 7, 5, 0),
    L("Doppel-N-FET FS8205A C908265", 1, 0.0718, 0, "extended", True, 6, 5, 4),
    L("R 470R 0402 Schutz-IC VDD C25117", 1, 0.0010, 0, "basic", True, 2, 20, 10),
    L("R 2.2k 0402 Schutz-IC V- C25879", 1, 0.0011, 0, "basic", True, 2, 20, 10),
    L("P-MOSFET Verpolschutz AO3401A C15127", 1, 0.0829, 0, "basic", True, 3, 5, 4),
    L("LDO 3.0 V TPS7A0230PDBVR C3747031", 1, 0.2800, 0, "extended", True, 5, 1, 0),
    L("USB-C 6P SHOU HAN C456012", 1, 0.0390, 0, "extended", True, 10, 1, 2),
    L("R 5.1k 0402 CC C25905", 2, 0.0023, 0, "basic", True, 2, 20, 15),
    L("PPTC 500 mA 24 V C2984676", 1, 0.0901, 0, "extended", True, 2, 5, 2),
    L("TVS SMAJ20A C148209", 1, 0.1038, 0, "extended", True, 2, 5, 2),
    L("Teiler Batteriespannung R 1M 0402 C26083", 2, 0.0012, 0, "basic", True, 2, 20, 15),
    L("Teiler-Schalter P-FET AO3401A C15127", 1, 0.0829, 0, "basic", True, 3, 5, 4),
    L("Teiler-Schalter N-FET 2N7002 C8545", 1, 0.0171, 0, "basic", True, 3, 10, 8),
] + common_ui_prog() + [
    L("Akku Renata ICP401230UPR 125 mAh (ANNAHME Preis)", 1, 0, LIPO_CHF, "none", False, 0, 1, 0, "LOKAL"),
    L("Waermeschutz Zelle + Klebepad (ANNAHME)", 1, 0, 0.30, "none", False, 0, 1, 0, "LOKAL"),
    L("Abdeckung Ladeport TPU (ANNAHME)", 1, 0, 0.05, "none", False, 0, 1, 0, "LOKAL"),
] + housing(14)

CONCEPTS = {
    "A Knopf (4L)": (BOM_A, 4),
    "A2 Knopf (2L+Coating)": (BOM_A2, 2),
    "B Spar (4L)": (BOM_B, 4),
    "B2 Spar (2L+Coating)": (BOM_B2, 2),
    "B+Osz. (4L, Rueckfall bestueckt)": (BOM_B_OSC, 4),
    "C Akku (4L)": (BOM_C, 4),
}

SCEN = {
    "Prototyp 5 PCB / 2 bestueckt": dict(pcb_qty=5, pcba_qty=2),
    "Prototyp 5 PCB / 5 bestueckt": dict(pcb_qty=5, pcba_qty=5),
    "Serie 15 / 15": dict(pcb_qty=15, pcba_qty=15),
}


def summarize(bom):
    ext = sorted({b.part for b in bom if b.jlc_assembled and b.category == "extended"})
    basic = sorted({b.part for b in bom if b.jlc_assembled and b.category == "basic"})
    comp = sum(b.qty_per_board * b.unit_price_usd for b in bom if b.source != "LOKAL")
    lokal = sum(b.qty_per_board * b.unit_price_chf for b in bom if b.source == "LOKAL")
    return len(ext), len(basic), comp, lokal


def run(bom, layers, scale=1.0, **kw):
    orig = dict(cm.PCB_PRICE_USD)
    try:
        for k in cm.PCB_PRICE_USD:
            cm.PCB_PRICE_USD[k] = orig[k] * scale
        return cm.compute(bom, layers, 1.6, **kw)
    finally:
        cm.PCB_PRICE_USD.clear()
        cm.PCB_PRICE_USD.update(orig)


def write_csv(outdir):
    os.makedirs(outdir, exist_ok=True)
    fields = ["part", "qty_per_board", "unit_price_usd", "unit_price_chf", "category", "jlc_assembled",
              "joints", "moq", "attrition", "source"]
    for name, (bom, _) in CONCEPTS.items():
        short = name.split()[0].replace("+Osz.", "_Osz")
        fn = os.path.join(outdir, f"bom_{short}.csv")
        with open(fn, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(fields)
            for b in bom:
                w.writerow([b.part, b.qty_per_board, b.unit_price_usd, b.unit_price_chf, b.category,
                            "ja" if b.jlc_assembled else "nein", b.joints, b.moq, b.attrition, b.source])
        print("geschrieben:", fn)


def main():
    if "--csv" in sys.argv:
        write_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "concepts", "bom"))
        return
    print(f"# Troepfli Konzeptkosten - Ausgabe scripts/concept_costs.py\n")
    print(f"USD->CHF {cm.USD_TO_CHF:.4f} ({cm.FX_DATE}); PCB-Preise und Versand aus dem JLC-Rechner (Auftraggeber, 2026-11-06); "
          f"Versand GSDL wenn Warenwert <= 65 USD, sonst DHL; 1.6 mm, PCBA auto.\n")
    print("## 1 BOM-Uebersicht\n")
    print("| Konzept | Extended-Typen (JLC) | Basic-Typen | Bauteile JLC USD/Sensor | lokal CHF/Sensor |")
    print("|---|---|---|---|---|")
    for name, (bom, layers) in CONCEPTS.items():
        e, b, comp, lok = summarize(bom)
        print(f"| {name} | {e} | {b} | {comp:.2f} | {lok:.2f} |")

    print("\n## 2 Stueck- und Einmalkosten (CHF)\n")
    print("| Konzept | Szenario | PCBA | Stueck CHF | davon PCB-Anteil USD | Einmal CHF | Bestellung total CHF |")
    print("|---|---|---|---|---|---|---|")
    for name, (bom, layers) in CONCEPTS.items():
        for sn, kw in SCEN.items():
            r = run(bom, layers, **kw)
            print(f"| {name} | {sn} | {r['mode']} | **{r['unit_chf']:.2f}** | "
                  f"{r['unit']['PCB (Anteil pro Platine)']:.2f} | {r['once_chf']:.2f} | {r['total_chf']:.2f} |")

    print("\n## 3 Vergleich 2 vs. 4 Lagen (gleiche BOM, ohne Coating-Zuschlag), Stueckkosten CHF\n")
    print("| BOM | Prototyp 5/2 4L | Prototyp 5/2 2L | Serie 15/15 4L | Serie 15/15 2L | Differenz Serie |")
    print("|---|---|---|---|---|---|")
    for name, bom in (("A", BOM_A), ("B", BOM_B), ("C", BOM_C)):
        v = {(l, q): run(bom, l, pcb_qty=q[0], pcba_qty=q[1])["unit_chf"] for l in (4, 2) for q in ((5, 2), (15, 15))}
        print(f"| {name} | {v[(4,(5,2))]:.2f} | {v[(2,(5,2))]:.2f} | {v[(4,(15,15))]:.2f} | {v[(2,(15,15))]:.2f} | "
              f"{v[(4,(15,15))]-v[(2,(15,15))]:.2f} |")

    print("\n## 4 Versandart und Hinweise je Szenario\n")
    for name, (bom, layers) in CONCEPTS.items():
        for sn, kw in SCEN.items():
            r = run(bom, layers, **kw)
            print(f"- {name} / {sn}: Versand {r['ship']}; " + ("; ".join(r["notes"]) or "-"))

    if "--detail" in sys.argv:
        for name, (bom, layers) in CONCEPTS.items():
            for sn, kw in SCEN.items():
                cm.report(run(bom, layers, **kw), f"{name} - {sn}")


if __name__ == "__main__":
    main()
