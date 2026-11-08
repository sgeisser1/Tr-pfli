"""Status-LED des Gateways (D-027 vorläufig, Vorlage docs/reviews/phase5_gateway_led.md Variante B).

Hardware: grüne 3-mm-LED + 470 Ω an J8 Pin 11 (GPIO17), Kathode an Pin 14 (GND). Der Kernel stellt sie über das
Overlay `dtoverlay=gpio-led,gpio=17,label=fluidi,trigger=heartbeat` (install_gateway.sh) als /sys/class/leds/fluidi
bereit (overlays README, Abschnitt gpio-led, `docs/references/RaspberryPi_GPIO-Doku_Auszug_2026-11-08.txt` Z. 1606 ff.).

| Zustand                                   | Muster                          | wer                                     |
|-------------------------------------------|---------------------------------|-----------------------------------------|
| Pi startet, Dienst noch nicht bereit      | Herzschlag (Kernel-Trigger)     | Overlay, ohne Programm                  |
| Dienst läuft, Funk in Ordnung             | kurzer Blitz alle 5 s ("ok")    | dieser Dienst -> Root-Helfer            |
| Kopplungsfenster offen                    | schnelles Blinken ("pair")      | dieser Dienst -> Root-Helfer            |
| Funk ausgefallen (Adapter, Funk-Thread)   | aus ("off")                     | dieser Dienst -> Root-Helfer            |
| Nacht (ausserhalb des LED-Zeitfensters)   | aus ("off")                     | dieser Dienst -> Root-Helfer            |
| Dienst gestoppt/abgestürzt/Watchdog       | aus                             | systemd ExecStopPost=+fluidi-helper led off |

Das Blinken selbst macht der Kernel (Trigger `timer`, delay_on/delay_off in ms, docs.kernel.org/leds/leds-class),
der Dienst meldet nur Zustandswechsel. Er hat keine Root-Rechte und schreibt nicht selbst nach /sys
(ProtectKernelTunables); den Schreibzugriff macht fluidi-helper (`helper.py`, Aktion `led`). Anfragen nur bei
Zustandswechsel (SD-Karte schonen: typisch 2 Wechsel pro Tag für Tag/Nacht).

ANNAHMEN (D-027 „vorläufig“, Anpassung nach Mustertest):
- Nacht = ausserhalb des Zeitfensters der Sensor-LED (Einstellungen -> LED -> Zeitfenster und Wochentage), wie
  in der Vorlage vorgeschlagen. Ohne gültige Zeit gilt "Tag" (wie die Sensor-LED: ohne Zeit ganztags).
- Schalter "Status-LED" in den Einstellungen (`led.enabled`) gilt auch für die Gateway-LED.
- Kopplung blinkt auch nachts (vom Benutzer ausgelöst).
PROTOTYP-PRÜFUNG: Sichtbarkeit, Trigger `timer` im Raspberry-Pi-Kernel vorhanden, Verhalten nach Watchdog.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime

from . import timesvc

log = logging.getLogger("fluidi.led")

STATES = ("ok", "pair", "off")
# Muster (delay_on_ms, delay_off_ms) für den Kernel-Trigger "timer"; None = aus
PATTERNS = {"ok": (100, 4900), "pair": (100, 100), "off": None}


def _hm(x: str) -> int:
    return int(x[:2]) * 60 + int(x[3:5])


def is_night(led: dict, t_unix: float, tz, time_valid: bool) -> bool:
    """Ausserhalb des LED-Zeitfensters (start <= Minute < end, über Mitternacht möglich) oder an einem abgewählten
    Wochentag (1 = Montag … 7 = Sonntag). Ohne gültige Zeit: nie Nacht."""
    if not time_valid:
        return False
    win = (led or {}).get("water_window") or {}
    try:
        start, end = _hm(win.get("start", "00:00")), _hm(win.get("end", "24:00"))
    except (TypeError, ValueError):
        return False
    lt = datetime.fromtimestamp(t_unix, tz)
    m = lt.hour * 60 + lt.minute
    days = win.get("weekdays") or [1, 2, 3, 4, 5, 6, 7]
    if lt.isoweekday() not in days:
        return True
    if start == end:
        return False                      # Fenster ganztags
    inside = start <= m < end if start < end else (m >= start or m < end)
    return not inside


def desired(model, central, t_unix: float | None = None) -> str:
    """Soll-Zustand der LED aus Funkzustand, Kopplungsfenster, Einstellungen und Uhrzeit."""
    if central is None or central.thread is None or not central.thread.is_alive() or not getattr(central, "radio_ok", True):
        return "off"
    t = timesvc.wall() if t_unix is None else t_unix
    p = model.pairing
    if p.get("active") and (p.get("until") is None or p["until"] > t):
        return "pair"
    led = model.settings.get("led", {})
    if not led.get("enabled", True):
        return "off"
    if is_night(led, t, model.tz(), timesvc.valid()):
        return "off"
    return "ok"


class StatusLed:
    def __init__(self, model, central, request, interval: float = 1.0):
        """request(action, data): Anfrage an den Root-Helfer (server.ServerCtl.helper_request)."""
        self.model, self.central, self.request = model, central, request
        self.interval = interval
        self.state: str | None = None
        self._stop = threading.Event()
        self.thread: threading.Thread | None = None

    def update(self, t_unix: float | None = None) -> str:
        try:
            s = desired(self.model, self.central, t_unix)
        except Exception:  # noqa: BLE001 – LED darf den Dienst nie stören
            log.exception("LED-Zustand")
            s = "off"
        if s != self.state:
            try:
                self.request("led", {"state": s})
                self.state = s
            except OSError as e:
                log.warning("LED-Anfrage fehlgeschlagen: %s", e)
        return s

    def run(self):
        while not self._stop.is_set():
            self.update()
            self._stop.wait(self.interval)

    def start(self):
        self.thread = threading.Thread(target=self.run, name="fluidi-led", daemon=True)
        self.thread.start()

    def stop(self):
        """Beim regulären Stopp schaltet systemd (ExecStopPost) die LED aus; hier nur den Thread beenden."""
        self._stop.set()
