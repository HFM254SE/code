"""Tests für src/summarize.py: Prompt und defensives Parsen, ohne Endpunkt.

Die Tests ersetzen den LLM-Aufruf durch feste Antworten. Sie prüfen nur die
öffentlichen Funktionen. Wie ihr das Parsen intern baut, bleibt euch überlassen.
"""

import re

import pytest

from src import summarize
from src.ticket_loader import load_tickets

TICKET = {
    "id": "T-9999",
    "betreff": "Drucker druckt nur leere Seiten",
    "text": "Seit dem Tonerwechsel kommen nur weiße Blätter heraus.",
}
USAGE = {"prompt_tokens": 350, "completion_tokens": 20}


@pytest.fixture
def antwort(monkeypatch):
    """Legt fest, was das "LLM" antwortet, und merkt sich die Prompts."""
    prompts = []

    def setze(text: str):
        def fake_chat_with_usage(prompt, **_kwargs):
            prompts.append(prompt)
            return text, USAGE

        monkeypatch.setattr(summarize, "chat_with_usage", fake_chat_with_usage)
        return prompts

    return setze


def test_sauberes_json_wird_uebernommen(antwort):
    antwort('{"kategorie": "Hardware", "prioritaet": "mittel"}')
    result = summarize.classify_ticket_llm(TICKET)
    assert result["kategorie"] == "Hardware"
    assert result["prioritaet"] == "mittel"
    assert result["parse_fehler"] is False


def test_geschwaetzige_antwort_wird_geparst(antwort):
    antwort('Gern! Ergebnis: {"kategorie": "Software", "prioritaet": "hoch"} Viel Erfolg.')
    result = summarize.classify_ticket_llm(TICKET)
    assert (result["kategorie"], result["prioritaet"]) == ("Software", "hoch")
    assert result["parse_fehler"] is False


def test_gross_und_kleinschreibung_wird_normalisiert(antwort):
    antwort('{"kategorie": "netzwerk", "prioritaet": "MITTEL"}')
    result = summarize.classify_ticket_llm(TICKET)
    assert (result["kategorie"], result["prioritaet"]) == ("Netzwerk", "mittel")


@pytest.mark.parametrize(
    "text",
    [
        "Das ist ein Hardware-Problem.",                        # gar kein JSON
        '{"kategorie": "Hardware", "prioritaet": }',            # kaputtes JSON
        '{"kategorie": "Drucker", "prioritaet": "mittel"}',     # unbekannte Kategorie
        '{"kategorie": "Hardware", "prioritaet": "dringend"}',  # unbekannte Priorität
        "",                                                     # leere Antwort
    ],
)
def test_unbrauchbare_antwort_wird_als_parse_fehler_markiert(antwort, text):
    antwort(text)
    result = summarize.classify_ticket_llm(TICKET)
    assert result["parse_fehler"] is True
    # Der Rückfall nutzt die Defaults der Regeln, damit das Ergebnis gültig bleibt.
    assert result["kategorie"] in summarize.CATEGORIES
    assert result["prioritaet"] in summarize.PRIORITIES


def test_prompt_enthaelt_ticket_und_erlaubte_kategorien(antwort):
    prompts = antwort('{"kategorie": "Hardware", "prioritaet": "mittel"}')
    summarize.classify_ticket_llm(TICKET)
    assert TICKET["betreff"] in prompts[0]
    assert TICKET["text"] in prompts[0]
    for category in summarize.CATEGORIES:
        assert category in prompts[0]


def test_token_zahlen_werden_durchgereicht(antwort):
    antwort('{"kategorie": "Hardware", "prioritaet": "mittel"}')
    result = summarize.classify_ticket_llm(TICKET)
    assert result["prompt_tokens"] == 350
    assert result["completion_tokens"] == 20


def test_few_shot_beispiele_stammen_nicht_aus_den_tickets():
    # Ein Ticket aus dem Golden Dataset im Prompt wäre eine Testfrage mit Lösung.
    # Geprüft werden der Betreff und jeder längere Satz aus dem Text. Ein
    # umformuliertes Ticket findet kein Test. Denkt euch die Beispiele wirklich aus.
    for ticket in load_tickets():
        assert ticket["betreff"] not in summarize.CLASSIFY_PROMPT, ticket["id"]
        for satz in re.split(r"(?<=[.!?])\s+", ticket["text"]):
            satz = satz.rstrip(".!?")
            if len(satz) >= 25:
                assert satz not in summarize.CLASSIFY_PROMPT, ticket["id"]


def test_zusammenfassung_nutzt_chat_und_entfernt_leerraum(monkeypatch):
    monkeypatch.setattr(summarize, "chat", lambda prompt, **_kwargs: "  Toner leer.  ")
    assert summarize.summarize_ticket(TICKET) == "Toner leer."
