"""Leichtgewichtige Volltext-Suche über die LeineTech-Wissensbasis (docs/).

Bewusst kein Embedding- oder Vektor-RAG. Das ist das Thema von VL 4/5.
Hier brauchen wir nur eine Funktion, die der Agent als Tool aufrufen kann:
„Gib mir die relevantesten KB-Abschnitte zu dieser Anfrage.“ Eine einfache
Term-Überlappung pro Abschnitt reicht, um Tool Use zu zeigen. Sie ist
vollständig offline testbar (kein LLM, kein Netz).

Grenze mit Absicht: Keyword-Überlappung versteht keine Bedeutung. Manchmal
landet deshalb ein unpassender Abschnitt oben (z. B. bei T-1003). Auch
Tool-Ergebnisse muss man prüfen, statt ihnen zu glauben.
"""

import re
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"

# Obergrenze pro Abschnitt, damit ein sehr langer Artikel den Kontext des
# Modells nicht flutet. Der längste Abschnitt in docs/ hat derzeit 981 Zeichen,
# es wird also nichts abgeschnitten (geprüft in tests/test_knowledge_base.py).
MAX_SECTION_CHARS = 1000

# Deutsche Stoppwörter, die sonst jede Suche verwässern.
_STOPWORDS = {
    "und", "oder", "der", "die", "das", "ein", "eine", "ist", "im", "in",
    "auf", "mit", "für", "von", "zu", "den", "dem", "des", "wie", "ich",
    "nicht", "auch", "bei", "an", "es", "sich", "wir", "uns", "mein", "meine",
}


def _tokenize(text: str) -> set[str]:
    """Zerlegt Text in kleingeschriebene Suchbegriffe ohne Stoppwörter."""
    return {
        w for w in re.findall(r"[a-zA-Zäöüß0-9]+", text.lower())
        if len(w) > 2 and w not in _STOPWORDS
    }


def _split_sections(markdown: str) -> list[tuple[str, str]]:
    """Zerlegt einen Artikel an ##- und ###-Überschriften in (Titel, Text).

    Der Text vor der ersten Überschrift wird ein eigener Abschnitt mit dem
    Artikeltitel. Überschriften ohne eigenen Text (z. B. „Häufige Fehler und
    Lösungen“ direkt vor den ###-Unterabschnitten) werden übersprungen. Sonst
    gewinnt ein leerer Sammeltitel gegen den Abschnitt mit der Lösung.
    """
    parts = re.split(r"^#{2,3}\s+", markdown, flags=re.MULTILINE)
    sections = []
    head = parts[0].strip()
    if head:
        title = head.splitlines()[0].lstrip("# ").strip()
        sections.append((title, head))
    for part in parts[1:]:
        title, _, body = part.partition("\n")
        if body.strip():
            sections.append((title.strip(), part.strip()))
    return sections


def search_knowledge_base(query: str, top_k: int = 3, docs_dir: Path | None = None) -> list[dict]:
    """Sucht die relevantesten KB-Abschnitte zu einer Anfrage.

    Liefert bis zu top_k Treffer als Liste von {artikel, abschnitt, text, score},
    nach Score absteigend. Leere Liste, wenn nichts überlappt.
    """
    base = docs_dir or DOCS_DIR
    q_terms = _tokenize(query)
    if not q_terms:
        return []

    scored = []
    for path in sorted(base.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        # Treffer im Artikelnamen oder Abschnittstitel zählen doppelt. Sonst
        # gewinnt ein Artikel, der „VPN“ nur nebenbei erwähnt, gegen den VPN-Artikel.
        name_terms = _tokenize(path.stem.replace("-", " "))
        for title, text in _split_sections(content):
            overlap = q_terms & _tokenize(text)
            title_bonus = len(q_terms & (name_terms | _tokenize(title)))
            if overlap or title_bonus:
                scored.append({
                    "artikel": path.stem,
                    "abschnitt": title,
                    "text": text[:MAX_SECTION_CHARS],
                    "score": len(overlap) + 2 * title_bonus,
                })

    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored[:top_k]
