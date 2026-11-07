// Statistik und Sensoren: Giessungen, Zeit im Zielbereich, Batterie, Energie, Funk, Datenzugang.
import { h, fmt, fill } from './dom.js';
import { icon, batteryIcon, signalIcon } from './art.js';
import { pageHead, card } from './comp.js';
import { bars, spark, climateChart } from './chart.js';

const PARTS = [['sleep', 'Schlaf'], ['advertising', 'Funk-Bereitschaft'], ['sessions', 'Übertragung'], ['measure', 'Messen'], ['led', 'LED']];

export default async function stats(el, ctx) {
  const [st, plants, cl] = await Promise.all([ctx.api.get('/stats', { days: 90 }), ctx.api.get('/plants'), ctx.api.get('/climate').catch(() => null)]);
  const name = (id) => (plants.find((p) => p.id === id) || {}).name || '–';
  const S = st.summary;
  const kpi = (ic, val, unit, lab) => h('div.kpi', null, h('span.kpi-ic', null, icon(ic)), h('div.kpi-v', null, val, h('small', null, unit)), h('div.kpi-l', null, lab));
  el.append(pageHead('Statistik', 'Letzte 90 Tage'),
    h('div.kpis', null,
      kpi('drop', fmt.n0(S.waterings), '', 'Giessungen'),
      kpi('calendar', fmt.n1(S.avg_interval_days), ' Tage', 'Ø Abstand'),
      kpi('target', fmt.n0(S.time_in_range_pct), ' %', 'Zeit im Zielbereich (30 T.)'),
      kpi('wifi', `${S.sensors_online}/${S.sensors}`, '', 'Sensoren online')));

  const barBox = h('div.chartbox');
  const wk = st.waterings_per_week;
  const drawBars = () => fill(barBox, bars(wk.map((w) => w.count), wk.map((w, i) => (i % 2 === wk.length % 2 ? '' : `KW${kw(w.week_start)}`)), { width: barBox.clientWidth || 500, height: 150 }));

  const plantRows = st.plants.filter((p) => p.waterings || p.time_in_range_pct != null).sort((a, b) => (b.time_in_range_pct ?? -1) - (a.time_in_range_pct ?? -1)).map((p) => {
    const bar = h('span.tir-fill');
    bar.style.width = `${p.time_in_range_pct ?? 0}%`;
    return h('tr', null, h('td', null, h('a', { href: `#/pflanze/${p.plant_id}` }, p.name)), h('td.num', null, String(p.waterings)),
      h('td.num', null, p.avg_interval_days ? `${fmt.n1(p.avg_interval_days)} T.` : '–'),
      h('td.tirc', null, h('span.tir', { role: 'img', 'aria-label': `${p.time_in_range_pct} %` }, bar), h('span.num', null, p.time_in_range_pct == null ? '–' : `${fmt.n0(p.time_in_range_pct)} %`)));
  });

  const maxMc = Math.max(1, ...st.sensors.map((x) => x.energy.total_mc_per_day));
  const sensRows = st.sensors.map((x) => {
    const b = x.battery;
    const stack = h('div.estack', { role: 'img', 'aria-label': `Energie ${x.energy.avg_ua} µA im Mittel` });
    if (!b) return null;
    for (const [k] of PARTS) {
      const seg = h(`span.es-${k}`);
      seg.style.width = `${(x.energy.mc_per_day[k] / maxMc) * 100}%`;
      stack.append(seg);
    }
    return h(`div.srow${b.state !== 'ok' ? '.warn' : ''}`, null,
      h('div.sr-name', null, h('strong', null, name(x.plant_id)), h('span.small.muted', null, x.sensor_id)),
      h('div.sr-batt', null, batteryIcon(b.pct, b.state !== 'ok'), h('span', null, `${b.pct} %`), h('span.small.muted', null, `${fmt.n1(b.mv / 1000)} V · ~${b.days_left} T.`)),
      h('div.sr-spark', null, spark(x.battery_history.mv, { width: 110, height: 30, min: 2500, max: 3050 })),
      h('div.sr-energy', null, stack, h('span.small.muted', null, `Ø ${fmt.n1(x.energy.avg_ua)} µA · ${fmt.n0(x.energy.mah_per_year)} mAh/Jahr`)),
      h('div.sr-radio', null, signalIcon(x.radio.quality), h('span.small', null, `${x.radio.rssi_dbm} dBm`), h('span.small.muted', null, `${fmt.n1(x.radio.missed_pct)} % verpasst`)));
  });

  const to = Math.floor(Date.now() / 1000);
  el.append(
    h('div.statgrid', null,
      card('Giessungen pro Woche', barBox, h('p.small.muted', null, 'Erkannt am Feuchtesprung oder per Knopf „gegossen“.')),
      card('Zeit im Zielbereich', h('table.tbl', null, h('thead', null, h('tr', null, h('th', null, 'Pflanze'), h('th.num', null, 'Giessungen'), h('th.num', null, 'Ø Abstand'), h('th', null, '30 Tage im Bereich'))), h('tbody', null, plantRows)))),
    card('Sensoren & Akku',
      h('div.slist', null, sensRows),
      h('div.elegend', null, PARTS.map(([k, t]) => h('span', null, h(`i.es-${k}`), t))),
      h('p.small.muted', null, `Energie: Schätzung aus der Ereigniszählung des Sensors × Ladung je Ereignis (Funkprotokoll Kap. 12), keine Messung. Zelle ${st.sensors[0] ? st.sensors[0].energy.cell : ''}, ${st.sensors[0] ? st.sensors[0].energy.capacity_mah : ''} mAh.`)),
    card('Daten für Auswertungen',
      h('p', null, 'Alle Rohwerte bleiben auf dem Gateway (SQLite). Für Analysen und ML:'),
      h('div.actions', null,
        h('a.btn.ghost', { href: `/api/v1/export.csv?from=${to - 365 * 86400}&to=${to}&res=raw` }, icon('download'), 'CSV (Rohwerte, 1 Jahr)'),
        h('a.btn.ghost', { href: `/api/v1/export.csv?from=${to - 365 * 86400}&to=${to}&res=day&decimal=comma` }, icon('download'), 'CSV (Tagesmittel, Excel)'),
        h('a.btn.ghost', { href: '#/daten' }, icon('download'), 'Weitere Formate & Backup')),
      h('p.small.muted', null, 'Lese-API: /api/v1/plants/{id}/series, /stats, /plants/{id}/journal – dokumentiert in openapi.yaml.')));
  const clBox = h('div.chartbox');
  const drawCl = () => { if (cl && cl.t.length) fill(clBox, climateChart(cl, { width: clBox.clientWidth || 500, height: 170 })); };
  if (cl && cl.source !== 'off') el.append(card('Raumklima am Gateway (7 Tage)', clBox,
    h('p.small.muted', null, cl.latest ? `Jetzt ${fmt.n1(cl.latest.temp_c)} °C, ${fmt.n0(cl.latest.rh_pct)} % rF · Sensor SHT4x im Gateway (D-017). Trockene Heizungsluft lässt Töpfe schneller austrocknen.` : 'Noch keine Werte.')));
  requestAnimationFrame(() => { drawBars(); drawCl(); });
  const onR = () => { drawBars(); drawCl(); };
  window.addEventListener('resize', onR);
  return { cleanup() { window.removeEventListener('resize', onR); } };
}

function kw(iso) {
  const d = new Date(Date.parse(iso) + 86400000);
  const t = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
  t.setUTCDate(t.getUTCDate() + 4 - (t.getUTCDay() || 7));
  return Math.ceil(((t - new Date(Date.UTC(t.getUTCFullYear(), 0, 1))) / 86400000 + 1) / 7);
}
