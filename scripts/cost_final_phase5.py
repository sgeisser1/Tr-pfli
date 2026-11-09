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
PROG_ADAPTER_CHF = (25.0, 55.0)
# W-4 (Red Team Phase 6): BT1-Vorrat 25 Stk C5213768 in den privaten JLC-Bestand, JLC-Teilesuche 2026-11-09 01:28
# (Staffel ab 10 Stk 0.3615 USD; ORDER_JLC_REV_C.md Kap. 4 Nr. 8a). MWST bei der Einfuhr der Serie (ANNAHME).
BT1_VORRAT = (25, 0.3615)      # hardware/programmer/README.md Kap. 6 (ANNAHME-Spanne)


def dummy_chf():
    """Mehrkosten Dummy-Platinen (Weg B) in der JLC-Prototypbestellung: (Untergrenze, Obergrenze) CHF inkl. MWST/DHL-Anteil,
    gerechnet mit hardware/dummy_cell/gen/cost_dummy.py (Konstanten und increment_chf dort)."""
    sys.path.insert(0, os.path.join(ROOT, "hardware", "dummy_cell", "gen"))
    import cost_dummy as cd
    out = []
    for f in (cd.P_PROMO, cd.P_2L_5):
        usd = (f + cd.DEBURR * cd.QTY) + (f * cd.F_2MM + cd.DEBURR * cd.QTY)
        out.append(sum(cd.increment_chf(usd)))
    return out[0], out[1]


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
    # W-5 (Red Team Phase 5): Kaufbetrag nur fuer kauffertige Zeilen; offene/nicht lieferbare separat
    buy = [r for r in gw if r["Status"] in ("kauffertig", "Eigenfertigung")]
    pend = [r for r in gw if r["Status"] in ("Entscheid offen", "nicht an Lager")]
    gw_buy = sum(r["sum"] for r in buy)
    gw_pend = sum(r["sum"] for r in pend)
    gw_plan = gw_buy + gw_pend
    gw_new = gw_plan + sum(r["sum"] for r in gw if r["Status"] == "vorhanden")
    gw_annahme = sum(r["sum"] for r in buy if "ANNAHME" in r["Preisquelle"])
    gw_open = [r for r in gw if r["Status"] == "offen"]

    # --- 4 System
    s4, pr = res["serie4"], res["proto"]
    # Verguss-Zubehoer/Schutz und Programmieradapter einmalig je Projekt: Phase 6 aus der Einkaufsliste
    # (docs/manuals/EINKAUFSLISTE.csv, teils CH-Shopbelege, Rest ANNAHME Konzept Kap. 7.1); Rueckfall: cost_rev_b-Pauschale
    zub, zub_ann, prog, prog_ann, zub_src = cr.ZUBEHOER_VERGUSS_CHF, cr.ZUBEHOER_VERGUSS_CHF, None, None, "Konzept Kap. 7.1 (ANNAHME)"
    try:
        import einkaufsliste as ek
        ekr = [r for r in ek.load() if r["Status"] not in ek.NICHT_SUMMIEREN]
        vz = [r for r in ekr if r["ID"].startswith("V-Z")]
        zub = round(sum(r["_sum"] for r in vz), 2)
        zub_ann = round(sum(r["_sum"] for r in vz if r["_annahme"]), 2)
        pz = [r for r in ekr if r["Bereich"] == "Programmieradapter" or r["ID"] == "W1"]
        lcsc_v = ek.VERSAND["LCSC (mit JLC-Bestellung buendeln, ANNAHME)"][0]
        prog = round(sum(r["_sum"] for r in pz) + lcsc_v, 2)
        prog_ann = round(sum(r["_sum"] for r in pz if r["_annahme"]) + lcsc_v, 2)
        zub_src = ("Einkaufsliste V-Z, nur Verbrauchsmaterial; Ausrüstung beim Auftraggeber vorhanden (2026-11-09), "
                   "`docs/manuals/EINKAUFSLISTE.csv`")
    except (ImportError, OSError, KeyError):
        pass
    sysA = s4["total_chf"] + gw_plan + zub
    sysB = pr["total_chf"] + s4["total_chf"] + gw_plan + zub
    unit_pre = pre["serie4"]["unit_chf"]
    sysB_lo, sysB_hi = sysB + PROG_ADAPTER_CHF[0], sysB + PROG_ADAPTER_CHF[1]
    dum_lo, dum_hi = dummy_chf()
    sysB_prog = sysB + prog + dum_hi if prog is not None else None

    md = io.StringIO()
    w = md.write
    w("# Phase 5 – Kostenrechnung final (Sensor, Gateway, System)\n\n")
    w("| | |\n|---|---|\n")
    w("| Stand | Sensor 2026-11-08, Vergussmasse 2026-11-09 (Kap. 2.0), Gateway 2026-11-09 (D-028/D-029), erzeugt von `.venv/bin/python scripts/cost_final_phase5.py` (nicht von Hand ändern) |\n")
    w(f"| Kurs | 1 USD = {cm.USD_TO_CHF:.4f} CHF, {cm.FX_DATE}; + {cm.FX_CARD_MARKUP*100:.1f} % Kartenaufschlag (ANNAHME) "
      f"= {fx():.4f} CHF; 2026-11-08 ist ein Sonntag, neuester EZB-Kurs = 2026-11-06 |\n")
    w("| Sensor | `hardware/sensor/gen/cost_rev_b.py` → `scripts/cost_model.compute` (D-005), Teilepreise "
      f"`docs/concepts/bom/jlc_prices.json` (Abruf {cr.PRICES['_abruf']}), Lager live 2026-11-08 13:06 (`order_check.py --live`) |\n")
    w("| Gateway | `hardware/gateway/BOM_GATEWAY.csv` (Preise pi-shop.ch/bastelgarage.ch, Abruf 2026-11-08/09, "
      "`docs/references/pi-shop_Gateway-Teile_Auszug_2026-11-08.txt`, `docs/references/Haendler_Einkauf_Auszug_2026-11-09.txt`; D-028/D-029) |\n")
    w("| Bestellunterlage | `hardware/sensor/out/ORDER_JLC_REV_C.md`, Anleitung `docs/manuals/BESTELLEN_JLC.md` |\n\n")

    w("## 0 Fazit\n\n")
    w(f"- **Stückkosten nach D-005** (REQ-FAB-04, Grenzkosten pro Sensor ohne Einmalkosten): Serie **{s4['unit_chf']:.2f} CHF** "
      f"→ < 10 CHF erfüllt, **unter Vorbehalt**: Berechnet JLC „Pre-reflow Soldering“ (0.016 USD/Lötstelle), steigen sie "
      f"auf **{unit_pre:.2f} CHF** → REQ-FAB-04 **verfehlt** (Kap. 2.1, Stopp-Kriterium im Warenkorb).\n")
    w(f"- **Vollkosten** (ganze Bestellung inkl. Einmalkosten / Sensoren): Serie **{s4['full_chf']:.2f} CHF/Sensor**; "
      f"mit Prototyp-Los und Gateway {sysB / 15:.2f} CHF/Sensor (15 Sensoren). Das ist, was ein Sensor real kostet.\n")
    w("- D-005 (Definition Stückkosten) hat Status „zur Kenntnis“; der Auftraggeber sollte ausdrücklich bestätigen, dass "
      "REQ-FAB-04 die Stückkosten nach D-005 meint und nicht die Vollkosten.\n")
    w(f"- Gateway: kauffertig {gw_buy:.2f} CHF, offen/nicht lieferbar {gw_pend:.2f} CHF, geplant total {gw_plan:.2f} CHF.\n\n")
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
      f"bzw. **{res['serie2']['unit_chf']:.2f} CHF** (2 × 100 µF) → **erfüllt unter Vorbehalt** „Pre-reflow Soldering“ "
      f"(falls berechnet: {unit_pre:.2f} CHF, **verfehlt**, Kap. 2.1); mit Standard-PCBA "
      f"{res['std_serie']['unit_chf']:.2f} CHF (erfüllt, Paneelpreis ANNAHME).\n\n")
    w("### 2.0 Vergussmasse (Phase 6, D-030-Vorschlag, Variante M-A)\n\n")
    w(f"Electrolube ER2223 Resin Pack 250 g, Simpex CH CHF 38.20 exkl. MWST = **{cr.VERGUSS_BEUTEL_CHF:.2f} CHF** inkl. MWST "
      f"(Abruf 2026-11-08). Variante M-A (abfüllen, 8-g-Ansätze wägen, `docs/manuals/MONTAGE_SENSOR.md` Kap. 3a): **1 Beutel je "
      f"Bestellung** (angebrochen max. 3 Monate, ANNAHME). Stückkosten = Verbrauch {cr.VERGUSS_G_PRO_SENSOR:.0f} g/Sensor = "
      f"{cr.VERGUSS_CHF_PRO_SENSOR:.2f} CHF (+5 % Ausschuss); Einmalkosten = Beutelrest (Prototyp "
      f"{pr['verguss_once_chf']:.2f}, Serie {s4['verguss_once_chf']:.2f} CHF), Einordnung nach D-005 durch den Orchestrator. "
      f"Zubehör/Schutzausrüstung einmalig je Projekt **{zub:.2f} CHF** ({zub_src}, davon {zub_ann:.2f} CHF ANNAHME; "
      f"in der Systemsumme Kap. 4). "
      "Hinweis M-B (ganzer Beutel je Sitzung): Prototyp 3 + Serie 3 Beutel = "
      f"{6 * cr.VERGUSS_BEUTEL_CHF:.2f} CHF statt {2 * cr.VERGUSS_BEUTEL_CHF:.2f} CHF.\n\n")
    w("### 2.1 Versteckte Kosten und Empfindlichkeiten\n\n")
    w("| Punkt | Wirkung | Behandlung |\n|---|---|---|\n")
    w(f"| Extended-Gebühr je Teiletyp | 10 × 3.07 = 30.70 USD je Bestellung | im Modell (Einmalkosten) |\n")
    w("| Mindestabnahmen/Verlust LCSC | Prototyp 3.13 / Serie 2.97 USD | im Modell (Einmalkosten) |\n")
    w("| Ausschuss lokale Teile | 5 % (ANNAHME) | im Modell |\n")
    w("| Reserveboard Serie | 16 bestückt für 15 Sensoren | im Modell (Stückkosten × 16/15) |\n")
    for k in ("proto", "serie4"):
        d = pre[k]["total_chf"] - res[k]["total_chf"]
        w(f"| „Pre-reflow Soldering“ 0.016 USD/Lötstelle (JLC-Preisseite, Anwendung nicht erklärt) – {scen[k][0]} | "
          f"+{d:.2f} CHF je Bestellung, Stückkosten {res[k]['unit_chf']:.2f} → **{pre[k]['unit_chf']:.2f} CHF** (D-005: "
          f"pro Lötstelle = Stückkosten) | **nicht** im Modell; **Stopp-Kriterium** im Warenkorb (Anleitung Schritt 9, ORDER Kap. 4 Nr. 11) |\n")
    w("| Confirm Production File = Yes | Preis unbekannt | ANNAHME 0 USD, am Bestelltag ablesen |\n")
    w(f"| Coupons 2 × 20 USD | bis −{2 * coupon_chf:.2f} CHF | nicht abgezogen (Bedingungen unbekannt) |\n")
    w("| Lager BT1 C5213768 (629 Stk, sinkend) | Ausfall → Ersatzteil/Layout | Bestand am Bestelltag prüfen |\n")
    w("| Verzollung DHL | 19 CHF + max(3 CHF; 2 %) je Sendung (K-2) | im Modell |\n")
    w("| Versand mit PCBA | Serie geschätzt ≈ 0.55 kg; DHL-Stufe über 0.5 kg evtl. einige USD teurer (ANNAHME) | pauschal 23.52 USD; im 10-%-Stoppkriterium enthalten |\n")
    w("| Zahlungsweg | Modell +1.5 % (ANNAHME); PayPal-Umrechnung meist teurer (ANNAHME, < 3 CHF je Bestellung) | Karte ohne Fremdwährungsgebühr empfohlen |\n\n")

    w("## 3 Gateway (W-8, REQ-FAB-06 separat ausgewiesen)\n\n")
    w("Stand Phase 6 (2026-11-09): **D-028** Gateway ohne RTC (G4 PiRTC DS3231 und G5 CR1220 gestrichen, Zeit per NTP, "
      "Rückfall `phase5_gateway_zeit.md`); **D-029** Klimasensor = DFRobot Fermion SHT40 SEN0428 (14 × 17 mm, passt in die "
      "Klimakammer; Auswahl und Belege `docs/manuals/EINKAUFSLISTE.md` Kap. 2). Bezugsquellen und Versand: Einkaufsliste.\n\n")
    w("| Pos | Teil | Typ | Menge | CHF/Stk | Summe CHF | Status | Lager (Abruf) | Quelle |\n")
    w("|---|---|---|---|---|---|---|---|---|\n")
    for r in gw:
        w(f"| {r['Pos']} | {r['Teil']} | {r['Hersteller_Typ']} | {r['Menge']:g} | {r['Preis_CHF_Stk']:.2f} | "
          f"{r['sum']:.2f} | {r['Status']} | {r['Lager_Abruf']} | {r['Preisquelle'].split(' http')[0]} |\n")
    w(f"\n- **Kauffertig: {gw_buy:.2f} CHF** (Netzteil, SHT40-Breakout, Status-LED, Schrauben/Einsätze, Gehäusedruck, Versand pi-shop.ch und "
      f"bastelgarage.ch), davon {gw_annahme:.2f} CHF ANNAHME. **Noch nicht kaufbar: {gw_pend:.2f} CHF** (G3 microSD Industrial "
      f"bei pi-shop.ch nicht an Lager; Alternative gleicher Serie sofort lieferbar, aber 56.95–63.95 CHF, Einkaufsliste). "
      f"Geplant total {gw_plan:.2f} CHF (Systemsumme rechnet damit).\n")
    w(f"- Neuwert inkl. Pi Zero 2 W: {gw_new:.2f} CHF.\n")
    w(f"- Offen, nicht enthalten: {', '.join(r['Teil'] for r in gw_open)}.\n")
    w("- Nicht an Lager (pi-shop.ch 2026-11-09): Pi Zero 2 W (vorhanden, nicht nötig), microSD Industrial (G3).\n\n")

    w("## 4 System (15 Sensoren + Gateway)\n\n")
    w("| Weg | Inhalt | CHF |\n|---|---|---|\n")
    w(f"| A: direkt Serie | Serie 20 PCB / 16 bestückt / 15 Sensoren + Gateway (geplant total) | **{sysA:.2f}** |\n")
    w(f"| B: Prototyp + Serie (geplant) | Prototyp 5 + Serie 15 Sensoren + Gateway (geplant total) | **{sysB:.2f}** |\n")
    w(f"| davon Verguss-Zubehör/Schutz (A und B je einmal) | Kap. 2.0, {zub_src}, davon {zub_ann:.2f} ANNAHME | {zub:.2f} |\n")
    if sysB_prog is not None:
        w(f"| B + Programmierwerkzeug | wie B + Adapter Rev 1 inkl. PL2303-Board und LCSC-Versand (Einkaufsliste P1–P9, W1; "
          f"{prog:.2f} CHF, davon {prog_ann:.2f} ANNAHME) + Dummy-Platinen Weg B als Einmalkosten des Prototyp-Loses "
          f"({dum_lo:.2f}–{dum_hi:.2f} CHF, Obergrenze gerechnet, `hardware/dummy_cell/gen/cost_dummy.py`) | {sysB_prog:.2f} |\n\n")
    else:
        w(f"| B + Programmieradapter | wie B + Adapter Rev 1 ({PROG_ADAPTER_CHF[0]:.0f}–{PROG_ADAPTER_CHF[1]:.0f} CHF, ANNAHME) | "
          f"{sysB_lo:.2f} – {sysB_hi:.2f} |\n\n")
    w(f"- Pro Sensor (Weg A, inkl. Gateway-Anteil): {sysA / 15:.2f} CHF; Weg B: {sysB / 15:.2f} CHF "
      f"(die 5 Prototypen sind zusätzlich nutzbar, falls sie die Prüfungen bestehen → dann 20 Sensoren: {sysB / 20:.2f} CHF).\n")
    w("- Nicht enthalten: Arbeitszeit, Werkzeug (ausser Verguss-Zubehör Kap. 2.0), Dichtmittel über die Sensor-Pauschalen hinaus, "
      "Status-LED-Platine Gateway, Ersatzzellen.\n\n")

    # --- 4a Kassenbedarf (W-2, Red Team Phase 6): alle Rechnungen, keine Kostenzuordnung
    def jlc_cash(r):
        return r["base_chf"] + r["vat_chf"] + r["carrier_fee_chf"]
    jlc_p, jlc_s = jlc_cash(pr), jlc_cash(s4)
    jlc_p_pre, jlc_s_pre = jlc_cash(pre["proto"]), jlc_cash(pre["serie4"])
    bt1_chf = BT1_VORRAT[0] * BT1_VORRAT[1] * fx() * (1 + cm.CH_VAT)
    dum_lo, dum_hi = dummy_chf()
    sm = None
    try:
        import einkaufsliste as ek
        sm = ek.summen(ek.load())
    except (ImportError, OSError, KeyError, AttributeError):
        pass
    if sm is not None:
        mu, se = sm["muster"], sm["serie"]
        k_mu = jlc_p + bt1_chf + dum_hi + mu["ware"] + mu["vers"]
        k_mu_pre = jlc_p_pre + bt1_chf + dum_hi + mu["ware"] + mu["vers"]
        k_se = jlc_s + se["ware"] + se["vers"]
        k_se_pre = jlc_s_pre + se["ware"] + se["vers"]
        kasse, kasse_pre = k_mu + k_se, k_mu_pre + k_se_pre
        ek_ware, ek_vers, ek_ann = mu["ware"] + se["ware"], mu["vers"] + se["vers"], mu["ann"] + se["ann"]
        w("## 4a Kassenbedarf (alle Rechnungen; Red Team Phase 6 W-2): nur Muster, Serie danach, gesamt\n\n")
        w("Kap. 4 ist eine Kostenzuordnung (Grenz- und Einmalkosten). Bar bezahlt werden ganze Packungen, Versand und "
          "Testzellen. **Stand 2026-11-09: Der Auftraggeber hat das Zubehör komplett** (Verguss-/Schutzzubehör V-Z1–V-Z4, "
          "V-Z8–V-Z12, Werkstatt Weg B, TX6, Etikettiergerät) → nicht bestellt; Verbrauchsmaterial bleibt bestellt "
          "(`docs/manuals/EINKAUFSLISTE.md` Kap. 1). Die Verguss-Beutel sind nur in der Einkaufsliste gezählt.\n\n")
        w("| Rechnung | Muster (Prototyp-Los, ohne Serie) CHF | Serie danach CHF |\n|---|---|---|\n")
        w(f"| JLC Sensor-PCBA (Ware + MWST + Verzollung DHL) | {jlc_p:.2f} | {jlc_s:.2f} |\n")
        w(f"| JLC BT1-Vorrat {BT1_VORRAT[0]} × C5213768 à {BT1_VORRAT[1]} USD (privater Bestand, MWST ANNAHME) | {bt1_chf:.2f} | – |\n")
        w(f"| JLC Dummy-Platinen PLUS/MINUS je 5 Stk (`cost_dummy.py`, Obergrenze; Untergrenze {dum_lo:.2f}) | {dum_hi:.2f} | – |\n")
        w(f"| Einkaufsliste Ware (Muster: LCSC, 1 Verguss-Beutel, Filament, Zellen Muster + Tests + Serie, Gateway, "
          f"Kleinteile, Verbrauchsmaterial; Serie: 2. Verguss-Beutel) | {mu['ware']:.2f} | {se['ware']:.2f} |\n")
        w(f"| Einkaufsliste Versand | {mu['vers']:.2f} | {se['vers']:.2f} |\n")
        w(f"| **Summe ohne Pre-reflow** | **{k_mu:.2f}** | **{k_se:.2f}** |\n")
        w(f"| Summe mit Pre-reflow | {k_mu_pre:.2f} | {k_se_pre:.2f} |\n\n")
        w(f"**Gesamt (Muster + Serie): {kasse:.2f} CHF**, mit Pre-reflow {kasse_pre:.2f} CHF.\n\n")
        w(f"- Preis-ANNAHME in der Einkaufsliste: Muster {mu['ann']:.2f} CHF, Serie {se['ann']:.2f} CHF (Händler offen, "
          "gesperrte Shopseiten); Versand teils ANNAHME.\n")
        w("- Verguss 1 Beutel für das Muster, 1 Beutel für die Serie: angebrochen 3 Monate haltbar (MA-3), Serie erst nach dem "
          "Mustertest, bei Rückfallmasse (Konzept Kap. 9a) wäre ein zweiter Beutel umsonst; Lieferzeit 8 Wochen.\n")
        w("- Zellen (48er-Packung), Filament (ganze Spulen) und Kleinteil-Packungen werden mit dem Muster gekauft und reichen "
          "für die Serie; die Seriensumme enthält sie deshalb nicht.\n")
        w("- Nicht enthalten: Pi Zero 2 W (vorhanden), Zubehör/Werkstatt (vorhanden), Arbeitszeit, Coupons. Die Serie zieht "
          "BT1 aus dem Vorrat; die Serien-JLC-Rechnung sinkt dann um ≈ 16 × 0.36 USD (nicht abgezogen, konservativ).\n\n")
    w("## 5 Annahmen und offene Punkte\n\n")
    w("- PCB 5 Stk (65.21 USD) stammt aus dem Angebot vom 2026-11-08 (CLIENT_INPUT), nicht aus dem Screenshot.\n")
    w("- Economic PCBA + ENIG + POFV + 4 Lagen: JLC-Doku sagt dazu nichts (`docs/references/JLCPCB_NOTES.md` Kap. 10) → "
      "BESTELL-PRÜFUNG; Ausweichen auf Standard-PCBA kostet Serie "
      f"+{res['std_serie']['total_chf'] - s4['total_chf']:.2f} CHF je Bestellung.\n")
    w("- Versandpreis mit PCBA (Gewicht höher) erst am Checkout sichtbar (ANNAHME pauschal 23.52 USD).\n")
    w("- Gateway: Netzteil-Konformität nicht lokal (Sicherheits-Agent beim Wareneingang); microSD-Datenblatt "
      "(`Kingston_SDCIT2_Datasheet_MKD-02122026.pdf`) und SHT40-Breakout-Schaltplan/Masse (`DFRobot_SEN0428_*`) seit 2026-11-09 lokal; "
      "RTC/CR1220 entfallen (D-028). Klimakammer mit Bodenschiene + Deckelrippe für SEN0428 (D-032).\n\n")
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
    print(f"Gateway kauffertig {gw_buy:.2f} CHF (ANNAHME-Anteil {gw_annahme:.2f}), offen {gw_pend:.2f}, geplant {gw_plan:.2f}, "
          f"Neuwert {gw_new:.2f} CHF; Serie mit Pre-reflow {unit_pre:.2f} CHF")
    print(f"System A {sysA:.2f} CHF, B {sysB:.2f} CHF, B+Adapter " + (f"{sysB_prog:.2f}" if sysB_prog is not None else f"{sysB_lo:.2f}-{sysB_hi:.2f}") + f" CHF (Zubehoer Verguss {zub:.2f}, Adapter {prog})")
    if sm is not None:
        print(f"Kasse Muster {k_mu:.2f} (Pre-reflow {k_mu_pre:.2f}), Serie {k_se:.2f} (Pre-reflow {k_se_pre:.2f}) CHF")
        print(f"Kassenbedarf {kasse:.2f} CHF (mit Pre-reflow {kasse_pre:.2f}); JLC P {jlc_p:.2f} S {jlc_s:.2f} BT1 {bt1_chf:.2f} "
              f"Dummy {dum_lo:.2f}-{dum_hi:.2f}; "
              f"Einkauf {ek_ware:.2f} + {ek_vers:.2f}, ANNAHME {ek_ann:.2f}")
    print("->", os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
