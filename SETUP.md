# SETUP — Kurs-LLM-Endpunkt (Nirk HomeCloud)

Anleitung für den **kostenlosen Kurs-Endpunkt** (Nortal Nirk HomeCloud).
Stand: 06/2026 — Client-Config-Formate ändern sich gelegentlich, im Zweifel die
verlinkten Docs prüfen.

## Was ist das?

Ein interner, self-hosted LLM-Endpunkt (Nortal Estonia AI Studio): ein
**LiteLLM-Gateway**, das **OpenAI- und Anthropic-kompatibel** ist und vor einem
vLLM-Inferenz-Node (6× RTX 3090) hängt. Für uns heißt das: OpenAI-kompatible
Clients (Continue.dev mit `vllm`-Provider, OpenCode, die `litellm`-Library, …)
sprechen den Endpunkt direkt an — **dauerhaft gratis, aber ohne SLA**. Einzige
Ausnahme: das **Python-OpenAI-SDK** — sein User-Agent wird vom WAF geblockt,
deshalb gehen wir durchgängig über litellm/`vllm` (mehr dazu unten).

| Dienst | URL | Zugang |
|---|---|---|
| API (LiteLLM) | `https://llm.homecloud.ee` | API-Key erhaltet ihr vom Dozenten |

**Kurs-Modell:** Wir nutzen durchgehend **`qwen3.6-35B-A3B-FP8`** (Qwen3.6-MoE,
35B Parameter / 3B aktiv, FP8 — Tool-Calling + Reasoning). Mit dem
`curl`-Schnelltest unten könnt ihr prüfen, dass es gerade geladen ist.

## ⚠️ Wichtig vor dem ersten Request

- **Verfügbarkeit: nur montags 06:00–23:59 (Europe/Berlin).** Außerhalb dieses
  Fensters ist euer Key gesperrt — das ist **Absicht** (Schutz vor Dauerlast),
  kein Ausfall. Plant Arbeit am Endpunkt in dieses Fenster.
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
das Modell „hot". *(Im Kurs wärmt der Dozent das Modell vor Beginn einmal vor —
dann ist es für alle direkt „hot".)*

## Client-Konfiguration

**Wichtigste Regel für alle Clients: Context auf ~128K cappen.** Der Server
kann mehr, aber große Kontexte fressen KV-Cache/VRAM und können den Endpunkt
für alle blockieren.

### Python / litellm (so nutzt es unser `src/llm.py`)

Wir sprechen den Endpunkt über die **litellm**-Library an, **nicht** über das
OpenAI-SDK: Der WAF vor dem Gateway blockt den User-Agent des OpenAI-SDK
(`OpenAI/Python`). litellm mit dem **`hosted_vllm/`**-Provider nutzt einen
eigenen HTTP-Client und kommt sauber durch (Installation: `pip install litellm`,
steckt schon in `requirements.txt`).

```python
import litellm

resp = litellm.completion(
    model="hosted_vllm/qwen3.6-35B-A3B-FP8",   # Provider-Präfix + Kurs-Modell
    messages=[{"role": "user", "content": "Sag Moin."}],
    api_base="https://llm.homecloud.ee/v1",    # = LLM_BASE_URL / OPENAI_BASE_URL
    api_key="<euer-key>",                       # = LLM_API_KEY / OPENAI_API_KEY
)
print(resp.choices[0].message.content)
```

`src/llm.py` liest `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` (ersatzweise die
`OPENAI_*`-Varianten) aus der Umgebung — für die Labs ab VL 3 reicht es also,
diese Variablen zu setzen. **Default-Modell ist `qwen3.6-35B-A3B-FP8`**; ein
eigener Modellname kommt ohne `hosted_vllm/`-Präfix in `LLM_MODEL` (das setzt
`src/llm.py` selbst davor).

### VS Code + Continue.dev — der Kurs-Client (ab VL 1)

Im Kurs nutzen wir **VS Code mit der Continue.dev-Extension**. Zwei Modelle für
zwei Aufgaben:

- **Chat / Edit / Apply** (der „KI-Assistent") → läuft über die **HomeCloud**.
- **Autovervollständigung (Tab)** → läuft **lokal über Ollama** mit einem
  winzigen Coder-Modell. Das ist schnell, offline und belastet den geteilten
  HomeCloud-Endpunkt nicht (Tab-Completion feuert sehr häufig).

**Einmalig:** [Ollama](https://ollama.com) installieren und das
Autocomplete-Modell ziehen (~1 GB, läuft auch auf der CPU):

```bash
ollama run qwen2.5-coder:1.5b
```

*(Sehr schwacher Laptop? `qwen2.5-coder:0.5b` reicht für Autocomplete auch.)*

`~/.continue/config.yaml`:

```yaml
name: FHDW Kurs-Assistent
version: 0.0.1
schema: v1
models:
  # KI-Assistent (Chat/Edit/Apply) — Nirk HomeCloud, vllm-Provider (NICHT openai!)
  - name: HomeCloud Qwen
    provider: vllm
    model: qwen3.6-35B-A3B-FP8
    apiBase: https://llm.homecloud.ee/v1
    apiKey: <euer-key>
    roles:
      - chat
      - edit
      - apply
    defaultCompletionOptions:
      contextLength: 131072   # ~128K cappen — schont VRAM am geteilten Endpunkt
    requestOptions:
      extraBodyProperties:
        chat_template_kwargs:
          enable_thinking: false   # Reasoning-Modell → Thinking aus (s. Hinweis unten)
  # Autovervollständigung (Tab) — lokal via Ollama (schnell, offline)
  - name: Qwen2.5-Coder 1.5B (Tab)
    provider: ollama
    model: qwen2.5-coder:1.5b
    roles:
      - autocomplete
```

**`<euer-key>`** durch euren persönlichen Kurs-Key ersetzen.

**Wohin mit der Datei?** Die **globale** Continue-Config liegt im *Benutzerordner*
(nicht im Projekt) und gilt für alle Projekte — ideal für den Kurs:

- macOS/Linux: `~/.continue/config.yaml`
- Windows: `%USERPROFILE%\.continue\config.yaml` (= `C:\Users\<name>\.continue\config.yaml`)

Habt ihr dort schon eine **`config.json`** (Default bei frischer Installation)?
Kein Problem — **sobald eine `config.yaml` existiert, wird sie *statt* der
(veralteten) `config.json` geladen**; die `config.json` müsst ihr nicht anfassen.
Dateiname exakt `config.yaml` (nicht `.yml`).

> *Alternativ projektlokal:* `<projekt>/.continue/agents/<name>.yml` — das legt
> Continues „New Config (YAML)"-Button an, gilt dann aber **nur für dieses
> Projekt** (greift z. B. nicht in der „Eigener-Code"-Übung). Für den Kurs daher
> die globale Datei oben bevorzugen.

> **Warum `vllm` und nicht `openai`?** Der Endpunkt ist ein vLLM-Server hinter
> einem LiteLLM-Gateway — der `vllm`-Provider passt direkt dazu. Außerdem blockt
> der WAF vor dem Gateway gezielt den **OpenAI-SDK-User-Agent** (`OpenAI/Python`
> → HTTP 403 „Your request was blocked"). Wir sprechen HomeCloud deshalb
> durchgängig über **litellm/vllm** an — in Continue **und** in `src/llm.py`
> (siehe oben). Der `vllm`-Provider hat einen eigenen HTTP-Client und ist vom
> WAF nicht betroffen.

> **„Thinking" erscheint als Fließtext?** `qwen3.6-35B-A3B-FP8` ist ein
> **Reasoning-Modell** und liefert seine Denk-Tokens im Feld `reasoning_content`.
> Continue (**Release**) faltet dieses Feld (noch) nicht in einen einklappbaren
> „Thinking"-Block, sondern gibt es als Text aus. Deshalb schalten wir Thinking
> oben per `enable_thinking: false` ab → sauberere, schnellere Antworten und
> weniger Tokens am geteilten Endpunkt. Wer das Denken *eingeklappt sehen* will:
> Continue **Pre-Release** installieren (rendert `reasoning_content` als Block —
> dann den `requestOptions`-Block weglassen). Alternativer Aus-Schalter:
> `chatOptions:` → `baseSystemMessage: "/no_think"`.

### OpenCode CLI (optional, CLI-Alternative)

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

## Troubleshooting

| Problem | Lösung |
|---|---|
| Erste Anfrage hängt minutenlang | Cold Start (200–300 s) — warten, nicht abbrechen |
| 403, „nur montags 06:00–23:59 …" | Außerhalb des Zeitfensters — der Guardrail blockt, kein Bug. Im Fenster (montags) erneut versuchen |
| HTTP 429 „rate limit" | Zu viele/zu schnelle Anfragen — kurz warten und Anfragetempo drosseln |
| HTTP 401 / „unauthorized" | `apiKey` falsch oder fehlt → Key prüfen; notfalls in `~/.continue/config.yaml` unter dem Modell `requestOptions:` → `headers:` → `Authorization: "Bearer <euer-key>"` setzen |
| Tab-Completion kommt nicht | Läuft Ollama? (`ollama list`) Modell gezogen? (`ollama run qwen2.5-coder:1.5b`) — Autocomplete ist **lokal**, nicht HomeCloud |
| „Thinking"/Reasoning als Fließtext | Reasoning-Modell; Continue (Release) faltet `reasoning_content` nicht → `enable_thinking: false` (Config oben) oder Continue **Pre-Release** |
| Timeout/Fehler nach Wartezeit | Endpunkt evtl. down → kurze Pause, später erneut; nicht lokal debuggen. Bei anhaltendem Ausfall dem Dozenten Bescheid geben |
| Sehr langsame Antworten | Cloudflare-Drosselung oder Last — kurze Sessions fahren |
| Agent „lockt" den Endpunkt | Context-Cap (128K) im Client prüfen — s. o. |
| Whole-Codebase-Aufgaben / große Multi-File-Edits | dafür ist der Endpunkt nicht gedacht → Aufgabe in kleinere Schritte zerlegen, Kontext kappen |

**Faustregel:** HomeCloud = gratis KI-Assistent für kurze, fokussierte
Sessions. Große Multi-File-Aufgaben in kleinere Schritte zerlegen.
