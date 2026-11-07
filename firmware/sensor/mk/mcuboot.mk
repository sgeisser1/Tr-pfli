# fluidi Sensor – MCUboot-Build (TI Arm Clang, ohne IDE)
# Grundlage: SDK examples/nortos/LP_EM_CC2340R5/mcuboot/mcuboot/ticlang/makefile (SDK 9.23.00.27).
# Abweichungen: eigene SysConfig (Device CC2340R5RGE, Swap-using-Move, Anti-Rollback, Flash-Layout fluidi),
# eigener oeffentlicher Schluessel (aus SIGN_KEY via imgtool getpub), eigene LED-Datei (aktiv low, kein 3-s-Blinken).
# Aufruf ueber das Haupt-Makefile:  make mcuboot

MB_B     := $(BUILD)/mcuboot
MB_SRC   := $(SDK)/source/third_party/mcuboot

MB_SOURCES := \
  $(TOP)/mcuboot/fluidi_led_debug.c \
  $(MB_SRC)/boot/ti/source/mcuboot_app/mcuboot_app.c \
  $(MB_B)/fluidi_keys.c \
  $(MB_SRC)/boot/ti/source/mcuboot_app/flash_map_backend/flash_map_backend.c \
  $(SDK)/source/ti/common/flash/no_rtos/extFlash/ext_flash.c \
  $(MB_SRC)/boot/ti/source/mcuboot_app/watchdog/watchdog.c \
  $(MB_SRC)/boot/ti/source/mcuboot_app/security_cnt.c \
  $(MB_SRC)/boot/bootutil/src/boot_record.c \
  $(MB_SRC)/boot/bootutil/src/image_ed25519.c \
  $(MB_SRC)/boot/bootutil/src/image_ecdsa.c \
  $(MB_SRC)/boot/bootutil/src/bootutil_misc.c \
  $(MB_SRC)/boot/bootutil/src/image_rsa.c \
  $(MB_SRC)/boot/bootutil/src/image_validate.c \
  $(MB_SRC)/boot/bootutil/src/bootutil_public.c \
  $(MB_SRC)/boot/bootutil/src/loader.c \
  $(MB_SRC)/boot/bootutil/src/caps.c \
  $(MB_SRC)/boot/bootutil/src/swap_misc.c \
  $(MB_SRC)/boot/bootutil/src/compressed.c \
  $(MB_SRC)/boot/bootutil/src/encrypted.c \
  $(MB_SRC)/boot/bootutil/src/swap_move.c \
  $(MB_SRC)/boot/bootutil/src/fault_injection_hardening.c \
  $(MB_SRC)/boot/bootutil/src/fault_injection_hardening_delay_rng_mbedtls.c \
  $(MB_SRC)/boot/bootutil/src/swap_scratch.c \
  $(MB_SRC)/boot/bootutil/src/tlv.c \
  $(MB_SRC)/ext/mbedtls-asn1/src/asn1parse.c \
  $(MB_SRC)/ext/mbedtls-asn1/src/platform_util.c \
  $(MB_SRC)/ext/ti-crypto/sl_crypto.c \
  $(SDK)/source/third_party/lzma/C/LzmaDec.c \
  $(SDK)/source/third_party/lzma/C/Lzma2Dec.c \
  $(SDK)/source/ti/common/ecdsa_lpf3/ecdsa_lpf3.c \
  $(SDK)/source/ti/common/aes_lpf3/aes_lpf3.c \
  $(SDK)/source/ti/common/flash/no_rtos/extFlash/bsp_spi_lpf3.c \
  $(MB_B)/ti_devices_config.c

MB_OBJS := $(addprefix $(MB_B)/obj/,$(addsuffix .obj,$(basename $(notdir $(MB_SOURCES)))))

MB_CFLAGS := -I$(MB_B) -I$(TOP)/config \
  @$(MB_B)/ti_utils_build_compiler.opt \
  -Oz -DEXCLUDE_TRACE -DBOOT_LOADER \
  -DSPI_CTL0_SPO_LOW=SPI_CTL0_SPO_LO -DSPI_CTL0_SPO_HIGH=SPI_CTL0_SPO_HI \
  -std=gnu9x -ffunction-sections -fdata-sections -g -Wall \
  "-I$(SDK)/source" "-I$(SDK)/kernel/nortos" "-I$(SDK)/kernel/nortos/posix" \
  "-I$(SDK)/source/third_party/ecc/include" \
  "-I$(SDK)/source/ti/devices/cc23x0r5/driverlib" \
  "-I$(MB_SRC)/boot/bootutil/include" "-I$(MB_SRC)/boot/bootutil/src" \
  "-I$(MB_SRC)/ext" "-I$(MB_SRC)/ext/mbedtls-asn1/include" \
  "-I$(MB_SRC)/boot/ti/source/mcuboot_app" \
  "-I$(SDK)/source/third_party/lzma/C" \
  -mcpu=cortex-m0plus -march=thumbv6m -mfloat-abi=soft -mthumb -gdwarf-3

MB_LFLAGS := "-L$(SDK)/source" "-L$(SDK)/kernel/nortos" -L$(MB_B) \
  $(MB_B)/ti_utils_build_linker.cmd.genlibs \
  -lthird_party/ecc/lib/ticlang/m0p/ecc.a \
  $(SDK)/examples/nortos/LP_EM_CC2340R5/mcuboot/mcuboot/mcuboot_cc2340r5.cmd \
  "-Wl,-m,$(MB_B)/mcuboot.map" -Wl,--rom_model -Wl,--warn_sections \
  "-L$(TICLANG_ARMCOMPILER)/lib" -llibc.a

$(MB_B)/.syscfg: $(TOP)/mcuboot/mcuboot.syscfg
	@mkdir -p $(MB_B)/obj
	@echo "[mcuboot] SysConfig"
	$(V)$(SYSCFG_STUB) --output $(MB_B) $< > $(MB_B)/syscfg.log 2>&1 || (cat $(MB_B)/syscfg.log; false)
	@touch $@

# Oeffentlicher Schluessel aus dem Signierschluessel (nur der PUBLIC-Teil landet im Bootloader)
$(MB_B)/fluidi_keys.c: $(SIGN_KEY) $(MB_B)/.syscfg
	@echo "[mcuboot] oeffentlicher Schluessel aus $(notdir $(SIGN_KEY))"
	$(V)printf '/* generiert von mk/mcuboot.mk aus %s - nicht editieren */\n#include <bootutil/sign_key.h>\n#include "mcuboot_config.h"\n' "$(notdir $(SIGN_KEY))" > $@
	$(V)$(IMGTOOL) getpub -k $(SIGN_KEY) -e lang-c >> $@
	$(V)printf 'const struct bootutil_key bootutil_keys[] = { { .key = ecdsa_pub_key, .len = &ecdsa_pub_key_len } };\nconst int bootutil_key_cnt = 1;\n' >> $@

define MB_RULE
$(MB_B)/obj/$(basename $(notdir $(1))).obj: $(1) $(MB_B)/.syscfg $(TOP)/config/fluidi_board.h
	@echo "[mcuboot] CC $$(notdir $$<)"
	$(V)$(CC) $(MB_CFLAGS) -c $$< -o $$@
endef
$(foreach s,$(MB_SOURCES),$(eval $(call MB_RULE,$(s))))

$(MB_B)/mcuboot.out: $(MB_OBJS)
	@echo "[mcuboot] LD $@"
	$(V)$(CC) -Wl,-u,_c_int00 $(MB_OBJS) $(MB_LFLAGS) -o $@
	@# CCFG-Pruefsummen eintragen (wie SDK basic_ble postbuild; ROM prueft die CCFG-CRCs, TRM Kap. 8)
	$(V)$(SDK)/tools/common/crc_tool/crc_tool patch-image --elf $@ --symbol-prefix ti_utils_build_GenMap_sym_CRC_CCFG -o $@
	$(V)"$(TICLANG_ARMCOMPILER)/bin/tiarmobjcopy" -O ihex $@ $(MB_B)/mcuboot.hex
