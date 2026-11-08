# fluidi Sensor – Batterie wechseln

Für alle, die den Sensor benutzen. Dauer etwa 5 Minuten. Bild: `renders/final/fluidi_04_batteriewechsel.png`
(graue Hülse halb nach unten abgezogen, die Knopfzelle ist sichtbar).

## Zuerst lesen: Sicherheit

> **Warnung – Knopfzelle verschlucken ist lebensgefährlich.**
> Eine verschluckte Lithium-Knopfzelle kann in kurzer Zeit schwere innere Verätzungen verursachen.
> - Neue und alte Zellen **ausser Reichweite von Kindern und Haustieren** aufbewahren.
> - **Besteht der Verdacht, dass eine Zelle verschluckt oder in den Körper eingeführt wurde: sofort ärztliche Hilfe holen**
>   (Notruf **144**, Tox Info Suisse **145**, https://www.toxinfo.ch). Nicht abwarten, bis Beschwerden auftreten.
> - Das Batteriefach muss nach dem Wechsel **immer vollständig geschlossen und verschraubt** sein. Lässt es sich nicht
>   schliessen: Zelle herausnehmen und den Sensor nicht mehr benutzen.
>
> Quellen: `docs/appnotes/Renata_3VLithium_SafetyGuidelines.pdf` (Rev. 10/02), `docs/reviews/phase3_sleeve_sicherheit.md`
> Kap. 3, `docs/reviews/phase5_fmea_light.md` F-20 … F-25.

- **Ersatzzellen** in der **Originalverpackung** lassen (kindergesichert) und erst beim Wechsel öffnen. Keine losen Zellen
  in Schubladen oder Taschen.
- **Altzelle sofort entsorgen:** beide Seiten mit Klebeband abkleben (kein Kurzschluss) und zur Batterie-Sammelstelle
  bringen (Verkaufsstellen nehmen Batterien zurück). Nicht in den Hausmüll, nicht ins Feuer.
- Zellen **nicht laden, nicht erwärmen, nicht öffnen**, nicht auf leitende Unterlagen legen (Renata Safety Guidelines).
- **Kein Metallwerkzeug** zum Herausdrücken der Zelle (Kurzschluss zwischen Clip und Minuspad, Beschädigung des Clips).
- Den Sensor nicht in Reichweite von Kleinkindern und Haustieren aufstellen (FMEA F-25).
- Nur **CR2032 der Marke laut Stückliste** verwenden (Panasonic CR2032, REQ-ENE-08), nur neue Zellen.
- Die Sondenspitze ist spitz: beim Herausziehen und Reinigen nicht gegen die Hand führen.
- **Beschädigte, verformte oder ausgelaufene Zellen** nicht einsetzen; ausgelaufene Zelle nur mit Handschuhen anfassen,
  abgeklebt entsorgen, Fach trocken auswischen.
- Sensor **nicht auf oder neben den Heizkörper** und nicht in die pralle Mittagssonne hinter Glas stellen (Zellentemperatur).

## Was Sie brauchen

- 1 neue Knopfzelle **CR2032** (Panasonic, Originalverpackung)
- **Torx-Schraubenzieher TX6** (T6; für die Schraube an der Kopfunterseite, neben der Sonde)
- Weiches Tuch, Wasser; eine **Schale** als Unterlage (falls die Zelle herausfällt, rollt sie nicht weg)
- Zahnstocher oder Kunststoffspatel (kein Metall)

## Schritte

1. **Sensor herausziehen** am Kopf, gerade nach oben. **Sonde reinigen** und trocknen (Erde würde beim Abziehen der
   Hülse an der Dichtung schleifen).
2. Über der Schale arbeiten. Sensor mit der **Sondenspitze nach oben** halten. Die Schraube sitzt an der Kopfunterseite
   **neben der Sonde** (zeigt jetzt nach oben). **Schraube lösen** (TX6, gegen den Uhrzeigersinn), **etwa 4 Umdrehungen,
   bis sich die Hülse abziehen lässt – nicht weiter drehen**, sonst fällt die Schraube heraus (R3-W1). Eine
   Ersatzschraube M2×3 bereithalten.
3. **Graue Hülse Richtung Sondenspitze von der Kappe wegziehen und über die Sonde abziehen** (wie im Bild). Nicht an der
   blauen Kappe drücken. Innen an der Rückwand sehen Sie das Warnsymbol „CR2032 Verschluckgefahr“.
4. **Alte Zelle herausschieben:** Sensor wieder normal halten (Kopf oben, Tropfenfenster zu Ihnen). Von vorne gesehen sitzt die Zelle rechts offen im Halter. Mit dem Fingernagel oder
   einem Zahnstocher **nach rechts** aus dem Halter schieben. Nicht hebeln. Altzelle sofort abkleben (siehe oben).
   **Taste oben am Kopf jetzt nicht drücken.**
5. Ist im Fach Wasser oder Feuchtigkeit: siehe „Wasser im Kopf“ unten, nicht weitermachen.
6. **Neue Zelle einsetzen:** Pluspol (beschriftete Seite) **nach vorne**, von rechts flach einschieben, bis sie am
   linken Anschlag anliegt. Sie sitzt gerade und bündig, nicht schräg. **Dabei die Taste nicht berühren.**
7. **LED beobachten:** Kurz nach dem Einsetzen blinkt die LED einmal grün (Selbsttest ok). Rot bedeutet Fehler, siehe
   Fehlersuche. Kommt **gar kein Signal**: zuerst die **Polung** prüfen (Pluspol nach vorne, Schritt 6). Dann Zelle 10 Sekunden herausnehmen und ohne die Taste zu berühren wieder einsetzen
   (`docs/manuals/PROGRAMMIEREN_SENSOR.md` Kap. 6).
8. **Dichtringe prüfen:** Die zwei roten bzw. durchsichtigen Gummiringe (oben und unten) sitzen in ihren Nuten, sind
   nicht verdreht und nicht beschädigt. Trocken wirkende Ringe dünn mit Silikonfett einreiben.
9. **Hülse wieder aufschieben**, bis der obere Rand ganz unter der blauen Kappe sitzt (gleichmässige Fuge).
10. **Schraube anziehen** (im Uhrzeigersinn), bis sie fest ist. Nicht überdrehen.
11. **Kontrolle (Pflicht):** Die Hülse lässt sich **von Hand nicht abziehen** und die Fuge ist rundum gleich. Erst dann
    den Sensor wieder einstecken (in fester Erde mit einem Stab vorstechen). **Beim Einstecken am Kopf seitlich bzw. an
    der Hülse greifen, nicht auf die Taste oben drücken** (die Taste ist dafür nicht ausgelegt, Red Team C-2).

## Wasser im Kopf

Wenn beim Öffnen Wasser oder Kondensat im Fach ist:

1. Zelle sofort herausnehmen (Schritt 4) und abgeklebt entsorgen. Nicht wieder einsetzen.
2. Hülse und Fach offen trocknen lassen (Raumtemperatur, nicht auf die Heizung).
3. Dichtringe auf Beschädigung prüfen, Schraube und Fuge prüfen.
4. Den Fall melden (Projektleitung). Ein Sensor, in dem wiederholt Wasser steht, wird nicht mehr verwendet.

## Wann wechseln?

Die App warnt, wenn die geschätzte Restlaufzeit unter 30 Tage fällt (REQ-ENE-05). Eine leere Zelle nicht im Gerät lassen
(FMEA F-13).
