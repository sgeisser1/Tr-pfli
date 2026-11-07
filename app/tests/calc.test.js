// Unit-Tests der Datenaufbereitung (node --test, Node >= 18, keine Abhängigkeiten).
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import * as calc from '../js/calc.js';

const V = JSON.parse(readFileSync(new URL('./vectors/calc_vectors.json', import.meta.url), 'utf8'));
const near = (a, b, eps = 1e-6) => (a === null || b === null ? a === b : Math.abs(a - b) < eps);

test('round1: halb weg von null', () => {
  for (const v of V.round1) assert.equal(calc.round1(v.x), v.y, `round1(${v.x})`);
  assert.equal(calc.round1(NaN), null);
});

test('evaluate: Feuchteindex, Plausibilität, Kompensation (Vektoren)', () => {
  for (const v of V.evaluate) {
    const r = calc.evaluate(v.raw, v.temp_c, v.cal, v.threshold);
    assert.equal(r.moisture_state, v.state, v._c);
    assert.equal(r.moisture_pct, v.pct, v._c);
    assert.equal(r.moisture_unclamped, v.unclamped, v._c);
  }
});

test('moistureIndex ist linear zwischen den Kalibrierpunkten', () => {
  for (let i = 0; i <= 10; i++) {
    const raw = 41000 + (26000 - 41000) * (i / 10);
    assert.ok(near(calc.moistureIndex(raw, 41000, 26000), i * 10, 1e-9));
  }
});

test('compensateRaw: k=0 ist Identität, Umkehrung des Modells', () => {
  assert.equal(calc.compensateRaw(12345, 35, 0), 12345);
  const k = 0.003, t = 28, ref = 20, rawRef = 30000;
  const measured = rawRef * (1 + k * (t - ref));
  assert.ok(near(calc.compensateRaw(measured, t, k, ref), rawRef, 1e-6));
});

test('Auflösung 0.1 % genügt REQ-MES-03 (≤ 1 %)', () => {
  const a = calc.evaluate(33500, 20, { dry: { raw: 41000 }, wet: { raw: 26000 } }, 0).moisture_pct;
  const b = calc.evaluate(33485, 20, { dry: { raw: 41000 }, wet: { raw: 26000 } }, 0).moisture_pct;
  assert.ok(Math.abs(b - a - 0.1) < 1e-9);
});

test('robustMean mit Ausreissererkennung (REQ-MES-10)', () => {
  for (const v of V.robust_mean) {
    const r = calc.robustMean(v.x);
    assert.ok(near(r.mean, v.mean), `mean ${v.x}`);
    assert.ok(near(r.stddev, v.stddev), `sd ${v.x}`);
    assert.equal(r.n, v.n);
    assert.equal(r.outliers, v.outliers);
  }
});

test('signalQuality / batteryBars', () => {
  for (const v of V.signal_quality) assert.equal(calc.signalQuality(v.rssi), v.q, `rssi ${v.rssi}`);
  for (const v of V.battery_bars) assert.equal(calc.batteryBars(v.pct), v.bars, `pct ${v.pct}`);
});

test('chooseResolution', () => {
  for (const v of V.choose_resolution) {
    assert.equal(calc.chooseResolution(0, v.days * 86400, v.per_day), v.res, JSON.stringify(v));
  }
});

test('isStale', () => {
  const now = 1_800_000_000;
  for (const v of V.is_stale) assert.equal(calc.isStale(now - v.age_s, now, v.per_day), v.stale, JSON.stringify(v));
  assert.equal(calc.isStale(undefined, now, 6), true);
});

test('relativeTime auf Deutsch', () => {
  const now = 1_800_000_000;
  assert.equal(calc.relativeTime(now - 10, now), 'gerade eben');
  assert.equal(calc.relativeTime(now - 300, now), 'vor 5 min');
  assert.equal(calc.relativeTime(now - 7200, now), 'vor 2 h');
  assert.equal(calc.relativeTime(now - 86400, now), 'vor 1 Tag');
  assert.equal(calc.relativeTime(now - 3 * 86400, now), 'vor 3 Tagen');
});

test('dropColor folgt den LED-Farben (D-010)', () => {
  const base = { latest: { moisture_state: 'ok' }, status: { needs_water: false, stale: false, battery_low: false, sensor_error: null } };
  assert.equal(calc.dropColor(base), 'green');
  assert.equal(calc.dropColor({ ...base, status: { ...base.status, needs_water: true } }), 'blue');
  assert.equal(calc.dropColor({ ...base, latest: { moisture_state: 'air' } }), 'red');
  assert.equal(calc.dropColor({ ...base, latest: null }), 'off');
});
