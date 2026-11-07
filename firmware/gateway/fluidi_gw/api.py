"""REST-Routen des Gateways (docs/interfaces/GATEWAY_API.md, app/api/openapi.yaml – normativ).

Gleiche Routen und Zugriffsregeln wie die Referenz app/dev/mock_server.py; hier gegen das echte Modell
(model.py), den Funkteil (central.py) und SQLite. Zugriff: 'public' immer, 'read' = public_read oder Sitzung,
'session' = Sitzung, 'write' = Sitzung + CSRF (+ elevated für heikle Aktionen, GATEWAY_API 3.3).
"""
from __future__ import annotations

import io
import json
import math
import re
import secrets
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from . import backup as BK
from . import mcuboot
from . import protocol as P
from . import sysinfo
from .model import ApiError, iso, now
from .shared import AN, C

ROUTES: list = []
VERSION = "0.5.0"


def route(method, tpl, *, auth="write", elevated=False):
    rx = re.compile("^" + re.sub(r"\{(\w+)\}", r"(?P<\1>[^/]+)", tpl) + "$")

    def deco(fn):
        ROUTES.append((method, tpl, rx, fn, auth, elevated))
        return fn
    return deco


def _plant(M, plant_id) -> dict:
    try:
        p = M.plants.get(int(plant_id))
    except ValueError:
        p = None
    if not p:
        raise ApiError(404, "not_found", "Pflanze nicht gefunden")
    return p


def _sensor(M, sid) -> dict:
    s = M.sensors.get(sid)
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


def _need_radio(M):
    if not M.central:
        raise ApiError(409, "sensor_unreachable", "Funkteil nicht aktiv")


# ================================================================================ Auth (GATEWAY_API 3)
@route("GET", "/auth/status", auth="public")
def auth_status(h, sess, **_):
    M = h.M
    f = M.fails.get(h.client_ip(), {})
    locked_for = max(0, int(math.ceil(f.get("until", 0) - now())))
    h.send_json(200, {
        "setup_required": M.auth is None, "logged_in": bool(sess),
        "elevated_until": iso(sess["elevated_until"]) if sess and (sess.get("elevated_until") or 0) > now() else None,
        "session_expires": iso(sess["expires"]) if sess else None,
        "csrf": sess["csrf"] if sess else None, "public_read": M.settings["public_read"],
        "lockout": {"locked": locked_for > 0, "retry_after_s": locked_for, "failed_attempts": f.get("n", 0)},
    })


@route("POST", "/auth/setup", auth="public")
def auth_setup(h, body, **_):
    M = h.M
    if M.auth is not None:
        raise ApiError(409, "setup_done", "Das Gateway ist bereits eingerichtet")
    h.lock_check()
    import hmac
    code = str(body.get("setup_code", "")).replace("-", "").strip()
    if not M.setup_code or not hmac.compare_digest(code, M.setup_code.replace("-", "")):
        h.lock_fail()
        raise ApiError(401, "auth_failed", "Einrichtungscode falsch")
    pw = body.get("password", "")
    if not isinstance(pw, str) or len(pw) < 10:
        raise ApiError(400, "validation", "Passwort: mindestens 10 Zeichen", "password")
    M.set_password(pw)
    M.log("info", "setup", "Passwort gesetzt (Ersteinrichtung)")
    s, hdr = h.new_session()
    h.send_json(200, h.session_body(s), hdr)


@route("POST", "/auth/login", auth="public")
def auth_login(h, body, **_):
    M = h.M
    if M.auth is None:
        raise ApiError(409, "setup_required", "Bitte zuerst das Gateway einrichten")
    h.lock_check()
    if not M.check_password(str(body.get("password", ""))):
        h.lock_fail()
        f = M.fails.get(h.client_ip(), {})
        left = max(0, 5 - f.get("n", 0))
        raise ApiError(401, "auth_failed", "Passwort falsch" + (f" (noch {left} Versuche bis zur Sperre)" if left else ""))
    s, hdr = h.new_session(bool(body.get("remember")))
    M.log("info", "login", f"Anmeldung von {h.client_ip()}")
    h.send_json(200, h.session_body(s), hdr)


@route("POST", "/auth/logout", auth="session")
def auth_logout(h, **_):
    h.end_session()
    h.send_json(204, None, {"Set-Cookie": "fluidi_sid=; Path=/; Max-Age=0; HttpOnly; SameSite=Strict"})


@route("POST", "/auth/elevate", auth="write")
def auth_elevate(h, sess, body, **_):
    h.lock_check()
    if not h.M.check_password(str(body.get("password", ""))):
        h.lock_fail()
        raise ApiError(401, "auth_failed", "Passwort falsch")
    sess["elevated_until"] = now() + 300
    h.save_session(sess)
    h.send_json(200, h.session_body(sess))


@route("POST", "/auth/password", elevated=True)
def auth_password(h, sess, body, **_):
    pw = body.get("new_password", "")
    if not isinstance(pw, str) or len(pw) < 10:
        raise ApiError(400, "validation", "Passwort: mindestens 10 Zeichen", "new_password")
    h.M.set_password(pw)
    h.end_other_sessions()
    h.M.log("info", "password", "Passwort geändert, andere Sitzungen beendet")
    h.send_json(204, None)


# ================================================================================ Pflanzen
@route("GET", "/plants", auth="read")
def plants_list(h, **_):
    h.send_json(200, [h.M.plant_out(p) for p in sorted(h.M.plants.values(), key=lambda p: p["name"].lower())])


@route("POST", "/plants")
def plants_create(h, body, **_):
    p = h.M.create_plant(body)
    out = h.M.plant_out(p)
    h.M.emit("plant", out)
    h.send_json(201, out)


@route("GET", "/plants/{plant_id}", auth="read")
def plant_get(h, plant_id, **_):
    h.send_json(200, h.M.plant_out(_plant(h.M, plant_id)))


@route("PATCH", "/plants/{plant_id}")
def plant_patch(h, plant_id, body, **_):
    M = h.M
    real = _plant(M, plant_id)
    p = dict(real)
    for k in ("name", "substrate", "threshold_pct", "water_led", "notes", "species", "upper_pct", "location", "pot",
              "regime", "winter_factor", "winter"):
        if k in body:
            v = body[k]
            if k == "name":
                v = str(v).strip()
                if not v:
                    raise ApiError(400, "validation", "Name fehlt", "name")
            if k == "threshold_pct" and not (isinstance(v, int) and 0 <= v <= 100):
                raise ApiError(400, "validation", "Schwelle 0–100 %", k)
            if k == "substrate" and v not in ("erde", "granulat"):
                raise ApiError(400, "validation", "Substrat erde oder granulat", k)
            if k == "regime" and v not in (None, "A", "B", "C", "D"):
                raise ApiError(400, "validation", "Regime A/B/C/D", k)
            if k == "winter_factor" and v is not None and not (isinstance(v, (int, float)) and 0.1 <= v <= 1.0):
                raise ApiError(400, "validation", "Winterfaktor 0.1–1.0", k)
            if k == "species" and v is not None and v not in M.species_keys():
                raise ApiError(400, "validation", "Unbekannte Art", k)
            p[k] = v
    M.check_range(p)
    real.update(p)
    M.store.save_plant(real)
    if real.get("sensor_id") and ({"threshold_pct", "water_led", "substrate"} & set(body)):
        s = M.sensors[real["sensor_id"]]
        s["pending_config"] = True
        M.save_sensor(s)
    M.invalidate(real["id"])
    out = M.plant_out(real)
    M.emit("plant", out)
    h.send_json(200, out)


@route("DELETE", "/plants/{plant_id}")
def plant_delete(h, plant_id, **_):
    M = h.M
    p = _plant(M, plant_id)
    M.assign_sensor(p, None, False)
    M.plants.pop(p["id"])
    M.store.delete_plant(p["id"])
    for r in M.roomplan["rooms"]:
        r["plants"] = [x for x in r.get("plants", []) if x["plant_id"] != p["id"]]
    M.store.meta_set("roomplan", M.roomplan)
    M.emit("plant_deleted", {"id": p["id"]})
    h.send_json(204, None)


@route("PUT", "/plants/{plant_id}/sensor")
def plant_sensor(h, plant_id, body, **_):
    p = _plant(h.M, plant_id)
    if "sensor_id" not in body:
        raise ApiError(400, "validation", "sensor_id fehlt", "sensor_id")
    h.M.assign_sensor(p, body["sensor_id"], bool(body.get("move_history")))
    out = h.M.plant_out(p)
    h.M.emit("plant", out)
    h.send_json(200, out)


@route("GET", "/plants/{plant_id}/series", auth="read")
def plant_series(h, plant_id, q, **_):
    M = h.M
    p = _plant(M, plant_id)
    t1, t0 = _int(q, "to"), _int(q, "from")
    if t1 <= t0 or t1 - t0 > 3 * 366 * 86400:
        raise ApiError(400, "validation", "Zeitbereich ungültig (max. 3 Jahre)", "from")
    res = q.get("res", "auto")
    if res not in ("auto", "raw", "hour", "day"):
        raise ApiError(400, "validation", "res muss auto, raw, hour oder day sein", "res")
    if res == "auto":
        res = C.choose_resolution(t0, t1, M.per_day(p.get("sensor_id")) + 2)
    rows = M.plant_records(p["id"], t0, t1)
    out = {"plant_id": p["id"], "from": t0, "to": t1, "res": res, "timezone": M.settings["time"]["timezone"],
           "threshold_pct": p["threshold_pct"]}
    ev = [(r, M.evaluate(r, p)) for _sid, r in rows]
    if res == "raw":
        out.update({"t": [r["t"] for r, _ in ev], "moisture": [e["moisture_pct"] for _, e in ev],
                    "temp_c": [r["temp"] for r, _ in ev], "raw": [r["raw"] for r, _ in ev], "flags": [r["flags"] for r, _ in ev]})
    else:
        out.update(C.aggregate([(r["t"], e["moisture_pct"], r["temp"]) for r, e in ev], res, out["timezone"]))
    out["events"] = [{"t": int(a["from"]), "type": "sensor_change", "text": f"Sensor {M.by_addr.get(a['sensor'], a['sensor'])} zugeordnet"}
                     for a in M.assign if a["plant"] == p["id"] and t0 <= a["from"] <= t1]
    out["events"] += [{"t": int(e["t"]), "type": "watering", "text": f"gegossen, +{e['delta']:.0f} %"}
                      for e in M.analysis(p["id"])["events_ok"] if t0 <= e["t"] <= t1]
    out["events"] += [{"t": int(e["t"]), "type": "fertilizing", "text": "gedüngt"} for e in M.journal.values()
                      if e["plant_id"] == p["id"] and e["type"] == "fertilizing" and t0 <= e["t"] <= t1]
    out["events"].sort(key=lambda e: e["t"])
    h.send_json(200, out)


def _measure_job(M, p, kind="measure", source_note=None):
    sid = p["sensor_id"]
    busy = [j for j in M.jobs.values() if j["sensor_id"] == sid and j["kind"] == kind and M.job_active(j)]
    if busy:
        return busy[0]
    _need_radio(M)
    j = M.new_job(kind, sid, p["id"])
    s = M.sensors[sid]

    def done(res):
        recs = res.get("records") or []
        with M.lock:
            pl = M.plants.get(p["id"])
            if not recs or not pl:
                return {}
            r = max(recs, key=lambda x: x.seq)
            row = M.store.q1("SELECT seq, t, raw, c_diag, temp, vbat, cause, sflags, flags FROM reading WHERE sensor=? AND seq=?", (s["addr"], r.seq))
            return {"reading": M.reading_out(M._rec(row) | {"_addr": s["addr"]}, pl)} if row else {}
    M.job_update(j, state="waiting_for_sensor", message="Warte auf Sensor (nächstes Funksignal)")
    M.central.submit(s["addr"], {"kind": "measure", "job": j, "on_done": done})
    return j


@route("POST", "/plants/{plant_id}/measure")
def plant_measure(h, plant_id, **_):
    M = h.M
    p = _plant(M, plant_id)
    if not p.get("sensor_id"):
        raise ApiError(409, "conflict", "Dieser Pflanze ist kein Sensor zugeordnet")
    h.send_json(202, M.job_public(_measure_job(M, p)))


# ================================================================================ Sensoren
@route("GET", "/sensors", auth="read")
def sensors_list(h, **_):
    h.send_json(200, [h.M.sensor_out(s) for s in sorted(h.M.sensors.values(), key=lambda s: s["id"])])


@route("GET", "/sensors/{sensor_id}", auth="read")
def sensor_get(h, sensor_id, **_):
    h.send_json(200, h.M.sensor_out(_sensor(h.M, sensor_id)))


@route("PATCH", "/sensors/{sensor_id}")
def sensor_patch(h, sensor_id, body, **_):
    s = _sensor(h.M, sensor_id)
    if "interval_per_day" in body:
        v = body["interval_per_day"]
        if v is not None and not (isinstance(v, int) and 1 <= v <= 96):
            raise ApiError(400, "validation", "Intervall 1–96 pro Tag", "interval_per_day")
        s["interval_per_day"] = v
    if "led_enabled" in body:
        s["led_enabled"] = bool(body["led_enabled"])
    s["pending_config"] = True
    h.M.save_sensor(s)
    h.send_json(200, h.M.sensor_out(s))


def remove_sensor(M, s, why="entkoppelt"):
    with M.lock:
        if s.get("plant_id") in M.plants:
            M.assign_sensor(M.plants[s["plant_id"]], None, False)
        M.sensors.pop(s["id"], None)
        M.by_addr.pop(s["addr"], None)
        M.store.delete_sensor(s["addr"])  # Schlüssel weg; Messwerte und Kalibrierhistorie bleiben (UC-11)
        M.log("info", "unpaired", f"Sensor {s['id']} {why}", s["id"])


@route("DELETE", "/sensors/{sensor_id}")
def sensor_delete(h, sensor_id, q, **_):
    M = h.M
    s = _sensor(M, sensor_id)
    if q.get("force") == "true":  # Sensor nicht erreichbar (z. B. defekt): nur im Gateway löschen
        remove_sensor(M, s, "lokal entfernt (Sensor nicht erreicht)")
        j = M.new_job("unpair", sensor_id, None)
        M.job_update(j, state="done", progress=1.0, message="Im Gateway entfernt. Sensor per Werkseinstellung zurücksetzen.")
        h.send_json(202, M.job_public(j))
        return
    _need_radio(M)
    s["unpairing"] = True
    j = M.new_job("unpair", sensor_id, s.get("plant_id"), timeout_s=max(300, M.settings["reaction_time_min"] * 60 + 30))
    M.job_update(j, state="waiting_for_sensor", message="Warte auf Sensor")
    M.central.submit(s["addr"], {"kind": "unpair", "job": j, "on_done": lambda res: remove_sensor(M, s) or {}})
    h.send_json(202, M.job_public(j))


@route("POST", "/sensors/{sensor_id}/identify")
def sensor_identify(h, sensor_id, **_):
    M = h.M
    s = _sensor(M, sensor_id)
    _need_radio(M)
    j = M.new_job("identify", sensor_id)
    M.job_update(j, state="waiting_for_sensor", message="Warte auf Sensor")
    M.central.submit(s["addr"], {"kind": "identify", "job": j, "seconds": 15})
    h.send_json(202, M.job_public(j))


@route("GET", "/sensors/{sensor_id}/calibration", auth="read")
def cal_get(h, sensor_id, **_):
    s = _sensor(h.M, sensor_id)
    h.send_json(200, {sub: h.M.cal_for(s["addr"], sub) for sub in ("erde", "granulat")})


@route("PUT", "/sensors/{sensor_id}/calibration/{substrate}")
def cal_put(h, sensor_id, substrate, body, **_):
    M = h.M
    s = _sensor(M, sensor_id)
    if substrate not in ("erde", "granulat"):
        raise ApiError(404, "not_found", "Unbekanntes Substrat")
    if not C.span_ok(body.get("dry_raw"), body.get("wet_raw")):
        raise ApiError(400, "calibration_span", "Trocken- und Nasswert liegen zu nahe beieinander")
    cal = M.make_cal(substrate, "manual", body["dry_raw"], body["wet_raw"], now())
    cal["temp_coeff_per_k"] = body.get("temp_coeff_per_k", 0.0)
    M.cal.setdefault(s["addr"], {})[substrate] = cal
    M.store.save_calibration(s["addr"], substrate, cal)
    s["pending_config"] = True
    M.invalidate()
    h.send_json(200, cal)


@route("DELETE", "/sensors/{sensor_id}/calibration/{substrate}")
def cal_delete(h, sensor_id, substrate, **_):
    M = h.M
    s = _sensor(M, sensor_id)
    if substrate not in ("erde", "granulat"):
        raise ApiError(404, "not_found", "Unbekanntes Substrat")
    cal = M.default_cal(substrate)
    M.cal.setdefault(s["addr"], {})[substrate] = cal
    M.store.save_calibration(s["addr"], substrate, cal)
    s["pending_config"] = True
    M.invalidate()
    h.send_json(200, cal)


@route("POST", "/sensors/{sensor_id}/calibration-runs")
def run_create(h, sensor_id, body, **_):
    M = h.M
    _sensor(M, sensor_id)
    for r in M.runs.values():
        if r["sensor_id"] == sensor_id and r["state"] not in ("committed", "cancelled", "failed"):
            r["state"] = "cancelled"
    rid = "c" + secrets.token_hex(4)
    samples = body.get("samples", 5)
    if not isinstance(samples, int) or not 3 <= samples <= 20:
        raise ApiError(400, "validation", "samples 3–20", "samples")
    run = {"id": rid, "sensor_id": sensor_id, "substrate": body.get("substrate", "erde"), "samples": samples,
           "state": "await_dry", "dry": None, "wet": None, "span_ok": None, "message": None,
           "expires": iso(now() + 6 * 3600)}
    M.runs[rid] = run
    h.send_json(201, run)


def _run(M, run_id):
    r = M.runs.get(run_id)
    if not r:
        raise ApiError(404, "not_found", "Kalibrierlauf nicht gefunden")
    return r


def _run_public(r):
    return {k: v for k, v in r.items() if not k.startswith("_")}


@route("GET", "/calibration-runs/{run_id}", auth="session")
def run_get(h, run_id, **_):
    h.send_json(200, _run_public(_run(h.M, run_id)))


@route("DELETE", "/calibration-runs/{run_id}")
def run_delete(h, run_id, **_):
    _run(h.M, run_id)["state"] = "cancelled"
    h.send_json(204, None)


@route("POST", "/calibration-runs/{run_id}/capture")
def run_capture(h, run_id, body, **_):
    M = h.M
    run = _run(M, run_id)
    point = body.get("point")
    if point not in ("dry", "wet"):
        raise ApiError(400, "validation", "point muss dry oder wet sein", "point")
    if run["state"] in ("committed", "cancelled", "failed") or run["state"].startswith("measuring"):
        raise ApiError(409, "conflict", "Lauf ist nicht bereit")
    s = _sensor(M, run["sensor_id"])
    _need_radio(M)
    run["state"] = "measuring_" + point
    j = M.new_job("calibration_capture", s["id"], s.get("plant_id"))
    run["_job"] = j["id"]

    def done(res):
        recs = [r for r in res.get("records") or [] if r.valid]
        temps = [r.temp_c for r in recs if r.temp_c is not None]
        temp = round(sum(temps) / len(temps), 2) if temps else None
        cal_k = 0.0
        # Punkte mit eigener Temperatur auf T_ref normieren (GATEWAY_API 7.1); k = 0 bis zur Messung (API-3)
        xs = [C.compensate_raw(r.c_probe, r.temp_c, cal_k) for r in recs]
        st = C.robust_mean(xs)
        with M.lock:
            if st["mean"] is None:
                run["state"] = "await_dry" if point == "dry" else "await_wet"
                run["message"] = "Keine gültigen Messwerte – Sensor prüfen"
            else:
                run[point] = {"raw": round(st["mean"]), "temp_c": temp, "n": st["n"],
                              "stddev": C.round1(st["stddev"]) if st["stddev"] is not None else None, "t": iso(now())}
                if run["dry"] and run["wet"]:
                    run["span_ok"] = C.span_ok(run["dry"]["raw"], run["wet"]["raw"])
                    run["state"] = "ready" if run["span_ok"] else "failed"
                    run["message"] = None if run["span_ok"] else "Trocken- und Nasswert zu ähnlich – Substrat wirklich nass?"
                else:
                    run["state"] = "await_wet" if point == "dry" else "await_dry"
            M.emit("calibration", _run_public(run))
            return {"run": _run_public(run), "outliers": st["outliers"]}
    M.job_update(j, state="waiting_for_sensor", message="Warte auf Sensor")
    M.central.submit(s["addr"], {"kind": "calibration_capture", "job": j, "samples": run["samples"],
                                 "purpose": 1 if point == "dry" else 2, "on_done": done})
    h.send_json(202, M.job_public(j))


@route("POST", "/calibration-runs/{run_id}/commit")
def run_commit(h, run_id, **_):
    M = h.M
    run = _run(M, run_id)
    if run["state"] != "ready":
        raise ApiError(409, "conflict", "Beide Messpunkte fehlen noch")
    if not run["span_ok"]:
        raise ApiError(422, "calibration_span", "Trocken- und Nasswert zu ähnlich")
    s = _sensor(M, run["sensor_id"])
    cal = M.make_cal(run["substrate"], "guided", run["dry"]["raw"], run["wet"]["raw"], now())
    cal["dry"], cal["wet"] = run["dry"], run["wet"]
    M.cal.setdefault(s["addr"], {})[run["substrate"]] = cal
    M.store.save_calibration(s["addr"], run["substrate"], cal)
    run["state"] = "committed"
    M.log("info", "calibrated", f"Kalibrierung {run['substrate']} gespeichert", s["id"])
    s["pending_config"] = True
    M.save_sensor(s)
    M.invalidate()
    if s.get("plant_id") in M.plants:
        e = M.journal_add(s["plant_id"], now(), "calibration", "system", note=f"Zwei-Punkt-Kalibrierung ({run['substrate']})")
        M.emit("plant", M.plant_out(M.plants[s["plant_id"]]))
    h.send_json(200, cal)


# ================================================================================ Jobs
@route("GET", "/jobs/{job_id}", auth="read")
def job_get(h, job_id, **_):
    j = h.M.jobs.get(job_id)
    if not j:
        raise ApiError(404, "not_found", "Auftrag nicht gefunden")
    h.send_json(200, h.M.job_public(j))


# ================================================================================ Kopplung (REQ-RF-05)
@route("GET", "/pairing", auth="session")
def pairing_get(h, **_):
    h.send_json(200, h.M.pairing_out())


@route("POST", "/pairing/start")
def pairing_start(h, body, **_):
    M = h.M
    dur = body.get("duration_s", 180) if isinstance(body, dict) else 180
    if not isinstance(dur, int) or not 30 <= dur <= 300:
        raise ApiError(400, "validation", "duration_s 30–300", "duration_s")
    M.pairing.update(active=True, until=now() + dur, candidates={})
    M.log("info", "pairing", "Kopplungsmodus geöffnet")
    if M.sim and M.central:  # Simulation: ein ungekoppelter Sensor geht in den Kopplungsmodus
        M.central.call(lambda: M.central.radio.sim_pairing_button())
    h.send_json(200, M.pairing_out())


@route("POST", "/pairing/stop")
def pairing_stop(h, **_):
    h.M.pairing.update(active=False, until=None, candidates={})
    h.send_json(200, h.M.pairing_out())


def _candidate(M, device):
    out = M.pairing_out()
    c = next((c for c in out["candidates"] if c["device"] == device), None)
    if not out["active"] or not c:
        raise ApiError(404, "not_found", "Sensor nicht (mehr) im Kopplungsmodus")
    return c


@route("POST", "/pairing/candidates/{device}/accept")
def pairing_accept(h, device, body, **_):
    M = h.M
    c = _candidate(M, device)
    if not body.get("plant_id") and not body.get("plant"):
        raise ApiError(400, "validation", "Pflanze angeben (bestehend oder neu)", "plant")
    if body.get("plant_id"):
        p = _plant(M, body["plant_id"])
        if p.get("sensor_id"):
            raise ApiError(409, "conflict", "Diese Pflanze hat schon einen Sensor")
    else:
        pl = body["plant"]
        if not str(pl.get("name", "")).strip():
            raise ApiError(400, "validation", "Name fehlt", "plant.name")
    other = M.sensors.get(device)
    if other and other["addr"] != c["address"]:
        raise ApiError(409, "conflict", f"Kennung {device} ist bereits an einen anderen Sensor vergeben")
    _need_radio(M)
    j = M.new_job("pair", device, body.get("plant_id"), timeout_s=150)
    M.central.pair(c["address"], j, {"plant_id": body.get("plant_id"), "plant": body.get("plant")})
    h.send_json(202, M.job_public(j))


@route("POST", "/pairing/candidates/{device}/confirm")
def pairing_confirm(h, device, body, **_):
    """Nutzer bestätigt, dass die Farbfolge am Sensor und in der App gleich ist (SAS, PROTOCOL 4.2)."""
    M = h.M
    if "match" not in body or not isinstance(body["match"], bool):
        raise ApiError(400, "validation", "match (true/false) fehlt", "match")
    addr = next((a for a, p in (M.central.pairs.items() if M.central else []) if P.sensor_name(a) == device), None)
    if not addr:
        raise ApiError(404, "not_found", "Keine laufende Kopplung für diesen Sensor")
    job = M.central.pairs[addr]["job"]
    if job["state"] != "awaiting_confirmation":
        raise ApiError(409, "conflict", "Farbfolge noch nicht bereit")
    M.central.confirm_pair(addr, body["match"])
    h.send_json(202, M.job_public(job))


# ================================================================================ Einstellungen
def _settings_out(M):
    o = json.loads(json.dumps(M.settings))
    o.pop("salt", None)
    o["storage_forecast_days"] = _forecast_days(M)
    return o


def _forecast_days(M):
    per_day = sum(M.per_day(sid) + 2 for sid in M.sensors) or 1
    free = sysinfo.disk(M.cfg.data_dir)["free"]
    return int(max(0, free - 200 * 2**20) / (120 * per_day))  # ≈ 120 B je Wert inkl. Index (gemessen grob, ANNAHME)


def _valid_hm(v):
    return isinstance(v, str) and re.fullmatch(r"([01][0-9]|2[0-3]):[0-5][0-9]", v)


@route("GET", "/settings", auth="read")
def settings_get(h, **_):
    h.send_json(200, _settings_out(h.M))


@route("PATCH", "/settings")
def settings_patch(h, body, **_):
    M = h.M
    if not isinstance(body, dict) or not body:
        raise ApiError(400, "validation", "Keine Änderungen")
    if "interval_per_day" in body and not (isinstance(body["interval_per_day"], int) and 1 <= body["interval_per_day"] <= 96):
        raise ApiError(400, "validation", "Intervall 1–96 pro Tag", "interval_per_day")
    if "reaction_time_min" in body and not (isinstance(body["reaction_time_min"], int) and 1 <= body["reaction_time_min"] <= 5):
        raise ApiError(400, "validation", "Reaktionszeit 1–5 min", "reaction_time_min")
    b = json.loads(json.dumps(body))
    tz = (b.get("time") or {}).get("timezone")
    if tz is not None:
        try:
            ZoneInfo(tz)
        except Exception:  # noqa: BLE001
            raise ApiError(400, "validation", "Unbekannte Zeitzone", "time.timezone")
    win = ((b.get("led") or {}).get("water_window") or {})
    for k in ("start", "end"):
        if k in win and not _valid_hm(win[k]):
            raise ApiError(400, "validation", "Zeit hh:mm", f"led.water_window.{k}")
    n = b.get("notifications") or {}
    if (n.get("email") or {}).get("enabled"):
        raise ApiError(409, "conflict", "E-Mail-Hinweise sind nicht vorgesehen (Entscheid D-020)")
    if (n.get("webpush") or {}).get("enabled") and not M.settings["notifications"]["webpush"]["allowed"]:
        raise ApiError(409, "conflict", "Web Push ist gesperrt: braucht Internet und Hersteller-Server (D-020, später als Option)")
    if (n.get("ntfy") or {}).get("enabled"):
        raise ApiError(409, "conflict", "ntfy ist für Rev A nicht vorgesehen (D-020: strikt lokal)")
    mqtt_pw = None
    if "mqtt" in b and "password" in b["mqtt"]:
        mqtt_pw = b["mqtt"].pop("password")
        M.settings["mqtt"]["password_set"] = bool(mqtt_pw)
        M.store.meta_set("mqtt_password", mqtt_pw or None)
    (b.get("notifications") or {}).get("email", {}).pop("password", None)
    old_dash = dict(M.settings["dashboard"])
    old_time = dict(M.settings["time"])
    from .model import _merge
    _merge(M.settings, b)
    M.save_settings()
    for s in M.sensors.values():
        s["pending_config"] = True
    M.invalidate()
    if M.settings["dashboard"] != old_dash and h.server_ctl:
        h.server_ctl.dashboard_changed()
    if M.settings["time"] != old_time and h.server_ctl:
        t = M.settings["time"]
        h.server_ctl.helper_request("ntp", {"enabled": bool(t["ntp_enabled"]), "server": str(t["ntp_server"])[:64]})
    if "mqtt" in b and M.mqtt:
        M.mqtt.configure(M.settings["mqtt"], M.store.meta_get("mqtt_password"))
    h.send_json(200, _settings_out(M))


@route("GET", "/settings/network", auth="session")
def network_get(h, **_):
    h.send_json(200, _network(h.M))


def _network(M):
    w = sysinfo.wifi(sim=M.sim)
    return {**w, "hostname": M.cfg.hostname, "mdns": True, "pending_change": M.store.meta_get("wifi_pending")}


@route("PUT", "/settings/network", elevated=True)
def network_put(h, body, **_):
    M = h.M
    ssid, psk = str(body.get("ssid", "")).strip(), body.get("password", body.get("psk", ""))
    if not 1 <= len(ssid) <= 32:
        raise ApiError(400, "validation", "SSID 1–32 Zeichen", "ssid")
    if psk and not 8 <= len(psk) <= 63:
        raise ApiError(400, "validation", "WLAN-Passwort 8–63 Zeichen", "password")
    pend = {"ssid": ssid, "deadline": iso(now() + 120)}
    M.store.meta_set("wifi_pending", pend)
    if h.server_ctl:
        h.server_ctl.helper_request("wifi", {"ssid": ssid, "psk": psk, "rollback_s": 120})
    M.log("info", "wifi_change", f"WLAN-Wechsel auf „{ssid}“ angefordert (Rückfall nach 120 s)")
    h.send_json(202, _network(M))


# ================================================================================ Firmware (REQ-FW-02/04)
def _fw_out(M):
    return {"gateway": {"platform": "mock" if M.sim else "rpi-zero2w", "version": VERSION, "build": "2026-11-07",
                        "update_slot": M.store.meta_get("release", "A"), "rollback_available": bool(M.store.meta_get("release_prev")),
                        "secure_boot": False, "storage_encryption": "off", "pwa_version": VERSION},
            "sensor_images": [{k: v for k, v in i.items() if not k.startswith("_")} for i in M.sensor_images],
            "rollout": M.rollout}


@route("GET", "/firmware", auth="session")
def fw_get(h, **_):
    h.send_json(200, _fw_out(h.M))


@route("POST", "/firmware/sensor-images", elevated=True)
def fw_upload(h, body, **_):
    M = h.M
    data = body if isinstance(body, (bytes, bytearray)) else b""
    if not data:
        raise ApiError(400, "bad_request", "Keine Datei erhalten")
    try:
        img = mcuboot.parse(bytes(data), h.server_ctl.fw_pubkey() if h.server_ctl else None)
    except mcuboot.ImageError as e:
        st = {"signature_invalid": 422, "too_large": 413, "downgrade": 409}.get(e.code, 400)
        M.log("warn", "fw_rejected", f"Sensor-Firmware abgelehnt: {e}")
        raise ApiError(st, e.code, str(e))
    if img.hw_rev is not None and img.hw_rev != 0x0A:
        raise ApiError(422, "signature_invalid", f"Abbild für andere Platinenrevision (0x{img.hw_rev:02X})")
    sec_max = M.store.meta_get("sec_cnt_max", 0)
    if img.security_counter < sec_max:
        raise ApiError(409, "downgrade", f"Sicherheitszähler {img.security_counter} < bereits verteilt {sec_max} (Anti-Rollback)")
    ver = "%d.%d.%d" % img.version
    if any(i["version"] == ver for i in M.sensor_images):
        raise ApiError(409, "conflict", f"Version {ver} ist bereits abgelegt")
    if len(M.sensor_images) >= 2:
        raise ApiError(409, "conflict", "Höchstens 2 Abbilder – bitte zuerst eines entfernen (ARCHITECTURE 7)")
    path = M.image_path(ver)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(data))
    doc = {"version": ver, "build": img.build, "security_counter": img.security_counter, "size": img.size,
           "sha256": img.file_sha256.hex(), "signature_ok": True,
           "hw_compat": "A-32 rev A" if img.hw_rev in (None, 0x0A) else f"0x{img.hw_rev:02X}", "uploaded": iso(now())}
    M.sensor_images.append(doc)
    M.store.save_image(doc)
    M.log("info", "fw_upload", f"Sensor-Firmware {ver} abgelegt (Signatur gültig)")
    h.send_json(201, doc)


@route("DELETE", "/firmware/sensor-images/{version}")
def fw_delete(h, version, **_):
    M = h.M
    if not any(i["version"] == version for i in M.sensor_images):
        raise ApiError(404, "not_found", "Version nicht vorhanden")
    if M.rollout and not M.rollout["finished"] and M.rollout["version"] == version:
        raise ApiError(409, "busy", "Abbild wird gerade verteilt")
    M.sensor_images = [i for i in M.sensor_images if i["version"] != version]
    M.store.delete_image(version)
    try:
        M.image_path(version).unlink()
    except OSError:
        pass
    h.send_json(204, None)


@route("POST", "/firmware/rollout", elevated=True)
def fw_rollout(h, body, **_):
    M = h.M
    ver = body.get("version")
    img = next((i for i in M.sensor_images if i["version"] == ver), None)
    if not img:
        raise ApiError(404, "not_found", "Version nicht vorhanden")
    if M.rollout and not M.rollout["finished"]:
        raise ApiError(409, "busy", "Es läuft bereits eine Verteilung")
    items = []
    for sid in body.get("sensor_ids", []):
        _sensor(M, sid)
        items.append({"sensor_id": sid, "state": "pending", "progress": 0.0, "message": "wartet auf den Sensor"})
    if not items:
        raise ApiError(400, "validation", "Keine Sensoren gewählt", "sensor_ids")
    M.rollout = {"version": ver, "started": iso(now()), "finished": None, "items": items}
    M.store.meta_set("sec_cnt_max", max(M.store.meta_get("sec_cnt_max", 0), img.get("security_counter", 0)))
    M.log("info", "fw_rollout", f"Verteilung {ver} an {len(items)} Sensor(en) gestartet")
    M.emit("rollout", M.rollout)
    h.send_json(202, M.rollout)


@route("DELETE", "/firmware/rollout")
def fw_rollout_cancel(h, **_):
    M = h.M
    if M.rollout and not M.rollout["finished"]:
        for it in M.rollout["items"]:
            if it["state"] not in ("done", "failed", "skipped", "rebooting"):
                it.update(state="skipped", message="abgebrochen")
        M.rollout["finished"] = iso(now())
        M.emit("rollout", M.rollout)
    h.send_json(204, None)


@route("POST", "/firmware/gateway", elevated=True)
def fw_gateway(h, body, **_):
    data = body if isinstance(body, (bytes, bytearray)) else b""
    if not data:
        raise ApiError(400, "bad_request", "Keine Datei erhalten")
    if not h.server_ctl:
        raise ApiError(409, "conflict", "Update nicht verfügbar")
    ver = h.server_ctl.gateway_update(bytes(data))  # prüft Signatur, packt aus, beauftragt den Helfer
    h.send_json(202, {"version": ver, "reboot_in_s": 10})


# ================================================================================ Daten
def _fmt(v, decimal):
    if v is None:
        return ""
    s = f"{v:.1f}" if isinstance(v, float) else str(v)
    return s.replace(".", ",") if decimal == "comma" else s


@route("GET", "/export.csv", auth="read")
def export_csv(h, q, **_):
    """fluidi-csv v1 (GATEWAY_API Kap. 9), gestreamt je Pflanze (kein Gesamtpuffer im RAM)."""
    M = h.M
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
        plants = [_plant(M, i) for i in ids.split(",")] if ids else sorted(M.plants.values(), key=lambda p: p["id"])
    except ValueError:
        raise ApiError(400, "validation", "plant_ids ungültig", "plant_ids")
    tzn = M.settings["time"]["timezone"]
    tz = ZoneInfo(tzn)
    name = f"fluidi-export-{datetime.now(tz).strftime('%Y%m%d-%H%M')}.csv"

    def q_(s):
        s = str(s)
        return '"' + s.replace('"', '""') + '"' if (sep in s or '"' in s or "\n" in s) else s

    def chunks():
        yield "﻿" + f"# fluidi-csv v1{sep} gateway={M.gw_name}{sep} erzeugt={iso(now())}{sep} zeitzone={tzn}{sep} aufloesung={res}\n"
        cols = (["pflanze_id", "pflanze", "sensor", "zeit_utc", "zeit_lokal", "feuchte_pct", "feuchte_zustand", "rohwert",
                 "temperatur_c", "quelle", "flags"] if res == "raw" else
                ["pflanze_id", "pflanze", "zeit_utc", "zeit_lokal", "feuchte_mittel_pct", "feuchte_min_pct", "feuchte_max_pct",
                 "temperatur_mittel_c"])
        yield sep.join(cols) + "\n"
        for p in plants:
            with M.lock:
                rows = M.plant_records(p["id"], t0, t1)
                ev = [(sid, r, M.evaluate(r, p)) for sid, r in rows]
            buf = io.StringIO()
            if res == "raw":
                for sid, r, e in ev:
                    lt = datetime.fromtimestamp(r["t"], tz).strftime("%Y-%m-%d %H:%M:%S")
                    buf.write(sep.join([str(p["id"]), q_(p["name"]), sid, iso(r["t"]), lt, _fmt(e["moisture_pct"], dec),
                                        e["moisture_state"], "" if r["raw"] is None else str(r["raw"]),
                                        _fmt(None if r["temp"] is None else float(r["temp"]), dec), r["source"], str(r["flags"])]) + "\n")
            else:
                a = C.aggregate([(r["t"], e["moisture_pct"], r["temp"]) for _s, r, e in ev], res, tzn)
                for i, t in enumerate(a["t"]):
                    lt = datetime.fromtimestamp(t, tz).strftime("%Y-%m-%d %H:%M:%S")
                    buf.write(sep.join([str(p["id"]), q_(p["name"]), iso(t), lt, _fmt(a["moisture"][i], dec),
                                        _fmt(a["moisture_min"][i], dec), _fmt(a["moisture_max"][i], dec), _fmt(a["temp_c"][i], dec)]) + "\n")
            yield buf.getvalue()
    h.send_stream(200, (c.encode("utf-8") for c in chunks()), "text/csv; charset=utf-8",
                  {"Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store"})


@route("POST", "/backup", elevated=True)
def backup(h, body, **_):
    M = h.M
    pp = body.get("passphrase", "")
    if not isinstance(pp, str) or len(pp) < 12:
        raise ApiError(400, "validation", "Passphrase: mindestens 12 Zeichen", "passphrase")
    data = BK.create(M, pp)
    name = f"fluidi-backup-{M.gw_name}-{datetime.now().strftime('%Y%m%d')}.fbk"
    M.log("info", "backup", "Backup erstellt")
    h.send_bytes(200, data, "application/octet-stream", {"Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store"})


@route("POST", "/backup/restore", elevated=True)
def restore(h, body, q, **_):
    M = h.M
    data = body if isinstance(body, (bytes, bytearray)) else b""
    pp = h.headers.get("X-Backup-Passphrase") or ""
    if len(pp) < 12:
        raise ApiError(400, "validation", "Passphrase fehlt", "X-Backup-Passphrase")
    dry = q.get("dry_run", "false") == "true"
    try:
        summary = BK.restore(M, bytes(data), pp, dry_run=dry)
    except BK.BackupError as e:
        raise ApiError(422, "bad_request", str(e))
    if not dry and h.server_ctl:
        h.server_ctl.restart_later(3)
    h.send_json(202, {"ok": True, "dry_run": dry, **summary, "reboot_in_s": None if dry else 3})


# ================================================================================ Profile, Tagebuch, Prognose, Raum, Statistik
@route("GET", "/species", auth="read")
def species_get(h, **_):
    h.send_json(200, h.M.species())


def journal_for(M, pid):
    a = M.analysis(pid)
    out, merged = [], {}
    for e in a["events"]:
        if e["button_t"] is not None:
            merged[e["button_t"]] = e
    for e in M.journal.values():
        if e["plant_id"] != pid:
            continue
        o = {**e, "t": iso(e["t"]), "delta_pct": None, "before_pct": None, "after_pct": None, "sensor_confirmed": False,
             "uncertain_time": False}
        if e["type"] == "watering" and e["t"] in merged:
            ev = merged[e["t"]]
            o.update(delta_pct=C.round1(ev["delta"]), before_pct=C.round1(ev["before"]), after_pct=C.round1(ev["peak"]),
                     sensor_confirmed=True)
        out.append(o)
    for ev in a["events"]:
        if ev["button_t"] is not None:
            continue
        st = M.journal_status.get((pid, int(ev["t"])), "unconfirmed")
        out.append({"id": f"s{pid}-{int(ev['t'])}", "plant_id": pid, "t": iso(ev["t"]), "type": "watering", "source": "sensor",
                    "status": st, "note": "", "amount_ml": None, "delta_pct": C.round1(ev["delta"]),
                    "before_pct": C.round1(ev["before"]), "after_pct": C.round1(ev["peak"]), "sensor_confirmed": True,
                    "uncertain_time": ev["uncertain_time"]})
    for asg in M.assign:
        if asg["plant"] == pid:
            out.append({"id": f"x{pid}-{int(asg['from'])}", "plant_id": pid, "t": iso(asg["from"]), "type": "sensor_change",
                        "source": "system", "status": "confirmed", "note": f"Sensor {M.by_addr.get(asg['sensor'], asg['sensor'])} zugeordnet",
                        "amount_ml": None, "delta_pct": None, "before_pct": None, "after_pct": None, "sensor_confirmed": False,
                        "uncertain_time": False})
    out.sort(key=lambda x: x["t"], reverse=True)
    return out


@route("GET", "/plants/{plant_id}/journal", auth="read")
def journal_get(h, plant_id, q, **_):
    p = _plant(h.M, plant_id)
    limit = _int(q, "limit", 100, 1, 1000)
    items = journal_for(h.M, p["id"])
    if q.get("include_rejected") != "true":
        items = [e for e in items if e["status"] != "rejected"]
    h.send_json(200, items[:limit])


@route("POST", "/plants/{plant_id}/journal")
def journal_post(h, plant_id, body, **_):
    M = h.M
    p = _plant(M, plant_id)
    t = now()
    if body.get("t"):
        try:
            t = datetime.fromisoformat(str(body["t"]).replace("Z", "+00:00")).timestamp()
        except ValueError:
            raise ApiError(400, "validation", "Zeitpunkt ungültig", "t")
        if t > now() + 300:
            raise ApiError(400, "validation", "Zeitpunkt liegt in der Zukunft", "t")
    typ = body.get("type", "watering")
    if typ not in ("watering", "fertilizing", "repotting", "note"):
        raise ApiError(400, "validation", "Typ unbekannt", "type")
    am = body.get("amount_ml")
    if am is not None and not (isinstance(am, int) and 0 < am <= 20000):
        raise ApiError(400, "validation", "Menge 1–20000 ml", "amount_ml")
    e = M.journal_add(p["id"], t, typ, "button" if typ == "watering" else "manual", note=str(body.get("note", ""))[:200], amount_ml=am)
    sid = p.get("sensor_id")
    if typ == "watering" and sid and not body.get("t") and M.central:
        # Konzept 7.3: Gateway fordert eine Messung an; der Feuchtesprung bestätigt den Eintrag
        s = M.sensors[sid]
        if M.sim:
            M.central.call(lambda: M.central.radio.sim_water(s["addr"]))
        M.central.submit(s["addr"], {"kind": "measure"})
    M.invalidate(p["id"])
    out = next(x for x in journal_for(M, p["id"]) if x["id"] == e["id"])
    M.emit("journal", {"plant_id": p["id"]})
    M.emit("plant", M.plant_out(p))
    h.send_json(201, out)


def _journal_entry(M, entry_id):
    if entry_id in M.journal:
        return M.journal[entry_id], False
    m = re.fullmatch(r"s(\d+)-(\d+)", entry_id)
    if m and int(m.group(1)) in M.plants:
        pid, t = int(m.group(1)), int(m.group(2))
        if any(int(e["t"]) == t for e in M.analysis(pid)["events"]):
            return {"plant_id": pid, "t": t}, True
    raise ApiError(404, "not_found", "Eintrag nicht gefunden")


@route("PATCH", "/journal/{entry_id}")
def journal_patch(h, entry_id, body, **_):
    M = h.M
    e, derived = _journal_entry(M, entry_id)
    st = body.get("status")
    if st is not None and st not in ("confirmed", "unconfirmed", "rejected"):
        raise ApiError(400, "validation", "Status unbekannt", "status")
    if derived:
        if st:
            M.journal_status[(e["plant_id"], e["t"])] = st
            M.store.set_journal_status(e["plant_id"], e["t"], st)
    else:
        for k in ("note", "amount_ml", "status"):
            if k in body:
                e[k] = body[k]
        M.store.save_journal(e)
    M.invalidate(e["plant_id"])
    out = next((x for x in journal_for(M, e["plant_id"]) if x["id"] == entry_id), None)
    if out is None:
        out = {"id": entry_id, "plant_id": e["plant_id"], "t": iso(e["t"]), "type": "watering", "source": "sensor",
               "status": st or "rejected", "note": "", "amount_ml": None, "delta_pct": None, "before_pct": None,
               "after_pct": None, "sensor_confirmed": True, "uncertain_time": False}
    M.emit("journal", {"plant_id": e["plant_id"]})
    h.send_json(200, out)


@route("DELETE", "/journal/{entry_id}")
def journal_delete(h, entry_id, **_):
    M = h.M
    e, derived = _journal_entry(M, entry_id)
    if derived:
        raise ApiError(409, "conflict", "Vom Sensor erkannte Giessung: bitte verwerfen statt löschen")
    M.journal.pop(entry_id)
    M.store.delete_journal(entry_id)
    M.invalidate(e["plant_id"])
    M.emit("journal", {"plant_id": e["plant_id"]})
    h.send_json(204, None)


@route("GET", "/plants/{plant_id}/forecast", auth="read")
def forecast_get(h, plant_id, **_):
    M = h.M
    p = _plant(M, plant_id)
    a = M.analysis(p["id"])
    fc = dict(a["forecast"])
    fc["next_water"] = iso(fc["next_water"])
    fc["plant_id"], fc["threshold_pct"], fc["curve"] = p["id"], p["threshold_pct"], None
    if a["forecast"]["state"] == "ok" and a["points"]:
        t_last, m_last = a["points"][-1]
        fc["curve"] = AN.forecast_curve(t_last, m_last, a["forecast"], p["threshold_pct"])
    hist = []
    for c in AN.cycles(a["points"], a["events_ok"])[-8:]:
        f = AN.fit_drying(c["points"])
        if f:
            hist.append({"start": iso(c["start"]), "k_per_day": round(f["k"], 4), "r2": round(f["r2"], 3), "current": c["current"]})
    fc["cycles"] = hist
    h.send_json(200, fc)


def _room_check(M, plan):
    if not isinstance(plan.get("rooms"), list) or not plan["rooms"]:
        raise ApiError(400, "validation", "Mindestens ein Raum", "rooms")
    if len(plan["rooms"]) > 1:
        raise ApiError(400, "validation", "Rev A: ein Raum (D-020)", "rooms")
    for room in plan["rooms"]:
        if not (100 <= room.get("width_cm", 0) <= 5000 and 100 <= room.get("depth_cm", 0) <= 5000):
            raise ApiError(400, "validation", "Raummasse 1–50 m", "rooms")
        seen = set()
        for pp in room.get("plants", []):
            if pp["plant_id"] not in M.plants:
                raise ApiError(400, "validation", f"Pflanze {pp['plant_id']} gibt es nicht", "plants")
            if pp["plant_id"] in seen:
                raise ApiError(400, "validation", "Pflanze doppelt platziert", "plants")
            seen.add(pp["plant_id"])
            if not (0 <= pp["x_cm"] <= room["width_cm"] and 0 <= pp["y_cm"] <= room["depth_cm"]):
                raise ApiError(400, "validation", "Pflanze liegt ausserhalb des Raums", "plants")
        for o in room.get("openings", []):
            wall_len = room["width_cm"] if o["wall"] in ("n", "s") else room["depth_cm"]
            if o["offset_cm"] < 0 or o["offset_cm"] + o["length_cm"] > wall_len:
                raise ApiError(400, "validation", "Fenster/Tür ragt über die Wand hinaus", "openings")


@route("GET", "/roomplan", auth="read")
def roomplan_get(h, **_):
    h.send_json(200, h.M.roomplan)


@route("PUT", "/roomplan")
def roomplan_put(h, body, **_):
    M = h.M
    if body.get("version") != M.roomplan["version"]:
        raise ApiError(409, "conflict", "Der Raumplan wurde inzwischen geändert – bitte neu laden")
    try:
        _room_check(M, body)
    except (KeyError, TypeError):
        raise ApiError(400, "validation", "Raumplan unvollständig", "rooms")
    plan = json.loads(json.dumps(body))
    plan["version"] = M.roomplan["version"] + 1
    plan["updated"] = iso(now())
    M.roomplan = plan
    M.store.meta_set("roomplan", plan)
    h.send_json(200, plan)


def _energy(M, s):
    """Schätzung je Sensor (PROTOCOL Kap. 12, Mittelwerte 'real'); Schlafstrom ANNAHME 2.0 µA (energy_budget.py)."""
    per_day = M.per_day(s["id"]) + 2
    p = M.plants.get(s.get("plant_id")) if s.get("plant_id") else None
    need = bool(p and M.plant_out(p)["status"]["needs_water"])
    adv = 86400 / (P.adv_interval_ms(M.settings["reaction_time_min"], M.cfg.p_miss) / 1000) * 0.0162
    mc = {"sleep": round(2.0 * 86.4, 1), "advertising": round(adv, 1), "sessions": round(per_day * 0.299, 2),
          "measure": round(per_day * 0.03, 2), "led": 11.5 if need and s.get("led_enabled", True) else 0.7}
    total = sum(mc.values())
    return {"model": "Ereigniszählung × Ladung je Ereignis (PROTOCOL Kap. 12), Schätzung", "mc_per_day": mc,
            "total_mc_per_day": round(total, 1), "avg_ua": round(total / 86.4, 2), "mah_per_year": round(total * 365 / 3600, 1),
            "cell": "CR2032", "capacity_mah": 225}


def _battery_hist(M, s):
    rows = M.store.q("SELECT (t/604800)*604800 AS w, AVG(vbat) AS v FROM reading WHERE sensor=? AND vbat IS NOT NULL "
                     "AND t>=? GROUP BY w ORDER BY w", (s["addr"], int(now() - 365 * 86400)))
    return {"t": [int(r["w"]) for r in rows], "mv": [int(r["v"]) for r in rows]}


@route("GET", "/stats", auth="read")
def stats_get(h, q, **_):
    M = h.M
    days = _int(q, "days", 90, 7, 730)
    t1 = now()
    t0 = t1 - days * 86400
    tz = M.tz()
    lt = datetime.fromtimestamp(t1, tz)
    monday = datetime(lt.year, lt.month, lt.day, tzinfo=tz).timestamp() - lt.weekday() * 86400
    weeks = [monday - i * 7 * 86400 for i in range(11, -1, -1)]
    counts = [0] * 12
    plants, total_w = [], 0
    for p in sorted(M.plants.values(), key=lambda x: x["id"]):
        a = M.analysis(p["id"])
        ws = sorted(e["t"] for e in a["events_ok"])
        for w in ws:
            for i, w0 in enumerate(weeks):
                if w0 <= w < w0 + 7 * 86400:
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
    for s in sorted(M.sensors.values(), key=lambda x: x["id"]):
        sensors.append({"sensor_id": s["id"], "plant_id": s.get("plant_id"), "battery": M.battery_out(s) or {"mv": 0, "pct": 0, "days_left": None, "state": "ok"},
                        "battery_history": _battery_hist(M, s), "energy": _energy(M, s),
                        "radio": {"rssi_dbm": s.get("rssi"), "quality": C.signal_quality(s.get("rssi")) if s.get("rssi") is not None else 0,
                                  "sessions_per_day": M.per_day(s["id"]) + 2, "missed_pct": M.missed_pct(s["id"]) or 0.0},
                        "last_seen": iso(s.get("last_seen")), "fw_version": s.get("fw_version", "?")})
    inr = [p["time_in_range_pct"] for p in plants if p["time_in_range_pct"] is not None]
    allint = [p["avg_interval_days"] for p in plants if p["avg_interval_days"]]
    cnt = M.store.count_readings()
    h.send_json(200, {
        "days": days, "generated": iso(t1),
        "summary": {"waterings": total_w, "avg_interval_days": round(sum(allint) / len(allint), 1) if allint else None,
                    "time_in_range_pct": round(sum(inr) / len(inr), 1) if inr else None,
                    "sensors_online": sum(1 for sid in M.sensors if M.reachable(sid)), "sensors": len(M.sensors),
                    "readings": cnt["n"]},
        "waterings_per_week": [{"week_start": iso(w), "count": c} for w, c in zip(weeks, counts)],
        "plants": plants, "sensors": sensors,
        "gateway": {"uptime_s": int(t1 - M.boot), "storage_used_bytes": M.store.size_bytes(), "platform": "mock" if M.sim else "rpi-zero2w"},
    })


@route("GET", "/alerts", auth="read")
def alerts_get(h, **_):
    h.send_json(200, h.M.alerts())


def dashboard_data(M):
    d = M.settings["dashboard"]
    plants = []
    for p in sorted(M.plants.values(), key=lambda x: x["name"].lower()):
        po = M.plant_out(p)
        L = po["latest"]
        plants.append({"id": p["id"], "name": p["name"] if d["show_names"] else f"Pflanze {p['id']}",
                       "species": p.get("species"), "mood": po["mood"],
                       "state": "stale" if po["status"]["stale"] else (L["moisture_state"] if L else "none"),
                       "moisture_pct": L["moisture_pct"] if L else None, "threshold_pct": p["threshold_pct"],
                       "upper_pct": p.get("upper_pct"), "needs_water": po["status"]["needs_water"],
                       "forecast_days": po["forecast"]["days"], "next_water": po["forecast"]["next_water"]})
    al = M.alerts()
    room = json.loads(json.dumps(M.roomplan))
    if not d["show_names"]:
        pass  # Namen stehen nur in plants[], nicht im Raumplan
    return {"generated": iso(now()), "title": d["title"], "public": d["public"],
            "summary": {"plants": len(plants), "needs_water": sum(p["needs_water"] for p in plants),
                        "warnings": sum(1 for a in al if a["level"] != "info" and a["kind"] != "needs_water")},
            "plants": plants, "roomplan": room, "climate": M.climate.latest() if M.climate else None}


@route("GET", "/dashboard", auth="public")
def dashboard_get(h, sess, **_):
    M = h.M
    d = M.settings["dashboard"]
    if not d["enabled"]:
        raise ApiError(404, "not_found", "Dashboard ist ausgeschaltet")
    if not d["public"] and not sess and not M.settings["public_read"]:
        raise ApiError(401, "auth_required", "Bitte anmelden")
    h.send_json(200, dashboard_data(M))


# ================================================================================ Raumklima (D-017)
@route("GET", "/climate", auth="read")
def climate_get(h, q, **_):
    M = h.M
    t1 = _int(q, "to", int(now()))
    t0 = _int(q, "from", t1 - 7 * 86400)
    if t1 <= t0 or t1 - t0 > 3 * 366 * 86400:
        raise ApiError(400, "validation", "Zeitbereich ungültig", "from")
    cl = M.climate
    rows = [dict(r) for r in M.store.climate(t0, t1)]
    if cl:  # noch nicht gesicherte Werte aus dem RAM (Schreibbündelung, climate.py)
        rows += [{"t": t, "temp": tc, "rh": rh} for t, tc, rh in list(cl.buf) if t0 <= t <= t1]
    out = {"source": cl.source if cl else "off", "latest": cl.latest() if cl else None, "from": t0, "to": t1,
           "t": [], "temp_c": [], "rh_pct": []}
    step = 3600 if t1 - t0 > 3 * 86400 else 0
    if step:
        b = {}
        for r in rows:
            k = r["t"] - r["t"] % step
            b.setdefault(k, []).append(r)
        for k in sorted(b):
            rs = b[k]
            out["t"].append(k)
            out["temp_c"].append(round(sum(x["temp"] for x in rs) / len(rs), 2))
            out["rh_pct"].append(round(sum(x["rh"] for x in rs) / len(rs), 1))
    else:
        for r in rows:
            out["t"].append(r["t"])
            out["temp_c"].append(r["temp"])
            out["rh_pct"].append(r["rh"])
    h.send_json(200, out)


# ================================================================================ System
def _cert(h):
    return h.server_ctl.cert_info() if h.server_ctl else None


@route("GET", "/system", auth="read")
def system_get(h, **_):
    M = h.M
    cnt = M.store.count_readings()
    online = sum(1 for sid in M.sensors if M.reachable(sid))
    d = sysinfo.disk(M.cfg.data_dir)
    cert = _cert(h) or {"not_after": iso(now()), "days_left": 0, "fingerprint_sha256": ""}
    h.send_json(200, {
        "gateway_id": M.gw_name, "version": VERSION, "uptime_s": int(now() - M.boot),
        "reset_reason": M.store.meta_get("last_stop", "power_on"),
        "time": M.time.status(M.settings["time"]["timezone"]),
        "storage": {"used_bytes": M.store.size_bytes(), "total_bytes": d["total"], "free_bytes": d["free"],
                    "records": cnt["n"], "oldest": iso(cnt["t0"]), "forecast_days": _forecast_days(M),
                    "db_transactions": M.store.writes, "sd_written_bytes": sysinfo.diskstats_written_bytes()},
        "network": _network(M), "certificate": cert,
        "sensors": {"paired": len(M.sensors), "online": online},
        "heap": {"internal_free": sysinfo.mem_free() or 0, "psram_free": 0},
        "radio": {"backend": M.central.radio.name if M.central else "off", **(M.central.stats if M.central else {})},
        "crypto_backend": __import__("fluidi_gw.crypto", fromlist=["BACKEND"]).BACKEND,
        "cpu_temp_c": sysinfo.cpu_temp(), "climate": M.climate.latest() if M.climate else None,
    })


@route("POST", "/system/time")
def system_time(h, body, sess, **_):
    M = h.M
    force = bool(body.get("force"))
    if force and (sess.get("elevated_until") or 0) < now():
        raise ApiError(403, "elevation_required", "Bitte Passwort erneut bestätigen")
    t = body.get("t") or body.get("now")
    if t:
        try:
            ts = datetime.fromisoformat(str(t).replace("Z", "+00:00")).timestamp()
        except ValueError:
            raise ApiError(400, "validation", "Zeit ungültig", "t")
        if not M.time.set_browser_time(ts, force=force) and force:
            raise ApiError(409, "conflict", "Zeit nicht übernommen")
    h.send_json(200, M.time.status(M.settings["time"]["timezone"]))


@route("POST", "/system/reboot")
def system_reboot(h, **_):
    h.M.log("info", "reboot", "Neustart angefordert")
    if h.server_ctl:
        h.server_ctl.helper_request("reboot", {})
    h.send_json(202, None)


@route("GET", "/system/events", auth="session")
def system_events(h, q, **_):
    limit = _int(q, "limit", 50, 1, 200)
    before = _int(q, "before", 2**62)
    h.send_json(200, [{"id": r["id"], "t": iso(r["t"]), "level": r["level"], "code": r["code"], "text": r["text"],
                       "sensor_id": r["sensor"]} for r in h.M.store.events(limit, before)])


@route("GET", "/stream", auth="read")
def stream(h, **_):
    h.sse()
