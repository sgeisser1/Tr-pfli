# Prüfbericht Phase 2 – Technische Konzepte, Fokus Sicherheit

| | |
|---|---|
| Geprüft | `docs/concepts/CONCEPTS.md` v0.1, `docs/concepts/bom/bom_{A,A2,B,C}.csv`, `docs/concepts/research_energie.md`, Gateway-Teil aus `research_gateway.md` (Kap. 2.5, 3, 4) |
| Grundlagen | `REQUIREMENTS.md` v1.0 (Kap. 6, RB-03, REQ-FW-04/06, REQ-ENE-07), `phase1_requirements_sicherheit.md` |
| Prüfer | Sicherheits-Agent (mit Veto), frischer Kontext |
| Datum | 2026-11-06 |
| Ergebnis | **1 kritisch (VETO), 7 wichtig, 7 klein.** Die Empfehlung A ist aus Sicherheitssicht richtig. Der Ladeschutz der Knopfzelle (REQ-SAF-CC-03) ist im Konzept aber falsch begründet und gilt in der Vergleichsmatrix zu Unrecht als erfüllt. |

Stufen: **kritisch** = blockiert die Freigabe (Veto), **wichtig** = vor bzw. in Phase 3 einarbeiten oder
begründet ablehnen, **klein** = Verbesserung. Seitenangaben = PDF-Seite.

## 1 Gesamturteil

- **Empfehlung A (CR2450N) ist richtig (REQ-SAF-03).** Die Primärzelle hat keinen Ladepfad, keinen
  VBUS und kein Aufblährisiko. Laut Datenblatt ist sie bis 85 °C spezifiziert, eine Rücksprache mit
  Renata braucht es erst über 70 °C (`Renata_CR2450N_Datasheet_Rev08.pdf`, S.1, Fussnote *). Die
  Reihenfolge A > B > C stimmt: B hat einen Eigenbau-Bootloader (REQ-FW-04), die CR2032 MFR verlangt
  schon über 60 °C eine Rücksprache (`Renata_CR2032MFR_Datasheet_Rev07.pdf`, S.1), die Kontakte sind
  aus SnSb. C ist nicht zulässig (Kap. 4).
- **Sicherheitsbewertung je Konzept:** Die Bewertungen von B und C sind korrekt und vollständig genug.
  Bei A sind drei Punkte zu optimistisch: REQ-SAF-CC-03 (falsche Topologie, **VETO**),
  REQ-SAF-01 (a) (Temperaturreserve im Fehlerfall nur 5 K) und REQ-FW-04 (Anti-Rollback auf dem
  CC2340 nicht belegt). REQ-SAF-05 (getrenntes Fach) ist nur als Absicht genannt, eine Konstruktion
  fehlt.
- **Veto S-K04 aus Phase 1** (Ladeport, nur [LI]) ist gegenstandslos, wenn C wegfällt.

## 2 Befunde

### Kritisch

**S2-K01 · kritisch · REQ-SAF-CC-03, REQ-SAF-06, REQ-FW-06 · Konzept A (und B)**
**VETO:** Die „Rückstromsperre Programmierung“ (CONCEPTS.md Kap. 1 und 2.6, Matrix 6.1 „✔ konstruktiv + D + R“)
verhindert das Laden der Zelle nicht.

*Begründung:*
1. **Die Diode zeigt in die falsche Richtung.** Der Pfad VPROG → 1N4148WS → 100 Ω → VDD leitet **zur Zelle hin**.
   Der AO3401A ist eingeschaltet und leitet in beide Richtungen (`research_energie.md` E-06). Damit liegt die
   Zelle direkt hinter VDD. Die Diode schützt nur den Adapter vor der Zelle. In Richtung Zelle wirkt sie bloss
   als Spannungsversatz von VF (≤ 0.715 V bei 1 mA, ≤ 0.855 V bei 10 mA; ein Minimalwert fehlt,
   `CJ_1N4148WS_Datasheet_LCSC-2018-10.pdf`, S.1). Es bleibt eine einzige echte Begrenzung, nämlich 100 Ω.
   Das widerspricht der Anforderung „zwei unabhängige Rückstrombegrenzungen“.
2. **Ladestrom in die Zelle, Rechnung** (VF 0.6 V **ANNAHME**, Zelle am Entladeende 2.0 V; frisch ≈ 3.2 V, dann kleiner):
   | Fall | Strom in die Zelle |
   |---|---|
   | Adapter 3.3 V, Diode intakt | (3.3 − 0.6 − 2.0) / 100 Ω ≈ **7 mA** |
   | Adapter 3.3 V, Diode kurzgeschlossen (Einzelfehler) | (3.3 − 2.0) / 100 Ω ≈ **13 mA** |
   | Adapter auf 5 V gesteckt (häufig bei billigen USB-UART-Adaptern), Diode intakt | (5 − 0.85 − 2.0) / 100 Ω ≈ **22 mA**; VDD ≈ 4.2 V liegt **über VDDS abs. max 4.1 V** (`TI_CC2340R5_Datasheet_SWRS272F.pdf`, S.18, Tab. 7.1) |
   | UART TX 3.3 V / 5 V über 1 kΩ und die ESD-Diode des Pins nach VDD (nur eine Begrenzung) | ≈ 0.8 mA / ≈ 2.5 mA |
   | BOOT-Trigger-Pad, nRST-Pad | ohne Serienwiderstand (bom_A.csv hat nur den nRST-Pull-up 100 kΩ) → keine Begrenzung |
3. **Kein Grenzwert vorhanden.** Renata gibt für die CR2450N keinen zulässigen Rückstrom an
   (`Renata_CR2450N_Datasheet_Rev08.pdf`, S.1), die Sicherheitsrichtlinie verweist nur auf „UL standard for diode
   use“ (`Renata_3VLithium_SafetyGuidelines.pdf`, S.1). Der Nachweis „Rückstrom ≤ Herstellerangabe“ ist damit
   im Moment nicht führbar.
4. **Die konstruktive Barriere ist nicht belegt.** Laut Konzept sind die Pads „nur bei entnommener Zelle zugänglich“.
   Der Halter BS-24-B4AA016 hat aber ein geschlossenes LCP-Gehäuse mit Boden (32.8 × 16 mm, H 7.5 mm,
   `MYOUNG_BS-24-B4AA016_Drawing_A0.pdf`, S.1, Schnitt). Pads unter der Zelle sind dort nicht erreichbar, Pads
   neben dem Halter dagegen auch bei eingesetzter Zelle. Wo die Pads liegen sollen, ist nirgends gezeigt.

*Vorschlag (eine der Lösungen, Entscheid Elektronik):*
- **Programmieradapter als Dummy-Zelle:** Versorgung nur über die Halterkontakte, kein VPROG-Pad. Zelle und
  Adapter schliessen sich so physisch aus (Barriere 1). Die UART-, BOOT- und nRST-Pads kontaktiert der
  Dummy-Adapter (z. B. Federstifte). Barriere 2: In jeder Signalleitung ein Serienwiderstand, so bemessen, dass
  bei 5.5 V, Zelle 2.0 V und kurzgeschlossenem Element der Strom ≤ Renata-Wert bleibt (z. B. ≥ 10 kΩ,
  **ANNAHME**, Baudrate prüfen).
- Alternative: ein echtes Sperrglied **im Zellpfad**, z. B. eine Schottky-Diode in Serie zur Zelle. Sie kostet
  aber ≈ 0.3 V und kollidiert mit der Abschaltschwelle 2.0 V (REQ-ENE-06) und mit VDDS min 1.71 V. Ein
  Load-Switch mit Rückstromsperre wäre nur mit lokalem Datenblatt und Ruhestromnachweis zulässig.
- Renata schriftlich nach dem zulässigen Rückstrom (Dauer und Fehlerfall) für die CR2450N fragen (OP-K7 erweitern).
- Programmieranleitung: Adapter nur mit 3.3 V, Zelle entnommen.

*Aufhebung des Vetos:* Das Konzept (spätestens der Schaltplan in Phase 3) zeigt für **jede** externe Quelle
(VPROG bzw. Halterkontakte, UART RX/TX, BOOT, nRST, Messbrücke nach S2-W04) zwei unabhängige Massnahmen.
Dazu kommt eine Worst-Case-Rechnung (Quelle 5.5 V, Zelle 2.0 V, ein Element kurzgeschlossen) mit Ergebnis
≤ zulässigem Rückstrom laut Renata. Die Matrix 6.1 ist korrigiert, und im Testplan steht die Rückstrommessung
mit überbrückter Diode bzw. überbrücktem Widerstand. Die Konzeptwahl A selbst blockiert das Veto nicht.
Es blockiert die Freigabe der Versorgungs- und Programmierschaltung.

### Wichtig

**S2-W01 · REQ-SAF-01 (a), REQ-SAF-CC-05 · A** – Reserve im Fehlerfall nur 5 K.
*Begründung:* REQ-SAF-01 (a) verlangt: 65 °C + Erwärmung der Zelle durch den Fehler ≤ zulässige Zelltemperatur.
Gilt die Rücksprachegrenze von 70 °C (`Renata_CR2450N_Datasheet_Rev08.pdf`, S.1) als zulässig, bleiben **5 K**.
Ein Kurzschluss im Versorgungspfad (z. B. ein gerissener MLCC, S2-W02) erwärmt die Zelle über ihren
Innenwiderstand. Der Satz „Strom durch Zellinnenwiderstand begrenzt“ (CONCEPTS 2.6) ist kein Nachweis.
*Vorschlag:* Renata fragen, ob 65 °C im Dauerbetrieb zulässig sind und welche Temperatur im
Kurzschlussfall erreicht wird. Bestätigt Renata 85 °C als zulässige Grenze, bleiben 20 K Reserve. Sonst
Kurzschlussversuch an der Zelle bei 20–25 °C mit Messung von ΔT_Zelle (PROTOTYP-PRÜFUNG) und FMEA-Eintrag.
Matrix 6.1: „~“ statt „✔“, bis Messung oder Antwort vorliegen.

**S2-W02 · REQ-SAF-01, neue Gefährdung durch Bauteilwahl** – 2 × 100 µF in 1206 (C15008) direkt an der Zelle,
auf einer langen Sondenplatine (Einstecklast 50 N, Fall 1 m, REQ-MECH-10). Ein Biegeriss im MLCC ist ein
typischer Ausfall: Er bildet einen niederohmigen Kurzschluss, die ganze Zellenergie fliesst in eine heisse
Stelle im Kopf.
*Vorschlag:* Puffer im steifen Kopfbereich platzieren, weit weg von Sondenwurzel und Schraubdom, mit der
Längsachse parallel zur Biegelinie. Prüfen, ob eine Variante mit Soft-Termination verfügbar ist (mit
Datenblatt). FMEA-Eintrag „MLCC-Kurzschluss“ mit Test nach REQ-SAF-01.

**S2-W03 · REQ-SAF-05 · A** – Ein getrenntes Fach ist nur als Absicht genannt („konstruktiv anspruchsvoll“).
Halter, Pads und Elektronik sitzen auf derselben Platine, und die Dichtung läuft über die Leiterplatte.
Wasserwege: (1) ungefüllte Vias im Fach, bei A-H (Halter hinten) zwingend vorhanden, Epoxy-Vias kosten
+20.3 USD; (2) Kapillarwirkung entlang der FR4-Kante unter der Dichtung; (3) Dichtung über Leiterbahnen und
Lötstopplack. Im Fach liegen zudem Pads unter Spannung (VDD, UART). Bei Wasser im Fach gibt es Elektrolyse
und Korrosion.
*Vorschlag:* In Phase 3/4 eine Skizze der Dichtlinie mit Regeln: keine Vias und Bauteile in der Dichtzone,
Vias im Fach gefüllt und gedeckelt oder ganz vermeiden, Platinenkante vollständig im Elektronikraum oder
umlaufend abgedichtet. Flutungstest beider Räume (24 h) mit Messung des Zellstroms im Testplan.

**S2-W04 · REQ-SAF-CC-03, REQ-ENE-07 · A** – Messbrücke: Die Pads auf der FET-Seite führen ohne jede Begrenzung
an die Zelle. Wird dort eine Laborspeisung angeschlossen, lädt sie die Zelle. REQ-SAF-CC-03 nennt den Messpunkt
ausdrücklich.
*Vorschlag:* Die Brücke als reinen Strommesspunkt bezeichnen (Silkscreen „nur Amperemeter“), Pads im Fach
platzieren. Speisung nur über den Dummy-Adapter (S2-K01), Messanleitung entsprechend. In den Veto-Nachweis
aufnehmen.

**S2-W05 · REQ-FW-04 · A** – Matrix 6.1 bewertet REQ-FW-04 mit „✔“, belegt ist aber nur die Signatur (MCUboot
ECDSA). Anti-Rollback auf dem CC2340 (Hardware-Zähler bzw. Overwrite-Modus mit Rückfall nach REQ-FW-03) ist
**nicht belegt** (OP-K8). Der CC2340 hat nur AES- und RNG-Hardware (`TI_CC2340R5_Datasheet_SWRS272F.pdf`, S.45),
ECDSA läuft also in Software (Bootzeit und Energie). Der ROM-Seriell-Bootloader (S.45;
`TI_CC23xx_HWDesignGuide_SWRA834A.pdf`, S.6–7) ist ein **unsignierter** Programmierweg. Er ist nur mit Werkzeug
erreichbar, das Restrisiko ist aber nicht dokumentiert.
*Vorschlag:* „~“ bis zum Beleg. In Phase 3 die MCUboot-Konfiguration nachweisen (Signaturtyp, Downgrade-Schutz,
Schreibschutz des Bootloaders). Entweder den ROM-Bootloader per CCFG sperren (**ANNAHME**, Beleg nötig) oder das
Restrisiko „physischer Zugang = Neuprogrammierung“ dokumentiert akzeptieren.

**S2-W06 · REQ-SAF-CC-03 sinngemäss, REQ-SAF-CC-04, REQ-SAF-DOC-02 · Gateway** – „DS3231-Modul gepuffert,
Baustein Phase 3“. Viele billige DS3231-Module (Typ ZS-042) haben eine **Ladeschaltung** (Widerstand + Diode von
VCC) für eine LIR2032 und werden mit einer **CR2032-Primärzelle** geliefert. Das ist ein Ladepfad in eine
Primärzelle (**ANNAHME**, verbreitet, für das konkrete Modul mit Schaltplan prüfen). Dazu sitzt im Gateway eine
lose Knopfzelle (Verschlucken). Das XIAO ESP32-S3 Plus hat Akku-Ladepads (**ANNAHME**, Board-Doku nicht lokal).
*Vorschlag:* Nur eine RTC ohne Ladepfad zur Primärzelle wählen (Schaltplan lokal ablegen) oder einen
Superkondensator bzw. eine ML-Zelle mit passendem Lader verwenden. Die Knopfzelle im Gateway-Gehäuse nur mit
Schraube zugänglich machen. Anleitung: keinen Akku an das Board anschliessen. Netzteil RPi 15 W USB-C (geprüft,
CE) ist in Ordnung (REQ-SAF-DOC-02).

**S2-W07 · REQ-SAF-NET-03/-04, REQ-GW-11 · Gateway** – Im Gateway-Flash liegen Firmen-WLAN-Zugangsdaten,
Sensorschlüssel, TLS-Serverschlüssel und Admin-Hash. Ohne Flash-Verschlüsselung kann sie jeder mit physischem
Zugang über USB auslesen. Gateway-Updates über die PWA sind nicht als signiert festgelegt. Das ESP32-S3 bietet
Secure Boot (RSA-PSS) und Flash Encryption (`Espressif_ESP32-S3_Datasheet_v2.2.pdf`, S.2, S.48).
*Vorschlag:* Phase 3 entscheidet und dokumentiert: (a) signierte Gateway-Images (Secure Boot v2 oder Prüfung
signierter Apps), (b) Flash- bzw. NVS-Verschlüsselung, mit Abwägung gegen irreversible eFuses und
Wiederherstellung. Mindestens: Das Update über die PWA nimmt nur signierte Images an, und der Signierschlüssel
liegt nicht auf dem Gateway.

### Klein

| ID | REQ | Befund | Vorschlag |
|---|---|---|---|
| S2-L01 | SAF-CC-01 | Der AO3401A **wirkt** als Verpolschutz, wenn er so eingebaut ist: Drain = Zelle+, Source = VDD, Gate = GND. Verpolt sind V_GS ≈ 0 und die Body-Diode gesperrt; I_DSS ≤ 1 µA (25 °C) bzw. 5 µA (55 °C), I_GSS ≤ 100 nA; V_GS im Betrieb −3 V bei ±12 V abs. max (`AOS_AO3401A_Datasheet_Rev3.1.pdf`, S.1–2). Über 24 h ist das unkritisch. Bei 65 °C ist I_DSS nicht spezifiziert. Ist der FET verkehrt herum bestückt (Source an der Zelle), leitet die Body-Diode, und der Schutz fehlt. Beim BS-24 liegt der Minus-Federkontakt in der Mitte des Bodens (Zeichnung „NEG“). Eine verkehrt eingelegte Zelle hat dann vermutlich gar keinen Minuskontakt. | Pinbelegung im Schaltplan festhalten und im Review prüfen. Gate direkt an GND ist in Ordnung. Verpoltest 24 h (PROTOTYP-PRÜFUNG), dazu das Kontaktbild bei verkehrt eingelegter Zelle. |
| S2-L02 | SAF-CC-02 | Halter: Die Kontakte sind nur mit **Au 1 µ″** (≈ 0.025 µm) über Ni vergoldet, also kein Hartgold. LCP UL94V-0, −25…85 °C, 30 mΩ (`MYOUNG_BS-24-B4AA016_Drawing_A0.pdf`, S.1). Die Zelle wird seitlich eingeschoben, ein Herausfallen verhindern nur Federkraft und Deckel. Ein Kurzschluss im Halter ist wegen der Führung unwahrscheinlich. | Gilt im abgedichteten Fach als ausreichend. Falltest 1 m mit Zelle, schräges Einsetzen testen. Der Deckel drückt mit einer Noppe auf den Pluspol. Die Schraubenspitze darf nicht in den Zellraum ragen. |
| S2-L03 | SAF-CC-04 | Der Deckel mit unverlierbarer Schraube und Warnsymbol ist richtig gewählt. Die Ausführung der Unverlierbarkeit (FDM), die Kopfform und die Werte nach UL 4200A sind weiterhin **ANNAHME**. | In Phase 4 belegen. Falltest mit geschlossenem Deckel. |
| S2-L04 | SAF-NET-04 | Das HTTPS-Konzept ist schlüssig: Einmal-CA mit Name Constraints, CA-Schlüssel nach dem Signieren gelöscht, CSR vom Gateway (CONCEPTS 5.2; `research_gateway.md` 4). Der Rückfall „IP-SAN bzw. IT-DNS-Name“ widerspricht `excluded IP`. Ein gelöschter Schlüssel auf einer SSD ist nicht sicher gelöscht. | Den CA-Schlüssel nur im RAM bzw. auf tmpfs erzeugen. Für den Rückfall eine neue Einmal-CA mit exakt einem Namen bzw. einer IP/32 erstellen, nie eine Domain oder einen ganzen Bereich. Erneuerung nach 825 Tagen in der Anleitung beschreiben. |
| S2-L05 | RB-03 | Renata empfiehlt allgemein „do not expose … to high temperatures, moisture or direct sunlight“ (`Renata_3VLithium_SafetyGuidelines.pdf`, S.1), die Fensterbank widerspricht dem. | Helle Gehäusefarbe, Hinweis in der Anleitung. In die Anfrage an Renata (OP-K7) aufnehmen: Dauerbetrieb bei 65 °C, zulässiger Rückstrom, Kurzschlusstemperatur. |
| S2-L06 | – | Die Rückfalloption „A-32“ (CR2032 + Clip-Halter TE) bringt bekannte Risiken mit: schräger Sitz bzw. Kurzschluss am Clip, Minuspad auf der Leiterplatte (ENIG), Rücksprache ab 60 °C. | Vor einer Verwendung eine eigene Sicherheitsprüfung. |
| S2-L07 | – (C) | Nur falls C je wieder aufgenommen wird: RISET 10 kΩ ergibt ≈ 54 mA, K_ISET ist aber erst ab 60 mA spezifiziert (`TI_BQ21040_Datasheet_RevD.pdf`, S.5). BQ29700 V_UVP 2.8 V liegt unter der Zell-Abschaltspannung 3.0 V (`TI_BQ2970_Datasheet_RevI.pdf`, S.3). SMAJ20A V_C 32.4 V liegt über BQ21040 IN abs. max 30 V (`Littelfuse_SMAJ_Datasheet.pdf`, S.2). | Erst bei einer Wiederaufnahme lösen. |

## 3 Prüffragen im Einzelnen

**1. Sicherheitsbewertung und Empfehlung:** siehe Kap. 1. Die Empfehlung A ist nach REQ-SAF-03 richtig. Die
Matrix 6.1 ist zu korrigieren: SAF-CC-03 ✘ bis S2-K01, SAF-CC-05/SAF-01 ~ (S2-W01), FW-04 ~ (S2-W05).

**2. Konzept A im Detail**

| Punkt | Urteil |
|---|---|
| Verpolschutz AO3401A | wirkt bei richtiger Pinbelegung, Leckstrom unkritisch (S2-L01) |
| Ladeschutz CC-03 (Pads, UART-Bootloader, Messpunkt) | **nicht erfüllt**, VETO S2-K01, S2-W04 |
| Halter C964809 | geeignet; Kurzschluss unwahrscheinlich, Herausfallen nur mit Deckel ausgeschlossen, Kontakte nur mit Goldflash (S2-L02) |
| Verschluckschutz | richtig gewählt, Ausführung in Phase 4 (S2-L03) |
| 65 °C (CC-05) | im Datenblattbereich; Fehlerreserve 5 K ungeklärt (S2-W01) |
| Wasser (SAF-05) | berücksichtigt, aber nicht konstruiert (S2-W03) |

**3. Gateway:** Das Netzteil ist in Ordnung. Das HTTPS-/CA-Konzept erfüllt REQ-SAF-NET-04 (S2-L04). Die
OTA-Signatur ist für den Sensor mit MCUboot schlüssig, solange der Signierschlüssel nur auf dem PC liegt und
das Gateway die Signatur zusätzlich prüft. Anti-Rollback und der ROM-Bootloader sind offen (S2-W05). Neu sind
die RTC-Ladeschaltung bzw. die Knopfzelle im Gateway (S2-W06) und der Schutz der Gateway-Firmware und der
Zugangsdaten (S2-W07).

**4. Konzept C und REQ-SAF-LI-09: bestätigt.** Für den Renata ICP401230UPR gelten: Entladen −20…60 °C,
Lagern −20…45 °C, Laden 0…45 °C (`Renata_ICP401230UPR_Datasheet_V02.pdf`, S.1). Bei 65 °C Kopftemperatur
(RB-03) liegt die Lagergrenze 20 K und die Entladegrenze 5 K darunter. Eine passive konstruktive Massnahme
(Wärmeschutz 1.5 mm) verzögert die Erwärmung nur, im Gleichgewicht senkt sie die Temperatur nicht um 20 K
(**ANNAHME** physikalisch, kein aktiver Kühlpfad im Kopf). C ist deshalb **nicht zulässig**, es sei denn, OP-04
misst eine Kopftemperatur ≤ 45 °C. Dann wäre aber RB-03 selbst zu ändern.

**5. Neue Gefährdungen durch die Bauteilwahl:** Diode in Durchlassrichtung zur Zelle und 5-V-Adapter über VDDS
abs. max (S2-K01), MLCC-Biegeriss (S2-W02), Vias und Platinenkante als Wasserweg (S2-W03), Messbrücke als
Speisepunkt (S2-W04), unsignierter ROM-Bootloader (S2-W05), RTC-Ladeschaltung bzw. Knopfzelle im Gateway
(S2-W06), auslesbare WLAN-Zugangsdaten (S2-W07).

## 4 Für Testplan (REQ-DOC-03) und FMEA vormerken

Rückstrom je Pad mit überbrückter Diode bzw. überbrücktem Widerstand bei 3.3 V und 5 V (S2-K01). Kurzschluss
im Versorgungspfad mit Messung von ΔT_Zelle (S2-W01/W02). Flutung von Fach und Elektronikraum getrennt, mit
Zellstrom (S2-W03). Verpolung 24 h und Kontaktbild (S2-L01). Falltest 1 m mit Zelle und Deckel (S2-L02/L03).
Gateway: Ladepfad der RTC messen (S2-W06), Portscan, Update mit unsigniertem Image wird abgelehnt (S2-W07).

## Runde 2

| | |
|---|---|
| Geprüft | `docs/concepts/CONCEPTS.md` v0.2 (Kap. 0, 1, 2.1–2.2, 2.4, 2.7–2.10, 2A, 5, 6.1, 7, 8), `docs/reviews/phase2_concepts_response.md` |
| Neue Quellen (lokal abgelegt) | `docs/references/Panasonic_LithiumHandbook_DesignTips_LiThb-BSG_2005.pdf` (Panasonic Lithium Handbook, Abschnitt „Reverse current blocking diode“, S.1; Quelle master-instruments.com.au, Abruf 2026-11-06); `docs/references/Maxell_CR_Warnings_12e_2012.pdf` (Maxell „CR Coin Type Lithium Manganese Dioxide Battery – Warnings“, S.2 „Circuit Design for Back-up Use“; Quelle maxell.com.tw, Abruf 2026-11-06) |
| Prüfer | Sicherheits-Agent (mit Veto) |
| Datum | 2026-11-06 |
| Ergebnis | **VETO S2-K01 aufgehoben (mit Auflagen R2-A1…A4).** W01–W07 und L01–L06 umgesetzt, L07 zurückgestellt (akzeptiert). A-32 aus Sicherheitssicht zulässig, A bleibt leicht vorzuziehen. Neu: 2 wichtig, 3 klein. |

### R2.1 VETO S2-K01 – Prüfung der Aufhebungsbedingung

**(a) Zwei unabhängige Massnahmen je externe Quelle** (Schaltung CONCEPTS 2.1, 2.2, 2.7):

| Externe Quelle | Massnahme 1 | Massnahme 2 | Urteil |
|---|---|---|---|
| VPROG-Pad | entfällt | – | Quelle beseitigt ✔ |
| Messbrücke (S2-W04) | entfällt, Mess-Zwischenadapter im Halter | – | Quelle beseitigt ✔ |
| nRST-, BOOT-Pad | entfallen (Reset über Aus/Ein, Trigger = Taster DIO21) | – | Quelle beseitigt ✔ |
| Halterkontakte (Dummy-Zellen-Adapter) | Adapter **ersetzt** die Zelle im selben Halter: Zelle ist nicht im Stromkreis | AO3401A sperrt bei verpoltem Adapter | ✔ – kein Ladepfad möglich, solange der Adapter einteilig ist (R2-A2) |
| RX, TX, SWDIO, SWDCK | 100 kΩ | 100 kΩ (zweites, getrenntes Bauteil) | ✔ – Einzelfehler (ein R kurz) lässt 100 kΩ |

Die Pads bleiben bei offenem Deckel und eingesetzter Zelle von aussen erreichbar (z. B. Klemmprüfspitzen
eines fremden USB-UART-Adapters). Die Dummy-Zelle schliesst also nur **ihren eigenen** Speisepfad aus,
nicht den Anschluss fremder Quellen an die Signalpads. Das ist zulässig, weil die Pads selbst zwei
Begrenzungen haben. Gleichzeitiges Stecken von Zelle und Dummy-Adapter ist beim BS-24 (ein Zellschacht)
nicht möglich, sofern Speisekörper und Federstiftkopf **ein starres Teil** sind.

**(b) Worst-Case nachgerechnet** (5.5 V am Pad, Zelle 2.0 V, ESD-Diode 0 V, Gerätestrom 0 – alles konservativ):
1 Pad 3.5 V / 200 kΩ = **17.5 µA**; ein R kurz 3.5 V / 100 kΩ = **35 µA**; 4 Pads, ein R kurz
3 × 17.5 + 35 = **87.5 µA**. Werte der Antwort bestätigt. Zusatz: Zelle ganz entladen (0 V, Gerät
abgestellt) ergibt 55 µA bzw. 3 × 27.5 + 55 = 137.5 µA – ändert das Urteil nicht. Die I²C-Pull-ups
(4.7 kΩ an TMP_PWR) und der TMP1075 liegen hinter den 200 kΩ und öffnen keinen Nebenpfad.
Realfall 3.3-V-Adapter, Zelle 3.0 V: (3.3 − 3.0)/200 kΩ ≈ 1.5 µA.

**(c) Matrix 6.1** auf „~“ korrigiert ✔. **(d) Testplan** (Rückstrom je Pad bei 3.3/5 V, überbrückter
Einzelwiderstand) in 2.7 genannt ✔.

**(e) Grenzwert ohne Renata-Angabe.** Zwei Hersteller von Li/MnO₂-Knopfzellen geben allgemeine Grenzen an:
- Maxell: Ladung durch Leckstrom **≤ 1 % der Nennkapazität**; Strom bei Ausfall der Sperrdiode höchstens
  **15 mA (CR2450)** bzw. **10 mA (CR2032)** (`Maxell_CR_Warnings_12e_2012.pdf`, S.2, Tabelle „Maximum Current“).
- Panasonic: gesamte Ladung über die Nutzungsdauer **≤ 3 %** der Nennkapazität bei Knopfzellen; Diode **und**
  Schutzwiderstand in Serie verlangt (`Panasonic_LithiumHandbook_DesignTips_LiThb-BSG_2005.pdf`, S.1).

**Vorgeschlagene Grenze** (bis zur Renata-/Panasonic-Antwort, jeweils die strengere Maxell-Regel):
**Fehlerfall ≤ 10 mA** (CR2032-Wert, gilt damit für A und A-32) **und Ladung ≤ 1 % C_nenn über die Lebensdauer**
(CR2450N 540 mAh → 5.4 mAh; CR2032 225 mAh → 2.25 mAh). **ANNAHME:** Übertragbarkeit der Maxell-/Panasonic-
Werte auf Renata CR2450N (gleiche Chemie und Bauform).

| Fall | Strom | Abstand zu 10 mA | Zeit bis 1 % C (CR2450N / CR2032) |
|---|---|---|---|
| 1 Pad, intakt | 17.5 µA | × 570 | 309 h / 129 h |
| 1 Pad, R kurz | 35 µA | × 285 | 154 h / 64 h |
| 4 Pads, R kurz | 87.5 µA | × 114 | 62 h / 26 h |

Fehlbedienung (fremder Adapter an den Pads bei eingesetzter Zelle) dauert realistisch Minuten bis Stunden,
nicht Tage. Die Grenze ist eingehalten.

**Urteil: VETO S2-K01 aufgehoben.** Die Renata-Antwort (OP-K7) bleibt nötig, blockiert aber nicht mehr.
Auflagen (prüft die Sicherheit im Schaltplan-Review Phase 3):
- **R2-A1:** CONCEPTS/Schaltplan übernehmen die Grenze (≤ 10 mA Fehlerfall, ≤ 1 % C Ladung) mit Quellen.
  Nennt Renata bzw. Panasonic einen strengeren Wert, die Rechnung wiederholen.
- **R2-A2:** Dummy-Adapter einteilig (Zellkörper + Federstiftkopf starr verbunden), Speisung nur über die
  Halterkontakte, Adapter enthält **keine** Zelle. Der Mess-Zwischenadapter darf keine Quelle in Serie zur
  Zelle zulassen (nur Amperemeter, keine SMU im Quellbetrieb), Anleitung.
- **R2-A3:** Die 2 × 100 kΩ je Leitung liegen im Elektronikraum (nicht im Batteriefach), nicht nebeneinander
  in derselben Lötstoppöffnung, Abstand so, dass eine Lötbrücke oder ein Wasserfilm nicht beide überbrückt.
- **R2-A4:** Testplan: zusätzlich Rückstrom mit 5.5 V an allen 4 Pads gleichzeitig; Injektionsstrom in die
  ESD-Struktur (CC2340-Datenblatt nennt keinen Grenzwert, `TI_CC2340R5_Datasheet_SWRS272F.pdf` S.18 nur
  VDDS + 0.3 V) als PROTOTYP-PRÜFUNG mit Funktionsprüfung danach.

### R2.2 Übrige Befunde aus Runde 1

| ID | Urteil |
|---|---|
| S2-W01 | umgesetzt (Matrix „~“, OP-K7, Kurzschlussversuch). Offen bis Messung/Antwort, kein Veto. |
| S2-W02 | umgesetzt (Platzierungsregeln, OP-K16). Hinweis: jetzt **4** MLCC → FMEA-Eintrag mit 4 Stellen. |
| S2-W03 | umgesetzt als Regeln; Konstruktion Phase 3/4. Pads im Fach zulässig (hinter 2 × 100 kΩ, R2-A3). |
| S2-W04 | erledigt (Messbrücke entfällt). |
| S2-W05 | umgesetzt (TRM belegt, Anti-Rollback „~“, OP-K8). |
| S2-W06 | umgesetzt (keine Ladepfad-RTC, Zelle hinter Schraube); RV-3028-Datenblatt fehlt lokal (OP-K14). |
| S2-W07 | umgesetzt (Secure Boot, Flash-Verschlüsselung, signierte Updates); eFuse-Entscheid Phase 3. |
| S2-L01…L05 | umgesetzt. |
| S2-L06 | durch R2.3 ersetzt. |
| S2-L07 | zurückgestellt – akzeptiert (C ausgeschlossen). |

### R2.3 Sicherheitsbewertung Variante A-32 (Panasonic CR2032, Keystone 3034TR)

Grundlagen: `Keystone_3034_Catalog_M65.pdf` S.1 (Fig. 1 „Ultra Low“, A 21.2 / L 16.1 / W 23.1 / H 4.1 mm,
Phosphorbronze vernickelt, Minuspol = Leiterplattenpad „.156 [3.96] SQ. MIN.“, passt für CR2025 und CR2032);
`Panasonic_CR2032_Datasheet_2026-02.pdf` S.1 (−30…85 °C, Rücksprache ab 70 °C).

| Gefährdung | A (BS-24, LCP) | A-32 (Clip 3034) |
|---|---|---|
| Kurzschluss Zelle beim Einsetzen | Führung im LCP-Gehäuse, Kontakte geschützt | Pluspol-Becher (Rand und Mantel) gleitet über die Leiterplatte; Kurzschluss, wenn der Becherrand das Minuspad bzw. freies Kupfer berührt, während die Minuskappe ebenfalls Kontakt hat → **Padgrösse und Lötstopp unter der Zelle sind sicherheitsrelevant** |
| Verkehrt eingesetzte Zelle | vermutlich kein Minuskontakt (S2-L01) | Minuskappe am Clip (+), Becher am Minuspad → Verpolung, AO3401A sperrt. **Berührt der Clip zugleich den Bechermantel, ist die Zelle über den Clip kurzgeschlossen** (Geometrie aus dem Katalog nicht beurteilbar) |
| Herausfallen (Fall 1 m) | Deckel + LCP-Führung | nur Clipfeder; lose Zelle im Fach kann Clip und Pad in beliebiger Lage berühren → Deckelnoppe muss die Zelle halten |
| Feuchte im Fach | Kontakte im LCP gekapselt | offenes Minuspad (ENIG) und Clip (Ni) mit wenigen mm Abstand auf der Leiterplatte → Elektrolyse, Korrosion, Selbstentladung |
| Verschlucken | CR2450 (24.5 mm) | CR2032 (20 mm), die häufigste Zelle bei schweren Verschluckunfällen (**ANNAHME** Literatur, nicht lokal belegt). Schutz in beiden Fällen gleich: Deckel mit unverlierbarer Schraube (REQ-SAF-CC-04) |
| 65 °C | 5 K bis 70 °C | 5 K bis 70 °C (gleich) |
| Rückstrom | 1 % = 5.4 mAh, Fehler ≤ 15 mA | 1 % = 2.25 mAh, Fehler ≤ 10 mA – beide eingehalten (R2.1) |
| Energie im Kurzschlussfall | 540 mAh | 225 mAh (kleiner, leichter Vorteil A-32) |

**Urteil:** A-32 ist **zulässig**, wenn R2-W01 und R2-W02 erfüllt sind. Aus Sicherheitssicht bleibt **A
leicht vorzuziehen** (gekapselter Halter, verpolt kein Kontakt). Die Empfehlung in CONCEPTS Kap. 7
(„leichter Vorteil A“) ist richtig. Ein Wechsel zu A-32 nach OP-K5 ist ohne Veto möglich, verlangt aber
vor dem Layout-Freeze die Tests aus R2-W01.

### R2.4 Neue Befunde

**R2-W01 · wichtig · REQ-SAF-CC-02 · A-32** – Kurzschluss im Clip-Halter nicht ausgeschlossen.
*Vorschlag:* (1) Minuspad nur so gross, dass es sicher innerhalb der Minuskappe liegt (Keystone nennt nur das
Mindestmass 3.96 mm; Kappendurchmesser aus einer Panasonic-Massszeichnung belegen, im lokalen Datenblatt nicht
bemasst). (2) Unter der ganzen Zellfläche ausser dem Minuspad nur Lötstopplack, keine Vias, keine Pads, kein
freies Kupfer (auch nicht RX/TX/SWD-Pads). (3) PROTOTYP-PRÜFUNG: Einsetzen schräg, verkehrt herum, halb
eingeschoben, mit CR2025; jeweils Strom aus der Zelle messen (Kurzschluss = Abbruch). (4) Deckelnoppe hält die
Zelle im Clip; Falltest 1 m, danach Sitz prüfen.

**R2-W02 · wichtig · REQ-SAF-CC-03 · A, A-32** – Auflagen R2-A1…A4 zum Veto (Kap. R2.1) sind in Phase 3 im
Schaltplan, Layout und Testplan nachzuweisen; sonst lebt S2-K01 wieder auf.

| ID | Stufe | Befund | Vorschlag |
|---|---|---|---|
| R2-L01 | klein | Worst-Case rechnet mit Zelle 2.0 V. Eine ganz entladene Zelle (0 V) gibt 55 µA je Pad mit Einzelfehler. | In 2.7 ergänzen; Urteil unverändert. |
| R2-L02 | klein | Dummy-Adapter: LDO-Ausfall (Kurzschluss) legt 5 V an VDD (> VDDS abs. max 4.1 V, DS S.18). Keine Zelle im Kreis → kein Brandrisiko, aber Geräteschaden. | Optional Überspannungsschutz im Adapter; Anleitung. |
| R2-L03 | klein | Die neuen Herstellerquellen (Panasonic, Maxell) liegen nur in `docs/references/`. | In OP-K7 und Kap. 2.7 zitieren; Renata/Panasonic gezielt nach „max. abnormal charging current“ (UL 1642) fragen. |
