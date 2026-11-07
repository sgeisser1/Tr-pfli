"""Unit-Tests der Python-Fassung (app/dev/fluidi_calc.py) gegen die gemeinsamen Vektoren.

Start: python3 -m unittest discover -s app/tests -p 'test_*.py'
"""
import json
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "dev"))
import fluidi_calc as C  # noqa: E402

V = json.loads((HERE / "vectors" / "calc_vectors.json").read_text(encoding="utf-8"))


def near(a, b, eps=1e-6):
    if a is None or b is None:
        return a is b
    return abs(a - b) < eps


class CalcVectors(unittest.TestCase):
    def test_round1(self):
        for v in V["round1"]:
            self.assertEqual(C.round1(v["x"]), v["y"], v)
        self.assertIsNone(C.round1(float("nan")))

    def test_evaluate(self):
        for v in V["evaluate"]:
            r = C.evaluate(v["raw"], v["temp_c"], v["cal"], v["threshold"])
            self.assertEqual(r["moisture_state"], v["state"], v["_c"])
            self.assertEqual(r["moisture_pct"], v["pct"], v["_c"])
            self.assertEqual(r["moisture_unclamped"], v["unclamped"], v["_c"])

    def test_robust_mean(self):
        for v in V["robust_mean"]:
            r = C.robust_mean(v["x"])
            self.assertTrue(near(r["mean"], v["mean"]), v)
            self.assertTrue(near(r["stddev"], v["stddev"]), v)
            self.assertEqual(r["n"], v["n"])
            self.assertEqual(r["outliers"], v["outliers"])

    def test_signal_battery(self):
        for v in V["signal_quality"]:
            self.assertEqual(C.signal_quality(v["rssi"]), v["q"], v)
        for v in V["battery_bars"]:
            self.assertEqual(C.battery_bars(v["pct"]), v["bars"], v)

    def test_resolution_and_stale(self):
        for v in V["choose_resolution"]:
            self.assertEqual(C.choose_resolution(0, v["days"] * 86400, v["per_day"]), v["res"], v)
        now = 1_800_000_000
        for v in V["is_stale"]:
            self.assertEqual(C.is_stale(now - v["age_s"], now, v["per_day"]), v["stale"], v)

    def test_compensation_inverse(self):
        k, t, ref, raw_ref = 0.003, 28.0, 20.0, 30000.0
        self.assertTrue(near(C.compensate_raw(raw_ref * (1 + k * (t - ref)), t, k, ref), raw_ref))
        self.assertEqual(C.compensate_raw(1234, None, 0.01), 1234)


class Aggregation(unittest.TestCase):
    def test_day_buckets_local_time_and_dst(self):
        # 2026-10-25 ist Ende der Sommerzeit in Zürich: der Tag hat 25 h, bleibt aber ein Eimer.
        from datetime import datetime
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Zurich")
        day0 = int(datetime(2026, 10, 25, 0, 0, tzinfo=tz).timestamp())
        day1 = int(datetime(2026, 10, 26, 0, 0, tzinfo=tz).timestamp())
        self.assertEqual(day1 - day0, 25 * 3600)
        pts = [(day0 + 600, 40.0, 20.0), (day0 + 24 * 3600 + 600, 60.0, 22.0),  # beide am 25.10.
               (day1 + 60, 10.0, None), (day1 + 120, None, 19.0)]
        a = C.aggregate(pts, "day")
        self.assertEqual(a["t"], [day0, day1])
        self.assertEqual(a["moisture"], [50.0, 10.0])
        self.assertEqual(a["moisture_min"], [40.0, 10.0])
        self.assertEqual(a["moisture_max"], [60.0, 10.0])
        self.assertEqual(a["temp_c"], [21.0, 19.0])

    def test_hour_bucket_without_valid_moisture(self):
        t0 = 1_800_000_000 - (1_800_000_000 % 3600)
        a = C.aggregate([(t0 + 5, None, 21.0)], "hour", "UTC")
        self.assertEqual(a["moisture"], [None])
        self.assertEqual(a["temp_c"], [21.0])


if __name__ == "__main__":
    unittest.main()
