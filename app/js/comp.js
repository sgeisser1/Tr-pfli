// fluidi – gemeinsame Bausteine (Zustand, Karten, Bereichsbalken, Giessen-Aktion).
import { h, fmt, toast } from './dom.js';
import { icon, dropChar, plantArt, batteryIcon, signalIcon, MOOD_TEXT } from './art.js';

/** Zustand einer Pflanze: immer Symbol + Text + Farbe (nicht nur Farbe, Barrierefreiheit). */
export function stateOf(p) {
  const L = p.latest;
  if (!p.sensor_id) return { key: 'none', drop: 'none', text: 'Kein Sensor', ic: 'info' };
  if (!L) return { key: 'none', drop: 'none', text: 'Noch kein Wert', ic: 'clock' };
  if (p.status.stale) return { key: 'stale', drop: 'stale', text: 'Keine neuen Werte', ic: 'clock' };
  const st = L.moisture_state;
  if (st === 'air') return { key: 'alert', drop: 'air', text: 'Sensor nicht in der Erde?', ic: 'alert' };
  if (st === 'flooded') return { key: 'alert', drop: 'flooded', text: 'Zu nass / überflutet?', ic: 'alert' };
  if (st === 'invalid' || st === 'uncalibrated') return { key: 'alert', drop: 'invalid', text: 'Kalibrierung prüfen', ic: 'alert' };
  if (st === 'dry') return { key: 'dry', drop: 'dry', text: 'Giessen nötig', ic: 'drop' };
  // „zu nass“ erst 48 h nach der letzten Giessung (D-021), das Gateway liefert care.too_wet
  if (p.care ? p.care.too_wet : p.upper_pct != null && L.moisture_pct > p.upper_pct) return { key: 'wet', drop: 'ok', text: 'Zu nass seit über 48 h', ic: 'info' };
  if (p.care && p.care.phase === 'dry_phase') return { key: 'ok', drop: 'ok', text: 'Trockenphase', ic: 'check' };
  return { key: 'ok', drop: 'ok', text: 'Feucht genug', ic: 'check' };
}

export function stateBadge(st) {
  return h(`span.badge.b-${st.key}`, null, icon(st.ic), st.text);
}

export function fcText(fc, short = false) {
  if (!fc) return '–';
  if (fc.state === 'due') return 'jetzt giessen';
  if (fc.state === 'insufficient_data') return short ? 'Prognose lernt' : 'Prognose lernt noch';
  if (fc.state !== 'ok') return 'keine Prognose';
  const d = fc.days;
  const base = d < 0.5 ? 'heute giessen' : d < 1.5 ? 'morgen giessen' : `giessen in ~${Math.round(d)} Tagen`;
  if (short) return base;
  const lo = Math.round(fc.days_low);
  const hi = Math.round(fc.days_high);
  return hi > lo && d >= 1.5 ? `${base} (${lo}–${hi})` : base;
}

/** Balken 0–100 % mit Zielbereich und Marke für den aktuellen Wert. */
export function rangeBar(m, lo, hi, cls = '') {
  const bar = h(`div.range${cls ? '.' + cls : ''}`, { role: 'img', 'aria-label': `Feuchte ${fmt.pct(m)} %, Zielbereich ${lo}–${hi ?? 100} %` });
  const band = h('span.range-band');
  band.style.left = `${lo}%`;
  band.style.width = `${(hi ?? 100) - lo}%`;
  bar.append(band);
  if (m != null) {
    const fill = h('span.range-fill');
    fill.style.width = `${Math.max(0, Math.min(100, m))}%`;
    const mark = h('span.range-mark');
    mark.style.left = `${Math.max(0, Math.min(100, m))}%`;
    bar.append(fill, mark);
  }
  return bar;
}

export function plantCard(p, ctx) {
  const st = stateOf(p);
  const L = p.latest;
  const m = L && L.moisture_pct;
  const sp = ctx.speciesName(p.species);
  const go = () => ctx.go(`/pflanze/${p.id}`);
  const meta = [];
  if (L) meta.push(h('span.meta-i', { title: 'Temperatur' }, icon('thermo'), fmt.temp(L.temp_c)));
  if (L) meta.push(h('span.meta-i', { title: fmt.dateTime(L.t) }, icon('clock'), fmt.ago(L.t)));
  if (p.battery && p.battery.state !== 'ok') meta.push(h('span.meta-i.warn', { title: `Batterie ${p.battery.pct} %` }, batteryIcon(p.battery.pct, true), `${p.battery.days_left} T.`));
  else if (p.battery) meta.push(h('span.meta-i', { title: `Batterie ${p.battery.pct} %` }, batteryIcon(p.battery.pct), `${p.battery.pct} %`));
  if (p.signal && p.signal.quality <= 1) meta.push(h('span.meta-i.warn', { title: `Signal ${p.signal.rssi_dbm} dBm` }, signalIcon(p.signal.quality), 'schwach'));
  const card = h(`div.card.pcard.k-${st.key}`, { 'data-id': p.id, onclick: (ev) => { if (!ev.target.closest('button,a')) go(); } },
    h('div.pc-art', null, plantArt((ctx.species.find((x) => x.key === p.species) || {}).illustration || p.species, { state: st.drop, size: 104, label: sp })),
    h('div.pc-main', null,
      h('div.pc-top', null,
        h('div.pc-name', null, h('a.pc-title', { href: `#/pflanze/${p.id}` }, p.name), h('div.pc-sub', null, [sp, p.location].filter(Boolean).join(' · '))),
        dropChar(p.mood, { pct: m, state: st.drop, size: 46 })),
      h('div.pc-val', null, h('span.big', null, m == null ? '–' : fmt.pct(m)), h('span.unit', null, m == null ? '' : '%'), stateBadge(st)),
      rangeBar(m, p.threshold_pct, p.upper_pct),
      h('div.pc-foot', null,
        h(`span.fc.fc-${p.forecast ? p.forecast.state : 'none'}`, null, icon(st.key === 'dry' ? 'drop' : 'calendar'), st.key === 'stale' || st.key === 'alert' ? h('span', null, MOOD_TEXT[p.mood]) : fcText(p.forecast, true)),
        h('span.meta', null, meta))),
    st.key === 'dry' ? h('button.btn.water.sm', { type: 'button', onclick: (ev) => waterNow(p, ctx, ev.currentTarget) }, icon('drop'), 'Gegossen') : null);
  return card;
}

/** Knopf „gegossen“: Eintrag ins Tagebuch; das Gateway fordert danach eine Messung an (Konzept 6.4). */
export async function waterNow(p, ctx, btn) {
  if (btn) {
    btn.disabled = true;
    btn.classList.add('splash');
  }
  try {
    await ctx.api.post(`/plants/${p.id}/journal`, { type: 'watering' });
    toast(h('span', null, icon('drop'), ` ${p.name}: gegossen eingetragen. Der Sensor bestätigt gleich.`), 'ok');
    if (p.care && p.care.regime === 'A' && p.latest && p.latest.moisture_pct > p.care.effective_threshold_pct + 15) setTimeout(() => toast('Früher gegossen als das Profil vorsieht – diese Art mag zwischendurch trocken stehen.'), 3400);
    setTimeout(() => ctx.refresh(), 3200);
  } catch (e) {
    toast(e.message, 'err');
    if (btn) btn.disabled = false;
  }
}

export function pageHead(title, sub, ...actions) {
  return h('header.ph', null, h('div.ph-text', null, sub ? h('p.kicker', null, sub) : null, h('h1', null, title)), actions.length ? h('div.ph-act', null, actions) : null);
}

export function seg(options, value, onChange, label) {
  const g = h('div.seg', { role: 'radiogroup', 'aria-label': label || '' });
  for (const [v, text, ic] of options) {
    const b = h('button', { type: 'button', role: 'radio', 'aria-checked': String(v === value), class: v === value ? 'on' : '' }, ic ? icon(ic) : null, text);
    b.addEventListener('click', () => {
      for (const x of g.children) { x.classList.remove('on'); x.setAttribute('aria-checked', 'false'); }
      b.classList.add('on');
      b.setAttribute('aria-checked', 'true');
      onChange(v);
    });
    g.append(b);
  }
  return g;
}

export function toggle(checked, onChange, label) {
  const inp = h('input', { type: 'checkbox', role: 'switch', checked, 'aria-label': label });
  inp.addEventListener('change', () => onChange(inp.checked, inp));
  return h('label.switch', null, inp, h('span.knob', { 'aria-hidden': 'true' }));
}

export function card(title, ...children) {
  return h('section.card', null, title ? h('h2.card-title', null, title) : null, children);
}
