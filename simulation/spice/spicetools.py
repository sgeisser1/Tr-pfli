"""fluidi - Hilfsfunktionen fuer ngspice im Batchbetrieb (nur Standardbibliothek + numpy).

run(netlist_text, cir_path, signals) schreibt die Netzliste, ruft `ngspice -b` auf und liest die mit
`wrdata` geschriebenen Spalten zurueck (dict signal -> numpy-Array, Schluessel "time" fuer die Zeitachse).
"""
import os
import subprocess

import numpy as np


def run(netlist, cir_path, signals, analysis, keep_cir=True):
    """netlist: Text ohne .control/.end; analysis: z. B. 'tran 1u 10m' oder 'op'."""
    data_path = os.path.splitext(cir_path)[0] + ".dat"
    ctl = [".control", "set wr_singlescale", "set wr_vecnames", "option numdgt=7",
           analysis, "wrdata " + os.path.basename(data_path) + " " + " ".join(signals), "quit", ".endc", ".end"]
    with open(cir_path, "w") as fh:
        fh.write(netlist.rstrip() + "\n" + "\n".join(ctl) + "\n")
    r = subprocess.run(["ngspice", "-b", os.path.basename(cir_path)], cwd=os.path.dirname(cir_path),
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(data_path):
        raise RuntimeError(f"ngspice-Fehler ({cir_path}):\n{r.stdout[-2000:]}\n{r.stderr[-2000:]}")
    with open(data_path) as fh:
        head = fh.readline().split()
        arr = np.loadtxt(fh, ndmin=2)
    os.remove(data_path)
    if not keep_cir:
        os.remove(cir_path)
    return {h: arr[:, i] for i, h in enumerate(head)}
