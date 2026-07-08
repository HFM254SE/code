# LeineTech Ticket-Triage — `vl04-rag-ingestion-pipeline-start`

Ausgangszustand für das **Lab in VL 4 (RAG: Ingestion-Pipeline)**.

Aufgesetzt auf dem VL-3-Stand (LLM-Anschluss + Evaluierung). Das Triage-Tool
läuft wie gehabt; die **Ingestion-Pipeline für RAG existiert noch nicht** — die
baut ihr im Lab. Aus den 8 Markdown-Artikeln der LeineTech-Wissensbasis (`docs/`)
soll ein durchsuchbarer Vektor-Index werden: die Grundlage für den RAG-Chatbot
in VL 5.

**Was schon da ist (aus VL 3):**

- `src/llm.py` — litellm-Wrapper gegen den **Kurs-Endpunkt** (HomeCloud). Liefert
  `get_base_url()` / `get_api_key()`, die ihr fürs Embedding wiederverwendet.
- `src/summarize.py`, `src/triage.py`, `src/stats.py`, `src/ticket_loader.py`,
  `src/main.py` — das bestehende Triage-Tool.

**Was ihr im Lab baut** (Schritt für Schritt in `labs/vl04-lab.md`):

- `src/loader.py` — lädt die `.md`-Dokumente in ein einheitliches Format.
- `src/chunker.py` — **rekursives Chunking** (Absätze → Zeilen → Sätze) mit
  Überlappung und stabilen `chunk_id`s. `tests/test_chunker.py` ist die Vorgabe:
  am Anfang rot, am Ende grün.
- `src/embedder.py` — Embeddings mit `qwen3-embed-4b` (2560 Dim.) über den
  Kurs-Endpunkt, via litellm — dieselbe Anbindung wie der Chat.
- `src/vectorstore.py` — persistente **ChromaDB**-Collection unter `./chroma_db`.
- `src/ingest.py` — die Pipeline **Dokumente → Chunks → Embeddings → ChromaDB**.
- `src/search.py` — semantische Suche + Keyword-Baseline zum Vergleich.

Embeddings laufen — wie Chat/Klassifikation (`src/llm.py`, VL 3) — über den
Kurs-Endpunkt. Es braucht also `LLM_BASE_URL` / `LLM_API_KEY` in der Umgebung
(siehe SETUP.md); der Endpunkt ist nur montags verfügbar und hat Cold Starts.

## Ausführen

```bash
pip install -r requirements.txt
export LLM_BASE_URL="https://llm.homecloud.ee/v1"   # Kurs-Endpunkt, siehe SETUP.md
export LLM_API_KEY="<euer-key>"

python -m src.main triage          # bestehendes Triage-Tool (Stand VL 3)
pytest                             # test_chunker.py ist rot, bis ihr loader/chunker baut
```

## Struktur

```
docs/                  8 Markdown-Artikel der LeineTech-Wissensbasis (Wissensquelle)
data/tickets.json      Support-Tickets (aus VL 1)
src/                   VL-3-Tool — hier entstehen loader/chunker/embedder/…
tests/test_chunker.py  Vorgabe für loader + chunker (offline, kein Netz nötig)
labs/vl04-lab.md       Schritt-für-Schritt-Anleitung für das Lab
```

> Das fertige Ergebnis liegt in `vl04-rag-ingestion-pipeline-solution`. In VL 5
> kommt der **Augment + Generate**-Schritt dazu: Die hier indexierten Chunks
> werden dem LLM als Kontext übergeben — aus der Suche wird ein RAG-Chatbot.
