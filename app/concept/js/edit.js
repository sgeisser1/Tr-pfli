// Pflanze anlegen / Profil bearbeiten: Art (Vorlage), Name, Substrat, Topf, Standort, Zielbereich.
import { h, toast } from './dom.js';
import { icon, plantArt } from './art.js';
import { pageHead, seg, rangeBar, card } from './comp.js';

export default async function edit(el, ctx) {
  const id = ctx.match[1] ? Number(ctx.match[1]) : null;
  const p = id ? await ctx.api.get(`/plants/${id}`) : { name: '', species: 'generic', substrate: 'erde', threshold_pct: 30, upper_pct: 70, location: '', pot: { diameter_cm: 14, material: 'kunststoff', drainage: true }, notes: '' };
  const f = { ...p, pot: { ...(p.pot || {}) } };
  const preview = h('div.ed-prev');
  const rb = h('div');
  const startNote = h('p.small.muted');
  const lo = h('input.input', { type: 'number', min: 0, max: 95, value: f.threshold_pct, 'aria-label': 'Giessschwelle' });
  const hi = h('input.input', { type: 'number', min: 5, max: 100, value: f.upper_pct ?? 100, 'aria-label': 'Obergrenze' });
  const upd = () => {
    f.threshold_pct = Number(lo.value);
    f.upper_pct = Number(hi.value);
    rb.replaceChildren(rangeBar(p.latest ? p.latest.moisture_pct : null, f.threshold_pct, f.upper_pct, 'lg'));
    preview.replaceChildren(plantArt(f.species, { size: 150, state: 'ok' }));
    const sp = ctx.species.find((x) => x.key === f.species);
    startNote.textContent = sp ? `Startwert „${sp.water_class_text}“: ${sp.start_range.lower_pct}–${sp.start_range.upper_pct} %. ${sp.note}` : '';
  };
  lo.addEventListener('input', upd);
  hi.addEventListener('input', upd);
  const picker = h('div.species', { role: 'radiogroup', 'aria-label': 'Art' }, ctx.species.map((sp) => {
    const b = h('button.sp-i', { type: 'button', role: 'radio', 'aria-checked': String(sp.key === f.species), onclick: () => {
      f.species = sp.key;
      for (const x of picker.children) x.setAttribute('aria-checked', String(x === b));
      if (!id) { lo.value = sp.start_range.lower_pct; hi.value = sp.start_range.upper_pct; }
      upd();
    } }, plantArt(sp.key, { size: 58, sensor: false }), h('span', null, sp.name));
    return b;
  }));
  const name = h('input.input', { value: f.name, maxlength: 40, placeholder: 'z. B. Monstera am Fenster', 'aria-label': 'Name' });
  const loc = h('input.input', { value: f.location || '', maxlength: 40, placeholder: 'z. B. Fenster Süd', 'aria-label': 'Standort' });
  const dia = h('input.input', { type: 'number', min: 4, max: 120, value: f.pot.diameter_cm ?? '', 'aria-label': 'Topfdurchmesser' });
  const mat = h('select.input', { 'aria-label': 'Topfmaterial' }, [['kunststoff', 'Kunststoff'], ['ton', 'Ton'], ['keramik', 'Keramik'], ['andere', 'anderes']].map(([v, t]) => h('option', { value: v, selected: v === f.pot.material }, t)));
  const notes = h('textarea.input', { maxlength: 200, rows: 2, 'aria-label': 'Notiz' }, f.notes || '');

  const submit = async () => {
    const body = { name: name.value.trim(), species: f.species, substrate: f.substrate, threshold_pct: f.threshold_pct, upper_pct: f.upper_pct, location: loc.value.trim(),
      pot: { diameter_cm: dia.value ? Number(dia.value) : null, material: mat.value, drainage: true }, notes: notes.value };
    try {
      const r = id ? await ctx.api.patch(`/plants/${id}`, body) : await ctx.api.post('/plants', body);
      toast('Profil gesichert', 'ok');
      ctx.go(`/pflanze/${r.id}`);
    } catch (e) { toast(e.message, 'err'); }
  };
  el.append(
    h('header.ph.ph-detail', null, h('a.iconbtn', { href: id ? `#/pflanze/${id}` : '#/', 'aria-label': 'Zurück' }, icon('back')),
      h('div.ph-text', null, h('p.kicker', null, id ? p.name : 'Neue Pflanze'), h('h1', null, 'Profil')),
      h('button.btn.primary', { type: 'button', onclick: submit }, icon('check'), 'Sichern')),
    h('div.editgrid', null,
      h('div', null, card('Art', picker, h('p.small.muted', null, 'Die Art bestimmt Bild und Startwert. Eigene Pflegeangaben kannst du jederzeit überschreiben.')),
        card('Feuchte-Zielbereich', rb, h('div.row2', null, h('label.field', null, 'Giessen unter (%)', lo), h('label.field', null, 'Zu nass über (%)', hi)), startNote)),
      h('div', null, h('section.card.ed-card', null, preview,
        h('label.field', null, 'Name', name), h('label.field', null, 'Standort', loc),
        h('div.field', null, h('span', null, 'Substrat'), seg([['erde', 'Erde'], ['granulat', 'Granulat']], f.substrate, (v) => { f.substrate = v; }, 'Substrat')),
        h('div.row2', null, h('label.field', null, 'Topf Ø (cm)', dia), h('label.field', null, 'Material', mat)),
        h('label.field', null, 'Notiz', notes),
        h('p.small.muted', null, 'Foto der Pflanze: geplant (Konzept Kap. 8).')))));
  upd();
}
