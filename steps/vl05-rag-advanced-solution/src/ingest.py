"""Ingestion-Pipeline: Dokumente → Chunks → Embeddings → ChromaDB.

Das Hauptskript, das die vier Einzelschritte (loader, chunker, embedder,
vectorstore) zu einer Pipeline verbindet — genau die Kette von den Folien.
Nach dem Lauf liegt die durchsuchbare Wissensbasis in `./chroma_db`; abgefragt
wird sie mit `python -m src.search "..."`.

Aufruf:
    python -m src.ingest docs
    python -m src.ingest docs --chunk-size 300 --chunk-overlap 50
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
    """Führt die komplette Ingestion durch und liefert eine Zusammenfassung."""
    # 1. Dokumente laden
    documents = load_documents(docs_dir)
    print(f"{len(documents)} Dokumente geladen")

    # 2. Alle Dokumente chunken
    chunks = []
    for document in documents:
        chunks.extend(chunk_document(document, chunk_size, chunk_overlap))
    print(f"{len(chunks)} Chunks erzeugt")

    # 3. Embeddings berechnen
    embeddings = embed_texts([chunk["text"] for chunk in chunks])
    dimensions = len(embeddings[0]) if embeddings else 0
    print(f"{len(embeddings)} Embeddings berechnet ({dimensions} Dimensionen)")

    # 4. In ChromaDB speichern
    collection = create_collection(collection_name)
    ingest(collection, chunks, embeddings)
    count = collection.count()
    print(f"Collection '{collection_name}': {count} Einträge gespeichert")

    return {
        "documents": len(documents),
        "chunks": len(chunks),
        "dimensions": dimensions,
        "collection_count": count,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingestion-Pipeline: Dokumente → Chunks → Embeddings → ChromaDB"
    )
    parser.add_argument("docs_dir", help="Verzeichnis mit den .md-Dokumenten (z. B. docs)")
    parser.add_argument("--chunk-size", type=int, default=500, help="Ziel-Chunk-Größe (Default: 500)")
    parser.add_argument("--chunk-overlap", type=int, default=50, help="Chunk-Überlappung (Default: 50)")
    parser.add_argument(
        "--collection", default=DEFAULT_COLLECTION, help="Name der Collection"
    )
    args = parser.parse_args()

    run_pipeline(
        docs_dir=args.docs_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap,
        collection_name=args.collection,
    )


if __name__ == "__main__":
    main()
