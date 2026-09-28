"""Tests für die hybride Suche (src/hybrid.py), offline ohne Modell und ohne Netz.

RRF ist reine Rang-Arithmetik. hybrid_search wird mit einer Attrappe für die
dichte Suche und einer kleinen Fake-Collection für die Keyword-Suche geprüft.

Lab Teil 2: Solange src/hybrid.py fehlt, werden diese Tests übersprungen. Nach dem
Kopieren der Vorlage (labs/templates/hybrid_skeleton.py) schlagen sie fehl, bis die
TODOs erledigt sind.
"""

import pytest

hybrid = pytest.importorskip(
    "src.hybrid",
    reason="src/hybrid.py fehlt noch (Lab Teil 2)",
    exc_type=ModuleNotFoundError,
)
reciprocal_rank_fusion = hybrid.reciprocal_rank_fusion


def _hit(text, source="a.md"):
    return {"text": text, "source": source}


def _texts(hits):
    return [hit["text"] for hit in hits]


def test_rrf_belohnt_treffer_in_beiden_listen():
    # B steht in beiden Listen (Rang 2 bzw. 1), A, C und D je nur in einer.
    dense = [_hit("A"), _hit("B"), _hit("C")]
    sparse = [_hit("B"), _hit("D")]

    fused = reciprocal_rank_fusion([dense, sparse])

    assert fused[0]["text"] == "B", "in beiden Listen → höchster RRF-Score"
    assert set(_texts(fused)) == {"A", "B", "C", "D"}


def test_rrf_folienbeispiel():
    # Beispiel aus der Vorlesung: dense A·C·B·D, BM25 B·A·D·E, k = 60.
    dense = [_hit(text) for text in "ACBD"]
    bm25 = [_hit(text) for text in "BADE"]

    fused = reciprocal_rank_fusion([dense, bm25], k=60)

    assert _texts(fused) == list("ABDCE"), "D steht in beiden Listen und schlägt deshalb C"
    assert [round(hit["score"], 4) for hit in fused] == [0.0325, 0.0323, 0.0315, 0.0161, 0.0156]


def test_rrf_kleines_k_laesst_spitzenplaetze_dominieren():
    # Selbstcheck: X steht dense auf Rang 5 und in BM25 auf Rang 2, Y nur dense auf Rang 1.
    filler = [_hit(f"f{i}") for i in range(3)]
    dense = [_hit("Y"), *filler, _hit("X")]
    bm25 = [_hit("g0"), _hit("X")]

    with_k0 = reciprocal_rank_fusion([dense, bm25], k=0)
    with_k60 = reciprocal_rank_fusion([dense, bm25], k=60)

    assert with_k0[0]["text"] == "Y", "k = 0: 1/1 schlägt 1/5 + 1/2"
    assert with_k60[0]["text"] == "X", "k = 60: 1/65 + 1/62 schlägt 1/61"


def test_rrf_beide_listen_schlagen_einzelnen_spitzenplatz():
    # Rang 30 in beiden Listen (2/90) schlägt Rang 1 in nur einer Liste (1/61).
    dense = [_hit("einzeln")] + [_hit(f"d{i}") for i in range(28)] + [_hit("doppelt")]
    bm25 = [_hit(f"b{i}") for i in range(29)] + [_hit("doppelt")]

    fused = reciprocal_rank_fusion([dense, bm25], k=60)

    assert fused[0]["text"] == "doppelt"


def test_rrf_vergibt_fortlaufende_raenge():
    fused = reciprocal_rank_fusion([[_hit("A"), _hit("B")], [_hit("B")]])

    assert [hit["rank"] for hit in fused] == list(range(1, len(fused) + 1))


def test_rrf_score_formel():
    # Eine einzelne Liste, k = 60: Rang 1 → 1/61, Rang 2 → 1/62.
    fused = reciprocal_rank_fusion([[_hit("A"), _hit("B")]], k=60)

    assert fused[0]["score"] == pytest.approx(1 / 61)
    assert fused[1]["score"] == pytest.approx(1 / 62)


def test_rrf_behaelt_quelle_und_chunk_id():
    hit = {"text": "A", "source": "vpn-zugang.md", "chunk_id": "vpn-zugang.md::0"}

    fused = reciprocal_rank_fusion([[hit]])

    assert fused[0]["source"] == "vpn-zugang.md"
    assert fused[0]["chunk_id"] == "vpn-zugang.md::0", "die ID zeigt, welcher Chunk gemeint ist"


def test_rrf_leere_eingabe():
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []


# --- hybrid_search mit Attrappen ------------------------------------------------

HOTLINE = "Hotline intern -4242 für dringende Fälle"
KONTAKT = "Kontaktwege: Ticketportal, E-Mail und Telefon"
ESKALATION = "Leitung IT-Service (Bernd Hagedorn, Durchwahl -4200)"
SOURCE = "it-support-prozesse.md"


class FakeCollection:
    """Liefert wie ChromaDB alle Chunks mit IDs und Metadaten. Mehr braucht keyword_search nicht."""

    def get(self, include=None):
        texts = [HOTLINE, KONTAKT, ESKALATION]
        return {
            "ids": [f"{SOURCE}::{i}" for i in range(len(texts))],
            "documents": texts,
            "metadatas": [{"source": SOURCE}] * len(texts),
        }


@pytest.fixture
def dense_calls(monkeypatch):
    """Ersetzt die dichte Suche: Sie findet Kontakt und Hotline, den Namen nur auf Rang 3."""
    calls = []

    def fake_embedding_search(collection, query, n_results=5):
        calls.append(n_results)
        ranking = [KONTAKT, HOTLINE, ESKALATION][:n_results]
        return [
            {"rank": rank, "source": SOURCE, "score": 1 - rank / 10, "text": text}
            for rank, text in enumerate(ranking, start=1)
        ]

    monkeypatch.setattr(hybrid, "embedding_search", fake_embedding_search)
    monkeypatch.setattr("src.search.embedding_search", fake_embedding_search)
    return calls


QUESTION = "Welche Durchwahl hat Bernd Hagedorn?"


def test_hybrid_search_zieht_keyword_treffer_nach_oben(dense_calls):
    hits = hybrid.hybrid_search(FakeCollection(), QUESTION, n_results=2)

    assert hits[0]["text"] == ESKALATION, "der Name aus der Frage steht nur im Eskalations-Chunk"
    assert len(hits) == 2


def test_hybrid_search_liefert_format_von_embedding_search(dense_calls):
    hits = hybrid.hybrid_search(FakeCollection(), QUESTION, n_results=2)

    assert [hit["rank"] for hit in hits] == [1, 2]
    for hit in hits:
        assert set(hit) >= {"rank", "chunk_id", "source", "score", "text"}


def test_hybrid_search_fragt_ein_groesseres_kandidatenfenster_ab(dense_calls):
    hybrid.hybrid_search(FakeCollection(), QUESTION, n_results=2)

    assert dense_calls and dense_calls[0] > 2, "dichte Suche mit mehr Kandidaten als n_results"
