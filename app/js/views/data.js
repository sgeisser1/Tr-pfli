// Daten: CSV-Export (REQ-APP-08) sowie Backup/Wiederherstellung (REQ-GW-06, UC-14).
import { h, field, toast, confirmDialog } from '../ui.js';

const PERIODS = [
  ['7', 'Letzte 7 Tage', 7],
  ['30', 'Letzte 30 Tage', 30],
  ['365', 'Letztes Jahr', 365],
  ['all', 'Alles', 3 * 365],
  ['custom', 'Zeitraum wählen', null],
];

function saveBlob(blob, name) {
  const a = h('a', { href: URL.createObjectURL(blob), download: name });
  document.body.append(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
}

export default async function data(main, ctx) {
  const plants = await ctx.api.get('/plants');
  const auth = ctx.auth || {};

  // ---- CSV
  const checks = plants.map((p) => h('label.check', null, h('input', { type: 'checkbox', value: p.id, checked: true }), p.name));
  const period = h('select', null, ...PERIODS.map(([v, l]) => h('option', { value: v, selected: v === '30' }, l)));
  const today = new Date().toISOString().slice(0, 10);
  const from = h('input', { type: 'date', value: new Date(Date.now() - 30 * 86400e3).toISOString().slice(0, 10) });
  const to = h('input', { type: 'date', value: today });
  const custom = h('div.row.hidden', null, field('von', from), field('bis', to));
  period.addEventListener('change', () => custom.classList.toggle('hidden', period.value !== 'custom'));
  const res = h('select', null, h('option', { value: 'raw' }, 'Einzelwerte'), h('option', { value: 'hour' }, 'Stundenmittel'), h('option', { value: 'day' }, 'Tagesmittel'));
  const fmtSel = h('select', null,
    h('option', { value: 'semicolon|point' }, 'Semikolon, Dezimalpunkt (Excel Schweiz)'),
    h('option', { value: 'semicolon|comma' }, 'Semikolon, Dezimalkomma (Excel Deutschland)'),
    h('option', { value: 'comma|point' }, 'Komma, Dezimalpunkt (international)'));
  const msg = h('p.status-line');
  const cardCsv = h('form.card', { onsubmit: (ev) => {
    ev.preventDefault();
    const ids = checks.map((c) => c.querySelector('input')).filter((i) => i.checked).map((i) => i.value);
    if (!ids.length) { msg.textContent = 'Bitte mindestens eine Pflanze wählen.'; return; }
    let t0;
    let t1 = Math.floor(Date.now() / 1000);
    if (period.value === 'custom') {
      t0 = Math.floor(new Date(from.value + 'T00:00').getTime() / 1000);
      t1 = Math.floor(new Date(to.value + 'T23:59:59').getTime() / 1000);
    } else {
      t0 = t1 - PERIODS.find((p) => p[0] === period.value)[2] * 86400;
    }
    if (!(t1 > t0)) { msg.textContent = 'Zeitraum ungültig.'; return; }
    const [sep, decimal] = fmtSel.value.split('|');
    const q = new URLSearchParams({ from: t0, to: t1, res: res.value, sep, decimal });
    if (ids.length !== plants.length) q.set('plant_ids', ids.join(','));
    const a = h('a', { href: `api/v1/export.csv?${q}`, download: '' });
    document.body.append(a);
    a.click();
    a.remove();
    msg.textContent = 'Export wird heruntergeladen.';
  } },
  h('h2', null, 'CSV-Export'),
  h('fieldset', null, h('legend', null, 'Pflanzen'), h('div', null, checks)),
  field('Zeitraum', period), custom,
  h('div.row', null, field('Auflösung', res), field('Format', fmtSel)),
  h('p.muted.small', null, 'Format „fluidi-csv v1“: erste Zeile mit Version und Zeitzone, Zeiten in UTC und Ortszeit.'),
  msg, h('button.primary', { type: 'submit' }, 'CSV herunterladen'));

  // ---- Backup
  const loggedIn = auth.logged_in;
  const bp1 = h('input', { type: 'password', autocomplete: 'new-password', minlength: 12 });
  const bp2 = h('input', { type: 'password', autocomplete: 'new-password', minlength: 12 });
  const bMsg = h('p.status-line');
  const cardBackup = h('div.card', null, h('h2', null, 'Backup'),
    h('p', null, 'Sichert alle Pflanzen, Messwerte, Einstellungen und die Kopplungsschlüssel der Sensoren. Damit lässt sich ein Ersatz-Gateway ohne neues Koppeln einrichten.'),
    h('p.muted.small', null, 'Die Datei wird mit der Passphrase verschlüsselt. Ohne Passphrase ist sie wertlos – gut aufbewahren.'),
    loggedIn ? [
      h('div.row', null, field('Passphrase', bp1, 'mindestens 12 Zeichen'), field('Wiederholen', bp2)),
      bMsg,
      h('button.primary', { type: 'button', onclick: async () => {
        if (bp1.value.length < 12 || bp1.value !== bp2.value) { bMsg.textContent = 'Passphrasen stimmen nicht überein oder sind zu kurz.'; return; }
        try {
          bMsg.textContent = 'Backup wird erstellt …';
          const r = await ctx.api.request('POST', '/backup', { passphrase: bp1.value }, { raw: true });
          const name = (/filename="([^"]+)"/.exec(r.headers.get('Content-Disposition') || '') || [])[1] || 'fluidi-backup.fbk';
          saveBlob(await r.blob(), name);
          bMsg.textContent = `Gespeichert als ${name}.`;
        } catch (e) { bMsg.textContent = e.message; }
      } }, 'Backup herunterladen'),
    ] : h('p', null, h('a', { href: '#/anmelden?zurueck=/daten' }, 'Anmelden'), ' für Backup und Wiederherstellung.'));

  // ---- Wiederherstellen
  const rFile = h('input', { type: 'file', accept: '.fbk,application/octet-stream' });
  const rPass = h('input', { type: 'password', autocomplete: 'off' });
  const rMsg = h('p.status-line');
  const cardRestore = loggedIn ? h('div.card', null, h('h2', null, 'Wiederherstellen'),
    h('p', null, 'Ersetzt alle Daten dieses Gateways durch das Backup. Danach startet das Gateway neu.'),
    field('Backupdatei (.fbk)', rFile), field('Passphrase', rPass), rMsg,
    h('button.danger', { type: 'button', onclick: async () => {
      const f = rFile.files && rFile.files[0];
      if (!f) { rMsg.textContent = 'Bitte Datei wählen.'; return; }
      const headers = { 'X-Backup-Passphrase': rPass.value };
      try {
        const check = await ctx.api.request('POST', '/backup/restore', f, { query: { dry_run: true }, headers });
        const ok = await confirmDialog('Backup einspielen?',
          `Backup von ${check.gateway_id}, erstellt ${new Date(check.created).toLocaleString('de-CH')}: ${check.plants} Pflanzen, ${check.sensors} Sensoren, ${check.records.toLocaleString('de-CH')} Messwerte. Alle aktuellen Daten werden ersetzt.`,
          'Einspielen', true);
        if (!ok) return;
        const r = await ctx.api.request('POST', '/backup/restore', f, { headers });
        rMsg.textContent = `Eingespielt. Neustart in ${r.reboot_in_s ?? '?'} s.`;
        toast('Backup eingespielt');
      } catch (e) { rMsg.textContent = e.message; }
    } }, 'Prüfen und einspielen')) : null;

  main.replaceChildren(h('h1', null, 'Daten'), h('div.grid', null, cardCsv, cardBackup, cardRestore));
}
