# Machbarkeitsstudie Phase 3 – Zellwechsel an der Farbfuge (P3 „Stele“), Sicht Mechanik

Bearbeiter: Mechanik-Konstrukteur, Stand 2026-11-07. Studie mit Volumenmodell, **kein Fertigungs-CAD**.
Anlass: D-009 („kein Batteriefach hinten; graues Teil nach unten abziehen, nur eine Trennung“).
Eingang: REQUIREMENTS (REQ-MECH-08/10/12/13/15, REQ-SAF-05, REQ-SAF-CC-02/04, REQ-UI-05/06, RB-03),
DECISIONS D-006/D-009, CONCEPTS Kap. 2.9/2A, DESIGN_PROPOSALS Kap. 0/3, `docs/reviews/phase3_design_mechanik.md`.

Modell und Prüfskript: `mechanical/gen/p3_sleeve_concept.py` (Lauf: `freecadcmd mechanical/gen/p3_sleeve_concept.py`),
Ergebnisse `mechanical/p3_sleeve/p3_sleeve_A1_30x13x48_sonde22.{FCStd,step}` und `…_28x13x48_sonde20.{FCStd,step}`.
Das Skript prüft automatisch Kollisionsfreiheit, das Abziehen der Hülse über die Sonde (150 mm in 1-mm-Schritten),
das seitliche Herausschieben der Zelle, Dichtungsstege, O-Ring-Verpressung und den Abstand Metall–Antenne.

## 0 Kurzantwort

**Machbar: ja, mit Bedingungen.** Empfohlen wird **A1 „Kern + Hülse, eine M2-Schraube von unten“**. Die blaue
Kappe und ein Sondenkragen sind dauerhaft mit der Platine verbunden (der „Kern“). Die graue Hülse wird nach
Lösen einer unverlierbaren Schraube in der Bodenfläche über die Sonde nach unten abgezogen. Sichtbar bleibt nur
die Farbfuge, die Schraube sitzt unsichtbar auf der Unterseite.
Die Bedingungen ändern das Hüllmass und das Layout, **28 × 13 × 45 mm sind so nicht zu halten**:

1. **Keystone 3034 um 90° drehen** (Einschub quer zur Sonde, offenes Ende zur Seite). In der bisherigen Lage
   müsste die Zelle in Sondenrichtung herausgleiten, dort stehen aber Kragen bzw. Schott im Weg (Kap. 2.3).
   Folge: Kopfhöhe **≈ 48 mm** (statt 45) bei 7 mm Elektronikband. Mit 5 mm Band sind es 46 mm (**ANNAHME**, Elektronik).
2. **Breite**: Die Bodendichtung braucht seitlich neben der Sonde ≥ 2 mm Steg. Möglich ist entweder ein
   **Kopf 30 mm bei Sonde 22 mm** (Steg 2.1 mm) oder ein **Kopf 28 mm bei Sonde 20 mm**. Mit 28/22 bleibt nur
   1.1 mm Steg, das reicht nicht (Skriptausgabe).
3. **Platine im Elektronikband/Antennenbereich nur 20 mm breit**, weil sie durch den Zapfen der Kappe läuft.
4. Die Sensoren müssen für den Zellwechsel **aus der Erde gezogen** werden (Hülse 37 mm lang, Freistrecke 5 mm).

## 1 Varianten

### A1 – Kern + Hülse, M2 von unten (empfohlen)

```
  z (mm)        Schnitt vorne-hinten (y), schematisch, Variante 30 x 13 x 48
  48 ┌───────────────┐  Kappe blau (ASA), Taste oben (unverändert, M-01/M-07)
  44 │  Antenne AN043│  Antenne 15.2 x 5.7, nur Kunststoff darüber
  38 │ Elektronikband│  Platine 20 breit, Elektronikraum dauerhaft dicht
  37 ├─┐ Farbfuge  ┌─┤  sichtbare Fuge 0.3 mm (keine Dichtfunktion), Kerbe für LED-Tropfen 34-37
  33 │ │◯ O-Ring  ◯│ │  O-Ring 1.5 radial auf Zapfen der Kappe (Nut 31.5-33.5)
  31 │ ╞══ Schott ══╡ │  Schott der Kappe, Platinendurchführung vergossen (Epoxid)
  29 │ │  ║  ┌──┐   │ │
     │ │  ║  │Zl│   │ │  CR2032 in 3034 (gedreht, Ausschub +x), Haltenoppe an Hülsenrückwand
   6 │ │  ║  └──┘   │ │
   6 │ ├──╫─Kragen──┤ │  Sondenkragen ASA + Epoxid, dauerhaft auf PCB = Dichtlinie REQ-MECH-08, Mutter M2
 2.8 │ │▓▓╫▓Dichtung▓│ │  Flachdichtung (Schlaufe) Boden/Kragen
   0 └─┴──╫───[S]───┴─┘  Hülsenboden 2.2, Sondenschlitz 22.6 x 2.2, Schraube M2 x 4 (unverlierbar)
          ║ Sonde 1.6
```

| Teil | Masse (Variante 30/22; in Klammern 28/20) |
|---|---|
| Hülse grau | aussen 30 (28) × 13 × 36.7, Wand 1.6, Boden 2.2; innen 26.8 (24.8) × 9.8; Sondenschlitz (Sonde + 0.6) × 2.2; Bohrung M2 bei y = 9 (hinter der Platine), Senkung für den Kopf; Kerbe 5.6 × 3.3 für die LED-Zunge; Haltenoppe 4 × 0.6 an der Rückwand (x = 4…8) |
| Kappe blau | Band z 37–48, Wand 1.6, Decke 2; Zapfen bis z 29.8 mit Gleitfläche (Hülse innen − 0.4), Nutgrund (Hülse innen − 2.2), Zapfenwand 1.0; Schott 1.5 bei z 29.8–31.3 mit Platinenschlitz, vergossen |
| O-Ring | Schnur **1.5 mm**, Nutgrund rechteckig mit Eckradius 2.0; Mittellinie 65.7 (61.7) mm → **ID ≈ 18 (17) mm** bei ≈ 3 % Dehnung; Verpressung 27 % nominal, **20–33 %** bei ± 0.1 mm Druckmass |
| Bodendichtung | Silikon-Flachdichtung als **Schlaufe 1.5 breit** entlang der Hülseninnenwand; Schlitz und Schraube liegen **innerhalb** der Schlaufe, also auf der Aussenseite der Dichtung; 0.8 → 0.6 mm (25 %); Verpressung über 2 Anschlagnocken am Kragen begrenzt |
| Kragen | ASA-Teil (Hülse innen − 0.4), Höhe 3.2, mit Epoxid auf die beschichtete Sondenwurzel vergossen; eingegossene Mutter M2 (SW 4 × 1.6, Schlüsselflächen parallel zu x → y 7.0–11.0); Längsnut 0.8 an der Rückseite, damit die Haltenoppe durchgleitet |
| Schraube | M2 × 4 A2, Linsen-/Zylinderkopf, Kreuz PH (handelsüblich). Unverlierbar, weil sie sich selbst durch eine Ø 1.7-Bohrung im Hülsenboden furcht; danach dreht sie frei. Metall–Antenne **33 mm** (Skript) |
| Höhenaufteilung | Boden 0–2.2, Dichtung –2.8, Kragen –6.0, Zelle/Clip 6.4–29.5, Schott 29.8–31.3, Elektronik 31.3–38.3, Antenne 38.3–44, Freiraum –46, Decke –48 |

**Skriptergebnis** (beide empfohlenen Varianten): keine Kollision im montierten Zustand; die Hülse lässt sich frei
150 mm über die Sonde abziehen; die Zelle lässt sich nach Entfernen der Hülse frei 25 mm in +x aus dem Clip schieben
(nur Kern geprüft, Clipverformung nicht modelliert). Bei 28/22 ist die Geometrie frei, aber der seitliche Dichtsteg ist nur 1.1 mm → **verworfen**.

### A2 – wie A1, aber Klick statt Schraube

Dafür wären zwei Rasthaken am Kragen (vorne/hinten, dort ist Steg vorhanden) nötig, die in Fenster der Hülse greifen.
Zum Lösen drückt man beide durch je ein Fenster und zieht gleichzeitig.
- Für REQ-SAF-CC-04 sind „zwei gleichzeitige, unabhängige Bewegungen“ plausibel, der Nachweis nach UL 4200A ist aber
  offen (Norm liegt nicht lokal vor, Phase 4).
- **Gegen A2:** Die Bodendichtung braucht dauernde Axialkraft (≈ 30–55 N, Kap. 3). ASA-Haken unter Dauerlast bei 65 °C
  kriechen, dadurch sinkt die Verpressung und die Dichtung wird undicht. Die Entriegelungsfenster sind zusätzliche
  sichtbare Öffnungen, also nicht mehr „nur eine Trennung“. Beim Fall aus 1 m kann die Rastung aufspringen.
- Bewertung: **machbar nur mit rein radialer Dichtung** (braucht mehr Breite, ≥ 30 mm auch bei Sonde 20) **und nicht empfohlen.**

### B – umgekehrt: graue Hülse fest am Sondenaustritt, Kappe + PCB nach oben

**Nicht machbar.** Sonde und Kopfplatine sind **eine** Leiterplatte (CONCEPTS Kap. 2.9, ≈ 22 × 170 mm). Ist die
Hülse an der Sonde vergossen, kann die Platine nicht nach oben heraus. Abnehmbar wäre dann nur die Kappe, und die
legt lediglich z ≥ 37 frei, also den Antennenbereich. Die Zelle (z 6–29) bliebe unerreichbar. Eine Zelle unter der
Kappe läge direkt an der AN043-Antenne (Metall in der Sperrzone) und scheidet aus. Dazu käme eine lösbare Fuge im
Bereich, den das Giesswasser direkt trifft.

### C – eigene Idee: Zelle in einer Tasche der Hülse (Konzept „A-F“)

Die Zelle sitzt in einer Tasche an der Hülsenrückwand und wird mit der Hülse abgezogen. Den Kontakt machen ein
Minus-Pad (ENIG) und eine Plus-Feder auf der Platine. So entfällt der Clip, und die Zelle kann auch beim Abziehen nicht verloren gehen.
- Dagegen: Der Federkontakt ist **nicht gewählt** (CONCEPTS Kap. 2.9, „A-F … Federkontakt noch nicht gewählt“), es
  bräuchte also eine Änderung von D-006 und eine neue Sicherheitsprüfung (Kurzschluss beim Abziehen/Aufschieben,
  Verpolung, Falltest). Beim Zusammenstecken gleitet die Zelle über Kontakte (Abrieb, Funken unkritisch bei 3 V).
- Bewertung: **möglich, aber Risiko und Aufwand zu hoch für Phase 4**. Rückfallebene, falls A1 am Muster scheitert.

Ebenfalls verworfen (nicht modelliert): A1 ohne Kragen, mit Gummitülle im Hülsenboden direkt auf der Sonde. Dann wäre
die Sondendichtung bei jedem Wechsel gelöst (verletzt REQ-MECH-15), die Tülle würde die schmutzige Sonde abstreifen,
und an den Platinenkanten (1.6 mm, eckig) wäre die Dichtung unsicher.

## 2 Bewertung A1 im Einzelnen

### 2.1 Farbfuge gegen Giesswasser (REQ-MECH-13)
- Die Sichtfuge (0.3 mm, horizontal, um die LED-Zunge herumgeführt) ist **keine** Dichtung. Abgedichtet wird radial
  mit dem O-Ring 3.5–5.5 mm tiefer (z 31.5–33.5), komplett unterhalb der Kerbe. Der Abstand zum Kerbengrund (z 33.7) beträgt
  im Modell aber nur 0.2 mm; in Phase 4 auf ≥ 1 mm vergrössern (Tropfen 1 mm kürzer oder Nut tiefer). Wasser, das in die
  Fuge gelangt, steht über dem O-Ring und trocknet über die Fuge ab.
- Ein radialer O-Ring braucht **keine Axialkraft** und ist unempfindlich gegen die axiale Lage der Hülse. Die
  Toleranzen von Kragen und Kappe (Klebelage ± 0.2) gehen deshalb nicht in die Dichtung ein.
- Gedruckte Dichtflächen: Die Hülse wird stehend gedruckt, die Schichtlinien laufen also umlaufend, quer zum Leckweg
  (günstig). Die **Z-Naht** muss in eine Hinterkante gelegt und im O-Ring-Bereich verschliffen werden, sonst entsteht
  ein axialer Kanal (PROTOTYP-PRÜFUNG).
- O-Ring aus **Silikon oder EPDM ohne Russ** (z. B. rot/transluzent) wählen: Er liegt 5 mm unter der Antenne, und
  russgefüllte Elastomere können HF-verlustbehaftet sein (**ANNAHME**, mit Elektronik klären). Dazu Silikonfett.
- Option für das Design: Die Kappe überlappt die Hülse um 1.5 mm. Die Hülse ist oben um 0.8 mm abgesetzt, die
  Sichtfuge bleibt eine Linie, öffnet aber nach unten (Tropfkante). Das verbessert den Schutz, ist aber nicht zwingend.

### 2.2 Sondenaustritt, Kriechweg (REQ-MECH-08, -15)
- Die **Dichtlinie ist der Kragen**: dauerhaft vergossen auf der beschichteten Sondenwurzel (REQ-MECH-07), 3.2 mm
  Haftlänge rundum (**ANNAHME**, genügt; Option 5 mm = +1.8 mm Höhe). Er wird beim Zellwechsel **nicht** gelöst,
  damit ist REQ-MECH-15 („ohne Lösen der Sondendichtung“) erfüllt.
- Die lösbare Bodendichtung (Hülse/Kragen) schliesst nur das Batteriefach. Schlitz und Schraubenloch liegen
  ausserhalb der Dichtschlaufe, ein Leckweg ins Fach über die Schraube ist deshalb ausgeschlossen.
- Der Kriechweg entlang der Platine wird **zweifach** unterbrochen: am Kragen (Erde → Fach) und am Schott (Fach → Elektronik).
  In der Dichtzone von Kragen und Schott ist laut M-03 ein 2-mm-Streifen ohne Kupfer und Vias nötig.
  Die Platinenkanten im Fach müssen beschichtet sein (Glasfaserdocht).
- Stege: seitlich 2.1, vorne 2.7, hinten 4.9 mm (Skript, Variante 30/22 bzw. 28/20).

### 2.3 Trennung Batteriefach / Elektronikraum (REQ-SAF-05) und Zelle erreichbar
- **Fach** = Raum zwischen Kragen (unten), Schott (oben) und Hülse, abgedichtet mit O-Ring und Bodendichtung.
  **Elektronikraum** = Kappe über dem Schott, dauerhaft vergossen bzw. verklebt. **Sondenübergang** = Kragen.
  Damit sind drei getrennte Räume vorhanden, und jeder lässt sich einzeln fluten (Fach: Hülse montiert; Elektronikraum:
  Prüfmuster mit Füllbohrung vor dem Verschliessen).
- Im Fach liegen nur Clip-Pads und Minus-Pad, keine Vias (Auflage R2-W01 Nr. 2 und S2-W03 bleiben). Die Signale
  laufen auf Innenlagen durch das Schott.
- **Warum der Clip gedreht werden muss:** Beim 3034 gleitet die Zelle in Richtung L (16.1 mm) aus
  (`docs/datasheets/Keystone_3034_Catalog_M65.pdf`, S. 1, Fig. 1/Zeile 3034). Liegt L in Sondenrichtung, braucht der
  Ausschub über 10 mm freien Weg nach unten oder oben. Dort sitzen aber Kragen bzw. Schott. Gedreht (L in x, offenes
  Ende +x) gleitet die Zelle bei abgezogener Hülse über die Platinenkante hinaus, das Skript zeigt den Weg als frei.
  W = 23.1 liegt nun in der Höhe, daher +3 mm.
  Gute Nebenwirkung: Die Platine muss im Fachbereich nur noch ≥ 20 mm breit sein (Zelle Ø 20), die Kopfbreite wird
  nicht mehr vom Clip bestimmt.

### 2.4 Verschluckschutz (REQ-SAF-CC-04)
- Die unverlierbare Schraube erfüllt die Anforderung („Werkzeug (unverlierbare Schraube)“). Zusätzlich ist der Sensor
  aus der Erde zu ziehen, und die Hülse muss über 37 mm Länge abgezogen werden. Nach dem Falltest bleibt die Hülse
  geschlossen (Schraube + O-Ring-Reibung).
- **Konflikt mit D-009 „kein Warnaufdruck“:** REQ-SAF-CC-04 verlangt ein Warnsymbol am Batteriefach. Vorschlag:
  Symbol erhaben auf der **Unterseite** (Bodenfläche, im Gebrauch unsichtbar, beim Öffnen zwingend gesehen) und/oder
  auf dem Kragen innen. → Entscheid Sicherheit/Orchestrator.

### 2.5 Ablauf Zellwechsel
1. Sensor ziehen und die Sonde abwischen (die Hülse gleitet über die Sonde, der Schlitz ist keine Dichtung, aber Krümel gelangen ins Fach).
2. Schraube PH lösen (bleibt in der Hülse), Hülse nach unten über die Sondenspitze abziehen.
3. Zelle mit dem Fingernagel am offenen Ende seitlich herausschieben, neue Zelle einschieben (+ oben, Markierung auf der Platine).
4. Dichtschlaufe und O-Ring kurz ansehen, Hülse aufschieben bis zum Anschlag am Kragen, Schraube bis Anschlag anziehen, Sensor stecken.
Dauer ≈ 2 min, etwa alle 12–17 Monate (D-006). Entnahme ohne Werkzeug: **PROTOTYP-PRÜFUNG**.

### 2.6 Druckbarkeit (Bambu P1S, ASA)
- **Hülse**: stehend, Boden auf dem Bett. Schlitz und Bohrung liegen in den ersten Schichten, keine Stützen. Die
  Noppe ist eine senkrechte Rippe, die Kerbe oben offen. **Kappe**: kopfüber (Decke auf dem Bett). Die O-Ring-Nut
  ergibt einen Überhang von 1.1 mm. Die überhängende Nutflanke mit 45° ausführen (oder mit 1.1 mm frei überbrücken, **ANNAHME**, Probedruck).
- Jedes Teil ist einfarbig, es gibt **keinen AMS-Farbwechsel** mehr (bisher einen bei z 34).
- Profil (Vorschlag): Bambu ASA, Düse 0.4, Schicht 0.16, 4 Wände (≈ 1.6), massiv (Wandteile), 5 Decken-/Bodenlagen,
  Elefantenfuss-Kompensation 0.15, Naht „hinten“.
- Passungen: Gleitsitz Hülse/Zapfen und Hülse/Kragen 0.2 je Seite, Sondenschlitz 0.3 je Seite, O-Ring-Spalt 1.1 ± 0.1.
  Vor dem ersten Gehäuse einen **Passungs-Prüfkörper** drucken (Spalt 0.15/0.2/0.25).

### 2.7 Dauerhaltbarkeit (65 °C, RB-03)
- Radialer O-Ring: Das ASA trägt nur den Anpressdruck des O-Rings, kein Kriechen der Fügestelle.
- Bodendichtung: Die Kraft geht über Schraube und **Stahlmutter**, im Gewinde kriecht also nichts. Unter dem
  Schraubenkopf kann das ASA kriechen; der Weg ist durch Anschlagnocken begrenzt, die Dichtung bleibt verpresst.
  Kopfauflage nicht dünner als 2 mm. Bei der Senkung im Modell bleiben nur 0.9 mm, deshalb **Kopf ohne Senkung, 1.2 mm
  vorstehend** (Unterseite, unsichtbar) oder Boden 3 mm (+0.8 Höhe). **PROTOTYP-PRÜFUNG**: 7 Tage 65 °C, danach Spritztest.
- Keine Schnapper unter Dauerlast (Gegenargument zu A2).

### 2.8 Robustheit (REQ-MECH-10)
Kraftfluss beim Einstecken (Druck auf die Kappe): Kappe → Schott-Verguss + Platinenschulter → Platine, **nicht** über
Hülse oder Schraube.
- Verguss im Schott: Umfang 2 × (20 + 1.6) = 43.2 mm × 1.5 = 65 mm². Mit Scherfestigkeit Epoxid auf ASA/FR4 ≥ 5 MPa
  (**ANNAHME**) ergibt das ≈ 320 N, gefordert 2 × 50 = 100 N → **SF ≈ 6.5**. Zusätzlich trägt bei Variante 30/22 die
  Schulter (22 → 20, 2 × 1 × 1.6 = 3.2 mm²): 100 N → 31 MPa auf ASA, nur als Zweitpfad.
- Zug 30 N, an der Hülse gefasst: Boden → Anschlag Kragen → Kragenverguss 47 mm × 3.2 = 150 mm² → ≈ 750 N (**ANNAHME** 5 MPa).
- Druck auf die Hülse (Fehlbedienung) 50 N: über Schraube M2/Stahlmutter. Mutter-Ausreissen durch 0.8 mm Epoxid
  ≈ 14 mm × 0.8 × 20 MPa ≈ 220 N (**ANNAHME**). In der Anleitung „auf die Kappe drücken“ angeben.
- Fall 1 m: Die Zelle hält im Clip, dazu die Noppe (0.5 mm Luft). Die Seitenwand begrenzt den Ausschubweg auf 3.4 (2.4) mm,
  die Zelle bleibt also im Clip gefangen (REQ-SAF-CC-02, PROTOTYP-PRÜFUNG). Die Hülse stützt sich radial über Zapfen und
  Kragen (je 0.2 mm Spalt) am Kern ab.
- Sondenbiegung unverändert, abgesehen vom Hebel (Kopfunterkante unverändert). FEM folgt in Phase 4. Bei Sonde 20 mm
  steigt die Biegespannung um 22/20 = **+10 %** (Kap. 3 von `phase3_design_mechanik.md`: 112 → ≈ 123 MPa, SF ≈ 3.3 gegen 400 MPa **ANNAHME**).

### 2.9 Kosten (Richtwerte, **ANNAHME**, keine Angebote eingeholt)
O-Ring Silikon 18 × 1.5 ≈ 0.10–0.30 CHF; Silikon-Flachdichtung (aus Platte geschnitten) ≈ 0.10; Schraube M2 × 4 A2 +
Mutter ≈ 0.05–0.08; Epoxid Kragen + Schott ≈ 1.5 g ≈ 0.15–0.30; ASA ≈ 10 g ≈ 0.25. **Total ≈ 0.65–1.0 CHF**, ähnlich wie
beim bisherigen Rückdeckel (Schraube + Gewindeeinsatz + Flachdichtung). Mit 7.07 CHF (D-006) bleibt das Ziel < 10 CHF erfüllt.
Der Gewindeeinsatz entfällt, dafür kommen eine Mutter und ein O-Ring hinzu.

## 3 Vergleich

| Kriterium | A1 Schraube | A2 Klick | B umgekehrt | C Zelltasche |
|---|---|---|---|---|
| Nur eine Sichtfuge | ✔ (Schraube unten) | ~ (Fenster) | – | ✔ |
| Dichtung Farbfuge | ✔ O-Ring radial | ✔ | ✘ | ✔ |
| Sondendichtung bleibt fest | ✔ Kragen | ✔ | – | ✔ |
| REQ-SAF-05 drei Räume | ✔ | ✔ | – | ~ (Kontakte durch Dichtung?) |
| REQ-SAF-CC-04 | ✔ Werkzeug | ~ Nachweis UL 4200A | – | ✔ |
| Kriechen 65 °C | ✔ | ✘ Haken unter Last | – | ~ |
| Neue Bauteile/Entscheide | Clip drehen | dto. | – | Federkontakt, D-006 |
| **Urteil** | **empfohlen** | nicht empfohlen | **nicht machbar** | Rückfallebene |

## 4 Bedingungen und offene Punkte (für Phase 4)

| Nr | Punkt | Wer |
|---|---|---|
| S-01 | 3034 gedreht (offenes Ende zur Seite), Platine im Fach ≥ 20 mm; Elektronikband z 31.3–38.3 (7 × 20 mm) auf einer Seite – reicht der Platz? | Elektronik |
| S-02 | Platine im Band/Antennenbereich 20 mm breit: AN043 (15.2 mm) mit 2.4 mm Rand, Massefläche nach AN043 prüfen | Elektronik |
| S-03 | Entscheid Hüllmass **30 × 13 × 48** (Sonde 22) oder **28 × 13 × 48** (Sonde 20, Feldsimulation REQ-MECH-11) | Auftraggeber, Elektronik |
| S-04 | O-Ring-Werkstoff ohne Russ, 5 mm unter der Antenne | Elektronik |
| S-05 | Warnsymbol an der Unterseite statt Aufdruck aussen (D-009 vs. REQ-SAF-CC-04) | Sicherheit |
| S-06 | Zellwechsel nur gezogen; Anleitung: Sonde abwischen, auf die Kappe drücken | Doku |
| S-07 | PROTOTYP-PRÜFUNG: Spritztest REQ-MECH-13 mit Zelle, Flutung Fach/Elektronikraum getrennt 24 h (REQ-SAF-05), 65 °C/7 d, Falltest 1 m, 20 Wechselzyklen (O-Ring, Gewinde in der Hülse), Feuchteindikator im Elektronikraum | Mechanik/Test |
| S-08 | LED/Taster wie bisher offen (M-01/M-07); die LED-Zunge der Kappe liegt in einer Kerbe der Hülse, Sichtfuge folgt dem Tropfen | Mechanik/Design |

## 5 Annahmen (Zusammenfassung)
Sondenbreite 22 mm (CONCEPTS 2.9); CR2032 Ø 20 × 3.2 (Nennmass); Clip-Hülle als Quader L 16.1 × W 23.1 × H 4.1;
Bauteilhöhe Elektronik 1.7 mm; Elektronikband 7 mm genügt; M2-Mutter SW 4 × 1.6; Kopf Schraube Ø 3.8 × 1.2;
Epoxid-Haftung 5 MPa auf ASA/FR4; Epoxid-Scherfestigkeit 20 MPa; FR4-Biegefestigkeit 400 MPa; O-Ring-Verpressung
15–30 % zulässig; Silikon-Dichtkraft 0.3–0.5 MPa bei 20–25 % Verpressung (≈ 30–55 N); Kosten Richtwerte. Alle Werte
sind in Phase 4 mit Datenblättern bzw. am Muster zu belegen.
