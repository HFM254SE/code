"""Suche über die indexierte Wissensbasis: semantisch oder per Keyword-Baseline.

Vorher muss die Collection gefüllt sein (`python -m src.ingest docs`). Zwei
Modi stehen für den direkten Vergleich im Lab bereit:

    --mode embedding   Vektor-Ähnlichkeit (Default). Findet auch Umschreibungen,
                       z. B. „Laptop“ zu einem Chunk über „Notebooks“.
    --mode keyword     Wortüberlappung. Findet exakte Begriffe und IDs wie
                       „0x80042109“ oder „LT-PRN-02“, kennt aber keine Synonyme.

Jeder Treffer ist ein Dict {"rank", "chunk_id", "source", "score", "text"}.

Aufruf:
    python -m src.search "Wie verbinde ich mich mit dem VPN?"
    python -m src.search "Mein Passwort ist abgelaufen" --mode keyword
    python -m src.search "Drucker druckt nicht" --n 3
"""

import argparse
import re
import sys

from src.embedder import embed_text
from src.vectorstore import DEFAULT_COLLECTION, create_collection
from src.vectorstore import search as vector_search

# Häufige deutsche Wörter, die sonst jede Keyword-Suche verwässern.
_STOPWORDS = {
    "und", "oder", "der", "die", "das", "ein", "eine", "ist", "im", "in",
    "auf", "mit", "für", "von", "zu", "den", "dem", "des", "wie", "ich",
    "nicht", "auch", "bei", "an", "es", "sich", "wir", "uns", "mein", "meine",
}

# Ein Wort aus Buchstaben und Ziffern, optional mit Bindestrich verkettet ("lt-prn-02").
_WORD_PATTERN = re.compile(r"[a-zäöüß0-9]+(?:-[a-zäöüß0-9]+)*")


def _tokenize(text: str) -> set[str]:
    """Zerlegt Text in die Menge seiner Suchwörter (klein geschrieben, ohne Stoppwörter).

    Wörter mit Bindestrich zählen ganz und zusätzlich mit ihren Teilen:
    "LT-PRN-02" ergibt {"lt-prn-02", "prn"}. So unterscheidet die Suche
    LT-PRN-02 von LT-PRN-03, und „VPN-Verbindung“ passt trotzdem zu „VPN“.
    Ein exakt gleiches Kompositum zählt dadurch mehr als ein einzelner Teil.
    Wörter mit höchstens zwei Zeichen werden ignoriert.
    """
    tokens = set()
    for word in _WORD_PATTERN.findall(text.lower()):
        for token in {word, *word.split("-")}:
            if len(token) > 2 and token not in _STOPWORDS:
                tokens.add(token)
    return tokens


def embedding_search(collection, query: str, n_results: int = 5) -> list[dict]:
    """Semantische Suche: bettet die Frage mit demselben Modell ein wie die Chunks.

    `score` ist die Kosinus-Ähnlichkeit (größer = ähnlicher), umgerechnet aus
    der Distanz, die ChromaDB liefert.
    """
    query_embedding = embed_text(query)
    result = vector_search(collection, [query_embedding], n_results=n_results)

    hits = []
    rows = zip(
        result["ids"][0],
        result["documents"][0],
        result["metadatas"][0],
        result["distances"][0],
    )
    for rank, (chunk_id, text, metadata, distance) in enumerate(rows, start=1):
        hits.append(
            {
                "rank": rank,
                "chunk_id": chunk_id,
                "source": metadata.get("source", "?"),
                "score": _distance_to_similarity(distance),
                "text": text,
            }
        )
    return hits


def keyword_search(collection, query: str, n_results: int = 5) -> list[dict]:
    """Baseline zum Vergleich: zählt die gemeinsamen Wörter von Frage und Chunk.

    Kennt keine Synonyme und findet nur, was wörtlich vorkommt. `score` ist
    die Anzahl gemeinsamer Wörter. Seltene Wörter zählen nicht mehr als
    häufige, und bei Gleichstand bleibt die Reihenfolge der Collection
    erhalten (Dokument für Dokument). Beides verbessert BM25 (VL 5).
    """
    query_terms = _tokenize(query)
    if not query_terms:
        return []

    stored = collection.get(include=["documents", "metadatas"])
    documents = stored["documents"]
    chunk_ids = stored["ids"]  # ChromaDB liefert die IDs bei get() immer mit

    scored = []
    for chunk_id, text, metadata in zip(chunk_ids, documents, stored["metadatas"]):
        overlap = query_terms & _tokenize(text)
        if overlap:
            scored.append(
                {
                    "chunk_id": chunk_id,
                    "source": metadata.get("source", "?"),
                    "score": len(overlap),
                    "text": text,
                }
            )

    # sort ist stabil: Bei Gleichstand bleibt die Reihenfolge der Collection erhalten.
    scored.sort(key=lambda hit: hit["score"], reverse=True)
    top = scored[:n_results]
    for rank, hit in enumerate(top, start=1):
        hit["rank"] = rank
    return top


def _distance_to_similarity(distance: float) -> float:
    """Rechnet die ChromaDB-Distanz in die Kosinus-Ähnlichkeit um (größer = ähnlicher).

    ChromaDB misst per Default die quadrierte euklidische Distanz d². Für
    Vektoren der Länge 1 gilt d² = 2 − 2·cos, also cos = 1 − d²/2. Das setzt
    normierte Embeddings voraus (im Lab Teil 2A prüfen). Das Ergebnis wird auf
    den Bereich 0 bis 1 begrenzt.
    """
    similarity = 1.0 - distance / 2.0
    return max(0.0, min(1.0, similarity))


def _print_hits(query: str, hits: list[dict], mode: str, preview_chars: int = 200) -> None:
    """Gibt die Treffer als Rangliste mit Score, chunk_id und Textvorschau aus.

    Kosinus-Werte erscheinen mit zwei Nachkommastellen, Keyword-Scores als
    ganze Zahl (Anzahl gemeinsamer Wörter).
    """
    print(f'Suche ({mode}): "{query}"')
    if not hits:
        print("  (keine Treffer)")
        return
    for hit in hits:
        score = hit["score"]
        score_text = str(score) if isinstance(score, int) else f"{score:.2f}"
        preview = " ".join(hit["text"].split())[:preview_chars]
        print(f'  {hit["rank"]}. [{score_text}] {hit["chunk_id"]} — "{preview}"')


def main() -> None:
    """Kommandozeile: python -m src.search "<Frage>" [Optionen]."""
    # Windows schreibt in eine Pipe wie `| tee` sonst in cp1252. Zeichen wie „→“
    # aus der Wissensbasis brächen dann die Ausgabe mit UnicodeEncodeError ab.
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Suche über die LeineTech-Wissensbasis")
    parser.add_argument("query", help="Suchanfrage in natürlicher Sprache")
    parser.add_argument(
        "--mode",
        choices=["embedding", "keyword"],
        default="embedding",
        help="Suchverfahren (Default: embedding)",
    )
    parser.add_argument("--n", type=int, default=5, help="Anzahl Treffer (Default: 5)")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Name der Collection")
    args = parser.parse_args()

    collection = create_collection(args.collection)
    if collection.count() == 0:
        raise SystemExit(
            f"Collection '{args.collection}' ist leer. "
            "Zuerst die Pipeline laufen lassen: python -m src.ingest docs"
        )

    if args.mode == "keyword":
        hits = keyword_search(collection, args.query, n_results=args.n)
    else:
        hits = embedding_search(collection, args.query, n_results=args.n)
    _print_hits(args.query, hits, args.mode)


if __name__ == "__main__":
    main()
