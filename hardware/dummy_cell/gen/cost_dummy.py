#!/usr/bin/env python3
"""fluidi Dummy-Scheibe - Mehrkosten in der JLC-Prototypbestellung (Kostenmodell scripts/cost_model.py).

Zwei Designs (PLUS 1.0 mm, MINUS 2.0 mm), je 5 Stk (JLC-Mindestmenge), 2 Lagen, gruen, HASL bleifrei, ohne PCBA,
in DERSELBEN Bestellung wie die Sensor-Platine (Versand und DHL-Verzollungspauschale fallen dort ohnehin an).
Alle Preise aus cost_model.py (Quellen und Abrufdaten dort); Annahmen hier ausdruecklich markiert.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts")))
import cost_model as CM  # noqa: E402

QTY = 5
# [JLC-RECHNER 2026-11-06, cost_model.PCB_PRICE_USD] 2 L 1.6 mm, 22 x 150 mm, 5 Stk = 6.9 USD. Die Scheiben sind
# kleiner (PLUS 27.9 x 19.8, MINUS 44.4 x 19.8 mm) -> 6.9 USD ist eine OBERE Grenze je Design (ANNAHME: Preis
# faellt nicht unter die Promo, steigt aber nicht mit kleinerer Flaeche).
P_2L_5 = CM.PCB_PRICE_USD[(2, 5)]
# [JLC] https://jlcpcb.com/pcb-fabrication/fr4-pcb "FR4 PCBs starting from just $2" (<= 100 x 100 mm, JLCPCB_NOTES
# Kap. 5): UNTERE Grenze je Design 2.0 USD (ANNAHME: Promo gilt je Design auch neben einer 4-Lagen-Bestellung).
P_PROMO = 2.0
# 1.0 mm: Standarddicke (JLCPCB_NOTES Kap. 3); Aufpreis ANNAHME 0 ([DRITTQUELLE] techoverflow: 0.8-1.6 mm gruen ohne
# Aufpreis). 2.0 mm, 2 Lagen: cost_model.SURCHARGE_2MM_FACTOR (ANNAHME, nicht abgelesen).
F_2MM = CM.SURCHARGE_2MM_FACTOR
# [JLC] Extra Charges Nr. 6 (JLCPCB_NOTES Kap. 5, lokal JLCPCB_ExtraCharges_Auszug_2026-11-08.txt): Einzelplatine mit
# einer Seite 1.5-3 cm -> Entgraten/Ecken 0.02 USD/Stk; beide Scheiben 19.8 mm breit -> betroffen.
DEBURR = 0.02


def increment_chf(usd):
    """Mehrkosten in CHF fuer zusaetzliche JLC-Positionen in einer bestehenden DHL-Sendung."""
    fx = CM.USD_TO_CHF * (1 + CM.FX_CARD_MARKUP)
    vat = usd * CM.USD_TO_CHF * CM.CH_VAT
    # DHL-Vorlagegebuehr: max(3 CHF, 2 % der Abgaben) - Obergrenze: 2 % auf die zusaetzliche MWST
    fee = CM.DHL_FEE_PCT * vat
    return usd * fx, vat, fee


def main():
    rows = []
    for name, f in (("Obergrenze (Rechnerpreis 2 L 5 Stk)", P_2L_5), ("Untergrenze (Promo $2)", P_PROMO)):
        plus = f + DEBURR * QTY
        minus = f * F_2MM + DEBURR * QTY
        usd = plus + minus
        pcb, vat, fee = increment_chf(usd)
        rows.append((name, plus, minus, usd, pcb, vat, fee, pcb + vat + fee))
    print("fluidi Dummy-Scheibe Rev 1 - Mehrkosten in der JLC-Prototypbestellung (je Design %d Stk, ohne PCBA)" % QTY)
    print("Kurs %.4f CHF/USD + %.1f %% Karte, MWST %.1f %%, 2.0-mm-Faktor %.2f (ANNAHME)"
          % (CM.USD_TO_CHF, CM.FX_CARD_MARKUP * 100, CM.CH_VAT * 100, F_2MM))
    for r in rows:
        print("%-38s PLUS %.2f USD + MINUS %.2f USD = %.2f USD -> %.2f CHF + MWST %.2f + DHL %.2f = %.2f CHF"
              % r)
    print("Versand: 0 (gleiche Sendung, +~10 g; DHL pauschal bis ca. 0.5 kg, ANNAHME cost_model). "
          "Getrennte Bestellung: + Versand %.2f USD (GSDL, Warenwert < 65 USD) und Post-Verzollung"
          % CM.SHIPPING_USD["GSDL"])
    print("Optionale Teile Variante B2 (U1/R1/C1): bereits in der Einkaufsliste P3/P5/P6 (Programmieradapter), 0 CHF")


if __name__ == "__main__":
    main()
