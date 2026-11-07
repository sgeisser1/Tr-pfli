/* fluidi – Ringspeicher (siehe fl_ringlog.h). */
#include "fl_ringlog.h"
#include "fl_util.h"

#define MAGIC 0x31474C46u   /* "FLG1" */
#define NONE  0xFFFFFFFFu

static uint32_t soff(const fl_log_t *l, uint32_t s) { return s * l->f->sector; }
static uint32_t eoff(const fl_log_t *l, uint32_t s, uint32_t i) { return soff(l, s) + FL_LOG_HDR + i * FL_LOG_ENTRY; }

static bool all_ff(const uint8_t *p, size_t n)
{
    for (size_t i = 0; i < n; i++) if (p[i] != 0xFF) return false;
    return true;
}

static void scan_sector(fl_log_t *l, uint32_t s)
{
    uint8_t h[FL_LOG_HDR], e[FL_LOG_ENTRY];
    l->gen[s] = 0; l->used[s] = 0; l->first_seq[s] = NONE; l->max_seq[s] = NONE;
    if (l->f->read(l->f->ctx, soff(l, s), h, sizeof h)) return;
    if (fl_get_u32(h) != MAGIC || fl_get_u16(h + 12) != fl_crc16_ccitt(h, 12, 0xFFFF)) return;
    l->gen[s] = fl_get_u32(h + 4);
    l->first_seq[s] = fl_get_u32(h + 8);
    for (uint32_t i = 0; i < l->per_sect; i++) {
        if (l->f->read(l->f->ctx, eoff(l, s, i), e, sizeof e)) break;
        if (all_ff(e, sizeof e)) break;
        l->used[s] = (uint16_t)(i + 1);
        if (fl_get_u16(e + 20) == fl_crc16_ccitt(e, 20, 0xFFFF)) {
            uint32_t q = fl_get_u32(e);
            if (l->max_seq[s] == NONE || q > l->max_seq[s]) l->max_seq[s] = q;
        }
    }
}

int fl_log_init(fl_log_t *l, const fl_flash_t *f, fl_log_meta_t *meta)
{
    memset(l, 0, sizeof *l);
    l->f = f; l->meta = meta;
    l->n_sect = f->size / f->sector;
    if (l->n_sect < 3 || l->n_sect > FL_LOG_MAX_SECT) return -1;
    l->per_sect = (f->sector - FL_LOG_HDR) / FL_LOG_ENTRY;
    uint32_t best = 0, bestgen = 0, maxseq = NONE;
    for (uint32_t s = 0; s < l->n_sect; s++) {
        scan_sector(l, s);
        if (l->gen[s] && l->gen[s] >= bestgen) { bestgen = l->gen[s]; best = s; }
        if (l->max_seq[s] != NONE && (maxseq == NONE || l->max_seq[s] > maxseq)) maxseq = l->max_seq[s];
    }
    l->cur = best;
    l->any = (maxseq != NONE);
    l->next_seq = l->any ? maxseq + 1 : 0;
    if (l->next_seq < meta->seq_floor) l->next_seq = meta->seq_floor;
    if (bestgen == 0) l->used[best] = (uint16_t)l->per_sect;  /* erzwingt neuen Sektor beim ersten Schreiben */
    return 0;
}

static uint32_t sector_unacked(const fl_log_t *l, uint32_t s)
{
    /* Anzahl unquittierter, sichtbarer Datensaetze im Sektor (konservativ ueber seq-Spanne) */
    if (!l->gen[s] || l->max_seq[s] == NONE) return 0;
    uint32_t lo = l->first_seq[s], hi = l->max_seq[s];
    uint32_t start = l->meta->acked_upto == NONE ? 0 : l->meta->acked_upto + 1;
    if (start < l->meta->visible_from) start = l->meta->visible_from;
    if (start < lo) start = lo;
    return hi >= start ? hi - start + 1 : 0;
}

static int open_next_sector(fl_log_t *l, uint32_t *overwritten)
{
    uint32_t n = (l->cur + 1) % l->n_sect;
    uint32_t after = (n + 1) % l->n_sect;
    uint32_t gen = l->gen[l->cur] + 1;
    /* Der Sektor NACH dem neuen muss leer sein (immer einer frei) -> den neuen jetzt nutzen,
     * den uebernaechsten vorsorglich loeschen, falls er Daten haelt (aelteste Daten). */
    *overwritten += sector_unacked(l, n);
    if (l->f->erase(l->f->ctx, soff(l, n))) return -1;
    uint8_t h[FL_LOG_HDR];
    memset(h, 0xFF, sizeof h);
    fl_put_u32(h, MAGIC); fl_put_u32(h + 4, gen ? gen : 1); fl_put_u32(h + 8, l->next_seq);
    fl_put_u16(h + 12, fl_crc16_ccitt(h, 12, 0xFFFF));
    if (l->f->write(l->f->ctx, soff(l, n), h, sizeof h)) return -1;
    l->gen[n] = gen ? gen : 1; l->first_seq[n] = l->next_seq; l->max_seq[n] = NONE; l->used[n] = 0;
    l->cur = n;
    if (l->gen[after]) {
        *overwritten += sector_unacked(l, after);
        if (l->f->erase(l->f->ctx, soff(l, after))) return -1;
        l->gen[after] = 0; l->used[after] = 0; l->max_seq[after] = NONE; l->first_seq[after] = NONE;
    }
    return 0;
}

int fl_log_append(fl_log_t *l, fl_record_t *r, uint32_t *overwritten)
{
    uint8_t e[FL_LOG_ENTRY];
    *overwritten = 0;
    if (l->used[l->cur] >= l->per_sect && open_next_sector(l, overwritten)) return FL_E_FLASH_FAIL;
    r->seq = l->next_seq;
    fl_record_encode(r, e);
    fl_put_u16(e + 20, fl_crc16_ccitt(e, 20, 0xFFFF));
    e[22] = 0xFF; e[23] = 0xFF;
    uint32_t slot = l->used[l->cur];
    l->used[l->cur]++;                       /* Slot gilt auch bei Fehler als verbraucht */
    if (l->f->write(l->f->ctx, eoff(l, l->cur, slot), e, sizeof e)) return FL_E_FLASH_FAIL;
    uint8_t chk[FL_LOG_ENTRY];
    if (l->f->read(l->f->ctx, eoff(l, l->cur, slot), chk, sizeof chk) || memcmp(chk, e, sizeof e)) return FL_E_FLASH_FAIL;
    l->max_seq[l->cur] = r->seq;
    l->next_seq++;
    l->any = true;
    if (*overwritten) l->meta->lost_records += *overwritten;
    return 0;
}

static int find_in_sector(fl_log_t *l, uint32_t s, uint32_t seq, uint32_t *best_seq, fl_record_t *r)
{
    uint8_t e[FL_LOG_ENTRY];
    int found = -1;
    for (uint32_t i = 0; i < l->used[s]; i++) {
        if (l->f->read(l->f->ctx, eoff(l, s, i), e, sizeof e)) return -1;
        if (fl_get_u16(e + 20) != fl_crc16_ccitt(e, 20, 0xFFFF)) continue;
        uint32_t q = fl_get_u32(e);
        if (q >= seq && q < *best_seq) { *best_seq = q; fl_record_decode(e, r); found = 0; if (q == seq) break; }
    }
    return found;
}

int fl_log_next(fl_log_t *l, uint32_t from, fl_record_t *r)
{
    uint32_t best = NONE;
    int found = -1;
    if (from < l->meta->visible_from) from = l->meta->visible_from;
    for (uint32_t s = 0; s < l->n_sect; s++) {
        if (!l->gen[s] || l->max_seq[s] == NONE || l->max_seq[s] < from) continue;
        if (find_in_sector(l, s, from, &best, r) == 0) found = 0;
        if (found == 0 && best == from) break;
    }
    return found;
}

int fl_log_read(fl_log_t *l, uint32_t seq, fl_record_t *r)
{
    if (fl_log_next(l, seq, r) || r->seq != seq) return -1;
    return 0;
}

uint32_t fl_log_last_seq(const fl_log_t *l)
{
    if (!l->any || l->next_seq == 0 || l->next_seq - 1 < l->meta->visible_from) return NONE;
    return l->next_seq - 1;
}

uint32_t fl_log_oldest_unacked(const fl_log_t *l)
{
    uint32_t o = l->meta->acked_upto == NONE ? 0 : l->meta->acked_upto + 1;
    if (o < l->meta->visible_from) o = l->meta->visible_from;
    /* aelteste noch vorhandene seq */
    uint32_t oldest = NONE;
    for (uint32_t s = 0; s < l->n_sect; s++)
        if (l->gen[s] && l->max_seq[s] != NONE && (oldest == NONE || l->first_seq[s] < oldest)) oldest = l->first_seq[s];
    if (oldest != NONE && o < oldest) o = oldest;
    if (o > l->next_seq) o = l->next_seq;
    return o;
}

bool fl_log_pending(const fl_log_t *l)
{
    return fl_log_last_seq(l) != NONE && fl_log_oldest_unacked(l) <= fl_log_last_seq(l);
}

void fl_log_ack(fl_log_t *l, uint32_t upto)
{
    uint32_t last = fl_log_last_seq(l);
    if (last == NONE) return;
    if (upto > last) upto = last;
    if (l->meta->acked_upto == NONE || upto > l->meta->acked_upto) l->meta->acked_upto = upto;
}

void fl_log_factory_clear(fl_log_t *l)
{
    l->meta->visible_from = l->next_seq;
    l->meta->seq_floor = l->next_seq;
    if (l->next_seq) l->meta->acked_upto = l->next_seq - 1;
}

/* garantierte Kapazitaet: ein Sektor frei, der aktuelle kann gerade erst begonnen sein -> (n-2) volle Sektoren */
uint16_t fl_log_capacity(const fl_log_t *l) { return (uint16_t)((l->n_sect - 2) * l->per_sect); }
