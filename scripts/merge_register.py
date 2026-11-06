#!/usr/bin/env python3
"""Führt die Register-Teillisten docs/datasheets/_staging/INDEX_*.csv in docs/datasheets/INDEX.csv zusammen.
- überzählige Felder (unquotierte ';' in Bemerkung) werden in die Bemerkung zusammengeführt
- Dubletten (gleicher Hersteller + Teilenummer + lokaler Pfad) werden entfernt
- bestehende Einträge in INDEX.csv bleiben erhalten
Aufruf: python3 scripts/merge_register.py
"""
import csv, glob, os
BASE = os.path.join(os.path.dirname(__file__), '..', 'docs', 'datasheets')
OUT = os.path.join(BASE, 'INDEX.csv')
rows, hdr = [], None
def norm(r):
    if len(r) > 12: r = r[:11] + [', '.join(x.strip() for x in r[11:])]
    return r + [''] * (12 - len(r))
if os.path.exists(OUT):
    old = list(csv.reader(open(OUT, encoding='utf-8'), delimiter=';'))
    hdr = old[0]; rows += [norm(r) for r in old[1:] if any(r)]
for f in sorted(glob.glob(os.path.join(BASE, '_staging', 'INDEX_*.csv'))):
    r = list(csv.reader(open(f, encoding='utf-8'), delimiter=';'))
    hdr = hdr or r[0]; rows += [norm(x) for x in r[1:] if any(x)]
seen, out = set(), []
for r in rows:
    k = (r[2].strip().lower(), r[3].strip().lower(), r[10].strip())
    if k in seen: continue
    seen.add(k); out.append(r)
missing = [r[10] for r in out if r[10].startswith('docs/') and not os.path.exists(os.path.join(BASE, '..', '..', r[10]))]
with open(OUT, 'w', encoding='utf-8', newline='') as fh:
    w = csv.writer(fh, delimiter=';', quoting=csv.QUOTE_MINIMAL); w.writerow(hdr); w.writerows(out)
print(f'{len(out)} Einträge geschrieben ({len(rows)-len(out)} Dubletten entfernt)')
print('Pfade ohne Datei:', missing or 'keine')
