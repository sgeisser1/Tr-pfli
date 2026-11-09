# Firmware Sensor – Hinweis zum Release Rev C

Das Paket enthält **bewusst keine** Firmware-Binärdateien. Gründe: (1) Die vorhandenen Build-Artefakte in `firmware/sensor/build/` sind mit dem öffentlichen **DEV-Schlüssel** signiert (`DEV_ONLY_*`): ein damit gebauter MCUboot nimmt jedes Image an, das irgendjemand mit dieser Datei signiert – solche Binärdateien dürfen nicht als Lieferstand erscheinen (`5_firmware/sensor/README.md` der Schlüssel, Regel 1). (2) Sie sind nicht versioniert, also nicht an den Git-Stand dieses Pakets gebunden. (3) Die Firmware ist **nicht freigegeben** (Musterstand); der Serienstand wird mit dem Produktionsschlüssel offline gebaut (`make release SIGN_KEY=…`), der nie ins Repository oder in dieses Paket gelangt. Für den Musterbau wird aus `8_quellcode/` gebaut (`5_firmware/sensor/README.md`).

- Quelle: `firmware/sensor` (Bau: `make`, siehe `firmware/sensor/README.md`).
- Programmieren: `5_firmware/PROGRAMMIEREN_SENSOR.md` (ROM-UART-Bootloader, Programmieradapter Rev 1 oder Behelf, Sicherheitsregeln Kap. 1).
- Werkzeug: `scripts/flash_sensor.py`.

Arbeitsstand beim Erzeugen dieses Pakets (nur zur Nachverfolgung, **nicht freigegeben**):

| Datei | sha256 |
|---|---|
| `firmware/sensor/build/fluidi-sensor-0.1.0+1.bin` | `353771f6e26c724feeed812757774b09d5d0c2aa96e0f35dee5e509bd00bc04e` |
| `firmware/sensor/build/fluidi-sensor-factory-0.1.0+1-key86e66310969bdc7d.hex` | `e05a569f0b454c9d61d8d5632e51801e6d3072ceec3a42bb7a54f86408cb14ef` |
