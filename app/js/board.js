// fluidi – Dashboard-Darstellung (In-App #/dashboard und öffentliche Nur-Lese-Seite dashboard.html, D-020).
// Nur dom.js/art.js als Abhängigkeit, damit der öffentliche Port nur wenige Dateien ausliefern muss.
import { h, s, fmt, fill } from './dom.js';
import { icon, dropChar, plantArt, MOOD_TEXT } from './art.js';

export const WALL = { n: 'Nord', e: 'Ost', s: 'Süd', w: 'West' };

/** Zeichnet einen Raum. plants: Map id -> {name, mood, state, pct}. opts.edit: Editor-Ereignisse. */
export function drawRoom(room, plants, opts = {}) {
  const W = room.width_cm;
  const D = room.depth_cm;
  const M = 70;
  const svg = s('svg', { viewBox: `${-M} ${-M} ${W + 2 * M} ${D + 2 * M}`, class: 'roomsvg' + (opts.edit ? ' editing' : ''), role: 'img', 'aria-label': `Raumplan ${room.name}` });
  const sunId = 'sun' + Math.random().toString(36).slice(2, 6);
  const grad = (k, x1, y1, x2, y2) => s('linearGradient', { id: sunId + k, x1, y1, x2, y2 }, s('stop', { offset: 0, class: 'sun-a' }), s('stop', { offset: 1, class: 'sun-b' }));
  svg.append(s('defs', null, grad('n', 0, 0, 0, 1), grad('s', 0, 1, 0, 0), grad('w', 0, 0, 1, 0), grad('e', 1, 0, 0, 0),
    s('pattern', { id: sunId + 'p', width: 50, height: 50, patternUnits: 'userSpaceOnUse' }, s('path', { d: 'M50 0H0V50', class: 'rm-gridl' }))));
  const floorParts = [];
  // Sonnenseiten: Lichtkeil nach innen + Sonne aussen
  for (const w of room.sun_walls || []) {
    const dp = Math.min(W, D) * 0.42;
    const [x, y, ww, hh] = { n: [0, 0, W, dp], s: [0, D - dp, W, dp], w: [0, 0, dp, D], e: [W - dp, 0, dp, D] }[w];
    floorParts.push(s('rect', { x, y, width: ww, height: hh, class: 'rm-sunlight', fill: `url(#${sunId}${w})` }));
    const [sx, sy] = { n: [W / 2, -44], s: [W / 2, D + 44], w: [-44, D / 2], e: [W + 44, D / 2] }[w];
    const sun = s('g', { class: 'rm-sun', transform: `translate(${sx} ${sy})` }, s('circle', { r: 12 }));
    for (let i = 0; i < 8; i++) sun.append(s('line', { x1: 0, y1: -18, x2: 0, y2: -25, transform: `rotate(${i * 45})` }));
    floorParts.push(sun);
  }
  svg.append(s('rect', { x: 0, y: 0, width: W, height: D, class: 'rm-floor' }), s('rect', { x: 0, y: 0, width: W, height: D, class: 'rm-grid', fill: `url(#${sunId}p)` }), ...floorParts);
  for (const f of room.furniture || []) {
    svg.append(s('g', { class: `rm-furn f-${f.kind}` }, s('rect', { x: f.x_cm, y: f.y_cm, width: f.w_cm, height: f.d_cm, rx: 8 }),
      s('text', { x: f.x_cm + f.w_cm / 2, y: f.y_cm + f.d_cm / 2 + 6, 'text-anchor': 'middle' }, f.label || '')));
  }
  svg.append(s('rect', { x: 0, y: 0, width: W, height: D, class: 'rm-wall' }));
  room.openings.forEach((o, i) => {
    const horiz = o.wall === 'n' || o.wall === 's';
    const y0 = o.wall === 'n' ? 0 : o.wall === 's' ? D : null;
    const x0 = o.wall === 'w' ? 0 : o.wall === 'e' ? W : null;
    const g = s('g', { class: `rm-open o-${o.type}`, 'data-i': i });
    if (horiz) {
      g.append(s('line', { x1: o.offset_cm, x2: o.offset_cm + o.length_cm, y1: y0, y2: y0, class: 'rm-gap' }));
      if (o.type === 'window') g.append(s('line', { x1: o.offset_cm, x2: o.offset_cm + o.length_cm, y1: y0 - 4, y2: y0 - 4, class: 'rm-glass' }), s('line', { x1: o.offset_cm, x2: o.offset_cm + o.length_cm, y1: y0 + 4, y2: y0 + 4, class: 'rm-glass' }));
      else { const dir = o.wall === 'n' ? 1 : -1; g.append(s('path', { d: `M${o.offset_cm} ${y0} L${o.offset_cm} ${y0 + dir * o.length_cm} A${o.length_cm} ${o.length_cm} 0 0 ${dir > 0 ? 0 : 1} ${o.offset_cm + o.length_cm} ${y0}`, class: 'rm-door' })); }
    } else {
      g.append(s('line', { y1: o.offset_cm, y2: o.offset_cm + o.length_cm, x1: x0, x2: x0, class: 'rm-gap' }));
      if (o.type === 'window') g.append(s('line', { y1: o.offset_cm, y2: o.offset_cm + o.length_cm, x1: x0 - 4, x2: x0 - 4, class: 'rm-glass' }), s('line', { y1: o.offset_cm, y2: o.offset_cm + o.length_cm, x1: x0 + 4, x2: x0 + 4, class: 'rm-glass' }));
      else { const dir = o.wall === 'w' ? 1 : -1; g.append(s('path', { d: `M${x0} ${o.offset_cm} L${x0 + dir * o.length_cm} ${o.offset_cm} A${o.length_cm} ${o.length_cm} 0 0 ${dir > 0 ? 1 : 0} ${x0} ${o.offset_cm + o.length_cm}`, class: 'rm-door' })); }
    }
    g.append(s('title', null, `${o.type === 'window' ? 'Fenster' : 'Tür'} ${WALL[o.wall]}`));
    svg.append(g);
  });
  // Nordpfeil
  svg.append(s('g', { class: 'rm-north', transform: `translate(${-44} ${-44}) rotate(${room.north_deg || 0})` }, s('path', { d: 'M0 -16 L7 8 L0 3 L-7 8Z' }), s('text', { y: 24, 'text-anchor': 'middle' }, 'N')));
  for (const pp of room.plants) {
    const p = plants.get(pp.plant_id);
    if (!p) continue;
    const g = s('g', { class: `rm-plant k-${p.key}`, 'data-id': pp.plant_id, transform: `translate(${pp.x_cm} ${pp.y_cm})`, tabindex: opts.edit ? null : 0, role: opts.edit ? null : 'link', 'aria-label': `${p.name}: ${p.text}` });
    g.append(s('circle', { r: 30, class: 'rm-halo' }));
    const d = dropChar(p.mood, { pct: p.pct, state: p.drop, size: 40, animate: false });
    d.setAttribute('x', -20); d.setAttribute('y', -28);
    g.append(d, s('rect', { x: -48, y: 32, width: 96, height: 24, rx: 12, class: 'rm-labbg' }), s('text', { y: 49, 'text-anchor': 'middle', class: 'rm-lab' }, p.name.length > 12 ? p.name.slice(0, 11) + '…' : p.name));
    if (!opts.edit && opts.onOpen) {
      g.addEventListener('click', () => opts.onOpen(pp.plant_id));
      g.addEventListener('keydown', (ev) => { if (ev.key === 'Enter') opts.onOpen(pp.plant_id); });
    }
    svg.append(g);
  }
  return svg;
}

export const dashKey = (p) => (p.needs_water ? 'dry' : p.state === 'ok' ? 'ok' : p.state === 'stale' ? 'stale' : p.state === 'none' ? 'none' : 'alert');
export const DASH_TEXT = { dry: 'Giessen nötig', ok: 'Feucht genug', stale: 'Keine neuen Werte', none: 'Kein Sensor', alert: 'Sensor prüfen' };


export function dashMap(list) {
  return new Map(list.map((p) => [p.id, { name: p.name, mood: p.mood, drop: p.state, key: dashKey(p), text: DASH_TEXT[dashKey(p)], pct: p.moisture_pct }]));
}

/** Dashboard zeichnen. opts: {kiosk, closeHref}. Liefert {update(d)}. */
export function renderBoard(el, d, opts = {}) {
  const clock = h('div.d-clock');
  const date = h('div.d-date');
  const tick = () => {
    const n = new Date();
    clock.textContent = n.toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' });
    date.textContent = n.toLocaleDateString('de-CH', { weekday: 'long', day: 'numeric', month: 'long' });
  };
  tick();
  const body = h('div.d-body');
  const foot = h('div.d-foot');
  const sum = h('div.d-sum');
  const title = h('span.d-title');
  const update = (dd) => {
    const pm = dashMap(dd.plants);
    title.textContent = dd.title;
    const cl = dd.climate;
    fill(sum, 
      h('span.chip.k-dry', null, icon('drop'), `${dd.summary.needs_water} giessen`),
      h('span.chip.k-alert', null, icon('alert'), `${dd.summary.warnings} Hinweise`),
      h('span.chip.k-ok', null, icon('plants'), `${dd.summary.plants} Pflanzen`),
      cl ? h('span.chip', { title: 'Raumklima am Gateway' }, icon('thermo'), `${fmt.n1(cl.temp_c)} °C · ${fmt.n0(cl.rh_pct)} %`) : null);
    const tiles = dd.plants.slice().sort((a, b) => (b.needs_water - a.needs_water) || (a.forecast_days ?? 99) - (b.forecast_days ?? 99)).map((p) => {
      const k = dashKey(p);
      return h(`div.d-tile.k-${k}`, null,
        h('div.d-art', null, plantArt(p.species, { state: p.state, size: 70 })),
        h('div.d-info', null,
          h('div.d-name', null, p.name),
          h('div.d-val', null, h('span.big', null, p.moisture_pct == null ? '–' : fmt.pct(p.moisture_pct)), h('span.unit', null, p.moisture_pct == null ? '' : '%')),
          h(`div.d-state.b-${k}`, null, icon(k === 'dry' ? 'drop' : k === 'ok' ? 'check' : k === 'stale' ? 'clock' : k === 'none' ? 'info' : 'alert'), DASH_TEXT[k]),
          h('div.d-fc', null, p.needs_water ? MOOD_TEXT[p.mood] : p.forecast_days != null ? `giessen ${fmt.days(p.forecast_days)}` : '')),
        dropChar(p.mood, { pct: p.moisture_pct, state: p.state, size: 44 }));
    });
    const room = dd.roomplan && dd.roomplan.rooms.length && dd.roomplan.rooms[0].plants.length ? dd.roomplan.rooms[0] : null;
    body.classList.toggle('no-room', !room);
    fill(body, ...[room ? h('section.card.d-room', null, h('h2.card-title', null, icon('room'), room.name), drawRoom(room, pm)) : null,
      h('section.d-tiles', null, tiles)].filter(Boolean));
    fill(foot, icon('info'), `Nur-Lese-Ansicht · aktualisiert ${fmt.time(dd.generated)} · ${dd.public ? 'öffentlich im Firmennetz (eigener Port, ohne Anmeldung)' : 'in der App'}`);
  };
  update(d);
  el.append(h('div.dash', null,
    h('header.d-head', null,
      h('div.d-brand', null, h('img.logo-l', { src: 'img/logo.svg', alt: 'fluidi', width: 120, height: 46 }), h('img.logo-d', { src: 'img/logo-dunkel.svg', alt: 'fluidi', width: 120, height: 46 }), title),
      sum, h('div.d-time', null, clock, date),
      opts.closeHref ? h('a.iconbtn.d-close', { href: opts.closeHref, 'aria-label': 'Dashboard schliessen' }, icon('x')) : null),
    body, foot));
  const t = setInterval(tick, 10_000);
  return { update, stop: () => clearInterval(t) };
}
