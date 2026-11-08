// fluidi PWA (Stil A „Frost“, D-020) – Shell: Hell/Dunkel/Automatisch, Navigation, Router, Anmeldung,
// Live-Ereignisse (SSE), Zähler am App-Symbol (Badging API), Service Worker. Strikt lokal (REQ-APP-09).
// URL-Parameter: ?kiosk=1 (nur Dashboard), ?mode=light|dark|auto, ?shot=1 (Screenshots ohne SSE).
import * as api from './api.js';
import { h, sheet, toast } from './dom.js';
import { icon, dropChar } from './art.js';
import { stateOf, waterNow } from './comp.js';
import home from './home.js';
import plant from './plant.js';
import room from './room.js';
import dash from './dash.js';
import stats from './stats.js';
import settings from './settings.js';
import edit from './edit.js';
import { loginPage, setupPage } from './login.js';
import pair from './pair.js';
import calibrate from './calibrate.js';
import sensors from './sensors.js';
import data from './data.js';
import system from './system.js';

const SCHEME = { light: '#EAF4FB', dark: '#0B1420' };
const root = document.documentElement;
const qs = new URLSearchParams(location.search);
const store = {
  get: (k) => { try { return localStorage.getItem('fluidi-' + k); } catch (_) { return null; } },
  set: (k, v) => { try { localStorage.setItem('fluidi-' + k, v); } catch (_) { /* privat */ } },
};
const mq = window.matchMedia('(prefers-color-scheme: dark)');

/** Hell/Dunkel/Automatisch, je Gerät gespeichert (F-11). */
export function setMode(mode) {
  if (mode) { root.dataset.mode = mode; store.set('mode', mode); }
  const scheme = root.dataset.mode === 'auto' ? (mq.matches ? 'dark' : 'light') : root.dataset.mode;
  root.dataset.scheme = scheme;
  document.querySelector('meta[name=theme-color]').setAttribute('content', SCHEME[scheme]);
}
root.dataset.mode = qs.get('mode') || store.get('mode') || 'auto';
setMode();
mq.addEventListener('change', () => setMode());
if (qs.get('shot')) root.dataset.shot = '1';
if (qs.get('kiosk')) root.dataset.kiosk = '1';

const routes = [
  [/^\/$/, home, 'home'],
  [/^\/pflanze\/(\d+)$/, plant, 'home'],
  [/^\/pflanze\/(\d+)\/profil$/, edit, 'home'],
  [/^\/pflanze\/(\d+)\/kalibrieren$/, calibrate, 'home'],
  [/^\/neu$/, edit, 'home'],
  [/^\/raum$/, room, 'room'],
  [/^\/statistik$/, stats, 'stats'],
  [/^\/einstellungen$/, settings, 'settings'],
  [/^\/koppeln$/, pair, 'settings'],
  [/^\/sensoren$/, sensors, 'settings'],
  [/^\/daten$/, data, 'settings'],
  [/^\/system$/, system, 'settings'],
  [/^\/dashboard$/, dash, 'dash'],
  [/^\/anmelden$/, loginPage, 'login'],
  [/^\/einrichten$/, setupPage, 'login'],
];

const main = document.getElementById('main');
const live = api.stream();
let current = null;
let species = [];

export const ctx = {
  api,
  live,
  go(path) { if (location.hash === '#' + path) render(); else location.hash = '#' + path; },
  refresh: () => render(true),
  speciesName: (k) => (species.find((x) => x.key === k) || {}).name || '',
  get species() { return species; },
  async loadSpecies() { if (!species.length) species = await api.get('/species'); return species; },
  setMode,
  badge,
};

function nav() {
  const link = (href, key, ic, text) => h('a.nav-a', { href, 'data-nav': key }, h('span.nav-ic', null, icon(ic)), h('span.nav-t', null, text));
  return h('nav.nav', { 'aria-label': 'Hauptnavigation' },
    h('a.brand', { href: '#/', 'aria-label': 'fluidi – Übersicht' },
      h('img.logo-l', { src: 'img/logo.svg', alt: 'fluidi', width: 116, height: 44 }), h('img.logo-d', { src: 'img/logo-dunkel.svg', alt: 'fluidi', width: 116, height: 44 })),
    h('div.nav-links', null,
      link('#/', 'home', 'plants', 'Pflanzen'),
      link('#/raum', 'room', 'room', 'Raum'),
      link('#/statistik', 'stats', 'stats', 'Statistik'),
      link('#/einstellungen', 'settings', 'settings', 'Einstellungen')),
    h('a.nav-dash', { href: '#/dashboard', 'data-nav': 'dash' }, icon('tv'), h('span', null, 'Dashboard')),
    h('button.fab', { type: 'button', 'aria-label': 'Gegossen eintragen', onclick: waterSheet }, icon('drop'), h('span.fab-t', null, 'Gegossen')));
}

/** Schnellaktion „Gegossen“ (häufigste Aktion, eine Hand): Pflanze wählen, durstige zuerst. */
async function waterSheet() {
  const plants = await api.get('/plants');
  plants.sort((a, b) => (stateOf(b).key === 'dry') - (stateOf(a).key === 'dry') || (a.forecast?.days ?? 99) - (b.forecast?.days ?? 99));
  if (!plants.length) { toast('Noch keine Pflanzen'); return; }
  await sheet((close) => h('div.stack', null,
    h('h2', null, 'Welche Pflanze hast du gegossen?'),
    h('div.pick', null, plants.map((p) => {
      const st = stateOf(p);
      return h('button.pick-i', { type: 'button', onclick: async (ev) => { close(true); await waterNow(p, ctx, ev.currentTarget); } },
        dropChar(p.mood, { pct: p.latest?.moisture_pct, state: st.drop, size: 30, animate: false }),
        h('span.pick-n', null, p.name), h(`span.pick-s.k-${st.key}`, null, st.text));
    }))));
}

/** Zähler am App-Symbol (Badging API, lokal; Android/Chrome installiert). */
export async function badge(plants) {
  try {
    const st = api.authState();
    if (!('setAppBadge' in navigator) || !st || !st.logged_in) return;
    const n = plants.filter((p) => p.status.needs_water && !p.status.stale).length;
    if (n) await navigator.setAppBadge(n); else await navigator.clearAppBadge();
  } catch (_) { /* nicht unterstützt */ }
}

async function render(keep) {
  const raw = location.hash.slice(1) || '/';
  const [path, q] = raw.split('?');
  for (const [rx, view, key] of routes) {
    const m = rx.exec(path);
    if (!m) continue;
    document.querySelectorAll('[data-nav]').forEach((a) => (a.dataset.nav === key ? a.setAttribute('aria-current', 'page') : a.removeAttribute('aria-current')));
    root.dataset.page = key;
    if (current && current.cleanup) current.cleanup();
    current = null;
    const y = window.scrollY;
    if (!keep) main.replaceChildren(h('div.loading', null, dropChar('ok', { pct: 60, size: 48, label: 'lädt' })));
    try {
      if (!['login'].includes(key)) await ctx.loadSpecies();
      const frag = h('div.page');
      current = (await view(frag, { ...ctx, params: Object.fromEntries(new URLSearchParams(q || '')), match: m })) || null;
      main.replaceChildren(frag);
      window.scrollTo(0, keep ? y : 0);
    } catch (e) {
      console.error(e);
      main.replaceChildren(h('section.card.empty', null, dropChar('confused', { size: 72 }), h('h2', null, 'Das hat nicht geklappt'),
        h('p', null, e.message || String(e)), h('button.btn.primary', { type: 'button', onclick: () => render() }, 'Nochmals versuchen')));
    }
    return;
  }
  main.replaceChildren(h('section.card.empty', null, dropChar('confused', { size: 72 }), h('h2', null, 'Seite nicht gefunden'), h('a.btn.ghost', { href: '#/' }, 'Zur Übersicht')));
}

async function boot() {
  document.getElementById('app').prepend(nav());
  let st = null;
  try { st = await api.refreshAuth(); } catch (e) { toast(e.message, 'err'); }
  if (st && st.logged_in) api.offerTime();   // Gateway ohne gültige Zeit übernimmt die Browserzeit (REQ-GW-09)
  api.setHooks({ onAuthRequired: () => ctx.go('/anmelden?zurueck=' + encodeURIComponent(location.hash.slice(1) || '/')) });
  if (st && st.setup_required && !location.hash.startsWith('#/einrichten')) location.hash = '#/einrichten';
  else if (st && !st.logged_in && !st.public_read && !location.hash.startsWith('#/anmelden') && !location.hash.startsWith('#/dashboard')) {
    location.hash = '#/anmelden?zurueck=' + encodeURIComponent(location.hash.slice(1) || '/');
  }
  window.addEventListener('hashchange', () => render());
  await render();
  if (!root.dataset.shot) setTimeout(() => live.connect(), 1500);
  live.on('plant', () => { if (['home', 'dash'].includes(root.dataset.page)) render(true); });
  live.on('plant_deleted', () => { if (root.dataset.page === 'home') render(true); });
  if ('serviceWorker' in navigator && !root.dataset.shot) {
    navigator.serviceWorker.register('sw.js').catch(() => { /* ohne sicheren Kontext (HTTP) nicht verfügbar */ });
  }
}
boot();
