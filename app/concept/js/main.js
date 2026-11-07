// fluidi Entwürfe – Shell: Entwurf/Hell-Dunkel, Navigation, Router.
// Entwurf per URL: ?theme=frost|botanik|stele  ?mode=light|dark|auto  ?shot=1 (ohne Entwurfsschalter)  ?kiosk=1
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

export const THEMES = {
  frost: { name: 'fluidi Frost', short: 'A Frost', light: '#EAF4FB', dark: '#0B1420' },
  botanik: { name: 'fluidi Botanik', short: 'B Botanik', light: '#EEF3EA', dark: '#0D1812' },
  stele: { name: 'fluidi Stele', short: 'C Stele', light: '#EEEBE5', dark: '#22201D' },
};
const root = document.documentElement;
const qs = new URLSearchParams(location.search);
const store = {
  get: (k) => { try { return localStorage.getItem('fluidi-' + k); } catch (_) { return null; } },
  set: (k, v) => { try { localStorage.setItem('fluidi-' + k, v); } catch (_) { /* privat */ } },
};
const mq = window.matchMedia('(prefers-color-scheme: dark)');

export function setTheme(theme, mode) {
  if (theme && THEMES[theme]) { root.dataset.theme = theme; store.set('theme', theme); }
  if (mode) { root.dataset.mode = mode; store.set('mode', mode); }
  const scheme = root.dataset.mode === 'auto' ? (mq.matches ? 'dark' : 'light') : root.dataset.mode;
  root.dataset.scheme = scheme;
  const t = THEMES[root.dataset.theme];
  document.querySelector('meta[name=theme-color]').setAttribute('content', t[scheme]);
  document.querySelectorAll('[data-draft]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.draft === root.dataset.theme)));
}
setTheme(qs.get('theme') || store.get('theme') || 'frost', qs.get('mode') || store.get('mode') || 'auto');
mq.addEventListener('change', () => setTheme(null, root.dataset.mode));
if (qs.get('shot')) root.dataset.shot = '1';
if (qs.get('kiosk')) root.dataset.kiosk = '1';
if (qs.get('frame')) root.dataset.frame = '1'; // Geräterahmen der Screenshots: Statusleiste simulieren

const routes = [
  [/^\/$/, home, 'home'],
  [/^\/pflanze\/(\d+)$/, plant, 'home'],
  [/^\/pflanze\/(\d+)\/profil$/, edit, 'home'],
  [/^\/neu$/, edit, 'home'],
  [/^\/raum$/, room, 'room'],
  [/^\/statistik$/, stats, 'stats'],
  [/^\/einstellungen$/, settings, 'settings'],
  [/^\/dashboard$/, dash, 'dash'],
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
  setTheme,
  THEMES,
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

/** Schnellaktion „Gegossen“: Pflanze wählen, durstige zuerst. */
async function waterSheet() {
  const plants = (await api.get('/plants')).filter((p) => p.sensor_id || true);
  plants.sort((a, b) => (stateOf(b).key === 'dry') - (stateOf(a).key === 'dry') || (a.forecast?.days ?? 99) - (b.forecast?.days ?? 99));
  await sheet((close) => h('div.stack', null,
    h('h2', null, 'Welche Pflanze hast du gegossen?'),
    h('div.pick', null, plants.map((p) => {
      const st = stateOf(p);
      return h('button.pick-i', { type: 'button', onclick: async (ev) => { close(true); await waterNow(p, ctx, ev.currentTarget); } },
        dropChar(p.mood, { pct: p.latest?.moisture_pct, state: st.drop, size: 30, animate: false }),
        h('span.pick-n', null, p.name), h(`span.pick-s.k-${st.key}`, null, st.text));
    }))));
}

function draftSwitch() {
  const b = (k) => h('button', { type: 'button', 'data-draft': k, onclick: () => setTheme(k) }, THEMES[k].short);
  const m = (k, ic, lab) => h('button', { type: 'button', 'aria-label': lab, title: lab, onclick: () => setTheme(null, k) }, icon(ic));
  return h('div.draft', { role: 'group', 'aria-label': 'Entwurf wählen' }, h('span.draft-l', null, 'Entwurf'), b('frost'), b('botanik'), b('stele'),
    h('span.draft-sep'), m('light', 'sun', 'Hell'), m('dark', 'moon', 'Dunkel'), m('auto', 'auto', 'Automatisch'));
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
    if (!keep) main.replaceChildren(h('div.loading', null, dropChar('ok', { pct: 60, size: 48 })));
    try {
      const frag = document.createElement('div');
      frag.className = 'page';
      current = (await view(frag, { ...ctx, params: Object.fromEntries(new URLSearchParams(q || '')), match: m })) || null;
      main.replaceChildren(frag);
      if (keep) window.scrollTo(0, y);
      else window.scrollTo(0, 0);
    } catch (e) {
      console.error(e);
      main.replaceChildren(h('div.card', null, h('h2', null, 'Fehler'), h('p', null, e.message || String(e))));
    }
    return;
  }
  main.replaceChildren(h('div.card', null, h('h2', null, 'Seite nicht gefunden'), h('a', { href: '#/' }, 'Zur Übersicht')));
}

async function boot() {
  document.getElementById('app').prepend(nav());
  document.body.append(draftSwitch());
  setTheme(null, root.dataset.mode);
  try {
    await api.refreshAuth();
    species = await api.get('/species');
  } catch (e) {
    toast(e.message, 'err');
  }
  window.addEventListener('hashchange', () => render());
  await render();
  if (!root.dataset.shot) setTimeout(() => live.connect(), 2500); // offene SSE-Verbindung blockiert headless-Screenshots
  live.on('plant', () => { if (['home', 'dash'].includes(root.dataset.page)) render(true); });
}
boot();
