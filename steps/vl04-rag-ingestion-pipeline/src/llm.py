"""Zentraler LLM-Zugriff über die OpenAI-kompatible API.

Standardmäßig wird ein lokales Modell über Ollama angesprochen
(http://localhost:11434/v1). Über Umgebungsvariablen lässt sich derselbe
Code gegen jedes OpenAI-kompatible Backend schalten — Cloud oder self-hosted:

    LLM_BASE_URL   z. B. https://api.openai.com/v1 (Default: lokales Ollama)
    LLM_API_KEY    API-Key des Anbieters (Default: "ollama" — wird von Ollama
                   nicht geprüft, der Client verlangt aber einen Wert)
    LLM_MODEL      Modellname, z. B. "llama3.2", "qwen2.5:3b", "gpt-5"
"""

import os
from openai import OpenAI
from dotenv_loader import load_env

load_env(steps_to_project_root=1)

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3.2"

SYSTEM_PROMPT = (
    "Du bist ein präziser Assistent für den IT-Support der LeineTech GmbH. "
    "Antworte knapp, sachlich und auf Deutsch."
)

def get_client() -> OpenAI:
    """Erzeugt einen OpenAI-Client für das konfigurierte Backend."""
    api_key = os.environ.get("LLM_API_KEY", "ollama")
    return OpenAI(
        base_url=os.environ.get("LLM_BASE_URL", DEFAULT_BASE_URL),
        api_key=api_key,
        default_headers={
            "x-litellm-api-key": api_key,
            "User-Agent": "python-httpx",
        },
    )


def get_model() -> str:
    """Liefert den konfigurierten Modellnamen."""
    return os.environ.get("LLM_MODEL", DEFAULT_MODEL)


def chat(
    prompt: str,
    system: str = SYSTEM_PROMPT,
    model: str | None = None,
    temperature: float = 0.0,
) -> str:
    """Schickt einen einzelnen Prompt an das LLM und liefert die Antwort."""
    client = get_client()
    response = client.chat.completions.create(
        model=model or get_model(),
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content or ""
