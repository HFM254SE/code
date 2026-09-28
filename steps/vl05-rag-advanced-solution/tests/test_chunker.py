"""Tests für Document Loader und Chunking: offline, ohne Modell und ohne Netz.

Diese Tests sind die Vorgabe für Lab VL 4, Teil 1. Embedder, Vektordatenbank
und Suche brauchen ein Embedding-Modell. Sie werden getrennt davon mit einer
Attrappe getestet (in VL 4: tests/test_pipeline_offline.py).
"""

import pytest

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
    with pytest.raises(FileNotFoundError):
        load_documents("gibt/es/nicht")


def _make_doc(text, source="test.md"):
    return {"text": text, "metadata": {"source": source}}


def test_chunk_kleines_dokument_bleibt_ein_chunk():
    doc = _make_doc("Ein kurzer Absatz, der locker in einen Chunk passt.")
    chunks = chunk_document(doc, chunk_size=500, chunk_overlap=50)

    assert len(chunks) == 1
    assert chunks[0]["text"] == doc["text"]


def test_chunk_grosses_dokument_wird_geteilt():
    absatz = "Dies ist ein Satz mit ordentlich Füllmaterial darin. "
    doc = _make_doc("\n\n".join([absatz * 3] * 6))

    chunks = chunk_document(doc, chunk_size=200, chunk_overlap=20)

    assert len(chunks) > 1


def test_chunk_ids_sind_eindeutig_und_praefixiert():
    doc = _make_doc("\n\n".join(f"Absatz Nummer {i} mit genug Text." * 5 for i in range(8)),
                    source="quelle.md")
    chunks = chunk_document(doc, chunk_size=150, chunk_overlap=20)

    ids = [c["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids)), "chunk_ids müssen eindeutig sein"
    assert all(cid.startswith("quelle.md::") for cid in ids)


def test_chunk_erbt_metadaten():
    doc = _make_doc("Text " * 100, source="vpn-zugang.md")
    chunks = chunk_document(doc, chunk_size=100, chunk_overlap=10)

    assert all(c["metadata"]["source"] == "vpn-zugang.md" for c in chunks)


def test_chunk_ueberlappung_verbindet_nachbarn():
    # Zwei klar getrennte Absätze, die einzeln je > chunk_size sind, ergeben
    # mehrere Chunks mit Überlappung. Der zweite Chunk trägt das Ende des ersten.
    doc = _make_doc(("A" * 120) + "\n\n" + ("B" * 120))
    chunks = chunk_document(doc, chunk_size=130, chunk_overlap=15)

    assert len(chunks) >= 2
    tail_of_first = chunks[0]["text"][-15:]
    assert chunks[1]["text"].startswith(tail_of_first)


def test_chunk_ueberlappung_beginnt_an_wortgrenze():
    satz = "Der Tunnel wird nicht überlastet, weil Teams direkt ins Internet geht."
    doc = _make_doc("\n\n".join([satz] * 12))
    woerter = {wort.strip(",.") for wort in satz.split()}

    chunks = chunk_document(doc, chunk_size=150, chunk_overlap=30)

    assert len(chunks) > 1
    for chunk in chunks[1:]:
        erstes_wort = chunk["text"].split()[0].strip(",.")
        assert erstes_wort in woerter, f"Überlappung beginnt mitten im Wort: {erstes_wort!r}"


def test_chunk_ueberlappung_bei_kurzem_vorgaenger():
    # Der erste Chunk ist genau chunk_overlap Zeichen lang. Er wird ganz vorangestellt.
    # Das darf keinen IndexError auslösen (z. B. durch previous[-chunk_overlap - 1]).
    doc = _make_doc("a" * 15 + "\n\n" + "b" * 40)

    chunks = chunk_document(doc, chunk_size=20, chunk_overlap=15)

    assert len(chunks) >= 2
    assert chunks[1]["text"].startswith("a" * 15)


def test_chunk_behaelt_satzpunkte():
    # Eine lange Zeile ohne Umbruch zwingt den Chunker bis auf die Satzebene.
    doc = _make_doc("Das VPN trennt nach zwölf Stunden. " * 10)

    chunks = chunk_document(doc, chunk_size=80, chunk_overlap=0)

    assert len(chunks) > 1
    assert all(c["text"].endswith(".") for c in chunks), "Satzpunkte dürfen nicht verloren gehen"


def test_chunk_behaelt_zeilenstruktur():
    doc = _make_doc("# Titel\n\n## Abschnitt\n\n" + "Ein Satz. " * 60)

    chunks = chunk_document(doc, chunk_size=200, chunk_overlap=20)

    assert chunks[0]["text"].startswith("# Titel\n## Abschnitt\n")
