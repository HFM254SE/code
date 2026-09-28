"""Tests für das Evalset und die Retrieval-Messung (src/rag_eval.py), offline.

Geprüft werden das Format von eval/rag_eval.jsonl, die Belegstellen gegen die
echten Dokumente in docs/, der Beleg- und Datei-Treffer und die Erkennung der
Enthaltung. Der Judge ist nicht Teil dieser Datei.

Im Start-Step braucht src/rag_eval.py die Datei src/rag.py (Lab Teil 1). Bis dahin
werden diese Tests übersprungen.
"""

import re
from pathlib import Path

import pytest

rag_eval = pytest.importorskip(
    "src.rag_eval",
    reason="src/rag_eval.py braucht src/rag.py (Lab Teil 1)",
    exc_type=ModuleNotFoundError,
)

from src.loader import load_documents  # noqa: E402  (erst nach dem importorskip)

REPO_ROOT = Path(__file__).resolve().parent.parent
EVALSET = rag_eval.load_evalset(REPO_ROOT / "eval" / "rag_eval.jsonl")
DOCUMENTS = {doc["metadata"]["source"]: doc["text"] for doc in load_documents(REPO_ROOT / "docs")}
ANSWERABLE = [entry for entry in EVALSET if not rag_eval.is_unanswerable(entry)]


# --- Evalset ----------------------------------------------------------------


def test_evalset_hat_pflichtfelder_und_gueltige_typen():
    for entry in EVALSET:
        assert {"question", "ground_truth", "evidence", "expected_source", "type"} <= set(entry)
        assert entry["type"] in rag_eval.QUESTION_TYPES, entry["question"]


def test_evalset_deckt_alle_vier_fragetypen_ab():
    types = [entry["type"] for entry in EVALSET]

    for question_type in rag_eval.QUESTION_TYPES:
        assert types.count(question_type) >= 2, f"zu wenige Fragen vom Typ {question_type}"


def test_unbeantwortbare_fragen_haben_weder_quelle_noch_beleg():
    for entry in EVALSET:
        if entry["type"] == rag_eval.UNANSWERABLE:
            assert entry["expected_source"] is None and entry["evidence"] == []
        else:
            assert entry["expected_source"] and entry["evidence"], entry["question"]


def test_jede_belegstelle_steht_in_der_erwarteten_datei():
    for entry in ANSWERABLE:
        document = DOCUMENTS[entry["expected_source"]]
        for literal in entry["evidence"]:
            assert rag_eval.contains_evidence(document, literal), (
                f"Beleg {literal!r} fehlt in {entry['expected_source']}"
            )


def test_evalset_nutzt_echte_umlaute():
    # "Prioritaet" statt "Priorität" findet die Keyword-Suche im Dokument nicht.
    corpus_words = set(re.findall(r"\w+", " ".join(DOCUMENTS.values()).lower()))
    umlauts = {"ae": "ä", "oe": "ö", "ue": "ü"}
    for entry in EVALSET:
        for word in re.findall(r"\w+", f"{entry['question']} {entry['ground_truth']}".lower()):
            restored = re.sub("ae|oe|ue", lambda match: umlauts[match.group()], word)
            if restored != word:
                assert restored not in corpus_words, f"{word!r} statt {restored!r}"


# --- Beleg- und Datei-Treffer --------------------------------------------------


@pytest.mark.parametrize(
    ("text", "evidence", "expected"),
    [
        ("Hotline intern **-4242** (extern ...)", "-4242", True),
        ("Nach 12 Stunden oder 30 Minuten", "2 Stunden", False),
        ("| **hoch** | ... | **2 Stunden** |", "2 Stunden", True),
        ("Mindestens **14 Zeichen**,\nkeine Wiederverwendung", "14 zeichen", True),
        ("des anfordernden Teams", "Anfordern", False),
        ("interne IP-Bereiche `10.20.0.0/16`) läuft", "10.20.0.0/16", True),
    ],
)
def test_contains_evidence_vergleicht_ganze_woerter(text, evidence, expected):
    assert rag_eval.contains_evidence(text, evidence) is expected


def test_count_evidence_zaehlt_belege_ueber_alle_treffer():
    hits = [{"text": "Firmengerät und MFA"}, {"text": "Secure Client ab Version 5.1"}]
    evidence = ["Firmengerät", "Secure Client ab Version 5.1", "16 Mbit/s"]

    assert rag_eval.count_evidence(evidence, hits) == 2


def test_source_hit_prueft_nur_den_dateinamen():
    hits = [{"source": "it-support-prozesse.md", "text": "Hotline intern -4242"}]

    assert rag_eval.source_hit("it-support-prozesse.md", hits)
    assert rag_eval.count_evidence(["-4200"], hits) == 0, "Datei stimmt, Beleg fehlt"


def test_evaluate_entry_retrieval_only_ruft_kein_llm_auf(monkeypatch):
    monkeypatch.setattr(rag_eval, "chat", lambda *args, **kwargs: pytest.fail("Chat-Aufruf"))
    entry = {
        "question": "Welche Durchwahl hat Bernd Hagedorn?",
        "evidence": ["-4200"],
        "expected_source": "it-support-prozesse.md",
        "type": "keyword",
    }

    def retriever(collection, query, n_results=5):
        return [{"rank": 1, "source": "it-support-prozesse.md", "text": "Hotline -4242"}]

    row = rag_eval.evaluate_entry(entry, object(), retriever, n_results=3, retrieval_only=True)

    assert row["source_hit"] is True
    assert (row["evidence_found"], row["evidence_total"]) == (0, 1)
    assert not rag_eval.evidence_complete(row)


def test_beleg_aus_einer_anderen_datei_zaehlt_nicht():
    # "2 Stunden" steht auch bei den Leihgeräten in hardware-bestellung.md. Das ist ein
    # Ablenker, nicht die SLA-Tabelle aus it-support-prozesse.md.
    entry = {
        "question": "Wie hoch ist die SLA-Reaktionszeit für Priorität hoch?",
        "evidence": ["2 Stunden"],
        "expected_source": "it-support-prozesse.md",
        "type": "einfach",
    }

    def retriever(collection, query, n_results=5):
        return [
            {"rank": 1, "source": "hardware-bestellung.md",
             "text": "Leihgeräte sind bei Priorität hoch innerhalb von 2 Stunden verfügbar."},
            {"rank": 2, "source": "it-support-prozesse.md", "text": "Hotline intern -4242"},
        ]

    row = rag_eval.evaluate_entry(entry, object(), retriever, n_results=3, retrieval_only=True)

    assert row["source_hit"] is True
    assert row["evidence_found"] == 0, "der Ablenker darf nicht als Beleg zählen"


# --- Enthaltung ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Ich habe dazu keine Information in der Wissensbasis.", True),
        ("  ich habe dazu keine information in der wissensbasis", True),
        ("Dazu liegen mir keine Informationen vor.", True),
        ("Das steht nicht im Kontext.", True),
        ("Die Durchwahl lautet -4200. [Quelle 1]", False),
    ],
)
def test_is_abstention(text, expected):
    assert rag_eval.is_abstention(text) is expected
