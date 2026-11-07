"""Gemeinsame Parameter der Feldsimulation Sonde fluidi (Phase 4a, Welle 1).

Alle Zahlen mit Quelle oder als ANNAHME gekennzeichnet. Quellenkuerzel siehe REPORT.md Kap. 9.
Einheiten: Laengen in mm, Leitfaehigkeit in S/m, Frequenz in Hz.
"""
import math

EPS0 = 8.8541878128e-12  # F/m

# --- Lagenaufbau 4 Lagen 1.6 mm, JLC04161H-7628 (Standard "No requirement") ----------------------
# [JLC-STACK] docs/references/JLCPCB_NOTES.md Kap. 4: Prepreg L1-L2 0.2104 mm, Kern 1.065 mm,
# Innenkupfer 0.0152 mm, Er Prepreg 7628 = 4.4.
T_CU_IN = 0.0152
STACK_4L = {
    # Name: (Prepreg L1-L2, Kern L2-L3, Er Prepreg)   Quelle: JLCPCB_NOTES.md Kap. 4 (JLC bzw. DRITTQUELLE)
    "7628 (Standard)": (0.2104, 1.065, 4.4),
    "1080": (0.0764, 1.265, 3.91),
    "2116": (0.116, 1.265, 4.16),
    "7628A": (0.294, 0.865, 4.4),   # Er 7628/1080-Mischung: ANNAHME 4.4
    "7628E": (0.428, 0.600, 4.4),
    "7628C": (0.646, 0.150, 4.4),
}
STACK_DEFAULT = "7628 (Standard)"
ER_CORE = 4.4          # ANNAHME: Kern wie Prepreg (JLC nennt fuer den Kern keinen Wert in NOTES Kap. 4)

# 2-Lagen 1.6 mm: Laminat ohne Aussenkupfer ~1.53 mm (1.6 mm Nenndicke inkl. 2 x 35 um Cu) ANNAHME
T_2L = 1.53
ER_2L = 4.5            # JLCPCB_NOTES.md Tab. 3 "FR-4 2 Lagen 4.5"

# FR4-Verlustfaktor und Feuchteaufnahme: [DUPONT] Khan, DuPont 1999, Tab. 1 (Glass/FR4, 7628, 25 degC):
#   trocken: Dk 4.83 / Df 0.015 @1 MHz, Dk 4.69 / Df 0.012 @10 MHz
#   gesaettigt 85 %RH/85 degC (0.66-0.68 % Feuchte): Dk 5.38 / Df 0.020 @1 MHz, Dk 5.15 / Df 0.018 @10 MHz
#   -> Dk +11.4 % (1 MHz), +9.8 % (10 MHz); Temperatur 25->80 degC trocken: Dk +5.4 % @1 MHz
TAN_D_FR4_DRY = 0.013    # Mittel 1-10 MHz
TAN_D_FR4_WET = 0.019
DK_FR4_MOIST_REL = 0.10  # +10 % bei Saettigung (Band 0.03 ... 0.12)
DK_FR4_TC = 0.054 / 55   # 1/K, ~0.1 %/K (25 -> 80 degC)

# Loetstopplack [JLC-SM] JLC Impedance Calculator Guide (2026-09-16): Er 3.8, 1.2 mil (0.030 mm) auf
# Laminat, 0.6 mil (0.015 mm) auf Kupfer.
ER_MASK = 3.8
T_MASK_LAM = 0.030
T_MASK_CU = 0.015

# Schutzlack/Coating [MG4200] MG Chemicals 4200UV TDS: Er 3.3, Df 0.03 @1 MHz, Schichtdicke 50-125 um.
ER_COAT = 3.3
TAN_D_COAT = 0.03

# Sondengeometrie (Mechanik phase3_sleeve_mechanik.md; D-010): Breite 20 mm
W_PROBE = 20.0
EDGE_CLEAR = 1.0       # REQ-MECH-06 Kupfer >= 1.0 mm zur Kontur

# --- Substrat --------------------------------------------------------------------------------------
# [TOPP] Topp, Davis, Annan 1980, WRR 16(3) 574-582, doi:10.1029/WR016i003p00574 (mineralische Boeden, TDR)


def eps_topp(theta):
    return 3.03 + 9.3 * theta + 146.0 * theta**2 - 76.7 * theta**3


EPS_AIR = 1.0
EPS_DRY = 4.0      # Topp theta ~0.05 -> 3.8; Band 3-5
EPS_WET = 25.0     # Topp theta ~0.40 -> 25.2; Band 20-30
EPS_WATER = 80.0

# Leitfaehigkeit: [KLZH] Kantonales Labor ZH, Trinkwasser Aesch 2026-02-02: 307-359 uS/cm @25 degC
# (Einzelprobe 721 uS/cm). [PURDUE] HO-237 Tab. 2: PourThru-EC Topfsubstrat "low" 1.0-2.6, "normal"
# 2.7-4.6 mS/cm. Umrechnung Porenwasser -> Bulk nach [HILHORST] Diss. 1998, Gl. 4.16:
#   sigma_p = eps_w * sigma_b / (eps' - eps_off)  ->  sigma_b = sigma_p * (eps' - eps_off) / eps_w
EPS_W_PORE = 80.0
EPS_OFF = 4.0      # ANNAHME (Glasperlen 7.7 laut Hilhorst Gl. 4.17; mineralisch ~3-4)


def sigma_bulk(sigma_pore, eps_bulk, eps_off=EPS_OFF):
    return sigma_pore * max(eps_bulk - eps_off, 0.0) / EPS_W_PORE


SIGMA_PORE_CASES = {
    # Name: Porenwasser-Leitfaehigkeit S/m
    "Leitungswasser (0.035 S/m)": 0.035,
    "geduengt, PourThru 'low' (0.18 S/m)": 0.18,
    "geduengt, PourThru 'normal' (0.37 S/m)": 0.37,
}

F_BAND = (2e6, 4e6, 6e6)   # Messkette CONCEPTS 2.3: 2-6 MHz
