"""Systemangaben des Pi (best effort, ohne Rechte): WLAN, IP, Speicher, Temperatur. In der Simulation Platzhalter."""
from __future__ import annotations

import shutil
import socket
import subprocess
from pathlib import Path


def _run(cmd, timeout=3):
    if not shutil.which(cmd[0]):
        return None
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("10.255.255.255", 1))  # kein Paket wird gesendet (UDP ohne Daten)
            return s.getsockname()[0]
        finally:
            s.close()
    except OSError:
        return None


def wifi(sim=False):
    if sim:
        return {"ssid": "Simulation", "connected": True, "rssi_dbm": -55, "ip": ip_address() or "127.0.0.1"}
    out = _run(["nmcli", "-t", "-f", "ACTIVE,SSID,SIGNAL", "dev", "wifi"])
    ssid, sig = "", None
    for line in (out or "").splitlines():
        p = line.split(":")
        if len(p) >= 3 and p[0] == "yes":
            ssid = p[1]
            try:
                sig = int(p[2])
            except ValueError:
                sig = None
    # nmcli liefert Signal in % (0–100); grobe Umrechnung in dBm (ANNAHME, nur Anzeige)
    rssi = None if sig is None else int(-100 + sig / 2)
    return {"ssid": ssid, "connected": bool(ssid), "rssi_dbm": rssi, "ip": ip_address()}


def disk(path):
    try:
        u = shutil.disk_usage(path)
        return {"total": u.total, "free": u.free}
    except OSError:
        return {"total": 0, "free": 0}


def cpu_temp():
    p = Path("/sys/class/thermal/thermal_zone0/temp")
    try:
        return int(p.read_text().strip()) / 1000.0
    except (OSError, ValueError):
        return None


def mem_free():
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    except OSError:
        pass
    return None


def diskstats_written_bytes(device="mmcblk0"):
    """Geschriebene Bytes seit Start (für die Messung der SD-Schreibrate, ARCHITECTURE Kap. 14.4)."""
    try:
        for line in Path("/proc/diskstats").read_text().splitlines():
            p = line.split()
            if len(p) > 9 and p[2] == device:
                return int(p[9]) * 512
    except OSError:
        pass
    return None
