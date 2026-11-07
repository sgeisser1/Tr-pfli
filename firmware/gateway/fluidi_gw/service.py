"""Zusammenbau und Lebenszyklus des Gateway-Dienstes (systemd: install/systemd/fluidi-gateway.service)."""
from __future__ import annotations

import logging
import os
import signal
import socket
import threading
import time

from . import backup, central, climate, config, model, mqtt, server, store, timesvc, transport
from .simsensor import SimSensor

log = logging.getLogger("fluidi")
SIM_PLANTS = [("Monstera", "monstera"), ("Geigenfeige", "ficus_lyrata"), ("Bogenhanf", "sansevieria"),
              ("Efeutute", "epipremnum"), ("Calathea", "calathea"), ("Zitronenbaum", "zitrus"),
              ("Grünlilie", "chlorophytum"), ("Glücksfeder", "zamioculcas")]


def sd_notify(msg: str):
    """systemd-Benachrichtigung (READY=1, WATCHDOG=1) ohne Zusatzpaket."""
    addr = os.environ.get("NOTIFY_SOCKET")
    if not addr:
        return
    if addr.startswith("@"):
        addr = "\0" + addr[1:]
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as s:
            s.connect(addr)
            s.sendall(msg.encode())
    except OSError:
        pass


class Gateway:
    def __init__(self, cfg: config.Config):
        self.cfg = cfg
        cfg.data_dir.mkdir(parents=True, exist_ok=True)
        if backup.apply_pending(cfg.data_dir, cfg.db_path):
            log.warning("Backup eingespielt")
        self.store = store.Store(cfg.db_path)
        sim = cfg.radio == "sim"
        self.time = timesvc.TimeService("sim" if (sim and cfg.time_mode != "system") else cfg.time_mode,
                                        log=lambda *a: self.model.log(*a) if hasattr(self, "model") else None)
        self.model = model.Model(self.store, cfg, self.time, sim=sim)
        if sim:
            self.radio = transport.SimRadio()
        else:
            try:
                self.radio = transport.BleakRadio(adapter=cfg.adapter, passive=cfg.passive_scan)
            except ImportError:
                raise SystemExit("bleak fehlt: pip install -r requirements-pi.txt (oder --sim für den Simulationsmodus)")
        self.central = central.Central(self.model, self.radio, cfg.max_connections)
        self.model.central = self.central
        ck = cfg.climate if cfg.climate != "auto" or not sim else "sim"
        self.climate = climate.Climate(self.store, ck, cfg.i2c_bus, cfg.climate_addr, cfg.climate_interval_s, log=self.model.log)
        self.model.climate = self.climate if self.climate.dev else None
        self.mqtt = mqtt.Mqtt(self.model.gw_name, log=self.model.log)
        self.mqtt.configure(self.model.settings["mqtt"], self.store.meta_get("mqtt_password"))
        self.model.mqtt = self.mqtt
        self.ctl = server.ServerCtl(self.model, cfg)
        self.sims = []
        if sim:
            self._make_sims()

    # ------------------------------------------------------------------ Simulation
    def _make_sims(self):
        n = self.cfg.sim_sensors
        for i in range(n + 1):  # +1 ungekoppelter Sensor für die Kopplung in der PWA
            addr = f"80:6F:B0:5E:{0xA0 + i:02X}:{(0x11 * (i + 1)) & 0xFF:02X}"
            if addr in self.model.by_addr:
                continue
            s = SimSensor(addr, speed=self.cfg.sim_speed, moisture=35 + 6 * i, drying_per_day=0.08 + 0.03 * (i % 4),
                          history_days=self.cfg.sim_history_days if i < n else 0, seed=i)
            self.radio.add(s)
            self.sims.append(s)

    def _autopair(self):
        """Simulation: Sensoren über das echte Kopplungsprotokoll koppeln (SAS automatisch bestätigt) und die
        Zuordnung auf den Beginn des Sensorpuffers zurückdatieren (nur Simulation, damit Verlauf sichtbar ist)."""
        M = self.model
        for i, s in enumerate(self.sims[: self.cfg.sim_sensors]):
            if s.addr in M.by_addr:
                continue
            s.press_button_long()
            M.pairing.update(active=True, until=time.time() + 60, candidates={})
            j = M.new_job("pair", s.name, None, 60)
            name, sp = SIM_PLANTS[i % len(SIM_PLANTS)]
            spec = next((x for x in M.species() if x["key"] == sp), None)
            plant = {"name": name, "substrate": "erde", "species": sp}
            if spec and spec["start_range"]["lower_pct"] is not None:
                plant.update(threshold_pct=spec["start_range"]["lower_pct"], upper_pct=spec["start_range"]["upper_pct"])
            self.central.pair(s.addr, j, {"plant": plant})
            for _ in range(200):
                time.sleep(0.05)
                if j["state"] == "awaiting_confirmation":
                    self.central.confirm_pair(s.addr, True)
                if j["state"] in ("done", "failed", "timeout"):
                    break
            if j["state"] == "done":
                with M.lock:
                    for a in M.assign:
                        if a["sensor"] == s.addr:
                            a["from"] = s.boot_clock
                    M.store.save_assignments(M.assign)
                    M.invalidate()
            else:
                log.warning("Simulation: Kopplung %s: %s", s.addr, j["message"])
        M.pairing.update(active=False, until=None, candidates={})

    # ------------------------------------------------------------------ Lauf
    def start(self):
        self.central.start()
        self.climate.start()
        if self.sims and self.cfg.sim_autopair:
            self._autopair()
        srv = self.ctl.start()
        self.model.log("info", "boot", f"Gateway gestartet ({self.radio.name}, Krypto {__import__('fluidi_gw.crypto', fromlist=['x']).BACKEND})")
        return srv

    def stop(self):
        self.ctl.stop()
        self.climate.stop()
        self.central.stop()
        with self.model.lock:
            self.model.flush_volatile()
        self.store.meta_set("last_stop", "clean")
        self.store.close()


def run(cfg: config.Config):
    logging.basicConfig(level=logging.INFO if not cfg.quiet else logging.WARNING,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    gw = Gateway(cfg)
    srv = gw.start()
    stop = threading.Event()
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda *_: stop.set())
    scheme = "https" if cfg.tls else "http"
    print(f"fluidi Gateway: {scheme}://{cfg.hostname if cfg.tls else 'localhost'}:{srv.server_address[1]}/  (Funk: {gw.radio.name})")
    if gw.model.setup_code:
        print(f"  Ersteinrichtung – Einrichtungscode: {gw.model.setup_code}")
    sd_notify("READY=1")
    wd = int(os.environ.get("WATCHDOG_USEC", "0")) / 2e6
    while not stop.wait(wd or 5):
        if wd and gw.central.thread.is_alive():
            sd_notify("WATCHDOG=1")  # nur solange der Funk-Thread lebt (REQ-FW-07)
    sd_notify("STOPPING=1")
    gw.stop()
