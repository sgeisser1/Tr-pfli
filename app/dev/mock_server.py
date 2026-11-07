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
import fluidi_analysis as AN  # noqa: E402

APP_DIR = Path(__file__).resolve().parent.parent
OPENAPI = APP_DIR / "api" / "openapi.yaml"
STATIC_ALLOW = {"index.html", "manifest.webmanifest", "sw.js", "favicon.ico"}
STATIC_DIRS = {"css", "js", "vendor", "icons", "img", "concept"}
API = "/api/v1"
CSP_FRAME_ANY = False  # nur --allow-framing (Screenshots im Geräterahmen)
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
            "notifications": {
                "in_app": True, "badge": True,
                "quiet_hours": {"enabled": True, "start": "19:00", "end": "07:30"},
                "rules": {"needs_water": True, "needs_water_delay_h": 6, "critical": True,
                          "battery_low": True, "offline_h": 24, "daily_summary": "08:00"},
                "email": {"enabled": False, "host": "", "port": 587, "security": "starttls", "username": "",
                          "password_set": False, "from": "", "to": ""},
                "ntfy": {"enabled": False, "url": "", "topic": "fluidi"},
                "webpush": {"enabled": False, "allowed": False},
            },
            "dashboard": {"enabled": True, "public": False, "port": 8443, "title": "Pflanzen im Büro",
                          "show_names": True, "rotate_s": 20},
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
        self.water_truth: dict[int, list] = {}
        self.journal: dict[str, dict] = {}
        self.journal_status: dict[tuple, str] = {}
        self.next_journal = 0
        self.cache: dict = {}
        self.roomplan = None
        self._generate()
        self.roomplan = default_roomplan()
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
            # name, substrate, threshold, sensor, start moisture now, drying %/d, extras (Profil)
            ("Monstera", "erde", 30, "fluidi-1A2B", 58, 5.0, {"species": "monstera", "upper": 75, "pot": (24, "kunststoff"), "loc": "Fenster Süd", "notes": "Neues Blatt im Oktober"}),
            ("Ficus lyrata", "erde", 35, "fluidi-2C4D", 27, 6.0, {"species": "ficus_lyrata", "upper": 70, "pot": (28, "keramik"), "loc": "Ecke beim Fenster"}),
            ("Bogenhanf", "granulat", 15, "fluidi-3E5F", 41, 3.0, {"battery": (2610, 12, 21), "species": "sansevieria", "upper": 50, "pot": (16, "keramik"), "loc": "Empfang"}),
            ("Efeutute", "erde", 30, "fluidi-4A61", 71, 7.0, {"rssi": -91, "species": "epipremnum", "upper": 75, "pot": (14, "kunststoff"), "loc": "Regal hinten"}),
            ("Kaktus Fensterbank", "granulat", 10, "fluidi-5B72", 22, 2.5, {"default_cal": True, "sun": True, "species": "kaktus", "upper": 45, "pot": (10, "ton"), "loc": "Fensterbank Süd"}),
            ("Zitronenbaum", "erde", 40, "fluidi-6C83", 50, 6.5, {"air": True, "species": "zitrus", "upper": 75, "pot": (30, "ton"), "loc": "Fenster West"}),
            ("Calathea", "erde", 45, "fluidi-7D94", 62, 8.0, {"stale_h": 52, "species": "calathea", "upper": 80, "pot": (17, "keramik"), "loc": "Besprechung"}),
            ("Orchidee", "granulat", 20, None, None, 0, {"species": "orchidee", "upper": 60, "pot": (12, "kunststoff"), "loc": "Fensterbank Ost"}),
            ("Glücksfeder", "erde", 15, "fluidi-9F16", 36, 2.8, {"species": "zamioculcas", "upper": 55, "pot": (20, "keramik"), "loc": "Pult Anna"}),
            ("Grünlilie", "erde", 35, "fluidi-A027", 41, 7.5, {"species": "chlorophytum", "upper": 75, "pot": (14, "kunststoff"), "loc": "Hängeampel"}),
        ]
        for name, sub, thr, sid, m_now, rate, ex in specs:
            pid = self.next_plant
            self.next_plant += 1
            pot = ex.get("pot", (None, None))
            self.plants[pid] = {"id": pid, "name": name, "substrate": sub, "threshold_pct": thr,
                                "water_led": "inherit", "notes": ex.get("notes", ""), "sensor_id": sid,
                                "created": C.iso(t_end - 400 * 86400), "species": ex.get("species"),
                                "upper_pct": ex.get("upper"), "location": ex.get("loc", ""),
                                "pot": {"diameter_cm": pot[0], "material": pot[1], "drainage": True}}
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
            self.records[sid] = self._history(sid, sub, m_now, rate, t_end - last_offset, ex, thr, pid)
        self.sensors["fluidi-7D94"]["buffered_records"] = None  # unbekannt: seit 52 h kein Kontakt
        self._journal_seed(t_end)

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

    def _history(self, sid, sub, m_now, rate, t_last, ex, thr=30, pid=None):
        """Rückwärts von „jetzt“: exponentielle Austrocknung m(t) = m0·exp(−k·t) (Konzept Kap. 7),
        rückwärts betrachtet steigt die Feuchte; Giessen = Sprung. k ≈ rate/40 pro Tag, Jahreszeit ±35 %."""
        r = self.rng
        per_day = 6
        step = 86400 / per_day
        t = t_last - (t_last % step)
        m = float(m_now)
        recs = []
        water_at = r.uniform(75, 90)
        k_base = rate / 40.0
        waters = self.water_truth.setdefault(pid, [])
        while t > t_last - 365 * 86400:
            lt = datetime.fromtimestamp(t, self.tz)
            seasonal = 1.0 + 0.35 * math.sin((lt.timetuple().tm_yday - 110) / 365 * 2 * math.pi)
            temp = self._temp_at(t, ex.get("sun", False))
            recs.append({"t": int(t), "raw": self._raw_from(sid, m, temp), "temp": temp, "flags": 0, "source": "auto"})
            m *= math.exp(k_base * seasonal / per_day * r.uniform(0.85, 1.15))
            if m >= water_at:  # rückwärts betrachtet: vor dem Giessen war es trocken
                waters.append(t - r.uniform(0.1, 0.9) * step)
                m = max(5.0, r.uniform(thr - 12, thr + 5))
                water_at = r.uniform(72, 90)
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

    def _journal_seed(self, t_end):
        """Tagebuch: Knopf „gegossen“ bei ~60 % der Giessungen, Dünger, Umtopfen, Notizen."""
        r = self.rng
        for pid, ws in self.water_truth.items():
            for w in ws:
                if t_end - w < 200 * 86400 and r.random() < 0.6:
                    self._journal_add(pid, w - r.uniform(0, 2) * 3600, "watering", "button",
                                      amount_ml=r.choice([None, 250, 300, 500]))
            for i in range(1, 7):
                if pid in (1, 2, 6) and r.random() < 0.8:
                    self._journal_add(pid, t_end - i * 30 * 86400 - r.uniform(0, 5) * 86400, "fertilizing", "manual",
                                      note="Flüssigdünger, halbe Dosis")
        self._journal_add(1, t_end - 150 * 86400, "repotting", "manual", note="In 24-cm-Topf umgetopft, frische Erde")
        self._journal_add(6, t_end - 3 * 3600, "note", "manual", note="Sensor beim Umstellen herausgerutscht?")
        self._journal_add(4, t_end - 20 * 86400, "note", "manual", note="Ableger ins Wasserglas gestellt")

    def _journal_add(self, pid, t, typ, source, note="", amount_ml=None):
        self.next_journal += 1
        e = {"id": f"j{self.next_journal}", "plant_id": pid, "t": int(t), "type": typ, "source": source,
             "status": "confirmed", "note": note, "amount_ml": amount_ml}
        self.journal[e["id"]] = e
        return e

    # ---------------------------------------------------------------- Auswertung (Konzept Kap. 7)
    def analysis(self, pid):
        """Gültige Punkte, erkannte Giessungen, Prognose (gecacht bis zur nächsten Änderung)."""
        if pid in self.cache:
            return self.cache[pid]
        p = self.plants[pid]
        now_s = now()
        pts = []
        for sid, rec in self.plant_records(pid, now_s - 400 * 86400, now_s + 60):
            ev = C.evaluate(rec["raw"], rec["temp"], self.cal[sid][p["substrate"]], p["threshold_pct"])
            if ev["moisture_state"] in ("ok", "dry") and ev["moisture_pct"] is not None:
                pts.append((rec["t"], ev["moisture_pct"]))
        buttons = [e["t"] for e in self.journal.values() if e["plant_id"] == pid and e["type"] == "watering"
                   and e["source"] == "button" and e["status"] != "rejected"]
        events = AN.detect_waterings(pts, buttons)
        rejected = {k[1] for k, v in self.journal_status.items() if k[0] == pid and v == "rejected"}
        events_ok = [e for e in events if e["t"] not in rejected]
        fc = AN.forecast(pts, events_ok, p["threshold_pct"], now_s, p.get("upper_pct"))
        lr = self.last_record(pid)
        latest_state = None
        if lr:
            latest_state = C.evaluate(lr[1]["raw"], lr[1]["temp"], self.cal[lr[0]][p["substrate"]], p["threshold_pct"])["moisture_state"]
        stale = bool(p["sensor_id"]) and lr is not None and C.is_stale(lr[1]["t"], now_s, self.per_day(p["sensor_id"]))
        if not p["sensor_id"]:
            fc.update(state="not_applicable", explanation="Kein Sensor zugeordnet.", next_water=None, days=None,
                      days_low=None, days_high=None, confidence=None)
        elif latest_state not in ("ok", "dry") or stale:
            fc.update(state="not_applicable", next_water=None, days=None, days_low=None, days_high=None, confidence=None,
                      explanation="Aktueller Wert unsicher (Sensor nicht in der Erde, überflutet oder keine neuen Werte) – keine Prognose.")
        last_w = None
        cand = [e["t"] for e in events_ok] + buttons
        if cand:
            last_w = max(cand)
        res = {"points": pts, "events": events, "events_ok": events_ok, "forecast": fc, "last_watered": last_w,
               "stale": stale, "latest_state": latest_state}
        self.cache[pid] = res
        return res

    def journal_for(self, pid):
        """Tagebuch = gespeicherte Einträge + vom Sensor erkannte Giessungen (abgeleitet)."""
        a = self.analysis(pid)
        out = []
        merged = {}
        for e in a["events"]:
            if e["button_t"] is not None:
                merged[e["button_t"]] = e
        for e in self.journal.values():
            if e["plant_id"] != pid:
                continue
            o = {**e, "t": C.iso(e["t"]), "delta_pct": None, "before_pct": None, "after_pct": None,
                 "sensor_confirmed": False, "uncertain_time": False}
            if e["type"] == "watering" and e["t"] in merged:
                ev = merged[e["t"]]
                o.update(delta_pct=C.round1(ev["delta"]), before_pct=C.round1(ev["before"]),
                         after_pct=C.round1(ev["peak"]), sensor_confirmed=True)
            out.append(o)
        for ev in a["events"]:
            if ev["button_t"] is not None:
                continue
            st = self.journal_status.get((pid, ev["t"]), "unconfirmed")
            out.append({"id": f"s{pid}-{ev['t']}", "plant_id": pid, "t": C.iso(ev["t"]), "type": "watering",
                        "source": "sensor", "status": st, "note": "", "amount_ml": None,
                        "delta_pct": C.round1(ev["delta"]), "before_pct": C.round1(ev["before"]),
                        "after_pct": C.round1(ev["peak"]), "sensor_confirmed": True,
                        "uncertain_time": ev["uncertain_time"]})
        for asg in self.assign:
            if asg["plant"] == pid:
                out.append({"id": f"x{pid}-{int(asg['from'])}", "plant_id": pid, "t": C.iso(asg["from"]),
                            "type": "sensor_change", "source": "system", "status": "confirmed",
                            "note": f"Sensor {asg['sensor']} zugeordnet", "amount_ml": None, "delta_pct": None,
                            "before_pct": None, "after_pct": None, "sensor_confirmed": False, "uncertain_time": False})
        out.sort(key=lambda x: x["t"], reverse=True)
        return out

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
            "species": p.get("species"), "upper_pct": p.get("upper_pct"), "location": p.get("location", ""),
            "pot": p.get("pot"), **self.plant_extras(p, latest, stale, s),
        }

    def plant_extras(self, p, latest, stale, s):
        a = self.analysis(p["id"])
        fc = a["forecast"]
        st = latest["moisture_state"] if latest else None
        m = latest["moisture_pct"] if latest else None
        md = AN.mood(st, m, p["threshold_pct"], p.get("upper_pct"), stale, bool(p["sensor_id"]),
                     bool(s and s["error"]), fc.get("days"))
        return {"forecast": {k: fc[k] for k in ("state", "next_water", "days", "days_low", "days_high", "confidence")}
                | {"next_water": C.iso(fc["next_water"]) if fc["next_water"] else None},
                "last_watered": C.iso(a["last_watered"]) if a["last_watered"] else None, "mood": md}

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
                self.cache.clear()
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
        self.send_header("Content-Security-Policy", CSP.replace("frame-ancestors 'none'", "frame-ancestors *") if CSP_FRAME_ANY else CSP)
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
        if rel.endswith("/") or (APP_DIR / rel).is_dir():
            rel = rel.rstrip("/") + "/index.html"
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
                if self.command != "GET":
                    self.S.cache.clear()
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
         "sensor_id": None, "created": C.iso(now()), "species": body.get("species"),
         "upper_pct": body.get("upper_pct"), "location": body.get("location", ""),
         "pot": body.get("pot") or {"diameter_cm": None, "material": None, "drainage": True}}
    _check_range(p)
    S.plants[pid] = p
    if sid:
        _assign(S, p, sid, False)
    return p


def _check_range(p):
    up = p.get("upper_pct")
    if up is not None and up <= p["threshold_pct"] + 5:
        raise ApiError(400, "validation", "Obergrenze muss mindestens 5 %-Punkte über der Giessschwelle liegen", "upper_pct")


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
    p_real = _plant(h.S, plant_id)
    p = dict(p_real)  # erst prüfen, dann übernehmen
    for k in ("name", "substrate", "threshold_pct", "water_led", "notes", "species", "upper_pct", "location", "pot"):
        if k in body:
            v = body[k]
            if k == "name":
                v = str(v).strip()
                if not v:
                    raise ApiError(400, "validation", "Name fehlt", "name")
            if k == "threshold_pct" and not (isinstance(v, int) and 0 <= v <= 100):
                raise ApiError(400, "validation", "Schwelle 0–100 %", k)
            if k == "species" and v is not None and v not in SPECIES_KEYS:
                raise ApiError(400, "validation", "Unbekannte Art", k)
            p[k] = v
    _check_range(p)
    p_real.update(p)
    p = p_real
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
    out["events"] += [{"t": e["t"], "type": "watering", "text": f"gegossen, +{e['delta']:.0f} %"}
                      for e in S.analysis(p["id"])["events_ok"] if t0 <= e["t"] <= t1]
    out["events"].sort(key=lambda e: e["t"])
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
            S.cache.clear()
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
    em = (b.get("notifications") or {}).get("email") or {}
    if "password" in em:
        S.settings["notifications"]["email"]["password_set"] = bool(em.pop("password"))
    if ((b.get("notifications") or {}).get("webpush") or {}).get("enabled") and not S.settings["notifications"]["webpush"]["allowed"]:
        raise ApiError(409, "conflict", "Web Push ist gesperrt: braucht Internet und Hersteller-Server (Entscheid offen, REQ-APP-10)")
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



# ------------------------------------------------------------------------------ Konzept: Profile, Tagebuch,
# Prognose, Raumplan, Statistik, Hinweise, Dashboard (docs/software/SOFTWARE_CONCEPT.md)
_STARTWERT = ("Startwert von fluidi (ANNAHME), keine Pflegeempfehlung aus der Literatur: Der Feuchteindex ist "
              "sensor- und substratspezifisch (0 % = trocken kalibriert, 100 % = nass kalibriert). Bitte an deine "
              "Pflanze anpassen.")
_CLASSES = {"dry": (10, 45, "trocken halten"), "medium": (30, 70, "mittel"), "moist": (45, 80, "eher feucht")}
SPECIES = [
    # key, Name, botanisch, Wasserklasse (Zuordnung = ANNAHME, vom Nutzer zu prüfen)
    ("monstera", "Monstera", "Monstera deliciosa", "medium"),
    ("ficus_lyrata", "Geigenfeige", "Ficus lyrata", "medium"),
    ("sansevieria", "Bogenhanf", "Dracaena trifasciata (syn. Sansevieria)", "dry"),
    ("epipremnum", "Efeutute", "Epipremnum aureum", "medium"),
    ("kaktus", "Kaktus", "Cactaceae", "dry"),
    ("zitrus", "Zitrus", "Citrus × limon", "medium"),
    ("calathea", "Calathea", "Goeppertia (syn. Calathea)", "moist"),
    ("orchidee", "Orchidee", "Phalaenopsis", "dry"),
    ("zamioculcas", "Glücksfeder", "Zamioculcas zamiifolia", "dry"),
    ("chlorophytum", "Grünlilie", "Chlorophytum comosum", "medium"),
    ("generic", "Andere Pflanze", "", "medium"),
]
SPECIES_KEYS = {k for k, *_ in SPECIES}


def species_out():
    out = []
    for key, name, latin, cls in SPECIES:
        lo, hi, txt = _CLASSES[cls]
        out.append({"key": key, "name": name, "latin": latin, "water_class": cls, "water_class_text": txt,
                    "start_range": {"lower_pct": lo, "upper_pct": hi}, "source": "startwert", "note": _STARTWERT,
                    "illustration": key})
    return out


def default_roomplan():
    """Büro 6.4 × 4.6 m, Fenster Süd und West, Tür Nord (Beispiel)."""
    pos = {1: (90, 360), 2: (520, 380), 3: (320, 60), 4: (600, 70), 5: (200, 435), 6: (618, 250),
           7: (120, 120), 9: (420, 220), 10: (300, 300)}
    return {"version": 1, "updated": C.iso(now() - 5 * 86400), "rooms": [{
        "id": "r1", "name": "Büro", "width_cm": 640, "depth_cm": 460, "north_deg": 0, "sun_walls": ["s", "w"],
        "openings": [{"type": "window", "wall": "s", "offset_cm": 60, "length_cm": 180},
                     {"type": "window", "wall": "s", "offset_cm": 380, "length_cm": 180},
                     {"type": "window", "wall": "e", "offset_cm": 140, "length_cm": 160},
                     {"type": "door", "wall": "n", "offset_cm": 470, "length_cm": 95}],
        "furniture": [{"kind": "desk", "label": "Pult", "x_cm": 170, "y_cm": 170, "w_cm": 180, "d_cm": 80},
                      {"kind": "desk", "label": "Pult", "x_cm": 360, "y_cm": 170, "w_cm": 180, "d_cm": 80},
                      {"kind": "shelf", "label": "Regal", "x_cm": 20, "y_cm": 20, "w_cm": 160, "d_cm": 40},
                      {"kind": "table", "label": "Besprechung", "x_cm": 60, "y_cm": 280, "w_cm": 120, "d_cm": 80}],
        "plants": [{"plant_id": k, "x_cm": x, "y_cm": y} for k, (x, y) in pos.items()],
    }]}


@route("GET", "/species", auth="read")
def species_get(h: Handler, **_):
    h.send_json(200, species_out())


@route("GET", "/plants/{plant_id}/journal", auth="read")
def journal_get(h: Handler, plant_id, q, **_):
    p = _plant(h.S, plant_id)
    limit = _int(q, "limit", 100, 1, 1000)
    items = h.S.journal_for(p["id"])
    if q.get("include_rejected") != "true":
        items = [e for e in items if e["status"] != "rejected"]
    h.send_json(200, items[:limit])


@route("POST", "/plants/{plant_id}/journal")
def journal_post(h: Handler, plant_id, body, **_):
    S = h.S
    p = _plant(S, plant_id)
    t = now()
    if body.get("t"):
        try:
            t = datetime.fromisoformat(body["t"].replace("Z", "+00:00")).timestamp()
        except ValueError:
            raise ApiError(400, "validation", "Zeitpunkt ungültig", "t")
        if t > now() + 300:
            raise ApiError(400, "validation", "Zeitpunkt liegt in der Zukunft", "t")
    typ = body.get("type", "watering")
    e = S._journal_add(p["id"], t, typ, "button" if typ == "watering" else "manual",
                       note=body.get("note", ""), amount_ml=body.get("amount_ml"))
    S.cache.clear()
    sid = p["sensor_id"]
    if typ == "watering" and sid and S.reachable(sid) and not body.get("t"):
        # Mock: Sensor misst kurz darauf den Feuchtesprung (Gateway fordert eine Messung an, Konzept 6.4)
        def wet():
            with S.lock:
                s = S.sensors.get(sid)
                if not s or p["name"] == "Zitronenbaum":
                    return
                temp = S._temp_at(now())
                rec = {"t": int(now()), "raw": S._raw_from(sid, S.rng.uniform(78, 88), temp), "temp": temp,
                       "flags": 1, "source": "manual"}
                S.records[sid].append(rec)
                s["last_seen"] = now()
                S.cache.clear()
                S.emit("measurement", {"plant_id": p["id"], "sensor_id": sid, "reading": S.reading(sid, rec, p)})
                S.emit("plant", S.plant_out(p))
                S.emit("journal", {"plant_id": p["id"]})
        threading.Timer(2.5, wet).start()
    out = next(x for x in S.journal_for(p["id"]) if x["id"] == e["id"])
    S.emit("journal", {"plant_id": p["id"]})
    S.emit("plant", S.plant_out(p))
    h.send_json(201, out)


def _journal_entry(S, entry_id):
    if entry_id in S.journal:
        return S.journal[entry_id], False
    m = re.fullmatch(r"s(\d+)-(\d+)", entry_id)
    if m and int(m.group(1)) in S.plants:
        pid, t = int(m.group(1)), int(m.group(2))
        if any(e["t"] == t for e in S.analysis(pid)["events"]):
            return {"plant_id": pid, "t": t}, True
    raise ApiError(404, "not_found", "Eintrag nicht gefunden")


@route("PATCH", "/journal/{entry_id}")
def journal_patch(h: Handler, entry_id, body, **_):
    S = h.S
    e, derived = _journal_entry(S, entry_id)
    if derived:
        if "status" in body:
            S.journal_status[(e["plant_id"], e["t"])] = body["status"]
    else:
        for k in ("note", "amount_ml", "status"):
            if k in body:
                e[k] = body[k]
    S.cache.clear()
    out = next((x for x in S.journal_for(e["plant_id"]) if x["id"] == entry_id), None)
    if out is None:  # verworfen -> nur mit include_rejected sichtbar
        out = {"id": entry_id, "plant_id": e["plant_id"], "t": C.iso(e["t"]), "type": "watering", "source": "sensor",
               "status": body.get("status", "rejected"), "note": "", "amount_ml": None, "delta_pct": None,
               "before_pct": None, "after_pct": None, "sensor_confirmed": True, "uncertain_time": False}
    S.emit("journal", {"plant_id": e["plant_id"]})
    h.send_json(200, out)


@route("DELETE", "/journal/{entry_id}")
def journal_delete(h: Handler, entry_id, **_):
    S = h.S
    e, derived = _journal_entry(S, entry_id)
    if derived:
        raise ApiError(409, "conflict", "Vom Sensor erkannte Giessung: bitte verwerfen statt löschen")
    S.journal.pop(entry_id)
    S.cache.clear()
    S.emit("journal", {"plant_id": e["plant_id"]})
    h.send_json(204, None)


@route("GET", "/plants/{plant_id}/forecast", auth="read")
def forecast_get(h: Handler, plant_id, **_):
    S = h.S
    p = _plant(S, plant_id)
    a = S.analysis(p["id"])
    fc = dict(a["forecast"])
    fc["next_water"] = C.iso(fc["next_water"]) if fc["next_water"] else None
    fc["plant_id"] = p["id"]
    fc["threshold_pct"] = p["threshold_pct"]
    fc["curve"] = None
    if a["forecast"]["state"] == "ok" and a["points"]:
        t_last, m_last = a["points"][-1]
        fc["curve"] = AN.forecast_curve(t_last, m_last, a["forecast"], p["threshold_pct"])
    hist = []
    for c in AN.cycles(a["points"], a["events_ok"])[-8:]:
        f = AN.fit_drying(c["points"])
        if f:
            hist.append({"start": C.iso(c["start"]), "k_per_day": round(f["k"], 4), "r2": round(f["r2"], 3),
                         "current": c["current"]})
    fc["cycles"] = hist
    h.send_json(200, fc)


def _room_check(S, plan):
    ids = set()
    for room in plan["rooms"]:
        if room["id"] in ids:
            raise ApiError(400, "validation", "Raum-ID doppelt", "rooms")
        ids.add(room["id"])
        seen = set()
        for pp in room.get("plants", []):
            if pp["plant_id"] not in S.plants:
                raise ApiError(400, "validation", f"Pflanze {pp['plant_id']} gibt es nicht", "plants")
            if pp["plant_id"] in seen:
                raise ApiError(400, "validation", "Pflanze doppelt platziert", "plants")
            seen.add(pp["plant_id"])
            if not (0 <= pp["x_cm"] <= room["width_cm"] and 0 <= pp["y_cm"] <= room["depth_cm"]):
                raise ApiError(400, "validation", "Pflanze liegt ausserhalb des Raums", "plants")
        for o in room.get("openings", []):
            wall_len = room["width_cm"] if o["wall"] in ("n", "s") else room["depth_cm"]
            if o["offset_cm"] + o["length_cm"] > wall_len:
                raise ApiError(400, "validation", "Fenster/Tür ragt über die Wand hinaus", "openings")


@route("GET", "/roomplan", auth="read")
def roomplan_get(h: Handler, **_):
    h.send_json(200, h.S.roomplan)


@route("PUT", "/roomplan")
def roomplan_put(h: Handler, body, **_):
    S = h.S
    if body.get("version") != S.roomplan["version"]:
        raise ApiError(409, "conflict", "Der Raumplan wurde inzwischen geändert – bitte neu laden")
    _room_check(S, body)
    plan = json.loads(json.dumps(body))
    plan["version"] = S.roomplan["version"] + 1
    plan["updated"] = C.iso(now())
    S.roomplan = plan
    h.send_json(200, plan)


def _energy(S, s):
    """Ladungsbilanz je Sensor aus Ereigniszählung (Modell PROTOCOL Kap. 12, Mittelwerte 'real').
    Mock: Zähler simuliert; Schlafstrom ANNAHME 1.6–2.4 µA (energy_budget.py, REQ-ENE-09 ≤ 8 µA)."""
    per_day = S.per_day(s["id"]) + 2
    r = random.Random(s["id"])
    p = S.plants.get(s["plant_id"]) if s["plant_id"] else None
    need = bool(p and S.plant_out(p)["status"]["needs_water"])
    mc = {"sleep": round(r.uniform(1.6, 2.4) * 86.4, 1), "advertising": 51.0,
          "sessions": round(per_day * 0.299, 2), "measure": round(per_day * 0.03, 2),
          "led": 11.5 if need and s["led_enabled"] else 0.7}
    total = sum(mc.values())
    return {"model": "Ereigniszählung × Ladung je Ereignis (PROTOCOL Kap. 12), Schätzung", "mc_per_day": mc,
            "total_mc_per_day": round(total, 1), "avg_ua": round(total / 86.4, 2),
            "mah_per_year": round(total * 365 / 3600, 1), "cell": "CR2032", "capacity_mah": 225}


def _battery_hist(S, s):
    t1 = now()
    paired = datetime.fromisoformat(s["paired"].replace("Z", "+00:00")).timestamp()
    ts, mv = [], []
    t = max(paired, t1 - 365 * 86400)
    span = max(1.0, t1 - t)
    while t <= t1:
        x = (t1 - t) / span
        ts.append(int(t))
        mv.append(int(s["battery"]["mv"] + (3020 - s["battery"]["mv"]) * x ** 1.6 + (6 if int(t / 86400) % 3 else -4)))
        t += 7 * 86400
    return {"t": ts, "mv": mv}


@route("GET", "/stats", auth="read")
def stats_get(h: Handler, q, **_):
    S = h.S
    days = _int(q, "days", 90, 7, 730)
    t1 = now()
    t0 = t1 - days * 86400
    tz = ZoneInfo(S.settings["time"]["timezone"])
    # Giessungen je Woche (Montag, Ortszeit), letzte 12 Wochen
    lt = datetime.fromtimestamp(t1, tz)
    monday = datetime(lt.year, lt.month, lt.day, tzinfo=tz).timestamp() - lt.weekday() * 86400
    weeks = [monday - i * 7 * 86400 for i in range(11, -1, -1)]
    counts = [0] * 12
    plants = []
    total_w = 0
    for p in sorted(S.plants.values(), key=lambda x: x["id"]):
        a = S.analysis(p["id"])
        ws = sorted(e["t"] for e in a["events_ok"])
        for w in ws:
            for i, ws0 in enumerate(weeks):
                if ws0 <= w < ws0 + 7 * 86400:
                    counts[i] += 1
        recent = [w for w in ws if w >= t0]
        total_w += len(recent)
        gaps = [(b - a_) / 86400 for a_, b in zip(ws, ws[1:]) if b >= t0]
        pts = [(t, m) for t, m in a["points"] if t >= t1 - 30 * 86400]
        plants.append({"plant_id": p["id"], "name": p["name"], "waterings": len(recent),
                       "avg_interval_days": round(sum(gaps) / len(gaps), 1) if gaps else None,
                       "time_in_range_pct": AN.time_in_range(pts, p["threshold_pct"], p.get("upper_pct")),
                       "min_pct": min((m for _, m in pts), default=None), "max_pct": max((m for _, m in pts), default=None)})
    sensors = []
    for s in sorted(S.sensors.values(), key=lambda x: x["id"]):
        sensors.append({"sensor_id": s["id"], "plant_id": s["plant_id"], "battery": S.battery_out(s),
                        "battery_history": _battery_hist(S, s), "energy": _energy(S, s),
                        "radio": {"rssi_dbm": s["rssi"], "quality": C.signal_quality(s["rssi"]),
                                  "sessions_per_day": S.per_day(s["id"]) + 2,
                                  "missed_pct": round(random.Random(s["id"] + "m").uniform(0.2, 4.0) + (8 if s["rssi"] < -88 else 0), 1)},
                        "last_seen": C.iso(s["last_seen"]), "fw_version": s["fw_version"]})
    inr = [p["time_in_range_pct"] for p in plants if p["time_in_range_pct"] is not None]
    allint = [p["avg_interval_days"] for p in plants if p["avg_interval_days"]]
    h.send_json(200, {
        "days": days, "generated": C.iso(t1),
        "summary": {"waterings": total_w, "avg_interval_days": round(sum(allint) / len(allint), 1) if allint else None,
                    "time_in_range_pct": round(sum(inr) / len(inr), 1) if inr else None,
                    "sensors_online": sum(1 for sid in S.sensors if S.reachable(sid)), "sensors": len(S.sensors),
                    "readings": sum(len(v) for v in S.records.values())},
        "waterings_per_week": [{"week_start": C.iso(w), "count": c} for w, c in zip(weeks, counts)],
        "plants": plants, "sensors": sensors,
        "gateway": {"uptime_s": int(t1 - S.boot), "storage_used_bytes": _used(S), "platform": "mock"},
    })


def _alerts(S):
    out = []
    t = now()
    for p in S.plants.values():
        po = S.plant_out(p)
        L, st = po["latest"], po["status"]
        name = p["name"]
        if st["sensor_error"]:
            out.append(("critical", "sensor_error", p, f"{name}: {st['sensor_error']}"))
        if L and L["moisture_state"] == "air" and not st["stale"]:
            out.append(("critical", "air", p, f"{name}: Sensor nicht in der Erde?"))
        if L and L["moisture_state"] == "flooded":
            out.append(("critical", "flooded", p, f"{name}: zu nass oder überflutet?"))
        if st["needs_water"] and not st["stale"]:
            lvl = "critical" if po["mood"] == "parched" else "warn"
            out.append((lvl, "needs_water", p, f"{name} braucht Wasser ({L['moisture_pct']:.0f} %)"))
        if st["stale"]:
            out.append(("warn", "stale", p, f"{name}: seit über {S.settings['notifications']['rules']['offline_h']} h keine neuen Werte"))
        if po["battery"] and po["battery"]["state"] != "ok":
            lvl = "critical" if po["battery"]["state"] == "critical" else "warn"
            out.append((lvl, "battery_low", p, f"{name}: Batterie noch ca. {po['battery']['days_left']} Tage"))
        if po["signal"] and po["signal"]["quality"] <= 1:
            out.append(("info", "weak_signal", p, f"{name}: Funksignal schwach ({po['signal']['rssi_dbm']} dBm)"))
    order = {"critical": 0, "warn": 1, "info": 2}
    out.sort(key=lambda x: (order[x[0]], x[2]["name"]))
    return [{"id": f"{kind}-{p['id']}", "level": lvl, "kind": kind, "plant_id": p["id"], "sensor_id": p["sensor_id"],
             "since": C.iso(t - 3600 * (1 + (p["id"] * 7) % 30)), "text": text} for lvl, kind, p, text in out]


@route("GET", "/alerts", auth="read")
def alerts_get(h: Handler, **_):
    h.send_json(200, _alerts(h.S))


@route("GET", "/dashboard", auth="public")
def dashboard_get(h: Handler, sess, **_):
    """Nur-Lese-Zusammenfassung für TV/Kollegen: keine Sensor-IDs, keine Systemdaten."""
    S = h.S
    d = S.settings["dashboard"]
    if not d["enabled"]:
        raise ApiError(404, "not_found", "Dashboard ist ausgeschaltet")
    if not d["public"] and not sess and not S.settings["public_read"]:
        raise ApiError(401, "auth_required", "Bitte anmelden")
    plants = []
    for p in sorted(S.plants.values(), key=lambda x: x["name"].lower()):
        po = S.plant_out(p)
        L = po["latest"]
        plants.append({"id": p["id"], "name": p["name"] if d["show_names"] else f"Pflanze {p['id']}",
                       "species": p.get("species"), "mood": po["mood"],
                       "state": "stale" if po["status"]["stale"] else (L["moisture_state"] if L else "none"),
                       "moisture_pct": L["moisture_pct"] if L else None, "threshold_pct": p["threshold_pct"],
                       "upper_pct": p.get("upper_pct"), "needs_water": po["status"]["needs_water"],
                       "forecast_days": po["forecast"]["days"], "next_water": po["forecast"]["next_water"]})
    al = _alerts(S)
    room = json.loads(json.dumps(S.roomplan))
    h.send_json(200, {"generated": C.iso(now()), "title": d["title"], "public": d["public"],
                      "summary": {"plants": len(plants), "needs_water": sum(p["needs_water"] for p in plants),
                                  "warnings": sum(1 for a in al if a["level"] != "info" and a["kind"] != "needs_water")},
                      "plants": plants, "roomplan": room})


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
    ap.add_argument("--allow-framing", action="store_true",
                    help="CSP frame-ancestors * (nur für Screenshots im Geräterahmen)")
    ap.add_argument("--demo-session", action="store_true",
                    help="jede Anfrage gilt als angemeldet (nur für Screenshots, nur mit --host 127.0.0.1)")
    a = ap.parse_args()
    if a.demo_session and a.host != "127.0.0.1":
        ap.error("--demo-session nur mit --host 127.0.0.1")
    global CSP_FRAME_ANY
    CSP_FRAME_ANY = a.allow_framing
    srv = make_server(a.host, a.port, a.seed, a.fresh, a.password, a.quiet, a.demo_session)
    S = Handler.S
    print(f"fluidi Mock-Gateway: http://{'localhost' if a.host in ('127.0.0.1', '0.0.0.0') else a.host}:{a.port}/")
    if S.setup_code:
        print(f"  Ersteinrichtung – Einrichtungscode (sonst nur über USB): {S.setup_code}")
    else:
        print(f"  Passwort: {a.password}")
    print(f"  Entwürfe: http://localhost:{a.port}/concept/?theme=frost | botanik | stele")
    print(f"  Schemaprüfung der Anfragen: {'ein' if Handler.CHECK.ok else 'aus (PyYAML/jsonschema fehlen)'}")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
