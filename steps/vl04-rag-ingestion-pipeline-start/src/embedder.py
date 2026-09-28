"""Embeddings: macht aus Text Vektoren, über den Kurs-Endpunkt (Lab VL 4, Teil 2A).

Wir nutzen das Embedding-Modell `qwen3-embed-4b` des Kurs-Endpunkts. Es wird
wie der Chat in `src/llm.py` über litellm mit dem Provider `hosted_vllm/`
angesprochen, weil die WAF vor dem Gateway das OpenAI-SDK blockt. Base-URL
und API-Key kommen aus derselben Konfiguration wie beim Chat (`LLM_BASE_URL`,
`LLM_API_KEY`, siehe SETUP.md). Das Modell liefert Vektoren mit 2560
Dimensionen.

Gleiches-Modell-Regel: Fragen und Chunks müssen mit demselben Modell
eingebettet werden. Wer `EMBEDDING_MODEL` ändert, muss neu indexieren.

Prüfen (offline, mit Attrappe):
    python -m pytest tests/test_pipeline_offline.py -q -k teil2a
"""

import os

# litellm lädt beim Import sonst eine Preisliste aus dem Internet nach. Wir
# bleiben lokal: Das startet schneller, funktioniert offline und schickt keine
# unnötigen Requests. Die Variable muss VOR dem Import gesetzt sein.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import litellm  # noqa: E402  pylint: disable=wrong-import-position

from src.llm import get_api_key, get_base_url  # noqa: E402  pylint: disable=wrong-import-position

litellm.telemetry = False  # keine Nutzungsdaten an litellm senden

DEFAULT_MODEL = "qwen3-embed-4b"


def get_model_name() -> str:
    """Name des Embedding-Modells aus `EMBEDDING_MODEL`, sonst der Kurs-Default."""
    return os.environ.get("EMBEDDING_MODEL", DEFAULT_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Bettet eine Liste von Texten mit einem einzigen Aufruf am Kurs-Endpunkt ein.

    Liefert pro Text einen Vektor in Eingabereihenfolge. Eine leere Liste
    ergibt eine leere Liste, ohne Netzaufruf.
    """
    # TODO Teil 2A:
    #   1. Leere Eingabe: sofort [] zurückgeben.
    #   2. response = litellm.embedding(
    #          model=f"hosted_vllm/{get_model_name()}",
    #          input=texts,
    #          api_base=get_base_url(),
    #          api_key=get_api_key(),
    #      )
    #   3. Die Einträge in response["data"] nach item["index"] sortieren und die
    #      Vektoren item["embedding"] als Liste zurückgeben.
    raise NotImplementedError("TODO Teil 2A: embed_texts in src/embedder.py")


def embed_text(text: str) -> list[float]:
    """Bettet genau einen Text ein (z. B. die Suchanfrage)."""
    return embed_texts([text])[0]
