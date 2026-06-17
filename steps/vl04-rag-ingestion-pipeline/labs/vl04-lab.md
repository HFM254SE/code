# Lab VL 4 — Ingestion-Pipeline für die LeineTech-Wissensbasis

**Ziel:** Ihr baut die komplette Ingestion-Pipeline für ein RAG-System: Dokumente
laden, chunken, embedden und in einer Vektordatenbank speichern. Am Ende
könnt ihr semantisch über die LeineTech-IT-Dokumentation suchen — die Grundlage
für den RAG-Chatbot in VL 5.

**Dauer:** ~90 Minuten (Teil 1: ~20 min · Teil 2: ~30 min · Teil 3: ~25 min · Abschluss: ~15 min)

---

## Schritt 0 — Setup (5–10 min)

```bash
cd leinetech
git checkout vl03-evaluation        # wir bauen auf dem VL-3-Stand auf
```

1) Virtuelle Umgebung aktivieren und Abhängigkeiten installieren:

```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

2) Environment korrekt einstellen:

Benennt die `.env.example` in `.env` um, öffnet sie, setzt euren API Key ein und speichert die Datei.

3) Prüfen, ob alles läuft (sentence transformer download kann etwas dauern):

```bash
python -c "import chromadb; print('ChromaDB', chromadb.__version__)"
python -c "from sentence_transformers import SentenceTransformer; print('sentence-transformers OK')"
```

> **Hinweis:** Der erste Import von `sentence-transformers` lädt das Modell
> `all-MiniLM-L6-v2` (~80 MB). Je nach WLAN kann das dauern — startet
> den Download frühzeitig.

4) Prüfen, ob die Verbindung zur LMM funktioniert:

```bash
python -c "from src.llm import chat; response = chat("Hey 👋"); print(response)"
```

Die Wissensbasis liegt in `docs/` — 8 Markdown-Dateien mit
IT-Dokumentation (VPN, Drucker, Passwörter, E-Mail, …). Schaut euch 2–3
Dateien kurz an, damit ihr wisst, was drinsteht.

---

## Teil 1 — Dokumente laden und chunken (~20 min)

Die Ingestion-Pipeline beginnt dort, wo die Folien es zeigen:
**Dokumente → Laden & Bereinigen → Chunking**.

### Aufgabe A — Document Loader

Erstellt `src/loader.py` mit einer Funktion:

```python
def load_documents(docs_dir: str) -> list[dict]:
    """
    Lädt alle .md-Dateien aus docs_dir.
    Gibt eine Liste von Dicts zurück:
    [{"text": "...", "metadata": {"source": "vpn-zugang.md", ...}}, ...]
    """
```

**Anforderungen:**

1. Alle `.md`-Dateien im Verzeichnis einlesen.
2. Pro Datei ein Dict mit `text` (gesamter Inhalt) und `metadata` (mindestens
   `source` = Dateiname).
3. Leere Dateien überspringen.

Testet:

```bash
python -c "
from src.loader import load_documents
docs = load_documents('docs')
print(f'{len(docs)} Dokumente geladen')
for d in docs:
    print(f'  {d[\"metadata\"][\"source\"]}: {len(d[\"text\"])} Zeichen')
"
```

Erwartet: **8 Dokumente**, je ca. 1500–3500 Zeichen.

### Aufgabe B — Chunking-Strategie

Erstellt `src/chunker.py` mit einer Funktion:

```python
def chunk_document(document: dict, chunk_size: int = 500, chunk_overlap: int = 50) -> list[dict]:
    """
    Zerlegt ein Dokument in Chunks.
    Jeder Chunk erbt die Metadaten des Quelldokuments und bekommt eine chunk_id.
    """
```

**Implementiert rekursives Chunking** (Strategie 2 aus der Vorlesung):

1. Versucht, an `\n\n` (Absätzen) aufzuteilen.
2. Falls ein Teil immer noch zu groß ist: an `\n` (Zeilen) aufteilen.
3. Letzter Ausweg: an `. ` (Sätzen) aufteilen.
4. Chunks, die kleiner als `chunk_overlap` sind, mit dem nächsten Chunk zusammenführen.
5. Überlappung zwischen aufeinanderfolgenden Chunks einfügen.
6. Jeder Chunk erbt die Metadaten (`source`) und bekommt eine eindeutige `chunk_id`.

Testet:

```bash
python -c "
from src.loader import load_documents
from src.chunker import chunk_document

docs = load_documents('docs')
all_chunks = []
for doc in docs:
    chunks = chunk_document(doc, chunk_size=500, chunk_overlap=50)
    all_chunks.extend(chunks)
    print(f'{doc[\"metadata\"][\"source\"]}: {len(chunks)} Chunks')
print(f'Gesamt: {len(all_chunks)} Chunks')
"
```

**Diskutiert zu zweit:** Warum nehmen wir `chunk_size=500`? Was passiert,
wenn ihr 100 oder 2000 wählt? Probiert es aus und vergleicht die Chunk-Anzahl.

---

## Teil 2 — Embeddings und Vektordatenbank (~30 min)

Jetzt wird aus Text Mathematik: **Chunking → Embedding → Vektor-DB**.

### Aufgabe A — Embeddings erzeugen

Erstellt `src/embedder.py`:

```python
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"

def get_model() -> SentenceTransformer:
    """Lädt das Embedding-Modell (gecacht nach dem ersten Aufruf)."""

def embed_texts(texts: list[str]) -> list[list[float]]:
    """Erzeugt Embeddings für eine Liste von Texten."""
```

Testet und beobachtet:

```bash
python -c "
from src.embedder import embed_texts
vecs = embed_texts(['Hallo Welt', 'VPN Verbindung', 'Drucker einrichten'])
print(f'Anzahl Vektoren: {len(vecs)}')
print(f'Dimensionen: {len(vecs[0])}')
print(f'Erste 5 Werte: {vecs[0][:5]}')
"
```

Erwartet: 3 Vektoren mit je **384 Dimensionen**.

### Aufgabe B — In ChromaDB speichern

Erstellt `src/vectorstore.py`:

```python
import chromadb

def create_collection(name: str = "leinetech_kb") -> chromadb.Collection:
    """Erstellt eine ChromaDB-Collection (persistent im Verzeichnis ./chroma_db)."""

def ingest(collection, chunks: list[dict], embeddings: list[list[float]]):
    """Speichert Chunks mit Embeddings und Metadaten in der Collection."""

def search(collection, query_embedding: list[list[float]], n_results: int = 5) -> dict:
    """Sucht die ähnlichsten Chunks zu einem Query-Embedding."""
```

**Anforderungen:**

1. `chromadb.PersistentClient(path="./chroma_db")` verwenden, damit die Daten
   zwischen Aufrufen erhalten bleiben.
2. `ingest` speichert für jeden Chunk: `ids`, `documents`, `embeddings`, `metadatas`.
3. `search` gibt die Top-k Ergebnisse mit Texten, Metadaten und Distanzen zurück.

### Aufgabe C — Die Pipeline zusammensetzen

Erstellt `src/ingest.py` — das Hauptskript, das alles verbindet:

```python
"""
Ingestion-Pipeline: Dokumente → Chunks → Embeddings → ChromaDB
Aufruf: python -m src.ingest docs
"""
```

Die Pipeline soll:

1. Dokumente aus dem angegebenen Verzeichnis laden.
2. Alle Dokumente chunken.
3. Embeddings für alle Chunks erzeugen.
4. In ChromaDB speichern.
5. Am Ende eine Zusammenfassung ausgeben (Anzahl Dokumente, Chunks, Collection-Größe).

```bash
python -m src.ingest docs
```

Erwartete Ausgabe (ungefähr):

```
8 Dokumente geladen
42 Chunks erzeugt
42 Embeddings berechnet (384 Dimensionen)
Collection 'leinetech_kb': 42 Einträge gespeichert
```

---

## Teil 3 — Semantische Suche testen (~25 min)

### Aufgabe A — Suchskript

Erstellt `src/search.py` — ein kleines CLI zum Abfragen:

```bash
python -m src.search "Wie verbinde ich mich mit dem VPN?"
python -m src.search "Mein Passwort ist abgelaufen"
python -m src.search "Kann ich einen zweiten Monitor bestellen?"
```

Pro Ergebnis anzeigen: **Rang, Quelle, Ähnlichkeitswert, Textvorschau** (erste 200 Zeichen).

Beispiel-Ausgabe:

```
Suche: "Wie verbinde ich mich mit dem VPN?"
  1. [0.82] vpn-zugang.md — "Der Fernzugriff auf das LeineTech-Netz erfolgt ausschließlich über Cisco..."
  2. [0.61] netzwerk-und-wlan.md — "Für Homeoffice und Dienstreisen wird der VPN-Client..."
  3. [0.45] passwort-und-konto.md — "Das zentrale Benutzerkonto wird auch für die VPN..."
```

> **Hinweis:** ChromaDB gibt standardmäßig Distanzen zurück (kleiner = besser).
> Um Ähnlichkeitswerte anzuzeigen, rechnet um: `similarity = 1 - distance`
> (bei L2) oder nutzt `collection.query(..., include=["distances"])`.

### Aufgabe B — Retrieval-Qualität bewerten

Testet diese 6 Fragen und füllt die Tabelle aus:

| #   | Frage                                   | Erwartete Quelle(n)      | Top-1 korrekt? | Top-3 korrekt? |
| --- | --------------------------------------- | ------------------------ | -------------- | -------------- |
| 1   | "Wie verbinde ich mich mit dem VPN?"    | vpn-zugang.md            |                |                |
| 2   | "Mein Passwort ist abgelaufen"          | passwort-und-konto.md    |                |                |
| 3   | "Drucker druckt nicht"                  | drucker.md               |                |                |
| 4   | "Welche Laptops kann ich bestellen?"    | hardware-bestellung.md   |                |                |
| 5   | "Outlook synchronisiert nicht"          | email-und-kalender.md    |                |                |
| 6   | "Ich brauche eine neue Software-Lizenz" | software-und-lizenzen.md |                |                |

**Diskutiert:**

- Bei welchen Fragen funktioniert die semantische Suche gut, bei welchen nicht?
- Was passiert, wenn ihr die Frage umformuliert (z. B. „VPN geht nicht" statt
  „Wie verbinde ich mich mit dem VPN?")?
- Wie beeinflusst die `chunk_size` die Ergebnisse? Probiert 200 vs. 1000.

### Aufgabe C — Keyword- vs. Embedding-Suche vergleichen

Implementiert in `src/search.py` eine einfache Keyword-Suche als Vergleich
(z. B. Wortüberlappung zwischen Frage und Chunk). Testet dieselben 6 Fragen
und vergleicht:

```bash
python -m src.search "Mein Passwort ist abgelaufen" --mode keyword
python -m src.search "Mein Passwort ist abgelaufen" --mode embedding
```

**Wann gewinnt die Keyword-Suche?** Wann die Embedding-Suche? (Tipp: Synonyme,
Umschreibungen, exakte Fachbegriffe.)

---

## Teil 4 — Reflexion (~15 min)

**Pitch je Gruppe (2 min):** Zeigt eure Pipeline, die beste und die
schlechteste Suchanfrage, und erklärt warum.

**Leitfragen:**

- Was war der schwierigste Teil der Pipeline? (Erfahrungsgemäß: Chunking-Grenzen
  und die Frage „wie groß ist groß genug?")
- Was passiert, wenn ein Dokument aktualisiert wird? Wie müsstet ihr die
  Pipeline erweitern, um Updates zu unterstützen? (Stichwort: Chunk-IDs,
  Duplikat-Erkennung, Upsert.)
- Was fehlt noch, damit aus der Suche ein RAG-System wird? (Antwort: der
  Augment + Generate-Schritt aus der Vorlesung — das kommt in VL 5.)
- Erinnert euch an die Gleiches-Modell-Regel: Was passiert, wenn jemand
  das Embedding-Modell wechselt, ohne die Collection neu zu indexieren?

**Vorschau VL 5:** Nächstes Mal baut ihr die Abfrage-Pipeline — die Chunks,
die ihr heute indexiert habt, werden dem LLM als Kontext übergeben.

---

## Troubleshooting

| Problem                                        | Lösung                                                                                                                                    |
| ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError: chromadb`                | `pip install -r requirements.txt`                                                                                                         |
| Modell-Download langsam                        | Vom Nachbarn kopieren: `~/.cache/huggingface/hub/` — oder Hörsaal-Hotspot                                                                 |
| `sqlite3.OperationalError` beim ChromaDB-Start | `chroma_db/`-Verzeichnis löschen und Pipeline neu laufen lassen                                                                           |
| Embedding dauert ewig                          | Nur 8 Dokumente × ~5 Chunks = ~40 Embeddings — sollte in Sekunden fertig sein. Falls nicht: `pip install --upgrade sentence-transformers` |
| Suchergebnisse alle gleich schlecht            | Chunk-Größe zu groß? Prüft mit `chunk_size=300`. Oder: wurde `python -m src.ingest` nach Codeänderungen erneut ausgeführt?                |
| `chromadb.errors.DuplicateIDError`             | Pipeline doppelt gelaufen — Collection löschen: `client.delete_collection("leinetech_kb")`                                                |
| `docs/` nicht gefunden                         | Aus dem Repo-Root starten: `python -m src.ingest docs`                                                                                     |
