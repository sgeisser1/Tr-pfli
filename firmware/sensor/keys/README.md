# Signierschluessel fluidi Sensor-Firmware (MCUboot, ECDSA P-256)

| Datei | Zweck | Status |
|---|---|---|
| `DEV_ONLY_fluidi_signing_ec-p256.pem` | **Entwicklungsschluessel** (privat!) fuer Labor und Prototyp | **NUR ENTWICKLUNG** – liegt bewusst im Repo, ist damit oeffentlich und bietet **keinen** Schutz |

Regeln (REQ-FW-04, CONCEPTS 2.8, PROTOCOL.md 9.1):

1. Der DEV-Schluessel darf **nie** auf ausgelieferten Sensoren als Vertrauensanker stehen. Ein mit dem DEV-Schluessel
   gebauter MCUboot akzeptiert jedes Image, das irgendjemand mit dieser (oeffentlichen) Datei signiert.
   `make` gibt beim Signieren mit `DEV_ONLY_*` eine Warnung aus.
2. **Produktionsschluessel nie ins Repo**, nie auf das Gateway. Erzeugen offline auf dem Entwickler-PC:
   `imgtool keygen -k ~/fluidi-keys/fluidi_prod_ec-p256.pem -t ecdsa-p256` (venv `~/fluidi-tools/venv`),
   Datei verschluesselt sichern (zwei Kopien, offline). Verlust = keine OTA-Updates mehr fuer ausgelieferte Sensoren.
3. Serie bauen: `make SIGN_KEY=~/fluidi-keys/fluidi_prod_ec-p256.pem VERSION=x.y.z BUILD_NO=n SEC_CNT=k`.
   Der **oeffentliche** Teil wird dabei automatisch in MCUboot eingebaut (`build/mcuboot/fluidi_keys.c`,
   `imgtool getpub`). Bootloader und Anwendung muessen mit demselben Schluessel gebaut sein.
4. Das Gateway prueft Images vor dem Verteilen mit dem **oeffentlichen** Schluessel
   (`imgtool getpub -k <prod.pem> -e pem > fluidi_sign_pub.pem`; Pruefung wie `tools/verify_image.py`).
5. `SEC_CNT` (Anti-Rollback) nur bei Sicherheitskorrekturen erhoehen (BIMINFO-Sektor hat begrenzt viele Eintraege,
   `security_cnt.c` im SDK); niemals senken.
