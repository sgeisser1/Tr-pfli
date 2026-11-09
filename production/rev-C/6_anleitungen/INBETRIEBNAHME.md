# fluidi – Inbetriebnahme: Gateway und erster Sensor

| | |
|---|---|
| Dokument | `docs/manuals/INBETRIEBNAHME.md` |
| Version | 0.2 (Phase 6: Sicherheit W-3/K-6, Red Team W-5) |
| Datum | 2026-11-09 |
| Für wen | Alle, die fluidi im Büro einrichten. Keine Fachkenntnisse nötig. |
| Gilt für | Gateway-Software `firmware/gateway/` 0.5.0, App `app/`, Sensor-Firmware 0.1.0 |
| Status | Erstellt nach dem Programmcode, **noch nicht am echten Gerät durchgespielt** (PROTOTYP-PRÜFUNG) |

fluidi besteht aus zwei Teilen:

- dem **Gateway** – ein kleines Kästchen mit Netzteil. Es empfängt die Messwerte der Sensoren per Funk (Bluetooth),
  speichert sie und zeigt sie in der App. Es arbeitet nur im eigenen WLAN, ohne Cloud.
- den **Sensoren** – Stäbe, die in die Blumenerde gesteckt werden. Sie messen die Feuchte und laufen mit einer
  Knopfzelle CR2032.

Die **App** ist eine Webseite auf dem Gateway (`https://fluidi.local`), die man auf dem Handy wie eine App auf den
Startbildschirm legen kann.

Verwandte Anleitungen: Koppeln und Kalibrieren ausführlich in `PAIRING_KALIBRIERUNG.md`, Probleme in
`FEHLERSUCHE.md`, Batteriewechsel in `BATTERIEWECHSEL.md`. Die technische Installation des Gateways (Software auf
die SD-Karte bringen) steht in `GATEWAY_SETUP.md` und ist Sache einer technisch versierten Person.

---

## 1 Was Sie brauchen

- das **Gateway** mit eingesetzter SD-Karte und dem **mitgelieferten Netzteil** (Raspberry Pi Original 12.5 W,
  5 V, Micro-USB). **Nur dieses Netzteil verwenden** – kein anderes Handy-Ladegerät, keine Mehrfachsteckdose am
  Fensterbrett.
- den **Zettel aus der Installation** mit **Einrichtungscode** (6 Ziffern, z. B. `123-456`) und
  **CA-Fingerabdruck** (lange Zeichenfolge). Beides zeigt das Installationsskript am Ende an (`GATEWAY_SETUP.md`
  Kap. 4). **ANNAHME:** Wer das Gateway installiert, übergibt diesen Zettel zusammen mit dem Gerät.
- ein **Handy** (Android mit Chrome oder iPhone mit Safari) oder einen PC, im **gleichen WLAN** wie das Gateway
- mindestens einen **Sensor** und eine neue Knopfzelle **CR2032** (falls noch keine eingesetzt ist)
- eine Steckdose mit gutem WLAN-Empfang, **ausserhalb des Giessbereichs** (Kap. 2)
- im **Firmen-WLAN:** die Vorabprüfung aus `GATEWAY_SETUP.md` Kap. 1.1 ist gemacht (Geräte im WLAN dürfen sich
  gegenseitig erreichen, `fluidi.local` wird aufgelöst). Für das Büro-WLAN des Auftraggebers hat der Auftraggeber
  mDNS bestätigt; nach einem WLAN-Wechsel oder an einem anderen Standort die Prüfung wiederholen.

Das Gateway hat **keine eigene Uhr mit Batterie**. Es holt die Uhrzeit aus dem Internet (NTP) über das WLAN. Fällt
das einmal aus, übernimmt es die Uhrzeit Ihres Handys, sobald Sie die App öffnen und angemeldet sind (Kap. 8).

## 2 Gateway aufstellen und einschalten

1. Gateway im selben Raum wie die Pflanzen aufstellen, aber **nicht im Giessbereich**:

   > **Achtung – Netzteil und Wasser.** Das Netzteil ist das einzige Teil mit Netzspannung (230 V).
   > - Gateway, Netzteil und Steckdose **nicht zwischen Töpfe, nicht auf oder neben Untersetzer, nicht unter
   >   hängende Pflanzen** und nicht auf die Fensterbank, wo gegossen wird oder Kondenswasser steht.
   > - Kabel nicht durch nasse Bereiche führen. Gateway nicht abdecken, nicht auf einen Heizkörper und nicht in die
   >   pralle Sonne stellen.
   > - Ist Wasser auf Netzteil oder Steckdose gelangt: **nicht anfassen**, zuerst den Stromkreis an der Sicherung
   >   abschalten, erst dann ausstecken. Netzteil ersetzen (nicht trocknen und weiterverwenden).

   Die Funkreichweite zu den Sensoren hängt vom Raum ab; ob sie genügt, sehen Sie später in der App (Kap. 7).
2. Netzteil einstecken. Das Gateway hat keinen Schalter.
3. **Status-LED am Gateway beobachten** (grüner Tropfen):

   | Was die LED tut | Bedeutung |
   |---|---|
   | pulsiert im Herzschlag-Rhythmus | Gateway startet (1 bis 3 Minuten) |
   | **kurzer Blitz alle 5 Sekunden** | bereit, alles in Ordnung |
   | blinkt schnell | Kopplung läuft (Kap. 6) |
   | aus | nachts gewollt aus – **tagsüber aus = Störung**, siehe `FEHLERSUCHE.md` Kap. 2 |

   „Nachts“ heisst: ausserhalb des LED-Zeitfensters, das Sie in der App einstellen (Werk: 07:00–19:00 Uhr, Kap. 5
   in `PAIRING_KALIBRIERUNG.md`). Die LED-Bedeutung ist vorläufig festgelegt (Entscheid D-027) und kann sich nach
   dem Mustertest noch ändern.

## 3 Handy vorbereiten: Zertifikat einmalig installieren

Warum: Die App läuft verschlüsselt (HTTPS). Das Gateway hat dafür ein eigenes Zertifikat. Damit Ihr Handy diesem
vertraut, installieren Sie einmalig das „fluidi-CA-Zertifikat“. Es gilt nur für die Adresse `fluidi.local`.

1. Handy mit dem **gleichen WLAN** verbinden wie das Gateway. VPN und „nur mobile Daten“ ausschalten.
2. Im Browser `http://fluidi.local/ca` öffnen.
3. Den angezeigten **Fingerabdruck** Zeichen für Zeichen mit dem Zettel vergleichen.
   **Stimmt er nicht: abbrechen** und die Person fragen, die das Gateway installiert hat. Jemand könnte sich im
   Netz dazwischengeschaltet haben.
4. „CA-Zertifikat laden“ antippen. Die Datei `fluidi-ca.crt` wird gespeichert.
5. Zertifikat installieren:
   - **Android:** *Einstellungen → Sicherheit & Datenschutz → Weitere Sicherheits- und Datenschutzeinstellungen →
     Verschlüsselung und Anmeldedaten → Zertifikat installieren → CA-Zertifikat* → Warnung mit „Trotzdem
     installieren“ bestätigen → `fluidi-ca.crt` wählen. Der Menüweg ist je nach Hersteller etwas anders; eine
     Bildschirmsperre (PIN) ist nötig.
   - **iPhone/iPad:** Datei öffnen → *Einstellungen → Profil geladen → Installieren*. **Danach unbedingt:**
     *Einstellungen → Allgemein → Info → Zertifikatsvertrauenseinstellungen* → „fluidi“ einschalten. Ohne diesen
     letzten Schritt vertraut das iPhone dem Zertifikat nicht.
   - **Windows-PC:** Datei doppelklicken → *Zertifikat installieren → Aktueller Benutzer → „Vertrauenswürdige
     Stammzertifizierungsstellen“*.
6. Browser schliessen und neu öffnen.

## 4 App einrichten

1. `https://fluidi.local` öffnen. Es darf **keine Sicherheitswarnung** erscheinen (sonst Kap. 3 wiederholen).
2. Beim ersten Mal erscheint „Hallo, ich bin fluidi“: **Einrichtungscode** vom Zettel eingeben, ein **eigenes
   Passwort** mit mindestens 10 Zeichen zweimal eingeben → „Passwort setzen“.
   Das Passwort bleibt auf dem Gateway. Gut aufbewahren: Zurücksetzen geht nur mit technischem Zugang
   (`GATEWAY_SETUP.md` Kap. 9).
3. App auf den Startbildschirm legen:
   - Android/Chrome: Menü ⋮ → **„App installieren“** bzw. „Zum Startbildschirm hinzufügen“
   - iPhone/Safari: Teilen-Symbol → **„Zum Home-Bildschirm“**
4. Die App wechselt nach der Einrichtung direkt zu **„Sensor koppeln“**.

Nach 5 falschen Passwörtern sperrt die App die Anmeldung für eine Weile und zeigt einen Countdown.

## 5 Ersten Sensor vorbereiten

1. Ist die Knopfzelle noch nicht eingesetzt: nach `BATTERIEWECHSEL.md` einsetzen (Sicherheitshinweise dort zuerst
   lesen). **Beim Einsetzen die Taste oben am Sensor nicht berühren.**

   > **Warnung – Knopfzelle verschlucken ist lebensgefährlich.** Neue und alte Zellen **ausser Reichweite von
   > Kindern und Haustieren** aufbewahren. Besteht der Verdacht, dass eine Zelle verschluckt wurde: **sofort**
   > ärztliche Hilfe holen (Notruf **144**, Tox Info Suisse **145**), nicht auf Beschwerden warten.
2. Direkt nach dem Einsetzen zeigt die Sensor-LED:
   - **grün kurz** (0.2 s) = Selbsttest in Ordnung, danach **2 × kurz gelb** = noch nicht gekoppelt → weiter mit
     Kap. 6
   - **rot 3 ×** = Selbsttest fehlgeschlagen → `FEHLERSUCHE.md` Kap. 1
   - **gar nichts** → `FEHLERSUCHE.md` Kap. 3 „Sensor zeigt nach dem Einsetzen der Zelle nichts“
3. Die Kennung des Sensors steht auf dem Aufkleber (`fluidi-` und vier Zeichen, z. B. `fluidi-8E05`). Sie
   erscheint auch in der App beim Koppeln.

## 6 Sensor koppeln (Kurzfassung)

Ausführlich mit allen Varianten: `PAIRING_KALIBRIERUNG.md` Kap. 2.

1. App → *Einstellungen → Sensor koppeln → **Kopplung starten***. Das Gateway sucht 3 Minuten; seine LED blinkt
   schnell.
2. Am Sensor die **Taste oben halten**, bis die LED nach 3 Sekunden **einmal kurz gelb** aufblitzt, dann
   **loslassen** (spätestens nach 8 Sekunden). Der Sensor blinkt jetzt **1 × pro Sekunde gelb**.
3. Der Sensor erscheint in der App (`fluidi-XXXX`). Kennung mit dem Aufkleber vergleichen. Namen der Pflanze
   eingeben und die **Art** wählen → **„Koppeln“**.
4. **Farben vergleichen:** Der Sensor blinkt fünf Farben (rot/grün/gelb) und wiederholt sie. Die App zeigt die
   Folge. Stimmt sie: **kurz die Sensortaste drücken** und in der App **„Farben stimmen“** antippen
   (zusammen innert 60 Sekunden). Stimmt sie nicht: „Stimmen nicht“.
5. Die Sensor-LED leuchtet **1 Sekunde grün** = gekoppelt. Die App öffnet die Seite der Pflanze.

## 7 Sensor in die Erde stecken und prüfen

1. Sensor **senkrecht bis zur Markierung** in die Erde stecken. In fester Erde vorher mit einem Stab vorstechen.
   **Am Kopf seitlich bzw. an der Hülse greifen, nicht auf die Taste drücken** (die Taste ist dafür nicht
   ausgelegt).
   **Nur die Sonde gehört in die Erde.** Beim Giessen den **Sensorkopf nicht übergiessen**; den Sensor **nie
   untertauchen**, nicht unter fliessendem Wasser und nie in der Spülmaschine reinigen – nur die Sonde mit einem
   feuchten Tuch abwischen. Kam Wasser in den Kopf: `FEHLERSUCHE.md` Kap. 3.8.
2. In der App auf der Seite der Pflanze **„Jetzt messen“** antippen. Die App zeigt „Warte auf Sensor“ →
   „Sensor misst“ → „Wert empfangen“. Das dauert bis etwa 1 Minute (Werkseinstellung „Reaktionszeit 1 min“).
3. **Funksignal prüfen:** *Einstellungen → Sensoren & Firmware*: Bei jedem Sensor steht der Empfang in dBm.
   Werte **unter −80 dBm** meldet die App als „Funksignal schwach“. Dann Gateway oder Sensor näher zueinander
   stellen.
4. **Kalibrieren (empfohlen):** Ohne Kalibrierung rechnet fluidi mit Startwerten, die für Ihre Erde nicht genau
   passen (die Pflanzenseite zeigt „Startkalibrierung“). Die Zwei-Punkt-Kalibrierung trocken/nass beschreibt
   `PAIRING_KALIBRIERUNG.md` Kap. 3.
5. **Schwellenwert prüfen:** Ab welcher Feuchte fluidi „Giessen nötig“ meldet, stellen Sie im Profil der Pflanze
   ein (`PAIRING_KALIBRIERUNG.md` Kap. 4).

Weitere Sensoren: Kap. 5–7 wiederholen.

## 8 Uhrzeit kontrollieren

App → *Einstellungen → System: Zeit, WLAN, Protokoll* → Karte **Zeit**:

| „Quelle“ | Bedeutung |
|---|---|
| Internet-Zeit (NTP) | in Ordnung |
| vom Handy | das Gateway hat die Uhrzeit Ihres Handys übernommen (z. B. nach einem Stromausfall ohne Internet). In Ordnung; sobald NTP wieder geht, wechselt es automatisch |
| keine gültige Zeit | das Gateway kennt die Uhrzeit nicht. Knopf **„Zeit vom Handy übernehmen“** antippen |

Ohne gültige Zeit gehen keine Messwerte verloren: Sie werden als „Zeit unsicher“ markiert und nach dem Zeitabgleich
automatisch korrigiert. Kann das Firmennetz keine Internet-Zeit, lässt sich unter *Einstellungen → Zeit* ein
NTP-Server im Firmennetz eintragen (IT fragen).

## 9 Fertig – was im Alltag passiert

- Die Sensoren messen von selbst (Werk: 6 × pro Tag) und blinken dabei kurz grün (Lebenszeichen).
- Braucht eine Pflanze Wasser, zeigt die App „Giessen nötig“ und die Sensor-LED blinkt **1 × pro Minute kurz blau**
  im LED-Zeitfenster (bei schwacher Batterie gelb statt blau).
- Nach dem Giessen in der App **„Gegossen“** antippen (Knopf „Gegossen“ in der Navigation oder auf der Pflanzenkarte).
- Kurz auf die Sensortaste drücken = sofort messen; **2 × grün** = Wert beim Gateway angekommen, **1 × grün** =
  im Sensor gespeichert, kommt später (kein Fehler).
- Die App warnt, wenn die Batterie eines Sensors noch etwa 30 Tage reicht → `BATTERIEWECHSEL.md`.
- Ein Bildschirm im Büro kann die Übersicht ohne Anmeldung zeigen: *Einstellungen → Dashboard für Kollegen*.
- Regelmässig *Einstellungen → Export & Backup* → Backup auf dem PC ablegen.
