"""Offline-Tests für Embedder, Vektordatenbank, Ingestion und Suche.

Das Embedding-Modell wird durch eine Attrappe ersetzt (monkeypatch auf
`litellm.embedding`). ChromaDB läuft lokal in einem temporären Ordner. So
laufen die Tests ohne Netz, ohne API-Key und an jedem Wochentag. Ob der echte
Kurs-Endpunkt antwortet, prüft ihr im Lab mit den Befehlen aus Teil 2.

Die Testnamen tragen den Lab-Teil. Einzeln prüfen, z. B.:
    python -m pytest tests/test_pipeline_offline.py -q -k teil2a
"""

import math
import os
import re
import zlib
from pathlib import Path

import pytest

# litellm lädt beim Import sonst eine Preisliste aus dem Internet nach. Die Tests
# laufen ohne Netz. Die Variable muss VOR dem Import gesetzt sein (wie in src/llm.py).
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

# pylint: disable=wrong-import-position
import litellm  # noqa: E402

from src import embedder, ingest, search, vectorstore  # noqa: E402

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
FAKE_DIMENSIONS = 64


def fake_vector(text: str) -> list[float]:
    """Bag-of-Words-Vektor als Ersatz für ein echtes Embedding.

    Jedes Wort erhöht eine per Hash gewählte Dimension. Texte mit gemeinsamen
    Wörtern liegen dadurch nah beieinander. Der Vektor wird wie bei
    qwen3-embed-4b auf Länge 1 normiert.
    """
    vector = [0.0] * FAKE_DIMENSIONS
    for word in re.findall(r"\w+", text.lower()):
        vector[zlib.crc32(word.encode("utf-8")) % FAKE_DIMENSIONS] += 1.0
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


@pytest.fixture
def fake_endpoint(monkeypatch):
    """Ersetzt litellm.embedding. Liefert die Liste der Aufrufe zum Prüfen."""
    calls = []

    def fake_embedding(model, input, **kwargs):  # pylint: disable=redefined-builtin
        calls.append({"model": model, "input": list(input)})
        data = [{"index": i, "embedding": fake_vector(text)} for i, text in enumerate(input)]
        return {"data": list(reversed(data))}  # absichtlich verdreht: embed_texts muss sortieren

    monkeypatch.setattr(litellm, "embedding", fake_embedding)
    return calls


@pytest.fixture
def local_db(tmp_path, monkeypatch):
    """Lenkt ChromaDB in einen temporären Ordner um."""
    monkeypatch.setattr(vectorstore, "DB_PATH", str(tmp_path / "chroma_db"))
    return tmp_path


def _write_docs(folder: Path, docs: dict[str, str]) -> str:
    folder.mkdir()
    for name, text in docs.items():
        (folder / name).write_text(text, encoding="utf-8")
    return str(folder)


def _chunk(chunk_id: str, text: str) -> dict:
    return {"text": text, "metadata": {"source": chunk_id.split("::")[0]}, "chunk_id": chunk_id}


def _index(chunks: list[dict]):
    collection = vectorstore.create_collection("test_kb")
    vectorstore.ingest(collection, chunks, [fake_vector(c["text"]) for c in chunks])
    return collection


# ---------------------------------------------------------------- Teil 2A: Embedder


def test_teil2a_embed_texts_leere_liste_ohne_netzaufruf(fake_endpoint):
    assert embedder.embed_texts([]) == []
    assert fake_endpoint == [], "für eine leere Liste darf kein Aufruf stattfinden"


def test_teil2a_embed_texts_behaelt_eingabereihenfolge(fake_endpoint):
    texts = ["VPN Verbindung", "Drucker Toner", "Passwort ändern"]

    vectors = embedder.embed_texts(texts)

    assert vectors == [fake_vector(text) for text in texts]
    assert len(fake_endpoint) == 1, "alle Texte in einem Aufruf"


def test_teil2a_embed_texts_nutzt_hosted_vllm_provider(fake_endpoint):
    embedder.embed_texts(["Test"])

    assert fake_endpoint[0]["model"].startswith("hosted_vllm/")


# ---------------------------------------------------------------- Teil 2B: Vektordatenbank


def test_teil2b_ingest_verlangt_gleich_viele_chunks_und_embeddings(local_db):
    collection = vectorstore.create_collection("test_kb")
    chunk = {"text": "x", "metadata": {"source": "a.md"}, "chunk_id": "a.md::0"}

    with pytest.raises(ValueError):
        vectorstore.ingest(collection, [chunk], [])


def test_teil2b_ingest_speichert_ids_texte_und_metadaten(local_db):
    collection = vectorstore.create_collection("test_kb")
    chunks = [
        {"text": "VPN einrichten", "metadata": {"source": "vpn.md"}, "chunk_id": "vpn.md::0"},
        {
            "text": "Toner wechseln",
            "metadata": {"source": "drucker.md"},
            "chunk_id": "drucker.md::0",
        },
    ]

    vectorstore.ingest(collection, chunks, [fake_vector(c["text"]) for c in chunks])

    stored = collection.get(ids=["vpn.md::0"], include=["documents", "metadatas"])
    assert collection.count() == 2
    assert stored["documents"] == ["VPN einrichten"]
    assert stored["metadatas"] == [{"source": "vpn.md"}]


def test_teil2b_ingest_ueberschreibt_vorhandene_id(local_db):
    # Ein geänderter Text mit derselben chunk_id muss ankommen.
    # add würde den alten Eintrag stillschweigend behalten, upsert überschreibt ihn.
    collection = vectorstore.create_collection("test_kb")
    alt = _chunk("vpn.md::0", "VPN alt")
    neu = _chunk("vpn.md::0", "VPN neu eingerichtet")

    vectorstore.ingest(collection, [alt], [fake_vector(alt["text"])])
    vectorstore.ingest(collection, [neu], [fake_vector(neu["text"])])

    stored = collection.get(ids=["vpn.md::0"], include=["documents"])
    assert collection.count() == 1
    assert stored["documents"] == ["VPN neu eingerichtet"], "upsert statt add verwenden"


def test_teil2b_search_liefert_distanzen(local_db):
    collection = _index(
        [
            _chunk("vpn.md::0", "VPN Gateway eintragen und Verbindung aufbauen"),
            _chunk("drucker.md::0", "Toner wechseln und Papierstau beheben"),
        ]
    )

    result = vectorstore.search(collection, [fake_vector("Toner wechseln")], n_results=2)

    assert result["ids"] == [["drucker.md::0", "vpn.md::0"]]
    assert result["documents"][0][0] == "Toner wechseln und Papierstau beheben"
    assert result["metadatas"][0][0] == {"source": "drucker.md"}
    nearest, farthest = result["distances"][0]
    assert 0.0 <= nearest < farthest, "kleinere Distanz heißt ähnlicher"


# ---------------------------------------------------------------- Teil 2C: Pipeline


def test_teil2c_dry_run_braucht_keinen_endpunkt(local_db, fake_endpoint):
    total = ingest.preview(str(DOCS_DIR))

    assert total > 0
    assert fake_endpoint == [], "der Probelauf darf keine Embeddings anfordern"
    assert not (local_db / "chroma_db").exists(), "der Probelauf darf nichts speichern"


def test_teil2c_run_pipeline_ist_wiederholbar(local_db, fake_endpoint):
    docs_dir = _write_docs(
        local_db / "docs", {"a.md": "Erster Artikel.", "b.md": "Zweiter Artikel."}
    )

    first = ingest.run_pipeline(docs_dir, collection_name="test_kb")
    second = ingest.run_pipeline(docs_dir, collection_name="test_kb")

    assert first["chunks"] == 2
    assert first["dimensions"] == FAKE_DIMENSIONS
    assert second["collection_count"] == first["collection_count"] == 2


def test_teil2c_endpunktausfall_laesst_alten_index_stehen(local_db, fake_endpoint, monkeypatch):
    docs_dir = _write_docs(
        local_db / "docs", {"a.md": "Erster Artikel.", "b.md": "Zweiter Artikel."}
    )
    ingest.run_pipeline(docs_dir, collection_name="test_kb")

    def endpoint_down(*args, **kwargs):
        raise ConnectionError("Kurs-Endpunkt nicht erreichbar")

    monkeypatch.setattr(litellm, "embedding", endpoint_down)
    with pytest.raises(ConnectionError):
        ingest.run_pipeline(docs_dir, collection_name="test_kb")

    count = vectorstore.create_collection("test_kb").count()
    assert count == 2, "alter Index muss erhalten bleiben"


def test_teil2c_run_pipeline_entfernt_veraltete_chunks(local_db, fake_endpoint):
    # Größere Chunks ergeben weniger Chunks. Die alten Chunks mit höheren
    # Nummern dürfen danach nicht mehr in der Collection liegen.
    small = ingest.run_pipeline(str(DOCS_DIR), chunk_size=500, collection_name="test_kb")
    large = ingest.run_pipeline(str(DOCS_DIR), chunk_size=1000, collection_name="test_kb")

    assert large["chunks"] < small["chunks"]
    assert large["collection_count"] == large["chunks"]


# ---------------------------------------------------------------- Teil 3: Suche


def test_teil3_distance_to_similarity_ergibt_kosinus():
    a = fake_vector("VPN Verbindung trennt nach 30 Minuten")
    b = fake_vector("VPN trennt die Verbindung")
    cosine = sum(x * y for x, y in zip(a, b))
    squared_l2 = sum((x - y) ** 2 for x, y in zip(a, b))

    assert search._distance_to_similarity(squared_l2) == pytest.approx(cosine)


def test_teil3_embedding_search_liefert_rangliste_mit_chunk_id(local_db, fake_endpoint):
    collection = _index(
        [
            _chunk("vpn.md::0", "VPN Gateway eintragen und Verbindung aufbauen"),
            _chunk("drucker.md::0", "Toner wechseln und Papierstau beheben"),
        ]
    )

    hits = search.embedding_search(collection, "Toner wechseln", n_results=2)

    assert [hit["rank"] for hit in hits] == [1, 2]
    assert hits[0]["chunk_id"] == "drucker.md::0"
    assert hits[0]["source"] == "drucker.md"
    assert 0.0 <= hits[1]["score"] <= hits[0]["score"] <= 1.0


def test_teil3_keyword_search_unterscheidet_geraete_ids(local_db, fake_endpoint):
    collection = _index(
        [
            _chunk("drucker.md::0", "LT-PRN-03 steht im 3. OG"),
            _chunk("drucker.md::1", "LT-PRN-02 steht im 2. OG und kann A3"),
        ]
    )

    hits = search.keyword_search(collection, "Wo steht LT-PRN-02?", n_results=2)

    assert hits[0]["chunk_id"] == "drucker.md::1"
    assert hits[0]["score"] > hits[1]["score"]


def test_teil3_keyword_search_ohne_suchwoerter_liefert_nichts(local_db, fake_endpoint):
    collection = _index([_chunk("a.md::0", "VPN Gateway")])

    assert search.keyword_search(collection, "ist es in der", n_results=3) == []
