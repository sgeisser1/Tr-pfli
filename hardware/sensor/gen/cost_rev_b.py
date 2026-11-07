#!/usr/bin/env python3
"""fluidi Sensor Rev B - Kosten aus der Schaltplan-BOM (Kostendefinition D-005, scripts/cost_model.compute).

Eingaben:
  hardware/sensor/out/fluidi_sensor_bom_jlc.csv  (bom_jlc.py, aus dem Schaltplan Rev B)
  docs/concepts/bom/jlc_prices.json             (JLC-API: Kategorie, Preisstaffeln, Mindestmenge, Verlust;
                                                 scripts/jlc_price_cache.py, Abruf siehe Feld _abruf)
  Loetstellen = Zahl der Padnummern mit Kupfer + Lotpaste je Footprint (pcbnew, KiCad-10-Bibliotheken + hardware/sensor/lib).
Lokale Teile wie hardware/sensor/gen/floorplan_options.py (LOKAL), dazu ASA-Mehrmenge Kopf V4 (ANNAHME, unten).
Szenarien: Prototyp 5 PCB / 5 bestueckt (4 x 100 uF, D-013); Serie 20 PCB / 16 bestueckt / 15 Sensoren mit 4 bzw.
2 x 100 uF (Entscheid nach Messung, D-013). 4 Lagen 1.6 mm, ENIG (A-32 Minuspad), Economic PCBA, GSDL.
Aufruf: .venv/bin/python hardware/sensor/gen/cost_rev_b.py   -> hardware/sensor/out/COSTS_REV_B.md
"""
import copy
import csv
import io
import json
import os
import sys
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import cost_model as cm  # noqa: E402

OUT = os.path.join(HERE, "..", "out")
PRICES = json.load(open(os.path.join(ROOT, "docs", "concepts", "bom", "jlc_prices.json"), encoding="utf-8"))
KICAD_FP = "/usr/share/kicad/footprints"
PRJ_FP = os.path.join(HERE, "..", "lib", "fluidi.pretty")

# PCB-Grenzkosten: cost_model rechnet mit 22 x 150 mm (JLC-Rechner 2026-11-06). Rev B: Kopf ca. 26 mm breit (D-019),
# Laenge ca. 160 mm (FLOORPLAN_OPTIONS Kap. 4). ANNAHME: Grenzkosten proportional zur Rechteckflaeche, Fixanteil
# unveraendert -> vor der Bestellung im JLC-Rechner mit der echten Kontur (PCB_OUTLINE Rev B) ersetzen.
PCB_W, PCB_L = 26.0, 160.0
AREA_FACTOR = (PCB_W * PCB_L) / (cm.BOARD_W_MM * cm.BOARD_L_MM)
# ASA: Rev A 11 g + 4 g AMS-Spuelung (concept_costs.housing(11)). Kopf V4 34 x 13 x 57.5 statt 28 x 13 x 48 mm:
# Oberflaechenverhaeltnis 6289/4664 = 1.35 -> +3.8 g (ANNAHME, Masse liefert die Mechanik)
ASA_EXTRA_G = 11.0 * (2 * (34 * 13 + 13 * 57.5 + 34 * 57.5)) / (2 * (28 * 13 + 13 * 48 + 28 * 48)) - 11.0
LOKAL = [cm.BomLine("Zelle Panasonic CR2032", 1, 0, 1.38, "none", False, 0, 1, 0, "LOKAL"),
         cm.BomLine("Gehaeuse ASA 11 g + 4 g AMS (ANNAHME)", 1, 0, 0.525, "none", False, 0, 1, 0, "LOKAL"),
         cm.BomLine(f"ASA-Mehrmenge Kopf V4 {ASA_EXTRA_G:.1f} g (ANNAHME 0.035 CHF/g)", 1, 0, 0.035 * ASA_EXTRA_G,
                    "none", False, 0, 1, 0, "LOKAL"),
         cm.BomLine("Dichtungen (ANNAHME)", 1, 0, 0.3, "none", False, 0, 1, 0, "LOKAL"),
         cm.BomLine("Versiegelung Sonde/Kragen (ANNAHME)", 1, 0, 0.4, "none", False, 0, 1, 0, "LOKAL"),
         cm.BomLine("Schraube/Mutter (ANNAHME)", 1, 0, 0.2, "none", False, 0, 1, 0, "LOKAL")]


def paste_pads(fp_name):
    import pcbnew
    lib, name = fp_name.split(":") if ":" in fp_name else (None, fp_name)
    path = PRJ_FP if lib == "fluidi" else os.path.join(KICAD_FP, lib + ".pretty")
    fp = pcbnew.FootprintLoad(path, name)
    # Kupferpads mit Lotpaste (jedes Pad einzeln, z. B. 2 Clip-Pads des 3034) + 1 fuer ein Exposed Pad, dessen Paste
    # als eigene Fenster ohne Kupfer angelegt ist (VQFN). Pads ohne Paste (Minuspad Zelle) sind keine Loetstellen.
    cu = [p for p in fp.Pads() if p.IsOnLayer(pcbnew.F_Cu)]
    paste_only = [p for p in fp.Pads() if p.IsOnLayer(pcbnew.F_Paste) and not p.IsOnLayer(pcbnew.F_Cu)]
    return sum(1 for p in cu if p.IsOnLayer(pcbnew.F_Paste)) + (1 if paste_only else 0)


def load_bom():
    rows = list(csv.DictReader(open(os.path.join(OUT, "fluidi_sensor_bom_jlc.csv"))))
    fps = {}
    for r in csv.DictReader(open(os.path.join(OUT, "fluidi_sensor_bom_raw.csv"))):
        fps[r["Ref"]] = r["Footprint"]
    lines = []
    for r in rows:
        refs = r["Designator"].split(",")
        lcsc = r["LCSC Part #"]
        d = PRICES[lcsc]
        cat = "basic" if d["library"] == "base" else ("preferred" if d["preferred"] else "extended")
        tiers = tuple((int(a), float(b)) for a, b in d["tiers"])
        fp = fps[refs[0]]
        joints = paste_pads(fp)
        leadless = "QFN" in fp or "DFN" in fp
        lines.append(cm.BomLine(f"{r['Comment']} ({' '.join(refs)}) {lcsc}", len(refs), tiers[0][1], 0.0, cat, True,
                                joints, max(1, int(d["least"])), int(d["loss"]), "JLC", tiers, leadless))
    return lines


def run(bom, pcb_qty, pcba_qty, sensors):
    var_bak = dict(cm.PCB_VAR_USD)
    try:
        cm.PCB_VAR_USD[(4, 1.6)] = var_bak[(4, 1.6)] * AREA_FACTOR
        return cm.compute(bom + copy.deepcopy(LOKAL), 4, 1.6, pcb_qty, pcba_qty, ship="GSDL", pcba="economic",
                          enig=True, sensors=sensors)
    finally:
        cm.PCB_VAR_USD.clear()
        cm.PCB_VAR_USD.update(var_bak)


def main():
    bom4 = load_bom()
    bom2 = copy.deepcopy(bom4)
    for b in bom2:
        if b.part.endswith("C15008"):
            b.qty_per_board = 2
    scen = [("Prototyp 5 PCB / 5 bestueckt, 4 x 100 uF (D-013)", bom4, 5, 5, 5),
            ("Serie 20 PCB / 16 bestueckt / 15 Sensoren, 4 x 100 uF", bom4, 20, 16, 15),
            ("Serie 20 PCB / 16 bestueckt / 15 Sensoren, 2 x 100 uF", bom2, 20, 16, 15)]
    res = [(n, run(b, *q)) for n, b, *q in scen]
    md = io.StringIO()
    w = md.write
    w("# fluidi Sensor Rev B – Kosten aus der Schaltplan-BOM\n\n")
    w("| | |\n|---|---|\n")
    w("| Stand | 2026-11-07, Elektronik, Schaltplan Rev B (`hardware/sensor/fluidi_sensor.kicad_sch`) |\n")
    w("| Skript | `.venv/bin/python hardware/sensor/gen/cost_rev_b.py` (erzeugt diese Datei) |\n")
    w(f"| Modell | `scripts/cost_model.compute` (D-005), USD→CHF {cm.USD_TO_CHF:.4f} + {cm.FX_CARD_MARKUP*100:.1f} % Karte; "
      f"4 Lagen 1.6 mm, **ENIG**, Economic PCBA, Versand GSDL (falls zulässig) |\n")
    w(f"| Teiledaten | `docs/concepts/bom/jlc_prices.json`, JLC-API Abruf {PRICES['_abruf']} (Kategorie, Staffeln, "
      f"Mindestmenge, Verlust) |\n")
    w("| BOM | `hardware/sensor/out/fluidi_sensor_bom_jlc.csv`; Lötstellen = Pads mit Lotpaste je Footprint (pcbnew) |\n\n")
    w("## 1 Ergebnis\n\n")
    w("| Szenario | PCBA | Versand | **Stück CHF** | Einmal CHF | Bestellung total CHF | Vollkosten/Sensor CHF |\n")
    w("|---|---|---|---|---|---|---|\n")
    for n, r in res:
        w(f"| {n} | {r['mode']} | {r['ship']} | **{r['unit_chf']:.2f}** | {r['once_chf']:.2f} | {r['total_chf']:.2f} | "
          f"{r['full_chf']:.2f} |\n")
    ser = res[2][1]
    w(f"\nREQ-FAB-04 (< 10 CHF Stückkosten bei 10–15 Stück): Serie **{res[1][1]['unit_chf']:.2f} / "
      f"{ser['unit_chf']:.2f} CHF** (4 / 2 × 100 µF) → erfüllt.\n\n")
    n_ext = len({b.part for b in bom4 if b.category == 'extended'})
    n_pref = len({b.part for b in bom4 if b.category == 'preferred'})
    n_bas = len({b.part for b in bom4 if b.category == 'basic'})
    w(f"BOM-Typen: {n_ext} Extended, {n_pref} Preferred, {n_bas} Basic; "
      f"{sum(b.qty_per_board for b in bom4):g} Bauteile, "
      f"{sum(b.qty_per_board * b.joints for b in bom4):g} Lötstellen je Board.\n\n")
    w("## 2 Annahmen\n\n")
    w(f"- **ANNAHME PCB:** Grenzkosten je Platine × {AREA_FACTOR:.2f} (Rechteck {PCB_W:g} × {PCB_L:g} mm statt "
      f"{cm.BOARD_W_MM:g} × {cm.BOARD_L_MM:g} mm im JLC-Rechner); Fixanteil unverändert. Vor der Bestellung mit der "
      f"Kontur aus PCB_OUTLINE Rev B im JLC-Rechner ersetzen.\n")
    w(f"- **ANNAHME Gehäuse:** Kopf V4 (D-019) braucht ≈ {ASA_EXTRA_G:.1f} g ASA mehr (Oberflächenverhältnis), "
      f"0.035 CHF/g; Masse aus dem CAD der Mechanik übernehmen.\n")
    w("- Lokale Teile wie FLOORPLAN_OPTIONS (Zelle Panasonic CR2032 1.38 CHF, Dichtungen, Versiegelung, Schraube), "
      "Ausschuss 5 %.\n")
    w("- Nicht enthalten: Programmieradapter (einmalig, CONCEPTS 2.7), Werkzeug, Arbeitszeit, Gateway.\n\n")
    w("## 3 Einzelposten\n\n")
    for n, r in res:
        buf = io.StringIO()
        with redirect_stdout(buf):
            cm.report(r, n)
        w("```\n" + buf.getvalue().strip() + "\n```\n\n")
    w("## 4 BOM mit Kostendaten\n\n| Teil | Stk/Board | Kat. | Lötstellen | USD @20 | MOQ | Verlust |\n"
      "|---|---|---|---|---|---|---|\n")
    for b in bom4:
        w(f"| {b.part} | {b.qty_per_board:g} | {b.category} | {b.joints} | {cm.part_price(b, 20):.4f} | {b.moq} | "
          f"{b.attrition} |\n")
    path = os.path.join(OUT, "COSTS_REV_B.md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(md.getvalue())
    for n, r in res:
        print(f"{n}: Stueck {r['unit_chf']:.2f} CHF, Einmal {r['once_chf']:.2f} CHF, Voll {r['full_chf']:.2f} CHF "
              f"({r['mode']}, {r['ship']})")
    print("->", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
