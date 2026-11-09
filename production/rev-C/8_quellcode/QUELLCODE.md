# Quellcode – Hinweis zum Release Rev C

Archiv `fluidi_quellcode_firmware_app.tar.gz` = `git archive 4b49ae84358b7de3961c2a7569a5d4edf141cb62` der Pfade `firmware`, `app`, `scripts/flash_sensor.py`, `scripts/test_flash_sensor.py`, `scripts/testfw_eval.py`, `scripts/test_testfw_eval.py`, `docs/interfaces/PINMAP_SENSOR.md`, `hardware/sensor/out/fluidi_sensor.net` (nur versionierte Dateien, deterministisch: gleicher Commit → gleicher sha256).

- **Schlüssel:** einzig enthalten ist der öffentliche Entwicklungsschlüssel `firmware/sensor/keys/DEV_ONLY_fluidi_signing_ec-p256.pem` (bewusst im Repository, kein Schutz; nötig für `make` und `make TESTFW=n`). Alle anderen Schlüsseldateien sind ausgeschlossen; der Inhalt wird beim Erzeugen auf „PRIVATE KEY“ geprüft. Produktionsschlüssel sind nie im Repository (`firmware/sensor/keys/README.md`).
- Für den Build ebenfalls enthalten: `docs/interfaces/PINMAP_SENSOR.md`, `hardware/sensor/out/fluidi_sensor.net` (Prüfung `make check`), Python-Tests in `scripts/` (K-1 Red Team).
- Firmware Sensor: Bau und Signierung `5_firmware/sensor/README.md`, Werkzeuge `5_firmware/INSTALL_FIRMWARE_TOOLS.md`, Flashen `5_firmware/PROGRAMMIEREN_SENSOR.md` (`scripts/flash_sensor.py` im Archiv).
- Gateway (Python, keine Binärdateien): `firmware/gateway/` im Archiv, Installation `4_gateway/GATEWAY_SETUP.md` (`firmware/gateway/install/install_gateway.sh`).
- PWA (statisch, kein Build-Schritt): `app/` im Archiv, Anleitung `4_gateway/APP.md`; das Gateway liefert die PWA aus.
- Prüfen: `make_release_rev_c.py --check` erzeugt das Archiv aus dem Commit neu und vergleicht den sha256.
