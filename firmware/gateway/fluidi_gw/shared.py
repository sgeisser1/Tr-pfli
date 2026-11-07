"""Gemeinsamer Rechenkern von PWA, Mock und Gateway (eine Quelle, keine Kopie):
app/dev/fluidi_calc.py (Feuchteindex, Aggregation, GATEWAY_API Kap. 7) und app/dev/fluidi_analysis.py
(Giess-Erkennung, Prognose, Stimmung, SOFTWARE_CONCEPT Kap. 8). Geprüft gegen app/tests/vectors/calc_vectors.json.
Auf dem Pi liegt app/ neben dem Paket (/opt/fluidi/current/app), im Repository unter app/.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

from .config import Config


def load(app_dir: Path):
    dev = Path(app_dir) / "dev"
    if not (dev / "fluidi_calc.py").is_file():
        raise RuntimeError(f"fluidi_calc.py nicht gefunden in {dev}")
    if str(dev) not in sys.path:
        sys.path.insert(0, str(dev))
    return importlib.import_module("fluidi_calc"), importlib.import_module("fluidi_analysis")


C, AN = load(Config().app_dir)
