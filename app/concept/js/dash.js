// Dashboard-Modus (TV/Bildschirm, auch Nur-Lese-Ansicht für Kollegen): nur GET /dashboard.
import { h, fmt } from './dom.js';
import { icon, dropChar, plantArt, MOOD_TEXT } from './art.js';
import { drawRoom, plantMap, dashKey, DASH_TEXT } from './room.js';

export default async function dash(el, ctx) {
  const root = document.documentElement;
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
  const draw = async () => {
    const d = await ctx.api.get('/dashboard');
    const pm = plantMap(d.plants);
    sum.replaceChildren(
      h('span.chip.k-dry', null, icon('drop'), `${d.summary.needs_water} giessen`),
      h('span.chip.k-alert', null, icon('alert'), `${d.summary.warnings} Hinweise`),
      h('span.chip.k-ok', null, icon('plants'), `${d.summary.plants} Pflanzen`));
    const tiles = d.plants.slice().sort((a, b) => (b.needs_water - a.needs_water) || (a.forecast_days ?? 99) - (b.forecast_days ?? 99)).map((p) => {
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
    body.replaceChildren(
      d.roomplan && d.roomplan.rooms.length ? h('section.card.d-room', null, h('h2.card-title', null, icon('room'), d.roomplan.rooms[0].name), drawRoom(d.roomplan.rooms[0], pm)) : null,
      h('section.d-tiles', null, tiles));
    foot.replaceChildren(icon('info'), `Nur-Lese-Ansicht · aktualisiert ${fmt.time(d.generated)} · ${d.public ? 'öffentlich im Firmennetz (eigener Port)' : 'nur im LAN mit Leserecht'}`);
  };
  await draw();
  el.append(h('div.dash', null,
    h('header.d-head', null,
      h('div.d-brand', null, h('img.logo-l', { src: 'img/logo.svg', alt: 'fluidi', width: 120, height: 46 }), h('img.logo-d', { src: 'img/logo-dunkel.svg', alt: 'fluidi', width: 120, height: 46 }), h('span.d-title', null, 'Pflanzen im Büro')),
      sum,
      h('div.d-time', null, clock, date),
      root.dataset.kiosk ? null : h('a.iconbtn.d-close', { href: '#/', 'aria-label': 'Dashboard schliessen' }, icon('x'))),
    body, foot));
  root.dataset.dash = '1';
  const t1 = setInterval(tick, 10_000);
  const t2 = setInterval(draw, 60_000);
  return { cleanup() { clearInterval(t1); clearInterval(t2); delete root.dataset.dash; } };
}
