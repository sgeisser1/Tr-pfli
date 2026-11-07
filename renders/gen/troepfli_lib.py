"""Tröpfli Phase 3 – Bibliothek für Renderings (Blender 4.0.2, nur bpy/bmesh, alles selbst modelliert).

Einheiten: Szene in Metern; Geometrie wird in mm beschrieben und mit 0.001 skaliert (mm-genau).
Kopf-Koordinaten: x = Breite, y = Tiefe (Front = -y, Batteriedeckel = +y), z nach oben,
z = 0 an der Kopfunterkante (Dichtlinie). Sonde unterhalb (z < 0).

Gemeinsame Masse (Quelle docs/concepts/CONCEPTS.md Kap. 2A, D-006):
  Kopf 28 x 13 x 45 mm (Breite 23.1 Halter + 1 + 2 x 2 Wand; Tiefe 12 + Schraubdom; Höhe 45)
  Sonde: Leiterplatte 1.6 mm, Breite 22 mm (ANNAHME aus Platinenformat ~22 x 170 mm, Kap. 2.9/OP-K1b),
         100 mm im Boden + 5 mm freie Strecke bis zur Markierung "max".
Verwendung:  exec(open('.../troepfli_lib.py').read())  (definiert Funktionen im Namensraum)
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix

REPO = '/home/sgeisser/git/Tr-pfli'
LOGO = os.path.join(REPO, 'docs/design/logo')
OUTDIR = os.path.join(REPO, 'renders/phase3')
MM = 0.001
HEAD_D = 13.0          # Tiefe Kopf
PROBE_W = 22.0
PROBE_T = 1.6
PROBE_L = 105.0        # unter Kopf: 5 frei + 100 im Boden
GAP_SOIL = 5.0         # Kopfunterkante bis Erdoberfläche (Markierung max. Stecktiefe)

# ----------------------------------------------------------------------------- Farben
COL = {
    'weiss':      (0.86, 0.86, 0.84),
    'creme':      (0.80, 0.74, 0.62),
    'hellgrau':   (0.56, 0.58, 0.58),
    'kiesel':     (0.66, 0.66, 0.63),
    'stein':      (0.36, 0.38, 0.38),
    'wasserblau': (0.10, 0.42, 0.72),
    'salbei':     (0.36, 0.50, 0.38),
    'koralle':    (0.85, 0.30, 0.22),
    'gelb':       (0.90, 0.68, 0.10),
    'anthrazit':  (0.035, 0.04, 0.045),
}


# ----------------------------------------------------------------------------- Hilfen
def find_node(nt, typ):
    return next(n for n in nt.nodes if n.type == typ)


def sock(node, *names):
    for nm in names:
        for s in node.inputs:
            if s.identifier == nm or s.name == nm:
                return s
    raise KeyError(names)


def setin(node, val, *names):
    try:
        sock(node, *names).default_value = val
    except KeyError:
        pass


def new_mat(name):
    m = bpy.data.materials.get(name)
    if m:
        bpy.data.materials.remove(m)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m


def mat_asa(name, color, layer_lines=True, rough=0.55):
    m = new_mat(name)
    nt = m.node_tree
    p = find_node(nt, 'BSDF_PRINCIPLED')
    setin(p, (*color, 1), 'Base Color')
    setin(p, rough, 'Roughness')
    setin(p, 0.35, 'Specular IOR Level', 'Specular')
    setin(p, 0.04, 'Subsurface Weight')
    m.diffuse_color = (*color, 1)
    if layer_lines:
        # FDM-Schichtlinien 0.2 mm (Objekt-Z) als feines Bump
        tc = nt.nodes.new('ShaderNodeTexCoord')
        sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        mul = nt.nodes.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'; mul.inputs[1].default_value = 2 * math.pi / 0.0002
        sn = nt.nodes.new('ShaderNodeMath'); sn.operation = 'SINE'
        bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.12
        bump.inputs['Distance'].default_value = 0.00002
        nt.links.new(tc.outputs['Object'], sep.inputs[0])
        nt.links.new(sep.outputs['Z'], mul.inputs[0])
        nt.links.new(mul.outputs[0], sn.inputs[0])
        nt.links.new(sn.outputs[0], bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], sock(p, 'Normal'))
    return m


def mat_simple(name, color, rough=0.5, metal=0.0, spec=0.5):
    m = new_mat(name)
    p = find_node(m.node_tree, 'BSDF_PRINCIPLED')
    setin(p, (*color, 1), 'Base Color')
    setin(p, rough, 'Roughness')
    setin(p, metal, 'Metallic')
    setin(p, spec, 'Specular IOR Level', 'Specular')
    m.diffuse_color = (*color, 1)
    return m


def mat_led(name, color=(1.0, 0.08, 0.03)):
    """Lichtleiter/transluzentes Fenster (naturweisses ASA/PETG transluzent). Emission über
    m['led'] = 0/1 umschaltbar (set_led)."""
    m = new_mat(name)
    p = find_node(m.node_tree, 'BSDF_PRINCIPLED')
    setin(p, (0.9, 0.88, 0.85, 1), 'Base Color')
    setin(p, 0.35, 'Roughness')
    setin(p, 0.5, 'Transmission Weight', 'Transmission')
    setin(p, 0.3, 'Subsurface Weight')
    setin(p, (*color, 1), 'Emission Color', 'Emission')
    setin(p, 0.0, 'Emission Strength')
    m['led_color'] = color
    return m


def set_led(on, strength=6.0):
    for m in bpy.data.materials:
        if m.name.startswith('LED'):
            p = find_node(m.node_tree, 'BSDF_PRINCIPLED')
            setin(p, strength if on else 0.0, 'Emission Strength')


# ----------------------------------------------------------------------------- Geometrie
def offset_poly(pts, d):
    """Polygon (CCW) um d nach innen versetzen (Gehrung)."""
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2 = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
        e1 = (p1 - p0).normalized(); e2 = (p2 - p1).normalized()
        n1 = Vector((-e1.y, e1.x)); n2 = Vector((-e2.y, e2.x))
        k = 1.0 + n1.dot(n2)
        out.append(tuple(p1 + d * (n1 + n2) / k))
    return out


def area2(pts):
    return sum(pts[i - 1][0] * pts[i][1] - pts[i][0] * pts[i - 1][1] for i in range(len(pts))) / 2


def mesh_obj(name, bm, mat=None, parent=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if mat:
        ob.data.materials.append(mat)
    if parent:
        ob.parent = parent
    return ob


def prism(name, prof, axis, a0, a1, ch0=0.0, ch1=0.0, mat=None, parent=None, bevel=0.25):
    """Prisma aus 2D-Profil (mm). axis='y': prof=(x,z), Extrusion y a0..a1.
    axis='x': prof=(y,z), Extrusion x a0..a1. ch0/ch1 = Fasen an den Stirnseiten."""
    if area2(prof) < 0:
        prof = prof[::-1]
    rings = []
    if ch0 > 0:
        rings.append((offset_poly(prof, ch0), a0)); rings.append((prof, a0 + ch0))
    else:
        rings.append((prof, a0))
    if ch1 > 0:
        rings.append((prof, a1 - ch1)); rings.append((offset_poly(prof, ch1), a1))
    else:
        rings.append((prof, a1))

    def P(u, v, w):
        if axis == 'y':
            return Vector((u, w, v)) * MM
        if axis == 'x':
            return Vector((w, u, v)) * MM
        return Vector((u, v, w)) * MM   # axis z: prof=(x,y)

    bm = bmesh.new()
    vr = [[bm.verts.new(P(u, v, w)) for (u, v) in pts] for pts, w in rings]
    n = len(prof)
    bm.faces.new(vr[0])
    bm.faces.new(vr[-1])
    for a, b in zip(vr[:-1], vr[1:]):
        for i in range(n):
            bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = mesh_obj(name, bm, mat, parent)
    if bevel > 0:
        mod = ob.modifiers.new('Kante', 'BEVEL')
        mod.width = bevel * MM; mod.segments = 2; mod.limit_method = 'ANGLE'
        mod.angle_limit = math.radians(20)
        mod.harden_normals = False
    return ob


def box(name, x0, x1, y0, y1, z0, z1, mat=None, parent=None, bevel=0.0):
    return prism(name, [(x0, z0), (x1, z0), (x1, z1), (x0, z1)], 'y', y0, y1, mat=mat, parent=parent, bevel=bevel)


def cyl(name, r, z0, z1, center=(0, 0), axis='z', seg=48, mat=None, parent=None, bevel=0.0):
    pts = [(center[0] + r * math.cos(2 * math.pi * i / seg), center[1] + r * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
    return prism(name, pts, axis, z0, z1, mat=mat, parent=parent, bevel=bevel)


def drop_pts(cx, cz, r, h, n=20, rot=0.0):
    a = math.asin(r / h); phi = math.pi / 2 - a
    pts = [(0, h)]
    a0, a1 = math.pi - phi, 2 * math.pi + phi
    for k in range(n + 1):
        t = a0 + (a1 - a0) * k / n
        pts.append((r * math.cos(t), r * math.sin(t)))
    c, s = math.cos(rot), math.sin(rot)
    return [(cx + x * c - y * s, cz + x * s + y * c) for x, y in pts]


def facet_drop_pts(cx, cz, r, h):
    a = math.asin(r / h); phi = math.pi / 2 - a
    angs = [phi, math.radians(-10), math.radians(-55), math.radians(-90), math.radians(-125), math.radians(-170), math.pi - phi]
    pts = [(cx + r * math.cos(t), cz + r * math.sin(t)) for t in angs]
    return [(cx, cz + h)] + pts[::-1]


def cut(target, cutter, op='DIFFERENCE', solver='EXACT'):
    m = target.modifiers.new('Bool_' + cutter.name, 'BOOLEAN')
    m.object = cutter; m.operation = op; m.solver = solver
    cutter.hide_render = True; cutter.display_type = 'WIRE'
    try:
        cutter.hide_set(True)
    except Exception:
        pass
    # Boolean vor Kantenfase
    idx = len(target.modifiers) - 1
    bev = [i for i, mm in enumerate(target.modifiers) if mm.type == 'BEVEL']
    if bev and bev[0] < idx:
        target.modifiers.move(idx, bev[0])
    return m


def text_obj(name, body, size, mat, parent=None, extrude=0.12):
    cu = bpy.data.curves.new(name, 'FONT')
    cu.body = body; cu.size = size * MM; cu.extrude = extrude * MM
    cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    ob = bpy.data.objects.new(name, cu)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    if parent:
        ob.parent = parent
    return ob


def svg_obj(name, fname, width_mm, mat, parent=None, extrude=0.15):
    """SVG (docs/design/logo) importieren, zentrieren, auf Breite skalieren; liegt in XY, Normale +Z."""
    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=os.path.join(LOGO, fname))
    new = [o for o in bpy.data.objects if o not in before]
    pts = [o.matrix_world @ Vector(v) for o in new for v in o.bound_box]
    cx = (min(p.x for p in pts) + max(p.x for p in pts)) / 2
    cy = (min(p.y for p in pts) + max(p.y for p in pts)) / 2
    w = max(p.x for p in pts) - min(p.x for p in pts)
    s = width_mm * MM / w
    for o in new:
        o.data.transform(Matrix.Translation(Vector((-cx, -cy, 0))))
        o.data.transform(Matrix.Scale(s, 4))
        o.location = (0, 0, 0)
        o.data.extrude = extrude * MM
        o.data.materials.clear(); o.data.materials.append(mat)
        for c in list(o.users_collection):
            c.objects.unlink(o)
        bpy.context.scene.collection.objects.link(o)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    for o in new:
        o.parent = root
    if parent:
        root.parent = parent
    return root, w * s / MM


def place(ob, loc_mm, rot_deg=(0, 0, 0)):
    ob.location = Vector(loc_mm) * MM
    ob.rotation_euler = [math.radians(a) for a in rot_deg]


def on_front_xz(ob, x, y, z, tilt=0.0):
    """Flaches Objekt (Normale +Z) auf eine Frontfläche (Normale -Y) setzen; tilt = Neigung der Fläche
    nach hinten (Grad, 0 = senkrecht)."""
    place(ob, (x, y, z), (90 - tilt, 0, 0))


def on_back_xz(ob, x, y, z):
    place(ob, (x, y, z), (90, 0, 180))


# ----------------------------------------------------------------------------- Sonde und Deckel
def probe(root, mats):
    prof = [(-PROBE_W / 2, 0), (PROBE_W / 2, 0), (PROBE_W / 2, -PROBE_L + 9), (3.0, -PROBE_L),
            (-3.0, -PROBE_L), (-PROBE_W / 2, -PROBE_L + 9)]
    prism('Sonde', prof, 'y', -PROBE_T / 2, PROBE_T / 2, mat=mats['pcb'], parent=root, bevel=0.15)
    # Dichtwulst (Epoxid/Silikon) an der Dichtlinie
    box('Dichtung', -PROBE_W / 2 - 1.0, PROBE_W / 2 + 1.0, -2.2, 2.2, -1.2, 0.2, mats['seal'], root, bevel=0.5)
    # Markierung max. Stecktiefe (Silkscreen) auf beiden Seiten
    for sgn, nm in ((-1, 'MarkV'), (1, 'MarkH')):
        box(nm, -PROBE_W / 2 + 1.0, PROBE_W / 2 - 1.0, sgn * (PROBE_T / 2) - 0.02, sgn * (PROBE_T / 2) + 0.02,
            -GAP_SOIL - 0.25, -GAP_SOIL + 0.25, mats['silk'], root)
    t = text_obj('MaxText', 'max', 1.6, mats['silk'], root, extrude=0.02)
    on_front_xz(t, -6.0, -PROBE_T / 2 - 0.03, -GAP_SOIL + 1.6)
    prism('MaxPfeil', [(-10.2, -GAP_SOIL + 2.4), (-7.8, -GAP_SOIL + 2.4), (-9.0, -GAP_SOIL + 0.6)], 'y',
          -PROBE_T / 2 - 0.04, -PROBE_T / 2, mat=mats['silk'], parent=root, bevel=0)
    t3 = text_obj('Rev', 'troepfli rev A', 1.2, mats['silk'], root, extrude=0.02)
    on_front_xz(t3, 2.0, -PROBE_T / 2 - 0.03, -GAP_SOIL + 1.6)


def battery_lid(body, root, mats, x0, x1, z0, z1, yb, screw_z, cham=1.2):
    """Batteriedeckel auf der Rückseite (+y). yb = Rückfläche. Fuge 0.4 mm, Tiefe 0.8 mm.
    Unverlierbare Schraube M2 (Senkkopf) unten, weit weg von der Antenne (oben)."""
    def octo(xa, xb, za, zb, c):
        return [(xa + c, za), (xb - c, za), (xb, za + c), (xb, zb - c), (xb - c, zb), (xa + c, zb), (xa, zb - c), (xa, za + c)]
    pocket = prism('DeckelTasche', octo(x0, x1, z0, z1, cham), 'y', yb - 0.8, yb + 1.0, mat=None, parent=root, bevel=0)
    cut(body, pocket)
    lid = prism('Batteriedeckel', octo(x0 + 0.4, x1 - 0.4, z0 + 0.4, z1 - 0.4, cham * 0.8), 'y', yb - 0.8, yb,
                0, 0.25, mat=body.data.materials[0], parent=root, bevel=0.1)
    # Schraube (Senkkopf, Edelstahl) unverlierbar
    sk = cyl('Schraubenkopf', 1.9, yb - 0.3, yb - 0.02, center=(0, screw_z), axis='y', mat=mats['steel'], parent=root, bevel=0.1)
    for i, ang in enumerate((0, 90)):
        k = box('Kreuz%d' % i, -1.1, 1.1, yb - 0.6, yb + 0.2, screw_z - 0.25, screw_z + 0.25, None, root)
        k.rotation_euler = (0, math.radians(ang), 0)
        k.location = Vector((0, 0, 0))
        # Kreuz um Schraubenachse drehen: Kreuzbalken als Boolean in Schraubenkopf
        k.data.transform(Matrix.Translation(Vector((0, 0, -screw_z * MM))))
        k.data.transform(Matrix.Rotation(math.radians(ang), 4, 'Y'))
        k.data.transform(Matrix.Translation(Vector((0, 0, screw_z * MM))))
        k.rotation_euler = (0, 0, 0)
        cut(sk, k)
    # Warnsymbol (IEC 60086-4 sinngemäss: "Von Kindern fernhalten"), hier vereinfacht als
    # Warndreieck + Zellenbezeichnung; endgültiges Symbol in Phase 4 (REQ-SAF-CC-04)
    zc = (z0 + z1) / 2 + 3.5
    tri = prism('Warndreieck', [(-3.2, zc - 2.6), (3.2, zc - 2.6), (0, zc + 3.0)], 'y', yb - 0.02, yb + 0.12,
                mat=mats['warn'], parent=root, bevel=0)
    tri_in = prism('WarnInnen', offset_poly([(-3.2, zc - 2.6), (3.2, zc - 2.6), (0, zc + 3.0)], 0.7), 'y',
                   yb - 0.1, yb + 0.3, parent=root, bevel=0)
    cut(tri, tri_in)
    ex = text_obj('WarnAusruf', '!', 3.4, mats['warn'], root, extrude=0.07)
    on_back_xz(ex, 0, yb + 0.05, zc - 0.6)
    t = text_obj('CR2032', 'CR2032 3V', 1.9, mats['warn'], root, extrude=0.07)
    on_back_xz(t, 0, yb + 0.05, zc - 5.6)
    return lid


# ----------------------------------------------------------------------------- Designs
def shared(name, fn):
    return bpy.data.materials.get(name) or fn(name)


def base_mats(design, cw):
    mats = {
        'body': shared(f'{design}_Koerper', lambda n: mat_asa(n, COL[cw[0]])),
        'acc': shared(f'{design}_Akzent', lambda n: mat_asa(n, COL[cw[1]])),
        'led': shared(f'LED_{design}', mat_led),
        'pcb': shared('Sonde_Loetstopp', lambda n: mat_simple(n, (0.02, 0.16, 0.06), rough=0.25, spec=0.6)),
        'silk': shared('Silkscreen', lambda n: mat_simple(n, (0.85, 0.85, 0.82), rough=0.6)),
        'seal': shared('Dichtmasse', lambda n: mat_simple(n, (0.05, 0.05, 0.055), rough=0.35)),
        'steel': shared('Edelstahl', lambda n: mat_simple(n, (0.62, 0.62, 0.6), rough=0.28, metal=1.0)),
        'warn': shared(f'{design}_Warn', lambda n: mat_asa(n, COL['anthrazit'], layer_lines=False)),
        'logo': shared(f'{design}_Logo', lambda n: mat_asa(n, COL[cw[2]] if len(cw) > 2 else COL[cw[1]], layer_lines=False)),
    }
    return mats


def head_p1(cw=('weiss', 'wasserblau')):
    """P1 Facette: facettierter Tropfen, oben gekappt; Taster oben (axial), LED-Tropfen vorne oben."""
    root = bpy.data.objects.new('P1_Facette', None); bpy.context.scene.collection.objects.link(root)
    mats = base_mats('P1', cw)
    # Oberkante 19 mm breit: Innenbreite bei z = 40.7 (Oberkante Antenne AN043, 15.2 x 5.7 mm) >= 17 mm
    prof = [(-10, 0), (10, 0), (14, 4), (14, 26), (9.5, 45), (-9.5, 45), (-14, 26), (-14, 4)]
    body = prism('P1_Koerper', prof, 'y', -6.5, 6.5, 3.0, 0.8, mats['body'], root, bevel=0.3)
    # Taster oben: Bohrung + Taste (Akzent), 0.6 mm über Fläche
    hole = cyl('P1_TastLoch', 3.9, 42.5, 47, center=(0, 1.2), axis='z', parent=root)
    cut(body, hole)
    cyl('P1_Taste', 3.5, 42.6, 45.6, center=(0, 1.2), axis='z', mat=mats['acc'], parent=root, bevel=0.3)
    # LED-Tropfen auf Frontfläche
    dp = drop_pts(0, 34.0, 2.1, 4.8)
    lc = prism('P1_LEDLoch', dp, 'y', -7, -4.5, parent=root, bevel=0)
    cut(body, lc)
    prism('P1_LED', dp, 'y', -6.45, -4.6, 0, 0.0, mats['led'], root, bevel=0.2)
    lg, _ = svg_obj('P1_Logo', 'logo_v1_schlicht_mono.svg', 15.0, mats['logo'], root)
    on_front_xz(lg, 0, -6.5, 14.0)
    battery_lid(body, root, mats, -11.5, 11.5, 2.0, 27.5, 6.5, 4.6)
    probe(root, mats)
    return root


def head_p2(cw=('creme', 'salbei')):
    """P2 Keil: Quader mit nach vorn geneigter Dachfläche (34°); LED-Tropfen + Taste auf der Schräge,
    Schräge in Akzentfarbe (AMS-Farbwechsel nur in den obersten Schichten)."""
    root = bpy.data.objects.new('P2_Keil', None); bpy.context.scene.collection.objects.link(root)
    mats = base_mats('P2', cw)
    zf, zb = 42.0, 48.0     # Front-/Rückhöhe (Dach innen über Leiterplatte >= 43 mm für Antenne)
    y0, y1 = -6.5, 6.5
    # Körper bis knapp unter die Dachplatte (Akzent 2 mm dick, senkrecht gemessen)
    off = 2.0 / math.cos(math.atan((zb - zf) / (y1 - y0)))
    prof_body = [(y0, 0), (y1, 0), (y1, zb - off), (y0, zf - off)]
    prof_cap = [(y0, zf - off), (y1, zb - off), (y1, zb), (y0, zf)]
    # Profil in (y,z), Extrusion in x; Fasen der senkrechten Kanten über Profil-Fase realisiert
    body = prism('P2_Koerper', chamfer_profile(prof_body, [], 0), 'x', -14, 14, 1.2, 1.2, mats['body'], root, bevel=0.3)
    cap = prism('P2_Dach', chamfer_profile(prof_cap, [], 0), 'x', -14, 14, 1.2, 1.2, mats['acc'], root, bevel=0.3)
    slope = math.degrees(math.atan((zb - zf) / (y1 - y0)))
    # Punkte auf der Dachfläche: y -> z
    def zroof(y):
        return zf + (zb - zf) * (y - y0) / (y1 - y0)
    # LED-Tropfen vorn auf der Schräge (Normalenrichtung)
    n = Vector((0, -math.sin(math.radians(slope)), math.cos(math.radians(slope))))
    for nm, yy, kind in (('LED', -3.2, 'led'), ('Taste', 2.6, 'btn')):
        zz = zroof(yy)
        if kind == 'led':
            shape = drop_pts(0, 0, 1.9, 4.2)
            shape = [(x, z - 1.2) for x, z in shape]
            hole = prism(f'P2_{nm}Loch', shape, 'z', -2.5, 3, parent=root, bevel=0)
            obj = prism(f'P2_{nm}', shape, 'z', -2.4, 0.05, mat=mats['led'], parent=root, bevel=0.2)
        else:
            sh = [(-5, -1.9), (5, -1.9), (5, 1.9), (-5, 1.9)]
            hole = prism(f'P2_{nm}Loch', offset_poly(sh, -0.4), 'z', -2.5, 3, parent=root, bevel=0)
            obj = prism(f'P2_{nm}', sh, 'z', -2.4, 0.5, mat=mats['body'], parent=root, bevel=0.4)
        for o in (hole, obj):
            # lokales z = Dachnormale; Tropfenspitze zeigt nach hinten-oben
            o.rotation_euler = (math.radians(slope), 0, 0)
            o.location = Vector((0, yy, zz)) * MM
        cut(cap, hole, solver='FAST')
    lg, _ = svg_obj('P2_Logo', 'logo_v1_schlicht_mono.svg', 16.0, mats['logo'], root)
    on_front_xz(lg, 0, y0, 17.0)
    battery_lid(body, root, mats, -11.5, 11.5, 2.0, 27.5, y1, 4.6)
    probe(root, mats)
    return root


def chamfer_profile(prof, idx, c):
    """Ecken idx eines Polygons um c anfasen (für senkrechte Kanten bei axis='x' nicht nötig)."""
    if not idx or c <= 0:
        return prof
    out = []
    n = len(prof)
    for i, p in enumerate(prof):
        if i in idx:
            a = Vector(prof[i - 1]); b = Vector(p); d = Vector(prof[(i + 1) % n])
            out.append(tuple(b + (a - b).normalized() * c)); out.append(tuple(b + (d - b).normalized() * c))
        else:
            out.append(p)
    return out


def head_p3(cw=('weiss', 'wasserblau')):
    """P3 Stele: schlanker Quader 28 x 12 x 45, harte Fasen; obere 11 mm als Farbband ("Wasserstand"),
    grosses LED-Tropfenfenster auf der Bandkante, quadratische Taste oben."""
    root = bpy.data.objects.new('P3_Stele', None); bpy.context.scene.collection.objects.link(root)
    mats = base_mats('P3', cw)
    D = 12.0
    zs = 34.0
    def oct_xz(x0, x1, z0, z1, c):
        return [(x0 + c, z0), (x1 - c, z0), (x1, z0 + c), (x1, z1 - c), (x1 - c, z1), (x0 + c, z1), (x0, z1 - c), (x0, z0 + c)]
    # Grundriss (x,y) mit Fasen 2.5 vorne, 1.0 hinten, als Prisma entlang z
    plan = [(-14 + 2.5, -D / 2), (14 - 2.5, -D / 2), (14, -D / 2 + 2.5), (14, D / 2 - 1.0), (14 - 1.0, D / 2),
            (-14 + 1.0, D / 2), (-14, D / 2 - 1.0), (-14, -D / 2 + 2.5)]
    body = prism('P3_Koerper', plan, 'z', 0, zs, 0.6, 0.0, mats['body'], root, bevel=0.3)
    band = prism('P3_Band', plan, 'z', zs, 45, 0.0, 1.0, mats['acc'], root, bevel=0.3)
    # Taste oben quadratisch mit Fase
    sq = oct_xz(-4.5, 4.5, -2.6, 3.4, 1.0)
    hole = prism('P3_TastLoch', offset_poly(sq, -0.4), 'z', 42.5, 47, parent=root, bevel=0)
    cut(band, hole)
    prism('P3_Taste', sq, 'z', 42.6, 45.6, 0, 0.6, mats['body'], root, bevel=0.2)
    # LED-Tropfen, halb im Band, halb im Körper -> verspielt
    dp = drop_pts(0, 32.2, 2.6, 5.8)
    lc = prism('P3_LEDLoch', dp, 'y', -7, -3.5, parent=root, bevel=0)
    cut(body, lc)
    lc2 = prism('P3_LEDLoch2', dp, 'y', -7, -3.5, parent=root, bevel=0)
    cut(band, lc2)
    prism('P3_LED', dp, 'y', -5.95, -3.6, 0, 0, mats['led'], root, bevel=0.25)
    lg, _ = svg_obj('P3_Logo', 'logo_v2_tropfen_mono.svg', 16.0, mats['logo'], root)
    on_front_xz(lg, 0, -D / 2, 13.0)
    battery_lid(body, root, mats, -11.5, 11.5, 2.0, 27.5, D / 2, 4.6)
    probe(root, mats)
    return root


def head_p4(cw=('stein', 'weiss')):
    """P4 Gipfel: asymmetrischer Berg; Gipfelkappe ("Schnee") ist der Lichtleiter der LED
    (Alpenglühen), Taste auf der flachen Schulter (axial)."""
    root = bpy.data.objects.new('P4_Gipfel', None); bpy.context.scene.collection.objects.link(root)
    mats = base_mats('P4', cw)
    # Schulter 43 mm (darunter volle Innenbreite für Antenne AN043 bis z = 40.7), Gipfel (6, 49):
    # der Gipfel ist reine Kunststoff-Sperrzone über der Antenne und zugleich Lichtleiter der LED.
    # Schneegrenze als Zickzack; Punkte liegen auf den Flanken (14,40)-(6,49) und (6,49)-(0,43).
    snow = [(10.0, 44.5), (8.9, 43.6), (7.6, 44.9), (6.0, 43.7), (4.6, 44.8), (1.5, 44.5)]
    prof = [(-14, 0), (14, 0), (14, 40), *snow, (0, 43), (-14, 43)]
    body = prism('P4_Koerper', prof, 'y', -6.5, 6.5, 1.6, 0.8, mats['body'], root, bevel=0.3)
    cap_prof = snow[::-1] + [(6.0, 49.0)]
    # Kappe aus transluzentem Material = LED-Lichtleiter ("Alpenglühen")
    prism('P4_LED_Kappe', cap_prof, 'y', -6.5, 6.5, 1.6, 0.8, mats['led'], root, bevel=0.25)
    hole = cyl('P4_TastLoch', 3.9, 40.5, 46, center=(-7.0, 0.3), axis='z', parent=root)
    cut(body, hole)
    cyl('P4_Taste', 3.5, 40.6, 43.6, center=(-7.0, 0.3), axis='z', mat=mats['acc'], parent=root, bevel=0.3)
    lg, _ = svg_obj('P4_Logo', 'logo_v1_schlicht_mono.svg', 15.0, mats['logo'], root)
    on_front_xz(lg, 0, -6.5, 13.0)
    battery_lid(body, root, mats, -11.5, 11.5, 2.0, 27.5, 6.5, 4.6)
    probe(root, mats)
    return root


HEADS = {'p1': head_p1, 'p2': head_p2, 'p3': head_p3, 'p4': head_p4}


# ----------------------------------------------------------------------------- Gateway
def gateway_g1(cw=('weiss', 'wasserblau')):
    """G1 Sockel: 62 x 40 x 20 mm, facettierte Kanten wie P1/P3, schräge Frontfacette mit LED-Tropfen
    und Wortmarke, Stabantenne (2.4 GHz, U.FL->Pigtail) hinten rechts, USB-C hinten.
    Innen: XIAO ESP32-S3 Plus 21 x 17.8 mm + RTC-Modul (ANNAHME 15 x 12 mm) nebeneinander."""
    root = bpy.data.objects.new('G1_Sockel', None); bpy.context.scene.collection.objects.link(root)
    mats = base_mats('G1', cw)
    W, D, H = 62.0, 40.0, 20.0
    # Seitenprofil (y,z): Front-Facette 45° oben vorn
    prof = [(-D / 2, 0), (D / 2, 0), (D / 2, H), (-D / 2 + 9, H), (-D / 2, H - 9)]
    body = prism('G1_Koerper', prof, 'x', -W / 2, W / 2, 3.0, 3.0, mats['body'], root, bevel=0.4)
    # LED-Tropfen auf der Facette
    ang = 45.0
    yy, zz = -D / 2 + 4.5, H - 4.5
    dp = drop_pts(0, -0.8, 2.2, 5.0)
    hole = prism('G1_LEDLoch', dp, 'z', -2.5, 3, parent=root, bevel=0)
    led = prism('G1_LED', dp, 'z', -2.4, 0.05, mat=mats['led'], parent=root, bevel=0.2)
    for o in (hole, led):
        o.rotation_euler = (math.radians(ang), 0, 0)
        o.location = Vector((20.0, yy, zz)) * MM
    cut(body, hole)
    lg, _ = svg_obj('G1_Logo', 'logo_v1_schlicht_mono.svg', 22.0, mats['logo'], root)
    place(lg, (-8.0, yy - 0.02, zz + 0.02), (90 - ang, 0, 0))
    # Gummifüsse
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f'G1_Fuss{sx}{sy}', 3.0, -0.8, 0.2, center=(sx * 24, sy * 14), axis='z', mat=mats['seal'], parent=root, bevel=0.3)
    antenna(root, mats, (W / 2 - 9, D / 2 - 7, H))
    usb_c(root, mats, (-14, D / 2, 7))
    return root


def gateway_g2(cw=('stein', 'weiss')):
    """G2 Gipfel: kleines Bergmassiv 64 x 38 x 36 mm (Gipfelkappe = LED-Lichtleiter), Antenne als
    'Gipfelkreuz-Stab' hinten. Passt zu P4."""
    root = bpy.data.objects.new('G2_Gipfel', None); bpy.context.scene.collection.objects.link(root)
    mats = base_mats('G2', cw)
    snow = [(15.6, 29.0), (12.5, 27.5), (9.5, 29.6), (6.3, 27.4), (3.2, 29.2), (0.0, 29.0)]
    prof = [(-32, 0), (32, 0), (32, 14), *snow, (-8, 22), (-32, 22)]
    body = prism('G2_Koerper', prof, 'y', -19, 19, 3.0, 1.5, mats['body'], root, bevel=0.4)
    capp = snow[::-1] + [(8.0, 36.0)]
    prism('G2_LED_Kappe', capp, 'y', -19, 19, 3.0, 1.5, mats['led'], root, bevel=0.3)
    lg, _ = svg_obj('G2_Logo', 'logo_v1_schlicht_mono.svg', 22.0, mats['logo'], root)
    on_front_xz(lg, -14.0, -19.0, 9.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f'G2_Fuss{sx}{sy}', 3.0, -0.8, 0.2, center=(sx * 25, sy * 13), axis='z', mat=mats['seal'], parent=root, bevel=0.3)
    antenna(root, mats, (-24, 10, 22))
    usb_c(root, mats, (16, 19, 6))
    return root


def antenna(root, mats, base):
    x, y, z = base
    cyl('Ant_Fuss', 4.2, z, z + 6, center=(x, y), axis='z', mat=mats['seal'], parent=root, bevel=0.5)
    cyl('Ant_Stab', 3.6, z + 6, z + 58, center=(x, y), axis='z', mat=mats['seal'], parent=root, bevel=1.2)


def usb_c(root, mats, pos):
    x, y, z = pos
    # Buchse in Rückwand (8.9 x 3.2 mm Öffnung), Stecker + Kabel nur angedeutet
    st = box('USB_Stecker', x - 6, x + 6, y, y + 16, z - 3.5, z + 3.5, mats['seal'], root, bevel=1.2)
    cu = bpy.data.curves.new('USB_Kabel', 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('BEZIER'); pts = [(x, y + 16, z), (x, y + 32, z - 3), (x + 6, y + 50, 1.9), (x + 20, y + 160, 1.9)]
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = Vector(p) * MM; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    cu.bevel_depth = 1.9 * MM; cu.bevel_resolution = 3
    ob = bpy.data.objects.new('USB_Kabel', cu); bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mats['seal']); ob.parent = root
    return st


# ----------------------------------------------------------------------------- Umgebung
def env_mats():
    m = {}
    # Holz hell (Eiche) prozedural
    w = new_mat('Tisch_Eiche')
    nt = w.node_tree; p = find_node(nt, 'BSDF_PRINCIPLED')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (4, 60, 4)
    wave = nt.nodes.new('ShaderNodeTexNoise'); wave.inputs['Scale'].default_value = 6; wave.inputs['Detail'].default_value = 8
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.62, 0.45, 0.30, 1); ramp.color_ramp.elements[1].color = (0.78, 0.62, 0.44, 1)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector']); nt.links.new(mp.outputs[0], wave.inputs['Vector'])
    nt.links.new(wave.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], sock(p, 'Base Color'))
    setin(p, 0.45, 'Roughness')
    m['wood'] = w
    m['wall'] = mat_simple('Wand', (0.80, 0.80, 0.78), rough=0.9, spec=0.2)
    # Terracotta
    t = new_mat('Terracotta'); nt = t.node_tree; p = find_node(nt, 'BSDF_PRINCIPLED')
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 400
    rp = nt.nodes.new('ShaderNodeValToRGB')
    rp.color_ramp.elements[0].color = (0.45, 0.17, 0.08, 1); rp.color_ramp.elements[1].color = (0.62, 0.27, 0.14, 1)
    nt.links.new(nz.outputs['Fac'], rp.inputs['Fac']); nt.links.new(rp.outputs['Color'], sock(p, 'Base Color'))
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.15
    nt.links.new(nz.outputs['Fac'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], sock(p, 'Normal'))
    setin(p, 0.85, 'Roughness')
    m['pot'] = t
    # Erde mit Perlite-Körnern
    s = new_mat('Erde'); nt = s.node_tree; p = find_node(nt, 'BSDF_PRINCIPLED')
    vo = nt.nodes.new('ShaderNodeTexVoronoi'); vo.inputs['Scale'].default_value = 900
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1500; nz.inputs['Detail'].default_value = 6
    rp = nt.nodes.new('ShaderNodeValToRGB')
    rp.color_ramp.elements[0].color = (0.035, 0.022, 0.014, 1); rp.color_ramp.elements[1].color = (0.11, 0.07, 0.045, 1)
    nt.links.new(nz.outputs['Fac'], rp.inputs['Fac'])
    vo2 = nt.nodes.new('ShaderNodeTexVoronoi'); vo2.inputs['Scale'].default_value = 260
    cr = nt.nodes.new('ShaderNodeMath'); cr.operation = 'LESS_THAN'; cr.inputs[1].default_value = 0.08
    nt.links.new(vo2.outputs['Distance'], cr.inputs[0])
    mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
    nt.links.new(cr.outputs[0], mix.inputs['Factor'])
    nt.links.new(rp.outputs['Color'], mix.inputs[6]); mix.inputs[7].default_value = (0.75, 0.74, 0.70, 1)
    nt.links.new(mix.outputs[2], sock(p, 'Base Color'))
    bp = nt.nodes.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6
    nt.links.new(vo.outputs['Distance'], bp.inputs['Height']); nt.links.new(bp.outputs['Normal'], sock(p, 'Normal'))
    setin(p, 0.95, 'Roughness'); setin(p, 0.2, 'Specular IOR Level', 'Specular')
    m['soil'] = s
    m['leaf'] = mat_simple('Blatt', (0.07, 0.26, 0.05), rough=0.38, spec=0.5)
    lp = find_node(m['leaf'].node_tree, 'BSDF_PRINCIPLED')
    setin(lp, 0.15, 'Subsurface Weight'); setin(lp, (0.1, 0.4, 0.05, 1), 'Subsurface Color')
    m['stem'] = mat_simple('Stiel', (0.25, 0.42, 0.12), rough=0.5)
    return m


def clear_scene():
    sc = bpy.context.scene
    for o in list(sc.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights, bpy.data.materials):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)


def room(m):
    box('Tisch', -600, 600, -400, 400, -25, 0, m['wood'])
    w = box('Wand', -800, 800, 330, 345, -25, 900, m['wall'])
    # Fensterlicht (gross, weich) von links hinten, Aufhellung rechts
    L = bpy.data.lights.new('Fenster', 'AREA'); L.shape = 'RECTANGLE'; L.size = 0.9; L.size_y = 1.1; L.energy = 45
    L.color = (1.0, 0.97, 0.93)
    lo = bpy.data.objects.new('Fenster', L); bpy.context.scene.collection.objects.link(lo)
    lo.location = (-0.75, -0.25, 0.55); lo.rotation_euler = Vector((0, 0, 0)).to_track_quat('Z', 'Y').to_euler()
    lo.rotation_euler = (Vector((0.0, 0.0, 0.08)) - lo.location).to_track_quat('-Z', 'Y').to_euler()
    F = bpy.data.lights.new('Aufheller', 'AREA'); F.size = 0.8; F.energy = 8; F.color = (0.92, 0.95, 1.0)
    fo = bpy.data.objects.new('Aufheller', F); bpy.context.scene.collection.objects.link(fo)
    fo.location = (0.7, -0.6, 0.45)
    fo.rotation_euler = (Vector((0.0, 0.0, 0.05)) - fo.location).to_track_quat('-Z', 'Y').to_euler()
    wd = bpy.context.scene.world or bpy.data.worlds.new('Welt')
    bpy.context.scene.world = wd
    wd.use_nodes = True
    bg = find_node(wd.node_tree, 'BACKGROUND')
    bg.inputs[0].default_value = (0.78, 0.82, 0.88, 1); bg.inputs[1].default_value = 0.18


def pot(m, loc=(0, 0), r_top=67.0, r_bot=52.0, h=125.0, soil_z=115.0):
    """Terracotta-Topf (mm), Erde bei soil_z. Liefert Erdhöhe."""
    x, y = loc
    bm = bmesh.new()
    seg = 96
    rings = [(r_bot, 0), (r_top, h - 8), (r_top + 3.5, h - 8), (r_top + 3.5, h), (r_top - 3.0, h), (r_top - 7.0, 10), (0, 10)]
    vs = []
    for r, z in rings:
        ring = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            ring.append(bm.verts.new(Vector((x + r * math.cos(a), y + r * math.sin(a), z)) * MM))
        vs.append(ring)
    for a, b in zip(vs[:-1], vs[1:]):
        for i in range(seg):
            bm.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    bm.faces.new(vs[0][::-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    po = mesh_obj('Topf', bm, m['pot'])
    sm = po.modifiers.new('Glatt', 'BEVEL'); sm.width = 0.0012; sm.segments = 3; sm.limit_method = 'ANGLE'
    for f in po.data.polygons:
        f.use_smooth = True
    # Erde: Scheibe mit leichtem Relief
    rs = r_top - 3.0 - (r_top - 7.0 - (r_top - 3.0)) * 0  # innen
    rr = (r_top - 7.0) + ((r_top - 3.0) - (r_top - 7.0)) * (soil_z - 10) / (h - 10)
    bm = bmesh.new()
    rnd = random.Random(7)
    res = bmesh.ops.create_circle(bm, cap_ends=True, segments=128, radius=rr * MM)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    for _ in range(3):
        bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=1, use_grid_fill=True)
    for v in bm.verts:
        rad = v.co.length / (rr * MM)
        v.co.z = (soil_z + rnd.uniform(-0.7, 0.7) + 1.5 * (1 - rad ** 4) - 1.2) * MM
        v.co.x += x * MM; v.co.y += y * MM
    so = mesh_obj('Erde', bm, m['soil'])
    for f in so.data.polygons:
        f.use_smooth = True
    return soil_z


def pilea(m, base=(0, 0, 115), seed=3, n_leaves=13, scale=1.0):
    """Ufopflanze (Pilea peperomioides), einfach modelliert: Stamm, Blattstiele, schildförmige Blätter."""
    rnd = random.Random(seed)
    bx, by, bz = base

    def tube(name, pts, r, mat):
        cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
        sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts) - 1)
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = Vector(p) * MM; bp.handle_left_type = bp.handle_right_type = 'AUTO'
        cu.bevel_depth = r * MM; cu.bevel_resolution = 3; cu.use_fill_caps = True
        ob = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(mat)
        return ob

    H = 75 * scale
    tube('Stamm', [(bx, by, bz - 5), (bx + 2, by + 1, bz + H * 0.5), (bx + 1, by - 1, bz + H)], 3.2 * scale, m['stem'])
    golden = math.radians(137.5)
    for i in range(n_leaves):
        t = (i + 1) / (n_leaves + 1)
        sz = bz + H * (0.25 + 0.75 * t)
        az = i * golden + rnd.uniform(-0.2, 0.2)
        L = (95 - 55 * t) * scale * rnd.uniform(0.85, 1.1)
        rise = (25 + 40 * t) * scale
        ex, ey = bx + L * math.cos(az), by + L * math.sin(az)
        ez = sz + rise * rnd.uniform(0.6, 1.0)
        mid = (bx + 0.45 * L * math.cos(az), by + 0.45 * L * math.sin(az), sz + rise * 0.9)
        tube(f'Stiel{i}', [(bx, by, sz), mid, (ex, ey, ez)], 1.1 * scale, m['stem'])
        R = (26 + 14 * (1 - t)) * scale * rnd.uniform(0.85, 1.1)
        bm = bmesh.new()
        bmesh.ops.create_circle(bm, cap_ends=True, segments=40, radius=R * MM)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges, cuts=2, use_grid_fill=True)
        for v in bm.verts:
            r = v.co.length / (R * MM)
            v.co.z = (0.18 * R * r * r) * MM
        lf = mesh_obj(f'Blatt{i}', bm, m['leaf'])
        so = lf.modifiers.new('Dicke', 'SOLIDIFY'); so.thickness = 0.5 * MM
        for f in lf.data.polygons:
            f.use_smooth = True
        tilt = math.radians(rnd.uniform(15, 40))
        lf.rotation_euler = (0, 0, 0)
        lf.location = Vector((ex, ey, ez)) * MM
        # Blatt nach aussen kippen
        axis = Vector((-math.sin(az), math.cos(az), 0))
        lf.rotation_mode = 'QUATERNION'
        from mathutils import Quaternion
        lf.rotation_quaternion = Quaternion(axis, tilt)


def camera(name, loc_m, target_m, lens=50, fstop=None, focus_m=None):
    cam = bpy.data.cameras.new(name); cam.lens = lens; cam.sensor_width = 36
    ob = bpy.data.objects.new(name, cam); bpy.context.scene.collection.objects.link(ob)
    ob.location = Vector(loc_m)
    ob.rotation_euler = (Vector(target_m) - Vector(loc_m)).to_track_quat('-Z', 'Y').to_euler()
    if fstop:
        cam.dof.use_dof = True; cam.dof.aperture_fstop = fstop
        cam.dof.focus_distance = focus_m or (Vector(target_m) - Vector(loc_m)).length
    return ob


def render_settings(res=(1600, 1200), samples=384):
    sc = bpy.context.scene
    try:
        sc.render.engine = 'CYCLES'
    except TypeError as e:
        print('Engine', e)
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.015
    sc.cycles.use_denoising = False
    sc.cycles.max_bounces = 8
    sc.cycles.transmission_bounces = 6
    sc.cycles.blur_glossy = 1.0
    sc.cycles.sample_clamp_indirect = 2.0
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.view_settings.view_transform = 'AgX' if 'AgX' in [i.identifier for i in type(sc.view_settings).bl_rna.properties['view_transform'].enum_items] else 'Filmic'
    try:
        sc.view_settings.look = 'Medium High Contrast'
    except TypeError:
        sc.view_settings.look = 'None'
    sc.view_settings.exposure = -0.6
    sc.unit_settings.system = 'METRIC'; sc.unit_settings.length_unit = 'MILLIMETERS'


def render_to(path, cam):
    sc = bpy.context.scene
    sc.camera = cam
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path
