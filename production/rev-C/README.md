# fluidi – Release-Paket Rev C (Sensor + Gateway-Druckteile)

| | |
|---|---|
| Erzeugt | 2026-11-08T14:45:46+01:00 von `.venv/bin/python production/make_release_rev_c.py` |
| Git-Stand | `16a1c84` |
| Bestellunterlage | `2_bestellung/ORDER_JLC_REV_C.md` (Kap. 1: Soll-sha256 der Upload-Dateien) |
| Prüfen | `cd production/rev-C && sha256sum -c SHA256SUMS` |
| Status | **Keine Bestellung ausgelöst.** Bestellen nur nach Freigabe durch den Auftraggeber (`2_bestellung/BESTELLEN_JLC.md`) |

Alle Dateien sind **Kopien** (keine Neuerzeugung); jede Kopie wurde beim Erzeugen per sha256 mit der Quelle verglichen. Die drei Upload-Dateien in `1_jlc_upload/` entsprechen den Hashes in ORDER_JLC_REV_C.md Kap. 1 (sonst bricht das Skript ab).

| Datei im Paket | Quelle im Repo | sha256 | Bytes | Zweck | geändert* |
|---|---|---|---|---|---|
| `1_jlc_upload/fluidi_sensor_gerber_jlc.zip` | `hardware/sensor/out/fluidi_sensor_gerber_jlc.zip` | `bf1902ea4bab83d96f385f557575d8311886acf2bacee7aa743d88eef47883d0` | 154032 | Gerber + Bohrdaten + Job (Upload JLC, PCB) |  |
| `1_jlc_upload/fluidi_sensor_bom_jlc.csv` | `hardware/sensor/out/fluidi_sensor_bom_jlc.csv` | `3d99ffca7b79abe550a57de4ff7d3228eabe4f532bc46f602e6bcec53f456ea9` | 1204 | BOM JLC-Format (Upload PCBA) |  |
| `1_jlc_upload/fluidi_sensor_cpl_jlc.csv` | `hardware/sensor/out/fluidi_sensor_cpl_jlc.csv` | `b01ba1477406d8c305693567ca70011ccb60892215ccc055ee17d99f6329213f` | 1634 | CPL JLC-Format (Upload PCBA) |  |
| `2_bestellung/ORDER_JLC_REV_C.md` | `hardware/sensor/out/ORDER_JLC_REV_C.md` | `fba07bf25ce8da1ec14f21ec1ecd28fa7275b41a71988b2ae7d49de242d34826` | 27251 | Bestellunterlage mit Checklisten (Kap. 4/5) und Remark (Kap. 8) |  |
| `2_bestellung/BESTELLEN_JLC.md` | `docs/manuals/BESTELLEN_JLC.md` | `1a61095052e1e0b3a19977ecd557fa675518bd34543a36a496c49dde7b62bc3f` | 15567 | Schritt-für-Schritt-Anleitung JLC-Formular |  |
| `2_bestellung/REMARK_JLC_REV_C.txt` | `hardware/sensor/out/REMARK_JLC_REV_C.txt` | `54ddcd49be85d56ff3377fcf55d2b8c94d90c50d529c916394d61825017b3dff` | 563 | Remark-Text zum Kopieren (eine Zeile, ohne Markdown) |  |
| `2_bestellung/fluidi_sensor_bom_extra.csv` | `hardware/sensor/out/fluidi_sensor_bom_extra.csv` | `6a8b983e697f65643d41ab92f3fc63b960eebf1b1de11b7c0f8c48f5d10636b0` | 739 | Teile ohne JLC-Bestückung (lokal, DNP, Leiterplattenstrukturen) |  |
| `2_bestellung/fluidi_sensor_cpl_jlc_rotationen.csv` | `hardware/sensor/out/fluidi_sensor_cpl_jlc_rotationen.csv` | `2f6fce43c8ca7b199dbfb2a6f3397be8078cd02e6cfd887d535b5206d2219653` | 2181 | Rotationskorrekturen CPL (für Confirm Parts Placement) |  |
| `2_bestellung/fluidi_sensor_bestueckung_F.pdf` | `hardware/sensor/out/pdf/fluidi_sensor_bestueckung_F.pdf` | `bcf850d67437ab2722c7b5f030b858ec9b4674cdefc2933d15e79574b182fce9` | 173080 | Bestückungsansicht Oberseite mit Pin-1 (Vorschau-Vergleich) |  |
| `2_bestellung/fluidi_sensor_layout_lagen.pdf` | `hardware/sensor/out/pdf/fluidi_sensor_layout_lagen.pdf` | `e667c5f805c2e7fd0b16bcf6aa4b3a35740d2ce5bd454dba2ce6cc4b305101cf` | 505130 | alle Lagen als PDF |  |
| `2_bestellung/fluidi_sensor_schematic.pdf` | `hardware/sensor/out/fluidi_sensor_schematic.pdf` | `9c3feb2731d78e1992a1fd9bd28343f33fa4358a7dae27e2f1b4e0a2dc367942` | 232916 | Schaltplan Rev C |  |
| `2_bestellung/COSTS_REV_B.md` | `hardware/sensor/out/COSTS_REV_B.md` | `a9b154a2a6c1b9e3744844ef3249508b72f40a80b44a302ea36411e751e36d94` | 18636 | Kostenrechnung Sensor (cost_rev_b.py) |  |
| `2_bestellung/phase5_kosten_final.md` | `docs/reviews/phase5_kosten_final.md` | `a55bc9d3768022a80b8913a7643f53ee1e09ed00261b7c4fafa07ece2d633a5a` | 21215 | Kosten final Sensor/Gateway/System |  |
| `3_druck/sensor/distanzlehre_24p2.3mf` | `mechanical/sensor/print/distanzlehre_24p2.3mf` | `c68d03b1653ba4af100ba79bea86ef3550d0a66d6be18ca76dd894103c253434` | 1117 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/distanzlehre_24p2.step` | `mechanical/sensor/print/distanzlehre_24p2.step` | `2a7bc2f1bf606958aba7dca1a8dabfeb83586ea348ed643e42ff5aa8b35df92e` | 6921 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/distanzlehre_24p2.stl` | `mechanical/sensor/print/distanzlehre_24p2.stl` | `e388258563a8ebdf0beb1f8d127463adaadd35b64adde84fd7d44b313bce0658` | 684 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/fenster_tropfen.3mf` | `mechanical/sensor/print/fenster_tropfen.3mf` | `2772b40975c6a736e73d83b1e3147b9fb61ffb060ccc55e113f8c312675afeba` | 5060 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/fenster_tropfen.step` | `mechanical/sensor/print/fenster_tropfen.step` | `a0ebf32db09e1853db999b90ea5058fe2aa30b2187953d0a608960c2b8f7593b` | 85607 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/fenster_tropfen.stl` | `mechanical/sensor/print/fenster_tropfen.stl` | `0cde0fd5c665a7db7d5418dcc7569b67d2cb3eed6df1761338dbe711a025aa64` | 22484 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/huelse_grau.3mf` | `mechanical/sensor/print/huelse_grau.3mf` | `fdbdbbb01567b61b618ffb4e2f51382438a849115e3faf6386b91ed9725c887d` | 109130 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/huelse_grau.step` | `mechanical/sensor/print/huelse_grau.step` | `16e00a05c636341505ac89efa0b798c847f9db1c91e7ce658addf79a2d3201e2` | 1243688 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/huelse_grau.stl` | `mechanical/sensor/print/huelse_grau.stl` | `08df24689424019f599ac10d5f27e24c045ca163b84ea4f3badda58aa2c0e280` | 519784 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/kappe_blau.3mf` | `mechanical/sensor/print/kappe_blau.3mf` | `841f2ebeced2d7583b00b3ab87f76991dc0d930acd029ae15274e10ee3ec4264` | 37973 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/kappe_blau.step` | `mechanical/sensor/print/kappe_blau.step` | `3dc0796f38d1de723d90cc4a8c8beb17e7a4c7f7280e5153acb58834077f174d` | 264162 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/kappe_blau.stl` | `mechanical/sensor/print/kappe_blau.stl` | `5b1742b450248a4f72d04c279b03f998d4ab6f92252aa1eb3a9d55232fe9c9ff` | 186684 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/klemmring.3mf` | `mechanical/sensor/print/klemmring.3mf` | `c9bb88a500c966e99b7052a2e6e068750203623401c927e6e90bff471109f73b` | 8027 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/klemmring.step` | `mechanical/sensor/print/klemmring.step` | `35683b2b37e1114ff778ce0784e64ddeb7b26cbea1ffeb090954c0f5bbf6d02c` | 7127 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/klemmring.stl` | `mechanical/sensor/print/klemmring.stl` | `7bb0c0b65bd3da2424f73d3fb0ef58489f404759942e0dee0df9bbb848a6f833` | 37884 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/kragen.3mf` | `mechanical/sensor/print/kragen.3mf` | `d2719670988227fa59d95fcb20260aea479e45dd4f3eed08b3807f1d6b3f25d0` | 13790 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/kragen.step` | `mechanical/sensor/print/kragen.step` | `08142822a258d16278549d9d6564adc61cfb2c9332f93b7fba513bc79835b459` | 72106 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/kragen.stl` | `mechanical/sensor/print/kragen.stl` | `b447f06b8d12754715e3ff286b0f808d4b3719effa36c471e35b42b9c16b8ce9` | 72684 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/passprobe_huelse_oben.3mf` | `mechanical/sensor/print/passprobe_huelse_oben.3mf` | `0f1a4bc57262f3781d1ae465fb4da7881b50d5c86b7407910375003c1077017f` | 6450 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/passprobe_huelse_oben.step` | `mechanical/sensor/print/passprobe_huelse_oben.step` | `6e59af2771ae4edc95393061377f19d4bbc5dd3e64f47885ee5f35ccd4a772ed` | 123592 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/passprobe_huelse_oben.stl` | `mechanical/sensor/print/passprobe_huelse_oben.stl` | `6e9ab159735b13bf37dbf0252869f71401985d31252e6e5fc5c0b0e1412b2ecc` | 31884 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/passprobe_huelse_unten.3mf` | `mechanical/sensor/print/passprobe_huelse_unten.3mf` | `2c9f587f474f8cd72f09d38663f2bbfd58f862900361f457e83dc23777e3da1e` | 8766 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/passprobe_huelse_unten.step` | `mechanical/sensor/print/passprobe_huelse_unten.step` | `e1914f5fe0be5cde782c4cc554464484832b78ab9cc9eb19577d7f72537a4988` | 31109 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/passprobe_huelse_unten.stl` | `mechanical/sensor/print/passprobe_huelse_unten.stl` | `e23734f3c0c8fcdd75118d535f662f80712ec82846093cd5ee3de3091fe0ed7f` | 42284 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/schottkeil.3mf` | `mechanical/sensor/print/schottkeil.3mf` | `82e5421bc12cb40bb064acc299616c49ea358bff6b4508a102c6f6e9e624e6f3` | 1120 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/schottkeil.step` | `mechanical/sensor/print/schottkeil.step` | `ec878f55d74bf9628c181f87b3fa0b75cd7bb5f67776b333ba336aac26d20706` | 7042 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/schottkeil.stl` | `mechanical/sensor/print/schottkeil.stl` | `c3c6380ebfa242d1f76b6e9d0d45d983d3b0018a73127a2470bf69a12116f95d` | 684 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/stoessel.3mf` | `mechanical/sensor/print/stoessel.3mf` | `3f4ad157dd867e636ef22c5929cbec662ae75a63c4e7a519d20f2346c71b126e` | 3841 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/stoessel.step` | `mechanical/sensor/print/stoessel.step` | `20c728f31fe87067985514ec4275122a1db50c0efba5810c906be92769f7ac93` | 15560 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/stoessel.stl` | `mechanical/sensor/print/stoessel.stl` | `247cae72c9e3a16a4cdf9f468332e0415a26cb6c3b6806a71dea4a23e725f474` | 12784 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/taste_blau.3mf` | `mechanical/sensor/print/taste_blau.3mf` | `8fe6aa6103052f414cf495f8043a201b6f3bbc8e4a2f0ce090e7fd769a268849` | 3915 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/taste_blau.step` | `mechanical/sensor/print/taste_blau.step` | `187eec8c67c8269e8987fd5c0720969e556438a26a20feeab4ae29bc7874b8d0` | 16978 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/taste_blau.stl` | `mechanical/sensor/print/taste_blau.stl` | `6f40909c6e7ae6ef2b0a25e68f76b1f6754f26fed522316916a4a67ae212ca0f` | 14384 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/tastenteller.3mf` | `mechanical/sensor/print/tastenteller.3mf` | `7b5b3bc9a437b9e7f92911e423050ecc6fa723b001b3a1b4d965080618b0f344` | 5512 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/tastenteller.step` | `mechanical/sensor/print/tastenteller.step` | `e40d5df34e980fd0b92de2be265a192523c23a66166377e91e3a47343f9644b6` | 4966 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/tastenteller.stl` | `mechanical/sensor/print/tastenteller.stl` | `b3919c2ad5f4fa81dc5ca2de6df97fdef84fbc275554420625155ae62c586b45` | 25284 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/gateway_pi/deckel_blau.3mf` | `mechanical/gateway_pi/print/deckel_blau.3mf` | `c8395a12c20d3a95af8fe5a8b263cd424b6be8abc82bcacdf9dc15674829c566` | 34068 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/deckel_blau.step` | `mechanical/gateway_pi/print/deckel_blau.step` | `2a3998f31795a78ed8c3fb132e4d03ec32167dbe56f8e5ca71e40aaebaf69658` | 177142 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/deckel_blau.stl` | `mechanical/gateway_pi/print/deckel_blau.stl` | `c86b8a19e1b1bf542a6048c7b0435116e62e20146a4e99aa4f3b82018c5c7902` | 176884 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/fenster_tropfen_gw.3mf` | `mechanical/gateway_pi/print/fenster_tropfen_gw.3mf` | `3993c51b8e6a338952ef1cb1a178051acd77b30e351e46ae2e7ef62bc886a102` | 2629 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/fenster_tropfen_gw.step` | `mechanical/gateway_pi/print/fenster_tropfen_gw.step` | `14eb770ee1bf6da450a8d20047055f55eb229d709b69e9e4fecf77e632f8c6c6` | 81182 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/fenster_tropfen_gw.stl` | `mechanical/gateway_pi/print/fenster_tropfen_gw.stl` | `a4be4bc39547086b32167659a239f92bb63b6d4e1e1b502c40321fabb17b94f6` | 9884 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau.3mf` | `mechanical/gateway_pi/print/wanne_grau.3mf` | `880d578b1a3265f9bb065689df31d05e35799276ec9ec1d991a6b3cdde784c82` | 51767 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau.step` | `mechanical/gateway_pi/print/wanne_grau.step` | `212b3b87ee38be966e39f16363fd10743f4e2a0904d3a4b40093fd36701945a2` | 535089 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau.stl` | `mechanical/gateway_pi/print/wanne_grau.stl` | `9fa271afe0e18af646551d6a817d22b4a609bb9d5c227d1d50a031c6fb3c329f` | 261984 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau_otg.3mf` | `mechanical/gateway_pi/print/wanne_grau_otg.3mf` | `68cb1520ee0dc78f3a7043f9c3c61a8536248e0404bd47eccaefef46b53c1cbe` | 51877 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau_otg.step` | `mechanical/gateway_pi/print/wanne_grau_otg.step` | `5f3a2c6a8330f2a489b785268d76fa16bdf261d893d9bdaffb7a9251c778295f` | 540366 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau_otg.stl` | `mechanical/gateway_pi/print/wanne_grau_otg.stl` | `ea8f93116d0404733da21a8fece38abb00f2eadfe109642bcd0503b0b2e0dc1a` | 262984 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/PRINT_SETTINGS.md` | `mechanical/PRINT_SETTINGS.md` | `c8be0f90981b1da47fce051d57460a2d1878e90b446c7bcd1d127d54ddd608a0` | 12441 | Druckeinstellungen |  |
| `4_gateway/BOM_GATEWAY.csv` | `hardware/gateway/BOM_GATEWAY.csv` | `a1af471795513d1d961ae36aecb3308e0275aa0c9958108a2a682d4eac0cb714` | 5196 | Gateway-Stückliste mit Preisen und Quellen (W-8) |  |
| `4_gateway/GATEWAY_SETUP.md` | `docs/manuals/GATEWAY_SETUP.md` | `c20cfe59e41f165422a32b16451fd181f4348387ea34e4f776f724856b1afb62` | 13773 | Gateway einrichten |  |
| `5_firmware/PROGRAMMIEREN_SENSOR.md` | `docs/manuals/PROGRAMMIEREN_SENSOR.md` | `b8f99ae4926d465b5b016de0ff5b35086880cd87c88030dec8910035cdc85878` | 14488 | Erstprogrammierung Sensor |  |
| `5_firmware/FIRMWARE_HINWEIS.md` | `(erzeugt von production/make_release_rev_c.py)` | `97974e56981d25ce1e10e4a80773034bd02d68a3ebba4e48b6fff2f93d45237a` | 981 | Firmware-Hinweis |  |

*geändert = Quelle hat beim Erzeugen nicht committete Änderungen (Arbeitskopie). Nach dem Commit das Paket neu erzeugen, damit Git-Stand und Inhalt übereinstimmen.

Nicht im Paket: Programmieradapter (`hardware/programmer/`), Gateway-Software (`firmware/gateway/`), PWA (`app/`), alte ESP32-Gateway-Druckteile (`mechanical/gateway/`, durch D-014 ersetzt).
