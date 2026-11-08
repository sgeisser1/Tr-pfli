#!/usr/bin/env python3
"""fluidi – Pruefung der Ausnahmebehandlung im gelinkten Anwendungs-Image (O-5).

1. Vektortabelle .resetVecs: NMI (Index 2) und HardFault (Index 3) zeigen auf fl_fault_handler, kein Eintrag zeigt
   auf Exception_handlerSpin (SDK kernel/freertos/exception/ExceptionArmV6M.c Z. 67-72: Endlosschleife bis Watchdog).
2. fl_fault_handler und das aufgerufene PMCTLResetSystem benutzen keinen Stack (kein push/sub sp/str ... [sp]):
   der Handler muss auch bei zerstoertem Stapel bis zum Systemreset kommen.

Aufruf (Makefile, Ziel size):  check_fault_vectors.py --objdump <tiarmobjdump> --elf build/app/fluidi_sensor.out
"""
import argparse
import re
import struct
import subprocess
import sys


def run(cmd):
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def symbols(objdump, elf):
    out = {}
    for line in run([objdump, "-t", elf]).splitlines():
        p = line.split()
        if len(p) >= 5 and re.fullmatch(r"[0-9a-fA-F]{8}", p[0]):
            out[p[-1]] = int(p[0], 16)
    return out


def section_bytes(objdump, elf, name):
    data = bytearray()
    base = None
    for line in run([objdump, "-s", "-j", name, elf]).splitlines():
        m = re.match(r"^\s([0-9a-f]+)\s((?:[0-9a-f]{1,8}\s){1,4})", line)
        if not m:
            continue
        addr = int(m.group(1), 16)
        if base is None:
            base = addr
        data += bytes.fromhex("".join(m.group(2).split()))
    return base, bytes(data)


def stack_use(objdump, elf, sym):
    dis = run([objdump, "-d", f"--disassemble-symbols={sym}", elf])
    body = [l for l in dis.splitlines() if re.match(r"^\s+[0-9a-f]+:", l)]
    bad = [l.strip() for l in body if re.search(r"\b(push|stm|stmdb)\b|\bsp\b", l.split("@")[0])]
    return body, bad


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--objdump", required=True)
    ap.add_argument("--elf", required=True)
    a = ap.parse_args(argv)
    errs = []
    sym = symbols(a.objdump, a.elf)
    h = sym.get("fl_fault_handler")
    if h is None:
        errs.append("fl_fault_handler fehlt im Image")
    base, vec = section_bytes(a.objdump, a.elf, ".resetVecs")
    words = struct.unpack_from(f"<{len(vec) // 4}I", vec) if vec else ()
    if len(words) < 16:
        errs.append(".resetVecs fehlt oder zu kurz")
    elif h is not None:
        for i, name in ((2, "NMI"), (3, "HardFault")):
            if words[i] & ~1 != h & ~1:
                errs.append(f"Vektor {i} ({name}) = 0x{words[i]:08x}, erwartet fl_fault_handler 0x{h | 1:08x}")
    spin = sym.get("Exception_handlerSpin")
    if spin is not None and any(w & ~1 == spin & ~1 for w in words):
        errs.append("Vektortabelle enthaelt noch Exception_handlerSpin")
    for s in ("fl_fault_handler", "PMCTLResetSystem"):
        if s not in sym:
            continue                                   # PMCTLResetSystem kann inline sein
        body, bad = stack_use(a.objdump, a.elf, s)
        if not body:
            errs.append(f"{s}: kein Disassemblat")
        for l in bad:
            errs.append(f"{s} benutzt den Stack: {l}")
    if errs:
        for e in errs:
            print(f"  [FEHLER] {e}")
        return 1
    print(f"  [ok] Ausnahmevektoren -> fl_fault_handler (0x{h | 1:08x}), ohne Stack, kein Exception_handlerSpin (O-5)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
