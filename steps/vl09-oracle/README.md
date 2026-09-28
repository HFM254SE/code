# LeineTech Ticket-Triage: Checkpoint `vl09-oracle`

Ausgangszustand des **Labs in VL 9** (KI im SDLC und Spec-Driven Development).
Die Leitfrage: Woher weiß ein Prüfer, was richtig ist, wenn KI den Code
schreibt?

- **Teil 1, Orakel:** Ihr messt mit Mutation Testing, wie wenig eine grüne
  Test-Suite prüft, wenn ihre Erwartung aus dem Prüfling stammt. Läuft ohne
  Installation, ohne Server, ohne Key und ohne Netz.
- **Teil 2, Spec-Driven:** Ihr baut mit dem Coding-Agenten opencode ein
  Feature spec-first und prüft es dreifach: statisches Gate, Offline-Tests,
  Contract-Test mit Schemathesis. Braucht das venv mit `requirements.txt`,
  opencode und euren HomeCloud-Key (montags 06:00 bis 23:59). Ohne Agent geht
  Teil 2 auch von Hand.

Die Anleitung ist [`labs/vl09-lab.md`](labs/vl09-lab.md). Anfangen bitte dort.

## Neu gegenüber `vl08-agent`

| Datei | Zweck |
|---|---|
| [`api/openapi.yaml`](api/openapi.yaml) | OpenAPI-3.1-Spec der LeineTech Ticket-API (Tickets auflisten, anlegen, lesen, `triage`, `escalate`). **Single Source of Truth.** |
| [`api/app.py`](api/app.py) | Referenz-Server (FastAPI), spec-konform im Sinne des Gates. Hier landet das Lab-Feature `GET /tickets/stats`. |
| [`api/drifted_server.py`](api/drifted_server.py) | weicht **absichtlich** ab. Der Docstring listet neun Abweichungen. Sechs davon sieht das Gate, sie ergeben 7 Befunde. |
| [`tools/specyaml.py`](tools/specyaml.py) | YAML-Leser aus der Standardbibliothek (kein PyYAML). Löst bewusst **kein `$ref`** auf und bricht bei Flow-Maps mit Zeilennummer ab. |
| [`tools/spec_gate.py`](tools/spec_gate.py) | **fertiges** statisches Konformitäts-Gate: liest die Spec und den Server per `ast`, ohne ihn zu starten. `--check` prüft beide Seiten. |
| [`tools/mutation_dojo.py`](tools/mutation_dojo.py) | Mutation Testing für [`src/triage.py`](src/triage.py). Misst die Suiten aus `tests/` und bringt selbst keine Erwartung mit. |
| [`tests/test_triage_oracle.py`](tests/test_triage_oracle.py) | Gerüst für Teil 1 mit drei TODOs. Die leeren Tests laufen unter pytest grün, der Dojo meldet sie als „leer“. |
| [`tests/test_openapi_spec.py`](tests/test_openapi_spec.py) | offline: Spec in sich stimmig, Kategorie-Enum passt zu den Triage-Regeln. |
| [`tests/test_vl09_werkzeuge.py`](tests/test_vl09_werkzeuge.py) | Tests für Dojo, Gate und YAML-Leser. Halten die Zahlen fest, auf die sich Lab und Folien stützen. |
| [`labs/AGENTS.beispiel.md`](labs/AGENTS.beispiel.md) | Beispiel-Kontextdatei zu Aufgabe D0. Erst selbst schreiben, dann vergleichen. |
| [`.ignore`](.ignore) | blendet `labs/` für Such-Werkzeuge auf ripgrep-Basis aus (opencode, `rg`, auch die Suche in VS Code). Der Agent soll die Lab-Anleitung nicht mitlesen. |

Alles andere ist unverändert der Stand von `vl08-agent`, einschließlich der
Musterlösung `src/agent.py` und aller Tests aus VL 1 bis VL 8. Eine eigene
Variante hat nur `requirements.txt` (plus fastapi, uvicorn, schemathesis,
email-validator, pytest-cov).

## Ausführen

Immer `python3`, immer aus dem Repo-Wurzelverzeichnis.

**Teil 1, ohne Installation:**

```bash
python3 tools/mutation_dojo.py --suite shipped        # 4 von 34 eliminiert
python3 tools/mutation_dojo.py --equivalence alle     # 8 Äquivalenz-Kandidaten
python3 tools/mutation_dojo.py --bruecke              # Unit-Test 5/5 grün, Spec-Test 3/4 rot
python3 tools/spec_gate.py --check                    # 0 Befunde auf app.py, 7 auf dem Drift-Server
```

**Teil 2, im venv:**

```bash
source .venv/bin/activate
pip install -r requirements.txt
python3 -m pytest -q                                   # alle Tests, offline
python3 -m uvicorn api.app:app --reload                # Referenz auf :8000, Doku unter /docs
python3 -m uvicorn api.drifted_server:app --port 8001  # driftet absichtlich
schemathesis run api/openapi.yaml --url http://localhost:8000 --checks all --mode all
```

Alles Weitere, inklusive Reihenfolge, Zeitplan und erwarteter Ausgaben, steht in
[`labs/vl09-lab.md`](labs/vl09-lab.md).

## Musterlösung

Einen Lösungs-Checkpoint gibt es für VL 9 nicht. Die Aufholpunkte für Teil 1
(TODO 1 und 2) stehen aufklappbar in der Anleitung. Aufholpunkte und Lösungen
für Teil 2 (Spec-Erweiterung, Handler, Beobachtungen aus F.4, Prüfer-Matrix,
Antworthinweise) stehen bewusst **nicht** im Repo. In Teil 2 durchsucht der
Agent das Repo und fände dort die Regel, die ihr ihm im Review beibringen
sollt. Sie stehen in `vl09-loesungen.md`. Die Datei ist Dozenten-Material im
privaten Folien-Repo (`course/lectures/09_ai_sdlc_spec_driven/dozent/vl09-loesungen.md`)
und wird an den Zeitchecks per Beamer gezeigt.

**Diskussionsstoff:** Wann ist DRY beim Testen falsch? Warum ist ein Mutation
Score ohne Angabe der Mutantenklasse bedeutungslos? Was findet ein statisches
Gate, was ein Contract-Test nicht findet, und umgekehrt?

> Damit ist der Code-Bogen des Kurses komplett: unordentliches Tool (VL 1) →
> LLM (VL 3) → RAG-Korpus (VL 4/5) → gehärtet (VL 6) → Agent (VL 8) →
> spezifiziert und geprüft (VL 9). VL 10 ordnet das Ganze in EU AI Act und
> Ethik ein.

## Hinweise für die nächste Durchführung

- **Vor nächster Durchführung prüfen:** Schemathesis einmal gegen die Referenz
  mit Feature (Port 8000) und gegen den Drift-Server (Port 8001) laufen lassen,
  Befehle wie im Lab. Danach die Schemathesis-Zellen der Prüfer-Matrix in
  `vl09-loesungen.md` bestätigen oder korrigieren. Bisher sind sie nur aus der
  Theorie abgeleitet. Möglicher Befund auf `POST /tickets`: `EmailStr` lehnt
  Adressen ab, die das Pattern der Spec erfüllen (Troubleshooting im Lab).
- `vl09-loesungen.md` aus dem privaten Folien-Repo
  (`course/lectures/09_ai_sdlc_spec_driven/dozent/vl09-loesungen.md`) vor dem Lab
  für den Beamer öffnen. Die Datei gehört nicht in diesen Checkpoint.
- Den ersten Aufruf gegen HomeCloud zu Lab-Beginn selbst abschicken, damit der
  Kaltstart nicht in Aufgabe D fällt.
