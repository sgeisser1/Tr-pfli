#!/usr/bin/env python3
"""fluidi – Mock-Gateway für die PWA-Entwicklung (nur Python-Standardbibliothek).

Bedient die API nach app/api/openapi.yaml mit realistischen Testdaten (8 Pflanzen, 1 Jahr
Verlauf) und liefert die PWA aus app/ aus – gleiche Herkunft wie später auf dem Gateway.

    python3 app/dev/mock_server.py                 # http://localhost:8080, Passwort fluidi-demo-2026
    python3 app/dev/mock_server.py --fresh         # Ersteinrichtung mit Einrichtungscode
    python3 app/dev/mock_server.py --port 9000 --host 0.0.0.0

Nur für die Entwicklung: kein TLS, Backups unverschlüsselt, Signaturprüfung simuliert.
Optional (wenn PyYAML und jsonschema installiert sind): Request-Bodies werden gegen die
OpenAPI-Schemas geprüft (wie später das Gateway); sonst nur die Prüfungen im Code.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import hmac
import io
import json
import math
import mimetypes
import os
import queue
import random
import re
import secrets
import sys
import threading
import time
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fluidi_calc as C  # noqa: E402

APP_DIR = Path(__file__).resolve().parent.parent
OPENAPI = APP_DIR / "api" / "openapi.yaml"
STATIC_ALLOW = {"index.html", "manifest.webmanifest", "sw.js", "favicon.ico"}
STATIC_DIRS = {"css", "js", "vendor", "icons", "img"}
API = "/api/v1"
CSP = ("default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data: blob:; "
       "connect-src 'self'; manifest-src 'self'; worker-src 'self'; object-src 'none'; "
       "frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
GATEWAY_ID = "fluidi-gw-3F9A"
VERSION = "0.4.0-mock"
SESSION_SHORT = 12 * 3600
SESSION_LONG = 30 * 86400
ELEVATE_S = 300
LOCK_AFTER = 5
LOCK_BASE_S = 60
LOCK_MAX_S = 900
GLOBAL_FAILS_PER_MIN = 20

mimetypes.add_type("application/manifest+json", ".webmanifest")
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("image/svg+xml", ".svg")


def now() -> float:
    return time.time()


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, field: str | None = None, retry_after: int | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.field, self.retry_after = status, code, message, field, retry_after

    def body(self):
        e = {"code": self.code, "message": self.message}
        if self.field:
            e["field"] = self.field
        if self.retry_after is not None:
            e["retry_after_s"] = self.retry_after
        return {"error": e}


# --------------------------------------------------------------------------------------------
# Optionale Schemaprüfung aus openapi.yaml
# --------------------------------------------------------------------------------------------
class SchemaCheck:
    def __init__(self):
        self.ok = False
        try:
            import yaml  # type: ignore
            import jsonschema  # type: ignore
        except Exception:
            return
        self.spec = yaml.safe_load(OPENAPI.read_text(encoding="utf-8"))
        self.js = jsonschema
        self.ok = True

    def _schema(self, sch):
        # $ref auf components auflösen: einfache Einbettung als Draft-2020-12-Dokument
        return {"$schema": "https://json-schema.org/draft/2020-12/schema",
                "components": self.spec["components"], **sch}

    def request(self, method: str, path_tpl: str, body):
        if not self.ok:
            return
        op = self.spec["paths"].get(path_tpl, {}).get(method.lower())
        if not op or "requestBody" not in op:
            return
        content = op["requestBody"].get("content", {})
        if "application/json" not in content:
            return
        sch = self._schema(content["application/json"]["schema"])
        v = self.js.Draft202012Validator(sch)
        errs = sorted(v.iter_errors(body), key=lambda e: list(e.path))
        if errs:
            e = errs[0]
            field = ".".join(str(p) for p in e.path) or None
            raise ApiError(400, "validation", f"Ungültige Eingabe: {e.message}", field)


# --------------------------------------------------------------------------------------------
# Zustand und Testdaten
# --------------------------------------------------------------------------------------------
class State:
    def __init__(self, seed: int, fresh: bool, password: str):
        self.lock = threading.RLock()
        self.rng = random.Random(seed)
        self.tz = ZoneInfo("Europe/Zurich")
        self.events_log: list[dict] = []
        self.sse_clients: list[queue.Queue] = []
        self.sse_id = 0
        self.jobs: dict[str, dict] = {}
        self.runs: dict[str, dict] = {}
        self.sessions: dict[str, dict] = {}
        self.fails: dict[str, dict] = {}
        self.global_fails: list[float] = []
        self.setup_code = None
        self.pw_salt = secrets.token_bytes(16)
        self.pw_hash = None
        if fresh:
            self.setup_code = f"{self.rng.randint(0, 999):03d}-{self.rng.randint(0, 999):03d}"
        else:
            self.pw_hash = self._hash(password)
        self.settings = {
            "interval_per_day": 6,
            "reaction_time_min": 1,
            "default_threshold_pct": 30,
            "led": {"enabled": True, "water_hint": True, "brightness": "normal",
                    "water_window": {"start": "08:00", "end": "18:00", "weekdays": [1, 2, 3, 4, 5]}},
            "time": {"ntp_enabled": True, "ntp_server": "pool.ntp.org", "timezone": "Europe/Zurich"},
            "public_read": True,
            "mqtt": {"enabled": False, "host": "", "port": 1883, "tls": False, "username": "",
                     "password_set": False, "base_topic": "fluidi", "discovery": True,
                     "discovery_prefix": "homeassistant"},
        }
        self.network = {"ssid": "Buero-WLAN", "connected": True, "rssi_dbm": -58, "ip": "192.168.10.47",
                        "hostname": "fluidi.local", "mdns": True, "pending_change": None}
        self.boot = now()
        self.sensor_images = [{"version": "1.0.3", "security_counter": 3, "size": 187_904,
                               "sha256": hashlib.sha256(b"fluidi-sensor-1.0.3").hexdigest(),
                               "signature_ok": True, "hw_compat": "A-32 rev A",
                               "uploaded": C.iso(now() - 3 * 86400)}]
        self.rollout = None
        self.pairing = {"active": False, "until": None, "candidates": []}
        self.plants: dict[int, dict] = {}
        self.sensors: dict[str, dict] = {}
        self.cal: dict[str, dict] = {}
        self.records: dict[str, list] = {}
        self.assign: list[dict] = []
        self.next_plant = 1
        self._generate()
        self.log("info", "boot", "Gateway gestartet (Mock)")

    # ---------------------------------------------------------------- Hilfen
    def _hash(self, pw: str) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", pw.encode(), self.pw_salt, 100_000)

    def log(self, level, code, text, sensor_id=None):
        e = {"id": len(self.events_log) + 1, "t": C.iso(now()), "level": level, "code": code,
             "text": text, "sensor_id": sensor_id}
        self.events_log.append(e)

    def emit(self, event: str, data):
        with self.lock:
            self.sse_id += 1
            msg = f"id: {self.sse_id}\nevent: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            for q in list(self.sse_clients):
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    pass

    # ---------------------------------------------------------------- Testdaten
    def _generate(self):
        r = self.rng
        t_end = now()
        specs = [
            # name, substrate, threshold, sensor, start moisture now, drying %/d, extras
            ("Monstera", "erde", 30, "fluidi-1A2B", 58, 5.0, {}),
            ("Ficus lyrata", "erde", 35, "fluidi-2C4D", 27, 6.0, {}),
            ("Bogenhanf", "granulat", 15, "fluidi-3E5F", 41, 3.0, {"battery": (2610, 12, 21)}),
            ("Efeutute", "erde", 30, "fluidi-4A61", 71, 7.0, {"rssi": -91}),
            ("Kaktus Fensterbank", "granulat", 10, "fluidi-5B72", 22, 2.5, {"default_cal": True, "sun": True}),
            ("Zitronenbaum", "erde", 40, "fluidi-6C83", 50, 6.5, {"air": True}),
            ("Calathea", "erde", 45, "fluidi-7D94", 62, 8.0, {"stale_h": 52}),
            ("Orchidee", "granulat", 20, None, None, 0, {}),
        ]
        for name, sub, thr, sid, m_now, rate, ex in specs:
            pid = self.next_plant
            self.next_plant += 1
            self.plants[pid] = {"id": pid, "name": name, "substrate": sub, "threshold_pct": thr,
                                "water_led": "inherit", "notes": "", "sensor_id": sid,
                                "created": C.iso(t_end - 400 * 86400)}
            if not sid:
                continue
            true_dry = (41000 if sub == "erde" else 42500) + r.uniform(-800, 800)
            true_wet = (26000 if sub == "erde" else 30000) + r.uniform(-600, 600)
            mv, pct, days = ex.get("battery", (2950 - r.randint(0, 120), r.randint(55, 92), r.randint(180, 420)))
            last_offset = ex.get("stale_h", 0) * 3600
            self.sensors[sid] = {
                "id": sid, "plant_id": pid, "hw_rev": "A-32 rev A", "fw_version": "1.0.2",
                "paired": C.iso(t_end - 365 * 86400), "last_seen": t_end - last_offset - r.randint(60, 2400),
                "battery": {"mv": mv, "pct": pct, "days_left": days,
                            "state": "critical" if days < 7 else "low" if days < 30 else "ok"},
                "rssi": ex.get("rssi", r.randint(-79, -60)), "interval_per_day": None, "led_enabled": True,
                "pending_config": False, "error": None, "unpairing": False,
                "true": {"dry": true_dry, "wet": true_wet, "k": 0.0015},
                "buffered_records": 0,
            }
            if ex.get("default_cal"):
                cal_src, dry, wet = "default", (41000 if sub == "erde" else 42000), (26000 if sub == "erde" else 29000)
            else:
                cal_src, dry, wet = "guided", true_dry + r.uniform(-150, 150), true_wet + r.uniform(-150, 150)
            self.cal[sid] = {}
            for s2 in ("erde", "granulat"):
                if s2 == sub:
                    self.cal[sid][s2] = self._cal(s2, cal_src, dry, wet, t_end - 360 * 86400 if cal_src != "default" else None)
                else:
                    self.cal[sid][s2] = self._default_cal(s2)
            self.assign.append({"sensor": sid, "plant": pid, "from": t_end - 365 * 86400, "to": None})
            self.records[sid] = self._history(sid, sub, m_now, rate, t_end - last_offset, ex)
        self.sensors["fluidi-7D94"]["buffered_records"] = None  # unbekannt: seit 52 h kein Kontakt

    def _default_cal(self, sub):
        dry, wet = (41000, 26000) if sub == "erde" else (42000, 29000)
        return self._cal(sub, "default", dry, wet, None)

    @staticmethod
    def _cal(sub, source, dry, wet, t):
        return {"substrate": sub, "source": source,
                "dry": {"raw": round(dry), "temp_c": 21.0 if t else None, "n": 5 if t else 0, "stddev": 18.0 if t else None},
                "wet": {"raw": round(wet), "temp_c": 21.0 if t else None, "n": 5 if t else 0, "stddev": 22.0 if t else None},
                "temp_coeff_per_k": 0.0, "t_ref_c": C.T_REF_C, "updated": C.iso(t) if t else None}

    def _raw_from(self, sid, moisture, temp):
        tr = self.sensors[sid]["true"]
        raw_ref = tr["dry"] + (tr["wet"] - tr["dry"]) * moisture / 100.0
        raw = raw_ref * (1 + tr["k"] * (temp - 20.0))
        return int(round(raw * (1 + self.rng.gauss(0, 0.0015))))

    def _temp_at(self, t, sun=False):
        lt = datetime.fromtimestamp(t, self.tz)
        doy = lt.timetuple().tm_yday
        season = 1.5 * math.sin((doy - 110) / 365 * 2 * math.pi)
        diurnal = 1.6 * math.sin((lt.hour + lt.minute / 60 - 9) / 24 * 2 * math.pi)
        temp = 21.0 + season + diurnal + self.rng.gauss(0, 0.15)
        if sun and 11 <= lt.hour <= 15 and doy % 3:
            temp += 6 + 3 * math.sin((lt.hour - 11) / 4 * math.pi)
        return round(temp, 2)

    def _history(self, sid, sub, m_now, rate, t_last, ex):
        """Rückwärts von „jetzt“: Feuchte steigt rückwärts (trocknet vorwärts), Giessen = Sprung."""
        r = self.rng
        per_day = 6
        step = 86400 / per_day
        t = t_last - (t_last % step)
        m = float(m_now)
        recs = []
        water_at = r.uniform(75, 90)
        while t > t_last - 365 * 86400:
            lt = datetime.fromtimestamp(t, self.tz)
            seasonal = 1.0 + 0.35 * math.sin((lt.timetuple().tm_yday - 110) / 365 * 2 * math.pi)
            temp = self._temp_at(t, ex.get("sun", False))
            recs.append({"t": int(t), "raw": self._raw_from(sid, m, temp), "temp": temp, "flags": 0, "source": "auto"})
            m += rate * seasonal / per_day * r.uniform(0.7, 1.3)
            if m >= water_at:  # rückwärts betrachtet: vor dem Giessen war es trocken
                m = r.uniform(8, 34)
                water_at = r.uniform(72, 92)
            t -= step
        recs.reverse()
        # einige manuelle Messungen und nachgelieferte Werte (Gateway-Ausfall)
        for rec in recs[::37]:
            rec["source"] = "manual"
            rec["flags"] |= 1
        for rec in recs[len(recs) // 3: len(recs) // 3 + 30]:
            rec["flags"] |= 8
        if ex.get("air"):
            for rec in recs[-2:]:
                rec["raw"] = int(self.sensors[sid]["true"]["dry"] * 1.06)
        return recs

    # ---------------------------------------------------------------- Ableitungen
    def per_day(self, sid=None):
        s = self.sensors.get(sid) if sid else None
        if s and s["interval_per_day"]:
            return s["interval_per_day"]
        return self.settings["interval_per_day"]

    def reading(self, sid, rec, plant):
        cal = self.cal[sid][plant["substrate"]]
        ev = C.evaluate(rec["raw"], rec["temp"], cal, plant["threshold_pct"])
        tq = "reconstructed" if rec["flags"] & 2 else "unsynced" if rec["flags"] & 4 else "ok"
        return {"t": C.iso(rec["t"]), **ev, "raw": rec["raw"], "temp_c": rec["temp"],
                "time_quality": tq, "source": rec["source"]}

    def plant_records(self, pid, t0, t1):
        out = []
        for a in self.assign:
            if a["plant"] != pid:
                continue
            lo, hi = max(t0, a["from"]), min(t1, a["to"] if a["to"] else t1)
            for rec in self.records.get(a["sensor"], []):
                if lo <= rec["t"] <= hi:
                    out.append((a["sensor"], rec))
        out.sort(key=lambda x: x[1]["t"])
        return out

    def last_record(self, pid):
        best = None
        for a in self.assign:
            if a["plant"] != pid:
                continue
            recs = self.records.get(a["sensor"], [])
            for rec in reversed(recs):
                if a["from"] <= rec["t"] <= (a["to"] or 1e12):
                    if best is None or rec["t"] > best[1]["t"]:
                        best = (a["sensor"], rec)
                    break
        return best

    def battery_out(self, s):
        return dict(s["battery"]) if s else None

    def signal_out(self, s):
        if not s or s["rssi"] is None:
            return None
        return {"rssi_dbm": s["rssi"], "quality": C.signal_quality(s["rssi"])}

    def plant_out(self, p):
        sid = p["sensor_id"]
        s = self.sensors.get(sid) if sid else None
        lr = self.last_record(p["id"])
        latest = self.reading(lr[0], lr[1], p) if lr else None
        last_t = lr[1]["t"] if lr else None
        stale = bool(sid) and C.is_stale(last_t, now(), self.per_day(sid))
        cal_state = "none"
        if s:
            cal_state = "default" if self.cal[sid][p["substrate"]]["source"] == "default" else "calibrated"
        return {
            "id": p["id"], "name": p["name"], "substrate": p["substrate"], "threshold_pct": p["threshold_pct"],
            "water_led": p["water_led"], "notes": p["notes"], "sensor_id": sid, "latest": latest,
            "status": {"needs_water": bool(latest and latest["moisture_state"] == "dry"),
                       "stale": stale,
                       "battery_low": bool(s and s["battery"]["state"] != "ok"),
                       "sensor_error": (s["error"]["text"] if s and s["error"] else None)},
            "battery": self.battery_out(s), "signal": self.signal_out(s),
            "calibration": cal_state, "created": p["created"],
        }

    def sensor_out(self, s):
        return {
            "id": s["id"], "plant_id": s["plant_id"], "hw_rev": s["hw_rev"], "fw_version": s["fw_version"],
            "paired": s["paired"], "last_seen": C.iso(s["last_seen"]) if s["last_seen"] else None,
            "battery": self.battery_out(s), "signal": self.signal_out(s),
            "interval_per_day": s["interval_per_day"], "effective_interval_per_day": self.per_day(s["id"]),
            "led_enabled": s["led_enabled"], "pending_config": s["pending_config"],
            "buffered_records": s["buffered_records"], "error": s["error"], "unpairing": s["unpairing"],
        }

    def reachable(self, sid):
        s = self.sensors.get(sid)
        return bool(s) and (now() - s["last_seen"]) < 6 * 3600

    # ---------------------------------------------------------------- Jobs
    def new_job(self, kind, sensor_id=None, plant_id=None, timeout_s=None):
        jid = "j" + secrets.token_hex(4)
        timeout_s = timeout_s or self.settings["reaction_time_min"] * 60 + 30
        j = {"id": jid, "kind": kind, "state": "queued", "sensor_id": sensor_id, "plant_id": plant_id,
             "created": C.iso(now()), "deadline": C.iso(now() + timeout_s), "progress": None,
             "message": "Auftrag angenommen", "result": None}
        self.jobs[jid] = j
        return j

    def job_update(self, j, **kw):
        with self.lock:
            j.update(kw)
            self.emit("job", j)

    def run_measure(self, j, pid, sid, source="manual", on_done=None, samples=1):
        def step1():
            self.job_update(j, state="waiting_for_sensor", message="Warte auf Sensor (nächstes Funksignal)")
            if not self.reachable(sid):
                threading.Timer(8.0, lambda: self.job_update(
                    j, state="timeout", message="Sensor hat innert Reaktionszeit nicht geantwortet")).start()
                return
            threading.Timer(self.rng.uniform(2.0, 5.0), step2).start()

        def step2():
            self.job_update(j, state="running", message="Sensor misst", progress=0.5)
            threading.Timer(1.5, step3).start()

        def step3():
            with self.lock:
                p = self.plants.get(pid)
                s = self.sensors.get(sid)
                if not s:
                    self.job_update(j, state="failed", message="Sensor nicht mehr gekoppelt")
                    return
                if on_done:
                    res = on_done()
                    self.job_update(j, state="done", progress=1.0, message="Messung abgeschlossen", result=res)
                    return
                last = self.records[sid][-1]
                if p and p["name"] == "Zitronenbaum":
                    moist_raw = last["raw"]
                    temp = self._temp_at(now())
                else:
                    tr = s["true"]
                    m_prev = (last["raw"] / (1 + tr["k"] * (last["temp"] - 20)) - tr["dry"]) / (tr["wet"] - tr["dry"]) * 100
                    temp = self._temp_at(now())
                    moist_raw = self._raw_from(sid, max(0.0, m_prev - 0.2), temp)
                rec = {"t": int(now()), "raw": moist_raw, "temp": temp, "flags": 1, "source": source}
                self.records[sid].append(rec)
                s["last_seen"] = now()
                reading = self.reading(sid, rec, p) if p else None
                self.job_update(j, state="done", progress=1.0, message="Neuer Messwert empfangen",
                                result={"reading": reading})
                if p:
                    self.emit("measurement", {"plant_id": pid, "sensor_id": sid, "reading": reading})
                    self.emit("plant", self.plant_out(p))

        threading.Timer(0.6, step1).start()


# --------------------------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------------------------
ROUTES: list = []


def route(method, tpl, *, auth="write", elevated=False):
    """auth: 'public' = immer, 'read' = public_read oder Sitzung, 'session' = Sitzung, 'write' = Sitzung+CSRF."""
    rx = re.compile("^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", tpl) + "$")

    def deco(fn):
        ROUTES.append((method, tpl, rx, fn, auth, elevated))
        return fn
    return deco


class Handler(BaseHTTPRequestHandler):
    server_version = "fluidi-mock/" + VERSION
    protocol_version = "HTTP/1.1"
    S: State = None  # type: ignore
    CHECK: SchemaCheck = None  # type: ignore
    HTTPS = False
    QUIET = False
    DEMO = False  # --demo-session: jede Anfrage gilt als angemeldet (nur für Screenshots)

    def log_message(self, fmt, *args):
        if not self.QUIET:
            sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    # ------------------------------------------------------------ Antworten
    def _common_headers(self):
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("Permissions-Policy", "camera=(), microphone=(), geolocation=()")

    def send_json(self, status, obj, headers=None):
        data = b"" if obj is None else json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self._common_headers()
        if obj is not None:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def send_bytes(self, status, data: bytes, ctype, headers=None):
        self.send_response(status)
        self._common_headers()
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    # ------------------------------------------------------------ Verteiler
    def do_GET(self):
        self._dispatch()

    def do_HEAD(self):
        self._dispatch()

    def do_POST(self):
        self._dispatch()

    def do_PUT(self):
        self._dispatch()

    def do_PATCH(self):
        self._dispatch()

    def do_DELETE(self):
        self._dispatch()

    def _dispatch(self):
        url = urlsplit(self.path)
        try:
            if url.path.startswith(API + "/") or url.path == API:
                self._api(url)
            elif self.command in ("GET", "HEAD"):
                self._static(url.path)
            else:
                raise ApiError(405, "bad_request", "Methode nicht erlaubt")
        except ApiError as e:
            h = {"Retry-After": str(e.retry_after)} if e.retry_after is not None else None
            self.send_json(e.status, e.body(), h)
        except BrokenPipeError:
            pass
        except Exception as e:  # pragma: no cover
            import traceback
            traceback.print_exc()
            self.send_json(500, {"error": {"code": "internal", "message": f"Interner Fehler: {e}"}})

    def _static(self, path):
        if path in ("", "/"):
            path = "/index.html"
        rel = path.lstrip("/")
        parts = rel.split("/")
        if ".." in parts or not (rel in STATIC_ALLOW or parts[0] in STATIC_DIRS):
            # SPA: unbekannte Pfade ohne Punkt -> index.html (Hash-Router braucht das nicht, schadet nicht)
            raise ApiError(404, "not_found", "Nicht gefunden")
        f = (APP_DIR / rel).resolve()
        if not str(f).startswith(str(APP_DIR)) or not f.is_file():
            raise ApiError(404, "not_found", "Nicht gefunden")
        data = f.read_bytes()
        ctype = mimetypes.guess_type(str(f))[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/json", "application/manifest+json", "image/svg+xml"):
            ctype += "; charset=utf-8"
        headers = {"Cache-Control": "no-cache"}
        if rel == "sw.js":
            headers["Service-Worker-Allowed"] = "/"
        etag = '"' + hashlib.sha256(data).hexdigest()[:16] + '"'
        headers["ETag"] = etag
        if self.headers.get("If-None-Match") == etag:
            self.send_response(304)
            self._common_headers()
            for k, v in headers.items():
                self.send_header(k, v)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        if "gzip" in (self.headers.get("Accept-Encoding") or "") and len(data) > 1024 and not ctype.startswith("image/png"):
            data = gzip.compress(data, 6)
            headers["Content-Encoding"] = "gzip"
            headers["Vary"] = "Accept-Encoding"
        self.send_bytes(200, data, ctype, headers)

    # ------------------------------------------------------------ Auth-Hilfen
    def client_ip(self):
        return self.client_address[0]

    def session(self):
        c = self.headers.get("Cookie") or ""
        m = re.search(r"(?:^|;\s*)fluidi_sid=([A-Za-z0-9_\-]+)", c)
        if not m:
            if self.DEMO:
                return "demo", {"csrf": "demo", "expires": now() + 3600, "elevated_until": now() + 3600}
            return None, None
        tok = m.group(1)
        s = self.S.sessions.get(tok)
        if not s or s["expires"] < now():
            self.S.sessions.pop(tok, None)
            return None, None
        return tok, s

    def _check_auth(self, auth, elevated):
        tok, s = self.session()
        if auth == "public":
            return s
        if auth == "read":
            if self.S.settings["public_read"] or s:
                return s
            raise ApiError(401, "auth_required", "Bitte anmelden")
        if not s:
            raise ApiError(401, "auth_required", "Bitte anmelden")
        if auth == "write":
            if not hmac.compare_digest(self.headers.get("X-CSRF-Token") or "", s["csrf"]):
                raise ApiError(403, "csrf", "Sicherheitsprüfung fehlgeschlagen, Seite neu laden")
            origin = self.headers.get("Origin")
            if origin and urlsplit(origin).netloc != (self.headers.get("Host") or ""):
                raise ApiError(403, "forbidden", "Fremde Herkunft abgelehnt")
        if elevated and (s.get("elevated_until") or 0) < now():
            raise ApiError(403, "elevation_required", "Bitte Passwort erneut bestätigen")
        return s

    def _read_body(self):
        n = int(self.headers.get("Content-Length") or 0)
        if n > 2 * 1024 * 1024:
            raise ApiError(413, "too_large", "Datei zu gross")
        return self.rfile.read(n) if n else b""

    def _api(self, url):
        sub = url.path[len(API):] or "/"
        for method, tpl, rx, fn, auth, elevated in ROUTES:
            m = rx.match(sub)
            if not m:
                continue
            if method != self.command and not (self.command == "HEAD" and method == "GET"):
                continue
            sess = self._check_auth(auth, elevated)
            raw = self._read_body() if self.command in ("POST", "PUT", "PATCH", "DELETE") else b""
            ctype = (self.headers.get("Content-Type") or "").split(";")[0].strip()
            body = None
            if raw and ctype == "application/json":
                try:
                    body = json.loads(raw)
                except ValueError:
                    raise ApiError(400, "bad_request", "Ungültiges JSON")
                self.CHECK.request(method, tpl, body)
            elif raw and ctype not in ("application/octet-stream",):
                raise ApiError(415 if ctype else 400, "bad_request", "Content-Type muss application/json sein")
            q = {k: v[-1] for k, v in parse_qs(url.query).items()}
            with self.S.lock:
                return fn(self, sess=sess, q=q, body=body if body is not None else ({} if not raw else raw), **m.groupdict())
        # Pfad passt, Methode nicht?
        if any(rx.match(sub) for _, _, rx, *_ in ROUTES):
            raise ApiError(405, "bad_request", "Methode nicht erlaubt")
        raise ApiError(404, "not_found", "Unbekannter Endpunkt")

    # ------------------------------------------------------------ Login-Sperre
    def _lock_check(self):
        S = self.S
        t = now()
        S.global_fails = [x for x in S.global_fails if t - x < 60]
        f = S.fails.get(self.client_ip())
        if f and f.get("until", 0) > t:
            ra = int(math.ceil(f["until"] - t))
            raise ApiError(429, "locked", f"Zu viele Fehlversuche. Bitte {ra} s warten.", retry_after=ra)
        if len(S.global_fails) >= GLOBAL_FAILS_PER_MIN:
            raise ApiError(429, "locked", "Zu viele Fehlversuche im Netz. Bitte 60 s warten.", retry_after=60)

    def _lock_fail(self):
        S = self.S
        t = now()
        S.global_fails.append(t)
        f = S.fails.setdefault(self.client_ip(), {"n": 0, "until": 0})
        f["n"] += 1
        if f["n"] >= LOCK_AFTER:
            f["until"] = t + min(LOCK_MAX_S, LOCK_BASE_S * 2 ** (f["n"] - LOCK_AFTER))
        S.log("warn", "login_failed", f"Anmeldung fehlgeschlagen von {self.client_ip()} ({f['n']}×)")

    def _new_session(self, remember=False, elevate=True):
        tok = secrets.token_urlsafe(24)
        life = SESSION_LONG if remember else SESSION_SHORT
        s = {"csrf": secrets.token_urlsafe(18), "expires": now() + life,
             "elevated_until": now() + ELEVATE_S if elevate else None, "remember": remember}
        self.S.sessions[tok] = s
        self.S.fails.pop(self.client_ip(), None)
        cookie = f"fluidi_sid={tok}; Path=/; HttpOnly; SameSite=Strict"
        if remember:
            cookie += f"; Max-Age={life}"
        if self.HTTPS:
            cookie += "; Secure"
        return s, {"Set-Cookie": cookie}

    @staticmethod
    def session_body(s):
        return {"csrf": s["csrf"], "expires": C.iso(s["expires"]),
                "elevated_until": C.iso(s["elevated_until"]) if s.get("elevated_until") and s["elevated_until"] > now() else None}


def _plant(S: State, plant_id) -> dict:
    try:
        p = S.plants.get(int(plant_id))
    except ValueError:
        p = None
    if not p:
        raise ApiError(404, "not_found", "Pflanze nicht gefunden")
    return p


def _sensor(S: State, sid) -> dict:
    s = S.sensors.get(sid)
    if not s:
        raise ApiError(404, "not_found", "Sensor nicht gefunden")
    return s


def _int(q, k, default=None, lo=None, hi=None):
    if k not in q or q[k] == "":
        if default is None:
            raise ApiError(400, "validation", f"Parameter {k} fehlt", k)
        return default
    try:
        v = int(q[k])
    except ValueError:
        raise ApiError(400, "validation", f"Parameter {k} ist keine Zahl", k)
    if (lo is not None and v < lo) or (hi is not None and v > hi):
        raise ApiError(400, "validation", f"Parameter {k} ausserhalb des Bereichs", k)
    return v


# ------------------------------------------------------------------------------ Auth
@route("GET", "/auth/status", auth="public")
def auth_status(h: Handler, sess, **_):
    S = h.S
    f = S.fails.get(h.client_ip(), {})
    locked_for = max(0, int(math.ceil(f.get("until", 0) - now())))
    h.send_json(200, {
        "setup_required": S.pw_hash is None, "logged_in": bool(sess),
        "elevated_until": C.iso(sess["elevated_until"]) if sess and sess.get("elevated_until") and sess["elevated_until"] > now() else None,
        "session_expires": C.iso(sess["expires"]) if sess else None,
        "csrf": sess["csrf"] if sess else None, "public_read": S.settings["public_read"],
        "lockout": {"locked": locked_for > 0, "retry_after_s": locked_for, "failed_attempts": f.get("n", 0)},
    })


@route("POST", "/auth/setup", auth="public")
def auth_setup(h: Handler, body, **_):
    S = h.S
    if S.pw_hash is not None:
        raise ApiError(409, "setup_done", "Das Gateway ist bereits eingerichtet")
    h._lock_check()
    code = str(body.get("setup_code", "")).replace("-", "")
    if not hmac.compare_digest(code, (S.setup_code or "").replace("-", "")):
        h._lock_fail()
        raise ApiError(401, "auth_failed", "Einrichtungscode falsch")
    pw = body.get("password", "")
    if len(pw) < 10:
        raise ApiError(400, "validation", "Passwort: mindestens 10 Zeichen", "password")
    S.pw_hash = S._hash(pw)
    S.setup_code = None
    S.log("info", "setup", "Passwort gesetzt (Ersteinrichtung)")
    s, hdr = h._new_session()
    h.send_json(200, h.session_body(s), hdr)


@route("POST", "/auth/login", auth="public")
def auth_login(h: Handler, body, **_):
    S = h.S
    if S.pw_hash is None:
        raise ApiError(409, "setup_required", "Bitte zuerst das Gateway einrichten")
    h._lock_check()
    if not hmac.compare_digest(S._hash(str(body.get("password", ""))), S.pw_hash):
        h._lock_fail()
        f = S.fails.get(h.client_ip(), {})
        left = max(0, LOCK_AFTER - f.get("n", 0))
        msg = "Passwort falsch" + (f" (noch {left} Versuche bis zur Sperre)" if left else "")
        raise ApiError(401, "auth_failed", msg)
    s, hdr = h._new_session(bool(body.get("remember")))
    S.log("info", "login", f"Anmeldung von {h.client_ip()}")
    h.send_json(200, h.session_body(s), hdr)


@route("POST", "/auth/logout", auth="session")
def auth_logout(h: Handler, **_):
    tok, _s = h.session()
    h.S.sessions.pop(tok, None)
    h.send_json(204, None, {"Set-Cookie": "fluidi_sid=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict"})


@route("POST", "/auth/elevate", auth="write")
def auth_elevate(h: Handler, sess, body, **_):
    h._lock_check()
    if not hmac.compare_digest(h.S._hash(str(body.get("password", ""))), h.S.pw_hash):
        h._lock_fail()
        raise ApiError(401, "auth_failed", "Passwort falsch")
    sess["elevated_until"] = now() + ELEVATE_S
    h.send_json(200, h.session_body(sess))


@route("POST", "/auth/password", elevated=True)
def auth_password(h: Handler, sess, body, **_):
    pw = body.get("new_password", "")
    if len(pw) < 10:
        raise ApiError(400, "validation", "Passwort: mindestens 10 Zeichen", "new_password")
    S = h.S
    S.pw_hash = S._hash(pw)
    tok, _ = h.session()
    for k in list(S.sessions):
        if k != tok:
            S.sessions.pop(k)
    S.log("info", "password", "Passwort geändert, andere Sitzungen beendet")
    h.send_json(204, None)


# ------------------------------------------------------------------------------ Pflanzen
@route("GET", "/plants", auth="read")
def plants_list(h: Handler, **_):
    h.send_json(200, [h.S.plant_out(p) for p in sorted(h.S.plants.values(), key=lambda p: p["name"].lower())])


def _create_plant(S: State, body) -> dict:
    name = str(body.get("name", "")).strip()
    if not name:
        raise ApiError(400, "validation", "Name fehlt", "name")
    sid = body.get("sensor_id")
    if sid:
        _sensor(S, sid)
        if S.sensors[sid]["plant_id"]:
            raise ApiError(409, "conflict", "Sensor ist bereits einer Pflanze zugeordnet")
    pid = S.next_plant
    S.next_plant += 1
    p = {"id": pid, "name": name, "substrate": body.get("substrate", "erde"),
         "threshold_pct": body.get("threshold_pct", S.settings["default_threshold_pct"]),
         "water_led": body.get("water_led", "inherit"), "notes": body.get("notes", ""),
         "sensor_id": None, "created": C.iso(now())}
    S.plants[pid] = p
    if sid:
        _assign(S, p, sid, False)
    return p


def _assign(S: State, p, sid, move_history):
    t = now()
    # alten Sensor der Pflanze lösen
    if p["sensor_id"]:
        old = S.sensors.get(p["sensor_id"])
        for a in S.assign:
            if a["plant"] == p["id"] and a["to"] is None:
                a["to"] = t
        if old:
            old["plant_id"] = None
        p["sensor_id"] = None
    if sid is None:
        return
    s = _sensor(S, sid)
    if s["plant_id"] and s["plant_id"] != p["id"]:
        other = S.plants[s["plant_id"]]
        for a in S.assign:
            if a["sensor"] == sid and a["to"] is None:
                a["to"] = t
        other["sensor_id"] = None
    if move_history:
        for a in S.assign:
            if a["sensor"] == sid:
                a["plant"] = p["id"]
    S.assign.append({"sensor": sid, "plant": p["id"], "from": t, "to": None})
    s["plant_id"] = p["id"]
    p["sensor_id"] = sid
    s["pending_config"] = True


@route("POST", "/plants")
def plants_create(h: Handler, body, **_):
    p = _create_plant(h.S, body)
    h.S.emit("plant", h.S.plant_out(p))
    h.send_json(201, h.S.plant_out(p))


@route("GET", "/plants/{plant_id}", auth="read")
def plant_get(h: Handler, plant_id, **_):
    h.send_json(200, h.S.plant_out(_plant(h.S, plant_id)))


@route("PATCH", "/plants/{plant_id}")
def plant_patch(h: Handler, plant_id, body, **_):
    p = _plant(h.S, plant_id)
    for k in ("name", "substrate", "threshold_pct", "water_led", "notes"):
        if k in body:
            v = body[k]
            if k == "name":
                v = str(v).strip()
                if not v:
                    raise ApiError(400, "validation", "Name fehlt", "name")
            if k == "threshold_pct" and not (isinstance(v, int) and 0 <= v <= 100):
                raise ApiError(400, "validation", "Schwelle 0–100 %", k)
            p[k] = v
    if p["sensor_id"] and ({"threshold_pct", "water_led", "substrate"} & set(body)):
        h.S.sensors[p["sensor_id"]]["pending_config"] = True
    out = h.S.plant_out(p)
    h.S.emit("plant", out)
    h.send_json(200, out)


@route("DELETE", "/plants/{plant_id}")
def plant_delete(h: Handler, plant_id, **_):
    S = h.S
    p = _plant(S, plant_id)
    _assign(S, p, None, False)
    S.plants.pop(p["id"])
    S.emit("plant_deleted", {"id": p["id"]})
    h.send_json(204, None)


@route("PUT", "/plants/{plant_id}/sensor")
def plant_sensor(h: Handler, plant_id, body, **_):
    p = _plant(h.S, plant_id)
    if "sensor_id" not in body:
        raise ApiError(400, "validation", "sensor_id fehlt", "sensor_id")
    _assign(h.S, p, body["sensor_id"], bool(body.get("move_history")))
    h.S.emit("plant", h.S.plant_out(p))
    h.send_json(200, h.S.plant_out(p))


@route("GET", "/plants/{plant_id}/series", auth="read")
def plant_series(h: Handler, plant_id, q, **_):
    S = h.S
    p = _plant(S, plant_id)
    t1 = _int(q, "to")
    t0 = _int(q, "from")
    if t1 <= t0 or t1 - t0 > 3 * 366 * 86400:
        raise ApiError(400, "validation", "Zeitbereich ungültig (max. 3 Jahre)", "from")
    res = q.get("res", "auto")
    if res not in ("auto", "raw", "hour", "day"):
        raise ApiError(400, "validation", "res muss auto, raw, hour oder day sein", "res")
    if res == "auto":
        res = C.choose_resolution(t0, t1, S.per_day(p["sensor_id"]) + 2)
    rows = S.plant_records(p["id"], t0, t1)
    out = {"plant_id": p["id"], "from": t0, "to": t1, "res": res, "timezone": S.settings["time"]["timezone"],
           "threshold_pct": p["threshold_pct"]}
    evald = []
    for sid, rec in rows:
        ev = C.evaluate(rec["raw"], rec["temp"], S.cal[sid][p["substrate"]], p["threshold_pct"])
        evald.append((rec, ev))
    if res == "raw":
        out.update({"t": [r["t"] for r, _ in evald], "moisture": [e["moisture_pct"] for _, e in evald],
                    "temp_c": [r["temp"] for r, _ in evald], "raw": [r["raw"] for r, _ in evald],
                    "flags": [r["flags"] for r, _ in evald]})
    else:
        agg = C.aggregate([(r["t"], e["moisture_pct"], r["temp"]) for r, e in evald], res, out["timezone"])
        out.update(agg)
    out["events"] = [{"t": int(a["from"]), "type": "sensor_change", "text": f"Sensor {a['sensor']} zugeordnet"}
                     for a in S.assign if a["plant"] == p["id"] and t0 <= a["from"] <= t1]
    h.send_json(200, out)


@route("POST", "/plants/{plant_id}/measure")
def plant_measure(h: Handler, plant_id, **_):
    S = h.S
    p = _plant(S, plant_id)
    if not p["sensor_id"]:
        raise ApiError(409, "conflict", "Dieser Pflanze ist kein Sensor zugeordnet")
    busy = [j for j in S.jobs.values() if j["sensor_id"] == p["sensor_id"] and j["kind"] == "measure"
            and j["state"] in ("queued", "waiting_for_sensor", "running")]
    if busy:
        h.send_json(202, busy[0])
        return
    j = S.new_job("measure", p["sensor_id"], p["id"])
    S.run_measure(j, p["id"], p["sensor_id"])
    h.send_json(202, j)


# ------------------------------------------------------------------------------ Sensoren
@route("GET", "/sensors", auth="read")
def sensors_list(h: Handler, **_):
    h.send_json(200, [h.S.sensor_out(s) for s in sorted(h.S.sensors.values(), key=lambda s: s["id"])])


@route("GET", "/sensors/{sensor_id}", auth="read")
def sensor_get(h: Handler, sensor_id, **_):
    h.send_json(200, h.S.sensor_out(_sensor(h.S, sensor_id)))


@route("PATCH", "/sensors/{sensor_id}")
def sensor_patch(h: Handler, sensor_id, body, **_):
    s = _sensor(h.S, sensor_id)
    if "interval_per_day" in body:
        v = body["interval_per_day"]
        if v is not None and not (isinstance(v, int) and 1 <= v <= 96):
            raise ApiError(400, "validation", "Intervall 1–96 pro Tag", "interval_per_day")
        s["interval_per_day"] = v
    if "led_enabled" in body:
        s["led_enabled"] = bool(body["led_enabled"])
    s["pending_config"] = True
    h.send_json(200, h.S.sensor_out(s))


@route("DELETE", "/sensors/{sensor_id}")
def sensor_delete(h: Handler, sensor_id, **_):
    S = h.S
    s = _sensor(S, sensor_id)
    s["unpairing"] = True
    j = S.new_job("unpair", sensor_id, s["plant_id"])

    def done():
        with S.lock:
            if s["plant_id"] and s["plant_id"] in S.plants:
                _assign(S, S.plants[s["plant_id"]], None, False)
            S.sensors.pop(sensor_id, None)
            S.log("info", "unpaired", f"Sensor {sensor_id} entkoppelt", sensor_id)
            S.job_update(j, state="done", progress=1.0, message="Sensor entkoppelt")
    threading.Timer(2.0, done).start()
    h.send_json(202, j)


@route("POST", "/sensors/{sensor_id}/identify")
def sensor_identify(h: Handler, sensor_id, **_):
    S = h.S
    _sensor(S, sensor_id)
    j = S.new_job("identify", sensor_id)
    S.run_measure(j, None, sensor_id, on_done=lambda: {"blinked": True})
    h.send_json(202, j)


@route("GET", "/sensors/{sensor_id}/calibration", auth="read")
def cal_get(h: Handler, sensor_id, **_):
    _sensor(h.S, sensor_id)
    h.send_json(200, h.S.cal[sensor_id])


@route("PUT", "/sensors/{sensor_id}/calibration/{substrate}")
def cal_put(h: Handler, sensor_id, substrate, body, **_):
    S = h.S
    _sensor(S, sensor_id)
    if substrate not in ("erde", "granulat"):
        raise ApiError(404, "not_found", "Unbekanntes Substrat")
    if not C.span_ok(body.get("dry_raw"), body.get("wet_raw")):
        raise ApiError(400, "calibration_span", "Trocken- und Nasswert liegen zu nahe beieinander")
    cal = S._cal(substrate, "manual", body["dry_raw"], body["wet_raw"], now())
    cal["temp_coeff_per_k"] = body.get("temp_coeff_per_k", 0.0)
    S.cal[sensor_id][substrate] = cal
    S.sensors[sensor_id]["pending_config"] = True
    h.send_json(200, cal)


@route("DELETE", "/sensors/{sensor_id}/calibration/{substrate}")
def cal_delete(h: Handler, sensor_id, substrate, **_):
    S = h.S
    _sensor(S, sensor_id)
    if substrate not in ("erde", "granulat"):
        raise ApiError(404, "not_found", "Unbekanntes Substrat")
    S.cal[sensor_id][substrate] = S._default_cal(substrate)
    h.send_json(200, S.cal[sensor_id][substrate])


@route("POST", "/sensors/{sensor_id}/calibration-runs")
def run_create(h: Handler, sensor_id, body, **_):
    S = h.S
    _sensor(S, sensor_id)
    for r in S.runs.values():
        if r["sensor_id"] == sensor_id and r["state"] not in ("committed", "cancelled", "failed"):
            r["state"] = "cancelled"
    rid = "c" + secrets.token_hex(4)
    run = {"id": rid, "sensor_id": sensor_id, "substrate": body.get("substrate", "erde"),
           "samples": body.get("samples", 5), "state": "await_dry", "dry": None, "wet": None,
           "span_ok": None, "message": None, "expires": C.iso(now() + 6 * 3600)}
    S.runs[rid] = run
    h.send_json(201, run)


def _run(S, run_id):
    r = S.runs.get(run_id)
    if not r:
        raise ApiError(404, "not_found", "Kalibrierlauf nicht gefunden")
    return r


@route("GET", "/calibration-runs/{run_id}", auth="session")
def run_get(h: Handler, run_id, **_):
    h.send_json(200, _run(h.S, run_id))


@route("DELETE", "/calibration-runs/{run_id}")
def run_delete(h: Handler, run_id, **_):
    _run(h.S, run_id)["state"] = "cancelled"
    h.send_json(204, None)


@route("POST", "/calibration-runs/{run_id}/capture")
def run_capture(h: Handler, run_id, body, **_):
    S = h.S
    run = _run(S, run_id)
    point = body.get("point")
    if point not in ("dry", "wet"):
        raise ApiError(400, "validation", "point muss dry oder wet sein", "point")
    if run["state"] in ("committed", "cancelled", "failed") or run["state"].startswith("measuring"):
        raise ApiError(409, "conflict", "Lauf ist nicht bereit")
    s = _sensor(S, run["sensor_id"])
    run["state"] = "measuring_" + point
    j = S.new_job("calibration_capture", s["id"], s["plant_id"])

    def do():
        tr = s["true"]
        base = tr["dry"] if point == "dry" else tr["wet"]
        if run["substrate"] != (S.plants.get(s["plant_id"]) or {}).get("substrate", run["substrate"]):
            base *= 1.01
        temp = S._temp_at(now())
        xs = [base * (1 + S.rng.gauss(0, 0.0008)) for _ in range(run["samples"])]
        if run["samples"] >= 5:
            xs[2] *= 1.03  # ein Ausreisser, wird verworfen
        st = C.robust_mean(xs)
        run[point] = {"raw": round(st["mean"]), "temp_c": temp, "n": st["n"],
                      "stddev": C.round1(st["stddev"]) if st["stddev"] is not None else None, "t": C.iso(now())}
        if run["dry"] and run["wet"]:
            run["span_ok"] = C.span_ok(run["dry"]["raw"], run["wet"]["raw"])
            run["state"] = "ready" if run["span_ok"] else "failed"
            run["message"] = None if run["span_ok"] else "Trocken- und Nasswert zu ähnlich – Substrat wirklich nass?"
        else:
            run["state"] = "await_wet" if point == "dry" else "await_dry"
        S.emit("calibration", run)
        return {"run": run, "outliers": st["outliers"]}
    S.run_measure(j, None, s["id"], on_done=do)
    h.send_json(202, j)


@route("POST", "/calibration-runs/{run_id}/commit")
def run_commit(h: Handler, run_id, **_):
    S = h.S
    run = _run(S, run_id)
    if run["state"] != "ready":
        raise ApiError(409, "conflict", "Beide Messpunkte fehlen noch")
    if not run["span_ok"]:
        raise ApiError(422, "calibration_span", "Trocken- und Nasswert zu ähnlich")
    cal = S._cal(run["substrate"], "guided", run["dry"]["raw"], run["wet"]["raw"], now())
    cal["dry"], cal["wet"] = run["dry"], run["wet"]
    S.cal[run["sensor_id"]][run["substrate"]] = cal
    run["state"] = "committed"
    S.log("info", "calibrated", f"Kalibrierung {run['substrate']} gespeichert", run["sensor_id"])
    s = S.sensors[run["sensor_id"]]
    s["pending_config"] = True
    if s["plant_id"]:
        S.emit("plant", S.plant_out(S.plants[s["plant_id"]]))
    h.send_json(200, cal)


# ------------------------------------------------------------------------------ Jobs
@route("GET", "/jobs/{job_id}", auth="read")
def job_get(h: Handler, job_id, **_):
    j = h.S.jobs.get(job_id)
    if not j:
        raise ApiError(404, "not_found", "Auftrag nicht gefunden")
    h.send_json(200, j)


# ------------------------------------------------------------------------------ Pairing
def _pairing_out(S):
    p = S.pairing
    if p["active"] and p["until"] < now():
        p["active"] = False
        p["candidates"] = []
    return {"active": p["active"], "until": C.iso(p["until"]) if p["active"] else None,
            "candidates": p["candidates"]}


@route("GET", "/pairing", auth="session")
def pairing_get(h: Handler, **_):
    h.send_json(200, _pairing_out(h.S))


@route("POST", "/pairing/start")
def pairing_start(h: Handler, body, **_):
    S = h.S
    dur = body.get("duration_s", 180) if isinstance(body, dict) else 180
    S.pairing.update({"active": True, "until": now() + dur, "candidates": []})

    def found():
        with S.lock:
            if not S.pairing["active"] or "fluidi-8E05" in S.sensors:
                return
            S.pairing["candidates"] = [{"device": "fluidi-8E05", "rssi_dbm": -52, "fw_version": "1.0.3",
                                        "hw_rev": "A-32 rev A", "first_seen": C.iso(now()), "known": False}]
            S.emit("pairing", _pairing_out(S))
    threading.Timer(3.0, found).start()
    S.log("info", "pairing", "Kopplungsmodus geöffnet")
    h.send_json(200, _pairing_out(S))


@route("POST", "/pairing/stop")
def pairing_stop(h: Handler, **_):
    h.S.pairing.update({"active": False, "until": None, "candidates": []})
    h.send_json(200, _pairing_out(h.S))


@route("POST", "/pairing/candidates/{device}/accept")
def pairing_accept(h: Handler, device, body, **_):
    S = h.S
    out = _pairing_out(S)
    if not out["active"] or not any(c["device"] == device for c in out["candidates"]):
        raise ApiError(404, "not_found", "Sensor nicht (mehr) im Kopplungsmodus")
    if not body.get("plant_id") and not body.get("plant"):
        raise ApiError(400, "validation", "Pflanze angeben (bestehend oder neu)", "plant")
    if body.get("plant_id"):
        p = _plant(S, body["plant_id"])
        if p["sensor_id"]:
            raise ApiError(409, "conflict", "Diese Pflanze hat schon einen Sensor")
    j = S.new_job("pair", device, None, timeout_s=60)

    def done():
        with S.lock:
            t = now()
            S.sensors[device] = {
                "id": device, "plant_id": None, "hw_rev": "A-32 rev A", "fw_version": "1.0.3",
                "paired": C.iso(t), "last_seen": t,
                "battery": {"mv": 3010, "pct": 98, "days_left": 480, "state": "ok"}, "rssi": -52,
                "interval_per_day": None, "led_enabled": True, "pending_config": False, "error": None,
                "unpairing": False, "true": {"dry": 41300, "wet": 25800, "k": 0.0015}, "buffered_records": 0}
            S.cal[device] = {"erde": S._default_cal("erde"), "granulat": S._default_cal("granulat")}
            temp = S._temp_at(t)
            S.records[device] = [{"t": int(t), "raw": S._raw_from(device, 46.0, temp), "temp": temp,
                                  "flags": 0, "source": "auto"}]
            p = S.plants[body["plant_id"]] if body.get("plant_id") else _create_plant(S, body["plant"])
            _assign(S, p, device, False)
            S.pairing.update({"active": False, "until": None, "candidates": []})
            S.log("info", "paired", f"Sensor {device} gekoppelt mit „{p['name']}“", device)
            S.job_update(j, state="done", progress=1.0, message="Gekoppelt",
                         result={"sensor_id": device, "plant_id": p["id"]})
            S.emit("plant", S.plant_out(p))

    def running():
        S.job_update(j, state="running", progress=0.3, message="Schlüsselaustausch")
        threading.Timer(2.5, done).start()
    threading.Timer(0.8, running).start()
    h.send_json(202, j)


# ------------------------------------------------------------------------------ Einstellungen
def _settings_out(S):
    o = json.loads(json.dumps(S.settings))
    o["storage_forecast_days"] = _forecast(S)
    return o


def _forecast(S):
    per_day = sum(S.per_day(sid) + 2 for sid in S.sensors) or 1
    free = 9_240_576 - _used(S)
    return int(free / (24 * per_day))


def _used(S):
    return 24 * sum(len(v) for v in S.records.values()) + 64 * 1024


def _merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _merge(dst[k], v)
        else:
            dst[k] = v


@route("GET", "/settings", auth="read")
def settings_get(h: Handler, **_):
    h.send_json(200, _settings_out(h.S))


@route("PATCH", "/settings")
def settings_patch(h: Handler, body, **_):
    S = h.S
    if not isinstance(body, dict) or not body:
        raise ApiError(400, "validation", "Keine Änderungen")
    if "interval_per_day" in body and not (isinstance(body["interval_per_day"], int) and 1 <= body["interval_per_day"] <= 96):
        raise ApiError(400, "validation", "Intervall 1–96 pro Tag", "interval_per_day")
    if "reaction_time_min" in body and not (isinstance(body["reaction_time_min"], int) and 1 <= body["reaction_time_min"] <= 5):
        raise ApiError(400, "validation", "Reaktionszeit 1–5 min", "reaction_time_min")
    b = json.loads(json.dumps(body))
    if "mqtt" in b and "password" in b["mqtt"]:
        S.settings["mqtt"]["password_set"] = bool(b["mqtt"].pop("password"))
    _merge(S.settings, b)
    for s in S.sensors.values():
        s["pending_config"] = True
    h.send_json(200, _settings_out(S))


@route("GET", "/settings/network", auth="session")
def network_get(h: Handler, **_):
    h.send_json(200, h.S.network)


@route("PUT", "/settings/network", elevated=True)
def network_put(h: Handler, body, **_):
    S = h.S
    S.network["pending_change"] = {"ssid": body.get("ssid", ""), "deadline": C.iso(now() + 120)}
    S.log("info", "wifi_change", f"WLAN-Wechsel auf „{body.get('ssid')}“ angefordert")
    h.send_json(202, S.network)


# ------------------------------------------------------------------------------ Firmware
def _fw_out(S):
    return {"gateway": {"platform": "mock", "version": VERSION, "build": "2026-11-07", "update_slot": "A",
                        "rollback_available": True, "secure_boot": False, "storage_encryption": "off",
                        "pwa_version": "0.1.0"},
            "sensor_images": S.sensor_images, "rollout": S.rollout}


@route("GET", "/firmware", auth="session")
def fw_get(h: Handler, **_):
    h.send_json(200, _fw_out(h.S))


@route("POST", "/firmware/sensor-images", elevated=True)
def fw_upload(h: Handler, body, **_):
    S = h.S
    data = body if isinstance(body, (bytes, bytearray)) else b""
    if not data:
        raise ApiError(400, "bad_request", "Keine Datei erhalten")
    if len(data) > 512 * 1024:
        raise ApiError(413, "too_large", "Abbild grösser als 512 kB")
    if data.startswith(b"BAD"):  # Testhaken des Mocks: simulierte ungültige Signatur
        raise ApiError(422, "signature_invalid", "Signatur ungültig – Datei wird nicht verteilt")
    n = len(S.sensor_images)
    img = {"version": f"1.0.{3 + n}", "security_counter": 3 + n, "size": len(data),
           "sha256": hashlib.sha256(data).hexdigest(), "signature_ok": True, "hw_compat": "A-32 rev A",
           "uploaded": C.iso(now())}
    S.sensor_images.append(img)
    S.log("info", "fw_upload", f"Sensor-Firmware {img['version']} abgelegt (Mock: Signatur simuliert)")
    h.send_json(201, img)


@route("DELETE", "/firmware/sensor-images/{version}")
def fw_delete(h: Handler, version, **_):
    S = h.S
    before = len(S.sensor_images)
    S.sensor_images = [i for i in S.sensor_images if i["version"] != version]
    if len(S.sensor_images) == before:
        raise ApiError(404, "not_found", "Version nicht vorhanden")
    h.send_json(204, None)


@route("POST", "/firmware/rollout", elevated=True)
def fw_rollout(h: Handler, body, **_):
    S = h.S
    ver = body.get("version")
    if not any(i["version"] == ver for i in S.sensor_images):
        raise ApiError(404, "not_found", "Version nicht vorhanden")
    if S.rollout and not S.rollout["finished"]:
        raise ApiError(409, "busy", "Es läuft bereits eine Verteilung")
    items = []
    for sid in body.get("sensor_ids", []):
        _sensor(S, sid)
        items.append({"sensor_id": sid, "state": "pending", "progress": 0.0, "message": None})
    S.rollout = {"version": ver, "started": C.iso(now()), "finished": None, "items": items}

    def tick():
        with S.lock:
            ro = S.rollout
            if not ro or ro["finished"]:
                return
            active = [i for i in ro["items"] if i["state"] not in ("done", "failed", "skipped", "waiting_for_sensor")]
            for it in ro["items"]:
                s = S.sensors.get(it["sensor_id"])
                if it["state"] == "pending":
                    if not s:
                        it.update(state="skipped", message="Sensor entkoppelt")
                    elif s["battery"]["pct"] < 20:
                        it.update(state="failed", message="Batterie zu tief für ein Update (REQ-FW-02)")
                    elif not S.reachable(it["sensor_id"]):
                        it.update(state="waiting_for_sensor", message="Sensor nicht erreichbar, wird später versucht")
                    elif it is (active[0] if active else None):
                        it.update(state="transferring", message="Übertragung")
                    break
                if it["state"] == "transferring":
                    it["progress"] = round(min(1.0, it["progress"] + 0.2), 2)
                    if it["progress"] >= 1.0:
                        it.update(state="verifying", message="Sensor prüft Signatur")
                    break
                if it["state"] == "verifying":
                    it.update(state="rebooting", message="Neustart mit neuer Version")
                    break
                if it["state"] == "rebooting":
                    it.update(state="done", message=f"Version {ver} aktiv")
                    if s:
                        s["fw_version"] = ver
                    break
            if all(i["state"] in ("done", "failed", "skipped", "waiting_for_sensor") for i in ro["items"]):
                ro["finished"] = C.iso(now())
            S.emit("rollout", ro)
            if not ro["finished"]:
                threading.Timer(1.0, tick).start()
    threading.Timer(0.5, tick).start()
    h.send_json(202, S.rollout)


@route("DELETE", "/firmware/rollout")
def fw_rollout_cancel(h: Handler, **_):
    S = h.S
    if S.rollout and not S.rollout["finished"]:
        for it in S.rollout["items"]:
            if it["state"] not in ("done", "failed", "skipped"):
                it.update(state="skipped", message="abgebrochen")
        S.rollout["finished"] = C.iso(now())
    h.send_json(204, None)


@route("POST", "/firmware/gateway", elevated=True)
def fw_gateway(h: Handler, body, **_):
    data = body if isinstance(body, (bytes, bytearray)) else b""
    if not data:
        raise ApiError(400, "bad_request", "Keine Datei erhalten")
    if data.startswith(b"BAD"):
        raise ApiError(422, "signature_invalid", "Signatur ungültig (Secure Boot) – Update verworfen")
    h.S.log("info", "gw_update", "Gateway-Update geschrieben (Mock, kein Neustart)")
    h.send_json(202, {"version": "0.4.1-mock", "reboot_in_s": 5})


# ------------------------------------------------------------------------------ Daten
def _fmt(v, decimal):
    if v is None:
        return ""
    s = f"{v:.1f}" if isinstance(v, float) else str(v)
    return s.replace(".", ",") if decimal == "comma" else s


@route("GET", "/export.csv", auth="read")
def export_csv(h: Handler, q, **_):
    S = h.S
    t0, t1 = _int(q, "from"), _int(q, "to")
    if t1 <= t0:
        raise ApiError(400, "validation", "Zeitbereich ungültig", "from")
    res = q.get("res", "raw")
    if res not in ("raw", "hour", "day"):
        raise ApiError(400, "validation", "res muss raw, hour oder day sein", "res")
    sep = ";" if q.get("sep", "semicolon") == "semicolon" else ","
    dec = q.get("decimal", "point")
    if sep == "," and dec == "comma":
        raise ApiError(400, "validation", "Dezimalkomma nur mit Semikolon als Trenner", "decimal")
    ids = q.get("plant_ids", "")
    try:
        plants = [_plant(S, i) for i in ids.split(",")] if ids else sorted(S.plants.values(), key=lambda p: p["id"])
    except ValueError:
        raise ApiError(400, "validation", "plant_ids ungültig", "plant_ids")
    tz = ZoneInfo(S.settings["time"]["timezone"])
    buf = io.StringIO()
    buf.write("﻿")
    buf.write(f"# fluidi-csv v1{sep} gateway={GATEWAY_ID}{sep} erzeugt={C.iso(now())}{sep} "
              f"zeitzone={S.settings['time']['timezone']}{sep} aufloesung={res}\n")
    if res == "raw":
        cols = ["pflanze_id", "pflanze", "sensor", "zeit_utc", "zeit_lokal", "feuchte_pct", "feuchte_zustand",
                "rohwert", "temperatur_c", "quelle", "flags"]
    else:
        cols = ["pflanze_id", "pflanze", "zeit_utc", "zeit_lokal", "feuchte_mittel_pct", "feuchte_min_pct",
                "feuchte_max_pct", "temperatur_mittel_c"]
    buf.write(sep.join(cols) + "\n")

    def q_(s):
        s = str(s)
        return '"' + s.replace('"', '""') + '"' if (sep in s or '"' in s or "\n" in s) else s
    for p in plants:
        rows = S.plant_records(p["id"], t0, t1)
        if res == "raw":
            for sid, rec in rows:
                ev = C.evaluate(rec["raw"], rec["temp"], S.cal[sid][p["substrate"]], p["threshold_pct"])
                lt = datetime.fromtimestamp(rec["t"], tz).strftime("%Y-%m-%d %H:%M:%S")
                buf.write(sep.join([str(p["id"]), q_(p["name"]), sid, C.iso(rec["t"]), lt,
                                    _fmt(ev["moisture_pct"], dec), ev["moisture_state"], str(rec["raw"]),
                                    _fmt(float(rec["temp"]), dec), rec["source"], str(rec["flags"])]) + "\n")
        else:
            pts = []
            for sid, rec in rows:
                ev = C.evaluate(rec["raw"], rec["temp"], S.cal[sid][p["substrate"]], p["threshold_pct"])
                pts.append((rec["t"], ev["moisture_pct"], rec["temp"]))
            a = C.aggregate(pts, res, S.settings["time"]["timezone"])
            for i, t in enumerate(a["t"]):
                lt = datetime.fromtimestamp(t, tz).strftime("%Y-%m-%d %H:%M:%S")
                buf.write(sep.join([str(p["id"]), q_(p["name"]), C.iso(t), lt, _fmt(a["moisture"][i], dec),
                                    _fmt(a["moisture_min"][i], dec), _fmt(a["moisture_max"][i], dec),
                                    _fmt(a["temp_c"][i], dec)]) + "\n")
    data = buf.getvalue().encode("utf-8")
    name = f"fluidi-export-{datetime.now(tz).strftime('%Y%m%d-%H%M')}.csv"
    h.send_bytes(200, data, "text/csv; charset=utf-8",
                 {"Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store"})


MOCK_BACKUP_MAGIC = b"FLUIDI-MOCK-BACKUP-1\n"


@route("POST", "/backup", elevated=True)
def backup(h: Handler, body, **_):
    S = h.S
    if len(body.get("passphrase", "")) < 12:
        raise ApiError(400, "validation", "Passphrase: mindestens 12 Zeichen", "passphrase")
    snap = {"gateway_id": GATEWAY_ID, "created": C.iso(now()), "plants": list(S.plants.values()),
            "sensors": [{k: v for k, v in s.items() if k != "true"} for s in S.sensors.values()],
            "records": sum(len(v) for v in S.records.values())}
    data = MOCK_BACKUP_MAGIC + base64.b64encode(gzip.compress(json.dumps(snap).encode()))
    name = f"fluidi-backup-{GATEWAY_ID}-{datetime.now().strftime('%Y%m%d')}.fbk"
    S.log("info", "backup", "Backup erstellt")
    h.send_bytes(200, data, "application/octet-stream", {"Content-Disposition": f'attachment; filename="{name}"',
                                                         "Cache-Control": "no-store"})


@route("POST", "/backup/restore", elevated=True)
def restore(h: Handler, body, q, **_):
    data = body if isinstance(body, (bytes, bytearray)) else b""
    if len(h.headers.get("X-Backup-Passphrase") or "") < 12:
        raise ApiError(400, "validation", "Passphrase fehlt", "X-Backup-Passphrase")
    if not data.startswith(MOCK_BACKUP_MAGIC):
        raise ApiError(422, "bad_request", "Keine gültige fluidi-Backupdatei")
    try:
        snap = json.loads(gzip.decompress(base64.b64decode(data[len(MOCK_BACKUP_MAGIC):])))
    except Exception:
        raise ApiError(422, "bad_request", "Backupdatei beschädigt")
    dry = q.get("dry_run", "false") == "true"
    h.send_json(202, {"ok": True, "dry_run": dry, "gateway_id": snap["gateway_id"], "created": snap["created"],
                      "plants": len(snap["plants"]), "sensors": len(snap["sensors"]), "records": snap["records"],
                      "reboot_in_s": None if dry else 5})


# ------------------------------------------------------------------------------ System
def _time_out(S):
    return {"now": C.iso(now()), "valid": True, "source": "ntp", "last_sync": C.iso(now() - 1800),
            "rtc_ok": True, "timezone": S.settings["time"]["timezone"]}


@route("GET", "/system", auth="read")
def system_get(h: Handler, **_):
    S = h.S
    oldest = min((r[0]["t"] for r in S.records.values() if r), default=None)
    online = sum(1 for sid in S.sensors if S.reachable(sid))
    h.send_json(200, {
        "gateway_id": GATEWAY_ID, "version": VERSION, "uptime_s": int(now() - S.boot), "reset_reason": "power_on",
        "time": _time_out(S),
        "storage": {"used_bytes": _used(S), "total_bytes": 9_240_576,
                    "records": sum(len(v) for v in S.records.values()), "oldest": C.iso(oldest),
                    "forecast_days": _forecast(S)},
        "network": S.network,
        "certificate": {"not_after": C.iso(now() + 712 * 86400), "days_left": 712,
                        "fingerprint_sha256": "MOCK:" + hashlib.sha256(b"mock-ca").hexdigest()[:59]},
        "sensors": {"paired": len(S.sensors), "online": online},
        "heap": {"internal_free": 143_360, "psram_free": 6_815_744},
    })


@route("POST", "/system/time")
def system_time(h: Handler, body, sess, **_):
    # Mock: Gateway hat gültige NTP-Zeit -> Browserzeit wird nur mit force übernommen
    if body.get("force") and (sess.get("elevated_until") or 0) < now():
        raise ApiError(403, "elevation_required", "Bitte Passwort erneut bestätigen")
    h.send_json(200, _time_out(h.S))


@route("POST", "/system/reboot")
def system_reboot(h: Handler, **_):
    h.S.log("info", "reboot", "Neustart angefordert (Mock: ignoriert)")
    h.send_json(202, None)


@route("GET", "/system/events", auth="session")
def system_events(h: Handler, q, **_):
    limit = _int(q, "limit", 50, 1, 200)
    before = _int(q, "before", 10**9)
    ev = [e for e in reversed(h.S.events_log) if e["id"] < before][:limit]
    h.send_json(200, ev)


@route("GET", "/stream", auth="read")
def stream(h: Handler, **_):
    S = h.S
    qu: queue.Queue = queue.Queue(maxsize=200)
    S.sse_clients.append(qu)
    S.lock.release()  # lange Verbindung: Zustand nicht blockieren
    try:
        h.send_response(200)
        h._common_headers()
        h.send_header("Content-Type", "text/event-stream; charset=utf-8")
        h.send_header("Cache-Control", "no-store")
        h.send_header("Connection", "close")
        h.end_headers()
        h.close_connection = True
        h.wfile.write(b"retry: 5000\n: fluidi mock stream\n\n")
        h.wfile.flush()
        while True:
            try:
                msg = qu.get(timeout=15)
                h.wfile.write(msg.encode())
            except queue.Empty:
                h.wfile.write(b": ping\n\n")
            h.wfile.flush()
    except (BrokenPipeError, ConnectionResetError, OSError):
        pass
    finally:
        S.lock.acquire()
        if qu in S.sse_clients:
            S.sse_clients.remove(qu)


def make_server(host="127.0.0.1", port=8080, seed=42, fresh=False, password="fluidi-demo-2026", quiet=False,
                demo=False):
    Handler.S = State(seed, fresh, password)
    Handler.DEMO = demo
    Handler.CHECK = SchemaCheck()
    Handler.QUIET = quiet
    srv = ThreadingHTTPServer((host, port), Handler)
    srv.daemon_threads = True
    return srv


def main():
    ap = argparse.ArgumentParser(description="fluidi Mock-Gateway (Entwicklung)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--fresh", action="store_true", help="Ersteinrichtung (Einrichtungscode) simulieren")
    ap.add_argument("--password", default="fluidi-demo-2026")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--demo-session", action="store_true",
                    help="jede Anfrage gilt als angemeldet (nur für Screenshots, nur mit --host 127.0.0.1)")
    a = ap.parse_args()
    if a.demo_session and a.host != "127.0.0.1":
        ap.error("--demo-session nur mit --host 127.0.0.1")
    srv = make_server(a.host, a.port, a.seed, a.fresh, a.password, a.quiet, a.demo_session)
    S = Handler.S
    print(f"fluidi Mock-Gateway: http://{'localhost' if a.host in ('127.0.0.1', '0.0.0.0') else a.host}:{a.port}/")
    if S.setup_code:
        print(f"  Ersteinrichtung – Einrichtungscode (sonst nur über USB): {S.setup_code}")
    else:
        print(f"  Passwort: {a.password}")
    print(f"  Schemaprüfung der Anfragen: {'ein' if Handler.CHECK.ok else 'aus (PyYAML/jsonschema fehlen)'}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
