/*
 * fluidi – Kryptografie fuer das Anwendungsprotokoll (PROTOCOL.md Kap. 4):
 * SHA-256 (FIPS 180-4), HMAC-SHA-256 (RFC 2104), HKDF-SHA-256 (RFC 5869), AES-128-CCM (RFC 3610 / NIST SP 800-38C).
 * Plattformneutral. Die AES-Blockfunktion kommt vom Port (Ziel: Hardware-AES ueber TI AESECB-Treiber;
 * Host-Tests: Software-AES fl_aes_sw.c).
 */
#ifndef FL_CRYPTO_H
#define FL_CRYPTO_H
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

typedef struct {
    uint32_t h[8];
    uint64_t len;
    uint8_t buf[64];
    uint32_t fill;
} fl_sha256_ctx;

void fl_sha256_init(fl_sha256_ctx *c);
void fl_sha256_update(fl_sha256_ctx *c, const void *data, size_t len);
void fl_sha256_final(fl_sha256_ctx *c, uint8_t out[32]);
void fl_sha256(const void *data, size_t len, uint8_t out[32]);

typedef struct {
    fl_sha256_ctx inner, outer;
} fl_hmac_ctx;

void fl_hmac_init(fl_hmac_ctx *c, const uint8_t *key, size_t keylen);
void fl_hmac_update(fl_hmac_ctx *c, const void *data, size_t len);
void fl_hmac_final(fl_hmac_ctx *c, uint8_t out[32]);
void fl_hmac_sha256(const uint8_t *key, size_t keylen, const void *data, size_t len, uint8_t out[32]);

/* HKDF-SHA-256: out_len <= 255*32. info darf aus zwei Teilen bestehen (info1 || info2 || info3). */
int fl_hkdf_sha256(const uint8_t *salt, size_t salt_len, const uint8_t *ikm, size_t ikm_len,
                   const uint8_t *info, size_t info_len, uint8_t *out, size_t out_len);

/* Port: ein AES-128-Block (ECB-Verschluesselung). Rueckgabe 0 = ok. */
int fl_aes128_encrypt_block(const uint8_t key[16], const uint8_t in[16], uint8_t out[16]);

/* AES-128-CCM, Nonce 13 Byte (L = 2), MIC-Laenge mic_len (4..16, gerade). In-place erlaubt (in == out). */
int fl_ccm_encrypt(const uint8_t key[16], const uint8_t nonce[13], const uint8_t *aad, size_t aad_len,
                   const uint8_t *in, size_t len, uint8_t *out, uint8_t *mic, size_t mic_len);
/* Rueckgabe 0 = MIC gueltig (out enthaelt Klartext), sonst -1 (out wird geloescht). */
int fl_ccm_decrypt(const uint8_t key[16], const uint8_t nonce[13], const uint8_t *aad, size_t aad_len,
                   const uint8_t *in, size_t len, uint8_t *out, const uint8_t *mic, size_t mic_len);

#endif
