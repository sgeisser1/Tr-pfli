/*
 * fluidi – TESTFIRMWARE (nur Build `make TESTFW=n`, n = 1..4; NIE ausliefern).
 * Spezifikation: docs/reviews/phase5_testplan_prototyp.md Anhang A (EP-15), Anleitung docs/manuals/TESTFIRMWARE.md.
 *
 *   TF-1  Watchdog-Test:     5 x kurz -> Endlosschleife ohne Watchdog-Bedienung (PT5.12, T-W1, REQ-FW-07)
 *   TF-2  Reset-Schleife:    5 x kurz -> fataler Fehler ueber den Serien-Pfad, wiederholt bei jedem Start bis zur
 *                            Serienreaktion (Abschaltung nach 3 abnormalen Neustarts, F-W3); 7 x kurz: fataler Fehler
 *                            VOR der ersten Lastmessung (N-2: Soll 0 Flash-Schreibvorgaenge); 9 x kurz: echter
 *                            HardFault (Serien-Ausnahmebehandlung) (PT11.07, ST-F6, PP-11)
 *   TF-3  SENS_PWR dauernd high, TMP1075N alle 60 s lesen, Ergebnis + I2C-Fehlerzaehler als Datensatz im
 *         Ringspeicher (PT11.19, ST-W4); sonst Normalbetrieb
 *   TF-4  Diagnose-Anhang in GET_DIAG (in ALLEN Testvarianten enthalten; TESTFW=4 = nur Diagnose)
 *
 * Gemeinsam: Geraetename `fl-tf<n>-XXXX`, Startsignal Rot/Gruen abwechselnd 3 x vor L11, GET_INFO-Anhang "TF",
 * Build-Nummer 9<n><bb> (Makefile), nur DEV-Schluessel (Makefile bricht sonst ab).
 *
 * Diese Datei ist ohne FLUIDI_TESTFW leer: die Produktfirmware enthaelt keine Testfunktion.
 */
#ifndef FL_TESTFW_H
#define FL_TESTFW_H
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include "fl_proto.h"

#ifndef FLUIDI_TESTFW
#define FLUIDI_TESTFW 0
#endif

#if FLUIDI_TESTFW
#if FLUIDI_TESTFW < 1 || FLUIDI_TESTFW > 4
#error "FLUIDI_TESTFW muss 1..4 sein"
#endif

#define FL_TF_FMT              1u
#define FL_TF_SEQ_GAP_MS       2000u     /* max. Abstand zweier kurzer Druecke in einer Sequenz (ANNAHME) */
#define FL_TF_SEQ_PRIMARY      5u        /* Anhang A: "z. B. 5 x kurz" */
#define FL_TF_SEQ_EARLY        7u        /* TF-2: fataler Fehler vor der ersten Lastmessung */
#define FL_TF_SEQ_HARDFAULT    9u        /* TF-2: echter HardFault */
#define FL_TF3_PERIOD_MS       60000u    /* Anhang A TF-3: alle 60 s */
#define FL_TF_SAVE_PERIOD_MS   (60u * 60000u)  /* Testzaehler stuendlich sichern */
#define FL_CAUSE_TF3           0x83u     /* Datensatz-`cause` nur in TF-3 (PROTOCOL 5.6 kennt 0..5; Gateway speichert
                                          * unbekannte Werte unveraendert, model.py zeigt sie als "manual") */

/* Retention-Register PMCTL.AONRSTA1: Bits 0..6 und 13 belegt fl_app.h (FL_RET_*, Bit 13 = FL_RET_FAULT, O-5),
 * 18 bit gesamt (SDK hw_pmctl.h: PMCTL_AONRSTA1_FLAG_M = 0x0003FFFF). TF-2 nutzt Bits 7..12 und 14..17; sie
 * ueberleben Reset und Shutdown, nicht Power-on (TRM 8.4.2). Geloescht beim Start nach Pin-Wecken/Power-on (= Testende). */
#define FL_TF_RET_MODE_SHIFT   7u        /* 0 aus, 1 fatal spaet, 2 fatal frueh (vor Lastmessung), 3 HardFault */
#define FL_TF_RET_MODE_MASK    (0x3u << 7)
#define FL_TF_RET_MAX_SHIFT    9u        /* max. Flash-Operationen in einem Schleifenzyklus (gesaettigt 15) */
#define FL_TF_RET_MAX_SAT      15u
#define FL_TF_RET_MAX_MASK     (0xFu << 9)
#define FL_TF_RET_CYC_SHIFT    14u       /* fatale Neustarts seit Ausloesen inkl. Ausloeser (gesaettigt 3) */
#define FL_TF_RET_CYC_MASK     (0x3u << 14)
#define FL_TF_RET_SD_SHIFT     16u       /* Flash-Operationen im Start, der abgeschaltet hat (Soll 0, gesaettigt 3) */
#define FL_TF_RET_SD_MASK      (0x3u << 16)
#define FL_TF_RET_ALL          (FL_TF_RET_MODE_MASK | FL_TF_RET_MAX_MASK | FL_TF_RET_CYC_MASK | FL_TF_RET_SD_MASK)

enum { FL_TF2_OFF = 0, FL_TF2_LATE = 1, FL_TF2_EARLY = 2, FL_TF2_HARDFAULT = 3 };
enum { FL_TF_PT_EARLY = 1, FL_TF_PT_LATE = 2 };
enum { FL_TF_FATAL_SERIES = 0, FL_TF_FATAL_HARDFAULT = 1 };

/* nichtfluechtig (NV-id FL_NV_TF = 6; die Serienfirmware ignoriert die id) */
typedef struct {
    uint8_t  fmt, variant, tf2_mode, tf2_cycles;
    uint8_t  tf2_max_ops, tf2_sd_ops, tf3_stage, pad;
    uint16_t tf1_trig, tf2_trig, tf2_done, vdd_min_ever;
    uint32_t tf3_reads, tf3_err;
    int16_t  tf3_last, tf3_min, tf3_max, pad2;
} fl_tf_nv_t;

#define FL_NV_TF               6u
#define FL_TF_INFO_TAIL_LEN    4u
#define FL_TF_DIAG_TAIL_LEN    68u

/* Aufrufe aus core/fl_app.c (nur mit FLUIDI_TESTFW) */
uint32_t fl_tf_boot(uint32_t ret_at_boot, uint8_t reset_reason);   /* -> TF-Bits, die im Retention-Register bleiben */
uint32_t fl_tf_shutdown_boot(uint32_t newret);                     /* Start endet in Abschaltung: Flash-Ops merken */
bool     fl_tf_point(uint8_t where);                               /* TF-2-Ausloesepunkt im Start; true = Neustart */
void     fl_tf_started(uint8_t l11_pattern);                       /* Ende Start: Startsignal, danach L11 */
bool     fl_tf_led_followup(uint32_t now);                         /* true = neues Muster gestartet */
void     fl_tf_on_short(uint32_t now);
void     fl_tf_vdd(uint16_t mv);
void     fl_tf_ready(void);                                        /* erste bestandene Lastmessung (N-2) */
bool     fl_tf_process(uint32_t now, uint32_t *deadline);          /* true = *deadline (absolut, ms) gilt */
size_t   fl_tf_info_tail(uint8_t *o);
size_t   fl_tf_diag_tail(uint8_t *o);

/* aus core/fl_app.c fuer das Testmodul */
bool     fl_app_nv_allowed(void);
int      fl_app_tf_log(fl_record_t *rec);

/* fuer Host-Tests */
const fl_tf_nv_t *fl_tf_nv(void);
uint32_t fl_tf_ops_boot(void);

#endif /* FLUIDI_TESTFW */
#endif
