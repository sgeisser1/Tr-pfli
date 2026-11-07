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
3. Serie bauen: `make release SIGN_KEY=~/fluidi-keys/fluidi_prod_ec-p256.pem VERSION=x.y.z BUILD_NO=n SEC_CNT=k`
   (bricht ab bei `DEV_ONLY_*` oder Schluessel im Repository; `.gitignore` sperrt `*.pem` ausser `DEV_ONLY_*`).
   Fingerabdruck: `python3 tools/key_fingerprint.py <pem>` (steht auch im Namen des Werks-Hex); Sperren nur mit
   `scripts/flash_sensor.py program --lock --expect-key-fp <fp>` – das Werkzeug verweigert den DEV-Schluessel.
   Der **oeffentliche** Teil wird dabei automatisch in MCUboot eingebaut (`build/mcuboot/fluidi_keys.c`,
   `imgtool getpub`). Bootloader und Anwendung muessen mit demselben Schluessel gebaut sein.
4. Das Gateway prueft Images vor dem Verteilen mit dem **oeffentlichen** Schluessel
   (`imgtool getpub -k <prod.pem> -e pem > fluidi_sign_pub.pem`; Pruefung wie `tools/verify_image.py`).
5. `SEC_CNT` (Anti-Rollback) nur bei Sicherheitskorrekturen erhoehen und niemals senken. BIMINFO-Sektor: Magic 2 B +
   Eintraege a 10 B (SDK `bootutil/security_cnt.h`) → hoechstens 204 Zaehleraenderungen, Zaehlerwert ≤ 204
   (`security_cnt.c` `MAX_SECURITY_CNT`). Jede Version muss zusaetzlich hoeher sein als die laufende: das prueft der
   Sensor nach OTA_END selbst (F-L1).
