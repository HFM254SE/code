# FHDW — Code zur Vorlesung Automatisierung im Software Engineering (Q3 2026) 

Hands-on **Lab-Code**

## Das Kursprojekt: LeineTech Ticket-Triage („roter Faden")

Über alle Vorlesungen hinweg wird am gleichen System gearbeitet: dem
internen **Support-Ticket-System der LeineTech GmbH** (fiktiver IT-Dienstleister,
Hannover, ~200 Mitarbeitende).

| VL | Erweiterung | Schwerpunkt |
|----|-------------|-------------|
| 1 | Bestehendes Triage-Tool verbessern | pylint, flake8, Trivy, Cursor/Copilot |
| 2 | Tickets per Prompt klassifizieren (Browser, ohne Code) | Zero-/Few-Shot, CoT |
| 3 | LLM-Anschluss über lokales Modell + Evaluierung | Ollama, OpenAI SDK, Golden Dataset |
| 4–5 | RAG-Chatbot über die LeineTech-Knowledge-Base (`docs/`) | ChromaDB, Embeddings |
| 6 | Das eigene System angreifen und absichern | Prompt Injection, Guardrails |
| 7–8 | Triage zum Tool-nutzenden Agenten ausbauen | LangGraph, MCP |
| 9 | Spec-Driven Development am Projekt | OpenAPI, CLAUDE.md |
| 10 | Fallstudie: Einordnung nach EU AI Act | — |


## Checkpoint-Branches

Jeder Lab-Zustand ist ein Branch — wer hängen bleibt oder eine Session
verpasst, steigt einfach wieder ein:

```
git checkout vl01-start        # VL 1: das "schlechte" Tool (Lab-Start)
git checkout vl01-solution     # VL 1: Musterlösung = Start für VL 3
git checkout vl03-llm-client   # VL 3: LLM-Anschluss über Ollama fertig
git checkout vl03-evaluation   # VL 3: Evaluierung Regeln vs. LLM fertig
git checkout vl06-guardrails   # VL 6: Injection-Scanner + Output-Filter
git checkout vl08-agent        # VL 8: Tool-nutzender LangGraph-Agent
git checkout vl09-spec         # VL 9: OpenAPI-Spec + Drift-Prüfung
```

Jeder Branch ist **vollständig** (Code + Daten + Docs + Lab-Anleitung in
`labs/`) und die Anleitungen funktionieren auch ohne Vorlesung zum Nacharbeiten.
(VL 2, 4–5, 7, 10 haben keinen eigenen Code-Branch: VL 2 ist browserbasiert,
VL 4/5 sind Svens separater RAG-Workshop, VL 7 und 10 sind Theorie/Fallstudie.)

## Inhalt eines Checkpoints

```
data/tickets.json    30 Support-Tickets der LeineTech GmbH (Mai 2026)
docs/                Knowledge-Base der LeineTech-IT (8 Artikel) → RAG-Korpus ab VL 4
eval/golden.jsonl    Menschliche Soll-Labels für alle 30 Tickets
src/                 Das Triage-Tool im jeweiligen Ausbauzustand
tests/               pytest — Sicherheitsnetz bei (KI-)Refactorings
labs/                Schritt-für-Schritt-Lab-Anleitungen
SETUP.md             Kurs-LLM-Endpunkt (Nirk HomeCloud) + Groq-Fallback einrichten
```

