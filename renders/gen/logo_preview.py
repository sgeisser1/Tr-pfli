"""Vorschau der Logo-SVGs (docs/design/logo) per Blender-SVG-Import -> je ein PNG.
Prüft zugleich, dass die Pfade als Flächen importierbar sind (FDM-Relief-Workflow).
In Blender: exec(open('/home/sgeisser/git/Tr-pfli/renders/gen/logo_preview.py').read())
"""
import bpy, os
from mathutils import Vector

REPO = '/home/sgeisser/git/Tr-pfli'
LOGO = os.path.join(REPO, 'docs/design/logo')
FILES = ['logo_v1_schlicht', 'logo_v2_tropfen', 'logo_v3_facette', 'icon_v1', 'icon_v2', 'icon_v3']

sc = bpy.data.scenes.get('LogoPreview') or bpy.data.scenes.new('LogoPreview')
bpy.context.window.scene = sc
sc.render.engine = 'BLENDER_WORKBENCH'
sc.display.shading.light = 'FLAT'
sc.display.shading.color_type = 'MATERIAL'
sc.view_settings.view_transform = 'Standard'
if sc.world is None:
    sc.world = bpy.data.worlds.new('LogoW')
sc.world.color = (0.8, 0.8, 0.8)
cam = bpy.data.objects.get('LogoCam') or bpy.data.objects.new('LogoCam', bpy.data.cameras.new('LogoCam'))
if cam.name not in sc.collection.objects:
    sc.collection.objects.link(cam)
cam.data.type = 'ORTHO'
sc.camera = cam
out = []
for fn in FILES:
    for o in list(sc.objects):
        if o != cam:
            bpy.data.objects.remove(o, do_unlink=True)
    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=os.path.join(LOGO, fn + '.svg'))
    new = [o for o in bpy.data.objects if o not in before]
    pts = [o.matrix_world @ Vector(v) for o in new for v in o.bound_box]
    x0, x1 = min(p.x for p in pts), max(p.x for p in pts)
    y0, y1 = min(p.y for p in pts), max(p.y for p in pts)
    for i, o in enumerate(new):
        o.location.z += i * 1e-4          # Zeichenreihenfolge wie im SVG
    w, h = x1 - x0, y1 - y0
    cam.location = ((x0 + x1) / 2, (y0 + y1) / 2, 1.0)
    cam.data.ortho_scale = max(w, h) * 1.08
    sc.render.resolution_x = 1200 if w >= h else int(1200 * w / h)
    sc.render.resolution_y = int(1200 * h / w) if w >= h else 1200
    if fn.startswith('icon'):
        sc.render.resolution_x = sc.render.resolution_y = 512
    sc.render.filepath = os.path.join(LOGO, 'preview_' + fn + '.png')
    bpy.ops.render.render(write_still=True)
    out.append((fn, len(new), round(w * 1000, 2), round(h * 1000, 2)))
print(out)
