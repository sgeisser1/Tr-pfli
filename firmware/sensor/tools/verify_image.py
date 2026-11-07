#!/usr/bin/env python3
"""fluidi – signiertes MCUboot-Image unabhaengig pruefen (Kopf, SHA-256-TLV, ECDSA-P256-Signatur,
Sicherheitszaehler). Ersatz fuer `imgtool verify` (imgtool 2.2.0rc1: KeyError 'SIG_PURE').
Gleiche Pruefung soll das Gateway vor dem Verteilen ausfuehren (PROTOCOL.md 9.1).

Format: MCUboot docs/design.md (image_header 32 Byte, TLV-Info 0x6908 geschuetzt / 0x6907 ungeschuetzt).
"""
import argparse
import hashlib
import struct
import sys

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

IMAGE_MAGIC = 0x96F3B83D
TLV_INFO, TLV_PROT_INFO = 0x6907, 0x6908
T_SHA256, T_ECDSA_SIG, T_SEC_CNT, T_KEYHASH = 0x10, 0x22, 0x50, 0x01


def parse(data):
    magic, load, hdr_sz, prot_sz, img_sz, flags, vmaj, vmin, vrev, vbuild = struct.unpack_from("<IIHHIIBBHI", data, 0)
    if magic != IMAGE_MAGIC:
        raise ValueError("kein MCUboot-Image (magic %#x)" % magic)
    off = hdr_sz + img_sz
    tlvs, prot_end = [], off
    if prot_sz:
        m, tot = struct.unpack_from("<HH", data, off)
        if m != TLV_PROT_INFO or tot != prot_sz:
            raise ValueError("geschuetzter TLV-Bereich fehlerhaft")
        p = off + 4
        while p < off + tot:
            t, ln = struct.unpack_from("<HH", data, p)
            tlvs.append((t, data[p + 4:p + 4 + ln], True))
            p += 4 + ln
        prot_end = off + tot
    m, tot = struct.unpack_from("<HH", data, prot_end)
    if m != TLV_INFO:
        raise ValueError("TLV-Info fehlt")
    p = prot_end + 4
    while p < prot_end + tot:
        t, ln = struct.unpack_from("<HH", data, p)
        tlvs.append((t, data[p + 4:p + 4 + ln], False))
        p += 4 + ln
    return dict(hdr_sz=hdr_sz, img_sz=img_sz, flags=flags, version="%d.%d.%d+%d" % (vmaj, vmin, vrev, vbuild),
                payload=data[:prot_end], tlvs=tlvs)


def verify(path, keyfile):
    data = open(path, "rb").read()
    im = parse(data)
    key = serialization.load_pem_private_key(open(keyfile, "rb").read(), None).public_key() \
        if b"PRIVATE" in open(keyfile, "rb").read() else serialization.load_pem_public_key(open(keyfile, "rb").read())
    t = {k: v for k, v, _ in im["tlvs"]}
    if t.get(T_SHA256) != hashlib.sha256(im["payload"]).digest():
        raise ValueError("SHA-256 stimmt nicht")
    pub_der = key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    if T_KEYHASH in t and t[T_KEYHASH] != hashlib.sha256(pub_der).digest():
        raise ValueError("Schluessel-Hash passt nicht zum Schluessel")
    key.verify(t[T_ECDSA_SIG], im["payload"], ec.ECDSA(hashes.SHA256()))   # wirft InvalidSignature
    sc = struct.unpack("<I", t[T_SEC_CNT])[0] if T_SEC_CNT in t else None
    return im["version"], im["img_sz"], sc


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--key", required=True, help="PEM (privat oder oeffentlich)")
    a = ap.parse_args()
    try:
        v, n, sc = verify(a.image, a.key)
    except Exception as e:  # noqa: BLE001
        print("[verify] FEHLER:", type(e).__name__, e)
        sys.exit(1)
    print("[verify] ok: Version %s, Image %d Byte, Sicherheitszaehler %s, Signatur ECDSA-P256 gueltig" % (v, n, sc))
