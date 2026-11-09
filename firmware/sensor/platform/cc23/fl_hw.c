/*
 * fluidi – CC2340R52 (QFN24 RGE): Hardware-Port fuer core/fl_port.h.
 * Pins ausschliesslich aus config/fluidi_board.h (PINMAP_SENSOR.md Rev B), Flash aus config/fluidi_flash_layout.h.
 * Alles, was nur am Muster nachweisbar ist, ist mit PROTOTYP-PRUEFUNG markiert.
 */
#include <string.h>
#include <FreeRTOS.h>
#include <task.h>
#include <timers.h>
#include <ti/drivers/GPIO.h>
#include <ti/drivers/I2C.h>
#include <ti/drivers/NVS.h>
#include <ti/drivers/Power.h>
#include <ti/drivers/power/PowerCC23X0.h>
#include <ti/drivers/Watchdog.h>
#include <ti/drivers/RNG.h>
#include <ti/drivers/AESECB.h>
#include <ti/drivers/ECDH.h>
#include <ti/drivers/BatteryMonitor.h>
#include <ti/drivers/cryptoutils/cryptokey/CryptoKeyPlaintext.h>
#include <ti/drivers/cryptoutils/ecc/ECCParams.h>
#include <ti/devices/DeviceFamily.h>
#include DeviceFamily_constructPath(inc/hw_memmap.h)
#include DeviceFamily_constructPath(inc/hw_types.h)
#include DeviceFamily_constructPath(inc/hw_lgpt.h)
#include DeviceFamily_constructPath(inc/hw_systim.h)
#include DeviceFamily_constructPath(inc/hw_pmctl.h)
#include DeviceFamily_constructPath(driverlib/pmctl.h)
#include "ti_drivers_config.h"
#include "ti/ble/app_util/framework/bleapputil_api.h"
#include "ti/ble/app_util/framework/bleapputil_timers.h"
#include "sysflash/sysflash.h"
#include "bootutil/bootutil_public.h"
#include "bootutil/image.h"
#include "fl_app.h"
#include "fl_port.h"
#include "fl_nvstore.h"
#include "fl_ota.h"
#include "fl_platform.h"
#include "fl_testfw.h"
#include "../../config/fluidi_board.h"
#include "../../config/fluidi_flash_layout.h"

/* ======================= Zeit ======================= */
uint32_t fl_port_ms(void) { return (uint32_t)(xTaskGetTickCount() * portTICK_PERIOD_MS); }
void fl_port_uptime(uint32_t *s, uint16_t *frac)
{
    uint32_t ms = fl_port_ms();
    *s = ms / 1000u;
    *frac = (uint16_t)((ms % 1000u) * 65536u / 1000u);
}
static uint32_t systim_us(void) { return HWREG(SYSTIM_BASE + SYSTIM_O_TIME1U); }
static void delay_us(uint32_t us) { uint32_t t0 = systim_us(); while (systim_us() - t0 < us) { } }
static void sleep_ms(uint32_t ms) { vTaskDelay(pdMS_TO_TICKS(ms)); }   /* Task schlaeft -> Standby */
void fl_port_delay_ms(uint32_t ms) { delay_us(ms * 1000u); }

/* ======================= Pins / Ruhezustand ======================= */
static void pins_sleep_state(void)
{
    /* FW-8: DIO11 high (Kette aus), DIO12 low, DIO16/17 low (FW-1/FW-6), DIO8 + DIO24 Puffer aus, LEDs high */
#if FLUIDI_HAS_OSC_FET
    GPIO_setConfig(FLUIDI_DIO_OSC_EN_N, GPIO_CFG_OUTPUT | GPIO_CFG_OUT_HIGH);
#endif
#if FLUIDI_TESTFW == 3
    /* TESTFIRMWARE TF-3 (Anhang A, PT11.19/ST-W4): SENS_PWR DAUERND high (TMP1075N + R4/R5 versorgt); SDA/SCL
     * hochohmig ohne Pull (R4/R5 ziehen auf SENS_PWR) statt low, sonst floesse VDD/R4 bzw. VDD/R5 dauernd. */
    GPIO_setConfig(FLUIDI_DIO_SENS_PWR, GPIO_CFG_OUTPUT | GPIO_CFG_OUT_STR_HIGH | GPIO_CFG_OUT_HIGH);
    GPIO_setConfig(FLUIDI_DIO_I2C_SDA, GPIO_CFG_NO_DIR);
    GPIO_setConfig(FLUIDI_DIO_I2C_SCL, GPIO_CFG_NO_DIR);
#else
    GPIO_setConfig(FLUIDI_DIO_SENS_PWR, GPIO_CFG_OUTPUT | GPIO_CFG_OUT_STR_HIGH | GPIO_CFG_OUT_LOW);
    GPIO_setConfig(FLUIDI_DIO_I2C_SDA, GPIO_CFG_OUTPUT | GPIO_CFG_OUT_LOW);
    GPIO_setConfig(FLUIDI_DIO_I2C_SCL, GPIO_CFG_OUTPUT | GPIO_CFG_OUT_LOW);
#endif
    GPIO_setConfig(FLUIDI_DIO_CREF1, GPIO_CFG_NO_DIR);
#if FLUIDI_HAS_CREF2
    GPIO_setConfig(FLUIDI_DIO_CREF2, GPIO_CFG_NO_DIR);
#endif
    GPIO_setConfig(FLUIDI_DIO_MEAS_CLK, GPIO_CFG_NO_DIR);
    GPIO_setConfig(FLUIDI_DIO_LED_R, GPIO_CFG_OUTPUT | GPIO_CFG_OUT_HIGH);
    GPIO_setConfig(FLUIDI_DIO_LED_G, GPIO_CFG_OUTPUT | GPIO_CFG_OUT_HIGH);
    GPIO_setConfig(FLUIDI_DIO_LED_B, GPIO_CFG_OUTPUT | GPIO_CFG_OUT_HIGH);
}

/* ======================= Taster (DIO21) ======================= */
static void btn_in_ctx(char *p) { (void)p; fl_app_on_button(GPIO_read(FLUIDI_DIO_BUTTON) == 0); fl_platform_reschedule(); }
static void btn_pend(void *a, uint32_t b) { (void)a; (void)b; BLEAppUtil_invokeFunction(btn_in_ctx, NULL); }
static void btn_isr(uint_least8_t idx)
{
    (void)idx;
    BaseType_t woken = pdFALSE;
    xTimerPendFunctionCallFromISR(btn_pend, NULL, 0, &woken);   /* ISR -> Task-Kontext -> BLEAppUtil-Kontext */
    portYIELD_FROM_ISR(woken);
}
static bool s_pullup = true;
void fl_port_button_pullup(bool on)
{
    s_pullup = on;
    GPIO_setConfig(FLUIDI_DIO_BUTTON, (on ? GPIO_CFG_IN_PU : GPIO_CFG_IN_NOPULL) | GPIO_CFG_IN_INT_BOTH_EDGES);
    GPIO_setCallback(FLUIDI_DIO_BUTTON, btn_isr);
    GPIO_enableInt(FLUIDI_DIO_BUTTON);
}
bool fl_port_button_pressed(void)
{
    bool was = s_pullup;
    if (!was) GPIO_setConfig(FLUIDI_DIO_BUTTON, GPIO_CFG_IN_PU);
    delay_us(1000);                                               /* Pull-up 1 ms ein (PROTOCOL 10.3) */
    bool p = GPIO_read(FLUIDI_DIO_BUTTON) == 0;
    if (!was) fl_port_button_pullup(false);
    return p;
}

/* ======================= LED ======================= */
void fl_port_led(uint8_t col, uint8_t level)
{
    /* aktiv low. FW-4-Pulse (<= 5 ms an, >= 5 ms aus) erzeugt core/fl_ui.c im Software-Takt; dazwischen Standby.
     * Keine LGPT-PWM: LGPT liegt im MCU-Bereich und laeuft im Standby nicht (TRM SWCU193A S.262 Kap. 6.4.5), PWM
     * hielte den Chip im Idle (0.8 mA, DS S.19). Dimmung led_level < 100 weiterhin offen (FW-O3). */
    (void)level;
    GPIO_write(FLUIDI_DIO_LED_R, (col & 1) ? 0 : 1);
    GPIO_write(FLUIDI_DIO_LED_G, (col & 2) ? 0 : 1);
    GPIO_write(FLUIDI_DIO_LED_B, (col & 4) ? 0 : 1);
}

/* ======================= Batterie ======================= */
static uint16_t s_conn_vmin = 0xFFFF;
/* FW-9 (DS S.19 Tab. 7.7). Nach einer Verbindung liefert der erste Aufruf das Minimum waehrend der Verbindung (FW-5). */
uint16_t fl_port_vbat_mv(void)
{
    uint16_t v = (uint16_t)BatteryMonitor_getVoltage();
    if (s_conn_vmin != 0xFFFF && s_conn_vmin < v) v = s_conn_vmin;
    s_conn_vmin = 0xFFFF;
    return v;
}

void fl_platform_conn_vbat_reset(void) { s_conn_vmin = 0xFFFF; }
void fl_platform_conn_vbat_sample(void)
{
    uint16_t v = (uint16_t)BatteryMonitor_getVoltage();
    if (v && v < s_conn_vmin) s_conn_vmin = v;
}

/* ======================= Messkette (FW-1, FW-2, FW-3) ======================= */
#if FLUIDI_TESTFW == 3
/* TESTFIRMWARE TF-3: wie tmp1075_read, aber SENS_PWR bleibt high und SDA/SCL werden danach hochohmig (nicht low).
 * Abweichung von FW-1 gewollt (Anhang A); Feuchtewerte unter TF-3 nur informativ. stage: Fehlerstelle. */
int fl_port_tf3_tmp_read(int16_t *t_c100, uint8_t *stage)
{
    int rc = -1;
    *stage = 1;
    GPIO_write(FLUIDI_DIO_SENS_PWR, 1);
    GPIO_setConfigAndMux(FLUIDI_DIO_I2C_SDA, GPIO_CFG_INPUT, GPIO_MUX_GPIO);
    GPIO_setConfigAndMux(FLUIDI_DIO_I2C_SCL, GPIO_CFG_INPUT, GPIO_MUX_GPIO);
    I2C_Params p; I2C_Params_init(&p); p.bitRate = I2C_100kHz;
    I2C_Handle h = I2C_open(CONFIG_I2C_TMP, &p);
    if (h) {
        uint8_t wr[2] = {0x01, 0x81}, ptr = 0x00, rd[2];      /* One-Shot, danach Shutdown (SBOS854F S.21-22) */
        I2C_Transaction t = {0};
        t.targetAddress = FLUIDI_TMP1075_I2C_ADDR;
        t.writeBuf = wr; t.writeCount = 2; t.readBuf = NULL; t.readCount = 0;
        *stage = 2;
        if (I2C_transfer(h, &t)) {
            sleep_ms(FLUIDI_TMP_CONV_MS);
            t.writeBuf = &ptr; t.writeCount = 1; t.readBuf = rd; t.readCount = 2;
            *stage = 3;
            if (I2C_transfer(h, &t)) {
                int16_t raw = (int16_t)((rd[0] << 8) | rd[1]) >> 4;
                *t_c100 = (int16_t)((int32_t)raw * 625 / 100);
                rc = 0; *stage = 0;
            }
        }
        I2C_close(h);
    }
    GPIO_setConfig(FLUIDI_DIO_I2C_SDA, GPIO_CFG_NO_DIR);
    GPIO_setConfig(FLUIDI_DIO_I2C_SCL, GPIO_CFG_NO_DIR);
    return rc;
}
static int tmp1075_read(int16_t *t_c100) { uint8_t st; return fl_port_tf3_tmp_read(t_c100, &st); }
#else
static int tmp1075_read(int16_t *t_c100)
{
    /* FW-1: SENS_PWR an -> One-Shot -> >= 15 ms schlafen -> lesen -> TMP in Shutdown (SD bleibt 1) -> SENS_PWR aus,
     * SDA/SCL low. Register: Konfiguration 0x01, nur Einzelbyte-Schreiben (TMP1075N), OS = Bit 15, SD = Bit 8;
     * Temperatur 0x00, T[11:0] in Bit 15:4, 0.0625 degC/LSB (SBOS854F S.21-22 Tab. 7-8). */
    int rc = -1;
    GPIO_write(FLUIDI_DIO_SENS_PWR, 1);
    delay_us(FLUIDI_SENS_PWR_SETTLE_US);
    GPIO_setConfigAndMux(FLUIDI_DIO_I2C_SDA, GPIO_CFG_INPUT, GPIO_MUX_GPIO);   /* Freigabe fuer den I2C-Treiber */
    GPIO_setConfigAndMux(FLUIDI_DIO_I2C_SCL, GPIO_CFG_INPUT, GPIO_MUX_GPIO);
    I2C_Params p; I2C_Params_init(&p); p.bitRate = I2C_100kHz;                 /* PINMAP: 100 kHz empfohlen */
    I2C_Handle h = I2C_open(CONFIG_I2C_TMP, &p);
    if (h) {
        uint8_t wr[2] = {0x01, 0x81}, ptr = 0x00, rd[2];
        I2C_Transaction t = {0};
        t.targetAddress = FLUIDI_TMP1075_I2C_ADDR;
        t.writeBuf = wr; t.writeCount = 2; t.readBuf = NULL; t.readCount = 0;
        if (I2C_transfer(h, &t)) {
            sleep_ms(FLUIDI_TMP_CONV_MS);
            t.writeBuf = &ptr; t.writeCount = 1; t.readBuf = rd; t.readCount = 2;
            if (I2C_transfer(h, &t)) {
                int16_t raw = (int16_t)((rd[0] << 8) | rd[1]) >> 4;
                *t_c100 = (int16_t)((int32_t)raw * 625 / 100);
                rc = 0;
            }
        }
        I2C_close(h);
    }
    GPIO_write(FLUIDI_DIO_SENS_PWR, 0);
    GPIO_setConfig(FLUIDI_DIO_I2C_SDA, GPIO_CFG_OUTPUT | GPIO_CFG_OUT_LOW);
    GPIO_setConfig(FLUIDI_DIO_I2C_SCL, GPIO_CFG_OUTPUT | GPIO_CFG_OUT_LOW);
    return rc;
}
#endif

#define LG(o) HWREG(LGPT3_BASE + (o))

static void lgpt3_start(void)
{
    /* Periodenmessung auf T3C0 (DIO24, Mux 3), 48 MHz, Zaehler startet bei jeder steigenden Flanke neu
     * (TRM 10.3.6.1, Tab. 10-1 CCACT 8). Mittelung vieler Perioden mit Zufallsphase -> Aufloesung << 1 Takt. */
    LG(LGPT_O_CTL) = LGPT_CTL_MODE_DIS;
    LG(LGPT_O_PRECFG) = 0;
    LG(LGPT_O_TGT) = 0xFFFFu;
    LG(LGPT_O_C0CFG) = LGPT_C0CFG_INPUT_IO | LGPT_C0CFG_EDGE_RISE | LGPT_C0CFG_CCACT_PER_PULSE_WIDTH_MEAS;
    LG(LGPT_O_ICLR) = LGPT_ICLR_C0CC;
    LG(LGPT_O_CTL) = LGPT_CTL_MODE_UP_PER;
}
static void lgpt3_stop(void) { LG(LGPT_O_CTL) = LGPT_CTL_MODE_DIS; LG(LGPT_O_C0CFG) = 0; }

/* Perioden fuer dur_us sammeln; Rueckgabe Mittel Q16 (0 = keine Flanken) */
static uint32_t sample_block(uint32_t dur_us)
{
    uint32_t t0 = systim_us(), n = 0;
    uint64_t sum = 0;
    LG(LGPT_O_ICLR) = LGPT_ICLR_C0CC;
    while (systim_us() - t0 < dur_us) {
        if (LG(LGPT_O_RIS) & LGPT_RIS_C0CC) {
            uint32_t v = LG(LGPT_O_C0CC) & 0xFFFFFFu;
            LG(LGPT_O_ICLR) = LGPT_ICLR_C0CC;
            if (n++ == 0) continue;                    /* erste Periode nach Umschalten verwerfen */
            sum += v;
        }
    }
    if (n < 3) return 0;
    return (uint32_t)((sum << 16) / (n - 1));
}

int fl_port_measure(fl_meas_raw_t *raw, uint8_t n_blocks, bool with_t2)
{
    memset(raw, 0, sizeof *raw);
    if (n_blocks > FL_MEAS_BLOCKS_MAX_FW2) n_blocks = FL_MEAS_BLOCKS_MAX_FW2;
    uint8_t per_burst = (uint8_t)((n_blocks + FLUIDI_BURST_MAX - 1) / FLUIDI_BURST_MAX);
    if (per_burst == 0) per_burst = 1;
    uint32_t blk_us = FLUIDI_BURST_CFG_US / per_burst;
    (void)with_t2;                                             /* Rev B: kein Cref2 (PINMAP Rev B Kap. 0) */

    /* FW-1: Temperatur zuerst, I2C danach still */
    raw->temp_ok = tmp1075_read(&raw->temp_c100) == 0;
    /* FW-3: VDD ohne Funk-/LED-Last vor dem ersten Burst */
    raw->vdd_ref_mv = (uint16_t)BatteryMonitor_getVoltage();
    fl_port_led(0, 0);

    Power_setDependency(PowerLPF3_PERIPH_LGPT3);
    GPIO_setConfigAndMux(FLUIDI_DIO_MEAS_CLK, GPIO_CFG_IN_NOPULL, FLUIDI_MUX_MEAS_CLK_T3C0);
    uint8_t k = 0;
    uint16_t vmin = 0xFFFF;
    for (uint8_t b = 0; b < FLUIDI_BURST_MAX && k < n_blocks; b++) {
        /* FW-2: ein Burst <= 0.6 ms: Kette ein, 50 us, f0, f1, Kette aus. Kein Flash-Schreiben/LED im Burst.
         * Funkereignisse koennen hier nicht hart ausgeschlossen werden -> PROTOTYP-PRUEFUNG (Einbruch messen). */
        uint32_t tb = systim_us();
#if FLUIDI_HAS_OSC_FET
        GPIO_write(FLUIDI_DIO_OSC_EN_N, 0);
#else
        GPIO_write(FLUIDI_DIO_SENS_PWR, 1);
#endif
        delay_us(FLUIDI_OSC_SETTLE_US);
        lgpt3_start();
        GPIO_setConfig(FLUIDI_DIO_CREF1, GPIO_CFG_NO_DIR);                    /* f0: Cref1 aus, Puffer aus */
        for (uint8_t i = 0; i < per_burst && k + i < n_blocks; i++) raw->t0_q16[k + i] = sample_block(blk_us);
        GPIO_setConfig(FLUIDI_DIO_CREF1, GPIO_CFG_OUTPUT | GPIO_CFG_OUT_LOW);  /* f1: Cref1 wirkt */
        for (uint8_t i = 0; i < per_burst && k + i < n_blocks; i++) raw->t1_q16[k + i] = sample_block(blk_us);
        uint16_t v = (uint16_t)BatteryMonitor_getVoltage();                   /* Spannung unter Messlast */
        if (v && v < vmin) vmin = v;
        lgpt3_stop();
        GPIO_setConfig(FLUIDI_DIO_CREF1, GPIO_CFG_NO_DIR);
#if FLUIDI_HAS_OSC_FET
        GPIO_write(FLUIDI_DIO_OSC_EN_N, 1);
#else
        GPIO_write(FLUIDI_DIO_SENS_PWR, 0);
#endif
        (void)tb;   /* Burstdauer am Muster mit Oszilloskop an DIO11 pruefen (<= 0.6 ms, ENERGIEMESSUNG.md) */
        for (uint8_t i = 0; i < per_burst && k < n_blocks; i++, k++)
            if (raw->t0_q16[k] == 0 || raw->t1_q16[k] == 0) raw->osc_timeout = true;
        if (b + 1u < FLUIDI_BURST_MAX && k < n_blocks) sleep_ms(FLUIDI_BURST_PAUSE_MS);   /* FW-2: >= 30 ms Pause */
    }
    raw->n = k;
    GPIO_setConfig(FLUIDI_DIO_MEAS_CLK, GPIO_CFG_NO_DIR);
    Power_releaseDependency(PowerLPF3_PERIPH_LGPT3);
    raw->vbat_load_mv = vmin == 0xFFFF ? raw->vdd_ref_mv : vmin;
    return raw->osc_timeout ? -1 : 0;
}

/* ======================= Krypto ======================= */
static RNG_Handle s_rng;
static AESECB_Handle s_aes;
static ECDH_Handle s_ecdh;

int fl_port_rng(uint8_t *buf, size_t len)
{
    if (!s_rng) s_rng = RNG_open(CONFIG_RNG_FLUIDI, NULL);
    if (!s_rng) return -1;
    return RNG_getRandomBits(s_rng, buf, len * 8u) == RNG_STATUS_SUCCESS ? 0 : -1;
}

int fl_aes128_encrypt_block(const uint8_t key[16], const uint8_t in[16], uint8_t out[16])
{
    CryptoKey k;
    AESECB_Operation op;
    uint8_t kb[16];
    if (!s_aes) s_aes = AESECB_open(CONFIG_AESECB_FLUIDI, NULL);
    if (!s_aes) return -1;
    memcpy(kb, key, 16);
    CryptoKeyPlaintext_initKey(&k, kb, 16);
    AESECB_Operation_init(&op);
    op.key = &k; op.input = (uint8_t *)in; op.output = out; op.inputLength = 16;
    int rc = AESECB_oneStepEncrypt(s_aes, &op) == AESECB_STATUS_SUCCESS ? 0 : -1;
    memset(kb, 0, sizeof kb);
    return rc;
}

/* ECDH P-256 in Software (ECDHLPF3SW). Schluesselformat big-endian 0x04||X||Y (PROTOCOL 5.2: X||Y ohne 0x04).
 * Rechenzeit/Energie: PROTOTYP-PRUEFUNG (ANNAHME <= 3 s). */
int fl_port_ecdh_keygen(uint8_t priv[32], uint8_t pub[64])
{
    uint8_t pubm[65];
    CryptoKey kp, kq;
    ECDH_OperationGeneratePublicKey op;
    if (!s_ecdh) s_ecdh = ECDH_open(CONFIG_ECDH_FLUIDI, NULL);
    if (!s_ecdh) return -1;
    for (int tries = 0; tries < 4; tries++) {
        if (fl_port_rng(priv, 32)) return -1;
        CryptoKeyPlaintext_initKey(&kp, priv, 32);
        CryptoKeyPlaintext_initBlankKey(&kq, pubm, sizeof pubm);
        ECDH_OperationGeneratePublicKey_init(&op);
        op.curve = &ECCParams_NISTP256; op.myPrivateKey = &kp; op.myPublicKey = &kq;
        if (ECDH_generatePublicKey(s_ecdh, &op) == ECDH_STATUS_SUCCESS) { memcpy(pub, pubm + 1, 64); return 0; }
    }
    return -1;
}

int fl_port_ecdh_shared(const uint8_t priv[32], const uint8_t peer[64], uint8_t z[32])
{
    uint8_t pk[32], their[65], sec[65];
    CryptoKey kp, kt, ks;
    ECDH_OperationComputeSharedSecret op;
    if (!s_ecdh) return -1;
    memcpy(pk, priv, 32);
    their[0] = 0x04; memcpy(their + 1, peer, 64);
    CryptoKeyPlaintext_initKey(&kp, pk, 32);
    CryptoKeyPlaintext_initKey(&kt, their, sizeof their);
    CryptoKeyPlaintext_initBlankKey(&ks, sec, sizeof sec);
    ECDH_OperationComputeSharedSecret_init(&op);
    op.curve = &ECCParams_NISTP256; op.myPrivateKey = &kp; op.theirPublicKey = &kt; op.sharedSecret = &ks;
    int rc = ECDH_computeSharedSecret(s_ecdh, &op) == ECDH_STATUS_SUCCESS ? 0 : -1;   /* ungueltiger Punkt -> Fehler */
    if (rc == 0) memcpy(z, sec + 1, 32);                                              /* Z = x-Koordinate */
    memset(pk, 0, sizeof pk); memset(sec, 0, sizeof sec);
    return rc;
}

/* ======================= Flash (NVS-Treiber) ======================= */
typedef struct { uint_least8_t idx; NVS_Handle h; } nvs_dev_t;
static nvs_dev_t d_flnv = {CONFIG_NVS_FLNV, NULL}, d_log = {CONFIG_NVS_LOG, NULL}, d_slot1 = {CONFIG_NVS_SLOT1, NULL};

#if FLUIDI_TESTFW
static uint32_t s_tf_ops;                                     /* Testfirmware: Schreib-/Loeschvorgaenge NV + Ring */
uint32_t fl_port_tf_flash_ops(void) { return s_tf_ops; }
static void tf_count(void *c) { if (c == &d_flnv || c == &d_log) s_tf_ops++; }
#define TF_COUNT(c) tf_count(c)
#else
#define TF_COUNT(c) ((void)0)
#endif

static NVS_Handle dev(nvs_dev_t *d)
{
    if (!d->h) { NVS_Params p; NVS_Params_init(&p); d->h = NVS_open(d->idx, &p); }
    return d->h;
}
static int f_read(void *c, uint32_t off, void *buf, size_t len) { NVS_Handle h = dev(c); return h && NVS_read(h, off, buf, len) == NVS_STATUS_SUCCESS ? 0 : -1; }
static int f_write(void *c, uint32_t off, const void *buf, size_t len)
{
    NVS_Handle h = dev(c);
    TF_COUNT(c);
    return h && NVS_write(h, off, (void *)buf, len, NVS_WRITE_POST_VERIFY) == NVS_STATUS_SUCCESS ? 0 : -1;
}
static int f_erase(void *c, uint32_t off) { NVS_Handle h = dev(c); TF_COUNT(c); return h && NVS_erase(h, off & ~(FL_FLASH_SECTOR - 1u), FL_FLASH_SECTOR) == NVS_STATUS_SUCCESS ? 0 : -1; }

static const fl_flash_t fl_nv_flash = {f_read, f_write, f_erase, &d_flnv, FL_NV_SIZE, FL_FLASH_SECTOR};
static const fl_flash_t fl_log_dev = {f_read, f_write, f_erase, &d_log, FL_LOG_SIZE, FL_FLASH_SECTOR};
static const fl_flash_t fl_slot1_dev = {f_read, f_write, f_erase, &d_slot1, FL_SLOT1_SIZE, FL_FLASH_SECTOR};
const fl_flash_t *fl_port_log_flash(void) { return &fl_log_dev; }
const fl_flash_t *fl_port_slot1_flash(void) { return &fl_slot1_dev; }

static fl_nvs_t s_nvs;
static bool s_nvs_ok;
static void nvs_ready(void) { if (!s_nvs_ok) s_nvs_ok = fl_nvs_init(&s_nvs, &fl_nv_flash) == 0; }
int fl_port_nv_read(uint8_t id, void *buf, uint16_t len) { nvs_ready(); return s_nvs_ok ? fl_nvs_read(&s_nvs, id, buf, len) : -1; }
int fl_port_nv_write(uint8_t id, const void *buf, uint16_t len) { nvs_ready(); return s_nvs_ok ? fl_nvs_write(&s_nvs, id, buf, len) : -1; }
int fl_port_nv_delete(uint8_t id) { nvs_ready(); return s_nvs_ok ? fl_nvs_delete(&s_nvs, id) : -1; }

/* ======================= MCUboot ======================= */
int fl_port_ota_request_test(void) { return boot_set_pending(0); }      /* Test-Swap, Rueckfall ohne Bestaetigung */
int fl_port_ota_confirm(void) { return boot_set_confirmed(); }
bool fl_port_image_confirmed(void)
{
    struct boot_swap_state st;
    if (boot_read_swap_state_by_id(FLASH_AREA_IMAGE_PRIMARY(0), &st) != 0) return true;
    return st.image_ok == BOOT_FLAG_SET || st.magic != BOOT_MAGIC_GOOD;   /* Werks-Image (--confirm) */
}
static int mem_read(void *c, uint32_t off, void *buf, size_t len) { (void)c; memcpy(buf, (const void *)(FL_SLOT0_BASE + off), len); return 0; }
static const fl_flash_t fl_slot0_mem = {mem_read, NULL, NULL, NULL, FL_SLOT0_SIZE, FL_FLASH_SECTOR};
void fl_port_fw_version(uint8_t v[4], uint32_t *b, uint32_t *sec_cnt)
{
    fl_img_info_t in;
    if (fl_img_parse(&fl_slot0_mem, 0, &in) == 0) { memcpy(v, in.ver, 4); *b = in.build; *sec_cnt = in.sec_cnt; }
    else { memset(v, 0, 4); *b = 0; *sec_cnt = 0; }
}

/* ======================= System ======================= */
static Watchdog_Handle s_wdt;
void fl_port_wdt_kick(void) { if (s_wdt) Watchdog_clear(s_wdt); }

/* C-1: RSTSTA einmal festhalten (fl_platform_early_init, vor der IO-Freigabe): PMCTL.SLPCTL.SLPN loescht SDDET/IOWUSD
 * (TRM SWCU193A S. 350 Tab. 6-83; SDK PowerCC23X0.h Z. 433-449, Hinweis zu PowerLPF3_releaseLatches) */
static uint32_t s_rststa;
static bool s_rststa_valid;
uint8_t fl_port_reset_reason(void)
{
    if (!s_rststa_valid) { s_rststa = PMCTLGetResetReason(); s_rststa_valid = true; }
    uint32_t r = s_rststa;
    if (r == PMCTL_RESET_WATCHDOG) return FL_RR_WATCHDOG;
    if (r == PMCTL_RESET_SYSTEM || r == PMCTL_RESET_CPU) return FL_RR_SOFTWARE;
    if (r == PMCTL_RESET_LOCKUP) return FL_RR_HARDFAULT;
    if (r == PMCTL_RESET_PIN || r == PMCTL_RESET_SHUTDOWN_IO) return FL_RR_PIN;   /* Wecken per Taster = Nutzer */
    if (r == PMCTL_RESET_VDDS || r == PMCTL_RESET_VDDR) return FL_RR_BROWNOUT;
    return FL_RR_POWER_ON;
}
void fl_port_reboot(void) { PMCTLResetSystem(); }
/* C-1: Nach dem Wecken aus Shutdown bleiben alle IOs verriegelt (TRM SWCU193A S. 261 Kap. 6.4.2), bis die Anwendung
 * nach dem Konfigurieren der Pins PMCTL.SLPCTL.SLPN setzt (TRM S. 343 Tab. 6-76: der Boot-Code setzt es sonst selbst,
 * "unless waking up from a SHUTDOWN"). SDK: PowerLPF3_releaseLatches (PowerCC23X0.h Z. 446-449), Beispiel
 * examples/rtos/LP_EM_CC2340R5/drivers/gpioshutdown/gpioshutdown.c Z. 66-69. Ohne Shutdown ist SLPN schon gesetzt;
 * erneutes Setzen aendert nichts. MCUboot fasst die Latches nicht an (grep SLPCTL/releaseLatches: keine Treffer) und
 * darf es nicht: sonst fielen die Pins vor fl_platform_early_init in den Reset-Zustand (DIO11 offen usw.). */
void fl_port_io_release(void) { (void)fl_port_reset_reason(); PowerLPF3_releaseLatches(); }
void fl_port_shutdown(void)
{
    /* Unterspannung (FW-5) / Reset-Schleife (F-W3): alles aus, Wecken ueber Taster (Shutdown-Wakeup low an DIO21).
     * Ist der Taster JETZT gedrueckt (klemmt), Pull-up aus und kein Wecken -> nur Zellwechsel (F-W3b). */
    pins_sleep_state();
#if FLUIDI_TESTFW == 3
    GPIO_write(FLUIDI_DIO_SENS_PWR, 0);                       /* TF-3: im Shutdown wie Serie (FW-8) */
    GPIO_setConfig(FLUIDI_DIO_I2C_SDA, GPIO_CFG_OUTPUT | GPIO_CFG_OUT_LOW);
    GPIO_setConfig(FLUIDI_DIO_I2C_SCL, GPIO_CFG_OUTPUT | GPIO_CFG_OUT_LOW);
#endif
    GPIO_setConfig(FLUIDI_DIO_BUTTON, GPIO_CFG_IN_PU);
    delay_us(200);
    if (GPIO_read(FLUIDI_DIO_BUTTON) == 0) GPIO_setConfig(FLUIDI_DIO_BUTTON, GPIO_CFG_NO_DIR);
    else GPIO_setConfig(FLUIDI_DIO_BUTTON, GPIO_CFG_IN_PU | GPIO_CFG_SHUTDOWN_WAKE_LOW);
    Power_shutdown(0, 0);
}

/* Retention-Register PMCTL.AONRSTA1 (18 bit, Power-on = 0; TRM 8.4.2, S.459-460). Ueberlebt Reset, Shutdown,
 * VDDR-Brownout (TRM S. 419-420 Tab. 8-1); VDDS-Brownout UNKLAR: TRM S. 265 Kap. 6.8 "only reset on POR" gegen
 * Tab. 8-1 S. 419 "retention: None" -> PROTOTYP-PRUEFUNG mit TF-4 (TESTFIRMWARE.md, Elektronik-Pruefung W-1).
 * K-4: erst setzen, dann loeschen -> zu keinem Zeitpunkt sind Bits geloescht, die in v bleiben (Ausnahme dazwischen
 * verliert den Reset-Schleifen-Zaehler nicht). */
uint32_t fl_port_retained_get(void) { return HWREG(PMCTL_BASE + PMCTL_O_AONRSTA1) & PMCTL_AONRSTA1_FLAG_M; }
void fl_port_retained_set(uint32_t v)
{
    HWREG(PMCTL_BASE + PMCTL_O_AONRSET1) = v & PMCTL_AONRSTA1_FLAG_M;
    HWREG(PMCTL_BASE + PMCTL_O_AONRCLR1) = PMCTL_AONRSTA1_FLAG_M & ~v;
}

/* ======================= Zeitplanung ======================= */
static BLEAppUtil_timerHandle s_timer = BLEAPPUTIL_TIMER_INVALID_HANDLE;
static bool s_started;

static void timer_cb(BLEAppUtil_timerHandle h, BLEAppUtil_timerTermReason_e r, void *p)
{
    (void)h; (void)p;
    if (r == BLEAPPUTIL_TIMER_TIMEOUT) { s_timer = BLEAPPUTIL_TIMER_INVALID_HANDLE; fl_platform_reschedule(); }
}

void fl_platform_reschedule(void)
{
    if (!s_started) return;
    fl_app_on_tx_ready();
    uint32_t d = fl_app_process();
    if (g_fl.txq_n && d > 20) d = 20;
    if (d == 0) d = 1;
    if (s_timer != BLEAPPUTIL_TIMER_INVALID_HANDLE) BLEAppUtil_abortTimer(s_timer);
    s_timer = BLEAppUtil_startTimer(timer_cb, d, false, NULL);
}

void fl_platform_start_app(void)
{
    Watchdog_Params wp;
    Watchdog_Params_init(&wp);
    wp.resetMode = Watchdog_RESET_ON;
    s_wdt = Watchdog_open(CONFIG_WATCHDOG_0, &wp);       /* uebernimmt von MCUboot (60 s) -> 10 min (syscfg) */
    fl_port_button_pullup(true);
    fl_app_init();
    s_started = true;
    fl_platform_reschedule();
}

void fl_platform_early_init(void)
{
    /* FW-6: SWDIO (DIO16, Pull-up) / SWDCK (DIO17, Pull-down) sofort als Ausgang low -> keine Pulls, kein Strom
     * ueber R4/R5 in den abgeschalteten TMP. Serie: SWD zusaetzlich per CCFG sperren (README). */
    (void)fl_port_reset_reason();          /* C-1: RSTSTA festhalten, bevor irgendetwas SLPN setzt */
    GPIO_init();
    pins_sleep_state();                    /* Pins konfigurieren, solange die IOs noch verriegelt sind (C-1) */
    BatteryMonitor_init();
    /* C-1 + W-2: Latches freigeben, Neustartgrund/Retention auswerten, bei >= 3 abnormalen Starts Abschaltung ohne
     * Flash - alles VOR BLEAppUtil_init, damit Fehler in der Stack-Initialisierung mitgezaehlt werden */
    (void)fl_app_early();
}

/* fataler Fehler: Neustart OHNE 'geplant'-Bit -> zaehlt als abnormal, nach 3 Abschaltung (F-W3c) */
void fl_platform_fatal(uint8_t code) { (void)code; PMCTLResetSystem(); }

/* O-5: Ausnahmebehandlung fuer HardFault, NMI und nicht registrierte Interrupts (SysConfig /freertos/exception
 * "Custom" -> Vektortabelle resetVectors in ti_freertos_config.c; IntRegister kopiert sie beim ersten Aufruf in die
 * RAM-Tabelle, SDK driverlib/interrupt.c Z. 101-112). Ersetzt Exception_handlerSpin (SDK ExceptionArmV6M.c Z. 67-72:
 * Interrupts aus, Endlosschleife -> erst der Watchdog nach bis zu 10 min, Grund "watchdog").
 * Minimal: kein Flash, keine Treiber, kein RAM-Zugriff ausser Registern, kein Stack (geprueft bei jedem Build:
 * tools/check_fault_vectors.py, Ziel size). Grund in REG3V3 (PMCTL.AONRSET1/AONRCLR1, TRM SWCU193A 8.4.2 S. 460 und
 * 6.11.13-15 S. 352-354), dann Systemreset ueber PMCTL.RSTCTL.SYSRST (TRM 6.11.10 S. 349; SDK driverlib/pmctl.h
 * PMCTLResetSystem: Interrupts aus, SYSRST, Schleife) -> RSTSTA SYSSRC = 4 (TRM 6.11.11 S. 350, Tab. 8-1 S. 420)
 * -> fl_port_reset_reason = FL_RR_SOFTWARE, fl_app_init macht daraus FL_RR_HARDFAULT (abnormal, F-W3).
 * Fault im Handler selbst / Stapelfehler beim Eintritt: Lockup -> Hardware-Systemreset LOCKUP (TRM 4.2.1 S. 117,
 * Tab. 8-1 S. 420) -> ebenfalls FL_RR_HARDFAULT. */
void fl_fault_handler(void)
{
    HWREG(PMCTL_BASE + PMCTL_O_AONRCLR1) = FL_RET_PLANNED;
    HWREG(PMCTL_BASE + PMCTL_O_AONRSET1) = FL_RET_FAULT;
    PMCTLResetSystem();
    __builtin_unreachable();             /* K-1: PMCTLResetSystem endet in while (1) (pmctl.h Z. 171), SDK ohne noreturn */
}

#if FLUIDI_TESTFW
/* TF-1: Endlosschleife im Anwendungs-Task OHNE Watchdog_clear; BLE-Stack (hoehere Prioritaet) laeuft weiter ->
 * prueft zugleich, dass nichts ausser fl_app_process den Watchdog bedient. Erwartung: Neustart nach <= 10 min
 * (CONFIG_WATCHDOG_0 period = 600000 ms, syscfg), reset_reason 2. */
void fl_port_tf_hang(void)
{
    volatile uint32_t spin = 0;
    fl_port_led(FL_COL_OFF, 0);
    for (;;) spin++;
}
/* TF-2: FL_TF_FATAL_SERIES = Serienpfad fuer fatale Fehler (fl_platform_fatal, wie crit_err des BLE-Stacks);
 * FL_TF_FATAL_HARDFAULT = undefinierter Befehl -> HardFault -> Serien-Ausnahmebehandlung fl_fault_handler (O-5:
 * FL_RET_FAULT, sofortiger Systemreset, Grund "hardfault"). */
void fl_port_tf_fatal(uint8_t kind)
{
    fl_port_led(FL_COL_OFF, 0);
    if (kind == FL_TF_FATAL_HARDFAULT) __builtin_trap();
    fl_platform_fatal(0xF2);
    for (;;) { }
}
#endif
