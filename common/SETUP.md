# SETUP: Kurs-LLM-Endpunkt (Nortal Nirk HomeCloud)

Anleitung für den **kostenlosen Kurs-Endpunkt** und die Werkzeuge, die ihn im Kurs
nutzen. Stand: 09/2026. Client-Formate ändern sich gelegentlich. Im Zweifel die
verlinkten Dokumentationen prüfen.

| Abschnitt | gebraucht ab |
|---|---|
| [Wichtig vor dem ersten Request](#wichtig-vor-dem-ersten-request), [Schnelltest](#schnelltest-2-min) | VL 1 |
| [VS Code und Continue.dev](#vs-code-und-continuedev-ab-vl-1) | VL 1 |
| [Python und litellm](#python-und-litellm-ab-vl-3-so-nutzt-es-srcllmpy) | VL 3 |
| [Embeddings](#embeddings-ab-vl-4) | VL 4 |
| [opencode](#opencode-ab-vl-9) | VL 9 |
| [Plan B](#plan-b-wenn-der-kurs-endpunkt-nicht-erreichbar-ist) | bei Bedarf |

## Was ist das?

Ein interner, self-hosted LLM-Endpunkt von Nortal (Estonia AI Studio): ein
**LiteLLM-Gateway**, das **OpenAI- und Anthropic-kompatibel** ist und vor einem
vLLM-Inferenz-Node (6× RTX 3090) hängt. OpenAI-kompatible Clients wie Continue.dev
(Provider `vllm`), opencode oder die Library `litellm` sprechen ihn direkt an. Er
ist **dauerhaft gratis, hat aber kein SLA**.

Einzige Ausnahme ist das **Python-OpenAI-SDK**. Die Web Application Firewall (WAF)
vor dem Gateway blockt seinen User-Agent (`OpenAI/Python` → HTTP 403 „Your request
was blocked“). Deshalb gehen wir durchgängig über litellm bzw. den Provider `vllm`.

| Dienst | URL | Zugang |
|---|---|---|
| API (LiteLLM) | `https://llm.homecloud.ee` | API-Key erhaltet ihr vom Dozenten |

**Kurs-Modelle:**

- Chat: **`qwen3.6-35B-A3B-FP8`** (Qwen3.6-MoE, 35B Parameter, davon 3B aktiv, FP8,
  kann Tool-Calling und Reasoning). Mit dem Schnelltest unten seht ihr, ob es
  gerade geladen ist.
- Embeddings ab VL 4: **`qwen3-embed-4b`** (Vektoren mit 2560 Dimensionen).

## Wichtig vor dem ersten Request

- **Verfügbarkeit: nur montags 06:00 bis 23:59 (Europe/Berlin).** Außerhalb dieses
  Fensters ist euer Key gesperrt. Das ist **Absicht** (Schutz vor Dauerlast) und
  kein Ausfall. Plant die Arbeit am Endpunkt in dieses Fenster.
- **Logging ist aktiv (Datenschutz!).** Eure **Prompts und die Antworten** werden
  protokolliert und sind über euren persönlichen API-Key **euch zuordenbar**. Gebt
  deshalb **keine Passwörter, Secrets oder echten Personen- und Kundendaten** in
  Prompts, Code-Snippets oder die Chat-Oberfläche ein. Im Zweifel anonymisieren.
- **Ein Key pro Person, nicht teilen.** Limits und Logs hängen am Key.
- **Kaltstart:** Die erste Antwort des Tages kann **200 bis 300 s** dauern, weil das
  Modell erst in die GPUs geladen wird. Das ist kein Fehler. Danach ist das Modell
  „hot“. Im Kurs wärmt der Dozent das Modell vor Beginn einmal vor. Das
  Embedding-Modell hat einen eigenen Kaltstart.

## Schnelltest (2 min)

```bash
export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"

# Welche Modelle sind verfügbar?
curl -s "$LLM_BASE_URL/models" -H "Authorization: Bearer $LLM_API_KEY"

# Eine Completion
curl -s "$LLM_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $LLM_API_KEY" -H "Content-Type: application/json" \
  -d '{"model": "qwen3.6-35B-A3B-FP8", "messages": [{"role": "user", "content": "Sag Moin."}]}'
```

Windows PowerShell: Variablen mit `$env:LLM_BASE_URL = "https://llm.homecloud.ee/v1"`
setzen und `curl.exe` statt `curl` aufrufen. Die Variablen gelten nur in dem
Terminal, in dem ihr sie setzt.

## VS Code und Continue.dev (ab VL 1)

Im Kurs nutzen wir **VS Code mit der Continue.dev-Extension**. Zwei Modelle
übernehmen zwei Aufgaben:

- **Chat, Edit und Apply** (der „KI-Assistent“) laufen über die **HomeCloud**.
- **Autovervollständigung (Tab)** läuft **lokal über Ollama** mit einem kleinen
  Coder-Modell. Das ist schnell, funktioniert offline und belastet den geteilten
  Endpunkt nicht, denn Tab-Completion feuert sehr häufig.

**Einmalig:** [Ollama](https://ollama.com) installieren und das Autocomplete-Modell
herunterladen (ca. 1 GB, läuft auch auf der CPU):

```bash
ollama pull qwen2.5-coder:1.5b
```

Sehr schwacher Laptop? Dann reicht `qwen2.5-coder:0.5b`. Tragt das Modell unten
in der Konfiguration bei der Tab-Rolle unter `model:` ein, sonst bleibt die
Tab-Vervollständigung stumm.

`~/.continue/config.yaml`:

```yaml
name: FHDW Kurs-Assistent
version: 0.0.1
schema: v1
models:
  # KI-Assistent (Chat, Edit, Apply) über die Nirk HomeCloud. Provider vllm, nicht openai.
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
      contextLength: 131072   # auf ca. 128K begrenzen, schont den VRAM am geteilten Endpunkt
    requestOptions:
      extraBodyProperties:
        chat_template_kwargs:
          enable_thinking: false   # Reasoning-Modell: Thinking aus, siehe Hinweis unten
  # Autovervollständigung (Tab) lokal über Ollama
  - name: Qwen2.5-Coder 1.5B (Tab)
    provider: ollama
    model: qwen2.5-coder:1.5b
    roles:
      - autocomplete
```

**`<euer-key>`** durch euren persönlichen Kurs-Key ersetzen.

**Wohin mit der Datei?** Die **globale** Continue-Konfiguration liegt im
Benutzerordner (nicht im Projekt) und gilt für alle Projekte. Das passt für den Kurs:

- macOS und Linux: `~/.continue/config.yaml`
- Windows: `%USERPROFILE%\.continue\config.yaml` (also `C:\Users\<name>\.continue\config.yaml`)

Liegt dort schon eine **`config.json`** (Default bei frischer Installation)? Kein
Problem: **Sobald eine `config.yaml` existiert, lädt Continue sie statt der
älteren `config.json`.** Die `config.json` müsst ihr nicht anfassen. Der Dateiname
lautet exakt `config.yaml` (nicht `.yml`).

> *Alternativ projektlokal:* `<projekt>/.continue/agents/<name>.yml`. Diese Datei
> legt Continues Button „New Config (YAML)“ an. Sie gilt aber **nur für dieses
> Projekt** und greift zum Beispiel nicht in der Übung mit eigenem Code. Für den
> Kurs deshalb die globale Datei oben bevorzugen.

> **Warum `vllm` und nicht `openai`?** Der Endpunkt ist ein vLLM-Server hinter
> einem LiteLLM-Gateway, dazu passt der Provider `vllm` direkt. Außerdem blockt die
> WAF vor dem Gateway gezielt den User-Agent des OpenAI-SDK. Der Provider `vllm`
> hat einen eigenen HTTP-Client und ist davon nicht betroffen. Dasselbe gilt für
> litellm in `src/llm.py` (siehe unten).

> **„Thinking“ erscheint als Fließtext?** `qwen3.6-35B-A3B-FP8` ist ein
> **Reasoning-Modell** und liefert seine Denk-Tokens im Feld `reasoning_content`.
> Continue (**Release**) faltet dieses Feld nicht in einen einklappbaren Block,
> sondern gibt es als Text aus. Deshalb schalten wir Thinking oben mit
> `enable_thinking: false` ab. Das ergibt sauberere und schnellere Antworten und
> spart Tokens am geteilten Endpunkt. Wer das Denken eingeklappt sehen will,
> installiert Continue **Pre-Release** und lässt den Block `requestOptions` weg.
> Alternativer Aus-Schalter: `chatOptions:` → `baseSystemMessage: "/no_think"`.

## Python und litellm (ab VL 3, so nutzt es `src/llm.py`)

Wir sprechen den Endpunkt über die Library **litellm** an, **nicht** über das
OpenAI-SDK (siehe WAF oben). litellm mit dem Provider-Präfix **`hosted_vllm/`**
nutzt einen eigenen HTTP-Client und kommt durch. litellm steht ab `vl01-solution`
in `requirements.txt`.

`src/llm.py` liest seine Konfiguration aus Umgebungsvariablen:

| Variable | Bedeutung | Default |
|---|---|---|
| `LLM_BASE_URL` | Gateway-URL inklusive `/v1` | `https://llm.homecloud.ee/v1` |
| `LLM_API_KEY` | euer persönlicher Key | leer |
| `LLM_MODEL` | Modellname **ohne** `hosted_vllm/`, das Präfix setzt `src/llm.py` selbst | `qwen3.6-35B-A3B-FP8` |
| `LLM_THINKING` | `off` oder `on`. Für die Labs empfohlen: `off` (schneller, weniger Last) | Default des Servers |
| `LLM_TIMEOUT` | Sekunden bis zum Abbruch einer Anfrage | `120` |

Statt `LLM_BASE_URL`, `LLM_API_KEY` und `LLM_MODEL` funktionieren auch
`OPENAI_BASE_URL`, `OPENAI_API_KEY` und `OPENAI_MODEL`. Sind beide gesetzt, hat
`LLM_*` Vorrang. `LLM_THINKING` nutzt denselben Schalter wie Continue oben
(`chat_template_kwargs.enable_thinking`).

```bash
export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"
export LLM_THINKING=off
python -m src.llm      # zeigt die Konfiguration, ohne den Endpunkt zu fragen
```

Erwartet (den Key selbst gibt `src/llm.py` nie aus):

```text
Endpunkt: https://llm.homecloud.ee/v1
Modell:   qwen3.6-35B-A3B-FP8
API-Key:  gesetzt
Thinking: aus
Timeout:  120 s
```

Danach die erste echte Anfrage:

```bash
python -c "from src.llm import chat; print(chat('Sag nur: OK'))"
```

Der Default-Timeout von 120 s ist kürzer als ein Kaltstart. Ist das Modell noch
nicht vorgewärmt, bricht die erste Anfrage mit `Timeout` ab. Dann die Anfrage mit
längerem Timeout wiederholen: `LLM_TIMEOUT=360 python -c "…"` (PowerShell: vorher
`$env:LLM_TIMEOUT = "360"`).

So sieht der Aufruf in litellm ohne `src/llm.py` aus:

```python
import litellm

resp = litellm.completion(
    model="hosted_vllm/qwen3.6-35B-A3B-FP8",   # Provider-Präfix und Kurs-Modell
    messages=[{"role": "user", "content": "Sag Moin."}],
    api_base="https://llm.homecloud.ee/v1",    # = LLM_BASE_URL
    api_key="<euer-key>",                       # = LLM_API_KEY
)
print(resp.choices[0].message.content)
```

## Embeddings (ab VL 4)

Die RAG-Labs betten Texte mit **`qwen3-embed-4b`** ein (`src/embedder.py`). Das
Modell läuft auf demselben Endpunkt, mit denselben Variablen `LLM_BASE_URL` und
`LLM_API_KEY`, und liefert Vektoren mit **2560 Dimensionen**.

- **Eigener Kaltstart:** Das Embedding-Modell wird unabhängig vom Chat-Modell
  geladen. Vorwärmen in einem zweiten Terminal (venv aktiv, Variablen gesetzt):

  ```bash
  python -c "from src.llm import get_base_url, get_api_key; import litellm; r = litellm.embedding(model='hosted_vllm/qwen3-embed-4b', input=['Test'], api_base=get_base_url(), api_key=get_api_key()); print(len(r['data'][0]['embedding']), 'Dimensionen')"
  ```

  Erwartet: `2560 Dimensionen`. `src.llm` steht bewusst vor `litellm` im Import,
  damit litellm seine Preisliste lokal lädt und nicht aus dem Internet.
- **Gleiches Modell für Fragen und Chunks:** Wer `EMBEDDING_MODEL` ändert, muss
  neu indexieren (`chroma_db/` löschen und `python -m src.ingest docs` ausführen).
  Sonst liegen die Vektoren in verschiedenen Räumen, oder ChromaDB meldet einen
  Dimensionsfehler.

## opencode (ab VL 9)

Ab VL 9 arbeitet ihr mit dem Coding-Agenten **opencode** im Terminal. Vorher ist
er eine optionale Alternative zu Continue.

Installieren (eine der beiden Varianten) und prüfen:

```bash
curl -fsSL https://opencode.ai/install | bash    # oder: npm i -g opencode-ai
opencode --version
```

`~/.config/opencode/opencode.json` liest den Key aus einer Umgebungsvariable. So
steht er in keiner Datei im Klartext:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "model": "homecloud/qwen3.6-35B-A3B-FP8",
  "provider": {
    "homecloud": {
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "https://llm.homecloud.ee/v1",
        "apiKey": "{env:HOMECLOUD_API_KEY}"
      },
      "models": {
        "qwen3.6-35B-A3B-FP8": { "limit": { "context": 131072, "output": 8192 } }
      }
    }
  }
}
```

```bash
export HOMECLOUD_API_KEY="<euer-key>"   # im Terminal, in dem ihr opencode startet
```

Die Arbeitsweise im Lab (Plan- und Build-Modus, `AGENTS.md`) beschreibt
`labs/vl09-lab.md`.

## Plan B: wenn der Kurs-Endpunkt nicht erreichbar ist

Ehrlich vorweg: **Einen Ersatz-Endpunkt mit Zusage gibt es im Kurs nicht** (Stand
09/2026). Keiner der Wege unten ist gegen alle Labs getestet. Für die
Präsenzveranstaltung sagt der Dozent an, welcher Weg gilt. Geht in dieser
Reihenfolge vor:

1. **Prüfen, ob es wirklich ein Ausfall ist.** HTTP 403 mit dem Hinweis „nur
   montags …“ ist das Zeitfenster. Ein `Timeout` bei der ersten Anfrage ist meist
   der Kaltstart: mit `LLM_TIMEOUT=360` wiederholen.
2. **Offline weiterarbeiten.** Jedes Lab hat Teile ohne Endpunkt: die Tests mit
   Attrappen (`python -m pytest -q`), die Regel-Baseline (`python -m src.evaluate
   --all`, ab VL 3), die Keyword-Suche (`--mode keyword`, ab VL 4), den
   Injection-Scanner (`python -m src.main scan --angriffe`, ab VL 6) und in VL 9
   den ganzen Teil 1. Die Schritte mit LLM holt ihr im nächsten Zeitfenster nach.
3. **Mit einem Team arbeiten, dessen Zugang läuft.**
4. **Lokales Modell über Ollama** (ungetestet, nur nach Ansage). Das Modell aus
   VL 1 läuft schon auf eurem Rechner:

   ```bash
   export LLM_BASE_URL="http://localhost:11434/v1"
   export LLM_MODEL="qwen2.5-coder:1.5b"
   export LLM_API_KEY="ollama"            # Ollama prüft den Key nicht, ein Platzhalter reicht
   ```

   `src/llm.py` setzt `hosted_vllm/` davor und spricht Ollama über dessen
   OpenAI-kompatible Schnittstelle an. Die Grenzen sind deutlich. Ein
   1,5-B-Modell klassifiziert schlechter, eure Messwerte aus VL 3 sind also nicht
   mit dem Kursmodell vergleichbar. Der Agent aus VL 8 braucht zuverlässiges
   Tool-Calling, das kleine Modelle nicht leisten. Für die Embeddings aus VL 4
   und VL 5 ist kein lokaler Ersatz vorgesehen: Ein anderes Modell hat eine
   andere Dimension, und der Index müsste neu gebaut werden.
5. **Anderer OpenAI-kompatibler Anbieter** mit eigenem Account: technisch über
   dieselben drei Variablen möglich (ein Modellname mit Provider-Präfix wie
   `anbieter/modell` geht unverändert an litellm). Das ist kein Kursweg und wird
   nicht unterstützt. Prüft vorher die Nutzungsbedingungen und schickt nur die
   erfundenen Kursdaten.

## Troubleshooting

| Problem | Lösung |
|---|---|
| Erste Anfrage hängt minutenlang oder endet mit `Timeout` | Kaltstart (200 bis 300 s). Continue: einmal warten. `src/llm.py`: mit `LLM_TIMEOUT=360` wiederholen. |
| HTTP 403 mit „nur montags 06:00–23:59 …“ | Außerhalb des Zeitfensters. Das Gateway blockt absichtlich, kein Bug. Im Fenster (montags) erneut versuchen. |
| HTTP 403 „Your request was blocked“ | Die WAF blockt den Client. Kein OpenAI-SDK verwenden, sondern litellm mit `hosted_vllm/` bzw. in Continue den Provider `vllm`. |
| HTTP 429 „rate limit“ | Zu viele oder zu schnelle Anfragen. Kurz warten und langsamer arbeiten. |
| HTTP 401 oder „unauthorized“ | Key falsch oder nicht gesetzt. `python -m src.llm` zeigt, ob `LLM_API_KEY` gesetzt ist. In Continue notfalls unter dem Modell `requestOptions:` → `headers:` → `Authorization: "Bearer <euer-key>"` setzen. |
| Tab-Completion kommt nicht | Läuft Ollama (`ollama list`)? Ist das Modell geladen (`ollama pull qwen2.5-coder:1.5b`)? Steht dasselbe Modell in der Tab-Rolle der `config.yaml`? Autocomplete läuft **lokal**, nicht über die HomeCloud. |
| „Thinking“ als Fließtext | Reasoning-Modell. Continue (Release) faltet `reasoning_content` nicht. `enable_thinking: false` (Konfiguration oben) oder Continue **Pre-Release**. |
| Fehler nach längerer Wartezeit, auch im Zeitfenster | Endpunkt eventuell ausgefallen. Kurz pausieren und später erneut versuchen, nicht lokal debuggen. Bei anhaltendem Ausfall dem Dozenten Bescheid geben, dann [Plan B](#plan-b-wenn-der-kurs-endpunkt-nicht-erreichbar-ist). |
| Sehr langsame Antworten | Last am geteilten Endpunkt oder Drosselung durch Cloudflare. Kurze Sessions fahren, `LLM_THINKING=off` setzen. |
| Agent blockiert den Endpunkt | Kontext im Client auf ca. 128K begrenzen (siehe oben). |
| Aufgaben über die ganze Codebasis oder große Multi-File-Edits | Dafür ist der Endpunkt nicht gedacht. Aufgabe in kleinere Schritte zerlegen, Kontext begrenzen. |

**Faustregel:** Die HomeCloud ist ein kostenloser KI-Assistent für kurze,
fokussierte Sessions. Große Aufgaben über viele Dateien in kleinere Schritte
zerlegen.
