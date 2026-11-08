/* fluidi – Protokoll-Kodierung (siehe fl_proto.h, PROTOCOL.md v0.1). */
#include "fl_proto.h"
#include "fl_crypto.h"
#include "fl_util.h"

void fl_record_encode(const fl_record_t *r, uint8_t o[FL_REC_LEN])
{
    fl_put_u32(o + 0, r->seq);
    fl_put_u16(o + 4, r->boot_id);
    fl_put_u32(o + 6, r->uptime_s);
    fl_put_u16(o + 10, r->c_probe);
    fl_put_u16(o + 12, r->c_diag);
    fl_put_u16(o + 14, (uint16_t)r->temp);
    fl_put_u16(o + 16, r->vbat_mv);
    o[18] = r->cause;
    o[19] = r->flags;
}

void fl_record_decode(const uint8_t i[FL_REC_LEN], fl_record_t *r)
{
    r->seq = fl_get_u32(i + 0);
    r->boot_id = fl_get_u16(i + 4);
    r->uptime_s = fl_get_u32(i + 6);
    r->c_probe = fl_get_u16(i + 10);
    r->c_diag = fl_get_u16(i + 12);
    r->temp = (int16_t)fl_get_u16(i + 14);
    r->vbat_mv = fl_get_u16(i + 16);
    r->cause = i[18];
    r->flags = i[19];
}

void fl_device_name(const uint8_t addr_le[6], char out[12])
{
    static const char hex[] = "0123456789ABCDEF";
    /* XXXX = zwei niederwertigste Adressbytes, hoeherwertiges zuerst (Kap. 2.3) */
#if defined(FLUIDI_TESTFW) && FLUIDI_TESTFW
    /* Testfirmware: anderer Name gleicher Laenge, damit ein Testmuster nie mit Serienfirmware verwechselt wird */
    const char p[8] = {'f', 'l', '-', 't', 'f', (char)('0' + FLUIDI_TESTFW), '-', 0};
#else
    const char *p = "fluidi-";
#endif
    for (int i = 0; i < 7; i++) out[i] = p[i];
    out[7] = hex[addr_le[1] >> 4]; out[8] = hex[addr_le[1] & 15];
    out[9] = hex[addr_le[0] >> 4]; out[10] = hex[addr_le[0] & 15];
    out[11] = 0;
}

void fl_gw_hint(const uint8_t gateway_id[8], uint8_t out[2])
{
    uint8_t h[32];
    fl_sha256(gateway_id, 8, h);
    out[0] = h[0]; out[1] = h[1];
}

size_t fl_adv_build(uint8_t o[31], const uint8_t addr_le[6], uint8_t state, uint16_t vbat_mv,
                    uint32_t seq_last, const uint8_t gw_hint[2])
{
    char name[12];
    fl_device_name(addr_le, name);
    o[0] = 0x02; o[1] = 0x01; o[2] = 0x06;            /* Flags */
    o[3] = 0x0C; o[4] = 0x09;                           /* Complete Local Name, 11 Zeichen */
    memcpy(o + 5, name, 11);
    o[16] = 0x0C; o[17] = 0xFF;                         /* Manufacturer Specific Data, 11 Byte */
    fl_put_u16(o + 18, FL_COMPANY_ID);
    o[20] = 0x66; o[21] = 0x6C;                         /* magic "fl" */
    o[22] = FL_ADV_FMT;
    o[23] = state;
    int v = ((int)vbat_mv - 2000) / 10;
    o[24] = (uint8_t)(v < 0 ? 0 : v > 255 ? 255 : v);
    fl_put_u16(o + 25, (uint16_t)seq_last);
    o[27] = gw_hint ? gw_hint[0] : 0; o[28] = gw_hint ? gw_hint[1] : 0;
    return FL_ADV_LEN;
}

void fl_pair_commit(const uint8_t gateway_id[8], const uint8_t gw_pub[64], const uint8_t gw_nonce[16], uint8_t out[32])
{
    fl_sha256_ctx c;
    fl_sha256_init(&c);
    fl_sha256_update(&c, "fluidi-commit", 13);
    fl_sha256_update(&c, gateway_id, 8);
    fl_sha256_update(&c, gw_pub, 64);
    fl_sha256_update(&c, gw_nonce, 16);
    fl_sha256_final(&c, out);
}

void fl_pair_transcript(const uint8_t req[FL_PAIR_REQ_LEN], const uint8_t rsp[FL_PAIR_RSP_LEN],
                        const uint8_t gw_nonce[FL_PAIR_REVEAL_LEN], uint8_t out[32])
{
    fl_sha256_ctx c;
    fl_sha256_init(&c);
    fl_sha256_update(&c, req, FL_PAIR_REQ_LEN);
    fl_sha256_update(&c, rsp, FL_PAIR_RSP_LEN);
    fl_sha256_update(&c, gw_nonce, FL_PAIR_REVEAL_LEN);
    fl_sha256_final(&c, out);
}

void fl_pair_keys(const uint8_t z[32], const uint8_t gw_nonce[16], const uint8_t s_nonce[16],
                  const uint8_t gateway_id[8], const uint8_t sensor_addr[6], uint8_t k_link[16], uint8_t k_conf[16])
{
    uint8_t salt[32], info[14 + 8 + 6], okm[32];
    memcpy(salt, gw_nonce, 16); memcpy(salt + 16, s_nonce, 16);
    memcpy(info, "fluidi-pair-v2", 14); memcpy(info + 14, gateway_id, 8); memcpy(info + 22, sensor_addr, 6);
    fl_hkdf_sha256(salt, 32, z, 32, info, sizeof info, okm, 32);
    memcpy(k_link, okm, 16); memcpy(k_conf, okm + 16, 16);
    fl_wipe(okm, sizeof okm);
}

void fl_pair_sas(const uint8_t transcript[32], uint8_t d[5])
{
    uint8_t h[32];
    fl_sha256_ctx c;
    fl_sha256_init(&c);
    fl_sha256_update(&c, "fluidi-sas", 10);
    fl_sha256_update(&c, transcript, 32);
    fl_sha256_final(&c, h);
    unsigned n = (unsigned)(h[0] | (h[1] << 8)) % 243u;
    for (int i = 4; i >= 0; i--) { d[i] = (uint8_t)(n % 3u); n /= 3u; }   /* hoechstwertige Ziffer zuerst */
}

void fl_pair_confirm_mac(const uint8_t k_conf[16], char who, const uint8_t transcript[32], uint8_t mac[16])
{
    uint8_t full[32];
    fl_hmac_ctx c;
    uint8_t w = (uint8_t)who;
    fl_hmac_init(&c, k_conf, 16);
    fl_hmac_update(&c, &w, 1);
    fl_hmac_update(&c, transcript, 32);
    fl_hmac_final(&c, full);
    memcpy(mac, full, 16);
    fl_wipe(full, sizeof full);
}

void fl_session_key(const uint8_t k_link[16], const uint8_t gw_nonce[8], const uint8_t s_nonce[8], uint8_t k_s[16])
{
    uint8_t salt[16];
    memcpy(salt, gw_nonce, 8); memcpy(salt + 8, s_nonce, 8);
    fl_hkdf_sha256(salt, 16, k_link, 16, (const uint8_t *)"fluidi-sess-v2", 14, k_s, 16);
}

static void make_nonce(uint8_t n[13], uint8_t dir, uint32_t ctr, const uint8_t addr[6])
{
    n[0] = dir;
    fl_put_u32(n + 1, ctr);
    memcpy(n + 5, addr, 6);
    n[11] = 0; n[12] = 0;
}

int fl_secure_seal(const uint8_t k_s[16], uint8_t dir, uint32_t ctr, const uint8_t addr[6],
                   uint8_t msg, uint8_t rid, const uint8_t *payload, size_t plen, uint8_t *out)
{
    uint8_t nonce[13];
    out[0] = FL_VT(FL_FT_SECURE);
    fl_put_u32(out + 1, ctr);
    out[5] = msg; out[6] = rid;
    if (plen) memmove(out + 7, payload, plen);
    make_nonce(nonce, dir, ctr, addr);
    if (fl_ccm_encrypt(k_s, nonce, out, 5, out + 5, plen + 2, out + 5, out + 7 + plen, FL_MIC_LEN)) return -1;
    return (int)(plen + FL_SECURE_OVERHEAD);
}

int fl_secure_open(const uint8_t k_s[16], uint8_t dir, uint32_t expect_ctr, const uint8_t addr[6],
                   const uint8_t *f, size_t len, uint8_t *plain)
{
    uint8_t nonce[13];
    if (len < FL_SECURE_OVERHEAD) return -FL_E_BAD_LENGTH;
    if (f[0] != FL_VT(FL_FT_SECURE)) return -FL_E_PROTO_VERSION;
    uint32_t ctr = fl_get_u32(f + 1);
    if (ctr != expect_ctr) return -FL_E_BAD_COUNTER;
    size_t clen = len - 5 - FL_MIC_LEN;
    make_nonce(nonce, dir, ctr, addr);
    if (fl_ccm_decrypt(k_s, nonce, f, 5, f + 5, clen, plain, f + len - FL_MIC_LEN, FL_MIC_LEN)) return -FL_E_AUTH_FAIL;
    return (int)clen;
}

int fl_secure_open_ge(const uint8_t k_s[16], uint8_t dir, uint32_t min_ctr, uint32_t max_gap, const uint8_t addr[6],
                      const uint8_t *f, size_t len, uint8_t *plain, uint32_t *ctr_out)
{
    if (len < FL_SECURE_OVERHEAD) return -FL_E_BAD_LENGTH;
    uint32_t ctr = fl_get_u32(f + 1);
    if (ctr < min_ctr || ctr - min_ctr > max_gap) return -FL_E_BAD_COUNTER;
    *ctr_out = ctr;
    return fl_secure_open(k_s, dir, ctr, addr, f, len, plain);
}
