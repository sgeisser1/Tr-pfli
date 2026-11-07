// fluidi – DOM-Hilfen. Texte nur über textContent (kein innerHTML mit Daten, CSP ohne Inline-Styles).
const SVGNS = 'http://www.w3.org/2000/svg';

/** h('div.card#id', {attr, onclick}, ...kinder) */
export function h(tag, attrs, ...children) {
  const m = /^([a-z0-9-]+)((?:[.#][\w-]+)*)$/i.exec(tag);
  const el = document.createElement(m ? m[1] : tag);
  if (m && m[2]) for (const p of m[2].match(/[.#][\w-]+/g)) p[0] === '.' ? el.classList.add(p.slice(1)) : (el.id = p.slice(1));
  attrs && setAttrs(el, attrs);
  add(el, children);
  return el;
}

export function s(tag, attrs, ...children) {
  const el = document.createElementNS(SVGNS, tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else el.setAttribute(k, String(v));
  }
  add(el, children);
  return el;
}

function setAttrs(el, attrs) {
  for (const [k, v] of Object.entries(attrs)) {
    if (v === undefined || v === null || v === false) continue;
    if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className = v;
    else if (['value', 'checked', 'disabled', 'selected', 'hidden'].includes(k)) el[k] = v;
    else el.setAttribute(k, v === true ? '' : String(v));
  }
}

function add(el, children) {
  for (const c of children.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
}

let uid = 0;
export const nextId = (p = 'u') => `${p}${++uid}`;

const nf0 = new Intl.NumberFormat('de-CH', { maximumFractionDigits: 0 });
const nf1 = new Intl.NumberFormat('de-CH', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
export const fmt = {
  pct: (v) => (v == null ? '–' : nf0.format(Math.round(v))),
  n1: (v) => (v == null ? '–' : nf1.format(v)),
  n0: (v) => (v == null ? '–' : nf0.format(v)),
  temp: (v) => (v == null ? '–' : `${nf1.format(v)}°`),
  time: (iso) => new Date(iso).toLocaleTimeString('de-CH', { hour: '2-digit', minute: '2-digit' }),
  date: (iso) => new Date(iso).toLocaleDateString('de-CH', { day: 'numeric', month: 'short' }),
  dateTime: (iso) => new Date(iso).toLocaleString('de-CH', { weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }),
  weekday: (iso) => new Date(iso).toLocaleDateString('de-CH', { weekday: 'long' }),
  dur(s) {
    if (s == null) return '–';
    if (s < 3600) return `${Math.round(s / 60)} min`;
    if (s < 86400) return `${Math.round(s / 3600)} h`;
    return `${Math.round(s / 86400)} Tage`;
  },
  ago(iso, now = Date.now()) {
    const d = (now - Date.parse(iso)) / 1000;
    if (d < 90) return 'gerade eben';
    if (d < 3600) return `vor ${Math.round(d / 60)} min`;
    if (d < 86400) return `vor ${Math.round(d / 3600)} h`;
    const days = Math.round(d / 86400);
    return days === 1 ? 'gestern' : `vor ${days} Tagen`;
  },
  days(d) {
    if (d == null) return '–';
    if (d < 0.5) return 'heute';
    if (d < 1.5) return 'morgen';
    return `in ~${Math.round(d)} Tagen`;
  },
};

let toastT = null;
export function toast(msg, kind = '') {
  const t = document.getElementById('toast');
  t.replaceChildren(msg);
  t.className = 'toast show ' + kind;
  clearTimeout(toastT);
  toastT = setTimeout(() => (t.className = 'toast'), 3200);
}

/** Bottom-Sheet (Handy) bzw. Dialog (Desktop). build(close) liefert den Inhalt. */
export function sheet(build, cls = '') {
  const d = document.getElementById('sheet');
  return new Promise((resolve) => {
    let done = false;
    const close = (v) => {
      if (done) return;
      done = true;
      d.close();
      resolve(v);
    };
    d.className = 'sheet ' + cls;
    d.replaceChildren(h('div.sheet-grip', { 'aria-hidden': 'true' }), build(close));
    d.onclose = () => close(undefined);
    d.onclick = (ev) => { if (ev.target === d) close(undefined); };
    d.showModal();
  });
}

/** replaceChildren ohne null/undefined/false (sonst erschiene „null“ als Text). */
export function fill(el, ...children) {
  el.replaceChildren(...children.flat(Infinity).filter((c) => c !== null && c !== undefined && c !== false).map((c) => (c instanceof Node ? c : document.createTextNode(String(c)))));
  return el;
}
