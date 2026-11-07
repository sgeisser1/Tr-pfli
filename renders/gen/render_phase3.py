"""Tröpfli Phase 3 – Renderings aller Designvorschläge (Blender 4.0.2, Cycles CPU, ohne Denoiser).

In Blender ausführen (MCP oder Texteditor):
    exec(open('/home/sgeisser/git/Tr-pfli/renders/gen/render_phase3.py').read())
    build_design('p1'); render_design('p1')        # je Vorschlag 3 Bilder + .blend
    build_family(); render_family()                 # Familienbild 2400 x 1200 + .blend
    build_gateway(); render_gateway()               # Gateway-Varianten
Alle Geometrie in troepfli_lib.py (mm-genau, Meter-Einheiten).
"""
import bpy, math, os
from mathutils import Vector
exec(open('/home/sgeisser/git/Tr-pfli/renders/gen/troepfli_lib.py').read())

NAMES = {'p1': 'facette', 'p2': 'keil', 'p3': 'stele', 'p4': 'gipfel'}
SOIL = 115.0  # mm, Erdoberfläche im Topf
SENSOR_POS = (36.0, -30.0)   # mm, im Topf vorne rechts
SENSOR_ROT = -18.0           # Grad um z (zur Kamera gedreht)
LYING_POS = (190.0, -60.0)   # mm, zweites Exemplar liegt rückseitig auf dem Tisch
LYING_ROT = 216.87           # Grad; Sonde zeigt nach rechts vorne, Deckelschrift lesbar


def new_scene(name):
    """Frische Szene; alle anderen Szenen und verwaisten Daten löschen (eine Szene je .blend)."""
    sc = bpy.context.scene          # aktuelle Szene weiterverwenden (funktioniert auch mit blender -b)
    sc.name = name
    for other in list(bpy.data.scenes):
        if other != sc:
            for o in list(other.objects):
                bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.scenes.remove(other)
    clear_scene()
    for o in list(bpy.data.objects):
        if not o.users_scene:
            bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights, bpy.data.images):
        for d in list(coll):
            if d.users == 0:
                coll.remove(d)
    for c in list(bpy.data.collections):
        if not c.objects and not c.children:
            bpy.data.collections.remove(c)
    for m in list(bpy.data.materials):
        if m.users == 0:
            bpy.data.materials.remove(m)
    return sc


def build_design(key, samples=384):
    sc = new_scene('Troepfli_' + key)
    env = env_mats()
    room(env)
    pot(env, (0, 0), soil_z=SOIL)
    pilea(env, base=(-8, 12, SOIL), seed=11, scale=0.85)
    # Sensor im Topf: Markierung "max" auf Erdhöhe
    a = HEADS[key]()
    a.name = a.name.split('.')[0] + '_Topf'
    a.location = Vector((SENSOR_POS[0], SENSOR_POS[1], SOIL + GAP_SOIL)) * MM
    a.rotation_euler = (0, 0, math.radians(SENSOR_ROT))
    # zweites Exemplar liegt auf dem Tisch, Rückseite oben (Batteriedeckel)
    b = HEADS[key]()
    b.name = b.name.split('.')[0] + '_liegend'
    d = math.degrees(math.asin(5.7 / PROBE_L))
    b.rotation_euler = (math.radians(90 - d), 0, math.radians(LYING_ROT))
    b.location = Vector((LYING_POS[0], LYING_POS[1], 6.5)) * MM
    hc = Vector((SENSOR_POS[0], SENSOR_POS[1], SOIL + GAP_SOIL + 23)) * MM
    ct = camera('Cam_Topf', (0.13, -0.31, 0.235), (0.016, -0.012, 0.128), lens=50, fstop=5.6)
    ct.data.dof.focus_distance = (hc - ct.location).length
    camera('Cam_Nah', hc + Vector((0.075, -0.17, 0.085)), hc + Vector((0, 0, 0.002)), lens=65, fstop=8.0)
    pdir = Vector((-math.sin(math.radians(LYING_ROT)), math.cos(math.radians(LYING_ROT)), 0))
    bl = Vector((LYING_POS[0], LYING_POS[1], 5)) * MM + pdir * 0.03
    camera('Cam_Rueck', bl + Vector((-0.12, -0.15, 0.24)), bl, lens=52, fstop=11.0)
    render_settings((1600, 1200), samples)
    return sc


def hide_occluders(cam, target, margin=1.0):
    """Blätter/Stiele, die zwischen Kamera und Ziel im Bild liegen, für diese Aufnahme ausblenden
    (nur Nahaufnahme; die Pflanze bleibt in der Topf-Ansicht vollständig)."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    dist_t = (Vector(target) - cam.location).length
    hidden = []
    for o in sc.objects:
        if not (o.name.startswith('Blatt') or o.name.startswith('Stiel') or o.name == 'Stamm'):
            continue
        pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
        for p in pts + [sum(pts, Vector()) / 8]:
            v = world_to_camera_view(sc, cam, p)
            if -0.1 <= v.x <= 1.1 and -0.1 <= v.y <= 1.1 and 0 < v.z < dist_t * margin:
                o.hide_render = True; hidden.append(o.name); break
    for nm in list(hidden):
        if nm.startswith('Blatt'):
            st = sc.objects.get('Stiel' + nm[5:])
            if st:
                st.hide_render = True
    return hidden


def show_all():
    for o in bpy.context.scene.objects:
        if o.name.startswith(('Blatt', 'Stiel', 'Stamm')):
            o.hide_render = False


def render_design(key, shots=('topf', 'nah', 'rueck')):
    os.makedirs(OUTDIR, exist_ok=True)
    nm = NAMES[key]
    out = []
    cams = {'topf': 'Cam_Topf', 'nah': 'Cam_Nah', 'rueck': 'Cam_Rueck'}
    for s in shots:
        set_led(s in ('nah', 'topf'))
        show_all()
        if s == 'nah':
            c = bpy.data.objects[cams[s]]
            print('ausgeblendet', hide_occluders(c, c.location + (c.matrix_world.to_3x3() @ Vector((0, 0, -c.data.dof.focus_distance)))))
        out.append(render_to(os.path.join(OUTDIR, f'{key}_{nm}_{s}.png'), bpy.data.objects[cams[s]]))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTDIR, f'{key}_{nm}.blend'), copy=True)
    return out


def contact_sheet(files, out, cols=3):
    """Kontaktbogen (nur zur Kontrolle)."""
    import numpy as np
    ims = [bpy.data.images.load(f, check_existing=False) for f in files]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    buf = np.ones((h * rows, w * cols, 4), dtype=np.float32)
    for k, im in enumerate(ims):
        a = np.array(im.pixels[:], dtype=np.float32).reshape(im.size[1], im.size[0], 4)
        if a.shape[:2] == (h, w):
            r = rows - 1 - k // cols; c = k % cols
            buf[r * h:(r + 1) * h, c * w:(c + 1) * w] = a
    s = bpy.data.images.new('sheet', w * cols, h * rows); s.pixels[:] = buf.ravel()
    s.filepath_raw = out; s.file_format = 'PNG'; s.save()
    for im in ims:
        bpy.data.images.remove(im)
    bpy.data.images.remove(s)


def quick_preview(key, tmpdir, pct=40, samples=48):
    sc = bpy.context.scene
    sc.render.resolution_percentage = pct; sc.cycles.samples = samples
    cams = {'topf': 'Cam_Topf', 'nah': 'Cam_Nah', 'rueck': 'Cam_Rueck'}
    files = []
    for s, cn in cams.items():
        set_led(s != 'rueck'); show_all()
        c = bpy.data.objects[cn]
        if s == 'nah':
            hide_occluders(c, c.location + (c.matrix_world.to_3x3() @ Vector((0, 0, -c.data.dof.focus_distance))))
        files.append(render_to(os.path.join(tmpdir, f'q_{key}_{s}.png'), c))
    show_all()
    sc.render.resolution_percentage = 100
    contact_sheet(files, os.path.join(tmpdir, f'q_{key}.png'))
    return os.path.join(tmpdir, f'q_{key}.png')


# ----------------------------------------------------------------------------- Familienbild
def trough(env, x0, x1, y0, y1, h=125.0, wall=8.0, soil_z=SOIL):
    """Rechteckiger Pflanztrog (Beton hell), Erde bei soil_z."""
    beton = mat_simple('Beton', (0.50, 0.49, 0.46), rough=0.8, spec=0.3)
    outer = box('Trog_aussen', x0, x1, y0, y1, 0, h, beton, bevel=1.5)
    inner = box('Trog_innen', x0 + wall, x1 - wall, y0 + wall, y1 - wall, wall, h + 10, None, bevel=0)
    cut(outer, inner)
    bm = bmesh.new()
    rnd = random.Random(5)
    bmesh.ops.create_grid(bm, x_segments=120, y_segments=30, size=0.5)
    for v in bm.verts:
        v.co.x = (x0 + wall + (v.co.x + 0.5) * (x1 - x0 - 2 * wall)) * MM
        v.co.y = (y0 + wall + (v.co.y + 0.5) * (y1 - y0 - 2 * wall)) * MM
        v.co.z = (soil_z + rnd.uniform(-0.6, 0.6)) * MM
    so = mesh_obj('Erde', bm, env['soil'])
    for f in so.data.polygons:
        f.use_smooth = True


def build_family(samples=256):
    """Alle 4 Vorschläge im gleichen Massstab auf einem Präsentationsständer (Eiche, Schlitze 40 mm tief),
    Sonden sichtbar; Gateway G1 daneben; Topf mit Pflanze im Hintergrund."""
    sc = new_scene('Troepfli_Familie')
    env = env_mats()
    room(env)
    stand = box('Staender', -195, 195, -25, 25, 0, 40, env['wood'], bevel=1.0)
    xs = [-142, -47, 47, 142]
    for k, x in zip(['p1', 'p2', 'p3', 'p4'], xs):
        slot = box('Schlitz_' + k, x - 12, x + 12, -1.5, 1.5, 2, 45, None, bevel=0)
        cut(stand, slot)
        r = HEADS[k]()
        r.location = Vector((x, 0, 2 + PROBE_L)) * MM
        r.rotation_euler = (0, 0, math.radians(-10))
        t = text_obj('Label_' + k, k.upper(), 7, mat_simple('Label_' + k, (0.16, 0.12, 0.08), rough=0.7), None, extrude=0.2)
        on_front_xz(t, x, -25.2, 20)
    g = gateway_g1()
    g.location = Vector((262, -35, 0)) * MM
    g.rotation_euler = (0, 0, math.radians(-20))
    pot(env, (-300, 190), soil_z=SOIL)
    pilea(env, base=(-300, 190, SOIL), seed=11, scale=0.85)
    camera('Cam_Familie', (0.05, -0.74, 0.16), (0.05, 0.0, 0.08), lens=50, fstop=11.0)
    render_settings((2400, 1200), samples)
    return sc


def render_family():
    set_led(True)
    p = render_to(os.path.join(OUTDIR, 'familie_alle4_gateway.png'), bpy.data.objects['Cam_Familie'])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTDIR, 'familie.blend'), copy=True)
    return p


# ----------------------------------------------------------------------------- Gateway
def build_gateway(samples=256):
    sc = new_scene('Troepfli_Gateway')
    env = env_mats()
    room(env)
    g1 = gateway_g1()
    g1.location = Vector((-48, -5, 0)) * MM
    g1.rotation_euler = (0, 0, math.radians(12))
    g2 = gateway_g2()
    g2.location = Vector((42, 15, 0)) * MM
    g2.rotation_euler = (0, 0, math.radians(-12))
    # Massstab: ein Sensor P1 liegt rechts vorne
    s = HEADS['p1']()
    d = math.degrees(math.asin(5.7 / PROBE_L))
    s.rotation_euler = (math.radians(90 - d), 0, math.radians(235))
    s.location = Vector((25, -75, 6.5)) * MM
    camera('Cam_Gateway', (0.03, -0.37, 0.16), (0.005, -0.01, 0.022), lens=50, fstop=8.0)
    render_settings((1600, 1200), samples)
    return sc


def render_gateway():
    set_led(True)
    p = render_to(os.path.join(OUTDIR, 'gateway_g1_sockel_g2_gipfel.png'), bpy.data.objects['Cam_Gateway'])
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUTDIR, 'gateway.blend'), copy=True)
    return p
