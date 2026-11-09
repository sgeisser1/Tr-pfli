# Quellcode – Hinweis zum Release Rev C

Archiv `fluidi_quellcode_firmware_app.tar.gz` = `git archive 9c39ce89e36b9b3d5fee3a5123202614c30ae3d7` der Pfade `firmware`, `app`, `scripts/flash_sensor.py` (nur versionierte Dateien, deterministisch: gleicher Commit → gleicher sha256).

- **Ohne Schlüssel:** `*.pem`, `*.key`, `*.der` ausgeschlossen, Inhalt beim Erzeugen auf „PRIVATE KEY“ geprüft. Der Entwicklungsschlüssel `firmware/sensor/keys/DEV_ONLY_*.pem` liegt nur im Repository (öffentlich, kein Schutz); Produktionsschlüssel sind nie im Repository (`firmware/sensor/keys/README.md`).
- Firmware Sensor: Bau und Signierung `5_firmware/sensor/README.md`, Werkzeuge `5_firmware/INSTALL_FIRMWARE_TOOLS.md`, Flashen `5_firmware/PROGRAMMIEREN_SENSOR.md` (`scripts/flash_sensor.py` im Archiv).
- Gateway (Python, keine Binärdateien): `firmware/gateway/` im Archiv, Installation `4_gateway/GATEWAY_SETUP.md` (`firmware/gateway/install/install_gateway.sh`).
- PWA (statisch, kein Build-Schritt): `app/` im Archiv, Anleitung `4_gateway/APP.md`; das Gateway liefert die PWA aus.
- Prüfen: `git archive --format=tar.gz <Commit> -- firmware app scripts/flash_sensor.py ':(exclude)*.pem' ':(exclude)*.key' ':(exclude)*.der' | sha256sum` muss dem Wert in `README.md` entsprechen (`make_release_rev_c.py --check` macht das).
