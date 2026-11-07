"""SQLite-Speicher des Gateways (ARCHITECTURE.md Kap. 3/4/12.3).

Grundsätze
- WAL + synchronous=FULL: ein Messwert gilt erst nach COMMIT als gespeichert; erst dann quittiert das Gateway
  dem Sensor (PROTOCOL Kap. 6.2 Regel 2, REQ-GW-05).
- Nur Rohwerte (raw = c_probe in 0.01 pF, Temperatur, Spannung); der Feuchteindex wird beim Lesen berechnet.
- Eindeutig (sensor, seq) -> Duplikate werden verworfen (INSERT OR IGNORE), trotzdem quittiert.
- SD-schonend: Messwerte je Sitzung in EINER Transaktion; flüchtige Zustände (RSSI, zuletzt gesehen, Batterie)
  hält model.py im RAM und schreibt sie höchstens alle 15 min (flush). Klimawerte gebündelt (climate.py).
  Schreibrate siehe ARCHITECTURE.md Kap. 14.4.
- Kleine Dokumente (Pflanze, Sensor-Konfiguration, Einstellungen, Raumplan) als JSON-Spalte – einfach zu
  migrieren, im Backup enthalten.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path

SCHEMA_VERSION = 1

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sensor (
  addr TEXT PRIMARY KEY,               -- 48-bit-Adresse 'AA:BB:CC:DD:EE:FF' = eindeutige Sensor-ID (PROTOCOL 2.3)
  id TEXT NOT NULL UNIQUE,             -- fluidi-XXXX (API, REQ-SYS-08)
  k_link BLOB,                         -- Kopplungsschlüssel (AES-128), Backup enthält ihn
  doc TEXT NOT NULL                    -- JSON: Konfiguration, Firmware, Batterie, Zustand
);
CREATE TABLE IF NOT EXISTS plant (id INTEGER PRIMARY KEY, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS assignment (
  id INTEGER PRIMARY KEY, sensor TEXT NOT NULL, plant INTEGER NOT NULL, t_from REAL NOT NULL, t_to REAL);
CREATE INDEX IF NOT EXISTS assignment_plant ON assignment(plant);
CREATE TABLE IF NOT EXISTS calibration (sensor TEXT NOT NULL, substrate TEXT NOT NULL, doc TEXT NOT NULL,
  PRIMARY KEY (sensor, substrate));
CREATE TABLE IF NOT EXISTS calibration_hist (id INTEGER PRIMARY KEY, sensor TEXT, substrate TEXT, t REAL, doc TEXT);
CREATE TABLE IF NOT EXISTS reading (
  sensor TEXT NOT NULL, seq INTEGER NOT NULL, t INTEGER NOT NULL,
  raw INTEGER, c_diag INTEGER, temp REAL, vbat INTEGER, cause INTEGER, sflags INTEGER, flags INTEGER,
  boot_id INTEGER, uptime INTEGER, rx REAL,
  PRIMARY KEY (sensor, seq)) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS reading_t ON reading(sensor, t);
CREATE TABLE IF NOT EXISTS syncpoint (sensor TEXT NOT NULL, boot_id INTEGER, uptime REAL, gw_time REAL, valid INTEGER);
CREATE INDEX IF NOT EXISTS syncpoint_s ON syncpoint(sensor, boot_id);
CREATE TABLE IF NOT EXISTS journal (id TEXT PRIMARY KEY, plant INTEGER NOT NULL, t REAL NOT NULL, doc TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS journal_plant ON journal(plant, t);
CREATE TABLE IF NOT EXISTS journal_status (plant INTEGER, t INTEGER, status TEXT, PRIMARY KEY (plant, t));
CREATE TABLE IF NOT EXISTS event_log (id INTEGER PRIMARY KEY AUTOINCREMENT, t REAL, level TEXT, code TEXT, text TEXT, sensor TEXT);
CREATE TABLE IF NOT EXISTS session (token_hash TEXT PRIMARY KEY, doc TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS climate (t INTEGER PRIMARY KEY, temp REAL, rh REAL) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS sensor_image (version TEXT PRIMARY KEY, doc TEXT NOT NULL);
"""
EVENT_LOG_MAX = 2000


class Store:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self.lock = threading.RLock()
        self.writes = 0  # Zähler Transaktionen (Diagnose Schreibrate)
        if self.path != ":memory:":
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path, check_same_thread=False, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        with self.lock:
            self.db.execute("PRAGMA journal_mode=WAL")
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.execute("PRAGMA foreign_keys=ON")
            self.db.execute("PRAGMA wal_autocheckpoint=1000")   # ≈ 4 MB WAL, seltene Checkpoints
            self.db.executescript(SCHEMA)
            if self.meta_get("schema") is None:
                self.meta_set("schema", SCHEMA_VERSION)

    # -------------------------------------------------------------------- Grundlagen
    def tx(self, fn):
        """fn(cursor) in einer Transaktion ausführen (BEGIN IMMEDIATE … COMMIT)."""
        with self.lock:
            cur = self.db.cursor()
            cur.execute("BEGIN IMMEDIATE")
            try:
                r = fn(cur)
                cur.execute("COMMIT")
                self.writes += 1
                return r
            except BaseException:
                cur.execute("ROLLBACK")
                raise

    def q(self, sql, args=()):
        with self.lock:
            return self.db.execute(sql, args).fetchall()

    def q1(self, sql, args=()):
        with self.lock:
            return self.db.execute(sql, args).fetchone()

    def close(self):
        with self.lock:
            try:
                self.db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            finally:
                self.db.close()

    # -------------------------------------------------------------------- meta (Einstellungen, Auth, IDs)
    def meta_get(self, k, default=None):
        r = self.q1("SELECT v FROM meta WHERE k=?", (k,))
        return json.loads(r["v"]) if r else default

    def meta_set(self, k, v):
        self.tx(lambda c: c.execute("INSERT OR REPLACE INTO meta(k, v) VALUES (?, ?)", (k, json.dumps(v))))

    # -------------------------------------------------------------------- Dokumente
    def load_docs(self, table, key="id"):
        return {r[key]: json.loads(r["doc"]) for r in self.q(f"SELECT * FROM {table}")}

    def save_plant(self, p):
        self.tx(lambda c: c.execute("INSERT OR REPLACE INTO plant(id, doc) VALUES (?, ?)", (p["id"], json.dumps(p))))

    def delete_plant(self, pid):
        self.tx(lambda c: c.execute("DELETE FROM plant WHERE id=?", (pid,)))

    def save_sensor(self, addr, sid, doc, k_link=None, keep_key=True):
        def f(c):
            if keep_key and k_link is None:
                c.execute("INSERT INTO sensor(addr, id, doc) VALUES (?, ?, ?) "
                          "ON CONFLICT(addr) DO UPDATE SET id=excluded.id, doc=excluded.doc", (addr, sid, json.dumps(doc)))
            else:
                c.execute("INSERT OR REPLACE INTO sensor(addr, id, k_link, doc) VALUES (?, ?, ?, ?)",
                          (addr, sid, k_link, json.dumps(doc)))
        self.tx(f)

    def save_sensor_docs(self, rows):
        """Mehrere Sensor-Dokumente in EINER Transaktion (flüchtige Werte, alle 15 min)."""
        if rows:
            self.tx(lambda c: c.executemany("UPDATE sensor SET doc=? WHERE addr=?", [(json.dumps(d), a) for a, d in rows]))

    def sensor_key(self, addr):
        r = self.q1("SELECT k_link FROM sensor WHERE addr=?", (addr,))
        return bytes(r["k_link"]) if r and r["k_link"] is not None else None

    def delete_sensor(self, addr):
        self.tx(lambda c: c.execute("DELETE FROM sensor WHERE addr=?", (addr,)))

    def sensors(self):
        return {r["addr"]: (r["id"], json.loads(r["doc"])) for r in self.q("SELECT addr, id, doc FROM sensor")}

    def save_calibration(self, addr, substrate, doc, history=True):
        def f(c):
            c.execute("INSERT OR REPLACE INTO calibration(sensor, substrate, doc) VALUES (?, ?, ?)", (addr, substrate, json.dumps(doc)))
            if history:
                c.execute("INSERT INTO calibration_hist(sensor, substrate, t, doc) VALUES (?, ?, ?, ?)",
                          (addr, substrate, time.time(), json.dumps(doc)))
        self.tx(f)

    def calibrations(self):
        out = {}
        for r in self.q("SELECT * FROM calibration"):
            out.setdefault(r["sensor"], {})[r["substrate"]] = json.loads(r["doc"])
        return out

    # -------------------------------------------------------------------- Zuordnungen (UC-11)
    def assignments(self):
        return [{"id": r["id"], "sensor": r["sensor"], "plant": r["plant"], "from": r["t_from"], "to": r["t_to"]}
                for r in self.q("SELECT * FROM assignment ORDER BY t_from")]

    def save_assignments(self, rows):
        def f(c):
            c.execute("DELETE FROM assignment")
            for a in rows:
                c.execute("INSERT INTO assignment(sensor, plant, t_from, t_to) VALUES (?, ?, ?, ?)",
                          (a["sensor"], a["plant"], a["from"], a["to"]))
        self.tx(f)

    # -------------------------------------------------------------------- Messwerte
    def insert_readings(self, addr, rows):
        """rows: dicts mit seq, t, raw, c_diag, temp, vbat, cause, sflags, flags, boot_id, uptime.
        -> Anzahl neu gespeicherter (Duplikate verworfen). Eine Transaktion, COMMIT mit synchronous=FULL."""
        now = time.time()

        def f(c):
            n = 0
            for r in rows:
                cur = c.execute("INSERT OR IGNORE INTO reading(sensor, seq, t, raw, c_diag, temp, vbat, cause, sflags, flags, boot_id, uptime, rx) "
                                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                                (addr, r["seq"], int(r["t"]), r["raw"], r.get("c_diag"), r.get("temp"), r.get("vbat"),
                                 r.get("cause", 0), r.get("sflags", 0), r.get("flags", 0), r.get("boot_id"), r.get("uptime"), now))
                n += cur.rowcount
            return n
        return self.tx(f) if rows else 0

    def readings(self, addr, t0, t1):
        return self.q("SELECT seq, t, raw, c_diag, temp, vbat, cause, sflags, flags FROM reading "
                      "WHERE sensor=? AND t>=? AND t<=? ORDER BY t", (addr, int(t0), int(t1)))

    def last_reading(self, addr, t0=0, t1=2**40):
        return self.q1("SELECT seq, t, raw, c_diag, temp, vbat, cause, sflags, flags FROM reading "
                       "WHERE sensor=? AND t>=? AND t<=? ORDER BY t DESC LIMIT 1", (addr, int(t0), int(t1)))

    def max_seq(self, addr):
        r = self.q1("SELECT MAX(seq) AS m FROM reading WHERE sensor=?", (addr,))
        return r["m"] if r and r["m"] is not None else None

    def seqs_from(self, addr, seq0):
        return [r["seq"] for r in self.q("SELECT seq FROM reading WHERE sensor=? AND seq>=? ORDER BY seq", (addr, seq0))]

    def count_readings(self):
        return self.q1("SELECT COUNT(*) AS n, MIN(t) AS t0 FROM reading")

    def retime(self, addr, updates):
        """updates: [(t, flags, seq)] – Zeit nachträglich korrigieren, wenn neue Synchronpunkte vorliegen."""
        if updates:
            self.tx(lambda c: c.executemany("UPDATE reading SET t=?, flags=? WHERE sensor=? AND seq=?",
                                            [(int(t), fl, addr, s) for t, fl, s in updates]))

    def uncertain_readings(self, addr, since):
        return self.q("SELECT seq, boot_id, uptime, flags FROM reading WHERE sensor=? AND (flags & 6) != 0 AND rx>=?",
                      (addr, since))

    def delete_readings(self, addr):
        self.tx(lambda c: c.execute("DELETE FROM reading WHERE sensor=?", (addr,)))

    # -------------------------------------------------------------------- Synchronpunkte (PROTOCOL 7)
    def add_syncpoint(self, addr, boot_id, uptime, gw_time, valid):
        def f(c):
            c.execute("INSERT INTO syncpoint VALUES (?, ?, ?, ?, ?)", (addr, boot_id, uptime, gw_time, 1 if valid else 0))
            # je boot_id höchstens 50 Punkte behalten (älteste zuerst löschen, ausser dem ersten)
            c.execute("DELETE FROM syncpoint WHERE rowid IN (SELECT rowid FROM syncpoint WHERE sensor=? AND boot_id=? "
                      "ORDER BY uptime LIMIT -1 OFFSET 50) ", (addr, boot_id))
        self.tx(f)

    def syncpoints(self, addr):
        return self.q("SELECT boot_id, uptime, gw_time, valid FROM syncpoint WHERE sensor=? ORDER BY boot_id, uptime", (addr,))

    # -------------------------------------------------------------------- Tagebuch
    def save_journal(self, e):
        self.tx(lambda c: c.execute("INSERT OR REPLACE INTO journal(id, plant, t, doc) VALUES (?, ?, ?, ?)",
                                    (e["id"], e["plant_id"], e["t"], json.dumps(e))))

    def delete_journal(self, jid):
        self.tx(lambda c: c.execute("DELETE FROM journal WHERE id=?", (jid,)))

    def journal(self):
        return {r["id"]: json.loads(r["doc"]) for r in self.q("SELECT id, doc FROM journal")}

    def journal_status(self):
        return {(r["plant"], r["t"]): r["status"] for r in self.q("SELECT * FROM journal_status")}

    def set_journal_status(self, pid, t, status):
        self.tx(lambda c: c.execute("INSERT OR REPLACE INTO journal_status VALUES (?, ?, ?)", (pid, t, status)))

    # -------------------------------------------------------------------- Ereignisse
    def log(self, level, code, text, sensor=None):
        def f(c):
            c.execute("INSERT INTO event_log(t, level, code, text, sensor) VALUES (?, ?, ?, ?, ?)",
                      (time.time(), level, code, text, sensor))
            c.execute("DELETE FROM event_log WHERE id <= (SELECT MAX(id) FROM event_log) - ?", (EVENT_LOG_MAX,))
        self.tx(f)

    def events(self, limit=50, before=None):
        return self.q("SELECT * FROM event_log WHERE id < ? ORDER BY id DESC LIMIT ?", (before or 2**62, limit))

    # -------------------------------------------------------------------- Sitzungen (PWA)
    def sessions(self):
        return {r["token_hash"]: json.loads(r["doc"]) for r in self.q("SELECT * FROM session")}

    def save_session(self, th, doc):
        self.tx(lambda c: c.execute("INSERT OR REPLACE INTO session VALUES (?, ?)", (th, json.dumps(doc))))

    def delete_session(self, th=None, keep=None):
        if th is not None:
            self.tx(lambda c: c.execute("DELETE FROM session WHERE token_hash=?", (th,)))
        else:
            self.tx(lambda c: c.execute("DELETE FROM session WHERE token_hash != ?", (keep or "",)))

    # -------------------------------------------------------------------- Klima (D-017)
    def insert_climate(self, rows):
        if rows:
            self.tx(lambda c: c.executemany("INSERT OR REPLACE INTO climate VALUES (?, ?, ?)", rows))

    def climate(self, t0, t1):
        return self.q("SELECT t, temp, rh FROM climate WHERE t>=? AND t<=? ORDER BY t", (int(t0), int(t1)))

    # -------------------------------------------------------------------- Firmware-Abbilder
    def images(self):
        return [json.loads(r["doc"]) for r in self.q("SELECT doc FROM sensor_image ORDER BY version")]

    def save_image(self, doc):
        self.tx(lambda c: c.execute("INSERT OR REPLACE INTO sensor_image VALUES (?, ?)", (doc["version"], json.dumps(doc))))

    def delete_image(self, version):
        self.tx(lambda c: c.execute("DELETE FROM sensor_image WHERE version=?", (version,)))

    # -------------------------------------------------------------------- Backup
    def snapshot(self, target: str):
        """Konsistente Kopie (läuft parallel zum Betrieb, SQLite-Backup-API)."""
        with self.lock:
            dst = sqlite3.connect(target)
            try:
                self.db.backup(dst)
            finally:
                dst.close()

    def size_bytes(self):
        r = self.q1("SELECT page_count * page_size AS s FROM pragma_page_count(), pragma_page_size()")
        return int(r["s"]) if r else 0
