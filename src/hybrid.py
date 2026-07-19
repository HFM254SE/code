"""Hybride Suche: dichte Vektorsuche + Keyword-Suche, fusioniert per RRF.

Reine Vektorsuche ist "keyword-blind": Sie findet Bedeutung ("VPN geht nicht"
↔ "Verbindung aufbauen"), verfehlt aber oft exakte Zeichenketten wie Codes,
Gerätenummern (`LT-PRN-02`) oder Eigennamen (`vpn.leinetech.de`). Die
Keyword-Suche aus VL 4 ist genau umgekehrt. Hybride Suche führt **beide
parallel** aus und fusioniert die Ranglisten per **Reciprocal Rank Fusion**.

RRF kombiniert Ranglisten, ohne unterschiedliche Score-Skalen (Kosinus-
Ähnlichkeit vs. Wortüberlappung) normalisieren zu müssen — es zählt nur die
**Ränge**. Dokumente, die in beiden Listen auftauchen, steigen dadurch
natürlich nach oben.

Aufruf:
    python -m src.hybrid "Welches Gateway trage ich für Cisco Secure Client ein?"
"""

import argparse

from src.search import embedding_search, keyword_search
from src.vectorstore import DEFAULT_COLLECTION, create_collection

# Kandidatenfenster relativ zu n_results: beide Suchen liefern mehr Treffer,
# damit die Fusion echte Auswahl hat.
CANDIDATE_FACTOR = 4


def reciprocal_rank_fusion(rankings: list[list[dict]], k: int = 60) -> list[dict]:
    """Fusioniert mehrere Ranglisten zu einer per Reciprocal Rank Fusion.

    Jedes Dokument bekommt ``score = Σ 1 / (k + rang)`` über alle Listen, in
    denen es vorkommt (rang 1-basiert). ``k=60`` ist die empirische
    Standardkonstante (Cormack et al. 2009).

    Als stabile Identität pro Chunk dient hier der Chunk-Text (identischer Text
    = identischer Chunk). In Produktion nähme man die ``chunk_id``.

    Gibt die fusionierten Treffer absteigend nach RRF-Score zurück, im
    Standardformat ``{"rank", "source", "score", "text"}``.
    """
    scores: dict[str, float] = {}
    hit_by_key: dict[str, dict] = {}

    for ranking in rankings:
        for rank, hit in enumerate(ranking, start=1):
            key = hit["text"]
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            hit_by_key.setdefault(key, hit)

    fused = []
    ordered = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    for rank, (key, score) in enumerate(ordered, start=1):
        source_hit = hit_by_key[key]
        fused.append(
            {
                "rank": rank,
                "source": source_hit.get("source", "?"),
                "score": score,
                "text": source_hit["text"],
            }
        )
    return fused


def hybrid_search(collection, query: str, n_results: int = 5) -> list[dict]:
    """Dichte + Keyword-Suche parallel, per RRF fusioniert.

    Liefert die Top-k im **gleichen Format** wie ``embedding_search`` — der
    RAG-Client kann den Retriever damit ohne Änderung austauschen.
    """
    candidates = n_results * CANDIDATE_FACTOR
    dense = embedding_search(collection, query, n_results=candidates)
    sparse = keyword_search(collection, query, n_results=candidates)
    fused = reciprocal_rank_fusion([dense, sparse])
    return fused[:n_results]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Hybride Suche (Dense + Keyword, RRF-fusioniert) über die LeineTech-Wissensbasis"
    )
    parser.add_argument("query", help="Suchanfrage in natürlicher Sprache")
    parser.add_argument("--n", type=int, default=5, help="Anzahl Treffer (Default: 5)")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Name der Collection")
    args = parser.parse_args()

    collection = create_collection(args.collection)
    if collection.count() == 0:
        raise SystemExit(
            "Collection ist leer — zuerst die Pipeline laufen lassen: "
            "python -m src.ingest docs"
        )

    hits = hybrid_search(collection, args.query, n_results=args.n)
    print(f'Hybride Suche: "{args.query}"')
    for hit in hits:
        preview = " ".join(hit["text"].split())[:200]
        print(f'  {hit["rank"]}. [{hit["score"]:.4f}] {hit["source"]} — "{preview}"')


if __name__ == "__main__":
    main()
