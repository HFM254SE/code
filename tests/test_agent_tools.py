"""Tests für die Agent-Tools und die KB-Suche — komplett offline, kein LLM.

Der Agenten-Graph (src/agent.py) braucht das LLM + LangGraph zum Laufen; die
*Tools* sind aber deterministischer Python-Code und müssen für sich testbar
sein. Genau das ist die Disziplin aus VL 7: Tools sind normaler Code, also
testet man sie wie normalen Code.
"""

import json
from pathlib import Path

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


def test_triage_tool():
    out = agent_tools.triage_ticket("Laptop defekt", "Mein ThinkPad startet nicht mehr.")
    assert "Kategorie:" in out and "Priorität:" in out


def test_escalation_wird_protokolliert():
    agent_tools.ESCALATIONS.clear()
    msg = agent_tools.escalate_to_human("T-9999", "Testgrund")
    assert "T-9999" in msg
    assert agent_tools.ESCALATIONS == [{"ticket_id": "T-9999", "grund": "Testgrund"}]


def test_injection_check_findet_t1030():
    tickets = json.loads((ROOT / "data" / "tickets.json").read_text(encoding="utf-8"))
    t1030 = next(t for t in tickets if t["id"] == "T-1030")
    assert agent_tools.injection_check(t1030["betreff"], t1030["text"])
    # Ein harmloses Ticket darf nicht anschlagen.
    t1001 = next(t for t in tickets if t["id"] == "T-1001")
    assert not agent_tools.injection_check(t1001["betreff"], t1001["text"])
