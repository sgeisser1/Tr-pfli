"""fluidi-helper: führt wenige, streng geprüfte Root-Aktionen für den Dienst aus (läuft als root über
fluidi-helper.path/.service, wenn in /var/lib/fluidi/requests eine Anfrage liegt). Der Gateway-Dienst selbst
hat keine Root-Rechte (ProtectSystem=strict, NoNewPrivileges).

Aktionen: reboot · wifi (nmcli, Rückfall nach 120 s, UC-13) · ntp (timesyncd-Drop-in) · update (Release umschalten
mit Rückfall, REQ-GW-11) · led (Status-LED GPIO17, D-027: nur die Zustände ok/pair/off mit fest programmierten
Werten). Alles andere wird verworfen und protokolliert (journald, flüchtig).

Direkter Aufruf `fluidi-helper led off` (systemd ExecStopPost des Gateway-Dienstes): LED aus, wenn der Dienst endet.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
import time
from pathlib import Path

REQ = Path("/var/lib/fluidi/requests")
OPT = Path("/opt/fluidi")
NTP_DROPIN = Path("/etc/systemd/timesyncd.conf.d/fluidi.conf")
LED_DIR = Path("/sys/class/leds/fluidi")      # dtoverlay=gpio-led,gpio=17,label=fluidi (install_gateway.sh)
# Kernel-Trigger "timer": delay_on/delay_off in ms (docs.kernel.org/leds/leds-class). Muss zu statusled.PATTERNS passen.
LED_PATTERNS = {"ok": (100, 4900), "pair": (100, 100), "off": None}
REQ_MAX = 4096          # Anfragen sind wenige hundert Byte (Sicherheit K-3)


def sh(*cmd, check=True, timeout=60):
    return subprocess.run(cmd, check=check, capture_output=True, text=True, timeout=timeout)


def online_ok():
    r = sh("nmcli", "-t", "-f", "STATE", "general", check=False)
    return r.stdout.strip().startswith("connected")


def do_wifi(req):
    ssid, psk = str(req["ssid"]), str(req.get("psk", ""))
    if not 1 <= len(ssid) <= 32 or (psk and not 8 <= len(psk) <= 63) or any(c in ssid for c in "\n\r\0"):
        raise ValueError("ungültige WLAN-Daten")
    old = sh("nmcli", "-t", "-f", "NAME,TYPE", "connection", "show", "--active", check=False).stdout
    old_name = next((l.split(":")[0] for l in old.splitlines() if l.endswith(":802-11-wireless")), None)
    args = ["nmcli", "device", "wifi", "connect", ssid] + (["password", psk] if psk else [])
    r = subprocess.run(args, capture_output=True, text=True, timeout=int(req.get("rollback_s", 120)))
    if r.returncode != 0 or not online_ok():
        print(f"WLAN-Wechsel fehlgeschlagen, Rückfall auf {old_name}", file=sys.stderr)
        if old_name:
            sh("nmcli", "connection", "up", old_name, check=False)


def do_ntp(req):
    server = str(req.get("server", ""))
    if server and not re.fullmatch(r"[A-Za-z0-9.-]{1,64}", server):
        raise ValueError("NTP-Server ungültig")
    NTP_DROPIN.parent.mkdir(parents=True, exist_ok=True)
    NTP_DROPIN.write_text(f"[Time]\nNTP={server}\n")
    sh("timedatectl", "set-ntp", "true" if req.get("enabled", True) else "false")
    sh("systemctl", "restart", "systemd-timesyncd", check=False)


def do_update(req):
    ver = str(req["version"])
    src = Path(req["path"]).resolve()
    if not re.fullmatch(r"\d+\.\d+\.\d+", ver) or not str(src).startswith("/var/lib/fluidi/staging/"):
        raise ValueError("Update-Anfrage ungültig")
    dst = OPT / "releases" / ver
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)
    cur = OPT / "current"
    prev = cur.resolve() if cur.exists() else None
    tmp = OPT / "current.new"
    tmp.unlink(missing_ok=True)
    tmp.symlink_to(dst)
    tmp.replace(cur)
    sh("systemctl", "restart", "fluidi-gateway", check=False)
    time.sleep(60)
    if sh("systemctl", "is-active", "fluidi-gateway", check=False).stdout.strip() != "active" and prev:
        print(f"Update {ver} startet nicht – Rückfall auf {prev}", file=sys.stderr)
        tmp.unlink(missing_ok=True)
        tmp.symlink_to(prev)
        tmp.replace(cur)
        sh("systemctl", "restart", "fluidi-gateway", check=False)
    shutil.rmtree(src, ignore_errors=True)


def do_led(req):
    state = req.get("state")
    if state not in LED_PATTERNS:
        raise ValueError("LED-Zustand ungültig")
    if not (LED_DIR / "trigger").exists():
        print("Status-LED nicht vorhanden (Overlay gpio-led fehlt oder Neustart nötig)", file=sys.stderr)
        return
    pat = LED_PATTERNS[state]
    if pat is None:
        (LED_DIR / "trigger").write_text("none")
        (LED_DIR / "brightness").write_text("0")
        return
    (LED_DIR / "trigger").write_text("timer")
    (LED_DIR / "delay_on").write_text(str(pat[0]))
    (LED_DIR / "delay_off").write_text(str(pat[1]))


ACTIONS = {"reboot": lambda r: sh("systemctl", "reboot"), "wifi": do_wifi, "ntp": do_ntp, "update": do_update,
           "led": do_led}


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv:
        if len(argv) == 2 and argv[0] == "led" and argv[1] in LED_PATTERNS:
            try:
                do_led({"state": argv[1]})
            except OSError as e:
                print(f"LED: {e}", file=sys.stderr)
            return
        print(f"unbekannter Aufruf: {argv}", file=sys.stderr)
        sys.exit(2)
    try:
        dfd = os.open(REQ, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)   # Ordner selbst kein Symlink (K-3)
    except OSError as e:
        print(f"Anfrageordner {REQ}: {e}", file=sys.stderr)
        return
    try:
        for name in sorted(n for n in os.listdir(dfd) if n.endswith(".json")):
            try:
                req = read_request(dfd, name)
                os.unlink(name, dir_fd=dfd)
                act = ACTIONS.get(req.get("action")) if isinstance(req, dict) else None
                if not act:
                    print(f"unbekannte Aktion verworfen: {req.get('action') if isinstance(req, dict) else '?'}", file=sys.stderr)
                    continue
                act(req)
            except Exception as e:  # noqa: BLE001
                print(f"{name}: {e}", file=sys.stderr)
                try:
                    os.unlink(name, dir_fd=dfd)       # entfernt einen Symlink selbst, nie sein Ziel
                except OSError:
                    pass
    finally:
        os.close(dfd)


def read_request(dfd: int, name: str) -> dict:
    """Anfrage lesen, ohne Symlinks zu folgen und ohne an FIFOs/Geräten zu hängen (Sicherheit K-3):
    O_NOFOLLOW | O_NONBLOCK, fstat = reguläre Datei mit einem Link, Grösse <= REQ_MAX."""
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0), dir_fd=dfd)
    try:
        st = os.fstat(fd)
        if not stat.S_ISREG(st.st_mode):
            raise ValueError("keine reguläre Datei – verworfen")
        if st.st_nlink != 1:
            raise ValueError("Datei mit mehreren Links – verworfen")
        if st.st_size > REQ_MAX:
            raise ValueError(f"Anfrage zu gross ({st.st_size} > {REQ_MAX} Byte) – verworfen")
        data = os.read(fd, REQ_MAX + 1)
        if len(data) > REQ_MAX:
            raise ValueError("Anfrage zu gross – verworfen")
        return json.loads(data.decode("utf-8"))
    finally:
        os.close(fd)


if __name__ == "__main__":
    main()
