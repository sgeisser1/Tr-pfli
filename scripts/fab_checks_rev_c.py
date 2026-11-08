#!/usr/bin/env python3
"""fluidi Sensor Rev C - Fertigungspruefungen fuer die Design-Review-Checkliste Phase 5 (nur lesen, nichts aendern).

Prueft:
  1  sha256 von Gerber-ZIP, BOM, CPL gegen hardware/sensor/out/ORDER_JLC_REV_C.md Kap. 1
  2  DRC mit den Projektregeln (JLC-Werte in hardware/sensor/fluidi_sensor.kicad_dru) auf einer KOPIE der Platine im
     Scratch-Ordner (kicad-cli pcb drc --schematic-parity --refill-zones --severity-all); Original bleibt unberuehrt
  3  BOM (LCSC) <-> Register docs/datasheets/INDEX.csv: jede LCSC-Nummer vorhanden, Basic/Extended gleich wie
     jlc_prices.json, lokales Datenblatt vorhanden; Footprint BOM = Footprint Platine
  4  ENIG-Flaeche (Pads mit Loetstoppoeffnung, F+B) in % der Platinenflaeche x 2 (JLC-Aufpreis ab 30 %)
  5  Silkscreen-Texte: kleinste Hoehe/Strichbreite (JLC min. 1.0 / 0.15 mm), Texte auf B.Silkscreen
  6  Bauteile nur auf F (Economic PCBA), kleinste Bauform 0402 (Economic min. 0402)
Aufruf: .venv/bin/python scripts/fab_checks_rev_c.py [--no-drc] [--scratch DIR]
"""
import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
HW = os.path.join(ROOT, "hardware", "sensor")
OUT = os.path.join(HW, "out")
ORDER = os.path.join(OUT, "ORDER_JLC_REV_C.md")
FILES = ["fluidi_sensor_gerber_jlc.zip", "fluidi_sensor_bom_jlc.csv", "fluidi_sensor_cpl_jlc.csv"]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def check_sha():
    txt = open(ORDER, encoding="utf-8").read()
    ok = True
    for f in FILES:
        h = sha(os.path.join(OUT, f))
        m = re.search(re.escape(f) + r".*?`([0-9a-f]{64})`", txt)
        exp = m.group(1) if m else None
        ok &= (h == exp)
        print(f"1 sha256 {f}: {h[:16]}… {'= ORDER' if h == exp else '!= ORDER ' + str(exp)}")
    return ok


def run_drc(scratch):
    d = os.path.join(scratch, "drc_copy")
    if os.path.isdir(d):
        shutil.rmtree(d)
    os.makedirs(d)
    for f in os.listdir(HW):
        p = os.path.join(HW, f)
        if os.path.isfile(p) and f.startswith("fluidi_sensor.") or f in ("fp-lib-table", "sym-lib-table"):
            shutil.copy2(p, d)
    shutil.copytree(os.path.join(HW, "lib"), os.path.join(d, "lib"))
    pcb = os.path.join(d, "fluidi_sensor.kicad_pcb")
    rpt = os.path.join(d, "drc.json")
    ver = subprocess.run(["kicad-cli", "--version"], capture_output=True, text=True).stdout.strip()
    subprocess.run(["kicad-cli", "pcb", "drc", "--schematic-parity", "--refill-zones", "--severity-all",
                    "--format", "json", "-o", rpt, pcb], capture_output=True, text=True)
    j = json.load(open(rpt, encoding="utf-8"))
    nv = len(j.get("violations", []))
    nu = len(j.get("unconnected_items", []))
    np_ = len(j.get("schematic_parity", []))
    rules = open(os.path.join(HW, "fluidi_sensor.kicad_dru"), encoding="utf-8").read()
    nrules = len(re.findall(r"^\(rule ", rules, re.M))
    print(f"2 DRC kicad-cli {ver} auf Kopie ({d}): Verstoesse {nv}, offene Verbindungen {nu}, "
          f"Schaltplan-Paritaet {np_}; Projektregeln {nrules} (fluidi_sensor.kicad_dru)")
    for v in j.get("violations", [])[:10]:
        print("   ", v.get("severity"), v.get("type"), v.get("description"))
    return nv == 0 and nu == 0 and np_ == 0


def check_register():
    prices = json.load(open(os.path.join(ROOT, "docs", "concepts", "bom", "jlc_prices.json"), encoding="utf-8"))
    reg = list(csv.reader(open(os.path.join(ROOT, "docs", "datasheets", "INDEX.csv"), encoding="utf-8"), delimiter=";"))
    hdr, rows = reg[0], reg[1:]
    i_l, i_be, i_path = hdr.index("LCSC"), hdr.index("Basic/Extended"), hdr.index("Lokaler Pfad")
    raw = {r["Ref"]: r["Footprint"] for r in csv.DictReader(open(os.path.join(OUT, "fluidi_sensor_bom_raw.csv")))}
    import pcbnew
    b = pcbnew.LoadBoard(os.path.join(HW, "fluidi_sensor.kicad_pcb"))
    fp_board = {f.GetReference(): f"{f.GetFPID().GetLibNickname()}:{f.GetFPID().GetLibItemName()}" for f in b.GetFootprints()}
    ok = True
    for r in csv.DictReader(open(os.path.join(OUT, "fluidi_sensor_bom_jlc.csv"))):
        lcsc = r["LCSC Part #"]
        d = prices[lcsc]
        cat = "Basic" if d["library"] == "base" else ("Preferred" if d["preferred"] else "Extended")
        hits = [x for x in rows if len(x) > i_l and x[i_l].strip() == lcsc]
        regcat = {x[i_be].strip() for x in hits}
        paths = {x[i_path].strip() for x in hits}
        path_ok = all(p and os.path.isfile(os.path.join(ROOT, p)) for p in paths) if paths else False
        cat_ok = any(cat.lower() in c.lower() or (cat == "Preferred" and "extended" in c.lower()) for c in regcat)
        refs = r["Designator"].split(",")
        fps = {fp_board.get(x) for x in refs}
        fp_ok = fps == {r["Footprint"]} or {raw.get(x) for x in refs} == fps
        flag = "ok" if hits and cat_ok and path_ok and fp_ok else "PRUEFEN"
        ok &= flag == "ok"
        print(f"3 {lcsc:<10} {cat:<9} Register {sorted(regcat) or '-'} Datenblatt {'ja' if path_ok else 'NEIN'} "
              f"Footprint BOM/Platine {'gleich' if fp_ok else str(fps)} {flag}  ({r['Designator']})")
    return ok


def board_checks():
    import pcbnew
    b = pcbnew.LoadBoard(os.path.join(HW, "fluidi_sensor.kicad_pcb"))
    mm = pcbnew.ToMM
    bb = b.GetBoardEdgesBoundingBox()
    # Platinenflaeche aus der Kontur (Polygon)
    poly = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(poly, True)
    area = mm(mm(poly.Area())) if hasattr(poly, "Area") else mm(bb.GetWidth()) * mm(bb.GetHeight())
    enig = {"F": 0.0, "B": 0.0}
    for fp in b.GetFootprints():
        for p in fp.Pads():
            for side, cu, mask in (("F", pcbnew.F_Cu, pcbnew.F_Mask), ("B", pcbnew.B_Cu, pcbnew.B_Mask)):
                if p.IsOnLayer(cu) and p.IsOnLayer(mask):
                    sp = pcbnew.SHAPE_POLY_SET()
                    p.TransformShapeToPolygon(sp, cu, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
                    enig[side] += mm(mm(sp.Area()))
    pct = (enig["F"] + enig["B"]) / area * 100.0
    print(f"4 ENIG-Flaeche: F {enig['F']:.1f} mm2 + B {enig['B']:.1f} mm2 = {pct:.2f} % von 2 x {area:.0f} mm2 "
          f"(JLC-Aufpreis erst ueber 30 %, Vias hier nicht gezaehlt: gefuellt/abgedeckt)")
    texts = []
    for d in b.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and d.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            texts.append((d.GetLayerName(), d.GetText(), mm(d.GetTextHeight()), mm(d.GetTextThickness())))
    for fp in b.GetFootprints():
        for t in [fp.Reference(), fp.Value()] + [x for x in fp.GraphicalItems() if isinstance(x, pcbnew.PCB_TEXT)]:
            if t.IsVisible() and t.GetLayer() in (pcbnew.F_SilkS, pcbnew.B_SilkS):
                texts.append((t.GetLayerName(), t.GetText(), mm(t.GetTextHeight()), mm(t.GetTextThickness())))
    if texts:
        hmin = min(t[2] for t in texts)
        wmin = min(t[3] for t in texts)
        print(f"5 Silkscreen-Texte {len(texts)}: kleinste Hoehe {hmin:.2f} mm, kleinste Strichbreite {wmin:.2f} mm "
              f"(JLC 1.0 / 0.15) -> {'ok' if hmin >= 1.0 - 1e-6 and wmin >= 0.15 - 1e-6 else 'PRUEFEN'}")
        for t in texts:
            if t[0] == "B.Silkscreen":
                print(f"   B.Silkscreen: {t[1]!r} h {t[2]:.2f} w {t[3]:.2f}")
    back = [fp.GetReference() for fp in b.GetFootprints()
            if fp.GetLayer() == pcbnew.B_Cu and not (fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES)]
    small = sorted({str(fp.GetFPID().GetLibItemName()) for fp in b.GetFootprints()
                    if re.search(r"0201|01005", str(fp.GetFPID().GetLibItemName()))})
    print(f"6 Bestueckte Teile auf B: {back or 'keine'}; Bauformen kleiner 0402: {small or 'keine'}")
    # 7 Abstand zur Kontur (Economic: Nutzentrennung +-0.2 mm, Bauteile > 0.3 mm von der Kante empfohlen, FAQ Q14)
    poly = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(poly, True)
    edge = poly.Outline(0)

    def dist(sps):
        if sps.OutlineCount() == 0:
            return None
        o = sps.Outline(0)
        return mm(int(min(edge.SquaredDistance(o.CPoint(i), True) for i in range(o.PointCount())) ** 0.5))

    pads, crt = [], []
    for fp in b.GetFootprints():
        if fp.GetAttributes() & pcbnew.FP_EXCLUDE_FROM_POS_FILES:
            continue
        for p in fp.Pads():
            sp = pcbnew.SHAPE_POLY_SET()
            p.TransformShapeToPolygon(sp, pcbnew.F_Cu, 0, pcbnew.FromMM(0.005), pcbnew.ERROR_INSIDE)
            d = dist(sp)
            if d is not None:
                pads.append((d, f"{fp.GetReference()}.{p.GetNumber()}"))
        d = dist(fp.GetCourtyard(pcbnew.F_CrtYd))
        if d is not None:
            bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
            outside = not b.GetBoardEdgesBoundingBox().Contains(bb)
            crt.append((0.0 if outside else d, fp.GetReference()))
    pads.sort()
    crt.sort()
    print(f"7 Kante: kleinster Pad-Abstand {pads[0][0]:.2f} mm ({pads[0][1]}), Courtyard < 0.3 mm oder ueber die Kante: "
          f"{[(r, round(d, 2)) for d, r in crt if d < 0.3] or 'keine'} (BT1-Courtyard = Zellumriss, siehe Checkliste)")
    return not back and not small and pads[0][0] >= 0.3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-drc", action="store_true")
    ap.add_argument("--scratch", default=None)
    a = ap.parse_args()
    res = {"sha": check_sha()}
    if not a.no_drc:
        scratch = a.scratch or tempfile.mkdtemp(prefix="fluidi_fab_")
        res["drc"] = run_drc(scratch)
    res["register"] = check_register()
    res["board"] = board_checks()
    print("ERGEBNIS:", ", ".join(f"{k} {'ok' if v else 'PRUEFEN'}" for k, v in res.items()))
    return 0 if all(res.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
