/* fluidi – kleine Hilfsfunktionen (plattformneutral, C99). Alle Mehrbyte-Felder little-endian (PROTOCOL.md). */
#ifndef FL_UTIL_H
#define FL_UTIL_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <stdbool.h>

static inline void fl_put_u16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); }
static inline void fl_put_u32(uint8_t *p, uint32_t v)
{
    p[0] = (uint8_t)v; p[1] = (uint8_t)(v >> 8); p[2] = (uint8_t)(v >> 16); p[3] = (uint8_t)(v >> 24);
}
static inline void fl_put_u64(uint8_t *p, uint64_t v) { fl_put_u32(p, (uint32_t)v); fl_put_u32(p + 4, (uint32_t)(v >> 32)); }
static inline uint16_t fl_get_u16(const uint8_t *p) { return (uint16_t)(p[0] | ((uint16_t)p[1] << 8)); }
static inline uint32_t fl_get_u32(const uint8_t *p)
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}
static inline uint64_t fl_get_u64(const uint8_t *p) { return (uint64_t)fl_get_u32(p) | ((uint64_t)fl_get_u32(p + 4) << 32); }

/* Vergleich in konstanter Zeit (MAC-Pruefung) */
static inline bool fl_ct_equal(const uint8_t *a, const uint8_t *b, size_t n)
{
    uint8_t d = 0;
    for (size_t i = 0; i < n; i++) d |= (uint8_t)(a[i] ^ b[i]);
    return d == 0;
}

/* Speicher sicher loeschen (nicht wegoptimierbar) */
static inline void fl_wipe(void *p, size_t n)
{
    volatile uint8_t *v = (volatile uint8_t *)p;
    while (n--) *v++ = 0;
}

uint16_t fl_crc16_ccitt(const uint8_t *data, size_t len, uint16_t crc);

#endif
