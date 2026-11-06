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
