/*
 * fluidi – Host-Tests der TESTFIRMWARE (core/fl_testfw.c, Testplan Anhang A TF-1..TF-4) auf der simulierten
 * Plattform. Uebersetzt je Variante mit -DFLUIDI_TESTFW=n (tests/Makefile). Schreibt die GET_DIAG-/GET_INFO-
 * Nutzlast und TF-3-Datensaetze als Hex nach build/ (Gegenprobe mit scripts/testfw_eval.py).
 */
#include <stdio.h>
#include <stdlib.h>
#include "fl_crypto.h"
#include "fl_proto.h"
#include "fl_app.h"
#include "fl_ui.h"
#include "fl_util.h"
#include "fl_testfw.h"
#include "port_sim.h"
#include "vectors.h"

static int g_fail, g_pass;
#define CHECK(c) do { if (c) g_pass++; else { g_fail++; printf("  FEHLER %s:%d: %s\n", __FILE__, __LINE__, #c); } } while (0)

static int find_tx(uint8_t vt, int from) { for (int i = from; i < (int)sim.tx_n; i++) if (sim.tx[i][0] == vt) return i; return -1; }

static void advance(uint32_t ms)
{
    uint32_t end = sim.ms + ms;
    while ((int32_t)(end - sim.ms) > 0) {
        uint32_t d = fl_app_process();
        if (d == 0) d = 1;
        if (d > end - sim.ms) d = end - sim.ms;
        sim.ms += d;
    }
    fl_app_process();
}

#if FLUIDI_TESTFW != 3
static void press(uint32_t hold_ms)
{
    sim.button_level = true; fl_app_on_button(true);
    advance(hold_ms);
    sim.button_level = false; fl_app_on_button(false);
    fl_app_process();
}

/* n x kurz (200 ms gedrueckt, 300 ms Pause), danach 3 s warten (Sequenzende + Quittung) */
static void press_seq(int n)
{
    for (int i = 0; i < n; i++) { press(200); advance(300); }
    advance(3000);
}
#endif

static uint8_t k_s[16];
static uint32_t g_ctr_tx, g_ctr_rx;
static uint8_t rid_ctr = 1;

static void gw_send_secure(uint8_t msg, const uint8_t *p, size_t n)
{
    uint8_t f[256];
    int len = fl_secure_seal(k_s, FL_DIR_G2S, g_ctr_tx++, V_ADDR, msg, rid_ctr++, p, n, f);
    fl_app_on_rx(f, (uint16_t)len);
}

static int gw_recv(int *idx, uint8_t *plain)
{
    int i = find_tx(FL_VT(FL_FT_SECURE), *idx);
    if (i < 0) return -1;
    *idx = i + 1;
    return fl_secure_open(k_s, FL_DIR_S2G, g_ctr_rx++, V_ADDR, sim.tx[i], sim.tx_len[i], plain);
}

static void gw_hello(void)
{
    uint8_t h[18] = {FL_VT(FL_FT_HELLO), 2};
    memcpy(h + 2, V_GWID, 8); memcpy(h + 10, V_GN8, 8);
    sim.tx_n = 0;
    fl_app_on_connect();
    fl_app_on_notify_enabled();
    fl_app_on_rx(h, 18);
    int i = find_tx(FL_VT(FL_FT_HELLO_RSP), 0);
    if (i >= 0) fl_session_key(V_KLINK, V_GN8, sim.tx[i] + 2, k_s);
    g_ctr_tx = 0; g_ctr_rx = 0;
}

/* Anfrage in neuer Sitzung; Antwort-Nutzlast (ohne msg/rid) nach out, Rueckgabe Laenge oder -1 */
static int request(uint8_t msg, const uint8_t *p, size_t n, uint8_t *out)
{
    uint8_t plain[256];
    int idx = 0;
    gw_hello();
    if (gw_recv(&idx, plain) < 0) return -1;                    /* SESSION_INFO */
    gw_send_secure(msg, p, n);
    int r = gw_recv(&idx, plain);
    fl_app_on_disconnect();
    if (r < 2 || plain[0] != FL_RSP(msg)) return -1;
    memcpy(out, plain + 2, (size_t)r - 2);
    return r - 2;
}

static void boot_paired(void)
{
    fl_pairing_t pr;
    memset(&pr, 0x3C, sizeof pr);
    pr.paired = 1; memcpy(pr.gateway_id, V_GWID, 8); memcpy(pr.k_link, V_KLINK, 16);
    memcpy(sim.nv[FL_NV_PAIR], &pr, sizeof pr); sim.nv_len[FL_NV_PAIR] = sizeof pr;
    fl_app_init();
}

static void dump_hex(const char *name, const uint8_t *b, int n)
{
    char path[96];
    snprintf(path, sizeof path, "build/tf%d_%s.hex", FLUIDI_TESTFW, name);
    FILE *f = fopen(path, "w");
    if (!f) return;
    for (int i = 0; i < n; i++) fprintf(f, "%02x", b[i]);
    fputc('\n', f);
    fclose(f);
}

/* Offset des TF-Anhangs in GET_DIAG */
static int diag_tail(const uint8_t *d, int n)
{
    int off = 1 + d[0] * 8 + 8;
    return (off + (int)FL_TF_DIAG_TAIL_LEN == n && d[off] == 'T' && d[off + 1] == 'F') ? off : -1;
}

#if FLUIDI_TESTFW == 1 || FLUIDI_TESTFW == 2
static bool diag_has(const uint8_t *d, uint8_t code)
{
    for (int i = 0; i < d[0]; i++) if (d[1 + 8 * i] == code) return true;
    return false;
}
#endif

static void test_common(void)
{
    uint8_t r[256];
    printf("[tf%d] Kennzeichnung: Name, Startsignal, GET_INFO-Anhang, GET_DIAG-Anhang (TF-4), N-2\n", FLUIDI_TESTFW);
    sim_reset_all(); sim.outlier_block = -1;
    boot_paired();
    CHECK(g_fl.led.active == FL_LED_TF_START);
    bool saw_start = false, saw_l11_after = false;
    for (int i = 0; i < 300; i++) {
        if (g_fl.led.active == FL_LED_TF_START) saw_start = true;
        if (saw_start && g_fl.led.active == FL_LED_L11_START_OK) saw_l11_after = true;
        advance(10);
    }
    CHECK(saw_start && saw_l11_after);                            /* Startsignal, danach L11 (Selbsttest ok) */
    advance(2000);
    char nm[12]; memcpy(nm, sim.adv + 5, 11); nm[11] = 0;
    char want[12]; snprintf(want, sizeof want, "fl-tf%d-ABCD", FLUIDI_TESTFW);
    CHECK(sim.adv_on && strcmp(nm, want) == 0);
    /* GET_INFO: 68 Byte + Anhang "TF" n fmt */
    int n = request(FL_MSG_GET_INFO, NULL, 0, r);
    CHECK(n == 68 + (int)FL_TF_INFO_TAIL_LEN && r[68] == 'T' && r[69] == 'F' && r[70] == FLUIDI_TESTFW && r[71] == FL_TF_FMT);
    if (n > 0) dump_hex("info", r, n);
    /* GET_DIAG mit TF-4-Anhang */
    n = request(FL_MSG_GET_DIAG, NULL, 0, r);
    int t = n > 0 ? diag_tail(r, n) : -1;
    CHECK(t > 0);
    if (t > 0) {
        const uint8_t *o = r + t;
        CHECK(o[2] == FLUIDI_TESTFW && o[3] == FL_TF_FMT);
        CHECK(fl_get_u32(o + 4) == g_fl.meas_count && fl_get_u32(o + 12) == g_fl.conn_count);
        CHECK(fl_get_u32(o + 20) == g_fl.charge_uc && o[24] == FL_RR_POWER_ON);
        CHECK(fl_get_u16(o + 30) == 2950 && fl_get_u16(o + 34) == 2950);       /* VDD-Minimum seit Start / gesamt */
        CHECK(fl_get_u16(o + 40) == 0);                                        /* N-2: 0 Flash-Ops vor Lastmessung */
        CHECK(fl_get_u16(o + 38) > 0 && fl_get_u16(o + 36) == g_fl.cnt.boot_id);
        CHECK(o[67] == (FLUIDI_TESTFW == 3 ? 1 : 0));
        dump_hex("diag_boot", r, n);
    }
    /* VDD-Minimum aus einer Verbindung (Lastwert) */
    sim.vbat = 2700; { fl_record_t rec; fl_app_measure(FL_CAUSE_AUTO, &rec); } sim.vbat = 2950;
    n = request(FL_MSG_GET_DIAG, NULL, 0, r);
    t = n > 0 ? diag_tail(r, n) : -1;
    CHECK(t > 0 && fl_get_u16(r + t + 30) == 2700);
}

#if FLUIDI_TESTFW == 1
static void test_tf1(void)
{
    uint8_t r[256];
    puts("[tf1] Watchdog-Test: 5 x kurz -> Endlosschleife; Neustart durch Watchdog, Zaehler bleibt");
    sim_reset_all(); sim.outlier_block = -1;
    boot_paired(); advance(3000);
    press_seq(4); CHECK(sim.tf_hangs == 0);
    press_seq(6); CHECK(sim.tf_hangs == 0);
    uint32_t kicks = sim.wdt_kicks;
    press_seq(5);
    CHECK(sim.tf_hangs == 1);
    CHECK(sim.nv_len[FL_NV_TF] == sizeof(fl_tf_nv_t) && ((fl_tf_nv_t *)sim.nv[FL_NV_TF])->tf1_trig == 1);
    advance(20 * 60000u);                                       /* "Schleife": keine Bedienung mehr, keine Aktion */
    (void)kicks;
    CHECK(sim.tf_hangs == 1);
    uint16_t wdt0 = g_fl.cnt.wdt_resets;
    sim.ms = 1000;                                              /* Neustart: Systemzeit beginnt neu */
    sim.reset_reason = FL_RR_WATCHDOG; fl_app_init(); advance(3000);
    CHECK(g_fl.cnt.wdt_resets == wdt0 + 1 && g_fl.reset_reason == FL_RR_WATCHDOG);
    int n = request(FL_MSG_GET_DIAG, NULL, 0, r);
    int t = n > 0 ? diag_tail(r, n) : -1;
    CHECK(t > 0 && diag_has(r, FL_E_WDT_RESET));
    CHECK(t > 0 && fl_get_u16(r + t - 8) == wdt0 + 1);          /* wdt_resets im Serienteil */
    CHECK(t > 0 && r[t + 24] == FL_RR_WATCHDOG && fl_get_u16(r + t + 44) == 1 && r[t + 25] == 1);
    if (t > 0) dump_hex("diag_wdt", r, n);
    /* zweiter Durchlauf: Zaehler steigt weiter (nichtfluechtig) */
    press_seq(5); CHECK(sim.tf_hangs == 2);
    sim.reset_reason = FL_RR_WATCHDOG; fl_app_init(); advance(3000);
    CHECK(g_fl.cnt.wdt_resets == wdt0 + 2 && fl_tf_nv()->tf1_trig == 2);
}
#endif

#if FLUIDI_TESTFW == 2
/* Reset-Schleife bis zur Abschaltung, dann Wecken per Taster; liefert GET_DIAG-Anhang */
static void tf2_loop(int presses, uint8_t mode, uint8_t rr_loop, const char *name)
{
    uint8_t r[256];
    sim_reset_all(); sim.outlier_block = -1;
    boot_paired(); advance(3000);
    uint32_t fs = sim.tf_fatal_series, fh = sim.tf_fatal_hf;
    press_seq(presses);
    CHECK(sim.tf_fatal_series + sim.tf_fatal_hf == fs + fh + 1);
    CHECK(((sim.retained & FL_TF_RET_MODE_MASK) >> FL_TF_RET_MODE_SHIFT) == mode);
    CHECK(((sim.retained & FL_TF_RET_CYC_MASK) >> FL_TF_RET_CYC_SHIFT) == 1);
    /* Schleife: 2 weitere fatale Neustarts, der 3. abnormale Start schaltet ab (F-W3) */
    for (int c = 1; c <= 2; c++) {
        uint32_t nvw = sim.nv_writes;
        sim.reset_reason = rr_loop; fl_app_init();
        CHECK(sim.tf_fatal_series + sim.tf_fatal_hf == fs + fh + 1 + (uint32_t)c);
        CHECK((sim.retained & FL_RET_ABN_MASK) == (uint32_t)c && sim.shutdowns == 0);
        CHECK(((sim.retained & FL_TF_RET_CYC_MASK) >> FL_TF_RET_CYC_SHIFT) == (uint32_t)c + 1);
        if (mode == FL_TF2_EARLY) CHECK(sim.nv_writes == nvw);   /* N-2: vor der Lastmessung kein Schreiben */
        else CHECK(sim.nv_writes > nvw);
        if (mode == FL_TF2_HARDFAULT) {                         /* O-5: Grund "hardfault", kein Watchdog-Umweg */
            CHECK(g_fl.reset_reason == FL_RR_HARDFAULT && (sim.retained & FL_RET_FAULT));   /* neuer Absturz */
            uint8_t ri[256];
            int ni = request(FL_MSG_GET_INFO, NULL, 0, ri);
            CHECK(ni >= 68 && ri[37] == FL_RR_HARDFAULT);         /* SESSION/GET_INFO Byte 37 = 5 -> Gateway */
        }
    }
    uint32_t nvw = sim.nv_writes, fw = sim.flash_writes;
    sim.reset_reason = rr_loop; fl_app_init();
    CHECK(sim.shutdowns == 1 && (sim.retained & FL_RET_BACKOFF) && sim.nv_writes == nvw && sim.flash_writes == fw);
    CHECK(((sim.retained & FL_TF_RET_SD_MASK) >> FL_TF_RET_SD_SHIFT) == 0);
    uint32_t mx = (sim.retained & FL_TF_RET_MAX_MASK) >> FL_TF_RET_MAX_SHIFT;
    CHECK(mode == FL_TF2_EARLY ? mx == 0 : mx > 0);
    /* Nutzer weckt per Taster: Testende, Ergebnis gespeichert, Bits geloescht, Normalbetrieb */
    sim.reset_reason = FL_RR_PIN; fl_app_init(); advance(3000);
    CHECK((sim.retained & FL_TF_RET_ALL) == 0 && g_fl.cnt.backoffs == 1 && g_fl.mode == FL_MODE_NORMAL);
    const fl_tf_nv_t *tv = fl_tf_nv();
    CHECK(tv->tf2_mode == mode && tv->tf2_cycles == 3 && tv->tf2_sd_ops == 0 && tv->tf2_max_ops == mx && tv->tf2_trig == 1);
    int n = request(FL_MSG_GET_DIAG, NULL, 0, r);
    int t = n > 0 ? diag_tail(r, n) : -1;
    CHECK(t > 0 && r[t + 48] == mode && r[t + 49] == 3 && r[t + 50] == mx && r[t + 51] == 0 && fl_get_u16(r + t + 42) == 1);
    CHECK(t > 0 && diag_has(r, FL_E_HARDFAULT));                /* Serienteil: 0x52/0xBF "Reset-Schleife war aktiv" */
    if (t > 0) dump_hex(name, r, n);
    /* ohne erneute Sequenz kein weiterer fataler Fehler */
    uint32_t tot = sim.tf_fatal_series + sim.tf_fatal_hf;
    sim.reset_reason = FL_RR_SOFTWARE; sim.retained |= FL_RET_PLANNED; fl_app_init(); advance(3000);
    CHECK(sim.tf_fatal_series + sim.tf_fatal_hf == tot);
}

static void test_tf2(void)
{
    puts("[tf2] Reset-Schleife: 5 x spaet, 7 x frueh (N-2), 9 x HardFault; Abschaltung nach 3, NV-Schreibzahl");
    tf2_loop(5, FL_TF2_LATE, FL_RR_SOFTWARE, "diag_tf2_late");
    CHECK(sim.tf_fatal_hf == 0);
    tf2_loop(7, FL_TF2_EARLY, FL_RR_SOFTWARE, "diag_tf2_early");
    /* HardFault: Serie springt in fl_fault_handler (O-5) -> FL_RET_FAULT + Systemreset (PMCTL SYSTEM = Grund 3),
     * fl_app_init meldet hardfault (5); kein Watchdog-Neustart mehr */
    tf2_loop(9, FL_TF2_HARDFAULT, FL_RR_SOFTWARE, "diag_tf2_hf");
    CHECK(sim.tf_fatal_hf == 3 && g_fl.cnt.wdt_resets == 0);
    /* andere Anzahl: keine Aktion */
    sim_reset_all(); sim.outlier_block = -1; boot_paired(); advance(3000);
    press_seq(6); press_seq(3);
    CHECK(sim.tf_fatal_series == 0 && sim.tf_fatal_hf == 0);
}
#endif

#if FLUIDI_TESTFW == 3
static void test_tf3(void)
{
    uint8_t r[256];
    puts("[tf3] SENS_PWR dauernd: TMP1075N alle 60 s, Ergebnis + I2C-Fehlerzaehler im Ringspeicher");
    sim_reset_all(); sim.outlier_block = -1;
    boot_paired();
    uint32_t seq0 = fl_log_last_seq(&g_fl.log);
    advance(60000u + 500u);
    CHECK(sim.tf3_reads == 1 && fl_log_last_seq(&g_fl.log) == seq0 + 1);
    fl_record_t rec;
    CHECK(fl_log_read(&g_fl.log, seq0 + 1, &rec) == 0 && rec.cause == FL_CAUSE_TF3 && rec.temp == 2150 &&
          rec.c_diag == 0 && rec.c_probe == FL_C_INVALID && rec.flags == 0);
    CHECK(sim.adv[23] & FL_ST_DATA_PENDING);
    /* I2C-Fehler: Datensatz ungueltig markiert, Zaehler im c_diag, sofort gesichert */
    sim.tf3_fail_stage = 3;
    advance(60000u);
    CHECK(sim.tf3_reads == 2 && fl_log_read(&g_fl.log, seq0 + 2, &rec) == 0 && rec.temp == FL_TEMP_INVALID &&
          rec.flags == FL_RF_TEMP_INVALID && rec.c_diag == 1);
    CHECK(sim.nv_len[FL_NV_TF] == sizeof(fl_tf_nv_t) && ((fl_tf_nv_t *)sim.nv[FL_NV_TF])->tf3_err == 1);
    sim.tf3_fail_stage = 0; sim.temp = 6512;
    advance(10u * 60000u);
    CHECK(sim.tf3_reads == 12 && fl_tf_nv()->tf3_err == 1 && fl_tf_nv()->tf3_max == 6512 && fl_tf_nv()->tf3_min == 2150);
    /* waehrend einer Verbindung verschoben, danach nachgeholt */
    uint32_t rd = sim.tf3_reads;
    fl_app_on_connect(); fl_app_on_notify_enabled();
    advance(70000u);
    uint32_t during = sim.tf3_reads;
    fl_app_on_disconnect(); advance(2000);
    CHECK(during == rd && sim.tf3_reads == rd + 1);
    /* Normalbetrieb laeuft weiter (automatische Messung nach meas_interval) */
    uint32_t mc = g_fl.meas_count;
    advance(g_fl.set.meas_interval_s * 1000u + 1000u);
    CHECK(g_fl.meas_count > mc);
    /* GET_DIAG-Anhang und Datensaetze ueber READ_RECORDS */
    int n = request(FL_MSG_GET_DIAG, NULL, 0, r);
    int t = n > 0 ? diag_tail(r, n) : -1;
    CHECK(t > 0 && fl_get_u32(r + t + 52) == sim.tf3_reads && fl_get_u32(r + t + 56) == 1 && r[t + 66] == 3 && r[t + 67] == 1);
    CHECK(t > 0 && (int16_t)fl_get_u16(r + t + 64) == 6512);
    if (t > 0) dump_hex("diag_tf3", r, n);
    uint8_t rr[6]; fl_put_u32(rr, seq0 + 1); fl_put_u16(rr + 4, 3);
    n = request(FL_MSG_READ_RECORDS, rr, 6, r);
    CHECK(n == 2 + 3 * FL_REC_LEN && r[0] == 3);
    if (n > 2) dump_hex("records_tf3", r + 2, n - 2);
    /* Stundensicherung der Zaehler */
    uint32_t w = sim.nv_writes;
    advance(61u * 60000u);
    CHECK(sim.nv_writes > w && ((fl_tf_nv_t *)sim.nv[FL_NV_TF])->tf3_reads >= 70);
}
#endif

#if FLUIDI_TESTFW == 4
static void test_tf4(void)
{
    puts("[tf4] nur Diagnose: Tastersequenzen ohne Wirkung");
    sim_reset_all(); sim.outlier_block = -1; boot_paired(); advance(3000);
    press_seq(5); press_seq(7); press_seq(9);
    CHECK(sim.tf_hangs == 0 && sim.tf_fatal_series == 0 && sim.tf_fatal_hf == 0 && sim.tf3_reads == 0);
}
#endif

int main(void)
{
    test_common();
#if FLUIDI_TESTFW == 1
    test_tf1();
#elif FLUIDI_TESTFW == 2
    test_tf2();
#elif FLUIDI_TESTFW == 3
    test_tf3();
#else
    test_tf4();
#endif
    printf("Ergebnis TF-%d: %d Pruefungen bestanden, %d fehlgeschlagen\n", FLUIDI_TESTFW, g_pass, g_fail);
    return g_fail ? 1 : 0;
}
