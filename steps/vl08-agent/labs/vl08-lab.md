# Lab VL 8: Aus der Triage wird ein Agent

**Worum es geht:** Ihr baut aus der LeineTech-Ticket-Triage einen Tool-nutzenden
Agenten mit LangGraph. Er entscheidet selbst, welche Tools er in welcher
Reihenfolge aufruft: Ticket einordnen, Wissensbasis (Knowledge Base, KB) in
`docs/` durchsuchen, bei Bedarf an einen Menschen eskalieren. Das ist der
ReAct-Loop aus VL 7 (Thought → Action → Observation) als lauffähiger Graph.

**So arbeitet ihr:** allein oder in Gruppen, in eurem Tempo. KI-Unterstützung im
Editor ist ausdrücklich erwünscht. Am Ende tauschen wir uns im Plenum aus.

## Lernziele

Nach dem Lab könnt ihr …

1. einen ReAct-Agenten in LangGraph **verdrahten** (agent-Node, tools-Node,
   bedingte Kante, Rückkante) und seinen Loop mit einem Trace **sichtbar machen**.
2. Schutzmechanismen **auslösen und unterscheiden**: Tool-Fehler als Observation,
   Step-Limit als geplanter Ausstieg, `recursion_limit` als harter Stopp mit
   Fallback an einen Menschen.
3. die Entscheidungen des Agenten gegen Soll-Labels **prüfen** und **begründen**,
   welche Aktionen er allein ausführen darf und welche eine menschliche Freigabe brauchen.

## Voraussetzungen

- [ ] Checkpoint-Branch **`vl06-guardrails`**. Wer VL 6 verpasst hat, steigt genau hier ein.
- [ ] `pip install -r requirements.txt` ist erledigt (lädt `langgraph` und
      `langchain-litellm`). Am besten schon vor der Vorlesung.
- [ ] Persönlicher API-Key für den Kurs-Endpunkt (HomeCloud, siehe `SETUP.md`).
      Der Endpunkt ist **nur montags von 06:00 bis 23:59** freigeschaltet. Die erste
      Antwort nach einem Kaltstart kann bis zu 300 s dauern.
- [ ] Die Begriffe aus VL 7: ReAct-Loop und Function Calling (das LLM schlägt
      einen Tool-Call vor, euer Code führt ihn aus).

Ohne Endpunkt kommt ihr trotzdem weit: Schritt 1, der Offline-Test in Schritt 2
und der Offline-Test in Schritt 4b laufen komplett ohne LLM. Wer nur nacharbeiten
will, kann auch direkt den fertigen Stand `git checkout vl08-agent` nehmen und die
Schritte dort nachvollziehen.

## Zeitplan

| Schritt | Inhalt | min |
|---|---|---|
| 0 | Setup-Check | 5 |
| 1 | Tools sind normaler Code: testen und ansehen | 10 |
| 2 | Den Graphen verdrahten (TODO 1 bis 3) und ausführen | 25 |
| 3 | Den Loop sichtbar machen | 10 |
| 4 | Grenzen provozieren und Entscheidungen prüfen (4a bis 4c, darin TODO 4) | 20 |
| Bonus | Erweiterungen A bis D, frei wählbar | 15 |
| danach | Austausch im Plenum | 10 |

Zusammen mit der Einführung auf den Folien sind das 90 Minuten Lab plus Austausch.
Wer zu Hause nacharbeitet, braucht ohne Wartezeiten am Endpunkt meist weniger.

---

## Schritt 0: Setup-Check (5 min)

```bash
cd leinetech                      # euer Klon des Kurs-Repos
git fetch origin                  # aktuelle Checkpoint-Branches holen
git status                        # offene VL-6-Änderungen? Erst committen
git checkout vl06-guardrails      # Startpunkt: der gehärtete Stand aus VL 6
pip install -r requirements.txt   # langgraph und langchain-litellm

export LLM_BASE_URL="https://llm.homecloud.ee/v1"   # Kurs-Endpunkt, siehe SETUP.md
export LLM_API_KEY="<euer-key>"                     # PowerShell: $env:LLM_API_KEY = "<euer-key>"

python -m pytest tests/test_agent_tools.py tests/test_knowledge_base.py -q
```

Erwartet:

```text
13 passed in 0.28s
```

pytest hängt an diese Zeile je nach Umgebung noch Warnungen und eine andere
Laufzeit an. Entscheidend sind die Zahlen für passed, failed und skipped.

Dann die Konfiguration prüfen, ohne den Endpunkt zu fragen:

```bash
python -m src.llm
```

Erwartet:

```text
Endpunkt: https://llm.homecloud.ee/v1
Modell:   qwen3.6-35B-A3B-FP8
API-Key:  gesetzt
Thinking: Server-Default
Timeout:  120 s
```

Steht dort `API-Key:  FEHLT`, ist `LLM_API_KEY` in diesem Terminal nicht gesetzt.
Ist alles gesetzt, prüft ihr den Endpunkt selbst:

```bash
python -c "from src.llm import chat; print(chat('Sag Moin.'))"
```

Erwartet ist ein kurzer Gruß, zum Beispiel `Moin!`. Die erste Anfrage des Tages
kann nach 120 s mit `Timeout` abbrechen, weil das Modell erst geladen wird
(Kaltstart, bis 300 s). Wiederholt den Befehl dann oder setzt vorher
`export LLM_TIMEOUT=360`.

> **✓ Checkpoint 0:** Die Tests sind grün, und der Endpunkt antwortet.
> Antwortet nur der Endpunkt nicht, macht trotzdem weiter. Schritt 1 und der
> Offline-Test in Schritt 2 brauchen ihn nicht. Lösungen stehen im Troubleshooting.

---

## Schritt 1: Tools sind normaler Code (10 min)

Ein Agent ist „LLM + Tools + Loop“. Die Tools sind schon gebaut und getestet,
als ganz normaler Python-Code in `src/agent_tools.py`:

| Tool | Was es tut | Woher |
|---|---|---|
| `kb_search(query)` | durchsucht `docs/` per Keyword-Überlappung | `src/knowledge_base.py` |
| `triage_ticket(betreff, text)` | ordnet Kategorie und Priorität per Regeln ein | Regel-Triage aus VL 1 |
| `escalate_to_human(ticket_id, grund)` | übergibt das Ticket an einen Menschen | die einzige Aktion des Agenten |

Probiert die Tools ohne LLM aus. Wir nehmen Ticket T-1006: Das VPN steht, aber
das Projektlaufwerk P: fehlt.

```bash
python -c "from src.agent_tools import kb_search; print(kb_search('VPN Tunnel Laufwerk DNS')[:400])"
```

Erwartet (der Befehl zeigt nur die ersten 400 Zeichen):

```text
[vpn-zugang › Tunnel steht, aber interne Ressourcen (Laufwerke, DMS, Jira) nicht erreichbar]
Tunnel steht, aber interne Ressourcen (Laufwerke, DMS, Jira) nicht erreichbar
Typische Ursache ist DNS oder Routing, nicht die Anmeldung:
1. VPN trennen und neu verbinden (Profil wird neu geladen).
2. `nslookup dms.leinetech.intern` ausführen — kommt keine `10.20.x.x`-Adresse zurück, liegt ein DNS-Problem
```

```bash
python -c "from src.agent_tools import triage_ticket; from src.ticket_loader import get_ticket; t = get_ticket('T-1006'); print(triage_ticket(t['betreff'], t['text']))"
```

Erwartet:

```text
Kategorie: Zugang, Priorität: mittel
```

Und so sieht das LLM das Tool `kb_search`. `bind_tools()` macht aus Docstring
und Typ-Hints genau dieses JSON-Schema (Function Calling aus VL 7):

```bash
python -c "import json; from langchain_core.utils.function_calling import convert_to_openai_tool; from src.agent_tools import kb_search; print(json.dumps(convert_to_openai_tool(kb_search), indent=2, ensure_ascii=False))"
```

Erwartet:

```json
{
  "type": "function",
  "function": {
    "name": "kb_search",
    "description": "Durchsucht die LeineTech-Wissensbasis und liefert relevante Abschnitte. Nutze dieses Tool, um eine Lösung für das Anliegen der Nutzerin zu finden, bevor du antwortest.",
    "parameters": {
      "properties": {
        "query": {
          "description": "Suchbegriffe aus dem Ticket, z. B. \"VPN Tunnel Laufwerk DNS\".",
          "type": "string"
        }
      },
      "required": [
        "query"
      ],
      "type": "object"
    }
  }
}
```

**Beobachtet:**

- Der KB-Treffer nennt seine Quelle als `[artikel › abschnitt]` und enthält die
  Lösungsschritte (`nslookup`). Die Suche ist einfache Keyword-Überlappung, kein
  Embedding wie in VL 4/5. Manchmal landet deshalb ein unpassender Abschnitt oben.
- Die Regel-Triage sagt **Zugang**. Richtig wäre **Netzwerk** (siehe
  `eval/golden.jsonl`). Das ist eine der Keyword-Fallen aus VL 1. Genau dieses
  falsche Ergebnis bekommt gleich auch der Agent.

**Fragen:**

<details>
<summary>Warum sind die Tools von der Agenten-Logik getrennt?</summary>

Tools sind deterministischer Code. Sie lassen sich ohne LLM testen, und ein Test
liefert jedes Mal dasselbe Ergebnis. Der Agent als Ganzes ist nicht deterministisch.
Wer beides trennt, kann wenigstens die Bausteine zuverlässig absichern.
</details>

<details>
<summary>Welcher Teil des Docstrings steuert, ob das LLM das Tool wählt?</summary>

Die `description`: die erste Zeile und der Satz „Nutze dieses Tool, um …, bevor du
antwortest.“ Die Einträge unter `Args:` werden zu Parameterbeschreibungen und
helfen dem Modell, sinnvolle Argumente zu bilden. Ein Test in
`tests/test_agent_tools.py` prüft, dass jeder Parameter beschrieben ist.
</details>

> **✓ Checkpoint 1:** Ihr habt KB-Treffer, Triage-Ergebnis und Schema gesehen.
> Ihr wisst, dass `triage_ticket` bei T-1006 falsch liegt.

---

## Schritt 2: Den Graphen verdrahten (25 min)

Kopiert das Gerüst nach `src/agent.py` (auf `vl06-guardrails` gibt es die Datei
noch nicht):

```bash
cp labs/templates/agent_skeleton.py src/agent.py
```

Auf dem Branch `vl08-agent` überschreibt der Befehl die Musterlösung. Zurück geht
es dort mit `git restore src/agent.py`.

Der Graph, den ihr baut:

```text
injection_check  →  [ START → agent ⇄ tools ]  →  END
(VL 6, läuft vor dem Graphen, ohne LLM)

agent   Reason: Das LLM liest den Verlauf und schlägt Tool-Calls oder eine Antwort vor.
tools   Act und Observe: Python-Code führt die Tool-Calls aus, das Ergebnis geht zurück.
```

**Vorgegeben** (kein TODO): `tool_node`, `step_limit_node`, `handle_ticket` mit der
Vorabprüfung aus VL 6, der Trace (`--trace`) und die Kommandozeile.
**Ihr baut** in `src/agent.py`:

1. **TODO 1 `agent_node`:** das Modell mit Systemprompt und bisherigem Verlauf
   aufrufen und die Antwort als Teil-Update zurückgeben.
2. **TODO 2 `route`:** Hat die letzte Nachricht `tool_calls`? Dann `"tools"`, sonst `END`.
3. **TODO 3 `build_agent`:** Nodes anlegen, Einstieg von `START`, bedingte Kante
   nach `agent`, Rückkante `tools → agent`.

TODO 4 lasst ihr vorerst offen. Das kommt in Schritt 4b.

### Erst offline prüfen

Die Datei `tests/test_agent_graph.py` ersetzt das LLM durch ein Skript-Modell mit
festen Antworten. So prüft ihr die Verdrahtung ohne Endpunkt.

```bash
python -m pytest tests/test_agent_graph.py -q
```

Direkt nach dem Kopieren ist das rot. Erwartet:

```text
11 failed, 4 passed
```

Die Fehlermeldungen zeigen, welches TODO fehlt: `NotImplementedError: TODO 2: route`
oder `ValueError: Graph must have an entrypoint …` (TODO 3). Nach TODO 1 bis 3
erwartet ihr:

```text
14 passed, 1 skipped
```

Der eine übersprungene Test gehört zu TODO 4 (Schritt 4b).

<details>
<summary>Hinweis zu TODO 1</summary>

```python
antwort = _model().invoke([SystemMessage(AGENT_SYSTEM_PROMPT), *state["messages"]])
return {"messages": [antwort]}
```

Der Node gibt nur das geänderte Feld zurück. Der Reducer `add_messages` hängt die
Antwort an den Verlauf an, statt ihn zu überschreiben.
</details>

<details>
<summary>Hinweis zu TODO 2</summary>

```python
if getattr(state["messages"][-1], "tool_calls", None):
    return "tools"
return END
```
</details>

<details>
<summary>Hinweis zu TODO 3</summary>

```python
graph.add_node("agent", agent_node)
graph.add_node("tools", tool_node)
graph.add_edge(START, "agent")                                            # Einstieg
graph.add_conditional_edges("agent", route, {"tools": "tools", END: END})  # bedingte Kante
graph.add_edge("tools", "agent")                                          # Rückkante: der Loop
```
</details>

### Dann gegen den Endpunkt

```bash
python -m src.agent T-1006    # VPN steht, Laufwerk P: fehlt
python -m src.agent T-1009    # Konto gesperrt, dringend
python -m src.agent T-1018    # Internet im Homeoffice langsam
python -m src.agent T-1003    # FinanzPro stürzt beim PDF-Export ab
```

Die Kommandozeile zeigt nur die finale Antwort, denn `invoke()` liefert nur das
Endergebnis. Beispiel für T-1006 (der Wortlaut hängt vom Modell ab):

```text
=== Agent bearbeitet T-1006: Kein Zugriff auf Projektlaufwerk über VPN ===

Bitte VPN trennen und neu verbinden. Prüft danach mit nslookup dms.leinetech.intern die DNS-Auflösung (KB: vpn-zugang).
```

Hat der Agent eskaliert, folgt ein Block `--- Eskalationen ---` mit Ticket-ID und Grund.

Was ihr ungefähr erwarten könnt:

| Ticket | Regel-Triage (Tool) | Soll laut `eval/golden.jsonl` | Erwartetes Verhalten |
|---|---|---|---|
| T-1006 | Zugang, mittel | Netzwerk, mittel | Antwort mit Verweis auf `vpn-zugang` und `nslookup` |
| T-1009 | Zugang, hoch | Zugang, hoch | Eskalation, weil die Priorität hoch ist |
| T-1018 | Netzwerk, mittel | Netzwerk, mittel | Antwort mit der Split-Tunneling-Lösung (VPN neu verbinden) |
| T-1003 | Abrechnung, hoch | Software, hoch | Eskalation, weil die Priorität hoch ist. Zusätzlich passt der KB-Top-Treffer nicht (Keyword-Grenze) |

**Prüft:** Hat die Antwort einen KB-Bezug? Wird T-1009 eskaliert? Notiert für
jedes Ticket, ob eskaliert wurde. Die Tabelle braucht ihr in Schritt 4c.

> **✓ Checkpoint 2:** `python -m pytest tests/test_agent_graph.py -q` meldet
> `14 passed, 1 skipped`, und T-1006 liefert eine Antwort.
> **Aufholen:** Wer festhängt, klappt die Hinweise oben auf. Wer ganz neu
> einsteigen will, übernimmt die Musterlösung (enthält auch Schritt 4b):
> `git show origin/vl08-agent:src/agent.py > src/agent.py`

---

## Schritt 3: Den Loop sichtbar machen (10 min)

Skizziert zuerst auf Papier, welchen Weg T-1009 durch den Graphen nehmen sollte.
Dann schaut nach:

```bash
python -m src.agent T-1006 --trace
python -m src.agent T-1009 --trace
```

Erwartet für T-1006 (Tool-Ergebnisse sind fest, die `ai`-Zeilen hängen vom Modell ab):

```text
=== Agent bearbeitet T-1006: Kein Zugriff auf Projektlaufwerk über VPN ===

start      human → Bearbeite dieses Ticket (ID T-1006). Betreff: Kein Zugriff auf Projektlaufwerk über VPN Text: Über …
agent      ai    → triage_ticket(betreff='Kein Zugriff auf Projektlaufwe', text='Über das VPN von zuhause habe ')
tools      tool  → Kategorie: Zugang, Priorität: mittel
agent      ai    → kb_search(query='VPN Tunnel Laufwerk DNS')
tools      tool  → [vpn-zugang › Tunnel steht, aber interne Ressourcen (Laufwerke, DMS, Jira) nicht erreichbar] Tunnel…
agent      ai    → Bitte VPN trennen und neu verbinden. Prüft danach mit nslookup dms.leinetech.intern die DNS-Auflösu…

=== Finale Antwort ===
Bitte VPN trennen und neu verbinden. …
```

`--trace` nutzt `stream()` statt `invoke()`. Jeder Node-Durchlauf liefert ein
Update, und der Trace druckt es. Der Kern steht in `_stream_with_trace()`:

```python
for update in agent.stream(state, config, stream_mode="updates"):
    for node, changes in update.items():
        for message in (changes or {}).get("messages", []):
            print(_format_step(node, message))
```

Den Graphen selbst zeigt LangGraph als Mermaid-Diagramm. `get_graph()` gibt es
nur auf dem kompilierten Graphen:

```bash
python -c "from src.agent import build_agent; print(build_agent().get_graph().draw_mermaid())"
```

Erwartet (Auszug, gestrichelt heißt bedingte Kante):

```text
	__start__ --> agent;
	agent -.-> __end__;
	agent -.-> tools;
	tools --> agent;
```

Nach Schritt 4b kommen `agent -.-> step_limit` und `step_limit --> __end__` dazu.
Wer das Diagramm grafisch sehen will, fügt die Ausgabe in einen Mermaid-Viewer
ein (z. B. die Markdown-Vorschau im Editor oder mermaid.live).

**Prüffragen:**

<details>
<summary>Welche Kante macht aus dem Ablauf einen Loop, und wo endet er?</summary>

Die Rückkante `tools --> agent` macht den Loop. Er endet über die bedingte Kante
`agent -.-> __end__`: `route()` liefert `END`, sobald die letzte LLM-Antwort keine
`tool_calls` mehr enthält.
</details>

<details>
<summary>Warum fehlt injection_check im Diagramm?</summary>

Die Vorabprüfung ist kein Node. `handle_ticket()` ruft sie vor dem Graphen auf.
Schlägt sie an, startet der Graph gar nicht erst.
</details>

<details>
<summary>Wie viele LLM-Aufrufe brauchte T-1006, und hat das Modell der Triage geglaubt?</summary>

Jede `agent`-Zeile ist ein LLM-Aufruf, im Beispiel also drei. Schaut, ob die
Antwort die Kategorie „Zugang“ übernimmt oder ob das Modell sie korrigiert.
Ein Agent ist nur so gut wie seine Tools.
</details>

> **✓ Checkpoint 3:** Ihr seht im Trace die Runden `agent → tools → agent` und
> könnt sagen, an welcher Stelle die Schleife endet.

---

## Schritt 4: Grenzen provozieren und Entscheidungen prüfen (20 min)

In der Theorie hattet ihr fünf Schutzmechanismen. So verteilen sie sich im Code,
zusammen mit den weiteren Schutzschichten:

| Ebene | Mechanismus | Stelle in `src/agent.py` | Im Lab |
|---|---|---|---|
| Schutzmechanismus 1 | Step-Limit | `route()` und `step_limit_node()`, `MAX_TOOL_RUNDEN` | 4b (TODO 4) |
| Schutzmechanismus 2 | Timeout und `recursion_limit` | `_model()`: `request_timeout=get_timeout()` (120 s, siehe `src/llm.py`), `handle_ticket(recursion_limit=12)` | 4a |
| Schutzmechanismus 3 | Exponential Backoff | `_model()`: `MAX_RETRIES`, in `ChatLiteLLM` eingebaut | nur lesen |
| Schutzmechanismus 4 | Fallback an einen Menschen | `handle_ticket()`: `GraphRecursionError` → `escalate_to_human` | 4a |
| Schutzmechanismus 5 | Token-Budget | fehlt im Lab-Code bewusst | Diskussion |
| Robustheit im tools-Node | Tool-Fehler und unbekannte Tools werden Observation | `tool_node()` | 4a |
| Sicherheit (VL 6) | Vorabprüfung, Output-Filter, Least Privilege | `handle_ticket()`, `src/agent_tools.py` | 4c |

### 4a: Schutzmechanismen auslösen (5 min)

**Tool-Fehler**, ohne eine Datei zu ändern. Der Patch gilt nur in diesem einen
Python-Prozess:

```bash
python -c "
import src.agent as a
def kaputt(query: str) -> str:
    raise TimeoutError('KB nicht erreichbar')
a._TOOLS_BY_NAME['kb_search'] = kaputt
print(a.handle_ticket(a.get_ticket('T-1006'), trace=True))
"
```

Erwartet ist im Trace die Zeile, sobald das Modell `kb_search` aufruft:

```text
tools      tool  → Tool-Fehler: KB nicht erreichbar
```

Was danach passiert, entscheidet das Modell: noch einmal suchen, ohne KB antworten
oder eskalieren. Der Agent stürzt jedenfalls nicht ab, denn `tool_node` macht aus
dem Fehler eine Observation.

**Harter Stopp mit Fallback:**

```bash
python -m src.agent T-1006 --recursion-limit 2
```

Erwartet, sobald das Modell ein Tool aufruft:

```text
=== Agent bearbeitet T-1006: Kein Zugriff auf Projektlaufwerk über VPN ===

Ticket T-1006 an Team eskaliert. Grund: recursion_limit=2 erreicht (harter Stopp von LangGraph)

--- Eskalationen ---
[
  {
    "ticket_id": "T-1006",
    "grund": "recursion_limit=2 erreicht (harter Stopp von LangGraph)"
  }
]
```

`recursion_limit` zählt Supersteps. Ein Superstep ist ein Takt, in dem die gerade
aktiven Nodes je einmal laufen. Hier sind das `agent` (1) und `tools` (2). Der
dritte Schritt überschreitet das Limit, LangGraph wirft `GraphRecursionError`,
und `handle_ticket()` übergibt das Ticket an einen Menschen. Antwortet das Modell
sofort ohne Tool, endet der Lauf nach einem Superstep ganz regulär.

Die nackte Ausnahme ohne Fallback seht ihr so:

```bash
python -c "from src.agent import build_agent, initial_state, get_ticket; build_agent().invoke(initial_state(get_ticket('T-1006')), {'recursion_limit': 2})"
```

```text
langgraph.errors.GraphRecursionError: Recursion limit of 2 reached without hitting a stop condition. …
```

<details>
<summary>Wie viele LLM-Aufrufe erlaubt recursion_limit=12, und warum setzen wir es überhaupt?</summary>

Eine Runde `agent → tools` sind zwei Supersteps. Ein Lauf muss mit höchstens 11
Supersteps enden. 12 erlaubt also höchstens sechs LLM-Aufrufe (6× `agent` und
5× `tools`). Ohne eigenen Wert gilt der Default von LangGraph. Der liegt seit
Version 1.0.6 bei 10 000 Supersteps (vorher 25) und schützt damit praktisch nicht.
Global ändern lässt er sich über die Umgebungsvariable `LANGGRAPH_DEFAULT_RECURSION_LIMIT`.
Wir setzen den Wert lieber pro Aufruf, dann steht er sichtbar im Code.
</details>

### 4b: Step-Limit selbst bauen, TODO 4 (7 min)

`recursion_limit` ist ein Sicherheitsnetz des Frameworks und endet mit einer
Ausnahme. Ein Step-Limit ist ein geplanter Ausstieg im eigenen Code: Nach
`MAX_TOOL_RUNDEN` Tool-Runden geht die bedingte Kante nicht mehr zu `tools`,
sondern zu `step_limit`. Dieser Node eskaliert geordnet. Auch ein Abbruch ist
also nur eine bedingte Kante.

Füllt TODO 4 an zwei Stellen in `src/agent.py`: in `route()` und in `build_agent()`.
`_tool_runden()` und `step_limit_node()` sind vorgegeben.

```bash
python -m pytest tests/test_agent_graph.py -q
```

Erwartet:

```text
15 passed
```

Probiert es gegen den Endpunkt aus. Setzt dafür kurz `MAX_TOOL_RUNDEN = 0` und
startet `python -m src.agent T-1006 --trace`. Dann greift das Step-Limit schon bei
der ersten Tool-Anforderung, und die letzte Trace-Zeile lautet:

```text
step_limit ai    → Ticket T-1006 an Team eskaliert. Grund: Step-Limit erreicht (MAX_TOOL_RUNDEN=0)
```

Setzt den Wert danach wieder auf `4`. `_tool_runden()` zählt LLM-Antworten mit
Tool-Calls, nicht einzelne Calls. Mit `MAX_TOOL_RUNDEN = 1` greift das Limit
deshalb nur, wenn das Modell zwei getrennte Runden braucht. Ruft es
`triage_ticket` und `kb_search` in einer Antwort gemeinsam auf, antwortet es
danach regulär.

<details>
<summary>Hinweis zu TODO 4</summary>

In `route()`, vor `return "tools"`:

```python
if _tool_runden(state["messages"]) > MAX_TOOL_RUNDEN:
    return "step_limit"
```

In `build_agent()`:

```python
graph.add_node("step_limit", step_limit_node)
graph.add_conditional_edges(
    "agent", route, {"tools": "tools", "step_limit": "step_limit", END: END}
)
graph.add_edge("step_limit", END)
```
</details>

<details>
<summary>Greift mit MAX_TOOL_RUNDEN = 4 das Step-Limit oder recursion_limit=12 zuerst?</summary>

Das Step-Limit. Vier Runden `agent → tools` sind acht Supersteps. Dazu kommen der
fünfte `agent`-Aufruf und `step_limit`, zusammen zehn. Das liegt unter zwölf. So
soll es sein: Der eigene, geordnete Ausstieg greift vor dem harten Stopp.

Allgemein gilt: 2 × `MAX_TOOL_RUNDEN` + 2 Supersteps müssen unter
`recursion_limit` bleiben (4 → 10 < 12). LangGraph verwirft auch einen Lauf,
dessen letzter Superstep genau auf das Limit fällt. Mit `MAX_TOOL_RUNDEN = 5`
wären es zwölf Supersteps. `step_limit` eskaliert dann noch, danach kommt
trotzdem `GraphRecursionError`, und das Ticket steht zweimal in der
Eskalationsliste.
</details>

### 4c: Entscheidungen messen und Sicherheit prüfen (8 min)

**Messen statt glauben.** Lasst noch T-1024 und T-1025 mit `--trace` laufen.
T-1024: „Kein Stress, aber …“, die Person kommt in kein System mehr. T-1025: Das
TimeTrack-Update scheitert mit Fehlercode 1603.

```bash
python -m src.agent T-1024 --trace
python -m src.agent T-1025 --trace
grep -E '"T-10(03|06|09|18|24|25)"' eval/golden.jsonl
```

Die Soll-Labels:

```text
{"id": "T-1003", "kategorie": "Software", "prioritaet": "hoch"}
{"id": "T-1006", "kategorie": "Netzwerk", "prioritaet": "mittel"}
{"id": "T-1009", "kategorie": "Zugang", "prioritaet": "hoch"}
{"id": "T-1018", "kategorie": "Netzwerk", "prioritaet": "mittel"}
{"id": "T-1024", "kategorie": "Zugang", "prioritaet": "hoch"}
{"id": "T-1025", "kategorie": "Software", "prioritaet": "mittel"}
```

Füllt die Tabelle mit euren Läufen aus Schritt 2 und 3 und den beiden Läufen von
eben. Die Regel lautet wie im Systemprompt: Priorität hoch heißt eskalieren. Die
Spalte „Code-Router (Teil 1)“ ist vorbefüllt. Sie zeigt, wie der Code-Router aus
Teil 1 der Vorlesung entscheidet (offline nachgerechnet). Er eskaliert bei
Priorität hoch und antwortet sonst mit dem ersten KB-Treffer.

| Ticket | Code-Router (Teil 1) | Tool-Folge laut Trace | eskaliert? | soll eskaliert werden? | richtig? |
|---|---|---|---|---|---|
| T-1003 | eskaliert ✓ | | | ja | |
| T-1006 | antwortet ✓ | | | nein | |
| T-1009 | eskaliert ✓ | | | ja | |
| T-1018 | antwortet ✓ | | | nein | |
| T-1024 | antwortet ✗ | | | ja | |
| T-1025 | Passwort-Anleitung ✗ | | | nein, Antwort mit dem FAQ-Treffer | |

Wo liegt der Agent falsch, und liegt der Fehler im Graphen, im Prompt oder im
Tool? Wo schlägt er den Code-Router?

<details>
<summary>Was ist zu erwarten, und warum?</summary>

Die Regel-Triage stuft T-1024 als „niedrig“ ein. Das ist die Negationsfalle aus
VL 1 („Kein Stress“). Folgt das Modell dem Tool, eskaliert es nicht, obwohl die
Person komplett ausgesperrt ist. Der Fehler steckt im Tool, nicht im Graphen.
Genau deshalb misst man gegen Soll-Labels, statt der Antwort zu glauben.

Bei T-1025 haben drei KB-Abschnitte denselben Score 6: „Passwort-Reset im
Self-Service“, „Kontosperrung nach Fehlversuchen“ und der FAQ-Eintrag in
`software-und-lizenzen`. Das Wort „Self-Service-Portal“ im Ticket zieht die
Passwort-Artikel nach oben. Der Code-Router nimmt den ersten Treffer und
antwortet mit der Passwort-Anleitung. Passend ist nur der FAQ-Eintrag zum
Fehlercode 1603. Wählt das Modell ihn, entscheidet der Agent hier besser als der
Code-Router. Oft sind es deshalb vier oder fünf von sechs richtigen
Entscheidungen, je nachdem, ob das Modell bei T-1025 den FAQ-Treffer wählt.
</details>

**Der Angriff aus VL 6, jetzt gegen einen Agenten:**

```bash
python -m src.agent T-1030
```

Erwartet (ohne LLM-Aufruf, auch außerhalb des Montagsfensters):

```text
=== Agent bearbeitet T-1030: Deployment-Anwendung LT-Deploy hängt komplett ===

Ticket T-1030 an Team eskaliert. Grund: Injection-Verdacht (instruction_override): Vorabprüfung

--- Eskalationen ---
[
  {
    "ticket_id": "T-1030",
    "grund": "Injection-Verdacht (instruction_override): Vorabprüfung"
  }
]
```

Außerdem läuft jede finale Antwort durch den Output-Filter aus VL 6
(`filter_output`). Nennt das Modell eine E-Mail-Adresse wie `it-support@leinetech.de`,
erscheint dort `[EMAIL ENTFERNT]`.

<details>
<summary>Was passiert mit der Lösung aus docs/drucker.md (gastdruck@leinetech.de)?</summary>

Der Filter maskiert jede E-Mail-Adresse, auch legitime Firmenadressen aus der KB.
Die korrekte Antwort „Dokument an `gastdruck@leinetech.de` senden“ kommt als
„Dokument an [EMAIL ENTFERNT] senden“ an und hilft niemandem mehr. Das ist
Over-Blocking: Der Datenschutz gewinnt, die Nützlichkeit verliert. Überlegt: Wie
sähe eine Allowlist für Adressen mit `@leinetech.de` aus? Welches Risiko bringt
sie? Auch persönliche Adressen von Beschäftigten enden auf `@leinetech.de` und
wären dann wieder sichtbar. Eine engere Liste mit bekannten Funktionspostfächern
wäre eine Alternative. Es geht hier um die Abwägung, nicht um eine Änderung an
`src/guardrails.py`.
</details>

<details>
<summary>Warum ist die Vorabprüfung bei einem handelnden Agenten noch wichtiger als in VL 6?</summary>

Stichwort Excessive Agency: Ein Agent führt Tools aus. Eine Injection kann ihn zu
Aktionen verleiten, nicht nur zu falschem Text. Je mehr Tools er hat, desto größer
ist der mögliche Schaden.
</details>

<details>
<summary>Was, wenn die Injection nicht im Ticket steht, sondern in einem KB-Artikel?</summary>

`injection_check` prüft nur Betreff und Text des Tickets. Was `kb_search` zurückgibt,
landet ungeprüft im Kontext des Modells. Das ist der Weg der indirekten Prompt
Injection aus VL 6. Least Privilege begrenzt dann den Schaden durch Tools: Der
Agent hat nur drei Tools, und keines kann etwas zerstören. Eine manipulierte
Antwort an die Nutzerin, etwa mit einem falschen Link, verhindert es nicht.
</details>

**Least Privilege skizzieren:** Ein produktiver LeineTech-Agent bräuchte mehr
Tools, etwa Ticket schließen, Mail senden oder Konto zurücksetzen. Skizziert für
jedes: lesend oder schreibend? umkehrbar? Darf der Agent es allein ausführen, oder
braucht es eine Freigabe?

<details>
<summary>Eine mögliche Einteilung</summary>

| Tool | Wirkung | Autonomie |
|---|---|---|
| `kb_search`, `triage_ticket` | nur lesen | autonom |
| `escalate_to_human` | Übergabe an einen Menschen | autonom |
| `close_ticket` | schreibend, umkehrbar | autonom nur bei Priorität niedrig |
| Mail an Nutzerin senden | schreibend, nicht umkehrbar | nach Freigabe oder mit Vorlage |
| `reset_account` | schreibend, sicherheitskritisch | nie ohne Freigabe (Erweiterung B) |

Faustregel: Je irreversibler die Aktion, desto eher braucht sie eine Freigabe.
</details>

> **✓ Checkpoint 4:** `python -m pytest tests/test_agent_graph.py -q` meldet
> `15 passed`. Eure Messtabelle ist ausgefüllt, und ihr könnt begründen, bei
> welchem Ticket der Agent falsch lag.

---

## Bonus: Erweiterungen (frei wählbar)

Niemand muss alles schaffen. Kombinieren ist erlaubt. Der Code unten ist mit
einem Skript-Modell geprüft und läuft auf dem Stand nach Schritt 4.

| | Aufgabe | Niveau | Bezug zu VL 7 |
|---|---|---|---|
| A | Antwort-Review: Eine zweite LLM-Instanz prüft den Entwurf | mittel | Evaluator-Optimizer, bedingte Kante |
| B | Freigabe-Tools: `reset_account` nur nach menschlicher Freigabe | schwer | Human-in-the-Loop mit `interrupt()` |
| C | A2A skizzieren: der Eskalations-Agent als eigener Service | Konzept | Agent Card, Task Lifecycle |
| D | Memory: frühere Lösungen wiederverwenden | für Schnelle | episodisches Memory |

### A: Antwort-Review (Evaluator-Optimizer)

Ein zweiter LLM-Aufruf bewertet den Entwurf, bevor er rausgeht. Ist der Score
unter 7, bekommt der Agent das Urteil als Feedback und überarbeitet. Der Zähler
`reviews` ist das Step-Limit dieser Schleife.

```text
START → agent ⇄ tools
        agent → review → [Score ≥ 7 oder 2 Reviews] → END
                review → [sonst, mit Feedback] → agent
```

Ergänzt in `src/agent.py`:

```python
import re                                  # zu den Importen

from src.llm import chat                   # chat zum bestehenden Import aus src.llm ergänzen

class TicketAgentState(TypedDict):
    # messages und ticket_id bleiben wie bisher
    reviews: int                           # neu: Anzahl der Überarbeitungen

MAX_REVIEWS = 2  # Step-Limit der Review-Schleife

REVIEW_PROMPT = (
    "Du prüfst Antworten des LeineTech-Supports. Bewerte die Antwort von 1 bis 10 "
    "nach Korrektheit, Bezug zur Wissensbasis und Ton. Antworte in einer Zeile im "
    "Format 'Score: <Zahl>. <ein Satz, was besser werden muss>'.\n\n"
    "{ticket}\n\nAntwort:\n{entwurf}"
)


def review_node(state: TicketAgentState) -> dict:
    """Evaluator: Eine zweite LLM-Instanz prüft den Entwurf und gibt Feedback."""
    ticket = state["messages"][0].content
    entwurf = _content_text(state["messages"][-1].content)
    urteil = chat(REVIEW_PROMPT.format(ticket=ticket, entwurf=entwurf))
    treffer = re.search(r"\d+", urteil)
    score = int(treffer.group()) if treffer else 0  # das Format wird nicht immer eingehalten
    reviews = state.get("reviews", 0)
    if score < 7 and reviews < MAX_REVIEWS:
        feedback = HumanMessage(f"Überarbeite deine Antwort. Review: {urteil}")
        return {"messages": [feedback], "reviews": reviews + 1}
    return {}  # gut genug oder Limit erreicht: Der Entwurf geht raus


def after_review(state: TicketAgentState) -> Literal["agent", "__end__"]:
    """Hat der Review Feedback geschrieben? Dann überarbeitet agent den Entwurf."""
    return "agent" if isinstance(state["messages"][-1], HumanMessage) else END
```

Verdrahtung: `route()` liefert `"review"` statt `END` (auch im Rückgabetyp
`Literal[...]`). In `build_agent()` ersetzt ihr die bedingte Kante nach `agent`
und ergänzt den Review-Node:

```python
graph.add_node("review", review_node)
graph.add_conditional_edges(
    "agent", route, {"tools": "tools", "step_limit": "step_limit", "review": "review"}
)
graph.add_conditional_edges("review", after_review, {"agent": "agent", END: END})
```

**`recursion_limit` auf 16 anheben.** Mit Review braucht ein Lauf mehr
Supersteps, im schlimmsten Fall 14: acht für vier Tool-Runden, sechs für drei
Antworten mit je einem Review. Mit `recursion_limit=12` bricht LangGraph schon
einen Lauf mit drei Tool-Runden und drei Reviews (zwölf Supersteps) mit
`GraphRecursionError` ab, und `handle_ticket()` eskaliert das Ticket. Deshalb:

```bash
python -m src.agent T-1006 --trace --recursion-limit 16
```

Im Code entspricht das `handle_ticket(ticket, recursion_limit=16)`.

Mit `--trace` seht ihr die neue Schleife als Zeile `review human → Überarbeite …`.
Beobachtet: Wird die zweite Fassung wirklich besser? Ein Score ohne Begründung
hilft dem Agenten kaum. Deshalb schickt der Reviewer einen Satz Feedback mit.

### B: Freigabe-Tools mit Human-in-the-Loop

Ein produktiver Agent braucht mehr Tools, aber nach Least Privilege (VL 6).
`close_ticket` darf er allein ausführen, aber nur bei Priorität niedrig. Diese
Regel prüft der Code, nicht das LLM. `reset_account` läuft nie ohne Freigabe:
`interrupt()` pausiert den Graphen, bis ein Mensch antwortet. Dafür braucht der
Graph einen Checkpointer, der den Zwischenstand speichert, und eine `thread_id`,
unter der er ihn wiederfindet.

Ergänzt in `src/agent_tools.py`:

```python
from src.ticket_loader import get_ticket    # zu den Importen


def reset_account(user: str) -> str:
    """Setzt ein gesperrtes Konto zurück. Läuft erst nach menschlicher Freigabe.

    Args:
        user: Benutzername im Format vorname.nachname.
    """
    from langgraph.types import interrupt  # hier importieren: Tools bleiben ohne LangGraph testbar

    antwort = interrupt(f"Konto {user} zurücksetzen? (ja/nein)")  # pausiert den Graphen
    if str(antwort).strip().lower() != "ja":
        return f"Abgelehnt: Konto {user} bleibt unverändert."
    return f"Konto {user} zurückgesetzt."  # der Seiteneffekt kommt erst nach der Freigabe


CLOSED_TICKETS: set[str] = set()


def close_ticket(ticket_id: str) -> str:
    """Schließt ein Ticket. Der Agent darf nur Tickets mit Priorität niedrig schließen.

    Args:
        ticket_id: ID des Tickets, z. B. "T-1027".
    """
    ticket = get_ticket(ticket_id)
    if ticket is None:
        return f"Ticket {ticket_id} nicht gefunden."
    _, prioritaet = classify_and_prioritize(ticket)  # die Regel prüft der Code, nicht das LLM
    if prioritaet != "niedrig":
        return f"Abgelehnt: {ticket_id} hat Priorität {prioritaet}. Das entscheidet ein Mensch."
    CLOSED_TICKETS.add(ticket_id)  # idempotent: ein zweiter Aufruf ändert nichts
    return f"Ticket {ticket_id} geschlossen."


AGENT_TOOLS = [kb_search, triage_ticket, escalate_to_human, close_ticket, reset_account]
```

Ergänzt im Systemprompt in `src/agent.py` einen Satz wie: „Ist ein Konto gesperrt,
schlage reset_account vor. Ein Mensch gibt die Aktion frei.“

Mit `interrupt()` startet ihr den Agenten über ein eigenes kleines Skript
`freigabe.py` im Projektordner, nicht über `python -m src.agent`:

```python
"""Erweiterung B: Der Agent pausiert vor reset_account, bis ein Mensch freigibt."""
import sys

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from src.agent import build_agent, initial_state
from src.agent_tools import injection_check
from src.ticket_loader import get_ticket

ticket = get_ticket(sys.argv[1] if len(sys.argv) > 1 else "T-1009")
if injection_check(ticket["betreff"], ticket["text"]):
    raise SystemExit("Vorabprüfung schlägt an. Das Ticket geht direkt an einen Menschen.")

agent = build_agent(checkpointer=InMemorySaver())  # speichert den Zwischenstand
config = {"configurable": {"thread_id": ticket["id"]}, "recursion_limit": 12}

result = agent.invoke(initial_state(ticket), config)
while "__interrupt__" in result:  # der Graph wartet auf eine Entscheidung
    frage = result["__interrupt__"][0].value
    result = agent.invoke(Command(resume=input(f"FREIGABE: {frage} ")), config)
print(result["messages"][-1].content)
```

```bash
python freigabe.py T-1009
```

Erwartet, wenn das Modell `reset_account` vorschlägt:

```text
FREIGABE: Konto <benutzer> zurücksetzen? (ja/nein) ja
<finale Antwort des Agenten>
```

Beobachtet und diskutiert:

- Nach `Command(resume=…)` läuft der **ganze** `tools`-Node noch einmal, also auch
  andere Tool-Calls derselben Runde. Ruft das Modell vor `reset_account` noch
  `escalate_to_human` auf, steht die Eskalation danach doppelt in der Liste.
  Seiteneffekte gehören deshalb hinter `interrupt()`, und Tools mit Seiteneffekt
  sollten idempotent sein.
- `close_ticket("T-1024")` schließt das Ticket, denn die Regel-Triage sagt
  „niedrig“. Laut Soll ist es „hoch“. Eine Freigaberegel ist nur so gut wie die
  Einstufung, auf der sie beruht.

### C: A2A skizzieren (Konzept, ohne Code)

Stellt euch den Eskalations-Spezialisten als eigenen Agenten vor, den unser
Triage-Agent über A2A beauftragt. Skizziert:

- die **Agent Card** (`/.well-known/agent-card.json`) im Format A2A 1.0 wie in
  VL 7: `name`, `description`, `supportedInterfaces` (je Endpunkt `url`,
  `protocolBinding` und `protocolVersion`, ersetzt das frühere Feld `url` auf
  oberster Ebene), `skills` mit `tags` (welche Aufgaben nimmt er an?),
  `securitySchemes` plus `securityRequirements` (welche Verfahren gibt es, welches
  wird verlangt, und wie authentifiziert sich unser Agent?).
- den **Task Lifecycle** einer Eskalation: `submitted` → `working` →
  `input-required`, `completed` oder `failed`, dazu `canceled`, `rejected` und
  `auth-required` wie in VL 7. Wann ginge der Task in `input-required`, und wer
  antwortet dann?
- Was würde aus `escalate_to_human`? Welche Daten dürfen die Grenze zum anderen
  Agenten überschreiten?

### D: Memory (für Schnelle)

Merkt euch gelöste Tickets in einem Dictionary (Ticket-ID, KB-Abschnitt,
Antwort). Gebt dem Agenten vor dem ersten LLM-Aufruf ähnliche frühere Lösungen
als zusätzliche Nachricht mit. Leitfragen: Welcher Memory-Typ aus VL 7 ist das?
Wann schadet Memory, zum Beispiel bei einer veralteten Lösung oder bei
personenbezogenen Daten im Verlauf?

---

## Austausch im Plenum (10 min)

- Welche Aufgabe habt ihr gewählt, und wie weit seid ihr gekommen?
- Bei welchem Ticket hat euer Agent gut entschieden, bei welchem nicht, und warum?

<details>
<summary>Wann lohnt ein Agent gegenüber der festen Pipeline aus VL 3?</summary>

Wenn die Schrittfolge vorher nicht feststeht. Lässt sich der Ablauf als Flowchart
aufschreiben, reicht eine Pipeline oder ein Workflow mit Router (Verzweigung im
Code). Mehr Freiheit bringt mehr Fehlerquellen. Deshalb gilt: einfach anfangen und Komplexität erst
hinzufügen, wenn sie nötig ist.
</details>

<details>
<summary>Wie testet man etwas Nicht-Deterministisches?</summary>

In Schichten: Tools deterministisch testen (`tests/test_agent_tools.py`), die
Verdrahtung mit einem Skript-Modell testen (`tests/test_agent_graph.py`) und den
Agenten als Ganzes gegen Soll-Labels evaluieren, wie das Golden Dataset in VL 3.
</details>

<details>
<summary>Wie misst man Agenten-Qualität jenseits von „läuft durch“?</summary>

Zum Beispiel: Hat er das richtige Tool gewählt? Eskaliert er zu oft oder zu
selten (eure Tabelle aus 4c)? Wie viele LLM-Aufrufe und Tokens braucht er pro
Ticket? Stimmt der KB-Bezug der Antwort?
</details>

---

## Musterlösung ansehen

```bash
git show origin/vl08-agent:src/agent.py                   # ansehen, ohne den Branch zu wechseln
diff src/agent.py <(git show origin/vl08-agent:src/agent.py)   # eure Fassung vergleichen (bash, zsh)
```

Wer den Branch wechseln will, muss vorher die eigenen Änderungen sichern. Das
selbst angelegte `src/agent.py` blockiert sonst den Checkout.

```bash
git stash -u                  # eigene Änderungen inklusive neuer Dateien beiseitelegen
git checkout vl08-agent       # Musterlösung
git checkout vl06-guardrails  # zurück
git stash pop                 # eigene Änderungen zurückholen
```

---

## Vorbereitung auf VL 9

Installiert alles vor dem Termin, dann beginnt das VL-9-Lab ohne Wartezeit.

- Branch `vl09-oracle` holen. Eigene Änderungen vorher mit `git stash -u` sichern,
  denn das selbst angelegte `src/agent.py` ist ungetrackt.
- `pip install -r requirements.txt` auf `vl09-oracle` ausführen.
- opencode installieren und `opencode --version` prüfen.
- opencode nach `SETUP.md` einrichten (Abschnitt „opencode (ab VL 9)“). Die Config
  liest den Key über `{env:HOMECLOUD_API_KEY}`.
- Euren HomeCloud-Key in `HOMECLOUD_API_KEY` setzen. Es ist derselbe Key wie bisher,
  nur in einer anderen Variable als `LLM_API_KEY`.

---

## Troubleshooting

| Problem | Ursache und Lösung |
|---|---|
| `ModuleNotFoundError: No module named 'langgraph'` oder `'langchain_litellm'` | Abhängigkeiten fehlen. `pip install -r requirements.txt` in der richtigen Umgebung ausführen. |
| `No module named src.agent` | Das Gerüst ist noch nicht kopiert (Schritt 2). Befehle im Projektordner starten, nicht in `src/`. |
| `NotImplementedError: TODO 1: agent_node` (oder TODO 2) | Das TODO ist noch offen. |
| `ValueError: Graph must have an entrypoint …` | TODO 3: Die Kante von `START` zu `agent` fehlt. |
| `ValueError: … 'route' branch found unknown target 'step_limit'` | Die Path-Map bei `add_conditional_edges` fehlt. Gebt sie wie im Hinweis zu TODO 3 an. |
| `KeyError: '__end__'` | In der Path-Map fehlt der Eintrag `END: END`. |
| Die „Antwort“ ist ein KB-Auszug oder `Kategorie: …` | Die Rückkante `tools → agent` fehlt. Der Graph endet nach dem Tool. |
| `litellm.Timeout` beim ersten Aufruf (etwa bei `chat('Sag Moin.')`) | Kaltstart. Befehl wiederholen oder `export LLM_TIMEOUT=360` setzen. |
| Der Agent hängt bei der ersten Anfrage minutenlang | Kaltstart des Endpunkts (bis 300 s). Warten. Meldungen wie `Retrying … in 4.0 seconds` sind dann normal, das ist der eingebaute Backoff (`MAX_RETRIES`). |
| `PermissionDeniedError` oder HTTP 403 | Außerhalb des Zeitfensters (montags 06:00 bis 23:59) ist der Key gesperrt. Im Fenster erneut versuchen. Bis dahin offline weiterarbeiten (siehe letzte Zeile). |
| `AuthenticationError` oder HTTP 401 | `LLM_API_KEY` fehlt oder ist falsch. |
| Der Agent ruft nie ein Tool auf | Ein nicht tool-fähiges Modell ist gesetzt. `LLM_MODEL` leeren, der Default `qwen3.6-35B-A3B-FP8` kann Tools. |
| Die Antwort hat keinen KB-Bezug | Das Modell hat `kb_search` übersprungen. Im Trace nachsehen, dann den Systemprompt schärfen. |
| Graph-Tests nach Schritt 4b rot (`assert 'step_limit' == 'tools'`) | `MAX_TOOL_RUNDEN` steht noch auf dem Demo-Wert `0`. Zurück auf `4` setzen. |
| Eskalation mit „recursion_limit=12 erreicht“ bei einem normalen Ticket | Das Modell ruft Tools in einer Schleife. Mit TODO 4 greift vorher das Step-Limit. Mit Erweiterung A (Review) sind bis zu 14 Supersteps nötig: `recursion_limit` auf 16 anheben (`--recursion-limit 16`). |
| `error: The following untracked working tree files would be overwritten by checkout: src/agent.py` | Beim Branchwechsel. Musterlösung per `git show` ansehen oder vorher `git stash -u`. |
| Tests sind nach Schritt 4a rot | Der Patch in 4a gilt nur im Python-Prozess. Wer stattdessen `src/agent_tools.py` geändert hat, stellt die Datei mit `git restore src/agent_tools.py` wieder her. |
| Endpunkt ganz ausgefallen (Plan B) | Der Abschnitt „Plan B“ in `SETUP.md` nennt keinen Ersatz-Endpunkt mit Zusage. Der lokale Weg über Ollama taugt für den Agenten nicht, denn ein 1,5-B-Modell ruft Tools zu unzuverlässig auf. Offline weiter: Schritt 1, die Graph-Tests in Schritt 2 und der Test in Schritt 4b. Die Läufe gegen den Endpunkt holt ihr im nächsten Zeitfenster nach. Nur erfundene Ticketdaten senden. |
