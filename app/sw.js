// fluidi Service Worker: Offline-App-Shell, keine API-Daten ausser letzter Übersicht.
// Version erhöhen, wenn sich die Shell ändert (das Gateway-Update liefert eine neue sw.js aus).
const VERSION = 'fluidi-shell-v1';
const DATA = 'fluidi-data-v1';
const SHELL = [
  './',
  'index.html',
  'manifest.webmanifest',
  'css/app.css',
  'js/app.js',
  'js/api.js',
  'js/calc.js',
  'js/ui.js',
  'js/chart.js',
  'js/views/overview.js',
  'js/views/detail.js',
  'js/views/edit.js',
  'js/views/calibrate.js',
  'js/views/pair.js',
  'js/views/settings.js',
  'js/views/firmware.js',
  'js/views/data.js',
  'js/views/login.js',
  'vendor/uplot/uPlot.iife.min.js',
  'vendor/uplot/uPlot.min.css',
  'img/logo.svg',
  'icons/icon-192.png',
  'icons/icon-180.png',
  'icons/favicon-32.png',
];
// GET-Antworten, die offline als letzter Stand gezeigt werden dürfen
const OFFLINE_API = [/\/api\/v1\/plants$/, /\/api\/v1\/settings$/];

self.addEventListener('install', (ev) => {
  ev.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (ev) => {
  ev.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== VERSION && k !== DATA).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (ev) => {
  const req = ev.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/')) {
    if (OFFLINE_API.some((rx) => rx.test(url.pathname))) ev.respondWith(networkFirst(req));
    return; // alle anderen API-Aufrufe (inkl. /stream) gehen direkt ans Netz
  }
  if (req.mode === 'navigate') {
    ev.respondWith(fetch(req).catch(() => caches.match('index.html')));
    return;
  }
  ev.respondWith(staleWhileRevalidate(req, ev));
});

async function networkFirst(req) {
  const cache = await caches.open(DATA);
  try {
    const res = await fetch(req);
    if (res.ok) cache.put(req, res.clone());
    return res;
  } catch (e) {
    const hit = await cache.match(req);
    if (!hit) throw e;
    const h = new Headers(hit.headers);
    h.set('X-Fluidi-Offline', '1');
    return new Response(await hit.blob(), { status: 200, headers: h });
  }
}

async function staleWhileRevalidate(req, ev) {
  const cache = await caches.open(VERSION);
  const hit = await cache.match(req, { ignoreSearch: true });
  const update = fetch(req)
    .then((res) => {
      if (res.ok) cache.put(req, res.clone());
      return res;
    })
    .catch(() => hit || Response.error());
  if (hit) {
    ev.waitUntil(update);
    return hit;
  }
  return update;
}
