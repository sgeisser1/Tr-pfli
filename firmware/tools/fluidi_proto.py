#!/usr/bin/env python3
"""fluidi – Python-Referenz des Funkprotokolls (firmware/PROTOCOL.md 0.2, Protokollversion 2).

Unabhaengige Implementierung mit der Bibliothek `cryptography` (HKDF, HMAC, AES-CCM, ECDH P-256).
Dient (1) als Gegenprobe fuer die Unit-Tests der Sensor-Firmware (firmware/sensor/tests) und
(2) als Vorlage fuer den Gateway-Client (Software-Agent).

Praezisierung Welle 2 (ANNAHME bis Pruefung Software-Agent): sensor_addr wird LSB-zuerst uebertragen
(BLE-Link-Layer-Reihenfolge).
"""
from __future__ import annotations

import hashlib
import hmac
import struct
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.ciphers.aead import AESCCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

PROTO = 2
FT_HELLO, FT_HELLO_RSP, FT_SECURE, FT_PAIR, FT_ERROR = 0x0, 0x1, 0x2, 0x3, 0xF
PAIR_REQ, PAIR_RSP, PAIR_REVEAL, PAIR_CONFIRM_S, PAIR_CONFIRM_G, PAIR_DONE = 1, 2, 3, 4, 5, 6
DIR_G2S, DIR_S2G = 0, 1
MIC_LEN = 8
SAS_COLORS = ("rot", "gruen", "gelb")


def vt(t: int) -> int:
    return (PROTO << 4) | t


def hkdf(ikm: bytes, salt: bytes, info: bytes, length: int) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=length, salt=salt, info=info).derive(ikm)


def device_name(addr_le: bytes) -> str:
    return "fluidi-%02X%02X" % (addr_le[1], addr_le[0])


def gw_hint(gateway_id: bytes) -> bytes:
    return hashlib.sha256(gateway_id).digest()[:2]


def adv_data(addr_le: bytes, state: int, vbat_mv: int, seq_last: int, hint: bytes) -> bytes:
    v = max(0, min(255, (vbat_mv - 2000) // 10))
    msd = struct.pack("<HBBBBBH", 0xFFFF, 0x66, 0x6C, 1, state, v, seq_last & 0xFFFF) + hint
    return bytes([2, 1, 6, 12, 9]) + device_name(addr_le).encode() + bytes([12, 0xFF]) + msd


def parse_adv(data: bytes) -> dict:
    """AD-Strukturen zerlegen; liefert name und Herstellerdaten (Kap. 2.4)."""
    out, i = {}, 0
    while i < len(data) and data[i]:
        ln, typ = data[i], data[i + 1]
        val = data[i + 2:i + 1 + ln]
        if typ == 0x09:
            out["name"] = val.decode()
        elif typ == 0xFF and len(val) == 11 and val[2:4] == b"fl":
            cid, _, _, fmt, st, v, seq = struct.unpack("<HBBBBBH", val[:9])
            out.update(company=cid, adv_fmt=fmt, state=st, vbat_mv=2000 + 10 * v, seq_lo=seq, gw_hint=val[9:11])
        i += ln + 1
    return out


# ---------------- Kopplung (Kap. 4.2, v2 mit Commitment/Reveal) ----------------
def commit(gateway_id: bytes, gw_pub64: bytes, gw_nonce16: bytes) -> bytes:
    """C = SHA-256("fluidi-commit" | gateway_id | gw_pub | gw_nonce) – in PAIR_REQ statt gw_nonce."""
    return hashlib.sha256(b"fluidi-commit" + gateway_id + gw_pub64 + gw_nonce16).digest()


def pair_req_payload(gateway_id: bytes, gw_pub64: bytes, gw_nonce16: bytes) -> bytes:
    """PAIR_REQ-Nutzlast (104 Byte): gateway_id . gw_pub . commit (gw_nonce bleibt geheim bis PAIR_REVEAL)."""
    return gateway_id + gw_pub64 + commit(gateway_id, gw_pub64, gw_nonce16)


def check_reveal(req: bytes, gw_nonce16: bytes) -> bool:
    return hmac.compare_digest(commit(req[:8], req[8:72], gw_nonce16), req[72:104])


def pair_rsp_payload(addr_le: bytes, hw_rev: int, fw_ver4: bytes, s_pub64: bytes, s_nonce16: bytes) -> bytes:
    return addr_le + bytes([hw_rev]) + fw_ver4 + s_pub64 + s_nonce16


def transcript(req: bytes, rsp: bytes, reveal: bytes) -> bytes:
    """SHA-256(payload(PAIR_REQ) | payload(PAIR_RSP) | payload(PAIR_REVEAL)); payload = ohne vt und pmsg."""
    return hashlib.sha256(req + rsp + reveal).digest()


def pair_keys(z: bytes, gw_nonce: bytes, s_nonce: bytes, gateway_id: bytes, addr_le: bytes) -> tuple[bytes, bytes]:
    okm = hkdf(z, gw_nonce + s_nonce, b"fluidi-pair-v2" + gateway_id + addr_le, 32)
    return okm[:16], okm[16:]


def sas(tr: bytes) -> list[int]:
    h = hashlib.sha256(b"fluidi-sas" + tr).digest()
    n = (h[0] | (h[1] << 8)) % 243
    d = []
    for _ in range(5):
        d.append(n % 3)
        n //= 3
    return d[::-1]


def confirm_mac(k_conf: bytes, who: str, tr: bytes) -> bytes:
    return hmac.new(k_conf, who.encode() + tr, hashlib.sha256).digest()[:16]


def pub64(key: ec.EllipticCurvePrivateKey) -> bytes:
    n = key.public_key().public_numbers()
    return n.x.to_bytes(32, "big") + n.y.to_bytes(32, "big")


def ecdh(priv: ec.EllipticCurvePrivateKey, peer64: bytes) -> bytes:
    peer = ec.EllipticCurvePublicNumbers(int.from_bytes(peer64[:32], "big"), int.from_bytes(peer64[32:], "big"),
                                         ec.SECP256R1()).public_key()
    return priv.exchange(ec.ECDH(), peer)


# ---------------- Sitzung (Kap. 4.3/4.4) ----------------
def session_key(k_link: bytes, gw_nonce8: bytes, s_nonce8: bytes) -> bytes:
    return hkdf(k_link, gw_nonce8 + s_nonce8, b"fluidi-sess-v2", 16)


def nonce(direction: int, ctr: int, addr_le: bytes) -> bytes:
    return bytes([direction]) + struct.pack("<I", ctr) + addr_le + b"\x00\x00"


def seal(k_s: bytes, direction: int, ctr: int, addr_le: bytes, msg: int, rid: int, payload: bytes) -> bytes:
    head = bytes([vt(FT_SECURE)]) + struct.pack("<I", ctr)
    ct = AESCCM(k_s, tag_length=MIC_LEN).encrypt(nonce(direction, ctr, addr_le), bytes([msg, rid]) + payload, head)
    return head + ct


def open_(k_s: bytes, direction: int, addr_le: bytes, frame: bytes) -> tuple[int, int, int, bytes]:
    if frame[0] != vt(FT_SECURE):
        raise ValueError("kein SECURE-Frame")
    ctr = struct.unpack("<I", frame[1:5])[0]
    pt = AESCCM(k_s, tag_length=MIC_LEN).decrypt(nonce(direction, ctr, addr_le), frame[5:], frame[:5])
    return ctr, pt[0], pt[1], pt[2:]


@dataclass
class Record:
    seq: int
    boot_id: int
    uptime_s: int
    c_probe: int
    c_diag: int
    temp: int
    vbat_mv: int
    cause: int
    flags: int

    FMT = "<IHIHHhHBB"

    @classmethod
    def decode(cls, b: bytes) -> "Record":
        return cls(*struct.unpack(cls.FMT, b[:20]))

    def encode(self) -> bytes:
        return struct.pack(self.FMT, self.seq, self.boot_id, self.uptime_s, self.c_probe, self.c_diag, self.temp,
                           self.vbat_mv, self.cause, self.flags)


if __name__ == "__main__":
    a = bytes.fromhex("CDAB12B06F80")
    print(device_name(a), adv_data(a, 0x05, 2950, 1234, b"\x12\x34").hex())
