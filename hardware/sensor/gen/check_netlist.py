#!/usr/bin/env python3
"""Vergleicht die von KiCad exportierte Netzliste mit der Soll-Netzliste des Generators.

Prueft damit die Koordinatentransformation (jeder Pin sitzt am richtigen Label) und dass keine
Netze ungewollt verschmelzen. Aufruf (nach gen_schematic.py):
  .venv/bin/python hardware/sensor/gen/check_netlist.py [kicad-cli]
Ausgabe: hardware/sensor/out/fluidi_sensor.net und Meldung OK / Abweichungen (Exit-Code 1).
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sexpr  # noqa: E402

PRJ = os.path.normpath(os.path.join(HERE, ".."))


def main():
    cli = sys.argv[1] if len(sys.argv) > 1 else "kicad-cli"
    out = os.path.join(PRJ, "out")
    os.makedirs(out, exist_ok=True)
    net = os.path.join(out, "fluidi_sensor.net")
    subprocess.run([cli, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net,
                    os.path.join(PRJ, "fluidi_sensor.kicad_sch")], check=True, capture_output=True)
    tree = sexpr.parse(open(net).read())
    nets = sexpr.find(tree, "nets")
    actual = {}
    for n in sexpr.find_all(nets, "net"):
        name = sexpr.find(n, "name")[1].lstrip("/")
        for node in sexpr.find_all(n, "node"):
            ref, pin = sexpr.find(node, "ref")[1], sexpr.find(node, "pin")[1]
            if ref.startswith("#"):
                continue
            actual.setdefault(ref, {})[pin] = name
    want = json.load(open(os.path.join(HERE, "intended_netlist.json")))
    # Symbole "nicht auf Platine" fehlen in der exportierten Netzliste: E1 (Sonde = Innenlagen-Zonen im Layout,
    # Netze PROBE_SENSE/GND dort ueber Zonen; gen_pcb.py)
    for ref in ("E1",):
        want.pop(ref, None)
    errs = []
    for ref, pins in want.items():
        for pin, netname in pins.items():
            got = actual.get(ref, {}).get(pin)
            if got != netname:
                errs.append(f"{ref}.{pin}: soll {netname}, ist {got}")
    for ref, pins in actual.items():
        for pin, netname in pins.items():
            if pin not in want.get(ref, {}) and not netname.startswith("unconnected-"):
                errs.append(f"{ref}.{pin}: unerwartet an {netname}")
    n_pins = sum(len(p) for p in want.values())
    if errs:
        print("NETZLISTE ABWEICHUNG:\n  " + "\n  ".join(errs))
        sys.exit(1)
    print(f"Netzliste OK: {len(want)} Bauteile, {n_pins} Pins, "
          f"{len({v for p in want.values() for v in p.values()})} Netze stimmen mit der Soll-Netzliste ueberein")


if __name__ == "__main__":
    main()
