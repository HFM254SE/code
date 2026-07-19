"""Tests fuer die Reciprocal Rank Fusion — offline, ohne Modell oder Netz.

RRF ist reine Rang-Arithmetik und laesst sich ohne Embeddings oder Vektor-DB
pruefen. Die netzabhaengigen Teile (hybrid_search, llm_rerank) werden im Lab
manuell getestet (siehe labs/vl05-lab.md).
"""

from src.hybrid import reciprocal_rank_fusion


def _hit(text, source="a.md"):
    return {"text": text, "source": source}


def test_rrf_belohnt_treffer_in_beiden_listen():
    # B steht in beiden Listen (Rang 2 bzw. 1), A und C je nur in einer.
    dense = [_hit("A"), _hit("B"), _hit("C")]
    sparse = [_hit("B"), _hit("D")]

    fused = reciprocal_rank_fusion([dense, sparse])

    assert fused[0]["text"] == "B", "in beiden Listen → hoechster RRF-Score"
    assert {h["text"] for h in fused} == {"A", "B", "C", "D"}


def test_rrf_vergibt_fortlaufende_raenge():
    fused = reciprocal_rank_fusion([[_hit("A"), _hit("B")], [_hit("B")]])

    assert [h["rank"] for h in fused] == list(range(1, len(fused) + 1))


def test_rrf_score_formel():
    # Einzelne Liste, k=60: Rang 1 → 1/61, Rang 2 → 1/62.
    fused = reciprocal_rank_fusion([[_hit("A"), _hit("B")]], k=60)

    assert abs(fused[0]["score"] - 1 / 61) < 1e-9
    assert abs(fused[1]["score"] - 1 / 62) < 1e-9


def test_rrf_behaelt_quelle():
    fused = reciprocal_rank_fusion([[_hit("A", source="vpn-zugang.md")]])

    assert fused[0]["source"] == "vpn-zugang.md"


def test_rrf_leere_eingabe():
    assert reciprocal_rank_fusion([]) == []
    assert reciprocal_rank_fusion([[], []]) == []
