#!/usr/bin/env python3
"""fluidi - SPICE: UART-Pegel und Zeitverhalten bei der Erstprogrammierung (Red-Team W-4, B-4).

Aufruf:  .venv/bin/python simulation/spice/programmer/prog_uart.py      (ca. 1 min, ngspice 42 im Batchbetrieb)
Ausgabe: prog_uart_report.txt (Tabellen), prog_uart_dc.csv, prog_uart_tran.csv, prog_uart_waveforms.png,
         prog_uart_*.cir (Netzliste des jeweils letzten Falls je Typ)

Was gerechnet wird
------------------
(1) DC-Pegel (ngspice .op), Sensor -> Host (TX-Leitung DIO6 -> R9 -> R10 -> TP1):
    A0  Ist-Zustand ohne Puffer: CH343-RXD direkt am Pogo-Stift TP1 (Befund W-4)
    A1  Adapter Rev 1: Schmitt-Puffer SN74AUP1G17 direkt am Pogo-Stift, Pull-up R1 10 MOhm
    A1o Puffer-Ausgang -> CH343-RXD (Pegel am CH343)
    A2  Behelf: CH343-RXD direkt am R9-Pad 1 (Knoten LED_R_UART_TX = DIO6)
    A3  Behelf am falschen Pad: R9-Pad 2 (UART_TX_MID, hinter den ersten 100 kOhm)
    Host -> Sensor (CH343-TXD -> TP2 -> R12 -> R11 -> DIO20, blaue LED ueber R8 nach VDD):
    B   Adapter 1.96 / 2.00 / 2.04 V und Behelf 2.2 V
(2) Transient: UART-Bytefolge 0x55 0x55 0x00 0xFF 0x01 0x80 0xCC 0x33 (8N1, LSB zuerst) bei 19200 / 38400 /
    57600 Baud (flash_sensor.py: hoechstens 57600, Standard 57600). Schmitt-Empfaenger mit Schwellen-Ecken, danach
    UART-Empfaenger-Modell: Startflanke erkennen, Abtastung in Bitmitte mit Taktfehler +-1.5 %, Bytes vergleichen.
    Reserve = kleinster Abstand eines Abtastpunkts zur naechsten Flanke (in Bitzeiten, ideal 0.5).

Datenblattwerte (lokale Dateien)
--------------------------------
- CH343: VIO 1.7-5.5 V; VIL <= 0.5 V, VIH >= 1.3 V bei VIO 1.8 V; Pull-up RXD 3/14/21 uA bei VIO 1.8 V,
  15/60/90 uA bei 3.3 V; VOL <= 0.4 V @ 3 mA, VOH >= VIO-0.4 V @ 2 mA (VIO 1.8 V); Taktfehler +-1.5 %
  (-40..85 degC): docs/datasheets/WCH_CH343_Datasheet_V1E.pdf S. 8 Tab. 6.2, S. 9 Tab. 6.3.
- Waveshare-Board: RXD-LED von VIO ueber 2 kOhm an RXD, TXD-LED ueber 4.7 kOhm, BAV99 an RXD/TXD:
  docs/references/Waveshare_CH343-USB-UART-Board_Schematic_2026-11-08.pdf.
- SN74AUP1G17: VT+ 0.91-1.29 V (VCC 1.65 V) / 1.37-1.77 V (2.3 V); VT- 0.47-0.84 V / 0.69-1.04 V; II <= 0.1 uA
  (25 degC), <= 0.5 uA (-40..85 degC); Ci 1.5 pF; VOL <= 0.35 V @ 1.9 mA (1.65 V):
  docs/datasheets/TI_SN74AUP1G17_Datasheet_SCES579J.pdf S. 5-7 Kap. 6.5.
- CC2340R5: GPIO-Uebergaenge bei VDDS 1.8 V 0->1 0.91/1.11/1.27 V, 1->0 0.59/0.75/0.91 V; VIH 0.8*VDDS, VIL 0.2*VDDS
  (S. 31-32 Tab. 7.21.4.1); CI GPIO 5 typ / 7 max pF (S. 32); VOL 0.20 V @ 2 mA, VOH 2.52 V @ 2 mA bei VDDS 3.0 V
  (S. 31): docs/datasheets/TI_CC2340R5_Datasheet_SWRS272F.pdf.
- XC6206P202: 1.960-2.040 V (+-2 %): docs/datasheets/Torex_XC6206_Datasheet_ETR0305-004b.pdf S. 5 Tab. E-1.
- LED-Modelle (rot/blau, min/mitte/max): ../led_rgb/led_models.inc (fit_led_models.py, TUOZHAN-Datenblatt S. 5).

ANNAHMEN (im Bericht so gekennzeichnet)
---------------------------------------
- Schwellen SN74AUP1G17 bei VCC 2.0 V linear zwischen den Datenblattstuetzstellen 1.65 V und 2.3 V interpoliert;
  zusaetzlich die Huellkurve "VT- >= Wert bei 1.65 V, VT+ <= Wert bei 2.3 V" (setzt Monotonie ueber VCC voraus).
- CH343-Pull-up bei VIO 2.0-2.2 V: Datenblatt nennt nur 1.8/3.3/5 V -> linear interpoliert, max. 30 uA (2.0 V)
  bzw. 39 uA (2.2 V); als Stromquelle modelliert (konservativ, ein Widerstand liefert bei Vpad > 0 weniger).
  CH343-VIL bei VIO 2.0-2.2 V: 0.5 V (Wert bei 1.8 V; steigt mit VIO -> konservativ).
- CC2340-Schwellen bei VDDS 2.0-2.2 V: Werte bei 1.8 V proportional zu VDDS skaliert.
- Ausgangswiderstand DIO6 bei VDDS 2.0 V: 480 Ohm (aus VOH 3.0 V: 0.48 V / 2 mA = 240 Ohm, x 2 fuer 2.0 V).
  CH343-TXD 200 Ohm (aus VOH VIO-0.4 V @ 2 mA). Puffer-Ausgang 184 Ohm (0.35 V / 1.9 mA).
- Kapazitaeten (keine Datenblattwerte, Schaetzung aus Padgroessen und Leitungslaengen im Layout Rev C):
    C_MID  Knoten R9/R10 bzw. R11/R12 (2 x 0402-Pad + Innenlagenleitung ca. 13 mm): nominal 1 pF, schlecht 3 pF
    C_TP   TP1/TP2 (Pad 1.5 mm + Via-in-Pad + Leitung ca. 9 mm):               nominal 2 pF, schlecht 3 pF
    C_AD   Pogo-Stift + Draht <= 3 cm + Puffer-Eingang 1.5 pF + Pull-up:        nominal 5 pF, schlecht 10 pF
    C_KAB  Fall "Puffer am Kabelende" (30 cm Litze): 40 pF  -> zeigt, warum der Puffer am Pogo-Kopf sitzen muss
    C_PIN  DIO20: CI 5-7 pF (DS) + Leitung 1-2 pF -> nominal 7 pF, schlecht 9 pF
    C_LED  Sperrschicht blaue LED (an DIO20 ueber R8, Anode an VDD = Wechselstrom-Masse): 0 / 15 / 30 pF
           (Datenblatt nennt keinen Wert)
- Leckstrom CC2340-Eingang DIO20: vernachlaessigt (Datenblatt nennt keinen Wert).
- UART-Empfaenger: Abtastung in Bitmitte nach erkannter Startflanke (CH343 und CC2340-UART sind 16-fach-Abtaster,
  Kriterium Reserve >= 0.20 Bit, ANNAHME).
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import spicetools  # noqa: E402

LEDINC = os.path.relpath(os.path.join(HERE, "..", "led_rgb", "led_models.inc"), HERE)
BAUDS = (19200, 38400, 57600)
BYTES = (0x55, 0x55, 0x00, 0xFF, 0x01, 0x80, 0xCC, 0x33)
CLK_ERR = 0.015                    # CH343 FD +-1.5 % (Tab. 6.3), fuer den CC2340-Empfaenger gleich angesetzt
CRIT_MARGIN = 0.20                 # Bit, ANNAHME
R1 = "10Meg"                        # Pull-up am Puffer-Eingang (hardware/programmer, R1)

# --------------------------------------------------------------------- Schwellen
def interp(v, x0, y0, x1, y1):
    return y0 + (y1 - y0) * (v - x0) / (x1 - x0)


def aup_thresholds(vcc):
    """SN74AUP1G17 (SCES579J S.5): (VT+min, VT+max, VT-min, VT-max) linear interpoliert (ANNAHME) und Huellkurve."""
    lin = (interp(vcc, 1.65, 0.91, 2.3, 1.37), interp(vcc, 1.65, 1.29, 2.3, 1.77),
           interp(vcc, 1.65, 0.47, 2.3, 0.69), interp(vcc, 1.65, 0.84, 2.3, 1.04))
    env = (0.91, 1.77, 0.47, 1.04)
    return lin, env


def cc2340_thresholds(vdd):
    """CC2340 GPIO bei 1.8 V (DS S.31) proportional skaliert (ANNAHME): (0->1 min, max, 1->0 min, max)."""
    k = vdd / 1.8
    return (0.91 * k, 1.27 * k, 0.59 * k, 0.91 * k)


def ch343_ipu_max(vio):
    """Pull-up-Strom RXD max: 21 uA @ 1.8 V, 90 uA @ 3.3 V (Tab. 6.2), linear interpoliert (ANNAHME)."""
    return interp(vio, 1.8, 21e-6, 3.3, 90e-6)


# --------------------------------------------------------------------- Netzlisten-Bausteine
def led(name, anode, cathode_node, model, off, rser):
    """LED wie in led_rgb: Diode + Offsetquelle (Exemplarlage) + Vorwiderstand."""
    return [f"D{name} {anode} a{name} {model}", f"VO{name} a{name} b{name} DC {{{off}}}",
            f"R{name} b{name} {cathode_node} {rser}"]


def pullup(name, node, vio, ipu):
    """CH343-Pull-up als Stromquelle nach VIO, die oberhalb VIO - 50 mV abregelt (kein Ueberschwingen ueber VIO)."""
    return [f"B{name} {vio} {node} I={ipu:.4g}*min(1,max(0,(v({vio})-v({node}))/0.05))"]


def head(title):
    return [f"* fluidi {title} - erzeugt von prog_uart.py (nicht von Hand aendern)", f".include {LEDINC}"]


def op(net, path, nodes):
    d = spicetools.run("\n".join(net), path, [f"v({n})" for n in nodes], "op")
    return {n: float(d[f"v({n})"][0]) for n in nodes}


# --------------------------------------------------------------------- (1) DC
def dc_cases():
    rows = []
    cir = os.path.join(HERE, "prog_uart_dc.cir")

    # A0: Ist-Zustand ohne Puffer, CH343-RXD am TP1; DIO6 low
    for vio in (1.8, 2.0):
        for ipu_lbl, ipu in (("min", 3e-6), ("typ", 14e-6), ("max", ch343_ipu_max(vio))):
            for off in ("OFF_R_MAX", "OFF_R_MIN"):
                net = head("A0") + [
                    f"VDD vdd 0 DC {vio}", f"VIO vio 0 DC {vio}",
                    "VDRV drv 0 DC 0", "RDRV drv dio6 480",
                    *led("RLED", "vdd", "dio6", "DR", "OFF_R_MID", 470),
                    "R9 dio6 mid 100k", "R10 mid tp1 100k",
                    *pullup("PU", "tp1", "vio", ipu),
                    *led("WSRX", "vio", "tp1", "DR", off, 2000)]
                v = op(net, cir, ["tp1"])["tp1"]
                rows.append(dict(fall="A0 ohne Puffer (Ist)", bedingung=f"VIO {vio} V, Pull-up {ipu_lbl} "
                                 f"{ipu*1e6:.0f} uA, Board-LED {off[6:]}", knoten="CH343-RXD (TP1)", pegel="low",
                                 v=v, grenze="<= 0.50 (CH343 VIL)", ok=v <= 0.5))

    # A1: Puffer am Pogo-Stift; Eingang mit Pull-up R1 an VIO, Leckstrom +-0.5 uA (worst, -40..85 degC)
    for vdd in (1.96, 2.04):
        for vio in (1.96, 2.04):
            lin, env = aup_thresholds(vio)
            for lvl, drv, ilk in (("low", 0.0, 0.5e-6), ("high", vdd, -0.5e-6)):
                net = head("A1") + [
                    f"VDD vdd 0 DC {vdd}", f"VIO vio 0 DC {vio}",
                    f"VDRV drv 0 DC {drv}", "RDRV drv dio6 480",
                    *led("RLED", "vdd", "dio6", "DR", "OFF_R_MIN", 470),
                    "R9 dio6 mid 100k", "R10 mid tp1 100k",
                    f"RPU tp1 vio {R1}", f"ILK 0 tp1 DC {ilk}"]
                v = op(net, cir, ["tp1"])["tp1"]
                if lvl == "low":
                    g_lin, g_env = lin[2], env[2]
                    ok = v <= g_env
                    gtxt = f"<= {g_env:.2f} (VT- min Huelle) / {g_lin:.2f} (interp.)"
                    res_lin, res_env = g_lin - v, g_env - v
                else:
                    g_lin, g_env = lin[1], env[1]
                    ok = v >= g_env
                    gtxt = f">= {g_env:.2f} (VT+ max Huelle) / {g_lin:.2f} (interp.)"
                    res_lin, res_env = v - g_lin, v - g_env
                rows.append(dict(fall="A1 Puffer-Eingang", bedingung=f"VDD {vdd} V, VIO {vio} V, Leck "
                                 f"{ilk*1e6:+.1f} uA, R1 {R1}", knoten="AUP1G17 A (TP1)", pegel=lvl, v=v,
                                 grenze=gtxt, ok=ok, reserve_huelle=res_env, reserve_interp=res_lin))

    # A1z: DIO6 noch hochohmig (Bootloader vor dem Sync, TRM S.464) bzw. Sensor ohne Speisung: nur R1 + Leck
    #      (Leck -0.1 uA bei 25 degC, -0.5 uA bei -40..85 degC, SCES579J S.7); rote LED/R6 haengen am Knoten DIO6
    for vio in (1.96, 2.04):
        lin, env = aup_thresholds(vio)
        for tlbl, ilk in (("25 degC", -0.1e-6), ("-40..85 degC", -0.5e-6)):
            net = head("A1z") + [f"VDD vdd 0 DC {vio}", f"VIO vio 0 DC {vio}",
                                 *led("RLED", "vdd", "dio6", "DR", "OFF_R_MIN", 470), "RHZ dio6 0 1e12",
                                 "R9 dio6 mid 100k", "R10 mid tp1 100k",
                                 f"RPU tp1 vio {R1}", f"ILK 0 tp1 DC {ilk}"]
            v = op(net, cir, ["tp1"])["tp1"]
            rows.append(dict(fall="A1z Ruhepegel, DIO6 hochohmig", bedingung=f"VDD = VIO = {vio} V, Leck "
                             f"{ilk*1e6:+.1f} uA ({tlbl}), R1 {R1}", knoten="AUP1G17 A (TP1)", pegel="high (Ruhe)",
                             v=v, grenze=f">= {env[3]:.2f} (VT- max Huelle, haelt high) / {env[1]:.2f} (VT+ max)",
                             ok=v >= env[3], reserve_huelle=v - env[3], reserve_interp=v - lin[1]))

    # A1o: Puffer-Ausgang low -> CH343-RXD (Pull-up + Board-LED)
    for vio in (1.96, 2.04):
        net = head("A1o") + [f"VIO vio 0 DC {vio}", "VY y0 0 DC 0", "RY y0 rxd 184",
                             *pullup("PU", "rxd", "vio", ch343_ipu_max(vio)), *led("WSRX", "vio", "rxd", "DR", "OFF_R_MIN", 2000)]
        v = op(net, cir, ["rxd"])["rxd"]
        rows.append(dict(fall="A1o Puffer-Ausgang", bedingung=f"VIO {vio} V, Pull-up max, Board-LED min",
                         knoten="CH343-RXD", pegel="low", v=v, grenze="<= 0.50 (CH343 VIL)", ok=v <= 0.5))

    # A2: Behelf: CH343-RXD direkt am R9-Pad 1 (DIO6), VDD = VIO = Labornetzteil
    for vdd in (2.0, 2.2):
        net = head("A2") + [f"VDD vdd 0 DC {vdd}", "VDRV drv 0 DC 0", "RDRV drv dio6 480",
                            *led("RLED", "vdd", "dio6", "DR", "OFF_R_MIN", 470),
                            *pullup("PU", "dio6", "vdd", ch343_ipu_max(vdd)),
                            *led("WSRX", "vdd", "dio6", "DR", "OFF_R_MIN", 2000),
                            "R9 dio6 mid 100k", "R10 mid tp1 100k", "RTP tp1 0 1e12"]
        v = op(net, cir, ["dio6"])["dio6"]
        rows.append(dict(fall="A2 Behelf R9-Pad", bedingung=f"VDD = VIO = {vdd} V, Pull-up max, beide LED min",
                         knoten="DIO6 = CH343-RXD", pegel="low", v=v, grenze="<= 0.50 (CH343 VIL)", ok=v <= 0.5))

    # A3: Behelf am FALSCHEN Pad (R9-Pad 2 = UART_TX_MID, hinter 100 kOhm)
    for ipu_lbl, ipu in (("min", 3e-6), ("max", ch343_ipu_max(2.0))):
        net = head("A3") + ["VDD vdd 0 DC 2.0", "VDRV drv 0 DC 0", "RDRV drv dio6 480",
                            *led("RLED", "vdd", "dio6", "DR", "OFF_R_MID", 470),
                            "R9 dio6 mid 100k", *pullup("PU", "mid", "vdd", ipu),
                            *led("WSRX", "vdd", "mid", "DR", "OFF_R_MAX", 2000),
                            "R10 mid tp1 100k", "RTP tp1 0 1e12"]
        v = op(net, cir, ["mid"])["mid"]
        rows.append(dict(fall="A3 Behelf falsches Pad (R9-Pad 2)", bedingung=f"VDD = VIO = 2.0 V, Pull-up {ipu_lbl} "
                         f"{ipu*1e6:.0f} uA", knoten="UART_TX_MID = CH343-RXD", pegel="low", v=v,
                         grenze="<= 0.50 (CH343 VIL)", ok=v <= 0.5))

    # B: Host -> Sensor-RX (DIO20), blaue LED + R8 nach VDD; CH343-TXD low
    for vdd, src in ((1.96, "Adapter min"), (2.00, "Adapter nom"), (2.04, "Adapter max"), (2.20, "Behelf"),
                     (1.80, "1.8 V (alt)")):
        for off in ("OFF_B_MIN", "OFF_B_MID"):
            net = head("B") + [f"VDD vdd 0 DC {vdd}", "VTX tx0 0 DC 0", "RTX tx0 tp2 200",
                               "R12 tp2 mid 100k", "R11 mid dio20 100k",
                               *led("BLED", "vdd", "dio20", "DB", off, 100)]
            v = op(net, cir, ["dio20"])["dio20"]
            vil = 0.2 * vdd
            t10 = cc2340_thresholds(vdd)[2]
            rows.append(dict(fall="B Sensor-RX", bedingung=f"VDD {vdd} V ({src}), LED blau {off[6:]}",
                             knoten="DIO20", pegel="low", v=v,
                             grenze=f"<= {vil:.2f} (VIL 0.2 VDDS) / 1->0 min {t10:.2f}", ok=v <= vil,
                             reserve_huelle=vil - v, reserve_interp=t10 - v))
    return rows


# --------------------------------------------------------------------- (2) Transient
STEP_BITS = 30                     # Sprung am Ende (30 Bit low, 30 Bit high) fuer die 10-90-%-Zeiten


def uart_pwl(baud, vhi, tr=10e-9):
    """PWL der Bytefolge (8N1), danach ein Sprung low/high zur Messung der Flankenzeiten.
    Rueckgabe: PWL-Text, Ende der Bytefolge [s], Ende gesamt [s]."""
    tb = 1.0 / baud
    bits = [1, 1]
    for b in BYTES:
        bits += [0] + [(b >> i) & 1 for i in range(8)] + [1]
    bits += [1] * 4
    t_bytes = len(bits) * tb
    bits += [0] * STEP_BITS + [1] * STEP_BITS
    pts, cur = [(0.0, vhi)], 1
    for i, b in enumerate(bits):
        if b != cur:
            pts += [(i * tb, vhi if cur else 0.0), (i * tb + tr, vhi if b else 0.0)]
            cur = b
    tend = len(bits) * tb
    pts.append((tend, vhi if cur else 0.0))
    return " ".join(f"{t:.9g} {v:.4g}" for t, v in pts), t_bytes, tend


def schmitt(t, v, vtp, vtm, init=1):
    """Digitalisieren mit Hysterese; Rueckgabe Flankenzeiten (linear interpoliert) und Pegel danach."""
    st, edges = init, []
    for i in range(1, len(v)):
        if st == 1 and v[i] < vtm:
            f = (v[i - 1] - vtm) / (v[i - 1] - v[i]) if v[i - 1] != v[i] else 0
            edges.append((t[i - 1] + f * (t[i] - t[i - 1]), 0))
            st = 0
        elif st == 0 and v[i] > vtp:
            f = (vtp - v[i - 1]) / (v[i] - v[i - 1]) if v[i - 1] != v[i] else 0
            edges.append((t[i - 1] + f * (t[i] - t[i - 1]), 1))
            st = 1
    return edges


def level_at(edges, tq, init=1):
    lv = init
    for te, l in edges:
        if te > tq:
            break
        lv = l
    return lv


def uart_decode(edges, baud, eps):
    """Empfaenger: Startflanke (1->0) suchen, Abtastung bei (k+0.5) Bit (Takt um eps verstimmt). Rueckgabe
    (Bytes, Reserve in Bit = kleinster Abstand Abtastpunkt-Flanke)."""
    tb = (1.0 / baud) * (1 + eps)
    out, margin = [], 0.5
    times = np.array([e[0] for e in edges]) if edges else np.array([])
    i, tlast = 0, -1.0
    while i < len(edges):
        te, lv = edges[i]
        if lv != 0 or te <= tlast:
            i += 1
            continue
        samples = [te + (k + 0.5) * tb for k in range(10)]
        bits = [level_at(edges, s) for s in samples]
        val = sum(b << k for k, b in enumerate(bits[1:9]))
        ok = bits[0] == 0 and bits[9] == 1
        out.append(val if ok else -1)
        for s in samples:
            if times.size:
                margin = min(margin, float(np.min(np.abs(times - s))) / (1.0 / baud))
        tlast = samples[9]
        # naechste Startflanke erst nach dem Stoppbit-Abtastpunkt suchen
        while i < len(edges) and edges[i][0] <= tlast:
            i += 1
    return out, margin


def tran_tx(baud, cset, vdd=2.0, vio=2.0):
    """Sensor-TX -> R9 -> R10 -> TP1 -> Puffer-Eingang (Pull-up R1, Leck +0.5 uA)."""
    cmid, ctp, cad = cset
    pwl, t_bytes, tend = uart_pwl(baud, vdd)
    tb = 1.0 / baud
    net = head("TX") + [f"VDD vdd 0 DC {vdd}", f"VIO vio 0 DC {vio}",
                        f"VDRV drv 0 PWL({pwl})", "RDRV drv dio6 480",
                        *led("RLED", "vdd", "dio6", "DR", "OFF_R_MIN", 470),
                        "R9 dio6 mid 100k", f"CMID mid 0 {cmid}p", "R10 mid tp1 100k",
                        f"CTP tp1 0 {ctp}p", f"CAD tp1 0 {cad}p", f"RPU tp1 vio {R1}", "ILK 0 tp1 DC 0.5u"]
    d = spicetools.run("\n".join(net), os.path.join(HERE, "prog_uart_tx.cir"), ["v(tp1)", "v(dio6)"],
                       f"tran {tb/400:.4g} {tend:.6g} 0 {tb/200:.4g}")
    return d, tb, t_bytes


def tran_rx(baud, cmid, cpin, cled, vdd):
    """Host-TX (CH343) -> TP2 -> R12 -> R11 -> DIO20 (CI + LED blau min ueber R8 nach VDD)."""
    pwl, t_bytes, tend = uart_pwl(baud, vdd)
    tb = 1.0 / baud
    net = head("RX") + [f"VDD vdd 0 DC {vdd}", f"VTX tx0 0 PWL({pwl})", "RTX tx0 tp2 200", "CTP2 tp2 0 30p",
                        "R12 tp2 mid 100k", f"CMID mid 0 {cmid}p", "R11 mid dio20 100k", f"CPIN dio20 0 {cpin}p",
                        *led("BLED", "vdd", "dio20", "DB", "OFF_B_MIN", 100), f"CLED vdd aBLED {cled}p"]
    d = spicetools.run("\n".join(net), os.path.join(HERE, "prog_uart_rx.cir"), ["v(dio20)", "v(tp2)"],
                       f"tran {tb/400:.4g} {tend:.6g} 0 {tb/200:.4g}")
    return d, tb, t_bytes


def rise_fall(t, v, t_bytes, tb):
    """10-90-%-Zeiten am Sprung nach der Bytefolge (30 Bit low, 30 Bit high), bezogen auf die eingeschwungenen
    Pegel am Ende der Low- bzw. High-Phase. Rueckgabe (t_steigend, t_fallend, V_low, V_high)."""
    t_fall0, t_rise0 = t_bytes, t_bytes + STEP_BITS * tb
    vlo = float(np.interp(t_rise0 - 0.01 * tb, t, v))
    vhi = float(np.interp(t_fall0 - 0.01 * tb, t, v))
    lo, hi = vlo + 0.1 * (vhi - vlo), vlo + 0.9 * (vhi - vlo)

    def cross(level, rising, t0):
        m = t >= t0
        tt, vv = t[m], v[m]
        for i in range(1, len(vv)):
            if (rising and vv[i - 1] < level <= vv[i]) or (not rising and vv[i - 1] > level >= vv[i]):
                f = (level - vv[i - 1]) / (vv[i] - vv[i - 1])
                return tt[i - 1] + f * (tt[i] - tt[i - 1])
        return float("nan")
    tf = cross(lo, False, t_fall0) - cross(hi, False, t_fall0)
    tr = cross(hi, True, t_rise0) - cross(lo, True, t_rise0)
    return tr, tf, vlo, vhi


def evaluate(d, tb, baud, sig, thr_sets, t_bytes):
    t, v = d["time"], d[sig]
    res = []
    for name, (vtp, vtm) in thr_sets.items():
        edges = [e for e in schmitt(t, v, vtp, vtm) if e[0] < t_bytes]
        worst, ok_all = 0.5, True
        for eps in (-CLK_ERR, 0.0, CLK_ERR):
            got, m = uart_decode(edges, baud, eps)
            ok_all &= tuple(got) == BYTES
            worst = min(worst, m)
        res.append((name, ok_all, worst))
    return res


def tran_cases():
    rows, waves = [], {}
    lin, env = aup_thresholds(2.0)
    thr_tx = {"interp. VT+max/VT-min": (lin[1], lin[2]), "interp. VT+min/VT-max": (lin[0], lin[3]),
              "Huelle VT+1.77/VT-0.47": (env[1], env[2])}
    csets = {"nominal (1/2/5 pF)": (1, 2, 5), "schlecht (3/3/10 pF)": (3, 3, 10),
             "Puffer am Kabelende (1/2/40 pF)": (1, 2, 40)}
    for baud in BAUDS:
        for cname, cs in csets.items():
            d, tb, t_bytes = tran_tx(baud, cs)
            tr, tf, vlo, vhi = rise_fall(d["time"], d["v(tp1)"], t_bytes, tb)
            for name, ok, m in evaluate(d, tb, baud, "v(tp1)", thr_tx, t_bytes):
                rows.append(dict(richtung="Sensor->Host (TP1, Puffer)", baud=baud, kap=cname, schwellen=name,
                                 v_low=vlo, v_high=vhi,
                                 t_rise_us=tr * 1e6, t_fall_us=tf * 1e6, bytes_ok=ok, reserve_bit=m,
                                 ok=ok and m >= CRIT_MARGIN))
            if baud == 57600:
                waves[("TX", cname)] = d
    for vdd in (2.0, 2.2):
        th = cc2340_thresholds(vdd)
        thr_rx = {"0->1 max / 1->0 min": (th[1], th[2]), "0->1 min / 1->0 max": (th[0], th[3])}
        for baud in BAUDS:
            for cname, (cm, cp, cl) in {"nominal, LED 0 pF": (1, 7, 0), "schlecht, LED 15 pF": (3, 9, 15),
                                        "schlecht, LED 30 pF": (3, 9, 30)}.items():
                d, tb, t_bytes = tran_rx(baud, cm, cp, cl, vdd)
                tr, tf, vlo, vhi = rise_fall(d["time"], d["v(dio20)"], t_bytes, tb)
                for name, ok, m in evaluate(d, tb, baud, "v(dio20)", thr_rx, t_bytes):
                    rows.append(dict(richtung=f"Host->Sensor (DIO20), VDD {vdd} V", baud=baud, kap=cname,
                                     schwellen=name, v_low=vlo, v_high=vhi,
                                     t_rise_us=tr * 1e6, t_fall_us=tf * 1e6, bytes_ok=ok,
                                     reserve_bit=m, ok=ok and m >= CRIT_MARGIN))
                if baud == 57600 and vdd == 2.0:
                    waves[("RX", cname)] = d
    return rows, waves


def plot(waves):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    lin, env = aup_thresholds(2.0)
    fig, ax = plt.subplots(2, 1, figsize=(11, 7), sharex=False)
    for (k, cname), d in waves.items():
        a = ax[0] if k == "TX" else ax[1]
        sig = "v(tp1)" if k == "TX" else "v(dio20)"
        a.plot(d["time"] * 1e6, d[sig], label=cname, lw=1)
    d0 = waves[("TX", "nominal (1/2/5 pF)")]
    ax[0].plot(d0["time"] * 1e6, d0["v(dio6)"], "k:", lw=0.8, label="DIO6 (Quelle)")
    for y, s in ((env[1], "VT+ max (Huelle)"), (env[2], "VT- min (Huelle)"), (lin[1], "VT+ max interp."),
                 (lin[2], "VT- min interp.")):
        ax[0].axhline(y, ls="--", lw=0.6, color="gray")
        ax[0].text(0, y, s, fontsize=7, va="bottom")
    th = cc2340_thresholds(2.0)
    for y in th:
        ax[1].axhline(y, ls="--", lw=0.6, color="gray")
    ax[0].set_title("Sensor-TX -> TP1 -> Puffer-Eingang, 57600 Baud (ANNAHME Kapazitaeten)")
    ax[1].set_title("CH343-TXD -> TP2 -> DIO20 (blaue LED min), VDD 2.0 V, 57600 Baud")
    for a in ax:
        a.set_xlim(0, 400)
        a.set_ylabel("V")
        a.grid(alpha=0.3)
        a.legend(fontsize=7, loc="lower right")
    ax[1].set_xlabel("t [us]")
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, "prog_uart_waveforms.png"), dpi=110)


def main():
    dc = dc_cases()
    tr, waves = tran_cases()
    with open(os.path.join(HERE, "prog_uart_dc.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["fall", "bedingung", "knoten", "pegel", "v", "grenze", "ok",
                                           "reserve_huelle", "reserve_interp"])
        w.writeheader()
        for r in dc:
            w.writerow(r)
    with open(os.path.join(HERE, "prog_uart_tran.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(tr[0].keys()))
        w.writeheader()
        for r in tr:
            w.writerow(r)
    L = ["fluidi - prog_uart.py (ngspice -b), Erstprogrammierung: Pegel und Zeitverhalten", "",
         "(1) DC-Pegel [V]", "| Fall | Bedingung | Knoten | Pegel | V | Grenze | ok | Reserve Huelle / interp. |",
         "|---|---|---|---|---|---|---|---|"]
    for r in dc:
        res = ""
        if r.get("reserve_huelle") is not None:
            res = f"{r['reserve_huelle']*1e3:+.0f} / {r['reserve_interp']*1e3:+.0f} mV"
        L.append(f"| {r['fall']} | {r['bedingung']} | {r['knoten']} | {r['pegel']} | {r['v']:.3f} | {r['grenze']} | "
                 f"{'ja' if r['ok'] else 'NEIN'} | {res} |")
    L += ["", f"(2) Transient: Bytes {' '.join('%02X' % b for b in BYTES)}, Taktfehler +-{CLK_ERR*100:.1f} %, "
          f"Kriterium Reserve >= {CRIT_MARGIN} Bit", "| Richtung | Baud | Kapazitaeten | Schwellen | V low / high "
          "eingeschw. | t10-90 steigend [us] | fallend [us] | Bytes ok | Reserve [Bit] | ok |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for r in tr:
        L.append(f"| {r['richtung']} | {r['baud']} | {r['kap']} | {r['schwellen']} | {r['v_low']:.3f} / "
                 f"{r['v_high']:.3f} | {r['t_rise_us']:.2f} | "
                 f"{r['t_fall_us']:.2f} | {'ja' if r['bytes_ok'] else 'NEIN'} | {r['reserve_bit']:.3f} | "
                 f"{'ja' if r['ok'] else 'NEIN'} |")
    open(os.path.join(HERE, "prog_uart_report.txt"), "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    plot(waves)


if __name__ == "__main__":
    main()
