"""Gemeinsame Testhilfen: Gateway mit simulierten Sensoren in einem Temp-Verzeichnis starten."""
from __future__ import annotations

import http.cookiejar
import json
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fluidi_gw import config, service  # noqa: E402
from fluidi_gw.simsensor import SimSensor  # noqa: E402

PASSWORD = "test-passwort-123"


def wait(cond, timeout=10.0, step=0.02):
    t0 = time.time()
    while time.time() - t0 < timeout:
        v = cond()
        if v:
            return v
        time.sleep(step)
    return None


def make_gateway(sensors=2, history_days=5, autopair=True, http=True, **kw):
    d = Path(tempfile.mkdtemp(prefix="fluidi-test-"))
    cfg = config.Config(data_dir=d, radio="sim", tls=False, https_port=0, http_port=0, dashboard_port=kw.pop("dashboard_port", 0), host="127.0.0.1",
                        sim_sensors=sensors, sim_speed=kw.pop("speed", 0.0005), sim_history_days=history_days,
                        sim_autopair=autopair, time_mode="sim", quiet=True, climate=kw.pop("climate", "sim"),
                        pbkdf2_iterations=1000, **kw)
    gw = service.Gateway(cfg)
    srv = gw.start() if http else None
    if not http:
        gw.central.start()
    return gw, srv


class Client:
    def __init__(self, base):
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.csrf = None

    def req(self, method, path, body=None, headers=None, raw=None):
        h = dict(headers or {})
        data = None
        if raw is not None:
            data, h["Content-Type"] = raw, "application/octet-stream"
        elif body is not None:
            data, h["Content-Type"] = json.dumps(body).encode(), "application/json"
        if self.csrf and method != "GET":
            h.setdefault("X-CSRF-Token", self.csrf)
        r = urllib.request.Request(self.base + path, data=data, method=method, headers=h)
        try:
            with self.op.open(r, timeout=15) as res:
                return res.status, dict(res.headers), res.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def json(self, method, path, body=None, **kw):
        st, hd, data = self.req(method, path, body, **kw)
        return st, (json.loads(data) if data and "json" in hd.get("Content-Type", "") else data)

    def setup(self, code, pw=PASSWORD):
        st, js = self.json("POST", "/api/v1/auth/setup", {"setup_code": code, "password": pw})
        if st == 200:
            self.csrf = js["csrf"]
        return st, js

    def login(self, pw=PASSWORD):
        st, js = self.json("POST", "/api/v1/auth/login", {"password": pw})
        if st == 200:
            self.csrf = js["csrf"]
        return st, js

    def job(self, j, timeout=15):
        def done():
            st, x = self.json("GET", f"/api/v1/jobs/{j['id']}")
            return x if x["state"] in ("done", "failed", "timeout", "cancelled", "awaiting_confirmation") else None
        return wait(done, timeout, 0.05)
