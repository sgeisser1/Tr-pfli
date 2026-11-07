// Übersicht: eine Karte pro Pflanze (REQ-APP-03, REQ-APP-10).
import { h, drop, batteryIcon, signalIcon, fmt, SUBSTRATE, STATE_TEXT } from '../ui.js';
import { dropColor, relativeTime } from '../calc.js';

export function plantCard(p, nowS) {
  const L = p.latest;
  const color = dropColor(p);
  const st = p.status;
  const alarm = color === 'red';
  let stateText = L ? STATE_TEXT[L.moisture_state] || L.moisture_state : p.sensor_id ? 'Noch kein Messwert' : 'Kein Sensor zugeordnet';
  if (st.stale && L) stateText = 'Keine neuen Werte';
  const stateCls = alarm ? 'red' : st.needs_water ? 'blue' : '';
  const meter = h('div.meter', { title: `Giessschwelle ${p.threshold_pct} %` });
  if (L && L.moisture_pct !== null) {
    const fill = h('span.fill' + (st.needs_water ? '.low' : ''));
    fill.style.width = `${Math.max(0, Math.min(100, L.moisture_pct))}%`;
    meter.append(fill);
  }
  const mark = h('span.mark');
  mark.style.left = `calc(${p.threshold_pct}% - 1px)`;
  meter.append(mark);

  const facts = [];
  if (L) facts.push(h('span.fact' + (st.stale ? '.warn' : ''), { title: fmt.dateTime(L.t) }, relativeTime(Date.parse(L.t) / 1000, nowS)));
  if (p.battery) {
    facts.push(h('span.fact' + (p.battery.state !== 'ok' ? '.warn' : ''), { title: `Batterie ${p.battery.pct} %, ${fmt.mv(p.battery.mv)}` },
      batteryIcon(p.battery), p.battery.state !== 'ok' ? `noch ca. ${p.battery.days_left ?? '?'} Tage` : `${p.battery.pct} %`));
  }
  if (p.signal) {
    facts.push(h('span.fact' + (p.signal.quality <= 1 ? '.warn' : ''), { title: `Signal ${p.signal.rssi_dbm} dBm` },
      signalIcon(p.signal), p.signal.quality <= 1 ? 'schwach' : `${p.signal.rssi_dbm} dBm`));
  }
  if (p.calibration === 'default') facts.push(h('span.pill.info', null, 'Startkalibrierung'));
  if (st.sensor_error) facts.push(h('span.pill.warn', null, st.sensor_error));

  return h(`a.card.plant${st.needs_water ? '.need' : ''}${alarm ? '.alarm' : ''}`, { href: `#/pflanze/${p.id}`, 'data-id': p.id },
    h('div.plant-head', null,
      h('div', null, h('h2.plant-name', null, p.name), h('div.plant-sub', null, SUBSTRATE[p.substrate] + (p.sensor_id ? ` · ${p.sensor_id}` : ''))),
      drop(color, stateText)),
    h('div.big', null,
      h('span.val', null, L && L.moisture_pct !== null ? fmt.pct(L.moisture_pct) : '–'),
      h('span.unit', null, '%'),
      h('span.temp', null, L ? fmt.temp(L.temp_c) : '')),
    meter,
    h(`div.state${stateCls ? '.' + stateCls : ''}`, null, stateText),
    h('div.facts', null, facts));
}

export default async function overview(main, ctx) {
  let plants = await ctx.api.get('/plants');
  const grid = h('div.grid');
  const summary = h('p.muted');
  const draw = () => {
    const now = Date.now() / 1000;
    grid.replaceChildren(...plants.map((p) => plantCard(p, now)));
    const need = plants.filter((p) => p.status.needs_water);
    const warn = plants.filter((p) => p.status.battery_low || p.status.stale || p.status.sensor_error ||
      (p.latest && ['air', 'flooded'].includes(p.latest.moisture_state)));
    summary.replaceChildren(
      need.length ? h('strong', null, need.length === 1 ? '1 Pflanze braucht Wasser. ' : `${need.length} Pflanzen brauchen Wasser. `) : 'Alle Pflanzen sind versorgt. ',
      warn.length ? `${warn.length} Hinweis${warn.length > 1 ? 'e' : ''} zu Sensoren.` : '');
    if (!plants.length) grid.replaceChildren(h('div.card.empty', null, 'Noch keine Pflanzen. ', h('a', { href: '#/koppeln' }, 'Ersten Sensor koppeln')));
  };
  // Reihenfolge: zuerst „giessen“, dann Warnungen, dann alphabetisch
  const sort = () => plants.sort((a, b) => (b.status.needs_water - a.status.needs_water) ||
    ((dropColor(b) === 'red') - (dropColor(a) === 'red')) || a.name.localeCompare(b.name, 'de'));
  sort();
  main.replaceChildren(
    h('div.pagehead', null, h('h1', null, 'Pflanzen'),
      h('div.row', null, h('a.btn.ghost', { href: '#/neu' }, 'Pflanze hinzufügen'), h('a.btn.primary', { href: '#/koppeln' }, 'Sensor koppeln'))),
    summary, grid);
  draw();
  const offPlant = ctx.stream.on('plant', (p) => {
    const i = plants.findIndex((x) => x.id === p.id);
    if (i >= 0) plants[i] = p;
    else plants.push(p);
    sort();
    draw();
  });
  const offDel = ctx.stream.on('plant_deleted', (d) => {
    plants = plants.filter((x) => x.id !== d.id);
    draw();
  });
  const timer = setInterval(draw, 60_000);
  return { cleanup() { offPlant(); offDel(); clearInterval(timer); } };
}
