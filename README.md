# FHDW — Automatisierung im Software Engineering (Q3 2026) · Code

Hands-on **lab / exercise code** for the FHDW Hannover lectureship
„Automatisierung im Software Engineering" (Q3 2026).

📋 Planning: [Confluence — FHDW Vorlesung Q3 2026](https://nortal.atlassian.net/wiki/spaces/DESS/pages/1461945047/FHDW+Vorlesung+Q3+2026)
🖥️ Slides live in the separate **`slides`** repository.

## Concept — one "roter Faden" project

Instead of isolated per-lecture examples, the course builds **one shared
project** that grows across the semester. Each lecture extends the same system:

| VL | Erweiterung | Stack-Schwerpunkt |
|----|-------------|-------------------|
| 1 | Bestehendes Python-Projekt mit Linter/Copilot verbessern | pylint, flake8, Cursor/Copilot |
| 3 | Lokales Modell per Ollama als OpenAI-kompatible API bereitstellen | Ollama, OpenAI SDK |
| 4–5 | RAG-Chatbot auf dem Modell aufbauen | Python · LlamaIndex · Ollama · Qdrant · Streamlit |
| 6 | Den eigenen Chatbot angreifen und absichern | Prompt Injection, Guardrails |
| 7–8 | Chatbot zu einem Tool-nutzenden Agenten erweitern | LangGraph · Ollama · MCP |
| 9 | Spec-Driven Development anwenden | OpenAPI · CLAUDE.md |
| 10 | Fallstudie: Projekt nach EU AI Act einordnen | — |

## Guided-lab branches

Guided labs are checkpointed as numbered branches/tags so students who fall
behind can `git checkout step-0X` and rejoin, e.g.:

```
step-01-setup   step-02-api-call   step-03-comparison
step-04-ingest  step-05-retrieval  step-06-qa-pipeline
step-07-mcp-server  step-08-multi-step  step-09-error-handling
```

Each lab also ships a Markdown walkthrough in the repo (not only on the slides)
so it can be redone independently.

> Status: scaffolding. Lab code is added per lecture as the course progresses.
