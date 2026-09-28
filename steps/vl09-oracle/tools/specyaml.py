"""Minimaler YAML-Leser für api/openapi.yaml, nur mit der Standardbibliothek.

Warum nicht PyYAML? Weil Teil 1 des Labs **ohne pip install** laufen soll.
Der Preis: Dieser Leser versteht nur die YAML-Teilmenge, die in unserer Spec
vorkommt. Das sind verschachtelte Maps im Blockstil, `- `-Listen,
Inline-Listen `[a, b]`, gequotete Strings, gefaltete Blöcke `>` und die leere
Map `{}` (auch `{ }`). Er löst **kein `$ref` auf**: `$ref` bleibt ein
normaler String.

Das ist Absicht und wird im Lab zum Thema: Ein Prüfer ist nie besser als
das, was er von der Spec überhaupt sehen kann.

Flow-Maps mit Inhalt (`schema: { type: integer }`) versteht der Leser nicht.
Statt sie still falsch zu lesen, bricht er mit Zeilennummer ab
(`SpecYamlFehler`). Abhilfe: dieselbe Angabe im Blockstil schreiben.
Geschweifte Klammern im Freitext eines gefalteten Blocks (`description: >`)
sind davon nicht betroffen.

In Produktion nehmt ihr `yaml.safe_load` plus einen echten Schema-Validator.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class SpecYamlFehler(ValueError):
    """Die Spec nutzt YAML, das dieser Leser nicht versteht."""


# Wert hinter "key:", mit dem ein gefalteter oder wörtlicher Block beginnt.
_BLOCK_MARKER = (">", "|", ">-", "|-")


def _convert(raw: str):
    """Skalar in Python-Wert wandeln (int, bool, None, String, [], {})."""
    v = raw.strip()
    if not v:
        return ""
    if v.replace(" ", "") == "{}":  # "{}" und "{ }"
        return {}
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
    """Kommentar am Zeilenende entfernen, aber nicht innerhalb von Quotes."""
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


def _parse(lines: list[tuple[int, str]], pos: int, indent: int) -> tuple[Any, int]:
    """Rekursiv einen Block ab Einrückung `indent` parsen.

    Der erste Rückgabewert ist ein YAML-Knoten beliebiger Art (Map, Liste oder
    Skalar). Welcher davon, entscheidet erst der Inhalt. Deshalb `Any`.
    """
    # Listen-Block?
    if pos < len(lines) and lines[pos][0] == indent and lines[pos][1].startswith("- "):
        items = []
        while pos < len(lines) and lines[pos][0] == indent and lines[pos][1].startswith("- "):
            rest = lines[pos][1][2:].strip()
            pos += 1
            if ":" in rest and not rest.startswith("["):
                # "- name: x": Die erste Map-Zeile steht direkt hinter dem Strich.
                key, _, val = rest.partition(":")
                sub: dict = {}
                if val.strip():
                    sub[key.strip()] = _convert(val)
                else:
                    sub_indent = lines[pos][0] if pos < len(lines) else indent + 2
                    child, pos = _parse(lines, pos, sub_indent)
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
        if cur_indent > indent:      # sollte nicht passieren, defensiv überspringen
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
        if val in _BLOCK_MARKER:
            # gefalteter Block: alle tiefer eingerückten Zeilen einsammeln
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


def _check_keine_flow_map(text: str, nr: int, path: str | Path) -> None:
    """Bricht ab, wenn eine Zeile eine Flow-Map mit Inhalt enthält."""
    rest = (text[2:] if text.startswith("- ") else text).strip()
    if rest.startswith("{"):
        kandidat = rest                        # "- { name: x }" oder "{ ... }"
    else:
        kandidat = rest.partition(":")[2].strip()  # "schema: { type: integer }"
    if kandidat.startswith("{") and kandidat.replace(" ", "") != "{}":
        raise SpecYamlFehler(
            f"{path}, Zeile {nr}: Flow-Map '{kandidat}' wird nicht unterstützt. "
            "Bitte im Blockstil schreiben (ein Schlüssel pro Zeile, eingerückt)."
        )


def load(path: str | Path) -> dict:
    """api/openapi.yaml als verschachteltes dict lesen."""
    raw = Path(path).read_text(encoding="utf-8").split("\n")
    lines: list[tuple[int, str]] = []
    block_indent: int | None = None   # Einrückung der Zeile mit ">" oder "|"
    for nr, line in enumerate(raw, start=1):
        clean = _strip_comment(line)
        if not clean.strip():
            continue
        indent, text = len(clean) - len(clean.lstrip()), clean.strip()
        if block_indent is not None and indent > block_indent:
            # Freitext in einem gefalteten Block: "{" ist hier nur ein Zeichen.
            lines.append((indent, text))
            continue
        block_indent = None
        _check_keine_flow_map(text, nr, path)
        if not text.startswith("- ") and text.partition(":")[2].strip() in _BLOCK_MARKER:
            block_indent = indent     # dieselbe Regel wie in _parse
        lines.append((indent, text))
    tree, _ = _parse(lines, 0, 0)
    return tree
