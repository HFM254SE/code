# LeineTech Ticket-Triage — `vl04-rag-ingestion-pipeline-solution`

**Musterlösung** nach dem Lab in **VL 4 (RAG: Ingestion-Pipeline)** — und
zugleich der **Startpunkt für VL 5**. Aus den 8 Markdown-Artikeln der
LeineTech-Wissensbasis (`docs/`) wird ein durchsuchbarer Vektor-Index.

Neu gegenüber `vl04-rag-ingestion-pipeline-start` (im Lab gebaut):

- `src/loader.py` — lädt die `.md`-Dokumente in ein einheitliches Format.
- `src/chunker.py` — **rekursives Chunking** (Absätze → Zeilen → Sätze) mit
  Überlappung und stabilen `chunk_id`s.
- `src/embedder.py` — Embeddings mit `qwen3-embed-4b` (2560 Dim.) über den
  **Kurs-Endpunkt (HomeCloud)**, via litellm — dieselbe Anbindung wie der Chat.
- `src/vectorstore.py` — persistente **ChromaDB**-Collection unter `./chroma_db`
  (idempotentes `upsert`).
- `src/ingest.py` — verbindet alles zur Pipeline **Dokumente → Chunks →
  Embeddings → ChromaDB**.
- `src/search.py` — semantische Suche + Keyword-Baseline zum Vergleich.

Embeddings laufen — wie Chat/Klassifikation (`src/llm.py`, VL 3) — über den
Kurs-Endpunkt. Es braucht also `LLM_BASE_URL` / `LLM_API_KEY` in der Umgebung
(siehe SETUP.md); der Endpunkt ist nur montags verfügbar und hat Cold Starts.

## Pipeline füllen

```bash
export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"      # siehe SETUP.md
python -m src.ingest docs
```

Erwartete Ausgabe (ungefähr):

```
8 Dokumente geladen
80 Chunks erzeugt
80 Embeddings berechnet (2560 Dimensionen)
Collection 'leinetech_kb': 80 Einträge gespeichert
```

*(Die genaue Chunk-Zahl hängt von `--chunk-size`/`--chunk-overlap` ab —
mit den Defaults 500/50 sind es ~80.)*

## Suchen

```bash
python -m src.search "Wie verbinde ich mich mit dem VPN?"
python -m src.search "Mein Passwort ist abgelaufen" --mode keyword
python -m src.search "Drucker druckt nicht" --n 3
```

Pro Treffer: **Rang, Ähnlichkeitswert, Quelle, Textvorschau**. Der `keyword`-Modus
(reine Wortüberlappung) dient dem Vergleich — er gewinnt bei exakten Fachbegriffen,
verliert bei Synonymen und Umschreibungen.

## Embedding-Modell

Fest verdrahtet ist `qwen3-embed-4b` (2560 Dim.), das einzige Embedding-Modell
des Kurs-Endpunkts. Überschreiben nur zu Testzwecken mit `EMBEDDING_MODEL`:

```bash
EMBEDDING_MODEL=<anderes-modell> python -m src.ingest docs
```

> **Gleiches-Modell-Regel:** Query und Chunks müssen mit demselben Modell
> eingebettet werden — sonst liegen die Vektoren in unterschiedlichen Räumen
> (oder haben nicht mal dieselbe Dimension) und die Suche wird zu Rauschen. Wer
> `EMBEDDING_MODEL` wechselt, muss die Collection neu indexieren: `chroma_db/`
> löschen und `python -m src.ingest docs` erneut ausführen.

## Tests

```bash
pytest                      # Loader/Chunker (offline, kein Netz/Endpunkt nötig)
```

Die Tests decken Laden und Chunking ab — die netzabhängigen Schritte (Embedding
über HomeCloud, ChromaDB) werden im Lab manuell geprüft (siehe `labs/vl04-lab.md`).

> Hier endet der VL-4-Stand. In VL 5 kommt der **Augment + Generate**-Schritt
> dazu: Die hier indexierten Chunks werden dem LLM als Kontext übergeben — aus
> der Suche wird ein RAG-Chatbot.
