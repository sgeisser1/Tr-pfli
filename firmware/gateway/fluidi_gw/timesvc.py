"""Zeitdienst des Gateways (ARCHITECTURE.md Kap. 5, REQ-GW-09, Entscheidungsvorlage docs/reviews/phase5_gateway_zeit.md).

Reihenfolge der Zeitquellen: NTP (systemd-timesyncd, abschaltbar) -> RTC (Pi Zero 2 W hat keine; OP-GW-3)
-> Browserzeit einer angemeldeten PWA (nur wenn sonst keine gültige Zeit). Ohne gültige Zeit verteilt das
Gateway keine Zeit an Sensoren und markiert Werte mit Flag 2 (unsicher).

Die Systemuhr wird NICHT verstellt (der Dienst läuft ohne CAP_SYS_TIME). Die Browserzeit wird an die
monotone Uhr gebunden (Anker), damit ein späterer Sprung der Systemuhr (z. B. NTP kommt nachträglich) die
Gateway-Zeit nicht verfälscht. `wall()` liefert dieselbe Zeit für alle Module (model.now, Speicher, Klima).
"""
from __future__ import annotations

import shutil
import subprocess
import time

JUMP_LOG_S = 600
# Plausibilitätsgrenzen für eine von aussen gesetzte Zeit (Browser): Software-Stand 2026, Obergrenze 2100.
# Eine Handy-Uhr vor 2026 ist sicher falsch (z. B. Werkszustand 1970/2000) und wird abgelehnt.
PLAUSIBLE_MIN = 1767225600.0      # 2026-01-01T00:00:00Z
PLAUSIBLE_MAX = 4102444800.0      # 2100-01-01T00:00:00Z
BROWSER_NTP_DIFF_LOG_S = 120      # Abweichung Browser -> NTP ab 2 min ins Ereignisprotokoll

_ACTIVE: "TimeService | None" = None


def wall() -> float:
    """Gateway-Zeit (Unix-Sekunden) des aktiven Zeitdienstes, sonst Systemzeit."""
    return _ACTIVE.now() if _ACTIVE is not None else time.time()


def plausible(t_unix: float) -> bool:
    return PLAUSIBLE_MIN <= t_unix < PLAUSIBLE_MAX


class TimeService:
    def __init__(self, mode: str = "system", log=None, activate=True):
        """mode: 'system' (timedatectl abfragen), 'sim' (Uhr gilt als gültig, Quelle 'ntp'), 'invalid' (Tests)."""
        global _ACTIVE
        self.mode = mode
        self.source = "none"
        self.valid = mode == "sim"
        self.last_sync = time.time() if mode == "sim" else None
        self.log = log or (lambda *a: None)
        self._anchor = None            # (Browser-Unixzeit, monotonic) bei Quelle 'browser'
        self._last_check = 0.0
        self._last_wall = time.time()
        self._mono = time.monotonic()
        if mode == "sim":
            self.source = "ntp"
        self.refresh(force=True)
        if activate:
            _ACTIVE = self

    @property
    def offset(self) -> float:
        """Versatz Gateway-Zeit minus Systemzeit (0 ausser bei Quelle 'browser')."""
        return self.now() - time.time()

    def now(self) -> float:
        if self.source == "browser" and self._anchor is not None:
            t0, m0 = self._anchor
            return t0 + (time.monotonic() - m0)
        return time.time()

    def refresh(self, force=False):
        t, m = time.time(), time.monotonic()
        if abs((t - self._last_wall) - (m - self._mono)) > JUMP_LOG_S:
            self.log("warn", "time_jump", "Systemzeit ist gesprungen (> 10 min)")
        self._last_wall, self._mono = t, m
        if self.mode != "system" or (not force and t - self._last_check < 60):
            return
        self._last_check = t
        synced = self._ntp_synced()
        if synced:
            if not self.valid or self.source != "ntp":
                if self.source == "browser" and abs(self.now() - t) > BROWSER_NTP_DIFF_LOG_S:
                    self.log("warn", "time_browser_diff",
                             f"Browserzeit wich {self.now() - t:+.0f} s von NTP ab (Werte seither entsprechend versetzt)")
                self.log("info", "time_ntp", "Zeit über NTP synchronisiert")
            self.valid, self.source, self.last_sync, self._anchor = True, "ntp", t, None
        elif self.source != "browser":
            self.valid, self.source = False, "none"

    @staticmethod
    def _ntp_synced() -> bool:
        if not shutil.which("timedatectl"):
            return False
        try:
            r = subprocess.run(["timedatectl", "show", "-p", "NTPSynchronized", "--value"], capture_output=True,
                               text=True, timeout=3)
            return r.stdout.strip() == "yes"
        except (OSError, subprocess.SubprocessError):
            return False

    def set_browser_time(self, t_unix: float, force=False) -> bool:
        """Browserzeit übernehmen, nur wenn keine gültige Zeit vorliegt (oder force + elevate, API 5.7)
        und nur wenn sie plausibel ist (2026 <= t < 2100)."""
        if not plausible(t_unix):
            self.log("warn", "time_browser_rejected", "Zeit von der PWA unplausibel – nicht übernommen")
            return False
        if self.valid and not force:
            return False
        self._anchor = (float(t_unix), time.monotonic())
        self.valid, self.source, self.last_sync = True, "browser", float(t_unix)
        self.log("info", "time_browser", "Zeit von der PWA übernommen")
        return True

    def status(self, tz: str):
        from datetime import datetime, timezone
        iso = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if t else None  # noqa: E731
        return {"now": iso(self.now()), "valid": self.valid, "source": self.source, "last_sync": iso(self.last_sync),
                "rtc_ok": False, "timezone": tz}
