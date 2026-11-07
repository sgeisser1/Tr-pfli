// Anmelden bzw. Ersteinrichtung (REQ-SAF-NET-01): kein Standardpasswort, Sperre nach Fehlversuchen.
import { h, field, toast } from '../ui.js';

export default async function login(main, ctx) {
  const st = await ctx.api.refreshAuth();
  ctx.updateSession();
  const back = ctx.params.zurueck && ctx.params.zurueck.startsWith('/') ? ctx.params.zurueck : '/';
  if (st.logged_in) {
    ctx.go(back);
    return;
  }
  const msg = h('p.err-text.status-line');
  let lockTimer = null;

  function lockout(sec, btn) {
    clearInterval(lockTimer);
    let left = sec;
    btn.disabled = true;
    const tick = () => {
      msg.textContent = `Zu viele Fehlversuche. Nächster Versuch in ${left} s.`;
      if (left-- <= 0) {
        clearInterval(lockTimer);
        btn.disabled = false;
        msg.textContent = '';
      }
    };
    tick();
    lockTimer = setInterval(tick, 1000);
  }

  if (st.setup_required) {
    const code = h('input', { type: 'text', inputmode: 'numeric', autocomplete: 'one-time-code', placeholder: '123-456', maxlength: 7, required: true });
    const pw1 = h('input', { type: 'password', autocomplete: 'new-password', minlength: 10, required: true });
    const pw2 = h('input', { type: 'password', autocomplete: 'new-password', minlength: 10, required: true });
    const btn = h('button.primary', { type: 'submit' }, 'Passwort setzen');
    main.replaceChildren(h('h1', null, 'Gateway einrichten'),
      h('form.card', { onsubmit: async (ev) => {
        ev.preventDefault();
        if (pw1.value !== pw2.value) { msg.textContent = 'Die Passwörter stimmen nicht überein.'; return; }
        try {
          await ctx.api.setup(code.value.trim(), pw1.value);
          ctx.updateSession();
          toast('Eingerichtet. Willkommen bei fluidi!');
          ctx.go('/koppeln');
        } catch (e) {
          if (e.code === 'locked') lockout(e.retryAfter || 60, btn);
          else msg.textContent = e.message;
        }
      } },
      h('p', null, 'Das Gateway hat noch kein Passwort. Den 6-stelligen Einrichtungscode zeigt das Einrichtungsprogramm am PC (USB) an.'),
      field('Einrichtungscode', code),
      field('Neues Passwort', pw1, 'Mindestens 10 Zeichen. Es gibt kein Standardpasswort.'),
      field('Passwort wiederholen', pw2),
      msg, btn));
    code.focus();
    return { cleanup: () => clearInterval(lockTimer) };
  }

  const pw = h('input', { type: 'password', autocomplete: 'current-password', required: true });
  const remember = h('input', { type: 'checkbox', checked: true });
  const btn = h('button.primary', { type: 'submit' }, 'Anmelden');
  main.replaceChildren(h('h1', null, 'Anmelden'),
    h('form.card', { onsubmit: async (ev) => {
      ev.preventDefault();
      try {
        await ctx.api.login(pw.value, remember.checked);
        ctx.updateSession();
        ctx.go(back);
      } catch (e) {
        pw.value = '';
        if (e.code === 'locked') lockout(e.retryAfter || 60, btn);
        else msg.textContent = e.message;
      }
    } },
    h('p.muted', null, 'Anschauen geht ohne Anmeldung. Für Änderungen, Koppeln, Kalibrieren und Updates braucht es das Passwort.'),
    field('Passwort', pw),
    h('label.check', null, remember, 'Auf diesem Gerät angemeldet bleiben (30 Tage)'),
    msg, btn,
    h('p.muted.small', null, 'Passwort vergessen? Gateway per USB mit dem PC verbinden und im Einrichtungsprogramm „Passwort zurücksetzen“ wählen. Daten bleiben erhalten.')));
  if (st.lockout && st.lockout.locked) lockout(st.lockout.retry_after_s, btn);
  pw.focus();
  return { cleanup: () => clearInterval(lockTimer) };
}
