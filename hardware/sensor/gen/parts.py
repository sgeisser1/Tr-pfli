"""fluidi Sensor Rev B - Bauteil- und Netzdefinition (einzige Quelle fuer Schaltplan, BOM, Register, Pinplan).

Jede Zeile: Referenz, Symbol, Wert, Footprint, Teiledaten-Schluessel, Position, Rotation, Pin->Netz, DNP.
Teiledaten (LCSC, Hersteller, MPN, JLC-Kategorie, Datenblatt) in PARTDB; JLC-Status 2026-11-07 per
JLC-Teilesuche (selectSmtComponentList) geprueft, siehe hardware/sensor/gen/jlc_check.json (neu erzeugen mit
jlc_check.py).

Rev B (2026-11-07) gegenueber Rev A:
- Messkette D3 (D-018, docs/concepts/MESSKETTE_SALZ.md): R3 1 kOhm (auf 10 kOhm umloetbar), Teiler /8 aus
  3 x SN74LVC1G80 (U4-U6), Lastschalter Q2 AO3401A an DIO11 (OSC_EN_N, R13 100k Pull-up), Cref2/C23 entfaellt,
  Testpad TP5 PROBE_SENSE, TP4 an MEAS_CLK (B-Seite).
- FLOORPLAN_OPTIONS Option (f): U3 TMP1075NDRLR (SOT-563) mit C24 im Sondenkragen, SW1 TS-1088-AR02016.
- D-013: Prototyp mit 4 x 100 uF (C3/C4 bestueckt).
"""

DS = "docs/datasheets/"

# key: (Hersteller, MPN, LCSC, JLC-Kategorie, Datenblatt lokal, Kurzbeschreibung)
PARTDB = {
    "CC2340": ("Texas Instruments", "CC2340R52E0RGER", "C20416850", "Extended", DS + "TI_CC2340R5_Datasheet_SWRS272F.pdf",
               "BLE-SoC 512 kB, VQFN-24 4x4"),
    "XT48": ("HCI (Suzhou HangJing)", "XC32M4-48.000-F08NLDT", "C2925606", "Extended",
             DS + "HCI_XC32M4-48.000-F08NLDT_Datasheet_LCSC-2022-05.pdf", "Quarz 48 MHz 8 pF 3225"),
    "XT32": ("Seiko Epson", "Q13FC13500003", "C99010", "Extended", DS + "Epson_Q13FC13500003_Datasheet_LCSC-2018-10.pdf",
             "Quarz 32.768 kHz 9 pF FC-135"),
    "L10U": ("Sunlord", "WPN201610H100MT", "C89132", "Extended", DS + "Sunlord_WPN201610H100MT_Datasheet_LCSC-2023-10.pdf",
             "Leistungsspule 10 uH 2016"),
    "L2N7": ("Sunlord", "SDCL1005C2N7STDF", "C27123", "Extended", DS + "Sunlord_SDCL1005-Serie_Datasheet_LCSC-2023-10.pdf",
             "HF-Spule 2.7 nH 0402"),
    "C100U": ("Samsung Electro-Mechanics", "CL31A107MQHNNNE", "C15008", "Basic",
              DS + "Samsung_CL31A107MQHNNNE_Catalog_2015-11.pdf", "MLCC 100 uF 6.3 V X5R 1206"),
    "C10U": ("Samsung Electro-Mechanics", "CL05A106MQ5NUNC", "C15525", "Basic",
             DS + "Samsung_CL05A106MQ5NUNC_Datasheet_LCSC-2022-08.pdf", "MLCC 10 uF 6.3 V X5R 0402"),
    "C1U": ("Samsung Electro-Mechanics", "CL05A105KA5NQNC", "C52923", "Basic", DS + "Samsung_CL05-Serie_Datasheet_LCSC-2023-04.pdf",
            "MLCC 1 uF 25 V X5R 0402"),
    "C100N": ("Samsung Electro-Mechanics", "CL05B104KO5NNNC", "C1525", "Basic", DS + "Samsung_CL05-Serie_Datasheet_LCSC-2023-04.pdf",
              "MLCC 100 nF 16 V X7R 0402"),
    "C15P": ("FH (Fenghua)", "0402CG150J500NT", "C1548", "Basic", DS + "FH_0402CG-Serie_Datasheet_LCSC-2023-04.pdf",
             "MLCC 15 pF C0G 0402"),
    "C22P": ("FH (Fenghua)", "0402CG220J500NT", "C1555", "Basic", DS + "FH_0402CG-Serie_Datasheet_LCSC-2023-04.pdf",
             "MLCC 22 pF C0G 0402"),
    "C100P": ("FH (Fenghua)", "0402CG101J500NT", "C1546", "Basic", DS + "FH_0402CG-Serie_Datasheet_LCSC-2023-04.pdf",
              "MLCC 100 pF C0G 0402"),
    "C1P5": ("FH (Fenghua)", "0402CG1R5C500NT", "C1552", "Preferred", DS + "FH_0402CG-Serie_Datasheet_LCSC-2023-04.pdf",
             "MLCC 1.5 pF C0G 0402"),
    "R0": ("UNI-ROYAL", "0402WGF0000TCE", "C17168", "Basic", DS + "UNI-ROYAL_0402WGF-Serie_Datasheet_LCSC-2024-11.pdf",
           "R 0 Ohm 0402"),
    "R100": ("UNI-ROYAL", "0402WGF1000TCE", "C25076", "Basic", DS + "UNI-ROYAL_0402WGF-Serie_Datasheet_LCSC-2024-11.pdf",
             "R 100 Ohm 1 % 0402"),
    "R200": ("UNI-ROYAL", "0402WGF2000TCE", "C25087", "Basic", DS + "UNI-ROYAL_0402WGF-Serie_Datasheet_LCSC-2024-11.pdf",
             "R 200 Ohm 1 % 0402"),
    "R470": ("UNI-ROYAL", "0402WGF4700TCE", "C25117", "Basic", DS + "UNI-ROYAL_0402WGF-Serie_Datasheet_LCSC-2024-11.pdf",
             "R 470 Ohm 1 % 0402"),
    "R4K7": ("UNI-ROYAL", "0402WGF4701TCE", "C25900", "Basic", DS + "UNI-ROYAL_0402WGF-Serie_Datasheet_LCSC-2024-11.pdf",
             "R 4.7 kOhm 1 % 0402"),
    "R1K": ("UNI-ROYAL", "0402WGF1001TCE", "C11702", "Basic", DS + "UNI-ROYAL_0402WGF-Serie_Datasheet_LCSC-2024-11.pdf",
            "R 1 kOhm 1 % 0402"),
    "R100K": ("UNI-ROYAL", "0402WGF1003TCE", "C25741", "Basic", DS + "UNI-ROYAL_0402WGF-Serie_Datasheet_LCSC-2024-11.pdf",
              "R 100 kOhm 1 % 0402"),
    "LVC14": ("Texas Instruments", "SN74LVC1G14DCKR", "C35740", "Extended", DS + "TI_SN74LVC1G14_Datasheet_SCES218AA.pdf",
              "Schmitt-Inverter SC-70-5"),
    "TMPN": ("Texas Instruments", "TMP1075NDRLR", "C3663690", "Extended", DS + "TI_TMP1075_Datasheet_SBOS854F.pdf",
             "Temperatursensor I2C SOT-563 (TMP1075N, 1.62-3.6 V)"),
    "LVC80": ("Texas Instruments", "SN74LVC1G80DCKR", "C473331", "Extended", DS + "TI_SN74LVC1G80_Datasheet_SCES221T.pdf",
              "D-Flipflop Q invertiert SC-70-5 (Teiler /2)"),
    "AO3401": ("Alpha & Omega", "AO3401A", "C15127", "Basic", DS + "AOS_AO3401A_Datasheet_Rev3.1.pdf", "P-MOSFET SOT-23"),
    "KS3034": ("Keystone", "3034TR", "C5213768", "Extended", DS + "Keystone_3034_Catalog_M65.pdf",
               "Halter CR2032 SMT (Zelle Panasonic CR2032 lokal)"),
    "LEDRGB": ("TUOZHAN", "P4-1615G2B2R4TS2-06T-001-24", "C7496855", "Extended",
               DS + "TUOZHAN_P4-1615G2B2R4TS2-06T-001-24_Datasheet_A0.pdf", "RGB-LED 1615 gem. Anode"),
    "TS1088": ("XUNPU", "TS-1088-AR02016", "C720477", "Basic", DS + "XUNPU_TS-1088-AR02016_Datasheet_LCSC-2022-06.pdf",
               "Taster SMD 3.9x3.0x2.0"),
    "DNM": ("-", "nicht bestueckt (Wert nach Abstimmung)", "", "-", "", "Footprint 0402, DNM"),
    # Leiterplattenstrukturen / Pads (keine Bestueckung)
    "PCB": ("-", "Leiterplattenstruktur", "", "-", "", "nicht bestueckt"),
}

FP_R = "Resistor_SMD:R_0402_1005Metric"
FP_C = "Capacitor_SMD:C_0402_1005Metric"
FP_C1206 = "Capacitor_SMD:C_1206_3216Metric"
FP_L0402 = "Inductor_SMD:L_0402_1005Metric"

S = 2.54  # Raster


def g(n):
    return round(n * S, 4)


# Bauteile: ref, lib_id, value, footprint, part-key, x, y, rot, {pin: net}, dnp, Bemerkung
# Netz "GND"/"VDD" -> Power-Symbol; "NC" -> No-Connect-Flag
COMPONENTS = []


def add(ref, lib, val, fp, key, x, y, rot, conns, dnp=False, note=""):
    COMPONENTS.append(dict(ref=ref, lib=lib, val=val, fp=fp, key=key, x=g(x), y=g(y), rot=rot, conns=conns, dnp=dnp,
                           note=note))


# ---------------- Energie (oben links)
add("BT1", "Device:Battery_Cell", "CR2032 / Keystone 3034TR", "fluidi:BatteryHolder_Keystone_3034_1x20mm_NegPad4mm",
    "KS3034", 10, 24, 0, {"1": "VBAT", "2": "GND"},
    note="Clip = Plus, Minus = ENIG-Pad 4x4 mm (R2-W01); Zelle Panasonic CR2032 lokal; Halter 90 Grad gedreht (Mechanik S-01)")
add("Q1", "fluidi:AO3401A", "AO3401A", "Package_TO_SOT_SMD:SOT-23", "AO3401", 17, 19, 270,
    {"3": "VBAT", "2": "VDD", "1": "GND"}, note="Verpolschutz: D = Zelle+, S = VDD, G = GND (CONCEPTS 2.10)")
add("C1", "Device:C", "100uF", FP_C1206, "C100U", 26, 24, 0, {"1": "VDD", "2": "GND"},
    note="Puffer E1, steifer Kopfbereich, Laengsachse parallel Biegelinie")
add("C2", "Device:C", "100uF", FP_C1206, "C100U", 30, 24, 0, {"1": "VDD", "2": "GND"}, note="Puffer E1")
add("C3", "Device:C", "100uF", FP_C1206, "C100U", 34, 24, 0, {"1": "VDD", "2": "GND"},
    note="Puffer E1; Prototyp bestueckt (D-013), Serie nach Messung 2 oder 4")
add("C4", "Device:C", "100uF", FP_C1206, "C100U", 38, 24, 0, {"1": "VDD", "2": "GND"},
    note="Puffer E1; Prototyp bestueckt (D-013), Serie nach Messung 2 oder 4")

# ---------------- SoC (Mitte)
add("U1", "fluidi:CC2340R52E0RGER", "CC2340R52E0RGER", "Package_DFN_QFN:VQFN-24-1EP_4x4mm_P0.5mm_EP2.45x2.45mm",
    "CC2340", 75, 30, 0, {
        "11": "VDD", "18": "VDD", "24": "VDD", "2": "VDDR", "20": "VDDR", "17": "DCDC_SW", "16": "VDDD",
        "13": "RSTN", "21": "X48P", "22": "X48N", "14": "X32P", "15": "X32N", "1": "RF_PIN",
        "19": "LED_R_UART_TX", "3": "CREF1_CTL", "4": "OSC_EN_N", "5": "SENS_PWR", "6": "LED_G",
        "7": "I2C_SDA", "8": "I2C_SCL", "9": "LED_B_UART_RX", "10": "BTN_BOOT_N", "12": "MEAS_CLK",
        "23": "GND", "25": "GND"})
# Entkopplung VDDS (je Pin 100 nF, HW-Guide SWRA834A S.5 Abb. 3-1) + 10 uF (DS S.18 Fussnote 3)
add("C5", "Device:C", "10uF", FP_C, "C10U", 54, 52, 0, {"1": "VDD", "2": "GND"},
    note="VDDS-Eingang 10 uF (DS S.18 Fussnote 3 Slew-Rate Knopfzelle)")
add("C6", "Device:C", "100nF", FP_C, "C100N", 57, 52, 0, {"1": "VDD", "2": "GND"}, note="an Pin 11 VDDS")
add("C7", "Device:C", "100nF", FP_C, "C100N", 60, 52, 0, {"1": "VDD", "2": "GND"}, note="an Pin 18 VDDS")
add("C8", "Device:C", "100nF", FP_C, "C100N", 63, 52, 0, {"1": "VDD", "2": "GND"}, note="an Pin 24 VDDS")
# DCDC / VDDR / VDDD
add("L1", "Device:L", "10uH", "fluidi:L_Sunlord_WPN201610H", "L10U", 67, 52, 0, {"1": "DCDC_SW", "2": "VDDR"},
    note="DCDC-Spule nahe Pin 17 (DS S.18 Tab. 7.4 Fussnote 2)")
add("C9", "Device:C", "10uF", FP_C, "C10U", 70, 52, 0, {"1": "VDDR", "2": "GND"}, note="VDDR 10 uF nahe Pin 17 / L1")
add("C10", "Device:C", "100nF", FP_C, "C100N", 73, 52, 0, {"1": "VDDR", "2": "GND"}, note="an Pin 2 VDDR")
add("C11", "Device:C", "100nF", FP_C, "C100N", 76, 52, 0, {"1": "VDDR", "2": "GND"}, note="an Pin 20 VDDR")
add("C12", "Device:C", "1uF", FP_C, "C1U", 79, 52, 0, {"1": "VDDD", "2": "GND"}, note="VDDD 1 uF (HW-Guide S.5)")
add("R1", "Device:R", "100k", FP_R, "R100K", 83, 52, 0, {"1": "VDD", "2": "RSTN"},
    note="RSTN-Pull-up, kein Pad (CONCEPTS 2.2)")
add("C13", "Device:C", "100nF", FP_C, "C100N", 86, 52, 0, {"1": "RSTN", "2": "GND"}, note="RSTN (HW-Guide S.5 C92)")
# Quarze
add("Y1", "Device:Crystal_GND24", "48MHz 8pF", "Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm", "XT48", 60, 62, 0,
    {"1": "X48P", "3": "X48N", "2": "GND", "4": "GND"},
    note="interne Lastkapazitaet (DS S.26 Fussnote 1), keine externen C")
add("Y2", "Device:Crystal", "32.768kHz 9pF", "Crystal:Crystal_SMD_3215-2Pin_3.2x1.5mm", "XT32", 74, 62, 0,
    {"1": "X32P", "2": "X32N"})
add("C14", "Device:C", "15pF", FP_C, "C15P", 70, 66, 0, {"1": "X32P", "2": "GND"},
    note="CL = C/2 + Cpar = 7.5 + 1.5 (ANNAHME) = 9 pF (HW-Guide S.11 Gl. 1)")
add("C15", "Device:C", "15pF", FP_C, "C15P", 78, 66, 0, {"1": "X32N", "2": "GND"}, note="wie C14")

# ---------------- HF (oben rechts): LC-Filter + DC-Block + Pi-Netz (HW-Guide S.5 Abb. 3-1)
add("C16", "Device:C", "1.5pF", FP_C, "C1P5", 100, 24, 0, {"1": "RF_PIN", "2": "GND"}, note="C33 Referenz")
add("L2", "Device:L", "2.7nH", FP_L0402, "L2N7", 106, 14, 90, {"1": "RF_PIN", "2": "RF_FILT"},
    note="L33 Referenz 2.8 nH; 2.7 nH Basis-Wert (OP-K9 Abstimmung)")
add("C17", "Device:C", "1.5pF", FP_C, "C1P5", 114, 24, 0, {"1": "RF_FILT", "2": "GND"}, note="C34 Referenz")
add("C18", "Device:C", "15pF", FP_C, "C15P", 120, 14, 90, {"1": "RF_FILT", "2": "RF_ANT_DC"}, note="DC-Block CA2")
add("C19", "Device:C", "DNM", FP_C, "DNM", 128, 24, 0, {"1": "RF_ANT_DC", "2": "GND"}, dnp=True,
    note="Pi-Netz Z60, Wert nach Antennenmessung")
add("R2", "Device:R", "0R", FP_R, "R0", 135, 14, 90, {"1": "RF_ANT_DC", "2": "ANT_FEED"}, note="Pi-Netz Z61")
add("C20", "Device:C", "DNM", FP_C, "DNM", 143, 24, 0, {"1": "ANT_FEED", "2": "GND"}, dnp=True,
    note="Pi-Netz Z62, Wert nach Antennenmessung")
add("AE1", "fluidi:ANT_IFA_AN043", "AN043_IFA", "RF_Antenna:Texas_SWRA117D_2.4GHz_Right", "PCB", 155, 24, 0,
    {"1": "ANT_FEED", "2": "GND"}, note="Leiterbahnantenne oben, Keepout nach AN043; Platzhalter-Footprint")

# ---------------- Messkette D3 (unten links/Mitte): Lastschalter, RC-Oszillator 17-36 MHz, Teiler /8
add("Q2", "fluidi:AO3401A", "AO3401A", "Package_TO_SOT_SMD:SOT-23", "AO3401", 40, 79, 270,
    {"2": "VDD", "3": "OSC_PWR", "1": "OSC_EN_N"},
    note="Lastschalter Messkette: S = VDD, D = OSC_PWR, G = DIO11 (low = an); Messkette ca. 10 mA > DIO12-Grenze")
add("R13", "Device:R", "100k", FP_R, "R100K", 48, 80, 0, {"1": "VDD", "2": "OSC_EN_N"},
    note="Gate-Pull-up Q2: haelt die Messkette im Reset/ROM-Bootloader aus (DIO11 = SPI-CS-Eingang, TRM S.464)")
add("U2", "74xGxx:74LVC1G14", "SN74LVC1G14DCKR", "Package_TO_SOT_SMD:SOT-353_SC-70-5", "LVC14", 28, 92, 0,
    {"2": "PROBE_SENSE", "4": "OSZ_OUT", "5": "OSC_PWR", "3": "GND"},
    note="RC-Schmitt-Oszillator 17-36 MHz (D3), VCC aus OSC_PWR (ratiometrisch zu VDD)")
add("R3", "Device:R", "1k", FP_R, "R1K", 24, 80, 90, {"2": "OSZ_OUT", "1": "PROBE_SENSE"},
    note="Rueckkopplung D3 1 kOhm; fuer Vergleich Variante A auf 10 kOhm (0402WGF1002TCE C25744) umloetbar")
add("C21", "Device:C", "100nF", FP_C, "C100N", 40, 96, 0, {"1": "OSC_PWR", "2": "GND"}, note="an U2 VCC")
add("C22", "Device:C", "22pF", FP_C, "C22P", 15, 96, 0, {"1": "PROBE_SENSE", "2": "CREF1_CTL"},
    note="Cref1 C0G, per DIO8 low zugeschaltet (Ratiometrie CONCEPTS 2.3)")
add("E1", "fluidi:SONDE_ELEKTRODEN", "Sonde_Innenlagen", "fluidi:SONDE_PLATZHALTER", "PCB", 10, 84, 0,
    {"1": "PROBE_SENSE", "2": "GND"}, note="Elektroden Innenlagen L2/L3 (REPORT Kap. 8); Gegenelektrode/Guard = GND")
add("TP5", "Connector:TestPoint", "PROBE_SENSE", "TestPoint:TestPoint_Pad_D1.0mm", "PCB", 6, 102, 0,
    {"1": "PROBE_SENSE"}, note="B-Seite Elektronikband: VNA-Messung Sonde (MESSKETTE_SALZ Kap. 6), nur messen")
add("U4", "74xGxx:74LVC1G80", "SN74LVC1G80DCKR", "Package_TO_SOT_SMD:SOT-353_SC-70-5", "LVC80", 58, 92, 0,
    {"1": "DIV2", "2": "OSZ_OUT", "4": "DIV2", "5": "OSC_PWR", "3": "GND"},
    note="Teiler /2 (D an Q invertiert, DS S.13 Tab. 7-1), fclock <= 160 MHz (S.6)")
add("U5", "74xGxx:74LVC1G80", "SN74LVC1G80DCKR", "Package_TO_SOT_SMD:SOT-353_SC-70-5", "LVC80", 74, 92, 0,
    {"1": "DIV4", "2": "DIV2", "4": "DIV4", "5": "OSC_PWR", "3": "GND"}, note="Teiler /4")
add("U6", "74xGxx:74LVC1G80", "SN74LVC1G80DCKR", "Package_TO_SOT_SMD:SOT-353_SC-70-5", "LVC80", 94, 92, 0,
    {"1": "MEAS_CLK", "2": "DIV4", "4": "MEAS_CLK", "5": "OSC_PWR", "3": "GND"}, note="Teiler /8 -> DIO24")
add("C25", "Device:C", "100nF", FP_C, "C100N", 46, 96, 0, {"1": "OSC_PWR", "2": "GND"},
    note="Abblock Teiler U4-U6 (nahe U4, hoechste Frequenz)")
add("TP4", "Connector:TestPoint", "MEAS_CLK", "TestPoint:TestPoint_Pad_D1.0mm", "PCB", 104, 98, 0, {"1": "MEAS_CLK"},
    note="B-Seite Elektronikband, f_osc/8 (nur messen)")

# ---------------- Temperatur (Mitte links): U3 + C24 im Sondenkragen (FLOORPLAN_OPTIONS Option f), R4/R5 im Band
add("U3", "fluidi:TMP1075NDRL", "TMP1075NDRLR", "Package_TO_SOT_SMD:SOT-563", "TMPN", 22, 48, 0,
    {"6": "I2C_SDA", "1": "I2C_SCL", "3": "NC", "4": "GND", "2": "GND", "5": "SENS_PWR"},
    note="im Sondenkragen (Option f, Freigabe S3-K2); Adresse 0x48 (A0 = GND, DS S.14 Tab. 7-3); ALERT offen")
add("C24", "Device:C", "100nF", FP_C, "C100N", 8, 46, 0, {"1": "SENS_PWR", "2": "GND"},
    note="an U3 V+ im Kragen (DS S.26 Kap. 8.3: typ. 0.01 uF, so nah wie moeglich)")
add("R4", "Device:R", "4.7k", FP_R, "R4K7", 36, 42, 0, {"1": "SENS_PWR", "2": "I2C_SDA"},
    note="I2C-Pull-up schaltbar, im Elektronikband")
add("R5", "Device:R", "4.7k", FP_R, "R4K7", 40, 42, 0, {"1": "SENS_PWR", "2": "I2C_SCL"},
    note="I2C-Pull-up schaltbar, im Elektronikband")

# ---------------- Bedienung (unten rechts)
add("D1", "Device:LED_ARGB", "RGB 1615", "fluidi:LED_RGB_TUOZHAN_1615", "LEDRGB", 124, 76, 0,
    {"1": "VDD", "2": "LED_R_K", "3": "LED_G_K", "4": "LED_B_K"}, note="gem. Anode an VDD (Phase-3-Review 1.3)")
add("R6", "Device:R", "470", FP_R, "R470", 112, 70, 90, {"2": "LED_R_K", "1": "LED_R_UART_TX"})
add("R7", "Device:R", "200", FP_R, "R200", 112, 76, 90, {"2": "LED_G_K", "1": "LED_G"})
add("R8", "Device:R", "100", FP_R, "R100", 112, 82, 90, {"2": "LED_B_K", "1": "LED_B_UART_RX"})
add("SW1", "Switch:SW_Push", "TS-1088", "Button_Switch_SMD:SW_SPST_TS-1088-xR020", "TS1088", 124, 86, 0,
    {"1": "BTN_BOOT_N", "2": "GND"},
    note="nach GND, interner Pull-up; beim Einschalten gedrueckt = ROM-Bootloader; Hoehe 2.0 mm (Zunge +0.5 mm)")

# ---------------- Programmierung / Testpunkte (rechts)
add("R9", "Device:R", "100k", FP_R, "R100K", 114, 46, 90, {"1": "LED_R_UART_TX", "2": "UART_TX_MID"},
    note="Barriere 2a TX (R2-A3: Elektronikraum, getrennt von R10)")
add("R10", "Device:R", "100k", FP_R, "R100K", 132, 46, 90, {"1": "UART_TX_MID", "2": "UART_TX_PAD"},
    note="Barriere 2b TX (R2-A3: eigene Loetstoppoeffnung, Abstand zu R9)")
add("TP1", "Connector:TestPoint", "UART_TX", "TestPoint:TestPoint_Pad_D1.5mm", "PCB", 142, 46, 0, {"1": "UART_TX_PAD"},
    note="Pogo-Pad TX im Zellfach ausserhalb der Zellflaeche (R2-W01 Nr. 2)")
add("R11", "Device:R", "100k", FP_R, "R100K", 114, 56, 90, {"1": "LED_B_UART_RX", "2": "UART_RX_MID"},
    note="Barriere 2a RX (R2-A3)")
add("R12", "Device:R", "100k", FP_R, "R100K", 132, 56, 90, {"1": "UART_RX_MID", "2": "UART_RX_PAD"},
    note="Barriere 2b RX (R2-A3)")
add("TP2", "Connector:TestPoint", "UART_RX", "TestPoint:TestPoint_Pad_D1.5mm", "PCB", 142, 56, 0, {"1": "UART_RX_PAD"},
    note="Pogo-Pad RX im Zellfach ausserhalb der Zellflaeche")
add("TP3", "Connector:TestPoint", "GND", "TestPoint:TestPoint_Pad_D1.0mm", "PCB", 152, 56, 0, {"1": "GND"},
    note="Messpunkt GND")

# Power-Flags (ERC): VDD/GND/SENS_PWR/OSC_PWR werden von passiven Bauteilen bzw. einem GPIO gespeist
FLAGS = [("VDD", 44, 16), ("GND", 44, 26), ("SENS_PWR", 44, 40), ("OSC_PWR", 52, 84)]
