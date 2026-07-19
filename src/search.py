"""Semantische Suche über die indexierte Wissensbasis — plus Keyword-Vergleich.

Fragt die in `./chroma_db` liegende Collection ab (vorher `python -m src.ingest
docs` ausführen!). Zwei Modi zum direkten Vergleich aus dem Lab:

    --mode embedding   Vektor-Ähnlichkeit (Default): findet auch Synonyme und
                       Umschreibungen ("VPN geht nicht" ↔ "Verbindung aufbauen")
    --mode keyword     simple Wortüberlappung: gewinnt bei exakten Fachbegriffen,
                       versagt bei Synonymen

Aufruf:
    python -m src.search "Wie verbinde ich mich mit dem VPN?"
    python -m src.search "Mein Passwort ist abgelaufen" --mode keyword
    python -m src.search "Drucker druckt nicht" --n 3
"""

import argparse
import re

from src.embedder import embed_text
from src.vectorstore import DEFAULT_COLLECTION, create_collection
from src.vectorstore import search as vector_search

# Deutsche Stoppwörter, die sonst jede Keyword-Suche verwässern.
_STOPWORDS = {
    "und", "oder", "der", "die", "das", "ein", "eine", "ist", "im", "in",
    "auf", "mit", "für", "von", "zu", "den", "dem", "des", "wie", "ich",
    "nicht", "auch", "bei", "an", "es", "sich", "wir", "uns", "mein", "meine",
}


def _tokenize(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"[a-zA-Zäöüß0-9]+", text.lower())
        if len(word) > 2 and word not in _STOPWORDS
    }


def embedding_search(collection, query: str, n_results: int = 5) -> list[dict]:
    """Vektor-Suche: embedded die Frage mit demselben Modell wie die Chunks.

    Liefert Treffer als {"rank", "source", "score", "text"}. `score` ist eine
    Ähnlichkeit (größer = besser), umgerechnet aus der ChromaDB-Distanz.
    """
    query_embedding = embed_text(query)
    result = vector_search(collection, [query_embedding], n_results=n_results)

    documents = result["documents"][0]
    metadatas = result["metadatas"][0]
    distances = result["distances"][0]

    hits = []
    for rank, (text, metadata, distance) in enumerate(
        zip(documents, metadatas, distances), start=1
    ):
        hits.append(
            {
                "rank": rank,
                "source": metadata.get("source", "?"),
                "score": _distance_to_similarity(distance),
                "text": text,
            }
        )
    return hits


def keyword_search(collection, query: str, n_results: int = 5) -> list[dict]:
    """Baseline zum Vergleich: reine Wortüberlappung zwischen Frage und Chunk.

    Kennt keine Synonyme — findet nur, was wörtlich vorkommt. `score` ist die
    Anzahl gemeinsamer Wörter.
    """
    q_terms = _tokenize(query)
    if not q_terms:
        return []

    stored = collection.get(include=["documents", "metadatas"])
    scored = []
    for text, metadata in zip(stored["documents"], stored["metadatas"]):
        overlap = q_terms & _tokenize(text)
        if overlap:
            scored.append(
                {
                    "source": metadata.get("source", "?"),
                    "score": len(overlap),
                    "text": text,
                }
            )

    scored.sort(key=lambda hit: hit["score"], reverse=True)
    top = scored[:n_results]
    for rank, hit in enumerate(top, start=1):
        hit["rank"] = rank
    return top


def _distance_to_similarity(distance: float) -> float:
    """Rechnet eine ChromaDB-Distanz in einen Ähnlichkeitswert (größer = besser).

    qwen3-embed-4b liefert normalisierte Vektoren; ChromaDB nutzt per Default
    die quadrierte L2-Distanz. Für Einheitsvektoren gilt d² = 2·(1 - cos), also
    ist `1 - d²/2` die Kosinus-Ähnlichkeit (auf [0, 1] begrenzt).
    """
    similarity = 1.0 - distance / 2.0
    return max(0.0, min(1.0, similarity))


def _print_hits(query: str, hits: list[dict], preview_chars: int = 200) -> None:
    print(f'Suche: "{query}"')
    if not hits:
        print("  (keine Treffer)")
        return
    for hit in hits:
        preview = " ".join(hit["text"].split())[:preview_chars]
        print(f'  {hit["rank"]}. [{hit["score"]:.2f}] {hit["source"]} — "{preview}"')


def main() -> None:
    parser = argparse.ArgumentParser(description="Semantische Suche über die LeineTech-Wissensbasis")
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
            "Collection ist leer — zuerst die Pipeline laufen lassen: "
            "python -m src.ingest docs"
        )

    if args.mode == "keyword":
        hits = keyword_search(collection, args.query, n_results=args.n)
    else:
        hits = embedding_search(collection, args.query, n_results=args.n)
    _print_hits(args.query, hits)


if __name__ == "__main__":
    main()
