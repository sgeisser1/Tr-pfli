# Firmware Sensor – Hinweis zum Release Rev C

> **NUR MUSTER – DEV-SCHLÜSSEL – NICHT FREIGEGEBEN.** Die Dateien in `5_firmware/MUSTER_DEV/` sind mit dem öffentlichen Entwicklungsschlüssel `DEV_ONLY_fluidi_signing_ec-p256.pem` signiert. Ein damit gebauter MCUboot nimmt jedes Image an, das jemand mit dieser (öffentlichen) Datei signiert – **nie an Endnutzer ausliefern**, nur für Prototypen im Labor. `scripts/flash_sensor.py program --lock` verweigert den DEV-Schlüssel.

- Gebaut beim Erzeugen dieses Pakets mit `make` aus dem entpackten Quellarchiv `8_quellcode/fluidi_quellcode_firmware_app.tar.gz` (Git `4b49ae84358b7de3961c2a7569a5d4edf141cb62`), Toolchain über `~/fluidi-tools/env.sh` (`5_firmware/INSTALL_FIRMWARE_TOOLS.md`). Danach `make check` im selben Baum (Probe, siehe unten). Das unsignierte Bild ist reproduzierbar; die ECDSA-Signatur ist bei jedem Bau anders, deshalb gilt der sha256 dieser Datei.
- Flashen: `5_firmware/PROGRAMMIEREN_SENSOR.md` (ROM-UART-Bootloader, PL2303 Weg A/B, Sicherheitsregeln Kap. 1).
- Testfirmware (`make TESTFW=n`) ist **nicht** beigelegt; bauen nach `5_firmware/TESTFIRMWARE.md`, nie an Endnutzer.
- **Serienstand:** nur `make release SIGN_KEY=<Produktionsschlüssel ausserhalb des Repositorys>` – der Produktionsschlüssel ist nie im Repository und nie in diesem Paket (`5_firmware/sensor/keys/README.md`).

| Datei | sha256 | Bytes |
|---|---|---|
| `MUSTER_DEV/fluidi-sensor-factory-0.1.0+1-key86e66310969bdc7d.hex` | `2e0511eec0228ffddd70c68ab9d2e451c761a7d5ed9cba74c4946dd219da1c6f` | 694996 |
| `MUSTER_DEV/fluidi-sensor-0.1.0+1.bin` | `b032bf8087f3c1dead05adaa580ad07333cb11d169d893d0aa03b18bbbe94893` | 207376 |

Probe-Build (Ausschnitt):

```
$ make  (aus entpacktem Quellarchiv) -> Exitcode 0
    [sign] imgtool sign --version 0.1.0+1 --security-counter 0
    [sign] WARNUNG: mit DEV-Schluessel signiert – nur Labor/Prototyp, nicht ausliefern
    [factory] MCUboot + Slot0 (bestaetigt) -> fluidi-sensor-factory-0.1.0+1-key86e66310969bdc7d.hex  (Schluessel-Fingerabdruck 86e66310969bdc7d)
    [factory] MCUboot bis 0x0430b, Slot0 0x06000..0x3efff (233472 Byte), CCFG ja
      [ok] MCUboot passt vor BIMINFO
      [ok] Anwendung passt in Slot 0 (inkl. Kopf, Trailer-Reserve)
      [ok] signiertes Image passt in Slot 1 (Swap-using-Move)
      [ok] Slot 0 = Slot 1 + 1 Sektor (Swap-using-Move)
      [ok] Bereiche luckenlos bis 512 kB
      [ok] RAM-Reserve >= 2 kB
      [ok] Ausnahmevektoren -> fl_fault_handler (0x00032e21), ohne Stack, kein Exception_handlerSpin (O-5)
      [ok] AssertHandler/Stackueberlauf -> fl_fault_handler, kein HAL_ASSERT_SPINLOCK/keine Spin-Schleife (O-5)
$ make check  (aus entpacktem Quellarchiv) -> Exitcode 0
    [check] Layout: ok
    [check] Pins: ok
    Ran 13 tests in 0.157s
    OK
    Ran 23 tests in 0.607s
    OK (skipped=1)
    Ran 3 tests in 0.208s
    OK
```
