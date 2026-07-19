# Lab VL 5 — Vom Retrieval zum RAG-Client: vervollständigen & besser ranken

**Ziel:** Aus der Such-Pipeline von VL 4 wird ein **vollständiger RAG-Chatbot**:
Retrieve → **Augment → Generate**. Danach verbessert ihr das Retrieval mit
**hybrider Suche** und implementiert dabei einmal selbst eine Rang-Fusion (RRF).
Am Ende habt ihr einen RAG-Client, der Fragen über die LeineTech-Wissensbasis
**belegt** beantwortet — und versteht, warum eine reine Vektorsuche bei exakten
Begriffen scheitert.

**Dauer:** ~90 min (Setup: ~10 min · Teil 1: ~35 min · Teil 2: ~30 min · Puffer/Fragen: ~15 min)

> **Fokus & Vertiefung.** Der **Pflichtteil** (Teil 1 + Teil 2) baut ein
> funktionierendes RAG-System mit hybridem Ranking. Die **Evaluation mit
> LLM-as-Judge** ist als **Vertiefung** unten angehängt — für schnelle Gruppen
> oder zum Selbststudium. Die Konzepte dazu kennt ihr aus der Vorlesung.

> **Baut auf VL 4 auf.** Ihr braucht die fertige Ingestion-Pipeline aus
> `vl04-rag-ingestion-pipeline-solution` (Loader, Chunker, Embedder,
> Vektorstore, Suche). Wer VL 4 nicht fertig hat: einfach den Lösungs-Branch
> auschecken (Schritt 0).

---

## Schritt 0 — Setup (~10 min)

```bash
cd leinetech
git checkout vl05-rag-advanced-start   # Start = VL-4-Musterlösung
```

1. Umgebung aktivieren und Abhängigkeiten installieren:

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2. Kurs-Endpunkt setzen (wie in VL 3/4, siehe `SETUP.md`) — er liefert **beides**,
   Chat _und_ Embeddings:

```bash
export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"    # Key auf Anfrage, siehe SETUP.md
```

3. Wissensbasis indexieren (falls `./chroma_db` noch leer ist):

```bash
python -m src.ingest docs
python -m src.search "Wie verbinde ich mich mit dem VPN?"   # Sanity-Check
```

Ihr solltet Treffer mit Rang, Ähnlichkeitswert und Quelle sehen. Läuft das,
steht die **Retrieve**-Stufe — jetzt hängen wir Augment + Generate an.

> **Wichtig — Cold Start:** Der Kurs-Endpunkt ist nur **montags** verfügbar, die
> erste Anfrage kann durch den Cold Start **200–300 s** dauern. Setzt den
> Sanity-Check **gleich zu Beginn** ab, damit der Endpunkt „warm" ist, während
> ihr an Teil 1 codet.

---

## Teil 1 — Das RAG-System vervollständigen _(Pflicht, ~35 min)_

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


def answer(
    query: str,
    n_results: int = 5,
    collection=None,
    retriever=embedding_search,
) -> dict:
    """Beantwortet eine Frage per RAG.

    Ablauf: retrieve (retriever) → augment (build_context + Prompt) → generate
    (chat). `retriever` ist standardmäßig die dichte Vektorsuche
    (embedding_search), lässt sich aber gegen `hybrid_search` (Teil 2) tauschen —
    beide liefern dasselbe Trefferformat. Gibt
    {"answer": ..., "sources": [...], "hits": [...], "context": ...} zurück, damit
    man Antwort, Belege UND den (für die Vertiefung nötigen) Kontext sieht.
    """
```

**Anforderungen:**

1. `build_context` nummeriert die Chunks als `[Quelle N | <source>]` — genau die
   Labels, auf die das LLM im Prompt verweist. **Reihenfolge nach Relevanz**
   (Rang 1 zuerst): LLMs beachten Anfang und Ende des Kontexts stärker als die
   Mitte („Lost in the Middle").
2. Der User-Prompt enthält **erst den Kontextblock, dann die Frage**.
3. `RAG_SYSTEM_PROMPT` als `system`-Argument an `chat(...)` übergeben (Grounding +
   Enthaltungsanweisung + Zitierformat — die drei Schlüsselelemente aus der
   Vorlesung).
4. `answer` gibt neben der Antwort auch die verwendeten Quellen zurück, damit
   man Zitate nachvollziehen kann.
5. `answer` akzeptiert einen optionalen `retriever`-Parameter (Default
   `embedding_search`). So läuft dieselbe RAG-Logik in der Vertiefung einmal mit
   dichter und einmal mit **hybrider** Suche (Teil 2) — ohne den Code zu
   duplizieren (`answer(..., retriever=hybrid_search)`).
6. `answer` gibt zusätzlich den zusammengebauten `context`-String zurück. Die
   Vertiefung (LLM-as-Judge `faithfulness`) braucht ihn, um die Antwort gegen den
   **tatsächlich genutzten** Kontext zu prüfen.

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

> **Hinweis:** Die Modellantwort kann mit Leerzeichen/Leerzeilen beginnen (Format-
> oder Reasoning-Artefakt einiger Modelle). Für eine saubere CLI-Ausgabe die
> Antwort vor dem Drucken mit `.strip()` bereinigen.

### Aufgabe C — Enthaltung testen (der wichtigste Test)

Stellt eine Frage, deren Antwort **nicht** in der Wissensbasis steht:

```bash
python -m src.rag "Wie viele Urlaubstage habe ich pro Jahr?"
```

Mit der Enthaltungsanweisung sollte das Modell sinngemäß antworten:
_„Ich habe dazu keine Information in der Wissensbasis."_

**Experiment:** Entfernt die Enthaltungsanweisung testweise aus dem System-Prompt
(oder nutzt `chat(prompt)` ganz ohne RAG-System-Prompt) und stellt dieselbe
Frage erneut.

**Diskutiert zu zweit:** Was antwortet das Modell jetzt? Klingt die erfundene
Antwort überzeugend? Warum ist das für einen IT-Support-Bot gefährlich? (→ Folie
„Warum die Enthaltungsanweisung wichtig ist".)

> **Hinweis (modellabhängig):** Starke, aktuelle Modelle erfinden oft *keine*
> überzeugende Falschantwort, sondern weisen von sich aus auf die fehlende
> Information hin oder verweisen an die Personalabteilung — der Halluzinations-
> effekt fällt dann schwächer aus als in der Vorlesung gezeigt. Das ändert nichts
> an der Kernaussage: Ohne explizite Enthaltungsanweisung ist das Verhalten
> **nicht garantiert** — und genau diese Garantie braucht ein IT-Support-Bot. Wer
> den Effekt deutlicher sehen will, formuliert eine Frage, die eine plausible,
> aber falsche Antwort nahelegt (z. B. nach einer konkreten Zahl/Frist, die es im
> Korpus nicht gibt).

---

## Teil 2 — Besseres Retrieval: Hybride Suche mit RRF _(Pflicht, ~30 min)_

Ihr habt jetzt ein funktionierendes RAG-System. Beim Testen fällt auf:
**keyword-lastige Fragen (Codes, exakte Fachbegriffe) scheitern oft.** Die
Vektorsuche ist „keyword-blind" — sie findet Bedeutung, aber verfehlt exakte
Zeichenketten.

Probiert eine solche Frage:

```bash
python -m src.search "Welche Durchwahl hat Bernd Hagedorn?"
```

Der exakte String `-4200` (Durchwahl von Bernd Hagedorn) steht in
`it-support-prozesse.md`. Landet die passende Stelle ganz oben? Oft nicht — die
Frage ähnelt semantisch vielen anderen Kontakt-/Hotline-Textstellen, und der
exakte Code selbst trägt fürs Embedding kaum Bedeutung. Genau dafür gibt es
**hybride Suche**: dichte Vektorsuche UND Keyword-Suche parallel, dann die
Ranglisten fusionieren.

> **Wichtig — modellabhängig:** Wie stark der Effekt ausfällt, hängt vom
> Embedding-Modell ab. Das hier genutzte `qwen3-embed-4b` ist stark genug, dass es
> viele exakte Begriffe (z. B. `vpn.leinetech.de`, `-4242`) **trotzdem** auf Rang 1
> findet. Der Vorteil der hybriden Suche zeigt sich dann vor allem bei kleinem k
> (Top-3) und bei selteneren Begriffen. Bei schwächeren Embeddern greift er
> deutlicher.

### Reciprocal Rank Fusion (RRF)

RRF kombiniert Ranglisten, **ohne** unterschiedliche Score-Skalen normalisieren
zu müssen (Kosinus-Ähnlichkeit vs. Wortüberlappung) — es zählt nur die **Ränge**.
Das ist der Kern: Ihr implementiert hier einmal selbst, wie aus zwei Ranglisten
eine wird.

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

> **Hinweis:** `keyword_search` liefert nur Chunks **mit Wortüberlappung** — die
> beiden Kandidatenlisten können also unterschiedlich lang sein (auch mal < k·4
> oder leer). Für RRF ist das unkritisch: Ein Chunk, der nur in einer Liste
> steht, bekommt eben nur deren Beitrag; ein Rang, den es in einer Liste nicht
> gibt, trägt 0 bei.

Testet die Fusion gegen die reine Vektorsuche:

```bash
python -c "
from src.vectorstore import create_collection
from src.search import embedding_search
from src.hybrid import hybrid_search
col = create_collection()
q = 'Welche Durchwahl hat Bernd Hagedorn?'
print('--- dense ---')
for h in embedding_search(col, q, 3): print(h['rank'], h['source'])
print('--- hybrid ---')
for h in hybrid_search(col, q, 3): print(h['rank'], h['source'])
"
```

Achtet darauf, auf welchem **Rang** die Stelle mit `-4200` (`it-support-prozesse.md`)
landet — bei dense oft außerhalb der Top-3, bei hybrid ganz oben.

**Diskutiert:** Bei welchen Fragen gewinnt hybrid, bei welchen macht es keinen
Unterschied? (Beispiele, bei denen dense die exakte Stelle verfehlt und hybrid
sie nach oben zieht: `-4200` (Bernd Hagedorn), `Bitwarden`. Beispiele, bei denen
schon dense reicht: `vpn.leinetech.de`, Hotline `-4242`, `Secure Client 5.1`.
Umschreibende Fragen wie „VPN geht nicht" profitieren gar nicht.)

---

## Puffer / Fragen (~15 min)

Reserviert am Ende Zeit für Cold-Start-Latenz, Debugging und offene Fragen.
Wer früh fertig ist, startet direkt mit der **Vertiefung** unten.

**Kurzer Abschluss-Check (2 min zu zweit):**

- Wo lag bei euch das größere Problem — Retrieval oder Generierung?
- Habt ihr eine Frage gefunden, die _nur_ mit hybrider Suche funktioniert?

---

# Vertiefung Prompt Evaluation

Alles ab hier ist **freiwillig**. Ihr vertieft den Pflichtteil um die
**Evaluation** eures RAG-Systems mit LLM-as-Judge. Die Konzepte kennt ihr aus
der Vorlesung — hier setzt ihr sie um.

## Evaluation: Wissen, ob es funktioniert

Bis jetzt beurteilt ihr Qualität „per Augenschein". Für Produktion braucht ihr
**Zahlen**. RAG kann an zwei Stellen scheitern (Retrieval _oder_ Generierung) —
und eine falsche Antwort sieht von außen immer gleich aus. Wir messen die
**RAG-Triade** mit einem LLM als Richter (**LLM-as-Judge** — genau das Verfahren,
das auch RAGAS nutzt).

### Ein kleines Evaluationsset

Erstellt `eval/rag_eval.jsonl` mit ~8–10 Frage-Antwort-Paaren aus dem Korpus
(nicht zu verwechseln mit dem bereits vorhandenen `eval/golden.jsonl` aus der
Ticket-Triage). Vier Sorten Fragen:

- **Einfach** — Antwort steht in einem Chunk (z. B. „Wie lautet die interne
  IT-Hotline?" → `-4242`)
- **Schwer** — Antwort erstreckt sich über mehrere Chunks (z. B. „Welche
  Voraussetzungen brauche ich fürs VPN?")
- **Keyword-lastig** — Antwort hängt an einem exakten Code/Namen, den die
  Vektorsuche leicht verfehlt (z. B. „Welche Durchwahl hat Bernd Hagedorn?" →
  `-4200`). **Wichtig:** genau diese Sorte macht später den Unterschied zwischen
  dense und hybrid sichtbar — nehmt mehrere davon auf.
- **Unbeantwortbar** — Antwort steht **nicht** im Korpus (testet Abstinenz;
  `ground_truth` = „nicht in der Wissensbasis")

Jede Zeile trägt zusätzlich `expected_source` (die Datei, in der die Antwort
steht — für `context_hit`; bei unbeantwortbaren Fragen `null`) und `type`
(steuert die Auswertung, z. B. Abstinenz-Prüfung bei `unbeantwortbar`):

```jsonl
{"question": "Wie lautet die interne IT-Hotline?", "ground_truth": "-4242", "expected_source": "it-support-prozesse.md", "type": "einfach"}
{"question": "Welche Voraussetzungen brauche ich fürs VPN?", "ground_truth": "verwaltetes Gerät, Secure Client ab 5.1, MFA, 16 Mbit/s", "expected_source": "vpn-zugang.md", "type": "schwer"}
{"question": "Welche Durchwahl hat Bernd Hagedorn?", "ground_truth": "-4200", "expected_source": "it-support-prozesse.md", "type": "keyword"}
{"question": "Wie viele Urlaubstage habe ich?", "ground_truth": "nicht in der Wissensbasis", "expected_source": null, "type": "unbeantwortbar"}
```

### LLM-as-Judge

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
   enthält (Abstinenz-Antwort). Prüft das gesondert — und **legt bewusst fest**,
   wie ihr Faithfulness/Answer-Relevancy in diesem Fall wertet (naheliegend: bei
   korrekter Enthaltung 1.0, bei Halluzination 0.0). Ohne diese Festlegung sind
   die Durchschnitte zwischen Konfigurationen nicht vergleichbar.
3. Am Ende Durchschnittswerte pro Metrik ausgeben.

### Konfigurationen vergleichen

Lasst die Evaluation über **beide Retriever-Konfigurationen** laufen (dense vs.
hybrid — genau die zwei, die ihr im Pflichtteil gebaut habt) und tragt die
Zahlen ein:

```bash
python -m src.rag_eval --retriever dense
python -m src.rag_eval --retriever hybrid
```

| Konfiguration | Faithfulness | Answer Relevancy | Kontext-Treffer |
| ------------- | ------------ | ---------------- | --------------- |
| Dense (VL 4)  |              |                  |                 |
| Hybrid        |              |                  |                 |

> **Wenn beide Konfigurationen identische Werte liefern:** Bei kleinem Korpus und
> starkem Embedder findet schon dense fast alles im Top-5-Fenster — der
> Kontext-Treffer ist dann für beide ≈ 1.0 und die Tabelle zeigt keinen
> Unterschied. Verkleinert das Kontextfenster, damit Retrieval-Qualität überhaupt
> ins Gewicht fällt:
>
> ```bash
> python -m src.rag_eval --retriever dense  --n 3
> python -m src.rag_eval --retriever hybrid --n 3
> ```
>
> Erst bei kleinem k zeigt sich der Effekt: Im Beispiel-Evalset verfehlt dense bei
> Top-3 die Stelle zu „Bernd Hagedorn / `-4200`", hybrid nicht — Kontext-Treffer
> **dense ≈ 0.93 vs. hybrid 1.0** (Faithfulness/Relevancy bleiben bei diesem
> starken Modell in beiden Fällen ≈ 1.0). Deshalb sind **keyword-lastige Fragen**
> im Evalset entscheidend — ohne sie belegt die Tabelle den Nutzen der hybriden
> Suche nicht.

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

## Troubleshooting

| Problem                                      | Lösung                                                                                                          |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `ImportError: embedding_search`              | Ihr seid nicht auf dem VL-4-Solution-Stand — `vl05-rag-advanced-start`                |
| Collection ist leer                          | Erst indexieren: `python -m src.ingest docs`                                                                    |
| Erste Anfrage hängt minutenlang              | Cold Start am Kurs-Endpunkt (200–300 s) — warten, nicht abbrechen (s. SETUP.md)                                 |
| 403 / „nur montags …"                        | Endpunkt außerhalb des Zeitfensters oder `LLM_API_KEY`/`LLM_BASE_URL` fehlen — s. SETUP.md                      |
| LLM ignoriert den Kontext / halluziniert     | Enthaltungs- und Grounding-Anweisung im System-Prompt prüfen (Teil 1)                                           |
| RAG antwortet immer „keine Information"      | Kontextblock leer? `n_results` > 0 und `build_context` prüfen — kommen Treffer an?                              |
| Hybrid ≙ Dense (kein Unterschied)            | Kandidatenfenster zu klein — beide Suchen mit `n_results * 4` aufrufen                                          |
| Judge gibt keine parsebare Zahl zurück       | `temperature=0.0`, Zahl per Regex extrahieren, Prompt auf „nur die Zahl" verschärfen                            |
| `InvalidDimensionException`                  | Collection mit anderem Embedding-Modell befüllt — `chroma_db/` löschen und neu ingesten (Gleiches-Modell-Regel) |
| `Failed to send telemetry event ...`         | Kosmetisch (chromadb 1.0.7 gegen neuere posthog-Lib). In `src/vectorstore.py` per `Settings(anonymized_telemetry=False)` + Stummschalten des Loggers `chromadb.telemetry.product.posthog` abgestellt |
