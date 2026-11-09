#!/usr/bin/env python3
"""fluidi - SPICE: Weg B Variante B2 (Puffer SN74AUP1G17 auf der Dummy-Scheibe, Prüfspitze an TP1), Auflage DS-B5.

Erweitert prog_uart.py (Adapter, VDD/VIO 1.96-2.04 V aus XC6206) auf den Fall B2: VDD = VIO = EIN Labornetzteil
(Brücke J3-J7 auf der Scheibe, DS-B2), 1.96 / 2.00 / 2.05 / 2.10 V. Gleiche Modelle, Schwellen und ANNAHMEN wie
prog_uart.py (Kopfkommentar dort) und prog_uart_pl2303.py (PL2303: VIL 0.40 V, Board-LED 1 kOhm, Pull-up 0/100 uA).

Aufruf:  .venv/bin/python simulation/spice/programmer/prog_uart_b2.py   (ngspice 42 -b, ca. 30 s)
Ausgabe: prog_uart_b2_report.txt, prog_uart_b2_*.cir (letzte Netzliste je Typ)

Kapazitäten B2 (ANNAHME): Prüfspitze + Leitung TP1-J6 <= 10 cm + Puffer: "Spitze 10 cm" 1/2/20 pF und
"Spitze lang" 1/2/40 pF (= Fall "Puffer am Kabelende" in prog_uart.py). Nur 19200 Baud (DS-B4).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prog_uart as pu  # noqa: E402
import prog_uart_pl2303 as pl  # noqa: E402
import spicetools  # noqa: E402

VS = (1.96, 2.00, 2.05, 2.10)
BAUD = 19200


def opx(net, nodes):
    return pu.op(net, os.path.join(HERE, "prog_uart_b2_dc.cir"), nodes)


def dc_cases():
    rows = []
    for v in VS:
        lin, env = pu.aup_thresholds(v)
        # A1: Puffer-Eingang an TP1, VDD = VIO = v
        for lvl, drv, ilk in (("low", 0.0, 0.5e-6), ("high", v, -0.5e-6)):
            net = pu.head("B2 A1") + [f"VDD vdd 0 DC {v}", f"VIO vio 0 DC {v}", f"VDRV drv 0 DC {drv}",
                                      "RDRV drv dio6 480", *pu.led("RLED", "vdd", "dio6", "DR", "OFF_R_MIN", 470),
                                      "R9 dio6 mid 100k", "R10 mid tp1 100k", f"RPU tp1 vio {pu.R1}",
                                      f"ILK 0 tp1 DC {ilk}"]
            x = opx(net, ["tp1"])["tp1"]
            if lvl == "low":
                ok, g, res = x <= env[2], f"<= {env[2]:.2f} (VT- min Huelle) / {lin[2]:.2f} interp.", env[2] - x
            else:
                ok, g, res = x >= env[1], f">= {env[1]:.2f} (VT+ max Huelle) / {lin[1]:.2f} interp.", x - env[1]
            rows.append(("A1 Puffer-Eingang TP1", f"VDD = VIO = {v} V, Leck {ilk*1e6:+.1f} uA", lvl, x, g, ok, res))
        # A1z: DIO6 hochohmig
        net = pu.head("B2 A1z") + [f"VDD vdd 0 DC {v}", f"VIO vio 0 DC {v}",
                                   *pu.led("RLED", "vdd", "dio6", "DR", "OFF_R_MIN", 470), "RHZ dio6 0 1e12",
                                   "R9 dio6 mid 100k", "R10 mid tp1 100k", f"RPU tp1 vio {pu.R1}", "ILK 0 tp1 DC -0.5u"]
        x = opx(net, ["tp1"])["tp1"]
        # Info wie Adapter (hardware/programmer/README.md Kap. 3 "Wahl von R1"): Ruhepegel vor dem ersten Zugriff im
        # Hysteresebereich, ein Low erscheint als Break 0x00 und wird von flash_sensor.py verworfen -> nicht gezaehlt
        rows.append(("A1z Ruhe, DIO6 hochohmig (Info)", f"VDD = VIO = {v} V, Leck -0.5 uA", "high (Ruhe)", x,
                     f">= {env[3]:.2f} (VT- max, haelt high)", None, x - env[3]))
        # A1o: Puffer-Ausgang -> CH343-RXD
        net = pu.head("B2 A1o") + [f"VIO vio 0 DC {v}", "VY y0 0 DC 0", "RY y0 rxd 184",
                                   *pu.pullup("PU", "rxd", "vio", pu.ch343_ipu_max(v)),
                                   *pu.led("WSRX", "vio", "rxd", "DR", "OFF_R_MIN", 2000)]
        x = opx(net, ["rxd"])["rxd"]
        rows.append(("A1o Puffer -> CH343-RXD", f"VIO {v} V, Pull-up max, Board-LED min", "low", x,
                     "<= 0.50 (CH343 VIL)", x <= 0.5, 0.5 - x))
        # A1p: Puffer-Ausgang -> PL2303-RXD
        for ipl, ipu in pl.IPU:
            net = pl.head("B2 A1p") + [f"VIO vio 0 DC {v}", "VY y0 0 DC 0", f"RY y0 rxd {pl.R_U4}",
                                       *pl.board_rxd("rxd", "vio", ipu)]
            x = opx(net, ["rxd"])["rxd"]
            rows.append(("A1p Puffer -> PL2303-RXD", f"VIO {v} V, Pull-up {ipl}, Board-LED min", "low", x,
                         f"<= {pl.VIL:.2f} (PL2303 VIL)", x <= pl.VIL, pl.VIL - x))
        # B: Host-TXD low (200 Ohm) -> TP2 -> DIO20, blaue LED min
        for off in ("OFF_B_MIN",):
            net = pu.head("B2 B") + [f"VDD vdd 0 DC {v}", "VTX tx0 0 DC 0", "RTX tx0 tp2 200",
                                     "R12 tp2 mid 100k", "R11 mid dio20 100k",
                                     *pu.led("BLED", "vdd", "dio20", "DB", off, 100)]
            x = opx(net, ["dio20"])["dio20"]
            vil = 0.2 * v
            rows.append(("B Sensor-RX (TXD 0 V)", f"VDD {v} V, LED blau min", "low", x, f"<= {vil:.3f} (0.2 VDDS)",
                         x <= vil, vil - x))
        # Bp: PL2303-TXD-Low 0.1 V (Grenze Eingangspruefung B3)
        net = pl.head("B2 Bp") + [f"VDD vdd 0 DC {v}", "VTX tx0 0 DC 0.1", f"RTX tx0 tp2 {pl.R_TX}",
                                  "R12 tp2 mid 100k", "R11 mid dio20 100k",
                                  *pu.led("BLED", "vdd", "dio20", "DB", "OFF_B_MIN", 100)]
        x = opx(net, ["dio20"])["dio20"]
        vil = 0.2 * v
        rows.append(("Bp Sensor-RX (PL2303 TXD 0.1 V)", f"VDD {v} V, LED blau min", "low", x,
                     f"<= {vil:.3f} (0.2 VDDS)", x <= vil, vil - x))
    return rows


def tran_tx(baud, cset, v):
    """wie prog_uart.tran_tx, aber eigene .cir-Datei (prog_uart_tx.cir bleibt unveraendert)."""
    cmid, ctp, cad = cset
    pwl, t_bytes, tend = pu.uart_pwl(baud, v)
    tb = 1.0 / baud
    net = pu.head("B2 TX") + [f"VDD vdd 0 DC {v}", f"VIO vio 0 DC {v}", f"VDRV drv 0 PWL({pwl})", "RDRV drv dio6 480",
                              *pu.led("RLED", "vdd", "dio6", "DR", "OFF_R_MIN", 470),
                              "R9 dio6 mid 100k", f"CMID mid 0 {cmid}p", "R10 mid tp1 100k",
                              f"CTP tp1 0 {ctp}p", f"CAD tp1 0 {cad}p", f"RPU tp1 vio {pu.R1}", "ILK 0 tp1 DC 0.5u"]
    d = spicetools.run("\n".join(net), os.path.join(HERE, "prog_uart_b2_tx.cir"), ["v(tp1)", "v(dio6)"],
                       f"tran {tb/400:.4g} {tend:.6g} 0 {tb/200:.4g}")
    return d, tb, t_bytes


def tran_rx(baud, cmid, cpin, cled, v):
    """wie prog_uart.tran_rx, eigene .cir-Datei."""
    pwl, t_bytes, tend = pu.uart_pwl(baud, v)
    tb = 1.0 / baud
    net = pu.head("B2 RX") + [f"VDD vdd 0 DC {v}", f"VTX tx0 0 PWL({pwl})", "RTX tx0 tp2 200", "CTP2 tp2 0 30p",
                              "R12 tp2 mid 100k", f"CMID mid 0 {cmid}p", "R11 mid dio20 100k", f"CPIN dio20 0 {cpin}p",
                              *pu.led("BLED", "vdd", "dio20", "DB", "OFF_B_MIN", 100), f"CLED vdd aBLED {cled}p"]
    d = spicetools.run("\n".join(net), os.path.join(HERE, "prog_uart_b2_rx.cir"), ["v(dio20)", "v(tp2)"],
                       f"tran {tb/400:.4g} {tend:.6g} 0 {tb/200:.4g}")
    return d, tb, t_bytes


def tran_cases():
    rows = []
    for v in (2.00, 2.10):
        lin, env = pu.aup_thresholds(v)
        thr = {"interp. VT+max/VT-min": (lin[1], lin[2]), "interp. VT+min/VT-max": (lin[0], lin[3]),
               "Huelle VT+1.77/VT-0.47": (env[1], env[2])}
        for cname, cs in {"Spitze 10 cm (1/2/20 pF)": (1, 2, 20), "Spitze lang (1/2/40 pF)": (1, 2, 40)}.items():
            d, tb, t_bytes = tran_tx(BAUD, cs, v)
            for name, ok, m in pu.evaluate(d, tb, BAUD, "v(tp1)", thr, t_bytes):
                rows.append((f"Sensor->Puffer (TP1), VDD = VIO = {v} V", cname, name, ok, m,
                             ok and m >= pu.CRIT_MARGIN))
        th = pu.cc2340_thresholds(v)
        thr_rx = {"0->1 max / 1->0 min": (th[1], th[2]), "0->1 min / 1->0 max": (th[0], th[3])}
        d, tb, t_bytes = tran_rx(BAUD, 3, 9, 30, v)
        for name, ok, m in pu.evaluate(d, tb, BAUD, "v(dio20)", thr_rx, t_bytes):
            rows.append((f"Host->Sensor (DIO20), VDD {v} V", "schlecht, LED 30 pF", name, ok, m,
                         ok and m >= pu.CRIT_MARGIN))
    return rows


def main():
    dc = dc_cases()
    tr = tran_cases()
    L = ["fluidi - prog_uart_b2.py (ngspice -b): Weg B Variante B2, VDD = VIO aus einem Netzteil, 1.96-2.10 V", "",
         "(1) DC-Pegel [V]", "| Fall | Bedingung | Pegel | V | Grenze | ok | Reserve [mV] |", "|---|---|---|---|---|---|---|"]
    for f, b, p, x, g, ok, r in dc:
        okt = "Info" if ok is None else ("ja" if ok else "NEIN")
        L.append(f"| {f} | {b} | {p} | {x:.3f} | {g} | {okt} | {r*1e3:+.0f} |")
    L += ["", f"(2) Transient {BAUD} Baud, Bytes {' '.join('%02X' % b for b in pu.BYTES)}, Taktfehler "
          f"+-{pu.CLK_ERR*100:.1f} %, Kriterium Reserve >= {pu.CRIT_MARGIN} Bit",
          "| Richtung | Kapazitaeten | Schwellen | Bytes ok | Reserve [Bit] | ok |", "|---|---|---|---|---|---|"]
    for r, c, s, ok, m, okk in tr:
        L.append(f"| {r} | {c} | {s} | {'ja' if ok else 'NEIN'} | {m:.3f} | {'ja' if okk else 'NEIN'} |")
    dcz = [r for r in dc if r[5] is not None]
    bad = [r for r in dcz if not r[5]] + [r for r in tr if not r[5]]
    L += ["", f"Ergebnis: {len(dcz) + len(tr) - len(bad)} von {len(dcz) + len(tr)} Faellen ok "
          f"(ohne {len(dc) - len(dcz)} Info-Faelle A1z, wie Adapter: Ruhepegel im Hysteresebereich, unschaedlich)"]
    for r in bad:
        L.append("NICHT ok: " + " / ".join(str(x) for x in r[:3]))
    open(os.path.join(HERE, "prog_uart_b2_report.txt"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
