# Phase 5 – Red Team: Bestellung JLC, Kosten, Gateway-BOM, Release-Paket

| | |
|---|---|
| Datum | 2026-11-08, Stand HEAD `cedccd5` (+ unversioniertes `production/rev-C/`) |
| Prüfer | Red Team (frischer Kontext, ohne Begründungskette der Ersteller) |
| Gegenstand | `docs/manuals/BESTELLEN_JLC.md`, `hardware/sensor/out/ORDER_JLC_REV_C.md`, `docs/reviews/phase5_kosten_final.md` (`scripts/cost_final_phase5.py`, `scripts/cost_model.py`, `hardware/sensor/out/COSTS_REV_B.md`), `hardware/gateway/BOM_GATEWAY.csv`, `production/make_release_rev_c.py` |
| Ergebnis | **Kein kritischer Befund.** 5 wichtige, 7 kleine Befunde. Das Release-Paket `production/rev-C` ist **veraltet** (W-1) und muss vor der Weitergabe neu erzeugt werden |

## Was selbst geprüft wurde

| Prüfung | Ergebnis |
|---|---|
| `.venv/bin/python hardware/sensor/gen/order_check.py --live` (2026-11-08 14:01) | 4 Lagen, 1.60 mm, 26.05 × 158.55 mm, ENIG, 145 Vias 0.45/0.30, 8 Via-in-Pad alle gefüllt+überkupfert, 0 ohne Attribut; Gerber-Job Rev C, Dielektrika 0.2104/1.065/0.2104 = JLC04161H-7628; ZIP = `out/gerber`; BOM = CPL (50), nur Top; sha256 = ORDER Kap. 1; BT1 C5213768: 629 an Lager |
| Gerber-ZIP selbst entpackt | `PTH.drl` nur Werkzeuge T1/T2 je 0.300 mm, 146 Bohrungen; `NPTH.drl` leer → Remark „146 holes 0.30 mm“ stimmt |
| Teilezählung live | 10 Extended, 1 Preferred (C1552), 15 Basic = 26 Zeilen → Anleitung Schritt 7 stimmt; Feeder 10 × 3.07 = 30.70 USD |
| Felder Schritt 4 gegen Platine/Job/Screenshot | alle 24 Zeilen konsistent (Dicke, Lagen, ENIG, 1/0.5 oz, Stackup No, Min via 0.3/(0.4/0.45), TG135, Remove Mark, Confirm Production File Yes) |
| EZB-Kurs 2026-11-06 (eurofxref-daily, abgerufen heute) | USD 1.1165, CHF 0.9143 → 0.81890 CHF/USD ✓ |
| Kosten nachgerechnet (von Hand) | PCB-Modell 61.51 + 0.739/Stk reproduziert 65.21/76.30 ✓; Prototyp JLC 163.22 USD ✓; MWST (133.67 + 19) × 8.1 % = 12.37 ✓; Prototyp total 135.68 + 12.37 + 19 + 3 + 5 × 3.09 = 185.50 (gerundet 185.47) ✓; Stück Serie 4.96 × 16/15 + 3.09 = 8.38 ✓; Gateway-Summe 81.47 ✓; System A 267.58 + 81.47 = 349.05 ✓, B + 185.47 = 534.52 ✓, 23.27/35.63/26.73 ✓; X-ray-Staffel 1.64 (5) / 0.82 (16) gemäss Preisseite ✓ |
| Skripte in sauberem Klon (Scratchpad) | `cost_final_phase5.py` und `cost_rev_b.py` erzeugen `phase5_kosten_final.md` und `COSTS_REV_B.md` **bytegleich** (kein Diff) ✓ |
| Release-Skript in sauberem Klon | läuft, 65 Dateien, `sha256sum -c` 0 Fehler, Upload-Hashes = ORDER ✓ – aber Unterschiede zum abgelegten Paket (W-1) |

## Befunde

### Kritisch
Keine.

### Wichtig

**W-1 Release-Paket `production/rev-C` ist veraltet (falsche Druckdateien).**
Beleg: README des Pakets „Git-Stand `d07a3b4` + nicht committete Änderungen“; HEAD ist `cedccd5` (P5-M2 Tastermechanik,
RTC-Rahmen). Vergleich Paket ↔ Repo: `kappe_blau.{3mf,step,stl}`, `stoessel.{3mf,step,stl}`,
`gateway_pi/deckel_blau.{3mf,step,stl}` und `PRINT_SETTINGS.md` weichen ab; ein Neulauf im Klon ergibt andere sha256
(z. B. `kappe_blau.3mf` 930d1d7d… statt 8f38d7b8…). `sha256sum -c SHA256SUMS` im alten Paket meldet trotzdem „OK“ –
es prüft nur die Kopie gegen sich selbst, nicht gegen die Quelle. Der Auftraggeber würde Kappe/Stössel ohne die
P5-M2-Korrektur drucken. Zudem ist `production/rev-C/` nicht versioniert. Upload-Dateien (Gerber/BOM/CPL), ORDER und
Anleitung sind dagegen aktuell.
Vorschlag: Paket nach dem letzten Commit neu erzeugen und committen; im Skript einen Modus `--check` (vergleicht ein
bestehendes Paket mit den Quellen und HEAD) und einen Abbruch bei nicht committeten Quellen ergänzen; in
BESTELLEN Schritt 1 statt nur `sha256sum -c` auch den Git-Stand im README gegen den freigegebenen Commit prüfen lassen.

**W-2 Rotationskontrolle Schritt 8: Laie soll ggf. selbst drehen; Hinweis „roter Punkt ≠ Pin 1“ fehlt.**
Beleg: BESTELLEN Schritt 8 „in der JLC-Ansicht drehen (falls möglich) … **oder** nicht weitermachen“ (kein
Entscheidungskriterium). JLC-FAQ Teil 2 Q1 (JLCPCB_NOTES Kap. 8): „we do not call the red dot pin 1, but a marking
only“. ORDER Kap. 5 lässt die Pin-1-Lage „im Bauteilbild (Punkt, …)“ suchen. Bei U1/U2/U3/U4–U6 führt eine falsche
Drehung zum Kurzschluss der Zelle bzw. der GPIOs (ORDER Kap. 5, fett).
Vorschlag: Eindeutige Regel: „Nie selbst drehen. Abweichung → Screenshot, Projektleitung, nicht bezahlen.“ Den
JLC-Hinweis zum roten Punkt wörtlich in Schritt 8 und ORDER Kap. 5 aufnehmen; Pin 1 am Gehäusemerkmal (Fase,
Pin-1-Pad-Form im JLC-Footprint) statt am roten Punkt beurteilen.

**W-3 „Pre-reflow Soldering“ ist als Bestellposten eingeordnet, wäre aber Stückkosten und kippt REQ-FAB-04.**
Beleg: Preisseite „Pre-reflow Soldering 1–1,000,000 joints: $0.016/joint“ (beide PCBA-Arten). Bei ca. 144 Lötstellen
(SMT 0.23 USD / 0.0016) = 2.30 USD/Board → 2.30 × 0.8312 + MWST 0.15 = 2.07 CHF/Board × 16/15 = **+2.20 CHF** →
Serie **≈ 10.58 CHF > 10 CHF**. `phase5_kosten_final.md` Kap. 2.1 weist nur „+33.32 CHF je Bestellung“ aus und
erklärt REQ-FAB-04 ohne Vorbehalt für erfüllt. Nach D-005 gehören Kosten pro Lötstelle in die Stückkosten.
Vorschlag: In Kap. 2/2.1 den Vorbehalt ausdrücklich nennen („falls berechnet: 10.58 CHF, REQ-FAB-04 verfehlt“),
im Warenkorb (Schritt 9) als **Stopp-Kriterium** behandeln (Posten vorhanden → Projektleitung). ANNAHME der Ersteller,
dass der Posten für reine SMD-Bestückung nicht anfällt, ist plausibel, aber unbelegt.

**W-4 Platzhalter `JLCJLCJLCJLC` widerspricht der aktuellen JLC-Anweisung.**
Beleg: `JLCPCB_HowToMarkOnPCB_Auszug_2026-11-08.txt`: „Please DO NOT add "JLCJLCJLCJLC" in your silkscreen layer“;
`order_check.py` bestätigt den Text auf B.Silkscreen (6.00/19.70). Die Lösung „Remark bittet um Löschen“ verlässt sich
auf manuelle Bearbeitung beim Ingenieur; mögliche Folgen sind Rückfrage/Verzögerung oder ein falsch interpretierter
Markierungswunsch (Auftrag läuft mit Remove Mark).
Vorschlag: Den Text vor der Bestellung im Layout löschen (reine Silkscreen-Änderung), Gerber neu erzeugen, ORDER-Hashes
und Paket nachführen, `order_check.py` erneut laufen lassen. Wird das abgelehnt: die heutige Behandlung ist vertretbar
(nur Silkscreen, im Kopf verdeckt), dann bitte als bewusste Abweichung in DECISIONS festhalten.

**W-5 Gateway-Einkaufsliste enthält Teile, die laut eigener BOM nicht passen oder nicht lieferbar sind.**
Beleg: `BOM_GATEWAY.csv` G6 Grove SHT41 „passt NICHT in die Klimakammer … kleineres Breakout wählen“ und „nicht an
Lager“; G4 PiRTC „passt NICHT“ mit Buchsenleiste (13.6 mm, Bauraum 10.2 mm, `check_gateway_pi.txt` Nr. 13), Pi ohne
Stiftleiste; G3 microSD „nicht an Lager“. Der Kaufbetrag 81.47 CHF summiert damit zwei Teile, die man so nicht
kaufen soll, und zwei nicht lieferbare Teile. Arbeitsmittel fehlen nicht wesentlich (Netzteil, SD, RTC-Zelle,
Gehäuse, Schrauben sind drin; Kartenleser/Lötkolben Werkstatt, ANNAHME).
Vorschlag: Liste als „nicht kauffertig“ kennzeichnen, bis Mechanik/Elektronik ein passendes SHT4x-Breakout und die
RTC-Montage (Leiste entfernen/Litzen) festlegen; Ersatz für SD und SHT41 mit Quelle und Lager angeben; Kaufbetrag
danach neu rechnen.

### Klein

**K-1 ORDER Kap. 6 zeigt alte Beträge.** 139.27 / 185.40 / 267.51 / 325.73 / 237.79 CHF (DHL 23.44) statt 139.34 /
185.47 / 267.58 / 325.80 / 237.86 (DHL 23.52, `COSTS_REV_B.md`, `phase5_kosten_final.md`). Vorschlag: nachführen.

**K-2 Felder, die nicht in der Tabelle stehen.** Schritt 4 nennt keine allgemeine Regel für unbekannte Felder (z. B.
„Impedance Control“, „Package Box“, „UL Marking“, Verpackungs-/Papieroptionen), Zeile 23 deckt nur Ja/Nein-Optionen.
Vorschlag: Satz „Feld nicht in der Tabelle → Vorgabe lassen, Screenshot; ändert es den Preis, Projektleitung fragen“.

**K-3 PCBA Qty 16 evtl. nicht wählbar.** Bei JLC ist die PCBA-Menge oft eine Auswahlliste; ob 16 von 20 angeboten
wird, ist nicht belegt (Spalte ist zwar „ANNAHME“, aber ohne Ausweichregel). Vorschlag: „16 nicht wählbar → nächst
grössere Menge (z. B. 20), Mehrkosten ≈ 4 × Stück-JLC-Anteil notieren“.

**K-4 Remark zum Kopieren.** Der Text steht als Markdown-Zitat (`> ` je Zeile) und nennt „Y -50 mm“ (Projektkoordinate,
für JLC ohne Bezug). Vorschlag: Remark als reine Textdatei ins Paket (`2_bestellung/REMARK.txt`), „Y -50 mm“ durch
„beyond ~50 mm from the antenna end“ ersetzen; Feldlänge im Formular prüfen (ANNAHME, nicht belegt).

**K-5 Versand mit PCBA.** Modell rechnet 23.52 USD pauschal, schätzt aber selbst 0.55 kg für die Serie; die
DHL-Stufe über 0.5 kg kann teurer sein. Wirkung wenige USD, im 10-%-Stoppkriterium enthalten. Vorschlag: im Text
erwähnen.

**K-6 Kartenaufschlag 1.5 % (ANNAHME).** PayPal-Umrechnung liegt typischerweise höher (ca. 3–4 %, ANNAHME, nicht
geprüft). Wirkung < 3 CHF je Bestellung. Vorschlag: Empfehlung „Karte ohne Fremdwährungsgebühr bzw. in USD zahlen“.

**K-7 Stückkostendefinition sichtbar machen.** REQ-FAB-04 „< 10 CHF“ ist nach D-005 (Status „zur Kenntnis“, nicht
„Entscheid Auftraggeber“) erfüllt; der tatsächliche Aufwand pro Sensor ist 17.84 CHF (Serie) bzw. 35.63 CHF (Prototyp +
Serie + Gateway). Das steht korrekt im Bericht, aber nicht in der Kurzaussage. Vorschlag: im Fazit beide Zahlen
nebeneinander nennen und D-005 vom Auftraggeber ausdrücklich bestätigen lassen.

## Geprüfte Alternativen
- **Review Before Payment statt Pay Directly:** würde die JLC-Prüfung der unbelegten Kombination Economic + POFV vor
  der Zahlung zeigen; Nachteil: Teile nicht reserviert (ANNAHME), Verzögerung. Beide Wege sind vertretbar, weil die
  Stopp-Regel 1, die Produktionsdatei (Lage `sk`) und die Erstattungszusage greifen. Keine Änderung nötig.
- **microSD:** „High Endurance“-Karte statt Industrial (deutlich billiger, ANNAHME ohne Angebot) zusammen mit
  schreibarmem Betrieb; Entscheid Gateway-Agent, ändert die Sicherheit nicht.
- **Standard-PCBA:** korrekt als Ausweg mit Freigabe beschrieben (+52/+58 CHF), nachgerechnet plausibel.

## Gesamturteil
Anleitung und Bestellunterlage sind sachlich korrekt, mit Platine, Gerber und JLC-Quellen konsistent und haben
brauchbare Stopp-Regeln (POFV, Economic, Lager, Betrag) sowie die Produktionsdatei-Kontrolle. Die Kosten sind
reproduzierbar und rechnerisch richtig. Vor der Weitergabe an den Auftraggeber: **W-1 (Paket neu erzeugen)** und
**W-2 (Rotationsregel)** erledigen; W-3 bis W-5 vor bzw. bei der Bestellung klären.

## Antwort Ersteller (Fertigung/Kosten, 2026-11-08)

| Befund | Antwort | Umsetzung |
|---|---|---|
| W-1 | **umgesetzt** (Skript); Paket nicht neu erzeugt (Vorgabe Projektleitung) | `production/make_release_rev_c.py`: Abbruch bei nicht committeten Quellen (`--allow-dirty` nur zum Testen, README markiert), neuer Modus `--check` (sha256 Paket ↔ Quelle, fehlende/überzählige Dateien, Git-Stand README = HEAD, Dirty-Vermerk). Heute: `--check` → 12 Abweichungen (Ihre Liste + Git-Stand). BESTELLEN Schritt 1: `--check` + Git-Stand gegen freigegebenen Commit; `sha256sum -c` allein genügt nicht |
| W-2 | **umgesetzt** | BESTELLEN Schritt 8 und ORDER Kap. 5: feste Regel „nie selbst drehen → Screenshot, nicht bezahlen, Projektleitung“; JLC-Zitat „we do not call the red dot pin 1, but a marking only“ (PCBA-FAQ Teil 2 Q1, JLCPCB_NOTES Kap. 8); Pin 1 am Gehäusemerkmal. Neue Stopp-Regel 5 |
| W-3 | **umgesetzt** | `cost_final_phase5.py`: Fazit (Kap. 0) und Kap. 2/2.1 mit Vorbehalt – falls berechnet Serie **10.60 CHF** (Skript; Ihre 10.58 aus 144 statt 145 Lötstellen) → REQ-FAB-04 verfehlt. Stopp-Kriterium in BESTELLEN Schritt 9 / Stopp-Regel 6 und ORDER Kap. 4 Nr. 11 |
| W-4 | **umgesetzt** (vorbereitet, Entscheid Projektleitung: Platzhalter raus) | `order_check.py` prüft jetzt das **Fehlen** des Platzhalters (Zeichnungen und Footprint-Texte) → Exit 1, solange vorhanden (meldet heute FEHLER, erwartet). ORDER Kap. 1 Warnhinweis (Hashes folgen nach neuem Gerber), Kap. 2/4/8, BESTELLEN Schritt 1/12 und Remark ohne Platzhaltersatz. Layoutänderung macht Elektronik |
| W-5 | **umgesetzt** | `BOM_GATEWAY.csv` Status je Zeile: kauffertig (G2, G8, V1), Eigenfertigung (G7), Entscheid offen (G4/G5 RTC-Montage ohne Buchsenleiste; G6 SHT41 Variante a Grove + grössere Kammer / b kleineres Breakout / c vorerst weglassen), nicht an Lager (G3). Kostenbericht: kauffertig **22.77 CHF**, offen 58.70 CHF, geplant 81.47 CHF. microSD-Ersatz: keine Industrial-Karte mit lokaler Quelle gefunden → keine Alternative eingetragen (Vermerk G3) |
| K-1 | **umgesetzt** | ORDER Kap. 6 auf DHL 23.52 (139.34/185.47/184.26/237.86/141.85/267.58/186.13/325.80) |
| K-2 | **umgesetzt** | BESTELLEN Schritt 4: Regel für Felder ausserhalb der Tabelle |
| K-3 | **umgesetzt** | BESTELLEN Schritt 6: 16 nicht wählbar → nächstgrössere Menge, Mehrkosten ≈ 4 × 5.53 USD notieren, melden |
| K-4 | **umgesetzt** | `hardware/sensor/out/REMARK_JLC_REV_C.txt` (eine Zeile, 563 Zeichen, „last approx. 109 mm … opposite the antenna“ statt Y-Koordinate), im Release-Paket aufgenommen; Feldlänge ANNAHME, bei Kürzung fragen |
| K-5 | **umgesetzt** | Kostenbericht Kap. 2.1 und BESTELLEN Schritt 10 (Gewichtsstufe > 0.5 kg, ANNAHME) |
| K-6 | **umgesetzt** | BESTELLEN Schritt 11: Karte ohne Fremdwährungsgebühr; Kostenbericht Kap. 2.1 |
| K-7 | **umgesetzt** | Kostenbericht Kap. 0: Stückkosten nach D-005 (8.38, Vorbehalt 10.60) neben Vollkosten (17.84 Serie, 35.63 System) und Bitte um ausdrückliche Bestätigung von D-005 durch den Auftraggeber |
| Zusatz R3-K5 (Sicherheit) | **umgesetzt** | BESTELLEN Schritt 13: Verpoltest ST-E2 vor dem ersten Einsetzen einer Zelle |

Geprüft nach Umsetzung: `cost_final_phase5.py` läuft (Screenshot-Assertion ok); `order_check.py` meldet den Platzhalter
(erwartet bis zur Layoutänderung); `make_release_rev_c.py --check` meldet das veraltete Paket. Nicht committet.
