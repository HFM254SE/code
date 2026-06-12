# LeineTech Ticket-Triage — `vl01-start`

Ausgangszustand für das Lab in **VL 1 (Software-Assistenten)**.

Dies ist das interne Ticket-Triage-Tool der LeineTech GmbH: Es liest Support-
Tickets aus `data/tickets.json`, ordnet sie per **Keyword-Regeln** einer
Kategorie und Priorität zu und druckt einen Report. Der Code **funktioniert** —
aber er ist in schlechtem Zustand (ein Kollege hat ihn "mal schnell" gebaut).

**Eure Aufgabe in VL 1:** den Zustand mit Linter, KI-Assistent und
Artefakt-Scanner sichtbar machen und verbessern → siehe `labs/vl01-lab.md`.

## Ausführen

```bash
pip install -r requirements.txt
python -m src.main          # Triage-Report über alle Tickets
python -m pytest            # Tests (müssen vor UND nach dem Refactoring grün sein)
```

## Struktur

```
data/tickets.json   30 Support-Tickets (Mai 2026)
docs/               Knowledge-Base der LeineTech-IT (wird ab VL 4 wichtig)
eval/golden.jsonl   Von Menschen vergebene Soll-Labels (wird ab VL 3 wichtig)
src/                Das Triage-Tool (bewusst in schlechtem Zustand)
tests/              pytest-Tests — euer Sicherheitsnetz beim Refactoring
labs/vl01-lab.md    Schritt-für-Schritt-Anleitung für das Lab
```
