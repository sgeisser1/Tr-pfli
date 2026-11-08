# fluidi Sensor – Montage, Verguss und Batteriewechsel (mechanischer Teil)

| | |
|---|---|
| Stand | 2026-11-08, Phase 5, Gehäuse Rev C mit V-K/M-4 (D-019, D-023) und P5-M1/M2/M3 |
| Zeichnungen | `mechanical/drawings/FL-S-00_zusammenbau_sensor.pdf` (Positionen 1–17), Einzelteile FL-S-01 … FL-S-10 |
| Bilder | `renders/final/fluidi_03_explosion.png` (alle Teile), `renders/final/fluidi_04_batteriewechsel.png` (Hülse abgezogen) |
| Grundlage | `docs/interfaces/PCB_OUTLINE.md` Kap. 7, `mechanical/PRINT_SETTINGS.md` Kap. 4–5, `docs/reviews/phase4_sicherheit_kragen_firmware.md` K-4/K-5/K-7, `docs/reviews/phase3_sleeve_sicherheit.md`, `docs/reviews/phase5_fmea_light.md` |
| Programmieren | `docs/manuals/PROGRAMMIEREN_SENSOR.md` (eigene Anleitung; Behelf Weg B steht unter Veto PS-K1) |
| Batteriewechsel für Nutzer | `docs/manuals/BATTERIEWECHSEL.md` |

Positionsnummern (Pos.) wie Stückliste FL-S-00. Koordinaten: x Breite (+ rechts von vorne), y Tiefe (0 = Front),
z Höhe (0 = Kopfunterkante). **Offen** markiert, was die Dokumentation noch nicht festlegt; dort nichts improvisieren,
sondern die Projektleitung fragen.

## 0 Offene Punkte, die die Montage betreffen

| Nr | Punkt | Stand |
|---|---|---|
| O-1 | **Vergussmasse** (Kragen, Schott): Epoxid 2K, mineralisch gefüllt, Tg ≥ 80 °C, niedriger CTE, *ein* Material für den ganzen Kragen (K-4) | Typ **offen** (`docs/datasheets/INDEX.csv` EP-K), damit auch Topfzeit, Mischverhältnis, Aushärtung, Primer. **Ohne Datenblatt kein Verguss am Serienteil.** |
| O-2 | **Kantenversiegelung/Beschichtung der Sonde** (REQ-MECH-07) | Verfahren nicht gewählt (Red-Team W-5) |
| O-3 | Klebstoff Lichtfenster | **ANNAHME** transparentes 2K-Epoxid oder UV-Kleber (PRINT_SETTINGS Kap. 5) |
| O-4 | Befestigung Klemmring (Pos. 6) in der Senkung: Spiel 0.05 je Seite im CAD, Befestigung (Presssitz/Kleber) nicht festgelegt | am Muster festlegen (PROTOTYP-PRÜFUNG) |
| O-5 | Tastermechanik (P5-M2): Zunge 0.6 mm mit Nase (Flanke 45°), Fingerkante des Stössels gleitet darauf; SW1 schaltet im CAD nominal bei 0.40 mm Tastenhub, Toleranzkette worst +0.14 mm (`check_sensor.txt` 2a–2c) | Betätigungskraft (≈ 4.7 N + Membran, μ ANNAHME), Biegespannung worst SF 1.34 (quer zu den Schichten), Last auf SW1 nach dem Durchschalten: PROTOTYP-PRÜFUNG M-T1/M-T4 |
| O-6 | Anzugsmoment Schraube M2 × 3 in ASA/Mutter | nicht festgelegt; „handfest mit PH1“ (**ANNAHME**), am Muster prüfen (ST-K1) |

## 1 Teile, Werkzeuge, Hilfsstoffe

Teile: Pos. 1–17 laut Stückliste FL-S-00 (gedruckt nach `PRINT_SETTINGS.md`, Passproben vorher bestanden).

| Werkzeug / Hilfsstoff | Zweck |
|---|---|
| Kreuzschlitz-Schraubenzieher **PH1** | Schraube ISO 7045 M2 × 3 PH1 (Pos. 12) |
| Messschieber 0.01 mm | Distanzlehre, Passungen, Dicke Dummy-Zelle |
| Lupe ≥ 10× | Sichtprüfungen (VIP-Pads, Verguss, Lötstellen; ST-E1) |
| 2 × Distanzlehre 24.2 (FL-S-10) | Abstand Kragen ↔ Schott beim Kragenverguss |
| Isopropanol, fusselfreie Tücher | Flussmittelreste im Kragenbereich entfernen (K-5) |
| 600er Schleifpapier | FDM-Naht auf den O-Ring-Gleitflächen der Hülse glätten (PRINT_SETTINGS Kap. 5) |
| Silikonfett | O-Ringe (Pos. 11) |
| Kapton-Punkt (Ø ≈ 3 mm) | Gewinde der Mutter vor Epoxid schützen (PCB_OUTLINE Kap. 7) |
| Dosierspritzen + Kanülen, Mischbecher, Waage | Verguss (Mengen siehe Kap. 4/5) |
| Vakuumkammer (falls vorhanden) | blasenfreier Verguss (K-4), sonst kopfüber mit Entlüftung |
| Nitrilhandschuhe, Schutzbrille | Epoxid (Schutzmassnahmen laut Datenblatt der gewählten Masse, O-1) |
| Halter „kopfüber“ (z. B. Lochplatte, Schraubstock mit Schutzbacken) | Kappe bzw. Sensor beim Aushärten senkrecht halten |

## 2 Vorbereitung der Druckteile

1. Teile auf Druckfehler prüfen: keine Fäden in Nuten und Schlitzen, Ablaufschlitze der Hülse (4 × 3.0 × 1.2) frei,
   Brücken (Muttertasche Kragen, USB/Schott) ohne Durchhang.
2. Hülse innen: Gleitflächen z 1.3 … 7 und 30 … 35 mit 600er Papier glätten (Naht quer zur Dichtung ist ein Leckkanal).
   Kerbe innen entgraten.
3. **Kappe (P5-M1):** Prüfen, dass der Zapfen fest mit der Kappe verbunden ist (Rev-C-Druckdatei hatte einen losen
   Zapfen; ab Phase 5 einteilig). Membran-Senkung Ø 6.4 rundum geschlossen (P5-M3, keine Öffnung zum Innenraum).
4. Masskontrolle der Prüfmasse (in den Zeichnungen gerahmt) stichprobenweise, mindestens: Hülse innen 30.8 × 9.8,
   Kappe/Zapfen 30.4 (Gleitsitz) und Nutgrund 28.1 × 7.1, Kragen 30.4 und Nutgrund, Distanzlehre 24.2 ± 0.1.

**Prüfung 2:** Passprobe (`passprobe_huelse_unten/oben`) mit Kragen bzw. Kappe und O-Ring: gleitet mit Silikonfett ohne
Klemmen, O-Ring sichtbar verpresst (PRINT_SETTINGS Kap. 4). Bei Abweichung XY-Lochkompensation anpassen, nicht die
Geometrie.

## 3 Kappe vormontieren (Pos. 1, 4–8, 10)

1. **Lichtfenster (Pos. 4)** von aussen in den Tropfenausschnitt kleben, Lichtschaft nach innen (Spalt 0.1 je Seite).
   Klebstoff nur auf den Rand, nicht auf die Sichtfläche und nicht in den Innenraum (O-3).
2. **Stössel (Pos. 8)** von unten in das Führungsrohr Ø 3.2 stecken, D-Fläche nach vorne, Finger links vor der Zunge,
   Fingerkante über der Nasenflanke (die Zunge dabei nicht nach hinten biegen).
3. **Membran (Pos. 10)** flach auf den Grund der Senkung Ø 6.4 legen.
4. **Taste (Pos. 5)** mit dem Hals von oben durch den Klemmring (Pos. 6) stecken, **Tastenteller (Pos. 7)** von unten
   auf den Hals pressen. Die Einheit Taste + Klemmring + Teller in die Senkung setzen, Klemmring auf die Membran drücken
   (Befestigung O-4).

**Prüfung 3:** Taste federt zurück (Membran), Stössel gleitet ohne Klemmen. Ohne Platine: beim Drücken bewegt sich die
Zunge sichtbar nach hinten (Nase, P5-M2), in Ruhe liegt die Fingerkante ≈ 0.1 mm vor der Flanke (Zunge nicht vorgespannt).
Fenster sitzt bündig, keine Kleberspuren auf der Sichtfläche.

## 4 Platine einsetzen und Schott vergiessen (Pos. 9, 15, 16)

1. Platine (Pos. 16, Zelle **nicht** eingesetzt) mit der bestückten Seite F **zum Fenster** von unten durch den
   Schottschlitz (26.4 × 4.0) einschieben, bis die Platinenoberkante am **Anschlag der Kappe** liegt (z 53.5). Die
   Quetschrippen (Gabel und Schott-Rückwand) drücken die Platine nach vorn an die F-Referenz.
2. Kappe **kopfüber** einspannen (Sonde zeigt nach oben). Die Platine bleibt durch ihr Gewicht am Anschlag
   (PCB_OUTLINE Kap. 2, Lage z ± 0.22).
3. **Schottkeil (Pos. 9)** in den vorderen Spalt zwischen Platine F und Schott schieben (Rückseite an F).
4. **Schott vergiessen (Pos. 15):** Epoxid (O-1) in den Schottschlitz um die Platine, Volumen ≈ **12 mm³** (CAD,
   `check_sensor.txt` Pkt. 8). Nicht überfüllen: kein Epoxid ins Zellfach (Clip-Pads liegen 0.55 mm unter der
   Vergusskante z 30.8). Aushärten kopfüber nach Datenblatt.

**Prüfung 4:** Verguss rundum lückenlos (Lupe), keine Blasen an der Platinenkante, nichts auf den Clip-Pads. Platine sitzt
weiterhin am Anschlag (Spalt Oberkante–Anschlag 0; Sicht durch das Fenster: LED mittig hinter dem Tropfen).

## 5 Kragen setzen und vergiessen (Pos. 3, 13, 14) – Sondenübergang, Dichtlinie

Der Kragenverguss ist die **Sondendichtung** (S3-K2, REQ-MECH-08). Er wird nie wieder gelöst.

1. **Reinigen (K-5):** Platine im Bereich z 0 … 8 (Dichtstreifen und Feld U3/C24) mit Isopropanol von Flussmittel
   befreien, trocknen. Falls das Datenblatt der Vergussmasse es verlangt: primern. Taschenwände des Kragens leicht
   anrauen bzw. primern.
2. **Mutter M2 (Pos. 13)** von vorne in die Muttertasche des Kragens schieben, **Kapton-Punkt** auf die Gewindeöffnung
   (unten) kleben, damit kein Epoxid ins Gewinde läuft.
3. Kragen von der Sondenspitze her über die Sonde schieben (Schlitz 20.3 × 1.9, Tasche U3/C24 auf der F-Seite).
4. Die **2 Distanzlehren 24.2 (FL-S-10)** auf der B-Seite zwischen Kragen-Oberkante und Schott-Unterkante stellen und den
   Kragen dagegen halten. Der Kragen sitzt mittig um die Platine.
5. Sensor **kopfüber** (Sondenspitze oben) einspannen. **Kragen vergiessen (Pos. 14)** von der Hohlkehle an der
   Kragenunterseite her, bis Spalt, Hohlkehle und Tasche U3/C24 gefüllt sind; Volumen ≈ **62 mm³** (CAD). Die Tasche ist
   unten offen und entlüftet nach oben (PCB_OUTLINE Kap. 7). **Nur eine Masse, kein weicher Vorverguss auf U3/C24
   (K-4).** Blasenfrei: Vakuum oder langsam füllen und entlüften.
6. Nach dem Aushärten Lehren entfernen.

**Prüfung 5:**
- Abstand Kragen-Oberkante ↔ Schott-Unterkante 24.2 ± 0.1 an beiden Seiten (Messschieber).
- Hohlkehle rundum gefüllt, kein Spalt Epoxid ↔ Platine im Dichtstreifen z 1.3 … 3.5 (Lupe), keine Lunker.
- Kein Epoxid in der O-Ring-Nut des Kragens und nicht auf den Clip-Pads (Abstand 0.55).
- Mutter fest eingegossen, Gewinde frei (Kapton entfernen, Schraube probeweise 2 Gänge eindrehen, wieder lösen).
- Sonde: Kantenversiegelung/Beschichtung nach dem festgelegten Verfahren (O-2), Stecktiefen-Markierung z −5 sichtbar.
- Für ein Opfermuster: Schliff bzw. Farbeindringprüfung durch den Kragen (K-7, Testplan ST-W4).

## 6 Programmieren

Nach Kap. `docs/manuals/PROGRAMMIEREN_SENSOR.md`, **Weg A** (Programmieradapter, Hülse abgezogen, Zugang zu TP1/TP2 im
Zellfach). Keine Zelle im Clip. Danach Dummy-Zelle entnehmen.

## 7 Zelle einsetzen, O-Ringe, Hülse schliessen (Pos. 2, 11, 12, 17)

1. **Zelle (Pos. 17)** einsetzen: Pluspol zur Front (−y), von der offenen Clip-Seite (+x, von vorne gesehen rechts)
   flach einschieben bis zum Anschlag. **Taste dabei nicht berühren** (sonst startet der ROM-Bootloader, W-10).
   Erwartet: LED-Startsignal L11 (Grün 200 ms; Fehler Rot 3 × 100 ms; PROGRAMMIEREN Kap. 6/7).
2. **O-Ringe AS568-019 (Pos. 11)** dünn mit Silikonfett einreiben und in die Nut am Kragen und am Zapfen legen. Nicht
   verdrehen, nicht über scharfe Kanten ziehen.
3. **Hülse (Pos. 2)** mit gereinigter Sonde von der Sondenspitze her aufschieben, bis der Rand im Dachziegelschlitz der
   Kappe sitzt. Gleichmässig schieben, nicht auf die Taste drücken.
4. **Schraube M2 × 3 (Pos. 12)** von unten durch den Hülsenboden eindrehen. Beim ersten Mal furcht sie durch die
   Lippe Ø 1.7 (danach unverlierbar), dann in die Mutter. Handfest anziehen (O-6). Einschraubtiefe 1.4 mm = 3.5 Gänge
   (`check_sensor.txt` 5c; UL-4200A-Massstab ≥ 2 volle Gänge, `phase3_sleeve_sicherheit.md`).

**Prüfung 7 (Pflicht, FMEA F-21/F-62):**
- Hülse lässt sich von Hand nicht abziehen, Sichtfuge rundum gleich (0.3 mm), Kerbe um den Tropfen gleichmässig.
- O-Ringe sichtbar verpresst bzw. nicht aus der Nut gequetscht (vor dem Aufschieben kontrollieren).
- Ablaufschlitze hinten frei.
- Funktion: kurzer Tastendruck → Messung/Statusanzeige (REQ-UI-04); die Taste stoppt nach dem Klick (SW1 am Anschlag,
  nominal ≈ 0.4 mm Hub), nicht erst am Taschenboden; L11 war nach dem Einsetzen sichtbar.
- Eintrag in der Musterliste: Seriennummer `fluidi-XXXX`, Prüfungen 2–7, Datum.

## 8 Batteriewechsel (Werkstatt / Muster)

Ablauf für Nutzer: `docs/manuals/BATTERIEWECHSEL.md` (mit Sicherheitshinweisen). Zusätzlich für die Werkstatt:

1. Sonde reinigen, über einer Schale arbeiten (FMEA F-22). Schraube lösen (PH1), Hülse nach unten über die Sonde
   abziehen (`renders/final/fluidi_04_batteriewechsel.png`).
2. Zelle zur offenen Clip-Seite (+x) herausschieben, **kein Metallwerkzeug** (S3-L1, F-24). Clip-Lötstellen unter der
   Lupe prüfen (Pads am Katalogminimum, Red-Team K-4).
3. Nur neue Markenzellen (Panasonic CR2032) mit **≥ 3.0 V Leerlauf** einsetzen; Zellen < 2.6 V nicht wieder verwenden,
   abkleben, entsorgen (PS-K1 Bed. 3). Taste nicht berühren, L11 beobachten.
4. O-Ringe prüfen und fetten, beschädigte ersetzen. Hülse aufschieben, Schraube handfest.
5. Prüfung 7 wiederholen. Wechsel in der Musterliste zählen (Testplan: 50 Wechsel ST-K6, Spritzwasser nach 10 Wechseln).

## 9 Demontage / Reparatur

Kappe, Platine, Schott und Kragen bilden nach dem Verguss eine Einheit und sind nicht zerstörungsfrei trennbar
(S3-K1/K2). Zugänglich bleiben nur Zellfach, O-Ringe, Hülse und Schraube.
