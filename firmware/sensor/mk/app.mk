# fluidi Sensor – Anwendungs-Build (TI Arm Clang, FreeRTOS, BLE5-Stack), ohne IDE.
# Grundlage: SDK examples/rtos/LP_EM_CC2340R5/ble/basic_ble/freertos/ticlang/makefile (SDK 9.23.00.27):
# gleiche Stack-/Treiber-Quellen und Optionen, ohne Menue/Display/Simple-GATT/TI-OAD; eigene Anwendung (core/,
# platform/cc23/), eigene SysConfig (CC2340R5RGE, kein LaunchPad), eigener Linker (Slot 0 hinter MCUboot).

APP_B   := $(BUILD)/app
EX      := $(SDK)/examples/rtos/LP_EM_CC2340R5/ble/basic_ble
BLE     := $(SDK)/source/ti/ble
MB_SRC  ?= $(SDK)/source/third_party/mcuboot
LIBOPT  := $(BLE)/stack_util/lib_opt/src

APP_SRC := \
  $(TOP)/core/fl_crypto.c $(TOP)/core/fl_proto.c $(TOP)/core/fl_settings.c $(TOP)/core/fl_meas.c \
  $(TOP)/core/fl_ringlog.c $(TOP)/core/fl_ui.c $(TOP)/core/fl_ota.c $(TOP)/core/fl_nvstore.c $(TOP)/core/fl_app.c \
  $(TOP)/platform/cc23/fl_ble.c $(TOP)/platform/cc23/fl_hw.c \
  $(MB_SRC)/boot/bootutil/src/bootutil_public.c \
  $(MB_SRC)/boot/ti/source/mcuboot_app/flash_map_backend/flash_map_backend.c \
  $(BLE)/app_util/framework/src/bleapputil_task.c $(BLE)/app_util/framework/src/bleapputil_init.c \
  $(BLE)/app_util/framework/src/bleapputil_process.c $(BLE)/app_util/framework/src/bleapputil_stack_callbacks.c \
  $(BLE)/app_util/framework/src/bleapputil_timers.c \
  $(EX)/common/Startup/osal_icall_ble.c $(EX)/common/Startup/main_freertos.c \
  $(BLE)/stack_util/lib_opt/rom_init.c \
  $(wildcard $(LIBOPT)/ctrl_opt_*.c) $(wildcard $(LIBOPT)/host_opt_*.c) \
  $(SDK)/source/ti/common/nv/crc.c $(SDK)/source/ti/common/nv/nvocmp.c \
  $(BLE)/stack_util/icall/app/src/icall.c $(BLE)/stack_util/icall/app/src/icall_user_config.c \
  $(BLE)/stack_util/icall/app/src/icall_POSIX.c \
  $(BLE)/app_util/config/src/ble_user_config.c $(BLE)/app_util/config/src/hci_supported_cmd.c \
  $(BLE)/app_util/common/src/util.c \
  $(BLE)/stack_util/health_toolkit/src/debugInfo.c $(BLE)/stack_util/health_toolkit/src/ble_sys_stat.c

APP_SYSCFG_C := ti_ble_config.c ti_devices_config.c ti_drivers_config.c ti_freertos_config.c \
                ti_freertos_portable_config.c ti_radio_config.c
APP_OBJS := $(addprefix $(APP_B)/obj/,$(addsuffix .obj,$(basename $(notdir $(APP_SRC) $(APP_SYSCFG_C)))))

HWREV_DEF := -DFLUIDI_HW_REV=$(if $(filter A,$(HW_REV)),0x0A,0x0B)

APP_CFLAGS := -I$(APP_B) -I$(TOP)/core -I$(TOP)/platform/cc23 -I$(TOP)/config -I$(MB_B) \
  @$(APP_B)/ti_utils_build_compiler.opt $(HWREV_DEF) \
  -DICALL_NO_APP_EVENTS -mthumb -mlittle-endian -std=c99 -ffunction-sections -fdata-sections -g -Oz -Wall \
  "-I$(SDK)/source" "-I$(SDK)/source/ti" "-I$(SDK)/source/ti/common/cc26xx" \
  "@$(SDK)/source/ti/ble/stack_util/config/build_components.opt" \
  "@$(SDK)/source/ti/ble/stack_util/config/factory_config.opt" \
  "-I$(SDK)/source/third_party/mbedtls/include" "-I$(SDK)/source/third_party/mbedtls/ti" \
  -DMBEDTLS_CONFIG_FILE=\"configs/config-hsm.h\" -DMBEDTLS_PSA_CRYPTO_CONFIG_FILE=\"configs/config-psa-crypto-hsm.h\" \
  "-I$(MB_SRC)/boot/bootutil/include" "-I$(MB_SRC)/boot/bootutil/src" "-I$(MB_SRC)/boot/ti/source/mcuboot_app" \
  "-I$(SDK)/source/ti/common/cc26xx/flash_interface" \
  -DNVOCMP_NVPAGES=2 -DNVOCMP_POSIX_MUTEX -DNVOCMP_NWSAMEITEM=1 \
  "-I$(SDK)/source/ti/drivers/rcl" "-I$(SDK)/source/ti/posix/ticlang" -DFREERTOS \
  "-I$(SDK)/kernel/freertos" "-I$(SDK)/source/third_party/freertos/include" \
  "-I$(SDK)/source/third_party/freertos/portable/GCC/ARM_CM0" \
  -mcpu=cortex-m0plus -march=thumbv6m -mfloat-abi=soft -gdwarf-3

APP_LFLAGS := "-Wl,-i$(APP_B)" -Wl,--diag_wrap=off -Wl,--display_error_number -Wl,-x -Wl,-c \
  "-L$(SDK)/source" $(APP_B)/ti_utils_build_linker.cmd.genlibs \
  $(TOP)/linker/fluidi_app.cmd "-Wl,-m,$(APP_B)/fluidi_sensor.map" -Wl,--rom_model -Wl,--warn_sections \
  "-L$(TICLANG_ARMCOMPILER)/lib" -llibc.a

$(APP_B)/.syscfg: $(TOP)/syscfg/fluidi_sensor.syscfg
	@mkdir -p $(APP_B)/obj
	@echo "[app] SysConfig"
	$(V)$(SYSCFG_STUB) --output $(APP_B) $< > $(APP_B)/syscfg.log 2>&1 || (cat $(APP_B)/syscfg.log; false)
	@touch $@

APP_HDRS := $(wildcard $(TOP)/core/*.h $(TOP)/platform/cc23/*.h $(TOP)/config/*.h)

define APP_RULE
$(APP_B)/obj/$(basename $(notdir $(1))).obj: $(1) $(APP_B)/.syscfg $(MB_B)/.syscfg $(APP_HDRS)
	@echo "[app] CC $$(notdir $$<)"
	$(V)$(CC) $(APP_CFLAGS) -c $$< -o $$@
endef
$(foreach s,$(APP_SRC),$(eval $(call APP_RULE,$(s))))
$(foreach s,$(APP_SYSCFG_C),$(eval $(call APP_RULE,$(APP_B)/$(s))))
$(addprefix $(APP_B)/,$(APP_SYSCFG_C)): $(APP_B)/.syscfg

$(APP_B)/fluidi_sensor.out: $(APP_OBJS) $(TOP)/linker/fluidi_app.cmd
	@echo "[app] LD $@"
	$(V)$(CC) -Wl,-u,_c_int00 $(APP_OBJS) $(APP_LFLAGS) -o $@ > $(APP_B)/link.log 2>&1 || (cat $(APP_B)/link.log; false)
	@grep -i "warning" $(APP_B)/link.log || true
