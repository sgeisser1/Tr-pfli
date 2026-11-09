#!/usr/bin/env python3
"""fluidi Release-Paket Rev C -> production/rev-C/ (nur KOPIEN, keine Neuerzeugung).

Kopiert Fertigungs-, Bestell- und Druckdateien aus dem Repo, prueft danach jede Kopie per sha256 gegen die Quelle und
die drei Bestelldateien zusaetzlich gegen die Hashes in hardware/sensor/out/ORDER_JLC_REV_C.md Kap. 1. Schreibt
production/rev-C/README.md (Inhalt, Quelle, sha256, Git-Stand) und production/rev-C/SHA256SUMS (Format sha256sum -c).
Abbruch (Exit 1), wenn eine Bestelldatei nicht dem ORDER-Hash entspricht.

Abbruch (Exit 1) auch, wenn eine Quelle nicht committete Aenderungen hat (Red Team W-1): Das Paket entsteht nur aus
einem sauberen Git-Stand; Ausnahme nur zum Testen mit --allow-dirty (README markiert das).

Aufruf : .venv/bin/python production/make_release_rev_c.py [--allow-dirty] [--no-fw-build]
         (baut das DEV-Werks-Hex aus dem Quellarchiv, braucht ~/fluidi-tools/env.sh; K-1 Red Team Phase 6)
Probe  : .venv/bin/python production/make_release_rev_c.py --probe   (Archiv + Firmware-Build + make check, ohne Paket)
Pruefen: .venv/bin/python production/make_release_rev_c.py --check
         vergleicht das vorhandene Paket mit den aktuellen Quellen (sha256 je Datei, fehlende/zusaetzliche Dateien,
         Git-Stand im README = HEAD). sha256sum -c SHA256SUMS allein prueft nur die Kopien gegen sich selbst.
"""
import datetime
import glob
import hashlib
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
DST = os.path.join(ROOT, "production", "rev-C")
ORDER = "hardware/sensor/out/ORDER_JLC_REV_C.md"
ORDER_FILES = ["hardware/sensor/out/fluidi_sensor_gerber_jlc.zip",
               "hardware/sensor/out/fluidi_sensor_bom_jlc.csv",
               "hardware/sensor/out/fluidi_sensor_cpl_jlc.csv"]

# (Zielordner, Quelle oder Glob, Zweck)
ITEMS = [
    ("1_jlc_upload", ORDER_FILES[0], "Gerber + Bohrdaten + Job (Upload JLC, PCB)"),
    ("1_jlc_upload", ORDER_FILES[1], "BOM JLC-Format (Upload PCBA)"),
    ("1_jlc_upload", ORDER_FILES[2], "CPL JLC-Format (Upload PCBA)"),
    ("2_bestellung", ORDER, "Bestellunterlage mit Checklisten (Kap. 4/5) und Remark (Kap. 8)"),
    ("2_bestellung", "docs/manuals/BESTELLEN_JLC.md", "Schritt-für-Schritt-Anleitung JLC-Formular"),
    ("2_bestellung", "hardware/sensor/out/REMARK_JLC_REV_C.txt", "Remark-Text zum Kopieren (eine Zeile, ohne Markdown)"),
    ("2_bestellung", "hardware/sensor/out/fluidi_sensor_bom_extra.csv", "Teile ohne JLC-Bestückung (lokal, DNP, Leiterplattenstrukturen)"),
    ("2_bestellung", "hardware/sensor/out/fluidi_sensor_cpl_jlc_rotationen.csv", "Rotationskorrekturen CPL (für Confirm Parts Placement)"),
    ("2_bestellung", "hardware/sensor/out/pdf/fluidi_sensor_bestueckung_F.pdf", "Bestückungsansicht Oberseite mit Pin-1 (Vorschau-Vergleich)"),
    ("2_bestellung", "hardware/sensor/out/pdf/fluidi_sensor_layout_lagen.pdf", "alle Lagen als PDF"),
    ("2_bestellung", "hardware/sensor/out/fluidi_sensor_schematic.pdf", "Schaltplan Rev C"),
    ("2_bestellung", "hardware/sensor/out/COSTS_REV_B.md", "Kostenrechnung Sensor (cost_rev_b.py)"),
    ("2_bestellung", "docs/reviews/phase5_kosten_final.md", "Kosten final Sensor/Gateway/System"),
    ("3_druck/sensor", "mechanical/sensor/print/*", "Druckdateien Sensor (3MF/STL/STEP)"),
    ("3_druck/gateway_pi", "mechanical/gateway_pi/print/*", "Druckdateien Gateway Pi Zero 2 W (G1 v4)"),
    ("3_druck", "mechanical/PRINT_SETTINGS.md", "Druckeinstellungen"),
    ("4_gateway", "hardware/gateway/BOM_GATEWAY.csv", "Gateway-Stückliste mit Preisen und Quellen (W-8)"),
    ("4_gateway", "docs/manuals/GATEWAY_SETUP.md", "Gateway einrichten"),
    ("5_firmware", "docs/manuals/PROGRAMMIEREN_SENSOR.md", "Erstprogrammierung Sensor"),
    # Phase 6 (2026-11-09): Anleitungen, Einkauf, Zeichnungen, Programmieradapter, Verguss, Renderings, Quellcode
    ("2_bestellung", "docs/manuals/EINKAUFSLISTE.md", "Einkaufsliste ausser JLC (Händlergruppierung, Versand)"),
    ("2_bestellung", "docs/manuals/EINKAUFSLISTE.csv", "Einkaufsliste Datenquelle (Preise, Lager, Abrufdatum, Beleg)"),
    ("3_druck/zeichnungen", "mechanical/drawings/*.pdf", "Massbilder Druckteile Sensor/Gateway"),
    ("4_gateway", "docs/manuals/APP.md", "PWA: Aufbau, Installation, Betrieb (Quellcode in 8_quellcode)"),
    ("5_firmware", "docs/manuals/TESTFIRMWARE.md", "Testfirmware (Musterprüfung)"),
    ("5_firmware", "docs/manuals/INSTALL_FIRMWARE_TOOLS.md", "Build-Werkzeuge installieren (Firmware Sensor)"),
    ("5_firmware/sensor", "firmware/sensor/README.md", "Build-Anleitung Firmware Sensor (make, Signierung)"),
    ("5_firmware/sensor/keys", "firmware/sensor/keys/README.md", "Schlüsselregeln (DEV/Produktion, Fingerabdruck)"),
    ("5_firmware", "firmware/PROTOCOL.md", "Funkprotokoll Sensor <-> Gateway"),
    ("6_anleitungen", "docs/manuals/MONTAGE_SENSOR.md", "Montage Sensor inkl. Verguss (Kap. 3a)"),
    ("6_anleitungen", "docs/manuals/BATTERIEWECHSEL.md", "Batteriewechsel"),
    ("6_anleitungen", "docs/manuals/INBETRIEBNAHME.md", "Inbetriebnahme"),
    ("6_anleitungen", "docs/manuals/PAIRING_KALIBRIERUNG.md", "Pairing und Kalibrierung"),
    ("6_anleitungen", "docs/manuals/FEHLERSUCHE.md", "Fehlersuche"),
    ("6_anleitungen", "docs/concepts/vergussmasse_versiegelung.md", "Konzept Vergussmasse/Versiegelung (D-030)"),
    ("6_anleitungen/sdb", "docs/references/Electrolube_ER2223-PartA_SDS_Rev0-2016-10-19_EN.pdf", "SDB ER2223 Teil A (EN)"),
    ("6_anleitungen/sdb", "docs/references/Electrolube_ER2223-PartA_SDS_Rev0.64-2023-10-27_SV.pdf", "SDB ER2223 Teil A (SV, 2023)"),
    ("6_anleitungen/sdb", "docs/references/Electrolube_ER2223-PartB_SDS_2023-10-02_HU.pdf",
     "SDB ER2223 Teil B (HU) – NICHT AUSREICHEND, DE/EN/FR/IT-Fassung vor dem ersten Beutel Pflicht (D-030)"),
    ("6_anleitungen/sdb", "docs/references/Electrolube_ER2223_TDS_Rev4-2019-03.pdf", "TDS ER2223"),
    ("6_anleitungen/sdb", "docs/references/UHU_PlusEndfest300-33g_SDS_V62-2026-07-17_DE.pdf", "SDB UHU plus endfest 300 (Fensterkleber)"),
    ("6_anleitungen/sdb", "docs/references/UHU_PlusEndfest300_TDS_2012-07.pdf", "TDS UHU plus endfest 300"),
    ("6_anleitungen/sdb", "docs/references/MAPA_Solo977_TechnicalSheet_DE_2026-09.pdf", "Handschuh MAPA Solo 977 (EN ISO 374)"),
    ("6_anleitungen/sdb", "docs/references/MAPA_Solo977_Bestaendigkeitstabelle_2024-04-11.pdf", "Beständigkeitstabelle Handschuh"),
    ("7_programmieradapter", "hardware/programmer/README.md", "Programmieradapter Rev 1 (Schaltung, Bezug, PL2303 Kap. 9)"),
    ("7_programmieradapter", "hardware/programmer/out/fluidi_programmer_schematic.pdf", "Schaltplan Programmieradapter"),
    ("9_renderings", "renders/final/*.png", "Produktrenderings"),
    ("9_renderings/pcb", "renders/pcb/*.png", "Leiterplatten-Renderings"),
]

# Quellarchiv aus dem Git-Stand (git archive, nur versionierte Dateien), ohne Schluesseldateien
SRC_ARCHIVE = os.path.join("8_quellcode", "fluidi_quellcode_firmware_app.tar.gz")
# K-1 (Red Team Phase 6): alles, was `make`, `make check`, `make TESTFW=n` und `make release` im Archiv brauchen
# (tools/check_config.py liest PINMAP und Netzliste, tests/Makefile ruft die Python-Tests in scripts/ auf).
SRC_PATHS = ["firmware", "app", "scripts/flash_sensor.py", "scripts/test_flash_sensor.py", "scripts/testfw_eval.py",
             "scripts/test_testfw_eval.py", "docs/interfaces/PINMAP_SENSOR.md", "hardware/sensor/out/fluidi_sensor.net"]
KEY_EXT = (".pem", ".key", ".der", ".p12", ".pfx")
# Einzige zugelassene Schluesseldatei: der oeffentliche Entwicklungsschluessel (liegt bewusst im Repository, .gitignore-
# Ausnahme, firmware/sensor/keys/README.md Regel 1). Alle anderen Schluesseldateien bleiben ausgeschlossen.
DEV_KEY = "firmware/sensor/keys/DEV_ONLY_fluidi_signing_ec-p256.pem"
MUSTER_DIR = os.path.join("5_firmware", "MUSTER_DEV")
GENERATED = {"README.md", "SHA256SUMS", "0_SICHERHEIT.md", os.path.join("5_firmware", "FIRMWARE_HINWEIS.md"), SRC_ARCHIVE,
             os.path.join("8_quellcode", "QUELLCODE.md")}


SAFETY_TEXT = """# Sicherheit zuerst – vor jeder Arbeit mit diesem Paket lesen

1. **Knopfzellen (CR2032):** Verschlucken ist lebensgefährlich (Verätzung innert Stunden). Zellen nur in der
   Originalverpackung (kindergesichert) oder in der abschliessbaren Box lagern; lose Zellen nie offen liegen lassen.
   Bei Verdacht auf Verschlucken sofort Notruf **144** (Sanität) bzw. Tox Info Suisse **145**. Wechsel nur nach
   `6_anleitungen/BATTERIEWECHSEL.md`; nur Panasonic CR2032 (D-006); Wareneingang nach `2_bestellung/EINKAUFSLISTE.md` S1.
2. **Vergussmasse ER2223 und Fensterkleber UHU plus endfest 300:** Sicherheitsdatenblätter in `6_anleitungen/sdb/`.
   Härter ER2223 Teil B ist **ätzend** (H314) und sensibilisierend. **Vor dem Öffnen des ersten Beutels** (D-030, unten):
   SDB Teil B in DE/EN/FR/IT beim Händler anfordern (vorliegend nur HU – nicht ausreichend), Handschuh-Beständigkeitsliste
   ablegen, Schutzausrüstung bereit (Korbbrille EN 166 Kennzeichnung 3 + Visier, Nitrilhandschuhe EN ISO 374,
   Schürze, Augenspülflasche, Halbmaske Filter A oder Absaugung; `2_bestellung/EINKAUFSLISTE.md` V-Z7…V-Z10).
   Ablauf `6_anleitungen/MONTAGE_SENSOR.md` Kap. 1 und 3a.
3. **Programmieren nur nach `5_firmware/PROGRAMMIEREN_SENSOR.md`:** nie mit eingelegter Zelle; Weg B nur mit
   Dummy-Scheibe, Netzteil 2.0 V (höchstens 2.1 V mit PL2303), Strombegrenzung 10 mA; USB zuerst ein, zuletzt aus.
4. **Testfirmware nie an Endnutzer** (auch nicht per OTA): nur Muster im Labor, `5_firmware/TESTFIRMWARE.md`.
   Die Binärdateien in `5_firmware/MUSTER_DEV/` sind DEV-signiert und **nicht freigegeben**.
5. **Gateway-Netzteil:** nur das Original-Netzteil (EU-Konformitätserklärung im Register, GW-PSU), nicht im Giessbereich
   der Pflanzen aufstellen, Kabel und Gehäuse unbeschädigt.
"""


def src_excludes(rev):
    """Pathspec-Ausschluesse: jede versionierte Schluesseldatei ausser DEV_KEY (git kann 'ausser' nicht direkt)."""
    files = subprocess.run(["git", "-C", ROOT, "ls-tree", "-r", "--name-only", rev, "--", *SRC_PATHS],
                           capture_output=True, text=True).stdout.split()
    return [f":(exclude){f}" for f in files if f.endswith(KEY_EXT) and f != DEV_KEY]


def make_archive(rev, dst):
    """git archive (deterministisch fuer gleichen Commit); prueft, dass kein privater Schluessel enthalten ist."""
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "wb") as fh:
        r = subprocess.run(["git", "-C", ROOT, "archive", "--format=tar.gz", rev, "--", *SRC_PATHS, *src_excludes(rev)],
                           stdout=fh)
    if r.returncode != 0:
        raise SystemExit("FEHLER: git archive")
    import tarfile
    with tarfile.open(dst, "r:gz") as tf:
        for m in tf.getmembers():
            if m.isfile():
                data = tf.extractfile(m).read()
                if m.name == DEV_KEY:
                    if not data.startswith(b"-----BEGIN PRIVATE KEY-----"):
                        raise SystemExit(f"FEHLER: {DEV_KEY} unerwarteter Inhalt")
                    continue
                if m.name.endswith(KEY_EXT) or b"PRIVATE KEY-----" in data:
                    raise SystemExit(f"FEHLER: Schluesselmaterial im Quellarchiv: {m.name}")
    return sha(dst)


def build_firmware(archive, outdir, log_lines):
    """K-1: Werks-Hex (DEV) reproduzierbar aus dem Quellarchiv bauen und `make check` als Probe laufen lassen.
    SDK/Toolchain ueber ~/fluidi-tools/env.sh (scripts/install_firmware_tools.sh). Liefert Liste der kopierten Dateien."""
    import tarfile
    import tempfile
    env_sh = os.path.expanduser("~/fluidi-tools/env.sh")
    if not os.path.isfile(env_sh):
        raise SystemExit(f"FEHLER: {env_sh} fehlt -> Firmware-Werkzeuge installieren oder --no-fw-build")
    with tempfile.TemporaryDirectory(prefix="fluidi_rel_") as td:
        with tarfile.open(archive, "r:gz") as tf:
            tf.extractall(td, filter="data")
        fw = os.path.join(td, "firmware", "sensor")
        for step in ("make", "make check"):
            r = subprocess.run(["bash", "-c", f"source '{env_sh}' && cd '{fw}' && {step}"], stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT, text=True)
            lines = r.stdout.strip().splitlines()
            keep = [x for x in lines if x.lstrip().startswith(("[ok]", "[sign]", "[factory]", "[check]", "OK", "Ran ", "FAILED"))]
            tail = (keep or lines)[-12:]
            log_lines.append(f"$ {step}  (aus entpacktem Quellarchiv) -> Exitcode {r.returncode}")
            log_lines += ["    " + x for x in tail]
            if r.returncode != 0:
                raise SystemExit(f"FEHLER: Probe-Build '{step}' aus dem Quellarchiv fehlgeschlagen:\n" + "\n".join(tail))
        out = []
        os.makedirs(outdir, exist_ok=True)
        for pat in ("fluidi-sensor-factory-*.hex", "fluidi-sensor-[0-9]*.bin"):
            for f in sorted(glob.glob(os.path.join(fw, "build", pat))):
                d = os.path.join(outdir, os.path.basename(f))
                shutil.copy2(f, d)
                out.append(d)
        if not any(x.endswith(".hex") for x in out):
            raise SystemExit("FEHLER: kein Werks-Hex gebaut")
        return out


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*a):
    try:
        return subprocess.run(["git", "-C", ROOT, *a], capture_output=True, text=True).stdout.strip()
    except OSError:
        return "-"


def sources():
    """Liste (Zielpfad relativ zum Paket, Quelle absolut, Zweck)."""
    out = []
    for sub, src, purpose in ITEMS:
        srcs = sorted(glob.glob(os.path.join(ROOT, src))) if "*" in src else [os.path.join(ROOT, src)]
        for s_ in srcs:
            out.append((os.path.join(sub, os.path.basename(s_)), s_, purpose))
    return out


def check():
    """Paket <-> Quellen vergleichen (W-1). Exit 0 nur ohne Abweichung."""
    if not os.path.isdir(DST):
        print("FEHLER: kein Paket", DST)
        return 1
    bad = []
    want = set()
    for rel, src, _ in sources():
        want.add(rel)
        d = os.path.join(DST, rel)
        if not os.path.isfile(src):
            bad.append(f"Quelle fehlt: {os.path.relpath(src, ROOT)}")
        elif not os.path.isfile(d):
            bad.append(f"fehlt im Paket: {rel}")
        elif sha(src) != sha(d):
            bad.append(f"veraltet: {rel} (Quelle {os.path.relpath(src, ROOT)} geaendert)")
    have = {os.path.relpath(os.path.join(dp, f), DST) for dp, _, fs in os.walk(DST) for f in fs}
    extra = {x for x in have - want - GENERATED if not x.startswith(MUSTER_DIR + os.sep)}
    if not any(x.startswith(MUSTER_DIR + os.sep) and x.endswith(".hex") for x in have) and "--no-fw-build" not in sys.argv:
        bad.append(f"kein DEV-Werks-Hex in {MUSTER_DIR} (K-1)")
    bad += [f"nicht mehr in der Quellliste: {x}" for x in sorted(extra)]
    readme = open(os.path.join(DST, "README.md"), encoding="utf-8").read()
    m = re.search(r"Git-Stand \| `([0-9a-f]+)`", readme)
    head = git("rev-parse", "--short", "HEAD")
    if not m:
        bad.append("Git-Stand fehlt im README")
    else:
        # Paket darf in einem spaeteren Commit liegen: massgebend ist, dass sich keine Quelle seit dem Stand geaendert hat
        srcs = sorted({os.path.relpath(s_, ROOT) for _, s_, _ in sources()})
        changed = git("diff", "--name-only", m.group(1), "HEAD", "--", *srcs)
        if changed:
            bad.append(f"Quellen seit Stand {m.group(1)} geaendert: {changed.split()}")
        if git("status", "--porcelain", "--", *srcs):
            bad.append("Quellen haben nicht committete Aenderungen")
        # Quellarchiv: aus dem Stand neu erzeugen und vergleichen; Quellcode seit dem Stand unveraendert?
        arc = os.path.join(DST, SRC_ARCHIVE)
        if not os.path.isfile(arc):
            bad.append(f"fehlt im Paket: {SRC_ARCHIVE}")
        else:
            import tempfile
            with tempfile.TemporaryDirectory() as td:
                ref = make_archive(m.group(1), os.path.join(td, "a.tar.gz"))
            if ref != sha(arc):
                bad.append(f"{SRC_ARCHIVE} entspricht nicht git archive {m.group(1)}")
        ch_src = git("diff", "--name-only", m.group(1), "HEAD", "--", *SRC_PATHS)
        if ch_src:
            bad.append(f"Quellcode seit Stand {m.group(1)} geaendert ({len(ch_src.split())} Dateien) -> Archiv veraltet")
    if "+ **nicht committete" in readme:
        bad.append("Paket wurde aus einer Arbeitskopie mit nicht committeten Aenderungen erzeugt")
    for b_ in bad:
        print("ABWEICHUNG:", b_)
    print("ERGEBNIS --check:", "Paket aktuell" if not bad else f"{len(bad)} Abweichung(en) -> Paket neu erzeugen")
    return 0 if not bad else 1


def probe():
    """--probe: Quellarchiv aus HEAD in ein Temp-Verzeichnis, Firmware daraus bauen + make check. Schreibt nichts ins Paket."""
    import tempfile
    head_full = git("rev-parse", "HEAD")
    with tempfile.TemporaryDirectory(prefix="fluidi_probe_") as td:
        a = os.path.join(td, "src.tar.gz")
        h = make_archive(head_full, a)
        log = []
        files = build_firmware(a, os.path.join(td, "out"), log)
        print(f"Quellarchiv {head_full[:7]} sha256 {h}")
        print("\n".join(log))
        for f in files:
            print(f"  {os.path.basename(f)}  {sha(f)}")
    print("ERGEBNIS --probe: ok")
    return 0


def main():
    if "--check" in sys.argv:
        return check()
    if "--probe" in sys.argv:
        return probe()
    allow_dirty = "--allow-dirty" in sys.argv
    dirty_src = [os.path.relpath(s_, ROOT) for _, s_, _ in sources()
                 if git("status", "--porcelain", "--", os.path.relpath(s_, ROOT))]
    if dirty_src and not allow_dirty:
        print("FEHLER: nicht committete Quellen -> erst committen (W-1):")
        for x in dirty_src:
            print("   ", x)
        return 1
    order_txt = open(os.path.join(ROOT, ORDER), encoding="utf-8").read()
    for f in ORDER_FILES:
        m = re.search(re.escape(os.path.basename(f)) + r".*?`([0-9a-f]{64})`", order_txt)
        if not m or sha(os.path.join(ROOT, f)) != m.group(1):
            print(f"FEHLER: {f} entspricht nicht dem Hash in {ORDER} -> kein Release")
            return 1
    if os.path.isdir(DST):
        shutil.rmtree(DST)
    rows = []
    for sub, src, purpose in ITEMS:
        srcs = sorted(glob.glob(os.path.join(ROOT, src))) if "*" in src else [os.path.join(ROOT, src)]
        if not srcs:
            print(f"FEHLER: Quelle fehlt: {src}")
            return 1
        for s in srcs:
            d = os.path.join(DST, sub, os.path.basename(s))
            os.makedirs(os.path.dirname(d), exist_ok=True)
            shutil.copy2(s, d)
            hs, hd = sha(s), sha(d)
            assert hs == hd, (s, d)
            rel_s = os.path.relpath(s, ROOT)
            dirty = bool(git("status", "--porcelain", "--", rel_s))
            rows.append((os.path.relpath(d, DST), rel_s, hd, os.path.getsize(d), purpose, dirty))

    # Quellarchiv (Projektauftrag: Firmware Sensor/Gateway und PWA im Quellcode) aus HEAD, ohne Schluessel
    head_full = git("rev-parse", "HEAD")
    arc = os.path.join(DST, SRC_ARCHIVE)
    h_arc = make_archive(head_full, arc)
    rows.append((SRC_ARCHIVE, f"git archive {head_full[:7]} -- {' '.join(SRC_PATHS)} (ohne *.pem/*.key/*.der)", h_arc,
                 os.path.getsize(arc), "Quellcode Firmware Sensor + Gateway, PWA, Flash-Werkzeug", False))
    qhint = os.path.join(DST, "8_quellcode", "QUELLCODE.md")
    with open(qhint, "w", encoding="utf-8") as fh:
        fh.write("# Quellcode – Hinweis zum Release Rev C\n\n")
        fh.write(f"Archiv `fluidi_quellcode_firmware_app.tar.gz` = `git archive {head_full}` der Pfade "
                 f"`{'`, `'.join(SRC_PATHS)}` (nur versionierte Dateien, deterministisch: gleicher Commit → gleicher sha256).\n\n")
        fh.write("- **Schlüssel:** einzig enthalten ist der öffentliche Entwicklungsschlüssel `firmware/sensor/keys/DEV_ONLY_fluidi_signing_ec-p256.pem` "
                 "(bewusst im Repository, kein Schutz; nötig für `make` und `make TESTFW=n`). Alle anderen Schlüsseldateien sind ausgeschlossen; "
                 "der Inhalt wird beim Erzeugen auf „PRIVATE KEY“ geprüft. Produktionsschlüssel sind nie im Repository "
                 "(`firmware/sensor/keys/README.md`).\n")
        fh.write("- Für den Build ebenfalls enthalten: `docs/interfaces/PINMAP_SENSOR.md`, `hardware/sensor/out/fluidi_sensor.net` "
                 "(Prüfung `make check`), Python-Tests in `scripts/` (K-1 Red Team).\n")
        fh.write("- Firmware Sensor: Bau und Signierung `5_firmware/sensor/README.md`, Werkzeuge `5_firmware/INSTALL_FIRMWARE_TOOLS.md`, "
                 "Flashen `5_firmware/PROGRAMMIEREN_SENSOR.md` (`scripts/flash_sensor.py` im Archiv).\n")
        fh.write("- Gateway (Python, keine Binärdateien): `firmware/gateway/` im Archiv, Installation `4_gateway/GATEWAY_SETUP.md` "
                 "(`firmware/gateway/install/install_gateway.sh`).\n")
        fh.write("- PWA (statisch, kein Build-Schritt): `app/` im Archiv, Anleitung `4_gateway/APP.md`; das Gateway liefert die PWA aus.\n")
        fh.write("- Prüfen: `make_release_rev_c.py --check` erzeugt das Archiv aus dem Commit neu und vergleicht den sha256.\n")
    rows.append((os.path.relpath(qhint, DST), "(erzeugt von production/make_release_rev_c.py)", sha(qhint),
                 os.path.getsize(qhint), "Hinweis Quellcode", False))

    # K-1: DEV-signiertes Werks-Hex fuer Muster, reproduzierbar aus dem Quellarchiv gebaut (Probe-Build + make check)
    fw_log = []
    muster = []
    if "--no-fw-build" not in sys.argv:
        muster = build_firmware(arc, os.path.join(DST, MUSTER_DIR), fw_log)
        for f in muster:
            rows.append((os.path.relpath(f, DST), f"make (DEV_ONLY-Schluessel) aus {SRC_ARCHIVE} @ {head_full[:7]}", sha(f),
                         os.path.getsize(f), "MUSTER, DEV-Schlüssel, NICHT FREIGEGEBEN", False))
    hint = os.path.join(DST, "5_firmware", "FIRMWARE_HINWEIS.md")
    with open(hint, "w", encoding="utf-8") as fh:
        fh.write("# Firmware Sensor – Hinweis zum Release Rev C\n\n")
        fh.write("> **NUR MUSTER – DEV-SCHLÜSSEL – NICHT FREIGEGEBEN.** Die Dateien in `5_firmware/MUSTER_DEV/` sind mit dem "
                 "öffentlichen Entwicklungsschlüssel `DEV_ONLY_fluidi_signing_ec-p256.pem` signiert. Ein damit gebauter MCUboot "
                 "nimmt jedes Image an, das jemand mit dieser (öffentlichen) Datei signiert – **nie an Endnutzer ausliefern**, "
                 "nur für Prototypen im Labor. `scripts/flash_sensor.py program --lock` verweigert den DEV-Schlüssel.\n\n")
        fh.write(f"- Gebaut beim Erzeugen dieses Pakets mit `make` aus dem entpackten Quellarchiv `{SRC_ARCHIVE}` "
                 f"(Git `{head_full}`), Toolchain über `~/fluidi-tools/env.sh` (`5_firmware/INSTALL_FIRMWARE_TOOLS.md`). "
                 "Danach `make check` im selben Baum (Probe, siehe unten). Das unsignierte Bild ist reproduzierbar; die "
                 "ECDSA-Signatur ist bei jedem Bau anders, deshalb gilt der sha256 dieser Datei.\n")
        fh.write("- Flashen: `5_firmware/PROGRAMMIEREN_SENSOR.md` (ROM-UART-Bootloader, PL2303 Weg A/B, Sicherheitsregeln Kap. 1).\n")
        fh.write("- Testfirmware (`make TESTFW=n`) ist **nicht** beigelegt; bauen nach `5_firmware/TESTFIRMWARE.md`, nie an Endnutzer.\n")
        fh.write("- **Serienstand:** nur `make release SIGN_KEY=<Produktionsschlüssel ausserhalb des Repositorys>` – der "
                 "Produktionsschlüssel ist nie im Repository und nie in diesem Paket (`5_firmware/sensor/keys/README.md`).\n\n")
        if muster:
            fh.write("| Datei | sha256 | Bytes |\n|---|---|---|\n")
            for f in muster:
                fh.write(f"| `MUSTER_DEV/{os.path.basename(f)}` | `{sha(f)}` | {os.path.getsize(f)} |\n")
            fh.write("\nProbe-Build (Ausschnitt):\n\n```\n" + "\n".join(fw_log) + "\n```\n")
        else:
            fh.write("Ohne Firmware-Build erzeugt (`--no-fw-build`): keine Binärdateien.\n")
    rows.append((os.path.relpath(hint, DST), "(erzeugt von production/make_release_rev_c.py)", sha(hint),
                 os.path.getsize(hint), "Firmware-Hinweis", False))

    # S W-7 (Sicherheit Schluss): Sicherheitsabschnitt auf Paketebene, D-030-Bedingungen aus DECISIONS.md uebernommen
    dec = open(os.path.join(ROOT, "docs", "requirements", "DECISIONS.md"), encoding="utf-8").read()
    d030 = dec[dec.find("### D-030"):dec.find("### D-031")].strip() if "### D-030" in dec else "(D-030 nicht gefunden)"
    sic = os.path.join(DST, "0_SICHERHEIT.md")
    with open(sic, "w", encoding="utf-8") as fh:
        fh.write(SAFETY_TEXT)
        fh.write("\n## Freigabebedingungen Vergussmasse (Auszug `docs/requirements/DECISIONS.md`)\n\n" + d030 + "\n")
    rows.append(("0_SICHERHEIT.md", "(erzeugt, D-030 aus docs/requirements/DECISIONS.md)", sha(sic), os.path.getsize(sic),
                 "Sicherheit zuerst (Sicherheit Schluss W-7)", False))

    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    head = git("rev-parse", "--short", "HEAD")
    any_dirty = any(r[5] for r in rows)
    with open(os.path.join(DST, "SHA256SUMS"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(f"{r[2]}  {r[0]}\n")
    with open(os.path.join(DST, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("# fluidi – Release-Paket Rev C (Sensor, Gateway, Anleitungen, Quellcode; Stand Phase 6)\n\n")
        fh.write("| | |\n|---|---|\n")
        fh.write(f"| Erzeugt | {now} von `.venv/bin/python production/make_release_rev_c.py` |\n")
        fh.write(f"| Git-Stand | `{head}`{' + **nicht committete Änderungen** in markierten Quellen (Spalte „geändert“)' if any_dirty else ''} |\n")
        fh.write(f"| Bestellunterlage | `2_bestellung/ORDER_JLC_REV_C.md` (Kap. 1: Soll-sha256 der Upload-Dateien) |\n")
        fh.write("| **Sicherheit** | **Zuerst `0_SICHERHEIT.md` lesen** (Knopfzellen, Verguss/Kleber mit SDB in `6_anleitungen/sdb/`, "
                 "Programmieren nur nach Anleitung, Testfirmware nie an Endnutzer, D-030-Bedingungen) |\n")
        fh.write("| Prüfen | `cd production/rev-C && sha256sum -c SHA256SUMS` |\n")
        fh.write("| Status | **Keine Bestellung ausgelöst.** Bestellen nur nach Freigabe durch den Auftraggeber "
                 "(`2_bestellung/BESTELLEN_JLC.md`) |\n\n")
        fh.write("Alle Dateien sind **Kopien** (keine Neuerzeugung); jede Kopie wurde beim Erzeugen per sha256 mit der "
                 "Quelle verglichen. Die drei Upload-Dateien in `1_jlc_upload/` entsprechen den Hashes in "
                 "ORDER_JLC_REV_C.md Kap. 1 (sonst bricht das Skript ab).\n\n")
        fh.write("| Datei im Paket | Quelle im Repo | sha256 | Bytes | Zweck | geändert* |\n|---|---|---|---|---|---|\n")
        for r in rows:
            fh.write(f"| `{r[0]}` | `{r[1]}` | `{r[2]}` | {r[3]} | {r[4]} | {'ja' if r[5] else ''} |\n")
        fh.write("\n*geändert = Quelle hat beim Erzeugen nicht committete Änderungen (Arbeitskopie). Nach dem Commit "
                 "das Paket neu erzeugen, damit Git-Stand und Inhalt übereinstimmen.\n\n")
        fh.write("Quellcode Firmware Sensor/Gateway und PWA: `8_quellcode/` (git archive des Git-Stands, ohne Schlüssel, "
                 "Hinweis `8_quellcode/QUELLCODE.md`). DEV-signiertes Muster-Werks-Hex in `5_firmware/MUSTER_DEV/` (nicht freigegeben, `5_firmware/FIRMWARE_HINWEIS.md`). "
                 "Nicht im Paket: alte ESP32-Gateway-Druckteile (`mechanical/gateway/`, durch D-014 ersetzt), Simulationen, Prüfberichte.\n")
    print(f"{len(rows)} Dateien -> {os.path.relpath(DST, ROOT)}; Git {head}, Arbeitskopie geändert: {any_dirty}")
    for r in rows[:3]:
        print(f"  {r[0]}  {r[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
