/* fluidi – OTA-Empfang (siehe fl_ota.h). */
#include "fl_ota.h"
#include "fl_proto.h"
#include "fl_util.h"

/* Reserve am Slot-Ende fuer den MCUboot-Trailer (Swap-using-Move, max. 113 Sektoren). ANNAHME 2 Sektoren;
 * imgtool --pad --max-sectors 113 zeigt die exakte Trailergroesse (README Kap. Groessen). */
#define TRAILER_RESERVE 0x1000u

bool fl_ver_newer(const uint8_t a[4], uint32_t ab, const uint8_t b[4], uint32_t bb)
{
    uint16_t ap = fl_get_u16(a + 2), bp = fl_get_u16(b + 2);
    if (a[0] != b[0]) return a[0] > b[0];
    if (a[1] != b[1]) return a[1] > b[1];
    if (ap != bp) return ap > bp;
    return ab > bb;
}

int fl_ota_begin(fl_ota_t *o, const fl_flash_t *f, const uint8_t *p, size_t len, const uint8_t run_ver[4],
                 uint32_t run_build, bool batt_ok, uint32_t now, uint8_t chunk_max, uint8_t rsp[7])
{
    /* size u32 . version[4] . build u32 . sec_cnt u32 . sha256[32] = 48 Byte */
    memset(rsp, 0, 7);
    rsp[5] = FL_OTA_WINDOW;
    rsp[6] = chunk_max > FL_OTA_CHUNK_MAX ? FL_OTA_CHUNK_MAX : chunk_max;
    if (len < 48) { rsp[0] = FL_E_BAD_LENGTH; return rsp[0]; }
    uint32_t size = fl_get_u32(p);
    const uint8_t *ver = p + 4, *sha = p + 16;
    uint32_t build = fl_get_u32(p + 8), sc = fl_get_u32(p + 12);
    if (!batt_ok) { rsp[0] = FL_E_OTA_BATT_LOW; return rsp[0]; }
    if (size == 0 || size > f->size - TRAILER_RESERVE) { rsp[0] = FL_E_OTA_TOO_LARGE; return rsp[0]; }
    if (!fl_ver_newer(ver, build, run_ver, run_build)) { rsp[0] = FL_E_OTA_ROLLBACK; return rsp[0]; }
    /* Fortsetzung: gleiches Image (sha) innerhalb 24 h */
    if (o->active && o->size == size && memcmp(o->sha, sha, 32) == 0 && (now - o->t_begin) < FL_OTA_RESUME_MS &&
        o->next_off > 0 && o->next_off <= size) {
        fl_put_u32(rsp + 1, o->next_off);
        o->since_progress = 0; o->status = 0;
        return 0;
    }
    memset(o, 0, sizeof *o);
    o->f = f; o->active = true; o->size = size; o->build = build; o->sec_cnt = sc; o->t_begin = now;
    memcpy(o->sha, sha, 32); memcpy(o->version, ver, 4);
    fl_sha256_init(&o->h);
    return 0;
}

int fl_ota_data(fl_ota_t *o, const uint8_t *p, size_t len, uint8_t prog[5])
{
    if (!o->active) { fl_put_u32(prog, 0); prog[4] = FL_E_OTA_NOT_STARTED; return 1; }
    if (len >= 4) {
        uint32_t off = fl_get_u32(p);
        const uint8_t *d = p + 4;
        size_t n = len - 4;
        if (off == o->next_off && n > 0 && off + n <= o->size) {
            /* Sektoren erst unmittelbar vor dem Beschreiben loeschen (Kap. 9.3) */
            while (o->erased_to < off + n) {
                if (o->f->erase(o->f->ctx, o->erased_to)) { o->status = FL_E_OTA_FLASH; break; }
                o->erased_to += o->f->sector;
            }
            if (o->status == 0) {
                if (o->f->write(o->f->ctx, off, d, n)) o->status = FL_E_OTA_FLASH;
                else { fl_sha256_update(&o->h, d, n); o->next_off += (uint32_t)n; }
            }
        } else if (off + n > o->size) {
            o->status = FL_E_OTA_BAD_OFFSET;
        }
        /* falscher Offset: verwerfen bis zur naechsten Fortschrittsmeldung (Go-back-N) */
    }
    if (++o->since_progress >= FL_OTA_WINDOW || o->next_off == o->size || o->status) {
        o->since_progress = 0;
        fl_put_u32(prog, o->next_off);
        prog[4] = o->status;
        return 1;
    }
    return 0;
}

uint8_t fl_ota_end(fl_ota_t *o, const uint8_t *p, size_t len)
{
    uint8_t dig[32];
    if (!o->active) return FL_E_OTA_NOT_STARTED;
    if (len < 4 || fl_get_u32(p) != o->size || o->next_off != o->size) return FL_E_OTA_BAD_OFFSET;
    fl_sha256_final(&o->h, dig);
    o->active = false;
    if (!fl_ct_equal(dig, o->sha, 32)) {
        o->f->erase(o->f->ctx, 0);       /* Kopf ungueltig machen */
        return FL_E_OTA_HASH;
    }
    return 0;
}

void fl_ota_abort(fl_ota_t *o)
{
    if (o->f && o->erased_to) o->f->erase(o->f->ctx, 0);
    o->active = false;
}
