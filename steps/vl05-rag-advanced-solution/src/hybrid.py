"""Hybride Suche: dichte Suche und Keyword-Suche parallel, fusioniert per RRF.

Die dichte Suche (Embeddings) findet Bedeutung, auch bei Umschreibungen wie
"VPN geht nicht" ↔ "Verbindungsaufbau bleibt hängen". Seltene exakte Begriffe
in der Frage gewichtet sie aber oft zu schwach: Namen ("Hagedorn"), Fehlercodes
("MSI-Code 1603", "0x80042109") oder Gerätenummern ("LT-PRN-02"). Die
Keyword-Suche aus VL 4 trifft genau diese Begriffe wörtlich, kennt aber keine
Synonyme. Die hybride Suche nutzt beide Stärken.

Keyword-Suche hilft also nur, wenn der seltene Begriff in der Frage steht. Nach
einer Antwort wie "-4200", die der Nutzer noch nicht kennt, kann sie nicht suchen.

Reciprocal Rank Fusion (RRF) fusioniert die Ranglisten nur über die Ränge. Die
Scores der beiden Suchen (Kosinus-Ähnlichkeit und Anzahl gemeinsamer Wörter)
müssen deshalb nicht vergleichbar sein.

Aufruf:
    python -m src.hybrid "Welche Durchwahl hat Bernd Hagedorn?" --n 3
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
    scores: dict[str, float] = {}
    first_hit: dict[str, dict] = {}

    for ranking in rankings:
        for rank, hit in enumerate(ranking, start=1):
            key = hit["text"]
            scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
            first_hit.setdefault(key, hit)

    ordered = sorted(scores, key=scores.get, reverse=True)
    return [
        {
            "rank": rank,
            "chunk_id": first_hit[key].get("chunk_id", "?"),
            "source": first_hit[key].get("source", "?"),
            "score": scores[key],
            "text": key,
        }
        for rank, key in enumerate(ordered, start=1)
    ]


def hybrid_search(collection, query: str, n_results: int = 5) -> list[dict]:
    """Führt dichte Suche und Keyword-Suche aus und fusioniert sie per RRF.

    Liefert die Top-k im gleichen Format wie embedding_search. Der RAG-Client
    kann den Retriever deshalb ohne Änderung austauschen.
    """
    candidates = n_results * CANDIDATE_FACTOR
    dense = embedding_search(collection, query, n_results=candidates)
    sparse = keyword_search(collection, query, n_results=candidates)
    return reciprocal_rank_fusion([dense, sparse])[:n_results]


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
