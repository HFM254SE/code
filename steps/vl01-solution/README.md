# LeineTech Ticket-Triage — `vl01-solution`

**Musterlösung** nach dem Lab in **VL 1 (Software-Assistenten)** — und zugleich
der **Startpunkt für VL 3**.

Gegenüber `vl01-start` wurde aufgeräumt:

- Sprechende Namen, Type Hints, Docstrings, `if __name__ == "__main__"`-Guard
- Keyword-Regeln als **Daten** (`CATEGORY_KEYWORDS`) statt fünffach kopierter
  Schleifen — die Prüf-Reihenfolge (first match wins) bleibt identisch
- Kein globaler Zustand mehr (`functools.lru_cache` statt `global CACHE`),
  Datei-Handling mit Context Manager + `encoding="utf-8"`
- Keine bare `except:`, kein `== None`, keine veränderbaren Default-Argumente
- `collections.Counter` statt acht Zähl-Schleifen
- `requirements.txt` aktualisiert → `trivy fs .` ist sauber

Das **Verhalten ist unverändert**: gleiche Klassifikation, gleicher Report,
gleiche grüne Tests (`python -m pytest`).

## Ausführen

```bash
pip install -r requirements.txt
python -m src.main
python -m pytest
pylint src/        # → deutlich ruhiger als auf vl01-start
trivy fs .         # → keine HIGH/CRITICAL-Findings mehr
```

> Weiter geht es in VL 3: `git checkout vl03-llm-client` —
> das Tool bekommt einen LLM-Anschluss über den OpenAI-kompatiblen Kurs-Endpunkt (HomeCloud).
