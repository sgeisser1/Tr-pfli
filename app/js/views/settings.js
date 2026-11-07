// Einstellungen: Messung, LED, Zeit, Zugriff, MQTT, WLAN, Systemstatus.
import { h, field, toast, fmt } from '../ui.js';

const DAYS = ['Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa', 'So'];

export default async function settings(main, ctx) {
  if (!ctx.requireLogin()) return;
  const [s, sys, net, events] = await Promise.all([
    ctx.api.get('/settings'),
    ctx.api.get('/system'),
    ctx.api.get('/settings/network').catch(() => null),
    ctx.api.get('/system/events', { limit: 15 }).catch(() => []),
  ]);

  async function save(patch, msgEl) {
    try {
      const n = await ctx.api.patch('/settings', patch);
      Object.assign(s, n);
      msgEl.textContent = 'Gespeichert. Sensoren übernehmen die Änderung beim nächsten Kontakt.';
      msgEl.className = 'ok-text status-line';
      return n;
    } catch (e) {
      msgEl.textContent = e.message;
      msgEl.className = 'err-text status-line';
      return null;
    }
  }
  const msg = () => h('p.status-line');

  // ---- Messung
  const m1 = msg();
  const interval = h('input', { type: 'number', min: 1, max: 96, value: s.interval_per_day });
  const reaction = h('select', null, ...[1, 2, 3, 4, 5].map((v) => h('option', { value: v, selected: v === s.reaction_time_min }, `${v} min`)));
  const thr = h('input', { type: 'number', min: 0, max: 100, value: s.default_threshold_pct });
  const cardMeasure = h('form.card', { onsubmit: async (ev) => {
    ev.preventDefault();
    await save({ interval_per_day: Number(interval.value), reaction_time_min: Number(reaction.value), default_threshold_pct: Number(thr.value) }, m1);
  } },
  h('h2', null, 'Messung'),
  field('Messungen pro Tag', interval, `1–96, Standard 6. Mehr Messungen verkürzen die Batterielaufzeit. Speicher reicht beim jetzigen Intervall noch ca. ${s.storage_forecast_days ?? '?'} Tage in voller Auflösung.`),
  field('Reaktionszeit „Jetzt messen“', reaction, 'So lange dauert es höchstens, bis ein Sensor auf „Jetzt messen“ reagiert. Kürzer = mehr Energie.'),
  field('Standard-Giessschwelle für neue Pflanzen (%)', thr),
  m1, h('button.primary', { type: 'submit' }, 'Speichern'));

  // ---- LED
  const m2 = msg();
  const ledOn = h('input', { type: 'checkbox', checked: s.led.enabled });
  const water = h('input', { type: 'checkbox', checked: s.led.water_hint });
  const start = h('input', { type: 'time', value: s.led.water_window.start });
  const end = h('input', { type: 'time', value: s.led.water_window.end });
  const days = DAYS.map((d, i) => h('label', null, h('input', { type: 'checkbox', value: i + 1, checked: (s.led.water_window.weekdays || []).includes(i + 1) }), d));
  const bright = h('select', null, ...[['low', 'schwach'], ['normal', 'normal'], ['high', 'hell']].map(([v, l]) => h('option', { value: v, selected: s.led.brightness === v }, l)));
  const cardLed = h('form.card', { onsubmit: async (ev) => {
    ev.preventDefault();
    const wd = days.map((l) => l.querySelector('input')).filter((i) => i.checked).map((i) => Number(i.value));
    await save({ led: { enabled: ledOn.checked, water_hint: water.checked, brightness: bright.value, water_window: { start: start.value, end: end.value, weekdays: wd } } }, m2);
  } },
  h('h2', null, 'LED am Sensor'),
  h('label.check', null, ledOn, 'Status-LED verwenden (Quittung nach Tastendruck, Fehler, Batterie tief)'),
  h('label.check', null, water, 'Giessen-Hinweis: LED blinkt blau, wenn die Pflanze Wasser braucht (höchstens 1× pro Minute)'),
  h('fieldset', null, h('legend', null, 'Giessen-Hinweis nur in diesem Zeitfenster'),
    h('div.row', null, field('von', start), field('bis', end)),
    h('div.days', null, days)),
  field('Helligkeit', bright),
  h('p.muted.small', null, 'Pro Pflanze lässt sich der Giessen-Hinweis unter „Bearbeiten“ abschalten. Farben: grün = ok, blau = giessen, rot = Batterie/Fehler, gelb = Kopplung.'),
  m2, h('button.primary', { type: 'submit' }, 'Speichern'));

  // ---- Zeit
  const m3 = msg();
  const ntp = h('input', { type: 'checkbox', checked: s.time.ntp_enabled });
  const ntpServer = h('input', { type: 'text', value: s.time.ntp_server, maxlength: 64 });
  const tz = h('input', { type: 'text', value: s.time.timezone, maxlength: 40 });
  const cardTime = h('form.card', { onsubmit: async (ev) => {
    ev.preventDefault();
    await save({ time: { ntp_enabled: ntp.checked, ntp_server: ntpServer.value.trim(), timezone: tz.value.trim() } }, m3);
  } },
  h('h2', null, 'Zeit'),
  h('p', null, `Gateway-Zeit: ${fmt.dateTime(sys.time.now)} · Quelle: ${{ ntp: 'Zeitserver (NTP)', rtc: 'eingebaute Uhr', browser: 'Browser', none: 'keine' }[sys.time.source]}`,
    sys.time.valid ? '' : h('span.pill.warn', null, ' ungültig')),
  h('label.check', null, ntp, 'Zeit von einem Zeitserver holen (einzige Verbindung ins Internet, abschaltbar)'),
  field('Zeitserver', ntpServer, 'Wenn vorhanden besser den Zeitserver der Firma eintragen.'),
  field('Zeitzone', tz, 'IANA-Name, z. B. Europe/Zurich'),
  m3, h('button.primary', { type: 'submit' }, 'Speichern'));

  // ---- Zugriff und Passwort
  const m4 = msg();
  const pub = h('input', { type: 'checkbox', checked: s.public_read });
  const pw1 = h('input', { type: 'password', autocomplete: 'new-password', minlength: 10 });
  const pw2 = h('input', { type: 'password', autocomplete: 'new-password', minlength: 10 });
  const cardAccess = h('div.card', null, h('h2', null, 'Zugriff'),
    h('label.check', null, pub, 'Pflanzen und Verlauf ohne Anmeldung anzeigen (nur im lokalen Netz). Ändern, Koppeln und Updates brauchen immer das Passwort.'),
    h('div.row', null, h('button', { type: 'button', onclick: () => save({ public_read: pub.checked }, m4) }, 'Übernehmen')),
    h('h3', null, 'Passwort ändern'),
    field('Neues Passwort', pw1, 'Mindestens 10 Zeichen. Alle anderen Geräte werden abgemeldet.'),
    field('Wiederholen', pw2),
    m4,
    h('button', { type: 'button', onclick: async () => {
      if (pw1.value.length < 10 || pw1.value !== pw2.value) { m4.textContent = 'Passwörter stimmen nicht überein oder sind zu kurz.'; m4.className = 'err-text status-line'; return; }
      try {
        await ctx.api.post('/auth/password', { new_password: pw1.value });
        m4.textContent = 'Passwort geändert.';
        m4.className = 'ok-text status-line';
        pw1.value = pw2.value = '';
      } catch (e) { m4.textContent = e.message; m4.className = 'err-text status-line'; }
    } }, 'Passwort ändern'));

  // ---- MQTT
  const m5 = msg();
  const mq = s.mqtt;
  const mqOn = h('input', { type: 'checkbox', checked: mq.enabled });
  const mqHost = h('input', { type: 'text', value: mq.host || '', placeholder: 'z. B. homeassistant.local' });
  const mqPort = h('input', { type: 'number', value: mq.port || 1883, min: 1, max: 65535 });
  const mqTls = h('input', { type: 'checkbox', checked: mq.tls });
  const mqUser = h('input', { type: 'text', value: mq.username || '', autocomplete: 'off' });
  const mqPw = h('input', { type: 'password', autocomplete: 'new-password', placeholder: mq.password_set ? '(gespeichert)' : '' });
  const mqDisc = h('input', { type: 'checkbox', checked: mq.discovery });
  const cardMqtt = h('form.card', { onsubmit: async (ev) => {
    ev.preventDefault();
    const p = { enabled: mqOn.checked, host: mqHost.value.trim(), port: Number(mqPort.value), tls: mqTls.checked, username: mqUser.value, discovery: mqDisc.checked };
    if (mqPw.value) p.password = mqPw.value;
    await save({ mqtt: p }, m5);
  } },
  h('h2', null, 'Heimautomation (MQTT, optional)'),
  h('label.check', null, mqOn, 'Messwerte an einen MQTT-Broker im lokalen Netz senden'),
  h('div.row', null, field('Broker', mqHost), field('Port', mqPort)),
  h('label.check', null, mqTls, 'TLS verwenden'),
  h('div.row', null, field('Benutzer', mqUser), field('Passwort', mqPw)),
  h('label.check', null, mqDisc, 'Home-Assistant-Discovery'),
  m5, h('button.primary', { type: 'submit' }, 'Speichern'));

  // ---- WLAN
  const m6 = msg();
  const ssid = h('input', { type: 'text', maxlength: 32, value: net ? net.ssid : '' });
  const wpw = h('input', { type: 'password', autocomplete: 'off', minlength: 8 });
  const cardNet = h('form.card', { onsubmit: async (ev) => {
    ev.preventDefault();
    try {
      await ctx.api.put('/settings/network', { ssid: ssid.value, password: wpw.value });
      m6.textContent = 'Das Gateway versucht das neue WLAN. Klappt es nicht innert 2 Minuten, nimmt es wieder das alte. Danach unter https://fluidi.local erreichbar.';
      m6.className = 'ok-text status-line';
    } catch (e) { m6.textContent = e.message; m6.className = 'err-text status-line'; }
  } },
  h('h2', null, 'WLAN'),
  net ? h('dl.kv', null, h('dt', null, 'Netz'), h('dd', null, net.ssid), h('dt', null, 'Adresse'), h('dd', null, `${net.hostname} (${net.ip || '–'})`),
    h('dt', null, 'Empfang'), h('dd', null, net.rssi_dbm != null ? `${net.rssi_dbm} dBm` : '–')) : null,
  h('h3', null, 'WLAN wechseln'),
  h('div.row', null, field('Netzname (SSID)', ssid), field('WLAN-Passwort', wpw)),
  h('p.muted.small', null, 'Die Sensoren müssen danach nicht neu gekoppelt werden.'),
  m6, h('button', { type: 'submit' }, 'WLAN wechseln'));

  // ---- System
  const st = sys.storage;
  const cardSys = h('div.card', null, h('h2', null, 'System'),
    h('dl.kv', null,
      h('dt', null, 'Gateway'), h('dd', null, sys.gateway_id),
      h('dt', null, 'Version'), h('dd', null, sys.version, ' · ', h('a', { href: '#/firmware' }, 'Firmware-Update')),
      h('dt', null, 'Läuft seit'), h('dd', null, `${Math.floor(sys.uptime_s / 86400)} d ${Math.floor((sys.uptime_s % 86400) / 3600)} h`),
      h('dt', null, 'Sensoren'), h('dd', null, `${sys.sensors.online} von ${sys.sensors.paired} erreichbar`),
      h('dt', null, 'Speicher'), h('dd', null, `${fmt.bytes(st.used_bytes)} von ${fmt.bytes(st.total_bytes)} · ${st.records.toLocaleString('de-CH')} Messwerte seit ${fmt.date(st.oldest)}`),
      h('dt', null, 'Zertifikat'), h('dd', null, `gültig bis ${fmt.date(sys.certificate.not_after)} (${sys.certificate.days_left} Tage)`,
        sys.certificate.days_left < 60 ? h('span.pill.warn', null, ' bald erneuern') : null),
      h('dt', null, 'Fingerabdruck'), h('dd.small', null, sys.certificate.fingerprint_sha256 || '–')),
    h('h3', null, 'Ereignisse'),
    events.length ? h('table', null, h('tbody', null, ...events.map((e) => h('tr', null,
      h('td.small', null, fmt.dateTime(e.t)), h('td', null, e.level === 'info' ? '' : h('span.pill.warn', null, e.level)), h('td', null, e.text))))) : h('p.muted', null, 'Keine Ereignisse.'),
    h('div.row', null, h('button.ghost', { type: 'button', onclick: async () => {
      try { await ctx.api.post('/system/reboot'); toast('Gateway startet neu …'); } catch (e) { toast(e.message, true); }
    } }, 'Gateway neu starten')));

  main.replaceChildren(h('h1', null, 'Einstellungen'),
    h('div.grid', null, cardMeasure, cardLed, cardTime, cardAccess, cardNet, cardMqtt), h('div', null, cardSys));
}
