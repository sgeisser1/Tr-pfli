/* fluidi – Messauswertung (siehe fl_meas.h). */
#include "fl_meas.h"
#include "fl_proto.h"
#include <limits.h>

static void isort(uint32_t *a, uint8_t n)
{
    for (uint8_t i = 1; i < n; i++) {
        uint32_t v = a[i];
        int j = i - 1;
        while (j >= 0 && a[j] > v) { a[j + 1] = a[j]; j--; }
        a[j + 1] = v;
    }
}

static uint32_t median_sorted(const uint32_t *a, uint8_t n)
{
    return (n & 1) ? a[n / 2] : (uint32_t)(((uint64_t)a[n / 2 - 1] + a[n / 2]) / 2);
}

uint32_t fl_meas_robust_mean(const uint32_t *x, uint8_t n, bool *outlier, bool *noisy)
{
    uint32_t s[FL_MEAS_MAX_BLOCKS], dev[FL_MEAS_MAX_BLOCKS];
    *outlier = false; *noisy = false;
    if (n == 0) return 0;
    if (n > FL_MEAS_MAX_BLOCKS) n = FL_MEAS_MAX_BLOCKS;
    for (uint8_t i = 0; i < n; i++) s[i] = x[i];
    isort(s, n);
    uint32_t med = median_sorted(s, n);
    for (uint8_t i = 0; i < n; i++) dev[i] = s[i] > med ? s[i] - med : med - s[i];
    isort(dev, n);
    uint32_t mad = median_sorted(dev, n);
    /* Grenze: 4 * 1.4826 * MAD (~ 4 sigma) + 0.05 % des Medians (Quantisierungsboden) */
    uint64_t lim = ((uint64_t)mad * 5930u) / 1000u + med / 2000u;
    uint64_t sum = 0;
    uint8_t k = 0;
    for (uint8_t i = 0; i < n; i++) {
        uint32_t d = x[i] > med ? x[i] - med : med - x[i];
        if (d <= lim) { sum += x[i]; k++; } else *outlier = true;
    }
    if (med && (uint64_t)mad * 1000u > (uint64_t)med * 2u) *noisy = true;
    if (k == 0) return med;
    return (uint32_t)((sum + k / 2) / k);
}

uint32_t fl_meas_period_ps(uint32_t pin_q16, uint8_t divider)
{
    /* 1 Takt 48 MHz = 62500/3 ps */
    if (divider == 0) divider = 1;
    uint64_t num = (uint64_t)pin_q16 * 62500u;
    uint64_t den = (uint64_t)3u * 65536u * divider;
    return (uint32_t)((num + den / 2) / den);
}

int32_t fl_meas_td_ps(const fl_cal_t *cal, uint16_t vdd_mv, int16_t temp_c100, bool temp_ok)
{
    int32_t td = cal->td0_ps;
    if (vdd_mv) td += (int32_t)cal->td_kv * ((int32_t)vdd_mv - 3000) / 1000;
    if (temp_ok) td += (int32_t)cal->td_kt * ((int32_t)temp_c100 - 2500) / 100;
    return td < 0 ? 0 : td;
}

int32_t fl_meas_cap(const fl_cal_t *cal, uint32_t t0_ps, uint32_t t1_ps, int32_t td_ps)
{
    if (t1_ps <= t0_ps || (int64_t)t0_ps <= td_ps) return -1;
    int64_t c = (int64_t)cal->cref_eff * ((int64_t)t0_ps - td_ps);
    int64_t d = (int64_t)t1_ps - t0_ps;
    c = (c + d / 2) / d - cal->cpar;
    if (c < 0 || c > 0xFFFE) return -1;
    return (int32_t)c;
}

int32_t fl_meas_offset_corr(const fl_cal_t *cal, int32_t c, uint16_t vdd_mv, int16_t temp_c100, bool temp_ok)
{
    if (vdd_mv) c += (int32_t)cal->c_kv * (3000 - (int32_t)vdd_mv) / 1000;
    if (temp_ok) c -= (int32_t)cal->c_kt * ((int32_t)temp_c100 - 2500) / 10000;
    return c;
}

void fl_meas_evaluate(const fl_meas_raw_t *raw, const fl_settings_t *s, uint8_t divider, fl_meas_result_t *o)
{
    bool out0, out1, nz0, nz1, o2 = false, n2 = false;
    o->flags = 0; o->error = 0;
    o->c_probe = FL_C_INVALID; o->c_diag = FL_C_INVALID;
    o->vbat_mv = raw->vbat_load_mv;
    o->temp = raw->temp_ok ? raw->temp_c100 : FL_TEMP_INVALID;
    if (!raw->temp_ok) { o->flags |= FL_RF_TEMP_INVALID; o->error = FL_E_TEMP_FAIL; }
    if (raw->osc_timeout || raw->n == 0) { o->flags |= FL_RF_CHAIN_FAULT; o->error = FL_E_MEAS_OSC_FAIL; return; }

    uint32_t m0 = fl_meas_robust_mean(raw->t0_q16, raw->n, &out0, &nz0);
    uint32_t m1 = fl_meas_robust_mean(raw->t1_q16, raw->n, &out1, &nz1);
    /* MEAS_CLK 0.048..12 MHz (Fehlercode 0x20) <=> Pinperiode 4..1000 Takte (siehe fl_meas.h) */
    if (m0 < (4u << 16) || m0 > (1000u << 16) || m1 < (4u << 16) || m1 > (1000u << 16)) {
        o->flags |= FL_RF_CHAIN_FAULT; o->error = FL_E_MEAS_OSC_FAIL; return;
    }
    if (out0 || out1) o->flags |= FL_RF_OUTLIER;
    if (nz0 || nz1) { o->flags |= FL_RF_NOISY; if (!o->error) o->error = FL_E_MEAS_NOISY; }

    uint32_t t0 = fl_meas_period_ps(m0, divider), t1 = fl_meas_period_ps(m1, divider);
    uint16_t vref = raw->vdd_ref_mv ? raw->vdd_ref_mv : raw->vbat_load_mv;   /* FW-3: VDD ohne Funk/LED */
    int32_t td = fl_meas_td_ps(&s->cal, vref, raw->temp_c100, raw->temp_ok);
    int32_t c = fl_meas_cap(&s->cal, t0, t1, td);
    if (c >= 0) c = fl_meas_offset_corr(&s->cal, c, vref, raw->temp_c100, raw->temp_ok);
    if (c < 0 || c > 0xFFFE) { o->flags |= FL_RF_CHAIN_FAULT; o->error = FL_E_MEAS_RANGE; return; }
    o->c_probe = (uint16_t)c;

    if (raw->has_t2) {
        /* Diagnose (Rev A, Cref2): scheinbare Sondenkapazitaet bei f2 mit gleicher Steigung k = (T1-T0)/Cref.
         * Cref2 nominal 100 pF (C23, parts.py) – ANNAHME ohne Einzelkalibrierung. */
        uint32_t m2 = fl_meas_robust_mean(raw->t2_q16, raw->n, &o2, &n2);
        uint32_t t2 = fl_meas_period_ps(m2, divider);
        if (t2 > t1 && t1 > t0) {
            int64_t cd = (int64_t)s->cal.cref_eff * ((int64_t)t2 - td) / ((int64_t)t1 - t0) - s->cal.cpar - 10000;
            if (cd >= 0 && cd < 0xFFFF) o->c_diag = (uint16_t)cd;
        }
    }
    if (s->air_raw && o->c_probe < s->air_raw) o->flags |= FL_RF_AIR;
    if (s->flood_raw && o->c_probe > s->flood_raw) o->flags |= FL_RF_FLOOD;
}

int32_t fl_moisture_permille(uint16_t c, uint16_t c_dry, uint16_t c_wet)
{
    if (c == FL_C_INVALID || c_wet <= c_dry) return INT32_MIN;
    return (int32_t)(((int64_t)c - c_dry) * 1000 / ((int64_t)c_wet - c_dry));
}

bool fl_water_needed(uint16_t c_probe, uint16_t water_raw)
{
    return water_raw != 0 && c_probe != FL_C_INVALID && c_probe < water_raw;
}
