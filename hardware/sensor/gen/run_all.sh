#!/usr/bin/env bash
# fluidi Sensor Rev B - Schaltplan komplett neu erzeugen und pruefen.
# Aufruf aus dem Repo-Wurzelordner: bash hardware/sensor/gen/run_all.sh
# Schritte: Bibliothek + Schaltplan erzeugen, Netzliste gegen Soll pruefen, ERC mit KiCad 10 (WSL) und
# KiCad 10 (Windows), PDF-Export, BOM im JLC-Format + Register-Zeilen.
# JLC-Status vorher bei Bedarf neu abfragen: .venv/bin/python hardware/sensor/gen/jlc_check.py
set -euo pipefail
cd "$(dirname "$0")/../../.."
PY=.venv/bin/python
SCH=hardware/sensor/fluidi_sensor.kicad_sch
OUT=hardware/sensor/out
WIN=/mnt/c/Users/steph/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe
mkdir -p "$OUT"
$PY hardware/sensor/gen/gen_schematic.py
$PY hardware/sensor/gen/check_netlist.py
echo "--- ERC KiCad $(kicad-cli --version) (WSL)"
kicad-cli sch erc --severity-all -o "$OUT/erc_wsl.rpt" "$SCH" | tail -1
grep -E "ERC messages" "$OUT/erc_wsl.rpt"
if [ -x "$WIN" ]; then
  echo "--- ERC KiCad $($WIN --version | tr -d '\r') (Windows)"
  "$WIN" sch erc --severity-all -o "$(wslpath -w "$OUT")\\erc_win.rpt" "$(wslpath -w "$SCH")" | tail -1
  grep -E "ERC messages" "$OUT/erc_win.rpt"
fi
kicad-cli sch export pdf -o "$OUT/fluidi_sensor_schematic.pdf" "$SCH" | tail -1
$PY hardware/sensor/gen/bom_jlc.py --register
