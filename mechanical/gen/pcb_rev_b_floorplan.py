# -*- coding: utf-8 -*-
"""fluidi Sensor - Flaechenbilanz und Blockplan Elektronikband, Schnittstelle PCB-Kontur Rev B.

Nachweis, dass Option (f) (hardware/sensor/out/FLOORPLAN_OPTIONS.md) + Messkette D3 (docs/concepts/MESSKETTE_SALZ.md,
D-018) in das Band 26 x 15.1 mm passen. Courtyards aus KiCad 10 (pcbnew) ueber hardware/sensor/gen/floorplan_options.py.
Bloecke = Cluster mit Flaeche >= 1.1 x Courtyard-Summe (ANNAHME packbar, wie FLOORPLAN_OPTIONS), Einzelteile = Courtyard.

Lauf:  .venv/bin/python mechanical/gen/pcb_rev_b_floorplan.py
Ausgabe: mechanical/interfaces/pcb_outline.json/.dxf (ueber fluidi_params.main, inkl. Layer Plan_*),
         mechanical/interfaces/pcb_rev_b_floorplan.png, Konsolenprotokoll
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fluidi_params as FP

REPO = FP.REPO
_spec = importlib.util.spec_from_file_location('fo', os.path.join(REPO, 'hardware/sensor/gen/floorplan_options.py'))
FO = importlib.util.module_from_spec(_spec)
_argv = sys.argv; sys.argv = [sys.argv[0]]
_spec.loader.exec_module(FO)          # liest Courtyards per pcbnew (KiCad 10)
sys.argv = _argv
CY, area = FO.CY, FO.area

FACTOR = 1.5                          # Leiterbahn-/Fanout-Faktor 1.3 ... 1.5 (ANNAHME, FLOORPLAN_OPTIONS Kap. 1)
Z0, Z1 = FP.Z['BAND0'], FP.Z['BAND1']
MARGIN_TOP = 0.3                      # Abstand Bloecke - Massekante unter der Antenne (ANNAHME wie FLOORPLAN_OPTIONS)
XM = FP.PCB['W_HEAD'] / 2 - FP.PCB['EDGE_CLR']   # 12.7

# ------------------------------------------------------------------ Bauteile im Band: (f) + D3
# (f) = REV_C aus floorplan_options ohne U3 (wandert mit C24 in den Kragen). Abgeglichen mit dem Schaltplan-Generator
# hardware/sensor/gen/parts.py (Stand 2026-11-07): Band = C1-C4 1206, C5-C22 + C25 0402 (19), R1-R13 (13), L1, L2, U1, U2,
# U4-U6, Q1, Q2, Y1, Y2, SW1, D1; TP4/TP5 als Pads auf B, TP1-TP3 im Fachstreifen, U3 + C24 im Kragen.
REV_F = [r for r in FO.REV_C if not r[0].startswith('U3')]
D3 = [("U4-U6 SN74LVC1G80DCKR Teiler /8 (C473331)", "SC70_5", 3),
      ("C25 100 nF Abblock U4-U6", "C0402", 1),
      ("Q2 AO3401A Lastschalter Messkette (C15127)", "SOT23", 1),
      ("R13 100 kOhm Pull-up Gate Q2", "R0402", 1),
      ("C23 Cref2 entfaellt (MESSKETTE_SALZ Kap. 4)", "C0402", -1)]
KRAGEN = [("U3 TMP1075NDRLR (C3663690)", "SOT563", 1), ("C24 100 nF", "C0402", 1)]


def bom_area(lst):
    return sum(area(k) * n for _, k, n in lst)


def blk(name, x0, x1, z0, z1, parts, color):
    return dict(name=name, x0=x0, z0=z0, w=x1 - x0, h=z1 - z0, parts=parts, color=color)


def part(name, key, cx, cz, color, rot=False):
    w, h = CY[key]
    if rot:
        w, h = h, w
    return dict(name=name, x0=cx - w / 2, z0=cz - h / 2, w=w, h=h, parts=[(key, 1)], color=color)


C_PWR, C_SOC, C_RF, C_MEAS, C_UI, C_UART = "#fdae6b", "#9ecae1", "#fb6a4a", "#a1d99b", "#dadaeb", "#fdd0a2"


def plan():
    b = [part("SW1 TS-1088", "TS1088", FP.SW['X'], FP.SW['Z'], C_UI),
         part("D1 RGB", "LED1615", FP.LED['X'], FP.LED['Z'], C_UI)]
    w, h = CY["C1206"]
    for i, x0 in enumerate((-10.0, -5.3, -0.6, 4.1)):
        b.append(blk("C%d 100uF" % (i + 1), x0, x0 + w, Z0, Z0 + h, [("C1206", 1)], C_PWR))
    b.append(blk("R9-R12\nUART", -XM, -10.1, Z0, 36.6, [("R0402", 4)], C_UART))
    b.append(blk("Q2 + R\nLast-\nschalter", -XM, -8.8, 36.7, 41.1, [("SOT23", 1), ("R0402", 1)], C_MEAS))
    b.append(blk("Teiler U4-U6\n+ C25 (D3)", -8.7, -1.3, 35.15, 40.15, [("SC70_5", 3), ("C0402", 1)], C_MEAS))
    b.append(blk("U2 R3\nC21 C22", -8.7, -3.1, 40.25, 43.25, [("SC70_5", 1), ("R0402", 1), ("C0402", 2)], C_MEAS))
    b.append(blk("R4 R5", -XM, -10.4, 43.4, 45.6, [("R0402", 2)], C_MEAS))
    b.append(blk("U1 CC2340 + C5-C13\nR1 L1", -1.2, 7.5, 35.15, 42.6,
                 [("QFN24", 1), ("C0402", 9), ("R0402", 1), ("L2016", 1)], C_SOC))
    b.append(blk("R6-R8\nLED", 1.3, 5.1, 42.7, 44.5, [("R0402", 3)], C_UI))
    b.append(blk("Q1", 5.2, 5.2 + CY["SOT23"][0], 42.7, 42.7 + CY["SOT23"][1], [("SOT23", 1)], C_PWR))
    b.append(blk("Y1 Y2\nC14 C15", XM - CY["XT3225"][1], XM, 34.6, Z1 - MARGIN_TOP,
                 [("XT3225", 1), ("XT3215", 1), ("C0402", 2)], C_SOC))
    b.append(blk("RF C16-C20 L2 R2", -2.9, 5.1, 45.3, Z1 - MARGIN_TOP, [("C0402", 5), ("L0402", 1), ("R0402", 1)], C_RF))
    return b


def plan_kragen():
    return [blk("U3 + C24", FP.TMP['X0'], FP.TMP['X1'], FP.TMP['Z0'], FP.TMP['Z1'], [("SOT563", 1), ("C0402", 1)], C_MEAS)]


def check(blocks, x0, x1, z0, z1):
    err = []
    for i, a in enumerate(blocks):
        if a['x0'] < x0 - 1e-6 or a['x0'] + a['w'] > x1 + 1e-6 or a['z0'] < z0 - 1e-6 or a['z0'] + a['h'] > z1 + 1e-6:
            err.append('ausserhalb: ' + a['name'].replace('\n', ' '))
        need = sum(area(k) * n for k, n in a['parts'])
        multi = len(a['parts']) > 1 or a['parts'][0][1] > 1
        if a['w'] * a['h'] < need * (1.1 if multi else 1.0) - 1e-6:
            err.append('Block zu klein: %s (%.1f < %.1f)' % (a['name'].replace('\n', ' '), a['w'] * a['h'], need * 1.1))
        for b2 in blocks[i + 1:]:
            if a['x0'] < b2['x0'] + b2['w'] - 1e-6 and b2['x0'] < a['x0'] + a['w'] - 1e-6 and \
                    a['z0'] < b2['z0'] + b2['h'] - 1e-6 and b2['z0'] < a['z0'] + a['h'] - 1e-6:
                err.append('Ueberlappung: %s / %s' % (a['name'].replace('\n', ' '), b2['name'].replace('\n', ' ')))
    return err


def placed_parts(blocks):
    cnt = {}
    for b in blocks:
        for k, n in b['parts']:
            cnt[k] = cnt.get(k, 0) + n
    return cnt


def draw(path, blocks, kr):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle, Polygon
    fig, ax = plt.subplots(figsize=(8.6, 13.5))
    ol = FP.outline()
    ax.add_patch(Polygon(ol, closed=True, fc='#e6efe6', ec='k', lw=1.2))
    for zd in FP.zones():
        x0, x1 = zd['x']; z0, z1 = zd['z']
        if zd['z'][0] < -6:
            continue
        ax.add_patch(Rectangle((x0, z0), x1 - x0, z1 - z0, fc='none', ec='#888', lw=0.6, ls='--'))
        ax.text(x0 - 0.4, (z0 + z1) / 2, zd['id'].replace('_', ' ') + '\n' + 'h<=%.1f' % zd['hmax'] if zd['side'] != 'B' else '',
                ha='right', va='center', fontsize=6.5, color='#555')
    Z = FP.Z
    ax.add_patch(Rectangle((-FP.ANT['W'] / 2 + 5.0, Z['ANT0']), FP.ANT['W'], FP.ANT['H'], fc='#fcbba1', ec='r', lw=0.8))
    ax.text(5.0, (Z['ANT0'] + Z['ANT1']) / 2, 'AN043 (Vorschlag rechtsbuendig,\nEinspeisung links, offenes Ende rechts)',
            ha='center', va='center', fontsize=6.5)
    for b in blocks + kr:
        ax.add_patch(Rectangle((b['x0'], b['z0']), b['w'], b['h'], fc=b['color'], ec='k', lw=0.6))
        ax.text(b['x0'] + b['w'] / 2, b['z0'] + b['h'] / 2, b['name'], ha='center', va='center', fontsize=5.6)
    c = FP.CLIP
    ax.add_patch(Rectangle((c['X0'], Z['CLIP0']), c['X1'] - c['X0'], Z['CLIP1'] - Z['CLIP0'], fc='#d9d9d9', ec='k', lw=0.6, alpha=0.6))
    ax.add_patch(Circle((FP.CELL['XC'], Z['CELL_C']), 10, fc='none', ec='k', lw=0.8))
    ax.text(FP.CELL['XC'], Z['CELL_C'], 'XBT1 Keystone 3034 (90 Grad)\nCR2032, Ausschub +x', ha='center', fontsize=7)
    t = FP.TPSTRIP
    ax.add_patch(Rectangle((t['X0'], t['Z0']), t['X1'] - t['X0'], t['Z1'] - t['Z0'], fc='#fdd0a2', ec='k', lw=0.6))
    ax.text((t['X0'] + t['X1']) / 2, (t['Z0'] + t['Z1']) / 2, 'Testpads\nUART\n(nur Pads)', ha='center', va='center', fontsize=6, rotation=90)
    k = FP.KPOCKET
    ax.add_patch(Rectangle((k['X0'], k['Z0']), k['X1'] - k['X0'], k['Z1'] - k['Z0'], fc='none', ec='b', lw=0.8, ls=':'))
    ax.add_patch(Circle((FP.SCREW['X'], 3.1), 2.3, fc='#bbb', ec='k', lw=0.5))
    ax.text(0, 3.1, 'M2', ha='center', va='center', fontsize=6)
    ax.add_patch(Circle((FP.DROP['X'], FP.DROP['ZC']), FP.DROP['BOSS_D'] / 2, fc='none', ec='b', lw=0.8))
    T = FP.TONGUE
    ax.add_patch(Rectangle((T['X0'], T['Z_TIP']), T['X1'] - T['X0'], FP.BTN['BLOCK_Z0'] - T['Z_TIP'], fc='none', ec='b', lw=0.8, ls='-.'))
    ax.text((T['X0'] + T['X1']) / 2, 50.5, 'Zunge\n(Kappe)', ha='center', fontsize=5.5, color='b')
    ax.axhline(FP.HEAD['Z_FUGE'], color='b', lw=0.6, ls=':')
    ax.text(13.3, FP.HEAD['Z_FUGE'], 'Sichtfuge z %.1f' % FP.HEAD['Z_FUGE'], fontsize=6.5, color='b', va='center')
    ax.axhline(-5.0, color='brown', lw=0.8)
    ax.text(13.3, -5.0, 'max. Stecktiefe z -5', fontsize=6.5, color='brown', va='center')
    ax.set_xlim(-22, 20); ax.set_ylim(-7, 56)
    ax.set_aspect('equal'); ax.grid(alpha=0.25)
    ax.set_xlabel('x [mm] (KiCad X)'); ax.set_ylabel('z [mm] Kopfkoordinate (KiCad Y = %.1f - z)' % FP.PCB['Z_TOP'])
    ax.set_title('fluidi PCB-Kontur Rev B: Band 26 x 15.1 mm, Blockplan (f) + D3\nAnsicht von vorne = KiCad Top (F.Cu)', fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=170)


def main():
    blocks = plan()
    kr = plan_kragen()
    xb0, xb1 = -XM, XM
    err = check(blocks, xb0, xb1, Z0, Z1 - MARGIN_TOP)
    err += ['Kragen: ' + e for e in check(kr, FP.KPOCKET['X0'] + 0.2, FP.KPOCKET['X1'] - 0.2, FP.Z['KCOMP0'], FP.Z['KCOMP1'])]
    a_f = bom_area(REV_F)
    a_d3 = bom_area(D3)
    a_band = a_f + a_d3
    gross = FP.PCB['W_HEAD'] * (Z1 - Z0)
    need = a_band * FACTOR
    # Vollstaendigkeit: platzierte Bauteile = Stueckliste
    want = {}
    for _, k, n in REV_F + D3:
        want[k] = want.get(k, 0) + n
    got = placed_parts(blocks)
    diff = {k: (got.get(k, 0), want.get(k, 0)) for k in set(want) | set(got) if got.get(k, 0) != want.get(k, 0)}
    if diff:
        err.append('Stueckliste != Blockplan: %s' % diff)
    lines = ['Flaechenbilanz Rev B (Courtyards KiCad 10, mm2):']
    for name, k, n in REV_F + D3:
        lines.append('  %-58s %-8s %2d x %6.2f = %7.2f' % (name, k, n, area(k), n * area(k)))
    lines.append('  Summe (f) ohne U3: %.1f, D3: %+.1f -> Band-Courtyard %.1f mm2' % (a_f, a_d3, a_band))
    lines.append('  x Faktor %.1f (ANNAHME Leiterbahnen/Fanout) = Bedarf %.1f mm2' % (FACTOR, need))
    lines.append('  Band brutto 26.0 x %.1f = %.1f mm2 (Faktor effektiv %.2f); Blockplan-Pruefung: %s'
                 % (Z1 - Z0, gross, gross / a_band, 'OK' if not err else '; '.join(err)))
    lines.append('  Kragen: U3 + C24 Courtyard %.1f mm2 im Feld %.1f x %.1f' % (bom_area(KRAGEN), FP.TMP['X1'] - FP.TMP['X0'],
                                                                          FP.TMP['Z1'] - FP.TMP['Z0']))
    print('\n'.join(lines))
    area_d = dict(courtyard_f_without_U3=round(a_f, 1), courtyard_D3=round(a_d3, 1), courtyard_band=round(a_band, 1),
                  factor=FACTOR, required=round(need, 1), band_gross=round(gross, 1), effective_factor=round(gross / a_band, 2),
                  block_plan_check='OK' if not err else err,
                  note='Blockplan (Layer Plan_* in der DXF, PNG pcb_rev_b_floorplan.png) ist Machbarkeitsnachweis, '
                       'keine Platzierungsvorgabe ausser D1/SW1')
    polys = []
    for b in blocks + kr:
        nm = 'Plan_' + b['name'].split('\n')[0].replace(' ', '_').replace('+', '').replace('/', '')
        polys.append((nm, FP.rect_k(b['x0'], b['x0'] + b['w'], b['z0'], b['z0'] + b['h']), True))
    FP.main(area_d, polys)
    png = os.path.join(REPO, 'mechanical', 'interfaces', 'pcb_rev_b_floorplan.png')
    draw(png, blocks, kr)
    print('PNG:', png)
    return 0 if not err else 1


if __name__ == '__main__':
    sys.exit(main())
