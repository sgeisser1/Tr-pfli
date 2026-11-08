# fluidi – Entscheidungsprotokoll

Format: Nr. · Datum · Entscheid · Alternativen · Begründung · Quelle · Status

---

### D-001 · 2026-11-06 · Arbeitsumgebung WSL2 statt nativem Windows
- **Entscheid:** Alle Werkzeuge laufen in WSL2 Ubuntu 24.04. Die MCP-Server FreeCAD und Blender
  laufen dort ebenfalls (getestet: `platform.system() == "Linux"`).
- **Alternativen:** Windows-Installationen (FreeCAD 1.0, Blender 3.6, KiCad 10.0.5 vorhanden).
- **Begründung:** Die Versionen in WSL entsprechen den Vorgaben (FreeCAD 0.21.2, Blender 4.0.2)
  und sind mit den MCP-Servern verbunden. Ein einheitliches Linux-System macht die Skripte
  reproduzierbar.
- **Quelle:** `docs/reviews/phase0_toolcheck.md`
- **Status:** gültig

### D-002 · 2026-11-06 · KiCad-Version (offen)
- **Situation:** WSL hat KiCad 9.0.9 inkl. Python-API `pcbnew`; Windows hat KiCad 10.0.5
  (nur CLI aus WSL nutzbar, kein Python-Modul in WSL). Dateien, die KiCad 10 speichert,
  kann KiCad 9 nicht mehr lesen.
- **Vorschlag:** KiCad 10 auch in WSL installieren (offizielles PPA), dann einheitlich KiCad 10.
  Übergangsweise: Generator mit KiCad 9 erzeugen, mit KiCad 10 (Windows) zusätzlich prüfen.
- **Prüfung KiCad 9 vs. 10 (2026-11-06, auf Wunsch des Auftraggebers):**
  - Python-API `pcbnew` (SWIG): seit 9.0 veraltet, Entfernung offiziell erst in **11.0**
    geplant (dev-docs.kicad.org/en/apis-and-binding/pcbnew/). Im PPA-Paket
    `kicad_10.0.8~ubuntu24.04.1` geprüft: `pcbnew.py` und `_pcbnew.so` sind enthalten.
  - Stabilität: Forumsberichte über Abstürze und Probleme beim Verschieben von Bauteilen in der
    **GUI** von 10.0.x (u. a. 10.0.5, Windows); 10.0.6 brachte ca. 150–200 Bugfixes. Für
    `kicad-cli` und Skripte keine Berichte gefunden. PPA liefert 10.0.8.
  - KiCad 9.x wird nicht mehr aktiv gepflegt (letzte Version 9.0.9).
  - 3D: KiCad 10 liefert Bibliotheksmodelle nur noch als STEP; die Ubuntu-Pakete von KiCad 9
    hier ebenfalls nur STEP. Beide exportieren STEP und GLB → kein Nachteil für FreeCAD/Blender.
  - CLI: in 10 entfallen `pcb export gerber` (Einzeldatei) und HPGL; `gerbers`, `drill`, `pos`,
    `step`, `glb` bleiben. Kein Nachteil.
- **Entscheid:** KiCad **10.0.8** in WSL (PPA `kicad-10.0-releases`, bleibt innerhalb 10.x).
  Empfehlung an den Auftraggeber: Windows-Installation 10.0.5 ebenfalls auf 10.0.8 aktualisieren
  (GUI-Bugfixes, gleiche Version auf beiden Seiten). Projekt bleibt bis Release auf KiCad 10
  (wegen geplanter Entfernung von `pcbnew` in 11).
- **Status:** entschieden, Installation durch Auftraggeber

### D-003 · 2026-11-06 · Feldsimulation der Sonde (offen)
- **Vorschlag:** Elmer FEM (Solver `StatElecSolve`, 3D, Netz aus gmsh) als Hauptwerkzeug,
  zusätzlich ein schnelles 2D-Querschnittsmodell in Python (`scikit-fem` + `gmsh`) für
  Parameterstudien (Elektrodenbreite, Abstand, Isolationsdicke).
- **Alternativen:** openEMS (für Elektrostatik bei niedriger Frequenz unnötig komplex, in Ubuntu
  24.04 nicht paketiert); FEMM (nur Windows/2D, schlecht skriptbar in WSL); FreeCAD-FEM mit
  Elmer (nutzt denselben Solver, bietet aber keinen Mehrwert gegenüber Skript).
- **Entscheid:** Elmer 26.2 (PPA) installiert und verifiziert, Aufruf nur über `scripts/elmer.sh`;
  2D-Parameterstudien mit scikit-fem + gmsh in `.venv`.
- **Status:** entschieden (2026-11-06)

### D-004 · 2026-11-06 · Anforderungen v1.0 freigegeben
- **Entscheid:** `REQUIREMENTS.md` v1.0 nach zwei Prüfrunden (Sicherheit, Red Team, Firmware/Energie) vom Auftraggeber freigegeben.
- **Ergänzungen bei Freigabe:** LED signalisiert „Giessen nötig“ (REQ-UI-07); öffentlicher NTP für Gateway erlaubt; nur Innenbereich; privates Handy, Zertifikat installierbar; Drucker P1S.
- **Quelle:** Auftraggeber im Chat 2026-11-06; Prüfberichte `docs/reviews/phase1_*`.
- **Status:** gültig

### D-005 · 2026-11-06 · Definition Stückkosten (REQ-FAB-04)
- **Entscheid:** Stückkosten = alle Kosten, die pro Sensor anfallen (Bauteile mit passender Preisstaffel,
  Grenzkosten der Leiterplatte, Bestückung pro Lötstelle, Energiequelle, Gehäusematerial, Kleinteile,
  Ausschuss). Der Fixanteil des PCB-Preises pro Bestellung zählt zu den Einmalkosten. Zusätzlich werden
  Vollkosten pro Sensor (Total / Anzahl) ausgewiesen.
- **Begründung:** Lineare Aufteilung der vom Auftraggeber abgelesenen JLC-Preise: 2 L 1.6 mm 5.10 USD fix +
  0.358 USD/Platine; 4 L 1.6 mm 30.05 + 0.448; 4 L 2.0 mm 71.05 + 0.554. Vorher wurde der volle PCB-Preis
  den Stückkosten zugeschlagen, das Setup der Bestückung aber den Einmalkosten (Red Team K-2, Phase 2).
- **Alternativen:** voller PCB-Preis in Stückkosten (inkonsistent); nur Vollkosten (vermischt Prototyp-/Serieneffekte).
- **Status:** gültig, vom Auftraggeber bestätigt 2026-11-08 (Stückkosten 8.38 CHF ok; Vollkosten 17.84 CHF zur Kenntnis)

### D-006 · 2026-11-07 · Konzeptwahl: A-32
- **Entscheid (Auftraggeber):** Konzept **A-32**: TI CC2340R52 (QFN24) + RC-Oszillator (SN74LVC1G14, 2–6 MHz,
  ratiometrisch) + TMP1075DGKR + **Panasonic CR2032** im Clip-Halter, 2 × 100 µF Puffer, Programmierung über
  Dummy-Zellen-Adapter + UART-Pads mit 2 × 100 kΩ; 4 Lagen 1.6 mm, Economic PCBA; Gateway ESP32-S3 + RTC ohne Ladepfad.
- **Alternativen:** A (CR2450N, mehr Laufzeitreserve, Kopf 17 mm höher, 10.18 CHF), B (CH592, keine signierbaren
  Updates), C (LiPo, 65 °C nicht zulässig, 20.79 CHF), C-WLAN (Laufzeit Stunden).
- **Begründung:** erfüllt alle Muss-Anforderungen; Stückkosten 7.07 CHF; Kopf ≈ 28 × 13 × 45 mm; Laufzeit
  pessimistisch 17 Monate (12.5 im ungünstigsten Fall). Sicherheitsauflagen R2-A1…A4 und R2-W01 sind in Phase 4 nachzuweisen.
- **Quelle:** `docs/concepts/CONCEPTS.md` v0.3, Prüfberichte `docs/reviews/phase2_*`.
- **Status:** gültig

### D-007 · 2026-11-07 · Designvorgaben
- **Auftraggeber:** „schöne harte Formen“, schlichte, einfache Logos, aber auch etwas verspielt. Keine weiteren Vorgaben.

### D-008 · 2026-11-07 · Umbenennung „Tröpfli“ → „fluidi“
- **Entscheid (Auftraggeber):** Produkt, PWA, Logo und Repository heissen **fluidi** (klein geschrieben).
  Logo: Wortmarke „fluidi“ mit Wassertropfen als i-Punkte. Technische Namen ebenfalls `fluidi`
  (`fluidi-XXXX`, `fluidi.local`), da keine Umlaute mehr.
- **Umsetzung:** Alle Projektdateien ersetzt (Ausnahme: `PROJEKTAUFTRAG.md` bleibt wörtliches Original mit Hinweis).
  Renderings und Logos werden in Phase 3 neu erzeugt. GitHub-Repository-Umbenennung `Tr-pfli` → `fluidi`
  durch den Auftraggeber (GitHub → Settings → Repository name); danach wird der Remote angepasst.
- **Status:** gültig

### D-009 · 2026-11-07 · Designwahl P3 „Stele“ mit Änderungen (Auftraggeber)
- Kopf **P3 Stele**; Körper **grau** statt weiss (weiss verschmutzt), Band oben **hellblau** wie bisher,
  **Taster oben ebenfalls hellblau**; LED-Tropfenfenster bleibt, dahinter **RGB-LED** für farbige Zustände.
- Kopf 28 × 12–13 × 45 mm und 5 mm Abstand zur Erde bestätigt.
- **Kein Batteriefach hinten**, kein Warnaufdruck. Wunsch: Batteriewechsel durch Trennen an der Farbfuge
  blau/grau (Klick oder Schraube von unten), graues Teil nach unten abziehen → nur eine sichtbare Trennung.
  Machbarkeit (Dichtung, REQ-SAF-05, REQ-SAF-CC-04) wird geprüft.
- Gateway in denselben Farben; Antenne möglichst intern statt Stabantenne (Machbarkeit wird geprüft).

### D-010 · 2026-11-07 · Design P3 fluidi – Verfeinerung 1 (Auftraggeber)
- **Sensor freigegeben wie Verfeinerung 1** („perfekt, genau wie gewünscht“): Grau **Option 1 warmes Hellgrau #B9B5AC**,
  hellblaue Kappe und Taste, RGB-Tropfen, Logo Ton in Ton als Relief, Masse 28 × 13 × 48 mm, Sonde 20 mm, 5 mm Abstand.
- **LED-Farben:** Grün = ok/Messung gesendet · Blau = giessen nötig (bei schwacher Zelle Gelb) · Rot = Batterie tief/Fehler ·
  Gelb = Kopplung.
- **Änderungswünsche:** (1) Gateway-LED als Tropfen, der wie beim Sensor aus dem blauen Teil „heraustropft“.
  (2) Wortmarke: zwei blaue Tropfen sind zu viel, Schwarz ist zu hart → neue Varianten. (3) App-Icon als Kachel im
  Sensor-Look: oben Blau, unten Warmgrau, grün leuchtender Tropfen an der Grenze.

### D-011 · 2026-11-07 · Design Verfeinerung 2 (Auftraggeber)
- **Gateway freigegeben** (G1 v3: Warmgrau hell/Hellblau, Tropfen-LED an der Farbkante, Antenne innen).
- **Wortmarke: Variante v3a** – warmes Dunkelgrau #4F4B45, erster i-Punkt grau, letzter i-Punkt hellblau
  (`docs/design/logo/fluidi_logo_v3a*.svg`).
- **App-Icon:** hochaufgelöste fotorealistische **Nahaufnahme des Sensors**: quadratisch, leuchtender **blauer Tropfen
  gross in der Mitte**, oben Hellblau, unten Warmgrau, Übergang als sichtbarer **Spalt** (Vorlage: Screenshot des Auftraggebers).

### D-012 · 2026-11-07 · Phase 3 abgeschlossen, App-Icon final
- **App-Icon** (Sensor-Nahaufnahme, blauer Tropfen, `app/icons/`) vom Auftraggeber freigegeben. Design komplett:
  `docs/design/P3_FLUIDI.md` / `P3_fluidi_v3.pdf`. **Phase 3 freigegeben, Phase 4 gestartet** (Auftraggeber 2026-11-07).
- Vorhandene Hardware beim Auftraggeber: Seeed XIAO nRF52840 Sense (Nutzung siehe Phase 4).

### D-013 · 2026-11-07 · Pufferkondensatoren im Prototyp
- **Entscheid (Projektleiter):** Prototyp-Los mit **4 × 100 µF bestückt** (C3/C4 nicht DNM). SPICE (simulation/spice/supply):
  Advertising-Einbruch mit 2 × 100 µF pessimistisch 246 mV (> 0.2 V, REQ-ENE-06), mit 4 × 100 µF 143 mV.
  Für die Serie wird nach Messung von DC-Bias und Leckstrom am Muster entschieden (2 oder 4); die pessimistische
  Laufzeit mit 4 × 100 µF und Datenblatt-Leckgrenze liegt unter 12 Monaten (CONCEPTS v0.2: 11.9) – deshalb nur Prototyp.
- **Status:** gültig bis Messung am Prototyp

### D-014 · 2026-11-07 · Gateway-Plattform: Raspberry Pi Zero 2 W
- **Entscheid (Auftraggeber):** Gateway auf **Raspberry Pi Zero 2 W** (beim Auftraggeber vorhanden) statt ESP32-S3,
  „so sind wir flexibler, was genau wir dann damit bauen wollen“ (Plattform für Analyse, Speicherung, Tracking, Dashboard,
  spätere ML-Auswertungen). Ersetzt die Gateway-Wahl aus D-006 und RB-05 („Pi nur wenn nötig“ – jetzt begründet).
- **Bluetooth:** zuerst das eingebaute BLE des Pi Zero 2 W; **XIAO nRF52840 Sense** (vorhanden) als Option für einen
  separaten BLE-Empfänger per USB, falls Koexistenz WLAN/BLE oder Reichweite nicht genügen.
- **Folgen:** Gateway-Software in Python (SQLite, HTTPS, systemd, SD-Schutz), OTA zum Sensor per Python-SMP-Client;
  Gateway-Gehäuse G1 wird auf den Pi Zero 2 W (65 × 30 mm, Micro-USB-Speisung) angepasst, Optik bleibt;
  ESP-IDF nicht mehr nötig.
- **Status:** gültig

### D-015 · 2026-11-07 · Software-Wünsche des Auftraggebers (Grundlage Software-Konzept)
- **Nutzer:** hauptsächlich der Auftraggeber (einziger Admin, App auf seinem Handy). Optional eine **öffentliche
  Nur-Lese-Ansicht/Dashboard** im Firmennetz für Kollegen (eigener Port/Route, ohne Login, abschaltbar).
- **Alltag:** ein Blick genügt, um den Zustand aller Pflanzen zu kennen; **Benachrichtigungen bei kritischen Zuständen**.
- **Funktionen:** Übersicht mit Ampel im Tropfen; Verläufe und Analysen; **Prognosen** (nächstes Giessen);
  **Giess-Tagebuch** (Button „gegossen“ + automatische Erkennung); **Pflanzenprofile** (Name, Art/Typ, Visualisierung,
  Substrat, artspezifische Feuchtebereiche); **Raumplan** mit Pflanzenpositionen und Fenstern; **Dashboard-Modus**
  (auch für Kollegen); **Statistiken** inkl. Akku/Stromverbrauch der Sensoren; Sensor- und Batterieverwaltung;
  **verspielte Elemente** erwünscht; Daten später für **ML und Auswertungen** nutzbar.
- **Gestaltung:** modern, „super cool“, einfach und intuitiv, Apple-Design als Vorbild; **hell/dunkel/automatisch**;
  primär Handy, aber auch am PC gut; Farbschema aus Referenzbildern übernehmbar (weiche Hellblau-Verläufe,
  Glas-Karten, schwebende untere Navigation; grüne Botanik-Referenzen) – eigene Vorschläge erwünscht.

### D-016 · 2026-11-07 · Knicklast der Sonde (REQ-MECH-10)
- **Entscheid (Auftraggeber):** Option a – REQ-MECH-10 axial 50 N gilt **mit geführter Spitze**; Anleitung: in fester Erde
  vorstechen. FEM (simulation/fem/REPORT.md): Knicklast frei 29 N (SF 0.58), geführt 236 N (SF 4.7).
- **Alternativen:** 2.0-mm-Platine (≈ +40–90 USD je Bestellung, Standard-PCBA), Versteifung/breitere Sonde (Designänderung).

### D-017 · 2026-11-07 · Raumklima-Sensor im Gateway (Wunsch Auftraggeber)
- Im Pi-Gateway wird ein Sensor für **Lufttemperatur und Luftfeuchte** eingeplant (I²C-Breakout am GPIO-Header,
  Typ in Phase 4 Welle 2, z. B. Sensirion SHT4x-Klasse). Thermisch getrennte, belüftete Kammer im Gehäuse.
  Daten fliessen in Dashboard/Analysen (Raumklima vs. Austrocknung der Töpfe).

### D-018 · 2026-11-07 · Messkette D3 (Salz/Dünger)
- **Entscheid (Auftraggeber):** Messkette **D3**: Schmitt-Oszillator 17–36 MHz (R3 1 kΩ) + Teiler ÷8 (3 × SN74LVC1G80,
  C473331) vor dem CC2340-Timer, P-FET-Schaltung, Testpad PROBE_SENSE; R3 auf 10 kΩ umlötbar für Vergleich mit Variante A.
  App: Taste „gedüngt“ + Salzhinweis aus der Zeitreihe. REQ-MES-11 (Soll) offen bis Becherversuch (OP-K3) am Muster.
- **Quelle:** docs/concepts/MESSKETTE_SALZ.md, simulation/field/REPORT.md.

### Info Auftraggeber · 2026-11-07 · Pi Zero 2 W Masszeichnung
- 65 × 30 mm, Eckradius 3.0 mm, 4 × M2.5-Bohrungen Ø 2.75 ± 0.05 mm, Lochabstand 58 × 23 mm (Lochmitte 3.5 mm vom Rand).
  Höhen (Platinendicke, Bauteile, Micro-USB) noch am Board zu messen.

### D-019 · 2026-11-07 · Kopfproportion V4
- **Entscheid (Auftraggeber):** Sensorkopf **V4 ≈ 34 × 13 × 57.5 mm** (Überschlag ±2 mm), blaue Kappe 14 mm (≈ 24 %),
  Fuge/Tropfen bei z ≈ 43.5 mm (graue Hülse als Sichtschale über dem dichten Kern), Platine im Kopf ≈ 26 mm breit,
  einseitig bestückt (Economic PCBA). Genaue Masse aus Layout (Welle 2). Ersetzt die Masse aus D-010 (28 × 13 × 48).
- **Quelle:** docs/design/PROPORTIONEN.md/.pdf, hardware/sensor/out/FLOORPLAN_OPTIONS.md (Option f: Temperatursensor im Kragen).

### D-020 · 2026-11-07 · Software-Entscheide (F-1 … F-8)
- **Stil A „Frost“** (allein, ohne Mischung). Tropfen-Charakter mit Gesicht **überall**.
- **Benachrichtigungen strikt lokal** für den Start (In-App, Badge, Sensor-LED, Dashboard); Auftraggeber nutzt ein
  **Google Pixel 10 (Android)**, kein iPhone. Push (via Google FCM) evtl. später als Option. **Keine E-Mail-Hinweise.**
- **Dashboard** für Kollegen als Nur-Lese-Seite ohne Login (HTTP-Port im LAN, abschaltbar).
- **Feuchteprofile:** drei Klassen trocken / mittel / feucht, ergänzt um eine recherchierte Artenliste mit
  **Giessverhalten** (z. B. „gut durchgiessen, dann abtrocknen lassen bis …“ vs. „gleichmässig feucht halten“) mit Quellen.
- **Raumplan:** ein Raum für Rev A; der Auftraggeber liefert später einen genaueren Plan.

### D-021 · 2026-11-07 · Pflanzenprofile (Projektleiter)
- 40 Artenprofile mit Regime A (abtrocknen lassen) / B (oberste Schicht abtrocknen) / C (gleichmässig feucht) / D (Sonderfall),
  65 Quellen (Universitäts-Merkblätter, RHS, NYBG, AOS): `docs/software/PFLANZENPROFILE.md`, `app/data/species.json`.
  Schwellen sind Startwerte (ANNAHME): A 15 %, B 30 %, C 45 %, Ziel nach Giessen ≥ 80 %, Winterfaktor Nov–Feb.
- **Entscheide:** (1) „Zu nass“ wird erst **48 h nach einer Giessung** geprüft (sonst Fehlalarm nach jeder korrekten Giessung).
  (2) **Efeutute → Regime A „trocken“**, weil beide Quellen „abtrocknen lassen“ nennen.
- Offen: belegte Abtrocknungstiefe für Yucca, Olive, Alocasia, Kentia; widersprüchliche Quellen bei Ficus benjamina, Hoya, Basilikum
  (in der Tabelle vermerkt). Zitate vor Verwendung in der App stichprobenweise gegenlesen.

### D-022 · 2026-11-07 · Gateway-Details (Projektleiter)
- `public_read` (Lesen ohne Login über die API) ab Werk **aus**; Kollegen sehen nur das öffentliche **Dashboard auf HTTP-Port 8080**
  (nur lesen, abschaltbar). Einrichtungscode beim ersten Start wird vom Installationsskript per SSH angezeigt (SSH danach aus).
  Startkalibrierung 13.3/40 pF bleibt ANNAHME bis zur Messung am Muster.
- Git-Historie bereinigt (Auftraggeber-OK): FEM-/Elmer-Arbeitsdateien und 2 × 64-MB-FCStd aus allen Commits entfernt
  (Repo 427 → 247 MB), Tags unverändert, Sicherung der alten Historie als Bundle im Scratchpad.

### D-023 · 2026-11-08 · Layout Rev B: Via-in-Pad im Zellfach (L-1) und Fachlänge V-K (L-2/LS-W1) (Projektleiter)
- **L-1 Via-in-Pad im Zellfach zulässig mit Auflagen** (Entscheid Sicherheit, `docs/reviews/phase4_layout_revb_sicherheit.md`):
  Clip-VBAT und Minuspad brauchen ein Via, weil das Schott kein Aussenkupfer zulässt; gefüllt und überkupfert (JLC
  „Epoxy Filled & Capped“/POFV) erfüllt REQ-MECH-05. Auflagen A-1 (TP3/GND im Fach entfällt → 4 VIP; GND für den
  Dummy-Adapter über das Minuspad), A-2 (POFV verbindlich in Bestellung, ohne POFV keine Bestellung), A-3 (Querschliff
  am Muster), A-4 (Isolationswiderstand beim Flutungstest), A-5 (diese Notiz + PCB_OUTLINE Rev C Z4).
  Alternative „TP1/TP2 auf B ins Band“ verworfen: POFV bleibt ohnehin nötig (kostengleich), und nach dem Schott-Verguss
  wäre kein UART-Zugang mehr möglich.
- **V-K Fach 0.7 mm länger** (Vorschlag Mechanik, `docs/reviews/phase4_kollision_mechanik.md`): Hülsenboden 2.0 → 1.3 mm,
  Kragen/Tasche/Mutter/O-Ring-Nut 0.7 mm tiefer (Vergusskante z 1.3), Fach 24.2 mm, Zelle im Layout 0.35 mm tiefer.
  Damit Clip-Pads ≥ 0.30 mm (RSS) zu beiden Vergusskanten (LS-W1). Aussenmasse unverändert.
  Alternativen: Rev C nominal 0.20 mm je Seite (verfehlt LS-W1); „Zelle 0.4 mm tiefer“ allein (Pad 0.27 mm im Kragen).
  Begründung: Sicherheit vor Kosten; V-K kostet nichts, ändert nur das Innere. **Bedingung:** FEM (Hülsenboden 1.3 mm,
  Sonde mit Vergusskante z 1.3) erfüllt weiterhin REQ-MECH-10, sonst Vorlage an den Auftraggeber.
- **M-4 Taster:** Tastenhub 0.6 → 0.8 mm und Quetschrippe an der Gabel umsetzen (Toleranzkette Spalt 0.05…0.61 mm).
- **EP-2 LED:** Pulse ≤ 5 ms (FW-4); lange Leuchtphasen dadurch halb so hell (wahrgenommen ≈ 70–80 %, ANNAHME) –
  akzeptiert für den Prototyp, PROTOTYP-PRÜFUNG E6 (Sichtbarkeit), ggf. Vorwiderstände anpassen.

### D-024 · 2026-11-08 · Erstprogrammierung der Sensoren (Projektleiter, Red-Team B-4/W-4)
- **Entscheid:** Programmieradapter Rev 1: Waveshare CH343 USB-UART-Board (VIO extern), Speisung 2.0 V über die
  Dummy-Zelle (XC6206P332 → 2 × XC6206P202, getrennter Regler für VIO), Schmitt-Puffer SN74AUP1G17 ≤ 3 cm am TP1-Stift.
  Muster vor dem Verguss: **Behelf** mit Labornetzteil 2.0–2.2 V und CH343-RXD an **R9 Pad 1** (DIO6), Draht vor dem
  Einsetzen der Zelle entfernen. Ablauf: `docs/manuals/PROGRAMMIEREN_SENSOR.md`.
- **Alternativen:** 1.8 V (nur 40–70 mV Reserve zu VDDS min), ohne Puffer (Low ≥ 0.64 V, vom CH343 nicht lesbar),
  SN74LVC1G17 (Leckstrom ±5 µA über 200 kΩ → bis 1 V).
- **Quelle:** `hardware/programmer/README.md`, `simulation/spice/programmer/prog_uart_report.txt` (Kapazitäten ANNAHME).
- Offen: Sicherheitsprüfung des Adapters und Mechanik des Federstiftkopfs (Phase 5); Bootloader-Strom (W-10) PROTOTYP-PRÜFUNG.

### D-025 · 2026-11-08 · Auslegungen für den Prototyp-Test (Projektleiter, **vom Auftraggeber freigegeben 2026-11-08**)
- **Abschaltschwelle (WS-06):** Abnahme gegen FW-5 (2.4 V VDD unter Last, `docs/interfaces/PINMAP_SENSOR.md`) statt
  2.0 V aus REQ-ENE-06, weil REQ-ENE-06 den Wert ausdrücklich als ANNAHME bis zur Chipwahl führt. 2.4 V ist strenger
  (mehr Reserve für Flash-Schreiben und Funk) und kostet rechnerisch Restkapazität (`phase5_energiebudget_final.md`).
- **Leckstrom-Grenze REQ-ENE-08 (W-6):** „Maximalwert“ der MLCC-Leckströme wird am Muster bestimmt: gemessener
  Höchstwert (E14, 25/50 °C, Sonnenprofil) × 1.5 ersetzt die Katalog-Leckgrenze; Entscheidungsregel 2 oder 4 × 100 µF
  nach `docs/reviews/phase5_energiebudget_final.md` Kap. W-6.
- **Testplan-Widersprüche WS-01…WS-18:** entschieden in `docs/reviews/phase5_testplan_prototyp.md` Kap. 10 (EP-01…EP-18).
- Alternativen: Anforderungen wörtlich (2.0 V; Katalog-Maximalwert → REQ-ENE-02 mit 4 × 100 µF nicht erfüllbar).
- Quelle: Testplan Entwurf 2, Firmware-Bericht Phase 5, Sicherheit Runde 3.

### D-026 · 2026-11-08 · Tastermechanik Rev C: Muster drucken mit Auflagen (Projektleiter, nach 3 Prüfrunden)
- **Entscheid:** Kappe/Stössel Stand `842f670` (60°-Keil, Verdrehsicherung, Worst Case +0.17 mm) werden für die Muster
  gedruckt. Red-Team C-2 (Überlast der Zunge bei 20–50 N auf die Taste) bleibt **offen für die Serienfreigabe**; Folge
  wäre Tastenausfall, keine Gefährdung. Auflagen: Tastenkraft vor dem ersten Kappenverguss messen (≤ 12 N, > 15 N
  stopp), Klemmring-Passprobe und Membran zusätzlich abdichten, Nase glätten, M-T2/PT11.08 mit 20 N, 50 N und Fall
  1 m; Anleitung „beim Einstecken nicht auf die Taste drücken“.
- **Alternativen:** harter Tastenanschlag (abgelehnt: Schaltpunkt streut 0.05–0.65 mm), versenkte Taste (nur ≈ 0.4 mm
  Decke über dem Elektronikraum), nachgiebiges Element (bräuchte vorgespannte Feder). Für **Rev D**: Taster mit
  Betätiger in z direkt unter dem Stössel (Layoutänderung).
- **Quelle:** `docs/reviews/phase5_mechanik_redteam.md` (Runde 1–3), `mechanical/sensor/check_sensor.txt` 2a–2e.

### D-027 · 2026-11-08 · Gateway-LED vorläufig (Auftraggeber)
- **Entscheid:** Vorschlag `docs/reviews/phase5_gateway_led.md` vorläufig angenommen: Blitz alle 5 s = ok, schnelles
  Blinken = Kopplung, aus = Fehler/Nacht; 3-mm-LED an GPIO17 ohne Platine.
- **Alternativen:** siehe Vorlage. **Status:** gültig „für den Moment“, Anpassung nach Mustertest möglich.

### D-028 · 2026-11-08 · Gateway ohne RTC (Auftraggeber)
- **Entscheid:** Kein RTC-Modul im Gateway (weder Muster noch Serie). Zeit per NTP über das Geschäfts-WLAN; ohne
  Netz greift der vorhandene Rückfall (Handyzeit beim Öffnen der App, nachträgliche Korrektur, `phase5_gateway_zeit.md`).
- **Alternativen:** Adafruit 4282 DS3231 (≈ 15 CHF, Platzproblem F-5, CR1220 im Gerät).
- **Begründung:** Gateway steht dauerhaft im Geschäfts-WLAN; spart Kosten, eine Knopfzelle und Platz.
- **Status:** gültig. Folge: G4/G5 aus BOM_GATEWAY, RTC-Platzhalter aus dem Gehäuse, CR1220 entfällt.

### D-029 · 2026-11-08 · Klimasensor Gateway: kleineres SHT4x-Breakout (Auftraggeber, Variante c)
- **Entscheid:** Statt Grove SHT41 (20 × 40 mm, nicht an Lager) ein kleineres SHT4x-Breakout, das in die Klimakammer
  passt (I2C 0x44, D-017). Auswahl mit Datenblatt, Massen und Bezugsquelle in Phase 6.
- **Alternativen:** (a) Sensor aussen am Kabel, (b) Gateway grösser.
- **Status:** gültig. Teilewahl Phase 6: **DFRobot Fermion SHT40 SEN0428** (14 × 17 mm, bastelgarage.ch Art. 421989, CHF 11.90), Kammer-Nut auf 17 mm (Mechanik).

### Freigabe Phase 5 · 2026-11-08
- Auftraggeber gibt Phase 5 frei und startet Phase 6. Musterbestellung erst am Schluss (nach Phase 6).

### D-030 · 2026-11-09 · Vergussmasse und Sondenversiegelung (Orchestrator, nach Sicherheit R1+R2 ohne Veto)
- **Entscheid:** Electrolube **ER2223** (2K-Epoxid, Resin Pack 250 g) für Schott, Kragen und Kantenversiegelung der
  Sonde; Sondenflächen ohne Zusatzschicht (Feldsimulation `simulation/field/coat_epoxy.py`: 100 µm kosten 12–17 %
  Spanne). Verarbeitung Variante **M-A** (Beutel einmal ungemischt abfüllen, je Sitzung ≥ 8 g wägen) unter MA-1…MA-5;
  bis dahin M-B (ganzer Beutel). Kosten: Verbrauch in den Stückkosten (≈ 0.33 CHF), Beutel und Zubehör als
  Einmalkosten (D-005).
- **MA-6 (Orchestrator):** M-A gilt auch ohne Antwort von Electrolube, wenn MA-1, MA-2, MA-4 umgesetzt und V-3 und V-6
  bestanden sind.
- **Freigabebedingungen:** `docs/concepts/vergussmasse_versiegelung.md` D-030 (1–5): SDB Teil B in Landessprache und
  Handschuh-Beständigkeitsliste vor dem ersten Beutel; V-1…V-3 vor dem Musterverguss; PT11.19 (≥ 2 Muster), PT11.23
  und Tg-Nachweis (Electrolube oder V-6) vor der Serie, sonst Rückfallmasse Kap. 9a.
- **Alternativen:** ER2221 (gefüllt, Tg unbekannt, Rückfall), MG 832HT (H360), Stycast 2651-40 (≈ 300 CHF), ER2188/832B (Tg zu tief).
- **Quelle:** `docs/reviews/phase6_vergussmasse_sicherheit.md` (R1, R2), Konzept, MONTAGE_SENSOR Kap. 3a.
- **Status:** gültig mit Auflagen.

### D-031 · 2026-11-09 · USB-UART Programmierplatz: Waveshare PL2303 (type A) V2 statt CH343 (Orchestrator)
- **Entscheid:** PL2303-Board (pi-shop.ch 11757, CHF 8.90, gleiche Sendung wie Gateway-Teile) mit Bedingungen B1–B6
  (`hardware/programmer/README.md` Kap. 9): Weg A nur mit Puffer U4; Weg B 2.0 V, höchstens 2.1 V, 10 mA,
  USB zuerst ein / zuletzt ab; Eingangsprüfung je Board. PA-6 (470 Ω VIO→GND am Adapter) angenommen.
- **Alternativen:** Waveshare CH343 (kein CH-Händler, Auslandsversand); Adapter mit festem 3.3-V-Pegel (ungeeignet).
- **Quelle:** `simulation/spice/programmer/prog_uart_pl2303_report.txt`, `docs/datasheets/Prolific_PL2303GS_Datasheet_Rev1.0.4.pdf` S. 39.
- **Status:** gültig; Sicherheitsprüfung der Anleitung PROGRAMMIEREN_SENSOR v1.2 folgt in der Phase-6-Prüfrunde.
