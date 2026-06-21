# LeineTech Ticket-Triage — `vl08-agent`

Endzustand des **Labs in VL 8**: Aus der Triage wird ein **Tool-nutzender
Agent**. Er entscheidet selbst, welche Tools er aufruft (Ticket einordnen,
Wissensbasis durchsuchen, an einen Menschen eskalieren) — der ReAct-Loop aus
VL 7, hier als expliziter LangGraph-Graph.

Neu gegenüber `vl06-guardrails`:

- `src/knowledge_base.py` — leichtgewichtige Volltext-Suche über `docs/`
  (bewusst **kein** Vektor-RAG — das ist Svens VL 4/5; hier nur ein Tool).
- `src/agent_tools.py` — die drei Tools des Agenten als **gewöhnliche,
  offline testbare** Funktionen: `kb_search`, `triage_ticket`,
  `escalate_to_human` (+ `injection_check` als Nicht-LLM-Vorprüfung aus VL 6).
- `src/agent.py` — der LangGraph-Agent: `guardrail → agent ⇄ tools → END`,
  mit `recursion_limit` als Endlosschleifen-Schutz.
- `tests/test_agent_tools.py` — **offline** (ohne LLM): KB-Treffer,
  Tool-Verhalten, Eskalations-Protokoll, Injection-Vorprüfung.

## Voraussetzung

```bash
pip install -r requirements.txt
export LLM_BASE_URL="https://llm.homecloud.ee/v1"   # Kurs-Endpunkt, siehe SETUP.md
export LLM_API_KEY="<euer-key>"
```

> **Wichtig:** Tool-Calling braucht ein tool-fähiges Modell. Der Kurs-Endpunkt
> liefert mit `qwen3.6-35B-A3B-FP8` (Default) ein robust tool-fähiges Modell —
> kleine Modelle rufen Tools nur unzuverlässig auf.

## Ausführen

```bash
python -m pytest tests/test_agent_tools.py   # offline, ohne LLM
python -m src.agent T-1001                   # Agent löst eine VPN-Frage per KB
python -m src.agent T-1003                   # Software-Bug — wird eingeordnet
python -m src.agent T-1030                   # Injection → sofort eskaliert (VL 6!)
```

**Diskussionsstoff:** Wann ruft der Agent welches Tool? Was passiert bei
T-1030 (greift die Vorabprüfung oder das Modell?)? Wo gehört ein
Human-in-the-Loop hin, und was darf der Agent **nie** autonom tun
(Least Privilege, VL 6)?

> Hier endet der VL-8-Stand. VL 9 nimmt dasselbe System und schreibt zuerst
> die **Spec** (OpenAPI für die Ticket-API, `CLAUDE.md` fürs Projekt).
