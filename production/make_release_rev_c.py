#!/usr/bin/env python3
"""fluidi Release-Paket Rev C -> production/rev-C/ (nur KOPIEN, keine Neuerzeugung).

Kopiert Fertigungs-, Bestell- und Druckdateien aus dem Repo, prueft danach jede Kopie per sha256 gegen die Quelle und
die drei Bestelldateien zusaetzlich gegen die Hashes in hardware/sensor/out/ORDER_JLC_REV_C.md Kap. 1. Schreibt
production/rev-C/README.md (Inhalt, Quelle, sha256, Git-Stand) und production/rev-C/SHA256SUMS (Format sha256sum -c).
Abbruch (Exit 1), wenn eine Bestelldatei nicht dem ORDER-Hash entspricht.

Abbruch (Exit 1) auch, wenn eine Quelle nicht committete Aenderungen hat (Red Team W-1): Das Paket entsteht nur aus
einem sauberen Git-Stand; Ausnahme nur zum Testen mit --allow-dirty (README markiert das).

Aufruf : .venv/bin/python production/make_release_rev_c.py [--allow-dirty]
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
]


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
    extra = have - want - {"README.md", "SHA256SUMS", os.path.join("5_firmware", "FIRMWARE_HINWEIS.md")}
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
    if "+ **nicht committete" in readme:
        bad.append("Paket wurde aus einer Arbeitskopie mit nicht committeten Aenderungen erzeugt")
    for b_ in bad:
        print("ABWEICHUNG:", b_)
    print("ERGEBNIS --check:", "Paket aktuell" if not bad else f"{len(bad)} Abweichung(en) -> Paket neu erzeugen")
    return 0 if not bad else 1


def main():
    if "--check" in sys.argv:
        return check()
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

    # Firmware-Hinweis (Text, keine Binaerdateien: Build-Artefakte sind nicht versioniert und schluesselgebunden)
    fw_dir = os.path.join(ROOT, "firmware", "sensor", "build")
    fw = sorted(glob.glob(os.path.join(fw_dir, "fluidi-sensor-factory-*.hex")) +
                glob.glob(os.path.join(fw_dir, "fluidi-sensor-*.bin")))
    hint = os.path.join(DST, "5_firmware", "FIRMWARE_HINWEIS.md")
    with open(hint, "w", encoding="utf-8") as fh:
        fh.write("# Firmware Sensor – Hinweis zum Release Rev C\n\n")
        fh.write("Das Paket enthält **keine** Firmware-Binärdateien. Gründe: Die Build-Artefakte in "
                 "`firmware/sensor/build/` sind nicht versioniert, das Werks-Hex ist an den Signierschlüssel gebunden "
                 "(Dateiname `…-key<Fingerabdruck>.hex`), und die Firmware wird erst am Muster freigegeben.\n\n")
        fh.write("- Quelle: `firmware/sensor` (Bau: `make`, siehe `firmware/sensor/README.md`).\n")
        fh.write("- Programmieren: `5_firmware/PROGRAMMIEREN_SENSOR.md` (ROM-UART-Bootloader, Programmieradapter Rev 1 "
                 "oder Behelf, Sicherheitsregeln Kap. 1).\n")
        fh.write("- Werkzeug: `scripts/flash_sensor.py`.\n\n")
        fh.write("Arbeitsstand beim Erzeugen dieses Pakets (nur zur Nachverfolgung, **nicht freigegeben**):\n\n")
        if fw:
            fh.write("| Datei | sha256 |\n|---|---|\n")
            for f in fw:
                fh.write(f"| `{os.path.relpath(f, ROOT)}` | `{sha(f)}` |\n")
        else:
            fh.write("keine Build-Artefakte vorhanden\n")
    rows.append((os.path.relpath(hint, DST), "(erzeugt von production/make_release_rev_c.py)", sha(hint),
                 os.path.getsize(hint), "Firmware-Hinweis", False))

    now = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    head = git("rev-parse", "--short", "HEAD")
    any_dirty = any(r[5] for r in rows)
    with open(os.path.join(DST, "SHA256SUMS"), "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(f"{r[2]}  {r[0]}\n")
    with open(os.path.join(DST, "README.md"), "w", encoding="utf-8") as fh:
        fh.write("# fluidi – Release-Paket Rev C (Sensor + Gateway-Druckteile)\n\n")
        fh.write("| | |\n|---|---|\n")
        fh.write(f"| Erzeugt | {now} von `.venv/bin/python production/make_release_rev_c.py` |\n")
        fh.write(f"| Git-Stand | `{head}`{' + **nicht committete Änderungen** in markierten Quellen (Spalte „geändert“)' if any_dirty else ''} |\n")
        fh.write(f"| Bestellunterlage | `2_bestellung/ORDER_JLC_REV_C.md` (Kap. 1: Soll-sha256 der Upload-Dateien) |\n")
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
        fh.write("Nicht im Paket: Programmieradapter (`hardware/programmer/`), Gateway-Software (`firmware/gateway/`), "
                 "PWA (`app/`), alte ESP32-Gateway-Druckteile (`mechanical/gateway/`, durch D-014 ersetzt).\n")
    print(f"{len(rows)} Dateien -> {os.path.relpath(DST, ROOT)}; Git {head}, Arbeitskopie geändert: {any_dirty}")
    for r in rows[:3]:
        print(f"  {r[0]}  {r[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
