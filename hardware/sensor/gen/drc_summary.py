#!/usr/bin/env python3
"""DRC-JSON (kicad-cli pcb drc --format json) zusammenfassen: Anzahl je Typ/Schwere, ungeroutete Verbindungen,
Paritaet. Aufruf: .venv/bin/python hardware/sensor/gen/drc_summary.py hardware/sensor/out/drc_wsl.json"""
import collections
import json
import sys

d = json.load(open(sys.argv[1]))
cnt = collections.Counter()
for v in d.get("violations", []):
    cnt[(v["severity"], v["type"])] += 1
unc = d.get("unconnected_items", [])
par = d.get("schematic_parity", [])
print("Verletzungen:", sum(cnt.values()), " Fehler:", sum(n for (s, t), n in cnt.items() if s == "error"),
      " Warnungen:", sum(n for (s, t), n in cnt.items() if s == "warning"))
for (s, t), n in sorted(cnt.items()):
    print("  %-8s %-32s %d" % (s, t, n))
print("Ungeroutet:", len(unc))
for u in unc[:30]:
    print("  ", "; ".join(i["description"] for i in u["items"]))
print("Paritaet:", len(par))
for p in par[:20]:
    print("  ", p["type"], p["description"], "; ".join(i["description"] for i in p.get("items", [])))
if len(sys.argv) > 2:
    for v in d.get("violations", []):
        if v["type"] == sys.argv[2]:
            print(v["description"], "|", " / ".join("%s @%.2f,%.2f" % (i["description"], i["pos"]["x"], i["pos"]["y"])
                                                     for i in v["items"]))
