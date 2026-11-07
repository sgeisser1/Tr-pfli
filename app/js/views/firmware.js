// Firmware: Gateway-Update (A/B, signiert) und Verteilung signierter Sensor-Firmware (UC-08, REQ-FW-02/04, REQ-GW-11).
import { h, toast, confirmDialog, fmt, field } from '../ui.js';

const ITEM_TEXT = {
  pending: 'wartet', waiting_for_sensor: 'Sensor nicht erreichbar', transferring: 'überträgt', verifying: 'prüft Signatur',
  rebooting: 'startet neu', done: 'fertig', failed: 'fehlgeschlagen', skipped: 'übersprungen',
};

export default async function firmware(main, ctx) {
  if (!ctx.requireLogin()) return;
  let fw = await ctx.api.get('/firmware');
  let sensors = await ctx.api.get('/sensors');
  const rolloutBox = h('div');
  const imagesBox = h('div');

  function readFile(input) {
    const f = input.files && input.files[0];
    if (!f) throw new Error('Bitte zuerst eine Datei wählen.');
    return f;
  }

  // ---- Gateway
  const gwFile = h('input', { type: 'file', accept: '.bin,application/octet-stream' });
  const gwMsg = h('p.status-line');
  const g = fw.gateway;
  const cardGw = h('div.card', null, h('h2', null, 'Gateway'),
    h('dl.kv', null,
      h('dt', null, 'Version'), h('dd', null, `${g.version} (PWA ${g.pwa_version || '?'})`),
      h('dt', null, 'Plattform'), h('dd', null, g.platform),
      h('dt', null, 'Aktiver Update-Platz'), h('dd', null, `${g.update_slot}${g.rollback_available ? ', Rückfall möglich' : ''}`),
      h('dt', null, 'Secure Boot'), h('dd', null, g.secure_boot ? 'aktiv' : h('span.pill.warn', null, 'aus (Entwicklung)')),
      h('dt', null, 'Speicherverschlüsselung'), h('dd', null, g.storage_encryption === 'off' ? h('span.pill.warn', null, 'aus (Entwicklung)') : g.storage_encryption)),
    field('Signiertes Gateway-Abbild (.bin)', gwFile, 'Das Gateway prüft die Signatur, schreibt in die freie Partition und startet neu. Daten und Kopplungen bleiben erhalten.'),
    gwMsg,
    h('button', { type: 'button', onclick: async () => {
      try {
        const f = readFile(gwFile);
        if (!(await confirmDialog('Gateway aktualisieren?', `${f.name} (${fmt.bytes(f.size)}) installieren. Das Gateway ist danach ca. 30 s nicht erreichbar.`, 'Installieren'))) return;
        gwMsg.textContent = 'Übertrage und prüfe …';
        const r = await ctx.api.request('POST', '/firmware/gateway', f);
        gwMsg.textContent = `Version ${r.version} installiert, Neustart in ${r.reboot_in_s} s.`;
      } catch (e) { gwMsg.textContent = e.message; }
    } }, 'Gateway aktualisieren'));

  // ---- Sensor-Abbilder
  const sFile = h('input', { type: 'file', accept: '.bin,application/octet-stream' });
  const sMsg = h('p.status-line');
  function drawImages() {
    imagesBox.replaceChildren(fw.sensor_images.length
      ? h('table', null, h('thead', null, h('tr', null, h('th', null, 'Version'), h('th', null, 'Grösse'), h('th', null, 'Signatur'), h('th', null, 'SHA-256'), h('th'))),
        h('tbody', null, ...fw.sensor_images.map((i) => h('tr', null,
          h('td', null, i.version), h('td', null, fmt.bytes(i.size)), h('td', null, i.signature_ok ? 'gültig' : h('span.pill.warn', null, 'ungültig')),
          h('td.small', null, i.sha256.slice(0, 12) + '…'),
          h('td', null, h('button.ghost', { type: 'button', onclick: async () => {
            await ctx.api.del(`/firmware/sensor-images/${encodeURIComponent(i.version)}`);
            fw = await ctx.api.get('/firmware');
            drawImages();
            drawRollout();
          } }, 'Entfernen'))))))
      : h('p.muted', null, 'Keine Sensor-Firmware abgelegt.'));
  }
  const cardImg = h('div.card', null, h('h2', null, 'Sensor-Firmware'),
    imagesBox,
    field('Signiertes Sensor-Abbild hochladen', sFile, 'Nur vom Projekt signierte Abbilder werden angenommen. Ältere Versionen als auf den Sensoren lehnt der Sensor ab.'),
    sMsg,
    h('button', { type: 'button', onclick: async () => {
      try {
        const f = readFile(sFile);
        sMsg.textContent = 'Prüfe Signatur …';
        const img = await ctx.api.request('POST', '/firmware/sensor-images', f);
        sMsg.textContent = `Version ${img.version} abgelegt.`;
        fw = await ctx.api.get('/firmware');
        drawImages();
        drawRollout();
      } catch (e) { sMsg.textContent = e.message; }
    } }, 'Hochladen'));

  // ---- Verteilung
  function drawRollout() {
    const ro = fw.rollout;
    const active = ro && !ro.finished;
    const parts = [h('h2', null, 'Verteilen')];
    if (ro) {
      parts.push(h('p', null, `Version ${ro.version}, gestartet ${fmt.dateTime(ro.started)}${ro.finished ? ', beendet' : ''}`),
        h('table', null, h('tbody', null, ...ro.items.map((it) => {
          const bar = h('div.progress', null, h('span'));
          bar.firstChild.style.width = `${Math.round((it.progress || 0) * 100)}%`;
          return h('tr', null, h('td', null, it.sensor_id), h('td', null, ITEM_TEXT[it.state] || it.state, it.message ? h('div.muted.small', null, it.message) : null), h('td', null, bar));
        }))));
      if (active) parts.push(h('button.ghost', { type: 'button', onclick: async () => { await ctx.api.del('/firmware/rollout'); refresh(); } }, 'Abbrechen'));
    }
    if (!active && fw.sensor_images.length) {
      const ver = h('select', null, ...fw.sensor_images.map((i) => h('option', { value: i.version }, i.version)));
      const checks = sensors.map((s) => h('label.check', null, h('input', { type: 'checkbox', value: s.id, checked: s.battery && s.battery.pct >= 20 }),
        `${s.id} – Version ${s.fw_version}, Batterie ${s.battery ? s.battery.pct + ' %' : '?'}`));
      const msg = h('p.status-line');
      parts.push(field('Version', ver), h('fieldset', null, h('legend', null, 'Sensoren'), ...checks),
        h('p.muted.small', null, 'Sensoren mit tiefer Batterie lehnen das Update ab (REQ-FW-02). Ein Update dauert pro Sensor einige Minuten; nicht erreichbare Sensoren werden später versucht.'),
        msg,
        h('button.primary', { type: 'button', onclick: async () => {
          const ids = checks.map((c) => c.querySelector('input')).filter((i) => i.checked).map((i) => i.value);
          if (!ids.length) { msg.textContent = 'Bitte Sensoren wählen.'; return; }
          try {
            fw.rollout = await ctx.api.post('/firmware/rollout', { version: ver.value, sensor_ids: ids });
            drawRollout();
          } catch (e) { msg.textContent = e.message; }
        } }, 'Verteilung starten'));
    }
    rolloutBox.replaceChildren(h('div.card', null, ...parts));
  }

  async function refresh() {
    fw = await ctx.api.get('/firmware');
    sensors = await ctx.api.get('/sensors');
    drawRollout();
  }

  const off = ctx.stream.on('rollout', (ro) => {
    fw.rollout = ro;
    drawRollout();
    if (ro.finished) refresh().then(() => toast('Verteilung beendet'));
  });

  main.replaceChildren(h('a.back', { href: '#/einstellungen' }, '← Einstellungen'), h('h1', null, 'Firmware-Update'), cardGw, cardImg, rolloutBox);
  drawImages();
  drawRollout();
  return { cleanup: off };
}
