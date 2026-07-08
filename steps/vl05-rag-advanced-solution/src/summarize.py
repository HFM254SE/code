"""LLM-gestützte Ticket-Funktionen: Zusammenfassung und Klassifikation.

Hier passiert der eigentliche Sprung von VL 1 zu VL 3: Statt Keyword-Regeln
(src/triage.py) beurteilt jetzt ein Sprachmodell den Ticket-Inhalt.
"""

import json

from src.llm import chat
from src.triage import CATEGORY_KEYWORDS, DEFAULT_CATEGORY, DEFAULT_PRIORITY

CATEGORIES = list(CATEGORY_KEYWORDS)  # Hardware, Software, ... — eine Quelle der Wahrheit
PRIORITIES = ["hoch", "mittel", "niedrig"]

CLASSIFY_PROMPT = """Klassifiziere das folgende Support-Ticket.

Erlaubte Kategorien: {categories}
Erlaubte Prioritäten: hoch (Produktionsausfall / viele Nutzer betroffen / \
Arbeit unmöglich), mittel (Einzelperson eingeschränkt), niedrig (Frage / \
Wunsch / kein Zeitdruck).

Antworte NUR mit validem JSON, ohne Erklärung, exakt in dieser Form:
{{"kategorie": "...", "prioritaet": "..."}}

Beispiel 1:
Betreff: Docking-Station erkennt Monitor nicht
Text: Seit heute Morgen bleibt der externe Bildschirm schwarz.
→ {{"kategorie": "Hardware", "prioritaet": "mittel"}}

Beispiel 2:
Betreff: Frage zur Kalenderfreigabe
Text: Wie gebe ich meinen Kalender für das Team frei? Eilt nicht.
→ {{"kategorie": "Software", "prioritaet": "niedrig"}}

Jetzt das echte Ticket:
Betreff: {betreff}
Text: {text}
→"""

SUMMARIZE_PROMPT = """Fasse das folgende Support-Ticket in maximal zwei Sätzen \
zusammen: Was ist das Problem, und was braucht die Person?

Betreff: {betreff}
Text: {text}"""


def summarize_ticket(ticket: dict, model: str | None = None) -> str:
    """Erzeugt eine 1-2-Satz-Zusammenfassung eines Tickets."""
    prompt = SUMMARIZE_PROMPT.format(
        betreff=ticket.get("betreff", ""), text=ticket.get("text", "")
    )
    return chat(prompt, model=model).strip()


def classify_ticket_llm(ticket: dict, model: str | None = None) -> dict:
    """Klassifiziert ein Ticket per LLM. Liefert {"kategorie", "prioritaet"}.

    Kleine Modelle halten sich nicht immer perfekt an Formatvorgaben —
    deshalb wird defensiv geparst und bei Unsinn auf Defaults zurückgefallen.
    """
    prompt = CLASSIFY_PROMPT.format(
        categories=", ".join(CATEGORIES),
        betreff=ticket.get("betreff", ""),
        text=ticket.get("text", ""),
    )
    answer = chat(prompt, model=model)
    return _parse_classification(answer)


def _parse_classification(answer: str) -> dict:
    """Extrahiert das JSON-Objekt aus einer (möglicherweise geschwätzigen) Antwort."""
    start, end = answer.find("{"), answer.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(answer[start : end + 1])
            kategorie = data.get("kategorie", DEFAULT_CATEGORY)
            prioritaet = str(data.get("prioritaet", DEFAULT_PRIORITY)).lower()
            if kategorie in CATEGORIES and prioritaet in PRIORITIES:
                return {"kategorie": kategorie, "prioritaet": prioritaet}
        except json.JSONDecodeError:
            pass
    return {"kategorie": DEFAULT_CATEGORY, "prioritaet": DEFAULT_PRIORITY}
