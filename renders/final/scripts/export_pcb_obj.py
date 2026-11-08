# -*- coding: utf-8 -*-
"""fluidi Phase 4e - KiCad-STEP der Sensorplatine (mit Bauteilen) als OBJ in Kopfkoordinaten, Farben aus dem STEP.

Quelle: hardware/sensor/out/fluidi_sensor.step (kicad-cli pcb export step, hardware/sensor/gen/run_pcb.sh)
Lage: docs/interfaces/PCB_OUTLINE.md Kap. 1: x = X_s - 150, y = 8.2 - Z_s, z = 83.5 + Y_s
      (= Drehung +90 Grad um x, dann Verschiebung (-150, 8.2, 83.5)).
Die Flaechenfarben liest nur ImportGui (FreeCAD mit Oberflaeche). Deshalb in der FreeCAD-GUI ausfuehren:
      freecad renders/final/scripts/export_pcb_obj.py      (oder per MCP execute_code: exec(open(...).read()))
Ausgabe: renders/final/mesh/pcb_kicad.obj (+ .mtl): ein Objekt je STEP-Farbe ("c_RRGGBB"), mm.
"""
import os
import FreeCAD as App
import ImportGui
import MeshPart
import Part

REPO = '/home/sgeisser/git/Tr-pfli'
STEP = os.path.join(REPO, 'hardware/sensor/out/fluidi_sensor.step')
OUT = os.path.join(REPO, 'renders/final/mesh/pcb_kicad.obj')
HEAD = App.Placement(App.Vector(-150, 8.2, 83.5), App.Rotation(App.Vector(1, 0, 0), 90))

doc = App.newDocument('fluidi_pcb_export')
ImportGui.insert(STEP, doc.Name)
groups = {}
for o in doc.Objects:
    if o.TypeId != 'Part::Feature' or o.Shape.isNull():
        continue
    gp = o.getGlobalPlacement()
    dc = o.ViewObject.DiffuseColor
    faces = o.Shape.Faces
    for i, fc in enumerate(faces):
        c = dc[i] if len(dc) == len(faces) else dc[0]
        key = '%02x%02x%02x' % tuple(int(round(v * 255)) for v in c[:3])
        f2 = fc.copy()
        f2.transformShape(gp.toMatrix())
        f2.transformShape(HEAD.toMatrix())
        groups.setdefault(key, []).append(f2)
App.closeDocument(doc.Name)

mtl = OUT[:-4] + '.mtl'
with open(OUT, 'w') as f, open(mtl, 'w') as fm:
    f.write('# fluidi Sensorplatine aus %s, Kopfkoordinaten mm\nmtllib %s\n' % (os.path.relpath(STEP, REPO), os.path.basename(mtl)))
    base = 1
    for key, fl in sorted(groups.items()):
        sh = Part.makeCompound(fl)
        m = MeshPart.meshFromShape(Shape=sh, LinearDeflection=0.005, AngularDeflection=0.1, Relative=False)
        r, g, b = (int(key[i:i + 2], 16) / 255 for i in (0, 2, 4))
        fm.write('newmtl c_%s\nKd %.4f %.4f %.4f\n' % (key, r, g, b))
        f.write('o c_%s\nusemtl c_%s\n' % (key, key))
        for p in m.Points:
            f.write('v %.5f %.5f %.5f\n' % (p.x, p.y, p.z))
        for t in m.Topology[1]:
            f.write('f %d %d %d\n' % (t[0] + base, t[1] + base, t[2] + base))
        base += m.CountPoints
        print('c_%s: %d Flaechen, %d Dreiecke' % (key, len(fl), m.CountFacets))
print('geschrieben', OUT)
