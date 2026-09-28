"""Tests für die Agent-Tools und die KB-Suche, komplett offline und ohne LLM.

Der Agenten-Graph (src/agent.py) braucht zum Laufen ein LLM und LangGraph.
Die Tools sind aber deterministischer Python-Code und müssen für sich testbar
sein. Das ist die Disziplin aus VL 7: Tools sind normaler Code, also testet
man sie wie normalen Code.
"""

import json
from pathlib import Path

import pytest

from src import agent_tools
from src.knowledge_base import search_knowledge_base

ROOT = Path(__file__).resolve().parent.parent


def test_kb_findet_vpn_artikel():
    hits = search_knowledge_base("Ich komme nicht ins VPN mit AnyConnect", docs_dir=ROOT / "docs")
    assert hits, "VPN-Anfrage sollte Treffer liefern"
    assert any("vpn" in h["artikel"] for h in hits), [h["artikel"] for h in hits]


def test_kb_leer_bei_unsinn():
    assert search_knowledge_base("xyzzy", docs_dir=ROOT / "docs") == []


def test_kb_search_tool_liefert_text():
    out = agent_tools.kb_search("Drucker im 3. OG druckt nicht")
    assert isinstance(out, str) and out


def test_kb_search_nennt_artikel_und_abschnitt():
    # Das Format [artikel › abschnitt] erlaubt dem LLM den Verweis auf die Quelle.
    out = agent_tools.kb_search("VPN AnyConnect")
    assert out.startswith("[vpn-zugang › ")


def test_kb_search_meldet_leere_suche_als_text():
    # Auch „nichts gefunden“ ist eine Observation, auf die das LLM reagieren kann.
    assert agent_tools.kb_search("xyzzy") == "Keine passenden Artikel in der Wissensbasis gefunden."


def test_triage_tool():
    out = agent_tools.triage_ticket("Laptop defekt", "Mein ThinkPad startet nicht mehr.")
    assert "Kategorie:" in out and "Priorität:" in out


def test_escalation_wird_protokolliert():
    agent_tools.ESCALATIONS.clear()
    msg = agent_tools.escalate_to_human("T-9999", "Testgrund")
    assert "T-9999" in msg
    assert agent_tools.ESCALATIONS == [{"ticket_id": "T-9999", "grund": "Testgrund"}]
    agent_tools.ESCALATIONS.clear()


def test_injection_check_findet_t1030():
    tickets = json.loads((ROOT / "data" / "tickets.json").read_text(encoding="utf-8"))
    t1030 = next(t for t in tickets if t["id"] == "T-1030")
    assert agent_tools.injection_check(t1030["betreff"], t1030["text"])
    # Ein harmloses Ticket darf nicht anschlagen.
    t1001 = next(t for t in tickets if t["id"] == "T-1001")
    assert not agent_tools.injection_check(t1001["betreff"], t1001["text"])


def test_jeder_tool_parameter_hat_eine_beschreibung():
    # Docstring und Typ-Hints werden zum JSON-Schema, das das LLM sieht (bind_tools).
    function_calling = pytest.importorskip("langchain_core.utils.function_calling")
    for tool in agent_tools.AGENT_TOOLS:
        schema = function_calling.convert_to_openai_tool(tool)["function"]
        assert schema["description"], tool.__name__
        for name, parameter in schema["parameters"]["properties"].items():
            assert parameter.get("description"), f"{tool.__name__}: Parameter {name} ohne Args-Eintrag"
