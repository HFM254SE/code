"""Tests für den LLM-as-a-Judge in src/rag_eval.py, offline mit Fake-LLM.

Geprüft wird vor allem das Auslesen der Judge-Antworten. Judges plaudern gern,
stellen Denkblöcke voran oder packen JSON in Codeblöcke. Nicht verwertbare
Antworten müssen als "nicht bewertbar" (None) zählen, nicht als 0 oder 1.
"""

import pytest

from src import rag_eval


def fake_chat(reply):
    """Attrappe für chat(): liefert immer dieselbe Antwort."""
    return lambda prompt, system="", **kwargs: reply


# --- JSON aus der Judge-Antwort lesen --------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        '{"relevanz": 0.75}',
        'Hier ist meine Bewertung:\n```json\n{"relevanz": 0.75}\n```',
        '<think>Die Antwort nennt 3 von 4 Punkten, also 1 Abzug.</think>{"relevanz": 0.75}',
    ],
)
def test_parse_json_object_findet_das_objekt(raw):
    assert rag_eval.parse_json_object(raw) == {"relevanz": 0.75}


@pytest.mark.parametrize("raw", ["", "keine Zahl, kein JSON", "{kaputt", "[1, 2]"])
def test_parse_json_object_ohne_verwertbares_json(raw):
    assert rag_eval.parse_json_object(raw) is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ('{"relevanz": 0.8}', 0.8),
        ("0,8", 0.8),
        ("  1  ", 1.0),
        ('<think>2 von 3</think>{"relevanz": 0.5}', 0.5),
        ("3/4 Aussagen gestützt: 0.75", None),
        ('{"relevanz": 7}', None),
        ('{"begründung": "fehlt"}', None),
    ],
)
def test_parse_score_liest_nur_eindeutige_werte(raw, expected):
    assert rag_eval.parse_score(raw) == expected


# --- Faithfulness ---------------------------------------------------------------


def test_faithfulness_rechnet_die_quote_in_python(monkeypatch):
    reply = (
        '{"aussagen": ['
        '{"aussage": "Die Hotline ist -4242.", "gestützt": true},'
        '{"aussage": "Sie ist rund um die Uhr erreichbar.", "gestützt": false},'
        '{"aussage": "Sie gilt für dringende Fälle.", "gestützt": true}]}'
    )
    monkeypatch.setattr(rag_eval, "chat", fake_chat(reply))

    score = rag_eval.faithfulness("Hotline?", "Antwort", "Kontext")

    assert score == pytest.approx(2 / 3)


def test_judge_claims_liefert_die_einzelurteile(monkeypatch):
    reply = '```json\n{"aussagen": [{"aussage": "A", "gestützt": true}]}\n```'
    monkeypatch.setattr(rag_eval, "chat", fake_chat(reply))

    assert rag_eval.judge_claims("F", "A", "K") == [{"aussage": "A", "gestützt": True}]


@pytest.mark.parametrize(
    "reply",
    ["0.75", '{"aussagen": []}', '{"aussagen": [{"aussage": "A", "gestützt": "ja"}]}'],
)
def test_faithfulness_ohne_einzelurteile_ist_nicht_bewertbar(monkeypatch, reply):
    monkeypatch.setattr(rag_eval, "chat", fake_chat(reply))

    assert rag_eval.faithfulness("F", "A", "K") is None


def test_eine_unklare_aussage_macht_das_urteil_unbewertbar(monkeypatch):
    # Würde man "teilweise" einfach weglassen, käme 1/1 = 1,0 heraus.
    reply = (
        '{"aussagen": ['
        '{"aussage": "A", "gestützt": true},'
        '{"aussage": "B", "gestützt": "teilweise"},'
        '{"aussage": "C", "gestützt": "teilweise"}]}'
    )
    monkeypatch.setattr(rag_eval, "chat", fake_chat(reply))

    assert rag_eval.judge_claims("F", "A", "K") is None
    assert rag_eval.faithfulness("F", "A", "K") is None


def test_judge_ruft_mit_temperatur_null_und_json_system_prompt(monkeypatch):
    calls = []

    def recording_chat(prompt, system="", temperature=None, **kwargs):
        calls.append({"prompt": prompt, "system": system, "temperature": temperature})
        return '{"relevanz": 1}'

    monkeypatch.setattr(rag_eval, "chat", recording_chat)
    rag_eval.answer_relevancy("Wie lautet die Hotline?", "-4242 [Quelle 1]")

    assert calls[0]["temperature"] == 0.0
    assert "JSON" in calls[0]["system"]
    assert "Wie lautet die Hotline?" in calls[0]["prompt"]


# --- Ablauf mit Antworten ----------------------------------------------------------

ENTRIES = [
    {
        "question": "Welche Durchwahl hat Bernd Hagedorn?",
        "evidence": ["-4200"],
        "expected_source": "it-support-prozesse.md",
        "type": "keyword",
    },
    {
        "question": "Wie viele Urlaubstage habe ich pro Jahr?",
        "evidence": [],
        "expected_source": None,
        "type": "unbeantwortbar",
    },
]


def hotline_retriever(collection, query, n_results=5):
    return [{"rank": 1, "source": "it-support-prozesse.md", "score": 0.8, "text": "Hotline -4242"}]


def evaluate_with_answers(entry):
    return rag_eval.evaluate_entry(
        entry, object(), hotline_retriever, n_results=3, retrieval_only=False
    )


def test_evaluate_zaehlt_faelschliche_und_korrekte_enthaltung(monkeypatch):
    # Der Kontext enthält die Durchwahl nicht, also enthält sich das System bei beiden Fragen.
    monkeypatch.setattr("src.rag.chat", fake_chat(rag_eval.ABSTENTION))
    monkeypatch.setattr(rag_eval, "chat", lambda *a, **k: pytest.fail("Judge bei Enthaltung"))

    rows = [evaluate_with_answers(entry) for entry in ENTRIES]

    keyword_row, unanswerable_row = rows
    assert keyword_row["abstained"] is True, "fälschliche Enthaltung: ehrlich, aber nutzlos"
    assert keyword_row["faithfulness"] is None
    assert unanswerable_row["abstained"] is True
    assert (keyword_row["evidence_found"], keyword_row["source_hit"]) == (0, True)


def test_evaluate_bewertet_echte_antworten_mit_dem_judge(monkeypatch):
    monkeypatch.setattr("src.rag.chat", fake_chat("Die Hotline ist -4242. [Quelle 1]"))
    replies = iter([
        '{"aussagen": [{"aussage": "Die Hotline ist -4242.", "gestützt": true}]}',
        '{"relevanz": 0.4}',
    ])
    monkeypatch.setattr(rag_eval, "chat", lambda *a, **k: next(replies))

    row = evaluate_with_answers(ENTRIES[0])

    assert row["abstained"] is False
    assert row["faithfulness"] == 1.0, "treu zum Kontext, obwohl die Frage verfehlt ist"
    assert row["answer_relevancy"] == 0.4


def test_report_mittelt_nur_bewertete_antworten(capsys):
    rows = [
        {"question": "A", "type": "einfach", "unanswerable": False, "source_hit": True,
         "evidence_found": 1, "evidence_total": 1, "abstained": False, "claims": None,
         "faithfulness": 1.0, "answer_relevancy": None},
        {"question": "B", "type": "einfach", "unanswerable": False, "source_hit": True,
         "evidence_found": 0, "evidence_total": 1, "abstained": False, "claims": None,
         "faithfulness": 0.5, "answer_relevancy": 0.9},
        {"question": "C", "type": "einfach", "unanswerable": False, "source_hit": False,
         "evidence_found": 0, "evidence_total": 1, "abstained": True, "claims": None,
         "faithfulness": None, "answer_relevancy": None},
    ]

    rag_eval.print_report(rows, "dense", 3, retrieval_only=False)
    report = capsys.readouterr().out

    assert "Beleg-Treffer:            1/3" in report
    assert "Fälschliche Enthaltung:   1/3" in report
    assert "Faithfulness (Ø):         0.75  (bewertet: 2 von 2 Antworten)" in report
    assert "Answer Relevancy (Ø):     0.90  (bewertet: 1 von 2 Antworten)" in report
