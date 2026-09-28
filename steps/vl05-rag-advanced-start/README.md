# LeineTech Ticket-Triage: `vl05-rag-advanced-start`

**Startpunkt für das Lab in VL 5 (RAG: Advanced).** Der Code entspricht der Musterlösung von VL 4:
Die LeineTech-Wissensbasis (`docs/`, 8 Artikel) wird geladen, gechunkt, eingebettet und in
ChromaDB durchsucht. Heute wird aus der Trefferliste ein RAG-Client, der belegt antwortet. Danach
kommt die hybride Suche dazu.

Die Anleitung steht in **`labs/vl05-lab.md`**. Sie funktioniert auch ohne Vorlesung zum
Nacharbeiten.

## Neu gegenüber `vl04-rag-ingestion-pipeline-solution`

| Datei | Zweck |
|---|---|
| `labs/vl05-lab.md` | Lab-Anleitung mit Zeitplan, Checkpoints und Troubleshooting |
| `labs/templates/rag_skeleton.py` | Vorlage für den RAG-Client (Teil 1), wird nach `src/rag.py` kopiert |
| `labs/templates/hybrid_skeleton.py` | Vorlage für die hybride Suche mit RRF (Teil 2), wird nach `src/hybrid.py` kopiert |
| `src/rag_eval.py` | Messwerkzeug. `--retrieval-only` ist fertig (Teil 2) und läuft, sobald `src/rag.py` aus Teil 1 existiert. Die Judge-Funktionen sind TODO (Vertiefung). |
| `eval/rag_eval.jsonl` | Evalset: 17 Fragen in vier Typen (einfach, schwer, keyword, unbeantwortbar) mit Belegstellen |
| `tests/test_rag.py`, `tests/test_hybrid.py`, `tests/test_rag_eval.py` | Selbsttests ohne Endpunkt. Sie werden übersprungen, solange die Lab-Dateien fehlen. |

Unverändert aus VL 4 übernommen sind die sechs Pipeline-Module in `src/` und ihre Tests
(`tests/test_chunker.py`, `tests/test_pipeline_offline.py`). Sie laufen offline mit und
schützen die Pipeline, falls ihr in VL 5 daran etwas ändert.

## Schnellstart

```bash
git checkout vl05-rag-advanced-start
source .venv/bin/activate                    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q                          # erwartet: kein failed, genau 3 skipped

export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"              # siehe SETUP.md
python -m src.ingest docs                    # 8 Dokumente, 80 Chunks
python -m src.search "Wie verbinde ich mich mit dem VPN?" --n 3
```

Ein alter Index aus VL 4 stört nicht. Das Ingest ersetzt alle Chunks jeder Datei. Fällt der
Endpunkt aus, bleibt der alte Index erhalten. Wann `chroma_db/` doch gelöscht werden muss, steht im
Troubleshooting der Lab-Anleitung.

## Was ihr im Lab baut

| Teil | Aufgabe | Selbsttest ohne Endpunkt |
|---|---|---|
| 1 | `src/rag.py`: System-Prompt, Kontextblock mit `[Quelle N \| datei.md]`, `answer()` | `python -m pytest tests/test_rag.py -q` |
| 2 | `src/hybrid.py`: Reciprocal Rank Fusion und `hybrid_search()` | `python -m pytest tests/test_hybrid.py -q` |
| 2 | Messung dense, keyword und hybrid mit `python -m src.rag_eval --retrieval-only --n 3` | Keyword-Zeile läuft ohne Endpunkt |
| Bonus | Faithfulness- und Relevanz-Judge in `src/rag_eval.py` (TODO V1, V2) | `git checkout origin/vl05-rag-advanced-solution -- tests/test_judge.py`, dann `python -m pytest tests/test_judge.py -q` |

Die Vorlagen laufen bis zum ersten offenen TODO und melden sich dann mit
`NotImplementedError: TODO …`.

## Kurs-Endpunkt

Chat und Embeddings laufen über den Kurs-Endpunkt (HomeCloud), wie seit VL 3 und VL 4. Es braucht
`LLM_BASE_URL` und `LLM_API_KEY` in der Umgebung (siehe `SETUP.md`). Der Endpunkt ist nur montags
von 06:00 bis 23:59 Uhr erreichbar. Die erste Anfrage kann durch den Cold Start 200 bis 300 Sekunden
dauern. `chat()` bricht per Default nach 120 s ab. Für die erste Chat-Anfrage des Tages deshalb
vorher `export LLM_TIMEOUT=360` setzen.

## Musterlösung

```bash
git checkout vl05-rag-advanced-solution
```

Dort sind `src/rag.py`, `src/hybrid.py` und beide Judges in `src/rag_eval.py` fertig.
