#!/usr/bin/env python3
"""Angriffstest Kopplung v2 (Befund F-K1, docs/reviews/phase4_sicherheit_kragen_firmware.md).

Nachgebildet wird der aktive Mittelsmann (MITM) aus dem Pruefskript des Sicherheits-Agenten (`mitm_sas.py`):
der Angreifer steht zwischen Gateway und Sensor, koppelt mit beiden und versucht, dass beide dieselbe Farbfolge
(SAS) zeigen. Er nutzt jede Freiheit, die ihm das Protokoll laesst:

  - v1 (ohne Commitment): er kennt die Sensor-SAS, bevor er seine PAIR_RSP an das Gateway festlegt, und schleift
    `s_nonce`, bis die Gateway-SAS passt  -> Erfolg ~100 % (Gegenprobe, muss erfolgreich sein).
  - v2 (Commitment/Reveal): zum Gateway muss er PAIR_RSP senden, BEVOR das Gateway gw_nonce offenlegt; zum Sensor
    muss er sein Commitment senden, BEVOR er s_nonce kennt. Er darf trotzdem beliebig viele Kandidaten pruefen,
    aber nur EINEN je Kopplung festlegen. Erfolg muss <= 1 % sein (theoretisch 1/243 = 0.41 %).

Die Schluesselpaare sind fest (ECDH beeinflusst die SAS nur ueber das Transkript, nicht ueber Zufall); variiert
werden alle Nonces wie im echten Ablauf.
"""
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fluidi_proto as P  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402

RUNS = 10000
ADDR = bytes.fromhex("CDAB12B06F80")
FW = b"\x00\x01\x00\x00"


class Keys:
    gw = P.pub64(ec.derive_private_key(11, ec.SECP256R1()))
    sensor = P.pub64(ec.derive_private_key(22, ec.SECP256R1()))
    m1 = P.pub64(ec.derive_private_key(33, ec.SECP256R1()))   # Angreifer -> Sensor (spielt Gateway)
    m2 = P.pub64(ec.derive_private_key(44, ec.SECP256R1()))   # Angreifer -> Gateway (spielt Sensor)


def run_v2(rng: random.Random) -> bool:
    """Ein Kopplungsversuch v2 mit bestmoeglichem Angreifer. True = MITM unentdeckt."""
    gw_id = rng.randbytes(8)
    # Seite Angreifer <-> Sensor: Angreifer legt gw_nonce' per Commitment fest, bevor er s_nonce sieht
    m_nonce = rng.randbytes(16)
    req_m = P.pair_req_payload(gw_id, Keys.m1, m_nonce)
    s_nonce = rng.randbytes(16)                                   # Sensor waehlt zufaellig nach dem Commitment
    rsp_s = P.pair_rsp_payload(ADDR, 0x0B, FW, Keys.sensor, s_nonce)
    assert P.check_reveal(req_m, m_nonce)                         # Sensor prueft die Offenlegung
    sas_sensor = P.sas(P.transcript(req_m, rsp_s, m_nonce))
    # Seite Gateway <-> Angreifer: Gateway hat gw_nonce festgelegt (Commitment), Angreifer kennt nur C
    gw_nonce = rng.randbytes(16)
    req_gw = P.pair_req_payload(gw_id, Keys.gw, gw_nonce)
    # Der Angreifer kann beliebig viele Kandidaten fuer seine PAIR_RSP erzeugen, aber die Gateway-SAS haengt von
    # gw_nonce ab, das er noch nicht kennt: keine Wahl ist besser als eine andere. Er muss genau eine senden.
    rsp_m = P.pair_rsp_payload(ADDR, 0x0B, FW, Keys.m2, rng.randbytes(16))
    # Erst jetzt legt das Gateway gw_nonce offen; ein Austausch der PAIR_RSP ist nicht mehr moeglich
    sas_gw = P.sas(P.transcript(req_gw, rsp_m, gw_nonce))
    return sas_gw == sas_sensor


def run_v1(rng: random.Random) -> bool:
    """Gegenprobe: Protokoll v1 ohne Commitment (Transkript REQ|RSP, gw_nonce offen in PAIR_REQ)."""
    import hashlib
    gw_id = rng.randbytes(8)
    req_m = gw_id + Keys.m1 + rng.randbytes(16)
    rsp_s = P.pair_rsp_payload(ADDR, 0x0B, FW, Keys.sensor, rng.randbytes(16))
    target = P.sas(hashlib.sha256(req_m + rsp_s).digest())
    req_gw = gw_id + Keys.gw + rng.randbytes(16)
    for _ in range(5000):                                         # schleifen bis die Gateway-SAS passt
        rsp_m = P.pair_rsp_payload(ADDR, 0x0B, FW, Keys.m2, rng.randbytes(16))
        if P.sas(hashlib.sha256(req_gw + rsp_m).digest()) == target:
            return True
    return False


class TestMitm(unittest.TestCase):
    def test_v1_attack_succeeds(self):
        rng = random.Random(1)
        ok = sum(run_v1(rng) for _ in range(200))
        self.assertGreaterEqual(ok, 198)          # bestaetigt den Befund F-K1

    def test_v2_attack_at_most_1_percent(self):
        rng = random.Random(2026)
        ok = sum(run_v2(rng) for _ in range(RUNS))
        rate = ok / RUNS
        print("\n[mitm] v2: %d von %d Angriffen unentdeckt = %.2f %% (Theorie 1/243 = 0.41 %%)" % (ok, RUNS, 100 * rate))
        self.assertLessEqual(rate, 0.01)

    def test_reveal_mismatch_detected(self):
        req = P.pair_req_payload(b"\x01" * 8, Keys.gw, b"\x02" * 16)
        self.assertTrue(P.check_reveal(req, b"\x02" * 16))
        self.assertFalse(P.check_reveal(req, b"\x03" * 16))


if __name__ == "__main__":
    unittest.main()
