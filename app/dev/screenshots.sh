#!/usr/bin/env bash
# fluidi – Screenshots der Hauptseiten mit Microsoft Edge (headless, Windows) gegen den Mock-Server in WSL.
# Edge erreicht den WSL-Dienst über die localhost-Weiterleitung von WSL2 (getestet 2026-11-07).
#
#   app/dev/screenshots.sh            # schreibt app/docs/screenshots/*.png
#
# Hinweis: Edge headless legt das Layout mindestens 492 px breit an (gemessen); schmale
# Aufnahmen daher mit 500 px statt Handybreite 390 px.
# Voraussetzungen: WSL2 mit localhost-Weiterleitung, Edge unter Windows, python3.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APP="$(cd "$HERE/.." && pwd)"
OUT="$APP/docs/screenshots"
EDGE="${EDGE:-/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe}"
PS=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
WINTMP_WSL=/mnt/c/Temp/fluidi-shots
WINTMP='C:\Temp\fluidi-shots'
BUDGET="${BUDGET:-1500}"  # muss kleiner sein als die SSE-Verzögerung in app.js (2000 ms)
mkdir -p "$OUT" "$WINTMP_WSL"

pids=()
cleanup() {
  for p in "${pids[@]}"; do kill "$p" 2>/dev/null || true; done
  # nur die eigenen headless-Instanzen beenden (Profil fluidi-shot-*)
  "$PS" -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | Where-Object { \$_.CommandLine -like '*fluidi-shot-*' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }" >/dev/null 2>&1 || true
}
trap cleanup EXIT

start_mock() { # port, extra args
  python3 "$HERE/mock_server.py" --port "$1" --quiet "${@:2}" >/dev/null 2>&1 &
  pids+=($!)
}
start_mock 8091 --demo-session
start_mock 8092
start_mock 8093 --fresh
for port in 8091 8092 8093; do
  for _ in $(seq 1 50); do curl -s -o /dev/null "http://localhost:$port/" && break; sleep 0.2; done
done

n=0
shot() { # name, port, hash, width, height
  local name="$1" port="$2" hash="$3" w="$4" h="$5"
  n=$((n + 1))
  rm -f "$WINTMP_WSL/$name.png"
  (cd /mnt/c/Temp && timeout 60 "$EDGE" --headless=new --disable-gpu --hide-scrollbars \
    --user-data-dir="C:\\Temp\\fluidi-shot-$n" --window-size="$w,$h" --virtual-time-budget="$BUDGET" \
    --screenshot="$WINTMP\\$name.png" "http://localhost:$port/$hash" >/dev/null 2>&1) || echo "WARNUNG: $name rc=$?"
  if [ -f "$WINTMP_WSL/$name.png" ]; then
    cp "$WINTMP_WSL/$name.png" "$OUT/$name.png"
    echo "ok  $name"
  else
    echo "FEHLT $name"
  fi
  rm -rf "/mnt/c/Temp/fluidi-shot-$n" 2>/dev/null || true
}

shot 01_uebersicht_desktop 8091 '#/' 1280 1000
shot 02_uebersicht_schmal 8091 '#/' 500 1400
shot 03_detail_woche_desktop 8091 '#/pflanze/2?bereich=woche' 1280 1000
shot 04_detail_jahr_schmal 8091 '#/pflanze/1?bereich=jahr' 500 1500
shot 05_detail_tag_desktop 8091 '#/pflanze/5?bereich=tag' 1280 1000
shot 06_bearbeiten 8091 '#/pflanze/2/bearbeiten' 1280 1100
shot 07_kalibrieren 8091 '#/pflanze/1/kalibrieren' 1280 900
shot 08_koppeln 8091 '#/koppeln' 1280 800
shot 09_einstellungen 8091 '#/einstellungen' 1280 2200
shot 10_firmware 8091 '#/firmware' 1280 1300
shot 11_daten 8091 '#/daten' 1280 1000
shot 12_anmelden_schmal 8092 '#/anmelden' 500 844
shot 13_einrichten_schmal 8093 '#/anmelden' 500 844
shot 14_detail_luft_schmal 8091 '#/pflanze/6?bereich=monat' 500 1400
echo "Screenshots in $OUT"
