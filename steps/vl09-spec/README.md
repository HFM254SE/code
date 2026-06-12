# LeineTech Ticket-Triage — `vl09-spec`

Endzustand des **Labs in VL 9**: Spec-Driven Development am eigenen Projekt.
Die API wird **zuerst als Spec** beschrieben (`api/openapi.yaml`), Code wird
daraus abgeleitet — und Abweichungen (Spec Drift) werden messbar gemacht.

Neu gegenüber `vl08-agent`:

- `api/openapi.yaml` — OpenAPI-3.1-Spec der LeineTech Ticket-API
  (Tickets auflisten/anlegen/lesen, `triage`, `escalate`). **Single Source
  of Truth.**
- `api/app.py` — Referenz-Server (FastAPI), exakt spec-konform.
- `api/drifted_server.py` — **absichtlich** abweichend (5 versteckte Drifts)
  für Lab-Teil 3.
- `api/CLAUDE.beispiel.md` — Beispiel-Lösung für die selbst geschriebene
  `CLAUDE.md` (Lab-Teil 2).
- `tests/test_openapi_spec.py` — offline: Spec self-consistent + Kategorie-Enum
  passt zu den Triage-Regeln (genau die Art Check, die Drift verhindert).

## Ausführen

```bash
pip install -r requirements.txt
python -m pytest tests/test_openapi_spec.py     # offline, kein Server nötig

uvicorn api.app:app --reload                    # Referenz-Server → :8000/docs
uvicorn api.drifted_server:app --port 8001      # driftet absichtlich

# Drift maschinell finden:
schemathesis run api/openapi.yaml --base-url http://localhost:8001 --checks all
```

**Diskussionsstoff:** Warum ist die Spec „das Gesetz"? Was findet schemathesis
automatisch, was nur ein Mensch? Wie verhindert ein CI-Gate, dass Code und
Spec auseinanderlaufen?

> Damit ist der Code-Bogen des Kurses komplett: messy Tool (VL 1) → LLM
> (VL 3) → RAG-Korpus (VL 4/5) → gehärtet (VL 6) → Agent (VL 8) → spezifiziert
> (VL 9). VL 10 ordnet das Ganze in EU AI Act & Ethik ein.
