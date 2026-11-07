// Einstellungen: Darstellung, Messung, LED, Hinweise (strikt lokal, D-020), Dashboard, Konto, Verwaltung.
import { h, toast } from './dom.js';
import { icon, dropChar } from './art.js';
import { pageHead, seg, toggle, card } from './comp.js';

const WD = [[1, 'Mo'], [2, 'Di'], [3, 'Mi'], [4, 'Do'], [5, 'Fr'], [6, 'Sa'], [7, 'So']];

export default async function settings(el, ctx) {
  const se = await ctx.api.get('/settings');
  const st = ctx.api.authState() || {};
  const N = se.notifications;
  const root = document.documentElement;
  const save = async (patch, msg = 'Gesichert') => {
    try { await ctx.api.patch('/settings', patch); toast(msg, 'ok'); return true; } catch (e) { toast(e.message, 'err'); return false; }
  };
  const row = (label, ctrl) => h('li', null, h('span', null, label), ctrl);
  const sel = (opts, val, on, label) => {
    const s = h('select.input.sm', { 'aria-label': label }, opts.map(([v, t]) => h('option', { value: v, selected: v === val }, t)));
    s.addEventListener('change', () => on(s.value));
    return s;
  };
  const time = (val, on, label) => {
    const i = h('input.input.sm', { type: 'time', value: val, 'aria-label': label });
    i.addEventListener('change', () => i.value && on(i.value));
    return i;
  };

  // ---------- Darstellung (nur Stil A Frost, D-020)
  const look = card('Darstellung',
    h('div.row-l', null, h('span.look-prev', { 'aria-hidden': 'true' }, dropChar('happy', { pct: 64, state: 'ok', size: 34, animate: false })),
      seg([['light', 'Hell', 'sun'], ['dark', 'Dunkel', 'moon'], ['auto', 'Automatisch', 'auto']], root.dataset.mode, (v) => ctx.setMode(v), 'Hell oder dunkel')),
    h('p.small.muted', null, 'Automatisch folgt der Einstellung des Geräts. Gespeichert pro Gerät.'));

  // ---------- Messung und Sensor-LED
  const W = se.led.water_window;
  const days = new Set(W.weekdays || [1, 2, 3, 4, 5, 6, 7]);
  const measure = card('Messung & Sensor-LED',
    h('ul.rules', null,
      row('Messungen pro Tag', sel([[1, '1'], [2, '2'], [4, '4'], [6, '6 (Werk)'], [12, '12'], [24, '24'], [48, '48'], [96, '96']].map(([v, t]) => [String(v), t]), String(se.interval_per_day),
        (v) => save({ interval_per_day: Number(v) }, Number(v) > 18 ? 'Gesichert – Puffer reicht dann < 60 Tage' : 'Gesichert'), 'Messungen pro Tag')),
      row('Reaktionszeit „Jetzt messen“', sel([['1', '1 min (Werk)'], ['2', '2 min'], ['5', '5 min (spart Batterie)']], String(se.reaction_time_min), (v) => save({ reaction_time_min: Number(v) }), 'Reaktionszeit')),
      row('Status-LED (Quittung, Lebenszeichen)', toggle(se.led.enabled, (v) => save({ led: { enabled: v } }), 'Status-LED')),
      row('Giessen-Hinweis an der LED (blau)', toggle(se.led.water_hint, (v) => save({ led: { water_hint: v } }), 'Giessen-Hinweis')),
      row('Zeitfenster Giessen-Hinweis', h('span.inl', null, time(W.start, (v) => save({ led: { water_window: { ...W, start: v } } }), 'von'), '–',
        time(W.end, (v) => save({ led: { water_window: { ...W, end: v } } }), 'bis'))),
      row('Helligkeit', sel([['low', 'tief'], ['normal', 'normal'], ['high', 'hoch']], se.led.brightness || 'normal', (v) => save({ led: { brightness: v } }), 'Helligkeit'))),
    h('div.chips', { role: 'group', 'aria-label': 'Wochentage' }, WD.map(([d, t]) => {
      const b = h(`button.chip.tog${days.has(d) ? '.on' : ''}`, { type: 'button', 'aria-pressed': String(days.has(d)) }, t);
      b.addEventListener('click', async () => {
        if (days.has(d)) days.delete(d); else days.add(d);
        if (await save({ led: { water_window: { ...W, weekdays: [...days].sort() } } })) { b.classList.toggle('on'); b.setAttribute('aria-pressed', String(days.has(d))); }
      });
      return b;
    })),
    h('p.small.muted', null, 'Änderungen erhalten die Sensoren beim nächsten Funkkontakt. An abgewählten Tagen bleibt die blaue LED aus.'));

  // ---------- Hinweise (strikt lokal)
  const chan = (ic, title, desc, tag, tagCls, ctrl) => h('li.chan', null, h('span.chan-ic', null, icon(ic)),
    h('div.chan-t', null, h('div', null, h('strong', null, title), h(`span.pill.${tagCls}`, null, tag)), h('p.small.muted', null, desc)), ctrl);
  const notify = card('Hinweise',
    h('ul.chans', null,
      chan('bell', 'In der App', 'Hinweisliste und Banner, sobald die App offen ist.', 'lokal', 'p-local', toggle(N.in_app, (v) => save({ notifications: { in_app: v } }), 'In der App')),
      chan('drop', 'Zähler am App-Symbol', 'Zahl durstiger Pflanzen am fluidi-Symbol (Chrome/Android, installierte App). Wird beim Öffnen aktualisiert.', 'lokal', 'p-local',
        toggle(N.badge, async (v) => { await save({ notifications: { badge: v } }); if (!v && 'clearAppBadge' in navigator) navigator.clearAppBadge().catch(() => null); }, 'Badge')),
      chan('sparkle', 'LED am Sensor', 'Blau blinkend, wenn die Pflanze Wasser braucht (Zeitfenster oben).', 'lokal', 'p-local', h('span.small.muted', null, 'siehe oben')),
      chan('tv', 'Dashboard / Bildschirm', 'Grosse Anzeige im Büro, aktualisiert jede Minute.', 'lokal', 'p-local', h('a.btn.ghost.sm', { href: '#/dashboard' }, 'Öffnen')),
      chan('link', 'Push aufs gesperrte Handy', 'Bräuchte Googles Push-Dienst (Internet). Für den Start bewusst nicht vorgesehen; später als Option möglich (D-020). E-Mail-Hinweise gibt es nicht.', 'später', 'p-ext', h('span.small.muted', null, 'aus'))),
    h('h3', null, 'Wann melden?'),
    h('ul.rules', null,
      row('Giessen nötig, wenn länger als', sel([0, 3, 6, 12, 24].map((x) => [String(x), x ? `${x} h` : 'sofort']), String(N.rules.needs_water_delay_h ?? 0),
        (v) => save({ notifications: { rules: { needs_water_delay_h: Number(v) } } }), 'Verzögerung')),
      row('Kritisch (Sensor in der Luft, überflutet, Fehler)', toggle(N.rules.critical, (v) => save({ notifications: { rules: { critical: v } } }), 'kritisch')),
      row('Batterie unter 30 Tagen', toggle(N.rules.battery_low, (v) => save({ notifications: { rules: { battery_low: v } } }), 'Batterie')),
      row(`Ruhezeit ${N.quiet_hours.start}–${N.quiet_hours.end} (ausser kritisch)`, toggle(N.quiet_hours.enabled, (v) => save({ notifications: { quiet_hours: { enabled: v } } }), 'Ruhezeit'))));

  // ---------- Dashboard
  const D = se.dashboard;
  const host = location.hostname || 'fluidi.local';
  const dashC = card('Dashboard für Kollegen',
    h('ul.rules', null,
      row('Dashboard eingeschaltet', toggle(D.enabled, (v) => save({ dashboard: { enabled: v } }), 'Dashboard')),
      row(`Ohne Anmeldung im Firmennetz (HTTP-Port ${D.port}, nur lesen)`, toggle(D.public, (v) => save({ dashboard: { public: v } }, v ? 'Freigegeben – nur Dashboard, ohne Sensordaten' : 'Nicht mehr freigegeben'), 'öffentlich')),
      row('Pflanzennamen zeigen', toggle(D.show_names, (v) => save({ dashboard: { show_names: v } }), 'Namen'))),
    (() => {
      const t = h('input.input', { value: D.title, maxlength: 40, 'aria-label': 'Titel' });
      t.addEventListener('change', () => save({ dashboard: { title: t.value } }));
      return h('label.field', null, 'Titel', t);
    })(),
    h('p.small.muted', null, `Adresse für den Bildschirm: http://${host}:${D.port}/ – unverschlüsselt (nur lesen, D-020), keine Sensor-IDs, keine Einstellungen, kein Login.`));

  // ---------- Zeit
  const tz = h('input.input', { value: se.time.timezone, maxlength: 40, 'aria-label': 'Zeitzone' });
  tz.addEventListener('change', () => save({ time: { timezone: tz.value.trim() } }));
  const ntp = h('input.input', { value: se.time.ntp_server, maxlength: 64, 'aria-label': 'NTP-Server' });
  ntp.addEventListener('change', () => save({ time: { ntp_server: ntp.value.trim() } }));
  const timeC = card('Zeit', h('ul.rules', null, row('Internet-Zeit (NTP, einzige Verbindung nach aussen)', toggle(se.time.ntp_enabled, (v) => save({ time: { ntp_enabled: v } }), 'NTP'))),
    h('div.row2', null, h('label.field', null, 'Zeitzone', tz), h('label.field', null, 'NTP-Server', ntp)));

  // ---------- Konto
  const npw = h('input.input', { type: 'password', autocomplete: 'new-password', minlength: 10, placeholder: 'Neues Passwort (mind. 10 Zeichen)', 'aria-label': 'Neues Passwort' });
  const acc = card('Konto',
    h('p.small.muted', null, st.logged_in ? `Angemeldet bis ${st.session_expires ? new Date(st.session_expires).toLocaleDateString('de-CH') : '–'}.` : 'Nicht angemeldet.'),
    h('ul.rules', null, row('Lesen ohne Anmeldung im LAN', toggle(se.public_read, (v) => save({ public_read: v }, v ? 'Alle im WLAN können mitlesen' : 'Lesen nur mit Anmeldung'), 'Lesen ohne Anmeldung'))),
    h('div.row-l', null, npw, h('button.btn.ghost.sm', { type: 'button', onclick: async () => {
      try { await ctx.api.post('/auth/password', { new_password: npw.value }); npw.value = ''; toast('Passwort geändert – andere Geräte sind abgemeldet', 'ok'); } catch (e) { toast(e.message, 'err'); }
    } }, 'Ändern')),
    h('div.actions', null, h('button.btn.ghost.sm', { type: 'button', onclick: async () => { await ctx.api.logout(); ctx.go('/anmelden'); } }, 'Abmelden')));

  const admin = card('Gateway & Sensoren',
    h('div.links', null,
      h('a.linkrow', { href: '#/koppeln' }, icon('plus'), 'Sensor koppeln', icon('chev', 'chev')),
      h('a.linkrow', { href: '#/sensoren' }, icon('battery'), 'Sensoren & Firmware', icon('chev', 'chev')),
      h('a.linkrow', { href: '#/daten' }, icon('download'), 'Export & Backup', icon('chev', 'chev')),
      h('a.linkrow', { href: '#/system' }, icon('settings'), 'System: Zeit, WLAN, Protokoll', icon('chev', 'chev'))));

  el.append(pageHead('Einstellungen', 'fluidi'), h('div.setgrid', null, h('div', null, look, admin, measure, timeC), h('div', null, notify, dashC, acc)));
  return null;
}
