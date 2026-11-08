# fluidi – Vorgaben des Auftraggebers (Antworten Phase 0, 2026-11-06)

Ergänzt die ursprüngliche Projektbeschreibung. Gilt als Grundlage für Phase 1.

| # | Thema | Antwort | Folgen für die Entwicklung |
|---|---|---|---|
| 1 | Tools | `scripts/install_tools.sh` wird vom Auftraggeber ausgeführt | Toolcheck danach wiederholen |
| 2 | Repository | Name `Tr-pfli` bleibt; sichtbarer Produktname und Logo: **fluidi**. Commit/Push frei | Remote auf SSH umgestellt |
| 3 | Einsatzort | Vorerst nur Büro, **ein grosser Raum ca. 10 × 15 m** | Max. Distanz Gateway–Sensor ≈ 18 m (Diagonale), Sichtverbindung wahrscheinlich, Personen/Möbel dämpfen. Ein Gateway sollte reichen (in Phase 2 belegen). |
| 4 | Gateway | Heute kein Dauerläufer vorhanden. **Raspberry Pi nur, wenn nötig.** MQTT optional | Gateway-Varianten in Phase 2 offen vergleichen, inkl. kleiner Mikrocontroller-Lösung mit USB-Netzteil. |
| 5 | Netz | **Firmen-WLAN, nicht sehr gut**; Bluetooth evtl. besser | Kein WLAN im Sensor. Gateway-Anbindung ans Firmennetz (Geräteisolation, Zertifikate auf Firmenhandys) ist ein Hauptrisiko → in Phase 2 Alternativen prüfen. |
| 6 | Töpfe | Ø 15–30 cm, kann ändern; **Erde und Granulat** | Kalibrierung pro Substrat; Sondenlänge 100 mm passt. Granulat: Luftspalte → grössere Streuung (Prototyp-Prüfung). |
| 7 | Messungen | 4–6 pro Tag; **manuelle Messung innerhalb ca. 1 min** | Sensor muss mindestens ca. alle 30–60 s kurz erreichbar sein (z. B. BLE-Advertising/Scan-Fenster) → Energiebudget. |
| 8 | Energie | Laden alle paar Monate ok; **Batterie (nicht aufladbar): max. 1 Wechsel pro Jahr** | Laufzeitziel Primärzelle ≥ 12 Monate realistisch (nicht nur optimistisch). Akku ≥ 2–3 Monate. |
| 9 | Drucker | Vermutlich **Bambu Lab P1S mit AMS** (zu bestätigen) | Geschlossener Bauraum → ASA druckbar; mehrfarbiges Logo per AMS möglich. |
| 10 | Werkstatt | Gut ausgerüstet, **kein Programmieradapter, keine 100 CHF für Messgeräte** | Programmierweg ohne teuren Adapter vorsehen (z. B. Chip mit USB/UART-Bootloader oder sehr günstiger Adapter < 10 CHF). Energiemessung mit Werkstattmitteln planen (Shunt + Oszilloskop/Multimeter-Mittelung). |

## Präzisierungen (2026-11-06, nach Phase 0)
- **Manuelle Aktualisierung:** Ziel ca. 1 min; **wenn das energetisch zu teuer ist, sind auch einige
  Minuten akzeptabel.** → In Phase 1/2 als Muss ≤ 5 min, Wunsch ≤ 1 min festlegen und die Energie
  beider Werte ausweisen.
- **Firmen-WLAN:** Die Firma sieht eigene Geräte im WLAN evtl. nicht gern, **möglich ist es aber
  durchaus.** → Gateway im Firmen-WLAN ist zulässig; Lösungen mit möglichst wenig Eingriff ins
  Firmennetz bevorzugen und Alternativen (z. B. ohne WLAN-Gateway) im Konzept mitbewerten.

## Ergänzungen Phase 2 (2026-11-06)
- **Firmen-WLAN-Test bestanden:** Geräte im Firmen-WLAN sehen sich gegenseitig. Ein Gateway im
  Firmen-WLAN ist ok und schnell. Wunsch: nicht zu viele Geräte ins Netz → nur das Gateway im WLAN,
  Sensoren ausschliesslich über BLE.
- **JLC-Preise** (Rechner, 22 × 150 mm, grün, LeadFree HASL, abgelesen vom Auftraggeber), USD gesamt für 5/10/15/20 Stk:
  2 L 1.6 mm 6.9/8.7/10.4/12.3 · 4 L 1.6 mm 32.3/34.5/36.8/39.0 · 4 L 2.0 mm 73.8/76.6/79.4/82.1 ·
  4 L 1.6 mm 5 Stk ENIG 44.2, ENIG + Epoxy filled & capped 64.5.
- **Versand CH** (JLC): DHL Express 23.44 USD, UPS 25.36, FedEx 31.15, Global Standard Direct Line 7.63 USD
  (10–12 Tage, max. 1.5 kg und Warenwert ≤ 65 USD).
- **JLC-Angebot Rev B** (Rechner, abgelesen vom Auftraggeber 2026-11-08): 26 × 158.5 mm, 4 L, 1.6 mm, ENIG,
  Epoxy Filled & Capped: **5 Stk 65.21 USD, 20 Stk 76.30 USD** (gesamt, ohne Versand/PCBA).
- **mDNS im Firmen-WLAN** (Auftraggeber 2026-11-08): `*.local` funktioniert, mit anderen Raspberry Pi geprüft →
  Red-Team W-9 erledigt, kein Rückfallweg nötig.
- **Koexistenz WLAN/BLE am Pi Zero 2 W** (Red-Team W-7): Test durch den Auftraggeber später → PROTOTYP-PRÜFUNG.
