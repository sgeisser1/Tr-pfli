#!/usr/bin/env python3
"""fluidi – Fingerabdruck eines MCUboot-Signierschluessels: erste 8 Byte (16 Hex) von SHA-256 des oeffentlichen
Schluessels im DER-Format (SubjectPublicKeyInfo) – genau diese 91 Byte baut `imgtool getpub` in MCUboot ein,
deshalb kann scripts/flash_sensor.py denselben Fingerabdruck aus dem Werks-Hex berechnen (Befund F-W1)."""
import hashlib
import sys

from cryptography.hazmat.primitives import serialization


def pub_der(path: str) -> bytes:
    data = open(path, "rb").read()
    key = serialization.load_pem_private_key(data, None).public_key() if b"PRIVATE" in data \
        else serialization.load_pem_public_key(data)
    return key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)


def fingerprint_der(der: bytes) -> str:
    return hashlib.sha256(der).hexdigest()[:16]


if __name__ == "__main__":
    print(fingerprint_der(pub_der(sys.argv[1])))
