// fluidi – App-Shell: Router, Anmeldung, Live-Ereignisse, Service Worker.
import * as api from './api.js';
import { h, dialog, toast, field } from './ui.js';
import overview from './views/overview.js';
import detail from './views/detail.js';
import edit from './views/edit.js';
import calibrate from './views/calibrate.js';
import pair from './views/pair.js';
import settings from './views/settings.js';
import firmware from './views/firmware.js';
import data from './views/data.js';
import login from './views/login.js';

const routes = [
  [/^\/$/, overview, 'overview'],
  [/^\/pflanze\/(\d+)$/, detail, 'overview'],
  [/^\/pflanze\/(\d+)\/bearbeiten$/, edit, 'overview'],
  [/^\/pflanze\/(\d+)\/kalibrieren$/, calibrate, 'overview'],
  [/^\/neu$/, edit, 'overview'],
  [/^\/koppeln$/, pair, 'pair'],
  [/^\/einstellungen$/, settings, 'settings'],
  [/^\/firmware$/, firmware, 'settings'],
  [/^\/daten$/, data, 'data'],
  [/^\/anmelden$/, login, null],
];

const main = document.getElementById('main');
const stream = api.openStream();
let current = null; // { cleanup }

export const ctx = {
  api,
  stream,
  go(path) {
    if (location.hash === '#' + path) render();
    else location.hash = '#' + path;
  },
  get auth() {
    return api.authState();
  },
  /** Für schreibende Seiten: true, wenn angemeldet, sonst Umleitung zur Anmeldung. */
  requireLogin() {
    const a = api.authState();
    if (a && a.logged_in) return true;
    ctx.go('/anmelden?zurueck=' + encodeURIComponent(location.hash.slice(1) || '/'));
    return false;
  },
  updateSession,
};

function updateSession() {
  const a = api.authState();
  const el = document.getElementById('session');
  if (!a) return;
  if (a.logged_in) {
    el.textContent = 'Abmelden';
    el.href = '#/abmelden';
  } else {
    el.textContent = a.setup_required ? 'Einrichten' : 'Anmelden';
    el.href = '#/anmelden';
  }
}

async function render() {
  const raw = location.hash.slice(1) || '/';
  const [path] = raw.split('?');
  if (path === '/abmelden') {
    await api.logout();
    updateSession();
    toast('Abgemeldet');
    ctx.go('/');
    return;
  }
  if (current && current.cleanup) current.cleanup();
  current = null;
  for (const [rx, view, nav] of routes) {
    const m = rx.exec(path);
    if (!m) continue;
    for (const a of document.querySelectorAll('[data-nav]')) {
      if (a.dataset.nav === nav) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    }
    const params = Object.fromEntries(new URLSearchParams(raw.split('?')[1] || ''));
    main.replaceChildren(h('p.muted', null, 'Lade …'));
    try {
      current = (await view(main, { ...ctx, params, match: m })) || null;
    } catch (e) {
      main.replaceChildren(h('div.card', null, h('h1', null, 'Fehler'), h('p.err-text', null, e.message || String(e)),
        h('a.btn.ghost', { href: '#/' }, 'Zur Übersicht')));
    }
    main.focus({ preventScroll: true });
    return;
  }
  main.replaceChildren(h('div.card', null, h('h1', null, 'Seite nicht gefunden'), h('a', { href: '#/' }, 'Zur Übersicht')));
}

function banner(text, err) {
  const b = document.getElementById('banner');
  b.textContent = text || '';
  b.classList.toggle('err', !!err);
  b.hidden = !text;
}

api.setHooks({
  onAuthRequired() {
    toast('Bitte anmelden', true);
    api.refreshAuth().then(updateSession).catch(() => null);
    ctx.go('/anmelden?zurueck=' + encodeURIComponent(location.hash.slice(1) || '/'));
  },
  onOffline(off) {
    banner(off ? 'Offline – angezeigt wird der letzte bekannte Stand.' : '', false);
  },
  // heikle Aktionen: Passwort erneut bestätigen (GATEWAY_API.md 3.3)
  onElevate() {
    return dialog((close) => {
      const pw = h('input', { type: 'password', autocomplete: 'current-password', required: true });
      const msg = h('p.err-text.status-line');
      const form = h('form', {
        onsubmit: async (ev) => {
          ev.preventDefault();
          try {
            await api.elevate(pw.value);
            close(true);
          } catch (e) {
            msg.textContent = e.message;
          }
        },
      },
      h('h2', null, 'Passwort bestätigen'),
      h('p.muted', null, 'Diese Aktion verändert das Gateway grundlegend. Bitte das Passwort erneut eingeben.'),
      field('Passwort', pw), msg,
      h('div.row', null, h('button.primary', { type: 'submit' }, 'Bestätigen'),
        h('button.ghost', { type: 'button', onclick: () => close(false) }, 'Abbrechen')));
      return form;
    });
  },
});

async function boot() {
  try {
    const st = await api.refreshAuth();
    updateSession();
    if (st.setup_required) {
      location.hash = '#/anmelden';
    }
    // Browserzeit anbieten, falls das Gateway keine gültige Zeit hat (REQ-GW-09)
    if (st.logged_in) {
      api.get('/system').then((s) => {
        if (s && s.time && !s.time.valid) api.post('/system/time', { epoch_ms: Date.now() }).catch(() => null);
      }).catch(() => null);
    }
  } catch (e) {
    banner(e.message, true);
  }
  // Live-Ereignisse erst nach dem ersten Bild öffnen (eine offene SSE-Verbindung
  // blockiert sonst headless-Screenshots mit --virtual-time-budget).
  setTimeout(() => stream.connect(), 2000);
  window.addEventListener('hashchange', render);
  render();
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('sw.js', { scope: './' }).catch((e) => console.warn('SW', e));
  }
}

boot();
