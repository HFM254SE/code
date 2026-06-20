# Lab VL 3 — LLM anbinden und evaluieren

**Ziel:** Ein LLM über den Kurs-Endpunkt (HomeCloud) per OpenAI-kompatibler
API ins LeineTech-Projekt integrieren — und dann **messen**, ob es die
Keyword-Triage aus VL 1 wirklich schlägt.

**Dauer:** ~90 Minuten (Teil 1: ~25 min · Teil 2: ~25 min · Teil 3: ~25 min · Ergebnisse: ~10 min)

---

## Schritt 0 — Setup (5–10 min)

Wir nutzen den **Kurs-Endpunkt** (Nortal HomeCloud) — einen OpenAI-kompatiblen
LiteLLM-Gateway. Kein lokales Modell nötig (Details + Key in `SETUP.md`).

```bash
cd leinetech
git checkout vl01-solution      # eure eigene Lösung geht natürlich auch
pip install -r requirements.txt # zieht u. a. litellm

export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"   # Key auf Anfrage, siehe SETUP.md
```

Schnelltest, dass der Endpunkt antwortet (Default-Modell `qwen3.6-35B-A3B-FP8`):

```bash
curl -s "$LLM_BASE_URL/models" -H "Authorization: Bearer $LLM_API_KEY" | head -c 200
```

> Geht der Endpunkt nicht (kein SLA!), schaltet ihr mit zwei Variablen auf
> Plan B (Groq) — siehe `SETUP.md`.

---

## Teil 1 — LLM-Client ins Projekt bauen (~25 min)

**Aufgabe:** Das Triage-Tool bekommt einen LLM-Anschluss. Baut zwei neue Module:

1. **`src/llm.py`** — ein dünner Wrapper um **litellm** (nicht das OpenAI-SDK,
   dessen User-Agent der Gateway-WAF blockt):
   - `litellm.completion(model="hosted_vllm/<modell>", api_base=…, api_key=…)`
   - Konfiguration aus `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL`
     (Default-Modell `qwen3.6-35B-A3B-FP8`)
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
python -m src.evaluate --llm          # qwen3.6 über HomeCloud (10 Tickets)
python -m src.evaluate --llm --all    # alle 30 Tickets
```

Der Default ist bewusst `--limit 10` (eine LLM-Runde dauert nur ein paar
Sekunden pro Ticket); mit `--all` laufen alle 30.

**Auswertung (notiert die Zahlen!):**

| System | Kategorie-Accuracy | Priorität-Accuracy | Ø Latenz |
|---|---|---|---|
| Keyword-Regeln | | | |
| qwen3.6-35B (HomeCloud) | | | |
| anderes Modell (optional) | | | |

- Bei welchen Tickets irren die **Regeln**, bei welchen das **LLM**?
  Schaut euch 2–3 Fehlklassifikationen in `eval/results.csv` konkret an.
- Optional: ein zweites Backend vergleichen — z. B. Groq als Plan B
  (`LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` umsetzen, siehe `SETUP.md`).
  Derselbe Code, anderes Modell. (Keine echten/sensiblen Daten — die
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
| `PermissionDeniedError` / „Your request was blocked" | OpenAI-SDK statt litellm, falsches Modell, oder `LLM_API_KEY` fehlt |
| Endpunkt antwortet nicht / Timeout | Kein SLA — Zeitfenster (Mo) prüfen, sonst Plan B (Groq), siehe `SETUP.md` |
| Erste Anfrage hängt minutenlang | Cold Start (Modell lädt in die GPUs) — einmal warten, danach „hot" |
| LLM antwortet kein valides JSON | Defensiv parsen (erstes `{` bis letztes `}`), Few-Shot-Beispiele in den Prompt |
| `ModuleNotFoundError: litellm` | `pip install -r requirements.txt` |
