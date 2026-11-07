# fluidi – Gateway einrichten (Raspberry Pi Zero 2 W)

| | |
|---|---|
| Dokument | `docs/manuals/GATEWAY_SETUP.md` |
| Version | 0.1 (Phase 4 Welle 2) |
| Datum | 2026-11-07 |
| Gilt für | Gateway-Software `firmware/gateway/` (Version 0.5.0), PWA `app/`, D-014 (Pi Zero 2 W), D-017 (Klimasensor), D-020 |
| Status | Anleitung **ohne Test am echten Pi** erstellt: Software und Installationsskript sind in WSL/Simulation geprüft; die Schritte am Gerät sind **PROTOTYP-PRÜFUNG** (Kap. 10). |

Kennzeichnungen wie im Projekt: **ANNAHME**, **PROTOTYP-PRÜFUNG**.

---

## 1 Überblick

```
Handy (Pixel 10, Chrome)  ──HTTPS──►  fluidi.local:443   PWA + API (Anmeldung)
Büro-Bildschirm           ──HTTP───►  fluidi.local:8080  Dashboard, nur lesen, ohne Login (abschaltbar)
                                       fluidi.local:80    nur Weiterleitung + CA-Zertifikat
Sensoren  ◄──BLE──►  Pi Zero 2 W (eingebautes Bluetooth)  ── I²C ── SHT4x (Raumklima)
```

Benötigt: Raspberry Pi Zero 2 W, microSD (empfohlen: Industrial/pSLC, ≥ 8 GB), Netzteil 5 V 2.5 A Micro-USB
(`docs/datasheets/RaspberryPi_Zero2W_ProductBrief_2024-04.pdf`, S. 3), ein PC mit **Raspberry Pi Imager**, das
fluidi-Repository auf dem PC, optional ein SHT4x-Breakout (Kap. 5).

Zeitbedarf: ca. 45 min (davon 15–20 min Paketinstallation auf dem Pi).

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

Am Ende zeigt das Skript **Einrichtungscode** und **CA-Fingerabdruck** – beides notieren.

### 4.2 Signaturschlüssel für Sensor-Firmware
Den **öffentlichen** Schlüssel (PEM) vom Entwickler nach `/etc/fluidi/keys/sensor-fw.pem` kopieren
(`sudo install -m 0644 sensor-fw.pem /etc/fluidi/keys/`). Ohne Schlüssel nimmt das Gateway **keine** Firmware an.
Der private Schlüssel bleibt offline beim Entwickler (REQ-FW-04).

### 4.3 Prüfen
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

## 5 Klimasensor anschliessen (D-017) – PLATZHALTER

> **Platzhalter:** Breakout-Modul, Kabellänge und Lage der belüfteten Kammer im Gehäuse G1 sind noch nicht
> festgelegt (Mechanik/Elektronik). Diese Anleitung wird nach der Wahl ergänzt. **PROTOTYP-PRÜFUNG.**

Vier Drähte vom SHT4x-Breakout an die Stiftleiste J8 des Pi (Pinbelegung aus
`docs/datasheets/RaspberryPi_Zero2W_ReducedSchematics_RP-008360-DS-1.pdf`, Block J8):

| Breakout | Pi J8 | Bemerkung |
|---|---|---|
| VIN / VDD | Pin 1 (3V3) | SHT4x: VDD 1.08–3.6 V (`docs/datasheets/Sensirion_SHT4x_Datasheet_V7.3.pdf`, S. 9) – **nicht** an 5 V (Pin 2/4), ausser das Breakout hat einen eigenen Regler (Datenblatt des Breakouts prüfen) |
| GND | Pin 6 (GND) | GND-Pin im Schaltplan prüfen (**PROTOTYP-PRÜFUNG**) |
| SDA | Pin 3 (GPIO2, SDA1) | I²C-Bus 1 → `/dev/i2c-1` |
| SCL | Pin 5 (GPIO3, SCL1) | |

Löten: Drähte (z. B. AWG 28–30, 4 Farben) direkt in die Lötaugen des Pi (ohne Stiftleiste, flaches Gehäuse) oder
an eine gekürzte Stiftleiste; Lötstellen mit Schrumpfschlauch isolieren. Den Sensor **nicht** direkt über dem
SoC/WLAN-Chip platzieren (Eigenerwärmung); belüftete, thermisch getrennte Kammer (D-017).

Prüfen: `sudo i2cdetect -y 1` → Adresse **44** (SHT4x-AD1B, Datenblatt S. 1). Danach
`sudo systemctl restart fluidi-gateway`; in der App unter *System* erscheint „Raumklima … °C · … % rF“.
Pull-ups für SDA/SCL: auf dem Pi vorhanden laut Schaltplan (R23/R24 bei GPIO2/3, **ANNAHME** aus Bauteilnähe,
prüfen); zusätzliche Pull-ups auf dem Breakout sind unkritisch.

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

App → *Einstellungen → Sensor koppeln → Kopplung starten*. Am Sensor Taste ≥ 3 s, bis die LED gelb blinkt.
Sensor in der Liste wählen, Pflanze (Art aus 40 Profilen) angeben → **Farbfolge vergleichen**: Die LED zeigt fünf
Farben (rot/grün/gelb), die App dieselbe Folge. Stimmt sie: **kurz die Sensortaste drücken** und in der App
**„Farben stimmen“**. LED grün = gekoppelt.

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
| Zeit | NTP (einzige Verbindung nach aussen, abschaltbar). Ohne Internet: App → System → „Zeit vom Handy übernehmen“ |
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
6. Watchdog: Funk-Thread blockieren → systemd startet neu.

## 11 Quellen
- Raspberry Pi Zero 2 W Product Brief (lokal), Reduced Schematics (lokal, J8).
- Sensirion SHT4x Datenblatt V7.3 (lokal, `docs/datasheets/INDEX.csv` GW-CLIM1).
- AOSP „DNS Resolver“ (.local ab Nov. 2021, Android 12+): https://source.android.com/docs/core/ota/modular-system/dns-resolver (abgerufen 2026-11-07).
- CA-Installation Android (Menüpfad): z. B. https://cloudveil.org/?p=2314925 , https://help.cybozu.cn/en/settings/browser/certificate/other/an_chrome.html (abgerufen 2026-11-07).
- Debian-Paketversionen python3-cryptography: https://packages.debian.org/bookworm/python3-cryptography , https://packages.debian.org/trixie/python3-cryptography (abgerufen 2026-11-07).
- bleak 3.0.2 (Python ≥ 3.10): https://pypi.org/project/bleak/ (abgerufen 2026-11-07).
