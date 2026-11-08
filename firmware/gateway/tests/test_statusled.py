"""Gateway-Status-LED (D-027, docs/reviews/phase5_gateway_led.md): Zustandslogik, Anfragen nur bei Wechsel,
Root-Helfer schreibt die sysfs-Dateien (Hardware gemockt: temporäres Verzeichnis statt /sys/class/leds/fluidi)."""
import json
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest import mock
from zoneinfo import ZoneInfo

from helpers import make_gateway, wait
from fluidi_gw import helper, statusled, timesvc

TZ = ZoneInfo("Europe/Zurich")


def at(y, mo, d, hh, mm):
    return datetime(y, mo, d, hh, mm, tzinfo=TZ).timestamp()


MON_10 = at(2026, 11, 9, 10, 0)     # Montag 10:00
MON_22 = at(2026, 11, 9, 22, 0)     # Montag 22:00
SUN_10 = at(2026, 11, 15, 10, 0)    # Sonntag 10:00


class FakeModel:
    def __init__(self, **led):
        self.pairing = {"active": False, "until": None, "candidates": {}}
        self.settings = {"led": {"enabled": True, "water_window": {"start": "07:00", "end": "19:00",
                                                                   "weekdays": [1, 2, 3, 4, 5, 6, 7]}} | led}

    def tz(self):
        return TZ


class FakeCentral:
    def __init__(self, alive=True, radio_ok=True):
        self.thread = SimpleNamespace(is_alive=lambda: alive)
        self.radio_ok = radio_ok


class Desired(unittest.TestCase):
    def setUp(self):
        self._prev = timesvc._ACTIVE
        timesvc._ACTIVE = None                      # valid() = True, wall() = Systemzeit

    def tearDown(self):
        timesvc._ACTIVE = self._prev

    def test_ok_by_day(self):
        self.assertEqual(statusled.desired(FakeModel(), FakeCentral(), MON_10), "ok")

    def test_night_off(self):
        self.assertEqual(statusled.desired(FakeModel(), FakeCentral(), MON_22), "off")

    def test_weekday_deselected_off(self):
        m = FakeModel(water_window={"start": "07:00", "end": "19:00", "weekdays": [1, 2, 3, 4, 5]})
        self.assertEqual(statusled.desired(m, FakeCentral(), SUN_10), "off")
        self.assertEqual(statusled.desired(m, FakeCentral(), MON_10), "ok")

    def test_window_over_midnight(self):
        m = FakeModel(water_window={"start": "20:00", "end": "06:00"})
        self.assertEqual(statusled.desired(m, FakeCentral(), MON_22), "ok")
        self.assertEqual(statusled.desired(m, FakeCentral(), MON_10), "off")

    def test_pairing_blinks_even_at_night(self):
        m = FakeModel()
        m.pairing.update(active=True, until=MON_22 + 60)
        self.assertEqual(statusled.desired(m, FakeCentral(), MON_22), "pair")
        self.assertEqual(statusled.desired(m, FakeCentral(), MON_22 + 61), "off")      # Fenster abgelaufen

    def test_radio_failure_off(self):
        m = FakeModel()
        m.pairing.update(active=True, until=MON_10 + 60)
        self.assertEqual(statusled.desired(m, FakeCentral(radio_ok=False), MON_10), "off")
        self.assertEqual(statusled.desired(m, FakeCentral(alive=False), MON_10), "off")
        self.assertEqual(statusled.desired(m, None, MON_10), "off")

    def test_led_switch_off(self):
        self.assertEqual(statusled.desired(FakeModel(enabled=False), FakeCentral(), MON_10), "off")

    def test_invalid_time_counts_as_day(self):
        """Ohne gültige Zeit (kein NTP, keine Browserzeit) ist die Ortszeit unbekannt -> nicht als Nacht werten."""
        timesvc._ACTIVE = timesvc.TimeService("invalid", activate=False)
        self.assertEqual(statusled.desired(FakeModel(), FakeCentral(), MON_22), "ok")

    def test_patterns_match_helper(self):
        self.assertEqual(statusled.PATTERNS, helper.LED_PATTERNS)
        on, off = statusled.PATTERNS["ok"]
        self.assertEqual(on + off, 5000)                                   # Blitz alle 5 s (D-027)
        self.assertLessEqual(sum(statusled.PATTERNS["pair"]), 500)        # schnelles Blinken (≥ 2 Hz)


class Requests(unittest.TestCase):
    def setUp(self):
        self._prev = timesvc._ACTIVE
        timesvc._ACTIVE = None

    def tearDown(self):
        timesvc._ACTIVE = self._prev

    def test_only_on_change(self):
        sent = []
        m = FakeModel()
        led = statusled.StatusLed(m, FakeCentral(), lambda a, d: sent.append((a, d)))
        for _ in range(5):
            led.update(MON_10)
        m.pairing.update(active=True, until=MON_10 + 100)
        led.update(MON_10)
        led.update(MON_10 + 1)
        led.update(MON_10 + 200)
        self.assertEqual(sent, [("led", {"state": "ok"}), ("led", {"state": "pair"}), ("led", {"state": "ok"})])

    def test_failed_request_retried(self):
        calls = []

        def req(a, d):
            calls.append(d["state"])
            if len(calls) == 1:
                raise OSError("Datenträger voll")
        led = statusled.StatusLed(FakeModel(), FakeCentral(), req)
        led.update(MON_10)
        led.update(MON_10)
        self.assertEqual(calls, ["ok", "ok"])
        self.assertEqual(led.state, "ok")

    def test_exception_in_logic_gives_off(self):
        m = FakeModel()
        m.settings = None                     # kaputte Einstellungen dürfen den Dienst nicht stören
        sent = []
        led = statusled.StatusLed(m, FakeCentral(), lambda a, d: sent.append(d["state"]))
        self.assertEqual(led.update(MON_10), "off")
        self.assertEqual(sent, ["off"])


class HelperLed(unittest.TestCase):
    """Root-Helfer mit gemocktem sysfs-Verzeichnis."""

    def setUp(self):
        self.d = Path(tempfile.mkdtemp(prefix="fluidi-led-"))
        for f in ("trigger", "brightness", "delay_on", "delay_off"):
            (self.d / f).write_text("")
        self.p = mock.patch.object(helper, "LED_DIR", self.d)
        self.p.start()

    def tearDown(self):
        self.p.stop()

    def read(self, f):
        return (self.d / f).read_text()

    def test_ok_flash_every_5s(self):
        helper.do_led({"state": "ok"})
        self.assertEqual((self.read("trigger"), self.read("delay_on"), self.read("delay_off")), ("timer", "100", "4900"))

    def test_pair_fast(self):
        helper.do_led({"state": "pair"})
        self.assertEqual((self.read("trigger"), self.read("delay_on"), self.read("delay_off")), ("timer", "100", "100"))

    def test_off(self):
        helper.do_led({"state": "pair"})
        helper.do_led({"state": "off"})
        self.assertEqual((self.read("trigger"), self.read("brightness")), ("none", "0"))

    def test_invalid_state_rejected(self):
        for bad in ("heartbeat", "default-on", "../../x", None, 1):
            with self.assertRaises(ValueError):
                helper.do_led({"state": bad})
        self.assertEqual(self.read("trigger"), "")

    def test_cli_led_off(self):
        """ExecStopPost=+… fluidi-helper led off"""
        helper.do_led({"state": "ok"})
        helper.main(["led", "off"])
        self.assertEqual(self.read("trigger"), "none")
        with self.assertRaises(SystemExit):
            helper.main(["led", "blink"])
        with self.assertRaises(SystemExit):
            helper.main(["reboot"])                    # nur "led <zustand>" ist als Aufruf erlaubt

    def test_missing_led_no_error(self):
        with mock.patch.object(helper, "LED_DIR", self.d / "fehlt"):
            helper.do_led({"state": "ok"})            # Overlay fehlt: nur Hinweis, kein Absturz

    def test_request_file_processed(self):
        req = Path(tempfile.mkdtemp(prefix="fluidi-req-"))
        (req / "1-led.json").write_text(json.dumps({"action": "led", "state": "pair"}))
        with mock.patch.object(helper, "REQ", req):
            helper.main([])
        self.assertEqual(self.read("delay_off"), "100")
        self.assertEqual(list(req.iterdir()), [])


class InGateway(unittest.TestCase):
    """Dienst mit simulierten Sensoren: LED-Anfragen an den Helfer (Verzeichnis requests) bei Zustandswechsel."""

    @classmethod
    def setUpClass(cls):
        cls.req = Path(tempfile.mkdtemp(prefix="fluidi-req-"))
        cls.gw, _ = make_gateway(sensors=0, http=False, status_led="on", helper_dir=cls.req)
        M = cls.gw.model
        M.settings["led"]["water_window"] = {"start": "00:00", "end": "00:00", "weekdays": [1, 2, 3, 4, 5, 6, 7]}
        cls.gw.led.interval = 0.05
        cls.gw.led.start()

    @classmethod
    def tearDownClass(cls):
        cls.gw.stop()

    def states(self):
        return [json.loads(f.read_text())["state"] for f in sorted(self.req.glob("*-led.json"))]

    def test_sequence(self):
        self.assertTrue(wait(lambda: self.states()[-1:] == ["ok"], 5), self.states())
        M = self.gw.model
        M.pairing.update(active=True, until=timesvc.wall() + 30, candidates={})
        self.assertTrue(wait(lambda: self.states()[-1:] == ["pair"], 5), self.states())
        M.pairing.update(active=False, until=None, candidates={})
        self.assertTrue(wait(lambda: self.states()[-1:] == ["ok"], 5), self.states())
        n = len(self.states())
        time.sleep(0.3)
        self.assertEqual(len(self.states()), n)              # keine Anfragen ohne Wechsel (SD-Karte)

    def test_sim_default_without_led(self):
        gw, _ = make_gateway(sensors=0, http=False)
        try:
            self.assertIsNone(gw.led)                      # Simulation: keine LED-Anfragen
        finally:
            gw.stop()


if __name__ == "__main__":
    unittest.main()
