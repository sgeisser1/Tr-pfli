"""fluidi – Auswertungen im Gateway: Giess-Erkennung, Austrocknungsmodell, Prognose, Stimmung.

Referenz für docs/software/SOFTWARE_CONCEPT.md Kap. 7 (Prognosemodell). Nur Standardbibliothek,
damit derselbe Code auf dem Raspberry Pi Zero 2 W (D-014) läuft. Eingaben sind gültige Punkte
(t in Unix-Sekunden, m = Feuchteindex in %, nur Zustände ok/dry; air/flooded/invalid vorher entfernen).

Modell (bewusst einfach und erklärbar):
  Zwischen zwei Giessungen trocknet der Boden näherungsweise exponentiell gegen den Trockenpunkt
  der Kalibrierung (Index 0):  m(t) = m0 · exp(−k · (t − t0)),  k in 1/Tag.
  k wird je Zyklus per linearer Regression von ln(m) über t bestimmt. Die Prognose nimmt den
  Median der k-Werte der letzten Zyklen (inkl. des laufenden), die Spannweite liefert das Intervall.

Alle Schwellen sind Startwerte (ANNAHME) und am Prototyp zu justieren (PROTOTYP-PRÜFUNG).
"""
from __future__ import annotations

import math

DAY = 86400.0

# Giess-Erkennung (ANNAHME, Kap. 7.2 des Konzepts)
RISE_MIN_PP = 12.0        # Mindestanstieg zwischen zwei Punkten, damit ein Ereignis beginnt
EVENT_MIN_PP = 15.0       # Mindestanstieg des ganzen Ereignisses (Vorher-Wert -> Spitze)
EVENT_MAX_SPAN_S = 12 * 3600   # so lange darf ein Ereignis ansteigen (Wasser verteilt sich)
GAP_MAX_S = 26 * 3600     # grössere Lücke vor dem Anstieg: Zeitpunkt unsicher (Flag)
NOISE_PP = 1.5            # Anstieg kleiner als das gilt als Rauschen und beendet das Ereignis
MERGE_BEFORE_S = 6 * 3600     # Knopf "gegossen" bis 6 h vor dem Sprung gehört dazu
MERGE_AFTER_S = 12 * 3600     # bzw. bis 12 h danach (Sensor misst evtl. erst später)

# Austrocknungsmodell
SETTLE_S = 6 * 3600       # die ersten 6 h nach dem Giessen auslassen (Abtropfen, Verteilen)
FIT_MIN_POINTS = 4
FIT_MIN_SPAN_S = 1.0 * DAY
M_FLOOR = 1.0             # ln(m) nur für m >= 1 %
MAX_CYCLES = 5


def detect_waterings(points, button_times=()):
    """Giessungen aus einem Feuchtesprung erkennen.

    points: [(t, m), ...] chronologisch, nur gültige Werte.
    button_times: Zeitpunkte, an denen der Nutzer "gegossen" gedrückt hat.
    Rückgabe: Liste von dict(t, t_before, before, peak, delta, uncertain_time, button_t)
      t = Zeit des ersten Werts nach dem Anstieg; die Giessung lag zwischen t_before und t.
    """
    ev = []
    i = 1
    n = len(points)
    while i < n:
        t0, m0 = points[i - 1]
        t1, m1 = points[i]
        if m1 - m0 >= RISE_MIN_PP:
            peak_i = i
            j = i + 1
            while j < n and points[j][0] - t1 <= EVENT_MAX_SPAN_S and points[j][1] > points[peak_i][1] + NOISE_PP:
                peak_i = j
                j += 1
            delta = points[peak_i][1] - m0
            if delta >= EVENT_MIN_PP:
                ev.append({"t": int(t1), "t_before": int(t0), "before": m0, "peak": points[peak_i][1],
                           "t_peak": int(points[peak_i][0]), "delta": delta,
                           "uncertain_time": (t1 - t0) > GAP_MAX_S, "button_t": None})
            i = peak_i + 1
            continue
        i += 1
    # Knopfdruck zuordnen (je Knopfdruck höchstens ein Ereignis)
    used = set()
    for e in ev:
        best = None
        for b in button_times:
            if b in used:
                continue
            if e["t_before"] - MERGE_BEFORE_S <= b <= e["t"] + MERGE_AFTER_S:
                if best is None or abs(b - e["t"]) < abs(best - e["t"]):
                    best = b
        if best is not None:
            used.add(best)
            e["button_t"] = best
    return ev


def fit_drying(points):
    """ln(m) = a − k·t (t in Tagen) per Kleinste-Quadrate. Rückgabe dict(k, r2, n, m0, t0) oder None."""
    pts = [(t, m) for t, m in points if m is not None and m >= M_FLOOR]
    if len(pts) < FIT_MIN_POINTS or pts[-1][0] - pts[0][0] < FIT_MIN_SPAN_S:
        return None
    t0 = pts[0][0]
    xs = [(t - t0) / DAY for t, _ in pts]
    ys = [math.log(m) for _, m in pts]
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx <= 0:
        return None
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    a = my - slope * mx
    ss_tot = sum((y - my) ** 2 for y in ys)
    ss_res = sum((y - (a + slope * x)) ** 2 for x, y in zip(xs, ys))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    k = -slope
    if k <= 0:
        return None
    return {"k": k, "r2": r2, "n": n, "m0": math.exp(a), "t0": t0}


def cycles(points, events):
    """Teilt die Punkte in Austrocknungszyklen: von Spitze+SETTLE bis vor die nächste Giessung."""
    out = []
    starts = [e["t_peak"] for e in events]
    bounds = starts + [None]
    for idx, s in enumerate(starts):
        end = bounds[idx + 1]
        seg = [(t, m) for t, m in points if t >= s + SETTLE_S and (end is None or t < events[idx + 1]["t_before"] + 1)]
        out.append({"start": s, "end": end, "points": seg, "current": end is None})
    return out


def forecast(points, events, threshold_pct, now_s, upper_pct=None):
    """Prognose 'nächstes Giessen'. Gibt immer ein dict nach Schema Forecast (openapi.yaml) zurück."""
    base = {"method": "exp", "state": "insufficient_data", "next_water": None, "days": None,
            "days_low": None, "days_high": None, "confidence": None, "k_per_day": None,
            "cycles_used": 0, "r2": None, "explanation": ""}
    if not points:
        base["explanation"] = "Noch keine Messwerte."
        return base
    t_last, m_last = points[-1]
    cyc = cycles(points, events)[-(MAX_CYCLES + 1):]
    fits = []
    for c in cyc:
        f = fit_drying(c["points"])
        if f and f["r2"] >= 0.5:
            fits.append((c, f))
    ks = sorted(f["k"] for _, f in fits)
    if m_last <= threshold_pct:
        base.update(state="due", days=0.0, days_low=0.0, days_high=0.0, confidence="high",
                    next_water=int(t_last), cycles_used=len(fits),
                    k_per_day=_r(_median(ks)) if ks else None,
                    explanation=f"Feuchte {m_last:.0f} % liegt unter der Schwelle {threshold_pct} % – jetzt giessen.")
        return base
    if not ks:
        base["explanation"] = ("Noch zu wenig Verlauf: Die Prognose braucht mindestens einen Austrocknungs-"
                               "abschnitt von einem Tag nach dem Giessen.")
        return base
    k = _median(ks)
    k_lo, k_hi = ks[0], ks[-1]
    if len(ks) >= 3:  # robuste Spannweite: zweitkleinster/zweitgrösster Wert bei vielen Zyklen
        k_lo, k_hi = (ks[1], ks[-2]) if len(ks) >= 5 else (ks[0], ks[-1])
    ratio = math.log(m_last / threshold_pct)
    days_from_last = ratio / k
    elapsed = (now_s - t_last) / DAY
    days = max(0.0, days_from_last - elapsed)
    d_lo = max(0.0, ratio / k_hi - elapsed)
    d_hi = max(0.0, ratio / k_lo - elapsed)
    r2s = [f["r2"] for _, f in fits]
    spread = k_hi / k_lo if k_lo > 0 else 99
    n = len(ks)
    if n >= 3 and spread <= 1.6 and _median(r2s) >= 0.9:
        conf = "high"
    elif n >= 2 and spread <= 2.5:
        conf = "medium"
    else:
        conf = "low"
    loss = (1 - math.exp(-k)) * 100
    base.update(state="ok", days=_r(days), days_low=_r(d_lo), days_high=_r(d_hi), confidence=conf,
                next_water=int(now_s + days * DAY), k_per_day=_r(k, 4), cycles_used=n, r2=_r(_median(r2s), 3),
                explanation=(f"Der Boden verliert zurzeit etwa {loss:.0f} % seines Restwassers pro Tag "
                             f"(Median aus {n} Zyklus{'en' if n != 1 else ''}). Von {m_last:.0f} % bis zur Schwelle "
                             f"{threshold_pct} % dauert das rund {days_from_last:.1f} Tage. Temperatur, Licht und "
                             f"Jahreszeit sind nicht eingerechnet."))
    return base


def forecast_curve(t_last, m_last, fc, threshold_pct, step_s=3 * 3600):
    """Kurve ab dem letzten Wert bis zur Schwelle (mittleres k) mit Band (k_lo/k_hi)."""
    if fc["state"] != "ok" or not fc["k_per_day"]:
        return None
    k = fc["k_per_day"]
    d_hi = fc["days_high"] or fc["days"]
    end = max(fc["next_water"], int(t_last + (d_hi or 0) * DAY)) + step_s
    ts, mid = [], []
    t = t_last
    while t <= end and len(ts) < 400:
        ts.append(int(t))
        mid.append(_r(m_last * math.exp(-k * (t - t_last) / DAY)))
        t += step_s
    return {"t": ts, "moisture": mid, "threshold_pct": threshold_pct}


MOODS = ("happy", "ok", "thirsty", "parched", "drowning", "confused", "sleepy", "unknown")


def mood(state, moisture, threshold_pct, upper_pct, stale, has_sensor, sensor_error, days_left):
    """Stimmung des Tropfen-Charakters (verspieltes Element, immer mit Text daneben)."""
    if not has_sensor:
        return "unknown"
    if sensor_error or state in ("air", "invalid", "uncalibrated"):
        return "confused"
    if stale:
        return "sleepy"
    if state == "flooded" or (upper_pct is not None and moisture is not None and moisture > upper_pct):
        return "drowning"
    if state == "dry":
        return "parched" if moisture is not None and moisture < threshold_pct - 10 else "thirsty"
    if days_left is not None and days_left <= 1.0:
        return "ok"
    return "happy"


def time_in_range(points, lo, hi):
    if not points:
        return None
    inside = sum(1 for _, m in points if lo <= m <= (hi if hi is not None else 1e9))
    return round(100.0 * inside / len(points), 1)


def _median(xs):
    s = sorted(xs)
    n = len(s)
    if not n:
        return None
    return s[n // 2] if n % 2 else 0.5 * (s[n // 2 - 1] + s[n // 2])


def _r(x, nd=2):
    return None if x is None else round(float(x), nd)
