// Anmelden und Ersteinrichtung (REQ-SAF-NET-01): kein Standardpasswort, Einrichtungscode nur lokal am Gateway,
// Sperre nach Fehlversuchen (GATEWAY_API 3.2).
import { h, toast } from './dom.js';
import { dropChar } from './art.js';

function lockout(msg, btn, sec) {
  let left = sec;
  btn.disabled = true;
  const t = setInterval(() => {
    msg.textContent = `Zu viele Fehlversuche. Nächster Versuch in ${left} s.`;
    if (left-- <= 0) { clearInterval(t); btn.disabled = false; msg.textContent = ''; }
  }, 1000);
  return t;
}

const shell = (title, sub, ...content) => h('section.card.auth', null,
  h('div.auth-drop', null, dropChar('happy', { pct: 70, size: 88, label: 'fluidi' })),
  h('img.logo-l.auth-logo', { src: 'img/logo.svg', alt: 'fluidi', width: 140, height: 53 }),
  h('img.logo-d.auth-logo', { src: 'img/logo-dunkel.svg', alt: 'fluidi', width: 140, height: 53 }),
  h('h1', null, title), sub ? h('p.muted', null, sub) : null, ...content);

export async function loginPage(el, ctx) {
  const st = await ctx.api.refreshAuth();
  const back = ctx.params.zurueck && ctx.params.zurueck.startsWith('/') ? ctx.params.zurueck : '/';
  if (st.setup_required) { ctx.go('/einrichten'); return null; }
  if (st.logged_in) { ctx.go(back); return null; }
  const pw = h('input.input', { type: 'password', autocomplete: 'current-password', required: true, 'aria-label': 'Passwort', placeholder: 'Passwort' });
  const remember = h('input', { type: 'checkbox', checked: true });
  const msg = h('p.err');
  const btn = h('button.btn.primary', { type: 'submit' }, 'Anmelden');
  let timer = null;
  el.append(shell('Willkommen zurück', 'Bitte melde dich an. Das Passwort bleibt auf dem Gateway.',
    h('form.stack', {
      onsubmit: async (ev) => {
        ev.preventDefault();
        try {
          await ctx.api.login(pw.value, remember.checked);
          ctx.go(back);
        } catch (e) {
          pw.value = '';
          if (e.code === 'locked') timer = lockout(msg, btn, e.retryAfter || 60);
          else msg.textContent = e.message;
        }
      },
    }, pw, h('label.check', null, remember, 'Auf diesem Gerät angemeldet bleiben (30 Tage)'), msg, btn),
    h('p.small.muted', null, 'Passwort vergessen? Am Gateway per SSH „fluidi_gw reset-password“ ausführen (Anleitung GATEWAY_SETUP.md). Die Daten bleiben erhalten.'),
    h('a.btn.ghost.sm', { href: '#/dashboard' }, 'Nur Dashboard ansehen')));
  if (st.lockout && st.lockout.locked) timer = lockout(msg, btn, st.lockout.retry_after_s);
  queueMicrotask(() => pw.focus());
  return { cleanup: () => clearInterval(timer) };
}

export async function setupPage(el, ctx) {
  const st = await ctx.api.refreshAuth();
  if (!st.setup_required) { ctx.go('/'); return null; }
  const code = h('input.input', { inputmode: 'numeric', autocomplete: 'one-time-code', placeholder: '123-456', maxlength: 7, required: true, 'aria-label': 'Einrichtungscode' });
  const pw1 = h('input.input', { type: 'password', autocomplete: 'new-password', minlength: 10, required: true, 'aria-label': 'Neues Passwort' });
  const pw2 = h('input.input', { type: 'password', autocomplete: 'new-password', minlength: 10, required: true, 'aria-label': 'Passwort wiederholen' });
  const msg = h('p.err');
  const btn = h('button.btn.primary', { type: 'submit' }, 'Passwort setzen');
  let timer = null;
  el.append(shell('Hallo, ich bin fluidi', 'Das Gateway hat noch kein Passwort. Den 6-stelligen Einrichtungscode hat das Installationsskript angezeigt.',
    h('form.stack', {
      onsubmit: async (ev) => {
        ev.preventDefault();
        if (pw1.value !== pw2.value) { msg.textContent = 'Die Passwörter stimmen nicht überein.'; return; }
        try {
          await ctx.api.setup(code.value.trim(), pw1.value);
          toast('Eingerichtet – jetzt den ersten Sensor koppeln', 'ok');
          ctx.go('/koppeln');
        } catch (e) {
          if (e.code === 'locked') timer = lockout(msg, btn, e.retryAfter || 60);
          else msg.textContent = e.message;
        }
      },
    }, h('label.field', null, 'Einrichtungscode', code), h('label.field', null, 'Neues Passwort (mind. 10 Zeichen)', pw1),
    h('label.field', null, 'Passwort wiederholen', pw2), msg, btn),
    h('p.small.muted', null, 'Tipp: In Chrome auf dem Handy „Zum Startbildschirm hinzufügen“ – dann startet fluidi wie eine App.')));
  queueMicrotask(() => code.focus());
  return { cleanup: () => clearInterval(timer) };
}
