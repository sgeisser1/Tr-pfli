"""fluidi – Datenaufbereitung und Kalibrierungsrechnung (Python-Spiegel von app/js/calc.js).

Wird vom Mock-Server benutzt und in app/tests/test_calc.py gegen dieselben Testvektoren
(app/tests/vectors/calc_vectors.json) geprüft wie die JavaScript-Fassung. Nur Standardbibliothek.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

AIR_MARGIN_PP = 10
FLOOD_MARGIN_PP = 10
MIN_SPAN_REL = 0.02
T_REF_C = 20.0
SIGNAL_LEVELS = (-70, -80, -88, -95)


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def round1(x):
    """Auf 0.1 runden, halb weg von null (wie calc.js, nicht Bankers-Rounding)."""
    if not _finite(x):
        return None
    s = -1 if x < 0 else 1
    return s * math.floor(abs(x) * 10 + 0.5) / 10


def compensate_raw(raw, temp_c, coeff_per_k=0.0, t_ref_c=T_REF_C):
    """Temperaturkompensation (Platzhalter): raw(T) = raw(Tref) * (1 + k (T - Tref))."""
    if not _finite(raw):
        return None
    if not coeff_per_k or not _finite(temp_c):
        return raw
    f = 1 + coeff_per_k * (temp_c - t_ref_c)
    if f <= 0.5 or f >= 1.5:
        return raw
    return raw / f


def span_ok(dry_raw, wet_raw) -> bool:
    if not _finite(dry_raw) or not _finite(wet_raw):
        return False
    ref = max(abs(dry_raw), abs(wet_raw))
    if ref == 0:
        return False
    return abs(wet_raw - dry_raw) / ref >= MIN_SPAN_REL


def moisture_index(raw_comp, dry_raw, wet_raw):
    if not _finite(raw_comp) or not span_ok(dry_raw, wet_raw):
        return None
    return (raw_comp - dry_raw) / (wet_raw - dry_raw) * 100


def classify(index_unclamped, threshold_pct):
    if not _finite(index_unclamped):
        return "invalid"
    if index_unclamped < -AIR_MARGIN_PP:
        return "air"
    if index_unclamped > 100 + FLOOD_MARGIN_PP:
        return "flooded"
    if _finite(threshold_pct) and index_unclamped < threshold_pct:
        return "dry"
    return "ok"


def evaluate(raw, temp_c, cal, threshold_pct):
    if not cal or not cal.get("dry") or not cal.get("wet"):
        return {"moisture_pct": None, "moisture_unclamped": None, "moisture_state": "uncalibrated"}
    k = cal.get("temp_coeff_per_k") or 0.0
    t_ref = cal.get("t_ref_c") if _finite(cal.get("t_ref_c")) else T_REF_C
    comp = compensate_raw(raw, temp_c, k, t_ref)
    idx = moisture_index(comp, cal["dry"]["raw"], cal["wet"]["raw"])
    state = classify(idx, threshold_pct)
    pct = None
    if state in ("ok", "dry"):
        pct = round1(min(100.0, max(0.0, idx)))
    return {"moisture_pct": pct, "moisture_unclamped": round1(idx), "moisture_state": state}


def median(xs):
    s = sorted(xs)
    m = len(s) >> 1
    return s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2


def robust_mean(samples):
    xs = [x for x in (samples or []) if _finite(x)]
    if not xs:
        return {"mean": None, "stddev": None, "n": 0, "outliers": 0}
    med = median(xs)
    mad = median([abs(x - med) for x in xs])
    lim = 3.5 * 1.4826 * mad
    if mad == 0:
        kept = [x for x in xs if x == med or len(xs) < 3]
    else:
        kept = [x for x in xs if abs(x - med) <= lim]
    use = kept or xs
    mean = sum(use) / len(use)
    sd = None
    if len(use) >= 2:
        sd = math.sqrt(sum((x - mean) ** 2 for x in use) / (len(use) - 1))
    return {"mean": mean, "stddev": sd, "n": len(use), "outliers": len(xs) - len(use)}


def signal_quality(rssi_dbm):
    if not _finite(rssi_dbm):
        return 0
    q = 4
    for lim in SIGNAL_LEVELS:
        if rssi_dbm >= lim:
            return q
        q -= 1
    return 0


def battery_bars(pct):
    if not _finite(pct):
        return 0
    for lim, bars in ((75, 4), (50, 3), (25, 2), (10, 1)):
        if pct >= lim:
            return bars
    return 0


def choose_resolution(from_s, to_s, per_day, max_points=800):
    days = max(0, to_s - from_s) / 86400
    if days * per_day <= max_points:
        return "raw"
    if days * 24 <= max_points:
        return "hour"
    return "day"


def is_stale(last_s, now_s, per_day):
    if not _finite(last_s):
        return True
    interval = 86400 / max(1, per_day)
    return now_s - last_s > max(3 * interval, 7200)


def bucket_start(t_s: int, res: str, tz: ZoneInfo) -> int:
    """Beginn des Stunden- bzw. Tages-Eimers in lokaler Zeit (Tage nach Ortszeit, DST-fest)."""
    dt = datetime.fromtimestamp(t_s, tz)
    if res == "hour":
        dt = dt.replace(minute=0, second=0, microsecond=0)
    elif res == "day":
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        raise ValueError(res)
    return int(dt.timestamp())


def aggregate(points, res, tz_name="Europe/Zurich"):
    """points: Liste (t_s, moisture|None, temp|None), zeitlich sortiert.

    Ergebnis: dict mit Listen t, moisture (Mittel), moisture_min, moisture_max, temp_c (Mittel).
    Werte None (air/flooded/invalid) zählen nicht zum Mittel; Eimer ohne gültigen Wert -> None.
    """
    tz = ZoneInfo(tz_name)
    out = {"t": [], "moisture": [], "moisture_min": [], "moisture_max": [], "temp_c": []}
    cur = None
    ms, ts = [], []

    def flush():
        if cur is None:
            return
        out["t"].append(cur)
        out["moisture"].append(round1(sum(ms) / len(ms)) if ms else None)
        out["moisture_min"].append(round1(min(ms)) if ms else None)
        out["moisture_max"].append(round1(max(ms)) if ms else None)
        out["temp_c"].append(round1(sum(ts) / len(ts)) if ts else None)

    for t, m, temp in points:
        b = bucket_start(t, res, tz)
        if b != cur:
            flush()
            cur, ms, ts = b, [], []
        if _finite(m):
            ms.append(m)
        if _finite(temp):
            ts.append(temp)
    flush()
    return out


def iso(t_s) -> str | None:
    if t_s is None:
        return None
    return datetime.fromtimestamp(int(t_s), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
