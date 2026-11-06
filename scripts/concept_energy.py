#!/usr/bin/env python3
"""Troepfli - Energiebudget je Konzept (Phase 2, docs/concepts/CONCEPTS.md).

Aufruf:  .venv/bin/python scripts/concept_energy.py

Teil 1 nutzt scripts/energy_budget.py unveraendert (gleiche Parameter, gleiche Funktionen) und
waehlt die Kombination SoC/Zelle je Konzept aus; zusaetzlich die Sensitivitaet "Puffer 2 x 100 uF
mit Datenblatt-Leckgrenze" (Konzepte A/B bestuecken 2 x 100 uF).
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

CONCEPTS = {
    "A Knopf: CC2340R5 + CR2450N": ("CC2340R5", "CR2450N (Renata)"),
    "B Spar: CH592F + CR2032": ("CH592F", "CR2032 (Renata)"),
    "C Akku: CC2340R5 + LiPo 125 mAh": ("CC2340R5", "LiPo ICP401230UPR 125 mAh"),
}


def part1():
    print("## 1 Konzepte A/B/C (Modell energy_budget.py, Standardprofil REQ-ENE-04)\n")
    print("| Konzept | Reaktionszeit | Mittelstrom real [uA] | Mittelstrom pess. A [uA] | "
          "Laufzeit real [Monate] | Laufzeit pess. A [Monate] | Schlaf pess. (SoC+Board) [uA] |")
    print("|---|---|---|---|---|---|---|")
    for name, (soc, cell) in CONCEPTS.items():
        s, c = eb.SOCS[soc], eb.CELLS[cell]
        for m in (1, 2, 5):
            qr, _ = eb.daily(s, m, c, "real")
            qp, pp = eb.daily(s, m, c, "pessA")
            sl = (pp["sleep_soc"] + pp["sleep_board"] + pp["mlcc"] + pp.get("vpol", 0)
                  + pp.get("li_path", 0)) / DAY * 1e6
            print(f"| {name} | {m} min | {qr/DAY*1e6:.2f} | {qp/DAY*1e6:.2f} | "
                  f"{eb.fmt_m(eb.lifetime_months(c, qr, False))} | "
                  f"**{eb.fmt_m(eb.lifetime_months(c, qp, True))}** | {sl:.2f} |")

    print("\n### 1b Sensitivitaet Puffer-Leckstrom (pess. B, Datenblattgrenze 50 Ohm*F), 1 min\n")
    print("| Konzept | Puffer nominal | Leckgrenze @3 V [uA] | Mittelstrom pess. B [uA] | Laufzeit pess. B [Monate] |")
    print("|---|---|---|---|---|")
    orig = eb.C_BUF_NOM
    try:
        for name, (soc, cell) in list(CONCEPTS.items())[:2]:
            for cnom in (100e-6, 200e-6):
                eb.C_BUF_NOM = cnom
                s, c = eb.SOCS[soc], eb.CELLS[cell]
                q, _ = eb.daily(s, 1, c, "pessB")
                print(f"| {name} | {cnom*1e6:.0f} uF | {3.0/(eb.GRM_RC/cnom)*1e6:.1f} | {q/DAY*1e6:.2f} | "
                      f"{eb.fmt_m(eb.lifetime_months(c, q, True))} |")
    finally:
        eb.C_BUF_NOM = orig

    print("\n### 1c Budgetanteile pess. A, 1 min (Anteil vor +20 %-Zuschlag)\n")
    print("| Konzept | Schlaf SoC | Board | MLCC | Verpol/Li-Pfad | Erreichbarkeit | Messung | LED | OTA |")
    print("|---|---|---|---|---|---|---|---|---|")
    for name, (soc, cell) in CONCEPTS.items():
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
    print("# Troepfli Energiebudget je Konzept - Ausgabe scripts/concept_energy.py\n")
    part1()
    part2()
