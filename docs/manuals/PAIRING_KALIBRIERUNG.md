# fluidi – Sensor koppeln, kalibrieren, Schwellenwerte einstellen

| | |
|---|---|
| Dokument | `docs/manuals/PAIRING_KALIBRIERUNG.md` |
| Version | 0.1 (Phase 6) |
| Datum | 2026-11-08 |
| Für wen | Alle, die Sensoren in Betrieb nehmen oder Pflanzen einrichten. Keine Fachkenntnisse nötig. |
| Gilt für | App `app/` (Seiten Koppeln, Kalibrieren, Profil, Einstellungen), Gateway 0.5.0, Sensor-Firmware 0.1.0 |
| Status | Nach dem Programmcode erstellt, **noch nicht am echten Sensor durchgespielt** (PROTOTYP-PRÜFUNG) |

Voraussetzung: Gateway läuft, App ist eingerichtet und Sie sind angemeldet (`INBETRIEBNAHME.md` Kap. 1–4).
Bei Problemen: `FEHLERSUCHE.md`.

## 1 Begriffe

- **Koppeln:** Sensor und Gateway tauschen einmalig einen geheimen Schlüssel aus. Danach nimmt das Gateway nur noch
  Werte von „seinen“ Sensoren an, und niemand kann sich als Sensor ausgeben.
- **Farbfolge:** Beim Koppeln zeigen Sensor-LED und App dieselben fünf Farben. Stimmen sie überein, ist sicher, dass
  kein fremdes Gerät dazwischen steckt.
- **Feuchteindex (%):** Die Anzeige in der App. **0 % = so trocken wie bei Ihrer Trocken-Kalibrierung, 100 % = so nass
  wie bei der Nass-Kalibrierung.** Es ist kein „Wassergehalt in Prozent“, sondern ein Vergleich mit Ihren zwei
  Kalibrierpunkten.
- **Schwelle „Giessen unter“:** Fällt der Feuchteindex darunter, meldet fluidi „Giessen nötig“.

## 2 Sensor koppeln

### 2.1 Ablauf

1. App → *Einstellungen* → **„Sensor koppeln“** → **„Kopplung starten“**.
   Das Gateway sucht jetzt **3 Minuten** (Countdown in der App), seine Status-LED blinkt schnell. Mit „Suche
   beenden“ brechen Sie ab.
2. Sensor in die Hand nehmen (Zelle eingesetzt). **Taste oben am Sensor drücken und halten.**
   - Nach **3 Sekunden** blitzt die LED **einmal kurz gelb** → jetzt **loslassen**.
   - Lassen Sie erst nach **8 Sekunden** los, passiert nichts (Schutz gegen versehentliches Drücken). Nochmals
     versuchen.
   - Nach dem Loslassen blinkt der Sensor **1 × pro Sekunde gelb**: Er ist bereit zum Koppeln, **2 Minuten** lang.
3. Nach wenigen Sekunden erscheint der Sensor in der App als Karte mit seiner Kennung (`fluidi-XXXX`) und der
   Signalstärke. **Kennung mit dem Aufkleber am Sensor vergleichen.** „war schon gekoppelt“ heisst: Dieser Sensor
   war früher mit diesem Gateway verbunden.
4. Pflanze angeben:
   - **Neue Pflanze:** Name (z. B. „Monstera am Fenster“) und **Art** wählen. fluidi übernimmt die Startwerte der Art
     für die Schwellen (Kap. 4).
   - **Bestehende Pflanze:** nur sichtbar, wenn es eine Pflanze ohne Sensor gibt (z. B. nach einem Sensorwechsel).
     Die bisherigen Messwerte bleiben bei der Pflanze.
5. **„Koppeln“** antippen. Die App zeigt „Schlüssel werden ausgetauscht …“.
6. **Farbfolge vergleichen:** Der Sensor blinkt fünf Farben nacheinander (rot, grün oder gelb; je 0.3 s), macht
   2 Sekunden Pause und wiederholt. Die App zeigt die fünf Farben nummeriert.
   - **Stimmt die Reihenfolge:** **kurz die Taste am Sensor drücken** *und* in der App **„Farben stimmen“**
     antippen. Die Reihenfolge der beiden Schritte ist egal.
   - **Stimmt sie nicht:** **„Stimmen nicht“** antippen. Die Kopplung wird abgebrochen. Nochmals versuchen; weicht
     die Folge wieder ab, das Koppeln an einem anderen Ort wiederholen und die verantwortliche Person informieren
     (ein fremdes Gerät könnte mithören).
   - Für den Vergleich haben Sie **60 Sekunden** (die App zählt herunter).
7. **Erfolg:** Die Sensor-LED leuchtet **1 Sekunde grün**, die App meldet „gekoppelt“ und öffnet die Seite der
   Pflanze. **Misserfolg:** Die Sensor-LED blinkt **3 × rot**, die App zeigt „Kopplung fehlgeschlagen“ → ab Schritt 2
   wiederholen (falls die Suche abgelaufen ist, ab Schritt 1).

### 2.2 Nach dem Koppeln

- Sensor bis zur Markierung in die Erde stecken, dabei **nicht auf die Taste drücken** (seitlich am Kopf greifen).
- Auf der Pflanzenseite **„Jetzt messen“** antippen; der erste Wert kommt innert etwa einer Minute.
- **„Sensor finden (LED blinkt)“** auf der Pflanzenseite lässt den Sensor beim nächsten Funkkontakt 15 Sekunden lang
  abwechselnd grün und blau blinken – praktisch bei vielen Töpfen.

### 2.3 Sensor entkoppeln oder wechseln

- *Einstellungen → Sensoren & Firmware* → beim Sensor **„Entkoppeln“**. Der Sensor löscht seinen Schlüssel beim
  nächsten Kontakt und blinkt danach 2 × gelb. Die Messwerte bleiben bei der Pflanze.
- Ist der Sensor nicht erreichbar (z. B. defekt), fragt die App, ob er trotzdem im Gateway entfernt werden soll. Den
  Sensor danach auf Werkseinstellung zurücksetzen, bevor er wieder verwendet wird (`FEHLERSUCHE.md` Kap. 3).
- **Sensor tauschen:** alten Sensor entkoppeln, neuen koppeln und dabei „Bestehende Pflanze“ wählen.

## 3 Zwei-Punkt-Kalibrierung (trocken / nass)

### 3.1 Wozu

Der Sensor misst eine elektrische Grösse (Kapazität), die je nach Erde anders ausfällt. Ohne Kalibrierung rechnet
fluidi mit **Startwerten** (in der App „Startkalibrierung (ANNAHME)“), die nicht zu Ihrer Erde passen müssen. Mit
zwei Messungen – einmal trocken, einmal frisch durchnässt – passt die Anzeige zu Ihrem Substrat.

- Die Kalibrierung gilt **je Sensor und Substrat** (Erde oder Granulat).
- Sie gilt nach dem Übernehmen **auch rückwirkend** für die bisherigen Werte.
- Wiederholen, wenn Sie umtopfen, die Erdsorte wechseln oder die Werte unplausibel wirken.

### 3.2 Vorbereitung

- Planen Sie etwa **30 Minuten** ein, mit Wartezeit.
- **Die App-Seite während der ganzen Kalibrierung offen lassen.** Wer die Seite vor dem Übernehmen verlässt, bricht
  den Lauf ab und beginnt von vorne. Ein Neustart des Gateways bricht ihn ebenfalls ab.
- Für den Trockenpunkt eignet sich die Pflanze am besten, wenn sie **ohnehin gegossen werden muss** (Erde mehrere
  Tage nicht gegossen). Alternativ ein Gefäss mit trockener Erde derselben Sorte.

### 3.3 Ablauf in der App

1. Pflanzenseite → **„Kalibrieren“**.
2. Schritt **Vorbereiten:** Substrat wählen (**Erde** oder **Granulat**). Die App zeigt die aktuellen Werte
   (Startkalibrierung oder Datum der letzten Kalibrierung). → **„Start“**.
3. Schritt **Trocken:** Sensor **bis zur Markierung** in das trockene Substrat stecken. Nicht drücken, nicht giessen.
   → **„Trocken messen“**. Der Sensor misst 5-mal, jeweils nach einem kurzen Funkkontakt. Das dauert **bis etwa
   1 Minute**. Werden einzelne Ausreisser verworfen, meldet die App das.
4. Schritt **Nass:** Jetzt **durchdringend giessen, bis unten Wasser austritt.** **10 Minuten warten.** Sensor nicht
   bewegen. → **„Nass messen“** (wieder bis etwa 1 Minute).
5. Schritt **Übernehmen:** Die App zeigt beide Rohwerte.
   - **„Bereit zum Übernehmen“** → **„Übernehmen“**. Fertig: „Kalibrierung gespeichert – gilt auch rückwirkend“.
     Auf der Pflanzenseite steht nun „kalibriert (2 Punkte)“.
   - **„Spanne zu klein“** („Trocken- und Nasswert liegen zu nahe beieinander“): Die Erde war beim Trockenpunkt
     nicht trocken genug oder beim Nasspunkt nicht nass genug, oder der Sensor steckte nicht tief genug.
     **„Neu beginnen“** und sorgfältiger wiederholen. Die alte Kalibrierung bleibt so lange gültig.

### 3.4 Was danach normal ist

- Direkt nach dem Giessen kann der Index etwas über 100 % liegen, in sehr trockener Erde etwas unter 0 %.
- Liegt er **mehr als 10 Punkte unter 0 %**, meldet die App **„Sensor nicht in der Erde?“**; **mehr als 10 Punkte
  über 100 %** → **„Zu nass / überflutet?“** (siehe `FEHLERSUCHE.md`).

## 4 Schwellenwerte: wann „Giessen nötig“?

Pflanzenseite → Stift-Symbol oben rechts (**„Profil“**) → Karte **„Feuchte-Zielbereich“** → **„Sichern“**.

| Feld | Bedeutung |
|---|---|
| **Giessen unter (%)** | Fällt der Feuchteindex darunter, zeigt die App „Giessen nötig“ und die Sensor-LED blinkt blau (Kap. 5). Bereich 0–95 % |
| **Zu nass über (%)** | Liegt der Index darüber, meldet die App „Zu nass seit über 48 h“ – aber erst **48 Stunden nach dem letzten Giessen** (direkt nach dem Giessen ist „zu nass“ normal) |
| **Giessverhalten** | „wie die Art“ oder eigene Wahl: A abtrocknen lassen, B oben abtrocknen, C feucht halten, D Sonderfall |
| **Winterfaktor (Nov–Feb)** | Leer = Wert aus der Art. Im Winter gilt die Schwelle „Giessen unter“ × Faktor (z. B. 30 % × 0.8 = 24 %); die Pflanzenseite zeigt dann „Winter: Schwelle … %“ |

Hinweise:

- Beim Wählen einer **Art** schlägt fluidi Startwerte vor (40 Pflanzenprofile). In der App heissen sie
  „Startwert“. **Alle Prozentwerte sind Startwerte (ANNAHME)** – nach 3–4 Giesszyklen an Ihre Pflanze anpassen:
  Lässt die Pflanze die Blätter hängen, bevor fluidi meldet, die Schwelle erhöhen; meldet fluidi zu früh, senken.
- Die neue Schwelle erhält der Sensor beim nächsten Funkkontakt (die App zeigt bis dahin „Änderung wartet“ unter
  *Sensoren & Firmware*).
- Bei Arten mit „Sonderfall“ (z. B. Hydrokultur) ist der Feuchteindex nur eingeschränkt aussagekräftig; dort gibt es
  keine Startwerte.

## 5 LED am Sensor und Hinweise einstellen

App → *Einstellungen* → Karte **„Messung & Sensor-LED“**:

| Einstellung | Wirkung |
|---|---|
| Messungen pro Tag | Werk 6. Mehr Messungen = kürzere Batterielaufzeit; über 18 pro Tag reicht der Speicher im Sensor weniger als 60 Tage |
| Reaktionszeit „Jetzt messen“ | Werk 1 min. 5 min spart Batterie, „Jetzt messen“ dauert dann länger |
| Status-LED (Quittung, Lebenszeichen) | grünes Lebenszeichen bei jeder Messung. Gilt **auch für die Status-LED des Gateways** (ANNAHME D-027) |
| Giessen-Hinweis an der LED (blau) | blaues Blinken 1 × pro Minute, wenn „Giessen nötig“ |
| Zeitfenster Giessen-Hinweis | von–bis (Werk 07:00–19:00). Ausserhalb bleibt die Sensor-LED dunkel (auch die roten Warnungen); die Gateway-LED ist dann ebenfalls aus |
| Wochentage | An abgewählten Tagen bleibt die blaue LED aus (z. B. Wochenende im Büro); die Gateway-LED ist dann aus |
| Helligkeit | tief / normal / hoch |

Pro Sensor lässt sich die LED unter *Einstellungen → Sensoren & Firmware* (Schalter „LED“) ausschalten.
Alle Änderungen erhält der Sensor beim nächsten Funkkontakt.

Karte **„Hinweise“**: Hinweise in der App, Zähler durstiger Pflanzen am App-Symbol (Android/Chrome), **„Giessen
nötig, wenn länger als“** (sofort bis 24 h), kritische Meldungen, Batterie unter 30 Tagen, Ruhezeit. fluidi
verschickt keine E-Mails und keine Push-Nachrichten (alles bleibt im lokalen Netz).
