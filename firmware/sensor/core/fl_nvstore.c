/* fluidi – Schluessel-Wert-Speicher (siehe fl_nvstore.h). */
#include "fl_nvstore.h"
#include "fl_util.h"

#define MAGIC 0x314E4C46u   /* "FLN1" */
#define HDR   8u

static uint32_t base(const fl_nvs_t *s, uint32_t sect) { return sect * s->f->sector; }
static uint32_t pad4(uint32_t n) { return (n + 3u) & ~3u; }

static bool read_hdr(fl_nvs_t *s, uint32_t sect, uint32_t *gen)
{
    uint8_t h[HDR];
    if (s->f->read(s->f->ctx, base(s, sect), h, HDR) || fl_get_u32(h) != MAGIC) return false;
    *gen = fl_get_u32(h + 4);
    return *gen != 0xFFFFFFFFu;
}

static void scan(fl_nvs_t *s)
{
    uint8_t e[4], d[FL_NVS_MAX_LEN];
    memset(s->off, 0, sizeof s->off);
    uint32_t p = HDR;
    while (p + 4u <= s->f->sector) {
        if (s->f->read(s->f->ctx, base(s, s->sect) + p, e, 4)) break;
        if (e[0] == 0xFF && e[1] == 0xFF) break;                       /* frei */
        uint8_t id = e[0], len = e[1];
        uint32_t step = 4u + pad4(len);
        if (p + step > s->f->sector) break;
        if (id < FL_NVS_MAX_ID && s->f->read(s->f->ctx, base(s, s->sect) + p + 4, d, len) == 0 &&
            fl_get_u16(e + 2) == fl_crc16_ccitt(d, len, (uint16_t)(0xA500u | id)))
            s->off[id] = (uint16_t)p;
        p += step;
    }
    s->wpos = p;
}

static int start_sector(fl_nvs_t *s, uint32_t sect, uint32_t gen)
{
    uint8_t h[HDR];
    if (s->f->erase(s->f->ctx, base(s, sect))) return -1;
    fl_put_u32(h, MAGIC); fl_put_u32(h + 4, gen);
    return s->f->write(s->f->ctx, base(s, sect), h, HDR);
}

int fl_nvs_init(fl_nvs_t *s, const fl_flash_t *f)
{
    uint32_t g0 = 0, g1 = 0;
    memset(s, 0, sizeof *s);
    s->f = f;
    bool v0 = read_hdr(s, 0, &g0), v1 = read_hdr(s, 1, &g1);
    if (!v0 && !v1) { s->sect = 0; s->gen = 1; if (start_sector(s, 0, 1)) return -1; s->wpos = HDR; return 0; }
    s->sect = (v0 && (!v1 || g0 > g1)) ? 0 : 1;
    s->gen = s->sect ? g1 : g0;
    scan(s);
    return 0;
}

int fl_nvs_read(fl_nvs_t *s, uint8_t id, void *buf, uint16_t len)
{
    uint8_t e[4];
    if (id >= FL_NVS_MAX_ID || !s->off[id]) return -1;
    if (s->f->read(s->f->ctx, base(s, s->sect) + s->off[id], e, 4) || e[1] != len || len == 0) return -1;
    return s->f->read(s->f->ctx, base(s, s->sect) + s->off[id] + 4, buf, len);
}

static int append(fl_nvs_t *s, uint8_t id, const void *buf, uint8_t len)
{
    uint8_t e[4 + FL_NVS_MAX_LEN + 3];
    uint32_t step = 4u + pad4(len);
    memset(e, 0xFF, sizeof e);
    e[0] = id; e[1] = len;
    if (len) memcpy(e + 4, buf, len);
    fl_put_u16(e + 2, fl_crc16_ccitt(e + 4, len, (uint16_t)(0xA500u | id)));
    if (s->f->write(s->f->ctx, base(s, s->sect) + s->wpos, e, step)) return -1;
    s->off[id] = len ? (uint16_t)s->wpos : 0;
    s->wpos += step;
    return 0;
}

static int compact(fl_nvs_t *s)
{
    uint8_t d[FL_NVS_MAX_LEN], e[4];
    fl_nvs_t n = *s;
    n.sect = s->sect ^ 1u; n.gen = s->gen + 1u; n.wpos = HDR;
    memset(n.off, 0, sizeof n.off);
    if (start_sector(&n, n.sect, 0xFFFFFFFFu)) return -1;            /* gen erst nach dem Kopieren gueltig */
    /* Kopf: magic geschrieben, gen = 0xFFFFFFFF (ungueltig) -> erst am Ende gen setzen */
    for (uint8_t id = 0; id < FL_NVS_MAX_ID; id++) {
        if (!s->off[id]) continue;
        if (s->f->read(s->f->ctx, base(s, s->sect) + s->off[id], e, 4) ||
            s->f->read(s->f->ctx, base(s, s->sect) + s->off[id] + 4, d, e[1])) return -1;
        if (append(&n, id, d, e[1])) return -1;
    }
    uint8_t g[4];
    fl_put_u32(g, n.gen);
    if (s->f->write(s->f->ctx, base(s, n.sect) + 4, g, 4)) return -1;   /* 0xFF.. -> gen: nur 1->0 */
    s->f->erase(s->f->ctx, base(s, s->sect));
    *s = n;
    return 0;
}

int fl_nvs_write(fl_nvs_t *s, uint8_t id, const void *buf, uint16_t len)
{
    if (id >= FL_NVS_MAX_ID || len > FL_NVS_MAX_LEN) return -1;
    /* unveraendert -> nicht schreiben (Verschleiss) */
    if (len && s->off[id]) {
        uint8_t cur[FL_NVS_MAX_LEN];
        if (fl_nvs_read(s, id, cur, len) == 0 && memcmp(cur, buf, len) == 0) return 0;
    }
    if (s->wpos + 4u + pad4(len) > s->f->sector) {
        if (compact(s)) return -1;
        if (s->wpos + 4u + pad4(len) > s->f->sector) return -1;
    }
    return append(s, id, buf, (uint8_t)len);
}

int fl_nvs_delete(fl_nvs_t *s, uint8_t id)
{
    if (id >= FL_NVS_MAX_ID || !s->off[id]) return 0;
    return fl_nvs_write(s, id, NULL, 0);
}
