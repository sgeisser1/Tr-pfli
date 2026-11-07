// Detail einer Pflanze: aktueller Wert, „Jetzt messen“, Verlauf Tag/Woche/Monat/Jahr (REQ-APP-04, -06).
import { h, drop, batteryIcon, signalIcon, fmt, SUBSTRATE, STATE_TEXT, toast } from '../ui.js';
import { dropColor, relativeTime } from '../calc.js';
import { renderChart } from '../chart.js';
import { watchJob } from '../api.js';

const RANGES = [
  ['tag', 'Tag', 86400],
  ['woche', 'Woche', 7 * 86400],
  ['monat', 'Monat', 30 * 86400],
  ['jahr', 'Jahr', 365 * 86400],
];
const RES_TEXT = { raw: 'Einzelwerte', hour: 'Stundenmittel mit Min/Max', day: 'Tagesmittel mit Min/Max' };
const JOB_TEXT = {
  queued: 'Auftrag angenommen …',
  waiting_for_sensor: 'Warte auf den Sensor (meldet sich innert Reaktionszeit) …',
  running: 'Sensor misst …',
  done: 'Neuer Messwert empfangen.',
  failed: 'Messung fehlgeschlagen.',
  timeout: 'Sensor hat nicht geantwortet.',
  cancelled: 'Abgebrochen.',
};

export default async function detail(main, ctx) {
  const id = Number(ctx.match[1]);
  let plant = await ctx.api.get(`/plants/${id}`);
  let sensor = plant.sensor_id ? await ctx.api.get(`/sensors/${plant.sensor_id}`).catch(() => null) : null;
  let range = ctx.params.bereich || sessionStorage.getItem('fluidi.range') || 'woche';
  if (!RANGES.some((r) => r[0] === range)) range = 'woche';
  let chart = null;

  const head = h('div');
  const info = h('div.card');
  const chartBox = h('div.chart');
  const chartNote = h('p.muted.small');
  const seg = h('div.seg', { role: 'group', 'aria-label': 'Zeitraum' });
  const measureBtn = h('button.primary', { type: 'button' }, 'Jetzt messen');
  const status = h('div.status-line.muted');
  const prog = h('div.progress.hidden', null, h('span'));

  function drawHead() {
    const L = plant.latest;
    const color = dropColor(plant);
    const st = plant.status;
    const stateText = L ? (st.stale ? 'Keine neuen Werte' : STATE_TEXT[L.moisture_state]) : 'Noch kein Messwert';
    const meter = h('div.meter');
    if (L && L.moisture_pct !== null) {
      const f = h('span.fill' + (st.needs_water ? '.low' : ''));
      f.style.width = `${L.moisture_pct}%`;
      meter.append(f);
    }
    const mark = h('span.mark');
    mark.style.left = `calc(${plant.threshold_pct}% - 1px)`;
    meter.append(mark);
    head.replaceChildren(
      h('a.back', { href: '#/' }, '← Pflanzen'),
      h('div.pagehead', null,
        h('div.row', null, drop(color, stateText), h('h1', null, plant.name)),
        h('div.row', null,
          h('a.btn.ghost', { href: `#/pflanze/${id}/bearbeiten` }, 'Bearbeiten'),
          plant.sensor_id ? h('a.btn.ghost', { href: `#/pflanze/${id}/kalibrieren` }, 'Kalibrieren') : null)),
    );
    const nowS = Date.now() / 1000;
    info.replaceChildren(
      h('div.big', null, h('span.val', null, L && L.moisture_pct !== null ? fmt.pct1(L.moisture_pct) : '–'), h('span.unit', null, '%'),
        h('span.temp', null, L ? fmt.temp(L.temp_c) : '')),
      meter,
      h(`p.state${st.needs_water ? '.blue' : ''}${color === 'red' ? '.red' : ''}`, null, stateText,
        L && L.moisture_state === 'air' ? ' Der Wert liegt deutlich unter dem Trockenpunkt.' : '',
        L && L.moisture_state === 'flooded' ? ' Der Wert liegt deutlich über dem Nasspunkt.' : ''),
      h('dl.kv', null,
        h('dt', null, 'Gemessen'), h('dd', null, L ? `${fmt.dateTime(L.t)} (${relativeTime(Date.parse(L.t) / 1000, nowS)})` : '–',
          L && L.time_quality !== 'ok' ? h('span.pill.warn', null, L.time_quality === 'reconstructed' ? ' Zeit rekonstruiert' : ' Zeit unsicher') : null),
        h('dt', null, 'Giessen unter'), h('dd', null, `${plant.threshold_pct} %`),
        h('dt', null, 'Substrat'), h('dd', null, SUBSTRATE[plant.substrate]),
        h('dt', null, 'Kalibrierung'), h('dd', null, { none: '–', default: 'Startkalibrierung (ungenau)', calibrated: 'kalibriert' }[plant.calibration]),
        h('dt', null, 'Rohwert'), h('dd', null, L ? String(L.raw) : '–')),
      plant.sensor_id ? h('div.row', null, measureBtn) : h('p', null, 'Kein Sensor zugeordnet. ', h('a', { href: '#/koppeln' }, 'Sensor koppeln')),
      status, prog);
  }

  function sensorCard() {
    if (!sensor) return null;
    const b = sensor.battery;
    return h('div.card', null, h('h2', null, 'Sensor'),
      h('dl.kv', null,
        h('dt', null, 'Kennung'), h('dd', null, sensor.id),
        h('dt', null, 'Firmware'), h('dd', null, sensor.fw_version),
        h('dt', null, 'Batterie'), h('dd', null, batteryIcon(b), b ? ` ${b.pct} % · ${fmt.mv(b.mv)}${b.days_left != null ? ` · noch ca. ${b.days_left} Tage` : ''}` : '–'),
        h('dt', null, 'Signal'), h('dd', null, signalIcon(sensor.signal), sensor.signal ? ` ${sensor.signal.rssi_dbm} dBm` : '–'),
        h('dt', null, 'Zuletzt gehört'), h('dd', null, fmt.dateTime(sensor.last_seen)),
        h('dt', null, 'Messungen/Tag'), h('dd', null, String(sensor.effective_interval_per_day)),
        sensor.pending_config ? [h('dt', null, 'Änderungen'), h('dd', null, 'werden beim nächsten Kontakt übertragen')] : null),
      b && b.state !== 'ok' ? h('p.err-text', null, 'Batterie bald wechseln (CR2032, Anleitung beachten).') : null,
      h('div.row', null, h('button.ghost', { type: 'button', onclick: identify }, 'LED blinken lassen')));
  }

  async function identify() {
    if (!ctx.requireLogin()) return;
    try {
      const j = await ctx.api.post(`/sensors/${sensor.id}/identify`);
      toast('Der Sensor blinkt beim nächsten Kontakt.');
      watchJob(j, null, ctx.stream);
    } catch (e) {
      toast(e.message, true);
    }
  }

  async function loadChart() {
    for (const b of seg.children) b.setAttribute('aria-pressed', String(b.dataset.r === range));
    const span = RANGES.find((r) => r[0] === range)[2];
    const to = Math.floor(Date.now() / 1000);
    chartNote.textContent = 'Lade Verlauf …';
    try {
      const s = await ctx.api.get(`/plants/${id}/series`, { from: to - span, to, res: 'auto' });
      if (chart) chart.destroy();
      chart = renderChart(chartBox, s);
      chartNote.textContent = s.t.length ? `${RES_TEXT[s.res]} · ${s.t.length} Punkte · gestrichelt: Giessschwelle und Temperatur` : 'Keine Messwerte in diesem Zeitraum.';
    } catch (e) {
      chartNote.textContent = e.message;
    }
  }

  for (const [key, label] of RANGES) {
    seg.append(h('button', { type: 'button', 'data-r': key, onclick: () => { range = key; sessionStorage.setItem('fluidi.range', key); loadChart(); } }, label));
  }

  measureBtn.addEventListener('click', async () => {
    if (!ctx.requireLogin()) return;
    measureBtn.disabled = true;
    prog.classList.remove('hidden');
    prog.classList.add('indet');
    const t0 = Date.now();
    let last = null;
    const tick = setInterval(() => {
      if (last) status.textContent = `${JOB_TEXT[last.state] || last.state} (${Math.round((Date.now() - t0) / 1000)} s)`;
    }, 1000);
    try {
      const job = await ctx.api.post(`/plants/${id}/measure`);
      last = job;
      status.textContent = JOB_TEXT[job.state];
      const fin = await watchJob(job, (j) => { last = j; status.textContent = JOB_TEXT[j.state] || j.message; }, ctx.stream);
      clearInterval(tick);
      if (fin.state === 'done') {
        plant = await ctx.api.get(`/plants/${id}`);
        drawHead();
        const r = fin.result && fin.result.reading;
        status.textContent = r ? `Neuer Wert: ${fmt.pct1(r.moisture_pct)} % nach ${Math.round((Date.now() - t0) / 1000)} s.` : JOB_TEXT.done;
        loadChart();
      } else {
        status.textContent = (fin.message || JOB_TEXT[fin.state]) + ' Bitte später erneut versuchen.';
        status.classList.add('err-text');
      }
    } catch (e) {
      clearInterval(tick);
      status.textContent = e.message;
    } finally {
      measureBtn.disabled = false;
      prog.classList.add('hidden');
    }
  });

  drawHead();
  main.replaceChildren(head,
    h('div.detail-top', null,
      h('div.card', null, h('div.row.between', null, h('h2', null, 'Verlauf'), seg), chartBox, chartNote),
      h('div', null, info, sensorCard())));
  loadChart();

  const off = ctx.stream.on('plant', (p) => {
    if (p.id !== id) return;
    plant = p;
    drawHead();
  });
  return { cleanup() { off(); if (chart) chart.destroy(); } };
}
