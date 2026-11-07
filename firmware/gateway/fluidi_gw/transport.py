"""Funk-Transport: echtes BLE über bleak (BlueZ/D-Bus) oder simulierte Sensoren im selben Prozess.

Schnittstelle (für central.py):
  Radio.start(on_adv)     dauerndes Scannen, on_adv(protocol.Adv) für jedes fluidi-Advertising
  Radio.connect(addr)     -> Link (GATT verbunden, Notify auf TX aktiv)
  Link.send(frame, response=True)   Schreiben auf RX (Write bzw. Write Without Response für OTA_DATA)
  Link.recv(timeout)      nächste Notification von TX (asyncio.TimeoutError bei Zeitablauf)
  Link.close()

bleak ist optional (requirements-pi.txt). Ohne bleak läuft nur der Simulationsmodus.
PROTOTYP-PRÜFUNG: BleakRadio ist ohne Hardware nur gegen die bleak-API geschrieben (bleak 3.0.x), nicht am
Pi Zero 2 W getestet. Verbindungsparameter (7.5–15 ms, PROTOCOL 2.5 Regel 4) setzt BlueZ selbst; bleak bietet
dafür keine Schnittstelle (Befund W-1 in docs/reviews/phase4_protocol_software.md).
"""
from __future__ import annotations

import asyncio
import logging

from . import protocol as P

log = logging.getLogger("fluidi.radio")


class LinkClosed(Exception):
    pass


class Link:
    mtu = 247

    async def send(self, frame: bytes, response: bool = True):
        raise NotImplementedError

    async def recv(self, timeout: float) -> bytes:
        raise NotImplementedError

    async def close(self):
        raise NotImplementedError


class Radio:
    name = "none"

    async def start(self, on_adv):
        raise NotImplementedError

    async def stop(self):
        pass

    async def connect(self, addr: str) -> Link:
        raise NotImplementedError


# ------------------------------------------------------------------------------------------------ Simulation
class SimLink(Link):
    def __init__(self, sensor, mtu=247):
        self.sensor = sensor
        self.mtu = mtu
        self.rxq: asyncio.Queue = asyncio.Queue()
        self.closed = False

    # Sensor -> Gateway
    def notify(self, frame: bytes):
        if not self.closed:
            self.rxq.put_nowait(frame)

    def drop(self):
        """vom Sensor getrennt"""
        if not self.closed:
            self.closed = True
            self.rxq.put_nowait(None)

    async def send(self, frame: bytes, response: bool = True):
        if self.closed:
            raise LinkClosed("getrennt")
        await asyncio.sleep(0)  # Funkzeit nicht modelliert, nur Reihenfolge
        await self.sensor.on_write(self, bytes(frame))

    async def recv(self, timeout: float) -> bytes:
        if self.closed and self.rxq.empty():
            raise LinkClosed("getrennt")
        f = await asyncio.wait_for(self.rxq.get(), timeout)
        if f is None:
            raise LinkClosed("vom Sensor getrennt")
        return f

    async def close(self):
        if not self.closed:
            self.closed = True
            self.sensor.on_disconnect(self)


class SimRadio(Radio):
    """Hält simulierte Sensoren (simsensor.SimSensor) und verteilt deren Advertising."""
    name = "sim"

    def __init__(self):
        self.sensors = {}
        self.on_adv = None
        self.rssi = {}

    def add(self, sensor):
        self.sensors[sensor.addr] = sensor
        sensor.radio = self
        return sensor

    def advertise(self, sensor, mfr: bytes):
        if self.on_adv:
            adv = P.parse_adv(sensor.addr, sensor.name, {P.COMPANY_ID: mfr}, rssi=sensor.rssi)
            if adv:
                self.on_adv(adv)

    async def start(self, on_adv):
        self.on_adv = on_adv
        for s in self.sensors.values():
            s.start()

    async def stop(self):
        for s in self.sensors.values():
            await s.stop()

    # ---- Simulationshilfen (nur Simulationsmodus)
    def sim_pairing_button(self):
        """Ein ungekoppelter simulierter Sensor geht in den Kopplungsmodus (Taste ≥ 3 s)."""
        for s in self.sensors.values():
            if not s.k_link:
                s.press_button_long()
                return s

    def sim_water(self, addr):
        s = self.sensors.get(addr)
        if s:
            s.water()

    async def connect(self, addr: str) -> Link:
        s = self.sensors.get(addr)
        if not s or not s.connectable():
            raise LinkClosed(f"{addr} nicht verbindbar")
        link = SimLink(s)
        s.on_connect(link)
        return link


# ------------------------------------------------------------------------------------------------ bleak
class BleakLink(Link):  # pragma: no cover - nur mit Hardware
    def __init__(self, client):
        self.client = client
        self.q: asyncio.Queue = asyncio.Queue()
        self.mtu = 247

    def _on_notify(self, _char, data: bytearray):
        self.q.put_nowait(bytes(data))

    def _on_disconnect(self, _client):
        self.q.put_nowait(None)

    async def send(self, frame: bytes, response: bool = True):
        await self.client.write_gatt_char(P.RX_UUID, frame, response=response)

    async def recv(self, timeout: float) -> bytes:
        f = await asyncio.wait_for(self.q.get(), timeout)
        if f is None:
            raise LinkClosed("vom Sensor getrennt")
        return f

    async def close(self):
        try:
            await self.client.disconnect()
        except Exception:  # noqa: BLE001
            pass


class BleakRadio(Radio):  # pragma: no cover - nur mit Hardware
    """BLE-Central über bleak. Scan dauernd (aktiv als Standard; passiv braucht BlueZ-Advertisement-Monitor,
    ANNAHME/PROTOTYP-PRÜFUNG). Filter: Company-ID 0xFFFF + Magic 'fl' (PROTOCOL 2.5 Regel 1)."""
    name = "bleak"

    def __init__(self, adapter: str = "hci0", passive: bool = False, connect_timeout: float = 8.0):
        import bleak  # noqa: F401  (ImportError -> Aufrufer fällt auf Simulation zurück)
        self.adapter = adapter
        self.passive = passive
        self.timeout = connect_timeout
        self.scanner = None
        self.devices = {}

    async def start(self, on_adv):
        from bleak import BleakScanner

        def cb(device, adv):
            a = P.parse_adv(device.address, adv.local_name, adv.manufacturer_data, rssi=adv.rssi)
            if a:
                self.devices[device.address.upper()] = device
                on_adv(a)
        kw = {"detection_callback": cb, "bluez": {"adapter": self.adapter}}
        if self.passive:
            # BlueZ verlangt für passives Scannen ein Muster (or_patterns); hier: Herstellerdaten mit Company-ID 0xFFFF
            from bleak.assigned_numbers import AdvertisementDataType
            from bleak.backends.bluezdbus.advertisement_monitor import OrPattern
            kw["scanning_mode"] = "passive"
            kw["bluez"]["or_patterns"] = [OrPattern(0, AdvertisementDataType.MANUFACTURER_SPECIFIC_DATA, b"\xff\xff\x66\x6c")]
        self.scanner = BleakScanner(**kw)
        await self.scanner.start()
        log.info("BLE-Scan gestartet (%s, %s)", self.adapter, "passiv" if self.passive else "aktiv")

    async def stop(self):
        if self.scanner:
            await self.scanner.stop()

    async def connect(self, addr: str) -> Link:
        from bleak import BleakClient
        dev = self.devices.get(addr.upper(), addr)
        link = None

        def on_disc(c):
            if link:
                link._on_disconnect(c)
        client = BleakClient(dev, disconnected_callback=on_disc, timeout=self.timeout, bluez={"adapter": self.adapter})
        await client.connect()
        link = BleakLink(client)
        try:
            link.mtu = max(23, int(getattr(client, "mtu_size", 247) or 247))
        except Exception:  # noqa: BLE001
            pass
        await client.start_notify(P.TX_UUID, link._on_notify)
        return link


def make_radio(kind: str, **kw) -> Radio:
    if kind == "bleak":
        return BleakRadio(**kw)
    return SimRadio()
