// Unit-Tests Diagnose-/Firmware-Anzeige (app/js/diag.js), node --test.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { testfwOf, fwLabel, diagRows, diagFileName, evalCommand, imageTestfw, tfLabel } from '../js/diag.js';

test('testfwOf: Gateway-Feld, Gerätename fl-tf<n>-, Build 9<n>xx (TESTFIRMWARE Kap. 3)', () => {
  assert.equal(testfwOf({ testfw: 2 }), 2);
  assert.equal(testfwOf({ adv_name: 'fl-tf3-AB12' }), 3);
  assert.equal(testfwOf({ adv_name: 'fluidi-AB12', fw_build: 9401 }), 4);
  assert.equal(testfwOf({ adv_name: 'fluidi-AB12', fw_build: 12 }), 0);
  assert.equal(testfwOf({ fw_build: 9501 }), 0);         // nur TF-1..4
  assert.equal(testfwOf({ fw_build: 8999 }), 0);
  assert.equal(testfwOf(null), 0);
});

test('fwLabel zeigt die Build-Nummer (O-3)', () => {
  assert.equal(fwLabel({ fw_version: '1.0.3', fw_build: 12 }), '1.0.3 · Build 12');
  assert.equal(fwLabel({ fw_version: '1.0.3', fw_build: null }), '1.0.3');
});

const SERIE = {
  sensor_id: 'fluidi-AB12', t: '2026-11-09T14:30:00Z', testfw: 0, decode_errors: [],
  info: { fw: '1.0.3', fw_build: 12, hw_rev: 10, boot_id: 4, uptime_s: 7200, reset_reason: 'watchdog', last_error: 0x50, last_error_name: 'WDT_RESET', vbat_load_mv: 2950, vbat_rest_mv: 2990, charge_uc: 812000, meas: 3, adv: 9, conn: 2, led_ms: 40 },
  diag: { entries: [{ code: 0x50, name: 'WDT_RESET', detail: 0, boot_id: 3, uptime_s: 1 }], wdt_resets: 1, brownouts: 0, auth_fail: 0, button_stuck: 0, tf: null },
};

test('diagRows: Serie', () => {
  const r = Object.fromEntries(diagRows(SERIE));
  assert.equal(r.Firmware, '1.0.3 · Build 12');
  assert.equal(r.Hardware, '0x0A');
  assert.equal(r.Neustartgrund, 'Watchdog');
  assert.equal(r['Letzter Fehler'], '0x50 WDT_RESET');
  assert.match(r.Fehlerprotokoll, /WDT_RESET \(0\) Start 3/);
  assert.ok(!('TF-2' in r));
});

test('diagRows: Testfirmware-Anhang, fehlende INFO und Dekodierhinweis', () => {
  const tf = { variant: 2, vdd_min: 2900, vdd_min_ever: 2850, vbat_rest: 2980, flash_ops_boot: 5, flash_ops_ready: 0, backoffs: 1, tf1_trig: 0, tf2_trig: 1, tf2_mode_txt: 'spaet (5 x)', tf2_cycles: 3, tf2_max_ops: 7, tf2_sd_ops: 0, tf3_reads: 0 };
  const d = { ...SERIE, testfw: 2, info: null, diag: { ...SERIE.diag, tf }, decode_errors: ['info: INFO zu kurz'] };
  const rows = diagRows(d);
  const r = Object.fromEntries(rows);
  assert.equal(r.INFO, 'keine Antwort');
  assert.match(r['TF-2'], /Neustarts 3/);
  assert.match(r['Flash-Ops'], /bis 1\. Messung 0/);
  assert.equal(r.Hinweis, 'info: INFO zu kurz');
  assert.ok(!rows.some(([k]) => k === 'TF-1'));
});

test('Dateiname und Auswertebefehl', () => {
  assert.equal(diagFileName(SERIE), 'fluidi-diag-fluidi-AB12-20261109T143000Z.json');
  assert.equal(evalCommand({ ...SERIE, testfw: 1 }), '.venv/bin/python scripts/testfw_eval.py diag --file fluidi-diag-fluidi-AB12-20261109T143000Z.json --expect tf1');
  assert.ok(!evalCommand(SERIE).includes('--expect'));
});

test('imageTestfw/tfLabel: Abbilder mit Build 9000–9999 sind Testfirmware (Sicherheit W-2)', () => {
  assert.equal(imageTestfw({ testfw: 3, build: 9301 }), 3);
  assert.equal(imageTestfw({ build: 9201 }), 2);          // älteres Gateway ohne Feld testfw
  assert.equal(imageTestfw({ build: 9001 }), 9);          // Testbuild unbekannter Variante
  assert.equal(imageTestfw({ build: 12 }), 0);
  assert.equal(imageTestfw({}), 0);
  assert.equal(tfLabel(2), 'TESTFIRMWARE TF-2');
  assert.equal(tfLabel(9), 'TESTFIRMWARE');
});
