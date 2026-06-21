# LeineTech Ticket-Triage — `vl03-evaluation`

Endzustand des **Labs in VL 3**: Das Bauchgefühl („das LLM ist bestimmt
besser") wird durch **Messung** ersetzt.

Neu gegenüber `vl03-llm-client`:

- `src/evaluate.py` — Use-Case-spezifische Evaluierung gegen das
  **Golden Dataset** (`eval/golden.jsonl`, 30 von Menschen gelabelte Tickets):
  Accuracy für Kategorie & Priorität plus Latenz, für Keyword-Regeln und
  beliebige LLMs. Ergebnisse zusätzlich als `eval/results.csv`.

## Ausführen

```bash
python -m src.evaluate                       # nur Regeln (offline, < 1 s)
python -m src.evaluate --llm                 # + qwen3.6 über HomeCloud (10 Tickets)
python -m src.evaluate --llm --all           # alle 30 Tickets
LLM_MODEL=<modell> python -m src.evaluate --llm      # anderes Modell/Backend
```

*(Default ist `--limit 10`, damit eine Runde im Lab ~1 Minute dauert; das
Lab-Gerüst zum Selberbauen liegt unter `labs/templates/evaluate_skeleton.py`.)*

Typisches Bild (eure Zahlen variieren je nach Modell):

- Keyword-Regeln: ~2/3 der Kategorien richtig, in Mikrosekunden, kostenlos
- LLM über den Kurs-Endpunkt (qwen3.6-35B): deutlich besser, Sekunden pro Ticket
- Cloud-Frontier-Modell (z. B. via Groq): am besten — gegen Geld und Datenabfluss

**Diskussionsstoff:** Ab welcher Accuracy-Differenz lohnt sich der LLM-Einsatz?
Wer zahlt die Latenz? Und was bedeutet das für die Deployment-Entscheidung
(Cloud / On-Prem / Edge) aus der Vorlesung?

> Hier endet der VL-3-Stand. Ab VL 4/5 (RAG) beantwortet das System Tickets
> inhaltlich — mit der Knowledge Base in `docs/` als Wissensquelle.
