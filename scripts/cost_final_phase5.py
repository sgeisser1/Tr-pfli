#!/usr/bin/env python3
"""fluidi Phase 5 - Kostenrechnung final: Sensor (Abgleich mit JLC-Screenshot 2026-11-08), Gateway (W-8), System.

Eingaben (nur lesen):
  hardware/sensor/gen/cost_rev_b.py      Sensor-Szenarien (BOM, JLC-Teilepreise, PCB-Angebot, D-005) ueber scripts/cost_model.py
  hardware/gateway/BOM_GATEWAY.csv       Gateway-Stueckliste mit Preis, Quelle, Abrufdatum (W-8)
  hardware/programmer/README.md Kap. 6   Programmieradapter (Werkzeug) 25-55 CHF (ANNAHME-Spanne dort)
JLC-Screenshot (Auftraggeber, 2026-11-08, Standard PCB ohne PCBA, nicht eingeloggt, 20 Stk 26 x 158.5 mm 4 L 1.6 mm ENIG
POFV, Material FR4 TG135, Confirm Production File = No): Positionen unten in SCREENSHOT_20; Summe muss 76.30 USD ergeben.
Ausgabe: docs/reviews/phase5_kosten_final.md
Aufruf : .venv/bin/python scripts/cost_final_phase5.py
"""
import csv
import io
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "hardware", "sensor", "gen"))
import cost_model as cm  # noqa: E402
import cost_rev_b as cr  # noqa: E402

OUT = os.path.join(ROOT, "docs", "reviews", "phase5_kosten_final.md")
GW_BOM = os.path.join(ROOT, "hardware", "gateway", "BOM_GATEWAY.csv")

# --- JLC-Screenshot 2026-11-08 (Auftraggeber), "Charge Details", 20 Stk, USD ------------------------------------------
SCREENSHOT_20 = {
    "Engineering fee": 25.00,
    "Via Covering (Epoxy Filled & Capped)": 18.59,
    "Surface Finish (ENIG 1 U\")": 18.50,
    "Deburring/Edge rounding": 0.50,
    "Board": 10.20,
    "Via Plating Method (Horizontal Electroless Copper Plating)": 3.51,
}
SCREENSHOT_TOTAL_20 = 76.30          # "Web Price" (Desktop Price "from 74.30")
SCREENSHOT_DHL = 23.52               # DHL Express, 2-4 Tage
SCREENSHOT_WEIGHT_KG = 0.41          # 20 unbestueckte Platinen
SCREENSHOT_COUPON_USD = 20.0         # 2 x "Save $20.00" angezeigt, Bedingungen nicht abgelesen (ANNAHME)
PROG_ADAPTER_CHF = (25.0, 55.0)      # hardware/programmer/README.md Kap. 6 (ANNAHME-Spanne)


def fx():
    return cm.USD_TO_CHF * (1 + cm.FX_CARD_MARKUP)


def load_gw():
    rows = list(csv.DictReader(open(GW_BOM, encoding="utf-8"), delimiter=";"))
    for r in rows:
        r["Menge"] = float(r["Menge"])
        r["Preis_CHF_Stk"] = float(r["Preis_CHF_Stk"])
        r["sum"] = r["Menge"] * r["Preis_CHF_Stk"]
    return rows


def main():
    # --- 1 Abgleich Screenshot
    s_sum = round(sum(SCREENSHOT_20.values()), 2)
    assert abs(s_sum - SCREENSHOT_TOTAL_20) < 0.005, s_sum
    assert abs(cr.QUOTE_USD[20] - SCREENSHOT_TOTAL_20) < 0.005, "PCB-Angebot im Modell != Screenshot"
    assert abs(cm.SHIPPING_USD["DHL"] - SCREENSHOT_DHL) < 0.005, "cost_model.SHIPPING_USD['DHL'] nachfuehren"

    # --- 2 Sensor-Szenarien (wie COSTS_REV_B.md, gleiche Funktionen)
    bom4 = cr.load_bom()
    bom2 = [b for b in __import__("copy").deepcopy(bom4)]
    for b in bom2:
        if b.part.endswith("C15008"):
            b.qty_per_board = 2
    scen = {
        "proto": ("Prototyp 5 PCB / 5 bestückt (4 × 100 µF)", bom4, 5, 5, 5, "economic"),
        "serie4": ("Serie 20 PCB / 16 bestückt / 15 Sensoren (4 × 100 µF)", bom4, 20, 16, 15, "economic"),
        "serie2": ("Serie 20 PCB / 16 bestückt / 15 Sensoren (2 × 100 µF)", bom2, 20, 16, 15, "economic"),
        "std_serie": ("ALT Standard-PCBA Serie 7 Paneele = 21 PCB / 18 bestückt / 15 Sensoren", bom4, 21, 18, 15,
                      "standard"),
        "std_proto": ("ALT Standard-PCBA Prototyp 2 Paneele = 6 PCB / 6 bestückt / 5 Sensoren", bom4, 6, 6, 5,
                      "standard"),
    }
    res = {k: cr.run(b, p, a, s, pcba=m) for k, (_, b, p, a, s, m) in scen.items()}
    # Sensitivitaet Pre-reflow Soldering (JLC-Preisseite, Anwendung unklar) -> nur ausgewiesen
    bak = cm.APPLY_PRE_REFLOW
    try:
        cm.APPLY_PRE_REFLOW = True
        pre = {k: cr.run(scen[k][1], *scen[k][2:5], pcba=scen[k][5]) for k in ("proto", "serie4")}
    finally:
        cm.APPLY_PRE_REFLOW = bak
    coupon_chf = SCREENSHOT_COUPON_USD * fx() + SCREENSHOT_COUPON_USD * cm.USD_TO_CHF * cm.CH_VAT

    # --- 3 Gateway
    gw = load_gw()
    buy = [r for r in gw if r["Status"] in ("kaufen", "Eigenfertigung")]
    gw_buy = sum(r["sum"] for r in buy)
    gw_new = gw_buy + sum(r["sum"] for r in gw if r["Status"] == "vorhanden")
    gw_annahme = sum(r["sum"] for r in buy if "ANNAHME" in r["Preisquelle"])
    gw_open = [r for r in gw if r["Status"] == "offen"]

    # --- 4 System
    s4, pr = res["serie4"], res["proto"]
    sysA = s4["total_chf"] + gw_buy
    sysB = pr["total_chf"] + s4["total_chf"] + gw_buy
    sysB_lo, sysB_hi = sysB + PROG_ADAPTER_CHF[0], sysB + PROG_ADAPTER_CHF[1]

    md = io.StringIO()
    w = md.write
    w("# Phase 5 – Kostenrechnung final (Sensor, Gateway, System)\n\n")
    w("| | |\n|---|---|\n")
    w("| Stand | 2026-11-08, erzeugt von `.venv/bin/python scripts/cost_final_phase5.py` (nicht von Hand ändern) |\n")
    w(f"| Kurs | 1 USD = {cm.USD_TO_CHF:.4f} CHF, {cm.FX_DATE}; + {cm.FX_CARD_MARKUP*100:.1f} % Kartenaufschlag (ANNAHME) "
      f"= {fx():.4f} CHF; 2026-11-08 ist ein Sonntag, neuester EZB-Kurs = 2026-11-06 |\n")
    w("| Sensor | `hardware/sensor/gen/cost_rev_b.py` → `scripts/cost_model.compute` (D-005), Teilepreise "
      f"`docs/concepts/bom/jlc_prices.json` (Abruf {cr.PRICES['_abruf']}), Lager live 2026-11-08 13:06 (`order_check.py --live`) |\n")
    w("| Gateway | `hardware/gateway/BOM_GATEWAY.csv` (Preise pi-shop.ch, Abruf 2026-11-08, "
      "`docs/references/pi-shop_Gateway-Teile_Auszug_2026-11-08.txt`) |\n")
    w("| Bestellunterlage | `hardware/sensor/out/ORDER_JLC_REV_C.md`, Anleitung `docs/manuals/BESTELLEN_JLC.md` |\n\n")

    w("## 1 Abgleich JLC-Screenshot ↔ Modell (Sensor-PCB, 2026-11-08)\n\n")
    w("| Position (Screenshot, 20 Stk) | USD |\n|---|---|\n")
    for k, v in SCREENSHOT_20.items():
        w(f"| {k} | {v:.2f} |\n")
    w(f"| **Summe = Web Price** | **{s_sum:.2f}** |\n\n")
    w("| Grösse | Screenshot | Modell | Ergebnis |\n|---|---|---|---|\n")
    w(f"| PCB 20 Stk | {SCREENSHOT_TOTAL_20:.2f} USD | `QUOTE_USD[20]` = {cr.QUOTE_USD[20]:.2f} USD | gleich |\n")
    w(f"| PCB 5 Stk | nicht im Screenshot | {cr.QUOTE_USD[5]:.2f} USD (Angebot 2026-11-08, CLIENT_INPUT) | am Bestelltag ablesen |\n")
    w(f"| DHL Express | {SCREENSHOT_DHL:.2f} USD | `SHIPPING_USD['DHL']` = {cm.SHIPPING_USD['DHL']:.2f} USD "
      "(bis 2026-11-07: 23.44) | nachgeführt (+0.08 USD) |\n")
    w(f"| Gewicht | {SCREENSHOT_WEIGHT_KG:.2f} kg (20 PCB, unbestückt) | {cm.WEIGHT_PACKAGING_KG + 20 * cm.WEIGHT_PER_BOARD_KG:.2f} kg "
      "(ANNAHME, nur Info) | Modell konservativ; Preis pauschal angenommen |\n")
    w("| Confirm Production File | No (Screenshot) | Soll **Yes** (ORDER Kap. 2) | Preis nicht belegt → **ANNAHME 0 USD**, "
      "am Bestelltag ablesen |\n")
    w("| Deburring/Edge rounding | Yes, 0.50 USD | im PCB-Preis | JLC: Pflicht-Aufpreis für Platinen mit einer Seite "
      "1.5–3 cm (0.02 USD/Stk, `docs/references/JLCPCB_ExtraCharges_Auszug_2026-11-08.txt` Nr. 6) |\n")
    w(f"| Coupons | 2 × „Save $20.00“ | nicht abgezogen | Bedingungen unbekannt (ANNAHME); je Coupon −{coupon_chf:.2f} CHF |\n\n")
    w("Die Aufschlüsselung bestätigt die Modellannahme D-005: Fixanteil (Engineering 25.00 + Via Covering + ENIG + "
      "Via Plating) dominiert, die Platine selbst kostet 10.20 USD für 20 Stück.\n\n")

    w("## 2 Sensor\n\n")
    w("| Szenario | PCBA | Stück CHF (D-005) | Einmal CHF | Bestellung total CHF | Vollkosten/Sensor CHF | JLC-Rechnung USD |\n")
    w("|---|---|---|---|---|---|---|\n")
    for k, (n, *_r) in scen.items():
        r = res[k]
        w(f"| {n} | {r['mode']} | **{r['unit_chf']:.2f}** | {r['once_chf']:.2f} | {r['total_chf']:.2f} | "
          f"{r['full_chf']:.2f} | {r['goods_usd']:.2f} |\n")
    w(f"\nREQ-FAB-04 (< 10 CHF Stückkosten bei 10–15 Stück, D-005): Serie **{s4['unit_chf']:.2f} CHF** (4 × 100 µF) "
      f"bzw. **{res['serie2']['unit_chf']:.2f} CHF** (2 × 100 µF) → **erfüllt**; mit Standard-PCBA "
      f"{res['std_serie']['unit_chf']:.2f} CHF (erfüllt, Paneelpreis ANNAHME).\n\n")
    w("### 2.1 Versteckte Kosten und Empfindlichkeiten\n\n")
    w("| Punkt | Wirkung | Behandlung |\n|---|---|---|\n")
    w(f"| Extended-Gebühr je Teiletyp | 10 × 3.07 = 30.70 USD je Bestellung | im Modell (Einmalkosten) |\n")
    w("| Mindestabnahmen/Verlust LCSC | Prototyp 3.13 / Serie 2.97 USD | im Modell (Einmalkosten) |\n")
    w("| Ausschuss lokale Teile | 5 % (ANNAHME) | im Modell |\n")
    w("| Reserveboard Serie | 16 bestückt für 15 Sensoren | im Modell (Stückkosten × 16/15) |\n")
    for k in ("proto", "serie4"):
        d = pre[k]["total_chf"] - res[k]["total_chf"]
        w(f"| „Pre-reflow Soldering“ 0.016 USD/Lötstelle (JLC-Preisseite, Anwendung nicht erklärt) – {scen[k][0]} | "
          f"+{d:.2f} CHF je Bestellung, falls berechnet | **nicht** im Modell; im Warenkorb prüfen |\n")
    w("| Confirm Production File = Yes | Preis unbekannt | ANNAHME 0 USD, am Bestelltag ablesen |\n")
    w(f"| Coupons 2 × 20 USD | bis −{2 * coupon_chf:.2f} CHF | nicht abgezogen (Bedingungen unbekannt) |\n")
    w("| Lager BT1 C5213768 (629 Stk, sinkend) | Ausfall → Ersatzteil/Layout | Bestand am Bestelltag prüfen |\n")
    w("| Verzollung DHL | 19 CHF + max(3 CHF; 2 %) je Sendung (K-2) | im Modell |\n\n")

    w("## 3 Gateway (W-8, REQ-FAB-06 separat ausgewiesen)\n\n")
    w("RTC-Entscheid (Vorschlag, OP-GW-3): **Adafruit PiRTC Precise DS3231** mit CR1220-Primärzelle. Belege: "
      "DS3231 ±2 ppm 0–40 °C (`docs/datasheets/Maxim_DS3231_Datasheet_19-5170Rev10.pdf` S. 1) ≙ 5 s/Monat "
      "(REQ-GW-09 ±2 min/Monat); Pufferstrom IBATT ≤ 3.0 µA (S. 3) → ≥ 24 h Haltezeit weit erfüllt; "
      "**kein Ladepfad**: VBAT nur Zelle + IC (`hardware/gateway/check_rtc_schematic.py` auf dem Adafruit-Schaltplan), "
      "VBAT-Pin UL-anerkannt gegen Rückladung einer Lithium-Primärzelle (S. 9). Linux-Treiber: `dtoverlay=i2c-rtc,ds3231` "
      "(`docs/appnotes/Adafruit_AddingRTC-RaspberryPi_Guide_2026-04-07.pdf`).\n\n")
    w("| Pos | Teil | Typ | Menge | CHF/Stk | Summe CHF | Status | Lager (Abruf) | Quelle |\n")
    w("|---|---|---|---|---|---|---|---|---|\n")
    for r in gw:
        w(f"| {r['Pos']} | {r['Teil']} | {r['Hersteller_Typ']} | {r['Menge']:g} | {r['Preis_CHF_Stk']:.2f} | "
          f"{r['sum']:.2f} | {r['Status']} | {r['Lager_Abruf']} | {r['Preisquelle'].split(' http')[0]} |\n")
    w(f"\n- **Kaufbetrag Gateway: {gw_buy:.2f} CHF** (Pi und XIAO vorhanden), davon {gw_annahme:.2f} CHF ANNAHME "
      f"(CR1220, Schrauben/Einsätze, ASA-Preis).\n")
    w(f"- Neuwert inkl. Pi Zero 2 W: {gw_new:.2f} CHF.\n")
    w(f"- Offen, nicht enthalten: {', '.join(r['Teil'] for r in gw_open)}.\n")
    w("- Nicht an Lager (pi-shop.ch 2026-11-08): Pi Zero 2 W (nicht nötig), microSD Industrial, Grove SHT41.\n\n")

    w("## 4 System (15 Sensoren + Gateway)\n\n")
    w("| Weg | Inhalt | CHF |\n|---|---|---|\n")
    w(f"| A: direkt Serie | Serie 20 PCB / 16 bestückt / 15 Sensoren + Gateway-Kauf | **{sysA:.2f}** |\n")
    w(f"| B: Prototyp + Serie (geplant) | Prototyp 5 + Serie 15 Sensoren + Gateway-Kauf | **{sysB:.2f}** |\n")
    w(f"| B + Programmieradapter | wie B + Adapter Rev 1 ({PROG_ADAPTER_CHF[0]:.0f}–{PROG_ADAPTER_CHF[1]:.0f} CHF, ANNAHME) | "
      f"{sysB_lo:.2f} – {sysB_hi:.2f} |\n\n")
    w(f"- Pro Sensor (Weg A, inkl. Gateway-Anteil): {sysA / 15:.2f} CHF; Weg B: {sysB / 15:.2f} CHF "
      f"(die 5 Prototypen sind zusätzlich nutzbar, falls sie die Prüfungen bestehen → dann 20 Sensoren: {sysB / 20:.2f} CHF).\n")
    w("- Nicht enthalten: Arbeitszeit, Werkzeug, Verguss-/Dichtmittel über die Sensor-Pauschalen hinaus, "
      "Status-LED-Platine Gateway, Ersatzzellen.\n\n")

    w("## 5 Annahmen und offene Punkte\n\n")
    w("- PCB 5 Stk (65.21 USD) stammt aus dem Angebot vom 2026-11-08 (CLIENT_INPUT), nicht aus dem Screenshot.\n")
    w("- Economic PCBA + ENIG + POFV + 4 Lagen: JLC-Doku sagt dazu nichts (`docs/references/JLCPCB_NOTES.md` Kap. 10) → "
      "BESTELL-PRÜFUNG; Ausweichen auf Standard-PCBA kostet Serie "
      f"+{res['std_serie']['total_chf'] - s4['total_chf']:.2f} CHF je Bestellung.\n")
    w("- Versandpreis mit PCBA (Gewicht höher) erst am Checkout sichtbar (ANNAHME pauschal 23.52 USD).\n")
    w("- Gateway: Netzteil-Konformität, microSD-Datenblatt, SHT41-Breakout-Schaltplan und CR1220-Datenblatt nicht lokal; "
      "Mechanik passt für RTC (21.3 × 20.0 mm) und Grove SHT41 (20 × 40 mm) nicht in die CAD-Platzhalter (15 × 12 bzw. "
      "24 × 14 mm) → Befund an Mechanik.\n\n")

    w("## 6 Einzelposten Sensor (cost_model.report)\n\n")
    from contextlib import redirect_stdout
    for k, (n, *_r) in scen.items():
        buf = io.StringIO()
        with redirect_stdout(buf):
            cm.report(res[k], n)
        w("```\n" + buf.getvalue().strip() + "\n```\n\n")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(md.getvalue())
    print(f"Screenshot-Summe {s_sum:.2f} USD = Modell {cr.QUOTE_USD[20]:.2f} USD")
    for k, (n, *_r) in scen.items():
        r = res[k]
        print(f"{n}: Stueck {r['unit_chf']:.2f}, Einmal {r['once_chf']:.2f}, total {r['total_chf']:.2f}, "
              f"voll {r['full_chf']:.2f} CHF")
    print(f"Gateway Kauf {gw_buy:.2f} CHF (ANNAHME-Anteil {gw_annahme:.2f}), Neuwert {gw_new:.2f} CHF")
    print(f"System A {sysA:.2f} CHF, B {sysB:.2f} CHF, B+Adapter {sysB_lo:.2f}-{sysB_hi:.2f} CHF")
    print("->", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
