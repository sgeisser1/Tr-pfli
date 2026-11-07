// Geführte Zwei-Punkt-Kalibrierung (REQ-APP-07, REQ-MES-09, UC-05, GATEWAY_API 5.2): trocken -> nass -> übernehmen.
// Der Sensor misst je Punkt mehrere Einzelwerte, das Gateway mittelt robust (Ausreisser verworfen, REQ-MES-10).
import { h, toast, fmt, fill } from './dom.js';
import { icon, dropChar, plantArt } from './art.js';
import { seg, card } from './comp.js';
import { watchJob } from './api.js';

const STEPS = [['prep', 'Vorbereiten'], ['dry', 'Trocken'], ['wet', 'Nass'], ['save', 'Übernehmen']];

export default async function calibrate(el, ctx) {
  const id = Number(ctx.match[1]);
  const p = await ctx.api.get(`/plants/${id}`);
  const head = h('header.ph.ph-detail', null, h('a.iconbtn', { href: `#/pflanze/${id}`, 'aria-label': 'Zurück' }, icon('back')),
    h('div.ph-text', null, h('p.kicker', null, p.name), h('h1', null, 'Kalibrieren')));
  if (!p.sensor_id) {
    el.append(head, card(null, h('p', null, 'Dieser Pflanze ist kein Sensor zugeordnet.'), h('a.btn.ghost', { href: '#/koppeln' }, 'Sensor koppeln')));
    return null;
  }
  const sid = p.sensor_id;
  const cals = await ctx.api.get(`/sensors/${sid}/calibration`);
  let substrate = p.substrate;
  let run = null;
  let stepIx = 0;
  const steps = h('ol.steps');
  const body = h('div.stack');
  const setStep = (i) => {
    stepIx = i;
    fill(steps, ...STEPS.map(([, t], k) => h(`li${k === i ? '.cur' : k < i ? '.done' : ''}`, null, h('span.st-n', null, k < i ? '✓' : String(k + 1)), t)));
  };
  const pt = (x) => (x ? `Rohwert ${fmt.n0(x.raw)} (${fmt.n1(x.raw / 100)} pF) · n = ${x.n}${x.stddev != null ? ` · σ ${fmt.n1(x.stddev)}` : ''}${x.temp_c != null ? ` · ${fmt.temp(x.temp_c)}C` : ''}` : '–');

  async function capture(point, btn, msg) {
    btn.disabled = true;
    btn.classList.add('busy');
    try {
      const j = await ctx.api.post(`/calibration-runs/${run.id}/capture`, { point });
      const fin = await watchJob(j, (x) => { msg.textContent = x.state === 'running' ? 'Sensor misst …' : x.message; }, ctx.live);
      run = await ctx.api.get(`/calibration-runs/${run.id}`);
      if (fin.state !== 'done') { msg.textContent = fin.message || 'Messung fehlgeschlagen'; btn.disabled = false; return; }
      if (fin.result && fin.result.outliers) toast(`${fin.result.outliers} Ausreisser verworfen`);
      draw();
    } catch (e) { msg.textContent = e.message; btn.disabled = false; } finally { btn.classList.remove('busy'); }
  }

  function measureStep(point, title, text, art) {
    const msg = h('p.status');
    const btn = h('button.btn.primary', { type: 'button' }, icon('pulse'), `${title} messen`);
    btn.addEventListener('click', () => capture(point, btn, msg));
    return card(title, h('div.cal-art', null, art), h('p', null, text), h('p.small.muted', null, 'Der Sensor misst 5-mal, jeweils nach einem kurzen Funkkontakt (Messung ohne Funk). Dauer bis ca. 1 min.'), msg, h('div.actions', null, btn));
  }

  function draw() {
    if (!run) {
      setStep(0);
      const cur = cals[substrate];
      fill(body, card('Vorbereiten',
        h('p', null, 'fluidi rechnet den Feuchteindex aus zwei Punkten: 0 % = deine trockene Erde, 100 % = frisch durchnässt. So passt die Anzeige zu deinem Substrat.'),
        h('div.field', null, h('span', null, 'Substrat'), seg([['erde', 'Erde'], ['granulat', 'Granulat']], substrate, (v) => { substrate = v; draw(); }, 'Substrat')),
        h('p.small.muted', null, `Aktuell: ${cur.source === 'default' ? 'Startkalibrierung (ANNAHME)' : `kalibriert ${cur.updated ? fmt.date(cur.updated) : ''}`} · trocken ${fmt.n0(cur.dry.raw)} · nass ${fmt.n0(cur.wet.raw)}`),
        h('div.actions', null, h('button.btn.primary', { type: 'button', onclick: async () => { run = await ctx.api.post(`/sensors/${sid}/calibration-runs`, { substrate, samples: 5 }); draw(); } }, 'Start'))));
      return;
    }
    if (run.state === 'await_dry' || (run.state === 'await_wet' && !run.dry)) {
      setStep(1);
      fill(body, measureStep('dry', 'Trocken', 'Sensor bis zur Markierung in trockenes Substrat stecken (z. B. Erde, die mehrere Tage nicht gegossen wurde). Nicht drücken, nicht giessen.', plantArt('generic', { state: 'dry', size: 110 })));
    } else if (run.state === 'await_wet' || (run.state === 'await_dry' && run.dry)) {
      setStep(2);
      fill(body, card('Trocken gemessen', h('p.small', null, pt(run.dry))),
        measureStep('wet', 'Nass', 'Jetzt durchdringend giessen, bis unten Wasser austritt. 10 min warten, dann messen.', dropChar('drowning', { pct: 95, state: 'ok', size: 80 })));
    } else if (run.state === 'ready' || run.state === 'failed') {
      setStep(3);
      const ok = run.state === 'ready';
      fill(body, card(ok ? 'Bereit zum Übernehmen' : 'Spanne zu klein',
        h('dl.kv', null, h('div', null, h('dt', null, 'Trocken'), h('dd', null, pt(run.dry))), h('div', null, h('dt', null, 'Nass'), h('dd', null, pt(run.wet)))),
        ok ? null : h('p.err', null, run.message || 'Trocken- und Nasswert liegen zu nahe beieinander.'),
        h('div.actions', null,
          ok ? h('button.btn.primary', { type: 'button', onclick: async () => {
            try { await ctx.api.post(`/calibration-runs/${run.id}/commit`); toast('Kalibrierung gespeichert – gilt auch rückwirkend', 'ok'); ctx.go(`/pflanze/${id}`); } catch (e) { toast(e.message, 'err'); }
          } }, icon('check'), 'Übernehmen') : null,
          h('button.btn.ghost', { type: 'button', onclick: async () => { run = await ctx.api.post(`/sensors/${sid}/calibration-runs`, { substrate, samples: 5 }); draw(); } }, 'Neu beginnen'))));
    }
  }
  el.append(head, h('section.card', null, steps), body);
  draw();
  return { cleanup() { if (run && !['committed', 'cancelled'].includes(run.state) && stepIx < 3) ctx.api.del(`/calibration-runs/${run.id}`).catch(() => null); } };
}
