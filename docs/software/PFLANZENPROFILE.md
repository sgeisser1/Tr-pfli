# fluidi – Pflanzenprofile: Giessverhalten und Startschwellen

Stand 2026-11-07 · Grundlage: D-020 (Feuchteprofile), SOFTWARE_CONCEPT Kap. 8 und 9 · maschinenlesbar:
`app/data/species.json` (gleicher Inhalt, die Tabelle unten ist daraus erzeugt)

## 1 Zweck und Regeln

Wunsch des Auftraggebers: mit den drei Klassen **trocken / mittel / feucht** arbeiten, aber je Art wissen, *wie* sie
es gern hat – z. B. „nach dem Giessen das Wasser aufbrauchen und dann eine Weile trocken stehen“ gegenüber „immer
etwas feucht“.

- **Was aus Quellen stammt:** Regime, Abtrocknungsgrad (Spalte „laut Quelle“, englischer Wortlaut im JSON-Feld
  `dryness_source`), Winterhinweise, Substrat, Warnungen vor Staunässe/Trockenheit. Quellen: Extension-Merkblätter
  (NC State, Clemson HGIC, UMD, Iowa State, Wisconsin, Penn State, UC ANR), RHS, NYBG, American Orchid Society.
  Händlerquellen nur bei Hydrokultur und Kentia (gekennzeichnet).
- **Was ANNAHME ist:** alle Prozentwerte (Schwellen, Winterfaktor), die Zuordnung Regime → Klasse und die
  Einordnung bei widersprüchlichen Quellen (in der Tabelle vermerkt).
- **Wiedergabe:** Die Seiten wurden am 2026-11-07 mit einem Abruf-Werkzeug gelesen, das den Seitentext
  zusammenfasst. Die Zitate sind daher nahezu wörtlich, aber nicht garantiert zeichengenau (Ausnahme: AOS-PDF,
  per `pdftotext` gelesen). Vor einer Veröffentlichung der Texte in der App stichprobenartig gegenlesen.
- **Nicht erreichbar** am Abruftag (deshalb nicht verwendet): University of Minnesota Extension (HTTP 403),
  Missouri Botanical Garden Plant Finder (TLS-Fehler), UF/IFAS EDIS ST297 Kentia (Umleitungsschleife), mehrere
  RHS-Einzelseiten (404). Nur aus Suchergebnis-Ausschnitten Gesehenes ist nicht als Quelle aufgeführt.

## 2 Regime-Typen

| Regime | Bedeutung (aus den Quellen) | Typische Formulierung der Quelle | Klasse |
|---|---|---|---|
| **A** | durchdringend giessen, bis Wasser unten austritt, dann **weitgehend bis vollständig abtrocknen** lassen – Trockenphase gehört dazu | „allow the soil to completely dry between waterings“, „only after the potting medium has completely dried“ | trocken |
| **B** | durchdringend giessen, dann **oberste Zentimeter / oberes Viertel bis Drittel** abtrocknen lassen | „top quarter to one-third“, „top two inches“, „dry to ½ inch deep“, „top 2 cm“ | mittel |
| **C** | **gleichmässig feucht**, nie austrocknen, aber nie nass | „keep evenly moist“, „should never be allowed to dry out“ | feucht |
| **D** | Sonderfall: Orchidee in Rinde (Topfgewicht, etwa wöchentlich), Hydrokultur (Wasserstandsanzeiger) | „If in doubt, wait a day“, „until the dial sits at minimum for 2–3 days“ | – |

Gemeinsam fast aller Quellen: **durchdringend giessen und abtropfen lassen, nie im Untersetzer stehen lassen**
(z. B. Clemson HGIC 1459: „Apply water until it runs out of the bottom of the pot“) und **im Winter / in der
Ruhezeit weniger Wasser**. Die häufigste Schadensursache in den Merkblättern ist **Übergiessen (Wurzelfäule)**.

## 3 Artenliste (40 Einträge)

¹ Empfindlichkeit gegen Staunässe / gegen Austrocknen: *hoch* = Quelle warnt ausdrücklich, *mittel* = Quelle nennt
Schäden bei beidem bzw. schwächer, *gering* = Quelle nennt Trockenheitsverträglichkeit, *k. A.* = keine Angabe.
Die Stufung ist eine Lesart der Quellentexte, keine Quellenangabe.
² **Startwerte von fluidi (ANNAHME)** im Feuchteindex 0–100 %, keine Literaturwerte (Kap. 4). „zu nass“ gilt erst
nach der Karenzzeit nach einer Giessung (Kap. 4.2).

| # | Art (botanisch) | Klasse | Regime | Abtrocknen vor dem Giessen (laut Quelle) | Winter (laut Quelle) | Staunässe / Trockenheit¹ | Substrat (laut Quelle) | Start: Giessen bei / zu nass² | Winter-faktor² | Quellen |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **Monstera, Fensterblatt** (Monstera deliciosa) | mittel | B | oberes Viertel bis Drittel abtrocknen lassen. *Clemson (allgemein Philodendron/Monstera): gleichmässig feucht, nicht nass; Wurzelfäule bei schlecht drainierendem Substrat oder zu häufigem Giessen.* | keine Angabe in den Quellen | mittel / k. A. | humusreich, gut durchlässig | 30 % / 75 % | 0.8 | S01, S02 |
| 2 | **Geigenfeige** (Ficus lyrata) | mittel | B | oberste ca. 5 cm (2 in) trocken. *Empfindlich gegen Übergiessen; Blattfall bei zu viel oder zu wenig Wasser. Untersetzer nach 15 min leeren.* | Okt-Feb bei wenig Licht langsamere Wasseraufnahme (NYBG) | hoch / mittel | durchlässig, lehmig, leicht sauer | 30 % / 70 % | 0.8 | S03, S04, S65 |
| 3 | **Birkenfeige** (Ficus benjamina) | mittel | B | im Wachstum gleichmässig feucht (Clemson) bzw. erst wenn obere Zentimeter trocken (NYBG); im Winter leicht abtrocknen lassen. *Quellen uneinheitlich (Clemson eher C, NYBG eher B) -> B mit höherer Schwelle. Blattfall bei Über- und Untergiessen; nie im Untersetzer stehen lassen.* | im Winter etwas stärker abtrocknen lassen | hoch / mittel | erdbasiertes Zimmerpflanzensubstrat | 35 % / 75 % | 0.8 | S05, S06, S07 |
| 4 | **Gummibaum** (Ficus elastica) | mittel | B | Oberfläche leicht abtrocknen lassen. *Übergiessen -> Blattverlust, Wurzelfäule. Untersetzer leeren.* | in der Ruhezeit (Herbst bis Spätwinter) deutlich weniger giessen (NCSU) | hoch / k. A. | gut drainierendes Zimmerpflanzensubstrat | 30 % / 75 % | 0.7 | S08, S09 |
| 5 | **Efeutute** (Epipremnum aureum) | trocken | A | zwischen den Wassergaben abtrocknen lassen (Clemson-Kurzübersicht: vollständig). *Bisher in der App 'mittel' (ANNAHME) - Quellen sprechen für Regime A. Schwelle 20 statt 15, weil NCSU nur 'dry out between' sagt.* | keine Angabe in den Quellen | hoch / gering | luftig, gut drainierend | 20 % / 65 % | 0.8 | S10, S11 |
| 6 | **Bogenhanf** (Dracaena trifasciata (syn. Sansevieria trifasciata)) | trocken | A | Frühling-Herbst zwischen den Wassergaben abtrocknen lassen; Winter nur alle 1-2 Monate. *Wurzeln faulen bei Übergiessen.* | nur alle 1-2 Monate giessen; Winternässe vermeiden (RHS) | hoch / gering | gut durchlässig, lehmig oder sandig | 15 % / 55 % | 0.5 | S12, S13 |
| 7 | **Glücksfeder, Zamioculcas** (Zamioculcas zamiifolia) | trocken | A | erst wenn das Substrat vollständig abgetrocknet ist. *Speichert Wasser im Rhizom; 'wet feet are not tolerated'.* | nur etwa einmal im Monat (NCSU) | hoch / gering | grob, gut drainierend (Clemson: 1/2 Torf- oder Kokoserde, 1/4 Perlite, 1/4 Sand) | 10 % / 55 % | 0.5 | S14, S15 |
| 8 | **Kakteen (Zimmer)** (Cactaceae) | trocken | A | Wachstum: durchdringend giessen, sobald die Oberfläche trocken ist, aber nicht übermässig austrocknen lassen; Winterruhe: kaum oder gar nicht giessen. *Ausnahme Blattkakteen (Epiphyllum, Schlumbergera) - nicht diese Vorlage. Im mineralischen Substrat eigene Kalibrierung nötig. Winterfaktor sehr klein = praktisch kein Hinweis im Winter.* | Winterruhe kühl (Nacht 8-10 °C), nur so viel, dass die Pflanze nicht schrumpft (RHS, NYBG) | hoch / gering | sehr durchlässig, mineralisch-körnig (Kakteenerde oder John Innes Nr. 2 mit Splitt) | 15 % / 50 % | 0.3 | S16, S17 |
| 9 | **Sukkulenten, Echeverie** (Echeveria spp. (u. a. Rosettensukkulenten)) | trocken | A | ganzen Wurzelballen durchnässen, dann vollständig abtrocknen lassen. *Normale Blumenerde hält zu viel Wasser (Iowa State). Wasser nie länger als wenige Stunden im Untersetzer.* | Winterruhe wie Kakteen, kaum giessen (RHS) | hoch / gering | Kakteen-/Sukkulentenerde oder 1 Teil organisch : 2 Teile mineralisch (Perlite, Bims, Splitt) | 10 % / 50 % | 0.5 | S18, S16, S19 |
| 10 | **Echte Aloe** (Aloe vera) | trocken | A | zwischen den Wassergaben vollständig abtrocknen lassen. | im Winter seltener giessen | hoch / gering | sehr durchlässig, Sukkulentenerde; Topf mit mehreren Abzugslöchern, Ton am besten | 10 % / 50 % | 0.5 | S20, S16 |
| 11 | **Geldbaum, Jadebaum** (Crassula ovata) | trocken | A | durchdringend giessen, dann abtrocknen lassen (Penn State: nur wenn vollständig trocken). *Übergiessen -> Blattfall und Stammfäule.* | halbruhend, Giessen einschränken, eher trocken halten | hoch / gering | gut drainierende, porenreiche Kakteen-/Sukkulentenerde | 10 % / 50 % | 0.5 | S40, S41, S42 |
| 12 | **Yucca, Riesenpalmlilie** (Yucca gigantea (syn. Y. elephantipes)) | trocken | A | keine Abtrocknungstiefe in seriöser Quelle; trockenheitsverträglich, Übergiessen problematisch. *Regime A aus 'drought tolerant' + Fäulnisgefahr abgeleitet (ANNAHME). Händlerangaben (nicht verifiziert): 'obere Hälfte trocken'.* | keine Angabe in seriöser Quelle | hoch / gering | 1 Teil Erde : 3 Teile Perlite oder Sand (NCSU) | 20 % / 60 % | 0.7 | S26 |
| 13 | **Philodendron, Baumfreund** (Philodendron hederaceum) | feucht | C | leicht feucht halten, nicht nass. *Clemson: gleichmässig feucht, nie im Wasser stehen lassen. Schwelle etwas tiefer als C-Standard, weil 'slightly moist'.* | im Winter weniger giessen | hoch / k. A. | gut drainierend | 40 % / 80 % | 0.8 | S21, S02 |
| 14 | **Strahlenaralie, Schefflera** (Schefflera arboricola / S. actinophylla) | mittel | B | durchdringend giessen, dann ca. 1 cm (1/2 in) tief abtrocknen lassen. *Blattfall bei zu nass und zu trocken.* | keine Angabe in den Quellen | hoch / mittel | gut drainierend, humusreich | 30 % / 75 % | 0.8 | S22, S23 |
| 15 | **Drachenbaum** (Dracaena fragrans / D. marginata) | mittel | B | Oberfläche trocken (Clemson) bzw. oberste 5 cm trocken (RHS), dann durchdringend giessen. *Nicht mit kaltem Wasser giessen.* | keine Angabe in den Quellen | hoch / k. A. | locker, schnell drainierend (RHS: lehmfrei, leicht sauer) | 25 % / 70 % | 0.8 | S24, S25 |
| 16 | **Dieffenbachie** (Dieffenbachia seguine) | mittel | B | oberste 2,5 cm (1 in) vollständig abtrocknen lassen, dann durchdringend giessen. | keine Angabe in der Quelle | hoch / k. A. | locker, nährstoff- und humusreich | 30 % / 75 % | 0.8 | S39 |
| 17 | **Kolbenfaden** (Aglaonema spp.) | mittel | B | Frühling-Herbst feucht halten, aber zwischen den Wassergaben abtrocknen lassen. *Kälteempfindlich.* | keine Ruhezeit nötig, aber im Winter weniger giessen | hoch / k. A. | k. A. | 30 % / 75 % | 0.8 | S38 |
| 18 | **Efeu (Zimmer)** (Hedera helix) | mittel | B | durchdringend giessen, dann ca. 1 cm (1/2 in) tief abtrocknen lassen. *Nicht im Wasser stehen lassen.* | keine Giessangabe (nur: bei Kühle nicht düngen) | hoch / k. A. | gute, nährstoffreiche Zimmerpflanzenerde | 30 % / 75 % | 0.8 | S37 |
| 19 | **Bergpalme** (Chamaedorea elegans) | mittel | B | zwischen den Wassergaben leicht abtrocknen lassen. | keine Giessangabe (im Winter nicht düngen) | hoch / mittel | humusreiche Zimmerpflanzen-/Kübelerde, gut drainierend | 35 % / 75 % | 0.8 | S43 |
| 20 | **Zitrusbäumchen (Zitrone, Calamondin)** (Citrus spp. (Kübel)) | mittel | B | Oberfläche zwischen den Wassergaben abtrocknen lassen, Wurzelballen nie ganz austrocknen; durchdringend giessen. *Blattfall = Hinweis auf zu nass, Blütenfall = zu trocken (UMD). Übergiessen im Winter ist laut RHS einer der häufigsten Fehler.* | Oberfläche teilweise abtrocknen lassen, dann durchdringend mit lauwarmem Regenwasser; 'err on the dry side' (RHS) | hoch / mittel | gut drainierend (Zitrus-, Kakteen- oder Universalerde; Clemson: 4 Teile Pinienrinde : 1 Teil Torf/Kokos) | 35 % / 75 % | 0.8 | S31, S32, S33 |
| 21 | **Olivenbaum (Kübel)** (Olea europaea) | mittel | B | keine Abtrocknungstiefe in seriöser Quelle; April-September regelmässig giessen. *Keine seriöse Quelle für Haltung im geheizten Raum gefunden. Regime B und Schwelle sind ANNAHME.* | Winter: Substrat nur knapp feucht, Topf nicht vernässen lassen (RHS); hell und kühl/frostfrei überwintern | hoch / k. A. | erdbasiert (John Innes Nr. 3) mit ca. 20 % Splitt, viele Abzugslöcher | 25 % / 70 % | 0.6 | S34 |
| 22 | **Strelitzie, Paradiesvogelblume** (Strelitzia reginae / S. nicolai) | feucht | C | Frühling/Sommer ständig feucht, nicht nass; ab Ende November ziemlich abtrocknen lassen. *Saisonal stärkster Wechsel der Liste: Sommer C, Winter fast A. RHS nennt keine eigene Regel für S. nicolai.* | im Herbst schrittweise reduzieren; im Winter ziemlich trocken (starker Wechsel!) | mittel / mittel | torffreie, lehmhaltige Erde mit Splitt | 45 % / 85 % | 0.5 | S27 |
| 23 | **Kentiapalme** (Howea forsteriana) | feucht | C | gleichmässig feucht, nie nass; vor dem Giessen Oberfläche prüfen. *Hauptquelle ist der RHS-Pflanzenshop (halb Händler). NCSU: verträgt Trockenheit und Vernachlässigung -> Schwelle 40 statt 45.* | im Winter weniger giessen, wenn das Wachstum nachlässt | mittel / mittel | gut drainierend, humusreich, trocknet nicht schnell aus (NCSU) | 40 % / 80 % | 0.8 | S28, S29 |
| 24 | **Goldfruchtpalme, Areca** (Dypsis lutescens) | feucht | C | in der Wachstumszeit feucht, aber nicht nass. *Hohe Luftfeuchte erwünscht.* | keine Angabe in der Quelle | k. A. / k. A. | gut drainierende Erde | 45 % / 85 % | 0.8 | S30 |
| 25 | **Calathea, Korbmarante** (Goeppertia spp. (syn. Calathea)) | feucht | C | gleichmässig feucht, nicht nass. *Regen- oder destilliertes Wasser empfohlen (Fluorid im Leitungswasser -> braune Blätter). Hohe Luftfeuchte (~60 %).* | im Winter weniger giessen | mittel / hoch | feucht haltend, gut drainierend, viel organische Substanz und Perlite | 45 % / 85 % | 0.85 | S46, S47 |
| 26 | **Pfeilwurz, Gebetspflanze** (Maranta leuconeura) | feucht | C | in der Wachstumszeit gleichmässig feucht. *Hohe Luftfeuchte.* | im Winter Giessen zurücknehmen und abtrocknen lassen | mittel / hoch | gut drainierend | 45 % / 85 % | 0.7 | S48 |
| 27 | **Schwertfarn, Boston-Farn** (Nephrolepis exaltata) | feucht | C | feucht, nie austrocknen lassen. *Empfindlichste Art gegen Austrocknen in der Liste -> Schwelle 50.* | im Winter weniger giessen (ruhend, Übergiessen -> Wurzelfäule) | mittel / hoch | gut drainierend | 50 % / 85 % | 0.85 | S49 |
| 28 | **Strauchbegonie (Zimmer)** (Begonia, stammbildende Hybriden) | feucht | C | nie ganz austrocknen lassen, aber nicht übergiessen. *RHS: die meisten Ausfälle durch Übergiessen oder zu trockene Luft.* | im Winter weniger giessen | hoch / mittel | torffreie Universalerde oder John Innes Nr. 2 | 40 % / 80 % | 0.8 | S59 |
| 29 | **Blattbegonie (Rex)** (Begonia Rex-Cultorum-Gruppe) | mittel | B | Sommer reichlich, sobald die Oberfläche abgetrocknet ist; Winter Oberfläche abtrocknen lassen. *Blätter und Herz nicht benetzen.* | weniger giessen | hoch / mittel | k. A. | 35 % / 75 % | 0.8 | S59 |
| 30 | **Einblatt, Friedenslilie** (Spathiphyllum spp.) | mittel | B | feucht, nicht nass; zwischen den Wassergaben abtrocknen lassen (ohne Tiefenangabe). *Grenzfall B/C -> B mit hoher Schwelle 40. Braune Blattspitzen u. a. bei Wassermangel. Giessen von unten funktioniert gut (NCSU).* | keine Giessangabe (Wachstum bei 4-15 °C stark verlangsamt) | mittel / mittel | viel organische Substanz, gut drainierend | 40 % / 80 % | 0.85 | S50 |
| 31 | **Grünlilie** (Chlorophytum comosum) | mittel | B | wächst am besten in feuchter Erde, verträgt aber Trockenheit (keine Abtrocknungstiefe). *Chlor/Fluorid im Leitungswasser -> Blattspitzen braun.* | im Winter weniger giessen | k. A. / gering | lehmig, gut drainierend | 30 % / 75 % | 0.8 | S51 |
| 32 | **Ufopflanze, Glückstaler** (Pilea peperomioides) | mittel | B | giessen, wenn die obersten 2 cm abtrocknen. *Nicht im Wasser stehen lassen, Wurzeln faulen leicht.* | keine Angabe in den Quellen | hoch / k. A. | durchlässige, torffreie Zimmerpflanzenerde | 30 % / 70 % | 0.8 | S54, S55 |
| 33 | **Zwergpfeffer** (Peperomia obtusifolia u. a.) | mittel | B | obere paar Zentimeter abtrocknen lassen. *NCSU: 'intolerant of wet soil, very dry soil'; Übergiessen grosses Problem -> Schwelle tiefer (25).* | keine Angabe in den Quellen (über 10 °C halten) | hoch / mittel | gut drainierend | 25 % / 65 % | 0.8 | S56, S57 |
| 34 | **Flamingoblume** (Anthurium andraeanum) | mittel | B | giessen, wenn die obersten 2,5 cm (1 in) trocken sind. *Luftfeuchte 60-80 %, keine kalte Zugluft.* | keine Angabe in der Quelle | hoch / k. A. | feucht haltend, gut drainierend | 30 % / 75 % | 0.8 | S58 |
| 35 | **Alokasie, Pfeilblatt** (Alocasia × amazonica u. a.) | mittel | B | keine Abtrocknungsangabe in seriöser Quelle; 'feucht, gut drainiert'. *Regime B ist ANNAHME (Händler, nicht verifiziert: 'obere 5-7 cm trocken'). Übergiessen -> Wurzel- und Stängelfäule.* | in der Ruhe sehr wenig Wasser, kühler und trockener halten (RHS) | hoch / k. A. | feucht, gut drainiert, nährstoffreich, lehmig | 35 % / 75 % | 0.6 | S60, S61 |
| 36 | **Wachsblume** (Hoya carnosa) | mittel | B | NCSU: zwischen den Wassergaben abtrocknen lassen; RHS: feucht, aber nie nass und nie ganz trocken. *Quellen uneinheitlich (A vs. C) -> B mit tiefer Schwelle 25. Blattfall bei zu nass und zu trocken.* | im Winter (halbruhend) weniger giessen, besonders auf Übergiessen achten | hoch / mittel | locker, schnell drainierend, organisch | 25 % / 65 % | 0.7 | S62, S63 |
| 37 | **Basilikum (Topf)** (Ocimum basilicum) | feucht | C | gleichmässig feucht (RHS); Iowa State (Kräuter allgemein): zwischen den Wassergaben abtrocknen lassen. *Quellen widersprechen sich -> C mit Schwelle 40. Morgens giessen. Meist einjährig.* | keine Angabe | mittel / mittel | torffreie Universalerde, durchlässig | 40 % / 80 % | 1 | S35, S36 |
| 38 | **Orchidee (Phalaenopsis, Rinde)** (Phalaenopsis) | trocken | D | in Rinde etwa wöchentlich; in Moos, wenn die Oberfläche trocken ist; am Topfgewicht beurteilen, 'im Zweifel einen Tag warten'. *Durchdringend giessen und vollständig abtropfen lassen; Wasser im Herz abtupfen (Herzfäule). Kein enthärtetes oder destilliertes Wasser. Feuchteindex in grober Rinde wenig aussagekräftig (Luftspalten, PROTOTYP-PRÜFUNG): Startwerte nur, wenn eigene Kalibrierung in diesem Substrat gelingt; sonst Erinnerung nach Zeit.* | Sommer häufiger, Winter seltener | hoch / mittel | Rinde (oder Moos) | 20 % / 60 % | 0.8 | S52, S53 |
| 39 | **Hydrokultur (beliebige Pflanze)** (-) | – | D | erst nachfüllen, wenn der Wasserstandsanzeiger einige Tage (2-3) auf Minimum steht. *Nur Händlerquellen. fluidi misst Substratfeuchte, nicht den Wasserstand: Sensor nicht empfohlen, Profil ohne Schwelle (nur manuelle Erinnerung).* | k. A. | - / - | Blähton mit Wasserstandsanzeiger | – | – | S44, S45 |
| 40 | **Andere Pflanze** () | mittel | B | Fingerprobe bis zum ersten Fingerglied; ist es dort trocken, giessen, bis Wasser unten austritt. *Allgemeine Regel, keine Art.* | in der Ruhezeit weniger Wasser | k. A. / k. A. | k. A. | 30 % / 75 % | 0.8 | S64 |

Auffälligkeiten gegenüber dem bisherigen Vorlagen-Stand (`app/dev/mock_server.py`, `SPECIES`):

- **Efeutute**: bisher „mittel“ – Clemson und NC State sagen „zwischen den Wassergaben (vollständig) abtrocknen
  lassen“ → hier **trocken / A** (Schwelle 20 %, nicht 15 %).
- **Orchidee**: bisher „trocken“ – jetzt **D** (Rinde; Sensoraussage unsicher), Klasse trocken als Rückfall.
- Übrige Vorlagen bestätigt: Monstera, Geigenfeige, Grünlilie, Zitrus = mittel; Bogenhanf, Kaktus, Glücksfeder =
  trocken; Calathea = feucht.

## 4 Übertragung auf fluidi (ANNAHME, Startwerte)

### 4.1 Warum keine Literaturwerte möglich sind
Der Feuchteindex ist **sensor- und substratabhängig**: 0 % = eigener Trockenpunkt, 100 % = eigener Nasspunkt aus der
Zwei-Punkt-Kalibrierung (GATEWAY_API Kap. 7). Die Quellen beschreiben die Abtrocknung **der obersten Zentimeter**
(Fingerprobe), die Sonde mittelt dagegen über ca. 100 mm Tiefe. Wenn „oben 2–5 cm trocken“ ist, zeigt die Sonde noch
einen mittleren Wert. Deshalb gibt es je Regime nur einen **Startwert**, der nach einigen Zyklen an die eigene Pflanze
angepasst wird. Mineralisches Granulat (Kakteen, Sukkulenten, Bims/Splitt) braucht eine eigene Kalibrierung; der
Index ist zwischen Erde und Granulat nicht vergleichbar. Ob die Startwerte zur Fingerprobe passen, ist
**PROTOTYP-PRÜFUNG** (3–5 Pflanzen je Regime: Indexwert notieren, wenn die Fingerprobe „giessen“ ergibt).

### 4.2 Schwellen je Regime (Startwerte, ANNAHME)

| Regime | Hinweis „giessen“ bei ≤ | Ziel nach dem Giessen | „zu nass“ (nach Karenz) | Trockenphase erwünscht | Winterfaktor | Begründung |
|---|---|---|---|---|---|---|
| A | **15 %** (Arten 10–20 %) | ≥ 80 % | > 60 % länger als 48 h nach dem Giessen | **ja** | 0.7 (Kakteen 0.3, Bogenhanf/Glücksfeder/Sukkulenten 0.5) | „vollständig/weitgehend trocken“ ≈ nahe am kalibrierten Trockenpunkt, aber Abstand zum Rauschen und zur Kalibrierunsicherheit |
| B | **30 %** (Arten 25–40 %) | ≥ 80 % | > 75 % länger als 48 h | nein | 0.8 | oben trocken, unten noch feucht → mittlerer Index über die Sondenlänge |
| C | **45 %** (Arten 40–50 %) | ≥ 80 % | > 85 % länger als 48 h | nein | 0.9 (Maranta 0.7, Strelitzie 0.5) | „nie austrocknen“ → früh erinnern; Obergrenze hoch, weil gleichmässig feucht gewollt |
| D | keine (nur Zeit-Erinnerung) | – | – | – | – | Rinde/Blähton: Sonde misst Luftspalten bzw. nicht den Wasserstand |

- Die bisherigen Klassen-Startwerte (SOFTWARE_CONCEPT Kap. 9: trocken 10–45 %, mittel 30–70 %, feucht 45–80 %)
  bleiben für die untere Schwelle fast gleich (A neu 15 statt 10 %). Die **obere Grenze** wird angehoben und erst
  nach einer **Karenz von 48 h** nach einer erkannten Giessung bewertet; sonst würde jede richtige, durchdringende
  Giessung (Ziel ≥ 80 %) sofort „zu nass“ melden. Zu entscheiden durch den Auftraggeber (Kap. 6).
- Karenz 48 h, Ziel 80 % und alle Prozentwerte: **ANNAHME**, PROTOTYP-PRÜFUNG.
- Art-spezifische Abweichungen stehen in `species[].start` und sind in der Tabelle begründet (z. B. Glücksfeder 10 %
  wegen „completely dried“, Schwertfarn 50 % wegen „never be allowed to dry out“, Peperomie 25 % wegen
  „intolerant of wet soil“).

### 4.3 Logik in der App
1. **Trockenphase (nur Regime A):** Nach einer erkannten Giessung bis zum Erreichen der Schwelle gilt der Zustand
   *Trockenphase*. Anzeige: „**Trockenphase erwünscht – noch nicht giessen**“ (Prognose: „giessen in ~9 Tagen“).
   Drückt der Nutzer „Gegossen“ oder wird eine Giessung erkannt, solange der Wert mehr als 15 %-Punkte über der
   Schwelle liegt, erscheint ein freundlicher Hinweis „Früher gegossen als das Profil vorsieht – diese Art mag
   zwischendurch trocken stehen“. Kein Alarm, keine LED.
2. **Regime B:** wie bisher (`ok` → `due`). Hinweis „früh gegossen“ erst bei > 25 %-Punkten über der Schwelle.
3. **Regime C:** Vorwarnung „bald giessen“ bereits 10 %-Punkte über der Schwelle (LED bleibt grün); Stimmung
   *sehr durstig* schon 5 statt 10 %-Punkte unter der Schwelle, weil Austrocknen hier schadet.
4. **Durchdringend gegossen?** (A und B, C): Erreicht die Spitze nach einer Giessung das Ziel (80 %) nicht, Hinweis
   „Vielleicht nicht durchdringend gegossen – giessen, bis unten Wasser austritt, Untersetzer leeren“.
5. **Zu nass:** Wert über `upper_pct` länger als 48 h nach der letzten Giessung → Stimmung *zu nass*, Text je
   Regime (A: „Diese Art verträgt Staunässe schlecht – Abzugsloch/Untersetzer prüfen“).
6. **D:** keine Schwelle; Erinnerung nach Tagen (Orchidee: Startwert 7 Tage laut AOS „once a week“), Sensor optional;
   bei Hydrokultur Hinweis „fluidi misst keinen Wasserstand – Wasserstandsanzeiger nutzen“.
7. **Prognose:** unverändert (Kap. 8.4); bei A zusätzlich Dauer der Trockenphase anzeigen.

### 4.4 Winteranpassung
- Winterschwelle = `round(water_at_pct × winter_factor)`, Standard-Wintermonate **November–Februar** (ANNAHME,
  Nordhalbkugel, geheiztes Büro); in den Einstellungen änderbar oder je Pflanze abschaltbar.
- Begründung: fast alle Quellen verlangen im Winter weniger Wasser bzw. stärkeres Abtrocknen (Bogenhanf „only every
  one to two months“, Kakteen „minimal or no watering“, Zitrus „err on the dry side“, Strelitzie „fairly dry“).
- Die Prognose passt sich ohnehin an, weil die Austrocknungsrate `k` im Winter sinkt; der Winterfaktor verschiebt nur
  die Schwelle. Kakteen mit Faktor 0.3: praktisch kein Giesshinweis im Winter. Schrumpfen kann fluidi nicht
  messen → fester Hinweistext „Winterruhe: nur giessen, wenn die Pflanze schrumpft“.

### 4.5 Anpassen durch den Nutzer
- Alle Werte sind als Pille **„Startwert“** markiert (`source: startwert`); der Nutzer kann Schwelle, Obergrenze,
  Winterfaktor und Regime ändern.
- Nach **3–4 Zyklen** schlägt die App vor (keine Automatik, SOFTWARE_CONCEPT Kap. 9): „Du giesst meist bei 22 %“
  → Schwelle übernehmen? Zusätzlich bei A: „Die Trockenphase dauert bei dir ~8 Tage“.
- Rückfrage beim Giessen (optional, eine Taste): „Fingerprobe oben trocken? ja/nein“ – liefert pro Pflanze den
  Indexwert, der der Quellenregel entspricht (Grundlage für Vorschläge).

## 5 Grenzen
- Die Quellen sind überwiegend US-/UK-Merkblätter; Licht, Temperatur, Topfgrösse und Substrat verändern das
  Giessintervall stark – das Regime ist eine Richtung, keine Tagesangabe.
- Für Yucca, Olive (geheizter Raum), Alocasia und Kentia fehlt eine seriöse Angabe zur Abtrocknungstiefe; die
  Einordnung ist dort ANNAHME (in der Tabelle vermerkt). Bei Ficus benjamina, Hoya und Basilikum widersprechen sich
  die Quellen.
- Hydrokultur: nur Händlerquellen.

## 6 Offene Punkte für den Auftraggeber
1. Obere Grenzen anheben und 48-h-Karenz einführen (Kap. 4.2) – ja/nein?
2. Efeutute von „mittel“ auf „trocken / A“ umstellen?
3. Nachfrage „Fingerprobe“ beim Giessen anbieten (Kap. 4.5)?
4. Wintermonate November–Februar als Standard?

## 7 Quellen (alle abgerufen am 2026-11-07)

| ID | Titel | Herausgeber | URL | Abruf |
|---|---|---|---|---|
| S01 | Monstera deliciosa | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/monstera-deliciosa/> | 2026-11-07 |
| S02 | HGIC 1509 Philodendron, Pothos & Monstera | Clemson Cooperative Extension HGIC | <https://hgic.clemson.edu/factsheet/philodendron-pothos-monstera/> | 2026-11-07 |
| S03 | Plant Information FAQ: Fiddle-leaf fig | New York Botanical Garden | <https://libanswers.nybg.org/faq/332601> | 2026-11-07 |
| S04 | Fiddle Leaf Fig Houseplant Proper Care (Coastal Gardener) | UC ANR | <https://ucanr.edu/blog/coastal-gardener/article/fiddle-leaf-fig-houseplant-proper-care> | 2026-11-07 |
| S05 | HGIC 1514 Weeping Ficus | Clemson Cooperative Extension HGIC | <https://hgic.clemson.edu/factsheet/weeping-ficus/> | 2026-11-07 |
| S06 | Ficus benjamina | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/ficus-benjamina/> | 2026-11-07 |
| S07 | Plant Information FAQ: Ficus benjamina | New York Botanical Garden | <https://libanswers.nybg.org/faq/223502> | 2026-11-07 |
| S08 | HGIC 1510 Rubber Plant | Clemson Cooperative Extension HGIC | <https://hgic.clemson.edu/factsheet/rubber-plant/> | 2026-11-07 |
| S09 | Ficus elastica | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/ficus-elastica/> | 2026-11-07 |
| S10 | HGIC 1568 How to Grow Pothos Indoors | Clemson Cooperative Extension HGIC | <https://hgic.clemson.edu/factsheet/how-to-grow-pothos-indoors-epipremnum-spp-care-cultivars-and-common-problems/> | 2026-11-07 |
| S11 | Epipremnum aureum | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/epipremnum-aureum/> | 2026-11-07 |
| S12 | Dracaena trifasciata | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/dracaena-trifasciata/> | 2026-11-07 |
| S13 | Sansevieria trifasciata (Plant Finder) | RHS | <https://www.rhs.org.uk/Plants/16430/Sansevieria-trifasciata/Details> | 2026-11-07 |
| S14 | HGIC 1570 ZZ Plant | Clemson Cooperative Extension HGIC | <https://hgic.clemson.edu/factsheet/zz-plant-zamioculcas-zamiifolia-indoor-care-growing-tips-plant-guide/> | 2026-11-07 |
| S15 | Zamioculcas zamiifolia | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/zamioculcas-zamiifolia/> | 2026-11-07 |
| S16 | Houseplant cacti and succulents: growing guide | RHS | <https://www.rhs.org.uk/plants/types/cacti-succulents/houseplants/growing-guide> | 2026-11-07 |
| S17 | Plant Information FAQ: Cactus watering | New York Botanical Garden | <https://libanswers.nybg.org/faq/222795> | 2026-11-07 |
| S18 | Growing Succulents Indoors | Iowa State University Extension | <https://yardandgarden.extension.iastate.edu/how-to/growing-succulents-indoors> | 2026-11-07 |
| S19 | Echeveria | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/echeveria/> | 2026-11-07 |
| S20 | Aloe vera | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/aloe-vera/> | 2026-11-07 |
| S21 | Philodendron hederaceum | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/philodendron-hederaceum/> | 2026-11-07 |
| S22 | HGIC 1511 Schefflera | Clemson Cooperative Extension HGIC | <https://hgic.clemson.edu/factsheet/schefflera-2/> | 2026-11-07 |
| S23 | Schefflera arboricola | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/schefflera-arboricola/> | 2026-11-07 |
| S24 | Dracaena | Clemson Cooperative Extension HGIC | <https://hgic.clemson.edu/factsheet/dracaena/> | 2026-11-07 |
| S25 | How to grow dracaena | RHS | <https://www.rhs.org.uk/plants/dracaena/how-to-grow-dracaena> | 2026-11-07 |
| S26 | Yucca gigantea | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/yucca-gigantea/> | 2026-11-07 |
| S27 | How to grow strelitzia | RHS | <https://www.rhs.org.uk/plants/strelitzia/how-to-grow-strelitzia> | 2026-11-07 |
| S28 | Howea forsteriana | RHS Plants (Pflanzenshop der RHS, halb Händler) | <https://www.rhsplants.co.uk/plants/_/howea-forsteriana/classid.2000027701> | 2026-11-07 |
| S29 | Howea forsteriana | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/howea-forsteriana/> | 2026-11-07 |
| S30 | Dypsis lutescens | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/dypsis-lutescens/> | 2026-11-07 |
| S31 | Citrus: grow your own | RHS | <https://www.rhs.org.uk/fruit/citrus/grow-your-own> | 2026-11-07 |
| S32 | Growing dwarf citrus | University of Maryland Extension | <https://extension.umd.edu/resource/growing-dwarf-citrus> | 2026-11-07 |
| S33 | Container Citrus Production | Clemson Cooperative Extension HGIC | <https://hgic.clemson.edu/factsheet/container-citrus-production/> | 2026-11-07 |
| S34 | How to grow olives | RHS | <https://www.rhs.org.uk/plants/olives/how-to-grow-olives> | 2026-11-07 |
| S35 | Basil: grow your own | RHS | <https://www.rhs.org.uk/herbs/basil/grow-your-own> | 2026-11-07 |
| S36 | Growing Herbs Indoors | Iowa State University Extension | <https://yardandgarden.extension.iastate.edu/how-to/growing-herbs-indoors> | 2026-11-07 |
| S37 | Growing English Ivy Indoors | Clemson Cooperative Extension HGIC | <https://hgic.clemson.edu/factsheet/growing-english-ivy-indoors/> | 2026-11-07 |
| S38 | Aglaonema | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/aglaonema/> | 2026-11-07 |
| S39 | Dieffenbachia seguine | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/dieffenbachia-seguine/> | 2026-11-07 |
| S40 | Jade Plant, Crassula ovata | University of Wisconsin-Madison Division of Extension Horticulture | <https://hort.extension.wisc.edu/articles/jade-plant-crassula-ovata/> | 2026-11-07 |
| S41 | Jade Plant - A No-Fuss Houseplant | Penn State Extension | <https://extension.psu.edu/jade-plant-a-no-fuss-houseplant> | 2026-11-07 |
| S42 | Crassula ovata | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/crassula-ovata/> | 2026-11-07 |
| S43 | Chamaedorea elegans | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/chamaedorea-elegans/> | 2026-11-07 |
| S44 | Hydrocare houseplants: the ultimate in easy care | Hortology (HÄNDLER) | <https://hortology.co.uk/blogs/guides-to-greenery/hydrocare-houseplants-the-ultimate-in-easy-care> | 2026-11-07 |
| S45 | Houseplants in hydroponics (schwedische Seite) | Bosch DIY (HÄNDLER) | <https://www.bosch-diy.com/se/sv/all-about-diy/houseplants-in-hydroponics> | 2026-11-07 |
| S46 | Goeppertia makoyana | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/goeppertia-makoyana/> | 2026-11-07 |
| S47 | Calathea | RHS | <https://www.rhs.org.uk/plants/calathea> | 2026-11-07 |
| S48 | Maranta leuconeura | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/maranta-leuconeura/> | 2026-11-07 |
| S49 | Nephrolepis exaltata | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/nephrolepis-exaltata/> | 2026-11-07 |
| S50 | Spathiphyllum | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/spathiphyllum/> | 2026-11-07 |
| S51 | Chlorophytum comosum | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/chlorophytum-comosum/> | 2026-11-07 |
| S52 | Phalaenopsis (C. Sullivan), PDF | American Orchid Society | <https://secure.aos.org/media/Content-Images/PDFs/Phalaenopsis_novice.pdf> | 2026-11-07 |
| S53 | New Member Lesson 4: Water Requirements | American Orchid Society | <https://www.aos.org/new-member-lesson-4-water-requirements> | 2026-11-07 |
| S54 | Pilea | RHS | <https://www.rhs.org.uk/plants/pilea> | 2026-11-07 |
| S55 | Pilea peperomioides | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/pilea-peperomioides/> | 2026-11-07 |
| S56 | Peperomia | RHS | <https://www.rhs.org.uk/plants/peperomia> | 2026-11-07 |
| S57 | Peperomia obtusifolia | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/peperomia-obtusifolia/> | 2026-11-07 |
| S58 | Anthurium andraeanum | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/anthurium-andraeanum/> | 2026-11-07 |
| S59 | Begonias: houseplants | RHS | <https://www.rhs.org.uk/plants/begonias> | 2026-11-07 |
| S60 | Alocasia × amazonica | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/alocasia-x-amazonica/> | 2026-11-07 |
| S61 | Alocasia | RHS | <https://www.rhs.org.uk/plants/alocasia> | 2026-11-07 |
| S62 | Hoya carnosa | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/hoya-carnosa/> | 2026-11-07 |
| S63 | Hoya | RHS | <https://www.rhs.org.uk/plants/hoya> | 2026-11-07 |
| S64 | HGIC 1459 Indoor Plants - Watering | Clemson Cooperative Extension HGIC | <http://hgic.clemson.edu/factsheet/indoor-plants-watering/> | 2026-11-07 |
| S65 | Ficus lyrata | NC State Extension Plant Toolbox | <https://plants.ces.ncsu.edu/plants/ficus-lyrata/> | 2026-11-07 |
