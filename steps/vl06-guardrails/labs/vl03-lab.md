# Lab VL 3 — Lokales LLM betreiben, anbinden und evaluieren

**Ziel:** Ein LLM vollständig lokal betreiben (Ollama), per OpenAI-kompatibler
API ins LeineTech-Projekt integrieren — und dann **messen**, ob es die
Keyword-Triage aus VL 1 wirklich schlägt.

**Dauer:** ~90 Minuten (Teil 1: ~25 min · Teil 2: ~25 min · Teil 3: ~25 min · Ergebnisse: ~10 min)

---

## Schritt 0 — Setup (5–10 min)

Ollama sollte als Vorbereitung bereits installiert sein (VL 2, Hausaufgabe):

```bash
ollama pull llama3.2        # 3B, ~2 GB — läuft auf jedem Laptop
ollama pull qwen2.5:3b      # zweites Modell für den Vergleich (~1.9 GB)
curl http://localhost:11434/api/tags    # API-Server läuft?
```

Projekt auf den VL-1-Endstand bringen:

```bash
cd leinetech
git checkout vl01-solution      # eure eigene Lösung geht natürlich auch
pip install -r requirements.txt
pip install openai
```

---

## Teil 1 — LLM-Client ins Projekt bauen (~25 min)

**Aufgabe:** Das Triage-Tool bekommt einen LLM-Anschluss. Baut zwei neue Module:

1. **`src/llm.py`** — ein Client über das OpenAI-SDK:
   - `base_url` aus `LLM_BASE_URL` (Default `http://localhost:11434/v1`)
   - `api_key` aus `LLM_API_KEY` (Default `"ollama"` — Platzhalter)
   - `chat(prompt, system=..., model=None, temperature=0.0) -> str`
2. **`src/summarize.py`** — zwei Funktionen auf Basis von `chat()`:
   - `summarize_ticket(ticket)` → 1–2 Sätze Zusammenfassung
   - `classify_ticket_llm(ticket)` → `{"kategorie": ..., "prioritaet": ...}`
     mit einem **Few-Shot-Prompt** (VL 2!) und JSON-Ausgabe.
     Denkt an defensives Parsing — kleine Modelle plappern gern um JSON herum.

Testet zwischendurch:

```bash
python -c "from src.llm import chat; print(chat('Sag nur: OK'))"
python -m src.main classify T-1003      # falls ihr die CLI erweitert habt
```

**Warum temperature=0?** Klassifikation soll reproduzierbar sein — Kreativität
ist hier ein Bug, kein Feature (vgl. Sampling-Folien).

> Nicht fertig geworden? `git checkout vl03-llm-client` ist der Checkpoint
> mit fertigem Client.

---

## Teil 2 — Evaluierung: Regeln vs. LLM (~25 min)

In `eval/golden.jsonl` liegen die **menschlichen Soll-Labels** für alle 30
Tickets — unser Golden Dataset (genau das Konzept aus der Vorlesung, nur klein).

**Aufgabe:** Baut `src/evaluate.py`. Damit die 25 Minuten in die Messlogik
fließen (nicht in CLI/CSV-Klempnerei), liegt ein Gerüst bereit:

```bash
cp labs/templates/evaluate_skeleton.py src/evaluate.py
```

Füllt die TODOs:
1. Pro Ticket klassifizieren: `classify_and_prioritize` (Regeln) und
   `classify_ticket_llm` (LLM), jeweils mit Latenzmessung.
2. `accuracy()` implementieren (Kategorie und Priorität getrennt).
3. Bonus: durchschnittliche Latenz pro System im Report.

```bash
python -m src.evaluate                # nur Regeln: Baseline (10 Tickets)
python -m src.evaluate --llm          # llama3.2 — ~1 Min auf CPU
LLM_MODEL=qwen2.5:3b python -m src.evaluate --llm
```

Der Default ist bewusst `--limit 10` — der **volle 30-Ticket-Lauf
(`--all`) ist Hausaufgabe** (10–15 Min Rechenzeit auf CPU-Laptops).

**Auswertung (notiert die Zahlen!):**

| System | Kategorie-Accuracy | Priorität-Accuracy | Ø Latenz |
|---|---|---|---|
| Keyword-Regeln | | | |
| llama3.2 (3B) | | | |
| qwen2.5:3b | | | |
| Cloud-Modell (optional) | | | |

- Bei welchen Tickets irren die **Regeln**, bei welchen das **LLM**?
  Schaut euch 2–3 Fehlklassifikationen in `eval/results.csv` konkret an.
- Optional mit API-Key: `LLM_BASE_URL=https://api.openai.com/v1 ...` —
  derselbe Code, Frontier-Modell. (Keine echten/sensiblen Daten — die
  LeineTech-Tickets sind fiktiv, genau dafür sind sie da.)

> Checkpoint mit fertiger Evaluierung: `git checkout vl03-evaluation`

---

## Teil 3 — Deployment-Szenario (Gruppenaufgabe, ~25 min)

Zurück zur Management-Perspektive. LeineTech will die LLM-Triage **produktiv**
nehmen — und ihr habt jetzt echte Messwerte aus Teil 2.

Analysiert in 2er-/3er-Gruppen **eines** dieser Szenarien (oder euer eigenes
aus der Praxis):

1. LeineTech-Ticket-Triage produktiv (interne Mitarbeiterdaten in Tickets!)
2. Internes Code-Review-Tool für eine Bank
3. Kunden-Chatbot für eine Arztpraxis
4. QA-Assistent in einer Fertigungshalle ohne Internetzugang

Füllt die Entscheidungsmatrix aus (Bewertung 1–5 **mit Begründung**):
Datensensitivität · Anfragevolumen · Latenz-Anforderung · Budget ·
Team-Expertise · DSGVO-Relevanz.

**Ergebnis:** Empfehlung (Cloud API / On-Prem / Edge) mit 3 Begründungen
und den wichtigsten DSGVO-Maßnahmen. **Pitch: 2–3 min pro Gruppe.**

---

## Troubleshooting

| Problem | Lösung |
|---|---|
| `Connection refused` auf Port 11434 | `ollama serve` starten (oder Ollama-App öffnen) |
| Download zu langsam / Hörsaal-WLAN | Modell vom Nachbarn kopieren: `~/.ollama/models` — oder `llama3.2:1b` (0,8 GB) |
| LLM antwortet kein valides JSON | Defensiv parsen (erstes `{` bis letztes `}`), Few-Shot-Beispiele in den Prompt |
| Alles zu langsam auf altem Laptop | `LLM_MODEL=llama3.2:1b` (Default ist eh nur `--limit 10`) |
| `ModuleNotFoundError: openai` | `pip install openai` |
