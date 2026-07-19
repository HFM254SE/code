"""RAG-Client: Retrieve → Augment → Generate über die LeineTech-Wissensbasis.

Hängt an die Such-Pipeline aus VL 4 die beiden fehlenden Schritte an und macht
aus der Suche einen Chatbot:

    Frage → [Embed] → Suche → Top-k Chunks      ← RETRIEVE (VL 4)
                                    |
                           Kontextblock + Prompt  ← AUGMENT
                        (Grounding, Zitate, Enthaltung)
                                    |
                             LLM generiert         ← GENERATE
                                    |
              "Die Verbindung trennt nach 30 Min. [Quelle 1]"

Das Retrieval ist austauschbar (``--retriever dense|hybrid``); die Generierung
läuft über ``src/llm.py`` (qwen3.6, Kurs-Endpunkt).

Aufruf:
    python -m src.rag "Wie lange bleibt die VPN-Verbindung bestehen?"
    python -m src.rag "..." --retriever hybrid --n 5
"""

import argparse
import textwrap

from src.llm import chat
from src.search import embedding_search
from src.vectorstore import DEFAULT_COLLECTION, create_collection

# Die drei Schlüsselelemente aus der Vorlesung:
#   1. Grounding   — nur aus dem Kontext antworten
#   2. Enthaltung  — bei fehlender Info ehrlich passen (statt zu halluzinieren)
#   3. Zitierpflicht — jede Aussage mit [Quelle N] belegen
ABSTENTION = "Ich habe dazu keine Information in der Wissensbasis."

RAG_SYSTEM_PROMPT = (
    "Beantworte die Frage AUSSCHLIESSLICH anhand des bereitgestellten Kontexts. "
    "Nutze kein eigenes Vorwissen und erfinde nichts. "
    f"Enthält der Kontext die Antwort nicht, antworte wörtlich: '{ABSTENTION}' "
    "Zitiere jede Aussage mit der passenden Quelle in der Form [Quelle N]. "
    "Antworte knapp und auf Deutsch."
)


def build_context(hits: list[dict]) -> str:
    """Formatiert die Treffer als nummerierten Kontextblock mit Quellen-Labels.

    Reihenfolge = Retrieval-Rang (relevantester Chunk zuerst). Das ist bewusst:
    LLMs beachten Anfang und Ende des Kontexts stärker als die Mitte
    ("Lost in the Middle") — der beste Treffer gehört nach vorn.

    Beispiel:
        [Quelle 1 | vpn-zugang.md]: Der Fernzugriff erfolgt über Cisco ...
        [Quelle 2 | passwort-und-konto.md]: Passwörter brauchen 14 Zeichen ...
    """
    blocks = []
    for hit in hits:
        text = " ".join(hit["text"].split())
        blocks.append(f'[Quelle {hit["rank"]} | {hit["source"]}]: {text}')
    return "\n\n".join(blocks)


def build_prompt(query: str, hits: list[dict]) -> str:
    """Baut den User-Prompt: erst der Kontextblock, dann die Frage."""
    return (
        f"KONTEXT:\n{build_context(hits)}\n\n"
        f"FRAGE: {query}\n\n"
        "ANTWORT (nur aus dem Kontext, mit [Quelle N]):"
    )


def answer(
    query: str,
    n_results: int = 5,
    collection=None,
    retriever: str = "dense",
) -> dict:
    """Beantwortet eine Frage per RAG.

    Ablauf: retrieve (dense: ``embedding_search``, hybrid: ``hybrid_search``) →
    augment (``build_context`` + Prompt) → generate (``chat``). Gibt
    ``{"answer", "sources", "hits"}`` zurück — Antwort UND Belege, damit Zitate
    nachvollziehbar sind und die Evaluation auf den Kontext zugreifen kann.
    """
    if collection is None:
        collection = create_collection(DEFAULT_COLLECTION)

    if retriever == "hybrid":
        from src.hybrid import hybrid_search

        hits = hybrid_search(collection, query, n_results=n_results)
    else:
        hits = embedding_search(collection, query, n_results=n_results)

    if not hits:
        return {"answer": ABSTENTION, "sources": [], "hits": []}

    response = chat(build_prompt(query, hits), system=RAG_SYSTEM_PROMPT)
    sources = [{"rank": hit["rank"], "source": hit["source"]} for hit in hits]
    return {"answer": response.strip(), "sources": sources, "hits": hits}


def _print_answer(query: str, result: dict) -> None:
    print(f"Frage: {query}\n")
    print("Antwort:")
    for line in textwrap.wrap(result["answer"], width=76) or [""]:
        print(f"  {line}")
    if result["sources"]:
        print("\nQuellen:")
        for source in result["sources"]:
            print(f'  [Quelle {source["rank"]}] {source["source"]}')


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RAG-Client: beantwortet Fragen belegt über die LeineTech-Wissensbasis"
    )
    parser.add_argument("query", help="Frage in natürlicher Sprache")
    parser.add_argument(
        "--retriever",
        choices=["dense", "hybrid"],
        default="dense",
        help="Retrieval-Verfahren (Default: dense)",
    )
    parser.add_argument("--n", type=int, default=5, help="Anzahl Kontext-Chunks (Default: 5)")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Name der Collection")
    args = parser.parse_args()

    collection = create_collection(args.collection)
    if collection.count() == 0:
        raise SystemExit(
            "Collection ist leer — zuerst die Pipeline laufen lassen: "
            "python -m src.ingest docs"
        )

    result = answer(
        args.query,
        n_results=args.n,
        collection=collection,
        retriever=args.retriever,
    )
    _print_answer(args.query, result)


if __name__ == "__main__":
    main()
