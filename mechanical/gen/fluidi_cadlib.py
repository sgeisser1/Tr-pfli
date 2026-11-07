# -*- coding: utf-8 -*-
"""Gemeinsame FreeCAD-Hilfsfunktionen fuer fluidi_sensor.py, fluidi_gateway.py, fem_probe.py (FreeCAD 0.21.2)."""
import math
import os
import re

import FreeCAD as App
import Part

V = App.Vector


def prism(poly_xy, z0, z1):
    pts = [V(x, y, z0) for x, y in poly_xy] + [V(poly_xy[0][0], poly_xy[0][1], z0)]
    return Part.Face(Part.makePolygon(pts)).extrude(V(0, 0, z1 - z0))


def prism_xz(poly_xz, y0, y1):
    """Polygon in der x-z-Ebene, extrudiert in y von y0 nach y1."""
    pts = [V(x, y0, z) for x, z in poly_xz] + [V(poly_xz[0][0], y0, poly_xz[0][1])]
    return Part.Face(Part.makePolygon(pts)).extrude(V(0, y1 - y0, 0))


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, z0, z1, x=0.0, y=0.0):
    return Part.makeCylinder(r, z1 - z0, V(x, y, z0))


def cyl_y(r, y0, y1, x, z):
    return Part.makeCylinder(r, y1 - y0, V(x, y0, z), V(0, 1, 0))


def plan(W, D, cf, cb, off=0.0):
    """P3-Grundriss mit Fasen vorne cf / hinten cb, parallel um off nach innen versetzt (Fasen 45 Grad)."""
    h = W / 2 - off
    y0, y1 = off, D - off
    k = 0.4142 * off
    a, b = max(cf - k, 0.3), max(cb - k, 0.3)
    return [(-h + a, y0), (h - a, y0), (h, y0 + a), (h, y1 - b), (h - b, y1), (-h + b, y1), (-h, y1 - b), (-h, y0 + a)]


def rrect_wire(xh, y0, y1, r, z):
    x0, x1 = -xh, xh
    e = [Part.LineSegment(V(x0 + r, y0, z), V(x1 - r, y0, z)).toShape(),
         Part.ArcOfCircle(Part.Circle(V(x1 - r, y0 + r, z), V(0, 0, 1), r), -math.pi / 2, 0).toShape(),
         Part.LineSegment(V(x1, y0 + r, z), V(x1, y1 - r, z)).toShape(),
         Part.ArcOfCircle(Part.Circle(V(x1 - r, y1 - r, z), V(0, 0, 1), r), 0, math.pi / 2).toShape(),
         Part.LineSegment(V(x1 - r, y1, z), V(x0 + r, y1, z)).toShape(),
         Part.ArcOfCircle(Part.Circle(V(x0 + r, y1 - r, z), V(0, 0, 1), r), math.pi / 2, math.pi).toShape(),
         Part.LineSegment(V(x0, y1 - r, z), V(x0, y0 + r, z)).toShape(),
         Part.ArcOfCircle(Part.Circle(V(x0 + r, y0 + r, z), V(0, 0, 1), r), math.pi, 1.5 * math.pi).toShape()]
    return Part.Wire(Part.__sortEdges__(e))


def rrect(d, z0, z1, grow=0.0):
    """d: dict X (halbe Breite), Y0, Y1, R. grow > 0 vergroessert nach aussen."""
    w = rrect_wire(d['X'] + grow, d['Y0'] - grow, d['Y1'] + grow, max(d['R'] + grow, 0.05), z0)
    return Part.Face(w).extrude(V(0, 0, z1 - z0))


def rrect_perimeter(d):
    return 2 * (2 * d['X'] + d['Y1'] - d['Y0']) - 8 * d['R'] + 2 * math.pi * d['R']


def drop2(cx, cz, r, k=2.4, n=48):
    """Tropfen (wie Logo/Render): Kreis r, tangentiale Spitze k*r ueber der Mitte. Polygon (x, z)."""
    h = k * r
    phi = math.asin(r / h)
    pts = [(cx, cz + h)]
    a0, a1 = math.pi - phi, 2 * math.pi + phi
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        pts.append((cx + r * math.cos(t), cz + r * math.sin(t)))
    return pts


def hexagon(s, cx, cy, flats_parallel_x=True):
    """Sechskant Schluesselweite s; flats_parallel_x -> Ausdehnung in y = s."""
    rc = s / 2 / math.cos(math.pi / 6)
    off = 0.0 if not flats_parallel_x else math.pi / 6 * 0
    pts = []
    for k in range(6):
        a = k * math.pi / 3 + (0.0 if flats_parallel_x else math.pi / 6)
        pts.append((cx + rc * math.cos(a), cy + rc * math.sin(a)))
    return pts


def svg_polys(path):
    """Liest Pfade aus M/L/Z-SVG (Logo-Generator), liefert (polys, width, height) in SVG-Einheiten."""
    txt = open(path, encoding='utf-8').read()
    vb = [float(v) for v in re.search(r'viewBox="([^"]+)"', txt).group(1).split()]
    polys = []
    for d in re.findall(r' d="([^"]+)"', txt):
        for sub in re.split(r'Z', d):
            nums = re.findall(r'[-0-9.]+,[-0-9.]+', sub)
            if len(nums) >= 3:
                polys.append([tuple(float(v) for v in p.split(',')) for p in nums])
    return polys, vb[2], vb[3]


def _area(p):
    return 0.5 * sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))


def _inside(pt, poly):
    x, y = pt
    c = False
    for i in range(len(poly)):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % len(poly)]
        if (y0 > y) != (y1 > y) and x < (x1 - x0) * (y - y0) / (y1 - y0) + x0:
            c = not c
    return c


def logo_solid(svg, width, xc, zc, y_face, relief, outward=-1):
    """Wortmarke als Relief in der x-z-Ebene: Breite width, Mitte (xc, zc), auf Flaeche y_face,
    erhaben um relief in Richtung outward (-1 = nach -y). Liefert (solid, min. Strichbreite-Skala)."""
    polys, w, h = svg_polys(svg)
    s = width / w
    conv = [[(xc + (u - w / 2) * s, zc + (h / 2 - v) * s) for u, v in p] for p in polys]
    conv.sort(key=lambda p: -abs(_area(p)))
    outers, holes = [], []
    for p in conv:
        if any(_inside(p[0], o) for o in outers):
            holes.append(p)
        else:
            outers.append(p)
    y0, y1 = (y_face + outward * relief, y_face + 0.05 * -outward) if outward < 0 else (y_face - 0.05, y_face + relief)
    sol = None
    for o in outers:
        so = prism_xz(o, y0, y1)
        for hp in holes:
            if _inside(hp[0], o):
                so = so.cut(prism_xz(hp, y0 - 0.1, y1 + 0.1))
        sol = so if sol is None else sol.fuse(so)
    return sol.removeSplitter(), s


FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def text_solid(s, size, xc, zb, y0, y1, font=FONT):
    """Text in der x-z-Ebene (lesbar mit Blick in +y), zentriert auf xc, Grundlinie zb, extrudiert y0..y1."""
    chars = Part.makeWireString(s, font, size, 0.0)
    faces = []
    for ch in chars:
        if not ch:
            continue
        try:
            f = Part.makeFace(ch, 'Part::FaceMakerBullseye')
            faces.extend(f.Faces)
        except Exception:
            pass
    comp = Part.Compound(faces)
    bb = comp.BoundBox
    comp.translate(V(-bb.XMin - bb.XLength / 2, 0, 0))
    comp.rotate(V(0, 0, 0), V(1, 0, 0), 90)
    comp.translate(V(xc, y0, zb))
    sols = [f.extrude(V(0, y1 - y0, 0)) for f in comp.Faces]
    out = sols[0]
    for so in sols[1:]:
        out = out.fuse(so)
    return out


def collide(shapes, allowed=(), tol=1e-3, verbose=True):
    """Paarweise Volumenpruefung (mit Bounding-Box-Vorfilter). Liefert Liste (a, b, vol)."""
    keys = list(shapes)
    hits = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            if (a, b) in allowed or (b, a) in allowed:
                continue
            A, B = shapes[a], shapes[b]
            if not A.BoundBox.intersect(B.BoundBox):
                continue
            v = A.common(B).Volume
            if v > tol:
                hits.append((a, b, v))
                if verbose:
                    print('  KOLLISION %-18s %-18s %.4f mm3' % (a, b, v))
    return hits


def export_part(shape, base, rot=None, lin=0.01, ang=0.2):
    """STEP + STL + 3MF eines Druckteils in Druckausrichtung (rot = (axis, deg) oder Liste davon), auf z = 0 gesetzt."""
    import Mesh, MeshPart
    s = shape.copy()
    for ax, deg in (rot or []):
        s.rotate(V(0, 0, 0), V(*ax), deg)
    bb = s.BoundBox
    s.translate(V(-(bb.XMin + bb.XMax) / 2, -(bb.YMin + bb.YMax) / 2, -bb.ZMin))
    s.exportStep(base + '.step')
    m = MeshPart.meshFromShape(Shape=s, LinearDeflection=lin, AngularDeflection=ang, Relative=False)
    if not m.isSolid():
        m.removeDuplicatedPoints(); m.removeDuplicatedFacets(); m.fixDegenerations(1e-4); m.harmonizeNormals()
        if not m.isSolid():
            print('WARNUNG: Netz nicht geschlossen:', base)
    m.write(base + '.stl')
    m.write(base + '.3mf')
    return s
