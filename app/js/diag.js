// Sensor-Diagnose und Firmware-Kennung (GATEWAY_API.md Kap. 5.10, TESTFIRMWARE.md Kap. 3). Ohne DOM: in node testbar.
// Dekodiert wird nur im Gateway (firmware/gateway/fluidi_gw/sensordiag.py, wie scripts/testfw_eval.py); hier nur Anzeige.

const TF_NAME = /^fl-tf([1-9])-[0-9A-Fa-f]{4}$/;

/** Testfirmware TF-n (0 = Serie). Gateway liefert `testfw`; ältere Gateways nicht -> Name/Build selbst prüfen. */
export function testfwOf(s) {
  if (!s) return 0;
  if (Number.isInteger(s.testfw) && s.testfw > 0) return s.testfw;
  const m = TF_NAME.exec(s.adv_name || '');
  if (m) return Number(m[1]);
  const b = s.fw_build;
  if (Number.isInteger(b) && b >= 9000 && b <= 9999 && Math.floor(b / 100) % 10 >= 1 && Math.floor(b / 100) % 10 <= 4) return Math.floor(b / 100) % 10;
  return 0;
}

/** "1.0.3 · Build 12" (Build fehlt bei Sensoren, die seit dem Gateway-Update noch keinen Kontakt hatten). */
export function fwLabel(s) {
  const v = (s && s.fw_version) || '?';
  return s && Number.isInteger(s.fw_build) ? `${v} · Build ${s.fw_build}` : v;
}

const RESET_DE = { power_on: 'Einschalten', pin_reset: 'Reset-Pin', watchdog: 'Watchdog', software: 'Software (Update/Neustart)', brownout: 'Brownout', hardfault: 'Absturz', undervoltage: 'Unterspannung' };

/** Zeilen [Bezeichnung, Wert] für die Anzeige eines SensorDiag-Objekts (openapi.yaml). */
export function diagRows(d) {
  const rows = [];
  const i = d.info;
  if (i) {
    rows.push(['Firmware', `${i.fw} · Build ${i.fw_build}`]);
    rows.push(['Hardware', `0x${Number(i.hw_rev).toString(16).toUpperCase().padStart(2, '0')}`]);
    rows.push(['Starts', String(i.boot_id)]);
    rows.push(['Laufzeit', `${Math.round(i.uptime_s / 3600)} h`]);
    rows.push(['Neustartgrund', RESET_DE[i.reset_reason] || String(i.reset_reason)]);
    if (i.last_error) rows.push(['Letzter Fehler', `0x${i.last_error.toString(16).toUpperCase().padStart(2, '0')} ${i.last_error_name || ''}`.trim()]);
    rows.push(['Batterie', `${i.vbat_load_mv} mV unter Last · ${i.vbat_rest_mv} mV Ruhe`]);
    rows.push(['Ladung', `${(i.charge_uc / 1e6).toFixed(2)} C seit Zellwechsel`]);
    rows.push(['Zähler', `${i.meas} Messungen · ${i.adv} Adv. · ${i.conn} Verb. · LED ${i.led_ms} ms`]);
  } else rows.push(['INFO', 'keine Antwort']);
  const g = d.diag;
  if (g) {
    rows.push(['Neustarts', `Watchdog ${g.wdt_resets} · Brownout ${g.brownouts}`]);
    rows.push(['Weitere', `Auth-Fehler ${g.auth_fail} · Taste klemmt ${g.button_stuck}`]);
    rows.push(['Fehlerprotokoll', g.entries.length ? g.entries.map((e) => `${e.name} (${e.detail}) Start ${e.boot_id}`).join(', ') : 'leer']);
    const t = g.tf;
    if (t) {
      rows.push([`TF-${t.variant}`, `VDD min ${t.vdd_min} mV (gesamt ${t.vdd_min_ever}) · Ruhe ${t.vbat_rest} mV`]);
      rows.push(['Flash-Ops', `seit Start ${t.flash_ops_boot} · bis 1. Messung ${t.flash_ops_ready} · Abschaltungen ${t.backoffs}`]);
      if (t.variant === 1 || t.tf1_trig) rows.push(['TF-1', `ausgelöst ${t.tf1_trig} ×`]);
      if (t.variant === 2 || t.tf2_trig) rows.push(['TF-2', `${t.tf2_mode_txt} · Neustarts ${t.tf2_cycles} · Ops/Zyklus ${t.tf2_max_ops} · Abschaltstart ${t.tf2_sd_ops}`]);
      if (t.variant === 3 || t.tf3_reads) rows.push(['TF-3', `${t.tf3_reads} Lesungen · ${t.tf3_err} I²C-Fehler · ${t.tf3_min_c ?? '–'}…${t.tf3_max_c ?? '–'} °C`]);
    }
  } else rows.push(['DIAG', 'keine Antwort']);
  for (const e of d.decode_errors || []) rows.push(['Hinweis', e]);
  return rows;
}

/** Dateiname für den JSON-Download, z. B. fluidi-diag-fluidi-AB12-20261109T143000Z.json */
export function diagFileName(d) {
  const t = String(d.t || '').replace(/[-:]/g, '').replace(/\.\d+/, '');
  return `fluidi-diag-${d.sensor_id}-${t || 'jetzt'}.json`;
}

/** Aufruf der Testplan-Auswertung für diesen Download (TESTFIRMWARE.md Kap. 8). */
export function evalCommand(d) {
  const exp = { 1: ' --expect tf1', 3: ' --expect tf3' }[d.testfw] || (d.testfw === 2 ? ' --expect tf2-late' : '');
  return `.venv/bin/python scripts/testfw_eval.py diag --file ${diagFileName(d)}${exp}`;
}
