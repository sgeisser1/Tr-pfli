"""Netzkonvergenz 3D (Geometrie sg, h = 1.4 / 1.0 / 0.8) mit Richardson-Extrapolation.
Aufruf: .venv/bin/python simulation/field/conv3d.py -> results/probe3d_convergence.json"""
import json
import os

from scipy.optimize import brentq

HERE = os.path.dirname(os.path.abspath(__file__))
H = (1.4, 1.0, 0.8)
d = {h: json.load(open(os.path.join(HERE, "results", f"probe3d_sg_h{h:g}.json")))["C_pF"] for h in H}
out = {}
for k in ("air", "dry", "wet", "water", "fill010.0", "fill090.0"):
    c = [d[h][k] for h in H]
    r = (c[0] - c[1]) / (c[1] - c[2])
    f = lambda p: (H[0] ** p - H[1] ** p) / (H[1] ** p - H[2] ** p) - r
    p = brentq(f, 0.3, 5.0)
    a = (c[1] - c[2]) / (H[1] ** p - H[2] ** p)
    c0 = c[2] - a * H[2] ** p
    out[k] = {"h1.4": c[0], "h1.0": c[1], "h0.8": c[2], "p": p, "C_extrap": c0, "err_h1.0_pct": 100 * (c[1] / c0 - 1)}
    print(f"{k:10s} {c[0]:7.3f} {c[1]:7.3f} {c[2]:7.3f}  p={p:4.2f}  h->0: {c0:7.3f}  Fehler h=1.0: {out[k]['err_h1.0_pct']:+.1f} %")
e = {k: v["C_extrap"] for k, v in out.items()}
print("REQ-MES-08 extrapoliert:", (e["fill010.0"] - e["fill090.0"]) / (e["wet"] - e["air"]))
json.dump(out, open(os.path.join(HERE, "results", "probe3d_convergence.json"), "w"), indent=1)

# Ersatzschaltbild an die extrapolierten Werte (Luft/trocken/nass/Wasser) -> Eingang SPICE
import numpy as np  # noqa: E402
from scipy.optimize import least_squares  # noqa: E402
import sys  # noqa: E402
sys.path.insert(0, HERE)
import params as P  # noqa: E402
pts = [(1.0, e["air"]), (P.EPS_DRY, e["dry"]), (P.EPS_WET, e["wet"]), (P.EPS_WATER, e["water"])]
ee = np.array([q[0] for q in pts]); cc = np.array([q[1] for q in pts])
mod = lambda q, x: np.exp(q[0]) + np.exp(q[1]) * np.exp(q[2]) * x / (np.exp(q[1]) + np.exp(q[2]) * x)
sol = least_squares(lambda q: (mod(q, ee) - cc) / cc, np.log([7.0, 100.0, 1.7]))
C0, Ci, Cg = np.exp(sol.x)
lump = {"C0_pF": C0, "Ci_pF": Ci, "Cg_pF": Cg, "fit_max_rel": float(np.max(np.abs(sol.fun))),
        "tag": "sg, Richardson h->0 (h 1.4/1.0/0.8)", "C_air": e["air"], "C_dry": e["dry"], "C_wet": e["wet"],
        "C_water": e["water"]}
print("Ersatzschaltbild (extrapoliert):", {k: round(v, 3) if isinstance(v, float) else v for k, v in lump.items()})
json.dump(lump, open(os.path.join(HERE, "results", "probe_lumped_3d_extrap.json"), "w"), indent=1)
