"""fluidi Phase 4e - Bilder 1 und 2: Sensor in einer Topfpflanze (Topf ca. 20 cm), Tageslicht.

  1 fluidi_01_topf_led_gruen.png   Uebersicht, LED gruen (ok)
  2 fluidi_02_nah_led_blau.png     nahe Kamera, LED blau (giessen)

Sensor: CAD-Meshes (final_lib.sensor), Kopfunterkante 5 mm ueber der Erde (Markierung max. Stecktiefe z = -5,
PCB_OUTLINE.md Kap. 2), Sonde 100 mm in der Erde. Topf, Erde, Pflanze per Skript (renders/gen/fluidi_lib.py).

Stapel:  blender -b --factory-startup --python renders/final/scripts/scene_topf.py -- 1 2 [--samples N] [--pct P]
"""
import sys
exec(open('/home/sgeisser/git/Tr-pfli/renders/final/scripts/final_lib.py').read())

SOIL = 166.0                       # Erdoberflaeche (mm ueber Tisch)
S_POS = (50.0, -42.0)              # Sensor im Topf (Mitte Front, mm)
S_ROT = 22.0                       # Drehung um z (Grad), Front leicht zur Kamera


def build_topf(led='gruen'):
    reset()
    sc = bpy.context.scene
    env = env_mats()
    room(env)
    # Tageslicht: Sonne durch das Fenster links hinten (zusaetzlich zur Fensterflaeche aus room())
    S = bpy.data.lights.new('Sonne', 'SUN'); S.energy = 1.6; S.angle = math.radians(4); S.color = (1.0, 0.96, 0.9)
    so = bpy.data.objects.new('Sonne', S); sc.collection.objects.link(so)
    so.rotation_euler = (Vector((0, 0, 0)) - Vector((-0.8, 0.35, 0.75))).to_track_quat('-Z', 'Y').to_euler()
    lp = find_node(env['leaf'].node_tree, 'BSDF_PRINCIPLED'); setin(lp, 0.5, 'Roughness')
    setin(lp, (0.045, 0.19, 0.035, 1), 'Base Color')
    big_pot(env, (0, 0), d_top=200.0, h=180.0, soil_z=SOIL)
    pilea(env, base=(-30, 26, SOIL), seed=11, n_leaves=15, scale=1.25)
    root, objs = sensor('', led)
    root.location = Vector((S_POS[0], S_POS[1], SOIL + GAP_SOIL)) * MM
    root.rotation_euler = (0, 0, math.radians(S_ROT))
    clear_leaves(root)
    return root


def cam_1(root):
    hc = root.matrix_world @ (Vector((0, 6.5, 30)) * MM)
    c = camera('Cam_Topf', (0.27, -0.56, 0.43), (0.012, -0.01, 0.225), lens=50, fstop=8.0)
    c.data.dof.focus_distance = (hc - c.location).length
    return c


def cam_2(root):
    hc = root.matrix_world @ (Vector((0, 0, 36)) * MM)
    c = camera('Cam_Nah', hc + Vector((0.12, -0.185, 0.105)), hc + Vector((-0.012, 0.004, -0.012)), lens=60, fstop=5.6)
    c.data.dof.focus_distance = (root.matrix_world @ (Vector((0, 0, 44)) * MM) - c.location).length
    return c


def run(jobs, samples=None, pct=100):
    times = {}
    for j in jobs:
        if j == '1':
            r = build_topf('gruen'); c = cam_1(r)
            settings((2000, 1500), samples or 1024, exposure=-0.9)
            bpy.context.scene.render.resolution_percentage = pct
            times[j] = render(os.path.join(OUTF, 'fluidi_01_topf_led_gruen.png'), c)
        elif j == '2':
            r = build_topf('blau'); c = cam_2(r)
            settings((2000, 1334), samples or 1536, exposure=-0.9)
            bpy.context.scene.render.resolution_percentage = pct
            times[j] = render(os.path.join(OUTF, 'fluidi_02_nah_led_blau.png'), c)
    print('ZEITEN', times, flush=True)


if bpy.app.background and '--' in sys.argv:
    a = batch_args()
    jobs = [x for x in sys.argv[sys.argv.index('--') + 1:] if x in ('1', '2')]
    run(jobs, a['samples'], a['pct'])
