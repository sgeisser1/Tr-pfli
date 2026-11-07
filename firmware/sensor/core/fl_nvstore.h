/*
 * fluidi – kleiner, stromausfallsicherer Schluessel-Wert-Speicher fuer Einstellungen, Kopplung, Zaehler und
 * Fehlerprotokoll (PROTOCOL.md 4.6 "doppelt gepuffert"). Plattformneutral ueber fl_flash_t.
 *
 * Aufbau: 2 Sektoren (A/B). Jeder Sektor: Kopf 8 Byte {magic "FLN1", gen u32}, dann Eintraege
 * {id u8, len u8, crc16 u16, daten (len, auf 4 Byte aufgerundet)}. Der neueste gueltige Eintrag je id gilt;
 * len = 0 bedeutet geloescht. Ist der Sektor voll, werden alle gueltigen Eintraege in den anderen Sektor
 * kopiert (neue gen) und erst danach der alte geloescht -> nach jedem Stromausfall bleibt ein konsistenter
 * Stand lesbar. Schreibvorgaenge je 256-B-Zeile <= 83 (DS S.21 Tab. 7.11) ist bei Eintraegen >= 8 Byte erfuellt
 * (max. 32 je Zeile).
 */
#ifndef FL_NVSTORE_H
#define FL_NVSTORE_H
#include <stdint.h>
#include <stdbool.h>
#include "fl_ringlog.h"

#define FL_NVS_MAX_ID   16
#define FL_NVS_MAX_LEN  252

typedef struct {
    const fl_flash_t *f;
    uint32_t sect;            /* aktiver Sektor (0/1) */
    uint32_t gen;
    uint32_t wpos;            /* Schreibposition im aktiven Sektor */
    uint16_t off[FL_NVS_MAX_ID];   /* Offset des neuesten Eintrags je id (0 = keiner) */
} fl_nvs_t;

int fl_nvs_init(fl_nvs_t *s, const fl_flash_t *f);
int fl_nvs_read(fl_nvs_t *s, uint8_t id, void *buf, uint16_t len);       /* 0 = ok (Laenge muss passen) */
int fl_nvs_write(fl_nvs_t *s, uint8_t id, const void *buf, uint16_t len);
int fl_nvs_delete(fl_nvs_t *s, uint8_t id);

#endif
