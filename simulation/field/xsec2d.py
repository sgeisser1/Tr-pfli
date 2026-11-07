"""2D-Querschnittsmodell der Sonde (gmsh + scikit-fem), elektro-quasistatisch.

Loest div(kappa grad phi) = 0 im Querschnitt senkrecht zur Sondenachse; kappa = sigma + j w eps0 eps_r
je Region (reell, wenn sigma = 0). Elektroden als Linien ohne Dicke (Innenkupfer 15 um << Prepreg
210 um), Dirichlet phi = 1 (S, Sondenknoten) bzw. 0 (G, Masse). Aussenrand (Topfwand) natuerlich (Neumann).
Ergebnis: Kapazitaetsbelag C' [pF/m] = eps0 * phi^T K phi bzw. Admittanzbelag Y' [S/m].

Begruendung quasistatisch: Wellenlaenge im nassen Substrat bei 6 MHz lambda = c/(f sqrt(30)) ~ 9 m,
Eindringtiefe bei 0.3 S/m delta = 1/sqrt(pi f mu0 sigma) ~ 0.37 m, beides >> Geometrie (0.1 m).
"""
from __future__ import annotations

import dataclasses as dc
import math

import gmsh
import numpy as np
import scipy.sparse.linalg as spla
from skfem import Basis, BilinearForm, ElementTriP0, ElementTriP2, Functional, MeshTri, asm, condense
from skfem.helpers import dot, grad

import params as P

# Regionen (Prioritaet: spaeter in der Liste = innen)
REG = ["soil", "gap", "coat", "mask", "fr4", "core"]


@dc.dataclass
class Electrode:
    layer: str      # 'L2', 'L3' (4 Lagen innen) oder 'F', 'B' (2 Lagen aussen)
    x0: float
    x1: float
    net: str        # 'S' oder 'G'


@dc.dataclass
class Geometry:
    electrodes: list
    layers: int = 4
    stack: str = P.STACK_DEFAULT
    t_mask: float = P.T_MASK_LAM          # Loetstopplack auf beiden Flaechen
    t_coat: float = 0.0                   # Schutzlack rundum (inkl. Kanten)
    t_gap: float = 0.0                    # Luftspalt Sonde/Substrat rundum
    width: float = P.W_PROBE
    r_dom: float = 50.0                   # Topfradius
    er_fr4: float | None = None           # None -> aus Stackup
    er_mask: float = P.ER_MASK
    er_coat: float = P.ER_COAT
    # Netz (Konvergenz geprueft: Aenderung C' < 0.03 % gegen 4x feineres Netz, validate2d.py)
    h_min: float = 0.005                  # an Elektrodenkanten
    h_el: float = 0.06                    # entlang Elektroden
    h_max: float = 3.0
    dist_el: float = 10.0                 # Netzwachstum Elektroden
    dist_surf: float = 5.0                # Netzwachstum Oberflaeche
    surf_fac: float = 1.2

    def stack_vals(self):
        if self.layers == 4:
            tpp, tcore, er = P.STACK_4L[self.stack]
            hb = 2 * tpp + tcore + 2 * P.T_CU_IN
            return tpp, tcore, er, hb
        return 0.0, 0.0, P.ER_2L, P.T_2L

    def layer_y(self, layer):
        tpp, tcore, er, hb = self.stack_vals()
        return {"L2": hb / 2 - tpp, "L3": -(hb / 2 - tpp), "F": hb / 2, "B": -hb / 2}[layer]

    def outer_halfsizes(self):
        """Halbe Breite/Hoehe der Sondenoberflaeche (inkl. Lack/Coating), ohne Luftspalt."""
        tpp, tcore, er, hb = self.stack_vals()
        return self.width / 2 + self.t_coat, hb / 2 + self.t_mask + self.t_coat


def build_mesh(g: Geometry):
    tpp, tcore, er, hb = g.stack_vals()
    W2 = g.width / 2
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("xsec")
    occ = gmsh.model.occ
    shapes = []  # (dimtag, region)
    shapes.append(((2, occ.addDisk(0, 0, 0, g.r_dom, g.r_dom)), "soil"))
    yo = hb / 2 + g.t_mask + g.t_coat
    if g.t_gap > 0:
        shapes.append(((2, occ.addRectangle(-W2 - g.t_coat - g.t_gap, -yo - g.t_gap, 0,
                                              g.width + 2 * (g.t_coat + g.t_gap), 2 * (yo + g.t_gap))), "gap"))
    if g.t_coat > 0:
        shapes.append(((2, occ.addRectangle(-W2 - g.t_coat, -yo, 0, g.width + 2 * g.t_coat, 2 * yo)), "coat"))
    if g.t_mask > 0:
        shapes.append(((2, occ.addRectangle(-W2, hb / 2, 0, g.width, g.t_mask)), "mask"))
        shapes.append(((2, occ.addRectangle(-W2, -hb / 2 - g.t_mask, 0, g.width, g.t_mask)), "mask"))
    shapes.append(((2, occ.addRectangle(-W2, -hb / 2, 0, g.width, hb)), "fr4"))
    if g.layers == 4:
        yc = hb / 2 - tpp
        shapes.append(((2, occ.addRectangle(-W2, -yc, 0, g.width, 2 * yc)), "core"))
    lines = []
    for e in g.electrodes:
        y = g.layer_y(e.layer)
        p0 = occ.addPoint(e.x0, y, 0)
        p1 = occ.addPoint(e.x1, y, 0)
        lines.append(((1, occ.addLine(p0, p1)), e.net))
    obj = [shapes[0][0]]
    tools = [s[0] for s in shapes[1:]] + [l[0] for l in lines]
    out, omap = occ.fragment(obj, tools)
    occ.synchronize()
    inputs = [shapes[0]] + shapes[1:] + lines
    surf_reg = {}
    line_net = {}
    for (dimtag, reg), pieces in zip(inputs, omap):
        for d, t in pieces:
            if d == 2:
                old = surf_reg.get(t)
                if old is None or REG.index(reg) > REG.index(old):
                    surf_reg[t] = reg
            elif d == 1 and reg in ("S", "G"):
                line_net[t] = reg
    for reg in REG:
        tags = [t for t, r in surf_reg.items() if r == reg]
        if tags:
            gmsh.model.addPhysicalGroup(2, tags, name=reg)
    for net in ("S", "G"):
        tags = [t for t, r in line_net.items() if r == net]
        if tags:
            gmsh.model.addPhysicalGroup(1, tags, name=net)
    # Netzfelder
    el_lines = list(line_net.keys())
    ends = []
    for t in el_lines:
        ends += [abs(b[1]) for b in gmsh.model.getBoundary([(1, t)], oriented=False)]
    f = gmsh.model.mesh.field
    f1 = f.add("Distance"); f.setNumbers(f1, "CurvesList", el_lines); f.setNumber(f1, "Sampling", 400)
    f2 = f.add("Threshold"); f.setNumber(f2, "InField", f1)
    f.setNumber(f2, "SizeMin", g.h_el); f.setNumber(f2, "SizeMax", g.h_max)
    f.setNumber(f2, "DistMin", 0.05); f.setNumber(f2, "DistMax", g.dist_el)
    f3 = f.add("Distance"); f.setNumbers(f3, "PointsList", ends)
    f4 = f.add("Threshold"); f.setNumber(f4, "InField", f3)
    f.setNumber(f4, "SizeMin", g.h_min); f.setNumber(f4, "SizeMax", g.h_max)
    f.setNumber(f4, "DistMin", 0.002); f.setNumber(f4, "DistMax", 1.5)
    # Sondenoberflaeche fein (Lack/Coating/Spalt aufloesen)
    bnd = [abs(b[1]) for t in [s for s, r in surf_reg.items() if r in ("mask", "coat", "gap", "fr4")]
           for b in gmsh.model.getBoundary([(2, t)], oriented=False)]
    f5 = f.add("Distance"); f.setNumbers(f5, "CurvesList", list(set(bnd))); f.setNumber(f5, "Sampling", 400)
    f6 = f.add("Threshold"); f.setNumber(f6, "InField", f5)
    tmin = min([x for x in (g.t_mask, g.t_coat, g.t_gap, 0.1) if x > 0])
    f.setNumber(f6, "SizeMin", max(tmin * g.surf_fac, 0.01)); f.setNumber(f6, "SizeMax", g.h_max)
    f.setNumber(f6, "DistMin", 0.02); f.setNumber(f6, "DistMax", g.dist_surf)
    f7 = f.add("Min"); f.setNumbers(f7, "FieldsList", [f2, f4, f6])
    f.setAsBackgroundMesh(f7)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.model.mesh.generate(2)
    # Knoten und Dreiecke je Region
    ntags, coords, _ = gmsh.model.mesh.getNodes()
    idx = {t: i for i, t in enumerate(ntags)}
    p = coords.reshape(-1, 3)[:, :2].T.copy()
    tris, regs = [], []
    for reg in REG:
        for t in [s for s, r in surf_reg.items() if r == reg]:
            et, _, en = gmsh.model.mesh.getElements(2, t)
            for typ, nodes in zip(et, en):
                if typ == 2:
                    tri = np.vectorize(idx.get)(nodes.reshape(-1, 3))
                    tris.append(tri)
                    regs.append(np.full(len(tri), REG.index(reg)))
    t = np.vstack(tris).T.copy()
    regs = np.concatenate(regs)
    seg = {"S": [], "G": []}
    for lt, net in line_net.items():
        et, _, en = gmsh.model.mesh.getElements(1, lt)
        for typ, nodes in zip(et, en):
            if typ == 1:
                seg[net].append(np.vectorize(idx.get)(nodes.reshape(-1, 2)))
    gmsh.finalize()
    # unbenutzte Knoten entfernen
    used = np.unique(t)
    remap = -np.ones(p.shape[1], dtype=int)
    remap[used] = np.arange(len(used))
    p = np.ascontiguousarray(p[:, used])
    t = remap[t]
    seg = {k: remap[np.vstack(v)] if v else np.zeros((0, 2), int) for k, v in seg.items()}
    return p, t, regs, seg


@BilinearForm
def _lap(u, v, w):
    return w.ind * dot(grad(u), grad(v))


@Functional
def _edens(w):
    return dot(grad(w.phi), grad(w.phi))


class Model:
    """Netz + regionweise Steifigkeitsmatrizen; danach beliebige Materialbelegungen schnell loesbar."""

    def __init__(self, g: Geometry):
        self.g = g
        p, t, regs, seg = build_mesh(g)
        self.mesh = MeshTri(p, t)
        self.regs = regs
        self.basis = Basis(self.mesh, ElementTriP2())
        b0 = self.basis.with_element(ElementTriP0())
        self.K = {}
        for i, reg in enumerate(REG):
            ind = (regs == i).astype(float)
            if ind.any():
                self.K[reg] = asm(_lap, self.basis, ind=b0.interpolate(ind)).tocsr()
        # Dirichlet-Freiheitsgrade auf Elektrodenlinien
        fac = self.mesh.facets
        key = {tuple(sorted(c)): i for i, c in enumerate(fac.T)}
        self.dof = {}
        for net in ("S", "G"):
            fi = np.array([key[tuple(sorted(s))] for s in seg[net]], dtype=int)
            self.dof[net] = self.basis.get_dofs(facets=fi).all()
        D = np.concatenate([self.dof["S"], self.dof["G"]])
        self.D = np.unique(D)
        self.x0 = np.zeros(self.basis.N)
        self.x0[self.dof["S"]] = 1.0
        # Element-Schwerpunkte und Abstand zur Sondenoberflaeche
        c = p[:, t].mean(axis=1)
        a, b = g.outer_halfsizes()
        self.centroid = c
        self.dist = np.hypot(np.maximum(np.abs(c[0]) - a, 0), np.maximum(np.abs(c[1]) - b, 0))
        self.area = self.mesh.volume if hasattr(self.mesh, "volume") else None
        self.nel = t.shape[1]
        self.ndof = self.basis.N

    def default_eps(self, eps_soil):
        tpp, tcore, er, hb = self.g.stack_vals()
        er = self.g.er_fr4 if self.g.er_fr4 is not None else er
        er_core = P.ER_CORE if self.g.er_fr4 is None else self.g.er_fr4
        return {"soil": eps_soil, "gap": 1.0, "coat": self.g.er_coat, "mask": self.g.er_mask,
                "fr4": er, "core": er_core}

    def solve(self, kappa: dict):
        """kappa: Region -> (komplexe) relative Leitwertzahl. Rueckgabe (Y, phi) mit Y = phi^T A phi."""
        A = sum(kappa[r] * K for r, K in self.K.items())
        dtype = complex if any(np.iscomplexobj(np.asarray(v)) for v in kappa.values()) else float
        A = A.astype(dtype)
        x = self.x0.astype(dtype)
        Ac, bc, xc, I = condense(A, x=x, D=self.D)
        xs = x.copy()
        xs[I] = spla.spsolve(Ac.tocsc(), bc)
        Y = xs @ (A @ xs)
        return Y, xs

    def cap(self, eps: dict):
        """C' in pF/m (Laengen in mm -> 2D-Integral dimensionslos)."""
        Y, phi = self.solve(eps)
        return float(np.real(Y)) * P.EPS0 * 1e12, phi

    def region_sens(self, phi):
        """dC'/d eps_r je Region in pF/m."""
        return {r: float(phi @ (K @ phi)) * P.EPS0 * 1e12 for r, K in self.K.items()}

    def element_energy(self, phi):
        """|grad phi|^2 integriert je Element (dimensionslos)."""
        return _edens.elemental(self.basis, phi=self.basis.interpolate(phi))

    def admittance(self, eps_r: dict, sigma: dict, f: float):
        """Komplexer Admittanzbelag Y' in S/m; eps_r komplex erlaubt (Verlustfaktor)."""
        w = 2 * math.pi * f
        kap = {r: sigma.get(r, 0.0) + 1j * w * P.EPS0 * eps_r[r] for r in self.K}
        Y, phi = self.solve(kap)
        return Y, phi


# ---- Topologien -----------------------------------------------------------------------------------

def topo_sg(gap, layers=("L2", "L3"), e=P.EDGE_CLEAR, W=P.W_PROBE):
    """Zwei Streifen koplanar: S links, G rechts, auf beiden Innenlagen gespiegelt."""
    a = W / 2 - e
    return [Electrode(l, -a, -gap / 2, "S") for l in layers] + [Electrode(l, gap / 2, a, "G") for l in layers]


def topo_gsg(ws, gap, layers=("L2", "L3"), e=P.EDGE_CLEAR, W=P.W_PROBE):
    """G-S-G koplanar: S mittig (Breite ws), G an beiden Raendern, Abstand gap."""
    a = W / 2 - e
    el = []
    for l in layers:
        el += [Electrode(l, -ws / 2, ws / 2, "S"), Electrode(l, -a, -ws / 2 - gap, "G"),
               Electrode(l, ws / 2 + gap, a, "G")]
    return el


def topo_sgs(wg, gap, layers=("L2", "L3"), e=P.EDGE_CLEAR, W=P.W_PROBE):
    """S-G-S: G mittig, S an den Raendern (Gegenstueck zu GSG)."""
    return [Electrode(x.layer, x.x0, x.x1, "S" if x.net == "G" else "G") for x in topo_gsg(wg, gap, layers, e, W)]


def topo_offset(gap, e=P.EDGE_CLEAR, W=P.W_PROBE):
    """Versetzt: S auf L2 (links), G auf L3 (rechts); je Elektrode nur eine Lage."""
    a = W / 2 - e
    return [Electrode("L2", -a, -gap / 2, "S"), Electrode("L3", gap / 2, a, "G")]


def topo_cross(gap, e=P.EDGE_CLEAR, W=P.W_PROBE):
    """Kreuz: L2 S links/G rechts, L3 G links/S rechts."""
    a = W / 2 - e
    return [Electrode("L2", -a, -gap / 2, "S"), Electrode("L2", gap / 2, a, "G"),
            Electrode("L3", -a, -gap / 2, "G"), Electrode("L3", gap / 2, a, "S")]


def topo_ide(n, gap, layers=("L2", "L3"), e=P.EDGE_CLEAR, W=P.W_PROBE):
    """Interdigital im Querschnitt: n Streifen abwechselnd S/G ueber die nutzbare Breite."""
    a = W / 2 - e
    w = (2 * a - (n - 1) * gap) / n
    el = []
    for l in layers:
        x = -a
        for k in range(n):
            el.append(Electrode(l, x, x + w, "S" if k % 2 == 0 else "G"))
            x += w + gap
    return el
