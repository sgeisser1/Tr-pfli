/* fluidi – Anwendungslogik Sensor (siehe fl_app.h). Kapitelverweise auf firmware/PROTOCOL.md. */
#include "fl_app.h"
#include "fl_port.h"
#include "fl_proto.h"
#include "fl_crypto.h"
#include "fl_meas.h"
#include "fl_util.h"
#include "../config/fluidi_board.h"

fl_app_t g_fl;
#define A (&g_fl)

/* ---- Konstanten ---- */
/* Fristen v2 (PROTOCOL 0.2 Kap. 3, Befunde K-1/K-2/W-9 Software-Pruefung): gateway-tauglich fuer BlueZ/bleak */
#define HELLO_AFTER_CCCD_MS    1000u         /* HELLO/PAIR_REQ nach CCCD-Write */
#define HELLO_ABS_MS           5000u         /* absolute Grenze ab Verbindungsaufbau (Dienstsuche BlueZ) */
#define IDLE_TIMEOUT_MS        5000u
#define IDLE_TIMEOUT_OTA_MS    30000u
#define SESSION_MAX_MS         30000u        /* ohne OTA/Kopplung */
#define PAIRING_MODE_MS        120000u       /* Kap. 2.1 */
#define PAIR_STEP_MS           15000u        /* PAIR_REQ -> REVEAL (ECDH am Gateway) */
#define PAIR_CONFIRM_MS        60000u        /* Kap. 4.2: Farbvergleich */
#define PAIR_TOTAL_MS          90000u        /* gesamte Kopplungsverbindung */
#define LOCK_MS                (30u * 60000u) /* Kap. 4.5 */
#define LOCK_AFTER_FAILS       3u            /* nur kryptografische Fehler */
#define LOCK_AFTER_TIMEOUTS    10u           /* Fristueberschreitungen (Energieschutz, ohne Gateway-Selbstaussperrung) */
#define FAST_ADV_MS            2000u
#define FAST_ADV_INT_MS        100u
#define PAIR_ADV_INT_MS        500u
#define OFFLINE_AFTER_MS       (24u * 3600u * 1000u)
#define BTN_RESULT_MS          10000u        /* L1/L2: Gateway innert 10 s */
#define STUCK_CHECK_MS         60000u
#define TEST_CONFIRM_MS        (24u * 3600u * 1000u)  /* Kap. 9.5 */
#define UV_MV                  2400u         /* CONCEPTS E1 */
#define UV_HARD_MV             2300u         /* sofort (ANNAHME) */
#define UV_RECOVER_MV          2600u         /* Hysterese nach Unterspannung, Ruhewert (ANNAHME) */
#define BATT_LOW_FALLBACK_MV   2550u         /* Kap. 8 (ANNAHME) */
#define CELL_USABLE_UC         607500000u    /* 225 mAh x 0.75 (Kap. 9.2, CR2032 A-32) */
/* Ladung je Ereignis (uC) fuer charge_uc (REQ-ENE-05), aus scripts/energy_budget.py "real" (PROTOCOL Kap. 12);
 * Messung Rev B (FW-1/FW-2): 4 Bursts x 0.6 ms x 12.8 mA (Kette + CPU, PINMAP FW-2) = 31 uC
 * + TMP-Wandlung 15 ms CPU im Schlaf + I2C/Auswertung ~3 ms x 2.6 mA ~ 10 uC + 4 x Aufwachen -> ~50 uC (ANNAHME) */
#define Q_ADV_UC               16u
#define Q_CONN_UC              299u
#define Q_MEAS_UC              50u
#define I_SLEEP_NA             1000u         /* 0.74 uA Standby (DS S.19) + Leck/Rest ~0.26 uA (ANNAHME) */

#define NONE32 0xFFFFFFFFu

static bool due(uint32_t now, uint32_t t) { return (int32_t)(now - t) >= 0; }
static void dl_min(uint32_t *best, uint32_t now, uint32_t t, bool active)
{
    if (!active) return;
    uint32_t d = due(now, t) ? 0 : t - now;
    if (d < *best) *best = d;
}

/* ---------------- Persistenz ---------------- */
/* N-2: waehrend des Starts bis zur ersten bestandenen Lastmessung wird nichts ins NV geschrieben */
static bool s_nv_defer;
static void save_counters(void) { if (!s_nv_defer) fl_port_nv_write(FL_NV_COUNTERS, &A->cnt, sizeof A->cnt); }
static void save_logmeta(void) { if (!s_nv_defer) fl_port_nv_write(FL_NV_LOGMETA, &A->logmeta, sizeof A->logmeta); }
static void save_settings(void) { if (!s_nv_defer) fl_port_nv_write(FL_NV_SETTINGS, &A->set, sizeof A->set); }
static void save_diag(void) { if (!s_nv_defer) fl_port_nv_write(FL_NV_DIAG, &A->diag, sizeof A->diag); }

static void diag_add(uint8_t code, uint8_t detail)
{
    fl_diag_entry_t *e = &A->diag.e[A->diag.head];
    uint16_t frac;
    e->code = code; e->detail = detail; e->boot_id = A->cnt.boot_id;
    fl_port_uptime(&e->uptime_s, &frac);
    A->diag.head = (uint8_t)((A->diag.head + 1) % 16);
    if (A->diag.count < 16) A->diag.count++;
    A->cnt.last_error = code;
    if ((code >= 0x20 && code <= 0x32) || (code >= 0x50 && code <= 0x55)) A->error_active = true;
    save_diag();
    save_counters();
}

/* ---------------- Zeit ---------------- */
static int64_t local_ms(uint32_t now)
{
    return (int64_t)now + A->unix_offset_ms + (int64_t)A->tz_min * 60000;
}
static uint16_t minute_of_day(uint32_t now)
{
    int64_t m = local_ms(now) / 60000;
    m %= 1440; if (m < 0) m += 1440;
    return (uint16_t)m;
}

static void schedule_meas(uint32_t now)
{
    uint32_t iv = A->set.meas_interval_s * 1000u;
    if (A->time_valid) {
        /* Vielfache von meas_interval ab Mitternacht Lokalzeit + Versatz sensor_addr mod 300 s (Kap. 7) */
        uint32_t addr = (uint32_t)A->addr[0] | ((uint32_t)A->addr[1] << 8) | ((uint32_t)A->addr[2] << 16);
        int64_t off = (int64_t)(addr % 300u) * 1000;
        int64_t day0 = local_ms(now) - (int64_t)minute_of_day(now) * 60000 - (local_ms(now) % 60000);
        int64_t t = day0 + off;
        while (t <= local_ms(now) + 1000) t += iv;
        A->next_meas_ms = now + (uint32_t)(t - local_ms(now));
    } else {
        A->next_meas_ms = now + iv;
    }
}

/* ---------------- Zustand / Advertising ---------------- */
uint8_t fl_app_state_bits(void)
{
    uint8_t s = 0;
    if (A->pair.paired) s |= FL_ST_PAIRED;
    if (A->mode == FL_MODE_PAIRING) s |= FL_ST_PAIRING;
    if (fl_log_pending(&A->log)) s |= FL_ST_DATA_PENDING;
    if (A->batt_low) s |= FL_ST_BATT_LOW;
    if (A->error_active) s |= FL_ST_ERROR;
    if (A->image_test) s |= FL_ST_OTA_TEST;
    if (A->locked) s |= FL_ST_LOCKED;
    if (!A->time_valid) s |= FL_ST_TIME_UNSYNCED;
    return s;
}

static void update_adv(uint32_t now)
{
    bool on = false, conn = true;
    uint32_t iv = A->set.adv_interval_ms;
    if (A->connected || A->mode == FL_MODE_UNDERVOLTAGE) on = false;
    else if (A->mode == FL_MODE_PAIRING) { on = true; iv = PAIR_ADV_INT_MS; }
    else if (A->pair.paired) {
        on = true;
        if (A->locked) conn = false;
        else if (!due(now, A->fast_adv_until)) iv = FAST_ADV_INT_MS;
        else if (A->had_contact ? (now - A->last_contact_ms) > OFFLINE_AFTER_MS : false) iv = A->set.adv_interval_offline_ms;
    }
    uint8_t st = fl_app_state_bits();
    uint32_t last = fl_log_last_seq(&A->log);
    if (A->adv_valid && on == A->adv_on_set && conn == A->adv_conn_set && iv == A->adv_int_set &&
        st == A->adv_state_set && A->vbat_load == A->adv_vbat_set && last == A->adv_seq_set) return;
    uint8_t d[31], hint[2] = {0, 0};
    if (A->pair.paired) fl_gw_hint(A->pair.gateway_id, hint);
    size_t n = fl_adv_build(d, A->addr, st, A->vbat_load, last, hint);
    fl_port_adv_set(d, (uint8_t)n, iv, conn, on);
    A->adv_valid = true; A->adv_on_set = on; A->adv_conn_set = conn; A->adv_int_set = iv;
    A->adv_state_set = st; A->adv_vbat_set = A->vbat_load; A->adv_seq_set = last;
}

/* ---------------- Batterie ---------------- */
static void enter_undervoltage(void)
{
    diag_add(FL_E_UNDERVOLTAGE, 0);
    A->cnt.charge_uc = A->charge_uc;
    save_counters(); save_logmeta();
    fl_port_retained_set(fl_port_retained_get() | FL_RET_UV);   /* naechster Start meldet reset_reason 6 */
    A->mode = FL_MODE_UNDERVOLTAGE;
    fl_port_adv_set(NULL, 0, 0, false, false);
    fl_led_stop(&A->led); fl_port_led(FL_COL_OFF, 0);
    fl_port_shutdown();
}

static void check_battery(uint16_t vload)
{
    if (!vload) return;
    A->vbat_load = vload;
    if (vload < UV_HARD_MV || (vload < UV_MV && ++A->uv_count >= 2)) { enter_undervoltage(); return; }
    if (vload >= UV_MV) A->uv_count = 0;
    if (vload < BATT_LOW_FALLBACK_MV) { if (A->low_count < 255) A->low_count++; } else A->low_count = 0;
    A->batt_low = A->set.batt_low_flag || A->low_count >= 3;
}

/* ---------------- Messung ---------------- */
int fl_app_measure(uint8_t cause, fl_record_t *rec)
{
    fl_meas_raw_t raw;
    fl_meas_result_t res;
    uint32_t ow = 0;
    if (A->mode == FL_MODE_UNDERVOLTAGE) { diag_add(FL_E_MEAS_LOW_BATT, 0); return FL_E_MEAS_LOW_BATT; }
    memset(&raw, 0, sizeof raw);
    /* F-W5: kein Funk waehrend der Bursts: nur ohne Verbindung (Aufrufer), Advertising fuer die Messdauer aus.
     * N-3: der Stopp ist im Stack asynchron; zwischen Stopp und erstem Burst liegen >= 16 ms (TMP-Wandlung,
     * FLUIDI_TMP_CONV_MS + SENS_PWR 1 ms), ein bereits geplantes ADV-Ereignis (3 Kanaele) ist nach wenigen ms vorbei. */
    if (A->adv_on_set) { fl_port_adv_set(NULL, 0, 0, false, false); A->adv_valid = false; A->adv_on_set = false; }
    bool f2 = FLUIDI_HAS_CREF2 && (cause == FL_CAUSE_DIAG || (A->set.diag_f2 && (A->meas_count % A->set.diag_f2) == 0));
    /* FW-2: max. 4 Bursts -> hoechstens 16 Teilbloecke je Konfiguration */
    uint8_t nb = A->set.avg_count > FL_MEAS_BLOCKS_MAX_FW2 ? FL_MEAS_BLOCKS_MAX_FW2 : A->set.avg_count;
    fl_port_measure(&raw, nb, f2);
    fl_meas_evaluate(&raw, &A->set, FLUIDI_OSC_DIVIDER, &res);
    A->meas_count++;
    A->charge_uc += Q_MEAS_UC;
    A->tmp_ok = raw.temp_ok;
    A->last_meas_ok = !(res.flags & FL_RF_CHAIN_FAULT);
    if (res.error) diag_add(res.error, res.flags);
    memset(rec, 0, sizeof *rec);
    rec->boot_id = A->cnt.boot_id;
    uint16_t frac;
    fl_port_uptime(&rec->uptime_s, &frac);
    rec->c_probe = res.c_probe; rec->c_diag = res.c_diag; rec->temp = res.temp;
    rec->vbat_mv = res.vbat_mv; rec->cause = cause; rec->flags = res.flags;
    check_battery(res.vbat_mv);                          /* N-2: Lastpruefung vor dem Flash-Schreiben */
    if (A->mode == FL_MODE_UNDERVOLTAGE) return FL_E_MEAS_LOW_BATT;
    s_nv_defer = false;
    int rc = fl_log_append(&A->log, rec, &ow);
    if (rc) diag_add(FL_E_FLASH_FAIL, 0);
    if (ow) { diag_add(FL_E_LOG_OVERWRITTEN, ow > 255 ? 255 : (uint8_t)ow); save_logmeta(); }
    A->water = fl_water_needed(res.c_probe, A->set.water_raw);
    return rc;
}

/* ---------------- Senden ---------------- */
static uint16_t max_frame(void) { uint16_t m = fl_port_ble_mtu(); return (uint16_t)((m < 23 ? 23 : m) - 3); }

static bool send_raw(const uint8_t *f, uint16_t len)
{
    if (len > sizeof A->txq[0]) return false;
    if (A->txq_n == 0) {
        int rc = fl_port_ble_send(f, len);
        if (rc == 0) return true;
        if (rc < 0) return false;
    }
    if (A->txq_n >= 3) return false;                 /* Warteschlange voll: Frame verworfen */
    memcpy(A->txq[A->txq_n], f, len); A->txq_len[A->txq_n] = len; A->txq_n++;
    return true;
}

static void send_error(uint8_t code, uint8_t detail, bool with_detail)
{
    uint8_t f[3] = {FL_VT(FL_FT_ERROR), code, detail};
    send_raw(f, with_detail ? 3 : 2);
}

static bool sec_send(uint8_t msg, uint8_t rid, const uint8_t *p, size_t plen)
{
    uint8_t f[256];
    if (plen + FL_SECURE_OVERHEAD > max_frame()) return false;
    int n = fl_secure_seal(A->k_s, FL_DIR_S2G, A->ctr_tx, A->addr, msg, rid, p, plen, f);
    if (n < 0) return false;
    A->ctr_tx++;
    return send_raw(f, (uint16_t)n);
}

static void err_rsp(uint8_t rid, uint8_t code, uint8_t detail)
{
    uint8_t p[2] = {code, detail};
    sec_send(FL_MSG_ERR_RSP, rid, p, 2);
}

static void disconnect(void)
{
    if (A->sess != FL_SESS_CLOSING) { A->sess = FL_SESS_CLOSING; fl_port_ble_disconnect(); }
}

static void planned_reboot(void)
{
    A->cnt.charge_uc = A->charge_uc;
    save_counters(); save_logmeta();
    fl_port_retained_set((fl_port_retained_get() & ~FL_RET_ABN_MASK) | FL_RET_PLANNED);
    if (A->connected) fl_port_ble_disconnect();
    fl_port_reboot();
}

/* Fristueberschreitung: KEIN kryptografischer Fehlversuch (K-1); eigener Zaehler gegen Batterie-Leerziehen */
static void handshake_timeout(void)
{
    diag_add(FL_E_TIMEOUT, 1);
    if (++A->timeout_streak >= LOCK_AFTER_TIMEOUTS) {
        A->locked = true; A->locked_until = fl_port_ms() + LOCK_MS; A->timeout_streak = 0;
        diag_add(FL_E_LOCKED, 1);
    }
    disconnect();
}

/* kryptografischer Fehlversuch (PROTOCOL 4.5): 3 in Folge -> 30 min LOCKED */
static void crypto_fail(uint8_t code, uint8_t detail)
{
    A->cnt.auth_fail++;
    diag_add(code, detail);
    if (++A->fail_streak >= LOCK_AFTER_FAILS) {
        A->locked = true; A->locked_until = fl_port_ms() + LOCK_MS; A->fail_streak = 0;
        diag_add(FL_E_LOCKED, 0);
    }
}

static void handshake_failed(uint8_t code)
{
    crypto_fail(code, 0);
    disconnect();
}

/* ---------------- SESSION_INFO / INFO (Kap. 5.5) ---------------- */
size_t fl_app_session_info(uint8_t *o, bool ext)
{
    uint32_t up; uint16_t frac;
    fl_port_uptime(&up, &frac);
    memset(o, 0, 68);
    o[0] = FL_INFO_FMT;
    memcpy(o + 1, A->fw_ver, 4);
    fl_put_u32(o + 5, A->fw_build);
    o[9] = FLUIDI_HW_REV;
    o[10] = fl_app_state_bits();
    fl_put_u16(o + 11, A->cnt.boot_id);
    fl_put_u32(o + 13, up);
    fl_put_u16(o + 17, frac);
    fl_put_u32(o + 19, fl_log_last_seq(&A->log));
    fl_put_u32(o + 23, fl_log_oldest_unacked(&A->log));
    fl_put_u16(o + 27, A->vbat_load);
    fl_put_u16(o + 29, A->vbat_rest);
    fl_put_u32(o + 31, A->charge_uc);
    fl_put_u16(o + 35, A->set.settings_ver);
    o[37] = A->reset_reason;
    o[38] = A->cnt.last_error;
    o[39] = A->cnt.ota_result;
    o[40] = A->image_test ? 0 : 1;
    o[41] = FL_REC_FMT;
    fl_put_u16(o + 42, fl_log_capacity(&A->log));
    fl_put_u32(o + 44, A->logmeta.lost_records);
    fl_put_u32(o + 48, A->sec_cnt);                     /* v2 (W-6): installierter Sicherheitszaehler */
    if (!ext) return 52;
    fl_put_u32(o + 52, A->meas_count);
    fl_put_u32(o + 56, A->adv_count);
    fl_put_u32(o + 60, A->conn_count);
    fl_put_u32(o + 64, A->led.on_ms_total);
    return 68;
}

/* ---------------- Datensatzstrom (Kap. 5.6) ---------------- */
static void stream_pump(void)
{
    while (A->stream && A->txq_n == 0 && A->connected) {
        uint8_t p[2 + 11 * FL_REC_LEN];
        uint32_t per = (uint32_t)(max_frame() - FL_SECURE_OVERHEAD - 2) / FL_REC_LEN;
        if (per > 11) per = 11;
        if (per == 0) per = 1;
        uint8_t cnt = 0;
        fl_record_t r;
        uint32_t last = fl_log_last_seq(&A->log);
        while (cnt < per && A->stream_left && last != NONE32 && A->stream_next <= last &&
               fl_log_next(&A->log, A->stream_next, &r) == 0) {
            fl_record_encode(&r, p + 2 + cnt * FL_REC_LEN);
            cnt++; A->stream_left--; A->stream_next = r.seq + 1;
        }
        bool more = A->stream_left && last != NONE32 && A->stream_next <= last &&
                    fl_log_next(&A->log, A->stream_next, &r) == 0;
        p[0] = cnt; p[1] = more ? 1 : 0;
        if (!sec_send(FL_RSP(FL_MSG_READ_RECORDS), A->stream_rid, p, 2u + cnt * FL_REC_LEN)) { A->stream = false; break; }
        if (!more) A->stream = false;
    }
}

/* ---------------- Befehle (Kap. 5.4) ---------------- */
static uint8_t cause_of_purpose(uint8_t purpose)
{
    switch (purpose) { case 1: return FL_CAUSE_CAL_DRY; case 2: return FL_CAUSE_CAL_WET; case 3: return FL_CAUSE_DIAG;
                       default: return FL_CAUSE_GATEWAY; }
}

static bool batt_ok_for_ota(void)
{
    uint32_t rest = A->charge_uc >= CELL_USABLE_UC ? 0 : CELL_USABLE_UC - A->charge_uc;
    return A->vbat_load >= A->set.ota_min_mv && rest >= CELL_USABLE_UC / 4u;
}

static void dispatch(uint8_t msg, uint8_t rid, const uint8_t *p, size_t n)
{
    uint8_t r[230];
    uint32_t now = fl_port_ms();
    switch (msg) {
    case FL_MSG_GET_INFO: sec_send(FL_RSP(msg), rid, r, fl_app_session_info(r, true)); break;
    case FL_MSG_TIME_SET:
        if (n < 10) { err_rsp(rid, FL_E_BAD_LENGTH, 0); break; }
        A->unix_offset_ms = (int64_t)fl_get_u64(p) - now;
        A->tz_min = (int16_t)fl_get_u16(p + 8);
        A->time_valid = true; A->time_set_ms = now;
        schedule_meas(now);
        r[0] = 0; sec_send(FL_RSP(msg), rid, r, 1); break;
    case FL_MSG_READ_RECORDS:
        if (n < 6) { err_rsp(rid, FL_E_BAD_LENGTH, 0); break; }
        A->stream = true; A->stream_rid = rid; A->stream_next = fl_get_u32(p);
        A->stream_left = fl_get_u16(p + 4) ? fl_get_u16(p + 4) : NONE32;
        stream_pump(); break;
    case FL_MSG_ACK_RECORDS: {
        if (n < 4) { err_rsp(rid, FL_E_BAD_LENGTH, 0); break; }
        uint32_t upto = fl_get_u32(p);
        fl_log_ack(&A->log, upto);
        save_logmeta();
        if (A->btn_wait && upto >= A->btn_seq) { A->btn_wait = false; A->after_disc_led = FL_LED_L1_SENT; }
        r[0] = 0; fl_put_u32(r + 1, fl_log_oldest_unacked(&A->log));
        sec_send(FL_RSP(msg), rid, r, 5); break; }
    case FL_MSG_MEASURE: {
        /* v2 (F-W5): keine Messung waehrend Funk. Antwort {status, seq} -> Sensor trennt, misst, schnelles
         * Advertising mit DATA_PENDING; das Gateway liest den Datensatz `seq` in der naechsten Sitzung. */
        if (n < 2) { err_rsp(rid, FL_E_BAD_LENGTH, 0); break; }
        if (A->mode == FL_MODE_UNDERVOLTAGE) { r[0] = FL_E_MEAS_LOW_BATT; fl_put_u32(r + 1, NONE32); }
        else {
            A->meas_pending = true; A->meas_pending_cause = cause_of_purpose(p[0]);
            r[0] = 0; fl_put_u32(r + 1, A->log.next_seq);
            if (p[1] == 1) A->after_disc_led = FL_LED_L2_BUFFERED;   /* Quittung gruen 1 x */
        }
        sec_send(FL_RSP(msg), rid, r, 5);
        if (r[0] == 0) A->t_last_rx = now - IDLE_TIMEOUT_MS + 300u;   /* ohne weiteren Frame nach 0.3 s trennen */
        break; }
    case FL_MSG_GET_SETTINGS: sec_send(FL_RSP(msg), rid, r, fl_settings_encode(&A->set, r, sizeof r)); break;
    case FL_MSG_SET_SETTINGS: {
        if (n < 2) { err_rsp(rid, FL_E_BAD_LENGTH, 0); break; }
        uint8_t bad = 0;
        int rc = fl_settings_apply_tlv(&A->set, fl_get_u16(p), p + 2, n - 2, &bad);
        if (rc == 0) { save_settings(); fl_port_tx_power(A->set.tx_power_dbm); schedule_meas(now); A->batt_low = A->set.batt_low_flag || A->low_count >= 3; }
        r[0] = (uint8_t)rc; r[1] = bad; sec_send(FL_RSP(msg), rid, r, 2); break; }
    case FL_MSG_IDENTIFY:
        if (n < 1 || p[0] < 1 || p[0] > 30) { err_rsp(rid, FL_E_BAD_PARAM, 0); break; }
        fl_led_play(&A->led, FL_LED_L16_IDENTIFY, now, A->vbat_load, p[0]);
        r[0] = 0; sec_send(FL_RSP(msg), rid, r, 1); break;
    case FL_MSG_GET_DIAG: {
        size_t k = 0;
        r[k++] = A->diag.count;
        for (uint8_t i = 0; i < A->diag.count; i++) {
            const fl_diag_entry_t *e = &A->diag.e[(A->diag.head + 16 - A->diag.count + i) % 16];
            r[k++] = e->code; r[k++] = e->detail; fl_put_u16(r + k, e->boot_id); k += 2; fl_put_u32(r + k, e->uptime_s); k += 4;
        }
        fl_put_u16(r + k, A->cnt.wdt_resets); fl_put_u16(r + k + 2, A->cnt.brownouts);
        fl_put_u16(r + k + 4, A->cnt.auth_fail); fl_put_u16(r + k + 6, A->cnt.button_stuck); k += 8;
        sec_send(FL_RSP(msg), rid, r, k); break; }
    case FL_MSG_CLEAR_DIAG:
        memset(&A->diag, 0, sizeof A->diag); A->cnt.last_error = 0; A->error_active = false;
        save_diag(); save_counters();
        r[0] = 0; sec_send(FL_RSP(msg), rid, r, 1); break;
    case FL_MSG_OTA_BEGIN: {
        uint16_t chunk = (uint16_t)(max_frame() - FL_SECURE_OVERHEAD - 4);
        int rc = fl_ota_begin(&A->ota, fl_port_slot1_flash(), p, n, A->fw_ver, A->fw_build, batt_ok_for_ota(), now,
                              (uint8_t)(chunk > 224 ? 224 : chunk), r);
        if (rc == 0) A->ota_in_session = true;
        sec_send(FL_RSP(msg), rid, r, 7); break; }
    case FL_MSG_OTA_DATA:
        if (fl_ota_data(&A->ota, p, n, r)) sec_send(FL_RSP(msg), rid, r, 5);
        if (A->vbat_load && A->vbat_load + 200u < A->set.ota_min_mv) {   /* Kap. 9.4 */
            fl_ota_abort(&A->ota); A->cnt.ota_result = FL_E_OTA_BATT_LOW; save_counters(); }
        break;
    case FL_MSG_OTA_END: {
        uint8_t st = fl_ota_end(&A->ota, p, n);
        /* F-L1/W-6: Version, Sicherheitszaehler und hw_rev aus dem Kopf/TLV in Slot 1 pruefen */
        if (st == 0) st = fl_ota_check_image(fl_port_slot1_flash(), A->fw_ver, A->fw_build, A->sec_cnt, FLUIDI_HW_REV);
        if (st != 0 && st != FL_E_OTA_HASH) fl_port_slot1_flash()->erase(fl_port_slot1_flash()->ctx, 0);
        if (st == 0 && fl_port_ota_request_test() != 0) st = FL_E_OTA_FLASH;
        r[0] = st; sec_send(FL_RSP(msg), rid, r, 1);
        if (st == 0) {
            A->cnt.ota_expect = 1; memcpy(A->cnt.ota_ver, A->ota.version, 4); A->cnt.ota_build = A->ota.build;
            A->cnt.charge_uc = A->charge_uc; save_counters(); save_logmeta();
            A->reboot_pending = true; A->reboot_at = now + 1000u;
        } else { A->cnt.ota_result = st; save_counters(); }
        break; }
    case FL_MSG_OTA_ABORT:
        fl_ota_abort(&A->ota); A->cnt.ota_result = FL_E_OTA_ABORTED; save_counters();
        r[0] = 0; sec_send(FL_RSP(msg), rid, r, 1); break;
    case FL_MSG_REBOOT:
        r[0] = 0; sec_send(FL_RSP(msg), rid, r, 1);
        save_counters(); save_logmeta();
        A->reboot_pending = true; A->reboot_at = now + (n ? p[0] : 0) * 1000u + 200u; break;
    case FL_MSG_UNPAIR:
        r[0] = 0; sec_send(FL_RSP(msg), rid, r, 1);
        fl_wipe(&A->pair, sizeof A->pair); fl_port_nv_delete(FL_NV_PAIR);
        fl_settings_user_defaults(&A->set); save_settings();
        A->mode = FL_MODE_UNPAIRED; A->after_disc_led = FL_LED_UNPAIRED_2Y;
        disconnect(); break;
    default: err_rsp(rid, FL_E_UNKNOWN_CMD, msg); break;
    }
}

/* ---------------- Kopplung (Kap. 4.2) ---------------- */
static void pair_fail(void)
{
    fl_wipe(A->k_link_new, 16); fl_wipe(A->k_conf, 16); fl_wipe(A->z_pair, 32);
    fl_led_play(&A->led, FL_LED_L7_PAIR_FAIL, fl_port_ms(), A->vbat_load, 0);
    A->mode = A->mode_before_pairing;
    disconnect();
}

static void pair_try_finish(void)
{
    if (!(A->pair_user_ok && A->pair_gw_ok)) return;
    fl_pairing_t np;
    if (fl_port_rng((uint8_t *)&np, sizeof np)) { pair_fail(); return; }   /* Fuellbyte zufaellig (4.6), F-W4 */
    np.paired = 1; memcpy(np.gateway_id, A->gw_id_new, 8); memcpy(np.k_link, A->k_link_new, 16);
    A->pair = np;
    fl_port_nv_write(FL_NV_PAIR, &A->pair, sizeof A->pair);
    fl_wipe(&np, sizeof np); fl_wipe(A->k_link_new, 16); fl_wipe(A->k_conf, 16);
    uint8_t f[3] = {FL_VT(FL_FT_PAIR), FL_PAIR_DONE, 0};
    send_raw(f, 3);
    fl_led_play(&A->led, FL_LED_L6_CONNECTED, fl_port_ms(), A->vbat_load, 0);
    /* Verbindung bleibt offen, bis das Gateway trennt (oder 3 s ohne Frame); HELLO waere erlaubt */
    A->mode = FL_MODE_NORMAL; A->sess = FL_SESS_NONE; A->had_contact = true; A->last_contact_ms = fl_port_ms();
    A->pair_deadline = 0;
    if (A->ota.active) { fl_ota_abort(&A->ota); A->cnt.ota_result = FL_E_OTA_ABORTED; save_counters(); } /* Kap. 9.4 */
}

static void on_pair(const uint8_t *f, uint16_t len)
{
    uint32_t now = fl_port_ms();
    if (A->mode != FL_MODE_PAIRING) { send_error(FL_E_NOT_ALLOWED, 0, false); disconnect(); return; }
    if (len < 2) { pair_fail(); return; }
    const uint8_t *p = f + 2;
    uint16_t n = (uint16_t)(len - 2);
    switch (f[1]) {
    case FL_PAIR_REQ: {
        /* v2: gateway_id . gw_pub . C = SHA-256("fluidi-commit" | gateway_id | gw_pub | gw_nonce) – gw_nonce folgt
         * erst nach PAIR_RSP (PAIR_REVEAL). Damit legt jede Seite ihre Nonce fest, bevor sie die andere kennt. */
        if (n < FL_PAIR_REQ_LEN || A->sess != FL_SESS_WAIT_HELLO) { pair_fail(); return; }
        uint8_t priv[32], spub[64], *rsp = A->pr_rsp;
        memcpy(A->pr_req, p, FL_PAIR_REQ_LEN);
        memcpy(A->gw_id_new, p, 8);
        memcpy(rsp, A->addr, 6);
        rsp[6] = FLUIDI_HW_REV;
        memcpy(rsp + 7, A->fw_ver, 4);
        if (fl_port_ecdh_keygen(priv, spub) || fl_port_rng(rsp + 75, 16)) { fl_wipe(priv, 32); pair_fail(); return; }
        memcpy(rsp + 11, spub, 64);
        int e = fl_port_ecdh_shared(priv, p + 8, A->z_pair);
        fl_wipe(priv, 32);
        if (e) { pair_fail(); return; }
        uint8_t out[2 + FL_PAIR_RSP_LEN] = {FL_VT(FL_FT_PAIR), FL_PAIR_RSP};
        memcpy(out + 2, rsp, FL_PAIR_RSP_LEN);
        send_raw(out, sizeof out);
        A->sess = FL_SESS_PAIR_RSP_SENT; A->t_last_rx = now; A->t_pair_start = now;
        A->pair_deadline = now + PAIR_STEP_MS;
        break; }
    case FL_PAIR_REVEAL: {
        uint8_t c[32];
        if (A->sess != FL_SESS_PAIR_RSP_SENT || n < FL_PAIR_REVEAL_LEN) { pair_fail(); return; }
        fl_pair_commit(A->pr_req, A->pr_req + 8, p, c);
        if (!fl_ct_equal(c, A->pr_req + 72, 32)) {            /* Commitment verletzt: Abbruch + Fehlversuch */
            crypto_fail(FL_E_AUTH_FAIL, 2); pair_fail(); return; }        /* N-1: zaehlt in fail_streak */
        fl_pair_transcript(A->pr_req, A->pr_rsp, p, A->transcript);
        fl_pair_keys(A->z_pair, p, A->pr_rsp + 75, A->gw_id_new, A->addr, A->k_link_new, A->k_conf);
        fl_wipe(A->z_pair, 32);
        fl_pair_sas(A->transcript, A->sas);
        A->sess = FL_SESS_PAIR_SHOWING; A->pair_user_ok = A->pair_gw_ok = false;
        A->pair_deadline = now + PAIR_CONFIRM_MS;
        fl_led_play_sas(&A->led, A->sas, now, PAIR_CONFIRM_MS);
        break; }
    case FL_PAIR_CONFIRM_G: {
        uint8_t mac[16];
        if (A->sess != FL_SESS_PAIR_SHOWING || n < 16) { pair_fail(); return; }
        fl_pair_confirm_mac(A->k_conf, 'G', A->transcript, mac);
        if (!fl_ct_equal(mac, p, 16)) { diag_add(FL_E_AUTH_FAIL, 1); pair_fail(); return; }
        A->pair_gw_ok = true;
        pair_try_finish();
        break; }
    default: pair_fail(); break;
    }
}

static void pair_user_confirm(void)
{
    uint8_t out[2 + 16] = {FL_VT(FL_FT_PAIR), FL_PAIR_CONFIRM_S};
    fl_pair_confirm_mac(A->k_conf, 'S', A->transcript, out + 2);
    send_raw(out, sizeof out);
    A->pair_user_ok = true;
    fl_led_stop(&A->led);
    pair_try_finish();
}

/* ---------------- Ereignisse ---------------- */
void fl_app_on_connect(void)
{
    uint32_t now = fl_port_ms();
    A->connected = true; A->sess = FL_SESS_WAIT_HELLO; A->authed = false; A->ota_in_session = false;
    A->t_conn = now; A->t_last_rx = now; A->stream = false; A->txq_n = 0; A->cccd_on = false;
    A->conn_count++; A->charge_uc += Q_CONN_UC;
    A->adv_valid = false; A->adv_on_set = false;
}

void fl_app_on_notify_enabled(void)
{
    if (!A->connected || A->cccd_on) return;
    A->cccd_on = true; A->t_cccd = fl_port_ms(); A->t_last_rx = A->t_cccd;
}

void fl_app_on_disconnect(void)
{
    uint32_t now = fl_port_ms();
    if (A->sess == FL_SESS_PAIR_RSP_SENT || A->sess == FL_SESS_PAIR_SHOWING) pair_fail();
    A->connected = false; A->sess = FL_SESS_NONE; A->stream = false; A->txq_n = 0;
    fl_wipe(A->k_s, 16);
    /* Spannung unter Last waehrend der Verbindung (PINMAP Kap. 3): Port liefert Minimum seit Verbindungsbeginn */
    check_battery(fl_port_vbat_mv());
    if (A->meas_pending && A->mode != FL_MODE_UNDERVOLTAGE) {   /* F-W5: Messung jetzt, ohne Funk */
        fl_record_t rec;
        A->meas_pending = false;
        fl_app_measure(A->meas_pending_cause, &rec);
        A->fast_adv_until = fl_port_ms() + FAST_ADV_MS;
    }
    if (A->after_disc_led != FL_LED_NONE && !fl_led_busy(&A->led)) {
        fl_led_play(&A->led, A->after_disc_led, now, A->vbat_load, 0);
        A->after_disc_led = FL_LED_NONE;
    }
    A->adv_valid = false;
}

void fl_app_on_rx(const uint8_t *f, uint16_t len)
{
    uint32_t now = fl_port_ms();
    uint8_t plain[256];
    if (!A->connected || len < 1 || A->sess == FL_SESS_CLOSING) return;
    if ((f[0] >> 4) != FL_PROTO_VERSION) { send_error(FL_E_PROTO_VERSION, FL_PROTO_VERSION, true); disconnect(); return; }
    switch (f[0] & 0x0F) {
    case FL_FT_HELLO: {
        if ((A->sess != FL_SESS_WAIT_HELLO && A->sess != FL_SESS_NONE) || len < 18) { handshake_failed(FL_E_BAD_LENGTH); return; }
        if (!A->pair.paired || !fl_ct_equal(f + 2, A->pair.gateway_id, 8)) {
            send_error(FL_E_NOT_PAIRED, 0, false); handshake_failed(FL_E_NOT_PAIRED); return; }
        uint8_t rsp[10] = {FL_VT(FL_FT_HELLO_RSP), (uint8_t)(f[1] < FL_PROTO_VERSION ? f[1] : FL_PROTO_VERSION)};
        if (fl_port_rng(rsp + 2, 8)) { diag_add(FL_E_AUTH_FAIL, 3); disconnect(); return; }   /* F-W4: ohne RNG keine Sitzung */
        fl_session_key(A->pair.k_link, f + 10, rsp + 2, A->k_s);
        A->ctr_rx = 0; A->ctr_tx = 0;
        send_raw(rsp, sizeof rsp);
        uint8_t info[72];
        size_t n = fl_app_session_info(info, false);
        sec_send(FL_MSG_SESSION_INFO, 0, info, n);
        A->sess = FL_SESS_SECURE_WAIT; A->t_last_rx = now;
        break; }
    case FL_FT_SECURE: {
        if (A->sess != FL_SESS_SECURE_WAIT && A->sess != FL_SESS_SECURE) { handshake_failed(FL_E_NOT_ALLOWED); return; }
        uint32_t got = A->ctr_rx;
        /* W-2: waehrend OTA darf der Zaehler springen (verlorene Write-Without-Response), nur fuer OTA_DATA */
        int n = A->ota_in_session ? fl_secure_open_ge(A->k_s, FL_DIR_G2S, A->ctr_rx, 64, A->addr, f, len, plain, &got)
                                  : fl_secure_open(A->k_s, FL_DIR_G2S, A->ctr_rx, A->addr, f, len, plain);
        if (n >= 0 && got != A->ctr_rx && plain[0] != FL_MSG_OTA_DATA) n = -FL_E_BAD_COUNTER;
        if (n < 0) {
            if (A->sess == FL_SESS_SECURE_WAIT) handshake_failed((uint8_t)-n);
            else { A->cnt.auth_fail++; diag_add((uint8_t)-n, 0); disconnect(); }
            return;
        }
        A->ctr_rx = got + 1; A->t_last_rx = now;
        if (A->sess == FL_SESS_SECURE_WAIT) {
            A->sess = FL_SESS_SECURE; A->authed = true; A->fail_streak = 0; A->timeout_streak = 0;
            A->had_contact = true; A->last_contact_ms = now;
        }
        dispatch(plain[0], plain[1], plain + 2, (size_t)n - 2);
        break; }
    case FL_FT_PAIR: A->t_last_rx = now; on_pair(f, len); break;
    default: send_error(FL_E_UNKNOWN_CMD, 0, false); disconnect(); break;
    }
}

void fl_app_on_tx_ready(void)
{
    while (A->txq_n) {
        int rc = fl_port_ble_send(A->txq[0], A->txq_len[0]);
        if (rc == 1) return;                         /* weiterhin voll */
        A->txq_n--;
        for (uint8_t i = 0; i < A->txq_n; i++) { memcpy(A->txq[i], A->txq[i + 1], A->txq_len[i + 1]); A->txq_len[i] = A->txq_len[i + 1]; }
    }
    stream_pump();
}

void fl_app_on_adv_event(void) { A->adv_count++; A->charge_uc += Q_ADV_UC; }

static void button_event(fl_btn_event_t ev, uint32_t now)
{
    fl_record_t rec;
    switch (ev) {
    case FL_BTN_EV_SHORT:
        if (A->sess == FL_SESS_PAIR_SHOWING && !A->pair_user_ok) { pair_user_confirm(); break; }
        if (A->mode == FL_MODE_UNDERVOLTAGE) { fl_led_play(&A->led, FL_LED_UV_BTN, now, A->vbat_load, 0); break; }
        if (A->connected) { A->meas_pending = true; A->meas_pending_cause = FL_CAUSE_BUTTON; break; }   /* F-W5 */
        fl_app_measure(FL_CAUSE_BUTTON, &rec);
        if (A->mode == FL_MODE_UNDERVOLTAGE) break;
        if (!A->pair.paired) { fl_led_play(&A->led, FL_LED_L15_UNPAIRED_BTN, now, A->vbat_load, 0); break; }
        A->fast_adv_until = now + FAST_ADV_MS;
        A->btn_wait = true; A->btn_seq = rec.seq; A->btn_deadline = now + BTN_RESULT_MS;
        break;
    case FL_BTN_EV_REACHED_3S: fl_led_play(&A->led, FL_LED_L12_3S, now, A->vbat_load, 0); break;
    case FL_BTN_EV_REACHED_10S: fl_led_play(&A->led, FL_LED_L13_ARMED_HOLD, now, A->vbat_load, 0); break;
    case FL_BTN_EV_LONG:
        if (A->mode == FL_MODE_UNDERVOLTAGE || A->connected) break;
        if (A->mode != FL_MODE_PAIRING) A->mode_before_pairing = A->mode;
        A->mode = FL_MODE_PAIRING; A->pairing_until = now + PAIRING_MODE_MS;
        fl_led_play(&A->led, FL_LED_L4_PAIRING, now, A->vbat_load, 0);
        break;
    case FL_BTN_EV_VLONG_ARMED: fl_led_play(&A->led, FL_LED_L13_CONFIRM_WIN, now, A->vbat_load, 0); break;
    case FL_BTN_EV_ARM_EXPIRED: fl_led_stop(&A->led); break;
    case FL_BTN_EV_FACTORY_RESET:
        fl_led_play(&A->led, FL_LED_L14_RESET, now, 0, 0);
        fl_app_factory_reset();
        A->reboot_pending = true; A->reboot_at = now + 1100u;   /* gewollt: planned_reboot */
        break;
    case FL_BTN_EV_STUCK:
        A->stuck = true; A->cnt.button_stuck++; diag_add(FL_E_BUTTON_STUCK, 0);
        fl_port_button_pullup(false); A->stuck_check_ms = now + STUCK_CHECK_MS;
        fl_led_stop(&A->led);
        break;
    case FL_BTN_EV_UNSTUCK: A->stuck = false; fl_port_button_pullup(true); break;
    default: break;
    }
}

void fl_app_on_button(bool pressed)
{
    if (A->stuck) return;
    uint32_t now = fl_port_ms();
    button_event(fl_btn_edge(&A->btn, pressed, now), now);
}

void fl_app_factory_reset(void)
{
    /* loescht K_link, gateway_id, Einstellungen, Ringspeicher-Inhalt, Fehlerprotokoll; behaelt seq, boot_id,
     * Werkskalibrierung (Kap. 10.3) */
    fl_cal_t cal = A->set.cal;
    fl_wipe(&A->pair, sizeof A->pair); fl_port_nv_delete(FL_NV_PAIR);
    fl_settings_defaults(&A->set); A->set.cal = cal; save_settings();
    fl_log_factory_clear(&A->log); save_logmeta();
    memset(&A->diag, 0, sizeof A->diag); save_diag();
    A->cnt.last_error = 0; save_counters();
    A->error_active = false;
    A->mode = FL_MODE_UNPAIRED;
}

/* ---------------- Start ---------------- */
static void boot_shutdown(void)
{
    /* Abschaltung ohne jedes Flash-Schreiben (F-W3a); Wecken nur per Taster, bei gedruecktem Taster nur Zellwechsel */
    A->mode = FL_MODE_UNDERVOLTAGE;
    fl_port_led(FL_COL_OFF, 0);
    fl_port_shutdown();
}

void fl_app_init(void)
{
    uint32_t now;
    memset(A, 0, sizeof *A);
    fl_led_init(&A->led);
    fl_btn_init(&A->btn);

    /* 1) Spannung und Neustartgrund ZUERST, vor jedem Flash-Schreiben (F-W3a) */
    A->reset_reason = fl_port_reset_reason();
    uint32_t ret = fl_port_retained_get();
    uint32_t abn = ret & FL_RET_ABN_MASK;
    bool planned = (ret & FL_RET_PLANNED) != 0, was_uv = (ret & FL_RET_UV) != 0, was_backoff = (ret & FL_RET_BACKOFF) != 0;
    bool abnormal = A->reset_reason == FL_RR_WATCHDOG || A->reset_reason == FL_RR_BROWNOUT ||
                    A->reset_reason == FL_RR_HARDFAULT || (A->reset_reason == FL_RR_SOFTWARE && !planned);
    if (A->reset_reason == FL_RR_POWER_ON || A->reset_reason == FL_RR_PIN) abn = 0;   /* Zellwechsel / Nutzer */
    else if (abnormal && abn < FL_RET_ABN_MASK) abn++;
    A->vbat_rest = fl_port_vbat_mv();
    if (A->vbat_rest == 0) A->vbat_rest = fl_port_vbat_mv();       /* N-4: Lesefehler einmal wiederholen */
    A->vbat_load = A->vbat_rest;
    if (was_uv) A->reset_reason = FL_RR_UNDERVOLTAGE;
    uint32_t newret = abn;
    /* Nach Unterspannung oder Brownout nur mit Erholung weiterlaufen (Ruhewert, Hysterese); nach Power-on ab 2.4 V */
    uint16_t vmin = (was_uv || A->reset_reason == FL_RR_BROWNOUT) ? UV_RECOVER_MV : UV_MV;
    if (A->vbat_rest < vmin) {                                      /* N-4: 0 (Lesefehler) gilt als Unterspannung */
        if (A->reset_reason == FL_RR_PIN || was_uv) {        /* Wecken per Taster: Rot 1 x 30 ms (Kap. 10.2) */
            fl_port_led(FL_COL_RED, 100);
            fl_port_delay_ms(30);
        }
        fl_port_retained_set(newret | FL_RET_UV);
        boot_shutdown();
        return;
    }
    /* Reset-Schleife: >= 3 abnormale Neustarts ohne 10 min stabilen Betrieb -> Abschaltung (F-W3a/c) */
    if (abn >= FL_ABN_MAX) {
        fl_port_retained_set((newret & ~FL_RET_ABN_MASK) | FL_RET_BACKOFF);
        boot_shutdown();
        return;
    }
    fl_port_retained_set(newret);
    s_nv_defer = true;

    /* 2) Persistente Daten (Schreiben erst nach der ersten Lastmessung, N-2) */
    fl_port_ble_addr(A->addr);
    fl_port_fw_version(A->fw_ver, &A->fw_build, &A->sec_cnt);
    if (fl_port_nv_read(FL_NV_SETTINGS, &A->set, sizeof A->set) || !fl_settings_valid(&A->set)) {
        bool had = fl_port_nv_read(FL_NV_SETTINGS, &A->set, sizeof A->set) == 0;
        fl_settings_defaults(&A->set);
        save_settings();
        if (had) diag_add(FL_E_NVS_RESTORED, 0);
    }
    if (fl_port_nv_read(FL_NV_PAIR, &A->pair, sizeof A->pair) || A->pair.paired != 1) memset(&A->pair, 0, sizeof A->pair);
    if (fl_port_nv_read(FL_NV_COUNTERS, &A->cnt, sizeof A->cnt)) memset(&A->cnt, 0, sizeof A->cnt);
    if (fl_port_nv_read(FL_NV_DIAG, &A->diag, sizeof A->diag) || A->diag.count > 16 || A->diag.head > 15)
        memset(&A->diag, 0, sizeof A->diag);
    if (fl_port_nv_read(FL_NV_LOGMETA, &A->logmeta, sizeof A->logmeta)) {
        A->logmeta.acked_upto = NONE32; A->logmeta.visible_from = 0; A->logmeta.lost_records = 0; A->logmeta.seq_floor = 0;
    }
    if (fl_log_init(&A->log, fl_port_log_flash(), &A->logmeta)) diag_add(FL_E_FLASH_FAIL, 1);

    A->cnt.boot_id++;
    /* S-5: entnommene Ladung nur bei Power-on (Zellwechsel) nullen */
    if (fl_port_reset_reason() == FL_RR_POWER_ON && !was_uv) A->cnt.charge_uc = 0;
    A->charge_uc = A->cnt.charge_uc;
    if (A->reset_reason == FL_RR_WATCHDOG) { A->cnt.wdt_resets++; diag_add(FL_E_WDT_RESET, (uint8_t)abn); }
    if (A->reset_reason == FL_RR_BROWNOUT) { A->cnt.brownouts++; diag_add(FL_E_BROWNOUT, (uint8_t)abn); }
    if (A->reset_reason == FL_RR_HARDFAULT) diag_add(FL_E_HARDFAULT, (uint8_t)abn);
    if (was_backoff) { A->cnt.backoffs++; diag_add(FL_E_HARDFAULT, 0xBF); }     /* Reset-Schleife war aktiv */
    for (uint8_t i = 0; i < A->diag.count; i++) {
        uint8_t c = A->diag.e[i].code;
        if ((c >= 0x20 && c <= 0x32) || (c >= 0x50 && c <= 0x55)) A->error_active = true;
    }

    /* OTA-Ergebnis bewerten (Kap. 9.4/9.5) */
    A->image_test = !fl_port_image_confirmed();
    if (A->cnt.ota_expect) {
        if (memcmp(A->fw_ver, A->cnt.ota_ver, 4) == 0 && A->fw_build == A->cnt.ota_build) {
            A->cnt.ota_result = 0xFE;       /* laeuft im Test, Ergebnis 0 nach Bestaetigung */
        } else {
            /* altes Image laeuft: Swap-Rueckfall (Image noch in Slot 1) oder von MCUboot verworfen (Signatur/Zaehler) */
            uint8_t hdr[4] = {0};
            const fl_flash_t *s1 = fl_port_slot1_flash();
            s1->read(s1->ctx, 0, hdr, 4);
            A->cnt.ota_result = (fl_get_u32(hdr) == 0x96f3b83du) ? FL_E_OTA_REVERTED : FL_E_OTA_SIGNATURE;
            diag_add(A->cnt.ota_result, 0);
        }
        A->cnt.ota_expect = 0;
    }
    now = fl_port_ms();
    A->test_deadline_ms = now + TEST_CONFIRM_MS;
    A->charge_ref_ms = now;
    A->last_charge_save = now;
    fl_port_tx_power(A->set.tx_power_dbm);

    /* Selbsttest = erste Messung (L11) */
    fl_record_t rec;
    fl_app_measure(FL_CAUSE_AUTO, &rec);                 /* erste Lastmessung (check_battery) */
    if (A->mode == FL_MODE_UNDERVOLTAGE) return;
    s_nv_defer = false;                                  /* N-2: erst jetzt alles Aufgelaufene schreiben */
    save_settings(); save_diag(); save_counters();
    now = fl_port_ms();
    A->mode = A->pair.paired ? FL_MODE_NORMAL : FL_MODE_UNPAIRED;
    fl_led_play(&A->led, (A->last_meas_ok && A->tmp_ok) ? FL_LED_L11_START_OK : FL_LED_L11_START_FAIL, now, A->vbat_load, 0);
    if (!A->pair.paired) A->after_disc_led = FL_LED_L11_UNPAIRED;   /* folgt nach L11 */
    schedule_meas(now);
    A->next_minute_ms = now + 60000u;
}

/* ---------------- Hauptschleife ---------------- */
uint32_t fl_app_process(void)
{
    uint32_t now = fl_port_ms();
    fl_record_t rec;
    fl_port_wdt_kick();

    /* Ladungsschaetzung Ruhestrom */
    uint32_t el = now - A->charge_ref_ms;
    if (el >= 1000u) { A->charge_uc += (uint32_t)(((uint64_t)el * I_SLEEP_NA) / 1000000u); A->charge_ref_ms = now - (el % 1000u); }

    if (A->reboot_pending && due(now, A->reboot_at) && !fl_led_busy(&A->led)) planned_reboot();

    /* F-W3: nach 10 min stabilem Betrieb Zaehler abnormaler Neustarts nullen */
    if (!A->stable_done && now >= FL_STABLE_MS) {
        A->stable_done = true;
        fl_port_retained_set(fl_port_retained_get() & ~(FL_RET_ABN_MASK | FL_RET_BACKOFF | FL_RET_UV | FL_RET_PLANNED));
    }
    /* S-5: Ladungsschaetzung alle 6 h sichern */
    if (now - A->last_charge_save >= 6u * 3600u * 1000u) { A->last_charge_save = now; A->cnt.charge_uc = A->charge_uc; save_counters(); }

    /* Sitzungsfristen (Kap. 3, 4.2) */
    if (A->connected && A->sess != FL_SESS_CLOSING) {
        uint32_t idle = A->ota_in_session ? IDLE_TIMEOUT_OTA_MS : IDLE_TIMEOUT_MS;
        bool pairing = A->sess == FL_SESS_PAIR_RSP_SENT || A->sess == FL_SESS_PAIR_SHOWING;
        if (A->sess == FL_SESS_WAIT_HELLO &&
            (due(now, A->t_conn + HELLO_ABS_MS) || (A->cccd_on && due(now, A->t_cccd + HELLO_AFTER_CCCD_MS))))
            handshake_timeout();
        else if (pairing && (due(now, A->pair_deadline) || due(now, A->t_pair_start + PAIR_TOTAL_MS))) {
            diag_add(FL_E_TIMEOUT, 2); pair_fail(); }
        else if (!pairing && A->sess != FL_SESS_WAIT_HELLO && due(now, A->t_last_rx + idle)) { diag_add(FL_E_TIMEOUT, 0); disconnect(); }
        else if (!A->ota_in_session && !pairing && due(now, A->t_conn + SESSION_MAX_MS)) disconnect();
    }
    if (A->mode == FL_MODE_PAIRING && !A->connected && due(now, A->pairing_until)) {
        A->mode = A->mode_before_pairing == FL_MODE_PAIRING ? FL_MODE_UNPAIRED : A->mode_before_pairing;
        if (A->led.active == FL_LED_L4_PAIRING) fl_led_stop(&A->led);
    }
    if (A->locked && due(now, A->locked_until)) A->locked = false;

    /* Taster */
    button_event(fl_btn_tick(&A->btn, now), now);
    if (A->stuck && due(now, A->stuck_check_ms)) {
        if (!fl_port_button_pressed()) { A->stuck = false; fl_btn_init(&A->btn); fl_port_button_pullup(true); }
        else A->stuck_check_ms = now + STUCK_CHECK_MS;
    }
    if (A->btn_wait && due(now, A->btn_deadline) && !A->connected) {
        A->btn_wait = false;
        fl_led_play(&A->led, FL_LED_L2_BUFFERED, now, A->vbat_load, 0);
        if (A->error_active) A->after_disc_led = FL_LED_L10B_ERROR_BTN;
        else if (A->batt_low) A->after_disc_led = FL_LED_L9_BATT_LOW;
    }

    /* Automatische Messung */
    if (due(now, A->next_meas_ms) && !A->connected && A->mode != FL_MODE_UNDERVOLTAGE) {
        fl_app_measure(FL_CAUSE_AUTO, &rec);
        if (A->set.heartbeat_led && !fl_led_busy(&A->led)) fl_led_play(&A->led, FL_LED_L3_HEARTBEAT, fl_port_ms(), A->vbat_load, 0);
        schedule_meas(now);
    }

    /* Minutentakt: periodische Anzeigen (max. 1 je Minute) */
    if (due(now, A->next_minute_ms)) {
        A->minute_counter++;
        A->next_minute_ms += 60000u;
        if (due(now, A->next_minute_ms)) A->next_minute_ms = now + 60000u;
        if (!A->connected && !fl_led_busy(&A->led) && A->mode == FL_MODE_NORMAL) {
            bool day_ok = true;
            if (A->time_valid) {                               /* W-7: Wochentage, 1970-01-01 war ein Donnerstag */
                int64_t d = local_ms(now) / 86400000; int wd = (int)((d % 7 + 7 + 3) % 7);   /* 0 = Montag */
                day_ok = (A->set.led_weekdays >> wd) & 1;
            }
            fl_periodic_in_t in = {A->error_active, A->batt_low, A->water, A->set.water_led != 0 && day_ok, A->time_valid,
                                   minute_of_day(now), A->set.led_win_start, A->set.led_win_end, A->minute_counter};
            fl_led_pattern_t p = fl_led_periodic(&in);
            if (p != FL_LED_NONE) fl_led_play(&A->led, p, now, A->vbat_load, 0);
        }
    }

    /* Bestaetigung eines neuen Images (Kap. 9.5) */
    if (A->image_test) {
        if (A->authed && A->last_meas_ok && A->tmp_ok) {
            if (fl_port_ota_confirm() == 0) {
                A->image_test = false; A->cnt.ota_result = 0; save_counters();
                A->after_disc_led = FL_LED_L17_OTA_OK;
            }
        } else if (due(now, A->test_deadline_ms) && !A->connected) {
            planned_reboot();                                  /* MCUboot faellt zurueck */
        }
    }

    /* LED (nach L11 ggf. Folgemuster ohne Verbindung) */
    uint32_t led_dl = fl_led_tick(&A->led, now);
    if (!fl_led_busy(&A->led) && !A->connected && A->after_disc_led != FL_LED_NONE) {
        fl_led_play(&A->led, A->after_disc_led, now, A->vbat_load, 0);
        A->after_disc_led = FL_LED_NONE;
        led_dl = fl_led_tick(&A->led, now);
    }
    fl_port_led(A->led.out, A->set.led_level);

    update_adv(now);

    /* naechste Frist */
    uint32_t best = 5u * 60000u;     /* spaetestens alle 5 min (Watchdog 10 min) */
    dl_min(&best, now, A->next_meas_ms, A->mode != FL_MODE_UNDERVOLTAGE);
    bool need_minute = A->error_active || A->batt_low || (A->water && A->set.water_led);
    dl_min(&best, now, A->next_minute_ms, need_minute);
    if (!need_minute && due(now, A->next_minute_ms)) A->next_minute_ms = now + 60000u;
    dl_min(&best, now, led_dl, led_dl != 0);
    dl_min(&best, now, fl_btn_next_deadline(&A->btn), fl_btn_next_deadline(&A->btn) != 0);
    dl_min(&best, now, A->stuck_check_ms, A->stuck);
    dl_min(&best, now, A->btn_deadline, A->btn_wait);
    dl_min(&best, now, A->pairing_until, A->mode == FL_MODE_PAIRING);
    dl_min(&best, now, A->fast_adv_until, !due(now, A->fast_adv_until));
    dl_min(&best, now, A->locked_until, A->locked);
    dl_min(&best, now, A->reboot_at, A->reboot_pending);
    dl_min(&best, now, A->test_deadline_ms, A->image_test);
    dl_min(&best, now, FL_STABLE_MS, !A->stable_done);
    if (A->connected) {
        dl_min(&best, now, A->t_conn + HELLO_ABS_MS, A->sess == FL_SESS_WAIT_HELLO);
        dl_min(&best, now, A->t_cccd + HELLO_AFTER_CCCD_MS, A->sess == FL_SESS_WAIT_HELLO && A->cccd_on);
        dl_min(&best, now, A->t_last_rx + (A->ota_in_session ? IDLE_TIMEOUT_OTA_MS : IDLE_TIMEOUT_MS), true);
        dl_min(&best, now, A->pair_deadline, A->sess == FL_SESS_PAIR_SHOWING || A->sess == FL_SESS_PAIR_RSP_SENT);
        dl_min(&best, now, A->t_conn + SESSION_MAX_MS, !A->ota_in_session);
    }
    return best;
}
