# LeineTech Ticket-Triage: `vl01-solution`

**Musterlösung** nach dem Lab in **VL 1 (Software-Assistenten)** und zugleich der
**Startpunkt für VL 3**.

## Was sich gegenüber `vl01-start` geändert hat

- Sprechende Namen, Type Hints und Docstrings. `src/main.py` hat einen `if __name__ == "__main__"`-Guard.
- Keyword-Regeln als **Daten** (`CATEGORY_KEYWORDS`, `PRIORITY_KEYWORDS`) statt fünf kopierter
  Schleifen. Die Prüfreihenfolge bleibt gleich, denn der erste Treffer gewinnt.
- `collections.Counter` statt acht Zählschleifen.
- Kein `global`-Statement mehr. Den Cache übernimmt `functools.lru_cache`. Er ist weiterhin Zustand
  auf Modulebene, hängt aber jetzt am Dateipfad.
- Datei-Handling mit Context Manager und `encoding="utf-8"`.
- Kein nacktes `except:`, kein `== None`, keine veränderbaren Default-Argumente, keine ungenutzten
  Importe und Parameter.
- `requirements.txt` mit aktualisierten Versionen. `trivy fs` findet damit keine CVEs mehr
  (Stand 25.09.2026). Außerdem ist `litellm` für VL 3 schon eingetragen.

## Bewusste Verhaltensänderungen

Report und Tests sind identisch mit `vl01-start`. Das Fehlerverhalten ist absichtlich strenger.
Keiner der 5 Tests bemerkt diese Änderungen. Deshalb stehen sie hier, und deshalb gehören sie in
jede Pull-Request-Beschreibung.

| Stelle | `vl01-start` | `vl01-solution` |
|---|---|---|
| `load_tickets` bei fehlender Datei | liefert still `[]`, der Report zeigt „Anzahl Tickets: 0“, Exit-Code 0 | wirft `FileNotFoundError`, Exit-Code 1 |
| `load_tickets` bei kaputtem JSON | liefert still `[]` | wirft `json.JSONDecodeError` |
| Rückgabetyp von `load_tickets` | Liste | Tupel |
| zweiter Aufruf mit anderem Pfad | liefert die Daten des ersten Aufrufs | liest die neue Datei |
| `get_ticket` | nur Standardpfad | optionaler Parameter `path` |
| ungenutzte Parameter | `load_tickets(filter=…)`, `print_stats(extra=…)` | entfernt |
| `import src.main` | startet sofort den Report | startet nichts, der Report läuft über `python -m src.main` |

## Ausführen und erwartete Ergebnisse

```bash
python3 -m venv .venv                 # bei Python 3.14: python3.13, Windows: py -3.12 -m venv .venv
source .venv/bin/activate             # Windows Git Bash: source .venv/Scripts/activate, PowerShell: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.main                    # derselbe Report wie auf vl01-start
python -m pytest                      # 5 passed
pylint src/                           # 10.00/10, Exit-Code 0
flake8 src/ --max-line-length 120     # keine Ausgabe
trivy fs --skip-dirs .venv .          # 0 Findings (Stand 25.09.2026)
```

Den Unterschied zum Lab-Start zeigt `git diff origin/vl01-start origin/vl01-solution -- src/`.

## Zur Diskussion

`requests`, `PyYAML` und `Jinja2` stehen weiter in `requirements.txt`, obwohl `src/` sie nicht
importiert. Die Musterlösung aktualisiert nur ihre Versionen. Für `vl01-start` allein wäre Entfernen
die bessere Behebung, denn die sicherste Abhängigkeit ist die, die man nicht hat. Ab VL 3 bringt
`litellm` die drei Pakete allerdings indirekt mit. Dann sorgt der Pin dafür, dass die gepatchten
Versionen installiert werden. Das ist Reflexionsfrage 4 im Lab.

> VL 2 hat keinen eigenen Branch. Dort klassifiziert ihr Tickets per Prompt, am Laptop mit dem
> Setup aus VL 1. Das nächste Code-Lab ist VL 3. Es startet auf diesem Branch (oder eurer eigenen
> Lösung) und baut einen LLM-Anschluss über den OpenAI-kompatiblen Kurs-Endpunkt (HomeCloud) ein. Die Anleitung
> liegt schon hier in `labs/vl03-lab.md`. Der fertige Stand des ersten Lab-Teils liegt auf
> `vl03-llm-client`, der des zweiten auf `vl03-evaluation`.
