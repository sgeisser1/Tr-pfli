# Sicherheit zuerst – vor jeder Arbeit mit diesem Paket lesen

1. **Knopfzellen (CR2032):** Verschlucken ist lebensgefährlich (Verätzung innert Stunden). Zellen nur in der
   Originalverpackung (kindergesichert) oder in der abschliessbaren Box lagern; lose Zellen nie offen liegen lassen.
   Bei Verdacht auf Verschlucken sofort Notruf **144** (Sanität) bzw. Tox Info Suisse **145**. Wechsel nur nach
   `6_anleitungen/BATTERIEWECHSEL.md`; nur Panasonic CR2032 (D-006); Wareneingang nach `2_bestellung/EINKAUFSLISTE.md` S1.
2. **Vergussmasse ER2223 und Fensterkleber UHU plus endfest 300:** Sicherheitsdatenblätter in `6_anleitungen/sdb/`.
   Härter ER2223 Teil B ist **ätzend** (H314) und sensibilisierend. **Vor dem Öffnen des ersten Beutels** (D-030, unten):
   SDB Teil B in DE/EN/FR/IT beim Händler anfordern (vorliegend nur HU – nicht ausreichend), Handschuh-Beständigkeitsliste
   ablegen, Schutzausrüstung bereit (Korbbrille EN 166 Kennzeichnung 3 + Visier, Nitrilhandschuhe EN ISO 374,
   Schürze, Augenspülflasche, Halbmaske Filter A oder Absaugung; `2_bestellung/EINKAUFSLISTE.md` V-Z7…V-Z10).
   Ablauf `6_anleitungen/MONTAGE_SENSOR.md` Kap. 1 und 3a.
3. **Programmieren nur nach `5_firmware/PROGRAMMIEREN_SENSOR.md`:** nie mit eingelegter Zelle; Weg B nur mit
   Dummy-Scheibe, Netzteil 2.0 V (höchstens 2.1 V mit PL2303), Strombegrenzung 10 mA; USB zuerst ein, zuletzt aus.
4. **Testfirmware nie an Endnutzer** (auch nicht per OTA): nur Muster im Labor, `5_firmware/TESTFIRMWARE.md`.
   Die Binärdateien in `5_firmware/MUSTER_DEV/` sind DEV-signiert und **nicht freigegeben**.
5. **Gateway-Netzteil:** nur das Original-Netzteil (EU-Konformitätserklärung im Register, GW-PSU), nicht im Giessbereich
   der Pflanzen aufstellen, Kabel und Gehäuse unbeschädigt.

## Freigabebedingungen Vergussmasse (Auszug `docs/requirements/DECISIONS.md`)

### D-030 · 2026-11-09 · Vergussmasse und Sondenversiegelung (Orchestrator, nach Sicherheit R1+R2 ohne Veto)
- **Entscheid:** Electrolube **ER2223** (2K-Epoxid, Resin Pack 250 g) für Schott, Kragen und Kantenversiegelung der
  Sonde; Sondenflächen ohne Zusatzschicht (Feldsimulation `simulation/field/coat_epoxy.py`: 100 µm kosten 12–17 %
  Spanne). Verarbeitung Variante **M-A** (Beutel einmal ungemischt abfüllen, je Sitzung ≥ 8 g wägen) unter MA-1…MA-5;
  bis dahin M-B (ganzer Beutel). Kosten: Verbrauch in den Stückkosten (≈ 0.33 CHF), Beutel und Zubehör als
  Einmalkosten (D-005).
- **MA-6 (Orchestrator):** M-A gilt auch ohne Antwort von Electrolube, wenn MA-1, MA-2, MA-4 umgesetzt und V-3 und V-6
  bestanden sind.
- **Freigabebedingungen:** `docs/concepts/vergussmasse_versiegelung.md` D-030 (1–5): SDB Teil B in Landessprache und
  Handschuh-Beständigkeitsliste vor dem ersten Beutel; V-1…V-3 vor dem Musterverguss; PT11.19 (≥ 2 Muster), PT11.23
  und Tg-Nachweis (Electrolube oder V-6) vor der Serie, sonst Rückfallmasse Kap. 9a.
- **Alternativen:** ER2221 (gefüllt, Tg unbekannt, Rückfall), MG 832HT (H360), Stycast 2651-40 (≈ 300 CHF), ER2188/832B (Tg zu tief).
- **Quelle:** `docs/reviews/phase6_vergussmasse_sicherheit.md` (R1, R2), Konzept, MONTAGE_SENSOR Kap. 3a.
- **Status:** gültig mit Auflagen.
