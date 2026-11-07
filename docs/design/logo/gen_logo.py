#!/usr/bin/env python3
"""fluidi – Wortmarke und Icons als SVG (eigene Pfade, keine Schrift).

Aufruf:  python3 docs/design/logo/gen_logo.py
Erzeugt im selben Ordner:
  logo_v1_schlicht.svg       Wortmarke, Oktagon-Bögen, quadratische Punkte
  logo_v2_tropfen.svg        dito, Umlaut- und i-Punkte als Tropfen (verspielt)
  logo_v3_facette.svg        facettierter Tropfen (Bildmarke) + Wortmarke v1
  icon_v1.svg / icon_v2.svg / icon_v3.svg   quadratische PWA-Icons (512 x 512)
  *_mono.svg                 einfarbige Fassungen (Silkscreen / FDM-Relief)

Konstruktion (Einheiten u): Strich s = 2.0 u, x-Höhe 8 u, Oberlänge 11 u, Unterlänge 3.5 u,
Bögen = Achtecke mit 45°-Fasen (harte Form). Alle Konturen sind geschlossene Polygone
(gefüllt, Aussenkontur gegen den Uhrzeigersinn, Löcher im Uhrzeigersinn, fill-rule nonzero),
keine Überlappungen innerhalb eines Pfads ausser Loch-in-Kontur -> direkt als Fläche für
Silkscreen (KiCad-Import), Bambu Studio (SVG-Relief/Prägung) und Web nutzbar.

Mindestgrössen (JLC Silkscreen: Linie >= 0.15 mm, Text >= 1.0 mm, research_fertigung.md Z. 38-39):
  Strich s = 2.0 u. Gesamthöhe Wortmarke 15 u (Unterlänge bis Punkt).
  s >= 0.2 mm (Empfehlung) -> 1 u >= 0.1 mm -> Wortmarke >= 5.2 mm breit x 1.5 mm hoch.
  Empfohlen auf der Platine: 12 mm Breite (s = 0.46 mm).
  FDM-Relief/AMS-Inlay (Düse 0.4 mm): s >= 0.6 mm -> 1 u >= 0.3 mm -> Breite >= 15.6 mm.
"""
import math
import os

OUT = os.path.dirname(os.path.abspath(__file__))
S = 2.0                      # Strichstärke
C = 2.4                      # Fase der Achteck-Bögen aussen
CI = C - S * (2 - math.sqrt(2))   # Fase innen (Parallelversatz um S)
INK = "#2B3036"              # Anthrazit
BLUE = "#2E9BD6"             # Wasserblau
BLUE_D = "#1F78AE"           # Facette dunkel
PAPER = "#FFFFFF"


def octagon(x0, y0, x1, y1, c):
    return [(x0 + c, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1 - c),
            (x1 - c, y1), (x0 + c, y1), (x0, y1 - c), (x0, y0 + c)]


def ring(x0, y0, w, h):
    outer = octagon(x0, y0, x0 + w, y0 + h, C)
    inner = octagon(x0 + S, y0 + S, x0 + w - S, y0 + h - S, CI)[::-1]
    return [outer, inner]


def rect(x0, y0, x1, y1):
    return [[(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]


def shift(polys, dx, dy=0.0):
    return [[(x + dx, y + dy) for x, y in p] for p in polys]


# --- Glyphen (Ursprung links unten auf Grundlinie, y nach oben) -----------------------
def g_T():
    return [[(3, 0), (5, 0), (5, 9), (8, 9), (8, 11), (0, 11), (0, 9), (3, 9)]]


def g_r():
    # Stamm + Schulter mit Fase (wie Achteck-Bogen)
    return [[(0, 0), (2, 0), (2, 8 - S - CI), (2 + CI, 8 - S), (6.2, 6), (6.2, 8), (C, 8), (0, 8 - C)]]


def g_o():
    return ring(0, 0, 8, 8)


def g_p():
    outer = [(0, -3.5), (2, -3.5), (2, C - 2), (C, 0), (8 - C, 0), (8, C), (8, 8 - C), (8 - C, 8), (0, 8)]
    # Schnittpunkt Fase unten links mit Stammkante x=2: y = C - 2
    inner = octagon(S, S, 8 - S, 8 - S, CI)[::-1]
    return [outer, inner]


def g_f():
    xi = 2 + CI   # innere Fase oben
    # innere Fase x - y = (2+CI) - 9 ; Schnitt mit Querbalken-Oberkante y = 8
    x8 = 8 + (xi - 9)
    return [[(0, 0), (2, 0), (2, 6), (4.5, 6), (4.5, 8), (x8, 8), (xi, 9), (5.5, 9), (5.5, 11),
             (C, 11), (0, 11 - C), (0, 8), (-1.5, 8), (-1.5, 6), (0, 6)]]


def g_l():
    return rect(0, 0, 2, 11)


def g_i_stem():
    return rect(0, 0, 2, 8)


def dot_square(cx, cy, a=2.1):
    return rect(cx - a / 2, cy - a / 2, cx + a / 2, cy + a / 2)


def drop_path(cx, cy, r, h, rot_deg=0.0):
    """Tropfen: Kreis Radius r (Mittelpunkt cx,cy), Spitze h über dem Mittelpunkt.
    Als SVG-Pfad mit Bogen; gibt Pfad-String (Koordinaten in u, y nach oben!)."""
    # Tangentenpunkte von der Spitze an den Kreis
    a = math.asin(r / h)            # halber Öffnungswinkel an der Spitze
    # Tangentenpunkt-Winkel vom Mittelpunkt aus
    phi = math.pi / 2 - a
    rot = math.radians(rot_deg)

    def T(x, y):
        x, y = x - cx, y - cy
        return (cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot))

    tip = T(cx, cy + h)
    pr = T(cx + r * math.cos(phi), cy + r * math.sin(phi))
    pl = T(cx - r * math.cos(phi), cy + r * math.sin(phi))
    return ("drop", tip, pr, pl, r)


def drop_poly(cx, cy, r, h, rot_deg=0.0, n=24):
    """Tropfen als Polygon (CCW), für einfarbige Fassungen und Blender-Import robust."""
    a = math.asin(r / h)
    phi = math.pi / 2 - a
    pts = [(cx, cy + h)]
    # Bogen von linkem Tangentenpunkt über unten zum rechten (CCW): Winkel pi-phi .. 2pi+phi
    a0, a1 = math.pi - phi, 2 * math.pi + phi
    for k in range(n + 1):
        t = a0 + (a1 - a0) * k / n
        pts.append((cx + r * math.cos(t), cy + r * math.sin(t)))
    rot = math.radians(rot_deg)
    out = []
    for x, y in pts:
        x, y = x - cx, y - cy
        out.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
    return [out]


def facet_drop(cx, cy, scale=1.0):
    """Facettierter Tropfen: Spitze + Achteck-Unterteil. Liefert (aussen, linke Hälfte, rechte Hälfte)."""
    r = 5.0 * scale
    h = 9.6 * scale
    tip = (cx, cy + h)
    a = math.asin(r / h)
    phi = math.pi / 2 - a                       # Tangentenwinkel
    angs = [phi] + [math.radians(d) for d in (0, -45, -90, -135, -180)] + [math.pi - phi]
    # Facetten: rechte Tangente, 0°, -45°, -90° (unten), -135°, 180°, linke Tangente
    angs = [phi, math.radians(-10), math.radians(-55), math.radians(-90), math.radians(-125),
            math.radians(-170), math.pi - phi]
    pts = [(cx + r * math.cos(t), cy + r * math.sin(t)) for t in angs]
    outer = [tip] + pts[::-1]  # CCW: Spitze, links runter, unten, rechts hoch
    outer = [tip] + [pts[6], pts[5], pts[4], pts[3], pts[2], pts[1], pts[0]]
    bottom = pts[3]
    left = [tip, pts[6], pts[5], pts[4], bottom]
    right = [tip, bottom, pts[2], pts[1], pts[0]]
    return outer, left, right


# --- Wortmarke aufbauen ------------------------------------------------------------
GAP = 1.8


def wordmark(dots="square"):
    """Liefert Liste (polys, color, path_override) und Bounding Box."""
    items = []
    x = 0.0
    items.append(shift(g_T(), x)); x += 8 + GAP - 1.2
    items.append(shift(g_r(), x)); xr = x; x += 6.2 + GAP
    xo = x
    items.append(shift(g_o(), x)); x += 8 + GAP
    items.append(shift(g_p(), x)); x += 8 + GAP + 1.5
    items.append(shift(g_f(), x)); x += 5.5 + GAP
    items.append(shift(g_l(), x)); x += 2 + GAP
    xi = x
    items.append(shift(g_i_stem(), x)); x += 2
    width = x
    accents = []
    if dots == "square":
        items.append(dot_square(xo + 2.2, 10.3))
        items.append(dot_square(xo + 5.8, 10.3))
        items.append(dot_square(xi + 1, 10.3))
    elif dots == "drop":
        accents.append(drop_poly(xo + 2.1, 9.9, 1.3, 2.6, rot_deg=10))
        accents.append(drop_poly(xo + 5.9, 9.9, 1.3, 2.6, rot_deg=-10))
        accents.append(drop_poly(xi + 1, 9.9, 1.3, 2.6, rot_deg=0))
    return items, accents, width


def poly_to_d(polys, ox, oy, k, H):
    """u-Koordinaten (y oben) -> SVG (y unten). Skalierung k, Ursprung ox/oy, Höhe H."""
    d = []
    for p in polys:
        pts = [((x - ox) * k, H - (y - oy) * k) for x, y in p]
        d.append("M" + " L".join(f"{a:.3f},{b:.3f}" for a, b in pts) + " Z")
    return " ".join(d)


def svg(w, h, body, title, desc, unit="mm"):
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}{unit}" height="{h:.2f}{unit}" '
            f'viewBox="0 0 {w:.3f} {h:.3f}">\n<title>{title}</title>\n<desc>{desc}</desc>\n{body}</svg>\n')


def write(name, text):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(text)
    print("geschrieben", name)


LIC = ("fluidi-Wortmarke, eigene geometrische Pfade (keine Schrift). "
       "Erzeugt mit gen_logo.py. 1 Einheit = 1 mm im viewBox.")


def make_wordmark_files():
    pad = 1.0
    for name, dots in (("logo_v1_schlicht", "square"), ("logo_v2_tropfen", "drop")):
        items, accents, width = wordmark(dots)
        y0, y1 = -3.5, 11.9
        W, H = width + 2 * pad, (y1 - y0) + 2 * pad
        ink = " ".join(poly_to_d(p, -pad, y0 - pad, 1.0, H) for p in items)
        acc = " ".join(poly_to_d(p, -pad, y0 - pad, 1.0, H) for p in accents)
        body = f'<path fill="{INK}" fill-rule="nonzero" d="{ink}"/>\n'
        if acc:
            body += f'<path fill="{BLUE}" fill-rule="nonzero" d="{acc}"/>\n'
        write(name + ".svg", svg(W, H, body, "fluidi", LIC + f" Variante {dots}."))
        mono = f'<path fill="#000000" fill-rule="nonzero" d="{ink} {acc}"/>\n'
        write(name + "_mono.svg", svg(W, H, mono, "fluidi mono", LIC + " Einfarbig für Silkscreen/FDM."))

    # V3: facettierter Tropfen + Wortmarke v1 (i-Punkt quadratisch)
    items, _, width = wordmark("square")
    outer, left, right = facet_drop(0, 0, 1.0)
    dx = 6.0       # Tropfen links, Wortmarke daneben
    y0, y1 = -5.2, 11.9
    drop_h = 9.6 + 5.0
    k = (y1 - y0) / drop_h  # Tropfen gleich hoch wie Wortmarke
    def tr(poly, s=k, ox=dx, oy=None):
        oy = y0 + 5.0 * s if oy is None else oy
        return [[(ox + x * s, oy + y * s) for x, y in poly]]
    gapx = dx + 5.0 * k + 3.0
    W = gapx + width + 1.0
    H = (y1 - y0) + 2.0
    oy0 = y0 - 1.0
    L = poly_to_d(tr(left), 0, oy0, 1.0, H)
    R = poly_to_d(tr(right), 0, oy0, 1.0, H)
    O = poly_to_d(tr(outer), 0, oy0, 1.0, H)
    ink = " ".join(poly_to_d(shift(p, gapx, 0), 0, oy0, 1.0, H) for p in items)
    body = (f'<path fill="{BLUE}" d="{L}"/>\n<path fill="{BLUE_D}" d="{R}"/>\n'
            f'<path fill="{INK}" d="{ink}"/>\n')
    write("logo_v3_facette.svg", svg(W, H, body, "fluidi", LIC + " Bildmarke facettierter Tropfen."))
    write("logo_v3_facette_mono.svg", svg(W, H, f'<path fill="#000000" d="{O} {ink}"/>\n',
                                          "fluidi mono", LIC + " Einfarbig."))
    # Bildmarke allein (für Gehäuse/Druck)
    Wd = 2 * 5.0 * k + 2
    Hd = drop_h * k + 2
    Lm = poly_to_d(tr(left, ox=5.0 * k + 1, oy=5.0 * k + 1), 0, 0, 1.0, Hd)
    Rm = poly_to_d(tr(right, ox=5.0 * k + 1, oy=5.0 * k + 1), 0, 0, 1.0, Hd)
    write("mark_v3_tropfen.svg", svg(Wd, Hd, f'<path fill="{BLUE}" d="{Lm}"/>\n<path fill="{BLUE_D}" d="{Rm}"/>\n',
                                    "fluidi Bildmarke", LIC))


def make_icons():
    N = 512.0
    bg = f'<rect x="0" y="0" width="{N}" height="{N}" rx="112" ry="112" fill="{{}}"/>\n'
    # V1: Achteck-ö mit quadratischen Punkten, weiss auf blau
    o = g_o() + dot_square(2.2, 10.3) + dot_square(5.8, 10.3)
    k = 24.0
    ox, oy = 4.0 - N / 2 / k, 6.0 - N / 2 / k   # Zentrum der Glyphe (4,6) ins Bildzentrum
    d = " ".join(poly_to_d([p], ox, oy, k, N) for p in o)
    write("icon_v1.svg", svg(N, N, bg.format(BLUE) + f'<path fill="{PAPER}" d="{d}"/>\n',
                             "fluidi Icon v1", "PWA-Icon 512 px, Motiv in der 80-%-Sicherheitszone (maskable).", unit=""))
    # V2: Achteck-ö mit Tropfenpunkten, anthrazit + blau auf weiss
    ring_d = poly_to_d(g_o(), ox, oy, k, N)
    drops = drop_poly(2.1, 9.9, 1.3, 2.6, 10) + drop_poly(5.9, 9.9, 1.3, 2.6, -10)
    dd = " ".join(poly_to_d([p], ox, oy, k, N) for p in drops)
    write("icon_v2.svg", svg(N, N, bg.format("#F4F1EA") + f'<path fill="{INK}" d="{ring_d}"/>\n'
                             f'<path fill="{BLUE}" d="{dd}"/>\n', "fluidi Icon v2", "PWA-Icon 512 px.", unit=""))
    # V3: facettierter Tropfen auf weiss
    outer, left, right = facet_drop(0, 0, 1.0)
    k3 = 19.0
    ox3, oy3 = 0 - N / 2 / k3, 2.3 - N / 2 / k3
    Ld = poly_to_d([left], ox3, oy3, k3, N)
    Rd = poly_to_d([right], ox3, oy3, k3, N)
    write("icon_v3.svg", svg(N, N, bg.format("#FFFFFF") + f'<path fill="{BLUE}" d="{Ld}"/>\n'
                             f'<path fill="{BLUE_D}" d="{Rd}"/>\n', "fluidi Icon v3", "PWA-Icon 512 px.", unit=""))


if __name__ == "__main__":
    make_wordmark_files()
    make_icons()
