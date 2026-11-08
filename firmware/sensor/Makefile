# fluidi Sensor-Firmware – reproduzierbarer Build ohne IDE
#
#   source ~/fluidi-tools/env.sh
#   make            -> MCUboot + Anwendung + signiertes Image + Groessenbericht (build/)
#   make test       -> Host-Unit-Tests (gcc + Python, ohne Hardware)
#   make check      -> Konsistenzpruefungen (Flash-Layout, Pins) + test
#   make clean
#   make TESTFW=n   -> TESTFIRMWARE TF-n (n = 1..4, Testplan Anhang A; docs/manuals/TESTFIRMWARE.md) in build-tf<n>/,
#                     nur mit DEV-Schluessel, Geraetename fl-tf<n>-XXXX, Build-Nummer 9<n><BUILD_NO 2-stellig>. NIE ausliefern.
#
# Optionen:  HW_REV=A|B (Default B, D-018)   VERSION=0.1.0  BUILD_NO=1  SEC_CNT=0
#            SIGN_KEY=<pfad>  (Default: DEV-Schluessel keys/DEV_ONLY_*.pem – NIE fuer Serie, siehe keys/README.md)
#            VERBOSE=1

TOP        := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
TESTFW     ?=
ifneq ($(TESTFW),)
ifeq ($(filter $(TESTFW),1 2 3 4),)
$(error TESTFW=$(TESTFW) ungueltig: 1, 2, 3 oder 4 (Testplan Anhang A))
endif
BUILD      ?= $(TOP)/build-tf$(TESTFW)
else
BUILD      ?= $(TOP)/build
endif
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

.PHONY: all mcuboot app sign size test check check-layout check-pins clean release
all: sign size

# Testfirmware (Anhang A): Kennung im Dateinamen und in der Build-Nummer (fw_build ist u32, PROTOCOL 5.5 ->
# Suffix "-tf<n>" als Ziffernfolge 9<n><bb>, z. B. TF-1 Build 1 = 9101); Serien-Build-Nummern bleiben < 9000.
ifneq ($(TESTFW),)
ifneq ($(shell test $(BUILD_NO) -ge 0 -a $(BUILD_NO) -le 99 2>/dev/null && echo ok),ok)
$(error TESTFW: BUILD_NO muss 0..99 sein)
endif
IMG_BUILD  := $(shell printf '9%d%02d' $(TESTFW) $(BUILD_NO))
TF_TAG     := -tf$(TESTFW)
TF_DEF     := -DFLUIDI_TESTFW=$(TESTFW)
ifeq ($(filter DEV_ONLY%,$(notdir $(SIGN_KEY))),)
$(error TESTFW: nur mit DEV-Schluessel (keys/DEV_ONLY_*.pem) signieren, nie mit dem Produktionsschluessel)
endif
else
ifneq ($(shell test $(BUILD_NO) -ge 9000 2>/dev/null && echo hi),)
$(error Serien-BUILD_NO >= 9000 ist fuer Testfirmware reserviert)
endif
IMG_BUILD  := $(BUILD_NO)
TF_TAG     :=
TF_DEF     :=
endif
include $(TOP)/mk/mcuboot.mk
include $(TOP)/mk/app.mk

HWREV_HEX  := $(if $(filter A,$(HW_REV)),0x0A,0x0B)

KEY_FP     := $(shell $(PYTHON) $(TOP)/tools/key_fingerprint.py $(SIGN_KEY) 2>/dev/null)
FACTORY    := $(BUILD)/fluidi-sensor$(TF_TAG)-factory-$(VERSION)+$(IMG_BUILD)-key$(KEY_FP).hex
IMG_TLV    := --custom-tlv 0xA0 $(HWREV_HEX)   # geschuetztes TLV hw_rev (PROTOCOL 0.2, 9.6)

mcuboot: $(MB_B)/mcuboot.out
app: $(APP_B)/fluidi_sensor.out

# Signiertes MCUboot-Image (Header 0x100, Swap-using-Move: --align 4 --max-sectors, Sicherheitszaehler)
SIGNED := $(BUILD)/fluidi-sensor$(TF_TAG)-$(VERSION)+$(IMG_BUILD).bin
sign: $(SIGNED) $(FACTORY)
$(SIGNED): $(APP_B)/fluidi_sensor.out $(SIGN_KEY)
	@echo "[sign] imgtool sign --version $(VERSION)+$(IMG_BUILD) --security-counter $(SEC_CNT)$(if $(TF_TAG),  TESTFIRMWARE TF-$(TESTFW))"
	$(V)"$(TICLANG_ARMCOMPILER)/bin/tiarmobjcopy" -O binary --only-section=.resetVecs --only-section=.text \
	  --only-section=.const --only-section=.constdata --only-section=.rodata --only-section=.binit \
	  --only-section=.cinit --only-section=.pinit --only-section=.init_array --only-section=.emb_text \
	  --only-section=.TI.ramfunc \
	  $< $(APP_B)/fluidi_sensor_noheader.bin
	$(V)$(IMGTOOL) sign --header-size 0x100 --pad-header --align 4 --slot-size 0x38800 \
	  --max-sectors 113 --version $(VERSION)+$(IMG_BUILD) --security-counter $(SEC_CNT) $(IMG_TLV) \
	  --key $(SIGN_KEY) $(APP_B)/fluidi_sensor_noheader.bin $@
	$(V)$(PYTHON) $(TOP)/tools/verify_image.py --key $(SIGN_KEY) $@
	@case "$(notdir $(SIGN_KEY))" in DEV_ONLY*) echo "[sign] WARNUNG: mit DEV-Schluessel signiert – nur Labor/Prototyp, nicht ausliefern";; esac
	$(if $(TF_TAG),@echo "[sign] TESTFIRMWARE TF-$(TESTFW) (Anhang A) – NIE ausliefern; Rueckkehr nur mit hoeherer Version (docs/manuals/TESTFIRMWARE.md)")

# Werks-Hex: MCUboot (inkl. CCFG) + signiertes, bestaetigtes Image in Slot 0 (fuer flash_sensor.py)
$(FACTORY): $(SIGNED) $(MB_B)/mcuboot.out
	@echo "[factory] MCUboot + Slot0 (bestaetigt) -> $(notdir $@)  (Schluessel-Fingerabdruck $(KEY_FP))"
	$(V)$(IMGTOOL) sign --header-size 0x100 --pad-header --align 4 --slot-size 0x39000 --max-sectors 114 \
	  --version $(VERSION)+$(IMG_BUILD) --security-counter $(SEC_CNT) $(IMG_TLV) --confirm \
	  --key $(SIGN_KEY) $(APP_B)/fluidi_sensor_noheader.bin $(BUILD)/slot0_confirmed.bin
	$(V)$(PYTHON) $(TOP)/tools/make_factory_hex.py --mcuboot $(MB_B)/mcuboot.hex \
	  --slot0 $(BUILD)/slot0_confirmed.bin --slot0-base 0x6000 -o $@

size: $(SIGNED)
	$(V)$(PYTHON) $(TOP)/tools/size_report.py --mcuboot-map $(MB_B)/mcuboot.map --app-map $(APP_B)/fluidi_sensor.map \
	  --signed $(SIGNED) --out $(BUILD)/size_report.txt

# Serienstand (F-W1): nur mit Produktionsschluessel AUSSERHALB des Repos, nie mit DEV_ONLY_*
release:
	$(if $(TESTFW),@echo "[release] ABBRUCH: TESTFW gesetzt – Testfirmware wird nie als Serie gebaut"; exit 1)
	@case "$(notdir $(SIGN_KEY))" in DEV_ONLY*) echo "[release] ABBRUCH: DEV-Schluessel – SIGN_KEY=<Produktionsschluessel> angeben"; exit 1;; esac
	@case "$(abspath $(SIGN_KEY))" in $(abspath $(TOP)/../..)/*) echo "[release] ABBRUCH: Schluessel liegt im Repository"; exit 1;; esac
	@test -f "$(SIGN_KEY)" || (echo "[release] ABBRUCH: $(SIGN_KEY) fehlt"; exit 1)
	$(V)$(MAKE) clean all check SIGN_KEY=$(abspath $(SIGN_KEY))
	@echo "[release] fertig: $(notdir $(FACTORY)) – Sperren mit: scripts/flash_sensor.py program --lock --hex <factory.hex> --expect-key-fp $(KEY_FP)"

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
