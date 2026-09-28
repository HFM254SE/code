# Lab VL 4: Ingestion-Pipeline für die LeineTech-Wissensbasis

Im Ticket T-1018 schreibt ein Kollege, dass das Internet auf seinem Firmengerät seit dem letzten
AnyConnect-Update quälend langsam ist. Die Antwort steht in unserer Wissensbasis
(`docs/vpn-zugang.md`, Abschnitt „Bekanntes Problem (Mai 2026)“). Das LLM aus VL 3 kommt aber nicht
heran. In diesem Lab baut ihr die Retrieval-Hälfte eines RAG-Systems: Dokumente laden, in Chunks
zerlegen, als Vektoren einbetten, in ChromaDB speichern und durchsuchen. Am Ende messt ihr an neun
Testfragen, wann die semantische Suche die richtige Passage findet und wann eine einfache
Keyword-Suche besser ist. In VL 5 wird aus den Treffern eine belegte Antwort.

**Leitfrage:** Findet unsere Suche die richtige Passage, und wann gewinnt die Keyword-Suche?

| | |
|---|---|
| **Dauer** | ca. 90 min in der Präsenz |
| **Sozialform** | 2er-Teams erwünscht, allein geht auch |
| **Start-Branch** | `vl04-rag-ingestion-pipeline-start` |
| **Musterlösung** | `vl04-rag-ingestion-pipeline-solution` (VL 5 startet auf `vl05-rag-advanced-start`, das sie enthält) |
| **Werkzeuge** | Python, pytest, litellm, ChromaDB, Kurs-Endpunkt mit `qwen3-embed-4b` |
| **Stand der Zahlen** | 25.09.2026, gemessen mit der Musterlösung (Chunk-Größe 500, Überlappung 50) |

---

## Lernziele

Nach diesem Lab könnt ihr …

1. eine Ingestion-Pipeline Dokumente → Chunks → Embeddings → ChromaDB **implementieren** und jeden
   Schritt einzeln **prüfen**.
2. rekursives Chunking mit Überlappung **umsetzen** und die Wirkung der Chunk-Größe an Zahlen
   **erklären**.
3. die Distanz von ChromaDB in eine Kosinus-Ähnlichkeit **umrechnen** und **begründen**, warum das
   nur für normierte Vektoren gilt.
4. semantische Suche und Keyword-Suche an Testfragen mit Treffer@1 und Treffer@3 **vergleichen** und
   das Ergebnis **begründen**.

---

## Voraussetzungen

**Wissen:** VL 4 Teil 3 bis 5 (Chunking-Strategien, Embeddings und Kosinus-Ähnlichkeit,
Gleiches-Modell-Regel, Vektordatenbank). Wer nacharbeitet, liest vorher die Folien dieser Teile.

**Software und Zugang:**

| Was | Version oder Stand | Prüfen mit |
|---|---|---|
| Repo `leinetech` aus VL 1 | Klon von `https://github.com/HFM254SE/code.git` | `git remote -v` |
| Python | 3.12 oder 3.13 (wie in VL 1) | `python --version` (Windows: `py --version`) |
| Kurs-API-Key | persönlich, aus VL 1 | siehe `SETUP.md` |
| Kurs-Endpunkt | nur **montags von 06:00 bis 23:59 Uhr** | Chat-Test in Schritt 0 |

Unter Windows funktionieren alle Befehle in **Git Bash**. Der Endpunkt loggt Prompts und Antworten.
Schickt deshalb keine Passwörter, Secrets oder echten Personendaten.

### Checkpoint-Branches

| Branch | Inhalt |
|---|---|
| `vl03-evaluation` | Stand nach VL 3 (LLM-Anschluss und Evaluierung) |
| `vl04-rag-ingestion-pipeline-start` | Ausgangszustand für dieses Lab: alle Module als Gerüst mit TODOs |
| `vl04-rag-ingestion-pipeline-solution` | Musterlösung |
| `vl05-rag-advanced-start` | Start für VL 5, enthält die Musterlösung von heute |

### Zeitplan

| Schritt | Inhalt | Minuten | Ergebnis |
|---|---|---|---|
| 0 | Setup: Branch, Umgebung, Endpunkt vorwärmen | 10 | Chat antwortet, Tests laufen |
| 1 | Laden und Chunken | 20 | `tests/test_chunker.py`: 13 passed, 80 Chunks |
| 2 | Embeddings und Vektordatenbank | 30 | Collection `leinetech_kb` mit 80 Einträgen |
| 3 | Suche messen statt glauben | 20 | ausgefüllte Messtabelle |
| Reflexion | 2 bis 3 Teams stellen vor | 10 | begründete Antworten auf die Leitfragen |
| **Summe** | | **90** | |

Wer zu Hause nacharbeitet, rechnet mit etwa 100 Minuten, weil Cold Starts und Setup dazukommen.

### So arbeitet ihr

Der Start-Branch enthält alle sechs Module der Pipeline als Gerüst. Was fehlt, ist mit
`TODO Teil …` markiert. Bis ihr es füllt, wirft die Funktion einen `NotImplementedError` mit genau
diesem Text. So seht ihr bei jedem Aufruf, wo es weitergeht. Alle offenen Stellen auf einen Blick:

```bash
grep -n "TODO Teil" src/*.py
```

Die Tests sind eure Vorgabe. Sie laufen offline: Das Embedding-Modell wird in
`tests/test_pipeline_offline.py` durch eine Attrappe ersetzt. Ihr könnt also jeden Teil auch dann
prüfen, wenn der Endpunkt gerade nicht erreichbar ist. Ein KI-Assistent (Continue aus VL 1) ist
erlaubt. Prüft seine Vorschläge wie in VL 1 mit den Tests.

**Aufholen:** Wer hängt, holt sich die fertige Datei aus der Musterlösung und macht mit dem
nächsten Teil weiter. Die Befehle stehen am Ende jedes Teils.

---

## Schritt 0: Setup (10 min)

Tipp: Startet die Punkte 1 und 2 schon in der Pause vor dem Lab. ChromaDB lädt beim Installieren
einige Pakete nach.

**1. Branch wechseln.** Eigene Änderungen aus VL 3 sichert ihr vorher, sonst verweigert git den
Wechsel.

```bash
cd leinetech
git status                                        # eigene Änderungen? Dann zuerst sichern:
git stash -u                                      # oder auf einem eigenen Branch committen
git fetch origin                                  # holt die neuen Checkpoint-Branches
git checkout vl04-rag-ingestion-pipeline-start
git switch -c lab-vl04                            # eigener Arbeitsbranch
```

**2. Umgebung.** Nutzt die venv aus VL 1. Neu seit VL 3 ist ChromaDB.

```bash
source .venv/bin/activate                         # Windows Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt
python -c "import chromadb; print('ChromaDB', chromadb.__version__)"
```

Erwartet: `ChromaDB 1.0.7`. Keine venv vorhanden? `python3 -m venv .venv` (Windows:
`py -3.12 -m venv .venv`), dann wie oben.

**3. Kurs-Endpunkt.** Die Variablen gelten nur in dieser Shell. In jedem neuen Terminal setzt ihr
sie erneut. Wir nutzen bewusst `export` statt einer `.env`-Datei.

```bash
export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"                   # Key siehe SETUP.md
export PYTHONUTF8=1                               # Windows: Ausgabe in UTF-8
LLM_TIMEOUT=360 python -c "from src.llm import chat; print(chat('Sag nur: OK'))"
```

Erwartet: `OK` oder eine ähnlich kurze Antwort. Die erste Anfrage kann durch den Cold Start 200 bis
300 Sekunden dauern. Das ist kein Fehler. Der Default-Timeout von 120 s reicht dafür nicht. Deshalb
startet der Test mit `LLM_TIMEOUT=360`.

`PYTHONUTF8=1` braucht ihr unter Windows. Python schreibt dort in eine Pipe wie `| tee` sonst in der
Codepage cp1252. Sonderzeichen wie „→“ aus der Wissensbasis brechen die Ausgabe dann ab. Unter macOS
und Linux ändert die Variable nichts.

**4. Embedding-Modell vorwärmen.** `qwen3-embed-4b` ist ein eigenes Modell mit eigenem Cold Start.
Öffnet ein zweites Terminal, aktiviert dort die venv, setzt die Variablen aus Punkt 3 und startet:

```bash
python -c "from src.llm import get_base_url, get_api_key; import litellm; r = litellm.embedding(model='hosted_vllm/qwen3-embed-4b', input=['Test'], api_base=get_base_url(), api_key=get_api_key()); print(len(r['data'][0]['embedding']), 'Dimensionen')"
```

Erwartet: `2560 Dimensionen`. Wartet nicht darauf. Beginnt parallel mit Teil 1, der ohne Endpunkt
auskommt.

**5. Tests als Landkarte.**

```bash
python -m pytest -q --tb=line
```

Erwartet in der letzten Zeile: `28 failed, 5 passed`. Das ist Absicht. Die 5 grünen Tests prüfen
die Triage aus VL 1. Die 28 roten Tests sind eure Vorgabe für heute: 13 in `tests/test_chunker.py`
(Teil 1) und 15 in `tests/test_pipeline_offline.py` (Teil 2 und 3). `--tb=line` zeigt pro rotem Test
nur eine Zeile mit Datei, Zeilennummer und `NotImplementedError: TODO Teil …`. So seht ihr direkt die
offene Stelle.

**6. Korpus ansehen.** `docs/` enthält 8 Markdown-Artikel der LeineTech-IT (VPN, Drucker, Passwort,
E-Mail, Hardware, Netzwerk, Software, Support-Prozesse). Öffnet `docs/vpn-zugang.md` und sucht den
Abschnitt „Bekanntes Problem (Mai 2026)“. Diese Passage soll eure Suche am Ende zu T-1018 finden.

---

## Teil 1: Laden und Chunken (20 min)

**Dokumente → Laden → Chunking** → Embedding → Speichern

### A: Loader (5 min)

Füllt `TODO Teil 1A` in `src/loader.py`. Anforderungen:

1. Alle `.md`-Dateien aus dem Verzeichnis einlesen, sortiert nach Dateiname.
2. Pro Datei ein Dict mit `text` (Inhalt ohne Leerraum am Rand) und `metadata` mit `source`
   (Dateiname).
3. Leere Dateien überspringen. Fehlt das Verzeichnis, einen `FileNotFoundError` werfen.

**Checkpoint 1A:**

```bash
python -m pytest tests/test_chunker.py -q -k load
```

Erwartet: `4 passed, 9 deselected`.

### B: Chunker (15 min)

`src/chunker.py` setzt rekursives Chunking (Strategie 2 aus der Vorlesung) in vier Schritten um:
rekursiv trennen, packen, sehr kurze Chunks verschmelzen, überlappen. Packen (`_pack`) und
Verschmelzen (`_merge_small`) sind fertig. Lest beide Funktionen kurz. Eure Aufgaben:

- `TODO Teil 1B-1` in `_recursive_split`: das rekursive Trennen.
- `TODO Teil 1B-2` in `_add_overlap`: die Überlappung.
- `TODO Teil 1B-3` in `chunk_document`: Metadaten und `chunk_id` je Chunk.

Anforderungen:

1. Trennzeichen in dieser Reihenfolge: Absatz `\n\n`, Zeile `\n`, Satz `. `. Ein Stück, das in
   `chunk_size` passt, bleibt ganz.
2. Beim Trennen an Sätzen bleibt der Satzpunkt erhalten.
3. Ist kein Trennzeichen mehr übrig, wird hart nach `chunk_size` Zeichen geschnitten (Strategie 1
   als Notlösung).
4. Jeder Chunk außer dem ersten beginnt mit höchstens `chunk_overlap` Zeichen vom Ende seines
   Vorgängers. Die Überlappung beginnt an einer Wortgrenze, nicht mitten im Wort. Ist der
   Vorgänger höchstens `chunk_overlap` Zeichen lang, wird er ganz vorangestellt.
5. Jeder Chunk erbt die Metadaten (als eigene Kopie) und bekommt die `chunk_id`
   `<source>::<nummer>`, gezählt ab 0.

**Checkpoint 1B:**

```bash
python -m pytest tests/test_chunker.py -q
python -m src.ingest docs --dry-run
```

Erwartet: `13 passed`. Der Probelauf mit `--dry-run` lädt und chunkt nur. Er braucht keinen
Endpunkt und speichert nichts. Die Musterlösung liefert:

```text
8 Dokumente geladen
  drucker.md: 3375 Zeichen, 8 Chunks
  email-und-kalender.md: 3511 Zeichen, 9 Chunks
  hardware-bestellung.md: 3710 Zeichen, 11 Chunks
  it-support-prozesse.md: 4388 Zeichen, 11 Chunks
  netzwerk-und-wlan.md: 3672 Zeichen, 9 Chunks
  passwort-und-konto.md: 4205 Zeichen, 12 Chunks
  software-und-lizenzen.md: 3705 Zeichen, 10 Chunks
  vpn-zugang.md: 3886 Zeichen, 10 Chunks
80 Chunks erzeugt (Probelauf: keine Embeddings, nichts gespeichert)
```

Weicht eure Chunk-Zahl leicht ab, ist das kein Fehler, solange die Tests grün sind. Vergleicht dann
eine Datei mit der Musterlösung (siehe Aufholen).

**Beobachtet:** Wo enden die ersten drei Chunks von `vpn-zugang.md`?

```bash
python -c "from src.loader import load_documents; from src.chunker import chunk_document; doc = [d for d in load_documents('docs') if d['metadata']['source'] == 'vpn-zugang.md'][0]; [print(c['chunk_id'], repr(c['text'][-40:])) for c in chunk_document(doc)[:3]]"
```

Musterlösung:

```text
vpn-zugang.md::0 'Passwort und Konto*).\n## Voraussetzungen'
vpn-zugang.md::1 '\n## VPN einrichten (Schritt für Schritt)'
vpn-zugang.md::2 'ush in der Authenticator-App bestätigen.'
```

Die Überschrift „## Voraussetzungen“ steht am Ende von `::0`, ihre Liste aber in `::1`. Dort taucht
die Überschrift nur dank der Überlappung noch einmal auf. Warum ist das für die Suche ungünstig?
Welche Strategie aus der Vorlesung vermeidet das? Bonus C probiert es aus.

**Diskutiert zu zweit:** Wie ändert sich die Chunk-Zahl mit der Chunk-Größe?

```bash
python -m src.ingest docs --dry-run --chunk-size 100
python -m src.ingest docs --dry-run --chunk-size 2000
```

Kontrollwerte der Musterlösung: 100 Zeichen ergeben 321 Chunks, 500 ergeben 80, 2000 ergeben 19.
Was bedeutet das für eine Frage nach einem einzelnen Fakt, was für eine Frage nach einem ganzen
Ablauf? Beachtet: `chunk_size` zählt hier Zeichen. Die Startwerte aus der Vorlesung sind in Tokens
angegeben. Ein Token ist bei deutschem Text meist kürzer als vier Zeichen. 500 Zeichen sind also
deutlich weniger als 500 Tokens.

**Aufholen Teil 1:**

```bash
git checkout origin/vl04-rag-ingestion-pipeline-solution -- src/loader.py src/chunker.py
```

---

## Teil 2: Embeddings und Vektordatenbank (30 min)

Dokumente → Laden → Chunking → **Embedding → Speichern**

### A: Embedder (8 min)

Füllt `TODO Teil 2A` in `src/embedder.py`. Das Embedding läuft wie der Chat aus VL 3 über litellm
und den Kurs-Endpunkt. Base-URL und Key kommen aus `src/llm.py`. Anforderungen:

1. Provider-Präfix `hosted_vllm/` verwenden. Die WAF vor dem Gateway blockt das OpenAI-SDK.
2. Alle Texte in einem einzigen Aufruf schicken.
3. Die Vektoren nach dem Feld `index` sortieren, damit ihre Reihenfolge zur Eingabe passt.
4. Eine leere Liste ergibt eine leere Liste, ohne Netzaufruf.

**Checkpoint 2A** (offline, dann live):

```bash
python -m pytest tests/test_pipeline_offline.py -q -k teil2a
python -c "import math; from src.embedder import embed_texts; v = embed_texts(['Hallo Welt', 'VPN Verbindung', 'Drucker einrichten']); print(len(v), 'Vektoren,', len(v[0]), 'Dimensionen, Länge', round(math.sqrt(sum(x * x for x in v[0])), 3))"
```

Erwartet: `3 passed, 12 deselected` und `3 Vektoren, 2560 Dimensionen, Länge 1.0`.

**Prüft die Länge kritisch.** In Teil 3 rechnet ihr die Distanz von ChromaDB in eine
Kosinus-Ähnlichkeit um. Die Formel dafür gilt nur für Vektoren der Länge 1. Weicht der Wert deutlich
von 1.0 ab, meldet es im Plenum.

### B: Vektordatenbank (10 min)

Füllt `TODO Teil 2B-1` bis `2B-3` in `src/vectorstore.py`. `get_client` ist fertig. Er legt die
Daten dauerhaft unter `./chroma_db` ab und schaltet die Telemetrie von ChromaDB ab. Anforderungen:

1. `create_collection` nutzt `get_or_create_collection`. Ein zweiter Lauf der Pipeline darf nicht
   scheitern.
2. `ingest` prüft, dass es genauso viele Embeddings wie Chunks gibt, und speichert dann per
   `upsert`: `ids` = `chunk_id`, `documents` = Text, `embeddings`, `metadatas` = Metadaten.
3. `search` ruft `collection.query` auf und liefert Texte, Metadaten und Distanzen.

Warum `upsert` statt `add`? `add` überschreibt keine vorhandene ID. Ein geänderter Text käme so nie
in der Collection an. `upsert` legt neue Einträge an und überschreibt vorhandene. Ein Test in
Checkpoint 2B prüft genau das.

**Checkpoint 2B:**

```bash
python -m pytest tests/test_pipeline_offline.py -q -k teil2b
```

Erwartet: `4 passed, 11 deselected`.

### C: Pipeline (12 min)

Lest `run_pipeline` in `src/ingest.py` einmal von oben nach unten. Es verbindet die Bausteine zu
der Kette aus der Vorlesung. Offen ist nur `TODO Teil 2C` in `chunk_documents`: alle Dokumente
chunken und die Chunks in einer Liste sammeln.

Lest danach `remove_old_chunks`. Erklärt euch gegenseitig in zwei Sätzen, warum die Pipeline vor dem
Speichern die alten Chunks derselben Quellen löscht, obwohl `upsert` doch überschreibt. Und warum
löscht sie erst nach dem Embedding? Die Fragen kommen in der Reflexion wieder. Bonus B misst die
Antwort.

**Checkpoint 2C** (offline, dann live):

```bash
python -m pytest tests/test_pipeline_offline.py -q -k teil2c
python -m src.ingest docs
```

Erwartet: `4 passed, 11 deselected` und

```text
8 Dokumente geladen
80 Chunks erzeugt
80 Embeddings berechnet (2560 Dimensionen)
Collection 'leinetech_kb': 80 Einträge gespeichert
```

Führt `python -m src.ingest docs` ein zweites Mal aus. Die Collection hat danach weiterhin 80
Einträge.

**Aufholen Teil 2:**

```bash
git checkout origin/vl04-rag-ingestion-pipeline-solution -- src/embedder.py src/vectorstore.py src/ingest.py
```

---

## Teil 3: Suche messen statt glauben (20 min)

Frage → Embedding → **Ähnlichkeitssuche → Top-k Chunks**

### A: Semantische Suche (7 min)

Füllt in `src/search.py`:

- `TODO Teil 3A-1` in `embedding_search`: Frage einbetten, ChromaDB abfragen, Treffer als Dicts
  `{"rank", "chunk_id", "source", "score", "text"}` zurückgeben.
- `TODO Teil 3A-2` in `_distance_to_similarity`: ChromaDB liefert die quadrierte euklidische
  Distanz d². Für Vektoren der Länge 1 gilt d² = 2 − 2·cos. Stellt nach cos um.

Die Keyword-Baseline `keyword_search` ist fertig. Lest sie und `_tokenize` kurz: Was zählt der
Score, und was passiert, wenn zwei Chunks gleich viele Wörter mit der Frage teilen?

**Checkpoint 3A:**

```bash
python -m pytest -q
python -m src.search "Wie verbinde ich mich mit dem VPN?" --n 3
python -m src.search "Fehlermeldung 0x80042109" --mode keyword --n 3
```

Erwartet: `33 passed`. Die semantische Suche zeigt drei Treffer mit `chunk_id` und einem Score
zwischen 0 und 1. Die Keyword-Suche liefert in der Musterlösung (Vorschau gekürzt):

```text
Suche (keyword): "Fehlermeldung 0x80042109"
  1. [2] email-und-kalender.md::2 — "teilen. ## Bekannte Fehler beim Senden ### Fehlermeldung 0x80042109 ..."
  2. [1] it-support-prozesse.md::8 — "auf das alte. ## Was gehört in ein gutes Ticket? ..."
```

Im Modus `embedding` ist der Score die Kosinus-Ähnlichkeit mit zwei Nachkommastellen. Im Modus
`keyword` ist er die Anzahl gemeinsamer Wörter.

**Aufholen Teil 3:**

```bash
git checkout origin/vl04-rag-ingestion-pipeline-solution -- src/search.py
```

### B: Messen (10 min)

Die neun Testfragen stehen in `labs/vl04-testfragen.txt`, eine pro Zeile. Frage 8 ist der Text von
Ticket T-1018. Diese Schleife stellt jede Frage beiden Suchverfahren und speichert die Ausgabe:

```bash
while IFS= read -r frage; do
  frage=${frage%$'\r'}                            # Windows-Zeilenende entfernen
  python -m src.search "$frage" --n 3
  python -m src.search "$frage" --n 3 --mode keyword
done < labs/vl04-testfragen.txt | tee messung-500.txt
```

Übertragt das Ergebnis in die Tabelle. Gezählt wird die **Passage**, nicht nur die Datei. Für die
Antwort in VL 5 zählt, ob der Chunk mit der Antwort beim LLM ankommt.

- **Treffer@1:** Der Chunk mit der erwarteten Passage steht auf Rang 1.
- **Treffer@3:** Er steht unter den ersten drei.

Die `chunk_id` in Klammern gilt für die Musterlösung. Mit eigenem Chunker entscheidet der Abschnitt.

| # | Frage | Erwartete Passage | Embedding @1 | Embedding @3 | Keyword @1 | Keyword @3 |
|---|---|---|---|---|---|---|
| 1 | Wie verbinde ich mich mit dem VPN? | `vpn-zugang.md` „VPN einrichten“ (`::2`) | | | | |
| 2 | Mein Passwort ist abgelaufen | `passwort-und-konto.md` „Passwort-Richtlinie“ oder „Passwort-Reset im Self-Service“ (`::1`, `::2`) | | | | |
| 3 | Drucker druckt nicht | `drucker.md` „Häufige Störungen und Lösungen“ (`::3`) | | | | |
| 4 | Welche Laptops kann ich bestellen? | `hardware-bestellung.md` „Standardgeräte“ (`::1`) | | | | |
| 5 | Outlook synchronisiert nicht | `email-und-kalender.md` „Mails bleiben im Postausgang“ (`::3`) | | | | |
| 6 | Ich brauche eine neue Software-Lizenz | `software-und-lizenzen.md` „Kostenpflichtige Lizenz beantragen“ (`::2`) | | | | |
| 7 | Fehlermeldung 0x80042109 | `email-und-kalender.md` „Fehlermeldung 0x80042109“ (`::2`) | | | | |
| 8 | Text von T-1018 | `vpn-zugang.md` „Bekanntes Problem (Mai 2026)“ (`::4`) | | | | |
| 9 | VPN geht nicht | `vpn-zugang.md` „Häufige Fehler und Lösungen“ (`::5`, `::6`) | | | | |
| | **Summe (von 9)** | | | | | |

Frage 5 ist absichtlich unscharf. Die Wissensbasis hat keinen Abschnitt zur Synchronisation. Wie
geht ihr damit um?

<details>
<summary>Zum Abgleich nach eurer Messung: Keyword-Ergebnisse der Musterlösung</summary>

Die Keyword-Suche ist deterministisch. Mit der Musterlösung (500/50) liefert sie:

| # | Keyword Top-3 | @1 | @3 |
|---|---|---|---|
| 1 | `vpn-zugang.md::9` (Score 2), `drucker.md::6`, `email-und-kalender.md::0` (Score 1, Gleichstand) | ✗ | ✗ |
| 2 | `netzwerk-und-wlan.md::1`, `::2`, `::7` (alle Score 1, Gleichstand) | ✗ | ✗ |
| 3 | `drucker.md::2`, `it-support-prozesse.md::2` (beide Score 1, Gleichstand) | ✗ | ✗ |
| 4 | `drucker.md::6`, `email-und-kalender.md::7`, `hardware-bestellung.md::3` (alle Score 1, Gleichstand) | ✗ | ✗ |
| 5 | `email-und-kalender.md::0`, `::2`, `::4` (alle Score 1, Gleichstand) | ✗ | ✗ |
| 6 | `software-und-lizenzen.md::2`, `::4`, `::7` (alle Score 2, Gleichstand) | ✓ | ✓ |
| 7 | `email-und-kalender.md::2`, `it-support-prozesse.md::8` | ✓ | ✓ |
| 8 | `vpn-zugang.md::4` (Score 15), `vpn-zugang.md::3`, `netzwerk-und-wlan.md::6` | ✓ | ✓ |
| 9 | `drucker.md::6`, `email-und-kalender.md::0`, `it-support-prozesse.md::2` (alle Score 1, Gleichstand) | ✗ | ✗ |
| | **Summe** | **3** | **3** |

Der Treffer bei Frage 6 entsteht durch die Reihenfolge bei Gleichstand, nicht durch die Gewichtung.
Bei den Fragen 1, 2 und 9 ist es umgekehrt: Die erwartete Passage hat denselben Score wie der
Treffer auf Rang 3 und landet nur wegen der Reihenfolge dahinter. Bei den Fragen 3, 4 und 5 teilt
sie kein einziges Suchwort mit der Frage.

Auf Dateiebene sähe die Keyword-Suche besser aus: Bei 6 von 9 Fragen stimmt die Datei auf Rang 1.
Die Embedding-Spalten hängen vom Modell ab und stehen deshalb nicht hier.

</details>

### C: Vergleichen (3 min)

- Bei welchen Fragen gewinnt die semantische Suche, bei welchen die Keyword-Suche?
- Tipps: Synonyme („Laptop“ und „Notebook“), exakte Codes („0x80042109“), lange Tickettexte mit
  vielen gemeinsamen Wörtern (T-1018).

---

## Reflexion (10 min)

2 bis 3 Teams zeigen je 2 Minuten lang ihre beste und ihre schlechteste Frage und erklären, warum.
Leitfragen für alle:

1. Wo gewinnt die semantische Suche, wo die Keyword-Suche, und warum?
2. Bei „VPN geht nicht“ und „Mein Passwort ist abgelaufen“ teilen viele Chunks genau ein Wort mit der
   Frage. Wer gewinnt dann, und was fehlt der Keyword-Suche, um seltene Wörter stärker zu gewichten?
3. Wie belastbar ist ein Unterschied von einer Frage, wenn ihr nur neun Fragen habt?
4. Die Datei `vpn-zugang.md` hat zehn Chunks. Warum reicht „richtige Datei“ als Treffer für T-1018
   nicht aus?
5. Ein Artikel wird aktualisiert und dabei kürzer. Was tut `remove_old_chunks`, und was ginge ohne
   schief?
6. Jemand wechselt das Embedding-Modell, ohne neu zu indexieren. Was passiert bei gleicher, was bei
   anderer Dimension?
7. Was fehlt noch, damit aus der Suche eine Antwort wird?

<details>
<summary>Zur Selbstkontrolle: Antwortskizzen</summary>

1. Semantisch gewinnt bei Umschreibungen und Synonymen, weil ähnliche Bedeutung nahe Vektoren
   ergibt. Keyword gewinnt bei exakten Codes und IDs. Ein seltener Code trägt für das Embedding kaum
   Bedeutung, als Wort ist er aber eindeutig.
2. Bei Gleichstand entscheidet die Reihenfolge in der Collection, also das alphabetisch erste
   Dokument. Es fehlt eine Gewichtung seltener Wörter (IDF). Genau das bringt BM25 in VL 5.
3. Eine Frage entspricht 11 Prozentpunkten. Aus einem Unterschied von einer Frage folgt nichts. Für
   belastbare Aussagen braucht ihr mehr Fragen, wie beim Golden Dataset in VL 3.
4. Nur `::4` enthält Version 5.1.3, das Symptom und den Workaround. Das LLM in VL 5 bekommt Chunks,
   nicht Dateien. Die übrigen Chunks derselben Datei helfen bei der Antwort nicht.
5. `upsert` überschreibt nur gleiche IDs. Liefert der Artikel weniger Chunks, blieben die alten
   Chunks mit höheren Nummern liegen. Die Suche fände dann veralteten Text. `remove_old_chunks`
   löscht vor dem Speichern alle Chunks der neu geladenen Quellen.
6. Gleiche Dimension: keine Fehlermeldung, aber die Vektoren liegen in verschiedenen Räumen, und die
   Ergebnisse sind Rauschen. Andere Dimension: ChromaDB meldet einen Dimensionsfehler. In beiden
   Fällen hilft nur neu indexieren.
7. Augment und Generate: Die Top-k Chunks kommen mit der Frage in einen Prompt, und das LLM antwortet
   mit Quellenangabe. Das baut ihr in VL 5.

</details>

---

## Bonus für Schnelle

### A: Chunk-Größe messen statt raten

Indexiert zwei weitere Collections und wiederholt die Messung. Die Standard-Collection bleibt dabei
unberührt.

```bash
python -m src.ingest docs --chunk-size 200 --collection leinetech_kb_200
python -m src.ingest docs --chunk-size 1000 --collection leinetech_kb_1000
while IFS= read -r frage; do
  frage=${frage%$'\r'}                            # Windows-Zeilenende entfernen
  python -m src.search "$frage" --n 3 --collection leinetech_kb_1000
done < labs/vl04-testfragen.txt | tee messung-1000.txt
```

Erwartet: 197 und 41 Einträge. Welche Fragen profitieren von kleinen, welche von großen Chunks?

### B: Veraltete Chunks sichtbar machen

Kommentiert in `run_pipeline` die Zeile `remove_old_chunks(collection, documents)` aus.

```bash
python -m pytest tests/test_pipeline_offline.py -q -k veraltete
python -m src.ingest docs --chunk-size 1000
```

Erwartet: `1 failed, 14 deselected`. Der Live-Lauf meldet `41 Chunks erzeugt`, aber
`Collection 'leinetech_kb': 80 Einträge gespeichert`. 39 Einträge stammen noch aus dem Lauf mit 500
Zeichen. Macht die Änderung danach rückgängig und stellt den Index wieder her:
`python -m src.ingest docs` ergibt wieder 80 Einträge.

### C: Strukturbewusstes Chunking (Strategie 3)

Schreibt in `src/chunker.py` eine Funktion `chunk_by_headings(document, chunk_size=500,
chunk_overlap=50)`:

1. Den Text vor jeder Überschrift trennen: `re.split(r"\n(?=#{1,3} )", text)`.
2. Die erste Zeile jedes Abschnitts als Metadatum `section` speichern.
3. Abschnitte über `chunk_size` mit `chunk_document` weiter zerlegen.
4. Eindeutige `chunk_id`s vergeben, z. B. `vpn-zugang.md::3.1`. Sonst meldet ChromaDB einen
   `DuplicateIDError`.

Tauscht in `chunk_documents` (`src/ingest.py`) die Funktion aus, indexiert mit
`--collection leinetech_kb_struktur` und wiederholt die Messtabelle. Wo landet jetzt die Überschrift
„## Voraussetzungen“?

---

## Troubleshooting

| Problem | Ursache und Lösung |
|---|---|
| `NotImplementedError: TODO Teil …` | Gewollt. Diese Funktion ist die nächste Aufgabe. |
| `28 failed, 5 passed` direkt nach dem Checkout | Gewollt. Die roten Tests sind die Vorgabe für Teil 1 bis 3. |
| `ModuleNotFoundError: No module named 'chromadb'` | venv nicht aktiv oder Abhängigkeiten fehlen: venv aktivieren, `pip install -r requirements.txt`. |
| `ModuleNotFoundError: No module named 'src'` | Befehl nicht im Repo-Root gestartet. Alle Befehle laufen im Ordner `leinetech`. |
| Erste Anfrage hängt minutenlang | Cold Start am Kurs-Endpunkt (200 bis 300 s). Warten, nicht abbrechen. Chat und Embedding wärmen getrennt auf (Schritt 0). |
| `Timeout` bei der ersten Anfrage | Cold Start. `export LLM_TIMEOUT=360` und erneut starten. Der Default von 120 s reicht dafür nicht. |
| 403 oder „nur montags …“ | Außerhalb des Zeitfensters oder `LLM_API_KEY` fehlt. Teil 1 und alle Offline-Tests funktionieren trotzdem. Die Live-Checks und die Messung holt ihr am nächsten Montag nach. |
| `Collection 'leinetech_kb' ist leer` | Zuerst `python -m src.ingest docs`. `chroma_db/` liegt relativ zum aktuellen Ordner. Startet alle Befehle im Repo-Root. |
| Fehler mit „Collection [leinetech_kb] already exists“ | `create_collection` statt `get_or_create_collection` benutzt (Teil 2B). |
| `DuplicateIDError` mit „Expected IDs to be unique“ | Zwei Chunks im selben Lauf haben dieselbe `chunk_id`. Prüft das Schema `<source>::<nummer>` (Teil 1B). |
| „Collection expecting embedding with dimension of 2560, got …“ | Collection und Anfrage stammen aus verschiedenen Modellen (Gleiches-Modell-Regel). Neu indexieren, am einfachsten in eine neue Collection mit `--collection`. |
| Mehr Einträge als Chunks, z. B. 80 nach `--chunk-size 1000` | Veraltete Chunks. `remove_old_chunks` fehlt oder ist auskommentiert (Bonus B). |
| `Failed to send telemetry event …` in der Ausgabe | Eigener ChromaDB-Client ohne `Settings(anonymized_telemetry=False)`. Nutzt `get_client` aus `src/vectorstore.py`. |
| Suchergebnisse passen nicht zum geänderten Code | Nach jeder Änderung an Chunker oder Embedder neu indexieren: `python -m src.ingest docs`. |
| `UnicodeEncodeError: 'charmap'` bei `python -m src.search` | Windows ohne UTF-8-Modus: `export PYTHONUTF8=1` (Schritt 0.3). |
| `sqlite3.OperationalError` beim Start von ChromaDB | Beschädigter oder gesperrter Index. Andere Prozesse beenden. Hilft das nicht, `chroma_db/` löschen und neu indexieren. |

---

## Checkpoints auf einen Blick

| Teil | Befehl | Erwartet |
|---|---|---|
| 0 | `python -m pytest -q --tb=line` | `28 failed, 5 passed`, jede Zeile zeigt auf ein TODO |
| 1A | `python -m pytest tests/test_chunker.py -q -k load` | `4 passed, 9 deselected` |
| 1B | `python -m pytest tests/test_chunker.py -q` | `13 passed` |
| 1B | `python -m src.ingest docs --dry-run` | 8 Dokumente mit 3375 bis 4388 Zeichen, 80 Chunks |
| 2A | `python -m pytest tests/test_pipeline_offline.py -q -k teil2a` | `3 passed, 12 deselected` |
| 2A | Embedding-Test aus Teil 2A | `3 Vektoren, 2560 Dimensionen, Länge 1.0` |
| 2B | `python -m pytest tests/test_pipeline_offline.py -q -k teil2b` | `4 passed, 11 deselected` |
| 2C | `python -m pytest tests/test_pipeline_offline.py -q -k teil2c` | `4 passed, 11 deselected` |
| 2C | `python -m src.ingest docs` | `Collection 'leinetech_kb': 80 Einträge gespeichert` |
| 3A | `python -m pytest -q` | `33 passed` |
| 3A | `python -m src.search "Fehlermeldung 0x80042109" --mode keyword --n 3` | Rang 1: `email-und-kalender.md::2` mit Score 2 |

Je nach Umgebung hängt pytest an die Zeile noch Warnungen an, z. B. `3 warnings`. Das ist kein
Fehler.

## Musterlösung und Weiterarbeit

Die Musterlösung liegt im Branch `vl04-rag-ingestion-pipeline-solution`. Der Start-Branch für VL 5,
`vl05-rag-advanced-start`, baut auf ihr auf. Wer heute nicht fertig wird, verliert also nichts.
Euren Stand der sechs Pipeline-Module vergleicht ihr, ohne ihn zu verlieren:

```bash
git diff origin/vl04-rag-ingestion-pipeline-solution -- src/loader.py src/chunker.py src/embedder.py src/vectorstore.py src/ingest.py src/search.py
```

In VL 5 kommen Augment und Generate dazu: Die Chunks, die ihr heute indexiert habt, gehen mit der
Frage an das LLM. Aus einem Treffer wie `vpn-zugang.md::4` wird so eine Antwort mit Quelle.

**Vorbereitung auf VL 5:** Eigene VL-4-Dateien committen, zum Beispiel auf eurem Branch `lab-vl04`
mit `git add -A && git commit -m "VL 4"`. Das Setup von VL 5 beginnt mit diesem Commit. VL 5
startet auf `vl05-rag-advanced-start`. Der Endpunkt ist wieder nur montags erreichbar.
