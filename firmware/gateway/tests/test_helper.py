"""Root-Helfer: Anfragedateien sicher lesen (Sicherheit K-3: O_NOFOLLOW, nur reguläre Dateien, <= 4 kB)."""
import json
import os
import tempfile
import threading
import unittest
from pathlib import Path

import helpers  # noqa: F401  (Pfad)
from fluidi_gw import helper


class Requests(unittest.TestCase):
    def setUp(self):
        self.d = Path(tempfile.mkdtemp())
        self.req = self.d / "requests"
        self.req.mkdir()
        self.calls = []
        self._old = helper.REQ, dict(helper.ACTIONS)
        helper.REQ = self.req
        helper.ACTIONS.clear()
        helper.ACTIONS["led"] = lambda r: self.calls.append(r)

    def tearDown(self):
        helper.REQ = self._old[0]
        helper.ACTIONS.clear()
        helper.ACTIONS.update(self._old[1])

    def run_helper(self):
        t = threading.Thread(target=helper.main, args=([],), daemon=True)
        t.start()
        t.join(5)
        self.assertFalse(t.is_alive(), "Helfer hängt")

    def test_valid_request(self):
        (self.req / "a.json").write_text(json.dumps({"action": "led", "state": "ok"}))
        self.run_helper()
        self.assertEqual(self.calls, [{"action": "led", "state": "ok"}])
        self.assertEqual(list(self.req.iterdir()), [])

    def test_symlink_fifo_big_rejected(self):
        secret = self.d / "secret.json"
        secret.write_text(json.dumps({"action": "led", "state": "off"}))
        (self.req / "link.json").symlink_to(secret)
        os.mkfifo(self.req / "fifo.json")                   # ohne O_NONBLOCK hinge open() hier
        (self.req / "big.json").write_text(json.dumps({"action": "led", "state": "ok", "x": "y" * 5000}))
        self.run_helper()
        self.assertEqual(self.calls, [])
        self.assertTrue(secret.exists())                     # Ziel des Symlinks unberührt
        self.assertEqual(list(self.req.iterdir()), [])       # alles verworfen

    def test_request_dir_symlink_ignored(self):
        other = self.d / "other"
        other.mkdir()
        (other / "x.json").write_text(json.dumps({"action": "led", "state": "ok"}))
        self.req.rmdir()
        self.req.symlink_to(other)
        self.run_helper()
        self.assertEqual(self.calls, [])
        self.assertTrue((other / "x.json").exists())


if __name__ == "__main__":
    unittest.main()
