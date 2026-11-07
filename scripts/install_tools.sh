#!/usr/bin/env bash
# fluidi – Vorschlag für fehlende Werkzeuge (Phase 0). NUR nach Freigabe ausführen.
# Ausführung durch den Auftraggeber in WSL (sudo braucht Passwort):  bash scripts/install_tools.sh
set -euo pipefail

# 1) Basis: PDF lesen (Datenblätter), pip/venv, zip (Gerber-ZIP), Node (PWA-Tests)
sudo apt-get update
sudo apt-get install -y poppler-utils python3-pip python3-venv zip nodejs npm

# 2) KiCad 10 in WSL (gleiche Version wie unter Windows, inkl. Python-API pcbnew).
#    Achtung: ersetzt KiCad 9.0.9 in WSL.
sudo add-apt-repository -y ppa:kicad/kicad-10.0-releases
sudo apt-get update
sudo apt-get install -y --install-recommends kicad

# 3) Elmer FEM für die elektrostatische Feldsimulation der Sonde
sudo add-apt-repository -y ppa:elmer-csc-ubuntu/elmer-csc-ppa
sudo apt-get update
sudo apt-get install -y elmerfem-csc

# 4) Projekt-venv für Python-Pakete (ohne sudo, im Repo ignoriert)
python3 -m venv --system-site-packages .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install gmsh meshio scikit-fem pypdf

echo "Fertig. Kontrolle: scripts/toolcheck.sh"
