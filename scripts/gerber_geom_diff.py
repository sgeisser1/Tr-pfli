#!/usr/bin/env python3
"""Geometrischer Vergleich zweier Gerber-/Excellon-Ordner (KiCad-Ausgabe), unabhaengig von Aperturnummern,
Reihenfolge und Kopf-/Datumszeilen.

Jede Gerber-Operation wird mit der aufgeloesten Apertur-Definition (statt D-Nummer), Polaritaet, Interpolationsart
und Koordinaten zu einem Datensatz; Regionen (G36/G37) als ganzer Umriss. Verglichen werden die Multimengen je Datei.
Excellon: Werkzeugdurchmesser statt T-Nummer + Koordinaten.

Aufruf: .venv/bin/python scripts/gerber_geom_diff.py <ordner_alt> <ordner_neu>
Exit 0 = alle Dateien geometrisch gleich, 1 = Unterschiede (Liste je Datei).
"""
import collections
import math
import os
import re
import sys

COORD = re.compile(r"(?:X(-?\d+))?(?:Y(-?\d+))?(?:I(-?\d+))?(?:J(-?\d+))?D0?([123])\*$")


def canon(region):
    """Region als geschlossener Umriss: Startecke und Umlaufsinn egal (nur Geraden; mit Boegen unveraendert)."""
    if any(r[1] != "G01" or r[4] is not None for r in region) or not region or region[0][0] != "2":
        return tuple(region)
    pts = [(r[2], r[3]) for r in region]
    if len(pts) > 1 and pts[-1] == pts[0]:
        pts = pts[:-1]
    best = None
    for seq in (pts, pts[::-1]):
        i = seq.index(min(seq))
        cand = tuple(seq[i:] + seq[:i])
        best = cand if best is None or cand < best else best
    return ("POLY",) + best


def gerber_records(path):
    ap, cur, pol, interp = {}, None, "D", "G01"
    x = y = 0
    region, in_region = [], False
    rec = collections.Counter()
    macro = False
    for raw in open(path, encoding="ascii", errors="replace"):
        line = raw.strip()
        if not line or line.startswith("G04") or line.startswith("%TF") or line.startswith("%TA") or line.startswith("%TO") \
                or line.startswith("%TD"):
            continue
        if macro:
            if line.endswith("%"):
                macro = False
            continue
        if line.startswith("%AM"):
            macro = not line.endswith("%")
            rec[("MACRO", line)] += 1
            continue
        m = re.match(r"%ADD(\d+)(.*)\*%$", line)
        if m:
            ap[m.group(1)] = m.group(2)
            continue
        if line.startswith("%LP"):
            pol = line[3]
            continue
        if line.startswith("%"):
            rec[("HDR", line)] += 1
            continue
        m = re.match(r"^(?:G54)?D(\d{2,})\*$", line)
        if m:
            cur = ap.get(m.group(1), "?" + m.group(1))
            continue
        for g in ("G01", "G02", "G03"):
            if line.startswith(g):
                interp = g
                line = line[3:]
        if line in ("", "*"):
            continue
        if line.startswith("G36"):
            in_region, region = True, []
            continue
        if line.startswith("G37"):
            in_region = False
            rec[("REGION", pol, canon(region))] += 1
            continue
        if line.startswith("G75") or line.startswith("M02"):
            continue
        m = COORD.match(line)
        if not m:
            rec[("OTHER", line)] += 1
            continue
        nx = int(m.group(1)) if m.group(1) is not None else x
        ny = int(m.group(2)) if m.group(2) is not None else y
        d = m.group(5)
        if in_region:
            region.append((d, interp, nx, ny, m.group(3), m.group(4)))  # Startpunkt (vorherige Lage) nicht speichern
        elif d == "1":
            a, b = sorted([(x, y), (nx, ny)]) if interp == "G01" else ((x, y), (nx, ny))
            rec[("DRAW", pol, cur, interp, a, b, m.group(3), m.group(4))] += 1
        elif d == "3":
            rec[("FLASH", pol, cur, nx, ny)] += 1
        x, y = nx, ny
    return rec


def drill_records(path):
    tools, cur, rec = {}, None, collections.Counter()
    for raw in open(path, encoding="ascii", errors="replace"):
        line = raw.strip()
        m = re.match(r"^T(\d+)C([\d.]+)", line)
        if m:
            tools[m.group(1)] = m.group(2)
            continue
        m = re.match(r"^T(\d+)$", line)
        if m:
            cur = tools.get(m.group(1), "?")
            continue
        if line.startswith("X") or line.startswith("Y") or line.startswith("G85"):
            rec[(cur, line)] += 1
    return rec


def main(a, b):
    files = sorted(set(os.listdir(a)) | set(os.listdir(b)))
    bad = 0
    for f in files:
        pa, pb = os.path.join(a, f), os.path.join(b, f)
        if not (os.path.exists(pa) and os.path.exists(pb)):
            print(f"{f}: nur in {'alt' if os.path.exists(pa) else 'neu'}")
            bad += 1
            continue
        if f.endswith(".gbrjob"):
            la = [l for l in open(pa) if "CreationDate" not in l]
            lb = [l for l in open(pb) if "CreationDate" not in l]
            same = la == lb
            print(f"{f}: {'gleich (ohne CreationDate)' if same else 'VERSCHIEDEN'}")
            bad += not same
            continue
        fn = drill_records if f.endswith(".drl") else gerber_records
        ra, rb = fn(pa), fn(pb)
        if ra == rb:
            print(f"{f}: geometrisch gleich ({sum(ra.values())} Elemente)")
        else:
            only_a, only_b = ra - rb, rb - ra
            if all(k[0] == "REGION" and k[2][0] == "POLY" for k in list(only_a) + list(only_b)) and \
                    regions_equivalent(list(only_a.elements()), list(only_b.elements())):
                print(f"{f}: geometrisch gleich ({sum(ra.values())} Elemente; {sum(only_a.values())} Flaechenumriss(e) "
                      f"nur anders zerlegt: gleiche Flaeche, alle abweichenden Ecken liegen auf Kanten des Gegenstuecks)")
                continue
            print(f"{f}: VERSCHIEDEN, nur alt {sum(only_a.values())}, nur neu {sum(only_b.values())} Elemente")
            bad += 1
    return 1 if bad else 0


def _area(p):
    return 0.5 * abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p))))


def _on_edges(pt, poly, tol=2):
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        if L == 0:
            continue
        cr = (b[0] - a[0]) * (pt[1] - a[1]) - (b[1] - a[1]) * (pt[0] - a[0])
        if abs(cr) / L <= tol and min(a[0], b[0]) - tol <= pt[0] <= max(a[0], b[0]) + tol \
                and min(a[1], b[1]) - tol <= pt[1] <= max(a[1], b[1]) + tol:
            return True
    return False


def regions_equivalent(ka, kb):
    """Paare (gleiche Polaritaet, gleiche kleinste Ecke) mit gleicher Flaeche (< 1e-6 mm2) und kollinearen Zusatzecken."""
    if len(ka) != len(kb):
        return False
    key = lambda k: (k[1], k[2][1])
    for x, y in zip(sorted(ka, key=key), sorted(kb, key=key)):
        if key(x) != key(y):
            return False
        p, q = list(x[2][1:]), list(y[2][1:])
        if abs(_area(p) - _area(q)) > 1e6:          # Gerber-Einheit 1e-6 mm -> Toleranz 1e-6 mm2
            return False
        if not all(_on_edges(v, q) for v in set(p) - set(q)) or not all(_on_edges(v, p) for v in set(q) - set(p)):
            return False
    return True


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
