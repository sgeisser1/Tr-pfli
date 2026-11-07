// Raumplan: Ansicht und einfacher Editor (Pflanzen ziehen, Fenster/Türen setzen, Sonnenseite).
import { h, toast, fill } from './dom.js';
import { icon } from './art.js';
import { stateOf, pageHead, seg } from './comp.js';

import { WALL, drawRoom, dashKey, DASH_TEXT } from './board.js';

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
    fill(box, svg);
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
      fill(side, 
        h('section.card', null, h('h2.card-title', null, icon('info'), 'Legende'),
          h('ul.legend-list', null,
            h('li', null, h('span.lgd.k-ok'), 'feucht genug'), h('li', null, h('span.lgd.k-dry'), 'giessen nötig'),
            h('li', null, h('span.lgd.k-alert'), 'Sensor prüfen'), h('li', null, h('span.lgd.k-stale'), 'keine neuen Werte'),
            h('li', null, icon('sun'), 'Sonnenseite'), h('li', null, icon('window'), 'Fenster'), h('li', null, icon('door'), 'Tür')),
          h('p.small.muted', null, `${byWin} von ${plants.length} Pflanzen platziert. Tippe auf eine Pflanze für Details.`)));
      return;
    }
    fill(side, 
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
    fill(actions, ...(editing ? [
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
