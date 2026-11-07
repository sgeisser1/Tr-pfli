"""Einmal-CA für HTTPS im LAN (REQ-APP-02, REQ-SAF-NET-04, ARCHITECTURE Kap. 9).

`python3 -m fluidi_gw pki-init` (läuft bei der Installation auf dem Pi):
  1. Gateway-Schlüssel (EC P-256) erzeugen, nur für den Dienstbenutzer lesbar (0600).
  2. CA-Schlüssel NUR IM ARBEITSSPEICHER erzeugen; CA-Zertifikat mit kritischer Name Constraint
     `permitted DNS = fluidi.local` und BasicConstraints CA, pathlen 0.
  3. Server-Zertifikat für fluidi.local (SAN), ≤ 825 Tage, EKU serverAuth, signiert.
  4. CA-Schlüssel verwerfen (wird nie gespeichert) -> niemand kann später weitere Zertifikate ausstellen.
  Auf dem Handy wird nur `ca.crt` installiert; wegen der Name Constraint gilt sie für keine andere Adresse.
Erneuern: pki-init nochmals ausführen (neue CA, neue Installation auf den Geräten nötig) – Warnung 60 Tage vorher.

Benötigt `cryptography` (Pi: Debian-Paket python3-cryptography).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import os
import ssl
from pathlib import Path

VALID_DAYS = 825


def init(tls_dir: Path, hostname="fluidi.local", days=VALID_DAYS, force=False):
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

    tls_dir = Path(tls_dir)
    tls_dir.mkdir(parents=True, exist_ok=True)
    if (tls_dir / "server.crt").exists() and not force:
        raise FileExistsError("Zertifikat existiert bereits (force=True zum Erneuern)")
    now = dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=5)
    ca_key = ec.generate_private_key(ec.SECP256R1())          # nur im RAM
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, f"fluidi Einmal-CA {hostname} {now:%Y-%m-%d}"),
                         x509.NameAttribute(NameOID.ORGANIZATION_NAME, "fluidi (lokal)")])
    ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name).public_key(ca_key.public_key())
          .serial_number(x509.random_serial_number()).not_valid_before(now).not_valid_after(now + dt.timedelta(days=days + 1))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.KeyUsage(digital_signature=False, content_commitment=False, key_encipherment=False,
                                       data_encipherment=False, key_agreement=False, key_cert_sign=True, crl_sign=True,
                                       encipher_only=False, decipher_only=False), critical=True)
          .add_extension(x509.NameConstraints(permitted_subtrees=[x509.DNSName(hostname)], excluded_subtrees=None), critical=True)
          .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
          .sign(ca_key, hashes.SHA256()))
    key = ec.generate_private_key(ec.SECP256R1())
    cert = (x509.CertificateBuilder().subject_name(x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, hostname)]))
            .issuer_name(ca_name).public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now).not_valid_after(now + dt.timedelta(days=days))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName(hostname)]), critical=False)
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
            .sign(ca_key, hashes.SHA256()))
    del ca_key  # CA-Schlüssel verwerfen
    kp = tls_dir / "server.key"
    fd = os.open(str(kp), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    (tls_dir / "server.crt").write_bytes(cert.public_bytes(serialization.Encoding.PEM) + ca.public_bytes(serialization.Encoding.PEM))
    (tls_dir / "ca.crt").write_bytes(ca.public_bytes(serialization.Encoding.PEM))
    (tls_dir / "ca.der").write_bytes(ca.public_bytes(serialization.Encoding.DER))  # Android akzeptiert beides
    return fingerprint(tls_dir)


def fingerprint(tls_dir: Path) -> str:
    der = Path(tls_dir, "ca.der").read_bytes() if Path(tls_dir, "ca.der").exists() else \
        ssl.PEM_cert_to_DER_cert(Path(tls_dir, "ca.crt").read_text())
    h = hashlib.sha256(der).hexdigest().upper()
    return ":".join(h[i:i + 2] for i in range(0, len(h), 2))


def info(tls_dir: Path):
    """Ablaufdatum des Server-Zertifikats (für GET /system, Warnung 60 Tage vorher)."""
    p = Path(tls_dir, "server.crt")
    if not p.exists():
        return None
    try:
        from cryptography import x509
        c = x509.load_pem_x509_certificate(p.read_bytes())
        na = c.not_valid_after_utc if hasattr(c, "not_valid_after_utc") else c.not_valid_after.replace(tzinfo=dt.timezone.utc)
    except ImportError:  # pragma: no cover
        return None
    left = (na - dt.datetime.now(dt.timezone.utc)).days
    return {"not_after": na.strftime("%Y-%m-%dT%H:%M:%SZ"), "days_left": left, "fingerprint_sha256": fingerprint(tls_dir)}


def server_context(tls_dir: Path) -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.load_cert_chain(str(Path(tls_dir, "server.crt")), str(Path(tls_dir, "server.key")))
    return ctx
