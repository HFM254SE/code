"""LLM-gestützte Ticket-Funktionen: Zusammenfassung und Klassifikation.

Hier passiert der Sprung von VL 1 zu VL 3: Statt Keyword-Regeln
(src/triage.py) beurteilt ein Sprachmodell den Ticket-Inhalt.
"""

import json

from src.llm import chat, chat_with_usage
from src.triage import CATEGORY_KEYWORDS, DEFAULT_CATEGORY, DEFAULT_PRIORITY

CATEGORIES = list(CATEGORY_KEYWORDS)  # Hardware, Software, ...: eine Quelle der Wahrheit
PRIORITIES = ["hoch", "mittel", "niedrig"]
_CANONICAL_CATEGORY = {category.lower(): category for category in CATEGORIES}

# Obergrenze für die Antwortlänge. Mit Thinking zählen die Denk-Tokens mit.
# Die Grenze fängt Endlosschleifen ab, ohne normale Antworten abzuschneiden.
CLASSIFY_MAX_TOKENS = 4096

# Die Few-Shot-Beispiele sind bewusst ausgedacht. Stammten sie aus
# data/tickets.json, stünden Testfragen im Prompt (Contamination im Kleinen).
CLASSIFY_PROMPT = """Klassifiziere das folgende Support-Ticket.

Erlaubte Kategorien: {categories}
Erlaubte Prioritäten: hoch (Produktionsausfall / viele Nutzer betroffen / \
Arbeit unmöglich), mittel (Einzelperson eingeschränkt), niedrig (Frage / \
Wunsch / kein Zeitdruck).

Antworte NUR mit validem JSON, ohne Erklärung, exakt in dieser Form:
{{"kategorie": "...", "prioritaet": "..."}}

Beispiel 1:
Betreff: Beamer im Schulungsraum zeigt kein Bild
Text: Der Beamer bleibt schwarz, die Schulung mit zwölf Teilnehmenden beginnt in einer Stunde.
→ {{"kategorie": "Hardware", "prioritaet": "hoch"}}

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
    """Erzeugt eine Zusammenfassung eines Tickets in ein bis zwei Sätzen."""
    prompt = SUMMARIZE_PROMPT.format(
        betreff=ticket.get("betreff", ""), text=ticket.get("text", "")
    )
    return chat(prompt, model=model).strip()


def classify_ticket_llm(ticket: dict, model: str | None = None) -> dict:
    """Klassifiziert ein Ticket per LLM.

    Liefert kategorie, prioritaet und parse_fehler, dazu prompt_tokens und
    completion_tokens für die Kostenabschätzung.
    """
    prompt = CLASSIFY_PROMPT.format(
        categories=", ".join(CATEGORIES),
        betreff=ticket.get("betreff", ""),
        text=ticket.get("text", ""),
    )
    answer, usage = chat_with_usage(prompt, model=model, max_tokens=CLASSIFY_MAX_TOKENS)
    return {**_parse_classification(answer), **usage}


def _parse_classification(answer: str) -> dict:
    """Macht aus der Modellantwort ein Dict mit kategorie, prioritaet und parse_fehler.

    Modelle schreiben gern Text um das JSON herum. Deshalb schneiden wir vom
    ersten "{" bis zum letzten "}" aus. Groß- und Kleinschreibung spielt keine
    Rolle. Ist die Antwort unbrauchbar, kommt der markierte Rückfall.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return _fallback()
    try:
        data = json.loads(answer[start:end + 1])
    except json.JSONDecodeError:
        return _fallback()

    kategorie = _CANONICAL_CATEGORY.get(str(data.get("kategorie", "")).strip().lower())
    prioritaet = str(data.get("prioritaet", "")).strip().lower()
    if kategorie is None or prioritaet not in PRIORITIES:
        return _fallback()
    return {"kategorie": kategorie, "prioritaet": prioritaet, "parse_fehler": False}


def _fallback() -> dict:
    """Rückfall bei unbrauchbarer Antwort: die Defaults der Regeln, als Parse-Fehler markiert.

    Software und mittel sind zugleich die häufigsten Gold-Labels. In der
    Evaluierung zählt der Rückfall weiter mit, so wie sich das System im Betrieb
    verhielte. Die Markierung zeigt, wie viele dieser Treffer nur Zufall sind.
    """
    return {"kategorie": DEFAULT_CATEGORY, "prioritaet": DEFAULT_PRIORITY, "parse_fehler": True}
