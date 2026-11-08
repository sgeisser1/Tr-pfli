# -*- coding: utf-8 -*-
"""fluidi Phase 4e - CAD-Generatorausgaben (FreeCAD) als OBJ fuer die Blender-Renderings.

Quelle (nichts nachmodelliert):
  mechanical/sensor/fluidi_sensor.FCStd        (fluidi_sensor.py, Schnittstelle Rev C, V-K/M-4 nach D-023)
  mechanical/gateway_pi/fluidi_gateway_pi.FCStd  (fluidi_gateway_pi.py, Gateway G1 v4)
Kopfkoordinaten wie docs/interfaces/PCB_OUTLINE.md Kap. 1 (mm, x Breite, y Tiefe 0 = Front, z 0 = Kopfunterkante).
Nicht exportiert: Platzhalter, die durch den KiCad-STEP ersetzt werden (PCB, Antenne, Band_Huelle_F, SW1_Taster,
U3_TMP_Kragen, Keystone3034) sowie die Distanzlehre und die OTG-Variante der Wanne.
D1_LED bleibt als Platzhalter (der KiCad-STEP enthaelt fuer D1 kein 3D-Modell).

Lauf:  freecadcmd renders/final/scripts/export_cad_obj.py
Ausgabe: renders/final/mesh/sensor_<Teil>.obj, gateway_<Teil>.obj (abgeleitet, jederzeit neu erzeugbar)
"""
import os
import FreeCAD as App
import MeshPart

REPO = '/home/sgeisser/git/Tr-pfli'
OUT = os.path.join(REPO, 'renders/final/mesh')
SKIP = {'PCB', 'Antenne_AN043', 'Band_Huelle_F', 'SW1_Taster', 'U3_TMP_Kragen', 'Keystone3034', 'Distanzlehre_24p2',
        'Wanne_grau_OTG'}


def write_obj(mesh, path, name):
    with open(path, 'w') as f:
        f.write('# fluidi, aus %s, mm\no %s\n' % (name, name))
        for p in mesh.Points:
            f.write('v %.5f %.5f %.5f\n' % (p.x, p.y, p.z))
        for t in mesh.Topology[1]:
            f.write('f %d %d %d\n' % (t[0] + 1, t[1] + 1, t[2] + 1))


def export(fc, prefix, lin=0.01, ang=0.08):
    doc = App.openDocument(fc)
    for o in doc.Objects:
        if o.TypeId != 'Part::Feature' or o.Name in SKIP or o.Shape.isNull():
            continue
        m = MeshPart.meshFromShape(Shape=o.Shape, LinearDeflection=lin, AngularDeflection=ang, Relative=False)
        p = os.path.join(OUT, '%s_%s.obj' % (prefix, o.Name))
        write_obj(m, p, o.Name)
        print('%-28s %7d Dreiecke  -> %s' % (o.Name, m.CountFacets, os.path.basename(p)))
    App.closeDocument(doc.Name)


os.makedirs(OUT, exist_ok=True)
export(os.path.join(REPO, 'mechanical/sensor/fluidi_sensor.FCStd'), 'sensor')
export(os.path.join(REPO, 'mechanical/gateway_pi/fluidi_gateway_pi.FCStd'), 'gateway')
