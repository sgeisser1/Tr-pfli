/*
 * fluidi – Einstellungen (PROTOCOL.md Kap. 8), TLV-Kodierung, Pruefung, Werkswerte. Plattformneutral.
 *
 * Erweiterung (neue TLV-ids, kompatibel nach Kap. 13 "neue id statt Bedeutungsaenderung"; Vorschlag Firmware
 * Welle 2, Pruefung Software-Agent): 0x10..0x16 = Werkskalibrierung der Messkette (Referenz-C-Kalibrierung,
 * MESSKETTE_SALZ.md Kap. 5 "tpd-Korrektur"). Diese Werte bleiben bei Werkseinstellung/UNPAIR erhalten.
 */
#ifndef FL_SETTINGS_H
#define FL_SETTINGS_H
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

typedef struct {
    uint16_t cref_eff;      /* 0.01 pF: wirksame Cref1-Differenz (Cref1 minus "aus"-Serienkapazitaet) */
    uint16_t cpar;          /* 0.01 pF: Parallelkapazitaet Knoten/Leitung */
    uint16_t td0_ps;        /* ps: Schleifenlaufzeit je Oszillatorperiode (2 x tpd) bei 3.0 V / 25 C */
    int16_t  td_kv;         /* ps/V: Aenderung von td mit VDD (negativ: td steigt bei sinkender Spannung) */
    int16_t  td_kt;         /* ps/K: Aenderung von td mit Temperatur */
    int16_t  c_kv;          /* 0.01 pF/V: Offset-Korrektur C ueber VDD (FW-3): C += c_kv*(3.0 V - VDD) */
    int16_t  c_kt;          /* 0.001 pF/K: Offset-Korrektur C ueber Temperatur (FW-3): C -= c_kt*(T-25) */
} fl_cal_t;

typedef struct {
    uint16_t settings_ver;
    uint32_t meas_interval_s;
    uint32_t adv_interval_ms;
    uint32_t adv_interval_offline_ms;
    int8_t   tx_power_dbm;
    uint16_t water_raw;
    uint8_t  water_led;
    uint16_t led_win_start, led_win_end;
    uint8_t  led_level;
    uint8_t  heartbeat_led;
    uint8_t  avg_count;
    uint16_t air_raw, flood_raw;
    uint8_t  batt_low_flag;
    uint16_t ota_min_mv;
    uint8_t  diag_f2;
    uint8_t  led_weekdays;  /* 0x0F: Bit0 = Montag .. Bit6 = Sonntag (v2, W-7) */
    fl_cal_t cal;
} fl_settings_t;

void fl_settings_defaults(fl_settings_t *s);           /* alles inkl. Kalibrierung */
void fl_settings_user_defaults(fl_settings_t *s);      /* nur Nutzereinstellungen, Kalibrierung bleibt */
void fl_cal_defaults(fl_cal_t *c);

/* SET_SETTINGS-Nutzlast ohne settings_ver anwenden (atomar). Rueckgabe 0 = ok, sonst Fehlercode;
 * *bad_id erhaelt die beanstandete TLV-id. */
int fl_settings_apply_tlv(fl_settings_t *s, uint16_t new_ver, const uint8_t *tlv, size_t len, uint8_t *bad_id);
/* GET_SETTINGS: settings_ver u16 + TLV-Liste. Rueckgabe Laenge. */
size_t fl_settings_encode(const fl_settings_t *s, uint8_t *out, size_t max);
/* Plausibilitaet einer gelesenen Struktur (z. B. nach NV-Lesen). */
bool fl_settings_valid(const fl_settings_t *s);

#endif
