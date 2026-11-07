/*
 * fluidi – Ersatz fuer SDK source/ti/common/cc26xx/debug/led_debug.c im MCUboot-Build.
 *
 * Grund: Das SDK-Original blinkt LaunchPad-Pins DIO14/DIO15 (gibt es am QFN24 RGE nicht) aktiv-high
 * und wartet bei JEDEM Start 3 x 2 x 500 ms (= 3 s CPU aktiv, Energie). fluidi-LEDs sind aktiv-LOW
 * (PINMAP_SENSOR.md: LED_R DIO6, LED_G DIO13). Erfolg: keine LED (Energie). Fehler: Rot kurz
 * (Pulse 10 ms, Regel "Pulse <= 5..10 ms mit Pausen" aus PINMAP_SENSOR.md Kap. 3).
 */
#include <stdint.h>
#include <ti/devices/DeviceFamily.h>
#include DeviceFamily_constructPath(driverlib/gpio.h)
#include "ti/common/cc26xx/debug/led_debug.h"
#include "../config/fluidi_board.h"

uint16_t delayConstant = 4010U; /* ~1 ms je Schleife (SDK-Wert, "by experimentation") */

void delay(uint32_t delayMs)
{
    for (volatile uint32_t j = 0; j < (uint32_t)delayConstant * delayMs; j++) { }
}

static void fl_led_pulse(uint32_t dio, uint32_t on_ms, uint32_t off_ms)
{
    GPIOSetOutputEnableDio(dio, GPIO_OUTPUT_ENABLE);
    GPIOClearDio(dio);                  /* aktiv low: an */
    delay(on_ms);
    GPIOSetDio(dio);                    /* aus */
    delay(off_ms);
}

void blinkLed(uint32_t led, uint8_t nBlinks, uint32_t periodMs)
{
    (void)periodMs;
    if (led == RED_LED) {
        /* Fehler (kein gueltiges Image): max. 3 kurze rote Pulse je Aufruf */
        for (uint8_t i = 0; i < nBlinks && i < 3; i++) {
            fl_led_pulse(FLUIDI_DIO_LED_R, 10, 150);
        }
    }
    /* GREEN_LED (Erfolg): bewusst keine Anzeige */
}

void lightRedLed(void)   { GPIOSetOutputEnableDio(FLUIDI_DIO_LED_R, GPIO_OUTPUT_ENABLE); GPIOClearDio(FLUIDI_DIO_LED_R); }
void lightGreenLed(void) { }
void powerUpGpio(void)   { }
void powerDownGpio(void) { }
