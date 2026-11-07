"""3D-Kontrolle Sonde mit den S-Zuleitungen aus Layout Rev B (Befund L-3), Elmer StatElecSolveVec.

Unterschied zu probe3d.py: VOLLMODELL (keine Symmetrieebene in der Dicke), weil die Zuleitungen in Rev B auf L2 und L3
an verschiedenen x liegen (L2 x -8.0, L3 x -7.0, je 0.3 breit, Kanal 0.3 im Guard). Elektroden, Guard, Steg, Kontur,
Lagenaufbau, Netzfelder und Faelle wie probe3d.py Geometrie "sg" (REPORT Kap. 6/8), damit alt und neu im selben
Netzverfahren verglichen werden. Die Zuleitungsgeometrie wird aus der Platine gelesen (leads_revb.read_leads), nicht
aus dem Bericht.

Varianten:
  alt   Zuleitung x -4.875 auf L2 UND L3 (so war sie im Halbmodell probe3d.py "sg" durch die Spiegelung enthalten)
  revb  Zuleitungen wie in hardware/sensor/fluidi_sensor.kicad_pcb (pcbnew)

Aufruf:  .venv/bin/python simulation/field/probe3d_revb.py --var alt|revb --h 1.4|1.0 [--jobs 8]
Ausgabe: results/probe3d_revb_<var>_h<h>.json; Netze/Faelle in simulation/field/elmer3d/revb_<var>_h<h>/ (nicht
versioniert). Elmer nur ueber scripts/elmer.sh (probe3d.run_case).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import dataclasses as dc
import json
import math
import os
import subprocess
import sys

import gmsh

sys.path.insert(0, os.path.dirname(__file__))
import params as P  # noqa: E402
import probe3d as P3  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def leads_for(var):
    """Liste (Lage, x_mitte, Breite, Abstand zum Guard) der S-Zuleitungen."""
    if var == "alt":
        g = P3.GEOS["sg"]
        xs = (-(P.W_PROBE / 2 - g.edge) - g.gap / 2) / 2
        return [("L2", xs, g.wf, g.cf), ("L3", xs, g.wf, g.cf)]
    import leads_revb as LR
    return [(d["layer"], d["x"], d["w"], d["clr"]) for d in LR.read_leads()]


def build_full(g: P3.Geo3D, leads, wd: str):
    tpp, tcore, er = P.STACK_4L[g.stack]
    hb2 = tpp + tcore / 2 + P.T_CU_IN
    yL2 = hb2 - tpp
    W2 = P.W_PROBE / 2
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("probe_full")
    occ = gmsh.model.occ
    sl = [occ.addCylinder(0, 0, z0, 0, 0, z1 - z0, g.R) for z0, z1 in P3.slabs(g)]
    zc = g.L - (W2 - g.x_tip)
    pts = [(-W2, g.z_top), (W2, g.z_top), (W2, zc), (g.x_tip, g.L), (-g.x_tip, g.L), (-W2, zc)]

    def prism(y0, y1):
        pt = [occ.addPoint(x, y0, z) for x, z in pts]
        ln = [occ.addLine(pt[i], pt[(i + 1) % len(pt)]) for i in range(len(pt))]
        s = occ.addPlaneSurface([occ.addCurveLoop(ln)])
        ex = occ.extrude([(2, s)], 0, y1 - y0, 0)
        return [t for d, t in ex if d == 3][0]

    board = prism(-hb2, hb2)
    mask_t = prism(hb2, hb2 + g.t_mask)
    mask_b = prism(-hb2 - g.t_mask, -hb2)
    xe = W2 - g.edge

    def rect(x0, x1, z0, z1):
        return occ.addRectangle(x0, z0, 0, x1 - x0, z1 - z0)

    s_all, g_all = [], []
    for lay, ysign in (("L2", 1.0), ("L3", -1.0)):
        ll = [ld for ld in leads if ld[0] == lay]
        s_parts = [rect(-xe, -g.gap / 2, g.z_s0, g.z_s1)]
        s_parts += [rect(x - w / 2, x + w / 2, g.z_top, g.z_s0 + 0.5) for _, x, w, c in ll]
        # Guard mit Kanaelen um die Zuleitungen dieser Lage
        cuts = sorted((x - w / 2 - c, x + w / 2 + c) for _, x, w, c in ll)
        g_parts, xa = [], -xe
        for a, b in cuts:
            g_parts.append(rect(xa, a, g.z_top, g.z_guard))
            xa = b
        g_parts.append(rect(xa, xe, g.z_top, g.z_guard))
        g_parts.append(rect(g.gap / 2, xe, g.z_top, g.z_g1))
        if g.g_bar:
            g_parts.append(rect(-xe, xe, g.z_s1 + g.gap, g.z_s1 + g.gap + g.w_bar))
        s_f, _ = occ.fuse([(2, s_parts[0])], [(2, t) for t in s_parts[1:]])
        g_f, _ = occ.fuse([(2, g_parts[0])], [(2, t) for t in g_parts[1:]])
        el = s_f + g_f
        occ.rotate(el, 0, 0, 0, 1, 0, 0, math.pi / 2)
        occ.translate(el, 0, ysign * yL2, 0)
        s_all += s_f
        g_all += g_f
    nsl = len(sl)
    tools = [(3, board), (3, mask_t), (3, mask_b)] + s_all + g_all
    out, omap = occ.fragment([(3, t) for t in sl], tools)
    occ.synchronize()
    vol_reg = {}
    for i, pieces in enumerate(omap[:nsl]):
        for d, t in pieces:
            if d == 3:
                vol_reg.setdefault(t, ("slab", i))
    for d, t in omap[nsl]:
        if d == 3:
            vol_reg[t] = ("fr4", 0)
    for k in (1, 2):
        for d, t in omap[nsl + k]:
            if d == 3:
                vol_reg[t] = ("mask", 0)
    surf_net = {}
    off = nsl + 3
    for k in range(len(s_all)):
        for d, t in omap[off + k]:
            if d == 2:
                surf_net[t] = "S"
    for k in range(len(g_all)):
        for d, t in omap[off + len(s_all) + k]:
            if d == 2:
                surf_net[t] = "G"
    gmsh.model.addPhysicalGroup(3, [t for t, r in vol_reg.items() if r[0] == "fr4"], tag=1)
    gmsh.model.addPhysicalGroup(3, [t for t, r in vol_reg.items() if r[0] == "mask"], tag=2)
    for i in range(nsl):
        gmsh.model.addPhysicalGroup(3, [t for t, r in vol_reg.items() if r == ("slab", i)], tag=3 + i)
    gmsh.model.addPhysicalGroup(2, [t for t, n in surf_net.items() if n == "S"], tag=1)
    gmsh.model.addPhysicalGroup(2, [t for t, n in surf_net.items() if n == "G"], tag=2)
    # Netzfelder identisch zu probe3d.build
    h = g.h
    ecurves = list({abs(c[1]) for s in surf_net for c in gmsh.model.getBoundary([(2, s)], oriented=False)})
    esurf = list(surf_net)
    bsurf = list({abs(b[1]) for t, r in vol_reg.items() if r[0] in ("fr4", "mask")
                  for b in gmsh.model.getBoundary([(3, t)], oriented=False)})
    F = gmsh.model.mesh.field
    f1 = F.add("Distance"); F.setNumbers(f1, "CurvesList", ecurves); F.setNumber(f1, "Sampling", 2000)
    f2 = F.add("Threshold"); F.setNumber(f2, "InField", f1)
    F.setNumber(f2, "SizeMin", 0.09 * h); F.setNumber(f2, "SizeMax", 6.0 * h)
    F.setNumber(f2, "DistMin", 0.05); F.setNumber(f2, "DistMax", 30.0)
    f3 = F.add("Distance"); F.setNumbers(f3, "SurfacesList", esurf); F.setNumber(f3, "Sampling", 200)
    f4 = F.add("Threshold"); F.setNumber(f4, "InField", f3)
    F.setNumber(f4, "SizeMin", 0.22 * h); F.setNumber(f4, "SizeMax", 6.0 * h)
    F.setNumber(f4, "DistMin", 0.3); F.setNumber(f4, "DistMax", 35.0)
    f5 = F.add("Distance"); F.setNumbers(f5, "SurfacesList", bsurf); F.setNumber(f5, "Sampling", 200)
    f6 = F.add("Threshold"); F.setNumber(f6, "InField", f5)
    F.setNumber(f6, "SizeMin", 0.35 * h); F.setNumber(f6, "SizeMax", 6.0 * h)
    F.setNumber(f6, "DistMin", 0.2); F.setNumber(f6, "DistMax", 35.0)
    f7 = F.add("Min"); F.setNumbers(f7, "FieldsList", [f2, f4, f6])
    F.setAsBackgroundMesh(f7)
    for k, v in (("Mesh.MeshSizeExtendFromBoundary", 0), ("Mesh.MeshSizeFromPoints", 0),
                 ("Mesh.MeshSizeFromCurvature", 0), ("Mesh.Algorithm", 6), ("Mesh.Algorithm3D", 10),
                 ("General.NumThreads", 16)):
        gmsh.option.setNumber(k, v)
    gmsh.model.mesh.generate(3)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    os.makedirs(wd, exist_ok=True)
    gmsh.write(os.path.join(wd, "probe.msh"))
    ntet = sum(len(x) for x in gmsh.model.mesh.getElements(3)[1])
    nnode = len(gmsh.model.mesh.getNodes()[0])
    gmsh.finalize()
    subprocess.run(["ElmerGrid", "14", "2", "probe.msh", "-autoclean"], cwd=wd, check=True, stdout=subprocess.DEVNULL)
    bodies = set()
    with open(os.path.join(wd, "probe", "mesh.elements")) as fh:
        for line in fh:
            bodies.add(int(line.split()[1]))
    assert bodies == set(range(1, len(P3.slabs(g)) + 3)), f"Koerpernummern unerwartet: {sorted(bodies)}"
    return {"ntet": ntet, "nnode": nnode, "nslab": len(P3.slabs(g))}


def cases(g):
    sl = P3.slabs(g)
    soil_from = lambda zf: [z0 >= zf - 1e-9 for z0, z1 in sl]
    _, _, er = P.STACK_4L[g.stack]
    C = {"air": (soil_from(1e9), 1.0, er)}
    for key, eps in (("dry", P.EPS_DRY), ("e10", 10.0), ("wet", P.EPS_WET), ("water", P.EPS_WATER)):
        C[key] = (soil_from(5.0), eps, er)
    C["air_fr4wet"] = (soil_from(1e9), 1.0, er * (1 + P.DK_FR4_MOIST_REL))
    C["water_fr4wet"] = (soil_from(5.0), P.EPS_WATER, er * (1 + P.DK_FR4_MOIST_REL))
    C["wet_flood"] = (soil_from(0.0), P.EPS_WET, er)          # Topf ueberflutet bis z_f 0 (wie REPORT Kap. 6)
    C["water_flood"] = (soil_from(0.0), P.EPS_WATER, er)
    C["dry_flood"] = (soil_from(0.0), P.EPS_DRY, er)
    # REQ-MES-08: nass ab Tiefe 10 bzw. 90 mm (Anteil 10-90 mm = (C10 - C90)/(C_wet - C_air))
    C["fill010.0"] = (soil_from(10.0), P.EPS_WET, er)
    C["fill090.0"] = (soil_from(90.0), P.EPS_WET, er)
    return C


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--var", default="revb", choices=["alt", "revb"])
    ap.add_argument("--h", type=float, default=1.4)
    ap.add_argument("--jobs", type=int, default=6)
    ap.add_argument("--reuse", action="store_true", help="vorhandenes Netz nutzen, nur fehlende Faelle rechnen")
    a = ap.parse_args()
    g = dc.replace(P3.GEOS["sg"], h=a.h)
    leads = leads_for(a.var)
    tag = f"revb_{a.var}_h{a.h:g}"
    wd = os.path.join(HERE, "elmer3d", tag)
    out = os.path.join(HERE, "results", f"probe3d_{tag}.json")
    res = {}
    if a.reuse and os.path.exists(out) and os.path.exists(os.path.join(wd, "probe", "mesh.elements")):
        old = json.load(open(out))
        info, res = old["mesh"], old["C_pF"]
    else:
        info = build_full(g, leads, wd)
    print(tag, leads, info, flush=True)
    C = {k: v for k, v in cases(g).items() if k not in res}
    n = len(P3.slabs(g))
    for case, (soil, eps, er) in C.items():
        P3.write_case(wd, case, n, soil, eps, er)
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for case, c in ex.map(lambda c: P3.run_case(wd, c, 1), list(C)):
            res[case] = c
            print(f"  {case:14s} C = {c:8.3f} pF", flush=True)
    json.dump({"var": a.var, "leads": leads, "geo": dc.asdict(g), "mesh": info, "C_pF": res}, open(out, "w"), indent=1)
    print("->", out)


if __name__ == "__main__":
    main()
