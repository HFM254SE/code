# LeineTech Ticket-Triage: `vl05-rag-advanced-solution`

**Musterlösung nach dem Lab in VL 5 (RAG: Advanced).** Aus der Such-Pipeline von VL 4 ist ein
RAG-Client geworden: Retrieve → Augment → Generate. Die hybride Suche verbessert das Retrieval, und
ein kleines Evalset misst, ob das stimmt.

Die Lab-Anleitung steht in `labs/vl05-lab.md`.

## Neu gegenüber `vl05-rag-advanced-start`

| Datei | Inhalt |
|---|---|
| `src/rag.py` | RAG-Client: Kontextblock mit Zitat-Labels, System-Prompt mit Grounding, fester Enthaltung und Zitierpflicht. Retriever umschaltbar (`--retriever dense\|keyword\|hybrid`). |
| `src/hybrid.py` | Hybride Suche: dichte Suche und Keyword-Suche parallel, fusioniert per Reciprocal Rank Fusion (k = 60) |
| `src/rag_eval.py` | zusätzlich die beiden Judges: Faithfulness (Einzelurteile als JSON, Quote in Python) und Answer Relevancy |
| `tests/test_judge.py` | Tests für die Judges mit Fake-LLM |

`eval/rag_eval.jsonl`, die Vorlagen in `labs/templates/` und die übrigen Tests sind identisch mit
dem Start-Branch.

## Voraussetzung: Index füllen

```bash
export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"              # siehe SETUP.md
python -m src.ingest docs                    # 8 Dokumente, 80 Chunks
```

Das Ingest ersetzt alle Chunks jeder Datei. Fällt der Endpunkt aus, bleibt der alte Index
erhalten. Den Ordner `chroma_db/` löscht ihr nur, wenn Chunks von Dateien liegen bleiben, die es
nicht mehr gibt, oder wenn der Index mit einem anderen Embedding-Modell gebaut wurde
(Troubleshooting in `labs/vl05-lab.md`).

Der Endpunkt ist nur montags von 06:00 bis 23:59 Uhr erreichbar und hat Cold Starts von 200 bis
300 Sekunden. `chat()` bricht per Default nach 120 s ab. Für die erste Chat-Anfrage des Tages
deshalb vorher `export LLM_TIMEOUT=360` setzen.

## Fragen beantworten

```bash
python -m src.rag "Wie lange bleibt die VPN-Verbindung bestehen?"
python -m src.rag "Welche Durchwahl hat Bernd Hagedorn?" --retriever hybrid --n 3
python -m src.rag "Wie viele Urlaubstage habe ich pro Jahr?"     # Enthaltung
```

Die Ausgabe zeigt die Antwort und die Quellenliste mit Labels (`[Quelle 1] vpn-zugang.md`). Für
Experimente nimmt `answer()` einen eigenen System-Prompt an, z. B. ohne Enthaltungsanweisung:
`answer(frage, system_prompt="...")`.

## Hybride Suche

```bash
python -m src.hybrid "Welche Durchwahl hat Bernd Hagedorn?" --n 3
```

Die dichte Suche findet Bedeutung, auch bei Umschreibungen. Seltene exakte Begriffe in der Frage
gewichtet sie oft zu schwach, etwa Namen („Hagedorn“), Fehlercodes („MSI-Code 1603“,
„0x80042109“) oder Gerätenummern. Die Keyword-Suche trifft genau diese Begriffe, kennt aber keine
Synonyme. RRF fusioniert beide Ranglisten nur über die Ränge. Eine Normalisierung der Scores ist
nicht nötig. Keyword-Suche hilft nur, wenn der seltene Begriff in der Frage steht.

## Evaluieren

```bash
python -m src.rag_eval --retrieval-only --retriever keyword --n 3   # ohne Chat, Sekunden
python -m src.rag_eval --retrieval-only --retriever hybrid --n 3
python -m src.rag_eval --retriever hybrid --n 3                     # mit Antworten und Judges
python -m src.rag_eval --retriever hybrid --n 3 --details           # plus Einzelurteile
```

Das Evalset hat 17 Fragen in vier Typen: einfach, schwer (mehrere Teilfakten), keyword (die Frage
enthält einen seltenen, exakten Begriff) und unbeantwortbar. Der Report nennt Zählungen:

- **Datei-Treffer:** Stammt ein Chunk der Top-k aus der erwarteten Datei?
- **Beleg-Treffer:** Stehen alle Belegstellen (`evidence`) in abgerufenen Chunks der erwarteten
  Datei? Das ist eine grobe, deterministische Näherung an Context Recall. Chunks aus anderen
  Dateien zählen nicht, damit ein Ablenker wie „2 Stunden“ bei den Leihgeräten nicht als Beleg
  für die SLA-Frage gilt.
- **Enthaltung korrekt** bei unbeantwortbaren und **fälschliche Enthaltung** bei beantwortbaren Fragen.
- **Faithfulness** und **Answer Relevancy** als Mittelwert über echte Antworten. Nicht verwertbare
  Judge-Antworten zählen als nicht bewertet, nicht als 0 oder 1.

Die Judge-Werte sind Richtungssignale zum Vergleich von Konfigurationen, keine absolute Wahrheit.
Das Kursmodell bewertet hier seine eigenen Antworten (Selbstverstärkungsbias). Bei 14 beantwortbaren
Fragen verschiebt jede einzelne Frage das Ergebnis um rund 7 Prozentpunkte. Richtwerte:
Faithfulness über 0,8 stark, unter 0,5 bedenklich. Answer Relevancy über 0,8 stark, unter 0,6
bedenklich.

Der Faithfulness-Judge ist eine vereinfachte Form des RAGAS-Verfahrens. RAGAS braucht dafür zwei
Aufrufe: einen zum Zerlegen der Antwort in Aussagen und einen zum Prüfen jeder Aussage. Hier
erledigt ein Aufruf beides. Gleich bleibt: Das Modell urteilt pro Aussage, die Quote rechnet
Python. Answer Relevancy ist ein direkter Judge. RAGAS erzeugt stattdessen Fragen aus der Antwort
und vergleicht sie per Embedding mit der Originalfrage.

> **Optional: „echtes“ RAGAS.** In Produktion nimmt man ein Framework wie `ragas`. Es ist bewusst
> nicht in `requirements.txt`, damit das Lab ohne neue Abhängigkeit läuft. Wer es nutzt,
> installiert es selbst und pinnt die Version. Stand September 2026 (ragas 0.4.x) liegen die
> Metriken in `ragas.metrics.collections`. Die alte Funktion `evaluate()` gilt als veraltet und
> lässt sich nicht mit den neuen Metriken mischen. Vor der Nutzung die aktuelle Doku prüfen.

## Tests

```bash
python -m pytest -q          # erwartet: alles grün, kein skipped (offline, ohne Endpunkt)
```

| Testdatei | prüft |
|---|---|
| `tests/test_rag.py` | Kontextblock, Prompt-Reihenfolge, Rückgabeformat, Enthaltung ohne LLM-Aufruf |
| `tests/test_hybrid.py` | RRF-Formel, Folienbeispiel A·B·D·C·E, Wirkung von k, Quelle und `chunk_id` bleiben erhalten, `hybrid_search` mit Attrappen |
| `tests/test_rag_eval.py` | Evalset-Format, Belegstellen gegen `docs/`, echte Umlaute, Beleg- und Datei-Treffer, Ablenker aus anderer Datei, Enthaltung |
| `tests/test_judge.py` | Auslesen der Judge-Antworten (JSON, Denkblöcke, Plaudertext), Quote, unklare Einzelurteile wie „teilweise“, Report |

Dazu laufen unverändert die Tests aus VL 1 (`tests/test_triage.py`) und VL 4
(`tests/test_chunker.py`, `tests/test_pipeline_offline.py`) mit.

Die netzabhängigen Teile (Embeddings, echte Antworten) prüft ihr im Lab mit dem Endpunkt.
