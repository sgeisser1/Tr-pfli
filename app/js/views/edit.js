// Pflanze anlegen/bearbeiten: Name, Substrat, Giessschwelle, Giessen-LED, Sensorzuordnung (REQ-APP-05, UC-11).
import { h, field, toast, confirmDialog, SUBSTRATE } from '../ui.js';
import { watchJob } from '../api.js';

export default async function edit(main, ctx) {
  if (!ctx.requireLogin()) return;
  const isNew = !ctx.match[1];
  const id = isNew ? null : Number(ctx.match[1]);
  const [plant, settings, sensors] = await Promise.all([
    isNew ? null : ctx.api.get(`/plants/${id}`),
    ctx.api.get('/settings'),
    ctx.api.get('/sensors'),
  ]);
  const p = plant || { name: '', substrate: 'erde', threshold_pct: settings.default_threshold_pct, water_led: 'inherit', notes: '', sensor_id: null };

  const name = h('input', { type: 'text', value: p.name, maxlength: 40, required: true, autocomplete: 'off' });
  const subs = Object.entries(SUBSTRATE).map(([k, label]) =>
    h('label.check', null, h('input', { type: 'radio', name: 'substrate', value: k, checked: p.substrate === k }), label));
  const thrOut = h('strong', null, `${p.threshold_pct} %`);
  const thr = h('input', { type: 'range', min: 0, max: 100, step: 1, value: p.threshold_pct, oninput: () => (thrOut.textContent = `${thr.value} %`) });
  const ledGlobal = settings.led.water_hint ? 'ein' : 'aus';
  const led = h('select', null,
    h('option', { value: 'inherit', selected: p.water_led === 'inherit' }, `wie Systemeinstellung (zurzeit ${ledGlobal})`),
    h('option', { value: 'on', selected: p.water_led === 'on' }, 'ein'),
    h('option', { value: 'off', selected: p.water_led === 'off' }, 'aus'));
  const notes = h('input', { type: 'text', value: p.notes || '', maxlength: 200 });
  const msg = h('p.err-text.status-line');

  const form = h('form.card', {
    onsubmit: async (ev) => {
      ev.preventDefault();
      const body = {
        name: name.value.trim(),
        substrate: form.querySelector('input[name=substrate]:checked').value,
        threshold_pct: Number(thr.value),
        water_led: led.value,
        notes: notes.value,
      };
      try {
        const saved = isNew ? await ctx.api.post('/plants', body) : await ctx.api.patch(`/plants/${id}`, body);
        toast('Gespeichert');
        ctx.go(`/pflanze/${saved.id}`);
      } catch (e) {
        msg.textContent = e.message;
      }
    },
  },
  h('h2', null, 'Pflanze'),
  field('Name', name),
  h('fieldset', null, h('legend', null, 'Substrat'), h('div.row', null, subs),
    h('div.hint.muted.small', null, 'Pro Substrat gibt es eine eigene Kalibrierung des Sensors.')),
  h('div.field', null, h('label', null, 'Giessen nötig unter ', thrOut), thr,
    h('div.hint', null, 'Unter diesem Feuchteindex wird die Pflanze hervorgehoben und die Sensor-LED blinkt blau.')),
  field('Giessen-Hinweis an der Sensor-LED', led, 'Zeitfenster und Wochentage unter Einstellungen → LED.'),
  field('Notiz', notes),
  msg,
  h('div.row', null, h('button.primary', { type: 'submit' }, isNew ? 'Anlegen' : 'Speichern'),
    h('a.btn.ghost', { href: isNew ? '#/' : `#/pflanze/${id}` }, 'Abbrechen')));

  const parts = [h('a.back', { href: isNew ? '#/' : `#/pflanze/${id}` }, '← zurück'), h('h1', null, isNew ? 'Pflanze hinzufügen' : `${p.name} bearbeiten`), form];

  if (!isNew) {
    const free = sensors.filter((s) => s.plant_id !== id);
    const sel = h('select', null, h('option', { value: '' }, '– kein Sensor –'),
      ...free.map((s) => h('option', { value: s.id }, `${s.id}${s.plant_id ? ' (an anderer Pflanze)' : ''}`)));
    const move = h('input', { type: 'checkbox' });
    const sMsg = h('p.status-line');
    parts.push(h('div.card', null, h('h2', null, 'Sensor'),
      h('p', null, p.sensor_id ? `Zugeordnet: ${p.sensor_id}` : 'Kein Sensor zugeordnet.'),
      field('Anderen Sensor zuordnen', sel, 'Der bisherige Sensor wird von dieser Pflanze gelöst. Die bisherigen Messwerte bleiben bei dieser Pflanze.'),
      h('label.check', null, move, 'Bisherige Messwerte des gewählten Sensors mitnehmen (Sensor zieht mit der Pflanze um)'),
      sMsg,
      h('div.row', null,
        h('button', { type: 'button', onclick: async () => {
          try {
            await ctx.api.put(`/plants/${id}/sensor`, { sensor_id: sel.value || null, move_history: move.checked });
            toast('Zuordnung geändert');
            ctx.go(`/pflanze/${id}`);
          } catch (e) { sMsg.textContent = e.message; }
        } }, 'Zuordnung übernehmen'),
        p.sensor_id ? h('button.danger', { type: 'button', onclick: async () => {
          if (!(await confirmDialog('Sensor entkoppeln?', `${p.sensor_id} vergisst seinen Schlüssel und muss neu gekoppelt werden. Die Messwerte bleiben erhalten.`, 'Entkoppeln', true))) return;
          try {
            const j = await ctx.api.del(`/sensors/${p.sensor_id}`);
            sMsg.textContent = 'Entkopplung läuft …';
            await watchJob(j, null, ctx.stream);
            toast('Sensor entkoppelt');
            ctx.go(`/pflanze/${id}`);
          } catch (e) { sMsg.textContent = e.message; }
        } }, 'Sensor entkoppeln') : null)));
    parts.push(h('div.card', null, h('h2', null, 'Pflanze löschen'),
      h('p.muted', null, 'Die Pflanze verschwindet aus der Übersicht. Messwerte bleiben im Gateway beim Sensor gespeichert und im Backup enthalten.'),
      h('button.danger', { type: 'button', onclick: async () => {
        if (!(await confirmDialog('Pflanze löschen?', `„${p.name}“ wird gelöscht.`, 'Löschen', true))) return;
        await ctx.api.del(`/plants/${id}`);
        toast('Gelöscht');
        ctx.go('/');
      } }, 'Löschen')));
  }
  main.replaceChildren(...parts);
  name.focus();
}
