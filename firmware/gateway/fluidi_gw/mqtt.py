"""Optional: MQTT-Veröffentlichung + Home-Assistant-Discovery (REQ-SYS-10, Kann; ARCHITECTURE Kap. 10).

Minimaler MQTT-3.1.1-Client (nur Standardbibliothek): CONNECT, PUBLISH QoS 0 mit retain, PINGREQ.
Nur ausgehend zu einem Broker im LAN, keine Abonnements (keine Befehle über MQTT, keine zusätzliche
Angriffsfläche). Standardmässig aus. Topics: <base>/<sensor>/state (JSON), Discovery unter
<prefix>/sensor/fluidi_<id>_<grösse>/config.
"""
from __future__ import annotations

import json
import socket
import ssl
import struct
import threading
import time


def _str(s: str) -> bytes:
    b = s.encode()
    return struct.pack(">H", len(b)) + b


def _len(n: int) -> bytes:
    out = bytearray()
    while True:
        d, n = n % 128, n // 128
        out.append(d | (0x80 if n else 0))
        if not n:
            return bytes(out)


def connect_packet(client_id, user=None, pw=None, keepalive=60) -> bytes:
    flags = 0x02 | (0x80 if user else 0) | (0x40 if pw else 0)
    vh = _str("MQTT") + bytes([4, flags]) + struct.pack(">H", keepalive)
    pl = _str(client_id) + (_str(user) if user else b"") + (_str(pw) if pw else b"")
    return bytes([0x10]) + _len(len(vh) + len(pl)) + vh + pl


def publish_packet(topic, payload: bytes, retain=True) -> bytes:
    body = _str(topic) + payload
    return bytes([0x30 | (1 if retain else 0)]) + _len(len(body)) + body


class Mqtt:
    def __init__(self, gw_name, log=None):
        self.gw = gw_name
        self.cfg = {"enabled": False}
        self.pw = None
        self.sock = None
        self.lock = threading.Lock()
        self.announced = set()
        self.log = log or (lambda *a: None)
        self.last_err = 0.0

    def configure(self, cfg, password=None):
        with self.lock:
            self.cfg, self.pw = dict(cfg), password
            self._close()
            self.announced.clear()

    def _close(self):
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
        self.sock = None

    def _connect(self):
        c = self.cfg
        s = socket.create_connection((c["host"], int(c.get("port", 1883))), timeout=5)
        if c.get("tls"):
            s = ssl.create_default_context().wrap_socket(s, server_hostname=c["host"])
        s.sendall(connect_packet(self.gw, c.get("username") or None, self.pw))
        ack = s.recv(4)
        if len(ack) < 4 or ack[0] != 0x20 or ack[3] != 0:
            s.close()
            raise OSError("MQTT CONNACK abgelehnt")
        self.sock = s

    def _send(self, pkt):
        if not self.sock:
            self._connect()
        try:
            self.sock.sendall(pkt)
        except OSError:
            self._close()
            self._connect()
            self.sock.sendall(pkt)

    def publish_plant(self, plant):
        if not self.cfg.get("enabled") or not self.cfg.get("host") or not plant.get("sensor_id"):
            return
        with self.lock:
            if time.time() - self.last_err < 60:
                return
            try:
                base = self.cfg.get("base_topic", "fluidi")
                sid = plant["sensor_id"]
                topic = f"{base}/{sid}/state"
                if self.cfg.get("discovery", True) and sid not in self.announced:
                    pre = self.cfg.get("discovery_prefix", "homeassistant")
                    for key, unit, dc, tpl in (("moisture", "%", "moisture", "{{ value_json.moisture }}"),
                                               ("temperature", "°C", "temperature", "{{ value_json.temperature }}"),
                                               ("battery", "%", "battery", "{{ value_json.battery }}")):
                        cfg = {"name": f"{plant['name']} {key}", "state_topic": topic, "unit_of_measurement": unit,
                               "device_class": dc, "value_template": tpl, "unique_id": f"fluidi_{sid}_{key}",
                               "device": {"identifiers": [f"fluidi_{sid}"], "name": f"fluidi {plant['name']}", "manufacturer": "fluidi"}}
                        self._send(publish_packet(f"{pre}/sensor/fluidi_{sid.replace('-', '_')}_{key}/config", json.dumps(cfg).encode()))
                    self.announced.add(sid)
                L = plant.get("latest") or {}
                st = {"moisture": L.get("moisture_pct"), "state": L.get("moisture_state"), "temperature": L.get("temp_c"),
                      "battery": (plant.get("battery") or {}).get("pct"), "rssi": (plant.get("signal") or {}).get("rssi_dbm"),
                      "needs_water": plant["status"]["needs_water"], "mood": plant.get("mood")}
                self._send(publish_packet(topic, json.dumps(st).encode()))
            except OSError as e:
                self.last_err = time.time()
                self._close()
                self.log("warn", "mqtt", f"MQTT nicht erreichbar: {e}")
