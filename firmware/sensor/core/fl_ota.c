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

int fl_img_parse(const fl_flash_t *f, uint32_t base, fl_img_info_t *in)
{
    uint8_t h[32], t[4];
    memset(in, 0, sizeof *in);
    in->hw_rev = -1;
    if (f->read(f->ctx, base, h, 32) || fl_get_u32(h) != 0x96f3b83du) return -1;
    uint16_t hdr = fl_get_u16(h + 8), prot = fl_get_u16(h + 10);
    in->img_size = fl_get_u32(h + 12);
    in->ver[0] = h[20]; in->ver[1] = h[21]; in->ver[2] = h[22]; in->ver[3] = h[23];
    in->build = fl_get_u32(h + 24);
    uint32_t p = base + hdr + in->img_size;
    if (hdr < 32 || p + 4 > base + f->size) return -1;
    if (prot) {
        if (f->read(f->ctx, p, t, 4) || fl_get_u16(t) != 0x6908 || fl_get_u16(t + 2) != prot) return -1;
        uint32_t end = p + prot, q = p + 4;
        while (q + 4 <= end) {
            uint8_t v[4] = {0};
            if (f->read(f->ctx, q, t, 4)) return -1;
            uint16_t ty = fl_get_u16(t), ln = fl_get_u16(t + 2);
            if (ln <= 4 && f->read(f->ctx, q + 4, v, ln)) return -1;
            if (ty == FL_TLV_SEC_CNT && ln == 4) in->sec_cnt = fl_get_u32(v);
            if (ty == FL_TLV_HW_REV && ln >= 1) in->hw_rev = v[0];
            q += 4u + ln;
        }
    }
    in->valid = true;
    return 0;
}

uint8_t fl_ota_check_image(const fl_flash_t *f, const uint8_t run_ver[4], uint32_t run_build, uint32_t run_sec_cnt,
                           uint8_t hw_rev)
{
    fl_img_info_t in;
    if (fl_img_parse(f, 0, &in)) return FL_E_OTA_HASH;
    if (!fl_ver_newer(in.ver, in.build, run_ver, run_build) || in.sec_cnt < run_sec_cnt) return FL_E_OTA_ROLLBACK;
    if (in.hw_rev != hw_rev) return FL_E_OTA_HW_MISMATCH;
    return 0;
}
