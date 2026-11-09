# fluidi – Gateway einrichten (Raspberry Pi Zero 2 W)

| | |
|---|---|
| Dokument | `docs/manuals/GATEWAY_SETUP.md` |
| Version | 0.3 (Phase 6: ohne RTC, Status-LED; Firmennetz-Vorabprüfung, Aufstellung, Testfirmware-Schalter) |
| Datum | 2026-11-09 |
| Gilt für | Gateway-Software `firmware/gateway/` (Version 0.5.0), PWA `app/`, D-014 (Pi Zero 2 W), D-017/D-029 (Klimasensor), D-020, D-027 (Status-LED, vorläufig), D-028 (keine RTC) |
| Status | Anleitung **ohne Test am echten Pi** erstellt: Software und Installationsskript sind in WSL/Simulation geprüft; die Schritte am Gerät sind **PROTOTYP-PRÜFUNG** (Kap. 10). |

Kennzeichnungen wie im Projekt: **ANNAHME**, **PROTOTYP-PRÜFUNG**.

---

## 1 Überblick

```
Handy (Pixel 10, Chrome)  ──HTTPS──►  fluidi.local:443   PWA + API (Anmeldung)
Büro-Bildschirm           ──HTTP───►  fluidi.local:8080  Dashboard, nur lesen, ohne Login (abschaltbar)
                                       fluidi.local:80    nur Weiterleitung + CA-Zertifikat
Sensoren  ◄──BLE──►  Pi Zero 2 W (eingebautes Bluetooth)  ── I²C ── SHT4x (Raumklima)
                                                           ── GPIO17 ── grüne Status-LED
Zeit: NTP über das WLAN (keine Echtzeituhr im Gateway, D-028); Rückfall: Uhrzeit des Handys beim Öffnen der App
```

Benötigt: Raspberry Pi Zero 2 W, microSD (empfohlen: Industrial/pSLC, ≥ 8 GB), Netzteil 5 V 2.5 A Micro-USB
(`docs/datasheets/RaspberryPi_Zero2W_ProductBrief_2024-04.pdf`, S. 3), ein PC mit **Raspberry Pi Imager**, das
fluidi-Repository auf dem PC, das SHT4x-Breakout (Teil siehe `hardware/gateway/BOM_GATEWAY.csv`, Kap. 5) und die
Status-LED (grüne 3-mm-LED + Widerstand 470 Ω, Kap. 5.2). **Keine** Echtzeituhr (RTC) und keine Knopfzelle im
Gateway (D-028): Das Gateway steht dauerhaft im WLAN und holt die Zeit per NTP.

Zeitbedarf: ca. 45 min (davon 15–20 min Paketinstallation auf dem Pi).

**Aufstellung und Strom (Sicherheit W-3):** nur das Original-Netzteil (Raspberry Pi 12.5 W, 5 V, Micro-USB,
`BOM_GATEWAY.csv` G2). Gateway, Netzteil und Steckdose **nicht im Giessbereich** (nicht zwischen Töpfen, auf
Untersetzern oder unter hängenden Pflanzen; Kabel nicht durch nasse Bereiche). Ist Wasser auf Netzteil oder
Steckdose gelangt: nicht anfassen, Sicherung aus, dann ausstecken, Netzteil ersetzen (`INBETRIEBNAHME.md` Kap. 2).

### 1.1 Vorabprüfung Firmen-WLAN (Red Team W-5)

Die App funktioniert nur, wenn das Handy das Gateway im WLAN **direkt** erreicht und den Namen `fluidi.local`
auflöst (mDNS). Für das Büro-WLAN des Auftraggebers ist mDNS bestätigt (Auftraggeber). In anderen Netzen oder nach
einem WLAN-Wechsel **vor dem Aufstellen** prüfen bzw. mit der IT klären:

| Frage | Prüfung ohne Gateway | Prüfung mit Gateway |
|---|---|---|
| WLAN mit Passwort (PSK) oder Firmenanmeldung (802.1X)? | WLAN-Einstellungen am Handy | Das Installationsskript kennt nur PSK über NetworkManager; 802.1X ist **nicht** vorbereitet → IT fragen |
| Dürfen Geräte im WLAN einander erreichen (keine **Client-Isolation**)? | Laptop im WLAN: `python -m http.server 8000`; am Handy `http://<IP des Laptops>:8000` öffnen → Ordnerliste erscheint | am Handy `http://<IP des Gateways>/ca` öffnen (IP aus dem Router) → Fingerabdruckseite erscheint |
| Wird mDNS (`.local`) weitergegeben? | am Handy `http://<Laptopname>.local:8000` (Windows beantwortet mDNS für den eigenen Namen, **ANNAHME**) | am Handy `http://fluidi.local/ca` öffnen; am PC `ping fluidi.local` |
| Ist NTP (UDP 123) ins Internet erlaubt? | – | App → *System → Zeit*: Quelle „Internet-Zeit (NTP)“ (ohne NTP: Handyzeit, `FEHLERSUCHE.md` 4.4) |

**Ausweichwege, wenn eine Prüfung scheitert (ehrlich):**

- **mDNS gefiltert, Geräte erreichen sich aber:** Es gibt einen vorbereiteten Weg (CONCEPTS 5.2), am echten Gerät
  aber **noch nicht erprobt (PROTOTYP-PRÜFUNG):** Die IT vergibt dem Gateway eine feste Adresse (DHCP-Reservierung)
  und **genau einen** DNS-Namen, z. B. `fluidi.firma.ch`. Dann in `/etc/fluidi/gateway.toml` `hostname =
  "fluidi.firma.ch"` setzen, ein neues Zertifikat erzeugen
  (`cd /opt/fluidi/current/gateway && sudo -u fluidi /opt/fluidi/venv/bin/python -m fluidi_gw pki-init -c
  /etc/fluidi/gateway.toml --force`), den Dienst neu starten (`sudo systemctl restart fluidi-gateway`) und das **neue** CA-Zertifikat samt
  Fingerabdruck auf allen Geräten installieren. Die CA gilt dann nur für diesen einen Namen. Ein Aufruf über die
  IP-Adresse ist **kein** Ausweichweg: Das Zertifikat gilt absichtlich nicht für IP-Adressen, und eine
  Zertifikatswarnung darf nicht weggeklickt werden.
- **Client-Isolation aktiv:** **Es gibt keinen Ausweichweg in der Software.** Das Gateway arbeitet weiter
  (Sensoren, Speicherung), aber ohne direkte Verbindung vom Handy ist die App nicht bedienbar. Lösung nur über die IT:
  Ausnahme für das Gateway, ein eigenes WLAN/VLAN ohne Isolation (z. B. für Geräte) oder ein separater Access Point.
  Ein Handy-Hotspot ist kein Dauerbetrieb (Zeit, Erreichbarkeit).
- **802.1X:** nicht vorbereitet; eigenes WLAN (PSK) für das Gateway bei der IT anfragen.

## 2 SD-Karte vorbereiten (Raspberry Pi Imager)

1. Imager starten → **Gerät:** Raspberry Pi Zero 2 W → **Betriebssystem:** *Raspberry Pi OS (other) →
   Raspberry Pi OS Lite (64-bit)* (Bookworm oder Trixie; ohne Desktop) → **SD-Karte** wählen.
2. **Einstellungen anpassen** (Menübezeichnungen je nach Imager-Version leicht anders, **ANNAHME**):
   - Hostname: `fluidi`
   - Benutzername und Passwort: eigener Admin-Benutzer (nicht `pi`), starkes Passwort
   - WLAN: SSID und Passwort des Firmen-WLANs, Land `CH`
   - Zeitzone `Europe/Zurich`, Tastatur `ch`
   - Dienste: **SSH aktivieren** (am besten mit öffentlichem Schlüssel). SSH wird **nur für die Einrichtung**
     gebraucht und am Ende abgeschaltet (Kap. 4.4).
3. Schreiben, Karte in den Pi, Netzteil anschliessen. Der erste Start dauert 1–3 min.
4. Am PC prüfen: `ping fluidi.local` (Windows: in PowerShell). Antwortet der Pi nicht, die IP im Router suchen.

## 3 Repository auf den Pi bringen

Vom PC aus (PowerShell oder WSL), im Repository-Ordner:

```bash
scp -r firmware app <benutzer>@fluidi.local:~/fluidi/
```

Für eine Installation **ohne PyPI-Zugang** zuerst auf einem PC mit Internet die Pakete für den Pi holen
(gleiche Python-Version wie auf dem Pi: Bookworm 3.11, Trixie 3.13):
`pip download --only-binary=:all: --platform manylinux_2_17_aarch64 --python-version 3.11 -r firmware/gateway/requirements-pi.txt -d wheels`
und den Ordner `wheels` mitkopieren (bleak und dbus-fast; **ANNAHME**: für aarch64 als Wheel verfügbar, sonst
Installation mit Internet).

## 4 Installation auf dem Pi

```bash
ssh <benutzer>@fluidi.local
cd ~/fluidi/firmware/gateway/install
sudo ./install_gateway.sh            # oder: sudo ./install_gateway.sh --wheels ~/fluidi/wheels
```

### 4.1 Was das Skript tut
| Schritt | Inhalt |
|---|---|
| Prüfung | Board, Raspberry Pi OS-Version, **Python ≥ 3.11** (Bookworm 3.11.x, Trixie 3.13.x) |
| apt | `python3-venv python3-cryptography bluez avahi-daemon nftables i2c-tools network-manager` (python3-cryptography: Bookworm 38.0.4, Trixie 43.0.0) |
| Name | Hostname `fluidi`, Avahi → `fluidi.local` im LAN (mDNS) |
| Schnittstellen | I²C ein (`raspi-config nonint do_i2c 0`), BlueZ GATT-Cache `Cache = always` (**ANNAHME**, beschleunigt Verbindungen), WLAN-Energiesparen aus |
| SD-Schonung | Journal nur im RAM (`Storage=volatile`), Swap-Datei aus, `noatime`, `/tmp` im RAM (Kap. 8) |
| Programm | `/opt/fluidi/releases/<version>/` (Gateway + PWA), Symlink `/opt/fluidi/current`, venv `/opt/fluidi/venv` mit `bleak==3.0.2` (Liste `requirements-pi.txt`, installierter Stand in `pip-freeze.txt`) |
| Benutzer | Systembenutzer `fluidi` (Gruppen `bluetooth`, `i2c`), Daten `/var/lib/fluidi` (0700) |
| Zertifikat | Einmal-CA nur für `fluidi.local` (Kap. 6), CA-Schlüssel nur im Arbeitsspeicher |
| Dienste | `fluidi-gateway.service` (ohne Root, Watchdog), `fluidi-helper.path` (Root-Helfer für WLAN/NTP/Neustart/Update) |
| Firewall | nftables: eingehend nur 80, 443, 8080, mDNS 5353, DHCP; 22 nur bis `--finish` |
| Status-LED | Zeile `dtoverlay=gpio-led,gpio=17,label=fluidi,trigger=heartbeat` in `/boot/firmware/config.txt` (wirksam nach dem nächsten Neustart); der Dienst schaltet sie über den Root-Helfer (Kap. 5.2) |
| Zeit | NTP über `systemd-timesyncd` einschalten (nur bei der Erstinstallation; danach gilt die Einstellung in der App). **Kein** RTC-Overlay, kein `hwclock` (D-028) |

Am Ende zeigt das Skript **Einrichtungscode** und **CA-Fingerabdruck** – beides notieren.

### 4.2 Signaturschlüssel für Sensor-Firmware
Den **öffentlichen** Schlüssel (PEM) vom Entwickler nach `/etc/fluidi/keys/sensor-fw.pem` kopieren
(`sudo install -m 0644 sensor-fw.pem /etc/fluidi/keys/`). Ohne Schlüssel nimmt das Gateway **keine** Firmware an.
Der private Schlüssel bleibt offline beim Entwickler (REQ-FW-04).

**Testfirmware (Sicherheit W-2):** Abbilder mit Build-Nummer 9000–9999 (bzw. Dateiname `-tf<n>-`) sind
Testfirmware (`TESTFIRMWARE.md`). Das Gateway nimmt sie nur an, wenn in `/etc/fluidi/gateway.toml`
`allow_testfw = true` steht (Werk: `false`), zeigt sie rot „TESTFIRMWARE“ und verteilt sie nur an **einen** einzeln
gewählten Sensor nach ausdrücklicher Bestätigung. Nach der Musterprüfung `allow_testfw = false` setzen und am
Nutzer-Gateway **nicht** den DEV-Schlüssel als `sensor-fw.pem` belassen, sobald Produktionsschlüssel vorliegen.

### 4.3 Prüfen
Nach der **Erstinstallation einmal neu starten** (`sudo reboot`), damit das LED-Overlay geladen wird (Kap. 5.2).
```bash
sudo ./install_gateway.sh --check
journalctl -u fluidi-gateway -n 50       # Protokoll (nur im RAM, nach Neustart leer)
```

### 4.4 Einrichtung abschliessen
Wenn App und Sensoren laufen (Kap. 6–7):
```bash
sudo ./install_gateway.sh --finish       # SSH aus, Port 22 zu
```
Später wieder Zugang (nur mit physischem Zugriff): SD-Karte am PC, leere Datei `ssh` auf die Boot-Partition,
neu starten (Raspberry-Pi-OS-Funktion, **ANNAHME** für Trixie unverändert), danach `--finish` erneut.

## 5 Klimasensor und Status-LED anschliessen

### 5.1 Klimasensor (D-017, D-029)

Verbaut wird ein **SHT4x-Breakout** (Teil, Bezugsquelle und Masse siehe `hardware/gateway/BOM_GATEWAY.csv`; die Wahl
eines kleineren Breakouts für die Klimakammer läuft in Phase 6, D-029). Elektrisch gilt für jedes SHT4x-Breakout:
I²C-Adresse **0x44**, Versorgung **3.3 V**. **PROTOTYP-PRÜFUNG:** Lage in der belüfteten Kammer, Kabellänge.

Vier Drähte vom Breakout an die Stiftleiste J8 des Pi (Pinbelegung aus
`docs/datasheets/RaspberryPi_Zero2W_ReducedSchematics_RP-008360-DS-1.pdf`, Block J8):

| Breakout | Pi J8 | Bemerkung |
|---|---|---|
| VIN / VDD | Pin 1 (3V3) | SHT4x: VDD 1.08–3.6 V (`docs/datasheets/Sensirion_SHT4x_Datasheet_V7.3.pdf`, S. 9) – **nicht** an 5 V (Pin 2/4), ausser das Breakout hat einen eigenen Regler (Datenblatt/Schaltplan des gewählten Breakouts prüfen) |
| GND | Pin 6 oder Pin 9 (GND) | Gehäuse-CAD sieht Pin 6 oder 9 vor (`mechanical/gen/fluidi_gateway_pi.py`); Pin 14 bleibt für die LED frei. GND-Pins im Schaltplan prüfen (**PROTOTYP-PRÜFUNG**) |
| SDA | Pin 3 (GPIO2, SDA1) | I²C-Bus 1 → `/dev/i2c-1` |
| SCL | Pin 5 (GPIO3, SCL1) | |

Löten: Drähte (z. B. AWG 28–30, 4 Farben) direkt in die Lötaugen des Pi (ohne Stiftleiste, flaches Gehäuse) oder
an eine gekürzte Stiftleiste; Lötstellen mit Schrumpfschlauch isolieren. Den Sensor **nicht** direkt über dem
SoC/WLAN-Chip platzieren (Eigenerwärmung); belüftete, thermisch getrennte Kammer (D-017).

Prüfen: `sudo i2cdetect -y 1` → Adresse **44** (SHT4x-AD1B, Datenblatt S. 1). Danach
`sudo systemctl restart fluidi-gateway`; in der App unter *Einstellungen → System: Zeit, WLAN, Protokoll* erscheint
bei „Raumklima“ „… °C · … % rF“ (sonst „kein Sensor“).
Pull-ups für SDA/SCL: auf dem Pi vorhanden laut Schaltplan (R23/R24 bei GPIO2/3, **ANNAHME** aus Bauteilnähe,
prüfen); zusätzliche Pull-ups auf dem Breakout sind unkritisch.

Raumklima und Zeit: Solange das Gateway keine gültige Zeit hat (Kap. 9), hält es die Klimawerte im Arbeitsspeicher
und speichert sie erst nach dem Zeitabgleich mit korrigierter Zeit; ein Neustart vorher verwirft sie.

### 5.2 Status-LED (D-027, vorläufig)

Schaltung nach `docs/reviews/phase5_gateway_led.md` Kap. 3 (Variante B): **J8 Pin 11 (GPIO17) → Widerstand 470 Ω →
Anode** der grünen 3-mm-LED (langes Bein), **Kathode** (kurzes Bein, Abflachung) → **J8 Pin 14 (GND)**. Widerstand
direkt am Anodenbein, beide Lötstellen mit Schrumpfschlauch. **Vor dem Einschalten** den Widerstand zwischen Pin 11
und Pin 14 messen (ohne Widerstand wäre GPIO17 bei leuchtender LED fast kurzgeschlossen). LED in den Lichtschacht des
Deckels (Mechanik).

| LED | Bedeutung | Quelle |
|---|---|---|
| Herzschlag-Muster des Kernels (Trigger `heartbeat`) | Pi startet, fluidi-Dienst noch nicht bereit | Kernel-Overlay `trigger=heartbeat` |
| **kurzer Blitz alle 5 s** | alles in Ordnung: Dienst läuft, Funk bereit | Dienst (`fluidi_gw/statusled.py`) |
| **schnelles Blinken** (5 × pro s) | Kopplungsfenster in der App offen | Dienst |
| **aus** | Nacht (ausserhalb des LED-Zeitfensters der Sensoren bzw. an abgewählten Wochentagen), Schalter „Status-LED“ in der App aus, **Funk ausgefallen**, Dienst gestoppt/abgestürzt oder Gateway ohne Strom | Dienst / systemd `ExecStopPost` |

**ANNAHMEN** (D-027 gilt „für den Moment“): Nacht = gleiches Zeitfenster wie der Giessen-Hinweis der Sensoren
(*Einstellungen → Messung & Sensor-LED*); ohne gültige Zeit gilt „Tag“; der Schalter „Status-LED (Quittung,
Lebenszeichen)“ schaltet auch die Gateway-LED; Kopplung blinkt auch nachts. „Aus“ ist mehrdeutig (Nacht oder
Fehler) – tagsüber heisst „aus“ also Fehler (FEHLERSUCHE.md).

Technik: Das Blinken macht der Kernel (Trigger `timer`). Der Dienst hat keine Root-Rechte; er legt bei einem
Zustandswechsel eine Anfrage für `fluidi-helper` ab (Aktion `led`, nur `ok|pair|off`). Endet der Dienst, schaltet
systemd die LED aus (`ExecStopPost=+… fluidi-helper led off`). Abschalten der Funktion: `status_led = "off"` in
`/etc/fluidi/gateway.toml`.

Prüfen (nach dem Neustart, der das Overlay lädt): `sudo ./install_gateway.sh --check` → Zeile „Status-LED“ mit
Trigger `[timer]` (Dienst läuft) bzw. `[heartbeat]` (Dienst noch nicht gestartet). Von Hand:
`echo none | sudo tee /sys/class/leds/fluidi/trigger; echo 1 | sudo tee /sys/class/leds/fluidi/brightness` → LED an.
**PROTOTYP-PRÜFUNG:** Sichtbarkeit hinter dem Fenster (zu dunkel → 330 Ω, Vorlage Kap. 3), Trigger `timer` im
Raspberry-Pi-Kernel vorhanden, LED aus nach `sudo systemctl stop fluidi-gateway` und nach einem Watchdog-Neustart.

## 6 Zertifikat auf dem Pixel 10 installieren (Android)

Warum: Die App läuft nur über HTTPS als installierbare PWA (Service Worker, sicherer Kontext). Das Gateway hat ein
eigenes Zertifikat, ausgestellt von einer **Einmal-CA, die nur für `fluidi.local` gilt** (Name Constraint). Der
CA-Schlüssel wurde nach dem Ausstellen verworfen – niemand kann damit weitere Zertifikate erstellen.

1. Handy im **gleichen WLAN** wie das Gateway (nicht über mobile Daten oder VPN: Android löst `.local` nur im WLAN
   auf; unterstützt ab Android 12 über das DNS-Resolver-Modul, AOSP-Dokumentation „DNS Resolver“, abgerufen
   2026-11-07).
2. In Chrome `http://fluidi.local/ca` öffnen. **Fingerabdruck** mit dem vom Installationsskript angezeigten
   vergleichen. Stimmt er nicht: abbrechen (jemand im Netz könnte sich dazwischenschalten).
3. Link „CA-Zertifikat laden“ → Datei `fluidi-ca.crt` wird heruntergeladen.
4. **Einstellungen → Sicherheit & Datenschutz → Weitere Sicherheits- und Datenschutzeinstellungen →
   Verschlüsselung und Anmeldedaten → Zertifikat installieren → CA-Zertifikat** → Warnung mit „Trotzdem
   installieren“ bestätigen → Datei `fluidi-ca.crt` wählen → mit PIN/Fingerabdruck bestätigen.
   (Menüpfad je nach Android-Version leicht anders, **ANNAHME**; Quelle: Hersteller- und Firmenanleitungen,
   siehe Kap. 11.)
5. Chrome neu starten, `https://fluidi.local/` öffnen – kein Warnhinweis mehr.
   **PROTOTYP-PRÜFUNG:** Chrome auf Android vertraut vom Nutzer installierten CAs für Webseiten; ob die Name
   Constraint auf dem Pixel 10 korrekt ausgewertet wird, am Gerät prüfen (Gegenprobe: ein Zertifikat für einen
   anderen Namen muss abgelehnt werden – Testzertifikat erzeugt der Entwickler).
6. **Ersteinrichtung:** Einrichtungscode und neues Passwort (≥ 10 Zeichen) eingeben.
7. Chrome-Menü ⋮ → **„Zum Startbildschirm hinzufügen“ / „App installieren“** → fluidi startet wie eine App.
   Zähler am App-Symbol (Anzahl durstiger Pflanzen) zeigt Android, sobald die App einmal geöffnet war.

Am Windows-PC (optional): `fluidi-ca.crt` doppelklicken → *Zertifikat installieren* → *Aktueller Benutzer* →
Speicher **„Vertrauenswürdige Stammzertifizierungsstellen“**. Edge/Chrome nutzen den Windows-Speicher.

Erneuern (Zertifikat ≤ 825 Tage, die App warnt 60 Tage vorher): SSH einschalten (Kap. 4.4),
`sudo -u fluidi /opt/fluidi/venv/bin/python -m fluidi_gw pki-init -c /etc/fluidi/gateway.toml --force`
(im Ordner `/opt/fluidi/current/gateway`), Dienst neu starten, CA auf allen Geräten neu installieren.

## 7 Sensoren koppeln

App → *Einstellungen → Sensor koppeln → Kopplung starten* (die Gateway-LED blinkt schnell). Am Sensor die Taste
halten, bis die LED nach 3 s **einmal kurz gelb** aufblitzt, dann loslassen (vor 8 s); der Sensor blinkt danach
1 × pro Sekunde gelb (bis 2 min). Sensor in der Liste wählen, Pflanze (Art aus 40 Profilen) angeben → **Farbfolge
vergleichen**: Die LED zeigt fünf Farben (rot/grün/gelb), die App dieselbe Folge. Stimmt sie: **kurz die
Sensortaste drücken** und in der App **„Farben stimmen“**. LED 1 s grün = gekoppelt. Ausführlich für Endnutzer:
`docs/manuals/PAIRING_KALIBRIERUNG.md`.

## 8 SD-Karte und Stromausfall

- Messwerte: SQLite mit WAL und `synchronous=FULL`; der Sensor löscht Werte erst nach der Quittung, die das Gateway
  erst **nach** dem Schreiben sendet → kein Datenverlust bei Stromausfall (REQ-GW-05).
- Schreibrate (Schätzung, **ANNAHME**): ≈ 700 Transaktionen/Tag bei 15 Sensoren, ≈ 15–25 MB/Tag inkl. WAL-Checkpoints
  und Dateisystem-Journal → ≈ 6–9 GB/Jahr (ARCHITECTURE Kap. 14.4). Messen: App → *System* → „Schreibvorgänge“, auf dem
  Pi `cat /proc/diskstats` (Feld 10 = geschriebene Sektoren à 512 B von `mmcblk0`) an zwei Tagen vergleichen.
- Optional stärker: Root schreibgeschützt (`raspi-config` → *Performance → Overlay File System*) **nur zusammen mit
  einer eigenen Datenpartition** für `/var/lib/fluidi` (sonst gehen die Daten beim Neustart verloren) – nicht
  automatisiert, **PROTOTYP-PRÜFUNG**.
- Backup regelmässig in der App (*Export & Backup*), Datei auf dem PC aufbewahren.

## 9 Betrieb

| Aufgabe | Weg |
|---|---|
| Passwort vergessen | SSH einschalten (Kap. 4.4), `cd /opt/fluidi/current/gateway && sudo -u fluidi /opt/fluidi/venv/bin/python -m fluidi_gw reset-password -c /etc/fluidi/gateway.toml` → neuer Einrichtungscode; Daten bleiben (UC-16) |
| Dashboard für Kollegen | App → Einstellungen → Dashboard → „Ohne Anmeldung im Firmennetz“ → Bildschirm öffnet `http://fluidi.local:8080/` (HTTP, nur lesen, keine Sensor-IDs; D-020) |
| WLAN wechseln | App → System → WLAN wechseln (Rückfall nach 2 min ohne Erfolg) |
| Zeit | **Keine Echtzeituhr im Gateway (D-028).** NTP (einzige Verbindung nach aussen, abschaltbar; Firmen-NTP unter Einstellungen → Zeit). Nach einem Stromausfall steht die Uhr zuerst auf der zuletzt gespeicherten Zeit und gilt **nicht** als gültig, bis NTP synchronisiert. Ohne NTP (z. B. nach Stromausfall ohne Internet) übernimmt das Gateway beim Öffnen der App durch den angemeldeten Admin automatisch die Uhrzeit des Handys (nur wenn plausibel); sonst App → System → „Zeit vom Handy übernehmen“. Bis dahin: Werte „Zeit unsicher“, sie werden danach anhand der Sensor-Laufzeit zurückgerechnet (docs/reviews/phase5_gateway_zeit.md) |
| Sensor-Firmware | App → Sensoren & Firmware → signiertes Abbild hochladen → Verteilen |
| Gateway-Update | neue Repository-Version auf den Pi kopieren, `sudo ./install_gateway.sh` (Daten bleiben); signiertes Online-Update über die App ist vorbereitet (REQ-GW-11, Schlüssel `/etc/fluidi/keys/gateway-update.pem`) |
| Simulation am PC | `cd firmware/gateway && python3 -m fluidi_gw sim --port 8080` (Sensoren simuliert, gleiches Funkprotokoll) |

## 10 Offene Prüfungen am Gerät (PROTOTYP-PRÜFUNG)

1. bleak/BlueZ am Pi Zero 2 W: Scan, Verbindung, Notify, MTU 247, Dauer bis HELLO (Befund K-1 in
   `docs/reviews/phase4_protocol_software.md`).
2. Koexistenz WLAN/BLE (OP-K12): 1000 × „Jetzt messen“, P_MISS messen → `p_miss` in `/etc/fluidi/gateway.toml`.
3. Name-Constraint-CA auf dem Pixel 10 (Kap. 6), mDNS `fluidi.local` in Chrome.
4. Klimasensor: Eigenerwärmung im Gehäuse, Offset.
5. Schreibrate der SD-Karte über 7 Tage messen.
6. Watchdog: Funk-Thread blockieren → systemd startet neu; Status-LED geht dabei aus und danach wieder auf „Blitz“.
7. Status-LED (Kap. 5.2): Sichtbarkeit, Muster, aus bei gestopptem Dienst.
8. Zeit ohne RTC (D-028): Prüfungen GZ-1…GZ-4 in `docs/reviews/phase5_gateway_zeit.md` Kap. 6 (Pi stromlos ohne Netz,
   Systemzeit nach dem Start, Handyzeit beim Öffnen der App, unplausible Handyzeit wird abgelehnt). **ANNAHME:**
   `systemd-timesyncd` speichert die Zeit auch unter Raspberry Pi OS regelmässig (`/var/lib/systemd/timesync/clock`).

## 11 Quellen
- Raspberry Pi Zero 2 W Product Brief (lokal), Reduced Schematics (lokal, J8).
- Sensirion SHT4x Datenblatt V7.3 (lokal, `docs/datasheets/INDEX.csv` GW-CLIM1).
- Overlay gpio-led: `docs/references/RaspberryPi_GPIO-Doku_Auszug_2026-11-08.txt` (overlays/README Z. 1606–1658);
  LED-Trigger `timer` mit `delay_on`/`delay_off`: https://docs.kernel.org/leds/leds-class.html (abgerufen 2026-11-08);
  Lage von `config.txt` (`/boot/firmware/`): https://www.raspberrypi.com/documentation/computers/config_txt.html
  (abgerufen 2026-11-08).
- AOSP „DNS Resolver“ (.local ab Nov. 2021, Android 12+): https://source.android.com/docs/core/ota/modular-system/dns-resolver (abgerufen 2026-11-07).
- CA-Installation Android (Menüpfad): z. B. https://cloudveil.org/?p=2314925 , https://help.cybozu.cn/en/settings/browser/certificate/other/an_chrome.html (abgerufen 2026-11-07).
- Debian-Paketversionen python3-cryptography: https://packages.debian.org/bookworm/python3-cryptography , https://packages.debian.org/trixie/python3-cryptography (abgerufen 2026-11-07).
- bleak 3.0.2 (Python ≥ 3.10): https://pypi.org/project/bleak/ (abgerufen 2026-11-07).
