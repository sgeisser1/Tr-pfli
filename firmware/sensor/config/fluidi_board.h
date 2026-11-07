/*
 * fluidi Sensor – ZENTRALE Pin- und Board-Konfiguration (einzige Stelle fuer Pinnummern).
 *
 * Quelle: docs/interfaces/PINMAP_SENSOR.md **Rev B** (2026-11-07, final fuer das Layout), Regeln FW-1..FW-10,
 * und DECISIONS.md D-018 (Messkette D3). Rev B: DIO11 = OSC_EN_N (Gate P-FET Q2 AO3401A, R13 100 k Pull-up,
 * low = Oszillator + Teiler EIN), DIO24 = MEAS_CLK = f_osc/8, DIO12 SENS_PWR nur noch TMP1075N, Cref2 entfaellt.
 * Rev A bleibt per HW_REV=A baubar (nur fuer Altmuster).
 *
 * Aenderungen der Pinbelegung NUR hier nachziehen (plus I2C-Pins in syscfg/fluidi_sensor.syscfg,
 * die `make check-pins` gegen diese Datei prueft).
 *
 * Diese Datei ist plattformneutral (nur #define), damit MCUboot, Anwendung und Host-Tests sie nutzen koennen.
 */
#ifndef FLUIDI_BOARD_H
#define FLUIDI_BOARD_H

/* ---- Hardware-Revision (Build-Option HW_REV=A|B, Default B) ---- */
#define FLUIDI_HW_REV_A 0x0A
#define FLUIDI_HW_REV_B 0x0B
#ifndef FLUIDI_HW_REV
#define FLUIDI_HW_REV FLUIDI_HW_REV_B
#endif

/* ---- DIO-Nummern (CC2340R52 QFN24 RGE; Pinnummer des Gehaeuses im Kommentar) ---- */
#define FLUIDI_DIO_LED_R        6   /* Pin 19, aktiv LOW, ROM-Bootloader UART TX (TRM S.464) */
#define FLUIDI_DIO_LED_G        13  /* Pin 6,  aktiv LOW */
#define FLUIDI_DIO_LED_B        20  /* Pin 9,  aktiv LOW, ROM-Bootloader UART RX */
#define FLUIDI_DIO_BUTTON       21  /* Pin 10, aktiv LOW, interner Pull-up, Bootloader-Trigger (TRM S.465) */
#define FLUIDI_DIO_SENS_PWR     12  /* Pin 5,  High-Drive, Speisung TMP1075N + C24 + I2C-Pull-ups R4/R5 (Rev A auch Oszillator) */
#define FLUIDI_DIO_MEAS_CLK     24  /* Pin 12, MEAS_CLK = f_osc/8 (Rev B), 0.59-4.51 MHz (SPICE) -> LGPT3 C0 (T3C0, Mux 3) */
#define FLUIDI_DIO_CREF1        8   /* Pin 3,  low = Cref1 22 pF wirkt; sonst hochohmig, Puffer aus */
#define FLUIDI_DIO_I2C_SDA      16  /* Pin 7,  I2C0 SDA (nach Reset SWDIO + Pull-up -> frueh umkonfigurieren) */
#define FLUIDI_DIO_I2C_SCL      17  /* Pin 8,  I2C0 SCL (nach Reset SWDCK + Pull-down) */
#define FLUIDI_DIO_X32P         3   /* Pin 14, LFXT */
#define FLUIDI_DIO_X32N         4   /* Pin 15, LFXT */

#if FLUIDI_HW_REV == FLUIDI_HW_REV_A
#define FLUIDI_DIO_CREF2        11  /* Pin 4, Rev A: Cref2 100 pF (Salzdiagnose f2) */
#define FLUIDI_HAS_CREF2        1
#define FLUIDI_HAS_OSC_FET      0
#define FLUIDI_OSC_DIVIDER      1   /* Rev A: 2-6 MHz direkt am Timer */
#else
#define FLUIDI_DIO_OSC_EN_N     11  /* Pin 4, Rev B: Gate P-FET Q2, aktiv LOW (PINMAP Rev B Kap. 1) */
#define FLUIDI_HAS_CREF2        0
#define FLUIDI_HAS_OSC_FET      1
#define FLUIDI_OSC_DIVIDER      8   /* Rev B: 3 x SN74LVC1G80 = /8 (MESSKETTE_SALZ.md Kap. 5) */
#endif

/* ---- Pin-Multiplexer-Werte (DS TI_CC2340R5_Datasheet_SWRS272F.pdf Tab. 6-1, PINMAP Kap. 1/3) ---- */
#define FLUIDI_MUX_MEAS_CLK_T3C0 3  /* DIO24 Mux 3 = LGPT3 C0 */

/* ---- Peripherie ---- */
#define FLUIDI_TMP1075_I2C_ADDR 0x48 /* TMP1075N (SOT-563, nur A0): A0 = GND (U3 Pin 4, Netzliste Rev B),
                                        TI_TMP1075_Datasheet_SBOS854F.pdf S.14 Tab. 7-3 */

/* ---- Zeiten (ANNAHME, am Muster messen -> PROTOTYP-PRUEFUNG) ---- */
#define FLUIDI_SENS_PWR_SETTLE_US   1000u  /* PINMAP Rev B DIO12: >= 1 ms nach SENS_PWR ein */
#define FLUIDI_TMP_CONV_MS          15u    /* FW-1: TMP1075N One-Shot tCONV 10-15 ms (SBOS854F S.7 Tab. 6.6) */
#define FLUIDI_OSC_SETTLE_US        50u    /* FW-2: >= 50 us nach DIO11 low (ANNAHME, am Muster messen) */
/* FW-2: Messkette nur in Bursts: Kette an <= 0.6 ms, danach >= 30 ms Pause, hoechstens 4 Bursts je Messung */
#define FLUIDI_BURST_MAX_US         600u
#define FLUIDI_BURST_PAUSE_MS       30u
#define FLUIDI_BURST_MAX            4u
#define FLUIDI_BURST_CFG_US         250u   /* Abtastzeit je Konfiguration (f0, f1) im Burst; 2 x 250 + 50 < 600 */

#endif /* FLUIDI_BOARD_H */
