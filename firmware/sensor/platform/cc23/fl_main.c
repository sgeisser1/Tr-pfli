/******************************************************************************

 @file  main_freertos.c

 @brief main entry of the BLE stack sample application.

 Group: WCS, BTS
 Target Device: cc23xx

 ******************************************************************************
 
 Copyright (c) 2013-2026, Texas Instruments Incorporated
 All rights reserved.

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions
 are met:

 *  Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

 *  Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

 *  Neither the name of Texas Instruments Incorporated nor the names of
    its contributors may be used to endorse or promote products derived
    from this software without specific prior written permission.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
 OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
 OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

 ******************************************************************************
 
 
 *****************************************************************************/

/*
 * fluidi-Aenderung (O-5 Folge, 2026-11-09): Kopie von SDK 9.23.00.27
 * examples/rtos/LP_EM_CC2340R5/ble/basic_ble/common/Startup/main_freertos.c bis vor vApplicationStackOverflowHook
 * (Z. 1-147 unveraendert, nur dieser Kommentar ergaenzt). vApplicationStackOverflowHook und AssertHandler stehen in
 * platform/cc23/fl_assert.c: statt HAL_ASSERT_SPINLOCK (SDK health_toolkit/assert.h Z. 76, Endlosschleife bis
 * Watchdog 10 min) -> fl_fault_handler (Retention-Bit FL_RET_FAULT, sofortiger Systemreset, Grund hardfault).
 */

/*******************************************************************************
 * INCLUDES
 */

/* RTOS header files */
#include <FreeRTOS.h>
#include <stdint.h>
#include <task.h>
#ifdef __ICCARM__
    #include <DLib_Threads.h>
#endif
#include <ti/drivers/Power.h>
#include <ti/devices/DeviceFamily.h>

#include "ti/ble/stack_util/icall/app/icall.h"
#include "ti/ble/stack_util/health_toolkit/assert.h"
#include "ti/ble/stack_util/bcomdef.h"

#ifndef USE_DEFAULT_USER_CFG
#include "ti/ble/app_util/config/ble_user_config.h"
// BLE user defined configuration
icall_userCfg_t user0Cfg = BLE_USER_CFG;
#endif // USE_DEFAULT_USER_CFG

#ifdef MS_OAD
#include "ti/ble/profiles/oad/ms_oad_profile.h"
#endif


/*******************************************************************************
 * MACROS
 */

/*******************************************************************************
 * CONSTANTS
 */

/*******************************************************************************
 * TYPEDEFS
 */

/*******************************************************************************
 * LOCAL VARIABLES
 */

/*******************************************************************************
 * GLOBAL VARIABLES
 */

/*******************************************************************************
 * EXTERNS
 */
extern void appMain(void);
extern void AssertHandler(uint8 assertCause, uint8 assertSubcause);

/*******************************************************************************
 * @fn          Main
 *
 * @brief       Application Main
 *
 * input parameters
 *
 * @param       None.
 *
 * output parameters
 *
 * @param       None.
 *
 * @return      None.
 */
int main()
{
  /* Register Application callback to trap asserts raised in the Stack */
  halAssertCback = AssertHandler;
  RegisterAssertCback(AssertHandler);

  Board_init();

  /* Update User Configuration of the stack */
  user0Cfg.appServiceInfo->timerTickPeriod = ICall_getTickPeriod();
  user0Cfg.appServiceInfo->timerMaxMillisecond  = ICall_getMaxMSecs();

  /* Initialize all applications tasks */
#if defined(MS_OAD)
  if (MSOAD_InitIfRequired() == false)
  {
#ifndef MS_OAD_HALF_MODE_BUILD
    appMain();
#endif
  }
#else // !defined(MS_OAD)
  appMain();
#endif

  /* Start the FreeRTOS scheduler */
  vTaskStartScheduler();

  return 0;

}

/* vApplicationStackOverflowHook, AssertHandler: platform/cc23/fl_assert.c */
