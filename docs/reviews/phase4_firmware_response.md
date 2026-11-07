# Antwort Firmware/Energie auf die Prüfberichte Phase 4 (Runde 1)

| | |
|---|---|
| Ersteller | Firmware/Energie, 2026-11-07 |
| Beantwortet | `docs/reviews/phase4_protocol_software.md` (Software-Agent) und `docs/reviews/phase4_sicherheit_kragen_firmware.md` (Sicherheits-Agent, **VETO F-K1**) |
| Ergebnis | `firmware/PROTOCOL.md` **0.2 / Protokollversion 2** (Änderungsliste Kap. 0), Sensor-Firmware `firmware/sensor/`, Python-Referenz `firmware/tools/fluidi_proto.py`, Angriffstest `firmware/tools/test_pairing_mitm.py`, `scripts/flash_sensor.py` |
| Nachweis | `make` (0 Fehler) und `make check` grün: 1499 C-Prüfungen (u. a. Kopplung v2, Commitment-Verletzung, RNG-Ausfall, Fristen, OTA-Zählerlücke, Reset-Schleifen, Image-Prüfung), 17 Tests Flash-Werkzeug, 3 Tests Kopplungsangriff: **MITM v2 39 von 10 000 = 0.39 %** (v1-Gegenprobe ≥ 99 %) |

Wer nachprüft, startet mit `source ~/fluidi-tools/env.sh; make -C firmware/sensor check`. Am Prüferskript
`mitm_sas.py` ist nur die Protokollversion anzupassen: Der Angreifer muss in v2 vor PAIR_REVEAL festlegen.

## 1 Software-Prüfung (`phase4_protocol_software.md`)

| Nr | Stufe | Antwort | Umsetzung |
|---|---|---|---|
| K-1 | kritisch | **umgesetzt** | Für HELLO gilt eine Frist von 1 s ab dem CCCD-Write, absolut höchstens 5 s ab dem Verbindungsaufbau. Fristüberschreitungen zählen **nicht** als Fehlversuch, sondern in einem eigenen Zähler: erst 10 in Folge lösen eine Sperre aus (Energieschutz). PROTOCOL Kap. 3 und 4.5, `fl_app.c` (`handshake_timeout`), Host-Test: 5 Timeouts führen zu keiner Sperre. Die Sensor-Plattform meldet den CCCD-Write (`fl_ble.c`). |
| K-2 | kritisch | **umgesetzt** | Kopplungsfristen: 15 s bis PAIR_REVEAL, danach 60 s für den Farbvergleich ohne Frames, gesamt ≤ 90 s. Die Sitzungsgrenze gilt während der Kopplung nicht. Host-Test: 8 s Pause zwischen PAIR_RSP und REVEAL. |
| W-1 | wichtig | **umgesetzt** | Der Sensor stellt nach dem Verbindungsaufbau selbst eine Anfrage für 7.5–15 ms, Latenz 0, Supervision 2 s (`GAP_UpdateLinkParamReq`). MTU ≥ 100 ist ein SOLL; ist sie kleiner, sendet der Sensor 1 Datensatz je Frame. Im Kopf steht jetzt die Gegenseite Pi/BlueZ/bleak. Ob BlueZ die Anfrage annimmt, ist PROTOTYP-PRÜFUNG PP-12. |
| W-2 | wichtig | **umgesetzt** | Während OTA nimmt der Sensor `erwartet ≤ ctr ≤ erwartet+64` an, aber nur, wenn die Nachricht OTA_DATA ist. Danach gilt `erwartet = ctr+1`, der Zähler bleibt streng monoton. Eine Lücke bei anderen Nachrichten führt zur Trennung. Host-Test vorhanden. |
| W-3 | wichtig | **umgesetzt** | `sensor_addr` wird LSB zuerst übertragen, `payload()` ohne `vt`/`pmsg`. Testvektoren in `tests/gen_vectors.py` aus der Python-Referenz; die Sensor-PAIR_RSP stimmt byte-genau. |
| W-4 | wichtig | **umgesetzt (Variante „werden geliefert“)** | Die Kopplung ändert den Ring nicht, damit keine Messung verloren geht. Das Gateway ordnet zeitlich zu oder verwirft (PROTOCOL 6.2 Regel 0). |
| W-5 | wichtig | **umgesetzt** | Richtungen festgelegt: `c < water_raw` heisst giessen, `c < air_raw` heisst Luft, `c > flood_raw` heisst geflutet (PROTOCOL Kap. 8). So war es im Code bereits (`fl_meas.c`). |
| W-6 | wichtig | **umgesetzt** | Geschütztes TLV `0xA0 hw_rev` per `imgtool --custom-tlv` (Build geprüft: TLV steht im geschützten Bereich). SESSION_INFO hat neu `sec_cnt` bei Offset 48, die INFO-Erweiterung beginnt ab Offset 52. Nach OTA_END prüft der Sensor `hw_rev` (neuer Fehler 0x4A). Ob MCUboot das TLV toleriert, ist PROTOTYP-PRÜFUNG PP-12. |
| W-7 | wichtig | **umgesetzt** | Neues TLV `0x0F led_weekdays` (Bit 0 = Montag) mit Lokalzeit aus TIME_SET. Ein eigener Host-Test fehlt noch; die TLV-Kodierung ist mitgetestet. |
| W-8 | wichtig | **umgesetzt** | MUSS-Regel in PROTOCOL 2.5 Nr. 6: Aus Klartext-ERROR leitet das Gateway keine Zustandsänderung ab. |
| W-9 | wichtig | **umgesetzt** | Die Sitzungsgrenze beträgt jetzt 30 s, die Frist ohne Frame 5 s. Das Gateway SOLL `max` ≤ 110 setzen und je Block quittieren (PROTOCOL 6.2). |
| S-1 | klein | **umgesetzt** | OTA_BEGIN-`sha256` ist der SHA-256 der ganzen Datei. |
| S-2 | klein | **umgesetzt** | Datensätze aus MEASURE werden normal quittiert (6.2). |
| S-3 | klein | **umgesetzt** | Nicht gesendete ids bleiben unverändert (so war es schon im Code, jetzt dokumentiert). |
| S-4 | klein | **umgesetzt** | TIME_SET wird auch bei einer Änderung von `tz_min` gesendet. |
| S-5 | klein | **umgesetzt** | `charge_uc` ist nichtflüchtig und wird nur bei Power-on genullt (Zellwechsel). Sicherung alle 6 h und vor jedem Neustart oder jeder Abschaltung. |
| S-6 | klein | **umgesetzt** | Für das Export-Format wird jetzt auf GATEWAY_API Kap. 9 verwiesen. |
| S-7 | klein | **umgesetzt** | Mehrfaches MEASURE mit Mittelung im Gateway ist in 5.4 erwähnt. |
| S-8 | klein | **angenommen** | Keine Protokolländerung: Die Sensor-ID bleibt die 48-bit-Adresse; die Kollisionsprüfung beim Koppeln macht das Gateway. |
| S-9 | klein | **angenommen** | Keine Änderung. |

## 2 Sicherheitsprüfung (`phase4_sicherheit_kragen_firmware.md`)

### Teil 2 – Firmware/Protokoll

| Nr | Stufe | Antwort | Umsetzung / Nachweis |
|---|---|---|---|
| **F-K1** | **kritisch, VETO** | **umgesetzt – Aufhebung beantragt** | Die Kopplung v2 mit Commitment/Reveal ist umgesetzt (Prinzip BLE Numeric Comparison):<br>• PAIR_REQ = `gateway_id ‖ gw_pub ‖ C` mit `C = SHA-256("fluidi-commit" ‖ gateway_id ‖ gw_pub ‖ gw_nonce)`.<br>• Neu PAIR_REVEAL `{gw_nonce}` erst nach PAIR_RSP.<br>• Der Sensor prüft C; passt C nicht, folgen Abbruch, Fehlversuch und rote LED.<br>• Transkript REQ‖RSP‖REVEAL, info `fluidi-pair-v2`, Protokollversion 2.<br>Erfüllte Bedingungen der Aufhebung:<br>• (1) PROTOCOL 4.2 ist geändert.<br>• (2) Sensor (`fl_app.c` `on_pair`) und Python-Referenz sind umgesetzt; das Gateway `fluidi_gw` stellt der Software-Agent um.<br>• (3) Testvektoren für Commitment, Transkript, Schlüssel, SAS und MACs liegen in `gen_vectors.py`; C-Test gegen die Python-Referenz.<br>• (4) Angriffstest `test_pairing_mitm.py` mit 10 000 Läufen: **0.39 %**; Gegenprobe v1: ≥ 99 %. C-Test: eine Commitment-Verletzung wird abgewiesen. |
| F-W1 | wichtig (Serie kritisch) | **umgesetzt** | Werkzeug und Build:<br>• `flash_sensor.py --lock` verlangt `--expect-key-fp`, liest den in MCUboot eingebauten Schlüssel aus dem Hex und lehnt den DEV-Schlüssel und abweichende Fingerabdrücke ab, bevor etwas geschrieben wird.<br>• Der Fingerabdruck steht im Namen des Werks-Hex.<br>• `make release` bricht ab bei `DEV_ONLY_*` und bei einem Schlüssel im Repository.<br>• `.gitignore` sperrt `*.pem` ausser `DEV_ONLY_*`.<br>Tests: DEV abgelehnt, falscher oder fehlender Fingerabdruck abgelehnt, der echte Werks-Hex mit DEV-Schlüssel ist nicht sperrbar. Der DEV-Schlüssel bleibt Standard für `make` (Labor); für die Serie ist `make release` Pflicht. |
| F-W2 | wichtig | **umgesetzt** | Serien-CCFG (`ccfg_lock`):<br>• Auf FORBID: allowFlashProgram, allowToolsClientMode, allowReturnToFactory, allowDebugPort, Debug-Autorisierung, allowBldr.<br>• ChipErase bleibt erlaubt; es löscht auch die Schlüssel.<br>• WEPRA schützt die Sektoren 0–10 (MCUboot); Sektor 11 (BIMINFO) und die Slots bleiben beschreibbar.<br>• Der CCFG-Sektor ist geschützt.<br>Tests prüfen jedes Feld. PP-9 ist um „OTA und Zähler funktionieren nach der Sperre“ ergänzt. Bit-Bedeutung „sticky-0 = geschützt“ nach `hw_ccfg.h`, am Muster zu bestätigen. |
| F-W3 | wichtig | **umgesetzt** | (a) Beim Start werden zuerst VDD und der Neustartgrund gelesen, Flash erst danach. Nach Brownout oder Unterspannung läuft der Sensor erst ab 2.6 V weiter. Abnormale Neustarts (Watchdog, Brownout, Absturz, ungeplanter Software-Reset) zählt das **Retention-Register PMCTL.AONRSTA1** (TRM 8.4.2; überlebt Reset und Shutdown, im SDK für CC23 nicht belegt). Ab 3 ohne 10 min stabilen Betrieb folgt die Abschaltung ohne Flash-Schreiben.<br>(b) Ist der Taster bei der Abschaltung gedrückt, werden Pull-up und Tasterwecken abgeschaltet; dann weckt nur ein Zellwechsel.<br>(c) Fatale Fehler sind ungeplante Neustarts und werden mitgezählt. Gewollte Neustarts (REBOOT, OTA, Werkseinstellung, Rückfall) setzen das Bit „geplant“.<br>Host-Tests `test_resets` (8 Fälle, u. a. NV-Schreibzahl unverändert). PP-11 neu. |
| F-W4 | wichtig | **umgesetzt** | Der RNG-Rückgabewert wird bei HELLO (kein HELLO_RSP, Trennung), bei `s_nonce` und Füllbyte der Kopplung (Abbruch) geprüft. Host-Test mit RNG-Ausfall im Simulator. |
| F-W5 | wichtig | **umgesetzt** | Gemessen wird nur ohne Verbindung. MEASURE und Tastendruck während einer Verbindung messen nach dem Trennen (Protokoll Ä-8: MEASURE antwortet `{status, seq}`). Das Advertising ist während der Messung angehalten. Die Batteriemonitor-Lesung im Burst ist nur ein Registerzugriff (wenige µs), Burst-Budget 50+250+250 µs < 600 µs. Restrisiko Stack-interner Funk, Messung PP-2. |
| F-L1 | klein | **umgesetzt** | Nach OTA_END liest der Sensor `ih_ver` und den Sicherheitszähler aus Slot 1 und lehnt ab, wenn die Version ≤ laufend oder der Zähler < laufend ist (0x45). BIMINFO belegt: Magic 2 B, Eintrag 10 B (`security_cnt.h`: `BIM_INFO_MAGIC_SZ 2`, `BIM_ITEM_SZ 10`) → höchstens (2048−2)/10 = **204 Einträge**. Der Zählerwert darf ebenfalls höchstens 204 betragen (`security_cnt.c` `MAX_SECURITY_CNT`). Beides steht in `keys/README.md` Regel 5. |
| F-L2 | klein | **abgelehnt für v2 (Begründung)** | Bei 3 Farben bleiben 1/243 je Versuch. Gegen eine Erweiterung sprechen:<br>• Weiss und Cyan sind mit der RGB-LED bei schwacher Zelle unsicher (Blau erst ab 2.65 V, D-010).<br>• Fehlversuche sind sichtbar, das Fenster ist kurz.<br>Am Muster wird die Erkennbarkeit von 4–6 Farben geprüft; die Option bleibt offen. |
| F-L3 | klein | **umgesetzt (Anleitung)** | README Kap. 5: Taster beim Zellwechsel im Prototyp nicht drücken. Die Serien-CCFG hebt das auf. |
| F-L4 | klein | **angenommen** | Keine Änderung. |
| F-L5 | klein | **angenommen** | Keine Änderung. |

### Teil 1 – Kragen (K-1…K-7)

Die Auflagen betreffen Layout, Mechanik und Montage und gehen an Elektronik und Mechanik. Die Firmware-Auflage ist
erfüllt: SENS_PWR nur während der TMP-Wandlung, SDA/SCL im Schlaf low, ein I²C-Versuch je Messung ohne
Wiederholschleife (`fl_hw.c` `tmp1075_read`). Für den Kragentest K-7 („SENS_PWR dauernd high“) ist eine Testfirmware
nötig; sie wird bei Bedarf als Build-Option geliefert.

## 3 Was die Gegenseite (Gateway) umstellen muss

Das ist PROTOCOL.md Kap. 0, Ä-1…Ä-16. Kurz:
- `vt` 0x2t und `proto_max = 2`.
- PAIR_REQ mit Commitment (104 Byte), danach PAIR_REVEAL statt PAIR_SHOW.
- Transkript über drei Teile, info `fluidi-pair-v2` / `fluidi-sess-v2`.
- SESSION_INFO 52 Byte, INFO-Erweiterung ab Offset 52.
- MEASURE-Antwort 5 Byte, Datensatz in der nächsten Sitzung.
- TLV 0x0F, TLV 0xA0 im Image, Fehler 0x4A.
- Fristen wie in Kap. 3.

Referenz und Vektoren: `firmware/tools/fluidi_proto.py`, `firmware/sensor/tests/gen_vectors.py`.

## 4 Runde 2 – Restbefunde (2026-11-07)

Nachweis: `make` 0 Fehler, `make check` grün (1503 C-Prüfungen, 17 + 3 Python-Tests, MITM v2 0.39 %); Gateway-Tests
`firmware/gateway` 62 Tests ok (1 übersprungen). Die Python-Referenz `fluidi_proto.py` ist **unverändert**.

| Nr | Antwort | Umsetzung |
|---|---|---|
| N-1 | **umgesetzt** | Eine Commitment-Verletzung bei PAIR_REVEAL zählt jetzt in `fail_streak` (gemeinsame Funktion `crypto_fail`), so wie PROTOCOL 4.5 und das Gateway. Host-Test: 3 Verletzungen in Folge führen zu `LOCKED`. |
| N-2 | **umgesetzt** | Ab dem Start bis zur ersten bestandenen Lastmessung schreibt die Firmware nichts ins NV (`s_nv_defer`); auch der Datensatz wird erst nach der Lastprüfung geschrieben. Ein POR-Zyklus am Lebensende, bei dem der Ruhewert genügt, die Last aber zusammenbricht, schreibt damit 0 NV-Einträge (Host-Test). PP-11 ist um den Einbruch unter POR, den gemeldeten Neustartgrund und die NV-Schreibzahl je Zyklus ergänzt. |
| N-3 | **umgesetzt (begründet, ohne Warten auf Ereignis)** | Zwischen Advertising-Stopp und erstem Burst liegen konstruktiv ≥ 16 ms (SENS_PWR 1 ms + TMP-Wandlung 15 ms, FW-1). Ein schon geplantes ADV-Ereignis dauert nur wenige ms. Begründung im Code (`fl_app_measure`). Messung bei gleichzeitigem ADV bleibt PP-2. |
| N-4 | **umgesetzt** | Liefert der Batteriemonitor beim Start 0, wird einmal wiederholt; ist der Wert weiter 0, gilt das als Unterspannung (Abschaltung ohne NV-Schreiben, Wecken per Taster). Host-Test. |
| N-5 | **umgesetzt** | PROTOCOL 4.3: Das Gateway verwendet `secrets.token_bytes`/`os.urandom`. |
| R-1 | **umgesetzt** | PROTOCOL 5.1–5.3: Frame-Version 2, `vt` 0x20/0x21/0x22/0x23/0x2F; ERROR hat 2–3 Byte. |
| R-2 | **umgesetzt** | PROTOCOL 5.4: höchstens ein MEASURE je Sitzung, als letzte Anfrage; ein zweites liefert dieselbe `seq`; der Sensor trennt 0.3 s nach der Antwort, wenn kein Frame folgt. |
| R-3 | **umgesetzt** | Einheitlich `info_fmt` 1 (Felder nur angehängt); der Kopf ist korrigiert. |
| R-4 | **umgesetzt** | Nummerierung in Kap. 2.5 korrigiert (5 vor 6); ESP-Reste in 1, 4.1 und 4.3 entfernt. |
| R-5 | **angenommen, keine Änderung** | `SAS_COLORS` in der Referenz ist ASCII („gruen“), die Anzeige macht die PWA. |
