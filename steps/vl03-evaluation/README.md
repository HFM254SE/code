# LeineTech Ticket-Triage: `vl03-evaluation`

Endzustand des **Labs in VL 3**. Das Bauchgefühl „das LLM ist bestimmt besser“ wird durch
eine **Messung** ersetzt. Die Anleitung steht in `labs/vl03-lab.md`.

Neu gegenüber `vl03-llm-client`:

- `src/evaluate.py`: Evaluierung gegen das **Golden Dataset** `eval/golden.jsonl`
  (30 von Menschen gelabelte Tickets). Der Report zeigt je System Accuracy für Kategorie und
  Priorität und die Median-Latenz, dazu die Mehrheitsklasse als Vergleichswert, die Testdaten
  getrennt, übersehene dringende Tickets, die Unterschiede je Ticket, Parse-Fehler samt
  Zufallstreffern, Endpunkt-Fehler und Token pro Ticket. Alle Werte je Ticket landen in
  `eval/results.csv`.
- `tests/test_evaluate.py`: prüft Messlogik und Report ohne Endpunkt.

## Ausführen

```bash
python -m src.evaluate                  # nur Regeln, erste 10 Tickets (offline, wenige Sekunden)
python -m src.evaluate --all            # nur Regeln, alle 30 Tickets
python -m src.evaluate --llm            # Regeln und LLM, 10 Entwicklungstickets
python -m src.evaluate --llm --all      # alle 30 Tickets, dauert je nach Last Minuten
python -m src.evaluate --llm --csv eval/lauf-2.csv  # Ergebnis in eigene Datei
LLM_MODEL=<modell> python -m src.evaluate --llm     # anderes Modell, gleicher Code
```

Gemessen auf allen 30 Tickets ohne Endpunkt:

| System | Kategorie | Priorität | dringend übersehen | Latenz (Median) |
|---|---|---|---|---|
| Mehrheitsklasse (immer Software / mittel) | 30 % | 60 % | 8 von 8 | |
| Keyword-Regeln (VL 1) | 70 % | 90 % | 2 von 8 | < 0,1 ms |

Die LLM-Zeile messt ihr selbst. Ein Ticket entspricht 3,3 Prozentpunkten. T-1001 bis
T-1010 kennt ihr aus VL 2, deshalb weist der Report T-1011 bis T-1030 als Testdaten
getrennt aus.

**Diskussionsstoff:** Ab welchem Abstand lohnt sich der LLM-Einsatz? Wer zahlt die Latenz,
und was kosten die Token im Monat? Was bedeutet das für die Deployment-Entscheidung
(Cloud API, On-Premises, Edge) aus der Vorlesung?

> Hier endet der VL-3-Stand. Ab VL 4 und 5 (RAG) beantwortet das System Tickets inhaltlich,
> mit der Knowledge Base in `docs/` als Wissensquelle.
