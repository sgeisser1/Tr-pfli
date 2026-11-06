# Tröpfli – Vorgaben des Auftraggebers (Antworten Phase 0, 2026-11-06)

Ergänzt die ursprüngliche Projektbeschreibung. Gilt als Grundlage für Phase 1.

| # | Thema | Antwort | Folgen für die Entwicklung |
|---|---|---|---|
| 1 | Tools | `scripts/install_tools.sh` wird vom Auftraggeber ausgeführt | Toolcheck danach wiederholen |
| 2 | Repository | Name `Tr-pfli` bleibt; sichtbarer Produktname und Logo: **Tröpfli**. Commit/Push frei | Remote auf SSH umgestellt |
| 3 | Einsatzort | Vorerst nur Büro, **ein grosser Raum ca. 10 × 15 m** | Max. Distanz Gateway–Sensor ≈ 18 m (Diagonale), Sichtverbindung wahrscheinlich, Personen/Möbel dämpfen. Ein Gateway sollte reichen (in Phase 2 belegen). |
| 4 | Gateway | Heute kein Dauerläufer vorhanden. **Raspberry Pi nur, wenn nötig.** MQTT optional | Gateway-Varianten in Phase 2 offen vergleichen, inkl. kleiner Mikrocontroller-Lösung mit USB-Netzteil. |
| 5 | Netz | **Firmen-WLAN, nicht sehr gut**; Bluetooth evtl. besser | Kein WLAN im Sensor. Gateway-Anbindung ans Firmennetz (Geräteisolation, Zertifikate auf Firmenhandys) ist ein Hauptrisiko → in Phase 2 Alternativen prüfen. |
| 6 | Töpfe | Ø 15–30 cm, kann ändern; **Erde und Granulat** | Kalibrierung pro Substrat; Sondenlänge 100 mm passt. Granulat: Luftspalte → grössere Streuung (Prototyp-Prüfung). |
| 7 | Messungen | 4–6 pro Tag; **manuelle Messung innerhalb ca. 1 min** | Sensor muss mindestens ca. alle 30–60 s kurz erreichbar sein (z. B. BLE-Advertising/Scan-Fenster) → Energiebudget. |
| 8 | Energie | Laden alle paar Monate ok; **Batterie (nicht aufladbar): max. 1 Wechsel pro Jahr** | Laufzeitziel Primärzelle ≥ 12 Monate realistisch (nicht nur optimistisch). Akku ≥ 2–3 Monate. |
| 9 | Drucker | Vermutlich **Bambu Lab P1S mit AMS** (zu bestätigen) | Geschlossener Bauraum → ASA druckbar; mehrfarbiges Logo per AMS möglich. |
| 10 | Werkstatt | Gut ausgerüstet, **kein Programmieradapter, keine 100 CHF für Messgeräte** | Programmierweg ohne teuren Adapter vorsehen (z. B. Chip mit USB/UART-Bootloader oder sehr günstiger Adapter < 10 CHF). Energiemessung mit Werkstattmitteln planen (Shunt + Oszilloskop/Multimeter-Mittelung). |
