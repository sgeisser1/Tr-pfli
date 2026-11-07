"""fluidi Sensor Rev B - DRC-Regeldatei (.kicad_dru): JLC-Mindestwerte + Projektregeln.

Quellen:
- JLC 4 Lagen: docs/references/JLCPCB_NOTES.md Kap. 3 (Abstand/Breite 0.09, Bohrung >= 0.15/0.2 empfohlen,
  Via-Durchmesser < 0.45 kostet Aufpreis, Innenlage Via-Bohrung-Kupfer 0.2, Kupfer-Kontur >= 0.2, Silk >= 0.15 / 1.0).
- Projekt: docs/interfaces/PCB_OUTLINE.md Rev B Kap. 3 (Zonen), simulation/field/REPORT.md Kap. 8 (Kupfer >= 1.25 zur
  Kontur), REQ-MECH-05/06, S2-W03/S3-K1 (keine Vias im Fach/Schott), Sicherheit Phase 4 K-1...K-3.
Die benannten Regelflaechen (Z1_ANTENNE, Z3_SCHOTT, Z4_FACH, VIP_FACH, Z3_Z4_INNEN, Z5_KRAGEN, Z5B_FELD, Z5A_DICHT,
Z6_Z7_NASS, Z5A_Z7_SONDE) legt pcb_build.py an.
"""

DRU = """(version 1)
# fluidi Sensor Rev B - erzeugt von hardware/sensor/gen/pcb_rules.py (nicht von Hand aendern)

# ---------------- JLC 4 Lagen 1.6 mm (JLCPCB_NOTES.md Kap. 3) - Entwurf mit Reserve
(rule "JLC Abstand Kupfer >= 0.10"
  (constraint clearance (min 0.1mm)))
(rule "JLC Leiterbahnbreite >= 0.10"
  (condition "A.Type == 'Track'")
  (constraint track_width (min 0.1mm)))
(rule "JLC Via Durchmesser >= 0.45 (ohne Aufpreis), Bohrung >= 0.20"
  (condition "A.Type == 'Via'")
  (constraint via_diameter (min 0.45mm))
  (constraint hole_size (min 0.2mm)))
(rule "JLC Restring Via >= 0.075"
  (condition "A.Type == 'Via'")
  (constraint annular_width (min 0.075mm)))
(rule "JLC Bohrabstand >= 0.25"
  (constraint hole_to_hole (min 0.25mm)))
(rule "JLC Bohrung - Kupfer >= 0.20 (Innenlage Via)"
  (constraint hole_clearance (min 0.2mm)))
(rule "JLC Kupfer - Kontur >= 0.30"
  (constraint edge_clearance (min 0.3mm)))
(rule "JLC Silkscreen Text >= 1.0 / 0.15"
  (layer "?.Silkscreen")
  (condition "A.Type == 'Text' || A.Type == 'Field'")
  (constraint text_height (min 1.0mm))
  (constraint text_thickness (min 0.15mm)))

# ---------------- Projektregeln (spaetere Regeln haben Vorrang)
(rule "K-3 Innenlagen Schott/Zellfach >= 1.0 mm zur Kante"
  (layer inner)
  (condition "A.intersectsArea('Z3_Z4_INNEN')")
  (constraint edge_clearance (min 1.0mm)))
(rule "Zellfach: Vias nur als Via-in-Pad (gefuellt+ueberkupfert, REQ-MECH-05)"
  (condition "A.Type == 'Via' && A.intersectsArea('Z4_FACH') && !A.intersectsArea('VIP_FACH')")
  (constraint disallow via))
(rule "Schott: keine Vias (S3-K1)"
  (condition "A.Type == 'Via' && A.intersectsArea('Z3_SCHOTT')")
  (constraint disallow via))
(rule "K-2 Kragenfeld: Vias >= 1.0 mm zur Kante"
  (condition "A.Type == 'Via' && A.intersectsArea('Z5B_FELD')")
  (constraint edge_clearance (min 1.0mm)))
(rule "K-1 Dichtstreifen Innenlagen nur GND/Guard und Sonde"
  (layer inner)
  (condition "A.intersectsArea('Z5A_DICHT') && A.NetName != 'GND' && A.NetName != '/PROBE_SENSE'")
  (constraint disallow track via zone pad))
(rule "Sonde/Dichtstreifen: Kupfer >= 1.25 mm zur Kontur (Feld Kap. 8, REQ-MECH-06)"
  (condition "A.intersectsArea('Z5A_Z7_SONDE')")
  (constraint edge_clearance (min 1.25mm)))
(rule "Nass/Kragen/Dichtstreifen: keine Vias (REQ-MECH-05)"
  (condition "A.Type == 'Via' && (A.intersectsArea('Z5A_Z7_SONDE') || (A.intersectsArea('Z5_KRAGEN') && !A.intersectsArea('Z5B_FELD')))")
  (constraint disallow via))
"""


def write(path):
    open(path, "w").write(DRU)
