"""fluidi App-Icon (final, D-011): frontale Nahaufnahme des echten Sensormodells P3 v2 (Warmgrau hell #B9B5AC,
Kappe hellblau), LED-Tropfen blau leuchtend, gross und mittig; Fuge (Sichtspalt 0.3 mm) horizontal durch den
Tropfenbauch. Kappe oben und Hülse unten füllen das ganze Quadrat (keine Gehäusekanten, kein Hintergrund).

Stapel (reproduzierbar, ohne Oberfläche):
    blender -b --factory-startup --python renders/gen/render_app_icon.py -- [--samples N] [--res PX] [--out PFAD]
    Standard: 2048 x 2048 px, 1536 Samples (adaptiv, min. 256), Ausgabe renders/phase3_v3/app_icon_render_2048.png (+ .blend)
Cycles CPU, OHNE Denoiser (use_denoising = False, gesetzt in fluidi_lib.render_settings; hier zusätzlich
adaptives Sampling mit strengerer Schwelle 0.006).

Geometrie und Materialien: unverändert aus renders/gen/fluidi_p3v2.py (head_p3v2, mats_v2, led_material),
LED-Zustand 'blau' mit gleicher Stärke wie p3v2_nah_led_blau (7.0 x LED_GAIN['blau']).
Bildausschnitt (orthografische Kamera, frontal, Blick +y):
  Tropfen: Unterkante z 34.9, Spitze z 43.4 -> 8.5 mm hoch. Ausschnitt 15.6 mm -> Tropfen 54 % der Bildhöhe.
  Bildmitte z 39.0 (Tropfen-Bounding-Box-Mitte 39.15, leicht optisch zentriert wegen des Glühens unten)
  -> Bild z 31.2 ... 46.8: unter der oberen Fase der Kappe (ab z 47.0) und weit über dem Logo (z 14.5);
  x -7.8 ... +7.8, Frontfläche ohne Fasen reicht x -11.5 ... +11.5. Keine Gehäusekante im Bild.
Licht: grosse, weiche Flächenleuchte frontal leicht von oben (gibt der Fuge den dunklen Schattenstrich wie in
der Vorlage), schwächere Aufhellung von unten, Welt neutral hell. Keine Glanzlichter auf der matten ASA-Fläche.
"""
import bpy, math, os, sys
from mathutils import Vector

_argv = sys.argv
sys.argv = [_argv[0]]                       # verhindert den Stapelteil von render_p3v2 beim exec
exec(open('/home/sgeisser/git/Tr-pfli/renders/gen/render_p3v2.py').read())
sys.argv = _argv

OUT3 = os.path.join(REPO, 'renders/phase3_v3')
ICON_FRAME = 15.6       # mm Bildbreite = Bildhöhe
ICON_ZC = 39.0          # mm Bildmitte (Kopfkoordinaten)


def area_light(name, loc, target, size, energy, col=(1, 1, 1)):
    L = bpy.data.lights.new(name, 'AREA'); L.shape = 'RECTANGLE'; L.size = size[0]; L.size_y = size[1]
    L.energy = energy; L.color = col
    o = bpy.data.objects.new(name, L); bpy.context.scene.collection.objects.link(o)
    o.location = Vector(loc)
    o.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    return o


def build_icon(samples=1536, res=2048):
    new_scene('fluidi_app_icon')
    a = head_p3v2('grau1', 'blau')
    a.location = (0, 0, 0)
    tgt = Vector((0, -D3 / 2, ICON_ZC)) * MM
    # weiche Frontleuchte, 25° von oben; Aufhellung von unten; beide gross gegenüber dem Motiv
    area_light('Key', tgt + Vector((0, -0.30, 0.14)), tgt, (0.40, 0.30), 3.3, (1.0, 0.95, 0.88))
    area_light('Fill', tgt + Vector((0, -0.30, -0.10)), tgt, (0.40, 0.20), 0.9, (0.95, 0.97, 1.0))
    wd = bpy.data.worlds.new('Welt_Icon'); bpy.context.scene.world = wd
    wd.use_nodes = True
    bg = find_node(wd.node_tree, 'BACKGROUND')
    bg.inputs[0].default_value = (0.80, 0.80, 0.80, 1); bg.inputs[1].default_value = 0.13
    cd = bpy.data.cameras.new('Cam_Icon'); cd.type = 'ORTHO'; cd.ortho_scale = ICON_FRAME * MM
    cd.clip_start = 0.01; cd.clip_end = 1.0
    cam = bpy.data.objects.new('Cam_Icon', cd); bpy.context.scene.collection.objects.link(cam)
    cam.location = tgt + Vector((0, -0.25, 0))
    cam.rotation_euler = (math.radians(90), 0, 0)          # Blick +y, oben = +z
    render_settings((res, res), samples)
    sc = bpy.context.scene
    sc.cycles.adaptive_threshold = 0.006
    sc.cycles.adaptive_min_samples = 256
    sc.cycles.sample_clamp_indirect = 1.0
    sc.cycles.filter_width = 1.5
    return cam


if bpy.app.background and '--' in sys.argv:
    import time
    argv = sys.argv[sys.argv.index('--') + 1:]
    opts = {'--samples': 1536, '--res': 2048, '--out': os.path.join(OUT3, 'app_icon_render_2048.png')}
    for k in list(opts):
        if k in argv:
            i = argv.index(k); opts[k] = type(opts[k])(argv[i + 1])
    t = time.time()
    cam = build_icon(opts['--samples'], opts['--res'])
    os.makedirs(os.path.dirname(opts['--out']), exist_ok=True)
    render_to(opts['--out'], cam)
    if opts['--out'].startswith(OUT3):
        bpy.ops.wm.save_as_mainfile(filepath=os.path.splitext(opts['--out'])[0] + '.blend', copy=True)
    print('fertig', opts['--out'], 'Zeit %.0f s' % (time.time() - t), flush=True)
