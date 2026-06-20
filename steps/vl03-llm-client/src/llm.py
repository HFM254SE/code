"""Zentraler LLM-Zugriff über den Kurs-Endpunkt (Nortal HomeCloud).

Der Endpunkt ist ein **LiteLLM-Gateway** vor einem vLLM-Node und OpenAI-kompatibel.
Wir sprechen ihn über die **litellm**-Library an — NICHT über das OpenAI-SDK:
Der WAF vor dem Gateway blockt den User-Agent des OpenAI-SDK ("OpenAI/Python").
litellm mit dem `hosted_vllm/`-Provider nutzt einen eigenen HTTP-Client und
kommt sauber durch.

Konfiguration über Umgebungsvariablen (siehe SETUP.md):

    LLM_BASE_URL / OPENAI_BASE_URL   Gateway-URL **inkl. /v1**
    LLM_API_KEY  / OPENAI_API_KEY    persönlicher API-Key
    LLM_MODEL    / OPENAI_MODEL       Modellname (Default: qwen3.6-35B-A3B-FP8)

LLM_* hat jeweils Vorrang vor OPENAI_*, damit die Standard-Variablen aus
SETUP.md ohne Zusatzaufwand greifen.
"""

import os

import litellm

litellm.telemetry = False  # keine Nutzungsdaten an litellm senden

DEFAULT_BASE_URL = "https://llm.homecloud.ee/v1"
DEFAULT_MODEL = "qwen3.6-35B-A3B-FP8"

SYSTEM_PROMPT = (
    "Du bist ein präziser Assistent für den IT-Support der LeineTech GmbH. "
    "Antworte knapp, sachlich und auf Deutsch."
)


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


def _provider_model(model: str) -> str:
    """Stellt litellm das richtige Provider-Präfix voran.

    `hosted_vllm/` weist litellm an, den OpenAI-kompatiblen vLLM-Endpunkt mit
    seinem eigenen HTTP-Client anzusprechen (statt über das OpenAI-SDK, dessen
    User-Agent der WAF blockt). Ein bereits präfixierter Name bleibt unangetastet.
    """
    return model if "/" in model else f"hosted_vllm/{model}"


def chat(
    prompt: str,
    system: str = SYSTEM_PROMPT,
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    """Schickt einen einzelnen Prompt an das LLM und liefert die Antwort.

    temperature=0.0 ist hier Default: Für Klassifikation und Zusammenfassung
    wollen wir reproduzierbare, nüchterne Antworten (vgl. VL 2/VL 3).
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
    )
    return response.choices[0].message.content or ""
