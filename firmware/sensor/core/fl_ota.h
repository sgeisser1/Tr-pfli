/*
 * fluidi – OTA-Empfang in Slot 1 (PROTOCOL.md Kap. 9.3/9.4). Plattformneutral; Flash ueber fl_flash_t,
 * MCUboot-Markierung ueber Port. Pruefung von Signatur und Sicherheitszaehler macht MCUboot beim Neustart.
 */
#ifndef FL_OTA_H
#define FL_OTA_H
#include <stdint.h>
#include <stdbool.h>
#include "fl_crypto.h"
#include "fl_ringlog.h"

#define FL_OTA_WINDOW      16
#define FL_OTA_CHUNK_MAX   224
#define FL_OTA_RESUME_MS   (24u * 3600u * 1000u)

typedef struct {
    bool active;          /* Uebertragung laeuft oder kann fortgesetzt werden */
    uint32_t size, next_off, erased_to, since_progress, t_begin;
    uint8_t sha[32], version[4];
    uint32_t build, sec_cnt;
    uint8_t status;       /* letzter Fehlerstatus fuer OTA_PROGRESS */
    fl_sha256_ctx h;
    const fl_flash_t *f;
} fl_ota_t;

/* OTA_BEGIN-Nutzlast pruefen/annehmen. rsp: status u8, resume_offset u32, window u8, chunk_max u8 (7 Byte). */
int  fl_ota_begin(fl_ota_t *o, const fl_flash_t *f, const uint8_t *p, size_t len, const uint8_t run_ver[4],
                  uint32_t run_build, bool batt_ok, uint32_t now_ms, uint8_t chunk_max, uint8_t rsp[7]);
/* OTA_DATA: Rueckgabe 1 = Fortschrittsmeldung faellig (prog: next_offset u32, status u8). */
int  fl_ota_data(fl_ota_t *o, const uint8_t *p, size_t len, uint8_t prog[5]);
/* OTA_END: Rueckgabe Status (0 = Image vollstaendig, SHA ok). */
uint8_t fl_ota_end(fl_ota_t *o, const uint8_t *p, size_t len);
void fl_ota_abort(fl_ota_t *o);
/* Kopf und geschuetzte TLVs eines MCUboot-Images im Flash lesen (W-6, F-L1) */
#define FL_TLV_SEC_CNT   0x50
#define FL_TLV_HW_REV    0xA0      /* fluidi: Platinenrevision, geschuetztes TLV (imgtool --custom-tlv 0xA0) */
typedef struct {
    bool valid;
    uint8_t ver[4];               /* major, minor, patch u16 LE (wie fw_ver) */
    uint32_t build, sec_cnt, img_size;
    int16_t hw_rev;               /* -1 = nicht vorhanden */
} fl_img_info_t;
int fl_img_parse(const fl_flash_t *f, uint32_t base, fl_img_info_t *info);
/* Pruefung nach OTA_END: Kopf gueltig, Version > laufend, Sicherheitszaehler >= laufend, hw_rev passt.
 * Rueckgabe 0 oder FL_E_OTA_*. */
uint8_t fl_ota_check_image(const fl_flash_t *f, const uint8_t run_ver[4], uint32_t run_build, uint32_t run_sec_cnt,
                           uint8_t hw_rev);

/* Version a > b ? (major.minor.patch, dann build) */
bool fl_ver_newer(const uint8_t a[4], uint32_t ab, const uint8_t b[4], uint32_t bb);

#endif
