"""Reine-Python-Kryptografie als Rückfallebene (nur Standardbibliothek).

Zweck: Unit- und Integrationstests ohne installierte Pakete und Simulationsmodus auf dem PC.
Auf dem Gateway wird `cryptography` (OpenSSL) verwendet (crypto.py wählt automatisch).
Nicht konstant in der Laufzeit (Seitenkanäle) – deshalb NICHT für den Produktivbetrieb gedacht;
crypto.py meldet den aktiven Pfad (`BACKEND`) im Systemstatus.

Inhalt: AES-128/256 (nur Verschlüsselung, für CTR-basierte Modi), AES-CCM (RFC 3610),
AES-GCM (NIST SP 800-38D), NIST P-256 (ECDH, ECDSA prüfen/signieren).
Geprüft gegen RFC-/NIST-Vektoren und gegen `cryptography` (tests/test_crypto.py).
"""
from __future__ import annotations

import hashlib
import hmac
import secrets

# ------------------------------------------------------------------------------------------------ AES
def _xtime(a: int) -> int:
    a <<= 1
    return (a ^ 0x11B) & 0xFF if a & 0x100 else a


def _gmul(a: int, b: int) -> int:
    r = 0
    while b:
        if b & 1:
            r ^= a
        a = _xtime(a)
        b >>= 1
    return r


def _make_sbox():
    # S-Box aus Inverser in GF(2^8) + affiner Abbildung berechnet (FIPS-197 Kap. 5.1.1), keine Tabelle abgetippt
    inv = [0] * 256
    for x in range(1, 256):
        for y in range(1, 256):
            if _gmul(x, y) == 1:
                inv[x] = y
                break
    sbox = []
    for x in range(256):
        b = inv[x]
        s = b
        for i in range(1, 5):
            s ^= ((b << i) | (b >> (8 - i))) & 0xFF
        sbox.append(s ^ 0x63)
    return sbox


SBOX = _make_sbox()
_MUL2 = [_gmul(x, 2) for x in range(256)]
_MUL3 = [_gmul(x, 3) for x in range(256)]


class AES:
    """Blockchiffre AES (FIPS-197), nur Verschlüsselungsrichtung."""

    def __init__(self, key: bytes):
        if len(key) not in (16, 32):
            raise ValueError("AES: Schlüssel 16 oder 32 Byte")
        nk = len(key) // 4
        self.nr = nk + 6
        w = [list(key[4 * i:4 * i + 4]) for i in range(nk)]
        rcon = 1
        for i in range(nk, 4 * (self.nr + 1)):
            t = list(w[i - 1])
            if i % nk == 0:
                t = t[1:] + t[:1]
                t = [SBOX[b] for b in t]
                t[0] ^= rcon
                rcon = _xtime(rcon)
            elif nk > 6 and i % nk == 4:
                t = [SBOX[b] for b in t]
            w.append([w[i - nk][j] ^ t[j] for j in range(4)])
        self.rk = [sum(w[4 * r:4 * r + 4], []) for r in range(self.nr + 1)]

    def encrypt_block(self, block: bytes) -> bytes:
        s = [b ^ k for b, k in zip(block, self.rk[0])]
        for r in range(1, self.nr + 1):
            s = [SBOX[b] for b in s]
            # ShiftRows (spaltenweise Ablage: Index = 4*Spalte + Zeile)
            s = [s[(4 * ((c + row) % 4)) + row] for c in range(4) for row in range(4)]
            if r != self.nr:
                t = []
                for c in range(4):
                    a0, a1, a2, a3 = s[4 * c:4 * c + 4]
                    t += [_MUL2[a0] ^ _MUL3[a1] ^ a2 ^ a3, a0 ^ _MUL2[a1] ^ _MUL3[a2] ^ a3,
                          a0 ^ a1 ^ _MUL2[a2] ^ _MUL3[a3], _MUL3[a0] ^ a1 ^ a2 ^ _MUL2[a3]]
                s = t
            s = [b ^ k for b, k in zip(s, self.rk[r])]
        return bytes(s)


def _xor(a: bytes, b: bytes) -> bytes:
    return bytes(x ^ y for x, y in zip(a, b))


class InvalidTag(Exception):
    pass


# ------------------------------------------------------------------------------------------------ CCM
def ccm_encrypt(key: bytes, nonce: bytes, data: bytes, aad: bytes, tag_len: int = 8) -> bytes:
    """RFC 3610: gibt Chiffrat ‖ MIC zurück."""
    tag, ct = _ccm(key, nonce, data, aad, tag_len, encrypt=True)
    return ct + tag


def ccm_decrypt(key: bytes, nonce: bytes, data: bytes, aad: bytes, tag_len: int = 8) -> bytes:
    if len(data) < tag_len:
        raise InvalidTag("zu kurz")
    ct, tag = data[:-tag_len], data[-tag_len:]
    calc, pt = _ccm(key, nonce, ct, aad, tag_len, encrypt=False)
    if not hmac.compare_digest(calc, tag):
        raise InvalidTag("MIC ungültig")
    return pt


def _ccm(key, nonce, data, aad, M, encrypt):
    aes = AES(key)
    L = 15 - len(nonce)
    if not 2 <= L <= 8 or M not in (4, 6, 8, 10, 12, 14, 16):
        raise ValueError("CCM-Parameter")
    ctr = lambda i: bytes([L - 1]) + nonce + i.to_bytes(L, "big")  # noqa: E731
    s0 = aes.encrypt_block(ctr(0))
    out = bytearray()
    for i in range(0, len(data), 16):
        ks = aes.encrypt_block(ctr(i // 16 + 1))
        out += _xor(data[i:i + 16], ks)
    pt = data if encrypt else bytes(out)
    flags = (64 if aad else 0) | (((M - 2) // 2) << 3) | (L - 1)
    b = bytes([flags]) + nonce + len(pt).to_bytes(L, "big")
    x = aes.encrypt_block(b)
    if aad:
        if len(aad) >= 0xFF00:
            raise ValueError("AAD zu lang")
        a = len(aad).to_bytes(2, "big") + aad
        a += b"\x00" * (-len(a) % 16)
        for i in range(0, len(a), 16):
            x = aes.encrypt_block(_xor(x, a[i:i + 16]))
    p = pt + b"\x00" * (-len(pt) % 16)
    for i in range(0, len(p), 16):
        x = aes.encrypt_block(_xor(x, p[i:i + 16]))
    tag = _xor(x[:M], s0[:M])
    return tag, bytes(out)


# ------------------------------------------------------------------------------------------------ GCM
_R = 0xE1 << 120


def _gf_mul(x: int, y: int) -> int:
    z, v = 0, x
    for i in range(127, -1, -1):
        if (y >> i) & 1:
            z ^= v
        v = (v >> 1) ^ _R if v & 1 else v >> 1
    return z


def _ghash(h: int, aad: bytes, ct: bytes) -> int:
    y = 0
    for blob in (aad, ct):
        p = blob + b"\x00" * (-len(blob) % 16)
        for i in range(0, len(p), 16):
            y = _gf_mul(y ^ int.from_bytes(p[i:i + 16], "big"), h)
    lens = (len(aad) * 8).to_bytes(8, "big") + (len(ct) * 8).to_bytes(8, "big")
    return _gf_mul(y ^ int.from_bytes(lens, "big"), h)


def _gcm_ctr(aes, j0: bytes, data: bytes) -> bytes:
    out = bytearray()
    c = int.from_bytes(j0[12:], "big")
    for i in range(0, len(data), 16):
        c = (c + 1) & 0xFFFFFFFF
        out += _xor(data[i:i + 16], aes.encrypt_block(j0[:12] + c.to_bytes(4, "big")))
    return bytes(out)


def gcm_encrypt(key: bytes, iv: bytes, data: bytes, aad: bytes = b"") -> bytes:
    if len(iv) != 12:
        raise ValueError("GCM: IV 12 Byte")
    aes = AES(key)
    h = int.from_bytes(aes.encrypt_block(b"\x00" * 16), "big")
    j0 = iv + b"\x00\x00\x00\x01"
    ct = _gcm_ctr(aes, j0, data)
    s = _ghash(h, aad, ct)
    tag = _xor(s.to_bytes(16, "big"), aes.encrypt_block(j0))
    return ct + tag


def gcm_decrypt(key: bytes, iv: bytes, data: bytes, aad: bytes = b"") -> bytes:
    if len(iv) != 12 or len(data) < 16:
        raise InvalidTag("GCM-Eingabe")
    aes = AES(key)
    ct, tag = data[:-16], data[-16:]
    h = int.from_bytes(aes.encrypt_block(b"\x00" * 16), "big")
    j0 = iv + b"\x00\x00\x00\x01"
    calc = _xor(_ghash(h, aad, ct).to_bytes(16, "big"), aes.encrypt_block(j0))
    if not hmac.compare_digest(calc, tag):
        raise InvalidTag("GCM-Tag ungültig")
    return _gcm_ctr(aes, j0, ct)


# ------------------------------------------------------------------------------------------------ P-256
P = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
A = P - 3
B = 0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B
GX = 0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296
GY = 0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5
N = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
G = (GX, GY)


def on_curve(pt) -> bool:
    if pt is None:
        return False
    x, y = pt
    return 0 <= x < P and 0 <= y < P and (y * y - (x * x * x + A * x + B)) % P == 0


def _add(p1, p2):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2:
        if (y1 + y2) % P == 0:
            return None
        lam = (3 * x1 * x1 + A) * pow(2 * y1, -1, P) % P
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, P) % P
    x3 = (lam * lam - x1 - x2) % P
    return x3, (lam * (x1 - x3) - y1) % P


def mul(k: int, pt=G):
    r = None
    q = pt
    while k:
        if k & 1:
            r = _add(r, q)
        q = _add(q, q)
        k >>= 1
    return r


def point_from_raw(raw64: bytes):
    if len(raw64) == 65 and raw64[0] == 4:
        raw64 = raw64[1:]
    if len(raw64) != 64:
        raise ValueError("Punkt: 64 Byte X‖Y erwartet")
    pt = (int.from_bytes(raw64[:32], "big"), int.from_bytes(raw64[32:], "big"))
    if not on_curve(pt):
        raise ValueError("Punkt liegt nicht auf P-256")
    return pt


def point_to_raw(pt) -> bytes:
    return pt[0].to_bytes(32, "big") + pt[1].to_bytes(32, "big")


def ecdh_keypair():
    d = secrets.randbelow(N - 1) + 1
    return d, point_to_raw(mul(d))


def ecdh_shared(d: int, peer_raw64: bytes) -> bytes:
    q = point_from_raw(peer_raw64)
    s = mul(d, q)
    if s is None:
        raise ValueError("ECDH: Punkt im Unendlichen")
    return s[0].to_bytes(32, "big")


def ecdsa_verify(pub_raw64: bytes, digest: bytes, r: int, s: int) -> bool:
    if not (1 <= r < N and 1 <= s < N):
        return False
    q = point_from_raw(pub_raw64)
    e = int.from_bytes(digest[:32], "big")
    w = pow(s, -1, N)
    x = _add(mul(e * w % N), mul(r * w % N, q))
    return x is not None and x[0] % N == r


def ecdsa_sign(d: int, digest: bytes):
    """Nur für Werkzeuge/Tests (zufälliges k aus secrets)."""
    e = int.from_bytes(digest[:32], "big")
    while True:
        k = secrets.randbelow(N - 1) + 1
        r = mul(k)[0] % N
        if not r:
            continue
        s = pow(k, -1, N) * (e + r * d) % N
        if s:
            return r, s


def sha256(b: bytes) -> bytes:
    return hashlib.sha256(b).digest()
