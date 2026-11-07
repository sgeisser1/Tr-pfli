# fluidi – drei klickbare Stil-Entwürfe der App

| | |
|---|---|
| Dokument | `docs/software/UI_ENTWUERFE.md` (PDF: `UI_ENTWUERFE.pdf`) |
| Stand | 2026-11-07, Entwurf zur Auswahl |
| Konzept | `docs/software/SOFTWARE_CONCEPT.md` (Funktionen, Abläufe, Prognose, Benachrichtigungen) |
| Entwürfe | `app/concept/` – **selbst ausprobieren:** `docs/manuals/APP.md` Kap. 5 (`python3 app/dev/mock_server.py`, dann `http://localhost:8080/concept/?theme=frost`, `…=botanik`, `…=stele`) |
| Bilder | `app/docs/concept/` (84 Einzelbilder), Vergleich `app/docs/concept/vergleich/` – erzeugt mit `app/dev/concept_shots.sh` und `app/dev/concept_compose.py` |

Alle drei Entwürfe haben **dieselbe Struktur, dieselben Daten und dieselben Funktionen** (Mock-Server, gleiche API).
Nur die Gestaltung unterscheidet sich (je eine CSS-Datei mit Farben und Dekor). Jeder Entwurf hat Hell- und
Dunkelmodus (automatisch nach Gerät oder per Schalter), ist für das Handy gebaut und hat ein eigenes Desktop-Layout.
Handy-Bilder: 430 × 932 px im Geräterahmen; Desktop: 1440 × 900 px. Pflanzen, Tropfen-Charakter und Symbole sind
eigene SVG-Zeichnungen, keine fremden Bilder.

## 1 Die drei Entwürfe in Kürze

| | **A „fluidi Frost“** | **B „fluidi Botanik“** | **C „fluidi Stele“** |
|---|---|---|---|
| Vorbild | Referenz 1 (helle Glas-Oberflächen, schwebende Leiste) | Referenz 2/3 (Grün, grosse Typografie, Pflanzen) | eigener Vorschlag: Sensor und Gateway (D-010/D-011) |
| Farben | Hellblau-Verläufe, Glas-Karten, warmes Hellgrau #B9B5AC als Neben-Ton | Salbei- und Waldgrün, Weiss, dunkelgrüne Knöpfe | Warmgrau hell (Hülse), Hellblau (Kappe), dunkle Fuge, Ton in Ton |
| Formen | sehr rund (30 px), Kreis-Knöpfe | rund (28 px), Pillen | hart, 45°-Fasen wie Logo und Gehäuse |
| Schrift | runde Systemschrift, leichte grosse Zahlen | sehr fett, eng, grosse Titel | ruhig, Versal-Labels, technische Zahlen |
| Pflanzen | frisches Grün in weissem Topf | üppiges Grün, grosse Pflanze im Kopf | **Ton in Ton grau**, Topf mit blauem Rand – nur die Tropfen leuchten farbig |
| Navigation Handy | dunkle schwebende Pille + blauer runder „Gegossen“-Knopf | Glas-Pille, aktiver Eintrag als grüne Pille mit Text | flache Leiste mit Farbfuge, aktiver Eintrag mit leuchtendem Mini-Tropfen, eckiger „Gegossen“-Knopf |
| Dunkel | Nachtblau, Tropfen glühen | Waldgrün mit Glas, weisse Knöpfe | warmes Anthrazit, LED-Tropfen leuchten stark |
| Wirkung | leicht, freundlich, „Apple-Home“ | lebendig, verspielt, Pflanzen-App | erwachsen, eigenständig, passt sichtbar zur Hardware |

Gemeinsam in allen drei: Tropfen-Ampel (Farbe = LED-Farbe, Füllstand = Feuchte, Gesicht = Stimmung), Zustand immer
auch als Text und Symbol, Prognose „giessen in ~X Tagen“, Knopf „Gegossen“ immer mit einem Tipp erreichbar.

## 2 Übersicht („Ein Blick genügt“)

![Übersicht Handy, hell: A Frost, B Botanik, C Stele](../../app/docs/concept/vergleich/home_handy_hell.png)

![Übersicht Handy, dunkel](../../app/docs/concept/vergleich/home_handy_dunkel.png)

![Übersicht Desktop, hell](../../app/docs/concept/vergleich/home_desktop_hell.png)

![Übersicht Desktop, dunkel](../../app/docs/concept/vergleich/home_desktop_dunkel.png)

Kopf mit Gesamtzustand („1 Pflanze hat Durst“) und Tropfen-Charakter, Zähler, Hinweisliste, dann die Karten: zuerst
durstig, dann Hinweise, dann nach Prognose. Durstige Karten haben direkt den Knopf „Gegossen“.

## 3 Pflanzen-Detail

![Detail Handy, hell](../../app/docs/concept/vergleich/pflanze_handy_hell.png)

![Detail Handy, dunkel](../../app/docs/concept/vergleich/pflanze_handy_dunkel.png)

![Detail Desktop, hell: links Zustand und Verlauf, rechts Prognose, Profil, Sensor](../../app/docs/concept/vergleich/pflanze_desktop_hell.png)

![Detail Desktop, dunkel](../../app/docs/concept/vergleich/pflanze_desktop_dunkel.png)

Verlauf mit Zielband, Giessschwelle, Giess-Markern (Tropfen oben) und gestrichelter Prognose bis zur Schwelle mit
Unsicherheitsband. Darunter (im Bild nicht sichtbar, im Entwurf scrollbar): Tagebuch mit „Stimmt / War nicht gegossen“
für erkannte Giessungen.

## 4 Raumplan und Editor

![Raumplan Handy, hell](../../app/docs/concept/vergleich/raum_handy_hell.png)

![Raumplan Handy, dunkel](../../app/docs/concept/vergleich/raum_handy_dunkel.png)

![Raumplan Desktop, hell](../../app/docs/concept/vergleich/raum_desktop_hell.png)

![Raumplan Desktop, dunkel](../../app/docs/concept/vergleich/raum_desktop_dunkel.png)

![Raumplan-Editor Handy (Werkzeuge, Sonnenseite, Raummasse)](../../app/docs/concept/vergleich/raumeditor_handy_hell.png)

![Raumplan-Editor Desktop](../../app/docs/concept/vergleich/raumeditor_desktop_hell.png)

## 5 Dashboard (Bildschirm, Kollegen)

![Dashboard Desktop/TV, hell](../../app/docs/concept/vergleich/dashboard_desktop_hell.png)

![Dashboard Desktop/TV, dunkel](../../app/docs/concept/vergleich/dashboard_desktop_dunkel.png)

![Dashboard Handy, hell](../../app/docs/concept/vergleich/dashboard_handy_hell.png)

![Dashboard Handy, dunkel](../../app/docs/concept/vergleich/dashboard_handy_dunkel.png)

## 6 Statistik, Sensoren und Akku

![Statistik Handy, hell](../../app/docs/concept/vergleich/statistik_handy_hell.png)

![Statistik Handy, dunkel](../../app/docs/concept/vergleich/statistik_handy_dunkel.png)

![Statistik Desktop, hell](../../app/docs/concept/vergleich/statistik_desktop_hell.png)

![Statistik Desktop, dunkel (unten: Sensoren mit Spannungsverlauf, Energieanteilen und Funk)](../../app/docs/concept/vergleich/statistik_desktop_dunkel.png)

## 7 Einstellungen und Profil

![Einstellungen Handy, hell](../../app/docs/concept/vergleich/einstellungen_handy_hell.png)

![Einstellungen Handy, dunkel](../../app/docs/concept/vergleich/einstellungen_handy_dunkel.png)

![Einstellungen Desktop, hell: Benachrichtigungen mit Kennzeichnung lokal / Firmennetz / Entscheid offen](../../app/docs/concept/vergleich/einstellungen_desktop_hell.png)

![Einstellungen Desktop, dunkel](../../app/docs/concept/vergleich/einstellungen_desktop_dunkel.png)

![Profil Handy: Art mit Bild, Zielbereich mit Startwert-Hinweis](../../app/docs/concept/vergleich/profil_handy_hell.png)

![Profil Desktop](../../app/docs/concept/vergleich/profil_desktop_hell.png)

## 8 Bewertung und Empfehlung

| Kriterium | A Frost | B Botanik | C Stele |
|---|---|---|---|
| Ein Blick / Lesbarkeit | sehr gut; leichte Zahlen etwas zarter | sehr gut, kräftigste Zahlen | sehr gut, ruhigste Flächen |
| Apple-Nähe | am nächsten (Glas, runde Schrift, schwebende Leiste) | nah (Pillen, Sheets), plakativer | nah im Geist (Reduktion), eigenständige Formen |
| Passt zur Hardware (grau/hellblau, Tropfen an der Fuge) | gut (Farben) | schwach (Grün dominiert) | **sehr gut** (Fuge, Fasen, Ton in Ton, leuchtende Tropfen) |
| Verspielt | mittel–hoch | **hoch** | mittel (Spiel nur über die Tropfen) |
| Dunkelmodus | sehr schön (glühende Tropfen) | sehr stimmungsvoll | sehr gut für den Büro-Bildschirm |
| Risiko | Glas-Effekte kosten auf alten Handys Leistung; wirkt evtl. generisch | Grün konkurriert mit „ok“-Grün der Ampel; Pflanzenbilder sind nur Illustrationen | grauer Pflanzen-Look kann zu nüchtern wirken |

**Empfehlung: A „Frost“ als Grundlage mit zwei Elementen aus C** – die Farbfuge (blaues Band mit dunkler Linie) im
Kopf und die leuchtenden LED-Tropfen als einzige kräftige Farbe. Begründung: Frost erfüllt den Wunsch „Apple-Design,
modern, einfach“ am direktesten, die Hellblau/Warmgrau-Palette ist die der Hardware, und der Tropfen-Charakter
bleibt der verspielte Mittelpunkt. Wer die App klar als Teil der fluidi-Hardware erkennen will, wählt C pur; wer es
am lebendigsten mag, B. B hat den Nachteil, dass Grün sowohl Marke als auch „alles gut“ bedeutet.

## 9 Fragen an den Auftraggeber

1. **Entwurf:** A, B, C oder eine Mischung (z. B. A mit Farbfuge aus C)? Gibt es Elemente, die unbedingt bleiben
   oder wegfallen sollen?
2. **Tropfen-Charakter mit Gesicht:** überall (Karten, Detail, Raumplan, Dashboard) oder nur in Übersicht und
   Dashboard?
3. **Pflanzen-Bilder:** reichen die Illustrationen (11 Arten), oder wird ein eigenes Foto pro Pflanze gewünscht
   (später, Konzept F-24)?
4. **„Gegossen“-Knopf** in der unteren Leiste (eine Hand) – passt das, oder lieber ein Plus-Knopf für mehrere Aktionen?
5. **Dashboard:** hell oder dunkel auf dem Büro-Bildschirm, mit oder ohne Raumplan?
6. **Benachrichtigungen:** Entscheid F-1 bis F-3 im Konzept (Kap. 12, 13, 17) – Web Push ja/nein, E-Mail über
   Firmen-SMTP, Dashboard für Kollegen über HTTP oder HTTPS.
