"""Ingestion-Pipeline: Dokumente → Chunks → Embeddings → ChromaDB.

Verbindet die vier Bausteine loader, chunker, embedder und vectorstore zu der
Kette aus der Vorlesung. Nach dem Lauf liegt die durchsuchbare Wissensbasis in
`./chroma_db`. Abgefragt wird sie mit `python -m src.search "..."`.

Aufruf:
    python -m src.ingest docs
    python -m src.ingest docs --dry-run          # nur laden und chunken, ohne Endpunkt
    python -m src.ingest docs --chunk-size 1000 --collection leinetech_kb_1000
"""

import argparse

from src.chunker import chunk_document
from src.embedder import embed_texts
from src.loader import load_documents
from src.vectorstore import DEFAULT_COLLECTION, create_collection, ingest


def run_pipeline(
    docs_dir: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    collection_name: str = DEFAULT_COLLECTION,
) -> dict:
    """Lädt, chunkt, bettet ein und speichert alle Dokumente aus docs_dir.

    Gibt eine Zusammenfassung mit den Zahlen aus der Konsolenausgabe zurück.
    """
    documents = load_documents(docs_dir)
    print(f"{len(documents)} Dokumente geladen")

    chunks = chunk_documents(documents, chunk_size, chunk_overlap)
    print(f"{len(chunks)} Chunks erzeugt")

    embeddings = embed_texts([chunk["text"] for chunk in chunks])
    dimensions = len(embeddings[0]) if embeddings else 0
    print(f"{len(embeddings)} Embeddings berechnet ({dimensions} Dimensionen)")

    # Erst nach dem Embedding aufräumen: Fällt der Endpunkt aus, bleibt der alte Index erhalten.
    collection = create_collection(collection_name)
    remove_old_chunks(collection, documents)
    ingest(collection, chunks, embeddings)
    count = collection.count()
    print(f"Collection '{collection_name}': {count} Einträge gespeichert")

    return {
        "documents": len(documents),
        "chunks": len(chunks),
        "dimensions": dimensions,
        "collection_count": count,
    }


def preview(docs_dir: str, chunk_size: int = 500, chunk_overlap: int = 50) -> int:
    """Probelauf ohne Endpunkt: lädt und chunkt nur und zeigt die Zahlen je Dokument.

    So lässt sich die Wirkung von chunk_size prüfen, bevor Embeddings berechnet werden.
    Gibt die Gesamtzahl der Chunks zurück.
    """
    documents = load_documents(docs_dir)
    print(f"{len(documents)} Dokumente geladen")
    total = 0
    for document in documents:
        count = len(chunk_document(document, chunk_size, chunk_overlap))
        total += count
        source = document["metadata"]["source"]
        print(f"  {source}: {len(document['text'])} Zeichen, {count} Chunks")
    print(f"{total} Chunks erzeugt (Probelauf: keine Embeddings, nichts gespeichert)")
    return total


def chunk_documents(documents: list[dict], chunk_size: int, chunk_overlap: int) -> list[dict]:
    """Zerlegt alle Dokumente und liefert die Chunks in Dokumentreihenfolge."""
    chunks = []
    for document in documents:
        chunks.extend(chunk_document(document, chunk_size, chunk_overlap))
    return chunks


def remove_old_chunks(collection, documents: list[dict]) -> None:
    """Löscht alle gespeicherten Chunks der Quellen, die gleich neu gespeichert werden.

    `upsert` überschreibt nur Einträge mit gleicher chunk_id. Liefert ein
    Dokument nach einer Änderung weniger Chunks (neuer Text oder größere
    chunk_size), blieben die alten Chunks mit den höheren Nummern sonst liegen
    und verfälschten jede spätere Suche.
    """
    sources = sorted({document["metadata"]["source"] for document in documents})
    if sources and collection.count() > 0:
        collection.delete(where={"source": {"$in": sources}})


def main() -> None:
    """Kommandozeile: python -m src.ingest <docs_dir> [Optionen]."""
    parser = argparse.ArgumentParser(
        description="Ingestion-Pipeline: Dokumente → Chunks → Embeddings → ChromaDB"
    )
    parser.add_argument("docs_dir", help="Verzeichnis mit den .md-Dokumenten (z. B. docs)")
    parser.add_argument(
        "--chunk-size", type=int, default=500, help="Chunk-Größe in Zeichen (Default: 500)"
    )
    parser.add_argument(
        "--chunk-overlap", type=int, default=50, help="Überlappung in Zeichen (Default: 50)"
    )
    parser.add_argument(
        "--collection",
        default=DEFAULT_COLLECTION,
        help=f"Name der Collection (Default: {DEFAULT_COLLECTION})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="nur laden und chunken, ohne Embeddings und ohne Speichern",
    )
    args = parser.parse_args()

    if args.dry_run:
        preview(args.docs_dir, args.chunk_size, args.chunk_overlap)
        return

    run_pipeline(
        docs_dir=args.docs_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        collection_name=args.collection,
    )


if __name__ == "__main__":
    main()
