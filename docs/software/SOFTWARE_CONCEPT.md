# fluidi – Software-Konzept (App und Gateway-Dienste)

| | |
|---|---|
| Dokument | `docs/software/SOFTWARE_CONCEPT.md` |
| Version | 0.1 (Entwurf zur Freigabe) |
| Datum | 2026-11-07 |
| Autor | Software-Agent |
| Grundlagen | `REQUIREMENTS.md` Kap. 3, 4, 6.4, 7, 8 · `DECISIONS.md` D-010, D-011, **D-014** (Gateway Pi Zero 2 W), **D-015** (Software-Wünsche) · `docs/design/P3_FLUIDI.md` · `firmware/gateway/ARCHITECTURE.md` · `docs/interfaces/GATEWAY_API.md` · `firmware/PROTOCOL.md` |
| Klickbare Entwürfe | `app/concept/` (drei Stile, gleiche Struktur), Vergleich `docs/software/UI_ENTWUERFE.md` |
| Referenzcode | Prognose/Erkennung `app/dev/fluidi_analysis.py` (Tests `app/tests/test_analysis.py`), Mock-API `app/dev/mock_server.py`, API `app/api/openapi.yaml` |
| Status | **zur Freigabe**; enthält Entscheidungsfragen (Kap. 17), u. a. zu Benachrichtigungen (berührt REQ-SYS-01/REQ-APP-10) |

Kennzeichnungen wie im Projekt: **ANNAHME** (nicht belegt), **PROTOTYP-PRÜFUNG** (erst am Muster prüfbar).

---

## 1 Ziel

Dieser Schritt legt **Funktionsumfang, Bedienung und Aussehen** der App fest – wie Phase 3 für die Hardware. Der
Funktionsprototyp aus Phase 4d (`app/`, alle Muss-Abläufe aus REQ-APP-xx) bleibt die technische Basis; neu kommen die
Wünsche aus D-015 dazu: Ein-Blick-Übersicht mit Tropfen-Ampel und Stimmung, Prognose, Giess-Tagebuch mit automatischer
Erkennung, Pflanzenprofile, Raumplan, Dashboard (auch für Kollegen), Statistik inkl. Energie, verspielte Elemente,
Datenzugang für ML. Strikt lokal (REQ-SYS-01); wo ein Wunsch damit kollidiert (Push-Mitteilungen), wird das offen
bewertet und dem Auftraggeber zur Entscheidung vorgelegt (Kap. 12).

## 2 Rollen und Personas

| Rolle | Wer | Gerät | Rechte | Ziel |
|---|---|---|---|---|
| **Admin** | Auftraggeber, einziger Admin (D-015) | iPhone (PWA auf dem Home-Bildschirm), PC | alles; schreibende Aktionen mit Anmeldung, heikle mit Passwort-Bestätigung (REQ-SAF-NET-01, API Kap. 3.3) | „Ein Blick genügt“, rechtzeitig giessen, Daten auswerten |
| **Mitleser im LAN** | Admin auf einem fremden Gerät, Kollegen mit Link | Browser | nur lesen, wenn `public_read` an (API Kap. 3.4) | Zustand ansehen |
| **Kollegen (öffentliche Ansicht)** | Büro-Kollegen | Browser, Büro-Bildschirm | **nur** das Dashboard auf eigenem Port, ohne Login, abschaltbar; keine Sensor-IDs, keine Einstellungen | „Muss ich giessen?“ ohne App |
| **Bildschirm (Kiosk)** | TV/Monitor im Büro | Browser im Vollbild | wie Kollegen | dauernd sichtbarer Zustand |
| **Analyst** | Auftraggeber am PC (später ML) | Skript, Excel, Python | lesen über Export/Lese-API | Rohdaten, Ereignisse, Kalibrierung |

Es gibt bewusst **keine Benutzerverwaltung** (ein Admin, ein Passwort). Mehrbenutzer ist „später“ (Kap. 4).

## 3 Kern-Anwendungsfälle

| ID | Anwendungsfall | Ablauf (kurz) | Bezug |
|---|---|---|---|
| K-01 | **Ein Blick** | App öffnen → Kopfzeile sagt „1 Pflanze hat Durst“, Tropfen-Charakter zeigt Gesamtstimmung, Karten sortiert: durstig → Hinweise → ok | REQ-APP-03, D-015 |
| K-02 | **Kritisches erfahren** | Hinweisliste in der App, Zähler am App-Symbol, LED am Sensor, Dashboard; optional E-Mail/ntfy/Web Push (Kap. 12) | REQ-APP-10, D-015 |
| K-03 | **Giessen eintragen** | Knopf „Gegossen“ (Karte, Detail oder schwebender Knopf) → Tagebuch; Gateway fordert eine Messung an und bestätigt den Feuchtesprung | D-015 |
| K-04 | **Giessen erkennen** | Sprung ≥ 15 %-Punkte → Eintrag „vom Sensor erkannt“, Nutzer bestätigt oder verwirft | D-015 |
| K-05 | **Nächstes Giessen planen** | Karte „giessen in ~3 Tagen (2–4)“, Detail mit Wochentag, Sicherheit und Erklärung | D-015 |
| K-06 | **Pflanze mit Profil anlegen** | Art wählen (Bild + Startwert), Name, Standort, Substrat, Topf, Zielbereich | REQ-APP-05, D-015 |
| K-07 | **Raumplan pflegen** | Raum, Fenster/Türen, Sonnenseite, Pflanzen ziehen | D-015 |
| K-08 | **Dashboard zeigen** | Bildschirm öffnet `https://fluidi.local:8443/` bzw. App → Dashboard | D-015 |
| K-09 | **Akku und Funk prüfen** | Statistik: Restlaufzeit, Spannungsverlauf, Energieanteile, Signal | REQ-ENE-05, D-015 |
| K-10 | **Daten auswerten** | CSV/Parquet, Lese-API, SQLite-Kopie | REQ-APP-08, D-015 |

Die bestehenden UC-01…UC-16 (REQUIREMENTS Kap. 3) bleiben gültig und sind im Prototyp umgesetzt.

## 4 Funktionsliste mit Priorität

**Rev A Muss** = erste ausgelieferte Gateway-Software; **Rev A Soll** = wenn Aufwand im Rahmen; **später** = nach Rev A.
Spalte „Entwurf“: im klickbaren Entwurf bedienbar (✔), angedeutet (◐), nur im Funktionsprototyp `app/` (P).

| Nr. | Funktion | Prio | Quelle | Entwurf |
|---|---|---|---|---|
| F-01 | Übersicht: Karten mit Tropfen-Ampel (Farbe = LED-Farbe D-010, Füllstand = Feuchte), Stimmung, Wert, Zustand als Text + Symbol, Zielbereich, Prognose, Temperatur, Zeit, Batterie, Signal | Rev A Muss | REQ-APP-03, D-015 | ✔ |
| F-02 | Gesamtzustand („1 Pflanze hat Durst“), Hinweisliste, Filter (Alle/Durst/Hinweise) | Rev A Muss | D-015 | ✔ |
| F-03 | Pflanzen-Detail: Verlauf Tag/Woche/Monat/Jahr mit Zielband, Giessschwelle, Giess-Markern, Prognose | Rev A Muss | REQ-APP-04 | ✔ |
| F-04 | Jetzt messen (Job mit Status) | Rev A Muss | REQ-APP-06 | ✔ |
| F-05 | Zwei-Punkt-Kalibrierung geführt | Rev A Muss | REQ-APP-07 | P |
| F-06 | Giess-Tagebuch: Knopf „Gegossen“, Einträge Düngen/Umtopfen/Notiz | Rev A Muss | D-015 | ✔ |
| F-07 | Automatische Giess-Erkennung am Feuchtesprung, bestätigen/verwerfen | Rev A Muss | D-015 | ✔ |
| F-08 | Prognose „nächstes Giessen“ mit Intervall, Sicherheit und Erklärung | Rev A Muss | D-015 | ✔ |
| F-09 | Pflanzenprofil: Art (Vorlage), Bild, Name, Standort, Substrat, Topf, Zielbereich (unten = Giessschwelle, oben = zu nass) | Rev A Muss | REQ-APP-05, D-015 | ✔ |
| F-10 | Eingebaute Vorlagen nur als Startwerte, vom Nutzer änderbar (Kap. 9) | Rev A Muss | D-015 | ✔ |
| F-11 | Hell/Dunkel/Automatisch, je Gerät gespeichert | Rev A Muss | D-015 | ✔ |
| F-12 | In-App-Hinweise + Zähler am App-Symbol (Badging API) | Rev A Muss | REQ-APP-10, D-015 | ◐ (Liste ✔, Badge nicht) |
| F-13 | Raumplan ansehen (Zustand pro Pflanze im Raum) | Rev A Muss | D-015 | ✔ |
| F-14 | Raumplan-Editor: Raumgrösse, Fenster/Türen auf Wände tippen, Sonnenseite, Pflanzen ziehen | Rev A Soll | D-015 | ✔ |
| F-15 | Dashboard-Modus (Vollbild, Uhr, Raumplan, Kacheln, Aktualisierung jede Minute) | Rev A Muss | D-015 | ✔ |
| F-16 | Öffentliche Nur-Lese-Ansicht auf eigenem Port, abschaltbar, Namen ausblendbar | Rev A Soll | D-015 | ◐ (Schalter + API) |
| F-17 | Statistik: Giessungen/Woche, Ø Abstand, Zeit im Zielbereich | Rev A Soll | D-015 | ✔ |
| F-18 | Sensoren & Akku: Restlaufzeit, Spannungsverlauf, Energieanteile (Schätzung), Funk | Rev A Muss | REQ-ENE-05, D-015 | ✔ |
| F-19 | CSV-Export (bestehend) + Lese-API dokumentiert | Rev A Muss | REQ-APP-08 | ✔ |
| F-20 | E-Mail über Firmen-SMTP für kritische Hinweise | Rev A Soll (Entscheid F-2) | D-015 | ◐ (Schalter) |
| F-21 | ntfy (LAN-Server) für Android | später (Entscheid F-1) | D-015 | ◐ |
| F-22 | Web Push über Apple/Google | **nur nach Entscheid F-1** (heute ausgeschlossen, REQ-APP-10) | D-015 | ◐ (gesperrt) |
| F-23 | Tageszusammenfassung, Ruhezeiten, Verzögerung „Giessen nötig“ | Rev A Soll | D-015 | ◐ |
| F-24 | Foto der Pflanze (eigene Aufnahme statt Illustration) | später | D-015 | – |
| F-25 | Parquet-Export, API-Token für Skripte (nur lesen) | später | D-015 | – |
| F-26 | Mehrere Räume/Etagen im Plan | später | REQ-SYS-11 | – |
| F-27 | MQTT/Home Assistant | Kann (bestehend REQ-SYS-10) | – | P |
| F-28 | Koppeln, Firmware, Backup, WLAN, Zeit (Funktionsprototyp) | Rev A Muss | REQ-GW-03/06/10 | P |
| F-29 | Lernende Prognose mit Temperatur/Jahreszeit (ML) | später | D-015 | – |
| F-30 | Mehrere Benutzer/Rollen | später | – | – |

## 5 Informationsarchitektur

```
fluidi
├─ Pflanzen (Übersicht)          Gesamtzustand · Hinweise · Karten
│   ├─ Pflanze                   Zustand · Prognose · Verlauf · Tagebuch · Profil · Sensor
│   │   ├─ Profil bearbeiten     Art · Name · Standort · Substrat · Topf · Zielbereich
│   │   └─ Kalibrieren           (geführt, Prototyp-Seite)
│   └─ Pflanze hinzufügen        Profil (+ Sensor koppeln)
├─ Raum                          Plan · Legende · Bearbeiten
├─ Statistik                     Kennzahlen · Giessungen · Zielbereich · Sensoren & Akku · Daten
├─ Einstellungen                 Darstellung · Benachrichtigungen · Dashboard · Gateway & Sensoren
└─ Dashboard (Vollbild)          eigener Modus, auch öffentlich auf Port 8443
```

| | Handy (< 900 px) | Desktop (≥ 900 px) |
|---|---|---|
| Hauptnavigation | schwebende Leiste unten mit 4 Zielen (Pflanzen, Raum, Statistik, Einstellungen) + runder **„Gegossen“-Knopf** (häufigste Aktion, eine Hand) | Seitenleiste links mit Logo, 4 Zielen, Dashboard-Link, Knopf „Gegossen“ |
| Detailseiten | Zurück-Knopf oben links, Bearbeiten oben rechts | gleich, zweispaltig (links Zustand/Verlauf/Tagebuch, rechts Prognose/Profil/Sensor) |
| Dialoge | Bottom-Sheet von unten | zentrierter Dialog |
| Dashboard | Vollbild ohne Navigation | Vollbild ohne Navigation |

Navigationsregel: höchstens zwei Ebenen unter einem Hauptziel; jede Pflanze ist von Übersicht, Raumplan, Hinweis
und Statistik aus mit einem Tipp erreichbar.

## 6 Bildschirmliste

| Bildschirm | Route (Entwurf) | Zweck | Inhalte |
|---|---|---|---|
| Übersicht | `#/` | K-01 | Begrüssung, Gesamtzustand, Zähler (giessen/Hinweise/zufrieden), Hinweisliste (max. 3–4), Filter, Pflanzenkarten |
| Pflanzen-Detail | `#/pflanze/{id}` | K-03…K-05 | Illustration, Tropfen-Charakter, Wert, Zustand, Zielbereich, Temperatur/Messung/Gegossen, Aktionen (Gegossen, Jetzt messen, Kalibrieren), Prognose, Verlauf, Tagebuch, Profil, Sensor |
| Profil | `#/pflanze/{id}/profil`, `#/neu` | K-06 | Artenwahl mit Bildern, Name, Standort, Substrat, Topf, Zielbereich mit Startwert-Hinweis, Notiz |
| Raumplan | `#/raum` | K-07 | Grundriss mit Wänden, Fenstern, Tür, Sonnenseite, Möbeln, Pflanzen als Tropfen; Legende |
| Raumplan-Editor | `#/raum?edit=1` | K-07 | Werkzeuge (Verschieben, Fenster, Tür, Entfernen), Sonnenseiten, Raummasse, nicht platzierte Pflanzen |
| Dashboard | `#/dashboard` | K-08 | Logo, Titel, Uhr, Zähler, Raumplan, Kacheln je Pflanze, Hinweis „Nur-Lese-Ansicht“ |
| Statistik | `#/statistik` | K-09, K-10 | Kennzahlen, Giessungen pro Woche, Zeit im Zielbereich, Sensoren & Akku (Spannungsverlauf, Energieanteile, Funk), Export |
| Einstellungen | `#/einstellungen` | K-02 | Entwurf/Darstellung, Benachrichtigungskanäle mit ehrlicher Kennzeichnung (lokal / Firmennetz / extern), Regeln, Dashboard-Freigabe, Verwaltung |
| Prototyp-Seiten | `/#/koppeln`, `/#/firmware`, `/#/daten`, `/#/pflanze/{id}/kalibrieren`, `/#/anmelden` | Verwaltung | unverändert aus Phase 4d, werden nach der Stilwahl angeglichen |

## 7 Hauptabläufe

### 7.1 Ersteinrichtung (UC-01, unverändert technisch, neu gestaltet)
1. Gateway per USB am PC einrichten (WLAN, Zertifikat, **Einrichtungscode**; ARCHITECTURE Kap. 9.1).
2. CA auf dem Handy installieren (APP.md Kap. 4) → `https://fluidi.local` → Willkommensseite mit Tropfen-Charakter:
   Einrichtungscode + Passwort → „Zum Home-Bildschirm hinzufügen“ (iOS-Anleitung mit Bildern).
3. Leerer Zustand der Übersicht: „Noch keine Pflanzen – ersten Sensor koppeln“ (ein Knopf).

### 7.2 Pflanze anlegen mit Profil und Sensor koppeln (UC-02, K-06)
1. Übersicht → „+ Pflanze“ **oder** Einstellungen → Sensor koppeln.
2. Koppeln: „Kopplung starten“ → Sensortaste ≥ 3 s (LED gelb) → Kandidat `fluidi-XXXX` erscheint → „Diese Pflanze“.
3. Profil: **Art** antippen (Bild + Startwert), Name, Standort, Substrat (Erde/Granulat), Topf (Ø, Material),
   Zielbereich (Schieber unten/oben, Startwert vorbelegt und als solcher markiert) → Sichern.
4. Neue Sensoren laufen mit Startkalibrierung; die Detailseite bietet „Kalibrieren“ an (Hinweis bis kalibriert).

### 7.3 Giessen eintragen (K-03) und erkennen (K-04)
1. Knopf „Gegossen“ (Karte, Detail oder schwebender Knopf → Pflanzenwahl, durstige oben). Kurze Spritz-Animation,
   Meldung „gegossen eingetragen, der Sensor bestätigt gleich“.
2. Gateway legt den Eintrag an (`POST /plants/{id}/journal`) und setzt für den Sensor eine **Messanforderung**
   (wie „Jetzt messen“). Kommt der Sprung, wird der Eintrag als „Sensor bestätigt +47 %“ markiert.
3. Ohne Knopfdruck erkennt das Gateway den Sprung selbst (Kap. 8.2) → Eintrag „vom Sensor erkannt“. Neue Einträge
   der letzten 14 Tage zeigen „Stimmt / War nicht gegossen“. Verworfene Sprünge zählen nicht für Prognose und Statistik.
4. Nachträglich: Eintrag mit Zeitpunkt (`t`) – z. B. „gestern Abend gegossen“.

### 7.4 Kalibrieren (UC-05)
Unverändert geführter Ablauf des Prototyps (trocken → nass → übernehmen, Ausreisser-Verwurf). Gestaltung nach
Stilwahl: je Schritt eine Illustration (Sensor in trockener Erde / im nassen Substrat), Fortschritt als Tropfen.

### 7.5 Raumplan bearbeiten (K-07)
Raum → „Bearbeiten“ → Werkzeug wählen: **Verschieben** (Pflanze ziehen), **Fenster**/**Tür** (auf eine Wand tippen;
Standardlänge 120/90 cm), **Entfernen** (Pflanze/Öffnung antippen) · Sonnenseiten N/O/S/W an/aus · Raummasse in m ·
„Nicht platziert“ antippen setzt die Pflanze in die Mitte → „Sichern“ (`PUT /roomplan`, optimistische Sperre über
`version`; bei Konflikt Meldung „inzwischen geändert – neu laden“).

### 7.6 Benachrichtigungen einrichten (K-02)
Einstellungen → Benachrichtigungen: Kanäle mit Kennzeichnung **lokal** / **Firmennetz** / **Entscheid offen**,
Regeln (Giessen nötig nach X h, kritisch sofort, Batterie < 30 Tage, Ruhezeit, Tageszusammenfassung). Web Push ist
gesperrt, bis der Auftraggeber entscheidet (Kap. 12; die API antwortet 409).

### 7.7 Dashboard (K-08)
Einstellungen → Dashboard: einschalten, „ohne Anmeldung im Firmennetz“ (eigener Port, Kap. 10), Namen zeigen.
Bildschirm öffnet die Adresse im Vollbild (`?kiosk=1` blendet alles ausser dem Dashboard aus).

## 8 Prognosemodell und Giess-Erkennung

Referenzimplementierung: `app/dev/fluidi_analysis.py` (nur Python-Standardbibliothek, läuft auf dem Pi), Tests
`app/tests/test_analysis.py` (13 Tests: Erkennung, Rauschen, zweistufiger Anstieg, Lücken, Knopf-Zuordnung, Fit,
Prognose gegen bekanntes Modell, Konfidenz, Zeitablauf, Stimmung).

### 8.1 Eingangsdaten
Gültige Feuchtewerte einer Pflanze (Zustände `ok`/`dry`; `air`, `flooded`, `invalid` werden ausgelassen), Zeit in
Unix-Sekunden, über alle Zuordnungsintervalle (UC-11). Der Feuchteindex 0–100 % ist auf die Kalibrierung bezogen
(0 % = trocken kalibriert, GATEWAY_API Kap. 7).

### 8.2 Giess-Erkennung am Feuchtesprung

| Regel | Wert (Startwert, **ANNAHME**, PROTOTYP-PRÜFUNG) | Grund |
|---|---|---|
| Ereignisbeginn | Anstieg ≥ **12 %-Punkte** zwischen zwei aufeinanderfolgenden Werten | Rauschen der Messung ≪ 1 %-Punkt (REQ-MES-03); Temperaturgang klein |
| Ereignis dauert an | solange jeder folgende Wert ≥ 1.5 %-Punkte höher ist, höchstens 12 h | Wasser verteilt sich, zweistufiger Anstieg |
| Ereignis gilt | Gesamtanstieg (Vorher-Wert → Spitze) ≥ **15 %-Punkte** | kleine Nachgiessungen werden nicht erkannt (bewusst) |
| Zeitpunkt | Giessung zwischen dem letzten Wert davor und dem ersten danach; angezeigt wird der erste Wert danach | Auflösung = Messintervall (Standard 4 h) |
| Lücke > 26 h vor dem Sprung | Eintrag mit „Zeit unsicher“ | Gateway-Ausfall, Nachlieferung (UC-10) |
| Knopf „Gegossen“ | gehört zum Sprung, wenn 6 h davor bis 12 h danach | Knopf wird oft vor/nach dem Giessen gedrückt |
| Ausgeschlossen | Sprünge aus `air` heraus (Sensor wieder eingesteckt) | sonst Fehlalarm beim Umtopfen |

### 8.3 Austrocknungsmodell
Zwischen zwei Giessungen trocknet der Boden näherungsweise **exponentiell** gegen den Trockenpunkt:
`m(t) = m0 · exp(−k · t)`, `k` in 1/Tag. Pro Zyklus (ab Spitze + 6 h bis vor die nächste Giessung) wird `ln(m)`
linear über `t` angepasst (kleinste Quadrate, mind. 4 Werte über ≥ 1 Tag, nur `m ≥ 1 %`, Bestimmtheitsmass
R² ≥ 0.5). Erklärbar in einem Satz: „Der Boden verliert zurzeit etwa 14 % seines Restwassers pro Tag.“
(`1 − e^−k`).

**ANNAHME:** Exponentielle Austrocknung ist ein vereinfachtes Modell (Verdunstung ~ verfügbares Wasser); reale Kurven
sind je nach Substrat, Topf, Pflanze und Wetter anders geformt (z. B. anfangs schneller Abfluss). Ob das Modell
genügt, zeigt der Vergleich mit echten Verläufen (**PROTOTYP-PRÜFUNG** mit 3–5 Pflanzen über 4 Wochen;
Kriterium: Prognosefehler ≤ ±1 Tag in 80 % der Fälle). Alternative bei schlechtem Fit: lineare Austrocknung in den
letzten 48 h (gleiche API).

### 8.4 Prognose und Sicherheit
- `k` = **Median** der k-Werte der letzten bis zu 5 abgeschlossenen Zyklen und des laufenden Zyklus.
- Tage bis zur Schwelle: `d = ln(m_jetzt / Schwelle) / k`, abzüglich der seit dem letzten Wert vergangenen Zeit.
- Intervall: mit kleinstem bzw. grösstem k (bei ≥ 5 Zyklen zweitkleinstes/zweitgrösstes) → „giessen in ~5 Tagen (5–6)“.
- **Sicherheit hoch**: ≥ 3 Zyklen, Spannweite k_max/k_min ≤ 1.6, Median-R² ≥ 0.9 · **mittel**: ≥ 2 Zyklen,
  Spannweite ≤ 2.5 · sonst **tief**.
- Zustände: `ok`, `due` (unter Schwelle → „jetzt giessen“), `insufficient_data` („Prognose lernt noch“, z. B. neue
  Pflanze), `not_applicable` (Sensor in Luft, überflutet, keine neuen Werte, ohne Sensor).
- Anzeige: Karte „giessen in ~3 Tagen“, Detail mit Wochentag und Datum, Sicherheits-Pille, aufklappbare Erklärung
  mit Säulen der k-Werte je Zyklus; im Diagramm gestrichelte Kurve bis zur Schwelle und ein Band für das Intervall.
- Nicht berücksichtigt (in der Erklärung genannt): Temperatur, Licht, Jahreszeit. Das ist der Ansatzpunkt für F-29
  (ML, später); Daten dafür werden ab Rev A gesammelt (Kap. 11).

Beispiel aus dem Mock (Monstera, 6 Zyklen): k ≈ 0.14/Tag, R² ≈ 0.997 → „Donnerstag, in ~5 Tagen (5–6), Sicherheit hoch“.

### 8.5 Stimmung des Tropfen-Charakters (verspieltes Element)

| Stimmung | Bedingung | Gesicht | Text (immer daneben) |
|---|---|---|---|
| happy | ok und Prognose > 1 Tag | lachend, rote Bäckchen | zufrieden |
| ok | ok, Prognose ≤ 1 Tag | lächelnd | bald durstig |
| thirsty | unter Schwelle | offener Mund, Schweisstropfen | durstig |
| parched | > 10 %-Punkte unter Schwelle | halb geschlossene Augen, Zunge | sehr durstig |
| drowning | überflutet oder über Obergrenze | grosse Augen, Blasen | zu nass |
| confused | Sensor in Luft, Kalibrierung ungültig, Sensorfehler | ungleiche Augen, Zickzack, „?“ | verwirrt – Sensor prüfen |
| sleepy | keine neuen Werte (> 3 Intervalle) | geschlossene Augen, „z“ | schläft – keine neuen Werte |
| unknown | ohne Sensor | neutral, grau | ohne Sensor |

Die Stimmung berechnet das Gateway (`Plant.mood`), damit App, Dashboard und später MQTT gleich sind. Farbe des Tropfens
= LED-Farbe (D-010): grün ok, **blau giessen**, rot Fehler, grau ohne Werte; Füllstand = Feuchte.

## 9 Pflanzenprofile und Vorlagen

- Profilfelder: Name, **Art** (Vorlage, bestimmt Illustration), Standort, Substrat (Erde/Granulat, bestimmt die
  Kalibrierung), Topf (Ø cm, Material, Abzugsloch), **Zielbereich** (unten = Giessschwelle, oben = „zu nass“),
  Notiz, später Foto.
- **Keine erfundenen Pflegeangaben.** Der Feuchteindex ist sensor- und substratspezifisch (0 % = eigener
  Trockenpunkt, 100 % = eigener Nasspunkt). Werte aus der Pflegeliteratur (z. B. Vol.-% Bodenwasser) lassen sich
  darauf nicht übertragen. Deshalb gibt es nur **drei Startwerte** – „trocken halten“ 10–45 %, „mittel“ 30–70 %,
  „eher feucht“ 45–80 % – deutlich als *Startwert von fluidi (ANNAHME)* markiert (Feld `source: startwert`, Pille
  „Startwert“). Die **Zuordnung der Art zu einer Klasse** (z. B. Kaktus → trocken) ist ebenfalls ANNAHME und vom
  Nutzer zu prüfen.
- 11 Vorlagen mit eigener Illustration: Monstera, Geigenfeige, Bogenhanf, Efeutute, Kaktus, Zitrus, Calathea,
  Orchidee, Glücksfeder, Grünlilie, „Andere Pflanze“. Das Feld `source: quelle` ist vorgesehen, falls später Werte mit
  Literaturangabe dazukommen.
- Lernen statt raten: Nach 3–4 Zyklen kann die App vorschlagen, die Schwelle an die tatsächlichen Giesszeitpunkte
  anzupassen („Du giesst meist bei 26 %“) – Vorschlag, keine Automatik (Rev A Soll).

## 10 Datenmodell-Ergänzungen (Gateway, SQLite)

Bestehend (ARCHITECTURE Kap. 3): `sensor`, `plant`, `assignment`, `calibration`, `reading` (nur Rohwerte), `event_log`.

| Tabelle / Feld | Inhalt | Bemerkung |
|---|---|---|
| `plant` + `species`, `upper_pct`, `location`, `pot_diameter_cm`, `pot_material`, `pot_drainage`, `photo_id` | Profil | `threshold_pct` bleibt die Giessschwelle |
| `species_template` (key, name, latin, water_class, lower, upper, source, note) | Vorlagen | im Software-Abbild, nicht in der DB änderbar; Nutzerwerte stehen in `plant` |
| `journal_entry` (id, plant_id, t, type, source, status, note, amount_ml, created) | Tagebuch | type: watering, fertilizing, repotting, note; source: button, manual |
| `watering_event` (plant_id, t, t_before, before_pct, peak_pct, delta_pct, uncertain_time, status, journal_id) | erkannte Giessungen | beim Ingest inkrementell erkannt (Kap. 16); status: unconfirmed/confirmed/rejected |
| `forecast_cache` (plant_id, computed, k, k_lo, k_hi, cycles, r2, next_water, state) | Prognose | nach jedem neuen Wert der Pflanze neu (≈ 6 ms, Kap. 16) |
| `roomplan` (version, updated, json) | Raumplan | als JSON-Dokument nach Schema `RoomPlan` (wenige kB); Mehrraum vorbereitet |
| `photo` (id, plant_id, t, mime, width, height, bytes) | Fotos (später) | JPEG ≤ 1600 px, ≤ 300 kB, EXIF entfernt; im Backup |
| `alert` (id, kind, level, plant_id, since, cleared, notified_via) | Hinweise | Grundlage für Badge, E-Mail, Tageszusammenfassung; Entprellung |
| `notify_channel`, `notify_rule` | Benachrichtigungen | Geheimnisse (SMTP-Passwort) wie andere Geheimnisse (0600) |
| `settings.dashboard` | Dashboard-Freigabe | `enabled`, `public`, `port`, `title`, `show_names`, `rotate_s` |

API (alle neu in `app/api/openapi.yaml`, im Mock umgesetzt, Konformität in `app/tests/test_mock_api.py`):
`GET /species` · `GET|POST /plants/{id}/journal` · `PATCH|DELETE /journal/{entry_id}` · `GET /plants/{id}/forecast` ·
`GET|PUT /roomplan` · `GET /stats` · `GET /alerts` · `GET /dashboard`; erweitert: `Plant` (species, upper_pct, location,
pot, forecast, last_watered, mood), `Series.events` (watering), `Settings` (notifications, dashboard).

## 11 Datenzugang für Auswertungen und ML

| Weg | Inhalt | Status |
|---|---|---|
| **CSV** `fluidi-csv v1` | Rohwerte inkl. Rohwert, Temperatur, Flags, Quelle; oder Stunden-/Tagesmittel | Rev A Muss (bestehend) |
| **Lese-API** | `series` (raw/hour/day), `journal`, `forecast`, `stats`, `sensors`, `calibration` – JSON, dokumentiert | Rev A Muss |
| **SQLite-Kopie** | vollständige Datenbank (konsistente Kopie per `VACUUM INTO`, nur Lesen) aus dem Backup-Bereich | Rev A Soll |
| **Parquet** | spaltenorientiert für pandas/polars | später; **auf dem PC** aus CSV/SQLite erzeugen (Skript), weil `pyarrow` auf dem Pi Zero 2 W (512 MB) schwer ist (**ANNAHME**) |
| **API-Token** | nur lesen, für Skripte/Notebooks, widerrufbar | später |

Für ML wichtig und deshalb von Anfang an gespeichert: **Rohwerte** (nicht nur Index), Temperatur, Kalibrierhistorie,
Flags (rekonstruierte/unsichere Zeit, nachgeliefert), Giessereignisse mit Quelle und Bestätigung (= Labels),
Profil (Art, Topf, Substrat, Standort), Raumplan (Fensternähe, Sonnenseite), Batteriespannung. Zeit immer UTC.

## 12 Benachrichtigungen ohne Cloud – ehrliche Bewertung

Ausgangslage: REQ-SYS-01 (kein Verkehr ausserhalb des LAN, ausser NTP) und REQ-APP-10 („Push über Hersteller-Server
ausgeschlossen“). D-015 wünscht Benachrichtigungen bei kritischen Zuständen. Kernproblem: **Eine Web-App kann auf
einem gesperrten Handy nur dann eine Mitteilung zeigen, wenn sie per Push geweckt wird – und Push läuft immer über den
Push-Dienst des Browser-Herstellers.** Ohne diesen Dienst erfährt das Handy erst etwas, wenn die App geöffnet wird.

| Kanal | Erreicht gesperrtes iPhone? | Android | Datenfluss / Internet | Aufwand | Bewertung |
|---|---|---|---|---|---|
| In-App-Hinweise + Banner | nein (nur offene App) | nein | strikt lokal | vorhanden | **Rev A** |
| Zähler am App-Symbol (Badging API) | Zahl nur sichtbar mit Mitteilungs-Erlaubnis; wird nur beim Öffnen der App aktualisiert (ohne Push läuft kein Hintergrund-Code) [1] | Chromium: ähnlich | lokal | klein | **Rev A**, Nutzen begrenzt |
| Sensor-LED „giessen“ (REQ-UI-07) | – (an der Pflanze) | – | lokal | vorhanden | **Rev A** |
| Dashboard/Bildschirm im Büro | – | – | lokal | Entwurf vorhanden | **Rev A** |
| E-Mail über Firmen-SMTP | ja (Mail-App) | ja | Gateway → Firmen-Mailserver; ob die Mail das Haus verlässt (z. B. Cloud-Postfach), entscheidet die Firmen-IT | klein (smtplib) | **Rev A Soll**, Entscheid F-2 |
| ntfy, Server im LAN (auch auf dem Pi möglich, ANNAHME) | nur mit Weiterleitung über ntfy.sh: dorthin geht nur die Nachrichten-ID und ein Hash des Themas, der Inhalt holt die App lokal; ohne Weiterleitung Verzögerung „bis Stunden“ [2] | **ja, sofort ohne Google**: Dauerverbindung als Vordergrund-Dienst (dauerhafte Mitteilung) [3] | Android strikt lokal; iOS: Metadaten zu ntfy.sh | mittel (ntfy-App auf jedem Handy) | Option für Android |
| MQTT → Home Assistant | HA-App: „Local Push“ per WebSocket nur in eingetragenen WLANs und nur bei laufender App, sonst über Apple/Google [4] | ähnlich | braucht HA-Server | gross (HA) | nur wenn HA ohnehin vorhanden |
| **Web Push** (Standard, iOS ab 16.4) | **ja** – App muss auf dem Home-Bildschirm sein, Erlaubnis per Tipp, Manifest `standalone` [1] | ja (Chrome über Firebase Cloud Messaging) | Gateway → `*.push.apple.com` bzw. Google; Inhalt **Ende-zu-Ende-verschlüsselt** (RFC 8291: der Push-Dienst kann Nachrichten nicht lesen oder ändern [5]); sichtbar für Apple/Google bleiben Zeitpunkt, Grösse, Empfänger-Endpunkt, IP des Gateways | mittel (VAPID-Schlüssel, Verschlüsselung, Abo-Verwaltung) | zuverlässigste Lösung, **verletzt heute REQ-SYS-01/REQ-APP-10** |
| Periodic Background Sync | nein (nicht in Safari) | nur installierte Chromium-App, Häufigkeit bestimmt der Browser [6] | lokal | klein | ungeeignet |
| Messenger-Bots (Telegram, Signal …) | ja | ja | Cloud, Inhalt beim Anbieter | klein | **abgelehnt** |

Web Push mit eigener CA und `fluidi.local`: Die PWA selbst ist nach Installation der fluidi-CA ein sicherer Kontext
(Service Worker, Installation funktionieren). Apple verlangt für Web Push laut WebKit **kein** Apple-Developer-Konto [1].
Ob Apples Push-Dienst Abos von einer Herkunft mit privater CA bzw. `.local`-Namen annimmt, ist **nicht dokumentiert**
(die alte macOS-Safari-Push-Variante verlangte ein CA-Zertifikat [7], die gilt für Standard-Web-Push aber nicht) →
**PROTOTYP-PRÜFUNG** (iPhone, iOS aktuell, Abo + Testnachricht), bevor F-22 freigegeben wird. Das Gateway bräuchte
ausgehend HTTPS zu `*.push.apple.com` [1] (bzw. Google für Android/Chrome); in der Firewall nur diese Ziele freigeben.

**Empfehlung**
1. **Rev A, strikt lokal:** In-App-Hinweise + Badge + LED + Dashboard (Entwurf zeigt alles) und **Tageszusammenfassung
   beim Öffnen**. Ehrlich kommuniziert: Ohne geöffnete App kommt am iPhone nichts an.
2. **E-Mail über Firmen-SMTP** als erster „Weck“-Kanal, nur kritische Hinweise und höchstens 1 Mail/Tag/Pflanze –
   wenn der Auftraggeber den Firmen-Mailserver als „LAN“ akzeptiert (F-2).
3. **Web Push als bewusste Ausnahme** (wie NTP, OP-08): standardmässig **aus**, einschaltbar nur vom Admin, Inhalt
   minimal („Ficus braucht Wasser“), Ende-zu-Ende-verschlüsselt, Firewall nur zu den Push-Diensten. Dafür müssten
   REQ-SYS-01 und REQ-APP-10 geändert werden → **Entscheidungsfrage F-1**. Bis dahin ist der Schalter gesperrt
   (API 409).
4. ntfy nur, wenn Kollegen mit Android ebenfalls Hinweise wollen (später).

Quellen: [1] WebKit-Blog „Web Push for Web Apps on iOS and iPadOS“ (https://webkit.org/blog/13878/web-push-for-web-apps-on-ios-and-ipados/) ·
[2] ntfy-Dokumentation, Konfiguration „iOS instant notifications“/`upstream-base-url` (https://docs.ntfy.sh/config/) ·
[3] ntfy-Dokumentation „Instant delivery“ (https://docs.ntfy.sh/subscribe/phone/) ·
[4] Home Assistant Companion „Local Push“ (https://companion.home-assistant.io/docs/notifications/notification-local) ·
[5] RFC 8291 „Message Encryption for Web Push“ (https://datatracker.ietf.org/doc/html/rfc8291) ·
[6] MDN „Web Periodic Background Synchronization API“ (https://developer.mozilla.org/en-US/docs/Web/API/Web_Periodic_Background_Synchronization_API) ·
[7] Apple „Configuring Safari Push Notifications“ (Archiv, https://developer.apple.com/library/archive/documentation/NetworkingInternet/Conceptual/NotificationProgrammingGuideForWebsites/PushNotifications/PushNotifications.html) ·
alle abgerufen 2026-11-07.

## 13 Dashboard und öffentliche Ansicht

- Eigener Dienst im Gateway auf **eigenem Port** (Vorschlag 8443), liefert nur die statische Dashboard-Seite und
  `GET /dashboard` – keine anderen Routen, keine Cookies, keine schreibenden Methoden; Rate-Limit. So kann die IT den
  Port getrennt freigeben oder sperren. Abschaltbar (`settings.dashboard.enabled/public`).
- Inhalt ohne Sensor-IDs, Batterie, Systemdaten; Namen ausblendbar (`show_names`).
- **Zertifikat:** Kollegen ohne fluidi-CA sehen bei HTTPS eine Warnung. Optionen: (a) Kollegen-Browser/TV bekommt die CA
  (die CA ist auf `fluidi.local` beschränkt, REQ-SAF-NET-04); (b) Dashboard-Port **nur HTTP**, da nur lesend und nicht
  vertraulich – Risiko: Inhalt im LAN mitlesbar und fälschbar (falsche Pflanzenzustände), kein Zugang zu Admin-Funktionen.
  → Entscheidungsfrage F-3. Empfehlung: (b) für den Büro-Bildschirm, wenn die IT zustimmt; sonst (a).
- Bildschirm: Browser im Vollbild/Kiosk (`?kiosk=1`), Aktualisierung jede Minute, Uhr; Dunkelmodus empfohlen.

## 14 Gestaltung – gemeinsame Regeln für alle Entwürfe

- Apple als Vorbild: Systemschrift (SF Pro auf Apple-Geräten, Segoe UI/Roboto sonst; keine Webfonts, REQ-APP-09),
  grosse Zahlen, ruhige Flächen, Tippziele ≥ 44 px, Bottom-Sheets, Segment-Schalter, Schalter im iOS-Stil.
- Eigene Linien-Symbole (24 px) und eigene Illustrationen (Pflanzen, Tropfen-Charakter) als SVG, Farben aus
  CSS-Variablen → jeder Entwurf färbt dieselben Grafiken anders. Keine fremden Bilder/Assets.
- Hell/Dunkel/Automatisch je Gerät (`prefers-color-scheme` + Schalter), `theme-color` passt sich an.
- Bewegung sparsam (Tropfen blinzelt, wippt; Spritzer beim Giessen), abgeschaltet bei `prefers-reduced-motion`.
- Die drei Entwürfe und ihre Unterschiede: `docs/software/UI_ENTWUERFE.md`.

## 15 Barrierefreiheit

- **Zustand nie nur über Farbe:** immer Symbol + Text („Giessen nötig“ mit Tropfen, „Sensor nicht in der Erde?“ mit
  Warndreieck), zusätzlich Gesichtsausdruck des Tropfens. Rot und Grün haben fast gleiche Helligkeit (1.5:1, Tabelle),
  deshalb tragen Form und Text die Information (wie bei der LED, P3 Kap. V2.3).
- Kontraste (WCAG 2.x, berechnet aus den CSS-Farben; Ziel ≥ 4.5:1 für Text):

| Paar | Farben | Kontrast |
|---|---|---|
| Frost hell Text / Nebentext | `#17222d` / `#66727f` auf Weiss bzw. `#f2f7fb` | 16.1:1 / 4.6:1 |
| Frost Akzent, „giessen“, ok, Alarm (Text) | `#1a73af`, `#1a6fa8`, `#24773f`, `#b93a2f` auf Weiss | 5.1 / 5.4 / 5.5 / 5.7:1 |
| Frost dunkel Text / Nebentext / „giessen“ | auf `#0b1420` | 16.3 / 6.6 / 9.5:1 |
| Botanik hell Text / Nebentext / Akzent | auf Weiss | 16.3 / 5.1 / 6.4:1 |
| Botanik Knopf (Weiss auf Dunkelgrün `#1b4433`) | | 10.9:1 |
| Botanik dunkel Text / Nebentext | auf `#13261a` | 14.3 / 6.3:1 |
| Stele hell Text / Nebentext / „giessen“ | auf `#faf9f6` bzw. `#eeebe5` | 13.2 / 4.6 / 5.6:1 |
| Stele Knopf (Navy `#0f2230` auf Hellblau `#59addd`) | | 6.5:1 |
| Stele dunkel Text / Nebentext | auf `#2a2724` bzw. `#1f1d1b` | 12.8 / 6.2:1 |
| Gesicht auf Tropfen grün / blau / rot | `#18232d` auf LED-Farbe | 5.3 / 6.0 / **3.5**:1 (Grafik, ≥ 3:1 genügt) |

- Diagramme und Grafiken haben `aria-label`; alle Werte stehen zusätzlich als Text. Fokus sichtbar, Tastatur im
  Raumplan (Enter öffnet Pflanze); der Editor (Ziehen) braucht Zeiger – Alternative später: Koordinaten per Formular.
- Schriftgrössen in `rem`, Layout bricht bei 200 % Zoom nicht (Grid mit `minmax(0, 1fr)`).

## 16 Plattform Raspberry Pi Zero 2 W (D-014)

Eckdaten: 4 × Arm Cortex-A53 mit 1 GHz, 512 MB LPDDR2, WLAN 2.4 GHz, Bluetooth 4.2/BLE
(`docs/datasheets/RaspberryPi_Zero2W_ProductBrief_2024-04.pdf`, S. 1–2).

| Thema | Massnahme |
|---|---|
| Rechenlast Prognose/Erkennung | gemessen auf dem Entwicklungs-PC (WSL2): alle 10 Mock-Pflanzen × 1 Jahr (19 700 Werte) **137 ms**, eine Pflanze **6 ms**. Pi Zero 2 W ≈ 10–20 × langsamer (**ANNAHME**, messen) → **inkrementell** je neuem Wert der betroffenen Pflanze (≈ 0.1 s), Ergebnis in `forecast_cache`; nie pro Anfrage über alle Pflanzen |
| Diagramme | Aggregation **serverseitig** (`res=auto` ≤ 800 Punkte, Stunden/Tage nach Ortszeit, GATEWAY_API 7.4); Jahresansicht aus Tagesaggregaten (Tabelle `reading_day`, nachts aktualisiert) |
| Statistik | `GET /stats` aus vorberechneten Tageswerten, Cache 10 min |
| Übersicht | ein Aufruf `GET /plants` enthält Prognose-Zusammenfassung und Stimmung (keine N+1-Abfragen); Dashboard ein Aufruf |
| Abhängigkeiten | nur Python-Standardbibliothek + wenige Pakete (bleak, cryptography); **kein** numpy/pandas/pyarrow auf dem Gateway |
| Netzwerk | gzip für JSON/Static, ETag, Service Worker cached die App-Shell; SSE für Live-Werte (≤ 4 Verbindungen) |
| Bilder | Illustrationen als SVG im Code (wenige kB), Fotos (später) auf 1600 px verkleinert im Browser vor dem Hochladen |
| Speicher | SQLite WAL, Indizes `(sensor, t)`, `(plant, t)` für Tagebuch; Fotos begrenzt (z. B. 50 MB gesamt) |
| Front-End | kein Build-Schritt, ES-Module, keine Laufzeit-CDNs; Entwurf ≈ 175 kB unkomprimiert (JS, CSS, Logos) |

## 17 Entscheidungsfragen an den Auftraggeber

| Nr. | Frage | Optionen | Empfehlung |
|---|---|---|---|
| **F-1** | Push-Mitteilungen aufs gesperrte Handy? Berührt REQ-SYS-01 und REQ-APP-10 | (a) nein, strikt lokal (In-App, Badge, LED, Dashboard) · (b) Web Push als abschaltbare Ausnahme über Apple/Google, Inhalt E2E-verschlüsselt · (c) ntfy im LAN (Android sofort, iOS nur mit ntfy.sh-Weiterleitung) | (a) für Rev A, (b) nach erfolgreicher PROTOTYP-PRÜFUNG mit eigener CA als Option |
| F-2 | Darf das Gateway E-Mails über den Firmen-Mailserver schicken? | ja / nein | ja, nur kritische Hinweise, max. 1/Tag/Pflanze |
| F-3 | Öffentliches Dashboard: HTTP ohne CA oder HTTPS mit CA auf den Bildschirmen? | HTTP-Port nur lesen · HTTPS + CA | HTTP für den Büro-Bildschirm, falls IT einverstanden |
| F-4 | Welcher Stil-Entwurf (A Frost, B Botanik, C Stele) oder Mischung? | siehe UI_ENTWUERFE.md | siehe dort |
| F-5 | Tropfen-Charakter mit Gesicht überall oder nur in Übersicht/Dashboard (sachlicher im Detail)? | überall / reduziert | überall, im Detail kleiner |
| F-6 | Startwerte (3 Klassen) so übernehmen, oder sollen wir für einzelne Arten Literaturwerte mit Quelle suchen (nur qualitativ übertragbar)? | Startwerte / Literatur | Startwerte, nach 3–4 Zyklen Vorschlag aus eigenem Giessverhalten |
| F-7 | Raumplan: ein Raum reicht für Rev A? | ein Raum / mehrere | ein Raum (Datenmodell kann mehrere) |
| F-8 | `public_read` (Lesen ohne Login im LAN, API-2) weiter Werk **ein**? | ein / aus | aus, sobald das öffentliche Dashboard existiert |

## 18 Dateien und Tests

| Datei | Inhalt |
|---|---|
| `app/concept/` | klickbare Entwürfe (index.html, `css/base.css` + `frost.css`/`botanik.css`/`stele.css`, `js/*.js`) |
| `app/dev/fluidi_analysis.py` | Giess-Erkennung, Austrocknungsfit, Prognose, Stimmung |
| `app/dev/mock_server.py` | Mock-Gateway inkl. neuer Endpunkte und realistischer Daten (10 Pflanzen, 1 Jahr, exponentielle Austrocknung, Tagebuch) |
| `app/api/openapi.yaml` | API inkl. Konzept-Erweiterung |
| `app/dev/concept_shots.sh`, `app/dev/concept_compose.py` | Screenshots (Geräterahmen) und Vergleichsbilder → `app/docs/concept/` |
| `app/tests/test_analysis.py`, `app/tests/test_mock_api.py`, `app/tests/test_pwa.py` | Tests (Erkennung/Prognose, API-Konformität neuer Endpunkte, Entwürfe ohne externe Ressourcen) |

```
node --test app/tests/
python3 -m unittest discover -s app/tests -p 'test_*.py'
```
