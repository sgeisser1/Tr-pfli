#!/bin/bash
# fluidi Sensor-Platine: 3D-Ansichten aus dem KiCad-Layout (kicad-cli 10, WSL). Aufruf aus dem Repo-Root.
set -e
P=hardware/sensor/fluidi_sensor.kicad_pcb; O=renders/pcb
C="--quality high --background opaque --use-board-stackup-colors"
for s in top bottom; do
  kicad-cli pcb render --side $s --rotate 0,0,90 --width 2400 --height 500 $C --zoom 3.3 -o $O/fluidi_pcb_$s.png $P
done
kicad-cli pcb render --side top --width 1400 --height 1600 $C --zoom 3.6 --pan 0,-5.5,0 -o $O/fluidi_pcb_kopf_nah.png $P
kicad-cli pcb render --rotate "'-40,0,30'" --perspective --width 2000 --height 1300 $C --zoom 2 -o $O/fluidi_pcb_iso.png $P
