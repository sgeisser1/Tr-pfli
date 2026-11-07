// Raumplan: Ansicht und einfacher Editor (Pflanzen ziehen, Fenster/Türen setzen, Sonnenseite).
import { h, s, toast } from './dom.js';
import { icon, dropChar } from './art.js';
import { stateOf, pageHead, seg } from './comp.js';

const WALL = { n: 'Nord', e: 'Ost', s: 'Süd', w: 'West' };

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

export function plantMap(list) {
  return new Map(list.map((p) => {
    const st = p.mood !== undefined && p.status ? stateOf(p) : null;
    return [p.id, st ? { name: p.name, mood: p.mood, drop: st.drop, key: st.key, text: st.text, pct: p.latest && p.latest.moisture_pct }
      : { name: p.name, mood: p.mood, drop: p.state, key: dashKey(p), text: DASH_TEXT[dashKey(p)], pct: p.moisture_pct }];
  }));
}

export default async function room(el, ctx) {
  const [plan, plants] = await Promise.all([ctx.api.get('/roomplan'), ctx.api.get('/plants')]);
  const pm = plantMap(plants);
  let work = JSON.parse(JSON.stringify(plan));
  let editing = ctx.params.edit === '1';
  let tool = 'move';
  const r = () => work.rooms[0];
  const box = h('div.roombox');
  const side = h('div.roomside');

  const svgPoint = (svg, ev) => {
    const pt = svg.createSVGPoint();
    pt.x = ev.clientX; pt.y = ev.clientY;
    return pt.matrixTransform(svg.getScreenCTM().inverse());
  };
  const draw = () => {
    const svg = drawRoom(r(), pm, { edit: editing, onOpen: (id) => ctx.go(`/pflanze/${id}`) });
    if (editing) wireEditor(svg);
    box.replaceChildren(svg);
    drawSide();
  };
  function wireEditor(svg) {
    let drag = null;
    svg.addEventListener('pointerdown', (ev) => {
      const pg = ev.target.closest('.rm-plant');
      const og = ev.target.closest('.rm-open');
      if (tool === 'delete') {
        if (pg) r().plants = r().plants.filter((x) => x.plant_id !== Number(pg.dataset.id));
        else if (og) r().openings.splice(Number(og.dataset.i), 1);
        draw();
        return;
      }
      if (tool === 'move' && pg) {
        drag = { id: Number(pg.dataset.id), g: pg };
        svg.setPointerCapture(ev.pointerId);
        pg.classList.add('drag');
        return;
      }
      if (tool === 'window' || tool === 'door') {
        const p = svgPoint(svg, ev);
        const W = r().width_cm;
        const D = r().depth_cm;
        const dist = { n: Math.abs(p.y), s: Math.abs(p.y - D), w: Math.abs(p.x), e: Math.abs(p.x - W) };
        const wall = Object.entries(dist).sort((a, b) => a[1] - b[1])[0];
        if (wall[1] > 50) { toast('Für Fenster/Türen auf eine Wand tippen'); return; }
        const len = tool === 'window' ? 120 : 90;
        const wl = wall[0] === 'n' || wall[0] === 's' ? W : D;
        const along = wall[0] === 'n' || wall[0] === 's' ? p.x : p.y;
        r().openings.push({ type: tool, wall: wall[0], offset_cm: Math.round(Math.max(0, Math.min(wl - len, along - len / 2))), length_cm: len });
        draw();
      }
    });
    svg.addEventListener('pointermove', (ev) => {
      if (!drag) return;
      const p = svgPoint(svg, ev);
      const x = Math.round(Math.max(0, Math.min(r().width_cm, p.x)));
      const y = Math.round(Math.max(0, Math.min(r().depth_cm, p.y)));
      drag.g.setAttribute('transform', `translate(${x} ${y})`);
      const e = r().plants.find((q) => q.plant_id === drag.id);
      e.x_cm = x; e.y_cm = y;
    });
    const end = () => { if (drag) { drag.g.classList.remove('drag'); drag = null; } };
    svg.addEventListener('pointerup', end);
    svg.addEventListener('pointercancel', end);
  }
  function drawSide() {
    const placed = new Set(r().plants.map((x) => x.plant_id));
    const unplaced = plants.filter((p) => !placed.has(p.id));
    if (!editing) {
      const byWin = r().plants.length;
      side.replaceChildren(
        h('section.card', null, h('h2.card-title', null, icon('info'), 'Legende'),
          h('ul.legend-list', null,
            h('li', null, h('span.lgd.k-ok'), 'feucht genug'), h('li', null, h('span.lgd.k-dry'), 'giessen nötig'),
            h('li', null, h('span.lgd.k-alert'), 'Sensor prüfen'), h('li', null, h('span.lgd.k-stale'), 'keine neuen Werte'),
            h('li', null, icon('sun'), 'Sonnenseite'), h('li', null, icon('window'), 'Fenster'), h('li', null, icon('door'), 'Tür')),
          h('p.small.muted', null, `${byWin} von ${plants.length} Pflanzen platziert. Tippe auf eine Pflanze für Details.`)));
      return;
    }
    side.replaceChildren(
      h('section.card', null, h('h2.card-title', null, icon('edit'), 'Werkzeug'),
        seg([['move', 'Verschieben', 'move'], ['window', 'Fenster', 'window'], ['door', 'Tür', 'door'], ['delete', 'Entfernen', 'trash']], tool, (v) => { tool = v; }, 'Werkzeug'),
        h('p.small.muted', null, 'Pflanzen ziehen · auf eine Wand tippen, um Fenster oder Türen zu setzen.'),
        h('h3', null, 'Sonnenseite'),
        h('div.chips', null, Object.entries(WALL).map(([k, t]) => {
          const on = (r().sun_walls || []).includes(k);
          return h(`button.chip.tog${on ? '.on' : ''}`, { type: 'button', 'aria-pressed': String(on), onclick: () => { const sw = new Set(r().sun_walls || []); sw.has(k) ? sw.delete(k) : sw.add(k); r().sun_walls = [...sw]; draw(); } }, icon('sun'), t);
        })),
        h('h3', null, 'Raum'),
        h('div.row2', null,
          h('label.field', null, 'Breite (m)', h('input.input', { type: 'number', min: 1, max: 50, step: 0.1, value: r().width_cm / 100, onchange: (ev) => { r().width_cm = Math.round(ev.target.value * 100); draw(); } })),
          h('label.field', null, 'Tiefe (m)', h('input.input', { type: 'number', min: 1, max: 50, step: 0.1, value: r().depth_cm / 100, onchange: (ev) => { r().depth_cm = Math.round(ev.target.value * 100); draw(); } })))),
      h('section.card', null, h('h2.card-title', null, icon('plants'), 'Nicht platziert'),
        unplaced.length ? h('div.chips', null, unplaced.map((p) => h('button.chip', { type: 'button', onclick: () => { r().plants.push({ plant_id: p.id, x_cm: Math.round(r().width_cm / 2), y_cm: Math.round(r().depth_cm / 2) }); draw(); } }, icon('plus'), p.name)))
          : h('p.small.muted', null, 'Alle Pflanzen sind im Plan.')));
  }
  const actions = h('div.ph-act');
  const head = pageHead(r().name, 'Raumplan', actions);
  const setActions = () => {
    actions.replaceChildren(...(editing ? [
      h('button.btn.ghost', { type: 'button', onclick: () => { work = JSON.parse(JSON.stringify(plan)); editing = false; setActions(); draw(); } }, 'Abbrechen'),
      h('button.btn.primary', { type: 'button', onclick: save }, icon('check'), 'Sichern')]
      : [h('button.btn.ghost', { type: 'button', onclick: () => { editing = true; setActions(); draw(); } }, icon('edit'), 'Bearbeiten')]));
  };
  async function save() {
    try {
      const saved = await ctx.api.put('/roomplan', work);
      Object.assign(plan, saved);
      work = JSON.parse(JSON.stringify(saved));
      editing = false;
      toast('Raumplan gesichert', 'ok');
      setActions();
      draw();
    } catch (e) { toast(e.message, 'err'); }
  }
  setActions();
  draw();
  el.append(head, h('div.roomwrap', null, h('section.card.roomcard', null, box), side));
}
