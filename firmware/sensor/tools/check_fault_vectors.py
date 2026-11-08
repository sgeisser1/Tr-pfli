#!/usr/bin/env python3
"""fluidi – Pruefung der Ausnahmebehandlung im gelinkten Anwendungs-Image (O-5).

1. Vektortabelle .resetVecs: NMI (Index 2) und HardFault (Index 3) zeigen auf fl_fault_handler, kein Eintrag zeigt
   auf Exception_handlerSpin (SDK kernel/freertos/exception/ExceptionArmV6M.c Z. 67-72: Endlosschleife bis Watchdog).
2. fl_fault_handler und das aufgerufene PMCTLResetSystem benutzen keinen Stack (kein push/sub sp/str ... [sp]):
   der Handler muss auch bei zerstoertem Stapel bis zum Systemreset kommen.
3. Asserts (O-5 Folge): AssertHandler und vApplicationStackOverflowHook stammen aus fl_assert.obj, main aus
   fl_main.obj, das SDK-main_freertos.obj (HAL_ASSERT_SPINLOCK in jeder Ursache) ist nicht gelinkt; beide rufen
   fl_fault_handler und enthalten keine Rueckwaertsspruenge (Spin-Schleife); main traegt AssertHandler in
   halAssertCback ein und uebergibt ihn an RegisterAssertCback. Die Rueckfall-Callbacks der Bibliotheken
   (halAssertSpinlock, halAssertHandler, DefaultAssertCback, driverTable_fnSpinlock), soweit gelinkt, enthalten
   ebenfalls keine Schleife.

Aufruf (Makefile, Ziel size):
  check_fault_vectors.py --objdump <tiarmobjdump> --elf build/app/fluidi_sensor.out --map build/app/fluidi_sensor.map
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


def disasm(objdump, elf, sym):
    dis = run([objdump, "-d", f"--disassemble-symbols={sym}", elf])
    return [l for l in dis.splitlines() if re.match(r"^\s+[0-9a-f]+:", l)]


def backward_branches(body):
    """Sprungbefehle (b, b<cond>, cbz/cbnz) auf eine Adresse <= eigene Adresse = Schleife."""
    out = []
    for l in body:
        m = re.match(r"^\s+([0-9a-f]+):\s+(?:[0-9a-f]{4}\s+)+\s*(\w+)(?:\.\w+)?\s+(?:\w+,\s*)?0x([0-9a-f]+)", l)
        if not m:
            continue
        addr, mn, tgt = int(m.group(1), 16), m.group(2), int(m.group(3), 16)
        if mn.startswith("bl") or mn.startswith("bx"):
            continue
        if (mn == "b" or re.fullmatch(r"b(eq|ne|cs|hs|cc|lo|mi|pl|vs|vc|hi|ls|ge|lt|gt|le|al)", mn)
                or mn in ("cbz", "cbnz")) and tgt <= addr:
            out.append(l.strip())
    return out


def text_words(objdump, elf):
    words = {}
    for line in run([objdump, "-s", "-j", ".text", elf]).splitlines():
        m = re.match(r"^\s([0-9a-f]+)\s((?:[0-9a-f]{1,8}\s){1,4})", line)
        if m:
            a = int(m.group(1), 16)
            for i, w in enumerate(m.group(2).split()):
                if len(w) == 8:
                    words[a + 4 * i] = struct.unpack("<I", bytes.fromhex(w))[0]
    return words


def check_asserts(objdump, elf, mapfile, sym):
    errs = []
    mp = open(mapfile, encoding="latin-1").read()
    if "main_freertos.obj" in mp:
        errs.append("SDK main_freertos.obj ist gelinkt (AssertHandler mit HAL_ASSERT_SPINLOCK)")
    for fn, obj in (("AssertHandler", "fl_assert.obj"), ("vApplicationStackOverflowHook", "fl_assert.obj"),
                    ("main", "fl_main.obj")):
        if not re.search(rf"\b{re.escape(obj)} \(\.text\.{fn}\)", mp):
            errs.append(f"{fn} stammt nicht aus {obj}")
    for fn in ("AssertHandler", "vApplicationStackOverflowHook"):
        body = disasm(objdump, elf, fn)
        if not any("<fl_fault_handler>" in l and re.search(r"\s(bl?|b\.w)\s", l) for l in body):
            errs.append(f"{fn} ruft fl_fault_handler nicht auf")
        errs += [f"{fn}: Schleife {l}" for l in backward_branches(body)]
        # Sprungtabellen (add/mov pc) entziehen sich der Schleifensuche -> in diesen Funktionen nicht zulaessig
        errs += [f"{fn}: berechneter Sprung {l.strip()}" for l in body if re.search(r"\s(add|mov)\s+pc,", l)]
        if len(body) > 4:
            errs.append(f"{fn}: {len(body)} Befehle, erwartet nur den Aufruf von fl_fault_handler")
    for fn in ("halAssertSpinlock", "halAssertHandler", "DefaultAssertCback", "driverTable_fnSpinlock"):
        if fn in sym:
            errs += [f"{fn}: Spin-Schleife {l}" for l in backward_branches(disasm(objdump, elf, fn))]
    # main: halAssertCback = AssertHandler; RegisterAssertCback(AssertHandler)
    if all(k in sym for k in ("main", "AssertHandler", "halAssertCback")):
        words = text_words(objdump, elf)
        lits = set()
        for l in disasm(objdump, elf, "main"):
            m = re.search(r"ldr\s+r\d+, \[pc, #0x[0-9a-f]+\]\s+@ 0x([0-9a-f]+)", l)
            if m and int(m.group(1), 16) in words:
                lits.add(words[int(m.group(1), 16)])
        if (sym["AssertHandler"] | 1) not in lits or sym["halAssertCback"] not in lits:
            errs.append("main laedt AssertHandler/halAssertCback nicht (Registrierung fehlt?)")
    return errs


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--objdump", required=True)
    ap.add_argument("--elf", required=True)
    ap.add_argument("--map", required=True)
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
    errs += check_asserts(a.objdump, a.elf, a.map, sym)
    if errs:
        for e in errs:
            print(f"  [FEHLER] {e}")
        return 1
    print(f"  [ok] Ausnahmevektoren -> fl_fault_handler (0x{h | 1:08x}), ohne Stack, kein Exception_handlerSpin (O-5)")
    print("  [ok] AssertHandler/Stackueberlauf -> fl_fault_handler, kein HAL_ASSERT_SPINLOCK/keine Spin-Schleife (O-5)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
