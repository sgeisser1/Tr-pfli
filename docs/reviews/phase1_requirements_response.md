# Phase 1 – Antworten des Erstellers auf die Prüfbefunde (Runde 1)

Ersteller: Orchestrator (Projektleitung). Ergebnis: `REQUIREMENTS.md` v0.2 (2026-11-06).
Legende: ✅ umgesetzt · 🔶 teilweise/angepasst umgesetzt (Begründung) · ❌ abgelehnt (Begründung)

## Sicherheit (`phase1_requirements_sicherheit.md`)

| Befund | Stufe | Antwort | Umsetzung |
|---|---|---|---|
| S-K01 Wasser im Kopf bei eingesetzter Zelle | kritisch/Veto | ✅ | neu REQ-SAF-05 (getrennt abgedichtetes Fach, Flutungstest 24 h); REQ-MECH-13 mit eingesetzter Zelle + Sichtprüfung |
| S-K02 Schutz unabhängig von Firmware | kritisch/Veto | ✅ | neu REQ-SAF-LI-07 (Test mit gelöschter/angehaltener MCU) |
| S-K03 Verschluckschutz Muss | kritisch/Veto | ✅ | REQ-SAF-CC-04 Muss (UL 4200A-Massstab, Falltest 1 m), REQ-SAF-CC-02, REQ-SAF-DOC-01 |
| S-K04 Ladeport technisch absichern | kritisch/Veto | ✅ | neu REQ-SAF-LI-08 (PTC/Sicherung, Überspannung bis 20 V, Test Fremdnetzteile/nass); REQ-SAF-LI-06 |
| S-W01 Rückstrom Einzelfehler, Pads | wichtig | ✅ | REQ-SAF-CC-03 (zwei unabhängige Begrenzungen), REQ-SAF-06 |
| S-W02 Ladefenster, NTC-Kopplung | wichtig | ✅ | REQ-SAF-LI-02 |
| S-W03 Timer, Toleranz, Vorladung, Ruhestrom | wichtig | ✅ | REQ-SAF-LI-03, -04 |
| S-W04 mechanische Belastung prüfbar | wichtig | ✅ | REQ-SAF-LI-05 (Kraftfluss, Quellraum; 10 % als ANNAHME) |
| S-W05 messbares Brandkriterium | wichtig | 🔶 | REQ-SAF-01: Einzelfehlerliste + Kriterien; Grenzwert als Erwärmung ≤ 25 K statt absolut, weil der Kopf in der Sonne schon ohne Fehler bis ~65 °C erreichen kann (RB-03). Grenzwert als ANNAHME, Quelle in Phase 2. |
| S-W06 Sonnentemperatur, Akkualterung | wichtig | ✅ | RB-03 (65 °C), REQ-SAF-LI-09, OP-04 |
| S-W07 Signatur Muss, Rollback | wichtig | ✅ | REQ-FW-04 Muss |
| S-W08 Schlüssel, Replay-Schutz | wichtig | ✅ | REQ-RF-05, -06 |
| S-W09 Passwort, SSH, Root-CA-Risiko | wichtig | ✅ | REQ-SAF-NET-01, -02, neu -04; OP-07 |
| S-L01 Messpunkt ohne Schutzumgehung | klein | ✅ | REQ-ENE-07 |
| S-L02 Pads im dichten Raum | klein | ✅ | REQ-SAF-06 |
| S-L03 Entsorgung, Lagerung | klein | ✅ | REQ-SAF-DOC-01, REQ-DOC-02 |
| S-L04 Verpolung 24 h | klein | ✅ | REQ-SAF-CC-01 |
| S-L05 korrosionsbeständige Kontakte | klein | ✅ | REQ-SAF-CC-02 |
| S-L06 Portliste, Portscan | klein | ✅ | REQ-SAF-NET-02 |
| S-L07 geprüftes Netzteil Gateway | klein | ✅ | REQ-SAF-DOC-02 |

## Red Team (`phase1_requirements_redteam.md`)

| Befund | Stufe | Antwort | Umsetzung |
|---|---|---|---|
| F-01 Kosten nur Soll, Komfort-Muss | kritisch | ✅ | Kap. 1.2 Prioritätsregel; REQ-FAB-04 Muss mit Freigabevorbehalt; Jahresdiagramm und Firefox/Safari-Desktop auf Soll; 5-Jahres-Historie auf Soll (REQ-GW-01) |
| F-02 Laufzeit nur für 5 min | wichtig | ✅ | REQ-SYS-05 einstellbar 1–5 min; REQ-ENE-04 Profil mit 1 min, zusätzlich 2/5 min ausweisen |
| F-03 Dünger/Salz | wichtig | ✅ | neu REQ-MES-11 (Soll) |
| F-04 Prüfmethode Temperatur | wichtig | ✅ | REQ-MES-05 |
| F-05 Drift-Prüfung | wichtig | ✅ | REQ-MES-06 neu formuliert, Muss |
| F-06 NTP-Widerspruch, Zeit nach Stromausfall | wichtig | ✅ | REQ-SYS-01, REQ-GW-09, OP-08 |
| F-07 Puffer vs. Zeitgenauigkeit | wichtig | 🔶 | REQ-SYS-07 (±2 min/14 d, ±5 min/60 d, relative Zeit), Puffer 60 statt vorgeschlagenen 30 Tagen (FE-12: kostet praktisch nichts) |
| F-08 „pessimistisch“ beziffern | wichtig | ✅ | neu REQ-ENE-08; REQ-ENE-05 (Last + Ereigniszählung) |
| F-09 5 Jahre Speicher | wichtig | 🔶 | REQ-GW-01: 2 Jahre voll Muss, 5 Jahre Soll (verdichtet/Backup). „Dauerhaft“ aus dem Auftrag bleibt durch Backup gewahrt. |
| F-10 Lastfälle Sonde | wichtig | ✅ | REQ-MECH-10 (4 Lastfälle, Lagerung, Vorstechen) |
| F-11 Netzwechsel, Gateway-Ersatz, 2. Gateway | wichtig | ✅ | UC-13, UC-14, REQ-GW-06, -10, REQ-SYS-11 |
| F-12 Design fehlt | wichtig | ✅ | neu Kap. 9 REQ-DES-01..04 |
| F-13 Sonnentemperatur 65 °C | wichtig | ✅ | RB-03, REQ-MECH-12 (≥ 70 °C formstabil), REQ-TMP-01 |
| F-14 Brand messbar, Verschluckschutz | wichtig | 🔶 | siehe S-W05 und S-K03 |
| F-15 4 Lagen vorweggenommen | klein | 🔶 | Wortlaut des Auftraggebers („möglichst“) beibehalten, Entscheid ausdrücklich nach Vergleich (REQ-MECH-04) |
| F-16 Messgrösse Reichweite | klein | ✅ | REQ-RF-02 |
| F-17 Messvolumen messbar | klein | ✅ | REQ-MES-08 |
| F-18 Rückverfolgungslücken | klein | ✅ | RB-09, REQ-MECH-01, -11, REQ-ENE-01, REQ-GW-07 |
| F-19 Update Gateway/PWA | klein | ✅ | REQ-GW-11, UC-14 |
| F-20 weitere Szenarien | klein | ✅ | UC-15, UC-16, REQ-MES-12, REQ-MECH-08, -18 |
| F-21 mehrfarbige LED | klein | ✅ | REQ-UI-01 |

## Firmware/Energie (`phase1_requirements_firmware-energie.md`)

| Befund | Stufe | Antwort | Umsetzung |
|---|---|---|---|
| FE-01 Annahmen beziffern, Markenzellen | wichtig | ✅ | REQ-ENE-08 |
| FE-02 Ruhestrom dominiert | kritisch | ✅ | neu REQ-ENE-09 (≤ 3 µA Schlaf, ≤ 8 µA Mittel, gemessen) |
| FE-03 1 min als Muss, Scan-Variante ausschliessen | wichtig | 🔶 | Profil rechnet mit 1 min (REQ-ENE-04). **Muss bleibt 5 min**, weil der Auftraggeber ausdrücklich „ein paar Minuten“ akzeptiert (CLIENT_INPUT). Ausschluss der Scan-Variante ist ein Lösungsentscheid → Phase 2. |
| FE-04 32-kHz-Quarz Muss | wichtig | 🔶 | Anforderung als Genauigkeit formuliert (REQ-SYS-07), nicht als Bauteil; Quarz als Lösungshinweis für Phase 2 notiert. |
| FE-05 Gateway-Uhr 23 ppm | wichtig | ✅ | REQ-GW-09 ±2 min/Monat |
| FE-06 Programmieren lädt Zelle | wichtig | ✅ | REQ-FW-06, REQ-SAF-CC-03 |
| FE-07 Spannungseinbruch beziffern | wichtig | ✅ | REQ-ENE-06 |
| FE-08 ESP32 an Knopfzelle unmöglich | wichtig | 🔶 | über REQ-ENE-09 abgedeckt (Ruhestrom ≤ 3 µA) statt Chipvorgabe |
| FE-09 LiPo-Schutzschaltung Ruhestrom | klein | ✅ | REQ-ENE-09 |
| FE-10 OTA Batterieschwelle, Flash | klein | ✅ | REQ-FW-02, -03 |
| FE-11 keine periodischen Blinks | klein | ✅ | REQ-UI-03 |
| FE-12 Puffer 60 Tage | klein | ✅ | REQ-LOG-01 |
| FE-13 Intervall 1–96/Tag | klein | ✅ | REQ-SYS-04 |
| FE-14 adaptive Sendeleistung | klein | ✅ | REQ-RF-03 |
| FE-15 Ladungszählung | klein | ✅ | REQ-ENE-05 |
| FE-16 Profil ergänzen | klein | ✅ | REQ-ENE-04 |

## Hinweis zu Datenblättern
Der Energieprüfer hat für seine Machbarkeitsrechnung Datenblätter in den Scratchpad geladen
(teils von Händler-Mirrors). Diese gelten **nicht** als Projektdokumentation. In Phase 2 werden die
Datenblätter der tatsächlich betrachteten Bauteile von den Herstellern bezogen, unter
`docs/datasheets/` abgelegt und in `INDEX.csv` eingetragen.

## Runde 2 (2026-11-06) – Antworten

| Befund | Quelle | Antwort | Umsetzung (v0.3) |
|---|---|---|---|
| S-K04 Bestehenskriterium Ladeport | Sicherheit | ✅ | REQ-SAF-LI-08: 5-V-Senke, 3 Netzteile inkl. PC-Port und PD/QC, Nasstest-Kriterien |
| S-W05 Brandkriterium | Sicherheit | ✅ | REQ-SAF-01: Prüfung bei 20–25 °C, Zelle: 65 °C + ΔT ≤ Datenblatt, Gehäuse: 65 °C + ΔT ≤ HDT − 10 K; REQ-MECH-12 HDT ≥ 80 °C |
| R2-W01 NTC offen/kurz, Port-Kurzschluss | Sicherheit | ✅ | REQ-SAF-LI-02, Einzelfehlerliste REQ-SAF-01 |
| R2-W02 Gegenmassnahme LiPo bei 65 °C | Sicherheit | ✅ | REQ-SAF-LI-09 konstruktiv, sonst Akku unzulässig |
| R2-L01 I²C-Lade-IC Hardwaregrenzen | Sicherheit | ✅ | REQ-SAF-LI-07 |
| R2-L02 Schraube unverlierbar, Moment/Winkel | Sicherheit | ✅ | REQ-SAF-CC-04 (Werte in Phase 4 mit Quelle) |
| R2-L03 Warnsymbol | Sicherheit | ✅ | REQ-SAF-CC-04 |
| R2-L04 Ladehinweise | Sicherheit | ✅ | REQ-SAF-DOC-01 |
| F-01 Rest: Sicherheitsbezug ausserhalb Kap. 6 | Red Team | ✅ | Kap. 1.2 nennt REQ-FW-04, RF-05, RF-06 |
| N-01 ENE-09 macht Soll zum Muss | Red Team | ✅ | ENE-09 auf Werkseinstellung bezogen, SYS-05 ergänzt |
| N-02 SAF-01 vs. MECH-12 | Red Team | ✅ | identisch mit S-W05 gelöst |
| N-03 Temperaturumfang, CC-Gegenstück, Sonnenprofil | Red Team | ✅ | RB-03 präzisiert inkl. Sonnenprofil (ANNAHME), neu REQ-SAF-CC-05, ENE-04 |
| N-04 Zeitreferenz/Temperatur | Red Team | ✅ | REQ-SYS-07 |
| N-05 Abschaltspannung | Red Team | ✅ | REQ-ENE-06 (2.0 V an Zellklemme, ANNAHME) |

Damit sind alle Befunde beantwortet. Gemäss Prüfregel (max. 2–3 Runden) erfolgt keine weitere
Agentenrunde; die Aufhebung von Veto S-K04 bestätigt der Orchestrator anhand der wörtlich
übernommenen Bedingungen der Sicherheitsrolle (siehe Bericht Sicherheit, Runde 2).
