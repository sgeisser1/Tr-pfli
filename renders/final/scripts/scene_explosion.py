"""fluidi Phase 4e - Bild 3 Explosionsansicht und Bild 4 Batteriewechsel (Detail Kopf).

  3 fluidi_03_explosion.png         alle Teile aus den CAD-Meshes, auseinandergezogen, Beschriftung per PIL
  4 fluidi_04_batteriewechsel.png   Huelse halb nach unten abgezogen (mit Schraube), Zelle sichtbar

Verschiebungen (mm, Kopfkoordinaten). Die Platine geht mit Kragen, Verguss, Mutter, O-Ring Kragen, Clip und Zelle
nach unten aus dem Kern (Kappe mit Zapfen und Schott), wie bei der Montage von unten eingeschoben (PCB_OUTLINE.md Kap. 2).
Stapel:  blender -b --factory-startup --python renders/final/scripts/scene_explosion.py -- 3 4 [--samples N] [--pct P]
"""
import sys, json
exec(open('/home/sgeisser/git/Tr-pfli/renders/final/scripts/final_lib.py').read())
from bpy_extras.object_utils import world_to_camera_view

DZ_PCB = -46.0
EXPLODE = {
    'Taste_blau': (0, 0, 42), 'Tastenteller': (0, 0, 42), 'Klemmring': (0, 0, 31), 'Membran_Silikon': (0, 0, 23),
    'Stoessel': (0, 0, 13),
    'Fenster_transluzent': (0, -22, -19),
    'PCB': (0, 0, DZ_PCB), 'Kragen': (0, 0, DZ_PCB), 'Verguss_Kragen': (0, 0, DZ_PCB), 'Mutter_M2': (0, 0, DZ_PCB),
    'ORing_Kragen': (0, 0, DZ_PCB), 'Schottkeil': (0, -3, -16), 'D1_LED': (0, 0, 0),
    'CR2032': (-34, -10, DZ_PCB),
    'Huelse_grau': (62, 0, -72), 'Schraube_M2': (62, 0, -72 - 22),
}
# Beschriftungen: Teil, Ankerpunkt (Kopfkoordinaten vor Verschiebung, mm), Text, Seite (L/R)
LABELS = [
    ('Taste_blau', (0, 5.5, 58.0), 'Taste', 'L'),
    ('Klemmring', (-4.0, 1.5, 55.8), 'Klemmring', 'L'),
    ('Membran_Silikon', (-4.6, 1.5, 54.5), 'Silikonmembran (Dichtung)', 'L'),
    ('Stoessel', (-5.5, 3.5, 52.5), 'Stössel', 'L'),
    ('Kappe_blau', (-17.0, 5, 52.0), 'Kappe = Kern (Zapfen, Schott, O-Ring)', 'L'),
    ('Fenster_transluzent', (2.0, 0.0, 47.0), 'LED-Fenster (Tropfen)', 'R'),
    ('Schottkeil', (11.0, 4.5, 31.4), 'Schottkeil', 'R'),
    ('PCB', (12.0, 6.6, 40.0), 'Platine mit Bauteilen (CC2340, LED, Taster)', 'R'),
    ('CR2032', (-7.0, 3.3, 18.7), 'Knopfzelle CR2032', 'L'),
    ('Kragen', (-15.0, 6.0, 4.0), 'Kragen mit Verguss, O-Ring, Mutter M2', 'L'),
    ('Huelse_grau', (17.0, 6.5, 30.0), 'Hülse (Batteriefach)', 'R'),
    ('Schraube_M2', (1.9, 4.2, -1.0), 'Schraube M2 × 3', 'R'),
    ('PCB', (10.0, 6.6, -80.0), 'Sonde (Platine, 100 mm in der Erde)', 'R'),
]


def build_explosion():
    reset()
    studio(floor_col=(0.80, 0.80, 0.79), key=14.0)
    root, objs = sensor('', 'gruen', explode=EXPLODE)
    # Explosionsbild: LED aus (Teile getrennt), Fenster naturweiss
    for m in bpy.data.materials:
        if m.name.startswith(('LED_Fenster', 'LED_Chip')):
            setin(find_node(m.node_tree, 'BSDF_PRINCIPLED'), 0.0, 'Emission Strength')
    for o in list(bpy.data.objects):
        if o.type == 'LIGHT' and o.name.startswith('LED'):
            bpy.data.objects.remove(o)
    root.location = Vector((0, 0, 168)) * MM
    root.rotation_euler = (0, 0, math.radians(26))
    return root


def cam_explosion(root):
    bpy.context.view_layer.update()
    tgt = root.matrix_world @ (Vector((12, 0, -25)) * MM)
    c = camera('Cam_Explosion', tgt + Vector((0.16, -0.46, 0.13)) * 0.95, tgt, lens=62)
    return c


def label_explosion(path, root, cam):
    """Ankerpunkte projizieren und mit PIL beschriften (Text links/rechts, Fuehrungslinie)."""
    from PIL import Image, ImageDraw, ImageFont
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    im = Image.open(path).convert('RGB')
    W, H = im.size
    dr = ImageDraw.Draw(im)
    k = W / 2000.0
    f = ImageFont.truetype(FONT, round(30 * k))
    pts = []
    for part, a, txt, side in LABELS:
        off = Vector(EXPLODE.get(part, (0, 0, 0)))
        p = root.matrix_world @ ((Vector(a) + off) * MM)
        q = world_to_camera_view(sc, cam, p)
        pts.append((q.x * W, (1 - q.y) * H, txt, side))
    for side in 'LR':
        sel = sorted([p for p in pts if p[3] == side], key=lambda p: p[1])
        xs = 70 * k if side == 'L' else W - 70 * k
        ylast = -1e9
        for x, y, txt, _ in sel:
            ty = max(y, ylast + 52 * k)
            ylast = ty
            tw = dr.textlength(txt, font=f)
            tx = xs if side == 'L' else xs - tw
            ex = tx + tw + 14 * k if side == 'L' else tx - 14 * k
            dr.line([(ex, ty), (x, y)], fill=INK, width=max(2, round(2 * k)))
            r = 5 * k
            dr.ellipse([x - r, y - r, x + r, y + r], fill=INK)
            dr.text((tx, ty - 18 * k), txt, font=f, fill=INK)
    fb = ImageFont.truetype(FONT_B, round(40 * k))
    dr.text((70 * k, H - 150 * k), 'fluidi Sensor – Explosionsansicht', font=fb, fill=INK)
    fs = ImageFont.truetype(FONT, round(24 * k))
    dr.text((70 * k, H - 96 * k), 'Kopf 34 × 13 × 57.5 mm · CAD-Stand Rev C (D-019, D-023) · Platine aus KiCad-STEP',
            font=fs, fill=INK)
    im.save(path)


# ----------------------------------------------------------------------------- 4 Batteriewechsel
PULL = 37.0                        # Huelse nach unten abgezogen (mm): Oberkante z 7.7 unter der Zelle (z 8.7), Kragen noch in der Huelse
CELL_OUT = 9.0                     # Zelle seitlich (+x) aus dem Clip geschoben (check_sensor.txt Pruefung 4: frei)


def build_batterie():
    reset()
    studio(floor_col=(0.80, 0.80, 0.79), key=14.0)
    root, objs = sensor('', None, explode={'Huelse_grau': (0, 0, -PULL), 'Schraube_M2': (0, 0, -PULL), 'CR2032': (CELL_OUT, 0, 0)})
    root.location = Vector((0, 0, 140)) * MM
    root.rotation_euler = (0, 0, math.radians(-14))
    return root


def cam_batterie(root):
    bpy.context.view_layer.update()
    tgt = root.matrix_world @ (Vector((3, 4, 23)) * MM)
    c = camera('Cam_Batterie', tgt + Vector((0.15, -0.24, 0.11)) * 1.12, tgt, lens=85, fstop=11)
    return c


def run(jobs, samples=None, pct=100):
    times = {}
    for j in jobs:
        if j == '3':
            r = build_explosion(); c = cam_explosion(r)
            settings((2000, 2400), samples or 768, exposure=-0.7)
            bpy.context.scene.render.resolution_percentage = pct
            p = os.path.join(OUTF, 'fluidi_03_explosion.png')
            times[j] = render(p, c)
            label_explosion(p, r, c)
        elif j == '4':
            r = build_batterie(); c = cam_batterie(r)
            settings((2000, 1500), samples or 1024, exposure=-0.7)
            bpy.context.scene.render.resolution_percentage = pct
            times[j] = render(os.path.join(OUTF, 'fluidi_04_batteriewechsel.png'), c)
    print('ZEITEN', times, flush=True)


if bpy.app.background and '--' in sys.argv:
    a = batch_args()
    jobs = [x for x in sys.argv[sys.argv.index('--') + 1:] if x in ('3', '4')]
    run(jobs, a['samples'], a['pct'])
