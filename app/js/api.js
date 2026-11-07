// fluidi – API-Zugriff (docs/interfaces/GATEWAY_API.md). Gleiche Herkunft, Cookie-Sitzung + CSRF-Header.

const BASE = 'api/v1';

export class ApiError extends Error {
  constructor(status, code, message, extra = {}) {
    super(message);
    this.status = status;
    this.code = code;
    Object.assign(this, extra);
  }
}

const auth = { csrf: null, status: null };
let hooks = { onAuthRequired: null, onElevate: null, onOffline: null };

export function setHooks(h) {
  hooks = { ...hooks, ...h };
}
export function authState() {
  return auth.status;
}

export async function refreshAuth() {
  const st = await request('GET', '/auth/status', undefined, { noHooks: true });
  auth.status = st;
  auth.csrf = st.csrf || null;
  return st;
}

function url(path, query) {
  let u = BASE + path;
  if (query) {
    const qs = new URLSearchParams();
    for (const [k, v] of Object.entries(query)) if (v !== undefined && v !== null && v !== '') qs.set(k, String(v));
    const s = qs.toString();
    if (s) u += '?' + s;
  }
  return u;
}

/**
 * request(method, path, body, opts)
 * body: Objekt (JSON) | Blob/ArrayBuffer (octet-stream) | undefined
 * opts: { query, headers, raw (Response zurückgeben), noHooks }
 */
export async function request(method, path, body, opts = {}) {
  const headers = { Accept: 'application/json', ...(opts.headers || {}) };
  let payload;
  if (body instanceof Blob || body instanceof ArrayBuffer) {
    headers['Content-Type'] = 'application/octet-stream';
    payload = body;
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json';
    payload = JSON.stringify(body);
  }
  if (method !== 'GET' && auth.csrf) headers['X-CSRF-Token'] = auth.csrf;
  let res;
  try {
    res = await fetch(url(path, opts.query), { method, headers, body: payload, credentials: 'same-origin', cache: 'no-store' });
  } catch (e) {
    if (hooks.onOffline && !opts.noHooks) hooks.onOffline(true);
    throw new ApiError(0, 'offline', 'Gateway nicht erreichbar. Bist du im richtigen WLAN?');
  }
  if (hooks.onOffline && !opts.noHooks) hooks.onOffline(res.headers.get('X-Fluidi-Offline') === '1');
  if (res.ok) {
    if (opts.raw) return res;
    if (res.status === 204) return null;
    const ct = res.headers.get('Content-Type') || '';
    return ct.includes('application/json') ? res.json() : res.text();
  }
  let err = { code: 'internal', message: `Fehler ${res.status}` };
  try {
    const j = await res.json();
    if (j && j.error) err = j.error;
  } catch (_) { /* kein JSON */ }
  const retry = Number(res.headers.get('Retry-After')) || err.retry_after_s;
  const e = new ApiError(res.status, err.code, err.message, { field: err.field, retryAfter: retry });
  if (!opts.noHooks) {
    if (e.code === 'elevation_required' && hooks.onElevate) {
      const ok = await hooks.onElevate();
      if (ok) return request(method, path, body, { ...opts, noHooks: true });
    }
    if ((e.code === 'auth_required' || e.code === 'csrf') && hooks.onAuthRequired) hooks.onAuthRequired(e);
  }
  throw e;
}

export const get = (p, query) => request('GET', p, undefined, { query });
export const post = (p, b, o) => request('POST', p, b === undefined ? {} : b, o);
export const patch = (p, b) => request('PATCH', p, b);
export const put = (p, b) => request('PUT', p, b);
export const del = (p) => request('DELETE', p);

export async function login(password, remember) {
  const s = await request('POST', '/auth/login', { password, remember }, { noHooks: true });
  auth.csrf = s.csrf;
  await refreshAuth();
  return s;
}
export async function setup(setup_code, password) {
  const s = await request('POST', '/auth/setup', { setup_code, password }, { noHooks: true });
  auth.csrf = s.csrf;
  await refreshAuth();
  return s;
}
export async function elevate(password) {
  return request('POST', '/auth/elevate', { password }, { noHooks: true });
}
export async function logout() {
  try {
    await request('POST', '/auth/logout', {}, { noHooks: true });
  } finally {
    auth.csrf = null;
    await refreshAuth().catch(() => null);
  }
}

/** Auf einen Job warten: SSE-Ereignisse bevorzugt, sonst Polling (1 s). */
export function watchJob(job, onUpdate, stream) {
  const final = new Set(['done', 'failed', 'timeout', 'cancelled']);
  return new Promise((resolve) => {
    let stop = false;
    let unsub = null;
    const finish = (j) => {
      if (stop) return;
      stop = true;
      if (unsub) unsub();
      resolve(j);
    };
    const handle = (j) => {
      if (stop || j.id !== job.id) return;
      onUpdate && onUpdate(j);
      if (final.has(j.state)) finish(j);
    };
    if (stream) unsub = stream.on('job', handle);
    const poll = async () => {
      while (!stop) {
        await new Promise((r) => setTimeout(r, stream && stream.connected ? 4000 : 1000));
        if (stop) break;
        try {
          handle(await get(`/jobs/${encodeURIComponent(job.id)}`));
        } catch (_) { /* weiter versuchen */ }
      }
    };
    poll();
  });
}

/** Server-Sent Events mit automatischem Wiederverbinden (iOS schliesst SSE im Hintergrund). */
export function openStream() {
  const listeners = new Map();
  let es = null;
  const api = {
    connected: false,
    on(type, fn) {
      if (!listeners.has(type)) listeners.set(type, new Set());
      listeners.get(type).add(fn);
      if (es && !wrapped.has(type)) {
        wrapped.add(type);
        es.addEventListener(type, wrap(type));
      }
      return () => listeners.get(type).delete(fn);
    },
    close() {
      if (es) es.close();
      es = null;
      api.connected = false;
    },
    connect,
  };
  const wrapped = new Set();
  function wrap(type) {
    return (ev) => {
      let d;
      try {
        d = JSON.parse(ev.data);
      } catch (_) {
        return;
      }
      for (const fn of listeners.get(type) || []) fn(d);
    };
  }
  function connect() {
    if (es) return;
    es = new EventSource(BASE + '/stream', { withCredentials: true });
    wrapped.clear();
    for (const type of listeners.keys()) {
      wrapped.add(type);
      es.addEventListener(type, wrap(type));
    }
    es.onopen = () => (api.connected = true);
    es.onerror = () => (api.connected = false);
  }
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible' && (!es || es.readyState === 2)) {
      es = null;
      connect();
    }
  });
  return api;
}
