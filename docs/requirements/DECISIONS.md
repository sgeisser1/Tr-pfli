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
- **Status:** wartet auf Freigabe des Auftraggebers

### D-003 · 2026-11-06 · Feldsimulation der Sonde (offen)
- **Vorschlag:** Elmer FEM (Solver `StatElecSolve`, 3D, Netz aus gmsh) als Hauptwerkzeug,
  zusätzlich ein schnelles 2D-Querschnittsmodell in Python (`scikit-fem` + `gmsh`) für
  Parameterstudien (Elektrodenbreite, Abstand, Isolationsdicke).
- **Alternativen:** openEMS (für Elektrostatik bei niedriger Frequenz unnötig komplex, in Ubuntu
  24.04 nicht paketiert); FEMM (nur Windows/2D, schlecht skriptbar in WSL); FreeCAD-FEM mit
  Elmer (nutzt denselben Solver, bietet aber keinen Mehrwert gegenüber Skript).
- **Status:** wartet auf Freigabe des Auftraggebers
