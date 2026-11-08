/* fluidi – simulierte Plattform fuer Host-Tests (implementiert core/fl_port.h ohne Hardware). */
#include "port_sim.h"
#include "fl_proto.h"
#include "fl_app.h"
#include "fl_util.h"
#include "vectors.h"
#include <stdio.h>
#include <stdlib.h>

sim_t sim;

/* ---- Flash im RAM ---- */
static uint8_t log_mem[0x6000], slot1_mem[0x38800];
typedef struct { uint8_t *mem; uint32_t size; int fail_write_after; } ramflash_t;
static ramflash_t rf_log = {log_mem, sizeof log_mem, -1}, rf_slot1 = {slot1_mem, sizeof slot1_mem, -1};

static int rf_read(void *c, uint32_t off, void *buf, size_t len)
{
    ramflash_t *r = c;
    if (off + len > r->size) return -1;
    memcpy(buf, r->mem + off, len);
    return 0;
}
static int rf_write(void *c, uint32_t off, const void *buf, size_t len)
{
    ramflash_t *r = c;
    const uint8_t *b = buf;
    if (off + len > r->size) return -1;
    if (r->fail_write_after == 0) {             /* Stromausfall simulieren: halber Eintrag geschrieben */
        for (size_t i = 0; i < len / 2; i++) r->mem[off + i] &= b[i];
        r->fail_write_after = -1;
        return -1;
    }
    if (r->fail_write_after > 0) r->fail_write_after--;
    for (size_t i = 0; i < len; i++) r->mem[off + i] &= b[i];   /* Flash: nur 1 -> 0 */
    sim.flash_writes++;
    return 0;
}
static int rf_erase(void *c, uint32_t off)
{
    ramflash_t *r = c;
    if (off >= r->size) return -1;
    off &= ~0x7FFu;
    memset(r->mem + off, 0xFF, 0x800);
    sim.flash_erases++;
    return 0;
}
static fl_flash_t fl_log_dev = {rf_read, rf_write, rf_erase, &rf_log, sizeof log_mem, 0x800};
static fl_flash_t fl_slot1_dev = {rf_read, rf_write, rf_erase, &rf_slot1, sizeof slot1_mem, 0x800};

void sim_flash_erase_all(void) { memset(log_mem, 0xFF, sizeof log_mem); memset(slot1_mem, 0xFF, sizeof slot1_mem); }
void sim_log_fail_next_write(int after) { rf_log.fail_write_after = after; }
uint8_t *sim_slot1(void) { return slot1_mem; }

void sim_reset_all(void)
{
    memset(&sim, 0, sizeof sim);
    sim_flash_erase_all();
    sim.vbat = 2950; sim.c_probe_pf = 30.0; sim.temp = 2150; sim.temp_ok = true;
    sim.ms = 1000;
    sim.fw_ver[0] = 0; sim.fw_ver[1] = 1; sim.fw_build = 1;
    sim.image_confirmed = true;
}

/* ---- Zeit ---- */
uint32_t fl_port_ms(void) { return sim.ms; }
void fl_port_delay_ms(uint32_t ms) { sim.ms += ms; }
void fl_port_uptime(uint32_t *s, uint16_t *frac) { *s = sim.ms / 1000u; *frac = (uint16_t)((sim.ms % 1000u) * 65536u / 1000u); }

/* ---- Messkette: Oszillatormodell T = k*(C + Cpar + Cref?) + td, Rev B mit Teiler 8 ---- */
int fl_port_measure(fl_meas_raw_t *raw, uint8_t n, bool with_t2)
{
    /* Modell passend zu den Werks-Startwerten: dC 17.29 pF, C_basis 15.21 pF (osc_report.txt), td im Fit enthalten,
     * VDD-Offset -3.2 pF bei 2.4 V (FW-3) */
    const double k_ps_per_pf = 950.0;   /* 0.95 * R(1 k) -> 0.95 ns/pF (CONCEPTS 2.3 T ~ 0.95 RC) */
    const double cpar = 15.21, cref = 17.29, td = 0.0;
    const double cvdd = -5.333 * (3000 - sim.vbat) / 1000.0;   /* scheinbare C-Verschiebung */
    memset(raw, 0, sizeof *raw);
    sim.meas_calls++;
    raw->n = n; raw->temp_ok = sim.temp_ok; raw->temp_c100 = sim.temp; raw->vbat_load_mv = sim.vbat_load ? sim.vbat_load : sim.vbat;
    raw->vdd_ref_mv = sim.vbat;
    if (sim.osc_dead) { raw->osc_timeout = true; return -1; }
    for (uint8_t i = 0; i < n; i++) {
        double t0 = k_ps_per_pf * (sim.c_probe_pf + cvdd + cpar) + td;          /* Oszillatorperiode ps */
        double t1 = k_ps_per_pf * (sim.c_probe_pf + cvdd + cpar + cref) + td;
        double t2 = k_ps_per_pf * (sim.c_probe_pf + cvdd + cpar + cref + 100.0) + td;
        /* Pinperiode in 48-MHz-Takten (x8 Teiler), Q16 */
        raw->t0_q16[i] = (uint32_t)(t0 * 8.0 / 20833.3333 * 65536.0);
        raw->t1_q16[i] = (uint32_t)(t1 * 8.0 / 20833.3333 * 65536.0);
        raw->t2_q16[i] = (uint32_t)(t2 * 8.0 / 20833.3333 * 65536.0);
        if (sim.outlier_block >= 0 && i == sim.outlier_block) raw->t0_q16[i] += raw->t0_q16[i] / 10;
    }
    raw->has_t2 = with_t2;
    return 0;
}
uint16_t fl_port_vbat_mv(void) { return sim.vbat; }   /* Ruhewert; Lastwert nur in fl_port_measure */

/* ---- LED ---- */
void fl_port_led(uint8_t col, uint8_t level)
{
    (void)level;
    if (col && col != sim.led_col) { sim.led_on_events++; sim.led_last_on = col; }
    sim.led_col = col;
}

/* ---- BLE ---- */
void fl_port_ble_addr(uint8_t a[6]) { memcpy(a, V_ADDR, 6); }
int fl_port_adv_set(const uint8_t *d, uint8_t len, uint32_t iv, bool conn, bool en)
{
    if (d && len <= 31) { memcpy(sim.adv, d, len); sim.adv_len = len; }
    sim.adv_int = iv; sim.adv_conn = conn; sim.adv_on = en; sim.adv_updates++;
    return 0;
}
int fl_port_ble_send(const uint8_t *f, uint16_t len)
{
    if (sim.tx_busy) return 1;
    if (sim.tx_n >= SIM_TX_MAX || len > 247) return -1;
    memcpy(sim.tx[sim.tx_n], f, len); sim.tx_len[sim.tx_n] = len; sim.tx_n++;
    return 0;
}
void fl_port_ble_disconnect(void) { sim.disconnect_req++; }
uint16_t fl_port_ble_mtu(void) { return sim.mtu ? sim.mtu : 247; }
void fl_port_tx_power(int8_t dbm) { sim.tx_power = dbm; }

/* ---- Krypto ---- */
int fl_port_rng(uint8_t *b, size_t n)
{
    if (sim.rng_fail) { memset(b, 0, n); return -1; }
    for (size_t i = 0; i < n; i++) {
        if (sim.rng_q_len) { b[i] = sim.rng_q[sim.rng_q_pos++]; if (sim.rng_q_pos >= sim.rng_q_len) sim.rng_q_len = 0, sim.rng_q_pos = 0; }
        else b[i] = (uint8_t)(0x5A ^ (sim.rng_ctr++ * 37u));
    }
    return 0;
}
void sim_rng_queue(const uint8_t *b, size_t n) { memcpy(sim.rng_q, b, n); sim.rng_q_len = n; sim.rng_q_pos = 0; }
int fl_port_ecdh_keygen(uint8_t priv[32], uint8_t pub[64]) { memset(priv, 0x77, 32); memcpy(pub, V_SPUB, 64); return 0; }
int fl_port_ecdh_shared(const uint8_t priv[32], const uint8_t peer[64], uint8_t z[32])
{
    (void)priv;
    if (memcmp(peer, V_GWPUB, 64)) return -1;
    memcpy(z, V_Z, 32);
    return 0;
}

/* ---- NV ---- */
int fl_port_nv_read(uint8_t id, void *buf, uint16_t len)
{
    if (id >= SIM_NV_MAX || sim.nv_len[id] != len) return -1;
    memcpy(buf, sim.nv[id], len);
    return 0;
}
int fl_port_nv_write(uint8_t id, const void *buf, uint16_t len)
{
    if (id >= SIM_NV_MAX || len > sizeof sim.nv[0]) return -1;
    memcpy(sim.nv[id], buf, len); sim.nv_len[id] = len; sim.nv_writes++;
    return 0;
}
int fl_port_nv_delete(uint8_t id) { if (id < SIM_NV_MAX) sim.nv_len[id] = 0; return 0; }
const fl_flash_t *fl_port_log_flash(void) { return &fl_log_dev; }
const fl_flash_t *fl_port_slot1_flash(void) { return &fl_slot1_dev; }

/* ---- MCUboot ---- */
int fl_port_ota_request_test(void) { sim.ota_pending = true; return 0; }
int fl_port_ota_confirm(void) { sim.image_confirmed = true; return 0; }
bool fl_port_image_confirmed(void) { return sim.image_confirmed; }
void fl_port_fw_version(uint8_t v[4], uint32_t *b, uint32_t *sc) { memcpy(v, sim.fw_ver, 4); *b = sim.fw_build; *sc = sim.sec_cnt; }

/* ---- System ---- */
uint8_t fl_port_reset_reason(void) { return sim.reset_reason; }
void fl_port_reboot(void) { sim.reboots++; }
void fl_port_shutdown(void) { sim.shutdowns++; sim.shutdown_wake = !sim.button_level; sim.pullup = !sim.button_level; }
uint32_t fl_port_retained_get(void) { return sim.retained; }
void fl_port_retained_set(uint32_t v) { sim.retained = v & 0x3FFFFu; }
/* Nachbildung von fl_fault_handler: AONRCLR1 = FL_RET_PLANNED, AONRSET1 = FL_RET_FAULT, PMCTLResetSystem
 * (naechster Start: reset_reason FL_RR_SOFTWARE = PMCTL_RESET_SYSTEM; setzt der Test) */
void sim_fault(void) { sim.retained = ((sim.retained & ~FL_RET_PLANNED) | FL_RET_FAULT) & 0x3FFFFu; sim.reboots++; }
void fl_port_wdt_kick(void) { sim.wdt_kicks++; }
void fl_port_button_pullup(bool on) { sim.pullup = on; }
bool fl_port_button_pressed(void) { return sim.button_level; }

#if defined(FLUIDI_TESTFW) && FLUIDI_TESTFW
/* ---- Testfirmware ---- */
uint32_t fl_port_tf_flash_ops(void) { return sim.nv_writes + sim.flash_writes + sim.flash_erases; }
void fl_port_tf_hang(void) { sim.tf_hangs++; }                  /* Hardware: Endlosschleife -> Watchdog */
void fl_port_tf_fatal(uint8_t kind)
{
    if (kind) { sim.tf_fatal_hf++; sim_fault(); }                /* __builtin_trap -> HardFault -> fl_fault_handler */
    else { sim.tf_fatal_series++; sim.reboots++; }              /* fl_platform_fatal: Systemreset ohne Bit */
}
int fl_port_tf3_tmp_read(int16_t *t, uint8_t *stage)
{
    sim.tf3_reads++;
    *stage = sim.tf3_fail_stage;
    if (sim.tf3_fail_stage) return -1;
    *t = sim.temp;
    return 0;
}
#endif
