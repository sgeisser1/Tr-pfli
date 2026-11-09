# Phase 6 – Red Team: Fertigungspaket production/rev-C

| | |
|---|---|
| Prüfer | Red Team (frischer Kontext, ohne Begründungskette der Ersteller) |
| Datum | 2026-11-09 |
| Prüfstand | Commit `f047cf5` (Arbeitsbaum sauber beim Start). Während der Prüfung haben andere Agenten Mechanik-Dateien, `MONTAGE_SENSOR.md`, `EINKAUFSLISTE.md` und `INDEX.csv` geändert und `1dab168` committet; danach meldet `make_release_rev_c.py --check` 49 Abweichungen. Die Befunde beziehen sich auf `f047cf5`. |
| Leitfrage | Würde ich das mit eigenem Geld bestellen und danach bauen können? |

## 0 Ergebnis in Kürze

- **JLC-Teil: ja, bestellbar.** Gerber/BOM/CPL sind konsistent, die Hashes stimmen, der Lagerbestand ist live geprüft, und die Stichproben zu Pins und Footprints sind korrekt.
- **Bauen aus dem Paket: nein, so nicht.** Die Firmware lässt sich aus `8_quellcode/` nicht bauen, wie die Anleitung es beschreibt. Die Testfirmware und `make release` lassen sich daraus überhaupt nicht bauen. Binärdateien fehlen (K-1).
- **Programmieren der Muster:** Nur der Behelf Weg B ist möglich (Labornetzteil, Lackdraht auf ein 0402-Pad). Den Normalweg A gibt es mechanisch noch nicht. Nach dem Verguss ist ein Muster mit defekter Firmware verloren (W-1).
- **Geld:** Die Systemsumme von 884.85 CHF ist eine Kostensicht. Bar ausgegeben werden **≈ 1030 CHF**, mit „Pre-reflow“ ≈ 1075 CHF (W-2). Die Stückkosten nach D-005 rechne ich nach: 8.31 CHF, plausibel.
- **Einkauf:** Die Liste nennt 8 Händler, 2 davon ohne Namen. 44 % des Warenwerts sind ANNAHME. Kritischer Pfad sind die Vergussmasse (8 Wochen Lieferzeit), das graue Filament (ausverkauft) und die microSD (nicht an Lager) (W-3).
- **Einen kritischen Befund gibt es: K-1** (Firmware-Lieferung). Er betrifft nicht die Sicherheit, ist aber eine Abnahmeanforderung von Phase 6. Er lässt sich mit wenig Aufwand beheben.

## 1 Was ich selbst geprüft habe

| Prüfung | Ergebnis |
|---|---|
| `cd production/rev-C && sha256sum -c SHA256SUMS` | 108 Dateien OK (Stand f047cf5) |
| `.venv/bin/python production/make_release_rev_c.py --check` | „Paket aktuell“ (Stand f047cf5); nach den parallelen Änderungen anderer Agenten 49 Abweichungen → vor der Freigabe neu erzeugen |
| `.venv/bin/python scripts/check_register.py` | 1 Lücke (G2 Netzteil ohne lokales Datenblatt, bekannt F-8); 50 JLC-Designatoren ok. **Hinweis:** Das Skript überschreibt `docs/reviews/phase6_register_abgleich.txt` (Zeitstempel); ich habe die Datei auf den Git-Stand zurückgesetzt |
| `hardware/sensor/gen/order_check.py --live` | 50 BOM = 50 CPL, 8 Via-in-Pad gefüllt, Gerber-ZIP = Ordner, Hashes = ORDER Kap. 1. Lager live 2026-11-09 01:13: alle Teile lieferbar, **BT1 C5213768: 594** (11-07: 654, 11-08: 629) |
| `scripts/cost_final_phase5.py` | erzeugt `phase5_kosten_final.md` inhaltsgleich (keine Änderung). Serie 8.31 / Prototyp 9.15 CHF, System B + Adapter 884.85 CHF |
| `scripts/einkaufsliste.py --check` | 44 Zeilen, 0 Fehler, 19 Hinweise |
| Firmware-Build aus dem **Release-Archiv** (Scratchpad, Toolchain `~/fluidi-tools`) | `make` **bricht ab** (DEV-Schlüssel fehlt); `make SIGN_KEY=<eigener Schlüssel>` baut; `make TESTFW=1` **unmöglich**; `make check` und `make release` **brechen ab** (fehlt `docs/interfaces/PINMAP_SENSOR.md`) → K-1 |
| Gateway-Tests aus dem Release-Archiv | `python -m unittest discover -s firmware/gateway/tests -p 'test_*.py'`: 109 Tests OK (1 übersprungen) |
| Stichproben Pins/Footprints (pcbnew gegen lokales Datenblatt) | U3 TMP1075NDRLR C3663690 (SBOS854F S. 4: SCL1 GND2 ALERT3 A0 4 V+5 SDA6, A0 = GND) ok; U4–U6 SN74LVC1G80 C473331 (SCES221T S. 3: D1 CLK2 GND3 Q̄4 VCC5) ok; U2 SN74LVC1G14 C35740 (SCES218AA Tab. 4-1: NC1 A2 GND3 Y4 VCC5) ok; Q1 AO3401A C15127 (G1 S2 D3; Drain an VBAT, Body-Diode in Durchlassrichtung) ok; D1 TUOZHAN 1615 C7496855 (Pin 1 Anode an VDD, 2/3/4 R/G/B) ok gemäss INDEX-Zitat S. 4 |
| Code ↔ Anleitungen | `fl_ui.c` (Muster L1–L17, Tastenzeiten 1.5/3/8/10/30 s, 5-s-Fenster), `statusled.py` (100/4900 ms, 100/100 ms), `api.py`/`plant.js` (Identify 15 s), `model.py` (6 Messungen/Tag) stimmen mit INBETRIEBNAHME/PAIRING/FEHLERSUCHE überein; Ausnahmen siehe K-l3 und W-6 |

## 2 Befunde

### Kritisch

**K-1 Firmware im Paket nicht lieferbar: keine Binärdateien, und der Quellcode im Paket baut nicht wie beschrieben**

- *Beleg:* `5_firmware/FIRMWARE_HINWEIS.md` sagt: „Für den Musterbau wird aus `8_quellcode/` gebaut.“ Das Archiv schliesst `*.pem` aus. Laut `Makefile` Z. 29 ist der Standard aber `SIGN_KEY ?= keys/DEV_ONLY_…pem`. Mein Lauf im Scratchpad:
  - `make` → `No rule to make target …/keys/DEV_ONLY_fluidi_signing_ec-p256.pem`
  - `make TESTFW=1 SIGN_KEY=<eigener>` → `TESTFW: nur mit DEV-Schluessel (keys/DEV_ONLY_*.pem)` (Makefile Z. 60–61). Damit lässt sich die Testfirmware für den Prototyp-Testplan (`5_firmware/TESTFIRMWARE.md`) aus dem Paket gar nicht bauen.
  - `make check` und `make release` → `FileNotFoundError …/docs/interfaces/PINMAP_SENSOR.md` (`tools/check_config.py` Z. 125). Weil `release` intern `clean all check` aufruft, ist auch der Serienstand aus dem Paket **nicht** baubar.
- *Begründung:* Die Phase-6-Anforderung verlangt Binärdateien. Der Ersatzweg aus dem Paket funktioniert nicht. Wer nur das Paket hat, kann keinen Sensor programmieren. Das Sicherheitsargument trägt nicht: Der DEV-Schlüssel ist ohnehin öffentlich im Repository. Ein mit „MUSTER/DEV – nicht ausliefern“ gekennzeichnetes Werks-Hex senkt die Sicherheit nicht, solange `flash_sensor.py --lock` den DEV-Schlüssel verweigert, was es tut.
- *Vorschlag:*
  - (a) Den Release-Generator zur Erzeugungszeit `make` aus dem archivierten Commit bauen lassen. Werks-Hex und `.bin` als `5_firmware/MUSTER_DEV/…` mit Hash und Commit beilegen. Dabei klar sagen: nur für Muster; das unsignierte Bild ist laut `firmware/sensor/README.md` bitgleich reproduzierbar.
  - (b) Alternativ im Archiv `make` ohne `SIGN_KEY` sauber abbrechen lassen, mit Hinweis auf `imgtool keygen`. Ausserdem die Bedingung für `TESTFW` von „Dateiname `DEV_ONLY*`“ auf „nicht der Produktionsschlüssel“ umstellen.
  - (c) `docs/interfaces/PINMAP_SENSOR.md` (und alles, was `check_config.py` liest) mit ins Archiv nehmen. Nach dem Erzeugen im Generator einen Probe-Build aus dem Archiv laufen lassen, damit dieser Fehler nicht wiederkehrt.

### Wichtig

**W-1 Programmieren der Muster: Weg A existiert noch nicht, Weg B ist kein Laienweg. Nach dem Verguss gibt es keinen Rückweg**

- *Beleg:* `hardware/programmer/README.md` Kap. 4: „Federstiftkopf – Konzept Mechanik (Phase 5, noch keine druckbare Konstruktion)“. `3_druck/` enthält keine Teile des Adapters. `MONTAGE_SENSOR.md` Kap. 6: Solange Weg A nicht freigegeben ist, wird vor dem Verguss nach Weg B programmiert. Weg B verlangt laut `PROGRAMMIEREN_SENSOR.md` Kap. 2:
  - ein Labornetzteil 2.0 V mit 10-mA-Begrenzung
  - Lackdraht 0.1–0.2 mm, auf R9 Pad 2 gelötet
  - eine Lötstation, eine Lupe
  - eine **selbstgebaute** Dummy-Scheibe 3.0–3.2 mm (FR4 schleifen, Kupfer teilweise entfernen)

  Nichts davon steht in der Einkaufsliste oder als Fertigungsdatei im Paket. Dafür kauft die Einkaufsliste Adapterteile P1–P8 (7.46 CHF), die ohne Federstiftkopf nicht einsetzbar sind. SWD gibt es nicht (PINMAP FW-10, E3). Nach dem Verguss bleibt nur Weg A oder OTA.
- *Begründung:* Die Muster-Firmware ist ausdrücklich „nicht freigegeben“, und die Hardware ist ungetestet. Ein Firmware-Fehler, der BLE oder OTA lahmlegt, macht einen vergossenen Sensor unbrauchbar. Der Behelf ist für eine Person ohne Feinlöt-Erfahrung riskant (0402-Pad, Spannungsgrenze 2.1 V beim PL2303).
- *Vorschlag:*
  - (a) Die Dummy-Scheibe als kleine runde Leiterplatte in die JLC-Bestellung aufnehmen (gleiche Sendung). Dicke und Kupferbild nach README Kap. 4; die verfügbare Plattendicke bei JLC am Bestelltag prüfen (**ANNAHME**).
  - (b) Den Federstiftkopf vor dem Musterverguss konstruieren und drucken. Oder ausdrücklich festlegen, dass **kein** Muster vergossen wird, bevor die Funktionsprüfung mit OTA-Hin-und-Zurück bestanden ist.
  - (c) Einen Abschnitt „Werkstatt-Voraussetzungen“ in die Einkaufsliste aufnehmen: Labornetzteil, Lötstation, Lackdraht, Messschieber, Multimeter, Lupe, 3D-Drucker mit AMS, TX6.

**W-2 Bargeldbedarf wird unterschätzt: Systemsumme 884.85 CHF, tatsächlich ≈ 1030 CHF**

- *Beleg, nachgerechnet:*
  - JLC Prototyp: 133.67 + 12.37 MWST + 22.00 Verzollung = 168.04 CHF
  - JLC Serie: 180.43 + 16.15 + 22.00 = 218.58 CHF
  - JLC zusammen: **386.62 CHF**
  - Einkaufsliste (ohne JLC, inkl. Versand): **642.47 CHF**
  - **Summe ≈ 1029 CHF**
  - Falls JLC „Pre-reflow Soldering“ berechnet: +10.41 + 33.32 → ≈ 1073 CHF
  - Gegenüber `phase5_kosten_final.md` Kap. 4: „B + Programmieradapter 884.85 CHF“.

  Die Differenz von ≈ 145 CHF kommt aus:
  - Versand Einkaufsliste 72.80 CHF
  - 28 Testzellen
  - ganze Filamentspulen und Packungen (100 Gewindeeinsätze, 10er-Schraubensets)
  - Labor- und Normteile-Versand (ANNAHME)

  Die Verguss-Beutel stehen in beiden Rechnungen. Für die Bargeldsumme habe ich sie nur einmal gezählt.
- *Begründung:* Der Auftraggeber fragt „was kostet mich das“. Die Systemsumme ist eine Kostenzuordnung, keine Kassenplanung.
- *Vorschlag:* In `phase5_kosten_final.md` Kap. 4 (bzw. README rev-C) eine Zeile „Kassenbedarf gesamt (alle Rechnungen)“ ergänzen, mit und ohne Pre-reflow, und den ANNAHME-Anteil ausweisen.

**W-3 Einkauf: 8 Händler, 2 davon ohne Namen; 44 % ANNAHME; drei Positionen auf dem kritischen Pfad**

- *Beleg (EINKAUFSLISTE.md Kap. 1/7/9):*
  - ANNAHME 251.34 von 569.67 CHF Ware
  - „offen (Labor-/Arbeitsschutz-Fachhandel)“ 189 CHF und „offen (Normteile-/Dichtungs-Fachhandel)“ 42.50 CHF: Händler und Preise erfunden bzw. geschätzt
  - S9 Filament grau ausverkauft (Bambu EU ebenfalls), G3 microSD nicht an Lager
  - V-M1 Verguss mit 8 Wochen Lieferzeit → Vorversuche V-1…V-3 und der Musterverguss sind frühestens Anfang Januar 2027 möglich
  - G9 Gateway-LED: Digi-Key soll mit LCSC gebündelt werden, aber eine LCSC-Teilenummer ist nicht gewählt → faktisch nicht bestellbar
- *Begründung:* Das Ziel „wenige Händler“ ist verfehlt. Bei den zwei offenen Händlern trägt der Auftraggeber das Such- und Preisrisiko selbst.
- *Vorschlag:*
  - (a) **galaxus.ch** (ohnehin für S1 in der Liste) als einen Händler für den ganzen Labor- und Schutzblock und die Normteile prüfen: Schutzbrille EN 166, Halbmaske mit A-Filter, Augenspülflasche, Prüfgewichte, Spritzen und Kanülen, Silikonfett, TX6-Schraubenzieher, eventuell O-Ring-Sortiment. Die Seite ist für Bots gesperrt, für Menschen aber nutzbar. Das sind 2 Händler weniger.
  - (b) ER2223RP250G wird auch bei **distrelec.ch (Art. 30116965)** und **RS (1526879)** geführt. Lager und Lieferzeit dort von Hand prüfen; das kann die 8 Wochen von Simpex verkürzen.
  - (c) G9: eine 3-mm-LED grün und 470 Ω bei bastelgarage.ch (ohnehin in der Liste) statt Digi-Key/LCSC, nach Datenblattprüfung durch die Elektronik.
  - (d) Bestellreihenfolge ausdrücklich festhalten: zuerst Verguss (Lieferzeit), dann JLC, dann der Rest.

**W-4 BT1-Halter: Bestand sinkt ≈ 30 Stück pro Tag. Die Serie kommt erst nach dem Mustertest**

- *Beleg:* Live 654 → 629 → 594 (2026-11-07/08/09). Bei gleichem Abfluss ist der Halter in ≈ 3 Wochen weg. Die Serie folgt erst nach dem Mustertest (Wochen bis Monate). `ORDER_JLC_REV_C.md` Kap. 7 sagt nur „prüfen, ob sich der Halter … vorbestellen lässt“.
- *Begründung:* BT1 ist mechanisch festgelegt (Zellfach, Hülse, Programmieradapter). Ein Ersatzteil bedeutet Layout- und Mechanikänderung.
- *Vorschlag:* Mit der Prototyp-Bestellung **≥ 25 Stück C5213768** in den privaten JLC-Teilebestand kaufen (≈ 10 USD) und das als Pflichtpunkt in die Checkliste Kap. 4 aufnehmen, nicht als „prüfen“.

**W-5 Firmennetz: Wenn mDNS gesperrt ist oder Clients voneinander isoliert sind, gibt es keine App – und keinen Ausweichweg**

- *Beleg:*
  - `pki.py` Z. 45: Die CA hat die Namensbeschränkung `permitted DNS = fluidi.local`. Ein Aufruf über die IP-Adresse führt also immer zu einer Zertifikatswarnung, und `FEHLERSUCHE.md` 4.3 verbietet ausdrücklich, diese wegzuklicken.
  - Die Anleitungen (INBETRIEBNAHME, FEHLERSUCHE 4.2, GATEWAY_SETUP) erwähnen weder Client-Isolation noch mDNS-Filter noch WPA2-Enterprise (802.1X).
  - D-028 stützt sich gerade auf das „Geschäfts-WLAN“.
- *Begründung:* In Firmen-WLANs sind Client-Isolation und gefiltertes mDNS häufig (**ANNAHME** aus Erfahrung, nicht belegt). Dann sind Gateway und Sensoren funktionsfähig, aber unbedienbar.
- *Vorschlag:* Vor der Bestellung eine IT-Abklärung (Checkliste in GATEWAY_SETUP Kap. 1):
  - PSK oder 802.1X?
  - Darf ein Client einen anderen Client erreichen?
  - Wird mDNS weitergeleitet?
  - Ist NTP erreichbar?

  Ausweichweg festlegen: z. B. eigener DNS-Name im Firmennetz mit passender Namensbeschränkung, oder ein separates SSID/VLAN.

**W-6 Kalibrierung lässt sich nicht fortsetzen: Geht die Seite verloren, ist der Trockenpunkt weg**

- *Beleg:* `app/js/calibrate.js` kennt keinen offenen Lauf wieder an. Beim Neuladen beginnt die Seite mit `run = null`. Der Lauf wird nur beim Navigieren gelöscht (Z. 85). `PAIRING_KALIBRIERUNG.md` 3.2 verlangt, die Seite „während der ganzen Kalibrierung offen“ zu lassen, und Schritt 3.3/4 sieht ausdrücklich „10 Minuten warten“ nach dem Giessen vor.
- *Begründung:* Auf dem Handy geht der Bildschirm in diesen 10 Minuten aus. iOS/Android können die Seite oder PWA verwerfen (**ANNAHME**, PROTOTYP-PRÜFUNG). Dann ist der Trockenpunkt verloren. Die Erde ist inzwischen nass, und der neue Versuch braucht **Tage** Abtrocknung.
- *Vorschlag:* Einen offenen Lauf je Sensor im Gateway halten und beim Öffnen der Seite fortsetzen, oder den Trockenpunkt einzeln speichern. Bis dahin in der Anleitung: „Bildschirm während der Wartezeit eingeschaltet lassen“ bzw. „App nicht schliessen“.

**W-7 Gateway-Gehäuse und Status-LED passen nicht zusammen**

- *Beleg:*
  - `BOM_GATEWAY.csv` G9 und `GATEWAY_SETUP.md` 5.2 sehen eine **3-mm-LED bedrahtet** mit 470 Ω vor, „LED in den Lichtschacht des Deckels (Mechanik)“.
  - Das CAD (`mechanical/gen/fluidi_gateway_pi.py` Z. 33, 104, 216–227; `check_gateway_pi.txt` Pkt. 2) modelliert dagegen weiterhin eine **LED-Platine 8 × 8.2 × 1.0 mm** (RGB 1615), die auf die Facette geklebt wird. Diese Platine wurde laut G9 nie entworfen (F-6).
  - G9: „CAD-Lichtschacht für 3-mm-LED = Mechanik“ ist offen.
- *Begründung:* Die Gateway-Druckteile im Paket haben keine Aufnahme für das Bauteil, das tatsächlich gekauft wird. Die Status-LED ist aber das Hauptdiagnosemittel in INBETRIEBNAHME Kap. 2 und FEHLERSUCHE Kap. 2.
- *Vorschlag:* Den Lichtschacht für eine 3-mm-LED mit Halterung (Klemmrippe oder Klebesitz) im Deckel ergänzen, die Prüfung neu laufen lassen und die Druckteile neu exportieren. Bis dahin im Paket kennzeichnen: „Gateway-Deckel: LED-Halter offen“.

**W-8 Widerspruch D-030 ↔ MONTAGE_SENSOR: „Freigabe offen, kein Verguss an Mustern“**

- *Beleg:*
  - `DECISIONS.md` D-030 (2026-11-09): „Status: gültig mit Auflagen“.
  - `6_anleitungen/MONTAGE_SENSOR.md` (f047cf5) Kopfzeile und O-1: „Vorschlag, Freigabe offen … Bis zur Freigabe **kein Verguss an Mustern**“. O-1 zitiert noch die K-4-Formulierung „mineralisch gefüllt“.
  - D-030 erlaubt M-A erst nach MA-1/2/4 und V-3/V-6, sonst M-B. Die Montageanleitung führt dagegen M-A als Normalweg.
- *Begründung:* Wer nach Paket baut, hält entweder an oder handelt gegen die Auflagen.
- *Vorschlag:*
  - MONTAGE Kopf und O-1 an D-030 angleichen: freigegeben mit Auflagen 1–5; M-B bis MA-6 erfüllt ist.
  - Eine Abhakliste „vor dem ersten Beutel“ einfügen.

  Die parallele Überarbeitung von MONTAGE_SENSOR.md während meiner Prüfung habe ich gesehen. Bitte dabei mitziehen.

### Klein

**K-l1 Verguss-Zubehör: 243.50 CHF für ≈ 4 g Masse im Produkt**

- *Beleg:* Konzept Kap. 2: 0.19 g pro Sensor tatsächlich nötig. Zubehör 243.50 CHF + 2 Beutel 82.58 CHF + Versand 15 CHF ≈ **341 CHF**, also ≈ 17 CHF pro Sensor bei 20 Stück. Das ist mehr als die Stückkosten.
- *Meine Gegenrechnung M-B (ganzer Beutel je Sitzung):*
  - Gespart werden Waage, Prüfgewichte, Flaschen, abschliessbare Box und Silikontrichter: ≈ 95 CHF.
  - Dafür braucht es 6 statt 2 Beutel: +165 CHF.
  - **M-A bleibt also billiger.** Die Einordnung (Verbrauch 2 g pro Sensor als Stückkosten, Beutelrest pro Bestellung und Zubehör pro Projekt als Einmalkosten nach D-005) halte ich für richtig.
- *Vorschlag:*
  - (a) Den zweiten Beutel erst bestellen, wenn der Serientermin feststeht. Ungeöffnet ist er laut TDS 12 Monate haltbar; das ist billiger, solange Distrelec oder RS als schnellere Quelle bestätigt sind.
  - (b) Die Sicherheit fragen, ob Halbmaske (V-Z10, 40 CHF) und Schürze bei 8-g-Ansätzen in einem gelüfteten Raum Pflicht oder nur „bereit“ sind. Die Anleitung sagt „bereit“.
  - (c) Bei Electrolube/Simpex nach einem Muster oder einer kleineren Packung fragen. Ich habe nur 250 g und 5 kg gefunden.

**K-l2 Silikonfett auf Silikon-O-Ringen**

- *Beleg:* S2 „Silikon oder EPDM“, S6 „silikonbasiert“, BATTERIEWECHSEL Schritt 8 und MONTAGE 7.2 „mit Silikonfett einreiben“. Silikonfett kann Silikon-O-Ringe quellen lassen. Parker (Super O-Lube) erlaubt bei Silikon nur einen **dünnen Film**; Berichte aus der Praxis sind widersprüchlich.
- *Vorschlag:* O-Ring-Werkstoff festlegen. Bei EPDM ist Silikonfett ideal; bei Silikon (VMQ) entweder ein Fett ohne Silikon (z. B. PTFE-basiert, Verträglichkeit prüfen) oder „nur hauchdünn“ ausdrücklich in die Anleitung schreiben und die Quellung in der PROTOTYP-PRÜFUNG (7 Tage 65 °C) mitmessen.

**K-l3 Pairing-Anleitung verschweigt die 10-s-Falle**

- *Beleg:* `fl_ui.c` `fl_btn_edge`: ab 10 s Halten wird `VLONG_ARMED` ausgelöst, und ein kurzer Druck innert 5 s setzt den Sensor auf Werkseinstellung (`FL_BTN_EV_FACTORY_RESET`). `PAIRING_KALIBRIERUNG.md` 2.1 sagt nur: „Lassen Sie erst nach 8 Sekunden los, passiert nichts … nochmals versuchen“.
- *Begründung:* Wer zu lange hält und sofort neu ansetzt, löscht Schlüssel und nicht abgeholte Werte. Bei einem Neu-Koppeln eines bereits gekoppelten Sensors ist das Datenverlust. FEHLERSUCHE 1.3 beschreibt es richtig, PAIRING nicht.
- *Vorschlag:* In PAIRING 2.1 ergänzen: „Blinkt die LED schnell rot (ab 10 s), loslassen und 5 Sekunden **nicht** drücken.“

**K-l4 Torx-TX6-Schraubenzieher fehlt in der Einkaufsliste; „handelsüblich“ ist grenzwertig**

- *Beleg:* D-032, BATTERIEWECHSEL „Was Sie brauchen“, REQ-MECH-15.
- *Vorschlag:* Einen TX6-Schraubenzieher je Standort in die Einkaufsliste aufnehmen (bastelgarage oder galaxus) und in INBETRIEBNAHME Kap. 1 als „liegt dem System bei“ nennen.

**K-l5 Sensor-Aufkleber mit Kennung wird nirgends hergestellt**

- *Beleg:* INBETRIEBNAHME 5.3 und PAIRING 2.1 Schritt 3 verlangen den Vergleich mit dem „Aufkleber“. MONTAGE trägt die Kennung nur in die Musterliste ein. Weder Material noch Arbeitsschritt sind vorgesehen.
- *Vorschlag:* In MONTAGE nach Kap. 7 einen Schritt „Kennung (`flash_sensor.py info` bzw. BLE-Name) auf Etikett, Etikett an die Kappenunterseite“ ergänzen, mit Etikettenmaterial in der Einkaufsliste.

**K-l6 Kostenmodell nicht mit der Einkaufsliste nachgeführt**

- *Beleg:* `cost_rev_b.py` `LOKAL` rechnet noch mit Pauschalen: Zelle 1.38 CHF (Liste 0.83), Schraube/Mutter 0.20 (Liste 0.39 + 0.29), Dichtungen 0.30. Membran, Fett und Kleber fehlen. Nachgerechnet mit Verbrauchsmengen und Listenpreisen ergibt sich ≈ 3.15 CHF statt 3.01 CHF, also +0.15 CHF Stückkosten. Das Ergebnis < 10 CHF bleibt. Der Vorbehalt „Pre-reflow“ (10.53 CHF) bleibt das eigentliche Risiko.
- *Vorschlag:* `LOKAL` aus `EINKAUFSLISTE.csv` speisen, wie es `cost_final_phase5.py` schon für V-Z tut.

**K-l7 Druckunterlagen: 3MF nur mit Geometrie, PRINT_SETTINGS-Kopf veraltet**

- *Beleg:*
  - Die 3MF-Dateien enthalten nur `3dmodel.model`: kein Profil, keine Ausrichtung.
  - `PRINT_SETTINGS.md` Titel: „Gateway G1 v3“, Kap. 3 verweist noch auf `mechanical/gateway/print/` (ESP32, durch D-014 ersetzt).
- *Vorschlag:* Bambu-Studio-Projektdateien (`.3mf` mit Plate und Profil) je Platte ergänzen; Kopf und Verweise auf G1 v4 korrigieren.

**K-l8 `check_register.py` schreibt bei jedem Lauf eine versionierte Datei**

- *Beleg:* `docs/reviews/phase6_register_abgleich.txt` ist nach jedem Lauf geändert (nur der Zeitstempel).
- *Vorschlag:* Ausgabe nur mit `--write` schreiben oder den Zeitstempel weglassen, damit Prüfer den Arbeitsbaum nicht verschmutzen.

## 3 Die drei tragenden Annahmen – selbst geprüft

1. **„Das Paket genügt zum Bauen.“** Widerlegt für die Firmware (K-1) und für das Programmieren (W-1). Für die JLC-Bestellung bestätigt.
2. **„< 10 CHF Stückkosten (D-005).“** Bestätigt mit 8.31 CHF (+≈ 0.15 CHF nach K-l6), **unter Vorbehalt Pre-reflow**: dann 10.53 CHF, als Stopp-Kriterium im Warenkorb richtig behandelt. Die Vollkosten von 20.17 CHF pro Sensor und der Bargeldbedarf von ≈ 1030 CHF (W-2) gehören vor die Freigabe noch einmal ausdrücklich vor den Auftraggeber (D-005 „zur Kenntnis“).
3. **„Die Einkaufsliste ist kauffertig.“** Nur teilweise: bastelgarage.ch und pi-shop.ch sind belegt und kauffertig. Der Rest ist ANNAHME, ausverkauft oder hat 8 Wochen Lieferzeit (W-3, W-4).

## 4 Entscheide D-028 … D-032

| Entscheid | Urteil |
|---|---|
| D-028 ohne RTC | Tragfähig, der Rückfall ist im Code und in den Anleitungen konsistent (FEHLERSUCHE 4.4, `timesvc`, Tests ok). Die Annahme „Geschäfts-WLAN“ ist aber nicht auf mDNS, Client-Isolation und 802.1X geprüft → W-5 |
| D-029 SEN0428 | Plausibel; der verlinkte Schaltplan ist SHTC3 und ist richtig als Befund markiert. Die Platinendicke ist ANNAHME und mit PROTOTYP-PRÜFUNG versehen. Keine Einwände |
| D-030 ER2223 | Technisch nachvollziehbar, aber Status und Anleitung widersprechen sich (W-8). Kosten und Aufwand sind hoch (K-l1). Kritischer Pfad: 8 Wochen Lieferzeit (W-3 b) |
| D-031 PL2303 | Datenblattgrenzen zitiert (VDD_IO ≤ VIN + 0.3 V), Bedingungen B1–B6 sinnvoll. Kein Einwand zum Teil selbst. Der Programmierplatz als Ganzes ist aber ohne Federstiftkopf unvollständig (W-1) |
| D-032 Kaufteile Mechanik | TX6 ist vertretbar, das Werkzeug fehlt aber in der Liste (K-l4). eSun ASA+ ist richtig als bedingt eingestuft. Grau ist ausverkauft, also ist die Hülse ohne Werkstattbestand nicht druckbar (W-3) |

## 5 Fehlerszenarien aus dem echten Gebrauch (Auswahl, nur Paketbezug)

- **Batteriewechsel durch Büropersonal:** Die Taste beim Einsetzen zu berühren, startet bei Mustern den ROM-Bootloader, und die Zelle ist in Tagen leer (FEHLERSUCHE 3.1). Das ist dokumentiert, in der Serie durch `--lock` behoben, und ein TX6 wird gebraucht (K-l4). Akzeptabel.
- **Gateway-Neustart oder Stromausfall:** Die Werte bleiben im Sensor (≥ 105 Tage). Eine laufende Kalibrierung bricht ab (dokumentiert, W-6 verschärft das).
- **WLAN-Wechsel oder neues Firmennetz:** Nur „technisch“ (GATEWAY_SETUP). Ohne mDNS keine App (W-5).
- **Zwei Gateways:** Das Pairing zeigt „war schon gekoppelt“. Ein Wechsel braucht Werkseinstellung (FEHLERSUCHE 3.6), und die 10-s-Falle gefährdet die Daten (K-l3).
- **Sonne auf der Fensterbank:** Zellwarnung in BATTERIEWECHSEL. Materialnachweis eSun ASA+ 7 Tage 65 °C ist PROTOTYP-PRÜFUNG (D-032). Ok.

## 6 Empfehlung an den Orchestrator

Den **JLC-Teil freigeben** (nach Abhaken der Checkliste Kap. 4 und mit BT1-Vorrat, W-4). **Das Gesamtpaket erst freigeben**, wenn diese Punkte erledigt sind:

- K-1 (Firmware baubar beilegen)
- W-1 (Dummy-Scheibe und Werkstatt-Voraussetzungen; Verguss erst nach bestandenem OTA-Test)
- W-8 (MONTAGE an D-030 angleichen)
- Paket nach den parallelen Änderungen neu erzeugt

W-2 bis W-7 vor der Bestellung dem Auftraggeber vorlegen. Die Bestellung kann trotzdem starten: Verguss sofort, wegen der Lieferzeit.

## Quellen (Websuche, 2026-11-09)

- Parker O-Ring Handbook ORD 5700: https://mfc.arizona.edu/sites/default/files/2022-02/parker_o-ring_handbook.pdf
- Super-Lube O-Ring Silicone Grease: https://www.super-lube.com/o-ring-silicone-grease
- Diskussion Silikonfett auf Silikon-O-Ringen: https://budgetlightforum.com/t/what-silicone-grease-or-other-lubricant/64622
- Distrelec CH ER2223RP250G: https://www.distrelec.ch/en/black-epoxy-resin-packet-liquid-250g-black-clear-to-light-brown-electrolube-er2223rp250g/p/30116965 (Bot-Sperre, nur Auflistung gesehen)
- RS ER2223 250 g: https://uk.rs-online.com/web/p/resins/1526879
- Electrolube ER2223 Technical Bulletin: https://macdermidalpha.com/sites/default/files/2023-08/ER2223-Encapsulation-Resins-EN-09Aug23-TB.pdf

## Antwort Ersteller (Software, 2026-11-09; nicht committet)

| Befund | Antwort | Umsetzung / Beleg |
|---|---|---|
| **W-5** | **umgesetzt** (Anleitung; kein neuer Software-Ausweichweg) | Der Auftraggeber hat mDNS im Firmen-WLAN bestätigt. Trotzdem neue Vorabprüfung **GATEWAY_SETUP Kap. 1.1** (Tabelle: PSK oder 802.1X, Client-Isolation, mDNS, NTP – je mit Prüfung ohne Gateway per Laptop `python -m http.server` und mit Gateway per `http://<IP>/ca` bzw. `http://fluidi.local/ca`), Verweis in INBETRIEBNAHME Kap. 1 und FEHLERSUCHE 4.2. Ausweichwege ehrlich beschrieben: **mDNS gefiltert** → Weg nach CONCEPTS 5.2: genau ein IT-DNS-Name + DHCP-Reservierung, `hostname` in `gateway.toml`, `pki-init --force` (CA mit Name Constraint auf diesen Namen), neue CA auf allen Geräten; im Code vorhanden (`cfg.hostname` in `pki.init`, Weiterleitung, CA-Seite), **am Gerät nicht erprobt (PROTOTYP-PRÜFUNG)**. IP-Adresse ist kein Ausweichweg (Name Constraint, Warnung nie wegklicken). **Client-Isolation → kein Ausweichweg in der Software**, nur IT (Ausnahme, eigenes WLAN/VLAN, eigener AP). **802.1X** nicht vorbereitet (Installationsskript nur PSK) |
| **W-6** | **umgesetzt** | Gateway: offene Kalibrierläufe in SQLite (`meta.cal_runs`, nur offene, ein Schreibvorgang je Schritt) bis `expires` (6 h), über Gateway-Neustart erhalten (laufende Messung → `await_*` mit Hinweis), Ablauf im Takt → `cancelled`; neu `GET /sensors/{id}/calibration-runs` (S). PWA `calibrate.js`: setzt den offenen Lauf beim Öffnen fort (Substrat aus dem Lauf, Trockenpunkt sichtbar), zeigt „Lauf bleibt bis HH:MM gespeichert“ und „Abbrechen“, bei laufender Messung Stand alle 3 s bzw. per SSE `calibration`; beim Verlassen der Seite wird der Lauf **nicht** mehr gelöscht. Mock gleich, OpenAPI, GATEWAY_API 5.2, PAIRING 3.2/3.3 (Handy darf ausgehen). Tests: `test_api.test_calibration_run_resumable` (Neustart über dieselbe DB, Ablauf), `test_mock_api.test_calibration_run_resume`; Darstellung mit Edge headless gegen den Mock geprüft |
| **K-l3** | **umgesetzt** | PAIRING 2.1: ab 10 s Halten „vorbereitet“ (schnell rot, danach 5 s schwach rot), **nur ein kurzer Druck < 1.5 s innert 5 s** löscht Schlüssel, Einstellungen und nicht abgeholte Werte; Anweisung „loslassen und mindestens 5 s nicht drücken“; erneutes Halten 3–8 s hebt die Vorbereitung auf, über 30 s gilt die Taste als klemmend. Abgeglichen mit `fl_ui.c` `fl_btn_edge`/`fl_btn_tick` und `fl_ui.h` (`FL_BTN_SHORT_MAX_MS` 1500, `FL_BTN_LONG` 3000–8000, `FL_BTN_VLONG_MIN_MS` 10000, `FL_BTN_CONFIRM_MS` 5000, `FL_BTN_STUCK_MS` 30000) und FEHLERSUCHE 1.3/3.6 |

## Antwort Ersteller (Fertigung, 2026-11-09, Einkauf/Kosten/Release; nicht committet)

| Befund | Antwort | Umsetzung |
|---|---|---|
| **K-1** | **umgesetzt** (Generator; Paket erzeugt der Orchestrator nach den Commits) | `production/make_release_rev_c.py`: Quellarchiv enthält zusätzlich `docs/interfaces/PINMAP_SENSOR.md`, `hardware/sensor/out/fluidi_sensor.net`, `scripts/test_flash_sensor.py`, `testfw_eval.py`, `test_testfw_eval.py` und gezielt **nur** `firmware/sensor/keys/DEV_ONLY_fluidi_signing_ec-p256.pem`. Alle anderen Schlüsseldateien (`*.pem/.key/.der/.p12/.pfx`) sind per `git ls-tree` einzeln ausgeschlossen, und die Prüfung auf „PRIVATE KEY“ lässt nur diese Datei zu. Der Generator entpackt das Archiv, baut mit `make` und lässt `make check` laufen (SDK über `~/fluidi-tools/env.sh`), dann kopiert er das Werks-Hex und `.bin` nach `5_firmware/MUSTER_DEV/` („nur Muster, DEV-Schlüssel, nicht freigegeben“, sha256 in FIRMWARE_HINWEIS und SHA256SUMS). Neu `--probe`, ohne Paket. **Probe am Stand f49f343 bestanden:** `make` 0, `make check` 0 (13 + 23 + 3 Tests ok, 1 skip), Werks-Hex `…key86e66310969bdc7d.hex`. Die Signatur (ECDSA) ist nicht reproduzierbar, deshalb gilt der sha256 der beigelegten Datei. **Neuer Befund an die Firmware:** `make release SIGN_KEY=<eigener Schlüssel>` aus dem Archiv bricht in `test_flash_sensor.TestRealBuild.test_factory_with_dev_key_cannot_be_locked` ab (erwartet den DEV-Fingerabdruck im gebauten Hex). Der Test muss bei Nicht-DEV-Schlüssel überspringen. Vorschlag (b) (TESTFW-Bedingung) betrifft die Firmware und ist mit dem beigelegten DEV-Schlüssel nicht mehr nötig. |
| **W-1 (a)/(c)** | **umgesetzt** (Fertigungsteil) | (c) EINKAUFSLISTE Block „Werkstatt Weg B“ WB-1…WB-24 nach `hardware/dummy_cell/README.md` Kap. 7, „entfällt, falls vorhanden“, nicht in der Bestellsumme, Neukauf-Richtwert 324 CHF (ANNAHME) in Kap. 8a. (a) Dummy-Platinen PLUS 1.0 / MINUS 2.0 mm (je 5 Stk, unbestückt) als Pflicht in derselben Prototyp-Bestellung: ORDER Kap. 4 Nr. 8b, BESTELLEN Schritt 9a (Ablauf „Add new item“ belegt; gemeinsame Sendung **ANNAHME** mit Stopp-Regel), Kosten 4.31–14.44 CHF über `cost_dummy.py` (Obergrenze im Kassenbedarf und als Einmalkosten des Prototyp-Loses). ZIPs und README im Release-Generator (`1_jlc_upload/dummy/`, `7_programmieradapter/dummy_cell/`), Hashprüfung gegen `hardware/dummy_cell/out/SHA256SUMS`. (b) Mechanik/Elektronik. |
| **W-2** | **umgesetzt** | `phase5_kosten_final.md` Kap. 4a „Kassenbedarf gesamt“, erzeugt von `cost_final_phase5.py`: JLC Prototyp 168.03 + Serie 218.58 + BT1-Vorrat 8.12 + Einkaufsliste 587.81 + Versand 81.70 = **1064.25 CHF**, mit Pre-reflow **1107.38 CHF**. ANNAHME-Anteil 292.64 CHF ist ausgewiesen. |
| **W-3** | **teilweise umgesetzt** | (a) galaxus.ch übernimmt Handschuhe, Brille + Visier, Augenspülflasche + Schürze, Halbmaske A, Silikonfett und TX6 (Listings per Suchmaschine; Seiten für automatischen Abruf gesperrt, Preise teils ANNAHME). Für Prüfgewichte 1/5 g, kindergesicherte Flaschen, Box, PE-Trichter, 1-ml-Spritzen und ein Thermometer bis 80 °C gab es bei galaxus keine Treffer → weiter Laborhändler offen. (b) distrelec 30116965 und RS 1526879 sind nicht abrufbar (Captcha bzw. 403); Vermerk in V-M1, von Hand prüfen. (c) G9 über **LCSC**: WP710A10GD C6001420 (gleiches Teil, Datenblatt lokal) und 470 Ω C119317, zusammen mit den Adapterteilen. bastelgarage und pi-shop führen keine einzelne 3-mm-LED mit Datenblatt. (d) Bestellreihenfolge steht in EINKAUFSLISTE Kap. 1. |
| **W-4** | **umgesetzt** | ORDER Kap. 4 **Nr. 8a (Pflicht)** und BESTELLEN **Schritt 10a**: 25 × C5213768 in „My Parts Lib“. Ablauf nach `docs/references/JLCPCB_PartsPreorder_Auszug_2026-11-09.txt` (Zahlungsfrist dort widersprüchlich: 1 h bzw. 168 h). Kosten 25 × 0.3615 USD = 9.04 USD (8.12 CHF inkl. MWST ANNAHME) im Kassenbedarf. Bestand 594 am 2026-11-09 01:28. |
| **K-l4** | **umgesetzt** (Liste) | EINKAUFSLISTE W3: Wiha T6 bei galaxus, CHF 6.50 (Suchtreffer), „entfällt, falls vorhanden“. Den Hinweis in INBETRIEBNAHME Kap. 1 setzen die Anleitungen (Software). |
| **K-l6** | **umgesetzt** | `cost_rev_b.py` LOKAL kommt aus `EINKAUFSLISTE.csv` (Preis je Stück bzw. je g × Verbrauch; Membran 1/20 Platte und Fett 1/50 Tube sind ANNAHME), mit Rückfall auf die Pauschalen. Lokale Teile 3.01 → 3.23 CHF. **Serie 8.31 → 8.69 CHF** (2 × 100 µF: 8.48), mit Pre-reflow 10.91. < 10 CHF bleibt. `COSTS_REV_B.md` und `phase5_kosten_final.md` neu erzeugt. |
| **K-l8** | **umgesetzt** | `check_register.py` schreibt `phase6_register_abgleich.txt` nur noch mit `--write`. |

## Antwort Ersteller (Mechanik, 2026-11-09; nicht committet)

| Befund | Antwort | Umsetzung / Beleg |
|---|---|---|
| **W-7** | **umgesetzt** (Aufnahme in der **Wanne**, nicht im Deckel) | `mechanical/gen/fluidi_gateway_pi.py`: LED-Platine 8 × 8.2 und RGB-Platzhalter entfernt. Neu ist ein **LED-Rohr** für die Kingbright WP710A10GD (Datenblatt V10B S. 1: Flansch Ø 3.2 × 1.0, Spitze bis Flanschrückseite 4.6 ± 0.3, Körper 2.9). Bohrung Ø 3.1, die Rohrstirn dient als Flanschanlage (Klebesitz), die Spitze liegt 0.1 mm hinter dem Fenster. Ein Kragen bindet das Rohr unterhalb der Fuge an die Facette an. Im Deckel liesse sich die LED nicht senkrecht montieren, weil sie unter der Facetten-Überhöhung liegt; das Rohr sitzt deshalb wie der frühere Lichtschacht an der Wanne. Dazu kommen 2 Kabelhalter am Boden vorne (Kanal 3.0, Lippe 0.8) und ein Litzen-Platzhalter zu **J8 Pin 11 (GPIO17)** und **Pin 14 (GND)**. Prüfung `check_gateway_pi.txt` Pkt. 15: Kollisionen keine; LED-Rohr zum Niederhalterrohr 0.61 mm; Pi beim senkrechten Einlegen 0.58 mm zum Rohr und 0.42 mm zur LED; Montage Pi/Deckel 0.00 mm³; Druckteile je 1 Körper. Exporte, Zeichnungen (FL-G-01 Note 7, FL-G-03; 182 Masse, 0 Fehler) und PRINT_SETTINGS Kap. 3/4/5 nachgeführt. **Nicht geändert (gesperrt):** GATEWAY_SETUP 5.2 sagt noch „Lichtschacht des Deckels“; richtig ist „LED-Rohr in der Wanne“. Bitte durch den zuständigen Agenten anpassen. PROTOTYP-PRÜFUNG: Sitz der LED (Bohrung unter 45° gedruckt), Leuchtbild, Litzen klemmen nicht |
| **W-8** | **umgesetzt** | MONTAGE_SENSOR Kopf und O-1/O-2: ER2223 „D-030, gültig mit Auflagen, Abweichung K-4“. Die Sperre „kein Verguss an Mustern“ ist ersetzt durch eine **Abhakliste D-030 Bed. 1–5** in Kap. 3a, gegliedert in: vor dem ersten Beutel, Mischvariante, vor dem Musterverguss, vor der Serie, FMEA. Es sind Vorbedingungen, keine offene Freigabe. **M-B gilt, bis M-A bestätigt ist** (Bed. 2/MA-6). Die Sicherheitsinhalte von Kap. 3a sind unverändert; ergänzt wurden die Handschuh-Auflagen HS-1…HS-5 (MAPA Solo 977) und die PE-Trichter (S W-4) |
| **W-1** (Reihenfolge) | **umgesetzt** | MONTAGE **Kap. 3b**. Vor Kap. 4 müssen am Muster drei Schritte bestanden sein: (1) Weg B (mit R9-Draht nur an der losen Platine), (2) Funktionsprüfung mit Zelle, (3) **ein erfolgreiches OTA-Update** auf eine höhere Version (Sensor meldet die neue Version, misst, bleibt gekoppelt). Danach Zelle heraus und Clip leer. Fällt ein Schritt durch: nicht vergiessen. Kap. 6 verweist darauf. **Zusatz DC-1:** Die Lasche der Dummy-Scheibe hat Platz (`hardware/dummy_cell/README.md` Kap. 6a) |
| **K-l2** | **umgesetzt** (Werkstoff EPDM) | Lokale Quelle `docs/references/Parker_ORD5700_ORingHandbook_2007.pdf` (Register REF-ORING1). PDF-S. 206, Silicone Greases: **EPDM 1**, **VMQ 3** (am Seitenbild geprüft). S. 68: Silikonfette mit allen Werkstoffen ausser Silikon. S. 16: EPDM bis 150 °C, nicht mit Mineralöl. Dünger-Salze und Wasser: EPDM 1 (S. 165/203/215). S. 50: Montagefett sparsam. MONTAGE Kap. 7/8, PRINT_SETTINGS Kap. 5, FL-S-00 Pos. 11 und EINKAUFSLISTE S2/S6 nachgeführt. „Ohne Russ“ bleibt bevorzugt; gibt es nur schwarzes EPDM, ist vorher ein RSSI-Vergleich mit der Elektronik nötig. Lieferant für S2 bleibt offen |
| **K-l5** | **umgesetzt** | MONTAGE **Kap. 7a**: Kennung `fluidi-XXXX` (nur aus der Werksfirmware) auf laminiertem Schriftband 9 mm, schwarz auf weiss, ≤ 26 mm. Ort: **Rückseite der blauen Kappe**, z ≈ 46…55, also ≥ 2 mm über der Fuge; nicht auf die Hülse (Tauschteil). Kein Metall. Zweite Person liest gegen. Haftung nach 7 d bei 65 °C ist PROTOTYP-PRÜFUNG. EINKAUFSLISTE **S12** als Werkstattbestand (ANNAHME vorhanden, sonst Beschaffung klären) |
| **K-l7** | **umgesetzt** (Dokumentation); Profile in die 3MF einbetten: **abgelehnt** | PRINT_SETTINGS-Kopf korrigiert auf G1 v4/`gateway_pi`; G1 v3 (`mechanical/gateway/`) als ersetzt markiert, Tabelle entfernt. Neues **Kap. 2a** „Bambu Studio einrichten“ mit Profilen, Import ohne Drehen, globalen und objektbezogenen Werten und Plattenplan S-1…S-5/G-1…G-2. Grund der Ablehnung: Das Bambu-Projektformat ist herstellerspezifisch und versionsabhängig, und Bambu Studio ist in der Umgebung nicht installiert. Eine per Skript geschriebene Projektdatei liesse sich nicht prüfen |
