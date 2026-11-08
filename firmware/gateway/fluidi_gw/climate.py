"""Raumklima im Gateway (D-017): Sensirion SHT4x über I²C (Linux i2c-dev), mit Simulationsmodus.

Belege: docs/datasheets/Sensirion_SHT4x_Datasheet_V7.3.pdf
  - I²C-Adresse 0x44 (SHT4x-AD1B), S. 1; Befehl 0xFD = Messung T & RH hohe Wiederholbarkeit, Antwort 6 Byte
    [T(2) CRC, RH(2) CRC], S. 12 Tab. 8
  - Messdauer tMEAS,h max. 8.3 ms, S. 10  -> wir warten 10 ms
  - CRC-8: Polynom 0x31, Init 0xFF, ohne Reflexion, Final-XOR 0x00, Beispiel CRC(0xBEEF) = 0x92, S. 11 Tab. 7
  - Umrechnung RH = −6 + 125·S_RH/(2^16−1) %RH, T = −45 + 175·S_T/(2^16−1) °C, S. 12 Formeln (1)/(2);
    RH auf 0–100 % begrenzen empfohlen (S. 13)
  - Versorgung 1.08–3.6 V (S. 9) -> 3V3 vom Pi-Header.
Konkretes Breakout-Modul und Verdrahtung: docs/manuals/GATEWAY_SETUP.md (Platzhalter, PROTOTYP-PRÜFUNG).

SD-Schonung: Messung alle 5 min, Werte im RAM gesammelt, in die Datenbank alle 30 min in einer Transaktion.
Zeit ohne RTC (D-028, phase5_gateway_zeit.md Z-7/V-3): Solange die Gateway-Zeit ungültig ist (kein NTP, keine
Browserzeit), bekommen die Werte nur einen Monotonzeitstempel und bleiben im RAM (höchstens MAX_PENDING Werte);
sobald die Zeit gültig ist, werden sie auf die Gateway-Zeit umgerechnet und gespeichert. Ein Neustart vor dem
Zeitabgleich verwirft diese Werte (kein Datenpfad der Pflanzen, nur Raumklima).
Eigenerwärmung des Pi verfälscht die Temperatur -> belüftete, getrennte Kammer (D-017), Offset später kalibrieren.
"""
from __future__ import annotations

import math
import os
import random
import threading
import time

from . import timesvc

I2C_SLAVE = 0x0703  # linux/i2c-dev.h
CMD_MEASURE_HIGH = 0xFD
FLUSH_S = 1800
MAX_PENDING = 2016          # 7 Tage à 5 min ohne gültige Zeit, danach älteste verwerfen


def crc8(data: bytes) -> int:
    crc = 0xFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x31) & 0xFF if crc & 0x80 else (crc << 1) & 0xFF
    return crc


def convert(raw6: bytes):
    """6 Byte Antwort -> (T °C, RH %) oder ValueError bei CRC-Fehler."""
    if len(raw6) != 6 or crc8(raw6[0:2]) != raw6[2] or crc8(raw6[3:5]) != raw6[5]:
        raise ValueError("SHT4x: CRC falsch")
    st = (raw6[0] << 8) | raw6[1]
    srh = (raw6[3] << 8) | raw6[4]
    t = -45 + 175 * st / 65535
    rh = -6 + 125 * srh / 65535
    return round(t, 2), round(min(100.0, max(0.0, rh)), 1)


class SHT4x:
    source = "sht4x"

    def __init__(self, bus=1, addr=0x44):
        import fcntl
        self.fd = os.open(f"/dev/i2c-{bus}", os.O_RDWR)
        fcntl.ioctl(self.fd, I2C_SLAVE, addr)

    def read(self):
        os.write(self.fd, bytes([CMD_MEASURE_HIGH]))
        time.sleep(0.010)  # tMEAS,h ≤ 8.3 ms
        return convert(os.read(self.fd, 6))


class SimClimate:
    source = "sim"

    def __init__(self, seed=1):
        self.rng = random.Random(seed)

    def read(self):
        t = time.time()
        day = math.sin((t % 86400) / 86400 * 2 * math.pi - 2.0)
        return round(21.5 + 1.5 * day + self.rng.gauss(0, 0.05), 2), round(42 - 6 * day + self.rng.gauss(0, 0.3), 1)


class Climate:
    def __init__(self, store, kind="auto", bus=1, addr=0x44, interval=300, log=None):
        self.store = store
        self.interval = interval
        self.buf = []
        self.last = None
        self.err = None
        self.log = log or (lambda *a: None)
        self.dev = None
        if kind in ("auto", "sht4x"):
            try:
                self.dev = SHT4x(bus, addr)
            except Exception as e:  # noqa: BLE001
                self.err = str(e)
                if kind == "sht4x":
                    self.log("warn", "climate", f"Klimasensor nicht gefunden: {e}")
        if self.dev is None and kind in ("sim",):
            self.dev = SimClimate()
        self.source = self.dev.source if self.dev else "off"
        self._stop = threading.Event()
        self.last_flush = time.monotonic()
        self.dropped = 0

    def sample(self):
        if not self.dev:
            return None
        try:
            t, rh = self.dev.read()
        except Exception as e:  # noqa: BLE001
            self.err = str(e)
            return None
        now, mono = int(timesvc.wall()), time.monotonic()
        self.last = {"t": now, "temp_c": t, "rh_pct": rh}
        # (Gateway-Zeit oder None bei ungültiger Zeit, Monotonzeit, T, rF)
        self.buf.append((now if timesvc.valid() else None, mono, t, rh))
        if mono - self.last_flush >= FLUSH_S:
            self.flush()
        return self.last

    def flush(self, final=False):
        """Gepufferte Werte speichern. Werte ohne gültige Zeit bleiben im Puffer, bis die Zeit gültig ist."""
        self.last_flush = time.monotonic()
        if not self.buf:
            return
        if any(w is None for w, *_ in self.buf) and not timesvc.valid():
            keep = [x for x in self.buf if x[0] is None]
            rows = [(w, t, rh) for w, _, t, rh in self.buf if w is not None]
            if final:
                self.log("info", "climate_time", f"{len(keep)} Klimawerte ohne gültige Zeit verworfen")
                keep = []
            elif len(keep) > MAX_PENDING:
                self.dropped += len(keep) - MAX_PENDING
                keep = keep[-MAX_PENDING:]
            self.buf = keep
        else:
            wall, mono = timesvc.wall(), time.monotonic()
            rows = [(w if w is not None else int(wall - (mono - m)), t, rh) for w, m, t, rh in self.buf]
            self.buf = []
        self.store.insert_climate(rows)

    def pending_rows(self):
        """Noch nicht gespeicherte Werte als (t, T, rF); ohne gültige Zeit nur die mit Zeitstempel."""
        ok = timesvc.valid()
        wall, mono = timesvc.wall(), time.monotonic()
        return [(w if w is not None else int(wall - (mono - m)), t, rh) for w, m, t, rh in list(self.buf)
                if w is not None or ok]

    def latest(self):
        from datetime import datetime, timezone
        if not self.last:
            return None
        return {"t": datetime.fromtimestamp(self.last["t"], timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "temp_c": self.last["temp_c"], "rh_pct": self.last["rh_pct"], "source": self.source}

    def run(self):
        first = True
        while not self._stop.wait(0 if first else self.interval):
            first = False
            self.sample()

    def start(self):
        if self.dev:
            threading.Thread(target=self.run, name="fluidi-climate", daemon=True).start()

    def stop(self):
        self._stop.set()
        if self.buf:
            self.flush(final=True)
