# Tröpfli – Entscheidungsprotokoll

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
- **Status:** gültig, dem Auftraggeber zur Kenntnis

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
