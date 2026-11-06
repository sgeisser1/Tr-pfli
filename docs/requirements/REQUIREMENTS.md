# Tröpfli – Anforderungsdokument

| | |
|---|---|
| Dokument | `docs/requirements/REQUIREMENTS.md` |
| Version | **0.2** (nach Prüfrunde 1) |
| Datum | 2026-11-06 |
| Grundlagen | `PROJEKTAUFTRAG.md` (Original), `CLIENT_INPUT.md` (Antworten Phase 0), `DECISIONS.md` |
| Prüfberichte | `docs/reviews/phase1_requirements_{redteam,sicherheit,firmware-energie}.md`, Antworten: `phase1_requirements_response.md` |
| Status | zur Freigabe durch den Auftraggeber |

Änderungen gegenüber v0.1 sind mit der Befund-ID markiert, z. B. *(S-K01)*.

## 1 Zweck und Systemübersicht

Tröpfli überwacht die Bodenfeuchte von Topfpflanzen im Büro. Das System besteht aus:

- **Sensor** (10–15 Stück): Stab mit kleinem, abgedichtetem Kopf (Elektronik, Energiequelle, LED,
  Taster) und einer ca. 100 mm langen Sonde, die als Teil der Leiterplatte in die Erde gesteckt wird.
  Misst kapazitiv die Feuchte sowie die Temperatur, puffert Messwerte und funkt sie lokal.
- **Gateway** (1 Stück): dauerhaft mit Strom versorgt, empfängt und speichert die Daten aller Sensoren
  und stellt die **PWA „Tröpfli“** im lokalen Netz bereit.
- **PWA**: Bedienung auf Smartphone (iOS, Android) und PC.

Alles bleibt **strikt lokal**: keine Cloud, keine externen Server, kein Zugriff aus dem Internet.

### 1.1 Begriffe
- **Muss**: zwingend für die Fertigungsfreigabe. **Soll**: angestrebt, Abweichung begründen.
  **Kann**: optional, nur wenn Kosten- und Energieziel nicht gefährdet sind.
- **Feuchteindex**: kalibrierter relativer Wert 0–100 % (0 % = Trockenpunkt, 100 % = Nasspunkt der
  Zwei-Punkt-Kalibrierung). Kein absoluter volumetrischer Wassergehalt. **%-Punkte** bezeichnen
  Differenzen auf dieser Skala.
- **Messzyklus**: Aufwachen, Messen (Feuchte + Temperatur + Batterie), Speichern, Senden, Schlafen.
- **Reaktionszeit**: Zeit vom Auslösen „Jetzt messen“ in der PWA bis zur Anzeige des neuen Werts.
- **Verifikation**: A = Analyse/Rechnung, S = Simulation, I = Inspektion (Unterlagen/Muster),
  T = Test am Prototyp.

### 1.2 Prioritätsregel bei Zielkonflikten *(F-01)*
**Sicherheit > Kosten > Komfort.** Verhindert eine Muss-Anforderung **ohne Sicherheitsbezug** das
Kostenziel REQ-FAB-04, wird sie dem Auftraggeber mit den Mehrkosten zur Entscheidung vorgelegt.
Sicherheitsanforderungen (Kap. 6) werden nie zugunsten der Kosten gesenkt.

### 1.3 Kennzeichnungen
**ANNAHME**: noch nicht belegte Annahme, wird in Phase 2 bestätigt oder ersetzt.
**PROTOTYP-PRÜFUNG**: erst am echten Prototyp nachweisbar.
**[LI]** gilt nur für die Akku-Variante, **[CC]** nur für die Knopfzellen-Variante.

## 2 Rahmenbedingungen

| ID | Rahmenbedingung |
|---|---|
| RB-01 | Einsatz vorerst in **einem Büroraum ca. 10 × 15 m**, innen. |
| RB-02 | Töpfe Ø 15–30 cm, Substrat **Erde und Granulat** (z. B. Blähton-/Mineralgranulat), gedüngt. |
| RB-03 | Umgebung: Raumklima; Sensoren können auf der Fensterbank in der Sonne stehen. Betrieb 5–45 °C Umgebung; **Kopftemperatur in praller Sonne bis 65 °C** (**ANNAHME**, am Muster messen); Lagerung −10–50 °C. *(F-13, S-W06)* |
| RB-04 | Firmen-WLAN vorhanden, Qualität mässig. Ein Gateway im Firmen-WLAN ist **zulässig**, Lösungen mit wenig Eingriff ins Firmennetz werden bevorzugt. |
| RB-05 | Kein dauerhaft laufender Rechner vorhanden. Ein Raspberry Pi nur, wenn nötig (begründen). |
| RB-06 | Eigengebrauch, keine Zertifizierung. Sicherheit hat trotzdem höchste Priorität. |
| RB-07 | Fertigung der Sensor-Leiterplatte inkl. Bestückung bei JLCPCB; Gehäuse auf Bambu Lab P1S mit AMS (**ANNAHME** Modell). |
| RB-08 | Kein Programmieradapter vorhanden; keine Messgeräte-Anschaffung von ca. 100 CHF. Werkstatt sonst gut ausgerüstet. |
| RB-09 | Stückzahlen: Prototyp-Los in kleinster sinnvoller JLC-Menge (aktuelle Mindestmengen PCB und PCBA in Phase 2 recherchiert), danach Serie 10–15 Sensoren. *(F-18)* |

## 3 Anwendungsfälle

| ID | Anwendungsfall | Ablauf (Kurzform) |
|---|---|---|
| UC-01 | **Erstinbetriebnahme Gateway** | Gateway einstecken, ins Netz bringen, PWA öffnen, Vertrauensstellung (HTTPS) einrichten, Passwort setzen, PWA installieren. |
| UC-02 | **Neuen Sensor koppeln** | Energiequelle einsetzen/laden → Taster lang drücken → Sensor erscheint in der PWA als `troepfli-XXXX` → Nutzer bestätigt, gibt Pflanzennamen und Substrat ein. |
| UC-03 | **Automatische Messung** | Im eingestellten Intervall misst der Sensor, puffert und überträgt; PWA zeigt aktuellen Wert und Verlauf. |
| UC-04 | **Manuelle Messung** | In der PWA „Jetzt messen“ → Wert innert Reaktionszeit (REQ-SYS-05). Alternativ kurzer Tastendruck am Sensor. |
| UC-05 | **Kalibrierung** | In der PWA geführt „Trocken“ und „Nass“ auslösen; Werte werden gespeichert. |
| UC-06 | **Giessen nötig** | Pro Pflanze Schwellenwert; PWA hebt Pflanzen unter dem Schwellenwert hervor. |
| UC-07 | **Verlauf und Export** | Verlauf je Pflanze ansehen; CSV exportieren. |
| UC-08 | **Firmware-Update Sensor** | Firmware auf das Gateway laden → Gateway verteilt sie an die Sensoren, ohne Öffnen des Gehäuses. |
| UC-09 | **Energiequelle wechseln/laden** | PWA warnt bei tiefem Stand; Wechsel bzw. Laden gemäss Anleitung. |
| UC-10 | **Gateway-Ausfall** | Gateway Stunden bis Wochen aus; Sensoren puffern; Nachlieferung mit korrektem Zeitstempel. |
| UC-11 | **Sensor entfernen/umziehen** | Sensor in andere Pflanze stecken oder entkoppeln; Historie bleibt der Pflanze bzw. dem Sensor zugeordnet (Nutzer wählt). |
| UC-12 | **Fehlerfall am Sensor** | LED zeigt Fehler; PWA zeigt Detailmeldung. |
| UC-13 | **Netzänderung** *(F-11)* | WLAN-Passwort oder IP-Adresse des Gateways ändert sich; Nutzer stellt das Gateway um, ohne Sensoren neu zu koppeln. |
| UC-14 | **Gateway ersetzen / aktualisieren** *(F-11, F-19)* | Backup einspielen auf neues Gateway bzw. Software-Update des Gateways und der PWA, ohne Verlust von Daten und Kopplungen. |
| UC-15 | **Sensor ausserhalb der Erde** *(F-20)* | Sensor liegt herausgezogen in der Luft oder Topf ist überflutet; PWA zeigt einen plausiblen Hinweis statt eines falschen Werts. |
| UC-16 | **Passwort vergessen** *(F-20)* | Zurücksetzen nur mit physischem Zugang zum Gateway, Daten bleiben erhalten. |

## 4 Systemanforderungen

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-SYS-01 | Das System arbeitet ohne Internetverbindung vollständig. Kein Datenverkehr zu Servern ausserhalb des LAN; einzige Ausnahme: Zeitabgleich des Gateways nach REQ-GW-09. *(F-06)* | Muss | T, I |
| REQ-SYS-02 | Ein Gateway versorgt mindestens **15 Sensoren** im Raum nach RB-01. | Muss | A, T |
| REQ-SYS-03 | Kapazität: bis **30 Sensoren** pro Gateway ohne Hardwareänderung. | Soll | A |
| REQ-SYS-04 | Automatische Messungen: Intervall einstellbar **1–96×/Tag**, Standard **6×/Tag**. *(FE-13)* | Muss | T |
| REQ-SYS-05 | Reaktionszeit der manuellen Messung (95 % der Auslösungen): **≤ 5 min** (Muss), **≤ 1 min** (Soll). Die Reaktionszeit ist im Bereich 1–5 min einstellbar; Werkseinstellung ist der kürzeste Wert, der REQ-ENE-02 bzw. -03 noch erfüllt. *(F-02, FE-03)* | Muss/Soll | A, T |
| REQ-SYS-06 | Zwei-Wege-Kommunikation Gateway → Sensor für: manuelle Messung, Kalibrierung, Einstellungen, Zeit, Firmware-Update. | Muss | T |
| REQ-SYS-07 | Zeitstempel der Messwerte: Abweichung ≤ **±2 min** nach 14 Tagen und ≤ **±5 min** nach 60 Tagen ohne Gateway. Nach einem Energiequellenwechsel ohne Gateway werden Werte mit relativer Zeit gespeichert und beim nächsten Kontakt korrekt zurückgerechnet. *(F-07, FE-04)* | Muss | A, T |
| REQ-SYS-08 | Eindeutige Sensor-ID, sichtbar als `troepfli-XXXX` (XXXX aus Chip-ID, hexadezimal). | Muss | I |
| REQ-SYS-09 | Datenformat (Funk und Export) versioniert und dokumentiert. | Muss | I |
| REQ-SYS-10 | Anbindung an MQTT / Home Assistant (Auto-Discovery). | Kann | T |
| REQ-SYS-11 | Architektur erlaubt später mehrere Gateways bzw. Räume (eindeutige Gateway-ID, Sensor gehört genau einem Gateway); nicht umgesetzt in Rev. A. *(F-11)* | Soll | A |

## 5 Sensor

### 5.1 Messung Feuchte

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-MES-01 | Kapazitives Messprinzip; die Sonde ist Teil der Hauptleiterplatte (ein durchgehendes PCB). | Muss | I |
| REQ-MES-02 | Ausgabe als Feuchteindex 0–100 % nach Zwei-Punkt-Kalibrierung, zusätzlich Rohwert. | Muss | T |
| REQ-MES-03 | Auflösung ≤ **1 %** des kalibrierten Bereichs. | Muss | A, T |
| REQ-MES-04 | Wiederholbarkeit bei unverändertem Substrat und Temperatur: Standardabweichung ≤ **1 %-Punkt** über 10 Messungen. | Muss | T |
| REQ-MES-05 | Temperatureinfluss nach Kompensation ≤ **0.3 %-Punkte/K** im Bereich 10–35 °C. Prüfmethode: Substrat in verschlossenem Beutel bei ca. 8, 22 und 35 °C (Kühlschrank, Raum, Wärmequelle), dazu Luft und Wasser als Referenzmedien. *(F-04)* | Soll | T, PROTOTYP-PRÜFUNG |
| REQ-MES-06 | Langzeitstabilität: Rohwerte in Luft und in Wasser vor und nach **30 Tagen** Eintauchen bis zur Dichtlinie unterscheiden sich um ≤ **3 %** der Kalibrierspanne; Zwischenmessungen nach 1, 7, 14 Tagen zur Erkennung der FR4-Sättigung. *(F-05)* | Muss | T, PROTOTYP-PRÜFUNG |
| REQ-MES-07 | Exemplarstreuung vor Kalibrierung: eine gemeinsame Startkalibrierung genügt für ±15 %-Punkte (nutzbar ohne Einzelkalibrierung). | Soll | T |
| REQ-MES-08 | Messvolumen: ≥ **80 %** der Kapazitätsänderung stammt aus dem Bereich 10–90 mm unterhalb der Dichtlinie (Feldsimulation, Plausibilisierung im Becherversuch mit stufenweiser Füllhöhe). *(F-17)* | Soll | S, T |
| REQ-MES-09 | Kalibrierwerte pro Sensor und Substrattyp (Erde, Granulat) speicherbar; Substrattyp pro Pflanze wählbar. | Muss | T |
| REQ-MES-10 | Mittelung mehrerer Einzelmessungen pro Messzyklus; Ausreisser werden erkannt. | Muss | I, T |
| REQ-MES-11 | Einfluss von Dünger/Salzgehalt: Feuchteindex ändert sich bei gleicher Feuchte zwischen Leitungswasser und üblich dosierter Flüssigdüngerlösung um ≤ **5 %-Punkte** (Becherversuch). Die Wahl der Messfrequenz bzw. des Messprinzips berücksichtigt dies. *(F-03)* | Soll | T, PROTOTYP-PRÜFUNG |
| REQ-MES-12 | Plausibilitätserkennung: Sensor in Luft (unter Trockenpunkt) und Überflutung (über Nasspunkt) werden als solche gemeldet. *(F-20)* | Soll | T |

### 5.2 Messung Temperatur

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-TMP-01 | Bodentemperatur nahe der Dichtlinie unter der Versiegelung, Genauigkeit ≤ **±1.0 °C** (10–35 °C) im Schatten; bei Sonneneinstrahlung auf den Kopf wird die Abweichung am Muster ermittelt und dokumentiert. *(F-13)* | Muss | A, T |
| REQ-TMP-02 | Temperatur wird für die Feuchtekompensation verwendet. | Muss | I |
| REQ-TMP-03 | Lufttemperatur im Kopf. | Kann | – |
| REQ-TMP-04 | Weitere Sensoren (Luftfeuchte, Licht) nur, wenn Mehrkosten ≤ 0.50 CHF/Sensor und Laufzeitverlust ≤ 5 %. | Kann | A |

### 5.3 Logging

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-LOG-01 | Sensor puffert mindestens **60 Tage** Messwerte (bei 6 Messungen/Tag) mit Zeitstempel **nichtflüchtig**, wenn das Gateway nicht erreichbar ist. *(F-07, FE-12)* | Muss | A, T |
| REQ-LOG-02 | Nachlieferung gepufferter Werte ohne Duplikate und ohne Verlust, sobald das Gateway erreichbar ist. | Muss | T |
| REQ-LOG-03 | Pufferinhalt übersteht einen Energiequellenwechsel. | Muss | T |

### 5.4 Energie und Laufzeit

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-ENE-01 | Variantenvergleich mindestens (a) LiPo mit USB-C-Laden und vollständiger Schutzschaltung, (b) Knopfzelle (z. B. CR2032/CR2450) mit sehr sparsamem Funkchip. Bewertet werden Sicherheit, Laufzeit, Kopfgrösse, Kosten, Aufwand; für jede Variante ein Energiebudget. | Muss | A |
| REQ-ENE-02 | **[CC] Primärbatterie:** Laufzeit ≥ **12 Monate** im Standardprofil, gerechnet mit den pessimistischen Annahmen nach REQ-ENE-08. | Muss | A, PROTOTYP-PRÜFUNG |
| REQ-ENE-03 | **[LI] Akku:** Laufzeit pro Ladung ≥ **3 Monate** im Standardprofil. | Muss | A, PROTOTYP-PRÜFUNG |
| REQ-ENE-04 | **Standardprofil**: 6 Messungen/Tag mit Übertragung, 2 manuelle Messungen/Tag, Reaktionszeit **1 min** (Soll-Wert REQ-SYS-05), LED gemäss Standardmuster, 1 Firmware-Update/Jahr, Sendeleistung gemäss Funkkonzept, mittlere Temperatur 25 °C mit Zuschlag für Sonnenplatz. Zusätzlich wird die Laufzeit für 2 und 5 min Reaktionszeit ausgewiesen. *(F-02, FE-03, FE-16)* | Muss | A |
| REQ-ENE-05 | Batteriestand wird bestimmt (Spannung unter Last plus Ereigniszählung) und angezeigt; Warnung, wenn die geschätzte Restlaufzeit < **30 Tage** ist. *(F-08, FE-15)* | Muss | T |
| REQ-ENE-06 | Spannungseinbrüche beim Senden führen nicht zu Resets oder Datenverlust bis zur definierten Abschaltschwelle; Einbruch ≤ **0.2 V** bei Zellinnenwiderstand 100 Ω; definierte Abschaltung (Unterspannung unter Last) mit sauberem Speichern. *(FE-07)* | Muss | S, T |
| REQ-ENE-07 | Energieverbrauch am Prototyp mit Werkstattmitteln messbar; Messpunkt im Versorgungspfad, der **keine Schutzfunktion umgeht**. *(S-L01)* | Muss | I |
| REQ-ENE-08 | **Pessimistische Rechenannahmen** (verbindlich für alle Laufzeitangaben): nutzbare Kapazität ≤ **75 %** der Nennkapazität für Knopfzellen mit Pufferkondensator (≤ 60 % ohne), Selbstentladung nach Herstellerangabe, Ruheströme = Datenblatt-Typwert × 1.5 oder Maximalwert, Zuschlag **+20 %** auf den Gesamtverbrauch. Nur Markenzellen laut Stückliste. *(F-08, FE-01)* | Muss | A |
| REQ-ENE-09 | **[CC] Strombudget:** Mittelstrom im Standardprofil ≤ **8 µA**, Ruhestrom (Schlaf) ≤ **3 µA**, am Prototyp gemessen. **[LI]** Ruhestrom von Lade- und Schutzschaltung ≤ **5 µA**. *(FE-02, FE-09)* | Muss | A, T |

### 5.5 Funk

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-RF-01 | Funktechnik nach dokumentiertem Vergleich (mindestens BLE vs. WLAN im Sensor); gewählt wird, was Laufzeit-, Kosten- und Sicherheitsziele erfüllt. *(F-15 sinngemäss)* | Muss | A |
| REQ-RF-02 | Reichweite: Über **7 Tage** Betrieb mit allen Sensoren an ihren Plätzen im Raum (RB-01, max. ca. 18 m) erreichen ≥ **99 %** der Messwerte das Gateway innert 1 h, **100 %** nach Nachlieferung. *(F-16)* | Muss | A, T |
| REQ-RF-03 | Linkreserve am schlechtesten Platz ≥ **10 dB** über der Empfängerempfindlichkeit; Sendeleistung anpassbar. *(FE-14)* | Soll | T |
| REQ-RF-04 | Antenne am oberen Ende des Kopfes, möglichst weit von der Erde entfernt, Keepout gemäss Hersteller. | Muss | I |
| REQ-RF-05 | Pairing nur nach bewusster Handlung (Tastendruck am Sensor **und** Bestätigung in der PWA). Beim Pairing wird ein individueller Schlüssel pro Sensor vereinbart. *(S-W08)* | Muss | T |
| REQ-RF-06 | Befehle und Firmware-Updates nimmt der Sensor nur vom gekoppelten Gateway an; Nachrichten sind gegen Verfälschung und Wiedereinspielen (Replay) geschützt. *(S-W08)* | Muss | T |

### 5.6 Firmware

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-FW-01 | Deep Sleep zwischen den Aktivitäten. | Muss | I, T |
| REQ-FW-02 | Firmware-Update über Funk (OTA) via Gateway, ohne Öffnen des Gehäuses; nur oberhalb einer definierten Batterieschwelle. *(FE-10)* | Muss | T |
| REQ-FW-03 | Abgebrochenes Update führt nicht zu einem unbrauchbaren Sensor (Rückfall auf vorherige Version); Flash ≥ 2 Firmware-Abbilder plus Puffer. *(FE-10)* | Muss | T |
| REQ-FW-04 | Nur **signierte** Firmware wird installiert; Schutz gegen Rückfall auf ältere, unsichere Versionen; Signierschlüssel nicht auf dem Gateway. *(S-W07)* | **Muss** | T |
| REQ-FW-05 | Ein OTA-Update beansprucht ≤ **2 %** der Batteriekapazität. | Soll | A, T |
| REQ-FW-06 | Erstprogrammierung ohne teuren Adapter: durch JLC vorprogrammierbar, über Bootloader mit USB-UART-Adapter oder mit einem Adapter ≤ **10 CHF** (RB-08), **ohne die Zelle zu laden** (siehe REQ-SAF-CC-03). *(FE-06)* | Muss | I |
| REQ-FW-07 | Watchdog; nach Absturz automatischer Neustart, Fehler wird gemeldet. | Muss | T |
| REQ-FW-08 | Firmware-Version in der PWA sichtbar. | Muss | T |

### 5.7 Bedienelemente

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-UI-01 | Genau eine Status-LED (ein- oder mehrfarbig) und ein Taster, kein Display. *(F-21)* | Muss | I |
| REQ-UI-02 | Blinkmuster für: Messung/Senden bestätigt, Pairing-Modus, verbunden, Batterie tief, Fehler. Festgelegt und dokumentiert. | Muss | I |
| REQ-UI-03 | LED-Energie ≤ **5 %** des Energiebudgets im Standardprofil; keine periodischen Anzeigen häufiger als **1×/min**. *(FE-11)* | Muss | A |
| REQ-UI-04 | Tasterfunktionen mindestens: kurz = manuelle Messung + Status, lang (≥ 3 s) = Pairing, sehr lang (≥ 10 s) = Werkseinstellungen. | Muss | T |
| REQ-UI-05 | LED aus normaler Blickrichtung (stehend, schräg von oben) erkennbar; Taster mit einem Finger bedienbar, ohne die Sonde im Topf zu verbiegen. | Muss | T |
| REQ-UI-06 | Fehlbetätigung (z. B. Giesswasser, Anstossen) löst keine Werkseinstellung aus. | Muss | T |

### 5.8 Mechanik und Sonde

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-MECH-01 | Sondenlänge im Boden ca. **100 mm** (±10 mm); definierte Sondenspitze; Markierung der maximalen Stecktiefe. *(F-18)* | Muss | I |
| REQ-MECH-02 | Kopf so klein wie möglich. Zielwerte (**ANNAHME**, nach Energiequellenwahl bestätigt): Querschnitt ≤ **35 × 20 mm**, Höhe ≤ **45 mm** über der Erde; AAA/AA ausgeschlossen. | Soll | I |
| REQ-MECH-03 | Kein freiliegendes Metall im Sondenbereich. | Muss | I |
| REQ-MECH-04 | Elektroden möglichst auf Innenlagen eines 4-Lagen-PCB, Aussenlagen im Sondenbereich ohne Kupfer; Entscheid nach dokumentiertem Vergleich mit 2 Lagen + Beschichtung (Empfindlichkeit, Kosten, Lebensdauer). *(F-15)* | Muss | A, I |
| REQ-MECH-05 | Keine Vias im nassen Bereich, ausser gefüllt und abgedeckt mit dokumentierter Begründung. | Muss | I |
| REQ-MECH-06 | Kupferabstand zur Platinenkontur im Sondenbereich ≥ **1.0 mm**. | Muss | I (DRC) |
| REQ-MECH-07 | Schnittkanten und Sonde versiegelt; Verfahren nach Vergleich (Conformal Coating, Epoxid, Schrumpfschlauch mit Kleber) gewählt, mit Anleitung. | Muss | I, T |
| REQ-MECH-08 | Definierte Dichtlinie am Übergang Sonde/Gehäuse; kein Wasser kriecht entlang der Platine ins Gehäuse (Prüfung mit Feuchteindikator im Kopf). *(F-20)* | Muss | T |
| REQ-MECH-09 | Masse-/Guard-Struktur zwischen Elektronik und Sonde. | Muss | I |
| REQ-MECH-10 | Robustheit der Sonde, mit dokumentierter Lagerung im Kopf, Sicherheitsfaktor ≥ 2 gegen Bruch, keine bleibende Verformung: **axial 50 N** (Einstecken), **seitlich 10 N** an der Spitze, **Zug 30 N** (Herausziehen), **Fall aus 1 m** auf harten Boden (Kopf voran und flach). Lastwerte **ANNAHME**, Plausibilisierung am Prototyp. Anleitung empfiehlt Vorstechen in verdichteter Erde. *(F-10)* | Muss | S, T |
| REQ-MECH-11 | Leiterplattendicke festgelegt (1.6 oder 2.0 mm) und begründet; Elektrodengeometrie per Feldsimulation optimiert (Empfindlichkeit, Messvolumen, Isolationsdicke). *(F-18)* | Muss | A, S |
| REQ-MECH-12 | Gehäuse FDM-druckbar auf Bambu Lab, Material feuchte- und UV-geeignet und formstabil bis mindestens **70 °C** (RB-03) (z. B. ASA; PETG nur mit Nachweis; kein PLA). *(F-13)* | Muss | I |
| REQ-MECH-13 | Spritzwasserschutz Kopf: kein Wassereintritt bei Giessen von oben (1 l Wasser aus 20 cm Höhe über den Kopf, 10 Wiederholungen; Anlehnung IPX4-Methode), **geprüft mit eingesetzter Energiequelle**, danach Öffnen und Sichtprüfung auf Feuchte/Kondensat. *(S-K01)* | Muss | T |
| REQ-MECH-14 | Sonde: dauerhaft in nassem Substrat ohne Funktionsverlust; Wassertest ≥ **30 Tage** bis zur Dichtlinie vor Freigabe der Serie (siehe REQ-MES-06). | Muss | T, PROTOTYP-PRÜFUNG |
| REQ-MECH-15 | Batteriefach bzw. Ladeport dicht und ohne Spezialwerkzeug zugänglich (ein handelsüblicher Schraubenzieher bzw. eine Münze gilt nicht als Spezialwerkzeug); Wechsel/Laden ohne Lösen der Sondendichtung. | Muss | T |
| REQ-MECH-16 | Revisionsstand auf PCB-Silkscreen; Produktname „Tröpfli“ bzw. Logo auf Gehäuse und Silkscreen. | Muss | I |
| REQ-MECH-17 | Sensor steht stabil; Kopfgewicht kippt die Sonde in lockerem Granulat nicht. | Soll | T |
| REQ-MECH-18 | Kein Kondenswasser im Kopf nach 7 Tag/Nacht-Zyklen auf der Fensterbank (Feuchteindikator). *(F-20)* | Soll | T, PROTOTYP-PRÜFUNG |

## 6 Sicherheit

### 6.1 Allgemein

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-SAF-01 | Brandrisiko minimal. Kriterium: In jedem **Einzelfehlerfall** der FMEA-Liste (mindestens Kurzschluss am Ausgang der Energiequelle, Verpolung, Wassereintritt, Kurzschluss jedes Bauteils im Versorgungspfad) keine Flamme, kein Rauch, kein Aufblähen; Erwärmung der Gehäuseoberfläche durch den Fehler ≤ **25 K** gegenüber dem fehlerfreien Zustand bei gleicher Umgebung (**ANNAHME**, Grenzwert in Phase 2 mit Quelle belegen) und absolut stets unter der Formbeständigkeit des Gehäusematerials. *(S-W05, F-14)* | Muss | A (FMEA), T |
| REQ-SAF-02 | Für die gewählte Energiequelle liegt eine **FMEA-light** vor (Fehler, Ursache, Wirkung, Bewertung, Massnahme, Restrisiko). | Muss | I |
| REQ-SAF-03 | Wenn eine nicht wiederaufladbare Lösung sicherer und günstiger ist und die Laufzeit erfüllt, wird sie empfohlen. | Muss | A |
| REQ-SAF-04 | Der Sicherheits-Agent hat ein Veto; offene kritische Befunde blockieren die Fertigungsfreigabe. | Muss | I |
| REQ-SAF-05 | **Wasser im Kopf bei eingesetzter Energiequelle:** Energiequellenfach ist vom Elektronikraum und vom Sondenübergang getrennt abgedichtet. Einzelfehlertest: Fach bzw. Elektronikraum je separat mit Leitungswasser geflutet, Energiequelle eingesetzt, 24 h beobachtet: Kriterien nach REQ-SAF-01, Zellstrom protokolliert. [LI] Zellanschlüsse und Schutzschaltung vergossen oder beschichtet. *(S-K01)* | Muss | T |
| REQ-SAF-06 | Programmier- und Testpads liegen im abgedichteten Raum und speisen keine Energie in die Energiequelle zurück. *(S-L02, S-W01)* | Muss | I, T |

### 6.2 Lithium-Akku [LI] (falls gewählt)

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-SAF-LI-01 | Zelle mit integrierter Schutzschaltung (Überladung, Tiefentladung, Überstrom/Kurzschluss). | Muss | I |
| REQ-SAF-LI-02 | Laderegler mit NTC-Überwachung, NTC thermisch an die Zelle gekoppelt; Laden nur im Temperaturfenster laut Zelldatenblatt (typisch 0–45 °C, **ANNAHME** bis Zellwahl). *(S-W02)* | Muss | I, T |
| REQ-SAF-LI-03 | Ladestrom ≤ 0.5 C bzw. Datenblattwert der Zelle inkl. temperaturabhängiger Reduktion; Vorladung bei tiefentladener Zelle; Ladeschluss-Timer; Toleranz der Ladeschlussspannung ≤ ±1 %. *(S-W03)* | Muss | I, T |
| REQ-SAF-LI-04 | Verpolschutz und Tiefentladeabschaltung auf der Platine (zusätzlich zur Zelle); Ruhestrom nach Abschaltung so klein, dass die Zelle ≥ 6 Monate nicht unter die Datenblattgrenze fällt. *(S-W03)* | Muss | I, T |
| REQ-SAF-LI-05 | Keine mechanische Belastung der Zelle: Kraftfluss beim Einstecken der Sonde und beim Tastendruck läuft nicht über die Zelle; Quellraum für die Zelle laut Datenblatt (bzw. ≥ 10 % der Dicke, **ANNAHME**). *(S-W04)* | Muss | I |
| REQ-SAF-LI-06 | Ladeport abgedeckt und so angeordnet, dass Giesswasser ihn nicht erreicht; Anleitung: nur ausserhalb des Topfs und beaufsichtigt laden. | Muss | I, T |
| REQ-SAF-LI-07 | **Alle Schutzfunktionen** (Überladung, NTC-Fenster, Ladestrom, Timer, Tiefentladung, Verpolung) wirken **hardwareseitig und unabhängig von der Firmware**. Nachweis: Schaltungsanalyse und Test mit gelöschter bzw. angehaltener MCU. *(S-K02)* | Muss | A, T |
| REQ-SAF-LI-08 | VBUS-Eingang mit Sicherung bzw. PTC und Überspannungsschutz, spannungsfest bis **20 V**; Test mit verschiedenen USB-Netzteilen und mit nassem Ladeport. *(S-K04)* | Muss | I, T |
| REQ-SAF-LI-09 | Zelle mit Temperaturen bis 65 °C (RB-03) im Lagerbereich laut Datenblatt; sonst Gegenmassnahme. *(S-W06)* | Muss | A, T |

### 6.3 Knopfzelle [CC] (falls gewählt)

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-SAF-CC-01 | Verpolschutz: falsch eingelegte Zelle (24 h) schadet weder Zelle noch Elektronik. *(S-L04)* | Muss | T |
| REQ-SAF-CC-02 | Sicherer Halter mit korrosionsbeständigen Kontakten; Zelle fällt bei Fall aus 1 m nicht heraus; Kurzschluss im Halter ausgeschlossen. *(S-K03, S-L05)* | Muss | I, T |
| REQ-SAF-CC-03 | **Keine Lademöglichkeit**, auch im Einzelfehlerfall: mindestens zwei unabhängige Rückstrombegrenzungen (z. B. Diode + Widerstand) zu jeder externen Quelle (Programmier-/Testpads, Messpunkt); Rückstrom ≤ Herstellerangabe der Zelle. Programmieren nur ohne eingesetzte Zelle oder mit Adapter ohne Versorgung, konstruktiv sichergestellt. *(S-W01, FE-06)* | Muss | A, T |
| REQ-SAF-CC-04 | **Verschluckschutz:** Batteriefach nur mit Werkzeug (Schraube) oder zwei gleichzeitigen, unabhängigen Handbewegungen zu öffnen (Massstab ANSI/UL 4200A); bleibt nach Falltest aus 1 m geschlossen (**ANNAHME** Fallhöhe). *(S-K03, F-14)* | **Muss** | I, T |

### 6.4 Netz und Daten

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-SAF-NET-01 | Schreibende Aktionen in der PWA (Kalibrierung, Einstellungen, Update, Pairing) erfordern Anmeldung; kein Standardpasswort (beim ersten Start gesetzt), Sperre bei wiederholten Fehlversuchen. *(S-W09)* | Muss | T |
| REQ-SAF-NET-02 | Gateway bietet nur PWA/API (und optional MQTT) an; keine Fernwartungsdienste (z. B. SSH) im Auslieferungszustand; dokumentierte Liste der offenen Ports, geprüft mit Portscan. *(S-W09, S-L06)* | Muss | T |
| REQ-SAF-NET-03 | Integration ins Firmennetz mit minimalem Eingriff dokumentiert (Ports, Geräte, Datenflüsse). | Muss | I |
| REQ-SAF-NET-04 | HTTPS-Lösung darf die Sicherheit der Endgeräte nicht schwächen: keine allgemein gültige eigene Root-CA ohne Namensbeschränkung auf Firmenhandys; privater CA-Schlüssel nie auf dem Gateway. *(S-W09)* | Muss | A, I |

### 6.5 Dokumentation zur Sicherheit

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-SAF-DOC-01 | Anleitung enthält Warnhinweise (Knopfzelle: Verschlucken; Akku: Laden), Lagerung von Ersatzzellen, Entsorgung, Verhalten bei Wasser im Kopf. *(S-K03, S-L03)* | Muss | I |
| REQ-SAF-DOC-02 | Gateway nur mit geprüftem Steckernetzteil (Angabe in Einkaufsliste). *(S-L07)* | Muss | I |

## 7 Gateway

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-GW-01 | Speichert die Historie aller Sensoren dauerhaft: ≥ **2 Jahre** in voller Auflösung (30 Sensoren, Standardintervall) auf dem Gateway (Muss); ältere Daten verdichtet bzw. per Export/Backup (Soll ≥ 5 Jahre). *(F-09)* | Muss/Soll | A, T |
| REQ-GW-02 | Stellt die PWA und eine dokumentierte API im LAN bereit. | Muss | T |
| REQ-GW-03 | Verwaltet Sensoren (koppeln, benennen, entfernen), verteilt Firmware-Updates, synchronisiert die Zeit der Sensoren. | Muss | T |
| REQ-GW-04 | Leistungsaufnahme ≤ **2 W** im Betrieb. | Soll | T |
| REQ-GW-05 | Startet nach Stromausfall selbständig, ohne Verlust der gespeicherten Historie. | Muss | T |
| REQ-GW-06 | Backup und Wiederherstellung der gesamten Datenbank inkl. Kopplungen (UC-14). *(F-11)* | Muss | T |
| REQ-GW-07 | Lösung (fertiges Board oder eigenes PCB) begründet; Raspberry Pi nur, wenn nötig (RB-05); Variante ohne Firmen-WLAN im Konzept mitbewertet. *(F-18)* | Muss | A |
| REQ-GW-08 | Gehäuse 3D-druckbar, passend zum Sensordesign. | Muss | I |
| REQ-GW-09 | Zeit ohne Internet: Zeitquelle im LAN (z. B. Firmen-NTP-Server, Uhrzeit des Browsers beim Öffnen der PWA) oder interne Uhr. Gangabweichung ≤ **±2 min/Monat** ohne Referenz; Zeit bleibt nach Stromausfall ≥ **24 h** erhalten, sonst werden keine Zeiten an Sensoren verteilt und Werte bis zum Abgleich markiert. Öffentlicher NTP im Internet nur nach Freigabe des Auftraggebers (OP-08). *(F-06, FE-05)* | Muss | A, T |
| REQ-GW-10 | Wechsel von WLAN-Zugangsdaten und IP-Adresse ohne Neukopplung der Sensoren; PWA bleibt über einen festen Namen erreichbar. *(F-11)* | Muss | T |
| REQ-GW-11 | Software-Update von Gateway und PWA ohne Verlust von Daten und Kopplungen. *(F-19)* | Muss | T |

## 8 PWA

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-APP-01 | Name „Tröpfli“; läuft auf iOS Safari, Android Chrome und Desktop (Chrome/Edge; Firefox/Safari Desktop **Soll**), jeweils aktuelle Version. *(F-01)* | Muss | T |
| REQ-APP-02 | Installierbar als PWA; dafür sicherer Kontext (HTTPS) im LAN mit praktikabler, dokumentierter Lösung, die REQ-SAF-NET-04 erfüllt. | Muss | T, I |
| REQ-APP-03 | Übersicht aller Pflanzen: Name, Feuchteindex, Temperatur, Zeit der letzten Messung, Batterie, Signalqualität, Hinweis „Giessen nötig“. | Muss | T |
| REQ-APP-04 | Verlauf/Diagramme pro Pflanze (Tag, Woche, Monat; Jahr **Soll**). *(F-01)* | Muss | T |
| REQ-APP-05 | Pflanzen benennen, Substrattyp und Schwellenwert setzen. | Muss | T |
| REQ-APP-06 | Manuelle Messung auslösen, mit Statusanzeige bis zum Eintreffen. | Muss | T |
| REQ-APP-07 | Zwei-Punkt-Kalibrierung mit geführtem Ablauf. | Muss | T |
| REQ-APP-08 | CSV-Export (alle oder ausgewählte Pflanzen, Zeitraum). | Muss | T |
| REQ-APP-09 | Keine externen Ressourcen zur Laufzeit (Schriften, Bibliotheken lokal). | Muss | I |
| REQ-APP-10 | Hinweis „Giessen nötig“ ist **in der PWA** sichtbar. Push-Benachrichtigungen über Hersteller-Server sind ausgeschlossen (REQ-SYS-01); Alternativen siehe OP-02. | Muss | I |
| REQ-APP-11 | Sprache Deutsch; Bedienung ohne Anleitung für UC-03, UC-04, UC-06, UC-07. | Soll | T |

## 9 Design *(F-12)*

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-DES-01 | Schlicht und modern; **3–4 Designvorschläge** für den Sensorkopf und ein passendes Gateway-Gehäuse als Renderings, vom Auftraggeber verfeinert und freigegeben. | Muss | I |
| REQ-DES-02 | Formsprache darf vom Namen inspiriert sein (z. B. weiche Tropfenform, dezentes Tropfensymbol). | Kann | I |
| REQ-DES-03 | Logo bzw. Wortmarke „Tröpfli“, geeignet für Gehäuse (FDM, ggf. mehrfarbig per AMS), PCB-Silkscreen (JLC-Mindestmasse) und PWA-Icon. | Muss | I |
| REQ-DES-04 | Fotorealistische Renderings des finalen Designs (in der Pflanze, Explosionsansicht, Details). | Muss | I |

## 10 Fertigung und Kosten

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-FAB-01 | Sensor-PCB inklusive kompletter Bestückung bei JLCPCB bestellbar (Gerber, BOM, CPL mit LCSC-Nummern, Rotationen geprüft). | Muss | I |
| REQ-FAB-02 | JLC Basic Parts konsequent bevorzugt; jedes Extended Part begründet. | Muss | I |
| REQ-FAB-03 | Nicht von JLC bestückbare Teile separat gelistet; manueller Schritt pro Sensor ≤ **5 min** (ohne Versiegelung und Aushärtezeit). | Soll | T |
| REQ-FAB-04 | **Stückkosten Sensor ≤ 10 CHF** bei 10–15 Stück, alle Teile inkl. Energiequelle und Gehäusematerial, ohne einmalige Kosten. Überschreitung nur mit ausdrücklicher Freigabe des Auftraggebers nach Darstellung von Mehrkosten und Ursache (Regel 1.2). *(F-01)* | **Muss** | A |
| REQ-FAB-05 | Einmalige Kosten pro Bestellung (Setup, Schablone, Extended-Gebühren, Versand, Zoll/MWST) getrennt ausgewiesen, für Prototyp-Los und Serie. | Muss | A |
| REQ-FAB-06 | Gateway-Kosten separat ausgewiesen. | Muss | A |
| REQ-FAB-07 | Jedes Bauteil: LCSC-Nummer, Herstellerdatenblatt lokal, Eintrag im Bauteilregister, geprüfte Verfügbarkeit. | Muss | I |
| REQ-FAB-08 | Alle Fertigungsdaten per Skript reproduzierbar erzeugt. | Muss | I |
| REQ-FAB-09 | Programmier- und Testzugang (Pads/Testpunkte) vorhanden (siehe REQ-SAF-06). | Muss | I |

## 11 Dokumentation und Lieferumfang

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-DOC-01 | Release-Paket unter `production/rev-X/` gemäss Projektauftrag. | Muss | I |
| REQ-DOC-02 | Anleitungen: Zusammenbau, Versiegelung, Inbetriebnahme, Pairing, Kalibrierung, Fehlersuche, Batteriewechsel bzw. sicherer Umgang mit dem Akku, Sicherheitshinweise nach REQ-SAF-DOC-01. | Muss | I |
| REQ-DOC-03 | Testplan für den Prototyp (Kalibrierung, Langzeit-Wassertest, Laufzeit, Funkreichweite, Batterie, Temperatur, Sicherheit inkl. REQ-SAF-05, -LI-07/08, -CC-03/04). | Muss | I |
| REQ-DOC-04 | Entscheidungsprotokoll und Bauteilregister laufend nachgeführt. | Muss | I |

## 12 Abgrenzungen (nicht im Umfang)

- Kein absoluter volumetrischer Wassergehalt; nur kalibrierter Feuchteindex.
- Kein Einsatz im Freien, keine Hydrokultur ohne Substrat (**ANNAHME**, OP-03).
- Keine Cloud, kein Fernzugriff von ausserhalb des LAN, keine Push-Benachrichtigungen über Hersteller-Server.
- Keine automatische Bewässerung, keine Aktoren.
- Keine Zertifizierung (CE/FCC); nur Funkchips/-module im lizenzfreien 2.4-GHz-Band mit regelkonformer Sendeleistung.
- Mehrere Räume bzw. Gateways: nicht in Rev. A (Architektur nach REQ-SYS-11 offen gehalten).

## 13 Offene Punkte und Annahmen

| Nr. | Punkt | Wer klärt |
|---|---|---|
| OP-01 | Druckermodell bestätigen (P1S?). | Auftraggeber |
| OP-02 | „Giessen nötig“: genügt die Anzeige in der PWA? Oder zusätzlich LED am Sensor (energetisch tragbar, wenn selten, z. B. 1×/min kurz) bzw. Meldung über MQTT/Home Assistant? | Auftraggeber |
| OP-03 | Nur Innenbereich, keine Hydrokultur? | Auftraggeber |
| OP-04 | Kopftemperatur in der Sonne (RB-03, 65 °C) am Muster messen. | Prototyp |
| OP-05 | Kopfgrösse REQ-MECH-02 hängt von der Energiequelle ab. | Phase 2 |
| OP-06 | Lastannahmen REQ-MECH-10 plausibilisieren. | Phase 2/4, Prototyp |
| OP-07 | Firmenhandys: Dürfen Zertifikate/Profile installiert werden? Lösung muss REQ-SAF-NET-04 erfüllen. | Auftraggeber / Phase 2 |
| OP-08 | Darf das Gateway die Uhrzeit von einem öffentlichen Zeitserver (NTP) holen, oder gibt es einen NTP-Server im Firmennetz? | Auftraggeber |
