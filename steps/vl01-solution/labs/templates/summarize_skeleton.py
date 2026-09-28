"""SKELETON für Lab VL 3, Teil 1: nach src/summarize.py kopieren und TODOs füllen.

    cp labs/templates/summarize_skeleton.py src/summarize.py

Fertig ist das Modul, wenn `python -m pytest tests/test_summarize.py` grün ist.
Eure Arbeit: der Few-Shot-Prompt (TODO 1.2) und das defensive Parsen der
Modellantwort (TODO 1.3). Der Aufruf des LLM ist schon fertig.
"""

import json  # noqa: F401  (braucht ihr in TODO 1.3)

from src.llm import chat, chat_with_usage
from src.triage import CATEGORY_KEYWORDS, DEFAULT_CATEGORY, DEFAULT_PRIORITY

CATEGORIES = list(CATEGORY_KEYWORDS)  # Hardware, Software, ...: eine Quelle der Wahrheit
PRIORITIES = ["hoch", "mittel", "niedrig"]
_CANONICAL_CATEGORY = {category.lower(): category for category in CATEGORIES}

# Obergrenze für die Antwortlänge. Mit Thinking zählen die Denk-Tokens mit.
# Die Grenze fängt Endlosschleifen ab, ohne normale Antworten abzuschneiden.
CLASSIFY_MAX_TOKENS = 4096

# TODO 1.2: Few-Shot-Prompt fertigstellen (Prompting aus VL 2).
#   - Ergänzt vor "Jetzt das echte Ticket" mindestens zwei Beispiele im Format
#       Beispiel 1:
#       Betreff: …
#       Text: …
#       → {{"kategorie": "…", "prioritaet": "…"}}
#   - Denkt euch die Beispiele selbst aus. Nehmt KEIN Ticket aus
#     data/tickets.json: Das wäre eine Testfrage samt Lösung im Prompt
#     (Contamination), und die Messung in Teil 2 wäre geschönt.
#   - Geschweifte Klammern im Beispiel-JSON doppelt schreiben ({{ }}), weil der
#     Text später mit .format() gefüllt wird.
# Ohne Beispiele läuft der Prompt schon (Zero-Shot). Die Beispiele sollen ihn verbessern.
CLASSIFY_PROMPT = """Klassifiziere das folgende Support-Ticket.

Erlaubte Kategorien: {categories}
Erlaubte Prioritäten: hoch (Produktionsausfall / viele Nutzer betroffen / \
Arbeit unmöglich), mittel (Einzelperson eingeschränkt), niedrig (Frage / \
Wunsch / kein Zeitdruck).

Antworte NUR mit validem JSON, ohne Erklärung, exakt in dieser Form:
{{"kategorie": "...", "prioritaet": "..."}}

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
    # TODO 1.3: Antwort defensiv parsen.
    #   - Das JSON steckt oft in Begleittext. Schneidet vom ersten "{" bis zum
    #     letzten "}" aus (str.find, str.rfind).
    #   - json.loads() kann scheitern: json.JSONDecodeError abfangen.
    #   - Kategorie ohne Rücksicht auf Groß- und Kleinschreibung erkennen und in
    #     der Schreibweise aus CATEGORIES zurückgeben (_CANONICAL_CATEGORY hilft).
    #   - Priorität klein schreiben und gegen PRIORITIES prüfen.
    #   - Gültig: return {"kategorie": ..., "prioritaet": ..., "parse_fehler": False}
    #   - In jedem anderen Fall: return _fallback()
    raise NotImplementedError("TODO 1.3 in src/summarize.py: _parse_classification() fertigstellen")


def _fallback() -> dict:
    """Rückfall bei unbrauchbarer Antwort: die Defaults der Regeln, als Parse-Fehler markiert.

    Software und mittel sind zugleich die häufigsten Gold-Labels. In der
    Evaluierung zählt der Rückfall weiter mit, so wie sich das System im Betrieb
    verhielte. Die Markierung zeigt, wie viele dieser Treffer nur Zufall sind.
    """
    return {"kategorie": DEFAULT_CATEGORY, "prioritaet": DEFAULT_PRIORITY, "parse_fehler": True}
