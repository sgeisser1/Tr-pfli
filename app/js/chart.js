// fluidi – eigene SVG-Diagramme (ohne Bibliothek, Farben aus dem Entwurf).
import { s } from './dom.js';

const DAY = 86400;

/** Feuchteverlauf: Zielbereich, Giessschwelle, Linie/Fläche, Min/Max-Band, Giessungen, Prognose. */
export function moistureChart({ series, forecast, lo, hi, from, to, width, height = 220, compact = false }) {
  const W = Math.max(260, Math.round(width));
  const H = height;
  const pad = { l: compact ? 6 : 34, r: 10, t: 14, b: compact ? 6 : 24 };
  const fcEnd = forecast && forecast.curve ? Math.max(...forecast.curve.t) : null;
  const t1 = fcEnd ? Math.max(to, Math.min(fcEnd, to + (to - from))) : to;
  const X = (t) => pad.l + ((t - from) / (t1 - from)) * (W - pad.l - pad.r);
  const Y = (v) => pad.t + (1 - v / 100) * (H - pad.t - pad.b);
  const svg = s('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, class: 'chart', role: 'img', 'aria-label': 'Feuchteverlauf' });
  // Gitter + Achsen
  const grid = s('g', { class: 'ch-grid' });
  for (const v of [0, 25, 50, 75, 100]) {
    grid.append(s('line', { x1: pad.l, x2: W - pad.r, y1: Y(v), y2: Y(v) }));
    if (!compact && v % 50 === 0) grid.append(s('text', { x: pad.l - 6, y: Y(v) + 4, class: 'ch-ylab', 'text-anchor': 'end' }, `${v} %`));
  }
  svg.append(grid);
  // Zielbereich und Schwelle
  if (hi != null) svg.append(s('rect', { x: pad.l, y: Y(hi), width: W - pad.l - pad.r, height: Y(lo) - Y(hi), class: 'ch-band' }));
  // x-Beschriftung
  if (!compact) {
    const span = t1 - from;
    const xl = s('g', { class: 'ch-xlab' });
    const ticks = [];
    const tz = (t) => new Date(t * 1000);
    if (span <= 1.6 * DAY) {
      for (let t = Math.ceil(from / 21600) * 21600; t <= t1; t += 21600) ticks.push([t, tz(t).toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' })]);
    } else if (span <= 16 * DAY) {
      const d0 = new Date(from * 1000); d0.setHours(24, 0, 0, 0);
      const step = span > 9 * DAY && W < 700 ? 2 : 1;
      for (let t = d0 / 1000; t <= t1; t += step * DAY) ticks.push([t, tz(t).toLocaleDateString('de-CH', span > 9 * DAY ? { weekday: 'short', day: 'numeric' } : { weekday: 'short' })]);
    } else if (span <= 70 * DAY) {
      const d0 = new Date(from * 1000); d0.setHours(24, 0, 0, 0);
      for (let t = d0 / 1000; t <= t1; t += 7 * DAY) ticks.push([t, tz(t).toLocaleDateString('de-CH', { day: 'numeric', month: 'numeric' })]);
    } else {
      const d = new Date(from * 1000); d.setDate(1); d.setHours(0, 0, 0, 0); d.setMonth(d.getMonth() + 1);
      for (; d / 1000 <= t1; d.setMonth(d.getMonth() + (span > 200 * DAY ? 2 : 1))) ticks.push([d / 1000, d.toLocaleDateString('de-CH', { month: 'short' })]);
    }
    for (const [t, lab] of ticks) xl.append(s('text', { x: X(t), y: H - 6, 'text-anchor': 'middle' }, lab));
    svg.append(xl);
  }
  // Min/Max-Band (aggregiert)
  const t = series.t;
  const m = series.moisture;
  if (series.moisture_min) {
    let d = '';
    let seg = [];
    const flush = () => {
      if (seg.length > 1) {
        d += 'M' + seg.map((i) => `${X(t[i]).toFixed(1)} ${Y(series.moisture_max[i]).toFixed(1)}`).join(' L');
        d += ' L' + seg.slice().reverse().map((i) => `${X(t[i]).toFixed(1)} ${Y(series.moisture_min[i]).toFixed(1)}`).join(' L') + 'Z ';
      }
      seg = [];
    };
    t.forEach((_, i) => (m[i] == null ? flush() : seg.push(i)));
    flush();
    svg.append(s('path', { d, class: 'ch-minmax' }));
  }
  // Fläche + Linie mit Lücken
  let line = '';
  let area = '';
  let run = [];
  const flush = () => {
    if (run.length) {
      const pts = run.map((i) => `${X(t[i]).toFixed(1)} ${Y(m[i]).toFixed(1)}`);
      line += 'M' + pts.join(' L') + ' ';
      area += `M${X(t[run[0]]).toFixed(1)} ${Y(0)} L` + pts.join(' L') + ` L${X(t[run[run.length - 1]]).toFixed(1)} ${Y(0)}Z `;
    }
    run = [];
  };
  t.forEach((_, i) => (m[i] == null ? flush() : run.push(i)));
  flush();
  const gid = 'cg' + Math.random().toString(36).slice(2, 7);
  svg.append(s('defs', null, s('linearGradient', { id: gid, x1: 0, y1: 0, x2: 0, y2: 1 }, s('stop', { offset: 0, class: 'ch-ga' }), s('stop', { offset: 1, class: 'ch-gb' }))));
  svg.append(s('path', { d: area, class: 'ch-area', fill: `url(#${gid})` }), s('path', { d: line, class: 'ch-line' }));
  svg.append(s('line', { x1: pad.l, x2: W - pad.r, y1: Y(lo), y2: Y(lo), class: 'ch-thr' }));
  if (!compact) svg.append(s('text', { x: pad.l + 4, y: Y(lo) + 14, class: 'ch-thrlab', 'text-anchor': 'start' }, `giessen unter ${lo} %`));
  // Giessungen
  for (const e of series.events || []) {
    if (e.type !== 'watering' || e.t < from) continue;
    const x = X(e.t);
    svg.append(s('g', { class: 'ch-water' }, s('line', { x1: x, x2: x, y1: pad.t, y2: H - pad.b }),
      s('path', { d: `M${x} ${pad.t - 1} l-3.6 7.6 a4 4 0 1 0 7.2 0Z` })));
  }
  // Prognose
  if (forecast && forecast.curve && forecast.state === 'ok') {
    const c = forecast.curve;
    const d = 'M' + c.t.map((tt, i) => `${X(tt).toFixed(1)} ${Y(c.moisture[i]).toFixed(1)}`).join(' L');
    const tl = Date.parse(forecast.next_water) / 1000;
    const tLo = tl - (forecast.days - forecast.days_low) * DAY;
    const tHi = tl + (forecast.days_high - forecast.days) * DAY;
    const xa = X(Math.min(tLo, t1));
    svg.append(s('rect', { x: xa, y: pad.t, width: Math.max(2, Math.min(X(tHi), W - pad.r) - xa), height: H - pad.t - pad.b, class: 'ch-fcband' }));
    const cid = gid + 'c';
    svg.append(s('clipPath', { id: cid }, s('rect', { x: pad.l, y: 0, width: W - pad.l - pad.r, height: H })));
    svg.append(s('path', { d, class: 'ch-fc', 'clip-path': `url(#${cid})` }));
    if (tl <= t1) svg.append(s('circle', { cx: X(tl), cy: Y(lo), r: 4.5, class: 'ch-fcdot' }));
  }
  const nx = X(Math.min(Date.now() / 1000, to));
  svg.append(s('line', { x1: nx, x2: nx, y1: pad.t, y2: H - pad.b, class: 'ch-now' }));
  return svg;
}

/** Säulen (z. B. Giessungen pro Woche). */
export function bars(values, labels, { width, height = 140 }) {
  const W = Math.max(240, Math.round(width));
  const H = height;
  const max = Math.max(1, ...values);
  const bw = (W - 8) / values.length;
  const svg = s('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, class: 'chart bars', role: 'img', 'aria-label': 'Säulendiagramm' });
  values.forEach((v, i) => {
    const h = (v / max) * (H - 36);
    const x = 4 + i * bw + bw * 0.18;
    svg.append(s('rect', { x, y: H - 20 - h, width: bw * 0.64, height: Math.max(1, h), rx: Math.min(8, bw * 0.2), class: i === values.length - 1 ? 'bar now' : 'bar' }));
    svg.append(s('text', { x: x + bw * 0.32, y: H - 24 - h, 'text-anchor': 'middle', class: 'bar-val' }, String(v)));
    if (labels[i]) svg.append(s('text', { x: x + bw * 0.32, y: H - 5, 'text-anchor': 'middle', class: 'bar-lab' }, labels[i]));
  });
  return svg;
}

/** Kleine Linie (z. B. Batteriespannung). */
export function spark(vals, { width = 120, height = 32, min, max } = {}) {
  const lo = min ?? Math.min(...vals);
  const hi = max ?? Math.max(...vals);
  const W = width;
  const H = height;
  const d = vals.map((v, i) => `${i ? 'L' : 'M'}${((i / Math.max(1, vals.length - 1)) * (W - 4) + 2).toFixed(1)} ${(H - 3 - ((v - lo) / Math.max(1, hi - lo)) * (H - 6)).toFixed(1)}`).join(' ');
  return s('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, class: 'spark', 'aria-hidden': 'true' }, s('path', { d }));
}

/** Raumklima: Temperatur (Linie, linke Achse) und relative Feuchte (Fläche, rechte Achse). */
export function climateChart(cl, { width, height = 170 }) {
  const W = Math.max(260, Math.round(width));
  const H = height;
  const pad = { l: 34, r: 34, t: 10, b: 22 };
  const t = cl.t;
  const t0 = t[0];
  const t1 = t[t.length - 1] || t0 + 1;
  const tmin = Math.floor(Math.min(...cl.temp_c) - 1);
  const tmax = Math.ceil(Math.max(...cl.temp_c) + 1);
  const X = (x) => pad.l + ((x - t0) / Math.max(1, t1 - t0)) * (W - pad.l - pad.r);
  const YT = (v) => pad.t + (1 - (v - tmin) / Math.max(1, tmax - tmin)) * (H - pad.t - pad.b);
  const YR = (v) => pad.t + (1 - v / 100) * (H - pad.t - pad.b);
  const svg = s('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, class: 'chart climate', role: 'img', 'aria-label': 'Raumklima: Temperatur und Luftfeuchte' });
  const g = s('g', { class: 'ch-grid' });
  for (const v of [0, 50, 100]) g.append(s('line', { x1: pad.l, x2: W - pad.r, y1: YR(v), y2: YR(v) }), s('text', { x: W - pad.r + 4, y: YR(v) + 4, class: 'ch-ylab' }, `${v} %`));
  for (const v of [tmin, tmax]) g.append(s('text', { x: pad.l - 6, y: YT(v) + 4, class: 'ch-ylab', 'text-anchor': 'end' }, `${v}°`));
  svg.append(g);
  const area = 'M' + t.map((x, i) => `${X(x).toFixed(1)} ${YR(cl.rh_pct[i]).toFixed(1)}`).join(' L') + ` L${X(t1).toFixed(1)} ${YR(0)} L${X(t0).toFixed(1)} ${YR(0)}Z`;
  svg.append(s('path', { d: area, class: 'ch-rh' }));
  svg.append(s('path', { d: 'M' + t.map((x, i) => `${X(x).toFixed(1)} ${YT(cl.temp_c[i]).toFixed(1)}`).join(' L'), class: 'ch-temp' }));
  const xl = s('g', { class: 'ch-xlab' });
  const d0 = new Date(t0 * 1000); d0.setHours(24, 0, 0, 0);
  for (let x = d0 / 1000; x <= t1; x += 86400) xl.append(s('text', { x: X(x), y: H - 6, 'text-anchor': 'middle' }, new Date(x * 1000).toLocaleDateString('de-CH', { weekday: 'short' })));
  svg.append(xl);
  return svg;
}
