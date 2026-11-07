// Sensoren & Firmware (REQ-FW-02/04/08, REQ-ENE-05, UC-08): Liste mit Batterie/Funk/Fehlern, signierte Abbilder
// hochladen (Signatur prüft das Gateway), Verteilung mit Fortschritt, Entkoppeln.
import { h, toast, fmt, fill } from './dom.js';
import { icon, batteryIcon, signalIcon } from './art.js';
import { card, toggle } from './comp.js';
import { watchJob } from './api.js';

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
      h('div.sr-name', null, h('strong', null, pname(s.plant_id)), h('span.small.muted', null, `${s.id} · ${s.address || ''}`)),
      h('div.sr-batt', null, batteryIcon(b.pct, b.state !== 'ok'), h('span', null, `${b.pct} %`), h('span.small.muted', null, `${fmt.n1(b.mv / 1000)} V · ~${b.days_left ?? '–'} T.`)),
      h('div.sr-radio', null, signalIcon(sig.quality), h('span.small', null, sig.rssi_dbm != null ? `${sig.rssi_dbm} dBm` : '–'), h('span.small.muted', null, s.last_seen ? fmt.ago(s.last_seen) : 'nie')),
      h('div.sr-fw', null, h('span.small', null, `Firmware ${s.fw_version}`), s.pending_config ? h('span.pill', null, 'Änderung wartet') : null,
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
      const img = await ctx.api.post('/firmware/sensor-images', await file.files[0].arrayBuffer());
      toast(`Version ${img.version} geprüft und abgelegt`, 'ok');
      ctx.refresh();
    } catch (e) { upMsg.textContent = e.message; }
  });
  const imgs = fw.sensor_images.map((i) => h('li.img', null, h('strong', null, i.version), h('span.small.muted', null, ` · ${fmt.n0(i.size / 1024)} kB · Zähler ${i.security_counter} · ${i.signature_ok ? 'Signatur gültig' : 'ungültig'}`),
    h('button.btn.primary.sm', { type: 'button', onclick: () => rollout(i.version) }, 'Verteilen'),
    h('button.btn.ghost.sm', { type: 'button', 'aria-label': 'Entfernen', onclick: async () => { try { await ctx.api.del(`/firmware/sensor-images/${i.version}`); ctx.refresh(); } catch (e) { toast(e.message, 'err'); } } }, icon('trash'))));
  async function rollout(version) {
    const ids = list.filter((s) => s.fw_version !== version.split('+')[0]).map((s) => s.id);
    if (!ids.length) { toast('Alle Sensoren haben diese Version'); return; }
    try { await ctx.api.post('/firmware/rollout', { version, sensor_ids: ids }); toast('Verteilung gestartet – ein Sensor nach dem anderen', 'ok'); ctx.refresh(); } catch (e) { toast(e.message, 'err'); }
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
