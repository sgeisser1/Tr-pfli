"""Skizze der empfohlenen Elektrodengeometrie (Vorgabe Layout Welle 2).

Aufruf: .venv/bin/python simulation/field/sketch.py  -> plots/sketch_electrodes.png
Masse aus probe3d.GEOS["gsg"] (gleiche Geometrie wie die 3D-Kontrolle).
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
    g = GEOS["gsg"]
    W2 = P.W_PROBE / 2
    xe = W2 - g.edge
    zc = g.L - (W2 - g.x_tip)
    fig = plt.figure(figsize=(13, 9.5))
    ax = fig.add_axes([0.04, 0.05, 0.50, 0.90])
    # Kontur (Draufsicht, z nach unten)
    out = [(-W2, -12), (W2, -12), (W2, zc), (g.x_tip, g.L), (-g.x_tip, g.L), (-W2, zc)]
    ax.add_patch(Polygon(out, closed=True, fc="#e8f0d8", ec="k", lw=1.2))
    # Sperrzone Kupfer 1.25 mm zur Kontur
    ax.add_patch(Polygon([(-xe, -12), (xe, -12), (xe, zc + 0.3), (g.x_tip, g.L - 1.4), (-g.x_tip, g.L - 1.4), (-xe, zc + 0.3)],
                         closed=True, fc="none", ec="r", lw=0.6, ls="--"))
    # Guard (GND) mit Zuleitungskanal
    gcol, scol = "#7f7f7f", "#d95f02"
    ax.add_patch(Rectangle((g.wf / 2 + g.cf, -12), xe - g.wf / 2 - g.cf, g.z_guard + 12, fc=gcol, alpha=.8))
    ax.add_patch(Rectangle((-xe, -12), xe - g.wf / 2 - g.cf, g.z_guard + 12, fc=gcol, alpha=.8))
    for s in (-1, 1):
        x0 = g.ws / 2 + g.gap
        ax.add_patch(Rectangle((x0 if s > 0 else -xe, g.z_guard), xe - x0, g.z_g1 - g.z_guard, fc=gcol, alpha=.8))
    if g.g_bar:
        ax.add_patch(Rectangle((-xe, g.z_s1 + g.gap), 2 * xe, g.w_bar, fc=gcol, alpha=.8))
    ax.add_patch(Rectangle((-g.ws / 2, g.z_s0), g.ws, g.z_s1 - g.z_s0, fc=scol, alpha=.9))
    ax.add_patch(Rectangle((-g.wf / 2, -12), g.wf, g.z_s0 + 12, fc=scol, alpha=.9))
    # Linien
    ax.axhline(0, color="b", lw=1.5); ax.text(W2 + 0.5, 0, "Dichtlinie z = 0 (Kragen-Unterkante)", va="center", color="b", fontsize=8)
    ax.axhline(5, color="b", lw=1, ls="--"); ax.text(W2 + 0.5, 5, "max. Stecktiefe (Silk-Markierung)\nz = 5 mm", va="center", color="b", fontsize=8)
    ax.axhspan(10, 90, xmin=0.0, xmax=0.03, color="g", alpha=.4)
    ax.text(-W2 - 0.5, 50, "Messvolumen\nREQ-MES-08\nz = 10...90", ha="right", va="center", color="g", fontsize=8)
    ax.text(W2 + 0.5, -6, "Kopf: Elektronik, GND-Flaechen\n(Vias erlaubt, Aussenlagen Kupfer erlaubt)", fontsize=8, va="center")
    ax.text(W2 + 0.5, 50, "Sondenbereich z > 0:\nL1/L4 kupferfrei, keine Vias,\nLoetstopplack beidseitig", fontsize=8, va="center")
    # Bemassung
    def dim_h(x0, x1, z, txt, dz=-1.2):
        ax.annotate("", (x0, z), (x1, z), arrowprops=dict(arrowstyle="<->", lw=0.7))
        ax.text((x0 + x1) / 2, z + dz, txt, ha="center", fontsize=7.5)

    def dim_v(x, z0, z1, txt):
        ax.annotate("", (x, z0), (x, z1), arrowprops=dict(arrowstyle="<->", lw=0.7))
        ax.text(x + 0.3, (z0 + z1) / 2, txt, va="center", fontsize=7.5, rotation=90)
    dim_h(-g.ws / 2, g.ws / 2, 40, f"S {g.ws:g}")
    dim_h(g.ws / 2, g.ws / 2 + g.gap, 30, f"{g.gap:g}")
    dim_h(g.ws / 2 + g.gap, xe, 40, f"G {xe - g.ws/2 - g.gap:g}")
    dim_h(xe, W2, 60, f"{g.edge:g}")
    dim_h(-W2, W2, g.L + 3, f"Sondenbreite {P.W_PROBE:g}", dz=1.8)
    dim_v(-W2 - 2.5, 0, g.L, f"L = {g.L:g} (5 frei + 100 im Substrat)")
    dim_v(-1.5, 0, g.z_guard, f"Guard {g.z_guard:g}")
    dim_v(-1.8, g.z_s0, g.z_s1, f"S z = {g.z_s0:g} ... {g.z_s1:g}")
    dim_v(g.ws / 2 + g.gap + 1.0, g.z_guard, g.z_g1, f"G z bis {g.z_g1:g}")
    ax.text(0.8, g.z_s1 + g.gap + g.w_bar / 2, f"G-Steg {g.w_bar:g} (Abstand {g.gap:g})", fontsize=7, va="center")
    ax.text(0.5, -10, f"S-Zuleitung {g.wf:g} / Abstand {g.cf:g}\nnur L2; L3 darunter GND", fontsize=7, color=scol)
    ax.text(0, zc + 4, "Spitze 45 deg,\nabgestumpft 4 mm\n(ANNAHME Mechanik)", ha="center", fontsize=7)
    ax.set_xlim(-W2 - 9, W2 + 22); ax.set_ylim(g.L + 7, -14)
    ax.set_aspect("equal"); ax.set_xlabel("x [mm]"); ax.set_ylabel("z = Tiefe unter Dichtlinie [mm]")
    ax.set_title("fluidi Sonde - Elektroden auf L2 und L3 deckungsgleich (Draufsicht, Masse mm)", fontsize=10)
    ax.legend(handles=[Rectangle((0, 0), 1, 1, fc=scol), Rectangle((0, 0), 1, 1, fc=gcol),
                       Rectangle((0, 0), 1, 1, fc="none", ec="r", ls="--")],
              labels=["S (Oszillator-Eingang)", "G (GND, Guard + Randstreifen)", "Kupfer-Sperrrand 1.25 mm"],
              loc="lower right", fontsize=7)
    # Querschnitt
    tpp, tcore, er = P.STACK_4L[P.STACK_DEFAULT]
    hb = 2 * tpp + tcore + 2 * P.T_CU_IN
    ax2 = fig.add_axes([0.60, 0.55, 0.38, 0.38])
    sc = 3.0
    ax2.add_patch(Rectangle((-W2, -hb / 2 * sc), 2 * W2, hb * sc, fc="#e8f0d8", ec="k"))
    ax2.add_patch(Rectangle((-W2, hb / 2 * sc), 2 * W2, P.T_MASK_LAM * sc * 4, fc="#4daf4a", alpha=.6))
    ax2.add_patch(Rectangle((-W2, -hb / 2 * sc - P.T_MASK_LAM * sc * 4), 2 * W2, P.T_MASK_LAM * sc * 4, fc="#4daf4a", alpha=.6))
    for ys in (1, -1):
        y = ys * (hb / 2 - tpp) * sc
        ax2.plot([-g.ws / 2, g.ws / 2], [y, y], color=scol, lw=4)
        ax2.plot([g.ws / 2 + g.gap, xe], [y, y], color=gcol, lw=4)
        ax2.plot([-xe, -g.ws / 2 - g.gap], [y, y], color=gcol, lw=4)
    ax2.text(W2 + 0.4, (hb / 2 - tpp / 2) * sc, f"Prepreg 7628 {tpp:.3f} mm, Er {er}", fontsize=7, va="center")
    ax2.text(W2 + 0.4, 0, f"Kern {tcore} mm", fontsize=7, va="center")
    ax2.text(W2 + 0.4, (hb / 2 - tpp) * sc, "L2", fontsize=7, va="center")
    ax2.text(W2 + 0.4, -(hb / 2 - tpp) * sc, "L3", fontsize=7, va="center")
    ax2.text(W2 + 0.4, hb / 2 * sc + 0.25, f"Loetstopplack {P.T_MASK_LAM*1000:.0f} um, Er {P.ER_MASK} (L1/L4 ohne Cu)", fontsize=7)
    ax2.set_xlim(-W2 - 1, W2 + 12); ax2.set_ylim(-4, 4); ax2.set_aspect("equal")
    ax2.set_title("Querschnitt z = 10...88 (Dicke 3-fach ueberhoeht)", fontsize=9)
    ax2.set_xlabel("x [mm]"); ax2.set_yticks([])
    ax3 = fig.add_axes([0.60, 0.06, 0.38, 0.42]); ax3.axis("off")
    txt = (
        "Layoutvorgaben (Welle 2)\n"
        f"- S: {g.ws:g} mm breit, mittig, z = {g.z_s0:g}...{g.z_s1:g} mm, auf L2 UND L3 deckungsgleich\n"
        f"- G: Randstreifen x = +/-({g.ws/2+g.gap:g}...{xe:g}) bis z = {g.z_g1:g}, Steg z = {g.z_s1+g.gap:g}...{g.z_s1+g.gap+g.w_bar:g}\n"
        f"- Guard GND volle Breite auf L2/L3 von Kopf bis z = {g.z_guard:g} mm\n"
        f"- S-Zuleitung im Guard nur auf L2, {g.wf:g} mm, Abstand {g.cf:g} mm; L3 dort GND\n"
        "- L2-S und L3-S nur im Kopf (z < -3) per Via verbinden; G ebenso\n"
        f"- Kupfer >= {g.edge:g} mm zur Kontur (REQ-MECH-06: >= 1.0 + Fraestoleranz)\n"
        "- z = 0...2: Dichtstreifen ohne Vias (Mechanik M-03); Guard auf L2/L3 durchgehend\n"
        "- keine Vias, kein Kupfer auf L1/L4 fuer z > 0; Silk: Stecktiefe z = 5, Revision\n"
        "- Stackup JLC04161H-7628 (Standard), 1.6 mm, Lack beidseitig ueber der Sonde\n"
        "- Temperatursensor/Thermal-Pad nicht im Guardbereich (separat klaeren)"
    )
    ax3.text(0, 1, txt, va="top", fontsize=8.5, family="monospace")
    fig.savefig(os.path.join(HERE, "plots", "sketch_electrodes.png"), dpi=140)


if __name__ == "__main__":
    main()
