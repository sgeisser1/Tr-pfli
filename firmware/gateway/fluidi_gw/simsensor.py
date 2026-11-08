"""Simulierter fluidi-Sensor (Sensorseite von PROTOCOL.md v2) für Simulationsmodus und Tests.

Bildet die für das Gateway sichtbaren Regeln nach: Advertising-Zustände (2.1), Kopplung mit SAS (4.2),
Sitzung mit HELLO/SECURE (4.3/4.4), Fehlversuch-Sperre (4.5), Nachrichten (5.4), Ringspeicher mit
Quittung und Überlauf (6), Laufzeit statt Uhr (7), Einstellungen (8), OTA mit Test/Bestätigung (9).
Feuchte-Modell: exponentielle Austrocknung, Giessen als Sprung (wie app/dev/mock_server.py).

Zeitraffer: `speed` skaliert Advertising- und Messintervalle (z. B. 0.002 -> 27.5 s werden 55 ms).
Nicht modelliert: Funkverluste, Energie, LED.
"""
from __future__ import annotations

import asyncio
import collections
import hashlib
import math
import random
import struct
import time

from . import crypto
from . import protocol as P
from . import sensordiag as SD

CAPACITY = 840                # PROTOCOL 6.3 v2: garantiert 840 Datensätze
SLOT_MAX = 226 * 1024         # PROTOCOL 6.4
DEFAULT_SETTINGS = {"meas_interval_s": 14400, "adv_interval_ms": 27500, "adv_interval_offline_ms": 147500,
                    "tx_power_dbm": 0, "water_raw": 0, "water_led": 1, "led_window": (420, 1140), "led_level": 100,
                    "heartbeat_led": 1, "avg_count": 16, "air_flood_raw": (0, 0), "batt_low_flag": 0,
                    "ota_min_mv": 2700, "diag_f2": 6, "led_weekdays": 0x7F}
# ANNAHME (Simulation): Kapazität der Sonde trocken/nass in 0.01 pF, Grössenordnung MESSKETTE_SALZ.md Kap. 0
SIM_DRY, SIM_WET = 1330, 4000


class SimSensor:
    def __init__(self, addr: str, *, seed=None, speed=1.0, moisture=55.0, drying_per_day=0.12, history_days=0,
                 auto_confirm=True, fw=(1, 0, 3), clock=time.time, rssi=-62, vbat=2980, testfw=0):
        self.addr = addr.upper()
        self.addr_b = P.addr_to_bytes(self.addr)
        self.testfw = testfw                       # 1..4 = Testfirmware TF-n (TESTFIRMWARE.md Kap. 3), 0 = Serie
        self.name = P.sensor_name(self.addr) if not testfw else f"fl-tf{testfw}-{self.addr.replace(':', '')[-4:]}"
        self.rng = random.Random(seed if seed is not None else self.addr)
        self.speed = speed
        self.clock = clock
        self.rssi = rssi
        self.vbat = vbat
        self.radio = None
        self.auto_confirm = auto_confirm
        # nichtflüchtig
        self.k_link = None
        self.gateway_id = None
        self.settings = dict(DEFAULT_SETTINGS)
        self.settings_ver = 0
        self.seq = 0
        self.boot_id = 1
        self.boot_clock = clock()
        self.ring = collections.deque(maxlen=CAPACITY)
        self.acked = -1
        self.lost = 0
        self.fw = fw
        self.fw_build = 9001 + 100 * testfw if testfw else 100
        self.diag_counters = {"wdt": 0, "brownouts": 0, "auth_fail": 0, "button_stuck": 0}
        self.slot_confirmed = True
        self.ota_result = 0xFF
        self.reset_reason = 0
        self.prev_fw = None
        self.charge_uc = 0
        # flüchtig
        self.pairing_until = 0.0
        self.locked_until = 0.0
        self.fail_streak = 0
        self.links = set()
        self.sess = None
        self.pair = None
        self.ota = None
        self.time_known = False
        self.tz_min = 0
        self.last_contact = clock()
        self.tasks = []
        self.identify_until = 0.0
        self.button_presses = 0
        self.log = []          # für Tests: empfangene Nachrichtentypen
        self.hello_deadline = 1.0      # v2: 1 s nach CCCD-Write (Simulation: ab Verbindung)
        self.timeouts = 0              # Fristüberschreitungen in Folge (Ä-4: 10 -> Sperre)
        self.meas_pending = None       # v2 (Ä-8): Messung nach dem Trennen
        self.fast_adv_until = 0.0
        self.sec_cnt = 1
        # Modell
        self.m = moisture
        self.k = drying_per_day
        self.temp = 21.5
        self.true_dry, self.true_wet = SIM_DRY + self.rng.uniform(-40, 40), SIM_WET + self.rng.uniform(-120, 120)
        if history_days:
            self._prefill(history_days)

    # ------------------------------------------------------------------ Zeit, Modell
    def uptime(self) -> float:
        return self.clock() - self.boot_clock

    def _raw(self, m, temp):
        raw = self.true_dry + (self.true_wet - self.true_dry) * m / 100.0
        return int(round(raw * (1 + self.rng.gauss(0, 0.002))))

    def _prefill(self, days):
        """Vergangenheit: Sensor lief schon `days` Tage (boot_id 1), Werte liegen unquittiert im Ring."""
        step = self.settings["meas_interval_s"]
        n = min(CAPACITY - 10, int(days * 86400 / step))
        self.boot_clock = self.clock() - n * step - 600
        m = self.m
        hist = []
        for i in range(n):
            hist.append(m)
            m = m * math.exp(-self.k * step / 86400)
            if m < 22 and self.rng.random() < 0.5:
                m = self.rng.uniform(70, 85)
        for i, mm in enumerate(hist):
            up = 300 + i * step
            self._append(up, mm, 21 + 1.5 * math.sin(i / 6 * 2 * math.pi), cause=0)
        self.m = hist[-1] if hist else self.m

    def _append(self, up, m, temp, cause, flags=0):
        raw = self._raw(m, temp)
        c_diag = int(raw * 1.15) if self.settings.get("diag_f2") and self.seq % max(1, self.settings["diag_f2"]) == 0 else 0xFFFF
        if len(self.ring) == self.ring.maxlen and self.ring[0].seq > self.acked:
            self.lost += 1
        rec = P.Record(self.seq, self.boot_id, int(up), max(0, min(0xFFFE, raw)), c_diag, int(round(temp * 100)),
                       self.vbat, cause, flags)
        self.ring.append(rec)
        self.seq += 1
        self.charge_uc += 30
        return rec

    def measure(self, cause=0):
        dt = max(0.0, self.uptime() - (self.ring[-1].uptime_s if self.ring else 0))
        self.m = max(0.5, self.m * math.exp(-self.k * dt / 86400))
        self.temp = 21.5 + self.rng.gauss(0, 0.2)
        return self._append(self.uptime(), self.m, self.temp, cause)

    def water(self, to=None):
        self.m = to if to is not None else self.rng.uniform(72, 88)

    def press_button_long(self):
        """Taster ≥ 3 s: Kopplungsmodus 120 s (PROTOCOL 10.3)."""
        self.pairing_until = self.clock() + 120

    def pending(self):
        return any(r.seq > self.acked for r in self.ring)

    def state_bits(self):
        st = 0
        if self.k_link:
            st |= P.ST_PAIRED
        if self.clock() < self.pairing_until:
            st |= P.ST_PAIRING
        if self.pending():
            st |= P.ST_DATA_PENDING
        if not self.slot_confirmed:
            st |= P.ST_OTA_TEST
        if self.clock() < self.locked_until:
            st |= P.ST_LOCKED
        if not self.time_known:
            st |= P.ST_TIME_UNSYNCED
        return st

    def session_info(self, counters=False) -> bytes:
        seq_last = self.seq - 1 if self.seq else 0xFFFFFFFF
        unacked = [r.seq for r in self.ring if r.seq > self.acked]
        up = self.uptime()
        si = P.SessionInfo(fw_ver=self.fw, fw_build=self.fw_build, hw_rev=0x0A, state=self.state_bits(),
                           boot_id=self.boot_id, uptime_s=int(up), uptime_frac=int((up % 1) * 65536),
                           seq_last=seq_last, seq_oldest_unacked=min(unacked) if unacked else self.seq,
                           vbat_load_mv=self.vbat, vbat_rest_mv=self.vbat + 40, charge_uc=self.charge_uc,
                           settings_ver=self.settings_ver, reset_reason=self.reset_reason, ota_result=self.ota_result,
                           slot=1 if self.slot_confirmed else 0, lost_records=self.lost, sec_cnt=self.sec_cnt,
                           counters={"meas": self.seq, "adv": 0, "conn": 0, "led_ms": 0})
        return si.pack(with_counters=counters)

    # ------------------------------------------------------------------ Lebenszyklus
    def start(self):
        loop = asyncio.get_running_loop()
        self.tasks = [loop.create_task(self._adv_loop()), loop.create_task(self._meas_loop())]

    async def stop(self):
        for t in self.tasks:
            t.cancel()
        self.tasks = []

    def connectable(self):
        now = self.clock()
        if now < self.locked_until:
            return False
        return bool(self.k_link) or now < self.pairing_until

    def adv_interval(self):
        now = self.clock()
        if now < self.pairing_until:
            return 0.5
        if now < self.fast_adv_until:
            return 0.1
        if now - self.last_contact > 86400:
            return self.settings["adv_interval_offline_ms"] / 1000
        return self.settings["adv_interval_ms"] / 1000

    async def _adv_loop(self):
        while True:
            await asyncio.sleep(max(0.01, self.adv_interval() * self.speed))
            if not (self.k_link or self.clock() < self.pairing_until):
                continue  # ungekoppelt: kein Advertising (2.1)
            if self.links:
                continue
            hint = P.gw_hint(self.gateway_id) if self.gateway_id else 0
            seq_lo = (self.seq - 1) & 0xFFFF if self.seq else 0
            self.radio.advertise(self, P.build_mfr(self.state_bits(), self.vbat, seq_lo, hint))

    async def _meas_loop(self):
        while True:
            await asyncio.sleep(max(0.05, self.settings["meas_interval_s"] * self.speed))
            self.measure(0)

    # ------------------------------------------------------------------ Verbindung
    def on_connect(self, link):
        self.links.add(link)
        self.sess = None
        self.pair = None
        loop = asyncio.get_running_loop()
        # v2: 1 s für HELLO (Kap. 3, ab CCCD-Write), in der Simulation ab Verbindung, Echtzeit
        link._deadline = loop.call_later(self.hello_deadline, lambda: self._timeout(link))

    def _timeout(self, link):
        if self.sess is None and self.pair is None and link in self.links:
            self.timeouts += 1     # kein Fehlversuch (Ä-4), eigener Zähler
            if self.timeouts >= 10:
                self.locked_until = self.clock() + 1800 * max(self.speed, 0.0001)
                self.timeouts = 0
            self._drop(link)

    def on_disconnect(self, link):
        self.links.discard(link)
        self.sess = None
        self.pair = None
        self._after_disconnect()

    def _drop(self, link):
        self.links.discard(link)
        self.sess = None
        self.pair = None
        link.drop()
        self._after_disconnect()

    def _after_disconnect(self):
        if self.meas_pending is not None:   # Ä-8: Messung ohne Funk, danach schnelles Advertising 2 s
            cause, self.meas_pending = self.meas_pending, None
            self.measure(cause)
            self.fast_adv_until = self.clock() + 2.0

    def _fail(self, link):
        self.fail_streak += 1   # nur kryptografische Fehler (Ä-4)
        if self.fail_streak >= 3:
            self.locked_until = self.clock() + 1800 * max(self.speed, 0.0001)
            self.fail_streak = 0
            self.timeouts = 0
        self._drop(link)

    async def on_write(self, link, f: bytes):
        try:
            ft = P.frame_type(f)
        except P.ProtocolError:
            link.notify(P.error_frame(0x08, P.PROTO_VERSION))
            self._drop(link)
            return
        if ft == P.FT_HELLO:
            return self._hello(link, f)
        if ft == P.FT_PAIR:
            return await self._pair(link, f)
        if ft == P.FT_SECURE and self.sess:
            try:
                msg, rid, pl = self.sess.open(f, ota_gap=64 if self.ota else 0)   # Ä-6
            except P.ProtocolError:
                return self._fail(link)
            self.fail_streak = 0
            self.last_contact = self.clock()
            if not self.slot_confirmed:  # 9.5: authentisierte Sitzung + Selbsttest -> bestätigen
                self.slot_confirmed = True
                self.ota_result = 0
                self.sec_cnt = max(self.sec_cnt, getattr(self, "sec_pending", self.sec_cnt))  # erst mit Bestätigung (9.5)
            self.log.append(msg)
            return await self._dispatch(link, msg, rid, pl)
        self._fail(link)

    def _hello(self, link, f):
        proto_max, gid, gw_nonce = P.parse_hello(f)
        if not self.k_link or gid != self.gateway_id:
            link.notify(P.error_frame(0x05))
            self._drop(link)
            return
        s_nonce = crypto.random_bytes(8)
        ks = P.session_key(self.k_link, gw_nonce, s_nonce)
        self.sess = P.SecureChannel(ks, self.addr_b, i_am_gateway=False)
        link.notify(P.hello_rsp(min(proto_max, P.PROTO_VERSION), s_nonce))
        link.notify(self.sess.seal(P.M_SESSION_INFO, 0, self.session_info()))

    def _send(self, link, msg, rid, payload=b""):
        link.notify(self.sess.seal(msg, rid, payload))

    async def _dispatch(self, link, msg, rid, pl):
        R = msg | P.RSP
        try:
            if msg == P.M_GET_INFO:
                tail = b"TF" + bytes([self.testfw, 1]) if self.testfw else b""   # TESTFIRMWARE Kap. 3
                self._send(link, R, rid, self.session_info(counters=True) + tail)
            elif msg == P.M_TIME_SET:
                unix_ms, tz = struct.unpack_from("<Qh", pl)
                self.time_known, self.tz_min = True, tz
                self._send(link, R, rid, b"\x00")
            elif msg == P.M_READ_RECORDS:
                frm, mx = struct.unpack_from("<IH", pl)
                recs = [r for r in self.ring if r.seq >= frm]
                if mx:
                    recs = recs[:mx]
                per = P.records_per_frame(link.mtu)
                chunks = [recs[i:i + per] for i in range(0, len(recs), per)] or [[]]
                for i, ch in enumerate(chunks):
                    self._send(link, P.M_RECORDS, rid, P.records_payload(ch, i < len(chunks) - 1))
            elif msg == P.M_ACK_RECORDS:
                upto = struct.unpack_from("<I", pl)[0]
                self.acked = max(self.acked, min(upto, self.seq - 1))
                unacked = [r.seq for r in self.ring if r.seq > self.acked]
                self._send(link, R, rid, struct.pack("<BI", 0, min(unacked) if unacked else self.seq))
            elif msg == P.M_MEASURE:
                purpose = pl[0] if pl else 0
                self.meas_pending = {0: 2, 1: 3, 2: 4, 3: 5}.get(purpose, 2)   # misst nach dem Trennen (Ä-8)
                self._send(link, R, rid, P.measure_rsp(0, self.seq))
                asyncio.get_running_loop().call_later(0.3, lambda: link in self.links and self._drop(link))
            elif msg == P.M_GET_SETTINGS:
                self._send(link, R, rid, struct.pack("<H", self.settings_ver) + P.encode_settings(self.settings))
            elif msg == P.M_SET_SETTINGS:
                ver = struct.unpack_from("<H", pl)[0]
                vals, bad = P.decode_settings(pl[2:])
                if bad:
                    self._send(link, R, rid, bytes([0x03, bad]))
                else:
                    self.settings.update(vals)
                    self.settings_ver = ver
                    self._send(link, R, rid, b"\x00\x00")
            elif msg == P.M_IDENTIFY:
                self.identify_until = self.clock() + (pl[0] if pl else 5)
                self._send(link, R, rid, b"\x00")
            elif msg == P.M_GET_DIAG:
                self._send(link, R, rid, SD.sim_diag(self.testfw, boot_id=self.boot_id, **self.diag_counters))
            elif msg == P.M_CLEAR_DIAG:
                self._send(link, R, rid, b"\x00")
            elif msg == P.M_OTA_BEGIN:
                self._ota_begin(link, rid, pl)
            elif msg == P.M_OTA_DATA:
                self._ota_data(link, rid, pl)
            elif msg == P.M_OTA_END:
                self._ota_end(link, rid, pl)
            elif msg == P.M_OTA_ABORT:
                self.ota = None
                self.ota_result = 0x47
                self._send(link, R, rid, b"\x00")
            elif msg == P.M_REBOOT:
                self._send(link, R, rid, b"\x00")
                self._reboot(3)
                self._drop(link)
            elif msg == P.M_UNPAIR:
                self._send(link, R, rid, b"\x00")
                self.k_link = None
                self.gateway_id = None
                self.settings = dict(DEFAULT_SETTINGS)
                self._drop(link)
            else:
                self._send(link, P.M_ERR_RSP, rid, bytes([0x01, msg]))
        except struct.error:
            self._send(link, P.M_ERR_RSP, rid, bytes([0x02, msg]))

    def _reboot(self, reason):
        self.boot_id += 1
        self.boot_clock = self.clock()
        self.reset_reason = reason
        self.time_known = False

    # ------------------------------------------------------------------ OTA (9)
    def _ota_begin(self, link, rid, pl):
        size, ver, build, sec, sha = P.parse_ota_begin(pl)
        st = 0
        if self.vbat < self.settings["ota_min_mv"]:
            st = 0x40
        elif size > SLOT_MAX:
            st = 0x41
        elif ver <= self.fw:
            st = 0x45
        resume = 0
        if not st and self.ota and self.ota["sha"] == sha:
            resume = len(self.ota["data"])
        elif not st:
            self.ota = {"size": size, "ver": ver, "build": build, "sha": sha, "data": bytearray(), "n": 0, "sec": sec}
        self._send(link, P.M_OTA_BEGIN | P.RSP, rid, P.ota_begin_rsp(st, resume, 16, 224))

    def _ota_data(self, link, rid, pl):
        if not self.ota:
            return self._send(link, P.M_ERR_RSP, rid, bytes([0x48, P.M_OTA_DATA]))
        off = struct.unpack_from("<I", pl)[0]
        o = self.ota
        if off == len(o["data"]) and not o.get("skip"):
            o["data"] += pl[4:]
        else:
            o["skip"] = True  # Go-back-N: bis zur nächsten Fortschrittsmeldung verwerfen
        o["n"] += 1
        if o["n"] % 16 == 0 or len(o["data"]) >= o["size"]:
            o["skip"] = False
            self._send(link, P.M_OTA_PROGRESS, rid, struct.pack("<IB", len(o["data"]), 0))

    def _ota_end(self, link, rid, pl):
        o = self.ota
        if not o:
            return self._send(link, P.M_ERR_RSP, rid, bytes([0x48, P.M_OTA_END]))
        total = struct.unpack_from("<I", pl)[0]
        if total != len(o["data"]) or hashlib.sha256(bytes(o["data"])).digest() != o["sha"]:
            self.ota = None
            return self._send(link, P.M_OTA_END | P.RSP, rid, b"\x43")
        self._send(link, P.M_OTA_END | P.RSP, rid, b"\x00")
        # MCUboot: Swap, neues Image im Test (Signaturprüfung im Bootloader hier nicht nachgebildet)
        self.prev_fw, self.fw, self.fw_build = self.fw, o["ver"], o["build"]
        self.sec_pending = o.get("sec", self.sec_cnt)
        self.slot_confirmed = False
        self.ota = None
        self._reboot(3)
        self._drop(link)

    # ------------------------------------------------------------------ Kopplung (4.2)
    async def _pair(self, link, f):
        pmsg, pl = P.parse_pair(f)
        if self.clock() >= self.pairing_until:
            link.notify(P.error_frame(0x0A))
            return self._drop(link)
        if pmsg == P.PAIR_REQ:
            req = P.PairReq.parse(pl)
            key = crypto.EcdhKey()
            rsp = P.PairRsp(self.addr_b, 0x0A, bytes([self.fw[0], self.fw[1]]) + struct.pack("<H", self.fw[2]),
                            key.public_raw, crypto.random_bytes(16))
            try:
                z = key.shared(req.gw_pub)
            except ValueError:
                link.notify(P.error_frame(0x03))
                return self._drop(link)
            self.pair = {"req": req, "rsp": rsp, "z": z, "pressed": False}
            link.notify(P.pair_frame(P.PAIR_RSP, rsp.payload()))
        elif pmsg == P.PAIR_REVEAL and self.pair and "tr" not in self.pair:
            gw_nonce = pl[:16]
            if len(gw_nonce) != 16 or not self.pair["req"].check_reveal(gw_nonce):   # Commitment verletzt
                link.notify(P.pair_frame(P.PAIR_DONE, b"\x06"))
                return self._fail(link)
            k_link, k_conf, tr, sas = P.pair_keys(self.pair["z"], self.pair["req"], self.pair["rsp"], gw_nonce)
            self.pair.update(k_link=k_link, k_conf=k_conf, tr=tr, sas=sas, shown=True)
            if self.auto_confirm:  # Nutzer vergleicht Farben und drückt kurz (Simulation: nach 0.2 s)
                await asyncio.sleep(0.2)
                self.press_short(link)
        elif pmsg == P.PAIR_CONFIRM_G and self.pair:
            exp = P.confirm_mac(self.pair.get("k_conf", b""), b"G", self.pair.get("tr", b""))
            if "tr" not in self.pair or pl[:16] != exp or not self.pair["pressed"]:
                link.notify(P.pair_frame(P.PAIR_DONE, b"\x06"))
                return self._drop(link)
            self.k_link, self.gateway_id = self.pair["k_link"], self.pair["req"].gateway_id
            self.pairing_until = 0
            # Ringinhalt bleibt unquittiert und wird nach der Kopplung geliefert (PROTOCOL 6.2 Regel 0, Ä-12)
            link.notify(P.pair_frame(P.PAIR_DONE, b"\x00"))
            self.pair = None
            self.last_contact = self.clock()
        else:
            link.notify(P.error_frame(0x0A))
            self._drop(link)

    def press_short(self, link=None):
        """kurzer Tastendruck: im SAS-Schritt = 'Farben stimmen' (10.3)."""
        if self.pair and self.pair.get("shown") and not self.pair["pressed"]:
            self.pair["pressed"] = True
            link = link or next(iter(self.links), None)
            if link:
                link.notify(P.pair_frame(P.PAIR_CONFIRM_S, P.confirm_mac(self.pair["k_conf"], b"S", self.pair["tr"])))
            return True
        self.button_presses += 1
        self.measure(1)
        return False
