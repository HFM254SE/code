# LeineTech Ticket-Triage: `vl04-rag-ingestion-pipeline-solution`

**Musterlösung** nach dem Lab in **VL 4 (RAG: Ingestion-Pipeline)**. Das VL-5-Lab startet auf
`vl05-rag-advanced-start`, das auf diesem Stand aufbaut. Aus den 8 Markdown-Artikeln der
LeineTech-Wissensbasis (`docs/`) wird ein durchsuchbarer Vektor-Index.

Neu gegenüber `vl04-rag-ingestion-pipeline-start` (im Lab gebaut):

| Modul | Aufgabe |
|---|---|
| `src/loader.py` | lädt die `.md`-Dokumente in ein einheitliches Format |
| `src/chunker.py` | rekursives Chunking (Absätze → Zeilen → Sätze) mit Überlappung ab einer Wortgrenze und stabilen `chunk_id`s |
| `src/embedder.py` | Embeddings mit `qwen3-embed-4b` (2560 Dimensionen) über den Kurs-Endpunkt, via litellm |
| `src/vectorstore.py` | persistente ChromaDB-Collection unter `./chroma_db` (`upsert`, Telemetrie aus) |
| `src/ingest.py` | Pipeline Dokumente → Chunks → Embeddings → ChromaDB, entfernt veraltete Chunks, Probelauf mit `--dry-run` |
| `src/search.py` | semantische Suche und Keyword-Baseline zum Vergleich, Treffer mit `chunk_id` |

Embeddings laufen wie der Chat aus VL 3 über den Kurs-Endpunkt. Dafür braucht es `LLM_BASE_URL` und
`LLM_API_KEY` in der Umgebung (siehe `SETUP.md`). Der Endpunkt ist nur montags verfügbar und hat
Cold Starts.

## Pipeline füllen

```bash
export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"      # siehe SETUP.md
python -m src.ingest docs --dry-run  # nur laden und chunken, ohne Endpunkt
python -m src.ingest docs
```

Erwartete Ausgabe von `python -m src.ingest docs`:

```
8 Dokumente geladen
80 Chunks erzeugt
80 Embeddings berechnet (2560 Dimensionen)
Collection 'leinetech_kb': 80 Einträge gespeichert
```

Die Chunk-Zahl hängt von `--chunk-size` und `--chunk-overlap` ab (Default 500 und 50 Zeichen).
Vor dem Speichern löscht die Pipeline alle alten Chunks der geladenen Quellen. So bleiben nach
einem Wechsel der Chunk-Größe keine veralteten Chunks liegen. Für Vergleiche mit anderer
Chunk-Größe eignet sich eine eigene Collection:

```bash
python -m src.ingest docs --chunk-size 1000 --collection leinetech_kb_1000
python -m src.search "VPN geht nicht" --collection leinetech_kb_1000
```

## Suchen

```bash
python -m src.search "Wie verbinde ich mich mit dem VPN?"
python -m src.search "Mein Passwort ist abgelaufen" --mode keyword
python -m src.search "Drucker druckt nicht" --n 3
```

Pro Treffer: Rang, Score, `chunk_id` und Textvorschau. Im Modus `embedding` ist der Score die
Kosinus-Ähnlichkeit, im Modus `keyword` die Anzahl gemeinsamer Wörter. Die Keyword-Suche dient dem
Vergleich. Sie findet exakte Begriffe und IDs wie `0x80042109` oder `LT-PRN-02`, kennt aber keine
Synonyme.

## Embedding-Modell

Fest eingestellt ist `qwen3-embed-4b` (2560 Dimensionen), das Embedding-Modell des Kurs-Endpunkts.
Überschreiben lässt es sich nur zu Testzwecken mit `EMBEDDING_MODEL`:

```bash
EMBEDDING_MODEL=<anderes-modell> python -m src.ingest docs --collection leinetech_kb_test
```

> **Gleiches-Modell-Regel:** Fragen und Chunks müssen mit demselben Modell eingebettet werden.
> Sonst liegen die Vektoren in verschiedenen Räumen oder haben nicht einmal dieselbe Dimension, und
> die Suche liefert Rauschen. Wer das Modell wechselt, indexiert neu: in eine eigene Collection
> oder nach dem Löschen von `chroma_db/`.

## Tests

```bash
python -m pytest -q          # 33 passed, offline, ohne Netz und ohne Key
```

- `tests/test_chunker.py`: Loader und Chunker (Satzpunkte, Zeilenstruktur, Überlappung ab Wortgrenze).
- `tests/test_pipeline_offline.py`: Embedder, Vektordatenbank, Pipeline und Suche. Eine
  Attrappe ersetzt das Embedding-Modell, ChromaDB läuft in einem temporären Ordner. Geprüft werden
  unter anderem die Reihenfolge der Vektoren, `upsert` bei vorhandener `chunk_id`, veraltete Chunks
  nach einem Größenwechsel, ein Endpunktausfall ohne Datenverlust und die Umrechnung der Distanz in
  die Kosinus-Ähnlichkeit.
- `tests/test_triage.py`: die Triage aus VL 1.

Ob der echte Endpunkt normierte Vektoren mit 2560 Dimensionen liefert, prüft der Live-Check in
`labs/vl04-lab.md` (Teil 2A).

> Hier endet der VL-4-Stand. In VL 5 kommen Augment und Generate dazu: Die hier indexierten Chunks
> gehen mit der Frage an das LLM, und aus der Suche wird ein RAG-Client.
