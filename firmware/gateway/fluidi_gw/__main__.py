"""fluidi Gateway – Kommandozeile.

  python3 -m fluidi_gw serve  [-c /etc/fluidi/gateway.toml]       Dienst (systemd)
  python3 -m fluidi_gw sim    [--port 8080] [--sensors 6]          Simulation ohne Hardware, HTTP auf localhost
  python3 -m fluidi_gw setup-code   [-c …]                         Einrichtungscode anzeigen (nur lokal/SSH)
  python3 -m fluidi_gw reset-password [-c …]                       Passwort-Reset (UC-16): neuer Einrichtungscode
  python3 -m fluidi_gw pki-init [-c …] [--force]                   Einmal-CA + Server-Zertifikat (fluidi.local)
  python3 -m fluidi_gw fingerprint [-c …]                          SHA-256 der CA anzeigen
  python3 -m fluidi_gw test-image OUT.bin --key-out K.pem          Test-Abbild (MCUboot-Format) mit Testschlüssel
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import config


def main(argv=None):
    ap = argparse.ArgumentParser(prog="fluidi_gw", description="fluidi Gateway")
    sub = ap.add_subparsers(dest="cmd")
    for name in ("serve", "sim", "setup-code", "reset-password", "pki-init", "fingerprint"):
        p = sub.add_parser(name)
        p.add_argument("-c", "--config", default="/etc/fluidi/gateway.toml")
        p.add_argument("--data-dir")
        if name in ("serve", "sim"):
            p.add_argument("--port", type=int)
            p.add_argument("--host")
            p.add_argument("--quiet", action="store_true")
        if name == "sim":
            p.add_argument("--sensors", type=int, default=6)
            p.add_argument("--speed", type=float, default=0.002)
            p.add_argument("--history-days", type=int, default=45)
            p.add_argument("--testfw", type=int, choices=[0, 1, 2, 3, 4], default=0,
                           help="letzter Sim-Sensor mit Testfirmware TF-n (Diagnose-Anzeige prüfen)")
        if name == "pki-init":
            p.add_argument("--force", action="store_true")
    ti = sub.add_parser("test-image")
    ti.add_argument("out")
    ti.add_argument("--key-out", required=True)
    ti.add_argument("--version", default="1.0.4")
    ti.add_argument("--size", type=int, default=150_000)
    a = ap.parse_args(argv)
    cmd = a.cmd or "serve"

    if cmd == "test-image":
        from . import crypto, mcuboot
        k = crypto.SigningKey()
        img = mcuboot.build(bytes((i * 7) & 0xFF for i in range(a.size)), tuple(int(x) for x in a.version.split(".")), key=k)
        Path(a.out).write_bytes(img)
        Path(a.key_out).write_text(k.public_pem())
        print(f"{a.out}: {len(img)} Byte, Version {a.version}; öffentlicher TEST-Schlüssel: {a.key_out} (nicht produktiv!)")
        return 0

    ov = {"data_dir": Path(a.data_dir) if getattr(a, "data_dir", None) else None}
    if cmd == "sim":
        ov.update(radio="sim", tls=False, https_port=a.port or 8080, http_port=0, host=a.host or "127.0.0.1",
                  sim_sensors=a.sensors, sim_speed=a.speed, sim_history_days=a.history_days, sim_testfw=a.testfw, time_mode="sim",
                  data_dir=ov["data_dir"] or Path.home() / ".cache" / "fluidi-sim", quiet=a.quiet, dashboard_port=(a.port or 8080) + 1)
    elif cmd == "serve":
        ov.update(https_port=a.port, host=a.host, quiet=a.quiet or None)
    cfg = config.load(a.config if Path(a.config).exists() else None, **ov)

    if cmd in ("serve", "sim"):
        from . import service
        service.run(cfg)
        return 0
    if cmd == "pki-init":
        from . import pki
        fp = pki.init(cfg.tls_path, cfg.hostname, force=a.force)
        print(f"Zertifikat für {cfg.hostname} erstellt. CA-Fingerabdruck (SHA-256):\n{fp}")
        return 0
    if cmd == "fingerprint":
        from . import pki
        print(pki.fingerprint(cfg.tls_path))
        return 0
    from . import model, store, timesvc
    st = store.Store(cfg.db_path)
    m = model.Model(st, cfg, timesvc.TimeService("sim"))
    if cmd == "setup-code":
        print(m.setup_code or "Bereits eingerichtet (Passwort gesetzt). Zurücksetzen: reset-password")
    elif cmd == "reset-password":
        print(f"Passwort zurückgesetzt. Neuer Einrichtungscode: {m.reset_password()}")
    st.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
