#!/usr/bin/env python3
"""Erzeugt tests/build/vectors.h: unabhaengige Erwartungswerte (Python `cryptography` + Referenz
firmware/tools/fluidi_proto.py) fuer die C-Unit-Tests der Sensor-Firmware. Deterministisch (feste Schluessel)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "tools"))
import fluidi_proto as fp  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402
from cryptography.hazmat.primitives.ciphers.aead import AESCCM  # noqa: E402


def carr(name, b):
    return "static const uint8_t %s[%d] = {%s};\n" % (name, len(b), ",".join("0x%02x" % x for x in b))


def main(out):
    h = ["/* generiert von tests/gen_vectors.py - nicht editieren */\n#include <stdint.h>\n"]
    # --- CCM-Gegenprobe (zufaellig, aber fest) ---
    key = bytes(range(0x40, 0x50))
    nonce = bytes(range(13))
    aad = bytes([0x12, 1, 0, 0, 0])
    pt = bytes((i * 7 + 3) & 0xFF for i in range(57))
    ct = AESCCM(key, tag_length=8).encrypt(nonce, pt, aad)
    h += [carr("V_CCM_KEY", key), carr("V_CCM_NONCE", nonce), carr("V_CCM_AAD", aad), carr("V_CCM_PT", pt),
          carr("V_CCM_CT", ct)]
    # --- Geraet / Advertising ---
    addr = bytes.fromhex("CDAB12B06F80")              # 80:6F:B0:12:AB:CD, LSB zuerst
    gw_id = bytes.fromhex("0102030405060708")
    hint = fp.gw_hint(gw_id)
    h += [carr("V_ADDR", addr), carr("V_GWID", gw_id), carr("V_GWHINT", hint),
          carr("V_ADV", fp.adv_data(addr, 0x05, 2950, 0x123456, hint))]
    # --- Kopplung mit festen Schluesseln ---
    gw_priv = ec.derive_private_key(0x1F2E3D4C5B6A79881F2E3D4C5B6A79881F2E3D4C5B6A79881F2E3D4C5B6A7988, ec.SECP256R1())
    s_priv = ec.derive_private_key(0x0A1B2C3D4E5F60710A1B2C3D4E5F60710A1B2C3D4E5F60710A1B2C3D4E5F6071, ec.SECP256R1())
    gw_pub, s_pub = fp.pub64(gw_priv), fp.pub64(s_priv)
    z = fp.ecdh(gw_priv, s_pub)
    assert z == fp.ecdh(s_priv, gw_pub)
    gw_nonce = bytes(range(0xA0, 0xB0))
    s_nonce = bytes(range(0xC0, 0xD0))
    fw = bytes([0, 1, 0, 0])
    req = fp.pair_req_payload(gw_id, gw_pub, gw_nonce)
    rsp = fp.pair_rsp_payload(addr, 0x0B, fw, s_pub, s_nonce)
    tr = fp.transcript(req, rsp, gw_nonce)
    k_link, k_conf = fp.pair_keys(z, gw_nonce, s_nonce, gw_id, addr)
    h += [carr("V_GWPUB", gw_pub), carr("V_SPUB", s_pub), carr("V_Z", z), carr("V_GWNONCE16", gw_nonce),
          carr("V_SNONCE16", s_nonce), carr("V_PAIRREQ", req), carr("V_COMMIT", fp.commit(gw_id, gw_pub, gw_nonce)), carr("V_PAIRRSP", rsp), carr("V_TRANSCRIPT", tr),
          carr("V_KLINK", k_link), carr("V_KCONF", k_conf), carr("V_SAS", bytes(fp.sas(tr))),
          carr("V_MAC_S", fp.confirm_mac(k_conf, "S", tr)), carr("V_MAC_G", fp.confirm_mac(k_conf, "G", tr))]
    # --- Sitzung ---
    gn8, sn8 = bytes(range(0x10, 0x18)), bytes(range(0x20, 0x28))
    k_s = fp.session_key(k_link, gn8, sn8)
    frame = fp.seal(k_s, fp.DIR_S2G, 7, addr, 0x90, 0x42, bytes(range(30)))
    h += [carr("V_GN8", gn8), carr("V_SN8", sn8), carr("V_KS", k_s), carr("V_SECFRAME", frame)]
    with open(out, "w") as f:
        f.write("".join(h))


if __name__ == "__main__":
    main(sys.argv[1])
