/*
 * fluidi – TESTFIRMWARE (siehe fl_testfw.h). Nur im Build `make TESTFW=n` uebersetzt und gelinkt.
 * Grundlage: docs/reviews/phase5_testplan_prototyp.md Anhang A (TF-1..TF-4), Kap. 10 (EP-15).
 */
#include "fl_testfw.h"
#if FLUIDI_TESTFW
#include "fl_app.h"
#include "fl_port.h"
#include "fl_ui.h"
#include "fl_util.h"

enum { ACT_NONE = 0, ACT_HANG, ACT_TF2_LATE, ACT_TF2_EARLY, ACT_TF2_HF };

static struct {
    uint32_t ops0, ops_excl;            /* Flash-Operationen beim Start / vom Testmodul selbst verursacht */
    uint32_t ret_boot;
    uint8_t  tf2_mode_boot;             /* TF-2 in diesem Start aktiv (Modus) */
    bool     result_pending;            /* TF-2-Ergebnis nach Pin-Wecken uebernehmen */
    uint8_t  res_mode, res_cyc, res_max, res_sd;
    uint16_t vdd_min;
    uint16_t ops_ready;                 /* Flash-Ops bis zur ersten bestandenen Lastmessung (N-2: Soll 0) */
    bool     ready_seen;
    uint8_t  follow_led;                /* L11 nach dem Startsignal */
    uint8_t  seq_n; uint32_t seq_last;
    uint8_t  action;
    bool     halted;
    bool     nv_loaded, dirty;
    fl_tf_nv_t nv, nv_saved;
    bool     timers; uint32_t next_save, next_tf3;
} T;

static bool due(uint32_t now, uint32_t t) { return (int32_t)(now - t) >= 0; }
static uint32_t ops_raw(void) { return fl_port_tf_flash_ops(); }
uint32_t fl_tf_ops_boot(void) { return ops_raw() - T.ops0 - T.ops_excl; }
const fl_tf_nv_t *fl_tf_nv(void) { return &T.nv; }

static void nv_defaults(void)
{
    memset(&T.nv, 0, sizeof T.nv);
    T.nv.fmt = FL_TF_FMT; T.nv.variant = FLUIDI_TESTFW;
    T.nv.tf3_last = (int16_t)0x8000; T.nv.tf3_min = 0x7FFF; T.nv.tf3_max = (int16_t)0x8000;
    T.nv.vdd_min_ever = 0xFFFF;
}

static void nv_load(void)
{
    if (T.nv_loaded) return;
    T.nv_loaded = true;
    if (fl_port_nv_read(FL_NV_TF, &T.nv, sizeof T.nv) || T.nv.fmt != FL_TF_FMT || T.nv.variant != FLUIDI_TESTFW) {
        nv_defaults();                       /* andere Variante/erstes Einspielen: Testzaehler neu beginnen */
        memset(&T.nv_saved, 0xFF, sizeof T.nv_saved);
        T.dirty = true;
    } else {
        T.nv_saved = T.nv;
    }
}

/* Testzaehler sichern; die eigenen Schreibvorgaenge zaehlen NICHT zu den Flash-Ops des Serienverhaltens */
static void save_now(void)
{
    nv_load();
    T.dirty = true;
    if (!fl_app_nv_allowed()) return;                    /* N-2: vor der ersten Lastmessung nichts schreiben */
    if (memcmp(&T.nv, &T.nv_saved, sizeof T.nv) != 0) {
        uint32_t b = ops_raw();
        fl_port_nv_write(FL_NV_TF, &T.nv, sizeof T.nv);
        T.ops_excl += ops_raw() - b;
        T.nv_saved = T.nv;
    }
    T.dirty = false;
}

uint32_t fl_tf_boot(uint32_t ret, uint8_t rr)
{
    memset(&T, 0, sizeof T);
    T.ops0 = ops_raw();
    T.ret_boot = ret;
    T.vdd_min = 0xFFFF;
    T.ops_ready = 0xFFFF;
    uint8_t mode = (uint8_t)((ret & FL_TF_RET_MODE_MASK) >> FL_TF_RET_MODE_SHIFT);
    if (!mode) return 0;
    if (rr == FL_RR_POWER_ON || rr == FL_RR_PIN) {
        /* Testende: Nutzer hat nach der Abschaltung per Taster geweckt -> Ergebnis uebernehmen, Bits loeschen */
        T.result_pending = true;
        T.res_mode = mode;
        T.res_cyc = (uint8_t)((ret & FL_TF_RET_CYC_MASK) >> FL_TF_RET_CYC_SHIFT);
        T.res_max = (uint8_t)((ret & FL_TF_RET_MAX_MASK) >> FL_TF_RET_MAX_SHIFT);
        T.res_sd = (uint8_t)((ret & FL_TF_RET_SD_MASK) >> FL_TF_RET_SD_SHIFT);
        return 0;
    }
    T.tf2_mode_boot = mode;                  /* abnormaler Neustart: Schleife laeuft weiter */
    return ret & FL_TF_RET_ALL;
}

uint32_t fl_tf_shutdown_boot(uint32_t newret)
{
    if (!T.tf2_mode_boot) return newret;
    uint32_t ops = fl_tf_ops_boot();
    if (ops > 3u) ops = 3u;
    return (newret & ~FL_TF_RET_SD_MASK) | (ops << FL_TF_RET_SD_SHIFT);
}

static void fatal(uint8_t kind)
{
    T.halted = true;
    fl_port_tf_fatal(kind);                  /* Hardware: kehrt nicht zurueck; Host-Simulation: kehrt zurueck */
}

bool fl_tf_point(uint8_t where)
{
    uint8_t m = T.tf2_mode_boot;
    if (!m) return false;
    if ((where == FL_TF_PT_EARLY) != (m == FL_TF2_EARLY)) return false;
    uint32_t ret = fl_port_retained_get();
    uint32_t ops = fl_tf_ops_boot(), mx = (ret & FL_TF_RET_MAX_MASK) >> FL_TF_RET_MAX_SHIFT;
    uint32_t cyc = (ret & FL_TF_RET_CYC_MASK) >> FL_TF_RET_CYC_SHIFT;
    if (ops > mx) mx = ops > 31u ? 31u : ops;
    if (cyc < 3u) cyc++;
    ret = (ret & ~(FL_TF_RET_MAX_MASK | FL_TF_RET_CYC_MASK)) | (mx << FL_TF_RET_MAX_SHIFT) | (cyc << FL_TF_RET_CYC_SHIFT);
    fl_port_retained_set(ret);
    fatal(m == FL_TF2_HARDFAULT ? FL_TF_FATAL_HARDFAULT : FL_TF_FATAL_SERIES);
    return true;
}

void fl_tf_started(uint8_t l11)
{
    uint32_t now = fl_port_ms();
    nv_load();
    if (T.result_pending) {
        T.nv.tf2_mode = T.res_mode; T.nv.tf2_cycles = T.res_cyc; T.nv.tf2_max_ops = T.res_max; T.nv.tf2_sd_ops = T.res_sd;
        T.nv.tf2_done++;
        T.result_pending = false;
    }
    if (T.vdd_min < T.nv.vdd_min_ever) T.nv.vdd_min_ever = T.vdd_min;
    save_now();
    T.timers = true; T.next_save = now + FL_TF_SAVE_PERIOD_MS; T.next_tf3 = now + FL_TF3_PERIOD_MS;
    if (fl_led_play(&g_fl.led, FL_LED_TF_START, now, g_fl.vbat_load, 0)) T.follow_led = l11;
    else fl_led_play(&g_fl.led, (fl_led_pattern_t)l11, now, g_fl.vbat_load, 0);
}

bool fl_tf_led_followup(uint32_t now)
{
    if (!T.follow_led || fl_led_busy(&g_fl.led)) return false;
    fl_led_play(&g_fl.led, (fl_led_pattern_t)T.follow_led, now, g_fl.vbat_load, 0);
    T.follow_led = 0;
    return true;
}

void fl_tf_on_short(uint32_t now)
{
    if (T.halted || T.action) return;
    if (T.seq_n && now - T.seq_last <= FL_TF_SEQ_GAP_MS) { if (T.seq_n < 255) T.seq_n++; }
    else T.seq_n = 1;
    T.seq_last = now;
}

void fl_tf_vdd(uint16_t mv)
{
    if (mv && mv < T.vdd_min) T.vdd_min = mv;
    if (T.nv_loaded && mv && mv < T.nv.vdd_min_ever) { T.nv.vdd_min_ever = mv; T.dirty = true; }
}

void fl_tf_ready(void)
{
    if (T.ready_seen) return;
    T.ready_seen = true;
    uint32_t o = fl_tf_ops_boot();
    T.ops_ready = (uint16_t)(o > 0xFFFEu ? 0xFFFEu : o);
}

static uint8_t seq_action(uint8_t n)
{
#if FLUIDI_TESTFW == 1
    if (n == FL_TF_SEQ_PRIMARY) return ACT_HANG;
#elif FLUIDI_TESTFW == 2
    if (n == FL_TF_SEQ_PRIMARY) return ACT_TF2_LATE;
    if (n == FL_TF_SEQ_EARLY) return ACT_TF2_EARLY;
    if (n == FL_TF_SEQ_HARDFAULT) return ACT_TF2_HF;
#endif
    (void)n;
    return ACT_NONE;
}

static void dl_set(bool *has, uint32_t *dl, uint32_t now, uint32_t t)
{
    if (!*has || (int32_t)(t - now) < (int32_t)(*dl - now)) *dl = t;
    *has = true;
}

#if FLUIDI_TESTFW == 3
static void tf3_read(uint32_t now)
{
    int16_t t = (int16_t)0x8000;
    uint8_t st = 0;
    int rc = fl_port_tf3_tmp_read(&t, &st);
    T.nv.tf3_reads++;
    if (rc) {
        bool first = T.nv.tf3_err == 0;
        T.nv.tf3_err++; T.nv.tf3_stage = st; t = (int16_t)0x8000;
        if (first) save_now();                                  /* erster I2C-Fehler sofort sichern */
    } else {
        T.nv.tf3_last = t;
        if (t < T.nv.tf3_min) T.nv.tf3_min = t;
        if (T.nv.tf3_max == (int16_t)0x8000 || t > T.nv.tf3_max) T.nv.tf3_max = t;
    }
    T.dirty = true;
    fl_record_t r;
    uint16_t frac;
    memset(&r, 0, sizeof r);
    r.boot_id = g_fl.cnt.boot_id;
    fl_port_uptime(&r.uptime_s, &frac);
    r.c_probe = FL_C_INVALID;                                   /* kein Feuchtewert */
    r.c_diag = (uint16_t)(T.nv.tf3_err > 0xFFFEu ? 0xFFFEu : T.nv.tf3_err);   /* I2C-Fehlerzaehler (kumuliert) */
    r.temp = rc ? FL_TEMP_INVALID : t;
    r.vbat_mv = g_fl.vbat_load;
    r.cause = FL_CAUSE_TF3;
    r.flags = rc ? FL_RF_TEMP_INVALID : 0;
    uint32_t b = ops_raw();
    fl_app_tf_log(&r);
    T.ops_excl += ops_raw() - b;                                /* Testdatensaetze nicht als Serien-Flash-Ops */
    (void)now;
}
#endif

bool fl_tf_process(uint32_t now, uint32_t *dl)
{
    bool has = false;
    if (T.halted) return false;
    nv_load();
    if (!T.timers) { T.timers = true; T.next_save = now + FL_TF_SAVE_PERIOD_MS; T.next_tf3 = now + FL_TF3_PERIOD_MS; }

    /* Tastersequenz auswerten, wenn FL_TF_SEQ_GAP_MS kein weiterer kurzer Druck kam */
    if (T.seq_n && !T.action) {
        if (now - T.seq_last > FL_TF_SEQ_GAP_MS) {
            T.action = seq_action(T.seq_n);
            T.seq_n = 0;
            if (T.action) { fl_led_stop(&g_fl.led); fl_led_play(&g_fl.led, FL_LED_TF_ACK, now, g_fl.vbat_load, 0); }
        } else {
            dl_set(&has, dl, now, T.seq_last + FL_TF_SEQ_GAP_MS + 1u);
        }
    }
    /* Aktion erst nach der Quittung und ohne Verbindung (sonst beim Trennen erneut aufgerufen) */
    if (T.action && !fl_led_busy(&g_fl.led) && !g_fl.connected) {
        uint8_t a = T.action;
        T.action = ACT_NONE;
        if (a == ACT_HANG) {
            T.nv.tf1_trig++; save_now();
            T.halted = true;
            fl_port_tf_hang();                                  /* TF-1: Watchdog muss nach <= 10 min neu starten */
            return false;
        }
        uint8_t mode = a == ACT_TF2_EARLY ? FL_TF2_EARLY : a == ACT_TF2_HF ? FL_TF2_HARDFAULT : FL_TF2_LATE;
        T.nv.tf2_trig++; save_now();
        uint32_t ret = fl_port_retained_get() & ~FL_TF_RET_ALL;
        ret |= ((uint32_t)mode << FL_TF_RET_MODE_SHIFT) | (1u << FL_TF_RET_CYC_SHIFT);   /* Ausloeser = 1. Neustart */
        fl_port_retained_set(ret);
        fatal(mode == FL_TF2_HARDFAULT ? FL_TF_FATAL_HARDFAULT : FL_TF_FATAL_SERIES);
        return false;
    }

#if FLUIDI_TESTFW == 3
    if (g_fl.mode != FL_MODE_UNDERVOLTAGE) {
        if (due(now, T.next_tf3)) {
            if (g_fl.connected) {
                dl_set(&has, dl, now, now + 1000u);             /* nach dem Trennen nachholen */
            } else {
                tf3_read(now);
                T.next_tf3 += FL_TF3_PERIOD_MS;
                if (due(now, T.next_tf3)) T.next_tf3 = now + FL_TF3_PERIOD_MS;
            }
        }
        if (!g_fl.connected || !due(now, T.next_tf3)) dl_set(&has, dl, now, T.next_tf3);
    }
#endif

    if (T.dirty && due(now, T.next_save)) { save_now(); T.next_save = now + FL_TF_SAVE_PERIOD_MS; }
    if (T.dirty) dl_set(&has, dl, now, T.next_save);
    return has;
}

size_t fl_tf_info_tail(uint8_t *o)
{
    o[0] = 'T'; o[1] = 'F'; o[2] = FLUIDI_TESTFW; o[3] = FL_TF_FMT;
    return FL_TF_INFO_TAIL_LEN;
}

static uint16_t sat16(uint32_t v) { return (uint16_t)(v > 0xFFFFu ? 0xFFFFu : v); }

size_t fl_tf_diag_tail(uint8_t *o)
{
    nv_load();
    memset(o, 0, FL_TF_DIAG_TAIL_LEN);
    o[0] = 'T'; o[1] = 'F'; o[2] = FLUIDI_TESTFW; o[3] = FL_TF_FMT;
    fl_put_u32(o + 4, g_fl.meas_count);
    fl_put_u32(o + 8, g_fl.adv_count);
    fl_put_u32(o + 12, g_fl.conn_count);
    fl_put_u32(o + 16, g_fl.led.on_ms_total);
    fl_put_u32(o + 20, g_fl.charge_uc);
    o[24] = g_fl.reset_reason;
    o[25] = (uint8_t)(fl_port_retained_get() & FL_RET_ABN_MASK);
    fl_put_u32(o + 26, T.ret_boot);
    fl_put_u16(o + 30, T.vdd_min);
    fl_put_u16(o + 32, g_fl.vbat_rest);
    fl_put_u16(o + 34, T.nv.vdd_min_ever);
    fl_put_u16(o + 36, g_fl.cnt.boot_id);
    fl_put_u16(o + 38, sat16(fl_tf_ops_boot()));
    fl_put_u16(o + 40, T.ops_ready);
    fl_put_u16(o + 42, g_fl.cnt.backoffs);
    fl_put_u16(o + 44, T.nv.tf1_trig);
    fl_put_u16(o + 46, T.nv.tf2_trig);
    o[48] = T.nv.tf2_mode; o[49] = T.nv.tf2_cycles; o[50] = T.nv.tf2_max_ops; o[51] = T.nv.tf2_sd_ops;
    fl_put_u32(o + 52, T.nv.tf3_reads);
    fl_put_u32(o + 56, T.nv.tf3_err);
    fl_put_u16(o + 60, (uint16_t)T.nv.tf3_last);
    fl_put_u16(o + 62, (uint16_t)T.nv.tf3_min);
    fl_put_u16(o + 64, (uint16_t)T.nv.tf3_max);
    o[66] = T.nv.tf3_stage;
    o[67] = FLUIDI_TESTFW == 3 ? 1 : 0;                  /* SENS_PWR dauernd high */
    return FL_TF_DIAG_TAIL_LEN;
}

#endif /* FLUIDI_TESTFW */
