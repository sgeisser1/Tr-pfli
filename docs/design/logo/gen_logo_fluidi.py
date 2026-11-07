#!/usr/bin/env python3
"""fluidi – Wortmarke "fluidi" (klein) mit Wassertropfen als i-Punkte, PWA-Icons, Vorschauen.

Aufruf:  python3 docs/design/logo/gen_logo_fluidi.py
Erzeugt in docs/design/logo/:
  fluidi_A_linie.svg / fluidi_A_linie_mono.svg        Variante A "Linie"    (Strich 2.0 u, schlank)
  fluidi_B_kraeftig.svg / fluidi_B_kraeftig_mono.svg  Variante B "Kräftig"  (Strich 2.6 u, grössere Tropfen)
  fluidi_A_linie_weiss.svg / fluidi_B_kraeftig_weiss.svg   Negativ (weiss + Tropfen blau) für dunkle Flächen
  icon_fluidi_fi.svg        PWA-Icon 512: "fi" mit Tropfen-Punkt
  icon_fluidi_tropfen.svg   PWA-Icon 512: ein Tropfen
  preview_*.png, logo_uebersicht.png (PIL, direkt aus denselben Polygonen gerastert)
und kopiert die Übersicht nach renders/phase3_v2/logo_uebersicht.png.

Konstruktion (Einheiten u, y nach oben, Grundlinie y = 0):
  harte Formsprache wie P3/Phase-3-Logos: Bögen = Achteck-Ecken mit 45°-Fasen, gerade Stämme, keine Schrift
  (eigene Pfade, keine Lizenzfrage). i-Punkte = Tropfen in derselben Form wie das LED-Fenster des Sensors
  (Kreis r + tangentiale Spitze h = 2.4 r über dem Mittelpunkt). Alle Flächen geschlossene Polygone, Löcher gegenläufig
  (fill-rule nonzero) -> direkt für KiCad-Silkscreen-Import, Bambu Studio (SVG-Relief) und Web.

Mindestmasse (JLC Silkscreen: Linie >= 0.15 mm, Text >= 1.0 mm hoch, research_fertigung.md Pkt. 7;
Projektempfehlung Strich >= 0.2 mm; FDM-Relief Düse 0.4 mm: Strich >= 0.8 mm = 2 Extrusionsbahnen,
absolute Grenze 0.45 mm = 1 Bahn) werden pro Variante ausgerechnet und ausgegeben (siehe main()).
"""
import math
import os
import shutil

OUT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(OUT, '..', '..', '..'))
INK = "#2B3036"        # Anthrazit
BLUE = "#4AA8DE"       # fluidi-Hellblau (Kappe/Taste, sRGB)
PAPER = "#FFFFFF"
GREY_BG = "#E6E5E1"

VARIANTS = {
    #            Strich  x-Höhe Oberlänge Fase  Bogenbreite Abstand Tropfen-r
    'A_linie':    dict(S=2.0, X=8.0, A=11.0, C=2.4, B=8.0, G=1.8, R=1.35, DG=0.9),
    'B_kraeftig': dict(S=2.6, X=8.6, A=11.4, C=2.6, B=9.0, G=1.9, R=1.75, DG=0.9),
}
DROP_K = 2.4           # Tropfen: Spitze 2.4 r über Kreismittelpunkt (wie LED-Fenster r 2.5 / Spitze 6.0 mm)


# ----------------------------------------------------------------------------- Grundformen
def octagon(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c),
            (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def drop(cx, cy, r, n=40):
    """Tropfen (CCW): Kreis um (cx, cy), Spitze DROP_K*r darüber, tangential angeschlossen."""
    h = DROP_K * r
    phi = math.asin(r / h)       # Tangentenpunkt: Winkel über der Horizontalen (Spitze tangential)
    pts = [(cx, cy + h)]
    a0, a1 = math.pi - phi, 2 * math.pi + phi
    for k in range(n + 1):
        t = a0 + (a1 - a0) * k / n
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    return pts


def ci(p):
    """Innere Fase bei Parallelversatz um den Strich S."""
    return p['C'] - p['S'] * (2 - math.sqrt(2))


# ----------------------------------------------------------------------------- Glyphen
def g_f(p):
    S, X, A, C = p['S'], p['X'], p['A'], p['C']
    hook = S + 1.75 * S          # Fahne oben rechts
    bar_l, bar_r = -0.75 * S, S + 1.25 * S
    CI = ci(p)
    xi = S + CI                  # innere Fase oben links: Linie x - y = xi - (A - S)
    # Schnitt der Innenfase mit der Querbalken-Oberkante y = X
    yi0 = A - S - CI             # Beginn der Innenfase am Stamm
    pts = [(0, 0), (S, 0), (S, X - S), (bar_r, X - S), (bar_r, X)]
    if yi0 < X:                  # Fase beginnt unterhalb der Balkenoberkante
        pts += [(X + xi - (A - S), X)]
    else:
        pts += [(S, X), (S, yi0)]
    pts += [(xi, A - S), (hook, A - S), (hook, A), (C, A), (0, A - C), (0, X), (bar_l, X), (bar_l, X - S), (0, X - S)]
    return [pts], bar_l, hook


def g_l(p):
    return [rect(0, 0, p['S'], p['A'])], 0, p['S']


def g_i(p):
    return [rect(0, 0, p['S'], p['X'])], 0, p['S']


def g_u(p):
    S, X, C, B = p['S'], p['X'], p['C'], p['B']
    CI = ci(p)
    pts = [(0, X), (0, C), (C, 0), (B, 0), (B, X), (B - S, X), (B - S, S), (S + CI, S), (S, S + CI), (S, X)]
    # CCW prüfen: (0,X)->(0,C) läuft nach unten auf der linken Seite = CCW
    return [pts], 0, B


def g_d(p):
    S, X, A, C, B = p['S'], p['X'], p['A'], p['C'], p['B']
    CI = ci(p)
    outer = [(C, 0), (B, 0), (B, A), (B - S, A), (B - S, X), (C, X), (0, X - C), (0, C)]
    inner = octagon(S, S, B - S, X - S, CI)[::-1]
    return [outer, inner], 0, B


def shift(polys, dx, dy=0.0):
    return [[(x + dx, y + dy) for x, y in pl] for pl in polys]


def wordmark(p, letters='fluidi'):
    """Liefert (Tinte-Polygone, Tropfen-Polygone, x0, x1, y0, y1)."""
    glyph = {'f': g_f, 'l': g_l, 'u': g_u, 'i': g_i, 'd': g_d}
    ink, drops = [], []
    x = 0.0
    xmin = None
    prev_right = None
    for ch in letters:
        polys, l, r = glyph[ch](p)
        if prev_right is not None:
            x = prev_right + p['G'] - l
        if ch == 'l' and prev_right is not None:
            x -= 0.25 * p['S']          # f-Fahne und l optisch näher
        ink += shift(polys, x)
        if xmin is None:
            xmin = x + l
        if ch == 'i':
            cx = x + p['S'] / 2
            cy = p['X'] + p['DG'] + p['R']
            drops.append(drop(cx, cy, p['R']))
        prev_right = x + r
    y1 = max(p['A'], p['X'] + p['DG'] + p['R'] * (1 + DROP_K))
    return ink, drops, xmin, prev_right, 0.0, y1


# ----------------------------------------------------------------------------- SVG
def to_d(polys, ox, oy, k, H):
    out = []
    for pl in polys:
        pts = [((x - ox) * k, H - (y - oy) * k) for x, y in pl]
        out.append("M" + " L".join(f"{a:.3f},{b:.3f}" for a, b in pts) + " Z")
    return " ".join(out)


def svg(w, h, body, title, desc, unit="mm"):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}{unit}" height="{h:.3f}{unit}" '
            f'viewBox="0 0 {w:.3f} {h:.3f}">\n<title>{title}</title>\n<desc>{desc}</desc>\n{body}</svg>\n')


def write(name, text):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(text)
    print("geschrieben", name)


DESC = ("fluidi-Wortmarke (klein, i-Punkte als Wassertropfen), eigene geometrische Pfade, keine Schrift. "
        "Erzeugt mit gen_logo_fluidi.py. 1 Einheit = 1 u (Massstab frei).")


def make_wordmarks():
    res = {}
    for name, p in VARIANTS.items():
        ink, drops, x0, x1, y0, y1 = wordmark(p)
        pad = 0.6
        W, H = (x1 - x0) + 2 * pad, (y1 - y0) + 2 * pad
        ox, oy = x0 - pad, y0 - pad
        di, dd = to_d(ink, ox, oy, 1, H), to_d(drops, ox, oy, 1, H)
        write(f"fluidi_{name}.svg", svg(W, H, f'<path fill="{INK}" fill-rule="nonzero" d="{di}"/>\n'
                                              f'<path fill="{BLUE}" fill-rule="nonzero" d="{dd}"/>\n',
                                        "fluidi", DESC + f" Variante {name}."))
        write(f"fluidi_{name}_mono.svg", svg(W, H, f'<path fill="#000000" fill-rule="nonzero" d="{di} {dd}"/>\n',
                                             "fluidi mono", DESC + " Einfarbig (Silkscreen, FDM-Relief, Prägung)."))
        write(f"fluidi_{name}_weiss.svg", svg(W, H, f'<path fill="{PAPER}" fill-rule="nonzero" d="{di}"/>\n'
                                                    f'<path fill="{BLUE}" fill-rule="nonzero" d="{dd}"/>\n',
                                              "fluidi negativ", DESC + " Negativ für dunkle Flächen."))
        res[name] = dict(p=p, ink=ink, drops=drops, box=(x0, x1, y0, y1))
    return res


def icon_polys():
    """Zwei Icons, 512 x 512, vollflächig (maskable: Motiv innerhalb Kreis r = 0.4 N um die Mitte)."""
    N = 512.0
    icons = {}
    # 1) "fi" mit Tropfen-Punkt (Variante B, kräftig: liest sich bei 48 px noch)
    p = VARIANTS['B_kraeftig']
    ink, drops, x0, x1, y0, y1 = wordmark(p, 'fi')
    w, h = x1 - x0, y1 - y0
    k = (0.56 * N) / max(w, h)           # Diagonale bleibt in der Sicherheitszone (geprüft unten)
    ox, oy = (x0 + x1) / 2 - N / 2 / k, (y0 + y1) / 2 - N / 2 / k
    icons['icon_fluidi_fi'] = dict(bg=PAPER, layers=[(INK, ink), (BLUE, drops)], k=k, ox=ox, oy=oy)
    # 2) ein Tropfen, weiss auf Hellblau
    r = 1.0
    dr = drop(0, 0, r, n=64)
    hgt = r * (1 + DROP_K)
    k2 = 0.62 * N / hgt
    ox2, oy2 = 0 - N / 2 / k2, (-r + DROP_K * r) / 2 - N / 2 / k2
    icons['icon_fluidi_tropfen'] = dict(bg=BLUE, layers=[(PAPER, [dr])], k=k2, ox=ox2, oy=oy2)
    return icons, N


def make_icons():
    icons, N = icon_polys()
    for name, ic in icons.items():
        body = f'<rect x="0" y="0" width="{N:.0f}" height="{N:.0f}" fill="{ic["bg"]}"/>\n'
        rmax = 0
        for col, polys in ic['layers']:
            body += f'<path fill="{col}" fill-rule="nonzero" d="{to_d(polys, ic["ox"], ic["oy"], ic["k"], N)}"/>\n'
            for pl in polys:
                for x, y in pl:
                    X, Y = (x - ic['ox']) * ic['k'], (y - ic['oy']) * ic['k']
                    rmax = max(rmax, math.hypot(X - N / 2, Y - N / 2))
        write(name + ".svg", svg(N, N, body, "fluidi " + name, "PWA-Icon 512 px, vollflächig, maskable "
                                 "(Motiv in Sicherheitskreis 0.4 N).", unit=""))
        print(f"  {name}: Motiv bis r = {rmax:.0f} px (Sicherheitszone maskable 205 px) ->",
              "OK" if rmax <= 205 else "AUSSERHALB")
    return icons, N


# ----------------------------------------------------------------------------- Raster-Vorschau (PIL)
def hexrgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def raster(layers, box, px_w, bg, pad_frac=0.08, ss=4):
    """layers: [(farbe, polys)], Polygone mit Löchern (gegenläufig) -> Even-odd über Maskenzeichnung."""
    from PIL import Image, ImageDraw
    x0, x1, y0, y1 = box
    w, h = x1 - x0, y1 - y0
    pad = pad_frac * w
    W = px_w * ss
    k = W / (w + 2 * pad)
    Hpx = int((h + 2 * pad) * k)
    img = Image.new('RGB', (W, Hpx), hexrgb(bg))
    for col, polys in layers:
        mask = Image.new('L', (W, Hpx), 0)
        dm = ImageDraw.Draw(mask)
        for pl in polys:
            pts = [((x - x0 + pad) * k, Hpx - (y - y0 + pad) * k) for x, y in pl]
            area = sum(pl[i - 1][0] * pl[i][1] - pl[i][0] * pl[i - 1][1] for i in range(len(pl)))
            dm.polygon(pts, fill=255 if area > 0 else 0)
        img.paste(Image.new('RGB', (W, Hpx), hexrgb(col)), (0, 0), mask)
    return img.resize((px_w, Hpx // ss), Image.LANCZOS)


def raster_icon(ic, N, px=512, ss=4):
    from PIL import Image, ImageDraw
    W = px * ss
    s = W / N
    img = Image.new('RGB', (W, W), hexrgb(ic['bg']))
    for col, polys in ic['layers']:
        mask = Image.new('L', (W, W), 0)
        dm = ImageDraw.Draw(mask)
        for pl in polys:
            pts = [((x - ic['ox']) * ic['k'] * s, (N - (y - ic['oy']) * ic['k']) * s) for x, y in pl]
            area = sum(pl[i - 1][0] * pl[i][1] - pl[i][0] * pl[i - 1][1] for i in range(len(pl)))
            dm.polygon(pts, fill=255 if area > 0 else 0)
        img.paste(Image.new('RGB', (W, W), hexrgb(col)), (0, 0), mask)
    return img.resize((px, px), Image.LANCZOS)


def round_corners(img, frac=0.22):
    from PIL import Image, ImageDraw
    m = Image.new('L', img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, img.size[0] - 1, img.size[1] - 1), radius=int(frac * img.size[0]), fill=255)
    out = Image.new('RGB', img.size, (255, 255, 255))
    out.paste(img, (0, 0), m)
    return out


def previews(res, icons, N):
    from PIL import Image, ImageDraw, ImageFont
    tiles = []
    for name, r in res.items():
        b = r['box']
        col = raster([(INK, r['ink']), (BLUE, r['drops'])], b, 900, PAPER)
        mono = raster([("#000000", r['ink'] + r['drops'])], b, 900, PAPER)
        neg = raster([(PAPER, r['ink']), (BLUE, r['drops'])], b, 900, "#7F878D")
        col.save(os.path.join(OUT, f'preview_fluidi_{name}.png'))
        tiles.append((name, col, mono, neg))
    ics = []
    for name, ic in icons.items():
        im = raster_icon(ic, N)
        im.save(os.path.join(OUT, f'preview_{name}.png'))
        ics.append((name, im))
    # Übersicht 1600 x 1200
    W, H = 1600, 1200
    sheet = Image.new('RGB', (W, H), (246, 246, 244))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
        fsm = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
    except OSError:
        font = fsm = ImageFont.load_default()
    y = 30
    for name, col, mono, neg in tiles:
        p = VARIANTS[name]
        d.text((40, y), f"Variante {name.replace('_', ' ')}  (Strich {p['S']} u, Tropfen r {p['R']} u)", fill=(40, 44, 50), font=font)
        y += 36
        tw = 480
        for i, (lab, im) in enumerate((("Farbe", col), ("Mono (Silkscreen/Relief)", mono), ("Negativ", neg))):
            t = im.resize((tw, int(im.size[1] * tw / im.size[0])), Image.LANCZOS)
            sheet.paste(t, (40 + i * (tw + 30), y))
            d.text((40 + i * (tw + 30), y + t.size[1] + 4), lab, fill=(90, 96, 104), font=fsm)
        y += t.size[1] + 44
    d.text((40, y), "PWA-Icons (512 px, maskable; Ansicht mit gerundeten Ecken)", fill=(40, 44, 50), font=font)
    y += 36
    x = 40
    for name, im in ics:
        xs = x
        for sz in (300, 96, 48):
            t = round_corners(im.resize((sz, sz), Image.LANCZOS))
            sheet.paste(t, (x, y + 300 - sz))
            x += sz + 24
        d.text((xs, y + 306), name.replace('icon_fluidi_', 'Icon ') + '  (300 / 96 / 48 px)', fill=(90, 96, 104), font=fsm)
        x += 60
    sheet = sheet.crop((0, 0, W, y + 350))
    sheet.save(os.path.join(OUT, 'logo_uebersicht.png'))
    dst = os.path.join(REPO, 'renders', 'phase3_v2')
    os.makedirs(dst, exist_ok=True)
    shutil.copy(os.path.join(OUT, 'logo_uebersicht.png'), os.path.join(dst, 'logo_uebersicht.png'))
    print('geschrieben logo_uebersicht.png (+ Kopie renders/phase3_v2/)')


def sizes(res):
    print("\nMindestmasse (Breite der Wortmarke in mm):")
    for name, r in res.items():
        p = r['p']
        x0, x1, y0, y1 = r['box']
        w_u, h_u = x1 - x0, y1 - y0
        smallest = min(p['S'], 2 * p['R'])
        print(f"  {name}: {w_u:.2f} x {h_u:.2f} u, Strich {p['S']} u, kleinstes Merkmal {smallest:.2f} u "
              f"(Tropfenbreite {2 * p['R']:.2f} u, Spitze rundet sich ab)")
        for lab, s_mm in (("JLC-Minimum Linie 0.15 mm", 0.15), ("Silkscreen empfohlen 0.2 mm", 0.20),
                          ("FDM 1 Bahn 0.45 mm", 0.45), ("FDM 2 Bahnen 0.8 mm", 0.80)):
            u = s_mm / smallest
            print(f"    {lab:30s}: Breite >= {w_u * u:5.1f} mm, Höhe {h_u * u:4.1f} mm, x-Höhe {p['X'] * u:4.2f} mm")
        for wmm in (12.0, 16.0, 18.0):
            u = wmm / w_u
            print(f"    bei {wmm:4.1f} mm Breite: Strich {p['S'] * u:.2f} mm, Tropfen {2 * p['R'] * u:.2f} mm breit, "
                  f"x-Höhe {p['X'] * u:.2f} mm, Gesamthöhe {h_u * u:.2f} mm")


def main():
    res = make_wordmarks()
    icons, N = make_icons()
    previews(res, icons, N)
    sizes(res)


if __name__ == "__main__":
    main()
