# Prüfbericht Phase 4 – Kragen-Feld (S3-K2) und Firmware/Protokoll, Sicht Sicherheit

Prüfer: Sicherheits-Agent, Stand 2026-11-07. Ich habe unabhängig von den Erstellern geprüft (frischer Kontext).

Geprüft wurden:
- `docs/interfaces/PCB_OUTLINE.md` Rev B (Z5A/Z5B, Kap. 7)
- `hardware/sensor/out/FLOORPLAN_OPTIONS.md` 2f
- `mechanical/sensor/check_sensor.txt`
- `docs/interfaces/PINMAP_SENSOR.md` Rev B (FW-1…FW-10)
- `firmware/PROTOCOL.md` (Kap. 4, 9, 17)
- `firmware/sensor/README.md`, `firmware/sensor/keys/README.md`
- `firmware/sensor/core/*.c`, `platform/cc23/fl_hw.c`
- `mcuboot/mcuboot.syscfg` und das erzeugte `build/mcuboot/mcuboot_config.h`
- `scripts/flash_sensor.py`
- REQ Kap. 6, REQ-RF-05/06, REQ-FW-04, D-013…D-021
- Auflagen S3-K1/K2 (`phase3_sleeve_sicherheit.md`) und R2-A1…A4 (`phase2_concepts_sicherheit.md`)

Selbst ausgeführt:
- `make check` (2026-11-07): **1463 C-Prüfungen und 14 Python-Tests bestanden**. Layout- und Pin-Prüfung ok.
- CCFG der Datei `build/fluidi-sensor-factory.hex` dekodiert, im Entwicklungszustand und nach `ccfg_lock()`.
- CCFG-Offsets und CRC-Bereiche gegen das SDK-`hw_ccfg.h` geprüft: **stimmen**
  (Permissions 0x18, allowDebugPort Bit 31:28, CRC 0x74C, debugCfg 0x7D0, CRC 0x7FC).
- MITM-Simulation gegen die Kopplung mit der Python-Referenz `firmware/tools/fluidi_proto.py`
  (Skript im Scratchpad, unten beschrieben).

**Ergebnis: Teil 1 freigegeben unter Bedingungen, kein Veto. Teil 2: 1 kritischer Befund mit VETO
(Kopplung ohne Commitment), dazu 5 wichtige und 5 kleine Befunde.**

---

## Teil 1 – TMP1075N + C24 im Vergusskragen (Z5B)

### 1.1 Vereinbarkeit mit S3-K2 und REQ-SAF-05

**Urteil: vereinbar, freigegeben unter den Bedingungen K-1…K-7.**

Begründung:
- **S3-K2 bleibt erfüllt.** Der Kragen bleibt ein fester Verguss. Die Hülse dichtet mit dem AS568-019 radial
  gegen den Kragen (z 4.3…6.7). Beim Zellwechsel wird der Kragen nicht berührt. Die Bauteile ändern am
  Dichtprinzip nichts, solange der Dichtstreifen z 2.0…4.2 auf F und B unverändert kupfer- und vialos bleibt.
- **Im Kragen liegt kein Netz der Energiequelle.** VBAT liegt nicht im Kragen, Q1 und die Pufferkondensatoren
  liegen im Band. Im Kragen liegen nur die Netze in der Tabelle. Bei Wasser im Kragen begrenzt also der
  GPIO-Treiber den Fehlerstrom (≤ einige mA, nur bei SENS_PWR = high). Das gibt keine relevante Erwärmung,
  REQ-SAF-01 ist nicht berührt. Folge eines Wassereintritts sind Korrosion und ein TMP-Ausfall, also ein
  Funktionsfehler.

| Netz | Treiber | Zustand |
|---|---|---|
| SENS_PWR | DIO12 (GPIO) | ≈ 20 ms je Messung high, sonst low |
| SDA, SCL | GPIO | im Schlaf low (Code `tmp1075_read`, Z. 159–161, geprüft) |
| GND | – | – |

- **REQ-SAF-05 bleibt prüfbar.** Die Flutung von Zellfach bzw. Elektronikraum ist unverändert möglich.

Neu und zu beachten:
- **Bauteile im Leckpfad:** Auf der F-Seite liegen U3 und C24 im Leckpfad Platine/Epoxid (z 2.0 → 7.3).
  Die wirksame Dichtlänge auf F ist damit nur der Dichtstreifen: **2.2 mm** (M-03 verlangt ≥ 2 mm, Reserve
  gering). Zum Zellfach hin liegen nur **0.5 mm Epoxid über U3** und **0.2 mm bis zur ASA-Taschenwand**
  (`check_sensor.txt` Z. 14).
- **Tasche unten offen:** Die Grenzfläche ASA/Epoxid der Tasche führt von aussen (z 2.0) bis 0.2 mm an U3 heran.

### 1.2 Bedingungen (Auflagen für Layout, Mechanik und Montage)

| Nr | Stufe | Bedingung |
|---|---|---|
| K-1 | wichtig | **Dichtstreifen z 2.0…4.2** auf allen Aussenlagen ohne Kupfer und Vias, Lötstopp geschlossen. **Innenlagen dort nur GND/Guard und die Sondennetze.** SENS_PWR, SDA und SCL enden über z 4.4: Sie kommen von oben und brauchen den Streifen nicht. So liegt am Dichtstreifen keine Signalspannung an. PCB_OUTLINE Z5A anpassen („die 4 Netze zu U3“ → nur GND). |
| K-2 | wichtig | **Vias im Feld:** zugedeckt (tented) oder gefüllt, und **≥ 1.0 mm von der Platinenkante**. Heute liegt das Feld bei x −9.4, die Kante bei −10, das sind nur 0.6 mm. Das Feld auf x ≥ −9.0 schieben (Mutter-Abstand bleibt ≥ 2.6). Grund: Die Kante im Zellfach wird geflutet, Wasser zieht entlang der Glasfaser (CAF/Docht) zu den Hülsen. |
| K-3 | wichtig | **Innenlagenleitungen in Z3/Z4** (Schott und Zellfach) **≥ 1.0 mm von der Platinenkante**. In Z4 keine Vias und kein Aussenkupfer (bleibt). |
| K-4 | wichtig | **Kein weicher Vorverguss (Gel/PU) auf U3/C24.** FLOORPLAN 2f schlägt ihn vor. Er würde im Leckpfad eine nicht haftende Grenzfläche schaffen, und mit 0.5 mm Deckschicht lässt er sich nicht allseitig einschliessen. Stattdessen ein einziges, mineralisch gefülltes Epoxid (Tg ≥ 80 °C, niedriger CTE) für den ganzen Kragen, blasenfrei (Vakuum oder kopfüber mit Entlüftung wie in PCB_OUTLINE 7). Typ mit Datenblatt nach `docs/references/` (heute ANNAHME). |
| K-5 | wichtig | **Montagevorbereitung:** Platine im Kragenbereich vor dem Verguss reinigen (Flussmittelreste) und, falls laut Datenblatt nötig, primern. Lötstopp im Dichtstreifen geschlossen. Die Taschenwände aus ASA anrauen bzw. primern (FDM-Naht nicht in die Tasche legen). |
| K-6 | klein | Schraubkanal M2 von unten als Sackloch bzw. mit O-Ring unter dem Kopf (S3-W1). Die Mutter muss vollständig eingegossen sein. Abstand U3–Mutter 3.09 mm ist ok. |
| K-7 | wichtig | **PROTOTYP-PRÜFUNG Kragen** (in den Testplan REQ-DOC-03), siehe Liste unten. |

Prüfablauf zu K-7 (PROTOTYP-PRÜFUNG):
1. 50 Zyklen −10/+65 °C, danach 168 h Lagerung bei 65 °C.
2. Danach je 24 h:
   - Kragen von aussen tauchen (Sonde bis z +3).
   - Zellfach fluten (REQ-SAF-05), mit eingesetzter Zelle.
   - Firmware-Fehlerfall nachbilden: **SENS_PWR dauernd high** (Testfirmware).
3. Messen:
   - Zellstrom und Leckstrom SENS_PWR→GND (Grenze **≤ 1 µA**, ANNAHME).
   - I²C-Funktion vorher und nachher.
4. Ein Opfermuster: Farbeindringprüfung bzw. Schliff durch den Kragen (Lunker, Ablösung an U3 und an der Taschenwand).

Firmware-Auflage (in PINMAP FW-1 bereits so, bestätigt): SENS_PWR nur während der TMP-Wandlung, SDA/SCL im
Schlaf low. Bei I²C-Fehler kein Dauer-Wiederholen, nur Fehler-Flag (Code: ein Versuch je Messung, ok).

**Freigabe Z5B: ja, unter K-1…K-7.** K-1…K-3 gehen vor dem Layout-Freeze in PCB_OUTLINE Rev C bzw. in die
Layoutregeln ein. Ohne K-1…K-3 gilt die Rückfallebene: U3 kommt ins Band.

---

## Teil 2 – Firmware, Protokoll, Schlüssel, Debug-Sperre, Energie-Regeln

### 2.1 Positiv bestätigt (selbst geprüft)

- **SECURE-Frames:**
  - AES-CCM-8, Nonce mit Richtungsbyte. Der Zähler wird **exakt** erwartet (`fl_secure_open`, Z. 150 `ctr != expect_ctr`).
  - Ein ungültiger MIC trennt die Verbindung. Nach 3 Fehlversuchen folgt eine Sperre von 30 min.
  - Frischer K_s je Sitzung aus beiden Nonces.
  - Ein Befehl wird erst nach einem gültigen Gateway-Frame ausgeführt.
- **Kopplung:**
  - Nur im Kopplungsmodus möglich (`on_pair`: `FL_MODE_PAIRING`).
  - Der Schlüssel wird erst gespeichert, wenn Tastendruck **und** CONFIRM_G vorliegen.
  - Füllbyte zufällig (PROTOCOL 4.6).
- **MCUboot-Konfiguration** (`mcuboot_config.h` erzeugt):
  - `MCUBOOT_SIGN_EC256`, `MCUBOOT_SWAP_USING_MOVE`, `MCUBOOT_HW_ROLLBACK_PROT`,
    `MCUBOOT_DOWNGRADE_PREVENTION_SECURITY_COUNTER`, `MCUBOOT_VALIDATE_PRIMARY_SLOT`.
  - `MCUBOOT_WATCHDOG_FEED` ist definiert: Ein Swap von 113 Sektoren läuft nicht in den 60-s-Watchdog.
  - Flash nach `TI_CC2340R5_Datasheet_SWRS272F.pdf` S. 21 Tab. 7.11: Löschen 2.2 ms, Schreiben 8.3 ms je Sektor.
- **OTA:**
  - Bestätigung erst nach Selbsttest **und** authentisierter Sitzung, sonst Rückfall nach 24 h.
  - Bei Abbruch wird der Kopfsektor von Slot 1 gelöscht.
  - Bei falschem SHA-256 kein Neustart.
  - Unterspannung während der Übertragung führt zum Abbruch.
- **Erstprogrammierung:**
  - `flash_sensor.py` erzwingt ≤ 57600 Baud und fragt „keine Zelle im Halter“ ab (R2-A2/A3, REQ-SAF-CC-03).
  - `--lock` setzt pBldrVtor = FORBID, bldrEnabled = 0, allowDebugPort = FORBID und dbgAuth = FORBID.
    Das reicht nach TRM 8.1.8 (`TI_CC23xx_TechnicalReferenceManual_SWCU193A.pdf` S. 425), um SWD zu sperren.
- **FW-1/FW-2 im Code** (`fl_port_measure`):
  - TMP zuerst, danach I²C low.
  - Burst = 50 + 250 + 250 µs (+ eine Batteriemonitor-Lesung), höchstens 4 Bursts, 30 ms Pause.
  - LED aus, kein Flash-Schreiben im Burst.
  - Alle Abtastschleifen sind zeitbegrenzt (kein Hängen bei totem Oszillator).
- **FW-5:** UV-Abschaltung bei < 2.4 V (zweimal) bzw. < 2.3 V. Neustart nach UV-Abschaltung nur ab 2.6 V Ruhespannung.

### 2.2 Befunde

**F-K1 · kritisch · REQ-RF-05/06 · VETO**

Die Farbfolge (SAS) hat **kein Commitment**. Ein aktiver Angreifer im Funkbereich koppelt sich unerkannt
dazwischen (MITM), und zwar **mit Wahrscheinlichkeit ≈ 1, nicht 1/243** wie in PROTOCOL 4.2 angegeben.

So geht der Angriff:
1. Der Angreifer koppelt zuerst mit dem Sensor und kennt danach dessen SAS.
2. Danach variiert er in seiner PAIR_RSP an das Gateway `s_nonce` so lange, bis die SAS des Gateways gleich ist.
   Im Mittel braucht er 243 SHA-256-Aufrufe, das dauert weniger als 1 ms.

Nachweis (Skript `mitm_sas.py` im Scratchpad, mit `fluidi_proto.py`): **200 von 200 Kopplungen** gelangen,
im Mittel mit 250 Versuchen, höchstens 1659.

Folge: Der Angreifer kennt K_link. Er kann dem Sensor Befehle geben (Einstellungen, Kalibrierung, Daten
löschen, Messintervall/Batterie) und dem Gateway falsche Messwerte liefern. Firmware einspielen kann er nur
mit einem gültigen Signierschlüssel, siehe F-W1.

Vorschlag (Prinzip wie Bluetooth Numeric Comparison bzw. ZRTP):
- `PAIR_REQ` enthält `gw_pub` und `C = SHA-256("fluidi-commit" ‖ gateway_id ‖ gw_pub ‖ gw_nonce)`, aber **ohne** `gw_nonce`.
- Der Sensor antwortet mit `PAIR_RSP` {s_pub, s_nonce}.
- Neu: `PAIR_REVEAL` {gw_nonce}. Der Sensor prüft C. Passt C nicht: Abbruch und Fehlversuch.
- Das Transkript umfasst REQ, RSP und REVEAL. SAS und Schlüsselableitung bleiben wie bisher.

Damit muss der Angreifer seine Nonce festlegen, bevor er die Nonce der Gegenseite kennt. Es bleibt 1/243 je Versuch.

**Aufhebung des VETO:**
1. PROTOCOL 4.2 ist geändert.
2. Sensor-Firmware, Gateway (`firmware/gateway/fluidi_gw`) und Python-Referenz setzen die Änderung um.
3. Neue Testvektoren.
4. Ein Host-Test bildet den Angreifer nach. In ≥ 10 000 Läufen liegt seine Erfolgsrate ≤ 1 %.

Das VETO blockiert:
- die Festschreibung von Protokoll v1,
- die Gateway-Kopplung für den Echtbetrieb,
- jede Firmware-Freigabe über den Labortest hinaus.

Es blockiert **nicht** die Inbetriebnahme im Labor und nicht Teil 1.

**F-W1 · wichtig (für die Serienfreigabe kritisch) · REQ-FW-04**

Der DEV-Schlüssel ist der Standard (`Makefile: SIGN_KEY ?= keys/DEV_ONLY…`). `flash_sensor.py --lock` prüft
nicht, welcher öffentliche Schlüssel in MCUboot steckt.

Ein gesperrter Sensor mit DEV-Schlüssel nimmt **dauerhaft** jedes Image an, das jemand mit dem öffentlichen
Repo-Schlüssel signiert:
- MCUboot ist per OTA nicht aktualisierbar.
- Bootloader und SWD sind gesperrt.

Vorschlag:
- `--lock` bricht ab, wenn der MCUboot-Bereich den DEV-Schlüssel enthält. Dazu den Byte-Vergleich mit
  `imgtool getpub` gegen den DEV-Schlüssel rechnen oder einen Fingerabdruck einbetten.
- Der Name des Werks-Hex enthält den Schlüssel-Fingerabdruck.
- `make release` verlangt einen `SIGN_KEY` ausserhalb des Repos.
- `.gitignore`: `*.pem` ausser `DEV_ONLY_*`.

**F-W2 · wichtig · REQ-FW-04, CONCEPTS 2.8**

Die Serien-CCFG ist unvollständig. Dekodiert aus `fluidi-sensor-factory.hex` nach `ccfg_lock()`:
- allowFlashProgram, allowToolsClientMode, allowReturnToFactory und allowFlashVerify stehen weiter auf **ALLOW (0xA)**.
- WEPRA ist 0xFFFFFFFF, also ohne Schutz (FW-O2).

TRM 8.1.8: Wird beim Start die SWD-Sequenz erkannt, ist SACI trotz allowDebugPort = FORBID erreichbar.
TRM 8.2.2: allowFlashProgram ist nach der Erstprogrammierung „normally not allowed“. Bit-Löschen in
MCUboot-Code per SACI (FLASH_PROG_MAIN_SECTOR, TRM 8.3.2.3.4) wäre damit möglich. Das braucht physischen
Zugang zu DIO16/17.

Vorschlag für `--lock`:
- allowFlashProgram = FORBID und allowToolsClientMode = FORBID. ChipErase darf bleiben (es löscht die Schlüssel).
- WEPRA für die Sektoren 0–10 (MCUboot). **Sektor 11 (0x5800, BIMINFO/Sicherheitszähler) bleibt beschreibbar.**
- CCFG-Sektor schützen.
- Den Test `test_flash_sensor.py` entsprechend erweitern.
- PROTOTYP-PRÜFUNG PP-9 ergänzen: OTA und Zähler funktionieren nach der Sperre weiter.

**F-W3 · wichtig · FW-2/FW-5, Energie**

Drei Reset- bzw. Weck-Schleifen können die Zelle leeren:
- **(a) Brownout-Reset ohne Sperre:** Der Neustart wird nur nach einer *geordneten* UV-Abschaltung gesperrt
  (`cnt.pad`). Nach einem Brownout-Reset (`FL_RR_BROWNOUT`) läuft der Sensor sofort voll an, mit dieser Folge
  von Lasten: MCUboot-ECDSA-Prüfung des Slots → `save_counters()` (Flash-Schreiben **vor** jeder
  VDD-Prüfung) → Mess-Bursts → L11-LED → Advertising. Am Lebensende der Zelle (hoher R_int) ergibt das
  einen Dauerzyklus. Jeder Zyklus schreibt NV. Die Endurance von 30 k Zyklen (DS Tab. 7.11) gefährdet dann
  auch K_link. DS Fussnote 2: Ein abgebrochener Flash-Vorgang ist „not a safe operation“.
- **(b) Taster dauerhaft gedrückt:** `fl_port_shutdown()` weckt bei DIO21 = low. Ist der Taster bei der
  UV-Abschaltung gedrückt oder klemmt er, wacht der Sensor sofort wieder auf, und das wiederholt sich.
  Dazu fliesst der Pull-up-Strom.
- **(c) Fatale Fehler:** `crit_err`/`fl_platform_fatal` setzen den Chip ohne Begrenzung zurück.

Vorschlag:
- Beim Start zuerst die VDD-Ruhespannung lesen, NV erst ab ≥ UV_MV schreiben.
- `BROWNOUT` wie UV behandeln: < 2.6 V führt zur Abschaltung.
- Aufeinanderfolgende abnormale Resets ohne 10 min stabilen Betrieb zählen. Ab 3 folgt die Abschaltung
  bzw. ein Backoff. Den Zähler im AON- bzw. Retention-Register führen statt im Flash.
- Vor der Abschaltung: Ist DIO21 low, Pull-up aus und **ohne** Tasterwecken. Aufwecken dann nur durch Zellwechsel (POR).
- PROTOTYP-PRÜFUNG mit Quelle 2.0–2.4 V über R_int 100–300 Ω und Taster gedrückt: Mittelstrom ≤ Ruhestrom × 10
  (ANNAHME). Ladung je Boot messen (inkl. MCUboot-Prüfung).

**F-W4 · wichtig · REQ-RF-06 (Replay)**

`fl_port_rng()` wird beim HELLO nicht geprüft (`fl_app.c` Z. 536). Dasselbe gilt für das Füllbyte (Z. 428).
Fällt der RNG aus, bleibt `s_nonce` = 0. K_s hängt dann nur noch von `gw_nonce` ab, und eine aufgezeichnete
Gateway-Sitzung lässt sich **vollständig wiederholen**.

Vorschlag:
- Rückgabewert prüfen. Bei Fehler kein HELLO_RSP und Trennung.
- Beim Koppeln abbrechen.
- Host-Test mit RNG-Fehler in `port_sim`.

**F-W5 · wichtig · FW-2**

FW-O4 ist offen: Funkereignisse während eines Bursts sind nicht ausgeschlossen. Die SPICE-Grenze
(136 mV Einbruch) setzt „kein Funk“ voraus. Ausserdem verlängert die Batteriemonitor-Lesung im Burst die
Kette-an-Zeit.

Vorschlag:
- Messung nur ohne aktive Verbindung.
- Advertising für die Messdauer (≤ 0.2 s) anhalten, oder die Messung per RCL-Planung nach einem ADV-Ereignis legen.
- PP-2 misst Burstdauer (DIO11) und VDD-Minimum bei gleichzeitigem ADV.

**F-L1 · klein · REQ-FW-04**

Die Versionsprüfung beim Downgrade nutzt die *vom Gateway angegebene* Version. MCUboot vergleicht nur den
Sicherheitszähler. Ein älteres signiertes Image mit gleichem `SEC_CNT` wäre installierbar. Die Regel „SEC_CNT
bei jeder Sicherheitskorrektur erhöhen“ (keys/README 5) deckt REQ-FW-04 ab.

Vorschlag: Bei OTA_END `ih_ver` aus dem Kopf von Slot 1 lesen und vergleichen. Die Zahl der BIMINFO-Einträge
(SDK `security_cnt.c`) belegen.

**F-L2 · klein · REQ-RF-05**

Auch mit Commitment bleiben 1/243 je Versuch. Für den Eigengebrauch ist das annehmbar: Fehlversuche sind
sichtbar (rot), und das Kopplungsfenster ist kurz. Optional 4–6 Farben (z. B. Cyan, Magenta, Weiss) →
6⁵ = 7776. Die Erkennbarkeit am Muster prüfen.

**F-L3 · klein · Energie (nur Entwicklungszustand)**

Pin-Trigger DIO21: Hält man den Taster beim Einsetzen der Zelle oder beim POR gedrückt, läuft der
ROM-Bootloader mit aktiver CPU ohne Ende. Die Serien-CCFG hebt das auf. Prototyp-Anleitung: „beim
Zellwechsel nicht drücken“.

**F-L4 · klein**

Company-ID 0xFFFF (FW-P7) ist für den Eigengebrauch ohne Inverkehrbringen vertretbar.

**F-L5 · klein · PROTOCOL 4.6**

CRC32-Seitenkanal: Im Entwicklungszustand braucht er physischen Zugang plus Taster. Er ist durch das
zufällige Füllbyte abgeschwächt und entfällt mit der Serien-CCFG. Für SACI_FLASH_VERIFY gilt dasselbe:
nur Ganzsektor-Vergleich, liefert keinen CRC (TRM 8.3.2.3.6). Ok.

Nicht vertieft:
- Gateway (REQ-SAF-NET-*). Stichprobe: Schreib-Routen mit `auth="write"`/`elevated`, Ersteinrichtung mit
  Einrichtungscode, Image-Signatur mit öffentlichem Schlüssel, SSH nur während der Einrichtung. Eigene Prüfung
  folgt mit der Gateway-Freigabe.
- Die Kopplungsänderung F-K1 betrifft auch `fluidi_gw`.

### 2.3 Testplan-Ergänzungen (REQ-DOC-03, PROTOTYP-PRÜFUNG)

1. MITM-Kopplungstest mit Relais-Angreifer (nach F-K1).
2. Replay einer Sitzung und RNG-Fehler.
3. Serien-CCFG:
   - SWD/SACI-Zugriff (Programmieren muss scheitern).
   - OTA, Zählerübernahme und Rückfall (PP-7/PP-9).
   - DEV-Schlüssel-Sperre im Werkzeug.
4. Reset-Schleifen nach F-W3 (EOL-Quelle, Taster gedrückt, fataler Fehler) mit Mittelstrom und NV-Schreibzahl.
5. Burst bei gleichzeitigem ADV (F-W5).
6. Kragentests nach K-7.

---

## Zusammenfassung

| Nr | Stufe | Kurz |
|---|---|---|
| Teil 1 | – | **Z5B freigegeben unter K-1…K-7** (K-1…K-3 vor Layout-Freeze) |
| F-K1 | **kritisch, VETO** | SAS ohne Commitment, MITM ≈ 100 % (nachgewiesen) |
| F-W1 | wichtig (Serie: kritisch) | DEV-Schlüssel und `--lock` ohne Prüfung |
| F-W2 | wichtig | Serien-CCFG: FlashProgram/ToolsClient erlaubt, WEPRA fehlt |
| F-W3 | wichtig | Reset- und Weck-Schleifen (Brownout, Taster, fataler Fehler) |
| F-W4 | wichtig | RNG-Rückgabe ungeprüft, Replay möglich |
| F-W5 | wichtig | Funk während Burst nicht ausgeschlossen |
| F-L1…L5 | klein | Downgrade per Header, SAS-Länge, Dev-Bootloader, Company-ID, CRC |

---

## Runde 2 (2026-11-07, Sicherheits-Agent)

Geprüft: Antwort `phase4_firmware_response.md`, PROTOCOL 0.2 (Kap. 0, 4.2–4.5), `fluidi_proto.py`,
`test_pairing_mitm.py`, `core/fl_app.c`, `platform/cc23/fl_hw.c`, `scripts/flash_sensor.py`, `Makefile`,
SDK-`hw_ccfg.h` (simplelink_lowpower_f3_sdk_9_23_00_27, cc23x0r5).

Selbst ausgeführt:
- `make check`: 1499 C-Prüfungen bestanden, 17 Tests Flash-Werkzeug ok, 3 Tests MITM ok. MITM v2: 39/10 000 = 0.39 %.
- Eigene Angriffsvariante (Scratchpad, Python-Referenz): Der Angreifer lässt zuerst das Gateway offenlegen und
  kennt damit die Ziel-SAS. Danach versucht er auf der Sensorseite, eine andere Nonce als die festgelegte offenzulegen.
  Ergebnis: 167/40 000 = 0.42 %. Keine gefälschte Offenlegung bestand die Commitment-Prüfung (0 von 200 000).
- Eigener C-Test gegen `fl_app.c` (Abbruch-und-Neustart):
  - Trennung nach PAIR_RSP führt zu Abbruch, LED rot (L7) und Verlassen des Kopplungsmodus.
  - Ein neues PAIR_REQ ohne erneuten Tastendruck lehnt der Sensor mit ERROR ab.
  - Ein zweites PAIR_REQ in derselben Verbindung führt zum Abbruch.
  - Ohne REVEAL innerhalb von 15 s folgt der Abbruch.
  - Ein wiederholtes PAIR_REVEAL führt zum Abbruch.
  - `s_nonce` ist bei jedem Versuch neu. Der Schlüssel ist im Simulator fest; die Plattform erzeugt ihn bei jedem
    Versuch neu aus dem RNG (`fl_hw.c` `fl_port_ecdh_keygen`).

### F-K1 – VETO aufgehoben (mit Auflage G-1)

Die Konstruktion ist korrekt:
- C bindet gateway_id, gw_pub und gw_nonce.
- Das Transkript REQ‖RSP‖REVEAL enthält beide Public Keys, beide Nonces und C. Die SAS hängt vom ganzen Transkript ab.
- Die Reihenfolge wird im Zustandsautomaten erzwungen (`sess`). Ein falscher Reveal führt zum Abbruch.
- Ein neuer Versuch ist nur möglich, nachdem der Nutzer den Taster erneut ≥ 3 s gedrückt hat. Jeder Fehlversuch ist
  rot sichtbar. Damit beträgt die Erfolgsrate je Nutzerversuch 1/243. Die Abbruch-und-Neustart-Taktik ist durch den
  Nutzer begrenzt: nach 3 Versuchen 1.2 %, nach 10 Versuchen 4 % (Restrisiko F-L2, akzeptiert).

Die Bedingungen 1, 3 und 4 sind erfüllt. Bedingung 2 ist nur teilweise erfüllt: `firmware/gateway/fluidi_gw`
(`central.py`, `protocol.py`, `simsensor.py`) ist **noch v1** (PAIR_SHOW, `fluidi-pair-v1`). Ein v1-Gateway kann
einen v2-Sensor nicht koppeln, weil die Versionsprüfung greift. Daraus entsteht deshalb kein offenes Angriffsfenster.

- **Auflage G-1 (vor der Gateway-Freigabe):**
  - Das Gateway auf v2 umstellen: gw_nonce und ECDH-Schlüssel je Versuch neu, REVEAL erst nach gültigem PAIR_RSP,
    keine automatische Wiederholung der Kopplung.
  - Den Interop-Test gegen `gen_vectors.py` bestehen.
  - Den Sensor-Simulator auf v2 umstellen.
  - Die Prüfung gehört zur Gateway-Sicherheitsprüfung.

### F-W1…F-W5, F-L1…F-L3 – Stichproben

| Nr | Ergebnis |
|---|---|
| F-W1 | **erledigt.** Prüfungen von `check_lock_key`: genau ein SPKI-Schlüssel im MCUboot-Bereich, ≠ DEV, = `--expect-key-fp`. Der Fingerabdruck steht im Namen des Werks-Hex. `make release` weist `DEV_ONLY*` und Schlüssel im Repo ab. `.gitignore` habe ich mit `git check-ignore` geprüft. |
| F-W2 | **erledigt.** Die Offsets und Masken habe ich gegen `hw_ccfg.h` geprüft: PERM 0x18 mit Maske 0xF00F0F0F (RTF, ToolsClient, FlashProgram, DebugPort), WEPRA 0x20 Bits 0–10, WEPRAUX.ccfgSector, debugCfg 0x7D0, CRC 0x74C/0x7FC. Laut Header ist die Schutzwirkung „sticky-0“ und wird mit der FCFG „maximally restrictive“ kombiniert. Der Nachweis bleibt PP-9. |
| F-W3 | **erledigt.** VDD und Neustartgrund werden vor dem ersten NV-Zugriff gelesen. Der Zähler steht in AONRSTA1 und begrenzt auf 3 Neustarts. Nach Brownout gilt die Schwelle 2.6 V. Bei gedrücktem Taster (`fl_hw.c` `fl_port_shutdown`) sind Pull-up und Wecken aus. `fl_platform_fatal` setzt kein „geplant“. |
| F-W4 | **erledigt.** Der RNG-Rückgabewert wird an diesen Stellen geprüft: HELLO, Schlüsselerzeugung, s_nonce, Füllbyte. |
| F-W5 | **erledigt.** Gemessen wird nur ohne Verbindung (`meas_pending`), und das ADV ist während der Messung aus. |
| F-L1 | **erledigt.** `ih_ver`, Sicherheitszähler und `hw_rev` werden aus Slot 1 geprüft; Host-Test vorhanden. |
| F-L2 | Ablehnung akzeptiert (siehe oben). |
| F-L3 | Anleitung vorhanden. |

### Neue bzw. verbleibende Punkte (keine Blocker)

**N-1 · klein · PROTOCOL 4.5**

Eine Commitment-Verletzung erhöht nur `cnt.auth_fail`, nicht `fail_streak` (`fl_app.c` Z. 514). Das widerspricht
PROTOCOL 4.5 („3 in Folge → LOCKED“). Weil der Sensor den Kopplungsmodus ohnehin verlässt, ist die Auswirkung gering.

Vorschlag: Den Text oder den Code angleichen.

**N-2 · klein · F-W3, PROTOTYP-PRÜFUNG**

Fällt VDD beim Brownout unter die POR-Schwelle, meldet der Chip vermutlich `POWER_ON`. Dann wird der Zähler genullt
und die Schwelle ist 2.4 V statt 2.6 V. Jeder solche Zyklus enthält:
- die MCUboot-ECDSA-Prüfung,
- `save_counters()` vor der ersten Lastmessung (`fl_app_init`).

Vorschlag:
- `save_counters()` erst nach der Selbsttest-Messung bzw. nach `check_battery`.
- PP-11 um „EOL-Quelle mit Einbruch unter POR, Neustartgrund und NV-Schreibzahl je Zyklus“ ergänzen.

**N-3 · klein · F-W5**

`fl_port_adv_set(NULL…)` ist im BLE-Stack vermutlich asynchron. Ein bereits geplantes ADV-Ereignis kann noch in den
ersten Burst fallen.

Vorschlag: Ein ADV-Ende-Ereignis abwarten oder eine Pause von ≥ 1 Intervall einhalten, alternativ in PP-2 messen.

**N-4 · klein**

Liefert `fl_port_vbat_mv()` beim Start 0 (Lesefehler), entfällt die UV-Prüfung (`A->vbat_rest &&`).

Vorschlag: Den Wert 0 wie Unterspannung behandeln oder die Lesung einmal wiederholen.

**N-5 · klein · Dokumentation**

PROTOCOL 4.3 nennt für das Gateway noch `esp_fill_random`. Das Gateway ist ein Pi (D-022), deshalb dort `os.urandom`
bzw. `secrets` angeben.

### Ergebnis Runde 2

- **VETO F-K1 aufgehoben** für Protokoll v2 und die Sensor-Firmware. Die Gateway-Kopplung im Echtbetrieb setzt
  Auflage G-1 voraus.
- F-W1…F-W5 sind umgesetzt. Die Serienfreigabe hängt weiter an PP-9 (CCFG-Wirkung) und PP-11.
- N-1…N-5 sind klein und blockieren nicht.
