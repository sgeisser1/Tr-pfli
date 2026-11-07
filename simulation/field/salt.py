"""Leitfaehigkeit/Salz (REQ-MES-11): Auswertung der komplexen 2D-Rechnung und Ersatzschaltbild.

Eingang: results/study2d_salt.csv (study2d.py, komplexe FEM eps* = eps' - j sigma/(w eps0), EQS).
1. Feuchteindex-Fehler im Frequenzbereich: Index aus C_eff = Im(Y)/w, kalibriert mit Leitungswasser.
2. Ersatzschaltbild je Meter (Fit an alle eps/sigma/f-Punkte):
      Y = jw C0 + 1 / ( 1/(jw Ci) + 1/(sigma Kg + jw eps0 eps' Kg) )
   C0 = Grundkapazitaet (FR4/Luft, substratunabhaengig), Ci = Isolationskapazitaet (Prepreg+Lack, in Serie),
   Kg = Geometriefaktor des Substrats (Cs = eps0 eps' Kg, Gs = sigma Kg).
Aufruf: .venv/bin/python simulation/field/salt.py
Ausgabe: results/salt_index_2d.csv, results/lumped_fit.json, plots/2d_salt_*.png
"""
import json
import math
import os
import sys

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, os.path.dirname(__file__))
import params as P  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
PLT = os.path.join(HERE, "plots")


def load():
    rows = []
    with open(os.path.join(RES, "study2d_salt.csv")) as f:
        keys = f.readline().strip().split(";")
        for line in f:
            v = line.strip().split(";")
            r = dict(zip(keys, v))
            for k in ("eps", "f", "sigma", "G", "C"):
                r[k] = float(r[k])
            rows.append(r)
    return rows


def interp_c(rows, name, eps, f, sigma):
    pts = sorted((r["sigma"], r["C"], r["G"]) for r in rows
                 if r["name"] == name and r["eps"] == eps and r["f"] == f)
    s = np.array([p[0] for p in pts]); c = np.array([p[1] for p in pts]); g = np.array([p[2] for p in pts])
    return float(np.interp(sigma, s, c)), float(np.interp(sigma, s, g))


def lumped_y(p, eps, sig, f):
    C0, Ci, Kg = p
    w = 2 * math.pi * f
    ys = sig * Kg + 1j * w * P.EPS0 * eps * Kg
    return 1j * w * C0 + 1.0 / (1.0 / (1j * w * Ci) + 1.0 / ys)


def fit_lumped(rows, name, fmax=20e6):
    sel = [r for r in rows if r["name"] == name and r["f"] <= fmax]
    def res(lp):
        p = np.exp(lp)
        out = []
        for r in sel:
            w = 2 * math.pi * r["f"]
            y = lumped_y(p, r["eps"], r["sigma"], r["f"])
            ym = r["G"] + 1j * w * r["C"] * 1e-12
            out += [(y.real - ym.real) / abs(ym), (y.imag - ym.imag) / abs(ym)]
        return np.array(out)
    c_air = [r["C"] for r in sel if r["eps"] == 1.0][0] * 1e-12
    p0 = np.log([0.6 * c_air, 30 * c_air, 0.5 * c_air / P.EPS0])
    sol = least_squares(res, p0)
    p = np.exp(sol.x)
    r = res(sol.x)
    return p, float(np.sqrt(np.mean(r**2))), float(np.max(np.abs(r)))


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    rows = load()
    names = list(dict.fromkeys(r["name"] for r in rows))
    eps_w, eps_m = P.EPS_WET, 10.0
    out = []
    print("Feuchteindex-Fehler (Frequenzbereich, C_eff), kalibriert trocken (sigma=0) / nass Leitungswasser")
    for name in names:
        for f in (2e6, 4e6, 6e6, 10e6, 20e6, 70e6):
            c_dry, _ = interp_c(rows, name, P.EPS_DRY, f, 0.0)
            sb_tap = P.sigma_bulk(0.035, eps_w)
            c_wet, _ = interp_c(rows, name, eps_w, f, sb_tap)
            for case, sp in P.SIGMA_PORE_CASES.items():
                for eps in (eps_m, eps_w):
                    sb = P.sigma_bulk(sp, eps)
                    sb_tap_e = P.sigma_bulk(0.035, eps)
                    c, g = interp_c(rows, name, eps, f, sb)
                    c_t, _ = interp_c(rows, name, eps, f, sb_tap_e)
                    idx = 100 * (c - c_dry) / (c_wet - c_dry)
                    idx_t = 100 * (c_t - c_dry) / (c_wet - c_dry)
                    out.append({"name": name, "f_MHz": f / 1e6, "case": case, "eps": eps, "sigma_b": sb,
                                "index": idx, "index_tap": idx_t, "err_pp": idx - idx_t})
    with open(os.path.join(RES, "salt_index_2d.csv"), "w") as fh:
        keys = list(out[0])
        fh.write(";".join(keys) + "\n")
        for r in out:
            fh.write(";".join(f"{r[k]:.4g}" if isinstance(r[k], float) else str(r[k]) for k in keys) + "\n")
    for name in names:
        line = [f"{name:28s}"]
        for f in (2e6, 4e6, 6e6, 20e6, 70e6):
            e = [r["err_pp"] for r in out if r["name"] == name and r["f_MHz"] == f / 1e6 and r["eps"] == eps_w]
            line.append(f"{f/1e6:4.0f}MHz: " + "/".join(f"{x:+6.1f}" for x in e))
        print("  ".join(line))
    # Plot C_eff vs sigma (nass) fuer alle Varianten bei 4 MHz, und Hauptvariante ueber f
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for name in names:
        pts = sorted((r["sigma"], r["C"]) for r in rows if r["name"] == name and r["eps"] == eps_w and r["f"] == 4e6)
        c0 = pts[0][1]
        ax[0].semilogx([max(p[0], 3e-4) for p in pts], [p[1] / c0 for p in pts], "o-", ms=3, label=name)
    for case, sp in P.SIGMA_PORE_CASES.items():
        ax[0].axvline(P.sigma_bulk(sp, eps_w), color="gray", ls=":")
        ax[0].text(P.sigma_bulk(sp, eps_w), ax[0].get_ylim()[1] if False else 1.02, case.split(" (")[0], rotation=90,
                   fontsize=7, va="bottom")
    ax[0].set_xlabel("Bulk-Leitfaehigkeit sigma_b [S/m] (0 links als 3e-4 dargestellt)")
    ax[0].set_ylabel("C_eff(sigma) / C_eff(0), eps' = 25, f = 4 MHz")
    ax[0].grid(True, which="both", alpha=.3); ax[0].legend(fontsize=7)
    main_name = "4L SG gap2" if "4L SG gap2" in names else names[0]
    for f in (1e6, 2e6, 4e6, 6e6, 10e6, 20e6, 70e6):
        pts = sorted((r["sigma"], r["C"]) for r in rows if r["name"] == main_name and r["eps"] == eps_w and r["f"] == f)
        ax[1].semilogx([max(p[0], 3e-4) for p in pts], [p[1] for p in pts], "o-", ms=3, label=f"{f/1e6:g} MHz")
    ax[1].set_xlabel("sigma_b [S/m]"); ax[1].set_ylabel("C_eff' [pF/m]")
    ax[1].set_title(main_name + ", eps' = 25"); ax[1].grid(True, which="both", alpha=.3); ax[1].legend(fontsize=7)
    fig.tight_layout(); fig.savefig(os.path.join(PLT, "2d_salt_ceff.png"), dpi=130)
    # Ersatzschaltbild
    fits = {}
    for name in names:
        p, rms, mx = fit_lumped(rows, name)
        fits[name] = {"C0_pF_per_m": p[0] * 1e12, "Ci_pF_per_m": p[1] * 1e12, "Kg": p[2],
                      "Cg_pF_per_m_per_eps": P.EPS0 * p[2] * 1e12, "fit_rms_rel": rms, "fit_max_rel": mx}
        print(f"Fit {name:28s} C0 {p[0]*1e12:7.1f} pF/m  Ci {p[1]*1e12:8.1f} pF/m  eps0*Kg {P.EPS0*p[2]*1e12:6.2f} pF/m"
              f"  rms {100*rms:.1f} %  max {100*mx:.1f} %")
    json.dump(fits, open(os.path.join(RES, "lumped_fit.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
