"""Tests fuer Document-Loader und Chunking — offline, ohne Modell oder Netz.

Diese Tests sichern das Verhalten der Ingestion-Pipeline-Bausteine ab, die
KEINEN Embedding-Download und keine Vektordatenbank brauchen. Embedder und
Vectorstore werden im Lab manuell getestet (siehe labs/vl04-lab.md).
"""

from src.chunker import chunk_document
from src.loader import load_documents


def test_load_documents_liest_md_dateien(tmp_path):
    (tmp_path / "a.md").write_text("Inhalt A", encoding="utf-8")
    (tmp_path / "b.md").write_text("Inhalt B", encoding="utf-8")
    (tmp_path / "ignore.txt").write_text("kein Markdown", encoding="utf-8")

    docs = load_documents(str(tmp_path))

    assert len(docs) == 2
    assert {d["metadata"]["source"] for d in docs} == {"a.md", "b.md"}
    assert all("text" in d for d in docs)


def test_load_documents_ueberspringt_leere_dateien(tmp_path):
    (tmp_path / "voll.md").write_text("etwas Text", encoding="utf-8")
    (tmp_path / "leer.md").write_text("   \n  ", encoding="utf-8")

    docs = load_documents(str(tmp_path))

    assert len(docs) == 1
    assert docs[0]["metadata"]["source"] == "voll.md"


def test_load_documents_sortiert_stabil(tmp_path):
    for name in ["c.md", "a.md", "b.md"]:
        (tmp_path / name).write_text("x", encoding="utf-8")

    sources = [d["metadata"]["source"] for d in load_documents(str(tmp_path))]

    assert sources == ["a.md", "b.md", "c.md"]


def test_load_documents_fehlendes_verzeichnis():
    try:
        load_documents("gibt/es/nicht")
        assert False, "FileNotFoundError erwartet"
    except FileNotFoundError:
        pass


def _make_doc(text, source="test.md"):
    return {"text": text, "metadata": {"source": source}}


def test_chunk_kleines_dokument_bleibt_ein_chunk():
    doc = _make_doc("Ein kurzer Absatz, der locker in einen Chunk passt.")
    chunks = chunk_document(doc, chunk_size=500, chunk_overlap=50)

    assert len(chunks) == 1
    assert chunks[0]["text"] == doc["text"]


def test_chunk_grosses_dokument_wird_geteilt():
    absatz = "Dies ist ein Satz mit ordentlich Fuellmaterial darin. "
    doc = _make_doc("\n\n".join([absatz * 3] * 6))

    chunks = chunk_document(doc, chunk_size=200, chunk_overlap=20)

    assert len(chunks) > 1


def test_chunk_ids_sind_eindeutig_und_praefixiert():
    doc = _make_doc("\n\n".join(f"Absatz Nummer {i} mit genug Text." * 5 for i in range(8)),
                    source="quelle.md")
    chunks = chunk_document(doc, chunk_size=150, chunk_overlap=20)

    ids = [c["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids)), "chunk_ids muessen eindeutig sein"
    assert all(cid.startswith("quelle.md::") for cid in ids)


def test_chunk_erbt_metadaten():
    doc = _make_doc("Text " * 100, source="vpn-zugang.md")
    chunks = chunk_document(doc, chunk_size=100, chunk_overlap=10)

    assert all(c["metadata"]["source"] == "vpn-zugang.md" for c in chunks)


def test_chunk_ueberlappung_verbindet_nachbarn():
    # Zwei klar getrennte Absaetze, die einzeln je > chunk_size sind → mehrere
    # Chunks mit Ueberlappung. Der zweite Chunk traegt das Ende des ersten.
    doc = _make_doc(("A" * 120) + "\n\n" + ("B" * 120))
    chunks = chunk_document(doc, chunk_size=130, chunk_overlap=15)

    assert len(chunks) >= 2
    # Ueberlappung: der Anfang des zweiten Chunks stammt aus dem ersten.
    tail_of_first = chunks[0]["text"][-15:]
    assert chunks[1]["text"].startswith(tail_of_first)
