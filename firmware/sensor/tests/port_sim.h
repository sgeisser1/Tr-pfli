#ifndef PORT_SIM_H
#define PORT_SIM_H
#include "fl_port.h"
#include <string.h>

#define SIM_TX_MAX 64
#define SIM_NV_MAX 8

typedef struct {
    uint32_t ms;
    uint16_t vbat, vbat_load;
    double c_probe_pf;
    int16_t temp; bool temp_ok; bool osc_dead; int outlier_block;
    uint32_t meas_calls;
    uint8_t led_col, led_last_on; uint32_t led_on_events;
    uint8_t adv[31]; uint8_t adv_len; uint32_t adv_int; bool adv_conn, adv_on; uint32_t adv_updates;
    uint8_t tx[SIM_TX_MAX][247]; uint16_t tx_len[SIM_TX_MAX]; uint32_t tx_n; bool tx_busy;
    uint32_t disconnect_req;
    uint16_t mtu; int8_t tx_power;
    uint8_t rng_q[64]; size_t rng_q_len, rng_q_pos; uint32_t rng_ctr;
    uint8_t nv[SIM_NV_MAX][256]; uint16_t nv_len[SIM_NV_MAX]; uint32_t nv_writes;
    bool ota_pending, image_confirmed;
    uint8_t fw_ver[4]; uint32_t fw_build, sec_cnt;
    uint32_t retained; bool rng_fail; bool shutdown_wake;
    uint8_t reset_reason;
    uint32_t reboots, shutdowns, wdt_kicks;
    bool pullup, button_level;
    uint32_t flash_writes, flash_erases;
} sim_t;

extern sim_t sim;
void sim_reset_all(void);
void sim_flash_erase_all(void);
void sim_log_fail_next_write(int after);
void sim_rng_queue(const uint8_t *b, size_t n);
uint8_t *sim_slot1(void);

#endif
