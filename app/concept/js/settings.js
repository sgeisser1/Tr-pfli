// Einstellungen: Darstellung, Benachrichtigungen (ehrlich: was ist lokal?), Dashboard, Verwaltung.
import { h, toast } from './dom.js';
import { icon, dropChar, plantArt } from './art.js';
import { pageHead, seg, toggle, card } from './comp.js';

export default async function settings(el, ctx) {
  const se = await ctx.api.get('/settings');
  const N = se.notifications;
  const root = document.documentElement;
  const save = async (patch, msg = 'Gesichert') => {
    try {
      await ctx.api.patch('/settings', patch);
      toast(msg, 'ok');
    } catch (e) {
      toast(e.message, 'err');
      return false;
    }
    return true;
  };

  // ---------- Darstellung
  const themeCards = h('div.themes', null, Object.entries(ctx.THEMES).map(([k, t]) => h(`button.themecard.tc-${k}`, { type: 'button', 'data-draft': k, 'aria-pressed': String(root.dataset.theme === k), onclick: () => { ctx.setTheme(k); ctx.refresh(); } },
    h('span.tc-prev', { 'aria-hidden': 'true' }, h('span.tc-a'), h('span.tc-b'), dropChar('happy', { pct: 64, state: 'ok', size: 30, animate: false })),
    h('span.tc-name', null, t.name))));
  const look = card('Darstellung', themeCards,
    h('div.row-l', null, h('span', null, 'Hell / Dunkel'),
      seg([['light', 'Hell', 'sun'], ['dark', 'Dunkel', 'moon'], ['auto', 'Automatisch', 'auto']], root.dataset.mode, (v) => ctx.setTheme(null, v), 'Hell oder dunkel')),
    h('p.small.muted', null, 'Automatisch folgt der Einstellung des Geräts. Gespeichert pro Gerät.'));

  // ---------- Benachrichtigungen
  const chan = (ic, title, desc, tag, tagCls, ctrl) => h('li.chan', null, h('span.chan-ic', null, icon(ic)),
    h('div.chan-t', null, h('div', null, h('strong', null, title), h(`span.pill.${tagCls}`, null, tag)), h('p.small.muted', null, desc)), ctrl);
  const notify = card('Benachrichtigungen',
    h('ul.chans', null,
      chan('bell', 'In der App', 'Hinweisliste und Banner, sobald die App offen ist.', 'lokal', 'p-local', toggle(N.in_app, (v) => save({ notifications: { in_app: v } }), 'In der App')),
      chan('drop', 'Zähler am App-Symbol', 'Badge mit der Zahl durstiger Pflanzen (installierte App; iOS zeigt ihn erst mit Mitteilungs-Erlaubnis).', 'lokal', 'p-local', toggle(N.badge, (v) => save({ notifications: { badge: v } }), 'Badge')),
      chan('tv', 'Dashboard / Bildschirm', 'Grosse Anzeige im Büro, aktualisiert sich jede Minute.', 'lokal', 'p-local', h('a.btn.ghost.sm', { href: '#/dashboard' }, 'Öffnen')),
      chan('note', 'E-Mail über Firmen-SMTP', 'Gateway schickt kritische Hinweise per Mail. Strikt lokal nur, wenn der Mailserver im Firmennetz steht.', 'Firmennetz', 'p-mid', toggle(N.email.enabled, async (v, inp) => { if (!(await save({ notifications: { email: { enabled: v } } }))) inp.checked = !v; }, 'E-Mail')),
      chan('wifi', 'ntfy im LAN', 'Eigener ntfy-Server im Firmennetz. Android sofort (Dauerverbindung), iOS nur mit Weiterleitung über ntfy.sh (Internet).', 'Android lokal', 'p-mid', toggle(N.ntfy.enabled, (v) => save({ notifications: { ntfy: { enabled: v } } }), 'ntfy')),
      chan('link', 'Push-Mitteilung (Web Push)', 'Echte Mitteilungen auf dem gesperrten Handy – laufen über Apple- bzw. Google-Server (verschlüsselt). Widerspricht heute REQ-SYS-01.', 'Entscheid offen', 'p-ext',
        toggle(N.webpush.enabled, async (v, inp) => { if (!(await save({ notifications: { webpush: { enabled: v } } }))) inp.checked = false; }, 'Web Push'))),
    h('h3', null, 'Wann melden?'),
    h('ul.rules', null,
      h('li', null, h('span', null, 'Giessen nötig, wenn länger als'), h('select.input.sm', { onchange: (ev) => save({ notifications: { rules: { needs_water_delay_h: Number(ev.target.value) } } }) },
        [0, 3, 6, 12, 24].map((x) => h('option', { value: x, selected: x === N.rules.needs_water_delay_h }, x ? `${x} h` : 'sofort')))),
      h('li', null, h('span', null, 'Kritisch (Sensor in der Luft, überflutet, Fehler)'), toggle(N.rules.critical, (v) => save({ notifications: { rules: { critical: v } } }), 'kritisch')),
      h('li', null, h('span', null, 'Batterie unter 30 Tagen'), toggle(N.rules.battery_low, (v) => save({ notifications: { rules: { battery_low: v } } }), 'Batterie')),
      h('li', null, h('span', null, `Ruhezeit ${N.quiet_hours.start}–${N.quiet_hours.end} (ausser kritisch)`), toggle(N.quiet_hours.enabled, (v) => save({ notifications: { quiet_hours: { enabled: v } } }), 'Ruhezeit')),
      h('li', null, h('span', null, `Tageszusammenfassung um ${N.rules.daily_summary || '–'}`), toggle(!!N.rules.daily_summary, (v) => save({ notifications: { rules: { daily_summary: v ? '08:00' : null } } }), 'Zusammenfassung'))));

  // ---------- Dashboard
  const D = se.dashboard;
  const dashC = card('Dashboard für Kollegen',
    h('ul.rules', null,
      h('li', null, h('span', null, 'Dashboard eingeschaltet'), toggle(D.enabled, (v) => save({ dashboard: { enabled: v } }), 'Dashboard')),
      h('li', null, h('span', null, `Ohne Anmeldung im Firmennetz (Port ${D.port}, nur lesen)`), toggle(D.public, (v) => save({ dashboard: { public: v } }, v ? 'Öffentlich – nur Dashboard, ohne Sensordaten' : 'Nicht mehr öffentlich'), 'öffentlich')),
      h('li', null, h('span', null, 'Pflanzennamen zeigen'), toggle(D.show_names, (v) => save({ dashboard: { show_names: v } }), 'Namen'))),
    h('p.small.muted', null, `Adresse für den Bildschirm: https://fluidi.local:${D.port}/  ·  zeigt keine Sensor-IDs, keine Einstellungen, kein Login.`));

  // ---------- Verwaltung (Prototyp-Seiten)
  const admin = card('Gateway & Sensoren',
    h('div.links', null,
      h('a.linkrow', { href: '/#/koppeln' }, icon('plus'), 'Sensor koppeln', icon('chev', 'chev')),
      h('a.linkrow', { href: '/#/firmware' }, icon('download'), 'Firmware & Updates', icon('chev', 'chev')),
      h('a.linkrow', { href: '/#/daten' }, icon('note'), 'Export & Backup', icon('chev', 'chev')),
      h('a.linkrow', { href: '/#/einstellungen' }, icon('settings'), 'Messintervall, LED, Zeit, WLAN', icon('chev', 'chev'))),
    h('p.small.muted', null, 'Diese Seiten stammen aus dem funktionalen Prototyp und werden nach der Stilwahl angeglichen.'));

  el.append(pageHead('Einstellungen', 'fluidi'), h('div.setgrid', null, h('div', null, look, dashC, admin), h('div', null, notify)));
}
