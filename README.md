# FHDW: Code zur Vorlesung „Automatisierung im Software Engineering“ (Q3 2026)

Hands-on-**Lab-Code** zur Vorlesung. Die Folien liegen im separaten `slides`-Repo.

## Das Kursprojekt: LeineTech Ticket-Triage („roter Faden“)

Über alle Vorlesungen hinweg arbeiten wir am selben System: dem internen
**Support-Ticket-System der LeineTech GmbH** (fiktiver IT-Dienstleister, Hannover,
ca. 200 Mitarbeitende).

| VL | Erweiterung | Schwerpunkt | Checkpoints |
|----|-------------|-------------|-------------|
| 1 | Bestehendes Triage-Tool verbessern | pylint, flake8, Trivy, VS Code mit Continue.dev (HomeCloud) | `vl01-start` → `vl01-solution` |
| 2 | Tickets per Prompt klassifizieren (Browser, ohne Code) | Zero-Shot, Few-Shot, Chain-of-Thought | – |
| 3 | LLM-Anschluss über den Kurs-Endpunkt und Evaluierung | litellm, Golden Dataset, Regeln gegen LLM messen | `vl03-llm-client`, `vl03-evaluation` |
| 4 | RAG-Ingestion-Pipeline über die Knowledge Base `docs/` (Sven Liebig) | Chunking, Embeddings, ChromaDB, Retrieval messen | `vl04-rag-ingestion-pipeline-start` → `-solution` |
| 5 | RAG-Client mit Quellen und hybrider Suche (Sven Liebig) | Kontext im Prompt, Enthaltung, RRF, Beleg-Treffer, LLM als Judge | `vl05-rag-advanced-start` → `-solution` |
| 6 | Das eigene System angreifen und absichern | Prompt Injection, Guardrails, OWASP Top 10 für LLMs | `vl06-guardrails` |
| 7–8 | Triage zum Tool-nutzenden Agenten ausbauen | LangGraph (MCP als Theorie in VL 7) | `vl08-agent` |
| 9 | Orakel und Spec-Driven Development am Projekt | Mutation Testing, OpenAPI, `AGENTS.md`, Schemathesis, opencode | `vl09-oracle` |
| 10 | Fallstudie: Einordnung nach EU AI Act | Risikoklassen, Pflichten, Fairness am eigenen Code | – (liest `vl09-oracle`) |

## Checkpoint-Branches

Jeder Lab-Zustand ist ein Branch. Wer hängen bleibt oder eine Session verpasst,
steigt dort wieder ein:

```
git checkout vl01-start                            # VL 1: das „schlechte“ Tool (Lab-Start)
git checkout vl01-solution                         # VL 1: Musterlösung, Start des Labs in VL 3
git checkout vl03-llm-client                       # VL 3: Teil 1 fertig (LLM-Anschluss)
git checkout vl03-evaluation                       # VL 3: Teil 2 fertig (Regeln gegen LLM), Start des Labs in VL 6
git checkout vl04-rag-ingestion-pipeline-start     # VL 4: Lab-Start mit Gerüsten
git checkout vl04-rag-ingestion-pipeline-solution  # VL 4: Musterlösung
git checkout vl05-rag-advanced-start               # VL 5: Lab-Start
git checkout vl05-rag-advanced-solution            # VL 5: Musterlösung
git checkout vl06-guardrails                       # VL 6: Musterlösung, Start des Labs in VL 8
git checkout vl08-agent                            # VL 8: Musterlösung (LangGraph-Agent)
git checkout vl09-oracle                           # VL 9: Lab-Start (Orakel, Spec-Driven)
```

Jeder Branch ist **vollständig** (Code, Daten, Knowledge Base, Tests und alle
bisherigen Lab-Anleitungen in `labs/`). Die Anleitungen funktionieren auch ohne
Vorlesung zum Nacharbeiten. VL 2, 7 und 10 haben keinen eigenen Code-Branch: VL 2
läuft im Browser, VL 7 ist Theorie, VL 10 ist eine Fallstudie.

Wo ein Lab startet, steht in seiner Anleitung. Die Übersicht:

| Lab | startet auf | Anleitung | Musterlösung |
|---|---|---|---|
| VL 1 | `vl01-start` | `labs/vl01-lab.md` | `vl01-solution` |
| VL 3 | `vl01-solution` | `labs/vl03-lab.md` (liegt schon auf `vl01-solution`) | `vl03-llm-client` (Teil 1), `vl03-evaluation` (Teil 2) |
| VL 4 | `vl04-rag-ingestion-pipeline-start` | `labs/vl04-lab.md` | `vl04-rag-ingestion-pipeline-solution` |
| VL 5 | `vl05-rag-advanced-start` | `labs/vl05-lab.md` | `vl05-rag-advanced-solution` |
| VL 6 | eigener Zweig ab `vl03-evaluation`, Lab-Material aus `vl06-guardrails` | `labs/vl06-lab.md` | `vl06-guardrails` |
| VL 8 | `vl06-guardrails` | `labs/vl08-lab.md` | `vl08-agent` |
| VL 9 | `vl09-oracle` | `labs/vl09-lab.md` | kein Branch, die Lösungen zu Teil 2 zeigt der Dozent am Beamer |

Inhaltlich bauen VL 4 und VL 5 auf `vl03-evaluation` auf. VL 6, VL 8 und VL 9
bauen ebenfalls auf `vl03-evaluation` auf und enthalten die RAG-Module aus VL 4
und VL 5 nicht. Die Anleitungen von VL 4 und VL 5 liegen dort trotzdem unter
`labs/`, weil jeder Branch alle bisherigen Anleitungen mitbringt. Ausführen lassen
sie sich nur auf den `vl04-` und `vl05-`Branches.

## Inhalt eines Checkpoints

```
data/tickets.json    30 Support-Tickets der LeineTech GmbH (Mai 2026)
docs/                Knowledge Base der LeineTech-IT (8 Artikel), RAG-Korpus ab VL 4
eval/golden.jsonl    Soll-Labels (Golden Dataset) für alle 30 Tickets
src/                 das Triage-Tool im jeweiligen Ausbauzustand
tests/               pytest, das Sicherheitsnetz bei (KI-)Refactorings, offline mit Attrappen
labs/                Lab-Anleitungen und Vorlagen aller bisherigen Vorlesungen
api/, tools/         ab VL 9: Ticket-API mit OpenAPI-Spec, Mutation-Dojo, Spec-Gate
SETUP.md             Kurs-LLM-Endpunkt (Nortal Nirk HomeCloud), Clients, Embeddings, Plan B
requirements.txt     gepinnte Abhängigkeiten des Checkpoints
conftest.py          macht src/ für pytest importierbar und blendet fremde Deprecation-Warnungen aus
```

## Für Lehrende: Aufbau dieses Repos

```
common/              Daten, Knowledge Base, Golden Set, SETUP.md, .gitignore, .gitattributes
steps/<checkpoint>/  vollständiger Code-Stand je Checkpoint (src/, tests/, labs/, requirements.txt, …)
scripts/steps.conf   Reihenfolge der Checkpoints
scripts/assemble-step.sh <step> <ziel>   baut einen Checkpoint zusammen
scripts/create-step-branches.sh          baut alle Branches (nur durch Menschen ausführen)
```

`assemble-step.sh` kopiert `common/`, dann die `labs/`-Ordner aller vorherigen
Steps und zuletzt den Ziel-Step. Nur `labs/` wird vererbt. Alles andere steht in
jedem Step vollständig.

**Pflegeregel:** Viele Dateien liegen als identische Kopie in mehreren Steps (etwa
`src/triage.py` in zehn Steps, `src/llm.py` in neun, `conftest.py` in allen elf).
Wer eine davon ändert, ändert alle identischen Kopien gleich und prüft vorher und
nachher mit `md5 -q`. Bewusste Abweichungen sind nur diese: `vl01-start` (absichtlich
schlechter Code und verwundbare Pins), die Gerüste in `vl04-rag-ingestion-pipeline-start/src/`,
`src/rag_eval.py` in `vl05-rag-advanced-start` (Judges als TODO) und die
`requirements.txt` je Step. Dateien, die ein Lab weiterentwickelt, beginnen dort eine
neue Kopie, etwa `src/main.py` in `vl01-solution`, `vl03-*` und ab `vl06-guardrails`
oder `src/summarize.py` ab `vl06-guardrails`. Verbesserungen an der älteren Fassung
gehören dann auch in die neuere, sonst dreht der spätere Checkpoint sie zurück.
Prüfen lässt sich das mit `diff steps/<vorgänger>/<datei> steps/<step>/<datei>`. Der
Diff soll nur zeigen, was das Lab des Steps neu einführt. Der Vorgänger von
`vl06-guardrails` ist inhaltlich `vl03-evaluation` (siehe `scripts/steps.conf`).

**Testen eines Checkpoints:**

```bash
./scripts/assemble-step.sh vl06-guardrails /tmp/build/vl06-guardrails
cd /tmp/build/vl06-guardrails && python3 -m pytest -q -p no:cacheprovider
```

Sollzustand (Stand 27.09.2026, offline, lokal mit Python 3.12):

| Checkpoint | `python3 -m pytest -q` |
|---|---|
| `vl01-start`, `vl01-solution` | 5 passed |
| `vl03-llm-client` | 35 passed |
| `vl03-evaluation` | 51 passed |
| `vl04-rag-ingestion-pipeline-start` | 28 failed, 5 passed (gewollt: jeder rote Test endet mit `NotImplementedError: TODO Teil …`) |
| `vl04-rag-ingestion-pipeline-solution` | 33 passed |
| `vl05-rag-advanced-start` | 33 passed, 3 skipped (gewollt: die Lab-Tests warten auf die Vorlagen) |
| `vl05-rag-advanced-solution` | 96 passed |
| `vl06-guardrails` | 98 passed, 1 skipped, 2 xfailed (Skip: Agent-Test für VL 8, xfail: bewusste Lücken des Scanners) |
| `vl08-agent` | 113 passed, 2 xfailed |
| `vl09-oracle` | 134 passed, 2 xfailed |

Die Branches baut ein Mensch nach jeder Änderung neu (`./scripts/create-step-branches.sh`,
danach die ausgegebene `git push -f`-Zeile). Didaktische Absichten des Datensatzes
und der Checkpoints (z. B. warum die Regel-Triage absichtlich danebenliegt) stehen
im `slides`-Repo unter `course/syllabus/roter-faden.md`, nicht hier. Diese Datei ist
die Startseite des öffentlichen Repos.
