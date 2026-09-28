"""Zentraler LLM-Zugriff über den Kurs-Endpunkt (Nortal HomeCloud).

Der Endpunkt ist ein LiteLLM-Gateway vor einem vLLM-Server und spricht das
OpenAI-Format. Wir nutzen die Library litellm und NICHT das OpenAI-SDK: Die
Web Application Firewall (WAF) vor dem Gateway blockt den User-Agent des
OpenAI-SDK. litellm mit dem Provider-Präfix `hosted_vllm/` kommt durch.

Konfiguration über Umgebungsvariablen (siehe SETUP.md). LLM_* hat jeweils
Vorrang vor OPENAI_*:

    LLM_BASE_URL / OPENAI_BASE_URL   Gateway-URL inkl. /v1
    LLM_API_KEY  / OPENAI_API_KEY    persönlicher API-Key
    LLM_MODEL    / OPENAI_MODEL      Modellname (Default: qwen3.6-35B-A3B-FP8)
    LLM_THINKING                     off oder on (ohne Variable: Default des Servers)
    LLM_TIMEOUT                      Sekunden bis zum Abbruch einer Anfrage (Default: 120)

`python -m src.llm` zeigt die aktuelle Konfiguration, ohne den Endpunkt zu fragen.
chat() liefert den Antworttext, chat_with_usage() zusätzlich die Token-Zahlen.
Ab VL 4 nutzen auch RAG und Agenten diese Funktionen. Neue Parameter kommen
deshalb nur als optionale Keyword-Argumente dazu.
"""

import os

# litellm lädt beim Import sonst eine Preisliste aus dem Internet nach. Wir
# bleiben lokal: Das startet schneller, funktioniert offline und schickt keine
# unnötigen Requests. Die Variable muss VOR dem Import gesetzt sein.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import litellm  # noqa: E402  pylint: disable=wrong-import-position

litellm.telemetry = False  # keine Nutzungsdaten an litellm senden

DEFAULT_BASE_URL = "https://llm.homecloud.ee/v1"
DEFAULT_MODEL = "qwen3.6-35B-A3B-FP8"
DEFAULT_TIMEOUT_S = 120.0

SYSTEM_PROMPT = (
    "Du bist ein präziser Assistent für den IT-Support der LeineTech GmbH. "
    "Antworte knapp, sachlich und auf Deutsch."
)

_THINKING_OFF = {"off", "aus", "0", "false", "no"}
_THINKING_ON = {"on", "an", "1", "true", "yes"}


def get_base_url() -> str:
    """Gateway-URL (inkl. /v1) aus der Umgebung, sonst Kurs-Default."""
    return (
        os.environ.get("LLM_BASE_URL")
        or os.environ.get("OPENAI_BASE_URL")
        or DEFAULT_BASE_URL
    )


def get_api_key() -> str:
    """API-Key aus der Umgebung (LLM_* hat Vorrang vor OPENAI_*)."""
    return os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or ""


def get_model() -> str:
    """Modellname aus der Umgebung, sonst Kurs-Default (ohne Provider-Präfix)."""
    return os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL


def get_thinking() -> bool | None:
    """Thinking-Schalter aus LLM_THINKING: False (aus), True (an), None (Server-Default)."""
    value = os.environ.get("LLM_THINKING", "").strip().lower()
    if value in _THINKING_OFF:
        return False
    if value in _THINKING_ON:
        return True
    return None


def get_timeout() -> float:
    """Timeout pro Anfrage in Sekunden aus LLM_TIMEOUT, sonst DEFAULT_TIMEOUT_S."""
    return float(os.environ.get("LLM_TIMEOUT") or DEFAULT_TIMEOUT_S)


def _provider_model(model: str) -> str:
    """Stellt litellm das richtige Provider-Präfix voran.

    `hosted_vllm/` weist litellm an, den OpenAI-kompatiblen vLLM-Endpunkt
    anzusprechen. Ein bereits präfixierter Name (z. B. `ollama/…`) bleibt
    unverändert.
    """
    return model if "/" in model else f"hosted_vllm/{model}"


def _request_options(max_tokens: int | None) -> dict:
    """Optionale Anfrage-Parameter: Timeout, Längengrenze und Thinking-Schalter."""
    options: dict = {"timeout": get_timeout()}
    if max_tokens is not None:
        options["max_tokens"] = max_tokens
    thinking = get_thinking()
    if thinking is not None:
        # Qwen3.x liest den Schalter aus dem Chat-Template. Continue nutzt in
        # SETUP.md denselben Weg, um Thinking abzuschalten.
        options["extra_body"] = {"chat_template_kwargs": {"enable_thinking": thinking}}
    return options


def _token_usage(response) -> dict:
    """Token-Zahlen der Antwort. Fehlt die Angabe beim Backend, stehen dort Nullen."""
    usage = getattr(response, "usage", None)
    return {
        "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
    }


def chat_with_usage(
    prompt: str,
    system: str = SYSTEM_PROMPT,
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int | None = None,
) -> tuple[str, dict]:
    """Schickt einen Prompt an das LLM und liefert (Antworttext, Token-Zahlen).

    Der Aufruf ist zustandslos: Das Modell sieht nur die Nachrichten, die wir
    hier mitschicken. temperature=0.0 ist Default, weil Klassifikation möglichst
    reproduzierbar sein soll. Bitgenau gleich sind die Antworten trotzdem nicht.
    Mit Thinking zählen die Denk-Tokens zu completion_tokens und kosten mit.
    """
    response = litellm.completion(
        model=_provider_model(model or get_model()),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        api_base=get_base_url(),
        api_key=get_api_key(),
        temperature=temperature,
        **_request_options(max_tokens),
    )
    # Ohne stream=True kommt eine vollständige Antwort. Mit Streaming käme ein
    # Wrapper, der Stück für Stück liefert und kein message.content hat. Die
    # Prüfung hält fest, dass wir nicht streamen, statt blind auf choices zu greifen.
    if isinstance(response, litellm.CustomStreamWrapper):
        raise TypeError("chat() erwartet eine vollständige Antwort, kein Streaming.")
    text = response.choices[0].message.content or ""
    return text, _token_usage(response)


def chat(
    prompt: str,
    system: str = SYSTEM_PROMPT,
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int | None = None,
) -> str:
    """Wie chat_with_usage(), liefert aber nur den Antworttext."""
    text, _ = chat_with_usage(
        prompt, system=system, model=model, temperature=temperature, max_tokens=max_tokens
    )
    return text


def describe_config() -> str:
    """Aktuelle Konfiguration als Text. Der Key selbst wird nie ausgegeben."""
    thinking = {None: "Server-Default", True: "an", False: "aus"}[get_thinking()]
    return (
        f"Endpunkt: {get_base_url()}\n"
        f"Modell:   {get_model()}\n"
        f"API-Key:  {'gesetzt' if get_api_key() else 'FEHLT'}\n"
        f"Thinking: {thinking}\n"
        f"Timeout:  {get_timeout():.0f} s"
    )


if __name__ == "__main__":
    # Offline-Check ohne Anfrage an den Endpunkt: python -m src.llm
    print(describe_config())
