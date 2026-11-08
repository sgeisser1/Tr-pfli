#!/usr/bin/env python3
"""fluidi Sensor - Bestellwerte fuer hardware/sensor/out/ORDER_JLC_REV_C.md pruefen (nur lesen, nichts bestellen).

Prueft an der Platine (pcbnew) und an den Fertigungsdaten:
  - Lagen, Dicke, Kontur, Oberflaeche, Lagenaufbau (Platine + Gerber-Job-Datei)
  - Vias: Anzahl, Groesse, Attribut gefuellt/ueberkupfert, Via-in-Pad (jede Via in einem Kupferpad muss gefuellt sein)
  - Bauteile nur auf der Oberseite (Economic PCBA), Platzhalter "JLCJLCJLCJLC" (Lage, Ebene)
  - Gerber-ZIP = Gerber-Ordner (Inhalt), BOM-Designatoren = CPL-Designatoren
  - sha256 von Gerber-ZIP, BOM, CPL
  - optional --live: JLC-Lager/Kategorie aller BOM-Teile (scripts/jlc_price_cache.query, schreibt keinen Cache)
Aufruf: .venv/bin/python hardware/sensor/gen/order_check.py [--live]
"""
import csv
import datetime
import hashlib
import json
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "hardware", "sensor", "out")
PCB = os.path.join(ROOT, "hardware", "sensor", "fluidi_sensor.kicad_pcb")
FILES = ["fluidi_sensor_gerber_jlc.zip", "fluidi_sensor_bom_jlc.csv", "fluidi_sensor_cpl_jlc.csv"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def board_facts():
    import pcbnew
    b = pcbnew.LoadBoard(PCB)
    ds = b.GetDesignSettings()
    bb = b.GetBoardEdgesBoundingBox()
    ao = ds.GetAuxOrigin()
    mm = pcbnew.ToMM
    print(f"Platine: {b.GetCopperLayerCount()} Kupferlagen, Dicke {mm(ds.GetBoardThickness()):.2f} mm, "
          f"Kontur inkl. Linienbreite {mm(bb.GetWidth()):.2f} x {mm(bb.GetHeight()):.2f} mm, "
          f"Hilfsursprung ({mm(ao.x):.2f}, {mm(ao.y):.2f})")
    txt = open(PCB, encoding="utf-8").read()
    fin = txt.split("(copper_finish", 1)[1].split(")", 1)[0].strip().strip('"') if "(copper_finish" in txt else "-"
    print(f"Oberflaeche (Platine): {fin}")
    vias = [t for t in b.GetTracks() if isinstance(t, pcbnew.PCB_VIA)]
    sizes = sorted({(round(mm(v.GetWidth(pcbnew.F_Cu)), 3), round(mm(v.GetDrillValue()), 3)) for v in vias})
    filled = [v for v in vias if v.GetPrimaryDrillFilledFlag() and v.GetPrimaryDrillCappedFlag()]
    print(f"Vias: {len(vias)}, Groessen (Ø/Bohrung mm) {sizes}, gefuellt+ueberkupfert {len(filled)}")
    vip_bad = 0
    for v in vias:
        p = v.GetPosition()
        pads = [f"{fp.GetReference()}.{pd.GetNumber() or 'EP-Paste'}" for fp in b.GetFootprints() for pd in fp.Pads()
                if pd.IsOnLayer(pcbnew.F_Cu) and pd.HitTest(p) and pd.GetNumber()]
        if pads:
            ok = v in filled
            vip_bad += 0 if ok else 1
            print(f"  Via-in-Pad ({mm(p.x - ao.x):7.2f}, {mm(p.y - ao.y):7.2f}) {v.GetNetname():<16s} "
                  f"{','.join(sorted(set(pads))):<10s} {'gefuellt+ueberkupfert' if ok else 'NICHT GEFUELLT'}")
    print(f"Via-in-Pad ohne Fuellattribut: {vip_bad}")
    bottom = [fp.GetReference() for fp in b.GetFootprints() if fp.GetLayer() != pcbnew.F_Cu]
    print(f"Footprints auf der Unterseite: {bottom or '-'} (nur bestueckte Teile zaehlen; Testpads sind keine Bauteile)")
    for d in b.GetDrawings():
        if isinstance(d, pcbnew.PCB_TEXT) and "JLCJLC" in d.GetText():
            p = d.GetPosition()
            print(f"Platzhalter {d.GetText()!r} auf {b.GetLayerName(d.GetLayer())} bei "
                  f"({mm(p.x - ao.x):.2f}, {mm(p.y - ao.y):.2f}) mm ab Hilfsursprung")


def job_facts():
    job = json.load(open(os.path.join(OUT, "gerber", "fluidi_sensor-job.gbrjob")))
    g = job["GeneralSpecs"]
    print(f"Gerber-Job: Revision {g['ProjectId']['Revision']}, Lagen {g['LayerNumber']}, Dicke {g['BoardThickness']}, "
          f"Finish {g['Finish']}, Groesse {g['Size']['X']} x {g['Size']['Y']}, erzeugt {job['Header']['CreationDate']}")
    diel = [(m["Name"], m.get("Thickness"), m.get("Material")) for m in job["MaterialStackup"] if m["Type"] == "Dielectric"]
    print(f"Gerber-Job Dielektrika: {diel}")


def files_facts():
    z = zipfile.ZipFile(os.path.join(OUT, FILES[0]))
    same = all(z.read(n) == open(os.path.join(OUT, "gerber", n), "rb").read() for n in z.namelist())
    print(f"Gerber-ZIP: {len(z.namelist())} Dateien, identisch mit out/gerber/: {same}")
    bom = set()
    for r in csv.DictReader(open(os.path.join(OUT, FILES[1]))):
        bom |= set(r["Designator"].split(","))
    cpl = list(csv.DictReader(open(os.path.join(OUT, FILES[2]))))
    print(f"BOM {len(bom)} Designatoren, CPL {len(cpl)} Zeilen, Differenz {sorted(bom ^ {r['Designator'] for r in cpl})}, "
          f"Lagen in CPL {sorted({r['Layer'] for r in cpl})}")
    for f in FILES:
        print(f"sha256 {sha256(os.path.join(OUT, f))}  hardware/sensor/out/{f}")


def live():
    sys.path.insert(0, os.path.join(ROOT, "scripts"))
    from jlc_price_cache import query
    print(f"JLC-Teilesuche live, {datetime.datetime.now().astimezone().isoformat(timespec='minutes')}:")
    for r in csv.DictReader(open(os.path.join(OUT, FILES[1]))):
        d = query(r["LCSC Part #"])
        if d is None:
            print(f"  {r['LCSC Part #']:<10s} NICHT GEFUNDEN ({r['Designator']})")
            continue
        cat = "basic" if d["library"] == "base" else ("preferred" if d["preferred"] else "extended")
        print(f"  {r['LCSC Part #']:<10s} {cat:<9s} Lager {d['stock']:>9d}  {d['package']:<14s} {d['model']:<28s} "
              f"{r['Designator']}")


if __name__ == "__main__":
    board_facts()
    job_facts()
    files_facts()
    if "--live" in sys.argv:
        live()
