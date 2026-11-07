/*
 * fluidi Sensor – Flash-Aufteilung CC2340R52 (512 kB, Sektor 2 kB: DS S.20 Tab. 7.11).
 * Quelle: firmware/PROTOCOL.md Kap. 6.4. MUSS mit mcuboot/mcuboot.syscfg und syscfg/fluidi_sensor.syscfg
 * uebereinstimmen; `make check-layout` prueft das automatisch (tools/check_config.py).
 */
#ifndef FLUIDI_FLASH_LAYOUT_H
#define FLUIDI_FLASH_LAYOUT_H

#define FL_FLASH_SECTOR         0x800u
#define FL_FLASH_SIZE           0x80000u

#define FL_MCUBOOT_BASE         0x00000u
#define FL_MCUBOOT_SIZE         0x06000u   /* letzter Sektor 0x05800 = BIMINFO (Sicherheitszaehler) */
#define FL_SLOT0_BASE           0x06000u   /* primaer: laufende Anwendung */
#define FL_SLOT0_SIZE           0x39000u
#define FL_SLOT1_BASE           0x3F000u   /* sekundaer: Update-Ziel */
#define FL_SLOT1_SIZE           0x38800u
#define FL_BLENV_BASE           0x77800u   /* BLE-Stack-NV (nvocmp, 2 Seiten; kein Bonding, nur Stack-intern) */
#define FL_BLENV_SIZE           0x01000u
#define FL_NV_BASE              0x78800u   /* fluidi-NV: Einstellungen/Schluessel/Zaehler (core/fl_nvstore, A/B) */
#define FL_NV_SIZE              0x01000u
#define FL_LOG_BASE             0x79800u   /* Ringspeicher Datensaetze + Zaehler + Fehlerprotokoll */
#define FL_LOG_SIZE             0x06000u
#define FL_RESERVE_BASE         0x7F800u
#define FL_RESERVE_SIZE         0x00800u

#define FL_MCUBOOT_HDR_SIZE     0x100u     /* imgtool --header-size; App-Vektortabelle bei SLOT0 + 0x100 */
#define FL_APP_BASE             (FL_SLOT0_BASE + FL_MCUBOOT_HDR_SIZE)

#endif
