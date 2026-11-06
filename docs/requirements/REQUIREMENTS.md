# Tröpfli – Anforderungsdokument

| | |
|---|---|
| Dokument | `docs/requirements/REQUIREMENTS.md` |
| Version | 0.1 (Entwurf zur Prüfung) |
| Datum | 2026-11-06 |
| Grundlagen | Projektauftrag (Auftraggeber), `CLIENT_INPUT.md` (Antworten Phase 0), `DECISIONS.md` |
| Status | in Prüfung (Phase 1) |

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
  Zwei-Punkt-Kalibrierung). Kein absoluter volumetrischer Wassergehalt.
- **Messzyklus**: Aufwachen, Messen (Feuchte + Temperatur + Batterie), Speichern, Senden, Schlafen.
- **Verifikation**: A = Analyse/Rechnung, S = Simulation, I = Inspektion (Unterlagen/Muster),
  T = Test am Prototyp.

### 1.2 Kennzeichnungen
**ANNAHME**: noch nicht belegte Annahme, wird in Phase 2 bestätigt oder ersetzt.
**PROTOTYP-PRÜFUNG**: erst am echten Prototyp nachweisbar.

## 2 Rahmenbedingungen

| ID | Rahmenbedingung |
|---|---|
| RB-01 | Einsatz vorerst in **einem Büroraum ca. 10 × 15 m**, innen. |
| RB-02 | Töpfe Ø 15–30 cm, Substrat **Erde und Granulat** (z. B. Blähton-/Mineralgranulat). |
| RB-03 | Umgebung: Raumklima; Sensoren können auf der Fensterbank stehen. **ANNAHME:** Betrieb 5–45 °C (Kopf in der Sonne), Lagerung −10–50 °C. |
| RB-04 | Firmen-WLAN vorhanden, Qualität mässig. Ein Gateway im Firmen-WLAN ist **zulässig**, Lösungen mit wenig Eingriff ins Firmennetz werden bevorzugt. |
| RB-05 | Kein dauerhaft laufender Rechner vorhanden. Ein Raspberry Pi nur, wenn nötig (begründen). |
| RB-06 | Eigengebrauch, keine Zertifizierung. Sicherheit hat trotzdem höchste Priorität. |
| RB-07 | Fertigung der Sensor-Leiterplatte inkl. Bestückung bei JLCPCB; Gehäuse auf Bambu Lab P1S mit AMS (**ANNAHME** Modell, vom Auftraggeber zu bestätigen). |
| RB-08 | Kein Programmieradapter vorhanden; keine Messgeräte-Anschaffung von ca. 100 CHF. Werkstatt sonst gut ausgerüstet. |
| RB-09 | Stückzahlen: Prototyp-Los in kleinster sinnvoller JLC-Menge, danach Serie 10–15 Sensoren. |

## 3 Anwendungsfälle

| ID | Anwendungsfall | Ablauf (Kurzform) |
|---|---|---|
| UC-01 | **Erstinbetriebnahme Gateway** | Gateway einstecken, ins Netz bringen, PWA im Browser öffnen, Vertrauensstellung (HTTPS) einrichten, PWA installieren. |
| UC-02 | **Neuen Sensor koppeln** | Energiequelle einsetzen/laden → Taster drücken → Sensor erscheint in der PWA als `troepfli-XXXX` → Nutzer bestätigt, gibt Pflanzennamen ein. |
| UC-03 | **Automatische Messung** | 4–6× pro Tag misst der Sensor, puffert und überträgt; PWA zeigt aktuellen Wert und Verlauf. |
| UC-04 | **Manuelle Messung** | In der PWA „Jetzt messen“ → Sensor misst und meldet sich innert Frist (REQ-SYS-05). Alternativ kurzer Tastendruck am Sensor. |
| UC-05 | **Kalibrierung** | In der PWA pro Sensor „Trocken“ (Sensor in trockener Erde bzw. an Luft gemäss Anleitung) und „Nass“ (frisch gegossenes Substrat) auslösen; Werte werden gespeichert. |
| UC-06 | **Giessen nötig** | Pro Pflanze Schwellenwert setzen; PWA hebt Pflanzen unter dem Schwellenwert hervor. |
| UC-07 | **Verlauf und Export** | Verlauf je Pflanze ansehen; Daten als CSV exportieren. |
| UC-08 | **Firmware-Update** | Neue Firmware auf das Gateway laden → Gateway verteilt sie an die Sensoren, ohne Öffnen des Gehäuses. |
| UC-09 | **Energiequelle wechseln/laden** | PWA warnt bei tiefem Stand; Nutzer wechselt die Batterie bzw. lädt den Akku gemäss Anleitung. |
| UC-10 | **Gateway-Ausfall** | Gateway ist Stunden bis Tage aus; Sensoren puffern; nach Rückkehr werden Daten mit korrektem Zeitstempel nachgeliefert. |
| UC-11 | **Sensor entfernen/umziehen** | Sensor in andere Pflanze stecken oder entkoppeln; Historie bleibt der Pflanze bzw. dem Sensor zugeordnet (Nutzer wählt). |
| UC-12 | **Fehlerfall am Sensor** | LED zeigt Fehler (Funk, Messung, Energie); PWA zeigt Detailmeldung. |

## 4 Systemanforderungen

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-SYS-01 | Das System arbeitet ohne Internetverbindung vollständig. Kein Datenverkehr zu Servern ausserhalb des LAN (inkl. CDNs, Zeitserver ausserhalb des LAN sind **Kann** nur für das Gateway und abschaltbar). | Muss | T, I |
| REQ-SYS-02 | Ein Gateway versorgt mindestens **15 Sensoren** im Raum nach RB-01. | Muss | A, T |
| REQ-SYS-03 | Kapazität: bis **30 Sensoren** pro Gateway ohne Hardwareänderung. | Soll | A |
| REQ-SYS-04 | Automatische Messungen: Intervall einstellbar, Standard **4×/Tag**, Bereich mindestens 1–24×/Tag. | Muss | T |
| REQ-SYS-05 | Manuelle Messung aus der PWA: Wert in der PWA nach **≤ 5 min** (Muss), Ziel **≤ 1 min** (Soll). Das Energiebudget weist beide Varianten aus. | Muss/Soll | A, T |
| REQ-SYS-06 | Zwei-Wege-Kommunikation Gateway → Sensor für: manuelle Messung, Kalibrierung, Einstellungen (Intervall, Schwellen-/LED-Optionen), Zeit, Firmware-Update. | Muss | T |
| REQ-SYS-07 | Zeitstempel der Messwerte: Abweichung ≤ **±2 min** gegenüber Gateway-Zeit, auch nach 7 Tagen ohne Gateway. | Muss | A, T |
| REQ-SYS-08 | Eindeutige Sensor-ID, sichtbar als `troepfli-XXXX` (XXXX aus Chip-ID, hexadezimal). | Muss | I |
| REQ-SYS-09 | Datenformat (Funk und Export) versioniert und dokumentiert. | Muss | I |
| REQ-SYS-10 | Anbindung an MQTT / Home Assistant (Auto-Discovery). | Kann | T |

## 5 Sensor

### 5.1 Messung Feuchte

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-MES-01 | Kapazitives Messprinzip; die Sonde ist Teil der Hauptleiterplatte (ein durchgehendes PCB). | Muss | I |
| REQ-MES-02 | Ausgabe als Feuchteindex 0–100 % nach Zwei-Punkt-Kalibrierung, zusätzlich Rohwert. | Muss | T |
| REQ-MES-03 | Auflösung ≤ **1 %** des kalibrierten Bereichs. | Muss | A, T |
| REQ-MES-04 | Wiederholbarkeit bei unverändertem Substrat und Temperatur: Standardabweichung ≤ **1 %** über 10 Messungen. | Muss | T |
| REQ-MES-05 | Temperatureinfluss nach Kompensation ≤ **0.3 %/K** im Bereich 10–35 °C (Feuchteindex bei konstantem Wassergehalt). | Soll | T, PROTOTYP-PRÜFUNG |
| REQ-MES-06 | Langzeitdrift (Sonde dauerhaft in nassem Substrat, konstanter Wassergehalt) ≤ **5 %** in 6 Monaten; Hochrechnung aus beschleunigtem Wassertest. | Soll | T, PROTOTYP-PRÜFUNG |
| REQ-MES-07 | Exemplarstreuung vor Kalibrierung: Rohwerte so, dass eine gemeinsame Werks-Startkalibrierung ±15 % genügt (nutzbar ohne Einzelkalibrierung). | Soll | T |
| REQ-MES-08 | Messvolumen: Feuchte wird über mindestens die unteren **70 mm** der Sonde erfasst (nicht nur an der Spitze oder an der Oberfläche). | Soll | S |
| REQ-MES-09 | Unterschiedliche Kalibrierwerte für Erde und Granulat werden pro Sensor gespeichert; Substrattyp ist pro Pflanze wählbar. | Muss | T |
| REQ-MES-10 | Mittelung mehrerer Einzelmessungen pro Messzyklus; Ausreisser werden erkannt. | Muss | I, T |

### 5.2 Messung Temperatur

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-TMP-01 | Bodentemperatur, gemessen nahe der Dichtlinie unter der Versiegelung, Genauigkeit ≤ **±1.0 °C** (10–35 °C). | Muss | A, T |
| REQ-TMP-02 | Temperatur wird für die Feuchtekompensation verwendet. | Muss | I |
| REQ-TMP-03 | Lufttemperatur im Kopf. | Kann | – |
| REQ-TMP-04 | Weitere Sensoren (Luftfeuchte, Licht) nur, wenn Mehrkosten ≤ 0.50 CHF/Sensor und Laufzeitverlust ≤ 5 %. | Kann | A |

### 5.3 Logging

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-LOG-01 | Sensor puffert mindestens **14 Tage** Messwerte (bei 6 Messungen/Tag) mit Zeitstempel, wenn das Gateway nicht erreichbar ist. | Muss | A, T |
| REQ-LOG-02 | Nachlieferung gepufferter Werte ohne Duplikate und ohne Verlust, sobald das Gateway erreichbar ist. | Muss | T |
| REQ-LOG-03 | Pufferinhalt übersteht einen Energiequellenwechsel. | Soll | T |

### 5.4 Energie und Laufzeit

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-ENE-01 | Variantenvergleich mindestens (a) LiPo mit USB-C-Laden und vollständiger Schutzschaltung, (b) Knopfzelle (z. B. CR2032/CR2450) mit sehr sparsamem Funkchip. Bewertet werden Sicherheit, Laufzeit, Kopfgrösse, Kosten, Aufwand. | Muss | A |
| REQ-ENE-02 | **Primärbatterie:** Laufzeit ≥ **12 Monate** im Standardprofil (REQ-ENE-04), rechnerisch mit pessimistischen Annahmen (Pulslast, Temperatur, Selbstentladung, Bauteilstreuung). | Muss | A, PROTOTYP-PRÜFUNG |
| REQ-ENE-03 | **Akku:** Laufzeit pro Ladung ≥ **3 Monate** im Standardprofil. | Muss | A, PROTOTYP-PRÜFUNG |
| REQ-ENE-04 | **Standardprofil** für alle Laufzeitangaben: 6 Messungen/Tag mit Übertragung, 2 manuelle Messungen/Tag, Erreichbarkeit nach REQ-SYS-05 (Muss-Wert), LED gemäss Standardmuster, 1 Firmware-Update/Jahr, 20 °C. | Muss | A |
| REQ-ENE-05 | Batteriestand wird gemessen und in der PWA angezeigt; Warnung, wenn die geschätzte Restlaufzeit < **30 Tage** ist. | Muss | T |
| REQ-ENE-06 | Spannungseinbrüche beim Senden (Knopfzelle) führen nicht zu Resets oder Datenverlust bis zum Ende der nutzbaren Kapazität. | Muss | S, T |
| REQ-ENE-07 | Der Energieverbrauch kann am Prototyp mit Werkstattmitteln (Shunt + Oszilloskop/Multimeter) gemessen werden; dafür ist ein Messpunkt bzw. Brückenpunkt im Versorgungspfad vorgesehen. | Muss | I |

### 5.5 Funk

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-RF-01 | Kein WLAN im Sensor, sofern die Konzeptphase nicht zeigt, dass WLAN die Laufzeit- und Kostenziele erfüllt (wird in Phase 2 verglichen). | Soll | A |
| REQ-RF-02 | Reichweite: Paketzustellung ≥ **99 %** (inkl. Wiederholungen) zwischen jedem Sensorplatz im Raum (RB-01, max. Distanz ca. 18 m) und dem Gateway, Sensor im Topf, Personen im Raum. | Muss | A, T |
| REQ-RF-03 | Linkreserve: gemessene Empfangsstärke am schlechtesten Platz ≥ **10 dB** über der Empfängerempfindlichkeit. | Soll | T |
| REQ-RF-04 | Antenne am oberen Ende des Kopfes, möglichst weit von der Erde entfernt, mit Keepout gemäss Hersteller. | Muss | I |
| REQ-RF-05 | Pairing nur nach bewusster Handlung (Tastendruck am Sensor **und** Bestätigung in der PWA). Fremde Geräte werden nicht automatisch übernommen. | Muss | T |
| REQ-RF-06 | Konfigurationsbefehle und Firmware-Updates werden nur von gekoppeltem Gateway angenommen (Authentifizierung). | Muss | T |

### 5.6 Firmware

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-FW-01 | Deep Sleep zwischen den Aktivitäten. | Muss | I, T |
| REQ-FW-02 | Firmware-Update über Funk (OTA) via Gateway, ohne Öffnen des Gehäuses. | Muss | T |
| REQ-FW-03 | Fehlgeschlagenes oder abgebrochenes Update führt nicht zu einem unbrauchbaren Sensor (Rückfall auf vorherige Version). | Muss | T |
| REQ-FW-04 | Nur signierte Firmware wird installiert. | Soll | T |
| REQ-FW-05 | Ein OTA-Update beansprucht ≤ **2 %** der Batteriekapazität. | Soll | A, T |
| REQ-FW-06 | Erstprogrammierung ohne teuren Adapter: entweder durch JLC vorprogrammierbar, über USB/UART-Bootloader oder mit einem Adapter ≤ **10 CHF** (RB-08). | Muss | I |
| REQ-FW-07 | Watchdog; nach Absturz automatischer Neustart, Fehler wird gemeldet. | Muss | T |
| REQ-FW-08 | Firmware-Version in der PWA sichtbar. | Muss | T |

### 5.7 Bedienelemente

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-UI-01 | Genau eine Status-LED und ein Taster, kein Display. | Muss | I |
| REQ-UI-02 | Blinkmuster für: Messung/Senden bestätigt, Pairing-Modus, verbunden, Batterie tief, Fehler. Muster in Phase 2/4 festgelegt und dokumentiert. | Muss | I |
| REQ-UI-03 | LED-Energie ≤ **5 %** des Tagesenergiebudgets im Standardprofil (z. B. kurze Pulse, nur bei Ereignissen oder Tastendruck). | Muss | A |
| REQ-UI-04 | Tasterfunktionen mindestens: kurz = manuelle Messung + Status, lang (≥ 3 s) = Pairing, sehr lang (≥ 10 s) = Werkseinstellungen. | Muss | T |
| REQ-UI-05 | LED aus normaler Blickrichtung (stehend, schräg von oben) erkennbar; Taster mit einem Finger bedienbar, ohne die Sonde im Topf zu verbiegen. | Muss | T |
| REQ-UI-06 | Fehlbetätigung (z. B. beim Giessen) löst keine Werkseinstellung aus. | Muss | T |

### 5.8 Mechanik und Sonde

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-MECH-01 | Sondenlänge im Boden ca. **100 mm** (±10 mm); Markierung der maximalen Stecktiefe. | Muss | I |
| REQ-MECH-02 | Kopf so klein wie möglich. Zielwerte (**ANNAHME**, in Phase 2 nach Energiequelle bestätigt): Querschnitt ≤ **35 × 20 mm**, Höhe ≤ **45 mm** über der Erde; AAA/AA ausgeschlossen. | Soll | I |
| REQ-MECH-03 | Kein freiliegendes Metall im Sondenbereich. | Muss | I |
| REQ-MECH-04 | Elektroden bevorzugt auf Innenlagen (4 Lagen), Aussenlagen im Sondenbereich ohne Kupfer; Vergleich mit 2 Lagen + Beschichtung dokumentiert. | Muss | A, I |
| REQ-MECH-05 | Keine Vias im nassen Bereich, ausser gefüllt und abgedeckt mit dokumentierter Begründung. | Muss | I |
| REQ-MECH-06 | Kupferabstand zur Platinenkontur im Sondenbereich ≥ **1.0 mm**. | Muss | I (DRC) |
| REQ-MECH-07 | Schnittkanten und Sonde versiegelt (Verfahren in Phase 4 gewählt, mit Anleitung). | Muss | I, T |
| REQ-MECH-08 | Definierte Dichtlinie am Übergang Sonde/Gehäuse; kein Wasser kriecht entlang der Platine ins Gehäuse. | Muss | T |
| REQ-MECH-09 | Masse-/Guard-Struktur zwischen Elektronik und Sonde. | Muss | I |
| REQ-MECH-10 | Sonde übersteht das Einstecken in verdichtete Erde und Granulat: seitliche Last **5 N** an der Spitze und axiale Last **30 N** ohne bleibende Verformung oder Bruch; Sicherheitsfaktor ≥ 2 gegen Biegebruch (FEM + Handrechnung). **ANNAHME** zu den Lastwerten, Plausibilisierung am Prototyp. | Muss | S, T |
| REQ-MECH-11 | Leiterplattendicke festgelegt (1.6 oder 2.0 mm) und begründet. | Muss | A |
| REQ-MECH-12 | Gehäuse FDM-druckbar auf Bambu Lab, Material feuchte- und UV-geeignet (z. B. PETG, ASA; kein PLA). | Muss | I |
| REQ-MECH-13 | Spritzwasserschutz Kopf: kein Wassereintritt bei Giessen von oben (Prüfung: 1 l Wasser aus 20 cm Höhe über den Kopf gegossen, 10 Wiederholungen; Anlehnung an IPX4-Methode). | Muss | T |
| REQ-MECH-14 | Sonde: dauerhaft in nassem Substrat ohne Funktionsverlust; Wassertest **≥ 30 Tage** eingetaucht bis zur Dichtlinie vor Freigabe der Serie. | Muss | T, PROTOTYP-PRÜFUNG |
| REQ-MECH-15 | Batteriefach bzw. Ladeport dicht und ohne Spezialwerkzeug zugänglich; Wechsel/Laden ohne Herausziehen der Leiterplatte aus der Dichtung. | Muss | T |
| REQ-MECH-16 | Revisionsstand auf PCB-Silkscreen; Produktname „Tröpfli“ bzw. Logo auf Gehäuse und Silkscreen. | Muss | I |
| REQ-MECH-17 | Sensor steht stabil; Kopfgewicht kippt die Sonde in lockerem Granulat nicht. | Soll | T |

## 6 Sicherheit

### 6.1 Allgemein

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-SAF-01 | Brandrisiko minimal: Keine Komponente darf im Einzelfehlerfall (Kurzschluss, Verpolung, Wassereintritt, Bauteildefekt) Temperaturen erreichen, die Gehäuse oder Umgebung entzünden. | Muss | A (FMEA), T |
| REQ-SAF-02 | Für die gewählte Energiequelle liegt eine **FMEA-light** vor (Fehler, Ursache, Wirkung, Bewertung, Massnahme, Restrisiko). | Muss | I |
| REQ-SAF-03 | Wenn eine nicht wiederaufladbare Lösung sicherer und günstiger ist und die Laufzeit erfüllt, wird sie empfohlen. | Muss | A |
| REQ-SAF-04 | Der Sicherheits-Agent hat ein Veto; offene kritische Befunde blockieren die Fertigungsfreigabe. | Muss | I |

### 6.2 Lithium-Akku (falls gewählt)

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-SAF-LI-01 | Zelle mit integrierter Schutzschaltung (Überladung, Tiefentladung, Überstrom/Kurzschluss). | Muss | I |
| REQ-SAF-LI-02 | Laderegler mit Temperaturüberwachung der Zelle (NTC), Laden nur im zulässigen Temperaturbereich der Zelle. | Muss | I, T |
| REQ-SAF-LI-03 | Ladestrom begrenzt auf ≤ 0.5 C der Zelle (bzw. Datenblattwert, falls tiefer). | Muss | I, T |
| REQ-SAF-LI-04 | Verpolschutz, Tiefentladeabschaltung auf der Platine (zusätzlich zur Zelle). | Muss | I, T |
| REQ-SAF-LI-05 | Zelle ohne mechanische Belastung (kein Klemmen, kein Druck durch Gehäuse oder Taster), feuchtigkeitsgeschützt. | Muss | I |
| REQ-SAF-LI-06 | Laden nur mit trockenem Ladeport; Ladeport so angeordnet/abgedeckt, dass Giesswasser ihn nicht erreicht. | Muss | I, T |

### 6.3 Knopfzelle (falls gewählt)

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-SAF-CC-01 | Verpolschutz (falsch eingelegte Zelle schadet weder Zelle noch Elektronik). | Muss | T |
| REQ-SAF-CC-02 | Sicherer Halter, Zelle kann nicht herausfallen; Kurzschluss im Halter ausgeschlossen. | Muss | I |
| REQ-SAF-CC-03 | **Keine Lademöglichkeit**: kein Strompfad in die Zelle, auch nicht über Programmier- oder USB-Anschlüsse. | Muss | A, T |
| REQ-SAF-CC-04 | Verschluckschutz: Batteriefach nur mit Werkzeug oder zwei unabhängigen Handlungen zu öffnen. | Soll | I |

### 6.4 Netz und Daten

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-SAF-NET-01 | Schreibende Aktionen in der PWA (Kalibrierung, Einstellungen, Update, Pairing) erfordern Anmeldung. | Muss | T |
| REQ-SAF-NET-02 | Gateway öffnet keine Verbindungen ins Internet (siehe REQ-SYS-01) und bietet keine Dienste ausser PWA/API (und optional MQTT) an. | Muss | T |
| REQ-SAF-NET-03 | Integration ins Firmennetz mit minimalem Eingriff dokumentiert (welche Ports, welche Geräte). | Muss | I |

## 7 Gateway

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-GW-01 | Empfängt Daten aller gekoppelten Sensoren, speichert die Historie dauerhaft (≥ **5 Jahre** bei 15 Sensoren, 6 Messungen/Tag). | Muss | A, T |
| REQ-GW-02 | Stellt die PWA und eine dokumentierte API im LAN bereit. | Muss | T |
| REQ-GW-03 | Verwaltet Sensoren (koppeln, benennen, entfernen), verteilt Firmware-Updates, synchronisiert die Zeit der Sensoren. | Muss | T |
| REQ-GW-04 | Leistungsaufnahme ≤ **2 W** im Betrieb. | Soll | T |
| REQ-GW-05 | Startet nach Stromausfall selbständig, ohne Datenverlust der bereits gespeicherten Historie. | Muss | T |
| REQ-GW-06 | Datensicherung: Export/Backup der gesamten Datenbank durch den Nutzer. | Muss | T |
| REQ-GW-07 | Lösung (fertiges Board oder eigenes PCB) ist begründet; Raspberry Pi nur, wenn nötig (RB-05). | Muss | A |
| REQ-GW-08 | Gehäuse 3D-druckbar, passend zum Sensordesign. | Muss | I |
| REQ-GW-09 | Zeitquelle ohne Internet: z. B. Uhrzeit aus dem Browser beim Öffnen der PWA, LAN-Zeitserver falls vorhanden, ggf. RTC. Abweichung ≤ ±1 min/Monat. | Muss | A, T |

## 8 PWA

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-APP-01 | Name „Tröpfli“; läuft auf iOS Safari, Android Chrome und Desktop-Browsern (Chrome/Edge/Firefox/Safari, jeweils aktuelle Version). | Muss | T |
| REQ-APP-02 | Installierbar als PWA; dafür sicherer Kontext (HTTPS) im LAN mit praktikabler, dokumentierter Lösung, auch für Firmenhandys bewertet. | Muss | T, I |
| REQ-APP-03 | Übersicht aller Pflanzen: Name, Feuchteindex, Temperatur, Zeit der letzten Messung, Batterie, Signalqualität, Hinweis „Giessen nötig“. | Muss | T |
| REQ-APP-04 | Verlauf/Diagramme pro Pflanze (Tag, Woche, Monat, Jahr). | Muss | T |
| REQ-APP-05 | Pflanzen benennen, Substrattyp und Schwellenwert setzen. | Muss | T |
| REQ-APP-06 | Manuelle Messung auslösen, mit Statusanzeige bis zum Eintreffen. | Muss | T |
| REQ-APP-07 | Zwei-Punkt-Kalibrierung mit geführtem Ablauf. | Muss | T |
| REQ-APP-08 | CSV-Export (alle oder ausgewählte Pflanzen, Zeitraum). | Muss | T |
| REQ-APP-09 | Keine externen Ressourcen zur Laufzeit (Schriften, Bibliotheken lokal). | Muss | I |
| REQ-APP-10 | Hinweis „Giessen nötig“ ist **in der PWA** sichtbar. Push-Benachrichtigungen auf das Handy laufen bei iOS/Android über Hersteller-Server und widersprechen REQ-SYS-01; daher nicht vorgesehen (siehe offene Punkte). | Muss | I |
| REQ-APP-11 | Sprache Deutsch; Bedienung ohne Anleitung für UC-03, UC-04, UC-06, UC-07. | Soll | T |

## 9 Fertigung und Kosten

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-FAB-01 | Sensor-PCB inklusive kompletter Bestückung bei JLCPCB bestellbar (Gerber, BOM, CPL mit LCSC-Nummern, Rotationen geprüft). | Muss | I |
| REQ-FAB-02 | JLC Basic Parts konsequent bevorzugt; jedes Extended Part begründet. | Muss | I |
| REQ-FAB-03 | Nicht von JLC bestückbare Teile (z. B. Batterie, Halter) separat gelistet; manueller Schritt pro Sensor ≤ **5 min** (ohne Versiegelung und Aushärtezeit). | Soll | T |
| REQ-FAB-04 | **Stückkosten Sensor ≤ 10 CHF** bei 10–15 Stück, alle Teile inkl. Energiequelle und Gehäusematerial, ohne einmalige Kosten. Wenn nicht erreichbar: klar ausweisen, was es kostet und warum. | Soll (Ziel, zwingend transparent) | A |
| REQ-FAB-05 | Einmalige Kosten pro Bestellung (Setup, Schablone, Extended-Gebühren, Versand, Zoll/MWST) getrennt ausgewiesen, für Prototyp-Los und Serie. | Muss | A |
| REQ-FAB-06 | Gateway-Kosten separat ausgewiesen. | Muss | A |
| REQ-FAB-07 | Jedes Bauteil: LCSC-Nummer, Herstellerdatenblatt lokal, Eintrag im Bauteilregister, geprüfte Verfügbarkeit. | Muss | I |
| REQ-FAB-08 | Alle Fertigungsdaten per Skript reproduzierbar erzeugt. | Muss | I |
| REQ-FAB-09 | Programmier- und Testzugang (Pads/Testpunkte) vorhanden. | Muss | I |

## 10 Dokumentation und Lieferumfang

| ID | Anforderung | Prio | Verif. |
|---|---|---|---|
| REQ-DOC-01 | Release-Paket unter `production/rev-X/` gemäss Projektauftrag (Fertigungsdaten, Schema/Layout-PDF, STEP, Mechanik, Firmware-Binärdateien, PWA, Anleitungen, Renderings, CHANGELOG). | Muss | I |
| REQ-DOC-02 | Anleitungen: Zusammenbau, Versiegelung, Inbetriebnahme, Pairing, Kalibrierung, Fehlersuche, Batteriewechsel bzw. sicherer Umgang mit dem Akku. | Muss | I |
| REQ-DOC-03 | Testplan für den Prototyp (Kalibrierung, Langzeit-Wassertest, Laufzeit, Funkreichweite, Batterie, Temperatur, Sicherheit). | Muss | I |
| REQ-DOC-04 | Entscheidungsprotokoll und Bauteilregister laufend nachgeführt. | Muss | I |

## 11 Abgrenzungen (nicht im Umfang)

- Kein absoluter volumetrischer Wassergehalt; nur kalibrierter Feuchteindex (REQ-MES-02).
- Kein Einsatz im Freien, keine Hydrokultur ohne Substrat (**ANNAHME**, vom Auftraggeber zu bestätigen).
- Keine Cloud, kein Fernzugriff von ausserhalb des LAN, keine Push-Benachrichtigungen über Hersteller-Server.
- Keine automatische Bewässerung, keine Aktoren.
- Keine Zertifizierung (CE/FCC), keine Funkzulassungsprüfung. Verwendet werden nur Funkmodule bzw.
  -chips im lizenzfreien 2.4-GHz-Band mit regelkonformer Sendeleistung.
- Mehrere Räume bzw. mehrere Gateways: nicht in Rev. A, Architektur soll es aber nicht verbauen.

## 12 Offene Punkte und Annahmen

| Nr. | Punkt | Wer klärt |
|---|---|---|
| OP-01 | Druckermodell bestätigen (P1S?). | Auftraggeber |
| OP-02 | Benachrichtigung „Giessen nötig“: genügt die Anzeige in der PWA? Oder soll zusätzlich die LED am Sensor blinken (kostet Energie) bzw. eine Meldung über MQTT/Home Assistant laufen? | Auftraggeber |
| OP-03 | Nur Innenbereich, keine Hydrokultur? (Abgrenzung) | Auftraggeber |
| OP-04 | Temperaturbereich RB-03 (Fensterbank in der Sonne) bestätigen. | Auftraggeber |
| OP-05 | Kopfgrösse REQ-MECH-02 hängt von der Energiequelle ab. | Phase 2 |
| OP-06 | Lastannahmen Einstecken REQ-MECH-10 plausibilisieren. | Phase 2/4, Prototyp |
| OP-07 | Firmenhandys: Können Root-Zertifikate bzw. Profile installiert werden (wichtig für HTTPS-Lösung)? | Auftraggeber / Phase 2 |
