"""fluidi Phase 3, Verfeinerung 2 – Gateway G1 v3 (LED-Tropfen "tropft" aus dem blauen Deckel wie am Sensor)
und Familienbild mit drei Sensoren (Warmgrau hell #B9B5AC, freigegeben D-010).

Stapel (reproduzierbar, ohne Oberfläche):
    blender -b --factory-startup --python renders/gen/render_p3v3.py -- gateway familie
    Optionen: --samples N (Standard 384), --pct P (Auflösung in %, Standard 100)
Ausgabe: renders/phase3_v3/g1v3_gateway.png, g1v3_familie_3sensoren.png (+ .blend).
Cycles CPU, OHNE Denoiser (use_denoising = False, gesetzt in fluidi_lib.render_settings).

Gateway G1 v3 (Masse wie G1 v2: 62 x 40 x 20 mm, Fuge z 14.0 +- 0.15, Frontfacette 45° von z 11 bis z 20):
  LED-Tropfen in GLEICHER Geometrie wie am Sensor (drop2: r 2.5 mm, Spitze 6.0 mm über der Mitte, Mitte
  0.4 mm über der Fuge), hier in der Ebene der 45°-Facette: Fuge liegt auf der Facette 4.24 mm (schräg gemessen)
  über der Unterkante der Facette -> Tropfenbauch reicht bis 2.14 mm über die Facettenkante, Spitze bis 10.64 mm
  (Facette 12.73 mm lang). Fenster im Deckel exakt, Kerbe in der Wanne 0.3 mm grösser (wie Hülse am Sensor).
  Lage x = +21 mm (rechts, wie G1 v2). Logo Ton in Ton (Relief 0.2 mm), ohne Stabantenne (FPC innen, D-009).
"""
import bpy, math, os, sys
from mathutils import Vector

_argv = sys.argv
sys.argv = [_argv[0]]                       # verhindert den Stapelteil von render_p3v2 beim exec
exec(open('/home/sgeisser/git/Tr-pfli/renders/gen/render_p3v2.py').read())
sys.argv = _argv

OUT3 = os.path.join(REPO, 'renders/phase3_v3')
G_FUGE = 14.0
G_FACET0 = 11.0                             # Facette beginnt bei z = Hg - 9


def gateway_g1v3(grey='grau1', led_state='gruen', logo='fluidi_A_linie_mono.svg', tag=''):
    root = bpy.data.objects.new('G1v3' + tag, None); bpy.context.scene.collection.objects.link(root)
    m = mats_v2(grey)
    Wg, Dg, Hg = 62.0, 40.0, 20.0
    zf = G_FUGE
    prof = [(-Dg / 2, 0), (Dg / 2, 0), (Dg / 2, Hg), (-Dg / 2 + 9, Hg), (-Dg / 2, Hg - 9)]
    low = prism('G1_Wanne' + tag, prof, 'x', -Wg / 2, Wg / 2, 3.0, 3.0, m['body'], root, bevel=0.4)
    cut(low, box('G1_ob' + tag, -40, 40, -30, 30, zf - 0.15, 40, None, root))
    up = prism('G1_Deckel' + tag, prof, 'x', -Wg / 2, Wg / 2, 3.0, 3.0, m['blue'], root, bevel=0.4)
    cut(up, box('G1_un' + tag, -40, 40, -30, 30, -5, zf + 0.15, None, root))
    # Facettenpunkt auf Fugenhöhe: y = -Dg/2 + (zf - 11), z = zf. Lokales System: x quer, y die Facette hinauf, z Normale.
    origin = Vector((21.0, -Dg / 2 + (zf - G_FACET0), zf)) * MM
    c_up = 0.4 * math.sqrt(2)                 # Mitte 0.4 mm (senkrecht) über der Fuge -> schräg 0.57 mm
    dp = drop2(0, c_up, LED_R)
    notch = drop2(0, c_up, LED_R + GAP_F, k=(LED_K * LED_R + GAP_F) / (LED_R + GAP_F))
    hole = prism('G1_LEDloch' + tag, dp, 'z', -2.5, 3, parent=root, bevel=0)
    kerbe = prism('G1_Kerbe' + tag, notch, 'z', -2.0, 3, parent=root, bevel=0)
    led = prism('G1_LED' + tag, dp, 'z', -1.6, 0.0, mat=led_material('LED_G1' + tag, led_state), parent=root, bevel=0.3)
    for o in (hole, kerbe, led):
        o.rotation_euler = (math.radians(45.0), 0, 0)
        o.location = origin
    cut(up, hole)
    cut(low, kerbe)
    lg, _ = svg_obj('G1_Logo' + tag, logo, 22.0, m['logo'], root, extrude=0.2)
    on_front_xz(lg, -12.0, -Dg / 2, 5.4)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cyl(f'G1_Fuss{sx}{sy}' + tag, 3.0, -0.8, 0.2, center=(sx * 24, sy * 14), axis='z', mat=m['seal'], parent=root, bevel=0.3)
    usb_c(root, m, (-14, Dg / 2, 5.5))
    return root


def build_gateway3(grey='grau1', samples=384):
    new_scene('fluidi_gateway_v3')
    env = env_mats()
    room(env)
    g = gateway_g1v3(grey, 'gruen')
    g.location = Vector((0, 0, 0.8)) * MM
    g.rotation_euler = (0, 0, math.radians(18))
    cam = camera('Cam_Gateway', (0.10, -0.25, 0.12), (0.002, 0.0, 0.010), lens=82, fstop=18.0)
    cam.data.dof.focus_distance = (Vector((0.0, -0.012, 0.010)) - cam.location).length
    render_settings((1600, 1200), samples)
    return cam


def build_familie3(grey='grau1', samples=384, states=('gruen', 'gruen', 'blau')):
    """Gateway vorne, drei Sensoren (Warmgrau hell) auf einem Eichenständer, LED grün / grün / blau."""
    new_scene('fluidi_familie_v3')
    env = env_mats()
    room(env)
    stand = box('Staender', -75, 75, -14, 14, 0, 40, env['wood'], bevel=1.0)
    xs = [-48, 0, 48]
    for i, (x, st) in enumerate(zip(xs, states)):
        cut(stand, box(f'Schlitz{i}', x - PW / 2 - 0.5, x + PW / 2 + 0.5, -1.8, 1.0, 2, 45, None))
        r = head_p3v2(grey, st, tag=f'_{i}')
        r.location = Vector((x, 1.1, 2 + PROBE_L)) * MM
        r.rotation_euler = (0, 0, math.radians(-8))
    g = gateway_g1v3(grey, 'gruen')
    g.location = Vector((62, -52, 0.8)) * MM
    g.rotation_euler = (0, 0, math.radians(-16))
    pot(env, (-150, 120), soil_z=SOIL)
    pilea(env, base=(-150, 120, SOIL), seed=11, scale=0.85)
    cam = camera('Cam_Familie', (0.09, -0.50, 0.23), (0.005, -0.02, 0.085), lens=55, fstop=11.0)
    render_settings((1600, 1200), samples)
    return cam


def run3(jobs, samples=384, pct=100):
    os.makedirs(OUT3, exist_ok=True)
    done = []
    for job in jobs:
        if job == 'gateway':
            cam = build_gateway3('grau1', samples); name = 'g1v3_gateway'
        elif job == 'familie':
            cam = build_familie3('grau1', samples); name = 'g1v3_familie_3sensoren'
        else:
            print('unbekannt', job); continue
        bpy.context.scene.render.resolution_percentage = pct
        done.append(render_to(os.path.join(OUT3, name + '.png'), cam))
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT3, name + '.blend'), copy=True)
        print('fertig', job, flush=True)
    return done


if bpy.app.background and '--' in sys.argv:
    import time
    argv = sys.argv[sys.argv.index('--') + 1:]
    samples, pct = 384, 100
    if '--samples' in argv:
        i = argv.index('--samples'); samples = int(argv[i + 1]); del argv[i:i + 2]
    if '--pct' in argv:
        i = argv.index('--pct'); pct = int(argv[i + 1]); del argv[i:i + 2]
    for j in argv or ['gateway', 'familie']:
        t = time.time()
        print(run3([j], samples, pct), 'Zeit %.0f s' % (time.time() - t), flush=True)
