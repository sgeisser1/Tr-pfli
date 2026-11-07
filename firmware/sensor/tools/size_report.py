#!/usr/bin/env python3
"""fluidi – Groessenbericht: MCUboot und Anwendung gegen die Flash-Aufteilung (config/fluidi_flash_layout.h)."""
import argparse
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def layout():
    d = {}
    for m in re.finditer(r"#define\s+(FL_\w+)\s+(0x[0-9A-Fa-f]+)u", open(os.path.join(HERE, "..", "config", "fluidi_flash_layout.h")).read()):
        d[m.group(1)] = int(m.group(2), 16)
    return d


def map_mem(path):
    """MEMORY CONFIGURATION aus TI-Linker-Map: name -> (origin, length, used)"""
    out, on = {}, False
    for line in open(path):
        if "MEMORY CONFIGURATION" in line:
            on = True
            continue
        if on and line.strip().startswith("SEGMENT ALLOCATION"):
            break
        m = re.match(r"\s+(\S+)\s+([0-9a-f]{8})\s+([0-9a-f]{8})\s+([0-9a-f]{8})", line)
        if on and m:
            out[m.group(1)] = tuple(int(x, 16) for x in m.group(2, 3, 4))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mcuboot-map", required=True)
    ap.add_argument("--app-map", required=True)
    ap.add_argument("--signed", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    L = layout()
    mb, app = map_mem(a.mcuboot_map), map_mem(a.app_map)
    signed = os.path.getsize(a.signed)
    mb_used = mb["FLASH"][2]
    app_used = app["APP_SLOT"][2]
    ram = app["SRAM"]
    sec = L["FL_FLASH_SECTOR"]
    # Swap-using-Move: Slot 0 muss 1 Sektor groesser sein; Bildgroesse <= Slot 1 - Trailer
    lines = [
        "fluidi Sensor-Firmware – Groessenbericht (aus Linker-Maps, %s)" % os.path.basename(a.signed),
        "",
        "| Bereich | Start | Groesse | belegt | frei | Anteil |",
        "|---|---|---|---|---|---|",
        "| MCUboot (ohne BIMINFO-Sektor) | %#07x | %#07x | %d B | %d B | %.0f %% |" % (
            L["FL_MCUBOOT_BASE"], L["FL_MCUBOOT_SIZE"] - sec, mb_used, L["FL_MCUBOOT_SIZE"] - sec - mb_used,
            100.0 * mb_used / (L["FL_MCUBOOT_SIZE"] - sec)),
        "| Slot 0 (Anwendung, Code ab +0x100) | %#07x | %#07x | %d B Code | %d B | %.0f %% |" % (
            L["FL_SLOT0_BASE"], L["FL_SLOT0_SIZE"], app_used, app["APP_SLOT"][1] - app_used,
            100.0 * app_used / app["APP_SLOT"][1]),
        "| Slot 1 (OTA-Ziel) – signiertes Image | %#07x | %#07x | %d B | %d B | %.0f %% |" % (
            L["FL_SLOT1_BASE"], L["FL_SLOT1_SIZE"], signed, L["FL_SLOT1_SIZE"] - signed, 100.0 * signed / L["FL_SLOT1_SIZE"]),
        "| BLE-Stack-NV | %#07x | %#07x | – | – | – |" % (L["FL_BLENV_BASE"], L["FL_BLENV_SIZE"]),
        "| fluidi-NV | %#07x | %#07x | – | – | – |" % (L["FL_NV_BASE"], L["FL_NV_SIZE"]),
        "| Ringspeicher | %#07x | %#07x | – | – | – |" % (L["FL_LOG_BASE"], L["FL_LOG_SIZE"]),
        "| RAM | %#010x | %#07x | %d B | %d B | %.0f %% |" % (ram[0], ram[1], ram[2], ram[1] - ram[2], 100.0 * ram[2] / ram[1]),
        "",
        "Pruefungen:",
    ]
    ok = True
    checks = [
        ("MCUboot passt vor BIMINFO", mb_used <= L["FL_MCUBOOT_SIZE"] - sec),
        ("Anwendung passt in Slot 0 (inkl. Kopf, Trailer-Reserve)", app_used <= app["APP_SLOT"][1]),
        ("signiertes Image passt in Slot 1 (Swap-using-Move)", signed <= L["FL_SLOT1_SIZE"] - 2 * sec),
        ("Slot 0 = Slot 1 + 1 Sektor (Swap-using-Move)", L["FL_SLOT0_SIZE"] == L["FL_SLOT1_SIZE"] + sec),
        ("Bereiche luckenlos bis 512 kB", L["FL_RESERVE_BASE"] + L["FL_RESERVE_SIZE"] == L["FL_FLASH_SIZE"]),
        ("RAM-Reserve >= 2 kB", ram[1] - ram[2] >= 2048),
    ]
    for name, res in checks:
        lines.append("  [%s] %s" % ("ok" if res else "FEHLER", name))
        ok &= res
    txt = "\n".join(lines) + "\n"
    open(a.out, "w").write(txt)
    print(txt)
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
