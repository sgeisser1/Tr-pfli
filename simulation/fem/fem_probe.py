# -*- coding: utf-8 -*-
"""FEM der Sonde fluidi P3 (REQ-MECH-10): FreeCAD 0.21.2 FEM + Gmsh + CalculiX, headless.

Lauf:  freecadcmd simulation/fem/fem_probe.py            (ca. 5-10 min)
Ausgabe: simulation/fem/results.json, simulation/fem/fem_log.txt, simulation/fem/work/<fall>/ (ccx-Dateien),
         simulation/fem/fem_probe_<fall>.FCStd (Modell inkl. Ergebnis, nur feinstes Netz)
Bericht: simulation/fem/REPORT.md

Modell (Masse aus mechanical/gen/fluidi_params.py, Schnittstelle Rev A):
  Leiterplatte FR4 20 x 1.6 mm, Spitze 45 Grad, von z = -105 (Spitze) bis z = 32.0 (Schott, eingespannt).
  Kragen (Verguss + ASA) als ein Koerper z 2.0 ... 7.3 um die Platine, mit der Platine verbunden (gemeinsames Netz),
  Aussenflaechen fest (Huelse liegt nach 0.2 mm Spiel an). Vergusskante bei z = 2.0 (Kragenunterkante, buendig).
Werkstoffe (ANNAHMEN, Quellen in REPORT.md): FR4 E = 20 GPa, nu = 0.15; Kragen E = 3 GPa (Epoxid, steifer als ASA ->
  konservativ fuer die Kerbe), nu = 0.35.
"""
import json
import math
import os
import re
import sys
import time

import FreeCAD as App
import Part
import ObjectsFem
import BOPTools.SplitAPI
from femtools import ccxtools
from femmesh.gmshtools import GmshTools

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'mechanical', 'gen'))
import fluidi_params as FP

OUT = os.path.join(REPO, 'simulation', 'fem')
V = App.Vector
PCB, Z = FP.PCB, FP.Z
E_FR4, NU_FR4 = 20000.0, 0.15
E_COL, NU_COL = 3000.0, 0.35
Z_TOP = Z['BULK1']                    # 32.0 Einspannung im Schott
Z_EDGE = Z['COL0']                    # 2.0 Vergusskante
Z_COL1 = Z['COL1']
Z_R0, Z_R1 = -3.0, 3.0                # verfeinerter Bereich
LOG = []


def log(*a):
    s = ' '.join(str(x) for x in a); print(s, flush=True); LOG.append(s)


def pcb_piece(z0, z1):
    out = FP.outline()
    poly = [(x, max(min(z, z1), z0)) for x, z in out]
    # Kontur auf z0..z1 beschneiden: ueber Schnitt mit Box
    s = Part.Face(Part.makePolygon([V(x, PCB['Y_F'], z) for x, z in out] + [V(out[0][0], PCB['Y_F'], out[0][1])]))
    s = s.extrude(V(0, PCB['T'], 0))
    return s.common(Part.makeBox(40, 10, z1 - z0, V(-20, PCB['Y_F'] - 1, z0)))


def geometry():
    pcb_full = pcb_piece(PCB['Z_TIP'], Z_TOP)
    pieces = [pcb_piece(PCB['Z_TIP'], Z_R0), pcb_piece(Z_R0, Z_EDGE), pcb_piece(Z_EDGE, Z_R1),
              pcb_piece(Z_R1, Z_COL1), pcb_piece(Z_COL1, Z_TOP)]
    G = FP.GROOVE_BOT
    col = Part.makeBox(2 * G['X'], G['Y1'] - G['Y0'], Z_COL1 - Z_EDGE, V(-G['X'], G['Y0'], Z_EDGE)).cut(pcb_full)
    col_lo = col.common(Part.makeBox(40, 20, Z_R1 - Z_EDGE, V(-20, 0, Z_EDGE)))
    col_hi = col.common(Part.makeBox(40, 20, Z_COL1 - Z_R1, V(-20, 0, Z_R1)))
    frag = BOPTools.SplitAPI.booleanFragments(pieces + [col_lo, col_hi], 'CompSolid', 0.0)
    return frag


def name_solids(shape):
    """Solids nach Schwerpunkt zuordnen."""
    d = {'pcb': [], 'col': [], 'fine': []}
    for i, so in enumerate(shape.Solids, 1):
        c = so.CenterOfMass
        is_pcb = PCB['Y_F'] - 1e-3 <= c.y <= PCB['Y_B'] + 1e-3 and abs(c.x) <= PCB['W'] / 2
        (d['pcb'] if is_pcb else d['col']).append('Solid%d' % i)
        if Z_R0 - 1e-3 <= so.BoundBox.ZMin and so.BoundBox.ZMax <= Z_R1 + 1e-3:
            d['fine'].append('Solid%d' % i)
    return d


def faces(shape, pred):
    return ['Face%d' % i for i, f in enumerate(shape.Faces, 1) if pred(f)]


def edge_dir(shape, vec):
    for i, e in enumerate(shape.Edges, 1):
        if len(e.Vertexes) == 2:
            d = e.Vertexes[1].Point - e.Vertexes[0].Point
            if d.Length > 0.5 and abs(abs(d.normalize().dot(vec)) - 1) < 1e-6:
                return 'Edge%d' % i
    raise RuntimeError('keine Kante in Richtung %s' % vec)


def build_case(case, h_fine, h_glob=3.0):
    doc = App.newDocument('fem_' + case['name'])
    geo = doc.addObject('Part::Feature', 'Geo')
    geo.Shape = geometry()
    sh = geo.Shape
    nm = name_solids(sh)
    an = ObjectsFem.makeAnalysis(doc, 'Analysis')
    solver = ObjectsFem.makeSolverCalculixCcxTools(doc, 'Solver')
    solver.AnalysisType = case.get('type', 'static')
    if case.get('type') == 'buckling':
        solver.BucklingFactors = 2
    solver.GeometricalNonlinearity = 'linear'
    an.addObject(solver)
    m1 = ObjectsFem.makeMaterialSolid(doc, 'FR4')
    m1.Material = {'Name': 'FR4', 'YoungsModulus': '%g MPa' % E_FR4, 'PoissonRatio': str(NU_FR4), 'Density': '1850 kg/m^3'}
    m1.References = [(geo, tuple(nm['pcb']))]
    an.addObject(m1)
    m2 = ObjectsFem.makeMaterialSolid(doc, 'Kragen')
    m2.Material = {'Name': 'Kragen', 'YoungsModulus': '%g MPa' % E_COL, 'PoissonRatio': str(NU_COL), 'Density': '1150 kg/m^3'}
    m2.References = [(geo, tuple(nm['col']))]
    an.addObject(m2)
    # Einspannung: Platine im Schott (Stirnflaeche z = 32) + Kragen-Aussenflaechen (Huelse)
    G = FP.GROOVE_BOT
    fix_f = faces(sh, lambda f: abs(f.BoundBox.ZMin - Z_TOP) < 1e-6 and abs(f.BoundBox.ZMax - Z_TOP) < 1e-6)
    col_out = faces(sh, lambda f: (abs(abs(f.BoundBox.XMin) - G['X']) < 1e-6 and abs(f.BoundBox.XMax - f.BoundBox.XMin) < 1e-6) or
                    (abs(f.BoundBox.YMin - f.BoundBox.YMax) < 1e-6 and (abs(f.BoundBox.YMin - G['Y0']) < 1e-6 or abs(f.BoundBox.YMin - G['Y1']) < 1e-6)))
    fx = ObjectsFem.makeConstraintFixed(doc, 'Fixed')
    fx.References = [(geo, tuple(fix_f + (col_out if case.get('collar_fixed', True) else [])))]
    an.addObject(fx)
    tip = faces(sh, lambda f: abs(f.BoundBox.ZMax - PCB['Z_TIP']) < 1e-6 and abs(f.BoundBox.ZMin - PCB['Z_TIP']) < 1e-6)
    if case.get('tip_guided'):
        dsp = ObjectsFem.makeConstraintDisplacement(doc, 'TipGuided')
        dsp.References = [(geo, tuple(tip))]
        dsp.xFree = False; dsp.xFix = True; dsp.yFree = False; dsp.yFix = True
        an.addObject(dsp)
    fo = ObjectsFem.makeConstraintForce(doc, 'Force')
    fo.References = [(geo, tuple(tip))]
    fo.Force = case['F']
    fo.Direction = (geo, [edge_dir(sh, V(*case['dir']))])
    fo.Reversed = case.get('reversed', False)
    an.addObject(fo)
    mesh = ObjectsFem.makeMeshGmsh(doc, 'Mesh')
    mesh.Part = geo
    mesh.CharacteristicLengthMax = h_glob
    mesh.CharacteristicLengthMin = min(h_fine, 0.1)
    mesh.ElementOrder = '2nd'
    an.addObject(mesh)
    reg = ObjectsFem.makeMeshRegion(doc, mesh, h_fine, 'Fine')
    reg.References = [(geo, tuple(nm['fine']))]
    doc.recompute()
    err = GmshTools(mesh).create_mesh()
    if err:
        log('  gmsh:', err)
    return doc, an, solver, mesh, fo


def run_case(case, h_fine, keep=False):
    t0 = time.time()
    doc, an, solver, mesh, fo = build_case(case, h_fine)
    wd = os.path.join(OUT, 'work', '%s_h%.2f' % (case['name'], h_fine))
    os.makedirs(wd, exist_ok=True)
    fea = ccxtools.FemToolsCcx(an, solver)
    fea.update_objects()
    fea.setup_working_dir(wd)
    fea.setup_ccx()
    msg = fea.check_prerequisites()
    if msg:
        raise RuntimeError(msg)
    fea.purge_results()
    fea.write_inp_file()
    fea.ccx_run()
    fea.load_results()
    nn = mesh.FemMesh.NodeCount
    out = dict(case=case['name'], h_fine=h_fine, nodes=nn, t=round(time.time() - t0, 1))
    if case.get('type') == 'buckling':
        dat = [f for f in os.listdir(wd) if f.endswith('.dat')][0]
        txt = open(os.path.join(wd, dat)).read()
        bf = re.findall(r'^\s+(\d+)\s+([-0-9.E+]+)\s*$', txt.split('B U C K L I N G')[-1], re.M)
        out['buckling_factors'] = [float(b[1]) for b in bf[:2]]
        out['P_cr_N'] = [round(f * case['F'], 1) for f in out['buckling_factors']]
    else:
        res = [o for o in doc.Objects if o.isDerivedFrom('Fem::FemResultObjectPython')][0]
        nodes = res.Mesh.FemMesh.Nodes
        ids = list(res.NodeNumbers)
        szz = res.NodeStressZZ
        p1 = res.PrincipalMax
        p3 = res.PrincipalMin
        dl = res.DisplacementLengths
        idx = {nid: k for k, nid in enumerate(ids)}
        surf = []
        for nid, p in nodes.items():
            on_surf = abs(p.y - PCB['Y_F']) < 1e-4 or abs(p.y - PCB['Y_B']) < 1e-4
            if on_surf and abs(p.x) <= 9.5 and -60 <= p.z <= Z_EDGE + 1e-6:
                k = idx[nid]
                surf.append((p.z, p.y, szz[k], p1[k], p3[k]))
        def at(zq, tol=0.3):
            v = [abs(s[2]) for s in surf if abs(s[0] - zq) <= tol]
            return round(max(v), 2) if v else None
        free = [s for s in surf if s[0] < Z_EDGE - 1e-3]
        out['sigma_zz_max_free'] = round(max(abs(s[2]) for s in free), 2)
        out['sigma_1_max_free'] = round(max(max(s[3], -s[4]) for s in free), 2)
        out['sigma_zz_edge'] = round(max(abs(s[2]) for s in surf if abs(s[0] - Z_EDGE) < 1e-6), 2)
        pcb_nodes = [k for nid, k in idx.items() if PCB['Y_F'] - 1e-4 <= nodes[nid].y <= PCB['Y_B'] + 1e-4
                     and abs(nodes[nid].x) <= PCB['W'] / 2 + 1e-4 and nodes[nid].z <= Z_TOP]
        out['sigma_1_max_pcb'] = round(max(max(p1[k], -p3[k]) for k in pcb_nodes), 2)
        out['vm_max'] = round(max(res.vonMises), 2)
        for zq in (-50.0, -20.0, -5.0, -1.0, 0.0, 1.0, 1.5):
            out['sigma_zz_at_%g' % zq] = at(zq, 0.35 if zq > -5 else 1.0)
        tipn = [k for nid, k in idx.items() if abs(nodes[nid].z - PCB['Z_TIP']) < 1e-4]
        out['u_tip'] = round(max(dl[k] for k in tipn), 3)
    log('  %-14s h=%.2f Knoten %6d  %s  (%.0f s)' % (case['name'], h_fine, out['nodes'],
        {k: v for k, v in out.items() if k not in ('case', 'h_fine', 'nodes', 't')}, out['t']))
    if keep:
        doc.saveAs(os.path.join(OUT, 'fem_probe_%s.FCStd' % case['name']))
    App.closeDocument(doc.Name)
    return out


def hand():
    b, t = PCB['W'], PCB['T']
    Iw = b * t ** 3 / 12
    Wy = b * t ** 2 / 6
    Wx = t * b ** 2 / 6
    L = Z_EDGE - PCB['Z_TIP']
    h = dict(I_weak=Iw, W_weak=Wy, W_strong=Wx, L_lever=L,
             sig_lat_y=10 * L / Wy, sig_lat_x=10 * L / Wx, sig_axial=50 / (b * t), sig_tension=30 / (b * t),
             u_tip_y=10 * L ** 3 / (3 * E_FR4 * Iw),
             Pcr_free=math.pi ** 2 * E_FR4 * Iw / (4 * L ** 2), Pcr_guided=2.046 * math.pi ** 2 * E_FR4 * Iw / L ** 2)
    return {k: round(v, 3) for k, v in h.items()}


def main():
    os.makedirs(os.path.join(OUT, 'work'), exist_ok=True)
    H = hand()
    log('Handrechnung:', H)
    cases = [
        dict(name='LC1_seitlich_y', F=10.0, dir=(0, 1, 0)),
        dict(name='LC2_seitlich_x', F=10.0, dir=(1, 0, 0)),
        dict(name='LC3_axial_druck', F=50.0, dir=(0, 0, 1)),
        dict(name='LC4_zug', F=30.0, dir=(0, 0, 1), reversed=True),
        dict(name='LC5_knick_frei', F=50.0, dir=(0, 0, 1), type='buckling'),
        dict(name='LC6_knick_gefuehrt', F=50.0, dir=(0, 0, 1), type='buckling', tip_guided=True),
        dict(name='LC1b_ohne_Kragenstuetze', F=10.0, dir=(0, 1, 0), collar_fixed=False),
    ]
    R = dict(hand=H, materials=dict(E_FR4=E_FR4, nu_FR4=NU_FR4, E_collar=E_COL, nu_collar=NU_COL), runs=[])
    if os.environ.get('FEM_QUICK'):
        run_case(cases[0], 1.0); run_case(cases[4], 1.0); return
    # Netzkonvergenz am kritischen Fall
    for hf in (1.0, 0.5, 0.25):
        R['runs'].append(run_case(cases[0], hf, keep=(hf == 0.25)))
    for c in cases[1:]:
        R['runs'].append(run_case(c, 0.5, keep=False))
    json.dump(R, open(os.path.join(OUT, 'results.json'), 'w'), indent=1)
    open(os.path.join(OUT, 'fem_log.txt'), 'w').write('\n'.join(LOG) + '\n')


main()
