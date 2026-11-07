#!/usr/bin/env python3
"""Markdown -> PDF für fluidi-Dokumente (ohne Zusatzpakete).

Wandelt eine Markdown-Datei (Untermenge: Überschriften, Absätze, Tabellen, Listen, Codeblöcke,
Bilder, **fett**, *kursiv*, `code`, Links, ---) in HTML um, verkleinert eingebettete PNG-Bilder
zu JPEG (Pillow) und lässt Microsoft Edge (Windows, headless) daraus ein A4-PDF drucken.

Aufruf (WSL):  python3 scripts/md2pdf.py docs/design/DESIGN_PROPOSALS.md [ausgabe.pdf]
"""
import html, os, re, shutil, subprocess, sys, tempfile
from PIL import Image

EDGE = "/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
WIN_TMP = "/mnt/c/Users/steph/AppData/Local/Temp"

CSS = """
@page { size: A4; margin: 14mm 13mm 16mm 13mm; }
body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 9.6pt; line-height: 1.42; color: #1f2328; }
h1 { font-size: 19pt; color: #1b6fb5; border-bottom: 2px solid #1b6fb5; padding-bottom: 4px; margin-top: 0; }
h2 { font-size: 14pt; color: #1b6fb5; margin-top: 18px; break-after: avoid; }
h2.np { break-before: page; }
h3 { font-size: 11.5pt; margin-top: 14px; break-after: avoid; }
table { border-collapse: collapse; width: 100%; margin: 6px 0 10px; break-inside: auto; }
th, td { border: 1px solid #d0d7de; padding: 3px 6px; vertical-align: top; text-align: left; }
th { background: #eef4fa; }
tr { break-inside: avoid; }
td img { max-height: 48px; }
code { font-family: Consolas, monospace; font-size: 8.6pt; background: #f2f4f6; padding: 0 3px; border-radius: 3px; }
pre { background: #f2f4f6; padding: 6px 8px; font-size: 8.4pt; white-space: pre-wrap; }
hr { border: 0; border-top: 1px solid #d0d7de; margin: 12px 0; }
.gal { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; margin: 6px 0 10px; break-inside: avoid; }
.gal figure { margin: 0; } .gal figure:first-child { grid-column: 1 / span 2; }
.gal.one figure:first-child { grid-column: 1 / span 2; }
.gal img { width: 100%; border-radius: 4px; display: block; }
.gal figcaption { font-size: 8pt; color: #57606a; margin-top: 2px; }
.icons img { height: 70px; margin-right: 10px; }
.foot { margin-top: 18px; font-size: 7.5pt; color: #8c959f; }
"""

def inline(s, img):
    s = html.escape(s, quote=False)
    s = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', lambda m: f'<img alt="{m[1]}" src="{img(m[2])}">', s)
    s = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', s)
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![\w*])\*([^*\n]+)\*(?![\w*])', r'<i>\1</i>', s)
    return s

def convert(md_path, out_pdf):
    src_dir = os.path.dirname(os.path.abspath(md_path))
    work = tempfile.mkdtemp(prefix="fluidi_pdf_", dir=WIN_TMP)
    n = [0]
    def img(rel):
        p = os.path.normpath(os.path.join(src_dir, rel))
        n[0] += 1
        im = Image.open(p).convert("RGB")
        im.thumbnail((1500, 1500))
        name = f"img{n[0]:02d}.jpg"
        im.save(os.path.join(work, name), quality=88)
        return name

    lines = open(md_path, encoding="utf-8").read().splitlines()
    out, i, h2_count = [], 0, 0
    while i < len(lines):
        l = lines[i]
        if l.startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"): j += 1
            out.append("<pre>" + html.escape("\n".join(lines[i+1:j])) + "</pre>"); i = j + 1; continue
        m = re.match(r'^(#{1,4}) (.*)', l)
        if m:
            lvl = len(m[1]); cls = ""
            if lvl == 2:
                h2_count += 1
                cls = ' class="np"' if h2_count > 2 else ""
            out.append(f"<h{lvl}{cls}>{inline(m[2], img)}</h{lvl}>"); i += 1; continue
        if l.strip() == "---":
            out.append("<hr>"); i += 1; continue
        if l.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append(lines[i]); i += 1
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            has_head = len(cells) > 1 and all(re.fullmatch(r":?-{3,}:?", c) for c in cells[1])
            body = [r for k, r in enumerate(cells) if not (has_head and k == 1)]
            t = ["<table>"]
            for k, r in enumerate(body):
                tag = "th" if k == 0 and has_head else "td"
                if all(c == "" for c in r): continue
                t.append("<tr>" + "".join(f"<{tag}>{inline(c, img)}</{tag}>" for c in r) + "</tr>")
            out.append("\n".join(t) + "</table>"); continue
        if re.match(r'^!\[', l.strip()):
            figs = []
            while i < len(lines) and re.match(r'^!\[', lines[i].strip()):
                for alt, p in re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', lines[i]):
                    figs.append(f'<figure><img src="{img(p)}"><figcaption>{html.escape(alt)}</figcaption></figure>')
                i += 1
            out.append(f'<div class="gal{" one" if len(figs) == 1 else ""}">' + "".join(figs) + "</div>"); continue
        if re.match(r'^\s*([-*]|\d+\.) ', l):
            ordered = bool(re.match(r'^\s*\d+\.', l)); tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines) and (re.match(r'^\s*([-*]|\d+\.) ', lines[i]) or (lines[i].startswith("  ") and lines[i].strip())):
                if re.match(r'^\s*([-*]|\d+\.) ', lines[i]):
                    items.append(re.sub(r'^\s*([-*]|\d+\.) ', '', lines[i]))
                else:
                    items[-1] += " " + lines[i].strip()
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x, img)}</li>" for x in items) + f"</{tag}>"); continue
        if not l.strip():
            i += 1; continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|\||```|---$|\s*([-*]|\d+\.) )', lines[i]):
            para.append(lines[i]); i += 1
        txt = " ".join(para)
        cls = ' class="icons"' if txt.count("![") > 1 else ""
        out.append(f"<p{cls}>{inline(txt, img)}</p>")

    title = os.path.basename(md_path)
    doc = (f"<!doctype html><html lang='de'><head><meta charset='utf-8'><title>{title}</title>"
           f"<style>{CSS}</style></head><body>{''.join(out)}"
           f"<div class='foot'>Erzeugt aus {html.escape(os.path.relpath(md_path))} mit scripts/md2pdf.py</div></body></html>")
    hp = os.path.join(work, "doc.html")
    open(hp, "w", encoding="utf-8").write(doc)
    pdf_tmp = os.path.join(work, "out.pdf")
    win = lambda p: subprocess.check_output(["wslpath", "-w", p], text=True).strip()
    subprocess.run([EDGE, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={win(pdf_tmp)}", "file:///" + win(hp).replace("\\", "/")],
                   check=True, timeout=180, capture_output=True)
    shutil.copy(pdf_tmp, out_pdf)
    shutil.rmtree(work, ignore_errors=True)
    print(f"{out_pdf}: {os.path.getsize(out_pdf)/1e6:.1f} MB, {n[0]} Bilder")

if __name__ == "__main__":
    md = sys.argv[1]
    convert(md, sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(md)[0] + ".pdf")
