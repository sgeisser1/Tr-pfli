#!/usr/bin/env bash
# fluidi Gateway – Installation auf dem Raspberry Pi Zero 2 W (Raspberry Pi OS Lite 64 bit, Bookworm/Trixie).
# Anleitung: docs/manuals/GATEWAY_SETUP.md
#
#   sudo ./install_gateway.sh              Installation bzw. Aktualisierung aus diesem Repository-Stand
#   sudo ./install_gateway.sh --wheels DIR bleak/dbus-fast offline aus DIR installieren (kein PyPI-Zugriff)
#   sudo ./install_gateway.sh --finish     Einrichtung abschliessen: SSH aus, Port 22 zu (REQ-SAF-NET-02)
#   sudo ./install_gateway.sh --check      nur prüfen (Python, Pakete, Dienste, Ports)
#
# Idempotent: mehrfach ausführbar. Daten unter /var/lib/fluidi bleiben erhalten.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
GW="$REPO/firmware/gateway"
OPT=/opt/fluidi
DATA=/var/lib/fluidi
ETC=/etc/fluidi
HOST=fluidi
WHEELS=""
MODE=install

while [ $# -gt 0 ]; do
  case "$1" in
    --wheels) WHEELS="$2"; shift 2 ;;
    --finish) MODE=finish; shift ;;
    --check) MODE=check; shift ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "Unbekannte Option: $1" >&2; exit 2 ;;
  esac
done

say() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
die() { printf '\033[1;31mFehler: %s\033[0m\n' "$*" >&2; exit 1; }
[ "$(id -u)" -eq 0 ] || die "bitte mit sudo ausführen"

check() {
  say "Prüfung"
  grep -a -q "Raspberry Pi Zero 2" /proc/device-tree/model 2>/dev/null && echo "Board: $(tr -d '\0' </proc/device-tree/model)" \
    || echo "Hinweis: kein Pi Zero 2 W erkannt ($(tr -d '\0' </proc/device-tree/model 2>/dev/null || echo unbekannt))"
  . /etc/os-release; echo "System: $PRETTY_NAME"
  python3 -c 'import sys; v=sys.version_info; print("Python", sys.version.split()[0]); sys.exit(0 if v>=(3,11) else 1)' \
    || die "Python >= 3.11 nötig (Bookworm 3.11, Trixie 3.13)"
  for s in bluetooth avahi-daemon nftables fluidi-gateway fluidi-helper.path; do
    printf '  %-22s %s\n' "$s" "$(systemctl is-active "$s" 2>/dev/null || true)"
  done
  ss -lntup 2>/dev/null | awk 'NR==1 || /:(22|80|443|8080|5353) /' || true
  # Zeit ohne RTC (D-028): NTP über systemd-timesyncd; Rückfall Browserzeit aus der App (GATEWAY_SETUP Kap. 9)
  printf '  %-22s %s\n' "systemd-timesyncd" "$(systemctl is-active systemd-timesyncd 2>/dev/null || true)"
  printf '  %-22s %s\n' "NTP synchronisiert" "$(timedatectl show -p NTPSynchronized --value 2>/dev/null || echo ?)"
  # Status-LED (D-027): Overlay gpio-led -> /sys/class/leds/fluidi
  if [ -e /sys/class/leds/fluidi/trigger ]; then
    printf '  %-22s %s\n' "Status-LED" "vorhanden, Trigger: $(grep -o '\[[a-z0-9-]*\]' /sys/class/leds/fluidi/trigger || echo ?)"
  else
    printf '  %-22s %s\n' "Status-LED" "fehlt (Overlay in config.txt? Neustart nötig?)"
  fi
  [ -x "$OPT/venv/bin/python" ] && "$OPT/venv/bin/python" -c 'import bleak, cryptography; print("bleak", bleak.__version__ if hasattr(bleak,"__version__") else "?", "cryptography", cryptography.__version__)' || true
}

if [ "$MODE" = check ]; then check; exit 0; fi

if [ "$MODE" = finish ]; then
  say "Einrichtung abschliessen: SSH aus, Port 22 zu"
  sed -i '/SSH-EINRICHTUNG/d' /etc/nftables.conf
  systemctl reload nftables || systemctl restart nftables
  systemctl disable --now ssh.service ssh.socket 2>/dev/null || true
  echo "SSH ist aus. Wieder einschalten (nur mit physischem Zugang): Datei 'ssh' auf die Boot-Partition legen,"
  echo "neu starten, dann 'sudo ./install_gateway.sh' erneut ausführen."
  exit 0
fi

check

# ------------------------------------------------------------------------------------------- Pakete
say "Pakete (apt)"
export DEBIAN_FRONTEND=noninteractive
apt-get update -q
apt-get install -y -q --no-install-recommends python3-venv python3-cryptography bluez avahi-daemon \
  nftables i2c-tools network-manager ca-certificates

# ------------------------------------------------------------------------------------------- Name, I²C, Bluetooth
say "Hostname '$HOST' (mDNS $HOST.local) und Schnittstellen"
if [ "$(hostname)" != "$HOST" ]; then
  hostnamectl set-hostname "$HOST"
  sed -i "s/^127\.0\.1\.1.*/127.0.1.1\t$HOST/" /etc/hosts
  grep -q "127.0.1.1" /etc/hosts || echo -e "127.0.1.1\t$HOST" >> /etc/hosts
fi
systemctl enable --now avahi-daemon
command -v raspi-config >/dev/null && raspi-config nonint do_i2c 0 || echo "Hinweis: I²C manuell aktivieren (dtparam=i2c_arm=on)"
# BlueZ: GATT-Datenbank auch ungebondeter Geräte zwischenspeichern -> schnellere Verbindung (PROTOCOL 0.5-s-Frist,
# Befund K-1). ANNAHME: Option 'Cache = always' in [GATT] von /etc/bluetooth/main.conf (PROTOTYP-PRÜFUNG).
python3 - <<'PY'
import re, pathlib
p = pathlib.Path("/etc/bluetooth/main.conf")
if p.exists():
    s = p.read_text()
    if "[GATT]" in s and not re.search(r"^Cache\s*=\s*always", s, re.M):
        s = re.sub(r"^#?\s*Cache\s*=.*$", "Cache = always", s, count=1, flags=re.M) if re.search(r"^#?\s*Cache\s*=", s, re.M) \
            else s.replace("[GATT]", "[GATT]\nCache = always", 1)
        p.write_text(s)
PY
systemctl restart bluetooth || true
# Status-LED (D-027, docs/reviews/phase5_gateway_led.md): grüne LED + 470 Ohm an GPIO17 (J8 Pin 11), GND Pin 14.
# Kernel-Overlay gpio-led: Herzschlag ab dem Start, danach steuert der Dienst über fluidi-helper (Aktion led).
# config.txt liegt bei Raspberry Pi OS in /boot/firmware/ (raspberrypi.com/documentation config_txt), älter /boot/.
BOOTCFG=""
for f in /boot/firmware/config.txt /boot/config.txt; do [ -f "$f" ] && { BOOTCFG="$f"; break; }; done
LED_OVERLAY="dtoverlay=gpio-led,gpio=17,label=fluidi,trigger=heartbeat"
if [ -n "$BOOTCFG" ]; then
  if ! grep -qxF "$LED_OVERLAY" "$BOOTCFG"; then
    printf '\n# fluidi Status-LED (D-027)\n%s\n' "$LED_OVERLAY" >> "$BOOTCFG"
    echo "Status-LED: Overlay in $BOOTCFG eingetragen – wirksam nach dem nächsten Neustart"
  fi
else
  echo "Hinweis: config.txt nicht gefunden – Zeile '$LED_OVERLAY' von Hand eintragen"
fi
# Zeit (D-028, ohne RTC): NTP über systemd-timesyncd (Root-Helfer stellt Server/Ein-Aus nach den App-Einstellungen).
# Ohne Netz übernimmt der Dienst die Handyzeit beim Öffnen der App; kein RTC-Overlay, kein hwclock.
# Nur bei der Erstinstallation einschalten: danach gilt die Einstellung aus der App (Drop-in des Root-Helfers).
if systemctl cat systemd-timesyncd.service >/dev/null 2>&1; then
  [ -f /etc/systemd/timesyncd.conf.d/fluidi.conf ] || timedatectl set-ntp true 2>/dev/null \
    || echo "Hinweis: 'timedatectl set-ntp true' fehlgeschlagen"
else
  echo "Hinweis: systemd-timesyncd fehlt – ohne NTP gilt nur die Handyzeit aus der App (GATEWAY_SETUP Kap. 9)"
fi
# WLAN-Energiesparen aus: Gateway muss jederzeit erreichbar sein (Koexistenz WLAN/BLE: PROTOTYP-PRÜFUNG OP-K12)
mkdir -p /etc/NetworkManager/conf.d
printf '[connection]\nwifi.powersave = 2\n' > /etc/NetworkManager/conf.d/fluidi-powersave.conf

# ------------------------------------------------------------------------------------------- SD-Karte schonen
say "SD-Karte schonen (ARCHITECTURE Kap. 14.4)"
mkdir -p /etc/systemd/journald.conf.d
printf '[Journal]\nStorage=volatile\nRuntimeMaxUse=16M\n' > /etc/systemd/journald.conf.d/fluidi.conf
systemctl restart systemd-journald
if systemctl list-unit-files | grep -q dphys-swapfile; then systemctl disable --now dphys-swapfile || true; fi
if command -v rpi-swap >/dev/null 2>&1; then echo "Hinweis: Swap (Trixie: zram) belassen – schreibt nicht auf die Karte"; fi
# noatime für die Root-Partition
if ! awk '$2=="/"{print $4}' /etc/fstab | grep -q noatime; then
  sed -i -E 's#^(\S+\s+/\s+\S+\s+)(\S+)#\1\2,noatime#' /etc/fstab
fi
grep -q '^tmpfs /tmp ' /etc/fstab || echo 'tmpfs /tmp tmpfs defaults,noatime,nosuid,size=32m 0 0' >> /etc/fstab

# ------------------------------------------------------------------------------------------- Benutzer, Dateien
say "Benutzer und Programmdateien"
id fluidi >/dev/null 2>&1 || useradd --system --home "$DATA" --shell /usr/sbin/nologin fluidi
for g in bluetooth i2c; do getent group "$g" >/dev/null && usermod -aG "$g" fluidi; done
VER="$(python3 -c "import re;print(re.search(r'__version__ = \"(.+?)\"', open('$GW/fluidi_gw/__init__.py').read()).group(1))")"
REL="$OPT/releases/$VER"
rm -rf "$REL"; mkdir -p "$REL/gateway" "$REL/app/dev"
cp -r "$GW/fluidi_gw" "$REL/gateway/"
cp "$GW/requirements-pi.txt" "$REL/gateway/"
( cd "$REPO/app" && cp -r index.html dashboard.html manifest.webmanifest sw.js css js img icons data "$REL/app/" )
cp "$REPO/app/dev/fluidi_calc.py" "$REPO/app/dev/fluidi_analysis.py" "$REL/app/dev/"   # gemeinsamer Rechenkern
find "$REL" -name '__pycache__' -prune -exec rm -rf {} +
chown -R root:root "$REL"; chmod -R go-w "$REL"
ln -sfn "$REL" "$OPT/current"
install -m 0755 "$GW/fluidi_gw/helper.py" /usr/local/sbin/fluidi-helper

say "Python-Umgebung $OPT/venv"
[ -x "$OPT/venv/bin/python" ] || python3 -m venv --system-site-packages "$OPT/venv"
if [ -n "$WHEELS" ]; then
  "$OPT/venv/bin/pip" install --no-index --find-links "$WHEELS" -r "$GW/requirements-pi.txt"
else
  "$OPT/venv/bin/pip" install -q -r "$GW/requirements-pi.txt"
fi
"$OPT/venv/bin/pip" freeze > "$REL/gateway/pip-freeze.txt"

mkdir -p "$ETC/keys" "$DATA/requests"
[ -f "$ETC/gateway.toml" ] || install -m 0644 "$GW/install/gateway.toml" "$ETC/gateway.toml"
chown -R fluidi:fluidi "$DATA"; chmod 0700 "$DATA" "$DATA/requests"

# ------------------------------------------------------------------------------------------- Zertifikat
say "HTTPS: Einmal-CA nur für $HOST.local (CA-Schlüssel nur im Arbeitsspeicher)"
if [ ! -f "$DATA/tls/server.crt" ]; then
  sudo -u fluidi "$OPT/venv/bin/python" -c "import sys; sys.path.insert(0,'$REL/gateway'); from fluidi_gw.__main__ import main; main(['pki-init','-c','$ETC/gateway.toml'])"
else
  echo "Zertifikat vorhanden (erneuern: sudo -u fluidi … pki-init --force, dann CA auf den Geräten neu installieren)"
fi

# ------------------------------------------------------------------------------------------- Dienste, Firewall
say "Dienste und Firewall"
install -m 0644 "$GW/install/systemd/"fluidi-*.service "$GW/install/systemd/"fluidi-helper.path /etc/systemd/system/
install -m 0644 "$GW/install/nftables-fluidi.conf" /etc/nftables.conf
systemctl daemon-reload
systemctl enable --now nftables
systemctl enable --now fluidi-helper.path
systemctl enable fluidi-gateway
systemctl restart fluidi-gateway
sleep 5
systemctl --no-pager --lines=5 status fluidi-gateway || true

say "Fertig"
CODE="$(sudo -u fluidi "$OPT/venv/bin/python" -c "import sys; sys.path.insert(0,'$REL/gateway'); from fluidi_gw.__main__ import main; main(['setup-code','-c','$ETC/gateway.toml'])")"
FP="$(sudo -u fluidi "$OPT/venv/bin/python" -c "import sys; sys.path.insert(0,'$REL/gateway'); from fluidi_gw.__main__ import main; main(['fingerprint','-c','$ETC/gateway.toml'])")"
cat <<EOT
  Version:            $VER
  CA herunterladen:   http://$HOST.local/ca  (auf dem Handy, siehe GATEWAY_SETUP.md Kap. 6)
  CA-Fingerabdruck:   $FP
  App:                https://$HOST.local/
  Einrichtungscode:   $CODE
  Öffentlicher Signaturschlüssel Sensor-Firmware nach $ETC/keys/sensor-fw.pem kopieren (vom Entwickler).
  Danach: sudo $0 --finish   (SSH aus)
EOT
