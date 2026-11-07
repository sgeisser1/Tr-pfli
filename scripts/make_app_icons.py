"""fluidi App-Icon (final, D-011): Icon-Dateien aus dem Blender-Rohrender erzeugen (Pillow + numpy).

Aufruf:  .venv/bin/python scripts/make_app_icons.py [rohrender.png]
Eingang: renders/phase3_v3/app_icon_render_2048.png  (renders/gen/render_app_icon.py, Cycles ohne Denoiser)
Ausgang: app/icons/icon-1024/512/192/180/96/48.png, favicon-32/16.png, icon-maskable-512.png,
         app/icons/favicon.ico (16 + 32), renders/phase3_v3/app_icon_uebersicht.png

Nachbearbeitung (einzige Eingriffe ins Rendering, alle hier dokumentiert):
 1. Rauschglättung NUR im Glühbereich: Maske = Pixel, deren Blauanteil deutlich über Rot liegt UND die heller
    als die Kappe sind (Tropfen, blauer Lichtsaum in der Kerbe und im Fugenspalt), weich ausgeblendet
    (Gauss 12 px); dort Gauss-Weichzeichner Radius GLOW_BLUR px (bei 2048 px). Kappe, Grau, Fuge unverändert.
 2. Verkleinern mit Lanczos (aus 2048 px, bzw. Zwischenstufe 2x für sehr kleine Grössen).
 3. Ab 48 px und kleiner: engerer Ausschnitt (SMALL_CROP der Bildbreite, mittig) -> Tropfen grösser, plus
    leichte Unschärfemaske, damit Fuge und Tropfen auch bei 16/32 px lesbar bleiben.
Maskable (W3C "maskable"): Motiv füllt das Quadrat bis an den Rand; Tropfen inkl. Glühen liegt vollständig in
der Sicherheitszone (Kreis 80 % Durchmesser) – wird hier numerisch geprüft und ausgegeben.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, 'renders/phase3_v3/app_icon_render_2048.png')
OUT = os.path.join(REPO, 'app/icons')
OVERVIEW = os.path.join(REPO, 'renders/phase3_v3/app_icon_uebersicht.png')
GLOW_BLUR = 2.0
SMALL_CROP = 0.78           # Anteil der Bildbreite für <= 48 px
SIZES = [('icon-1024.png', 1024), ('icon-512.png', 512), ('icon-192.png', 192), ('icon-180.png', 180),
         ('icon-96.png', 96), ('icon-48.png', 48), ('favicon-32.png', 32), ('favicon-16.png', 16)]


def glow_mask(im):
    a = np.asarray(im.convert('RGB'), dtype=np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    cap_lum = np.median(a[: a.shape[0] // 8].mean(axis=2))          # Kappe oben als Referenz
    lum = a.mean(axis=2)
    m = ((b - r) > 25) & (lum > cap_lum + 8)
    m |= (b > 225) & (g > 225)                                        # heller Tropfenkern
    mk = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(12))
    return mk, m


def smooth_glow(im):
    mk, _ = glow_mask(im)
    return Image.composite(im.filter(ImageFilter.GaussianBlur(GLOW_BLUR)), im, mk)


def drop_extent(im):
    """Lage des leuchtenden Tropfens (inkl. Glühsaum) relativ zur Bildmitte, in Anteilen der Bildgrösse."""
    _, m = glow_mask(im)
    ys, xs = np.nonzero(m)
    h, w = m.shape
    cx, cy = (w - 1) / 2, (h - 1) / 2
    rmax = np.sqrt(((xs - cx) / w) ** 2 + ((ys - cy) / h) ** 2).max()
    return dict(top=ys.min() / h, bottom=ys.max() / h, left=xs.min() / w, right=xs.max() / w, rmax=rmax)


def scaled(src, size):
    w = src.width
    if size <= 48:
        c = int(round(w * SMALL_CROP))
        o = (w - c) // 2
        src = src.crop((o, o, o + c, o + c))
        mid = src.resize((size * 4, size * 4), Image.LANCZOS)
        out = mid.resize((size, size), Image.LANCZOS)
        return out.filter(ImageFilter.UnsharpMask(radius=1, percent=35 if size >= 32 else 25, threshold=0))
    return src.resize((size, size), Image.LANCZOS)


def round_mask(size, kind):
    s = 4
    mk = Image.new('L', (size * s, size * s), 0)
    d = ImageDraw.Draw(mk)
    if kind == 'kreis':
        d.ellipse((0, 0, size * s - 1, size * s - 1), fill=255)
    else:                                                               # Rundquadrat, Radius 22.5 %
        d.rounded_rectangle((0, 0, size * s - 1, size * s - 1), radius=int(0.225 * size * s), fill=255)
    return mk.resize((size, size), Image.LANCZOS)


def overview(icons, maskable, ext):
    font = ImageFont.load_default()
    try:
        font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
        fbig = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
    except OSError:
        fbig = font
    show = [192, 180, 96, 48, 32, 16]          # 512 steht unten (maskable, drei Masken)
    W, pad = 1960, 30
    rows = [('Hell, Rundquadrat', (246, 245, 242), 'rund'), ('Dunkel, Rundquadrat', (32, 33, 36), 'rund'),
            ('Hell, Kreis (Android)', (246, 245, 242), 'kreis'), ('Dunkel, Kreis (Android)', (32, 33, 36), 'kreis')]
    rh = 192 + 90
    H = 80 + len(rows) * rh + 620
    sheet = Image.new('RGB', (W, H), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 24), 'fluidi App-Icon (final) - Nahaufnahme Sensor, Tropfen blau  |  alle Grössen 1:1', fill=(40, 40, 40), font=fbig)
    y = 80
    for label, bg, kind in rows:
        d.rectangle((0, y, W, y + rh - 10), fill=bg)
        tc = (60, 60, 60) if sum(bg) > 300 else (220, 220, 220)
        d.text((pad, y + 10), label, fill=tc, font=font)
        x = pad
        for s in show:
            im = icons[s]
            sheet.paste(im, (x, y + 45), round_mask(s, kind))
            d.text((x, y + 45 + s + 6), f'{s} px', fill=tc, font=font)
            x += max(s, 40) + 50
        y += rh
    # Maskable mit Sicherheitszone
    d.text((pad, y + 10), '512 px, maskable (Motiv bis an den Rand), Sicherheitszone 80 % (rot gestrichelt), Kreis- und Rundquadrat-Maske',
           fill=(40, 40, 40), font=font)
    m = maskable.copy()
    dm = ImageDraw.Draw(m)
    r = 0.4 * 512
    import math
    for k in range(72):
        if k % 2 == 0:
            a0, a1 = 5 * k, 5 * k + 5
            dm.arc((256 - r, 256 - r, 256 + r, 256 + r), a0, a1, fill=(220, 30, 30), width=3)
    sheet.paste(m, (pad, y + 45))
    sheet.paste(maskable, (pad + 560, y + 45), round_mask(512, 'kreis'))
    sheet.paste(maskable, (pad + 1120, y + 45), round_mask(512, 'rund'))
    d.text((pad + 1660, y + 60), 'Tropfen inkl. Glühen:', fill=(40, 40, 40), font=font)
    d.text((pad + 1660, y + 85), f'max. Abstand zur Mitte', fill=(40, 40, 40), font=font)
    d.text((pad + 1660, y + 110), f'{ext["rmax"] * 100:.1f} % der Kante', fill=(40, 40, 40), font=font)
    d.text((pad + 1660, y + 135), '(Grenze 40 %)', fill=(40, 40, 40), font=font)
    sheet.save(OVERVIEW)
    return OVERVIEW


def main(raw=RAW):
    os.makedirs(OUT, exist_ok=True)
    src = Image.open(raw).convert('RGB')
    assert src.width == src.height, 'Rohrender muss quadratisch sein'
    src = smooth_glow(src)
    icons = {}
    for name, s in SIZES:
        im = scaled(src, s)
        im.save(os.path.join(OUT, name), optimize=True)
        icons[s] = im
    # Maskable: gleicher Ausschnitt; Sicherheitszone prüfen
    ext = drop_extent(src)
    assert ext['rmax'] <= 0.40, f'Tropfen ragt aus der Sicherheitszone: {ext}'
    mask512 = src.resize((512, 512), Image.LANCZOS)
    mask512.save(os.path.join(OUT, 'icon-maskable-512.png'), optimize=True)
    icons[32].save(os.path.join(OUT, 'favicon.ico'), sizes=[(16, 16), (32, 32)], append_images=[icons[16]])
    print('Tropfen (inkl. Glühen) relativ:', {k: round(v, 3) for k, v in ext.items()})
    print('Höhe Tropfen+Glühen: %.1f %%' % ((ext['bottom'] - ext['top']) * 100))
    print('Übersicht:', overview(icons, mask512, ext))
    for f in sorted(os.listdir(OUT)):
        print(f, Image.open(os.path.join(OUT, f)).size, os.path.getsize(os.path.join(OUT, f)), 'B')


if __name__ == '__main__':
    main(*sys.argv[1:2])
