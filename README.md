# LeineTech Ticket-Triage — `vl09-oracle`

Ausgangszustand des **Labs in VL 9**: Testorakel und Spec-Driven Development
am eigenen Projekt. Erst messt ihr, wie wenig eine grüne Test-Suite prüft,
wenn ihre Erwartung aus dem Prüflings-Code stammt. Danach baut ihr ein Gate,
das eine Implementierung maschinell gegen [`api/openapi.yaml`](api/openapi.yaml) prüft — die
einzige Erwartung in diesem Repo, die außerhalb des Codes liegt, den sie
beurteilt.

Das Lab-Sheet ist [`labs/vl09-lab.md`](labs/vl09-lab.md). Anfangen bitte dort.

Neu gegenüber `vl08-agent`:

- [`api/openapi.yaml`](api/openapi.yaml) — OpenAPI-3.1-Spec der LeineTech Ticket-API
  (Tickets auflisten/anlegen/lesen, `triage`, `escalate`). **Single Source
  of Truth.**
- [`api/app.py`](api/app.py) — Referenz-Server (FastAPI), exakt spec-konform.
- [`api/drifted_server.py`](api/drifted_server.py) — weicht **absichtlich** ab, mit sechs Drifts, die
  im Lab-Sheet offen aufgelistet sind. Zielscheibe für Teil 2. Die Aufgabe
  ist nicht, die Abweichungen zu finden, sondern das Gate, das sie findet.
- [`tools/specyaml.py`](tools/specyaml.py) — YAML-Leser aus der Standardbibliothek (kein PyYAML).
  Löst bewusst **kein `$ref`** auf — das wird in der Vertiefung zum Thema.
- [`tools/spec_gate.py`](tools/spec_gate.py) — Gerüst für das Konformitäts-Gate, sechs TODOs.
- [`tools/mutation_dojo.py`](tools/mutation_dojo.py) — Mutation-Testing für [`src/triage.py`](src/triage.py), misst die
  Suiten aus `tests/`. Enthält selbst keine Tests und keine Erwartungen.
- [`tests/test_triage_oracle.py`](tests/test_triage_oracle.py) — Gerüst für Teil 1, drei TODOs.
- [`tests/test_openapi_spec.py`](tests/test_openapi_spec.py) — offline: Spec self-consistent + Kategorie-Enum
  passt zu den Triage-Regeln (genau die Art Check, die Drift verhindert).

## Ausführen

Das Lab braucht **keine Installation**: reine Standardbibliothek, kein Server,
kein API-Key, kein Netz. Immer `python3`, immer aus dem Repo-Wurzelverzeichnis.

```bash
python3 tools/mutation_dojo.py --suite shipped    # Mutation Score Teil 1
python3 tools/mutation_dojo.py --bruecke          # Unit-Test vs. Spec-Test
python3 tools/spec_gate.py --check                # Abnahme-Kriterium Teil 2
```

Alles Weitere — inklusive der Reihenfolge — steht in [`labs/vl09-lab.md`](labs/vl09-lab.md).

### Optional, außerhalb des Labs

Die Server laufen zu sehen ist nicht Teil der Aufgabe; das Gate arbeitet rein
statisch und braucht keinen laufenden Prozess. Wer trotzdem mag und eine
Umgebung mit den Abhängigkeiten aus [`requirements.txt`](requirements.txt) hat:

```bash
python3 -m uvicorn api.app:app --reload                # Referenz  -> :8000/docs
python3 -m uvicorn api.drifted_server:app --port 8001  # driftet absichtlich

# Contract-Testing gegen den LAUFENDEN Server — findet Laufzeitverhalten,
# das ein statisches Gate strukturell nicht sehen kann (Teil 3, Leitfrage 2):
schemathesis run api/openapi.yaml --url http://localhost:8001 --checks all
```

**Diskussionsstoff:** Wann ist DRY beim Testen falsch? Warum ist ein Mutation
Score ohne Angabe der Mutantenklasse bedeutungslos? Was findet ein statisches
Gate, was ein Contract Test nicht findet — und umgekehrt?

> Damit ist der Code-Bogen des Kurses komplett: messy Tool (VL 1) → LLM
> (VL 3) → RAG-Korpus (VL 4/5) → gehärtet (VL 6) → Agent (VL 8) → spezifiziert
> (VL 9). VL 10 ordnet das Ganze in EU AI Act & Ethik ein.
