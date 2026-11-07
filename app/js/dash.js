// Dashboard-Modus in der App (Vollbild, Kiosk mit ?kiosk=1) – gleiche Darstellung wie die öffentliche Seite.
import { renderBoard } from './board.js';

export default async function dash(el, ctx) {
  const root = document.documentElement;
  const d = await ctx.api.get('/dashboard');
  const b = renderBoard(el, d, { closeHref: root.dataset.kiosk ? null : '#/' });
  root.dataset.dash = '1';
  const t = setInterval(async () => { try { b.update(await ctx.api.get('/dashboard')); } catch (_) { /* nächste Minute */ } }, 60_000);
  return { cleanup() { clearInterval(t); b.stop(); delete root.dataset.dash; } };
}
