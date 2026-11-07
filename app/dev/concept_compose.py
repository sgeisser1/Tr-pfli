#!/usr/bin/env python3
"""fluidi – Vergleichsbilder der drei Stil-Entwürfe für docs/software/UI_ENTWUERFE.md.

Liest app/docs/concept/<entwurf>_<seite>_<geraet>_<schema>.png (concept_shots.sh) und legt je Seite,
Gerät und Schema die drei Entwürfe nebeneinander: app/docs/concept/vergleich/<seite>_<geraet>_<schema>.png

    python3 app/dev/concept_compose.py
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SRC = Path(__file__).resolve().parent.parent / "docs" / "concept"
OUT = SRC / "vergleich"
THEMES = [("frost", "A  fluidi Frost"), ("botanik", "B  fluidi Botanik"), ("stele", "C  fluidi Stele")]
PAGES = ["home", "pflanze", "raum", "dashboard", "statistik", "einstellungen", "profil", "raumeditor"]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def font(size):
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def compose(page, device, scheme):
    files = [SRC / f"{t}_{page}_{device}_{scheme}.png" for t, _ in THEMES]
    if not all(f.is_file() for f in files):
        return None
    ims = [Image.open(f).convert("RGB") for f in files]
    tile_w = 470 if device == "handy" else 900
    ims = [im.resize((tile_w, round(im.height * tile_w / im.width)), Image.LANCZOS) for im in ims]
    gap, head = 24, 52
    h = max(im.height for im in ims)
    dark = scheme == "dunkel"
    bg = (24, 26, 30) if dark else (246, 247, 249)
    fg = (235, 238, 242) if dark else (30, 34, 40)
    canvas = Image.new("RGB", (len(ims) * tile_w + (len(ims) + 1) * gap, h + head + gap), bg)
    d = ImageDraw.Draw(canvas)
    f = font(26 if device == "handy" else 34)
    for i, (im, (_, label)) in enumerate(zip(ims, THEMES)):
        x = gap + i * (tile_w + gap)
        d.text((x + 4, 12), label, fill=fg, font=f)
        canvas.paste(im, (x, head))
    OUT.mkdir(exist_ok=True)
    out = OUT / f"{page}_{device}_{scheme}.png"
    canvas.save(out, optimize=True)
    return out


def main():
    n = 0
    for page in PAGES:
        for device in ("handy", "desktop"):
            for scheme in ("hell", "dunkel"):
                if compose(page, device, scheme):
                    n += 1
    print(f"{n} Vergleichsbilder in {OUT}")


if __name__ == "__main__":
    main()
