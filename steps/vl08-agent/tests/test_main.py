"""Tests für die Kommandozeile src/main.py, ohne Endpunkt."""

import pytest

from src import main as cli


def test_ohne_subkommando_laeuft_der_regel_report_wie_in_vl1(capsys):
    cli.main([])
    out = capsys.readouterr().out
    assert "LeineTech Ticket-Triage" in out
    assert "Anzahl Tickets: 30" in out


def test_classify_stellt_regeln_und_llm_gegenueber(capsys, monkeypatch):
    monkeypatch.setattr(
        cli, "classify_ticket_llm",
        lambda ticket: {"kategorie": "Software", "prioritaet": "hoch", "parse_fehler": False,
                        "prompt_tokens": 310, "completion_tokens": 18},
    )
    cli.main(["classify", "t-1003"])  # Kleinschreibung der ID ist erlaubt
    out = capsys.readouterr().out
    assert "Regeln (VL 1):  Abrechnung / hoch" in out
    assert "Software / hoch" in out
    assert "310 ein, 18 aus" in out


def test_unbekanntes_ticket_beendet_mit_meldung():
    with pytest.raises(SystemExit, match="T-0000 nicht gefunden"):
        cli.main(["classify", "T-0000"])
