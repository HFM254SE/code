# LeineTech-Ticketdatensatz

Gemeinsamer Datensatz für alle Labs des Kurses **„Automatisierung im Software Engineering“**.
Szenario: der interne IT-Support der fiktiven **LeineTech GmbH** (Software- und IT-Dienstleister,
Hannover, ca. 200 Mitarbeitende). Alle Personen, Systeme und Kontaktdaten sind erfunden.

## Dateien

### `tickets.json`

30 Support-Tickets (`T-1001` bis `T-1030`) aus dem Mai 2026. Schema pro Ticket:

```json
{
  "id": "T-1001",
  "von": "vorname.nachname@leinetech.de",
  "betreff": "...",
  "text": "... (2 bis 6 Sätze)",
  "erstellt": "2026-05-04"
}
```

**Bewusst ohne** `kategorie` und `prioritaet`: Die Einordnung ist die Übungsaufgabe.
Tippfehler und Umgangssprache in den Tickets sind Absicht, so sehen echte Tickets aus.

### `../eval/golden.jsonl`

Soll-Labels (Golden Dataset) für alle 30 Tickets: das, was eine erfahrene
Support-Mitarbeiterin vergeben würde. Eine JSON-Zeile pro Ticket:

```json
{"id": "T-1001", "kategorie": "Hardware", "prioritaet": "hoch"}
```

- **Kategorien:** `Hardware` | `Software` | `Netzwerk` | `Zugang` | `Abrechnung` (Definitionen in `../docs/it-support-prozesse.md`)
- **Prioritäten:** `hoch` | `mittel` | `niedrig` (Kriterien und SLAs ebenfalls in `it-support-prozesse.md`)

Die Labels liegen in jedem Checkpoint. Ordnet Tickets deshalb **erst selbst ein und schlagt
dann nach**. Ab VL 3 vergleicht `python -m src.evaluate` automatisch. Wie gut ein Verfahren
trifft, messt ihr dort selbst.

### `../docs/`

Acht Knowledge-Base-Artikel des LeineTech-IT-Supports (Markdown, Stand Mai 2026). Sie passen
inhaltlich zu den Tickets (dieselben Systeme: FinanzPro, Cisco AnyConnect, Outlook, ThinkPads,
Follow-Me-Printing, LT-Corp und LT-Guest usw.) und beantworten die meisten Ticket-Fragen.

## Verwendung in den Vorlesungen

| Vorlesung | Verwendung |
|---|---|
| **VL 1** | regelbasierte Triage über `tickets.json`, die das Lab mit Linter, KI-Assistent und Trivy verbessert |
| **VL 2** | Tickets per Prompt im Browser einordnen, Selbstkontrolle mit `golden.jsonl` |
| **VL 3** | LLM-Klassifikation derselben Tickets, Evaluation von Regeln und LLM gegen `golden.jsonl` |
| **VL 4 und VL 5** | `docs/` als RAG-Korpus (ChromaDB, Embeddings über den Kurs-Endpunkt), Tickets als realistische Anfragen |
| **VL 6** | Angriffe auf die eigene LLM-Pipeline und Guardrails |
| **VL 8** | Ticket-Agent (LangGraph) mit `docs/` als Wissensbasis |
| **VL 9** | `golden.jsonl` als Orakel außerhalb des Prüflings (Mutation Testing, Spec-Driven Development) |
| **VL 10** | Fallstudie zum EU AI Act am eigenen System |
