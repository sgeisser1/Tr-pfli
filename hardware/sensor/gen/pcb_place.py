"""fluidi Sensor Rev B - Platzierung (Schnittstellen-Koordinaten X = x, Y = 53.5 - z, siehe
docs/interfaces/PCB_OUTLINE.md Rev B Kap. 1). Einzige Quelle der Bauteillagen fuer gen_pcb.py.

Feste Lagen (PCB_OUTLINE Kap. 5): D1 (0, 9.6), SW1 (-6.0, 8.4), XBT1/BT1 Zelle (3.0, 34.45) 90 Grad,
U3/C24 im Kragenfeld (Z5B, Freigabe Sicherheit mit K-1...K-3: Feld x >= -9.0) oder - Option u3="band" - im Band.
Antenne AN043 (Texas_SWRA117D_2.4GHz_Right: Einspeisung links, offenes Ende rechts), Ursprung = Speisepunkt.

Rotation in Grad nach KiCad (positiv = gegen den Uhrzeigersinn in der Draufsicht).
Seiten: "F" (bestueckt), "B" (nur Testpads TP4/TP5).
"""

ANT_X, ANT_Y = 0.35, 5.45          # Speisepunkt; Keepout X ANT_X-3.05 ... ANT_X+12.15, Y 0 ... 5.2
RF_Y = 6.38                         # HF-Kette (Reihenelemente auf dieser Linie)
U1_X, U1_Y = 6.0, 12.6              # CC2340 (rot 270: Pin 1 oben rechts)
PIN1_X = U1_X + 1.25                # = 7.55, senkrechte HF-Bahn

# S-Zuleitungen (Feld Kap. 8, angepasst: x -8.0 auf L2/In1, x -7.0 auf L3/In2, links der U3-Leitungen,
# siehe LAYOUT_REV_B.md); U3-Leitungen In2 laufen im Fach bei x 0.0/0.6/1.2 ins Band (kurz zu U1/R4/R5)
FEED_L2_X = -8.0
FEED_L3_X = -7.0
FEED_VIA_Y = 20.5
STUB_VIA_Y = 20.5
VBAT_X, VBAT_Y = 11.8, 6.35         # VBAT-Leitung In2: rechter Rand, dann oberer Rand (unter der Masse-Kante)
VBAT_VIA = (-12.25, 6.6)            # Uebergabevia VBAT neben Q1                   # Uebergabevias Innenlage In2 -> F/B am Bandende

# Kragenfeld U3 (Z5B, Sicherheit K-2: x >= -9.0; Vias >= 1.0 mm von der Kante, tented)
U3_KRAGEN = dict(U3=(-6.69, 47.9, 180), C24=(-8.45, 48.0, 90))
U3_GND_VIA2 = (-8.7, 46.95)        # zweites GND-Via fuer C24/U3 Pin 4 (Kante 1.3 mm, K-2)
# Vias im Kragenfeld: Spalte x -5.0 (Abstand Kante 4.8 mm, S-Zuleitung L2 bei -2.85)
U3_VIA_X = -5.0
U3_VIA_Y = dict(I2C_SDA=46.95, GND=47.59, I2C_SCL=48.23, SENS_PWR=48.87)
U3_LINE_X = dict(I2C_SDA=0.0, I2C_SCL=0.6, SENS_PWR=1.2)   # Innenlage In2 im Fach

PLACE = {
    # ref: (X, Y, rot, side)
    "AE1": (ANT_X, ANT_Y, 0, "F"),
    "D1": (0.0, 9.6, 180, "F"),       # 180 Grad: G_K/B_K links (zu R7/R8), R_K/Anode rechts
    "SW1": (-6.0, 8.4, 0, "F"),
    "BT1": (3.0, 34.45, 90, "F"),
    # HF-Kette, Reihenfolge von der Antenne: C20 (Pi, DNM) - R2 - C19 (DNM) - C18 - C17 - L2 - C16 - U1 Pin 1
    "C20": (-0.85, RF_Y + 0.48, 270, "F"),
    "R2": (0.65, RF_Y, 180, "F"),
    "C19": (2.14, RF_Y + 0.48, 270, "F"),
    "C18": (3.61, RF_Y, 180, "F"),
    "C17": (5.08, RF_Y + 0.48, 270, "F"),
    "L2": (6.57, RF_Y, 180, "F"),
    "C16": (PIN1_X + 0.48, 7.65, 0, "F"),
    # SoC und Umfeld
    "U1": (U1_X, U1_Y, 270, "F"),
    "Y1": (10.8, 12.6, 90, "F"),
    "C8": (9.6, 9.1, 90, "F"),          # VDDS Pin 24
    "C10": (6.05, 9.1, 180, "F"),       # VDDR Pin 2
    "C6": (2.3, 13.35, 180, "F"),      # VDDS Pin 11
    "C13": (2.3, 14.85, 0, "F"),        # RSTN
    "Y2": (3.2, 16.8, 180, "F"),        # 32 kHz
    "C14": (0.5, 16.8, 270, "F"),
    "C15": (5.77, 16.8, 270, "F"),
    "C12": (6.8, 16.4, 270, "F"),      # VDDD Pin 16
    "L1": (8.75, 16.5, 0, "F"),         # DCDC Pin 17
    "C7": (11.05, 15.3, 0, "F"),        # VDDS Pin 18
    "C9": (10.6, 17.0, 270, "F"),       # VDDR 10 uF
    "C11": (11.75, 17.0, 270, "F"),      # VDDR Pin 20
    # Puffer (Reihe unten, Laengsachse quer = parallel Biegelinie)
    "C1": (-10.35, 19.2, 0, "F"),
    "C2": (-5.64, 19.2, 0, "F"),
    "C3": (1.05, 19.2, 0, "F"),
    "C4": (5.76, 19.2, 0, "F"),
    "C5": (9.75, 19.2, 0, "F"),        # 10 uF VDDS
    "R1": (11.85, 19.2, 90, "F"),      # RSTN Pull-up
    # Verpolschutz oben links
    "Q1": (-10.95, 7.9, 90, "F"),
    # LED-Widerstaende zwischen SW1 und D1
    "R6": (1.78, 9.5, 270, "F"),
    "R7": (-2.1, 10.76, 90, "F"),
    "R8": (-2.1, 8.8, 270, "F"),
    # Messkette D3 (Spalten: links U5/U4/UART-Barrieren 2b, Mitte Q2/U6, rechts R3/C22/U2 nahe der S-Zuleitung)
    "U5": (-10.8, 11.6, 0, "F"),
    "U4": (-10.8, 14.25, 0, "F"),
    "R10": (-12.15, 16.9, 90, "F"),
    "R12": (-10.9, 16.9, 90, "F"),
    "C25": (-9.6, 16.9, 90, "F"),
    "Q2": (-6.95, 12.05, 0, "F"),
    "U6": (-6.9, 15.15, 0, "F"),
    "R13": (-7.9, 17.35, 0, "F"),
    "C22": (-4.45, 13.0, 90, "F"),
    "R3": (-3.4, 13.0, 90, "F"),
    "C21": (-2.6, 14.58, 0, "F"),
    "U2": (-2.6, 16.4, 0, "F"),
    # UART-Barrieren 2a (R2-A3: getrennt von 2b, eigene Loetstoppoeffnung, Abstand > 10 mm)
    "R9": (-0.2, 11.95, 0, "F"),
    "R11": (-2.1, 6.84, 90, "F"),     # neben R8 (gleiches Netz LED_B_UART_RX)
    # I2C-Pull-ups unten Mitte, nahe den Uebergabevias der U3-Leitungen (x 0 ... 1.2, Y 20.5)
    "R4": (-2.3, 18.6, 0, "F"),
    "R5": (-2.3, 19.65, 0, "F"),
    # Testpads Zellfach (Streifen x -12.7...-7.5, z 12...30 -> Y 23.5...41.5)
    "TP1": (-10.6, 25.5, 0, "F"),
    "TP2": (-10.6, 28.5, 0, "F"),
    "TP3": (-10.6, 31.5, 0, "F"),
    # Testpads B-Seite im Band
    "TP5": (-2.3, 17.9, 0, "B"),
    "TP4": (-8.0, 13.6, 0, "B"),
    # Sonde (Innenlagen), Platzhalter-Footprint mit Innenlagen-Pads
    "E1": (0.0, 100.0, 0, "F"),
}

# Option u3="band": Rueckfallebene (Sicherheit lehnt Z5B ab) -> U3/C24 ins Band
U3_BAND = dict(U3=(11.4, 7.05, 0), C24=(11.6, 9.0, 0))   # freie Ecke rechts oben, unter dem offenen Antennenende


def placement(u3="kragen"):
    p = dict(PLACE)
    src = U3_KRAGEN if u3 == "kragen" else U3_BAND
    for k, (x, y, r) in src.items():
        p[k] = (x, y, r, "F")
    return p
