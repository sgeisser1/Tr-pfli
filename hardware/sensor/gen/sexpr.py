"""Minimaler S-Expression-Parser/-Writer fuer KiCad-Dateien (nur Standardbibliothek).

Atome bleiben Strings; Strings in Anfuehrungszeichen werden als Klasse Q gespeichert, damit
beim Zurueckschreiben die Quotierung erhalten bleibt.
"""
import re


class Q(str):
    """String, der in Anfuehrungszeichen geschrieben wird."""


_UNESC = re.compile(r"\\(.)", re.S)
_TOK = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)


def parse(text):
    stack, cur = [], []
    pos = 0
    n = len(text)
    while pos < n:
        m = _TOK.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError(f"Parsefehler bei {pos}: {text[pos:pos+40]!r}")
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            cur.append(Q(_UNESC.sub(lambda e: "\n" if e.group(1) == "n" else e.group(1), m.group(3))))
        else:
            cur.append(m.group(4))
    return cur[0] if len(cur) == 1 else cur


def _esc(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def dump(node, indent=0):
    """Schreibt Liste als S-Expression mit Tabs (KiCad-aehnlich)."""
    if not isinstance(node, list):
        return _esc(node) if isinstance(node, Q) else str(node)
    simple = all(not isinstance(x, list) for x in node)
    if simple:
        return "(" + " ".join(dump(x) for x in node) + ")"
    out = "(" + " ".join(dump(x) for x in node if not isinstance(x, list))
    for x in node:
        if isinstance(x, list):
            out += "\n" + "\t" * (indent + 1) + dump(x, indent + 1)
    out += "\n" + "\t" * indent + ")"
    return out


def find(node, key):
    """Erstes Kind-Element (Liste) mit Kopf `key`."""
    for x in node:
        if isinstance(x, list) and x and x[0] == key:
            return x
    return None


def find_all(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]
