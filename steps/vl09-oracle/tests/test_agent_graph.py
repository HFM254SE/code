"""Offline-Tests für die Graph-Verdrahtung in src/agent.py (Lab VL 8).

Ein Skript-Modell ersetzt das LLM. Es liefert vorher festgelegte Antworten und
ruft keinen Endpunkt auf. So prüft ihr die Verdrahtung ohne Kurs-Endpunkt,
auch außerhalb des Montagsfensters.

Im Stand vl06-guardrails fehlt src/agent.py noch. Dann wird diese Datei
übersprungen. Nach `cp labs/templates/agent_skeleton.py src/agent.py` sind die
Tests rot (NotImplementedError), bis TODO 1 bis 3 gefüllt sind. Der Test zum
Step-Limit wird übersprungen, bis TODO 4 (Schritt 4b) erledigt ist.
"""

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

pytest.importorskip("langgraph", reason="langgraph fehlt: pip install -r requirements.txt")
if not (ROOT / "src" / "agent.py").exists():
    pytest.skip(
        "Lab VL 8, Schritt 2: src/agent.py fehlt noch (cp labs/templates/agent_skeleton.py src/agent.py).",
        allow_module_level=True,
    )

from langchain_core.messages import AIMessage  # noqa: E402
from langgraph.checkpoint.memory import InMemorySaver  # noqa: E402
from langgraph.graph import END  # noqa: E402
from langgraph.types import Command, interrupt  # noqa: E402

from src import agent, agent_tools  # noqa: E402
from src.ticket_loader import get_ticket  # noqa: E402

TICKETS = ROOT / "data" / "tickets.json"


class SkriptModell:
    """Ersetzt das LLM: liefert die vorgegebenen Antworten der Reihe nach."""

    def __init__(self, antworten):
        self.antworten = list(antworten)
        self.aufrufe = 0

    def invoke(self, messages):
        self.aufrufe += 1
        return self.antworten.pop(0) if self.antworten else AIMessage("Fertig.")


class EndlosModell:
    """Ersetzt das LLM: fordert bei jedem Aufruf wieder ein Tool an."""

    def __init__(self):
        self.aufrufe = 0

    def invoke(self, messages):
        self.aufrufe += 1
        return AIMessage("", tool_calls=[tool_call("kb_search", {"query": "VPN"}, self.aufrufe)])


def tool_call(name: str, args: dict, nr: int = 1) -> dict:
    """Ein Tool-Call, wie ihn ein tool-fähiges Modell liefert."""
    return {"name": name, "args": args, "id": f"call_{nr}", "type": "tool_call"}


def ticket(ticket_id: str) -> dict:
    return get_ticket(ticket_id, TICKETS)


def t1006_ablauf() -> list:
    """Erwarteter Ablauf für T-1006: einordnen, KB durchsuchen, antworten."""
    t = ticket("T-1006")
    return [
        AIMessage("", tool_calls=[tool_call("triage_ticket", {"betreff": t["betreff"], "text": t["text"]}, 1)]),
        AIMessage("", tool_calls=[tool_call("kb_search", {"query": "VPN Tunnel Laufwerk DNS"}, 2)]),
        AIMessage("Bitte VPN neu verbinden und nslookup dms.leinetech.intern prüfen (KB: vpn-zugang)."),
    ]


@pytest.fixture(autouse=True)
def leere_eskalationen():
    agent_tools.ESCALATIONS.clear()
    yield
    agent_tools.ESCALATIONS.clear()


@pytest.fixture
def modell(monkeypatch):
    """Setzt ein Skript-Modell statt des LLM ein: modell([antwort1, antwort2, ...])."""

    def einsetzen(antworten):
        skript = SkriptModell(antworten)
        monkeypatch.setattr(agent, "_model", lambda: skript)
        return skript

    return einsetzen


# --- TODO 2: route -----------------------------------------------------------

def test_route_waehlt_tools_bei_tool_calls():
    state = {"messages": [AIMessage("", tool_calls=[tool_call("kb_search", {"query": "VPN"})])]}
    assert agent.route(state) == "tools"


def test_route_endet_ohne_tool_calls():
    assert agent.route({"messages": [AIMessage("Antwort")]}) == END


# --- TODO 3: build_agent -----------------------------------------------------

def test_graph_hat_einstieg_bedingte_kante_und_rueckkante():
    kanten = {(e.source, e.target) for e in agent.build_agent().get_graph().edges}
    assert ("__start__", "agent") in kanten  # Einstieg
    assert ("agent", "tools") in kanten  # bedingte Kante: Tool-Calls offen
    assert ("agent", "__end__") in kanten  # bedingte Kante: fertig
    assert ("tools", "agent") in kanten  # Rückkante: der ReAct-Loop


# --- TODO 1 bis 3 zusammen: ein ganzer Durchlauf ------------------------------

def test_react_loop_fuer_t1006(modell):
    modell(t1006_ablauf())
    result = agent.build_agent().invoke(agent.initial_state(ticket("T-1006")), {"recursion_limit": 12})
    typen = [m.type for m in result["messages"]]
    assert typen == ["human", "ai", "tool", "ai", "tool", "ai"]
    kb_ergebnis = result["messages"][4].content
    assert "[vpn-zugang › Tunnel steht" in kb_ergebnis
    assert "nslookup" in kb_ergebnis  # die Lösungsschritte erreichen das Modell


def test_handle_ticket_liefert_die_finale_antwort(modell):
    modell(t1006_ablauf())
    antwort = agent.handle_ticket(ticket("T-1006"))
    assert antwort.startswith("Bitte VPN neu verbinden")


def test_trace_zeigt_jeden_node_durchlauf(modell, capsys):
    modell(t1006_ablauf())
    agent.handle_ticket(ticket("T-1006"), trace=True)
    knoten = [zeile.split()[0] for zeile in capsys.readouterr().out.splitlines() if zeile.strip()]
    assert knoten == ["start", "agent", "tools", "agent", "tools", "agent"]


def test_output_filter_maskiert_die_antwort(modell):
    modell([AIMessage("Schreibt bitte an max.mustermann@example.org.")])
    antwort = agent.handle_ticket(ticket("T-1006"))
    assert "@" not in antwort and "[EMAIL ENTFERNT]" in antwort


# --- vorgegeben: _model mit Timeout und Backoff -----------------------------

def test_model_setzt_timeout_und_backoff(monkeypatch):
    """Schutzmechanismen 2 und 3: Zeitlimit pro Aufruf und eingebaute Wiederholungen."""
    erhalten = {}

    class FakeChatLiteLLM:
        def __init__(self, **kwargs):
            erhalten.update(kwargs)

        def bind_tools(self, tools):
            erhalten["tools"] = [tool.__name__ for tool in tools]
            return self

    monkeypatch.setitem(sys.modules, "langchain_litellm", types.SimpleNamespace(ChatLiteLLM=FakeChatLiteLLM))
    for variable in ("LLM_MODEL", "OPENAI_MODEL", "LLM_TIMEOUT"):
        monkeypatch.delenv(variable, raising=False)
    agent._model()
    assert erhalten["request_timeout"] == agent.get_timeout()  # Default aus src/llm.py
    assert erhalten["max_retries"] == agent.MAX_RETRIES == 3
    assert erhalten["model"].startswith("hosted_vllm/")  # litellm-Provider für den Kurs-Endpunkt
    assert {"kb_search", "triage_ticket", "escalate_to_human"} <= set(erhalten["tools"])


# --- vorgegeben: tool_node ---------------------------------------------------

def test_tool_fehler_wird_zur_observation(monkeypatch):
    def kaputt(query: str) -> str:
        raise TimeoutError("KB nicht erreichbar")

    monkeypatch.setitem(agent._TOOLS_BY_NAME, "kb_search", kaputt)
    state = {"messages": [AIMessage("", tool_calls=[tool_call("kb_search", {"query": "VPN"})])]}
    antwort = agent.tool_node(state)["messages"][0]
    assert antwort.content == "Tool-Fehler: KB nicht erreichbar"


def test_unbekanntes_tool_crasht_nicht():
    state = {"messages": [AIMessage("", tool_calls=[tool_call("delete_ticket", {"ticket_id": "T-1"})])]}
    antwort = agent.tool_node(state)["messages"][0]
    assert "Unbekanntes Tool 'delete_ticket'" in antwort.content


def test_interrupt_wird_nicht_als_tool_fehler_verschluckt(monkeypatch, modell):
    """Erweiterung B: interrupt() pausiert den Graphen und setzt nach der Freigabe fort."""
    ausgefuehrt = []

    def reset_account(user: str) -> str:
        if interrupt(f"Konto {user} zurücksetzen? (ja/nein)") != "ja":
            return f"Abgelehnt: Konto {user} bleibt unverändert."
        ausgefuehrt.append(user)  # Seiteneffekt erst nach der Freigabe
        return f"Konto {user} zurückgesetzt."

    monkeypatch.setitem(agent._TOOLS_BY_NAME, "reset_account", reset_account)
    modell([
        AIMessage("", tool_calls=[tool_call("reset_account", {"user": "m.muster"})]),
        AIMessage("Das Konto ist wieder freigeschaltet."),
    ])
    graph = agent.build_agent(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": "T-1009"}}

    erster_lauf = graph.invoke(agent.initial_state(ticket("T-1009")), config)
    assert "__interrupt__" in erster_lauf and ausgefuehrt == []

    zweiter_lauf = graph.invoke(Command(resume="ja"), config)
    assert ausgefuehrt == ["m.muster"]
    assert zweiter_lauf["messages"][-1].content == "Das Konto ist wieder freigeschaltet."


# --- vorgegeben: handle_ticket mit Vorabprüfung und Fallback -----------------

def test_t1030_erreicht_das_modell_nie(monkeypatch):
    def verboten():
        raise AssertionError("Bei Injection-Verdacht darf kein Modell aufgerufen werden")

    monkeypatch.setattr(agent, "_model", verboten)
    antwort = agent.handle_ticket(ticket("T-1030"))
    assert antwort.startswith("Ticket T-1030 an Team eskaliert. Grund: Injection-Verdacht")
    assert agent_tools.ESCALATIONS[0]["ticket_id"] == "T-1030"


def test_recursion_limit_fuehrt_zur_eskalation(modell):
    modell(t1006_ablauf())
    antwort = agent.handle_ticket(ticket("T-1006"), recursion_limit=2)
    assert "recursion_limit=2 erreicht" in antwort
    assert agent_tools.ESCALATIONS[0]["ticket_id"] == "T-1006"


def test_recursion_limit_greift_nur_bei_tool_calls(modell):
    """Antwortet das Modell sofort, endet der Lauf nach einem Superstep regulär."""
    modell([AIMessage("Direkte Antwort ohne Tools.")])
    assert agent.handle_ticket(ticket("T-1006"), recursion_limit=2) == "Direkte Antwort ohne Tools."


# --- TODO 4 (Schritt 4b): Step-Limit -----------------------------------------

def test_step_limit_beendet_den_loop_geordnet(monkeypatch):
    if "step_limit" not in agent.build_agent().get_graph().nodes:
        pytest.skip("Schritt 4b (TODO 4) ist noch offen.")
    endlos = EndlosModell()
    monkeypatch.setattr(agent, "_model", lambda: endlos)
    antwort = agent.handle_ticket(ticket("T-1006"), recursion_limit=50)
    assert "Step-Limit erreicht" in antwort  # eigener Ausstieg, kein GraphRecursionError
    assert endlos.aufrufe == agent.MAX_TOOL_RUNDEN + 1

    # Mit dem Default von handle_ticket (recursion_limit=12) muss das Step-Limit
    # ebenfalls vorher greifen: 2 × MAX_TOOL_RUNDEN + 2 < 12. Sonst eskaliert
    # zuerst step_limit und danach noch einmal der Fallback für GraphRecursionError.
    agent_tools.ESCALATIONS.clear()
    antwort = agent.handle_ticket(ticket("T-1006"))
    hinweis = "2 × MAX_TOOL_RUNDEN + 2 muss unter recursion_limit=12 bleiben"
    assert "Step-Limit erreicht" in antwort, hinweis
    assert len(agent_tools.ESCALATIONS) == 1, hinweis
