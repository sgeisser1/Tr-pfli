#!/usr/bin/env python3
"""fluidi - Energiebudget Sensor (Phase 2, Variantenvergleich REQ-ENE-01).

Aufruf:   .venv/bin/python scripts/energy_budget.py            (alle Tabellen, Markdown)
          .venv/bin/python scripts/energy_budget.py --params   (nur Parametertabelle)
          .venv/bin/python scripts/energy_budget.py --revb --out hardware/sensor/out/ENERGIE_REV_B.md
                                                               (Rev B: bauteilgenaues Budget, Phase 4 Welle 3)

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


# ============================================================================================
# Rev B: Bauteil-genaues Budget fuer das fertige Layout (hardware/sensor, Phase 4, Welle 3)
# Aufruf: .venv/bin/python scripts/energy_budget.py --revb [--out hardware/sensor/out/ENERGIE_REV_B.md]
# Die Phase-2-Tabellen oben bleiben unveraendert (scripts/concept_energy.py baut darauf auf).
# Zusaetzliche Quellen-Kuerzel (lokal):
#   [TMP]  docs/datasheets/TI_TMP1075_Datasheet_SBOS854F.pdf
#   [G14]  docs/datasheets/TI_SN74LVC1G14_Datasheet_SCES218AA.pdf
#   [G80]  docs/datasheets/TI_SN74LVC1G80_Datasheet_SCES221T.pdf
#   [SAM]  docs/datasheets/Samsung_CL31A107MQHNNNE_Catalog_2015-11.pdf (C1-C4, LCSC C15008)
#   [S10]  docs/datasheets/Samsung_CL05A106MQ5NUNC_Datasheet_LCSC-2022-08.pdf (C5, C9, LCSC C15525)
#   [LED]  docs/datasheets/TUOZHAN_P4-1615G2B2R4TS2-06T-001-24_Datasheet_A0.pdf (D1)
#   [PAN]  docs/datasheets/Panasonic_CR2032_Datasheet_2026-02.pdf (Zelle laut BOM-Extra, D-006)
#   [NET]  hardware/sensor/out/fluidi_sensor.net (Rev B), [PIN] docs/interfaces/PINMAP_SENSOR.md Rev B
#   [FW]   firmware/sensor (config/fluidi_board.h, core/fl_settings.c, core/fl_app.c, platform/cc23/fl_hw.c)
# ============================================================================================
VDD_NOM = P("rb.vdd", 3.0, "V", "Nennspannung CR2032 [PAN] S.1 (Rechenwert fuer Leck-/Laststroeme)")

# ---- Ruhestrom (Schlaf, FW-8) je Bauteil: (real, pess A, pess DS) ----------------------------------------
# pess A = REQ-ENE-08 mit ANNAHME fuer Teile ohne Typwert; pess DS = jedes Teil an seiner Datenblattgrenze
# (REQ-ENE-08 "oder Maximalwert"; Nachweisfall REQ-ENE-02).
CC_SLEEP_PESS = SOCS["CC2340R5"]["sleep_ldo"] * PESS_SLEEP * SLEEP_TEMP_FACTOR
RB_SLEEP = {
    "U1 CC2340R52 Standby (LFXT, RAM, RTC)": (
        SOCS["CC2340R5"]["sleep"], CC_SLEEP_PESS, CC_SLEEP_PESS,
        "[CC] S.19 Tab. 7.9 0.74 uA (DCDC) real; pess. GLDO 1.15 uA (S.20) x1.5 x Sonnenprofil "
        f"{SLEEP_TEMP_FACTOR:.3f} (S.35 Fig. 7-7); DS nennt keinen Max-Wert"),
    "Q1 AO3401A Verpolschutz (leitend, VGS = -VDD)": (
        P("rb.q1_real", 0.02e-6, "A", "ANNAHME 20 % der IGSS-Grenze bei |VGS| 3 V statt 12 V"),
        I_PFET_PESS, I_PFET_PESS, "[AO] S.2 IGSS <= 100 nA @ VGS +-12 V"),
    "Q2 AO3401A Messkette aus (VGS = 0, VDS = -VDD)": (
        P("rb.q2_real", 0.01e-6, "A", "ANNAHME IDSS bei VDS -3 V (DS nur bei -30 V)"),
        P("rb.q2_pa", 0.1e-6, "A", "ANNAHME 10 % der DS-Grenze (VDS -3 V statt -30 V)"),
        P("rb.q2_ds", ((24 - SUN_H) * 1e-6 + SUN_H * 5e-6) / 24, "A",
          "[AO] S.2 IDSS <= 1 uA (TJ 25 C) / 5 uA (TJ 55 C) @ VDS -30 V, Sonnenprofil 4 h/Tag bei 55 C"),
        "[AO] S.2; Leckstrom fliesst ueber OSC_PWR in U2/U4-U6 (ICC), zaehlt nur einmal"),
    "C1-C4 4 x 100 uF X5R 6.3 V (Puffer, D-013)": (
        P("rb.mlcc_real", 4 * 0.05e-6, "A", "ANNAHME 0.05 uA je 100 uF (wie oben mlcc.real), PROTOTYP-PRUEFUNG"),
        P("rb.mlcc_pa", 0.5e-6, "A", "ANNAHME pess. A gesamt (wie concept_energy.py MLCC_PESSA)"),
        P("rb.mlcc_ds", 4 * 3.0 / (100.0 / 100e-6), "A",
          "[SAM] S.53 IR >= 100 MOhm*uF (markierte Hochkapazitaetstypen) -> 1 MOhm je 100 uF -> 3 uA @3 V, x4"),
        "[SAM] S.53 Insulation Resistance; Messung bei Nennspannung 6.3 V, bei 3 V real deutlich kleiner"),
    "C5 10 uF (VDD) + C9 10 uF (VDDR)": (
        P("rb.c10_real", 0.01e-6, "A", "ANNAHME"),
        P("rb.c10_pa", 0.05e-6, "A", "ANNAHME"),
        P("rb.c10_ds", 3.0 / 5e6 + 1.8 / 5e6, "A",
          "[S10] S.2 IR >= 50 MOhm*uF -> 5 MOhm je 10 uF; C5 @3.0 V + C9 @VDDR <= 1.8 V (ANNAHME VDDR)"),
        "[S10] S.2; 100 nF/1 uF-Typen (C6-C8, C10-C13, C21, C24, C25) < 1 nA je Stueck (500 MOhm*uF), vernachlaessigt"),
    "U2 SN74LVC1G14 + U4-U6 SN74LVC1G80 (OSC_PWR = 0)": (
        0.0, 0.0, 0.0,
        "unversorgt (Q2 aus); Eingang U2 an PROBE_SENSE ohne Quelle (DIO8 hochohmig), Ausgang U6 an DIO24 Puffer aus "
        "-> keine Spannung an Ioff-Pins ([G14] S.7, [G80] S.6 Ioff <= 10 uA nur bei angelegter Spannung)"),
    "U3 TMP1075N + R4/R5 4.7k + C24 (SENS_PWR low)": (
        0.0, 0.0, 0.0,
        "unversorgt: DIO12 low, DIO16/17 Ausgang low (FW-1/FW-8) -> 0 V an R4/R5 und U3; "
        "ISD 0.15/0.35 uA [TMP] S.7 Tab. 6.6 entfaellt"),
    "R13 100k (Gate Q2), R1 100k (RSTN), D1 RGB, SW1": (
        0.0, 0.0, 0.0,
        "beide Enden auf VDD: DIO11 high, RSTN high, LED-Kathoden high (FW-8); Taster offen, Pull-up stromlos"),
    "R9-R12 UART-Barriere zu TP1/TP2 (Zellfach)": (
        P("rb.uart_real", 0.0, "A", "Pads offen"),
        P("rb.uart_pa", 2 * VDD_NOM / 100e6, "A", "ANNAHME Oberflaechenisolation TP1/TP2-TP3 >= 100 MOhm"),
        P("rb.uart_ds", 2 * VDD_NOM / 100e6, "A", "wie pess. A (kein DS-Wert)"),
        "Fehlerfall Feuchte im Zellfach: <= 3 V / 200 kOhm = 15 uA je Pad (nicht im Budget, Sicherheit/Dichtung)"),
    "GPIO-Leck U1, Leiterplatte, Flussmittel": (
        P("rb.board_real", 0.05e-6, "A", "ANNAHME (concept_energy.py BOARD)"),
        P("rb.board_pa", 0.2e-6, "A", "ANNAHME (concept_energy.py BOARD)"),
        0.2e-6, "kein DS-Wert fuer Pad-Leckstrom in [CC] Tab. 7.21.4.1 (S.31-32) -> ANNAHME"),
}

# ---- Messung Rev B (FW-1, FW-2; fl_hw.c fl_port_measure) ----------------------------------------------
CPD_G14 = P("rb.cpd14", 22e-12, "F", "[G14] S.8 Tab. 5.8 Cpd 22 pF @3.3 V, f 10 MHz")
CPD_G80 = P("rb.cpd80", 25e-12, "F", "[G80] S.8 Tab. 5.11 Cpd 25 pF @3.3 V, f 10 MHz")
F_OSC = (P("rb.fosc_real", 24.2e6, "Hz", "simulation/spice/README.md (b): f_osc typ trocken, R3 1 kOhm"),
         P("rb.fosc_pess", 36.1e6, "Hz", "MESSKETTE_SALZ Kap. 5 D3: Luft 36.1 MHz (= 8 x 4.51 MHz, schnelle Ecke)"))
C_NODE = P("rb.c_node", 5e-12, "F", "ANNAHME Last je Teilerknoten (CIN ~3-5 pF + Bahn)")
C_MEASCLK = P("rb.c_measclk", 15e-12, "F", "ANNAHME DIO24 (C_pin 5-7 pF, [CC] S.32) + TP4 + Bahn")
C_PROBE = P("rb.c_probe", 30e-12, "F", "ANNAHME C_Sonde + Cpar (MESSKETTE_SALZ Kap. 5: 22.7-44.1 pF)")
DV_HYST = P("rb.dv_hyst", 1.0, "V", "ANNAHME Schmitt-Hysterese LVC1G14 bei 3 V (DS-Tabelle VT+/VT-, gerundet)")
I_SHOOT = P("rb.i_shoot", 1.0e-3, "A", "ANNAHME Querstrom U2, Eingang laeuft dauernd durch die Schwellen")
T_BURST = P("rb.t_burst", 0.6e-3, "s", "FW-2 Grenze (fluidi_board.h: 50 us + 2 x 250 us + Rest)")
N_BURST = P("rb.n_burst", 4, "-", "FW-2 FLUIDI_BURST_MAX")
T_PAUSE = P("rb.t_pause", 3 * 30e-3 + 15e-3, "s", "FW-2 3 Pausen x 30 ms + FW-1 tCONV 15 ms ([TMP] S.7 Tab. 6.6)")
I_IDLE = (P("rb.idle", 0.8e-3, "A", "[CC] S.19 Tab. 7.9 Idle, Flash aus, DCDC"),
          P("rb.idle_ldo", 1.2e-3, "A", "[CC] S.20 Tab. 7.9 Idle, Flash aus, GLDO"))
T_TMP_SETTLE = P("rb.t_tmp_settle", 1e-3, "s", "fluidi_board.h FLUIDI_SENS_PWR_SETTLE_US (Busy-Wait, CPU aktiv)")
T_I2C = P("rb.t_i2c", 0.8e-3, "s", "2 Transaktionen 100 kHz (Schreiben 3 B, Zeiger + Lesen 2 B) ~ 80 Takte")
I_TMP_CONV = (P("rb.tmp_conv", 52e-6, "A", "[TMP] S.7 Tab. 6.5 TMP1075 'during active conversion' typ "
                "(TMP1075N Tab. 6.6 nennt nur IDD_AVG 4.8/7.5 uA) -> ANNAHME fuer N"),
              P("rb.tmp_conv_max", 85e-6, "A", "[TMP] S.7 Tab. 6.5 max (ANNAHME fuer N)"))
R_PULLUP = P("rb.r_i2c", 4.7e3, "Ohm", "[NET] R4/R5 4.7 kOhm nach SENS_PWR")
C_SENS = P("rb.c24", 100e-9, "F", "[NET] C24 100 nF an SENS_PWR (je Messung umgeladen)")
R_GATE = P("rb.r13", 100e3, "Ohm", "[NET] R13 100 kOhm VDD-OSC_EN_N, Strom nur bei Kette ein")
T_CPU_MEAS = (P("rb.t_cpu_meas", 3e-3, "s", "ANNAHME Auswertung, Datensatz, Planung (CPU aktiv)"),
              P("rb.t_cpu_meas_p", 6e-3, "s", "ANNAHME pess."))
Q_FLASH_REC = P("rb.q_flash_rec", FLASH_Q_PER_2K * 24 / 2048, "C",
                "24-B-Datensatz anteilig an [CC] S.21 Tab. 7.11 (2 kB), fl_ringlog.c")


def rb_chain_current(f, v=VDD_NOM):
    """Messkette U2 + U4-U6 bei Oszillatorfrequenz f: Cpd*V*f je Stufe + Knotenlasten + Sonde + Querstrom."""
    cpd = (CPD_G14 + CPD_G80 * (1 + 1 / 2 + 1 / 4)) * v * f
    load = v * f * (C_NODE + C_NODE / 2 + C_NODE / 4 + C_MEASCLK / 8)
    probe = C_PROBE * DV_HYST * f
    return cpd + load + probe + I_SHOOT


def rb_meas_charge(case):
    """Ladung je Messung (ohne Funk): TMP1075N + 4 Bursts + CPU + Flash; pess: Idle statt Standby in Pausen."""
    pess = case != "real"
    k = 1 if pess else 0
    s = SOCS["CC2340R5"]
    icpu = s["cpu_ldo"] if pess else s["cpu"]
    i_chain = rb_chain_current(F_OSC[k])
    q = {}
    q["Kette (4 Bursts)"] = N_BURST * T_BURST * (i_chain + icpu + VDD_NOM / R_GATE)
    q["TMP1075N + I2C"] = (T_TMP_SETTLE * icpu + T_I2C * (I_IDLE[k] + VDD_NOM / R_PULLUP)  # ~50 % low je Leitung
                           + I_TMP_CONV[k] * (T_PAUSE - 3 * 30e-3 + T_TMP_SETTLE + T_I2C) + C_SENS * VDD_NOM)
    q["Pausen (Standby real / Idle pess)"] = T_PAUSE * I_IDLE[k] if pess else 0.0
    q["CPU + Flash"] = T_CPU_MEAS[k] * icpu + Q_FLASH_REC
    f = PESS_EVENT if pess else 1.0
    return {kk: v * f for kk, v in q.items()}, i_chain


# ---- Funk und LED Rev B ---------------------------------------------------------------------------
ADV_IV = P("rb.adv_iv", 27.5, "s", "[FW] fl_settings.c adv_interval_ms 27500 (= reach_interval(1 min))")
N_FAST_ADV = P("rb.fast_adv", 2000 / 100, "1/Taste", "[FW] fl_app.c FAST_ADV_MS 2000 / FAST_ADV_INT_MS 100")
I_LED = P("rb.i_led", 3e-3, "A", "FW-4 / PROTOCOL 10.1 Obergrenze 3 mA (Rechnung D1 + R6/R7/R8 siehe Bericht)")
T_LED_AUTO = P("rb.led_l3", 20e-3, "s", "PROTOCOL 10.2 L3 Gruen 1 x 20 ms je automatischer Messung (heartbeat_led = 1)")
T_LED_MAN = P("rb.led_l1", 2 * 30e-3, "s", "PROTOCOL 10.2 L1 Gruen 2 x 30 ms je Tastendruck")
T_LED_WATER = P("rb.led_l8", 12 * 60 * 5e-3, "s/Tag", "PROTOCOL 10.2 L8 1/min x 5 ms, 12 h (nur pess.)")
LED_PULSE = P("rb.led_pulse", 5e-3, "s", "FW-4 / core/fl_ui.c FL_LED_PULSE_MS (Pause FL_LED_PAUSE_MS gleich)")
Q_LED_WAKE = P("rb.q_led_wake", 0.2e-3 * 2.6e-3, "C",
               "ANNAHME je Schaltflanke: Wecken aus Standby + fl_app_process 0.2 ms bei CPU 2.6 mA ([CC] S.19)")
T_IDLE_PWM_L1 = P("rb.t_pwm_l1", 2 * 55e-3 + 125e-3, "s",
                  "Vergleich LGPT-PWM: Idle waehrend L1 (Pulsfolgen 2 x 55 ms + Pause), LGPT im MCU-Bereich, "
                  "im Standby aus (TRM SWCU193A S.262 Kap. 6.4.5)")
N_MAN_RB = P("rb.n_man", 2, "1/Tag", "REQ-ENE-04 Standardprofil")
C_BUF_RB = P("rb.c_buf", 4 * 100e-6, "F", "D-013 Prototyp 4 x 100 uF (C1-C4)")
CUTOFF_RB = P("rb.cutoff", 0.90, "-", "concept_energy.py CUTOFF_FACTOR: Abschaltung 2.4 V unter Last (E1, FW-5), "
              "[PAN] S.1 Entladekurve abgelesen")


def rb_daily(n_auto, case, c_buf=C_BUF_RB):
    pess = case != "real"
    k = {"real": 0, "pessA": 1, "pessDS": 2}[case]
    s = SOCS["CC2340R5"]
    parts = {}
    for name, v in RB_SLEEP.items():
        i = v[k]
        if name.startswith("C1-C4"):
            i = i * c_buf / C_BUF_RB
        parts["Schlaf: " + name] = i * DAY
    n_meas = n_auto + N_MAN_RB
    qm, _ = rb_meas_charge(case)
    parts["Messung (TMP, Kette, CPU)"] = n_meas * sum(qm.values())
    parts["Advertising 27.5 s"] = DAY / ADV_IV * adv_event_charge(s, pess)
    parts["Schnelles Advertising nach Taste"] = N_MAN_RB * N_FAST_ADV * adv_event_charge(s, pess)
    parts["Datensitzung je Messung"] = n_meas * conn_charge(s, pess)
    t_led = n_auto * T_LED_AUTO + N_MAN_RB * T_LED_MAN + (T_LED_WATER if pess else 0.0)
    n_edges = 2 * (n_auto * T_LED_AUTO + N_MAN_RB * T_LED_MAN + (T_LED_WATER if pess else 0.0)) / LED_PULSE
    parts["LED"] = I_LED * t_led + n_edges * Q_LED_WAKE * (PESS_EVENT if pess else 1.0)
    parts["OTA 1/Jahr"] = ota_charge(s, pess) / YEAR_D
    tot = sum(parts.values()) * (PESS_TOTAL if pess else 1.0)
    return tot, parts


def rb_lifetime_months(q_day, case):
    cell = CELLS["CR2032 (Renata)"]
    k = 0 if case == "real" else 1
    cap = cell["cap"]
    usable = cap * cell["util"][k] * CUTOFF_RB * mAh
    sd_day = cap * cell["sd"][k] * mAh / YEAR_D
    return usable / (q_day + sd_day) / MONTH_D


def rb_pulse_drop(i, t, n=1, pause=0.0, r=R_CELL_EOL, c=C_BUF_RB * DCBIAS * 0.8):
    """Einbruch an VDD (RC-Modell Zelle R_int + Puffer C_eff) fuer n Rechteckpulse i, Dauer t, Pause pause."""
    import math
    tau = r * c
    dv = 0.0
    worst = 0.0
    for j in range(n):
        dv = i * r + (dv - i * r) * math.exp(-t / tau)
        worst = max(worst, dv)
        if j + 1 < n:
            dv *= math.exp(-pause / tau)
    return worst


def revb_report():
    L = []
    w = L.append
    w("# fluidi Sensor Rev B - Energiebudget (erzeugt von scripts/energy_budget.py --revb)\n")
    w("| | |\n|---|---|")
    w("| Grundlage | Layout/Netzliste Rev B (`hardware/sensor/out/fluidi_sensor.net`), BOM `fluidi_sensor_bom_jlc.csv`, "
      "PINMAP Rev B (FW-1..10), Firmware `firmware/sensor` (Einstellungen, Burst-Konstanten) |")
    w("| Zelle | CR2032 225 mAh ([RC32] S.1 / [PAN] S.1), nutzbar real 90 % / pess 75 % (REQ-ENE-08) x 0.90 "
      "(Abschaltung 2.4 V unter Last, E1) |")
    w("| Faelle | **real** = Typwerte, DCDC; **pess. A** = REQ-ENE-08 (Typ x1.5, Ereignisse x1.5, +20 %), Teile ohne "
      "Typwert mit ANNAHME; **pess. DS** = jedes Leck an der Datenblattgrenze (REQ-ENE-08 'Maximalwert', "
      "Nachweisfall REQ-ENE-02) |")
    w("| Profil | n automatische Messungen/Tag + 2 manuelle (REQ-ENE-04), Advertising 27.5 s (Reaktionszeit 1 min), "
      "Datensitzung je Messung, LED L3/L1 (pess. + L8 12 h), OTA 1/Jahr |")
    w("")
    w("## 1 Ruhestrom (Schlaf, FW-8) je Bauteil [uA]\n")
    w("| Bauteil / Pfad | real | pess. A | pess. DS | Quelle / Begruendung |")
    w("|---|---|---|---|---|")
    tot = [0.0, 0.0, 0.0]
    for name, v in RB_SLEEP.items():
        for j in range(3):
            tot[j] += v[j]
        w(f"| {name} | {v[0]*1e6:.3f} | {v[1]*1e6:.3f} | {v[2]*1e6:.3f} | {v[3]} |")
    w(f"| **Summe Schlaf** | **{tot[0]*1e6:.2f}** | **{tot[1]*1e6:.2f}** | **{tot[2]*1e6:.2f}** | "
      "REQ-ENE-09 Schlaf <= 3 uA (am Prototyp gemessen, ENERGIEMESSUNG E1) |")
    w("")
    w("## 2 Messung Rev B (je Messung, ohne Funk) [uC]\n")
    qr, ir = rb_meas_charge("real")
    qp, ip = rb_meas_charge("pessA")
    w(f"Messkettenstrom (U2 + U4-U6, Cpd + Lasten + Sonde + Querstrom): real {ir*1e3:.1f} mA bei "
      f"{F_OSC[0]/1e6:.1f} MHz, pess. {ip*1e3:.1f} mA bei {F_OSC[1]/1e6:.1f} MHz "
      "(MESSKETTE_SALZ Kap. 5: 10.2 mA). Dazu CPU und R13 (30 uA) waehrend des Bursts.\n")
    w("| Anteil | real | pess. (x1.5) |")
    w("|---|---|---|")
    for kk in qr:
        w(f"| {kk} | {qr[kk]*1e6:.1f} | {qp[kk]*1e6:.1f} |")
    w(f"| **Summe** | **{sum(qr.values())*1e6:.1f}** | **{sum(qp.values())*1e6:.1f}** |")
    w("")
    w("## 3 Tagesbudget und Laufzeit CR2032 (4 x 100 uF, D-013)\n")
    w("| Messungen/Tag (auto + 2 manuell) | Fall | Mittelstrom [uA] | davon Schlaf [uA] | Laufzeit [Monate] | "
      "Laufzeit [Jahre] | >= 12 Monate |")
    w("|---|---|---|---|---|---|---|")
    res = {}
    for n in (4, 5, 6):
        for case in ("real", "pessA", "pessDS"):
            q, p = rb_daily(n, case)
            sl = sum(v for kk, v in p.items() if kk.startswith("Schlaf")) / DAY * 1e6
            m = rb_lifetime_months(q, case)
            res[(n, case)] = m
            ok = "ja" if m >= 12 else "**nein**"
            w(f"| {n} + 2 | {case} | {q/DAY*1e6:.2f} | {sl:.2f} | {m:.1f} | {m/12:.1f} | {ok} |")
    w("")
    w("Laufzeiten ueber ca. 120 Monate sind rechnerisch; begrenzend ist dann die Lagerfaehigkeit/Alterung der Zelle "
      "(kein Wert in [PAN]/[RC32], ANNAHME ~10 Jahre).")
    w("")
    w("### 3b Serienoption 2 x 100 uF (C3/C4 DNM, D-013)\n")
    w("| Messungen/Tag | real | pess. A | pess. DS |")
    w("|---|---|---|---|")
    for n in (4, 5, 6):
        row = [f"{rb_lifetime_months(rb_daily(n, c, 200e-6)[0], c):.1f}" for c in ("real", "pessA", "pessDS")]
        w(f"| {n} + 2 | {row[0]} | {row[1]} | **{row[2]}** |")
    w("")
    w("### 3c Budgetanteile 6 + 2 Messungen/Tag (vor +20 %-Zuschlag) [mC/Tag]\n")
    w("| Posten | real | pess. A | pess. DS |")
    w("|---|---|---|---|")
    ps = [rb_daily(6, c)[1] for c in ("real", "pessA", "pessDS")]
    for kk in ps[0]:
        w(f"| {kk} | {ps[0][kk]*1e3:.2f} | {ps[1][kk]*1e3:.2f} | {ps[2][kk]*1e3:.2f} |")
    w("")
    w("## 4 Pulslast (REQ-ENE-06: <= 0.2 V bei R_int 100 Ohm)\n")
    c_eff = C_BUF_RB * DCBIAS * 0.8
    w(f"RC-Modell: R_int {R_CELL_EOL:.0f} Ohm, C_eff = 4 x 100 uF x {DCBIAS} (DC-Bias, ANNAHME) x 0.8 (Toleranz) "
      f"= {c_eff*1e6:.0f} uF, tau = {R_CELL_EOL*c_eff*1e3:.0f} ms. Vollstaendige Rechnung mit DCDC und "
      "Ereignisformen: `simulation/spice/supply/supply_report.txt`.\n")
    s = SOCS["CC2340R5"]
    i_burst_p = ip + s["cpu_ldo"] + VDD_NOM / R_GATE
    rows = [
        ("Messung FW-2: 4 x 0.6 ms, Pause 30 ms (pess.)", i_burst_p, T_BURST, 4, 30e-3),
        ("Messung ohne FW-2: 16 x 0.6 ms am Stueck (pess.)", i_burst_p, 16 * T_BURST, 1, 0.0),
        ("TX 0 dBm GLDO, 3 Kanaele ~0.38 ms (pess.)", s["tx_ldo"], T_ADV_TX, 3, T_RX_WIN + T_CH),
        ("LED 3 mA, 5 ms (L8)", I_LED, 5e-3, 1, 0.0),
        ("LED 3 mA, 30 ms am Stueck (ohne FW-4)", I_LED, 30e-3, 1, 0.0),
        ("LED L1 nach FW-4: 6 x 5 ms, Pause 5 ms", I_LED, LED_PULSE, 6, LED_PULSE),
        ("LED 1 s (L6/L14) nach FW-4: 100 x 5 ms, Pause 5 ms", I_LED, LED_PULSE, 100, LED_PULSE),
        ("LED Blau 3.5 mA (nur bei VDD > 3.1 V, frische Zelle) 100 x 5 ms, mit R_int 100 Ohm gerechnet", 3.5e-3, LED_PULSE, 100, LED_PULSE),
    ]
    w("| Ereignis | Strom [mA] | Einbruch [mV] | <= 200 mV |")
    w("|---|---|---|---|")
    for name, i, t, n, pz in rows:
        dv = rb_pulse_drop(i, t, n, pz)
        w(f"| {name} | {i*1e3:.1f} | {dv*1e3:.0f} | {'ja' if dv <= 0.2 else '**nein**'} |")
    w("")
    w("LED nach FW-4 (core/fl_ui.c): Pulse <= 5 ms, Pause >= 5 ms. Schritte <= 50 ms behalten die Lichtmenge "
      "(gleiche Helligkeit, Folge laenger), laengere Schritte die Dauer bei 50 % Tastgrad. Software-Takt statt LGPT-PWM: "
      f"PWM haelt den Chip im Idle ({I_IDLE[0]*1e3:.1f} mA, [CC] S.19), fuer L1 "
      f"{T_IDLE_PWM_L1*I_IDLE[0]*1e6:.0f} uC zusaetzlich; Software-Takt 24 Flanken x {Q_LED_WAKE*1e6:.2f} uC = "
      f"{24*Q_LED_WAKE*1e6:.0f} uC (LED selbst {I_LED*T_LED_MAN*1e6:.0f} uC). "
      "Ohne FW-4 ueberschreiten LED-Ereignisse > 5 ms 0.2 V bei 100 Ohm (wie SPICE). Zelltemperatur: CR2032 -30...+85 C ([PAN] S.1); "
      "Kapazitaet bei Kaelte nicht gesondert reduziert (Innenraum, ANNAHME), Innenwiderstand bei Kaelte ueber "
      "R_int 100 Ohm EOL abgedeckt (REQ-ENE-06).")
    w("")
    w("## 5 Parameter (Auszug Rev B)\n")
    w("| Schluessel | Wert | Einheit | Quelle |")
    w("|---|---|---|---|")
    for kk, (v, u, src) in PARAMS.items():
        if kk.startswith("rb."):
            vs = f"{v:.4g}" if isinstance(v, float) else str(v)
            w(f"| {kk} | {vs} | {u} | {src} |")
    return "\n".join(L) + "\n", res


def main():
    if "--params" in sys.argv:
        print_params()
        return
    if "--revb" in sys.argv:
        txt, _ = revb_report()
        if "--out" in sys.argv:
            path = sys.argv[sys.argv.index("--out") + 1]
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(txt)
            print(f"geschrieben: {path}")
        else:
            print(txt)
        return
    print("# fluidi Energiebudget - Ausgabe scripts/energy_budget.py\n")
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
