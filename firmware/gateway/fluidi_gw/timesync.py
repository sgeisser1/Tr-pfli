"""Zeitrekonstruktion der Sensor-Datensätze (PROTOCOL.md Kap. 7, ARCHITECTURE.md Kap. 4/5).

Der Sensor kennt nur (boot_id, uptime). Bei jeder Sitzung speichert das Gateway einen Synchronpunkt
(boot_id, uptime, Gateway-Zeit, Gateway-Zeit gültig). Ein Datensatz bekommt seine absolute Zeit so:
  1. Punkte derselben boot_id davor UND danach -> lineare Interpolation (korrigiert Quarzdrift)
  2. nur davor  -> Extrapolation mit der Gangabweichung aus den letzten zwei Punkten ≥ 24 h Abstand (sonst 0 ppm)
  3. nur danach -> Rückrechnung vom ersten Punkt der boot_id (Batteriewechsel ohne Gateway, REQ-SYS-07)
  4. kein Punkt -> Zeit unsicher; obere Grenze = Start der nächsten boot_id, falls bekannt
Nur Punkte mit gültiger Gateway-Zeit werden verwendet (Kap. 7 Regel 3).

API-Flags (GATEWAY_API Kap. 2.1): Bit 1 = rekonstruiert, Bit 2 = Zeit unsicher.
"""
from __future__ import annotations

from dataclasses import dataclass

FLAG_RECONSTRUCTED = 1 << 1
FLAG_UNSYNCED = 1 << 2
DRIFT_MIN_SPAN_S = 24 * 3600
EXTRAPOLATE_OK_S = 26 * 3600     # bis hierhin gilt eine Extrapolation als "normal" (Messintervall + Reserve)
MAX_DRIFT_PPM = 500              # unplausible Gangabweichung (Quarz-Budget 48 ppm, Kap. 7.5) -> ignorieren


@dataclass(frozen=True)
class SyncPoint:
    boot_id: int
    uptime: float
    gw_time: float
    valid: bool = True


def _rate(points):
    """Sekunden Gateway-Zeit je Sekunde Sensor-Laufzeit aus den letzten zwei Punkten mit ≥ 24 h Abstand."""
    pts = sorted(points, key=lambda p: p.uptime)
    if len(pts) < 2:
        return 1.0
    last = pts[-1]
    for p in reversed(pts[:-1]):
        if last.uptime - p.uptime >= DRIFT_MIN_SPAN_S:
            r = (last.gw_time - p.gw_time) / (last.uptime - p.uptime)
            if abs(r - 1.0) * 1e6 <= MAX_DRIFT_PPM:
                return r
            return 1.0
    return 1.0


def reconstruct(boot_id: int, uptime: float, points, now_s: float, gw_time_valid=True):
    """-> (t_unix, flags). points: alle SyncPoints dieses Sensors (beliebige boot_id)."""
    good = [p for p in points if p.valid]
    same = sorted((p for p in good if p.boot_id == boot_id), key=lambda p: p.uptime)
    before = [p for p in same if p.uptime <= uptime]
    after = [p for p in same if p.uptime >= uptime]
    if before and after:
        a, b = before[-1], after[0]
        if b.uptime == a.uptime:
            return a.gw_time, 0
        f = (uptime - a.uptime) / (b.uptime - a.uptime)
        return a.gw_time + f * (b.gw_time - a.gw_time), 0
    if before:
        a = before[-1]
        dt = (uptime - a.uptime) * _rate(before)
        return a.gw_time + dt, (0 if uptime - a.uptime <= EXTRAPOLATE_OK_S else FLAG_RECONSTRUCTED)
    if after:
        b = after[0]
        return b.gw_time - (b.uptime - uptime) * _rate(same), FLAG_RECONSTRUCTED
    # kein Punkt dieser boot_id: obere Grenze = Start der nächsten boot_id (falls bekannt)
    nxt = [p for p in good if p.boot_id > boot_id]
    if nxt:
        first = min(nxt, key=lambda p: (p.boot_id, p.uptime))
        start_next = first.gw_time - first.uptime
        return start_next, FLAG_RECONSTRUCTED | FLAG_UNSYNCED
    return now_s, FLAG_RECONSTRUCTED | FLAG_UNSYNCED | (0 if gw_time_valid else FLAG_UNSYNCED)
