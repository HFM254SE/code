# FHDW — Automatisierung im Software Engineering (Q3 2026) · Code

Hands-on **Lab-Code** für den Lehrauftrag „Automatisierung im Software
Engineering" (FHDW Hannover, Juli–September 2026).

📋 Planung: [Confluence — FHDW Vorlesung Q3 2026](https://nortal.atlassian.net/wiki/spaces/DESS/pages/1461945047/FHDW+Vorlesung+Q3+2026)
🖥️ Folien liegen im separaten **`slides`**-Repository.

## Das Kursprojekt: LeineTech Ticket-Triage („roter Faden")

Statt isolierter Beispiele wächst über das Semester **ein** System: das
interne **Support-Ticket-System der LeineTech GmbH** (fiktiver IT-Dienstleister,
Hannover, ~200 Mitarbeitende). Jede Vorlesung baut darauf auf:

| VL | Erweiterung | Schwerpunkt |
|----|-------------|-------------|
| 1 | Bestehendes (absichtlich schlechtes) Triage-Tool verbessern | pylint, flake8, Trivy, Cursor/Copilot |
| 2 | Tickets per Prompt klassifizieren (Browser, ohne Code) | Zero-/Few-Shot, CoT |
| 3 | LLM-Anschluss über lokales Modell + Evaluierung | Ollama, OpenAI SDK, Golden Dataset |
| 4–5 | RAG-Chatbot über die LeineTech-Knowledge-Base (`docs/`) | ChromaDB, Embeddings (Sven) |
| 6 | Das eigene System angreifen und absichern | Prompt Injection (Easter Egg in den Tickets!), Guardrails |
| 7–8 | Triage zum Tool-nutzenden Agenten ausbauen | LangGraph, MCP |
| 9 | Spec-Driven Development am Projekt | OpenAPI, CLAUDE.md |
| 10 | Fallstudie: Einordnung nach EU AI Act | — |

Das Szenario spiegelt bewusst die Klausur-Anwendungsaufgaben
(Support-Ticket-Agent, interner Chatbot für ein 200-MA-Unternehmen).

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

## Für Lehrende: Branches bauen

Die Branch-Inhalte werden auf `main` unter `common/` (geteilte Daten/Docs)
und `steps/<checkpoint>/` (Code-Stände) gepflegt. Daraus baut

```bash
./scripts/create-step-branches.sh
git push -f origin vl01-start vl01-solution vl03-llm-client vl03-evaluation \
                   vl06-guardrails vl08-agent vl09-spec
```

die Checkpoint-Branches als lineare Historie (Diffs zwischen Checkpoints
zeigen genau den Lernschritt). Commits/Pushes ausschließlich durch Menschen.
