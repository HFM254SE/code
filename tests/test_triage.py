"""Tests fuer die regelbasierte Ticket-Triage.

Diese Tests definieren das erwartete Verhalten. Sie muessen VOR und NACH
jedem Refactoring gruen sein — egal ob Mensch oder KI den Code anfasst.
"""

from src.triage import classify_and_prioritize, triage_all


def make_ticket(betreff, text):
    return {"id": "T-9999", "von": "test@leinetech.de", "betreff": betreff,
            "text": text, "erstellt": "2026-05-01"}


def test_hardware_ticket():
    t = make_ticket("Laptop startet nicht", "Mein Laptop bleibt beim Boot haengen.")
    kategorie, prioritaet = classify_and_prioritize(t)
    assert kategorie == "Hardware"
    assert prioritaet == "mittel"


def test_netzwerk_ticket_hohe_prioritaet():
    t = make_ticket("VPN down", "Das VPN faellt dauernd aus, Ausfall betrifft das ganze Team. Dringend!")
    kategorie, prioritaet = classify_and_prioritize(t)
    assert kategorie == "Netzwerk"
    assert prioritaet == "hoch"


def test_zugang_vor_netzwerk():
    # Reihenfolge der Regeln: Zugang wird vor Netzwerk geprueft.
    t = make_ticket("Kein Zugriff", "Ich habe keinen Zugriff auf das WLAN-Portal.")
    kategorie, _ = classify_and_prioritize(t)
    assert kategorie == "Zugang"


def test_default_kategorie_software():
    t = make_ticket("Alles seltsam", "Irgendwas stimmt hier nicht.")
    kategorie, prioritaet = classify_and_prioritize(t)
    assert kategorie == "Software"
    assert prioritaet == "mittel"


def test_triage_all_liefert_alle_tickets():
    tickets = [
        make_ticket("Drucker kaputt", "Der Drucker im 2. OG druckt nicht."),
        make_ticket("Frage zur Rechnung", "Ich habe eine Frage zu den Kosten."),
    ]
    results = triage_all(tickets)
    assert len(results) == 2
    assert results[0]["kategorie"] == "Hardware"
    assert results[1]["kategorie"] == "Abrechnung"
    assert results[1]["prioritaet"] == "niedrig"
