/* fluidi – SHA-256, HMAC, HKDF, AES-CCM (siehe fl_crypto.h). Referenzen: FIPS 180-4, RFC 2104, RFC 5869, RFC 3610. */
#include "fl_crypto.h"
#include "fl_util.h"
#include <string.h>

/* ---------------- SHA-256 ---------------- */
static const uint32_t K256[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2};

#define ROR(x, n) (((x) >> (n)) | ((x) << (32 - (n))))

static void sha256_block(fl_sha256_ctx *c, const uint8_t *p)
{
    uint32_t w[64], a, b, cc, d, e, f, g, h;
    for (int i = 0; i < 16; i++)
        w[i] = ((uint32_t)p[4 * i] << 24) | ((uint32_t)p[4 * i + 1] << 16) | ((uint32_t)p[4 * i + 2] << 8) | p[4 * i + 3];
    for (int i = 16; i < 64; i++) {
        uint32_t s0 = ROR(w[i - 15], 7) ^ ROR(w[i - 15], 18) ^ (w[i - 15] >> 3);
        uint32_t s1 = ROR(w[i - 2], 17) ^ ROR(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    a = c->h[0]; b = c->h[1]; cc = c->h[2]; d = c->h[3]; e = c->h[4]; f = c->h[5]; g = c->h[6]; h = c->h[7];
    for (int i = 0; i < 64; i++) {
        uint32_t t1 = h + (ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)) + ((e & f) ^ (~e & g)) + K256[i] + w[i];
        uint32_t t2 = (ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)) + ((a & b) ^ (a & cc) ^ (b & cc));
        h = g; g = f; f = e; e = d + t1; d = cc; cc = b; b = a; a = t1 + t2;
    }
    c->h[0] += a; c->h[1] += b; c->h[2] += cc; c->h[3] += d; c->h[4] += e; c->h[5] += f; c->h[6] += g; c->h[7] += h;
}

void fl_sha256_init(fl_sha256_ctx *c)
{
    static const uint32_t iv[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                                   0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
    memcpy(c->h, iv, sizeof iv);
    c->len = 0;
    c->fill = 0;
}

void fl_sha256_update(fl_sha256_ctx *c, const void *data, size_t len)
{
    const uint8_t *p = (const uint8_t *)data;
    c->len += len;
    while (len) {
        size_t n = 64 - c->fill;
        if (n > len) n = len;
        memcpy(c->buf + c->fill, p, n);
        c->fill += (uint32_t)n; p += n; len -= n;
        if (c->fill == 64) { sha256_block(c, c->buf); c->fill = 0; }
    }
}

void fl_sha256_final(fl_sha256_ctx *c, uint8_t out[32])
{
    uint64_t bits = c->len * 8u;
    uint8_t pad = 0x80;
    fl_sha256_update(c, &pad, 1);
    pad = 0;
    while (c->fill != 56) fl_sha256_update(c, &pad, 1);
    uint8_t l[8];
    for (int i = 0; i < 8; i++) l[i] = (uint8_t)(bits >> (56 - 8 * i));
    fl_sha256_update(c, l, 8);
    for (int i = 0; i < 8; i++) {
        out[4 * i] = (uint8_t)(c->h[i] >> 24); out[4 * i + 1] = (uint8_t)(c->h[i] >> 16);
        out[4 * i + 2] = (uint8_t)(c->h[i] >> 8); out[4 * i + 3] = (uint8_t)c->h[i];
    }
    fl_wipe(c, sizeof *c);
}

void fl_sha256(const void *data, size_t len, uint8_t out[32])
{
    fl_sha256_ctx c;
    fl_sha256_init(&c);
    fl_sha256_update(&c, data, len);
    fl_sha256_final(&c, out);
}

/* ---------------- HMAC / HKDF ---------------- */
void fl_hmac_init(fl_hmac_ctx *c, const uint8_t *key, size_t keylen)
{
    uint8_t k[64], pad[64];
    memset(k, 0, sizeof k);
    if (keylen > 64) fl_sha256(key, keylen, k); else memcpy(k, key, keylen);
    for (int i = 0; i < 64; i++) pad[i] = k[i] ^ 0x36;
    fl_sha256_init(&c->inner); fl_sha256_update(&c->inner, pad, 64);
    for (int i = 0; i < 64; i++) pad[i] = k[i] ^ 0x5c;
    fl_sha256_init(&c->outer); fl_sha256_update(&c->outer, pad, 64);
    fl_wipe(k, sizeof k); fl_wipe(pad, sizeof pad);
}

void fl_hmac_update(fl_hmac_ctx *c, const void *data, size_t len) { fl_sha256_update(&c->inner, data, len); }

void fl_hmac_final(fl_hmac_ctx *c, uint8_t out[32])
{
    uint8_t ih[32];
    fl_sha256_final(&c->inner, ih);
    fl_sha256_update(&c->outer, ih, 32);
    fl_sha256_final(&c->outer, out);
    fl_wipe(ih, sizeof ih);
}

void fl_hmac_sha256(const uint8_t *key, size_t keylen, const void *data, size_t len, uint8_t out[32])
{
    fl_hmac_ctx c;
    fl_hmac_init(&c, key, keylen);
    fl_hmac_update(&c, data, len);
    fl_hmac_final(&c, out);
}

int fl_hkdf_sha256(const uint8_t *salt, size_t salt_len, const uint8_t *ikm, size_t ikm_len,
                   const uint8_t *info, size_t info_len, uint8_t *out, size_t out_len)
{
    uint8_t prk[32], t[32];
    static const uint8_t zero[32] = {0};
    if (out_len > 255u * 32u) return -1;
    if (salt == NULL || salt_len == 0) { salt = zero; salt_len = 32; }
    fl_hmac_sha256(salt, salt_len, ikm, ikm_len, prk);
    size_t done = 0, tlen = 0;
    uint8_t ctr = 1;
    while (done < out_len) {
        fl_hmac_ctx c;
        fl_hmac_init(&c, prk, 32);
        fl_hmac_update(&c, t, tlen);
        fl_hmac_update(&c, info, info_len);
        fl_hmac_update(&c, &ctr, 1);
        fl_hmac_final(&c, t);
        tlen = 32;
        size_t n = out_len - done < 32 ? out_len - done : 32;
        memcpy(out + done, t, n);
        done += n;
        ctr++;
    }
    fl_wipe(prk, sizeof prk); fl_wipe(t, sizeof t);
    return 0;
}

/* ---------------- AES-128-CCM (L = 2) ---------------- */
static int ccm_core(const uint8_t key[16], const uint8_t nonce[13], const uint8_t *aad, size_t aad_len,
                    const uint8_t *msg, size_t len, size_t mic_len, uint8_t tag[16])
{
    uint8_t b[16], x[16];
    if (len > 0xFFFFu || mic_len < 4 || mic_len > 16 || (mic_len & 1) || aad_len > 0xFEFFu) return -1;
    /* B0: Flags | Nonce | Laenge */
    b[0] = (uint8_t)((aad_len ? 0x40 : 0) | (((mic_len - 2) / 2) << 3) | (2 - 1));
    memcpy(b + 1, nonce, 13);
    b[14] = (uint8_t)(len >> 8); b[15] = (uint8_t)len;
    if (fl_aes128_encrypt_block(key, b, x)) return -1;
    if (aad_len) {
        uint8_t blk[16];
        size_t i = 0, pos = 2;
        memset(blk, 0, 16);
        blk[0] = (uint8_t)(aad_len >> 8); blk[1] = (uint8_t)aad_len;
        while (i < aad_len) {
            blk[pos++] = aad[i++];
            if (pos == 16 || i == aad_len) {
                for (int k = 0; k < 16; k++) x[k] ^= blk[k];
                if (fl_aes128_encrypt_block(key, x, x)) return -1;
                memset(blk, 0, 16); pos = 0;
            }
        }
    }
    for (size_t i = 0; i < len; i += 16) {
        size_t n = len - i < 16 ? len - i : 16;
        for (size_t k = 0; k < n; k++) x[k] ^= msg[i + k];
        if (fl_aes128_encrypt_block(key, x, x)) return -1;
    }
    memcpy(tag, x, 16);
    return 0;
}

static int ccm_ctr(const uint8_t key[16], const uint8_t nonce[13], uint16_t i, uint8_t s[16])
{
    uint8_t a[16];
    a[0] = 2 - 1;
    memcpy(a + 1, nonce, 13);
    a[14] = (uint8_t)(i >> 8); a[15] = (uint8_t)i;
    return fl_aes128_encrypt_block(key, a, s);
}

static int ccm_crypt(const uint8_t key[16], const uint8_t nonce[13], const uint8_t *in, size_t len, uint8_t *out)
{
    uint8_t s[16];
    for (size_t i = 0; i < len; i += 16) {
        if (ccm_ctr(key, nonce, (uint16_t)(i / 16 + 1), s)) return -1;
        size_t n = len - i < 16 ? len - i : 16;
        for (size_t k = 0; k < n; k++) out[i + k] = in[i + k] ^ s[k];
    }
    fl_wipe(s, sizeof s);
    return 0;
}

int fl_ccm_encrypt(const uint8_t key[16], const uint8_t nonce[13], const uint8_t *aad, size_t aad_len,
                   const uint8_t *in, size_t len, uint8_t *out, uint8_t *mic, size_t mic_len)
{
    uint8_t t[16], s0[16];
    if (ccm_core(key, nonce, aad, aad_len, in, len, mic_len, t)) return -1;
    if (ccm_crypt(key, nonce, in, len, out)) return -1;
    if (ccm_ctr(key, nonce, 0, s0)) return -1;
    for (size_t k = 0; k < mic_len; k++) mic[k] = t[k] ^ s0[k];
    fl_wipe(t, sizeof t); fl_wipe(s0, sizeof s0);
    return 0;
}

int fl_ccm_decrypt(const uint8_t key[16], const uint8_t nonce[13], const uint8_t *aad, size_t aad_len,
                   const uint8_t *in, size_t len, uint8_t *out, const uint8_t *mic, size_t mic_len)
{
    uint8_t t[16], s0[16], m[16];
    if (mic_len < 4 || mic_len > 16) return -1;
    if (ccm_crypt(key, nonce, in, len, out)) return -1;
    if (ccm_core(key, nonce, aad, aad_len, out, len, mic_len, t) || ccm_ctr(key, nonce, 0, s0)) {
        fl_wipe(out, len);
        return -1;
    }
    for (size_t k = 0; k < mic_len; k++) m[k] = t[k] ^ s0[k];
    int ok = fl_ct_equal(m, mic, mic_len);
    fl_wipe(t, sizeof t); fl_wipe(s0, sizeof s0); fl_wipe(m, sizeof m);
    if (!ok) { fl_wipe(out, len); return -1; }
    return 0;
}

/* ---------------- CRC16-CCITT (Ringspeicher-Eintraege) ---------------- */
uint16_t fl_crc16_ccitt(const uint8_t *data, size_t len, uint16_t crc)
{
    for (size_t i = 0; i < len; i++) {
        crc ^= (uint16_t)data[i] << 8;
        for (int b = 0; b < 8; b++) crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
    }
    return crc;
}
