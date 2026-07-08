# Lab VL 5 — Vom Retrieval zum RAG-Client: vervollständigen, verbessern, evaluieren

**Ziel:** Aus der Such-Pipeline von VL 4 wird ein **vollständiger RAG-Chatbot**:
Retrieve → **Augment → Generate**. Danach macht ihr ihn produktionsreif —
hybride Suche, besseres Prompting, Evaluation mit LLM-as-Judge und systematische
Fehlerdiagnose. Am Ende habt ihr einen RAG-Client, der Fragen über die
LeineTech-Wissensbasis **belegt** beantwortet — und Zahlen, die zeigen, wie gut
er wirklich ist.

**Dauer:** ~2 Std. (Teil 1: ~30 min · Teil 2: ~30 min · Teil 3: ~20 min · Teil 4: ~30 min · Teil 5: ~15 min)

> **Baut auf VL 4 auf.** Ihr braucht die fertige Ingestion-Pipeline aus
> `vl04-rag-ingestion-pipeline-solution` (Loader, Chunker, Embedder,
> Vektorstore, Suche). Wer VL 4 nicht fertig hat: einfach den Lösungs-Branch
> auschecken (Schritt 0).

---

## Schritt 0 — Setup (5–10 min)

```bash
cd leinetech
git checkout vl04-rag-ingestion-pipeline-solution   # Start = VL-4-Musterlösung
```

1) Umgebung aktivieren und Abhängigkeiten installieren:

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2) Kurs-Endpunkt setzen (wie in VL 3/4, siehe `SETUP.md`) — er liefert **beides**,
   Chat *und* Embeddings:

```bash
export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"    # Key auf Anfrage, siehe SETUP.md
```

3) Wissensbasis indexieren (falls `./chroma_db` noch leer ist):

```bash
python -m src.ingest docs
python -m src.search "Wie verbinde ich mich mit dem VPN?"   # Sanity-Check
```

Ihr solltet Treffer mit Rang, Ähnlichkeitswert und Quelle sehen. Läuft das,
steht die **Retrieve**-Stufe — jetzt hängen wir Augment + Generate an.

> **Hinweis:** Der Kurs-Endpunkt ist nur **montags** verfügbar, die erste
> Anfrage kann durch den Cold Start 200–300 s dauern. Cross-Encoder-Reranking
> (Teil 2, optional) und „echtes" RAGAS (Teil 4, optional) brauchen zusätzliche
> Pakete — die sind klar als **optional** markiert. Der Pflichtteil kommt mit
> den vorhandenen Abhängigkeiten aus.

---

## Teil 1 — Das RAG-System vervollständigen (~30 min)

Gestern endete die Pipeline bei den Top-k Chunks. Eine Trefferliste ist aber
**noch keine Antwort**. Wir hängen zwei Schritte an:

```
 Frage → [Embed] → ANN-Suche → Top-k Chunks     ← RETRIEVE (VL 4)
                                     |
                            Prompt-Template       ← AUGMENT
                         (Grounding + Kontext)
                                     |
                              LLM generiert        ← GENERATE
                                     |
              "Das Timeout beträgt 30 Min. [Quelle 2]"
```

### Aufgabe A — Der RAG-Client

Erstellt `src/rag.py`. Es nutzt die **vorhandene** Retrieval-Funktion aus VL 4
(`embedding_search` in `src/search.py`) und den Chat-Wrapper aus VL 3
(`chat` in `src/llm.py`):

```python
"""RAG-Client: Retrieve → Augment → Generate über die LeineTech-Wissensbasis."""

from src.llm import chat
from src.search import embedding_search
from src.vectorstore import create_collection, DEFAULT_COLLECTION

RAG_SYSTEM_PROMPT = (
    "Beantworte die Frage AUSSCHLIESSLICH anhand des bereitgestellten Kontexts. "
    "Wenn der Kontext die Antwort nicht enthält, sage wörtlich: "
    "'Ich habe dazu keine Information in der Wissensbasis.' "
    "Zitiere jede Aussage mit [Quelle N]."
)


def build_context(hits: list[dict]) -> str:
    """Formatiert die Treffer als nummerierten Kontextblock mit Quellen-Labels.

    Beispiel:
        [Quelle 1 | vpn-zugang.md]: Der Fernzugriff erfolgt über Cisco ...
        [Quelle 2 | passwort-und-konto.md]: Passwörter laufen nach 90 Tagen ...
    """


def answer(query: str, n_results: int = 5, collection=None) -> dict:
    """Beantwortet eine Frage per RAG.

    Ablauf: retrieve (embedding_search) → augment (build_context + Prompt)
    → generate (chat). Gibt {"answer": ..., "sources": [...], "hits": [...]}
    zurück, damit man Antwort UND Belege sieht.
    """
```

**Anforderungen:**

1. `build_context` nummeriert die Chunks als `[Quelle N | <source>]` — genau die
   Labels, auf die das LLM im Prompt verweist.
2. Der User-Prompt enthält **erst den Kontextblock, dann die Frage**.
3. `RAG_SYSTEM_PROMPT` als `system`-Argument an `chat(...)` übergeben (Grounding +
   Enthaltungsanweisung + Zitierformat — die drei Schlüsselelemente aus der
   Vorlesung).
4. `answer` gibt neben der Antwort auch die verwendeten Quellen zurück, damit
   man Zitate nachvollziehen kann.

### Aufgabe B — Das CLI

Macht `src/rag.py` aufrufbar:

```bash
python -m src.rag "Wie lange bleibt die VPN-Verbindung bestehen?"
python -m src.rag "Mein Passwort ist abgelaufen, was tun?"
```

Ausgabe: die generierte Antwort **plus** eine Liste der zitierten Quellen.

Beispiel:

```
Frage: Wie lange bleibt die VPN-Verbindung bestehen?

Antwort:
  Die VPN-Verbindung wird nach 12 Stunden oder nach 30 Minuten Inaktivität
  automatisch getrennt. [Quelle 1]

Quellen:
  [Quelle 1] vpn-zugang.md
  [Quelle 2] netzwerk-und-wlan.md
```

### Aufgabe C — Enthaltung testen (der wichtigste Test)

Stellt eine Frage, deren Antwort **nicht** in der Wissensbasis steht:

```bash
python -m src.rag "Wie viele Urlaubstage habe ich pro Jahr?"
```

Mit der Enthaltungsanweisung sollte das Modell sinngemäß antworten:
*„Ich habe dazu keine Information in der Wissensbasis."*

**Experiment:** Entfernt die Enthaltungsanweisung testweise aus dem System-Prompt
(oder nutzt `chat(prompt)` ganz ohne RAG-System-Prompt) und stellt dieselbe
Frage erneut.

**Diskutiert zu zweit:** Was antwortet das Modell jetzt? Klingt die erfundene
Antwort überzeugend? Warum ist das für einen IT-Support-Bot gefährlich? (→ Folie
„Warum die Enthaltungsanweisung wichtig ist".)

**Diskutiert außerdem:** Probiert `n_results` = 3, 5 und 10. Wird die Antwort
mit mehr Kontext besser — oder nur länger und verrauschter? (→ „Lost in the
Middle", Teil 3.)

---

## Teil 2 — Besseres Retrieval: Hybride Suche (~30 min)

Ihr habt jetzt ein funktionierendes RAG-System. Beim Testen fällt auf:
**keyword-lastige Fragen (Codes, exakte Fachbegriffe) scheitern oft.** Die
Vektorsuche ist „keyword-blind" — sie findet Bedeutung, aber verfehlt exakte
Zeichenketten.

Probiert eine solche Frage:

```bash
python -m src.search "Welches Gateway trage ich für Cisco Secure Client ein?"
```

Der exakte String `vpn.leinetech.de` steht in `vpn-zugang.md` — landet er ganz
oben? Oft nicht. Genau dafür gibt es **hybride Suche**: dichte Vektorsuche UND
Keyword-Suche parallel, dann die Ranglisten fusionieren.

### Aufgabe A — Reciprocal Rank Fusion (RRF)

RRF kombiniert Ranglisten, **ohne** unterschiedliche Score-Skalen normalisieren
zu müssen (Kosinus-Ähnlichkeit vs. Wortüberlappung) — es zählt nur die **Ränge**.

Erstellt `src/hybrid.py`:

```python
"""Hybride Suche: dichte Vektorsuche + Keyword-Suche, fusioniert per RRF."""

from src.search import embedding_search, keyword_search


def reciprocal_rank_fusion(rankings: list[list[dict]], k: int = 60) -> list[dict]:
    """Fusioniert mehrere Ranglisten zu einer.

    Jedes Dokument bekommt score = Σ 1 / (k + rang) über alle Listen, in denen
    es vorkommt (rang 1-basiert). k=60 ist die empirische Standardkonstante
    (Cormack et al. 2009). Dokumente, die in BEIDEN Listen auftauchen, steigen
    dadurch natürlich nach oben.

    Als stabile Identität pro Chunk dient hier der Chunk-Text (identischer Text
    = identischer Chunk). In Produktion nähme man die chunk_id.
    """


def hybrid_search(collection, query: str, n_results: int = 5) -> list[dict]:
    """Führt dichte + Keyword-Suche aus und fusioniert die Ergebnisse per RRF."""
```

**Anforderungen:**

1. Beide Suchen mit einem größeren Kandidatenfenster aufrufen (z. B. je
   `n_results * 4`), damit die Fusion echte Auswahl hat.
2. `reciprocal_rank_fusion` fusioniert die beiden Ranglisten und sortiert
   absteigend nach RRF-Score.
3. `hybrid_search` gibt die Top-k als `{"rank", "source", "score", "text"}`
   zurück — **gleiches Format** wie `embedding_search`, damit `src/rag.py` es
   ohne Änderung nutzen kann.

Testet die Fusion gegen die reine Vektorsuche:

```bash
python -c "
from src.vectorstore import create_collection
from src.search import embedding_search
from src.hybrid import hybrid_search
col = create_collection()
q = 'Welches Gateway trage ich für Cisco Secure Client ein?'
print('--- dense ---')
for h in embedding_search(col, q, 3): print(h['rank'], h['source'])
print('--- hybrid ---')
for h in hybrid_search(col, q, 3): print(h['rank'], h['source'])
"
```

### Aufgabe B — Den RAG-Client umschaltbar machen

Erweitert `src/rag.py` um einen `--retriever`-Schalter:

```bash
python -m src.rag "..." --retriever dense     # nur Vektorsuche (Default)
python -m src.rag "..." --retriever hybrid     # hybride Suche
```

**Diskutiert:** Bei welchen Fragen gewinnt hybrid, bei welchen macht es keinen
Unterschied? (Tipp: exakte Codes/Namen wie `vpn.leinetech.de`, Hotline `-4242`,
`Secure Client 5.1` vs. umschreibende Fragen wie „VPN geht nicht".)

### Aufgabe C — Reranking *(optional, wenn Zeit)*

Zweistufiges Retrieval: Stufe 1 (hybrid) liefert breit ~20 Kandidaten, Stufe 2
(Reranker) sortiert präzise auf die Top 3–5. Zwei Wege — wählt einen:

**Variante 1 — LLM-as-Reranker (ohne Zusatzpaket, nutzt den Kurs-Endpunkt):**
Lasst das LLM jeden Kandidaten gegen die Frage auf einer Skala 0–10 bewerten
(`chat(...)` mit einem knappen Bewertungs-Prompt), dann nach Score sortieren.
Einfach, aber ein LLM-Call pro Kandidat.

**Variante 2 — Cross-Encoder (Produktionsmuster aus den Folien):**

> ⚠️ **Neue Abhängigkeit** — laut Kurspolitik installiert *ihr* das Paket selbst
> (`pip install sentence-transformers`); es lädt zusätzlich ein Modell (~90 MB)
> herunter und läuft **lokal**, nicht über den Kurs-Endpunkt.

```python
from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
pairs = [[query, hit["text"]] for hit in candidates]
scores = reranker.predict(pairs)
ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
top_5 = [hit for hit, score in ranked[:5]]
```

**Bi-Encoder vs. Cross-Encoder:** Eure VL-4-Vektorsuche *ist* ein Bi-Encoder —
Frage und Chunk werden **getrennt** eingebettet (schnell, vorberechenbar). Der
Cross-Encoder verarbeitet **Frage + Chunk gemeinsam** (präzise, aber ein Forward
Pass pro Kandidat). Deshalb rerankt man nur die ~20 Kandidaten aus Stufe 1, nicht
den ganzen Korpus.

---

## Teil 3 — Bessere Generierung: Prompt Engineering (~20 min)

Selbst bei perfektem Retrieval entscheidet der **Prompt**, ob das LLM den Kontext
richtig nutzt. Ein bekannter Fehlerfall: Das Modell soll *alle* Elemente
auflisten, lässt aber welche weg (Folie „Unvollständige Antwort").

### Aufgabe A — Den Fehlerfall reproduzieren

Stellt eine Frage, deren Antwort über **mehrere Chunks** verstreut ist:

```bash
python -m src.rag "Nenne alle Voraussetzungen, um das VPN einzurichten."
```

`vpn-zugang.md` listet vier Voraussetzungen (verwaltetes Gerät, Secure Client
≥ 5.1, eingerichtete MFA, ≥ 16 Mbit/s). Bekommt ihr wirklich **alle**?

### Aufgabe B — Die fünf Prinzipien anwenden

Verbessert `RAG_SYSTEM_PROMPT` nach den fünf Prinzipien aus der Vorlesung:

| # | Prinzip | Umsetzung im Prompt |
|---|---|---|
| 1 | Explizites Grounding | „Antworte NUR aus dem Kontext" |
| 2 | Zitierformat | „Zitiere mit [Quelle N]" |
| 3 | Abstinenz-Anweisung | „Sage: keine Information in der Wissensbasis" |
| 4 | Metadaten in Labels | `[Quelle N \| dateiname.md]` |
| 5 | Ausgabeformat | „Liste **ALLE** im Kontext genannten Punkte als Aufzählung" |

Fügt Prinzip 5 hinzu und testet die VPN-Frage erneut. Werden jetzt alle vier
Voraussetzungen genannt?

### Aufgabe C — „Lost in the Middle" *(kurz)*

LLMs beachten den **Anfang** und das **Ende** des Kontextfensters stärker als
die **Mitte**. Gegenmaßnahmen: relevanteste Chunks nach vorn, `n_results`
begrenzen, per Reranking (Teil 2) die Reihenfolge bestimmen.

**Prüft:** `build_context` sortiert die Chunks bereits nach Relevanz (Rang 1
zuerst)? Falls nicht — korrigiert es. Die Reihenfolge im Prompt ist kein Zufall.

---

## Teil 4 — Evaluation: Wissen, ob es funktioniert (~30 min)

Bis jetzt beurteilt ihr Qualität „per Augenschein". Für Produktion braucht ihr
**Zahlen**. RAG kann an zwei Stellen scheitern (Retrieval *oder* Generierung) —
und eine falsche Antwort sieht von außen immer gleich aus. Wir messen die
**RAG-Triade** mit einem LLM als Richter (**LLM-as-Judge** — genau das Verfahren,
das auch RAGAS nutzt).

### Aufgabe A — Ein kleines Evaluationsset

Erstellt `eval/rag_eval.jsonl` mit ~8–10 Frage-Antwort-Paaren aus dem Korpus.
Drei Sorten Fragen (wie in der Vorlesung):

- **Einfach** — Antwort steht in einem Chunk (z. B. „Wie lautet die interne
  IT-Hotline?" → `-4242`)
- **Schwer** — Antwort erstreckt sich über mehrere Chunks (z. B. „Welche
  Voraussetzungen brauche ich fürs VPN?")
- **Unbeantwortbar** — Antwort steht **nicht** im Korpus (testet Abstinenz;
  `ground_truth` = „nicht in der Wissensbasis")

```jsonl
{"question": "Wie lautet die interne IT-Hotline?", "ground_truth": "-4242"}
{"question": "Nach welcher Zeit trennt das VPN bei Inaktivität?", "ground_truth": "nach 30 Minuten"}
{"question": "Wie viele Urlaubstage habe ich?", "ground_truth": "nicht in der Wissensbasis"}
```

### Aufgabe B — LLM-as-Judge

Erstellt `src/rag_eval.py`. Für jede Frage: `answer(...)` aufrufen, dann das LLM
zwei Dinge bewerten lassen (0.0–1.0), plus eine harte Prüfung:

```python
"""RAG-Evaluation per LLM-as-Judge — die RAG-Triade auf unserem Evalset."""

from src.llm import chat
from src.rag import answer


def faithfulness(question: str, rag_answer: str, context: str) -> float:
    """Wird JEDE Aussage der Antwort durch den Kontext gestützt? (Grounding)

    LLM-Judge-Prompt: 'Extrahiere die Aussagen der Antwort. Wie viele sind durch
    den Kontext gedeckt? Gib nur die Zahl gestützt/gesamt als Dezimalzahl.'
    """


def answer_relevancy(question: str, rag_answer: str) -> float:
    """Beantwortet die Antwort die Frage? (Generierung)

    Intuition: Aus einer guten Antwort ließe sich die Frage rekonstruieren.
    """


def context_hit(expected_source: str, hits: list[dict]) -> bool:
    """Kontextrelevanz (Retrieval): war die erwartete Quelle unter den Treffern?"""
```

**Anforderungen:**

1. Den Judge mit `temperature=0.0` aufrufen (reproduzierbar) und nur eine Zahl
   parsen — robust gegen „Die Antwort ist 0.8".
2. Für **unbeantwortbare** Fragen zählt als korrekt, wenn das System sich
   enthält (Abstinenz-Antwort). Prüft das gesondert.
3. Am Ende Durchschnittswerte pro Metrik ausgeben.

### Aufgabe C — Drei Konfigurationen vergleichen

Lasst die Evaluation über **drei Retriever-Konfigurationen** laufen und tragt
die Zahlen ein:

```bash
python -m src.rag_eval --retriever dense
python -m src.rag_eval --retriever hybrid
python -m src.rag_eval --retriever hybrid --rerank    # falls Teil 2 C gebaut
```

| Konfiguration | Faithfulness | Answer Relevancy | Kontext-Treffer |
|---|---|---|---|
| Dense (VL 4) | | | |
| Hybrid | | | |
| Hybrid + Rerank | | | |

**Richtwerte zur Kalibrierung** (aus der Vorlesung — keine absoluten Standards):
Faithfulness > 0.8 stark, < 0.5 bedenklich; Answer Relevancy > 0.8 stark,
< 0.6 bedenklich.

**Wichtiger Vorbehalt:** Wir bewerten ein LLM mit einem LLM. Bekannte Biases
(Positions-, Ausführlichkeits-, Selbstverstärkungsbias) machen die Zahlen zu
**Richtungssignalen zum Vergleich von Konfigurationen**, nicht zu absoluter
Wahrheit. Für Hochrisiko bleibt menschliche Evaluation der Goldstandard.

> **Optional — „echtes" RAGAS:** In Produktion nimmt man das Standard-Framework
> `ragas` (`from ragas import evaluate`, Metriken `faithfulness`,
> `answer_relevancy`, `context_precision`). ⚠️ Neue Abhängigkeit → selbst
> installieren, und **die Version pinnen** (die RAGAS-API ändert sich zwischen
> Releases). Wer mag, verdrahtet es hinterher mit dem Kurs-Endpunkt als Judge.

---

## Teil 5 — Fehlerdiagnose (~15 min)

Wenn eine Antwort falsch ist, ratet nicht — **diagnostiziert**. Die sieben
Fehlerpunkte (Barnett et al., 2024) und die Diagnosetabelle machen aus Scores
umsetzbare Entscheidungen.

| Muster (aus Teil 4) | Ursache | Lösung |
|---|---|---|
| Niedrige Faithfulness + guter Kontext-Treffer | Generator halluziniert trotz gutem Kontext | Grounding im Prompt schärfen (Teil 3) |
| Hohe Faithfulness + schlechter Kontext-Treffer | Retriever verpasst relevante Chunks | hybride Suche, besseres Chunking (Teil 2) |
| Niedrige Answer Relevancy | Antwort driftet vom Thema ab | Rauschen reduzieren, Prompt schärfen |
| Relevanter Chunk nicht oben | zu viel Rauschen im Retrieval | Reranking hinzufügen (Teil 2 C) |

### Übung — Diagnostiziert euer eigenes System

Sucht in eurer Evaluation aus Teil 4 die **schlechteste Frage** heraus. Schaut
euch `hits` **und** `answer` an und ordnet den Fehler einem der Muster oben zu.
Was würdet ihr konkret ändern?

### Übung — Fall C aus der Vorlesung (Diskussion)

> **Frage:** „Wie hoch war unser Q3-2024-Umsatz?"
> **Abgerufene Chunks:** über den **Q3-2023**-Umsatz
> **Antwort:** nennt die Q3-2023-Zahl, als wäre es 2024

**Diskutiert zu zweit (60 s):** Welcher Fehlerpunkt ist das? Warum hat der
Retriever 2023 statt 2024 geliefert (Stichwort: „2023" und „2024" sind im
Embedding-Raum fast identisch)? Was würdet ihr ändern? (Tipp: Metadaten-Filter
nach Jahr, hybride Suche auf die exakte Jahreszahl.)

---

## Teil 6 — Reflexion (~10 min)

**Pitch je Gruppe (2 min):** Zeigt eine Frage, die *nur* mit hybrider Suche oder
*nur* nach dem Prompt-Tuning funktioniert hat — und eure drei Eval-Zahlen.

**Leitfragen:**

- Wo lag bei euch das größere Problem — Retrieval oder Generierung? Woran habt
  ihr das an den Metriken **abgelesen** (nicht geraten)?
- Die Vorlesung sagt: „Einfach anfangen, Komplexität nach gemessenen Defiziten
  hinzufügen." Hat die hybride Suche / das Reranking bei *euch* messbar geholfen
  — oder war Dense schon gut genug?
- Was würde für den Produktivbetrieb noch fehlen? (Multi-Turn/Folgefragen,
  Kosten-/Latenzbudget, größeres Evalset mit 50–100 Fragen, menschliche Prüfung.)

**Zentrale Erkenntnisse:** Einfach anfangen (Dense → Hybrid → +Reranking) ·
früh evaluieren (Testset vor der Optimierung) · systematisch diagnostizieren
(die sieben Fehlerpunkte statt raten) · der Prompt ist entscheidend (Grounding,
Zitate, Abstinenz) · messen statt raten (RAGAS/LLM-Judge liefert
Richtungssignale).

---

## Troubleshooting

| Problem | Lösung |
| --- | --- |
| `ImportError: embedding_search` | Ihr seid nicht auf dem VL-4-Solution-Stand — `git checkout vl04-rag-ingestion-pipeline-solution` |
| Collection ist leer | Erst indexieren: `python -m src.ingest docs` |
| Erste Anfrage hängt minutenlang | Cold Start am Kurs-Endpunkt (200–300 s) — warten, nicht abbrechen (s. SETUP.md) |
| 403 / „nur montags …" | Endpunkt außerhalb des Zeitfensters oder `LLM_API_KEY`/`LLM_BASE_URL` fehlen — s. SETUP.md |
| LLM ignoriert den Kontext / halluziniert | Enthaltungs- und Grounding-Anweisung im System-Prompt prüfen (Teil 1/3) |
| RAG antwortet immer „keine Information" | Kontextblock leer? `n_results` > 0 und `build_context` prüfen — kommen Treffer an? |
| Hybrid ≙ Dense (kein Unterschied) | Kandidatenfenster zu klein — beide Suchen mit `n_results * 4` aufrufen |
| `ModuleNotFoundError: sentence_transformers` | Nur für Reranking (Teil 2 C, optional) — `pip install sentence-transformers` |
| Judge gibt keine parsebare Zahl zurück | `temperature=0.0`, Zahl per Regex extrahieren, Prompt auf „nur die Zahl" verschärfen |
| `InvalidDimensionException` | Collection mit anderem Embedding-Modell befüllt — `chroma_db/` löschen und neu ingesten (Gleiches-Modell-Regel) |
