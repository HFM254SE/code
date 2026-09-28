"""Lab VL 5, Teil 2: Vorlage für die hybride Suche (kopieren nach src/hybrid.py).

    cp labs/templates/hybrid_skeleton.py src/hybrid.py

Fertig sind die Imports, die Konstanten und das CLI. Eure Arbeit sind die TODOs:

    TODO 1  reciprocal_rank_fusion: zwei Ranglisten per RRF zu einer machen
    TODO 2  hybrid_search: beide Suchen aufrufen und fusionieren

Selbsttest ohne Endpunkt:  python -m pytest tests/test_hybrid.py -q
Aufruf mit Endpunkt:       python -m src.hybrid "Welche Durchwahl hat Bernd Hagedorn?" --n 3
"""

import argparse

from src.search import embedding_search, keyword_search
from src.vectorstore import DEFAULT_COLLECTION, create_collection

# Standardkonstante aus Cormack et al. (2009). Nicht zu verwechseln mit top-k,
# der Anzahl der Chunks im Prompt.
RRF_K = 60

# Beide Suchen liefern mehr Kandidaten als am Ende gebraucht werden, damit die
# Fusion eine echte Auswahl hat.
CANDIDATE_FACTOR = 4


def reciprocal_rank_fusion(rankings: list[list[dict]], k: int = RRF_K) -> list[dict]:
    """Fusioniert mehrere Ranglisten per Reciprocal Rank Fusion.

    Jeder Chunk bekommt score = Σ 1 / (k + rang) über alle Listen, in denen er
    vorkommt. Der Rang beginnt bei 1. Fehlt ein Chunk in einer Liste, trägt diese
    Liste nichts bei. Wer in mehreren Listen steht, sammelt mehrere Beiträge.

    Als Identität eines Chunks dient sein Text. In Produktion nähme man die
    chunk_id. Bei Gleichstand bleibt die Reihenfolge des ersten Auftretens erhalten.

    Gibt die Treffer absteigend nach RRF-Score zurück, im Format von
    embedding_search: {"rank", "chunk_id", "source", "score", "text"}.
    """
    # TODO 1:
    #   a) Über alle Listen und darin mit enumerate(ranking, start=1) über die Treffer gehen.
    #   b) Pro Chunk-Text den Beitrag 1 / (k + rang) in einem Dict aufsummieren.
    #   c) Den ersten Treffer pro Text merken, damit "chunk_id" und "source" erhalten
    #      bleiben (Tipp: hit.get("chunk_id", "?"), nicht jeder Treffer hat eine ID).
    #   d) Nach Score absteigend sortieren (sorted ist stabil, Gleichstände bleiben geordnet).
    #   e) Neue Ränge ab 1 vergeben und {"rank", "chunk_id", "source", "score", "text"}
    #      zurückgeben.
    raise NotImplementedError("TODO 1: reciprocal_rank_fusion in src/hybrid.py implementieren")


def hybrid_search(collection, query: str, n_results: int = 5) -> list[dict]:
    """Führt dichte Suche und Keyword-Suche aus und fusioniert sie per RRF.

    Liefert die Top-k im gleichen Format wie embedding_search. Der RAG-Client
    kann den Retriever deshalb ohne Änderung austauschen.
    """
    # TODO 2:
    #   a) Kandidatenfenster: candidates = n_results * CANDIDATE_FACTOR
    #   b) embedding_search und keyword_search mit n_results=candidates aufrufen
    #   c) Beide Listen mit reciprocal_rank_fusion fusionieren
    #   d) Nur die ersten n_results Treffer zurückgeben
    raise NotImplementedError("TODO 2: hybrid_search in src/hybrid.py implementieren")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hybride Suche (dense + keyword, per RRF fusioniert) über die Wissensbasis"
    )
    parser.add_argument("query", help="Suchanfrage in natürlicher Sprache")
    parser.add_argument("--n", type=int, default=5, help="Anzahl Treffer (Default: 5)")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Name der Collection")
    args = parser.parse_args()

    collection = create_collection(args.collection)
    if collection.count() == 0:
        raise SystemExit("Die Collection ist leer. Zuerst indexieren: python -m src.ingest docs")

    hits = hybrid_search(collection, args.query, n_results=args.n)
    print(f'Hybride Suche: "{args.query}"')
    for hit in hits:
        preview = " ".join(hit["text"].split())[:200]
        chunk_id = hit.get("chunk_id", "?")
        print(f'  {hit["rank"]}. [{hit["score"]:.4f}] {chunk_id} — "{preview}"')


if __name__ == "__main__":
    main()
