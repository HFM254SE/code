"""Tests für src/evaluate.py: Messlogik und Report, ohne Endpunkt.

Die Regel-Baseline läuft echt gegen data/tickets.json und eval/golden.jsonl.
Das LLM wird durch eine Attrappe ersetzt.
"""

import csv

import pytest

from src import evaluate

TREFFER = {"kategorie": "Software", "prioritaet": "mittel", "parse_fehler": False,
           "prompt_tokens": 300, "completion_tokens": 20}


def test_accuracy_zaehlt_treffer():
    rows = [
        {"gold_kategorie": "Hardware", "llm_kategorie": "Hardware"},
        {"gold_kategorie": "Hardware", "llm_kategorie": "Software"},
        {"gold_kategorie": "Zugang", "llm_kategorie": ""},  # Endpunkt-Fehler zählt als falsch
        {"gold_kategorie": "Zugang", "llm_kategorie": "Zugang"},
    ]
    assert evaluate.accuracy(rows, "llm", "kategorie") == 0.5


def test_accuracy_leere_liste_ist_null():
    assert evaluate.accuracy([], "regel", "kategorie") == 0.0


def test_regel_baseline_auf_allen_tickets():
    rows = evaluate.evaluate(use_llm=False, limit=None)
    assert len(rows) == 30
    # Absichtlich nicht perfekt: 9 Keyword-Fallen, 3 Negations- und Ironie-Tickets.
    assert evaluate.accuracy(rows, "regel", "kategorie") == pytest.approx(0.7)
    assert evaluate.accuracy(rows, "regel", "prioritaet") == pytest.approx(0.9)


def test_regel_latenz_wird_in_millisekunden_gemessen():
    rows = evaluate.evaluate(use_llm=False, limit=10)
    assert all("regel_latenz_ms" in row for row in rows)
    assert any(row["regel_latenz_ms"] > 0 for row in rows)


def test_mehrheitsklasse_als_vergleichswert():
    rows = evaluate.evaluate(use_llm=False, limit=None)
    assert evaluate.majority_label(rows, "prioritaet") == "mittel"
    assert evaluate.majority_accuracy(rows, "prioritaet") == pytest.approx(0.6)


def test_llm_ergebnis_landet_in_den_spalten(monkeypatch):
    monkeypatch.setattr(evaluate, "classify_ticket_llm", lambda ticket: TREFFER)
    rows = evaluate.evaluate(use_llm=True, limit=3)
    assert len(rows) == 3
    for row in rows:
        assert row["llm_kategorie"] == "Software"
        assert row["llm_parse_fehler"] is False
        assert row["llm_fehler"] == ""
        assert row["llm_completion_tokens"] == 20
        assert row["llm_latenz_s"] >= 0


def test_endpunkt_fehler_bricht_die_messung_nicht_ab(monkeypatch):
    def classify(ticket):
        if ticket["id"] == "T-1002":
            raise TimeoutError("Endpunkt antwortet nicht")
        return TREFFER

    monkeypatch.setattr(evaluate, "classify_ticket_llm", classify)
    rows = evaluate.evaluate(use_llm=True, limit=4)
    assert len(rows) == 4
    assert rows[1]["llm_fehler"] == "TimeoutError"
    assert rows[1]["llm_kategorie"] == ""
    assert rows[1]["llm_parse_fehler"] == ""  # ohne Antwort nichts zu parsen
    assert rows[2]["llm_fehler"] == ""


def test_drei_fehler_in_folge_beenden_den_lauf(monkeypatch):
    def classify(_ticket):
        raise ConnectionError("Endpunkt nicht erreichbar")

    monkeypatch.setattr(evaluate, "classify_ticket_llm", classify)
    rows = evaluate.evaluate(use_llm=True, limit=10)
    assert len(rows) == evaluate.MAX_ERRORS_IN_A_ROW


def test_fehler_im_eigenen_code_bricht_sichtbar_ab(monkeypatch):
    def classify(_ticket):
        # So endet z. B. eine einzelne geschweifte Klammer im Few-Shot-Prompt.
        raise KeyError('"kategorie"')

    monkeypatch.setattr(evaluate, "classify_ticket_llm", classify)
    with pytest.raises(KeyError):
        evaluate.evaluate(use_llm=True, limit=3)


def test_endpunkt_fehler_werden_am_paket_erkannt():
    class RateLimitError(Exception):
        """Attrappe für litellm.RateLimitError, ohne litellm zu importieren."""

    RateLimitError.__module__ = "litellm.exceptions"
    assert evaluate.is_endpoint_error(RateLimitError("429"))
    assert evaluate.is_endpoint_error(TimeoutError("zu langsam"))
    assert not evaluate.is_endpoint_error(KeyError("kategorie"))
    assert not evaluate.is_endpoint_error(TypeError("falscher Typ im Parser"))


def test_parse_fehler_zaehlen_mit_und_zufallstreffer_werden_ausgewiesen(capsys):
    def row(ticket_id, gold, llm, parse_fehler):
        return {"id": ticket_id, "gold_kategorie": gold[0], "gold_prioritaet": gold[1],
                "llm_kategorie": llm[0], "llm_prioritaet": llm[1],
                "llm_parse_fehler": parse_fehler, "llm_fehler": ""}

    rows = [
        row("T-1", ("Software", "mittel"), ("Software", "mittel"), True),   # Zufall
        row("T-2", ("Hardware", "mittel"), ("Software", "mittel"), True),   # halber Zufall
        row("T-3", ("Hardware", "hoch"), ("Hardware", "hoch"), False),      # echter Treffer
    ]
    # Wie im Betrieb zählt der Rückfall mit: T-1 ist bei der Kategorie ein Treffer.
    assert evaluate.accuracy(rows, "llm", "kategorie") == pytest.approx(2 / 3)
    assert evaluate.parse_error_hits(rows, "kategorie") == 1
    assert evaluate.parse_error_hits(rows, "prioritaet") == 2

    evaluate._print_llm_details(rows)
    out = capsys.readouterr().out
    assert "2 Parse-Fehler" in out
    assert "Parse-Fehler zufällig richtig: Kategorie 1, Priorität 2" in out


def test_aeltere_classify_variante_ohne_zusatzfelder(monkeypatch, tmp_path, capsys):
    # Eine ältere Variante liefert kein parse_fehler und keine Tokens.
    monkeypatch.setattr(evaluate, "classify_ticket_llm",
                        lambda ticket: {"kategorie": "Software", "prioritaet": "mittel"})
    ziel = tmp_path / "r.csv"
    evaluate.main(["--llm", "--limit", "2", "--csv", str(ziel)])

    # „0 Parse-Fehler“ wäre geraten. Die Variante meldet Parse-Fehler gar nicht.
    report = capsys.readouterr().out
    assert "Parse-Fehler nicht erfasst" in report
    assert "zufällig richtig" not in report

    with open(ziel, encoding="utf-8") as file:
        row = next(csv.DictReader(file))
    assert row["llm_parse_fehler"] == ""
    assert row["llm_prompt_tokens"] == ""


def test_unterschiede_und_uebersehene_dringende_tickets():
    def row(ticket_id, gold, regel, llm):
        return {"id": ticket_id, "gold_prioritaet": gold,
                "regel_prioritaet": regel, "llm_prioritaet": llm}

    rows = [
        row("T-1", "hoch", "mittel", "hoch"),
        row("T-2", "hoch", "hoch", "niedrig"),
        row("T-3", "niedrig", "niedrig", "niedrig"),
    ]
    assert evaluate.missed_urgent(rows, "regel") == ["T-1"]
    assert evaluate.missed_urgent(rows, "llm") == ["T-2"]
    assert evaluate.only_correct(rows, "llm", "regel", "prioritaet") == ["T-1"]
    assert evaluate.only_correct(rows, "regel", "llm", "prioritaet") == ["T-2"]


def test_main_schreibt_csv_und_report(tmp_path, capsys):
    ziel = tmp_path / "ergebnis.csv"
    evaluate.main(["--all", "--csv", str(ziel)])

    report = capsys.readouterr().out
    assert "EVALUIERUNG auf 30 Tickets (1 Ticket = 3,3 Prozentpunkte)" in report
    assert "Mehrheitsklasse: Software / mittel" in report
    assert "Nur Testdaten (20 Tickets ab T-1011): Regeln 70 % / 90 %" in report
    assert "Dringend übersehen, Regeln: 2 von 8" in report

    with open(ziel, encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    assert len(rows) == 30
    assert "regel_latenz_ms" in rows[0]


def test_main_mit_llm_zeigt_fehler_und_tokens(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(evaluate, "classify_ticket_llm", lambda ticket: TREFFER)
    evaluate.main(["--llm", "--limit", "2", "--csv", str(tmp_path / "r.csv")])
    report = capsys.readouterr().out
    assert "0 Parse-Fehler, 0 Endpunkt-Fehler" in report
    assert "Parse-Fehler zufällig richtig: Kategorie 0, Priorität 0" in report
    assert "300 ein, 20 aus" in report


def test_main_ohne_tickets_meldet_sich(tmp_path):
    with pytest.raises(SystemExit):
        evaluate.main(["--limit", "0", "--csv", str(tmp_path / "r.csv")])
