# SETUP — Kurs-LLM-Endpunkt (Nirk HomeCloud) & Plan B

Anleitung für den **kostenlosen Kurs-Endpunkt** (Nortal Nirk HomeCloud) und den
**Pflicht-Fallback** (Groq). Stand: 06/2026 — Client-Config-Formate ändern sich
gelegentlich, im Zweifel die verlinkten Docs prüfen.

## Was ist das?

Ein interner, self-hosted LLM-Endpunkt (Nortal Estonia AI Studio): ein
**LiteLLM-Gateway**, das **OpenAI- und Anthropic-kompatibel** ist und vor einem
vLLM-Inferenz-Node (6× RTX 3090) hängt. Für uns heißt das: jedes Tool, das mit
der OpenAI-API reden kann (OpenAI SDK, Continue.dev, OpenCode, Cursor mit
Custom Endpoint, …), funktioniert dagegen — **dauerhaft gratis, aber ohne SLA**.

| Dienst | URL | Zugang |
|---|---|---|
| API (LiteLLM) | `https://llm.homecloud.ee` | API-Key — Account auf Anfrage beim Head of Engineering (Nortal Estonia) |
| Chat-UI (OpenWebUI) | `https://ai.homecloud.ee` | selbst registrieren, dann Freischaltung durch den Head of Engineering (Nortal Estonia) |
| Monitoring (Grafana) | `https://grafana.homecloud.ee` | Google-SSO — *hier nachsehen, bevor ihr „kaputt" meldet* |

**Kurs-Modell:** Wir nutzen durchgehend **`qwen3.6-35B-A3B-FP8`** (Qwen3.6-MoE,
35B Parameter / 3B aktiv, FP8 — Tool-Calling + Reasoning). Mit dem
`curl`-Schnelltest unten könnt ihr prüfen, dass es gerade geladen ist.

## ⚠️ Wichtig vor dem ersten Request

- **Verfügbarkeit: nur montags 06:00–23:59 (Europe/Berlin).** Außerhalb dieses
  Fensters ist euer Key gesperrt — das ist **Absicht** (Schutz vor Dauerlast),
  kein Ausfall. Plant Arbeit am Endpunkt in dieses Fenster; sonst → Plan B
  (Groq) oder lokales Ollama.
- **Logging ist aktiv (Datenschutz!).** Eure **Prompts und die Antworten**
  werden geloggt und sind über euren persönlichen API-Key **euch zuordenbar**.
  Gebt deshalb **keine Passwörter, Secrets oder echten Personen-/Kundendaten**
  in Prompts, Code-Snippets oder die Chat-UI ein — im Zweifel anonymisieren.
- **Ein Key pro Person, nicht teilen.** Limits und Logs hängen am Key.

## Schnelltest (2 min)

```bash
export OPENAI_BASE_URL="https://llm.homecloud.ee/v1"
export OPENAI_API_KEY="<euer-key>"

# Welche Modelle sind verfügbar?
curl -s "$OPENAI_BASE_URL/models" -H "Authorization: Bearer $OPENAI_API_KEY"

# Eine Completion
curl -s "$OPENAI_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" -H "Content-Type: application/json" \
  -d '{"model": "qwen3.6-35B-A3B-FP8", "messages": [{"role": "user", "content": "Sag Moin."}]}'
```

⚠️ **Erste Antwort kann 200–300 s dauern** (Cold Start: Modell wird erst vom
Storage in die GPUs geladen). Das ist kein Fehler — einmal warten, danach ist
das Modell „hot".

## Client-Konfiguration

**Wichtigste Regel für alle Clients: Context auf ~128K cappen.** Der Server
kann mehr, aber große Kontexte fressen KV-Cache/VRAM und können den Endpunkt
für alle blockieren.

### Python / OpenAI SDK (so nutzt es unser `src/llm.py`)

```python
from openai import OpenAI

client = OpenAI()  # liest OPENAI_BASE_URL + OPENAI_API_KEY aus der Umgebung
```

Für die Labs ab VL 3 reicht es also, die beiden Umgebungsvariablen zu setzen —
derselbe Code läuft gegen Ollama (lokal), HomeCloud oder Groq.

### Continue.dev (VS Code)

`~/.continue/config.yaml` (Auszug):

```yaml
models:
  - name: HomeCloud Qwen
    provider: openai
    apiBase: https://llm.homecloud.ee/v1
    apiKey: <euer-key>
    model: qwen3.6-35B-A3B-FP8
    defaultCompletionOptions:
      contextLength: 131072   # ~128K cappen!
```

### OpenCode CLI

`~/.config/opencode/opencode.json` (Auszug):

```jsonc
{
  "provider": {
    "homecloud": {
      "npm": "@ai-sdk/openai-compatible",
      "options": { "baseURL": "https://llm.homecloud.ee/v1", "apiKey": "<euer-key>" },
      "models": {
        "qwen3.6-35B-A3B-FP8": { "limit": { "context": 131072 } }
      }
    }
  }
}
```

## Plan B: Groq (Pflicht!)

Der HomeCloud-Endpunkt hat **kein SLA** — er kann ausfallen, Cloudflare drosselt
teils Verbindungen von außerhalb Estlands, und der Betreiber ist zeitweise
offline. **Richtet deshalb vorab einen Groq-Account ein** (gratis, sehr schnell,
OpenAI-kompatibel):

1. `console.groq.com` → Account + API-Key (gratis Free-Tier)
2. Umschalten = nur zwei Variablen tauschen:

```bash
export OPENAI_BASE_URL="https://api.groq.com/openai/v1"
export OPENAI_API_KEY="<groq-key>"
# Modell z. B.: llama-3.3-70b-versatile (aktuelle Liste: console.groq.com/docs/models)
```

## Troubleshooting

| Problem | Lösung |
|---|---|
| Erste Anfrage hängt minutenlang | Cold Start (200–300 s) — warten, nicht abbrechen |
| 403, „nur montags 06:00–23:59 …" | Außerhalb des Zeitfensters — der Guardrail blockt, kein Bug. → Plan B (Groq)/Ollama |
| HTTP 429 „rate limit" | Zu viele/zu schnelle Anfragen — kurz warten und Anfragetempo drosseln |
| Timeout/Fehler nach Wartezeit | Endpunkt evtl. down → **Plan B (Groq)** nutzen, nicht debuggen |
| Sehr langsame Antworten | Cloudflare-Drosselung oder Last — kurze Sessions fahren |
| Agent „lockt" den Endpunkt | Context-Cap (128K) im Client prüfen — s. o. |
| Whole-Codebase-Aufgaben / große Multi-File-Edits | dafür ist der Endpunkt nicht gedacht → Cursor/Copilot oder lokales Ollama |

**Faustregel:** HomeCloud = gratis agentic Coding für kurze, fokussierte
Sessions. Alles Große → Cursor-Studierendenjahr oder lokal (Ollama).
