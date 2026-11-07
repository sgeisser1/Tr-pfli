"""fluidi Phase 4 – Proportionsstudie Sensorkopf P3 (Entscheidungshilfe Auftraggeber).

Ausgangslage: Die Elektronik passt nicht in den freigegebenen Kopf 28 x 13 x 48 mm (D-010). Der Kopf wird höher
und/oder breiter. Die Farbfuge blau/grau (mit LED-Tropfen) muss nicht an der inneren Dichtung liegen: die graue
Hülse darf als Sichtschale über den dichten Kern hinaufreichen, die Fuge wird auf die optisch beste Höhe gelegt.
Tiefe 13 mm, Unterseite (Schraube, Sondenschlitz, Sonde 20 mm, 5 mm Abstand zur Erde) unverändert.
Machbare Kombinationen B x H: Überschlag Projektleiter, ANNAHME +-2 mm.

Geometrie, Materialien und Szene unverändert aus fluidi_p3v2.py / render_p3v2.py (freigegebene Fassung):
Grundriss mit Fasen 2.5 / 1.0 mm, Sichtfuge 0.3 mm, LED-Tropfen r 2.5 mm (Spitze 6.0 mm über der Mitte, Mitte
0.4 mm über der Fuge), Taste 9 x 6 mm. Je Variante geändert: Breite, Höhe, Fugenhöhe; Logo (Wortmarke Ton in Ton)
skaliert mit der Breite (16 mm bei 28 mm), Lage bei 39 % der Hülsenhöhe wie im freigegebenen Kopf (z 14.5 / 37).

Stapel (reproduzierbar, ohne Oberfläche):
    blender -b --factory-startup --python renders/gen/render_proportions.py -- aufstellung topf nah vergleich
    Optionen: --samples N (Standard 384), --pct P (Auflösung in %, Standard 100), --nah V4,V5 (Varianten Nahaufnahme)
Ausgabe: renders/phase4_prop/*.png. Cycles CPU, OHNE Denoiser (use_denoising = False, fluidi_lib.render_settings).
"""
import bpy, math, os, sys
from mathutils import Vector

_argv = sys.argv
sys.argv = [_argv[0]]                       # verhindert den Stapelteil von render_p3v2 beim exec
exec(open('/home/sgeisser/git/Tr-pfli/renders/gen/render_p3v2.py').read())
sys.argv = _argv

OUT4 = os.path.join(REPO, 'renders/phase4_prop')
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'

# Name, Kurztext, Breite, Höhe, Fuge (= Unterkante Kappe; Hülse endet 0.3 mm tiefer)
VARIANTS = {
    'V0': ('Referenz (freigegeben)', 28.0, 48.0, 37.0),
    'V1': ('Fuge wie heute', 28.0, 62.0, 37.0),
    'V2': ('Fuge hoch, Verhältnis wie V0', 28.0, 62.0, 47.8),
    'V3': ('breiter', 32.0, 59.0, 45.0),
    'V4': ('breiter', 34.0, 57.5, 43.5),
    'V5': ('am breitesten', 38.0, 55.5, 41.5),
}
LOGO_W0, LOGO_Z_REL = 16.0, 14.5 / 37.0


def kappe_pct(v):
    _, W, H, F = VARIANTS[v]
    return 100.0 * (H - F) / H


def set_variant(v):
    """Globale Masse von fluidi_p3v2 auf Variante v setzen (head_p3v2 liest sie beim Aufruf)."""
    global W3, H3, Z_FUGE, LED_Z
    _, W, H, F = VARIANTS[v]
    W3, H3, Z_FUGE, LED_Z = W, H, F, F + 0.4
    plan3.__defaults__ = (0.0, W3, D3, 2.5, 1.0)   # Standardwerte von plan3 sind bei der Definition gebunden


def head_var(v, led='gruen', tag=''):
    set_variant(v)
    r = head_p3v2('grau1', led, tag=tag)
    lg = bpy.data.objects['Logo' + tag]
    f = W3 / 28.0
    lg.scale = (f, f, 1.0)
    lg.location.z = LOGO_Z_REL * Z_FUGE * MM
    return r


# ----------------------------------------------------------------------------- 1 Aufstellung
SPACING = 54.0
LINE_X = {v: (i - 2.5) * SPACING for i, v in enumerate(VARIANTS)}
PLINTH_TOP = 40.0                           # Erdoberfläche; Kopfunterkante 5 mm darüber
ORTHO = 360.0
CAM_Z = 66.0


def build_aufstellung(samples=384):
    new_scene('fluidi_proportionen')
    studio(key=16.0)
    env = env_mats()
    plinth = mat_simple('Sockel', (0.70, 0.69, 0.66), rough=0.8, spec=0.3)
    box('Sockel', -175, 175, -30, 30, 0, PLINTH_TOP - 4, plinth, bevel=1.0)
    box('Erde_Streifen', -173, 173, -28, 28, PLINTH_TOP - 4, PLINTH_TOP, env['soil'], bevel=0.8)
    for v in VARIANTS:
        r = head_var(v, 'gruen', tag='_' + v)
        r.location = Vector((LINE_X[v], 0, PLINTH_TOP + GAP_SOIL)) * MM
    cam_d = cam_def()
    c = bpy.data.cameras.new('Cam_Aufstellung'); c.type = 'ORTHO'; c.ortho_scale = ORTHO * MM
    cam = bpy.data.objects.new('Cam_Aufstellung', c); bpy.context.scene.collection.objects.link(cam)
    cam.location, tgt = cam_d
    cam.rotation_euler = (tgt - cam.location).to_track_quat('-Z', 'Y').to_euler()
    render_settings((2400, 1000), samples)
    return cam


def cam_def(elev=6.0):
    tgt = Vector((0, 0, CAM_Z)) * MM
    d = Vector((0, -math.cos(math.radians(elev)), math.sin(math.radians(elev))))
    return tgt + d * 0.8, tgt


def label_aufstellung(path):
    """Beschriftung (Variante, B x H, Fuge/Kappe) per PIL unter jedem Kopf auf den Sockel."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(path).convert('RGB')
    Wp, Hp = im.size
    loc, tgt = cam_def()
    fwd = (tgt - loc).normalized()
    right = Vector((1, 0, 0))
    up = right.cross(fwd).normalized()
    sc = Wp / (ORTHO * MM)
    def px(p):
        q = Vector(p) * MM - tgt
        return Wp / 2 + q.dot(right) * sc, Hp / 2 - q.dot(up) * sc
    dr = ImageDraw.Draw(im)
    k = Wp / 2400.0
    f1 = ImageFont.truetype(FONT_B, round(30 * k))
    f2 = ImageFont.truetype(FONT, round(22 * k))
    ink = (79, 75, 69)
    for v, (txt, W, H, F) in VARIANTS.items():
        x, y = px((LINE_X[v], -30, 26))
        l1 = f'{v}  {W:g} × {H:g} mm'
        l2 = f'Fuge {F:g} mm · Kappe {kappe_pct(v):.0f} %'
        for s, f, dy in ((l1, f1, 0), (l2, f2, 40 * k), (txt, f2, 70 * k)):
            w = dr.textlength(s, font=f)
            dr.text((x - w / 2, y + dy), s, font=f, fill=ink)
    im.save(path)
    return path


def clear_leaves(head, W=38.0, H=62.0, margin=2.0):
    """Blätter, die in den Raum des GRÖSSTEN Kopfes (38 x 13 x 62 mm, alle Varianten gleich) ragen würden, samt
    Stiel ausblenden. Ein echtes Blatt würde ausweichen; so bleibt die Pflanze für V1 ... V5 identisch.
    (Im freigegebenen Bild p3v2_topf_grau1 ist das betroffene Blatt noch vorhanden; V0 wird hier ohne es neu gerendert.)"""
    bpy.context.view_layer.update()
    inv = head.matrix_world.inverted()
    dg = bpy.context.evaluated_depsgraph_get()
    hidden = []
    for o in bpy.context.scene.objects:
        if not o.name.startswith('Blatt'):
            continue
        me = o.evaluated_get(dg).to_mesh()
        hit = False
        for v in me.vertices:
            q = inv @ (o.matrix_world @ v.co) / MM
            if abs(q.x) < W / 2 + margin and abs(q.y) < D3 / 2 + margin and -margin < q.z < H + margin:
                hit = True; break
        o.evaluated_get(dg).to_mesh_clear()
        if hit:
            o.hide_render = True; hidden.append(o.name)
            st = bpy.context.scene.objects.get('Stiel' + o.name[5:])
            if st:
                st.hide_render = True
    print('ausgeblendet (Kollision mit Kopf):', hidden, flush=True)
    return hidden


# ----------------------------------------------------------------------------- 2 Topf (Kamera wie p3v2_topf_grau1)
def build_topf_var(v, samples=384):
    new_scene('fluidi_topf_' + v)
    env = env_mats()
    room(env)
    pot(env, (0, 0), soil_z=SOIL)
    pilea(env, base=(-8, 12, SOIL), seed=11, scale=0.85)
    a = head_var(v, 'gruen')
    a.location = Vector((S_POS[0], S_POS[1], SOIL + GAP_SOIL)) * MM
    a.rotation_euler = (0, 0, math.radians(S_ROT))
    clear_leaves(a)
    hc = Vector((S_POS[0], S_POS[1], SOIL + GAP_SOIL + 24)) * MM          # Fokus wie v2 (gleiche Kamera)
    ct = camera('Cam_Topf', (0.13, -0.31, 0.235), (0.022, -0.016, 0.128), lens=62, fstop=5.6)
    ct.data.dof.focus_distance = (hc - ct.location).length
    render_settings((1600, 1200), samples)
    return ct


# ----------------------------------------------------------------------------- 3 Nahaufnahme 3/4 (wie p3v2_nah)
def build_nah_var(v, samples=512):
    new_scene('fluidi_nah_' + v)
    env = env_mats()
    room(env)
    pot(env, (0, 0), soil_z=SOIL)
    pilea(env, base=(-8, 12, SOIL), seed=11, scale=0.85)
    a = head_var(v, 'gruen')
    a.location = Vector((S_POS[0], S_POS[1], SOIL + GAP_SOIL)) * MM
    a.rotation_euler = (0, 0, math.radians(S_ROT))
    clear_leaves(a)
    hc = Vector((S_POS[0], S_POS[1], SOIL + GAP_SOIL + H3 * 0.58)) * MM
    c = camera('Cam_Nah', hc + Vector((0.07, -0.16, 0.075)) * 1.22, hc, lens=70, fstop=8.0)
    render_settings((1600, 1200), samples)
    hide_occluders(c, hc)
    return c


def side_by_side(files, labels, out, crop_w=None):
    """Bilder nebeneinander (optional mittig beschnitten), Beschriftung oben links (PIL)."""
    from PIL import Image, ImageDraw, ImageFont
    ims = [Image.open(f).convert('RGB') for f in files]
    w, h = ims[0].size
    cw = crop_w or w
    x0 = (w - cw) // 2
    gap = 12
    s = Image.new('RGB', (cw * len(ims) + gap * (len(ims) - 1), h), (255, 255, 255))
    dr = ImageDraw.Draw(s)
    f = ImageFont.truetype(FONT_B, max(22, h // 30))
    for k, (im, lab) in enumerate(zip(ims, labels)):
        s.paste(im.crop((x0, 0, x0 + cw, h)), (k * (cw + gap), 0))
        dr.text((k * (cw + gap) + 24, 18), lab, font=f, fill=(79, 75, 69))
    s.save(out)
    return out


def vergleich_topf():
    """Ausschnitt der Topfbilder V0 ... V5 (gleiche Kamera wie p3v2_topf_grau1) nebeneinander."""
    from PIL import Image
    files = [os.path.join(OUT4, f'prop_topf_{v}.png') for v in VARIANTS]
    tmp = []
    for f in files:                             # Ausschnitt um den Kopf (x 560 ... 1200, y 100 ... 900)
        p = os.path.join(OUT4, '_crop_' + os.path.basename(f))
        Image.open(f).convert('RGB').crop((600, 120, 1160, 860)).save(p)
        tmp.append(p)
    labs = [f'{v}  {VARIANTS[v][1]:g} × {VARIANTS[v][2]:g}' for v in VARIANTS]
    out = side_by_side(tmp, labs, os.path.join(OUT4, 'prop_topf_vergleich.png'))
    for p in tmp:
        os.remove(p)
    return out


def run4(jobs, samples=384, pct=100, nah=('V4', 'V5')):
    os.makedirs(OUT4, exist_ok=True)
    done = []
    for job in jobs:
        if job == 'aufstellung':
            cam = build_aufstellung(samples)
            bpy.context.scene.render.resolution_percentage = pct
            p = render_to(os.path.join(OUT4, 'prop_aufstellung.png'), cam)
            done.append(label_aufstellung(p))
        elif job == 'topf' or job.startswith('topf_'):
            vs = [job[5:]] if job.startswith('topf_') else list(VARIANTS)
            for v in vs:
                cam = build_topf_var(v, samples)
                bpy.context.scene.render.resolution_percentage = pct
                done.append(render_to(os.path.join(OUT4, f'prop_topf_{v}.png'), cam))
                print('fertig', v, flush=True)
        elif job == 'nah':
            files = []
            for v in nah:
                cam = build_nah_var(v, int(samples * 1.3))
                bpy.context.scene.render.resolution_percentage = pct
                files.append(render_to(os.path.join(OUT4, f'prop_nah_{v}.png'), cam))
            labs = [f'{v}  {VARIANTS[v][1]:g} × {VARIANTS[v][2]:g} mm' for v in nah]
            done += files
            done.append(side_by_side(files, labs, os.path.join(OUT4, 'prop_nah_' + '_'.join(nah) + '.png'), crop_w=1000))
        elif job == 'vergleich':
            done.append(vergleich_topf())
        else:
            print('unbekannt', job)
        print('fertig', job, flush=True)
    return done


if bpy.app.background and '--' in sys.argv:
    import time
    argv = sys.argv[sys.argv.index('--') + 1:]
    samples, pct, nah = 384, 100, ('V4', 'V5')
    if '--samples' in argv:
        i = argv.index('--samples'); samples = int(argv[i + 1]); del argv[i:i + 2]
    if '--pct' in argv:
        i = argv.index('--pct'); pct = int(argv[i + 1]); del argv[i:i + 2]
    if '--nah' in argv:
        i = argv.index('--nah'); nah = tuple(argv[i + 1].split(',')); del argv[i:i + 2]
    for j in argv or ['aufstellung', 'topf', 'nah', 'vergleich']:
        t = time.time()
        print(run4([j], samples, pct, nah), 'Zeit %.0f s' % (time.time() - t), flush=True)
