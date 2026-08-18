"""Leichtgewichtige Volltext-Suche über die LeineTech-Wissensbasis (docs/).

Bewusst KEIN Embedding/Vektor-RAG — das ist Svens Thema in VL 4/5. Hier
brauchen wir nur eine Funktion, die der Agent als *Tool* aufrufen kann:
„Gib mir die relevantesten KB-Abschnitte zu dieser Anfrage." Eine simple
Term-Überlappung pro Abschnitt reicht, um Tool-Use zu demonstrieren — und
sie ist vollständig offline testbar (kein LLM, kein Netz).
"""

import re
from pathlib import Path

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"

# Deutsche Stoppwörter, die sonst jede Suche verwässern.
_STOPWORDS = {
    "und", "oder", "der", "die", "das", "ein", "eine", "ist", "im", "in",
    "auf", "mit", "für", "von", "zu", "den", "dem", "des", "wie", "ich",
    "nicht", "auch", "bei", "an", "es", "sich", "wir", "uns", "mein", "meine",
}


def _tokenize(text: str) -> set[str]:
    return {
        w for w in re.findall(r"[a-zA-Zäöüß0-9]+", text.lower())
        if len(w) > 2 and w not in _STOPWORDS
    }


def _split_sections(markdown: str) -> list[tuple[str, str]]:
    """Zerlegt einen Artikel an ## Überschriften in (Titel, Text)-Abschnitte."""
    parts = re.split(r"^##\s+", markdown, flags=re.MULTILINE)
    sections = []
    head = parts[0].strip()
    if head:
        title = head.splitlines()[0].lstrip("# ").strip()
        sections.append((title, head))
    for part in parts[1:]:
        lines = part.splitlines()
        sections.append((lines[0].strip(), part.strip()))
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
        # Treffer im Artikelnamen/Abschnittstitel zählen doppelt — sonst gewinnt
        # ein Artikel, der „VPN" nur nebenbei erwähnt, gegen den VPN-Artikel.
        name_terms = _tokenize(path.stem.replace("-", " "))
        for title, text in _split_sections(content):
            overlap = q_terms & _tokenize(text)
            title_bonus = len(q_terms & (name_terms | _tokenize(title)))
            if overlap or title_bonus:
                scored.append({
                    "artikel": path.stem,
                    "abschnitt": title,
                    "text": text[:600],
                    "score": len(overlap) + 2 * title_bonus,
                })

    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored[:top_k]
