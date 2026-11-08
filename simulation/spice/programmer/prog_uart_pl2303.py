#!/usr/bin/env python3
"""fluidi - SPICE: Erstprogrammierung mit dem Waveshare PL2303 USB UART Board (type A) V2 statt CH343 (FW-T3).

Aufruf:  .venv/bin/python simulation/spice/programmer/prog_uart_pl2303.py      (ca. 1 min, ngspice 42 im Batchbetrieb)
Ausgabe: prog_uart_pl2303_report.txt, prog_uart_pl2303_dc.csv, prog_uart_pl2303_tran.csv, prog_uart_pl2303_pwr.csv,
         prog_uart_pl2303_pwr.png, prog_uart_pl2303_*.cir (Netzliste des jeweils letzten Falls je Typ)
Baut auf prog_uart.py auf (gleiche Sensormodelle, gleiche Fallnummern A0-A3/B; "p" = PL2303).

Was gerechnet wird
------------------
(1) DC-Pegel (ngspice .op)
    A0p  ohne Puffer: PL2303-RXD direkt am Pogo-Stift TP1 (zeigt, dass der Puffer U4 weiter noetig ist)
    A1   Puffer-Eingang: haengt nicht vom USB-UART ab -> prog_uart_report.txt gilt unveraendert (hier nicht wiederholt)
    A1p  Puffer-Ausgang U4 low -> PL2303-RXD (Board-LED 1 kOhm + Pull-up)
    A2p  Weg B: PL2303-RXD direkt an R9 Pad 1 (DIO6), VDD = VCCIO = Labornetzteil 2.0 / 2.1 / 2.2 V
    A3p  Weg B am falschen Pad (R9 Pad 2)
    Bp   Host -> Sensor: PL2303-TXD (VOL 0 ... 0.4 V) -> TP2 -> 200 kOhm -> DIO20 (blaue LED ueber R8 nach VDD)
    Bh   TXD high am DIO20 gegen VIH 0.8 x VDDS
    G    Grenzwerte fuer die Eingangspruefung des Boards (Bisektion): zulaessiger Senkenstrom des Boards an RXD
         (A1p, A2p) und zulaessiges TXD-Low (Bp); dazu der Strom, den das Board-Modell bei RXD = 0 V liefert
(2) Transient Host -> Sensor (DIO20) wie prog_uart.py, aber mit TXD-Low = 0 V bzw. = Grenzwert aus G.
    Sensor -> Host: Weg A unveraendert (Puffer-Eingang wie prog_uart.py), Weg B treibt DIO6 direkt (480 Ohm gegen
    LED + Leitung, Zeitkonstante << 1 us) -> nicht gerechnet.
(3) Ein-/Ausstecken der USB (Weg A, Adapter Rev 1): VDD_IO (= VIO aus U3) gegen VIN (= USB 5 V, J1.1),
    Grenze VDD_IO <= VIN + 0.3 V (abs. max). Faelle: Sensor ab/angeschlossen, LDO-Modell ohne/mit Rueckwaertsleitung
    im Dropout, ohne/mit Klemmdiode RB751S-40 von VIO nach +5V, ohne/mit Entladewiderstand 1 kOhm / 470 Ohm von VIO
    nach GND (beides Vorschlaege, nicht im Schaltplan Rev 1).

Datenblattwerte (lokale Dateien)
--------------------------------
- PL2303GS: VIN 2.8-5.5 V, VDD_IO 1.8 V ... VIN + 0.3 V, IDD typ 9.5 / max 15 mA (S. 39 Tab. 11-2a); abs. max
  VDD_IO -0.3 ... VIN + 0.3 V, I/O 5-V-tolerant -0.3 ... 6.0 V (S. 39 Tab. 11-1); VIL <= 0.4 V, VIH >= 0.7 x VDD_IO,
  VOL <= 0.4 V, VOH >= 0.7 x VDD_IO, jeweils OHNE Strom-Testbedingung (S. 39 Tab. 11-2b); RXD mit internem schwachem
  Pull-up nach VDD_IO, Wert nicht angegeben (S. 13 Tab. 7-2, S. 27 "Enable-Pull Up"); Anstieg VIN < 1 ms (S. 32
  Bild 10-3b); keine Angabe zur Taktgenauigkeit: docs/datasheets/Prolific_PL2303GS_Datasheet_Rev1.0.4.pdf.
- Board: docs/references/Waveshare_PL2303-USB-UART-Board-TypeA-V2_Schematic_2026-11-08.pdf: P2 1 VCCIO / 2 GND /
  3 TXD / 4 RXD; J1 1 VCC3.3V / 2 VCCIO / 3 VCC5V (Jumper); RXD-LED D3 und TXD-LED D2 je 1 kOhm von VCCIO an die
  Leitung; PWR-LED D1 1 kOhm an VCC5V; C1 4.7 uF an VCC5V (= VIN), C4 1 uF an VCCIO.
- XC6206: Parasitaerdiode VOUT -> VIN im Blockschaltbild (S. 3), VIN 1.8-6.0 V (S. 5), Vdif 250 mV @ 100 mA (S. 1):
  docs/datasheets/Torex_XC6206_Datasheet_ETR0305-004b.pdf.
- RB751S-40: VF <= 0.37 V @ 1 mA, IR <= 0.5 uA @ 30 V (S. 1): docs/datasheets/CJ_RB751S-40_Datasheet.pdf.
- uebrige Werte (CC2340, SN74AUP1G17, LED des Sensors): siehe Kopf von prog_uart.py.

ANNAHMEN
--------
- Board-LEDs: Typ/Farbe nicht angegeben -> Modell der roten Sensor-LED (DR, Exemplar MIN = groesster Strom). Deshalb
  zusaetzlich der zulaessige Board-Senkenstrom (G) als Messkriterium fuer die Eingangspruefung.
- RXD-Pull-up: Wert fehlt im Datenblatt -> Klammer 0 / 100 uA (Stromquelle; CH343 hat 90 uA bei 3.3 V).
- PL2303-TXD: VOL als Spannungsquelle 0 ... 0.4 V hinter 200 Ohm; VOH bei Last < 10 uA = VDD_IO (DS garantiert nur
  0.7 x VDD_IO) -> Messkriterium.
- Puffer U4 Ausgang 184 Ohm (0.35 V @ 1.9 mA bei VCC 1.65 V, wie prog_uart.py), DIO6 480 Ohm.
- Taktfehler PL2303: nicht spezifiziert -> +-1.5 % wie CH343 (der ROM-Bootloader misst die Baudrate des Hosts selbst,
  TRM S. 461/464, damit zaehlt nur die Abweichung innerhalb eines Bytes).
- Abschaltfall: PL2303-VIN als Widerstand 333 Ohm (15 mA bei 5 V, IDD max) -> VIN faellt schnell (ungünstig);
  VDD_IO-Strom des PL2303 und der Last an VIO = 0 (unbekannt; ungünstig, VIO entlaedt sich nur ueber die LDO);
  TXD-/RXD-LED ohne Strom (ungünstig); Parasitaerdiode XC6206: IS 1e-12 A, N 1 (Wert nicht angegeben);
  LDO-Regelung aktiv ab VIN 1.8 V (DS S. 5 VIN min), darunter Durchlasselement aus.
  Sensor angeschlossen: 4 x 100 uF + 10 uF = 410 uF, Last 0.8 mA (Bootloader Idle, PROGRAMMIEREN Kap. 6).
  RB751S-40: IS 6.1e-10 A, N 1 aus dem einzigen Datenblattpunkt 0.37 V @ 1 mA.
  Kondensatoren an VIO: C4 1 uF (Adapter) + C4 1 uF (Board) + C5 100 nF; an VIN: C1 4.7 uF (Board) + C1 1 uF (Adapter).
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prog_uart as pu  # noqa: E402  (setzt auch den Pfad fuer spicetools)
import spicetools  # noqa: E402

VIL = 0.40                      # PL2303 VIL max (Tab. 11-2b)
R_LED = 1000                    # Board RXD-/TXD-LED-Vorwiderstand
IPU = (("0", 0.0), ("100 uA", 100e-6))   # ANNAHME Pull-up-Klammer
R_U4 = 184
R_DIO6 = 480
R_TX = 200


def head(t):
    return pu.head("PL2303 " + t)


def board_rxd(node, vio, ipu, off="OFF_R_MIN"):
    """RXD-Seite des Boards: LED D3 + 1 kOhm von VCCIO an RXD, interner Pull-up."""
    out = pu.led("BRX", vio, node, "DR", off, R_LED)
    if ipu > 0:
        out += pu.pullup("PU", node, vio, ipu)
    return out


def op(net, name, nodes):
    return pu.op(net, os.path.join(HERE, f"prog_uart_pl2303_{name}.cir"), nodes)


def bisect(f, lo, hi, target, n=40):
    """f monoton steigend; liefert x mit f(x) = target."""
    for _ in range(n):
        mid = 0.5 * (lo + hi)
        if f(mid) > target:
            hi = mid
        else:
            lo = mid
    return 0.5 * (lo + hi)


# --------------------------------------------------------------------- (1) DC
def dc_cases():
    rows = []

    def row(fall, bed, knoten, pegel, v, grenze, ok, res=None):
        rows.append(dict(fall=fall, bedingung=bed, knoten=knoten, pegel=pegel, v=v, grenze=grenze, ok=ok,
                         reserve_mV=None if res is None else res * 1e3))

    # A0p: ohne Puffer, PL2303-RXD am TP1
    for ipl, ipu in IPU:
        for off in ("OFF_R_MIN", "OFF_R_MAX"):
            net = head("A0p") + ["VDD vdd 0 DC 2.0", "VIO vio 0 DC 2.0", "VDRV drv 0 DC 0", f"RDRV drv dio6 {R_DIO6}",
                                 *pu.led("RLED", "vdd", "dio6", "DR", "OFF_R_MID", 470),
                                 "R9 dio6 mid 100k", "R10 mid tp1 100k", *board_rxd("tp1", "vio", ipu, off)]
            v = op(net, "dc", ["tp1"])["tp1"]
            row("A0p ohne Puffer", f"VIO 2.0 V, Pull-up {ipl}, Board-LED {off[6:]}", "PL2303-RXD (TP1)", "low", v,
                f"<= {VIL:.2f} (VIL)", v <= VIL, VIL - v)

    # A1p: Puffer-Ausgang low -> PL2303-RXD
    for vio in (1.96, 2.04):
        for ipl, ipu in IPU:
            net = head("A1p") + [f"VIO vio 0 DC {vio}", "VY y0 0 DC 0", f"RY y0 rxd {R_U4}", *board_rxd("rxd", "vio", ipu)]
            v = op(net, "dc", ["rxd"])["rxd"]
            row("A1p Puffer-Ausgang", f"VIO {vio} V, Pull-up {ipl}, Board-LED MIN", "PL2303-RXD", "low", v,
                f"<= {VIL:.2f} (VIL)", v <= VIL, VIL - v)

    # A2p: Weg B, RXD an DIO6; VDD = VCCIO
    for vdd in (2.0, 2.1, 2.2):
        for ipl, ipu in IPU:
            net = head("A2p") + [f"VDD vdd 0 DC {vdd}", "VDRV drv 0 DC 0", f"RDRV drv dio6 {R_DIO6}",
                                 *pu.led("RLED", "vdd", "dio6", "DR", "OFF_R_MIN", 470), *board_rxd("dio6", "vdd", ipu),
                                 "R9 dio6 mid 100k", "R10 mid tp1 100k", "RTP tp1 0 1e12"]
            v = op(net, "dc", ["dio6"])["dio6"]
            row("A2p Weg B R9 Pad 1", f"VDD = VCCIO = {vdd} V, Pull-up {ipl}, beide LED MIN", "DIO6 = PL2303-RXD",
                "low", v, f"<= {VIL:.2f} (VIL)", v <= VIL, VIL - v)

    # A3p: falsches Pad
    for ipl, ipu in IPU:
        net = head("A3p") + ["VDD vdd 0 DC 2.0", "VDRV drv 0 DC 0", f"RDRV drv dio6 {R_DIO6}",
                             *pu.led("RLED", "vdd", "dio6", "DR", "OFF_R_MID", 470), "R9 dio6 mid 100k",
                             *board_rxd("mid", "vdd", ipu, "OFF_R_MAX"), "R10 mid tp1 100k", "RTP tp1 0 1e12"]
        v = op(net, "dc", ["mid"])["mid"]
        row("A3p Weg B falsches Pad (R9 Pad 2)", f"VDD = VCCIO = 2.0 V, Pull-up {ipl}, Board-LED MAX",
            "UART_TX_MID = PL2303-RXD", "low", v, f"<= {VIL:.2f} (VIL)", v <= VIL, VIL - v)

    # Bp: TXD low (VOL-Quelle) -> DIO20
    for vdd, src in ((1.96, "Weg A min"), (2.04, "Weg A max"), (2.0, "Weg B"), (2.2, "Weg B max")):
        for vol in (0.0, 0.1, 0.2, 0.4):
            net = head("Bp") + [f"VDD vdd 0 DC {vdd}", f"VTX tx0 0 DC {vol}", f"RTX tx0 tp2 {R_TX}",
                                "R12 tp2 mid 100k", "R11 mid dio20 100k",
                                *pu.led("BLED", "vdd", "dio20", "DB", "OFF_B_MIN", 100)]
            v = op(net, "dc", ["dio20"])["dio20"]
            vil = 0.2 * vdd
            row("Bp Sensor-RX", f"VDD {vdd} V ({src}), TXD-Low {vol:.1f} V, LED blau MIN", "DIO20", "low", v,
                f"<= {vil:.3f} (VIL 0.2 VDDS)", v <= vil, vil - v)

    # Bh: TXD high -> DIO20 (Last < 10 uA, DIO20 hochohmig, LED sperrt)
    for vio, vdd, lbl in ((1.96, 2.04, "Weg A, VIO min / VDD max"), (2.0, 2.0, "Weg B"), (2.2, 2.2, "Weg B max")):
        for voh_lbl, voh in (("DS min 0.7 x VDD_IO", 0.7 * vio), ("= VDD_IO (ANNAHME, Last < 10 uA)", vio)):
            net = head("Bh") + [f"VDD vdd 0 DC {vdd}", f"VTX tx0 0 DC {voh}", f"RTX tx0 tp2 {R_TX}",
                                "R12 tp2 mid 100k", "R11 mid dio20 100k",
                                *pu.led("BLED", "vdd", "dio20", "DB", "OFF_B_MIN", 100)]
            v = op(net, "dc", ["dio20"])["dio20"]
            vih = 0.8 * vdd
            row("Bh Sensor-RX high", f"{lbl}: VIO {vio} V, VDD {vdd} V, TXD-High {voh_lbl}", "DIO20", "high", v,
                f">= {vih:.3f} (VIH 0.8 VDDS)", v >= vih, v - vih)
    return rows


def limits():
    """Grenzwerte fuer die Eingangspruefung des Boards."""
    out = []

    # Strom, den das Board-Modell bei RXD = 0 V liefert (das misst man mit dem Amperemeter RXD -> GND)
    def i_short(vio, ipu):
        net = head("Ish") + [f"VIO vio 0 DC {vio}", "VM rxd 0 DC 0", *board_rxd("rxd", "vio", ipu)]
        d = spicetools.run("\n".join(net), os.path.join(HERE, "prog_uart_pl2303_dc.cir"), ["i(vm)"], "op")
        return float(d["i(vm)"][0])

    for vio in (2.0, 2.04, 2.2):
        for ipl, ipu in IPU:
            out.append(dict(groesse=f"Board-Modell: Strom RXD -> GND bei VCCIO {vio} V, Pull-up {ipl}",
                            wert=i_short(vio, ipu) * 1e3, einheit="mA"))

    # A1p: zulaessiger Board-Senkenstrom (Stromquelle in RXD) bis 0.40 V am U4-Ausgang
    out.append(dict(groesse="A1p (Weg A): zulaessiger Board-Strom in den U4-Ausgang bis RXD = 0.40 V",
                     wert=VIL / R_U4 * 1e3, einheit="mA"))

    # A2p: zulaessiger Board-Senkenstrom in DIO6 bis 0.40 V
    for vdd in (2.0, 2.1, 2.2):
        def f(ib, vdd=vdd):
            net = head("G2") + [f"VDD vdd 0 DC {vdd}", "VDRV drv 0 DC 0", f"RDRV drv dio6 {R_DIO6}",
                                *pu.led("RLED", "vdd", "dio6", "DR", "OFF_R_MIN", 470), f"IB vdd dio6 DC {ib:.6g}",
                                "R9 dio6 mid 100k", "R10 mid tp1 100k", "RTP tp1 0 1e12"]
            return op(net, "dc", ["dio6"])["dio6"]
        ib = bisect(f, 0.0, 5e-3, VIL, 30)
        out.append(dict(groesse=f"A2p (Weg B): zulaessiger Board-Strom in DIO6 bis 0.40 V, VDD = {vdd} V",
                        wert=ib * 1e3, einheit="mA"))

    # Bp: zulaessiges TXD-Low bis DIO20 = 0.2 VDDS
    for vdd in (1.96, 2.0, 2.2):
        def g(vol, vdd=vdd):
            net = head("G3") + [f"VDD vdd 0 DC {vdd}", f"VTX tx0 0 DC {vol:.6g}", f"RTX tx0 tp2 {R_TX}",
                                "R12 tp2 mid 100k", "R11 mid dio20 100k",
                                *pu.led("BLED", "vdd", "dio20", "DB", "OFF_B_MIN", 100)]
            return op(net, "dc", ["dio20"])["dio20"]
        vol = bisect(g, 0.0, 0.6, 0.2 * vdd, 30)
        out.append(dict(groesse=f"Bp: zulaessiges TXD-Low bis DIO20 = 0.2 x VDDS, VDD = {vdd} V",
                        wert=vol * 1e3, einheit="mV"))
    return out


# --------------------------------------------------------------------- (2) Transient Host -> Sensor
def tran_rx(baud, cmid, cpin, cled, vdd, vol):
    pwl, t_bytes, tend = pu.uart_pwl(baud, vdd - vol)
    tb = 1.0 / baud
    net = head("RX") + [f"VDD vdd 0 DC {vdd}", f"VTX tx0 txo PWL({pwl})", f"VOL txo 0 DC {vol}",
                        f"RTX tx0 tp2 {R_TX}", "CTP2 tp2 0 30p",
                        "R12 tp2 mid 100k", f"CMID mid 0 {cmid}p", "R11 mid dio20 100k", f"CPIN dio20 0 {cpin}p",
                        *pu.led("BLED", "vdd", "dio20", "DB", "OFF_B_MIN", 100), f"CLED vdd aBLED {cled}p"]
    d = spicetools.run("\n".join(net), os.path.join(HERE, "prog_uart_pl2303_rx.cir"), ["v(dio20)"],
                       f"tran {tb/400:.4g} {tend:.6g} 0 {tb/200:.4g}")
    return d, tb, t_bytes


def tran_cases(vol_lim):
    rows = []
    for vdd in (2.0, 2.2):
        th = pu.cc2340_thresholds(vdd)
        thr = {"0->1 max / 1->0 min": (th[1], th[2]), "0->1 min / 1->0 max": (th[0], th[3])}
        for vol_lbl, vol in (("0 V", 0.0), ("0.1 V", 0.1), ("0.2 V", 0.2),
                             (f"DC-Grenze {vol_lim[vdd]*1e3:.0f} mV", vol_lim[vdd])):
            for baud in (19200, 57600):
                for cname, (cm, cp, cl) in {"nominal, LED 0 pF": (1, 7, 0), "schlecht, LED 30 pF": (3, 9, 30)}.items():
                    d, tb, t_bytes = tran_rx(baud, cm, cp, cl, vdd, vol)
                    tr, tf, vlo, vhi = pu.rise_fall(d["time"], d["v(dio20)"], t_bytes, tb)
                    for name, ok, m in pu.evaluate(d, tb, baud, "v(dio20)", thr, t_bytes):
                        rows.append(dict(richtung=f"PL2303-TXD -> DIO20, VDD {vdd} V", txd_low=vol_lbl, baud=baud,
                                         kap=cname, schwellen=name, v_low=vlo, v_high=vhi, t_rise_us=tr * 1e6,
                                         t_fall_us=tf * 1e6, bytes_ok=ok, reserve_bit=m,
                                         ok=ok and m >= pu.CRIT_MARGIN))
    return rows


# --------------------------------------------------------------------- (3) USB ein-/ausstecken
LDO_SUB = """
.subckt XC6206 in out params: VSET=2.0 RON=2.5 GM=10 ILIM=0.2 BIDIR=0
* Durchlasselement: Regelung, Dropout (RON), Strombegrenzung; aktiv ab VIN 1.8 V (DS S. 5)
B1 in out I = max(0,min(1,(v(in)-1.7)/0.1)) * ( v(in) >= v(out) ? max(0, min(min(GM*(VSET-v(out)), ILIM), (v(in)-v(out))/RON)) : ( v(out) < VSET-0.01 ? BIDIR*(v(in)-v(out))/RON : 0 ) )
* Parasitaerdiode VOUT -> VIN (DS S. 3)
DB out in DBODY
.model DBODY D(IS=1e-12 N=1)
.ends
.model DRB751 D(IS=6.1e-10 N=1 RS=1)
.model SWU SW(VT=0.5 VH=0.1 RON=0.05 ROFF=1e9)
"""


def pwr_case(mode, sensor, bidir, clamp, bleed=None):
    """mode 'aus': USB bei 1 ms getrennt; 'ein': VBUS-Rampe 0 -> 5 V in 0.5 ms (ANNAHME, DS verlangt < 1 ms)."""
    tend = 0.4 if sensor else 0.05
    if mode == "aus":
        src = ["VUSB usb 0 DC 5", "VCTL ctl 0 PWL(0 1 1m 1 1.001m 0)", "S1 usb vin ctl 0 SWU"]
    else:
        src = ["VUSB usb 0 PWL(0 0 1m 0 1.5m 5)", "RUSB usb vin 0.2"]
        tend = 0.05
    net = head("PWR") + [LDO_SUB] + src + [
        "CVIN vin 0 5.7u", "RIDD vin 0 333", *pu.led("PWR", "vin", "0", "DR", "OFF_R_MIN", 1000),
        f"XU1 vin v33 XC6206 VSET=3.3 BIDIR={bidir}", "C2 v33 0 1u",
        f"XU2 v33 vdd XC6206 VSET=2.0 BIDIR={bidir}", "C3 vdd 0 1u",
        f"XU3 v33 vio XC6206 VSET=2.0 BIDIR={bidir}", "C4 vio 0 1u", "CB4 vio 0 1u", "C5 vio 0 0.1u",
        "RVIO vio 0 1e9"]
    if sensor:
        net += ["CSEN vdd 0 410u", "RSEN vdd 0 2.5k"]
    if clamp:
        net += ["DCL vio vin DRB751"]
    if bleed:
        net += [f"RBL vio 0 {bleed}"]
    d = spicetools.run("\n".join(net), os.path.join(HERE, "prog_uart_pl2303_pwr.cir"),
                       ["v(vin)", "v(vio)", "v(v33)", "v(vdd)"], f"tran 5u {tend} 0 20u")
    t, vin, vio = d["time"], d["v(vin)"], d["v(vio)"]
    dv = vio - vin
    m = t > (1e-3 if mode == "aus" else 0)
    over = dv > 0.3
    dt = np.diff(t, prepend=t[0])
    t_over = float(np.sum(dt[over & m]))
    q_cap = 2.1e-6 * max(0.0, float(np.max(dv[m])))   # Ladung der VIO-Kondensatoren oberhalb VIN (Groessenordnung)
    return dict(vorgang="USB ziehen" if mode == "aus" else "USB einstecken", sensor="ja (410 uF)" if sensor else "nein",
                ldo="rueckwaerts leitend im Dropout" if bidir else "nur Parasitaerdiode (ungünstig)",
                klemme=("RB751S-40 VIO->+5V" if clamp else "keine") + (f", R {bleed} VIO->GND" if bleed else ""),
                dv_max=float(np.max(dv[m])), t_ueber_0_3=t_over * 1e3,
                vio_bei_vin_0_5=float(np.interp(0.5, vin[::-1], vio[::-1])) if mode == "aus" and vin[-1] < 0.5 else float("nan"),
                q_uC=q_cap * 1e6, ok=bool(np.max(dv[m]) <= 0.3)), d


def pwr_cases():
    rows, waves = [], {}
    r, _ = pwr_case("ein", False, 0, False)
    rows.append(r)
    r, _ = pwr_case("ein", True, 0, False)
    rows.append(r)
    for sensor in (False, True):
        for bidir in (0, 1):
            for clamp in (False, True):
                r, d = pwr_case("aus", sensor, bidir, clamp)
                rows.append(r)
                waves[(sensor, bidir, clamp)] = d
    for sensor in (False, True):
        for clamp, bleed in ((False, "1k"), (False, "470"), (True, "1k")):
            r, _ = pwr_case("aus", sensor, 0, clamp, bleed)
            rows.append(r)
    return rows, waves


def plot(waves):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
    for k, (sensor, bidir, clamp) in enumerate([(False, 0, False), (True, 0, False)]):
        a = ax[k]
        for cl, ls in ((False, "-"), (True, "--")):
            d = waves[(sensor, bidir, cl)]
            tt = d["time"] * 1e3
            a.plot(tt, d["v(vin)"], ls, color="C0", lw=1, label="VIN (USB 5 V)" + (" mit Klemme" if cl else ""))
            a.plot(tt, d["v(vio)"], ls, color="C3", lw=1, label="VDD_IO (U3)" + (" mit Klemme" if cl else ""))
            a.plot(tt, d["v(vio)"] - d["v(vin)"], ls, color="k", lw=0.8,
                   label="VDD_IO - VIN" + (" mit Klemme" if cl else ""))
        a.axhline(0.3, color="gray", ls=":", lw=0.8)
        a.set_xscale("log")
        a.set_xlim(0.5, 400 if sensor else 50)
        a.set_title(f"USB ziehen, Sensor {'angeschlossen' if sensor else 'ab'}, LDO nur Parasitaerdiode")
        a.set_xlabel("t [ms] (log)")
        a.set_ylabel("V")
        a.grid(alpha=0.3)
        a.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "prog_uart_pl2303_pwr.png"), dpi=110)


def main():
    dc = dc_cases()
    lim = limits()
    vol_lim = {}
    for vdd in (2.0, 2.2):
        vol_lim[vdd] = [x["wert"] for x in lim if x["groesse"].endswith(f"VDD = {vdd} V") and
                        x["groesse"].startswith("Bp")][0] / 1e3
    tr = tran_cases(vol_lim)
    pw, waves = pwr_cases()

    for name, rows in (("dc", dc), ("tran", tr), ("pwr", pw)):
        with open(os.path.join(HERE, f"prog_uart_pl2303_{name}.csv"), "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader()
            for r in rows:
                w.writerow(r)

    yn = lambda b: "ja" if b else "NEIN"  # noqa: E731
    L = ["fluidi - prog_uart_pl2303.py (ngspice -b): Waveshare PL2303 USB UART Board (type A) V2 statt CH343", "",
         "(1) DC-Pegel [V]", "| Fall | Bedingung | Knoten | Pegel | V | Grenze | ok | Reserve |", "|---|---|---|---|---|---|---|---|"]
    for r in dc:
        res = "" if r["reserve_mV"] is None else f"{r['reserve_mV']:+.0f} mV"
        L.append(f"| {r['fall']} | {r['bedingung']} | {r['knoten']} | {r['pegel']} | {r['v']:.3f} | {r['grenze']} | "
                 f"{yn(r['ok'])} | {res} |")
    L += ["", "(1b) Grenzwerte fuer die Eingangspruefung des Boards", "| Groesse | Wert | Einheit |", "|---|---|---|"]
    for x in lim:
        L.append(f"| {x['groesse']} | {x['wert']:.3f} | {x['einheit']} |")
    L += ["", f"(2) Transient PL2303-TXD -> DIO20: Bytes {' '.join('%02X' % b for b in pu.BYTES)}, Taktfehler "
          f"+-{pu.CLK_ERR*100:.1f} % (ANNAHME), Kriterium Reserve >= {pu.CRIT_MARGIN} Bit",
          "| Richtung | TXD-Low | Baud | Kapazitaeten | Schwellen | V low / high | t10-90 steigend [us] | fallend [us] | "
          "Bytes ok | Reserve [Bit] | ok |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in tr:
        L.append(f"| {r['richtung']} | {r['txd_low']} | {r['baud']} | {r['kap']} | {r['schwellen']} | {r['v_low']:.3f} / "
                 f"{r['v_high']:.3f} | {r['t_rise_us']:.2f} | {r['t_fall_us']:.2f} | {yn(r['bytes_ok'])} | "
                 f"{r['reserve_bit']:.3f} | {yn(r['ok'])} |")
    L += ["", "(3) USB ein-/ausstecken (Weg A, Adapter Rev 1): Grenze VDD_IO - VIN <= 0.3 V (PL2303 S. 39 Tab. 11-1)",
          "| Vorgang | Sensor | LDO-Modell | Klemmdiode | max(VDD_IO - VIN) [V] | Dauer > 0.3 V [ms] | VDD_IO bei VIN 0.5 V | "
          "ok |", "|---|---|---|---|---|---|---|---|"]
    for r in pw:
        vv = "" if np.isnan(r["vio_bei_vin_0_5"]) else f"{r['vio_bei_vin_0_5']:.2f} V"
        L.append(f"| {r['vorgang']} | {r['sensor']} | {r['ldo']} | {r['klemme']} | {r['dv_max']:.3f} | "
                 f"{r['t_ueber_0_3']:.2f} | {vv} | {yn(r['ok'])} |")
    open(os.path.join(HERE, "prog_uart_pl2303_report.txt"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    plot(waves)


if __name__ == "__main__":
    main()
