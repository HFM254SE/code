# Lab VL 8 — Aus der Triage wird ein Agent

**Ziel:** Ihr baut aus der LeineTech-Ticket-Pipeline einen **Tool-nutzenden
Agenten** mit LangGraph. Er entscheidet selbst, welche Tools er in welcher
Reihenfolge aufruft, durchsucht die Wissensbasis (`docs/`) und eskaliert bei
Bedarf an einen Menschen — der ReAct-Loop aus VL 7 in Code.

**So arbeitet ihr:** eigenständig, allein oder in Gruppen (organisiert euch selbst),
in eurem Tempo — **KI-Unterstützung ausdrücklich erwünscht**. Am Ende besprechen wir
die Erfahrungen gemeinsam.

**Dauer:** ~90 Minuten Kern (Teil 1: ~20 min · Teil 2: ~35 min · Teil 3: ~20 min · Reflexion: ~15 min) — Erweiterungen frei wählbar, in eurem Tempo.

---

## Schritt 0 — Setup (5–10 min)

```bash
cd leinetech
git checkout vl06-guardrails       # wir bauen auf dem gehärteten Stand auf
pip install -r requirements.txt    # zieht jetzt langgraph + langchain-litellm

# Kurs-Endpunkt setzen (siehe SETUP.md) — derselbe Key wie ab VL 3:
export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"
```

> **Tool-Calling braucht ein tool-fähiges Modell.** Der Kurs-Endpunkt liefert
> mit `qwen3.6-35B-A3B-FP8` (Default in `src/llm.py`) ein zuverlässig
> tool-fähiges Modell. Kleine Modelle lernen zwar die Mechanik, rufen Tools aber
> unzuverlässig auf — deshalb hier bewusst das große Kurs-Modell über HomeCloud.

---

## Teil 1 — Tools verstehen und testen (~20 min)

Ein Agent ist „LLM + Tools + Loop". Die **Tools** sind schon gebaut und
getestet — als ganz normaler Python-Code (`src/agent_tools.py`):

- `kb_search(query)` — durchsucht `docs/` (über `src/knowledge_base.py`)
- `triage_ticket(betreff, text)` — Regel-Klassifikation aus VL 1
- `escalate_to_human(ticket_id, grund)` — die einzige „echte" Aktion

```bash
python -m pytest tests/test_agent_tools.py     # offline, ohne LLM
python -c "from src.agent_tools import kb_search; print(kb_search('VPN AnyConnect Verbindung'))"
```

**Beobachtet:** Die KB-Suche ist simple Keyword-Überlappung — manchmal landet
der falsche Artikel oben. Das ist der Grund, warum ihr in VL 4/5 *Embeddings*
gelernt habt. Fürs Tool-Use-Prinzip reicht es: das LLM bekommt Text zurück
und entscheidet, was es damit macht.

**Frage:** Warum sind die Tools von der Agenten-Logik getrennt? (Antwort: weil
man deterministischen Code testen kann — ein Agent ist nicht-deterministisch.)

---

## Teil 2 — Den Agenten-Graphen bauen (~35 min)

Jetzt verdrahtet ihr den ReAct-Loop selbst. Gerüst kopieren:

```bash
cp labs/templates/agent_skeleton.py src/agent.py
```

Der Graph:
```
   START → agent ⇄ tools → END
           (LLM)   (Code)
   agent schlägt Tool-Calls vor → tools führt aus → zurück zu agent,
   bis das LLM keine Tools mehr braucht und antwortet.
```

Füllt die drei TODOs:
1. **`agent_node`** — Modell mit System-Prompt + bisherigen Messages aufrufen.
2. **`route`** — hat die letzte Nachricht `tool_calls`? → `"tools"`, sonst `END`.
3. **`build_agent`** — Nodes, Entry-Point, conditional edge + Rück-Edge `tools → agent`.

Ausführen — die CLI zeigt jeweils die finale Antwort (den Tool-für-Tool-Verlauf macht ihr gleich mit `stream()` sichtbar):

```bash
python -m src.agent T-1006      # VPN-Frage → kb_search → Antwort
python -m src.agent T-1018      # einfache Frage → KB-Lösung
python -m src.agent T-1003      # Rechnungsmodul-Bug → einordnen, ggf. eskalieren
```

**Den Loop sichtbar machen:** `invoke` zeigt nur das Endergebnis — `stream()` zeigt jeden Node-Durchlauf:

```python
from src.agent import build_agent
from langchain_core.messages import HumanMessage

agent = build_agent()
state = {"messages": [HumanMessage("Bearbeite Ticket T-1006 …")], "ticket_id": "T-1006"}
for schritt in agent.stream(state, stream_mode="values"):
    m = schritt["messages"][-1]
    print(m.type, "→", getattr(m, "tool_calls", None) or m.content[:80])
```

**Grenzen provozieren:** ein Tool absichtlich `raise TimeoutError(...)` werfen lassen (der
Agent erhält „Tool-Fehler: …") oder `handle_ticket(get_ticket("T-1006"), recursion_limit=2)`
aufrufen → `GraphRecursionError`.

> Stecken geblieben? `git checkout vl08-agent` zeigt die Musterlösung mit
> `recursion_limit`-Schutz und der VL-6-Vorabprüfung.

---

## Teil 3 — Sicherheit & Grenzen (~20 min)

**Aufgabe A — Der Angriff von VL 6, jetzt gegen einen Agenten:**
```bash
python -m src.agent T-1030
```
T-1030 enthält die Prompt-Injection. Eine im Gerüst vorgegebene
**Nicht-LLM-Vorabprüfung** (`injection_check`) greift und eskaliert sofort — das
Ticket erreicht das Modell gar nicht. **Diskutiert:** Warum ist das bei einem
*handelnden* Agenten noch wichtiger als bei der reinen Klassifikation aus VL 6?
(Stichwort Excessive Agency: ein Agent, der Tools ausführt, kann durch eine
Injection zu *Aktionen* verleitet werden, nicht nur zu falschem Text.)

**Aufgabe B — Least Privilege:** Der Agent hat genau 3 Tools, keines
destruktiv. Skizziert für euch: Welche Tools bräuchte ein
*produktiver* LeineTech-Agent (Ticket schließen, Mail senden, Konto
zurücksetzen)? Welche davon dürfen **nie** ohne menschliche Freigabe laufen?
Wo genau setzt ihr den Human-in-the-Loop?

**Erweiterungen — frei wählbar, in eurem Tempo (Startcode auf den Folien für Antwort-Review und Eskalations-Tools; A2A und Memory ohne Code):**
- **Antwort-Review** (mittel): eine zweite LLM-Instanz prüft die Entwurfsantwort
  vor dem Versand — neuer Node zwischen `agent` und `END`, Conditional Edge.
- **Eskalations-Tools** (schwer): weitere Tools nach *Least Privilege* (Ticket
  schließen, Konto zurücksetzen) — `reset_account` nur mit echtem
  Human-in-the-Loop (`interrupt()` + Checkpointer).
- **A2A skizzieren** (Konzept): Wie sähe ein zweiter Agent (Eskalations-
  Spezialist) als eigener A2A-Service aus (Agent Card, Task Lifecycle)?
- *Wer schnell ist:* Memory — vorige Lösungen im State halten und wiederverwenden.

---

## Teil 4 — Reflexion (~15 min)

**Gemeinsame Besprechung im Plenum** (wer mag, zeigt kurz seine Lösung): Bei welchem Ticket hat der
Agent gut/schlecht entschieden? Welches Tool wurde unnötig oder gar nicht aufgerufen?

**Leitfragen:**
- Wann lohnt ein Agent gegenüber der festen Pipeline aus VL 3? (Mehr Freiheit
  = mehr Fehlerquellen — „Start simple, add complexity when needed.")
- Wie **testet** man etwas Nicht-Deterministisches? (Tools deterministisch +
  Agent gegen Golden-Tickets evaluieren, vgl. VL 3.)
- Wie misst man Agenten-Qualität jenseits von „läuft durch"? (Hat er das
  richtige Tool gewählt? Eskaliert er zu oft / zu selten?)

---

## Troubleshooting

| Problem | Lösung |
|---|---|
| Agent ruft nie ein Tool auf | Falsches Modell in `LLM_MODEL` — Default `qwen3.6-35B-A3B-FP8` (tool-fähig) nutzen |
| `Recursion limit reached` | Endlosschleife — Modell ruft dasselbe Tool wiederholt; `recursion_limit` greift wie vorgesehen, Prompt schärfen |
| `PermissionDeniedError` / „request blocked" | `LLM_API_KEY` gesetzt? Endpunkt im Zeitfenster (Mo)? Sonst Plan B (Groq), siehe SETUP.md |
| `ModuleNotFoundError: langgraph` | `pip install -r requirements.txt` |
| Antwort kommt, aber ohne KB-Bezug | Modell hat `kb_search` übersprungen — System-Prompt-Schritte expliziter machen |
