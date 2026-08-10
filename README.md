# LeineTech Ticket-Triage — `vl03-llm-client`

Stand nach **Teil 1 des Labs in VL 3** (LLMs: Deployment, Betrieb & Evaluierung).

Das Triage-Tool aus VL 1 hat jetzt einen **LLM-Anschluss**:

- `src/llm.py` — ein **litellm**-Wrapper gegen den **Kurs-Endpunkt**
  (HomeCloud, OpenAI-kompatibel). Per Umgebungsvariablen (`LLM_BASE_URL`,
  `LLM_API_KEY`, `LLM_MODEL`) auf jedes kompatible Backend umschaltbar —
  HomeCloud, Groq oder self-hosted. **Eine Codebasis, jedes Backend.**
- `src/summarize.py` — Ticket-Zusammenfassung und **LLM-Klassifikation**
  (Few-Shot-Prompt aus VL 2, JSON-Ausgabe, defensives Parsing).
- `src/main.py` — CLI mit Subkommandos.

## Ausführen

```bash
pip install -r requirements.txt
export LLM_BASE_URL="https://llm.homecloud.ee/v1"   # Kurs-Endpunkt, siehe SETUP.md
export LLM_API_KEY="<euer-key>"

python -m src.main triage             # regelbasiert (Stand VL 1)
python -m src.main summarize T-1003   # LLM-Zusammenfassung
python -m src.main classify T-1003    # Regeln vs. LLM im direkten Vergleich

# Anderes Backend (z. B. Groq als Plan B, siehe SETUP.md):
LLM_BASE_URL=https://api.groq.com/openai/v1 LLM_API_KEY=gsk-... \
  LLM_MODEL=llama-3.3-70b-versatile python -m src.main summarize T-1003
```

> Weiter im Lab: `labs/vl03-lab.md`. Der nächste Checkpoint
> (`vl03-evaluation`) misst systematisch, ob das LLM wirklich besser
> klassifiziert als die Keyword-Regeln.
