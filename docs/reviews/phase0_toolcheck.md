# Phase 0 – Toolcheck (2026-11-06)

Rohausgabe: `phase0_toolcheck_output.txt` (erzeugt mit `scripts/toolcheck.sh`).
Umgebung: WSL2 Ubuntu 24.04, Ryzen 7 3700X (16 Threads), 54 GB RAM, 945 GB frei.

| Werkzeug | Version | Test | Ergebnis |
|---|---|---|---|
| FreeCAD-MCP | FreeCAD 0.21.2 (Linux), Addon 0.1.28 | Box 100×20×1.6 mm, gmsh-Netz (16 471 Knoten), CalculiX-Kragträger 10 N | ✅ 22.09 mm / 117.1 MPa; Handrechnung 22.2 mm / 117 MPa |
| freecadcmd | 0.21.2 | Version | ✅ |
| Blender-MCP | Blender 4.0.2 (Linux), Addon 1.8 | Material per Node, Cycles- und EEVEE-Render | ✅ Cycles CPU 128 spp 640×480 in 1 s; **kein OpenImageDenoise** im Build → Denoising aus |
| KiCad (WSL) | 9.0.9, Python `pcbnew` | 4-Lagen-Board per Skript, DRC, Gerber, STEP, leerer Schaltplan ERC + PDF | ✅ |
| KiCad (Windows) | 10.0.5 `kicad-cli.exe` | DRC/ERC auf WSL-Dateien | ✅ (deutschsprachige Ausgabe) |
| ngspice | 42 | RC-Puffer Knopfzelle | ✅ 2.870 V, Handrechnung 2.870 V |
| gmsh | 4.12.1 (CLI) | Netz in FreeCAD | ✅ (Python-Modul fehlt) |
| CalculiX | `/usr/bin/ccx` | über FreeCAD-FEM | ✅ |
| Websuche / WebFetch | – | JLC-PCBA-Mindestmenge | ✅ |
| JLC-Teilesuche (API) | – | C25744 | ✅ Basic, Lager 16.49 Mio |
| Datenblatt-Download | curl | LCSC-PDF, TI-PDF | ✅ |
| **PDF lesen** | – | Read-Tool auf PDF | ❌ `pdftoppm` (poppler-utils) fehlt |
| Elmer FEM | – | – | ❌ nicht installiert |
| pip / venv | – | – | ❌ `python3-pip`, `python3-venv` fehlen |
| zip | – | – | ❌ fehlt (für Gerber-ZIP; Python `zipfile` als Ersatz möglich) |
| Node.js/npm | – | – | ❌ fehlt (für PWA-Tests optional) |
| Firmware-Toolchain | – | – | ⏸ erst nach Konzeptwahl (Phase 2) |

## Auffälligkeiten
- Die Vorgabe nennt Windows; tatsächlich laufen beide MCP-Server in WSL. Siehe D-001.
- KiCad-Versionen gemischt (9 in WSL, 10 unter Windows). Siehe D-002.
- `sudo` braucht ein Passwort; Installationen führt der Auftraggeber aus.
- Nebenbefund FEM-Test: Ein 1.6 mm FR4-Streifen 20 mm breit erreicht bei 10 N seitlicher Last
  am Ende eines 100 mm Hebels ~117 MPa (FR4-Biegefestigkeit typisch 300–400 MPa, ANNAHME bis
  Materialdatenblatt vorliegt). Relevant für Sondenbreite, Dicke und die Einsteckanleitung.
