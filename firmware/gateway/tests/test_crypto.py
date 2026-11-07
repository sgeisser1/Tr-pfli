"""Krypto-Grundlagen gegen veröffentlichte Testvektoren (PROTOCOL Kap. 14) und – falls installiert – gegen
`cryptography` (OpenSSL). Prüft beide Pfade: reine Python-Rückfallebene (_pure) und Fassade (crypto)."""
import os
import unittest

import helpers  # noqa: F401  (Pfad)
from fluidi_gw import _pure, climate, crypto

try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives.ciphers.aead import AESCCM, AESGCM
    HAVE_C = True
except ImportError:  # pragma: no cover
    HAVE_C = False


class Vectors(unittest.TestCase):
    def test_aes_fips197_c1(self):
        # FIPS-197 Anhang C.1 (AES-128)
        k = bytes(range(16))
        pt = bytes.fromhex("00112233445566778899aabbccddeeff")
        self.assertEqual(_pure.AES(k).encrypt_block(pt).hex(), "69c4e0d86a7b0430d8cdb78070b4c55a")

    def test_aes256_fips197_c3(self):
        k = bytes(range(32))
        pt = bytes.fromhex("00112233445566778899aabbccddeeff")
        self.assertEqual(_pure.AES(k).encrypt_block(pt).hex(), "8ea2b7ca516745bfeafc49904b496089")

    def test_hkdf_rfc5869_tc1(self):
        okm = crypto.hkdf_sha256(bytes([0x0B] * 22), bytes(range(13)), bytes(range(0xF0, 0xFA)), 42)
        self.assertEqual(okm.hex(), "3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf34007208d5b887185865")

    def test_gcm_nist_tc2(self):
        # GCM-Spezifikation (McGrew/Viega) Testfall 2: K=0, P=0^128, IV=0^96
        out = _pure.gcm_encrypt(bytes(16), bytes(12), bytes(16))
        self.assertEqual(out[:16].hex(), "0388dace60b6a392f328c2b971b2fe78")
        self.assertEqual(out[16:].hex(), "ab6e47d42cec13bdf53a67b21257bddf")

    def test_sht4x_crc_example(self):
        # Datenblatt SHT4x V7.3 S. 11 Tab. 7: CRC(0xBEEF) = 0x92
        self.assertEqual(climate.crc8(b"\xbe\xef"), 0x92)
        t, rh = climate.convert(bytes([0x66, 0x66, climate.crc8(b"\x66\x66"), 0x80, 0x00, climate.crc8(b"\x80\x00")]))
        self.assertAlmostEqual(t, -45 + 175 * 0x6666 / 65535, places=2)
        self.assertAlmostEqual(rh, round(-6 + 125 * 0x8000 / 65535, 1), places=1)
        with self.assertRaises(ValueError):
            climate.convert(b"\x66\x66\x00\x80\x00\x00")

    def test_ccm_roundtrip_and_tamper(self):
        k, n = os.urandom(16), os.urandom(13)
        ct = _pure.ccm_encrypt(k, n, b"hallo fluidi", b"aad", 8)
        self.assertEqual(_pure.ccm_decrypt(k, n, ct, b"aad", 8), b"hallo fluidi")
        bad = bytearray(ct)
        bad[0] ^= 1
        with self.assertRaises(_pure.InvalidTag):
            _pure.ccm_decrypt(k, n, bytes(bad), b"aad", 8)
        with self.assertRaises(_pure.InvalidTag):
            _pure.ccm_decrypt(k, n, ct, b"AAD", 8)

    def test_p256_generator_order(self):
        self.assertTrue(_pure.on_curve(_pure.G))
        self.assertIsNone(_pure.mul(_pure.N))
        with self.assertRaises(ValueError):
            _pure.point_from_raw(bytes(64))  # (0,0) liegt nicht auf der Kurve

    def test_ecdsa_der(self):
        k = crypto.SigningKey()
        dg = crypto.sha256(b"image")
        sig = k.sign_digest(dg)
        self.assertTrue(crypto.ecdsa_verify_digest(k.public_raw, dg, sig))
        self.assertFalse(crypto.ecdsa_verify_digest(k.public_raw, crypto.sha256(b"other"), sig))
        self.assertFalse(crypto.ecdsa_verify_digest(k.public_raw, dg, sig[:-1]))
        self.assertEqual(crypto.load_public_key(k.public_pem()), k.public_raw)


@unittest.skipUnless(HAVE_C, "cryptography nicht installiert")
class AgainstOpenSSL(unittest.TestCase):
    def test_aes_ccm_gcm(self):
        for _ in range(5):
            k, k32, n, iv = os.urandom(16), os.urandom(32), os.urandom(13), os.urandom(12)
            pt, aad = os.urandom(os.urandom(1)[0]), os.urandom(5)
            self.assertEqual(_pure.AES(k).encrypt_block(pt[:16].ljust(16, b"\0")),
                             Cipher(algorithms.AES(k), modes.ECB()).encryptor().update(pt[:16].ljust(16, b"\0")))
            self.assertEqual(_pure.ccm_encrypt(k, n, pt, aad, 8), AESCCM(k, tag_length=8).encrypt(n, pt, aad))
            self.assertEqual(_pure.gcm_encrypt(k32, iv, pt, aad), AESGCM(k32).encrypt(iv, pt, aad))

    def test_ecdh_cross(self):
        a = crypto.EcdhKey()  # cryptography
        d, pub = _pure.ecdh_keypair()
        self.assertEqual(a.shared(pub), _pure.ecdh_shared(d, a.public_raw))


if __name__ == "__main__":
    unittest.main()
