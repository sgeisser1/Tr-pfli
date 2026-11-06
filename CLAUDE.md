# Tröpfli – Projektregeln für alle Agenten

Kapazitiver Pflanzen-Feuchtesensor (Stab mit PCB-Sonde, ~100 mm im Boden) plus lokales
Gateway mit PWA. Strikt lokal, keine Cloud. Projektleitung: Orchestrator (Hauptsitzung).
Der Auftraggeber gibt jede Phase frei.

## Namen
- Sichtbar (UI, Dokumente, Silkscreen-Logo): **Tröpfli**
- Technisch (Dateien, Code, BLE-Namen, Hostnamen, Repo): **troepfli**, z. B. `troepfli-XXXX`

## Prioritäten
Sicherheit > Kosten > Komfort. Ziel: < 10 CHF pro Sensor bei 10–15 Stück (alles inkl.
Energiequelle und Gehäusematerial). JLC **Basic Parts** bevorzugen.

## Nichts erfinden
- Keine Bauteile, Footprints, LCSC-Nummern, Pinbelegungen oder Datenblattwerte aus dem Gedächtnis.
- Jede Bauteilangabe zitiert die **lokale** Datei mit Seite/Tabelle, z. B.
  `docs/datasheets/TI_TPS7A02_Datasheet_RevC.pdf, S. 12, Tab. 6.5`.
- Annahmen als **ANNAHME** kennzeichnen. Was erst am Prototyp prüfbar ist, als
  **PROTOTYP-PRÜFUNG** kennzeichnen.
- Ergebnisse mit Tools verifizieren (ERC, DRC, Simulation, Build), nicht nur behaupten.

## Bauteildokumentation
- Herstellerdatenblatt (aktuellste Version) nach `docs/datasheets/`, App Notes, Referenzdesigns,
  Errata nach `docs/appnotes/`, JLC-Regeln, Material-/Coating-Datenblätter nach `docs/references/`.
- Dateiname: `Hersteller_Teilenummer_Dokumenttyp_Revision.pdf` (ASCII, keine Umlaute/Leerzeichen).
- Register `docs/datasheets/INDEX.csv` (Spalten: Ref, Funktion, Hersteller, Teilenummer, LCSC,
  Basic/Extended, Gehäuse/Footprint, Dok-Revision, Quelle-URL, Abrufdatum, lokaler Pfad, Bemerkung).
  **Neue Bauteile sofort eintragen**, nicht erst am Ende. Nicht herunterladbare Dokumente
  (Login usw.) im Register vermerken und dem Orchestrator melden.
- Entscheidungen in `docs/requirements/DECISIONS.md` (Datum, Entscheid, Alternativen,
  Begründung, Quelle).

## Prüfregeln
- Jedes wichtige Ergebnis prüft ein **anderer** Agent mit frischem Kontext (Anforderungen +
  Ergebnis, nicht die Begründungskette).
- Prüfer verifizieren **selbst**: ERC/DRC neu laufen lassen, Rechnungen nachrechnen,
  LCSC-Nummern/Pins/Footprints gegen das lokale Datenblatt prüfen.
- Befunde: **kritisch / wichtig / klein**, je mit Begründung und Vorschlag.
  Ersteller antwortet je Befund: *umgesetzt* / *abgelehnt (Grund)*.
- Max. 2–3 Prüfrunden. Danach entscheidet der Orchestrator oder legt es dem Auftraggeber vor.
- Prüfberichte nach `docs/reviews/<phase>_<thema>_<pruefer>.md`.
- Der Sicherheits-Agent hat ein **Veto**: ein kritischer Sicherheitsbefund blockiert die Freigabe.

## Arbeitsumgebung (Stand Phase 0, siehe docs/reviews/phase0_toolcheck.md)
- Alles läuft in **WSL2 Ubuntu 24.04** (Linux), auch die MCP-Server FreeCAD 0.21.2 und
  Blender 4.0.2. Windows-Laufwerk unter `/mnt/c`.
- KiCad: WSL hat KiCad **9.0.9** inkl. Python-Modul `pcbnew`; Windows hat KiCad **10.0.5**
  (`/mnt/c/Users/steph/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe`, Pfade per
  `wslpath -w` übergeben). Formatfrage siehe DECISIONS.md.
- FEM: FreeCAD-FEM mit CalculiX (`ccx`) und gmsh funktionieren.
- SPICE: `ngspice -b` (Version 42).
- Blender: Cycles nur CPU, **ohne OpenImageDenoise** → `scene.cycles.use_denoising = False`,
  dafür mehr Samples. Keine Asset-Bibliotheken/Generatoren: Szene per Skript aufbauen.
- `sudo` ist passwortgeschützt: **nichts installieren** ohne Freigabe des Auftraggebers.
- Reproduzierbarkeit: Generatoren und Berechnungen als Skript unter `scripts/` bzw. im
  jeweiligen Fachordner; Ergebnisse müssen per Skript neu erzeugbar sein.
- Temporäres in den Scratchpad-Ordner, nicht ins Repo.

## Ablage
`docs/{requirements,concepts,datasheets,appnotes,references,reviews,manuals}`,
`hardware/{sensor,gateway}`, `mechanical`, `simulation/{spice,field,fem}`,
`firmware/{sensor,gateway}`, `app`, `renders`, `scripts`, `production/rev-X`.
