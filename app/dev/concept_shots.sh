#!/usr/bin/env bash
# fluidi – Screenshots der drei Stil-Entwürfe (app/concept/) mit Microsoft Edge headless (Windows) gegen den
# Mock-Server in WSL. Handy-Aufnahmen in einem Geräterahmen: Edge headless legt Seiten mindestens ~500 px breit an,
# deshalb lädt eine lokale Rahmenseite die App in einem 430 px breiten iframe (Mock mit --allow-framing).
#
#   app/dev/concept_shots.sh                 # alle: 3 Entwürfe × 6 Seiten × hell/dunkel × Handy/Desktop
#                                            # + Profil und Raumeditor (nur hell)
#   app/dev/concept_shots.sh frost home      # nur Entwurf/Seite (Filter, Teilstring)
#   python3 app/dev/concept_compose.py       # Vergleichsbilder für docs/software/UI_ENTWUERFE.md
#
# Ausgabe: app/docs/concept/<entwurf>_<seite>_<handy|desktop>_<hell|dunkel>.png
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
APP="$(cd "$HERE/.." && pwd)"
OUT="$APP/docs/concept"
EDGE="${EDGE:-/mnt/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe}"
PS=/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe
WT=/mnt/c/Temp/fluidi-concept
WTW='C:\Temp\fluidi-concept'
PORT="${PORT:-8097}"
BUDGET="${BUDGET:-5000}"
FILTER_T="${1:-}"
FILTER_P="${2:-}"
mkdir -p "$OUT" "$WT"

cleanup() {
  [ -n "${MOCK:-}" ] && kill "$MOCK" 2>/dev/null || true
  [ -n "${FRS:-}" ] && kill "$FRS" 2>/dev/null || true
  [ -n "${FR:-}" ] && rm -rf "$FR"
  "$PS" -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='msedge.exe'\" | Where-Object { \$_.CommandLine -like '*fluidi-cshot-*' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }" >/dev/null 2>&1 || true
}
trap cleanup EXIT

python3 "$HERE/mock_server.py" --port "$PORT" --quiet --demo-session --allow-framing >/dev/null 2>&1 &
MOCK=$!
# Rahmenseiten über einen zweiten lokalen Server (frame-ancestors * erlaubt kein file:)
FR="$(mktemp -d)"
FPORT=$((PORT + 1))
python3 -m http.server "$FPORT" --bind 127.0.0.1 --directory "$FR" >/dev/null 2>&1 &
FRS=$!
for _ in $(seq 1 50); do curl -s -o /dev/null "http://localhost:$PORT/concept/" && break; sleep 0.2; done

# Rahmenseite (Handy 430 × 932 CSS-px, wie iPhone Pro Max), Hintergrund je Modus
frame() { # datei, url, bg
  cat > "$1" <<EOF
<!doctype html><html><head><meta charset="utf-8"><style>
html,body{margin:0;background:$3;}
.phone{position:absolute;left:40px;top:34px;width:430px;height:932px;border-radius:58px;overflow:hidden;
box-shadow:0 0 0 11px #121417,0 0 0 13px #3a3f46,0 30px 60px rgba(0,0,0,.35);background:#000}
iframe{border:0;width:430px;height:932px;display:block}
.isl{position:absolute;left:50%;top:11px;width:122px;height:34px;margin-left:-61px;background:#000;border-radius:20px;z-index:2}
.sb{position:absolute;z-index:2;top:17px;font:600 16px -apple-system,"Segoe UI",sans-serif;color:$4}
.t{left:46px}.r{right:34px;letter-spacing:2px;font-size:13px}
</style></head><body><div class="phone"><div class="isl"></div><div class="sb t">9:41</div><div class="sb r">&#9679;&#9679;&#9679; &#9646;</div><iframe src="$2"></iframe></div></body></html>
EOF
}

n=0
shot() { # name, url, w, h
  n=$((n + 1))
  local name="$1" url="$2" w="$3" h="$4"
  rm -f "$WT/$name.png"
  (cd /mnt/c/Temp && timeout 90 "$EDGE" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 \
    --user-data-dir="C:\\Temp\\fluidi-cshot-$n" --window-size="$w,$h" --virtual-time-budget="$BUDGET" \
    --screenshot="$WTW\\$name.png" "$url" >/dev/null 2>&1) || echo "WARNUNG: $name rc=$?"
  if [ -f "$WT/$name.png" ]; then cp "$WT/$name.png" "$OUT/$name.png"; echo "ok  $name"; else echo "FEHLT $name"; fi
  rm -rf "/mnt/c/Temp/fluidi-cshot-$n" 2>/dev/null || true
}

PAGES=("home|#/" "pflanze|#/pflanze/1" "raum|#/raum" "dashboard|#/dashboard" "statistik|#/statistik" "einstellungen|#/einstellungen"
       "profil|#/pflanze/2/profil" "raumeditor|#/raum?edit=1")
ONLY_LIGHT=" profil raumeditor "  # Unterseiten: nur hell
for theme in frost botanik stele; do
  [ -n "$FILTER_T" ] && [[ "$theme" != *"$FILTER_T"* ]] && continue
  for pg in "${PAGES[@]}"; do
    page="${pg%%|*}"; hash="${pg#*|}"
    [ -n "$FILTER_P" ] && [[ "$page" != *"$FILTER_P"* ]] && continue
    for mode in light dark; do
      [ "$mode" = dark ] && [[ "$ONLY_LIGHT" == *" $page "* ]] && continue
      sch=$([ "$mode" = light ] && echo hell || echo dunkel)
      url="http://localhost:$PORT/concept/?theme=$theme&mode=$mode&shot=1$hash"
      bg=$([ "$mode" = light ] && echo '#dfe3e8' || echo '#0d0f12')
      fg=$([ "$mode" = light ] && echo '#111' || echo '#f2f2f2')
      [ "$theme" = stele ] && [ "$mode" = light ] && fg='#0f2230'
      frame "$FR/frame_$theme$page$mode.html" "${url%%#*}&frame=1#${url#*#}" "$bg" "$fg"
      shot "${theme}_${page}_handy_${sch}" "http://localhost:$FPORT/frame_$theme$page$mode.html" 510 1000
      shot "${theme}_${page}_desktop_${sch}" "$url" 1440 900
    done
  done
done
echo "Screenshots in $OUT"
