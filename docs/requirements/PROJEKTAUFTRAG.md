# Projektauftrag (Original des Auftraggebers, 2026-11-06, wörtlich übernommen)

> Dieses Dokument ist die unveränderte Vorgabe. Ergänzungen und Antworten stehen in
> `CLIENT_INPUT.md`, die daraus abgeleitete Spezifikation in `REQUIREMENTS.md`.

# Projekt Tröpfli – kapazitiver Pflanzen-Feuchtigkeitssensor, Produktentwicklung von A bis Z

**Produktname: Tröpfli.** Verwende diesen Namen durchgehend: in Dokumenten, im
Repository (`troepfli`), in Firmware und App, auf dem PCB-Silkscreen und im Design.

## Deine Rolle
Du arbeitest als komplettes Hardware-Produktentwicklungsteam in einer Person: Elektronik
(Schaltung, PCB-Layout, RF/Antenne), Embedded-Firmware, Mechanik/Gehäuse (3D-Druck),
Simulation (Schaltung, FEM, Feldsimulation), Software (PWA/Gateway), Industriedesign,
Visualisierung und Dokumentation. Du arbeitest gründlich, prüfst deine Ergebnisse mit den
verfügbaren Tools und erfindest niemals Bauteile, Footprints, LCSC-Nummern oder
Datenblattwerte.

## Ziel
Ein System aus mehreren kleinen Sensoren und einem lokalen Gateway.

Der **Sensor** wird wie ein Stab in einen Pflanzentopf gesteckt. Oben sitzt ein möglichst
kleiner, abgedichteter Kopf mit Elektronik und Energiequelle, unten eine Sonde. Er misst
die Bodenfeuchte kapazitiv und die Temperatur, loggt die Daten und überträgt sie per Funk
ausschliesslich lokal.

Das **Gateway** (im Büro oder zuhause, dauerhaft mit Strom versorgt) sammelt die Daten
aller Sensoren, speichert sie und stellt eine PWA im lokalen Netz bereit, die auf
Smartphone (iOS und Android) und PC funktioniert.

Endergebnis: ein vollständiges, bestellfertiges Paket ("ready to build"):
- Sensor-PCB inkl. kompletter Bestückung direkt bei JLCPCB bestellbar (Gerber, BOM, CPL)
- Gateway: fertiges Board (z. B. Entwicklungsboard oder Raspberry Pi) oder eigenes PCB,
  begründet
- druckfertige Gehäusedateien für einen Bambu-Lab-Drucker (Sensor und Gateway)
- flashbare Firmware für Sensor und Gateway
- lauffähige PWA
- Dokumentation für Zusammenbau, Inbetriebnahme, Kalibrierung und Test
- fotorealistische Renderings

## Vorgaben (vom Auftraggeber geklärt)
- **Stückzahlen:** zuerst ein Prototyp-Los in der kleinsten sinnvollen Bestellmenge bei
  JLC (aktuelle Mindestmengen für PCB und PCBA recherchieren und angeben), danach eine
  Serie von 10–15 Sensoren.
- **Kosten:** tiefer Preis ist zwingend. Ziel unter 10 CHF pro Sensor (Stückkosten bei
  10–15 Stück, alle Teile inkl. Energiequelle und Gehäusematerial). Das Gateway wird nur
  einmal gebraucht und separat ausgewiesen. Weise Stückkosten und einmalige Kosten pro
  Bestellung (Setup, Schablone, Extended-Part-Gebühren, Versand) getrennt aus, für
  Prototyp-Los und Serie. Bevorzuge JLC Basic Parts konsequent. Wenn das Ziel nicht
  erreichbar ist, sag es klar und zeig, was es kosten würde und warum.
- **Grösse:** Sondenlänge im Boden ca. 100 mm. Der Kopf oben soll so klein wie möglich
  sein. AAA/AA-Batterien sind ausgeschlossen (zu gross).
- **Energie:** lange Laufzeit ist sehr wichtig. Nur wenige Messungen pro Tag, zusätzlich
  manuelle Aktualisierung aus der App. Vergleiche mindestens:
  (a) kleiner LiPo mit USB-C-Laden und vollständiger Schutzschaltung,
  (b) Knopfzelle (z. B. CR2032, CR2450 oder ähnlich) mit sehr sparsamem BLE-Chip.
  Berücksichtige Pulsbelastbarkeit und Innenwiderstand von Knopfzellen (Pufferkondensator,
  Spannungseinbruch beim Senden), Kopfgrösse, Wechsel- bzw. Ladeaufwand und Kosten.
  Rechne für jede Variante ein Energiebudget und eine realistische Laufzeit.
- **Sicherheit hat höchste Priorität.** Keine Zertifizierung nötig (Eigengebrauch), aber
  das Brandrisiko muss minimal sein. Bei Lithium-Akkus: Zellen mit Schutzschaltung,
  Laderegler mit Temperaturüberwachung (NTC), Strombegrenzung, Verpolschutz, keine
  mechanische Belastung der Zelle, keine Feuchtigkeit an der Zelle, Abschaltung bei
  Tiefentladung. Bei Knopfzellen: Verpolschutz, sicherer Halter, keine Ladung möglich.
  Wenn eine nicht wiederaufladbare Lösung sicherer und günstiger ist und die Laufzeit
  stimmt, empfiehl sie aktiv. Erstelle für die gewählte Lösung eine kurze Risikoanalyse
  (FMEA-light).
- **Funk und Gateway:** alles strikt lokal, keine Cloud. Ein Gateway im Büro oder zuhause
  ist ausdrücklich erlaubt. Bevorzugte Richtung: sparsamer Funk (z. B. BLE) zwischen
  Sensor und Gateway, Gateway im WLAN/LAN. Vergleiche mit WLAN direkt im Sensor. Prüfe
  die Funkreichweite im Büro und ob ein Gateway reicht. Zwei-Wege-Kommunikation ist nötig
  (manuelle Messung, Kalibrierung, Einstellungen, Firmware-Updates).
- **App:** PWA, ausgeliefert vom Gateway. Löse das Thema sicherer Kontext (HTTPS für
  Service Worker/Installation im LAN) praktikabel und dokumentiere es.
- **Bedienelemente:** eine Status-LED (Batteriestand, Verbindungsstatus, Fehler) und ein
  Taster (z. B. Pairing, manuelle Messung, Reset). Kein Display. Leg Blinkmuster und
  Tastenfunktionen fest und achte auf den Energieverbrauch der LED.
- **Design:** schlicht und modern. Erstelle mehrere Designvorschläge (Renderings), die ich
  verfeinere und freigebe. Der Name Tröpfli (Wassertropfen, freundlich, schweizerisch)
  darf die Formsprache inspirieren, z. B. eine weiche Tropfenform des Kopfes oder ein
  dezentes Tropfensymbol. Schlag auch ein einfaches Logo bzw. eine Wortmarke für Gehäuse,
  Silkscreen und PWA vor. Die PWA heisst ebenfalls Tröpfli.
- **Namen in der Technik:** wo Umlaute Probleme machen (Dateinamen, Repository,
  Code-Bezeichner, BLE-Gerätenamen, Hostnamen), konsequent `troepfli` verwenden. In der
  sichtbaren Oberfläche und in Dokumenten immer "Tröpfli". Sensoren melden sich z. B. als
  `troepfli-XXXX` (eindeutige ID).
- **3D-Druck:** Bambu-Lab-Drucker vorhanden, alle gängigen Materialien möglich.
- **Bestückung:** komplett durch JLC. Teile, die JLC nicht bestücken kann (z. B. Akku,
  Batteriehalter), separat auflisten und den manuellen Schritt minimal halten.

## Technische Anforderungen
1. **Kapazitive Messung, Sonde als Teil des Haupt-PCB.** Ein durchgehendes PCB: oben die
   Elektronik im abgedichteten Gehäuse, unten bildet die Platine selbst die Sonde. Kein
   freiliegendes Metall im Sondenbereich.
   - Elektroden möglichst auf Innenlagen eines 4-Lagen-PCB, Aussenlagen im Sondenbereich
     ohne Kupfer. Mit 2-Lagen-Variante plus Coating vergleichen (Empfindlichkeit, Kosten,
     Lebensdauer).
   - Keine Vias im nassen Bereich (oder gefüllt und abgedeckt, begründen).
   - Kupferabstand zur Platinenkontur im Sondenbereich mindestens ca. 1 mm.
   - Versiegelung der Schnittkanten und der Sonde bewerten (Conformal Coating, Epoxid,
     Schrumpfschlauch mit Kleber), mit Anleitung.
   - Definierte Dichtlinie am Übergang Sonde/Gehäuse, sodass kein Wasser an der Platine
     entlang ins Gehäuse kriecht.
   - Masse- bzw. Guard-Struktur zwischen Elektronik und Sonde. Antenne am oberen Ende,
     maximal weit von der Erde entfernt, mit korrektem Keepout.
   - PCB-Dicke (1.6 oder 2.0 mm) und Sondenform (Spitze, Markierung der maximalen
     Stecktiefe) festlegen. FEM-Prüfung auf Biegung beim Einstecken.
   - Elektrodengeometrie per Feldsimulation optimieren (Empfindlichkeit, Messvolumen,
     Einfluss der Isolationsdicke).
   - Langzeitdrift durch Feuchteaufnahme des FR4 berücksichtigen.
2. **Temperatur:** Bodentemperatur nahe der Dichtlinie unter dem Coating, optional
   Lufttemperatur im Kopf. Weitere Sensoren (Luftfeuchte, Licht) nur, wenn sie das
   Kosten- und Energieziel nicht gefährden.
3. **Kalibrierung und Kompensation:** Zwei-Punkt-Kalibrierung (trocken/nass) pro Sensor,
   in der App auslösbar und gespeichert. Temperaturkompensation.
4. **Logging:** Sensor puffert Messwerte mit Zeitstempel, wenn das Gateway nicht
   erreichbar ist. Gateway speichert die Historie dauerhaft. Zeitsynchronisierung.
5. **Firmware Sensor:** Deep Sleep, Messung mit Mittelung, einfaches Pairing neuer
   Sensoren, Firmware-Updates ohne Öffnen des Gehäuses (OTA über das Gateway),
   Geräte-ID, klar dokumentiertes Datenformat.
6. **Gateway:** Datenempfang, Speicherung, Web-Server für die PWA, Verwaltung der
   Sensoren, OTA-Verteilung. Optional MQTT bzw. Home-Assistant-Anbindung.
7. **PWA:** Übersicht aller Pflanzen, Verlauf/Diagramme, Batteriestand, Signalqualität,
   Pflanzen benennen, Schwellenwerte und Hinweis "giessen nötig", manuelle Messung
   auslösen, Kalibrierung, Datenexport (CSV).
8. **Gehäuse:** FDM-druckbar, spritzwassergeschützt (Giessen von oben), Batteriefach bzw.
   Ladeport dicht und zugänglich, LED sichtbar, Taster bedienbar, Material für Feuchte
   und UV geeignet (z. B. PETG/ASA statt PLA).

(Abschnitte zu Tools, Agenten, Phasen, Projektstruktur und Arbeitsregeln sind in `CLAUDE.md`
und `.claude/agents/` umgesetzt.)
