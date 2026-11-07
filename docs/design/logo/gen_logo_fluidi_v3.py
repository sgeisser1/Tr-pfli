#!/usr/bin/env python3
"""fluidi – Verfeinerung 2 (D-010): Wortmarke in vier ruhigeren Farbfassungen und App-Icon als Kachel im Sensor-Look.

Aufruf:  python3 docs/design/logo/gen_logo_fluidi_v3.py
Feedback D-010: „zwei blaue Tropfen zu viel. auch das schwarz ist zu hart.“

Geometrie der Wortmarke aus gen_logo_fluidi.py (harte Formsprache, 45°-Fasen, Tropfen wie das LED-Fenster).
Erzeugt in docs/design/logo/:
  fluidi_logo_v3a.svg / _dunkel.svg / _mono.svg   (a) Warmes Dunkelgrau, nur letzter Tropfen hellblau
  fluidi_logo_v3b.svg / ...                       (b) Warmes Dunkelgrau, beide Tropfen in Schriftfarbe (ganz ruhig)
  fluidi_logo_v3c.svg / ...                       (c) Gedämpftes Petrol/Blaugrau, letzter Tropfen hellblau
  fluidi_logo_v3d.svg / ...                       (d) Feinere Linie (Strich 1.7 u), Dunkelgrau, letzter Tropfen Grün („ok“)
  preview_fluidi_logo_v3a..d.png                  Hell / Dunkel / Mono nebeneinander
  icon_fluidi_kachel_a.svg / _b.svg + icon_fluidi_kachel_a_512/192/96/48.png (dto. b)
  logo_icon_uebersicht.png (+ Kopie nach renders/phase3_v3/)
SVG der Wortmarke ohne Hintergrund (transparent); _dunkel = Fassung für dunkle Flächen (helle Schrift).
_mono = eine Farbe, eine Fläche (Silkscreen, FDM-Relief, Prägung; Farbe bestimmt das Verfahren).

Icon-Kachel 512 x 512 (vollflächig, maskable: Motiv im Sicherheitskreis r = 0.4 N = 205 px um die Mitte):
  oben Hellblau #4AA8DE (Kappe), unten Warmgrau hell #B9B5AC (Hülse, D-010), an der Grenze der grüne LED-Tropfen
  in Sensorgeometrie: Kreis r, Spitze 2.4 r über der Mitte, Mitte 0.16 r über der Farbgrenze (Sensor: r 2.5 mm,
  Mitte 0.4 mm über der Fuge). Flach mit dezentem Leuchten (radialer Verlauf), keine Fotografie.
  a: Grenze auf 2/5 Höhe (von oben), flach, ohne Fuge.
  b: Grenze auf 1/3 Höhe (Proportion näher am Sensor), mit dezenter Fuge (folgt um den Tropfenbauch) und
     leichtem Schatten unter der Kappe.
Die PNG werden mit numpy/PIL direkt aus denselben Formeln gerastert (kein SVG-Renderer installiert).
"""
import math
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(OUT, '..', '..', '..'))
sys.path.insert(0, OUT)
import gen_logo_fluidi as base  # noqa: E402

BLUE = "#4AA8DE"          # Kappe/Taste hellblau
BLUE_D = "#6CC0EC"        # Hellblau etwas heller für dunkle Flächen
GREY_BODY = "#B9B5AC"     # Hülse Warmgrau hell (D-010)
WARM_DARK = "#4F4B45"     # Warmes Dunkelgrau: Farbton der Hülse, abgedunkelt
WARM_LIGHT = "#EEEBE5"    # Schrift auf Dunkel
DARK_BG = "#3A3732"       # dunkle Fläche (warm)
PETROL = "#3D5F6B"        # gedämpftes Petrol/Blaugrau
PETROL_LIGHT = "#DCE7EA"
PETROL_BG = "#22363D"
GREEN = "#3FA95C"         # LED-Zustand „ok“ (Grafik, gedämpft)
GREEN_D = "#5CC877"
PAPER = "#FFFFFF"

P_A = dict(base.VARIANTS['A_linie'])                  # Geometrie wie am Sensor (Relief 16 mm, Strich 0.85 mm)
P_FINE = dict(P_A, S=1.7, C=2.2)                       # (d) feinere Linie

#        Name  Geometrie  hell: (Schrift, Tropfen1, Tropfen2, Hintergrund)  dunkel: (...)            Titel
LOGOS = {
    'v3a': (P_A, (WARM_DARK, WARM_DARK, BLUE, PAPER), (WARM_LIGHT, WARM_LIGHT, BLUE_D, DARK_BG),
            'a  Warmes Dunkelgrau, ein blauer Tropfen'),
    'v3b': (P_A, (WARM_DARK, WARM_DARK, WARM_DARK, PAPER), (WARM_LIGHT, WARM_LIGHT, WARM_LIGHT, DARK_BG),
            'b  Warmes Dunkelgrau, ohne Farbe (ganz ruhig)'),
    'v3c': (P_A, (PETROL, PETROL, BLUE, PAPER), (PETROL_LIGHT, PETROL_LIGHT, BLUE_D, PETROL_BG),
            'c  Petrol/Blaugrau, ein hellblauer Tropfen'),
    'v3d': (P_FINE, (WARM_DARK, WARM_DARK, GREEN, PAPER), (WARM_LIGHT, WARM_LIGHT, GREEN_D, DARK_BG),
            'd  Feine Linie, Tropfen im LED-Grün „ok“'),
}


# ----------------------------------------------------------------------------- Farbe
def rgb(h):
    return base.hexrgb(h)


def lum(h):
    c = [x / 255 for x in rgb(h)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


# ----------------------------------------------------------------------------- Wortmarke
DESC = ("fluidi-Wortmarke (klein, i-Punkte als Wassertropfen), eigene geometrische Pfade, keine Schrift. "
        "Verfeinerung 2 (D-010), erzeugt mit gen_logo_fluidi_v3.py. 1 Einheit = 1 u (Massstab frei).")


def make_logos():
    res = {}
    for key, (p, light, dark, title) in LOGOS.items():
        ink, drops, x0, x1, y0, y1 = base.wordmark(p)
        pad = 0.6
        W, H = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
        ox, oy = x0 - pad, y0 - pad
        d = lambda polys: base.to_d(polys, ox, oy, 1, H)  # noqa: E731

        def body(cols):
            ci, c1, c2 = cols[:3]
            groups = {}
            for col, polys in ((ci, ink), (c1, [drops[0]]), (c2, [drops[1]])):
                groups.setdefault(col, []).extend(polys)
            return "".join(f'<path fill="{c}" fill-rule="nonzero" d="{d(pl)}"/>\n' for c, pl in groups.items())

        base.write(f"fluidi_logo_{key}.svg", base.svg(W, H, body(light), "fluidi", DESC + f" Variante {key}, für helle Flächen."))
        base.write(f"fluidi_logo_{key}_dunkel.svg", base.svg(W, H, body(dark), "fluidi (dunkel)",
                                                             DESC + f" Variante {key}, für dunkle Flächen (Hintergrund z. B. {dark[3]})."))
        base.write(f"fluidi_logo_{key}_mono.svg", base.svg(W, H, f'<path fill="{light[0]}" fill-rule="nonzero" d="{d(ink + drops)}"/>\n',
                                                           "fluidi mono", DESC + " Einfarbig, eine Fläche (Silkscreen, FDM-Relief, Prägung)."))
        res[key] = dict(p=p, ink=ink, drops=drops, box=(x0, x1, y0, y1), light=light, dark=dark, title=title)
    return res


def logo_layers(r, cols):
    return [(cols[0], r['ink']), (cols[1], [r['drops'][0]]), (cols[2], [r['drops'][1]])]


def logo_previews(res, px=900):
    out = {}
    for key, r in res.items():
        hell = base.raster(logo_layers(r, r['light']), r['box'], px, r['light'][3])
        dunkel = base.raster(logo_layers(r, r['dark']), r['box'], px, r['dark'][3])
        mono = base.raster([(r['light'][0], r['ink'] + r['drops'])], r['box'], px, "#F4F3F0")
        strip = Image.new('RGB', (3 * px + 2 * 20, hell.size[1]), (255, 255, 255))
        for i, im in enumerate((hell, dunkel, mono)):
            strip.paste(im, (i * (px + 20), 0))
        strip.save(os.path.join(OUT, f'preview_fluidi_logo_{key}.png'))
        out[key] = (hell, dunkel, mono)
    return out


# ----------------------------------------------------------------------------- Icon-Kachel
N = 512.0
DROP_K = base.DROP_K
SAFE = 0.4 * N
ICONS = {
    #             Grenze (Anteil von oben)  Fuge/Schatten
    'kachel_a': dict(b=2 / 5, seam=False),
    'kachel_b': dict(b=1 / 3, seam=True),
}
G_CORE, G_MID, G_EDGE, G_GLOW = "#B4FAC4", "#4FDD77", "#1FA84A", "#4BE074"
SEAM = "#8F8A80"


def icon_geom(spec):
    """Liefert Grenze yb (px von oben), Tropfenmitte (cx, cy) und r so, dass die Spitze im Sicherheitskreis liegt."""
    yb = spec['b'] * N
    top_min = N / 2 - SAFE + 3                 # Spitze 3 px innerhalb des Sicherheitskreises
    r = min((yb - top_min) / (DROP_K + 0.16), 0.15 * N)
    cx, cy = N / 2, yb - 0.16 * r              # Mitte 0.16 r über der Grenze (wie Sensor 0.4 / 2.5 mm)
    return yb, cx, cy, r


def drop_px(cx, cy, r, n=96):
    """Tropfen in Bildkoordinaten (y nach unten), Spitze oben."""
    return [(x, 2 * cy - y) for x, y in base.drop(cx, cy, r, n)]


def notch_px(cx, cy, r, gap):
    k = (DROP_K * r + gap) / (r + gap)
    h = k * (r + gap)
    phi = math.asin((r + gap) / h)
    pts = [(cx, cy - h)]
    a0, a1 = math.pi - phi, 2 * math.pi + phi
    for i in range(97):
        t = a0 + (a1 - a0) * i / 96
        pts.append((cx + (r + gap) * math.cos(t), cy - (r + gap) * math.sin(t)))
    return pts


def path(pts):
    return "M" + " L".join(f"{x:.2f},{y:.2f}" for x, y in pts) + " Z"


def icon_svg(name, spec):
    yb, cx, cy, r = icon_geom(spec)
    gap = 0.009 * N
    s = []
    s.append('<defs>\n'
             f'<radialGradient id="glow" cx="{cx:.1f}" cy="{cy:.1f}" r="{2.3 * r:.1f}" gradientUnits="userSpaceOnUse">'
             f'<stop offset="0" stop-color="{G_GLOW}" stop-opacity="0.45"/><stop offset="0.45" stop-color="{G_GLOW}" stop-opacity="0.16"/>'
             f'<stop offset="1" stop-color="{G_GLOW}" stop-opacity="0"/></radialGradient>\n'
             f'<radialGradient id="core" cx="{cx:.1f}" cy="{cy - 0.15 * r:.1f}" r="{1.25 * r:.1f}" gradientUnits="userSpaceOnUse">'
             f'<stop offset="0" stop-color="{G_CORE}"/><stop offset="0.45" stop-color="{G_MID}"/><stop offset="1" stop-color="{G_EDGE}"/></radialGradient>\n')
    if spec['seam']:
        s.append(f'<linearGradient id="shade" x1="0" y1="{yb:.1f}" x2="0" y2="{yb + 0.06 * N:.1f}" gradientUnits="userSpaceOnUse">'
                 f'<stop offset="0" stop-color="#000000" stop-opacity="0.13"/><stop offset="1" stop-color="#000000" stop-opacity="0"/></linearGradient>\n'
                 f'<clipPath id="below"><rect x="0" y="{yb:.1f}" width="{N:.0f}" height="{N - yb:.1f}"/></clipPath>\n')
    s.append('</defs>\n')
    s.append(f'<rect x="0" y="0" width="{N:.0f}" height="{N:.0f}" fill="{GREY_BODY}"/>\n')
    s.append(f'<rect x="0" y="0" width="{N:.0f}" height="{yb:.1f}" fill="{BLUE}"/>\n')
    if spec['seam']:
        s.append(f'<rect x="0" y="{yb:.1f}" width="{N:.0f}" height="{0.06 * N:.1f}" fill="url(#shade)"/>\n')
        s.append(f'<rect x="0" y="{yb - gap / 2:.1f}" width="{N:.0f}" height="{gap:.1f}" fill="{SEAM}"/>\n')
        s.append(f'<path d="{path(notch_px(cx, cy, r, gap))}" fill="{SEAM}" clip-path="url(#below)"/>\n')
    s.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{2.3 * r:.1f}" fill="url(#glow)"/>\n')
    s.append(f'<path d="{path(drop_px(cx, cy, r))}" fill="url(#core)"/>\n')
    base.write(f"icon_fluidi_{name}.svg", base.svg(N, N, "".join(s), f"fluidi App-Icon {name}",
                                                   "PWA-Icon 512 px, Kachel im Sensor-Look (oben Hellblau, unten Warmgrau, grüner "
                                                   "LED-Tropfen an der Farbgrenze), vollflächig, maskable (Motiv im Kreis r = 0.4 N).",
                                                   unit=""))
    pts = drop_px(cx, cy, r)
    rmax = max(math.hypot(x - N / 2, y - N / 2) for x, y in pts)
    print(f"  {name}: Grenze y = {yb:.0f} px, Tropfen r = {r:.1f} px, Höhe {r * (1 + DROP_K):.0f} px, "
          f"Motiv bis r = {rmax:.0f} px (Sicherheitszone 205 px) ->", "OK" if rmax <= SAFE else "AUSSERHALB")


def poly_mask(pts, size, ss):
    m = Image.new('L', (size, size), 0)
    ImageDraw.Draw(m).polygon([(x * ss, y * ss) for x, y in pts], fill=255)
    return np.asarray(m, dtype=np.float32) / 255


def icon_raster(spec, px=512, ss=4):
    """Rastert die Kachel mit denselben Formeln wie icon_svg (Verläufe linear interpoliert wie SVG)."""
    yb, cx, cy, r = icon_geom(spec)
    gap = 0.009 * N
    S = int(N * ss)
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / ss + 0.5 / ss
    img = np.empty((S, S, 3), np.float32)
    img[:] = np.array(rgb(GREY_BODY), np.float32) / 255
    img[yy < yb] = np.array(rgb(BLUE), np.float32) / 255

    def over(col, a):
        c = np.array(rgb(col), np.float32) / 255 if isinstance(col, str) else col
        img[:] = img * (1 - a[..., None]) + c * a[..., None]

    def ramp(t, stops):
        t = np.clip(t, 0, 1)
        out = np.interp(t, [s[0] for s in stops], [s[1] for s in stops])
        return out
    if spec['seam']:
        t = (yy - yb) / (0.06 * N)
        a = np.where((t >= 0) & (t <= 1), 0.13 * (1 - t), 0)
        over('#000000', a.astype(np.float32))
        band = ((yy >= yb - gap / 2) & (yy < yb + gap / 2)).astype(np.float32)
        over(SEAM, band)
        nm = poly_mask(notch_px(cx, cy, r, gap), S, ss) * (yy >= yb)
        over(SEAM, nm.astype(np.float32))
    d = np.hypot(xx - cx, yy - cy) / (2.3 * r)
    ga = ramp(d, [(0, 0.45), (0.45, 0.16), (1, 0.0)]) * (d <= 1)
    over(G_GLOW, ga.astype(np.float32))
    dm = poly_mask(drop_px(cx, cy, r), S, ss)
    t = np.hypot(xx - cx, yy - (cy - 0.15 * r)) / (1.25 * r)
    cols = [np.array(rgb(c), np.float32) / 255 for c in (G_CORE, G_MID, G_EDGE)]
    core = np.stack([ramp(t, [(0, cols[0][i]), (0.45, cols[1][i]), (1, cols[2][i])]) for i in range(3)], -1)
    img[:] = img * (1 - dm[..., None]) + core * dm[..., None]
    im = Image.fromarray((np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8), 'RGB')
    return im.resize((px, px), Image.LANCZOS)


def make_icons():
    ims = {}
    for name, spec in ICONS.items():
        icon_svg(name, spec)
        big = icon_raster(spec, 512)
        ims[name] = {512: big}
        big.save(os.path.join(OUT, f'icon_fluidi_{name}_512.png'))
        for sz in (192, 96, 48):
            im = big.resize((sz, sz), Image.LANCZOS)
            im.save(os.path.join(OUT, f'icon_fluidi_{name}_{sz}.png'))
            ims[name][sz] = im
        print("geschrieben", f'icon_fluidi_{name}_512/192/96/48.png')
    return ims


def mask_shape(im, kind):
    """Vorschau: so schneidet ein Launcher das maskable Icon zu (Rundquadrat bzw. Kreis)."""
    m = Image.new('L', im.size, 0)
    dr = ImageDraw.Draw(m)
    w = im.size[0] - 1
    if kind == 'kreis':
        dr.ellipse((0, 0, w, w), fill=255)
    else:
        dr.rounded_rectangle((0, 0, w, w), radius=int(0.22 * im.size[0]), fill=255)
    out = Image.new('RGB', im.size, (246, 246, 244))
    out.paste(im, (0, 0), m)
    return out


# ----------------------------------------------------------------------------- Übersicht
def overview(res, prev, icons):
    W = 1800
    try:
        f1 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
        f2 = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
    except OSError:
        f1 = f2 = ImageFont.load_default()
    sheet = Image.new('RGB', (W, 3000), (246, 246, 244))
    d = ImageDraw.Draw(sheet)
    y = 30
    d.text((40, y), "fluidi – Wortmarke Verfeinerung 2 (je: auf Hell / auf Dunkel / Mono)", fill=(45, 45, 45), font=f1)
    y += 50
    tw = 540
    for key, (hell, dunkel, mono) in prev.items():
        r = res[key]
        d.text((40, y), r['title'] + f"   (Strich {r['p']['S']} u)", fill=(45, 45, 45), font=f2)
        y += 30
        for i, im in enumerate((hell, dunkel, mono)):
            t = im.resize((tw, int(im.size[1] * tw / im.size[0])), Image.LANCZOS)
            sheet.paste(t, (40 + i * (tw + 30), y))
        y += t.size[1] + 30
    d.text((40, y), "App-Icon als Kachel im Sensor-Look (512 maskable: Rundquadrat, Kreis; 192 / 96 / 48 px in Originalgrösse)",
           fill=(45, 45, 45), font=f1)
    y += 46
    for name, ims in icons.items():
        spec = ICONS[name]
        lab = (f"{name.replace('kachel_', 'Kachel ')}: Grenze auf {'2/5' if spec['b'] > 0.35 else '1/3'} Höhe, "
               f"{'mit Fuge und leichtem Schatten' if spec['seam'] else 'flach, ohne Fuge'}")
        d.text((40, y), lab, fill=(45, 45, 45), font=f2)
        y += 30
        x = 40
        for kind in ('rund', 'kreis'):
            t = mask_shape(ims[512].resize((300, 300), Image.LANCZOS), kind)
            sheet.paste(t, (x, y)); x += 330
        for sz in (192, 96, 48):
            sheet.paste(mask_shape(ims[sz], 'rund'), (x, y + 300 - sz)); x += sz + 30
        # 48 px vergrössert (pixelgenau), um die Lesbarkeit zu beurteilen
        big = mask_shape(ims[48], 'rund').resize((192, 192), Image.NEAREST)
        sheet.paste(big, (x + 20, y + 108))
        d.text((x + 20, y + 80), "48 px, 4-fach", fill=(90, 96, 104), font=f2)
        y += 340
    sheet = sheet.crop((0, 0, W, y + 10))
    p = os.path.join(OUT, 'logo_icon_uebersicht.png')
    sheet.save(p)
    dst = os.path.join(REPO, 'renders', 'phase3_v3')
    os.makedirs(dst, exist_ok=True)
    shutil.copy(p, os.path.join(dst, 'logo_icon_uebersicht.png'))
    print('geschrieben logo_icon_uebersicht.png (+ Kopie renders/phase3_v3/)')


def report(res):
    print("\nKontrast (WCAG) Schrift/Hintergrund:")
    for key, r in res.items():
        print(f"  {key}: hell {r['light'][0]} auf {r['light'][3]} = {contrast(r['light'][0], r['light'][3]):.1f}:1, "
              f"dunkel {r['dark'][0]} auf {r['dark'][3]} = {contrast(r['dark'][0], r['dark'][3]):.1f}:1, "
              f"Akzent {r['light'][2]} auf Weiss = {contrast(r['light'][2], PAPER):.1f}:1")
    print(f"  Schrift Dunkelgrau auf Hülse {GREY_BODY}: {contrast(WARM_DARK, GREY_BODY):.1f}:1; "
          f"Kachel Hellblau/Warmgrau: {contrast(BLUE, GREY_BODY):.2f}:1 (Helligkeit), Grün {G_EDGE} auf Grau {contrast(G_EDGE, GREY_BODY):.2f}:1")
    print("\nMindestbreite der Wortmarke (Strich S, kleinstes Merkmal = min(S, Tropfenbreite)):")
    for key, r in res.items():
        p = r['p']
        x0, x1, y0, y1 = r['box']
        w = x1 - x0
        sm = min(p['S'], 2 * p['R'])
        req = {lab: w * s / sm for lab, s in (("JLC 0.15", 0.15), ("Silk 0.2", 0.2), ("FDM 1 Bahn 0.45", 0.45), ("FDM 2 Bahnen 0.8", 0.8))}
        print(f"  {key}: {w:.2f} x {y1 - y0:.2f} u, Strich {p['S']} u; bei 16 mm Breite Strich {p['S'] * 16 / w:.2f} mm; "
              + ", ".join(f"{k} -> >= {v:.1f} mm" for k, v in req.items()))


def main():
    res = make_logos()
    prev = logo_previews(res)
    icons = make_icons()
    overview(res, prev, icons)
    report(res)


if __name__ == "__main__":
    main()
