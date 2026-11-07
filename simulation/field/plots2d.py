"""Diagramme zur 2D-Studie. Aufruf: .venv/bin/python simulation/field/plots2d.py (nach study2d.py)."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import params as P  # noqa: E402
import xsec2d as X  # noqa: E402
from study2d import penetration  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PLT = os.path.join(HERE, "plots")


def load():
    rows = []
    with open(os.path.join(HERE, "results", "study2d.csv")) as f:
        keys = f.readline().strip().split(";")
        for line in f:
            r = dict(zip(keys, line.rstrip("\n").split(";")))
            for k, v in r.items():
                if k in ("name", "stack", "topo"):
                    continue
                try:
                    r[k] = float(v)
                except ValueError:
                    pass
            rows.append(r)
    return rows


def main():
    rows = load()
    # A: Topologievergleich ueber den Abstand
    fig, ax = plt.subplots(2, 2, figsize=(12, 8))
    groups = {
        "SG koplanar": [r for r in rows if str(r["name"]).startswith("4L SG gap")],
        "GSG ws 6": [r for r in rows if str(r["name"]).startswith("4L GSG ws6 gap") and "stack" not in r["name"]
                     and "coat" not in r["name"] and "mask" not in r["name"] and "rand" not in r["name"]],
        "GSG ws 4": [r for r in rows if str(r["name"]).startswith("4L GSG ws4 gap")],
        "versetzt L2/L3": [r for r in rows if str(r["name"]).startswith("4L versetzt")],
    }
    for lab, rr in groups.items():
        rr = sorted(rr, key=lambda r: r["gap"])
        gx = [r["gap"] for r in rr]
        ax[0, 0].plot(gx, [r["span"] for r in rr], "o-", label=lab)
        ax[0, 1].plot(gx, [r["d90_wet"] for r in rr], "o-", label=lab)
        ax[1, 0].plot(gx, [r["fr4_moist"] for r in rr], "o-", label=lab)
        ax[1, 1].plot(gx, [-r["gap01"] for r in rr], "o-", label=lab)
    ax[0, 0].set_ylabel("Spanne C'(eps 25) - C'(eps 4) [pF/m]")
    ax[0, 1].set_ylabel("d90 nass: 90 % der Empfindlichkeit innerhalb [mm]")
    ax[1, 0].set_ylabel("FR4 Er +10 % (Feuchtesaettigung): Drift [% Spanne]")
    ax[1, 0].axhline(3, color="r", ls=":", label="REQ-MES-06 (3 %, gesamt)")
    ax[1, 1].set_ylabel("Spannenverlust bei 0.1 mm Luftspalt [%]")
    for a in ax.flat:
        a.set_xlabel("Abstand S-G [mm]"); a.grid(alpha=.3); a.legend(fontsize=8)
    fig.suptitle("2D-Querschnitt, 4 Lagen JLC 7628 (Prepreg 0.21 mm, Lack 30 um), Breite 20 mm, Rand 1 mm")
    fig.tight_layout(); fig.savefig(os.path.join(PLT, "2d_topologien.png"), dpi=130)
    # B: Isolationsdicke (Stackup) und 2L/4L
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    st = [r for r in rows if str(r["name"]).startswith("4L SG gap2 stack")]
    st += [dict(r, stack=P.STACK_DEFAULT) for r in rows if r["name"] == "4L SG gap2"]
    t = [P.STACK_4L[r["stack"]][0] for r in st]
    o = np.argsort(t)
    ax[0].plot(np.array(t)[o], np.array([r["span"] for r in st])[o], "o-", label="Spanne [pF/m]")
    ax[0].plot(np.array(t)[o], np.array([r["C_air"] for r in st])[o], "s-", label="C' Luft [pF/m]")
    ax2 = ax[0].twinx()
    ax2.plot(np.array(t)[o], np.array([r["fr4_moist"] for r in st])[o], "r^--", label="FR4-Drift [% Spanne]")
    ax2.set_ylabel("FR4-Drift bei Er +10 % [% Spanne]", color="r")
    ax[0].set_xlabel("Isolationsdicke Prepreg L1-L2 [mm] (+30 um Lack)")
    ax[0].set_title("SG gap2: Einfluss der Isolationsdicke (JLC-Stackups 1.6 mm)")
    ax[0].legend(loc="upper center", fontsize=8); ax[0].grid(alpha=.3)
    for i, s in enumerate(np.array([r["stack"] for r in st])[o]):
        ax[0].annotate(s.split(" ")[0], (np.array(t)[o][i], np.array([r["span"] for r in st])[o][i]), fontsize=7)
    comp = [r for r in rows if str(r["name"]) in ("4L SG gap2", "4L GSG ws6 gap2", "4L GSG ws6 gap2 coat0.05",
                                                  "2L SG gap2 coat0.02", "2L SG gap2 coat0.05", "2L SG gap2 coat0.1",
                                                  "2L GSG ws6 gap2 coat0.02", "2L GSG ws6 gap2 coat0.05", "2L GSG ws6 gap2 coat0.1")]
    x = np.arange(len(comp))
    ax[1].bar(x - 0.2, [r["span"] for r in comp], 0.4, label="Spanne [pF/m]")
    ax[1].bar(x + 0.2, [r["C_air"] for r in comp], 0.4, label="C' Luft [pF/m]")
    ax[1].set_xticks(x); ax[1].set_xticklabels([r["name"] for r in comp], rotation=35, ha="right", fontsize=7)
    ax3 = ax[1].twinx()
    ax3.plot(x, [r["fr4_moist"] + r.get("lack_moist", 0) for r in comp], "r^", label="Drift FR4+Lack [% Spanne]")
    ax3.set_ylabel("Drift FR4 (+10 %) + Lack (+10 %) [% Spanne]", color="r")
    ax[1].legend(fontsize=8, loc="upper left"); ax[1].set_title("4 Lagen innen vs. 2 Lagen aussen + Coating")
    fig.tight_layout(); fig.savefig(os.path.join(PLT, "2d_isolation_2L4L.png"), dpi=130)
    # C: Feldbilder + Eindringkurven
    fig, ax = plt.subplots(3, 1, figsize=(11, 11), gridspec_kw={"height_ratios": [1, 1, 1.1]})
    for i, (lab, el) in enumerate((("SG koplanar gap 2 mm (Empfehlung)", X.topo_sg(2, e=1.25)),
                                   ("GSG ws 6 gap 2 mm", X.topo_gsg(6, 2, e=1.25)))):
        m = X.Model(X.Geometry(el))
        c, phi = m.cap(m.default_eps(P.EPS_WET))
        e = m.element_energy(phi)
        area = m.mesh.p[:, m.mesh.t]
        a = 0.5 * np.abs((area[0, 1] - area[0, 0]) * (area[1, 2] - area[1, 0]) - (area[0, 2] - area[0, 0]) * (area[1, 1] - area[1, 0]))
        dens = e / a
        tri = mtri.Triangulation(m.mesh.p[0], m.mesh.p[1], m.mesh.t.T)
        pc = ax[i].tripcolor(tri, facecolors=np.log10(dens + 1e-6), cmap="magma", vmin=-3, vmax=2)
        ax[i].tricontour(mtri.Triangulation(m.mesh.p[0], m.mesh.p[1], m.mesh.t[:3].T), phi[:m.mesh.p.shape[1]],
                         levels=np.linspace(0.05, 0.95, 10), colors="c", linewidths=0.5)
        a_, b_ = m.g.outer_halfsizes()
        ax[i].add_patch(plt.Rectangle((-a_, -b_), 2 * a_, 2 * b_, fill=False, ec="w", lw=0.8))
        for el_ in el:
            y = m.g.layer_y(el_.layer)
            ax[i].plot([el_.x0, el_.x1], [y, y], color="orange" if el_.net == "S" else "lightgray", lw=2)
        ax[i].set_xlim(-22, 22); ax[i].set_ylim(-9, 9); ax[i].set_aspect("equal")
        ax[i].set_title(f"{lab}: |E|^2 (log10, rel.) und Aequipotentiallinien, Substrat eps 25; C' = {c:.0f} pF/m", fontsize=9)
        plt.colorbar(pc, ax=ax[i], shrink=0.8)
        for es, ls in ((P.EPS_DRY, "--"), (P.EPS_WET, "-")):
            c2, phi2 = m.cap(m.default_eps(es))
            d50, d90, (d, cs) = penetration(m, phi2, es)
            ax[2].plot(d, cs * 100, ls, label=f"{lab}, eps {es:g} (d50 {d50:.1f}, d90 {d90:.1f} mm)")
    ax[2].set_xlim(0, 20); ax[2].set_xlabel("Abstand von der Sondenoberflaeche [mm]")
    ax[2].set_ylabel("kumulierter Anteil dC/d eps_Substrat [%]"); ax[2].grid(alpha=.3); ax[2].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(os.path.join(PLT, "2d_feldbild_eindringtiefe.png"), dpi=120)


if __name__ == "__main__":
    main()
