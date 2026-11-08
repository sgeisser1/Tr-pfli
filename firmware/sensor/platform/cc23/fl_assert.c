/*
 * fluidi – Assert- und Stackueberlauf-Behandlung (O-5 Folge, 2026-11-09).
 *
 * Ersetzt AssertHandler und vApplicationStackOverflowHook aus SDK 9.23.00.27
 * examples/rtos/LP_EM_CC2340R5/ble/basic_ble/common/Startup/main_freertos.c (Z. 157-161 und 199-274): dort endet
 * JEDE Ursache (out of memory, internal error, ICall abort/timeout, wrong API call, stack overflow, RNG noise,
 * default) in HAL_ASSERT_SPINLOCK (SDK ti/ble/stack_util/health_toolkit/assert.h Z. 76: volatile-Schleife) ->
 * Neustart erst durch den Watchdog nach bis zu 10 min, Grund "watchdog", CPU die ganze Zeit aktiv.
 *
 * Neu: jede Ursache -> fl_fault_handler (platform/cc23/fl_hw.c): Retention-Bit FL_RET_FAULT, FL_RET_PLANNED loeschen,
 * sofort Systemreset; naechster Start meldet reset_reason 5 (hardfault) und zaehlt abnormal (F-W3).
 * Ursache/Subursache werden nicht gespeichert (kein freies Retention-Bit, kein Flash im Fehlerpfad).
 *
 * Aufrufwege (SDK-Quelltext): AssertHandler wird in fl_main.c::main per halAssertCback und RegisterAssertCback
 * eingetragen (ble_user_config.c Z. 358-371); der Stack ruft ihn ueber halAssertHandlerExt (health_toolkit/src/
 * assert.c Z. 194-217) bzw. appAssertCback (icall_user_config.c Z. 61-65, ohne EXT_HAL_ASSERT). FreeRTOS ruft
 * vApplicationStackOverflowHook bei configCHECK_FOR_STACK_OVERFLOW = 2 (build/app/FreeRTOSConfig.h); diese starke
 * Definition ersetzt auch die schwache Spin-Variante in kernel/freertos/dpl/AppHooks_freertos.c Z. 46-53.
 *
 * Host-Test: tests/test_main.c (test_assert) bindet diese Datei mit FL_HOST_TEST ein.
 */
#include <stdint.h>
#include "fl_platform.h"
#ifdef FL_HOST_TEST
typedef void *TaskHandle_t;
#else
#include <FreeRTOS.h>
#include <task.h>
#endif

void AssertHandler(uint8_t assertCause, uint8_t assertSubcause);
void vApplicationStackOverflowHook(TaskHandle_t pxTask, char *pcTaskName);

void AssertHandler(uint8_t assertCause, uint8_t assertSubcause)
{
    (void)assertCause; (void)assertSubcause;
    fl_fault_handler();                      /* kehrt nicht zurueck */
}

void vApplicationStackOverflowHook(TaskHandle_t pxTask, char *pcTaskName)
{
    (void)pxTask; (void)pcTaskName;
    fl_fault_handler();                      /* kehrt nicht zurueck */
}
