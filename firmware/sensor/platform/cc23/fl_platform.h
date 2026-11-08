/* fluidi – CC2340-Plattform: interne Schnittstellen zwischen fl_ble.c und fl_hw.c */
#ifndef FL_PLATFORM_H
#define FL_PLATFORM_H
#include <stdint.h>

void fl_platform_early_init(void);       /* Pins in Ruhezustand (FW-6, FW-8), Treiber-Init */
void fl_platform_start_app(void);        /* fl_app_init + erster Zeitplan (BLEAppUtil-Kontext) */
void fl_platform_reschedule(void);       /* fl_app_process ausfuehren und Weckzeit neu setzen */
void fl_platform_fatal(uint8_t code);
/* O-5: Ausnahmen (Vektortabelle), Asserts und Stackueberlauf (fl_assert.c): FL_RET_FAULT setzen, FL_RET_PLANNED
 * loeschen, sofort Systemreset; kein Flash, kein Stack (fl_hw.c, tools/check_fault_vectors.py) */
void fl_fault_handler(void) __attribute__((noreturn));
void fl_platform_conn_vbat_reset(void);
void fl_platform_conn_vbat_sample(void);

#endif
