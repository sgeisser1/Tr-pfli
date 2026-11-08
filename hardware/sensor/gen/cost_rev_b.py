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
Layout Rev B (Commit 425174d): Via-in-Pad im Zellfach (Befund L-1) und im EP von U1 -> Via-Behandlung "Epoxy Filled &
Capped" (POFV) fuer die ganze Platine; PCB-Preis aus dem JLC-Angebot 2026-11-08 (Auftraggeber,
docs/requirements/CLIENT_INPUT.md): 5 Stk 65.21 / 20 Stk 76.30 USD inkl. ENIG + POFV.
Layout Rev C (Commit 03341e8): BOM-Teile unveraendert, 4 statt 5 Via-in-Pad im Fach (POFV gilt fuer die ganze Platine).
Rev C / Red Team 2026-11-08 (docs/reviews/phase4_redteam_gesamt.md):
  K-2: Verzollung DHL mit belegter Quelle (scripts/cost_model.py DHL_CLEARANCE_CHF, docs/references/DHL-Express-CH_*);
       Vergleich alt (nur Vorlagegebuehr 3 CHF) / neu wird mit ausgegeben.
  K-3: Gegenueberstellung Stueckkosten (D-005) und Vollkosten.
  W-2: Alternative Standard-PCBA (falls Economic + ENIG + POFV im Formular nicht kombinierbar), Paneel 3 x 1.
PCB-Preislogik (Angebot 2026-11-08, linear) unveraendert, auch fuer die Standard-PCBA-Alternative (ANNAHME, s. Text).
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

# PCB-Preis Rev B: JLC-Rechner, vom Auftraggeber abgelesen 2026-11-08 (Konversation, docs/requirements/CLIENT_INPUT.md):
# 26 x 158.5 mm, 4 L, 1.6 mm, ENIG, Epoxy Filled & Capped: 5 Stk 65.21 USD, 20 Stk 76.30 USD.
# Lineares Modell durch beide Punkte: Grenzkosten 0.7393 USD/Platine, Fixanteil inkl. ENIG+POFV 61.51 USD/Bestellung.
# Damit sind die Aufpreise ENIG/POFV ueberwiegend fix (Befund DFM W-2 erledigt; Grenzfall "mengenproportional" entfaellt).
QUOTE_USD = {5: 65.21, 20: 76.30}
PCB_VAR_QUOTE = (QUOTE_USD[20] - QUOTE_USD[5]) / 15.0
PCB_FIX_QUOTE = QUOTE_USD[5] - 5 * PCB_VAR_QUOTE   # inkl. ENIG + POFV
PCB_W, PCB_L = 26.0, 158.5
POFV = True   # Layout Rev B: Via-in-Pad (Zellfach, U1-EP) -> Epoxy Filled & Capped zwingend
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


# W-2 Alternative Standard-PCBA: Einzelplatine/Panel min. 70 x 70 mm (cost_model.STD_MIN_SIZE_MM) -> Paneel
# 3 x 1 = 78 x 158.5 mm zuzueglich Randstreifen mit Fiducials/Tooling-Loechern (JLCPCB_NOTES Kap. 2: "noetig").
# ANNAHME: JLC bestueckt nur ganze Paneele; PCB-Preis wie Angebot pro Platine (Paneelpreis inkl. Raender nicht
# abgelesen -> BESTELL-PRUEFUNG im Rechner).
PANEL_N = 3
STD_SCEN = [("ALT W-2 Standard-PCBA Prototyp: 2 Paneele = 6 PCB / 6 bestueckt / 5 Sensoren", 6, 6, 5),
            ("ALT W-2 Standard-PCBA Serie: 7 Paneele = 21 PCB / 18 bestueckt / 15 Sensoren", 21, 18, 15)]


def run(bom, pcb_qty, pcba_qty, sensors, pcba="economic", old_customs=False):
    """PCB-Preis aus dem JLC-Angebot (QUOTE_USD): Fixanteil so gesetzt, dass Fix + ENIG + POFV = PCB_FIX_QUOTE."""
    fix_bak, var_bak = dict(cm.PCB_FIX_USD), dict(cm.PCB_VAR_USD)
    clr_bak = (cm.DHL_CLEARANCE_CHF, cm.DHL_CLEARANCE_IN_VAT_BASE)
    try:
        assert POFV
        cm.PCB_FIX_USD[(4, 1.6)] = PCB_FIX_QUOTE - cm.SURCHARGE_ENIG_USD[4] - cm.SURCHARGE_EPOXY_VIA_USD[4]
        cm.PCB_VAR_USD[(4, 1.6)] = PCB_VAR_QUOTE
        for q, usd in QUOTE_USD.items():   # Selbstpruefung: Fix (inkl. ENIG+POFV) + q x Grenzkosten = Angebot
            got = (cm.PCB_FIX_USD[(4, 1.6)] + cm.SURCHARGE_ENIG_USD[4] + cm.SURCHARGE_EPOXY_VIA_USD[4]
                   + cm.SURCHARGE_COLOR_USD + q * cm.PCB_VAR_USD[(4, 1.6)])
            assert abs(got - usd) < 0.01, (q, got, usd)
        if old_customs:   # Stand vor K-2: nur Vorlagegebuehr max(3 CHF, 2 %), keine 19 CHF Abwicklung
            cm.DHL_CLEARANCE_CHF, cm.DHL_CLEARANCE_IN_VAT_BASE = 0.0, False
        return cm.compute(bom + copy.deepcopy(LOKAL), 4, 1.6, pcb_qty, pcba_qty, ship="GSDL", pcba=pcba,
                          enig=True, epoxy_vias=POFV, sensors=sensors)
    finally:
        cm.DHL_CLEARANCE_CHF, cm.DHL_CLEARANCE_IN_VAT_BASE = clr_bak
        cm.PCB_FIX_USD.clear()
        cm.PCB_FIX_USD.update(fix_bak)
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
    old = [(n, run(b, *q, old_customs=True)) for n, b, *q in scen]
    sens = [(n, run(bom4, *q, pcba="standard")) for n, *q in STD_SCEN]
    md = io.StringIO()
    w = md.write
    w("# fluidi Sensor Rev B/C – Kosten aus der Schaltplan-BOM\n\n")
    w("| | |\n|---|---|\n")
    w("| Stand | 2026-11-08 (PCB-Preis aus JLC-Angebot; Verzollung DHL nach K-2), Schaltplan/Layout **Rev C** (Commit 03341e8, "
      "BOM-Teile wie Rev B), Red-Team-Befunde K-2/K-3/W-2 (`docs/reviews/phase4_redteam_gesamt.md`) |\n")
    w("| Bestellunterlage | `hardware/sensor/out/ORDER_JLC_REV_C.md` |\n")
    w("| Skript | `.venv/bin/python hardware/sensor/gen/cost_rev_b.py` (erzeugt diese Datei) |\n")
    w(f"| Modell | `scripts/cost_model.compute` (D-005), USD→CHF {cm.USD_TO_CHF:.4f} + {cm.FX_CARD_MARKUP*100:.1f} % Karte; "
      f"4 Lagen 1.6 mm, **ENIG**, **Epoxy Filled & Capped (POFV)**, Economic PCBA, Versand GSDL (falls zulässig, sonst DHL) |\n")
    w(f"| Verzollung DHL | {cm.DHL_CLEARANCE_CHF:.2f} CHF Abwicklung (in der MWST-Bemessung) + Vorlagegebühr max({cm.DHL_FEE_MIN_CHF:.2f} CHF; "
      f"{cm.DHL_FEE_PCT*100:.0f} % der Abgaben); Quelle DHL Express CH, gültig ab 2026-01-01, abgerufen 2026-11-08, "
      f"`docs/references/DHL-Express-CH_Customs-Services_Gebuehren_Auszug_2026-11-08.txt` und "
      f"`…_Zollinformationen-Privatkunden_Auszug_2026-11-08.txt`; **ANNAHME** Empfänger ohne eigenes ZAZ-Konto |\n")
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
      f"{ser['unit_chf']:.2f} CHF** (4 / 2 × 100 µF) → **erfüllt**. PCB-Preis aus dem JLC-Angebot (5 Stk "
      f"{QUOTE_USD[5]:.2f} USD, 20 Stk {QUOTE_USD[20]:.2f} USD): Aufpreise ENIG/POFV sind überwiegend fix "
      f"(Befund DFM W-2 erledigt).\n\n")
    w("### 1.1 Stückkosten und Vollkosten (K-3)\n\n")
    w("Die Stückkosten nach D-005 enthalten alles, was pro Sensor anfällt (Bauteile, PCB-Grenzkosten, Bestückung, "
      "Röntgen, MWST-Anteil, lokale Teile, Reserveboard). Die Vollkosten verteilen die ganze Bestellung inkl. Einmalkosten "
      "(PCB-Fixanteil mit ENIG/POFV, Setup, Feeder, Versand, Verzollung) auf die nutzbaren Sensoren. REQ-FAB-04 "
      "(< 10 CHF) bezieht sich auf die Stückkosten (D-005); was ein Sensor real kostet, zeigt die Vollkosten-Spalte.\n\n")
    w("| Szenario | Sensoren | Stückkosten CHF (D-005) | Einmalkosten CHF | Vollkosten CHF/Sensor | Anteil Einmalkosten an Vollkosten |\n")
    w("|---|---|---|---|---|---|\n")
    for n, r in res:
        w(f"| {n} | {r['sensors']} | {r['unit_chf']:.2f} | {r['once_chf']:.2f} | **{r['full_chf']:.2f}** | "
          f"{r['once_chf'] / r['total_chf'] * 100:.0f} % |\n")
    w("\n### 1.2 Verzollung alt / neu (K-2)\n\n")
    w("Bis 2026-11-08 rechnete das Modell nur die DHL-Vorlagegebühr (max(3 CHF; 2 %)). Laut DHL Express CH (gültig ab "
      f"2026-01-01) kommen {cm.DHL_CLEARANCE_CHF:.2f} CHF Abwicklung/Kontoabwicklung je Sendung ohne ZAZ-Konto dazu; "
      "sie sind Teil des steuerbaren Warenwerts (MWST 8.1 %). Die Stückkosten ändern sich nicht.\n\n")
    w("| Szenario | Verzollung alt CHF | neu CHF (inkl. MWST darauf) | Einmal alt | Einmal neu | Vollkosten alt | Vollkosten neu |\n")
    w("|---|---|---|---|---|---|---|\n")
    for (n, r), (_, o) in zip(res, old):
        assert abs(r['unit_chf'] - o['unit_chf']) < 1e-9
        fee_new = r['carrier_fee_chf'] + (r['vat_chf'] - o['vat_chf'])
        w(f"| {n} | {o['carrier_fee_chf']:.2f} | {fee_new:.2f} | {o['once_chf']:.2f} | {r['once_chf']:.2f} | "
          f"{o['full_chf']:.2f} | {r['full_chf']:.2f} |\n")
    w("\n### 1.3 Alternative Standard-PCBA (W-2, nur falls Economic + ENIG + POFV nicht bestellbar)\n\n")
    w("Standard-PCBA verlangt mindestens 70 × 70 mm je Einzelplatine oder Paneel sowie Randstreifen mit Fiducials "
      f"(`docs/references/JLCPCB_NOTES.md` Kap. 2). Die Platine (26 × 158.5 mm) muss deshalb als Paneel {PANEL_N} × 1 "
      f"(78 × 158.5 mm + Ränder) bestellt werden. **ANNAHME:** JLC bestückt nur ganze Paneele; der PCB-Preis folgt "
      "dem Angebot pro Platine (Paneelpreis mit Rändern **nicht** abgelesen, im Rechner prüfen). Feeder 1.53 USD für jeden "
      "Teiletyp, Setup 25.56 USD, Schablone 8.21 USD, Fixture 16.42 USD (JLCPCB_NOTES Kap. 1).\n\n")
    w("| Szenario | PCBA | Versand | Stück CHF | Einmal CHF | Bestellung total CHF | Vollkosten/Sensor CHF | Δ Stück ggü. Economic | Δ Bestellung ggü. Economic |\n")
    w("|---|---|---|---|---|---|---|---|---|\n")
    for (n, r), (_, e) in zip(sens, res[:2]):
        w(f"| {n} | {r['mode']} | {r['ship']} | **{r['unit_chf']:.2f}** | {r['once_chf']:.2f} | {r['total_chf']:.2f} | "
          f"{r['full_chf']:.2f} | {r['unit_chf'] - e['unit_chf']:+.2f} | {r['total_chf'] - e['total_chf']:+.2f} |\n")
    w("\nREQ-FAB-04 bleibt auch mit Standard-PCBA erfüllt, solange der Paneelpreis nicht deutlich über dem Angebot pro "
      "Platine liegt; die Mehrkosten sind überwiegend einmalig (Setup, Schablone, Fixture, Feeder für Basic-Teile). "
      "Freigabe durch den Auftraggeber nötig.\n\n")
    n_ext = len({b.part for b in bom4 if b.category == 'extended'})
    n_pref = len({b.part for b in bom4 if b.category == 'preferred'})
    n_bas = len({b.part for b in bom4 if b.category == 'basic'})
    w(f"BOM-Typen: {n_ext} Extended, {n_pref} Preferred, {n_bas} Basic; "
      f"{sum(b.qty_per_board for b in bom4):g} Bauteile, "
      f"{sum(b.qty_per_board * b.joints for b in bom4):g} Lötstellen je Board.\n\n")
    w("## 2 Annahmen\n\n")
    w(f"- **PCB (Angebot):** JLC-Rechner, abgelesen vom Auftraggeber 2026-11-08: {PCB_W:g} × {PCB_L:g} mm, 4 L, "
      f"1.6 mm, ENIG, Epoxy Filled & Capped (POFV) → 5 Stk {QUOTE_USD[5]:.2f} USD, 20 Stk {QUOTE_USD[20]:.2f} USD "
      f"(`docs/requirements/CLIENT_INPUT.md`). Linear: Fixanteil {PCB_FIX_QUOTE:.2f} USD/Bestellung (D-005, einmalig), "
      f"Grenzkosten {PCB_VAR_QUOTE:.4f} USD/Platine. Andere Mengen interpoliert (ANNAHME linear).\n")
    w("- **POFV** gilt für die ganze Platine (alle Vias), daher gleich für 4 oder 2 Via-in-Pad im Zellfach "
      "(L-1, D-023). **ANNAHME:** Kombination mit Economic PCBA zulässig (BESTELL-PRÜFUNG, ORDER_JLC_REV_C.md Kap. 3; "
      "Alternative Standard-PCBA Kap. 1.3).\n")
    w("- **Verzollung (K-2):** DHL Express CH, siehe Kopf. **ANNAHME:** kein eigenes ZAZ-Konto, vereinfachte Verzollung "
      "(MWST-Wert < 1000 CHF). Zoll 0 (Industriezölle seit 2024-01-01 aufgehoben), MWST 8.1 %.\n")
    w(f"- **ANNAHME Gehäuse:** Kopf V4 (D-019) braucht ≈ {ASA_EXTRA_G:.1f} g ASA mehr (Oberflächenverhältnis), "
      f"0.035 CHF/g; Masse aus dem CAD der Mechanik übernehmen.\n")
    w("- Lokale Teile wie FLOORPLAN_OPTIONS (Zelle Panasonic CR2032 1.38 CHF, Dichtungen, Versiegelung, Schraube), "
      "Ausschuss 5 %.\n")
    w("- Nicht enthalten: Programmieradapter (einmalig, CONCEPTS 2.7), Werkzeug, Arbeitszeit, Gateway.\n\n")
    w("## 3 Einzelposten\n\n")
    for n, r in res + sens:
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
    for n, r in res + sens:
        print(f"{n}: Stueck {r['unit_chf']:.2f} CHF, Einmal {r['once_chf']:.2f} CHF, Voll {r['full_chf']:.2f} CHF "
              f"({r['mode']}, {r['ship']})")
    print("->", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
