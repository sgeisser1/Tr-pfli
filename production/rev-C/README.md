# fluidi – Release-Paket Rev C (Sensor, Gateway, Anleitungen, Quellcode; Stand Phase 6)

| | |
|---|---|
| Erzeugt | 2026-11-09T01:07:40+01:00 von `.venv/bin/python production/make_release_rev_c.py` |
| Git-Stand | `9c39ce8` |
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
| `2_bestellung/COSTS_REV_B.md` | `hardware/sensor/out/COSTS_REV_B.md` | `61c43d78a9350fda1765712ac93c8a8b10c5ab5b45e72d671e4572013430f1e2` | 19281 | Kostenrechnung Sensor (cost_rev_b.py) |  |
| `2_bestellung/phase5_kosten_final.md` | `docs/reviews/phase5_kosten_final.md` | `5d354b3036b73dbd1f127b2f788c06ba31d4266117ce6a1a3d89dc251e2ec77e` | 23147 | Kosten final Sensor/Gateway/System |  |
| `3_druck/sensor/distanzlehre_24p2.3mf` | `mechanical/sensor/print/distanzlehre_24p2.3mf` | `6705dbce96fee5194351787674e97e76b304bf8cb32035f37514fed96c53b986` | 1117 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/distanzlehre_24p2.step` | `mechanical/sensor/print/distanzlehre_24p2.step` | `b3d50e7d55e0e10d84df2eb2e6a5df487a730655748a98c045b567afaec967a2` | 6921 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/distanzlehre_24p2.stl` | `mechanical/sensor/print/distanzlehre_24p2.stl` | `e388258563a8ebdf0beb1f8d127463adaadd35b64adde84fd7d44b313bce0658` | 684 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/fenster_tropfen.3mf` | `mechanical/sensor/print/fenster_tropfen.3mf` | `2af7c905cad97917360dac1d8a2532a9ca223d5f04b06637905a157caf6f7817` | 5060 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/fenster_tropfen.step` | `mechanical/sensor/print/fenster_tropfen.step` | `216fcf5298de318fb36210382adbd2cc7b9f551898f89bb0f1ac2e144be2252f` | 85607 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/fenster_tropfen.stl` | `mechanical/sensor/print/fenster_tropfen.stl` | `0cde0fd5c665a7db7d5418dcc7569b67d2cb3eed6df1761338dbe711a025aa64` | 22484 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/huelse_grau.3mf` | `mechanical/sensor/print/huelse_grau.3mf` | `3e7ca24d9d5858e2155e19cab977464fe4b81ca27043f859e566143a6438a550` | 109130 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/huelse_grau.step` | `mechanical/sensor/print/huelse_grau.step` | `e25f43ec8cd8383a3dceba5a322ce1d09d6d07496b3707af8f07097b605f53d7` | 1243688 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/huelse_grau.stl` | `mechanical/sensor/print/huelse_grau.stl` | `08df24689424019f599ac10d5f27e24c045ca163b84ea4f3badda58aa2c0e280` | 519784 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/kappe_blau.3mf` | `mechanical/sensor/print/kappe_blau.3mf` | `57c4b490a6bd5f559434a2a32386ccd60bdce8d31bb442f8fa2a8f7571725f9b` | 37973 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/kappe_blau.step` | `mechanical/sensor/print/kappe_blau.step` | `f7eaa72d7767879807eb0677051218382b8d715ccb53031ba51fe5246c731a03` | 264162 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/kappe_blau.stl` | `mechanical/sensor/print/kappe_blau.stl` | `5b1742b450248a4f72d04c279b03f998d4ab6f92252aa1eb3a9d55232fe9c9ff` | 186684 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/klemmring.3mf` | `mechanical/sensor/print/klemmring.3mf` | `cf1b6adf82877bf3ebbe3d5aaaa348c2e5915023cee8ccca3a9031845edee27f` | 8027 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/klemmring.step` | `mechanical/sensor/print/klemmring.step` | `2f82c5670de38a6855bc5a5a25dec5a183277604e6654439f4779b9472739dd4` | 7127 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/klemmring.stl` | `mechanical/sensor/print/klemmring.stl` | `7bb0c0b65bd3da2424f73d3fb0ef58489f404759942e0dee0df9bbb848a6f833` | 37884 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/kragen.3mf` | `mechanical/sensor/print/kragen.3mf` | `62908f03bd2f57105551f0f6b5d0bec45c3469b597fff1476c5a639daa509c45` | 13790 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/kragen.step` | `mechanical/sensor/print/kragen.step` | `a289d54e373d92b751b892bbc35beb3ffe1913724af93805ab9bd21f11521801` | 72106 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/kragen.stl` | `mechanical/sensor/print/kragen.stl` | `b447f06b8d12754715e3ff286b0f808d4b3719effa36c471e35b42b9c16b8ce9` | 72684 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/passprobe_huelse_oben.3mf` | `mechanical/sensor/print/passprobe_huelse_oben.3mf` | `f9fc1dca45c9033aa52653958c9ea27548341b7317c0604c8ac9bed42ff2a512` | 6450 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/passprobe_huelse_oben.step` | `mechanical/sensor/print/passprobe_huelse_oben.step` | `a884224fce9741dc2c696a69cbe2cb4079dcfba7dbc2ed63eb944bfb7a7ecfed` | 123592 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/passprobe_huelse_oben.stl` | `mechanical/sensor/print/passprobe_huelse_oben.stl` | `6e9ab159735b13bf37dbf0252869f71401985d31252e6e5fc5c0b0e1412b2ecc` | 31884 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/passprobe_huelse_unten.3mf` | `mechanical/sensor/print/passprobe_huelse_unten.3mf` | `b5963c0119d98033c55b5e6ba212877eba35310e1e88036b1cd51b68f68f8dde` | 8766 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/passprobe_huelse_unten.step` | `mechanical/sensor/print/passprobe_huelse_unten.step` | `4d0169ddd832697945243dcf0d44b65fd8c671730363a70aa7a22e94d6ad7ffe` | 31109 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/passprobe_huelse_unten.stl` | `mechanical/sensor/print/passprobe_huelse_unten.stl` | `e23734f3c0c8fcdd75118d535f662f80712ec82846093cd5ee3de3091fe0ed7f` | 42284 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/schottkeil.3mf` | `mechanical/sensor/print/schottkeil.3mf` | `648f372efdcc43c840bca713573db708c41ac6c5ed6e2db0b272c4276c8fc363` | 1120 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/schottkeil.step` | `mechanical/sensor/print/schottkeil.step` | `d320f73890de8d776d78c30f7f3cdc5a382425bfd84752ee64ec8ff90d80ae80` | 7042 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/schottkeil.stl` | `mechanical/sensor/print/schottkeil.stl` | `c3c6380ebfa242d1f76b6e9d0d45d983d3b0018a73127a2470bf69a12116f95d` | 684 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/stoessel.3mf` | `mechanical/sensor/print/stoessel.3mf` | `eb70f49fe2f1a6ed951a27d102c5aad73c23c38113c01ce1cf2e9c998c2a8d92` | 3841 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/stoessel.step` | `mechanical/sensor/print/stoessel.step` | `b6733a083f532e453a7128443f67444c910be94db408cbcd5c10559f0c37e971` | 15560 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/stoessel.stl` | `mechanical/sensor/print/stoessel.stl` | `247cae72c9e3a16a4cdf9f468332e0415a26cb6c3b6806a71dea4a23e725f474` | 12784 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/taste_blau.3mf` | `mechanical/sensor/print/taste_blau.3mf` | `5234b038aa0a7e936a0581e88877117267633b3d456187459fc99359ffe7e5d5` | 3915 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/taste_blau.step` | `mechanical/sensor/print/taste_blau.step` | `c03ec74dfc90f9371f7f9ffccb62f70563ba9a54d891c106c27dce8d980a9aa0` | 16978 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/taste_blau.stl` | `mechanical/sensor/print/taste_blau.stl` | `6f40909c6e7ae6ef2b0a25e68f76b1f6754f26fed522316916a4a67ae212ca0f` | 14384 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/tastenteller.3mf` | `mechanical/sensor/print/tastenteller.3mf` | `404c3b6afd4a3adc675aa2bd17d597541aaad46fa793ca024244a93aa26cb63b` | 5512 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/tastenteller.step` | `mechanical/sensor/print/tastenteller.step` | `91cbd00042546c6022d93c98e4822d6f1e294845f083445a1499730578c715c5` | 4966 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/sensor/tastenteller.stl` | `mechanical/sensor/print/tastenteller.stl` | `b3919c2ad5f4fa81dc5ca2de6df97fdef84fbc275554420625155ae62c586b45` | 25284 | Druckdateien Sensor (3MF/STL/STEP) |  |
| `3_druck/gateway_pi/deckel_blau.3mf` | `mechanical/gateway_pi/print/deckel_blau.3mf` | `e0cf432684844de2124d7ae2f7ab91d86b37886cbc111719f1b8577c230bf75b` | 46510 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/deckel_blau.step` | `mechanical/gateway_pi/print/deckel_blau.step` | `d280f6527f640ec9e952685b13027ef929f73c422e8001033e323ece506b2472` | 197402 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/deckel_blau.stl` | `mechanical/gateway_pi/print/deckel_blau.stl` | `500d1e4340a0619f6fdd27eb44c9deacc0f7e8ff1c648d6f72a5f8c265b3fb97` | 237584 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/fenster_tropfen_gw.3mf` | `mechanical/gateway_pi/print/fenster_tropfen_gw.3mf` | `841b7a92c5ee9a5235d3787154d3161c4ac203024cbb953fc8ae9f5ff7dc619e` | 2629 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/fenster_tropfen_gw.step` | `mechanical/gateway_pi/print/fenster_tropfen_gw.step` | `8553d4f27a8b6e89d87ea5b3dc87f03006f6b7ffd687e23b96b66d3ab592f9ec` | 81182 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/fenster_tropfen_gw.stl` | `mechanical/gateway_pi/print/fenster_tropfen_gw.stl` | `a4be4bc39547086b32167659a239f92bb63b6d4e1e1b502c40321fabb17b94f6` | 9884 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau.3mf` | `mechanical/gateway_pi/print/wanne_grau.3mf` | `bf4767e24781c21abae06942a2b54f70ab9526e468b4a4cc930726f01ec7a6e3` | 51523 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau.step` | `mechanical/gateway_pi/print/wanne_grau.step` | `6f99a9eda92bc32ef6d6ff670e6404a57890014fa09a1d166525aaa4396e56b6` | 523934 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau.stl` | `mechanical/gateway_pi/print/wanne_grau.stl` | `b1615bb741de5fe8fb76064bbad965597fae34874e9f3d6141831ff4498dbfc3` | 260384 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau_otg.3mf` | `mechanical/gateway_pi/print/wanne_grau_otg.3mf` | `3d9425f24d8b75428f5be5e07263ef195ad152526031196bf4a0fce2c579662c` | 51632 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau_otg.step` | `mechanical/gateway_pi/print/wanne_grau_otg.step` | `f33974602ee6e473ae57173cde2f9ced18f54df63b4220c592de8060b64fa43e` | 529212 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau_otg.stl` | `mechanical/gateway_pi/print/wanne_grau_otg.stl` | `fde49652619088c6dbf2e7b4d233e7c93a2398214f7c65f6ee79f40ee9016fdf` | 261384 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/PRINT_SETTINGS.md` | `mechanical/PRINT_SETTINGS.md` | `a9d24a52c68ff153d28184cc37dfcb81e13e4d020f4dccbc85352e4fd2fb0a7f` | 17378 | Druckeinstellungen |  |
| `4_gateway/BOM_GATEWAY.csv` | `hardware/gateway/BOM_GATEWAY.csv` | `6e03b56cd5adcf02f6f9dd27509291cf414e15287e6185f7f7fda1db1a6cae88` | 6042 | Gateway-Stückliste mit Preisen und Quellen (W-8) |  |
| `4_gateway/GATEWAY_SETUP.md` | `docs/manuals/GATEWAY_SETUP.md` | `ec27aab2ee7b9d491bf4ffd6ac5577bb7be819d84b2f0adcafd1d99aae2d6c59` | 19159 | Gateway einrichten |  |
| `5_firmware/PROGRAMMIEREN_SENSOR.md` | `docs/manuals/PROGRAMMIEREN_SENSOR.md` | `d90337ec252510c84506d596c2fed5e70bfacc41b152f28287988a2dd0c5abc0` | 16973 | Erstprogrammierung Sensor |  |
| `2_bestellung/EINKAUFSLISTE.md` | `docs/manuals/EINKAUFSLISTE.md` | `66a98f90576af63136d65f9c720df8607220eebe3ddcacd3908e819a4414ac38` | 32402 | Einkaufsliste ausser JLC (Händlergruppierung, Versand) |  |
| `2_bestellung/EINKAUFSLISTE.csv` | `docs/manuals/EINKAUFSLISTE.csv` | `e57c8d77e6479d2274a9c9caa337a8d24552a5b58fbf3ed2bad141b4d8d6aa21` | 20069 | Einkaufsliste Datenquelle (Preise, Lager, Abrufdatum, Beleg) |  |
| `3_druck/zeichnungen/FL-G-01_wanne_grau.pdf` | `mechanical/drawings/FL-G-01_wanne_grau.pdf` | `53bcf13fb6d16891742cd35a2bc0a24be090a8683be6306352bb51755ecfbfe6` | 54160 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-G-02_deckel_blau.pdf` | `mechanical/drawings/FL-G-02_deckel_blau.pdf` | `bf0870700f5420a864e785839677f618ee257846ec2c54b7e421c563c034d697` | 49455 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-G-03_fenster_tropfen_gw.pdf` | `mechanical/drawings/FL-G-03_fenster_tropfen_gw.pdf` | `a0098109764ea6b4914c6cd75aa646c778dfcb00a4cf85b5ea72c2e86224aa7d` | 29887 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-00_zusammenbau_sensor.pdf` | `mechanical/drawings/FL-S-00_zusammenbau_sensor.pdf` | `07a1ede6e8eb38be36ee988d20cb32515ff74d7c342a5cf7f0e7b08ecec501e9` | 105879 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-01_huelse_grau.pdf` | `mechanical/drawings/FL-S-01_huelse_grau.pdf` | `3945bd5596531559934d7e7d0b131adf1781498c5602ff4dba8e3439289a0dec` | 50209 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-02_kappe_blau.pdf` | `mechanical/drawings/FL-S-02_kappe_blau.pdf` | `6f6050bcf5bac116eba4ed608b610e5f7b9d3f2d9dc3f19fa643d306a9894022` | 60174 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-03_kragen.pdf` | `mechanical/drawings/FL-S-03_kragen.pdf` | `e04f130d2a77c94eedc28864d5d249c9800080a35acfe4808680abd995c29dda` | 50761 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-04_fenster_tropfen.pdf` | `mechanical/drawings/FL-S-04_fenster_tropfen.pdf` | `c87e8655d5aaf742ae9aabc0f5ec6b079aafde3cc977ec79d75611e363ff186a` | 32286 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-05_taste_blau.pdf` | `mechanical/drawings/FL-S-05_taste_blau.pdf` | `5c8188e0c5a4eab1e893d0245ac862a4bd4cc8e10ca0f7ed697b25fca075f03a` | 29027 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-06_klemmring.pdf` | `mechanical/drawings/FL-S-06_klemmring.pdf` | `9b53419714c4b7eec5363a5e02de82b5a8121efbb4d26927a37843714f55b8da` | 30988 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-07_tastenteller.pdf` | `mechanical/drawings/FL-S-07_tastenteller.pdf` | `b0f936eca3f7af80638a2610e8746341a8fe1a5d42de67c067399e319f1c6462` | 29264 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-08_stoessel.pdf` | `mechanical/drawings/FL-S-08_stoessel.pdf` | `1d9efe218b86770252d30d889fb44ab4c009de991a5e60e75b27dfd2e9a58a12` | 31445 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-09_schottkeil.pdf` | `mechanical/drawings/FL-S-09_schottkeil.pdf` | `f5c6f64b2f4f971fb558e06561f81ea95c6064f8789505d0b7d80249e877fdd2` | 27855 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-10_distanzlehre_24p2.pdf` | `mechanical/drawings/FL-S-10_distanzlehre_24p2.pdf` | `f39196fb0e1529efc15391d09751635d62273df691af32617666fd9fbecc0c2a` | 29256 | Massbilder Druckteile Sensor/Gateway |  |
| `4_gateway/APP.md` | `docs/manuals/APP.md` | `2b78bb718c69b928f74d2f132db3e24747c84380326de12195b063d83048eca1` | 12467 | PWA: Aufbau, Installation, Betrieb (Quellcode in 8_quellcode) |  |
| `5_firmware/TESTFIRMWARE.md` | `docs/manuals/TESTFIRMWARE.md` | `7a721f217f78cdae5b8b3425f09f02ae96a4f6981c075f347994cf1c3a8c5447` | 20525 | Testfirmware (Musterprüfung) |  |
| `5_firmware/INSTALL_FIRMWARE_TOOLS.md` | `docs/manuals/INSTALL_FIRMWARE_TOOLS.md` | `06400ceafd853d1086df66efd46b0a1946f0d60acce78262b2392fc98d6c907a` | 19001 | Build-Werkzeuge installieren (Firmware Sensor) |  |
| `5_firmware/sensor/README.md` | `firmware/sensor/README.md` | `c66f9d2e054792610cb9e5d8caa61fbaf9c9c60e2bded5d2ef1dcfe3b26f3fae` | 15522 | Build-Anleitung Firmware Sensor (make, Signierung) |  |
| `5_firmware/sensor/keys/README.md` | `firmware/sensor/keys/README.md` | `c2f5c3912758142c31f52085d6845af0a23724bb92ffa57af132f637ebaccc0f` | 2199 | Schlüsselregeln (DEV/Produktion, Fingerabdruck) |  |
| `5_firmware/PROTOCOL.md` | `firmware/PROTOCOL.md` | `8738491817214155e672748c08098663b432c0fef475458c5e4d401c3894db81` | 63435 | Funkprotokoll Sensor <-> Gateway |  |
| `6_anleitungen/MONTAGE_SENSOR.md` | `docs/manuals/MONTAGE_SENSOR.md` | `443360335fc581d99eaf4c9fdc6c3ef67f36faa134e1076808b7353069287b40` | 33883 | Montage Sensor inkl. Verguss (Kap. 3a) |  |
| `6_anleitungen/BATTERIEWECHSEL.md` | `docs/manuals/BATTERIEWECHSEL.md` | `76e71dfc941a5416130491cede0688043f83e4345af6c486650dc05395b4d090` | 5808 | Batteriewechsel |  |
| `6_anleitungen/INBETRIEBNAHME.md` | `docs/manuals/INBETRIEBNAHME.md` | `81ade604ab1d567033920bcaba056ad2d3ffa593440540b0985b5587ef0023d6` | 10378 | Inbetriebnahme |  |
| `6_anleitungen/PAIRING_KALIBRIERUNG.md` | `docs/manuals/PAIRING_KALIBRIERUNG.md` | `61d6e2da6e39830c7fb5399637c88d4049282fd1bec7f7a674bc4929d4e62bd0` | 10682 | Pairing und Kalibrierung |  |
| `6_anleitungen/FEHLERSUCHE.md` | `docs/manuals/FEHLERSUCHE.md` | `cec53b7818151810fe316e43a193ca36cfdac76c92089ead1f8759a413a67c5b` | 14510 | Fehlersuche |  |
| `6_anleitungen/vergussmasse_versiegelung.md` | `docs/concepts/vergussmasse_versiegelung.md` | `3358e1e6addc2a0f2ad085489a7d618b0898ba0f205917f0b9eeef0ad0f9d05a` | 34596 | Konzept Vergussmasse/Versiegelung (D-030) |  |
| `7_programmieradapter/README.md` | `hardware/programmer/README.md` | `97bd6414f92a1ba4312afdedebff3bcb8a787d7ebaec2721987e7694a7f9d8b8` | 31861 | Programmieradapter Rev 1 (Schaltung, Bezug, PL2303 Kap. 9) |  |
| `7_programmieradapter/fluidi_programmer_schematic.pdf` | `hardware/programmer/out/fluidi_programmer_schematic.pdf` | `52ff572e8575257cbd0abe9c6db6392b278e013663f7a4c6a29e357c0462a19d` | 118494 | Schaltplan Programmieradapter |  |
| `9_renderings/fluidi_01_topf_led_gruen.png` | `renders/final/fluidi_01_topf_led_gruen.png` | `8a46986bf321dbbe8f27644d4761062fd29e74bcc35a87260ea7eb03b7ca2873` | 4219059 | Produktrenderings |  |
| `9_renderings/fluidi_02_nah_led_blau.png` | `renders/final/fluidi_02_nah_led_blau.png` | `6605440658d414b07f0d0bc91c1e55495e144b1388c7d8c12d7a0195a1147527` | 4324906 | Produktrenderings |  |
| `9_renderings/fluidi_03_explosion.png` | `renders/final/fluidi_03_explosion.png` | `44eea6d1b63a85d57233d224e93819dc98299f3c8369024b1334a00fb30b338c` | 4289452 | Produktrenderings |  |
| `9_renderings/fluidi_04_batteriewechsel.png` | `renders/final/fluidi_04_batteriewechsel.png` | `34a369bacc32aa66db0a37550ef62dcad1b7a3349169fb46030345de46a642fd` | 3672118 | Produktrenderings |  |
| `9_renderings/fluidi_05_gateway_buero.png` | `renders/final/fluidi_05_gateway_buero.png` | `dbb519753a80219538251d797c332f3b9a92838c234b81603fe85cd22a20266e` | 3278779 | Produktrenderings |  |
| `9_renderings/fluidi_06_produktfoto.png` | `renders/final/fluidi_06_produktfoto.png` | `54f8ac6b8cf27213b147d45dd9cd7b97cd845bff3e4ba9d85f8714cf972d1b53` | 3107861 | Produktrenderings |  |
| `9_renderings/pcb/fluidi_pcb_bottom.png` | `renders/pcb/fluidi_pcb_bottom.png` | `8d95535b6fa504453cb825c02ed2d45cf70f01b9d31fb698d99ca61c34100d6b` | 76031 | Leiterplatten-Renderings |  |
| `9_renderings/pcb/fluidi_pcb_iso.png` | `renders/pcb/fluidi_pcb_iso.png` | `50e6bca0285d2ea9fe06ca6fb73391021c4176136cc8aab05fe81b9b9c8a4798` | 525484 | Leiterplatten-Renderings |  |
| `9_renderings/pcb/fluidi_pcb_kopf_nah.png` | `renders/pcb/fluidi_pcb_kopf_nah.png` | `1812980cecf7388a5ed4a598d474f1ecfff1697b7c845d093fdcdaf609821dfe` | 408539 | Leiterplatten-Renderings |  |
| `9_renderings/pcb/fluidi_pcb_top.png` | `renders/pcb/fluidi_pcb_top.png` | `6ee34a81574bede0c18564044d7fb86f38d4971bd8a903236daa5ed1f4e21fe0` | 123803 | Leiterplatten-Renderings |  |
| `8_quellcode/fluidi_quellcode_firmware_app.tar.gz` | `git archive 9c39ce8 -- firmware app scripts/flash_sensor.py (ohne *.pem/*.key/*.der)` | `741adc6029c7a5fd499ed9df7427ed627fa3ffae25a949afd237e8c85b1ef0e1` | 2369104 | Quellcode Firmware Sensor + Gateway, PWA, Flash-Werkzeug |  |
| `8_quellcode/QUELLCODE.md` | `(erzeugt von production/make_release_rev_c.py)` | `464d0cb6451b23f684ae5f07c36397d25b7dd1cefe7f688b1a7880810ea96f16` | 1327 | Hinweis Quellcode |  |
| `5_firmware/FIRMWARE_HINWEIS.md` | `(erzeugt von production/make_release_rev_c.py)` | `8114288dfc3ff861b335f300011783951c22be3ad72a1be2cdf1a31ab436c3a1` | 1498 | Firmware-Hinweis |  |

*geändert = Quelle hat beim Erzeugen nicht committete Änderungen (Arbeitskopie). Nach dem Commit das Paket neu erzeugen, damit Git-Stand und Inhalt übereinstimmen.

Quellcode Firmware Sensor/Gateway und PWA: `8_quellcode/` (git archive des Git-Stands, ohne Schlüssel, Hinweis `8_quellcode/QUELLCODE.md`). Firmware-Binärdateien bewusst nicht enthalten (`5_firmware/FIRMWARE_HINWEIS.md`). Nicht im Paket: alte ESP32-Gateway-Druckteile (`mechanical/gateway/`, durch D-014 ersetzt), Simulationen, Prüfberichte.
