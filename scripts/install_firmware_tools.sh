#!/usr/bin/env bash
# =============================================================================================
# fluidi – Firmware-Werkzeuge installieren (Phase 4)  ·  WSL2 Ubuntu 24.04
#
# Anleitung: docs/manuals/INSTALL_FIRMWARE_TOOLS.md  (dort auch der Windows-Teil usbipd-win)
# Kontrolle: scripts/toolcheck.sh  (prüft nur, installiert nichts)
#
# Aufruf (aus dem Repo-Root, als normaler Benutzer, NICHT mit sudo):
#   bash scripts/install_firmware_tools.sh            # alles: apt (fragt sudo-Passwort) + TI + ESP + Python + Check
#   bash scripts/install_firmware_tools.sh apt        # nur Systempakete + Gruppe dialout (sudo)
#   bash scripts/install_firmware_tools.sh ti         # nur TI: SDK, TI Arm Clang, SysConfig (ohne sudo)
#   bash scripts/install_firmware_tools.sh sdklibs    # nur SDK-Bibliotheken bauen (dauert lange)
#   bash scripts/install_firmware_tools.sh py         # nur Python-venv (imgtool, pyserial)
#   bash scripts/install_firmware_tools.sh sbl        # optional: TI Linux-SBL (Referenz-Flasher, C)
#   bash scripts/install_firmware_tools.sh esp        # nur ESP-IDF für das Gateway (ohne sudo)
#   bash scripts/install_firmware_tools.sh check      # nur Versionscheck
#
# Eigenschaften:
#   - idempotent: bereits vorhandene, geprüfte Downloads und Installationen werden übersprungen
#   - alles ausser apt/dialout liegt im Home: ~/fluidi-tools (TI, Python) und ~/esp (ESP-IDF)
#   - jede TI-Datei wird mit der SHA-256-Prüfsumme von ti.com verglichen (Abruf 2026-11-07)
#   - kein Login nötig (alle URLs am 2026-11-07 per HTTP-HEAD geprüft: 200, application/octet-stream)
#
# Versionen (Begründung in der Anleitung, Kap. 2):
#   TI SimpleLink Low Power F3 SDK 9.23.00.27 · TI Arm Clang 4.0.4.LTS (vom SDK getestet)
#   SysConfig 1.28.2 (SDK verlangt >= 1.26.4) · ESP-IDF v6.1 · imgtool aus dem SDK (MCUboot)
# =============================================================================================
set -euo pipefail

# ---------------------------------------------------------------- Einstellungen / Versionen --
TOOLS="${FLUIDI_TOOLS:-$HOME/fluidi-tools}"         # TI-Werkzeuge, Python-venv, env.sh
ESPDIR="${FLUIDI_ESP:-$HOME/esp}"                   # ESP-IDF + Werkzeuge
DL="$TOOLS/downloads"
TI="$TOOLS/ti"

SDK_VER="9.23.00.27"; SDK_US="9_23_00_27"
SDK_ZIP="simplelink_lowpower_f3_sdk_${SDK_US}__linux.zip"
SDK_URL="https://dr-download.ti.com/software-development/software-development-kit-sdk/MD-emMPuXshOG/${SDK_VER}/${SDK_ZIP}"
SDK_SHA="651ce15880fd1c049b94b24be5738942fbf97a358036f58a856299c3f946733b"
SDK_DIR="$TI/simplelink_lowpower_f3_sdk_${SDK_US}"

CLANG_VER="4.0.4.LTS"
CLANG_BIN="ti_cgt_armllvm_${CLANG_VER}_linux-x64_installer.bin"
CLANG_URL="https://dr-download.ti.com/software-development/ide-configuration-compiler-or-debugger/MD-ayxs93eZNN/${CLANG_VER}/${CLANG_BIN}"
CLANG_SHA="98c60ecc259a07a54be6fcc0f55990332f493bfe5dad460c0ba83963f5dcb06f"
CLANG_DIR="$TI/ti-cgt-armllvm_${CLANG_VER}"

SYSCFG_VER="1.28.2"; SYSCFG_BUILD="4845"
SYSCFG_RUN="sysconfig-${SYSCFG_VER}_${SYSCFG_BUILD}-setup.run"
SYSCFG_URL="https://dr-download.ti.com/software-development/ide-configuration-compiler-or-debugger/MD-nsUM6f7Vvb/${SYSCFG_VER}.${SYSCFG_BUILD}/${SYSCFG_RUN}"
SYSCFG_SHA="86707095714ba9422a8e1523516fba17bdc3cc96ccc21ddad2deaabdd67b4da6"
SYSCFG_DIR="$TI/sysconfig_${SYSCFG_VER}"

IDF_VER="v6.1"
IDF_DIR="$ESPDIR/esp-idf"
export IDF_TOOLS_PATH="$ESPDIR/.espressif"          # ESP-Werkzeuge ebenfalls unter ~/esp

SBL_REPO="https://github.com/TexasInstruments-Sandbox/ble_examples.git"
SBL_BRANCH="simplelink_low_power_f3_sdk-7.40"
SBL_PATH="tools/TI_CC2340_Linux_SBL"

VENV="$TOOLS/venv"
ENVFILE="$TOOLS/env.sh"

# ---------------------------------------------------------------------------- Hilfsfunktionen --
say()  { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()   { printf '  [OK]    %s\n' "$*"; }
warn() { printf '  [WARN]  %s\n' "$*"; }
die()  { printf '\n\033[1;31m[FEHLER] %s\033[0m\n' "$*" >&2; exit 1; }

need_user() { [ "$(id -u)" -ne 0 ] || die "Bitte NICHT mit sudo starten. Das Skript fragt selbst nach dem sudo-Passwort (nur Teil 'apt')."; }

free_gb() { df -Pk "$1" | awk 'NR==2{printf "%d", $4/1048576}'; }

# Download mit Fortsetzung + SHA-256-Prüfung. Liegt die Datei schon korrekt da: überspringen.
fetch() {  # fetch <url> <datei> <sha256>
  local url="$1" f="$DL/$2" sha="$3"
  mkdir -p "$DL"
  if [ -f "$f" ] && echo "$sha  $f" | sha256sum -c --status; then ok "vorhanden + Prüfsumme ok: $2"; return; fi
  say "Lade $2"
  wget -c --progress=dot:giga -O "$f" "$url" || die "Download fehlgeschlagen: $url
  -> Datei von Hand im Browser laden (Seite in der Anleitung, Kap. 6) und nach $DL legen, dann Skript erneut starten."
  if ! echo "$sha  $f" | sha256sum -c --status; then
    mv -f "$f" "$f.bad"
    die "Prüfsumme falsch für $2 (Datei nach $f.bad verschoben).
  Erwartet: $sha
  Erhalten: $(sha256sum "$f.bad" | cut -d' ' -f1)
  -> Möglicherweise verlangt ti.com inzwischen ein Login (HTML statt Datei). Siehe Anleitung Kap. 6."
  fi
  ok "Prüfsumme ok: $2"
}

# ------------------------------------------------------------------------- Teil 1: apt (sudo) --
do_apt() {
  say "Teil 1: Systempakete (sudo) – Passwortabfrage folgt"
  # ESP-IDF-Voraussetzungen laut Espressif (ESP-IDF v6.1, Linux-Setup „legacy“):
  #   git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache
  #   libffi-dev libssl-dev dfu-util libusb-1.0-0
  # TI-SDK: make, cmake, python3; unzip für das SDK-Archiv; build-essential für den TI-SBL (optional)
  # Werkzeuge: usbutils (lsusb), picocom (serielles Terminal), curl
  sudo apt-get update
  sudo apt-get install -y \
    git wget curl unzip make build-essential \
    flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache \
    libffi-dev libssl-dev dfu-util libusb-1.0-0 \
    usbutils picocom
  # Zugriff auf /dev/ttyUSB* und /dev/ttyACM* ohne sudo
  if id -nG "$USER" | tr ' ' '\n' | grep -qx dialout; then
    ok "Benutzer $USER ist bereits in der Gruppe dialout"
  else
    sudo usermod -aG dialout "$USER"
    warn "Gruppe dialout ergänzt. Wirksam erst nach Neustart von WSL: in Windows-PowerShell 'wsl --shutdown', dann Ubuntu neu öffnen."
  fi
}

# ------------------------------------------------------------- Teil 2: TI-Werkzeuge (ohne sudo) --
install_bitrock() {  # install_bitrock <installer> <zielordner-erwartet>
  local inst="$DL/$1" want="$2"
  if [ -d "$want" ]; then ok "bereits installiert: $want"; return; fi
  chmod +x "$inst"
  say "Installiere $1 nach $TI (unbeaufsichtigt)"
  # TI-Installer (BitRock/InstallBuilder): --mode unattended --prefix <ordner>
  "$inst" --mode unattended --prefix "$TI" || die "Installer $1 meldet Fehler. Interaktiv versuchen: $inst --prefix $TI"
  [ -d "$want" ] || die "Erwarteter Ordner fehlt nach Installation: $want  (Inhalt von $TI: $(ls "$TI" | tr '\n' ' '))"
  ok "installiert: $want"
}

do_ti() {
  need_user
  say "Teil 2: TI-Werkzeuge für den Sensor (CC2340R52) nach $TI"
  mkdir -p "$TI"
  [ "$(free_gb "$HOME")" -ge 15 ] || die "Zu wenig Platz im Home (< 15 GB frei)."

  fetch "$CLANG_URL"  "$CLANG_BIN"  "$CLANG_SHA"
  fetch "$SYSCFG_URL" "$SYSCFG_RUN" "$SYSCFG_SHA"
  fetch "$SDK_URL"    "$SDK_ZIP"    "$SDK_SHA"

  install_bitrock "$CLANG_BIN"  "$CLANG_DIR"
  install_bitrock "$SYSCFG_RUN" "$SYSCFG_DIR"

  if [ -d "$SDK_DIR" ]; then
    ok "SDK bereits entpackt: $SDK_DIR"
  else
    say "Entpacke SDK (ca. 0.9 GB Archiv)"
    local tmp="$TI/.sdk_unpack"; rm -rf "$tmp"; mkdir -p "$tmp"
    unzip -q "$DL/$SDK_ZIP" -d "$tmp"
    # Archiv enthält den Ordner simplelink_lowpower_f3_sdk_<ver> (sonst Inhalt direkt)
    if [ -d "$tmp/$(basename "$SDK_DIR")" ]; then mv "$tmp/$(basename "$SDK_DIR")" "$SDK_DIR"; else mv "$tmp" "$SDK_DIR"; fi
    rm -rf "$tmp"
    ok "SDK entpackt: $SDK_DIR"
  fi

  # imports.mak auf unsere Pfade setzen (Original bleibt als imports.mak.orig erhalten).
  # Nur TI Arm Clang: Die BLE-Stack-Bibliotheken des SDK gibt es nur für ticlang und iar
  # (source/ti/ble/lib/CC2340R5/*/lib/{ticlang,iar}) – GCC kann den BLE-Stack nicht linken.
  local im="$SDK_DIR/imports.mak"
  [ -f "$im.orig" ] || cp "$im" "$im.orig"
  sed -e "s|^SYSCONFIG_TOOL .*|SYSCONFIG_TOOL         ?= $SYSCFG_DIR/sysconfig_cli.sh|" \
      -e "s|^CMAKE .*|CMAKE                  ?= $(command -v cmake || echo cmake)|" \
      -e "s|^TICLANG_ARMCOMPILER .*|TICLANG_ARMCOMPILER    ?= $CLANG_DIR|" \
      -e "s|^GCC_ARMCOMPILER .*|GCC_ARMCOMPILER        ?=|" \
      -e "s|^IAR_ARMCOMPILER .*|IAR_ARMCOMPILER        ?=|" \
      "$im.orig" > "$im"
  ok "imports.mak gesetzt (nur ticlang)"
  write_env
}

do_sdklibs() {
  need_user
  [ -d "$SDK_DIR" ] || die "SDK fehlt – zuerst Teil 'ti' ausführen."
  local stamp="$SDK_DIR/.fluidi_libs_built"
  if [ -f "$stamp" ]; then ok "SDK-Bibliotheken bereits gebaut ($(cat "$stamp"))"; return; fi
  say "Baue SDK-Bibliotheken (ticlang) – dauert je nach PC 15–60 min, Log: $TOOLS/sdk_build.log"
  ( cd "$SDK_DIR" && make -j"$(nproc)" ) > "$TOOLS/sdk_build.log" 2>&1 \
    || die "SDK-Build fehlgeschlagen. Letzte Zeilen: $(tail -n 20 "$TOOLS/sdk_build.log")"
  date -Iseconds > "$stamp"
  ok "SDK-Bibliotheken gebaut"
}

# --------------------------------------------------------------- Teil 3: Python-venv (ohne sudo) --
do_py() {
  need_user
  say "Teil 3: Python-venv $VENV (imgtool für MCUboot-Signatur, pyserial für ROM-UART-Bootloader)"
  [ -d "$VENV" ] || python3 -m venv "$VENV"
  "$VENV/bin/pip" install --quiet --upgrade pip
  "$VENV/bin/pip" install --quiet "pyserial==3.5" intelhex
  # imgtool in genau der Version, die zum MCUboot im SDK passt (SDK: imgtool 2.2.0rc1)
  local imgsrc="$SDK_DIR/source/third_party/mcuboot/scripts"
  if [ -d "$imgsrc" ]; then
    "$VENV/bin/pip" install --quiet "$imgsrc"
    ok "imgtool aus dem SDK installiert"
  else
    warn "SDK fehlt – imgtool von PyPI (2.5.0) als Ersatz. Nach Teil 'ti' erneut 'py' ausführen."
    "$VENV/bin/pip" install --quiet "imgtool==2.5.0"
  fi
  write_env
}

# ------------------------------------------------- Teil 4 (optional): TI Linux-SBL (Referenz) --
do_sbl() {
  need_user
  local dst="$TI/TI_CC2340_Linux_SBL"
  if [ -d "$dst" ]; then ok "TI-SBL bereits vorhanden: $dst"; return; fi
  say "Teil 4 (optional): TI CC2340 Linux Serial Bootloader (C-Quelltext, nur Referenz)"
  local tmp="$TI/.sbl_clone"; rm -rf "$tmp"
  git clone --quiet --depth 1 --branch "$SBL_BRANCH" --filter=blob:none --sparse "$SBL_REPO" "$tmp"
  git -C "$tmp" sparse-checkout set "$SBL_PATH"
  mv "$tmp/$SBL_PATH" "$dst"; rm -rf "$tmp"
  ok "TI-SBL nach $dst (nicht gebaut; fest 1 152 000 Baud, Linux_Serial.c Z. 148 – über 2 x 100 kOhm zu schnell, siehe Anleitung)"
}

# ---------------------------------------------------------- Teil 5: ESP-IDF Gateway (ohne sudo) --
do_esp() {
  need_user
  say "Teil 5: ESP-IDF $IDF_VER nach $IDF_DIR, Werkzeuge nach $IDF_TOOLS_PATH"
  mkdir -p "$ESPDIR"
  if [ -d "$IDF_DIR/.git" ]; then
    local cur; cur="$(git -C "$IDF_DIR" describe --tags --exact-match 2>/dev/null || echo '?')"
    if [ "$cur" = "$IDF_VER" ]; then ok "ESP-IDF $IDF_VER bereits geklont"
    else warn "ESP-IDF in $IDF_DIR ist '$cur', nicht $IDF_VER – wird nicht angefasst (von Hand prüfen)."; fi
  else
    # Befehl laut Espressif-Doku v6.1 (Linux, legacy): -b v6.1 --single-branch --recursive
    git clone -b "$IDF_VER" --single-branch --recursive https://github.com/espressif/esp-idf.git "$IDF_DIR"
  fi
  # install.sh ist selbst idempotent; nur Werkzeuge für das Ziel esp32s3
  ( cd "$IDF_DIR" && ./install.sh esp32s3 )
  write_env
}

# ------------------------------------------------------------------- Umgebungsdatei env.sh --
write_env() {
  mkdir -p "$TOOLS"
  cat > "$ENVFILE" <<EOF
# fluidi – Umgebung für Firmware-Builds. Erzeugt von scripts/install_firmware_tools.sh.
# Laden mit:  source ~/fluidi-tools/env.sh        (ESP-IDF zusätzlich:  fluidi_idf)
export FLUIDI_TOOLS="$TOOLS"
export FLUIDI_TI_SDK="$SDK_DIR"
export FLUIDI_TICLANG="$CLANG_DIR"
export FLUIDI_SYSCONFIG="$SYSCFG_DIR/sysconfig_cli.sh"
export IDF_TOOLS_PATH="$IDF_TOOLS_PATH"
export FLUIDI_IDF="$IDF_DIR"
case ":\$PATH:" in *":$CLANG_DIR/bin:"*) ;; *) export PATH="$CLANG_DIR/bin:$VENV/bin:\$PATH";; esac
fluidi_idf() { . "$IDF_DIR/export.sh"; }   # ESP-IDF-Umgebung (idf.py, esptool.py) in dieser Shell
EOF
  ok "Umgebungsdatei: $ENVFILE"
}

# ---------------------------------------------------------------------- Teil 6: Versionscheck --
do_check() {
  say "Versionscheck"
  local fail=0
  chk() { if eval "$2" >/dev/null 2>&1; then ok "$1: $(eval "$2" 2>&1 | head -n1)"; else warn "$1: FEHLT"; fail=1; fi; }
  chk "cmake"          "cmake --version"
  chk "make"           "make --version"
  chk "git"            "git --version"
  chk "picocom"        "picocom --help 2>&1 | head -n1"
  chk "TI Arm Clang"   "'$CLANG_DIR/bin/tiarmclang' --version"
  chk "SysConfig"      "test -x '$SYSCFG_DIR/sysconfig_cli.sh' && echo '$SYSCFG_DIR (Version $SYSCFG_VER)'"
  chk "TI F3 SDK"      "test -f '$SDK_DIR/imports.mak' && echo '$SDK_VER in $SDK_DIR'"
  chk "SDK-Libs gebaut" "cat '$SDK_DIR/.fluidi_libs_built'"
  chk "imgtool"        "'$VENV/bin/imgtool' version"
  chk "pyserial"       "'$VENV/bin/python' -c 'import serial; print(\"pyserial\", serial.VERSION)'"
  chk "ESP-IDF"        "git -C '$IDF_DIR' describe --tags"
  chk "idf.py/esptool" "bash -c '. \"$IDF_DIR/export.sh\" >/dev/null 2>&1 && idf.py --version && python -m esptool version | tail -n1'"
  if id -nG "$USER" | tr ' ' '\n' | grep -qx dialout; then ok "Gruppe dialout: ja"; else warn "Gruppe dialout: nein (Teil 'apt', danach wsl --shutdown)"; fail=1; fi
  for m in cdc_acm ch341 cp210x ftdi_sio; do
    if modinfo "$m" >/dev/null 2>&1; then ok "Kernelmodul $m verfügbar"; else warn "Kernelmodul $m fehlt (wsl --update)"; fi
  done
  echo; [ $fail -eq 0 ] && echo "Alles vorhanden." || echo "Es fehlt noch etwas (siehe [WARN])."
}

# ------------------------------------------------------------------------------- Ablauf --
cmd="${1:-all}"
case "$cmd" in
  apt)     need_user; do_apt ;;
  ti)      do_ti ;;
  sdklibs) do_sdklibs ;;
  py)      do_py ;;
  sbl)     do_sbl ;;
  esp)     do_esp ;;
  check)   do_check ;;
  all)     need_user; do_apt; do_ti; do_py; do_sdklibs; do_esp; do_check
           echo; echo "Fertig. Neue Shell öffnen (bzw. nach dialout-Änderung 'wsl --shutdown') und: source $ENVFILE" ;;
  *)       die "Unbekannter Teil '$cmd'. Erlaubt: all apt ti sdklibs py sbl esp check" ;;
esac
