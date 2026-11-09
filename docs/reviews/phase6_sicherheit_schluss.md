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

## Antwort Ersteller (Firmware, 2026-11-09, nur die der Firmware zugewiesenen Befunde; nicht committet)

| Befund | Antwort | Umsetzung / Beleg |
|---|---|---|
| **W-1** | **umgesetzt** | Wie Elektronik W-2 (`phase6_firmware_pruefung_elektronik.md`, Antwort Ersteller): `fl_app_early` in `fl_platform_early_init` **vor** `BLEAppUtil_init` zählt alle abnormalen Neustarts (auch Watchdog/Lockup vor der Initialisierung, nicht nur Abstürze über den Handler) und schaltet beim 3. Start **ohne Flash** ab; keine Doppelzählung mit `fl_app_init`. Host-Test `test_early` (0 NV-, Flash-Schreib- und Löschvorgänge). FMEA **F-67** eingetragen (Vorschlag S 4 / O 2 / D 6 → D 3). PROTOTYP-PRÜFUNG **PT11.07b** im Testplan: TF-2 hat keinen freien Modus (2-bit-Feld belegt, 18 Retention-Bits voll), daher am offenen Muster S2 mit SWD (Haltepunkt in `BLEAppUtil_init`, Fault erzwingen, 3 ×; BLE-NV-Seiten vorher und nachher vergleichen). Eine TF-Variante mit Auslösung vor `stack_ready` ist **nicht** umgesetzt (Grund: kein Retention-Bit frei); bei Bedarf als eigener Auftrag |
| **W-2** | **umgesetzt** (nur der Teil im Flash-Werkzeug; Gateway/PWA macht ein anderer Agent) | `scripts/flash_sensor.py`: Testfirmware wird erkannt an der Build-Nummer 9000–9999 im MCUboot-Kopf von Slot 0 (0x6000, `ih_ver` ab +20, SDK `bootutil/image.h` Z. 141–146 und 159–168) oder an `-tf<n>-` im Dateinamen. `program` läuft nur mit `--testfw <n>` (passende Nummer; `--yes` genügt nicht), `--lock` mit Testfirmware wird immer abgelehnt, `--testfw` an einer Serien-Datei ebenfalls; `--dry-run` zeigt die Erkennung an. Tests `TestTestfirmware` (4) und 2 Tests gegen die echten Werks-Hex der Serie und von TF-1…TF-4. Die FMEA-Zeile „Testfirmware per OTA im Feld“ (S 3 / O 3 / D 5) habe ich **nicht** eingetragen; sie betrifft vor allem die Gateway-Massnahmen (anderer Agent) |
| **K-2** | **umgesetzt** (TESTFIRMWARE.md) | TESTFIRMWARE Kap. 1: 2.0 V, höchstens 2.2 V (CH343) bzw. **2.1 V (PL2303)**, Strombegrenzung **10 mA**, Verweis auf PROGRAMMIEREN v1.2. **Offen ausserhalb der Firmware:** `PROGRAMMIEREN_SENSOR.md` nennt in Regel 2 und Schritt 5 weiterhin „(höchstens 20 mA)“; die Bereinigung gehört der Elektronik bzw. dem Orchestrator |


## Antwort Ersteller (Software, 2026-11-09, Gateway/PWA/Anleitungen; nicht committet)

| Befund | Antwort | Umsetzung / Beleg |
|---|---|---|
| **W-2** (Gateway/PWA) | **umgesetzt** | `fluidi_gw/sensordiag.py` `testfw_of_image`: Build 9000–9999 im **signierten** MCUboot-Kopf (für Testfirmware reserviert; unbekannte Variante = 9) oder Dateiname `-tf<n>-` (PWA sendet ihn als Query `filename`). `api.py` `fw_upload`: ohne neuen Schalter **`allow_testfw`** (`config.py`, `gateway.toml`, Werk `false`) → `403 forbidden` + Ereignis; mit Schalter Abbild-Dokument `testfw: n`, Ereignis „TESTFIRMWARE“. `fw_rollout`: Schalter nochmals geprüft, **genau ein** Sensor (`400`), ausdrückliche Bestätigung `confirm_testfw` = Kennung dieses Sensors (`409 confirmation_required`), Ereignis `fw_rollout_testfw`. PWA `sensors.js`: rote Marke „TESTFIRMWARE TF-n“ und Build-Nummer in der Abbildliste, „Verteilen“ öffnet bei TF ein Sheet (ein Sensor wählen + Kontrollkästchen), Serienabbilder wie bisher. Mock gleich (`--allow-testfw`). OpenAPI (`SensorImage.build/testfw`, `confirm_testfw`, 403), GATEWAY_API 5.4 Pkt. 4, GATEWAY_SETUP 4.2 (Schalter; DEV-Schlüssel am Nutzer-Gateway nicht belassen), TESTFIRMWARE Kap. 4. Tests: `test_api.test_testfw_image_needs_switch_and_confirmation`, `test_mock_api.test_testfw_image`, `diag.test.js` (imageTestfw). FMEA **F-68** eingetragen (S 3 / O 3 / D 5 → D 3 nach Umsetzung) |
| **W-3** | **umgesetzt** | INBETRIEBNAHME Kap. 1 (nur Original-Netzteil Raspberry Pi 12.5 W, Steckdose ausserhalb des Giessbereichs) und Kap. 2 (Warnkasten: nicht zwischen Töpfe/auf Untersetzer/unter hängende Pflanzen, Kabel nicht durch nasse Bereiche, nicht abdecken; bei Wasser nicht anfassen, Sicherung aus, dann ausstecken, Netzteil ersetzen), GATEWAY_SETUP Kap. 1 („Aufstellung und Strom“), FEHLERSUCHE 4.1 Schritt 1. FMEA **F-69** eingetragen (S 8 / O 2 / D 6) |
| **K-3** | **umgesetzt** | `helper.py`: Anfrageordner mit `O_DIRECTORY | O_NOFOLLOW` geöffnet (Ordner selbst kein Symlink), jede Datei mit `O_RDONLY | O_NOFOLLOW | O_NONBLOCK` relativ zum Ordner-fd, `fstat` = reguläre Datei mit einem Link, Grösse ≤ 4096 Byte, sonst verworfen; Löschen nur des Eintrags selbst (`unlink(dir_fd)`, nie das Ziel). Test `test_helper.py` (3): gültige Anfrage, Symlink/FIFO/zu gross verworfen ohne Hängen und ohne Ziel zu berühren, symlinkter Anfrageordner ignoriert |
| **K-4** | **umgesetzt** (Diagnose) / **abgelehnt** (Jetzt messen) | `POST /sensors/{id}/diag`: Mindestabstand **60 s je Sensor** ab dem letzten Auftrag, sonst `429 locked` mit `Retry-After`; laufender Auftrag wird weiterhin zusammengefasst. Gateway und Mock, OpenAPI, GATEWAY_API 5.10. Tests in `test_api.test_sensor_diag`, `test_mock_api.test_sensor_diag`. „Jetzt messen“ unverändert: Doppelaufträge werden schon zusammengefasst, MEASURE ist auf eines je Sitzung begrenzt (PROTOCOL R-2), und nach dem Giessen ist ein sofortiges zweites Messen ein normaler Bedienfall; Grund: Komfort, Energie je Messung wie Diagnose (eine Verbindung), Auslöser nur angemeldete Nutzer |
| **K-6** | **umgesetzt** | INBETRIEBNAHME Kap. 5 Knopfzellenwarnung direkt (Kinder/Haustiere, 144/145), Kap. 7 Sensorkopf nicht übergiessen, nie untertauchen, nicht unter fliessendem Wasser/Spülmaschine, nur Sonde feucht abwischen; PAIRING 3.3 Schritt 4 (giessen auf die Erde, nicht über den Kopf); FEHLERSUCHE 3.8 (Vorbeugen) und 3.4 Schritt 2 + Kap. 5 Zeile „Absturz“: nach Schutzabschaltung weckt ein **kurzer Tastendruck** (Wecken per Taster = Reset-Grund Pin, Zähler 0, `fl_app.c` `boot_shutdown`, `fl_hw.c` Z. 443); erst wenn nichts oder 1 × kurz rot kommt, Zelle wechseln. BATTERIEWECHSEL nicht geändert (Hinweise dort bestehen bereits; K-5 gehört nicht der Software) |

Tests nach Umsetzung: Gateway 114 OK, App JS 17 OK, App Python 63 OK, `test_testfw_eval` 13 OK. `sw.js` Shell `fluidi-frost-v5`.

## Antwort Ersteller (Fertigung, 2026-11-09, Einkauf/Release; nicht committet)

| Befund | Antwort | Umsetzung |
|---|---|---|
| **W-4** | **umgesetzt** | V-Z5c (Silikontrichter mit Feinfilter) aus der Einkaufsliste gestrichen. V-Z5d plant jetzt fest **2 PE-Einwegtrichter** (A/B getrennt, beschriftet, mit dem Beutel entsorgen). Bei bastelgarage und galaxus ist keine Quelle gefunden → Laborhändler offen. |
| **W-5** | **umgesetzt (Kandidat), Bewertung Sicherheit offen** | V-Z7 = **MAPA Solo 977**, Einweg-Nitril, **0.13 mm**, EN ISO 374-1 Typ B, EN ISO 374-5, CE 0075/014/162/08/18/1659. TDS und Beständigkeitstabelle liegen unter `docs/references/MAPA_Solo977_*`, Register VERG-ZUB-GL. Bezug: galaxus-Listing oder bul.ch. **Die Tabelle enthält keine Werte für CAS 1761-71-3 oder 25068-38-6** (nur z. B. Ammoniak 25 %: 16 min) → Bewertung durch die Sicherheit. bastelgarage 421782 ist nur noch für Arbeiten ohne Vergussmasse vermerkt. Status „PFLICHT vor dem ersten Beutel“. |
| **W-6** | **umgesetzt** (Bemerkung) / **Bezugsquelle offen** | S1 enthält jetzt: Händler-Eigenware in Blisterpackung bevorzugen; Wareneingang mit Originalverpackung, Los-/Datumscode, 3 Zellen ≤ 3.2 mm, Leerlaufspannung; lose Zellen in die abschliessbare Box. Ob galaxus 61927007 Eigenware oder Marktplatzware in Einzelblistern ist, lässt sich nicht abrufen (Bot-Sperre) → beim Bestellen von Hand prüfen. Eintrag „PT Wareneingang“ im Testplan: Testplan-Verantwortliche. |
| **W-7** | **umgesetzt** (Generator; wirksam beim nächsten Erzeugen) | Neu `0_SICHERHEIT.md` im Paket: Knopfzellen (144/145, Originalverpackung), Verguss und Kleber mit SDB, PSA vor dem ersten Beutel, Programmieren nur nach Anleitung (Weg B 2.0/2.1 V, 10 mA), Testfirmware und DEV-Hex nie an Endnutzer, Netzteil nicht im Giessbereich. Dazu der **D-030-Auszug, automatisch aus DECISIONS.md**. Das README verweist zuoberst darauf. `6_anleitungen/sdb/` enthält ER2223 A (EN, SV), B (HU, als „nicht ausreichend“ markiert), TDS ER2223, SDB und TDS UHU sowie die Handschuhdokumente. |
| **K-1** | **umgesetzt** | EU-DoC RP-001257-CF-3 (11.08.2026) unter `docs/datasheets/RaspberryPi_12W5-MicroUSB-PSU_EU-DoC_RP-001257-CF-3.pdf`, Register GW-PSU, BOM_GATEWAY G2 mit Wareneingangsprüfung. Die Registerlücke G2 ist geschlossen. |
| **K-7** | **umgesetzt** | V-Z7…V-Z10 tragen den Status „PFLICHT vor dem ersten Beutel“. V-Z8: vorhandene Brille nur als Korbbrille EN 166 **Kennzeichnung 3** + Visier (Kandidat 3M 2890SA gasdicht + BGS Visier, galaxus; Kennzeichnung am Artikel prüfen). V-Z9 Augenspülflasche 500 ml + Schürze, V-Z10 Halbmaske A2P2 bzw. Absaugung. EINKAUFSLISTE Kap. 5 ist ergänzt. |
