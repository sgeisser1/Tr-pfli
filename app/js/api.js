// fluidi – API-Zugriff (docs/interfaces/GATEWAY_API.md, app/api/openapi.yaml). Gleiche Herkunft, Cookie-Sitzung + CSRF.
// Fehler „Anmeldung nötig“ öffnet die Anmeldung, „Passwort bestätigen“ (elevate) ein Bottom-Sheet und wiederholt die Anfrage.
import { h, sheet } from './dom.js';

const BASE = '/api/v1';
let csrf = null;
let status = null;
const hooks = { onAuthRequired: null };

export class ApiError extends Error {
  constructor(st, code, message, extra = {}) {
    super(message);
    this.status = st;
    this.code = code;
    Object.assign(this, extra);
  }
}

export const setHooks = (h2) => Object.assign(hooks, h2);
export const authState = () => status;

export async function refreshAuth() {
  status = await req('GET', '/auth/status', undefined, { noHooks: true });
  csrf = status.csrf || null;
  return status;
}

function url(path, query) {
  let u = BASE + path;
  if (query) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(query)) if (v !== undefined && v !== null && v !== '') qs.set(k, String(v));
    if (qs.toString()) u += '?' + qs;
  }
  return u;
}

export async function req(method, path, body, opts = {}) {
  const headers = { Accept: 'application/json', ...(opts.headers || {}) };
  let payload;
  if (body instanceof Blob || body instanceof ArrayBuffer) {
    headers['Content-Type'] = 'application/octet-stream';
    payload = body;
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }
  if (method !== 'GET' && csrf) headers['X-CSRF-Token'] = csrf;
  let res;
  try {
    res = await fetch(url(path, opts.query), { method, headers, body: payload, credentials: 'same-origin', cache: 'no-store' });
  } catch (_) {
    throw new ApiError(0, 'offline', 'Gateway nicht erreichbar – bist du im richtigen WLAN?');
  }
  if (res.ok) {
    if (opts.raw) return res;
    if (res.status === 204) return null;
    return (res.headers.get('Content-Type') || '').includes('application/json') ? res.json() : res.text();
  }
  let err = { code: 'internal', message: `Fehler ${res.status}` };
  try { err = (await res.json()).error || err; } catch (_) { /* kein JSON */ }
  const e = new ApiError(res.status, err.code, err.message, { field: err.field, retryAfter: Number(res.headers.get('Retry-After')) || err.retry_after_s });
  if (!opts.noHooks) {
    if (e.code === 'elevation_required' && (await elevateSheet())) return req(method, path, body, { ...opts, noHooks: true });
    if (e.code === 'auth_required' || e.code === 'csrf') {
      if (await loginSheet()) return req(method, path, body, { ...opts, noHooks: true });
      if (hooks.onAuthRequired) hooks.onAuthRequired(e);
    }
  }
  throw e;
}

export const get = (p, query) => req('GET', p, undefined, { query });
export const post = (p, b = {}, o) => req('POST', p, b, o);
export const patch = (p, b) => req('PATCH', p, b);
export const put = (p, b) => req('PUT', p, b);
export const del = (p, query) => req('DELETE', p, undefined, { query });

/** Browserzeit anbieten (GATEWAY_API 5.7, REQ-GW-09): Das Gateway übernimmt sie nur ohne gültige Zeit
 *  (kein NTP – das Gateway hat keine Uhr mit Batterie, D-028 –, z. B. nach Stromausfall ohne Internet). Ohne Anmeldung/CSRF nichts tun, Fehler still. */
export async function offerTime() {
  if (!csrf) return null;
  try { return await req('POST', '/system/time', { t: new Date().toISOString() }, { noHooks: true }); } catch { return null; }
}
export async function login(password, remember = true) {
  const s = await req('POST', '/auth/login', { password, remember }, { noHooks: true });
  csrf = s.csrf;
  await refreshAuth();
  offerTime();
  return s;
}
export async function setup(setup_code, password) {
  const s = await req('POST', '/auth/setup', { setup_code, password }, { noHooks: true });
  csrf = s.csrf;
  await refreshAuth();
  offerTime();
  return s;
}
export async function logout() {
  try { await req('POST', '/auth/logout', {}, { noHooks: true }); } finally { csrf = null; await refreshAuth().catch(() => null); }
}

/** Anmeldung als Sheet (einziger Admin, REQ-SAF-NET-01). */
export function loginSheet(text = 'Für diese Aktion braucht es dein Passwort.') {
  if (status && status.setup_required) return Promise.resolve(false);
  return sheet((close) => {
    const pw = h('input.input', { type: 'password', autocomplete: 'current-password', placeholder: 'Passwort', 'aria-label': 'Passwort' });
    const msg = h('p.err');
    queueMicrotask(() => pw.focus());
    return h('form.stack', {
      onsubmit: async (ev) => {
        ev.preventDefault();
        try { await login(pw.value, true); close(true); } catch (e) { msg.textContent = e.message; pw.value = ''; }
      },
    }, h('h2', null, 'Anmelden'), h('p.muted', null, text), pw, msg, h('button.btn.primary', { type: 'submit' }, 'Anmelden'));
  });
}

/** Heikle Aktionen: Passwort erneut bestätigen (5 min gültig, GATEWAY_API 3.3). */
export function elevateSheet() {
  return sheet((close) => {
    const pw = h('input.input', { type: 'password', autocomplete: 'current-password', placeholder: 'Passwort', 'aria-label': 'Passwort' });
    const msg = h('p.err');
    queueMicrotask(() => pw.focus());
    return h('form.stack', {
      onsubmit: async (ev) => {
        ev.preventDefault();
        try { await req('POST', '/auth/elevate', { password: pw.value }, { noHooks: true }); close(true); } catch (e) { msg.textContent = e.message; pw.value = ''; }
      },
    }, h('h2', null, 'Passwort bestätigen'), h('p.muted', null, 'Diese Aktion ist heikel (Firmware, Backup, WLAN, Passwort). Bitte bestätige dein Passwort.'),
    pw, msg, h('button.btn.primary', { type: 'submit' }, 'Bestätigen'));
  });
}

/** Auf einen Job warten (SSE bevorzugt, sonst Polling 1 s, iOS/Android im Hintergrund). */
export async function watchJob(job, onUpdate, live, final = ['done', 'failed', 'timeout', 'cancelled']) {
  let j = job;
  let off = null;
  const p = new Promise((resolve) => {
    const check = (x) => {
      if (x.id !== job.id) return;
      j = x;
      onUpdate && onUpdate(x);
      if (final.includes(x.state)) resolve(x);
    };
    if (live) off = live.on('job', check);
    const tick = async () => {
      if (final.includes(j.state)) return;
      try { check(await get(`/jobs/${job.id}`)); } catch (_) { /* nächster Versuch */ }
      if (!final.includes(j.state)) setTimeout(tick, 1000);
    };
    setTimeout(tick, 600);
  });
  const r = await p;
  if (off) off();
  return r;
}

/** Server-Sent Events: Live-Aktualisierung; verbindet bei visibilitychange neu (Android/iOS schliessen im Hintergrund). */
export function stream() {
  const ls = new Map();
  let es = null;
  const wired = new Set();
  const wire = (t) => {
    if (!es || wired.has(t)) return;
    wired.add(t);
    es.addEventListener(t, (ev) => {
      let d;
      try { d = JSON.parse(ev.data); } catch (_) { return; }
      for (const f of ls.get(t) || []) f(d);
    });
  };
  const on = (t, fn) => {
    if (!ls.has(t)) ls.set(t, new Set());
    ls.get(t).add(fn);
    wire(t);
    return () => ls.get(t).delete(fn);
  };
  const connect = () => {
    if (es || typeof EventSource === 'undefined') return;
    es = new EventSource(BASE + '/stream');
    wired.clear();
    for (const t of ls.keys()) wire(t);
    es.onerror = () => { if (es && es.readyState === 2) { es = null; setTimeout(connect, 5000); } };
  };
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && (!es || es.readyState === 2)) { es = null; connect(); }
  });
  return { on, connect };
}
