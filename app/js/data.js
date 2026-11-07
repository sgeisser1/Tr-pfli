// Export & Backup (REQ-APP-08, REQ-GW-06, UC-14): CSV fluidi-csv v1, verschlüsseltes Vollbackup, Wiederherstellen.
import { h, toast, fmt, fill } from './dom.js';
import { icon } from './art.js';
import { seg, card } from './comp.js';

const DAY = 86400;

export default async function data(el, ctx) {
  const plants = await ctx.api.get('/plants');
  let range = 'jahr';
  let res = 'raw';
  let excel = true;
  const link = h('a.btn.primary', { download: '' }, icon('download'), 'CSV herunterladen');
  const sel = h('select.input', { multiple: true, size: Math.min(6, plants.length || 1), 'aria-label': 'Pflanzen' }, plants.map((p) => h('option', { value: p.id }, p.name)));
  const upd = () => {
    const to = Math.floor(Date.now() / 1000);
    const from = to - { woche: 7, monat: 31, jahr: 366, alles: 3 * 365 }[range] * DAY;
    const ids = [...sel.selectedOptions].map((o) => o.value).join(',');
    const q = new URLSearchParams({ from, to, res, ...(excel ? { sep: 'semicolon', decimal: 'comma' } : { sep: 'comma', decimal: 'point' }), ...(ids ? { plant_ids: ids } : {}) });
    link.href = `/api/v1/export.csv?${q}`;
  };
  sel.addEventListener('change', upd);
  upd();

  // ---------- Backup
  const pp = h('input.input', { type: 'password', autocomplete: 'new-password', minlength: 12, placeholder: 'Passphrase (mind. 12 Zeichen)', 'aria-label': 'Passphrase' });
  const bmsg = h('p.status');
  const mk = h('button.btn.primary', { type: 'button' }, icon('download'), 'Backup erstellen');
  mk.addEventListener('click', async () => {
    if (pp.value.length < 12) { bmsg.textContent = 'Passphrase: mindestens 12 Zeichen.'; return; }
    mk.disabled = true;
    try {
      const r = await ctx.api.req('POST', '/backup', { passphrase: pp.value }, { raw: true });
      const blob = await r.blob();
      const name = (/filename="([^"]+)"/.exec(r.headers.get('Content-Disposition') || '') || [])[1] || 'fluidi-backup.fbk';
      const a = h('a', { href: URL.createObjectURL(blob), download: name });
      document.body.append(a);
      a.click();
      a.remove();
      bmsg.textContent = `Backup ${name} (${fmt.n0(blob.size / 1024)} kB) erstellt. Passphrase gut aufbewahren – ohne sie ist das Backup nicht lesbar.`;
    } catch (e) { bmsg.textContent = e.message; } finally { mk.disabled = false; }
  });
  const rfile = h('input', { type: 'file', accept: '.fbk', 'aria-label': 'Backupdatei' });
  const rpp = h('input.input', { type: 'password', placeholder: 'Passphrase des Backups', 'aria-label': 'Passphrase des Backups' });
  const rmsg = h('p.status');
  const restore = async (dry) => {
    if (!rfile.files.length) { rmsg.textContent = 'Bitte eine .fbk-Datei wählen.'; return; }
    try {
      const r = await ctx.api.req('POST', '/backup/restore', await rfile.files[0].arrayBuffer(), { query: { dry_run: dry }, headers: { 'X-Backup-Passphrase': rpp.value } });
      if (dry) {
        fill(rmsg, `Backup von ${r.gateway_id}, ${fmt.dateTime(r.created)}: ${r.plants} Pflanzen, ${r.sensors} Sensoren, ${fmt.n0(r.records)} Messwerte. `,
          h('button.btn.primary.sm', { type: 'button', onclick: () => { if (window.confirm('Alle Daten dieses Gateways durch das Backup ersetzen? Passwort und Zertifikat bleiben.')) restore(false); } }, 'Jetzt einspielen'));
      } else rmsg.textContent = 'Wird eingespielt – das Gateway startet neu. Seite in einer Minute neu laden.';
    } catch (e) { rmsg.textContent = e.message; }
  };
  el.append(
    h('header.ph.ph-detail', null, h('a.iconbtn', { href: '#/einstellungen', 'aria-label': 'Zurück' }, icon('back')),
      h('div.ph-text', null, h('p.kicker', null, 'Daten'), h('h1', null, 'Export & Backup'))),
    card('CSV-Export (Excel, Auswertungen, ML)',
      h('div.field', null, h('span', null, 'Zeitraum'), seg([['woche', 'Woche'], ['monat', 'Monat'], ['jahr', 'Jahr'], ['alles', 'Alles']], range, (v) => { range = v; upd(); }, 'Zeitraum')),
      h('div.field', null, h('span', null, 'Auflösung'), seg([['raw', 'Rohwerte'], ['hour', 'Stunden'], ['day', 'Tage']], res, (v) => { res = v; upd(); }, 'Auflösung')),
      h('div.field', null, h('span', null, 'Format'), seg([['x', 'Excel (Semikolon, Komma)'], ['c', 'Standard (Komma, Punkt)']], 'x', (v) => { excel = v === 'x'; upd(); }, 'Format')),
      h('label.field', null, 'Pflanzen (keine Auswahl = alle)', sel),
      h('div.actions', null, link),
      h('p.small.muted', null, 'Format fluidi-csv v1: Rohwert, Temperatur, Quelle und Flags (rekonstruierte Zeit, nachgeliefert …) bleiben erhalten. Lese-API: openapi.yaml.')),
    card('Backup',
      h('p.small.muted', null, 'Vollständige, verschlüsselte Sicherung (AES-256-GCM): Pflanzen, Messwerte, Kalibrierung, Tagebuch und Sensorschlüssel. Nicht enthalten: Passwort, Zertifikat, WLAN.'),
      pp, h('div.actions', null, mk), bmsg),
    card('Wiederherstellen',
      rfile, rpp, h('div.actions', null, h('button.btn.ghost', { type: 'button', onclick: () => restore(true) }, 'Prüfen')), rmsg));
  return null;
}
