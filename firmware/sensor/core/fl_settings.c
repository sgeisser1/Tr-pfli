/* fluidi – Einstellungen (siehe fl_settings.h). Wertebereiche und Werkswerte: PROTOCOL.md Kap. 8. */
#include "fl_settings.h"
#include "fl_proto.h"
#include "fl_util.h"

void fl_cal_defaults(fl_cal_t *c)
{
    /* Startwerte bis zur Referenz-C-Kalibrierung am Muster (PROTOTYP-PRUEFUNG, README Kap. Kalibrierung).
     * Quelle: simulation/spice/osc/osc_report.txt (R3 1 kOhm, Rev B): Ratiometrie-Fit dC = 17.29 pF,
     * C_basis = 15.21 pF; die Laufzeit tpd steckt dort bereits in C_basis -> td0 = 0 (td-Pfad bleibt fuer
     * spaetere Feinkorrektur verfuegbar). FW-3 (PINMAP Rev B): VDD 3.0 -> 2.4 V verschiebt C um -3.2 pF
     * -> c_kv = 3.2 pF / 0.6 V = 5.33 pF/V. Temperaturkoeffizient unbekannt -> 0 (am Muster bestimmen). */
    c->cref_eff = 1729;
    c->cpar = 1521;
    c->td0_ps = 0;
    c->td_kv = 0;
    c->td_kt = 0;
    c->c_kv = 533;
    c->c_kt = 0;
}

void fl_settings_user_defaults(fl_settings_t *s)
{
    s->settings_ver = 0;
    s->meas_interval_s = 14400;
    s->adv_interval_ms = 27500;
    s->adv_interval_offline_ms = 147500;
    s->tx_power_dbm = 0;
    s->water_raw = 0;
    s->water_led = 1;
    s->led_win_start = 420;
    s->led_win_end = 1140;
    s->led_level = 100;
    s->heartbeat_led = 1;
    s->avg_count = 16;
    s->air_raw = 0;
    s->flood_raw = 0;
    s->batt_low_flag = 0;
    s->ota_min_mv = 2700;
    s->diag_f2 = 6;
}

void fl_settings_defaults(fl_settings_t *s)
{
    memset(s, 0, sizeof *s);
    fl_settings_user_defaults(s);
    fl_cal_defaults(&s->cal);
}

static bool in_range(int64_t v, int64_t lo, int64_t hi) { return v >= lo && v <= hi; }

/* Ein TLV pruefen und (wenn dst != NULL) uebernehmen. Rueckgabe 0 oder Fehlercode. */
static int one_tlv(fl_settings_t *d, uint8_t id, uint8_t len, const uint8_t *v)
{
    switch (id) {
    case 0x01: if (len != 4 || !in_range(fl_get_u32(v), 900, 86400)) return FL_E_BAD_PARAM;
        d->meas_interval_s = fl_get_u32(v); return 0;
    case 0x02: if (len != 4 || !in_range(fl_get_u32(v), 1000, 150000)) return FL_E_BAD_PARAM;
        d->adv_interval_ms = fl_get_u32(v); return 0;
    case 0x03: if (len != 4 || !in_range(fl_get_u32(v), 27500, 300000)) return FL_E_BAD_PARAM;
        d->adv_interval_offline_ms = fl_get_u32(v); return 0;
    case 0x04: if (len != 1 || !in_range((int8_t)v[0], -20, 8)) return FL_E_BAD_PARAM;
        d->tx_power_dbm = (int8_t)v[0]; return 0;
    case 0x05: if (len != 2) return FL_E_BAD_PARAM; d->water_raw = fl_get_u16(v); return 0;
    case 0x06: if (len != 1 || v[0] > 1) return FL_E_BAD_PARAM; d->water_led = v[0]; return 0;
    case 0x07: if (len != 4 || fl_get_u16(v) >= 1440 || fl_get_u16(v + 2) > 1440) return FL_E_BAD_PARAM;
        d->led_win_start = fl_get_u16(v); d->led_win_end = fl_get_u16(v + 2); return 0;
    case 0x08: if (len != 1 || !in_range(v[0], 10, 100)) return FL_E_BAD_PARAM; d->led_level = v[0]; return 0;
    case 0x09: if (len != 1 || v[0] > 1) return FL_E_BAD_PARAM; d->heartbeat_led = v[0]; return 0;
    case 0x0A: if (len != 1 || !in_range(v[0], 4, 32)) return FL_E_BAD_PARAM; d->avg_count = v[0]; return 0;
    case 0x0B: if (len != 4) return FL_E_BAD_PARAM; d->air_raw = fl_get_u16(v); d->flood_raw = fl_get_u16(v + 2); return 0;
    case 0x0C: if (len != 1 || v[0] > 1) return FL_E_BAD_PARAM; d->batt_low_flag = v[0]; return 0;
    case 0x0D: if (len != 2 || !in_range(fl_get_u16(v), 2500, 3000)) return FL_E_BAD_PARAM; d->ota_min_mv = fl_get_u16(v); return 0;
    case 0x0E: if (len != 1) return FL_E_BAD_PARAM; d->diag_f2 = v[0]; return 0;
    /* Werkskalibrierung (Erweiterung) */
    case 0x10: if (len != 2 || !in_range(fl_get_u16(v), 500, 5000)) return FL_E_BAD_PARAM; d->cal.cref_eff = fl_get_u16(v); return 0;
    case 0x11: if (len != 2 || fl_get_u16(v) > 5000) return FL_E_BAD_PARAM; d->cal.cpar = fl_get_u16(v); return 0;
    case 0x12: if (len != 2 || fl_get_u16(v) > 30000) return FL_E_BAD_PARAM; d->cal.td0_ps = fl_get_u16(v); return 0;
    case 0x13: if (len != 2) return FL_E_BAD_PARAM; d->cal.td_kv = (int16_t)fl_get_u16(v); return 0;
    case 0x14: if (len != 2) return FL_E_BAD_PARAM; d->cal.td_kt = (int16_t)fl_get_u16(v); return 0;
    case 0x15: if (len != 2) return FL_E_BAD_PARAM; d->cal.c_kv = (int16_t)fl_get_u16(v); return 0;
    case 0x16: if (len != 2) return FL_E_BAD_PARAM; d->cal.c_kt = (int16_t)fl_get_u16(v); return 0;
    default: return FL_E_BAD_PARAM;
    }
}

int fl_settings_apply_tlv(fl_settings_t *s, uint16_t new_ver, const uint8_t *tlv, size_t len, uint8_t *bad_id)
{
    fl_settings_t tmp = *s;
    size_t i = 0;
    *bad_id = 0;
    while (i < len) {
        if (i + 2 > len) { *bad_id = 0xFF; return FL_E_BAD_LENGTH; }
        uint8_t id = tlv[i], l = tlv[i + 1];
        if (i + 2u + l > len) { *bad_id = id; return FL_E_BAD_LENGTH; }
        int rc = one_tlv(&tmp, id, l, tlv + i + 2);
        if (rc) { *bad_id = id; return rc; }
        i += 2u + l;
    }
    if (tmp.adv_interval_offline_ms < tmp.adv_interval_ms) { *bad_id = 0x03; return FL_E_BAD_PARAM; }
    tmp.settings_ver = new_ver;
    *s = tmp;
    return 0;
}

static size_t put(uint8_t *o, size_t pos, size_t max, uint8_t id, const uint8_t *v, uint8_t l)
{
    if (pos + 2u + l > max) return pos;
    o[pos] = id; o[pos + 1] = l;
    memcpy(o + pos + 2, v, l);
    return pos + 2u + l;
}

size_t fl_settings_encode(const fl_settings_t *s, uint8_t *o, size_t max)
{
    uint8_t b[4];
    size_t p = 0;
    if (max < 2) return 0;
    fl_put_u16(o, s->settings_ver); p = 2;
    fl_put_u32(b, s->meas_interval_s); p = put(o, p, max, 0x01, b, 4);
    fl_put_u32(b, s->adv_interval_ms); p = put(o, p, max, 0x02, b, 4);
    fl_put_u32(b, s->adv_interval_offline_ms); p = put(o, p, max, 0x03, b, 4);
    b[0] = (uint8_t)s->tx_power_dbm; p = put(o, p, max, 0x04, b, 1);
    fl_put_u16(b, s->water_raw); p = put(o, p, max, 0x05, b, 2);
    p = put(o, p, max, 0x06, &s->water_led, 1);
    fl_put_u16(b, s->led_win_start); fl_put_u16(b + 2, s->led_win_end); p = put(o, p, max, 0x07, b, 4);
    p = put(o, p, max, 0x08, &s->led_level, 1);
    p = put(o, p, max, 0x09, &s->heartbeat_led, 1);
    p = put(o, p, max, 0x0A, &s->avg_count, 1);
    fl_put_u16(b, s->air_raw); fl_put_u16(b + 2, s->flood_raw); p = put(o, p, max, 0x0B, b, 4);
    p = put(o, p, max, 0x0C, &s->batt_low_flag, 1);
    fl_put_u16(b, s->ota_min_mv); p = put(o, p, max, 0x0D, b, 2);
    p = put(o, p, max, 0x0E, &s->diag_f2, 1);
    fl_put_u16(b, s->cal.cref_eff); p = put(o, p, max, 0x10, b, 2);
    fl_put_u16(b, s->cal.cpar); p = put(o, p, max, 0x11, b, 2);
    fl_put_u16(b, s->cal.td0_ps); p = put(o, p, max, 0x12, b, 2);
    fl_put_u16(b, (uint16_t)s->cal.td_kv); p = put(o, p, max, 0x13, b, 2);
    fl_put_u16(b, (uint16_t)s->cal.td_kt); p = put(o, p, max, 0x14, b, 2);
    fl_put_u16(b, (uint16_t)s->cal.c_kv); p = put(o, p, max, 0x15, b, 2);
    fl_put_u16(b, (uint16_t)s->cal.c_kt); p = put(o, p, max, 0x16, b, 2);
    return p;
}

bool fl_settings_valid(const fl_settings_t *s)
{
    uint8_t buf[128], bad;
    fl_settings_t t;
    size_t n = fl_settings_encode(s, buf, sizeof buf);
    fl_settings_defaults(&t);
    return n > 2 && fl_settings_apply_tlv(&t, s->settings_ver, buf + 2, n - 2, &bad) == 0;
}
