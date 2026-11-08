# Phase 5 – Testplan-Beitrag Software (Gateway, PWA, Funk)

Stand 2026-11-08 · Ersteller: Software-Agent · Eingang in den Gesamt-Testplan Prototyp.
Alle Punkte sind **PROTOTYP-PRÜFUNG** (am Pi Zero 2 W bzw. an Mustern). Grundlage: `docs/manuals/GATEWAY_SETUP.md`,
`docs/interfaces/GATEWAY_API.md`, `firmware/PROTOCOL.md`, Checkliste `phase5_checkliste_software.md`.

**Ausrüstung:** Pi Zero 2 W + geprüftes Netzteil, SD-Karte, PC mit Repo, Android-Handy (Pixel 10), iPhone (falls
verfügbar), Desktop-Browser, 2–5 Sensormuster (vorher 1 Muster + simulierte Sensoren möglich: `python -m fluidi_gw sim`),
Referenzuhr (Handy mit Netzzeit), Steckdosenleiste mit Schalter, zweiter BLE-Sender (z. B. XIAO nRF52840) für TS-14.
**Protokoll:** je Test Datum, Software-Stand (`GET /system` → `version`), Ergebnis, Abweichung, Foto/Log.

| Nr. | Test | Ablauf | Bestanden wenn | Bezug |
|---|---|---|---|---|
| TS-1 | Installation auf frischem Pi | SD nach GATEWAY_SETUP Kap. 2 schreiben, Repo kopieren (Kap. 3), `sudo ./install_gateway.sh` (Kap. 4), Prüfung Kap. 4.3, `--finish` (Kap. 4.4). Zeit stoppen | Skript ohne Fehler; `systemctl is-active fluidi-gateway` = active; nach `--finish` kein SSH (Port 22 zu); Dauer notiert | REQ-GW-02, REQ-GW-07 |
| TS-2 | `fluidi.local` | Von Android, iPhone, Windows/Linux-PC `https://fluidi.local` aufrufen; zusätzlich im Firmen-WLAN | Name wird aufgelöst auf allen Geräten; sonst Gerät/Netz notieren (W-9, Rückfall IP) | NET-02, W-9 |
| TS-3 | HTTPS-Zertifikat im Browser, PWA | `http://fluidi.local/ca.crt` laden, CA installieren (Kap. 6 Android; iOS: Profil installieren + „Vertrauenseinstellungen“ aktivieren), Fingerabdruck mit App → System vergleichen; App „Zum Startbildschirm“; Flugmodus → App startet (Offline-Shell) | Kein Zertifikatsfehler; Fingerabdruck gleich; Name Constraint: CA gilt nicht für andere Namen (Testseite mit anderem Namen schlägt fehl); PWA installierbar und offline startbar auf iOS Safari, Android Chrome, Desktop | REQ-SAF-NET, A-1…A-3 |
| TS-4 | Einrichtung und Anmeldung | Einrichtungscode, Passwort setzen; 5 falsche Passwörter | Sperre greift (Retry-Zeit angezeigt); Abmelden/Anmelden ok | S-4 |
| TS-5 | Kopplung | App → Sensor koppeln, Taster am Sensor, Farbcode (SAS) vergleichen, Pflanze zuordnen; Gegenprobe: Farben „stimmen nicht“ | Sensor erscheint mit Pflanze; bei Ablehnung kein Schlüssel gespeichert; fremder Sensor ausserhalb des Fensters wird ignoriert | PROTOCOL 4.2, REQ-RF-05 |
| TS-6 | Datenempfang und Nachlieferung | Sensor 24 h laufen lassen; Gateway 6 h ausschalten, wieder ein | Alle Messpunkte ohne Lücke und ohne Duplikat (seq lückenlos, `GET /plants/{id}/history?res=raw`); nachgelieferte Werte Flag 8, Zeit korrekt ±5 s gegen Referenz | PROTOCOL 6, REQ-LOG-01…03 |
| TS-7 | „Jetzt messen“ und Kalibrierung | 20 × „Jetzt messen“; Zwei-Punkt-Kalibrierung trocken/nass nach App-Anleitung | Antwort innerhalb Reaktionszeit + 30 s (95 %); Kalibrierung gespeichert, Feuchte 0/100 % an den Punkten ±3 pp | REQ-SYS-05, UC Kalibrierung |
| TS-8 | Stromausfall Gateway | (a) Strom 1 min weg während einer Datensitzung; (b) 25 h stromlos ohne Internet/NTP (Router-WAN trennen) | (a) Dienst startet selbst, DB intakt (`PRAGMA integrity_check` = ok), keine Lücke nach Nachlieferung; (b) nach Start `time.valid=false`, kein TIME_SET (Sensor-LED-Fenster unverändert), Werte „Zeit unsicher“; nach Öffnen der App durch den Admin `source=browser`, Werte danach ohne Flag 2 und ±5 s korrekt; Handyuhr auf 2001 → abgelehnt (GZ-1…GZ-4 in `phase5_gateway_zeit.md`) | REQ-GW-05, REQ-GW-09 |
| TS-9 | Mehrere Sensoren | 5 Muster (+ bis 30 simulierte) gleichzeitig; 5 gleichzeitige „Jetzt messen“ | Max. 3 Verbindungen gleichzeitig, Rest wartet; keine Zeitüberschreitung als Fehlversuch gezählt; alle Werte da | ARCHITECTURE Kap. 6, PROTOCOL 2.5 |
| TS-10 | CSV-Export | Export einer Pflanze und aller Pflanzen, 30 Tage; in LibreOffice/Excel öffnen | Lokalzeit korrekt (inkl. Sommer-/Winterzeitwechsel, falls im Zeitraum), Dezimaltrennung lesbar, Zeilenzahl = Messwerte, Flags enthalten | UC Export |
| TS-11 | Ports und Dienste | Vom PC `nmap -p- fluidi.local` und `nmap -sU --top-ports 100 fluidi.local` | Nur 80, 443, 5353/udp (und 8080 nur wenn Dashboard eingeschaltet) | NET-02 |
| TS-12 | Backup/Restore | Verschlüsseltes Backup erstellen; zweite SD frisch installieren (TS-1), Restore mit Probelauf, dann einspielen | Pflanzen, Verlauf, Kalibrierung, Kopplungen vorhanden; Sensoren liefern ohne Neukopplung weiter; falsche Passphrase → abgelehnt | REQ-GW-06, UC-14 |
| TS-13 | OTA Sensor-Firmware | Signiertes Abbild hochladen, an 1 Sensor verteilen; Gegenproben: unsigniert, falsche Signatur, ältere Version (SEC_CNT), Strom am Sensor während Übertragung weg (Zelle entnehmen) | Neues Image bestätigt (Version in App); Gegenproben abgelehnt (422/409); nach Abbruch läuft alte Version, erneuter Versuch klappt | REQ-FW-02…05, PROTOCOL 9 |
| TS-14 | **Koexistenz WLAN/BLE (W-7) – Auftraggeber-Test** | Pi im Zielraum, WLAN-Last (z. B. Videostream zum Handy über den Pi-AP-Pfad bzw. Dateikopie auf den Pi); BLE-Sender (Sensor oder XIAO nRF52840 mit 27.5 s Intervall) in 18 m Abstand, 24 h; danach App → Sensoren → „verpasste Advertisings“ (`missed_pct`) ablesen; zusätzlich 1000 × „Jetzt messen“ unter Last (GATEWAY_SETUP Kap. 10 Nr. 2) | Fangquote und P_MISS protokolliert; P_MISS ≤ Annahme in `gateway.toml` (`p_miss`), sonst Wert eintragen und Energiebudget neu rechnen; 95-%-Reaktionszeit ≤ eingestellte Reaktionszeit + 30 s. Entscheid XIAO-Empfänger (D-014) | W-7, OP-K12, OP-GW-4 |
| TS-15 | Gateway-Update | Neue Version per `install_gateway.sh` über bestehende Installation; (falls Schlüssel eingerichtet) signiertes Online-Update, Gegenprobe mit defekter Signatur | Daten erhalten, Dienst aktiv; defekte Signatur abgelehnt; nicht startende Version → Rückfall nach 60 s | REQ-GW-11 |
| TS-16 | Dauerlauf | 7 Tage Betrieb mit allen Mustern | Kein Neustart durch Watchdog (ausser absichtlich), SD-Schreibmenge/Tag aus `GET /system` notiert, CPU-Temperatur, Leistungsaufnahme ≤ 2 W (USB-Messgerät) | REQ-GW-04, GATEWAY_SETUP Kap. 10 Nr. 5 |

**Reihenfolge:** TS-1 → TS-4 → TS-2/TS-3 → TS-5 → TS-6/TS-7 → TS-14 (früh, entscheidet über Funkweg) → TS-9 →
TS-8 → TS-10 → TS-12 → TS-13 → TS-15 → TS-11 → TS-16.

**Hinweise:** TS-14 kann vor Eintreffen der Muster mit dem vorhandenen Pi und einem XIAO gemacht werden
(Red-Team W-7: kostet nichts). Für TS-8 (b) darf das Gateway kein Internet haben; öffentlicher NTP (OP-08) sonst
in App → Einstellungen → Zeit abschalten.
