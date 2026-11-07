# fluidi – PWA: Entwicklung und Betrieb

| | |
|---|---|
| Dokument | `docs/manuals/APP.md` |
| Version | 0.1 (Prototyp, Phase 4d) |
| Datum | 2026-11-07 |
| Gilt für | `app/` (PWA, Mock-Gateway, Tests) |

Die PWA ist ein **funktionaler Prototyp**: alle Seiten und Abläufe sind bedienbar, Gestaltung und Funktionsumfang
werden in einem eigenen Software-Konzeptschritt festgelegt. Schnittstelle: `docs/interfaces/GATEWAY_API.md`.

## 1 Aufbau

```
app/
  index.html, manifest.webmanifest, sw.js     App-Shell, Manifest, Service Worker
  css/app.css                                 Gestaltung (nur Systemschriften, keine Inline-Styles)
  js/app.js, api.js, ui.js, chart.js          Router, API-Zugriff, DOM-Hilfen, Diagramm
  js/calc.js                                  Rechenregeln (Feuchteindex, Plausibilität …), getestet
  js/views/*.js                               Seiten
  vendor/uplot/                               uPlot 1.6.32 (MIT), Herkunft/Prüfsummen in SOURCE.md
  icons/, img/logo.svg                        App-Icon (D-012), Wortmarke v3a (D-011)
  api/openapi.yaml                            API-Spezifikation (OpenAPI 3.1)
  dev/mock_server.py, dev/fluidi_calc.py      Mock-Gateway (Python-Standardbibliothek)
  dev/screenshots.sh                          Screenshots mit Edge headless
  tests/                                      Unit- und Konformitätstests
  docs/screenshots/                           erzeugte Screenshots
```

Kein Build-Schritt, keine npm-Abhängigkeiten, keine externen Ressourcen zur Laufzeit (REQ-APP-09).
`app/package.json` dient nur dazu, `node --test` die ES-Module erkennen zu lassen.

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
| `test_pwa.py` | Manifest (Name, Farben, Icons 192/512/maskable mit echten PNG-Grössen), index.html (Viewport, theme-color, apple-touch-icon), Service Worker (alle Shell-Dateien vorhanden, API ausgenommen), keine externen URLs, keine Inline-Skripte/-Styles, kein `innerHTML`, Prüfsummen uPlot |

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
