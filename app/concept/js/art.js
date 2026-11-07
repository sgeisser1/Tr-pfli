// fluidi Entwürfe – eigene SVG-Grafiken: Symbole, Tropfen-Charakter (Ampel + Stimmung), Pflanzen.
// Alles selbst gezeichnet (keine fremden Assets). Farben kommen aus CSS-Variablen des Entwurfs.
import { s, nextId } from './dom.js';

// ------------------------------------------------------------------ Symbole (24 × 24, Linie)
const I = {
  plants: 'M7 14h10l-1.2 6.2a1 1 0 0 1-1 .8H9.2a1 1 0 0 1-1-.8L7 14Z M12 14V9 M12 10c0-3 2-5 5-5 0 3-2 5-5 5Z M12 12c0-2.5-1.7-4.2-4.5-4.2 0 2.5 1.8 4.2 4.5 4.2Z',
  room: 'M4 4h16v16H4z M4 13h6 M14 4v6 M14 14h6 M14 14v6',
  stats: 'M5 20v-8 M10 20V5 M15 20v-6 M20 20V9',
  settings: 'M4 7h9 M17 7h3 M15 5v4 M4 17h3 M11 17h9 M9 15v4',
  tv: 'M3 5h18v11H3z M8 20h8 M12 16v4',
  drop: 'M12 2.6 7.3 12.4A5.4 5.4 0 1 0 16.7 12.4Z',
  plus: 'M12 5v14 M5 12h14',
  back: 'M15 5l-7 7 7 7',
  chev: 'M9 6l6 6-6 6',
  check: 'M5 12.5l4.5 4.5L19 7.5',
  x: 'M6 6l12 12 M18 6 6 18',
  clock: 'M12 3.5a8.5 8.5 0 1 1 0 17 8.5 8.5 0 0 1 0-17Z M12 7.5V12l3 2',
  thermo: 'M10 14.5V5a2 2 0 1 1 4 0v9.5a4 4 0 1 1-4 0Z M12 10v6',
  sun: 'M12 8a4 4 0 1 1 0 8 4 4 0 0 1 0-8Z M12 2.5v2 M12 19.5v2 M2.5 12h2 M19.5 12h2 M5.3 5.3l1.4 1.4 M17.3 17.3l1.4 1.4 M5.3 18.7l1.4-1.4 M17.3 6.7l1.4-1.4',
  moon: 'M19.5 14.5A8 8 0 1 1 9.5 4.5a6.3 6.3 0 0 0 10 10Z',
  auto: 'M12 3.5a8.5 8.5 0 1 1 0 17Z M12 3.5a8.5 8.5 0 1 0 0 17',
  bell: 'M6 16v-5a6 6 0 1 1 12 0v5l1.5 2h-15L6 16Z M10 20.5a2 2 0 0 0 4 0',
  edit: 'M4 20h4L19 9l-4-4L4 16v4Z M13.5 6.5l4 4',
  download: 'M12 4v11 M7 10l5 5 5-5 M5 20h14',
  pulse: 'M3 12h4l2-5 4 10 2-5h6',
  target: 'M12 4a8 8 0 1 1 0 16 8 8 0 0 1 0-16Z M12 9a3 3 0 1 1 0 6 3 3 0 0 1 0-6Z M12 2v3 M12 19v3 M2 12h3 M19 12h3',
  window: 'M4 5h16v14H4z M12 5v14 M4 12h16',
  door: 'M6 20V4h12v16 M3 20h18 M14.5 12h.5',
  sprout: 'M12 20v-8 M12 12c-4 0-6-3-6-7 4 0 6 3 6 7Z M12 14c3 0 5-2 5-5-3 0-5 2-5 5Z',
  pot: 'M6 10h12l-1.5 9.2a1 1 0 0 1-1 .8h-7a1 1 0 0 1-1-.8L6 10Z M4.5 7h15v3h-15z',
  note: 'M6 3.5h9l3 3V20.5H6z M9 11h6 M9 15h6',
  move: 'M12 3v18 M3 12h18 M9 6l3-3 3 3 M9 18l3 3 3-3 M6 9l-3 3 3 3 M18 9l3 3-3 3',
  trash: 'M5 7h14 M9.5 7V4.5h5V7 M7 7l1 13h8l1-13',
  info: 'M12 3.5a8.5 8.5 0 1 1 0 17 8.5 8.5 0 0 1 0-17Z M12 11v5.5 M12 7.6v.4',
  alert: 'M12 4 2.8 19.5h18.4L12 4Z M12 10v4.5 M12 17v.4',
  link: 'M14 4h6v6 M20 4l-9 9 M18 14v6H4V6h6',
  leaf: 'M5 19c0-8 5-14 14-14 0 9-6 14-14 14Z M5 19l8-8',
  battery: 'M3 8h15v8H3z M20 10.5v3',
  wifi: 'M4 18h.01 M4 13a7 7 0 0 1 7 7 M4 8a12 12 0 0 1 12 12',
  calendar: 'M4 6h16v14H4z M4 10h16 M8 3.5v4 M16 3.5v4',
  sparkle: 'M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8Z',
  hand: 'M8 12V5.5a1.5 1.5 0 0 1 3 0V11 M11 10.5V4a1.5 1.5 0 0 1 3 0v6.5 M14 10.5V6a1.5 1.5 0 0 1 3 0v8a6 6 0 0 1-6 6 6 6 0 0 1-5.2-3L4 13.5a1.5 1.5 0 0 1 2.5-1.5L8 14',
};

export function icon(name, cls = '') {
  return s('svg', { viewBox: '0 0 24 24', class: `ic ${cls}`, 'aria-hidden': 'true' }, s('path', { d: I[name] || I.info }));
}

export function batteryIcon(pct, warn) {
  const w = Math.max(0, Math.min(1, (pct || 0) / 100)) * 12;
  return s('svg', { viewBox: '0 0 24 24', class: `ic batt${warn ? ' warn' : ''}`, 'aria-hidden': 'true' },
    s('path', { d: I.battery }), s('rect', { x: 4.5, y: 9.5, width: w.toFixed(1), height: 5, class: 'fillc' }));
}

export function signalIcon(q) {
  const g = s('svg', { viewBox: '0 0 24 24', class: `ic sig${q <= 1 ? ' warn' : ''}`, 'aria-hidden': 'true' });
  for (let i = 0; i < 4; i++) g.append(s('rect', { x: 3 + i * 5, y: 17 - i * 4, width: 3, height: 3 + i * 4, rx: 0.8, class: i < q ? 'fillc' : 'emptyc' }));
  return g;
}

// ------------------------------------------------------------------ Tropfen-Charakter
// Geometrie wie LED-Fenster und i-Punkte (Spitze 2.4 r über der Mitte, D-010/D-011).
const DROP = 'M50 1.6 L82.7 73 A36 36 0 1 1 17.3 73 Z';
export const STATE_CLASS = { ok: 'st-ok', dry: 'st-dry', air: 'st-alert', flooded: 'st-alert', invalid: 'st-alert', uncalibrated: 'st-off', stale: 'st-off', none: 'st-off' };
export const MOOD_TEXT = {
  happy: 'zufrieden', ok: 'bald durstig', thirsty: 'durstig', parched: 'sehr durstig', drowning: 'zu nass',
  confused: 'verwirrt – Sensor prüfen', sleepy: 'schläft – keine neuen Werte', unknown: 'ohne Sensor',
};

/** Tropfen mit Füllstand (= Feuchte), Farbe (= Ampel, LED-Farben D-010) und Gesicht (= Stimmung). */
export function dropChar(mood = 'ok', { pct = null, state = 'ok', size = 64, label, animate = true } = {}) {
  const id = nextId('dc');
  const cls = STATE_CLASS[state] || 'st-off';
  const svg = s('svg', { viewBox: '0 0 100 128', width: size, height: Math.round(size * 1.28), class: `dropchar ${cls} mood-${mood}${animate ? ' anim' : ''}`, role: 'img', 'aria-label': label || `Tropfen: ${MOOD_TEXT[mood] || mood}` });
  const lvl = pct == null ? 0 : Math.max(0, Math.min(100, pct));
  const yFill = 124 - (lvl / 100) * 112;
  svg.append(
    s('defs', null,
      s('clipPath', { id }, s('path', { d: DROP })),
      s('radialGradient', { id: id + 'g', cx: '35%', cy: '55%', r: '70%' }, s('stop', { offset: '0', class: 'dc-s1' }), s('stop', { offset: '1', class: 'dc-s2' }))),
    s('path', { d: DROP, class: 'dc-glow' }),
    s('path', { d: DROP, class: 'dc-body' }),
    s('g', { 'clip-path': `url(#${id})` },
      s('path', { class: 'dc-fill', fill: `url(#${id}g)`, d: `M-10 ${yFill} Q 15 ${yFill - 5} 40 ${yFill} T 90 ${yFill} T 140 ${yFill} V 140 H -10 Z` })),
    s('path', { d: DROP, class: 'dc-line' }),
    s('ellipse', { cx: 33, cy: 62, rx: 6, ry: 11, class: 'dc-shine', transform: 'rotate(22 33 62)' }),
    face(mood),
  );
  return svg;
}

function face(m) {
  const g = s('g', { class: 'dc-face' });
  const eye = (x, r = 5) => [s('circle', { cx: x, cy: 82, r, class: 'f-eye' }), s('circle', { cx: x + 1.6, cy: 80.4, r: r * 0.32, class: 'f-hi' })];
  const arc = (x, up) => s('path', { d: up ? `M${x - 6} 85 Q${x} 76 ${x + 6} 85` : `M${x - 6} 81 Q${x} 88 ${x + 6} 81`, class: 'f-line' });
  const mouth = (d, fill) => s('path', { d, class: fill ? 'f-mouth' : 'f-line' });
  const eyesG = s('g', { class: 'f-eyes' });
  switch (m) {
    case 'happy':
      eyesG.append(arc(38, true), arc(62, true));
      g.append(eyesG, s('ellipse', { cx: 28, cy: 94, rx: 5, ry: 3, class: 'f-cheek' }), s('ellipse', { cx: 72, cy: 94, rx: 5, ry: 3, class: 'f-cheek' }),
        mouth('M40 96 Q50 109 60 96 Z', true));
      break;
    case 'ok':
      eyesG.append(...eye(38), ...eye(62));
      g.append(eyesG, mouth('M42 99 Q50 105 58 99'));
      break;
    case 'thirsty':
      eyesG.append(...eye(38), ...eye(62));
      g.append(eyesG, s('path', { d: 'M31 73 L44 75 M56 75 L69 73', class: 'f-line' }), s('ellipse', { cx: 50, cy: 101, rx: 4.5, ry: 5.5, class: 'f-mouth' }),
        s('path', { d: 'M80 52 L76.5 60 A4 4 0 1 0 83.5 60 Z', class: 'f-sweat' }));
      break;
    case 'parched':
      eyesG.append(s('path', { d: 'M32 83 L44 81 M56 81 L68 83', class: 'f-line' }));
      g.append(eyesG, mouth('M38 102 Q44 97 50 102 Q56 107 62 102'), s('path', { d: 'M54 106 Q56 113 52 114', class: 'f-tongue' }));
      break;
    case 'drowning':
      eyesG.append(s('circle', { cx: 38, cy: 81, r: 7, class: 'f-white' }), s('circle', { cx: 62, cy: 81, r: 7, class: 'f-white' }),
        s('circle', { cx: 38, cy: 82, r: 3, class: 'f-eye' }), s('circle', { cx: 62, cy: 82, r: 3, class: 'f-eye' }));
      g.append(eyesG, mouth('M39 102 Q44.5 98 50 102 Q55.5 106 61 102'), s('circle', { cx: 78, cy: 48, r: 4, class: 'f-bubble' }), s('circle', { cx: 86, cy: 38, r: 2.6, class: 'f-bubble' }));
      break;
    case 'confused':
      eyesG.append(...eye(38, 5.5), ...eye(62, 3.6));
      g.append(eyesG, s('path', { d: 'M31 72 L45 74 M56 75 Q62 71 69 74', class: 'f-line' }), mouth('M41 102 L45.5 99 L50 103 L54.5 99 L59 102'),
        s('path', { d: 'M74 30 Q74 24 79 24 Q84 24 84 29 Q84 33 79 35 V38 M79 42 V42.5', class: 'f-q' }));
      break;
    case 'sleepy':
      eyesG.append(arc(38, false), arc(62, false));
      g.append(eyesG, s('circle', { cx: 50, cy: 101, r: 3, class: 'f-mouth' }), s('path', { d: 'M70 30 H78 L70 38 H78 M82 18 H88 L82 24 H88', class: 'f-z' }));
      break;
    default:
      eyesG.append(...eye(38, 4), ...eye(62, 4));
      g.append(eyesG, mouth('M43 101 H57'));
  }
  return g;
}

// ------------------------------------------------------------------ Pflanzen-Illustrationen
// viewBox 0 0 120 150, Erde bei (60,104). Klassen: pl-leaf/-leaf2/-leaf3, pl-vein, pl-stem, pl-acc/-acc2, pl-pot…
const P = {
  heart: 'M0 -1.5 C-4 -1 -10 -3 -10 -9 C-10 -15 -4 -20 0 -25 C4 -20 10 -15 10 -9 C10 -3 4 -1 0 -1.5Z',
  violin: 'M0 0 C-7 -4 -12 -13 -10 -21 C-8 -29 -3 -32 0 -31 C3 -32 8 -29 10 -21 C12 -13 7 -4 0 0Z',
  oval: 'M0 0 C-9 -6 -10 -24 0 -34 C10 -24 9 -6 0 0Z',
  slim: 'M0 0 C-4 -5 -4 -14 0 -19 C4 -14 4 -5 0 0Z',
  round: 'M0 0 C-8 -3 -10 -14 0 -20 C10 -14 8 -3 0 0Z',
};
const T = (x, y, r = 0, k = 1) => `translate(${x} ${y}) rotate(${r}) scale(${k})`;
const leaf = (d, x, y, r, k, fill, vein = true) => {
  const g = s('g', { transform: T(x, y, r, k) }, s('path', { d, class: 'pl-leaf', fill }));
  if (vein) g.append(s('path', { d: 'M0 -1 L0 -' + (d === P.violin ? 28 : d === P.heart ? 21 : d === P.oval ? 30 : 16), class: 'pl-vein' }));
  return g;
};
const stem = (d, w = 2) => s('path', { d, class: 'pl-stem', 'stroke-width': w });

function monstera(g, f, id) {
  // Herzförmige Blätter mit Schlitzen vom Rand her (Maske) und kleinen Löchern
  const mask = s('mask', { id: id + 'm', maskUnits: 'userSpaceOnUse', x: -40, y: -60, width: 80, height: 80 }, s('rect', { x: -40, y: -60, width: 80, height: 80, fill: '#fff' }));
  for (const [x1, y1, x2, y2] of [[-21, -14, -8, -12], [-21.5, -22, -7, -20], [-18, -30, -6, -27], [21, -14, 8, -12], [21.5, -22, 7, -20], [18, -30, 6, -27], [-13, -2, -5, -6], [13, -2, 5, -6]]) {
    mask.append(s('path', { d: `M${x1} ${y1} Q${(x1 + x2) / 2} ${(y1 + y2) / 2 + 2} ${x2} ${y2}`, stroke: '#000', 'stroke-width': 2.6, 'stroke-linecap': 'round', fill: 'none' }));
  }
  mask.append(s('ellipse', { cx: -9, cy: -26, rx: 1.6, ry: 2.6, fill: '#000' }), s('ellipse', { cx: 10, cy: -18, rx: 1.4, ry: 2.4, fill: '#000' }));
  g.append(s('defs', null, mask));
  const leaves = [[34, 64, -42, 0.95], [62, 38, 6, 1.12], [88, 62, 44, 0.98], [46, 88, -72, 0.68], [78, 88, 70, 0.66]];
  for (const [x, y] of leaves) g.append(stem(`M60 104 Q${(60 + x) / 2} ${y + 24} ${x} ${y}`, 2.2));
  for (const [x, y, r, k] of leaves) {
    g.append(s('g', { transform: T(x, y, r, k) },
      s('path', { d: 'M0 0 C-14 2 -23 -10 -21 -23 C-19 -33 -9 -39 0 -36 C9 -39 19 -33 21 -23 C23 -10 14 2 0 0Z', class: 'pl-leaf', fill: f, mask: `url(#${id}m)` }),
      s('path', { d: 'M0 -1 L0 -33', class: 'pl-vein' })));
  }
}

function ficus(g, f) {
  g.append(stem('M60 104 C58 80 63 55 60 16', 2.6));
  const L = [[59, 90, -55, 0.95], [61, 80, 52, 1], [59, 66, -48, 1], [61, 55, 46, 0.95], [60, 42, -40, 0.9], [60, 32, 36, 0.85], [60, 20, -6, 0.8]];
  for (const [x, y, r, k] of L) g.append(leaf(P.violin, x, y, r, k, f));
}

function sansevieria(g, f) {
  const L = [[52, 22, -4, 7], [64, 14, 3, 7.5], [44, 40, -14, 6], [74, 34, 14, 6.5], [58, 30, 0, 6], [36, 58, -24, 5], [84, 56, 24, 5]];
  for (const [xt, yt, lean, w] of L) {
    const xb = 60 + lean * 0.4;
    const d = `M${xb - w} 104 C${xb - w * 1.1} 76 ${xt - 3} ${yt + 26} ${xt} ${yt} C${xt + 3} ${yt + 26} ${xb + w * 1.1} 76 ${xb + w} 104Z`;
    g.append(s('path', { d, class: 'pl-leaf', fill: f }));
    for (let k = 1; k < 5; k++) {
      const yy = 104 - k * ((104 - yt) / 5.2);
      const tt = (104 - yy) / (104 - yt);
      const ww = w * (1 - tt) * 0.9;
      const xx = xb + (xt - xb) * tt;
      g.append(s('path', { d: `M${xx - ww} ${yy} Q${xx} ${yy - 3} ${xx + ww} ${yy}`, class: 'pl-band' }));
    }
    g.append(s('path', { d: `M${xb + w} 104 C${xb + w * 1.1} 76 ${xt + 3} ${yt + 26} ${xt} ${yt}`, class: 'pl-edge' }));
  }
}

function epipremnum(g, f) {
  g.append(stem('M50 104 C40 112 30 124 26 146', 1.6), stem('M72 104 C84 114 92 128 94 148', 1.6), stem('M60 104 C60 90 56 70 58 50', 1.8));
  const L = [[58, 52, -8, 1.05], [48, 68, -50, 0.95], [70, 66, 46, 0.95], [44, 88, -70, 0.8], [76, 88, 70, 0.8], [58, 80, 10, 0.85],
    [33, 116, -150, 0.62], [27, 134, -160, 0.55], [88, 120, 150, 0.62], [94, 140, 165, 0.55]];
  for (const [x, y, r, k] of L) {
    const lg = leaf(P.heart, x, y, r, k, f);
    lg.append(s('path', { d: 'M-4 -6 Q-2 -14 1 -18', class: 'pl-var' }));
    g.append(lg);
  }
}

function kaktus(g, f) {
  g.append(s('path', { d: 'M52 82 H41 V60', class: 'pl-arm', stroke: f }), s('path', { d: 'M68 74 H79 V50', class: 'pl-arm', stroke: f }));
  g.append(s('rect', { x: 49, y: 30, width: 22, height: 76, rx: 11, class: 'pl-leaf', fill: f }));
  for (const x of [54.5, 60, 65.5]) g.append(s('path', { d: `M${x} 36 V102`, class: 'pl-rib' }));
  for (let y = 40; y < 100; y += 9) for (const x of [52, 57.5, 63, 68]) g.append(s('circle', { cx: x + ((y / 9) % 2) * 1.2, cy: y, r: 0.7, class: 'pl-spine' }));
  for (let i = 0; i < 6; i++) g.append(s('ellipse', { cx: 60, cy: 25, rx: 2.6, ry: 6, transform: `rotate(${i * 60} 60 29)`, class: 'pl-acc' }));
  g.append(s('circle', { cx: 60, cy: 29, r: 2.4, class: 'pl-acc2' }));
}

function zitrus(g, f) {
  g.append(stem('M60 104 C59 90 61 76 60 62', 3.4), stem('M60 74 L52 64', 1.8), stem('M60 70 L69 61', 1.8));
  g.append(s('circle', { cx: 60, cy: 46, r: 23, class: 'pl-leaf2' }));
  const n = 16;
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2;
    const x = 60 + Math.cos(a) * 21;
    const y = 46 + Math.sin(a) * 19;
    g.append(leaf(P.slim, x, y, (a * 180) / Math.PI + 90, 0.95, f, false));
  }
  for (const [x, y, r, k] of [[52, 40, -20, 1], [66, 36, 25, 1], [58, 54, 5, 1], [70, 52, 60, 0.9]]) g.append(leaf(P.slim, x, y, r, k, f, false));
  for (const [x, y] of [[47, 54], [72, 44], [58, 62], [64, 30]]) g.append(s('ellipse', { cx: x, cy: y, rx: 4.6, ry: 3.6, class: 'pl-acc' }), s('circle', { cx: x - 1.5, cy: y - 1.2, r: 0.9, class: 'pl-acc2' }));
}

function calathea(g, f) {
  const L = [[60, 30, 0, 1.15], [42, 40, -28, 1.05], [78, 40, 28, 1.05], [32, 62, -52, 0.95], [88, 62, 52, 0.95], [50, 58, -12, 0.9], [70, 58, 12, 0.9]];
  for (const [x, y] of L) g.append(stem(`M60 104 Q${(60 + x) / 2} ${(104 + y) / 2 + 8} ${x} ${y}`, 1.4));
  for (const [x, y, r, k] of L) {
    const lg = s('g', { transform: T(x, y, r, k) }, s('path', { d: P.oval, class: 'pl-leaf', fill: f }));
    for (let i = 1; i < 6; i++) {
      const yy = -i * 5.4;
      const w = 6.4 * Math.sin((i / 6) * Math.PI) + 1;
      lg.append(s('path', { d: `M0 ${yy} Q${-w * 0.6} ${yy - 1.8} ${-w} ${yy - 4}`, class: 'pl-feather' }), s('path', { d: `M0 ${yy} Q${w * 0.6} ${yy - 1.8} ${w} ${yy - 4}`, class: 'pl-feather' }));
    }
    lg.append(s('path', { d: 'M0 -1 L0 -31', class: 'pl-vein' }));
    g.append(lg);
  }
}

function orchidee(g, f) {
  g.append(stem('M62 100 C64 70 62 46 70 34 C76 26 86 26 92 34', 1.6));
  const lv = (r, flip) => s('g', { transform: `translate(60 103) scale(${flip ? -1 : 1} 1) rotate(${r})` }, s('path', { d: 'M0 0 C8 -9 26 -10 36 -3 C26 3 8 4 0 0Z', class: 'pl-leaf', fill: f }), s('path', { d: 'M2 -1 Q18 -5 33 -3', class: 'pl-vein' }));
  g.append(lv(-8, false), lv(-14, true), lv(4, false));
  const flower = (x, y, k) => {
    const fg = s('g', { transform: T(x, y, 0, k) });
    for (const a of [0, 120, 240]) fg.append(s('ellipse', { cx: 0, cy: -6, rx: 3, ry: 6, transform: `rotate(${a})`, class: 'pl-acc' }));
    for (const a of [60, 300]) fg.append(s('ellipse', { cx: 0, cy: -6.5, rx: 5.2, ry: 6, transform: `rotate(${a})`, class: 'pl-acc' }));
    fg.append(s('ellipse', { cx: 0, cy: 3.5, rx: 3, ry: 3.6, class: 'pl-acc2' }), s('circle', { cx: 0, cy: -0.5, r: 1.6, class: 'pl-acc3' }));
    return fg;
  };
  for (const [x, y, k] of [[66, 44, 0.9], [72, 33, 1], [82, 28, 1.05], [92, 34, 0.95], [95, 46, 0.7]]) g.append(flower(x, y, k));
}

function zamioculcas(g, f) {
  const S = [[60, 104, 58, 18, 0], [60, 104, 38, 30, -1], [60, 104, 82, 28, 1], [60, 104, 30, 58, -1], [60, 104, 90, 56, 1]];
  for (const [x0, y0, x1, y1] of S) g.append(stem(`M${x0} ${y0} Q${(x0 + x1) / 2} ${(y0 + y1) / 2 + 10} ${x1} ${y1}`, 2.2));
  for (const [x0, y0, x1, y1] of S) {
    const cx = (x0 + x1) / 2;
    const cy = (y0 + y1) / 2 + 10;
    for (let t = 0.38; t <= 1.0001; t += 0.124) {
      const x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * x1;
      const y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * y1;
      const dx = 2 * (1 - t) * (cx - x0) + 2 * t * (x1 - cx);
      const dy = 2 * (1 - t) * (cy - y0) + 2 * t * (y1 - cy);
      const ang = (Math.atan2(dy, dx) * 180) / Math.PI + 90;
      const k = 0.55 + 0.25 * (1 - Math.abs(t - 0.7));
      if (t > 0.97) g.append(leaf(P.round, x, y, ang, k * 0.85, f, false));
      else g.append(leaf(P.round, x, y, ang - 55, k, f, false), leaf(P.round, x, y, ang + 55, k, f, false));
    }
  }
}

function chlorophytum(g, f) {
  const n = 13;
  for (let i = 0; i < n; i++) {
    const a = -80 + (i / (n - 1)) * 160;
    const rad = (a * Math.PI) / 180;
    const len = 40 + 12 * Math.cos(rad * 1.2);
    const x1 = 60 + Math.sin(rad) * len;
    const y1 = 102 - Math.cos(rad) * len * 0.75 + Math.abs(Math.sin(rad)) * 26;
    const cx = 60 + Math.sin(rad) * len * 0.55;
    const cy = 102 - len * 0.95;
    g.append(s('path', { d: `M60 102 Q${cx} ${cy} ${x1} ${y1}`, class: 'pl-blade', stroke: f }), s('path', { d: `M60 102 Q${cx} ${cy} ${x1} ${y1}`, class: 'pl-blade-mid' }));
  }
  g.append(stem('M74 100 C96 92 104 112 100 132', 1), stem('M97 132 l-5 -6 M98 132 l1 -8 M100 132 l6 -5', 1.4));
}

function generic(g, f) {
  g.append(stem('M60 104 C60 84 58 66 60 40', 2.2));
  for (const [x, y, r, k] of [[60, 42, 0, 1.1], [59, 60, -55, 1], [61, 70, 55, 1], [59, 84, -60, 0.85], [61, 90, 62, 0.8]]) g.append(leaf(P.round, x, y, r, k, f));
}

const DRAW = { monstera, ficus_lyrata: ficus, sansevieria, epipremnum, kaktus, zitrus, calathea, orchidee, zamioculcas, chlorophytum, generic };

/** Pflanze im Topf mit kleinem fluidi-Sensor (LED-Tropfen in Zustandsfarbe). */
export function plantArt(species, { state = 'ok', size = 120, sensor = true, label } = {}) {
  const id = nextId('pa');
  const key = DRAW[species] ? species : 'generic';
  const svg = s('svg', { viewBox: '0 0 120 150', width: size, height: Math.round(size * 1.25), class: `plantart sp-${key}`, role: 'img', 'aria-label': label || 'Pflanze' });
  const defs = s('defs', null,
    s('linearGradient', { id: id + 'l', x1: '0', y1: '0', x2: '0.4', y2: '1' }, s('stop', { offset: '0', class: 'lg-a' }), s('stop', { offset: '1', class: 'lg-b' })),
    s('linearGradient', { id: id + 'p', x1: '0', y1: '0', x2: '1', y2: '0' }, s('stop', { offset: '0', class: 'pg-a' }), s('stop', { offset: '0.55', class: 'pg-b' }), s('stop', { offset: '1', class: 'pg-c' })));
  svg.append(defs, s('ellipse', { cx: 60, cy: 147, rx: 34, ry: 3, class: 'pl-shadow' }));
  const g = s('g', { class: 'pl-plant' });
  DRAW[key](g, `url(#${id}l)`, id);
  // Topf: Körper, Erde, Sensor, Rand
  svg.append(
    s('path', { d: 'M33 110 H87 L82.5 144 Q82 147 79 147 H41 Q38 147 37.5 144 Z', class: 'pl-pot', fill: `url(#${id}p)` }),
    s('ellipse', { cx: 60, cy: 105, rx: 27, ry: 4, class: 'pl-soil' }));
  svg.append(g);
  if (sensor) {
    const sc = STATE_CLASS[state] || 'st-off';
    svg.append(s('g', { class: `pl-sensor ${sc}` },
      s('rect', { x: 75, y: 89, width: 9, height: 17, rx: 1.2, class: 'sn-body' }),
      s('rect', { x: 75, y: 89, width: 9, height: 5.5, rx: 1.2, class: 'sn-cap' }),
      s('path', { d: 'M79.5 91.2 L78.2 94 A1.5 1.5 0 1 0 80.8 94 Z', class: 'sn-led' })));
  }
  svg.append(s('rect', { x: 30, y: 103, width: 60, height: 8, rx: 2, class: 'pl-rim' }));
  return svg;
}

export const SPECIES_ORDER = Object.keys(DRAW);
