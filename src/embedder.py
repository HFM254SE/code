"""Embeddings — macht aus Text Vektoren, über den Kurs-Endpunkt (HomeCloud).

Wir nutzen das Embedding-Modell **`qwen3-embed-4b`** des Kurs-Endpunkts und
sprechen es — genau wie den Chat in `src/llm.py` — über **litellm** mit dem
`hosted_vllm/`-Provider an (WAF-sicher; das OpenAI-SDK würde geblockt). Base-URL
und API-Key kommen aus derselben Umgebungs-Konfiguration wie beim Chat
(`LLM_BASE_URL` / `LLM_API_KEY`, ersatzweise `OPENAI_*`, siehe SETUP.md).

Das Modell liefert **2560-dimensionale** Vektoren. Überschreiben lässt es sich
mit `EMBEDDING_MODEL`.

**Gleiches-Modell-Regel:** Query und Dokumente MÜSSEN mit demselben Modell
eingebettet werden — sonst liegen ihre Vektoren in unterschiedlichen Räumen und
die Suche wird zu Rauschen. Wer `EMBEDDING_MODEL` wechselt, muss die Collection
neu indexieren (`chroma_db/` löschen und `python -m src.ingest docs` erneut).
"""

import os

import litellm

from src.llm import get_api_key, get_base_url

litellm.telemetry = False  # keine Nutzungsdaten an litellm senden

DEFAULT_MODEL = "qwen3-embed-4b"

def get_model_name() -> str:
    """Name des Embedding-Modells aus der Umgebung, sonst Kurs-Default."""
    return os.environ.get("EMBEDDING_MODEL", DEFAULT_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Erzeugt Embeddings für eine Liste von Texten über den Kurs-Endpunkt.

    Liefert pro Eingabetext einen Vektor. Für die leere Eingabeliste kommt eine
    leere Liste zurück.
    """
    if not texts:
        return []

    response = litellm.embedding(
        model=f"hosted_vllm/{get_model_name()}",
        input=texts,
        api_base=get_base_url(),
        api_key=get_api_key(),
    )

    # Nach 'index' ordnen, damit die Reihenfolge zur Eingabe passt.
    data = sorted(response["data"], key=lambda item: item["index"])
    return [item["embedding"] for item in data]


def embed_text(text: str) -> list[float]:
    """Bequemer Einzel-Wrapper: embedded genau einen Text."""
    return embed_texts([text])[0]
