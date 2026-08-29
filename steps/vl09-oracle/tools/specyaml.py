"""Minimaler YAML-Leser fuer api/openapi.yaml — reine Standardbibliothek.

Warum nicht PyYAML? Weil dieses Lab **ohne pip install** laufen soll. Der
Preis: dieser Leser versteht nur die YAML-Teilmenge, die in unserer Spec
vorkommt (verschachtelte Maps, `- `-Listen, Inline-Listen `[a, b]`,
gequotete Strings, gefaltete Bloecke `>`), und er loest **keine `$ref`
auf** — `$ref` bleibt ein ganz normaler String-Wert.

Das ist Absicht und wird im Lab zum Thema: ein Pruefer ist nie besser als
das, was er von der Spec ueberhaupt sehen kann.

In Produktion nehmt ihr `yaml.safe_load` plus einen echten Schema-Validator.
"""

from __future__ import annotations

import re
from pathlib import Path


def _convert(raw: str):
    """Skalar in Python-Wert wandeln (int, bool, None, String)."""
    v = raw.strip()
    if not v:
        return ""
    if v[0] in "\"'" and v[-1] == v[0] and len(v) >= 2:
        return v[1:-1]
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [_convert(part) for part in inner.split(",")]
    if v in ("true", "True"):
        return True
    if v in ("false", "False"):
        return False
    if v in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    return v


def _strip_comment(line: str) -> str:
    """Kommentar am Zeilenende entfernen — aber nicht innerhalb von Quotes."""
    out, quote = [], None
    for ch in line:
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#":
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _parse(lines: list[tuple[int, str]], pos: int, indent: int):
    """Rekursiv einen Block ab Einrueckung `indent` parsen."""
    # Listen-Block?
    if pos < len(lines) and lines[pos][0] == indent and lines[pos][1].startswith("- "):
        items = []
        while pos < len(lines) and lines[pos][0] == indent and lines[pos][1].startswith("- "):
            rest = lines[pos][1][2:].strip()
            pos += 1
            if ":" in rest and not rest.startswith("["):
                # "- name: x" — erste Map-Zeile steht direkt hinter dem Strich
                key, _, val = rest.partition(":")
                sub: dict = {}
                if val.strip():
                    sub[key.strip()] = _convert(val)
                else:
                    child, pos = _parse(lines, pos, lines[pos][0] if pos < len(lines) else indent + 2)
                    sub[key.strip()] = child
                # weitere Map-Zeilen desselben Listenelements
                while pos < len(lines) and lines[pos][0] > indent \
                        and not lines[pos][1].startswith("- "):
                    k2, _, v2 = lines[pos][1].partition(":")
                    child_indent = lines[pos][0]
                    pos += 1
                    if v2.strip():
                        sub[k2.strip()] = _convert(v2)
                    else:
                        nxt = lines[pos][0] if pos < len(lines) else child_indent
                        if nxt > child_indent:
                            child, pos = _parse(lines, pos, nxt)
                            sub[k2.strip()] = child
                        else:
                            sub[k2.strip()] = {}
                items.append(sub)
            else:
                items.append(_convert(rest))
        return items, pos

    # Map-Block
    result: dict = {}
    while pos < len(lines):
        cur_indent, text = lines[pos]
        if cur_indent < indent:
            break
        if cur_indent > indent:      # sollte nicht passieren; defensiv ueberspringen
            pos += 1
            continue
        if text.startswith("- "):
            break
        key, _, val = text.partition(":")
        key = key.strip()
        if len(key) >= 2 and key[0] in "\"'" and key[-1] == key[0]:
            key = key[1:-1]          # "200": -> 200
        pos += 1
        val = val.strip()
        if val in (">", "|", ">-", "|-"):
            # gefalteter Block: alle tiefer eingerueckten Zeilen einsammeln
            chunk = []
            while pos < len(lines) and lines[pos][0] > cur_indent:
                chunk.append(lines[pos][1])
                pos += 1
            result[key] = " ".join(chunk)
        elif val:
            result[key] = _convert(val)
        else:
            nxt = lines[pos][0] if pos < len(lines) else cur_indent
            if pos < len(lines) and nxt > cur_indent:
                child, pos = _parse(lines, pos, nxt)
                result[key] = child
            elif pos < len(lines) and nxt == cur_indent and lines[pos][1].startswith("- "):
                child, pos = _parse(lines, pos, nxt)
                result[key] = child
            else:
                result[key] = {}
    return result, pos


def load(path: str | Path) -> dict:
    """api/openapi.yaml als verschachteltes dict lesen."""
    raw = Path(path).read_text(encoding="utf-8").split("\n")
    lines: list[tuple[int, str]] = []
    for line in raw:
        clean = _strip_comment(line)
        if not clean.strip():
            continue
        lines.append((len(clean) - len(clean.lstrip()), clean.strip()))
    tree, _ = _parse(lines, 0, 0)
    return tree
