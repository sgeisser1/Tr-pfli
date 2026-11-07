"""API-Konformität des Mock-Servers gegen app/api/openapi.yaml.

Startet den Mock in einem Thread auf einem freien Port, ruft die Endpunkte auf und prüft
Statuscodes, Sicherheitsregeln und Antwortschemas (jsonschema, Draft 2020-12).
Ohne PyYAML/jsonschema werden die Schemaprüfungen übersprungen, die übrigen Tests laufen.

Start: python3 -m unittest discover -s app/tests -p 'test_*.py'
"""
import http.cookiejar
import json
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "dev"))
import mock_server as M  # noqa: E402

try:
    import yaml  # type: ignore
    import jsonschema  # type: ignore
    SPEC = yaml.safe_load((HERE.parent / "api" / "openapi.yaml").read_text(encoding="utf-8"))
except Exception:  # pragma: no cover
    SPEC = None

PASSWORD = "test-passwort-123"


class Client:
    def __init__(self, base):
        self.base = base
        self.jar = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar))
        self.csrf = None

    def req(self, method, path, body=None, headers=None, raw=None, csrf=True):
        h = dict(headers or {})
        data = None
        if raw is not None:
            data, h["Content-Type"] = raw, "application/octet-stream"
        elif body is not None:
            data, h["Content-Type"] = json.dumps(body).encode(), "application/json"
        if csrf and self.csrf and method != "GET":
            h["X-CSRF-Token"] = self.csrf
        r = urllib.request.Request(self.base + path, data=data, method=method, headers=h)
        try:
            with self.op.open(r, timeout=10) as res:
                return res.status, dict(res.headers), res.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def json(self, method, path, body=None, **kw):
        st, hd, data = self.req(method, path, body, **kw)
        return st, (json.loads(data) if data and "json" in hd.get("Content-Type", "") else data)

    def login(self, pw=PASSWORD):
        st, js = self.json("POST", "/api/v1/auth/login", {"password": pw})
        if st == 200:
            self.csrf = js["csrf"]
        return st, js


class MockApiTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = M.make_server("127.0.0.1", 0, seed=7, password=PASSWORD, quiet=True)
        cls.port = cls.srv.server_address[1]
        cls.th = threading.Thread(target=cls.srv.serve_forever, daemon=True)
        cls.th.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()

    def setUp(self):
        M.Handler.S.fails.clear()
        M.Handler.S.global_fails.clear()

    # ---------------------------------------------------------------- Schema
    def check(self, path_tpl, method, status, obj):
        if SPEC is None:
            return
        op = SPEC["paths"][path_tpl][method.lower()]
        resp = op["responses"][str(status)]
        if "$ref" in resp:
            resp = SPEC["components"]["responses"][resp["$ref"].split("/")[-1]]
        sch = resp["content"]["application/json"]["schema"]
        full = {"$schema": "https://json-schema.org/draft/2020-12/schema", "components": SPEC["components"], **sch}
        jsonschema.Draft202012Validator(full, format_checker=jsonschema.FormatChecker()).validate(obj)

    def wait_job(self, c, job, timeout=20):
        t0 = time.time()
        while time.time() - t0 < timeout:
            st, j = c.json("GET", f"/api/v1/jobs/{job['id']}")
            self.assertEqual(st, 200)
            self.check("/jobs/{job_id}", "get", 200, j)
            if j["state"] in ("done", "failed", "timeout", "cancelled"):
                return j
            time.sleep(0.3)
        self.fail("Job nicht fertig")

    # ---------------------------------------------------------------- Tests
    def test_static_and_headers(self):
        c = Client(self.base)
        st, hd, body = c.req("GET", "/")
        self.assertEqual(st, 200)
        self.assertIn("default-src 'self'", hd["Content-Security-Policy"])
        self.assertEqual(hd["X-Content-Type-Options"], "nosniff")
        st, hd, _ = c.req("GET", "/manifest.webmanifest")
        self.assertTrue(hd["Content-Type"].startswith("application/manifest+json"))
        for bad in ("/dev/mock_server.py", "/tests/test_calc.py", "/../CLAUDE.md", "/api/openapi.yaml"):
            self.assertEqual(c.req("GET", bad)[0], 404, bad)

    def test_read_public_and_schemas(self):
        c = Client(self.base)
        st, a = c.json("GET", "/api/v1/auth/status")
        self.check("/auth/status", "get", 200, a)
        self.assertFalse(a["logged_in"])
        st, plants = c.json("GET", "/api/v1/plants")
        self.assertEqual(st, 200)
        self.check("/plants", "get", 200, plants)
        states = {p["latest"]["moisture_state"] for p in plants if p["latest"]}
        self.assertTrue({"ok", "dry", "air"} <= states, states)
        self.assertTrue(any(p["status"]["stale"] for p in plants))
        self.assertTrue(any(p["status"]["battery_low"] for p in plants))
        st, s = c.json("GET", "/api/v1/sensors")
        self.check("/sensors", "get", 200, s)
        st, cal = c.json("GET", f"/api/v1/sensors/{s[0]['id']}/calibration")
        self.check("/sensors/{sensor_id}/calibration", "get", 200, cal)
        st, sys_ = c.json("GET", "/api/v1/system")
        self.check("/system", "get", 200, sys_)
        st, se = c.json("GET", "/api/v1/settings")
        self.check("/settings", "get", 200, se)
        self.assertEqual(se["interval_per_day"], 6)  # REQ-SYS-04 Werkseinstellung

    def test_series_resolutions(self):
        c = Client(self.base)
        now = int(time.time())
        for span, res in ((86400, "raw"), (7 * 86400, "raw"), (30 * 86400, "raw"), (365 * 86400, "day")):
            st, s = c.json("GET", f"/api/v1/plants/1/series?from={now - span}&to={now}&res=auto")
            self.assertEqual(st, 200)
            self.check("/plants/{plant_id}/series", "get", 200, s)
            self.assertEqual(s["res"], res, span)
            self.assertEqual(len(s["t"]), len(s["moisture"]))
            self.assertEqual(s["t"], sorted(s["t"]))
        st, s = c.json("GET", f"/api/v1/plants/1/series?from={now - 30 * 86400}&to={now}&res=hour")
        self.assertEqual(s["res"], "hour")
        self.assertTrue(all(lo is None or lo <= m <= hi for lo, m, hi in zip(s["moisture_min"], s["moisture"], s["moisture_max"]) if m is not None))
        self.assertEqual(c.json("GET", f"/api/v1/plants/1/series?from={now}&to={now - 10}")[0], 400)
        self.assertEqual(c.json("GET", "/api/v1/plants/999/series?from=0&to=10")[0], 404)

    def test_writes_need_login_and_csrf(self):
        c = Client(self.base)
        st, e = c.json("PATCH", "/api/v1/plants/1", {"name": "X"})
        self.assertEqual(st, 401)
        self.assertEqual(e["error"]["code"], "auth_required")
        self.assertEqual(c.login()[0], 200)
        st, e = c.json("PATCH", "/api/v1/plants/1", {"name": "X"}, csrf=False)
        self.assertEqual((st, e["error"]["code"]), (403, "csrf"))
        st, e = c.json("PATCH", "/api/v1/plants/1", {"name": "X"}, headers={"Origin": "http://evil.example"})
        self.assertEqual(st, 403)
        st, p = c.json("PATCH", "/api/v1/plants/1", {"name": "Monstera deliciosa", "threshold_pct": 33})
        self.assertEqual(st, 200)
        self.check("/plants/{plant_id}", "patch", 200, p)
        self.assertEqual(p["threshold_pct"], 33)
        # Validierung
        st, e = c.json("PATCH", "/api/v1/plants/1", {"threshold_pct": 140})
        self.assertEqual((st, e["error"]["code"]), (400, "validation"))
        st, e = c.json("PATCH", "/api/v1/settings", {"interval_per_day": 97})
        self.assertEqual(st, 400)

    def test_elevation_for_sensitive(self):
        c = Client(self.base)
        c.login()
        for tok, s in M.Handler.S.sessions.items():
            if s["csrf"] == c.csrf:
                s["elevated_until"] = 0
        st, e = c.json("POST", "/api/v1/backup", {"passphrase": "x" * 12})
        self.assertEqual((st, e["error"]["code"]), (403, "elevation_required"))
        st, s = c.json("POST", "/api/v1/auth/elevate", {"password": PASSWORD})
        self.assertEqual(st, 200)
        self.check("/auth/elevate", "post", 200, s)
        st, hd, data = c.req("POST", "/api/v1/backup", {"passphrase": "x" * 12})
        self.assertEqual(st, 200)
        self.assertIn(".fbk", hd["Content-Disposition"])
        st, r = c.json("POST", "/api/v1/backup/restore?dry_run=true", raw=data, headers={"X-Backup-Passphrase": "x" * 12})
        self.assertEqual(st, 202)
        self.check("/backup/restore", "post", 202, r)
        self.assertTrue(r["dry_run"])

    def test_login_lockout(self):
        c = Client(self.base)
        for i in range(M.LOCK_AFTER):
            st, e = c.login("falsch")
            self.assertEqual(st, 401)
        st, e = c.login(PASSWORD)  # auch richtiges Passwort wird während der Sperre abgewiesen
        self.assertEqual(st, 429)
        self.assertEqual(e["error"]["code"], "locked")
        self.assertGreater(e["error"]["retry_after_s"], 0)
        st, a = c.json("GET", "/api/v1/auth/status")
        self.assertTrue(a["lockout"]["locked"])

    def test_manual_measure_job(self):
        c = Client(self.base)
        c.login()
        st, j = c.json("POST", "/api/v1/plants/2/measure")
        self.assertEqual(st, 202)
        self.check("/plants/{plant_id}/measure", "post", 202, j)
        fin = self.wait_job(c, j)
        self.assertEqual(fin["state"], "done")
        self.assertIn("reading", fin["result"])
        # Pflanze ohne Sensor
        st, e = c.json("POST", "/api/v1/plants/8/measure")
        self.assertEqual(st, 409)
        # nicht erreichbarer Sensor -> timeout
        st, j = c.json("POST", "/api/v1/plants/7/measure")
        self.assertEqual(self.wait_job(c, j)["state"], "timeout")

    def test_calibration_run(self):
        c = Client(self.base)
        c.login()
        st, run = c.json("POST", "/api/v1/sensors/fluidi-1A2B/calibration-runs", {"substrate": "erde", "samples": 5})
        self.assertEqual(st, 201)
        self.check("/sensors/{sensor_id}/calibration-runs", "post", 201, run)
        self.assertEqual(c.json("POST", f"/api/v1/calibration-runs/{run['id']}/commit")[0], 409)
        for point in ("dry", "wet"):
            st, j = c.json("POST", f"/api/v1/calibration-runs/{run['id']}/capture", {"point": point})
            self.assertEqual(st, 202)
            self.assertEqual(self.wait_job(c, j)["state"], "done")
        st, run = c.json("GET", f"/api/v1/calibration-runs/{run['id']}")
        self.check("/calibration-runs/{run_id}", "get", 200, run)
        self.assertEqual(run["state"], "ready")
        self.assertEqual(run["dry"]["n"], 4)  # 1 Ausreisser verworfen (REQ-MES-10)
        st, cal = c.json("POST", f"/api/v1/calibration-runs/{run['id']}/commit")
        self.assertEqual(st, 200)
        self.check("/calibration-runs/{run_id}/commit", "post", 200, cal)
        self.assertEqual(cal["source"], "guided")
        st, e = c.json("PUT", "/api/v1/sensors/fluidi-1A2B/calibration/erde", {"dry_raw": 30000, "wet_raw": 30100})
        self.assertEqual((st, e["error"]["code"]), (400, "calibration_span"))

    def test_pairing_flow(self):
        c = Client(self.base)
        c.login()
        st, p = c.json("POST", "/api/v1/pairing/start", {"duration_s": 60})
        self.check("/pairing/start", "post", 200, p)
        self.assertTrue(p["active"])
        for _ in range(30):
            st, p = c.json("GET", "/api/v1/pairing")
            if p["candidates"]:
                break
            time.sleep(0.3)
        self.check("/pairing", "get", 200, p)
        dev = p["candidates"][0]["device"]
        st, j = c.json("POST", f"/api/v1/pairing/candidates/{dev}/accept", {"plant": {"name": "Testpflanze", "substrate": "erde"}})
        self.assertEqual(st, 202)
        # SAS: Farbfolge vergleichen und bestätigen (PROTOCOL 4.2)
        for _ in range(40):
            st, j2 = c.json("GET", f"/api/v1/jobs/{j['id']}")
            if j2["state"] == "awaiting_confirmation":
                break
            time.sleep(0.2)
        self.check("/jobs/{job_id}", "get", 200, j2)
        self.assertEqual(len(j2["result"]["sas"]), 5)
        st, j3 = c.json("POST", f"/api/v1/pairing/candidates/{dev}/confirm", {"match": True})
        self.assertEqual(st, 202)
        self.check("/pairing/candidates/{device}/confirm", "post", 202, j3)
        fin = self.wait_job(c, j)
        self.assertEqual(fin["state"], "done")
        st, plant = c.json("GET", f"/api/v1/plants/{fin['result']['plant_id']}")
        self.assertEqual(plant["sensor_id"], dev)
        self.assertEqual(plant["calibration"], "default")
        # ausserhalb des Kopplungsmodus kein Koppeln möglich (REQ-RF-05)
        st, _ = c.json("POST", f"/api/v1/pairing/candidates/{dev}/accept", {"plant": {"name": "X", "substrate": "erde"}})
        self.assertEqual(st, 404)

    def test_reassign_sensor_keeps_history(self):
        c = Client(self.base)
        c.login()
        now = int(time.time())
        st, before = c.json("GET", f"/api/v1/plants/4/series?from={now - 7 * 86400}&to={now}&res=raw")
        st, p = c.json("PUT", "/api/v1/plants/8/sensor", {"sensor_id": "fluidi-4A61", "move_history": False})
        self.assertEqual(st, 200)
        self.check("/plants/{plant_id}/sensor", "put", 200, p)
        st, old = c.json("GET", "/api/v1/plants/4")
        self.assertIsNone(old["sensor_id"])
        st, after = c.json("GET", f"/api/v1/plants/4/series?from={now - 7 * 86400}&to={now}&res=raw")
        self.assertEqual(len(after["t"]), len(before["t"]))  # Historie bleibt bei der alten Pflanze
        c.json("PUT", "/api/v1/plants/4/sensor", {"sensor_id": "fluidi-4A61", "move_history": False})

    def test_csv_export(self):
        c = Client(self.base)
        now = int(time.time())
        st, hd, data = c.req("GET", f"/api/v1/export.csv?plant_ids=1,2&from={now - 2 * 86400}&to={now}&res=raw")
        self.assertEqual(st, 200)
        txt = data.decode("utf-8")
        self.assertTrue(txt.startswith("﻿# fluidi-csv v1"))
        lines = txt.strip().split("\n")
        self.assertEqual(lines[1].split(";")[0], "pflanze_id")
        self.assertTrue(all(len(l.split(";")) == 11 for l in lines[1:]))
        self.assertGreater(len(lines), 10)
        st, hd, data = c.req("GET", f"/api/v1/export.csv?from={now - 40 * 86400}&to={now}&res=day&decimal=comma")
        self.assertEqual(st, 200)
        self.assertIn(",", data.decode().split("\n")[2].split(";")[4])
        self.assertEqual(c.req("GET", f"/api/v1/export.csv?from={now}&to={now - 1}")[0], 400)

    def test_firmware(self):
        c = Client(self.base)
        c.login()
        st, fw = c.json("GET", "/api/v1/firmware")
        self.check("/firmware", "get", 200, fw)
        st, e = c.json("POST", "/api/v1/firmware/sensor-images", raw=b"BAD-signature")
        self.assertEqual((st, e["error"]["code"]), (422, "signature_invalid"))
        st, img = c.json("POST", "/api/v1/firmware/sensor-images", raw=b"\x00" * 1024)
        self.assertEqual(st, 201)
        self.check("/firmware/sensor-images", "post", 201, img)
        st, ro = c.json("POST", "/api/v1/firmware/rollout", {"version": img["version"], "sensor_ids": ["fluidi-1A2B", "fluidi-3E5F"]})
        self.assertEqual(st, 202)
        self.check("/firmware/rollout", "post", 202, ro)
        for _ in range(60):
            st, fw = c.json("GET", "/api/v1/firmware")
            if fw["rollout"]["finished"]:
                break
            time.sleep(0.3)
        items = {i["sensor_id"]: i["state"] for i in fw["rollout"]["items"]}
        self.assertEqual(items["fluidi-1A2B"], "done")
        self.assertEqual(items["fluidi-3E5F"], "failed")  # Batterie zu tief (REQ-FW-02)

    def test_unknown_and_method(self):
        c = Client(self.base)
        self.assertEqual(c.req("GET", "/api/v1/gibtsnicht")[0], 404)
        self.assertEqual(c.req("PUT", "/api/v1/plants")[0], 405)
        self.assertEqual(c.req("GET", "/api/v1/plants/abc")[0], 404)

    def test_sse_stream(self):
        import socket
        s = socket.create_connection(("127.0.0.1", self.port), timeout=5)
        s.sendall(b"GET /api/v1/stream HTTP/1.1\r\nHost: x\r\nAccept: text/event-stream\r\n\r\n")
        buf = b""
        while b"retry:" not in buf:
            buf += s.recv(4096)
        self.assertIn(b"text/event-stream", buf)
        M.Handler.S.emit("plant", {"id": 1})
        while b"event: plant" not in buf:
            buf += s.recv(4096)
        s.close()


    # ---------------------------------------------------------------- Konzept-Erweiterung
    def test_profiles_and_species(self):
        c = Client(self.base)
        st, sp = c.json("GET", "/api/v1/species")
        self.check("/species", "get", 200, sp)
        self.assertGreaterEqual(len(sp), 40)  # app/data/species.json (PFLANZENPROFILE.md, D-021)
        self.assertTrue(all("ANNAHME" in x["start_note"] for x in sp))
        self.assertEqual({x["regime"] for x in sp}, {"A", "B", "C", "D"})
        self.assertEqual(next(x for x in sp if x["key"] == "epipremnum")["regime"], "A")  # D-021 (2)
        st, cl = c.json("GET", "/api/v1/climate")
        self.check("/climate", "get", 200, cl)
        st, plants = c.json("GET", "/api/v1/plants")
        moods = {p["mood"] for p in plants}
        self.assertTrue({"happy", "thirsty", "confused", "sleepy", "unknown"} <= moods, moods)
        c.login()
        st, p = c.json("PATCH", "/api/v1/plants/1", {"species": "monstera", "upper_pct": 72, "location": "Fenster",
                                                     "pot": {"diameter_cm": 24, "material": "ton", "drainage": True}})
        self.assertEqual(st, 200)
        self.check("/plants/{plant_id}", "patch", 200, p)
        self.assertEqual(p["pot"]["material"], "ton")
        st, e = c.json("PATCH", "/api/v1/plants/1", {"upper_pct": 31})  # zu nahe an der Schwelle
        self.assertEqual(st, 400)
        st, e = c.json("PATCH", "/api/v1/plants/1", {"species": "triffid"})
        self.assertEqual(st, 400)

    def test_forecast(self):
        c = Client(self.base)
        st, f = c.json("GET", "/api/v1/plants/1/forecast")
        self.assertEqual(st, 200)
        self.check("/plants/{plant_id}/forecast", "get", 200, f)
        self.assertEqual(f["state"], "ok")
        self.assertTrue(f["days_low"] <= f["days"] <= f["days_high"])
        self.assertTrue(f["curve"]["t"])
        self.assertEqual(c.json("GET", "/api/v1/plants/2/forecast")[1]["state"], "due")       # Ficus trocken
        self.assertEqual(c.json("GET", "/api/v1/plants/6/forecast")[1]["state"], "not_applicable")  # Luft
        self.assertEqual(c.json("GET", "/api/v1/plants/8/forecast")[1]["state"], "not_applicable")  # ohne Sensor
        now = int(time.time())
        st, s = c.json("GET", f"/api/v1/plants/1/series?from={now - 60 * 86400}&to={now}")
        self.assertTrue(any(e["type"] == "watering" for e in s["events"]))

    def test_journal_watering_flow(self):
        c = Client(self.base)
        st, j = c.json("GET", "/api/v1/plants/9/journal?limit=50")
        self.check("/plants/{plant_id}/journal", "get", 200, j)
        self.assertTrue(any(e["source"] == "sensor" for e in j))
        self.assertEqual(c.json("POST", "/api/v1/plants/9/journal", {"type": "watering"})[0], 401)
        c.login()
        st, e = c.json("POST", "/api/v1/plants/9/journal", {"type": "watering", "amount_ml": 400})
        self.assertEqual(st, 201)
        self.check("/plants/{plant_id}/journal", "post", 201, e)
        for _ in range(30):  # Mock: Sensor misst nach ~2.5 s den Sprung
            st, j = c.json("GET", "/api/v1/plants/9/journal?limit=5")
            top = next(x for x in j if x["id"] == e["id"])
            if top["sensor_confirmed"]:
                break
            time.sleep(0.3)
        self.assertTrue(top["sensor_confirmed"])
        self.assertGreater(top["delta_pct"], 15)
        st, p = c.json("GET", "/api/v1/plants/9")
        self.assertIsNotNone(p["last_watered"])
        # erkannte Giessung verwerfen, eigene löschen
        det = next(x for x in c.json("GET", "/api/v1/plants/1/journal?limit=100")[1] if x["source"] == "sensor")
        st, x = c.json("PATCH", f"/api/v1/journal/{det['id']}", {"status": "rejected"})
        self.assertEqual(st, 200)
        self.check("/journal/{entry_id}", "patch", 200, x)
        ids = [x["id"] for x in c.json("GET", "/api/v1/plants/1/journal?limit=1000")[1]]
        self.assertNotIn(det["id"], ids)
        self.assertEqual(c.json("DELETE", f"/api/v1/journal/{det['id']}")[0], 409)
        self.assertEqual(c.json("DELETE", f"/api/v1/journal/{e['id']}")[0], 204)
        self.assertEqual(c.json("DELETE", "/api/v1/journal/j99999")[0], 404)
        st, err = c.json("POST", "/api/v1/plants/1/journal", {"type": "watering", "t": "2099-01-01T00:00:00Z"})
        self.assertEqual(st, 400)

    def test_roomplan(self):
        c = Client(self.base)
        st, plan = c.json("GET", "/api/v1/roomplan")
        self.check("/roomplan", "get", 200, plan)
        c.login()
        plan["rooms"][0]["plants"][0]["x_cm"] = 100
        st, new = c.json("PUT", "/api/v1/roomplan", plan)
        self.assertEqual(st, 200)
        self.check("/roomplan", "put", 200, new)
        self.assertEqual(new["version"], plan["version"] + 1)
        self.assertEqual(c.json("PUT", "/api/v1/roomplan", plan)[0], 409)  # veraltete Version
        bad = json.loads(json.dumps(new))
        bad["rooms"][0]["plants"][0]["x_cm"] = 99999
        self.assertEqual(c.json("PUT", "/api/v1/roomplan", bad)[0], 400)
        bad = json.loads(json.dumps(new))
        bad["rooms"][0]["openings"].append({"type": "window", "wall": "n", "offset_cm": 600, "length_cm": 200})
        self.assertEqual(c.json("PUT", "/api/v1/roomplan", bad)[0], 400)

    def test_stats_alerts(self):
        c = Client(self.base)
        st, s = c.json("GET", "/api/v1/stats?days=90")
        self.assertEqual(st, 200)
        self.check("/stats", "get", 200, s)
        self.assertEqual(len(s["waterings_per_week"]), 12)
        for x in s["sensors"]:
            self.assertLess(x["energy"]["avg_ua"], 8.0)  # REQ-ENE-09 (Modell)
        st, a = c.json("GET", "/api/v1/alerts")
        self.check("/alerts", "get", 200, a)
        self.assertEqual(a[0]["level"], "critical")
        self.assertTrue({"air", "battery_low", "stale", "needs_water"} <= {x["kind"] for x in a})

    def test_dashboard_public_switch(self):
        S = M.Handler.S
        c = Client(self.base)
        st, d = c.json("GET", "/api/v1/dashboard")
        self.assertEqual(st, 200)
        self.check("/dashboard", "get", 200, d)
        self.assertNotIn("fluidi-", json.dumps(d["plants"]))  # keine Sensor-IDs
        S.settings["public_read"] = False
        try:
            self.assertEqual(c.json("GET", "/api/v1/dashboard")[0], 401)
            S.settings["dashboard"]["public"] = True
            self.assertEqual(c.json("GET", "/api/v1/dashboard")[0], 200)
            self.assertEqual(c.json("GET", "/api/v1/plants")[0], 401)  # nur das Dashboard ist öffentlich
            S.settings["dashboard"]["enabled"] = False
            self.assertEqual(c.json("GET", "/api/v1/dashboard")[0], 404)
        finally:
            S.settings["public_read"] = True
            S.settings["dashboard"].update(enabled=True, public=False)

    def test_notification_settings(self):
        c = Client(self.base)
        c.login()
        st, se = c.json("PATCH", "/api/v1/settings", {"notifications": {"email": {"enabled": True, "host": "smtp.firma.local",
                                                                                   "password": "geheim", "to": "a@firma.ch"}}})
        self.assertEqual(st, 200)
        self.check("/settings", "patch", 200, se)
        self.assertTrue(se["notifications"]["email"]["password_set"])
        self.assertNotIn("password", se["notifications"]["email"])
        st, e = c.json("PATCH", "/api/v1/settings", {"notifications": {"webpush": {"enabled": True}}})
        self.assertEqual(st, 409)  # gesperrt bis Entscheid (REQ-APP-10)
        self.assertEqual(c.req("GET", "/concept/")[0], 200)


class SpecTest(unittest.TestCase):
    def test_all_spec_paths_have_mock_route(self):
        if SPEC is None:
            self.skipTest("PyYAML/jsonschema fehlen")
        have = {(m, t) for m, t, *_ in M.ROUTES}
        missing = [(m.upper(), p) for p, ops in SPEC["paths"].items() for m in ops if m in ("get", "post", "put", "patch", "delete")
                   and (m.upper(), p) not in have]
        self.assertEqual(missing, [])
        extra = [(m, t) for m, t in have if t not in SPEC["paths"] or m.lower() not in SPEC["paths"][t]]
        self.assertEqual(extra, [])

    def test_elevated_flags_match(self):
        if SPEC is None:
            self.skipTest("PyYAML fehlt")
        spec_el = {(m.upper(), p) for p, ops in SPEC["paths"].items() for m, op in ops.items() if isinstance(op, dict) and op.get("x-fluidi-elevated")}
        mock_el = {(m, t) for m, t, _rx, _fn, _a, el in M.ROUTES if el}
        self.assertEqual(spec_el, mock_el)


if __name__ == "__main__":
    unittest.main()
