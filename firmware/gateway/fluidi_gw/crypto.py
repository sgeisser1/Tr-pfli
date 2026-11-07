"""Kryptografie-Fassade des Gateways (PROTOCOL.md Kap. 4, ARCHITECTURE.md Kap. 8).

Bevorzugt `cryptography` (auf dem Pi: Debian-Paket python3-cryptography), sonst reine Python-Umsetzung
aus _pure.py (Tests/Simulation). Umgebungsvariable FLUIDI_CRYPTO=pure erzwingt die Rückfallebene.

Verfahren: HKDF-SHA-256 (RFC 5869), HMAC-SHA-256, AES-128-CCM mit 8-Byte-MIC (RFC 3610),
ECDH P-256 (SEC1, X‖Y big-endian ohne 0x04), ECDSA P-256 mit SHA-256 (MCUboot-Signatur),
AES-256-GCM + PBKDF2-HMAC-SHA256 (Backup).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re

from . import _pure

InvalidTag = _pure.InvalidTag

_C = None
if os.environ.get("FLUIDI_CRYPTO", "").lower() != "pure":
    try:  # optional
        from cryptography.exceptions import InvalidSignature as _InvSig, InvalidTag as _InvTag
        from cryptography.hazmat.primitives import hashes as _hashes
        from cryptography.hazmat.primitives.asymmetric import ec as _ec
        from cryptography.hazmat.primitives.asymmetric.utils import Prehashed as _Prehashed
        from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature as _dec_sig
        from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature as _enc_sig
        from cryptography.hazmat.primitives.ciphers.aead import AESCCM as _AESCCM, AESGCM as _AESGCM
        _C = True
    except Exception:  # pragma: no cover - abhängig von der Umgebung
        _C = None

BACKEND = "cryptography" if _C else "pure-python"


# ------------------------------------------------------------------------------------------------ Hash/KDF
def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()


def hmac_sha256(key: bytes, msg: bytes) -> bytes:
    return hmac.new(key, msg, hashlib.sha256).digest()


def hkdf_sha256(ikm: bytes, salt: bytes, info: bytes, length: int) -> bytes:
    """RFC 5869 (Extract + Expand)."""
    prk = hmac_sha256(salt or b"\x00" * 32, ikm)
    out, t, i = b"", b"", 1
    while len(out) < length:
        t = hmac_sha256(prk, t + info + bytes([i]))
        out += t
        i += 1
    return out[:length]


def pbkdf2(password: bytes, salt: bytes, iterations: int, length: int = 32) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password, salt, iterations, length)


# ------------------------------------------------------------------------------------------------ AES-CCM
def ccm_encrypt(key: bytes, nonce: bytes, plaintext: bytes, aad: bytes, tag_len: int = 8) -> bytes:
    if _C:
        return _AESCCM(key, tag_length=tag_len).encrypt(nonce, plaintext, aad)
    return _pure.ccm_encrypt(key, nonce, plaintext, aad, tag_len)


def ccm_decrypt(key: bytes, nonce: bytes, data: bytes, aad: bytes, tag_len: int = 8) -> bytes:
    if _C:
        try:
            return _AESCCM(key, tag_length=tag_len).decrypt(nonce, data, aad)
        except _InvTag as e:
            raise InvalidTag("MIC ungültig") from e
    return _pure.ccm_decrypt(key, nonce, data, aad, tag_len)


# ------------------------------------------------------------------------------------------------ AES-GCM
def gcm_encrypt(key: bytes, iv: bytes, plaintext: bytes, aad: bytes = b"") -> bytes:
    if _C:
        return _AESGCM(key).encrypt(iv, plaintext, aad)
    return _pure.gcm_encrypt(key, iv, plaintext, aad)


def gcm_decrypt(key: bytes, iv: bytes, data: bytes, aad: bytes = b"") -> bytes:
    if _C:
        try:
            return _AESGCM(key).decrypt(iv, data, aad)
        except _InvTag as e:
            raise InvalidTag("GCM-Tag ungültig") from e
    return _pure.gcm_decrypt(key, iv, data, aad)


# ------------------------------------------------------------------------------------------------ ECDH
class EcdhKey:
    """Einmal-Schlüsselpaar für eine Kopplung (PROTOCOL 4.2)."""

    def __init__(self):
        if _C:
            self._k = _ec.generate_private_key(_ec.SECP256R1())
            n = self._k.public_key().public_numbers()
            self.public_raw = n.x.to_bytes(32, "big") + n.y.to_bytes(32, "big")
        else:
            self._d, self.public_raw = _pure.ecdh_keypair()

    def shared(self, peer_raw64: bytes) -> bytes:
        """x-Koordinate (32 Byte). Prüft, dass der Gegenpunkt auf der Kurve liegt."""
        _pure.point_from_raw(peer_raw64)  # Kurvenprüfung immer (ungültige Punkte -> ValueError)
        if _C:
            pub = _ec.EllipticCurvePublicNumbers(int.from_bytes(peer_raw64[:32], "big"),
                                                 int.from_bytes(peer_raw64[32:], "big"),
                                                 _ec.SECP256R1()).public_key()
            return self._k.exchange(_ec.ECDH(), pub)
        return _pure.ecdh_shared(self._d, peer_raw64)


# ------------------------------------------------------------------------------------------------ ECDSA
def der_to_rs(sig: bytes):
    """ASN.1 DER SEQUENCE{INTEGER r, INTEGER s} -> (r, s)."""
    def _len(b, i):
        n = b[i]
        if n < 0x80:
            return n, i + 1
        k = n & 0x7F
        return int.from_bytes(b[i + 1:i + 1 + k], "big"), i + 1 + k
    if not sig or sig[0] != 0x30:
        raise ValueError("Signatur: kein DER")
    total, i = _len(sig, 1)
    if i + total != len(sig):
        raise ValueError("Signatur: Länge")
    out = []
    for _ in range(2):
        if sig[i] != 0x02:
            raise ValueError("Signatur: INTEGER erwartet")
        n, i = _len(sig, i + 1)
        out.append(int.from_bytes(sig[i:i + n], "big"))
        i += n
    if i != len(sig):
        raise ValueError("Signatur: Restbytes")
    return out[0], out[1]


def rs_to_der(r: int, s: int) -> bytes:
    def _int(v):
        b = v.to_bytes((v.bit_length() + 8) // 8, "big")
        return b"\x02" + bytes([len(b)]) + b
    body = _int(r) + _int(s)
    return b"\x30" + bytes([len(body)]) + body


def load_public_key(pem_or_raw) -> bytes:
    """PEM (SubjectPublicKeyInfo, P-256) oder 64/65 Byte roh -> 64 Byte X‖Y (Kurve geprüft)."""
    if isinstance(pem_or_raw, str):
        pem_or_raw = pem_or_raw.encode()
    data = pem_or_raw
    if b"-----BEGIN" in data:
        m = re.search(rb"-----BEGIN PUBLIC KEY-----(.*?)-----END PUBLIC KEY-----", data, re.S)
        if not m:
            raise ValueError("PEM: PUBLIC KEY erwartet")
        der = base64.b64decode(b"".join(m.group(1).split()))
        # SPKI für P-256 endet mit BIT STRING 00 04 X Y (65 Byte Punkt)
        if b"\x2a\x86\x48\xce\x3d\x03\x01\x07" not in der:  # OID prime256v1
            raise ValueError("Schlüssel ist nicht P-256")
        data = der[-65:]
    pt = _pure.point_from_raw(data)
    return _pure.point_to_raw(pt)


def ecdsa_verify_digest(pub_raw64: bytes, digest: bytes, der_sig: bytes) -> bool:
    """ECDSA-P-256 über einen fertigen SHA-256-Hash (so signiert imgtool die MCUboot-Images)."""
    try:
        r, s = der_to_rs(der_sig)
    except (ValueError, IndexError):
        return False
    if _C:
        try:
            pub = _ec.EllipticCurvePublicNumbers(int.from_bytes(pub_raw64[:32], "big"),
                                                 int.from_bytes(pub_raw64[32:], "big"),
                                                 _ec.SECP256R1()).public_key()
            pub.verify(_enc_sig(r, s), digest, _ec.ECDSA(_Prehashed(_hashes.SHA256())))
            return True
        except (_InvSig, ValueError):
            return False
    try:
        return _pure.ecdsa_verify(pub_raw64, digest, r, s)
    except ValueError:
        return False


class SigningKey:
    """Nur für Werkzeuge und Tests (Testabbilder signieren). Produktivschlüssel bleiben offline (REQ-FW-04)."""

    def __init__(self, d: int | None = None):
        import secrets
        self.d = d or (secrets.randbelow(_pure.N - 1) + 1)
        self.public_raw = _pure.point_to_raw(_pure.mul(self.d))

    def sign_digest(self, digest: bytes) -> bytes:
        r, s = _pure.ecdsa_sign(self.d, digest)
        return rs_to_der(r, s)

    def public_pem(self) -> str:
        spki = bytes.fromhex("3059301306072a8648ce3d020106082a8648ce3d030107034200") + b"\x04" + self.public_raw
        b64 = base64.b64encode(spki).decode()
        return "-----BEGIN PUBLIC KEY-----\n" + "\n".join(b64[i:i + 64] for i in range(0, len(b64), 64)) + "\n-----END PUBLIC KEY-----\n"


def random_bytes(n: int) -> bytes:
    return os.urandom(n)
