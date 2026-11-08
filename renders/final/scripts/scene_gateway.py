"""fluidi Phase 4e - Bild 5 Gateway G1 v4 auf einem Buerotisch neben einem Sensor, Bild 6 Produktfoto beider Geraete.

  5 fluidi_05_gateway_buero.png    Schreibtisch (Tageslicht), Gateway mit Micro-USB-Kabel, daneben Sensor in einer
                                    kleinen Topfpflanze (Topf ca. 12 cm)
  6 fluidi_06_produktfoto.png      heller neutraler Hintergrund, Gateway und Sensor (liegend, Front nach oben)

Gateway und Sensor: CAD-Meshes (final_lib.gateway / final_lib.sensor). Kabel, Tisch, Topf, Pflanze, Notizbuch, Tasse:
Requisiten per Skript (keine Produktgeometrie). Micro-USB-PWR-Fenster: x -28, z 7.5, Rueckwand y +21
(fluidi_gateway_pi.py: px(USB['PWR_X']), ZP + USB['ZC_DZ']); Steckerumspritzung 10.6 x 7.0 (USB['PLUG']).
Stapel:  blender -b --factory-startup --python renders/final/scripts/scene_gateway.py -- 5 6 [--samples N] [--pct P]
"""
import sys
exec(open('/home/sgeisser/git/Tr-pfli/renders/final/scripts/final_lib.py').read())


def usb_cable(parent, pts_mm, mat_plug, mat_cable):
    """Micro-USB-Stecker (Umspritzung 10.6 x 7.0, laut Generator) in der PWR-Buchse + Kabel als Kurve (Requisite)."""
    box('USB_Stecker', -28 - 5.3, -28 + 5.3, 19.5, 33.0, 7.5 - 3.5, 7.5 + 3.5, mat_plug, parent, bevel=1.2)
    cyl('USB_Knickschutz', 2.4, 33.0, 41.0, center=(-28, 7.5), axis='y', seg=32, mat=mat_plug, parent=parent, bevel=0.4)
    cu = bpy.data.curves.new('USB_Kabel', 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(pts_mm) - 1)
    for bp, p in zip(sp.bezier_points, pts_mm):
        bp.co = Vector(p) * MM; bp.handle_left_type = bp.handle_right_type = 'AUTO'
    cu.bevel_depth = 1.6 * MM; cu.bevel_resolution = 4; cu.resolution_u = 24
    ob = bpy.data.objects.new('USB_Kabel', cu); bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat_cable); ob.parent = parent
    return ob


def desk_props(env):
    """Schreibtisch hell, Wand, Notizbuch, Tasse (Requisiten)."""
    top = mat_simple('Tischplatte_hell', (0.62, 0.60, 0.56), rough=0.55, spec=0.35)
    box('Tisch', -700, 700, -450, 450, -25, 0, env['wood'])
    box('Wand', -900, 900, 380, 395, -25, 900, env['wall'])
    nb = mat_simple('Notizbuch', (0.08, 0.12, 0.16), rough=0.6)
    pg = mat_simple('Papier', (0.85, 0.84, 0.80), rough=0.8)
    b = box('Notizbuch', -60, 90, -105, 105, 0.0, 12.0, nb, bevel=1.5)
    b.rotation_euler = (0, 0, math.radians(-22)); b.location = Vector((-330, -90, 0)) * MM
    p = box('Seiten', -58, 88, -102, 102, 1.0, 11.0, pg, bevel=0.3)
    p.parent = b
    cm = mat_simple('Tasse', (0.86, 0.85, 0.82), rough=0.15, spec=0.5)
    mug = cyl('Tasse', 42.0, 0, 95, center=(0, 0), axis='z', seg=96, mat=cm, bevel=1.5)
    inner = cyl('Tasse_innen', 38.5, 6, 100, center=(0, 0), axis='z', seg=96)
    cut(mug, inner)
    mug.location = Vector((140, 230, 0)) * MM
    cof = mat_simple('Kaffee', (0.06, 0.03, 0.015), rough=0.05)
    k = cyl('Kaffee', 38.6, 0, 80, center=(0, 0), axis='z', seg=96, mat=cof)
    k.location = mug.location


def build_buero():
    reset()
    sc = bpy.context.scene
    env = env_mats()
    desk_props(env)
    # Tageslicht: Fensterflaeche links, Sonne flach, Aufhellung rechts, Himmel
    area_light('Fenster', (-0.9, 0.05, 0.6), (0.0, 0.0, 0.05), (1.2, 1.0), 70, (1.0, 0.97, 0.93))
    area_light('Aufheller', (0.45, -0.8, 0.35), (0.0, 0.0, 0.05), (0.9, 0.9), 28, (0.93, 0.96, 1.0))
    S = bpy.data.lights.new('Sonne', 'SUN'); S.energy = 1.4; S.angle = math.radians(5); S.color = (1.0, 0.95, 0.88)
    so = bpy.data.objects.new('Sonne', S); sc.collection.objects.link(so)
    so.rotation_euler = (Vector((0, 0, 0)) - Vector((-0.85, 0.3, 0.6))).to_track_quat('-Z', 'Y').to_euler()
    wd = sc.world or bpy.data.worlds.new('Welt'); sc.world = wd; wd.use_nodes = True
    bg = find_node(wd.node_tree, 'BACKGROUND'); bg.inputs[0].default_value = (0.80, 0.84, 0.90, 1)
    bg.inputs[1].default_value = 0.25
    # Gateway
    g = gateway('', 'gruen')
    g.location = Vector((30, -40, 1.5)) * MM               # auf den Fuessen (z -1.5 ... 0)
    g.rotation_euler = (0, 0, math.radians(14))
    plug = mat_simple('USB_Kunststoff', (0.85, 0.85, 0.83), rough=0.45)
    usb_cable(g, [(-28, 41, 7.5), (-30, 70, 4.0), (-45, 130, 1.6), (-120, 230, 1.6), (-160, 380, 1.6)], plug, plug)
    # Sensor in kleiner Topfpflanze (Topf ca. 12 cm) links neben dem Gateway
    pot_xy = (-90, 70)
    soil = big_pot(env, pot_xy, d_top=120.0, h=110.0, soil_z=100.0)
    pilea(env, base=(pot_xy[0] - 14, pot_xy[1] + 16, soil), seed=5, n_leaves=11, scale=0.62)
    r, objs = sensor('_S', 'gruen')
    r.location = Vector((pot_xy[0] + 14, pot_xy[1] - 24, soil + GAP_SOIL)) * MM
    r.rotation_euler = (0, 0, math.radians(18))
    clear_leaves(r)
    return g, r


def cam_buero(g, r):
    c = camera('Cam_Buero', (0.15, -0.45, 0.235), (-0.03, 0.025, 0.06), lens=45, fstop=6.3)
    bpy.context.view_layer.update()
    c.data.dof.focus_distance = ((g.matrix_world @ Vector((0, -0.015, 0.012))) - c.location).length
    return c


# ----------------------------------------------------------------------------- 6 Produktfoto
def build_produkt():
    reset()
    sc = bpy.context.scene
    studio(floor_col=(0.88, 0.88, 0.87), key=18.0)
    g = gateway('', 'gruen')
    g.location = Vector((40, 42, 1.5)) * MM
    g.rotation_euler = (0, 0, math.radians(-14))
    # Sensor liegend auf der Rueckwand der Huelse (y = 13 -> Boden), Front nach oben. Die Sonde (B-Seite y 8.2)
    # steht 4.8 mm ueber der Unterlage frei (Schwerpunkt im Kopf).
    r, objs = sensor('_S', 'gruen')
    r.rotation_euler = (math.radians(-90), 0, math.radians(58))
    bpy.context.view_layer.update()
    r.location = Vector((-10, -45, 13.0)) * MM
    return g, r


def cam_produkt(g, r):
    c = camera('Cam_Produkt', (0.13, -0.40, 0.26), (0.006, -0.014, 0.006), lens=58, fstop=10.0)
    return c


def run(jobs, samples=None, pct=100):
    times = {}
    for j in jobs:
        if j == '5':
            g, r = build_buero(); c = cam_buero(g, r)
            settings((2000, 1334), samples or 1024, exposure=-0.9)
            bpy.context.scene.render.resolution_percentage = pct
            times[j] = render(os.path.join(OUTF, 'fluidi_05_gateway_buero.png'), c)
        elif j == '6':
            g, r = build_produkt(); c = cam_produkt(g, r)
            settings((2000, 1334), samples or 768, exposure=-0.85)
            bpy.context.scene.render.resolution_percentage = pct
            times[j] = render(os.path.join(OUTF, 'fluidi_06_produktfoto.png'), c)
    print('ZEITEN', times, flush=True)


if bpy.app.background and '--' in sys.argv:
    a = batch_args()
    jobs = [x for x in sys.argv[sys.argv.index('--') + 1:] if x in ('5', '6')]
    run(jobs, a['samples'], a['pct'])
