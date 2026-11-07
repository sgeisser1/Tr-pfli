#!/usr/bin/env python3
"""fluidi - RGB-Status-LED an CC2340-GPIO (gemeinsame Anode an VDD, Kathoden ueber R an GPIO, GPIO zieht low).

Aufruf:  .venv/bin/python simulation/spice/led_rgb/fit_led_models.py   (einmal, erzeugt led_models.inc)
         .venv/bin/python simulation/spice/led_rgb/led_rgb_drive.py    (erzeugt led_rgb_drive.cir, ruft ngspice -b)

Modell je Zweig:  VDD -> LED (Modell aus led_models.inc, VF-Offset min/mitte/max) -> R_ser -> R_on(GPIO) -> GND
  R_on: CC2340 Standard-Drive VOL <= 0.20 V bei 2 mA, VDDS = 3.0 V, 25 degC
        (docs/datasheets/TI_CC2340R5_Datasheet_SWRS272F.pdf S.31, 7.21.4.1) -> <= 100 Ohm (Grenzwert).
        40 Ohm = ANNAHME typisch. Bei VDDS < 3.0 V ist der Pin schwaecher (ANNAHME, nicht spezifiziert)
        -> 100 Ohm wird fuer den ganzen Bereich als pessimistischer Wert verwendet.
  VDD:  2.4 V (Abschaltschwelle unter Funklast, CONCEPTS.md 2.5) ... 3.0 V (neue Zelle) ... 3.3 V (Adapter).
Ergebnis: LED-Strom je Farbe, Exemplar-Ecke, Vorwiderstand.

Teil 2 (UART-RX-Konflikt): LED_B haengt an DIO20 = ROM-Bootloader UART RX (TRM SWCU193A S.464 Tab. 8-38).
  Der Dummy-Zellen-Adapter treibt RX ueber 2 x 100 kOhm (CONCEPTS.md 2.2). Bei RX = low zieht die blaue LED
  (Anode an VDD = Adapterspannung) den Pin hoch. Gerechnet wird die Pinspannung bei RX = 0 V.
  Schwellen (CC2340 DS S.31/32, 25 degC): high->low 0.59-0.91 V bei VDDS 1.8 V, 1.26-1.79 V bei 3.0 V.
  ACHTUNG: Das Diodenmodell ist unter 1 mA extrapoliert (ANNAHME) -> PROTOTYP-PRUEFUNG.
"""
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
CIR = os.path.join(HERE, "led_rgb_drive.cir")

RSER = {"R": [470, 200], "G": [470, 200, 100], "B": [100, 0.01]}
RON = {"wc": 100, "typ": 40}
CORNERS = ["MIN", "MID", "MAX"]


def build():
    L = ["* fluidi RGB-LED-Treiber, erzeugt von led_rgb_drive.py",
         ".include led_models.inc",
         "VDD vdd 0 DC 3.0"]
    names = []
    k = 0
    for c, rs in RSER.items():
        for r in rs:
            for corner in CORNERS:
                for ron_name, ron in RON.items():
                    k += 1
                    n = f"{c}_{int(r)}_{corner}_{ron_name}"
                    names.append(n)
                    L += [f"D{k} vdd a{k} D{c}",
                          f"VO{k} a{k} b{k} DC {{OFF_{c}_{corner}}}",
                          f"RS{k} b{k} g{k} {r}",
                          f"RON{k} g{k} m{k} {ron}",
                          f"VM{k} m{k} 0 DC 0"]
    L += [".control", "set width=200", "dc VDD 2.4 3.3 0.1"]
    for i, n in enumerate(names, 1):
        L.append(f"print i(VM{i})")
    L += [".endc", ".end"]
    with open(CIR, "w") as f:
        f.write("\n".join(L) + "\n")
    return names


def run(names):
    out = subprocess.run(["ngspice", "-b", CIR], cwd=HERE, capture_output=True, text=True).stdout
    # Bloecke "Index v-sweep i(vmN)"
    res = {}
    cur = None
    for line in out.splitlines():
        m = re.match(r"^Index\s+v-sweep\s+i\(vm(\d+)\)", line.strip(), re.I)
        if m:
            cur = int(m.group(1))
            res.setdefault(cur, {})
            continue
        m = re.match(r"^(\d+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)$", line.strip())
        if m and cur:
            res[cur][round(float(m.group(2)), 2)] = float(m.group(3))
    if not res:
        print(out)
        raise SystemExit("ngspice-Ausgabe nicht lesbar")
    return {names[i - 1]: v for i, v in res.items()}


def rx_check():
    cir = os.path.join(HERE, "led_rx_conflict.cir")
    L = ["* fluidi: blaue LED an DIO20 (UART RX) waehrend Programmierung, erzeugt von led_rgb_drive.py",
         ".include led_models.inc", "VDD vdd 0 DC 3.3"]
    for k, corner in enumerate(CORNERS, 1):
        L += [f"D{k} vdd a{k} DB", f"VO{k} a{k} b{k} DC {{OFF_B_{corner}}}", f"RS{k} b{k} pin{k} 100",
              f"RP{k} pin{k} 0 200k"]
    L += [".control", "set width=200", "dc VDD 1.8 3.3 0.1", "print v(pin1) v(pin2) v(pin3)", ".endc", ".end"]
    open(cir, "w").write("\n".join(L) + "\n")
    out = subprocess.run(["ngspice", "-b", cir], cwd=HERE, capture_output=True, text=True).stdout
    print("\nTeil 2: Pinspannung DIO20 bei RX = 0 V ueber 200 kOhm, blaue LED + 100 Ohm an VDD (Adapter)\n")
    print("| VDD Adapter [V] | V_pin VF-min [V] | V_pin VF-mitte [V] | V_pin VF-max [V] |")
    print("|---|---|---|---|")
    for line in out.splitlines():
        m = re.match(r"^\d+\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)$", line.strip())
        if m:
            v = [float(x) for x in m.groups()]
            if round(v[0], 2) in (1.8, 2.0, 2.2, 2.5, 2.8, 3.0, 3.3):
                print(f"| {v[0]:.1f} | {v[1]:.3f} | {v[2]:.3f} | {v[3]:.3f} |")


def main():
    names = build()
    r = run(names)
    vs = [2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 3.0, 3.3]
    print("LED-Strom in mA (gemeinsame Anode an VDD, GPIO low). Ecken: VF min/mitte/max nach TUOZHAN S.5;"
          " R_on 100 Ohm (Grenzwert) bzw. 40 Ohm (ANNAHME typ)\n")
    print("| Farbe | R_ser | VF-Ecke | R_on | " + " | ".join(f"{v:.1f} V" for v in vs) + " |")
    print("|---|---|---|---|" + "---|" * len(vs))
    for n in names:
        c, rr, corner, ron = n.split("_")
        vals = [abs(r[n].get(v, float('nan'))) * 1e3 for v in vs]
        print(f"| {c} | {rr} | {corner.lower()} | {ron} | " + " | ".join(f"{x:.2f}" for x in vals) + " |")
    rx_check()


if __name__ == "__main__":
    main()
