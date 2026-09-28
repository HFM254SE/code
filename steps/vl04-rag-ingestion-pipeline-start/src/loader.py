"""Document Loader: erster Schritt der Ingestion-Pipeline (Lab VL 4, Teil 1A).

Liest die LeineTech-Wissensbasis (`docs/`, 8 Markdown-Artikel) und liefert pro
Datei ein Dict {"text", "metadata"}. Alle weiteren Schritte (chunker, embedder,
vectorstore) arbeiten nur noch mit diesem Format.

Prüfen:
    python -m pytest tests/test_chunker.py -q -k load
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
    # TODO Teil 1A:
    #   1. Existiert Path(docs_dir) nicht als Verzeichnis: FileNotFoundError werfen.
    #   2. Alle Dateien aus sorted(Path(docs_dir).glob("*.md")) durchgehen.
    #   3. Inhalt mit read_text(encoding="utf-8") lesen und strip() anwenden.
    #      Leere Dateien überspringen.
    #   4. Pro Datei {"text": text, "metadata": {"source": path.name}} anhängen.
    raise NotImplementedError("TODO Teil 1A: load_documents in src/loader.py")
