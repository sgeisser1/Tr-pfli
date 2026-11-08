// fluidi Service Worker: Offline-App-Shell (strikt lokal, keine fremden Ressourcen).
// Version erhöhen, wenn sich die Shell ändert (ein Gateway-Update liefert eine neue sw.js aus).
const VERSION = 'fluidi-frost-v3';
const DATA = 'fluidi-data-v1';
const SHELL = [
  './',
  'index.html',
  'manifest.webmanifest',
  'css/app.css',
  'js/main.js',
  'js/api.js',
  'js/dom.js',
  'js/art.js',
  'js/chart.js',
  'js/comp.js',
  'js/board.js',
  'js/home.js',
  'js/plant.js',
  'js/edit.js',
  'js/room.js',
  'js/dash.js',
  'js/stats.js',
  'js/settings.js',
  'js/login.js',
  'js/pair.js',
  'js/calibrate.js',
  'js/sensors.js',
  'js/data.js',
  'js/system.js',
  'js/calc.js',
  'js/dashboard.js',
  'dashboard.html',
  'img/logo.svg',
  'img/logo-dunkel.svg',
  'icons/icon-192.png',
  'icons/icon-180.png',
  'icons/icon-96.png',
  'icons/favicon-32.png',
];
// GET-Antworten, die offline als letzter Stand gezeigt werden dürfen (Übersicht, Arten)
const OFFLINE_API = [/\/api\/v1\/plants$/, /\/api\/v1\/species$/, /\/api\/v1\/alerts$/];

self.addEventListener('install', (ev) => {
  ev.waitUntil(caches.open(VERSION).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (ev) => {
  ev.waitUntil(caches.keys()
    .then((keys) => Promise.all(keys.filter((k) => k !== VERSION && k !== DATA).map((k) => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', (ev) => {
  const req = ev.request;
  const url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== self.location.origin) return;
  if (url.pathname.startsWith('/api/')) {
    // API nie aus dem Shell-Cache; einzelne Lesewerte nur als Notnagel, wenn das Gateway nicht antwortet
    if (OFFLINE_API.some((rx) => rx.test(url.pathname))) {
      ev.respondWith(fetch(req).then((res) => {
        if (res.ok) { const copy = res.clone(); caches.open(DATA).then((c) => c.put(req, copy)); }
        return res;
      }).catch(() => caches.match(req).then((r) => r || new Response(JSON.stringify({ error: { code: 'offline', message: 'Gateway nicht erreichbar' } }),
        { status: 503, headers: { 'Content-Type': 'application/json' } }))));
    }
    return;
  }
  // Shell: zuerst Netz (neue Version nach Gateway-Update), sonst Cache
  ev.respondWith(fetch(req).then((res) => {
    if (res.ok && SHELL.some((f) => url.pathname.endsWith('/' + f.replace('./', '')))) {
      const copy = res.clone();
      caches.open(VERSION).then((c) => c.put(req, copy));
    }
    return res;
  }).catch(() => caches.match(req).then((r) => r || caches.match('index.html'))));
});
