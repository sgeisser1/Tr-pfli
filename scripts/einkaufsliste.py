#!/usr/bin/env python3
"""fluidi Phase 6 - Einkaufsliste (alles, was nicht von JLC kommt): Pruefung + Summen + Haendlergruppierung.

Eingabe : docs/manuals/EINKAUFSLISTE.csv   (Datenquelle, von Hand gepflegt; Preise/Lager mit Abrufdatum und Beleg)
Ausgabe : docs/manuals/EINKAUFSLISTE.md    (erzeugt, nicht von Hand aendern)
Aufruf  : .venv/bin/python scripts/einkaufsliste.py [--check]
          --check: nur pruefen (Pflichtfelder, Packungen x Inhalt >= Bedarf, Beleg-/Registerverweise), Exitcode 1 bei Fehlern

Versandregeln je Haendler (VERSAND) mit Quelle; ANNAHMEN sind markiert.
"""
import csv
import io
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(ROOT, "docs", "manuals", "EINKAUFSLISTE.csv")
OUT = os.path.join(ROOT, "docs", "manuals", "EINKAUFSLISTE.md")
INDEX = os.path.join(ROOT, "docs", "datasheets", "INDEX.csv")
EX = "docs/references/Haendler_Einkauf_Auszug_2026-11-09.txt"

# Haendler -> (Versand CHF, gratis ab CHF Warenwert oder None, Quelle)
VERSAND = {
    "bastelgarage.ch": (6.90, 80.0, "bastelgarage.ch/lieferung-versandkosten (2026-11-09): PostPac Economy 6.90, Priority 8.90, "
                        "ab CHF 80 Warenwert gratis (" + EX + ")"),
    "pi-shop.ch": (7.90, None, "pi-shop.ch/versandkosten (2026-11-08): B-Post 7.90, A-Post 9.90 "
                   "(docs/references/pi-shop_Gateway-Teile_Auszug_2026-11-08.txt)"),
    "galaxus.ch": (9.90, None, "ANNAHME (Versandseite nicht abrufbar, Bot-Sperre)"),
    "3djake.ch": (8.90, 69.90, "3djake.ch/de-CH/hilfe/versandkosten (2026-11-09): Standardversand Schweiz 8.90, ab CHF 69.90 "
                  "gratis (docs/references/3DJake_PolymakerASA-Natural_Auszug_2026-11-09.txt)"),
    "offen (Normteile-/Dichtungs-Fachhandel)": (10.00, None, "ANNAHME (Haendler offen, eine Sammelbestellung S2/S5/G8b/P8)"),
    "offen (Platzhalter)": (0.00, None, "Platzhalter"),
    "Digi-Key CH (laut phase5_gateway_led.md)": (0.00, None, "nicht einzeln bestellen (23 CHF Versand unter 70 CHF, "
                                                 "docs/reviews/phase5_gateway_led.md): mit LCSC-Bestellung Programmieradapter buendeln"),
    "Werkstattbestand": (0.00, None, "-"),
    "LCSC + Fachhandel (siehe README)": (0.00, None, "im Werkzeugbudget hardware/programmer/README.md Kap. 6"),
    "LCSC (mit JLC-Bestellung buendeln, ANNAHME)": (20.00, None, "ANNAHME (README Kap. 6: 10-25 CHF), Kombination mit der "
                                                    "JLC-Sendung im Warenkorb pruefen"),
    "Simpex Electronic AG": (15.00, None, "ANNAHME (Versandbetrag laut Konzept Kap. 7 nicht angegeben)"),
    "offen (Labor-/Arbeitsschutz-Fachhandel)": (10.00, None, "ANNAHME (Haendler offen, eine Sammelbestellung V-Z2/V-Z3/V-Z4/V-Z5d/V-Z6b/V-Z11)"),
}
BEREICHE = ["Sensor", "Sensor+Werkstatt", "Sensor+Gateway", "Gateway", "Werkstatt", "Verguss", "Programmieradapter",
            "Werkstatt Weg B"]
NICHT_SUMMIEREN = {"vorhanden", "separat", "Platzhalter", "entfaellt, falls vorhanden (Werkstatt)"}
REQ = ["ID", "Bereich", "Teil", "Spezifikation_Soll", "Bedarf_Stk", "Haendler", "Packung_Stk", "Preis_CHF_Packung",
       "Packungen", "Preisbasis", "Lager", "Abruf", "Status"]


def load():
    rows = list(csv.DictReader(open(SRC, encoding="utf-8"), delimiter=";"))
    for r in rows:
        r["_bedarf"] = float(r["Bedarf_Stk"])
        r["_pack"] = float(r["Packung_Stk"])
        r["_n"] = float(r["Packungen"])
        r["_preis"] = float(r["Preis_CHF_Packung"])
        r["_sum"] = round(r["_n"] * r["_preis"], 2)
        r["_annahme"] = r["Preisbasis"].startswith("ANNAHME") or r["Status"] in ("Quelle offen", "Platzhalter")
        r["_jetzt"] = (r["Lager"] not in ("nicht an Lager", "Ausverkauft") and not r["Status"].startswith("Quelle offen")
                      and not r["Haendler"].startswith("offen"))
    return rows


def check(rows):
    err, warn = [], []
    reg = {}
    for x in csv.reader(open(INDEX, encoding="utf-8"), delimiter=";"):
        if x:
            reg[x[0].strip()] = x
    ids = set()
    for r in rows:
        if r["ID"] in ids:
            err.append(f"{r['ID']}: ID doppelt")
        ids.add(r["ID"])
        for k in REQ:
            if not r.get(k, "").strip():
                err.append(f"{r['ID']}: Pflichtfeld {k} leer")
        if r["Status"] not in NICHT_SUMMIEREN and r["_n"] * r["_pack"] < r["_bedarf"]:
            err.append(f"{r['ID']}: Packungen x Inhalt {r['_n'] * r['_pack']:g} < Bedarf {r['_bedarf']:g}")
        if r["Bereich"] not in BEREICHE:
            err.append(f"{r['ID']}: Bereich '{r['Bereich']}' unbekannt")
        if r["Haendler"] not in VERSAND:
            err.append(f"{r['ID']}: Haendler '{r['Haendler']}' ohne Versandregel")
        b = r["Beleg"].strip()
        if b and b != "-" and not os.path.exists(os.path.join(ROOT, b)):
            err.append(f"{r['ID']}: Beleg fehlt: {b}")
        for ref in [s.strip() for s in r["Register"].split(" + ")] if r["Register"].strip() not in ("", "-") else []:
            if ref not in reg:
                warn.append(f"{r['ID']}: Register-Ref '{ref}' nicht in INDEX.csv")
        if r["Lager"] in ("nicht an Lager", "Ausverkauft"):
            warn.append(f"{r['ID']}: {r['Haendler']} {r['Lager']} (Abruf {r['Abruf']})")
        if r["_annahme"] and r["Status"] not in NICHT_SUMMIEREN:
            warn.append(f"{r['ID']}: Preis ANNAHME/Quelle offen ({r['_sum']:.2f} CHF)")
    return err, warn


def haendler(rows):
    g = {}
    for r in rows:
        if r["Status"] in NICHT_SUMMIEREN:
            continue
        g.setdefault(r["Haendler"], []).append(r)
    res = []
    for h, rs in g.items():
        ware = round(sum(r["_sum"] for r in rs), 2)
        ware_jetzt = round(sum(r["_sum"] for r in rs if r["_jetzt"]), 2)
        v, frei, q = VERSAND[h]
        vers = 0.0 if (frei is not None and ware >= frei) else v
        vers_jetzt = 0.0 if (frei is not None and ware_jetzt >= frei) or ware_jetzt == 0 else v
        res.append(dict(h=h, rows=rs, ware=ware, vers=vers, ware_jetzt=ware_jetzt, vers_jetzt=vers_jetzt, frei=frei, q=q))
    return sorted(res, key=lambda d: -d["ware"])


TEXT_SHT = """## 2 Klimasensor-Breakout Gateway (D-029, G6)

Platz (CAD `mechanical/gen/fluidi_gateway_pi.py`, Konstante `CLIMA`, Prüfung 11/14 in
`mechanical/gateway_pi/check_gateway_pi.txt`): Klimakammer innen **x 8.0 × y 38.0 × z 16.0 mm** (x 32…40, Wand 2 mm).
Das Modul steht hochkant in der y-z-Ebene, Sensorseite +x zur Stirnwand. Hochkant ist z ≤ 14 nutzbar (z 3…17 in 2…18),
flach liegend nur 8 mm (x).

| Kandidat | Masse (Quelle) | Elektrik (Quelle) | Bezug CH (Abruf 2026-11-09) | Passt? |
|---|---|---|---|---|
| **DFRobot Fermion SHT40 SEN0428** | **14.0 × 17.0 mm**, 2 × Ø2.0 im Raster 10.0, 4 Lötaugen VCC/GND/SCL/SDA an einer 14-mm-Kante (`docs/datasheets/DFRobot_SEN0428_Dimensions_V0.1.png`; Wiki „Dimension 14×17mm“) | VCC 3.3–5 V (Wiki); LDO → „3V“, Pegelwandler 2 × 2N7002, 10 kΩ Pull-ups beidseitig (`docs/datasheets/DFRobot_SEN0428_Schematic_V0.1.pdf`); SHT40 VDD 1.08–3.6 V (`docs/datasheets/Sensirion_SHT4x_Datasheet_V7.3.pdf` S. 9); Adresse 0x44 (DFRobot-Bibliothek `DFRobot_SHT40.h` Z. 20, SHT40-AD1B; Sensirion S. 21/22) | bastelgarage.ch Art. 421989, **CHF 11.90, lagernd** | **ja**, hochkant 17 (y) × 14 (z) |
| Adafruit SHT41 STEMMA QT (5776) | 25.4 × 17.8 mm (1.00 × 0.70 in, `docs/datasheets/Adafruit_5776_SHT41_FabPrint_2023-07.png`) | Regler + Pegelwandler (`…_Schematic_2023-07.png`) | play-zone.ch Art. ada-5776, CHF 9.90, > 10 an Lager (Versand ab 300 CHF frei, Tarif nicht abgelesen) | nein: 17.8 > 16 (hochkant), > 8 (flach) |
| Seeed Grove SHT41 (bisher G6) | 20 × 40 mm (`docs/references/Seeed_Grove-SHT4x_Wiki_Auszug_2026-11-08.txt`) | Schaltplan nicht lokal | pi-shop.ch Art. 12042, CHF 8.90, nicht an Lager | nein: 40 > 38 |

Gesucht, aber ohne CH-Quelle: 7Semi SHT40/SHT41-Kleinstbreakouts (nur indische Händler), Generika ohne Schaltplan.
pi-shop.ch führt kein weiteres SHT4x-Breakout (Suche „sht40“ 2026-11-09: nur CO2-Sensor/E-Paper-Kit, Beleg im Auszug).

**Empfehlung: DFRobot SEN0428** – einziges gefundenes SHT4x-Breakout mit Herstellermass und Schaltplan, das in die
Kammer passt, ab Lager in der Schweiz, beim selben Händler wie Muttern/Einsätze/Kleber (kein zusätzlicher Versand).

**Umsetzung Mechanik (D-032, `mechanical/gateway_pi/check_gateway_pi.txt` Pkt. 14):** SEN0428 hochkant 17.0 (y) × 14.0 (z),
gehalten von einer **Bodenschiene** (Nut 1.90 breit, Eingriff 1.00) und einer **Deckelrippe** (Eingriff 0.80, 0.30 Luft über
der Oberkante), Endanschläge mit je 0.30 Luft in y; Bauteilfreiheit zur Schiene 0.45 mm, zur Deckelrippe 0.65 mm.
**Platinendicke 1.6 mm und Bauteilhöhen sind ANNAHME** (Hersteller gibt sie nicht an) → am Muster messen.

**Befund (klein):** Der vom DFRobot-Wiki für SEN0428 verlinkte Schaltplan trägt Titel und Bauteil „SHTC3“
(SKU-D008, Schwesterprodukt SEN0414). Topologie (LDO, 2N7002, 10 kΩ) plausibel, die Sensor-Pinbelegung im Plan gilt
nicht für den SHT40. **PROTOTYP-PRÜFUNG:** 3V-Schiene messen, Pull-ups messen, `i2cdetect -y 1` zeigt 0x44, Messwerte
plausibel (Treiber `climate.py`, D-017). Anschluss: VCC an Pi-3V3 (Pin 1), GND, SDA/SCL Pins 3/5.

"""

TEXT_UART = """## 3 USB-UART für den Programmieradapter (FW-T3)

Anforderung (`docs/manuals/INSTALL_FIRMWARE_TOOLS.md`, `hardware/programmer/README.md`): VIO extern 2.0 V aus dem
Adapter, kein Rückstrom, ROM-Bootloader 19 200–57 600 Baud, +5 V vom USB für die Adapterregler.

| Option | Bezug (Abruf) | Kosten inkl. Versand | Bewertung |
|---|---|---|---|
| A Waveshare **CH343 USB UART Board** SKU 21440–21443 (TOOL-UART1, bisher geplant) | waveshare.com USD 3.49 (2026-11-07), Seite JS-basiert, Lager/Versand nicht ablesbar; eckstein-shop.de Art. WS21443 EUR 4.15, „ca. 3 Wochen“, Seite meldet „nicht in Ihr Lieferland“ (Land nicht erkennbar); kein CH-Händler gefunden (pi-shop.ch „ch343“: nur Geräte mit CH343-Chip, z. B. Industrial USB TO TTL mit festem 3.3/5-V-Pegel; bastelgarage.ch, play-zone.ch: keine Treffer) | ≈ 3–4 CHF + Auslandsversand **ANNAHME 10–25 CHF** (programmer/README Kap. 6) | elektrisch belegt (CH343-Datenblatt), aber eigener Auslandsversand |
| **B Waveshare PL2303 USB UART Board (type A) V2** (PL2303GS, TOOL-UART2) | **pi-shop.ch Art. 11757, CHF 8.90, Sofort-Versand** (2026-11-09) | **8.90 CHF, kein Zusatzversand** (mit G2/G3 bei pi-shop.ch) | **freigegeben mit Bedingungen** (Elektronik 2026-11-09), siehe unten |
| C Adafruit CH9102F Friend / Waveshare Industrial USB TO TTL (CH343G) | pi-shop.ch CHF 7.90 / 12.90 | – | **ungeeignet**: Pegel fest 3.3/5 V per Schalter, kein externes VIO |

Begründung B gegen Datenblatt (`docs/datasheets/Prolific_PL2303GS_Datasheet_Rev1.0.4.pdf`):
VDD_IO 1.8 V … VIN + 0.3 V (S. 39 Tab. 11-2a) → 2.0 V zulässig; 6 Mbit/s bei 1.8 V (S. 40); VIL ≤ 0.4 V, VIH ≥ 0.7 × VDD_IO
= 1.4 V, VOL ≤ 0.4 V (S. 39 Tab. 11-2b); I/O 5-V-tolerant, externe VDD_IO-Speisung vorgesehen (S. 33). Board
(`docs/references/Waveshare_PL2303-USB-UART-Board-TypeA-V2_Schematic_2026-11-08.pdf`): Jumper J1 5V/VCCIO/3.3V offen
= VCCIO von aussen; +5 V an J1 abgreifbar; P2 = VCCIO/GND/TXD/RXD.

Prüfung Elektronik 2026-11-09 (`hardware/programmer/README.md` Kap. 9, SPICE `simulation/spice/programmer/prog_uart_pl2303.py`):
1. **Abs. max VDD_IO ≤ VIN + 0.3 V** (S. 39 Tab. 11-1): Einstecken unkritisch (0.000 V); Weg B nur mit Reihenfolge
   „USB zuerst ein, zuletzt aus“; Weg A beim Ziehen der USB ohne Gegenmassnahme bis 1.06 V (Ladung der VIO-Kondensatoren)
   → Entladewiderstand R2 470 Ω an VIO im Adapter (D-031/PA-6): ≤ 0.015 V.
2. VIL ≤ 0.4 V, RXD-LED 1 kΩ: mit Puffer U4 0.06–0.09 V (+311 mV); Weg B an R9 Pad 1 +113 mV bei 2.0 V, **höchstens 2.1 V**.
   VOL/VOH ohne Stromangabe → Eingangsprüfung des Boards (TXD high ≥ 1.90 V, TXD low ≤ 0.10 V, RXD → GND ≤ 0.69 mA,
   VCCIO offen ≤ 0.10 V).
3. J1 des Adapters: 1 = Board-J1 Stift „5V“ (VCC5V), 2 = P2.2 GND, 3 = P2.1 VCCIO, 4 = P2.4 RXD, 5 = P2.3 TXD; Jumper J1 ab.
   Port `/dev/ttyUSB0` (Treiber `pl2303`, VID/PID 067B:23A3, S. 22).

**Empfehlung:** Variante B (ein Händler weniger, 8.90 CHF) unter den Bedingungen B1–B6 (README Kap. 9.5); A nur noch,
falls ohnehin eine Auslandsbestellung bei waveshare.com nötig ist.

"""

TEXT_VERG = """## 5 Verguss (D-030) und Programmieradapter (D-031)

**Verguss:** Electrolube ER2223 Resin Pack 250 g, **2 Beutel** (je Bauserie einer, Haltbarkeit nach dem Abfüllen 3 Monate,
MA-3) bei Simpex, CHF 41.29 inkl. MWST, **Lieferzeit 8 Wochen** → sofort nach Freigabe bestellen; vorher SDB Teil B in
Landessprache anfordern (D-030 Bed. 1). Zubehör nach `docs/concepts/vergussmasse_versiegelung.md` Kap. 7.1 (V-Z1…V-Z11):
mit Schweizer Shopbeleg bei bastelgarage.ch (ohnehin in der Liste) Feinwaage, Mischbecher, Rührstäbe, Pinsel. Nach Red Team W-3
liegen Handschuhe (MAPA Solo 977, 0.13 mm, EN ISO 374-1, TDS und Beständigkeitstabelle lokal), Korbbrille + Visier,
Augenspülflasche/Schürze und Halbmaske A bei **galaxus.ch** (ohnehin für die Zellen in der Liste; Listings per Suchmaschine,
Seiten gesperrt → Preise teils **ANNAHME**). Ohne gefundene Quelle bleiben Prüfgewichte, kindergesicherte Flaschen,
Sekundärbehälter, 2 PE-Einwegtrichter, Spritzen/Kanülen und Thermometer bis 80 °C (Laborhändler, **ANNAHME** Kap. 7.1).

**Pflicht vor dem Öffnen des ersten Beutels (D-030 Bed. 1, Sicherheit K-7):** V-Z7 Handschuhe mit Beständigkeitsliste,
V-Z8 Korbbrille nach **EN 166 mit Kennzeichnung 3** (Flüssigkeiten) **und** Visier – eine vorhandene Brille zählt nur mit
dieser Kennzeichnung –, V-Z9 Augenspülflasche und Schürze, V-Z10 Halbmaske mit Filter A (EN 14387) bzw. Absaugung
(SDB B Abschn. 7.1/8.2). Der Silikontrichter mit Feinfilter ist gestrichen (Sicherheit W-4), stattdessen 2 PE-Einwegtrichter
(A/B getrennt, V-Z5d). **Entfällt, falls vorhanden:** Feinwaage (V-Z1), Wärmeschrank (V-Z12), TX6-Schraubenzieher (W3).
Waage ohne Justiergewicht → Prüfgewichte V-Z2 nötig.

**Programmieradapter:** Teile nach `hardware/programmer/README.md` Kap. 2.1/6 (inkl. R2 470 Ω C17710, D-031/PA-6) bei LCSC,
Preise der JLC/LCSC-Teilesuche umgerechnet mit dem Kurs aus `scripts/cost_model.py`; LCSC-Mindestmengen und Versand
**ANNAHME** (README: 10–25 CHF) – mit der JLC-Bestellung im selben Warenkorb prüfen. USB-UART = W1 (PL2303, pi-shop.ch).

"""

TEXT_SD = """## 4 microSD Industrial (G3)

`GATEWAY_SETUP.md` Kap. 1: Industrial/pSLC, ≥ 8 GB. Bisher Kingston SDCIT2/16GB, Datenblatt jetzt lokal
(`docs/datasheets/Kingston_SDCIT2_Datasheet_MKD-02122026.pdf` S. 1: TLC im pSLC-Modus, bis 3840 TBW / 30K P/E,
−40…85 °C; Kapazitäten 8–128 GB).

| Quelle (Abruf 2026-11-09) | Artikel | Preis | Lager |
|---|---|---|---|
| pi-shop.ch Art. 10951 | SDCIT2/16GB | CHF 27.90 | nicht an Lager (Benachrichtigung möglich) |
| alltron.ch (Grosshandel, Brack-Gruppe, **ANNAHME** nur Geschäftskunden) | SDCIT2/16GB | – | 0, **100 Stk bestellt auf 23.11.2026**; 8 GB: 12 an Lager |
| mediamarkt.ch Marktplatz (Ultimus.ch) | SDCIT2/8GB | CHF 56.95, versandfrei | an Lager, Lieferung 27.11.–01.12. |
| mediamarkt.ch Marktplatz (Ultimus.ch) | SDCIT2/16GB | CHF 63.95, versandfrei | an Lager, Lieferung 19.–23.11. |

Nicht abrufbar (Bot-Sperre): digitec/galaxus, brack.ch, distrelec.ch (führt SDCIT2/8GBSP, Art. 302-48-289 laut Suchmaschine),
mouser.ch. Andere Industrial-Serien (SanDisk Industrial, Swissbit) ohne CH-Angebot mit abrufbarem Preis.

**Empfehlung:** bei pi-shop.ch auf Lagereingang warten (Grosshandel meldet Lieferung 23.11.) und G2 + W1 + G3 in **einer**
Sendung bestellen. Nur wenn der Termin drängt: SDCIT2/8GB über mediamarkt.ch (gleiche Serie, +29 CHF).

"""


def main():
    rows = load()
    err, warn = check(rows)
    if "--check" in sys.argv:
        for e in err:
            print("FEHLER", e)
        for w_ in warn:
            print("Hinweis", w_)
        print(f"{len(rows)} Zeilen, {len(err)} Fehler, {len(warn)} Hinweise")
        sys.exit(1 if err else 0)
    if err:
        for e in err:
            print("FEHLER", e)
        sys.exit(1)
    hs = haendler(rows)
    md = io.StringIO()
    w = md.write
    w("# fluidi – Einkaufsliste (alles ausser JLC)\n\n")
    w("| | |\n|---|---|\n")
    w("| Stand | 2026-11-09, erzeugt von `.venv/bin/python scripts/einkaufsliste.py` aus `docs/manuals/EINKAUFSLISTE.csv` "
      "(nicht von Hand ändern) |\n")
    w("| Umfang | Sensor (Prototyp 5 + Serie 15), Gateway (D-028 ohne RTC, D-029 SHT40-Breakout), Werkstatt (USB-UART, Testzellen) |\n")
    w(f"| Belege | `{EX}`, `docs/references/pi-shop_Gateway-Teile_Auszug_2026-11-08.txt`, Register `docs/datasheets/INDEX.csv` |\n")
    w("| Nicht abrufbar | digitec/galaxus, mouser.ch, distrelec.ch, digikey.ch, conrad.ch, brack.ch, toppreise.ch (Bot-Sperre/403) "
      "→ Preise von dort sind **ANNAHME** |\n")
    w("| Hinweis | Keine Bestellung ausgelöst. Preise inkl. MWST, Lager = Anzeige am Abruftag |\n\n")
    w("## 1 Fazit\n\n")
    tot = sum(h["ware"] for h in hs)
    tot_v = sum(h["vers"] for h in hs)
    ann = sum(r["_sum"] for r in rows if r["_annahme"] and r["Status"] not in NICHT_SUMMIEREN)
    w(f"- Warenwert geplant **{tot:.2f} CHF** + Versand **{tot_v:.2f} CHF** = **{tot + tot_v:.2f} CHF** "
      f"(davon {ann:.2f} CHF Preis-ANNAHME; ohne JLC, ohne Werkstattbestand; Summen je Bereich Kap. 8).\n")
    w(f"- **Händler mit Bestellung: {sum(1 for h in hs if h['ware'] > 0)}** "
      f"({', '.join(h['h'] for h in hs if h['ware'] > 0)}). Kern sind **zwei** CH-Händler: bastelgarage.ch und pi-shop.ch; "
      "dazu Simpex (Verguss, 8 Wochen Lieferzeit) und LCSC (mit JLC bündeln).\n")
    w("- Ein Händler weniger möglich: Zellen bei bastelgarage.ch (Varta statt Panasonic, Entscheid Auftraggeber, S1).\n")
    w("- Bestellreihenfolge (Red Team W-3d): **zuerst Verguss** (V-M1, 8 Wochen; Distrelec/RS von Hand vergleichen), dann JLC "
      "(mit BT1-Vorrat 25 Stk, ORDER Kap. 4 Nr. 8a) und LCSC, dann der Rest.\n")
    w("- Offen: Quelle O-Ringe AS568-019 Silikon, ISO 7380 M2.5×8, Silikonplatte, Federstifte (Normteile-/Dichtungshändler) "
      "und Prüfgewichte, Flaschen, Sekundärbehälter, PE-Trichter, Spritzen, Thermometer (Laborhändler); Filament grau und "
      "microSD nicht an Lager. Werkstatt Weg B (WB-1…WB-24) in Kap. 8a, entfällt, falls vorhanden; Dummy-Platinen über JLC "
      "(ORDER Kap. 4 Nr. 8b).\n\n")
    w(TEXT_SHT)
    w(TEXT_UART)
    w(TEXT_SD)
    w(TEXT_VERG)
    w("## 6 Liste\n\n")
    w("| ID | Teil | Soll | Bedarf | Händler | Art.-Nr. | Angebot | Pack. × Inhalt | CHF/Pack. | Summe CHF | Lager | Abruf | Status |\n")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")
    for r in rows:
        link = f"[{r['Haendler']}]({r['Link']})" if r["Link"].startswith("http") else r["Haendler"]
        summe = "–" if r["Status"] in NICHT_SUMMIEREN else f"{r['_sum']:.2f}" + (" (A)" if r["_annahme"] else "")
        w(f"| {r['ID']} | {r['Teil']} | {r['Spezifikation_Soll']} | {r['_bedarf']:g} | {link} | {r['Artikelnr']} | "
          f"{r['Angebot']} | {r['_n']:g} × {r['_pack']:g} | {r['_preis']:.2f} | {summe} | {r['Lager']} | {r['Abruf']} | "
          f"{r['Status']} |\n")
    w("\n(A) = Preis ANNAHME bzw. Quelle offen. Bedarf-Herleitung, Register-Ref und Bemerkungen: Spalten in der CSV.\n\n")
    w("Bemerkungen:\n\n")
    for r in rows:
        if r["Bemerkung"].strip():
            w(f"- **{r['ID']}** ({r['Bedarf_Herleitung']}): {r['Bemerkung']}\n")
    w("\n## 7 Händlergruppierung und Versand\n\n")
    w("| Händler | Positionen | Ware CHF | Versand CHF | Total CHF | davon jetzt lieferbar | Versandregel |\n|---|---|---|---|---|---|---|\n")
    for h in hs:
        w(f"| {h['h']} | {', '.join(r['ID'] for r in h['rows'])} | {h['ware']:.2f} | {h['vers']:.2f} | "
          f"{h['ware'] + h['vers']:.2f} | {h['ware_jetzt']:.2f} (+{h['vers_jetzt']:.2f} Versand) | {h['q']} |\n")
    w(f"| **Summe** | | **{tot:.2f}** | **{tot_v:.2f}** | **{tot + tot_v:.2f}** | | |\n\n")
    bg = next((h for h in hs if h["h"] == "bastelgarage.ch"), None)
    if bg:
        w(f"- bastelgarage.ch: geplant {bg['ware']:.2f} CHF → {'versandkostenfrei' if bg['vers'] == 0 else 'Versand 6.90'}; "
          f"jetzt lieferbar {bg['ware_jetzt']:.2f} CHF (ohne ausverkauftes Grau) → "
          f"{'frei' if bg['vers_jetzt'] == 0 else 'unter 80 CHF, Versand 6.90'}.\n")
    w("- pi-shop.ch: G2 + W1 + G3 in **einer** Sendung, sobald G3 an Lager ist; getrennt bestellt kostet die zweite Sendung "
      "nochmals 7.90 CHF.\n")
    w("- Normteile/Dichtungen (S2, S5, G8b, P8): **ein** Fachhändler für alles; noch keiner mit abrufbarem Angebot "
      "(Versand ANNAHME 10 CHF).\n")
    w("- G9 (Gateway-LED, D-027): WP710A10GD C6001420 + 470 Ω C119317 bei LCSC zusammen mit den Adapterteilen (kein "
      "Digi-Key-Versand).\n")
    w("- JLC (PCBA Sensor) und Verguss (S8) sind separat (ORDER_JLC_REV_C.md bzw. Material-Agent).\n\n")
    w("## 8 Summen je Bereich (Ware, ohne Versand)\n\n| Bereich | Positionen | Ware CHF | davon ANNAHME CHF |\n|---|---|---|---|\n")
    for b in BEREICHE:
        rb = [r for r in rows if r["Bereich"] == b and r["Status"] not in NICHT_SUMMIEREN]
        if rb:
            w(f"| {b} | {len(rb)} | {sum(r['_sum'] for r in rb):.2f} | {sum(r['_sum'] for r in rb if r['_annahme']):.2f} |\n")
    w("\nVerguss-Zubehör (V-Z…) ohne Beutel: "
      f"**{sum(r['_sum'] for r in rows if r['ID'].startswith('V-Z') and r['Status'] not in NICHT_SUMMIEREN):.2f} CHF** "
      "(geht als Einmalkosten in `scripts/cost_final_phase5.py`); Programmieradapter (P…, W1, LCSC-Versand ANNAHME) siehe "
      "Kap. 7.\n\n")
    wb = [r for r in rows if r["Bereich"] == "Werkstatt Weg B"]
    if wb:
        w("## 8a Werkstatt-Voraussetzungen Weg B (entfällt, falls vorhanden)\n\n")
        w("Vorgabe `hardware/dummy_cell/README.md` Kap. 7 (WB-1…WB-24), je Weg-B-Platz. **Nicht in der Bestellsumme**: in der "
          "Regel Werkstattbestand. Fehlt etwas, gilt der Neukauf-Richtwert (**ANNAHME**, kein Angebot geprüft).\n\n")
        w("| ID | Werkzeug/Material | Mindestanforderung | Richtwert CHF |\n|---|---|---|---|\n")
        for r in wb:
            w(f"| {r['ID']} | {r['Teil']} | {r['Spezifikation_Soll']} | {r['_preis']:.2f} |\n")
        w(f"| | **Summe, falls nichts vorhanden (ANNAHME)** | | **{sum(r['_preis'] for r in wb):.2f}** |\n\n")
    w("## 9 Prüfhinweise (`scripts/einkaufsliste.py --check`)\n\n")
    for x in warn:
        w(f"- {x}\n")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(md.getvalue())
    for h in hs:
        print(f"{h['h']:45s} Ware {h['ware']:7.2f}  Versand {h['vers']:5.2f}  jetzt {h['ware_jetzt']:7.2f}")
    print(f"Total Ware {tot:.2f} + Versand {tot_v:.2f} = {tot + tot_v:.2f} CHF (ANNAHME-Anteil {ann:.2f}); "
          f"{len(warn)} Hinweise -> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
