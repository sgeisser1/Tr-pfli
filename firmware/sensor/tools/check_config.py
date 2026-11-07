#!/usr/bin/env python3
"""fluidi – Konsistenzpruefung: Flash-Aufteilung (Header <-> MCUboot-SysConfig <-> App-SysConfig <-> Linker)
und Pins (config/fluidi_board.h <-> syscfg <-> docs/interfaces/PINMAP_SENSOR.md)."""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FW = os.path.join(HERE, "..")
REPO = os.path.join(FW, "..", "..")


def rd(p):
    return open(os.path.join(FW, p)).read()


def defs(text, prefix):
    return {m.group(1): int(m.group(2), 0) for m in re.finditer(r"#define\s+(%s\w*)\s+(0x[0-9A-Fa-f]+|\d+)u?\b" % prefix, text)}


def check_layout():
    L = defs(rd("config/fluidi_flash_layout.h"), "FL_")
    mb = rd("mcuboot/mcuboot.syscfg")
    app = rd("syscfg/fluidi_sensor.syscfg")
    lk = rd("linker/fluidi_app.cmd")
    errs = []

    def mbv(name):
        m = re.search(r"mcuboot\.%s\s*=\s*(0x[0-9A-Fa-f]+)" % name, mb)
        return int(m.group(1), 16) if m else None
    for key, name in [("FL_MCUBOOT_BASE", "bootloaderBaseAddress"), ("FL_MCUBOOT_SIZE", "bootloaderSize"),
                      ("FL_SLOT0_BASE", "primaryBase1"), ("FL_SLOT0_SIZE", "primarySize1"),
                      ("FL_SLOT1_BASE", "secondaryBase1"), ("FL_SLOT1_SIZE", "secondarySize1")]:
        if mbv(name) != L[key]:
            errs.append("mcuboot.syscfg %s=%s != %s=%#x" % (name, mbv(name), key, L[key]))
    nvs = dict((m.group(1), (int(m.group(2), 16), int(m.group(3), 16))) for m in re.finditer(
        r"(\w+)\.internalFlash\.regionBase = (0x[0-9A-Fa-f]+);\s*\n\s*\1\.internalFlash\.regionSize = (0x[0-9A-Fa-f]+);", app))
    want = {"nvs": ("FL_BLENV_BASE", "FL_BLENV_SIZE"), "nvsFl": ("FL_NV_BASE", "FL_NV_SIZE"),
            "nvsLog": ("FL_LOG_BASE", "FL_LOG_SIZE"), "nvsSlot1": ("FL_SLOT1_BASE", "FL_SLOT1_SIZE")}
    for var, (b, s) in want.items():
        if nvs.get(var) != (L[b], L[s]):
            errs.append("syscfg %s = %s != %s/%s" % (var, nvs.get(var), b, s))
    ab = int(re.search(r"#define APP_BASE\s+(0x[0-9A-Fa-f]+)", lk).group(1), 16)
    asz = int(re.search(r"#define APP_SIZE\s+(0x[0-9A-Fa-f]+)", lk).group(1), 16)
    if ab != L["FL_APP_BASE"] if "FL_APP_BASE" in L else ab != L["FL_SLOT0_BASE"] + L["FL_MCUBOOT_HDR_SIZE"]:
        errs.append("Linker APP_BASE %#x falsch" % ab)
    if ab + asz > L["FL_SLOT0_BASE"] + L["FL_SLOT0_SIZE"]:
        errs.append("Linker APP_SIZE ragt ueber Slot 0")
    regions = sorted([(L[k], L[k.replace("BASE", "SIZE")], k) for k in L if k.endswith("_BASE") and k != "FL_APP_BASE"])
    for (b1, s1, k1), (b2, _, k2) in zip(regions, regions[1:]):
        if b1 + s1 > b2:
            errs.append("Ueberlappung %s/%s" % (k1, k2))
    if L["FL_SLOT0_SIZE"] != L["FL_SLOT1_SIZE"] + L["FL_FLASH_SECTOR"]:
        errs.append("Swap-using-Move: Slot 0 muss Slot 1 + 1 Sektor sein")
    return errs


def check_pins():
    B = defs(rd("config/fluidi_board.h"), "FLUIDI_DIO_")
    app = rd("syscfg/fluidi_sensor.syscfg")
    errs = []
    sda = re.search(r'sdaPin\.\$assign = "DIO(\d+)', app)
    scl = re.search(r'sclPin\.\$assign = "DIO(\d+)', app)
    if not sda or int(sda.group(1)) != B["FLUIDI_DIO_I2C_SDA"]:
        errs.append("I2C SDA syscfg != fluidi_board.h")
    if not scl or int(scl.group(1)) != B["FLUIDI_DIO_I2C_SCL"]:
        errs.append("I2C SCL syscfg != fluidi_board.h")
    pm = open(os.path.join(REPO, "docs", "interfaces", "PINMAP_SENSOR.md")).read()
    # Tabelle Kap. 1: | Pin | DIO | Netz | ... | Firmware-Name |
    table = {}
    for m in re.finditer(r"^\|\s*(\d+)\s*\|\s*DIO(\d+)\w*\s*\|\s*`([A-Z0-9_]+)`\s*\|[^|]*\|\s*`?(FLUIDI_PIN_\w+|–)`?", pm, re.M):
        table[m.group(4)] = int(m.group(2))
    mapping = {"FLUIDI_PIN_OSC_EN_N": "FLUIDI_DIO_OSC_EN_N", "FLUIDI_PIN_MEAS_CLK": "FLUIDI_DIO_MEAS_CLK",
               "FLUIDI_PIN_CREF1": "FLUIDI_DIO_CREF1", "FLUIDI_PIN_SENS_PWR": "FLUIDI_DIO_SENS_PWR",
               "FLUIDI_PIN_I2C_SDA": "FLUIDI_DIO_I2C_SDA", "FLUIDI_PIN_I2C_SCL": "FLUIDI_DIO_I2C_SCL",
               "FLUIDI_PIN_LED_R": "FLUIDI_DIO_LED_R", "FLUIDI_PIN_LED_G": "FLUIDI_DIO_LED_G",
               "FLUIDI_PIN_LED_B": "FLUIDI_DIO_LED_B", "FLUIDI_PIN_BUTTON": "FLUIDI_DIO_BUTTON"}
    for pin, d in mapping.items():
        if pin not in table:
            errs.append("PINMAP: %s nicht gefunden" % pin)
        elif d not in B:
            errs.append("fluidi_board.h: %s fehlt (Rev B)" % d)
        elif table[pin] != B[d]:
            errs.append("%s: PINMAP DIO%d != fluidi_board.h DIO%d" % (pin, table[pin], B[d]))
    return errs


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--layout", action="store_true")
    ap.add_argument("--pins", action="store_true")
    a = ap.parse_args()
    errs = (check_layout() if a.layout else []) + (check_pins() if a.pins else [])
    for e in errs:
        print("FEHLER:", e)
    print("[check] %s: %s" % ("Layout" if a.layout else "Pins", "ok" if not errs else "%d Fehler" % len(errs)))
    sys.exit(1 if errs else 0)
