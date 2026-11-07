"""3D-Kontrolle der Sonde mit Elmer (StatElecSolveVec), Netz aus gmsh.

Viertelmodell (Symmetrieebenen x = 0 und y = 0, natuerliche RB) fuer die gespiegelte GSG-Geometrie auf
L2/L3. z = Tiefe unter der Dichtlinie (z = 0, Unterkante Kragen), positiv nach unten. Kopfbereich
z < 0 als Luft/Kunststoff mit eps 1 (ANNAHME), Guard (GND) auf L2/L3 vollflaechig bis z_guard.
Substrat in 5-mm-Scheiben -> Fuellstandskurve (Becherversuch REQ-MES-08) ohne Neuvernetzung.

Aufruf:  .venv/bin/python simulation/field/probe3d.py [--geo NAME] [--h FAKTOR] [--jobs N]
Ausgabe: results/probe3d_<geo>.csv, Netze/Faelle in simulation/field/elmer3d/<geo>/ (nicht versioniert)
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ELMER = os.path.join(ROOT, "scripts", "elmer.sh")


@dc.dataclass
class Geo3D:
    name: str = "gsg"
    ws: float = 6.0          # Breite S (voll)
    gap: float = 2.0         # Abstand S-G seitlich
    edge: float = P.EDGE_CLEAR + 0.25   # Kupfer-Kontur (Empfehlung 1.25 mm, >= 1.0 REQ-MECH-06)
    z_guard: float = 8.0     # Guard (GND, volle Breite) bis z_guard
    gap_z: float = 2.0       # Abstand Guard-Unterkante zu S-Oberkante
    z_s1: float = 88.0       # Ende S
    z_g1: float = 90.0       # Ende G-Randstreifen
    g_bar: bool = True       # G-Querbalken unter dem S-Ende (U-Form)
    w_bar: float = 2.0
    wf: float = 0.3          # S-Zuleitung im Guardbereich
    cf: float = 0.3          # Abstand Zuleitung-Guard
    L: float = 105.0         # Sondenlaenge unter der Dichtlinie (5 frei + 100 im Substrat)
    x_tip: float = 2.0       # halbe Breite der abgestumpften Spitze (ANNAHME, Mechanik)
    z_top: float = -15.0
    z_bot: float = 125.0
    R: float = 50.0
    stack: str = P.STACK_DEFAULT
    t_mask: float = P.T_MASK_LAM
    h: float = 1.0           # globaler Netzfaktor

    @property
    def z_s0(self):
        return self.z_guard + self.gap_z


GEOS = {
    "gsg": Geo3D(),
    "gsg_long": Geo3D(name="gsg_long", z_s1=94.0, z_g1=95.5, g_bar=False),
    "gsg_short": Geo3D(name="gsg_short", z_guard=10.0, z_s1=84.0, z_g1=86.0),
}


def slabs(g: Geo3D):
    zs = [g.z_top, 0.0] + [5.0 * k for k in range(1, int(g.z_bot // 5) + 1)]
    return list(zip(zs[:-1], zs[1:]))


def build(g: Geo3D, wd: str):
    tpp, tcore, er = P.STACK_4L[g.stack]
    hb2 = tpp + tcore / 2 + P.T_CU_IN
    yL2 = hb2 - tpp
    W2 = P.W_PROBE / 2
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("probe")
    occ = gmsh.model.occ
    # Substratscheiben (Viertelzylinder)
    sl = []
    for z0, z1 in slabs(g):
        c = occ.addCylinder(0, 0, z0, 0, 0, z1 - z0, g.R, angle=math.pi / 2)
        sl.append(c)
    # Sondenkontur in der x-z-Ebene als Prisma in y

    def outline_prism(y0, y1):
        zc = g.L - (W2 - g.x_tip)
        pts = [(0, g.z_top), (W2, g.z_top), (W2, zc), (g.x_tip, g.L), (0, g.L)]
        pt = [occ.addPoint(x, y0, z) for x, z in pts]
        ln = [occ.addLine(pt[i], pt[(i + 1) % len(pt)]) for i in range(len(pt))]
        cl = occ.addCurveLoop(ln)
        s = occ.addPlaneSurface([cl])
        ex = occ.extrude([(2, s)], 0, y1 - y0, 0)
        return [t for d, t in ex if d == 3][0]

    board = outline_prism(0.0, hb2)
    mask = outline_prism(hb2, hb2 + g.t_mask)
    # Elektroden auf L2 (Flaechen in der Ebene y = yL2)
    xe = W2 - g.edge

    def rect(x0, x1, z0, z1):
        return occ.addRectangle(x0, z0, 0, x1 - x0, z1 - z0)

    s_parts = [rect(0, g.ws / 2, g.z_s0, g.z_s1), rect(0, g.wf / 2, g.z_top, g.z_s0 + 0.5)]
    g_parts = [rect(g.wf / 2 + g.cf, xe, g.z_top, g.z_guard), rect(g.ws / 2 + g.gap, xe, g.z_top, g.z_g1)]
    if g.g_bar:
        g_parts.append(rect(0, xe, g.z_s1 + g.gap, g.z_s1 + g.gap + g.w_bar))
    s_f, _ = occ.fuse([(2, s_parts[0])], [(2, t) for t in s_parts[1:]])
    g_f, _ = occ.fuse([(2, g_parts[0])], [(2, t) for t in g_parts[1:]])
    el = s_f + g_f
    # Rechtecke liegen in der x-y-Ebene (z=0) mit (x, "z") -> drehen um x-Achse auf y = yL2
    occ.rotate(el, 0, 0, 0, 1, 0, 0, math.pi / 2)  # (x, y, 0) -> (x, 0, y)
    occ.translate(el, 0, yL2, 0)
    ntools = [(3, board), (3, mask)] + el
    out, omap = occ.fragment([(3, t) for t in sl], ntools)
    occ.synchronize()
    nsl = len(sl)
    vol_reg = {}
    for i, pieces in enumerate(omap[:nsl]):
        for d, t in pieces:
            if d == 3:
                vol_reg.setdefault(t, ("slab", i))
    for d, t in omap[nsl]:
        if d == 3:
            vol_reg[t] = ("fr4", 0)
    for d, t in omap[nsl + 1]:
        if d == 3:
            vol_reg[t] = ("mask", 0)
    surf_net = {}
    for d, t in [x for k in range(len(s_f)) for x in omap[nsl + 2 + k]]:
        if d == 2:
            surf_net[t] = "S"
    for d, t in [x for k in range(len(g_f)) for x in omap[nsl + 2 + len(s_f) + k]]:
        if d == 2:
            surf_net[t] = "G"
    gmsh.model.addPhysicalGroup(3, [t for t, r in vol_reg.items() if r[0] == "fr4"], tag=1)
    gmsh.model.addPhysicalGroup(3, [t for t, r in vol_reg.items() if r[0] == "mask"], tag=2)
    for i in range(nsl):
        tags = [t for t, r in vol_reg.items() if r == ("slab", i)]
        gmsh.model.addPhysicalGroup(3, tags, tag=10 + i)
    gmsh.model.addPhysicalGroup(2, [t for t, n in surf_net.items() if n == "S"], tag=1)
    gmsh.model.addPhysicalGroup(2, [t for t, n in surf_net.items() if n == "G"], tag=2)
    # Netz
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
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Algorithm3D", 10)  # HXT
    gmsh.option.setNumber("General.NumThreads", 16)
    gmsh.model.mesh.generate(3)
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    os.makedirs(wd, exist_ok=True)
    msh = os.path.join(wd, "probe.msh")
    gmsh.write(msh)
    ntet = sum(len(x) for x in gmsh.model.mesh.getElements(3)[1])
    nnode = len(gmsh.model.mesh.getNodes()[0])
    gmsh.finalize()
    subprocess.run(["ElmerGrid", "14", "2", "probe.msh", "-autoclean"], cwd=wd, check=True,
                   stdout=subprocess.DEVNULL)
    return {"ntet": ntet, "nnode": nnode, "nslab": len(slabs(g))}


SIF = """Header
  Mesh DB "." "probe"
End
Simulation
  Coordinate System = Cartesian 3D
  Simulation Type = Steady State
  Steady State Max Iterations = 1
  Coordinate Scaling = 0.001
  Output Intervals = 0
End
Constants
  Permittivity Of Vacuum = 8.8541878128e-12
End
{bodies}
Equation 1
  Active Solvers(2) = 1 2
End
Solver 1
  Equation = Stat Elec Solver
  Procedure = "StatElecSolveVec" "StatElecSolver"
  Variable = Potential
  Calculate Electric Energy = True
  Linear System Solver = Iterative
  Linear System Iterative Method = CG
  Linear System Preconditioning = ILU0
  Linear System Max Iterations = 5000
  Linear System Convergence Tolerance = 1e-9
End
Solver 2
  Exec Solver = After All
  Equation = SaveScalars
  Procedure = "SaveData" "SaveScalars"
  Filename = "{case}.dat"
End
Material 1
  Relative Permittivity = {er_fr4}
End
Material 2
  Relative Permittivity = {er_mask}
End
Material 3
  Relative Permittivity = 1.0
End
Material 4
  Relative Permittivity = {eps_soil}
End
Boundary Condition 1
  Target Boundaries(1) = 1
  Potential = 1
End
Boundary Condition 2
  Target Boundaries(1) = 2
  Potential = 0
End
"""


def write_case(wd, case, nslab, soil_mask, eps_soil, er_fr4):
    bodies = ["Body 1\n  Target Bodies(1) = 1\n  Equation = 1\n  Material = 1\nEnd",
              "Body 2\n  Target Bodies(1) = 2\n  Equation = 1\n  Material = 2\nEnd"]
    for i in range(nslab):
        mat = 4 if soil_mask[i] else 3
        bodies.append(f"Body {3 + i}\n  Target Bodies(1) = {10 + i}\n  Equation = 1\n  Material = {mat}\nEnd")
    txt = SIF.format(bodies="\n".join(bodies), case=case, er_fr4=er_fr4, er_mask=P.ER_MASK, eps_soil=eps_soil)
    with open(os.path.join(wd, case + ".sif"), "w") as f:
        f.write(txt)


def run_case(wd, case):
    log = open(os.path.join(wd, case + ".log"), "w")
    subprocess.run([ELMER, case + ".sif"], cwd=wd, stdout=log, stderr=subprocess.STDOUT, check=True)
    with open(os.path.join(wd, case + ".dat")) as f:
        v = [float(x) for x in f.read().split()]
    return case, 4 * v[2] * 1e12  # Viertelmodell -> volle Sonde, pF


def cases_for(g: Geo3D):
    sl = slabs(g)
    n = len(sl)
    soil_from = lambda zf: [z0 >= zf - 1e-9 for z0, z1 in sl]  # Substrat ab Fuellhoehe zf (Tiefe)
    _, _, er = P.STACK_4L[g.stack]
    C = {}
    # Grundfaelle: Luft, trocken, nass, Wasser bis zur Markierung (z = 5)
    C["air"] = (soil_from(1e9), 1.0, er)
    for key, eps in (("dry", P.EPS_DRY), ("wet", P.EPS_WET), ("water", P.EPS_WATER), ("e10", 10.0)):
        C[key] = (soil_from(5.0), eps, er)
    # FR4-Feuchte +10 % (Luft- und Wasserpunkt)
    C["air_fr4wet"] = (soil_from(1e9), 1.0, er * (1 + P.DK_FR4_MOIST_REL))
    C["water_fr4wet"] = (soil_from(5.0), P.EPS_WATER, er * (1 + P.DK_FR4_MOIST_REL))
    # Ueberflutung bis zur Dichtlinie
    C["wet_flood"] = (soil_from(0.0), P.EPS_WET, er)
    # Fuellstandskurve (nass): Substrat ab Tiefe zf
    for z0, z1 in sl:
        if z0 >= 5.0:
            C[f"fill{z0:05.1f}"] = (soil_from(z0), P.EPS_WET, er)
    # nur 10-90 mm nass, Rest trocken (Superpositionskontrolle)
    m = [(z0 >= 10 - 1e-9 and z1 <= 90 + 1e-9) for z0, z1 in sl]
    C["wet10_90_dryrest"] = ([z0 >= 5.0 - 1e-9 for z0, z1 in sl], None, er, m)
    return C, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--geo", default="gsg")
    ap.add_argument("--h", type=float, default=1.0)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    g = dc.replace(GEOS[a.geo], h=a.h)
    tag = f"{g.name}_h{a.h:g}"
    wd = os.path.join(HERE, "elmer3d", tag)
    info = build(g, wd)
    print(tag, info, flush=True)
    C, n = cases_for(g)
    todo = []
    for case, spec in C.items():
        if a.only and case not in a.only.split(","):
            continue
        if len(spec) == 3:
            soil, eps, er = spec
            write_case(wd, case, n, soil, eps, er)
        else:  # gemischte Belegung: 10-90 nass, sonst trocken -> eigene Materialien
            soil, _, er, wetm = spec
            write_case(wd, case, n, soil, P.EPS_DRY, er)
            p = os.path.join(wd, case + ".sif")
            txt = open(p).read()
            txt = txt.replace("Material 4\n", f"Material 5\n  Relative Permittivity = {P.EPS_WET}\nEnd\nMaterial 4\n", 1)
            for i in range(n):
                if wetm[i]:
                    txt = txt.replace(f"Target Bodies(1) = {10 + i}\n  Equation = 1\n  Material = 4",
                                      f"Target Bodies(1) = {10 + i}\n  Equation = 1\n  Material = 5")
            open(p, "w").write(txt)
        todo.append(case)
    res = {}
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for case, c in ex.map(lambda c: run_case(wd, c), todo):
            res[case] = c
            print(f"  {case:18s} C = {c:8.3f} pF", flush=True)
    out = os.path.join(HERE, "results", f"probe3d_{tag}.json")
    json.dump({"geo": dc.asdict(g), "mesh": info, "C_pF": res, "slabs": slabs(g)}, open(out, "w"), indent=1)
    print("->", out)


if __name__ == "__main__":
    main()
