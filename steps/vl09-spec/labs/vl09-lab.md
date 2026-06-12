# Lab VL 9 — Spec-First am LeineTech-Projekt

**Ziel:** Den Spec-First-Workflow praktisch erleben: von der OpenAPI-Spec zu
Code (mit eurem KI-Assistenten), eine `CLAUDE.md` schreiben und ihren Effekt
messen, und Spec Drift sichtbar machen.

**Dauer:** ~90 Minuten (Teil 1: ~30 min · Teil 2: ~25 min · Teil 3: ~20 min · Abschluss: ~15 min)

---

## Schritt 0 — Setup (5 min)

```bash
cd leinetech
git checkout vl08-agent          # wir bauen auf dem Agenten-Stand auf
pip install -r requirements.txt  # zieht jetzt fastapi, uvicorn, schemathesis
cat api/openapi.yaml             # die Spec lesen — das ist heute die Hauptrolle
```

Ihr braucht euren KI-Assistenten (Cursor **oder** Copilot) aus VL 1.

---

## Teil 1 — OpenAPI → Code (~30 min)

In `api/openapi.yaml` liegt die vollständige Spezifikation der LeineTech
Ticket-API (auflisten, anlegen, lesen, `triage`, `escalate`).

**Aufgabe A — Code generieren:** Öffnet `api/openapi.yaml` in Cursor/Copilot.
Prompt:
```
Generiere einen FastAPI-Server aus dieser OpenAPI-Spec. Pydantic-Models für
alle Schemas, ein Router pro Tag, korrekte Status-Codes. Lade die Tickets aus
data/tickets.json über src.ticket_loader.
```

**Aufgabe B — Gegen die Referenz prüfen:** Vergleicht das Ergebnis mit
`api/app.py` (der spec-konformen Referenz). Wo weicht euer generierter Code ab?
- Fehlen Endpunkte oder Status-Codes (201? 202? 404?)?
- Stimmen die Feldnamen (`prioritaet`, nicht `prio`)?
- Wird der `kategorie`-Query-Parameter umgesetzt?

**Lerneffekt:** Selbst *mit* vollständiger Spec als Kontext erfindet/vergisst
ein LLM Details — Spec-Konformität muss **geprüft**, nicht angenommen werden
(vgl. Determinismus-Folien).

---

## Teil 2 — CLAUDE.md schreiben und messen (~25 min)

**Aufgabe:** Schreibt eine `CLAUDE.md` im Projektwurzelverzeichnis. Pflichtteile:

```markdown
## Stack          → Sprachen, Frameworks, Versionen
## Architektur    → welche Datei/welches Verzeichnis wofür
## Coding-Regeln  → Type Hints, Naming, Error-Handling
## Test-Strategie → pytest, was wird getestet
## Verboten       → was der Agent NIE tun soll
```

**Vergleichstest — derselbe Auftrag mit und ohne CLAUDE.md:**
```
"Füge einen Endpoint POST /tickets/{id}/summary hinzu, der eine
LLM-Zusammenfassung des Tickets zurückgibt. Halte dich an unsere Konventionen."
```
Lasst euren Assistenten das einmal **ohne** und einmal **mit** `CLAUDE.md` im
Projekt tun. Vergleicht: Nutzt er `src/summarize.py`? Type Hints? Den richtigen
Doku-/Teststil? Aktualisiert er die `openapi.yaml`?

**Vergleichen** mit `api/CLAUDE.beispiel.md` — welche eurer Regeln hatte den
größten Effekt? Was fehlte?

---

## Teil 3 — Spec Drift finden (~20 min)

`api/drifted_server.py` weicht **absichtlich** an fünf Stellen von der Spec ab.

**Toolgestützt:**
```bash
uvicorn api.drifted_server:app --port 8001 &
schemathesis run api/openapi.yaml --base-url http://localhost:8001 --checks all
```

**Manuelle Checkliste:**
- [ ] Alle Endpunkte aus der Spec vorhanden?
- [ ] Pflichtfelder in Request-Bodies (`von`!)?
- [ ] Response-Feldnamen korrekt (`prioritaet` vs. `prio`)?
- [ ] Status-Codes wie spezifiziert (404 vs. 400)?
- [ ] Query-Parameter (`kategorie`) vorhanden?

Findet ihr alle fünf? (Auflösung steht am Ende von `drifted_server.py` — erst
selbst suchen.) **Bonus:** Schreibt einen GitHub-Actions-Workflow, der
schemathesis bei jedem PR ausführt und bei Drift den Build rot macht.

---

## Teil 4 — Reflexion (~15 min)

**Pitch je Gruppe (2 min):** Was hat die `CLAUDE.md` konkret verändert? Welcher
Drift war am schwersten zu finden — und welcher in Produktion am gefährlichsten?

**Leitfragen:**
- Wann lohnt Spec-First, wann ist es Overhead? (Stichwort: API mit mehreren
  Konsumenten vs. Wegwerf-Skript.)
- Was findet ein Tool wie schemathesis automatisch, was braucht ein Mensch?
- `CLAUDE.md`, Cursor Rules, `llms.txt` — wofür ist welches Format gedacht?

---

## Troubleshooting

| Problem | Lösung |
|---|---|
| `ModuleNotFoundError: fastapi` | `pip install -r requirements.txt` |
| `uvicorn: command not found` | `python -m uvicorn api.app:app --reload` |
| schemathesis findet nichts | läuft der **drifted** Server auf Port 8001? Base-URL prüfen |
| Generierter Code importiert nichts aus `src/` | im Prompt explizit auf `src.ticket_loader` / `src.triage` verweisen — oder `CLAUDE.md` nutzen (Teil 2!) |
