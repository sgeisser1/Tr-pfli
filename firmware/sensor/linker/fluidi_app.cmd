/*
 * fluidi Sensor – Linker-Datei Anwendung (TI Arm Clang). Grundlage: SDK basic_ble/freertos/ticlang/cc2340_freertos.cmd.
 * Anwendung in MCUboot-Slot 0: Kopf 0x100 bei 0x06000 (imgtool --header-size 0x100), Vektortabelle bei 0x06100.
 * Am Slot-Ende bleibt Platz fuer den MCUboot-Trailer (Swap-using-Move). Werte: config/fluidi_flash_layout.h
 * (`make check-layout` prueft die Uebereinstimmung).
 */
#include "ti_utils_build_linker.cmd.genmap"

--stack_size=1024
--heap_size=0
--entry_point resetISR
--retain "*(.resetVecs)"
--diag_suppress=10063,16011,16012
--diag_remark=10068

#define APP_BASE      0x00006100
#define APP_SIZE      0x00037F00   /* Slot 0 0x39000 - Kopf 0x100 - Trailer-Reserve 0x1000 */
#define RAM_BASE      ti_utils_build_GenMap_RAM0_BASE
#define RAM_SIZE      ti_utils_build_GenMap_RAM0_SIZE
#define S2RRAM_BASE   ti_utils_build_GenMap_S2RRAM_BASE
#define S2RRAM_SIZE   ti_utils_build_GenMap_S2RRAM_SIZE
#define CCFG_BASE     ti_utils_build_GenMap_CCFG_BASE
#define CCFG_SIZE     ti_utils_build_GenMap_CCFG_SIZE

__STACK_TOP = __stack + __STACK_SIZE;

MEMORY
{
    APP_SLOT (RX) : origin = APP_BASE, length = APP_SIZE
    SRAM (RWX)    : origin = RAM_BASE, length = RAM_SIZE
    S2RRAM (RW)   : origin = S2RRAM_BASE, length = S2RRAM_SIZE
    /* CCFG gehoert dem MCUboot-Build; die Anwendung bringt ihre CCFG nur zum Linken mit, sie wird beim
     * Signieren NICHT uebernommen (Makefile: objcopy ohne .ccfg). */
    CCFG (R)      : origin = CCFG_BASE, length = CCFG_SIZE
    LOG_DATA (R)  : origin = 0x90000000, length = 0x40000
    LOG_PTR  (R)  : origin = 0x94000008, length = 0x40000
}

SECTIONS
{
    .resetVecs      :   > APP_BASE
    .text           :   > APP_SLOT
    .const          :   > APP_SLOT
    .constdata      :   > APP_SLOT
    .rodata         :   > APP_SLOT
    .binit          :   > APP_SLOT
    .cinit          :   > APP_SLOT
    .pinit          :   > APP_SLOT
    .init_array     :   > APP_SLOT
    .emb_text       :   > APP_SLOT
    .TI.ramfunc     : {} load = APP_SLOT, run = SRAM, table(BINIT)
    .ccfg           :   > CCFG
    .ramVecs        :   > SRAM, type = NOLOAD, ALIGN(256)
    .data           :   > SRAM
    .bss            :   > SRAM
    .sysmem         :   > SRAM
    .stack          :   > SRAM (HIGH)
    .nonretenvar    :   > SRAM
    .s2rram         :   > S2RRAM, type = NOINIT
    .log_data       :   > LOG_DATA, type = COPY
    .log_ptr        : { *(.log_ptr*) } > LOG_PTR align 4, type = COPY
}
