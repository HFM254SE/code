# Lab VL 5: Vom Retrieval zum belegten RAG-Client

In VL 4 endete eure Pipeline bei einer Trefferliste. Heute wird daraus ein Support-Bot für die
LeineTech-Wissensbasis. Er antwortet belegt mit Quellenangaben und sagt ehrlich, wenn er etwas
nicht weiß. Danach verbessert ihr das Retrieval mit hybrider Suche und messt, ob es wirklich
besser wird. Das ist der Kern-Loop des Kurses: Tool benutzen, Ergebnis kritisch prüfen, messen
statt glauben.

| | |
|---|---|
| **Format** | Paararbeit, 90 min (5 min Briefing, 85 min Arbeit) |
| **Start-Branch** | `vl05-rag-advanced-start` (VL-4-Musterlösung plus Lab-Material) |
| **Musterlösung** | `vl05-rag-advanced-solution` |
| **Ohne Endpunkt möglich** | alle Tests, Aufgabe 1A, die Keyword-Suche und die Keyword-Messung (sobald ein Index existiert) |

## Lernziele

Nach dem Lab könnt ihr …

1. einen RAG-Client bauen, der Treffer als Kontextblock mit Zitat-Labels in den Prompt setzt und
   belegt antwortet.
2. mit einem Experiment zeigen, wozu die Enthaltungsanweisung im System-Prompt dient.
3. Reciprocal Rank Fusion (RRF) implementieren und mit Tests absichern.
4. dichte Suche, Keyword-Suche und hybride Suche auf einem Evalset messen und einen Unterschied
   einem der sieben Fehlerpunkte zuordnen.
5. *(Vertiefung)* einen LLM-as-a-Judge für Faithfulness bauen und seine Urteile von Hand prüfen.

## Voraussetzungen

- Das Repo `leinetech` ist geklont. Python 3.12 oder 3.13 ist installiert (`python --version`), wie seit VL 1.
  Die Vorlagen nutzen Typangaben wie `str | None`, die ältere Versionen nicht kennen.
- Ihr habt euren persönlichen API-Key für den Kurs-Endpunkt (seit VL 1, siehe `SETUP.md`).
- **Zeitfenster des Endpunkts:** nur montags von 06:00 bis 23:59 Uhr. Findet das Lab an einem
  anderen Tag statt, gilt der Plan B in `SETUP.md` (Abschnitt „Plan B“). Die erste Anfrage kann
  durch den Cold Start 200 bis 300 Sekunden dauern.
- Aus der Vorlesung kennt ihr die drei Pflichtelemente eines RAG-Prompts, die RRF-Formel, die vier
  Fragetypen eines Evalsets und die sieben Fehlerpunkte. Die Fehlerpunkte stehen zum Nachschlagen
  auch in Aufgabe 2D.
- Wer VL 4 nicht abgeschlossen hat, verliert nichts. Der Start-Branch enthält die VL-4-Musterlösung.

## Zeitplan und Checkpoints

| Schritt | Inhalt | Zeit | Checkpoint |
|---|---|---|---|
| 0 | Setup und Index bauen | 10 min | **CP 1:** `src.search` liefert Treffer aus `vpn-zugang.md` |
| 1 | RAG-Client bauen, Enthaltung testen | 35 min | **CP 2:** `tests/test_rag.py` grün, der Bot enthält sich bei der Urlaubstage-Frage |
| 2 | Hybride Suche bauen und messen | 30 min | **CP 3:** `tests/test_hybrid.py` grün, Messtabelle mit drei Zeilen |
| 3 | Abschluss und Reflexion | 10 min | |
| Bonus | Vertiefung für Schnelle | offen | |

Summe: 85 min Arbeit plus 5 min Briefing. Wer an einem Checkpoint hängt, holt sich mit der
Aufholzeile im Checkpoint-Kasten die Musterlösung für genau diesen Schritt und macht weiter.

---

## Schritt 0: Setup (10 min)

### 0.1 Eigene VL-4-Arbeit sichern

Habt ihr in VL 4 eigene Dateien angelegt oder geändert, sichert ihr sie zuerst. Sonst bricht der
Checkout mit „Your local changes would be overwritten“ oder „untracked working tree files would be
overwritten“ ab.

```bash
cd leinetech
git status                                   # zeigt eigene Änderungen
git switch -c meine-vl04-loesung             # eigener Branch für eure VL-4-Arbeit
git add -A && git commit -m "Meine VL-4-Lösung"
```

Ohne eigene Änderungen überspringt ihr diesen Schritt. Alternative ohne Branch:
`git stash push -u -m "meine VL-4-Arbeit"`.

### 0.2 Start-Branch und Umgebung

```bash
git fetch origin
git checkout vl05-rag-advanced-start
python -m venv .venv                         # nur, falls es noch keine .venv gibt
source .venv/bin/activate                    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python -m pytest -q
```

Erwartet ist eine letzte Zeile ohne `failed` und mit genau `3 skipped`, etwa so (Anzahl der
bestandenen Tests und Laufzeit können abweichen):

```
33 passed, 3 skipped in 2.41s
```

Die drei übersprungenen Testdateien gehören zu euren Aufgaben. Sie laufen, sobald ihr die
Vorlagen kopiert habt.

### 0.3 Endpunkt setzen und Index neu bauen

```bash
export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"              # Key siehe SETUP.md
export LLM_TIMEOUT=360                       # Chat-Anfragen: Kaltstart dauert länger als 120 s
python -m src.ingest docs
```

Unter Windows (PowerShell) setzt ihr die Variablen mit `$env:LLM_BASE_URL="…"`,
`$env:LLM_API_KEY="<euer-key>"` und `$env:LLM_TIMEOUT="360"`. Ohne `LLM_TIMEOUT` bricht
`chat()` nach 120 s ab (Default seit VL 3). Das Ingest ist davon nicht betroffen.

Der Ordner `chroma_db/` ist von Git ausgenommen und überlebt den Checkout. Ein alter Index aus
VL 4 stört trotzdem nicht. Das Ingest ersetzt alle Chunks jeder Datei. Fällt der Endpunkt aus,
bleibt der alte Index erhalten.

Erwartete Ausgabe:

```
8 Dokumente geladen
80 Chunks erzeugt
80 Embeddings berechnet (2560 Dimensionen)
Collection 'leinetech_kb': 80 Einträge gespeichert
```

Dauert es beim ersten Mal minutenlang, ist das der Cold Start. Nicht abbrechen. Startet das
Ingest deshalb sofort und beginnt in einem zweiten Terminal parallel mit Aufgabe 1A. Sie läuft
offline. Im zweiten Terminal genügt `source .venv/bin/activate`. Den Sanity-Check 0.4 holt ihr
nach, sobald das Ingest fertig ist.

### 0.4 Sanity-Check

```bash
python -m src.search "Wie verbinde ich mich mit dem VPN?" --n 3
```

Erwartet sind drei Treffer mit Rang, Ähnlichkeit, Chunk-ID und Textvorschau. Die Chunk-ID besteht
aus Dateiname und Chunk-Nummer, zum Beispiel `vpn-zugang.md::0`. Oben steht ein Chunk aus
`vpn-zugang.md`. Die Werte hängen vom Embedding-Modell ab, etwa so (Vorschau hier gekürzt):

```
Suche (embedding): "Wie verbinde ich mich mit dem VPN?"
  1. [0.xx] vpn-zugang.md::0 — "# VPN-Zugang (Cisco AnyConnect) Stand: Mai 2026 Der Fernzugriff …"
  2. …
```

> **✓ Checkpoint 1:** `src.search` liefert Treffer aus `vpn-zugang.md`.
> Hängt es? Sucht die Fehlermeldung in der Tabelle „Troubleshooting“ am Ende. Ohne Endpunkt
> könnt ihr trotzdem Teil 1 bis einschließlich `pytest tests/test_rag.py` bearbeiten, denn diese
> Selbsttests laufen offline.

---

## Teil 1: Den RAG-Client bauen (35 min)

Eine Trefferliste ist noch keine Antwort. Ihr hängt an die Suche aus VL 4 die zwei fehlenden
Schritte an:

```
Frage → Retrieve (VL 4): Top-k Chunks
      → Augment: Kontextblock mit [Quelle N | datei.md] und System-Prompt
      → Generate: Das LLM antwortet belegt, z. B. „… nach 30 Minuten Inaktivität. [Quelle 1]“
```

### Aufgabe 1A: Vorlage kopieren, Prompt und Kontextblock bauen (12 min)

```bash
cp labs/templates/rag_skeleton.py src/rag.py
python -m pytest tests/test_rag.py -q
```

Erwartet: `8 failed`. Das ist gewollt. Jeder Fehler zeigt auf ein TODO in `src/rag.py`.

**TODO 1, System-Prompt.** Die Vorlage startet mit einem naiven Prompt: „Du bist ein hilfreicher
Assistent. Beantworte die Frage.“ Überlegt kurz zu zweit, was fehlt.
Ergänzt dann die drei Pflichtelemente:

1. **Grounding:** nur aus dem Kontext antworten, kein Vorwissen.
2. **Enthaltung:** Fehlt die Antwort im Kontext, antwortet das Modell wörtlich mit `ABSTENTION`
   („Ich habe dazu keine Information in der Wissensbasis.“). Baut den Satz per f-String ein. Nur
   ein fester Wortlaut lässt sich später per String-Vergleich zählen.
3. **Zitierpflicht:** jede Aussage mit `[Quelle N]` belegen.

**TODO 2, `build_context`.** Pro Treffer eine Zeile `[Quelle N | <source>]: <text>`. N zählt ab 1
in Trefferreihenfolge. Der beste Treffer steht vorn, weil Modelle die Mitte eines langen Kontexts
schlechter nutzen (Lost in the Middle). Zeilenumbrüche im Text werden zu Leerzeichen.

**TODO 3, `build_prompt`.** Erst der Kontextblock, dann die markierte Frage. So liest das Modell
die Frage nicht als Teil des Kontexts.

Selbsttest ohne Endpunkt:

```bash
python -c "
from src.rag import build_context
hits = [
    {'rank': 1, 'source': 'vpn-zugang.md', 'text': 'Nach 12 Stunden oder 30 Minuten\nInaktivität trennt das Gateway automatisch.'},
    {'rank': 2, 'source': 'it-support-prozesse.md', 'text': 'Hotline intern -4242'},
]
print(build_context(hits))
"
```

Erwartete Ausgabe:

```
[Quelle 1 | vpn-zugang.md]: Nach 12 Stunden oder 30 Minuten Inaktivität trennt das Gateway automatisch.

[Quelle 2 | it-support-prozesse.md]: Hotline intern -4242
```

### Aufgabe 1B: `answer()` verbinden und das CLI nutzen (13 min)

**TODO 4, `answer`.** Verbindet die drei Schritte. Anforderungen:

1. Retrieve mit dem übergebenen `retriever` und `n_results`. Der Default ist die dichte Suche
   `embedding_search`. In Teil 2 tauscht ihr sie ohne Codeänderung gegen `hybrid_search`.
2. Liefert der Retriever nichts, gebt ihr `ABSTENTION` zurück, ohne `chat()` aufzurufen.
3. Augment und Generate: `chat(build_prompt(query, context), system=system_prompt)`.
4. `sources` ist eine Liste in Trefferreihenfolge, pro Chunk ein Eintrag mit Label und Datei:
   `[{"label": "Quelle 1", "source": "vpn-zugang.md"}, ...]`. So passt jedes Label im Antworttext
   zu genau einer Datei.
5. Rückgabe: `{"answer": ..., "sources": ..., "hits": ..., "context": ...}`. Die Antwort wird mit
   `.strip()` bereinigt, weil manche Modelle mit Leerzeilen beginnen. Den Kontext braucht später
   die Evaluation.

```bash
python -m pytest tests/test_rag.py -q
```

Erwartet: `8 passed`. Jetzt mit Endpunkt:

```bash
python -m src.rag "Wie lange bleibt die VPN-Verbindung bestehen?"
```

Erwartete Ausgabe (schematisch, Wortlaut und Quellen hängen von Modell und Retrieval ab):

```
Frage: Wie lange bleibt die VPN-Verbindung bestehen?

Antwort:
  Die VPN-Verbindung wird nach 12 Stunden oder nach 30 Minuten Inaktivität
  automatisch getrennt. [Quelle 1]

Quellen:
  [Quelle 1] vpn-zugang.md
  [Quelle 2] vpn-zugang.md
  …
```

**Prüft selbst:** Steht die Aussage wirklich in der zitierten Quelle? Öffnet die Datei in `docs/`.

### Aufgabe 1C: Enthaltung testen (10 min)

Stellt eine Frage, deren Antwort nicht in der Wissensbasis steht:

```bash
python -m src.rag "Wie viele Urlaubstage habe ich pro Jahr?"
```

Erwartet: `Ich habe dazu keine Information in der Wissensbasis.` Schaut auf die Quellenliste.
Der Retriever liefert trotzdem fünf Chunks, denn top-k liefert immer k Treffer, auch wenn keiner
passt. Deshalb braucht der Prompt die Enthaltungsanweisung.

**Experiment:** gleicher Retriever, gleicher Kontext, aber ein System-Prompt ohne
Enthaltungsanweisung.

```bash
python -c "
from src.rag import answer
ohne_enthaltung = 'Beantworte die Frage anhand des Kontexts. Zitiere mit [Quelle N].'
result = answer('Wie viele Urlaubstage habe ich pro Jahr?', system_prompt=ohne_enthaltung)
print(result['answer'])
"
```

**Diskutiert zu zweit:** Was antwortet das Modell jetzt? Klingt die Antwort überzeugend? Warum ist
das für einen IT-Support-Bot gefährlich?

> **Hinweis (modellabhängig):** Starke Modelle erfinden oft keine Zahl, sondern verweisen von sich
> aus an die Personalabteilung. Das ändert nichts an der Kernaussage. Ohne Enthaltungsanweisung ist
> ehrliches Nichtwissen nicht garantiert. Deutlicher wird der Effekt mit einer Frage, zu der der
> Kontext etwas Ähnliches enthält: „Wie viele Tage pro Woche darf ich im Homeoffice arbeiten?“ Die
> Wissensbasis beschreibt nur die technischen Anforderungen für Heimarbeit.

> **✓ Checkpoint 2:** `python -m pytest tests/test_rag.py -q` meldet `8 passed`, und der Bot
> enthält sich bei der Urlaubstage-Frage.
> Aufholen: `cp src/rag.py src/rag_eigene.py` sichert eure Version, danach holt
> `git checkout origin/vl05-rag-advanced-solution -- src/rag.py` die Musterlösung.

---

## Teil 2: Hybride Suche bauen und messen (30 min)

Die dichte Suche findet Bedeutung, auch bei Umschreibungen. Seltene exakte Begriffe in der Frage
gewichtet sie aber oft zu schwach: Namen, Fehlercodes, Gerätenummern. Die Keyword-Suche trifft
genau diese Begriffe wörtlich. Wichtig ist die Richtung: Keyword-Suche hilft nur, wenn der seltene
Begriff **in der Frage** steht. Bei „Welche Durchwahl hat Bernd Hagedorn?“ ist das „Hagedorn“. Die
Antwort „-4200“ kennt der Nutzer ja noch nicht.

### Aufgabe 2A: Das Problem ansehen (4 min)

```bash
python -m src.search "Welche Durchwahl hat Bernd Hagedorn?" --n 3
python -m src.search "Welche Durchwahl hat Bernd Hagedorn?" --n 3 --mode keyword
```

Die Keyword-Suche braucht kein Embedding und liefert deshalb bei allen dieselben Treffer (Vorschau
hier gekürzt):

```
Suche (keyword): "Welche Durchwahl hat Bernd Hagedorn?"
  1. [3] it-support-prozesse.md::6 — "(nur per Hotline). ## Eskalationsweg 1. **1st Level — Service Desk:** …"
  2. [3] it-support-prozesse.md::7 — "IT-Service (**Bernd Hagedorn**, Durchwahl -4200). ## Ticket-Lebenszyklus …"
  3. [1] drucker.md::3 — "Job freigeben. ## Häufige Störungen und Lösungen ### Job erscheint nicht am Gerät …"
```

Die Zahl in Klammern ist hier die Anzahl gemeinsamer Wörter. Rang 1 und 2 sind die beiden Chunks
mit „Bernd Hagedorn, Durchwahl -4200“: `it-support-prozesse.md::6` und `it-support-prozesse.md::7`.
Es sind zwei, weil sich benachbarte Chunks überlappen. Die Vorschau zeigt nur die ersten 200
Zeichen. Bei `::6` steht die Durchwahl erst am Ende des Chunks, deshalb fehlt sie in der Vorschau.
Rang 3 trifft nur über das Wort „hat“. Die Wortüberlappung aus VL 4 zählt jedes gemeinsame Wort
einmal, ohne IDF. „hat“ zählt also so viel wie „Hagedorn“. BM25 würde das seltene Wort stärker
gewichten.

Notiert für die dichte Suche, ob `it-support-prozesse.md::6` oder `::7` in den Top 3 steht. Achtet
auf die Chunk-ID, nicht auf die Vorschau.

### Aufgabe 2B: RRF implementieren (10 min)

```bash
cp labs/templates/hybrid_skeleton.py src/hybrid.py
python -m pytest tests/test_hybrid.py -q
```

Erwartet: `11 failed`. **TODO 1, `reciprocal_rank_fusion`:** Jeder Chunk bekommt

```
score(d) = Σ 1 / (k + rang_r(d))    über alle Ranglisten r, in denen d vorkommt, k = 60
```

Der Rang beginnt bei 1. Fehlt ein Chunk in einer Liste, trägt diese Liste nichts bei. Als Identität
eines Chunks dient sein Text. Die Scores der beiden Suchen braucht RRF nicht, nur die Ränge.
Kosinus-Ähnlichkeit und Anzahl gemeinsamer Wörter wären ohnehin nicht vergleichbar.

Selbsttest mit dem Beispiel aus der Vorlesung (dense A·C·B·D, BM25 B·A·D·E):

```bash
python -c "
from src.hybrid import reciprocal_rank_fusion
dense = [{'text': t, 'source': '-'} for t in 'ACBD']
bm25 = [{'text': t, 'source': '-'} for t in 'BADE']
for hit in reciprocal_rank_fusion([dense, bm25]):
    print(hit['rank'], hit['text'], round(hit['score'], 4))
"
```

Erwartete Ausgabe:

```
1 A 0.0325
2 B 0.0323
3 D 0.0315
4 C 0.0161
5 E 0.0156
```

D steht vor C, obwohl C in der dichten Liste besser platziert ist. D steht in beiden Listen und
sammelt zwei Beiträge.

### Aufgabe 2C: `hybrid_search` bauen (6 min)

**TODO 2, `hybrid_search`:** Beide Suchen mit einem größeren Kandidatenfenster aufrufen
(`n_results * CANDIDATE_FACTOR`, also 4-mal so viele), damit die Fusion echte Auswahl hat. Dann
fusionieren und die Top-k zurückgeben. Das Format ist dasselbe wie bei `embedding_search`:
`{"rank", "chunk_id", "source", "score", "text"}`. Deshalb nutzt `src/rag.py` die Funktion ohne
Änderung.

> **Hinweis:** `keyword_search` liefert nur Chunks mit Wortüberlappung. Die beiden Listen können
> also unterschiedlich lang oder sogar leer sein. Für RRF ist das kein Problem.

```bash
python -m pytest tests/test_hybrid.py -q
python -m src.hybrid "Welche Durchwahl hat Bernd Hagedorn?" --n 3
```

Erwartet: `11 passed`. Die Ausgabe zeigt wie `src.search` pro Treffer Score, Chunk-ID und
Vorschau. Der Score ist hier der RRF-Score und liegt um 0,03. Oben sollten die beiden Chunks mit
„Durchwahl -4200“ stehen. Prüft die IDs `it-support-prozesse.md::6` und `::7`. Die Keyword-Suche
hat beide auf Rang 1 und 2. Findet auch die dichte Suche sie unter ihren 12 Kandidaten (`--n 3`
mal `CANDIDATE_FACTOR` 4), sammeln sie Beiträge aus beiden Listen. Vergleicht mit eurer Notiz aus
2A. Die RAG-Antwort dazu holt ihr mit
`python -m src.rag "Welche Durchwahl hat Bernd Hagedorn?" --retriever hybrid --n 3`.

### Aufgabe 2D: Messen statt glauben (10 min)

Eine einzelne Frage beweist nichts. Das Evalset `eval/rag_eval.jsonl` enthält 17 Fragen in vier
Typen: einfach, schwer (mehrere Teilfakten), keyword (die Frage enthält einen seltenen, exakten
Begriff) und unbeantwortbar. Jede beantwortbare Frage nennt ihre Belegstellen im Feld `evidence`.

```bash
python -m src.rag_eval --retrieval-only --retriever keyword --n 3
python -m src.rag_eval --retrieval-only --retriever dense --n 3
python -m src.rag_eval --retrieval-only --retriever hybrid --n 3
```

`--retrieval-only` ruft kein Chat-Modell auf und läuft in Sekunden. Der Report zeigt zwei Zahlen:

- **Datei-Treffer:** Stammt mindestens ein Chunk der Top-k aus der erwarteten Datei?
- **Beleg-Treffer:** Stehen alle Belegstellen der Frage in abgerufenen Chunks der erwarteten Datei?
  Das ist eine grobe, deterministische Näherung an Context Recall. Chunks aus anderen Dateien
  zählen bewusst nicht. „2 Stunden“ steht zum Beispiel auch bei den Leihgeräten in
  `hardware-bestellung.md`, die SLA-Frage meint aber die Tabelle in `it-support-prozesse.md`.

Warum `--n 3`? Mit fünf Chunks findet schon die dichte Suche fast alles. Erst das kleine
Kontextfenster macht Unterschiede im Retrieval sichtbar (top-k-Trade-off aus der Vorlesung).

Die Keyword-Messung hängt nicht vom Embedding-Modell ab. Ihr Report endet deshalb bei allen so:

```
==============================================================================
RAG-Evaluation · retriever=keyword · n=3 · nur Retrieval · 17 Fragen
==============================================================================
  Datei-Treffer:            14/14 beantwortbare Fragen
  Beleg-Treffer:            12/14 (alle Belege im Kontext)
  Ohne vollständigen Beleg:
    - Ich habe mein Passwort vergessen und keine MFA registriert. Was kann ich tun?
    - Wie beantrage ich eine kostenpflichtige Lizenz, und was passiert, wenn der Antrag hängen bleibt?
==============================================================================
```

Tragt eure Zahlen ein:

| Retriever (n = 3) | Datei-Treffer | Beleg-Treffer | Fragen ohne vollständigen Beleg |
|---|---|---|---|
| keyword | 14/14 | 12/14 | Passwort ohne MFA, kostenpflichtige Lizenz |
| dense | | | |
| hybrid | | | |

> **Hinweis:** Unser `hybrid` kombiniert dense mit einer einfachen Wortüberlappung, nicht mit
> BM25. Ein schwaches Ergebnis im Lab widerlegt BM25-Hybrid also nicht.

> **Zum Nachschlagen: die sieben Fehlerpunkte** nach Barnett et al. (2024), „Seven Failure Points
> When Engineering a Retrieval Augmented Generation System“
>
> | # | Fehlerpunkt | Was passiert | Stufe |
> |---|---|---|---|
> | 1 | Fehlender Inhalt | Die Antwort steht nicht in der Wissensbasis. Das System antwortet trotzdem. | Wissensbasis |
> | 2 | Nicht top-gerankt | Der relevante Chunk existiert, landet aber nicht in den Top-k. | Retrieval |
> | 3 | Nicht im Kontext | Der Chunk wurde abgerufen, fällt aber beim Zusammenstellen des Kontexts heraus (Kontextbudget, Kürzung). | Konsolidierung |
> | 4 | Nicht extrahiert | Die Antwort steht im Kontext, das LLM findet sie nicht (Rauschen, Widersprüche). | Generierung |
> | 5 | Falsches Format | Der Inhalt stimmt, das verlangte Format (Tabelle, Liste) fehlt. | Generierung |
> | 6 | Falsche Spezifität | Die Antwort ist zu allgemein oder zu detailliert für den Bedarf. | Anfrage, Generierung |
> | 7 | Unvollständig | Eine Teilantwort, obwohl alles Nötige im Kontext stand. | Generierung |
>
> Die Messung mit `--retrieval-only` prüft nur das Retrieval. Ob sich das System bei fehlendem
> Inhalt enthält und ob es die Antwort aus dem Kontext richtig herauszieht, zeigen erst die
> Antworten (Bonus B1 bis B4).

**Diskutiert zu zweit:**

- Bei welcher Frage unterscheiden sich dense und hybrid? Welcher Fehlerpunkt liegt vor, wenn der
  richtige Chunk existiert, aber nicht in den Top-k landet?
- Bei der Passwort-Frage zeigt der Datei-Treffer ✓, die Belege aber 0/2. Was misst der
  Datei-Treffer also wirklich?
- Ist hybrid überall besser? Wo hilft es, wo nicht?

> **✓ Checkpoint 3:** `python -m pytest tests/test_hybrid.py -q` meldet `11 passed`, und eure
> Tabelle hat drei Zeilen.
> Aufholen: `cp src/hybrid.py src/hybrid_eigene.py` sichert eure Version, danach holt
> `git checkout origin/vl05-rag-advanced-solution -- src/hybrid.py` die Musterlösung.

---

## Teil 3: Abschluss und Reflexion (10 min)

Beantwortet zu zweit mindestens drei Fragen (5 min). Danach sammeln wir im Plenum (5 min).

1. Eure Tabelle misst nur das Retrieval. Welche Frage scheitert schon dort? Was müsstet ihr
   zusätzlich messen, um einen Fehler in der Generierung zu erkennen (Teil 4 der Vorlesung,
   Bonus B1 bis B4)? Angenommen, diese Messung ergibt Faithfulness hoch und Context Recall
   niedrig: Welche Komponente ist schuld, und was tut ihr?
2. Ordnet eine Frage ohne vollständigen Beleg einem der sieben Fehlerpunkte zu. Welche Maßnahme
   würdet ihr als Nächstes ausprobieren und wie würdet ihr sie messen?
3. Warum hilft die Keyword-Suche bei der Durchwahl-Frage, obwohl „-4200“ gar nicht in der Frage
   steht?
4. Bei „Ich habe mein Passwort vergessen und keine MFA registriert“ scheitert die Keyword-Suche.
   Welche Wörter der Frage treffen, und warum ist das ohne IDF ein Problem? (Tipp: „kann“ steht in
   12 von 80 Chunks, „registriert“ in einem.)
5. Der Datei-Treffer der Keyword-Suche war 14/14, der Beleg-Treffer 12/14. Was lernt ihr daraus
   über Metriken, deren Name mehr verspricht, als sie messen?
6. Bei 14 beantwortbaren Fragen verschiebt eine einzige Frage das Ergebnis um rund 7 Prozentpunkte.
   Ist ein Unterschied von einer Frage ein Beleg? Was bräuchtet ihr für einen belastbaren Vergleich?
7. Die ganze LeineTech-Wissensbasis hat nur rund 31 KB und passt in das Kontextfenster des
   Kursmodells. Warum lohnt sich Retrieval trotzdem? Denkt an Kosten, Latenz, Lost in the Middle,
   Zitierbarkeit und an eine Wissensbasis mit 10.000 Dokumenten.

---

## Bonus: Vertiefung für Schnelle

Alles ab hier ist freiwillig. Die Aufgaben bauen aufeinander auf, ihr könnt aber auch einzelne
auswählen.

### B1: Antworten messen und Enthaltungen zählen (5 min)

```bash
python -m src.rag_eval --retriever hybrid --n 3
```

Ohne `--retrieval-only` erzeugt das Werkzeug zu jeder Frage eine Antwort. Das sind 17 Aufrufe
und dauert einige Minuten. Der Report zählt zusätzlich:

- **Enthaltung korrekt:** Das System enthält sich bei unbeantwortbaren Fragen.
- **Fälschliche Enthaltung:** Das System enthält sich, obwohl die Antwort existiert. Das ist ehrlich,
  aber nutzlos. Häufige Ursache: Der richtige Chunk fehlte im Kontext.

Die Spalten `Faith` und `Relev` zeigen `–`, bis ihr B2 und B3 erledigt habt.

### B2: Einen Faithfulness-Judge bauen (15 min)

In `src/rag_eval.py` ist `judge_claims` noch TODO V1. Der Judge soll

1. die Antwort in einzelne Aussagen zerlegen,
2. jede Aussage einzeln gegen den Kontext prüfen und
3. nur JSON ausgeben: `{"aussagen": [{"aussage": "...", "gestützt": true}]}`.

Ruft `chat(prompt, system=JUDGE_SYSTEM, temperature=0.0)` auf und lest das Ergebnis mit der
fertigen Funktion `parse_json_object`. Die Quote `gestützt / gesamt` rechnet schon
`supported_share` in Python. Ist die Judge-Antwort nicht verwertbar, gebt ihr `None` zurück. Der
Report zählt sie dann als nicht bewertet, statt eine falsche 0 oder 1 einzutragen. Nicht
verwertbar ist die Antwort auch, wenn nur eine einzige Aussage bei „gestützt“ keinen Wert `true`
oder `false` hat, etwa „teilweise“. Lasst ihr solche Aussagen einfach weg, schönt das die Quote.

Selbsttest ohne Endpunkt: Die Tests für die Judges liegen in der Musterlösung. Holt sie euch und
startet sie:

```bash
git checkout origin/vl05-rag-advanced-solution -- tests/test_judge.py
python -m pytest tests/test_judge.py -q
```

Vor V1 und V2 meldet der Test `4 failed`, nach V1 noch `2 failed`. Sind B2 und B3 erledigt, meldet
er `24 passed` und kein `failed`.

Warum nicht einfach „Gib die Quote als Zahl aus“? Judges plaudern gern. Aus „3/4 Aussagen
gestützt, also 0.75“ liest ein naiver Parser die 3 und klemmt sie auf 1,0. Das ist dieselbe Idee
wie bei RAGAS: Das Modell urteilt pro Aussage, gerechnet wird im Code. RAGAS nutzt dafür zwei
Aufrufe, unsere vereinfachte Form einen.

### B3: Einen Relevanz-Judge bauen (5 min)

`answer_relevancy` ist TODO V2. Der Judge bewertet, wie direkt die Antwort die Frage beantwortet,
und gibt `{"relevanz": 0.8}` zurück. Die fertige Funktion `parse_score` liest den Wert. Bedenkt die
Grenze: Ohne Referenzantwort kann kein Judge prüfen, ob die Antwort vollständig ist. RAGAS geht
anders vor. Es erzeugt aus der Antwort Fragen und vergleicht sie per Embedding mit der
Originalfrage. Ausweichende Antworten wie eine Enthaltung bewertet RAGAS dabei mit 0. Unser Report
zählt Enthaltungen deshalb getrennt und mittelt die Judge-Werte nur über echte Antworten.

Danach vergleicht ihr beide Retriever. Mit Judges sind das bis zu 45 Aufrufe pro Lauf:

```bash
python -m src.rag_eval --retriever dense --n 3
python -m src.rag_eval --retriever hybrid --n 3
```

| Retriever (n = 3) | Faithfulness Ø | Answer Relevancy Ø | Fälschliche Enthaltung | Enthaltung korrekt |
|---|---|---|---|---|
| dense | | | | |
| hybrid | | | | |

Richtwerte aus der Vorlesung, keine Normen: Faithfulness über 0,8 ist stark, unter 0,5
bedenklich. Answer Relevancy über 0,8 ist stark, unter 0,6 bedenklich.

### B4: Den Judge prüfen (5 min)

```bash
python -m src.rag_eval --retriever hybrid --n 3 --details
```

`--details` zeigt unter jeder Frage die Einzelurteile des Judges (✓ gestützt, ✗ nicht gestützt).
Prüft drei Urteile von Hand gegen den Kontext. Stimmt ihr zu? Hier bewertet das Kursmodell seine
eigenen Antworten (Selbstverstärkungsbias). Einen Judge prüft man wie ein Messgerät: an Beispielen,
die Menschen bewertet haben.

### B5: Eigene Fragen ergänzen (10 min)

Ergänzt in `eval/rag_eval.jsonl` zwei Fragen im gleichen Format:

- eine Keyword-Frage mit einem seltenen Begriff in der Frage (Gerätenummer, Fehlercode, Name aus
  `docs/`),
- eine unbeantwortbare Frage, zu der die Wissensbasis etwas Ähnliches enthält.

```bash
python -m pytest tests/test_rag_eval.py -q
```

Der Test prüft das Format, echte Umlaute und ob jede Belegstelle wirklich in der erwarteten Datei
steht. Schreibt „Priorität“, nicht „Prioritaet“. Sonst findet die Keyword-Suche das Wort im
Dokument nicht.

### B6: Die RRF-Konstante verstehen (5 min, ohne Endpunkt)

Chunk X steht in der dichten Liste auf Rang 5 und in BM25 auf Rang 2. Chunk Y steht nur in der
dichten Liste auf Rang 1. Wer gewinnt bei k = 0, k = 1 und k = 60? Rechnet erst von Hand, dann:

```bash
python -c "
from src.hybrid import reciprocal_rank_fusion
dense = [{'text': t, 'source': '-'} for t in ['Y', 'a', 'b', 'c', 'X']]
bm25 = [{'text': t, 'source': '-'} for t in ['d', 'X']]
for k in (0, 1, 60):
    scores = {h['text']: round(h['score'], 4) for h in reciprocal_rank_fusion([dense, bm25], k=k)}
    print(f'k={k}: X={scores[\"X\"]}  Y={scores[\"Y\"]}')
"
```

Erwartete Ausgabe:

```
k=0: X=0.7  Y=1.0
k=1: X=0.5  Y=0.5
k=60: X=0.0315  Y=0.0164
```

Ein kleines k lässt Spitzenplätze dominieren. Ein großes k belohnt vor allem, in mehreren Listen zu
stehen. k = 60 ist ein bewährter Standardwert ohne Tuning, aber nicht für jeden Korpus optimal.

### B7: RAGAS ausprobieren (optional, außerhalb des Labs)

In Produktion nimmt man ein Framework wie `ragas`. Es ist bewusst nicht in `requirements.txt`,
damit das Lab ohne zusätzliche Abhängigkeit läuft. Wer es ausprobiert, installiert es selbst und
pinnt die Version, denn die API ändert sich zwischen Releases. Stand September 2026 (ragas 0.4.x)
liegen die Metriken in `ragas.metrics.collections`. Die alte Funktion `evaluate()` gilt als veraltet
und lässt sich nicht mit den neuen Metriken mischen. Prüft vorher die aktuelle Doku.

---

## Troubleshooting

| Problem | Ursache und Lösung |
|---|---|
| `git checkout` meldet „Your local changes would be overwritten“ oder „untracked working tree files would be overwritten“ | Eigene VL-4-Dateien liegen noch im Arbeitsverzeichnis. Erst sichern (Schritt 0.1), dann auschecken. |
| `pathspec 'vl05-rag-advanced-start' did not match` | Der Branch ist lokal unbekannt. Erst `git fetch origin`, dann erneut auschecken. |
| `ModuleNotFoundError: No module named 'src.rag'` oder `'src.hybrid'` | Die Vorlage ist noch nicht kopiert: `cp labs/templates/rag_skeleton.py src/rag.py` bzw. `hybrid_skeleton.py`. Befehle immer im Repo-Root ausführen. |
| `NotImplementedError: TODO …` | Gewollt. Das Programm läuft bis zum ersten offenen TODO. Die Meldung nennt Datei und Nummer. |
| `pytest` meldet die Lab-Tests als `skipped` | Die zugehörige Datei in `src/` fehlt noch. Nach dem Kopieren der Vorlage laufen die Tests. |
| `TypeError: unsupported operand type(s) for \|` | Python älter als 3.10. Neuere Version installieren und die `.venv` neu anlegen. |
| `Die Collection ist leer` oder `Collection 'leinetech_kb' ist leer` | Erst indexieren: `python -m src.ingest docs`. `chroma_db/` liegt relativ zum aktuellen Ordner. Befehle im Repo-Root ausführen. |
| Mehr als 80 Einträge im Index oder Ergebnisse weichen von der Anleitung ab | Im Index liegen noch Chunks von Dateien, die es in `docs/` nicht mehr gibt, etwa eigene Testdokumente aus VL 4. Das Ingest ersetzt nur die Chunks der aktuellen Dateien. Index löschen und neu bauen: `rm -rf chroma_db && python -m src.ingest docs` (PowerShell: `Remove-Item -Recurse -Force chroma_db`). Das braucht den Endpunkt. |
| `InvalidArgumentError: Collection expecting embedding with dimension of …, got …` | Index und Anfrage stammen aus verschiedenen Embedding-Modellen (Gleiches-Modell-Regel aus VL 4). Die Collection behält ihre Dimension auch dann, wenn das Ingest ihre Chunks löscht. Deshalb hilft nur ein neuer Index: `rm -rf chroma_db && python -m src.ingest docs`. |
| Erste Anfrage hängt minutenlang oder endet mit `Timeout` | Cold Start am Kurs-Endpunkt (200 bis 300 s). Das Ingest wartet, also nicht abbrechen. Chat-Aufrufe (`src.rag`, `src.rag_eval` mit Antworten) brechen nach 120 s ab: `export LLM_TIMEOUT=360` setzen und den Befehl wiederholen. |
| 403 oder „nur montags …“ | Außerhalb des Zeitfensters, oder `LLM_API_KEY` bzw. `LLM_BASE_URL` fehlen in dieser Shell. Die Variablen gelten nur im aktuellen Terminal. |
| `Failed to send telemetry event …` | Kosmetisch (chromadb 1.0.7 gegen neuere posthog-Versionen). `src/vectorstore.py` schaltet die Telemetrie bereits ab. |
| Das Modell ignoriert den Kontext oder erfindet Antworten | System-Prompt prüfen: Grounding, fester Enthaltungs-Wortlaut und Zitierpflicht (TODO 1). Wird `system_prompt` wirklich an `chat()` übergeben? |
| Der Bot antwortet immer mit der Enthaltung | Kommen Treffer an? `n_results` größer 0? Mit `--n 5` und einer Frage aus dem Evalset testen. |
| Hybrid liefert dasselbe wie dense | Kandidatenfenster zu klein. Beide Suchen mit `n_results * CANDIDATE_FACTOR` aufrufen. |
| `python -c "…"` funktioniert unter Windows nicht | Die PowerShell verarbeitet mehrzeilige Anführungszeichen anders. Den Python-Code in eine Datei schreiben und mit `python datei.py` ausführen. |
| Der Report zeigt `Faith –` und `Relev –` | Die Judges sind noch TODO (B2, B3), oder der Judge lieferte kein verwertbares JSON. `--details` zeigt die Einzelurteile. |

## Wie geht es weiter?

Die Musterlösung liegt im Branch `vl05-rag-advanced-solution` (`src/rag.py`, `src/hybrid.py` und
`src/rag_eval.py` mit beiden Judges). Dort meldet `python -m pytest -q` nur bestandene Tests, kein
`failed` und kein `skipped`.

In VL 6 greift ihr euer eigenes System an. Bei RAG landet die Wissensbasis im Prompt, bei der
Triage der Ticket-Text. VL 6 greift die Triage an. Was passiert, wenn solche Daten selbst
Anweisungen enthalten?

**Vorbereitung auf VL 6:** keine Installation. Committet eure VL-5-Arbeit, denn Schritt 0 im
VL-6-Lab verlangt ein sauberes `git status`:

```bash
git switch -c meine-vl05-loesung && git add -A && git commit -m "VL 5"
```
