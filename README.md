# LeineTech Ticket-Triage — `vl06-guardrails`

Endzustand des **Labs in VL 6**: Die LLM-Pipeline aus VL 3 wird **angegriffen**
(T-1030, das Prompt-Injection-Easter-Egg) und dann **gehärtet**.

Neu gegenüber `vl03-evaluation`:

- `src/guardrails.py` — zwei Verteidigungsschichten:
  - **Input-Scan** (`scan_text`/`scan_ticket`): bekannte Injection-Muster
    erkennen — bewusst **unvollständig** (Paraphrasen/Fremdsprachen rutschen
    durch, siehe `eval/injections.jsonl`).
  - **Output-Filter** (`filter_output`): PII und Secrets aus LLM-Antworten
    maskieren — LLM-Output ist Untrusted Input.
- `src/summarize.py` — gehärtet: Tickettext als Daten markiert (`<<<TICKET … TICKET>>>`),
  nicht verhandelbare Sicherheitsregeln im System-Prompt, Injection-Verdacht
  wird im Ergebnis markiert statt blind weiterverarbeitet.
- `src/main.py` — neues Subkommando `scan`.
- `eval/injections.jsonl` — 12 Angriffe (10 sollen erkannt werden, 2 bewusst
  nicht: Paraphrase + Fremdsprache).
- `tests/test_guardrails.py` — **offline** (kein LLM): Erkennungsrate UND
  False-Positive-Rate gegen die echten Tickets.

## Ausführen

```bash
python -m src.main scan                # Offline-Scan aller 30 Tickets → nur T-1030
python -m src.main classify T-1030     # mit Härtung: Verdacht wird gemeldet
python -m pytest tests/test_guardrails.py   # offline, ohne LLM
```

Vergleich vorher/nachher (das ist der Lerneffekt):

```bash
git checkout vl03-evaluation
python -m src.main classify T-1030     # ungehärtet: LLM stuft evtl. "niedrig" ein
git checkout vl06-guardrails
python -m src.main classify T-1030     # gehärtet: bleibt "hoch", Verdacht markiert
```

**Diskussionsstoff:** Der Scanner erkennt 10 von 12 Angriffen — die zwei
Lücken (Paraphrase, Suaheli) sind Absicht. Warum ist Pattern-Matching allein
keine Lösung? Warum braucht es zusätzlich Härtung im Prompt *und* einen
Output-Filter (Defense in Depth)?

> Hier endet der VL-6-Stand. Ab VL 7/8 wird aus der Pipeline ein
> **Tool-nutzender Agent** — mit der Knowledge Base aus `docs/` und einer
> Eskalations-Funktion.
