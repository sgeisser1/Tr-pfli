"""BLE-Central des Gateways: Scan-Entscheid, Sitzungen, Nachlieferung, Befehle, Kopplung, OTA (PROTOCOL.md v1).

Läuft in einem eigenen Thread mit asyncio-Ereignisschleife (bleak ist asyncio). HTTP-Threads reichen Aufträge
über submit()/pair()/confirm_pair() thread-sicher herein.

Ablauf je Kontakt (PROTOCOL 6.1, ARCHITECTURE 4): verbinden -> HELLO -> HELLO_RSP + SECURE#0 SESSION_INFO
(MIC geprüft = Sensor echt) -> ggf. TIME_SET -> ggf. SET_SETTINGS -> READ_RECORDS blockweise -> speichern (COMMIT)
-> ACK_RECORDS -> ausstehende Befehle (MEASURE, IDENTIFY, UNPAIR, OTA) -> trennen.
"""
from __future__ import annotations

import asyncio
import logging
import struct
import threading
import time
from collections import defaultdict, deque

from . import crypto
from . import protocol as P
from .shared import C
from .transport import LinkClosed

log = logging.getLogger("fluidi.central")
READ_CHUNK = 110            # Datensätze je READ_RECORDS (10 Frames bei MTU 247); danach speichern + quittieren
RSP_TIMEOUT = 3.0           # PROTOCOL Kap. 3: Sensor trennt nach 3 s ohne gültigen Frame
PAIR_USER_TIMEOUT = 60.0    # PROTOCOL 4.2: 60 s nach PAIR_SHOW
RETRY_BACKOFF_S = 20.0


class SessionError(Exception):
    pass


class Central:
    def __init__(self, model, radio, max_conn=3):
        self.model = model
        self.radio = radio
        self.max_conn = max_conn
        self.loop: asyncio.AbstractEventLoop | None = None
        self.thread = None
        self.sem = None
        self.busy = set()               # Adressen mit laufender Verbindung
        self.pending = defaultdict(deque)   # addr -> Befehle
        self.plock = threading.Lock()
        self.pairs = {}                 # addr -> {"job", "spec", "event", "match"}
        self.ota_lock = None
        self.last_try = {}
        self.stats = {"sessions": 0, "errors": 0, "auth_fail": 0}
        self.ready = threading.Event()

    # ------------------------------------------------------------------ Thread
    def start(self):
        self.thread = threading.Thread(target=self._run, name="fluidi-ble", daemon=True)
        self.thread.start()
        self.ready.wait(10)

    def _run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.sem = asyncio.Semaphore(self.max_conn)
        self.ota_lock = asyncio.Lock()
        self.loop.run_until_complete(self._main())

    async def _main(self):
        try:
            await self.radio.start(self._on_adv)
        except Exception as e:  # noqa: BLE001
            self.model.log("error", "radio", f"Funk nicht verfügbar: {e}")
            log.error("Radio-Start fehlgeschlagen: %s", e)
        self.ready.set()
        while True:
            await asyncio.sleep(1.0)
            try:
                self.model.tick()
            except Exception:  # noqa: BLE001
                log.exception("tick")

    def stop(self):
        if self.loop:
            fut = asyncio.run_coroutine_threadsafe(self.radio.stop(), self.loop)
            try:
                fut.result(5)
            except Exception:  # noqa: BLE001
                pass

    def call(self, fn, *a):
        """Funktion im Funk-Thread ausführen (thread-sicher)."""
        if self.loop:
            self.loop.call_soon_threadsafe(fn, *a)

    # ------------------------------------------------------------------ Aufträge (aus HTTP-Threads)
    def submit(self, addr, cmd):
        with self.plock:
            self.pending[addr].append(cmd)

    def has_pending(self, addr):
        with self.plock:
            return bool(self.pending.get(addr)) or addr in self.pairs

    def cancel_job(self, job_id):
        with self.plock:
            for q in self.pending.values():
                for c in list(q):
                    if c.get("job") and c["job"]["id"] == job_id:
                        q.remove(c)

    def pair(self, addr, job, spec):
        ev = threading.Event()
        self.pairs[addr] = {"job": job, "spec": spec, "event": ev, "match": None}
        self.call(lambda: self.loop.create_task(self._pair_task(addr)))

    def confirm_pair(self, addr, match: bool):
        p = self.pairs.get(addr)
        if not p:
            return False
        p["match"] = bool(match)
        p["event"].set()
        return True

    # ------------------------------------------------------------------ Advertising -> Entscheid
    def _on_adv(self, adv):
        try:
            want = self.model.on_adv(adv)
        except Exception:  # noqa: BLE001
            log.exception("on_adv")
            return
        if not want or adv.addr in self.busy or adv.addr in self.pairs:
            return
        if time.monotonic() - self.last_try.get(adv.addr, -1e9) < 0.05:
            return
        self.last_try[adv.addr] = time.monotonic()
        self.busy.add(adv.addr)
        self.loop.create_task(self._session_task(adv.addr, adv.rssi))

    async def _session_task(self, addr, rssi):
        try:
            async with self.sem:
                link = await self.radio.connect(addr)
                try:
                    await Session(self, link, addr).run()
                    self.stats["sessions"] += 1
                finally:
                    await link.close()
        except (LinkClosed, asyncio.TimeoutError, SessionError, P.ProtocolError, OSError) as e:
            self.stats["errors"] += 1
            log.info("Sitzung %s abgebrochen: %s", addr, e)
            self._requeue_running(addr, str(e))
        except Exception as e:  # noqa: BLE001
            self.stats["errors"] += 1
            log.exception("Sitzung %s", addr)
            self._requeue_running(addr, str(e))
        finally:
            self.busy.discard(addr)

    def _requeue_running(self, addr, why):
        m = self.model
        with self.plock:
            q = self.pending.get(addr, ())
            for c in q:
                j = c.get("job")
                if j and j["state"] == "running":
                    m.job_update(j, state="waiting_for_sensor", message=f"Verbindung abgebrochen, neuer Versuch ({why})")

    # ------------------------------------------------------------------ Kopplung
    async def _pair_task(self, addr):
        p = self.pairs[addr]
        job = p["job"]
        m = self.model
        link = None
        try:
            m.job_update(job, state="running", progress=0.2, message="Verbinde mit dem Sensor")
            async with self.sem:
                link = await self.radio.connect(addr)
                ek = crypto.EcdhKey()
                req = P.PairReq(m.gateway_id, ek.public_raw, crypto.random_bytes(16))
                await link.send(P.pair_frame(P.PAIR_REQ, req.payload()))
                f = await link.recv(RSP_TIMEOUT + 3)  # ECDH auf dem Sensor ≤ 3 s (ANNAHME, FW-P3)
                if P.frame_type(f) == P.FT_ERROR:
                    code, _ = P.parse_error(f)
                    raise SessionError(f"Sensor lehnt ab: {P.ERRORS.get(code, code)}")
                pm, pl = P.parse_pair(f)
                if pm != P.PAIR_RSP:
                    raise SessionError("PAIR_RSP erwartet")
                rsp = P.PairRsp.parse(pl)
                if P.bytes_to_addr(rsp.sensor_addr) != addr.upper():
                    raise SessionError("Sensor meldet eine andere Adresse")
                try:
                    z = ek.shared(rsp.s_pub)
                except ValueError as e:
                    raise SessionError("Öffentlicher Schlüssel des Sensors ungültig") from e
                k_link, k_conf, tr, sas = P.pair_keys(z, req, rsp)
                await link.send(P.pair_frame(P.PAIR_SHOW))
                m.job_update(job, state="awaiting_confirmation", progress=0.5,
                             message="Farbfolge vergleichen: Stimmen die Farben am Sensor mit der App überein?",
                             result={"sas": [P.SAS_COLORS[d] for d in sas], "sas_codes": sas})
                # warten: PAIR_CONFIRM_S (Taste am Sensor) und Bestätigung in der PWA, beides innert 60 s
                deadline = time.monotonic() + PAIR_USER_TIMEOUT
                conf_s = None
                while conf_s is None:
                    f = await link.recv(max(0.1, deadline - time.monotonic()))
                    pm, pl = P.parse_pair(f)
                    if pm == P.PAIR_CONFIRM_S:
                        conf_s = pl[:16]
                if conf_s != P.confirm_mac(k_conf, b"S", tr):
                    raise SessionError("Bestätigung des Sensors ungültig (MAC) – möglicher Angriff, Kopplung verworfen")
                while not p["event"].is_set():
                    if time.monotonic() > deadline:
                        raise asyncio.TimeoutError("keine Bestätigung in der App")
                    await asyncio.sleep(0.1)
                if not p["match"]:
                    raise SessionError("Farben stimmen nicht überein – Kopplung abgebrochen")
                await link.send(P.pair_frame(P.PAIR_CONFIRM_G, P.confirm_mac(k_conf, b"G", tr)))
                f = await link.recv(RSP_TIMEOUT)
                pm, pl = P.parse_pair(f)
                if pm != P.PAIR_DONE or not pl or pl[0] != 0:
                    raise SessionError(f"Sensor meldet Fehler {pl[0] if pl else '?'}")
                sid, pid = m.pair_finished(addr, k_link, rsp, p["spec"])
                m.job_update(job, state="done", progress=1.0, message="Gekoppelt – die LED leuchtet grün",
                             result={"sensor_id": sid, "plant_id": pid})
        except Exception as e:  # noqa: BLE001
            msg = getattr(e, "message", None) or str(e) or e.__class__.__name__
            if isinstance(e, asyncio.TimeoutError):
                msg = "Zeit abgelaufen (60 s) – Taste am Sensor erneut ≥ 3 s drücken"
            m.job_update(job, state="failed", message=f"Kopplung fehlgeschlagen: {msg}")
            m.log("warn", "pair_failed", f"Kopplung {addr} fehlgeschlagen: {msg}")
        finally:
            self.pairs.pop(addr, None)
            if link:
                await link.close()


class Session:
    """Eine Datensitzung mit einem gekoppelten Sensor (Gateway-Seite)."""

    def __init__(self, central: Central, link, addr):
        self.c = central
        self.m = central.model
        self.link = link
        self.addr = addr
        self.rid = 0
        self.ch = None
        self.si = None

    async def run(self):
        m = self.m
        key = m.store.sensor_key(self.addr)
        if not key:
            raise SessionError("kein Schlüssel")
        gw_nonce = crypto.random_bytes(8)
        await self.link.send(P.hello(m.gateway_id, gw_nonce))
        f = await self.link.recv(RSP_TIMEOUT)
        ft = P.frame_type(f)
        if ft == P.FT_ERROR:
            code, det = P.parse_error(f)
            # ERROR-Frames sind nicht authentisiert: NICHT den Schlüssel löschen, nur melden (Befund W-8)
            s = m.sensor_by_addr(self.addr)
            if s:
                s["error"] = {"code": f"0x{code:02X}", "text": P.ERRORS.get(code, f"Fehler 0x{code:02X}"), "t": C.iso(time.time())}
            m.log("warn", "sensor_refused", f"{self.addr}: {P.ERRORS.get(code, code)}", s["id"] if s else None)
            raise SessionError(P.ERRORS.get(code, str(code)))
        if ft != P.FT_HELLO_RSP:
            raise SessionError("HELLO_RSP erwartet")
        proto, s_nonce = P.parse_hello_rsp(f)
        self.ch = P.SecureChannel(P.session_key(key, gw_nonce, s_nonce), P.addr_to_bytes(self.addr), i_am_gateway=True)
        f = await self.link.recv(RSP_TIMEOUT)
        try:
            msg, _rid, pl = self.ch.open(f)
        except P.ProtocolError:
            self.c.stats["auth_fail"] += 1
            m.log("warn", "auth_fail", f"{self.addr}: SESSION_INFO mit ungültigem MIC – Verbindung getrennt")
            raise
        if msg != P.M_SESSION_INFO:
            raise SessionError("SESSION_INFO erwartet")
        self.si = P.SessionInfo.parse(pl)
        plan = m.on_session_info(self.addr, self.si)
        if plan.get("time_set"):
            st, _ = await self.request(P.M_TIME_SET, struct.pack("<Qh", int(m.time.now() * 1000), plan["tz_min"]))
            m.time_sent(self.addr, plan["tz_min"])
        if plan.get("settings"):
            ver, vals = plan["settings"]
            rmsg, rp = await self.request(P.M_SET_SETTINGS, struct.pack("<H", ver) + P.encode_settings(vals))
            if rp and rp[0] == 0:
                m.settings_applied(self.addr, ver, vals)
            else:
                m.log("error", "settings_rejected", f"{self.addr}: Einstellung {rp[1] if len(rp) > 1 else '?'} abgelehnt")
        await self.fetch_records()
        m.retime_uncertain(self.addr)
        await self.commands()
        it = m.rollout_item(m.by_addr.get(self.addr))
        if it and it["state"] in ("pending", "waiting_for_sensor") and not self.c.ota_lock.locked():
            await self.ota(it)

    # ------------------------------------------------------------------ Anfrage/Antwort
    async def request(self, msg, payload=b"", timeout=RSP_TIMEOUT):
        self.rid = (self.rid + 1) & 0xFF or 1
        await self.link.send(self.ch.seal(msg, self.rid, payload))
        while True:
            f = await self.link.recv(timeout)
            rmsg, rid, pl = self.ch.open(f)
            if rid != self.rid:
                continue
            if rmsg == P.M_ERR_RSP:
                code = pl[0] if pl else 0
                raise SessionError(f"Sensor lehnt {msg:#04x} ab: {P.ERRORS.get(code, code)}")
            return rmsg, pl

    async def fetch_records(self):
        """Nachlieferung blockweise: lesen -> COMMIT -> ACK (PROTOCOL 6.2). Duplikate verwirft die DB."""
        si = self.si
        if si.seq_last == 0xFFFFFFFF or si.seq_oldest_unacked > si.seq_last:
            return
        frm = si.seq_oldest_unacked
        while frm <= si.seq_last:
            self.rid = (self.rid + 1) & 0xFF or 1
            await self.link.send(self.ch.seal(P.M_READ_RECORDS, self.rid, struct.pack("<IH", frm, READ_CHUNK)))
            recs = []
            while True:
                f = await self.link.recv(RSP_TIMEOUT)
                rmsg, rid, pl = self.ch.open(f)
                if rmsg == P.M_ERR_RSP:
                    raise SessionError("READ_RECORDS abgelehnt")
                if rmsg != P.M_RECORDS:
                    continue
                batch, more = P.parse_records(pl)
                recs += batch
                if not more:
                    break
            if not recs:
                break
            self.m.store_records(self.addr, recs, via_read=True)          # COMMIT (synchronous=FULL)
            upto = self.m.contiguous_ack(self.addr, frm, max(r.seq for r in recs))
            if upto >= frm:
                _, pl = await self.request(P.M_ACK_RECORDS, struct.pack("<I", upto))
                self.m.acked(self.addr, upto, si.seq_last)
            if max(r.seq for r in recs) < frm or len(recs) < READ_CHUNK:
                break
            frm = max(r.seq for r in recs) + 1

    async def commands(self):
        c, m = self.c, self.m
        while True:
            with c.plock:
                q = c.pending.get(self.addr)
                cmd = q[0] if q else None
            if not cmd:
                return
            j = cmd.get("job")
            if j and not m.job_active(j):
                with c.plock:
                    q.popleft()
                continue
            if j:
                m.job_update(j, state="running", progress=0.5, message="Sensor verbunden")
            try:
                res = await self.execute(cmd)
                with c.plock:
                    if q and q[0] is cmd:
                        q.popleft()
                msg = res.pop("_message", "erledigt")
                if cmd.get("on_done"):
                    res = cmd["on_done"](res) or {}
                res.pop("records", None)
                if j and m.job_active(j):
                    m.job_update(j, state="done", progress=1.0, message=msg, result=res or None)
            except SessionError as e:
                with c.plock:
                    if q and q[0] is cmd:
                        q.popleft()
                if j:
                    m.job_update(j, state="failed", message=str(e))
            if cmd["kind"] == "unpair":
                return

    async def execute(self, cmd):
        m, k = self.m, cmd["kind"]
        if k in ("measure", "calibration_capture"):
            purpose = cmd.get("purpose", 0)
            recs = []
            for _ in range(cmd.get("samples", 1)):
                _, pl = await self.request(P.M_MEASURE, bytes([purpose, 1 if k == "measure" else 0]), timeout=5.0)
                if not pl or pl[0] != 0:
                    raise SessionError(P.ERRORS.get(pl[0] if pl else 0x09, "Messung fehlgeschlagen"))
                recs.append(P.Record.parse(pl[1:21]))
            m.store_records(self.addr, recs, via_read=False)
            # Quittung: der Messwert liegt auch im Ring des Sensors (Kap. 6.2 Regel 1) -> lückenlos quittieren
            start = self.si.seq_oldest_unacked
            upto = m.contiguous_ack(self.addr, start, max(r.seq for r in recs))
            if upto >= start:
                await self.request(P.M_ACK_RECORDS, struct.pack("<I", upto))
            return {"records": recs, "_message": "Neuer Messwert empfangen"}
        if k == "identify":
            await self.request(P.M_IDENTIFY, bytes([cmd.get("seconds", 10)]))
            return {"blinked": True, "_message": "LED blinkt"}
        if k == "unpair":
            await self.request(P.M_UNPAIR)
            return {"_message": "Sensor entkoppelt"}
        if k == "diag":
            _, pl = await self.request(P.M_GET_DIAG)
            return {"diag": pl.hex()}
        if k == "reboot":
            await self.request(P.M_REBOOT, b"\x01")
            return {"_message": "Neustart"}
        raise SessionError(f"unbekannter Befehl {k}")

    # ------------------------------------------------------------------ OTA (PROTOCOL 9.3)
    async def ota(self, item):
        m = self.m
        async with self.c.ota_lock:  # höchstens ein Sensor gleichzeitig (GATEWAY_API 5.4)
            ro = m.rollout
            img = next((i for i in m.sensor_images if i["version"] == ro["version"]), None)
            if not img:
                m.rollout_update(item, state="failed", message="Abbild nicht mehr vorhanden")
                return
            data = m.image_path(img["version"]).read_bytes()
            vparts = [int(x) for x in img["version"].split("+")[0].split(".")]
            cur = tuple(self.si.fw_ver)
            if tuple(vparts) <= cur:
                m.rollout_update(item, state="failed", message=f"Sensor hat bereits {self.si.fw_version} (keine Rückstufung)")
                return
            m.rollout_update(item, state="transferring", progress=0.0, message="Übertragung")
            _, pl = await self.request(P.M_OTA_BEGIN, P.ota_begin(len(data), tuple(vparts), img.get("build", 0),
                                                                 img.get("security_counter", 0), bytes.fromhex(img["sha256"])), timeout=5.0)
            st, resume, window, chunk_max = P.parse_ota_begin_rsp(pl)
            if st:
                m.rollout_update(item, state="failed", message=P.ERRORS.get(st, f"Fehler 0x{st:02X}"))
                return
            chunk = max(16, min(chunk_max or 224, self.link.mtu - 3 - 15 - 4))
            off = resume
            while off < len(data):
                sent = 0
                o = off
                while sent < (window or 16) and o < len(data):
                    part = data[o:o + chunk]
                    await self.link.send(self.ch.seal(P.M_OTA_DATA, self.rid, struct.pack("<I", o) + part), response=False)
                    o += len(part)
                    sent += 1
                # Fortschritt abwarten (Go-back-N: Sensor nennt next_offset)
                while True:
                    f = await self.link.recv(30.0)  # OTA: 30 s Frist (PROTOCOL Kap. 3)
                    rmsg, _rid, ppl = self.ch.open(f)
                    if rmsg == P.M_OTA_PROGRESS:
                        nxt, pst = struct.unpack_from("<IB", ppl)
                        break
                    if rmsg == P.M_ERR_RSP:
                        raise SessionError("OTA_DATA abgelehnt")
                if pst:
                    m.rollout_update(item, state="failed", message=P.ERRORS.get(pst, f"Fehler 0x{pst:02X}"))
                    return
                off = nxt
                m.rollout_update(item, progress=round(min(0.99, off / len(data)), 3))
            m.rollout_update(item, state="verifying", message="Sensor prüft Prüfsumme")
            _, pl = await self.request(P.M_OTA_END, struct.pack("<I", len(data)), timeout=10.0)
            if pl and pl[0] != 0:
                m.rollout_update(item, state="failed", message=P.ERRORS.get(pl[0], f"Fehler 0x{pl[0]:02X}"))
                return
            m.rollout_update(item, state="rebooting", progress=1.0,
                             message="Neustart: Bootloader prüft Signatur, Bestätigung bei der nächsten Sitzung")
            m.log("info", "fw_transfer", f"{m.by_addr.get(self.addr)}: Abbild {img['version']} übertragen", m.by_addr.get(self.addr))
