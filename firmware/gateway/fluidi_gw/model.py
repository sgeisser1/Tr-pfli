"""Fachmodell des Gateways: Pflanzen, Sensoren, Kalibrierung, Tagebuch, Jobs, Auswertung – SQLite-gestützt.

Abgeleitet aus der Referenzimplementierung app/dev/mock_server.py (State), aber ohne Testdaten-Generator:
kleine Dokumente liegen im RAM und werden bei jeder Änderung geschrieben (write-through), Messwerte nur in
SQLite (store.py). Flüchtiges (RSSI, zuletzt gesehen, Advertising-Zähler) bleibt im RAM und wird höchstens
alle 15 min gesichert (SD-Schonung, ARCHITECTURE Kap. 14.4).

Thread-Modell: HTTP-Threads und der asyncio-Thread des Funkteils (central.py) greifen über `self.lock` zu.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import queue
import secrets
import struct
import threading
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from . import protocol as P
from . import timesync
from .shared import AN, C

SPECIES_FALLBACK_NOTE = ("Startwert von fluidi (ANNAHME), keine Pflegeempfehlung aus der Literatur: Der Feuchteindex ist "
                         "sensor- und substratspezifisch (0 % = trocken kalibriert, 100 % = nass kalibriert).")
CLASSES = {"dry": (10, 45, "trocken halten"), "medium": (30, 70, "mittel"), "moist": (45, 80, "eher feucht")}
DEFAULT_SETTINGS = {
    "interval_per_day": 6, "reaction_time_min": 1, "default_threshold_pct": 30,
    "led": {"enabled": True, "water_hint": True, "brightness": "normal",
            "water_window": {"start": "07:00", "end": "19:00", "weekdays": [1, 2, 3, 4, 5, 6, 7]}},
    "time": {"ntp_enabled": True, "ntp_server": "pool.ntp.org", "timezone": "Europe/Zurich"},
    # F-8 (SOFTWARE_CONCEPT Kap. 17): Lesen ohne Anmeldung AUS, seit es das öffentliche Dashboard gibt (D-020)
    "public_read": False,
    "mqtt": {"enabled": False, "host": "", "port": 1883, "tls": False, "username": "", "password_set": False,
             "base_topic": "fluidi", "discovery": True, "discovery_prefix": "homeassistant"},
    "notifications": {
        "in_app": True, "badge": True, "quiet_hours": {"enabled": True, "start": "19:00", "end": "07:30"},
        "rules": {"needs_water": True, "needs_water_delay_h": 0, "critical": True, "battery_low": True,
                  "offline_h": 24, "daily_summary": "08:00"},
        # D-020: keine E-Mail, Web Push später – Felder bleiben im Schema, sind aber gesperrt
        "email": {"enabled": False, "host": "", "port": 587, "security": "starttls", "username": "",
                  "password_set": False, "from": "", "to": ""},
        "ntfy": {"enabled": False, "url": "", "topic": "fluidi"},
        "webpush": {"enabled": False, "allowed": False},
    },
    "dashboard": {"enabled": True, "public": False, "port": 8080, "title": "Pflanzen im Büro", "show_names": True,
                  "rotate_s": 20},
    "salt": {"peak_pct": 130},
}
LED_LEVEL = {"low": 30, "normal": 70, "high": 100}  # ANNAHME: Abbildung Helligkeit -> led_level (PROTOCOL 8)
# Batterie (REQ-ENE-05): CR2032 225 mAh, nutzbar 75 % (PROTOCOL 9.2, ANNAHME), 1 mAh = 3.6e6 µC
CAP_UC = 225 * 3.6e6 * 0.75
# Rückfall ohne gemessene Rate: pessimistische Laufzeit 17 Monate (D-006) auf die nutzbare Ladung verteilt (ANNAHME)
MODEL_UC_PER_DAY = CAP_UC / (17 * 30.44)
ILLUSTRATIONS = {"monstera", "ficus_lyrata", "sansevieria", "epipremnum", "kaktus", "zitrus", "calathea", "orchidee",
                 "zamioculcas", "chlorophytum", "generic"}   # eigene SVG-Zeichnungen in app/js/art.js
SESSION_INFO_STALE = 6 * 3600   # Zeit/Status spätestens alle 6 h (PROTOCOL 2.5)
VOLATILE_FLUSH_S = 900


def now() -> float:
    return time.time()


def iso(t):
    return C.iso(t) if t else None


class ApiError(Exception):
    def __init__(self, status, code, message, field=None, retry_after=None):
        super().__init__(message)
        self.status, self.code, self.message, self.field, self.retry_after = status, code, message, field, retry_after

    def body(self):
        e = {"code": self.code, "message": self.message}
        if self.field:
            e["field"] = self.field
        if self.retry_after is not None:
            e["retry_after_s"] = self.retry_after
        return {"error": e}


def _merge(dst, src):
    for k, v in src.items():
        if isinstance(v, dict) and isinstance(dst.get(k), dict):
            _merge(dst[k], v)
        else:
            dst[k] = v
    return dst


class Model:
    def __init__(self, store, cfg, timesvc, sim=False):
        self.store = store
        self.cfg = cfg
        self.time = timesvc
        self.sim = sim
        self.lock = threading.RLock()
        self.central = None          # central.Central (Funk), gesetzt in service.py
        self.climate = None          # climate.Climate
        self.mqtt = None
        self.boot = now()
        self.sse_clients: list[queue.Queue] = []
        self.sse_id = 0
        self.jobs: dict[str, dict] = {}
        self.runs: dict[str, dict] = {}
        self.fails: dict[str, dict] = {}
        self.global_fails: list[float] = []
        self.pairing = {"active": False, "until": None, "candidates": {}}
        self.rollout = None
        self.cache: dict = {}
        self.alert_since: dict = {}
        self.adv_stats: dict = {}
        self.volatile_dirty = set()
        self.last_flush = now()
        self._load()

    # ================================================================== Laden / Grunddaten
    def _load(self):
        st = self.store
        gid = st.meta_get("gateway_id")
        if not gid:
            gid = secrets.token_hex(8)
            st.meta_set("gateway_id", gid)
        self.gateway_id = bytes.fromhex(gid)
        self.gw_name = "fluidi-gw-" + gid[-4:].upper()
        self.settings = _merge(json.loads(json.dumps(DEFAULT_SETTINGS)), st.meta_get("settings", {}))
        self.auth = st.meta_get("auth")
        self.setup_code = st.meta_get("setup_code")
        if not self.auth and not self.setup_code:
            self.new_setup_code()
        self.plants = {int(k): v for k, v in st.load_docs("plant").items()}
        self.next_plant = max(self.plants, default=0) + 1
        self.sensors = {}       # API-ID -> Dokument (enthält addr)
        self.by_addr = {}
        for addr, (sid, doc) in st.sensors().items():
            doc.update(id=sid, addr=addr)
            self.sensors[sid] = doc
            self.by_addr[addr] = sid
        self.cal = st.calibrations()          # addr -> {substrat: Kalibrierung}
        self.assign = st.assignments()        # sensor = addr
        self.journal = st.journal()
        self.journal_status = st.journal_status()
        self.next_journal = max((int(k[1:]) for k in self.journal if k[1:].isdigit()), default=0)
        self.roomplan = st.meta_get("roomplan") or self.default_roomplan()
        self.sensor_images = st.images()
        self.sessions = st.sessions()
        self.max_seq = {addr: st.max_seq(addr) for addr in self.by_addr}

    def new_setup_code(self):
        self.setup_code = f"{secrets.randbelow(1000):03d}-{secrets.randbelow(1000):03d}"
        self.store.meta_set("setup_code", self.setup_code)
        return self.setup_code

    def save_settings(self):
        self.store.meta_set("settings", self.settings)

    def log(self, level, code, text, sensor_id=None):
        try:
            self.store.log(level, code, text, sensor_id)
        except Exception:  # noqa: BLE001 - Protokoll darf nie den Ablauf stoppen
            pass

    def emit(self, event: str, data):
        with self.lock:
            self.sse_id += 1
            msg = f"id: {self.sse_id}\nevent: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
            for q in list(self.sse_clients):
                try:
                    q.put_nowait(msg)
                except queue.Full:
                    pass

    def tz(self):
        try:
            return ZoneInfo(self.settings["time"]["timezone"])
        except Exception:  # noqa: BLE001
            return ZoneInfo("Europe/Zurich")

    # ================================================================== Auth
    def pw_hash(self, pw: str, salt: bytes, it: int) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, it)

    def check_password(self, pw: str) -> bool:
        if not self.auth:
            return False
        import hmac
        h = self.pw_hash(pw, bytes.fromhex(self.auth["salt"]), self.auth["iter"])
        return hmac.compare_digest(h.hex(), self.auth["hash"])

    def set_password(self, pw: str):
        salt = secrets.token_bytes(16)
        it = self.cfg.pbkdf2_iterations
        self.auth = {"salt": salt.hex(), "iter": it, "hash": self.pw_hash(pw, salt, it).hex(), "set": iso(now())}
        self.store.meta_set("auth", self.auth)
        self.setup_code = None
        self.store.meta_set("setup_code", None)

    def reset_password(self):
        """Passwort-Reset (UC-16) nur lokal über die Kommandozeile (SSH/Konsole): neuer Einrichtungscode, Daten bleiben."""
        self.auth = None
        self.store.meta_set("auth", None)
        self.sessions.clear()
        self.store.delete_session(keep="")
        self.log("warn", "password_reset", "Passwort zurückgesetzt (lokal), neuer Einrichtungscode erzeugt")
        return self.new_setup_code()

    # ================================================================== Sensor-Zugriff
    def sensor_by_addr(self, addr):
        sid = self.by_addr.get(addr)
        return self.sensors.get(sid) if sid else None

    def sensor_doc_public(self, s):
        return {k: v for k, v in s.items() if not k.startswith("_")}

    def save_sensor(self, s):
        doc = {k: v for k, v in s.items() if k not in ("id", "addr")}
        self.store.save_sensor(s["addr"], s["id"], doc)

    def per_day(self, sid=None):
        s = self.sensors.get(sid) if sid else None
        if s and s.get("interval_per_day"):
            return s["interval_per_day"]
        return self.settings["interval_per_day"]

    def reachable(self, sid):
        s = self.sensors.get(sid)
        return bool(s) and s.get("last_seen") is not None and (now() - s["last_seen"]) < 6 * 3600

    def cal_for(self, addr, substrate):
        c = self.cal.get(addr, {}).get(substrate)
        return c or self.default_cal(substrate)

    def default_cal(self, sub):
        dry, wet = self.cfg.default_cal.get(sub, (1330, 4000))
        return self.make_cal(sub, "default", dry, wet, None)

    @staticmethod
    def make_cal(sub, source, dry, wet, t, temp=None, n=0, sd=None):
        return {"substrate": sub, "source": source,
                "dry": {"raw": round(dry), "temp_c": temp, "n": n, "stddev": sd},
                "wet": {"raw": round(wet), "temp_c": temp, "n": n, "stddev": sd},
                "temp_coeff_per_k": 0.0, "t_ref_c": C.T_REF_C, "updated": iso(t)}

    # ================================================================== Messwerte lesen
    @staticmethod
    def _rec(row):
        cause = row["cause"] or 0
        return {"t": row["t"], "raw": row["raw"], "temp": row["temp"], "flags": row["flags"] or 0,
                "source": {0: "auto", 1: "button", 2: "manual", 3: "calibration", 4: "calibration"}.get(cause, "manual"),
                "c_diag": row["c_diag"], "vbat": row["vbat"], "seq": row["seq"]}

    def plant_records(self, pid, t0, t1):
        out = []
        for a in self.assign:
            if a["plant"] != pid:
                continue
            lo, hi = max(t0, a["from"]), min(t1, a["to"] if a["to"] else t1)
            if hi < lo:
                continue
            sid = self.by_addr.get(a["sensor"], P.sensor_name(a["sensor"]))
            for r in self.store.readings(a["sensor"], lo, hi):
                rec = self._rec(r)
                rec["_addr"] = a["sensor"]
                out.append((sid, rec))
        out.sort(key=lambda x: x[1]["t"])
        return out

    def last_record(self, pid):
        best = None
        for a in self.assign:
            if a["plant"] != pid:
                continue
            r = self.store.last_reading(a["sensor"], a["from"], a["to"] or 2**40)
            if r and (best is None or r["t"] > best[1]["t"]):
                rec = self._rec(r)
                rec["_addr"] = a["sensor"]
                best = (self.by_addr.get(a["sensor"], P.sensor_name(a["sensor"])), rec)
        return best

    def evaluate(self, rec, plant):
        return C.evaluate(rec["raw"], rec["temp"], self.cal_for(rec["_addr"], plant["substrate"]), self.thr(plant))

    # ================================================================== Profile (D-021, PFLANZENPROFILE.md Kap. 4)
    def species_of(self, p):
        return next((x for x in self.species() if x["key"] == p.get("species")), None)

    def regime(self, p):
        if p.get("regime") in ("A", "B", "C", "D"):
            return p["regime"]
        sp = self.species_of(p)
        return (sp or {}).get("regime") or "B"

    def winter_active(self, p, t=None):
        """Winterschwelle = round(water_at_pct × winter_factor) in den Wintermonaten (Kap. 4.4, ANNAHME)."""
        if p.get("winter") is False:
            return False
        wf = self.winter_factor(p)
        if not wf or wf >= 1:
            return False
        months = self.settings.get("winter_months") or self._species_meta().get("winter_months_default") or [11, 12, 1, 2]
        return datetime.fromtimestamp(t or now(), self.tz()).month in months

    def winter_factor(self, p):
        if p.get("winter_factor") is not None:
            return p["winter_factor"]
        return (self.species_of(p) or {}).get("winter_factor")

    def thr(self, p):
        """Wirksame Giessschwelle (Winterfaktor berücksichtigt)."""
        t = p["threshold_pct"]
        if self.winter_active(p):
            t = int(round(t * self.winter_factor(p)))
        return t

    def care(self, p, latest, a, stale):
        """Regime-Hinweise (PFLANZENPROFILE Kap. 4.3). Zu nass erst 48 h nach der letzten Giessung (D-021 Entscheid 1)."""
        rg = self.regime(p)
        thr = self.thr(p)
        m = latest["moisture_pct"] if latest and latest["moisture_state"] in ("ok", "dry") else None
        lw = a["last_watered"]
        t = now()
        hints, phase, too_wet = [], None, False
        up = p.get("upper_pct")
        if m is not None and up is not None and m > up and (lw is None or t - lw > 48 * 3600) and not stale:
            too_wet = True
            hints.append({"kind": "too_wet", "level": "warn", "text": "Seit über 48 h zu nass – " + (
                "diese Art verträgt Staunässe schlecht: Abzugsloch/Untersetzer prüfen." if rg == "A"
                else "Abzugsloch und Untersetzer prüfen, weniger oft giessen.")})
        if rg == "A" and m is not None and m >= thr:
            phase = "dry_phase"
            hints.append({"kind": "dry_phase", "level": "info", "text": "Trockenphase erwünscht – noch nicht giessen."})
        if rg == "C" and m is not None and thr <= m < thr + 10:
            hints.append({"kind": "soon", "level": "info", "text": "Bald giessen – diese Art soll nicht austrocknen."})
        evs = a["events_ok"]
        if evs and t - evs[-1]["t"] < 3 * 86400:
            ev = evs[-1]
            early = {"A": 15, "B": 25}.get(rg)
            if early is not None and ev["before"] > thr + early:
                hints.append({"kind": "early", "level": "info", "text": "Früher gegossen als das Profil vorsieht"
                              + (" – diese Art mag zwischendurch trocken stehen." if rg == "A" else ".")})
            if rg in ("A", "B", "C") and ev["peak"] < 80:
                hints.append({"kind": "not_thorough", "level": "info", "text": "Vielleicht nicht durchdringend gegossen – "
                              "giessen, bis unten Wasser austritt, Untersetzer leeren."})
        if rg == "D":
            sp = self.species_of(p) or {}
            rd = (sp.get("start_range") or {}).get("reminder_days")
            if p.get("species") == "hydrokultur":
                hints.append({"kind": "hydro", "level": "info", "text": "fluidi misst keinen Wasserstand – Wasserstandsanzeiger nutzen."})
            elif rd and lw and t - lw > rd * 86400:
                hints.append({"kind": "reminder", "level": "warn", "text": f"Erinnerung: zuletzt vor über {rd} Tagen gegossen."})
        if self.winter_active(p) and self.winter_factor(p) and self.winter_factor(p) <= 0.5:
            hints.append({"kind": "winter", "level": "info", "text": "Winterruhe: nur giessen, wenn die Pflanze schrumpft."})
        return {"regime": rg, "phase": phase, "too_wet": too_wet, "winter_active": self.winter_active(p),
                "effective_threshold_pct": thr, "hints": hints}

    def reading_out(self, rec, plant):
        ev = self.evaluate(rec, plant)
        tq = "reconstructed" if rec["flags"] & 2 else "unsynced" if rec["flags"] & 4 else "ok"
        return {"t": iso(rec["t"]), **ev, "raw": rec["raw"], "temp_c": rec["temp"], "time_quality": tq,
                "source": rec["source"] if rec["source"] in ("auto", "manual", "button", "calibration") else "manual"}

    # ================================================================== Auswertung (SOFTWARE_CONCEPT Kap. 8)
    def analysis(self, pid):
        if pid in self.cache:
            return self.cache[pid]
        p = self.plants[pid]
        t1 = now()
        pts, unclamped = [], []
        for sid, rec in self.plant_records(pid, t1 - 400 * 86400, t1 + 60):
            ev = self.evaluate(rec, p)
            if ev["moisture_state"] in ("ok", "dry") and ev["moisture_pct"] is not None:
                pts.append((rec["t"], ev["moisture_pct"]))
            if ev["moisture_unclamped"] is not None:
                unclamped.append((rec["t"], ev["moisture_unclamped"]))
        buttons = [e["t"] for e in self.journal.values() if e["plant_id"] == pid and e["type"] == "watering"
                   and e["source"] == "button" and e["status"] != "rejected"]
        events = AN.detect_waterings(pts, buttons)
        rejected = {k[1] for k, v in self.journal_status.items() if k[0] == pid and v == "rejected"}
        events_ok = [e for e in events if e["t"] not in rejected]
        fc = AN.forecast(pts, events_ok, self.thr(p), t1, p.get("upper_pct"))
        lr = self.last_record(pid)
        latest_state = self.evaluate(lr[1], p)["moisture_state"] if lr else None
        stale = bool(p.get("sensor_id")) and lr is not None and C.is_stale(lr[1]["t"], t1, self.per_day(p["sensor_id"]))
        if not p.get("sensor_id"):
            fc.update(state="not_applicable", explanation="Kein Sensor zugeordnet.", next_water=None, days=None,
                      days_low=None, days_high=None, confidence=None)
        elif latest_state not in ("ok", "dry") or stale:
            fc.update(state="not_applicable", next_water=None, days=None, days_low=None, days_high=None, confidence=None,
                      explanation="Aktueller Wert unsicher (Sensor nicht in der Erde, überflutet oder keine neuen Werte) – keine Prognose.")
        cand = [e["t"] for e in events_ok] + buttons
        res = {"points": pts, "events": events, "events_ok": events_ok, "forecast": fc,
               "last_watered": max(cand) if cand else None, "stale": stale, "latest_state": latest_state,
               "salt": self._salt(pid, unclamped, events_ok, t1)}
        self.cache[pid] = res
        return res

    def _salt(self, pid, unclamped, events, t1):
        """Salz-/Dünger-Hinweis aus der Zeitreihe (D-018, MESSKETTE_SALZ Kap. A+): Spitze des ungekappten Index
        nach dem Giessen > 130 % (ANNAHME-Schwelle, am Muster festlegen, OP-K3). Nur Hinweis, keine Messung."""
        lim = self.settings.get("salt", {}).get("peak_pct", 130)
        fert = [e["t"] for e in self.journal.values() if e["plant_id"] == pid and e["type"] == "fertilizing"
                and e["status"] != "rejected"]
        last_fert = max(fert) if fert else None
        peak, peak_t = None, None
        for ev in events[-3:]:
            for t, v in unclamped:
                if ev["t"] - 3600 <= t <= ev["t"] + 12 * 3600 and (peak is None or v > peak):
                    peak, peak_t = v, t
        if peak is not None and peak > lim and t1 - peak_t < 30 * 86400:
            return {"state": "suspected", "peak_pct": peak, "since": iso(peak_t), "last_fertilized": iso(last_fert),
                    "text": "Dünger/Salz erkannt – die Anzeige im nassen Bereich ist unsicher. Gelegentlich mit "
                            "klarem Wasser durchspülen."}
        if last_fert and t1 - last_fert < 14 * 86400:
            return {"state": "fertilized", "peak_pct": peak, "since": iso(last_fert), "last_fertilized": iso(last_fert),
                    "text": "Kürzlich gedüngt – Feuchtewerte im nassen Bereich können einige Tage zu hoch sein."}
        return {"state": "none", "peak_pct": peak, "since": None, "last_fertilized": iso(last_fert), "text": None}

    def invalidate(self, pid=None):
        if pid is None:
            for k in [k for k in self.cache if not str(k).startswith("_species")]:
                self.cache.pop(k, None)
        else:
            self.cache.pop(pid, None)

    # ================================================================== Ausgaben (Schemas openapi.yaml)
    def battery_out(self, s):
        b = s.get("battery") if s else None
        return dict(b) if b else None

    def signal_out(self, s):
        if not s or s.get("rssi") is None:
            return None
        return {"rssi_dbm": int(s["rssi"]), "quality": C.signal_quality(s["rssi"])}

    def plant_out(self, p):
        sid = p.get("sensor_id")
        s = self.sensors.get(sid) if sid else None
        lr = self.last_record(p["id"])
        latest = self.reading_out(lr[1], p) if lr else None
        stale = bool(sid) and lr is not None and C.is_stale(lr[1]["t"], now(), self.per_day(sid))
        cal_state = "none"
        if s:
            cal_state = "default" if self.cal_for(s["addr"], p["substrate"])["source"] == "default" else "calibrated"
        a = self.analysis(p["id"])
        fc = a["forecast"]
        st = latest["moisture_state"] if latest else None
        m = latest["moisture_pct"] if latest else None
        err = s.get("error") if s else None
        care = self.care(p, latest, a, stale)
        thr = care["effective_threshold_pct"]
        # „zu nass“ nur nach Karenz 48 h (D-021); Regime C: „sehr durstig“ schon 5 statt 10 %-Punkte unter der Schwelle
        md = AN.mood(st, m, thr + (5 if care["regime"] == "C" else 0), p.get("upper_pct") if care["too_wet"] else None,
                     stale, bool(sid), bool(err), fc.get("days"))
        if md == "parched" and care["regime"] != "C" and m is not None and m >= thr - 10:
            md = "thirsty"
        return {
            "id": p["id"], "name": p["name"], "substrate": p["substrate"], "threshold_pct": p["threshold_pct"],
            "water_led": p.get("water_led", "inherit"), "notes": p.get("notes", ""), "sensor_id": sid, "latest": latest,
            "status": {"needs_water": bool(latest and latest["moisture_state"] == "dry"), "stale": stale,
                       "battery_low": bool(s and s.get("battery") and s["battery"]["state"] != "ok"),
                       "sensor_error": err["text"] if err else None},
            "battery": self.battery_out(s), "signal": self.signal_out(s), "calibration": cal_state,
            "created": p.get("created"), "species": p.get("species"), "upper_pct": p.get("upper_pct"),
            "location": p.get("location", ""), "pot": p.get("pot"),
            "forecast": {k: fc[k] for k in ("state", "days", "days_low", "days_high", "confidence")}
            | {"next_water": iso(fc["next_water"])},
            "last_watered": iso(a["last_watered"]), "mood": md, "salt": a["salt"], "care": care,
            "winter_factor": self.winter_factor(p), "regime": care["regime"],
        }

    def sensor_out(self, s):
        return {
            "id": s["id"], "plant_id": s.get("plant_id"), "hw_rev": s.get("hw_rev", ""), "fw_version": s.get("fw_version", "?"),
            "paired": s.get("paired"), "last_seen": iso(s.get("last_seen")), "battery": self.battery_out(s),
            "signal": self.signal_out(s), "interval_per_day": s.get("interval_per_day"),
            "effective_interval_per_day": self.per_day(s["id"]), "led_enabled": s.get("led_enabled", True),
            "pending_config": bool(s.get("pending_config")), "buffered_records": s.get("buffered_records"),
            "error": s.get("error"), "unpairing": bool(s.get("unpairing")), "address": s["addr"],
            "lost_records": s.get("lost_records", 0), "reset_reason": s.get("reset_reason"),
        }

    # ================================================================== Jobs
    def new_job(self, kind, sensor_id=None, plant_id=None, timeout_s=None):
        jid = "j" + secrets.token_hex(4)
        timeout_s = timeout_s or self.settings["reaction_time_min"] * 60 + 30
        j = {"id": jid, "kind": kind, "state": "queued", "sensor_id": sensor_id, "plant_id": plant_id,
             "created": iso(now()), "deadline": iso(now() + timeout_s), "progress": None,
             "message": "Auftrag angenommen", "result": None, "_deadline": now() + timeout_s}
        self.jobs[jid] = j
        # alte Jobs aufräumen
        if len(self.jobs) > 300:
            for k in sorted(self.jobs, key=lambda k: self.jobs[k]["created"])[:100]:
                if self.jobs[k]["state"] in ("done", "failed", "timeout", "cancelled"):
                    self.jobs.pop(k, None)
        return j

    @staticmethod
    def job_public(j):
        return {k: v for k, v in j.items() if not k.startswith("_")}

    def job_update(self, j, **kw):
        with self.lock:
            j.update(kw)
            self.emit("job", self.job_public(j))

    def job_active(self, j):
        return j["state"] in ("queued", "waiting_for_sensor", "running", "awaiting_confirmation")

    def tick(self):
        """jede Sekunde: Fristen der Jobs, Kopplungsfenster, flüchtige Daten sichern."""
        t = now()
        with self.lock:
            for j in list(self.jobs.values()):
                if self.job_active(j) and t > j["_deadline"]:
                    self.job_update(j, state="timeout", message="Sensor hat innert Reaktionszeit nicht geantwortet")
                    if self.central:
                        self.central.cancel_job(j["id"])
                    if j["kind"] == "calibration_capture":
                        for r in self.runs.values():
                            if r.get("_job") == j["id"] and r["state"].startswith("measuring"):
                                r["state"] = "await_dry" if r["dry"] is None else "await_wet"
            if self.pairing["active"] and self.pairing["until"] < t:
                self.pairing.update(active=False, until=None, candidates={})
                self.emit("pairing", self.pairing_out())
            if t - self.last_flush > VOLATILE_FLUSH_S:
                self.flush_volatile()
        self.time.refresh()

    def flush_volatile(self):
        rows = [(s["addr"], {k: v for k, v in s.items() if k not in ("id", "addr")})
                for s in (self.sensors.get(sid) for sid in list(self.volatile_dirty)) if s]
        self.store.save_sensor_docs(rows)
        self.volatile_dirty.clear()
        self.last_flush = now()

    # ================================================================== Funk: Advertising (aus central.py)
    def on_adv(self, adv: P.Adv) -> bool:
        """-> True, wenn das Gateway jetzt verbinden soll (PROTOCOL 2.5 Regel 2)."""
        with self.lock:
            t = now()
            if adv.has(P.ST_PAIRING) and self.pairing["active"]:
                c = self.pairing["candidates"].get(adv.addr)
                new = c is None
                known = adv.addr in self.by_addr
                self.pairing["candidates"][adv.addr] = {
                    "device": P.sensor_name(adv.addr), "address": adv.addr, "rssi_dbm": int(adv.rssi or -99),
                    "fw_version": c.get("fw_version") if c else None, "hw_rev": "A-32 rev A",
                    "first_seen": c["first_seen"] if c else iso(t), "known": known, "_seen": t}
                if new:
                    self.emit("pairing", self.pairing_out())
            s = self.sensor_by_addr(adv.addr)
            if not s:
                return False
            s["last_seen"] = t
            if adv.rssi is not None:
                s["rssi"] = int(adv.rssi) if s.get("rssi") is None else int(round(0.7 * s["rssi"] + 0.3 * adv.rssi))
            self._count_adv(s, t)
            self.volatile_dirty.add(s["id"])
            if adv.has(P.ST_LOCKED):
                if not (s.get("error") or {}).get("code") == "0x0B":
                    s["error"] = {"code": "0x0B", "text": P.ERRORS[0x0B], "t": iso(t)}
                return False
            if not self.store.sensor_key(adv.addr):
                return False
            ms = self.max_seq.get(adv.addr)
            return bool(adv.has(P.ST_DATA_PENDING) or adv.has(P.ST_OTA_TEST)
                        or (ms is not None and (ms & 0xFFFF) != adv.seq_lo)
                        or s.get("pending_config") or (self.central and self.central.has_pending(adv.addr))
                        or (self.time.valid and t - s.get("last_time_set", 0) > SESSION_INFO_STALE)
                        or self._rollout_wants(s["id"]))

    def _count_adv(self, s, t):
        st = self.adv_stats.setdefault(s["id"], {"hour": int(t // 3600), "n": 0, "hist": []})
        h = int(t // 3600)
        if h != st["hour"]:
            st["hist"] = (st["hist"] + [(st["hour"], st["n"])])[-24:]
            st["hour"], st["n"] = h, 0
        st["n"] += 1

    def missed_pct(self, sid):
        """Anteil verpasster Advertisings der letzten Stunden (Grundlage für P_MISS, OP-K12/FW-P8)."""
        st = self.adv_stats.get(sid)
        if not st or not st["hist"]:
            return None
        interval = P.adv_interval_ms(self.settings["reaction_time_min"], self.cfg.p_miss) / 1000
        exp = 3600 / interval
        got = sum(n for _, n in st["hist"]) / len(st["hist"])
        return round(max(0.0, 100 * (1 - got / exp)), 1)

    # ================================================================== Funk: Sitzung
    def desired_settings(self, s):
        """Einstellungen für den Sensor (PROTOCOL Kap. 8) aus API-Einstellungen, Pflanze und Kalibrierung."""
        se = self.settings
        per_day = self.per_day(s["id"])
        p = self.plants.get(s.get("plant_id")) if s.get("plant_id") else None
        led = se["led"]
        win = led["water_window"]
        hm = lambda x: int(x[:2]) * 60 + int(x[3:5])  # noqa: E731
        wl = se["led"]["water_hint"] if not p or p.get("water_led", "inherit") == "inherit" else p["water_led"] == "on"
        wl = wl and s.get("led_enabled", True)
        v = {"meas_interval_s": max(900, min(86400, round(86400 / per_day))),
             "adv_interval_ms": max(1000, min(150000, P.adv_interval_ms(se["reaction_time_min"], self.cfg.p_miss))),
             "water_led": 1 if wl else 0, "led_window": (hm(win["start"]), hm(win["end"])),
             "led_weekdays": P.weekdays_mask(win.get("weekdays")),   # TLV 0x0F (v2, W-7)
             "led_level": LED_LEVEL.get(led.get("brightness", "normal"), 70),
             "heartbeat_led": 1 if led.get("enabled", True) and s.get("led_enabled", True) else 0,
             "batt_low_flag": 1 if s.get("battery") and s["battery"]["state"] != "ok" else 0}
        water_raw, air, flood = 0, 0, 0
        if p:
            cal = self.cal_for(s["addr"], p["substrate"])
            dry, wet = cal["dry"]["raw"], cal["wet"]["raw"]
            if C.span_ok(dry, wet):
                at = lambda pct: int(round(dry + (wet - dry) * pct / 100))  # noqa: E731
                water_raw = at(self.thr(p))
                air, flood = at(-C.AIR_MARGIN_PP), at(100 + C.FLOOD_MARGIN_PP)
        v["water_raw"] = max(0, min(0xFFFF, water_raw))
        v["air_flood_raw"] = (max(0, min(0xFFFF, air)), max(0, min(0xFFFF, flood)))
        return v

    def on_session_info(self, addr, si: P.SessionInfo, rssi=None):
        """SECURE#0 ausgewertet. Speichert Synchronpunkt, aktualisiert Sensor. -> Plan für die Sitzung."""
        with self.lock:
            s = self.sensor_by_addr(addr)
            if not s:
                return {}
            t = now()
            self.store.add_syncpoint(addr, si.boot_id, si.uptime, self.time.now(), self.time.valid)
            prev_boot = s.get("boot_id")
            s.update(last_seen=t, fw_version=si.fw_version, hw_rev=f"rev 0x{si.hw_rev:02X}", boot_id=si.boot_id,
                     lost_records=si.lost_records, reset_reason=P.RESET_REASONS[si.reset_reason] if si.reset_reason < 7 else str(si.reset_reason),
                     slot_confirmed=bool(si.slot & 1), ota_result=si.ota_result, sec_cnt=si.sec_cnt)
            pend = 0 if si.seq_last == 0xFFFFFFFF else max(0, si.seq_last - si.seq_oldest_unacked + 1)
            s["buffered_records"] = pend
            self._battery(s, si, t)
            if si.last_error and si.last_error in P.ERRORS and (0x20 <= si.last_error <= 0x32 or 0x50 <= si.last_error <= 0x55):
                if not s.get("error") or s["error"]["code"] != f"0x{si.last_error:02X}":
                    self.log("warn", "sensor_error", f"{s['id']}: {P.ERRORS[si.last_error]}", s["id"])
                s["error"] = {"code": f"0x{si.last_error:02X}", "text": P.ERRORS[si.last_error], "t": iso(t)}
            elif s.get("error"):
                s["error"] = None
            if prev_boot is not None and si.boot_id != prev_boot:
                self.log("info", "sensor_boot", f"{s['id']}: Neustart ({s['reset_reason']})", s["id"])
            if si.lost_records and si.lost_records != s.get("_lost_logged"):
                s["_lost_logged"] = si.lost_records
                self.log("warn", "records_lost", f"{s['id']}: {si.lost_records} Messwerte im Sensor überschrieben", s["id"])
            plan = {"time_set": self.time.valid and (t - s.get("last_time_set", 0) > SESSION_INFO_STALE
                                                      or prev_boot != si.boot_id or not s.get("tz_min_sent") == self.tz_offset_min()
                                                      or bool(si.state & P.ST_TIME_UNSYNCED)),
                    "tz_min": self.tz_offset_min()}
            want = self.desired_settings(s)
            if want != s.get("settings_applied") or si.settings_ver != s.get("settings_ver"):
                ver = (max(si.settings_ver, s.get("settings_ver", 0)) + 1) & 0xFFFF or 1
                plan["settings"] = (ver, want)
            self._rollout_check(s)
            self.save_sensor(s)
            return plan

    def tz_offset_min(self):
        off = datetime.now(self.tz()).utcoffset()
        return int(off.total_seconds() // 60) if off else 0

    def time_sent(self, addr, tz_min):
        s = self.sensor_by_addr(addr)
        if s:
            s["last_time_set"], s["tz_min_sent"] = now(), tz_min

    def settings_applied(self, addr, ver, values):
        with self.lock:
            s = self.sensor_by_addr(addr)
            if s:
                s.update(settings_ver=ver, settings_applied=values, pending_config=False)
                self.save_sensor(s)

    def _battery(self, s, si, t):
        """Batterie (REQ-ENE-05): Ladungszähler seit Power-on-Reset gegen nutzbare Kapazität, Rate gemessen
        (≥ 1 Tag Abstand) oder Modell; Spannung unter Last begrenzt die Schätzung. Alles ANNAHME bis FW-P6."""
        hist = s.setdefault("_charge", [])
        if si.reset_reason == 0 and hist and si.charge_uc < hist[-1][1]:
            hist.clear()  # neue Zelle (Power-on, Zähler kleiner)
        if not hist or t - hist[-1][0] > 86400:
            hist.append((t, si.charge_uc))
            del hist[:-8]
        rate = MODEL_UC_PER_DAY
        if len(hist) >= 2 and hist[-1][0] - hist[0][0] >= 86400 and hist[-1][1] > hist[0][1]:
            rate = max(20_000, (hist[-1][1] - hist[0][1]) / ((hist[-1][0] - hist[0][0]) / 86400))
        remaining = max(0.0, CAP_UC - si.charge_uc)
        pct = int(round(100 * remaining / CAP_UC))
        days = int(remaining / rate)
        v = si.vbat_load_mv
        if v < 2450:
            days, pct = min(days, 3), min(pct, 3)
        elif v < 2550:  # Rückfallschwelle „Batterie tief“ (PROTOCOL Kap. 8, ANNAHME)
            days, pct = min(days, 14), min(pct, 10)
        state = "critical" if days < 7 else "low" if days < 30 else "ok"
        old = (s.get("battery") or {}).get("state")
        s["battery"] = {"mv": int(v), "pct": max(0, min(100, pct)), "days_left": days, "state": state}
        if old and old != state and state != "ok":
            self.log("warn", "battery", f"{s['id']}: Batterie {state} (noch ca. {days} Tage)", s["id"])

    def store_records(self, addr, recs, via_read=True):
        """Datensätze dauerhaft speichern (vor der Quittung). -> (neu gespeichert, höchste seq)."""
        if not recs:
            return 0, self.max_seq.get(addr)
        with self.lock:
            pts = [timesync.SyncPoint(r["boot_id"], r["uptime"], r["gw_time"], bool(r["valid"])) for r in self.store.syncpoints(addr)]
            t_now = self.time.now()
            rows = []
            for r in recs:
                t, fl = timesync.reconstruct(r.boot_id, r.uptime_s, pts, t_now, self.time.valid)
                if not self.time.valid:
                    fl |= timesync.FLAG_UNSYNCED
                if r.cause in (1, 2):
                    fl |= 1
                if via_read and t_now - t > 3600:
                    fl |= 8  # nachgeliefert
                if r.flags & 0x23:
                    fl |= 16  # Plausibilitätswarnung (Ausreisser, Streuung, Messkette)
                if t > t_now + 300:
                    fl |= 16  # Zukunft (ARCHITECTURE 4)
                rows.append({"seq": r.seq, "t": t, "raw": r.c_probe if r.valid else None,
                             "c_diag": None if r.c_diag == 0xFFFF else r.c_diag, "temp": r.temp_c, "vbat": r.vbat_mv,
                             "cause": r.cause, "sflags": r.flags, "flags": fl, "boot_id": r.boot_id, "uptime": r.uptime_s})
            for x in rows:
                if x["raw"] is None:
                    x["flags"] |= 16  # c_probe ungültig (0xFFFF): Zeile bleibt für Lückenfreiheit, Index = null
            n = self.store.insert_readings(addr, rows)
            ms = max(r.seq for r in recs)
            self.max_seq[addr] = max(ms, self.max_seq.get(addr) or 0)
            s = self.sensor_by_addr(addr)
            if n and s:
                pid = s.get("plant_id")
                self.invalidate(pid)
                if pid in self.plants:
                    newest = max(rows, key=lambda x: x["t"])
                    rec = self._rec(newest | {"cause": newest["cause"]}) | {"_addr": addr}
                    self.emit("measurement", {"plant_id": pid, "sensor_id": s["id"], "reading": self.reading_out(rec, self.plants[pid])})
                    self.emit("plant", self.plant_out(self.plants[pid]))
                    if self.mqtt:
                        self.mqtt.publish_plant(self.plant_out(self.plants[pid]))
            return n, ms

    def retime_uncertain(self, addr):
        """Nach neuem Synchronpunkt: Werte mit rekonstruierter/unsicherer Zeit der letzten 90 Tage neu rechnen."""
        with self.lock:
            pts = [timesync.SyncPoint(r["boot_id"], r["uptime"], r["gw_time"], bool(r["valid"])) for r in self.store.syncpoints(addr)]
            upd = []
            for r in self.store.uncertain_readings(addr, now() - 90 * 86400):
                if r["boot_id"] is None:
                    continue
                t, fl = timesync.reconstruct(r["boot_id"], r["uptime"], pts, now(), self.time.valid)
                upd.append((t, (r["flags"] & ~6) | fl, r["seq"]))
            self.store.retime(addr, upd)
            if upd:
                s = self.sensor_by_addr(addr)
                self.invalidate(s.get("plant_id") if s else None)

    def acked(self, addr, upto, seq_last):
        s = self.sensor_by_addr(addr)
        if s:
            s["buffered_records"] = max(0, seq_last - upto) if seq_last != 0xFFFFFFFF else 0
            self.volatile_dirty.add(s["id"])

    def contiguous_ack(self, addr, seq_from, received_max):
        """Höchste lückenlos GESPEICHERTE seq ab seq_from (ACK_RECORDS upto, PROTOCOL 6.2 Regel 2)."""
        have = set(self.store.seqs_from(addr, seq_from))
        upto = seq_from - 1
        while upto + 1 in have and upto + 1 <= received_max:
            upto += 1
        return upto

    # ================================================================== Kopplung
    def pairing_out(self):
        p = self.pairing
        if p["active"] and p["until"] < now():
            p.update(active=False, until=None, candidates={})
        cands = [{k: v for k, v in c.items() if not k.startswith("_")} for c in p["candidates"].values()
                 if now() - c["_seen"] < 30]
        return {"active": p["active"], "until": iso(p["until"]) if p["active"] else None, "candidates": cands}

    def pair_finished(self, addr, k_link, rsp: P.PairRsp, plant_spec):
        """Kopplung gültig (beide Bestätigungen). Schlüssel speichern, Sensor und Pflanze anlegen."""
        with self.lock:
            sid = P.sensor_name(addr)
            other = self.sensors.get(sid)
            if other and other["addr"] != addr:
                raise ApiError(409, "conflict", f"Kennung {sid} ist bereits an einen anderen Sensor vergeben (16-bit-Kurzname)")
            t = now()
            s = self.sensors.get(sid) or {"id": sid, "addr": addr, "plant_id": None, "interval_per_day": None,
                                           "led_enabled": True}
            s.update(paired=iso(t), last_seen=t, fw_version="%d.%d.%d" % (rsp.fw_ver[0], rsp.fw_ver[1], struct.unpack("<H", rsp.fw_ver[2:4])[0]),
                     hw_rev=f"rev 0x{rsp.hw_rev:02X}", battery=s.get("battery"), rssi=s.get("rssi"), error=None,
                     unpairing=False, pending_config=True, settings_ver=0, settings_applied=None, buffered_records=None)
            self.sensors[sid] = s
            self.by_addr[addr] = sid
            self.store.save_sensor(addr, sid, {k: v for k, v in s.items() if k not in ("id", "addr")}, k_link=k_link, keep_key=False)
            self.max_seq.setdefault(addr, self.store.max_seq(addr))
            for sub in ("erde", "granulat"):
                if sub not in self.cal.get(addr, {}):
                    self.cal.setdefault(addr, {})[sub] = self.default_cal(sub)
                    self.store.save_calibration(addr, sub, self.cal[addr][sub], history=False)
            if plant_spec.get("plant_id"):
                p = self.plants[plant_spec["plant_id"]]
            else:
                p = self.create_plant(plant_spec["plant"])
            self.assign_sensor(p, sid, False)
            self.pairing.update(active=False, until=None, candidates={})
            self.log("info", "paired", f"Sensor {sid} ({addr}) gekoppelt mit „{p['name']}“", sid)
            self.emit("plant", self.plant_out(p))
            return sid, p["id"]

    # ================================================================== Tagebuch
    def journal_add(self, pid, t, typ, source, note="", amount_ml=None):
        self.next_journal += 1
        e = {"id": f"j{self.next_journal}", "plant_id": pid, "t": int(t), "type": typ, "source": source,
             "status": "confirmed", "note": note, "amount_ml": amount_ml}
        self.journal[e["id"]] = e
        self.store.save_journal(e)
        self.invalidate(pid)
        return e

    # ================================================================== Pflanzen
    def create_plant(self, body) -> dict:
        name = str(body.get("name", "")).strip()
        if not name:
            raise ApiError(400, "validation", "Name fehlt", "name")
        sid = body.get("sensor_id")
        if sid:
            s = self.sensors.get(sid)
            if not s:
                raise ApiError(404, "not_found", "Sensor nicht gefunden")
            if s.get("plant_id"):
                raise ApiError(409, "conflict", "Sensor ist bereits einer Pflanze zugeordnet")
        sp = body.get("species")
        if sp is not None and sp not in self.species_keys():
            raise ApiError(400, "validation", "Unbekannte Art", "species")
        pid = self.next_plant
        self.next_plant += 1
        p = {"id": pid, "name": name, "substrate": body.get("substrate", "erde"),
             "threshold_pct": body.get("threshold_pct", self.settings["default_threshold_pct"]),
             "water_led": body.get("water_led", "inherit"), "notes": body.get("notes", ""), "sensor_id": None,
             "created": iso(now()), "species": sp, "upper_pct": body.get("upper_pct"),
             "location": body.get("location", ""), "pot": body.get("pot") or {"diameter_cm": None, "material": None, "drainage": True},
             "regime": body.get("regime"), "winter_factor": body.get("winter_factor"), "winter": body.get("winter", True)}
        self.check_range(p)
        self.plants[pid] = p
        self.store.save_plant(p)
        if sid:
            self.assign_sensor(p, sid, False)
        return p

    @staticmethod
    def check_range(p):
        up = p.get("upper_pct")
        if up is not None and up <= p["threshold_pct"] + 5:
            raise ApiError(400, "validation", "Obergrenze muss mindestens 5 %-Punkte über der Giessschwelle liegen", "upper_pct")

    def assign_sensor(self, p, sid, move_history):
        t = now()
        if p.get("sensor_id"):
            old = self.sensors.get(p["sensor_id"])
            for a in self.assign:
                if a["plant"] == p["id"] and a["to"] is None:
                    a["to"] = t
            if old:
                old["plant_id"] = None
                old["pending_config"] = True
                self.save_sensor(old)
            p["sensor_id"] = None
        if sid is not None:
            s = self.sensors.get(sid)
            if not s:
                raise ApiError(404, "not_found", "Sensor nicht gefunden")
            if s.get("plant_id") and s["plant_id"] != p["id"] and s["plant_id"] in self.plants:
                other = self.plants[s["plant_id"]]
                for a in self.assign:
                    if a["sensor"] == s["addr"] and a["to"] is None:
                        a["to"] = t
                other["sensor_id"] = None
                self.store.save_plant(other)
            if move_history:
                for a in self.assign:
                    if a["sensor"] == s["addr"]:
                        a["plant"] = p["id"]
            self.assign.append({"sensor": s["addr"], "plant": p["id"], "from": t, "to": None})
            s["plant_id"] = p["id"]
            s["pending_config"] = True
            p["sensor_id"] = sid
            self.save_sensor(s)
        self.store.save_plant(p)
        self.store.save_assignments(self.assign)
        self.invalidate()

    # ================================================================== Arten (app/data/species.json)
    def _species_meta(self):
        if "_species_meta" not in self.cache:
            try:
                self.cache["_species_meta"] = json.loads((self.cfg.app_dir / "data" / "species.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                self.cache["_species_meta"] = {}
        return self.cache["_species_meta"]

    def species(self):
        """Artenprofile aus app/data/species.json (PFLANZENPROFILE.md, D-021) -> Schema Species (openapi.yaml)."""
        if "_species" in self.cache:
            return self.cache["_species"]
        data = self._species_meta()
        regimes = data.get("regimes", {}) if isinstance(data, dict) else {}
        srcs = data.get("sources", {}) if isinstance(data, dict) else {}
        items = data.get("species", []) if isinstance(data, dict) else data
        out = []
        for it in items or []:
            try:
                key = it.get("id") or it["key"]
                rg = it.get("regime")
                cls = it.get("water_class")
                st = it.get("start") or {}
                lo = st.get("water_at_pct")
                hi = st.get("upper_pct")
                if lo is None and cls in CLASSES:
                    lo, hi = CLASSES[cls][0], CLASSES[cls][1]
                o = {"key": key, "name": it.get("name_de") or it.get("name") or key, "latin": it.get("botanical") or it.get("latin", ""),
                     "water_class": cls, "water_class_text": it.get("class") or (CLASSES.get(cls, (0, 0, ""))[2] if cls else "Sonderfall"),
                     "start_range": {"lower_pct": lo, "upper_pct": hi, **({"reminder_days": st["reminder_days"]} if st.get("reminder_days") else {})},
                     "source": "quelle" if it.get("sources") else "startwert",
                     "note": it.get("notes_de") or it.get("note") or SPECIES_FALLBACK_NOTE,
                     "illustration": it.get("illustration") if it.get("illustration") in ILLUSTRATIONS else "generic",
                     "regime": rg, "regime_text": (regimes.get(rg) or {}).get("text"), "dryness": it.get("dryness_de"),
                     "dryness_source": it.get("dryness_source"), "winter": it.get("winter_de"),
                     "winter_factor": it.get("winter_factor"), "waterlogging": it.get("waterlogging"), "drought": it.get("drought"),
                     "substrate": it.get("substrate_de"), "start_note": "Startwert von fluidi (ANNAHME), an die eigene Pflanze anpassen.",
                     "sources": [{"id": sid, **{k: srcs[sid].get(k) for k in ("title", "publisher", "url", "retrieved", "type")}}
                                 for sid in it.get("sources", []) if sid in srcs]}
                out.append(o)
            except (KeyError, TypeError, AttributeError):
                continue
        if not any(x["key"] == "generic" for x in out):
            lo, hi, txt = CLASSES["medium"]
            out.append({"key": "generic", "name": "Andere Pflanze", "latin": "", "water_class": "medium", "water_class_text": txt,
                        "start_range": {"lower_pct": lo, "upper_pct": hi}, "source": "startwert", "note": SPECIES_FALLBACK_NOTE,
                        "illustration": "generic", "regime": "B", "sources": []})
        self.cache["_species"] = out
        return out

    def species_keys(self):
        return {x["key"] for x in self.species()}

    # ================================================================== Firmware-Verteilung
    def _rollout_wants(self, sid):
        ro = self.rollout
        return bool(ro and not ro["finished"] and any(i["sensor_id"] == sid and i["state"] in ("pending", "waiting_for_sensor", "rebooting")
                                                        for i in ro["items"]))

    def rollout_item(self, sid):
        ro = self.rollout
        if not ro or ro["finished"]:
            return None
        return next((i for i in ro["items"] if i["sensor_id"] == sid), None)

    def rollout_update(self, item, **kw):
        with self.lock:
            item.update(kw)
            ro = self.rollout
            if all(i["state"] in ("done", "failed", "skipped", "waiting_for_sensor") for i in ro["items"]) and \
                    not any(i["state"] == "waiting_for_sensor" for i in ro["items"]):
                ro["finished"] = iso(now())
            self.emit("rollout", ro)

    def _rollout_check(self, s):
        """Nach Neustart mit neuem Abbild: bestätigt oder zurückgefallen (PROTOCOL 9.4/9.5)."""
        it = self.rollout_item(s["id"])
        if not it or it["state"] != "rebooting":
            return
        want = self.rollout["version"].split("+")[0]
        if s.get("fw_version") == want and s.get("slot_confirmed"):
            self.rollout_update(it, state="done", progress=1.0, message=f"Version {want} aktiv und bestätigt")
            self.log("info", "fw_done", f"{s['id']}: Firmware {want} aktiv", s["id"])
        elif s.get("ota_result") not in (0, 0xFF, None):
            self.rollout_update(it, state="failed", message=P.ERRORS.get(s["ota_result"], f"Fehler 0x{s['ota_result']:02X}"))

    def image_path(self, version):
        return self.cfg.data_dir / "images" / f"fluidi-sensor-{version}.bin"

    # ================================================================== Raumplan
    @staticmethod
    def default_roomplan():
        """Ein Raum (D-020), leer; der Auftraggeber liefert später einen genaueren Plan."""
        return {"version": 1, "updated": iso(now()), "rooms": [{
            "id": "r1", "name": "Büro", "width_cm": 600, "depth_cm": 450, "north_deg": 0, "sun_walls": ["s"],
            "openings": [{"type": "window", "wall": "s", "offset_cm": 150, "length_cm": 180},
                         {"type": "door", "wall": "n", "offset_cm": 450, "length_cm": 95}],
            "furniture": [], "plants": []}]}

    # ================================================================== Hinweise (In-App, Badge, Dashboard)
    def alerts(self):
        out = []
        t = now()
        rules = self.settings["notifications"]["rules"]
        for p in self.plants.values():
            po = self.plant_out(p)
            L, st = po["latest"], po["status"]
            name = p["name"]
            if st["sensor_error"]:
                out.append(("critical", "sensor_error", p, f"{name}: {st['sensor_error']}"))
            if L and L["moisture_state"] == "air" and not st["stale"]:
                out.append(("critical", "air", p, f"{name}: Sensor nicht in der Erde?"))
            if L and L["moisture_state"] == "flooded":
                out.append(("critical", "flooded", p, f"{name}: zu nass oder überflutet?"))
            if st["needs_water"] and not st["stale"] and rules.get("needs_water", True):
                lvl = "critical" if po["mood"] == "parched" else "warn"
                out.append((lvl, "needs_water", p, f"{name} braucht Wasser ({L['moisture_pct']:.0f} %)"))
            if st["stale"]:
                out.append(("warn", "stale", p, f"{name}: keine neuen Werte"))
            if po["battery"] and po["battery"]["state"] != "ok" and rules.get("battery_low", True):
                lvl = "critical" if po["battery"]["state"] == "critical" else "warn"
                out.append((lvl, "battery_low", p, f"{name}: Batterie noch ca. {po['battery']['days_left']} Tage"))
            if po["signal"] and po["signal"]["quality"] <= 1:
                out.append(("info", "weak_signal", p, f"{name}: Funksignal schwach ({po['signal']['rssi_dbm']} dBm)"))
            if po["salt"]["state"] == "suspected":
                out.append(("info", "salt", p, f"{name}: {po['salt']['text']}"))
            for hn in po["care"]["hints"]:
                if hn["kind"] in ("too_wet", "reminder"):
                    out.append(("warn", hn["kind"], p, f"{name}: {hn['text']}"))
        order = {"critical": 0, "warn": 1, "info": 2}
        out.sort(key=lambda x: (order[x[0]], x[2]["name"]))
        res, seen = [], set()
        for lvl, kind, p, text in out:
            aid = f"{kind}-{p['id']}"
            seen.add(aid)
            since = self.alert_since.setdefault(aid, t)
            if kind == "needs_water" and t - since < rules.get("needs_water_delay_h", 0) * 3600:
                continue
            res.append({"id": aid, "level": lvl, "kind": kind, "plant_id": p["id"], "sensor_id": p.get("sensor_id"),
                        "since": iso(since), "text": text})
        for k in list(self.alert_since):
            if k not in seen:
                self.alert_since.pop(k)
        return res
