"""Backup/Restore `.fbk` v1 (ARCHITECTURE.md Kap. 8, GATEWAY_API 5.6, REQ-GW-06).

Datei:  "FLUIDIBK" · Format u16 (=1) · Kopf-Länge u16 · Kopf-JSON (Gateway-ID, Erstellzeit, KDF) ·
        Nonce 12 B · AES-256-GCM(Chiffrat ‖ Tag 16 B); AAD = alle Bytes vor der Nonce.
Schlüssel: PBKDF2-HMAC-SHA256(Passphrase, Salt 16 B, Iterationen) -> 32 B.
Klartext: gzip-Tar mit manifest.json und fluidi.sqlite (konsistente Kopie über die SQLite-Backup-API;
enthält Pflanzen, Zuordnungen, Kalibrierungen, Sensorschlüssel, Messwerte, Tagebuch, Ereignisse).
Abweichung von ARCHITECTURE 8 (plattformneutrale 24-B-Datensätze): seit D-014 nur noch Pi -> SQLite-Abbild,
vollständiger und einfacher (Befund in ARCHITECTURE Kap. 14.5 dokumentiert).
Nicht übernommen beim Einspielen: Passwort/Sitzungen, Einrichtungscode, TLS, WLAN (bleiben vom Zielgerät).
"""
from __future__ import annotations

import gzip
import io
import json
import os
import sqlite3
import struct
import tarfile
import tempfile
import time
from pathlib import Path

from . import crypto

MAGIC = b"FLUIDIBK"
FORMAT = 1
ITER = 200_000
KEEP_LOCAL = ("auth", "setup_code", "wifi_pending", "release", "release_prev")


class BackupError(Exception):
    pass


def _key(pp: str, salt: bytes, it: int) -> bytes:
    return crypto.pbkdf2(pp.encode(), salt, it, 32)


def create(model, passphrase: str) -> bytes:
    tmp = tempfile.mkdtemp(prefix="fluidi-bk-", dir=str(model.cfg.data_dir))
    snap = Path(tmp) / "fluidi.sqlite"
    try:
        model.store.snapshot(str(snap))
        db = sqlite3.connect(str(snap))
        for k in KEEP_LOCAL:
            db.execute("DELETE FROM meta WHERE k=?", (k,))
        db.execute("DELETE FROM session")
        db.commit()
        n = db.execute("SELECT COUNT(*) FROM reading").fetchone()[0]
        db.execute("VACUUM")
        db.close()
        manifest = {"format": "fluidi-backup", "version": FORMAT, "gateway_id": model.gw_name, "created": time.time(),
                    "records": n, "plants": len(model.plants), "sensors": len(model.sensors), "schema": 1}
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w:gz") as tar:
            m = json.dumps(manifest).encode()
            ti = tarfile.TarInfo("manifest.json")
            ti.size = len(m)
            tar.addfile(ti, io.BytesIO(m))
            tar.add(str(snap), arcname="fluidi.sqlite")
        plain = raw.getvalue()
    finally:
        for f in Path(tmp).glob("*"):
            f.unlink()
        os.rmdir(tmp)
    salt = os.urandom(16)
    head = json.dumps({"gateway_id": model.gw_name, "created": manifest["created"],
                       "kdf": {"alg": "pbkdf2-sha256", "salt": salt.hex(), "iter": ITER}, "cipher": "aes-256-gcm"}).encode()
    pre = MAGIC + struct.pack("<HH", FORMAT, len(head)) + head
    nonce = os.urandom(12)
    return pre + nonce + crypto.gcm_encrypt(_key(passphrase, salt, ITER), nonce, plain, pre)


def open_backup(data: bytes, passphrase: str):
    if not data.startswith(MAGIC) or len(data) < 12:
        raise BackupError("Keine gültige fluidi-Backupdatei")
    fmt, hl = struct.unpack_from("<HH", data, 8)
    if fmt != FORMAT:
        raise BackupError(f"Backup-Format {fmt} wird nicht unterstützt")
    head = json.loads(data[12:12 + hl])
    pre = data[:12 + hl]
    nonce = data[12 + hl:24 + hl]
    kdf = head["kdf"]
    try:
        plain = crypto.gcm_decrypt(_key(passphrase, bytes.fromhex(kdf["salt"]), int(kdf["iter"])), nonce, data[24 + hl:], pre)
    except crypto.InvalidTag:
        raise BackupError("Passphrase falsch oder Datei beschädigt")
    with tarfile.open(fileobj=io.BytesIO(plain), mode="r:gz") as tar:
        names = tar.getnames()
        if set(names) != {"manifest.json", "fluidi.sqlite"}:
            raise BackupError("Backup-Inhalt unerwartet")
        manifest = json.loads(tar.extractfile("manifest.json").read())
        db = tar.extractfile("fluidi.sqlite").read()
    return head, manifest, db


def restore(model, data: bytes, passphrase: str, dry_run=True):
    head, man, db = open_backup(data, passphrase)
    tmp = model.cfg.data_dir / "restore-check.sqlite"
    tmp.write_bytes(db)
    try:
        c = sqlite3.connect(str(tmp))
        ok = c.execute("PRAGMA integrity_check").fetchone()[0]
        c.close()
        if ok != "ok":
            raise BackupError("Datenbank im Backup beschädigt")
    finally:
        if dry_run:
            tmp.unlink()
    summary = {"gateway_id": man["gateway_id"], "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(man["created"])),
               "plants": man["plants"], "sensors": man["sensors"], "records": man["records"]}
    if not dry_run:
        # beim nächsten Start übernehmen (service.apply_pending_restore), lokale Geheimnisse bleiben
        tmp.rename(model.cfg.data_dir / "restore-pending.sqlite")
        model.log("warn", "restore", f"Backup von {man['gateway_id']} wird beim Neustart eingespielt")
    return summary


def apply_pending(data_dir: Path, db_path: Path):
    """Beim Start: wartendes Backup einspielen, lokale Werte (Passwort, Einrichtungscode …) übernehmen."""
    pend = data_dir / "restore-pending.sqlite"
    if not pend.exists():
        return False
    keep = {}
    if db_path.exists():
        old = sqlite3.connect(str(db_path))
        for k in KEEP_LOCAL:
            r = old.execute("SELECT v FROM meta WHERE k=?", (k,)).fetchone()
            if r:
                keep[k] = r[0]
        old.close()
        db_path.rename(db_path.with_suffix(".before-restore"))
        for ext in ("-wal", "-shm"):
            p = Path(str(db_path) + ext)
            if p.exists():
                p.unlink()
    pend.rename(db_path)
    new = sqlite3.connect(str(db_path))
    for k, v in keep.items():
        new.execute("INSERT OR REPLACE INTO meta(k, v) VALUES (?, ?)", (k, v))
    new.commit()
    new.close()
    return True
