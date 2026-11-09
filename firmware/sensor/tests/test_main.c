/*
 * fluidi Sensor-Firmware – Host-Unit-Tests (gcc, ohne Hardware). Erwartungswerte fuer Krypto/Protokoll stammen
 * aus Normen (FIPS 180-4/197, RFC 4231, RFC 5869, RFC 3610) und aus der unabhaengigen Python-Referenz
 * (tests/gen_vectors.py -> build/vectors.h, Bibliothek `cryptography`).
 */
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "fl_crypto.h"
#include "fl_proto.h"
#include "fl_settings.h"
#include "fl_meas.h"
#include "fl_ringlog.h"
#include "fl_ui.h"
#include "fl_ota.h"
#include "fl_app.h"
#include "fl_nvstore.h"
#include "fl_util.h"
#include "port_sim.h"
#include "vectors.h"

static int g_fail, g_pass;
#define CHECK(c) do { if (c) g_pass++; else { g_fail++; printf("  FEHLER %s:%d: %s\n", __FILE__, __LINE__, #c); } } while (0)
#define CHECK_MEM(a, b, n) CHECK(memcmp((a), (b), (n)) == 0)

static void hex2bin(const char *h, uint8_t *o, size_t n) { for (size_t i = 0; i < n; i++) { unsigned v; sscanf(h + 2 * i, "%2x", &v); o[i] = (uint8_t)v; } }

/* ---------------- Krypto ---------------- */
static void test_crypto(void)
{
    uint8_t out[64], exp[64], key[64];
    puts("[crypto] SHA-256, HMAC, HKDF, AES, CCM");
    fl_sha256("abc", 3, out);
    hex2bin("ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad", exp, 32); CHECK_MEM(out, exp, 32);
    fl_sha256("", 0, out);
    hex2bin("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", exp, 32); CHECK_MEM(out, exp, 32);
    { /* FIPS 180-4: 448-bit-Nachricht (zwei Bloecke) */
        const char *m = "abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq";
        fl_sha256(m, strlen(m), out);
        hex2bin("248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1", exp, 32); CHECK_MEM(out, exp, 32);
    }
    /* RFC 4231 Testfall 1 und 2 */
    memset(key, 0x0b, 20);
    fl_hmac_sha256(key, 20, "Hi There", 8, out);
    hex2bin("b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7", exp, 32); CHECK_MEM(out, exp, 32);
    fl_hmac_sha256((const uint8_t *)"Jefe", 4, "what do ya want for nothing?", 28, out);
    hex2bin("5bdcc146bf60754e6a042426089575c75a003f089d2739839dec58b964ec3843", exp, 32); CHECK_MEM(out, exp, 32);
    /* RFC 5869 Testfall 1 */
    { uint8_t ikm[22], salt[13], info[10], okm[42];
      memset(ikm, 0x0b, 22); for (int i = 0; i < 13; i++) salt[i] = (uint8_t)i; for (int i = 0; i < 10; i++) info[i] = (uint8_t)(0xf0 + i);
      CHECK(fl_hkdf_sha256(salt, 13, ikm, 22, info, 10, okm, 42) == 0);
      hex2bin("3cb25f25faacd57a90434f64d0362f2a2d2d0a90cf1a5a4c5db02d56ecc4c5bf34007208d5b887185865", exp, 42);
      CHECK_MEM(okm, exp, 42); }
    /* RFC 5869 Testfall 3 (ohne salt/info) */
    { uint8_t ikm[22], okm[42];
      memset(ikm, 0x0b, 22);
      fl_hkdf_sha256(NULL, 0, ikm, 22, NULL, 0, okm, 42);
      hex2bin("8da4e775a563c18f715f802a063c5a31b8a11f5c5ee1879ec3454e5f3c738d2d9d201395faa4b61a96c8", exp, 42);
      CHECK_MEM(okm, exp, 42); }
    /* FIPS-197 Anhang C.1 */
    { uint8_t k[16], p[16];
      for (int i = 0; i < 16; i++) { k[i] = (uint8_t)i; p[i] = (uint8_t)(i * 0x11); }
      fl_aes128_encrypt_block(k, p, out);
      hex2bin("69c4e0d86a7b0430d8cdb78070b4c55a", exp, 16); CHECK_MEM(out, exp, 16); }
    /* RFC 3610 Packet Vector #1 (M = 8, L = 2) */
    { uint8_t k[16], n[13] = {0, 0, 0, 3, 2, 1, 0, 0xa0, 0xa1, 0xa2, 0xa3, 0xa4, 0xa5}, a[8], m[23], c[23], mic[8], d[23];
      for (int i = 0; i < 16; i++) k[i] = (uint8_t)(0xc0 + i);
      for (int i = 0; i < 8; i++) a[i] = (uint8_t)i;
      for (int i = 0; i < 23; i++) m[i] = (uint8_t)(8 + i);
      CHECK(fl_ccm_encrypt(k, n, a, 8, m, 23, c, mic, 8) == 0);
      hex2bin("588C979A61C663D2F066D0C2C0F989806D5F6B61DAC38417E8D12CFDF926E0", exp, 31);
      CHECK_MEM(c, exp, 23); CHECK_MEM(mic, exp + 23, 8);
      CHECK(fl_ccm_decrypt(k, n, a, 8, c, 23, d, mic, 8) == 0); CHECK_MEM(d, m, 23);
      mic[7] ^= 1; CHECK(fl_ccm_decrypt(k, n, a, 8, c, 23, d, mic, 8) != 0);
      mic[7] ^= 1; a[0] ^= 1; CHECK(fl_ccm_decrypt(k, n, a, 8, c, 23, d, mic, 8) != 0); }
    /* Gegenprobe gegen Python cryptography AESCCM (57 Byte, 4 Bloecke + Rest) */
    { uint8_t c[64], mic[8];
      fl_ccm_encrypt(V_CCM_KEY, V_CCM_NONCE, V_CCM_AAD, 5, V_CCM_PT, sizeof V_CCM_PT, c, mic, 8);
      CHECK_MEM(c, V_CCM_CT, sizeof V_CCM_PT); CHECK_MEM(mic, V_CCM_CT + sizeof V_CCM_PT, 8); }
}

/* ---------------- Protokoll ---------------- */
static void test_proto(void)
{
    char name[12];
    uint8_t adv[31], hint[2], tr[32], kl[16], kc[16], sas[5], mac[16], ks[16];
    puts("[proto] Name, Advertising, Kopplung, Sitzung, SECURE-Frames, Datensatz");
    fl_device_name(V_ADDR, name);
    CHECK(strcmp(name, "fluidi-ABCD") == 0);          /* PROTOCOL 2.3 Beispiel 80:6F:B0:12:AB:CD */
    fl_gw_hint(V_GWID, hint); CHECK_MEM(hint, V_GWHINT, 2);
    CHECK(fl_adv_build(adv, V_ADDR, 0x05, 2950, 0x123456, hint) == 29);
    CHECK(sizeof V_ADV == 29); CHECK_MEM(adv, V_ADV, 29);
    { uint8_t c[32]; fl_pair_commit(V_GWID, V_GWPUB, V_GWNONCE16, c); CHECK_MEM(c, V_COMMIT, 32);
      CHECK_MEM(V_PAIRREQ + 72, V_COMMIT, 32); }                                   /* Commitment v2 (F-K1) */
    fl_pair_transcript(V_PAIRREQ, V_PAIRRSP, V_GWNONCE16, tr); CHECK_MEM(tr, V_TRANSCRIPT, 32);
    fl_pair_keys(V_Z, V_GWNONCE16, V_SNONCE16, V_GWID, V_ADDR, kl, kc);
    CHECK_MEM(kl, V_KLINK, 16); CHECK_MEM(kc, V_KCONF, 16);
    fl_pair_sas(tr, sas); CHECK_MEM(sas, V_SAS, 5);
    for (int i = 0; i < 5; i++) CHECK(sas[i] < 3);
    fl_pair_confirm_mac(kc, 'S', tr, mac); CHECK_MEM(mac, V_MAC_S, 16);
    fl_pair_confirm_mac(kc, 'G', tr, mac); CHECK_MEM(mac, V_MAC_G, 16);
    fl_session_key(V_KLINK, V_GN8, V_SN8, ks); CHECK_MEM(ks, V_KS, 16);
    uint8_t pl[30], f[64], plain[64];
    for (int i = 0; i < 30; i++) pl[i] = (uint8_t)i;
    int n = fl_secure_seal(ks, FL_DIR_S2G, 7, V_ADDR, 0x90, 0x42, pl, 30, f);
    CHECK(n == 45); CHECK(n == (int)sizeof V_SECFRAME); CHECK_MEM(f, V_SECFRAME, 45);
    CHECK(fl_secure_open(ks, FL_DIR_S2G, 7, V_ADDR, f, 45, plain) == 32);
    CHECK(plain[0] == 0x90 && plain[1] == 0x42 && memcmp(plain + 2, pl, 30) == 0);
    CHECK(fl_secure_open(ks, FL_DIR_S2G, 8, V_ADDR, f, 45, plain) == -FL_E_BAD_COUNTER);   /* Replay */
    CHECK(fl_secure_open(ks, FL_DIR_G2S, 7, V_ADDR, f, 45, plain) == -FL_E_AUTH_FAIL);     /* falsche Richtung */
    f[10] ^= 1; CHECK(fl_secure_open(ks, FL_DIR_S2G, 7, V_ADDR, f, 45, plain) == -FL_E_AUTH_FAIL);
    f[10] ^= 1; f[2] ^= 1; CHECK(fl_secure_open(ks, FL_DIR_S2G, 7, V_ADDR, f, 45, plain) == -FL_E_BAD_COUNTER);
    CHECK(fl_secure_open(ks, FL_DIR_S2G, 7, V_ADDR, f, 14, plain) == -FL_E_BAD_LENGTH);
    /* Datensatz */
    fl_record_t r = {123456, 7, 99999, 4321, 0xFFFF, -512, 2875, 1, 0x05}, q;
    uint8_t e[20];
    fl_record_encode(&r, e); fl_record_decode(e, &q);
    CHECK(memcmp(&r, &q, sizeof r) == 0);
    CHECK(e[0] == 0x40 && e[1] == 0xE2 && e[2] == 0x01 && e[14] == 0x00 && e[15] == 0xFE);
}

/* ---------------- Einstellungen ---------------- */
static void test_settings(void)
{
    fl_settings_t s, t;
    uint8_t buf[160], bad;
    puts("[settings] Werkswerte, TLV, Atomaritaet");
    fl_settings_defaults(&s);
    CHECK(s.meas_interval_s == 14400 && s.adv_interval_ms == 27500 && s.ota_min_mv == 2700 && s.avg_count == 16);
    CHECK(fl_settings_valid(&s));
    size_t n = fl_settings_encode(&s, buf, sizeof buf);
    CHECK(n > 2 && n < 229);
    fl_settings_defaults(&t); t.meas_interval_s = 999;
    CHECK(fl_settings_apply_tlv(&t, 5, buf + 2, n - 2, &bad) == 0 && t.meas_interval_s == 14400 && t.settings_ver == 5);
    uint8_t tlv1[] = {0x01, 4, 0x10, 0x0E, 0, 0, 0x08, 1, 50};               /* 3600 s, 50 % */
    CHECK(fl_settings_apply_tlv(&t, 6, tlv1, sizeof tlv1, &bad) == 0 && t.meas_interval_s == 3600 && t.led_level == 50);
    uint8_t tlv2[] = {0x08, 1, 80, 0x01, 4, 0x10, 0, 0, 0};                  /* 16 s < 900 -> ungueltig */
    fl_settings_t before = t;
    CHECK(fl_settings_apply_tlv(&t, 7, tlv2, sizeof tlv2, &bad) == FL_E_BAD_PARAM && bad == 0x01);
    CHECK(memcmp(&t, &before, sizeof t) == 0);                               /* nichts uebernommen */
    uint8_t tlv3[] = {0x7E, 1, 0};
    CHECK(fl_settings_apply_tlv(&t, 7, tlv3, sizeof tlv3, &bad) != 0 && bad == 0x7E);
    uint8_t tlv4[] = {0x04, 1, (uint8_t)-25};
    CHECK(fl_settings_apply_tlv(&t, 7, tlv4, sizeof tlv4, &bad) != 0);
    uint8_t tlv5[] = {0x02, 4, 0xE0, 0x93, 0x04, 0};                         /* adv 300000 > offline 147500 */
    CHECK(fl_settings_apply_tlv(&t, 7, tlv5, sizeof tlv5, &bad) != 0);
    uint8_t tlv6[] = {0x15, 2, 0x10, 0x02};                                  /* c_kv = 528 */
    CHECK(fl_settings_apply_tlv(&t, 8, tlv6, sizeof tlv6, &bad) == 0 && t.cal.c_kv == 528);
}

/* ---------------- Messung ---------------- */
static void test_meas(void)
{
    puts("[meas] robuste Mittelung, Ratiometrie, VDD-Korrektur, Index");
    uint32_t x[16];
    bool o, nz;
    for (int i = 0; i < 16; i++) x[i] = 1000000u + (uint32_t)(i % 3) * 100u;
    uint32_t m = fl_meas_robust_mean(x, 16, &o, &nz);
    CHECK(!o && !nz && m > 1000000u && m < 1000200u);
    x[5] = 1300000u;                                                         /* Ausreisser */
    m = fl_meas_robust_mean(x, 16, &o, &nz);
    CHECK(o && m < 1000200u);
    for (int i = 0; i < 16; i++) x[i] = 1000000u + (uint32_t)(i * 1000u);    /* starke Streuung */
    fl_meas_robust_mean(x, 16, &o, &nz); CHECK(nz);
    /* Pinperiode -> Oszillatorperiode: 10 Takte = 208333 ps, /8 = 26042 ps */
    CHECK(fl_meas_period_ps(10u << 16, 8) == 26042u);
    /* Ratiometrie: ideale Perioden aus Modell T = k*(C+Cpar+[Cref]) */
    fl_settings_t s; fl_settings_defaults(&s);
    double k = 950.0, C = 25.00;
    uint32_t t0 = (uint32_t)lround(k * (C + 15.21)), t1 = (uint32_t)lround(k * (C + 15.21 + 17.29));
    int32_t c = fl_meas_cap(&s.cal, t0, t1, 0);
    CHECK(abs(c - 2500) <= 2);
    CHECK(fl_meas_cap(&s.cal, t1, t0, 0) < 0);
    /* FW-3: bei 2.4 V wird C um 3.2 pF zu tief gemessen -> Korrektur + 3.2 pF */
    CHECK(abs(fl_meas_offset_corr(&s.cal, 2180, 2400, 0, false) - 2500) <= 1);
    CHECK(fl_meas_offset_corr(&s.cal, 2500, 3000, 2500, true) == 2500);
    /* Gesamtablauf mit simuliertem Oszillator bei 3.0 V und 2.4 V */
    sim_reset_all(); sim.outlier_block = -1;
    fl_meas_raw_t raw; fl_meas_result_t r;
    sim.c_probe_pf = 30.0; sim.vbat = 3000;
    fl_port_measure(&raw, 16, false); fl_meas_evaluate(&raw, &s, 8, &r);
    CHECK(r.error == 0 && abs((int)r.c_probe - 3000) <= 3);
    sim.vbat = 2400;
    fl_port_measure(&raw, 16, false); fl_meas_evaluate(&raw, &s, 8, &r);
    CHECK(abs((int)r.c_probe - 3000) <= 3);
    sim.vbat = 3000; sim.outlier_block = 3;
    fl_port_measure(&raw, 16, false); fl_meas_evaluate(&raw, &s, 8, &r);
    CHECK((r.flags & FL_RF_OUTLIER) && abs((int)r.c_probe - 3000) <= 3);
    sim.outlier_block = -1; sim.osc_dead = true;
    fl_port_measure(&raw, 16, false); fl_meas_evaluate(&raw, &s, 8, &r);
    CHECK(r.c_probe == FL_C_INVALID && (r.flags & FL_RF_CHAIN_FAULT) && r.error == FL_E_MEAS_OSC_FAIL);
    sim.osc_dead = false; sim.temp_ok = false;
    fl_port_measure(&raw, 16, false); fl_meas_evaluate(&raw, &s, 8, &r);
    CHECK((r.flags & FL_RF_TEMP_INVALID) && r.temp == FL_TEMP_INVALID && r.c_probe != FL_C_INVALID);
    s.air_raw = 3500; sim.temp_ok = true;
    fl_port_measure(&raw, 16, false); fl_meas_evaluate(&raw, &s, 8, &r);
    CHECK(r.flags & FL_RF_AIR);
    /* Index und Giess-Schwelle */
    CHECK(fl_moisture_permille(3000, 2270, 4410) == 341);
    CHECK(fl_moisture_permille(6000, 2270, 4410) > 1000);                   /* > 100 %: Duenger-Hinweis */
    CHECK(fl_moisture_permille(FL_C_INVALID, 2270, 4410) == INT32_MIN);
    CHECK(fl_water_needed(2800, 3000) && !fl_water_needed(3200, 3000) && !fl_water_needed(2800, 0));
}

/* ---------------- Ringspeicher ---------------- */
static void test_ringlog(void)
{
    puts("[ringlog] Anhaengen, Lesen, Quittung, Ueberlauf, Stromausfall, Werkseinstellung");
    sim_reset_all();
    fl_log_meta_t meta = {0xFFFFFFFFu, 0, 0, 0};
    fl_log_t l;
    fl_record_t r, q;
    uint32_t ow;
    CHECK(fl_log_init(&l, fl_port_log_flash(), &meta) == 0);
    CHECK(fl_log_last_seq(&l) == 0xFFFFFFFFu && !fl_log_pending(&l));
    CHECK(fl_log_capacity(&l) == 840);
    for (uint32_t i = 0; i < 100; i++) {
        memset(&r, 0, sizeof r); r.c_probe = (uint16_t)(1000 + i);
        CHECK(fl_log_append(&l, &r, &ow) == 0 && r.seq == i && ow == 0);
    }
    CHECK(fl_log_last_seq(&l) == 99 && fl_log_pending(&l) && fl_log_oldest_unacked(&l) == 0);
    CHECK(fl_log_read(&l, 57, &q) == 0 && q.c_probe == 1057);
    fl_log_ack(&l, 49);
    CHECK(fl_log_oldest_unacked(&l) == 50);
    fl_log_ack(&l, 10);                                                       /* rueckwaerts ignoriert */
    CHECK(fl_log_oldest_unacked(&l) == 50);
    fl_log_ack(&l, 99); CHECK(!fl_log_pending(&l));
    /* Neustart: Zustand aus Flash rekonstruieren */
    fl_log_t l2; CHECK(fl_log_init(&l2, fl_port_log_flash(), &meta) == 0);
    CHECK(fl_log_last_seq(&l2) == 99 && fl_log_read(&l2, 3, &q) == 0 && q.c_probe == 1003);
    /* Ueberlauf ohne Quittung: verlorene Datensaetze werden gezaehlt */
    uint32_t lost = 0;
    for (uint32_t i = 0; i < 1200; i++) { memset(&r, 0, sizeof r); fl_log_append(&l2, &r, &ow); lost += ow; }
    CHECK(fl_log_last_seq(&l2) == 1299);
    CHECK(lost > 0 && meta.lost_records == lost);
    CHECK(fl_log_read(&l2, 5, &q) != 0);                                      /* alt -> ueberschrieben */
    CHECK(fl_log_read(&l2, 1299 - 839, &q) == 0);                             /* garantierte Kapazitaet */
    CHECK(fl_log_oldest_unacked(&l2) > 100);
    /* Stromausfall mitten im Schreiben: Eintrag ungueltig, seq bleibt fortlaufend gueltig */
    sim_log_fail_next_write(0);
    memset(&r, 0, sizeof r);
    CHECK(fl_log_append(&l2, &r, &ow) != 0);
    fl_log_t l3; fl_log_init(&l3, fl_port_log_flash(), &meta);
    CHECK(fl_log_last_seq(&l3) == 1299);
    memset(&r, 0, sizeof r); r.c_probe = 4242;
    CHECK(fl_log_append(&l3, &r, &ow) == 0 && r.seq == 1300);
    CHECK(fl_log_read(&l3, 1300, &q) == 0 && q.c_probe == 4242);
    /* Werkseinstellung: Inhalt unsichtbar, seq laeuft weiter (PROTOCOL 6.2 Regel 6) */
    fl_log_factory_clear(&l3);
    CHECK(fl_log_last_seq(&l3) == 0xFFFFFFFFu && !fl_log_pending(&l3));
    memset(&r, 0, sizeof r); fl_log_append(&l3, &r, &ow); CHECK(r.seq == 1301);
    CHECK(fl_log_next(&l3, 0, &q) == 0 && q.seq == 1301);
    /* Verschleiss: <= 11 Schreibvorgaenge je 256-B-Zeile (DS Tab. 7.11: max. 83) */
    CHECK(256u / FL_LOG_ENTRY + 1u <= 83u);
}


/* ---------------- NV-Speicher ---------------- */
static uint8_t nvmem[0x1000];
static int nv_fail_after = -1;
static int nr(void *c, uint32_t o, void *b, size_t n) { (void)c; memcpy(b, nvmem + o, n); return 0; }
static int nw(void *c, uint32_t o, const void *b, size_t n)
{
    (void)c;
    if (nv_fail_after == 0) { nv_fail_after = -1; return -1; }   /* Stromausfall: Schreiben bricht ab */
    if (nv_fail_after > 0) nv_fail_after--;
    for (size_t i = 0; i < n; i++) nvmem[o + i] &= ((const uint8_t *)b)[i];
    return 0;
}
static int ne(void *c, uint32_t o) { (void)c; memset(nvmem + (o & ~0x7FFu), 0xFF, 0x800); return 0; }
static const fl_flash_t nvflash = {nr, nw, ne, NULL, sizeof nvmem, 0x800};

static void test_nvstore(void)
{
    puts("[nvstore] Schreiben, Lesen, Loeschen, Verdichten, Stromausfall");
    fl_nvs_t s;
    uint8_t a[40], b[40];
    memset(nvmem, 0xFF, sizeof nvmem);
    CHECK(fl_nvs_init(&s, &nvflash) == 0);
    CHECK(fl_nvs_read(&s, 1, a, 40) != 0);
    for (int i = 0; i < 40; i++) a[i] = (uint8_t)i;
    CHECK(fl_nvs_write(&s, 1, a, 40) == 0 && fl_nvs_read(&s, 1, b, 40) == 0 && memcmp(a, b, 40) == 0);
    CHECK(fl_nvs_read(&s, 1, b, 39) != 0);                                    /* Laenge muss passen */
    uint32_t gen0 = s.gen;
    for (int k = 0; k < 200; k++) { a[0] = (uint8_t)k; CHECK(fl_nvs_write(&s, 2, a, 40) == 0); }
    CHECK(s.gen > gen0);                                                      /* verdichtet */
    CHECK(fl_nvs_read(&s, 2, b, 40) == 0 && b[0] == 199 && fl_nvs_read(&s, 1, b, 40) == 0 && b[0] == 0);
    fl_nvs_t s2; fl_nvs_init(&s2, &nvflash);
    CHECK(fl_nvs_read(&s2, 2, b, 40) == 0 && b[0] == 199);
    CHECK(fl_nvs_delete(&s2, 1) == 0 && fl_nvs_read(&s2, 1, b, 40) != 0);
    fl_nvs_init(&s2, &nvflash); CHECK(fl_nvs_read(&s2, 1, b, 40) != 0);
    /* Stromausfall waehrend eines Schreibvorgangs: alter Wert bleibt */
    a[0] = 0x55; nv_fail_after = 0;
    CHECK(fl_nvs_write(&s2, 2, a, 40) != 0);
    fl_nvs_init(&s2, &nvflash); CHECK(fl_nvs_read(&s2, 2, b, 40) == 0 && b[0] == 199);
    /* Stromausfall waehrend der Verdichtung: alter Sektor bleibt gueltig */
    for (int k = 0; k < 300; k++) {
        fl_nvs_init(&s2, &nvflash);
        a[0] = (uint8_t)(k + 1); nv_fail_after = (k % 7 == 3) ? 2 : -1;
        int rc = fl_nvs_write(&s2, 2, a, 40);
        nv_fail_after = -1;
        fl_nvs_init(&s2, &nvflash);
        CHECK(fl_nvs_read(&s2, 2, b, 40) == 0);
        if (rc == 0) CHECK(b[0] == (uint8_t)(k + 1));
        CHECK(fl_nvs_read(&s2, 1, b, 40) != 0);
    }
}

/* ---------------- LED / Taster ---------------- */
/* FW-4: jedes Muster nur in Pulsen <= 5 ms mit >= 5 ms Pause; kurze Schritte (<= 50 ms) gleiche Lichtmenge,
 * lange Schritte gleiche Dauer bei 50 % Tastgrad; Musterdauer der kurzen Muster hoechstens um die Verlaengerung laenger */
static void led_run(fl_led_pattern_t p, uint32_t max_ms, uint32_t *lit, uint32_t *max_on, uint32_t *min_off, uint32_t *dur)
{
    fl_led_t l; fl_led_init(&l);
    uint32_t t0 = 5000, run = 0, dark = 0; bool seen = false;
    *lit = 0; *max_on = 0; *min_off = 0xFFFFFFFFu; *dur = 0;
    fl_led_play(&l, p, t0, 2900, 0);
    for (uint32_t ms = 0; ms < max_ms; ms++) {
        fl_led_tick(&l, t0 + ms);
        if (l.out) {
            if (seen && dark && dark < *min_off) *min_off = dark;
            seen = true; dark = 0; run++; (*lit)++; if (run > *max_on) *max_on = run;
        } else { run = 0; if (seen) dark++; }
        if (!fl_led_busy(&l)) { *dur = ms; break; }
    }
}

static void test_led_fw4(void)
{
    puts("[ui] FW-4: LED-Pulse <= 5 ms, Pause >= 5 ms, Lichtmenge/Dauer");
    static const struct { fl_led_pattern_t p; uint32_t lit, dur_max; } T[] = {
        /* Lichtmenge [ms] wie PROTOCOL 10.2 (L12 100 ms: langer Schritt, 50 %); Dauer <= Original + Verlaengerung */
        {FL_LED_L1_SENT, 60, 30 + 150 + 55},  {FL_LED_L2_BUFFERED, 30, 55}, {FL_LED_L3_HEARTBEAT, 20, 35},
        {FL_LED_L8_WATER, 5, 5},              {FL_LED_L9_BATT_LOW, 20, 10 + 150 + 15},
        {FL_LED_L10_ERROR, 30, 10 + 150 + 10 + 150 + 15}, {FL_LED_L12_3S, 50, 100},
        {FL_LED_L11_UNPAIRED, 100, 50 + 150 + 95},        {FL_LED_L17_OTA_OK, 150, 50 + 100 + 50 + 100 + 95},
    };
    for (unsigned i = 0; i < sizeof T / sizeof T[0]; i++) {
        uint32_t lit, mon, moff, dur;
        led_run(T[i].p, 10000, &lit, &mon, &moff, &dur);
        CHECK(mon <= FL_LED_PULSE_MS);
        CHECK(moff >= FL_LED_PAUSE_MS || moff == 0xFFFFFFFFu);
        CHECK(lit == T[i].lit);
        CHECK(dur > 0 && dur <= T[i].dur_max);
    }
    /* lange Schritte: Dauer gleich, 50 % Tastgrad (L6 Gruen 1 s, L14 Rot 1 s, L7 Rot 3 x 100 ms) */
    uint32_t lit, mon, moff, dur;
    led_run(FL_LED_L6_CONNECTED, 5000, &lit, &mon, &moff, &dur);
    CHECK(mon <= 5 && moff >= 5 && lit == 500 && dur == 1000);
    led_run(FL_LED_L7_PAIR_FAIL, 5000, &lit, &mon, &moff, &dur);
    CHECK(mon <= 5 && moff >= 5 && lit == 150 && dur == 500);
    /* Statistik led_ms zaehlt die tatsaechliche Leuchtzeit */
    fl_led_t l; fl_led_init(&l); fl_led_play(&l, FL_LED_L1_SENT, 0, 2900, 0);
    for (uint32_t ms = 0; ms < 400; ms++) fl_led_tick(&l, ms);
    CHECK(l.on_ms_total == 60);
}

static void test_ui(void)
{
    fl_led_t l;
    puts("[ui] LED-Muster, Farbregeln, periodische Anzeigen, Taster");
    fl_led_init(&l);
    uint32_t t = 1000;
    CHECK(fl_led_play(&l, FL_LED_L1_SENT, t, 2900, 0));
    uint32_t on = 0;
    for (uint32_t ms = 0; ms < 400; ms++) { fl_led_tick(&l, t + ms); if (l.out) { on++; CHECK(l.out == FL_COL_GREEN); } }
    CHECK(on == 60 && !fl_led_busy(&l));                                     /* 2 x 30 ms Lichtmenge (FW-4 gepulst) */
    fl_led_play(&l, FL_LED_L8_WATER, t, 2900, 0); fl_led_tick(&l, t); CHECK(l.out == FL_COL_BLUE);
    fl_led_play(&l, FL_LED_L8_WATER, t, 2600, 0); fl_led_tick(&l, t); CHECK(l.out == FL_COL_YELLOW);   /* schwache Zelle */
    fl_led_tick(&l, t + 5); CHECK(l.out == FL_COL_OFF);                       /* FW-4: Puls <= 5 ms */
    CHECK(!fl_led_play(&l, FL_LED_L3_HEARTBEAT, t, 2350, 0));                /* Unterspannung: keine LED */
    CHECK(fl_led_play(&l, FL_LED_UV_BTN, t, 2350, 0));
    fl_led_play(&l, FL_LED_L4_PAIRING, t, 2900, 0);
    on = 0; { uint32_t dark = 1000; for (uint32_t ms = 0; ms < 130000; ms++) { fl_led_tick(&l, t + ms);
        if (l.out) { if (dark >= 20) on++; dark = 0; } else dark++; } }       /* Blinkgruppe = Licht nach >= 20 ms dunkel */
    CHECK(!fl_led_busy(&l) && on >= 119 && on <= 121);                       /* 1 Hz waehrend 120 s */
    uint8_t d[5] = {0, 1, 2, 2, 0};
    fl_led_play_sas(&l, d, t, 60000);
    fl_led_tick(&l, t); CHECK(l.out == FL_COL_RED);
    fl_led_tick(&l, t + 600); CHECK(l.out == FL_COL_GREEN);
    fl_led_tick(&l, t + 1200); CHECK(l.out == FL_COL_YELLOW);
    /* periodisch: Vorrang Fehler > Batterie > Giessen, Fenster */
    fl_periodic_in_t in = {true, true, true, true, true, 600, 420, 1140, 10};
    CHECK(fl_led_periodic(&in) == FL_LED_L10_ERROR);
    in.error = false; CHECK(fl_led_periodic(&in) == FL_LED_L9_BATT_LOW);
    in.minute_counter = 11; CHECK(fl_led_periodic(&in) == FL_LED_L8_WATER);
    in.minute_of_day = 1200; CHECK(fl_led_periodic(&in) == FL_LED_NONE);    /* ausserhalb 07-19 Uhr */
    in.time_valid = false; in.minute_counter = 11; CHECK(fl_led_periodic(&in) == FL_LED_NONE);   /* ohne Zeit alle 2 min */
    in.minute_counter = 12; CHECK(fl_led_periodic(&in) == FL_LED_L8_WATER);
    in.water_led_enabled = false; CHECK(fl_led_periodic(&in) == FL_LED_NONE);
    /* Taster */
    fl_btn_t b; fl_btn_init(&b);
    fl_btn_edge(&b, true, 0); CHECK(fl_btn_edge(&b, false, 30) == FL_BTN_EV_NONE);         /* Prellen */
    fl_btn_edge(&b, true, 100); CHECK(fl_btn_edge(&b, false, 400) == FL_BTN_EV_SHORT);
    fl_btn_edge(&b, true, 1000); CHECK(fl_btn_edge(&b, false, 3000) == FL_BTN_EV_NONE);    /* 2 s Trennbereich */
    fl_btn_edge(&b, true, 5000);
    CHECK(fl_btn_tick(&b, 8000) == FL_BTN_EV_REACHED_3S);
    CHECK(fl_btn_edge(&b, false, 9000) == FL_BTN_EV_LONG);                                  /* 4 s */
    fl_btn_edge(&b, true, 10000); CHECK(fl_btn_edge(&b, false, 18500) == FL_BTN_EV_NONE);   /* 8.5 s */
    fl_btn_edge(&b, true, 20000);
    fl_btn_tick(&b, 23000); CHECK(fl_btn_tick(&b, 30000) == FL_BTN_EV_REACHED_10S);
    CHECK(fl_btn_edge(&b, false, 31000) == FL_BTN_EV_VLONG_ARMED);
    fl_btn_edge(&b, true, 33000); CHECK(fl_btn_edge(&b, false, 33200) == FL_BTN_EV_FACTORY_RESET);
    fl_btn_edge(&b, true, 40000); fl_btn_tick(&b, 51000); fl_btn_edge(&b, false, 52000);   /* scharf */
    CHECK(fl_btn_tick(&b, 57500) == FL_BTN_EV_ARM_EXPIRED);                                 /* 5 s ohne Bestaetigung */
    fl_btn_edge(&b, true, 60000); fl_btn_tick(&b, 63000); fl_btn_tick(&b, 70000);
    CHECK(fl_btn_tick(&b, 90001) == FL_BTN_EV_STUCK);
    CHECK(fl_btn_edge(&b, false, 95000) == FL_BTN_EV_UNSTUCK);
}

/* ---------------- OTA ---------------- */
static void test_ota(void)
{
    puts("[ota] Beginn, Daten, Go-back-N, SHA, Rollback, Fortsetzung");
    sim_reset_all();
    static uint8_t img[5000];
    for (unsigned i = 0; i < sizeof img; i++) img[i] = (uint8_t)(i * 13 + 1);
    uint8_t begin[48], rsp[7], prog[5], d[4 + 200], end[4];
    fl_put_u32(begin, sizeof img);
    begin[4] = 0; begin[5] = 2; fl_put_u16(begin + 6, 0); fl_put_u32(begin + 8, 5); fl_put_u32(begin + 12, 0);
    fl_sha256(img, sizeof img, begin + 16);
    uint8_t run[4] = {0, 1, 0, 0};
    fl_ota_t o; memset(&o, 0, sizeof o);
    CHECK(fl_ota_begin(&o, fl_port_slot1_flash(), begin, 48, run, 1, false, 0, 200, rsp) == FL_E_OTA_BATT_LOW);
    uint8_t old[4] = {0, 0, 9, 0}; uint8_t b2[48]; memcpy(b2, begin, 48); memcpy(b2 + 4, old, 4);
    CHECK(fl_ota_begin(&o, fl_port_slot1_flash(), b2, 48, run, 1, true, 0, 200, rsp) == FL_E_OTA_ROLLBACK);
    memcpy(b2, begin, 48); fl_put_u32(b2, 0x40000);
    CHECK(fl_ota_begin(&o, fl_port_slot1_flash(), b2, 48, run, 1, true, 0, 200, rsp) == FL_E_OTA_TOO_LARGE);
    CHECK(fl_ota_begin(&o, fl_port_slot1_flash(), begin, 48, run, 1, true, 0, 200, rsp) == 0);
    CHECK(rsp[0] == 0 && fl_get_u32(rsp + 1) == 0 && rsp[5] == FL_OTA_WINDOW && rsp[6] == 200);
    uint32_t off = 0; int progs = 0, frames = 0;
    while (off < 2000) {                                                     /* erste 2000 Byte, dann Abbruch */
        size_t n = 200;
        fl_put_u32(d, off); memcpy(d + 4, img + off, n);
        if (fl_ota_data(&o, d, 4 + n, prog)) progs++;
        off += (uint32_t)n; frames++;
    }
    CHECK(o.next_off == 2000 && progs == 0 && frames == 10);
    /* falscher Offset -> verworfen, Fortschritt nennt next_offset */
    fl_put_u32(d, 2400); memcpy(d + 4, img + 2400, 200);
    for (int i = 0; i < 6; i++) fl_ota_data(&o, d, 204, prog);
    CHECK(fl_get_u32(prog) == 2000 && o.next_off == 2000);
    /* Fortsetzung (gleiches sha256) nach Trennung */
    CHECK(fl_ota_begin(&o, fl_port_slot1_flash(), begin, 48, run, 1, true, 1000, 200, rsp) == 0 && fl_get_u32(rsp + 1) == 2000);
    off = 2000;
    while (off < sizeof img) {
        size_t n = sizeof img - off < 200 ? sizeof img - off : 200;
        fl_put_u32(d, off); memcpy(d + 4, img + off, n);
        fl_ota_data(&o, d, 4 + n, prog);
        off += (uint32_t)n;
    }
    CHECK(fl_get_u32(prog) == sizeof img && prog[4] == 0);
    fl_put_u32(end, sizeof img);
    CHECK(fl_ota_end(&o, end, 4) == 0);
    CHECK(memcmp(sim_slot1(), img, sizeof img) == 0);
    /* falscher Hash */
    begin[16] ^= 1; memset(&o, 0, sizeof o);
    fl_ota_begin(&o, fl_port_slot1_flash(), begin, 48, run, 1, true, 0, 200, rsp);
    for (off = 0; off < sizeof img; off += 200) { size_t n = sizeof img - off < 200 ? sizeof img - off : 200;
        fl_put_u32(d, off); memcpy(d + 4, img + off, n); fl_ota_data(&o, d, 4 + n, prog); }
    CHECK(fl_ota_end(&o, end, 4) == FL_E_OTA_HASH);
    CHECK(sim_slot1()[0] == 0xFF);                                            /* Kopf ungueltig gemacht */
    CHECK(fl_ota_data(&o, d, 204, prog) == 1 && prog[4] == FL_E_OTA_NOT_STARTED);
}

/* ---------------- Gesamtablauf mit simulierter Plattform ---------------- */
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

static void press(uint32_t hold_ms)
{
    sim.button_level = true; fl_app_on_button(true);
    advance(hold_ms);
    sim.button_level = false; fl_app_on_button(false);
    fl_app_process();
}

static uint8_t k_s[16];
static uint32_t g_ctr_tx, g_ctr_rx;
static uint8_t rid_ctr = 1;

static void gw_send_secure(uint8_t msg, const uint8_t *p, size_t n)
{
    uint8_t f[256];
    int len = fl_secure_seal(k_s, FL_DIR_G2S, g_ctr_tx++, V_ADDR, msg, rid_ctr++, p, n, f);
    fl_app_on_rx(f, (uint16_t)len);
}

/* naechsten SECURE-Frame des Sensors entschluesseln */
static int gw_recv(int *idx, uint8_t *plain)
{
    int i = find_tx(FL_VT(FL_FT_SECURE), *idx);
    if (i < 0) return -1;
    *idx = i + 1;
    return fl_secure_open(k_s, FL_DIR_S2G, g_ctr_rx++, V_ADDR, sim.tx[i], sim.tx_len[i], plain);
}

static void gw_hello(const uint8_t gwid[8])
{
    uint8_t h[18] = {FL_VT(FL_FT_HELLO), 1};
    memcpy(h + 2, gwid, 8); memcpy(h + 10, V_GN8, 8);
    fl_app_on_connect();
    fl_app_on_notify_enabled();
    fl_app_on_rx(h, 18);
    int i = find_tx(FL_VT(FL_FT_HELLO_RSP), 0);
    if (i >= 0) fl_session_key(V_KLINK, V_GN8, sim.tx[i] + 2, k_s);
    g_ctr_tx = 0; g_ctr_rx = 0;
}

static void test_app(void)
{
    uint8_t plain[256];
    int idx;
    puts("[app] Start, Messung, Kopplung, Sitzung, Datensaetze, Einstellungen, Angriffe, Unterspannung");
    sim_reset_all(); sim.outlier_block = -1;
    fl_app_init();
    CHECK(sim.meas_calls == 1);                                               /* Selbsttest-Messung */
    CHECK(fl_log_last_seq(&g_fl.log) == 0 && g_fl.cnt.boot_id == 1);
    CHECK(g_fl.mode == FL_MODE_UNPAIRED);
    advance(2000);
    CHECK(!sim.adv_on);                                                       /* ungekoppelt: kein Advertising */
    CHECK(sim.led_on_events >= 2);                                            /* L11 gruen + gelb */
    /* Kopplungsmodus: Taster 4 s */
    press(4000);
    CHECK(g_fl.mode == FL_MODE_PAIRING && sim.adv_on && sim.adv_conn && sim.adv_int == 500);
    CHECK(sim.adv[23] & FL_ST_PAIRING);
    { char nm[12]; memcpy(nm, sim.adv + 5, 11); nm[11] = 0; CHECK(strcmp(nm, "fluidi-ABCD") == 0); }
    /* PAIR_REQ mit Gateway-Schluessel aus Python-Vektor */
    fl_app_on_connect();
    sim.tx_n = 0;
    sim_rng_queue(V_SNONCE16, 16);
    uint8_t req[2 + 104] = {FL_VT(FL_FT_PAIR), FL_PAIR_REQ};
    memcpy(req + 2, V_PAIRREQ, 104);
    fl_app_on_rx(req, sizeof req);
    idx = find_tx(FL_VT(FL_FT_PAIR), 0);
    CHECK(idx >= 0 && sim.tx[idx][1] == FL_PAIR_RSP && sim.tx_len[idx] == 93);
    /* PAIR_RSP-Nutzlast muss byte-genau der Python-Referenz entsprechen (fw 0.1.0, hw 0x0B) */
    CHECK(idx >= 0 && memcmp(sim.tx[idx] + 2, V_PAIRRSP, 91) == 0);
    advance(8000);                                       /* Nutzer/Gateway brauchen Zeit: keine 3-s-Trennung (K-2) */
    CHECK(sim.disconnect_req == 0 && g_fl.sess == FL_SESS_PAIR_RSP_SENT);
    uint8_t show[2 + 16] = {FL_VT(FL_FT_PAIR), FL_PAIR_REVEAL};
    memcpy(show + 2, V_GWNONCE16, 16);
    fl_app_on_rx(show, sizeof show);
    CHECK(g_fl.sess == FL_SESS_PAIR_SHOWING && g_fl.led.active == FL_LED_L5_SAS);
    CHECK(memcmp(g_fl.sas, V_SAS, 5) == 0);
    /* Gateway bestaetigt zuerst -> noch nicht gespeichert */
    uint8_t cg[18] = {FL_VT(FL_FT_PAIR), FL_PAIR_CONFIRM_G};
    memcpy(cg + 2, V_MAC_G, 16);
    fl_app_on_rx(cg, 18);
    CHECK(!g_fl.pair.paired);
    advance(300);
    press(200);                                                               /* Nutzer: Farben stimmen */
    idx = find_tx(FL_VT(FL_FT_PAIR), idx + 1);
    CHECK(idx >= 0 && sim.tx[idx][1] == FL_PAIR_CONFIRM_S && memcmp(sim.tx[idx] + 2, V_MAC_S, 16) == 0);
    idx = find_tx(FL_VT(FL_FT_PAIR), idx + 1);
    CHECK(idx >= 0 && sim.tx[idx][1] == FL_PAIR_DONE && sim.tx[idx][2] == 0);
    CHECK(g_fl.pair.paired && memcmp(g_fl.pair.k_link, V_KLINK, 16) == 0 && g_fl.mode == FL_MODE_NORMAL);
    CHECK(sim.nv_len[FL_NV_PAIR] == sizeof(fl_pairing_t));
    fl_app_on_disconnect();
    advance(2000);
    CHECK(sim.adv_on && sim.adv_conn && sim.adv_int == 27500 && (sim.adv[23] & FL_ST_PAIRED));
    CHECK(sim.adv[27] == V_GWHINT[0] && sim.adv[28] == V_GWHINT[1]);
    CHECK(sim.adv[23] & FL_ST_DATA_PENDING);

    /* Sitzung: HELLO -> HELLO_RSP + SESSION_INFO */
    sim.tx_n = 0;
    gw_hello(V_GWID);
    idx = 0;
    int n = gw_recv(&idx, plain);
    CHECK(n == 2 + 52 && plain[0] == FL_MSG_SESSION_INFO && plain[2] == 1);
    CHECK(plain[2 + 9] == 0x0B && fl_get_u16(plain + 2 + 11) == 1);         /* hw_rev, boot_id */
    uint32_t last = fl_get_u32(plain + 2 + 19), oldest = fl_get_u32(plain + 2 + 23);
    CHECK(last == 0 && oldest == 0);                                          /* Startmessung (Selbsttest) */
    CHECK(fl_get_u16(plain + 2 + 42) == 840);
    /* TIME_SET */
    uint8_t ts[10]; fl_put_u64(ts, 1794000000000ull); fl_put_u16(ts, 0); fl_put_u64(ts, 1794000000000ull); fl_put_u16(ts + 8, 60);
    gw_send_secure(FL_MSG_TIME_SET, ts, 10);
    n = gw_recv(&idx, plain); CHECK(n == 3 && plain[0] == 0x91 && plain[2] == 0 && g_fl.time_valid);
    /* READ_RECORDS ab 0 */
    uint8_t rr[6]; fl_put_u32(rr, 0); fl_put_u16(rr + 4, 0);
    gw_send_secure(FL_MSG_READ_RECORDS, rr, 6);
    n = gw_recv(&idx, plain);
    CHECK(n == 2 + 2 + 20 && plain[0] == 0x92 && plain[2] == 1 && plain[3] == 0);
    fl_record_t rec; fl_record_decode(plain + 4, &rec);
    CHECK(rec.seq == 0 && rec.cause == FL_CAUSE_AUTO && abs((int)rec.c_probe - 3000) <= 3 && rec.temp == 2150);
    /* ACK */
    uint8_t ack[4]; fl_put_u32(ack, 0);
    gw_send_secure(FL_MSG_ACK_RECORDS, ack, 4);
    n = gw_recv(&idx, plain); CHECK(n == 7 && plain[0] == 0x93 && fl_get_u32(plain + 3) == 1);
    CHECK(!fl_log_pending(&g_fl.log));
    /* MEASURE (Kalibrierung nass) */
    sim.c_probe_pf = 44.1;
    uint8_t ms[2] = {2, 0};
    gw_send_secure(FL_MSG_MEASURE, ms, 2);
    uint32_t mc0 = sim.meas_calls;
    n = gw_recv(&idx, plain); CHECK(n == 2 + 5 && plain[0] == 0x94 && plain[2] == 0);
    uint32_t meas_seq = fl_get_u32(plain + 3);
    CHECK(meas_seq == 1 && sim.meas_calls == mc0);                            /* F-W5: keine Messung waehrend Funk */
    /* SET_SETTINGS (water_raw = 30 pF, ungueltiger zweiter Satz) / GET_SETTINGS */
    uint8_t ss[2 + 4 + 6] = {0, 0, 0x05, 2, 0xB8, 0x0B, 0x07, 4, 0, 0, 0xA0, 0x05}; fl_put_u16(ss, 3);   /* LED-Fenster ganztags */
    gw_send_secure(FL_MSG_SET_SETTINGS, ss, sizeof ss);
    n = gw_recv(&idx, plain); CHECK(n == 4 && plain[0] == 0x96 && plain[2] == 0 && g_fl.set.water_raw == 3000 && g_fl.set.settings_ver == 3);
    uint8_t ss2[2 + 3] = {4, 0, 0x08, 1, 5};
    gw_send_secure(FL_MSG_SET_SETTINGS, ss2, sizeof ss2);
    n = gw_recv(&idx, plain); CHECK(plain[2] == FL_E_BAD_PARAM && plain[3] == 0x08 && g_fl.set.settings_ver == 3);
    gw_send_secure(FL_MSG_GET_SETTINGS, NULL, 0);
    n = gw_recv(&idx, plain); CHECK(n > 10 && plain[0] == 0x95 && fl_get_u16(plain + 2) == 3);
    /* GET_INFO (erweitert), unbekannter Befehl, GET_DIAG */
    gw_send_secure(FL_MSG_GET_INFO, NULL, 0);
    n = gw_recv(&idx, plain); CHECK(n == 2 + 68 && plain[0] == 0x90 && fl_get_u32(plain + 2 + 52) == 1 && fl_get_u32(plain + 2 + 48) == 0);
    gw_send_secure(0x55, NULL, 0);
    n = gw_recv(&idx, plain); CHECK(plain[0] == 0xFF && plain[2] == FL_E_UNKNOWN_CMD);
    gw_send_secure(FL_MSG_GET_DIAG, NULL, 0);
    n = gw_recv(&idx, plain); CHECK(plain[0] == 0x98 && n >= 2 + 1 + 8);
    /* Replay eines alten Frames -> Trennung */
    uint32_t disc = sim.disconnect_req;
    uint8_t f[64]; int fl = fl_secure_seal(k_s, FL_DIR_G2S, 2, V_ADDR, FL_MSG_GET_INFO, 9, NULL, 0, f);
    fl_app_on_rx(f, (uint16_t)fl);
    CHECK(sim.disconnect_req == disc + 1);
    fl_app_on_disconnect();
    CHECK(sim.meas_calls == mc0 + 1 && fl_log_read(&g_fl.log, meas_seq, &rec) == 0);   /* Messung nach dem Trennen */
    CHECK(rec.cause == FL_CAUSE_CAL_WET && abs((int)rec.c_probe - 4410) <= 4);
    advance(1000);

    /* Fremdes Gateway: 3 Fehlversuche -> Sperre 30 min (nicht verbindbar) */
    uint8_t other[8] = {9, 9, 9, 9, 9, 9, 9, 9};
    for (int i = 0; i < 3; i++) {
        sim.tx_n = 0; gw_hello(other);
        CHECK(sim.tx_n >= 1 && sim.tx[0][0] == FL_VT(FL_FT_ERROR) && sim.tx[0][1] == FL_E_NOT_PAIRED);
        fl_app_on_disconnect(); advance(100);
    }
    CHECK(g_fl.locked && !sim.adv_conn && (sim.adv[23] & FL_ST_LOCKED));
    advance(31u * 60000u);
    CHECK(!g_fl.locked && sim.adv_conn);
    /* HELLO-Fristen v2 (K-1): 1 s ab CCCD, 5 s absolut; Zeitueberschreitung ist KEIN Fehlversuch */
    uint16_t af = g_fl.cnt.auth_fail;
    fl_app_on_connect(); disc = sim.disconnect_req;
    advance(4000); CHECK(sim.disconnect_req == disc);                        /* BlueZ-Dienstsuche darf dauern */
    advance(1100); CHECK(sim.disconnect_req == disc + 1);
    fl_app_on_disconnect();
    fl_app_on_connect(); fl_app_on_notify_enabled(); disc = sim.disconnect_req;
    advance(1100); CHECK(sim.disconnect_req == disc + 1);
    fl_app_on_disconnect();
    for (int i = 0; i < 5; i++) { fl_app_on_connect(); advance(5100); fl_app_on_disconnect(); }
    CHECK(g_fl.cnt.auth_fail == af && !g_fl.locked);                          /* keine Selbstaussperrung */
    /* RNG-Ausfall beim HELLO: keine Sitzung (F-W4) */
    sim.rng_fail = true; sim.tx_n = 0; disc = sim.disconnect_req;
    gw_hello(V_GWID);
    CHECK(find_tx(FL_VT(FL_FT_HELLO_RSP), 0) < 0 && find_tx(FL_VT(FL_FT_SECURE), 0) < 0 && sim.disconnect_req == disc + 1);
    fl_app_on_disconnect(); sim.rng_fail = false;
    /* OTA_DATA mit Zaehlerluecke (W-2) wird angenommen, andere Nachrichten mit Luecke nicht */
    sim.tx_n = 0; gw_hello(V_GWID); idx = 0; gw_recv(&idx, plain);
    { static uint8_t img[600]; uint8_t b[48] = {0}, d[4 + 200];
      for (unsigned i = 0; i < sizeof img; i++) img[i] = (uint8_t)i;
      fl_put_u32(b, sizeof img); b[4] = 0; b[5] = 2; fl_sha256(img, sizeof img, b + 16);
      gw_send_secure(FL_MSG_OTA_BEGIN, b, 48);
      n = gw_recv(&idx, plain); CHECK(n == 2 + 7 && plain[2] == 0);
      fl_put_u32(d, 0); memcpy(d + 4, img, 200); gw_send_secure(FL_MSG_OTA_DATA, d, 204);
      g_ctr_tx++;                                                            /* ein Frame ging verloren */
      fl_put_u32(d, 200); memcpy(d + 4, img + 200, 200); gw_send_secure(FL_MSG_OTA_DATA, d, 204);
      CHECK(g_fl.connected && g_fl.sess == FL_SESS_SECURE && g_fl.ota.next_off == 400);   /* Luecke angenommen */
      disc = sim.disconnect_req; g_ctr_tx++;
      gw_send_secure(FL_MSG_GET_INFO, NULL, 0);
      CHECK(sim.disconnect_req == disc + 1); }                               /* Luecke ausserhalb OTA_DATA */
    fl_app_on_disconnect();
    /* Giessen noetig: periodische LED (Messung unter Schwelle) */
    sim.c_probe_pf = 25.0;
    uint32_t mc = sim.meas_calls;
    advance(4u * 3600u * 1000u + 400000u);
    CHECK(sim.meas_calls > mc && g_fl.water);
    uint32_t ev = sim.led_on_events;
    advance(10u * 60000u);
    CHECK(sim.led_on_events > ev);
    /* Unterspannung unter Last -> geordnete Abschaltung */
    sim.vbat_load = 2250;                                                     /* < 2.3 V: sofort (ANNAHME) */
    uint32_t sd = sim.shutdowns;
    press(200);
    CHECK(sim.shutdowns == sd + 1 && g_fl.mode == FL_MODE_UNDERVOLTAGE && g_fl.cnt.last_error == FL_E_UNDERVOLTAGE);
    /* Neustart nach Unterspannung bei erholter Zelle */
    sim.vbat_load = 0; sim.vbat = 2900;
    fl_app_init();
    CHECK(g_fl.reset_reason == FL_RR_UNDERVOLTAGE && g_fl.cnt.boot_id == 2 && g_fl.pair.paired);
    CHECK(fl_log_last_seq(&g_fl.log) >= 3);                                   /* seq laeuft ueber den Neustart weiter */
    /* Werkseinstellung: 10 s halten, loslassen, kurz bestaetigen */
    uint32_t seq_before = fl_log_last_seq(&g_fl.log);
    press(10500);
    advance(500);
    press(200);
    CHECK(!g_fl.pair.paired && g_fl.mode == FL_MODE_UNPAIRED && g_fl.reboot_pending);
    advance(2000);
    CHECK(sim.reboots >= 1);
    fl_record_t r2; fl_app_measure(FL_CAUSE_AUTO, &r2);
    CHECK(r2.seq == seq_before + 1);                                          /* seq behalten */
}


/* ---------------- Kopplung: Commitment-Verletzung (F-K1) ---------------- */
static void test_pair_reveal(void)
{
    puts("[pair] Reveal passt nicht zum Commitment -> Abbruch + Fehlversuch");
    sim_reset_all(); sim.outlier_block = -1;
    fl_app_init();
    advance(1000);
    press(4000);
    CHECK(g_fl.mode == FL_MODE_PAIRING);
    fl_app_on_connect(); fl_app_on_notify_enabled();
    uint8_t req[2 + 104] = {FL_VT(FL_FT_PAIR), FL_PAIR_REQ};
    memcpy(req + 2, V_PAIRREQ, 104);
    fl_app_on_rx(req, sizeof req);
    uint16_t af = g_fl.cnt.auth_fail;
    uint8_t rv[2 + 16] = {FL_VT(FL_FT_PAIR), FL_PAIR_REVEAL};
    memcpy(rv + 2, V_GWNONCE16, 16); rv[2] ^= 1;                         /* Angreifer aendert seine Nonce */
    fl_app_on_rx(rv, sizeof rv);
    CHECK(g_fl.cnt.auth_fail == af + 1 && !g_fl.pair.paired && g_fl.led.active == FL_LED_L7_PAIR_FAIL);
    CHECK(g_fl.sess == FL_SESS_CLOSING);
    /* PAIR_REVEAL ohne vorheriges PAIR_REQ wird abgelehnt */
    fl_app_on_disconnect(); press(4000); fl_app_on_connect(); fl_app_on_notify_enabled();
    rv[2] ^= 1; fl_app_on_rx(rv, sizeof rv);
    CHECK(!g_fl.pair.paired && g_fl.sess == FL_SESS_CLOSING);
    fl_app_on_disconnect();
    /* N-1: Commitment-Verletzung zaehlt als kryptografischer Fehlversuch -> nach 3 in Folge LOCKED */
    CHECK(!g_fl.locked);
    for (int k = 0; k < 3 && !g_fl.locked; k++) {
        press(4000); fl_app_on_connect(); fl_app_on_notify_enabled();
        fl_app_on_rx(req, sizeof req);
        rv[2] ^= 0x55; fl_app_on_rx(rv, sizeof rv);
        fl_app_on_disconnect();
    }
    CHECK(g_fl.locked && g_fl.fail_streak == 0);
}

/* ---------------- Reset-Schleifen (F-W3) ---------------- */
static void test_resets(void)
{
    puts("[reset] Reset-Schleife, Brownout bei schwacher Zelle, Taster klemmt bei Abschaltung, geplanter Neustart");
    sim_reset_all(); sim.outlier_block = -1;
    fl_app_init();                                       /* Power-on */
    CHECK(sim.shutdowns == 0 && (sim.retained & FL_RET_ABN_MASK) == 0);
    sim.reset_reason = FL_RR_WATCHDOG; fl_app_init(); CHECK(sim.shutdowns == 0 && (sim.retained & FL_RET_ABN_MASK) == 1);
    sim.reset_reason = FL_RR_HARDFAULT; fl_app_init(); CHECK(sim.shutdowns == 0 && (sim.retained & FL_RET_ABN_MASK) == 2);
    uint32_t nvw = sim.nv_writes;
    sim.reset_reason = FL_RR_SOFTWARE; fl_app_init();    /* fataler Fehler (nicht geplant) = 3. abnormaler Start */
    CHECK(sim.shutdowns == 1 && (sim.retained & FL_RET_BACKOFF) && sim.nv_writes == nvw);   /* ohne Flash-Schreiben */
    sim.reset_reason = FL_RR_PIN; fl_app_init();         /* Nutzer weckt per Taster */
    CHECK(sim.shutdowns == 1 && (sim.retained & FL_RET_ABN_MASK) == 0 && g_fl.cnt.backoffs == 1);
    /* geplanter Neustart zaehlt nicht */
    sim.retained |= FL_RET_PLANNED; sim.reset_reason = FL_RR_SOFTWARE; fl_app_init();
    CHECK((sim.retained & FL_RET_ABN_MASK) == 0 && !(sim.retained & FL_RET_PLANNED));
    /* stabiler Betrieb 10 min nullt den Zaehler */
    sim.reset_reason = FL_RR_WATCHDOG; fl_app_init(); CHECK((sim.retained & FL_RET_ABN_MASK) == 1);
    advance(FL_STABLE_MS + 1000); CHECK((sim.retained & FL_RET_ABN_MASK) == 0);
    /* Brownout mit schwacher Zelle: sofort aus, kein NV-Schreiben, keine Messung */
    sim.reset_reason = FL_RR_BROWNOUT; sim.vbat = 2500; nvw = sim.nv_writes;
    uint32_t mc = sim.meas_calls, sd = sim.shutdowns;
    fl_app_init();
    CHECK(sim.shutdowns == sd + 1 && sim.nv_writes == nvw && sim.meas_calls == mc && (sim.retained & FL_RET_UV));
    /* Wecken per Taster bei weiterhin schwacher Zelle: kurz rot, wieder aus */
    sim.reset_reason = FL_RR_PIN; fl_app_init(); CHECK(sim.shutdowns == sd + 2 && sim.nv_writes == nvw);
    /* Erholt (Zellwechsel = Power-on, Retention 0) */
    sim.retained = 0; sim.reset_reason = FL_RR_POWER_ON; sim.vbat = 2950; fl_app_init(); CHECK(g_fl.mode != FL_MODE_UNDERVOLTAGE);
    /* Unterspannung waehrend Tastendruck, Taster bleibt gedrueckt: Abschaltung OHNE Tasterwecken */
    sd = sim.shutdowns;
    sim.vbat_load = 2250; sim.button_level = true; fl_app_on_button(true);
    advance(200);
    fl_app_on_button(false);                              /* Flanke gemeldet, Kontakt klemmt aber (Pegel low) */
    CHECK(sim.shutdowns == sd + 1 && g_fl.mode == FL_MODE_UNDERVOLTAGE && !sim.shutdown_wake && !sim.pullup);
    /* Gegenprobe: Taster losgelassen -> Wecken per Taster bleibt aktiv */
    sim.retained = 0; sim.reset_reason = FL_RR_POWER_ON; sim.vbat_load = 0; sim.button_level = false; fl_app_init();
    sim.vbat_load = 2250; sd = sim.shutdowns;
    { fl_record_t r; fl_app_measure(FL_CAUSE_AUTO, &r); }
    CHECK(sim.shutdowns == sd + 1 && sim.shutdown_wake);
    sim.button_level = false; sim.vbat_load = 0;
    /* N-4: Batteriemonitor liefert 0 beim Start -> wie Unterspannung (kein Weiterlaufen ohne Pruefung) */
    sim.retained = 0; sim.reset_reason = FL_RR_POWER_ON; sim.vbat = 0; sd = sim.shutdowns; nvw = sim.nv_writes;
    fl_app_init();
    CHECK(sim.shutdowns == sd + 1 && sim.nv_writes == nvw && g_fl.mode == FL_MODE_UNDERVOLTAGE);
    /* N-2: Ruhewert ok, aber Einbruch bei der ersten Lastmessung (POR-Zyklus am Lebensende): kein NV-Schreiben */
    sim.retained = 0; sim.vbat = 2600; sim.vbat_load = 2250; sd = sim.shutdowns; nvw = sim.nv_writes;
    fl_app_init();
    CHECK(sim.shutdowns == sd + 1 && sim.nv_writes == nvw && (sim.retained & FL_RET_UV));
    sim.vbat = 2950; sim.vbat_load = 0;
}

/* ---------------- Ausnahmebehandlung (O-5) ---------------- */
static int diag_count(uint8_t code, int skip_detail)
{
    int k = 0;
    for (uint8_t i = 0; i < g_fl.diag.count; i++)
        if (g_fl.diag.e[i].code == code && g_fl.diag.e[i].detail != skip_detail) k++;
    return k;
}

static void test_fault(void)
{
    puts("[fault] O-5: HardFault -> fl_fault_handler (Retention-Bit, Systemreset) -> Grund hardfault, F-W3 zaehlt");
    /* Belegung: FL_RET_FAULT ueberschneidet weder Serien- noch TF-Bits und liegt im 18-bit-Register */
    CHECK((FL_RET_FAULT & (FL_RET_ABN_MASK | FL_RET_PLANNED | FL_RET_UV | FL_RET_BACKOFF)) == 0);
    CHECK((FL_RET_FAULT & ~0x3FFFFu) == 0 && (FL_RET_FAULT & (0x7Fu << 7)) != 0);   /* Bit in 7..17: alte Serie loescht es */
    sim_reset_all(); sim.outlier_block = -1;
    fl_app_init(); advance(3000);                                /* Power-on */
    uint16_t wdt0 = g_fl.cnt.wdt_resets;
    int hf0 = diag_count(FL_E_HARDFAULT, 0xBF);
    /* 1. Absturz waehrend eines geplanten Neustarts (PLANNED gesetzt): Handler loescht PLANNED, Grund hardfault */
    sim.retained |= FL_RET_PLANNED;
    uint32_t rb = sim.reboots, nvw = sim.nv_writes;
    sim_fault();
    CHECK(sim.reboots == rb + 1 && (sim.retained & FL_RET_FAULT) && !(sim.retained & FL_RET_PLANNED));
    CHECK(sim.nv_writes == nvw);                                 /* Fehlerpfad schreibt nichts */
    sim.reset_reason = FL_RR_SOFTWARE; fl_app_init(); advance(3000);
    CHECK(g_fl.reset_reason == FL_RR_HARDFAULT && !(sim.retained & FL_RET_FAULT));
    CHECK((sim.retained & FL_RET_ABN_MASK) == 1 && sim.shutdowns == 0);
    CHECK(g_fl.cnt.wdt_resets == wdt0 && diag_count(FL_E_HARDFAULT, 0xBF) == hf0 + 1);
    CHECK(diag_count(FL_E_WDT_RESET, -1) == 0);
    /* 2. zweiter Absturz */
    sim_fault(); sim.reset_reason = FL_RR_SOFTWARE; fl_app_init(); advance(3000);
    CHECK(g_fl.reset_reason == FL_RR_HARDFAULT && (sim.retained & FL_RET_ABN_MASK) == 2 && sim.shutdowns == 0);
    /* 3. dritter: Reset-Schleife -> Abschaltung ohne Flash-Schreiben (F-W3a/c), Bit geloescht */
    nvw = sim.nv_writes; uint32_t fw = sim.flash_writes;
    sim_fault(); sim.reset_reason = FL_RR_SOFTWARE; fl_app_init();
    CHECK(sim.shutdowns == 1 && (sim.retained & FL_RET_BACKOFF) && !(sim.retained & FL_RET_FAULT));
    CHECK(sim.nv_writes == nvw && sim.flash_writes == fw);
    /* Taster weckt: Normalbetrieb, Backoff gezaehlt */
    sim.reset_reason = FL_RR_PIN; fl_app_init(); advance(3000);
    CHECK(g_fl.mode != FL_MODE_UNDERVOLTAGE && g_fl.cnt.backoffs == 1 && g_fl.reset_reason == FL_RR_PIN);
    CHECK(g_fl.cnt.wdt_resets == wdt0);
    /* Gegenproben: ungeplanter Software-Reset ohne Bit bleibt "software"; Bit + Pin-/Watchdog-Reset aendert den
     * Hardware-Grund nicht (Bit gilt nur fuer SYSRST), wird aber geloescht */
    sim.reset_reason = FL_RR_SOFTWARE; fl_app_init(); advance(3000);
    CHECK(g_fl.reset_reason == FL_RR_SOFTWARE && (sim.retained & FL_RET_ABN_MASK) == 1);
    sim.retained |= FL_RET_FAULT; sim.reset_reason = FL_RR_WATCHDOG; fl_app_init(); advance(3000);
    CHECK(g_fl.reset_reason == FL_RR_WATCHDOG && !(sim.retained & FL_RET_FAULT) && (sim.retained & FL_RET_ABN_MASK) == 2);
    sim.retained |= FL_RET_FAULT; sim.reset_reason = FL_RR_PIN; fl_app_init(); advance(3000);
    CHECK(g_fl.reset_reason == FL_RR_PIN && !(sim.retained & FL_RET_FAULT) && (sim.retained & FL_RET_ABN_MASK) == 0);
    /* Absturz waehrend Unterspannungs-Abschaltung: Unterspannung hat Vorrang (Grund 6) */
    sim.retained |= FL_RET_UV; sim_fault(); sim.reset_reason = FL_RR_SOFTWARE; fl_app_init(); advance(3000);
    CHECK(g_fl.reset_reason == FL_RR_UNDERVOLTAGE && !(sim.retained & FL_RET_FAULT));
    /* stabiler Betrieb 10 min nullt den Zaehler auch nach Abstuerzen */
    sim.retained = 0; sim.reset_reason = FL_RR_POWER_ON; fl_app_init();
    sim_fault(); sim.reset_reason = FL_RR_SOFTWARE; fl_app_init();
    CHECK((sim.retained & FL_RET_ABN_MASK) == 1);
    advance(FL_STABLE_MS + 1000); CHECK((sim.retained & FL_RET_ABN_MASK) == 0);
}

/* ---------------- Asserts / Stackueberlauf (O-5 Folge, platform/cc23/fl_assert.c) ---------------- */
void AssertHandler(uint8_t assertCause, uint8_t assertSubcause);
void vApplicationStackOverflowHook(void *pxTask, char *pcTaskName);

/* ruft f(c) auf; true, wenn fl_fault_handler erreicht wurde (statt Rueckkehr oder Endlosschleife) */
static bool reaches_fault(int which, uint8_t cause, uint8_t sub)
{
    jmp_buf jb;
    uint32_t n = sim_fault_calls;
    sim_fault_jmp = &jb;
    if (setjmp(jb) == 0) {
        if (which == 0) AssertHandler(cause, sub);
        else vApplicationStackOverflowHook(NULL, "fl");
        sim_fault_jmp = NULL;
        return false;                                           /* zurueckgekehrt: Fehler */
    }
    sim_fault_jmp = NULL;
    return sim_fault_calls == n + 1;
}

static void test_assert(void)
{
    puts("[assert] BLE-Stack-Assert (alle Ursachen) und FreeRTOS-Stackueberlauf -> fl_fault_handler, Grund hardfault");
    /* SDK assert.h Ursachen 0x00..0x0C, dazu BLE/MAC/RCN-Bereich und unbekannt (SDK: default -> Spinlock) */
    static const uint8_t causes[] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C,
                                     0x20, 0x40, 0x60, 0xFF};
    int ok = 0;
    for (size_t i = 0; i < sizeof causes; i++) {
        sim.retained = FL_RET_PLANNED;
        uint32_t nvw = sim.nv_writes, fw = sim.flash_writes;
        if (reaches_fault(0, causes[i], (uint8_t)i) && sim.retained == FL_RET_FAULT && sim.nv_writes == nvw &&
            sim.flash_writes == fw) ok++;
    }
    CHECK(ok == (int)sizeof causes);
    /* Ablauf wie im Feld: 3 Asserts in Folge -> Abschaltung ohne Flash-Schreiben; Grund jeweils hardfault */
    sim_reset_all(); sim.outlier_block = -1;
    fl_app_init(); advance(3000);
    CHECK(reaches_fault(0, 0x04, 0));                           /* out of memory */
    sim.reset_reason = FL_RR_SOFTWARE; fl_app_init(); advance(3000);
    CHECK(g_fl.reset_reason == FL_RR_HARDFAULT && (sim.retained & FL_RET_ABN_MASK) == 1 && !(sim.retained & FL_RET_FAULT));
    CHECK(reaches_fault(1, 0, 0));                              /* Stackueberlauf */
    sim.reset_reason = FL_RR_SOFTWARE; fl_app_init(); advance(3000);
    CHECK(g_fl.reset_reason == FL_RR_HARDFAULT && (sim.retained & FL_RET_ABN_MASK) == 2);
    uint32_t nvw = sim.nv_writes, fw = sim.flash_writes;
    CHECK(reaches_fault(0, 0x05, 0));                           /* ICall abort */
    sim.reset_reason = FL_RR_SOFTWARE; fl_app_init();
    CHECK(sim.shutdowns == 1 && (sim.retained & FL_RET_BACKOFF) && sim.nv_writes == nvw && sim.flash_writes == fw);
    CHECK(g_fl.cnt.wdt_resets == 0);
}

/* ---------------- C-1: IO-Latches nach Shutdown, W-2: Zaehlung vor fl_app_init ---------------- */
static void test_latch(void)
{
    puts("[latch] C-1: nach Shutdown-Wecken Grund vor Freigabe lesen, Latches freigeben; LED/Messung danach, Gruende stimmen");
    sim_reset_all(); sim.outlier_block = -1;
    fl_app_init(); advance(3000);
    CHECK(sim.io_releases == 1 && sim.rr_reads_at_release >= 1 && !sim.latched);
    /* Modell: ohne Freigabe kleben SDDET/IOWUSD -> ein spaeterer Systemreset wuerde als POWER_ON erkannt */
    sim.sddet = true; sim.reset_reason = FL_RR_SOFTWARE; CHECK(fl_port_reset_reason() == FL_RR_POWER_ON); sim.sddet = false;
    /* Abschaltung (Reset-Schleife), Wecken per Taster */
    for (int k = 0; k < 3; k++) { sim.reset_reason = FL_RR_SOFTWARE; fl_app_init(); }
    CHECK(sim.shutdowns == 1 && sim.latched && sim.sddet);
    uint32_t rel = sim.io_releases, rd = sim.rr_reads, led0 = sim.led_on_events, mc = sim.meas_calls;
    sim.latched_violations = 0;
    sim.reset_reason = FL_RR_PIN; fl_app_init(); advance(3000);
    CHECK(sim.io_releases == rel + 1 && sim.rr_reads_at_release > rd);    /* Grund gelesen, DANN freigegeben */
    CHECK(!sim.latched && !sim.sddet && sim.latched_violations == 0);
    CHECK(g_fl.reset_reason == FL_RR_PIN && sim.meas_calls > mc && sim.led_on_events > led0);  /* L11 sichtbar, Messung */
    CHECK(g_fl.mode != FL_MODE_UNDERVOLTAGE);
    /* danach: Absturz -> hardfault (nicht power_on), geplanter Neustart -> software */
    sim_fault(); sim.reset_reason = FL_RR_SOFTWARE; fl_app_init(); advance(3000);
    CHECK(g_fl.reset_reason == FL_RR_HARDFAULT && (sim.retained & FL_RET_ABN_MASK) == 1);
    sim.retained = (sim.retained & ~FL_RET_ABN_MASK) | FL_RET_PLANNED;      /* wie planned_reboot (REBOOT) */
    sim.reset_reason = FL_RR_SOFTWARE; fl_app_init(); advance(3000);
    CHECK(g_fl.reset_reason == FL_RR_SOFTWARE && (sim.retained & FL_RET_ABN_MASK) == 0);
    /* Unterspannungs-Abschaltung, Wecken, erholt: ebenfalls freigegeben */
    sim.vbat_load = 2250; { fl_record_t r; fl_app_measure(FL_CAUSE_AUTO, &r); }
    CHECK(sim.latched);
    sim.vbat_load = 0; sim.latched_violations = 0; sim.reset_reason = FL_RR_PIN; fl_app_init(); advance(3000);
    CHECK(!sim.latched && sim.latched_violations == 0 && g_fl.mode != FL_MODE_UNDERVOLTAGE);
}

static void test_early(void)
{
    puts("[early] W-2: Absturz/Assert/Watchdog vor fl_app_init (BLE-Init) zaehlt, 3. Start schaltet ohne Flash ab");
    sim_reset_all(); sim.outlier_block = -1;
    fl_app_init(); advance(3000);                                /* Normalbetrieb */
    uint32_t nvw = sim.nv_writes, fw = sim.flash_writes, fe = sim.flash_erases;
    /* Absturz waehrend der Stack-Initialisierung: nur fl_app_early laeuft (fl_platform_early_init), dann Fehler */
    sim_fault(); sim.reset_reason = FL_RR_SOFTWARE;
    CHECK(!fl_app_early() && (sim.retained & FL_RET_ABN_MASK) == 1 && !(sim.retained & FL_RET_FAULT));
    sim_fault(); sim.reset_reason = FL_RR_SOFTWARE;
    CHECK(!fl_app_early() && (sim.retained & FL_RET_ABN_MASK) == 2);
    sim_fault(); sim.reset_reason = FL_RR_SOFTWARE;
    CHECK(fl_app_early() && sim.shutdowns == 1 && (sim.retained & FL_RET_BACKOFF) && !(sim.retained & FL_RET_ABN_MASK));
    CHECK(sim.nv_writes == nvw && sim.flash_writes == fw && sim.flash_erases == fe);   /* kein Flash im ganzen Ablauf */
    /* Wecken per Taster: Normalbetrieb, Abschaltung einmal gezaehlt */
    sim.reset_reason = FL_RR_PIN; fl_app_init(); advance(3000);
    CHECK(g_fl.mode != FL_MODE_UNDERVOLTAGE && g_fl.cnt.backoffs == 1 && (sim.retained & FL_RET_ABN_MASK) == 0);
    /* Hardware-Ablauf mit Erfolg: fl_app_early (frueh) + fl_app_init (spaet) zaehlen EINMAL */
    sim_fault(); sim.reset_reason = FL_RR_SOFTWARE;
    CHECK(!fl_app_early());
    fl_app_init(); advance(3000);
    CHECK(g_fl.reset_reason == FL_RR_HARDFAULT && (sim.retained & FL_RET_ABN_MASK) == 1 && sim.io_releases > 0);
    /* Watchdog (MCUboot-/Init-Haenger) vor fl_app_init zaehlt ebenso; gemischt mit Absturz -> Abschaltung */
    sim.reset_reason = FL_RR_WATCHDOG; CHECK(!fl_app_early() && (sim.retained & FL_RET_ABN_MASK) == 2);
    sim_fault(); sim.reset_reason = FL_RR_SOFTWARE; CHECK(fl_app_early() && sim.shutdowns == 2);
}

/* ---------------- Image-Pruefung nach OTA_END (W-6, F-L1) ---------------- */
static void put_img(uint8_t maj, uint8_t min, uint16_t rev, uint32_t build, uint32_t sc, int hw)
{
    uint8_t *m = sim_slot1();
    memset(m, 0xFF, 0x1000);
    memset(m, 0, 0x100);
    fl_put_u32(m, 0x96f3b83du); fl_put_u16(m + 8, 0x100);
    uint16_t prot = 4 + 8 + (hw >= 0 ? 5 : 0);
    fl_put_u16(m + 10, prot); fl_put_u32(m + 12, 0x200);
    m[20] = maj; m[21] = min; fl_put_u16(m + 22, rev); fl_put_u32(m + 24, build);
    uint8_t *t = m + 0x300;
    fl_put_u16(t, 0x6908); fl_put_u16(t + 2, prot);
    fl_put_u16(t + 4, 0x50); fl_put_u16(t + 6, 4); fl_put_u32(t + 8, sc);
    if (hw >= 0) { fl_put_u16(t + 12, 0xA0); fl_put_u16(t + 14, 1); t[16] = (uint8_t)hw; }
}

static void test_img_check(void)
{
    puts("[ota] Kopf-/TLV-Pruefung: Version, Sicherheitszaehler, hw_rev");
    sim_reset_all();
    uint8_t run[4] = {0, 1, 0, 0};
    put_img(0, 2, 0, 1, 1, 0x0B); CHECK(fl_ota_check_image(fl_port_slot1_flash(), run, 5, 1, 0x0B) == 0);
    fl_img_info_t in; CHECK(fl_img_parse(fl_port_slot1_flash(), 0, &in) == 0 && in.sec_cnt == 1 && in.hw_rev == 0x0B);
    CHECK(fl_ota_check_image(fl_port_slot1_flash(), run, 5, 1, 0x0A) == FL_E_OTA_HW_MISMATCH);
    CHECK(fl_ota_check_image(fl_port_slot1_flash(), run, 5, 2, 0x0B) == FL_E_OTA_ROLLBACK);   /* Zaehler kleiner */
    put_img(0, 1, 0, 1, 1, 0x0B); CHECK(fl_ota_check_image(fl_port_slot1_flash(), run, 5, 0, 0x0B) == FL_E_OTA_ROLLBACK);
    put_img(0, 2, 0, 1, 1, -1); CHECK(fl_ota_check_image(fl_port_slot1_flash(), run, 5, 0, 0x0B) == FL_E_OTA_HW_MISMATCH);
    sim_slot1()[0] = 0; CHECK(fl_ota_check_image(fl_port_slot1_flash(), run, 5, 0, 0x0B) == FL_E_OTA_HASH);
}

int main(void)
{
    test_crypto();
    test_proto();
    test_settings();
    test_meas();
    test_ringlog();
    test_nvstore();
    test_led_fw4();
    test_ui();
    test_ota();
    test_app();
    test_pair_reveal();
    test_resets();
    test_fault();
    test_assert();
    test_latch();
    test_early();
    test_img_check();
    printf("\nErgebnis: %d Pruefungen bestanden, %d fehlgeschlagen\n", g_pass, g_fail);
    return g_fail ? 1 : 0;
}
