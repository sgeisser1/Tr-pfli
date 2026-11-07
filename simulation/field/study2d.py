"""2D-Parameterstudie Elektrodengeometrie / Isolationsdicke / 2L vs 4L.

Aufruf: .venv/bin/python simulation/field/study2d.py   (ca. 2-4 min, 16 Prozesse)
Ausgabe: results/study2d.csv, results/study2d_salt.csv, plots/2d_*.png
Kennzahlen je Variante (Belaege pro m Elektrodenlaenge):
  C_air/C_dry/C_wet/C_water  C' in pF/m bei eps_Substrat 1 / 4 / 25 / 80
  span     C_wet - C_dry (Nutzhub), ratio = (C_wet - C_air)/C_air (Nutz- zu Grundkapazitaet)
  S_dry/S_wet  dC'/d eps_Substrat bei eps 4 bzw. 25 (pF/m pro eps-Einheit)
  d50/d90  Abstand von der Sondenoberflaeche, innerhalb dessen 50/90 % von dC'/d eps liegen (mm)
  fr4_moist  Drift bei FR4-Er +10 % (Saettigung) in % der Spanne, Mittel aus Luft- und Wasserpunkt
  tc_fr4   FR4-Temperaturgang (0.1 %/K) in %-Punkten/K, im Nasspunkt
  gap01/gap05  Spanne mit 0.1 / 0.5 mm Luftspalt relativ zu ohne (%)
"""
import os
import sys
import math
import multiprocessing as mp

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import params as P  # noqa: E402
import xsec2d as X  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
PLT = os.path.join(HERE, "plots")


def penetration(m, phi, eps_soil):
    e = m.element_energy(phi)
    soil = m.regs == X.REG.index("soil")
    d = m.dist[soil]
    s = e[soil]
    o = np.argsort(d)
    cs = np.cumsum(s[o]) / s.sum()
    return float(np.interp(0.5, cs, d[o])), float(np.interp(0.9, cs, d[o])), (d[o], cs)


def fr4_sens(m, phi):
    rs = m.region_sens(phi)
    return rs.get("fr4", 0) + rs.get("core", 0)


def evaluate(args):
    name, g, extra = args
    m = X.Model(g)
    out = {"name": name, **extra, "ndof": m.ndof}
    caps = {}
    for key, es in (("air", P.EPS_AIR), ("dry", P.EPS_DRY), ("wet", P.EPS_WET), ("water", P.EPS_WATER)):
        eps = m.default_eps(es)
        c, phi = m.cap(eps)
        caps[key] = (c, phi, eps)
        out["C_" + key] = c
    span = out["C_wet"] - out["C_dry"]
    out["span"] = span
    out["ratio"] = (out["C_wet"] - out["C_air"]) / out["C_air"]
    out["S_dry"] = m.region_sens(caps["dry"][1])["soil"]
    out["S_wet"] = m.region_sens(caps["wet"][1])["soil"]
    tpp, tcore, er, hb = g.stack_vals()
    er_fr4 = g.er_fr4 or er
    dfa = fr4_sens(m, caps["air"][1]) * er_fr4 * P.DK_FR4_MOIST_REL
    dfw = fr4_sens(m, caps["water"][1]) * er_fr4 * P.DK_FR4_MOIST_REL
    out["fr4_moist_air"] = 100 * dfa / span
    out["fr4_moist_water"] = 100 * dfw / span
    out["fr4_moist"] = 0.5 * (out["fr4_moist_air"] + out["fr4_moist_water"])
    out["tc_fr4"] = 100 * fr4_sens(m, caps["wet"][1]) * er_fr4 * P.DK_FR4_TC / span
    # Energieanteile im Nasspunkt
    rs = m.region_sens(caps["wet"][1])
    eps = caps["wet"][2]
    out["share_soil_wet"] = rs["soil"] * eps["soil"] / out["C_wet"]
    out["share_fr4_air"] = fr4_sens(m, caps["air"][1]) * er_fr4 / out["C_air"]
    d50, d90, _ = penetration(m, caps["dry"][1], P.EPS_DRY)
    out["d50_dry"], out["d90_dry"] = d50, d90
    d50, d90, _ = penetration(m, caps["wet"][1], P.EPS_WET)
    out["d50_wet"], out["d90_wet"] = d50, d90
    if extra.get("gaps", True):
        for tg, key in ((0.1, "gap01"), (0.5, "gap05")):
            g2 = X.Geometry(**{**g.__dict__, "t_gap": tg})
            m2 = X.Model(g2)
            sp = m2.cap(m2.default_eps(P.EPS_WET))[0] - m2.cap(m2.default_eps(P.EPS_DRY))[0]
            out[key] = 100 * (sp / span - 1)
    return out


def salt_eval(args):
    """Komplexe Admittanz ueber sigma und f; Rueckgabe Liste von Zeilen."""
    name, g = args
    m = X.Model(g)
    rows = []
    tpp, tcore, er, hb = g.stack_vals()
    er_fr4 = g.er_fr4 or er
    for eps_s in (P.EPS_AIR, P.EPS_DRY, 10.0, P.EPS_WET, P.EPS_WATER):
        sig_list = [0.0] if eps_s == P.EPS_AIR else [0.0, 0.001, 0.003, 0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3]
        for f in (1e6, 2e6, 4e6, 6e6, 10e6, 20e6, 70e6):
            for sg in sig_list:
                epsr = {"soil": eps_s, "gap": 1.0, "coat": g.er_coat * (1 - 1j * P.TAN_D_COAT),
                        "mask": g.er_mask * (1 - 1j * 0.02),  # Df Lack 0.02 ANNAHME
                        "fr4": er_fr4 * (1 - 1j * P.TAN_D_FR4_DRY), "core": er_fr4 * (1 - 1j * P.TAN_D_FR4_DRY)}
                # 2D: Integral |grad phi|^2 dA ist dimensionslos -> Y' [S/m] = kappa [S/m] * Integral
                Y, _ = m.admittance(epsr, {"soil": sg}, f)
                w = 2 * math.pi * f
                rows.append({"name": name, "eps": eps_s, "f": f, "sigma": sg,
                             "G": float(np.real(Y)), "C": float(np.imag(Y)) / w * 1e12})
    return rows


def variants():
    V = []
    base = dict(layers=4)
    for gap in (0.5, 1, 2, 3, 4, 6, 8):
        V.append((f"4L SG gap{gap}", X.Geometry(X.topo_sg(gap), **base), {"topo": "SG", "gap": gap}))
    for ws in (2, 4, 6, 8, 10):
        for gap in (1, 2, 3, 4):
            if ws + 2 * gap <= 16:
                V.append((f"4L GSG ws{ws} gap{gap}", X.Geometry(X.topo_gsg(ws, gap), **base),
                          {"topo": "GSG", "ws": ws, "gap": gap}))
    for wg in (4, 6):
        V.append((f"4L SGS wg{wg} gap2", X.Geometry(X.topo_sgs(wg, 2), **base), {"topo": "SGS", "ws": wg, "gap": 2}))
    for gap in (1, 2, 4):
        V.append((f"4L versetzt gap{gap}", X.Geometry(X.topo_offset(gap), **base), {"topo": "versetzt", "gap": gap}))
        V.append((f"4L Kreuz gap{gap}", X.Geometry(X.topo_cross(gap), **base), {"topo": "Kreuz", "gap": gap}))
    for n in (4, 6, 8):
        V.append((f"4L IDE n{n} gap1", X.Geometry(X.topo_ide(n, 1.0), **base), {"topo": "IDE", "n": n, "gap": 1}))
    # Isolationsdicke (Stackups) und Coating fuer GSG ws6 gap2 und SG gap2
    for st in P.STACK_4L:
        V.append((f"4L GSG ws6 gap2 stack {st}", X.Geometry(X.topo_gsg(6, 2), layers=4, stack=st),
                  {"topo": "GSG", "ws": 6, "gap": 2, "stack": st}))
    for tc in (0.05, 0.1):
        V.append((f"4L GSG ws6 gap2 coat{tc}", X.Geometry(X.topo_gsg(6, 2), layers=4, t_coat=tc),
                  {"topo": "GSG", "ws": 6, "gap": 2, "coat": tc}))
    V.append(("4L GSG ws6 gap2 mask0.02", X.Geometry(X.topo_gsg(6, 2), layers=4, t_mask=0.02),
              {"topo": "GSG", "ws": 6, "gap": 2, "mask": 0.02}))
    for e in (1.5, 2.0):
        V.append((f"4L GSG ws6 gap2 rand{e}", X.Geometry(X.topo_gsg(6, 2, e=e), layers=4),
                  {"topo": "GSG", "ws": 6, "gap": 2, "edge": e}))
    # 2 Lagen + Coating (Elektroden aussen unter Lack 15 um auf Cu + Coating)
    for tc in (0.02, 0.05, 0.1):
        V.append((f"2L GSG ws6 gap2 coat{tc}", X.Geometry(X.topo_gsg(6, 2, layers=("F", "B")), layers=2,
                                                       t_mask=P.T_MASK_CU, t_coat=tc),
                  {"topo": "GSG", "ws": 6, "gap": 2, "coat": tc, "layers": 2}))
        V.append((f"2L SG gap2 coat{tc}", X.Geometry(X.topo_sg(2, layers=("F", "B")), layers=2,
                                                  t_mask=P.T_MASK_CU, t_coat=tc),
                  {"topo": "SG", "gap": 2, "coat": tc, "layers": 2}))
    return V


SALT_VARIANTS = [
    ("4L GSG ws6 gap2", X.Geometry(X.topo_gsg(6, 2), layers=4)),
    ("4L GSG ws6 gap2 7628C", X.Geometry(X.topo_gsg(6, 2), layers=4, stack="7628C")),
    ("4L GSG ws6 gap2 1080", X.Geometry(X.topo_gsg(6, 2), layers=4, stack="1080")),
    ("4L GSG ws4 gap4", X.Geometry(X.topo_gsg(4, 4), layers=4)),
    ("4L SG gap2", X.Geometry(X.topo_sg(2), layers=4)),
    ("4L IDE n6 gap1", X.Geometry(X.topo_ide(6, 1.0), layers=4)),
    ("2L GSG ws6 gap2 coat0.05", X.Geometry(X.topo_gsg(6, 2, layers=("F", "B")), layers=2,
                                             t_mask=P.T_MASK_CU, t_coat=0.05)),
]


def write_csv(path, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w") as f:
        f.write(";".join(keys) + "\n")
        for r in rows:
            f.write(";".join(f"{r.get(k, ''):.6g}" if isinstance(r.get(k), float) else str(r.get(k, ""))
                             for k in keys) + "\n")


def main():
    os.makedirs(RES, exist_ok=True)
    os.makedirs(PLT, exist_ok=True)
    V = variants()
    with mp.Pool(min(16, os.cpu_count())) as pool:
        if "--salt-only" not in sys.argv:
            rows = pool.map(evaluate, V, chunksize=1)
            write_csv(os.path.join(RES, "study2d.csv"), rows)
        if "--no-salt" not in sys.argv:
            srows = sum(pool.map(salt_eval, SALT_VARIANTS, chunksize=1), [])
            write_csv(os.path.join(RES, "study2d_salt.csv"), srows)
    if "--salt-only" in sys.argv:
        return
    for r in rows:
        print(f"{r['name']:34s} Cair {r['C_air']:7.1f} Cdry {r['C_dry']:7.1f} Cwet {r['C_wet']:7.1f} "
              f"span {r['span']:7.1f} ratio {r['ratio']:5.2f} d90w {r['d90_wet']:5.2f} "
              f"fr4 {r['fr4_moist']:5.2f}% gap01 {r.get('gap01', 0):6.1f}% gap05 {r.get('gap05', 0):6.1f}%")


if __name__ == "__main__":
    main()
