/*
 * fluidi – Schnittstelle Kern <-> Plattform. Der Kern (core/) ist plattformneutral und wird auf dem Host getestet
 * (tests/port_sim.c); auf dem CC2340 implementiert platform/cc23/ diese Funktionen mit TI-Treibern/BLE-Stack.
 */
#ifndef FL_PORT_H
#define FL_PORT_H
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include "fl_meas.h"
#include "fl_ringlog.h"

/* ---- Zeit ---- */
uint32_t fl_port_ms(void);                                  /* monotone ms seit Start (Ueberlauf nach 49 d, wrap-sicher verwenden) */
void     fl_port_uptime(uint32_t *s, uint16_t *frac);
void     fl_port_delay_ms(uint32_t ms);                      /* kurze Wartezeit (blockierend) */       /* RTC aus 32.768-kHz-Quarz, frac = Bruchteil x 65536 */

/* ---- Messkette ---- */
/* Fuehrt den kompletten Messablauf aus (PINMAP Kap. 3): SENS_PWR ein, TMP1075 lesen + Shutdown, Oszillator ein
 * (Rev B: P-FET), f0 (Cref aus) / f1 (Cref1) / optional f2, Batteriespannung unter Last, alles aus. */
int      fl_port_measure(fl_meas_raw_t *raw, uint8_t n_blocks, bool with_t2);
uint16_t fl_port_vbat_mv(void);                             /* Batteriemonitor jetzt (mV) */

/* ---- LED ---- */
void     fl_port_led(uint8_t col, uint8_t level_pct);       /* col: FL_COL_* Bitmaske; 0 = aus */

/* ---- BLE ---- */
void     fl_port_ble_addr(uint8_t addr_le[6]);              /* oeffentliche Adresse aus FCFG, LSB zuerst */
int      fl_port_adv_set(const uint8_t *data, uint8_t len, uint32_t interval_ms, bool connectable, bool enable);
int      fl_port_ble_send(const uint8_t *frame, uint16_t len);  /* 0 ok, 1 Puffer voll (spaeter erneut), <0 Fehler */
void     fl_port_ble_disconnect(void);
uint16_t fl_port_ble_mtu(void);
void     fl_port_tx_power(int8_t dbm);

/* ---- Krypto ---- */
int      fl_port_rng(uint8_t *buf, size_t len);
int      fl_port_ecdh_keygen(uint8_t priv[32], uint8_t pub[64]);            /* pub = X||Y big-endian */
int      fl_port_ecdh_shared(const uint8_t priv[32], const uint8_t peer[64], uint8_t z[32]);

/* ---- nichtfluechtiger Speicher ---- */
enum { FL_NV_SETTINGS = 1, FL_NV_PAIR = 2, FL_NV_COUNTERS = 3, FL_NV_LOGMETA = 4, FL_NV_DIAG = 5 };
int      fl_port_nv_read(uint8_t id, void *buf, uint16_t len);   /* 0 = ok */
int      fl_port_nv_write(uint8_t id, const void *buf, uint16_t len);
int      fl_port_nv_delete(uint8_t id);
const fl_flash_t *fl_port_log_flash(void);
const fl_flash_t *fl_port_slot1_flash(void);

/* ---- MCUboot ---- */
int      fl_port_ota_request_test(void);     /* boot_set_pending(0): Image in Slot 1 als "Test" markieren */
int      fl_port_ota_confirm(void);          /* boot_set_confirmed(): laufendes Image bestaetigen */
bool     fl_port_image_confirmed(void);
void     fl_port_fw_version(uint8_t ver[4], uint32_t *build, uint32_t *sec_cnt);   /* aus eigenem MCUboot-Kopf/TLV */

/* ---- System ---- */
uint8_t  fl_port_reset_reason(void);         /* FL_RR_* */
void     fl_port_reboot(void);
void     fl_port_shutdown(void);             /* Shutdown; Wecken per Taster, AUSSER der Taster ist gerade gedrueckt
                                              * (dann Pull-up aus, kein Wecken -> nur Zellwechsel, F-W3b) */
uint32_t fl_port_retained_get(void);         /* Retention-Register (FL_RET_*) */
void     fl_port_retained_set(uint32_t v);
void     fl_port_wdt_kick(void);
void     fl_port_button_pullup(bool on);
bool     fl_port_button_pressed(void);       /* Pegel jetzt (mit kurz eingeschaltetem Pull-up) */

#endif
