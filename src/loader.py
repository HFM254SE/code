"""Document Loader — erster Schritt der Ingestion-Pipeline.

Liest die LeineTech-Wissensbasis (`docs/`, 8 Markdown-Artikel) von der Platte
und liefert pro Datei ein einheitliches Dict {"text", "metadata"}. Die Pipeline
(loader → chunker → embedder → vectorstore) arbeitet ab hier nur noch mit
diesem Format — egal woher die Dokumente ursprünglich stammen.
"""

from pathlib import Path


def load_documents(docs_dir: str) -> list[dict]:
    """Lädt alle .md-Dateien aus docs_dir.

    Gibt eine Liste von Dicts zurück:
        [{"text": "...", "metadata": {"source": "vpn-zugang.md"}}, ...]

    Leere Dateien werden übersprungen. Sortiert nach Dateiname, damit die
    Reihenfolge (und damit die vergebenen chunk_ids) reproduzierbar ist.

    Raises:
        FileNotFoundError: wenn docs_dir nicht existiert.
    """
    base = Path(docs_dir)
    if not base.is_dir():
        raise FileNotFoundError(f"Verzeichnis nicht gefunden: {docs_dir}")

    documents = []
    for path in sorted(base.glob("*.md")):
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            continue  # leere Dateien überspringen
        documents.append(
            {
                "text": text,
                "metadata": {"source": path.name},
            }
        )
    return documents
