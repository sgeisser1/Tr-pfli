#!/usr/bin/env python3
"""fluidi - JLC-Teiledaten (Basic/Preferred/Extended, Lager, Preisstaffeln, Mindestmengen) abfragen
und als Cache fuer scripts/concept_costs.py ablegen.

Aufruf:  .venv/bin/python scripts/jlc_price_cache.py C20416850 C2925606 ...   (ohne Argumente: alle Teile
         aus concept_costs.LCSC_ALL)
Ausgabe: docs/concepts/bom/jlc_prices.json  (Abrufdatum im Feld "_abruf")
Quelle:  JLC-Teilesuche https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList
Nur Standardbibliothek + curl.
"""
import datetime
import json
import os
import subprocess
import sys

URL = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs", "concepts", "bom", "jlc_prices.json")


def query(code):
    body = json.dumps({"keyword": code, "currentPage": 1, "pageSize": 10})
    r = subprocess.run(["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json", "-A", "Mozilla/5.0",
                        URL, "-d", body], capture_output=True, text=True, check=True)
    lst = json.loads(r.stdout)["data"]["componentPageInfo"]["list"] or []
    m = [x for x in lst if x["componentCode"] == code]
    if not m:
        return None
    x = m[0]
    return {
        "model": x["componentModelEn"], "brand": x["componentBrandEn"], "package": x["componentSpecificationEn"],
        "library": x["componentLibraryType"], "preferred": bool(x.get("preferredComponentFlag")),
        "stock": x["stockCount"], "least": x.get("leastPatchNumber") or 0, "loss": x.get("lossNumber") or 0,
        "tiers": sorted([[p["startNumber"], p["productPrice"]] for p in x["componentPrices"]]),
        "describe": x["describe"],
    }


def main():
    codes = sys.argv[1:]
    if not codes:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import concept_costs
        codes = sorted(concept_costs.LCSC_ALL)
    data = json.load(open(OUT)) if os.path.exists(OUT) else {}
    for c in codes:
        d = query(c)
        print(c, "NICHT GEFUNDEN" if d is None else f"{d['library']} pref={d['preferred']} Lager {d['stock']} "
              f"{d['tiers'][:2]} {d['model']}")
        if d:
            data[c] = d
    data["_abruf"] = datetime.date.today().isoformat()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False, sort_keys=True)


if __name__ == "__main__":
    main()
