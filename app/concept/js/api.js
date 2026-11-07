// fluidi Entwürfe – API-Zugriff (gleiche API wie die PWA, app/api/openapi.yaml).
import { h, sheet } from './dom.js';

const BASE = '/api/v1';
let csrf = null;

export class ApiError extends Error {
  constructor(status, code, message) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export async function refreshAuth() {
  const st = await req('GET', '/auth/status', undefined, true);
  csrf = st.csrf || null;
  return st;
}

async function req(method, path, body, noRetry = false) {
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (method !== 'GET' && csrf) headers['X-CSRF-Token'] = csrf;
  let res;
  try {
    res = await fetch(BASE + path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body), credentials: 'same-origin', cache: 'no-store' });
  } catch (e) {
    throw new ApiError(0, 'offline', 'Gateway nicht erreichbar');
  }
  if (res.ok) return res.status === 204 ? null : res.json();
  let err = { code: 'internal', message: `Fehler ${res.status}` };
  try { err = (await res.json()).error || err; } catch (_) { /* leer */ }
  if (!noRetry && (err.code === 'auth_required' || err.code === 'csrf')) {
    if (await loginSheet()) return req(method, path, body, true);
  }
  throw new ApiError(res.status, err.code, err.message);
}

/** Anmeldung als Sheet (einziger Admin = Auftraggeber, REQ-SAF-NET-01). */
function loginSheet() {
  return sheet((close) => {
    const pw = h('input.input', { type: 'password', autocomplete: 'current-password', placeholder: 'Passwort', 'aria-label': 'Passwort' });
    const msg = h('p.err');
    return h('form.stack', {
      onsubmit: async (ev) => {
        ev.preventDefault();
        try {
          const s = await req('POST', '/auth/login', { password: pw.value, remember: true }, true);
          csrf = s.csrf;
          close(true);
        } catch (e) { msg.textContent = e.message; }
      },
    }, h('h2', null, 'Anmelden'), h('p.muted', null, 'Ändern geht nur mit Anmeldung. Lesen ist im LAN frei.'), pw, msg,
    h('button.btn.primary', { type: 'submit' }, 'Anmelden'));
  });
}

export const get = (p) => req('GET', p);
export const post = (p, b = {}) => req('POST', p, b);
export const patch = (p, b) => req('PATCH', p, b);
export const put = (p, b) => req('PUT', p, b);
export const del = (p) => req('DELETE', p);

/** Server-Sent Events (Live-Aktualisierung), verbindet erst nach dem ersten Bild. */
export function stream() {
  const ls = new Map();
  const wired = new Set();
  let es = null;
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
    for (const t of ls.keys()) wire(t);
  };
  return { on, connect };
}
