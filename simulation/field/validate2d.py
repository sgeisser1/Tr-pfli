"""Validierung 2D-Loeser: koplanare Streifen in homogenem Medium gegen konforme Abbildung,
C' = eps0 K(k')/K(k), k = s/(s+2w) (Coplanar Strips). Netzkonvergenz und Topfradius.
Aufruf: .venv/bin/python simulation/field/validate2d.py
"""
import math, time, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from scipy.special import ellipk
import xsec2d as X
import params as P

w, s = 8.5, 1.0
k = s / (s + 2 * w)
c_ana = P.EPS0 * ellipk(1 - k**2) / ellipk(k**2) * 1e12
print(f"analytisch CPS w={w} s={s}: C' = {c_ana:.3f} pF/m")
# Studien-Netz (Standardwerte xsec2d.Geometry) und feinere Netze; R = 200 mm ~ unendlich
for r_dom, hmin, hel, dist in [(50, 0.005, 0.06, 10), (200, 0.005, 0.06, 10), (200, 0.005, 0.06, 60),
                               (200, 0.002, 0.02, 60)]:
    el = [X.Electrode("F", -s/2 - w, -s/2, "S"), X.Electrode("F", s/2, s/2 + w, "G")]
    g = X.Geometry(el, layers=2, t_mask=0, r_dom=r_dom, h_min=hmin, h_el=hel, h_max=3.0 if dist == 10 else r_dom / 12,
                   dist_el=dist, dist_surf=dist)
    t0 = time.time()
    m = X.Model(g)
    c, phi = m.cap({r: 1.0 for r in m.K})
    print(f"R={r_dom:4.0f} hmin={hmin} hel={hel} dist={dist}: C'={c:.3f} pF/m  Abw {100*(c/c_ana-1):+.2f} %  "
          f"ndof={m.ndof} t={time.time()-t0:.1f}s")
