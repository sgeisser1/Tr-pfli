#!/usr/bin/env python3
"""Troepfli - Energiebudget Sensor (Phase 2, Variantenvergleich REQ-ENE-01).

Aufruf:   .venv/bin/python scripts/energy_budget.py            (alle Tabellen, Markdown)
          .venv/bin/python scripts/energy_budget.py --params   (nur Parametertabelle)

Nur Standardbibliothek. Alle Zahlen stehen in PARAMS mit Quelle; Werte ohne Datenblatt sind
als ANNAHME markiert. Seitenangaben = PDF-Seite.

Quellen-Kuerzel (lokale Dateien, Register docs/datasheets/_staging/INDEX_energie.csv):
  [CC]   docs/datasheets/TI_CC2340R5_Datasheet_SWRS272F.pdf (Mai 2026)
  [N52]  Nordic nRF52832 PS v1.0          (nur Scratchpad .../scratchpad/energy2/soc/, nicht im Repo)
  [BG22] SiLabs EFR32BG22C112 DS Prelim. Rev 0.5 (nur Scratchpad, via LCSC C1864138)
  [CH]   docs/datasheets/WCH_CH592_Datasheet_V1.9.pdf (engl.; Werte gleich wie V1.8 chin.)
  [RC32] docs/datasheets/Renata_CR2032MFR_Datasheet_Rev07.pdf
  [RC45] docs/datasheets/Renata_CR2450N_Datasheet_Rev08.pdf
  [RC77] docs/datasheets/Renata_CR2477N_Datasheet_Rev08.pdf
  [MX45] docs/datasheets/Maxell_CR2450HR_Datasheet_table.pdf
  [RL..] docs/datasheets/Renata_ICP*_Datasheet_*.pdf (LiPo)
  [TPS]  docs/datasheets/TI_TPS7A02_Datasheet_RevC.pdf
  [B21]  docs/datasheets/TI_BQ21040_Datasheet_RevD.pdf
  [B29]  docs/datasheets/TI_BQ2970_Datasheet_RevI.pdf
  [DW]   docs/datasheets/PUOLOP_DW01A_Datasheet.pdf
  [GRM]  docs/datasheets/Murata_GRM31CR60J107ME39L_Datasheet.pdf
  [AO]   docs/datasheets/AOS_AO3401A_Datasheet_Rev3.1.pdf
  [SW]   docs/appnotes/TI_SWRA349_WhitePaper.pdf (Coin cells and peak current draw)
"""
import sys

DAY = 86400.0
YEAR_D = 365.0
MONTH_D = 30.4
mAh = 3.6  # Coulomb

# --------------------------------------------------------------------------------------------
# Parametertabelle: (Wert, Einheit, Quelle). "ANNAHME" im Quellentext = nicht aus Datenblatt.
# --------------------------------------------------------------------------------------------
PARAMS = {}


def P(key, value, unit, source):
    PARAMS[key] = (value, unit, source)
    return value


# ---- SoC-Parametersaetze (typ. Werte; pess = Werte ohne DCDC bzw. x1.5) --------------------
SOCS = {
    "CC2340R5": dict(
        sleep=P("CC.sleep", 0.74e-6, "A", "[CC] S.19 Tab. 7.9 Standby LFXT, DCDC, 25 C, typ (kein Max)"),
        sleep_ldo=P("CC.sleep_ldo", 1.15e-6, "A", "[CC] S.20 Tab. 7.9 Standby LFXT, GLDO, typ"),
        tx=P("CC.tx", 5.1e-3, "A", "[CC] S.20 Tab. 7.10 TX 0 dBm, DCDC"),
        tx_ldo=P("CC.tx_ldo", 9.0e-3, "A", "[CC] S.20 Tab. 7.10 TX 0 dBm, DCDC off"),
        rx=P("CC.rx", 5.3e-3, "A", "[CC] S.20 Tab. 7.10 RX 1 Mbps, DCDC"),
        rx_ldo=P("CC.rx_ldo", 9.0e-3, "A", "[CC] S.20 Tab. 7.10 RX, DCDC off"),
        cpu=P("CC.cpu", 2.6e-3, "A", "[CC] S.19 Tab. 7.9 CoreMark 48 MHz, DCDC"),
        cpu_ldo=P("CC.cpu_ldo", 4.1e-3, "A", "[CC] S.20 Tab. 7.9 CoreMark, GLDO"),
        vmin=P("CC.vmin", 1.71, "V", "[CC] S.18 Rec. Op. Cond. VDDS 1.71-3.8 V"),
        vmax=P("CC.vmax", 3.8, "V", "[CC] S.18"),
        price=P("CC.price", 1.59, "USD", "JLC C20416850 CC2340R52E0RGER, 1 Stk, Abruf 2026-11-06"),
    ),
    "nRF52832": dict(
        # PS v1.0 nennt System ON + RTC nur ohne RAM-Erhalt (1.9 uA); RAM-Erhalt-Zuschlag aus
        # Differenz ION_RAMON_EVENT - ION_RAMOFF_EVENT = 1.5 - 1.2 = 0.3 uA (Ableitung, ANNAHME).
        sleep=P("N52.sleep", 1.9e-6 + 0.3e-6, "A",
                "[N52] S.75 ION_RAMOFF_RTC 1.9 uA + RAM-Erhalt 0.3 uA (S.75 Differenz, ANNAHME-Ableitung)"),
        sleep_ldo=P("N52.sleep_ldo", 2.2e-6, "A", "wie oben (Ruhestrom unabh. von DCDC, ANNAHME)"),
        tx=P("N52.tx", 7.1e-3, "A", "[N52] S.74 IRADIO_TX0 0 dBm, DCDC, System"),
        tx_ldo=P("N52.tx_ldo", 11.6e-3, "A", "[N52] S.226 ITX,0dBM (LDO, Radio only)"),
        rx=P("N52.rx", 6.5e-3, "A", "[N52] S.74 IRADIO_RX0, DCDC, System"),
        rx_ldo=P("N52.rx_ldo", 11.7e-3, "A", "[N52] S.226 IRX,1M (LDO, Radio only)"),
        cpu=P("N52.cpu", 215 / 58 * 1e-3, "A", "[N52] S.19 CMFLASH 215 / CMFLASH/mA 58 (DCDC 3 V) = 3.7 mA"),
        cpu_ldo=P("N52.cpu_ldo", 215 / 58 * 1e-3 * 1.5, "A", "ANNAHME x1.5 fuer LDO-Betrieb (kein DS-Wert)"),
        vmin=P("N52.vmin", 1.7, "V", "[N52] S.17 VDD 1.7-3.6 V (independent of DCDC)"),
        vmax=P("N52.vmax", 3.6, "V", "[N52] S.17"),
        price=P("N52.price", 5.10, "USD", "JLC C77540 NRF52832-QFAA-R, 1 Stk, Abruf 2026-11-06"),
    ),
    "EFR32BG22": dict(
        sleep=P("BG.sleep", 1.40e-6, "A", "[BG22] S.23 Tab. 4.5 EM2 full RAM, RTC LFXO, typ"),
        sleep_ldo=P("BG.sleep_ldo", 1.40e-6, "A", "wie oben (ANNAHME: kein Wert ohne DC-DC im DS)"),
        tx=P("BG.tx", 4.1e-3, "A", "[BG22] S.29 ITX 0 dBm, System, DC-DC 3 V"),
        tx_ldo=P("BG.tx_ldo", 4.1e-3 * 1.5, "A", "ANNAHME x1.5 (kein Wert ohne DC-DC)"),
        rx=P("BG.rx", 3.6e-3, "A", "[BG22] S.29 IRX_ACTIVE 1 Mbit/s, System"),
        rx_ldo=P("BG.rx_ldo", 3.6e-3 * 1.5, "A", "ANNAHME x1.5"),
        cpu=P("BG.cpu", 38e-6 * 38.4, "A", "[BG22] S.23 Tab. 4.5 EM0 CoreMark 38 uA/MHz x 38.4 MHz"),
        cpu_ldo=P("BG.cpu_ldo", 38e-6 * 38.4 * 1.5, "A", "ANNAHME x1.5"),
        vmin=P("BG.vmin", 1.71, "V", "[BG22] S.18 VREGVDD 1.71-3.8 V (DC-DC in Regelung erst ab 2.2 V)"),
        vmax=P("BG.vmax", 3.8, "V", "[BG22] S.18"),
        price=P("BG.price", 1.94, "USD", "JLC C1864138 EFR32BG22C112F352GM32-CR, 1 Stk, Abruf 2026-11-06"),
    ),
    "CH592F": dict(
        sleep=P("CH.sleep", 2.2e-6, "A",
                "[CH] S.43 Tab. 5-3 Sleep, RAM24K + RTC(LSE) + Kern erhalten, 2.2 uA (Stichprobe Raumtemp.)"),
        sleep_ldo=P("CH.sleep_ldo", 2.2e-6, "A", "wie oben"),
        tx=P("CH.tx", 3.5e-3, "A", "[CH] S.154 BLE TX 0 dBm, DC-DC"),
        tx_ldo=P("CH.tx_ldo", 7.5e-3, "A", "[CH] S.154 BLE TX 0 dBm, Direktversorgung"),
        rx=P("CH.rx", 3.4e-3, "A", "[CH] S.154 BLE RX, DC-DC"),
        rx_ldo=P("CH.rx_ldo", 7.1e-3, "A", "[CH] S.154 BLE RX, Direktversorgung"),
        cpu=P("CH.cpu", 2.6e-3, "A", "[CH] S.152 IDDC8 Flash 2.6 mA (DC-DC, 8 MHz)"),
        cpu_ldo=P("CH.cpu_ldo", 3.2e-3, "A", "[CH] S.152 ICC8 Flash 3.2 mA (direkt)"),
        vmin=P("CH.vmin", 1.75, "V", "[CH] S.152 VDD33 CH592X/F/D 1.75-3.6 V"),
        vmax=P("CH.vmax", 3.6, "V", "[CH] S.152"),
        price=P("CH.price", 0.83, "USD", "JLC C39831287 CH592F, 1 Stk, Abruf 2026-11-06"),
    ),
}

# ---- Temperatur (Sonnenprofil RB-03) ----------------------------------------------------------
SUN_H = P("sun.h", 4.0, "h/Tag", "RB-03 Sonnenprofil (ANNAHME des Auftraggebers)")
SLEEP_T50 = P("sleep.t50", 1.35, "-",
              "[CC] S.35 Fig. 7-7 abgelesen: Standby ~0.75 uA @25 C, ~1.0 uA @50 C -> Faktor 1.35; "
              "fuer alle SoCs uebernommen (ANNAHME)")
SLEEP_TEMP_FACTOR = ((24 - SUN_H) * 1.0 + SUN_H * SLEEP_T50) / 24
PESS_SLEEP = P("pess.sleep", 1.5, "-", "REQ-ENE-08: Typwert x 1.5 (kein Max-Wert in den SoC-Datenblaettern)")
PESS_TOTAL = P("pess.total", 1.2, "-", "REQ-ENE-08: Zuschlag +20 % auf Gesamtverbrauch")
PESS_EVENT = P("pess.event", 1.5, "-", "ANNAHME: Zuschlag auf Ereignisladung (Stack-Overhead, Streuung), wie Phase 1")

# ---- BLE-Ereignis (Erreichbarkeit per verbindbarem Advertising, Phase 1 Var. a) -------------
T_ADV_TX = P("ble.t_adv", 47 * 8e-6, "s", "BLE 1 Mbit/s, 47 B ADV_IND voll (Rechnung)")
T_RX_WIN = P("ble.t_rx", 250e-6, "s", "ANNAHME: T_IFS 150 us + Lauschfenster je Kanal")
T_CH = P("ble.t_ch", 150e-6, "s", "ANNAHME: Kanalwechsel je Kanal (bei RX-Strom gerechnet)")
T_CPU_EV = P("ble.t_cpu", 1.5e-3, "s", "ANNAHME: CPU je Funkereignis")
I_HFXO, T_HFXO = 0.4e-3, 0.36e-3
P("ble.hfxo", I_HFXO * T_HFXO, "C", "[N52] S.106 ISTART_HFXO 0.4 mA x 0.36 ms, fuer alle SoCs (ANNAHME)")
T_SETUP = P("ble.t_setup", 5.0, "s", "ANNAHME: Verbindungsaufbau + Messung + Anzeige PWA")
P_MISS = P("ble.p_miss", 0.10, "-", "ANNAHME: Gateway verpasst ein Erreichbarkeitsfenster mit 10 %")

# ---- Messung / Uebertragung / LED / OTA --------------------------------------------------------
N_AUTO = P("prof.n_auto", 6, "1/Tag", "REQ-ENE-04 Standardprofil")
N_MAN = P("prof.n_man", 2, "1/Tag", "REQ-ENE-04 Standardprofil")
Q_MEAS = P("prof.q_meas", 10e-3 * 3e-3, "C", "ANNAHME: Messung inkl. Mittelung 10 ms bei 3 mA")
T_CONN = P("prof.t_conn", 50e-3, "s", "ANNAHME: Verbindung + Daten + Abbau, Funk/CPU aktiv")
LED_I = P("led.i", 2e-3, "A", "ANNAHME (REQ-UI-03, FE-11)")
LED_STD = P("led.std", 6 * 20e-3, "s/Tag", "ANNAHME Standardmuster: 6 Blinks x 20 ms pro Tag")
LED_WATER = P("led.water", 12 * 60 * 5e-3, "s/Tag",
              "REQ-UI-07 Giessen-noetig 1x/min, 12 h/Tag, 5 ms (ANNAHME; nur pessimistisch dauernd aktiv)")
OTA_IMG = P("ota.img", 200e3, "B", "ANNAHME Image-Groesse; 1 Update/Jahr (REQ-ENE-04)")
FLASH_Q_PER_2K = P("ota.flash", 8.3e-3 * 1.7e-3 + 2.2e-3 * 1.2e-3, "C",
                   "[CC] S.21 Tab. 7.11 Schreiben+Loeschen 2 kB (fuer alle SoCs ANNAHME)")

# ---- Weitere Ruhestroeme (Bauteile ausser SoC) -------------------------------------------------
I_OTHER_REAL = P("oth.real", 0.2e-6, "A", "ANNAHME: Sensor-Frontend aus, Teiler geschaltet, Taster offen")
I_OTHER_PESS = P("oth.pess", 0.5e-6, "A", "ANNAHME pess. (bis Schaltplan: Pull-ups, ESD-Dioden, Temp.-Sensor)")
I_PFET_PESS = P("cc.pfet", 0.1e-6, "A", "[AO] S.2 IGSS max 100 nA @ +-12 V (Gate an GND, Verpolschutz)")
# MLCC-Pufferkondensator-Leckstrom
GRM_RC = P("mlcc.rc", 50.0, "Ohm*F", "[GRM] S.2 Pos. 5 Insulation Resistance > 50 Ohm*F (Raumtemp., Nennspannung)")
C_BUF_NOM = P("mlcc.c", 100e-6, "F", "Kandidat GRM31CR60J107ME39L / CL31A107MQHNNNE (Basic C15008), 100 uF 6.3 V")
I_MLCC_REAL = P("mlcc.real", 0.05e-6, "A", "ANNAHME (typisch weit unter Grenzwert; PROTOTYP-PRUEFUNG)")
I_MLCC_PESS = P("mlcc.pess", 0.5e-6, "A", "ANNAHME pessimistisch fuer Fall A; Fall B = Datenblattgrenze")
DCBIAS = P("mlcc.dcbias", 0.5, "-", "ANNAHME: Restkapazitaet 50 % bei 3 V (6.3-V-X5R-1206); Kurve fehlt lokal")

# ---- Pulslast / Puffer (REQ-ENE-06) ------------------------------------------------------------
R_CELL_EOL = P("cc.r_eol", 100.0, "Ohm", "REQ-ENE-06 Nachweisfall Zellinnenwiderstand 100 Ohm")
DV_MAX = P("cc.dv", 0.2, "V", "REQ-ENE-06 Einbruch <= 0.2 V")

# ---- Energiequellen ----------------------------------------------------------------------------
# (Nennkap. mAh, Selbstentl. real/pess pro Jahr, nutzbar real/pess, Zusatz-Ruhestrom real/pess, Typ)
CELLS = {
    "CR2032 (Renata)": dict(
        cap=P("cell.cr2032", 225, "mAh", "[RC32] S.1 Rated Capacity 225 mAh (0.4 mA... 2.0 V)"),
        sd=(P("cell.sd_cc", 0.01, "1/a", "[RC32]/[RC45]/[RC77] S.1 Self Discharge < 1 %/a @23 C"),
            P("cell.sd_cc_p", 0.02, "1/a", "ANNAHME pess. (Sonnenprofil 50 C)")),
        util=(P("cell.util_real", 0.90, "-", "ANNAHME realistisch mit Puffer-C"),
              P("cell.util_pess", 0.75, "-", "REQ-ENE-08: <= 75 % mit Puffer-C")),
        extra=(I_PFET_PESS * 0.2, I_PFET_PESS), kind="CC"),
    "CR2450N (Renata)": dict(
        cap=P("cell.cr2450", 540, "mAh", "[RC45] S.1 Rated Capacity 540 mAh"),
        sd=(0.01, 0.02), util=(0.90, 0.75), extra=(I_PFET_PESS * 0.2, I_PFET_PESS), kind="CC"),
    "CR2477N (Renata)": dict(
        cap=P("cell.cr2477", 950, "mAh", "[RC77] S.1 Rated Capacity 950 mAh"),
        sd=(0.01, 0.02), util=(0.90, 0.75), extra=(I_PFET_PESS * 0.2, I_PFET_PESS), kind="CC"),
    "LiPo ICP401230UPR 125 mAh": dict(
        cap=P("cell.li130", 125, "mAh", "[RL4012] S.1 Minimum Capacity 125 mAh (0.2C, 3.0 V)"),
        sd=(P("cell.sd_li", 0.02 * 12, "1/a", "ANNAHME 2 %/Monat (kein DS-Wert)"),
            P("cell.sd_li_p", 0.03 * 12, "1/a", "ANNAHME 3 %/Monat pess.")),
        util=(P("cell.li_util", 0.90, "-", "ANNAHME realistisch bis 3.0 V"),
              P("cell.li_util_p", 0.80, "-", "ANNAHME pess. (Abschaltung > 3.0 V, Alterung)")),
        extra=None, kind="LI"),
    "LiPo ICP501022UPM 75 mAh": dict(
        cap=P("cell.li80", 75, "mAh", "[RL5010] S.1 Minimum Capacity 75 mAh"),
        sd=(0.24, 0.36), util=(0.90, 0.80), extra=None, kind="LI"),
}

# LiPo-Versorgungspfad (Ruhestroeme ohne SoC)
I_LDO = (P("li.ldo", 25e-9, "A", "[TPS] S.6 IGND typ 25 nA (25 C)"),
         P("li.ldo_max", 60e-9, "A", "[TPS] S.6 IGND max 60 nA (-40..85 C)"))
I_CHG = (P("li.chg", 0.2e-6, "A", "ANNAHME typ (DS nennt nur Max)"),
         P("li.chg_max", 1.0e-6, "A", "[B21] S.5 IOUT(PDWN) max 1 uA, VIN = 0"))
I_PROT = (P("li.prot", 4.0e-6, "A", "[B29] S.5 INORMAL typ 4 uA (BQ2970, BAT 3.8 V)"),
          P("li.prot_max", 5.5e-6, "A", "[B29] S.5 INORMAL max 5.5 uA"))
I_PCM_CELL = (P("li.pcm", 1.0e-6, "A", "ANNAHME: zelleninterne Schutzschaltung (Renata: kein Wert)"),
              P("li.pcm_p", 3.0e-6, "A", "ANNAHME pess."))


# --------------------------------------------------------------------------------------------
def reach_interval(deadline_s):
    """Erreichbarkeitsintervall, damit 99 % der Anfragen innert Frist beantwortet werden."""
    k = 1
    while P_MISS ** k > 0.01 + 1e-12:  # Gleitkomma-Toleranz
        k += 1
    return (deadline_s - T_SETUP) / k


def soc_currents(s, pess):
    if pess:
        return s["tx_ldo"], s["rx_ldo"], s["cpu_ldo"]
    return s["tx"], s["rx"], s["cpu"]


def adv_event_charge(s, pess):
    itx, irx, icpu = soc_currents(s, pess)
    q = 3 * (T_ADV_TX * itx + (T_RX_WIN + T_CH) * irx) + T_CPU_EV * icpu + I_HFXO * T_HFXO
    return q * (PESS_EVENT if pess else 1.0)


def conn_charge(s, pess):
    itx, irx, icpu = soc_currents(s, pess)
    return T_CONN * (0.5 * (itx + irx) + 0.3 * icpu) * (PESS_EVENT if pess else 1.0)


def ota_charge(s, pess):
    itx, irx, _ = soc_currents(s, pess)
    pkt = 244
    n = OTA_IMG / pkt
    q = n * ((pkt + 14) * 8e-6 * irx + 0.2e-3 * itx) + OTA_IMG / 2048 * FLASH_Q_PER_2K
    q += 120.0 * 0.5 * 1.5e-3  # ANNAHME: 2 min, CPU halbe Zeit idle 1.5 mA
    return q * 2.0  # ANNAHME Faktor 2 (Wiederholungen, Verifikation)


def daily(s, reaction_min, cell, case):
    """case: 'real', 'pessA' (REQ-ENE-08, MLCC-Leck ANNAHME), 'pessB' (MLCC-Leck = DS-Grenze)."""
    pess = case != "real"
    t_reach = reach_interval(reaction_min * 60.0)
    i_sleep = s["sleep_ldo" if pess else "sleep"]
    if pess:
        i_sleep *= PESS_SLEEP * SLEEP_TEMP_FACTOR
    parts = {"sleep_soc": i_sleep * DAY}
    if cell["kind"] == "CC":
        if case == "real":
            i_mlcc = I_MLCC_REAL
        elif case == "pessA":
            i_mlcc = I_MLCC_PESS
        else:
            i_mlcc = 3.0 / (GRM_RC / C_BUF_NOM)
        parts["sleep_board"] = (I_OTHER_PESS if pess else I_OTHER_REAL) * DAY
        parts["mlcc"] = i_mlcc * DAY
        parts["vpol"] = cell["extra"][1 if pess else 0] * DAY
    else:
        k = 1 if pess else 0
        parts["sleep_board"] = (I_OTHER_PESS if pess else I_OTHER_REAL) * DAY
        parts["mlcc"] = (I_MLCC_PESS if pess else I_MLCC_REAL) * DAY * 0.2  # ANNAHME 10-22 uF genuegen
        parts["li_path"] = (I_LDO[k] + I_CHG[k] + I_PROT[k] + I_PCM_CELL[k]) * DAY
    parts["reach"] = DAY / t_reach * adv_event_charge(s, pess)
    parts["meas"] = (N_AUTO + N_MAN) * (Q_MEAS + conn_charge(s, pess))
    parts["led"] = LED_I * (LED_STD + (LED_WATER if pess else 0.0))
    parts["ota"] = ota_charge(s, pess) / YEAR_D
    tot = sum(parts.values()) * (PESS_TOTAL if pess else 1.0)
    return tot, parts


def lifetime_months(cell, q_day, pess):
    k = 1 if pess else 0
    cap = cell["cap"]
    usable = cap * cell["util"][k] * mAh
    sd_day = cap * cell["sd"][k] * mAh / YEAR_D
    return usable / (q_day + sd_day) / MONTH_D


def buffer_cap(s, pess=True):
    """Benoetigte effektive Kapazitaet fuer ein Advertising-Ereignis bei R=100 Ohm, dV=0.2 V.
    Die Zelle liefert waehrend des Ereignisses hoechstens dV/R; den Rest liefert der Kondensator."""
    itx, irx, icpu = soc_currents(s, pess)
    q = adv_event_charge(s, pess)
    t_ev = 3 * (T_ADV_TX + T_RX_WIN + T_CH) + T_CPU_EV + T_HFXO
    q_cell = DV_MAX / R_CELL_EOL * t_ev
    c_eff = max(q - q_cell, 0) / DV_MAX
    i_peak = max(itx, irx) + 0.0
    return c_eff, i_peak, q, t_ev


def fmt_m(x):
    return ">120" if x > 120 else f"{x:.1f}"


def print_params():
    print("| Schluessel | Wert | Einheit | Quelle |")
    print("|---|---|---|---|")
    for k, (v, u, src) in PARAMS.items():
        vs = f"{v:.4g}" if isinstance(v, float) else str(v)
        print(f"| {k} | {vs} | {u} | {src} |")


def main():
    if "--params" in sys.argv:
        print_params()
        return
    print("# Troepfli Energiebudget - Ausgabe scripts/energy_budget.py\n")
    print(f"Sonnenprofil: Ruhestrom-Temperaturfaktor (Tagesmittel) = {SLEEP_TEMP_FACTOR:.3f}")
    for m in (1, 2, 5):
        print(f"Reaktionszeit {m} min -> Erreichbarkeitsintervall {reach_interval(m*60):.1f} s")

    print("\n## 1 Ereignisladungen je SoC (uC)\n")
    print("| SoC | Adv-Ereignis real | Adv-Ereignis pess | Verbindung real | Verbindung pess | OTA pess [mAh] |")
    print("|---|---|---|---|---|---|")
    for n, s in SOCS.items():
        print(f"| {n} | {adv_event_charge(s, False)*1e6:.1f} | {adv_event_charge(s, True)*1e6:.1f} | "
              f"{conn_charge(s, False)*1e6:.0f} | {conn_charge(s, True)*1e6:.0f} | {ota_charge(s, True)/mAh:.3f} |")

    print("\n## 2 Mittelstrom (uA) im Standardprofil, Knopfzelle (CR2032)\n")
    print("REQ-ENE-09: <= 8 uA mit Werkseinstellung; Schlaf <= 3 uA.\n")
    print("| SoC | Reaktionszeit | real | pess A | pess B (MLCC-Leck = DS-Grenze) | Schlaf pess (SoC+Board) |")
    print("|---|---|---|---|---|---|")
    cr = CELLS["CR2032 (Renata)"]
    for n, s in SOCS.items():
        for m in (1, 2, 5):
            r = [daily(s, m, cr, c)[0] / DAY * 1e6 for c in ("real", "pessA", "pessB")]
            _, pa = daily(s, m, cr, "pessA")
            sl = (pa["sleep_soc"] + pa["sleep_board"] + pa["mlcc"] + pa["vpol"]) / DAY * 1e6
            print(f"| {n} | {m} min | {r[0]:.2f} | {r[1]:.2f} | {r[2]:.2f} | {sl:.2f} |")

    print("\n## 3 Laufzeit in Monaten (realistisch / pessimistisch A), Standardprofil\n")
    print("REQ-ENE-02 [CC] >= 12 Monate pess.; REQ-ENE-03 [LI] >= 3 Monate pro Ladung.\n")
    hdr = "| SoC | Reakt. | " + " | ".join(CELLS) + " |"
    print(hdr)
    print("|" + "---|" * (2 + len(CELLS)))
    for n, s in SOCS.items():
        for m in (1, 2, 5):
            row = f"| {n} | {m} min |"
            for cn, c in CELLS.items():
                qr, _ = daily(s, m, c, "real")
                qp, _ = daily(s, m, c, "pessA")
                row += f" {fmt_m(lifetime_months(c, qr, False))} / **{fmt_m(lifetime_months(c, qp, True))}** |"
            print(row)

    print("\n## 4 Laufzeit pessimistisch B (MLCC 100 uF mit Datenblatt-Leckgrenze, nur Knopfzellen)\n")
    print(f"MLCC-Leckstrom-Grenze bei 3.0 V: {3.0/(GRM_RC/C_BUF_NOM)*1e6:.1f} uA ([GRM] S.2, 50 Ohm*F / 100 uF)\n")
    ccells = {k: v for k, v in CELLS.items() if v["kind"] == "CC"}
    print("| SoC | Reakt. | " + " | ".join(ccells) + " |")
    print("|" + "---|" * (2 + len(ccells)))
    for n, s in SOCS.items():
        for m in (1, 5):
            row = f"| {n} | {m} min |"
            for cn, c in ccells.items():
                qp, _ = daily(s, m, c, "pessB")
                row += f" {fmt_m(lifetime_months(c, qp, True))} |"
            print(row)

    print("\n## 5 Budgetanteile pess. A, CR2032, 1 min (Anteil am Verbrauch vor Zuschlag)\n")
    print("| SoC | Schlaf SoC | Board | MLCC | Verpol | Erreichb. | Messung | LED | OTA | Summe mC/Tag |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for n, s in SOCS.items():
        tot, p = daily(s, 1, cr, "pessA")
        base = tot / PESS_TOTAL
        f = lambda k: f"{p.get(k, 0)/base*100:.0f} %"
        print(f"| {n} | {f('sleep_soc')} | {f('sleep_board')} | {f('mlcc')} | {f('vpol')} | {f('reach')} | "
              f"{f('meas')} | {f('led')} | {f('ota')} | {tot*1e3:.0f} |")

    print("\n## 6 Pufferkondensator (REQ-ENE-06: dV <= 0.2 V bei 100 Ohm), pess. Ereignis\n")
    print("| SoC | Fall | Spitzenstrom Funk [mA] | Einbruch ohne C @100 Ohm [V] | Ereignisladung [uC] | "
          "Dauer [ms] | C_eff noetig [uF] | C_nenn bei DC-Bias-ANNAHME [uF] | DS-Leckgrenze C_nenn @3 V [uA] |")
    print("|---|---|---|---|---|---|---|---|---|")
    for n, s in SOCS.items():
        for pess in (False, True):
            c_eff, ip, q, t = buffer_cap(s, pess)
            c_nom = c_eff / DCBIAS
            print(f"| {n} | {'pess' if pess else 'real'} | {ip*1e3:.1f} | {ip*R_CELL_EOL:.2f} | {q*1e6:.1f} | "
                  f"{t*1e3:.2f} | {c_eff*1e6:.0f} | {c_nom*1e6:.0f} | {3.0/(GRM_RC/c_nom)*1e6:.1f} |")

    print("\n## 7 LiPo-Pfad: Ruhestrom Lade-/Schutzschaltung (REQ-ENE-09 [LI] <= 5 uA)\n")
    print(f"typ: LDO {I_LDO[0]*1e9:.0f} nA + Lader {I_CHG[0]*1e6:.1f} uA + Schutz-IC {I_PROT[0]*1e6:.1f} uA "
          f"= {(I_LDO[0]+I_CHG[0]+I_PROT[0])*1e6:.2f} uA (ohne zelleninterne PCM)")
    print(f"max: LDO {I_LDO[1]*1e9:.0f} nA + Lader {I_CHG[1]*1e6:.1f} uA + Schutz-IC {I_PROT[1]*1e6:.1f} uA "
          f"= {(I_LDO[1]+I_CHG[1]+I_PROT[1])*1e6:.2f} uA (ohne zelleninterne PCM)")

    print("\n## 8 Grenz-Mittelstrom fuer 12 Monate (pess. Zelle)\n")
    for cn, c in ccells.items():
        i_lim = c["cap"] * (c["util"][1] - c["sd"][1]) * mAh / (YEAR_D * DAY)
        print(f"- {cn}: {i_lim*1e6:.1f} uA")


if __name__ == "__main__":
    main()
