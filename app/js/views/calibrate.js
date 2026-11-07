// Geführte Zwei-Punkt-Kalibrierung (REQ-APP-07, REQ-MES-09, UC-05).
import { h, toast, SUBSTRATE, fmt } from '../ui.js';
import { evaluate, spanOk } from '../calc.js';
import { watchJob } from '../api.js';

const STEPS = ['Vorbereiten', 'Trocken', 'Nass', 'Speichern'];

export default async function calibrate(main, ctx) {
  if (!ctx.requireLogin()) return;
  const id = Number(ctx.match[1]);
  const plant = await ctx.api.get(`/plants/${id}`);
  if (!plant.sensor_id) {
    main.replaceChildren(h('div.card', null, h('p', null, 'Dieser Pflanze ist kein Sensor zugeordnet.')));
    return;
  }
  const sid = plant.sensor_id;
  const cals = await ctx.api.get(`/sensors/${sid}/calibration`);
  let run = null;
  let substrate = plant.substrate;
  const body = h('div.card');
  const steps = h('ol.steps');

  function setStep(i) {
    steps.replaceChildren(...STEPS.map((s, k) => h(`li${k === i ? '.cur' : k < i ? '.done' : ''}`, null, `${k + 1}. ${s}`)));
  }

  function pointText(pt) {
    if (!pt) return '–';
    return `Rohwert ${Math.round(pt.raw)} (n = ${pt.n}${pt.stddev != null ? `, σ = ${fmt.pct1(pt.stddev)}` : ''}${pt.temp_c != null ? `, ${fmt.temp(pt.temp_c)}` : ''})`;
  }

  function step0() {
    setStep(0);
    const radios = Object.entries(SUBSTRATE).map(([k, label]) =>
      h('label.check', null, h('input', { type: 'radio', name: 'sub', value: k, checked: k === substrate, onchange: () => (substrate = k) }), label,
        h('span.muted', null, ` – ${cals[k].source === 'default' ? 'Startkalibrierung' : `kalibriert ${fmt.date(cals[k].updated)}`}`)));
    const msg = h('p.err-text.status-line');
    body.replaceChildren(
      h('h2', null, 'Vorbereiten'),
      h('p', null, 'Die Kalibrierung legt fest, welcher Rohwert 0 % (trocken) und welcher 100 % (nass) entspricht. Du brauchst etwa 30 Minuten und einen Becher mit dem gleichen Substrat wie im Topf.'),
      h('ol', null,
        h('li', null, 'Einen Becher (mind. 12 cm tief) mit trockenem Substrat füllen und leicht andrücken.'),
        h('li', null, 'Sensor aus dem Topf ziehen, abwischen und bis zur Markierung in den Becher stecken.'),
        h('li', null, 'Danach misst du trocken, giesst das Substrat durch und misst nass.')),
      h('fieldset', null, h('legend', null, 'Substrat'), ...radios),
      msg,
      h('div.row', null,
        h('button.primary', { type: 'button', onclick: async () => {
          try {
            run = await ctx.api.post(`/sensors/${sid}/calibration-runs`, { substrate, samples: 5 });
            step1();
          } catch (e) { msg.textContent = e.message; }
        } }, 'Start'),
        h('a.btn.ghost', { href: `#/pflanze/${id}` }, 'Abbrechen')));
  }

  function captureUi(point, title, text, next) {
    setStep(point === 'dry' ? 1 : 2);
    const status = h('p.status-line.muted');
    const prog = h('div.progress.indet.hidden', null, h('span'));
    const result = h('p', null, pointText(run[point]));
    const btn = h('button.primary', { type: 'button' }, run[point] ? 'Nochmals messen' : 'Jetzt messen');
    const nextBtn = h('button', { type: 'button', disabled: !run[point], onclick: next }, 'Weiter');
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      nextBtn.disabled = true;
      prog.classList.remove('hidden');
      status.textContent = 'Warte auf den Sensor …';
      try {
        const job = await ctx.api.post(`/calibration-runs/${run.id}/capture`, { point });
        const fin = await watchJob(job, (j) => (status.textContent = j.message || j.state), ctx.stream);
        run = await ctx.api.get(`/calibration-runs/${run.id}`);
        if (fin.state === 'done' && run[point]) {
          const out = fin.result && fin.result.outliers;
          status.textContent = `Gemessen.${out ? ` ${out} Ausreisser verworfen.` : ''}`;
          result.textContent = pointText(run[point]);
          btn.textContent = 'Nochmals messen';
          nextBtn.disabled = false;
        } else {
          status.textContent = fin.message || 'Messung fehlgeschlagen.';
        }
      } catch (e) {
        status.textContent = e.message;
      } finally {
        btn.disabled = false;
        prog.classList.add('hidden');
      }
    });
    body.replaceChildren(h('h2', null, title), ...text.map((t) => h('p', null, t)),
      h('div.card.flat', null, h('strong', null, point === 'dry' ? 'Trockenpunkt: ' : 'Nasspunkt: '), result), status, prog,
      h('div.row', null, btn, nextBtn, cancelBtn()));
  }

  function cancelBtn() {
    return h('button.ghost', { type: 'button', onclick: async () => {
      if (run) await ctx.api.del(`/calibration-runs/${run.id}`).catch(() => null);
      ctx.go(`/pflanze/${id}`);
    } }, 'Abbrechen');
  }

  function step1() {
    captureUi('dry', 'Trocken messen', [
      'Der Sensor steckt bis zur Markierung im trockenen Substrat. Nicht berühren, solange gemessen wird.',
      'Der Sensor misst mehrmals hintereinander; Ausreisser werden verworfen.',
    ], step2);
  }

  function step2() {
    captureUi('wet', 'Nass messen', [
      'Substrat im Becher langsam durchgiessen, bis unten Wasser austritt. 10 Minuten abtropfen lassen.',
      'Sensor gleich tief wie vorher stecken lassen (nicht neu einstecken).',
    ], step3);
  }

  function step3() {
    setStep(3);
    const ok = spanOk(run.dry.raw, run.wet.raw);
    const cal = { dry: run.dry, wet: run.wet };
    const L = plant.latest;
    const preview = L ? evaluate(L.raw, L.temp_c, cal, plant.threshold_pct) : null;
    const msg = h('p.err-text.status-line');
    body.replaceChildren(h('h2', null, 'Prüfen und speichern'),
      h('dl.kv', null,
        h('dt', null, 'Substrat'), h('dd', null, SUBSTRATE[run.substrate]),
        h('dt', null, 'Trocken (0 %)'), h('dd', null, pointText(run.dry)),
        h('dt', null, 'Nass (100 %)'), h('dd', null, pointText(run.wet)),
        preview ? [h('dt', null, 'Letzter Topf-Wert neu'), h('dd', null, preview.moisture_pct != null ? `${fmt.pct1(preview.moisture_pct)} %` : preview.moisture_state)] : null),
      ok ? h('p.ok-text', null, 'Die Werte sind plausibel.') : h('p.err-text', null, 'Trocken- und Nasswert liegen zu nahe beieinander. War das Substrat wirklich nass? Bitte Nass erneut messen.'),
      msg,
      h('div.row', null,
        h('button.primary', { type: 'button', disabled: !ok, onclick: async () => {
          try {
            await ctx.api.post(`/calibration-runs/${run.id}/commit`);
            toast('Kalibrierung gespeichert. Sensor wieder in den Topf stecken.');
            ctx.go(`/pflanze/${id}`);
          } catch (e) { msg.textContent = e.message; }
        } }, 'Speichern'),
        h('button', { type: 'button', onclick: step2 }, 'Nass erneut messen'),
        cancelBtn()));
  }

  main.replaceChildren(h('a.back', { href: `#/pflanze/${id}` }, '← ' + plant.name), h('h1', null, `Kalibrieren: ${plant.name}`),
    h('p.muted', null, `Sensor ${sid}`), steps, body);
  step0();
}
