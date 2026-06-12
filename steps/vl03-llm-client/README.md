# LeineTech Ticket-Triage — `vl03-llm-client`

Stand nach **Teil 1 des Labs in VL 3** (LLMs: Deployment, Betrieb & Evaluierung).

Das Triage-Tool aus VL 1 hat jetzt einen **LLM-Anschluss**:

- `src/llm.py` — ein OpenAI-SDK-Client gegen die **OpenAI-kompatible
  Ollama-API** (`http://localhost:11434/v1`). Per Umgebungsvariablen
  (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`) auf jedes kompatible Backend
  umschaltbar — lokal, self-hosted oder Cloud. **Eine Codebasis, jedes Backend.**
- `src/summarize.py` — Ticket-Zusammenfassung und **LLM-Klassifikation**
  (Few-Shot-Prompt aus VL 2, JSON-Ausgabe, defensives Parsing).
- `src/main.py` — CLI mit Subkommandos.

## Ausführen

```bash
pip install -r requirements.txt
ollama pull llama3.2                  # einmalig, ~2 GB

python -m src.main triage             # regelbasiert (Stand VL 1)
python -m src.main summarize T-1003   # LLM-Zusammenfassung
python -m src.main classify T-1003    # Regeln vs. LLM im direkten Vergleich

# Anderes Modell / anderes Backend:
LLM_MODEL=qwen2.5:3b python -m src.main classify T-1003
LLM_BASE_URL=https://api.openai.com/v1 LLM_API_KEY=sk-... LLM_MODEL=gpt-5 \
  python -m src.main summarize T-1003
```

> Weiter im Lab: `labs/vl03-lab.md`. Der nächste Checkpoint
> (`vl03-evaluation`) misst systematisch, ob das LLM wirklich besser
> klassifiziert als die Keyword-Regeln.
