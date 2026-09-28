"""Tests für den RAG-Client (src/rag.py), offline mit Fake-Retriever und Fake-LLM.

Lab Teil 1: Solange src/rag.py fehlt, werden diese Tests übersprungen. Nach dem
Kopieren der Vorlage (labs/templates/rag_skeleton.py) schlagen sie fehl, bis die
TODOs erledigt sind. Grün heißt: Der Client funktioniert, noch ohne Endpunkt.
"""

import pytest

rag = pytest.importorskip(
    "src.rag",
    reason="src/rag.py fehlt noch (Lab Teil 1)",
    exc_type=ModuleNotFoundError,
)

HITS = [
    {
        "rank": 1,
        "source": "vpn-zugang.md",
        "score": 0.91,
        "text": "Nach 12 Stunden oder 30 Minuten\nInaktivität trennt das Gateway automatisch.",
    },
    {"rank": 2, "source": "it-support-prozesse.md", "score": 0.74, "text": "Hotline intern -4242"},
]

EXPECTED_CONTEXT = (
    "[Quelle 1 | vpn-zugang.md]: Nach 12 Stunden oder 30 Minuten "
    "Inaktivität trennt das Gateway automatisch.\n\n"
    "[Quelle 2 | it-support-prozesse.md]: Hotline intern -4242"
)


def fake_retriever(collection, query, n_results=5):
    return HITS[:n_results]


def empty_retriever(collection, query, n_results=5):
    return []


@pytest.fixture
def chat_calls(monkeypatch):
    """Ersetzt chat() durch eine Attrappe und merkt sich jeden Aufruf."""
    calls = []

    def fake_chat(prompt, system="", **kwargs):
        calls.append({"prompt": prompt, "system": system})
        return "\n  Nach 30 Minuten Inaktivität. [Quelle 1]  \n"

    monkeypatch.setattr(rag, "chat", fake_chat)
    return calls


def test_system_prompt_enthaelt_enthaltung_und_zitierpflicht():
    assert rag.ABSTENTION in rag.RAG_SYSTEM_PROMPT, "fester Enthaltungs-Wortlaut fehlt"
    assert "[Quelle" in rag.RAG_SYSTEM_PROMPT, "Zitierpflicht [Quelle N] fehlt"


def test_build_context_nummeriert_mit_quelle_und_rang_reihenfolge():
    assert rag.build_context(HITS) == EXPECTED_CONTEXT


def test_build_prompt_setzt_kontext_vor_die_frage():
    prompt = rag.build_prompt("Wie lange hält das VPN?", "KONTEXTBLOCK")

    assert "KONTEXTBLOCK" in prompt
    assert prompt.index("KONTEXTBLOCK") < prompt.index("Wie lange hält das VPN?")


def test_answer_liefert_antwort_quellen_treffer_und_kontext(chat_calls):
    result = rag.answer("Wie lange hält das VPN?", collection=object(), retriever=fake_retriever)

    assert set(result) >= {"answer", "sources", "hits", "context"}
    assert result["answer"] == "Nach 30 Minuten Inaktivität. [Quelle 1]"
    assert result["sources"] == [
        {"label": "Quelle 1", "source": "vpn-zugang.md"},
        {"label": "Quelle 2", "source": "it-support-prozesse.md"},
    ]
    assert result["hits"] == HITS
    assert result["context"] == EXPECTED_CONTEXT


def test_answer_schickt_kontext_und_frage_mit_system_prompt(chat_calls):
    rag.answer("Wie lange hält das VPN?", collection=object(), retriever=fake_retriever)

    assert len(chat_calls) == 1
    assert EXPECTED_CONTEXT in chat_calls[0]["prompt"]
    assert "Wie lange hält das VPN?" in chat_calls[0]["prompt"]
    assert chat_calls[0]["system"] == rag.RAG_SYSTEM_PROMPT


def test_answer_nimmt_eigenen_system_prompt_fuer_experimente(chat_calls):
    rag.answer(
        "Frage?", collection=object(), retriever=fake_retriever, system_prompt="Ohne Regeln."
    )

    assert chat_calls[0]["system"] == "Ohne Regeln."


def test_answer_reicht_n_results_an_den_retriever_weiter(chat_calls):
    result = rag.answer("Frage?", n_results=1, collection=object(), retriever=fake_retriever)

    assert result["sources"] == [{"label": "Quelle 1", "source": "vpn-zugang.md"}]


def test_answer_ohne_treffer_enthaelt_sich_ohne_llm_aufruf(chat_calls):
    result = rag.answer("Wie viele Urlaubstage?", collection=object(), retriever=empty_retriever)

    assert result["answer"] == rag.ABSTENTION
    assert result["sources"] == []
    assert chat_calls == [], "ohne Kontext darf kein LLM-Aufruf stattfinden"
