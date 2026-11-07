// Sensor koppeln (UC-02, REQ-RF-05): Tastendruck am Sensor + Bestätigung hier.
import { h, field, toast, drop, SUBSTRATE } from '../ui.js';
import { watchJob } from '../api.js';

export default async function pair(main, ctx) {
  if (!ctx.requireLogin()) return;
  let state = await ctx.api.get('/pairing');
  const plants = await ctx.api.get('/plants');
  const free = plants.filter((p) => !p.sensor_id);
  const box = h('div');
  let timer = null;

  function countdown() {
    if (!state.active || !state.until) return '';
    const s = Math.max(0, Math.round((Date.parse(state.until) - Date.now()) / 1000));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  }

  function candidateCard(c) {
    const mode = { v: free.length ? 'new' : 'new' };
    const name = h('input', { type: 'text', maxlength: 40, placeholder: 'z. B. Monstera im Sitzungszimmer', required: true });
    const sub = h('select', null, ...Object.entries(SUBSTRATE).map(([k, l]) => h('option', { value: k }, l)));
    const existing = h('select', null, ...free.map((p) => h('option', { value: p.id }, p.name)));
    const newBox = h('div', null, field('Name der Pflanze', name), field('Substrat', sub));
    const exBox = h('div.hidden', null, field('Pflanze', existing));
    const msg = h('p.status-line');
    const radios = h('div.row', null,
      h('label.check', null, h('input', { type: 'radio', name: `m-${c.device}`, checked: true, onchange: () => { mode.v = 'new'; newBox.classList.remove('hidden'); exBox.classList.add('hidden'); } }), 'Neue Pflanze'),
      free.length ? h('label.check', null, h('input', { type: 'radio', name: `m-${c.device}`, onchange: () => { mode.v = 'ex'; exBox.classList.remove('hidden'); newBox.classList.add('hidden'); } }), 'Bestehende Pflanze ohne Sensor') : null);
    const btn = h('button.primary', { type: 'submit' }, 'Koppeln');
    return h('form.card', {
      onsubmit: async (ev) => {
        ev.preventDefault();
        const body = mode.v === 'ex' ? { plant_id: Number(existing.value) } : { plant: { name: name.value.trim(), substrate: sub.value } };
        if (mode.v === 'new' && !body.plant.name) { msg.textContent = 'Bitte einen Namen eingeben.'; return; }
        btn.disabled = true;
        try {
          const j = await ctx.api.post(`/pairing/candidates/${encodeURIComponent(c.device)}/accept`, body);
          msg.textContent = 'Schlüssel werden ausgetauscht …';
          const fin = await watchJob(j, (x) => (msg.textContent = x.message || x.state), ctx.stream);
          if (fin.state === 'done') {
            toast(`${c.device} gekoppelt. Die LED blinkt grün.`);
            ctx.go(`/pflanze/${fin.result.plant_id}`);
          } else {
            msg.textContent = fin.message || 'Kopplung fehlgeschlagen. Taste am Sensor erneut lange drücken.';
            btn.disabled = false;
          }
        } catch (e) {
          msg.textContent = e.message;
          btn.disabled = false;
        }
      },
    },
    h('div.row', null, drop('yellow', 'Kopplungsmodus'), h('h2', null, c.device),
      h('span.muted', null, `${c.rssi_dbm} dBm · Firmware ${c.fw_version || '?'}${c.known ? ' · war schon gekoppelt' : ''}`)),
    h('p.muted.small', null, 'Prüfe, dass die Kennung zum Aufkleber bzw. zum Sensor in deiner Hand passt.'),
    radios, newBox, exBox, msg, h('div.row', null, btn));
  }

  function draw() {
    if (!state.active) {
      box.replaceChildren(h('div.card', null,
        h('h2', null, 'Neuen Sensor koppeln'),
        h('ol', null,
          h('li', null, 'Batterie (CR2032) in den Sensor einsetzen, wie in der Anleitung beschrieben.'),
          h('li', null, 'Hier „Kopplung starten“ drücken. Das Gateway sucht 3 Minuten lang.'),
          h('li', null, 'Taste oben am Sensor mindestens 3 Sekunden drücken, bis die LED gelb blinkt.'),
          h('li', null, 'Sensor in der Liste bestätigen und der Pflanze zuordnen.')),
        h('button.primary', { type: 'button', onclick: async () => {
          state = await ctx.api.post('/pairing/start', { duration_s: 180 });
          draw();
        } }, 'Kopplung starten')));
      return;
    }
    const list = state.candidates.length
      ? state.candidates.map(candidateCard)
      : [h('div.card.empty', null, 'Noch kein Sensor gefunden. Taste am Sensor mindestens 3 Sekunden drücken, bis die LED gelb blinkt.')];
    box.replaceChildren(
      h('div.card', null, h('div.row.between', null,
        h('div', null, h('h2', null, 'Suche läuft'), h('p.muted', null, 'Noch ', h('strong#cd', null, countdown()), ' – Sensoren im Kopplungsmodus erscheinen hier.')),
        h('button.ghost', { type: 'button', onclick: async () => { state = await ctx.api.post('/pairing/stop'); draw(); } }, 'Suche beenden')),
        h('div.progress.indet', null, h('span'))),
      ...list);
  }

  const off = ctx.stream.on('pairing', (s) => {
    const hadForm = box.querySelector('form');
    const same = hadForm && s.candidates.length === state.candidates.length;
    state = s;
    if (!same) draw();
  });
  timer = setInterval(async () => {
    const cd = document.getElementById('cd');
    if (cd) cd.textContent = countdown();
    if (state.active && Date.parse(state.until) < Date.now()) {
      state = await ctx.api.get('/pairing');
      draw();
    }
  }, 1000);
  const poll = setInterval(async () => {
    if (!state.active || box.querySelector('form')) return;
    const s = await ctx.api.get('/pairing').catch(() => null);
    if (s && s.candidates.length !== state.candidates.length) { state = s; draw(); }
  }, 4000);

  main.replaceChildren(h('h1', null, 'Sensor koppeln'), box);
  draw();
  return { cleanup() { off(); clearInterval(timer); clearInterval(poll); } };
}
