/*
 * fluidi – Messauswertung (plattformneutral): robuste Mittelung (REQ-MES-10), ratiometrische Kapazitaet mit
 * Cref1 und tpd-Korrektur (CONCEPTS 2.3, MESSKETTE_SALZ.md Kap. 5 D3), Plausibilitaetsflags (REQ-MES-12),
 * Feuchteindex (Referenzformel, massgebend ist das Gateway: PROTOCOL.md Kap. 1 "Kalibrierung im Gateway").
 *
 * Rohdaten vom Port: je Konfiguration (f0 ohne Cref, f1 mit Cref1, Rev A optional f2 mit Cref2) `n` Blockmittel
 * der Periodendauer AM TIMER-PIN (MEAS_CLK) in 48-MHz-Takten, Q16 (Wert * 65536). Rev B: Pinperiode = 8 x f_osc-Periode.
 * Plausibel: MEAS_CLK 0.048..12 MHz (4..1000 Takte); deckt R3 1 k (0.59-4.51 MHz) und 10 k (0.07-0.65 MHz) ab.
 */
#ifndef FL_MEAS_H
#define FL_MEAS_H
#include <stdint.h>
#include <stdbool.h>
#include "fl_settings.h"

#define FL_MEAS_MAX_BLOCKS 32

typedef struct {
    uint8_t  n;                              /* Bloecke je Konfiguration (= avg_count) */
    uint32_t t0_q16[FL_MEAS_MAX_BLOCKS];
    uint32_t t1_q16[FL_MEAS_MAX_BLOCKS];
    uint32_t t2_q16[FL_MEAS_MAX_BLOCKS];
    bool     has_t2;
    bool     osc_timeout;                    /* Port: keine Flanken innerhalb der Frist */
    bool     temp_ok;
    int16_t  temp_c100;                      /* 0.01 degC */
    uint16_t vbat_load_mv;                   /* Batteriemonitor waehrend Messkette ein (Datensatz, Unterspannung) */
    uint16_t vdd_ref_mv;                     /* FW-3: VDD ohne Funk-/LED-Last unmittelbar vor dem 1. Burst */
} fl_meas_raw_t;

typedef struct {
    uint16_t c_probe;   /* 0.01 pF oder FL_C_INVALID */
    uint16_t c_diag;
    int16_t  temp;
    uint16_t vbat_mv;
    uint8_t  flags;     /* FL_RF_* */
    uint8_t  error;     /* 0 oder FL_E_MEAS_* / FL_E_TEMP_FAIL fuer das Fehlerprotokoll */
} fl_meas_result_t;

/* Rohdaten FW-2: hoechstens 4 Bursts; je Burst werden f0 und f1 in n/4 Teilbloecke zerlegt (n <= 16). */
#define FL_MEAS_BLOCKS_MAX_FW2 16

/* Robuster Mittelwert: Median, MAD, Verwerfen |x-med| > 4*1.4826*MAD + 0.05 % (ANNAHME Schwellen).
 * *outlier = mindestens ein Block verworfen; *noisy = MAD/Median > 0.2 % (ANNAHME). Rueckgabe Mittel Q16. */
uint32_t fl_meas_robust_mean(const uint32_t *x, uint8_t n, bool *outlier, bool *noisy);

/* Pinperiode (Q16 Takte) -> Oszillatorperiode in ps */
uint32_t fl_meas_period_ps(uint32_t pin_q16, uint8_t divider);

/* Schleifenlaufzeit td in ps (tpd-Korrektur ueber VDD und Temperatur) */
int32_t fl_meas_td_ps(const fl_cal_t *cal, uint16_t vdd_mv, int16_t temp_c100, bool temp_ok);

/* C_sonde in 0.01 pF aus T0/T1 (ps) – ratiometrisch: C = Cref*(T0-td)/(T1-T0) - Cpar. Rueckgabe < 0 = ungueltig */
int32_t fl_meas_cap(const fl_cal_t *cal, uint32_t t0_ps, uint32_t t1_ps, int32_t td_ps);
/* FW-3: Offset-Korrektur ueber VDD und Temperatur (0.01 pF) */
int32_t fl_meas_offset_corr(const fl_cal_t *cal, int32_t c, uint16_t vdd_mv, int16_t temp_c100, bool temp_ok);

/* Vollstaendige Auswertung */
void fl_meas_evaluate(const fl_meas_raw_t *raw, const fl_settings_t *s, uint8_t divider, fl_meas_result_t *out);

/* Feuchteindex in Promille (Referenz): (C - C_trocken)/(C_nass - C_trocken)*1000, NICHT begrenzt
 * (> 1000 = Duenger-Hinweis, MESSKETTE_SALZ.md Kap. 5). INT32_MIN bei ungueltigen Eingaben. */
int32_t fl_moisture_permille(uint16_t c, uint16_t c_dry, uint16_t c_wet);

/* "Giessen noetig" (REQ-UI-07): Schwelle water_raw vom Gateway; trockener = kleinere Kapazitaet */
bool fl_water_needed(uint16_t c_probe, uint16_t water_raw);

#endif
