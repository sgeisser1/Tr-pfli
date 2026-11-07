# uPlot (vendored)

| | |
|---|---|
| Bibliothek | uPlot – kleine Zeitreihen-Diagramme (Canvas) |
| Version | **1.6.32** (`package.json` des Pakets: `"version": "1.6.32"`, `"license": "MIT"`) |
| Lizenz | MIT, Copyright (c) 2022 Leon Sorokin, siehe `LICENSE` |
| Quelle | npm-Paket `uplot@1.6.32`, abgerufen über `https://unpkg.com/uplot@1.6.32/<Datei>` |
| Abgerufen | 2026-11-07 (curl, einzelne Dateien, kein npm install) |
| Projekt | https://github.com/leeoniya/uPlot |

| Datei | Herkunft | SHA-256 |
|---|---|---|
| `uPlot.iife.min.js` | `dist/uPlot.iife.min.js` | `19c8d4c6ad88929a79f4ae49d6f7161566dfd0ba3d15cc495e974f787eb78f1f` |
| `uPlot.min.css` | `dist/uPlot.min.css` | `df630c6a8d6f8eeaff264b50f73ce5b114f646ffd9a0bb74f049b0a00135fa04` |
| `LICENSE` | `LICENSE` | `8f989229699b4fe2f1a0432d0e9edc338a8a911e250e2d1b01ecd770a5f5b1bd` |

Prüfung beim Einbinden: Datei nach Netzwerkzugriffen und dynamischer Code-Ausführung durchsucht
(`fetch(`, `XMLHttpRequest`, `WebSocket`, `sendBeacon`, `import(`, `eval(`, `new Function`, URLs):
einziger Treffer ist der Kommentar `https://github.com/leeoniya/uPlot` im Kopf. Keine Laufzeit-CDNs.

Prüfsummen neu berechnen: `sha256sum app/vendor/uplot/*` (der Test `app/tests/check_pwa.py` vergleicht sie).
