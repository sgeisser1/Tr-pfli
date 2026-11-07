// fluidi – kleine DOM-Hilfen. Texte immer über textContent (kein innerHTML mit Daten).
import { batteryBars } from './calc.js';

const SVG = 'http://www.w3.org/2000/svg';

/** h('div.card#x', {attrs/on*}, ...kinder) */
export function h(tag, attrs, ...children) {
  const m = /^([a-z0-9-]+)((?:[.#][\w-]+)*)$/i.exec(tag);
  const el = document.createElement(m ? m[1] : tag);
  if (m && m[2]) {
    for (const part of m[2].match(/[.#][\w-]+/g)) {
      if (part[0] === '.') el.classList.add(part.slice(1));
      else el.id = part.slice(1);
    }
  }
  applyAttrs(el, attrs);
  append(el, children);
  return el;
}

function applyAttrs(el, attrs) {
  if (!attrs) return;
  for (const [k, v] of Object.entries(attrs)) {
    if (v === undefined || v === null || v === false) continue;
    if (k.startsWith('on') && typeof v === 'function') el.addEventListener(k.slice(2), v);
    else if (k === 'class') el.className = v;
    else if (k === 'value' && 'value' in el) el.value = v;
    else if (k === 'checked' || k === 'disabled' || k === 'selected' || k === 'hidden' || k === 'required') el[k] = !!v;
    else el.setAttribute(k, v === true ? '' : String(v));
  }
}

function append(el, children) {
  for (const c of children.flat(Infinity)) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
}

export function svg(tag, attrs, ...children) {
  const el = document.createElementNS(SVG, tag);
  for (const [k, v] of Object.entries(attrs || {})) if (v !== undefined && v !== null) el.setAttribute(k, String(v));
  for (const c of children.flat()) if (c) el.append(c);
  return el;
}

/** Tropfen in Sensorgeometrie (Spitze oben, Kreisbauch), Farbe = LED-Zustand. */
export function drop(color = 'off', title) {
  const s = svg('svg', { viewBox: '0 0 10 15.2', class: `drop ${color}`, role: 'img', 'aria-label': title || '' },
    svg('path', { d: 'M5 0.2 L0.997 8.774 A4.4 4.4 0 1 0 9.003 8.774 Z' }));
  if (title) s.append(svg('title', {}, document.createTextNode(title)));
  return s;
}

export function batteryIcon(b) {
  const bars = b ? batteryBars(b.pct) : 0;
  const warn = b && b.state !== 'ok';
  const s = svg('svg', { viewBox: '0 0 22 12', class: `ico${warn ? ' warn' : ''}`, 'aria-hidden': 'true' });
  s.append(svg('rect', { x: 20, y: 3.5, width: 2, height: 5, class: 'on' }));
  for (let i = 0; i < 4; i++) s.append(svg('rect', { x: 0.5 + i * 4.9, y: 0.5, width: 4.2, height: 11, class: i < bars ? 'on' : '' }));
  return s;
}

export function signalIcon(sig) {
  const q = sig ? sig.quality : 0;
  const s = svg('svg', { viewBox: '0 0 18 14', class: 'sig', 'aria-hidden': 'true' });
  for (let i = 0; i < 4; i++) s.append(svg('rect', { x: i * 4.6, y: 10 - i * 3.2, width: 3.4, height: 4 + i * 3.2, class: i < q ? 'on' : '' }));
  return s;
}

const nf1 = new Intl.NumberFormat('de-CH', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const nf0 = new Intl.NumberFormat('de-CH', { maximumFractionDigits: 0 });
export const fmt = {
  pct: (v) => (v === null || v === undefined ? '–' : nf0.format(Math.round(v))),
  pct1: (v) => (v === null || v === undefined ? '–' : nf1.format(v)),
  temp: (v) => (v === null || v === undefined ? '–' : `${nf1.format(v)} °C`),
  mv: (v) => (v ? `${nf1.format(v / 1000)} V` : '–'),
  dateTime: (iso) => (iso ? new Date(iso).toLocaleString('de-CH', { dateStyle: 'short', timeStyle: 'short' }) : '–'),
  date: (iso) => (iso ? new Date(iso).toLocaleDateString('de-CH') : '–'),
  bytes: (n) => (n >= 1048576 ? `${nf1.format(n / 1048576)} MB` : `${nf0.format(n / 1024)} kB`),
};

export const SUBSTRATE = { erde: 'Erde', granulat: 'Granulat' };
export const STATE_TEXT = {
  ok: 'Feucht genug',
  dry: 'Giessen nötig',
  air: 'Sensor nicht in der Erde?',
  flooded: 'Zu nass / überflutet?',
  uncalibrated: 'Nicht kalibriert',
  invalid: 'Kalibrierung ungültig',
};

let toastTimer = null;
export function toast(msg, isErr = false) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.classList.toggle('err', !!isErr);
  t.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => (t.hidden = true), isErr ? 6000 : 3000);
}

/** Modaler Dialog; build(close) liefert den Inhalt, Rückgabe über close(value). */
export function dialog(build) {
  const d = document.getElementById('dialog');
  return new Promise((resolve) => {
    let done = false;
    const close = (v) => {
      if (done) return;
      done = true;
      d.close();
      resolve(v);
    };
    d.replaceChildren(build(close));
    d.onclose = () => close(undefined);
    d.showModal();
    const f = d.querySelector('input, button.primary, button');
    if (f) f.focus();
  });
}

export function confirmDialog(title, text, okLabel = 'OK', danger = false) {
  return dialog((close) =>
    h('div', null, h('h2', null, title), h('p', null, text),
      h('div.row', null,
        h(`button.${danger ? 'danger' : 'primary'}`, { onclick: () => close(true) }, okLabel),
        h('button.ghost', { onclick: () => close(false) }, 'Abbrechen'))));
}

/** Eingabefeld mit Label und Hinweis. */
export function field(label, input, hint) {
  const id = input.id || 'f' + Math.random().toString(36).slice(2, 8);
  input.id = id;
  return h('div.field', null, h('label', { for: id }, label), input, hint ? h('div.hint', null, hint) : null);
}

export function setBusy(btn, busy, label) {
  if (!btn) return;
  btn.disabled = busy;
  if (label) btn.textContent = label;
}
