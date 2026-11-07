/*
 * fluidi – Ringspeicher fuer Datensaetze im internen Flash (PROTOCOL.md Kap. 6). Plattformneutral.
 *
 * Ablage (Firmware-Detail, ersetzt die ANNAHME "102 Datensaetze je Sektor" in PROTOCOL.md 6.3):
 *  - Bereich FL_LOG_BASE, 12 Sektoren a 2 kB; immer ein Sektor frei zum Loeschen -> 11 nutzbar.
 *  - Sektorkopf 16 Byte: magic "FLG1", gen (u32, steigt je neu begonnenem Sektor), first_seq, CRC16, 0xFFFF.
 *  - Eintrag 24 Byte (4-Byte-ausgerichtet): Datensatz 20 Byte + CRC16 + 0xFFFF. 84 Eintraege je Sektor
 *    -> garantiert 10 x 84 = 840 Datensaetze (bis 924), 8/Tag: >= 105 Tage, 18/Tag: >= 46 Tage
 *    (REQ-LOG-01: 60 Tage bei 6/Tag -> erfuellt; PROTOCOL.md 6.3 nannte 1122 als ANNAHME).
 *  - Jeder Eintrag wird genau einmal geschrieben (DS S.21 Tab. 7.11: max. 83 Schreibvorgaenge je 256-B-Zeile;
 *    hier <= 11 je Zeile). Quittungen und Zaehler stehen NICHT im Ring, sondern im NV (fl_log_meta_t).
 *  - Stromausfall waehrend Schreiben: Eintrag mit falscher CRC wird uebersprungen; seq kommt aus dem Eintrag.
 */
#ifndef FL_RINGLOG_H
#define FL_RINGLOG_H
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include "fl_proto.h"

typedef struct {
    int (*read)(void *ctx, uint32_t off, void *buf, size_t len);
    int (*write)(void *ctx, uint32_t off, const void *buf, size_t len);
    int (*erase)(void *ctx, uint32_t off);           /* loescht den Sektor, in dem off liegt */
    void *ctx;
    uint32_t size;                                   /* Bereichsgroesse */
    uint32_t sector;                                 /* Sektorgroesse */
} fl_flash_t;

/* Nichtfluechtige Metadaten (NV-Element, vom Aufrufer gespeichert) */
typedef struct {
    uint32_t acked_upto;      /* alle seq <= acked_upto quittiert; 0xFFFFFFFF = noch keine */
    uint32_t visible_from;    /* seq < visible_from gelten als geloescht (Werkseinstellung) */
    uint32_t lost_records;
    uint32_t seq_floor;       /* naechste seq ist mindestens dieser Wert (ueberdauert Loeschen des Rings) */
} fl_log_meta_t;

#define FL_LOG_MAX_SECT   16
#define FL_LOG_HDR        16u
#define FL_LOG_ENTRY      24u

typedef struct {
    const fl_flash_t *f;
    fl_log_meta_t *meta;
    uint32_t n_sect, per_sect;
    uint32_t gen[FL_LOG_MAX_SECT];        /* 0 = Sektor leer/ungueltig */
    uint32_t first_seq[FL_LOG_MAX_SECT];
    uint32_t max_seq[FL_LOG_MAX_SECT];    /* hoechste gueltige seq im Sektor */
    uint16_t used[FL_LOG_MAX_SECT];       /* belegte Slots (inkl. defekter) */
    uint32_t cur;                         /* aktueller Schreibsektor */
    uint32_t next_seq;
    bool     any;                         /* mindestens ein Datensatz vorhanden */
} fl_log_t;

int fl_log_init(fl_log_t *l, const fl_flash_t *f, fl_log_meta_t *meta);
/* Datensatz anhaengen: r->seq wird vergeben. *overwritten = Anzahl unquittiert ueberschriebener Datensaetze.
 * Rueckgabe 0 = ok, sonst FL_E_FLASH_FAIL. Der Aufrufer speichert danach meta (lost_records). */
int fl_log_append(fl_log_t *l, fl_record_t *r, uint32_t *overwritten);
/* Datensatz mit seq lesen. Rueckgabe 0 = gefunden. */
int fl_log_read(fl_log_t *l, uint32_t seq, fl_record_t *r);
/* Naechsten vorhandenen Datensatz mit seq >= from finden (Luecken durch Ueberschreiben/defekte Eintraege) */
int fl_log_next(fl_log_t *l, uint32_t from, fl_record_t *r);
uint32_t fl_log_last_seq(const fl_log_t *l);          /* 0xFFFFFFFF = keiner */
uint32_t fl_log_oldest_unacked(const fl_log_t *l);    /* = last+1, wenn keiner offen */
bool fl_log_pending(const fl_log_t *l);
void fl_log_ack(fl_log_t *l, uint32_t upto);          /* aendert meta, Aufrufer speichert */
void fl_log_factory_clear(fl_log_t *l);               /* Inhalt unsichtbar, seq bleibt */
uint16_t fl_log_capacity(const fl_log_t *l);

#endif
