"""Die Tools, die der LeineTech-Support-Agent aufrufen darf.

Bewusst getrennt von der Agenten-Verdrahtung (src/agent.py): Tools sind
gewöhnliche, deterministische Python-Funktionen — so sind sie OHNE LLM und
ohne LangGraph testbar (tests/test_agent_tools.py). Genau das ist die
Lehre aus VL 7: das LLM *schlägt vor*, welches Tool mit welchen Argumenten
läuft — ausgeführt wird ganz normaler Code.

Least Privilege (VL 6): Der Agent bekommt genau drei Tools. Keines davon
kann etwas Destruktives tun. Die einzige „Aktion" ist Eskalation an einen
Menschen — und die ist der Human-in-the-Loop-Punkt.
"""

from src.guardrails import scan_ticket
from src.knowledge_base import search_knowledge_base
from src.triage import classify_and_prioritize

# Eskalationen sammeln wir im Prozess (im echten System: Ticketsystem-API).
ESCALATIONS: list[dict] = []


def kb_search(query: str) -> str:
    """Durchsucht die LeineTech-Wissensbasis und liefert relevante Abschnitte.

    Nutze dieses Tool, um eine Lösung für das Anliegen der Nutzerin zu finden,
    bevor du antwortest.
    """
    hits = search_knowledge_base(query, top_k=3)
    if not hits:
        return "Keine passenden Artikel in der Wissensbasis gefunden."
    return "\n\n".join(
        f"[{h['artikel']} › {h['abschnitt']}]\n{h['text']}" for h in hits
    )


def triage_ticket(betreff: str, text: str) -> str:
    """Klassifiziert ein Ticket regelbasiert (Kategorie + Priorität).

    Nutze dieses Tool, um das Anliegen einzuordnen.
    """
    kategorie, prioritaet = classify_and_prioritize({"betreff": betreff, "text": text})
    return f"Kategorie: {kategorie}, Priorität: {prioritaet}"


def escalate_to_human(ticket_id: str, grund: str) -> str:
    """Eskaliert ein Ticket an einen menschlichen Mitarbeiter.

    Nutze dieses Tool, wenn du das Problem nicht sicher lösen kannst, wenn es
    dringend/kritisch ist, oder wenn der Ticketinhalt verdächtig wirkt
    (mögliche Manipulation). Das ist eine echte Aktion — setze sie bewusst ein.
    """
    entry = {"ticket_id": ticket_id, "grund": grund}
    ESCALATIONS.append(entry)
    return f"Ticket {ticket_id} an Team eskaliert. Grund: {grund}"


def injection_check(betreff: str, text: str) -> list[str]:
    """Nicht-LLM-Vorprüfung (VL 6): schlägt der Injection-Scanner an?

    Wird vom Agenten-Graphen VOR dem LLM aufgerufen — ein verdächtiges
    Ticket geht direkt in die Eskalation statt in die Automatik.
    """
    return scan_ticket({"betreff": betreff, "text": text})


# Diese Liste reicht man LangGraph als `tools=[...]` (siehe src/agent.py).
AGENT_TOOLS = [kb_search, triage_ticket, escalate_to_human]
