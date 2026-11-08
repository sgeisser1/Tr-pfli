"""Integrationstest: echter Gateway-Dienst (HTTP, SQLite, Funk-Simulation über das echte Protokoll) gegen
app/api/openapi.yaml (Schemas, Zugriffsregeln) – wie app/tests/test_mock_api.py für den Mock."""
import json
import socket
import time
import unittest
import urllib.request
from pathlib import Path

from helpers import PASSWORD, ROOT, Client, make_gateway, wait
from fluidi_gw import api, backup, crypto, mcuboot

try:
    import jsonschema
    import yaml
    SPEC = yaml.safe_load((ROOT.parent.parent / "app" / "api" / "openapi.yaml").read_text(encoding="utf-8"))
except Exception:  # pragma: no cover
    SPEC = None


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


class GatewayApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = crypto.SigningKey()
        d = Path(__import__("tempfile").mkdtemp())
        (d / "fw.pem").write_text(cls.key.public_pem())
        cls.dash_port = free_port()
        cls.gw, srv = make_gateway(sensors=2, history_days=30, fw_pubkey=d / "fw.pem", dashboard_port=cls.dash_port)
        cls.base = f"http://127.0.0.1:{srv.server_address[1]}"
        cls.c = Client(cls.base)
        st, _ = cls.c.setup(cls.gw.model.setup_code)
        assert st == 200
        wait(lambda: all(s.acked >= s.seq - 1 for s in cls.gw.sims[:2]), 20)

    @classmethod
    def tearDownClass(cls):
        cls.gw.stop()

    def check(self, tpl, method, status, obj):
        if SPEC is None:
            return
        resp = SPEC["paths"][tpl][method]["responses"][str(status)]
        if "$ref" in resp:
            resp = SPEC["components"]["responses"][resp["$ref"].split("/")[-1]]
        sch = resp["content"]["application/json"]["schema"]
        jsonschema.Draft202012Validator({"$schema": "https://json-schema.org/draft/2020-12/schema",
                                         "components": SPEC["components"], **sch},
                                        format_checker=jsonschema.FormatChecker()).validate(obj)

    def test_routes_match_spec(self):
        if SPEC is None:
            self.skipTest("PyYAML/jsonschema fehlen")
        have = {(m, t) for m, t, *_ in api.ROUTES}
        spec = {(m.upper(), p) for p, ops in SPEC["paths"].items() for m in ops if m in ("get", "post", "put", "patch", "delete")}
        self.assertEqual(spec - have, set())
        self.assertEqual(have - spec, set())
        el = {(m.upper(), p) for p, ops in SPEC["paths"].items() for m, op in ops.items() if isinstance(op, dict) and op.get("x-fluidi-elevated")}
        self.assertEqual(el, {(m, t) for m, t, _r, _f, _a, e in api.ROUTES if e})

    def test_read_requires_login_by_default(self):
        anon = Client(self.base)
        st, _ = anon.json("GET", "/api/v1/plants")
        self.assertEqual(st, 401)  # public_read Werk aus (F-8)
        st, s = anon.json("GET", "/api/v1/auth/status")
        self.check("/auth/status", "get", 200, s)
        self.assertFalse(s["setup_required"])

    def test_read_schemas(self):
        c = self.c
        for path, tpl in (("/plants", "/plants"), ("/sensors", "/sensors"), ("/settings", "/settings"), ("/system", "/system"),
                          ("/species", "/species"), ("/alerts", "/alerts"), ("/roomplan", "/roomplan"), ("/stats", "/stats"),
                          ("/firmware", "/firmware"), ("/climate", "/climate"), ("/pairing", "/pairing"),
                          ("/plants/1", "/plants/{plant_id}"), ("/plants/1/forecast", "/plants/{plant_id}/forecast"),
                          ("/plants/1/journal", "/plants/{plant_id}/journal"), ("/system/events", "/system/events")):
            st, js = c.json("GET", "/api/v1" + path)
            self.assertEqual(st, 200, path)
            self.check(tpl, "get", 200, js)
        st, js = c.json("GET", "/api/v1/plants")
        self.assertTrue(all(p["latest"] for p in js if p["id"] in (1, 2)), "Verlauf aus der Nachlieferung sichtbar")
        to = int(time.time())
        for res in ("raw", "hour", "day", "auto"):
            st, ser = c.json("GET", f"/api/v1/plants/1/series?from={to - 20 * 86400}&to={to}&res={res}")
            self.check("/plants/{plant_id}/series", "get", 200, ser)
            self.assertTrue(any(m is not None for m in ser["moisture"]), res)

    def test_write_needs_csrf_and_elevate(self):
        st, _ = self.c.json("PATCH", "/api/v1/plants/1", {"notes": "x"}, headers={"X-CSRF-Token": "falsch"})
        self.assertEqual(st, 403)
        st, p = self.c.json("PATCH", "/api/v1/plants/1", {"notes": "Fensterbank", "regime": "A", "winter_factor": 0.5})
        self.assertEqual(st, 200)
        self.check("/plants/{plant_id}", "patch", 200, p)
        self.assertEqual(p["regime"], "A")
        sess = next(iter(self.gw.model.sessions.values()))
        sess["elevated_until"] = 0
        st, e = self.c.json("POST", "/api/v1/backup", {"passphrase": "lange-passphrase-1"})
        self.assertEqual((st, e["error"]["code"]), (403, "elevation_required"))
        st, _ = self.c.json("POST", "/api/v1/auth/elevate", {"password": PASSWORD})
        self.assertEqual(st, 200)

    def test_system_time_browser(self):
        """REQ-GW-09: Browserzeit nur ohne gültige Zeit, unplausible Zeit -> 400 (phase5_gateway_zeit.md)."""
        from fluidi_gw import timesvc
        st, e = self.c.json("POST", "/api/v1/system/time", {"t": "1999-12-31T23:00:00Z"})
        self.assertEqual((st, e["error"]["code"]), (400, "validation"))
        st, r = self.c.json("POST", "/api/v1/system/time", {"epoch_ms": int(time.time() * 1000) + 7200_000})
        self.assertEqual(st, 200)
        self.check("/system/time", "post", 200, r)
        self.assertEqual(r["source"], "ntp")                      # Sim-Zeit gilt als gültig: nicht übernommen
        M, prev, prev_active = self.gw.model, self.gw.model.time, timesvc._ACTIVE
        M.time = timesvc.TimeService("invalid")
        try:
            target = time.time() + 2 * 86400        # Systemuhr lag 2 Tage zurück (Stromausfall ohne NTP)
            st, r = self.c.json("POST", "/api/v1/system/time", {"epoch_ms": int(target * 1000)})
            self.assertEqual((st, r["valid"], r["source"]), (200, True, "browser"))
            self.assertAlmostEqual(timesvc.wall(), target, delta=5)
            st, a = self.c.json("GET", "/api/v1/auth/status")
            self.assertTrue(a["logged_in"])                       # Sitzungsfrist mitgezogen
        finally:
            d = M.time.now() - prev.now()
            M.time, timesvc._ACTIVE = prev, prev_active
            for se in M.sessions.values():          # Fristen für die übrigen Tests zurückschieben
                se["expires"] -= d
                if se.get("elevated_until"):
                    se["elevated_until"] -= d

    def test_measure_job_via_radio(self):
        st, j = self.c.json("POST", "/api/v1/plants/1/measure")
        self.assertEqual(st, 202)
        fin = self.c.job(j)
        self.check("/jobs/{job_id}", "get", 200, fin)
        self.assertEqual(fin["state"], "done", fin["message"])
        self.assertEqual(fin["result"]["reading"]["source"], "manual")

    def test_sensor_diag(self):
        """O-1: GET_INFO + GET_DIAG als Job, Rohdaten + dekodiert gespeichert, nur mit Sitzung/CSRF lesbar/auslösbar."""
        st, sensors = self.c.json("GET", "/api/v1/sensors")
        sid = sensors[0]["id"]
        self.assertIn("fw_build", sensors[0])
        self.assertEqual(sensors[0]["testfw"], 0)
        anon = Client(self.base)
        self.assertEqual(anon.json("POST", f"/api/v1/sensors/{sid}/diag")[0], 401)
        self.assertEqual(anon.json("GET", f"/api/v1/sensors/{sid}/diag")[0], 401)
        st, e = self.c.json("POST", f"/api/v1/sensors/{sid}/diag", headers={"X-CSRF-Token": "falsch"})
        self.assertEqual((st, e["error"]["code"]), (403, "csrf"))
        st, e = self.c.json("POST", f"/api/v1/sensors/{sid}/diag", headers={"Origin": "https://evil.example"})
        self.assertEqual(st, 403)
        st, j = self.c.json("POST", f"/api/v1/sensors/{sid}/diag")
        self.assertEqual(st, 202)
        self.check("/sensors/{sensor_id}/diag", "post", 202, j)
        st, j2 = self.c.json("POST", f"/api/v1/sensors/{sid}/diag")
        self.assertEqual(j2["id"], j["id"])                       # kein Doppelauftrag
        fin = self.c.job(j)
        self.assertEqual(fin["state"], "done", fin["message"])
        r = fin["result"]
        self.assertEqual(len(bytes.fromhex(r["info_hex"])), 68)   # Serie: 68 Byte (PROTOCOL 5.5)
        self.assertEqual(r["info"]["fw_build"], 100)
        self.assertEqual((r["testfw"], r["decode_errors"]), (0, []))
        self.assertIsNone(r["diag"]["tf"])
        st, lst = self.c.json("GET", f"/api/v1/sensors/{sid}/diag?limit=5")
        self.assertEqual(st, 200)
        self.check("/sensors/{sensor_id}/diag", "get", 200, lst)
        self.assertEqual(lst[0]["info_hex"], r["info_hex"])
        st, s = self.c.json("GET", f"/api/v1/sensors/{sid}")
        self.check("/sensors/{sensor_id}", "get", 200, s)
        self.assertEqual(s["fw_build"], 100)
        self.assertIsNotNone(s["diag_last"])
        self.assertEqual(self.c.json("GET", "/api/v1/sensors/fluidi-0000/diag")[0], 404)

    def test_pairing_with_sas(self):
        st, p = self.c.json("POST", "/api/v1/pairing/start", {"duration_s": 60})
        self.assertEqual(st, 200)
        p = wait(lambda: (self.c.json("GET", "/api/v1/pairing")[1] or {}).get("candidates"), 10)
        self.assertTrue(p)
        dev = p[0]["device"]
        st, j = self.c.json("POST", f"/api/v1/pairing/candidates/{dev}/accept", {"plant": {"name": "Neu", "substrate": "erde", "species": "calathea"}})
        self.assertEqual(st, 202)
        j2 = self.c.job(j)
        self.assertEqual(j2["state"], "awaiting_confirmation")
        self.assertTrue(set(j2["result"]["sas"]) <= {"rot", "grün", "gelb"})
        st, j3 = self.c.json("POST", f"/api/v1/pairing/candidates/{dev}/confirm", {"match": True})
        self.assertEqual(st, 202)
        fin = wait(lambda: (lambda x: x if x["state"] in ("done", "failed") else None)(self.c.json("GET", f"/api/v1/jobs/{j['id']}")[1]), 15)
        self.assertEqual(fin["state"], "done", fin["message"])

    def test_firmware_upload(self):
        self.c.json("POST", "/api/v1/auth/elevate", {"password": PASSWORD})
        bad = mcuboot.build(b"\x00" * 3000, (9, 9, 9), key=crypto.SigningKey())
        st, e = self.c.json("POST", "/api/v1/firmware/sensor-images", raw=bad)
        self.assertEqual((st, e["error"]["code"]), (422, "signature_invalid"))
        good = mcuboot.build(b"\x00" * 3000, (9, 9, 9), key=self.key)
        st, img = self.c.json("POST", "/api/v1/firmware/sensor-images", raw=good)
        self.assertEqual(st, 201, img)
        self.check("/firmware/sensor-images", "post", 201, img)
        st, _ = self.c.json("DELETE", "/api/v1/firmware/sensor-images/9.9.9")
        self.assertEqual(st, 204)

    def test_journal_fertilized_and_csv(self):
        st, e = self.c.json("POST", "/api/v1/plants/1/journal", {"type": "fertilizing", "note": "halbe Dosis"})
        self.assertEqual(st, 201)
        self.check("/plants/{plant_id}/journal", "post", 201, e)
        st, p = self.c.json("GET", "/api/v1/plants/1")
        self.assertIn(p["salt"]["state"], ("fertilized", "suspected"))
        to = int(time.time())
        st, hd, data = self.c.req("GET", f"/api/v1/export.csv?from={to - 40 * 86400}&to={to}&res=raw")
        self.assertEqual(st, 200)
        txt = data.decode("utf-8-sig")
        self.assertTrue(txt.startswith("# fluidi-csv v1"))
        self.assertGreater(txt.count("\n"), 50)

    def test_backup_roundtrip(self):
        self.c.json("POST", "/api/v1/auth/elevate", {"password": PASSWORD})
        st, hd, data = self.c.req("POST", "/api/v1/backup", {"passphrase": "lange-passphrase-1"})
        self.assertEqual(st, 200)
        self.assertTrue(data.startswith(b"FLUIDIBK"))
        st, r = self.c.json("POST", "/api/v1/backup/restore?dry_run=true", raw=data, headers={"X-Backup-Passphrase": "lange-passphrase-1"})
        self.assertEqual(st, 202, r)
        self.check("/backup/restore", "post", 202, r)
        self.assertGreater(r["records"], 100)
        st, e = self.c.json("POST", "/api/v1/backup/restore?dry_run=true", raw=data, headers={"X-Backup-Passphrase": "falsche-passphrase"})
        self.assertEqual(st, 422)
        with self.assertRaises(backup.BackupError):
            backup.open_backup(data[:-1] + bytes([data[-1] ^ 1]), "lange-passphrase-1")

    def test_public_dashboard_port(self):
        url = f"http://127.0.0.1:{self.dash_port}"
        st, s = self.c.json("PATCH", "/api/v1/settings", {"dashboard": {"public": True}})
        self.assertEqual(st, 200)
        with urllib.request.urlopen(url + "/api/v1/dashboard", timeout=5) as r:
            d = json.loads(r.read())
        self.check("/dashboard", "get", 200, d)
        self.assertNotIn("sensor_id", json.dumps(d))
        for path, code in (("/api/v1/plants", 404), ("/api/v1/system", 404), ("/index.html", 404)):
            try:
                urllib.request.urlopen(url + path, timeout=5)
                self.fail(path)
            except urllib.error.HTTPError as e:
                self.assertEqual(e.code, code, path)
        req = urllib.request.Request(url + "/api/v1/dashboard", data=b"{}", method="POST")
        with self.assertRaises(urllib.error.HTTPError):
            urllib.request.urlopen(req, timeout=5)
        self.c.json("PATCH", "/api/v1/settings", {"dashboard": {"public": False}})
        time.sleep(0.3)
        with self.assertRaises(OSError):
            urllib.request.urlopen(url + "/api/v1/dashboard", timeout=2)

    def test_settings_rules(self):
        st, e = self.c.json("PATCH", "/api/v1/settings", {"notifications": {"email": {"enabled": True}}})
        self.assertEqual(st, 409)  # D-020: keine E-Mail
        st, e = self.c.json("PATCH", "/api/v1/settings", {"time": {"timezone": "Mars/Olympus"}})
        self.assertEqual(st, 400)
        st, s = self.c.json("PATCH", "/api/v1/settings", {"reaction_time_min": 2})
        self.assertEqual(st, 200)
        self.check("/settings", "patch", 200, s)
        s0 = self.gw.sims[0]
        self.assertTrue(wait(lambda: s0.settings["adv_interval_ms"] == 57500, 15))  # Tab. 2.2: 2 min -> 57.5 s
        self.c.json("PATCH", "/api/v1/settings", {"reaction_time_min": 1})

    def test_login_lockout(self):
        x = Client(self.base)
        for _ in range(5):
            x.json("POST", "/api/v1/auth/login", {"password": "falsch-falsch"})
        st, e = x.json("POST", "/api/v1/auth/login", {"password": PASSWORD})
        self.assertEqual(st, 429)
        self.gw.model.fails.clear()
        self.gw.model.global_fails.clear()


if __name__ == "__main__":
    unittest.main()
