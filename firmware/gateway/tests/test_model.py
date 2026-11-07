"""Fachregeln: Artenprofile (species.json, D-021), Winterfaktor, „zu nass“ erst nach 48 h, Regime-Hinweise,
Batterieschätzung, Einstellungen an den Sensor, HTTPS-Zertifikat (Einmal-CA mit Name Constraint)."""
import tempfile
import time
import unittest
from pathlib import Path

from helpers import make_gateway
from fluidi_gw import pki
from fluidi_gw import protocol as P


class Rules(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gw, _ = make_gateway(sensors=0, http=False)
        cls.M = cls.gw.model

    @classmethod
    def tearDownClass(cls):
        cls.gw.stop()

    def plant(self, **kw):
        body = {"name": "P", "substrate": "erde", "threshold_pct": 30, "upper_pct": 75, "species": "monstera"} | kw
        return self.M.create_plant(body)

    def analysis(self, last_watered=None, events=()):
        return {"last_watered": last_watered, "events_ok": list(events)}

    def latest(self, m):
        return {"moisture_pct": m, "moisture_state": "ok" if m >= 30 else "dry"}

    def test_species_file(self):
        sp = self.M.species()
        self.assertGreaterEqual(len(sp), 40)
        ep = next(x for x in sp if x["key"] == "epipremnum")
        self.assertEqual((ep["regime"], ep["water_class"]), ("A", "dry"))   # D-021 Entscheid 2
        self.assertTrue(all(s["url"] for s in ep["sources"]))
        hy = next(x for x in sp if x["key"] == "hydrokultur")
        self.assertIsNone(hy["start_range"]["lower_pct"])

    def test_too_wet_only_after_48h(self):
        p = self.plant()
        t = time.time()
        c = self.M.care(p, self.latest(85), self.analysis(last_watered=t - 3600), False)
        self.assertFalse(c["too_wet"])                       # direkt nach dem Giessen: kein Fehlalarm
        c = self.M.care(p, self.latest(85), self.analysis(last_watered=t - 49 * 3600), False)
        self.assertTrue(c["too_wet"])
        self.assertTrue(any(h["kind"] == "too_wet" for h in c["hints"]))

    def test_regime_a_dry_phase_and_early(self):
        p = self.plant(species="sansevieria", threshold_pct=15, upper_pct=55)
        self.assertEqual(self.M.regime(p), "A")
        ev = {"t": time.time() - 3600, "before": 40, "peak": 70}
        c = self.M.care(p, self.latest(50), self.analysis(time.time() - 3600, [ev]), False)
        kinds = {h["kind"] for h in c["hints"]}
        self.assertEqual(c["phase"], "dry_phase")
        self.assertIn("early", kinds)                        # 40 > 15 + 15
        self.assertIn("not_thorough", kinds)                 # Spitze 70 < 80

    def test_winter_factor(self):
        p = self.plant(species="kaktus", threshold_pct=20, upper_pct=50)
        jan = time.mktime((2027, 1, 15, 12, 0, 0, 0, 0, -1))
        jul = time.mktime((2027, 7, 15, 12, 0, 0, 0, 0, -1))
        self.assertTrue(self.M.winter_active(p, jan))
        self.assertFalse(self.M.winter_active(p, jul))
        p2 = self.plant(species="kaktus", threshold_pct=20, upper_pct=50, winter=False)
        self.assertFalse(self.M.winter_active(p2, jan))

    def test_battery_estimate(self):
        s = {"id": "fluidi-0001"}
        si = P.SessionInfo(vbat_load_mv=2980, charge_uc=0)
        self.M._battery(s, si, time.time())
        self.assertEqual(s["battery"]["state"], "ok")
        self.assertGreater(s["battery"]["days_left"], 400)   # D-006: pessimistisch 17 Monate
        si = P.SessionInfo(vbat_load_mv=2500, charge_uc=0)
        self.M._battery(s, si, time.time())
        self.assertEqual(s["battery"]["state"], "low")


class Tls(unittest.TestCase):
    def test_one_time_ca_with_name_constraint(self):
        try:
            from cryptography import x509
        except ImportError:
            self.skipTest("cryptography fehlt")
        d = Path(tempfile.mkdtemp())
        fp = pki.init(d, "fluidi.local")
        self.assertEqual(len(fp.split(":")), 32)
        ca = x509.load_pem_x509_certificate((d / "ca.crt").read_bytes())
        nc = ca.extensions.get_extension_for_class(x509.NameConstraints)
        self.assertTrue(nc.critical)
        self.assertEqual([n.value for n in nc.value.permitted_subtrees], ["fluidi.local"])
        self.assertEqual((d / "server.key").stat().st_mode & 0o777, 0o600)
        self.assertFalse(list(d.glob("*ca*.key")))           # CA-Schlüssel nie gespeichert
        info = pki.info(d)
        self.assertLessEqual(info["days_left"], 825)
        pki.server_context(d)                                  # lädt Kette + Schlüssel


if __name__ == "__main__":
    unittest.main()
