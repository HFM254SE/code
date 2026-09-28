# LeineTech Ticket-Triage: `vl04-rag-ingestion-pipeline-start`

Ausgangszustand für das **Lab in VL 4 (RAG: Ingestion-Pipeline)**.

Das Triage-Tool aus VL 1 sowie LLM-Anschluss und Evaluierung aus VL 3 laufen wie gehabt. Neu ist
das Gerüst der Ingestion-Pipeline: Aus den 8 Markdown-Artikeln der LeineTech-Wissensbasis (`docs/`)
soll ein durchsuchbarer Vektor-Index werden. Das ist die Grundlage für den RAG-Client in VL 5.

**Was schon da ist:**

- `src/llm.py` aus VL 3: litellm-Wrapper für den Kurs-Endpunkt (HomeCloud). Liefert
  `get_base_url()` und `get_api_key()`, die ihr für das Embedding wiederverwendet.
- `src/evaluate.py` aus VL 3: vergleicht Keyword-Regeln und LLM auf dem Golden Dataset
  (`eval/golden.jsonl`).
- `src/summarize.py`, `src/triage.py`, `src/stats.py`, `src/ticket_loader.py`, `src/main.py`:
  das bestehende Triage-Tool.

**Was ihr im Lab ergänzt** (Schritt für Schritt in `labs/vl04-lab.md`). Jedes Modul ist ein Gerüst.
Die offenen Stellen sind mit `TODO Teil …` markiert und werfen bis dahin einen `NotImplementedError`.

| Modul | Aufgabe | Lab-Teil |
|---|---|---|
| `src/loader.py` | lädt die `.md`-Dokumente in ein einheitliches Format | 1A |
| `src/chunker.py` | rekursives Chunking (Absätze → Zeilen → Sätze) mit Überlappung und stabilen `chunk_id`s | 1B |
| `src/embedder.py` | Embeddings mit `qwen3-embed-4b` (2560 Dimensionen) über den Kurs-Endpunkt | 2A |
| `src/vectorstore.py` | persistente ChromaDB-Collection unter `./chroma_db` | 2B |
| `src/ingest.py` | die Pipeline Dokumente → Chunks → Embeddings → ChromaDB, mit `--dry-run` | 2C |
| `src/search.py` | semantische Suche, dazu eine fertige Keyword-Baseline zum Vergleich | 3A |

Embeddings laufen wie der Chat aus VL 3 über den Kurs-Endpunkt. Dafür braucht es `LLM_BASE_URL` und
`LLM_API_KEY` in der Umgebung (siehe `SETUP.md`). Der Endpunkt ist nur montags verfügbar und hat
Cold Starts. Die Tests laufen dagegen offline.

## Ausführen

```bash
pip install -r requirements.txt
export LLM_BASE_URL="https://llm.homecloud.ee/v1"   # Kurs-Endpunkt, siehe SETUP.md
export LLM_API_KEY="<euer-key>"

python -m src.main triage          # bestehendes Triage-Tool (Stand VL 3)
python -m pytest -q --tb=line      # am Anfang: 28 failed, 5 passed (gewollt, siehe unten)
grep -n "TODO Teil" src/*.py       # alle offenen Stellen
```

## Tests

Die Tests sind die Vorgabe für das Lab und brauchen weder Netz noch Key:

- `tests/test_chunker.py` (13 Tests): Loader und Chunker, Teil 1.
- `tests/test_pipeline_offline.py` (15 Tests): Embedder, Vektordatenbank, Pipeline und Suche mit
  einer Embedding-Attrappe, Teil 2 und 3. Die Testnamen tragen den Lab-Teil, z. B. `-k teil2a`.
- `tests/test_triage.py` (5 Tests): die Triage aus VL 1, von Anfang an grün.

Direkt nach dem Checkout sind 28 Tests rot. Das ist gewollt: Jeder rote Test zeigt auf ein TODO.
Mit `--tb=line` steht pro Test eine Zeile mit `NotImplementedError: TODO Teil …`. Am Ende des Labs
laufen alle 33 Tests grün.

## Struktur

```
docs/                          8 Markdown-Artikel der LeineTech-Wissensbasis (Wissensquelle)
data/tickets.json              Support-Tickets (aus VL 1), darunter T-1018
src/                           VL-3-Tool plus Pipeline-Gerüst mit TODOs
tests/test_chunker.py          Vorgabe für Loader und Chunker (offline)
tests/test_pipeline_offline.py Vorgabe für Embedder, Vektordatenbank, Pipeline und Suche (offline)
labs/vl04-lab.md               Schritt-für-Schritt-Anleitung für das Lab
labs/vl04-testfragen.txt       die neun Testfragen für die Messung in Teil 3
```

> Das fertige Ergebnis liegt in `vl04-rag-ingestion-pipeline-solution`. In VL 5 kommen Augment und
> Generate dazu: Die hier indexierten Chunks gehen mit der Frage an das LLM, und aus der Suche wird
> ein RAG-Client.
