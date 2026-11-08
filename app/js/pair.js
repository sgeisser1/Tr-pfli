// Sensor koppeln (UC-02, REQ-RF-05, PROTOCOL v2 Kap. 4.2 mit Commitment/Reveal): Taste ≥ 3 s am Sensor, Kandidat wählen, Farbfolge (SAS)
// am Sensor mit der App vergleichen, kurz die Sensortaste drücken UND hier bestätigen.
import { h, toast, fill } from './dom.js';
import { icon, dropChar } from './art.js';
import { pageHead, seg, card } from './comp.js';
import { watchJob } from './api.js';

const SAS = { rot: 'sas-r', 'grün': 'sas-g', gelb: 'sas-y' };

export default async function pair(el, ctx) {
  let state = await ctx.api.get('/pairing');
  const plants = await ctx.api.get('/plants');
  const free = plants.filter((p) => !p.sensor_id);
  const box = h('div.stack');
  let busy = false;

  const cd = h('strong');
  const countdown = () => {
    if (!state.active || !state.until) return '';
    const s = Math.max(0, Math.round((Date.parse(state.until) - Date.now()) / 1000));
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
  };

  function sasView(job, device, msg) {
    const dots = h('div.sas', { role: 'img', 'aria-label': `Farbfolge: ${job.result.sas.join(', ')}` },
      job.result.sas.map((c, i) => h(`span.sas-dot.${SAS[c] || 'sas-y'}`, null, h('span.sas-n', null, String(i + 1)), h('span.sas-t', null, c))));
    const yes = h('button.btn.primary', { type: 'button' }, icon('check'), 'Farben stimmen');
    const no = h('button.btn.ghost', { type: 'button' }, icon('x'), 'Stimmen nicht');
    const send = async (match) => {
      yes.disabled = no.disabled = true;
      try { await ctx.api.post(`/pairing/candidates/${encodeURIComponent(device)}/confirm`, { match }); msg.textContent = match ? 'Bestätigt – drücke jetzt kurz die Taste am Sensor (falls noch nicht geschehen).' : 'Abgebrochen.'; } catch (e) { msg.textContent = e.message; }
    };
    yes.addEventListener('click', () => send(true));
    no.addEventListener('click', () => send(false));
    // Protokoll v2: 60 s für Farbvergleich und Bestätigung (PROTOCOL Kap. 3), danach bricht der Sensor ab
    const left = h('strong');
    const t0 = Date.now();
    const tick = () => { const r = Math.max(0, 60 - Math.round((Date.now() - t0) / 1000)); left.textContent = `${r} s`; if (r > 0 && left.isConnected !== false) setTimeout(tick, 1000); };
    tick();
    return card('Farbfolge vergleichen', h('p', null, 'Der Sensor blinkt jetzt diese fünf Farben (danach Pause, dann wieder von vorne). Stimmt die Reihenfolge?'),
      dots, h('ol.small', null, h('li', null, 'Stimmt die Folge, drücke kurz die Taste am Sensor.'), h('li', null, 'Bestätige hier mit „Farben stimmen“.')),
      h('p.small.muted', null, 'Weicht die Folge ab, könnte ein fremdes Gerät mithören – dann „Stimmen nicht“ wählen.'),
      h('p.small', null, 'Zeit für den Vergleich: ', left),
      h('div.actions', null, yes, no));
  }

  function candidateCard(c) {
    let mode = 'new';
    const name = h('input.input', { maxlength: 40, placeholder: 'z. B. Monstera am Fenster', 'aria-label': 'Name der Pflanze' });
    const spSel = h('select.input', { 'aria-label': 'Art' }, ctx.species.map((s) => h('option', { value: s.key, selected: s.key === 'generic' }, s.name)));
    const existing = h('select.input', { 'aria-label': 'Pflanze' }, free.map((p) => h('option', { value: p.id }, p.name)));
    const newBox = h('div', null, h('label.field', null, 'Name der Pflanze', name), h('label.field', null, 'Art', spSel));
    const exBox = h('div', { hidden: true }, h('label.field', null, 'Pflanze ohne Sensor', existing));
    const msg = h('p.status');
    const sasBox = h('div');
    const btn = h('button.btn.primary', { type: 'submit' }, icon('link'), 'Koppeln');
    return h('form.card.cand', {
      onsubmit: async (ev) => {
        ev.preventDefault();
        let body;
        if (mode === 'ex') body = { plant_id: Number(existing.value) };
        else {
          const sp = ctx.species.find((s) => s.key === spSel.value);
          body = { plant: { name: name.value.trim(), substrate: 'erde', species: spSel.value } };
          if (sp && sp.start_range.lower_pct != null) Object.assign(body.plant, { threshold_pct: sp.start_range.lower_pct, upper_pct: sp.start_range.upper_pct });
          if (!body.plant.name) { msg.textContent = 'Bitte einen Namen eingeben.'; return; }
        }
        btn.disabled = true;
        busy = true;
        try {
          const j = await ctx.api.post(`/pairing/candidates/${encodeURIComponent(c.device)}/accept`, body);
          msg.textContent = 'Schlüssel werden ausgetauscht …';
          let shown = false;
          const fin = await watchJob(j, (x) => {
            msg.textContent = x.message || x.state;
            if (x.state === 'awaiting_confirmation' && !shown) { shown = true; fill(sasBox, sasView(x, c.device, msg)); }
          }, ctx.live);
          fill(sasBox, );
          if (fin.state === 'done') {
            toast(h('span', null, icon('check'), ` ${c.device} gekoppelt – die LED leuchtet grün.`), 'ok');
            ctx.go(`/pflanze/${fin.result.plant_id}`);
          } else {
            msg.textContent = fin.message || 'Kopplung fehlgeschlagen. Taste am Sensor erneut 3 s halten (bis zum gelben Blitz) und loslassen.';
            btn.disabled = false;
            busy = false;
          }
        } catch (e) { msg.textContent = e.message; btn.disabled = false; busy = false; }
      },
    },
    h('div.cand-head', null, dropChar('ok', { pct: 50, state: 'ok', size: 44, animate: true }),
      h('div', null, h('h2', null, c.device), h('p.small.muted', null, `${c.rssi_dbm} dBm${c.known ? ' · war schon gekoppelt' : ''}`))),
    h('p.small.muted', null, 'Kennung mit dem Aufkleber am Sensor vergleichen.'),
    free.length ? seg([['new', 'Neue Pflanze'], ['ex', 'Bestehende Pflanze']], mode, (v) => { mode = v; newBox.hidden = v !== 'new'; exBox.hidden = v !== 'ex'; }, 'Pflanze') : null,
    newBox, exBox, msg, sasBox, h('div.actions', null, btn));
  }

  function draw() {
    if (busy) return;
    if (!state.active) {
      fill(box, card('Neuen Sensor koppeln',
        h('div.pairsteps', null,
          step('1', 'Batterie (CR2032) einsetzen.'),
          step('2', '„Kopplung starten“ – das Gateway sucht 3 Minuten.'),
          step('3', 'Taste oben am Sensor halten, bis die LED nach 3 s kurz gelb blitzt, dann loslassen (vor 8 s). Danach blinkt sie 1 × pro Sekunde gelb.'),
          step('4', 'Sensor wählen, Farbfolge vergleichen, bestätigen.')),
        h('button.btn.primary', { type: 'button', onclick: async () => { state = await ctx.api.post('/pairing/start', { duration_s: 180 }); draw(); } }, icon('plus'), 'Kopplung starten')));
      return;
    }
    cd.textContent = countdown();
    fill(box, 
      card('Suche läuft', h('p', null, 'Noch ', cd, ' – Sensoren im Kopplungsmodus erscheinen hier.'), h('div.progress.indet', null, h('span')),
        h('button.btn.ghost.sm', { type: 'button', onclick: async () => { state = await ctx.api.post('/pairing/stop'); draw(); } }, 'Suche beenden')),
      ...(state.candidates.length ? state.candidates.map(candidateCard)
        : [h('section.card.empty', null, dropChar('sleepy', { size: 60 }), h('p', null, 'Noch kein Sensor gefunden. Taste am Sensor halten, bis die LED nach 3 s kurz gelb blitzt, dann loslassen. Der Sensor blinkt danach gelb.'))]));
  }
  const step = (n, t) => h('div.pstep', null, h('span.pstep-n', null, n), h('span', null, t));

  const off = ctx.live.on('pairing', (s) => { const changed = s.candidates.length !== state.candidates.length; state = s; if (changed) draw(); });
  const timer = setInterval(async () => {
    cd.textContent = countdown();
    if (state.active && Date.parse(state.until) < Date.now() && !busy) { state = await ctx.api.get('/pairing'); draw(); }
  }, 1000);
  const poll = setInterval(async () => {
    if (!state.active || busy) return;
    const s = await ctx.api.get('/pairing').catch(() => null);
    if (s && s.candidates.length !== state.candidates.length) { state = s; draw(); }
  }, 3000);
  el.append(h('header.ph.ph-detail', null, h('a.iconbtn', { href: '#/einstellungen', 'aria-label': 'Zurück' }, icon('back')),
    h('div.ph-text', null, h('p.kicker', null, 'Gateway & Sensoren'), h('h1', null, 'Sensor koppeln'))), box);
  draw();
  return { cleanup() { off(); clearInterval(timer); clearInterval(poll); } };
}
