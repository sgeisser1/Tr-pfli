"""fluidi Phase 3, Verfeinerung 1 – Renderings P3 "Stele" (Hülse, grau + hellblau) und Gateway G1 v2.

Stapel (reproduzierbar, ohne Oberfläche):
    blender -b --factory-startup --python renders/gen/render_p3v2.py -- topf1 topf2 vergleich nah explosion unten gateway familie
    Optionen: --samples N (Standard 384), --pct P (Auflösung in %, Standard 100)
Interaktiv (MCP/Texteditor): exec(open('.../render_p3v2.py').read()); build_topf('grau1') ...
Ausgabe: renders/phase3_v2/*.png (+ .blend je Szene). Cycles CPU, OHNE Denoiser (use_denoising = False).
Geometrie: renders/gen/fluidi_p3v2.py (Masse aus docs/reviews/phase3_sleeve_mechanik.md, Variante 28/20).
"""
import bpy, math, os, sys
from mathutils import Vector, Euler, Matrix

exec(open('/home/sgeisser/git/Tr-pfli/renders/gen/fluidi_p3v2.py').read())

SOIL = 115.0
S_POS = (36.0, -30.0)
S_ROT = -18.0


def save_blend(name):
    os.makedirs(OUT2, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT2, name + '.blend'), copy=True)


# ----------------------------------------------------------------------------- 1/2 Topf
def build_topf(grey='grau1', samples=384, led='gruen'):
    new_scene('fluidi_topf_' + grey)
    env = env_mats()
    room(env)
    pot(env, (0, 0), soil_z=SOIL)
    pilea(env, base=(-8, 12, SOIL), seed=11, scale=0.85)
    a = head_p3v2(grey, led)
    a.location = Vector((S_POS[0], S_POS[1], SOIL + GAP_SOIL)) * MM
    a.rotation_euler = (0, 0, math.radians(S_ROT))
    hc = Vector((S_POS[0], S_POS[1], SOIL + GAP_SOIL + 24)) * MM
    ct = camera('Cam_Topf', (0.13, -0.31, 0.235), (0.022, -0.016, 0.128), lens=62, fstop=5.6)
    ct.data.dof.focus_distance = (hc - ct.location).length
    render_settings((1600, 1200), samples)
    return ct


# ----------------------------------------------------------------------------- 3 Nahaufnahme LED
def build_nah(grey='grau1', samples=512):
    new_scene('fluidi_nah')
    env = env_mats()
    room(env)
    pot(env, (0, 0), soil_z=SOIL)
    pilea(env, base=(-8, 12, SOIL), seed=11, scale=0.85)
    a = head_p3v2(grey, 'gruen')
    a.location = Vector((S_POS[0], S_POS[1], SOIL + GAP_SOIL)) * MM
    a.rotation_euler = (0, 0, math.radians(S_ROT))
    hc = Vector((S_POS[0], S_POS[1], SOIL + GAP_SOIL + 26)) * MM
    c = camera('Cam_Nah', hc + Vector((0.07, -0.16, 0.075)), hc + Vector((0, 0, 0.0)), lens=70, fstop=8.0)
    render_settings((1600, 1200), samples)
    hide_occluders(c, hc)
    return c


# ----------------------------------------------------------------------------- 4 Explosion / 5 Unterseite
def build_explosion(grey='grau1', samples=384):
    """Kern (Kappe + Schott + Platine + Kragen) schwebt senkrecht, Rückseite (Zelle) zur Kamera, Zelle 9 mm
    seitlich aus dem Clip geschoben. Die Hülse ist über die Sondenspitze abgezogen und
    schwebt neben der Spitze, Öffnung schräg zur Kamera: innen sieht man das Warnsymbol (Rückwand) und den Schraubenschaft."""
    new_scene('fluidi_explosion')
    studio(key=16.0)
    a = head_p3v2(grey, None, cell_out=9.0)
    a.location = Vector((0, 0, 128)) * MM
    a.rotation_euler = (0, 0, math.radians(205))      # Rückseite (lokal +y) zur Kamera (-y)
    cam_loc, cam_tgt = Vector((0.12, -0.42, 0.25)), Vector((0.022, -0.01, 0.130))
    sg = bpy.data.objects['Huelse']
    sg.parent = None
    pos = Vector((0.046, -0.028, 0.094))
    to_cam = (cam_loc - pos).normalized()
    th = Vector((to_cam.x, to_cam.y, 0)).normalized()
    zl = (Vector((0, 0, 1)) + 0.9 * th).normalized()       # Öffnung nach oben, ca. 42° zur Kamera gekippt
    yl = (-th - zl * (-th).dot(zl)).normalized()           # Rückwand auf der kamerafernen Seite
    xl = yl.cross(zl)
    sg.matrix_world = Matrix(((xl.x, yl.x, zl.x, pos.x), (xl.y, yl.y, zl.y, pos.y), (xl.z, yl.z, zl.z, pos.z), (0, 0, 0, 1)))
    ink = mat_simple('Pfeil', (0.10, 0.11, 0.12), rough=0.6)
    # Pfeile: Hülse nach unten über die Sonde abziehen, Zelle seitlich (+x) herausschieben
    arrow('Pfeil_ab', (-15, 2, -6), (-15, 2, -34), width=1.4, head=4.5, mat=ink, parent=a, normal=(0, 1, 0))
    arrow('Pfeil_Zelle', (14, 6, Z_CELL + 13), (25, 6, Z_CELL + 13), width=1.2, head=3.5, mat=ink, parent=a, normal=(0, 1, 0))
    cam = camera('Cam_Explosion', tuple(cam_loc), tuple(cam_tgt), lens=98, fstop=16.0)
    render_settings((1600, 1200), samples)
    return cam


def build_unten(grey='grau1', samples=384):
    """Kopf steht kopfüber auf der Kappe, Sonde zeigt nach oben; Blick auf die Bodenfläche mit der
    unverlierbaren Schraube M2 (Kreuzschlitz) und dem Sondenschlitz."""
    new_scene('fluidi_unten')
    studio(key=16.0)
    a = head_p3v2(grey, None)
    a.rotation_euler = (math.radians(180), 0, math.radians(160))
    a.location = Vector((0, 0, H3 + 0.6)) * MM            # steht auf der Taste/Kappe
    cam = camera('Cam_Unten', (0.055, 0.095, 0.150), (0.0, 0.001, 0.044), lens=72, fstop=14.0)
    render_settings((1600, 1200), samples)
    return cam


# ----------------------------------------------------------------------------- 6 Gateway / Familie
def build_gateway(grey='grau1', samples=384):
    new_scene('fluidi_gateway')
    env = env_mats()
    room(env)
    g = gateway_g1v2(grey, 'gruen')
    g.location = Vector((0, 0, 0.8)) * MM
    g.rotation_euler = (0, 0, math.radians(18))
    cam = camera('Cam_Gateway', (0.10, -0.25, 0.12), (0.002, 0.0, 0.010), lens=82, fstop=18.0)
    cam.data.dof.focus_distance = (Vector((0.0, -0.012, 0.010)) - cam.location).length
    render_settings((1600, 1200), samples)
    return cam


def build_familie(grey='grau1', samples=384):
    """Gateway vorne, drei Sensoren auf einem Eichenständer (Schlitze 40 mm), LED grün / blau / rot."""
    new_scene('fluidi_familie')
    env = env_mats()
    room(env)
    stand = box('Staender', -75, 75, -14, 14, 0, 40, env['wood'], bevel=1.0)
    xs = [-48, 0, 48]
    for i, (x, st) in enumerate(zip(xs, ('gruen', 'blau', 'rot'))):
        cut(stand, box(f'Schlitz{i}', x - PW / 2 - 0.5, x + PW / 2 + 0.5, -1.8, 1.0, 2, 45, None))
        r = head_p3v2(grey, st, tag=f'_{i}')
        r.location = Vector((x, 1.1, 2 + PROBE_L)) * MM
        r.rotation_euler = (0, 0, math.radians(-8))
    g = gateway_g1v2(grey, 'gruen')
    g.location = Vector((62, -52, 0.8)) * MM
    g.rotation_euler = (0, 0, math.radians(-16))
    pot(env, (-150, 120), soil_z=SOIL)
    pilea(env, base=(-150, 120, SOIL), seed=11, scale=0.85)
    cam = camera('Cam_Familie', (0.09, -0.50, 0.23), (0.005, -0.02, 0.085), lens=55, fstop=11.0)
    render_settings((1600, 1200), samples)
    return cam


# ----------------------------------------------------------------------------- Rendern
def triptych(files, out, labels):
    """Drei Nahaufnahmen nebeneinander (Ausschnitt), mit Beschriftung (PIL ausserhalb Blender nicht nötig:
    numpy über Blender-Bilder)."""
    import numpy as np
    ims = [bpy.data.images.load(f, check_existing=False) for f in files]
    w, h = ims[0].size
    cw = w // 3 + 120                    # Ausschnitt um die Bildmitte
    x0 = (w - cw) // 2
    buf = np.ones((h, cw * 3 + 2 * 8, 4), dtype=np.float32)
    for k, im in enumerate(ims):
        a = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        buf[:, k * (cw + 8):k * (cw + 8) + cw] = a[:, x0:x0 + cw]
    s = bpy.data.images.new('trip', buf.shape[1], h); s.pixels[:] = buf.ravel()
    s.filepath_raw = out; s.file_format = 'PNG'; s.save()
    for im in ims:
        bpy.data.images.remove(im)
    bpy.data.images.remove(s)
    return out


def run(jobs, samples=384, pct=100):
    os.makedirs(OUT2, exist_ok=True)
    done = []
    for job in jobs:
        if job in ('topf1', 'topf2'):
            g = 'grau1' if job == 'topf1' else 'grau2'
            cam = build_topf(g, samples)
            bpy.context.scene.render.resolution_percentage = pct
            done.append(render_to(os.path.join(OUT2, f'p3v2_topf_{g}.png'), cam))
            save_blend(f'p3v2_topf_{g}')
        elif job == 'nah':
            cam = build_nah('grau1', int(samples * 1.3))
            bpy.context.scene.render.resolution_percentage = pct
            files = []
            for st in ('gruen', 'blau', 'rot'):
                set_led_state(st, 7.0)
                files.append(render_to(os.path.join(OUT2, f'p3v2_nah_led_{st}.png'), cam))
            done += files
            done.append(triptych(files, os.path.join(OUT2, 'p3v2_nah_led_triptychon.png'), ('grün', 'blau', 'rot')))
            save_blend('p3v2_nah')
        elif job == 'vergleich':                    # Grau 1 | Grau 2 nebeneinander (aus topf1/topf2)
            import numpy as np
            ims = [bpy.data.images.load(os.path.join(OUT2, f'p3v2_topf_{g}.png'), check_existing=False) for g in ('grau1', 'grau2')]
            w, h = ims[0].size
            buf = np.ones((h, 2 * w + 16, 4), dtype=np.float32)
            for k, im in enumerate(ims):
                buf[:, k * (w + 16):k * (w + 16) + w] = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
            s_ = bpy.data.images.new('vgl', 2 * w + 16, h); s_.pixels[:] = buf.ravel()
            s_.filepath_raw = os.path.join(OUT2, 'p3v2_topf_vergleich_grau1_grau2.png'); s_.file_format = 'PNG'; s_.save()
            done.append(s_.filepath_raw)
        elif job == 'explosion':
            cam = build_explosion('grau1', samples)
            bpy.context.scene.render.resolution_percentage = pct
            done.append(render_to(os.path.join(OUT2, 'p3v2_batteriewechsel_explosion.png'), cam))
            save_blend('p3v2_explosion')
        elif job == 'unten':
            cam = build_unten('grau1', samples)
            bpy.context.scene.render.resolution_percentage = pct
            done.append(render_to(os.path.join(OUT2, 'p3v2_unterseite_schraube.png'), cam))
            save_blend('p3v2_unten')
        elif job == 'gateway':
            cam = build_gateway('grau1', samples)
            bpy.context.scene.render.resolution_percentage = pct
            done.append(render_to(os.path.join(OUT2, 'g1v2_gateway.png'), cam))
            save_blend('g1v2_gateway')
        elif job == 'familie':
            cam = build_familie('grau1', samples)
            bpy.context.scene.render.resolution_percentage = pct
            done.append(render_to(os.path.join(OUT2, 'g1v2_familie_3sensoren.png'), cam))
            save_blend('g1v2_familie')
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
    for j in argv or ['topf1', 'topf2', 'vergleich', 'nah', 'explosion', 'unten', 'gateway', 'familie']:
        t = time.time()
        print(run([j], samples, pct), 'Zeit %.0f s' % (time.time() - t), flush=True)
