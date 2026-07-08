"""Regelbasierte Triage: ordnet Tickets per Keyword-Suche einer Kategorie
und Priorität zu.

Die Reihenfolge der Kategorien ist Teil des Verhaltens (first match wins) —
sie darf beim Refactoring nicht verändert werden.
"""

from src.ticket_loader import load_tickets

# Reihenfolge ist relevant: die erste Kategorie mit Keyword-Treffer gewinnt.
CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Abrechnung": ["rechnung", "kosten", "vertrag", "tarif", "zahlung", "buchhaltung"],
    "Zugang": ["passwort", "login", "anmelden", "konto", "gesperrt", "zugriff", "berechtigung"],
    "Netzwerk": ["wlan", "vpn", "internet", "netzwerk", "verbindung", "lan"],
    "Hardware": ["laptop", "drucker", "monitor", "tastatur", "maus", "docking", "akku", "headset"],
    "Software": ["absturz", "fehlermeldung", "update", "installation", "lizenz", "programm", "anwendung"],
}
DEFAULT_CATEGORY = "Software"

PRIORITY_KEYWORDS: dict[str, list[str]] = {
    "hoch": ["dringend", "sofort", "produktion", "ausfall", "nichts geht", "komplett"],
    "niedrig": ["frage", "gelegentlich", "kein stress", "wunsch", "irgendwann"],
}
DEFAULT_PRIORITY = "mittel"


def _ticket_text(ticket: dict) -> str:
    return f"{ticket.get('betreff', '')} {ticket.get('text', '')}".lower()


def _first_match(text: str, rules: dict[str, list[str]], default: str) -> str:
    for label, keywords in rules.items():
        if any(keyword in text for keyword in keywords):
            return label
    return default


def classify_and_prioritize(ticket: dict) -> tuple[str, str]:
    """Liefert (Kategorie, Priorität) für ein einzelnes Ticket."""
    text = _ticket_text(ticket)
    kategorie = _first_match(text, CATEGORY_KEYWORDS, DEFAULT_CATEGORY)
    prioritaet = _first_match(text, PRIORITY_KEYWORDS, DEFAULT_PRIORITY)
    return kategorie, prioritaet


def triage_all(tickets: list[dict] | None = None) -> list[dict]:
    """Klassifiziert alle übergebenen Tickets (oder die gesamte Datenbasis)."""
    if tickets is None:
        tickets = list(load_tickets())
    results = []
    for ticket in tickets:
        kategorie, prioritaet = classify_and_prioritize(ticket)
        results.append(
            {
                "id": ticket["id"],
                "betreff": ticket["betreff"],
                "kategorie": kategorie,
                "prioritaet": prioritaet,
            }
        )
    return results
