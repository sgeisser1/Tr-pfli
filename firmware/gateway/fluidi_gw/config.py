"""Konfiguration des Gateways: Datei /etc/fluidi/gateway.toml (install/gateway.toml) + Kommandozeile.

Nur Betriebsparameter (Pfade, Ports, Funk). Fachliche Einstellungen (Intervall, LED, Dashboard …) liegen in der
Datenbank und werden über die API geändert.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib  # Python ≥ 3.11
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

HERE = Path(__file__).resolve().parent
REPO_APP = HERE.parent.parent.parent / "app"   # Entwicklung im Repository


@dataclass
class Config:
    data_dir: Path = Path("/var/lib/fluidi")
    app_dir: Path = REPO_APP if REPO_APP.is_dir() else Path("/opt/fluidi/current/app")
    tls_dir: Path | None = None              # Standard: data_dir/tls
    host: str = "0.0.0.0"
    https_port: int = 443
    http_port: int = 80                      # nur Weiterleitung, /ca.crt, Fingerabdruck
    dashboard_port: int = 8080               # öffentliches Dashboard (HTTP, nur lesen, D-020)
    tls: bool = True
    hostname: str = "fluidi.local"
    radio: str = "bleak"                     # bleak | sim
    adapter: str = "hci0"
    passive_scan: bool = False
    max_connections: int = 3                 # PROTOCOL 2.5 Regel 3
    p_miss: float = 0.10                     # PROTOCOL 2.2 (ANNAHME bis Koexistenztest OP-K12, FW-P8)
    sim_sensors: int = 0
    sim_speed: float = 0.002                 # Zeitraffer der simulierten Sensoren
    sim_history_days: int = 30
    sim_autopair: bool = True
    climate: str = "auto"                    # auto | sht4x | sim | off
    i2c_bus: int = 1
    climate_addr: int = 0x44                 # SHT4x-AD1B (Datenblatt V7.3 S. 1)
    climate_interval_s: int = 300
    fw_pubkey: Path | None = None            # öffentlicher Signaturschlüssel Sensor-Firmware (PEM)
    gw_update_pubkey: Path | None = None     # öffentlicher Schlüssel für Gateway-Updates (PEM)
    pbkdf2_iterations: int = 200_000
    time_mode: str = "system"                # system | sim
    helper_dir: Path | None = None           # Anfragen an den Root-Helfer (helper.py), Standard data_dir/requests
    quiet: bool = False
    # Startkalibrierung (REQ-MES-07) in 0.01 pF: ANNAHME aus MESSKETTE_SALZ.md Kap. 0 (D3, 13.3 pF trocken),
    # Nasswert grob; PROTOTYP-PRÜFUNG am Muster (API-3)
    default_cal: dict = field(default_factory=lambda: {"erde": (1330, 4000), "granulat": (1250, 3600)})

    @property
    def db_path(self) -> Path:
        return self.data_dir / "fluidi.sqlite"

    @property
    def tls_path(self) -> Path:
        return self.tls_dir or (self.data_dir / "tls")

    @property
    def requests_path(self) -> Path:
        return self.helper_dir or (self.data_dir / "requests")


def load(path: str | Path | None, **overrides) -> Config:
    cfg = Config()
    if path and Path(path).is_file():
        if tomllib is None:
            print("Python < 3.11: TOML-Datei wird ignoriert", file=sys.stderr)
        else:
            with open(path, "rb") as f:
                data = tomllib.load(f)
            for k, v in data.get("gateway", data).items():
                if hasattr(cfg, k):
                    cur = getattr(cfg, k)
                    if isinstance(cur, Path) or k.endswith(("_dir", "pubkey")):
                        v = Path(v)
                    setattr(cfg, k, v)
    for k, v in overrides.items():
        if v is not None and hasattr(cfg, k):
            setattr(cfg, k, v)
    return cfg
