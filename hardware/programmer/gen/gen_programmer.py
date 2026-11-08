#!/usr/bin/env python3
"""fluidi Programmieradapter Rev 1 - Schaltplan-Generator (KiCad 10, S-Expression direkt geschrieben).

Nutzt die Bausteine des Sensor-Generators (hardware/sensor/gen/gen_schematic.py: Pin-Transformation, Stummel,
Labels, Power-Symbole). Abgeleitete KiCad-Symbole (XC6206PxxxMR -> APE8865N, 74AUP1G17 -> 74LVC1G17) werden
in eine Projektbibliothek "fluidi_programmer" aufgeloest (flach), damit ERC ohne lib_symbol-Warnungen laeuft.

Erzeugt in hardware/programmer/:
  fluidi_programmer.kicad_sch, fluidi_programmer.kicad_pro, sym-lib-table, fp-lib-table,
  lib/fluidi_programmer.kicad_sym,
  gen/intended_netlist.json (Soll-Netzliste fuer check_netlist)
Aufruf: .venv/bin/python hardware/programmer/gen/gen_programmer.py   (bzw. run_all.sh: + ERC + PDF + Netzlistenpruefung)

Schaltung und Begruendung: hardware/programmer/README.md. Pinbelegungen:
  XC6206 SOT-23: 1 VSS, 2 VOUT, 3 VIN  (docs/datasheets/Torex_XC6206_Datasheet_ETR0305-004b.pdf S. 2 "Pin Assignment")
  SN74AUP1G17 DBV: 1 NC, 2 A, 3 GND, 4 Y, 5 VCC (docs/datasheets/TI_SN74AUP1G17_Datasheet_SCES579J.pdf S. 3)
  Waveshare CH343 USB UART Board: H1 1 +5V / 2 GND / 3 +3.3V / 4 GND; H3 Jumper 3 +5V / 2 VIO / 1 +3.3V;
  H2 1 VOUT / 2 GND / 3 TXD / 4 RXD / 5 RTS / 6 CTS
  (docs/references/Waveshare_CH343-USB-UART-Board_Schematic_2026-11-08.pdf)
"""
import copy
import json
import os
import subprocess
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "hardware", "sensor", "gen"))
import gen_schematic as gs  # noqa: E402
import sexpr  # noqa: E402
from sexpr import Q  # noqa: E402

PRJ = os.path.normpath(os.path.join(HERE, ".."))
NAME = "fluidi_programmer"
LIBNAME = "fluidi_programmer"
LIBDIR = os.path.join(PRJ, "lib")
KICAD_SYM = "/usr/share/kicad/symbols"
REV = "1"
DATE = "2026-11-08"
DS = "docs/datasheets/"

# Generator-Globale des Sensor-Generators auf dieses Projekt umstellen (uid/Power-Symbole/Instanzpfade)
gs.NAME = NAME
gs.NS = uuid.UUID("6f1d2c3a-0b6e-4c9a-9a51-f1a1d2000001")
gs.ROOT_UUID = str(uuid.uuid5(gs.NS, "root"))

# --------------------------------------------------------------------- Teile
# key: (Hersteller, MPN, LCSC, Datenblatt, Beschreibung)  - LCSC/Lager per JLC-Teilesuche 2026-11-08 geprueft
PARTDB = {
    "LDO33": ("Torex", "XC6206P332MR-G", "C5446", DS + "Torex_XC6206_Datasheet_ETR0305-004b.pdf",
              "LDO 3.3 V 200 mA SOT-23 (Vorstufe, begrenzt Einzelfehler auf 3.3 V)"),
    "LDO20": ("Torex", "XC6206P202MR-G", "C2891260", DS + "Torex_XC6206_Datasheet_ETR0305-004b.pdf",
              "LDO 2.0 V +-2 % SOT-23 (1.960-2.040 V, S. 5 Tab. E-1)"),
    "AUP17": ("Texas Instruments", "SN74AUP1G17DBVR", "C183012", DS + "TI_SN74AUP1G17_Datasheet_SCES579J.pdf",
              "Schmitt-Puffer, II <= 0.1 uA (25 degC) / 0.5 uA (-40..85 degC), SOT-23-5"),
    "C1U": ("Samsung Electro-Mechanics", "CL21B105KBFNNNE", "C28323",
            DS + "Samsung_CL31A107MQHNNNE_Catalog_2015-11.pdf", "MLCC 1 uF 50 V X7R 0805 (CIN/CL nach XC6206 DS S. 1)"),
    "C100N": ("Samsung Electro-Mechanics", "CL21B104KBCNNNC", "C1711",
              DS + "Samsung_CL31A107MQHNNNE_Catalog_2015-11.pdf", "MLCC 100 nF 50 V X7R 0805"),
    "R10M": ("UNI-ROYAL", "0402WGF1005TCE", "C26082", DS + "UNI-ROYAL_0402WGF-Serie_Datasheet_LCSC-2024-11.pdf",
             "R 10 MOhm 1 % 0402 (Seriendatenblatt 01005-2512, Kap. 6 Resistance Range: 0402 1 Ohm-10 MOhm)"),
    "CABLE": ("-", "Litze/Steckbruecken zum Waveshare CH343 USB UART Board", "", "", "Kabel <= 20 cm (ANNAHME)"),
    "DUMMY": ("-", "Eigenbau: 2 x FR4 1.6 mm Cu, D 20.0 mm", "", "", "Dummy-Zelle CR2032-Form (README Kap. 4)"),
    "POGO": ("-", "Federkontaktstift, Handelsware", "", "", "Federstifte auf TP1/TP2 (ANNAHME, README Kap. 4)"),
}

FP_C = "Capacitor_SMD:C_0805_2012Metric"
G = 2.54
COMPONENTS = []


def add(ref, lib, val, fp, key, x, y, rot, conns, note=""):
    COMPONENTS.append(dict(ref=ref, lib=lib, val=val, fp=fp, key=key, x=round(x * G, 4), y=round(y * G, 4), rot=rot,
                           conns=conns, note=note))


L = LIBNAME + ":"
# Versorgung: USB 5 V (Waveshare H3.3 bzw. H1.1) -> U1 3.3 V -> U2 2.0 V (Dummy-Zelle) und U3 2.0 V (VIO des CH343 + Puffer)
add("J1", "Connector_Generic:Conn_01x05", "zu Waveshare CH343", "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical",
    "CABLE", 12, 20, 0, {"1": "+5V", "2": "GND", "3": "VIO", "4": "RXD_HOST", "5": "TXD_HOST"},
    note="1 = H3.3 +5V, 2 = H2.2 GND, 3 = H3.2 VIO (Jumper H3 ENTFERNT), 4 = H2.4 RXD, 5 = H2.3 TXD; +5V alternativ H1.1, falls H1 bestueckt")
add("U1", L + "XC6206PxxxMR", "XC6206P332MR", "Package_TO_SOT_SMD:SOT-23", "LDO33", 34, 14, 0,
    {"1": "GND", "2": "+3V3", "3": "+5V"})
add("C1", "Device:C", "1u", FP_C, "C1U", 26, 18, 0, {"1": "+5V", "2": "GND"}, note="CIN U1")
add("C2", "Device:C", "1u", FP_C, "C1U", 42, 18, 0, {"1": "+3V3", "2": "GND"}, note="CL U1 = CIN U2/U3")
add("U2", L + "XC6206PxxxMR", "XC6206P202MR", "Package_TO_SOT_SMD:SOT-23", "LDO20", 58, 14, 0,
    {"1": "GND", "2": "VDD_DUT", "3": "+3V3"}, note="Speisung Dummy-Zelle (Sensor-VDD)")
add("C3", "Device:C", "1u", FP_C, "C1U", 66, 18, 0, {"1": "VDD_DUT", "2": "GND"}, note="CL U2")
add("U3", L + "XC6206PxxxMR", "XC6206P202MR", "Package_TO_SOT_SMD:SOT-23", "LDO20", 58, 32, 0,
    {"1": "GND", "2": "VIO", "3": "+3V3"}, note="eigene Schiene fuer CH343-VIO und Puffer: Einstecken der Dummy-Zelle "
                                               "(Einschaltstrom in 4 x 100 uF) stoert die USB-Bruecke nicht")
add("C4", "Device:C", "1u", FP_C, "C1U", 66, 36, 0, {"1": "VIO", "2": "GND"}, note="CL U3")
add("J2", "Connector_Generic:Conn_01x02", "Dummy-Zelle CR2032", "", "DUMMY", 84, 14, 0,
    {"1": "VDD_DUT", "2": "GND"}, note="1 = Oberseite (+, Clip), 2 = Mittelinsel D 8 mm (-, Minuspad); keine Zelle!")
# TX-Puffer am Federstiftkopf (<= 3 cm Draht ab Stift TP1)
add("J3", "Connector_Generic:Conn_01x02", "Federstifte TP1/TP2", "", "POGO", 12, 52, 0,
    {"1": "TX_PAD", "2": "TXD_HOST"}, note="1 = TP1 UART_TX_PAD (Sensor sendet), 2 = TP2 UART_RX_PAD (Sensor empfaengt)")
add("R1", "Device:R", "10M", "Resistor_SMD:R_0402_1005Metric", "R10M", 26, 44, 0, {"1": "VIO", "2": "TX_PAD"},
    note="schwacher Ruhepegel high, solange DIO6 im Bootloader noch hochohmig ist (TRM S. 464); groesser = mehr "
         "Low-Reserve, kleiner = sichererer Ruhepegel (SPICE A1/A1z)")
add("U4", L + "74AUP1G17", "SN74AUP1G17DBVR", "Package_TO_SOT_SMD:SOT-23-5", "AUP17", 44, 52, 0,
    {"2": "TX_PAD", "3": "GND", "4": "RXD_HOST", "5": "VIO"}, note="direkt am Federstiftkopf (SPICE: Puffer am Kabelende "
                                                                     "faellt bei 57600 Baud aus)")
add("C5", "Device:C", "100n", FP_C, "C100N", 34, 44, 0, {"1": "VIO", "2": "GND"}, note="an U4 VCC")

FLAGS = [("+5V", 20, 32), ("GND", 26, 32)]


# --------------------------------------------------------------------- Bibliothek (abgeleitete Symbole aufloesen)
_SRC = {}


def _load(lib):
    if lib not in _SRC:
        _SRC[lib] = sexpr.parse(open(os.path.join(KICAD_SYM, lib + ".kicad_sym")).read())
    return _SRC[lib]


def flatten(lib, name):
    node = next(x for x in _load(lib) if isinstance(x, list) and x[0] == "symbol" and x[1] == name)
    ext = sexpr.find(node, "extends")
    if not ext:
        return copy.deepcopy(node)
    base = flatten(lib, ext[1])
    pname = base[1]
    base[1] = Q(name)
    for x in base:
        if isinstance(x, list) and x[0] == "symbol" and isinstance(x[1], str) and x[1].startswith(pname + "_"):
            x[1] = Q(name + x[1][len(pname):])
    props = {p[1]: p for p in sexpr.find_all(node, "property")}
    for i, x in enumerate(base):
        if isinstance(x, list) and x[0] == "property" and x[1] in props:
            base[i] = copy.deepcopy(props.pop(x[1]))
    for p in props.values():
        base.insert(3, copy.deepcopy(p))
    return base


def write_lib():
    syms = []
    for lib, name, fp, dsheet, desc in (
            ("Regulator_Linear", "XC6206PxxxMR", "Package_TO_SOT_SMD:SOT-23",
             DS + "Torex_XC6206_Datasheet_ETR0305-004b.pdf",
             "LDO Torex XC6206, SOT-23: 1 VSS, 2 VOUT, 3 VIN (DS S. 2); CIN = CL = 1 uF Keramik (S. 1)"),
            ("74xGxx", "74AUP1G17", "Package_TO_SOT_SMD:SOT-23-5", DS + "TI_SN74AUP1G17_Datasheet_SCES579J.pdf",
             "Schmitt-Puffer SN74AUP1G17 DBV: 1 NC, 2 A, 3 GND, 4 Y, 5 VCC (DS S. 3)")):
        n = flatten(lib, name)
        n[1] = Q(name)
        for x in n:
            if isinstance(x, list) and x[0] == "property":
                if x[1] == "Footprint":
                    x[2] = Q(fp)
                elif x[1] == "Datasheet":
                    x[2] = Q(dsheet)
                elif x[1] == "Description":
                    x[2] = Q(desc)
        syms.append(n)
    out = ["kicad_symbol_lib", ["version", "20241209"], ["generator", Q("fluidi_gen_programmer")],
           ["generator_version", Q("1.0")]] + syms
    os.makedirs(LIBDIR, exist_ok=True)
    with open(os.path.join(LIBDIR, LIBNAME + ".kicad_sym"), "w") as fh:
        fh.write(sexpr.dump(out) + "\n")


# --------------------------------------------------------------------- Schaltplan
class Sheet(gs.Sheet):
    def use(self, lib_id):
        if lib_id not in self.libs:
            lib, name = lib_id.split(":")
            if lib == LIBNAME:
                tree = sexpr.parse(open(os.path.join(LIBDIR, LIBNAME + ".kicad_sym")).read())
                node = copy.deepcopy(next(x for x in tree if isinstance(x, list) and x[0] == "symbol"
                                          and x[1] == name))
            else:
                node = flatten(lib, name)
            node[1] = Q(lib_id)
            self.libs[lib_id] = node
        return self.libs[lib_id]

    def connect(self, net, px, py, d):
        ex, ey = px + d[0] * gs.STUB, py + d[1] * gs.STUB
        if net == "NC":
            self.no_connect(px, py)
            return
        self.wire(px, py, ex, ey)
        if net == "GND":
            self.power(net, ex, ey, d)
        else:
            self.label(net, ex, ey, d)

    def flag(self, net, x, y):
        self.power("PWR_FLAG", x, y, (0, -1))
        self.wire(x, y, x, y + gs.STUB)
        if net == "GND":
            self.power(net, x, y + gs.STUB, (0, 1))
        else:
            self.label(net, x, y + gs.STUB, (0, 1))

    def component(self, c):
        node = self.use(c["lib"])
        pdb = PARTDB[c["key"]]
        X, Y, rot = c["x"], c["y"], c["rot"]
        pins = gs.lib_pins(node)
        ys = [gs.transform(p["x"], p["y"], rot, X, Y)[1] for p in pins]
        xs = [gs.transform(p["x"], p["y"], rot, X, Y)[0] for p in pins]
        if c["key"].startswith("LDO") or c["key"] == "AUP17":
            rx, ry, just = X - 2.0, min(ys) - 9.0, "left"      # oberhalb des Koerpers
            if c["key"] == "AUP17":
                rx, ry = X + 4.0, min(ys) - 6.0
        else:
            rx, ry, just = max(xs) + (5.0 if c["ref"].startswith("J") else 1.5), min(ys) - 2.0, "left"
        props = [("Reference", c["ref"], rx, ry, False, just), ("Value", c["val"], rx, ry + 2.2, False, just),
                 ("Footprint", c["fp"], X, Y, True, None),
                 ("Datasheet", pdb[3] or gs.lib_prop(node, "Datasheet"), X, Y, True, None),
                 ("Description", pdb[4] + (("; " + c["note"]) if c["note"] else ""), X, Y, True, None),
                 ("LCSC", pdb[2], X, Y, True, None), ("Hersteller", pdb[0], X, Y, True, None),
                 ("MPN", pdb[1], X, Y, True, None)]
        sym = ["symbol", ["lib_id", Q(c["lib"])], ["at", gs.f(X), gs.f(Y), str(rot)], ["unit", "1"],
               ["exclude_from_sim", "no"], ["in_bom", "yes"], ["on_board", "yes"], ["dnp", "no"],
               ["uuid", Q(gs.uid("s", c["ref"]))]]
        for k, v, x, y, hide, j in props:
            sym.append(["property", Q(k), Q(v), ["at", gs.f(x), gs.f(y), "0"], gs.font(1.27, j, hide)])
        for p in pins:
            sym.append(["pin", Q(p["num"]), ["uuid", Q(gs.uid("sp", c["ref"], p["num"]))]])
        sym.append(["instances", ["project", Q(NAME), ["path", Q("/" + gs.ROOT_UUID), ["reference", Q(c["ref"])],
                                                         ["unit", "1"]]]])
        self.items.append(sym)
        self.intended[c["ref"]] = {}
        for p in pins:
            net = c["conns"].get(p["num"])
            if net is None:
                if p["hidden"] or p["type"] == "no_connect":
                    continue
                raise ValueError(f"{c['ref']} Pin {p['num']} ({p['name']}) ohne Netz")
            px, py = gs.transform(p["x"], p["y"], rot, X, Y)
            d = gs.direction(p["ang"] + 180 + rot)
            self.intended[c["ref"]][p["num"]] = net
            self.connect(net, px, py, d)
        unknown = set(c["conns"]) - {p["num"] for p in pins}
        if unknown:
            raise ValueError(f"{c['ref']}: unbekannte Pins {unknown}")

    def write(self, path):
        tb = ["title_block", ["title", Q("fluidi Programmieradapter (Dummy-Zelle + TX-Puffer)")], ["date", Q(DATE)],
              ["rev", Q(REV)], ["company", Q("fluidi (Projekt Tr-pfli)")],
              ["comment", "1", Q("Werkzeug, nicht Teil des Sensors. Erstprogrammierung ueber ROM-UART-Bootloader")],
              ["comment", "2", Q("Generiert: hardware/programmer/gen/gen_programmer.py - nicht von Hand aendern")],
              ["comment", "3", Q("Sicherheit: Speisung NUR ueber die Dummy-Zelle, nie mit echter Zelle (R2-A2)")],
              ["comment", "4", Q("Begruendung, Stueckliste, Aufbau: hardware/programmer/README.md")]]
        root = ["kicad_sch", ["version", "20250114"], ["generator", Q("eeschema")], ["generator_version", Q("9.0")],
                ["uuid", Q(gs.ROOT_UUID)], ["paper", Q("A4")], tb,
                ["lib_symbols"] + list(self.libs.values())] + self.items + \
               [["sheet_instances", ["path", Q("/"), ["page", Q("1")]]], ["embedded_fonts", "no"]]
        with open(path, "w") as fh:
            fh.write(sexpr.dump(root) + "\n")


NOTES = [
    (4, 5, "VERSORGUNG  USB 5 V (Waveshare H3.3) -> U1 3.3 V -> U2 2.0 V (Dummy-Zelle = Sensor-VDD) und U3 2.0 V (VIO).\n"
           "Einzelfehler: U2 oder U3 durchlegiert -> hoechstens 3.3 V (VDDS max 3.8 V, abs. max 4.1 V, CC2340 DS S. 18);\n"
           "U1 durchlegiert -> U2/U3 regeln weiter (VIN max 6.0 V). Fuer 5 V am Sensor braucht es zwei Fehler (R2-L02).\n"
           "Waveshare: Jumper H3 (3.3 V/5 V) ENTFERNEN, VIO kommt von U3. Vor dem Einsetzen VDD_DUT und VIO messen."),
    (4, 64, "TX-PUFFER  CH343-RXD hat 3-21 uA Pull-up (DS S. 8) + Board-LED 2 kOhm: ueber 2 x 100 kOhm kein Low.\n"
            "U4 SN74AUP1G17 (Leck <= 0.5 uA -> <= 0.1 V ueber 200 kOhm) direkt am Federstift TP1, <= 3 cm Draht.\n"
            "R1 10 MOhm: schwacher Ruhepegel high, bevor der Bootloader DIO6 als Ausgang schaltet.\n"
            "Nachweis: simulation/spice/programmer/prog_uart.py (Pegel, Flanken, 19200-57600 Baud)."),
    (72, 46, "SICHERHEIT (CONCEPTS 2.7, R2-A2)\n"
             "Dummy-Zelle und Federstiftkopf sind EIN starres Teil.\n"
             "Speisung nur ueber Clip/Minuspad, keine Zelle\n"
             "im Adapter, nie zusammen mit einer echten Zelle.\n"
             "TP2 wird ueber 2 x 100 kOhm auf dem Sensor getrieben."),
]


def main():
    write_lib()
    sh = Sheet()
    for c in COMPONENTS:
        sh.component(c)
    for net, x, y in FLAGS:
        sh.flag(net, x * G, y * G)
    for x, y, t in NOTES:
        sh.text(t, x * G, y * G)
    sh.write(os.path.join(PRJ, NAME + ".kicad_sch"))
    pro = {"meta": {"filename": NAME + ".kicad_pro", "version": 3},
           "erc": {"erc_exclusions": [], "meta": {"version": 0}, "pin_map": [], "rule_severities": {}},
           "schematic": {"meta": {"version": 1}}, "text_variables": {"REV": REV}}
    with open(os.path.join(PRJ, NAME + ".kicad_pro"), "w") as fh:
        json.dump(pro, fh, indent=2)
    libs = sorted({c["lib"].split(":")[0] for c in COMPONENTS} | {"power"})
    lines = ['(sym_lib_table', '  (version 7)']
    for lib in libs:
        uri = "${KIPRJMOD}/lib/" + LIBNAME + ".kicad_sym" if lib == LIBNAME else \
            "${KICAD10_SYMBOL_DIR}/" + lib + ".kicad_sym"
        lines.append(f'  (lib (name "{lib}")(type "KiCad")(uri "{uri}")(options "")(descr ""))')
    with open(os.path.join(PRJ, "sym-lib-table"), "w") as fh:
        fh.write("\n".join(lines + [")"]) + "\n")
    lines = ['(fp_lib_table', '  (version 7)']
    for lib in sorted({c["fp"].split(":")[0] for c in COMPONENTS if c["fp"]}):
        lines.append(f'  (lib (name "{lib}")(type "KiCad")(uri "${{KICAD10_FOOTPRINT_DIR}}/{lib}.pretty")'
                     f'(options "")(descr ""))')
    with open(os.path.join(PRJ, "fp-lib-table"), "w") as fh:
        fh.write("\n".join(lines + [")"]) + "\n")
    with open(os.path.join(HERE, "intended_netlist.json"), "w") as fh:
        json.dump(sh.intended, fh, indent=1, sort_keys=True)
    print(f"Schaltplan geschrieben: {NAME}.kicad_sch ({len(COMPONENTS)} Symbole)")


def check_netlist(cli="kicad-cli"):
    out = os.path.join(PRJ, "out")
    os.makedirs(out, exist_ok=True)
    net = os.path.join(out, NAME + ".net")
    subprocess.run([cli, "sch", "export", "netlist", "--format", "kicadsexpr", "-o", net,
                    os.path.join(PRJ, NAME + ".kicad_sch")], check=True, capture_output=True)
    tree = sexpr.parse(open(net).read())
    actual = {}
    for n in sexpr.find_all(sexpr.find(tree, "nets"), "net"):
        name = sexpr.find(n, "name")[1].lstrip("/")
        for node in sexpr.find_all(n, "node"):
            ref, pin = sexpr.find(node, "ref")[1], sexpr.find(node, "pin")[1]
            if not ref.startswith("#"):
                actual.setdefault(ref, {})[pin] = name
    want = json.load(open(os.path.join(HERE, "intended_netlist.json")))
    errs = [f"{r}.{p}: soll {n}, ist {actual.get(r, {}).get(p)}" for r, ps in want.items() for p, n in ps.items()
            if actual.get(r, {}).get(p) != n]
    errs += [f"{r}.{p}: unerwartet an {n}" for r, ps in actual.items() for p, n in ps.items()
             if p not in want.get(r, {}) and not n.startswith("unconnected-")]
    if errs:
        print("NETZLISTE ABWEICHUNG:\n  " + "\n  ".join(errs))
        sys.exit(1)
    nets = {n for ps in want.values() for n in ps.values()}
    print(f"Netzliste OK: {len(want)} Bauteile, {sum(len(p) for p in want.values())} Pins, {len(nets)} Netze")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        check_netlist(*sys.argv[2:])
    else:
        main()
