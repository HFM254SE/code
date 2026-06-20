"""Zentraler LLM-Zugriff über die OpenAI-kompatible API.

Standardmäßig wird ein lokales Modell über Ollama angesprochen
(http://localhost:11434/v1). Über Umgebungsvariablen lässt sich derselbe
Code gegen jedes OpenAI-kompatible Backend schalten — Cloud oder self-hosted:

    LLM_BASE_URL   z. B. https://api.openai.com/v1 (Default: lokales Ollama)
    LLM_API_KEY    API-Key des Anbieters (Default: "ollama" — wird von Ollama
                   nicht geprüft, der Client verlangt aber einen Wert)
    LLM_MODEL      Modellname, z. B. "llama3.2", "qwen2.5:3b", "gpt-5"

Als Fallback werden OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL gelesen
(LLM_* hat Vorrang), damit auch die Standard-Variablen aus SETUP.md greifen.
"""

import os

from openai import OpenAI

DEFAULT_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MODEL = "llama3.2"

SYSTEM_PROMPT = (
    "Du bist ein präziser Assistent für den IT-Support der LeineTech GmbH. "
    "Antworte knapp, sachlich und auf Deutsch."
)


def get_client() -> OpenAI:
    """Erzeugt einen OpenAI-Client für das konfigurierte Backend."""
    return OpenAI(
        base_url=os.environ.get("LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL") or DEFAULT_BASE_URL,
        api_key=os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY") or "ollama",
    )


def get_model() -> str:
    """Liefert den konfigurierten Modellnamen."""
    return os.environ.get("LLM_MODEL") or os.environ.get("OPENAI_MODEL") or DEFAULT_MODEL


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
