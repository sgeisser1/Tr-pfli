"""Auswertung 3D (Elmer): Messvolumen REQ-MES-08, Fuellstandskurve, Ersatzschaltbild Gesamtsonde.

Aufruf: .venv/bin/python simulation/field/probe3d_post.py results/probe3d_<tag>.json [weitere ...]
Ausgabe: plots/3d_fill_<tag>.png, results/probe_lumped_3d.json (aus der ersten Datei = Hauptvariante)
"""
import json
import os
import sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(__file__))
import params as P  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def lumped_fit(C):
    """C(eps) = C0 + Ci*Cg*eps/(Ci + Cg*eps) an Luft/trocken/eps10/nass/Wasser (alle bis Markierung z = 5)."""
    pts = [(1.0, C["air"]), (P.EPS_DRY, C["dry"]), (10.0, C["e10"]), (P.EPS_WET, C["wet"]), (P.EPS_WATER, C["water"])]
    e = np.array([p[0] for p in pts]); c = np.array([p[1] for p in pts])

    def model(q, e):
        C0, Ci, Cg = np.exp(q)
        return C0 + Ci * Cg * e / (Ci + Cg * e)
    q0 = np.log([0.6 * C["air"], 10 * (C["water"] - C["air"]), (C["dry"] - C["air"]) / 3])
    sol = least_squares(lambda q: (model(q, e) - c) / c, q0)
    C0, Ci, Cg = np.exp(sol.x)
    return {"C0_pF": C0, "Ci_pF": Ci, "Cg_pF": Cg, "fit_max_rel": float(np.max(np.abs(sol.fun)))}


def analyse(path):
    d = json.load(open(path))
    C = d["C_pF"]
    tag = os.path.basename(path)[len("probe3d_"):-5]
    out = {"tag": tag, "ntet": d["mesh"]["ntet"], "nnode": d["mesh"]["nnode"]}
    for k in ("air", "dry", "e10", "wet", "water", "wet_flood"):
        out["C_" + k] = C.get(k)
    out["span"] = C["wet"] - C["dry"]
    fills = sorted((float(k[4:]), v) for k, v in C.items() if k.startswith("fill"))
    out["fill"] = fills
    z = np.array([f[0] for f in fills] + [d["geo"]["z_bot"]])
    cz = np.array([f[1] for f in fills] + [C["air"]])
    cf = dict(zip(np.round(z, 3), cz))
    tot = cf[5.0] - C["air"]
    out["mes08_fill"] = (cf[10.0] - cf[90.0]) / tot
    out["share_5_10"] = (cf[5.0] - cf[10.0]) / tot
    out["share_90_bot"] = (cf[90.0] - C["air"]) / tot
    if "wet10_90_dryrest" in C:
        out["mes08_mix"] = (C["wet10_90_dryrest"] - C["dry"]) / (C["wet"] - C["dry"])
    if "air_fr4wet" in C:
        span = C["wet"] - C["dry"]
        out["fr4_drift_air_pct"] = 100 * (C["air_fr4wet"] - C["air"]) / span
        out["fr4_drift_water_pct"] = 100 * (C["water_fr4wet"] - C["water"]) / span
    if "wet_flood" in C:
        out["flood_pct"] = 100 * (C["wet_flood"] - C["wet"]) / (C["wet"] - C["dry"])
    out["lumped"] = lumped_fit(C)
    return out, d


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    res = []
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.5))
    for i, p in enumerate(sys.argv[1:]):
        o, d = analyse(p)
        res.append(o)
        z = [f[0] for f in o["fill"]]
        c = [f[1] for f in o["fill"]]
        tot = o["fill"][0][1] - o["C_air"]
        ax[0].plot(z, c, "o-", ms=3, label=o["tag"])
        # Anteil je 5-mm-Scheibe an der Gesamtaenderung
        dz = np.diff(c + [o["C_air"]]) * -1 / tot * 100
        ax[1].step(z, dz, where="post", label=o["tag"])
        print(json.dumps({k: v for k, v in o.items() if k != "fill"}, indent=None, default=float))
        if i == 0:
            json.dump({**o["lumped"], "tag": o["tag"], "C_air": o["C_air"], "C_dry": o["C_dry"],
                       "C_wet": o["C_wet"], "C_water": o["C_water"]},
                      open(os.path.join(HERE, "results", "probe_lumped_3d.json"), "w"), indent=1)
    for a in ax:
        a.axvspan(10, 90, color="green", alpha=.08)
        a.set_xlabel("Fuellhoehe = Tiefe der Substratoberflaeche unter der Dichtlinie [mm]")
        a.grid(alpha=.3)
    ax[0].set_ylabel("C Sonde [pF] (nasses Substrat eps 25 unterhalb der Fuellhoehe)")
    ax[1].set_ylabel("Anteil an Delta C je 5-mm-Scheibe [%]")
    ax[0].legend(fontsize=7); ax[1].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "plots", "3d_fill.png"), dpi=130)
    json.dump(res, open(os.path.join(HERE, "results", "probe3d_summary.json"), "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
