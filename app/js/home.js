// Übersicht: „Ein Blick genügt“ – Gesamtzustand, Hinweise, Pflanzenkarten (D-015).
import { h, fmt, fill } from './dom.js';
import { icon, dropChar, plantArt } from './art.js';
import { stateOf, plantCard, seg } from './comp.js';

const plural = (n, one, many) => (n === 1 ? one : many);

export default async function home(el, ctx) {
  const [plants, alerts, climate] = await Promise.all([ctx.api.get('/plants'), ctx.api.get('/alerts'), ctx.api.get('/climate', { from: Math.floor(Date.now() / 1000) - 3600 }).catch(() => null)]);
  ctx.badge(plants);
  if (!plants.length) return empty(el);
  const st = plants.map((p) => [p, stateOf(p)]);
  const dry = st.filter(([, s]) => s.key === 'dry');
  const crit = alerts.filter((a) => a.level !== 'info' && a.kind !== 'needs_water');
  const okN = st.filter(([, s]) => s.key === 'ok' || s.key === 'wet').length;
  const next = plants.filter((p) => p.forecast && p.forecast.state === 'ok').sort((a, b) => a.forecast.days - b.forecast.days)[0];

  const hour = new Date().getHours();
  const greet = hour < 11 ? 'Guten Morgen' : hour < 17 ? 'Guten Tag' : 'Guten Abend';
  const today = new Date().toLocaleDateString('de-CH', { weekday: 'long', day: 'numeric', month: 'long' });
  let title;
  let mood;
  if (dry.length) {
    title = [h('em', null, `${dry.length} ${plural(dry.length, 'Pflanze', 'Pflanzen')}`), ` ${plural(dry.length, 'hat', 'haben')} Durst`];
    mood = 'thirsty';
  } else if (crit.length) {
    title = ['Alles feucht, ', h('em', null, `${crit.length} ${plural(crit.length, 'Hinweis', 'Hinweise')}`)];
    mood = 'ok';
  } else {
    title = ['Alle Pflanzen sind ', h('em', null, 'zufrieden')];
    mood = 'happy';
  }
  const sub = [];
  if (dry.length) sub.push(`${dry.map(([p]) => p.name).join(', ')} jetzt giessen`);
  if (next) sub.push(`als Nächstes ${next.name} ${next.forecast.days < 1.5 ? 'morgen' : `in ~${Math.round(next.forecast.days)} Tagen`}`);
  const avg = Math.round(plants.filter((p) => p.latest && p.latest.moisture_pct != null).reduce((a, p, _, arr) => a + p.latest.moisture_pct / arr.length, 0));

  const hero = h('section.card.hero', null,
    h('div.hero-deco', { 'aria-hidden': 'true' }, plantArt('monstera', { sensor: false, size: 230 })),
    h('div.hero-drop', null, dropChar(mood, { pct: avg, state: dry.length ? 'dry' : 'ok', size: 104, label: 'Gesamtzustand' })),
    h('div.hero-text', null,
      h('p.kicker', null, `${greet} · ${today}`),
      h('h1.hero-h', null, title),
      h('p.hero-sub', null, sub.join(' · ') || 'Nichts zu tun.'),
      h('div.chips', null,
        h('span.chip.k-dry', null, icon('drop'), `${dry.length} giessen`),
        h('span.chip.k-alert', null, icon('alert'), `${crit.length} ${plural(crit.length, 'Hinweis', 'Hinweise')}`),
        h('span.chip.k-ok', null, icon('check'), `${okN} zufrieden`),
        climate && climate.latest ? h('span.chip', { title: 'Raumklima am Gateway' }, icon('thermo'), `${fmt.n1(climate.latest.temp_c)} °C · ${fmt.n0(climate.latest.rh_pct)} % rF`) : null)));

  const alertList = h('section.card.alerts', null,
    h('div.card-head', null, h('h2.card-title', null, icon('bell'), 'Hinweise'), h('span.count', null, String(alerts.length))),
    h('ul.alist', null, alerts.slice(0, 4).map((a) => h(`li.al.l-${a.level}`, null,
      h('a', { href: `#/pflanze/${a.plant_id}` }, icon(a.level === 'critical' ? 'alert' : a.kind === 'needs_water' ? 'drop' : a.kind === 'battery_low' ? 'battery' : a.kind === 'weak_signal' ? 'wifi' : a.kind === 'salt' ? 'flask' : 'clock'),
        h('span.al-t', null, a.text), h('span.al-s', null, fmt.ago(a.since)), icon('chev', 'chev'))))));

  let filter = 'all';
  const grid = h('div.grid');
  const draw = () => {
    const order = { dry: 0, alert: 1, stale: 2, wet: 3, ok: 4, none: 5 };
    const hint = (p, s) => ['alert', 'stale', 'none'].includes(s.key) || (p.battery && p.battery.state !== 'ok') || (p.signal && p.signal.quality <= 1);
    const list = st.filter(([p, s]) => filter === 'all' || (filter === 'dry' ? s.key === 'dry' : hint(p, s)))
      .sort((a, b) => order[a[1].key] - order[b[1].key] || (a[0].forecast?.days ?? 99) - (b[0].forecast?.days ?? 99));
    fill(grid, ...list.map(([p]) => plantCard(p, ctx)));
  };
  draw();
  el.append(
    h('div.home-top', null, hero, alerts.length ? alertList : null),
    h('div.sec-head', null, h('h2.sec-title', null, 'Pflanzen ', h('span.count', null, String(plants.length))),
      seg([['all', 'Alle'], ['dry', 'Durst'], ['hint', 'Hinweise']], filter, (v) => { filter = v; draw(); }, 'Filter'),
      h('a.btn.ghost.sm', { href: '#/neu', 'aria-label': 'Pflanze hinzufügen' }, icon('plus'), h('span.lbl', null, 'Pflanze'))),
    grid);
}

function empty(el) {
  el.append(h('section.card.hero.empty-hero', null,
    h('div.hero-drop', null, dropChar('happy', { pct: 70, state: 'ok', size: 110, label: 'fluidi' })),
    h('div.hero-text', null, h('p.kicker', null, 'Willkommen bei fluidi'), h('h1.hero-h', null, 'Noch keine ', h('em', null, 'Pflanzen')),
      h('p.hero-sub', null, 'Koppel deinen ersten Sensor: Batterie einsetzen, Taste 3 s drücken, hier bestätigen.'),
      h('div.actions', null, h('a.btn.primary', { href: '#/koppeln' }, icon('plus'), 'Sensor koppeln'), h('a.btn.ghost', { href: '#/neu' }, 'Pflanze ohne Sensor')))));
  return null;
}
