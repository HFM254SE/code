"""Vektordatenbank — speichert und durchsucht Chunk-Embeddings mit ChromaDB.

ChromaDB übernimmt das, was man sonst selbst bauen müsste: Vektoren persistent
ablegen und per Nächste-Nachbarn-Suche die ähnlichsten zu einem Query-Vektor
finden. Wir nutzen einen `PersistentClient` unter `./chroma_db`, damit die
einmal berechneten Embeddings zwischen Aufrufen erhalten bleiben — `ingest.py`
schreibt, `search.py` liest.
"""

import chromadb

DB_PATH = "./chroma_db"
DEFAULT_COLLECTION = "leinetech_kb"


def get_client():
    """Persistenter ChromaDB-Client unter ./chroma_db."""
    return chromadb.PersistentClient(path=DB_PATH)


def create_collection(name: str = DEFAULT_COLLECTION) -> chromadb.Collection:
    """Erstellt (oder öffnet) eine persistente ChromaDB-Collection.

    `get_or_create` ist idempotent: erneutes Ausführen der Pipeline wirft keinen
    Fehler, sondern nutzt die bestehende Collection weiter.
    """
    return get_client().get_or_create_collection(name=name)


def ingest(collection, chunks: list[dict], embeddings: list[list[float]]) -> None:
    """Speichert Chunks mit ihren Embeddings und Metadaten in der Collection.

    Nutzt `upsert`: gleiche `chunk_id` überschreibt den bestehenden Eintrag,
    statt einen DuplicateIDError zu werfen. So kann die Pipeline gefahrlos
    erneut laufen (Grundlage für Dokument-Updates, vgl. Reflexion im Lab).

    Raises:
        ValueError: wenn Chunk- und Embedding-Anzahl nicht zusammenpassen.
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"{len(chunks)} Chunks, aber {len(embeddings)} Embeddings — "
            "das muss 1:1 passen."
        )
    if not chunks:
        return

    collection.upsert(
        ids=[chunk["chunk_id"] for chunk in chunks],
        documents=[chunk["text"] for chunk in chunks],
        embeddings=embeddings,
        metadatas=[chunk["metadata"] for chunk in chunks],
    )


def search(collection, query_embedding: list[list[float]], n_results: int = 5) -> dict:
    """Sucht die ähnlichsten Chunks zu einem (oder mehreren) Query-Embedding(s).

    Gibt das ChromaDB-Ergebnis zurück (ids, documents, metadatas, distances).
    Distanzen sind kleiner = ähnlicher.
    """
    return collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
