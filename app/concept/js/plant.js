// Pflanzen-Detail: Zustand, Prognose, Verlauf, Tagebuch, Profil, Sensor.
import { h, fmt, toast, sheet } from './dom.js';
import { icon, dropChar, plantArt, batteryIcon, signalIcon, MOOD_TEXT } from './art.js';
import { stateOf, stateBadge, rangeBar, fcText, waterNow, seg, card } from './comp.js';
import { moistureChart } from './chart.js';

const DAY = 86400;
const RANGES = { tag: [DAY, 'Tag'], woche: [7 * DAY, 'Woche'], monat: [30 * DAY, 'Monat'], jahr: [365 * DAY, 'Jahr'] };
const SUB = { erde: 'Blumenerde', granulat: 'Granulat / Seramis' };
const MAT = { kunststoff: 'Kunststoff', ton: 'Ton', keramik: 'Keramik', andere: 'anderes' };
const JT = { watering: ['drop', 'Gegossen'], fertilizing: ['sprout', 'Gedüngt'], repotting: ['pot', 'Umgetopft'], note: ['note', 'Notiz'], sensor_change: ['link', 'Sensor zugeordnet'], calibration: ['target', 'Kalibriert'] };

export default async function plant(el, ctx) {
  const id = Number(ctx.match[1]);
  const [p, fc, journal] = await Promise.all([ctx.api.get(`/plants/${id}`), ctx.api.get(`/plants/${id}/forecast`), ctx.api.get(`/plants/${id}/journal?limit=60`)]);
  const sensor = p.sensor_id ? await ctx.api.get(`/sensors/${p.sensor_id}`) : null;
  const st = stateOf(p);
  const L = p.latest;
  const m = L && L.moisture_pct;
  const sp = ctx.species.find((x) => x.key === p.species);

  // ---------- Kopf
  el.append(h('header.ph.ph-detail', null,
    h('a.iconbtn', { href: '#/', 'aria-label': 'Zurück' }, icon('back')),
    h('div.ph-text', null, h('p.kicker', null, [sp && sp.name, p.location].filter(Boolean).join(' · ')), h('h1', null, p.name)),
    h('a.iconbtn', { href: `#/pflanze/${id}/profil`, 'aria-label': 'Profil bearbeiten' }, icon('edit'))));

  // ---------- Held
  const measureBtn = h('button.btn.ghost', { type: 'button', disabled: !p.sensor_id, onclick: () => measure(ctx, p, measureBtn) }, icon('pulse'), 'Jetzt messen');
  const hero = h('section.card.phero', null,
    h('div.phero-art', null, plantArt(p.species, { state: st.drop, size: 200, label: sp ? sp.name : 'Pflanze' })),
    h('div.phero-info', null,
      h('div.phero-top', null,
        dropChar(p.mood, { pct: m, state: st.drop, size: 78 }),
        h('div', null, h('div.pc-val.xl', null, h('span.big', null, m == null ? '–' : fmt.pct(m)), h('span.unit', null, m == null ? '' : '%')),
          stateBadge(st), h('p.mood', null, `Stimmung: ${MOOD_TEXT[p.mood]}`))),
      rangeBar(m, p.threshold_pct, p.upper_pct, 'lg'),
      h('div.range-lab', null, h('span', null, '0 %'), h('span', null, `Zielbereich ${p.threshold_pct}–${p.upper_pct ?? 100} %`), h('span', null, '100 %')),
      h('dl.facts', null,
        h('div', null, h('dt', null, icon('thermo'), 'Temperatur'), h('dd', null, L ? fmt.temp(L.temp_c) + 'C' : '–')),
        h('div', null, h('dt', null, icon('clock'), 'Gemessen'), h('dd', null, L ? fmt.ago(L.t) : '–')),
        h('div', null, h('dt', null, icon('drop'), 'Gegossen'), h('dd', null, p.last_watered ? fmt.ago(p.last_watered) : '–'))),
      h('div.actions', null,
        h('button.btn.primary.water', { type: 'button', onclick: (ev) => waterNow(p, ctx, ev.currentTarget) }, icon('drop'), 'Gegossen'),
        measureBtn,
        h('a.btn.ghost', { href: `/#/pflanze/${id}/kalibrieren` }, icon('target'), 'Kalibrieren'))));

  // ---------- Prognose
  const fcCard = h('section.card.fcard', null, h('h2.card-title', null, icon('calendar'), 'Nächstes Giessen'));
  if (fc.state === 'ok') {
    const when = new Date(fc.next_water);
    fcCard.append(
      h('p.fc-big', null, fc.days < 1.5 ? (fc.days < 0.5 ? 'heute' : 'morgen') : when.toLocaleDateString('de-CH', { weekday: 'long' })),
      h('p.fc-sub', null, `${fcText(fc)} · etwa ${when.toLocaleDateString('de-CH', { day: 'numeric', month: 'long' })}`),
      h(`span.pill.conf-${fc.confidence}`, null, `Sicherheit: ${{ high: 'hoch', medium: 'mittel', low: 'tief' }[fc.confidence]}`));
  } else {
    fcCard.append(h('p.fc-big', null, fc.state === 'due' ? 'jetzt' : '–'), h('p.fc-sub', null, fc.explanation));
  }
  if (fc.cycles && fc.cycles.length) {
    const maxk = Math.max(...fc.cycles.map((c) => c.k_per_day));
    fcCard.append(h('details.explain', null, h('summary', null, 'Wie rechnet fluidi?'),
      h('p', null, fc.state === 'ok' ? fc.explanation : 'Modell: exponentielle Austrocknung je Giesszyklus.'),
      h('div.kbars', { role: 'img', 'aria-label': 'Austrocknungsrate der letzten Zyklen' }, fc.cycles.map((c) => {
        const b = h(`span.kbar${c.current ? '.cur' : ''}`, { title: `${fmt.date(c.start)}: ${(100 * (1 - Math.exp(-c.k_per_day))).toFixed(0)} %/Tag` });
        b.style.height = `${(c.k_per_day / maxk) * 100}%`;
        return b;
      })),
      h('p.small.muted', null, 'Säulen: Austrocknung je Zyklus (zuletzt rechts). Grosse Unterschiede = tiefere Sicherheit.')));
  }

  // ---------- Verlauf
  let range = ctx.params.bereich in RANGES ? ctx.params.bereich : 'woche';
  const chartBox = h('div.chartbox');
  const drawChart = async () => {
    const to = Math.floor(Date.now() / 1000);
    const from = to - RANGES[range][0];
    const series = await ctx.api.get(`/plants/${id}/series?from=${from}&to=${to}`);
    const w = chartBox.clientWidth || 600;
    chartBox.replaceChildren(moistureChart({ series, forecast: range === 'woche' || range === 'tag' ? fc : null, lo: p.threshold_pct, hi: p.upper_pct, from, to, width: w, height: w < 500 ? 200 : 240 }));
  };
  const chartCard = h('section.card.chartcard', null,
    h('div.card-head', null, h('h2.card-title', null, icon('stats'), 'Verlauf'),
      seg(Object.entries(RANGES).map(([k, [, t]]) => [k, t]), range, (v) => { range = v; drawChart(); }, 'Zeitraum')),
    chartBox,
    h('div.legend', null, h('span.lg-band', null, 'Zielbereich'), h('span.lg-thr', null, 'Giessschwelle'), h('span.lg-water', null, 'gegossen'), h('span.lg-fc', null, 'Prognose')));

  // ---------- Tagebuch
  const recent = Date.now() - 14 * DAY * 1000;
  const jList = h('ul.jlist', null, journal.slice(0, 7).map((e) => {
    const [ic, title] = JT[e.type] || ['note', e.type];
    let src = '';
    if (e.type === 'watering') {
      if (e.source === 'button') src = e.sensor_confirmed ? `per Knopf · Sensor bestätigt +${fmt.pct(e.delta_pct)} %` : 'per Knopf · Sensor noch ohne Sprung';
      else if (e.source === 'sensor') src = `vom Sensor erkannt · ${fmt.pct(e.before_pct)} → ${fmt.pct(e.after_pct)} %`;
      if (e.amount_ml) src += ` · ${e.amount_ml} ml`;
    } else src = e.note || '';
    const ask = e.source === 'sensor' && e.status === 'unconfirmed' && Date.parse(e.t) > recent;
    return h(`li.je.t-${e.type}${ask ? '.ask' : ''}`, null,
      h('span.je-ic', null, icon(ic)),
      h('div.je-txt', null, h('div.je-t', null, title, e.uncertain_time ? h('span.pill', null, 'Zeit unsicher') : null), h('div.je-s', null, src)),
      h('time.je-d', { datetime: e.t }, fmt.date(e.t)),
      ask ? h('div.je-ask', null,
        h('button.btn.sm.primary', { type: 'button', onclick: () => jset(ctx, e, 'confirmed') }, icon('check'), 'Stimmt'),
        h('button.btn.sm.ghost', { type: 'button', onclick: () => jset(ctx, e, 'rejected') }, icon('x'), 'War nicht gegossen')) : null);
  }));
  const jCard = h('section.card.jcard', null,
    h('div.card-head', null, h('h2.card-title', null, icon('note'), 'Tagebuch'),
      h('button.btn.ghost.sm', { type: 'button', onclick: () => addEntry(ctx, p) }, icon('plus'), 'Eintrag')),
    jList,
    h('p.small.muted', null, 'Giessungen erkennt fluidi auch selbst am Feuchtesprung (≥ 15 %-Punkte). Erkannte Einträge kannst du bestätigen oder verwerfen.'));

  // ---------- Profil + Sensor
  const sameAsStart = sp && sp.start_range.lower_pct === p.threshold_pct && sp.start_range.upper_pct === p.upper_pct;
  const prof = card('Profil',
    h('dl.kv', null,
      kv('Art', sp ? `${sp.name}${sp.latin ? ` (${sp.latin})` : ''}` : '–'),
      kv('Substrat', SUB[p.substrate]),
      kv('Topf', p.pot && p.pot.diameter_cm ? `${p.pot.diameter_cm} cm, ${MAT[p.pot.material] || ''}${p.pot.drainage ? ', mit Abzugsloch' : ''}` : '–'),
      kv('Standort', p.location || '–'),
      kv('Zielbereich', h('span', null, `${p.threshold_pct}–${p.upper_pct ?? 100} %`, sameAsStart ? h('span.pill.start', { title: sp.note }, 'Startwert') : h('span.pill', null, 'eigener Wert'))),
      p.notes ? kv('Notiz', p.notes) : null),
    h('a.btn.ghost.sm', { href: `#/pflanze/${id}/profil` }, icon('edit'), 'Profil bearbeiten'));
  const sens = sensor ? card('Sensor',
    h('dl.kv', null,
      kv('Kennung', sensor.id),
      kv('Batterie', h('span.inl', null, batteryIcon(sensor.battery.pct, sensor.battery.state !== 'ok'), `${sensor.battery.pct} % · ${fmt.n1(sensor.battery.mv / 1000)} V · noch ca. ${sensor.battery.days_left} Tage`)),
      kv('Funk', h('span.inl', null, signalIcon(sensor.signal.quality), `${sensor.signal.rssi_dbm} dBm`)),
      kv('Kalibrierung', p.calibration === 'calibrated' ? 'kalibriert (2 Punkte)' : 'Startkalibrierung'),
      kv('Firmware', sensor.fw_version),
      kv('Zuletzt gesehen', fmt.ago(sensor.last_seen))),
    h('button.btn.ghost.sm', { type: 'button', onclick: () => identify(ctx, sensor.id) }, icon('sparkle'), 'Sensor finden (LED blinkt)')) : card('Sensor', h('p.muted', null, 'Kein Sensor zugeordnet.'), h('a.btn.ghost.sm', { href: '/#/koppeln' }, icon('plus'), 'Sensor koppeln'));

  el.append(h('div.detail', null, h('div.col-a', null, hero, chartCard, jCard), h('div.col-b', null, fcCard, prof, sens)));
  requestAnimationFrame(drawChart);
  let t = null;
  const onResize = () => { clearTimeout(t); t = setTimeout(drawChart, 150); };
  window.addEventListener('resize', onResize);
  const off = ctx.live.on('journal', (d) => { if (d.plant_id === id) ctx.refresh(); });
  return { cleanup() { window.removeEventListener('resize', onResize); off(); } };
}

const kv = (k, v) => h('div', null, h('dt', null, k), h('dd', null, v));

async function jset(ctx, e, status) {
  try {
    await ctx.api.patch(`/journal/${encodeURIComponent(e.id)}`, { status });
    toast(status === 'confirmed' ? 'Bestätigt – zählt fürs Lernen der Prognose' : 'Verworfen', 'ok');
    ctx.refresh();
  } catch (err) { toast(err.message, 'err'); }
}

async function addEntry(ctx, p) {
  const type = await sheet((close) => h('div.stack', null, h('h2', null, `Eintrag für ${p.name}`),
    h('div.pick', null, ['watering', 'fertilizing', 'repotting', 'note'].map((t) => h('button.pick-i', { type: 'button', onclick: () => close(t) }, icon(JT[t][0]), h('span.pick-n', null, JT[t][1]))))));
  if (!type) return;
  try {
    await ctx.api.post(`/plants/${p.id}/journal`, { type, note: type === 'note' ? 'Notiz aus dem Entwurf' : '' });
    toast(`${JT[type][1]} eingetragen`, 'ok');
    ctx.refresh();
  } catch (e) { toast(e.message, 'err'); }
}

async function measure(ctx, p, btn) {
  btn.disabled = true;
  btn.classList.add('busy');
  try {
    let j = await ctx.api.post(`/plants/${p.id}/measure`);
    while (['queued', 'waiting_for_sensor', 'running'].includes(j.state)) {
      btn.lastChild.textContent = j.state === 'running' ? 'misst …' : 'warte auf Sensor …';
      await new Promise((r) => setTimeout(r, 1000));
      j = await ctx.api.get(`/jobs/${j.id}`);
    }
    toast(j.state === 'done' ? 'Neuer Messwert' : j.message, j.state === 'done' ? 'ok' : 'err');
    ctx.refresh();
  } catch (e) {
    toast(e.message, 'err');
  } finally {
    btn.disabled = false;
    btn.classList.remove('busy');
  }
}

async function identify(ctx, sid) {
  try {
    await ctx.api.post(`/sensors/${sid}/identify`);
    toast('Der Sensor blinkt beim nächsten Kontakt', 'ok');
  } catch (e) { toast(e.message, 'err'); }
}
