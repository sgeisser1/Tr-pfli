"""Skizze der empfohlenen Elektrodengeometrie (Vorgabe Layout Welle 2).

Aufruf: .venv/bin/python simulation/field/sketch.py  -> plots/sketch_electrodes.png
Masse aus probe3d.GEOS["sg"] (identisch mit der 3D-Kontrolle).
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

sys.path.insert(0, os.path.dirname(__file__))
import params as P  # noqa: E402
from probe3d import GEOS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    g = GEOS["sg"]
    W2 = P.W_PROBE / 2
    xe = W2 - g.edge
    zc = g.L - (W2 - g.x_tip)
    xs = (-xe - g.gap / 2) / 2
    gcol, scol = "#7f7f7f", "#d95f02"
    fig = plt.figure(figsize=(14, 10))
    ax = fig.add_axes([0.03, 0.04, 0.50, 0.92])
    out = [(-W2, -12), (W2, -12), (W2, zc), (g.x_tip, g.L), (-g.x_tip, g.L), (-W2, zc)]
    ax.add_patch(Polygon(out, closed=True, fc="#e8f0d8", ec="k", lw=1.2))
    # Kupfer-Sperrrand (Kontur - edge)
    d = g.edge * 2 ** 0.5 - g.edge  # Versatz der 45-Grad-Linie
    ax.add_patch(Polygon([(-xe, -12), (xe, -12), (xe, zc + d), (g.x_tip - 0.41, g.L - g.edge), (-g.x_tip + 0.41, g.L - g.edge),
                          (-xe, zc + d)], closed=True, fc="none", ec="r", lw=0.7, ls="--"))
    # Guard (GND) mit Kanal fuer S-Zuleitung
    ax.add_patch(Rectangle((-xe, -12), (xs - g.wf / 2 - g.cf) + xe, g.z_guard + 12, fc=gcol, alpha=.85))
    ax.add_patch(Rectangle((xs + g.wf / 2 + g.cf, -12), xe - xs - g.wf / 2 - g.cf, g.z_guard + 12, fc=gcol, alpha=.85))
    ax.add_patch(Rectangle((g.gap / 2, g.z_guard), xe - g.gap / 2, g.z_g1 - g.z_guard, fc=gcol, alpha=.85))
    if g.g_bar:
        ax.add_patch(Rectangle((-xe, g.z_s1 + g.gap), 2 * xe, g.w_bar, fc=gcol, alpha=.85))
    ax.add_patch(Rectangle((-xe, g.z_s0), xe - g.gap / 2, g.z_s1 - g.z_s0, fc=scol, alpha=.9))
    ax.add_patch(Rectangle((xs - g.wf / 2, -12), g.wf, g.z_s0 + 12, fc=scol, alpha=.95))
    # Bezugslinien
    ax.axhline(0, color="b", lw=1.5)
    ax.text(W2 + 0.6, 0, "Dichtlinie z = 0 (Kragen-Unterkante)", va="center", color="b", fontsize=8)
    ax.axhline(5, color="b", lw=1, ls="--")
    ax.text(W2 + 0.6, 5.2, "max. Stecktiefe z = 5 (Silk-Markierung L1+L4)", va="center", color="b", fontsize=8)
    ax.add_patch(Rectangle((-W2 - 1.2, 10), 0.6, 80, color="g", alpha=.5))
    ax.text(-W2 - 2.0, 50, "Messvolumen REQ-MES-08: z = 10...90", ha="right", va="center", color="g", fontsize=8, rotation=90)
    ax.text(W2 + 0.6, -7, "Kopf (z < 0): Elektronik, GND,\nVias und Aussenkupfer erlaubt;\nL2-S/L3-S und G per Via nur hier verbinden", fontsize=8, va="center")
    ax.text(W2 + 0.6, 45, "Sondenbereich z > 0:\nL1/L4 kupferfrei, keine Vias,\nLoetstopplack beidseitig,\nKanten versiegelt (REQ-MECH-07)", fontsize=8, va="center")

    def dim_h(x0, x1, z, txt, dz=-1.0):
        ax.annotate("", (x0, z), (x1, z), arrowprops=dict(arrowstyle="<->", lw=0.7))
        ax.text((x0 + x1) / 2, z + dz, txt, ha="center", fontsize=7.5)

    def dim_v(x, z0, z1, txt, col="k"):
        ax.annotate("", (x, z0), (x, z1), arrowprops=dict(arrowstyle="<->", lw=0.7, color=col))
        ax.text(x + 0.25, (z0 + z1) / 2, txt, va="center", fontsize=7.5, rotation=90, color=col)
    dim_h(-xe, -g.gap / 2, 30, f"S {xe - g.gap/2:g}")
    dim_h(-g.gap / 2, g.gap / 2, 40, f"{g.gap:g}")
    dim_h(g.gap / 2, xe, 30, f"G {xe - g.gap/2:g}")
    dim_h(xe, W2, 70, f"{g.edge:g}")
    dim_h(-W2, W2, -14, f"Sondenbreite {P.W_PROBE:g} (D-010)", dz=-0.8)
    dim_v(-W2 - 6.0, 0, g.L, f"L = {g.L:g} (5 frei + 100 im Substrat)")
    dim_v(4.0, -12, g.z_guard, f"Guard bis {g.z_guard:g}", "w")
    dim_v(-6.5, g.z_s0, g.z_s1, f"S: z = {g.z_s0:g} ... {g.z_s1:g}", "k")
    dim_v(6.0, g.z_guard, g.z_g1, f"G: bis z = {g.z_g1:g}", "w")
    ax.text(0, g.z_s1 + g.gap + g.w_bar + 1.2, f"G-Steg z = {g.z_s1+g.gap:g}...{g.z_s1+g.gap+g.w_bar:g}", ha="center", fontsize=7)
    ax.text(xs - 1, 3, f"S-Zuleitung\n{g.wf:g} / Abst. {g.cf:g}", ha="center", fontsize=6.5, color="w")
    ax.text(0, zc + 3.5, "Spitze 45 deg,\nStumpf 4 mm\n(ANNAHME Mechanik)", ha="center", fontsize=7)
    ax.set_xlim(-W2 - 10, W2 + 25); ax.set_ylim(g.L + 4, -17)
    ax.set_aspect("equal"); ax.set_xlabel("x [mm]"); ax.set_ylabel("z = Tiefe unter der Dichtlinie [mm]")
    ax.set_title("fluidi Sonde: Elektroden S/G koplanar, auf L2 und L3 deckungsgleich (Draufsicht, mm)", fontsize=10)
    ax.legend(handles=[Rectangle((0, 0), 1, 1, fc=scol), Rectangle((0, 0), 1, 1, fc=gcol),
                       Rectangle((0, 0), 1, 1, fc="none", ec="r", ls="--")],
              labels=["S (Oszillator-Eingang)", "G (GND: Guard, Gegenelektrode, Steg)", f"Kupfer-Sperrrand {g.edge:g} mm"],
              loc="lower left", bbox_to_anchor=(0.62, 0.02), fontsize=7.5)
    # Querschnitt
    tpp, tcore, er = P.STACK_4L[P.STACK_DEFAULT]
    hb = 2 * tpp + tcore + 2 * P.T_CU_IN
    ax2 = fig.add_axes([0.58, 0.60, 0.40, 0.34])
    sc = 3.0
    ax2.add_patch(Rectangle((-W2, -hb / 2 * sc), 2 * W2, hb * sc, fc="#e8f0d8", ec="k"))
    for ys in (1, -1):
        ax2.add_patch(Rectangle((-W2, (hb / 2 if ys > 0 else -hb / 2 - 0.03 * 4) * sc / (1 if ys > 0 else 1)), 2 * W2,
                                0.03 * 4 * sc, fc="#4daf4a", alpha=.6))
        y = ys * (hb / 2 - tpp) * sc
        ax2.plot([-xe, -g.gap / 2], [y, y], color=scol, lw=4)
        ax2.plot([g.gap / 2, xe], [y, y], color=gcol, lw=4)
    ax2.text(W2 + 0.4, (hb / 2 - tpp / 2) * sc, f"Prepreg 7628 {tpp:.2f} mm, Er {er}", fontsize=7, va="center")
    ax2.text(W2 + 0.4, 0, f"Kern {tcore} mm", fontsize=7, va="center")
    ax2.text(W2 + 0.4, (hb / 2 - tpp) * sc - 0.3, "L2", fontsize=7, va="center")
    ax2.text(W2 + 0.4, -(hb / 2 - tpp) * sc + 0.3, "L3", fontsize=7, va="center")
    ax2.text(-W2, hb / 2 * sc + 0.7, f"Loetstopplack {P.T_MASK_LAM*1000:.0f} um, Er {P.ER_MASK}; L1/L4 ohne Kupfer", fontsize=7)
    ax2.text(-xe, -hb / 2 * sc - 1.2, f"S {xe-g.gap/2:g}", fontsize=7, color=scol)
    ax2.text(g.gap / 2, -hb / 2 * sc - 1.2, f"G {xe-g.gap/2:g}", fontsize=7)
    ax2.set_xlim(-W2 - 1, W2 + 11); ax2.set_ylim(-4, 4); ax2.set_aspect("equal")
    ax2.set_title(f"Querschnitt z = {g.z_s0:g}...{g.z_s1:g} (Dicke 3-fach, Lack 12-fach ueberhoeht)", fontsize=9)
    ax2.set_xlabel("x [mm]"); ax2.set_yticks([])
    ax3 = fig.add_axes([0.58, 0.04, 0.40, 0.50]); ax3.axis("off")
    txt = (
        "Layoutvorgaben fuer Welle 2 (Masse mm, z ab Dichtlinie)\n\n"
        f"S  : x = -{xe:g} ... -{g.gap/2:g}, z = {g.z_s0:g} ... {g.z_s1:g}\n"
        f"G  : x = +{g.gap/2:g} ... +{xe:g}, z = Kopf ... {g.z_g1:g}\n"
        f"Steg G: x = -{xe:g} ... +{xe:g}, z = {g.z_s1+g.gap:g} ... {g.z_s1+g.gap+g.w_bar:g}\n"
        f"Guard G: volle Breite, Kopf ... z = {g.z_guard:g}\n"
        f"S-Zuleitung: {g.wf:g} breit bei x = {xs:g}, Abstand {g.cf:g}\n"
        "  nur auf L2; auf L3 unter der Zuleitung GND\n"
        "  (3D-Modell spiegelt sie auf L3: konservativ)\n"
        "Alle Elektroden auf L2 UND L3 deckungsgleich;\n"
        "  Verbindung L2/L3 nur im Kopf (z < -3) per Via\n"
        f"Kupfer >= {g.edge:g} zur Kontur (REQ-MECH-06 >= 1.0\n"
        "  + Fraestoleranz), auch entlang der Spitze\n"
        "z = 0 ... 2: Dichtstreifen ohne Vias (M-03)\n"
        "z > 0: keine Vias, L1/L4 ohne Kupfer, Lack beidseitig\n"
        "Silk: Stecktiefe z = 5, Revision, Logo (Kopf)\n"
        "Stackup JLC04161H-7628 (Standard), 1.6 mm\n"
        "Cpar Leitung im Kopf klein halten (< 5 pF)"
    )
    ax3.text(0, 1, txt, va="top", fontsize=8.6, family="monospace")
    fig.savefig(os.path.join(HERE, "plots", "sketch_electrodes.png"), dpi=140)


if __name__ == "__main__":
    main()
