# fluidi – Fehlersuche

| | |
|---|---|
| Dokument | `docs/manuals/FEHLERSUCHE.md` |
| Version | 0.2 (Phase 6: Sicherheit W-3/K-6, Red Team W-5) |
| Datum | 2026-11-09 |
| Für wen | Alle, die fluidi benutzen. Abschnitte mit „technisch“ brauchen Zugang zum Gateway (SSH) |
| Gilt für | Sensor-Firmware 0.1.0 (`firmware/sensor/core/fl_ui.c`, `fl_app.c`), Gateway 0.5.0 (`firmware/gateway/`), App `app/` |
| Status | LED-Muster aus dem Programmcode übernommen; **am echten Gerät noch nicht geprüft** (PROTOTYP-PRÜFUNG) |

Inhalt: 1 LED am Sensor · 2 LED am Gateway · 3 Probleme am Sensor · 4 Probleme mit der App und dem Gateway ·
5 Meldungen in der App · 6 Wann Hilfe holen

---

## 1 Was die LED am Sensor bedeutet

Farben: **grün** = in Ordnung / gesendet · **blau** = Giessen nötig · **rot** = Batterie tief oder Fehler ·
**gelb** = Kopplung. Bei schwacher Batterie zeigt der Sensor **gelb statt blau**. Unter etwa 2.4 V Batteriespannung
bleibt die LED ganz dunkel, ausser nach einem Tastendruck (dann 1 × kurz rot).

### 1.1 Von selbst (ohne Tastendruck)

| LED | Bedeutung | Was tun |
|---|---|---|
| 1 × sehr kurz grün, einige Male am Tag | Lebenszeichen bei der automatischen Messung | nichts (abschaltbar: *Einstellungen → Messung & Sensor-LED → Status-LED*) |
| 1 × pro Minute sehr kurz **blau** (bzw. gelb) | **Giessen nötig** | giessen, in der App „Gegossen“ antippen. Nur im LED-Zeitfenster; ohne gültige Uhrzeit alle 2 min ganztags |
| alle 10 min 2 × kurz **rot** | **Batterie tief** (Restlaufzeit unter etwa 30 Tagen) | Zelle wechseln (`BATTERIEWECHSEL.md`) |
| alle 10 min 3 × kurz **rot** | **Fehler im Sensor** (Messung, Speicher, Taste klemmt …) | Text in der App ansehen (Kap. 5), Kap. 3 |
| abwechselnd grün und blau, 15 s | „Sensor finden“ wurde in der App angetippt | nichts |
| 3 × kurz grün | neue Firmware erfolgreich übernommen | nichts |
| 3 × kurz rot (nach einem Update) | neue Firmware nicht bestätigt, alte Version läuft wieder | App: *Sensoren & Firmware*, Kap. 5 |

Rot und Blau erscheinen nur im **LED-Zeitfenster** (Werk 07:00–19:00); nachts bleibt der Sensor dunkel.

### 1.2 Nach dem Einsetzen der Knopfzelle

| LED | Bedeutung |
|---|---|
| 1 × grün (0.2 s) | Selbsttest in Ordnung |
| danach 2 × kurz gelb | Sensor ist noch nicht gekoppelt → `PAIRING_KALIBRIERUNG.md` Kap. 2 |
| 3 × rot (je 0.1 s) | Selbsttest fehlgeschlagen (Messung oder Temperatursensor) → Kap. 3 |
| **nichts** | siehe Kap. 3 „Sensor zeigt nach dem Einsetzen nichts“ |

### 1.3 Nach einem Tastendruck

| Tastendruck | LED | Bedeutung |
|---|---|---|
| kurz (unter 1.5 s) | **2 × grün** | gemessen, Gateway hat den Wert bestätigt |
| kurz | **1 × grün** | gemessen und im Sensor gespeichert; das Gateway holt ihn später (kein Fehler) |
| kurz | danach 2 × kurz rot / 3 × rot (je 0.1 s) | zusätzlich: Batterie tief / Fehler aktiv |
| kurz | 1 × gelb (0.2 s) | Sensor ist nicht gekoppelt |
| kurz | 1 × ganz kurz rot | Batterie leer (Unterspannung) – Zelle wechseln |
| halten | nach 3 s 1 × kurz gelb | jetzt loslassen = Kopplung starten |
| 3–8 s, dann loslassen | gelb 1 × pro Sekunde (bis 2 min) | Kopplungsmodus |
| beim Koppeln | 5 Farben rot/grün/gelb, wiederholt | Farbfolge vergleichen (`PAIRING_KALIBRIERUNG.md` Kap. 2) |
| beim Koppeln | 1 s grün / 3 × rot | gekoppelt / Kopplung fehlgeschlagen |
| halten ≥ 10 s | rot schnell blinkend bis zum Loslassen, dann 5 s schwach rot | **Werkseinstellung vorbereitet** – siehe Kap. 3.6. Ohne weiteren Tastendruck passiert nichts |
| innert 5 s danach kurz | 1 s rot, Neustart | **Werkseinstellung ausgeführt** |

Zwischen 1.5 und 3 s sowie zwischen 8 und 10 s Drücken passiert absichtlich nichts.

## 2 Was die LED am Gateway bedeutet

Grüne LED im Tropfen am Gateway. Festlegung vorläufig (D-027), Anpassung nach dem Mustertest möglich.

| LED | Bedeutung | Was tun |
|---|---|---|
| Herzschlag-Rhythmus | Gateway startet | 1–3 min warten |
| **kurzer Blitz alle 5 s** | alles in Ordnung | nichts |
| schnelles Blinken | Kopplung läuft (Suche in der App gestartet) | Sensor koppeln oder in der App „Suche beenden“ |
| **aus, nachts** oder an abgewählten Wochentagen | gewollt (gleiches Zeitfenster wie der Giessen-Hinweis der Sensoren) | nichts |
| **aus, tagsüber** | Störung: Funk ausgefallen, fluidi-Dienst gestoppt, Gateway ohne Strom, **oder** der Schalter „Status-LED“ in den Einstellungen ist aus | Kap. 4.1 |
| Herzschlag hört nicht auf (länger als 5 min) | Gateway läuft, aber der fluidi-Dienst startet nicht | Kap. 4.1 |

## 3 Probleme am Sensor

### 3.1 Sensor zeigt nach dem Einsetzen der Zelle nichts

1. **Polung prüfen:** Pluspol (beschriftete Seite) nach vorne (`BATTERIEWECHSEL.md` Schritt 6).
2. Zelle **mindestens 10 Sekunden** herausnehmen, dann wieder einsetzen **ohne die Taste zu berühren**. Wird beim
   Einsetzen die Taste gedrückt, startet der Sensor (bei den Mustern) in einen Programmiermodus, wirkt tot und
   leert die Zelle in wenigen Tagen (`PROGRAMMIEREN_SENSOR.md` Kap. 6).
3. Neue Zelle versuchen (nur Panasonic CR2032 aus der Originalverpackung).
4. Kommt immer noch nichts: Sensor nicht weiter benutzen, Kap. 6.

### 3.2 Sensor erscheint beim Koppeln nicht in der App

- Wurde in der App **„Kopplung starten“** gedrückt, und läuft der Countdown noch (3 min)?
- Blinkt der Sensor **gelb 1 × pro Sekunde**? Wenn nicht: Taste halten bis zum gelben Blitz nach 3 s, dann
  loslassen (nicht länger als 8 s halten). Der Kopplungsmodus endet nach 2 Minuten.
- Sensor näher ans Gateway bringen (gleicher Raum).
- Ist die Zelle leer (Unterspannung), reagiert der Sensor nicht auf langes Drücken → Zelle wechseln.
- War der Sensor schon mit diesem Gateway gekoppelt, steht in der App „war schon gekoppelt“; er lässt sich neu koppeln.

### 3.3 Kopplung schlägt fehl (3 × rot)

- Farbvergleich nicht innert 60 Sekunden abgeschlossen → neu beginnen.
- „Stimmen nicht“ gewählt oder die Farben stimmten wirklich nicht → neu beginnen. Wiederholt abweichende Farben:
  anderer Ort, verantwortliche Person informieren.
- Nach 3 fehlgeschlagenen Schlüsselprüfungen in Folge sperrt der Sensor Verbindungen für **30 Minuten** (App:
  „Verbindungssperre aktiv“). Messwerte bleiben im Sensor gespeichert. 30 Minuten warten.

### 3.4 Keine neuen Werte

Die App meldet „**Keine neuen Werte**“, wenn länger als 3 Messintervalle (mindestens 2 Stunden) nichts angekommen
ist.

1. Gateway-LED prüfen (Kap. 2).
2. **Sensor kurz drücken.** Nach mehreren Abstürzen kurz hintereinander schaltet sich der Sensor zum Schutz der
   Zelle ab (LED dunkel, keine Werte). **Ein kurzer Tastendruck weckt ihn:** Er startet neu (1 × grün) und arbeitet
   normal weiter; die App zeigt danach „Absturz“ (Kap. 5). Erst wenn auf den Tastendruck **nichts** oder nur
   **1 × kurz rot** kommt, die Zelle wechseln – so wird keine gute Zelle unnötig weggeworfen.
3. Batterie: *Einstellungen → Sensoren & Firmware* zeigt Prozent, Spannung und geschätzte Tage. Tastendruck am
   Sensor: kommt gar nichts oder 1 × kurz rot → Zelle wechseln.
4. Funk: Signal unter −80 dBm gilt als schwach. Gateway oder Sensor umstellen (nicht hinter Metall, nicht in einen
   Metalltopf).
5. Werte gehen nicht verloren: Der Sensor speichert sie und liefert sie nach (bis etwa 60 Tage bei 6 Messungen pro
   Tag). Unter *Sensoren & Firmware* steht „… Werte im Puffer“.

### 3.5 Unplausible Feuchtewerte

| Anzeige | Ursache | Abhilfe |
|---|---|---|
| „**Sensor nicht in der Erde?**“ | Index weit unter 0 %: Sensor steckt nicht oder nicht tief genug in der Erde | bis zur Markierung einstecken |
| „**Zu nass / überflutet?**“ | Index weit über 100 %: Wasser steht im Topf, oder Kalibrierung nicht passend | Untersetzer leeren; ggf. neu kalibrieren |
| „**Kalibrierung prüfen**“ | Kalibrierwerte fehlen oder sind unbrauchbar | kalibrieren (`PAIRING_KALIBRIERUNG.md` Kap. 3) |
| „Spanne zu klein“ beim Kalibrieren | Trocken- und Nasswert zu ähnlich | trockener/nasser messen, tiefer einstecken, neu beginnen |
| Werte springen nach dem Umtopfen | andere Erde | neu kalibrieren |
| „Zeit unsicher“ im Tagebuch | Gateway hatte bei Empfang keine gültige Uhrzeit | wird nach dem Zeitabgleich automatisch korrigiert (Kap. 4.4) |

### 3.6 Sensor auf Werkseinstellung zurücksetzen

Nötig, wenn ein Sensor im Gateway „trotzdem entfernt“ wurde oder mit einem anderen Gateway verwendet werden soll.

1. Taste **mindestens 10 Sekunden** halten – die LED blinkt schnell rot.
2. Loslassen – die LED glimmt 5 Sekunden schwach rot.
3. **Innerhalb dieser 5 Sekunden kurz drücken.** Die LED leuchtet 1 s rot, der Sensor startet neu.

Gelöscht werden Schlüssel, Einstellungen und noch nicht abgeholte Messwerte. Danach neu koppeln.

### 3.7 Taste klemmt

Hält die Taste länger als 30 Sekunden gedrückt (z. B. verkantet), ignoriert der Sensor sie, meldet „Taste klemmt“
und prüft jede Minute, ob sie wieder frei ist. Sensor herausnehmen, Taste prüfen. Nie mit Kraft auf die Taste
drücken und den Sensor nicht über die Taste in die Erde drücken.

### 3.8 Wasser im Sensorkopf

Sofort nach `BATTERIEWECHSEL.md` „Wasser im Kopf“ vorgehen (Zelle heraus, trocknen, melden).
Vorbeugen: beim Giessen den Kopf nicht übergiessen, den Sensor nie untertauchen, nicht unter fliessendem Wasser oder
in der Spülmaschine reinigen; nur die Sonde mit einem feuchten Tuch abwischen.

## 4 Probleme mit der App und dem Gateway

### 4.1 Gateway-LED tagsüber aus oder dauernd im Herzschlag

1. Netzteil und Steckdose prüfen. **Ist Wasser auf Netzteil oder Steckdose gelangt: nicht anfassen**, zuerst den
   Stromkreis an der Sicherung abschalten, dann ausstecken und das Netzteil ersetzen. Gateway und Netzteil danach
   ausserhalb des Giessbereichs aufstellen (`INBETRIEBNAHME.md` Kap. 2). Nur das Original-Netzteil verwenden.
2. In der App *Einstellungen → Messung & Sensor-LED*: Ist „Status-LED“ eingeschaltet? Stimmt das Zeitfenster?
3. App öffnen: *Einstellungen → System: Zeit, WLAN, Protokoll* → Karte **Gateway**, Zeile „Funk“, und das
   **Ereignisprotokoll** ansehen (z. B. „Funk nicht verfügbar“).
4. *System* → **„Neu starten“** (die App ist etwa 1 Minute nicht erreichbar).
5. Hilft das nicht: Netzteil 10 Sekunden ausstecken und wieder einstecken. Messwerte gehen dabei nicht verloren
   (die Sensoren löschen Werte erst, wenn das Gateway sie gespeichert hat).
6. **Technisch:** `sudo systemctl status fluidi-gateway`, `journalctl -u fluidi-gateway -n 50`,
   `sudo ./install_gateway.sh --check` (Zeilen „Status-LED“ und Dienste; `GATEWAY_SETUP.md` Kap. 4.3, 5.2).

### 4.2 App nicht erreichbar (`fluidi.local`)

- Handy im **gleichen WLAN** wie das Gateway? Kein VPN, keine mobilen Daten.
- Gateway-LED blitzt alle 5 s? Sonst Kap. 4.1.
- Android löst `fluidi.local` erst ab Version 12 auf. Am PC im gleichen Netz prüfen: `ping fluidi.local`.
  Antwortet das Gateway dort auch nicht, ist es nicht im WLAN (WLAN-Passwort geändert? → technisch, `GATEWAY_SETUP.md`).
- Neues oder anderes WLAN (z. B. Gäste- oder Firmennetz): Dort sind Geräte oft voneinander abgeschottet
  (Client-Isolation) oder `.local`-Namen gesperrt. Prüfung und Ausweichwege: `GATEWAY_SETUP.md` Kap. 1.1. Bei
  Client-Isolation hilft nur die IT. **Nicht** über die IP-Adresse arbeiten und die Zertifikatswarnung wegklicken.
- Ist das Gateway nicht erreichbar, zeigt die App den zuletzt geladenen Stand mit einem Hinweisbalken.

### 4.3 Zertifikatswarnung im Browser

- Zertifikat nicht installiert oder (iPhone) Vertrauen nicht eingeschaltet → `INBETRIEBNAHME.md` Kap. 3.
- Zertifikat abgelaufen (spätestens nach 825 Tagen; die App warnt 60 Tage vorher unter *System →
  Zertifikat (HTTPS)*) → technisch erneuern (`GATEWAY_SETUP.md` Kap. 6), danach auf allen Geräten neu installieren.
- **Nie** eine Warnung bei `fluidi.local` einfach wegklicken, wenn das Zertifikat installiert ist: Jemand könnte
  sich im Netz dazwischengeschaltet haben. Fingerabdruck prüfen (*System → Zertifikat*).

### 4.4 Falsche oder „keine gültige“ Uhrzeit

Das Gateway hat **keine eigene Uhr mit Batterie** (D-028). Es holt die Zeit aus dem Internet (NTP).

- *System → Zeit*: „keine gültige Zeit“ → **„Zeit vom Handy übernehmen“**. Angemeldet übernimmt das Gateway die
  Handyzeit beim Öffnen der App auch automatisch, aber nur wenn es selbst keine gültige Zeit hat.
- Das Gateway lehnt eine offensichtlich falsche Handyzeit (vor 2026) ab. Uhrzeit des Handys prüfen.
- Dauerhaft keine Internet-Zeit: Das Firmennetz sperrt eventuell NTP. Unter *Einstellungen → Zeit* einen
  NTP-Server im Firmennetz eintragen (IT fragen).
- Folgen: Bis zum Zeitabgleich bekommen die Sensoren keine Uhrzeit (LED-Zeitfenster gilt dann ganztags), Werte sind
  „Zeit unsicher“ und werden danach korrigiert; Raumklimawerte werden erst danach gespeichert.

### 4.5 Anmeldung

- „Passwort falsch (noch … Versuche bis zur Sperre)“: Nach 5 Fehlversuchen ist die Anmeldung gesperrt; die App zeigt
  einen Countdown.
- **Passwort vergessen:** nur technisch zurücksetzbar, die Daten bleiben erhalten (`GATEWAY_SETUP.md` Kap. 9).
- Nach einer Passwortänderung sind alle anderen Geräte abgemeldet.

### 4.6 Raumklima zeigt „kein Sensor“

Der Klimasensor im Gateway wurde beim Start nicht gefunden. **Technisch:** `sudo i2cdetect -y 1` muss Adresse 44
zeigen; Verdrahtung nach `GATEWAY_SETUP.md` Kap. 5.1 prüfen; danach `sudo systemctl restart fluidi-gateway`.

### 4.7 Firmware-Verteilung an Sensoren schlägt fehl

| Meldung | Bedeutung |
|---|---|
| „Update: Batterie zu tief“ | Sensor hat zu wenig Batterie für ein Update – Zelle wechseln, dann erneut verteilen |
| „Update: Signatur abgelehnt“ / Abbild „ungültig“ | Datei nicht vom Entwickler signiert – nicht verwenden |
| „Update: Version zu alt (Anti-Rollback)“ | ältere Firmware lässt sich nicht einspielen (Schutz) |
| „Update nicht bestätigt, alte Version wiederhergestellt“ | der Sensor hat nach dem Update den Selbsttest nicht bestanden und läuft mit der alten Version weiter |

## 5 Meldungen zum Sensor in der App

Unter *Einstellungen → Sensoren & Firmware* (und in den Hinweisen) zeigt die App Fehlermeldungen des Sensors:

| Meldung | Was tun |
|---|---|
| Messkette: Oszillator ohne Signal / Kapazität ausserhalb Messbereich | Sensor herausziehen, Sonde reinigen und auf Beschädigung prüfen, wieder einstecken; bleibt die Meldung: Kap. 6 |
| Temperatursensor antwortet nicht | Kap. 6 |
| Messung streut zu stark | Sensor fester in die Erde stecken; bleibt sie: Kap. 6 |
| Messung wegen Unterspannung ausgelassen / Unterspannungsabschaltung | Zelle wechseln |
| Flash-Fehler / Einstellungen beschädigt | Sensor neu koppeln; wiederholt: Kap. 6 |
| Pufferüberlauf: unquittierte Messwerte überschrieben | Sensor war zu lange ohne Gateway (über etwa 60 Tage) – Funk prüfen |
| Watchdog-Neustart / Brownout-Neustart / Absturz | einmalig: beobachten. War der Sensor danach dunkel (Schutzabschaltung nach Abstürzen in Folge): kurzer Tastendruck weckt ihn (Kap. 3.4). Häufig: Zelle wechseln, sonst Kap. 6 |
| Taste klemmt | Kap. 3.7 |
| 32-kHz-Quarz gestört | Kap. 6 |
| Verbindungssperre aktiv (zu viele Fehlversuche) | 30 Minuten warten (Kap. 3.3). Tritt sie ohne eigenes Koppeln auf, versucht eventuell ein fremdes Gerät, sich zu verbinden → Kap. 6 |

## 6 Wann Hilfe holen

Bitte an die verantwortliche Person bzw. Projektleitung melden (mit Sensor-Kennung `fluidi-XXXX`, Datum und Text
der Meldung aus dem Ereignisprotokoll unter *System*):

- Sensor bleibt nach Kap. 3.1 dunkel oder meldet wiederholt Fehler aus Kap. 5
- Wasser im Sensorkopf
- Farbfolge beim Koppeln weicht wiederholt ab
- Zertifikatswarnung trotz installiertem Zertifikat
- Gateway startet nach Kap. 4.1 nicht
