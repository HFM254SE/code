"""Vektordatenbank — speichert und durchsucht Chunk-Embeddings mit ChromaDB.

ChromaDB übernimmt das, was man sonst selbst bauen müsste: Vektoren persistent
ablegen und per Nächste-Nachbarn-Suche die ähnlichsten zu einem Query-Vektor
finden. Wir nutzen einen `PersistentClient` unter `./chroma_db`, damit die
einmal berechneten Embeddings zwischen Aufrufen erhalten bleiben — `ingest.py`
schreibt, `search.py` liest.
"""

import logging

import chromadb
from chromadb.config import Settings

DB_PATH = "./chroma_db"
DEFAULT_COLLECTION = "leinetech_kb"

# chromadb 1.0.7 ruft posthog.capture() noch mit der alten Signatur auf; gegen
# neuere posthog-Versionen scheitert das und wird als `logger.error(...)` in die
# Ausgabe geschrieben ("Failed to send telemetry event ..."). Der Logger wird
# stummgeschaltet — zusätzlich zum anonymized_telemetry=False unten.
logging.getLogger("chromadb.telemetry.product.posthog").setLevel(logging.CRITICAL)


def get_client():
    """Persistenter ChromaDB-Client unter ./chroma_db.

    `anonymized_telemetry=False` schaltet die ChromaDB-Telemetrie ab — sonst
    spammt chromadb 1.0.7 bei jedem Aufruf `Failed to send telemetry event ...`
    in die Ausgabe (Inkompatibilität mit neueren posthog-Versionen).
    """
    return chromadb.PersistentClient(
        path=DB_PATH,
        settings=Settings(anonymized_telemetry=False),
    )


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
