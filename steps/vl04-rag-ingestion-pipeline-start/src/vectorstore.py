"""Vektordatenbank: speichert und durchsucht Embeddings mit ChromaDB (Lab VL 4, Teil 2B).

ChromaDB legt die Vektoren dauerhaft unter `./chroma_db` ab und findet per
Nächste-Nachbarn-Suche die ähnlichsten zu einem Anfrage-Vektor. `ingest.py`
schreibt, `search.py` liest.

Prüfen (offline, mit Attrappe):
    python -m pytest tests/test_pipeline_offline.py -q -k teil2b
"""

import logging

import chromadb
from chromadb.config import Settings

DB_PATH = "./chroma_db"
DEFAULT_COLLECTION = "leinetech_kb"

# chromadb 1.0.7 schreibt sonst bei jedem Aufruf "Failed to send telemetry event ..."
# in die Ausgabe. Der Logger wird stummgeschaltet, die Telemetrie unten abgeschaltet.
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)


def get_client():
    """Persistenter ChromaDB-Client unter ./chroma_db, ohne Telemetrie (fertig)."""
    return chromadb.PersistentClient(
        path=DB_PATH,
        settings=Settings(anonymized_telemetry=False),
    )


def create_collection(name: str = DEFAULT_COLLECTION) -> chromadb.Collection:
    """Öffnet die Collection oder legt sie an, falls es sie noch nicht gibt."""
    # TODO Teil 2B-1: get_client().get_or_create_collection(name=name) zurückgeben.
    #   Warum nicht create_collection? Der zweite Lauf der Pipeline würde sonst scheitern.
    raise NotImplementedError("TODO Teil 2B-1: create_collection in src/vectorstore.py")


def ingest(collection, chunks: list[dict], embeddings: list[list[float]]) -> None:
    """Speichert Chunks mit ihren Embeddings und Metadaten in der Collection.

    Raises:
        ValueError: wenn Chunk- und Embedding-Anzahl nicht zusammenpassen.
    """
    # TODO Teil 2B-2:
    #   1. Ist len(chunks) != len(embeddings): ValueError werfen.
    #   2. Keine Chunks: nichts tun.
    #   3. collection.upsert(ids=..., documents=..., embeddings=..., metadatas=...) aufrufen.
    #      ids = chunk["chunk_id"], documents = chunk["text"], metadatas = chunk["metadata"].
    #      upsert statt add: Ein erneuter Lauf überschreibt Einträge mit gleicher ID.
    raise NotImplementedError("TODO Teil 2B-2: ingest in src/vectorstore.py")


def search(collection, query_embedding: list[list[float]], n_results: int = 5) -> dict:
    """Sucht die ähnlichsten Chunks zu einem oder mehreren Anfrage-Vektoren.

    Gibt das ChromaDB-Ergebnis zurück (ids, documents, metadatas, distances).
    Kleinere Distanz heißt ähnlicher.
    """
    # TODO Teil 2B-3: collection.query(query_embeddings=query_embedding, n_results=n_results,
    #   include=["documents", "metadatas", "distances"]) zurückgeben.
    raise NotImplementedError("TODO Teil 2B-3: search in src/vectorstore.py")
