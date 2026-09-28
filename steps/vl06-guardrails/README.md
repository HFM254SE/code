# LeineTech Ticket-Triage: `vl06-guardrails`

Musterlösung des **Labs in VL 6**. Die LLM-Pipeline aus VL 3 wird angegriffen
(T-1030, das Prompt-Injection-Easter-Egg aus dem Datensatz) und danach gehärtet.
Die Anleitung steht in `labs/vl06-lab.md`. Das Lab startet nicht auf diesem
Branch, sondern auf `vl03-evaluation` und holt sich von hier nur das Lab-Material.

> Hinweis für Lehrende: Dieser Ordner enthält den vollständigen Code-Stand
> (`src/`, `tests/`, `eval/injections.jsonl`, `labs/`). Daten und Knowledge Base
> (`data/`, `docs/`, `eval/golden.jsonl`) kommen beim Zusammenbauen aus `common/`.
> Lauffähig ist der Stand erst im zusammengebauten Branch, für Studierende via
> `git switch vl06-guardrails`.

## Die Schichten im Code

Die Nummern folgen dem Modell aus der Vorlesung (Defense in Depth).

| Schicht | Wo im Code | Was passiert |
|---|---|---|
| 1 Input-Validierung | `src/guardrails.py`: `scan_text`, `scan_ticket` | Bekannte Injection-Muster erkennen. Bewusst **unvollständig**: Umschreibung und Fremdsprache rutschen durch (INJ-10, INJ-11). |
| 2 Robuster System Prompt | `src/summarize.py`: `SECURITY_RULES`, `_als_daten` | Nicht verhandelbare Regeln. Das ganze Ticket steht als Daten zwischen `<<<TICKET` und `TICKET>>>`, Markierungszeichen im Ticket werden entschärft. |
| 3 Guardrails und Output-Validierung | `src/guardrails.py`: `filter_output`. `src/summarize.py`: `_parse_classification` | E-Mail, IBAN und API-Keys in Antworten maskieren. Die Klassifikation lässt nur erlaubte Werte durch. |
| 4 Least Privilege und HITL | `src/main.py`: `cmd_classify` | Ein Ergebnis mit `injection_verdacht` wird für die menschliche Review markiert. |
| 5 Monitoring | fehlt noch | Die Folien zeigen am Beispiel Langfuse, wie es ginge. |

## Neu gegenüber `vl03-evaluation`

- `src/guardrails.py`: Input-Scan (Schicht 1) und Output-Filter (Schicht 3).
- `src/summarize.py`: gehärteter Prompt (Schicht 2), Scan vor und Filter nach dem LLM-Aufruf.
- `src/main.py`: `scan` (Offline-Scan der 30 Tickets), `scan --angriffe [DATEI]`
  (Erkennungsrate, bewusste Lücken und False Positives messen) und `--text` für
  `classify` und `summarize` (eigene Angriffe testen, ohne `data/tickets.json` zu ändern).
- `eval/injections.jsonl`: 12 Angriffe. 10 sollen erkannt werden, 2 bewusst nicht.
- `tests/test_guardrails.py`: offline, gilt für Musterlösung und Lab-Gerüst
  (Erkennungsrate, False Positives, Output-Filter). Die zwei bewussten Lücken
  erscheinen als `xfailed`.
- `tests/test_haertung.py`: offline mit simuliertem LLM, nur für die Musterlösung
  (Datenmarkierung, IBAN, Format-Check, Review-Markierung, Kommandozeile).
- `labs/vl06-lab.md`, `labs/templates/guardrails_skeleton.py`: Anleitung und Gerüst.

Alles andere in `src/summarize.py` und `src/main.py` ist unverändert der Stand
aus VL 3: Few-Shot-Beispiele, `chat_with_usage` mit `CLASSIFY_MAX_TOKENS`,
`parse_fehler` beim Rückfall, Token-Anzeige, `main(argv)` mit `triage` als
Default. Der Diff unten zeigt deshalb nur die Härtung. Die Tests aus VL 3
(`tests/test_llm.py`, `tests/test_summarize.py`, `tests/test_main.py`,
`tests/test_evaluate.py`) liegen unverändert bei und laufen auch gegen die
gehärtete Fassung.

**Außerdem enthalten (Vorbereitung für VL 8):** Das Lab in VL 8 startet von
diesem Branch. Dafür liegen hier schon `src/agent_tools.py`,
`src/knowledge_base.py`, `labs/vl08-lab.md`, `labs/templates/agent_skeleton.py`
und die Tests `tests/test_agent_tools.py`, `tests/test_knowledge_base.py` und
`tests/test_agent_graph.py`. `tests/test_agent_graph.py` wird übersprungen, bis
`src/agent.py` existiert (Lab VL 8, Schritt 2). Deshalb meldet `pytest` hier
genau einen `skipped`.

**Nicht enthalten:** die RAG-Module aus VL 4/5 (`chunker.py`, `embedder.py`,
`vectorstore.py`, `rag.py` usw.). VL 6 baut auf der Triage aus VL 3 auf.

## Ausführen

```bash
python -m src.main scan                       # offline: nur T-1030 ist auffällig
python -m src.main scan --angriffe            # offline: 10 von 10, 2 von 2, 0 von 29
python -m src.main classify T-1030            # mit LLM: Verdacht wird gemeldet
python -m pytest -q tests/test_guardrails.py tests/test_haertung.py   # offline
```

Vergleich vorher und nachher (das ist der Lerneffekt):

```bash
git switch vl03-evaluation
python -m src.main classify T-1030            # ungehärtet: LLM stuft evtl. "niedrig" ein
git switch vl06-guardrails
python -m src.main classify T-1030            # gehärtet: Verdacht markiert, Review
git diff vl03-evaluation vl06-guardrails -- src/summarize.py
```

**Diskussionsstoff:** Der Scanner erkennt alle 10 erwarteten Angriffe des
Testsets, aber kaum neue Formulierungen (Held-out-Runde im Lab). Warum ist
Pattern-Matching allein keine Lösung? Warum hängt die Review in diesem Stand
trotzdem allein am Scanner, und welcher zweite Auslöser wäre unabhängig davon?

> Hier endet der Stand von VL 6. Ab VL 7/8 wird aus der Pipeline ein
> Tool-nutzender Agent mit der Knowledge Base aus `docs/` und einer
> Eskalationsfunktion.
