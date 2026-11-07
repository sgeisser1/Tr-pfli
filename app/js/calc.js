// fluidi – Datenaufbereitung und Kalibrierungsrechnung (Referenzimplementierung).
//
// Diese Datei ist rein funktional (kein DOM) und wird von der PWA und von den Unit-Tests
// (node --test) benutzt. Das Gateway (C, ESP-IDF) und der Mock-Server (app/dev/fluidi_calc.py)
// implementieren dieselben Formeln; alle drei werden gegen app/tests/vectors/calc_vectors.json
// geprüft. Formeln und Grenzen: docs/interfaces/GATEWAY_API.md Kap. 7.

/** Grenzen der Plausibilitätserkennung (REQ-MES-12), in %-Punkten ausserhalb 0..100. */
export const AIR_MARGIN_PP = 10;
export const FLOOD_MARGIN_PP = 10;
/** Mindestspanne zwischen Trocken- und Nasspunkt, relativ zum grösseren Betrag. */
export const MIN_SPAN_REL = 0.02;
/** Referenztemperatur der Temperaturkompensation (Platzhalter, PROTOTYP-PRÜFUNG REQ-MES-05). */
export const T_REF_C = 20.0;

/** Runden auf eine Nachkommastelle, kaufmännisch (halb weg von null), identisch in Python. */
export function round1(x) {
  if (x === null || x === undefined || !Number.isFinite(x)) return null;
  const s = x < 0 ? -1 : 1;
  return (s * Math.floor(Math.abs(x) * 10 + 0.5)) / 10;
}

/**
 * Temperaturkompensation des Rohwerts (PLATZHALTER).
 * Modell: raw(T) = raw(T_ref) * (1 + k * (T - T_ref)) mit relativem Koeffizienten k [1/K].
 * Werkseinstellung k = 0 (keine Kompensation), bis der Prototyp-Versuch nach REQ-MES-05
 * einen Wert liefert. Fehlt die Temperatur, bleibt der Rohwert unverändert.
 */
export function compensateRaw(raw, tempC, coeffPerK = 0, tRefC = T_REF_C) {
  if (!Number.isFinite(raw)) return null;
  if (!coeffPerK || tempC === null || tempC === undefined || !Number.isFinite(tempC)) return raw;
  const f = 1 + coeffPerK * (tempC - tRefC);
  if (f <= 0.5 || f >= 1.5) return raw; // unplausibler Koeffizient: nicht kompensieren
  return raw / f;
}

/** true, wenn Trocken- und Nasspunkt genügend weit auseinanderliegen. */
export function spanOk(dryRaw, wetRaw) {
  if (!Number.isFinite(dryRaw) || !Number.isFinite(wetRaw)) return false;
  const ref = Math.max(Math.abs(dryRaw), Math.abs(wetRaw));
  if (ref === 0) return false;
  return Math.abs(wetRaw - dryRaw) / ref >= MIN_SPAN_REL;
}

/**
 * Feuchteindex (unbegrenzt) aus kompensiertem Rohwert und Zwei-Punkt-Kalibrierung.
 * 0 % = Trockenpunkt, 100 % = Nasspunkt; Richtung des Rohwerts (steigend oder fallend) egal.
 * Gibt null zurück, wenn die Kalibrierung ungültig ist.
 */
export function moistureIndex(rawComp, dryRaw, wetRaw) {
  if (!Number.isFinite(rawComp) || !spanOk(dryRaw, wetRaw)) return null;
  return ((rawComp - dryRaw) / (wetRaw - dryRaw)) * 100;
}

/**
 * Zustand eines Messwerts.
 * air = deutlich unter dem Trockenpunkt (Sensor in Luft), flooded = deutlich über dem Nasspunkt,
 * dry = unter der Giessschwelle, ok sonst, invalid = nicht berechenbar.
 */
export function classify(indexUnclamped, thresholdPct) {
  if (indexUnclamped === null || !Number.isFinite(indexUnclamped)) return 'invalid';
  if (indexUnclamped < -AIR_MARGIN_PP) return 'air';
  if (indexUnclamped > 100 + FLOOD_MARGIN_PP) return 'flooded';
  if (Number.isFinite(thresholdPct) && indexUnclamped < thresholdPct) return 'dry';
  return 'ok';
}

/**
 * Vollständige Aufbereitung eines Rohmesswerts.
 * cal = { dry: {raw}, wet: {raw}, temp_coeff_per_k, t_ref_c }
 * Ergebnis: { moisture_pct (0..100, 0.1 % Auflösung, null bei air/flooded/invalid),
 *             moisture_unclamped (0.1 %), moisture_state }
 */
export function evaluate(raw, tempC, cal, thresholdPct) {
  if (!cal || !cal.dry || !cal.wet) {
    return { moisture_pct: null, moisture_unclamped: null, moisture_state: 'uncalibrated' };
  }
  const k = cal.temp_coeff_per_k || 0;
  const tRef = Number.isFinite(cal.t_ref_c) ? cal.t_ref_c : T_REF_C;
  const comp = compensateRaw(raw, tempC, k, tRef);
  const idx = moistureIndex(comp, cal.dry.raw, cal.wet.raw);
  const state = classify(idx, thresholdPct);
  let pct = null;
  if (state === 'ok' || state === 'dry') pct = round1(Math.min(100, Math.max(0, idx)));
  return { moisture_pct: pct, moisture_unclamped: round1(idx), moisture_state: state };
}

/**
 * Mittelwert mehrerer Einzelmessungen mit Ausreissererkennung (REQ-MES-10).
 * Ausreisser: |x - Median| > 3.5 * 1.4826 * MAD (robuster z-Wert). Bei MAD = 0 nur exakte Werte.
 * Ergebnis: { mean, stddev (Stichprobe, null bei n<2), n, outliers }
 */
export function robustMean(samples) {
  const xs = (samples || []).filter((x) => Number.isFinite(x));
  if (xs.length === 0) return { mean: null, stddev: null, n: 0, outliers: 0 };
  const med = median(xs);
  const mad = median(xs.map((x) => Math.abs(x - med)));
  const lim = 3.5 * 1.4826 * mad;
  const kept = mad === 0 ? xs.filter((x) => x === med || xs.length < 3) : xs.filter((x) => Math.abs(x - med) <= lim);
  const use = kept.length ? kept : xs;
  const mean = use.reduce((a, b) => a + b, 0) / use.length;
  let sd = null;
  if (use.length >= 2) {
    sd = Math.sqrt(use.reduce((a, b) => a + (b - mean) ** 2, 0) / (use.length - 1));
  }
  return { mean, stddev: sd, n: use.length, outliers: xs.length - use.length };
}

export function median(xs) {
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/** Signalqualität 0..4 aus RSSI am Gateway (Schwellen ANNAHME, am Prototyp justieren). */
export const SIGNAL_LEVELS = [-70, -80, -88, -95];
export function signalQuality(rssiDbm) {
  if (!Number.isFinite(rssiDbm)) return 0;
  let q = 4;
  for (const lim of SIGNAL_LEVELS) {
    if (rssiDbm >= lim) return q;
    q -= 1;
  }
  return 0;
}

/** Batterie-Balken 0..4 für die Anzeige. */
export function batteryBars(pct) {
  if (!Number.isFinite(pct)) return 0;
  if (pct >= 75) return 4;
  if (pct >= 50) return 3;
  if (pct >= 25) return 2;
  if (pct >= 10) return 1;
  return 0;
}

/**
 * Auflösung für eine Zeitreihe wählen: die feinste Stufe mit höchstens maxPoints Punkten.
 * perDay = Messungen pro Tag (inkl. Reserve für manuelle Messungen).
 */
export function chooseResolution(fromS, toS, perDay, maxPoints = 800) {
  const days = Math.max(0, toS - fromS) / 86400;
  if (days * perDay <= maxPoints) return 'raw';
  if (days * 24 <= maxPoints) return 'hour';
  return 'day';
}

/** Ein Wert gilt als veraltet, wenn länger als 3 Messintervalle nichts kam (min. 2 h). */
export function isStale(lastS, nowS, perDay) {
  if (!Number.isFinite(lastS)) return true;
  const interval = 86400 / Math.max(1, perDay);
  return nowS - lastS > Math.max(3 * interval, 7200);
}

/** Relative Zeit auf Deutsch, z. B. „vor 5 min“. */
export function relativeTime(tS, nowS) {
  if (!Number.isFinite(tS)) return '–';
  const d = Math.round(nowS - tS);
  if (d < 0) return 'gerade eben';
  if (d < 60) return 'gerade eben';
  if (d < 3600) return `vor ${Math.floor(d / 60)} min`;
  if (d < 86400) return `vor ${Math.floor(d / 3600)} h`;
  const days = Math.floor(d / 86400);
  return days === 1 ? 'vor 1 Tag' : `vor ${days} Tagen`;
}

/** LED-/Zustandsfarbe für das Tropfensymbol (D-010). */
export function dropColor(plant) {
  if (!plant || !plant.latest) return 'off';
  const s = plant.status || {};
  if (s.sensor_error || plant.latest.moisture_state === 'air' || plant.latest.moisture_state === 'flooded') return 'red';
  if (s.battery_low && plant.battery && plant.battery.state === 'critical') return 'red';
  if (s.needs_water) return 'blue';
  if (s.stale) return 'off';
  return 'green';
}
