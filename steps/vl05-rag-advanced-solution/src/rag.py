"""RAG-Client: Retrieve → Augment → Generate über die LeineTech-Wissensbasis.

Die Suche aus VL 4 endet bei einer Trefferliste. Dieses Modul hängt die zwei
fehlenden Schritte an:

    Frage → Retrieve (VL 4): Top-k Chunks
          → Augment: Kontextblock mit Zitat-Labels, System-Prompt mit Grounding,
            Enthaltung und Zitierpflicht
          → Generate: Das LLM antwortet belegt, z. B.
            "Nach 12 Stunden oder 30 Minuten Inaktivität. [Quelle 1]"

Der Retriever ist austauschbar (dense, keyword, hybrid). Die Generierung läuft
über src/llm.py und den Kurs-Endpunkt.

Aufruf:
    python -m src.rag "Wie lange bleibt die VPN-Verbindung bestehen?"
    python -m src.rag "Welche Durchwahl hat Bernd Hagedorn?" --retriever hybrid --n 3
"""

import argparse
import textwrap

from src.llm import chat
from src.search import embedding_search, keyword_search
from src.vectorstore import DEFAULT_COLLECTION, create_collection

# Fester Wortlaut der Enthaltung. Weil der Satz feststeht, lässt er sich per
# String-Vergleich testen (siehe is_abstention in src/rag_eval.py).
ABSTENTION = "Ich habe dazu keine Information in der Wissensbasis."

# Die drei Pflichtelemente eines RAG-Prompts:
#   1. Grounding: nur aus dem Kontext antworten
#   2. Enthaltung: fester Wortlaut, wenn der Kontext die Antwort nicht enthält
#   3. Zitierpflicht: jede Aussage mit [Quelle N] belegen
RAG_SYSTEM_PROMPT = (
    "Beantworte die Frage AUSSCHLIESSLICH anhand des bereitgestellten Kontexts. "
    "Nutze kein eigenes Vorwissen und erfinde nichts. "
    f"Enthält der Kontext die Antwort nicht, antworte wörtlich: '{ABSTENTION}' "
    "Zitiere jede Aussage mit der passenden Quelle in der Form [Quelle N]. "
    "Antworte knapp und auf Deutsch."
)

RETRIEVER_NAMES = ("dense", "keyword", "hybrid")


def resolve_retriever(name: str):
    """Liefert die Suchfunktion zum Namen "dense", "keyword" oder "hybrid".

    Alle drei haben dieselbe Signatur (collection, query, n_results) und liefern
    Treffer im Format {"rank", "chunk_id", "source", "score", "text"}.
    """
    if name == "hybrid":
        # Import erst hier: src/hybrid.py entsteht im Lab erst in Teil 2.
        from src.hybrid import hybrid_search

        return hybrid_search
    retrievers = {"dense": embedding_search, "keyword": keyword_search}
    return retrievers[name]


def build_context(hits: list[dict]) -> str:
    """Formatiert die Treffer als nummerierten Kontextblock mit Zitat-Labels.

    Die Reihenfolge folgt dem Retrieval-Rang. Der beste Treffer steht vorn, weil
    Modelle die Mitte eines langen Kontexts schlechter nutzen (Lost in the Middle).
    Zeilenumbrüche im Chunk werden zu Leerzeichen, damit jeder Chunk genau eine
    Zeile bleibt. Tabellen verlieren dabei ihre Zeilen, bleiben aber lesbar.

    Beispiel:
        [Quelle 1 | vpn-zugang.md]: Nach 12 Stunden oder 30 Minuten Inaktivität ...

        [Quelle 2 | it-support-prozesse.md]: Hotline intern -4242
    """
    blocks = []
    for number, hit in enumerate(hits, start=1):
        text = " ".join(hit["text"].split())
        blocks.append(f"[Quelle {number} | {hit['source']}]: {text}")
    return "\n\n".join(blocks)


def build_prompt(query: str, context: str) -> str:
    """Baut den User-Prompt: erst der Kontextblock, dann die markierte Frage."""
    return (
        f"KONTEXT:\n{context}\n\n"
        f"FRAGE: {query}\n\n"
        "ANTWORT (nur aus dem Kontext, mit [Quelle N]):"
    )


def answer(
    query: str,
    n_results: int = 5,
    collection=None,
    retriever=embedding_search,
    system_prompt: str = RAG_SYSTEM_PROMPT,
) -> dict:
    """Beantwortet eine Frage per RAG: retrieve → augment → generate.

    retriever: Suchfunktion wie embedding_search (Default), keyword_search oder
        hybrid_search. Damit läuft dieselbe RAG-Logik mit jedem Retrieval.
    system_prompt: austauschbar für Experimente, z. B. ohne Enthaltungsanweisung.

    Gibt ein Dict zurück:
        answer   Antwort des Modells ohne Leerraum am Anfang und Ende
        sources  [{"label": "Quelle 1", "source": "vpn-zugang.md"}, ...] in Trefferreihenfolge
        hits     die Treffer des Retrievers
        context  der Kontextblock, den das Modell gesehen hat (braucht die Evaluation)

    Liefert der Retriever nichts, gibt es die Enthaltung ohne LLM-Aufruf.
    """
    if collection is None:
        collection = create_collection(DEFAULT_COLLECTION)

    hits = retriever(collection, query, n_results=n_results)
    if not hits:
        return {"answer": ABSTENTION, "sources": [], "hits": [], "context": ""}

    context = build_context(hits)
    response = chat(build_prompt(query, context), system=system_prompt)
    sources = [
        {"label": f"Quelle {number}", "source": hit["source"]}
        for number, hit in enumerate(hits, start=1)
    ]
    return {
        "answer": response.strip(),
        "sources": sources,
        "hits": hits,
        "context": context,
    }


def print_answer(query: str, result: dict) -> None:
    """Gibt Frage, Antwort und die Quellenliste mit Labels aus."""
    print(f"Frage: {query}\n")
    print("Antwort:")
    for line in textwrap.wrap(result["answer"], width=76) or [""]:
        print(f"  {line}")
    if result["sources"]:
        print("\nQuellen:")
        for source in result["sources"]:
            print(f"  [{source['label']}] {source['source']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="RAG-Client: beantwortet Fragen belegt über die LeineTech-Wissensbasis"
    )
    parser.add_argument("query", help="Frage in natürlicher Sprache")
    parser.add_argument(
        "--retriever",
        choices=RETRIEVER_NAMES,
        default="dense",
        help="Retrieval-Verfahren (Default: dense)",
    )
    parser.add_argument("--n", type=int, default=5, help="Anzahl Kontext-Chunks (Default: 5)")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Name der Collection")
    args = parser.parse_args()

    collection = create_collection(args.collection)
    if collection.count() == 0:
        raise SystemExit("Die Collection ist leer. Zuerst indexieren: python -m src.ingest docs")

    result = answer(
        args.query,
        n_results=args.n,
        collection=collection,
        retriever=resolve_retriever(args.retriever),
    )
    print_answer(args.query, result)


if __name__ == "__main__":
    main()
