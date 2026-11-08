"""fluidi Phase 4e - Bibliothek fuer die finalen Renderings (Blender 4.0.2, nur bpy/bmesh).

Geometrie der Geraete kommt AUSSCHLIESSLICH aus den Generator-Ausgaben (nichts nachmodelliert):
  renders/final/mesh/sensor_*.obj   <- mechanical/sensor/fluidi_sensor.FCStd       (export_cad_obj.py, freecadcmd)
  renders/final/mesh/gateway_*.obj  <- mechanical/gateway_pi/fluidi_gateway_pi.FCStd (export_cad_obj.py)
  renders/final/mesh/pcb_kicad.obj  <- hardware/sensor/out/fluidi_sensor.step       (export_pcb_obj.py, FreeCAD-GUI)
Alle OBJ in mm, Kopfkoordinaten nach docs/interfaces/PCB_OUTLINE.md Kap. 1 (x Breite, y Tiefe, 0 = Front, z 0 =
Kopfunterkante). In Blender: Meter, Front des Sensors zeigt nach -y.
Umgebung (Raum, Tisch, Topf, Erde, Pflanze, Studio) per Skript aus renders/gen/fluidi_lib.py.

Verwendung:  exec(open('/home/sgeisser/git/Tr-pfli/renders/final/scripts/final_lib.py').read())
Cycles CPU, OHNE Denoiser (use_denoising = False), Rauschen nur ueber Samples.
"""
import bpy, bmesh, math, os, random, sys, time
from mathutils import Vector, Matrix, Quaternion

exec(open('/home/sgeisser/git/Tr-pfli/renders/gen/fluidi_lib.py').read())

MESH = os.path.join(REPO, 'renders/final/mesh')
OUTF = os.path.join(REPO, 'renders/final')
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


def srgb(hexs):
    h = hexs.lstrip('#')
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# Farben: Huelse/Wanne Warmgrau hell #B9B5AC (D-010), Kappe/Deckel Hellblau #59ADDD
# (mechanical/gen/fluidi_gateway_pi.py COLORS, = P3_FLUIDI.md "ca. sRGB #59ADDD"), Schrift #4F4B45 (Wortmarke v3a).
GREY = srgb('#B9B5AC')
BLUE = srgb('#59ADDD')
INK = (79, 75, 69)                     # #4F4B45 fuer PIL-Beschriftungen
LED_COL = {'gruen': (0.06, 1.0, 0.16), 'blau': (0.04, 0.22, 1.0)}
LED_GAIN = {'gruen': 0.85, 'blau': 2.0}   # Wahrnehmungsabgleich wie renders/gen/fluidi_p3v2.py (ANNAHME)

# Sensor-Teile: Datei -> Materialschluessel
SENSOR_PARTS = {
    'Huelse_grau': 'grau', 'Kappe_blau': 'blau', 'Taste_blau': 'blau', 'Tastenteller': 'blau', 'Klemmring': 'blau',
    'Fenster_transluzent': 'led', 'Stoessel': 'natur', 'Schottkeil': 'natur', 'Kragen': 'kragen',
    'Verguss_Kragen': 'verguss', 'Verguss_Schott': 'verguss', 'Mutter_M2': 'stahl', 'Schraube_M2': 'stahl',
    'ORing_Kragen': 'oring', 'ORing_Zapfen': 'oring', 'Membran_Silikon': 'membran', 'CR2032': 'zelle',
    'D1_LED': 'led_chip',
}
GATEWAY_PARTS = {
    'Wanne_grau': 'grau', 'Deckel_blau': 'blau', 'Fenster_transluzent': 'led', 'Fuss_0': 'fuss', 'Fuss_1': 'fuss',
    'Fuss_2': 'fuss', 'Fuss_3': 'fuss',
    # Innenleben (durch USB-Fenster, Schlitze und Tropfenfenster sichtbar), Huellmodelle des Generators
    'Pi_PCB': 'pcb', 'Pi_Bauteile_oben': 'ic', 'Pi_Bauteile_unten': 'ic', 'microSD_Karte': 'ic',
    'LED_Platine': 'pcb', 'LED_RGB': 'led_chip', 'Klima_Modul_Option': 'pcb_blau', 'RTC_Modul_Option': 'pcb_blau',
    'Leitungen_Klima': 'ic', 'Schraube_M2p5_0': 'stahl', 'Schraube_M2p5_1': 'stahl', 'Schraube_M2p5_2': 'stahl',
    'Schraube_M2p5_3': 'stahl', 'Einsatz_0': 'messing', 'Einsatz_1': 'messing', 'Einsatz_2': 'messing',
    'Einsatz_3': 'messing',
}


# ----------------------------------------------------------------------------- Materialien
def shared(name, fn):
    return bpy.data.materials.get(name) or fn(name)


def mat_led_win(name, state=None):
    """Fenster naturweiss transluzent; leuchtet in der LED-Farbe (Emission)."""
    m = new_mat(name)
    p = find_node(m.node_tree, 'BSDF_PRINCIPLED')
    setin(p, (0.92, 0.91, 0.88, 1), 'Base Color')
    setin(p, 0.35, 'Roughness')
    setin(p, 0.45, 'Transmission Weight', 'Transmission')
    setin(p, 0.35, 'Subsurface Weight')
    if state in LED_COL:
        setin(p, (*LED_COL[state], 1), 'Emission Color', 'Emission')
        setin(p, 7.0 * LED_GAIN[state], 'Emission Strength')
    else:
        setin(p, 0.0, 'Emission Strength')
    return m


def mats(led_state=None, tag=''):
    def silicone(n, c, tr=0.3):
        m = mat_simple(n, c, rough=0.4)
        p = find_node(m.node_tree, 'BSDF_PRINCIPLED')
        setin(p, 0.25, 'Subsurface Weight'); setin(p, tr, 'Transmission Weight', 'Transmission')
        return m
    m = {
        'grau': shared('ASA_Warmgrau', lambda n: mat_asa(n, GREY)),
        'logo': shared('ASA_Warmgrau_Logo', lambda n: mat_asa(n, tuple(c * 0.80 for c in GREY), layer_lines=False)),
        'blau': shared('ASA_Hellblau', lambda n: mat_asa(n, BLUE)),
        'natur': shared('ASA_natur', lambda n: mat_asa(n, (0.70, 0.68, 0.62))),
        'kragen': shared('ASA_Kragen_anthrazit', lambda n: mat_asa(n, (0.06, 0.062, 0.065))),
        'verguss': shared('Epoxid', lambda n: mat_simple(n, (0.025, 0.025, 0.028), rough=0.2, spec=0.6)),
        'stahl': shared('Stahl_verzinkt', lambda n: mat_simple(n, (0.66, 0.66, 0.64), rough=0.3, metal=1.0)),
        'oring': shared('ORing_Silikon_rot', lambda n: silicone(n, (0.62, 0.08, 0.05))),
        'membran': shared('Membran_Silikon', lambda n: silicone(n, (0.85, 0.85, 0.82), 0.5)),
        'zelle': shared('CR2032_Stahl', lambda n: mat_simple(n, (0.80, 0.80, 0.79), rough=0.14, metal=1.0)),
        'fuss': shared('Fuss_Gummi', lambda n: mat_simple(n, (0.03, 0.03, 0.03), rough=0.7)),
        'pcb': shared('PCB_gruen', lambda n: mat_simple(n, (0.012, 0.13, 0.035), rough=0.28, spec=0.6)),
        'pcb_blau': shared('PCB_blau', lambda n: mat_simple(n, (0.01, 0.04, 0.20), rough=0.28, spec=0.6)),
        'ic': shared('IC_schwarz', lambda n: mat_simple(n, (0.03, 0.03, 0.03), rough=0.45)),
        'messing': shared('Messing', lambda n: mat_simple(n, (0.75, 0.55, 0.25), rough=0.3, metal=1.0)),
        'led': shared('LED_Fenster' + tag, lambda n: mat_led_win(n, led_state)),
    }
    m['led_chip'] = shared('LED_Chip' + tag, lambda n: led_chip(n, led_state))
    return m


def led_chip(name, state):
    mm = mat_simple(name, (0.9, 0.9, 0.88), rough=0.3)
    p = find_node(mm.node_tree, 'BSDF_PRINCIPLED')
    if state in LED_COL:
        setin(p, (*LED_COL[state], 1), 'Emission Color', 'Emission')
        setin(p, 30.0, 'Emission Strength')
    return mm


def pcb_mat(key):
    """KiCad-STEP-Farbe -> Material. Platine: JLC Loetstopp gruen (ORDER_JLC_REV_B.md: PCB Color Gruen, ENIG)."""
    r, g, b = (int(key[i:i + 2], 16) / 255 for i in (0, 2, 4))
    name = 'PCB_' + key
    if bpy.data.materials.get(name):
        return bpy.data.materials[name]
    lin = srgb(key)
    if key == '507c69':
        mm = mat_simple(name, (0.012, 0.13, 0.035), rough=0.28, spec=0.6)
    elif (r + g + b) / 3 > 0.7 and key != 'dbbc7e':
        mm = mat_simple(name, (0.80, 0.80, 0.78), rough=0.25, metal=1.0)      # verzinnte Anschluesse
    elif key == 'dbbc7e':
        mm = mat_simple(name, (0.78, 0.78, 0.76), rough=0.2, metal=1.0)       # Quarzdeckel (Metall)
    elif key == '818181':
        mm = mat_simple(name, (0.70, 0.69, 0.66), rough=0.22, metal=1.0)      # Clip 3034 (Nickel), Tastergehaeuse
    elif (r + g + b) / 3 < 0.2:
        mm = mat_simple(name, (0.03, 0.03, 0.03), rough=0.4)
    else:
        mm = mat_simple(name, lin, rough=0.45)
    return mm


# ----------------------------------------------------------------------------- OBJ laden
def read_obj(path):
    """Eigener OBJ-Leser (v/f/o/usemtl). Liefert Liste (Objektname, Material, verts, faces)."""
    out = []
    verts = []
    cur = None
    for line in open(path):
        if line.startswith('v '):
            _, x, y, z = line.split()
            verts.append((float(x), float(y), float(z)))
        elif line.startswith('f '):
            cur[2].append(tuple(int(t.split('/')[0]) - 1 for t in line.split()[1:]))
        elif line.startswith('o '):
            cur = [line.split()[1], None, []]
            out.append(cur)
        elif line.startswith('usemtl '):
            cur[1] = line.split()[1]
    res = []
    for name, mt, faces in out:
        used = sorted({i for f in faces for i in f})
        remap = {o: n for n, o in enumerate(used)}
        res.append((name, mt, [verts[i] for i in used], [tuple(remap[i] for i in f) for f in faces]))
    return res


_CACHE = {}


def obj_mesh(path, key):
    """Mesh-Datenblock (Meter) aus OBJ; mehrfach verwendbar (Instanzen fuer mehrere Sensoren)."""
    if (path, key) in _CACHE and _CACHE[(path, key)].name in bpy.data.meshes:
        return _CACHE[(path, key)]
    for name, mt, vs, fs in read_obj(path):
        if name != key:
            continue
        me = bpy.data.meshes.new(key)
        me.from_pydata([(x * MM, y * MM, z * MM) for x, y, z in vs], [], fs)
        me.validate()
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        try:
            me.use_auto_smooth = True; me.auto_smooth_angle = math.radians(32)
        except AttributeError:
            pass
        _CACHE[(path, key)] = me
        return me
    raise KeyError(key)


def link(name, me, mat, parent):
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if mat is not None and len(me.materials) == 0:
        me.materials.append(mat)
    elif mat is not None:
        ob.material_slots[0].link = 'OBJECT'; ob.material_slots[0].material = mat
    ob.parent = parent
    return ob


def empty(name, parent=None, loc=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.parent = parent
    e.location = Vector(loc) * MM
    e.empty_display_size = 0.01
    return e


def logo_faces(me, mlogo):
    """Logo-Relief der Huelse (0.25 mm erhaben vor y = 0, fluidi_params.LOGO) eigenes Material (Ton in Ton, dunkler)."""
    if len(me.materials) > 1:
        return
    me.materials.append(mlogo)
    for p in me.polygons:
        c = p.center / MM
        if c.y < -0.02 and abs(c.x) < 12 and 10 < c.z < 24:
            p.material_index = 1


def sensor(tag='', led_state='gruen', parts=None, explode=None, with_pcb=True):
    """Sensor aus den CAD-Meshes. explode: {Teilname|'PCB': (dx, dy, dz) mm}. Liefert Wurzel-Empty
    (Ursprung = Kopfkoordinaten-Nullpunkt: Mitte Frontflaeche x 0, y 0, z 0 Kopfunterkante)."""
    m = mats(led_state, tag)
    root = empty('fluidi_Sensor' + tag)
    explode = explode or {}
    objs = {}
    for part, mk in SENSOR_PARTS.items():
        if parts is not None and part not in parts:
            continue
        me = obj_mesh(os.path.join(MESH, 'sensor_%s.obj' % part), part)
        g = empty(part + tag + '_E', root, explode.get(part, (0, 0, 0)))
        ob = link(part + tag, me, m[mk], g)
        if part == 'Huelse_grau':
            logo_faces(me, m['logo'])
        objs[part] = ob
    if with_pcb:
        g = empty('PCB' + tag + '_E', root, explode.get('PCB', (0, 0, 0)))
        for name, mt, vs, fs in read_obj(os.path.join(MESH, 'pcb_kicad.obj')):
            me = obj_mesh(os.path.join(MESH, 'pcb_kicad.obj'), name)
            link('PCB_' + name + tag, me, pcb_mat(name[2:]), g)
        objs['PCB'] = g
        # D1 (kein 3D-Modell im KiCad-STEP): Platzhalter des Mechanik-Generators mit der Platine bewegen
        if 'D1_LED' in objs:
            objs['D1_LED'].parent.parent = g
            objs['D1_LED'].parent.location = (0, 0, 0)
    # LED-Licht im Fenster (Punktlicht an D1: x 0, y 6.0, z 43.85 -> leuchtet durch den Lichtschaft)
    if led_state in LED_COL:
        L = bpy.data.lights.new('LED' + tag, 'POINT'); L.energy = 0.012; L.shadow_soft_size = 0.0005
        L.color = LED_COL[led_state]
        lo = bpy.data.objects.new('LED' + tag, L); bpy.context.scene.collection.objects.link(lo)
        lo.parent = root; lo.location = Vector((0, 1.5, 44.6)) * MM
    return root, objs


def gateway(tag='', led_state='gruen'):
    """Gateway G1 v4 aus den CAD-Meshes; Ursprung Mitte Boden (x 0, y 0, z 0), Front (Facette) nach -y."""
    m = mats(led_state, tag)
    root = empty('fluidi_Gateway' + tag)
    for part, mk in GATEWAY_PARTS.items():
        me = obj_mesh(os.path.join(MESH, 'gateway_%s.obj' % part), part)
        ob = link('GW_' + part + tag, me, m[mk], root)
        if part == 'Wanne_grau' and len(me.materials) == 1:
            # Logo-Relief auf der Front (y < -21 vor der Wand): dunkler Ton in Ton
            me.materials.append(m['logo'])
            for p in me.polygons:
                c = p.center / MM
                if c.y < -21.02 and c.z < 11.5:
                    p.material_index = 1
    if led_state in LED_COL:
        L = bpy.data.lights.new('GW_LED' + tag, 'POINT'); L.energy = 0.012; L.shadow_soft_size = 0.0005
        L.color = LED_COL[led_state]
        lo = bpy.data.objects.new('GW_LED' + tag, L); bpy.context.scene.collection.objects.link(lo)
        lo.parent = root; lo.location = Vector((24.0, -17.5, 13.5)) * MM
    return root


# ----------------------------------------------------------------------------- Szene
def new_scene(name):
    sc = bpy.data.scenes.new(name)
    bpy.context.window.scene = sc if bpy.context.window else None
    return sc


def reset():
    """Alles loeschen (Szene + Datenbloecke), frische Szene."""
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights, bpy.data.materials,
                 bpy.data.images, bpy.data.node_groups):
        for d in list(coll):
            if getattr(d, 'type', '') in ('RENDER_RESULT', 'COMPOSITING'):
                continue
            coll.remove(d)
    _CACHE.clear()


def big_pot(env, loc=(0, 0), d_top=200.0, h=180.0, soil_z=166.0):
    """Terracotta-Topf ca. 20 cm (Oberkante aussen ~ d_top) mit Erde; fluidi_lib.pot skaliert."""
    r_top = d_top / 2 - 3.5
    return pot(env, loc, r_top=r_top, r_bot=r_top * 0.76, h=h, soil_z=soil_z)


def clear_leaves(head, W=34.0, D=13.0, H=58.5, margin=3.0, probe=True):
    """Blaetter (samt Stiel), die den Sensorkopf schneiden wuerden, ausblenden (echtes Blatt wuerde ausweichen)."""
    bpy.context.view_layer.update()
    inv = head.matrix_world.inverted()
    dg = bpy.context.evaluated_depsgraph_get()
    hidden = []
    for o in bpy.context.scene.objects:
        if not (o.name.startswith('Blatt') or o.name.startswith('Stiel')):
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        hit = False
        for v in me.vertices:
            q = inv @ (o.matrix_world @ v.co) / MM
            if abs(q.x) < W / 2 + margin and -margin < q.y < D + margin and -6 < q.z < H + margin:
                hit = True; break
        ev.to_mesh_clear()
        if hit:
            hidden.append(o.name)
    for n in hidden:
        o = bpy.data.objects[n]; o.hide_render = True; o.hide_viewport = True
        other = ('Stiel' + n[5:]) if n.startswith('Blatt') else ('Blatt' + n[5:])
        if other in bpy.data.objects:
            bpy.data.objects[other].hide_render = True; bpy.data.objects[other].hide_viewport = True
    print('ausgeblendet (Kollision mit Kopf):', hidden, flush=True)
    return hidden


def settings(res, samples, exposure=-0.6):
    render_settings(res, samples)
    sc = bpy.context.scene
    sc.cycles.use_denoising = False
    sc.view_settings.exposure = exposure
    sc.cycles.adaptive_threshold = 0.01
    try:
        sc.cycles.use_preview_denoising = False
    except AttributeError:
        pass


def area_light(name, loc, target, size, energy, col=(1, 1, 1)):
    L = bpy.data.lights.new(name, 'AREA'); L.shape = 'RECTANGLE'; L.size = size[0]; L.size_y = size[1]
    L.energy = energy; L.color = col
    o = bpy.data.objects.new(name, L); bpy.context.scene.collection.objects.link(o)
    o.location = Vector(loc)
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


def render(path, cam, samples=None):
    sc = bpy.context.scene
    if samples:
        sc.cycles.samples = samples
    sc.camera = cam
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True)
    dt = time.time() - t
    print('RENDER %s %.0f s' % (path, dt), flush=True)
    return dt


def batch_args():
    """Argumente nach '--' bei blender -b: --samples N --pct P."""
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    o = {'samples': None, 'pct': 100}
    for k in ('--samples', '--pct'):
        if k in argv:
            o[k[2:]] = int(argv[argv.index(k) + 1])
    return o


# ----------------------------------------------------------------------------- Studio (aus renders/gen/fluidi_p3v2.py, Farbe/Licht parametrisiert)
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
