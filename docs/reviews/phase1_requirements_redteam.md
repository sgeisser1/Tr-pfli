# Phase 1 – Red-Team-Prüfung Anforderungsdokument

| | |
|---|---|
| Geprüft | `docs/requirements/REQUIREMENTS.md` v0.1 (Entwurf) |
| Grundlagen | `docs/requirements/PROJEKTAUFTRAG.md`, `docs/requirements/CLIENT_INPUT.md` |
| Prüfer | Red Team, 2026-11-06 |
| Ergebnis | **1 kritischer, 13 wichtige, 7 kleine Befunde. (Zählung im Kopf vom Orchestrator korrigiert, Befundliste unverändert.)** Das Dokument ist gut gegliedert und deckt den Auftrag weitgehend ab. Zur Freigabe nötig: Prioritätsregel Kosten (F-01) und die wichtigen Befunde. |

Hinweis: Ich habe nichts an `REQUIREMENTS.md` geändert. Rechnungen sind unten nachvollziehbar.
Zahlen, die ich nicht aus einem lokalen Datenblatt belegen kann, sind als **ANNAHME** markiert.

## 1 Tragende Annahmen (selbst geprüft)

1. **Primärzelle schafft 12 Monate mit Erreichbarkeit ≤ 5 min.** Rechnung: 12 Monate = 8760 h.
   Bei 225 mAh Nennkapazität (CR2032) wären im Mittel ≤ 25.7 µA erlaubt. Mit pessimistischen
   160 mAh nutzbar sind es ≤ 18.3 µA. Laut TI SWRA349 liefern manche CR2032-Marken bei
   Pulslast nur etwa die Hälfte der Nennkapazität. Für ein BLE-SoC mit Advertising im
   Sekundenbereich liegt das im machbaren Bereich (ANNAHME, in Phase 2 zu rechnen). Die
   Annahme trägt also, **aber nur, wenn „pessimistisch“ beziffert wird** (siehe F-08).
2. **Die Sonde hält die Einstecklast aus.** Handrechnung mit Annahme Breite 15 mm, Dicke
   1.6 mm, Länge 100 mm und E(FR4) ≈ 20 GPa (ANNAHME):
   - Biegung bei 5 N an der Spitze: σ = 500 N·mm / 6.4 mm³ ≈ **78 MPa**. Das ist unkritisch
     gegenüber der typischen Biegefestigkeit von FR4 von einigen 100 MPa (ANNAHME).
   - Knicken bei 30 N axial: P_cr ≈ 25 N (K = 2, frei auskragend), 101 N (K = 1), 206 N (K = 0.7).
   - Die Werte tragen also nur, wenn die Lagerung beim Einstecken definiert ist (siehe F-10).
3. **Zeitstempel ±2 min nach 7 Tagen.** Das entspricht ≤ 198 ppm. Für 14 Tage (Pufferdauer
   REQ-LOG-01) wären es ≤ 99 ppm, für ±1 min/Monat (REQ-GW-09) ≤ 23 ppm. Ein 32-kHz-Quarz
   erfüllt das. Ein interner RC-Oszillator erfüllt es eher nicht (ANNAHME, typisch einige
   100 ppm; in Phase 2 am Datenblatt prüfen). Machbar, aber in sich inkonsistent (F-07).

Geprüfte Alternative: Statt dauernder Erreichbarkeit durch Advertising kann der Sensor alle
N Minuten **selbst** beim Gateway nachfragen (Polling). Das erfüllt REQ-SYS-05 vermutlich
billiger. Die Anforderung ist bereits lösungsneutral formuliert, also gut so. Die Folgerung
in CLIENT_INPUT #7 („alle 30–60 s erreichbar“) sollte aber nicht als Vorgabe weiterwandern.

## 2 Rückverfolgung (Vorgabe → Anforderung)

| Vorgabe (Quelle) | REQ-ID | Bewertung |
|---|---|---|
| Sensor als Stab, kleiner abgedichteter Kopf, Sonde (PA Ziel) | MECH-01/02/13, MES-01 | ok |
| Feuchte kapazitiv + Temperatur, loggen, lokal funken (PA Ziel) | MES-01, TMP-01, LOG-01, SYS-01 | ok |
| Gateway sammelt, speichert, PWA iOS/Android/PC (PA Ziel) | GW-01/02, APP-01 | ok |
| Lieferpaket: Gerber/BOM/CPL, Gehäusedateien Bambu, Firmware, PWA, Doku, Renderings | FAB-01, DOC-01/02, MECH-12 | teilweise: Druckdateien (3MF/Profile) nicht explizit, **Gateway-Firmware-Update fehlt** (F-19) |
| Gateway: fertiges Board oder eigenes PCB, begründet | GW-07 | ok |
| JLC-Mindestmengen für PCB/PCBA recherchieren und angeben | RB-09 | **fehlt als REQ** (F-18) |
| Kosten < 10 CHF, „zwingend“, Stück- vs. Einmalkosten, Basic Parts | FAB-02/04/05/06 | abgedeckt, aber Priorität falsch (F-01) |
| Grösse: Sonde ~100 mm, Kopf minimal, kein AAA/AA | MECH-01/02 | ok |
| Energie: Vergleich LiPo/Knopfzelle, Pulslast, Ri, Puffer-C, Energiebudget und Laufzeit je Variante | ENE-01/02/03/06 | teilweise: „Energiebudget je Variante“ und Pulslast/Ri nicht explizit (F-18) |
| Sicherheit LiPo (Schutz, NTC, Strombegrenzung, Verpolung, Mechanik, Feuchte, Tiefentladung) | SAF-LI-01..06 | ok |
| Sicherheit Knopfzelle (Verpolung, Halter, keine Ladung) | SAF-CC-01..03 | ok |
| Nicht wiederaufladbar empfehlen, falls sicherer/günstiger; FMEA-light | SAF-02/03 | ok |
| Funk lokal, BLE bevorzugt, Vergleich WLAN im Sensor, Reichweite, ein Gateway reicht | SYS-01/02, RF-01/02 | ok |
| Zwei-Wege-Kommunikation | SYS-06 | ok |
| PWA vom Gateway, HTTPS praktikabel | APP-02 | ok |
| LED + Taster, Blinkmuster, Tastenfunktionen, LED-Energie | UI-01..06 | ok |
| **Design**: schlicht/modern, mehrere Designvorschläge zur Freigabe, Tropfenform, Logo/Wortmarke für Gehäuse, Silkscreen, PWA | MECH-16 (nur Name/Logo) | **fehlt weitgehend** (F-12) |
| Namen `troepfli` in Technik, „Tröpfli“ sichtbar | SYS-08, APP-01 | teilweise (Hostname, Dateien nicht als REQ) – klein, in CLAUDE.md geregelt |
| 3D-Druck Bambu, alle Materialien | MECH-12, RB-07 | ok |
| Bestückung komplett JLC, Rest separat und minimal | FAB-01/03 | ok |
| TA1: Sonde Teil des PCB, kein freiliegendes Metall | MES-01, MECH-03 | ok |
| TA1: Innenlagen 4L vs. 2L + Coating vergleichen | MECH-04 | abgedeckt, aber vorweggenommen (F-15) |
| TA1: Vias, 1 mm Randabstand, Versiegelung + Anleitung, Dichtlinie, Guard, Antenne | MECH-05..09, RF-04, DOC-02 | ok |
| TA1: Dicke, **Sondenform (Spitze)**, Stecktiefenmarkierung, FEM | MECH-01/10/11 | Spitze fehlt (F-18) |
| TA1: Elektrodengeometrie per Feldsimulation (Empfindlichkeit, Messvolumen, Isolationsdicke) | MES-08 | nur Messvolumen; Simulation als Nachweis fehlt (F-18) |
| TA1: Langzeitdrift FR4 | MES-06 | abgedeckt, nicht prüfbar (F-05) |
| TA2: Bodentemperatur an Dichtlinie, opt. Luft, weitere Sensoren nur wenn Kosten/Energie ok | TMP-01..04 | ok |
| TA3: Zwei-Punkt-Kalibrierung in App, gespeichert; Temperaturkompensation | APP-07, MES-02/05/09, TMP-02 | ok |
| TA4: Puffer mit Zeitstempel, Historie dauerhaft, Zeitsync | LOG-01/02, GW-01/09, SYS-07 | ok, inkonsistent (F-07) |
| TA5: Deep Sleep, Mittelung, Pairing, OTA, ID, Datenformat | FW-01/02, MES-10, RF-05, SYS-08/09 | ok |
| TA6: Gateway-Funktionen, OTA-Verteilung, opt. MQTT/HA | GW-01..03, SYS-10 | ok |
| TA7: PWA-Funktionen inkl. CSV | APP-03..08 | ok |
| TA8: Gehäuse FDM, spritzwassergeschützt, Fach/Port dicht und zugänglich, LED/Taster, PETG/ASA | MECH-12/13/15, UI-05 | ok |
| CI #3: ein Raum 10 × 15 m | RB-01, RF-02 | ok |
| CI #4: Pi nur wenn nötig, MCU-Gateway prüfen, MQTT optional | RB-05, GW-07, SYS-10 | ok |
| CI #5 + Präzisierung: Firmen-WLAN zulässig, wenig Eingriff, **Alternativen ohne WLAN-Gateway mitbewerten** | RB-04, SAF-NET-03 | Alternativenvergleich fehlt als REQ (F-18) |
| CI #6: Töpfe 15–30 cm, Erde + Granulat | RB-02, MES-09 | ok |
| CI #7 + Präzisierung: 4–6/Tag, manuell ≤ 5 min Muss, ≤ 1 min Soll, Energie beider Werte | SYS-04/05, ENE-04 | ok, Lücke bei 1-min-Variante (F-02) |
| CI #8: Primärzelle ≤ 1 Wechsel/Jahr, Akku Laden alle paar Monate | ENE-02/03 | ok |
| CI #9: P1S mit AMS | RB-07, OP-01 | ok |
| CI #10: kein Programmieradapter, Energiemessung mit Werkstattmitteln | FW-06, ENE-07, FAB-09 | ok |

## 3 Befunde

### Kritisch

**F-01 · kritisch · REQ-FAB-04, Kap. 1.1 – Die Kostenpriorität widerspricht dem Auftrag.**
- *Begründung:* Im Auftrag steht: „tiefer Preis ist **zwingend**“. Die Projektregel lautet
  Sicherheit > Kosten > Komfort. Im Entwurf ist das Kostenziel nur **Soll** („angestrebt,
  Abweichung begründen“). Gleichzeitig sind viele Komfort- und Kostentreiber **Muss**, zum
  Beispiel:
  - MECH-04 (4 Lagen bevorzugt),
  - GW-01 (5 Jahre Historie),
  - APP-04 (Jahresdiagramm),
  - SAF-LI-04 (zusätzliche Tiefentladeabschaltung zur Zelle),
  - FW-07 (Fehlermeldung),
  - APP-01 (vier Desktop-Browser).

  So wie das Dokument formuliert ist, verliert das Kostenziel jeden Konflikt mit einer
  Komfort-Muss-Anforderung. Das ist die umgekehrte Priorität.
- *Beleg:* PROJEKTAUFTRAG.md Z. „Kosten: tiefer Preis ist zwingend“; CLAUDE.md „Prioritäten“.
- *Vorschlag:*
  - In 1.1 ergänzen: „**Zielkonflikte:** Es gilt Sicherheit > Kosten > Komfort. Verhindert
    eine Muss-Anforderung ohne Sicherheitsbezug das Kostenziel REQ-FAB-04, wird sie dem
    Auftraggeber mit Mehrkosten pro Sensor zum Entscheid vorgelegt.“
  - REQ-FAB-04 auf „**Muss** (Abweichung nur mit schriftlicher Freigabe des Auftraggebers,
    mit Kostenaufstellung und Treiberliste)“ setzen.

### Wichtig

**F-02 · wichtig · REQ-SYS-05, REQ-ENE-02/04 – Die Laufzeit ist nur für den 5-min-Wert gesichert.**
- *Begründung:* Das Standardprofil rechnet mit dem Muss-Wert von 5 min. Wird das Soll von
  1 min umgesetzt, kann REQ-ENE-02 fallen, und niemand hat es entschieden.
- *Vorschlag:* „Die Reaktionszeit ist in der PWA einstellbar (Bereich 1–5 min). Die
  Werkseinstellung ist der kürzeste Wert, bei dem REQ-ENE-02 noch erfüllt ist. Das
  Energiebudget nennt die Laufzeit für 1, 2 und 5 min.“

**F-03 · wichtig · fehlt (REQ-MES) – Der Einfluss von Dünger/Salzgehalt fehlt.**
- *Begründung:* Kapazitive Low-Cost-Sensoren reagieren bei niedriger Messfrequenz deutlich
  auf die Leitfähigkeit des Bodens. Topfpflanzen werden gedüngt, das Substrat versalzt über
  Monate. Ohne Anforderung wird die Messfrequenz bzw. das Messprinzip nicht danach
  ausgelegt.
- *Beleg:* Placidi et al., *Sensors* 2020, 20(12):3585: Die Kalibrierung muss
  Bodenstruktur, Temperatur und Salinität berücksichtigen. Adla et al., *Sensors* 2020:
  Die Sensoren reagieren auf Temperatur und Salinität.
- *Vorschlag:* Neue REQ-MES-11 (Soll): „Die Änderung des Feuchteindex durch übliche Düngung
  (Flüssigdünger in Herstellerdosis, Giesswasser statt Leitungswasser) beträgt ≤ 5 %-Punkte
  bei gleichem Wassergehalt. Prüfung im Becher mit gleichem Substrat und gleicher
  Wassermenge, einmal mit und einmal ohne Dünger. **PROTOTYP-PRÜFUNG**. In Phase 2 wird
  der Einfluss der Messfrequenz in die Konzeptwahl aufgenommen.“

**F-04 · wichtig · REQ-MES-05 – Die Prüfmethode fehlt, und mit Werkstattmitteln ist die Anforderung kaum prüfbar.**
- *Begründung:* 0.3 %/K über 25 K ergibt bis 7.5 %-Punkte. Das ist als Ziel sinnvoll. Ohne
  Klimakammer bleibt aber offen, wie man Temperatur ändert und den Wassergehalt konstant hält.
  Hinzu kommt: Die Permittivität von Wasser sinkt selbst um rund 0.4–0.5 %/K (ANNAHME,
  Literaturwert ε ≈ 80 bei 20 °C). Unklar ist, ob physikalische oder elektronische Drift
  kompensiert werden soll.
- *Vorschlag:* „Prüfung: Substrat im dicht verschlossenen Beutel (Masse vor/nach ± 1 %),
  Messung bei ca. 8 °C (Kühlschrank), 22 °C und 35 °C (Ofen/Heizmatte), je 2 h
  Ausgleich. Kompensiert wird die **Sensor-/Elektronikdrift**; zusätzlich wird ein
  Referenzmedium (Luft, Wasser) gemessen.“

**F-05 · wichtig · REQ-MES-06, REQ-MECH-14 – Die Drift-Prüfung ist nicht durchführbar.**
- *Begründung:* „Konstanter Wassergehalt über 6 Monate“ lässt sich im Substrat nicht
  einhalten. Für eine „Hochrechnung aus beschleunigtem Test“ fehlt ein Modell. FR4 nimmt
  Wasser über Wochen bis zur Sättigung auf.
- *Vorschlag:* „Drift = Änderung der Rohwerte in **Referenzmedien** (Luft und
  Leitungswasser, 22 °C) vor und nach 30 Tagen Eintauchen bis zur Dichtlinie, ≤ 3 % der
  Kalibrierspanne. Zwischenmessungen an Tag 1, 3, 7, 14 und 30 zeigen, ob die Drift sättigt.
  Dauertest 6 Monate mit 2 Mustern läuft parallel zur Serie weiter.“

**F-06 · wichtig · REQ-SYS-01 ↔ REQ-SAF-NET-02 ↔ REQ-GW-09 – Widerspruch bei der Zeitquelle; Gateway ohne Zeit nach Neustart.**
- *Begründung:*
  - SYS-01 erlaubt einen Zeitserver ausserhalb des LAN als Kann. SAF-NET-02 verbietet jede
    Verbindung ins Internet.
  - GW-09 nennt „Uhrzeit aus dem Browser“. Nach einem Stromausfall in der Nacht hat das
    Gateway keine Zeit, bis jemand die PWA öffnet. Die Zeitstempel aller Sensoren werden dann
    falsch synchronisiert.
  - ±1 min/Monat (≈ 23 ppm) erfordert eine dauerhaft laufende Uhr mit Quarz.
- *Vorschlag:*
  - SAF-NET-02 ergänzen: „ausser optionalem, abschaltbarem NTP (SYS-01)“.
  - GW-09 ergänzen: „Nach einem Neustart ohne gültige Zeit synchronisiert das Gateway die
    Sensoren **nicht**. Es übernimmt deren Zeit oder markiert Werte als ‚Zeit unsicher‘ und
    korrigiert sie nach, sobald eine Zeitquelle verfügbar ist. Die Gangreserve über einen
    Stromausfall von ≥ 24 h ist nachgewiesen.“

**F-07 · wichtig · REQ-SYS-07 ↔ REQ-LOG-01 / LOG-03 – Zeitgenauigkeit und Pufferdauer passen nicht zusammen.**
- *Begründung:* Gepuffert werden 14 Tage, die Zeitgenauigkeit ist aber nur für 7 Tage
  festgelegt. Nach einem Batteriewechsel ohne Gateway ist die Uhr verloren, und neue Werte
  haben keine gültige Zeit.
- *Vorschlag:* SYS-07: „≤ ±2 min nach 7 Tagen, ≤ ±5 min nach der vollen Pufferdauer.
  Nach Energieverlust ohne Zeitsync speichert der Sensor relative Zeit seit Neustart; das
  Gateway rechnet sie beim Nachliefern um.“ LOG-01 auf **30 Tage** erhöhen (Ferien,
  Büroschliessung; 180 Datensätze, Speicherkosten vernachlässigbar).

**F-08 · wichtig · REQ-ENE-02, ENE-04, ENE-05 – „Pessimistisch“ ist nicht beziffert, und die Restlaufzeit ist kaum schätzbar.**
- *Begründung:*
  - Laut TI SWRA349 liefern manche CR2032 bei Pulslast nur etwa 50 % der Nennkapazität.
    Ohne Zahl kann jeder Ersteller „pessimistisch“ anders auslegen.
  - Das Profil rechnet mit 20 °C, RB-03 erlaubt bis 45 °C. Das ist ein Widerspruch zur
    Forderung nach pessimistischen Annahmen.
  - Die Knopfzellenspannung ist flach, deshalb ist „Restlaufzeit < 30 Tage“ allein aus der
    Spannung unzuverlässig.
- *Vorschlag:*
  - ENE-02: „gerechnet mit ≤ 60 % der Datenblatt-Nennkapazität (oder gemessenem Wert bei
    Pulslast), Selbstentladung gemäss Datenblatt, Ruhestrom +50 % Streuung, Temperatur
    gemäss RB-03“.
  - ENE-05: „Warnung ≥ 30 Tage vor Ausfall; Schätzung aus Ereigniszählung (verbrauchte
    Ladung) plus Spannung unter Last; Nachweis mit beschleunigtem Entladetest an 2 Zellen“.

**F-09 · wichtig · REQ-GW-01 – 5 Jahre Historie engt die Gateway-Wahl ohne Not ein.**
- *Begründung:* Rechnung: 15 Sensoren × 6/Tag × 365 × 5 = 164 250 Datensätze ≈ 2.6 MB roh
  bei 16 B pro Datensatz. Mit Datenbank-Overhead sind es ein Mehrfaches davon. Bei SYS-03
  (30 Sensoren, 24/Tag) sind es ≈ 21 MB roh. Ein MCU-Gateway mit 4 MB Flash (CI #4) fällt
  damit heraus. Nötig wären SD-Karte oder Pi, beides heikel bei Stromausfall (GW-05) und
  gegen RB-05.
- *Vorschlag:* „Historie ≥ **2 Jahre** in voller Auflösung bei 15 Sensoren × 6/Tag, ältere
  Daten dürfen auf Tageswerte verdichtet werden. Vollständige Historie über Backup
  (GW-06).“ Die Speicherrechnung wird in der Gateway-Variantenwahl ausgewiesen.

**F-10 · wichtig · REQ-MECH-10 – Lastfall unklar und zu mild; Lastfälle aus dem echten Gebrauch fehlen.**
- *Begründung:*
  - Die Knicklast hängt stark von der Lagerung ab (25 N frei auskragend bis 206 N, siehe
    oben). 30 N können also bestanden oder klar nicht bestanden sein.
  - Granulat (2–8 mm Körner) erzeugt punktuelle Seitenkräfte.
  - Real kommen hinzu: Herausziehen am Kopf (Zug + Hebel auf die Dichtlinie), Hebeln beim
    Umtopfen, Fall von der Fensterbank.
- *Vorschlag:* „Lastfälle: (1) axial 50 N, Kopf in der Hand eingespannt, Spitze in der Erde
  gelenkig; (2) Seitenlast 10 N an der Spitze; (3) Herausziehen 30 N am Kopf, ohne
  Undichtigkeit der Dichtlinie danach; (4) **Fall aus 1 m auf harten Boden**, 3×, Sonde und
  Kopf funktionsfähig und dicht. Anleitung: in festem Substrat und Granulat mit Stab
  vorstechen.“

**F-11 · wichtig · fehlt (GW/SAF-NET) – Szenarien für den Netzbetrieb fehlen.**
- *Begründung:* Das Firmen-WLAN ist laut CI #5 ein Hauptrisiko. Diese Fälle sind nicht
  geregelt:
  - WLAN-Passwort- oder Netzwechsel,
  - neue IP über DHCP: PWA-Lesezeichen und Zertifikat hängen am Namen bzw. an der IP; mDNS
    ist in Firmennetzen oft blockiert (ANNAHME),
  - Ersatz eines defekten Gateways: Müssen dann alle Kopplungsschlüssel neu gepaart werden?
  - zweites Gateway im Raum.
- *Vorschlag:* Neue Muss-Anforderungen:
  - „Netzwechsel ohne Neuflashen (z. B. Rückfall-Zugangspunkt oder Taster am Gateway).“
  - „Gateway unter fester, dokumentierter Adresse erreichbar, auch nach DHCP-Wechsel.“
  - „Backup (GW-06) enthält Kopplungsdaten; ein Ersatzgateway übernimmt alle Sensoren ohne
    erneutes Pairing.“
  - „Ein Sensor kommuniziert nur mit seinem Gateway; ein zweites Gateway stört nicht.“

**F-12 · wichtig · fehlt – Design- und Logo-Anforderungen fehlen.**
- *Begründung:* Im Auftrag gefordert: schlicht/modern, **mehrere Designvorschläge
  (Renderings) zur Freigabe**, Tropfenform als Inspiration, Logo/Wortmarke für Gehäuse,
  Silkscreen und PWA. Im Entwurf steht nur REQ-MECH-16.
- *Vorschlag:* Neue REQ-DES-01 bis 03:
  - „≥ 3 Designvorschläge als fotorealistische Renderings, Auswahl und Freigabe durch den
    Auftraggeber.“
  - „Wortmarke/Logo ‚Tröpfli‘ in Varianten für Gehäuse (ein- bzw. mehrfarbig mit AMS),
    Silkscreen und PWA-Icon.“
  - „Formsprache schlicht, Tropfenmotiv optional.“

**F-13 · wichtig · RB-03, REQ-SAF-LI-02/05 – Temperaturannahme für die Fensterbank vermutlich zu tief.**
- *Begründung:* Ein dunkler ASA-Kopf in direkter Sonne hinter Glas kann deutlich über
  45 °C erreichen (ANNAHME, nicht gemessen). Für eine LiPo ist das sicherheitsrelevant
  (Lagerung und Laden). Auch die Bodentemperatur an der Dichtlinie wird dann durch den
  aufgeheizten Kopf verfälscht (TMP-01).
- *Vorschlag:* RB-03: „Kopf in direkter Sonne bis **65 °C** (ANNAHME), in Phase 2 mit einem
  Thermometer an einem gedruckten Muster auf der Fensterbank messen.“ Die Energiequelle
  muss diese Temperatur sicher aushalten. Die Kopffarbe wird hell empfohlen.

**F-14 · wichtig · REQ-SAF-01, REQ-SAF-CC-04 – Die Sicherheitsanforderungen sind nicht messbar bzw. zu weich priorisiert.**
- *Begründung:*
  - „Temperaturen, die das Gehäuse entzünden“ lässt sich nicht prüfen. PETG erweicht schon
    bei etwa 70–80 °C (ANNAHME).
  - Das Verschlucken von Knopfzellen durch Kinder oder Haustiere ist eine bekannte schwere
    Gefahr. Die Absicherung ist billig, aber nur als Soll eingestuft, obwohl Sicherheit
    höchste Priorität hat.
- *Vorschlag:*
  - SAF-01: „Im Einzelfehlerfall: keine Oberfläche > 60 °C, kein Bauteil über seiner
    Datenblattgrenze, kein Rauch-/Elektrolytaustritt. Nachweis: FMEA plus Kurzschlusstest am
    Ausgang der Energiequelle und Verpolungstest.“
  - SAF-CC-04 auf **Muss**.

### Klein

**F-15 · klein · REQ-MECH-04 – Die Lösung ist vorweggenommen.** Die Anforderung ist Muss,
enthält aber „bevorzugt 4 Lagen“ und ist so nicht prüfbar. Der Auftrag verlangt den
*Vergleich*.
→ „Lagenaufbau nach dokumentiertem Vergleich 4L (Innenlagen) vs. 2L + Coating
(Empfindlichkeit, Kosten bei 5/15 Stück, Lebensdauer) gewählt.“

**F-16 · klein · REQ-RF-02 – Die Messgrösse ist unklar.** Was bedeutet „99 % inkl.
Wiederholungen“, über welche Dauer? Mit Puffer muss die Endzustellung 100 % sein.
→ „Über 7 Tage mit allen Sensoren: ≥ 99 % der geplanten Messungen innert 1 h in der PWA,
100 % nach Nachlieferung.“

**F-17 · klein · REQ-MES-08 – Messvolumen nicht messbar definiert.**
→ „Die Simulation zeigt: ≥ 80 % der Kapazitätsänderung stammen aus dem Bereich 10–90 mm
unter der Dichtlinie, kein 10-mm-Abschnitt trägt > 25 % bei.“

**F-18 · klein · diverse – Kleinere Lücken in der Rückverfolgung.** Ergänzen:
- JLC-Mindestmengen PCB/PCBA recherchiert und angegeben (zu FAB-05),
- Energiebudget und realistische Laufzeit **je Variante** inkl. Pulslast, Innenwiderstand
  und Pufferkondensator (zu ENE-01),
- Sondenspitze (zu MECH-01),
- Elektrodengeometrie per Feldsimulation optimiert, inkl. Isolationsdicke (neu, Verif. S),
- Gateway-Varianten inkl. Lösung ohne Firmen-WLAN mitbewertet (CI Präzisierung).

**F-19 · klein · fehlt – Update der Gateway-Firmware und PWA ohne Datenverlust.**
→ „Gateway-Firmware/PWA aktualisierbar ohne Verlust von Historie und Kopplungen.“

**F-20 · klein · fehlt – Weitere Szenarien.**
- Sensor liegt ausserhalb der Erde (in Luft) → kein „Giessen nötig“-Alarm, sondern
  „nicht im Boden“.
- Überfluten: Wasser steht kurz über der Dichtlinie (z. B. 2 cm, 15 min) → Erweiterung von
  MECH-13.
- Kondenswasser im Kopf bei Temperaturwechsel.
- Vergessenes Passwort der PWA.
- Prüfnachweis bei MECH-13 über Feuchteindikator im Kopf.

**F-21 · klein · REQ-UI-01 – Mehrfarbige LED zulassen.** „Genau eine Status-LED“ sollte eine
mehrfarbige LED (eine Lichtöffnung) ausdrücklich erlauben, sonst sind fünf Zustände schwer
unterscheidbar.

Nicht beanstandet (geprüft): UI-03 (5 % LED-Budget ist bei ms-Pulsen grosszügig erfüllbar),
FW-05 (2 % pro OTA ist realistisch), SYS-02/03, SAF-LI-01..06, SAF-CC-03, FW-06,
APP-10 (Begründung zu Push ist korrekt).

## Quellen
- Placidi et al., „Characterization of Low-Cost Capacitive Soil Moisture Sensors for IoT
  Networks“, *Sensors* 2020, 20(12):3585, https://pmc.ncbi.nlm.nih.gov/articles/PMC7348898
- Adla et al., *Sensors* 2020 (Temperatur/Salinität kapazitiver Low-Cost-Sensoren),
  https://pmc.ncbi.nlm.nih.gov/articles/PMC7014303
- Texas Instruments, „Coin cells and peak current draw“, SWRA349, https://www.ti.com/lit/pdf/swra349
- Eigene Rechnungen (Biegung, Knicken, ppm, Speicher, Strombudget): oben im Text, reproduzierbar mit
  Python-Einzeiler (nicht im Repo abgelegt).

## Runde 2 (2026-11-06)

| | |
|---|---|
| Geprüft | `REQUIREMENTS.md` v0.2, `phase1_requirements_response.md` |
| Grundlagen | `PROJEKTAUFTRAG.md`, `CLIENT_INPUT.md` (inkl. Präzisierungen) |
| Ergebnis | F-01 gelöst. Von 7 🔶-Punkten 6 akzeptiert, 1 strittig (F-14/SAF-01). **Neu: 2 wichtige, 3 kleine Befunde, kein kritischer.** |

### F-01 (kritisch) – **gelöst, akzeptiert**
Kap. 1.2 übernimmt die Regel Sicherheit > Kosten > Komfort mit Eskalation an den Auftraggeber.
REQ-FAB-04 ist Muss mit Freigabevorbehalt. Jahresdiagramm, Firefox/Safari Desktop und
5-Jahres-Historie sind auf Soll gesetzt. Das entspricht „tiefer Preis ist zwingend“ und „wenn nicht
erreichbar, klar sagen und zeigen, was es kostet“.
Rest (klein, kein Freigabehindernis): „Sicherheitsbezug“ ist nur über Kap. 6 definiert.
Security-Anforderungen ausserhalb von Kap. 6 (REQ-FW-04, RF-05/06) sind damit formal
verhandelbar. Vorschlag: In 1.2 „Kap. 6 sowie REQ-FW-04, REQ-RF-05/06“ nennen.

### Urteile zu den 🔶-Antworten

| Punkt | Urteil | Begründung |
|---|---|---|
| F-07 Puffer vs. Zeit | **akzeptiert** | ±2 min/14 d = 99 ppm, ±5 min/60 d = 58 ppm. Beides ist mit einem 32-kHz-Quarz einhaltbar (FE-04: 39 ppm worst case). 60 statt 30 Tage Puffer ist besser als mein Vorschlag. Relative Zeit nach Zellwechsel ist geregelt. Rest siehe N-04. |
| F-09 Historie | **akzeptiert** | 2 Jahre Muss bei **30** Sensoren (strenger als mein Vorschlag mit 15): 30 × 6 × 730 = 131 400 Datensätze, roh ca. 2 MB. Das bleibt für ein MCU-Gateway mit grösserem Flash machbar. „Dauerhaft“ ist über Backup (GW-06) gewahrt. |
| F-14 Brand/Verschlucken | **strittig** (Teil SAF-01) | Verschluckschutz als Muss ist gelöst. Das relative Kriterium ΔT ≤ 25 K ist sinnvoll begründet. Der Zusatz „absolut stets unter der Formbeständigkeit“ ist aber ohne Bezugstemperatur nicht prüfbar und widerspricht den übrigen Zahlen, siehe **N-02**. |
| F-15 4 Lagen | **akzeptiert** | Der Wortlaut des Auftraggebers wird beibehalten, Muss ist der dokumentierte Vergleich. Damit ist das prüfbar. |
| FE-03 1 min als Muss | **akzeptiert** | Die CLIENT_INPUT-Präzisierung legt ausdrücklich Muss ≤ 5 min und Soll ≤ 1 min fest. Den Ausschluss der Scan-Variante in Phase 2 zu entscheiden, ist korrekt. Die Muss-Kette ist aber nicht sauber, siehe **N-01**. |
| FE-04 Quarz als Muss | **akzeptiert** | Eine lösungsneutrale Zahl in SYS-07 ist richtig. Der Nachweis braucht allerdings eine Temperaturbedingung, siehe N-04. |
| FE-08 ESP32 an Knopfzelle | **akzeptiert** | REQ-ENE-09 ([CC] Schlaf ≤ 3 µA, Mittel ≤ 8 µA) schliesst die ESP32-Klasse für die Knopfzelle aus (Deep Sleep 5 µA laut FE-08). Für [LI] bleibt sie offen, wie von FE-08 vorgeschlagen. |

### Neue Befunde aus v0.2

**N-01 · wichtig · REQ-ENE-09 ↔ REQ-SYS-05 ↔ REQ-ENE-04 – Das Soll von 1 min wird über das Strombudget zum Muss.**
- *Begründung:* ENE-09 (Muss) fordert einen Mittelstrom ≤ 8 µA im **Standardprofil**. ENE-04
  legt das Standardprofil auf 1 min Reaktionszeit fest. Erfüllt ein Konzept 12 Monate bei 2 oder
  5 min, aber nicht 8 µA bei 1 min, verletzt es ein Muss, obwohl SYS-05 nur ≤ 5 min verlangt.
  Zudem richtet sich die Werkseinstellung nach SYS-05 an ENE-02/03 aus, nicht an ENE-09. Damit
  gibt es zwei verschiedene Kriterien.
- *Vorschlag:* Den Mittelstrom in ENE-09 auf das „Standardprofil mit der Werkseinstellung
  nach REQ-SYS-05“ beziehen. In SYS-05 ergänzen: „… der REQ-ENE-02/03 **und** REQ-ENE-09
  erfüllt“. Die Werte für 1/2/5 min in ENE-04 als Ausweis belassen.

**N-02 · wichtig · REQ-SAF-01 ↔ RB-03 ↔ REQ-MECH-12 – Das absolute Temperaturkriterium im Fehlerfall ist nicht prüfbar.**
- *Begründung:* Im Fehlerfall sind ΔT ≤ 25 K zulässig. In der Sonne liegt der Kopf bei 65 °C,
  zusammen also bis 90 °C. Die Mindestformbeständigkeit nach MECH-12 ist aber nur 70 °C.
  Bei einem Material an der Untergrenze bleiben am Sonnenplatz nur 5 K für den Fehlerfall.
  Ein Test bei Raumtemperatur sagt darüber nichts aus.
- *Vorschlag:* SAF-01 so fassen: „ΔT bei Raumtemperatur messen. Nachweis:
  65 °C (RB-03) + gemessenes ΔT < Formbeständigkeit des Gehäusematerials laut Datenblatt.“
  MECH-12 auf „≥ 65 °C + max. Fehlererwärmung, mindestens 70 °C“ koppeln, oder pauschal
  ≥ 90 °C (Materialwert in Phase 2 aus dem Datenblatt belegen).

**N-03 · klein · RB-03, REQ-ENE-04, Kap. 6.3 – Der Temperaturumfang ist unklar.**
- *Begründung:*
  - Betrieb ist mit 5–45 °C Umgebung angegeben, der Kopf erreicht aber 65 °C, und die
    Lagerung ist nur bis 50 °C festgelegt. Offen bleibt, ob der Sensor bei 65 °C Kopftemperatur
    funktionieren muss oder diese nur unbeschädigt überstehen muss.
  - Für [CC] fehlt ein Gegenstück zu LI-09 (Zelle bei 65 °C: Selbstentladung, Auslaufen).
  - Der „Zuschlag für Sonnenplatz“ in ENE-04 ist nicht beziffert. Die Rechnung A ist damit
    nicht reproduzierbar.
- *Vorschlag:* In RB-03 ergänzen: „Kopf bis 65 °C: Funktion und kein Schaden; Messgenauigkeit
  nur 10–35 °C.“ Neue REQ-SAF-CC-05: Zelle laut Datenblatt bis 65 °C zulässig. ENE-04:
  Sonnenprofil beziffern, z. B. „4 h/Tag bei 50 °C (**ANNAHME**)“.

**N-04 · klein · REQ-SYS-07 ↔ REQ-GW-09 – Bezug und Bedingungen der Zeitgenauigkeit fehlen.**
- *Begründung:*
  - SYS-07 nennt keine Referenz: Ist die Abweichung gegen die Gateway-Zeit oder gegen die echte
    Zeit gemeint? Die Gateway-Drift (±2 min/Monat) addiert sich sonst.
  - SYS-07 nennt auch keine Temperatur. Gerechnet mit einem Quarz bei dauerhaft 65 °C
    (20 ppm + 0.034 ppm/K² × 40² ≈ 74 ppm, Koeffizient **ANNAHME**, typisch für
    Stimmgabelquarze) ergeben sich 386 s in 60 d. Das liegt über ±5 min.
- *Vorschlag:* „Abweichung gegenüber der Gateway-Zeit beim letzten Abgleich, über
  RB-03-Umgebung 5–45 °C; Nachweis A aus dem Datenblatt plus T über 7 d.“

**N-05 · klein · REQ-ENE-06/08 – Abschaltschwelle und Messpunkt fehlen.**
- *Begründung:*
  - Die Laufzeitrechnung hängt von der Abschaltspannung ab, die nirgends beziffert ist
    (FE-07 schlug 2.0 V unter Last vor).
  - 0.2 V bei 100 Ω bedeuten einen Zellstrom ≤ 2 mA während des Ereignisses. Das ist richtig,
    erzwingt aber einen Puffer-C. Offen bleibt, ob an der Zellklemme oder an VDD gemessen wird.
  - Der OTA-Dauerbetrieb ist nicht abgegrenzt.
- *Vorschlag:* In ENE-08 ergänzen: „Ende der nutzbaren Kapazität = 2.0 V unter Last
  (**ANNAHME** bis Chipwahl)“. In ENE-06 ergänzen: „gemessen an der Zellklemme, Lastfall
  Funkereignis; OTA nur oberhalb der Schwelle nach FW-02“.

Geprüft ohne Befund: Pufferdauer 60 d vs. Warnschwelle 30 d (ENE-05), Strombudget gegen Laufzeit
(8 µA + 20 % = 84 mAh/a gegen 169 mAh nutzbar bei CR2032 ergibt ≈ 1.9 Jahre, also Reserve
vorhanden), UI-03 vs. OP-02 (1×/min), SAF-CC-04 vs. MECH-15 (Münze als Werkzeug passt zu
UL 4200A, **ANNAHME** ohne lokale Norm), FW-05 (2 % ≈ 3.4 mAh), GW-01-Speicherbedarf.
Rechnungen: Python-Einzeiler, reproduzierbar aus den hier genannten Zahlen.
