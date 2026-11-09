// Sensoren & Firmware (REQ-FW-02/04/08, REQ-ENE-05, UC-08): Liste mit Batterie/Funk/Fehlern, signierte Abbilder
// hochladen (Signatur prüft das Gateway), Verteilung mit Fortschritt, Entkoppeln. Diagnose (GET_INFO/GET_DIAG),
// Build-Nummer und Testfirmware-Kennung (TESTFIRMWARE.md Kap. 3, GATEWAY_API 5.10).
import { h, toast, fmt, fill, sheet } from './dom.js';
import { icon, batteryIcon, signalIcon } from './art.js';
import { card, toggle } from './comp.js';
import { watchJob } from './api.js';
import { testfwOf, fwLabel, diagRows, diagFileName, evalCommand, imageTestfw, tfLabel } from './diag.js';

/** Kennzeichnung Testfirmware (nie mit Serie verwechseln): Pill + Gerätename. null bei Serie. */
export function testfwBadge(s) {
  const n = testfwOf(s);
  return n ? h('span.pill.p-ext', { title: `Gerätename ${s.adv_name || '?'} – nur für Prüfungen, nicht für den Betrieb` }, tfLabel(n)) : null;
}

function diagView(d) {
  if (!d) return h('p.muted', null, 'Noch keine Diagnose gespeichert.');
  const url = URL.createObjectURL(new Blob([JSON.stringify(d, null, 1)], { type: 'application/json' }));
  return h('div.diag', null,
    h('p.small.muted', null, `Stand ${fmt.dateTime(d.t)}${d.adv_name ? ` · ${d.adv_name}` : ''}`),
    d.testfw ? h('p.err', null, `TESTFIRMWARE TF-${d.testfw} – nur für Prüfungen. Nach dem Test Serienfirmware einspielen (TESTFIRMWARE.md Kap. 4).`) : null,
    h('dl.kv', null, diagRows(d).map(([k, v]) => h('div', null, h('dt', null, k), h('dd', null, v)))),
    h('div.actions', null, h('a.btn.ghost.sm', { href: url, download: diagFileName(d) }, icon('download'), 'JSON herunterladen')),
    h('p.small.muted', null, 'Auswertung am PC: ', h('code.cmd', null, evalCommand(d))));
}

/** Bottom-Sheet: letzte gespeicherte Diagnose zeigen, neue abrufen (Job wie „Jetzt messen“). */
export async function openDiag(ctx, s) {
  let last = null;
  try { last = (await ctx.api.get(`/sensors/${s.id}/diag`, { limit: 1 }))[0] || null; } catch (e) { toast(e.message, 'err'); return; }
  await sheet((close) => {
    const body = h('div', null, diagView(last));
    const msg = h('p.status');
    const btn = h('button.btn.primary', { type: 'button' }, icon('pulse'), 'Diagnose abrufen');
    btn.addEventListener('click', async () => {
      btn.disabled = true;
      try {
        const j = await ctx.api.post(`/sensors/${s.id}/diag`);
        msg.textContent = j.message || 'Warte auf Sensor';
        const fin = await watchJob(j, (x) => { msg.textContent = x.message || ''; }, ctx.live);
        if (fin.state === 'done' && fin.result) fill(body, diagView(fin.result));
        msg.textContent = fin.state === 'done' ? fin.message : (fin.message || 'Sensor hat nicht geantwortet');
      } catch (e) { msg.textContent = e.message; } finally { btn.disabled = false; }
    });
    return h('div.stack', null, h('h2', null, `Diagnose ${s.id}`), testfwBadge(s),
      h('p.small.muted', null, 'Liest Firmwarestand, Zähler und Fehlerprotokoll beim nächsten Funkkontakt. Nur lesen – der Sensor ändert nichts.'),
      body, msg, h('div.actions', null, btn, h('button.btn.ghost', { type: 'button', onclick: () => close() }, 'Schliessen')));
  }, 'diag-sheet');
}

const RO = { pending: 'wartet', waiting_for_sensor: 'wartet auf Sensor', transferring: 'überträgt', verifying: 'prüft', rebooting: 'Neustart', done: 'fertig', failed: 'fehlgeschlagen', skipped: 'übersprungen' };

export default async function sensors(el, ctx) {
  const [list, plants, fw] = await Promise.all([ctx.api.get('/sensors'), ctx.api.get('/plants'), ctx.api.get('/firmware')]);
  const pname = (id) => (plants.find((p) => p.id === id) || {}).name || 'ohne Pflanze';
  const rows = list.map((s) => {
    const b = s.battery || { pct: 0, mv: 0, days_left: null, state: 'ok' };
    const sig = s.signal || { quality: 0, rssi_dbm: null };
    const unpair = h('button.btn.ghost.sm', { type: 'button' }, icon('trash'), 'Entkoppeln');
    unpair.addEventListener('click', async () => {
      if (!window.confirm(`${s.id} entkoppeln? Der Sensor löscht seinen Schlüssel beim nächsten Kontakt. Messwerte bleiben bei der Pflanze.`)) return;
      unpair.disabled = true;
      try {
        const j = await ctx.api.del(`/sensors/${s.id}`);
        const fin = await watchJob(j, (x) => { unpair.lastChild.textContent = x.message; }, ctx.live);
        if (fin.state === 'done') { toast('Entkoppelt', 'ok'); ctx.refresh(); return; }
        if (window.confirm('Sensor nicht erreicht. Trotzdem im Gateway entfernen (Sensor später per Werkseinstellung zurücksetzen)?')) {
          await ctx.api.del(`/sensors/${s.id}`, { force: 'true' });
          ctx.refresh();
        } else unpair.disabled = false;
      } catch (e) { toast(e.message, 'err'); unpair.disabled = false; }
    });
    return h(`div.srow${b.state !== 'ok' || s.error ? '.warn' : ''}`, null,
      h('div.sr-name', null, h('strong', null, pname(s.plant_id)), h('span.small.muted', null, `${s.id}${s.adv_name && s.adv_name !== s.id ? ` „${s.adv_name}“` : ''} · ${s.address || ''}`)),
      h('div.sr-batt', null, batteryIcon(b.pct, b.state !== 'ok'), h('span', null, `${b.pct} %`), h('span.small.muted', null, `${fmt.n1(b.mv / 1000)} V · ~${b.days_left ?? '–'} T.`)),
      h('div.sr-radio', null, signalIcon(sig.quality), h('span.small', null, sig.rssi_dbm != null ? `${sig.rssi_dbm} dBm` : '–'), h('span.small.muted', null, s.last_seen ? fmt.ago(s.last_seen) : 'nie')),
      h('div.sr-fw', null, h('span.small', null, `Firmware ${fwLabel(s)}`), testfwBadge(s),
        h('button.linkbtn.small', { type: 'button', onclick: () => openDiag(ctx, s), title: 'Firmwarestand, Zähler und Fehlerprotokoll vom Sensor lesen' }, 'Diagnose'), s.pending_config ? h('span.pill', null, 'Änderung wartet') : null,
        s.buffered_records ? h('span.pill', null, `${s.buffered_records} Werte im Puffer`) : null, s.lost_records ? h('span.pill.p-ext', null, `${s.lost_records} verloren`) : null),
      s.error ? h('div.sr-err.small', null, icon('alert'), ` ${s.error.text}`) : null,
      h('div.sr-act', null,
        h('label.inl.small', null, toggle(s.led_enabled, async (v) => { try { await ctx.api.patch(`/sensors/${s.id}`, { led_enabled: v }); toast('Gesichert – gilt beim nächsten Kontakt', 'ok'); } catch (e) { toast(e.message, 'err'); } }, 'LED'), 'LED'),
        unpair));
  });

  // ---------- Firmware
  const file = h('input', { type: 'file', accept: '.bin,application/octet-stream', 'aria-label': 'Firmware-Datei' });
  const upMsg = h('p.status');
  const upload = h('button.btn.ghost', { type: 'button' }, icon('download'), 'Abbild hochladen');
  upload.addEventListener('click', async () => {
    if (!file.files.length) { upMsg.textContent = 'Bitte eine signierte Datei fluidi-sensor-x.y.z.bin wählen.'; return; }
    try {
      const f = file.files[0];
      const img = await ctx.api.post('/firmware/sensor-images', await f.arrayBuffer(), { query: { filename: f.name } });
      const tf = imageTestfw(img);
      toast(tf ? `${tfLabel(tf)} ${img.version} abgelegt – nur für die Musterprüfung` : `Version ${img.version} geprüft und abgelegt`, tf ? 'err' : 'ok');
      ctx.refresh();
    } catch (e) { upMsg.textContent = e.message; }
  });
  const imgs = fw.sensor_images.map((i) => h('li.img', null, h('strong', null, i.version),
    imageTestfw(i) ? h('span.pill.p-ext', { title: 'Testfirmware: nur für die Musterprüfung, nie an Nutzersensoren' }, tfLabel(imageTestfw(i))) : null,
    h('span.small.muted', null, ` · ${Number.isInteger(i.build) ? `Build ${i.build} · ` : ''}${fmt.n0(i.size / 1024)} kB · Zähler ${i.security_counter} · ${i.signature_ok ? 'Signatur gültig' : 'ungültig'}`),
    h('button.btn.primary.sm', { type: 'button', onclick: () => (imageTestfw(i) ? rolloutTestfw(i) : rollout(i.version)) }, 'Verteilen'),
    h('button.btn.ghost.sm', { type: 'button', 'aria-label': 'Entfernen', onclick: async () => { try { await ctx.api.del(`/firmware/sensor-images/${i.version}`); ctx.refresh(); } catch (e) { toast(e.message, 'err'); } } }, icon('trash'))));
  async function rollout(version) {
    const ids = list.filter((s) => s.fw_version !== version.split('+')[0]).map((s) => s.id);
    if (!ids.length) { toast('Alle Sensoren haben diese Version'); return; }
    try { await ctx.api.post('/firmware/rollout', { version, sensor_ids: ids }); toast('Verteilung gestartet – ein Sensor nach dem anderen', 'ok'); ctx.refresh(); } catch (e) { toast(e.message, 'err'); }
  }
  // Sicherheit W-2: Testfirmware nur an EINEN gewählten Sensor und nur nach ausdrücklicher Bestätigung
  async function rolloutTestfw(img) {
    const n = imageTestfw(img);
    await sheet((close) => {
      const sel = h('select.input', { 'aria-label': 'Sensor' }, h('option', { value: '' }, 'Sensor wählen …'),
        list.map((s) => h('option', { value: s.id }, `${s.id} · ${pname(s.plant_id)}`)));
      const chk = h('input', { type: 'checkbox' });
      const msg = h('p.status');
      const go = h('button.btn.primary', { type: 'button', disabled: true }, `${tfLabel(n)} verteilen`);
      const upd = () => { go.disabled = !(sel.value && chk.checked); };
      sel.addEventListener('change', upd);
      chk.addEventListener('change', upd);
      go.addEventListener('click', async () => {
        go.disabled = true;
        try {
          await ctx.api.post('/firmware/rollout', { version: img.version, sensor_ids: [sel.value], confirm_testfw: sel.value });
          toast(`${tfLabel(n)} wird an ${sel.value} verteilt`, 'err');
          close(true);
          ctx.refresh();
        } catch (e) { msg.textContent = e.message; upd(); }
      });
      return h('div.stack', null, h('h2', null, `${tfLabel(n)} ${img.version}`),
        h('p.err', null, 'Testfirmware ist nur für die Musterprüfung (TESTFIRMWARE.md). Sie ändert das Verhalten des Sensors (z. B. Absturztests, Dauerspeisung) – nie an Sensoren im Betrieb verteilen.'),
        sel, h('label.inl.small', null, chk, ' Ich verteile die Testfirmware bewusst an diesen einen Sensor.'),
        msg, h('div.actions', null, go, h('button.btn.ghost', { type: 'button', onclick: () => close() }, 'Abbrechen')));
    });
  }
  const roBox = h('div');
  const drawRo = (ro) => {
    if (!ro) { fill(roBox, ); return; }
    fill(roBox, h('h3', null, `Verteilung ${ro.version}${ro.finished ? ' (beendet)' : ''}`),
      h('ul.rolist', null, ro.items.map((it) => {
        const bar = h('span.tir-fill');
        bar.style.width = `${Math.round((it.progress || 0) * 100)}%`;
        return h(`li.ro-${it.state}`, null, h('span', null, it.sensor_id), h('span.tir', null, bar), h('span.small', null, RO[it.state] || it.state), h('span.small.muted', null, it.message || ''));
      })),
      ro.finished ? null : h('button.btn.ghost.sm', { type: 'button', onclick: async () => { await ctx.api.del('/firmware/rollout'); ctx.refresh(); } }, 'Abbrechen'));
  };
  drawRo(fw.rollout);
  const off = ctx.live.on('rollout', drawRo);
  const g = fw.gateway;
  el.append(
    h('header.ph.ph-detail', null, h('a.iconbtn', { href: '#/einstellungen', 'aria-label': 'Zurück' }, icon('back')),
      h('div.ph-text', null, h('p.kicker', null, 'Gateway & Sensoren'), h('h1', null, 'Sensoren & Firmware')),
      h('a.btn.primary', { href: '#/koppeln' }, icon('plus'), 'Koppeln')),
    card(`Sensoren (${list.length})`, list.length ? h('div.slist', null, rows) : h('p.muted', null, 'Noch keine Sensoren gekoppelt.')),
    card('Sensor-Firmware',
      h('p.small.muted', null, 'Nur vom Entwickler signierte MCUboot-Abbilder (ECDSA P-256). Das Gateway prüft Signatur, Hardware und Sicherheitszähler; der Sensor prüft beim Start nochmals und fällt bei Problemen auf die alte Version zurück.'),
      fw.sensor_images.length ? h('ul.imgs', null, imgs) : h('p.muted', null, 'Kein Abbild abgelegt.'),
      h('div.actions', null, file, upload), upMsg, roBox),
    card('Gateway', h('dl.kv', null,
      h('div', null, h('dt', null, 'Version'), h('dd', null, `${g.version} (${g.platform})`)),
      h('div', null, h('dt', null, 'Release'), h('dd', null, `${g.update_slot}${g.rollback_available ? ' · Rückfall möglich' : ''}`))),
    h('p.small.muted', null, 'Gateway-Updates als signiertes Paket über „Daten & System“ (nur nach Freigabe).')));
  return { cleanup: off };
}
