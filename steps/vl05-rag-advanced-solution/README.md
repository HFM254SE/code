# LeineTech Ticket-Triage — `vl05-rag-advanced-solution`

**Musterlösung** nach dem Lab in **VL 5 (Advanced RAG)**. Aus der Such-Pipeline
von VL 4 wird ein **vollständiger RAG-Chatbot**: Retrieve → **Augment →
Generate** — und mit **hybrider Suche** besser rankendes Retrieval.

Neu gegenüber `vl05-rag-advanced-start` (im Lab gebaut):

- `src/rag.py` — der **RAG-Client**: Kontextblock mit Quellen-Labels bauen
  (Augment), geerdeter Prompt (Grounding + Zitierpflicht + Enthaltung) an das
  LLM (Generate). Retriever umschaltbar: `--retriever dense|hybrid`.
- `src/hybrid.py` — **hybride Suche**: dichte Vektorsuche + Keyword-Suche,
  selbst fusioniert per **Reciprocal Rank Fusion** (RRF).
- `src/rag_eval.py` — **Evaluation per LLM-as-Judge** (die RAG-Triade:
  Kontext-Treffer, Faithfulness, Answer Relevancy); vergleicht dense vs. hybrid.
  *(Vertiefung — im Lab optional.)*
- `eval/rag_eval.jsonl` — kleines Evalset (einfach / schwer / unbeantwortbar).

Alles läuft — wie Chat/Embeddings seit VL 3/4 — über den **Kurs-Endpunkt
(HomeCloud)**. Es braucht `LLM_BASE_URL` / `LLM_API_KEY` in der Umgebung
(siehe SETUP.md); der Endpunkt ist nur montags verfügbar und hat Cold Starts.

## Voraussetzung: Index füllen

```bash
export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"      # siehe SETUP.md
python -m src.ingest docs            # Wissensbasis nach ./chroma_db indexieren
```

## Fragen beantworten (RAG)

```bash
python -m src.rag "Wie lange bleibt die VPN-Verbindung bestehen?"
python -m src.rag "Nenne alle Voraussetzungen fürs VPN." --retriever hybrid
python -m src.rag "Welches Gateway trage ich für Cisco Secure Client ein?" --retriever hybrid
python -m src.rag "Wie viele Urlaubstage habe ich?"   # → Enthaltung (nicht im Korpus)
```

Ausgabe: die generierte Antwort **plus** die zitierten Quellen. Die
Enthaltungsanweisung sorgt dafür, dass unbeantwortbare Fragen ein ehrliches
„Ich habe dazu keine Information in der Wissensbasis" bekommen statt einer
selbstbewussten Halluzination.

## Hybride Suche direkt

```bash
python -m src.hybrid "Welches Gateway trage ich für Cisco Secure Client ein?"
```

Dense allein ist „keyword-blind" (verfehlt exakte Codes/Namen wie
`vpn.leinetech.de` oder `LT-PRN-02`), Keyword allein kennt keine Synonyme. RRF
kombiniert beide Ranglisten **ohne Score-Normalisierung** — es zählt nur die
Ränge; was in beiden Listen auftaucht, steigt nach oben.

## Evaluieren (LLM-as-Judge) — Vertiefung

```bash
python -m src.rag_eval                              # Baseline: dense
python -m src.rag_eval --retriever hybrid
```

Misst die **RAG-Triade** und gibt Durchschnitte aus. Das ist das Verfahren
hinter RAGAS (**LLM-as-Judge**) — die Zahlen sind **Richtungssignale zum
Vergleich von Konfigurationen**, keine absolute Wahrheit (Positions-,
Ausführlichkeits-, Selbstverstärkungsbias). Richtwerte: Faithfulness > 0.8
stark / < 0.5 bedenklich, Answer Relevancy > 0.8 stark / < 0.6 bedenklich.

Im Lab ist die Evaluation als **Vertiefung** ausgewiesen (freiwillig) — die
Musterlösung liefert sie fertig mit.

> **Optional — „echtes" RAGAS:** In Produktion nimmt man das Standard-Framework
> `ragas` (`from ragas import evaluate`, Metriken `faithfulness`,
> `answer_relevancy`, `context_precision`). ⚠️ Neue Abhängigkeit → gemäß
> Kurspolitik selbst installieren, und **die Version pinnen** (die API ändert
> sich zwischen Releases). Bewusst *nicht* in `requirements.txt`, damit der
> Pflichtteil abhängigkeitsfrei bleibt.

## Tests

```bash
pytest                      # Loader/Chunker + RRF-Fusion (offline, kein Netz)
```

`tests/test_hybrid.py` sichert die Reciprocal Rank Fusion ab (reine
Rang-Arithmetik). Die netzabhängigen Teile (RAG-Generierung, hybride Suche,
Evaluation) werden im Lab manuell geprüft (siehe `labs/vl05-lab.md`).

> Hier endet der VL-5-Stand: aus der Ingestion-Pipeline von VL 4 ist ein
> evaluierter, produktionsnaher RAG-Client geworden.
