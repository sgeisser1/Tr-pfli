#!/usr/bin/env python3
"""fluidi Sensor - JLC-Status (Basic/Preferred/Extended, Lager, Preis @1) aller LCSC-Nummern aus parts.PARTDB abfragen.

Quelle: JLC-Teilesuche https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList
(gleiche Abfrage wie scripts/jlc_price_cache.py). Ausgabe: hardware/sensor/gen/jlc_check.json (von bom_jlc.py --register
gelesen). Nur benutzte Teile werden ins Register uebernommen.
Aufruf: .venv/bin/python hardware/sensor/gen/jlc_check.py
"""
import datetime
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "scripts"))
import parts  # noqa: E402
from jlc_price_cache import query  # noqa: E402


def main():
    used = {parts.PARTDB[c["key"]][2] for c in parts.COMPONENTS if parts.PARTDB[c["key"]][2]}
    out = {"_abruf": datetime.date.today().isoformat()}
    for code in sorted(used):
        d = query(code)
        if d is None:
            print(code, "NICHT GEFUNDEN")
            continue
        out[code] = {"model": d["model"], "brand": d["brand"], "package": d["package"], "library": d["library"],
                     "preferred": d["preferred"], "stock": d["stock"], "price1": d["tiers"][:1],
                     "describe": d["describe"]}
        cat = {"base": "Basic", "expand": "Extended"}.get(d["library"], d["library"])
        cat = "Preferred" if d["preferred"] else cat
        key = next(k for k, v in parts.PARTDB.items() if v[2] == code)
        flag = "" if cat == parts.PARTDB[key][3] else f"  << parts.py sagt {parts.PARTDB[key][3]}"
        mpn_ok = "" if d["model"] == parts.PARTDB[key][1] else f"  << MPN JLC {d['model']}"
        print(f"{code:10s} {cat:9s} Lager {d['stock']:>9} {d['tiers'][0][1]:>8} USD  {d['model']}{flag}{mpn_ok}")
    with open(os.path.join(HERE, "jlc_check.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
