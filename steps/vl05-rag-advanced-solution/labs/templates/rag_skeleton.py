"""Lab VL 5, Teil 1: Vorlage für den RAG-Client (kopieren nach src/rag.py).

    cp labs/templates/rag_skeleton.py src/rag.py

Fertig sind die Imports, der Enthaltungs-Wortlaut, die Retriever-Auswahl und das
CLI. Eure Arbeit sind die TODOs:

    TODO 1  RAG_SYSTEM_PROMPT: die drei Pflichtelemente eines RAG-Prompts
    TODO 2  build_context: Kontextblock mit Zitat-Labels
    TODO 3  build_prompt: erst der Kontext, dann die Frage
    TODO 4  answer: retrieve → augment → generate

Selbsttest ohne Endpunkt:  python -m pytest tests/test_rag.py -q
Aufruf mit Endpunkt:       python -m src.rag "Wie lange bleibt die VPN-Verbindung bestehen?"
"""

import argparse
import textwrap

from src.llm import chat
from src.search import embedding_search, keyword_search
from src.vectorstore import DEFAULT_COLLECTION, create_collection

# Fester Wortlaut der Enthaltung. Weil der Satz feststeht, lässt er sich per
# String-Vergleich testen (siehe is_abstention in src/rag_eval.py).
ABSTENTION = "Ich habe dazu keine Information in der Wissensbasis."

# TODO 1: Die Vorlage startet mit einem naiven Prompt. Ergänzt die drei
# Pflichtelemente eines RAG-Prompts:
#   1. Grounding: nur aus dem Kontext antworten, kein Vorwissen
#   2. Enthaltung: fehlt die Antwort im Kontext, wörtlich ABSTENTION antworten
#      (Tipp: f-String, damit der Wortlaut exakt übereinstimmt)
#   3. Zitierpflicht: jede Aussage mit [Quelle N] belegen
RAG_SYSTEM_PROMPT = "Du bist ein hilfreicher Assistent. Beantworte die Frage."

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

    Beispiel:
        [Quelle 1 | vpn-zugang.md]: Nach 12 Stunden oder 30 Minuten Inaktivität ...

        [Quelle 2 | it-support-prozesse.md]: Hotline intern -4242
    """
    # TODO 2: Pro Treffer eine Zeile "[Quelle N | <source>]: <text>" bauen.
    #   - N zählt ab 1 in Trefferreihenfolge (Tipp: enumerate(hits, start=1)).
    #   - Zeilenumbrüche im Text durch Leerzeichen ersetzen: " ".join(text.split()).
    #   - Die Zeilen mit einer Leerzeile trennen: "\n\n".join(...).
    raise NotImplementedError("TODO 2: build_context in src/rag.py implementieren")


def build_prompt(query: str, context: str) -> str:
    """Baut den User-Prompt: erst der Kontextblock, dann die markierte Frage."""
    # TODO 3: Einen String mit den Abschnitten "KONTEXT:" und "FRAGE:" zurückgeben.
    #   Der Kontext kommt zuerst, die Frage danach. So liest das Modell die Frage
    #   nicht als Teil des Kontexts.
    raise NotImplementedError("TODO 3: build_prompt in src/rag.py implementieren")


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

    # TODO 4: Die drei Schritte verbinden.
    #   a) Retrieve: hits = retriever(collection, query, n_results=n_results)
    #   b) Keine Treffer? Dann ABSTENTION zurückgeben, ohne chat() aufzurufen.
    #   c) Augment: context = build_context(hits) und prompt = build_prompt(query, context)
    #   d) Generate: response = chat(prompt, system=system_prompt)
    #   e) sources als Liste [{"label": "Quelle 1", "source": ...}, ...] bauen
    #   f) {"answer": response.strip(), "sources": ..., "hits": ..., "context": ...}
    raise NotImplementedError("TODO 4: answer in src/rag.py implementieren")


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
