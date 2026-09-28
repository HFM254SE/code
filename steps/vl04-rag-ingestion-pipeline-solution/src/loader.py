"""Document Loader: erster Schritt der Ingestion-Pipeline.

Liest die LeineTech-Wissensbasis (`docs/`, 8 Markdown-Artikel) und liefert pro
Datei ein Dict {"text", "metadata"}. Alle weiteren Schritte (chunker, embedder,
vectorstore) arbeiten nur noch mit diesem Format. Käme ein Dokument aus einem
PDF oder Wiki, müsste nur der Loader angepasst werden.
"""

from pathlib import Path


def load_documents(docs_dir: str | Path) -> list[dict]:
    """Lädt alle .md-Dateien aus docs_dir, sortiert nach Dateiname.

    Rückgabe: [{"text": "...", "metadata": {"source": "vpn-zugang.md"}}, ...]

    Leere Dateien werden übersprungen. Die feste Sortierung macht die
    Reihenfolge und damit die chunk_ids reproduzierbar.

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
            continue
        documents.append({"text": text, "metadata": {"source": path.name}})
    return documents
