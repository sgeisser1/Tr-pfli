// System: Zeit (REQ-GW-09), WLAN (UC-13), Zertifikat, Speicher, Raumklima, Ereignisprotokoll (UC-12), Neustart.
import { h, toast, fmt } from './dom.js';
import { icon } from './art.js';
import { card } from './comp.js';

const LVL = { info: 'info', warn: 'alert', error: 'alert' };

export default async function system(el, ctx) {
  const [sy, ev] = await Promise.all([ctx.api.get('/system'), ctx.api.get('/system/events', { limit: 60 })]);
  const kv = (k, v) => h('div', null, h('dt', null, k), h('dd', null, v));
  const t = sy.time;
  const timeBtn = t.valid ? null : h('button.btn.primary.sm', { type: 'button', onclick: async () => {
    try { await ctx.api.post('/system/time', { t: new Date().toISOString() }); toast('Zeit vom Handy übernommen', 'ok'); ctx.refresh(); } catch (e) { toast(e.message, 'err'); }
  } }, icon('clock'), 'Zeit vom Handy übernehmen');
  const ssid = h('input.input', { maxlength: 32, placeholder: 'WLAN-Name (SSID)', 'aria-label': 'SSID' });
  const wpw = h('input.input', { type: 'password', minlength: 8, maxlength: 63, placeholder: 'WLAN-Passwort', 'aria-label': 'WLAN-Passwort' });
  const wmsg = h('p.status');
  const st = sy.storage;
  const cert = sy.certificate || {};
  el.append(
    h('header.ph.ph-detail', null, h('a.iconbtn', { href: '#/einstellungen', 'aria-label': 'Zurück' }, icon('back')),
      h('div.ph-text', null, h('p.kicker', null, sy.gateway_id), h('h1', null, 'System'))),
    h('div.setgrid', null,
      h('div', null,
        card('Gateway', h('dl.kv', null,
          kv('Version', sy.version), kv('Läuft seit', fmt.dur(sy.uptime_s)), kv('Funk', `${sy.radio ? sy.radio.backend : '–'} · ${sy.sensors.online}/${sy.sensors.paired} Sensoren online`),
          kv('Kryptografie', sy.crypto_backend || '–'), sy.cpu_temp_c != null ? kv('CPU-Temperatur', `${fmt.n1(sy.cpu_temp_c)} °C`) : null,
          sy.climate ? kv('Raumklima', `${fmt.n1(sy.climate.temp_c)} °C · ${fmt.n0(sy.climate.rh_pct)} % rF`) : kv('Raumklima', 'kein Sensor')),
        h('div.actions', null, h('button.btn.ghost.sm', { type: 'button', onclick: async () => { if (window.confirm('Gateway neu starten? Die App ist ca. 1 min nicht erreichbar.')) { await ctx.api.post('/system/reboot'); toast('Neustart …'); } } }, 'Neu starten'))),
        card('Zeit', h('dl.kv', null, kv('Jetzt', fmt.dateTime(t.now)), kv('Quelle', { ntp: 'Internet-Zeit (NTP)', browser: 'vom Handy', none: 'keine gültige Zeit' }[t.source] || t.source),
          kv('Zeitzone', t.timezone)), t.valid ? null : h('p.err', null, 'Ohne gültige Zeit verteilt das Gateway keine Zeit an die Sensoren; Werte werden als „Zeit unsicher“ markiert.'), timeBtn),
        card('Speicher', h('dl.kv', null, kv('Messwerte', fmt.n0(st.records)), kv('Ältester Wert', st.oldest ? fmt.date(st.oldest) : '–'),
          kv('Datenbank', `${fmt.n1(st.used_bytes / 2 ** 20)} MB`), kv('Frei', st.free_bytes ? `${fmt.n1(st.free_bytes / 2 ** 30)} GB` : '–'),
          st.db_transactions != null ? kv('Schreibvorgänge seit Start', fmt.n0(st.db_transactions)) : null)),
        card('Zertifikat (HTTPS)', h('dl.kv', null, kv('Gültig bis', cert.not_after ? `${fmt.date(cert.not_after)} (${cert.days_left} Tage)` : '–'),
          kv('CA-Fingerabdruck', h('code.fp', null, cert.fingerprint_sha256 || '–'))),
        cert.days_left != null && cert.days_left < 60 ? h('p.err', null, 'Zertifikat läuft bald ab – auf dem Gateway erneuern (GATEWAY_SETUP.md).') : null)),
      h('div', null,
        card('WLAN', h('dl.kv', null, kv('Netz', sy.network.ssid || '–'), kv('Adresse', `${sy.network.hostname} · ${sy.network.ip || '–'}`),
          sy.network.rssi_dbm != null ? kv('Signal', `${sy.network.rssi_dbm} dBm`) : null),
        h('h3', null, 'WLAN wechseln'), ssid, wpw,
        h('div.actions', null, h('button.btn.ghost', { type: 'button', onclick: async () => {
          try { await ctx.api.put('/settings/network', { ssid: ssid.value.trim(), password: wpw.value }); wmsg.textContent = 'Wechsel läuft. Gelingt er nicht innert 2 min, kehrt das Gateway ins alte WLAN zurück.'; } catch (e) { wmsg.textContent = e.message; }
        } }, 'Wechseln')), wmsg),
        card('Ereignisprotokoll', h('ul.events', null, ev.map((e) => h(`li.ev-${e.level}`, null, icon(LVL[e.level] || 'info'),
          h('span.ev-t', null, e.text), h('time.small.muted', { datetime: e.t }, fmt.dateTime(e.t)))))))));
  return null;
}
