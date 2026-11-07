/* fluidi – LED-Muster und Taster (siehe fl_ui.h). Tabellen 1:1 aus PROTOCOL.md Kap. 10.2/10.3. */
#include "fl_ui.h"
#include <string.h>

#define VDD_BLUE_MIN_MV   2650u   /* Kap. 10.1, phase3_rgb_antenne_elektronik.md 1.4 */
#define VDD_LED_MIN_MV    2400u   /* Unterspannung: keine LED ausser auf Tastendruck (Kap. 10.2) */

static const fl_led_step_t S_L1[]  = {{FL_COL_GREEN, 30, 150}, {FL_COL_GREEN, 30, 0}};
static const fl_led_step_t S_L2[]  = {{FL_COL_GREEN, 30, 0}};
static const fl_led_step_t S_L3[]  = {{FL_COL_GREEN, 20, 0}};
static const fl_led_step_t S_L4[]  = {{FL_COL_YELLOW, 50, 950}};                       /* 1 Hz, max. 120 s */
static const fl_led_step_t S_L6[]  = {{FL_COL_GREEN, 1000, 0}};
static const fl_led_step_t S_L7[]  = {{FL_COL_RED, 100, 100}, {FL_COL_RED, 100, 100}, {FL_COL_RED, 100, 0}};
static const fl_led_step_t S_L8[]  = {{FL_COL_BLUE, 5, 0}};
static const fl_led_step_t S_L9[]  = {{FL_COL_RED, 10, 150}, {FL_COL_RED, 10, 0}};
static const fl_led_step_t S_L10[] = {{FL_COL_RED, 10, 150}, {FL_COL_RED, 10, 150}, {FL_COL_RED, 10, 0}};
static const fl_led_step_t S_L10B[] = {{FL_COL_RED, 100, 100}, {FL_COL_RED, 100, 100}, {FL_COL_RED, 100, 0}};
static const fl_led_step_t S_L11OK[] = {{FL_COL_GREEN, 200, 0}};
static const fl_led_step_t S_L11F[] = {{FL_COL_RED, 100, 100}, {FL_COL_RED, 100, 100}, {FL_COL_RED, 100, 0}};
static const fl_led_step_t S_L11U[] = {{FL_COL_YELLOW, 50, 150}, {FL_COL_YELLOW, 50, 0}};
static const fl_led_step_t S_L12[] = {{FL_COL_YELLOW, 100, 0}};
static const fl_led_step_t S_L13H[] = {{FL_COL_RED, 100, 100}};                       /* bis Loslassen */
static const fl_led_step_t S_L13W[] = {{FL_COL_RED, 5, 245}};                         /* "gedimmt": 2 % Tastgrad, 5 s */
static const fl_led_step_t S_L14[] = {{FL_COL_RED, 1000, 0}};
static const fl_led_step_t S_L15[] = {{FL_COL_YELLOW, 200, 0}};
static const fl_led_step_t S_L16[] = {{FL_COL_GREEN, 200, 0}, {FL_COL_BLUE, 200, 0}};
static const fl_led_step_t S_L17OK[] = {{FL_COL_GREEN, 50, 100}, {FL_COL_GREEN, 50, 100}, {FL_COL_GREEN, 50, 0}};
static const fl_led_step_t S_L17RV[] = {{FL_COL_RED, 50, 100}, {FL_COL_RED, 50, 100}, {FL_COL_RED, 50, 0}};
static const fl_led_step_t S_UV[]  = {{FL_COL_RED, 30, 0}};

typedef struct { const fl_led_step_t *s; uint8_t n; uint16_t repeats; uint16_t gap; uint16_t limit_s; } pat_t;
#define P(a, rep, gap, lim) {a, (uint8_t)(sizeof(a) / sizeof(a[0])), rep, gap, lim}
static const pat_t PATS[FL_LED_COUNT] = {
    [FL_LED_L1_SENT] = P(S_L1, 0, 0, 0),           [FL_LED_L2_BUFFERED] = P(S_L2, 0, 0, 0),
    [FL_LED_L3_HEARTBEAT] = P(S_L3, 0, 0, 0),      [FL_LED_L4_PAIRING] = P(S_L4, 0xFFFF, 0, 120),
    [FL_LED_L6_CONNECTED] = P(S_L6, 0, 0, 0),      [FL_LED_L7_PAIR_FAIL] = P(S_L7, 0, 0, 0),
    [FL_LED_L8_WATER] = P(S_L8, 0, 0, 0),          [FL_LED_L9_BATT_LOW] = P(S_L9, 0, 0, 0),
    [FL_LED_L10_ERROR] = P(S_L10, 0, 0, 0),        [FL_LED_L10B_ERROR_BTN] = P(S_L10B, 0, 0, 0),
    [FL_LED_L11_START_OK] = P(S_L11OK, 0, 0, 0),   [FL_LED_L11_START_FAIL] = P(S_L11F, 0, 0, 0),
    [FL_LED_L11_UNPAIRED] = P(S_L11U, 0, 0, 0),    [FL_LED_L12_3S] = P(S_L12, 0, 0, 0),
    [FL_LED_L13_ARMED_HOLD] = P(S_L13H, 0xFFFF, 0, 30), [FL_LED_L13_CONFIRM_WIN] = P(S_L13W, 0xFFFF, 0, 5),
    [FL_LED_L14_RESET] = P(S_L14, 0, 0, 0),        [FL_LED_L15_UNPAIRED_BTN] = P(S_L15, 0, 0, 0),
    [FL_LED_L16_IDENTIFY] = P(S_L16, 0xFFFF, 0, 30), [FL_LED_L17_OTA_OK] = P(S_L17OK, 0, 0, 0),
    [FL_LED_L17_OTA_REVERT] = P(S_L17RV, 0, 0, 0), [FL_LED_UV_BTN] = P(S_UV, 0, 0, 0),
    [FL_LED_UNPAIRED_2Y] = P(S_L11U, 0, 0, 0),
};

void fl_led_init(fl_led_t *l) { memset(l, 0, sizeof *l); }

static uint8_t map_col(uint8_t c, uint16_t vdd)
{
    /* Blau nur bei VDD >= 2.65 V, sonst Gelb (D-010 "bei schwacher Zelle Gelb") */
    if ((c & FL_COL_BLUE) && vdd < VDD_BLUE_MIN_MV) return FL_COL_YELLOW;
    return c;
}

bool fl_led_play(fl_led_t *l, fl_led_pattern_t p, uint32_t now_ms, uint16_t vdd_mv, uint16_t duration_s)
{
    if (p <= FL_LED_NONE || p >= FL_LED_COUNT || p == FL_LED_L5_SAS) return false;
    if (vdd_mv && vdd_mv < VDD_LED_MIN_MV && p != FL_LED_UV_BTN) return false;
    const pat_t *pt = &PATS[p];
    /* Farben je nach Spannung ersetzen (kopieren, damit Tabellen konstant bleiben) */
    uint8_t n = pt->n > 4 ? 4 : pt->n;
    for (uint8_t i = 0; i < n; i++) { l->buf[i] = pt->s[i]; l->buf[i].col = map_col(pt->s[i].col, vdd_mv); }
    if (p == FL_LED_L16_IDENTIFY && vdd_mv < VDD_BLUE_MIN_MV) l->buf[1].col = FL_COL_OFF;
    l->steps = l->buf; l->n = n; l->idx = 0; l->on = false;
    l->repeats = pt->repeats; l->gap_ms = pt->gap;
    uint16_t lim = duration_s ? duration_s : pt->limit_s;
    l->t_end = lim ? now_ms + lim * 1000u : 0;
    l->t_next = now_ms; l->active = p; l->out = FL_COL_OFF;
    return true;
}

void fl_led_play_sas(fl_led_t *l, const uint8_t d[5], uint32_t now_ms, uint32_t max_ms)
{
    static const uint8_t cmap[3] = {FL_COL_RED, FL_COL_GREEN, FL_COL_YELLOW};
    for (int i = 0; i < 5; i++) { l->sas[i].col = cmap[d[i] % 3]; l->sas[i].on_ms = 300; l->sas[i].off_ms = 300; }
    l->sas[4].off_ms = 2000;                       /* Wiederholung nach 2 s */
    l->steps = l->sas; l->n = 5; l->idx = 0; l->on = false;
    l->repeats = 0xFFFF; l->gap_ms = 0;
    l->t_end = now_ms + max_ms; l->t_next = now_ms; l->active = FL_LED_L5_SAS; l->out = FL_COL_OFF;
}

void fl_led_stop(fl_led_t *l) { l->steps = NULL; l->active = FL_LED_NONE; l->out = FL_COL_OFF; l->t_next = 0; }
bool fl_led_busy(const fl_led_t *l) { return l->steps != NULL; }

uint32_t fl_led_tick(fl_led_t *l, uint32_t now)
{
    if (!l->steps) return 0;
    if (l->t_end && (int32_t)(now - l->t_end) >= 0) { fl_led_stop(l); return 0; }
    while (l->steps && (int32_t)(now - l->t_next) >= 0) {
        const fl_led_step_t *s = &l->steps[l->idx];
        if (!l->on) {
            l->on = true; l->out = s->col; l->t_next += s->on_ms;
            if (s->col) l->on_ms_total += s->on_ms;
        } else {
            l->on = false; l->out = FL_COL_OFF; l->t_next += s->off_ms;
            if (++l->idx >= l->n) {
                l->idx = 0;
                if (l->repeats == 0) { fl_led_stop(l); return 0; }
                if (l->repeats != 0xFFFF) l->repeats--;
                l->t_next += l->gap_ms;
            }
        }
    }
    return l->steps ? l->t_next : 0;
}

uint32_t fl_led_charge_uc(uint32_t on_ms) { return on_ms * 3u; }   /* 3 mA x ms = uC */

fl_led_pattern_t fl_led_periodic(const fl_periodic_in_t *in)
{
    bool in_win;
    if (in->time_valid) {
        if (in->win_start <= in->win_end) in_win = in->minute_of_day >= in->win_start && in->minute_of_day < in->win_end;
        else in_win = in->minute_of_day >= in->win_start || in->minute_of_day < in->win_end;   /* ueber Mitternacht */
    } else {
        in_win = true;   /* ohne Zeit: ganztags */
    }
    if (!in_win) return FL_LED_NONE;
    /* Vorrang: Fehler > Batterie tief > Giessen noetig; L9/L10 alle 10 min, L8 1/min (ohne Zeit alle 2 min) */
    if (in->error && in->minute_counter % 10u == 0) return FL_LED_L10_ERROR;
    if (in->batt_low && in->minute_counter % 10u == 0) return FL_LED_L9_BATT_LOW;
    if (in->water && in->water_led_enabled && (in->time_valid || in->minute_counter % 2u == 0)) return FL_LED_L8_WATER;
    return FL_LED_NONE;
}

/* ---------------- Taster ---------------- */
void fl_btn_init(fl_btn_t *b) { memset(b, 0, sizeof *b); }

fl_btn_event_t fl_btn_edge(fl_btn_t *b, bool pressed, uint32_t now)
{
    if (pressed == b->pressed) return FL_BTN_EV_NONE;
    b->pressed = pressed;
    if (pressed) { b->t_press = now; b->m3 = b->m10 = false; return FL_BTN_EV_NONE; }
    if (b->stuck) { b->stuck = false; return FL_BTN_EV_UNSTUCK; }
    uint32_t d = now - b->t_press;
    if (d < FL_BTN_DEBOUNCE_MS) return FL_BTN_EV_NONE;
    if (d <= FL_BTN_SHORT_MAX_MS) {
        if (b->armed && (int32_t)(now - b->t_arm_end) < 0) { b->armed = false; return FL_BTN_EV_FACTORY_RESET; }
        return FL_BTN_EV_SHORT;
    }
    if (d >= FL_BTN_LONG_MIN_MS && d < FL_BTN_LONG_MAX_MS) { b->armed = false; return FL_BTN_EV_LONG; }
    if (d >= FL_BTN_VLONG_MIN_MS) { b->armed = true; b->t_arm_end = now + FL_BTN_CONFIRM_MS; return FL_BTN_EV_VLONG_ARMED; }
    b->armed = false;
    return FL_BTN_EV_NONE;   /* Trennbereiche 1.5-3 s und 8-10 s */
}

fl_btn_event_t fl_btn_tick(fl_btn_t *b, uint32_t now)
{
    if (b->pressed && !b->stuck) {
        uint32_t d = now - b->t_press;
        if (d >= FL_BTN_STUCK_MS) { b->stuck = true; b->armed = false; return FL_BTN_EV_STUCK; }
        if (d >= FL_BTN_VLONG_MIN_MS && !b->m10) { b->m10 = true; return FL_BTN_EV_REACHED_10S; }
        if (d >= FL_BTN_LONG_MIN_MS && !b->m3) { b->m3 = true; return FL_BTN_EV_REACHED_3S; }
    }
    if (!b->pressed && b->armed && (int32_t)(now - b->t_arm_end) >= 0) { b->armed = false; return FL_BTN_EV_ARM_EXPIRED; }
    return FL_BTN_EV_NONE;
}

uint32_t fl_btn_next_deadline(const fl_btn_t *b)
{
    if (b->pressed && !b->stuck) {
        if (!b->m3) return b->t_press + FL_BTN_LONG_MIN_MS;
        if (!b->m10) return b->t_press + FL_BTN_VLONG_MIN_MS;
        return b->t_press + FL_BTN_STUCK_MS;
    }
    if (!b->pressed && b->armed) return b->t_arm_end;
    return 0;
}
