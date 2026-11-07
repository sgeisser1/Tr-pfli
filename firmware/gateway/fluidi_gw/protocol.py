"""Funkprotokoll Sensor <-> Gateway, Version 1 (firmware/PROTOCOL.md) – Rahmen, Nachrichten, Krypto.

Wird vom Gateway (central.py) UND vom simulierten Sensor (simsensor.py) benutzt; beide Seiten sind
damit gegeneinander testbar. Alle Mehrbyte-Zahlen little-endian (PROTOCOL Kap. 1).

Festlegungen, die PROTOCOL.md offen lässt (Befunde in docs/reviews/phase4_protocol_software.md):
- `sensor_addr` (6 Byte) in PAIR_RSP, HKDF-info und CCM-Nonce: Byte-Reihenfolge wie in der Luft (LSB zuerst),
  d. h. Adresse 80:6F:B0:12:AB:CD -> CD AB 12 B0 6F 80 (ANNAHME, Befund W-3).
- payload(PAIR_REQ/PAIR_RSP) für das Transkript = Nutzlast nach `vt` und `pmsg` (88 bzw. 91 Byte).
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

from . import crypto

PROTO_VERSION = 1
SERVICE_UUID = "0f740001-f9fb-4a4d-9c3b-347f1f1affd5"
RX_UUID = "0f740002-f9fb-4a4d-9c3b-347f1f1affd5"   # Gateway -> Sensor (Write / Write Without Response)
TX_UUID = "0f740003-f9fb-4a4d-9c3b-347f1f1affd5"   # Sensor -> Gateway (Notify)
COMPANY_ID = 0xFFFF
MAGIC = b"\x66\x6c"  # "fl"
ADV_FMT = 1

# Frame-Typen (Kap. 5.1)
FT_HELLO, FT_HELLO_RSP, FT_SECURE, FT_PAIR, FT_ERROR = 0x0, 0x1, 0x2, 0x3, 0xF
# Advertising-Zustandsbits (Kap. 2.4)
ST_PAIRED, ST_PAIRING, ST_DATA_PENDING, ST_BATT_LOW, ST_ERROR, ST_OTA_TEST, ST_LOCKED, ST_TIME_UNSYNCED = (1 << i for i in range(8))
# PAIR-Nachrichten (Kap. 5.2)
PAIR_REQ, PAIR_RSP, PAIR_SHOW, PAIR_CONFIRM_S, PAIR_CONFIRM_G, PAIR_DONE = 1, 2, 3, 4, 5, 6
# SECURE-Nachrichten (Kap. 5.4)
M_SESSION_INFO = 0x01
M_GET_INFO, M_TIME_SET, M_READ_RECORDS, M_ACK_RECORDS, M_MEASURE = 0x10, 0x11, 0x12, 0x13, 0x14
M_GET_SETTINGS, M_SET_SETTINGS, M_IDENTIFY, M_GET_DIAG, M_CLEAR_DIAG = 0x15, 0x16, 0x17, 0x18, 0x19
M_OTA_BEGIN, M_OTA_DATA, M_OTA_END, M_OTA_ABORT = 0x20, 0x21, 0x22, 0x23
M_REBOOT, M_UNPAIR = 0x30, 0x31
M_ERR_RSP = 0xFF
RSP = 0x80
M_OTA_PROGRESS = 0xA1  # unaufgefordert
M_RECORDS = 0x92

# Fehlercodes (Kap. 11) mit Klartext für die PWA (UC-12)
ERRORS = {
    0x00: "OK", 0x01: "Befehl unbekannt", 0x02: "Länge falsch", 0x03: "Wert ausserhalb des Bereichs",
    0x04: "Sensor beschäftigt", 0x05: "Sensor nicht mit diesem Gateway gekoppelt", 0x06: "Prüfsumme (MIC) ungültig",
    0x07: "Zähler unerwartet", 0x08: "Protokollversion nicht unterstützt", 0x09: "Zeitüberschreitung",
    0x0A: "im aktuellen Zustand nicht erlaubt", 0x0B: "Verbindungssperre aktiv (zu viele Fehlversuche)",
    0x20: "Messkette: Oszillator ohne Signal", 0x21: "Messkette: Kapazität ausserhalb Messbereich",
    0x22: "Temperatursensor antwortet nicht", 0x23: "Messung streut zu stark", 0x24: "Messung wegen Unterspannung ausgelassen",
    0x30: "Flash-Fehler", 0x31: "Pufferüberlauf: unquittierte Messwerte überschrieben", 0x32: "Einstellungen beschädigt, Werkseinstellung geladen",
    0x40: "Update: Batterie zu tief", 0x41: "Update: Abbild zu gross", 0x42: "Update: Offset falsch", 0x43: "Update: Prüfsumme falsch",
    0x44: "Update: Signatur abgelehnt", 0x45: "Update: Version zu alt (Anti-Rollback)", 0x46: "Update: Flash-Fehler",
    0x47: "Update abgebrochen", 0x48: "Update nicht gestartet", 0x49: "Update nicht bestätigt, alte Version wiederhergestellt",
    0x50: "Watchdog-Neustart", 0x51: "Brownout-Neustart", 0x52: "Absturz (HardFault)", 0x53: "Taste klemmt",
    0x54: "32-kHz-Quarz gestört", 0x55: "Unterspannungsabschaltung",
}
RESET_REASONS = ["power_on", "pin_reset", "watchdog", "software", "brownout", "hardfault", "undervoltage"]
SAS_COLORS = ["rot", "grün", "gelb"]  # 0, 1, 2 (Kap. 4.2)


class ProtocolError(Exception):
    def __init__(self, msg, code=None):
        super().__init__(msg)
        self.code = code


# ------------------------------------------------------------------------------------------------ Adressen
def addr_to_bytes(addr: str) -> bytes:
    """'80:6F:B0:12:AB:CD' -> 6 Byte in Luft-Reihenfolge (LSB zuerst)."""
    b = bytes.fromhex(addr.replace(":", ""))
    if len(b) != 6:
        raise ValueError("BLE-Adresse")
    return b[::-1]


def bytes_to_addr(b: bytes) -> str:
    return ":".join(f"{x:02X}" for x in b[::-1])


def sensor_name(addr: str) -> str:
    """REQ-SYS-08: fluidi-XXXX aus den zwei niederwertigsten Adressbytes, höherwertiges zuerst (Kap. 2.3)."""
    h = addr.replace(":", "").upper()
    return "fluidi-" + h[-4:]


def gw_hint(gateway_id: bytes) -> int:
    return int.from_bytes(crypto.sha256(gateway_id)[:2], "little")


# ------------------------------------------------------------------------------------------------ Advertising
@dataclass
class Adv:
    addr: str
    name: str | None
    state: int
    vbat_mv: int
    seq_lo: int
    gw_hint: int
    rssi: int | None = None

    def has(self, bit):
        return bool(self.state & bit)


def build_mfr(state: int, vbat_mv: int, seq_lo: int, hint: int) -> bytes:
    """Nutzlast der Herstellerdaten NACH der Company-ID (wie bleak sie liefert)."""
    v = max(0, min(255, round((vbat_mv - 2000) / 10)))
    return MAGIC + bytes([ADV_FMT, state & 0xFF, v]) + struct.pack("<HH", seq_lo & 0xFFFF, hint & 0xFFFF)


def parse_adv(addr: str, name, manufacturer_data: dict, rssi=None) -> Adv | None:
    """Filter nach Company-ID 0xFFFF und Magic 'fl' (Kap. 2.5 Regel 1). Unbekanntes Format -> None."""
    d = (manufacturer_data or {}).get(COMPANY_ID)
    if not d or len(d) < 9 or d[:2] != MAGIC or d[2] != ADV_FMT:
        return None
    seq_lo, hint = struct.unpack_from("<HH", d, 5)
    return Adv(addr=addr, name=name, state=d[3], vbat_mv=2000 + 10 * d[4], seq_lo=seq_lo, gw_hint=hint, rssi=rssi)


# ------------------------------------------------------------------------------------------------ Klartext-Frames
def vt(ftype: int) -> int:
    return (PROTO_VERSION << 4) | ftype


def frame_type(frame: bytes) -> int:
    if not frame:
        raise ProtocolError("leerer Frame")
    if frame[0] >> 4 != PROTO_VERSION:
        raise ProtocolError(f"Frame-Version {frame[0] >> 4}", 0x08)
    return frame[0] & 0x0F


def hello(gateway_id: bytes, gw_nonce: bytes, proto_max=PROTO_VERSION) -> bytes:
    assert len(gateway_id) == 8 and len(gw_nonce) == 8
    return bytes([vt(FT_HELLO), proto_max]) + gateway_id + gw_nonce


def parse_hello(f: bytes):
    if len(f) < 18:
        raise ProtocolError("HELLO zu kurz", 0x02)
    return f[1], f[2:10], f[10:18]


def hello_rsp(proto: int, s_nonce: bytes) -> bytes:
    return bytes([vt(FT_HELLO_RSP), proto]) + s_nonce


def parse_hello_rsp(f: bytes):
    if len(f) < 10:
        raise ProtocolError("HELLO_RSP zu kurz", 0x02)
    return f[1], f[2:10]


def error_frame(code: int, detail: int | None = None) -> bytes:
    return bytes([vt(FT_ERROR), code]) + (bytes([detail]) if detail is not None else b"")


def parse_error(f: bytes):
    return (f[1] if len(f) > 1 else 0), (f[2] if len(f) > 2 else None)


def pair_frame(pmsg: int, payload: bytes = b"") -> bytes:
    return bytes([vt(FT_PAIR), pmsg]) + payload


def parse_pair(f: bytes):
    if len(f) < 2:
        raise ProtocolError("PAIR zu kurz", 0x02)
    return f[1], f[2:]


# ------------------------------------------------------------------------------------------------ Kopplung (4.2)
@dataclass
class PairReq:
    gateway_id: bytes
    gw_pub: bytes
    gw_nonce: bytes

    def payload(self):
        return self.gateway_id + self.gw_pub + self.gw_nonce

    @staticmethod
    def parse(p: bytes):
        if len(p) < 88:
            raise ProtocolError("PAIR_REQ zu kurz", 0x02)
        return PairReq(p[:8], p[8:72], p[72:88])


@dataclass
class PairRsp:
    sensor_addr: bytes
    hw_rev: int
    fw_ver: bytes
    s_pub: bytes
    s_nonce: bytes

    def payload(self):
        return self.sensor_addr + bytes([self.hw_rev]) + self.fw_ver + self.s_pub + self.s_nonce

    @staticmethod
    def parse(p: bytes):
        if len(p) < 91:
            raise ProtocolError("PAIR_RSP zu kurz", 0x02)
        return PairRsp(p[:6], p[6], p[7:11], p[11:75], p[75:91])


def pair_keys(z: bytes, req: PairReq, rsp: PairRsp):
    """-> (K_link 16 B, K_conf 16 B, transcript 32 B, SAS-Ziffern [5])"""
    okm = crypto.hkdf_sha256(z, req.gw_nonce + rsp.s_nonce, b"fluidi-pair-v1" + req.gateway_id + rsp.sensor_addr, 32)
    transcript = crypto.sha256(req.payload()[:88] + rsp.payload()[:91])
    return okm[:16], okm[16:], transcript, sas_digits(transcript)


def sas_digits(transcript: bytes):
    h = crypto.sha256(b"fluidi-sas" + transcript)
    n = (h[0] | (h[1] << 8)) % 243
    digits = []
    for _ in range(5):
        digits.append(n % 3)
        n //= 3
    return digits[::-1]  # höchstwertige zuerst


def confirm_mac(k_conf: bytes, who: bytes, transcript: bytes) -> bytes:
    return crypto.hmac_sha256(k_conf, who + transcript)[:16]


def session_key(k_link: bytes, gw_nonce: bytes, s_nonce: bytes) -> bytes:
    return crypto.hkdf_sha256(k_link, gw_nonce + s_nonce, b"fluidi-sess-v1", 16)


# ------------------------------------------------------------------------------------------------ SECURE (4.4, 5.3)
DIR_G2S, DIR_S2G = 0x00, 0x01


class SecureChannel:
    """AES-128-CCM, MIC 8 Byte, Nonce dir‖ctr(LE)‖sensor_addr‖00 00, AAD = Byte 0–4 (vt + ctr).
    Empfänger akzeptiert nur ctr == erwartet (keine Lücken) -> kein Replay innerhalb der Sitzung."""

    def __init__(self, key: bytes, sensor_addr: bytes, i_am_gateway: bool):
        self.key = key
        self.addr = sensor_addr
        self.tx_dir = DIR_G2S if i_am_gateway else DIR_S2G
        self.rx_dir = DIR_S2G if i_am_gateway else DIR_G2S
        self.tx_ctr = 0
        self.rx_ctr = 0

    def _nonce(self, d, ctr):
        return bytes([d]) + struct.pack("<I", ctr) + self.addr + b"\x00\x00"

    def seal(self, msg: int, rid: int, payload: bytes = b"") -> bytes:
        head = bytes([vt(FT_SECURE)]) + struct.pack("<I", self.tx_ctr)
        ct = crypto.ccm_encrypt(self.key, self._nonce(self.tx_dir, self.tx_ctr), bytes([msg, rid]) + payload, head, 8)
        self.tx_ctr += 1
        return head + ct

    def open(self, frame: bytes):
        """-> (msg, rid, payload). Fehler -> ProtocolError (Sitzung beenden, Kap. 4.4)."""
        if len(frame) < 15 or frame_type(frame) != FT_SECURE:
            raise ProtocolError("kein SECURE-Frame", 0x02)
        ctr = struct.unpack_from("<I", frame, 1)[0]
        if ctr != self.rx_ctr:
            raise ProtocolError(f"ctr {ctr} statt {self.rx_ctr}", 0x07)
        try:
            pt = crypto.ccm_decrypt(self.key, self._nonce(self.rx_dir, ctr), frame[5:], frame[:5], 8)
        except crypto.InvalidTag as e:
            raise ProtocolError("MIC ungültig", 0x06) from e
        self.rx_ctr += 1
        return pt[0], pt[1], pt[2:]


# ------------------------------------------------------------------------------------------------ Nutzlasten
_SI = struct.Struct("<BBBHIBBHIHIIHHIHBBBBBHI")  # 48 Byte, Kap. 5.5
assert _SI.size == 48


@dataclass
class SessionInfo:
    fw_ver: tuple = (1, 0, 0)
    fw_build: int = 0
    hw_rev: int = 0x0A
    state: int = 0
    boot_id: int = 0
    uptime_s: int = 0
    uptime_frac: int = 0
    seq_last: int = 0xFFFFFFFF
    seq_oldest_unacked: int = 0
    vbat_load_mv: int = 3000
    vbat_rest_mv: int = 3000
    charge_uc: int = 0
    settings_ver: int = 0
    reset_reason: int = 0
    last_error: int = 0
    ota_result: int = 0xFF
    slot: int = 1
    rec_fmt: int = 1
    log_capacity: int = 1122
    lost_records: int = 0
    counters: dict = field(default_factory=dict)  # INFO-Erweiterung ab Offset 48 (SOLL)

    def pack(self, with_counters=False) -> bytes:
        b = _SI.pack(1, self.fw_ver[0], self.fw_ver[1], self.fw_ver[2], self.fw_build, self.hw_rev, self.state,
                     self.boot_id, self.uptime_s, self.uptime_frac, self.seq_last, self.seq_oldest_unacked,
                     self.vbat_load_mv, self.vbat_rest_mv, self.charge_uc, self.settings_ver, self.reset_reason,
                     self.last_error, self.ota_result, self.slot, self.rec_fmt, self.log_capacity, self.lost_records)
        if with_counters:
            c = self.counters
            b += struct.pack("<IIII", c.get("meas", 0), c.get("adv", 0), c.get("conn", 0), c.get("led_ms", 0))
        return b

    @staticmethod
    def parse(p: bytes) -> "SessionInfo":
        if len(p) < 48:
            raise ProtocolError("SESSION_INFO zu kurz", 0x02)
        v = _SI.unpack_from(p)
        si = SessionInfo((v[1], v[2], v[3]), v[4], v[5], v[6], v[7], v[8], v[9], v[10], v[11], v[12], v[13], v[14],
                         v[15], v[16], v[17], v[18], v[19], v[20], v[21], v[22])
        if len(p) >= 64:  # zusätzliche Byte am Ende ignorieren (Kap. 5.3 Erweiterbarkeit)
            m, a, c, l = struct.unpack_from("<IIII", p, 48)
            si.counters = {"meas": m, "adv": a, "conn": c, "led_ms": l}
        return si

    @property
    def uptime(self) -> float:
        return self.uptime_s + self.uptime_frac / 65536.0

    @property
    def fw_version(self) -> str:
        return "%d.%d.%d" % self.fw_ver


_REC = struct.Struct("<IHIHHhHBB")  # 20 Byte, Kap. 5.6
assert _REC.size == 20
CAUSES = {0: "auto", 1: "button", 2: "manual", 3: "calibration", 4: "calibration", 5: "diagnose"}


@dataclass
class Record:
    seq: int
    boot_id: int
    uptime_s: int
    c_probe: int      # 0.01 pF, 0xFFFF ungültig
    c_diag: int       # 0.01 pF, 0xFFFF nicht gemessen
    temp: int         # 0.01 °C, -32768 (0x8000) ungültig
    vbat_mv: int
    cause: int
    flags: int

    def pack(self) -> bytes:
        return _REC.pack(self.seq, self.boot_id, self.uptime_s, self.c_probe, self.c_diag, self.temp, self.vbat_mv,
                         self.cause, self.flags)

    @staticmethod
    def parse(b: bytes) -> "Record":
        return Record(*_REC.unpack_from(b))

    @property
    def valid(self):
        return self.c_probe != 0xFFFF

    @property
    def temp_c(self):
        return None if self.temp == -32768 or self.flags & 0x10 else self.temp / 100.0


def records_payload(recs, more: bool) -> bytes:
    return bytes([len(recs), 1 if more else 0]) + b"".join(r.pack() for r in recs)


def parse_records(p: bytes):
    if len(p) < 2:
        raise ProtocolError("RECORDS zu kurz", 0x02)
    n, more = p[0], p[1]
    if len(p) < 2 + 20 * n:
        raise ProtocolError("RECORDS Länge", 0x02)
    return [Record.parse(p[2 + 20 * i: 22 + 20 * i]) for i in range(n)], bool(more)


def records_per_frame(mtu: int) -> int:
    return max(1, (mtu - 3 - 15 - 2) // 20)


# ------------------------------------------------------------------------------------------------ Einstellungen (Kap. 8)
# id: (Name, struct-Format, min, max)  – Bereiche aus PROTOCOL Tab. Kap. 8
SETTINGS = {
    0x01: ("meas_interval_s", "<I", 900, 86400),
    0x02: ("adv_interval_ms", "<I", 1000, 150000),
    0x03: ("adv_interval_offline_ms", "<I", 27500, 300000),
    0x04: ("tx_power_dbm", "<b", -20, 8),
    0x05: ("water_raw", "<H", 0, 0xFFFF),
    0x06: ("water_led", "<B", 0, 1),
    0x07: ("led_window", "<HH", 0, 1440),
    0x08: ("led_level", "<B", 10, 100),
    0x09: ("heartbeat_led", "<B", 0, 1),
    0x0A: ("avg_count", "<B", 4, 32),
    0x0B: ("air_flood_raw", "<HH", 0, 0xFFFF),
    0x0C: ("batt_low_flag", "<B", 0, 1),
    0x0D: ("ota_min_mv", "<H", 2500, 3000),
    0x0E: ("diag_f2", "<B", 0, 255),
}
SETTING_IDS = {v[0]: k for k, v in SETTINGS.items()}


def encode_settings(values: dict) -> bytes:
    out = b""
    for name, val in sorted(values.items(), key=lambda kv: SETTING_IDS[kv[0]]):
        tid = SETTING_IDS[name]
        fmt = SETTINGS[tid][1]
        v = struct.pack(fmt, *(val if isinstance(val, (tuple, list)) else (val,)))
        out += bytes([tid, len(v)]) + v
    return out


def decode_settings(b: bytes, strict=True):
    """-> (dict, bad_tlv_id). Unbekannte id oder Bereichsfehler -> bad_tlv_id (atomar, Kap. 8)."""
    out, i = {}, 0
    while i < len(b):
        if i + 2 > len(b):
            return out, 0xFF
        tid, ln = b[i], b[i + 1]
        v = b[i + 2:i + 2 + ln]
        i += 2 + ln
        spec = SETTINGS.get(tid)
        if not spec or struct.calcsize(spec[1]) != ln:
            if strict:
                return out, tid
            continue
        vals = struct.unpack(spec[1], v)
        if any(not (spec[2] <= x <= spec[3]) for x in vals):
            return out, tid
        out[spec[0]] = vals if len(vals) > 1 else vals[0]
    return out, 0


def adv_interval_ms(reaction_min: int, p_miss: float = 0.10, setup_s: float = 5.0) -> int:
    """Kap. 2.2: t_adv = (Reaktionszeit − 5 s) / k, k = kleinste Zahl mit P_MISS^k ≤ 1 % (FW-P8: P_MISS messen)."""
    k = 1
    while p_miss ** k > 0.01 + 1e-12 and k < 10:
        k += 1
    return int(round((reaction_min * 60 - setup_s) / k * 1000))


# ------------------------------------------------------------------------------------------------ OTA (Kap. 9.3)
def ota_begin(size: int, ver: tuple, build: int, sec_cnt: int, sha: bytes) -> bytes:
    return struct.pack("<IBBHII", size, ver[0], ver[1], ver[2], build, sec_cnt) + sha


def parse_ota_begin(p: bytes):
    size, a, b, c, build, sec = struct.unpack_from("<IBBHII", p)
    return size, (a, b, c), build, sec, p[16:48]


def ota_begin_rsp(status, resume, window, chunk_max) -> bytes:
    return struct.pack("<BIBB", status, resume, window, chunk_max)


def parse_ota_begin_rsp(p: bytes):
    if len(p) < 7:
        raise ProtocolError("OTA_BEGIN_RSP zu kurz", 0x02)
    return struct.unpack_from("<BIBB", p)
