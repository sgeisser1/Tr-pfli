"""Unit-Tests Giess-Erkennung, Austrocknungsmodell, Prognose, Stimmung (app/dev/fluidi_analysis.py).

Start: python3 -m unittest discover -s app/tests -p 'test_*.py'
"""
import math
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "dev"))
import fluidi_analysis as A  # noqa: E402

DAY = 86400
STEP = DAY / 6  # Standardprofil 6 Werte/Tag


def synth(k_list, start=0, m_peak=85.0, m_water=28.0, noise=0.0, seed=1, step=STEP):
    """Zyklen mit exponentieller Austrocknung; gegossen wird, wenn m_water unterschritten ist."""
    r = random.Random(seed)
    pts, waters = [], []
    t = start
    for k in k_list:
        m0 = m_peak
        t0 = t
        waters.append(t)
        while True:
            m = m0 * math.exp(-k * (t - t0) / DAY)
            pts.append((t, m + r.gauss(0, noise)))
            t += step
            if m < m_water:
                break
    return pts, waters


class Detection(unittest.TestCase):
    def test_finds_each_watering(self):
        pts, waters = synth([0.12, 0.15, 0.10, 0.13], noise=0.6)
        ev = A.detect_waterings(pts)
        # die erste "Giessung" ist der Anfang der Reihe (kein Sprung), danach 3 Sprünge
        self.assertEqual(len(ev), 3)
        for e, w in zip(ev, waters[1:]):
            self.assertEqual(e["t"], w)
            self.assertGreater(e["delta"], 50)
            self.assertFalse(e["uncertain_time"])

    def test_noise_and_small_rise_ignored(self):
        pts = [(i * STEP, 50 + (3 if i % 2 else 0)) for i in range(60)]
        pts[30] = (30 * STEP, 61)  # Ausreisser +11 pp, unter RISE_MIN_PP
        self.assertEqual(A.detect_waterings(pts), [])

    def test_two_step_rise_is_one_event(self):
        pts = [(0, 30), (STEP, 29.5), (2 * STEP, 45), (3 * STEP, 70), (4 * STEP, 69)]
        ev = A.detect_waterings(pts)
        self.assertEqual(len(ev), 1)
        self.assertAlmostEqual(ev[0]["delta"], 40.5)
        self.assertEqual(ev[0]["t_peak"], 3 * STEP)

    def test_gap_marks_uncertain_time(self):
        pts = [(0, 30), (STEP, 29), (STEP + 3 * DAY, 80), (2 * STEP + 3 * DAY, 79)]
        ev = A.detect_waterings(pts)
        self.assertTrue(ev[0]["uncertain_time"])

    def test_button_merge(self):
        pts, waters = synth([0.12, 0.12])
        ev = A.detect_waterings(pts, button_times=[waters[1] - 3600, waters[1] + 5 * DAY])
        self.assertEqual(ev[0]["button_t"], waters[1] - 3600)


class Fit(unittest.TestCase):
    def test_recovers_k(self):
        pts, _ = synth([0.14], noise=0.0)
        f = A.fit_drying(pts)
        self.assertAlmostEqual(f["k"], 0.14, places=3)
        self.assertGreater(f["r2"], 0.999)

    def test_too_short(self):
        self.assertIsNone(A.fit_drying([(0, 80), (STEP, 79), (2 * STEP, 78)]))

    def test_rising_rejected(self):
        self.assertIsNone(A.fit_drying([(i * STEP, 40 + i) for i in range(12)]))


class Forecast(unittest.TestCase):
    def test_prediction_matches_model(self):
        k = 0.12
        pts, _ = synth([k, k, k, k], noise=0.3, seed=3)
        # laufender Zyklus: 2 Tage nach dem letzten Giessen abschneiden
        t_w = [e["t_peak"] for e in A.detect_waterings(pts)][-1]
        cur = [p for p in pts if p[0] <= t_w + 2 * DAY]
        ev = A.detect_waterings(cur)
        now = cur[-1][0]
        fc = A.forecast(cur, ev, 30, now)
        self.assertEqual(fc["state"], "ok")
        expect = math.log(cur[-1][1] / 30) / k
        self.assertAlmostEqual(fc["days"], expect, delta=0.4)
        self.assertLessEqual(fc["days_low"], fc["days"])
        self.assertGreaterEqual(fc["days_high"], fc["days"])
        self.assertEqual(fc["confidence"], "high")
        self.assertIn("Restwassers", fc["explanation"])
        curve = A.forecast_curve(now, cur[-1][1], fc, 30)
        self.assertLessEqual(curve["moisture"][-1], 31)

    def test_variable_cycles_lower_confidence(self):
        pts, _ = synth([0.06, 0.2, 0.09, 0.25], noise=0.3)
        ev = A.detect_waterings(pts)
        fc = A.forecast(pts[:-8], ev, 30, pts[-9][0])
        self.assertIn(fc["confidence"], ("low", "medium"))
        self.assertGreater(fc["days_high"] - fc["days_low"], 1.0)

    def test_due_and_insufficient(self):
        pts = [(i * STEP, 40 - i) for i in range(15)]
        self.assertEqual(A.forecast(pts, [], 30, pts[-1][0])["state"], "due")
        self.assertEqual(A.forecast([(0, 80), (STEP, 79)], [], 30, STEP)["state"], "insufficient_data")
        self.assertEqual(A.forecast([], [], 30, 0)["state"], "insufficient_data")

    def test_elapsed_time_counts(self):
        pts, _ = synth([0.12, 0.12, 0.12])
        cut = [p for p in pts if p[0] <= pts[-1][0] - 2 * DAY]
        ev = A.detect_waterings(cut)
        a = A.forecast(cut, ev, 30, cut[-1][0])
        b = A.forecast(cut, ev, 30, cut[-1][0] + DAY)
        self.assertAlmostEqual(a["days"] - b["days"], 1.0, delta=0.02)


class Mood(unittest.TestCase):
    def test_mapping(self):
        self.assertEqual(A.mood("ok", 60, 30, 80, False, True, None, 4), "happy")
        self.assertEqual(A.mood("ok", 33, 30, 80, False, True, None, 0.5), "ok")
        self.assertEqual(A.mood("dry", 25, 30, 80, False, True, None, 0), "thirsty")
        self.assertEqual(A.mood("dry", 12, 30, 80, False, True, None, 0), "parched")
        self.assertEqual(A.mood("ok", 90, 30, 80, False, True, None, 9), "drowning")
        self.assertEqual(A.mood("air", None, 30, 80, False, True, None, None), "confused")
        self.assertEqual(A.mood("ok", 50, 30, 80, True, True, None, 3), "sleepy")
        self.assertEqual(A.mood(None, None, 30, 80, False, False, None, None), "unknown")
        self.assertEqual(set(A.MOODS), {"happy", "ok", "thirsty", "parched", "drowning", "confused", "sleepy", "unknown"})


if __name__ == "__main__":
    unittest.main()
