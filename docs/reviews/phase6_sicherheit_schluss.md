# Phase 6 – Schlussprüfung Sicherheit (Fertigungspaket Rev C)

| | |
|---|---|
| Prüfer | Sicherheit (frischer Kontext, Vetorecht) |
| Datum | 2026-11-09 |
| Stand | Git `f047cf5`, Paket `production/rev-C` (README: Git-Stand `9c39ce8`, `make_release_rev_c.py --check` = „Paket aktuell“) |
| Umfang | (1) PROGRAMMIEREN_SENSOR v1.2 + Programmieradapter Kap. 9 (PL2303), (2) Testfirmware TF-1…4, (3) `fl_fault_handler`/Assert-Pfad, (4) Endnutzer-Anleitungen, (5) Einkaufsliste Verguss/Schutzausrüstung, Zellen, Netzteil G2, (6) Release-Paket/Quellarchiv, (7) Gateway Root-Helfer LED und Diagnose-API |
| Ergebnis | **Kein Veto.** 0 kritisch, 7 wichtig, 7 klein |

## 0 Selbst geprüft

| Was | Ergebnis |
|---|---|
| `Prolific_PL2303GS_Datasheet_Rev1.0.4.pdf` S. 39 Tab. 11-1/11-2a/11-2b (pdftotext) | VDD_IO abs. max −0.3 … VIN + 0.3 V; VDD_IO 1.8 … VIN + 0.3 V; VIL ≤ 0.4 V; VOL/VOH ohne Laststrom; IDD max 15 mA – stimmt mit README Kap. 9.1 überein |
| `simulation/spice/programmer/prog_uart_pl2303_report.txt` und `prog_uart_pl2303_pwr.cir` gelesen | A2p 2.2 V: +1 mV → Grenze 2.1 V richtig gezogen; USB ziehen ohne R2 bis 1.06 V über VIN, mit 470 Ω ≤ 0.014 V (ohne Sensor) bzw. −0.005 V (mit Sensor). Modell konservativ (Parasitärdiode, VIO ohne Last) |
| R2 470 Ω 0805 1/8 W | 2.0²/470 = 8.5 mW; Einzelfehler U3 durchlegiert 3.3²/470 = 23 mW – unkritisch |
| `firmware/sensor`: `make test` (mit `~/fluidi-tools/env.sh`) | Serie 1569, TF-1 24, TF-2 77, TF-3 25, TF-4 14 Prüfungen bestanden; Flash-Werkzeug, MITM 3 Tests ok |
| `firmware/gateway`: `python3 -m unittest discover -s tests` | 109 Tests ok |
| `production/rev-C`: `sha256sum -c SHA256SUMS`, `make_release_rev_c.py --check` | alle ok, Paket aktuell |
| Quellarchiv `8_quellcode/fluidi_quellcode_firmware_app.tar.gz` entpackt (Scratchpad), 197 Dateien, grep `PRIVATE KEY`/`BEGIN EC/RSA/OPENSSH`, Dateinamen `*.pem/*.key/*.p12/*.crt` | **keine privaten Schlüssel**; `firmware/sensor/keys/` enthält nur `README.md`. Fest codierte Schlüssel nur als deterministische Testvektoren (`derive_private_key(11…)`, `0x1F2E…`) in Tests – öffentlich und gewollt |
| Makefile/`flash_sensor.py` | `TESTFW` nur mit `DEV_ONLY_*`, `make release` bricht mit `TESTFW` und DEV-Schlüssel ab, Serien-`BUILD_NO` ≥ 9000 abgelehnt; `check_lock_key` lehnt DEV-Schlüssel ab → TF kann nie gesperrt werden |
| Gateway `mcuboot.parse` | ohne `fw_pubkey` wird jedes Abbild abgelehnt (fail-closed) |
| Gateway-PKI `pki.py` | CA mit kritischer NameConstraint `fluidi.local`, pathlen 0, CA-Schlüssel nur im RAM – Aussage in INBETRIEBNAHME Kap. 3 „gilt nur für fluidi.local“ ist belegt |
| Netzteil G2 (Web, 2026-11-09) | Raspberry Pi 12.5 W Micro-USB, EU-Ausführung SC0624, 2-Pol-Eurostecker; EU-Konformitätserklärung öffentlich (RP-001257) |

## 1 Programmieren mit PL2303 (PROGRAMMIEREN v1.2, Adapter-README Kap. 9)

**Veto PS-K1 bleibt intakt.** Geprüft gegen `phase5_programmer_sicherheit.md` (Bed. 1–3) und `phase5_sicherheit_runde3.md`
(Z5-1…Z5-7):

- Regel 1: „Nie mit eingesetzter Zelle“, Speisung nur über Dummy-Zelle/-Scheibe, keine Prüfklemme, kein Draht am
  Minuspad, keine Speisung über TP1/TP2, Ausnahme nur ST-Z5 nach Z5-1…Z5-7 – vorhanden.
- Kap. 2: Dummy-Scheibe „Pflicht“ für Weg B; Kap. 5 Schritt 2 „Ohne Scheibe kein Weg B“; Schritt 8 feste Reihenfolge
  (a) Netzteil aus und ab → (b) Scheibe heraus → (c) Draht weg; Schritt 9 Zellen < 2.6 V entsorgen – vorhanden.
- PL2303-Ergänzungen (USB zuerst stecken, Netzteil zuletzt ein; Netzteil zuerst aus, USB zuletzt ziehen) sind in
  Schritt 5 und 8 sauber in die PS-K1-Reihenfolge eingefügt und widersprechen ihr nicht. Ein Vertauschen gefährdet nur
  das Board (8.90 CHF), keine Zelle im Kreis – Bewertung im README Kap. 9.4 ist richtig.
- Weg A: B5 (R2 bestückt, Kontrollmessung) deckt das Ziehen der USB bei gesteckter Dummy-Zelle ab; ohne R2 ist die
  Ersatzregel genannt. PS-W2 (Stifte flach/gerundet) und PS-W3 (3.0–3.2 mm) stehen jetzt auch im README Kap. 4/7.
- Rückspeisung PL2303 → Sensor bei offenem VCCIO wird mit der Eingangsprüfung 9.3 Schritt 1 (≤ 0.10 V) ausgeschlossen.

Kein Befund ausser Textabgleich in K-2.

## 2 Befunde

### W-1 · wichtig · Reset-Schleife vor `fl_app_init` wird nicht gezählt (Lücke in F-W3 nach O-5)

**Befund:** `fl_app_init` (Zählung abnormaler Starts, Abschaltung nach 3, Unterspannungsprüfung) läuft erst in
`stack_ready` → `fl_platform_start_app` (`platform/cc23/fl_ble.c` Z. 232–248, `fl_hw.c` Z. 489–498), also **nach** der
ganzen BLE-Stack-Initialisierung. Jeder HardFault, BLE-Assert (z. B. out of memory, RNG, ICall) oder Stacküberlauf
**davor** geht seit O-5 über `fl_fault_handler` in einen **sofortigen** Systemreset; beim nächsten Start wird wieder
nicht gezählt. Ergebnis: unbegrenzte Reset-Schleife mit der Periode MCUboot-Prüfung + Stack-Init (Bruchteile einer
Sekunde) statt bisher 60 s (MCUboot-Watchdog nach Spin). Der mittlere Strom ist ähnlich wie beim alten Spin (CPU
aktiv, mA-Bereich → CR2032 in Tagen leer, Sensor „tot“), **neu ist die ≈ 100-fache Zahl der Starts**. Ob die
Stack-Initialisierung (`nvocmp`, 2 Seiten BLE-NV, `FL_BLENV_BASE`) je Start Flash schreibt, ist nicht belegt
(**ANNAHME**: im Normalfall nein; bei inkonsistenter NV-Seite Kompaktierung möglich). Kein Brand-/Ladepfad, eine
einzelne Primärzelle wird nicht umgepolt; Folge ist Tiefentladung im Gerät (FMEA F-13) und möglicher Flash-Verschleiss.
TF-2 deckt diesen Pfad nicht ab (Fehler erst nach der Taste, also nach `fl_app_init`).

**Vorschlag:**
- Zählung in den Fehlerpfad bzw. ganz an den Anfang ziehen: `fl_fault_handler` erhöht den Zähler `FL_RET_ABN_MASK` im
  Retention-Register selbst (nur Registerzugriffe, kein Stack nötig), und `fl_platform_early_init` (vor
  `BLEAppUtil_init`) prüft Resetgrund + Zähler und schaltet bei ≥ 3 ohne Flash ab (gleiche Logik wie
  `boot_shutdown`). Doppelzählung mit `fl_app_init` vermeiden.
- **PROTOTYP-PRÜFUNG** (Testplan, neu, z. B. PT11.07b): TF-2-Variante, die beim Start **vor** `BLEAppUtil_init` bzw. vor
  `stack_ready` einen HardFault auslöst (Aktivierung über ein Retention-Bit aus der Tastensequenz); Kriterium:
  Abschaltung nach 3 Starts, 0 Flash-Schreibvorgänge (auch BLE-NV, Lesevergleich der 2 Seiten vorher/nachher),
  Mittelstrom.
- FMEA (`phase5_fmea_light.md`) neuer Eintrag „Absturz vor Initialisierung → schnelle Reset-Schleife“: Vorschlag
  S 4 / O 2 / D 6 (Skala 1–10), nach Umsetzung D 3.

### W-2 · wichtig · Testfirmware kann über OTA ohne Kennzeichnung an Nutzersensoren gehen

**Befund:** Die Schutzkette (Makefile, `make release`, `--lock`) verhindert Testfirmware im **Serienstand mit
Produktionsschlüssel** zuverlässig. Für die Muster gilt das nicht: TESTFIRMWARE Kap. 4 verlangt, dass das Gateway den
**DEV-Pubkey** als `fw_pubkey` führt, und solange die ausgelieferten 10–15 Sensoren DEV-signiert sind (Musterstand,
`FIRMWARE_HINWEIS.md`), nimmt deren MCUboot jedes TF-Abbild an. Am Gateway prüft `POST /firmware/sensor-images`
(`api.py` Z. 728–760) nur Signatur, Hardware-Rev., Sicherheitszähler und Version, **nicht** die Build-Nummer 9000–9999;
die Liste der Abbilder in der PWA (`app/js/sensors.js` Z. 98) zeigt weder Build noch eine TF-Marke, und
`POST /firmware/rollout` warnt nicht. `flash_sensor.py program` warnt bei einem TF-Hex ebenfalls nicht. Die rote Marke
erscheint erst **nach** der Verteilung am Sensor. Gefährdung gering (TF-3: Feuchtewerte nur informativ → falsche
Giesshinweise, Mehrstrom µA; TF-1/TF-2 nur über Tastensequenz: Hänger/Abschaltung), aber die Projektregel „nie mit
Werksfirmware verwechseln“ ist am Verteilpunkt nicht umgesetzt.

**Vorschlag:**
- Gateway: Abbilder mit Build 9000–9999 beim Hochladen markieren (`testfw: n` im Abbild-Dokument), in der PWA rot
  „TESTFIRMWARE TF-n“ anzeigen, Rollout nur mit ausdrücklicher Bestätigung („Testfirmware an Sensor X verteilen“) und
  nur an einzeln gewählte Sensoren; ohne Konfigurationsschalter `allow_testfw = true` ganz ablehnen.
- `flash_sensor.py`: Dateiname `-tf<n>-` oder Build 9xxx im Abbildkopf → Warnung und zusätzliche Bestätigung.
- Nach Abschluss der Musterprüfung: `fw_pubkey` am Nutzer-Gateway nicht auf DEV lassen (Hinweis in GATEWAY_SETUP).

### W-3 · wichtig · Gateway und Netzteil: kein Hinweis auf Giesswasser, Aufstellung „in der Nähe der Pflanzen“

**Befund:** INBETRIEBNAHME Kap. 1/2 empfiehlt eine Steckdose bzw. das Gateway „in der Nähe der Pflanzen“ und warnt nur
vor Heizkörper und Sonne. In INBETRIEBNAHME, GATEWAY_SETUP und FEHLERSUCHE fehlt jeder Hinweis auf Wasser (grep
„wasser/giess/tropf/feucht“: nur Feuchteindex und Giesshinweise). Das Netzteil ist das einzige Teil mit 230 V; auf
der Fensterbank zwischen Töpfen und Untersetzern ist Giess- und Kondenswasser der naheliegende Fehlgebrauch.

**Vorschlag (INBETRIEBNAHME Kap. 2, FEHLERSUCHE Kap. 4.1, GATEWAY_SETUP):**
- „Gateway, Netzteil und Steckdose **nicht im Giessbereich**: nicht zwischen Töpfe, nicht auf oder neben Untersetzer,
  nicht unter hängende Pflanzen; Kabel nicht durch nasse Bereiche führen. Nicht abdecken.“
- „Nur das mitgelieferte Netzteil verwenden (5 V, Micro-USB, Raspberry Pi 12.5 W).“
- „Ist Wasser auf Netzteil oder Steckdose gelangt: nicht anfassen, Stromkreis über die Sicherung abschalten, erst dann
  ausstecken; Netzteil ersetzen.“

### W-4 · wichtig · V-Z5c Silikon-Trichter mit Edelstahl-Feinfilter – nicht freigegeben für Härter B

**Befund:** MA-5 (`phase6_vergussmasse_sicherheit.md`) und Konzept 7.1 V-Z5 verlangen **2 PE-Trichter**. Bestellt werden
soll ein Silikon-Resin-Trichter **mit Edelstahl-Feinfilter** (bastelgarage 424244). Für Silikon fehlt ein
Beständigkeitsnachweis gegen den Amin-Härter (CAS 1761-71-3, ätzend, SDB B); das Feinfilter staut die Flüssigkeit
(Überlaufen in der Auffangwanne möglich) und hält ätzenden Härter zurück, der danach gereinigt werden muss
(zusätzliche Hautexposition). Ein einzelner Trichter für A und B führt zudem zu Mischresten und Aushärtung im Filter.

**Vorschlag:** V-Z5c **streichen**. In V-Z5d **zwei PE-Einwegtrichter** (je einer für A und B, beschriftet, nach dem
Abfüllen mit dem Beutel entsorgt) fest einplanen. Falls der Silikontrichter trotzdem beschafft wird: nur für Teil A,
**Filter entfernt**, nie für Teil B.

### W-5 · wichtig · V-Z7 Handschuhe ohne Hersteller, Dicke und EN ISO 374 erfüllen Bedingung D-030 Nr. 1 nicht

**Befund:** Freigabebedingung R2.4 Nr. 1 (D-030): „Beständigkeitsliste der Handschuhe abgelegt“ vor dem ersten Beutel;
K-3: Nitril ≥ 0.1 mm, doppelt. Der gelistete Artikel (bastelgarage 421782) nennt weder Hersteller noch Wandstärke noch
EN ISO 374 – eine Beständigkeitsliste ist damit nicht beschaffbar. Die Liste markiert das zwar als „Freigabe
Sicherheit“, als Kaufposition ist sie aber nicht freigabefähig.

**Vorschlag:** Nur Einweg-Nitrilhandschuhe mit benanntem Hersteller, Wandstärke ≥ 0.1 mm, Kennzeichnung
**EN ISO 374-1** und Permeationsdaten des Herstellers für die Härter-/Harzbestandteile (CAS 1761-71-3, 25068-38-6) oder
ersatzweise für Amine/Epoxidharze generell; Datenblatt nach `docs/references/` und Register. Bis dahin ist V-Z7 nur für
Arbeiten ohne Vergussmasse zulässig. Kein Veto, weil die Bedingung „vor dem ersten Beutel“ schon besteht und die
Masse frühestens in 8 Wochen eintrifft.

### W-6 · wichtig · S1 Zellen: Marktplatz-Drittanbieter, Echtheit und kindergesicherte Verpackung nicht belegt

**Befund:** S1 = galaxus 61927007, „Panasonic CR2032 Lithium 48 Knopfbatterien“, Auszug „wenige Packungen,
Drittanbieter“. BATTERIEWECHSEL verspricht „Originalverpackung (kindergesichert)“ und schreibt „nur Panasonic CR2032“.
Ob die 48er-Packung aus Einzelblistern besteht oder lose Zellen im Tray enthält, ist unbekannt (**ANNAHME** offen).
Marktplatzware hat ein höheres Fälschungsrisiko; Fälschungen weichen bei Kapazität, Dicke (Clip, max. 3.2 mm laut
`Panasonic_CR2032_Datasheet_2026-02.pdf` S. 1) und Dichtung ab. Lose Zellen im Haushalt sind das Hauptrisiko der
Knopfzelle (Verschlucken).

**Vorschlag:**
- Bevorzugt Händler-Eigenware (nicht Marktplatz) in **Blisterpackungen**; sonst Wareneingangsprüfung:
  Originalverpackung Panasonic, Los-/Datumscode, Dicke 3 Zellen stichprobenweise ≤ 3.2 mm, Leerlaufspannung, keine
  Beschädigung. Lose oder nicht kindergesicherte Zellen in einer **abschliessbaren Box** lagern (wie V-Z4).
- Ausweichlösung Varta (Bemerkung S1): nur mit abgelegtem Datenblatt und Entscheid D-006-Änderung.
- Wareneingangsprüfung in den Testplan (PT Wareneingang) aufnehmen.

### W-7 · wichtig · Release-Paket: kein Sicherheitsabschnitt auf Paketebene, Sicherheitsdatenblätter fehlen

**Befund:** `production/rev-C/README.md` enthält keinen Sicherheitshinweis (grep „sicherheit/knopfzelle/warn“: 0
Treffer). Die Hinweise stehen verteilt in `5_firmware/PROGRAMMIEREN_SENSOR.md` Kap. 1, `6_anleitungen/BATTERIEWECHSEL.md`,
`6_anleitungen/MONTAGE_SENSOR.md` Kap. 3a, `7_programmieradapter/README.md` Kap. 2.3/9. MONTAGE Kap. 3a verlangt die
SDB A/B ausgedruckt am Arbeitsplatz, das Paket enthält aber kein SDB (`docs/references/Electrolube_ER2223-Part*_SDS*`
fehlen), und die Sperrbedingungen von D-030 (vor dem ersten Beutel: SDB B in Landessprache, Handschuhliste,
Schutzausrüstung) sind auf Paketebene nicht sichtbar. Wer nur das Paket bekommt, sieht die Vetobedingungen nicht.

**Vorschlag:** Im Generator `production/make_release_rev_c.py` einen Abschnitt „Sicherheit zuerst“ in die README
aufnehmen (oder `0_SICHERHEIT.md`) mit: Knopfzelle (Verschlucken, Notruf 145/144, Originalverpackung,
`BATTERIEWECHSEL`), Programmieren nie mit Zelle / Weg B nur mit Dummy-Scheibe (PS-K1), Testfirmware nie ausliefern,
Verguss nur nach D-030 Bed. 1–3 (SDB B DE/EN/FR/IT **noch ausstehend**, Handschuhliste, PSA), Gateway-Netzteil nicht im
Giessbereich (W-3). SDB ER2223 A (EN) und B (HU, mit Vermerk „nicht ausreichend, DE-Fassung Pflicht“) in
`6_anleitungen/` mitkopieren.

### K-1 · klein · G2 Netzteil: Bewertung – zulässig, Nachweis ablegen

**Bewertung:** Original-Netzteil des Pi-Herstellers (12.5 W Micro-USB, EU-Ausführung SC0624, 5.1 V/2.5 A,
2-Pol-Eurostecker, passt in CH-Steckdosen) über einen offiziellen Händler. Hersteller veröffentlicht eine
EU-Konformitätserklärung (RP-001257) und regionale Zulassungen (pip.raspberrypi.com). Gegenüber einem No-Name-Netzteil
ist das Risiko gering; der fehlende Nachweis im Repo ist ein Dokumentationsmangel, kein Sicherheitsmangel.
**Vorschlag:** DoC und Produktbrief nach `docs/references/` + INDEX.csv (F-8 schliessen). Wareneingang: Typ/Kennzeichnung
(CE, Herstellername), Gehäuse und Kabel unbeschädigt, Stecker 2-polig Typ C; kein Ersatz durch Fremdnetzteile.

### K-2 · klein · Grenzwerte Weg B nicht überall gleich

TESTFIRMWARE Kap. 1 nennt für Weg B „2.0 V (höchstens 2.2 V)“ ohne die PL2303-Grenze 2.1 V und hält fest, dass
PROGRAMMIEREN Regel 2 „höchstens 20 mA“ sagt, während EP-03 10 mA verlangt. **Vorschlag:** Beide Dokumente
vereinheitlichen: 2.0 V, höchstens 2.2 V (CH343) bzw. 2.1 V (PL2303), Strombegrenzung **10 mA** (ohne „höchstens 20 mA“).

### K-3 · klein · Root-Helfer liest Anfragen ohne Datei-Typ- und Grössenprüfung

`helper.py` `main()` liest jede `*.json` in `/var/lib/fluidi/requests` als root mit `read_text()`. Der Ordner gehört dem
Dienstbenutzer. Ein kompromittierter Dienst könnte dort eine FIFO oder einen Symlink auf `/dev/zero` ablegen → der
Root-Helfer hängt bzw. belegt Speicher (nur DoS, keine Rechteausweitung; Inhalte gelangen nicht zurück). Die neue
LED-Aktion selbst ist sauber (Zustand gegen feste Tabelle, feste sysfs-Pfade); `ExecStopPost=+… -I … led off` hat
keine Eingabe, `-I` verhindert Modul-Nachladen aus dem Arbeitsverzeichnis – in Ordnung. **Vorschlag:** `os.open(…,
O_RDONLY | O_NOFOLLOW | O_NONBLOCK)`, `fstat` = reguläre Datei, Grösse ≤ 4 kB, sonst verwerfen.

### K-4 · klein · Diagnose-API ohne Mindestabstand je Sensor

`POST /sensors/{id}/diag` (Sitzung + CSRF + Origin, ohne elevate) ist für die reine Leseabfrage angemessen; laufende
Jobs werden zusammengefasst, gespeichert werden höchstens 50 je Sensor, `GET …/diag` ist nicht öffentlich (Dashboard
kann nicht lesen). Ein angemeldeter Client kann aber nach Abschluss sofort erneut auslösen (je eine BLE-Verbindung,
Energie wie „Jetzt messen“). **Vorschlag:** Mindestabstand je Sensor (z. B. 60 s) oder letztes Ergebnis < 10 min
zurückgeben; gleiches für „Jetzt messen“, falls nicht vorhanden.

### K-5 · klein · Batteriefachschraube ist nicht unverlierbar

Einkaufsliste S3 heisst „Schraube unverlierbar Batteriefach“, BATTERIEWECHSEL Schritt 2 sagt „sonst fällt die Schraube
heraus“ und empfiehlt eine Ersatzschraube. **Vorschlag:** Bezeichnung in der CSV korrigieren („Batteriefachschraube“);
in BATTERIEWECHSEL ergänzen: „Ersatz- und lose Schrauben wie Zellen ausser Reichweite von Kindern; ohne Schraube Sensor
nicht benutzen“ (die Regel „verschraubt“ steht schon im Warnkasten).

### K-6 · klein · Endnutzer-Anleitungen: Feuchte am Kopf, Knopfzellenhinweis, Abschaltung nach Absturz

- Hinweis fehlt: Sensorkopf beim Giessen nicht übergiessen, Sensor nie untertauchen oder unter fliessendem Wasser bzw.
  in der Spülmaschine reinigen; nur die Sonde mit feuchtem Tuch (INBETRIEBNAHME Kap. 7, PAIRING Kap. 3.3 Schritt 4,
  BATTERIEWECHSEL Schritt 1).
- INBETRIEBNAHME Kap. 1/5: neben dem Verweis auf BATTERIEWECHSEL eine Zeile „Knopfzellen ausser Reichweite von Kindern;
  verschluckt → sofort 144/145“ direkt einfügen.
- FEHLERSUCHE Kap. 3.4/5 „Absturz“: nach der Abschaltung wegen Reset-Schleife weckt ein kurzer Tastendruck; erst wenn
  nichts kommt, Zelle wechseln (verhindert unnötig weggeworfene Zellen).

Sonst nichts Gefährliches empfohlen: Kein Metallwerkzeug, Fach immer verschraubt, Wasser im Kopf → Zelle heraus und
melden, keine Aufforderung zum Laden/Erwärmen; Zertifikat mit Fingerabdruck vom Zettel, „Warnung nie wegklicken“,
Passwort ≥ 10 Zeichen, Sperre nach 5 Fehlversuchen – angemessen.

### K-7 · klein · Einkaufsliste: Pflicht-PSA als solche kennzeichnen

V-Z8…V-Z10 stehen als „Quelle offen“ bzw. „entfällt, falls vorhanden“. **Vorschlag:** In Kap. 5 ergänzen: „Pflicht vor
dem Öffnen des ersten Beutels (D-030 Bed. 1). Eine vorhandene Brille gilt nur als Korbbrille nach EN 166 mit
Kennzeichnung 3 (Flüssigkeiten), dazu Visier.“ Ebenso V-Z9 Augenspülflasche und V-Z10 Halbmaske A (bzw. Absaugung,
SDB B Abschn. 7.1/8.2).

## 3 Fault-/Assert-Handler (Auftrag Punkt 3) – Zusammenfassung

- `fl_fault_handler` (`fl_hw.c` Z. 524–529): nur Registerzugriffe, kein Flash, kein Stack; Lockup führt ebenfalls zu
  Reset → Grund hardfault. Gut.
- Nach `fl_app_init`: Abschaltung nach 3 abnormalen Starts **ohne** Flash-Schreiben (`fl_app.c` Z. 798–805), Wecken
  nur per Taster, klemmender Taster → kein Wecken (`fl_hw.c` Z. 453–456). Flash-Schreibzahl je Episode ≤ wenige
  Einträge, durch TF-2 messbar. Unterspannung vor jeder Schreiboperation geprüft. Tiefentladung durch die Schleife
  damit begrenzt.
- Lücke: Abstürze **vor** `fl_app_init` → W-1. Unverändert offen (O-5 „bleibt“): MCUboot-Faults (60-s-Watchdog-
  Schleife ohne Spannungsprüfung) und SDK-Schleifen ohne Assert-Weg (10 min). Beides wie W-1 Tiefentladung, kein
  Brandpfad; in FMEA mit W-1 erfassen.

## 4 Testplan- und FMEA-Ergänzungen (bitte aufnehmen)

| Nr | Inhalt | Quelle |
|---|---|---|
| PT neu (W-1) | HardFault vor `stack_ready`: Abschaltung nach 3 Starts, 0 Flash-Schreibvorgänge inkl. BLE-NV, Mittelstrom | PROTOTYP-PRÜFUNG |
| PT neu (W-6, K-1) | Wareneingang Zellen (Original, Verpackung, Dicke, Spannung) und Netzteil (Kennzeichnung, Unversehrtheit) | Sichtprüfung |
| bestehend | PL2303: VIO/VIN beim USB-Ziehen mit Oszilloskop (README 9.4), Eingangsprüfung 9.3 je Board, PA-7 | PROTOTYP-PRÜFUNG |
| FMEA neu | Absturz vor Init → Schnellschleife (W-1); Testfirmware per OTA im Feld (W-2, Vorschlag S 3 / O 3 / D 5); Wasser am Gateway-Netzteil (W-3, Vorschlag S 8 / O 2 / D 6) | `phase5_fmea_light.md` |

## 5 Ergebnis

**Kein Veto.** Kein Befund eröffnet einen Lade- oder Brandpfad für die Zelle, die Auflagen aus Veto PS-K1 sind in
PROGRAMMIEREN v1.2 vollständig erhalten, das Quellarchiv enthält keine privaten Schlüssel. W-4, W-5 und K-7 betreffen
die bereits geltende Sperrbedingung „vor dem ersten Beutel“ (D-030) und müssen vor dem Öffnen eines Beutels erledigt
sein. W-3 und W-7 sollen vor der Übergabe an Endnutzer umgesetzt werden, W-1 und W-2 vor der Serienfreigabe der Firmware
(W-2 spätestens vor dem ersten OTA einer Testfirmware an vergossene Muster).

Bitte je Befund *umgesetzt* / *abgelehnt (Grund)*.

Quellen Web (2026-11-09): [Raspberry Pi 12.5W Micro USB Power Supply](https://www.raspberrypi.com/products/micro-usb-power-supply/),
[EU-Konformitätserklärung RP-001257](https://pip-assets.raspberrypi.com/categories/499-approvals/documents/RP-001257-CF-3-EU%20CE%20Declaration%20of%20Conformity.pdf),
[element14 SC0624 (EU-Stecker)](https://au.element14.com/raspberry-pi/sc0624/power-supply-unit-12-5w-eu-raspberry/dp/383850202).
