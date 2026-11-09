# fluidi – Release-Paket Rev C (Sensor, Gateway, Anleitungen, Quellcode; Stand Phase 6)

| | |
|---|---|
| Erzeugt | 2026-11-09T07:44:38+01:00 von `.venv/bin/python production/make_release_rev_c.py` |
| Git-Stand | `4b49ae8` |
| Bestellunterlage | `2_bestellung/ORDER_JLC_REV_C.md` (Kap. 1: Soll-sha256 der Upload-Dateien) |
| **Sicherheit** | **Zuerst `0_SICHERHEIT.md` lesen** (Knopfzellen, Verguss/Kleber mit SDB in `6_anleitungen/sdb/`, Programmieren nur nach Anleitung, Testfirmware nie an Endnutzer, D-030-Bedingungen) |
| Prüfen | `cd production/rev-C && sha256sum -c SHA256SUMS` |
| Status | **Keine Bestellung ausgelöst.** Bestellen nur nach Freigabe durch den Auftraggeber (`2_bestellung/BESTELLEN_JLC.md`) |

Alle Dateien sind **Kopien** (keine Neuerzeugung); jede Kopie wurde beim Erzeugen per sha256 mit der Quelle verglichen. Die drei Upload-Dateien in `1_jlc_upload/` entsprechen den Hashes in ORDER_JLC_REV_C.md Kap. 1 (sonst bricht das Skript ab).

| Datei im Paket | Quelle im Repo | sha256 | Bytes | Zweck | geändert* |
|---|---|---|---|---|---|
| `1_jlc_upload/fluidi_sensor_gerber_jlc.zip` | `hardware/sensor/out/fluidi_sensor_gerber_jlc.zip` | `bf1902ea4bab83d96f385f557575d8311886acf2bacee7aa743d88eef47883d0` | 154032 | Gerber + Bohrdaten + Job (Upload JLC, PCB) |  |
| `1_jlc_upload/fluidi_sensor_bom_jlc.csv` | `hardware/sensor/out/fluidi_sensor_bom_jlc.csv` | `3d99ffca7b79abe550a57de4ff7d3228eabe4f532bc46f602e6bcec53f456ea9` | 1204 | BOM JLC-Format (Upload PCBA) |  |
| `1_jlc_upload/fluidi_sensor_cpl_jlc.csv` | `hardware/sensor/out/fluidi_sensor_cpl_jlc.csv` | `b01ba1477406d8c305693567ca70011ccb60892215ccc055ee17d99f6329213f` | 1634 | CPL JLC-Format (Upload PCBA) |  |
| `2_bestellung/ORDER_JLC_REV_C.md` | `hardware/sensor/out/ORDER_JLC_REV_C.md` | `5ed4f921177b90a1b41e7f9dce69fb8c15b4fa56a5f395e8852d48abff02d60b` | 29213 | Bestellunterlage mit Checklisten (Kap. 4/5) und Remark (Kap. 8) |  |
| `2_bestellung/BESTELLEN_JLC.md` | `docs/manuals/BESTELLEN_JLC.md` | `bcd71102259f1da26df407ea267f0258380d6aebfff95d2242c8a3abc338b868` | 19194 | Schritt-für-Schritt-Anleitung JLC-Formular |  |
| `2_bestellung/REMARK_JLC_REV_C.txt` | `hardware/sensor/out/REMARK_JLC_REV_C.txt` | `54ddcd49be85d56ff3377fcf55d2b8c94d90c50d529c916394d61825017b3dff` | 563 | Remark-Text zum Kopieren (eine Zeile, ohne Markdown) |  |
| `2_bestellung/fluidi_sensor_bom_extra.csv` | `hardware/sensor/out/fluidi_sensor_bom_extra.csv` | `6a8b983e697f65643d41ab92f3fc63b960eebf1b1de11b7c0f8c48f5d10636b0` | 739 | Teile ohne JLC-Bestückung (lokal, DNP, Leiterplattenstrukturen) |  |
| `2_bestellung/fluidi_sensor_cpl_jlc_rotationen.csv` | `hardware/sensor/out/fluidi_sensor_cpl_jlc_rotationen.csv` | `2f6fce43c8ca7b199dbfb2a6f3397be8078cd02e6cfd887d535b5206d2219653` | 2181 | Rotationskorrekturen CPL (für Confirm Parts Placement) |  |
| `2_bestellung/fluidi_sensor_bestueckung_F.pdf` | `hardware/sensor/out/pdf/fluidi_sensor_bestueckung_F.pdf` | `bcf850d67437ab2722c7b5f030b858ec9b4674cdefc2933d15e79574b182fce9` | 173080 | Bestückungsansicht Oberseite mit Pin-1 (Vorschau-Vergleich) |  |
| `2_bestellung/fluidi_sensor_layout_lagen.pdf` | `hardware/sensor/out/pdf/fluidi_sensor_layout_lagen.pdf` | `e667c5f805c2e7fd0b16bcf6aa4b3a35740d2ce5bd454dba2ce6cc4b305101cf` | 505130 | alle Lagen als PDF |  |
| `2_bestellung/fluidi_sensor_schematic.pdf` | `hardware/sensor/out/fluidi_sensor_schematic.pdf` | `9c3feb2731d78e1992a1fd9bd28343f33fa4358a7dae27e2f1b4e0a2dc367942` | 232916 | Schaltplan Rev C |  |
| `2_bestellung/COSTS_REV_B.md` | `hardware/sensor/out/COSTS_REV_B.md` | `529dc95c152a6c1d01e1f4e1749fc9fc12b333fd6ebb3f8b493b21a131c92840` | 19281 | Kostenrechnung Sensor (cost_rev_b.py) |  |
| `2_bestellung/phase5_kosten_final.md` | `docs/reviews/phase5_kosten_final.md` | `6b5fdaee2b739da1099d5d5344b135c932e161b3228900bd684638c575c5652d` | 25505 | Kosten final Sensor/Gateway/System |  |
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
| `3_druck/gateway_pi/deckel_blau.3mf` | `mechanical/gateway_pi/print/deckel_blau.3mf` | `bf00dd3c01618d84d78d3dc18d43314a32bfa45c526465c279fde1b082e6369e` | 46510 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/deckel_blau.step` | `mechanical/gateway_pi/print/deckel_blau.step` | `440b91c5bd7f1c574e0923ee0a79f480a29c61beb1887ddc36b794563817c94e` | 197402 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/deckel_blau.stl` | `mechanical/gateway_pi/print/deckel_blau.stl` | `500d1e4340a0619f6fdd27eb44c9deacc0f7e8ff1c648d6f72a5f8c265b3fb97` | 237584 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/fenster_tropfen_gw.3mf` | `mechanical/gateway_pi/print/fenster_tropfen_gw.3mf` | `3310078bbd8b987f7000f0a0e3b332df93e979fc88a5e1682037ce0cdb0547a4` | 2629 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/fenster_tropfen_gw.step` | `mechanical/gateway_pi/print/fenster_tropfen_gw.step` | `d1f36f156a0615769c9db32eab32c515efb732a52d6c71aed62f5f18955cd581` | 81182 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/fenster_tropfen_gw.stl` | `mechanical/gateway_pi/print/fenster_tropfen_gw.stl` | `a4be4bc39547086b32167659a239f92bb63b6d4e1e1b502c40321fabb17b94f6` | 9884 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau.3mf` | `mechanical/gateway_pi/print/wanne_grau.3mf` | `5df38c7613c241a2b153e12b8decbebbb39d5ca7c53343081155cc3a19f4fbbd` | 60076 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau.step` | `mechanical/gateway_pi/print/wanne_grau.step` | `39a441e36f0bcf2796d890218f686f6a2c55a89470533bdb4a27ae85834802a7` | 545280 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau.stl` | `mechanical/gateway_pi/print/wanne_grau.stl` | `75cc35157c6dce315a1eb774f83259390cf3d4fec17c20405c14458360dc6387` | 295184 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau_otg.3mf` | `mechanical/gateway_pi/print/wanne_grau_otg.3mf` | `c43f3893636f64f553780c243146e842235c847020b68d7a0f24b94e4f58e6fd` | 60272 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau_otg.step` | `mechanical/gateway_pi/print/wanne_grau_otg.step` | `94da61c17874491c6578434c033a6c175194dc0199517e89860c087276bb6e3e` | 550565 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/gateway_pi/wanne_grau_otg.stl` | `mechanical/gateway_pi/print/wanne_grau_otg.stl` | `25524a8e272b2d04e9d398c80372117f627c52e9b9e90c74635021e1e619df4f` | 296184 | Druckdateien Gateway Pi Zero 2 W (G1 v4) |  |
| `3_druck/PRINT_SETTINGS.md` | `mechanical/PRINT_SETTINGS.md` | `dd28af7751d3417ae9f260f15e1144183ac24284b4cd89ec62039d33b81e5d4f` | 25490 | Druckeinstellungen |  |
| `4_gateway/BOM_GATEWAY.csv` | `hardware/gateway/BOM_GATEWAY.csv` | `e380ec5e598ec9508f2cfb088ed0b38577becf3aff22998c14ebbdd2329f6c96` | 5828 | Gateway-Stückliste mit Preisen und Quellen (W-8) |  |
| `4_gateway/GATEWAY_SETUP.md` | `docs/manuals/GATEWAY_SETUP.md` | `6b17a97e9b76272915805789db18a9e25f4900d8a2d78d17828a49e77e76c1e9` | 23131 | Gateway einrichten |  |
| `5_firmware/PROGRAMMIEREN_SENSOR.md` | `docs/manuals/PROGRAMMIEREN_SENSOR.md` | `3d4b00a6228b135f75e9ef57fd867b1f68935e64dcae54cdd6fbd4bfcfca1a42` | 19991 | Erstprogrammierung Sensor |  |
| `2_bestellung/EINKAUFSLISTE.md` | `docs/manuals/EINKAUFSLISTE.md` | `325d7d2ea6408b6aacf172766830467eb02ba92d80004335de45fa0f03af5e08` | 70732 | Einkaufsliste ausser JLC (Händlergruppierung, Versand) |  |
| `2_bestellung/EINKAUFSLISTE.csv` | `docs/manuals/EINKAUFSLISTE.csv` | `fc9b9666c73808c42c8d528e39324288ac6e96dfaeb627e22409939e899f9c6c` | 56313 | Einkaufsliste Datenquelle (Preise, Lager, Abrufdatum, Beleg) |  |
| `3_druck/zeichnungen/FL-G-01_wanne_grau.pdf` | `mechanical/drawings/FL-G-01_wanne_grau.pdf` | `b844889b5c5c0fa80c0febd9df7507ff5ada2ce1d6dea4bfdaf9cc960bf82b3f` | 55874 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-G-02_deckel_blau.pdf` | `mechanical/drawings/FL-G-02_deckel_blau.pdf` | `706ec1f2f9a8778f60caac65265eecb48f7888c8a92ec60489eab98f17dd05c1` | 49453 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-G-03_fenster_tropfen_gw.pdf` | `mechanical/drawings/FL-G-03_fenster_tropfen_gw.pdf` | `4a92e467eda426a320f2e281d0370a0f33f30daf9975aeea02f64be809623f27` | 29909 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-00_zusammenbau_sensor.pdf` | `mechanical/drawings/FL-S-00_zusammenbau_sensor.pdf` | `87d8c76ed69c13166c2f35e2ab86ac08f68e0add63943d95fadafb805cac729d` | 106090 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-01_huelse_grau.pdf` | `mechanical/drawings/FL-S-01_huelse_grau.pdf` | `f6c5f18be27e20b8066ee97ab679b8888f382076581a0ae9289e1921cc8b7142` | 50206 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-02_kappe_blau.pdf` | `mechanical/drawings/FL-S-02_kappe_blau.pdf` | `f2a32b5be4f9f1b07e6197703dabfd689eae7c0b434efa7417017c1544e71b88` | 60172 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-03_kragen.pdf` | `mechanical/drawings/FL-S-03_kragen.pdf` | `d9a33b5b581bf471e4747e88b6a657685eac468ad64eacdf37ca7de2ee33a08f` | 50762 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-04_fenster_tropfen.pdf` | `mechanical/drawings/FL-S-04_fenster_tropfen.pdf` | `53511ed4a0a605a1c16ed8767b5612946b22b1208ae12a950805a610fbf40afc` | 32532 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-05_taste_blau.pdf` | `mechanical/drawings/FL-S-05_taste_blau.pdf` | `75123d7e8b4806605dcbc3d86dfb63d30bd6af6836c6f9292278e0a13861560d` | 29027 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-06_klemmring.pdf` | `mechanical/drawings/FL-S-06_klemmring.pdf` | `984f50c51cb5357c5bf86da084f471d52a4565655fea210a6b10047053dbc596` | 30988 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-07_tastenteller.pdf` | `mechanical/drawings/FL-S-07_tastenteller.pdf` | `248b46e537a62d693a743b075d5e9f6a499bbe70e7dfc3586cb7088c67bf7a10` | 29264 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-08_stoessel.pdf` | `mechanical/drawings/FL-S-08_stoessel.pdf` | `32338f0388150c236ca760e4e7c51f4a6398a6235b0f6135133f77e0179e30b6` | 31446 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-09_schottkeil.pdf` | `mechanical/drawings/FL-S-09_schottkeil.pdf` | `9c7210911a52e60d9c40caa79e1eca91bb7d8a43da73ad55bde7357d743aef53` | 27855 | Massbilder Druckteile Sensor/Gateway |  |
| `3_druck/zeichnungen/FL-S-10_distanzlehre_24p2.pdf` | `mechanical/drawings/FL-S-10_distanzlehre_24p2.pdf` | `3e1241d923161a3e389303dab3b2d888834fa4dfbbd6d4ff3274176f7c6c5188` | 29255 | Massbilder Druckteile Sensor/Gateway |  |
| `4_gateway/APP.md` | `docs/manuals/APP.md` | `2b78bb718c69b928f74d2f132db3e24747c84380326de12195b063d83048eca1` | 12467 | PWA: Aufbau, Installation, Betrieb (Quellcode in 8_quellcode) |  |
| `5_firmware/TESTFIRMWARE.md` | `docs/manuals/TESTFIRMWARE.md` | `979e441d064153517f5d64a2b6c665472f5b8613352b38ebee0ffb2f1f02ec02` | 24946 | Testfirmware (Musterprüfung) |  |
| `5_firmware/INSTALL_FIRMWARE_TOOLS.md` | `docs/manuals/INSTALL_FIRMWARE_TOOLS.md` | `06400ceafd853d1086df66efd46b0a1946f0d60acce78262b2392fc98d6c907a` | 19001 | Build-Werkzeuge installieren (Firmware Sensor) |  |
| `5_firmware/sensor/README.md` | `firmware/sensor/README.md` | `adf837aae3b7305e981d6dc411e0a60320bf29521757392292adb7169e9e2351` | 15835 | Build-Anleitung Firmware Sensor (make, Signierung) |  |
| `5_firmware/sensor/keys/README.md` | `firmware/sensor/keys/README.md` | `c2f5c3912758142c31f52085d6845af0a23724bb92ffa57af132f637ebaccc0f` | 2199 | Schlüsselregeln (DEV/Produktion, Fingerabdruck) |  |
| `5_firmware/PROTOCOL.md` | `firmware/PROTOCOL.md` | `8738491817214155e672748c08098663b432c0fef475458c5e4d401c3894db81` | 63435 | Funkprotokoll Sensor <-> Gateway |  |
| `6_anleitungen/MONTAGE_SENSOR.md` | `docs/manuals/MONTAGE_SENSOR.md` | `12fd6cee948b5de4edcc0e393f952d365a500d0d73dd96ac1de5ac1fcbb19db3` | 45704 | Montage Sensor inkl. Verguss (Kap. 3a) |  |
| `6_anleitungen/BATTERIEWECHSEL.md` | `docs/manuals/BATTERIEWECHSEL.md` | `7e8f8e4ecb0ca276d8d8c7777d8c855a8402bec50cdd0eb5e0e8d2567b397838` | 6117 | Batteriewechsel |  |
| `6_anleitungen/INBETRIEBNAHME.md` | `docs/manuals/INBETRIEBNAHME.md` | `3b5237b87e24b20acb457c47f28ece98176a38774463c05783d448a8ca148768` | 12197 | Inbetriebnahme |  |
| `6_anleitungen/PAIRING_KALIBRIERUNG.md` | `docs/manuals/PAIRING_KALIBRIERUNG.md` | `c817b8859c6fca143da061828a13f859c9f4fe1a9aefca2cd04bba740a0a0a10` | 12012 | Pairing und Kalibrierung |  |
| `6_anleitungen/FEHLERSUCHE.md` | `docs/manuals/FEHLERSUCHE.md` | `53d3a279c78aec598949e50b502226c43fd24f254de0c62039f841b7fee56bac` | 15937 | Fehlersuche |  |
| `6_anleitungen/vergussmasse_versiegelung.md` | `docs/concepts/vergussmasse_versiegelung.md` | `3358e1e6addc2a0f2ad085489a7d618b0898ba0f205917f0b9eeef0ad0f9d05a` | 34596 | Konzept Vergussmasse/Versiegelung (D-030) |  |
| `6_anleitungen/sdb/Electrolube_ER2223-PartA_SDS_Rev0-2016-10-19_EN.pdf` | `docs/references/Electrolube_ER2223-PartA_SDS_Rev0-2016-10-19_EN.pdf` | `b28f7e1b821479ec25f142ad0691b03d1dd86e4617b6592675062efc74355387` | 252634 | SDB ER2223 Teil A (EN) |  |
| `6_anleitungen/sdb/Electrolube_ER2223-PartA_SDS_Rev0.64-2023-10-27_SV.pdf` | `docs/references/Electrolube_ER2223-PartA_SDS_Rev0.64-2023-10-27_SV.pdf` | `00986e0e26ab7f8110906a1507d042d2ffc933611a61fe9b216ef2c9d9f6b6c4` | 209907 | SDB ER2223 Teil A (SV, 2023) |  |
| `6_anleitungen/sdb/Electrolube_ER2223-PartB_SDS_2023-10-02_HU.pdf` | `docs/references/Electrolube_ER2223-PartB_SDS_2023-10-02_HU.pdf` | `c35bea0ad1adbdf244dc8a72cb15b1fbd07960b39b283549bbc1762dfa1651c2` | 307367 | SDB ER2223 Teil B (HU) – NICHT AUSREICHEND, DE/EN/FR/IT-Fassung vor dem ersten Beutel Pflicht (D-030) |  |
| `6_anleitungen/sdb/Electrolube_ER2223_TDS_Rev4-2019-03.pdf` | `docs/references/Electrolube_ER2223_TDS_Rev4-2019-03.pdf` | `dc54a06dcb9353ef841783696557b17582efddf2b756d402660bec64caa7ff41` | 384664 | TDS ER2223 |  |
| `6_anleitungen/sdb/UHU_PlusEndfest300-33g_SDS_V62-2026-07-17_DE.pdf` | `docs/references/UHU_PlusEndfest300-33g_SDS_V62-2026-07-17_DE.pdf` | `8cd158bebcf1fbea4c651c25e20de6c5baeb479b757f641a659aa214371be420` | 441700 | SDB UHU plus endfest 300 (Fensterkleber) |  |
| `6_anleitungen/sdb/UHU_PlusEndfest300_TDS_2012-07.pdf` | `docs/references/UHU_PlusEndfest300_TDS_2012-07.pdf` | `b0d440b405f0dde1e4c450c60bee7b0d739ffcf351474d9618e6f63e1a10d4c1` | 91437 | TDS UHU plus endfest 300 |  |
| `6_anleitungen/sdb/MAPA_Solo977_TechnicalSheet_DE_2026-09.pdf` | `docs/references/MAPA_Solo977_TechnicalSheet_DE_2026-09.pdf` | `f294e6ab0dd986e39e0f2e9b26e240706060f319cb8cbb85f980b1a1b29e0988` | 1042786 | Handschuh MAPA Solo 977 (EN ISO 374) |  |
| `6_anleitungen/sdb/MAPA_Solo977_Bestaendigkeitstabelle_2024-04-11.pdf` | `docs/references/MAPA_Solo977_Bestaendigkeitstabelle_2024-04-11.pdf` | `d1692d886149fd90205e76a18f159a58788a37556746a2df1c8db5b59d932884` | 128186 | Beständigkeitstabelle Handschuh |  |
| `7_programmieradapter/README.md` | `hardware/programmer/README.md` | `1c74ecb0836334b91e4a5d699aa476e78e9eb41e52a6c6890f83b638a952f8b5` | 31997 | Programmieradapter Rev 1 (Schaltung, Bezug, PL2303 Kap. 9) |  |
| `7_programmieradapter/fluidi_programmer_schematic.pdf` | `hardware/programmer/out/fluidi_programmer_schematic.pdf` | `52ff572e8575257cbd0abe9c6db6392b278e013663f7a4c6a29e357c0462a19d` | 118494 | Schaltplan Programmieradapter |  |
| `1_jlc_upload/dummy/fluidi_dummy_plus_gerber_jlc.zip` | `hardware/dummy_cell/out/fluidi_dummy_plus_gerber_jlc.zip` | `02d5b9ec4c880b3f4f84d55aa81295a4b59e9b5b554da938c63db902244bcf6c` | 6126 | Dummy-Scheibe PLUS 1.0 mm (Upload JLC, PCB ohne PCBA) |  |
| `1_jlc_upload/dummy/fluidi_dummy_minus_gerber_jlc.zip` | `hardware/dummy_cell/out/fluidi_dummy_minus_gerber_jlc.zip` | `03a535a6bb2168db98aee80e2b0d93e1e095395b60e614bb8cb16f2ce3872eb3` | 12494 | Dummy-Scheibe MINUS 2.0 mm (Upload JLC, PCB ohne PCBA) |  |
| `7_programmieradapter/dummy_cell/README.md` | `hardware/dummy_cell/README.md` | `a676cbd9a8a3640bafac2982d9a02dfd58492fb8ef8bc1eaa931d495af5fe87c` | 24129 | Dummy-Scheibe: Aufbau, Bestelloptionen, Zusammenbau, Werkstatt Weg B |  |
| `7_programmieradapter/dummy_cell/fluidi_dummy_plus_layout.pdf` | `hardware/dummy_cell/out/fluidi_dummy_plus_layout.pdf` | `fc255da5618100bfad7441adc7d835b323ab0de4d428c8f869df3c620fc6f3f5` | 44637 | Dummy-Scheibe PLUS Layout |  |
| `7_programmieradapter/dummy_cell/fluidi_dummy_minus_layout.pdf` | `hardware/dummy_cell/out/fluidi_dummy_minus_layout.pdf` | `68cc16b74af6a968675698862ab6659407f19ef52862ec1c904d6033f2bfd3e6` | 69420 | Dummy-Scheibe MINUS Layout |  |
| `7_programmieradapter/dummy_cell/kosten.txt` | `hardware/dummy_cell/out/kosten.txt` | `b63118e84626775f7c33f469e9f1a65c554bd22b0dfcd78131e28f4b61b3a1fa` | 713 | Dummy-Scheibe Kosten (cost_dummy.py) |  |
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
| `8_quellcode/fluidi_quellcode_firmware_app.tar.gz` | `git archive 4b49ae8 -- firmware app scripts/flash_sensor.py scripts/test_flash_sensor.py scripts/testfw_eval.py scripts/test_testfw_eval.py docs/interfaces/PINMAP_SENSOR.md hardware/sensor/out/fluidi_sensor.net (ohne *.pem/*.key/*.der)` | `69f9f5be99e3ce4875ab742e7f7abf2c94ad02f92d88bf957f13d096273155c7` | 2408485 | Quellcode Firmware Sensor + Gateway, PWA, Flash-Werkzeug |  |
| `8_quellcode/QUELLCODE.md` | `(erzeugt von production/make_release_rev_c.py)` | `9e7eae7d0bf2653fd62c89beecdd3c8ee71fb544e363c8dacb0f1480a713970f` | 1636 | Hinweis Quellcode |  |
| `5_firmware/MUSTER_DEV/fluidi-sensor-factory-0.1.0+1-key86e66310969bdc7d.hex` | `make (DEV_ONLY-Schluessel) aus 8_quellcode/fluidi_quellcode_firmware_app.tar.gz @ 4b49ae8` | `2e0511eec0228ffddd70c68ab9d2e451c761a7d5ed9cba74c4946dd219da1c6f` | 694996 | MUSTER, DEV-Schlüssel, NICHT FREIGEGEBEN |  |
| `5_firmware/MUSTER_DEV/fluidi-sensor-0.1.0+1.bin` | `make (DEV_ONLY-Schluessel) aus 8_quellcode/fluidi_quellcode_firmware_app.tar.gz @ 4b49ae8` | `b032bf8087f3c1dead05adaa580ad07333cb11d169d893d0aa03b18bbbe94893` | 207376 | MUSTER, DEV-Schlüssel, NICHT FREIGEGEBEN |  |
| `5_firmware/FIRMWARE_HINWEIS.md` | `(erzeugt von production/make_release_rev_c.py)` | `0bf0d38f37624ad7ffb043d40e190c851a7a1b4fa9cad9a1e9ce92005bb9cde7` | 2877 | Firmware-Hinweis |  |
| `0_SICHERHEIT.md` | `(erzeugt, D-030 aus docs/requirements/DECISIONS.md)` | `7ca2e746d620ae8699384634a3f10a28861147997c641da80f8f5f7524d69e85` | 3224 | Sicherheit zuerst (Sicherheit Schluss W-7) |  |

*geändert = Quelle hat beim Erzeugen nicht committete Änderungen (Arbeitskopie). Nach dem Commit das Paket neu erzeugen, damit Git-Stand und Inhalt übereinstimmen.

Quellcode Firmware Sensor/Gateway und PWA: `8_quellcode/` (git archive des Git-Stands, ohne Schlüssel, Hinweis `8_quellcode/QUELLCODE.md`). DEV-signiertes Muster-Werks-Hex in `5_firmware/MUSTER_DEV/` (nicht freigegeben, `5_firmware/FIRMWARE_HINWEIS.md`). Nicht im Paket: alte ESP32-Gateway-Druckteile (`mechanical/gateway/`, durch D-014 ersetzt), Simulationen, Prüfberichte.
