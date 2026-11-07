// Öffentliches Dashboard (eigener HTTP-Port, nur lesen, ohne Anmeldung, D-020). Lädt nur GET /api/v1/dashboard.
import { h } from './dom.js';
import { renderBoard } from './board.js';

const root = document.documentElement;
const mq = window.matchMedia('(prefers-color-scheme: dark)');
const qs = new URLSearchParams(location.search);
const scheme = () => { root.dataset.scheme = qs.get('mode') === 'light' ? 'light' : qs.get('mode') === 'dark' || mq.matches ? 'dark' : 'light'; };
scheme();
mq.addEventListener('change', scheme);
root.dataset.dash = '1';
root.dataset.kiosk = '1';

const main = document.getElementById('main');
let board = null;
async function load() {
  try {
    const res = await fetch('api/v1/dashboard', { cache: 'no-store', credentials: 'omit' });
    if (!res.ok) throw new Error(res.status === 404 ? 'Das Dashboard ist ausgeschaltet.' : `Fehler ${res.status}`);
    const d = await res.json();
    if (!board) { main.replaceChildren(); board = renderBoard(main, d, {}); } else board.update(d);
  } catch (e) {
    if (!board) main.replaceChildren(h('div.card', null, h('h2', null, 'fluidi Dashboard'), h('p', null, e.message || 'Gateway nicht erreichbar')));
  }
}
load();
setInterval(load, 60_000);
