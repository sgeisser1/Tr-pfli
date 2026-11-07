"""fluidi Phase 3, Verfeinerung 1 – P3 "Stele" mit Hülsen-Batteriewechsel (Konstruktion A1), Gateway G1 in
Grau + Hellblau. Blender 4.0.2, nur bpy/bmesh, alles selbst modelliert. Baut auf fluidi_lib.py und
render_phase3.py auf (Materialien, Umgebung, Kamera, Rendereinstellungen).

Masse (Quelle docs/reviews/phase3_sleeve_mechanik.md, Kap. 1 A1, Variante 28/20; Modell
mechanical/gen/p3_sleeve_concept.py, build(28, 20)):
  Kopf 28 x 13 x 48 mm, Grundriss mit Fasen vorne 2.5 / hinten 1.0 mm
  Hülse grau z 0 ... 36.7 (Wand 1.6, Boden 2.2), Sichtfuge 0.3 mm, Kappe blau z 37 ... 48
  Sonde (Leiterplatte) 20 x 1.6 mm, liegt bei y_mech 4.6 ... 6.2 (hier y -1.9 ... -0.3, Front = -6.5)
  Sondenschlitz im Boden 20.6 x 2.2; Schraube M2 x 4 bei y_mech 9.0 (hier y +2.5), Kopf D 3.8 x 1.2 in Senkung D 4.4
  Kragen z 2.8 ... 6.0, Bodendichtung z 2.2 ... 2.8, CR2032 in Keystone 3034 (gedreht, Ausschub +x),
  Zellmitte z 17.95, Clip z 6.4 ... 29.5, Schott z 29.8 ... 31.3, O-Ring-Nut z 31.5 ... 33.5 (Schnur 1.5)
  LED-Tropfenfenster (transluzent, in die Kappe eingeklebt): r 2.5, Spitze 6.0 über Mitte, Mitte z 37.4
  -> Unterkante z 34.9, Kerbe in der Hülse 0.3 mm grösser (Unterkante 34.6 = 1.1 mm über der O-Ring-Nut,
  Forderung Mechanikbericht Kap. 2.1 ">= 1 mm").
  Taste oben 9 x 6 mm (Fase 1.0), hellblau, Spalt 0.4, 0.6 mm über der Decke.
Koordinaten wie fluidi_lib: x Breite, y Tiefe (Front = -y), z hoch, z = 0 Kopfunterkante, Meter-Szene, mm-Geometrie.
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix

exec(open('/home/sgeisser/git/Tr-pfli/renders/gen/render_phase3.py').read())

OUT2 = os.path.join(REPO, 'renders/phase3_v2')
W3, D3, H3 = 28.0, 13.0, 48.0
Z_FUGE, GAP_F = 37.0, 0.3
WALL, FLOOR = 1.6, 2.2
PW = 20.0                         # Sondenbreite Variante 28/20
PCB_Y0, PCB_Y1 = -1.9, -0.3       # y_mech 4.6 ... 6.2
SCREW_Y = 2.5
Z_CELL = 17.95
LED_R, LED_K, LED_Z = 2.5, 2.4, 37.4


def srgb(hexs):
    h = hexs.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


GREYS = {
    'grau1': ('Warmgrau hell', '#B9B5AC'),
    'grau2': ('Kühlgrau mittel', '#7F8790'),
}
BLUE_LIN = (0.10, 0.42, 0.72)     # Hellblau wie Phase-3-Renderings (sRGB ca. #59ADDD)
LED_GAIN = {'gruen': 0.85, 'blau': 2.0, 'rot': 1.3, 'gelb': 1.0}   # Wahrnehmungsabgleich im Bild (ANNAHME)
LED_COL = {
    'gruen': (0.06, 1.0, 0.16),
    'blau': (0.04, 0.22, 1.0),
    'rot': (1.0, 0.04, 0.02),
    'gelb': (1.0, 0.50, 0.0),
}


def plan3(off=0.0, W=W3, D=D3, cf=2.5, cb=1.0):
    """P3-Grundriss (x, y) wie im Mechanikmodell, um off nach innen versetzt; Front bei y = -D/2."""
    h = W / 2 - off
    y0, y1 = -D / 2 + off, D / 2 - off
    k = 0.4142 * off
    a, b = max(cf - k, 0.3), max(cb - k, 0.3)
    return [(-h + a, y0), (h - a, y0), (h, y0 + a), (h, y1 - b), (h - b, y1), (-h + b, y1), (-h, y1 - b), (-h, y0 + a)]


def drop2(cx, cz, r, k=LED_K, n=32):
    """Tropfen wie Logo (gen_logo_fluidi.drop): Kreis r, tangentiale Spitze k*r über der Mitte."""
    h = k * r
    phi = math.asin(r / h)
    pts = [(cx, cz + h)]
    a0, a1 = math.pi - phi, 2 * math.pi + phi
    for i in range(n + 1):
        t = a0 + (a1 - a0) * i / n
        pts.append((cx + r * math.cos(t), cz + r * math.sin(t)))
    return pts


def bake_mesh(ob):
    """Modifier-Ergebnis als neues Mesh (für Boolean-Werkzeuge)."""
    dg = bpy.context.evaluated_depsgraph_get()
    bpy.context.view_layer.update()
    return bpy.data.meshes.new_from_object(ob.evaluated_get(dg))


def mesh_from(ob, name, parent):
    """Text-/Kurvenobjekt in ein Mesh-Objekt gleicher Lage umwandeln (Boolean-Werkzeug); Original löschen."""
    bpy.context.view_layer.update()
    me = bake_mesh(ob)
    mo = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(mo)
    mo.parent = parent
    mo.matrix_parent_inverse = ob.matrix_parent_inverse.copy()
    mo.location, mo.rotation_euler, mo.scale = ob.location.copy(), ob.rotation_euler.copy(), ob.scale.copy()
    bpy.data.objects.remove(ob, do_unlink=True)
    return mo


def mats_v2(grey):
    g = srgb(GREYS[grey][1])
    m = {
        'body': shared(f'Huelse_{grey}', lambda n: mat_asa(n, g)),
        'logo': shared(f'Logo_{grey}', lambda n: mat_asa(n, tuple(c * 0.80 for c in g), layer_lines=False)),
        'blue': shared('Kappe_hellblau', lambda n: mat_asa(n, BLUE_LIN)),
        'led': shared('LED_Fenster', mat_led),
        'pcb': shared('Sonde_Loetstopp', lambda n: mat_simple(n, (0.02, 0.16, 0.06), rough=0.25, spec=0.6)),
        'silk': shared('Silkscreen', lambda n: mat_simple(n, (0.85, 0.85, 0.82), rough=0.6)),
        'seal': shared('Dichtmasse', lambda n: mat_simple(n, (0.05, 0.05, 0.055), rough=0.35)),
        'steel': shared('Edelstahl', lambda n: mat_simple(n, (0.62, 0.62, 0.6), rough=0.28, metal=1.0)),
        'nickel': shared('Nickel', lambda n: mat_simple(n, (0.70, 0.68, 0.64), rough=0.22, metal=1.0)),
        'cell': shared('Zelle', lambda n: mat_simple(n, (0.80, 0.80, 0.80), rough=0.12, metal=1.0)),
        'collar': shared('Kragen_anthrazit', lambda n: mat_asa(n, (0.05, 0.055, 0.06))),
        'oring': shared('ORing_Silikon', mat_silicone),
        'gasket': shared('Dichtung_Silikon', lambda n: mat_silicone(n, (0.85, 0.85, 0.82))),
    }
    return m


def mat_silicone(name, color=(0.75, 0.10, 0.06)):
    m = new_mat(name)
    p = find_node(m.node_tree, 'BSDF_PRINCIPLED')
    setin(p, (*color, 1), 'Base Color')
    setin(p, 0.4, 'Roughness')
    setin(p, 0.25, 'Subsurface Weight')
    setin(p, 0.3, 'Transmission Weight', 'Transmission')
    m.diffuse_color = (*color, 1)
    return m


def set_led_state(state, strength=7.0):
    """state: None/'aus' oder Schlüssel aus LED_COL. Wirkt auf alle LED-Materialien."""
    for m in bpy.data.materials:
        if m.name.startswith('LED'):
            p = find_node(m.node_tree, 'BSDF_PRINCIPLED')
            if state in LED_COL:
                setin(p, (*LED_COL[state], 1), 'Emission Color', 'Emission')
                setin(p, strength * LED_GAIN[state], 'Emission Strength')
            else:
                setin(p, 0.0, 'Emission Strength')


def led_material(name, state):
    """Eigenes LED-Material je Objekt (für Familienbild mit verschiedenen Farben)."""
    m = mat_led(name)
    if state in LED_COL:
        p = find_node(m.node_tree, 'BSDF_PRINCIPLED')
        setin(p, (*LED_COL[state], 1), 'Emission Color', 'Emission')
        setin(p, 7.0 * LED_GAIN[state], 'Emission Strength')
        m['fix_state'] = state
    return m


def arrow(name, p0, p1, width=1.2, head=3.0, mat=None, parent=None, normal=(0, -1, 0)):
    """Flacher Pfeil (mm) von p0 nach p1 in der Ebene senkrecht zu normal."""
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0)
    L = d.length
    u = d.normalized()
    v = u.cross(Vector(normal)).normalized()
    q = [(0, -width / 2), (L - head, -width / 2), (L - head, -head * 0.6), (L, 0), (L - head, head * 0.6), (L - head, width / 2), (0, width / 2)]
    bm = bmesh.new()
    vs = [bm.verts.new((p0 + u * a + v * b) * MM) for a, b in q]
    bm.faces.new(vs)
    ob = mesh_obj(name, bm, mat, parent)
    so = ob.modifiers.new('Dicke', 'SOLIDIFY'); so.thickness = 0.4 * MM
    return ob


# ----------------------------------------------------------------------------- Sensorkopf
def head_p3v2(grey='grau1', led_state=None, explode=0.0, cell_out=0.0, logo='fluidi_A_linie_mono.svg',
              internals=True, tag=''):
    """P3 fluidi v2. explode = Hülse (mit Schraube) um diesen Weg nach unten abgezogen (mm);
    cell_out = Zelle seitlich (+x) aus dem Clip geschoben (mm). Liefert das Wurzel-Empty."""
    root = bpy.data.objects.new('fluidi_P3' + tag, None); bpy.context.scene.collection.objects.link(root)
    m = mats_v2(grey)
    led_mat = led_material('LED_Fenster' + tag, led_state) if led_state else m['led']
    # ---- Hülse (grau) als eigene Gruppe, damit sie abgezogen werden kann
    sg = bpy.data.objects.new('Huelse' + tag, None); bpy.context.scene.collection.objects.link(sg)
    sg.parent = root
    sg.location = (0, 0, -explode * MM)
    z_top = Z_FUGE - GAP_F
    sleeve = prism('Huelse_grau' + tag, plan3(), 'z', 0, z_top, 0.6, 0.0, m['body'], sg, bevel=0.25)
    cut(sleeve, prism('H_innen' + tag, plan3(WALL), 'z', FLOOR, z_top + 2, parent=sg, bevel=0))
    cut(sleeve, box('H_Schlitz' + tag, -PW / 2 - 0.3, PW / 2 + 0.3, PCB_Y0 - 0.3, PCB_Y1 + 0.3, -1, FLOOR + 1, None, sg))
    cut(sleeve, cyl('H_Bohrung' + tag, 1.1, -1, FLOOR + 1, center=(0, SCREW_Y), axis='z', seg=32, parent=sg))
    cut(sleeve, cyl('H_Senkung' + tag, 2.2, -1, 1.4, center=(0, SCREW_Y), axis='z', seg=40, parent=sg))
    notch = drop2(0, LED_Z, LED_R + GAP_F, k=(LED_K * LED_R + GAP_F) / (LED_R + GAP_F))
    cut(sleeve, prism('H_Kerbe' + tag, notch, 'y', -D3 / 2 - 1, -D3 / 2 + WALL + 0.3, parent=sg, bevel=0))
    # Haltenoppe der Zelle an der Rückwand (x 4 ... 8)
    box('H_Noppe' + tag, 4.0, 8.0, D3 / 2 - WALL - 0.6, D3 / 2 - WALL + 0.05, Z_CELL - 3, Z_CELL + 3, m['body'], sg, bevel=0.1)
    # Logo: Relief 0.2 mm, Ton in Ton (etwas dunkler wirkend), Front unten
    lg, lw = svg_obj('Logo' + tag, logo, 16.0, m['logo'], sg, extrude=0.2)
    on_front_xz(lg, 0, -D3 / 2, 14.5)
    # Warnsymbol innen auf der Rückwand (gegenüber der Zelle, beim Abnehmen der Hülse zwangsläufig sichtbar).
    # VERTIEFT 0.4 mm (Restwand 1.2 mm): erhaben ginge nicht, weil Kragen und Zapfen beim Aufschieben mit nur
    # 0.2 mm Spalt durch die ganze Hülse gleiten.
    yi = D3 / 2 - WALL
    zc = 30.5                                         # Dreieck 8 x 9 mm (>= 7 x 9 mm, Sicherheitsbericht Kap. 3)
    tri = [(-4.0, zc - 4.5), (4.0, zc - 4.5), (0, zc + 4.5)]
    t_cut = prism('Warn_Dreieck' + tag, tri, 'y', yi - 0.3, yi + 0.4, parent=sg, bevel=0)
    cut(t_cut, prism('Warn_Innen' + tag, offset_poly(tri, 0.8), 'y', yi - 0.6, yi + 0.6, parent=sg, bevel=0), solver='FAST')
    t_cut.data = bake_mesh(t_cut)
    t_cut.modifiers.clear()
    cut(sleeve, t_cut)
    for i, (txt, sz, dz) in enumerate((('!', 4.6, -1.6), ('CR2032', 1.9, -6.6), ('Kinder: Verschluckgefahr', 1.25, -8.8))):
        t = text_obj(f'Warn_Text{i}' + tag, txt, sz, m['logo'], sg, extrude=0.35)
        on_front_xz(t, 0, yi + 0.05, zc + dz)
        tm = mesh_from(t, f'Warn_TextM{i}' + tag, sg)
        cut(sleeve, tm)
    # Schraube M2 x 4, unverlierbar in der Hülse (Kopf in Senkung, Kreuzschlitz PH0)
    sk = cyl('Schraube_Kopf' + tag, 1.9, 0.1, 1.3, center=(0, SCREW_Y), axis='z', seg=40, mat=m['steel'], parent=sg, bevel=0.2)
    for i, ang in enumerate((0, 90)):
        kb = box(f'Kreuz{i}' + tag, -1.15, 1.15, SCREW_Y - 0.28, SCREW_Y + 0.28, -0.5, 0.75, None, sg)
        kb.data.transform(Matrix.Translation(Vector((0, -SCREW_Y * MM, 0))))
        kb.data.transform(Matrix.Rotation(math.radians(ang), 4, 'Z'))
        kb.data.transform(Matrix.Translation(Vector((0, SCREW_Y * MM, 0))))
        cut(sk, kb, solver='FAST')
    cyl('Schraube_Schaft' + tag, 0.95, 1.3, 5.3, center=(0, SCREW_Y), axis='z', seg=24, mat=m['steel'], parent=sg, bevel=0.1)

    # ---- Kappe (hellblau) + Kern
    cap = prism('Kappe_blau' + tag, plan3(), 'z', Z_FUGE, H3, 0.0, 1.0, m['blue'], root, bevel=0.25)
    sq = [(-4.5 + 1, -2.6), (4.5 - 1, -2.6), (4.5, -1.6), (4.5, 2.4), (3.5, 3.4), (-3.5, 3.4), (-4.5, 2.4), (-4.5, -1.6)]
    cut(cap, prism('K_Tastloch' + tag, offset_poly(sq, -0.4), 'z', H3 - 2.5, H3 + 2, parent=root, bevel=0))
    prism('Taste_blau' + tag, sq, 'z', H3 - 2.4, H3 + 0.6, 0, 0.6, m['blue'], root, bevel=0.2)
    led = drop2(0, LED_Z, LED_R)
    cut(cap, prism('K_LEDloch' + tag, led, 'y', -D3 / 2 - 1, -D3 / 2 + WALL + 0.2, parent=root, bevel=0))
    prism('LED_Tropfen' + tag, led, 'y', -D3 / 2, -D3 / 2 + WALL, 0, 0, led_mat, root, bevel=0.3)
    if internals:
        # Zapfen der Kappe mit O-Ring-Nut, Schott (Unterkante z 29.8)
        prism('Zapfen_unten' + tag, plan3(1.8), 'z', 29.8, 31.5, mat=m['blue'], parent=root, bevel=0.15)
        prism('Zapfen_Nut' + tag, plan3(2.7), 'z', 31.5, 33.5, mat=m['blue'], parent=root, bevel=0)
        prism('Zapfen_oben' + tag, plan3(1.8), 'z', 33.5, Z_FUGE, mat=m['blue'], parent=root, bevel=0.15)
        orr = prism('ORing' + tag, plan3(1.75), 'z', 31.75, 33.25, mat=m['oring'], parent=root, bevel=0)
        cut(orr, prism('ORing_in' + tag, plan3(2.75), 'z', 31, 34, parent=root, bevel=0))
        bv = orr.modifiers.new('Rund', 'BEVEL'); bv.width = 0.6 * MM; bv.segments = 3
        # Verguss am Schott (Platinendurchführung)
        box('Verguss_Schott' + tag, -PW / 2 - 0.6, PW / 2 + 0.6, PCB_Y0 - 0.5, PCB_Y1 + 0.5, 29.3, 29.85, m['seal'], root, bevel=0.2)
        # Kragen (anthrazit, auf der Sonde vergossen) + Bodendichtung (Silikon)
        prism('Kragen' + tag, plan3(1.8), 'z', 2.8, 6.0, mat=m['collar'], parent=root, bevel=0.2)
        gas = prism('Bodendichtung' + tag, plan3(1.75), 'z', 2.2, 2.8, mat=m['gasket'], parent=root, bevel=0)
        cut(gas, box('G_Schlitz' + tag, -PW / 2 - 0.3, PW / 2 + 0.3, PCB_Y0 - 0.3, PCB_Y1 + 0.3, 1, 4, None, root), solver='FAST')
        cut(gas, cyl('G_Loch' + tag, 1.2, 1, 4, center=(0, SCREW_Y), axis='z', seg=24, parent=root), solver='FAST')
        # Leiterplatte im Kopf (Fach) mit Clip und Zelle auf der Rückseite (+y)
        box('PCB_Fach' + tag, -PW / 2, PW / 2, PCB_Y0, PCB_Y1, 0.0, 29.8, m['pcb'], root, bevel=0.1)
        clip_x0, clip_x1 = -10.0, 6.1
        cz0, cz1 = Z_CELL - 11.55, Z_CELL + 11.55
        yb = PCB_Y1
        strap = box('Clip_Buegel' + tag, clip_x0, clip_x1, yb + 3.5, yb + 3.8, cz0 + 1.2, cz1 - 1.2, m['nickel'], root, bevel=0.1)
        cut(strap, cyl('Clip_Fenster' + tag, 6.5, yb + 3, yb + 4.5, center=(0, Z_CELL), axis='y', seg=48, parent=root), solver='FAST')
        for nm, za, zb in (('Clip_Schiene_u', cz0, cz0 + 1.2), ('Clip_Schiene_o', cz1 - 1.2, cz1)):
            box(nm + tag, clip_x0, clip_x1, yb, yb + 3.8, za, zb, m['nickel'], root, bevel=0.1)
        box('Clip_Ende' + tag, clip_x0, clip_x0 + 0.5, yb, yb + 3.8, cz0, cz1, m['nickel'], root, bevel=0.1)
        cell = cyl('CR2032' + tag, 10.0, yb + 0.15, yb + 3.35, center=(cell_out, Z_CELL), axis='y', seg=72, mat=m['cell'], parent=root, bevel=0.3)
        t = text_obj('CR2032_Text' + tag, 'CR2032  3V', 1.8, m['seal'], root, extrude=0.03)
        on_back_xz(t, cell_out, yb + 3.37, Z_CELL - 5.0)
        t2 = text_obj('CR2032_Plus' + tag, '+', 4.0, m['seal'], root, extrude=0.03)
        on_back_xz(t2, cell_out + 5.5, yb + 3.37, Z_CELL + 4.0)
    probe_v2(root, m, tag)
    return root


def probe_v2(root, m, tag=''):
    L = PROBE_L
    prof = [(-PW / 2, 0), (PW / 2, 0), (PW / 2, -L + 8), (2.5, -L), (-2.5, -L), (-PW / 2, -L + 8)]
    prism('Sonde' + tag, prof, 'y', PCB_Y0, PCB_Y1, mat=m['pcb'], parent=root, bevel=0.15)
    for sgn, nm in ((-1, 'MarkV'), (1, 'MarkH')):
        yy = PCB_Y0 if sgn < 0 else PCB_Y1
        box(nm + tag, -PW / 2 + 1.0, PW / 2 - 1.0, yy - 0.02, yy + 0.02, -GAP_SOIL - 0.25, -GAP_SOIL + 0.25, m['silk'], root)
    t = text_obj('MaxText' + tag, 'max', 1.6, m['silk'], root, extrude=0.02)
    on_front_xz(t, -5.0, PCB_Y0 - 0.03, -GAP_SOIL + 1.6)
    prism('MaxPfeil' + tag, [(-9.2, -GAP_SOIL + 2.4), (-6.8, -GAP_SOIL + 2.4), (-8.0, -GAP_SOIL + 0.6)], 'y',
          PCB_Y0 - 0.04, PCB_Y0, mat=m['silk'], parent=root, bevel=0)
    t3 = text_obj('Rev' + tag, 'fluidi rev A', 1.2, m['silk'], root, extrude=0.02)
    on_front_xz(t3, 3.0, PCB_Y0 - 0.03, -GAP_SOIL + 1.6)


# ----------------------------------------------------------------------------- Gateway G1 v2
def gateway_g1v2(grey='grau1', led_state='gruen', logo='fluidi_A_linie_mono.svg', tag=''):
    """G1 "Sockel" 62 x 40 x 20 mm: Wanne grau (z 0 ... 13.85), Deckel hellblau (z 14.15 ... 20, oberer
    Teil der 45°-Frontfacette mit Status-Tropfen); Sichtfuge 0.3 mm. Ohne Stabantenne: FPC-Antenne (Seeed A-02,
    ANNAHME) innen an der Frontwand hinter der Facette, >= 15 mm zu XIAO/USB-C/RTC
    (docs/reviews/phase3_rgb_antenne_elektronik.md Kap. 2). USB-C hinten, Logo-Relief vorne."""
    root = bpy.data.objects.new('G1v2' + tag, None); bpy.context.scene.collection.objects.link(root)
    m = mats_v2(grey)
    Wg, Dg, Hg = 62.0, 40.0, 20.0
    zf = 14.0
    prof = [(-Dg / 2, 0), (Dg / 2, 0), (Dg / 2, Hg), (-Dg / 2 + 9, Hg), (-Dg / 2, Hg - 9)]
    low = prism('G1_Wanne' + tag, prof, 'x', -Wg / 2, Wg / 2, 3.0, 3.0, m['body'], root, bevel=0.4)
    cut(low, box('G1_ob' + tag, -40, 40, -30, 30, zf - 0.15, 40, None, root))
    up = prism('G1_Deckel' + tag, prof, 'x', -Wg / 2, Wg / 2, 3.0, 3.0, m['blue'], root, bevel=0.4)
    cut(up, box('G1_un' + tag, -40, 40, -30, 30, -5, zf + 0.15, None, root))
    # Status-LED: kleiner Tropfen auf der Facette rechts
    ang = 45.0
    yy, zz = -Dg / 2 + 6.0, Hg - 3.0
    dp = drop2(0, -1.0, 1.6)
    hole = prism('G1_LEDloch' + tag, dp, 'z', -2.5, 3, parent=root, bevel=0)
    led = prism('G1_LED' + tag, dp, 'z', -1.6, 0.02, mat=led_material('LED_G1' + tag, led_state), parent=root, bevel=0.2)
    for o in (hole, led):
        o.rotation_euler = (math.radians(ang), 0, 0)
        o.location = Vector((21.0, yy, zz)) * MM
    cut(up, hole)
    lg, _ = svg_obj('G1_Logo' + tag, logo, 22.0, m['logo'], root, extrude=0.2)
    on_front_xz(lg, -12.0, -Dg / 2, 5.4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f'G1_Fuss{sx}{sy}' + tag, 3.0, -0.8, 0.2, center=(sx * 24, sy * 14), axis='z', mat=m['seal'], parent=root, bevel=0.3)
    usb_c(root, m, (-14, Dg / 2, 5.5))
    return root


# ----------------------------------------------------------------------------- Studio
def studio(floor_col=(0.55, 0.555, 0.56), key=16.0):
    """Hohlkehle (Boden + Rückwand mit Radius), Softboxen; für Explosions- und Unterseitenbild."""
    mat = mat_simple('Studio', floor_col, rough=0.75, spec=0.3)
    bm = bmesh.new()
    R, Wd = 250.0, 1600.0
    prof = [(-900, 0), (300 - R, 0)]
    for i in range(1, 12):
        a = -math.pi / 2 + (math.pi / 2) * i / 12
        prof.append((300 - R + R * math.cos(a) + 0, R + R * math.sin(a)))
    prof.append((300, R)); prof.append((300, 1200))
    rows = []
    for x in (-Wd / 2, Wd / 2):
        rows.append([bm.verts.new(Vector((x, y, z)) * MM) for y, z in prof])
    for i in range(len(prof) - 1):
        bm.faces.new((rows[0][i], rows[1][i], rows[1][i + 1], rows[0][i + 1]))
    ob = mesh_obj('Hohlkehle', bm, mat)
    for f in ob.data.polygons:
        f.use_smooth = True
    def area(name, loc, target, size, energy, col=(1, 1, 1)):
        L = bpy.data.lights.new(name, 'AREA'); L.shape = 'RECTANGLE'; L.size = size[0]; L.size_y = size[1]
        L.energy = energy; L.color = col
        o = bpy.data.objects.new(name, L); bpy.context.scene.collection.objects.link(o)
        o.location = Vector(loc)
        o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
        return o
    area('Key', (-0.45, -0.35, 0.55), (0, 0, 0.1), (0.6, 0.6), key, (1.0, 0.97, 0.93))
    area('Fill', (0.5, -0.4, 0.25), (0, 0, 0.1), (0.7, 0.7), key * 0.30, (0.93, 0.96, 1.0))
    area('Rim', (0.15, 0.45, 0.45), (0, 0, 0.1), (0.5, 0.2), key * 0.5)
    wd = bpy.context.scene.world or bpy.data.worlds.new('Welt')
    bpy.context.scene.world = wd
    wd.use_nodes = True
    bg = find_node(wd.node_tree, 'BACKGROUND')
    bg.inputs[0].default_value = (0.85, 0.86, 0.88, 1); bg.inputs[1].default_value = 0.12
