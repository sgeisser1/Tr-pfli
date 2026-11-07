// Pflanze anlegen / Profil bearbeiten: Art (40 Profile, PFLANZENPROFILE.md / D-021), Name, Standort, Substrat, Topf,
// Zielbereich (Startwert je Art, ANNAHME), Giessverhalten (Regime A–D), Winteranpassung.
import { h, toast, fill } from './dom.js';
import { icon, plantArt } from './art.js';
import { seg, rangeBar, card } from './comp.js';

const REG = [['A', 'A · abtrocknen'], ['B', 'B · oben abtrocknen'], ['C', 'C · feucht halten'], ['D', 'D · Sonderfall']];
const CLS = { dry: 'trocken', medium: 'mittel', moist: 'feucht' };

export default async function edit(el, ctx) {
  const id = ctx.match[1] ? Number(ctx.match[1]) : null;
  const p = id ? await ctx.api.get(`/plants/${id}`)
    : { name: '', species: 'generic', substrate: 'erde', threshold_pct: 30, upper_pct: 75, location: '', pot: { diameter_cm: 14, material: 'kunststoff', drainage: true }, notes: '', regime: null, winter_factor: null };
  const f = { ...p, pot: { ...(p.pot || {}) }, regimeOwn: id && p.regime && (ctx.species.find((x) => x.key === p.species) || {}).regime !== p.regime ? p.regime : null };
  const preview = h('div.ed-prev');
  const rb = h('div');
  const spInfo = h('div.sp-info');
  const lo = h('input.input', { type: 'number', min: 0, max: 95, value: f.threshold_pct, 'aria-label': 'Giessschwelle' });
  const hi = h('input.input', { type: 'number', min: 5, max: 100, value: f.upper_pct ?? 100, 'aria-label': 'Obergrenze' });
  const wf = h('input.input', { type: 'number', min: 0.1, max: 1, step: 0.05, value: f.winter_factor ?? '', placeholder: 'aus der Art', 'aria-label': 'Winterfaktor' });
  const spOf = () => ctx.species.find((x) => x.key === f.species);
  const upd = () => {
    f.threshold_pct = Number(lo.value);
    f.upper_pct = Number(hi.value);
    const sp = spOf();
    fill(rb, rangeBar(p.latest ? p.latest.moisture_pct : null, f.threshold_pct, f.upper_pct, 'lg'));
    fill(preview, plantArt((sp && sp.illustration) || f.species, { size: 150, state: 'ok' }));
    fill(spInfo, ...(sp ? [
      h('p', null, h('strong', null, sp.name), sp.latin ? h('em', null, ` ${sp.latin}`) : null),
      h('p.small', null, h('span.pill', null, `Regime ${sp.regime || '–'}`), sp.water_class ? h('span.pill', null, CLS[sp.water_class]) : null, ' ', sp.regime_text || ''),
      sp.dryness ? h('p.small', null, 'Laut Quelle: ', sp.dryness) : null,
      sp.winter ? h('p.small.muted', null, 'Winter: ', sp.winter) : null,
      h('p.small.muted', null, sp.start_range.lower_pct != null ? `Startwert: giessen unter ${sp.start_range.lower_pct} %, zu nass über ${sp.start_range.upper_pct} % (erst 48 h nach dem Giessen geprüft). ${sp.start_note || ''}`
        : 'Sonderfall: Der Feuchteindex ist hier nur eingeschränkt aussagekräftig.')] : []));
  };
  lo.addEventListener('input', upd);
  hi.addEventListener('input', upd);

  // Artenwahl mit Suche (40 Profile)
  const q = h('input.input', { type: 'search', placeholder: 'Art suchen (z. B. Monstera, Ficus, Kaktus)', 'aria-label': 'Art suchen' });
  const picker = h('div.species', { role: 'radiogroup', 'aria-label': 'Art' });
  const drawPicker = () => {
    const term = q.value.trim().toLowerCase();
    const list = ctx.species.filter((sp) => !term || sp.name.toLowerCase().includes(term) || (sp.latin || '').toLowerCase().includes(term) || sp.key === f.species);
    fill(picker, ...list.map((sp) => {
      const b = h('button.sp-i', { type: 'button', role: 'radio', 'aria-checked': String(sp.key === f.species) },
        plantArt(sp.illustration || sp.key, { size: 52, sensor: false }), h('span', null, sp.name), h('span.sp-r', null, sp.regime || ''));
      b.addEventListener('click', () => {
        f.species = sp.key;
        for (const x of picker.children) x.setAttribute('aria-checked', String(x === b));
        if (!id || window.confirm('Startwerte dieser Art übernehmen (Schwelle, Obergrenze)?')) {
          if (sp.start_range.lower_pct != null) { lo.value = sp.start_range.lower_pct; hi.value = sp.start_range.upper_pct; }
        }
        upd();
      });
      return b;
    }));
  };
  q.addEventListener('input', drawPicker);
  drawPicker();

  const name = h('input.input', { value: f.name, maxlength: 40, placeholder: 'z. B. Monstera am Fenster', 'aria-label': 'Name' });
  const loc = h('input.input', { value: f.location || '', maxlength: 40, placeholder: 'z. B. Fenster Süd', 'aria-label': 'Standort' });
  const dia = h('input.input', { type: 'number', min: 4, max: 120, value: f.pot.diameter_cm ?? '', 'aria-label': 'Topfdurchmesser' });
  const mat = h('select.input', { 'aria-label': 'Topfmaterial' }, [['kunststoff', 'Kunststoff'], ['ton', 'Ton'], ['keramik', 'Keramik'], ['andere', 'anderes']].map(([v, t]) => h('option', { value: v, selected: v === f.pot.material }, t)));
  const notes = h('textarea.input', { maxlength: 200, rows: 2, 'aria-label': 'Notiz' }, f.notes || '');
  const regSel = h('select.input', { 'aria-label': 'Giessverhalten' }, h('option', { value: '' }, 'wie die Art'), REG.map(([v, t]) => h('option', { value: v, selected: v === f.regimeOwn }, t)));

  const submit = async () => {
    const body = { name: name.value.trim(), species: f.species, substrate: f.substrate, threshold_pct: f.threshold_pct, upper_pct: f.upper_pct, location: loc.value.trim(),
      pot: { diameter_cm: dia.value ? Number(dia.value) : null, material: mat.value, drainage: true }, notes: notes.value,
      regime: regSel.value || null, winter_factor: wf.value ? Number(wf.value) : null };
    try {
      const r = id ? await ctx.api.patch(`/plants/${id}`, body) : await ctx.api.post('/plants', body);
      toast('Profil gesichert', 'ok');
      ctx.go(`/pflanze/${r.id}`);
    } catch (e) { toast(e.message, 'err'); }
  };
  const del = id ? h('button.btn.ghost.sm', { type: 'button', onclick: async () => {
    if (!window.confirm(`„${p.name}“ löschen? Der Sensor wird frei, Messwerte bleiben beim Sensor.`)) return;
    try { await ctx.api.del(`/plants/${id}`); toast('Gelöscht', 'ok'); ctx.go('/'); } catch (e) { toast(e.message, 'err'); }
  } }, icon('trash'), 'Pflanze löschen') : null;
  el.append(
    h('header.ph.ph-detail', null, h('a.iconbtn', { href: id ? `#/pflanze/${id}` : '#/', 'aria-label': 'Zurück' }, icon('back')),
      h('div.ph-text', null, h('p.kicker', null, id ? p.name : 'Neue Pflanze'), h('h1', null, 'Profil')),
      h('button.btn.primary', { type: 'button', onclick: submit }, icon('check'), 'Sichern')),
    h('div.editgrid', null,
      h('div', null, card('Art', q, picker, spInfo),
        card('Feuchte-Zielbereich', rb, h('div.row2', null, h('label.field', null, 'Giessen unter (%)', lo), h('label.field', null, 'Zu nass über (%)', hi)),
          h('div.row2', null, h('label.field', null, 'Giessverhalten', regSel), h('label.field', null, 'Winterfaktor (Nov–Feb)', wf)),
          h('p.small.muted', null, 'Alle Prozentwerte sind Startwerte (ANNAHME). Nach 3–4 Giesszyklen an deine Pflanze anpassen.'))),
      h('div', null, h('section.card.ed-card', null, preview,
        h('label.field', null, 'Name', name), h('label.field', null, 'Standort', loc),
        h('div.field', null, h('span', null, 'Substrat'), seg([['erde', 'Erde'], ['granulat', 'Granulat']], f.substrate, (v) => { f.substrate = v; }, 'Substrat')),
        h('div.row2', null, h('label.field', null, 'Topf Ø (cm)', dia), h('label.field', null, 'Material', mat)),
        h('label.field', null, 'Notiz', notes), del))));
  upd();
  return null;
}
