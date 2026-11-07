"""PWA-Kriterien ohne Browser-Installation (Lighthouse-ähnlich, statisch geprüft).

Manifest (Name, start_url, display, Farben, Icons inkl. 192/512/maskable mit echten PNG-Grössen),
Service Worker (alle Shell-Dateien existieren, API wird nicht gecacht), index.html (Viewport,
theme-color, apple-touch-icon, Manifest-Link), keine externen Ressourcen (REQ-APP-09),
keine Inline-Skripte/-Styles (CSP), Prüfsummen der vendored Bibliothek.
"""
import hashlib
import json
import re
import struct
import unittest
from pathlib import Path

APP = Path(__file__).resolve().parent.parent
SHELL_DIRS = ["index.html", "sw.js", "manifest.webmanifest", "css", "js"]


def png_size(p: Path):
    b = p.read_bytes()[:24]
    assert b[:8] == b"\x89PNG\r\n\x1a\n", p
    return struct.unpack(">II", b[16:24])


def shell_files():
    for name in SHELL_DIRS:
        p = APP / name
        if p.is_dir():
            yield from (f for f in p.rglob("*") if f.is_file())
        else:
            yield p


class Manifest(unittest.TestCase):
    def setUp(self):
        self.m = json.loads((APP / "manifest.webmanifest").read_text(encoding="utf-8"))

    def test_required_fields(self):
        m = self.m
        self.assertEqual(m["name"], "fluidi")
        self.assertEqual(m["short_name"], "fluidi")
        self.assertIn(m["display"], ("standalone", "fullscreen", "minimal-ui"))
        self.assertTrue(m["start_url"])
        self.assertRegex(m["theme_color"], r"^#[0-9A-Fa-f]{6}$")
        self.assertRegex(m["background_color"], r"^#[0-9A-Fa-f]{6}$")
        self.assertTrue(m["lang"].startswith("de"))

    def test_icons_exist_and_sizes_match(self):
        sizes = set()
        maskable = False
        for ic in self.m["icons"]:
            p = APP / ic["src"]
            self.assertTrue(p.is_file(), ic["src"])
            w, h = png_size(p)
            self.assertEqual(f"{w}x{h}", ic["sizes"], ic["src"])
            sizes.add(ic["sizes"])
            maskable |= "maskable" in ic.get("purpose", "")
        self.assertIn("192x192", sizes)
        self.assertIn("512x512", sizes)
        self.assertTrue(maskable)


class Html(unittest.TestCase):
    def setUp(self):
        self.html = (APP / "index.html").read_text(encoding="utf-8")

    def test_head(self):
        h = self.html
        self.assertIn('name="viewport"', h)
        self.assertIn('rel="manifest"', h)
        self.assertIn('name="theme-color"', h)
        self.assertIn('rel="apple-touch-icon" href="icons/icon-180.png"', h)
        self.assertEqual(png_size(APP / "icons/icon-180.png"), (180, 180))
        self.assertIn('lang="de', h)

    def test_no_inline_script_or_style(self):
        self.assertIsNone(re.search(r"<script(?![^>]*\bsrc=)[^>]*>", self.html))
        self.assertNotIn("<style", self.html)
        self.assertIsNone(re.search(r"\sstyle=", self.html))
        self.assertIsNone(re.search(r"\son[a-z]+=", self.html))

    def test_referenced_files_exist(self):
        for ref in re.findall(r'(?:src|href)="([^"#:]+)"', self.html):
            self.assertTrue((APP / ref).is_file(), ref)


class NoExternal(unittest.TestCase):
    def test_no_external_urls_at_runtime(self):
        rx = re.compile(r"(?:https?:)?//(?!www\.w3\.org/2000/svg)[a-z0-9.-]+\.[a-z]{2,}", re.I)
        for f in list(shell_files()) + [APP / "img/logo.svg"]:
            if f.suffix not in (".html", ".js", ".css", ".webmanifest", ".svg"):
                continue
            txt = f.read_text(encoding="utf-8")
            txt = re.sub(r"//[^\n]*", "", txt) if f.suffix == ".js" else txt  # Kommentare ignorieren
            hits = [m.group(0) for m in rx.finditer(txt) if "w3.org" not in m.group(0)]
            self.assertEqual(hits, [], f)

    def test_no_innerhtml_with_data(self):
        for f in (APP / "js").rglob("*.js"):
            self.assertIsNone(re.search(r"\.(innerHTML|outerHTML)\s*=|insertAdjacentHTML|document\.write", f.read_text(encoding="utf-8")), f.name)

    def test_vendor_checksums(self):
        src = (APP / "vendor/uplot/SOURCE.md").read_text(encoding="utf-8")
        for name, digest in re.findall(r"\| `([^`]+)` \| `[^`]+` \| `([0-9a-f]{64})` \|", src):
            self.assertEqual(hashlib.sha256((APP / "vendor/uplot" / name).read_bytes()).hexdigest(), digest, name)
        self.assertTrue((APP / "vendor/uplot/LICENSE").is_file())


class ServiceWorker(unittest.TestCase):
    def setUp(self):
        self.sw = (APP / "sw.js").read_text(encoding="utf-8")

    def test_shell_files_exist(self):
        block = re.search(r"const SHELL = \[(.*?)\];", self.sw, re.S).group(1)
        files = re.findall(r"'([^']+)'", block)
        self.assertIn("index.html", files)
        for f in files:
            if f == "./":
                continue
            self.assertTrue((APP / f).is_file(), f)
        # alle JS-Module sind in der Shell (sonst offline unvollständig)
        js = {str(p.relative_to(APP)) for p in (APP / "js").rglob("*.js")}
        self.assertEqual(js - set(files), set())

    def test_handlers_and_api_policy(self):
        for ev in ("install", "activate", "fetch"):
            self.assertIn(f"addEventListener('{ev}'", self.sw)
        self.assertIn("url.pathname.startsWith('/api/')", self.sw)  # API nicht aus dem Shell-Cache


class PublicDashboard(unittest.TestCase):
    """Öffentliches Dashboard (eigener HTTP-Port, D-020): nur wenige Dateien, keine Inline-Skripte, nur GET /dashboard."""

    def test_page_and_import_graph(self):
        html = (APP / "dashboard.html").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html))
        self.assertIsNone(re.search(r"\sstyle=", html))
        for ref in re.findall(r'(?:src|href)="([^"#:]+)"', html):
            self.assertTrue((APP / ref).is_file(), ref)
        seen, todo = set(), ["dashboard.js"]
        while todo:
            f = todo.pop()
            seen.add(f)
            for imp in re.findall(r"from '\./([\w-]+\.js)'", (APP / "js" / f).read_text(encoding="utf-8")):
                if imp not in seen:
                    todo.append(imp)
        # muss zur Freigabeliste des Gateways passen (server.py DASH_FILES)
        self.assertEqual(seen, {"dashboard.js", "board.js", "dom.js", "art.js"})
        src = (APP / "js" / "dashboard.js").read_text(encoding="utf-8")
        self.assertIn("api/v1/dashboard", src)
        self.assertEqual(set(re.findall(r"api/v1/[a-z/]+", src)), {"api/v1/dashboard"})


class FrostOnly(unittest.TestCase):
    def test_single_style(self):
        css = (APP / "css" / "app.css").read_text(encoding="utf-8")
        self.assertIn('html[data-theme="frost"][data-scheme="dark"]', css)
        self.assertNotIn('data-theme="botanik"', css)
        self.assertNotIn('data-theme="stele"', css)
        self.assertIn('data-theme="frost"', (APP / "index.html").read_text(encoding="utf-8"))


class ConceptDrafts(unittest.TestCase):
    """Klickbare Stil-Entwürfe (app/concept/): gleiche Regeln wie die PWA (REQ-APP-09, CSP)."""
    C = APP / "concept"

    def test_index_no_inline_and_files_exist(self):
        html = (self.C / "index.html").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r"<script(?![^>]*\bsrc=)[^>]*>", html))
        self.assertNotIn("<style", html)
        self.assertIsNone(re.search(r"\sstyle=", html))
        for ref in re.findall(r'(?:src|href)="([^"#:]+)"', html):
            self.assertTrue((self.C / ref).resolve().is_file(), ref)
        for t in ("frost", "botanik", "stele"):
            self.assertIn(f'css/{t}.css', html)

    def test_no_external_and_no_innerhtml(self):
        rx = re.compile(r"(?:https?:)?//(?!www\.w3\.org/2000/svg)[a-z0-9.-]+\.[a-z]{2,}", re.I)
        for f in list(self.C.rglob("*.js")) + list(self.C.rglob("*.css")) + list(self.C.rglob("*.html")):
            txt = f.read_text(encoding="utf-8")
            if f.suffix == ".js":
                self.assertIsNone(re.search(r"\.(innerHTML|outerHTML)\s*=|insertAdjacentHTML|document\.write", txt), f.name)
                txt = re.sub(r"//[^\n]*", "", txt)
            hits = [m.group(0) for m in rx.finditer(txt) if "w3.org" not in m.group(0)]
            self.assertEqual(hits, [], f)

    def test_imports_resolve(self):
        for f in (self.C / "js").glob("*.js"):
            for imp in re.findall(r"from '(\./[^']+)'", f.read_text(encoding="utf-8")):
                self.assertTrue((f.parent / imp).is_file(), f"{f.name}: {imp}")

    def test_themes_have_dark_mode(self):
        for t in ("frost", "botanik", "stele"):
            css = (self.C / "css" / f"{t}.css").read_text(encoding="utf-8")
            self.assertIn(f'html[data-theme="{t}"][data-scheme="dark"]', css)


if __name__ == "__main__":
    unittest.main()
