# LeineTech Ticket-Triage: `vl03-llm-client`

Stand nach **Teil 1 des Labs in VL 3** (LLMs: Deployment, Betrieb und Evaluierung).
Die Anleitung steht in `labs/vl03-lab.md`.

Das Triage-Tool aus VL 1 hat jetzt einen **LLM-Anschluss**:

- `src/llm.py`: ein litellm-Wrapper gegen den Kurs-Endpunkt (HomeCloud, OpenAI-kompatibel).
  `chat()` liefert den Antworttext, `chat_with_usage()` zusätzlich die Token-Zahlen.
  Über Umgebungsvariablen lässt sich jedes OpenAI-kompatible Backend ansprechen.
- `src/summarize.py`: Zusammenfassung und LLM-Klassifikation mit Few-Shot-Prompt,
  JSON-Ausgabe und defensivem Parsen. Unbrauchbare Antworten bekommen den Rückfall
  Software / mittel und die Markierung `parse_fehler`. So zeigt die Evaluierung später,
  welche Treffer nur Zufall sind.
- `src/main.py`: Kommandozeile mit Subkommandos. Ohne Subkommando läuft der Regel-Report
  wie in VL 1.
- `tests/test_llm.py`, `tests/test_summarize.py`, `tests/test_main.py`: laufen ohne
  Endpunkt, weil sie den LLM-Aufruf durch eine Attrappe ersetzen.

## Ausführen

```bash
pip install -r requirements.txt
python -m pytest -q                   # offline, kein Key nötig

export LLM_BASE_URL="https://llm.homecloud.ee/v1"   # Kurs-Endpunkt, siehe SETUP.md
export LLM_API_KEY="<euer-key>"
export LLM_THINKING=off               # Reasoning aus: schneller, weniger Last
python -m src.llm                     # zeigt die Konfiguration, ohne den Endpunkt zu fragen

python -m src.main                    # regelbasierter Report (Stand VL 1)
python -m src.main summarize T-1003   # LLM-Zusammenfassung
python -m src.main classify T-1003    # Regeln und LLM im direkten Vergleich
```

## Konfiguration

| Variable | Bedeutung | Default |
|---|---|---|
| `LLM_BASE_URL` | Gateway-URL inkl. `/v1` | `https://llm.homecloud.ee/v1` |
| `LLM_API_KEY` | persönlicher Key | leer |
| `LLM_MODEL` | Modellname ohne Provider-Präfix | `qwen3.6-35B-A3B-FP8` |
| `LLM_THINKING` | `off` oder `on` | Default des Servers |
| `LLM_TIMEOUT` | Sekunden pro Anfrage | `120` |

`LLM_*` hat Vorrang vor den gleichnamigen `OPENAI_*`-Variablen aus `SETUP.md`. Welche Modelle
der Gateway gerade anbietet, zeigt `curl -s "$LLM_BASE_URL/models" -H "Authorization: Bearer $LLM_API_KEY"`.

> Weiter im Lab: Der nächste Checkpoint `vl03-evaluation` misst systematisch, ob das LLM
> wirklich besser klassifiziert als die Keyword-Regeln.
