#!/usr/bin/env bash
# Tröpfli – Toolcheck (Phase 0). Prüft alle CLI-Werkzeuge reproduzierbar.
# MCP-Server (FreeCAD, Blender) werden vom Orchestrator separat getestet.
# Aufruf: scripts/toolcheck.sh   (aus dem Repo-Root, in WSL)
set -u
REPO="$(cd "$(dirname "$0")/.." && pwd)"
PY="$REPO/.venv/bin/python"; [ -x "$PY" ] || PY=python3
K10="${KICAD10_CLI:-/mnt/c/Users/steph/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe}"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
ok(){ printf "  [OK]    %s\n" "$*"; }; bad(){ printf "  [FEHLT] %s\n" "$*"; }

echo "== Versionen =="
for t in python3 kicad-cli ngspice freecadcmd blender gmsh ccx git curl; do
  if command -v "$t" >/dev/null; then ok "$t -> $(command -v $t)"; else bad "$t"; fi
done
kicad-cli version 2>/dev/null | sed 's/^/  kicad-cli (WSL): /'
[ -x "$K10" ] && "$K10" version 2>/dev/null | head -1 | sed 's/^/  kicad-cli (Windows): /' || bad "KiCad 10 (Windows) unter $K10"

echo "== Optionale/fehlende Werkzeuge =="
for t in pdftoppm pdftotext zip node npm ElmerSolver ElmerGrid pio west; do
  command -v "$t" >/dev/null && ok "$t" || bad "$t"
done
for m in numpy scipy matplotlib sympy requests yaml serial cryptography pcbnew gmsh skfem meshio pypdf; do
  "$PY" -c "import $m" 2>/dev/null && ok "python ($PY): $m" || bad "python: $m"
done

echo "== Funktionstest KiCad (Board erzeugen, DRC, Gerber, STEP) =="
( cd "$TMP" && "$PY" - <<'EOF'
import pcbnew
b = pcbnew.BOARD(); b.SetCopperLayerCount(4)
pts=[(0,0),(20,0),(20,100),(0,100)]
for i in range(4):
    s=pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT); s.SetLayer(pcbnew.Edge_Cuts)
    s.SetStart(pcbnew.VECTOR2I_MM(*pts[i])); s.SetEnd(pcbnew.VECTOR2I_MM(*pts[(i+1)%4])); b.Add(s)
pcbnew.SaveBoard("t.kicad_pcb", b)
EOF
kicad-cli pcb drc t.kicad_pcb -o drc.rpt >/dev/null 2>&1 && grep -q "Found 0 DRC" drc.rpt && ok "DRC (kicad-cli WSL)" || bad "DRC"
kicad-cli pcb export gerbers t.kicad_pcb -o g/ >/dev/null 2>&1 && ok "Gerber-Export" || bad "Gerber-Export"
kicad-cli pcb export step t.kicad_pcb -o t.step >/dev/null 2>&1 && ok "STEP-Export" || bad "STEP-Export"
[ -x "$K10" ] && "$K10" pcb drc "$(wslpath -w t.kicad_pcb)" -o "$(wslpath -w drc10.rpt)" >/dev/null 2>&1 && grep -q "Found 0 DRC" drc10.rpt && ok "DRC (kicad-cli Windows)" || bad "DRC (kicad-cli Windows)" )

echo "== Funktionstest ngspice (RC-Puffer, erwartet vmin ~2.870 V) =="
cat > "$TMP/rc.cir" <<'EOF'
* Knopfzelle Ri=15 Ohm, 10 mA / 3 ms, C=100 uF
V1 a 0 3.0
R1 a b 15
C1 b 0 100u IC=3.0
I1 b 0 PULSE(0 10m 1m 1u 1u 3m 100m)
.tran 10u 10m UIC
.control
run
meas tran vmin MIN v(b)
quit
.endc
.end
EOF
ngspice -b "$TMP/rc.cir" 2>/dev/null | grep -i "vmin" | sed 's/^/  /'

echo "== Funktionstest Elmer (Plattenkondensator, erwartet W = 1.992E-10 J/m) =="
cp "$REPO/simulation/field/selftest/"{box.grd,case.sif} "$TMP/" && ( cd "$TMP" && ElmerGrid 1 2 box.grd >/dev/null 2>&1 \
  && echo case.sif > ELMERSOLVER_STARTINFO && timeout -s KILL 60 "$REPO/scripts/elmer.sh" case.sif 2>&1 \
  | grep -E "Total Electric Energy" | sed 's/^/  /' ) || bad "Elmer"
