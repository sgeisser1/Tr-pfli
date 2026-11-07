# fluidi – PWA: Entwicklung und Betrieb

| | |
|---|---|
| Dokument | `docs/manuals/APP.md` |
| Version | 0.3 (PWA final im Stil A „Frost“, Phase 4 Welle 2) |
| Datum | 2026-11-07 |
| Gilt für | `app/` (PWA, öffentliches Dashboard, Mock-Gateway, Tests) |

Die PWA ist die produktive App im Stil A **„Frost“** (D-020): hell/dunkel/automatisch, Tropfen-Charakter überall,
Android/Chrome zuerst (Pixel 10), Desktop gut. Schnittstelle: `docs/interfaces/GATEWAY_API.md`, `app/api/openapi.yaml`.
Inbetriebnahme mit dem echten Gateway: `docs/manuals/GATEWAY_SETUP.md`.

## 1 Aufbau

```
app/
  index.html, manifest.webmanifest, sw.js     App-Shell, Manifest (Frost-Farben, Shortcuts), Service Worker
  dashboard.html                              öffentliches Dashboard (eigener HTTP-Port, nur lesen, D-020)
  css/app.css                                 Frost: Struktur + Frost-Variablen + Produktiv-Ergänzungen
  js/main.js, api.js, dom.js                  Shell/Router/Badge/SW, API (Login, elevate, Jobs, SSE), DOM-Hilfen
  js/art.js, chart.js, comp.js, board.js      eigene SVG-Grafiken (Tropfen-Charakter, Pflanzen), Diagramme, Bausteine,
                                              Dashboard-Darstellung (auch für dashboard.html)
  js/home.js, plant.js, edit.js, room.js      Übersicht, Pflanze (Pflege-/Salzhinweis, „Gedüngt“), Profil (40 Arten), Raumplan
  js/stats.js, settings.js, dash.js           Statistik (inkl. Raumklima), Einstellungen, Dashboard-Modus
  js/login.js, pair.js, calibrate.js          Anmelden/Einrichten, Koppeln mit Farbfolge (SAS), Zwei-Punkt-Kalibrierung
  js/sensors.js, data.js, system.js           Sensoren & Firmware, Export & Backup, System (Zeit, WLAN, Protokoll)
  js/dashboard.js                             Einstieg öffentliches Dashboard (lädt nur GET /api/v1/dashboard)
  js/calc.js                                  Rechenregeln (Feuchteindex …), getestet gegen tests/vectors
  data/species.json                           40 Artenprofile (docs/software/PFLANZENPROFILE.md, D-021)
  icons/, img/logo*.svg                       App-Icon (D-012), Wortmarke v3a hell/dunkel (D-011)
  api/openapi.yaml                            API-Spezifikation (OpenAPI 3.1, normativ für Schemas)
  dev/mock_server.py                          Mock-Gateway mit Testdaten (Entwicklung, Screenshots)
  dev/fluidi_calc.py, fluidi_analysis.py      gemeinsamer Rechenkern (Mock UND echtes Gateway)
  concept/                                    klickbare Stil-Entwürfe (Archiv der Stilwahl)
  vendor/uplot/                               nicht mehr verwendet (Archiv; eigene SVG-Diagramme)
  tests/                                      Unit- und Konformitätstests
```

Kein Build-Schritt, keine npm-Abhängigkeiten, keine externen Ressourcen zur Laufzeit (REQ-APP-09).
Echtes Gateway ohne Hardware (simulierte Sensoren über das echte Funkprotokoll):
`cd firmware/gateway && python3 -m fluidi_gw sim --port 8080` → http://localhost:8080/ (Einrichtungscode steht in der
Konsole), öffentliches Dashboard auf Port 8081 nach Freigabe in den Einstellungen.

## 2 Entwicklung lokal mit Mock

Voraussetzung: Python ≥ 3.10 (getestet 3.12.3), für JS-Tests Node ≥ 18 (getestet 18.19.1).

```bash
python3 app/dev/mock_server.py            # http://localhost:8080 , Passwort: fluidi-demo-2026
python3 app/dev/mock_server.py --fresh    # Ersteinrichtung; Einrichtungscode steht in der Konsole
python3 app/dev/mock_server.py --host 0.0.0.0 --port 8080   # Zugriff vom Handy im selben Netz (nur HTTP!)
```

Im Browser `http://localhost:8080/` öffnen. `localhost` gilt als sicherer Kontext: Service Worker und
„Installieren“ funktionieren in Chrome/Edge auch ohne HTTPS. Vom Handy über die IP des PCs läuft die App, aber
**ohne** Service Worker/Installation (kein sicherer Kontext).

Der Mock liefert 8 Pflanzen mit einem Jahr Verlauf und alle Sonderfälle: Giessen nötig (Ficus), Sensor in Luft
(Zitronenbaum), Batterie tief (Bogenhanf), schwaches Signal (Efeutute), Startkalibrierung + Sonne (Kaktus),
keine neuen Werte (Calathea), Pflanze ohne Sensor (Orchidee). Abläufe mit simulierter Verzögerung: Jetzt messen,
Kalibrierung, Koppeln (Sensor `fluidi-8E05` erscheint nach 3 s), Firmware-Verteilung (Sensor mit 12 % Batterie
lehnt ab), Backup (Mock: unverschlüsselt), CSV.

Testhaken: Hochgeladene Firmware, die mit `BAD` beginnt, gilt als falsch signiert. Mit PyYAML + jsonschema prüft
der Mock eingehende JSON-Bodies gegen `openapi.yaml`.

Wo WSL2 genutzt wird: Windows-Browser erreichen `http://localhost:8080` dank der localhost-Weiterleitung von WSL2
(geprüft mit Edge 2026-11-07).

## 3 Tests

```bash
node --test app/tests/                                       # calc.js (11 Tests)
python3 -m unittest discover -s app/tests -p 'test_*.py'     # Python-Rechenregeln, API-Konformität, PWA-Kriterien
app/dev/screenshots.sh                                       # 14 Screenshots nach app/docs/screenshots/
```

| Test | Inhalt |
|---|---|
| `calc.test.js`, `test_calc.py` | gleiche Vektoren `tests/vectors/calc_vectors.json`: Feuchteindex, Begrenzung, Luft/Überflutung, Temperaturkompensation (Platzhalter), Kalibrierspanne, Rundung, Ausreisser, Signal/Batterie, Auflösung, Tagesmittel über Zeitumstellung |
| `test_mock_api.py` | jede Route der OpenAPI hat eine Mock-Route und umgekehrt; Antworten gegen die Schemas; Login-Pflicht, CSRF, Origin, elevate, Sperre nach 5 Fehlversuchen; Messjob inkl. Timeout; Kalibrierlauf; Koppeln nur im Fenster; Sensorwechsel mit Historie; CSV; Firmware-Signatur und Batterieschwelle; SSE |
| `test_analysis.py` | Giess-Erkennung, Austrocknungsfit, Prognose (Intervall, Sicherheit), Stimmung (`dev/fluidi_analysis.py`) |
| `test_pwa.py` | Manifest (Name, Farben, Icons 192/512/maskable mit echten PNG-Grössen), index.html (Viewport, theme-color, apple-touch-icon), Service Worker (alle Shell-Dateien vorhanden, API ausgenommen), keine externen URLs, keine Inline-Skripte/-Styles, kein `innerHTML`, Prüfsummen uPlot; Entwürfe `app/concept/` ohne externe Ressourcen, Inline-Skripte und `innerHTML`, Importe vorhanden, je Entwurf Dunkelmodus |

Screenshots: Edge headless legt das Layout mindestens 492 px breit an (gemessen); schmale Aufnahmen daher 500 px.
Die SSE-Verbindung öffnet die App erst 2 s nach dem Start, weil eine offene Verbindung `--virtual-time-budget`
sonst blockiert.

## 4 Betrieb über das Gateway

1. **Gateway einrichten** (einmalig, per USB am PC, ARCHITECTURE Kap. 9.1): Einrichtungsprogramm erzeugt
   Zertifikat und WLAN-Zugang und zeigt **Einrichtungscode** und **Fingerabdruck** der fluidi-CA.
2. **CA-Zertifikat auf jedem Gerät installieren** (`fluidi-ca.crt`, Fingerabdruck vergleichen):
   - **iOS/iPadOS (Safari):** Datei öffnen → Einstellungen → „Profil geladen“ → Installieren → danach
     Einstellungen → Allgemein → Info → **Zertifikatsvertrauenseinstellungen** → fluidi-CA einschalten.
     Ohne diesen letzten Schritt vertraut iOS dem Zertifikat nicht.
   - **Android (Chrome):** Einstellungen → Sicherheit → Verschlüsselung & Anmeldedaten → Zertifikat
     installieren → **CA-Zertifikat** (Menüpfad je nach Hersteller; Bildschirmsperre nötig).
   - **Windows (Edge/Chrome):** Doppelklick → Zertifikat installieren → Aktueller Benutzer →
     „Vertrauenswürdige Stammzertifizierungsstellen“. **macOS:** Schlüsselbund → „Immer vertrauen“.
     **Firefox:** Einstellungen → Zertifikate → Importieren.
   Die CA ist auf `fluidi.local` beschränkt, ihr privater Schlüssel existiert nicht mehr (REQ-SAF-NET-04).
3. `https://fluidi.local` öffnen → beim ersten Mal **Einrichtungscode + eigenes Passwort** (≥ 10 Zeichen).
4. **App installieren:** iOS: Teilen → „Zum Home-Bildschirm“ (nur Safari). Android: Menü → „App installieren“.
   Desktop: Symbol „App installieren“ in der Adressleiste.
5. Sensor koppeln: Seite **Koppeln** → „Kopplung starten“ → Sensortaste ≥ 3 s (LED gelb) → bestätigen.

Hinweise:
- `fluidi.local` braucht mDNS im WLAN (Android ab ca. Version 12, nicht über VPN). Geht es nicht, siehe
  ARCHITECTURE Kap. 9 / CONCEPTS 5.2 (IT-DNS-Name mit neuer Einmal-CA).
- Updates der PWA kommen mit dem Gateway-Update; der Service Worker lädt die neue Shell beim nächsten Öffnen.
- Offline (Gateway nicht erreichbar) zeigt die App den zuletzt geladenen Stand mit Hinweisbalken.
- Passwort vergessen: Gateway per USB → Einrichtungsprogramm → „Passwort zurücksetzen“ (Daten bleiben).
- Zertifikat läuft nach ≤ 825 Tagen ab; die App warnt 60 Tage vorher (Einstellungen → System).

## 5 Stil-Entwürfe selbst ausprobieren (Software-Konzept)

Die drei klickbaren Entwürfe liegen in `app/concept/` und laufen gegen denselben Mock-Server wie der Prototyp
(gleiche API, realistische Daten: 10 Pflanzen, 1 Jahr Verlauf, Tagebuch, Prognosen, Raumplan). Konzept:
`docs/software/SOFTWARE_CONCEPT.md`, Vergleich: `docs/software/UI_ENTWUERFE.md`.

### 5.1 Am PC

```bash
python3 app/dev/mock_server.py                      # Passwort für Änderungen: fluidi-demo-2026
```

| Entwurf | Adresse |
|---|---|
| A „fluidi Frost“ | http://localhost:8080/concept/?theme=frost |
| B „fluidi Botanik“ | http://localhost:8080/concept/?theme=botanik |
| C „fluidi Stele“ | http://localhost:8080/concept/?theme=stele |

- Zusätzlich `&mode=light`, `&mode=dark` oder `&mode=auto` (folgt dem Gerät). Die Wahl bleibt im Browser gespeichert.
- Oben rechts schaltet ein schwarzer Balken zwischen den Entwürfen und Hell/Dunkel/Automatisch um; dasselbe unter
  **Einstellungen → Darstellung**. `&shot=1` blendet den Balken aus.
- Direkt zu Seiten: `#/` Übersicht, `#/pflanze/1` Detail, `#/pflanze/2/profil` Profil, `#/raum` Raumplan
  (`#/raum?edit=1` Editor), `#/statistik`, `#/einstellungen`, `#/dashboard` (mit `?kiosk=1&theme=…` als Vollbild
  für einen Bildschirm, z. B. `http://localhost:8080/concept/?theme=stele&mode=dark&kiosk=1#/dashboard`).
- Zum Ausprobieren: „Gegossen“ (Karte oder runder Knopf) – nach ~3 s bestätigt der simulierte Sensor den
  Feuchtesprung im Tagebuch; erkannte Giessungen „Stimmt / War nicht gegossen“; Raumplan bearbeiten und sichern;
  „Jetzt messen“; Schalter bei den Benachrichtigungen (Web Push ist absichtlich gesperrt). Beim ersten Ändern fragt
  die App nach dem Passwort.
- Kalibrieren, Koppeln, Firmware und Backup führen auf die Seiten des Funktionsprototyps (`/#/…`).

### 5.2 Vom Handy im WLAN

```bash
python3 app/dev/mock_server.py --host 0.0.0.0 --port 8080
ip -4 addr show eth0 | grep inet        # IP des PCs bzw. der WSL-Instanz
```

Auf dem Handy `http://<IP-des-PCs>:8080/concept/?theme=frost` öffnen (Handy und PC im selben WLAN).

- **WSL2:** Der Dienst läuft in der WSL-VM. Windows leitet nur `localhost` weiter, nicht Anfragen aus dem WLAN.
  Entweder WSL im Netzwerkmodus „mirrored“ betreiben (`.wslconfig`: `networkingMode=mirrored`, dann gilt die
  Windows-IP) oder unter Windows eine Portweiterleitung einrichten (als Administrator):
  `netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=<WSL-IP>`
  und in der Windows-Firewall TCP 8080 für das private Netz erlauben. Danach wieder entfernen
  (`netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0`).
- Über `http://<IP>` ist das **kein sicherer Kontext**: Darstellung und Bedienung funktionieren, „Zum Home-Bildschirm“
  ergibt aber keine echte PWA (kein Service Worker). Für einen Eindruck in Safari genügt das.
- Der Mock ist nur für Entwicklung gedacht (kein TLS, Demo-Passwort). Nach dem Ausprobieren beenden (Ctrl+C).

### 5.3 Screenshots neu erzeugen

```bash
app/dev/concept_shots.sh                 # 84 Bilder nach app/docs/concept/ (3 Entwürfe, Handy im Geräterahmen + Desktop)
python3 app/dev/concept_compose.py       # Vergleichsbilder nach app/docs/concept/vergleich/
python3 scripts/md2pdf.py docs/software/UI_ENTWUERFE.md docs/software/UI_ENTWUERFE.pdf
```

Edge headless legt Seiten mindestens ~500 px breit an. Deshalb lädt eine kleine Rahmenseite die App in einem
430 px breiten iframe (Handy-Rahmen); der Mock läuft dafür mit `--allow-framing` (nur für Screenshots, setzt
`frame-ancestors *`) und `--demo-session`.
