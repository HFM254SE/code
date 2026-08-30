# FHDW — Code zur Vorlesung Automatisierung im Software Engineering (Q3 2026) 

Hands-on **Lab-Code**

## Das Kursprojekt: LeineTech Ticket-Triage („roter Faden")

Über alle Vorlesungen hinweg wird am gleichen System gearbeitet: dem
internen **Support-Ticket-System der LeineTech GmbH** (fiktiver IT-Dienstleister,
Hannover, ~200 Mitarbeitende).

| VL | Erweiterung | Schwerpunkt |
|----|-------------|-------------|
| 1 | Bestehendes Triage-Tool verbessern | pylint, flake8, Trivy, VS Code + Continue.dev (HomeCloud) |
| 2 | Tickets per Prompt klassifizieren (Browser, ohne Code) | Zero-/Few-Shot, CoT |
| 3 | LLM-Anschluss über den Kurs-Endpunkt + Evaluierung | HomeCloud (litellm), Golden Dataset |
| 4–5 | RAG-Chatbot über die LeineTech-Knowledge-Base (`docs/`) | ChromaDB, Embeddings (Sven, in Arbeit) |
| 6 | Das eigene System angreifen und absichern | Prompt Injection, Guardrails |
| 7–8 | Triage zum Tool-nutzenden Agenten ausbauen | LangGraph, MCP |
| 9 | Spec-Driven Development am Projekt | OpenAPI, CLAUDE.md |
| 10 | Fallstudie: Einordnung nach EU AI Act | — |


## Checkpoint-Branches

Jeder Lab-Zustand ist ein Branch — wer hängen bleibt oder eine Session
verpasst, steigt einfach wieder ein:

```
git checkout vl01-start                           # VL 1: das "schlechte" Tool (Lab-Start)
git checkout vl01-solution                        # VL 1: Musterlösung = Start für VL 3
git checkout vl03-llm-client                      # VL 3: LLM-Anschluss über den Kurs-Endpunkt fertig
git checkout vl03-evaluation                      # VL 3: Evaluierung Regeln vs. LLM fertig
git checkout vl04-rag-ingestion-pipeline-start    # VL 4: Startpunkt für das RAG Ingestion Pipeline Lab
git checkout vl04-rag-ingestion-pipeline-solution # VL 4: Musterlösung für VL 4
git checkout vl05-rag-advanced-start              # VL 5: Startpunkt für die RAG Advanced Lab
git checkout vl05-rag-advanced-solution           # VL 5: Musterlösung für VL 5
git checkout vl06-guardrails                      # VL 6: Injection-Scanner + Output-Filter
git checkout vl08-agent                           # VL 8: Tool-nutzender LangGraph-Agent
git checkout vl09-oracle                          # VL 9: Mutation Testing + Spec Driven Development
```

Jeder Branch ist **vollständig** (Code + Daten + Docs + Lab-Anleitung in
`labs/`) und die Anleitungen funktionieren auch ohne Vorlesung zum Nacharbeiten.
(VL 2, 7, 10 haben keinen eigenen Code-Branch: VL 2 ist browserbasiert,
VL 7 und 10 sind Theorie/Fallstudie. **VL 4/5 (RAG, Sven):** Der Lab-Code
liegt in den Branches `vl04-rag-ingestion-pipeline-start` (Lab-Start) und
`vl04-rag-ingestion-pipeline-solution` (Musterlösung = Start für VL 5) und
baut auf `vl03-evaluation` auf; die Anleitung steht in `labs/vl04-lab.md`.
Die Folien liegen im separaten `slides`-Repo.)

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

