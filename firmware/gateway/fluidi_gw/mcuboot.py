"""MCUboot-Abbild prüfen (PROTOCOL.md Kap. 9.1, REQ-FW-04) – Format laut MCUboot „design.md“
(https://docs.mcuboot.com/design.html, abgerufen 2026-11-07):

  image_header (32 B, LE): ih_magic 0x96f3b83d, ih_load_addr, ih_hdr_size u16, ih_protect_tlv_size u16,
                           ih_img_size u32 (ohne Kopf), ih_flags, ih_ver {major u8, minor u8, revision u16,
                           build_num u32}, _pad1
  danach: Kopf-Auffüllung bis ih_hdr_size, Abbild, geschützte TLVs (Magic 0x6908, im Hash), TLVs (Magic 0x6907)
  image_tlv_info: it_magic u16, it_tlv_tot u16 (inkl. info-Kopf); image_tlv: it_type u16, it_len u16
  TLV 0x10 SHA256 über Kopf+Abbild(+geschützte TLVs), 0x22 ECDSA_SIG (DER) über diesen Hash, 0x50 SEC_CNT,
  0x01 KEYHASH.

Das Gateway prüft: Magic, Längen, SHA-256, ECDSA-P-256-Signatur mit dem öffentlichen Projektschlüssel,
Sicherheitszähler (Anti-Rollback) und optional die Hardware-Kennung (eigenes TLV 0xA0, VORSCHLAG, Befund W-6).
Der Sensor (MCUboot) prüft die Signatur beim Start nochmals.
"""
from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass

from . import crypto

IMAGE_MAGIC = 0x96F3B83D
TLV_INFO_MAGIC = 0x6907
TLV_PROT_INFO_MAGIC = 0x6908
TLV_KEYHASH, TLV_SHA256, TLV_ECDSA_SIG, TLV_SEC_CNT = 0x01, 0x10, 0x22, 0x50
TLV_FLUIDI_HW = 0xA0      # Vorschlag: Platinenrevision (u8), imgtool --custom-tlv 0xA0 0x0A
HDR = struct.Struct("<IIHHIIBBHII")
assert HDR.size == 32


class ImageError(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code  # signature_invalid | bad_request | too_large | downgrade


@dataclass
class Image:
    version: tuple
    build: int
    security_counter: int
    size: int
    sha256: bytes
    hw_rev: int | None
    signature_ok: bool
    file_sha256: bytes = b""   # über die ganze Datei = OTA_BEGIN.sha256 (PROTOCOL 9.3)

    @property
    def version_str(self):
        return "%d.%d.%d" % self.version + (f"+{self.build}" if self.build else "")


def _tlvs(data, off, magic):
    if off + 4 > len(data):
        raise ImageError("bad_request", "TLV-Bereich fehlt")
    m, tot = struct.unpack_from("<HH", data, off)
    if m != magic:
        raise ImageError("bad_request", "TLV-Magic falsch")
    end = off + tot
    if end > len(data):
        raise ImageError("bad_request", "TLV-Bereich abgeschnitten")
    out, i = [], off + 4
    while i < end:
        t, ln = struct.unpack_from("<HH", data, i)
        out.append((t, data[i + 4:i + 4 + ln]))
        i += 4 + ln
    if i != end:
        raise ImageError("bad_request", "TLV-Länge inkonsistent")
    return out, end


def parse(data: bytes, pubkey_raw64: bytes | None, max_size=226 * 1024) -> Image:
    if len(data) > max_size:
        raise ImageError("too_large", f"Abbild grösser als {max_size // 1024} kB (Slot, PROTOCOL 6.4)")
    if len(data) < HDR.size:
        raise ImageError("bad_request", "Datei zu kurz")
    magic, _load, hdr_size, prot_size, img_size, _flags, vmaj, vmin, vrev, build, _pad = HDR.unpack_from(data)
    if magic != IMAGE_MAGIC:
        raise ImageError("bad_request", "Kein MCUboot-Abbild (Magic)")
    body_end = hdr_size + img_size
    if hdr_size < HDR.size or body_end > len(data):
        raise ImageError("bad_request", "Längen im Kopf ungültig")
    prot, off = [], body_end
    if prot_size:
        prot, off = _tlvs(data, body_end, TLV_PROT_INFO_MAGIC)
        if off - body_end != prot_size:
            raise ImageError("bad_request", "Grösse geschützte TLVs")
    hashed = data[:off]
    tlvs, end = _tlvs(data, off, TLV_INFO_MAGIC)
    allv = prot + tlvs
    get = lambda t: next((v for k, v in allv if k == t), None)  # noqa: E731
    sha = get(TLV_SHA256)
    digest = hashlib.sha256(hashed).digest()
    if sha is None or sha != digest:
        raise ImageError("signature_invalid", "SHA-256 im Abbild stimmt nicht")
    sec = get(TLV_SEC_CNT)
    sec_cnt = struct.unpack("<I", sec)[0] if sec and len(sec) == 4 else 0
    if sec and not any(k == TLV_SEC_CNT for k, _ in prot):
        raise ImageError("signature_invalid", "Sicherheitszähler nicht im geschützten Bereich")
    hw = get(TLV_FLUIDI_HW)
    sig = get(TLV_ECDSA_SIG)
    ok = False
    if pubkey_raw64 is None:
        raise ImageError("signature_invalid", "Kein öffentlicher Signaturschlüssel konfiguriert – Abbild wird nicht angenommen")
    if sig is None or not crypto.ecdsa_verify_digest(pubkey_raw64, digest, sig):
        raise ImageError("signature_invalid", "Signatur ungültig – Datei wird nicht verteilt")
    ok = True
    return Image((vmaj, vmin, vrev), build, sec_cnt, len(data), digest, hw[0] if hw else None, ok,
                 hashlib.sha256(data).digest())


def build(body: bytes, version=(1, 0, 4), build_num=0, sec_cnt=1, key: crypto.SigningKey | None = None,
          hw_rev: int | None = 0x0A, hdr_size=0x200) -> bytes:
    """Testabbild im MCUboot-Format erzeugen (Werkzeug/Tests; ersetzt NICHT imgtool für echte Images)."""
    prot_entries = struct.pack("<HH", TLV_SEC_CNT, 4) + struct.pack("<I", sec_cnt)
    if hw_rev is not None:
        prot_entries += struct.pack("<HHB", TLV_FLUIDI_HW, 1, hw_rev)
    prot = struct.pack("<HH", TLV_PROT_INFO_MAGIC, 4 + len(prot_entries)) + prot_entries
    hdr = HDR.pack(IMAGE_MAGIC, 0, hdr_size, len(prot), len(body), 0, version[0], version[1], version[2], build_num, 0)
    head = hdr + b"\xff" * (hdr_size - len(hdr)) + body + prot
    digest = hashlib.sha256(head).digest()
    entries = struct.pack("<HH", TLV_SHA256, 32) + digest
    if key:
        sig = key.sign_digest(digest)
        entries += struct.pack("<HH", TLV_ECDSA_SIG, len(sig)) + sig
    return head + struct.pack("<HH", TLV_INFO_MAGIC, 4 + len(entries)) + entries
