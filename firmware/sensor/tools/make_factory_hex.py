#!/usr/bin/env python3
"""fluidi – Werks-Hex: MCUboot-Hex (inkl. CCFG) + signiertes, bestaetigtes Slot-0-Image zusammenfuehren.
Ergebnis dient scripts/flash_sensor.py als Eingabe (Erstprogrammierung per ROM-UART-Bootloader)."""
import argparse
from intelhex import IntelHex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mcuboot", required=True)
    ap.add_argument("--slot0", required=True)
    ap.add_argument("--slot0-base", type=lambda s: int(s, 0), default=0x6000)
    ap.add_argument("-o", required=True)
    a = ap.parse_args()
    ih = IntelHex(a.mcuboot)
    mb_max = max(a for a in ih.addresses() if a < 0x40000000)
    if mb_max >= a.slot0_base:
        raise SystemExit("MCUboot ueberlappt Slot 0 (%#x >= %#x)" % (mb_max, a.slot0_base))
    img = open(a.slot0, "rb").read()
    ih.frombytes(img, offset=a.slot0_base)
    ih.write_hex_file(a.o)
    print("[factory] MCUboot bis %#07x, Slot0 %#07x..%#07x (%d Byte), CCFG %s" % (
        mb_max, a.slot0_base, a.slot0_base + len(img) - 1, len(img),
        "ja" if any(x >= 0x4E020000 for x in ih.addresses()) else "NEIN"))


if __name__ == "__main__":
    main()
