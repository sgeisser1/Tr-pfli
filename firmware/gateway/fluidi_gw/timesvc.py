"""Zeitdienst des Gateways (ARCHITECTURE.md Kap. 5, REQ-GW-09).

Reihenfolge der Zeitquellen: NTP (systemd-timesyncd, abschaltbar) -> RTC (Pi Zero 2 W hat keine; OP-GW-3)
-> Browserzeit einer angemeldeten PWA (nur wenn sonst keine gültige Zeit). Ohne gültige Zeit verteilt das
Gateway keine Zeit an Sensoren und markiert Werte mit Flag 2 (unsicher).

Die Systemuhr wird NICHT verstellt (der Dienst läuft ohne CAP_SYS_TIME); die Browserzeit wirkt als Versatz.
"""
from __future__ import annotations

import shutil
import subprocess
import time

JUMP_LOG_S = 600


class TimeService:
    def __init__(self, mode: str = "system", log=None):
        """mode: 'system' (timedatectl abfragen), 'sim' (Uhr gilt als gültig, Quelle 'ntp'), 'invalid' (Tests)."""
        self.mode = mode
        self.offset = 0.0
        self.source = "none"
        self.valid = mode == "sim"
        self.last_sync = time.time() if mode == "sim" else None
        self.log = log or (lambda *a: None)
        self._last_check = 0.0
        self._last_wall = time.time()
        if mode == "sim":
            self.source = "ntp"
        self.refresh(force=True)

    def now(self) -> float:
        return time.time() + self.offset

    def refresh(self, force=False):
        t = time.time()
        if abs((t - self._last_wall) - (time.monotonic() - getattr(self, "_mono", time.monotonic()))) > JUMP_LOG_S:
            self.log("warn", "time_jump", "Systemzeit ist gesprungen (> 10 min)")
        self._last_wall, self._mono = t, time.monotonic()
        if self.mode != "system" or (not force and t - self._last_check < 60):
            return
        self._last_check = t
        synced = self._ntp_synced()
        if synced:
            if not self.valid or self.source != "ntp":
                self.log("info", "time_ntp", "Zeit über NTP synchronisiert")
            self.valid, self.source, self.offset, self.last_sync = True, "ntp", 0.0, t
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
        """Browserzeit übernehmen, nur wenn keine gültige Zeit vorliegt (oder force + elevate, API 5.7)."""
        if self.valid and not force:
            return False
        self.offset = t_unix - time.time()
        self.valid, self.source, self.last_sync = True, "browser", time.time()
        self.log("info", "time_browser", "Zeit von der PWA übernommen")
        return True

    def status(self, tz: str):
        from datetime import datetime, timezone
        iso = lambda t: datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if t else None  # noqa: E731
        return {"now": iso(self.now()), "valid": self.valid, "source": self.source, "last_sync": iso(self.last_sync),
                "rtc_ok": False, "timezone": tz}
