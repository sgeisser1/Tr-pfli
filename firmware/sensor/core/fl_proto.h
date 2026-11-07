/*
 * fluidi – Protokoll-Kodierung nach firmware/PROTOCOL.md (Protokollversion 1). Plattformneutral.
 *
 * Praezisierung (Firmware Welle 2, ANNAHME bis Pruefung durch Software-Agent): `sensor_addr` (6 Byte) wird
 * ueberall (PAIR_RSP, HKDF-info, CCM-Nonce) in BLE-Link-Layer-Reihenfolge uebertragen, d. h. niederwertigstes
 * Byte zuerst (Adresse 80:6F:B0:12:AB:CD -> CD AB 12 B0 6F 80), so wie TI-Stack und NimBLE sie speichern.
 */
#ifndef FL_PROTO_H
#define FL_PROTO_H
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#define FL_PROTO_VERSION        2   /* v2 (PROTOCOL.md 0.2): Kopplung mit Commitment/Reveal (VETO F-K1) */
#define FL_ADV_FMT              1
#define FL_INFO_FMT             1
#define FL_REC_FMT              1

/* Frame-Typen (Kap. 5.1) */
#define FL_FT_HELLO             0x0
#define FL_FT_HELLO_RSP         0x1
#define FL_FT_SECURE            0x2
#define FL_FT_PAIR              0x3
#define FL_FT_ERROR             0xF
#define FL_VT(t)                ((uint8_t)((FL_PROTO_VERSION << 4) | (t)))

/* PAIR-Nachrichten (Kap. 5.2) */
#define FL_PAIR_REQ             0x01
#define FL_PAIR_RSP             0x02
#define FL_PAIR_REVEAL          0x03   /* v2: ersetzt PAIR_SHOW, Nutzlast gw_nonce[16] */
#define FL_PAIR_CONFIRM_S       0x04
#define FL_PAIR_CONFIRM_G       0x05
#define FL_PAIR_DONE            0x06
#define FL_PAIR_REQ_LEN         104  /* gateway_id[8] . gw_pub[64] . commit[32] */
#define FL_PAIR_RSP_LEN         91
#define FL_PAIR_REVEAL_LEN      16

/* Nachrichten in SECURE-Frames (Kap. 5.4) */
#define FL_MSG_SESSION_INFO     0x01
#define FL_MSG_GET_INFO         0x10
#define FL_MSG_TIME_SET         0x11
#define FL_MSG_READ_RECORDS     0x12
#define FL_MSG_ACK_RECORDS      0x13
#define FL_MSG_MEASURE          0x14
#define FL_MSG_GET_SETTINGS     0x15
#define FL_MSG_SET_SETTINGS     0x16
#define FL_MSG_IDENTIFY         0x17
#define FL_MSG_GET_DIAG         0x18
#define FL_MSG_CLEAR_DIAG       0x19
#define FL_MSG_OTA_BEGIN        0x20
#define FL_MSG_OTA_DATA         0x21
#define FL_MSG_OTA_END          0x22
#define FL_MSG_OTA_ABORT        0x23
#define FL_MSG_REBOOT           0x30
#define FL_MSG_UNPAIR           0x31
#define FL_MSG_ERR_RSP          0xFF
#define FL_RSP(m)               ((uint8_t)((m) | 0x80))

/* Fehlercodes (Kap. 11) */
enum {
    FL_OK = 0x00, FL_E_UNKNOWN_CMD = 0x01, FL_E_BAD_LENGTH = 0x02, FL_E_BAD_PARAM = 0x03, FL_E_BUSY = 0x04,
    FL_E_NOT_PAIRED = 0x05, FL_E_AUTH_FAIL = 0x06, FL_E_BAD_COUNTER = 0x07, FL_E_PROTO_VERSION = 0x08,
    FL_E_TIMEOUT = 0x09, FL_E_NOT_ALLOWED = 0x0A, FL_E_LOCKED = 0x0B,
    FL_E_MEAS_OSC_FAIL = 0x20, FL_E_MEAS_RANGE = 0x21, FL_E_TEMP_FAIL = 0x22, FL_E_MEAS_NOISY = 0x23,
    FL_E_MEAS_LOW_BATT = 0x24,
    FL_E_FLASH_FAIL = 0x30, FL_E_LOG_OVERWRITTEN = 0x31, FL_E_NVS_RESTORED = 0x32,
    FL_E_OTA_BATT_LOW = 0x40, FL_E_OTA_TOO_LARGE = 0x41, FL_E_OTA_BAD_OFFSET = 0x42, FL_E_OTA_HASH = 0x43,
    FL_E_OTA_SIGNATURE = 0x44, FL_E_OTA_ROLLBACK = 0x45, FL_E_OTA_FLASH = 0x46, FL_E_OTA_ABORTED = 0x47,
    FL_E_OTA_NOT_STARTED = 0x48, FL_E_OTA_REVERTED = 0x49, FL_E_OTA_HW_MISMATCH = 0x4A,
    FL_E_WDT_RESET = 0x50, FL_E_BROWNOUT = 0x51, FL_E_HARDFAULT = 0x52, FL_E_BUTTON_STUCK = 0x53,
    FL_E_LFXT_FAIL = 0x54, FL_E_UNDERVOLTAGE = 0x55
};

/* state-Bitfeld (Kap. 2.4) */
#define FL_ST_PAIRED            0x01
#define FL_ST_PAIRING           0x02
#define FL_ST_DATA_PENDING      0x04
#define FL_ST_BATT_LOW          0x08
#define FL_ST_ERROR             0x10
#define FL_ST_OTA_TEST          0x20
#define FL_ST_LOCKED            0x40
#define FL_ST_TIME_UNSYNCED     0x80

/* reset_reason (Kap. 5.5) */
enum { FL_RR_POWER_ON = 0, FL_RR_PIN = 1, FL_RR_WATCHDOG = 2, FL_RR_SOFTWARE = 3, FL_RR_BROWNOUT = 4,
       FL_RR_HARDFAULT = 5, FL_RR_UNDERVOLTAGE = 6 };

/* Datensatz (Kap. 5.6), 20 Byte */
#define FL_REC_LEN              20
#define FL_C_INVALID            0xFFFFu
#define FL_TEMP_INVALID         ((int16_t)0x8000)
enum { FL_CAUSE_AUTO = 0, FL_CAUSE_BUTTON = 1, FL_CAUSE_GATEWAY = 2, FL_CAUSE_CAL_DRY = 3, FL_CAUSE_CAL_WET = 4,
       FL_CAUSE_DIAG = 5 };
#define FL_RF_OUTLIER           0x01
#define FL_RF_NOISY             0x02
#define FL_RF_AIR               0x04
#define FL_RF_FLOOD             0x08
#define FL_RF_TEMP_INVALID      0x10
#define FL_RF_CHAIN_FAULT       0x20

typedef struct {
    uint32_t seq;
    uint16_t boot_id;
    uint32_t uptime_s;
    uint16_t c_probe;   /* 0.01 pF */
    uint16_t c_diag;    /* 0.01 pF, 0xFFFF = nicht gemessen */
    int16_t temp;       /* 0.01 degC */
    uint16_t vbat_mv;
    uint8_t cause;
    uint8_t flags;
} fl_record_t;

void fl_record_encode(const fl_record_t *r, uint8_t out[FL_REC_LEN]);
void fl_record_decode(const uint8_t in[FL_REC_LEN], fl_record_t *r);

/* Advertising (Kap. 2.3/2.4) */
#define FL_ADV_LEN              29
#define FL_COMPANY_ID           0xFFFFu
void fl_device_name(const uint8_t addr_le[6], char out[12]);    /* "fluidi-XXXX\0" */
size_t fl_adv_build(uint8_t out[31], const uint8_t addr_le[6], uint8_t state, uint16_t vbat_mv,
                    uint32_t seq_last, const uint8_t gw_hint[2]);
void fl_gw_hint(const uint8_t gateway_id[8], uint8_t out[2]);

/* Kopplung (Kap. 4.2, v2 mit Commitment) */
void fl_pair_commit(const uint8_t gateway_id[8], const uint8_t gw_pub[64], const uint8_t gw_nonce[16], uint8_t c[32]);
void fl_pair_transcript(const uint8_t req_payload[FL_PAIR_REQ_LEN], const uint8_t rsp_payload[FL_PAIR_RSP_LEN],
                        const uint8_t gw_nonce[FL_PAIR_REVEAL_LEN], uint8_t out[32]);
void fl_pair_keys(const uint8_t z[32], const uint8_t gw_nonce[16], const uint8_t s_nonce[16],
                  const uint8_t gateway_id[8], const uint8_t sensor_addr[6], uint8_t k_link[16], uint8_t k_conf[16]);
void fl_pair_sas(const uint8_t transcript[32], uint8_t digits[5]);   /* 0 rot, 1 gruen, 2 gelb */
void fl_pair_confirm_mac(const uint8_t k_conf[16], char who, const uint8_t transcript[32], uint8_t mac[16]);

/* Sitzung (Kap. 4.3/4.4) */
#define FL_MIC_LEN              8
#define FL_SECURE_OVERHEAD      15   /* vt + ctr + msg + rid + MIC */
void fl_session_key(const uint8_t k_link[16], const uint8_t gw_nonce[8], const uint8_t s_nonce[8], uint8_t k_s[16]);
/* SECURE-Frame bauen: out muss >= 15 + plen Byte fassen. Rueckgabe Laenge oder -1. */
int fl_secure_seal(const uint8_t k_s[16], uint8_t dir, uint32_t ctr, const uint8_t sensor_addr[6],
                   uint8_t msg, uint8_t rid, const uint8_t *payload, size_t plen, uint8_t *out);
/* SECURE-Frame oeffnen: prueft vt, ctr == expect_ctr und MIC. plain erhaelt msg|rid|payload (len-15+2 Byte).
 * Rueckgabe: Klartextlaenge (>= 2) oder -FL_E_* */
int fl_secure_open(const uint8_t k_s[16], uint8_t dir, uint32_t expect_ctr, const uint8_t sensor_addr[6],
                   const uint8_t *frame, size_t len, uint8_t *plain);

/* Variante fuer W-2 (OTA_DATA per Write Without Response): akzeptiert ctr in [min_ctr, min_ctr + max_gap];
 * *ctr_out = empfangener Zaehler. Der Aufrufer MUSS pruefen, dass eine Luecke nur bei msg = OTA_DATA vorkommt. */
int fl_secure_open_ge(const uint8_t k_s[16], uint8_t dir, uint32_t min_ctr, uint32_t max_gap, const uint8_t sensor_addr[6],
                      const uint8_t *frame, size_t len, uint8_t *plain, uint32_t *ctr_out);

#define FL_DIR_G2S              0x00
#define FL_DIR_S2G              0x01

#endif
