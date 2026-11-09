/*
 * fluidi – Anwendungslogik Sensor (plattformneutral): Zustandsautomat, Sitzung/Kopplung nach PROTOCOL.md,
 * Messplan, Ringspeicher, LED/Taster, Unterspannung, Ladungsschaetzung, OTA-Bestaetigung.
 * Die Plattform ruft die fl_app_on_*-Funktionen aus EINEM Task auf und schlaeft bis zur gelieferten Frist.
 */
#ifndef FL_APP_H
#define FL_APP_H
#include <stdint.h>
#include <stdbool.h>
#include "fl_settings.h"
#include "fl_ringlog.h"
#include "fl_ui.h"
#include "fl_ota.h"

typedef enum { FL_MODE_UNPAIRED = 0, FL_MODE_PAIRING, FL_MODE_NORMAL, FL_MODE_UNDERVOLTAGE } fl_mode_t;

typedef enum {
    FL_SESS_NONE = 0, FL_SESS_WAIT_HELLO, FL_SESS_SECURE_WAIT, FL_SESS_SECURE,
    FL_SESS_PAIR_RSP_SENT,   /* PAIR_RSP gesendet, warte auf PAIR_REVEAL (v2) */
    FL_SESS_PAIR_SHOWING,    /* Farbfolge, warte auf Taster + PAIR_CONFIRM_G */
    FL_SESS_CLOSING
} fl_sess_state_t;

/* nichtfluechtige Zaehler (FL_NV_COUNTERS) */
typedef struct {
    uint16_t boot_id;
    uint16_t wdt_resets, brownouts, auth_fail, button_stuck;
    uint8_t  last_error, ota_result;
    uint8_t  ota_expect;                 /* 1 = Update angestossen, Ergebnis beim naechsten Start bewerten */
    uint8_t  pad;
    uint8_t  ota_ver[4];
    uint32_t ota_build;
    uint32_t charge_uc;                  /* S-5: nichtfluechtig, Nullung nur bei Power-on (Zellwechsel) */
    uint16_t backoffs;                   /* F-W3: Abschaltungen wegen Reset-Schleife */
    uint16_t pad2;
} fl_counters_t;

/* Bits im Retention-Register (PMCTL.AONRSTA1, 18 bit, ueberlebt Reset und Shutdown, nicht Power-on; TRM 8.4.2).
 * VDDS-Brownout: TRM widerspruechlich (S. 265 Kap. 6.8 gegen S. 419 Tab. 8-1) -> PROTOTYP-PRUEFUNG mit TF-4 */
#define FL_RET_ABN_MASK   0x0Fu      /* Zaehler aufeinanderfolgender abnormaler Neustarts (F-W3) */
#define FL_RET_PLANNED    0x10u      /* gewollter Neustart (REBOOT, OTA, Werkseinstellung, Rueckfall) */
#define FL_RET_UV         0x20u      /* Abschaltung wegen Unterspannung */
#define FL_RET_BACKOFF    0x40u      /* Abschaltung wegen Reset-Schleife */
/* O-5: Ausnahme (HardFault, NMI, nicht registrierter Interrupt) -> fl_fault_handler (platform/cc23/fl_hw.c) setzt
 * dieses Bit, loescht FL_RET_PLANNED und loest sofort einen Systemreset aus (PMCTL.RSTCTL.SYSRST -> Neustartgrund
 * PMCTL_RESET_SYSTEM = FL_RR_SOFTWARE). fl_app_init meldet diesen Start als FL_RR_HARDFAULT und loescht das Bit.
 * Bit 13: Bits 7..12 und 14..17 gehoeren der Testfirmware (fl_testfw.h, FL_TF_RET_ALL). Aeltere Serienfirmware
 * loescht Bit 13 beim Start (newret = abn) und wertet den Neustart als ungeplanten Software-Reset = abnormal. */
#define FL_RET_FAULT      0x2000u
#define FL_ABN_MAX        3u
#define FL_STABLE_MS      (10u * 60000u)

/* Kopplungsdaten (FL_NV_PAIR); Schluesselbereich mit Zufallsbyte aufgefuellt (PROTOCOL.md 4.6) */
typedef struct {
    uint8_t paired;
    uint8_t gateway_id[8];
    uint8_t k_link[16];
    uint8_t fill[39];
} fl_pairing_t;

typedef struct { uint8_t code, detail; uint16_t boot_id; uint32_t uptime_s; } fl_diag_entry_t;
typedef struct { uint8_t head, count; uint8_t pad[2]; fl_diag_entry_t e[16]; } fl_diag_t;

typedef struct {
    /* Konfiguration / Persistenz */
    fl_settings_t set;
    fl_pairing_t pair;
    fl_counters_t cnt;
    fl_diag_t diag;
    fl_log_meta_t logmeta;
    fl_log_t log;
    uint8_t addr[6];
    uint8_t fw_ver[4];
    uint32_t fw_build;
    uint8_t reset_reason;

    /* Zustand */
    fl_mode_t mode, mode_before_pairing;
    uint32_t pairing_until;
    bool locked; uint32_t locked_until;
    uint8_t fail_streak, timeout_streak;
    bool stable_done;
    uint32_t sec_cnt;
    uint32_t last_charge_save;
    bool meas_pending; uint8_t meas_pending_cause;   /* F-W5: Messung erst nach dem Trennen */
    bool error_active, batt_low, water;
    uint8_t low_count, uv_count;
    uint16_t vbat_load, vbat_rest;
    bool last_meas_ok, tmp_ok;
    uint32_t last_contact_ms; bool had_contact;
    uint32_t fast_adv_until;
    uint32_t next_meas_ms, next_minute_ms, minute_counter;
    uint32_t meas_count, adv_count, conn_count;
    uint32_t charge_uc, charge_ref_ms;
    bool image_test; uint32_t test_deadline_ms; bool ota_confirmed_now;
    uint32_t reboot_at; bool reboot_pending;
    bool stuck; uint32_t stuck_check_ms;

    /* Zeit */
    bool time_valid; int64_t unix_offset_ms; int16_t tz_min; uint32_t time_set_ms;

    /* Taster-Messung: Anzeige "gesendet/gepuffert" */
    bool btn_wait; uint32_t btn_seq; uint32_t btn_deadline;
    fl_led_pattern_t after_disc_led;

    /* Advertising (zuletzt gesetzt) */
    uint8_t adv_state_set; uint16_t adv_vbat_set; uint32_t adv_seq_set, adv_int_set;
    bool adv_conn_set, adv_on_set, adv_valid;

    /* Verbindung / Sitzung */
    bool connected;
    fl_sess_state_t sess;
    uint32_t t_conn, t_last_rx, t_cccd, t_pair_start;
    bool cccd_on;
    uint8_t k_s[16];
    uint32_t ctr_rx, ctr_tx;
    bool authed, ota_in_session;
    /* Datensatzstrom */
    bool stream; uint8_t stream_rid; uint32_t stream_next; uint32_t stream_left;
    uint8_t txq[3][247]; uint16_t txq_len[3]; uint8_t txq_n;      /* Frames, die auf freien BLE-Puffer warten */
    /* Kopplung */
    uint8_t pr_req[104], pr_rsp[91], transcript[32], k_link_new[16], k_conf[16], gw_id_new[8], z_pair[32];
    uint8_t sas[5];
    bool pair_user_ok, pair_gw_ok;
    uint32_t pair_deadline;

    fl_led_t led;
    fl_btn_t btn;
    fl_ota_t ota;
} fl_app_t;

extern fl_app_t g_fl;

bool     fl_app_early(void);   /* frueh, vor BLE-Init: Neustartgrund, IO-Freigabe, Reset-Schleifen-Zaehler (W-2);
                                * true = abgeschaltet (Hardware: kehrt nicht zurueck). fl_app_init ruft es selbst,
                                * falls noch nicht geschehen. */
void     fl_app_init(void);
void     fl_app_on_connect(void);
void     fl_app_on_notify_enabled(void);    /* CCCD von TX auf Notify geschrieben (K-1) */
void     fl_app_on_disconnect(void);
void     fl_app_on_rx(const uint8_t *data, uint16_t len);
void     fl_app_on_button(bool pressed);
void     fl_app_on_tx_ready(void);
void     fl_app_on_adv_event(void);
/* Faellige Arbeit erledigen; Rueckgabe: ms bis zur naechsten Frist (Plattform schlaeft so lange oder bis Ereignis) */
uint32_t fl_app_process(void);

/* fuer Tests */
int      fl_app_measure(uint8_t cause, fl_record_t *rec);
void     fl_app_factory_reset(void);
uint8_t  fl_app_state_bits(void);
size_t   fl_app_session_info(uint8_t *out, bool extended);

#endif
