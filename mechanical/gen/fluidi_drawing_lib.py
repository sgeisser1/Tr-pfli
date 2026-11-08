# -*- coding: utf-8 -*-
"""fluidi - Zeichnungsbibliothek (FreeCAD 0.21.2 headless + matplotlib), ISO-nahe Fertigungszeichnungen.

Warum nicht TechDraw-Seiten: In FreeCAD 0.21.2 rechnet TechDraw die Ansichten zwar headless, der Export einer Seite
als PDF/SVG und die Darstellung der Bemassung laufen aber nur ueber TechDrawGui (GUI-Thread). Deshalb:
  - Kanten: TechDraw.projectEx (Hidden-Line-Removal von OpenCascade, headless) -> sichtbar / verdeckt,
  - Schnitte: Boolean mit einem Halbraum, Schnittflaechen schraffiert (45 Grad, ISO 128-50),
  - Bemassung: jede Masszahl wird aus zwei Modellpunkten (3D) berechnet; jeder Messpunkt wird gegen die Geometrie
    geprueft (Abstand zur Oberflaeche < 0.005 mm), Ergebnis im Pruefprotokoll. Keine Masszahl wird von Hand gesetzt.
Projektionsmethode 1 (ISO E, ISO 5456-2): Draufsicht unter, Ansicht von links rechts neben der Vorderansicht.
"""
import math
import os
import subprocess

import FreeCAD as App
import Part
import TechDraw

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt                      # noqa: E402
from matplotlib.patches import PathPatch, Polygon, FancyBboxPatch, Rectangle, Circle   # noqa: E402
from matplotlib.path import Path                     # noqa: E402
from matplotlib.collections import LineCollection    # noqa: E402

V = App.Vector
MM2PT = 72.0 / 25.4
LW_TH = 0.35 * MM2PT          # Liniengruppe 0.35 (ISO 128-20): breit 0.35, schmal 0.18
LW_TN = 0.18 * MM2PT
TXT = 2.5                     # Schrifthoehe Masszahlen (mm)
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['pdf.fonttype'] = 42

# Blickrichtungen: (rechts, oben) im Bild; Betrachter auf der Seite rechts x oben
VIEWS = {'front': ((1, 0, 0), (0, 0, 1)), 'back': ((-1, 0, 0), (0, 0, 1)),
         'top': ((1, 0, 0), (0, 1, 0)), 'bottom': ((1, 0, 0), (0, -1, 0)),
         'left': ((0, -1, 0), (0, 0, 1)), 'right': ((0, 1, 0), (0, 0, 1))}


def fs(h_mm):
    """Schriftgroesse (pt) fuer Versalhoehe h_mm."""
    return h_mm * MM2PT / 0.73


def fmt(v, nd=2):
    s = ('%.*f' % (nd, v)).rstrip('0').rstrip('.')
    return '0' if s in ('-0', '') else s


def git_stand(repo, paths):
    try:
        h = subprocess.check_output(['git', '-C', repo, 'rev-parse', '--short', 'HEAD']).decode().strip()
        st = subprocess.check_output(['git', '-C', repo, 'status', '--porcelain', '--'] + paths).decode().strip()
        return h + (' + Arbeitsstand' if st else '')
    except Exception:
        return 'unbekannt'


def _pts(edge, defl=0.004):
    try:
        p = edge.discretize(Deflection=defl)
    except Exception:
        p = [v.Point for v in edge.Vertexes]
    return [(q.x, q.y) for q in p]


class Sheet:
    def __init__(self, fmt_, number, title, subtitle, material, scale, orient, stand, source, notes, sheet='1/1',
                 date=''):
        self.W, self.H = {'A4': (297.0, 210.0), 'A3': (420.0, 297.0)}[fmt_]
        self.fmt = fmt_
        self.number = number
        self.title = title
        self.fig = plt.figure(figsize=(self.W / 25.4, self.H / 25.4))
        ax = self.fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, self.W)
        ax.set_ylim(0, self.H)
        ax.set_aspect('equal')
        ax.axis('off')
        self.ax = ax
        self.checks = []
        self._frame()
        self._title_block(number, title, subtitle, material, scale, orient, stand, source, sheet, date)
        self._notes(notes)

    # ------------------------------------------------------------------ Rahmen, Schriftfeld (ISO 5457 / ISO 7200 vereinfacht)
    def line(self, pts, lw=LW_TN, ls='-', color='k', z=3, clip=None):
        xs, ys = zip(*pts)
        ln, = self.ax.plot(xs, ys, color=color, lw=lw, ls=ls, solid_capstyle='butt', zorder=z)
        if clip is not None:
            ln.set_clip_path(clip)
        return ln

    def text(self, x, y, s, h=TXT, ha='left', va='baseline', rot=0, weight='normal', color='k', z=6, **kw):
        return self.ax.text(x, y, s, fontsize=fs(h), ha=ha, va=va, rotation=rot, weight=weight, color=color, zorder=z,
                            **kw)

    def _frame(self):
        W, H = self.W, self.H
        self.ax.add_patch(Rectangle((20, 10), W - 30, H - 20, fill=False, lw=0.7 * MM2PT, zorder=2))
        for x in (W / 2,):                                         # Mittenmarken
            self.line([(x, 5), (x, 10)], lw=0.7 * MM2PT)
            self.line([(x, H - 10), (x, H - 5)], lw=0.7 * MM2PT)
        self.line([(15, H / 2), (20, H / 2)], lw=0.7 * MM2PT)
        self.line([(W - 10, H / 2), (W - 5, H / 2)], lw=0.7 * MM2PT)

    def _cell(self, x, y, w, h, label, value, vh=3.0, weight='normal'):
        self.ax.add_patch(Rectangle((x, y), w, h, fill=False, lw=LW_TN, zorder=2))
        self.text(x + 1.0, y + h - 2.2, label, h=1.4, color='0.35')
        lines = value.split('\n')
        for i, l in enumerate(lines):
            self.text(x + 1.2, y + 1.3 + (len(lines) - 1 - i) * (vh + 1.0), l, h=vh, weight=weight)

    def _title_block(self, number, title, subtitle, material, scale, orient, stand, source, sheet, date):
        x0, y0 = self.W - 10 - 180, 10
        self.tb = (x0, y0, 180, 52)
        self.ax.add_patch(Rectangle((x0, y0), 180, 52, fill=False, lw=0.7 * MM2PT, zorder=2))
        self._cell(x0, y0 + 40, 140, 12, 'Benennung', title, vh=4.2 if len(title) <= 34 else 3.3, weight='bold')
        self._cell(x0 + 140, y0 + 40, 40, 12, 'Projekt', 'fluidi', vh=4.2, weight='bold')
        self._cell(x0, y0 + 32, 140, 8, 'Benennung 2 / Funktion', subtitle, vh=2.4 if len(subtitle) <= 70 else 1.9)
        self._cell(x0 + 140, y0 + 32, 40, 8, 'Sachnummer', number, vh=3.0, weight='bold')
        self._cell(x0, y0 + 24, 105, 8, 'Werkstoff', material, vh=2.0)
        self._cell(x0 + 105, y0 + 24, 35, 8, 'Massstab', scale, vh=3.0 if len(scale) < 9 else 2.2)
        self._cell(x0 + 140, y0 + 16, 40, 16, 'Projektion ISO E (Methode 1)', '', vh=2.4)
        self._proj_symbol(x0 + 160, y0 + 22.5)
        self._cell(x0, y0 + 16, 140, 8, 'Druck Bambu Lab P1S (Ausrichtung)', orient, vh=2.2 if len(orient) <= 85 else 1.9)
        self._cell(x0, y0 + 8, 140, 8, 'Stand / Commit', stand, vh=2.2)
        self._cell(x0 + 140, y0 + 8, 40, 8, 'Format / Blatt', '%s   %s' % (self.fmt, sheet), vh=2.6)
        self._cell(x0, y0, 140, 8, 'Quelle (Modell, Generator)', source, vh=2.0)
        self._cell(x0 + 140, y0, 40, 8, 'Datum', date, vh=2.6)

    def _proj_symbol(self, cx, cy):
        """ISO 5456-2 Methode 1: Kegelstumpf (kleines Ende links) links, Stirnansicht (2 Kreise) rechts."""
        h = 4.0
        d1, d2, L = h * 0.5, h, h * 1.1
        xl = cx - 11
        self.ax.add_patch(Polygon([(xl, cy - d1 / 2), (xl + L, cy - d2 / 2), (xl + L, cy + d2 / 2), (xl, cy + d1 / 2)],
                                  closed=True, fill=False, lw=LW_TH, zorder=3))
        xc = cx + 5
        self.ax.add_patch(Circle((xc, cy), d2 / 2, fill=False, lw=LW_TH, zorder=3))
        self.ax.add_patch(Circle((xc, cy), d1 / 2, fill=False, lw=LW_TH, zorder=3))
        self.line([(xl - 1.5, cy), (xc + d2 / 2 + 1.5, cy)], lw=LW_TN, ls=(0, (6, 1.5, 1, 1.5)))

    def _notes(self, notes):
        x0, y0, w, h = self.tb
        y = y0 + h + 3 + 3.6 * (len(notes) - 1)
        for n in notes:
            self.text(x0, y, n, h=1.9)
            y -= 3.6

    def check(self, what, value, pts, shape, tol=0.005):
        res = []
        for p in pts:
            d = shape.distToShape(Part.Vertex(V(*p)))[0]
            res.append(d)
        ok = all(d < tol for d in res)
        self.checks.append((self.number, what, value, ok, max(res) if res else 0.0))
        return ok

    def save(self, pdf, png=None, dpi=110):
        self.fig.savefig(pdf)
        if png:
            self.fig.savefig(png, dpi=dpi)
        plt.close(self.fig)


class View:
    """Normalansicht oder Schnitt eines (oder mehrerer) Koerper.
    shapes: Liste (shape, hatch) mit hatch = (Winkel, Abstand) oder None. section: Modellpunkt der Schnittebene
    (Ebene senkrecht zur Blickrichtung), geschnitten wird alles zwischen Betrachter und Ebene entfernt."""

    def __init__(self, sheet, shapes, kind, scale, section=None, hidden=False, label=None, clip_model=None,
                 hatch=(45, 1.0), skip_hidden_small=0.0):
        self.sh = sheet
        self.ax = sheet.ax
        r, u = VIEWS[kind]
        self.r, self.u = V(*r), V(*u)
        self.n = self.r.cross(self.u)
        self.s = scale
        self.kind = kind
        self.label = label
        if not isinstance(shapes, (list, tuple)):
            shapes = [(shapes, hatch)]
        self.src = shapes
        m = App.Matrix(self.r.x, self.r.y, self.r.z, 0, self.u.x, self.u.y, self.u.z, 0,
                       self.n.x, self.n.y, self.n.z, 0, 0, 0, 0, 1)
        self.faces = []                      # (Liste Wire-Polylinien, hatch)
        self.face_idx = []                   # (Index Koerper, Part.Face in Bildkoordinaten)
        solids = []
        solids_idx = []
        for shp, hat in shapes:
            solids_idx.append(1)
            t = shp.copy()
            t.transformShape(m)
            if section is not None:
                c = V(*section).dot(self.n)
                half = Part.makeBox(6000, 6000, 3000, V(-3000, -3000, c - 3000))
                t = t.common(half)
                for f0 in t.Faces:
                    bb = f0.BoundBox
                    if bb.ZLength < 1e-6 and abs(bb.ZMax - c) < 1e-5:
                      fl = [f0]
                      if clip_model:
                          cu0, cu1, cv0, cv1 = clip_model
                          fl = f0.common(Part.makeBox(cu1 - cu0, cv1 - cv0, 1.0, V(cu0, cv0, c - 0.5))).Faces
                      for f in fl:
                        wires = [[(p.x, p.y) for p in w.discretize(Deflection=0.004)] for w in
                                 [f.OuterWire] + [w for w in f.Wires if not w.isSame(f.OuterWire)]]
                        self.faces.append((wires, hat))
                        self.face_idx.append((len(solids_idx) - 1, f))
            if t.Solids or t.Faces:
                solids.append(t)
        comp = Part.makeCompound(solids)
        res = TechDraw.projectEx(comp, V(0, 0, 1))
        self.vis = [_pts(e) for k in (0, 3) if res[k] and not res[k].isNull() for e in res[k].Edges]
        self.hid = []
        if hidden:
            self.hid = [_pts(e) for k in (5, 8) if res[k] and not res[k].isNull() for e in res[k].Edges]
            if skip_hidden_small:
                self.hid = [p for p in self.hid if math.dist(p[0], p[-1]) > skip_hidden_small or len(p) > 2]
        allp = [q for pl in self.vis for q in pl] or [(0, 0)]
        self.u0, self.u1 = min(p[0] for p in allp), max(p[0] for p in allp)
        self.v0, self.v1 = min(p[1] for p in allp), max(p[1] for p in allp)
        self.clip_model = clip_model         # (u0, u1, v0, v1) in Bildkoordinaten (mm Modell) -> Einzelheit
        if clip_model:
            self.u0, self.u1, self.v0, self.v1 = clip_model
        self.ox = self.oy = 0.0

    # ------------------------------------------------------------------ Lage auf dem Blatt
    def place(self, x, y, anchor='c'):
        """Bild so legen, dass der Huellquader-Punkt anchor ('c', 'll', 'lc', 'uc', 'cl', 'cr') bei (x, y) liegt."""
        s = self.s
        w, h = (self.u1 - self.u0) * s, (self.v1 - self.v0) * s
        ax_, ay_ = {'c': (0.5, 0.5), 'll': (0, 0), 'lc': (0.5, 0), 'uc': (0.5, 1), 'cl': (0, 0.5), 'cr': (1, 0.5),
                    'ul': (0, 1)}[anchor]
        self.ox = x - ax_ * w - self.u0 * s
        self.oy = y - ay_ * h - self.v0 * s
        return self

    def S(self, p):
        p = V(*p)
        return (self.ox + self.s * p.dot(self.r), self.oy + self.s * p.dot(self.u))

    def UV(self, uv):
        return (self.ox + self.s * uv[0], self.oy + self.s * uv[1])

    @property
    def box(self):
        return (self.ox + self.s * self.u0, self.ox + self.s * self.u1, self.oy + self.s * self.v0, self.oy + self.s * self.v1)

    def top(self, k=1, gap=7.0):
        return self.box[3] + k * gap

    def bottom(self, k=1, gap=7.0):
        return self.box[2] - k * gap

    def left(self, k=1, gap=7.0):
        return self.box[0] - k * gap

    def right(self, k=1, gap=7.0):
        return self.box[1] + k * gap

    # ------------------------------------------------------------------ Zeichnen
    def draw(self, title=None, title_dy=6.0):
        clip = None
        if self.clip_model:
            x0, x1, y0, y1 = self.box
            clip = Rectangle((x0, y0), x1 - x0, y1 - y0, transform=self.ax.transData)
            self.ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=LW_TN, ls=(0, (4, 1.5)), zorder=2))
        for wires, hat in self.faces:
            if hat is None:
                continue
            verts, codes = [], []
            for i, w in enumerate(wires):
                pts = [self.UV(p) for p in w]
                a = sum(pts[k][0] * pts[(k + 1) % len(pts)][1] - pts[(k + 1) % len(pts)][0] * pts[k][1] for k in range(len(pts)))
                if (i == 0 and a < 0) or (i > 0 and a > 0):
                    pts = pts[::-1]
                verts += pts + [pts[0]]
                codes += [Path.MOVETO] + [Path.LINETO] * (len(pts) - 1) + [Path.CLOSEPOLY]
            path = Path(verts, codes)
            patch = PathPatch(path, fill=False, lw=0, transform=self.ax.transData)
            self.ax.add_patch(patch)
            ang, d = hat
            bb = path.get_extents()
            cx, cy = (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2
            R = math.hypot(bb.width, bb.height) / 2 + 1
            ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            segs = []
            k = -R
            while k <= R:
                px_, py_ = cx - sa * k, cy + ca * k
                segs.append([(px_ - ca * R, py_ - sa * R), (px_ + ca * R, py_ + sa * R)])
                k += d
            lc = LineCollection(segs, colors='k', linewidths=LW_TN * 0.9, zorder=2)
            lc.set_clip_path(patch)
            self.ax.add_collection(lc)
        segs = [[self.UV(p) for p in pl] for pl in self.vis]
        lc = LineCollection(segs, colors='k', linewidths=LW_TH, zorder=4, capstyle='round', joinstyle='round')
        self.ax.add_collection(lc)
        if clip is not None:
            lc.set_clip_path(clip)
        if self.hid:
            segs = [[self.UV(p) for p in pl] for pl in self.hid]
            lc = LineCollection(segs, colors='k', linewidths=LW_TN, linestyles=(0, (2.2, 1.1)), zorder=3)
            self.ax.add_collection(lc)
            if clip is not None:
                lc.set_clip_path(clip)
        if title:
            x0, x1, y0, y1 = self.box
            self.sh.text((x0 + x1) / 2, y1 + title_dy, title, h=3.5, ha='center')
        return self

    def inner_point(self, k):
        """Blattpunkt sicher in der Schnittflaeche von Koerper k (Schwerpunkt des groessten Dreiecks)."""
        best = None
        for i, f in self.face_idx:
            if i != k:
                continue
            pts, tris = f.tessellate(0.05)
            for t in tris:
                a, b, c = pts[t[0]], pts[t[1]], pts[t[2]]
                ar = abs((b.x - a.x) * (c.y - a.y) - (c.x - a.x) * (b.y - a.y)) / 2
                if best is None or ar > best[0]:
                    best = (ar, ((a.x + b.x + c.x) / 3, (a.y + b.y + c.y) / 3))
        return self.UV(best[1]) if best else None

    def balloon(self, k, num, pos, p=None):
        """Positionsnummer (Kreis 7 mm) bei pos (Blatt), Hinweislinie mit Punkt auf Koerper k bzw. Blattpunkt p."""
        a = p or self.inner_point(k)
        if a is None:
            return False
        L = math.dist(a, pos) or 1
        e = (pos[0] + (a[0] - pos[0]) / L * 3.5, pos[1] + (a[1] - pos[1]) / L * 3.5)
        self.sh.line([a, e], lw=LW_TN, z=7)
        self.ax.add_patch(Circle(a, 0.45, color='k', zorder=7))
        self.ax.add_patch(Circle(pos, 3.5, fc='white', ec='k', lw=LW_TN, zorder=7))
        self.sh.text(pos[0], pos[1], str(num), h=3.0, ha='center', va='center', z=8)
        return True

    # ------------------------------------------------------------------ Hilfslinien
    def centerline(self, p1, p2, ext=2.0):
        a, b = self.S(p1), self.S(p2)
        L = math.dist(a, b) or 1
        d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        a = (a[0] - d[0] * ext, a[1] - d[1] * ext)
        b = (b[0] + d[0] * ext, b[1] + d[1] * ext)
        self.sh.line([a, b], lw=LW_TN, ls=(0, (8, 1.5, 1, 1.5)), z=3)

    def cross(self, c, r):
        """Mittellinienkreuz fuer einen Kreis (Radius r im Modell) in dieser Ansicht."""
        c3 = V(*c)
        self.centerline(c3 - self.r * r, c3 + self.r * r)
        self.centerline(c3 - self.u * r, c3 + self.u * r)

    def thick_chain(self, p1, p2, off=0.0):
        """breite Strichpunktlinie (Kennzeichnung behandelter/funktionswichtiger Flaechen, ISO 128-20 Typ 10.2)."""
        a, b = self.S(p1), self.S(p2)
        L = math.dist(a, b) or 1
        nx, ny = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
        a = (a[0] + nx * off, a[1] + ny * off)
        b = (b[0] + nx * off, b[1] + ny * off)
        self.sh.line([a, b], lw=0.7 * MM2PT, ls=(0, (6, 1.2, 1, 1.2)), z=5)

    def cutline(self, p1, p2, letter, look, ext=4.0):
        """Schnittverlauf in dieser Ansicht: p1, p2 Modellpunkte; look = Blickrichtung des Schnitts (Modellvektor)."""
        a, b = self.S(p1), self.S(p2)
        L = math.dist(a, b) or 1
        d = ((b[0] - a[0]) / L, (b[1] - a[1]) / L)
        a2 = (a[0] - d[0] * ext, a[1] - d[1] * ext)
        b2 = (b[0] + d[0] * ext, b[1] + d[1] * ext)
        self.sh.line([a2, b2], lw=LW_TN, ls=(0, (8, 1.5, 1, 1.5)), z=5)
        lk = V(*look)
        ld = (lk.dot(self.r), lk.dot(self.u))
        ll = math.hypot(*ld) or 1
        ld = (ld[0] / ll, ld[1] / ll)
        for e, sgn in ((a2, -1), (b2, 1)):
            e0 = (e[0] - sgn * d[0] * 5, e[1] - sgn * d[1] * 5)
            self.sh.line([e0, e], lw=0.7 * MM2PT, z=6)
            tip = (e0[0] + ld[0] * 5, e0[1] + ld[1] * 5)
            self.sh.line([e0, tip], lw=LW_TN, z=6)
            _arrow(self.ax, tip, ld)
            self.sh.text(tip[0] + ld[0] * 1.5 + sgn * d[0] * 1.5, tip[1] + ld[1] * 1.5 + sgn * d[1] * 1.5 - 1.6, letter,
                         h=3.5, ha='center')

    # ------------------------------------------------------------------ Bemassung
    def dim(self, p1, p2, axis, at, what, shape, pre='', suf='', nd=2, chk=None, frame=False, text=None, tside=0,
            ext=True):
        """Laengenmass. axis 'h' (Bild waagrecht) / 'v' (senkrecht). at = Blattkoordinate der Masslinie.
        Masszahl = Abstand der Modellpunkte p1, p2 in Bildrichtung. chk: Punkte, die auf 'shape' liegen muessen
        (Standard p1, p2)."""
        P1, P2 = V(*p1), V(*p2)
        val = abs((P2 - P1).dot(self.r if axis == 'h' else self.u))
        t = text if text is not None else pre + fmt(val, nd) + suf
        a, b = self.S(p1), self.S(p2)
        _linear(self.sh, a, b, axis, at, t, frame=frame, tside=tside, ext=ext)
        ok = self.sh.check('%s = %s' % (what, t), val, chk if chk is not None else [p1, p2], shape)
        return val, ok

    def radial(self, c, r, ang, what, shape, pre='R', length=8.0, shoulder=4.0, dirv=None, frame=False, nd=2,
               inside=False, chk=True):
        """Radius/Durchmesser (Kreis sichtbar in dieser Ansicht): Hinweislinie unter ang (Grad, Blatt) auf den Kreis."""
        c3 = V(*c)
        ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        tip3 = c3 + self.r * (r * ca) + self.u * (r * sa)
        tip = self.S(tip3)
        sgn = -1 if inside else 1
        knee = (tip[0] + sgn * ca * length, tip[1] + sgn * sa * length)
        hd = 1 if knee[0] >= tip[0] else -1
        end = (knee[0] + hd * shoulder, knee[1])
        self.sh.line([tip, knee, end], lw=LW_TN, z=6)
        _arrow(self.ax, tip, (-sgn * ca, -sgn * sa))
        val = 2 * r if pre.startswith('Ø') or pre.endswith('Ø') else r
        t = pre + fmt(val, nd)
        tx = self.sh.text(end[0] if hd > 0 else end[0], end[1] + 0.8, t, ha='right' if hd > 0 else 'left', h=TXT)
        if hd > 0:
            tx.set_ha('right')
        if frame:
            _frame_text(self.sh, tx)
        pts = [(tip3.x, tip3.y, tip3.z)] if chk else []
        self.sh.check('%s = %s' % (what, t), val, pts, shape)

    def note(self, p, txt, dx, dy, shape=None, what=None, dot=False, h=2.2):
        a = self.S(p)
        b = (a[0] + dx, a[1] + dy)
        hd = 1 if dx >= 0 else -1
        c = (b[0] + hd * 2.0, b[1])
        self.sh.line([a, b, c], lw=LW_TN, z=6)
        if dot:
            self.ax.add_patch(Circle(a, 0.5, color='k', zorder=6))
        else:
            L = math.dist(a, b) or 1
            _arrow(self.ax, a, ((a[0] - b[0]) / L, (a[1] - b[1]) / L))
        lines = txt.split('\n')
        for i, l in enumerate(lines):
            self.sh.text(c[0] + hd * 0.6, c[1] - 0.8 - i * (h + 1.2) + (len(lines) - 1) * 0 + 0.0, l,
                         ha='left' if hd > 0 else 'right', va='center', h=h)
        if shape is not None and what:
            self.sh.check(what, 0.0, [p], shape)


def _arrow(ax, tip, d, L=2.2, w=0.42):
    """gefuellter Pfeil, Spitze bei tip, zeigt in Richtung d (Einheitsvektor)."""
    dx, dy = d
    n = math.hypot(dx, dy) or 1
    dx, dy = dx / n, dy / n
    bx, by = tip[0] - dx * L, tip[1] - dy * L
    ax.add_patch(Polygon([tip, (bx - dy * w, by + dx * w), (bx + dy * w, by - dx * w)], closed=True, color='k',
                         lw=0, zorder=7))


def _frame_text(sh, tx):
    """Pruefmass: Masszahl im Rahmen mit runden Enden (ISO 129-1)."""
    tx.set_bbox(dict(boxstyle='round,pad=0.25,rounding_size=0.9', fc='white', ec='k', lw=LW_TN))


def _linear(sh, a, b, axis, at, t, frame=False, tside=0, ext=True):
    ax = sh.ax
    gap, over = 0.8, 1.5
    tw = len(t) * TXT * 0.62 + 1.0
    if axis == 'h':
        xa, xb = sorted([a[0], b[0]])
        pa, pb = (a, b) if a[0] <= b[0] else (b, a)
        if ext:
            for p in (pa, pb):
                sgn = 1 if at > p[1] else -1
                if abs(at - p[1]) > gap:
                    sh.line([(p[0], p[1] + sgn * gap), (p[0], at + sgn * over)], z=5)
        span = xb - xa
        if span >= 7.0:
            sh.line([(xa, at), (xb, at)], z=5)
            _arrow(ax, (xa, at), (-1, 0))
            _arrow(ax, (xb, at), (1, 0))
        else:
            sh.line([(xa - 5, at), (xb + 5, at)], z=5)
            _arrow(ax, (xa, at), (1, 0))
            _arrow(ax, (xb, at), (-1, 0))
        if span >= tw + 4.5 and tside == 0:
            tx = sh.text((xa + xb) / 2, at + 0.7, t, ha='center')
        elif tside < 0:
            tx = sh.text(xa - 5.5, at + 0.7, t, ha='right')
        else:
            tx = sh.text(xb + 5.5, at + 0.7, t, ha='left')
    else:
        ya, yb = sorted([a[1], b[1]])
        pa, pb = (a, b) if a[1] <= b[1] else (b, a)
        if ext:
            for p in (pa, pb):
                sgn = 1 if at > p[0] else -1
                if abs(at - p[0]) > gap:
                    sh.line([(p[0] + sgn * gap, p[1]), (at + sgn * over, p[1])], z=5)
        span = yb - ya
        if span >= 7.0:
            sh.line([(at, ya), (at, yb)], z=5)
            _arrow(ax, (at, ya), (0, -1))
            _arrow(ax, (at, yb), (0, 1))
        else:
            sh.line([(at, ya - 5), (at, yb + 5)], z=5)
            _arrow(ax, (at, ya), (0, 1))
            _arrow(ax, (at, yb), (0, -1))
        if span >= tw + 4.5 and tside == 0:
            tx = sh.text(at - 0.7, (ya + yb) / 2, t, ha='center', va='bottom', rot=90)
        elif tside < 0:
            tx = sh.text(at - 0.7, ya - 5.5, t, ha='right', va='bottom', rot=90)
        else:
            tx = sh.text(at - 0.7, yb + 5.5, t, ha='left', va='bottom', rot=90)
    if frame:
        _frame_text(sh, tx)
    return tx
