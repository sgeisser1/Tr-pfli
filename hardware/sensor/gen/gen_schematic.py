#!/usr/bin/env python3
"""fluidi Sensor Rev B - Schaltplan-Generator (KiCad 10, S-Expression direkt geschrieben).

Erzeugt im Ordner hardware/sensor/:
  fluidi_sensor.kicad_sch, fluidi_sensor.kicad_pro, sym-lib-table, fp-lib-table
  gen/intended_netlist.json  (Soll-Netzliste fuer check_netlist.py)

Verbindungen werden mit kurzen Leitungsstuecken + Netzlabels bzw. Power-Symbolen hergestellt.
Bauteil- und Netzdefinition: parts.py. Projektbibliothek: gen_lib.py (wird zuerst ausgefuehrt).
Aufruf: .venv/bin/python hardware/sensor/gen/gen_schematic.py
"""
import copy
import datetime
import json
import math
import os
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_lib  # noqa: E402
import parts  # noqa: E402
import sexpr  # noqa: E402
from sexpr import Q  # noqa: E402

PRJ = os.path.normpath(os.path.join(HERE, ".."))
NAME = "fluidi_sensor"
KICAD_SYM = "/usr/share/kicad/symbols"
NS = uuid.UUID("6f1d2c3a-0b6e-4c9a-9a51-f1a1d1000000")
ROOT_UUID = str(uuid.uuid5(NS, "root"))
REV = "B"
DATE = "2026-11-07"
STUB = 2.54


def uid(*k):
    return str(uuid.uuid5(NS, "/".join(map(str, k))))


def f(v):
    return f"{round(v, 4):g}"


def font(size=1.27, justify=None, hide=False):
    e = ["effects", ["font", ["size", f(size), f(size)]]]
    if justify:
        e.append(["justify"] + justify.split())
    if hide:
        e.append(["hide", "yes"])
    return e


# ------------------------------------------------------------------ Bibliothekssymbole
_LIBCACHE = {}


def lib_symbol(lib_id):
    lib, name = lib_id.split(":")
    if lib not in _LIBCACHE:
        path = os.path.join(gen_lib.LIBDIR, "fluidi.kicad_sym") if lib == "fluidi" else \
            os.path.join(KICAD_SYM, lib + ".kicad_sym")
        _LIBCACHE[lib] = sexpr.parse(open(path).read())
    node = next(x for x in _LIBCACHE[lib] if isinstance(x, list) and x[0] == "symbol" and x[1] == name)
    if sexpr.find(node, "extends"):
        raise ValueError(f"abgeleitetes Symbol nicht unterstuetzt: {lib_id}")
    n = copy.deepcopy(node)
    n[1] = Q(lib_id)
    return n


def lib_pins(node):
    pins = []

    def walk(n):
        for x in n:
            if isinstance(x, list):
                if x[0] == "pin":
                    at = sexpr.find(x, "at")
                    pins.append(dict(num=sexpr.find(x, "number")[1], name=sexpr.find(x, "name")[1], type=x[1],
                                     x=float(at[1]), y=float(at[2]), ang=int(float(at[3])),
                                     hidden=sexpr.find(x, "hide") is not None or "hide" in x))
                else:
                    walk(x)
    walk(node)
    return pins


def lib_prop(node, key):
    for p in sexpr.find_all(node, "property"):
        if p[1] == key:
            return p[2]
    return ""


def transform(px, py, rot, X, Y):
    """Bibliothekskoordinate (y nach oben) -> Schaltplankoordinate (y nach unten), Rotation gegen Uhrzeiger."""
    r = math.radians(rot)
    xr = px * math.cos(r) - py * math.sin(r)
    yr = px * math.sin(r) + py * math.cos(r)
    return X + xr, Y - yr


def direction(ang):
    r = math.radians(ang)
    return round(math.cos(r)), -round(math.sin(r))


# ------------------------------------------------------------------ Schaltplan-Aufbau
class Sheet:
    def __init__(self):
        self.libs = {}
        self.items = []
        self.pwr_n = 0
        self.intended = {}

    def use(self, lib_id):
        if lib_id not in self.libs:
            self.libs[lib_id] = lib_symbol(lib_id)
        return self.libs[lib_id]

    def wire(self, x1, y1, x2, y2):
        self.items.append(["wire", ["pts", ["xy", f(x1), f(y1)], ["xy", f(x2), f(y2)]],
                           ["stroke", ["width", "0"], ["type", "default"]], ["uuid", Q(uid("w", x1, y1, x2, y2))]])

    def label(self, name, x, y, d):
        ang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[d]
        just = "left bottom" if ang in (0, 90) else "right bottom"
        self.items.append(["label", Q(name), ["at", f(x), f(y), str(ang)], font(1.27, just),
                           ["uuid", Q(uid("l", name, x, y))]])

    def text(self, t, x, y, size=1.0):
        self.items.append(["text", Q(t), ["exclude_from_sim", "no"], ["at", f(x), f(y), "0"],
                           font(size, "left top"), ["uuid", Q(uid("t", t[:30], x, y))]])

    def junction(self, x, y):
        self.items.append(["junction", ["at", f(x), f(y)], ["diameter", "0"], ["color", "0", "0", "0", "0"],
                           ["uuid", Q(uid("j", x, y))]])

    def no_connect(self, x, y):
        self.items.append(["no_connect", ["at", f(x), f(y)], ["uuid", Q(uid("nc", x, y))]])

    def power(self, net, x, y, body_dir):
        """Power-Symbol (GND/VDD) bzw. PWR_FLAG, Koerper in Richtung body_dir."""
        if net == "PWR_FLAG":
            lib_id, base = "power:PWR_FLAG", 90
            self.pwr_n += 1
            ref = f"#FLG{self.pwr_n:02d}"
            val = "PWR_FLAG"
        else:
            lib_id = f"power:{net}"
            base = 270 if net == "GND" else 90
            self.pwr_n += 1
            ref = f"#PWR{self.pwr_n:03d}"
            val = net
        node = self.use(lib_id)
        dang = {(1, 0): 0, (-1, 0): 180, (0, -1): 90, (0, 1): 270}[body_dir]
        rot = (dang - base) % 360
        tx, ty = transform(0, -3.0 if base == 270 else 3.0, rot, x, y)
        sym = ["symbol", ["lib_id", Q(lib_id)], ["at", f(x), f(y), str(rot)], ["unit", "1"],
               ["exclude_from_sim", "no"], ["in_bom", "no"], ["on_board", "yes"], ["dnp", "no"],
               ["uuid", Q(uid("p", ref))],
               ["property", Q("Reference"), Q(ref), ["at", f(x), f(y), "0"], font(1.27, hide=True)],
               ["property", Q("Value"), Q(val), ["at", f(tx), f(ty), "0"], font(1.0)],
               ["property", Q("Footprint"), Q(""), ["at", f(x), f(y), "0"], font(1.27, hide=True)],
               ["property", Q("Datasheet"), Q(""), ["at", f(x), f(y), "0"], font(1.27, hide=True)],
               ["pin", Q("1"), ["uuid", Q(uid("pp", ref))]],
               ["instances", ["project", Q(NAME), ["path", Q("/" + ROOT_UUID), ["reference", Q(ref)],
                                                     ["unit", "1"]]]]]
        self.items.append(sym)
        return node

    def connect(self, net, px, py, d):
        """Leitungsstueck vom Pin nach aussen, am Ende Label oder Power-Symbol."""
        ex, ey = px + d[0] * STUB, py + d[1] * STUB
        if net == "NC":
            self.no_connect(px, py)
            return
        self.wire(px, py, ex, ey)
        if net in ("GND", "VDD"):
            self.power(net, ex, ey, d)
        else:
            self.label(net, ex, ey, d)

    def component(self, c):
        node = self.use(c["lib"])
        pdb = parts.PARTDB[c["key"]]
        X, Y, rot = c["x"], c["y"], c["rot"]
        pins = lib_pins(node)
        # Feldpositionen
        xs = [transform(p["x"], p["y"], rot, X, Y)[0] for p in pins]
        ys = [transform(p["x"], p["y"], rot, X, Y)[1] for p in pins]
        big = len(pins) > 4
        if big:
            rx, ry, vx, vy, just = min(xs), min(ys) - 3.81, min(xs), max(ys) + 6.35, "left"
            if c["lib"].startswith("74xGxx") or "TMP1075" in c["lib"]:
                rx, ry = X + 6.0, Y - 6.5
                vx, vy = X + 6.0, Y + 8.0
        elif rot in (90, 270):
            rx, ry, vx, vy, just = X, Y - 2.54, X, Y + 3.0, None
        elif any(direction(p["ang"] + rot)[1] == 0 for p in pins) and len(pins) > 1:
            # Pins waagrecht (Quarz, Taster, LED): Felder oberhalb
            top = min(ys) - (4.5 if c["lib"].endswith("LED_ARGB") else 3.2)
            rx, ry, vx, vy, just = X, top - 2.0, X, top, None
        else:
            rx, ry, vx, vy, just = X + 2.0, Y - 1.0, X + 2.0, Y + 1.5, "left"
        props = [("Reference", c["ref"], rx, ry, False, just), ("Value", c["val"], vx, vy, False, just),
                 ("Footprint", c["fp"], X, Y, True, None),
                 ("Datasheet", pdb[4] or lib_prop(node, "Datasheet"), X, Y, True, None),
                 ("Description", pdb[5] + (("; " + c["note"]) if c["note"] else ""), X, Y, True, None),
                 ("LCSC", pdb[2], X, Y, True, None), ("Hersteller", pdb[0], X, Y, True, None),
                 ("MPN", pdb[1], X, Y, True, None), ("JLC", pdb[3], X, Y, True, None)]
        sym = ["symbol", ["lib_id", Q(c["lib"])], ["at", f(X), f(Y), str(rot)], ["unit", "1"],
               ["exclude_from_sim", "no"], ["in_bom", "no" if c["key"] == "PCB" else "yes"],
               ["on_board", "yes"], ["dnp", "yes" if c["dnp"] else "no"], ["uuid", Q(uid("s", c["ref"]))]]
        for k, v, x, y, hide, j in props:
            sym.append(["property", Q(k), Q(v), ["at", f(x), f(y), "0"], font(1.27, j, hide)])
        for p in pins:
            sym.append(["pin", Q(p["num"]), ["uuid", Q(uid("sp", c["ref"], p["num"]))]])
        sym.append(["instances", ["project", Q(NAME), ["path", Q("/" + ROOT_UUID), ["reference", Q(c["ref"])],
                                                         ["unit", "1"]]]])
        self.items.append(sym)
        # Verbindungen
        self.intended[c["ref"]] = {}
        pwr = {}
        for p in pins:
            net = c["conns"].get(p["num"])
            if net is None:
                if p["hidden"] or p["type"] == "no_connect":
                    continue
                raise ValueError(f"{c['ref']} Pin {p['num']} ({p['name']}) ohne Netz")
            px, py = transform(p["x"], p["y"], rot, X, Y)
            d = direction(p["ang"] + 180 + rot)
            if net != "NC":
                self.intended[c["ref"]][p["num"]] = net
            if net in ("GND", "VDD") and len(pins) > 4:
                pwr.setdefault((net, d, round(px if d[1] == 0 else py, 3)), []).append((px, py))
                continue
            self.connect(net, px, py, d)
        # gleichartige Power-Pins eines ICs (gleiche Seite) mit einer Leitung verbinden, ein Symbol
        for (net, d, _), pts in pwr.items():
            ends = sorted(((px + d[0] * STUB, py + d[1] * STUB) for px, py in pts),
                          key=lambda e: (e[1], e[0]) if d[1] == 0 else (e[0], e[1]))
            for (px, py), (ex, ey) in zip(pts, [(px + d[0] * STUB, py + d[1] * STUB) for px, py in pts]):
                self.wire(px, py, ex, ey)
            for a, b in zip(ends, ends[1:]):
                self.wire(a[0], a[1], b[0], b[1])
            for e in ends[1:-1]:
                self.junction(*e)
            if d[1] == 0:   # waagrechte Stummel: Symbol am oberen (VDD) bzw. unteren (GND) Ende
                ex, ey = ends[0] if net == "VDD" else ends[-1]
                if len(ends) > 1:
                    self.junction(ex, ey)
                    ey2 = ey - STUB if net == "VDD" else ey + STUB
                    self.wire(ex, ey, ex, ey2)
                    ey = ey2
                self.power(net, ex, ey, (0, -1) if net == "VDD" else (0, 1))
            else:
                ex, ey = ends[0]
                self.power(net, ex, ey, d)
        unknown = set(c["conns"]) - {p["num"] for p in pins}
        if unknown:
            raise ValueError(f"{c['ref']}: unbekannte Pins {unknown}")

    def flag(self, net, x, y):
        """PWR_FLAG an ein Netz haengen (Leitung nach oben, Label bzw. Power-Symbol unten)."""
        self.power("PWR_FLAG", x, y, (0, -1))
        self.wire(x, y, x, y + STUB)
        if net in ("GND", "VDD"):
            self.power(net, x, y + STUB, (0, 1))
        else:
            self.label(net, x, y + STUB, (0, 1))

    def write(self, path):
        tb = ["title_block", ["title", Q("fluidi Sensor - Schaltplan")], ["date", Q(DATE)], ["rev", Q(REV)],
              ["company", Q("fluidi (Projekt Tr-pfli)")],
              ["comment", "1", Q("A-32 (D-006), Messkette D3 (D-018), Kopf V4 (D-019): CC2340R52, TMP1075N, CR2032")],
              ["comment", "2", Q("Generiert: hardware/sensor/gen/gen_schematic.py - nicht von Hand aendern")],
              ["comment", "3", Q("Revisionsstand Rev B, Silkscreen 'fluidi Rev B' im Layout")],
              ["comment", "4", Q("4 Lagen 1.6 mm, Economic PCBA, ENIG")]]
        root = ["kicad_sch", ["version", "20250114"], ["generator", Q("eeschema")], ["generator_version", Q("9.0")],
                ["uuid", Q(ROOT_UUID)], ["paper", Q("A3")], tb,
                ["lib_symbols"] + list(self.libs.values())] + self.items + \
               [["sheet_instances", ["path", Q("/"), ["page", Q("1")]]], ["embedded_fonts", "no"]]
        with open(path, "w") as fh:
            fh.write(sexpr.dump(root) + "\n")


NOTES = [
    (4, 5, "ENERGIEPFAD\n"
           "CR2032 (Panasonic) im Keystone 3034, 90 Grad gedreht (Mechanik S-01)\n"
           "-> AO3401A Verpolschutz (D = Zelle+, S = VDD, G = GND) -> VDD, kein Regler\n"
           "(VDDS 1.71-3.8 V, DS S.18). Puffer 4 x 100 uF im Prototyp (D-013).\n"
           "Abschaltung 2.4 V unter Last an der Zellklemme (E1), SPICE simulation/spice.\n"
           "Kein Pad auf VBAT/VDD: AO3401A leitet in beide Richtungen (REQ-SAF-CC-03)."),
    (46, 5, "SoC CC2340R52E0RGER (QFN24, DS S.7 Abb. 6-2)\n"
            "Entkopplung nach HW-Guide SWRA834A S.5 Abb. 3-1, auf RGE-Pins uebertragen:\n"
            "VDDS 11/18/24 je 100 nF + 10 uF; VDDR 2/20 je 100 nF + 10 uF an L1;\n"
            "VDDD 1 uF; RSTN 100 k + 100 nF; 48 MHz ohne externe C (Cap-Array, DS S.26)."),
    (100, 5, "HF  LC-Filter 1.5 pF / 2.7 nH / 1.5 pF, DC-Block 15 pF, Pi-Netz 0 R + 2 x DNM\n"
             "(HW-Guide S.5). ESD-Diode der Referenz (TPD1E0B04) nicht vorgesehen.\n"
             "Antenne AN043 oben, Keepout nach AN043 (FLOORPLAN_OPTIONS Kap. 1)."),
    (104, 30, "PROGRAMMIERUNG (REQ-SAF-CC-03, Auflagen R2-A1...A4)\n"
              "Barriere 1: Dummy-Zellen-Adapter einteilig, statt der Zelle im Halter,\n"
              "  Speisung nur ueber die Halterkontakte, VDD 1.8-2.0 V, 1.8-V-UART (R2-A2).\n"
              "Barriere 2: je Pad 2 x 100 k, beide im Elektronikraum, getrennte\n"
              "  Loetstoppoeffnungen, Abstand gegen Loetbruecke/Wasserfilm (R2-A3).\n"
              "Grenze (R2-A1): Fehlerfall <= 10 mA, Ladung <= 1 % C = 2.25 mAh\n"
              "  (Maxell Warnings S.2, Panasonic Handbook S.1).\n"
              "Pads RX/TX im Zellfach ausserhalb der Zellflaeche, keine Vias (R2-W01).\n"
              "Kein nRST-, SWD- oder VDD-Pad. ROM-Bootloader: SW1 (DIO21) beim\n"
              "  Einschalten gedrueckt, RX = DIO20, TX = DIO6 (TRM S.464).\n"
              "TP3 GND (Fach); TP4 MEAS_CLK, TP5 PROBE_SENSE auf der B-Seite des\n"
              "  Elektronikbands: nur messen, keine Quelle (Abstimmung sicherheit)."),
    (4, 66, "MESSKETTE D3 (D-018)  Q2 AO3401A schaltet OSC_PWR (DIO11 low = an, R13 haelt aus).\n"
            "U2 SN74LVC1G14: Y -> R3 1 k -> A, Sondenknoten PROBE_SENSE gegen GND (Innenlagen),\n"
            "17-36 MHz; R3 auf 10 k umloetbar (Variante A). Cref1 22 pF (DIO8 low = zu).\n"
            "Teiler /8: U4-U6 SN74LVC1G80, D an /Q -> MEAS_CLK (DIO24, T3C0). Cref2 entfaellt.\n"
            "TP5 PROBE_SENSE (B-Seite, VNA). Firmware: kein I2C waehrend der Messung."),
    (4, 32, "TEMPERATUR  U3 TMP1075NDRLR + C24 im Sondenkragen\n"
            "(FLOORPLAN_OPTIONS Option f), R4/R5 im Band. SENS_PWR = DIO12.\n"
            "Adresse 0x48 (A0 = GND, DS S.14 Tab. 7-3). SWD + Pulls DIO16/17 aus (E3)."),
    (102, 61, "BEDIENUNG  RGB-LED gem. Anode an VDD,\n"
              "Kathode ueber R an GPIO (low = an).\n"
              "DIO6 = LED_R + UART-TX, DIO20 = LED_B + UART-RX.\n"
              "SW1 TS-1088 (H 2.0 mm) nach GND."),
]


def main():
    gen_lib.main()
    sh = Sheet()
    for c in parts.COMPONENTS:
        sh.component(c)
    for net, x, y in parts.FLAGS:
        sh.flag(net, parts.g(x), parts.g(y))
    for x, y, t in NOTES:
        sh.text(t, parts.g(x), parts.g(y))
    sh.write(os.path.join(PRJ, NAME + ".kicad_sch"))
    # Projektdateien
    pro = {"meta": {"filename": NAME + ".kicad_pro", "version": 3},
           "erc": {"erc_exclusions": [], "meta": {"version": 0}, "pin_map": [], "rule_severities": {}},
           "schematic": {"meta": {"version": 1}},
           "text_variables": {"REV": REV}}
    with open(os.path.join(PRJ, NAME + ".kicad_pro"), "w") as fh:
        json.dump(pro, fh, indent=2)
    # Projekt-Bibliothekstabellen: Projektbibliothek + benutzte KiCad-Standardbibliotheken ueber
    # ${KICAD10_SYMBOL_DIR}/${KICAD10_FOOTPRINT_DIR} (gleich unter WSL und Windows, unabhaengig von der Benutzerkonfiguration)
    sym_libs = sorted({c["lib"].split(":")[0] for c in parts.COMPONENTS} | {"power"})
    fp_libs = sorted({c["fp"].split(":")[0] for c in parts.COMPONENTS})
    lines = ['(sym_lib_table', '  (version 7)']
    for lib in sym_libs:
        uri = "${KIPRJMOD}/lib/fluidi.kicad_sym" if lib == "fluidi" else "${KICAD10_SYMBOL_DIR}/" + lib + ".kicad_sym"
        lines.append(f'  (lib (name "{lib}")(type "KiCad")(uri "{uri}")(options "")(descr ""))')
    with open(os.path.join(PRJ, "sym-lib-table"), "w") as fh:
        fh.write("\n".join(lines + [")"]) + "\n")
    lines = ['(fp_lib_table', '  (version 7)']
    for lib in fp_libs:
        uri = "${KIPRJMOD}/lib/fluidi.pretty" if lib == "fluidi" else "${KICAD10_FOOTPRINT_DIR}/" + lib + ".pretty"
        lines.append(f'  (lib (name "{lib}")(type "KiCad")(uri "{uri}")(options "")(descr ""))')
    with open(os.path.join(PRJ, "fp-lib-table"), "w") as fh:
        fh.write("\n".join(lines + [")"]) + "\n")
    with open(os.path.join(HERE, "intended_netlist.json"), "w") as fh:
        json.dump(sh.intended, fh, indent=1, sort_keys=True)
    n_parts = sum(1 for c in parts.COMPONENTS)
    print(f"Schaltplan geschrieben: {NAME}.kicad_sch ({n_parts} Symbole, {len(sh.libs)} Bibliothekssymbole)")


if __name__ == "__main__":
    main()
