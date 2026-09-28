"""Vektordatenbank: speichert und durchsucht Embeddings mit ChromaDB.

ChromaDB legt die Vektoren dauerhaft unter `./chroma_db` ab und findet per
Nächste-Nachbarn-Suche die ähnlichsten zu einem Anfrage-Vektor. So bleiben die
einmal berechneten Embeddings zwischen zwei Aufrufen erhalten. `ingest.py`
schreibt, `search.py` liest.
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
    """Persistenter ChromaDB-Client unter ./chroma_db, ohne Telemetrie."""
    return chromadb.PersistentClient(
        path=DB_PATH,
        settings=Settings(anonymized_telemetry=False),
    )


def create_collection(name: str = DEFAULT_COLLECTION) -> chromadb.Collection:
    """Öffnet die Collection oder legt sie an, falls es sie noch nicht gibt.

    Ein zweiter Lauf der Pipeline nutzt so die bestehende Collection weiter.
    Mit `create_collection` würde er scheitern.
    """
    return get_client().get_or_create_collection(name=name)


def ingest(collection, chunks: list[dict], embeddings: list[list[float]]) -> None:
    """Speichert Chunks mit ihren Embeddings und Metadaten in der Collection.

    Nutzt upsert: Eine vorhandene chunk_id wird überschrieben. add würde den
    alten Eintrag stillschweigend behalten. So kann die Pipeline gefahrlos
    erneut laufen.

    Raises:
        ValueError: wenn Chunk- und Embedding-Anzahl nicht zusammenpassen.
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"{len(chunks)} Chunks, aber {len(embeddings)} Embeddings. "
            "Die Anzahl muss übereinstimmen."
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
    """Sucht die ähnlichsten Chunks zu einem oder mehreren Anfrage-Vektoren.

    Gibt das ChromaDB-Ergebnis zurück (ids, documents, metadatas, distances).
    Kleinere Distanz heißt ähnlicher.
    """
    return collection.query(
        query_embeddings=query_embedding,
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )
