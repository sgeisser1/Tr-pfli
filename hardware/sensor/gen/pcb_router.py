"""fluidi - einfacher Raster-Router (A*) fuer das Elektronikband des Sensor-PCB.

Kein Ersatz fuer einen Autorouter, aber reproduzierbar und skriptbar:
- Raster 0.05 mm, Lagen in Reihenfolge `layers` (z. B. F.Cu, In2.Cu, B.Cu), Durchkontaktierungen
  verbinden alle Routing-Lagen (Through-Vias).
- Hindernisse: Rasterbild je Lage mit Netz-ID (0 frei, -1 hart, >0 Netz). Fuer ein Netz mit halber Breite hw
  ist eine Zelle frei, wenn der Abstand zum naechsten fremden Kupfer > hw + clr (Distanztransformation).
- Mehrpunkt-Netze: Baum wachsen lassen (naechster Pad an den bestehenden Baum).
- Ergebnis: Segmente (Lage, x1, y1, x2, y2, Breite) und Vias (x, y).

Diskretisierungsfehler <= halbe Zellendiagonale (0.035 mm); die Projektregel (0.15 mm) liegt daher sicher ueber der
DRC-Grenze 0.10 mm (JLC 0.09 mm).
"""
import heapq
import math

import numpy as np
from matplotlib.path import Path
from scipy import ndimage

HARD = -1
HIST_INC = float(__import__("os").environ.get("FLUIDI_HIST", "0.2"))


class Router:
    def __init__(self, x0, y0, x1, y1, res, layers, clr):
        self.x0, self.y0, self.res = x0, y0, res
        self.nx = int(round((x1 - x0) / res)) + 1
        self.ny = int(round((y1 - y0) / res)) + 1
        self.layers = list(layers)
        self.nl = len(layers)
        self.clr = clr
        self.own = np.zeros((self.nl, self.ny, self.nx), np.int32)
        self.via_ok = np.zeros((self.ny, self.nx), bool)      # Bereich, in dem Vias erlaubt sind
        self.no_via = np.zeros((self.ny, self.nx), bool)      # Pads usw. (keine Vias in Pads)
        self.holes = []                                       # (x, y, r_hole) fuer Bohrabstand
        self.xs = x0 + np.arange(self.nx) * res
        self.ys = y0 + np.arange(self.ny) * res
        self.segments = []   # (layer_name, x1, y1, x2, y2, width, net)
        self.vias = []       # (x, y, net)

    # ---------- Koordinaten
    def ij(self, x, y):
        return int(round((y - self.y0) / self.res)), int(round((x - self.x0) / self.res))

    def xy(self, j, i):
        return self.x0 + i * self.res, self.y0 + j * self.res

    def li(self, layer):
        return self.layers.index(layer)

    # ---------- Malen
    def _window(self, xmin, ymin, xmax, ymax):
        j0 = max(0, int(math.floor((ymin - self.y0) / self.res)) - 1)
        j1 = min(self.ny, int(math.ceil((ymax - self.y0) / self.res)) + 2)
        i0 = max(0, int(math.floor((xmin - self.x0) / self.res)) - 1)
        i1 = min(self.nx, int(math.ceil((xmax - self.x0) / self.res)) + 2)
        return j0, j1, i0, i1

    def poly_mask(self, pts):
        pts = np.asarray(pts, float)
        j0, j1, i0, i1 = self._window(pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max())
        if j1 <= j0 or i1 <= i0:
            return None
        X, Y = np.meshgrid(self.xs[i0:i1], self.ys[j0:j1])
        inside = Path(pts).contains_points(np.c_[X.ravel(), Y.ravel()], radius=1e-9).reshape(X.shape)
        return (j0, j1, i0, i1), inside

    def paint_poly(self, layer_idx, pts, net):
        r = self.poly_mask(pts)
        if r is None:
            return None
        (j0, j1, i0, i1), m = r
        self.own[layer_idx, j0:j1, i0:i1][m] = net
        return r

    def paint_rect(self, layer_idx, xa, ya, xb, yb, net):
        self.paint_poly(layer_idx, [(xa, ya), (xb, ya), (xb, yb), (xa, yb)], net)

    def seg_mask(self, x1, y1, x2, y2, hw):
        j0, j1, i0, i1 = self._window(min(x1, x2) - hw, min(y1, y2) - hw, max(x1, x2) + hw, max(y1, y2) + hw)
        X, Y = np.meshgrid(self.xs[i0:i1], self.ys[j0:j1])
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        if L2 == 0:
            d = np.hypot(X - x1, Y - y1)
        else:
            t = np.clip(((X - x1) * dx + (Y - y1) * dy) / L2, 0, 1)
            d = np.hypot(X - (x1 + t * dx), Y - (y1 + t * dy))
        return (j0, j1, i0, i1), d <= hw + 1e-9

    def paint_seg(self, layer_idx, x1, y1, x2, y2, hw, net):
        (j0, j1, i0, i1), m = self.seg_mask(x1, y1, x2, y2, hw)
        self.own[layer_idx, j0:j1, i0:i1][m] = net

    def paint_via(self, x, y, r, net, hole_r=0.15):
        for L in range(self.nl):
            self.paint_seg(L, x, y, x, y, r, net)
        self.holes.append((x, y, hole_r, net))

    def add_track(self, layer, pts, width, net, paint=True):
        L = self.li(layer) if isinstance(layer, str) else layer
        for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
            self.segments.append((self.layers[L], xa, ya, xb, yb, width, net))
            if paint:
                self.paint_seg(L, xa, ya, xb, yb, width / 2, net)

    def add_via(self, x, y, net, r=0.225):
        self.vias.append((x, y, net))
        self.paint_via(x, y, r, net)

    # ---------- Freiraum
    def set_base(self):
        """Aktuellen Stand (Pads, feste Strukturen, Fanouts) als nicht aufreissbar festhalten."""
        self.base = self.own.copy()
        self.base_holes = len(self.holes)
        self.base_segs = len(self.segments)
        self.base_vias = len(self.vias)

    def rip(self, net):
        """Geroutetes Kupfer eines Netzes entfernen (nur oberhalb der Basis)."""
        m = (self.own == net)
        self.own[m] = self.base[m]
        self.segments = self.segments[:self.base_segs] + [s for s in self.segments[self.base_segs:] if s[6] != net]
        self.vias = self.vias[:self.base_vias] + [v for v in self.vias[self.base_vias:] if v[2] != net]
        self.holes = self.holes[:self.base_holes] + [h for h in self.holes[self.base_holes:] if h[3] != net]

    def free_masks(self, net, hw, extra_clr=0.0, base_only=False):
        """bool[L, ny, nx]: Mittellinie einer Bahn (halbe Breite hw) darf hier liegen."""
        out = np.zeros_like(self.own, bool)
        src = self.base if base_only else self.own
        for L in range(self.nl):
            foreign = (src[L] != 0) & (src[L] != net)
            d = ndimage.distance_transform_edt(~foreign) * self.res
            out[L] = d > hw + self.clr + extra_clr
        return out

    def via_mask(self, net, via_r, hole_clr=0.25, base_only=False):
        m = self.via_ok & ~self.no_via
        src = self.base if base_only else self.own
        holes = self.holes[:self.base_holes] if base_only else self.holes
        for L in range(self.nl):
            foreign = (src[L] != 0) & (src[L] != net)
            d = ndimage.distance_transform_edt(~foreign) * self.res
            m &= d > via_r + self.clr + 0.04   # Reserve: Bohrung-Kupfer >= 0.20 (JLC) trotz Raster
        # Bohrabstand (alle Netze)
        if holes:
            hm = np.zeros((self.ny, self.nx), bool)
            for (x, y, r, _n) in holes:
                j, i = self.ij(x, y)
                if 0 <= j < self.ny and 0 <= i < self.nx:
                    hm[j, i] = True
            d = ndimage.distance_transform_edt(~hm) * self.res
            m &= d > 0.15 + 0.15 + hole_clr
        return m

    # ---------- A*
    def astar(self, net, hw, src, goal, via_r=0.225, via_cost=0.9, layer_cost=None, window=None,
              goal_is_via=False, max_len=None, free=None, vfree=None, pen=None, vpen=None, pen_cost=3.0, hist=None):
        """src: bool[L,ny,nx] Startzellen; goal: bool[L,ny,nx] Zielzellen (oder None bei goal_is_via).
        Liefert Liste [(L, j, i), ...] oder None."""
        nl, ny, nx = self.nl, self.ny, self.nx
        if free is None:
            free = self.free_masks(net, hw)
        if vfree is None:
            vfree = self.via_mask(net, via_r)
        if layer_cost is None:
            layer_cost = [1.0] * nl
        res = self.res
        if window is None:
            j0, j1, i0, i1 = 0, ny, 0, nx
        else:
            j0, j1, i0, i1 = window
        free_w = free[:, j0:j1, i0:i1]
        vfree_w = vfree[j0:j1, i0:i1]
        pen_w = pen[:, j0:j1, i0:i1] if pen is not None else None
        if hist is None:
            hist = getattr(self, "hist", None)
        hist_w = hist[:, j0:j1, i0:i1] if hist is not None else None
        vpen_w = vpen[j0:j1, i0:i1] if vpen is not None else None
        src_w = src[:, j0:j1, i0:i1] & free_w | src[:, j0:j1, i0:i1]
        wy, wx = j1 - j0, i1 - i0
        N = nl * wy * wx
        g = np.full(N, np.inf, np.float32)
        came = np.full(N, -1, np.int64)
        closed = np.zeros(N, bool)
        if goal is not None:
            goal_w = goal[:, j0:j1, i0:i1]
            gl, gj, gi = np.nonzero(goal_w)
            if len(gj) == 0:
                return None
            gcx, gcy = gi.mean(), gj.mean()
            grad = max(np.hypot(gi - gcx, gj - gcy).max(), 0)

            def h(j, i):
                return max(0.0, math.hypot(i - gcx, j - gcy) - grad) * res
        else:
            goal_w = None

            def h(j, i):
                return 0.0
        heap = []
        sl, sj, si = np.nonzero(src[:, j0:j1, i0:i1])
        for L, j, i in zip(sl, sj, si):
            k = (L * wy + j) * wx + i
            g[k] = 0.0
            heapq.heappush(heap, (h(j, i), 0.0, k))
        if not heap:
            return None
        dirs = [(0, 1, 1.0), (0, -1, 1.0), (1, 0, 1.0), (-1, 0, 1.0),
                (1, 1, 1.41421356), (1, -1, 1.41421356), (-1, 1, 1.41421356), (-1, -1, 1.41421356)]
        found = -1
        while heap:
            f, gk, k = heapq.heappop(heap)
            if closed[k]:
                continue
            closed[k] = True
            L, rem = divmod(k, wy * wx)
            j, i = divmod(rem, wx)
            if goal_w is not None:
                if goal_w[L, j, i] and gk > 0:
                    found = k
                    break
            else:
                if L == 0 and vfree_w[j, i] and gk > 0:
                    found = k
                    break
            if max_len is not None and gk > max_len:
                continue
            lc = layer_cost[L]
            for dj, di, c in dirs:
                jj, ii = j + dj, i + di
                if jj < 0 or jj >= wy or ii < 0 or ii >= wx:
                    continue
                if not free_w[L, jj, ii]:
                    continue
                if dj and di and not (free_w[L, j + dj, i] or free_w[L, j, i + di]):
                    continue
                kk = (L * wy + jj) * wx + ii
                ng = gk + c * res * lc
                if pen_w is not None and pen_w[L, jj, ii]:
                    ng += pen_cost
                if hist_w is not None:
                    ng += hist_w[L, jj, ii]
                if ng < g[kk]:
                    g[kk] = ng
                    came[kk] = k
                    heapq.heappush(heap, (ng + h(jj, ii), ng, kk))
            if vfree_w[j, i] and not goal_is_via:
                for L2 in range(nl):
                    if L2 == L or not free_w[L2, j, i]:
                        continue
                    kk = (L2 * wy + j) * wx + i
                    ng = gk + via_cost + (pen_cost * 4 if (vpen_w is not None and vpen_w[j, i]) else 0.0)
                    if ng < g[kk]:
                        g[kk] = ng
                        came[kk] = k
                        heapq.heappush(heap, (ng + h(j, i), ng, kk))
        if found < 0:
            return None
        path = []
        k = found
        while k >= 0:
            L, rem = divmod(k, wy * wx)
            j, i = divmod(rem, wx)
            path.append((int(L), int(j + j0), int(i + i0)))
            if g[k] == 0:
                break
            k = came[k]
        path.reverse()
        return path

    def fanout_path(self, net, hw, src, window, free, vfree, score, max_len=1.6, wlen=0.6):
        """Dijkstra auf Lage 0 ab src; waehlt das Via mit bestem Wert score[j,i] - wlen*Weglaenge
        (score = Abstand zu fremden Pads: Vias sollen Nachbarn nicht einschliessen)."""
        j0, j1, i0, i1 = window
        wy, wx = j1 - j0, i1 - i0
        g = np.full((wy, wx), np.inf)
        came = np.full((wy, wx, 2), -1, np.int32)
        heap = []
        sj, si = np.nonzero(src[0, j0:j1, i0:i1])
        for j, i in zip(sj, si):
            g[j, i] = 0.0
            heapq.heappush(heap, (0.0, j, i))
        best, bval = None, -1e9
        dirs = [(0, 1, 1.0), (0, -1, 1.0), (1, 0, 1.0), (-1, 0, 1.0),
                (1, 1, 1.41421356), (1, -1, 1.41421356), (-1, 1, 1.41421356), (-1, -1, 1.41421356)]
        while heap:
            d, j, i = heapq.heappop(heap)
            if d > g[j, i]:
                continue
            if vfree[j + j0, i + i0] and d > 0:
                v = score[j + j0, i + i0] - wlen * d
                if v > bval:
                    best, bval = (j, i), v
            if d > max_len:
                continue
            for dj, di, c in dirs:
                jj, ii = j + dj, i + di
                if 0 <= jj < wy and 0 <= ii < wx and free[0, jj + j0, ii + i0]:
                    nd = d + c * self.res
                    if nd < g[jj, ii]:
                        g[jj, ii] = nd
                        came[jj, ii] = (j, i)
                        heapq.heappush(heap, (nd, jj, ii))
        if best is None:
            return None
        path = []
        j, i = best
        while j >= 0:
            path.append((0, j + j0, i + i0))
            if g[j, i] == 0:
                break
            j, i = came[j, i]
        path.reverse()
        return path

    # ---------- Pfad -> Segmente
    def commit_path(self, path, net, width, end_via=False):
        hw = width / 2
        # zwei Lagenwechsel naeher als 0.6 mm (Bohrabstand): Zwischenstueck auf der Ausgangslage fuehren
        changed = True
        while changed:
            changed = False
            idx = [k for k in range(1, len(path)) if path[k][0] != path[k - 1][0]]
            for a, b in zip(idx[:-1], idx[1:]):
                ja, ia = path[a][1], path[a][2]
                jb, ib = path[b][1], path[b][2]
                if math.hypot(ja - jb, ia - ib) * self.res < 0.6 and path[a - 1][0] == path[b][0]:
                    L = path[a - 1][0]
                    n = max(abs(jb - ja), abs(ib - ia))
                    mid = [(L, ja + round((jb - ja) * t / max(n, 1)), ia + round((ib - ia) * t / max(n, 1)))
                           for t in range(n + 1)]
                    path = path[:a] + mid + path[b + 1:]
                    changed = True
                    break
        runs = []
        cur = [path[0]]
        for p in path[1:]:
            if p[0] != cur[-1][0]:
                runs.append(cur)
                j, i = p[1], p[2]
                x, y = self.xy(j, i)
                self.add_via(x, y, net)
                cur = [p]
            else:
                cur.append(p)
        runs.append(cur)
        for run in runs:
            L = run[0][0]
            pts = [self.xy(j, i) for (_, j, i) in run]
            pts = simplify(pts)
            if len(pts) >= 2:
                self.add_track(L, pts, width, net)
        if end_via:
            _, j, i = path[-1]
            x, y = self.xy(j, i)
            self.add_via(x, y, net)

    def victims(self, path, net, hw, pen, vpen):
        """Netze (oberhalb der Basis), deren Kupfer die Pfadzellen tatsaechlich verletzt (nur Strafzellen)."""
        out = set()
        rt_ = int(math.ceil((hw + self.clr) / self.res))
        rv = int(math.ceil((0.225 + self.clr + 0.04) / self.res))
        prev = None
        for (L, j, i) in path:
            via = prev is not None and prev[0] != L
            prev = (L, j, i)
            checks = []
            if pen[L, j, i]:
                checks.append(([L], rt_, hw + self.clr))
            if via and vpen[j, i]:
                checks.append((range(self.nl), rv, 0.225 + self.clr + 0.04))
            for layers, r, dist in checks:
                for LL in layers:
                    j0, i0 = max(0, j - r), max(0, i - r)
                    w = self.own[LL, j0:j + r + 1, i0:i + r + 1]
                    b = self.base[LL, j0:j + r + 1, i0:i + r + 1]
                    jj, ii = np.mgrid[j0:j0 + w.shape[0], i0:i0 + w.shape[1]]
                    near = np.hypot(jj - j, ii - i) * self.res <= dist
                    ids = np.unique(w[near & (w != b) & (w > 0) & (w != net)])
                    out.update(int(v) for v in ids)
        # Bohrabstand: fremde Router-Vias in der Naehe eines neuen Vias
        return out

    def route_net(self, net, hw, pad_cells, layer_cost=None, margin=3.0, via_cost=0.9, verbose=False, rr=False,
                  protect=()):
        """pad_cells: Liste von bool[L,ny,nx]-Masken je Pad. Baum wachsen lassen.
        rr=True: bei Fehlschlag Weg mit Strafkosten durch fremde (aufreissbare) Bahnen suchen, diese Netze
        entfernen und zurueckgeben. Liefert (Anzahl Fehlschlaege, Menge aufgerissener Netze)."""
        ripped = set()
        if len(pad_cells) < 2:
            return 0, ripped
        free = self.free_masks(net, hw)
        vfree = self.via_mask(net, 0.225)
        tree = pad_cells[0].copy()
        todo = list(range(1, len(pad_cells)))
        fails = 0
        while todo:
            tl, tj, ti = np.nonzero(tree)
            best, bd = None, 1e9
            for n in todo:
                pl, pj, pi = np.nonzero(pad_cells[n])
                d = np.min(np.hypot(tj - pj.mean(), ti - pi.mean()))
                if d < bd:
                    best, bd = n, d
            todo.remove(best)
            goal = pad_cells[best]
            if (goal & tree).any():
                tree |= goal
                continue
            gl, gj, gi = np.nonzero(goal)
            path = None

            def window(m):
                mc = int(m / self.res)
                dd = np.hypot(tj - gj.mean(), ti - gi.mean())
                near = dd <= dd.min() + mc
                jj = np.r_[tj[near], gj]
                ii = np.r_[ti[near], gi]
                win = (max(0, jj.min() - mc), min(self.ny, jj.max() + mc + 1),
                       max(0, ii.min() - mc), min(self.nx, ii.max() + mc + 1))
                src = np.zeros_like(tree)
                src[tl[near], tj[near], ti[near]] = True
                return win, src
            for m in (margin, margin * 2.5):
                win, src = window(m)
                path = self.astar(net, hw, src, goal, layer_cost=layer_cost, window=win, free=free, vfree=vfree,
                                  via_cost=via_cost)
                if path is not None:
                    break
            if path is None and rr:
                hfree = self.free_masks(net, hw, base_only=True)
                hvfree = self.via_mask(net, 0.225, base_only=True)
                pen = hfree & ~free
                vpen = hvfree & ~vfree
                # geschuetzte Netze wie Basis behandeln
                for pn in protect:
                    pm = self.own == pn
                    if pm.any():
                        from scipy import ndimage as _nd
                        for L in range(self.nl):
                            d = _nd.distance_transform_edt(~pm[L]) * self.res
                            hfree[L] &= d > hw + self.clr
                pen &= hfree
                spath = None
                for mm_ in (margin * 2.5, margin * 6):
                    win, src = window(mm_)
                    spath = self.astar(net, hw, src, goal, layer_cost=layer_cost, window=win, free=hfree,
                                       vfree=hvfree, via_cost=via_cost, pen=pen, vpen=vpen)
                    if spath is not None:
                        break
                if spath is not None:
                    # Verlauf (PathFinder): umkaempfte Zellen werden teurer -> Zyklen brechen
                    if getattr(self, "hist", None) is None:
                        self.hist = np.zeros(self.own.shape, np.float32)
                    for (L, j, i) in spath:
                        if pen[L, j, i]:
                            self.hist[L, max(0, j - 3):j + 4, max(0, i - 3):i + 4] += HIST_INC
                    vic = self.victims(spath, net, hw, pen, vpen) - set(protect)
                    for v in vic:
                        self.rip(v)
                    ripped |= vic
                    free = self.free_masks(net, hw)
                    vfree = self.via_mask(net, 0.225)
                    path = self.astar(net, hw, src, goal, layer_cost=layer_cost, window=win, free=free, vfree=vfree,
                                      via_cost=via_cost)
            if path is None:
                fails += 1
                if verbose or rr:
                    x, y = self.xy(int(gj.mean()), int(gi.mean()))
                    print("   FAIL Netz %d -> Pad bei (%.2f, %.2f)%s" % (net, x, y,
                          " auch mit Rip-up blockiert (Basis)" if rr else ""))
                continue
            nvia0 = len(self.vias)
            self.commit_path(path, net, hw * 2)
            tree |= goal
            for (L, j, i) in path:
                tree[L, j, i] = True
            for (x, y, n) in self.vias[nvia0:]:
                j, i = self.ij(x, y)
                tree[:, j, i] = True
            vfree = self.via_mask(net, 0.225)
        return fails, ripped


def simplify(pts):
    """Kollineare Rasterpunkte zusammenfassen."""
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    for k in range(1, len(pts) - 1):
        ax, ay = out[-1]
        bx, by = pts[k]
        cx, cy = pts[k + 1]
        d1 = (round((bx - ax) / 0.05), round((by - ay) / 0.05))
        d2 = (round((cx - bx) / 0.05), round((cy - by) / 0.05))
        # Richtung normieren
        def nrm(d):
            g = math.gcd(abs(d[0]), abs(d[1])) or 1
            return (d[0] // g, d[1] // g)
        if nrm(d1) != nrm(d2):
            out.append(pts[k])
    out.append(pts[-1])
    return out
