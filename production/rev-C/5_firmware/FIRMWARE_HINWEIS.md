# Firmware Sensor – Hinweis zum Release Rev C

Das Paket enthält **keine** Firmware-Binärdateien. Gründe: Die Build-Artefakte in `firmware/sensor/build/` sind nicht versioniert, das Werks-Hex ist an den Signierschlüssel gebunden (Dateiname `…-key<Fingerabdruck>.hex`), und die Firmware wird erst am Muster freigegeben.

- Quelle: `firmware/sensor` (Bau: `make`, siehe `firmware/sensor/README.md`).
- Programmieren: `5_firmware/PROGRAMMIEREN_SENSOR.md` (ROM-UART-Bootloader, Programmieradapter Rev 1 oder Behelf, Sicherheitsregeln Kap. 1).
- Werkzeug: `scripts/flash_sensor.py`.

Arbeitsstand beim Erzeugen dieses Pakets (nur zur Nachverfolgung, **nicht freigegeben**):

| Datei | sha256 |
|---|---|
| `firmware/sensor/build/fluidi-sensor-0.1.0+1.bin` | `76c88e3c34c4380ff75fe50b8497c4019c9aa39f9948e610c5bab85f0068578d` |
| `firmware/sensor/build/fluidi-sensor-factory-0.1.0+1-key86e66310969bdc7d.hex` | `7a3e74ed9ff6295af3b2f93532191859ee25c0b6be6535c6f00a463e8966e524` |
