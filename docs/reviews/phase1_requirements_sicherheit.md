# Prüfbericht Phase 1 – Anforderungen, Fokus Sicherheit

| | |
|---|---|
| Geprüft | `docs/requirements/REQUIREMENTS.md`, Entwurf v0.1 (2026-11-06) |
| Grundlagen | `PROJEKTAUFTRAG.md`, `CLIENT_INPUT.md`, `DECISIONS.md`, `CLAUDE.md` |
| Prüfer | Sicherheits-Agent (mit Veto), frischer Kontext |
| Datum | 2026-11-06 |
| Ergebnis | **4 kritisch (Veto), 9 wichtig, 7 klein.** Freigabe der Anforderungen erst nach Umsetzung der kritischen Befunde oder ausdrücklichem anderem Entscheid des Auftraggebers. |

Stufen: **kritisch** = blockiert die Freigabe (Veto), **wichtig** = muss vor Phase 2 eingearbeitet
oder begründet abgelehnt werden, **klein** = Verbesserung.

## 1 Gesamturteil

Kapitel 6 setzt die Sicherheitsvorgaben des Auftraggebers **inhaltlich vollständig** um (alle
Stichworte aus dem Projektauftrag sind vorhanden). Die Schwächen liegen in der **Prüfbarkeit**:
mehrere Muss-Anforderungen sind nur mit „I“ verifiziert und haben kein Abnahmekriterium
(„feuchtigkeitsgeschützt“, „Temperaturen, die … entzünden“, „zulässiger Temperaturbereich“).
Es fehlen die Gefährdungen **Wasser im Kopf bei eingesetzter Energiequelle**, **Unabhängigkeit der
Schutzfunktionen von der Firmware**, **Fremdladegeräte/nasser Ladeport** sowie **Ersatzzellen,
Lagerung, Entsorgung**. Der Verschluckschutz ist nur „Soll“, die Firmware-Signatur nur „Soll“.

## 2 Abgleich mit den Vorgaben des Auftraggebers (Prüffrage 1)

| Vorgabe Auftraggeber | REQ | umgesetzt | prüfbar | Befund |
|---|---|---|---|---|
| Li: Zelle mit Schutzschaltung | SAF-LI-01 | ja | ja (I: Datenblatt) | – |
| Li: Laderegler mit NTC | SAF-LI-02 | ja | **nein** (kein Temperaturfenster, keine thermische Kopplung NTC–Zelle) | S-W02 |
| Li: Strombegrenzung | SAF-LI-03 | ja | ja | S-W03 (Ergänzungen) |
| Li: Verpolschutz | SAF-LI-04 | ja | ja | – |
| Li: keine mechanische Belastung | SAF-LI-05 | ja | **nein** (keine Last, kein Quellraum) | S-W04 |
| Li: keine Feuchte an der Zelle | SAF-LI-05/06 | ja | **nein** (kein Test mit eingesetzter Zelle) | **S-K01** |
| Li: Tiefentladeabschaltung | SAF-LI-01/04 | ja | teilweise (Ruhestrom nach Abschaltung fehlt) | S-W03 |
| Knopfzelle: Verpolschutz | SAF-CC-01 | ja | ja (T) | – |
| Knopfzelle: sicherer Halter | SAF-CC-02 | ja | teilweise (Kriterium „kann nicht herausfallen“ ohne Test) | S-K03 |
| Knopfzelle: keine Ladung | SAF-CC-03 | ja | teilweise (Einzelfehler nicht betrachtet, kein Grenzwert) | S-W01 |
| Brandrisiko minimal | SAF-01 | ja | **nein** (kein Messkriterium) | S-W05 |
| FMEA-light | SAF-02 | ja | ja | – |
| Nicht wiederaufladbar empfehlen, wenn sicherer | SAF-03 | ja | ja | – |

## 3 Befunde

### Kritisch (Veto)

**S-K01 · kritisch · REQ-SAF-01, REQ-SAF-LI-05, REQ-SAF-CC-02, REQ-MECH-13/15**
**VETO:** Wasser im Kopf bei eingesetzter Energiequelle ist nicht als prüfbare Anforderung erfasst.
- *Begründung:* Giesswasser über den Kopf, stehendes Wasser im Untersetzer und Kondensat
  (Fensterbank, Tag/Nacht-Zyklen) sind im Einsatz zu erwarten. Bei Li-Akku kann Wasser die Zellanschlüsse
  bzw. die Schutzschaltung (PCM) überbrücken und so den Schutz umgehen (ungeschützte Entladung →
  Erwärmung). Bei Knopfzelle führt Wasser im Halter zu Elektrolyse, Korrosion, Auslaufen und
  Kriechströmen. REQ-MECH-13 prüft nur „kein Wassereintritt“, nicht die **Folgen eines Eintritts**
  (Einzelfehler nach REQ-SAF-01). „Feuchtigkeitsgeschützt“ (SAF-LI-05) ist nicht messbar.
- *Vorschlag (neu REQ-SAF-07, Muss, T):* „Energiequellenfach ist vom übrigen Kopf und vom Sondenübergang
  getrennt abgedichtet. Einzelfehlertest: Kopf mit eingesetzter Energiequelle wird mit Leitungswasser
  geflutet (Fach bzw. Elektronikraum je separat) und 24 h beobachtet: keine Flamme, kein Rauch, kein
  Aufblähen der Zelle, Oberflächentemperatur nach REQ-SAF-01, Stromaufnahme aus der Zelle protokolliert.
  Bei Li-Akku: Zellanschlüsse und PCM vergossen oder beschichtet.“ Zusätzlich in REQ-MECH-13:
  „Prüfung mit eingesetzter Energiequelle; danach Öffnen und Sichtprüfung auf Feuchte/Kondensat.“
- *Aufhebung des Vetos:* Anforderung aufgenommen, Test im Testplan (REQ-DOC-03).

**S-K02 · kritisch · Kapitel 6.2 (fehlt)**
**VETO:** Es fehlt die Anforderung, dass alle Schutzfunktionen **hardwareseitig und unabhängig von der
Firmware** wirken.
- *Begründung:* Firmware ist per OTA veränderbar (REQ-FW-02, Signatur nur „Soll“). Ladeabschaltung,
  NTC-Fenster, Strombegrenzung, Verpol- und Tiefentladeschutz dürfen nicht von Firmware, Konfiguration
  oder einem Absturz abhängen; sonst wird ein Software- oder Angriffsfehler zum Brandrisiko.
- *Vorschlag (neu REQ-SAF-LI-07, Muss, A, T):* „Überladung, Ladetemperaturfenster, Ladestrom,
  Ladezeit-Timer, Tiefentladung und Verpolung werden durch Hardware (Lade-IC, Zellschutz, Bauteilwahl)
  begrenzt. Kein Firmwarezustand (inkl. Absturz, Bootloader, fehlerhafte OTA, MCU ohne Versorgung)
  kann diese Grenzen aufheben. Nachweis: Schaltungsanalyse + Test mit gelöschter/angehaltener MCU.“
  Für Knopfzelle sinngemäss in REQ-SAF-CC-03.

**S-K03 · kritisch · REQ-SAF-CC-04 (Soll), REQ-SAF-CC-02, REQ-DOC-02**
**VETO:** Verschluckschutz ist nur „Soll“ und ohne Prüfkriterium.
- *Begründung:* Verschluckte Lithium-Knopfzellen verursachen schwere Verätzungen; die Folgen sind
  schwerwiegend und irreversibel. Im Büro sind Besucherkinder und Haustiere nicht ausgeschlossen, Ersatzzellen
  liegen in Schubladen. Eine Schraube kostet wenige Rappen, das Kostenargument greift also nicht.
  Als anerkannter Massstab dient ANSI/UL 4200A-2023 (in den USA über 16 CFR 1263 verbindlich, hier nur
  als Anlehnung): Batteriefach nur mit Werkzeug **oder** mit zwei unabhängigen, gleichzeitigen
  Handbewegungen zu öffnen. Bei Schraubdeckeln nennt die Norm u. a. mind. 0.5 Nm und 90° Drehung bzw.
  mind. zwei volle Gewindegänge (Quellen 1–3; genaue Werte am Normtext prüfen, **ANNAHME** bis dahin).
- *Vorschlag:* REQ-SAF-CC-04 auf **Muss** heben: „Batteriefach nur mit Werkzeug (z. B. Schraube, die beim
  Öffnen unverlierbar im Deckel bleibt) oder zwei unabhängigen, gleichzeitigen Handbewegungen zu öffnen,
  in Anlehnung an ANSI/UL 4200A. Prüfung: Fall aus 1 m auf harten Boden (**ANNAHME** Höhe), Zelle bleibt
  eingeschlossen.“ Neu REQ-DOC-05 (Muss): Warnhinweis Verschlucken in Anleitung und als Symbol am
  Gehäuse oder Fach, Lagerung von Ersatzzellen in Originalverpackung ausser Reichweite von Kindern,
  verbrauchte Zellen mit abgeklebten Polen zur Sammelstelle.
- *Aufhebung:* Muss-Anforderung mit Prüfkriterium aufgenommen.

**S-K04 · kritisch · REQ-SAF-LI-06, Kapitel 6.2 (fehlt), RB-03**
**VETO (nur Variante Li-Akku):** Laden am Arbeitsplatz ist nicht gegen Fremdladegeräte, nassen
Ladeport und Laden im Topf bzw. an der Sonne abgesichert.
- *Begründung:* „Laden nur mit trockenem Ladeport“ ist eine Bedienregel und keine technische Massnahme. Der Sensor
  wird direkt aus nasser Erde an ein beliebiges USB-Netzteil gesteckt (auch Schnellladegeräte, defekte
  Billiggeräte). Nasser USB-C-Stecker + 5 V → Elektrolyse und Korrosion an den Kontakten, mögliche
  Erwärmung im Stecker. Lädt der Nutzer im Topf auf der Fensterbank, kann die Zelle ausserhalb des
  Ladefensters liegen. Typische LiPo-Datenblätter erlauben Laden nur bei 0–45 °C, teils 0.5 C nur im
  Bereich 15–45 °C und darunter 0.2 C (Quellen 4–6, zellspezifisch).
- *Vorschlag (neu REQ-SAF-LI-08, Muss, A, T):* „VBUS-Eingang: Sicherung/PTC, Überspannungsschutz,
  dauerhaft spannungsfest bis mindestens 20 V (höchste USB-PD-SPR-Festspannung), CC-Beschaltung nur
  als 5-V-Senke; Ladeport hinter dichtem Deckel oder als Kontaktierung, die im Giessbereich nicht offen
  liegt. Test: Laden an 3 verschiedenen Netzteilen inkl. PC-Port; Port mit Wasser benetzt eingesteckt →
  keine Erwärmung > 10 K am Port (**ANNAHME** Grenzwert), kein Schaden.“ In der Anleitung: Laden nur
  ausserhalb des Topfs, trocken, auf nicht brennbarer Unterlage und nur beaufsichtigt.

### Wichtig

**S-W01 · REQ-SAF-CC-03** – „Kein Strompfad“ ist richtig, deckt aber den Einzelfehler nicht ab
(Diode kurzgeschlossen) und auch nicht das Programmieren mit eingesetzter Zelle (Adapter speist 3.3 V auf VDD →
Rückstrom in die Zelle). Hersteller verlangen Diode + Schutzwiderstand, wobei der Widerstand den Strom
bei Diodenausfall auf den zulässigen Ladestrom begrenzt (Maxell CR2032 nennt ca. 10 mA – aus Sekundärquelle,
**ANNAHME** bis zum lokalen Datenblatt; Quelle 7). *Vorschlag:* „Zwischen jeder externen Spannungsquelle
(Programmierpads, Messpunkt REQ-ENE-07, ggf. USB) und der Zelle liegen zwei unabhängige Massnahmen; auch bei
Ausfall einer davon bleibt der Strom in die Zelle ≤ dem im Datenblatt zulässigen Wert. Programmieranleitung:
Zelle entnehmen.“ Verif. A + T (Rückstrom messen mit überbrückter Diode).

**S-W02 · REQ-SAF-LI-02** – Kein konkretes Fenster, NTC-Lage offen. *Vorschlag:* „Laden nur im
Temperaturfenster des Zelldatenblatts (typ. 0–45 °C, **ANNAHME** bis Zellwahl), NTC thermisch an die Zelle
gekoppelt (nicht nur auf der Leiterplatte), Prüfung mit erwärmter/gekühlter Zelle (Föhn/Kühlschrank) →
Laden stoppt ausserhalb des Fensters.“

**S-W03 · REQ-SAF-LI-03/04** – Ergänzen: Lade-Sicherheitstimer; Ladeschlussspannung gemäss Datenblatt
(Toleranz Lade-IC einrechnen); Strom bei tiefer Temperatur reduziert, falls das Datenblatt es verlangt;
Ruhestrom nach Tiefentladeabschaltung so klein, dass die Zelle ≥ 6 Monate (**ANNAHME**) gelagert werden kann,
ohne unter die Datenblatt-Mindestspannung zu fallen; tief entladene Zelle wird nur per Vorladung (Precharge)
geladen.

**S-W04 · REQ-SAF-LI-05** – Prüfbar machen: „Kraftfluss beim Einstecken (REQ-MECH-10, 30 N axial) und beim
Tastendruck läuft nicht über die Zelle; Quellraum für Pouch-Zelle gemäss Datenblatt (sonst **ANNAHME**
≥ 10 % der Zelldicke); Test REQ-MECH-10 mit eingesetzter Zelle, danach Sichtprüfung.“

**S-W05 · REQ-SAF-01** – „Entzünden“ ist nicht messbar. *Vorschlag:* „Im Einzelfehlerfall (Liste in der
FMEA, mindestens Ausgangskurzschluss, Verpolung, Wasser nach S-K01, Ladeport-Kurzschluss): keine Flamme,
kein Rauch, keine Gehäuseverformung; max. Oberflächentemperatur unter der Wärmeformbeständigkeit des
Gehäusematerials laut Datenblatt.“ Zusätzlich Gehäusematerial: Datenblatt (Wärmeformbeständigkeit, Brennverhalten) unter
`docs/references/`.

**S-W06 · RB-03, OP-04** – Kopftemperatur in praller Sonne ist ungeklärt (dunkles ASA, geschlossen).
Für Li-Akku wäre das Lagern bei > 45–60 °C bereits ein Alterungs- und Aufblährisiko. *Vorschlag:* PROTOTYP-PRÜFUNG
„Kopf-Innentemperatur auf Südfensterbank bei Sonne gemessen“; Anforderung: Innentemperatur ≤
max. Lager-/Betriebstemperatur der Zelle laut Datenblatt, sonst Einschränkung in der Anleitung oder helle
Gehäusefarbe.

**S-W07 · REQ-FW-04** – Signatur nur „Soll“. *Vorschlag:* **Muss**: „Sensor und Gateway installieren nur
Firmware mit gültiger Signatur (Schlüssel nicht im Repo, nicht auf dem Gateway-Dateisystem lesbar);
Rollback auf ältere, signierte Versionen mit bekannter Lücke verhindert (Versionszähler).“

**S-W08 · REQ-RF-05/06** – Authentifizierung unbestimmt. *Vorschlag:* „Pairing mit Schlüsselaustausch
(z. B. BLE LE Secure Connections oder eigener Schlüssel beim Pairing), Befehle mit Integritätsschutz
und Replay-Schutz; ungepaarte Geräte können nur Advertising lesen. Werkseinstellung löscht Schlüssel.“

**S-W09 · REQ-SAF-NET-01, REQ-APP-02** – Anmeldung und HTTPS im Firmennetz konkretisieren:
keine Standardpasswörter (Passwort bei Ersteinrichtung), Passwort-Hash, Sperre nach Fehlversuchen, Sitzung nur über
HTTPS; SSH/Debug-Zugänge im Auslieferungszustand aus. **Wichtig:** Eine eigene Root-CA auf Firmenhandys ist ein
Risiko für den gesamten TLS-Verkehr dieser Geräte, falls ihr Schlüssel abfliesst. *Vorschlag:* CA mit
Name Constraints (nur Gateway-Hostname/-IP) oder nur ein selbstsigniertes Einzelzertifikat;
CA-Privatschlüssel nie auf dem Gateway; Vorgehen mit IT des Auftraggebers abstimmen (OP-07 erweitern).
Gateway-OS (falls Linux/RPi): Sicherheitsupdates offline einspielbar, dokumentiert.

### Klein

| ID | REQ | Kernaussage | Vorschlag |
|---|---|---|---|
| S-L01 | REQ-ENE-07 | Mess-/Brückenpunkt darf keinen Schutz umgehen. | „Messpunkt liegt hinter Verpol-/Zellschutz; Brücke ist im Serienzustand geschlossen und isoliert.“ |
| S-L02 | REQ-FAB-09 | Programmierpads im Kopf zugänglich → Rückspeisepfad. | Verweis auf S-W01; Pads innerhalb des abgedichteten Raums, nicht nach aussen geführt. |
| S-L03 | REQ-DOC-02 | Entsorgung, Lagerung, Transport fehlen. | Kapitel „Sicherer Umgang“: Entsorgung über Sammelstelle (CH), Lagerung Li-Akku bei Teilladung, kühl; aufgeblähte Zelle nicht mehr laden. |
| S-L04 | REQ-SAF-CC-01 | Verpolschutz nicht spezifiziert. | Prüfung ergänzen: Zelle 24 h verkehrt eingelegt → keine Erwärmung, kein Schaden, Zelle danach normal. Halter mit mechanischer Verpolsicherung bevorzugen. |
| S-L05 | REQ-SAF-CC-02 | Korrosion im Halter. | Halterkontakte aus korrosionsbeständigem Material (Datenblatt), Kontaktfläche nicht im Wasserpfad; FMEA-Eintrag. |
| S-L06 | REQ-SAF-NET-02 | „keine Dienste“ – mDNS/DHCP-Client nicht erwähnt. | Explizite Port-/Dienstliste (Muss) und Prüfung per Portscan (`nmap`) als Test. |
| S-L07 | REQ-GW-* | Gateway-Netzteil: Sicherheit (Netzspannung). | Nur geprüftes, CE-gekennzeichnetes Steckernetzteil; kein selbstgebautes Netzteil. |

## 4 Grenzwerte (Prüffrage 3)

- **Ladestrom ≤ 0.5 C:** sinnvoll und branchenüblich als Standardladung; viele Zellen erlauben 0.5 C aber
  nur bei 15–45 °C und verlangen 0.2 C darunter (Quelle 6). Der Zusatz „bzw. Datenblattwert, falls tiefer“
  ist richtig, er muss aber auch die **Temperaturabhängigkeit** abdecken (S-W03). Bei Kleinzellen (z. B. 100 mAh)
  ergibt 0.5 C = 50 mA; der Lade-IC muss so tief einstellbar sein (Phase 2 prüfen).
- **Ladetemperatur:** 0–45 °C typisch (Quellen 4–5), zellspezifisch → **ANNAHME** bis zur Zellwahl.
- **Betrieb 5–45 °C (RB-03):** für die Elektronik unkritisch, für die Li-Lagerung im Sonnenlicht ungeklärt (S-W06).
- **Spritzwassertest REQ-MECH-13:** praxisnah, aber ohne Energiequelle und ohne Nachkontrolle (S-K01).
- **Rückstrom Knopfzelle:** Grenzwert aus Herstellerdatenblatt übernehmen, nicht pauschal (S-W01).

## 5 Netz/OTA (Prüffrage 4)

Grundrichtung (strikt lokal, Anmeldung für Schreibaktionen, Pairing mit zwei Handlungen) ist angemessen.
Mängel: Signatur nur Soll (S-W07), Authentifizierung Sensor–Gateway unbestimmt (S-W08), Root-CA-Risiko
für Firmenhandys und fehlende Härtung des Gateways (S-W09). Kein Veto, da keine Netzfunktion die
elektrische Sicherheit beeinflussen darf – **sofern S-K02 umgesetzt ist**.

## 6 Für Testplan (REQ-DOC-03) vorzumerken

Flutungstest mit Zelle (S-K01), Schutzfunktion bei angehaltener MCU (S-K02), Falltest Batteriefach (S-K03),
nasser Ladeport und Fremdnetzteile (S-K04), Rückstrom bei überbrückter Diode und angeschlossenem Programmieradapter
(S-W01), NTC-Fenster (S-W02), Einstecklast mit Zelle (S-W04), Kopftemperatur an der Sonne (S-W06), Portscan
Gateway (S-L06), Verpolung 24 h (S-L04).

## 7 Quellen

1. Intertek, „US CPSC approve safety standard for button cell or coin batteries“ (2023):
   https://www.intertek.com/products-retail/insight-bulletins/2023/us-cpsc-approve-safety-standard-for-button-cell-or-coin-batteries/
2. ComplianceGate, „Part 1263 – Safety Standard for Button Cell Batteries“:
   https://www.compliancegate.com/part-1263-safety-standard-for-button-cell-batteries-guide/
3. Intertek, UL 4200A Standards Update Notice:
   https://intertek.com/siteassets/resources/sun/2024/ul-4200a-sun-rev-8-15-2023-and-8-30-2023-ed-3-19-2025.pdf
4. Vernier, LiPo 300 mAh Spezifikation (Laden 0–45 °C): https://www.vernier.com/til/4089
5. DNK Power, DNK485643 LiPo Specification:
   https://www.dnkpower.com/wp-content/uploads/2023/11/DNK485643-3.7V-1300mAh-Lipo-Battery-Specification.pdf
6. LP503035 Datenblatt (0.5 C bei 15–45 °C, darunter 0.2 C): https://mm.digikey.com/Volume0/opasdata/d220001/medias/docus/7155/LP503035.pdf
7. Hinweis auf Maxell-CR2032-Datenblatt (Diode + Schutzwiderstand, zulässiger Ladestrom) via Websuche;
   **Originaldatenblatt in Phase 2 lokal ablegen und zitieren**, Wert bis dahin ANNAHME.

Hinweis: IEC 62133-2 und IEC 60086-4 waren nicht frei verfügbar und wurden nicht im Wortlaut geprüft.
Grenzwerte aus diesen Normen sind nicht übernommen. Massgeblich sind die Zell-Datenblätter, die in Phase 2
lokal abgelegt werden.
