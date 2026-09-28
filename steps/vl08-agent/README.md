# LeineTech Ticket-Triage: `vl08-agent`

Endzustand des **Labs in VL 8**: Aus der Triage wird ein **Tool-nutzender
Agent**. Er entscheidet selbst, welche Tools er aufruft (Ticket einordnen,
Wissensbasis durchsuchen, an einen Menschen eskalieren). Das ist der ReAct-Loop
aus VL 7 als expliziter LangGraph-Graph.

```text
injection_check  →  [ START → agent ⇄ tools ]  →  END
(VL 6, vor dem                   ↓
 Graphen, ohne LLM)          step_limit  →  END
```

## Was ist neu gegenüber `vl06-guardrails`?

`vl06-guardrails` enthält als Vorbereitung auf das Lab schon die Tools, die
KB-Suche, die Lab-Anleitung und das Gerüst. Neu ist die Graph-Verdrahtung:

- `src/agent.py`: die Musterlösung des Labs. Nodes `agent` (LLM), `tools`
  (Python-Code) und `step_limit`, bedingte Kante `route()`, Rückkante
  `tools → agent`. Dazu die Schutzmechanismen: Step-Limit, Timeout und Backoff
  im Modell, `recursion_limit` mit Fallback an einen Menschen, Vorabprüfung und
  Output-Filter aus VL 6. Mit `--trace` zeigt die Kommandozeile jeden Node-Durchlauf.

Schon aus `vl06-guardrails` übernommen (dort Lab-Vorbereitung):

- `src/knowledge_base.py`: leichtgewichtige Volltext-Suche über `docs/`, bewusst
  **kein** Vektor-RAG (das ist Thema von VL 4/5), hier nur ein Tool.
- `src/agent_tools.py`: die drei Tools als **gewöhnliche, offline testbare**
  Funktionen `kb_search`, `triage_ticket`, `escalate_to_human`, dazu
  `injection_check` als Vorabprüfung ohne LLM.
- `labs/vl08-lab.md` und `labs/templates/agent_skeleton.py`: Anleitung und Gerüst.
- Tests, alle **offline** (ohne LLM):
  - `tests/test_agent_tools.py`: Tool-Verhalten, Eskalations-Protokoll,
    Vorabprüfung, Parameterbeschreibungen im Tool-Schema.
  - `tests/test_knowledge_base.py`: Lösungsabschnitte kommen vollständig an.
  - `tests/test_agent_graph.py`: Verdrahtung mit einem Skript-Modell statt LLM
    (Loop, Tool-Fehler, unbekannte Tools, `interrupt()`, Step-Limit,
    `recursion_limit`, T-1030). Im Stand `vl06-guardrails` wird die Datei
    übersprungen, bis `src/agent.py` existiert.
  - Die Tests aus VL 1, VL 3 und VL 6 (`test_triage.py`, `test_llm.py`,
    `test_summarize.py`, `test_main.py`, `test_evaluate.py`,
    `test_guardrails.py`, `test_haertung.py`) laufen unverändert mit.

## Voraussetzung

```bash
pip install -r requirements.txt
export LLM_BASE_URL="https://llm.homecloud.ee/v1"   # Kurs-Endpunkt, siehe SETUP.md
export LLM_API_KEY="<euer-key>"
```

> **Wichtig:** Tool-Calling braucht ein tool-fähiges Modell. Der Kurs-Endpunkt
> liefert mit `qwen3.6-35B-A3B-FP8` (Default) ein robust tool-fähiges Modell.
> Kleine Modelle rufen Tools nur unzuverlässig auf. Der Endpunkt ist nur montags
> von 06:00 bis 23:59 freigeschaltet.

## Ausführen

```bash
python -m pytest -q                          # alles offline, ohne LLM
python -m src.agent T-1030                   # Injection → sofort eskaliert, ohne LLM (VL 6)
python -m src.agent T-1006                   # Agent löst eine VPN-Frage per KB
python -m src.agent T-1006 --trace           # jeden Node-Durchlauf zeigen
python -m src.agent T-1009                   # Konto gesperrt, Priorität hoch → Eskalation
python -m src.agent T-1006 --recursion-limit 2   # harter Stopp → Fallback an einen Menschen
python -c "from src.agent import build_agent; print(build_agent().get_graph().draw_mermaid())"
```

**Diskussionsstoff:** Wann ruft der Agent welches Tool? Bei welchem Ticket liegt
er falsch, weil die Regel-Triage falsch liegt (T-1006, T-1024)? Was passiert bei
T-1030: Greift die Vorabprüfung oder das Modell? Was darf der Agent **nie**
autonom tun (Least Privilege, VL 6), und wo gehört eine Freigabe hin
(Human-in-the-Loop mit `interrupt()`, Erweiterung B im Lab)?

> Hier endet der VL-8-Stand. VL 9 nimmt dasselbe System und fragt: Woher weiß
> ein Prüfer, was richtig ist, wenn KI den Code schreibt? Dazu kommen Mutation
> Testing gegen schwache Testorakel und Spec-Driven Development mit einer
> OpenAPI-Spec als Gate (`vl09-oracle`).
