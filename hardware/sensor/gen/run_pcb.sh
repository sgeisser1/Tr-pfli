#!/usr/bin/env bash
# fluidi Sensor Rev B - Layout neu erzeugen, DRC (KiCad 10 WSL + Windows) und Fertigungsdaten exportieren.
# Aufruf aus dem Repo-Wurzelordner:  bash hardware/sensor/gen/run_pcb.sh [kragen|band] [SEED]
# SEED: Reihenfolge der Signalnetze im Router (Standard kragen 7, band 8 = vollstaendig geroutet; deterministisch)
# Voraussetzung: Schaltplan aktuell (bash hardware/sensor/gen/run_all.sh), sonst schlaegt die Paritaetspruefung fehl.
set -euo pipefail
cd "$(dirname "$0")/../../.."
PY=.venv/bin/python
PCB=hardware/sensor/fluidi_sensor.kicad_pcb
OUT=hardware/sensor/out
WIN=/mnt/c/Users/steph/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe
U3=${1:-kragen}
if [ "$U3" = "band" ]; then SEED=${2:-8}; else SEED=${2:-7}; fi
mkdir -p "$OUT" "$OUT/gerber" "$OUT/pdf" "$OUT/render"

$PY hardware/sensor/gen/gen_pcb.py --u3 "$U3" --seed "$SEED" --out "$PCB" --plot "$OUT/layout_band_routing.png"

echo "--- DRC KiCad $(kicad-cli --version) (WSL)"
kicad-cli pcb drc --schematic-parity --refill-zones --severity-all --format report -o "$OUT/drc_wsl.rpt" "$PCB" | tail -1
kicad-cli pcb drc --schematic-parity --refill-zones --severity-all --format json -o "$OUT/drc_wsl.json" "$PCB" >/dev/null
grep -E "^\*\*" "$OUT/drc_wsl.rpt" || true
if [ -x "$WIN" ]; then
  echo "--- DRC KiCad $($WIN --version | tr -d '\r') (Windows)"
  "$WIN" pcb drc --schematic-parity --refill-zones --severity-all --format report \
    -o "$(wslpath -w "$OUT")\\drc_win.rpt" "$(wslpath -w "$PCB")" | tail -1
  grep -E "^\*\*" "$OUT/drc_win.rpt" || true
fi

echo "--- Gerber/Bohrdaten (JLC: Protel-Endungen, ohne X2, Bohrdaten Excellon mm, PTH/NPTH getrennt)"
rm -f "$OUT"/gerber/*
kicad-cli pcb export gerbers --no-x2 --no-netlist --subtract-soldermask --use-drill-file-origin \
  -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts \
  -o "$OUT/gerber/" "$PCB" | tail -1
kicad-cli pcb export drill --format excellon --drill-origin plot --excellon-units mm --excellon-separate-th \
  --excellon-zeros-format decimal --generate-map --map-format pdf -o "$OUT/gerber/" "$PCB" | tail -1
mv -f "$OUT"/gerber/*-drl_map.pdf "$OUT/pdf/" 2>/dev/null || true
(cd "$OUT/gerber" && rm -f ../fluidi_sensor_gerber_jlc.zip && zip -q ../fluidi_sensor_gerber_jlc.zip ./*)

echo "--- Bestueckung (CPL JLC), BOM"
kicad-cli pcb export pos --format csv --units mm --side front --use-drill-file-origin --exclude-dnp \
  -o "$OUT/fluidi_sensor_pos_kicad.csv" "$PCB" | tail -1
$PY hardware/sensor/gen/cpl_jlc.py "$OUT/fluidi_sensor_pos_kicad.csv" "$OUT/fluidi_sensor_cpl_jlc.csv"

echo "--- STEP, PDF, Render"
kicad-cli pcb export step --subst-models --force --no-dnp -o "$OUT/fluidi_sensor.step" "$PCB" 2>&1 | tail -2
kicad-cli pcb export pdf --mode-multipage --include-border-title --drill-shape-opt 1 \
  -l F.Cu,In1.Cu,In2.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,F.Fab,B.Fab,User.2 --cl Edge.Cuts \
  -o "$OUT/pdf/fluidi_sensor_layout_lagen.pdf" "$PCB" | tail -1
kicad-cli pcb export pdf --mode-single --include-border-title --sp --cdnp \
  -l F.Fab,F.Silkscreen,F.Courtyard,Edge.Cuts -o "$OUT/pdf/fluidi_sensor_bestueckung_F.pdf" "$PCB" | tail -1
kicad-cli pcb export pdf --mode-single --include-border-title --mirror --sp \
  -l B.Fab,B.Silkscreen,B.Cu,Edge.Cuts -o "$OUT/pdf/fluidi_sensor_bestueckung_B.pdf" "$PCB" | tail -1
for side in top bottom; do
  kicad-cli pcb render --side $side --quality high -w 900 -h 2400 --background opaque \
    -o "$OUT/render/fluidi_sensor_$side.png" "$PCB" 2>&1 | tail -1 || true
done
kicad-cli pcb render --side top --quality high -w 1600 -h 1100 --zoom 4 --pan "0,-6.15,0" --background opaque \
  -o "$OUT/render/fluidi_sensor_kopf_top.png" "$PCB" 2>&1 | tail -1 || true
echo "fertig"
