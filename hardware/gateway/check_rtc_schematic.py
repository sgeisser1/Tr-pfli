#!/usr/bin/env python3
"""Gateway RTC (W-8): Prueft im Eagle-Schaltplan des Adafruit PiRTC DS3231 (Produkt 4282), dass die Pufferzelle keinen
Ladepfad hat (REQ-GW-09 / OP-GW-3 "RTC ohne Ladepfad", Primaerzelle CR1220).

Quelle: docs/datasheets/Adafruit_4282_PiRTC-DS3231_Schematic_2021-02-22.sch
        (https://github.com/adafruit/Adafruit-PiRTC-DS3231-PCB, Commit 2021-02-22, abgerufen 2026-11-08)
Regel : Netz VBAT darf nur den Zellenhalter (B1, Pin +) und den VBAT-Pin des RTC-IC verbinden. Jede weitere Verbindung
        (Diode, Widerstand, Versorgungsnetz) waere ein moeglicher Ladepfad -> Fehler.
DS3231: VBAT-Pin "UL recognized to ensure against reverse charging when used with a primary lithium battery"
        (docs/datasheets/Maxim_DS3231_Datasheet_19-5170Rev10.pdf, S. 9, Pin 14).
Aufruf: .venv/bin/python hardware/gateway/check_rtc_schematic.py   (Exit 0 = kein Ladepfad)
"""
import hashlib
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SCH = os.path.join(ROOT, "docs", "datasheets", "Adafruit_4282_PiRTC-DS3231_Schematic_2021-02-22.sch")


def nets(text):
    out = {}
    for m in re.finditer(r'<net name="([^"]+)"[^>]*>(.*?)</net>', text, re.S):
        out[m.group(1)] = sorted(set(re.findall(r'<pinref part="([^"]+)" gate="[^"]*" pin="([^"]+)"', m.group(2))))
    return out


def main():
    text = open(SCH, encoding="utf-8", errors="replace").read()
    parts = re.findall(r'<part name="([^"]+)" library="[^"]+" deviceset="([^"]+)" device="([^"]*)"(?: value="([^"]*)")?',
                       text)
    print(f"Datei {os.path.relpath(SCH, ROOT)} sha256 {hashlib.sha256(text.encode('utf-8', 'replace')).hexdigest()[:16]}…")
    print("Bauteile (ohne Versorgungssymbole/Fiducials):",
          ", ".join(f"{n}={d}{('/' + v) if v else ''}" for n, d, dev, v in parts
                    if d not in ("GND", "3.3V", "+5V", "FIDUCIAL", "MOUNTINGHOLE")))
    n = nets(text)
    for k in ("VBAT", "3.3V", "+5V"):
        print(f"Netz {k}: {n.get(k)}")
    vbat = set(n.get("VBAT", []))
    ok = vbat == {("B1", "+"), ("IC2", "VBAT")}
    diodes = [p for p in parts if re.search(r"DIODE|SCHOTTKY", p[1], re.I)]
    print(f"Dioden im Schaltplan: {diodes or 'keine'}")
    print("ERGEBNIS:", "kein Ladepfad (VBAT nur Zelle + RTC-IC)" if ok and not diodes else "PRUEFEN: moeglicher Ladepfad")
    return 0 if ok and not diodes else 1


if __name__ == "__main__":
    sys.exit(main())
