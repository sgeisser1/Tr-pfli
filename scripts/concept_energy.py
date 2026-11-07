#!/usr/bin/env python3
"""fluidi - Energiebudget je Konzept (Phase 2, docs/concepts/CONCEPTS.md).

Aufruf:  .venv/bin/python scripts/concept_energy.py

Teil 1 nutzt die Funktionen von scripts/energy_budget.py unveraendert und setzt je Konzept nur die
Board-, Puffer- und Koexistenzparameter (Klasse Patch, v0.2 nach Pruefrunde 1).
Teil 2 rechnet die Variante C-WLAN (ESP32-C3 mit WLAN im Sensor, gleicher LiPo-Pfad).

Quellen Teil 2 (lokal):
  [C3]  docs/datasheets/Espressif_ESP32-C3_Datasheet_v2.4.pdf
  [RT]  docs/datasheets/Richtek_RT9080_Datasheet_DS9080-05.pdf
Alle anderen Werte siehe energy_budget.py (PARAMS). ANNAHME = nicht aus Datenblatt.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import energy_budget as eb  # noqa: E402

DAY = eb.DAY

# ---------------------------------------------------------------------------------------------
# Konzeptspezifische Parameter v0.2 (Pruefrunde 1, RT W-2 / k-1, S2-W02):
#  - TMP1075 + I2C-Pull-ups an GPIO geschaltet -> 0 uA im Schlaf (statt Shutdown 0.37 typ / 0.65 max uA,
#    TI_TMP1075_Datasheet_SBOS854F.pdf S.7)
#  - Board-Rest: GPIO-Leckstroeme ANNAHME 0.05 real / 0.1 pess (RT 2), Reserve 0.1 pess (ANNAHME)
#  - Puffer nach REQ-ENE-06 pess.: A/A-32 4 x 100 uF (325 uF noetig, energy_budget.py Tab. 6), B 3 x 100 uF
#  - Leckgrenze Puffer = Samsung-Katalog (bestuecktes Teil C15008): >= 100 MOhm*uF (= 100 Ohm*F) fuer markierte
#    Hochkapazitaets-Typen, Samsung_CL31A107MQHNNNE_Catalog_2015-11.pdf S.53 -> 3 uA je 100 uF bei 3 V.
#    (nach Dauerpruefung S.55: 25 bzw. 12.5 MOhm*uF -> nur als Hinweis)
# ---------------------------------------------------------------------------------------------
SAMSUNG_RC = 100.0
# v0.3 (E1, Projektleiter nach Pruefrunde 2): Abschaltung 2.4 V unter Last an der Zellklemme (statt 2.0 V),
# damit der DCDC unter Last aktiv bleibt (VDDS >= 2.2 V, TI_CC2340R5_Datasheet_SWRS272F.pdf S.18).
# Nutzbarer Anteil der bis 2.0 V spezifizierten Kapazitaet: ANNAHME 0.90, abgelesen aus
# Panasonic_CR2032_Datasheet_2026-02.pdf S.1 "Discharge temperature characteristics" (20 C, 15 kOhm):
# 2.4 V bei ca. 1100 h, 2.0 V bei ca. 1150 h (~96 %); mit 0.2 V Lasteinbruch Kriterium ~2.6 V bei ca.
# 1050 h (~91 %) -> 0.90. Fuer Renata CR2450N gleicher Faktor (ANNAHME, gleiche Chemie).
CUTOFF_FACTOR = 0.90
BOARD = (0.05e-6, 0.2e-6)
MLCC_REAL_PER_100U = 0.05e-6   # ANNAHME wie energy_budget.py
MLCC_PESSA = 0.5e-6            # ANNAHME pess. A (gesamt, wie v0.1)

# v0.3 (E1): A und A-32 mit 2 x 100 uF und Abschaltung 2.4 V; A-32 rechnet mit den CR2032-Zelldaten
# des Modells (225 mAh, Renata), Panasonic CR2032 nennt ebenfalls 225 mAh (Datenblatt S.1).
CONCEPTS = {
    "A: CC2340 + CR2450N, 2 x 100 uF, 2.4 V": ("CC2340R5", "CR2450N (Renata)", 200e-6, True),
    "A-32: CC2340 + CR2032, 2 x 100 uF, 2.4 V": ("CC2340R5", "CR2032 (Renata)", 200e-6, True),
    "A (v0.2): 4 x 100 uF, 2.0 V": ("CC2340R5", "CR2450N (Renata)", 400e-6, False),
    "A-32 (v0.2): 4 x 100 uF, 2.0 V": ("CC2340R5", "CR2032 (Renata)", 400e-6, False),
    "B: CH592F + CR2032, 3 x 100 uF": ("CH592F", "CR2032 (Renata)", 300e-6, False),
    "C: CC2340 + LiPo 125 mAh": ("CC2340R5", "LiPo ICP401230UPR 125 mAh", 22e-6, False),
}


class Patch:
    """Setzt globale Parameter von energy_budget.py voruebergehend (Modell selbst unveraendert)."""
    def __init__(self, cbuf, p_miss=None):
        self.cbuf, self.p_miss = cbuf, p_miss

    def __enter__(self):
        self.old = (eb.I_OTHER_REAL, eb.I_OTHER_PESS, eb.I_MLCC_REAL, eb.I_MLCC_PESS, eb.GRM_RC, eb.C_BUF_NOM, eb.P_MISS)
        eb.I_OTHER_REAL, eb.I_OTHER_PESS = BOARD
        eb.I_MLCC_REAL = MLCC_REAL_PER_100U * self.cbuf / 100e-6
        eb.I_MLCC_PESS = MLCC_PESSA
        eb.GRM_RC, eb.C_BUF_NOM = SAMSUNG_RC, self.cbuf
        if self.p_miss is not None:
            eb.P_MISS = self.p_miss

    def __exit__(self, *a):
        (eb.I_OTHER_REAL, eb.I_OTHER_PESS, eb.I_MLCC_REAL, eb.I_MLCC_PESS, eb.GRM_RC, eb.C_BUF_NOM, eb.P_MISS) = self.old


def calc(soc, cell, cbuf, m, case, p_miss=None, cutoff24=False):
    s, c = eb.SOCS[soc], dict(eb.CELLS[cell])
    if cutoff24:
        c["util"] = tuple(u * CUTOFF_FACTOR for u in c["util"])
    with Patch(cbuf, p_miss):
        q, parts = eb.daily(s, m, c, case)
        months = eb.lifetime_months(c, q, case != "real")
        reach = eb.reach_interval(m * 60)
    return q / DAY * 1e6, months, parts, reach


def part1():
    print("## 1 Konzepte (Modell energy_budget.py, Standardprofil REQ-ENE-04, Parameter v0.3)\n")
    print("pess. A = REQ-ENE-08 mit Puffer-Leck ANNAHME 0.5 uA (Information REQ-ENE-09, Nachweis am Prototyp); "
          "**pess. DS** = Puffer-Leck an der Samsung-Datenblattgrenze (Nachweis REQ-ENE-02).\n")
    print("| Konzept | Reaktionszeit | Mittel real [uA] | Mittel pess. A [uA] | Mittel pess. DS [uA] | "
          "Laufzeit real [Mt.] | Laufzeit pess. A [Mt.] | **Laufzeit pess. DS [Mt.]** | Schlaf pess. A [uA] |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, (soc, cell, cb, cut) in CONCEPTS.items():
        for m in (1, 2, 5):
            ir, mr, _, _ = calc(soc, cell, cb, m, "real", None, cut)
            ia, ma, pa, _ = calc(soc, cell, cb, m, "pessA", None, cut)
            ib, mb, _, _ = calc(soc, cell, cb, m, "pessB", None, cut)
            sl = (pa["sleep_soc"] + pa["sleep_board"] + pa["mlcc"] + pa.get("vpol", 0) + pa.get("li_path", 0)) / DAY * 1e6
            print(f"| {name} | {m} min | {ir:.2f} | {ia:.2f} | {ib:.2f} | {eb.fmt_m(mr)} | {eb.fmt_m(ma)} | "
                  f"**{eb.fmt_m(mb)}** | {sl:.2f} |")

    print("\n### 1b Sensitivitaet Koexistenz Gateway: 50 % verpasste Advertising-Fenster (P_MISS 0.5), 1 min\n")
    print("| Konzept | Erreichbarkeitsintervall [s] | Mittel pess. A [uA] | Laufzeit pess. A [Mt.] | "
          "Mittel pess. DS [uA] | Laufzeit pess. DS [Mt.] |")
    print("|---|---|---|---|---|---|")
    for name, (soc, cell, cb, cut) in CONCEPTS.items():
        ia, ma, _, reach = calc(soc, cell, cb, 1, "pessA", 0.5, cut)
        ib, mb, _, _ = calc(soc, cell, cb, 1, "pessB", 0.5, cut)
        print(f"| {name} | {reach:.1f} | {ia:.2f} | {eb.fmt_m(ma)} | {ib:.2f} | {eb.fmt_m(mb)} |")

    print("\n### 1c Budgetanteile pess. A, 1 min (vor +20 %-Zuschlag)\n")
    print("| Konzept | Schlaf SoC | Board | MLCC | Verpol/Li-Pfad | Erreichbarkeit | Messung | LED | OTA |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, (soc, cell, cb, cut) in CONCEPTS.items():
        with Patch(cb):
            tot, p = eb.daily(eb.SOCS[soc], 1, eb.CELLS[cell], "pessA")
        base = tot / eb.PESS_TOTAL
        f = lambda k: f"{p.get(k, 0)/base*100:.1f} %"  # noqa: E731
        vp = (p.get("vpol", 0) + p.get("li_path", 0)) / base * 100
        print(f"| {name} | {f('sleep_soc')} | {f('sleep_board')} | {f('mlcc')} | {vp:.1f} % | {f('reach')} | "
              f"{f('meas')} | {f('led')} | {f('ota')} |")


# ---------------------------------------------------------------------------------------------
# Teil 2: C-WLAN (ESP32-C3, WLAN im Sensor)
# ---------------------------------------------------------------------------------------------
C3_DEEP = 5e-6        # [C3] S.57 Tab. 5-9 Deep-sleep (RTC timer + RTC memory), typ
C3_LIGHT = 130e-6     # [C3] S.57 Tab. 5-9 Light-sleep, typ
C3_RX = 84e-3         # [C3] S.56 Tab. 5-7 RX 802.11b/g/n HT20
C3_TX_PEAK = 335e-3   # [C3] S.56 Tab. 5-7 TX 802.11b 1 Mbps @21 dBm (Spitze)
C3_VMIN = 3.0         # [C3] S.54 Tab. 5-2 VDD 3.0-3.6 V
LDO_IQ = 2e-6         # [RT] S.1 RT9080 "2 uA Ground Current" (600 mA LDO; TPS7A02 hat nur 200 mA)
I_CONN = (0.100, 0.130)   # ANNAHME: Mittelstrom waehrend Verbindungsaufbau (RX-dominiert, TX-Bursts)
T_CONN = (0.8, 2.5)       # ANNAHME: Aufwachen + WLAN-Assoziation + (statische IP) + TLS-freie Abfrage [s]
DTIM_EXTRA = (0.55e-3, 1.5e-3)  # ANNAHME: Light-sleep mit WLAN-Verbindung, DTIM 3, Beacon-Empfang 2/5 ms


def wlan_case(strategy, reaction_min, pess):
    k = 1 if pess else 0
    temp = eb.SLEEP_TEMP_FACTOR if pess else 1.0
    fac = 1.5 if pess else 1.0
    li = LDO_IQ + eb.I_CHG[k] + eb.I_PROT[k] + eb.I_PCM_CELL[k]
    board = eb.I_OTHER_PESS if pess else eb.I_OTHER_REAL
    q_conn = I_CONN[k] * T_CONN[k]
    n_meas = eb.N_AUTO + eb.N_MAN
    if strategy == "deep":
        i_sleep = C3_DEEP * fac * temp
        n_wake = DAY / eb.reach_interval(reaction_min * 60.0) if reaction_min else 0
        q = (i_sleep + li + board) * DAY + (n_wake + n_meas) * q_conn
    else:  # light-sleep, dauernd assoziiert
        i_sleep = C3_LIGHT * fac * temp + DTIM_EXTRA[k]
        q = (i_sleep + li + board) * DAY + n_meas * q_conn * 0.3  # ANNAHME: kein Neuaufbau, 30 % Aufwand
    q += eb.LED_I * (eb.LED_STD + (eb.LED_WATER if pess else 0.0))
    if pess:
        q *= eb.PESS_TOTAL
    return q


def part2():
    cell = eb.CELLS["LiPo ICP401230UPR 125 mAh"]
    print("\n## 2 C-WLAN: ESP32-C3 im Sensor, LiPo 125 mAh (Modell concept_energy.py)\n")
    print("Strategie 'deep': Deep-sleep, Sensor fragt das Gateway im Erreichbarkeitsintervall ab "
          "(27.5/57.5/147.5 s, wie BLE-Modell). Strategie 'light': dauernd im WLAN angemeldet (Light-sleep + DTIM).\n")
    print("| Strategie | Reaktionszeit | Mittelstrom real [mA] | Mittelstrom pess. [mA] | "
          "Laufzeit real [Tage] | Laufzeit pess. [Tage] | REQ-ENE-03 (>= 3 Monate) |")
    print("|---|---|---|---|---|---|---|")
    rows = [("deep", 1), ("deep", 2), ("deep", 5), ("light", 1), ("deep", None)]
    for strat, m in rows:
        qr, qp = wlan_case(strat, m, False), wlan_case(strat, m, True)
        lr = eb.lifetime_months(cell, qr, False) * eb.MONTH_D
        lp = eb.lifetime_months(cell, qp, True) * eb.MONTH_D
        lab = f"{m} min" if m else "keine (nur 8 Messungen/Tag)"
        ok = "erfuellt" if lp >= 3 * eb.MONTH_D else "verfehlt"
        print(f"| {strat} | {lab} | {qr/DAY*1e3:.3f} | {qp/DAY*1e3:.3f} | {lr:.1f} | {lp:.1f} | {ok} |")
    print(f"\nSpitzenstrom TX {C3_TX_PEAK*1e3:.0f} mA ([C3] S.56) -> LDO >= 500 mA noetig (TPS7A02: 200 mA); "
          f"VDD min {C3_VMIN} V ([C3] S.54) -> mit LDO-Dropout (RT9080 0.31 V @ 600 mA, [RT] S.1) "
          f"ist der LiPo nur bis ca. 3.3-3.4 V nutzbar.")


if __name__ == "__main__":
    print("# fluidi Energiebudget je Konzept - Ausgabe scripts/concept_energy.py\n")
    part1()
    part2()
