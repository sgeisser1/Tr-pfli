"""Nachtrag Layout Rev B (Befund L-3): S-Zuleitungen der Sonde aus der Platine lesen und nachrechnen.

1. Geometrie direkt aus hardware/sensor/fluidi_sensor.kicad_pcb (pcbnew): Zuleitungen /PROBE_SENSE auf In1/In2,
   gefuellte Zonen (Guard, Fach-GND, S-Elektrode), Bahnen, Pads und Vias aller Netze auf F/In1/In2/B. Querschnitte alle
   0.05 mm in Y zwischen Bandkante und Guard-Ende; gleiche Querschnitte werden zu Abschnitten zusammengefasst.
2. 2D-FEM (xsec2d.Model, P2, wie REPORT Kap. 2) je Abschnitt: Kapazitaetsbelag C' der Zuleitung(en) gegen alle anderen
   Leiter (= AC-Masse, ANNAHME: alle Netze ausser PROBE_SENSE sind waehrend der Messung niederohmig) fuer
   Aussenmedium eps 1 ... 80 und "leitend" (eps 1e4, schwebend), FR4-Empfindlichkeit.
   Vergleich mit den bisherigen Annahmen: "alt" (Zuleitung x -4.875 auf L2 und L3, wie im 3D-Halbmodell enthalten)
   und "Kap. 8" (nur L2 bei x -4.9, L3 darunter GND).
3. Medien je Zone (PCB_OUTLINE Rev B Kap. 3, KiCad-Y): Schott/Fach Y 20.8-46.0 (Luft; geflutet: Wasser), Kragen-Verguss
   Y 46.0-51.5 (Epoxid, eps 4 ANNAHME, Typ offen: INDEX.csv EP-K), frei Y 51.5-58.5 (Luft; Oberflaeche nass/ueberflutet),
   Erde Y 58.5-61.5 (Guard im Substrat). Ab Y 61.5 (Guard-Ende) gehoert die Zuleitung zum Messfeld -> 3D.
4. Zusammenfuehrung mit dem 3D-Vollmodell (probe3d_revb.py, alt/revb, h 1.4 und 1.0): Differenz revb - alt auf die
   extrapolierten Werte von REPORT Kap. 6 aufgeschlagen, plus 2D-Anteile ausserhalb des 3D-Modells (Kopf z_f < -15,
   Breite 26 mm im Fach, Verguss). Neues Ersatzschaltbild C0/Ci/Cg.
5. Frequenzbereich der Messkette D3 (osc_sim.py-Netzliste, ngspice -b, Ausgabe nur im Scratch/Temp) mit dem neuen
   Ersatzschaltbild und dem neuen Knotenanteil.

Aufruf:  .venv/bin/python simulation/field/leads_revb.py [--no-spice]
         (vorher: probe3d_revb.py --var alt|revb --h 1.4 und --h 1.0)
Ausgabe: results/leads_revb.json, results/leads_revb.txt
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
import params as P  # noqa: E402

PCB = os.path.join(ROOT, "hardware", "sensor", "fluidi_sensor.kicad_pcb")
RES = os.path.join(HERE, "results")
OX, OY = 150.0, 30.0            # Hilfsursprung der Platine (Schnittstellen-Ursprung, LAYOUT_REV_B Kap. 8)
LAYERS = {"F.Cu": "F", "In1.Cu": "L2", "In2.Cu": "L3", "B.Cu": "B"}
DY = 0.05
# Zonen in KiCad-Y (PCB_OUTLINE Rev B Kap. 3; Vergusskante z 2.0 -> Y 51.5; Stecktiefe Y 58.5; Guard-Ende Y 61.5)
Y_BAND, Y_SCHOTT1, Y_FACH1, Y_VERG, Y_EARTH, Y_GUARD1, Y_S0 = 20.78, 23.2, 46.0, 51.5, 58.5, 61.5, 63.5
EPS_LIST = [1.0, 3.0, 4.0, 6.0, 10.0, 25.0, 80.0, 1e4]
EPS_VERGUSS = 4.0               # ANNAHME Epoxid 2K mineralisch gefuellt (Typ offen, INDEX.csv EP-K); Band 3-6


# ---------------------------------------------------------------------------------------------------- Platine lesen
def _board():
    import pcbnew
    return pcbnew, pcbnew.LoadBoard(PCB)


def read_leads():
    """S-Zuleitungen: lange senkrechte /PROBE_SENSE-Bahnen auf In1/In2; Kanal aus der Guard-Fuellung (Y 55)."""
    pcbnew, b = _board()
    mm = pcbnew.ToMM
    out = []
    for t in b.GetTracks():
        if t.GetClass() == "PCB_VIA" or not t.GetNetname().endswith("PROBE_SENSE"):
            continue
        ln = b.GetLayerName(t.GetLayer())
        if ln not in ("In1.Cu", "In2.Cu"):
            continue
        x0, y0, x1, y1 = mm(t.GetStart().x) - OX, mm(t.GetStart().y) - OY, mm(t.GetEnd().x) - OX, mm(t.GetEnd().y) - OY
        if abs(x0 - x1) > 1e-6 or abs(y1 - y0) < 10:
            continue
        w = mm(t.GetWidth())
        sec = cross_section(55.0, b=b)
        gaps = [iv for iv in _gaps(sec["G"][LAYERS[ln]]) if iv[0] < x0 < iv[1]]
        clr = (gaps[0][1] - gaps[0][0] - w) / 2 if gaps else float("nan")
        out.append({"layer": LAYERS[ln], "x": round(x0, 4), "w": round(w, 4), "clr": round(clr, 4),
                    "y0": round(min(y0, y1), 3), "y1": round(max(y0, y1), 3)})
    return sorted(out, key=lambda d: d["layer"])


def _gaps(iv):
    return [(iv[k][1], iv[k + 1][0]) for k in range(len(iv) - 1)]


_POLYS = {}


def _polys(b):
    """{(Lage, 'S'|'G'): SHAPE_POLY_SET} aus Zonenfuellung, Bahnen, Pads, Vias."""
    import pcbnew
    if _POLYS:
        return _POLYS
    err = pcbnew.FromMM(0.001)
    for ln, lk in LAYERS.items():
        lid = b.GetLayerID(ln)
        for k in ("S", "G"):
            _POLYS[(lk, k)] = pcbnew.SHAPE_POLY_SET()

        def cls(net):
            if net.endswith("PROBE_SENSE"):
                return "S"
            if net.startswith("unconnected") or net == "":
                return None          # schwebende Pads (U3 ALERT) nicht modelliert
            return "G"
        for z in b.Zones():
            if z.GetIsRuleArea() or not z.IsOnLayer(lid):
                continue
            c = cls(z.GetNetname())
            if c:
                _POLYS[(lk, c)].Append(z.GetFilledPolysList(lid))
        for t in b.GetTracks():
            c = cls(t.GetNetname())
            if not c:
                continue
            if t.GetClass() == "PCB_VIA":
                if t.FlashLayer(lid):
                    t.TransformShapeToPolygon(_POLYS[(lk, c)], lid, 0, err, pcbnew.ERROR_INSIDE)
            elif t.GetLayer() == lid:
                t.TransformShapeToPolygon(_POLYS[(lk, c)], lid, 0, err, pcbnew.ERROR_INSIDE)
        for fp in b.GetFootprints():
            for pad in fp.Pads():
                c = cls(pad.GetNetname())
                if c and pad.IsOnLayer(lid) and pad.FlashLayer(lid):
                    pad.TransformShapeToPolygon(_POLYS[(lk, c)], lid, 0, err, pcbnew.ERROR_INSIDE)
    ol = pcbnew.SHAPE_POLY_SET()
    b.GetBoardPolygonOutlines(ol, True)
    _POLYS[("edge", "E")] = ol
    return _POLYS


def _strip(pcbnew, y):
    r = pcbnew.SHAPE_POLY_SET()
    r.NewOutline()
    for x, yy in ((-20, y - 5e-4), (20, y - 5e-4), (20, y + 5e-4), (-20, y + 5e-4)):
        r.Append(pcbnew.FromMM(OX + x), pcbnew.FromMM(OY + yy))
    return r


def _intervals(pcbnew, ps, y):
    c = pcbnew.SHAPE_POLY_SET(ps)
    c.BooleanIntersection(_strip(pcbnew, y))
    iv = []
    for i in range(c.OutlineCount()):
        o = c.Outline(i)
        xs = [pcbnew.ToMM(o.CPoint(k).x) - OX for k in range(o.PointCount())]
        if xs:
            iv.append([min(xs), max(xs)])
    iv.sort()
    m = []
    for a, bb in iv:                      # verschmelzen (Zonen ueberlappen, Bahnen in Zonen)
        if m and a <= m[-1][1] + 1e-4:
            m[-1][1] = max(m[-1][1], bb)
        else:
            m.append([a, bb])
    return [(round(a, 4), round(bb, 4)) for a, bb in m]


def cross_section(y, b=None):
    import pcbnew
    if b is None:
        _, b = _board()
    ps = _polys(b)
    sec = {"y": y, "S": {}, "G": {}}
    for lk in LAYERS.values():
        s = _intervals(pcbnew, ps[(lk, "S")], y)
        g = _intervals(pcbnew, ps[(lk, "G")], y)
        # S hat Vorrang (die S-Bahn liegt im Kanal, nie in der G-Flaeche; Kontrolle)
        for a, bb in s:
            for c, d in g:
                assert d <= a + 1e-3 or c >= bb - 1e-3, f"S/G-Ueberlappung bei Y {y} {lk}"
        sec["S"][lk], sec["G"][lk] = s, g
    e = _intervals(pcbnew, ps[("edge", "E")], y)
    sec["x_edge"] = (e[0][0], e[-1][1])
    return sec


def section_key(sec):
    """Rundung: nahe der Zuleitung 0.01 mm, weiter als 1.5 mm entfernt 0.25 mm (Kanten im Schulterbogen)."""
    xs = [v for lk in sec["S"] for iv in sec["S"][lk] for v in iv]
    lo, hi = (min(xs), max(xs)) if xs else (0, 0)

    def r(v):
        far = v < lo - 1.5 or v > hi + 1.5
        return round(round(v / 0.25) * 0.25, 2) if far else round(v, 2)
    key = []
    for k in ("S", "G"):
        for lk in ("F", "L2", "L3", "B"):
            key.append((k, lk, tuple((r(a), r(bb)) for a, bb in sec[k][lk] if r(bb) > r(a))))
    key.append(("W", round(round((sec["x_edge"][1] - sec["x_edge"][0]) / 0.25) * 0.25, 2)))
    return tuple(key)


def extract_sections(y0=Y_BAND + 0.025, y1=Y_GUARD1):
    _, b = _board()
    segs = []
    for y in np.arange(y0, y1 - 1e-9, DY):
        sec = cross_section(float(y), b=b)
        if not any(sec["S"][lk] for lk in sec["S"]):
            continue
        key = section_key(sec)
        # Abschnitte nie ueber Zonengrenzen (Medium) zusammenfassen
        if segs and segs[-1]["key"] == key and zone_of(segs[-1]["y0"] + DY / 2) == zone_of(float(y)):
            segs[-1]["y1"] = float(y) + DY / 2
        else:
            segs.append({"key": key, "y0": float(y) - DY / 2, "y1": float(y) + DY / 2})
    return segs


# ---------------------------------------------------------------------------------------------------- 2D-FEM
def geometry_from_key(key, **kw):
    import xsec2d as X
    el = []
    W = None
    for item in key:
        if item[0] == "W":
            W = item[1]
            continue
        net, lk, ivs = item
        for a, bb in ivs:
            el.append(X.Electrode(lk, a, bb, net))
    # Platine symmetrisch zur Mitte (Kontur PCB_OUTLINE Kap. 2), Breite aus Edge.Cuts
    return X.Geometry(el, width=W, **kw)


def synth_key(leads, W, gx):
    """Synthetischer Querschnitt: Guard (GND) auf L2/L3 von -gx..gx mit Kanaelen um die Zuleitungen."""
    key = []
    for net in ("S", "G"):
        for lk in ("F", "L2", "L3", "B"):
            ll = sorted([ld for ld in leads if ld[0] == lk], key=lambda d: d[1])
            if net == "S":
                key.append((net, lk, tuple((x - w / 2, x + w / 2) for _, x, w, c in ll)))
            elif lk in ("L2", "L3"):
                ivs, xa = [], -gx
                for _, x, w, c in ll:
                    ivs.append((xa, x - w / 2 - c))
                    xa = x + w / 2 + c
                ivs.append((xa, gx))
                key.append((net, lk, tuple(ivs)))
            else:
                key.append((net, lk, ()))
    key.append(("W", W))
    return tuple(key)


def solve_key(key):
    import xsec2d as X
    g = geometry_from_key(key)
    m = X.Model(g)
    out = {"C": {}, "S_fr4": {}}
    for e in EPS_LIST:
        eps = m.default_eps(e)
        c, phi = m.cap(eps)
        rs = m.region_sens(phi)
        out["C"][e] = c
        # Drift bei FR4-Er +10 % (linear): dC = 0.1 * (er_pp * S_pp + er_core * S_core)
        out["S_fr4"][e] = P.DK_FR4_MOIST_REL * (eps["fr4"] * rs.get("fr4", 0) + eps["core"] * rs.get("core", 0))
    out["ndof"] = m.ndof
    return out


def _solve_many(keys, jobs=12):
    import multiprocessing as mp
    with mp.get_context("fork").Pool(jobs) as pool:
        return pool.map(solve_key, keys)


def overlap(seg, ya, yb):
    """Laenge [mm] des Abschnitts seg innerhalb ya ... yb."""
    return max(0.0, min(seg["y1"], yb) - max(seg["y0"], ya))


def zone_of(ymid):
    if ymid < Y_SCHOTT1:
        return "schott"
    if ymid < Y_FACH1:
        return "fach"
    if ymid < Y_VERG:
        return "kragen"
    if ymid < Y_EARTH:
        return "frei"
    return "erde"


# ---------------------------------------------------------------------------------------------------- Band (Schaetzung)
def band_trace_estimate():
    """Laenge der /PROBE_SENSE-Bahnen im Band (F/B) und Vias. Belag aus 2D-Mikrostreifen 0.15 mm auf F ueber In1-GND
    mit koplanarer F-GND-Flaeche (Abstand 0.2, Zonenregel GND_F) und Luft darueber; B entsprechend ueber In2 (VDD)."""
    import xsec2d as X
    pcbnew, b = _board()
    mm = pcbnew.ToMM
    L = {"F.Cu": 0.0, "B.Cu": 0.0}
    nvia = 0
    for t in b.GetTracks():
        if not t.GetNetname().endswith("PROBE_SENSE"):
            continue
        if t.GetClass() == "PCB_VIA":
            nvia += 1
        elif b.GetLayerName(t.GetLayer()) in L:
            L[b.GetLayerName(t.GetLayer())] += mm(t.GetLength())
    w, s = 0.15, 0.2
    el = [X.Electrode("F", -w / 2, w / 2, "S"), X.Electrode("F", -6, -w / 2 - s, "G"),
          X.Electrode("F", w / 2 + s, 6, "G"), X.Electrode("L2", -6, 6, "G")]
    m = X.Model(X.Geometry(el, width=12.0))
    c, _ = m.cap(m.default_eps(1.0))
    return {"len_F_mm": L["F.Cu"], "len_B_mm": L["B.Cu"], "n_via": nvia, "Cp_microstrip_pF_m": c,
            "C_traces_pF": c * (L["F.Cu"] + L["B.Cu"]) * 1e-3}


# ---------------------------------------------------------------------------------------------------- Auswertung
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-spice", action="store_true")
    ap.add_argument("--jobs", type=int, default=12)
    a = ap.parse_args()
    lines = []

    def pr(s=""):
        print(s, flush=True)
        lines.append(s)

    leads = read_leads()
    pr("## 1 Zuleitungen aus der Platine (pcbnew, " + os.path.relpath(PCB, ROOT) + ")")
    for d in leads:
        pr(f"- {d['layer']}: x {d['x']:+.3f} mm, Breite {d['w']:.3f}, Kanal (Abstand zum Guard) {d['clr']:.3f}, "
           f"Y {d['y0']:.2f} ... {d['y1']:.2f} (Laenge {d['y1'] - d['y0']:.2f} mm)")
    lead_t = [(d["layer"], d["x"], d["w"], d["clr"]) for d in leads]
    g3 = __import__("probe3d").GEOS["sg"]
    xs_old = (-(P.W_PROBE / 2 - g3.edge) - g3.gap / 2) / 2
    old_t = [("L2", xs_old, g3.wf, g3.cf), ("L3", xs_old, g3.wf, g3.cf)]
    kap8_t = [("L2", -4.9, 0.3, 0.3)]
    for y in (30.0, 47.9, 48.95, 55.0, 60.0):
        sec = cross_section(y)
        pr(f"- Querschnitt Y {y}: Kante {sec['x_edge'][0]:+.2f}/{sec['x_edge'][1]:+.2f}; " + "; ".join(
            f"{lk} S {sec['S'][lk]} G {[iv for iv in sec['G'][lk] if iv[0] < -3.5]}..." for lk in ("F", "L2", "L3")))

    segs = extract_sections()
    pr(f"\n## 2 Abschnitte (Y {Y_BAND + 0.025:.2f} ... {Y_GUARD1}, Raster {DY} mm): {len(segs)} verschiedene Querschnitte")
    # Synthetische Vergleichsquerschnitte: Fach (26 mm, Guard bis 11.95) und Sonde (20 mm, Guard bis 8.75)
    synth = {}
    schmal_t = [(lk, x, 0.15, 0.2) for lk, x, w, c in lead_t]     # Option Rev C: 0.15 mm, Kanal 0.2 (JLC >= 0.10)
    for name, ld in (("revb", lead_t), ("alt", old_t), ("kap8", kap8_t), ("schmal", schmal_t)):
        synth[(name, "sonde")] = synth_key(ld, 20.0, 8.75)
        synth[(name, "fach")] = synth_key(ld, 26.0, 11.95)
    keys = [s["key"] for s in segs] + list(synth.values())
    uniq = list(dict.fromkeys(keys))
    sol = dict(zip(uniq, _solve_many(uniq, a.jobs)))
    # Zonen-Summen (pF) je Aussen-eps
    zones = {}
    for s in segs:
        L = (s["y1"] - s["y0"]) * 1e-3
        z = zone_of((s["y0"] + s["y1"]) / 2)
        r = sol[s["key"]]
        zd = zones.setdefault(z, {"L_mm": 0.0, "C": {e: 0.0 for e in EPS_LIST}, "dFR4": {e: 0.0 for e in EPS_LIST}})
        zd["L_mm"] += L * 1e3
        for e in EPS_LIST:
            zd["C"][e] += r["C"][e] * L
            zd["dFR4"][e] += r["S_fr4"][e] * L
    pr("\n| Zone | Y | Laenge [mm] | C [pF] bei Aussen-eps 1 / 4 / 25 / 80 / leitend | FR4 +10 % [pF] (eps 1) |")
    pr("|---|---|---|---|---|")
    yr = {"schott": (Y_BAND, Y_SCHOTT1), "fach": (Y_SCHOTT1, Y_FACH1), "kragen": (Y_FACH1, Y_VERG),
          "frei": (Y_VERG, Y_EARTH), "erde": (Y_EARTH, Y_GUARD1)}
    for z in ("schott", "fach", "kragen", "frei", "erde"):
        zd = zones[z]
        pr(f"| {z} | {yr[z][0]}-{yr[z][1]} | {zd['L_mm']:.2f} | " + " / ".join(
            f"{zd['C'][e]:.3f}" for e in (1.0, 4.0, 25.0, 80.0, 1e4)) + f" | {zd['dFR4'][1.0]:.3f} |")
    pr("\nBelag C' [pF/m] synthetisch (Guard ohne U3-Feld), Aussen-eps 1 / 4 / 25 / 80 / leitend:")
    for (name, where), k in synth.items():
        c = sol[k]["C"]
        pr(f"- {name:5s} {where:5s}: " + " / ".join(f"{c[e]:.1f}" for e in (1.0, 4.0, 25.0, 80.0, 1e4)) +
           f"   (Kopplung nach aussen eps 1 -> 80: {c[80.0] - c[1.0]:+.1f} pF/m)")
    # Ganze Zuleitung, Betriebsfall: Fach Luft, Kragen Verguss, frei Luft, Erde eps_soil
    def total(name, media):
        """name 'revb' = extrahierte Abschnitte; 'alt'/'kap8' = synthetisch mit gleichen Zonenlaengen."""
        tot = 0.0
        for z, zd in zones.items():
            e = media[z]
            if name == "revb":
                tot += zd["C"][e]
            else:
                k = synth[(name, "fach" if z in ("schott", "fach") else "sonde")]
                tot += sol[k]["C"][e] * zd["L_mm"] * 1e-3
        return tot
    base = {"schott": EPS_VERGUSS, "fach": 1.0, "kragen": EPS_VERGUSS, "frei": 1.0, "erde": 1.0}
    scen = {
        "Betrieb, Erde Luft": base,
        "Betrieb, Erde trocken (4)": {**base, "erde": P.EPS_DRY},
        "Betrieb, Erde nass (25)": {**base, "erde": P.EPS_WET},
        "Betrieb, Erde Wasser (80)": {**base, "erde": P.EPS_WATER},
        "Oberflaeche nass: frei+Erde 25": {**base, "frei": P.EPS_WET, "erde": P.EPS_WET},
        "ueberflutet bis Verguss: frei+Erde 80": {**base, "frei": P.EPS_WATER, "erde": P.EPS_WATER},
        "Wasser leitend bis Verguss": {**base, "frei": 1e4, "erde": 1e4},
        "Fach geflutet (80), sonst trocken": {**base, "fach": P.EPS_WATER, "erde": P.EPS_DRY},
        "Fach geflutet leitend, sonst trocken": {**base, "fach": 1e4, "erde": P.EPS_DRY},
        "Verguss eps 3 / 6 (trocken)": None,
    }
    pr("\n## 3 Ganze Zuleitung bis Guard-Ende (Y 20.8 ... 61.5) [pF]: Rev B / alt (x -4.875, L2+L3) / Kap. 8 (L2 -4.9) / "
       "Option schmal (Rev-B-Lage, 0.15 mm, Kanal 0.2; synthetisch)")
    pr("| Fall | Rev B | alt | Kap. 8 | schmal |")
    pr("|---|---|---|---|---|")
    tots = {}
    for k, media in scen.items():
        if media is None:
            v = [total(n, {**base, "erde": P.EPS_DRY, "kragen": 3.0, "schott": 3.0}) for n in ("revb", "alt", "kap8", "schmal")]
            w = [total(n, {**base, "erde": P.EPS_DRY, "kragen": 6.0, "schott": 6.0}) for n in ("revb", "alt", "kap8", "schmal")]
            pr(f"| {k} | {v[0]:.3f} / {w[0]:.3f} | {v[1]:.3f} / {w[1]:.3f} | {v[2]:.3f} / {w[2]:.3f} | {v[3]:.3f} / {w[3]:.3f} |")
            tots[k] = {"revb": [v[0], w[0]], "alt": [v[1], w[1]], "kap8": [v[2], w[2]]}
            continue
        v = {n: total(n, media) for n in ("revb", "alt", "kap8", "schmal")}
        tots[k] = v
        pr(f"| {k} | {v['revb']:.3f} | {v['alt']:.3f} | {v['kap8']:.3f} | {v['schmal']:.3f} |")

    # ---------------- 3D zusammenfuehren
    r3 = {}
    for var in ("alt", "revb"):
        for h in (1.4, 1.0):
            p = os.path.join(RES, f"probe3d_revb_{var}_h{h:g}.json")
            if os.path.exists(p):
                r3[(var, h)] = json.load(open(p))["C_pF"]
    out = {"leads": leads, "zones": {z: {"L_mm": zd["L_mm"], "C_pF": {str(e): v for e, v in zd["C"].items()},
                                         "dFR4_pF": {str(e): v for e, v in zd["dFR4"].items()}}
                                     for z, zd in zones.items()},
           "synth_Cp_pF_m": {f"{n}_{w}": {str(e): v for e, v in sol[k]["C"].items()} for (n, w), k in synth.items()},
           "totals_pF": tots, "segments": len(segs), "band": None, "3d": {f"{v}_h{h:g}": c for (v, h), c in r3.items()}}
    band = band_trace_estimate()
    out["band"] = band
    pr(f"\nBand: /PROBE_SENSE F {band['len_F_mm']:.1f} mm, B {band['len_B_mm']:.1f} mm, {band['n_via']} Vias; "
       f"Mikrostreifen {band['Cp_microstrip_pF_m']:.1f} pF/m -> {band['C_traces_pF']:.2f} pF (ohne Vias/Pads)")
    old_ext = json.load(open(os.path.join(RES, "probe_lumped_3d_extrap.json")))
    if r3:
        pr("\n## 4 3D-Vollmodell (Elmer, Kopf z_f -15...0 Luft wie REPORT Kap. 6) [pF]")
        cases = list(next(iter(r3.values())).keys())
        pr("| Fall | " + " | ".join(f"{v} h{h:g}" for (v, h) in r3) + " | revb-alt h1.0 | revb-alt h1.4 |")
        pr("|---|" + "---|" * (len(r3) + 2))
        d3 = {}
        for c in cases:
            vals = [r3[k][c] for k in r3]
            dd = {h: r3[("revb", h)][c] - r3[("alt", h)][c] for h in (1.4, 1.0)
                  if ("revb", h) in r3 and ("alt", h) in r3}
            d3[c] = dd
            pr(f"| {c} | " + " | ".join(f"{v:.3f}" for v in vals) + " | " +
               " | ".join(f"{dd.get(h, float('nan')):+.3f}" for h in (1.0, 1.4)) + " |")
        out["delta3d"] = {c: {str(h): v for h, v in dd.items()} for c, dd in d3.items()}
        # Neue Sondenwerte: extrapolierte alte Werte + Differenz (h 1.0) + 2D-Korrekturen ausserhalb des 3D-Modells:
        #  (a) Zuleitung Y 20.8 ... 38.5 (z_f < -15, im 3D nicht enthalten), Fach Luft -> konstant
        #  (b) Kopf z_f -15 ... -7.5 (Y 38.5 ... 46): reale Breite 26 mm/Fach-GND statt 20 mm im 3D-Modell
        #  (c) Kragen-Verguss Y 46.0 ... 51.5: eps 4 statt Luft im 3D-Modell
        # Diese Anteile sind unabhaengig vom Substrat -> Knoten (C_NODE), getrennt ausgewiesen.
        hbest = 1.0 if all(1.0 in d3[c] for c in d3) else 1.4
        new = {}
        for c, key in (("air", "C_air"), ("dry", "C_dry"), ("wet", "C_wet"), ("water", "C_water")):
            new[c] = old_ext[key] + d3[c][hbest]
        out["probe_new_extrap_pF"] = new
        out["h_used"] = hbest
        pr(f"\nSonde (Messfeld + Zuleitung ab z_f -15) extrapoliert: alt / neu [pF] (Differenz aus h {hbest:g}):")
        for c, key in (("air", "C_air"), ("dry", "C_dry"), ("wet", "C_wet"), ("water", "C_water")):
            pr(f"- {c:5s}: {old_ext[key]:.3f} / {new[c]:.3f}  ({new[c] - old_ext[key]:+.3f})")
        sp_o = old_ext["C_wet"] - old_ext["C_dry"]
        sp_n = new["wet"] - new["dry"]
        pr(f"- Spanne trocken->nass: {sp_o:.3f} / {sp_n:.3f} pF ({100 * (sp_n / sp_o - 1):+.2f} %)")
        for hh in (1.0, 1.4):
            if ("revb", hh) in r3:
                ro, rn = r3[("alt", hh)], r3[("revb", hh)]
                for c in ("wet_flood", "water_flood", "dry_flood"):
                    base_c = {"wet_flood": "wet", "water_flood": "water", "dry_flood": "dry"}[c]
                    so, sn = ro["wet"] - ro["dry"], rn["wet"] - rn["dry"]
                    pr(f"- h {hh:g} {c}: Zusatz gegen Erde ab z_f 5: alt {ro[c] - ro[base_c]:+.3f} pF "
                       f"({100 * (ro[c] - ro[base_c]) / so:+.1f} % Spanne), neu {rn[c] - rn[base_c]:+.3f} pF "
                       f"({100 * (rn[c] - rn[base_c]) / sn:+.1f} % Spanne)")
                # z_f -2 ... 0 (Y 51.5 ... 53.5) liegt im 3D-Modell im Luftkopf -> 2D-Anteil der Zuleitung dazu
                for e_fl, c in ((P.EPS_WET, "wet_flood"), (P.EPS_WATER, "water_flood"), (1e4, "water_flood")):
                    d2 = sum((sol[s["key"]]["C"][e_fl] - sol[s["key"]]["C"][1.0]) * overlap(s, Y_VERG, 53.5) * 1e-3
                             for s in segs)
                    base_c = "wet" if c == "wet_flood" else "water"
                    sn = rn["wet"] - rn["dry"]
                    tot = rn[c] - rn[base_c] + d2
                    lab = "leitend" if e_fl > 1e3 else f"eps {e_fl:g}"
                    pr(f"- h {hh:g} Wasser/Erde bis Vergusskante (z_f -2), {lab}: 3D z_f 0...5 "
                       f"{rn[c] - rn[base_c]:+.3f} + Zuleitung z_f -2...0 (2D) {d2:+.3f} = {tot:+.3f} pF "
                       f"({100 * tot / sn:+.1f} % Spanne)")
                fo = (ro["water_fr4wet"] - ro["water"]) / (ro["wet"] - ro["dry"])
                fn = (rn["water_fr4wet"] - rn["water"]) / (rn["wet"] - rn["dry"])
                fa_o = (ro["air_fr4wet"] - ro["air"]) / (ro["wet"] - ro["dry"])
                fa_n = (rn["air_fr4wet"] - rn["air"]) / (rn["wet"] - rn["dry"])
                pr(f"- h {hh:g} FR4 +10 %: Luft alt/neu {100 * fa_o:.2f}/{100 * fa_n:.2f} % Spanne, "
                   f"Wasser {100 * fo:.2f}/{100 * fn:.2f} % Spanne")
                if "fill010.0" in ro and "fill010.0" in rn:
                    q = [(r["fill010.0"] - r["fill090.0"]) / (r["wet"] - r["air"]) for r in (ro, rn)]
                    pr(f"- h {hh:g} REQ-MES-08 Anteil 10-90 mm: alt {100 * q[0]:.1f} %, neu {100 * q[1]:.1f} %")
        # Ersatzschaltbild (wie conv3d.py) auf die neuen Werte
        from scipy.optimize import least_squares
        ee = np.array([1.0, P.EPS_DRY, P.EPS_WET, P.EPS_WATER])
        cc = np.array([new["air"], new["dry"], new["wet"], new["water"]])
        mod = lambda q, x: np.exp(q[0]) + np.exp(q[1]) * np.exp(q[2]) * x / (np.exp(q[1]) + np.exp(q[2]) * x)
        so = least_squares(lambda q: (mod(q, ee) - cc) / cc, np.log([7.0, 100.0, 1.7]))
        C0, Ci, Cg = (float(v) for v in np.exp(so.x))
        out["lumped_new"] = {"C0_pF": C0, "Ci_pF": Ci, "Cg_pF": Cg, "fit_max_rel": float(np.max(np.abs(so.fun)))}
        pr(f"- Ersatzschaltbild neu: C0 {C0:.3f} (alt {old_ext['C0_pF']:.3f}), Ci {Ci:.2f} (alt {old_ext['Ci_pF']:.2f}),"
           f" Cg {Cg:.4f} (alt {old_ext['Cg_pF']:.4f}) pF, Fit max {100 * out['lumped_new']['fit_max_rel']:.2f} %")
        # Knotenanteil (konstant): Zuleitung ausserhalb des 3D-Modells (a)+(b)+(c)
        a_ = 0.0
        b_ = 0.0
        c3d = sol[synth[("revb", "sonde")]]["C"][1.0]      # wie im 3D-Kopf: 20 mm breit, Guard +-8.75, Luft
        for s in segs:
            r = sol[s["key"]]
            e_z = EPS_VERGUSS if zone_of((s["y0"] + s["y1"]) / 2) in ("schott", "kragen") else 1.0
            a_ += r["C"][e_z] * overlap(s, 0.0, 53.5 - 15.0) * 1e-3
            b_ += (r["C"][e_z] - c3d) * overlap(s, 53.5 - 15.0, 53.5) * 1e-3
        out["node_extra_pF"] = {"a_kopf_ausserhalb_3d": a_, "b_c_breite_verguss": b_}
        pr(f"- Knotenanteil ausserhalb 3D: (a) Zuleitung Y 20.8...38.5 (z_f < -15) {a_:.3f} pF, (b+c) Y 38.5...53.5 Breite 26 mm/Verguss statt 3D-Kopf {b_:+.3f} pF")
        # alte Annahme fuer den gleichen Anteil: Zuleitung alt (synthetisch, Fach) gleiche Laenge
        a_old = sum(sol[synth[("alt", "fach")]]["C"][EPS_VERGUSS if (s["y0"] + s["y1"]) / 2 < Y_SCHOTT1 else 1.0]
                    * overlap(s, 0.0, 53.5 - 15.0) * 1e-3 for s in segs)
        out["node_extra_old_pF"] = a_old
        pr(f"- gleicher Anteil mit alter Zuleitung (x -4.875, L2+L3): {a_old:.3f} pF")

        if not a.no_spice:
            out["spice"] = spice(out, old_ext, band, pr)
    json.dump(out, open(os.path.join(RES, "leads_revb.json"), "w"), indent=1, default=str)
    open(os.path.join(RES, "leads_revb.txt"), "w").write("\n".join(lines) + "\n")
    print("->", os.path.join(RES, "leads_revb.json"))


def spice(out, old_ext, band, pr):
    """Frequenzbereich D3 mit osc_sim-Netzliste: alt (Repo-Stand) und neu (Ersatzschaltbild + Knoten)."""
    sys.path.insert(0, os.path.join(ROOT, "simulation", "spice", "osc"))
    import osc_sim as O
    tmp = tempfile.mkdtemp(prefix="fluidi_leads_")
    O.HERE = tmp                              # osc_last.cir nur im Temp-Ordner, Repo bleibt unveraendert
    fit_old = dict(O.FIT)
    c_node_old = O.C_NODE
    # Neuer Knoten: alter Knoten (10.5 pF: U2 Ci 4.5 + Leiterbahn/Durchfuehrung 5.5 ANNAHME + TP5 0.5) ersetzt durch
    # U2 4.5 + TP5 0.5 + Band-Bahnen (2D) + 4 Vias je 0.15 pF (ANNAHME) + Zuleitung ausserhalb des 3D-Modells (2D)
    c_node_new = (4.5 + 0.5 + band["C_traces_pF"] + 0.15 * band["n_via"] + out["node_extra_pF"]["a_kopf_ausserhalb_3d"]
                  + out["node_extra_pF"]["b_c_breite_verguss"]) * 1e-12
    fit_new = dict(fit_old, **out["lumped_new"])
    pr(f"\n## 5 Messkette D3 (ngspice, osc_sim.py-Netzliste): Knoten alt {c_node_old * 1e12:.2f} pF, "
       f"neu {c_node_new * 1e12:.2f} pF; C0 alt {fit_old['C0_pF']:.3f} / neu {fit_new['C0_pF']:.3f} pF")
    runs = [("Luft", "typ", 3.0, "f0", 1e3), ("trocken", "typ", 3.0, "f0", 1e3), ("Mitte Leitung", "typ", 3.0, "f0", 1e3),
            ("nass Leitung", "typ", 3.0, "f0", 1e3), ("Wasser Leitung", "typ", 3.0, "f0", 1e3),
            ("Luft", "hyst_min", 3.0, "f0", 1e3), ("nass gedüngt normal", "hyst_max", 2.4, "f1", 1e3),
            ("Luft", "hyst_min", 3.0, "f0", 1e4), ("nass gedüngt normal", "hyst_max", 2.4, "f1", 1e4)]
    res = []
    pr("| Sonde | Ecke | VDD | Cref | R3 | f_osc alt [MHz] | f_osc neu [MHz] | MEAS_CLK neu [MHz] | Aenderung |")
    pr("|---|---|---|---|---|---|---|---|---|")
    for probe, corner, vdd, cref, r3 in runs:
        f = {}
        for tag, fit, cn in (("alt", fit_old, c_node_old), ("neu", fit_new, c_node_new)):
            O.FIT, O.C_NODE = fit, cn
            r, _ = O.sim(vdd, probe, cref, corner, r3)
            f[tag] = r["f"] / 1e6
        res.append(dict(probe=probe, corner=corner, vdd=vdd, cref=cref, R3=r3, f_old=f["alt"], f_new=f["neu"]))
        pr(f"| {probe} | {corner} | {vdd} | {cref} | {r3 / 1e3:g} k | {f['alt']:.2f} | {f['neu']:.2f} | "
           f"{f['neu'] / 8:.3f} | {100 * (f['neu'] / f['alt'] - 1):+.1f} % |")
    O.FIT, O.C_NODE = fit_old, c_node_old
    return {"c_node_old_pF": c_node_old * 1e12, "c_node_new_pF": c_node_new * 1e12, "runs": res}


if __name__ == "__main__":
    main()
