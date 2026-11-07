# fluidi Sensor-Firmware – reproduzierbarer Build ohne IDE
#
#   source ~/fluidi-tools/env.sh
#   make            -> MCUboot + Anwendung + signiertes Image + Groessenbericht (build/)
#   make test       -> Host-Unit-Tests (gcc + Python, ohne Hardware)
#   make check      -> Konsistenzpruefungen (Flash-Layout, Pins) + test
#   make clean
#
# Optionen:  HW_REV=A|B (Default B, D-018)   VERSION=0.1.0  BUILD_NO=1  SEC_CNT=0
#            SIGN_KEY=<pfad>  (Default: DEV-Schluessel keys/DEV_ONLY_*.pem – NIE fuer Serie, siehe keys/README.md)
#            VERBOSE=1

TOP        := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
BUILD      ?= $(TOP)/build
HW_REV     ?= B
VERSION    ?= 0.1.0
BUILD_NO   ?= 1
SEC_CNT    ?= 0
SIGN_KEY   ?= $(TOP)/keys/DEV_ONLY_fluidi_signing_ec-p256.pem

SDK        := $(or $(SIMPLELINK_LOWPOWER_F3_SDK_INSTALL_DIR),$(FLUIDI_TI_SDK))
SIMPLELINK_LOWPOWER_F3_SDK_INSTALL_DIR := $(SDK)
ifeq ($(SDK),)
$(error TI-SDK nicht gefunden: zuerst 'source ~/fluidi-tools/env.sh')
endif
include $(SDK)/imports.mak

CC         := "$(TICLANG_ARMCOMPILER)/bin/tiarmclang"
SYSCFG_STUB := $(SYSCONFIG_TOOL) --compiler ticlang --product $(SDK)/.metadata/product.json
IMGTOOL    ?= $(or $(shell command -v imgtool 2>/dev/null),$(FLUIDI_TOOLS)/venv/bin/imgtool)
PYTHON     ?= $(or $(wildcard $(FLUIDI_TOOLS)/venv/bin/python),python3)

V := @
ifeq ($(VERBOSE),1)
V :=
endif

.PHONY: all mcuboot app sign size test check check-layout check-pins clean
all: sign size

include $(TOP)/mk/mcuboot.mk
include $(TOP)/mk/app.mk

mcuboot: $(MB_B)/mcuboot.out
app: $(APP_B)/fluidi_sensor.out

# Signiertes MCUboot-Image (Header 0x100, Swap-using-Move: --align 4 --max-sectors, Sicherheitszaehler)
SIGNED := $(BUILD)/fluidi-sensor-$(VERSION)+$(BUILD_NO).bin
sign: $(SIGNED) $(BUILD)/fluidi-sensor-factory.hex
$(SIGNED): $(APP_B)/fluidi_sensor.out $(SIGN_KEY)
	@echo "[sign] imgtool sign --version $(VERSION)+$(BUILD_NO) --security-counter $(SEC_CNT)"
	$(V)"$(TICLANG_ARMCOMPILER)/bin/tiarmobjcopy" -O binary --only-section=.resetVecs --only-section=.text \
	  --only-section=.const --only-section=.constdata --only-section=.rodata --only-section=.binit \
	  --only-section=.cinit --only-section=.pinit --only-section=.init_array --only-section=.emb_text \
	  --only-section=.TI.ramfunc \
	  $< $(APP_B)/fluidi_sensor_noheader.bin
	$(V)$(IMGTOOL) sign --header-size 0x100 --pad-header --align 4 --slot-size 0x38800 \
	  --max-sectors 113 --version $(VERSION)+$(BUILD_NO) --security-counter $(SEC_CNT) \
	  --key $(SIGN_KEY) $(APP_B)/fluidi_sensor_noheader.bin $@
	$(V)$(PYTHON) $(TOP)/tools/verify_image.py --key $(SIGN_KEY) $@
	@case "$(notdir $(SIGN_KEY))" in DEV_ONLY*) echo "[sign] WARNUNG: mit DEV-Schluessel signiert – nur Labor/Prototyp, nicht ausliefern";; esac

# Werks-Hex: MCUboot (inkl. CCFG) + signiertes, bestaetigtes Image in Slot 0 (fuer flash_sensor.py)
$(BUILD)/fluidi-sensor-factory.hex: $(SIGNED) $(MB_B)/mcuboot.out
	@echo "[factory] MCUboot + Slot0 (bestaetigt) -> $(notdir $@)"
	$(V)$(IMGTOOL) sign --header-size 0x100 --pad-header --align 4 --slot-size 0x39000 --max-sectors 114 \
	  --version $(VERSION)+$(BUILD_NO) --security-counter $(SEC_CNT) --confirm \
	  --key $(SIGN_KEY) $(APP_B)/fluidi_sensor_noheader.bin $(BUILD)/slot0_confirmed.bin
	$(V)$(PYTHON) $(TOP)/tools/make_factory_hex.py --mcuboot $(MB_B)/mcuboot.hex \
	  --slot0 $(BUILD)/slot0_confirmed.bin --slot0-base 0x6000 -o $@

size: $(SIGNED)
	$(V)$(PYTHON) $(TOP)/tools/size_report.py --mcuboot-map $(MB_B)/mcuboot.map --app-map $(APP_B)/fluidi_sensor.map \
	  --signed $(SIGNED) --out $(BUILD)/size_report.txt

test:
	$(V)$(MAKE) -C $(TOP)/tests PYTHON=$(PYTHON)

check-layout:
	$(V)$(PYTHON) $(TOP)/tools/check_config.py --layout

check-pins:
	$(V)$(PYTHON) $(TOP)/tools/check_config.py --pins

check: check-layout check-pins test

clean:
	rm -rf $(BUILD)
	$(MAKE) -C $(TOP)/tests clean
