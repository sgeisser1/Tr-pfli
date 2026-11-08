#!/usr/bin/env bash
# fluidi Programmieradapter Rev 1 - Schaltplan neu erzeugen und pruefen.
# Aufruf aus dem Repo-Wurzelordner: bash hardware/programmer/gen/run_all.sh
# Schritte: Bibliothek + Schaltplan erzeugen, Netzliste gegen Soll pruefen, ERC KiCad 10 (WSL, falls vorhanden
# auch Windows), PDF-Export.
set -euo pipefail
cd "$(dirname "$0")/../../.."
PY=.venv/bin/python
SCH=hardware/programmer/fluidi_programmer.kicad_sch
OUT=hardware/programmer/out
WIN=/mnt/c/Users/steph/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe
mkdir -p "$OUT"
$PY hardware/programmer/gen/gen_programmer.py
$PY hardware/programmer/gen/gen_programmer.py check
echo "--- ERC KiCad $(kicad-cli --version) (WSL)"
kicad-cli sch erc --severity-all -o "$OUT/erc_wsl.rpt" "$SCH" | tail -1
grep -E "ERC messages" "$OUT/erc_wsl.rpt"
if [ -x "$WIN" ]; then
  echo "--- ERC KiCad $($WIN --version | tr -d '\r') (Windows)"
  "$WIN" sch erc --severity-all -o "$(wslpath -w "$OUT")\\erc_win.rpt" "$(wslpath -w "$SCH")" | tail -1
  grep -E "ERC messages" "$OUT/erc_win.rpt"
fi
kicad-cli sch export pdf -o "$OUT/fluidi_programmer_schematic.pdf" "$SCH" | tail -1
$PY hardware/programmer/gen/behelf_pads.py
