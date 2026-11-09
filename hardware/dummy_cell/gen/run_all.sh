#!/usr/bin/env bash
# fluidi Dummy-Scheibe Rev 1 - Platinen erzeugen, DRC (KiCad 10 WSL + Windows), Gerber/Bohrdaten/ZIP, PDF, Kosten.
# Aufruf aus dem Repo-Wurzelordner:  bash hardware/dummy_cell/gen/run_all.sh
set -euo pipefail
cd "$(dirname "$0")/../../.."
PY=.venv/bin/python
D=hardware/dummy_cell
OUT=$D/out
WIN=/mnt/c/Users/steph/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe
mkdir -p "$OUT"
$PY $D/gen/gen_dummy.py
for B in plus minus; do
  PCB=$D/fluidi_dummy_$B.kicad_pcb
  echo "--- $B: DRC KiCad $(kicad-cli --version) (WSL)"
  kicad-cli pcb drc --severity-all --format report -o "$OUT/drc_${B}_wsl.rpt" "$PCB" | tail -1
  grep -E "^\*\* Found" "$OUT/drc_${B}_wsl.rpt"
  if [ -x "$WIN" ]; then
    echo "--- $B: DRC KiCad $($WIN --version | tr -d '\r') (Windows)"
    "$WIN" pcb drc --severity-all --format report -o "$(wslpath -w "$OUT")\\drc_${B}_win.rpt" "$(wslpath -w "$PCB")" | tail -1
    grep -E "^\*\* Found" "$OUT/drc_${B}_win.rpt"
  fi
  G=$OUT/gerber_$B
  rm -rf "$G"; mkdir -p "$G"
  kicad-cli pcb export gerbers --no-x2 --no-netlist --subtract-soldermask \
    -l F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts -o "$G/" "$PCB" | tail -1
  kicad-cli pcb export drill --format excellon --excellon-units mm --excellon-separate-th \
    --excellon-zeros-format decimal -o "$G/" "$PCB" | tail -1
  (cd "$G" && rm -f ../fluidi_dummy_${B}_gerber_jlc.zip && zip -q -X ../fluidi_dummy_${B}_gerber_jlc.zip ./*)
  kicad-cli pcb export pdf --mode-single --include-border-title \
    -l F.Cu,B.Cu,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,F.Fab,Edge.Cuts -o "$OUT/fluidi_dummy_${B}_layout.pdf" "$PCB" | tail -1
  kicad-cli pcb export svg --mode-single --exclude-drawing-sheet --fit-page-to-board \
    -l F.Cu,F.Mask,F.Silkscreen,Edge.Cuts -o "$OUT/fluidi_dummy_${B}_oben.svg" "$PCB" | tail -1
  kicad-cli pcb export svg --mode-single --exclude-drawing-sheet --fit-page-to-board --mirror \
    -l B.Cu,B.Mask,B.Silkscreen,Edge.Cuts -o "$OUT/fluidi_dummy_${B}_unten.svg" "$PCB" | tail -1
done
$PY $D/gen/cost_dummy.py | tee "$OUT/kosten.txt"
(cd "$OUT" && sha256sum fluidi_dummy_*_gerber_jlc.zip > SHA256SUMS && cat SHA256SUMS)
