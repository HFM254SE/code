# Lab VL 9 — Orakel & Spec-Driven: woher weiß ein Prüfer, was richtig ist?

**Ziel:** Ihr messt an eurem eigenen Triage-Modul, dass eine grüne Test-Suite
fast nichts prüft, und findet heraus warum: die Erwartung kommt aus dem
Prüflings-Code selbst. Dann dreht ihr den Spieß um — Spec-Driven mit
**opencode** (gegen das HomeCloud-Qwen): der Agent entwirft **Spec und Plan**,
ihr seid das Review-Gate an jedem Übergang, der Agent implementiert — und
die Konformität beweist ihr **maschinell, dreifach**: statisches Gate,
Offline-Tests, Contract-Test.

**Dauer:** ~85 Minuten in 90 (Setup: ~10 · Teil 1: ~30 · Teil 2: ~45 ·
Abschluss: ~5). Alles, was hier gegenüber der Vorlesung gekürzt ist, steht
unter **Für zu Hause**.

---

## Schritt 0 — Setup (~10 min)

```bash
cd leinetech
git checkout vl09-oracle
python3 --version                 # 3.11+
pip install -r requirements.txt   # fastapi, uvicorn, schemathesis (für Teil 2)
```

> Teil 1 läuft komplett ohne Installation (reine Standardbibliothek, kein
> Netz). Teil 2 braucht das venv aus den früheren Vorlesungen plus opencode
> und euren HomeCloud-Key.

**opencode einrichten** (Details und Troubleshooting: [`SETUP.md`](../SETUP.md)):

```jsonc
// ~/.config/opencode/opencode.json
{
  "model": "homecloud/qwen3.6-35B-A3B-FP8",
  "provider": {
    "homecloud": {
      "npm": "@ai-sdk/openai-compatible",
      "options": { "baseURL": "https://llm.homecloud.ee/v1", "apiKey": "<euer-key>" },
      "models": { "qwen3.6-35B-A3B-FP8": { "limit": { "context": 131072 } } }
    }
  }
}
```

> ⚠️ **Der Key funktioniert nur montags 06:00–23:59** (Europe/Berlin) — für
> den Lab-Slot okay; wer zu Hause nacharbeitet, wählt einen Montag. Und:
> Prompts werden **geloggt** — keine Secrets, keine echten Personendaten.

**Zwei Smoke-Tests** — beide müssen so aussehen:

```bash
python3 tools/mutation_dojo.py --suite shipped     # muss "eliminiert 4" melden
python3 -m pytest tests/test_openapi_spec.py -q    # muss "4 passed" melden
```

---

## Teil 1 — Das Orakel (~30 min)

[`src/triage.py`](../src/triage.py) ordnet Tickets per Keyword-Listen ein. 61 Zeilen, keine
Verzweigungen über die Keywords: das ganze Verhalten steckt in zwei dicts.
[`tests/test_triage.py`](../tests/test_triage.py) hat 5 Tests, alle grün.

### Aufgabe A — Schätzen, dann messen (~10 min)

[`src/triage.py`](../src/triage.py) enthält **34 Kategorie-Keywords**. Mutantenklasse heute:
*ein Keyword aus einer Liste löschen*.

```bash
python3 tools/mutation_dojo.py --list        # die 34, ohne Beschreibung
```

**Schreibt eure Schätzung in den Chat, BEVOR ihr weitermacht:** Wie viele der
34 Mutanten eliminiert die ausgelieferte Suite?

```bash
python3 tools/mutation_dojo.py --suite shipped
```

**Erwartete Ausgabe:** `Mutanten 34 · eliminiert 4 · Mutation Score (roh) 4/34 = 0.118`,
eliminiert werden `laptop`, `drucker`, `vpn`, `zugriff`.

**Überlegt kurz:** Was haben genau diese vier gemeinsam? (Antwort: sie sind
die einzigen Keywords, die für eine Assertion **allein entscheidend** sind.
Wörtlich in den Testtexten stehen acht — aber `rechnung` und `kosten` teilen
sich dasselbe Ticket und decken sich gegenseitig: löscht man eins, matcht das
andere weiter. Und `wlan`/`lan` stehen in einem Ticket, dessen Assertion
`Zugang` schon `zugriff` entscheidet (first match wins). Die Keyword-Listen
sind *Daten*, keine Verzweigungen — Coverage sieht sie beim Import als
abgedeckt und kann ein geprüftes Keyword nicht von einem ungeprüften
unterscheiden.)

> In der Vorlesung lief dieselbe Messung mit `--scope all`: 45 Mutanten,
> anderer Nenner, anderer Score — Score ohne Mutantenklasse ist bedeutungslos.
> Die Äquivalenz-Analyse (8 der Mutanten kann *niemand* eliminieren) habt ihr
> dort gesehen; die Kommandos zum Nachrechnen stehen unter **Für zu Hause**.

### Aufgabe B — Die naheliegende Refaktorierung (~10 min)

Öffnet [`tests/test_triage_oracle.py`](../tests/test_triage_oracle.py). **TODO 1** dort ist der Test, den man in
jedem Review vorschlagen würde: keine Magic Strings, eine Schleife über
`CATEGORY_KEYWORDS`.

Schreibt ihn. Dann:

```bash
python3 tools/mutation_dojo.py --suite oracle
```

> `--suite oracle` führt **eure** Funktion aus — der Dojo hat keine eigene
> Kopie davon. Solange TODO 1 leer ist, misst er nichts: ein Score auf einem
> leeren Test wäre die nächste Orakel-Falle.

**Notiert die Zahl, bevor ihr weiterlest.** Sie überrascht: 34 geprüfte
Keywords statt 5 handgeschriebener Fälle — und der Score geht **runter**,
nicht rauf.

**Warum:** Der Test importiert seine Erwartung aus dem Modul, das er prüft.
Löscht der Mutant ein Keyword, verschwindet der zugehörige Testfall
*mitsamt der Erwartung*. Es bleibt nichts, was fehlschlagen könnte. Das ist
die Orakel-Falle aus der Vorlesung — mit einem Orakel, das sich **mitbewegt**.

Vergleicht mit dem ACH-Filter aus der Theorie: ein Test taugt nur, wenn er
auf dem Mutanten FEHLSCHLÄGT **und** auf dem Original BESTEHT. Diese Suite
erfüllt genau die Hälfte davon.

### Aufgabe C — Eine Zeile Unterschied (~10 min)

**TODO 2** in derselben Datei: derselbe Test, aber die Erwartung steht als
eingefrorene Kopie **in der Testdatei**.

```bash
python3 tools/mutation_dojo.py --suite frozen
```

**Erwartete Ausgabe:** `eliminiert 26 · Mutation Score (roh) 26/34 = 0.765`.

Ja, das dupliziert Daten. **Notiert im Code-Kommentar, warum das hier richtig
ist** — DRY gilt für Produktionscode, nicht für Orakel.

Schreibt `FROZEN` als ausgeschriebenes Literal, nicht als Ableitung aus
`CATEGORY_KEYWORDS`. Eine Ableitung wäre dasselbe mitwandernde Orakel wie in
TODO 1, nur besser getarnt.

### Die Brücke zu Teil 2 (2 min, ein Kommando)

Löscht nicht ein Keyword, sondern den **Schlüssel** `"Software"`:

```bash
python3 tools/mutation_dojo.py --bruecke
```

[`tests/test_triage.py`](../tests/test_triage.py) bleibt **grün (5/5)** — `DEFAULT_CATEGORY` fängt alles
auf, der Rückgabewert ändert sich nie. [`tests/test_openapi_spec.py`](../tests/test_openapi_spec.py) wird
**rot (3/4)**: er vergleicht das `Kategorie`-Enum der Spec gegen
`CATEGORY_KEYWORDS`. Der Unterschied zwischen den beiden Dateien ist nicht
Sorgfalt, sondern **wo ihre Erwartung liegt**.

> **Die maschinenlesbare Spec ist das einzige Orakel in diesem Repo, das
> außerhalb des Codes liegt, den es beurteilt.** Genau dieses Orakel arbeitet
> jetzt für euch.

---

## Teil 2 — Spec-Driven Feature mit opencode (~45 min)

Der Ablauf ist der Vier-Schritt aus der Vorlesung, auf Lab-Größe gefaltet:

> **Specify** (Aufgabe D: der Agent entwirft die Spec, ihr reviewt) →
> **Plan** (Aufgabe E: der Agent plant, ihr reviewt) → **Implement**
> (Aufgabe E: der Agent setzt den freigegebenen Plan um) → und statt eines
> vierten Agent-Schritts beweist Aufgabe F die Konformität **maschinell**.
> `Tasks` entfällt ehrlich: ein Endpunkt ist genau ein Task. An jedem
> Übergang steht ihr — **der Agent bekommt nie den Gesamtauftrag.**

Die Rollen in diesem Teil:

- [`api/openapi.yaml`](../api/openapi.yaml) — **Single Source of Truth.** Hier beginnt das Feature.
- [`api/app.py`](../api/app.py) — Referenz-Server, exakt spec-konform. Hier landet der Code.
- [`api/drifted_server.py`](../api/drifted_server.py) — weicht absichtlich an 6 Stellen ab (7 Befunde).
- [`tools/spec_gate.py`](../tools/spec_gate.py) — **fertiges** statisches Konformitäts-Gate: liest die
  Spec mit [`tools/specyaml.py`](../tools/specyaml.py) und die Implementierung per `ast` — kein
  Server, kein Import des Prüflings. Ein kaputter Server kann das Gate nicht
  beeinflussen.

> **Lest den Docstring von `gate()`, bevor ihr es benutzt** (~2 min). Zwei
> Design-Entscheidungen darin braucht ihr gleich: (1) das Gate verfolgt
> Hilfsfunktions-Aufrufe, weil [`app.py`](../api/app.py) den 404 in `_require()` erhebt, nicht
> im Handler; (2) `FRAMEWORK_CODES = {400, 422}` sind ausgenommen, weil
> FastAPI sie selbst erzeugt — sie zu fordern würde den *korrekten* Server
> anschwärzen. Ein Gate ist nie neutral: jemand hat entschieden, was es sieht.

Das Abnahme-Kriterium des Gates ist **zweiseitig** — merkt euch die Zahlen:

```bash
python3 tools/spec_gate.py --check
# grün auf api/app.py             : 0 Befund(e)  OK
# rot   auf api/drifted_server.py : 7 Befund(e)  OK
# BESTANDEN
```

Ein Gate, das immer rot ist, ist von einem funktionierenden nicht zu
unterscheiden. Ein Gate, das immer grün ist, auch nicht.

### Aufgabe D — Specify: der Agent entwirft, ihr entscheidet (~15 min)

**Das Feature kommt als Auftrag, nicht als YAML.** Startet opencode im
Repo-Root Directory (`opencode`) und wechselt mit **Tab** in den
**Plan-Modus** — dort liest und antwortet der Agent, editiert aber keine
Dateien. Dann:

```text
Wir erweitern die LeineTech Ticket-API spec-first. Feature-Wunsch:
"Als Teamlead möchte ich auf einen Blick sehen, wie viele Tickets in
jeder Kategorie und jeder Priorität liegen, um Engpässe zu erkennen."

Entwirf NUR die Änderung an api/openapi.yaml — noch keinen Code:
ein neuer GET-Endpunkt /tickets/stats. Übernimm Stil und Konventionen
der bestehenden Spec (operationId, tags, $ref auf ein Schema namens
StatistikReport unter components). Zeige das YAML als Entwurf und
begründe jede Entscheidung in einem Satz. Ändere noch keine Datei.
```

**Jetzt seid ihr das Review-Gate** — der Übergang Specify → Plan ist in der
Vorlesung ein menschlicher Prüfpunkt, hier auch. Checkliste gegen den Entwurf:

- [ ] `operationId` vorhanden? ([`tests/test_openapi_spec.py`](../tests/test_openapi_spec.py) erzwingt sie)
- [ ] `$ref` auf ein Schema `StatistikReport` unter `components` — kein
  Inline-Gewusel?
- [ ] **Blockstil wie der Rest der Datei?** Flow-Maps (`{ type: integer }`)
  versteht [`specyaml.py`](../tools/specyaml.py) nicht — Gate und Offline-Tests lesen die Spec
  damit falsch.
- [ ] Nichts erfunden? Keine Query-Parameter, keine Extra-Endpunkte, kein
  404 (der Endpunkt hat keinen Pfad-Parameter).
- [ ] **Die Regel, die der Agent nicht erraten kann:** Auch eine Kategorie
  mit **0 Tickets** muss als Schlüssel in der Antwort stehen — sonst kann
  kein Dashboard sie anzeigen. Die Form: `StatistikReport` hat **genau drei
  Top-Level-Felder** — `gesamt` (integer), `kategorien` (object),
  `prioritaeten` (object). Kodiert wird die Regel über `required` in den
  beiden Unterobjekten: **alle fünf** Kategorie-Namen in `kategorien` und
  **alle drei** Prioritäts-Namen in `prioritaeten`, jeweils als Pflichtfeld
  (integer, `minimum: 0`). **Diese Geschäftsregel stand nicht im
  Feature-Wunsch — sie kommt von euch.** Lasst den Agenten nachbessern.

> Die fünf Kategorie-Namen stehen damit zweimal in der Spec (Enum + Schema).
> Das ist dieselbe Entscheidung wie `FROZEN` in Aufgabe C — Duplikation
> *innerhalb* des Orakels ist der Preis dafür, dass [`specyaml.py`](../tools/specyaml.py) kein
> `$ref` auflöst (siehe **Für zu Hause**).

Erst wenn die Checkliste steht: Freigabe geben und die Datei ändern lassen
(Tab zurück in den Build-Modus) — oder das YAML von Hand übernehmen.

> **Warum das Review nicht optional ist:** In Teil 1 war der Test wertlos,
> dessen Erwartung aus dem Prüfling kam. Eine Spec, die derselbe Agent
> geschrieben hat, der gleich implementiert — und die niemand geprüft hat —
> wäre **dieselbe Falle eine Etage höher**: ein mitwanderndes Orakel. Erst
> euer Review macht den Entwurf zum Vertrag.

**Abnahme von Aufgabe D — beide Kommandos:**

```bash
python3 -m pytest tests/test_openapi_spec.py -q   # 4 passed — u. a. weil jede
                                                  # Operation eine operationId hat
python3 tools/spec_gate.py api/app.py             # genau 1 Befund:
                                                  # ROUTE GET /tickets/stats fehlt
```

Der eine rote Befund ist der Punkt von Spec-first: **das Gate ist jetzt die
Aufgabenbeschreibung.** Rot beginnt beim Gate, nicht beim Bugreport.

> `--check` ist zwischen Aufgabe D und E absichtlich rot („NICHT BESTANDEN") —
> es misst das Endergebnis, nicht den Zwischenstand. Der Einzelaufruf oben ist
> hier die richtige Messung.

### Aufgabe E — Plan reviewen, dann implementieren lassen (~15 min)

**Erst der Plan — immer noch kein Code** (Plan-Modus):

```text
Die Spec deklariert jetzt GET /tickets/stats mit dem Schema
StatistikReport. Schreibe einen Umsetzungsplan für api/app.py in
maximal 10 Zeilen — noch keinen Code:
1. welche vorhandenen Module und Objekte du wiederverwendest,
2. wo in der Datei der neue Handler stehen muss und warum,
3. wie du das Ergebnis verifizierst.
```

**Plan-Review — vier Fragen, je 30 Sekunden:**

1. Nennt er `_STORE` und `src.triage.classify_and_prioritize` — oder erfindet
   er eine eigene Datenhaltung? (In [`src/stats.py`](../src/stats.py) steckt sogar schon
   Counter-Logik, aber sie *druckt* nur — findet er sie?)
2. Plant er ein Pydantic-Modell mit `response_model`, wie die übrigen
   Endpunkte? (Ohne das prüft das Gate sein Response-Schema stumm nicht.)
3. Sagt er etwas Belastbares zur **Position** des Handlers in der Datei?
   Wenn nein: **nicht einsagen, nur notieren** — Aufgabe F kommt darauf zurück.
4. Steht echte Verifikation drin (`spec_gate`, pytest) — oder „sieht dann
   gut aus"?

Fehlt Punkt 1, 2 oder 4: zurückgeben, nachbessern lassen. Das ist der zweite
Review-Übergang — billiger als jedes Code-Review danach.

**Dann erst: Implement** (Tab → Build-Modus):

```text
Setz deinen Plan um. Ändere nur api/app.py, halte dich exakt an die
Spec, erfinde nichts dazu. Prüfe dein Ergebnis mit:
python3 tools/spec_gate.py api/app.py
```

**Danach: Diff lesen, bevor ihr validiert** (`git diff api/app.py`). Ihr seid
Auftraggeber und Prüfer, nicht Zuschauer. Notiert für den Abschluss: Was hat
der Agent stillschweigend entschieden, das weder in Spec noch Plan stand?

> **Wer eine `AGENTS.md` aus der Vorlesungsübung hat:** ins
> Wurzelverzeichnis legen — opencode liest sie automatisch. Ein Durchlauf
> mit und einer ohne ist das Mit/Ohne-Experiment aus Teil 4 der Vorlesung,
> diesmal am echten Feature.
>
> **Falls HomeCloud klemmt** (Fenster, Cold Start, Ausfall): Spec entlang
> der Checkliste aus Aufgabe D von Hand schreiben, Endpunkt von Hand
> implementieren — es sind ~15 Zeilen mit `collections.Counter`. Die
> Validierung in Aufgabe F ist exakt dieselbe; das Lab hängt nicht am Agenten.

### Aufgabe F — Dreifach beweisen (~15 min)

Der Agent hat geliefert. Jetzt gilt das Muster des Tages — **stochastischer
Generator, deterministische Prüfer** — mit drei Prüfern, die verschiedene
Dinge sehen:

**1. Das statische Gate** (Struktur: Routen, Statuscodes, Query-Parameter,
Response-Felder):

```bash
python3 tools/spec_gate.py --check
# grün auf api/app.py             : 0 Befund(e)  OK
# rot   auf api/drifted_server.py : 8 Befund(e)  OK   ← 7 + euer neues Feature,
#                                                       das dort natürlich fehlt
```

> **Eine Zeile fehlt noch:** Das Gate prüft Response-Felder gegen
> `SPEC_RESPONSE_FIELDS` in [`tools/spec_gate.py`](../tools/spec_gate.py) — und Schemas, die dort
> nicht eingetragen sind, prüft es **stumm gar nicht**. Tragt
> `"StatistikReport": {"gesamt", "kategorien", "prioritaeten"}` nach und lauft
> erneut. **Die Zahlen bewegen sich dabei nicht** — eine korrekte
> Implementierung besteht mit und ohne Eintrag. Dass der Eintrag trotzdem
> etwas tut, beweist ihr in zwei Zeilen: benennt im Pydantic-Modell `gesamt`
> testweise in `total` um → jetzt meldet das Gate einen SCHEMA-Befund, wo es
> vorher geschwiegen hätte. Dann zurückbenennen. Ein von Hand gepflegtes
> Orakel ignoriert, was es nicht kennt — lautlos. (Die Kür, die das dict
> ganz abschafft: **Für zu Hause**.)

**2. Die Offline-Tests** (Spec self-consistent, Triage unangetastet):

```bash
python3 -m pytest tests/test_openapi_spec.py tests/test_triage.py -q
```

**3. Der Contract-Test gegen den laufenden Server** (Verhalten — Schemathesis
generiert aus der Spec hunderte Requests, auch gegen euren neuen Endpunkt):

```bash
python3 -m uvicorn api.app:app &          # Terminal 1 (oder eigenes Fenster)
schemathesis run api/openapi.yaml --url http://localhost:8000 --checks all
```

**Zwei Befunde, die euch hier begegnen können — beide für das statische Gate
unsichtbar:**

- **404 auf `GET /tickets/stats`, obwohl der Code richtig aussieht:** FastAPI
  matcht Routen in Deklarations-Reihenfolge. Steht der neue Handler *hinter*
  `GET /tickets/{ticket_id}`, fängt der Platzhalter „stats" als `ticket_id`
  ab. Das Gate sieht beide Routen im `ast` und ist zufrieden — **Reihenfolge
  ist Laufzeitverhalten.** Fix: Handler vor `get_ticket` verschieben.
  Hat euer Agent die Position von sich aus richtig gewählt: provoziert den
  Fall trotzdem einmal — schiebt den Handler testweise *hinter* `get_ticket`,
  startet den Server neu, beobachtet den 404 bei weiterhin grünem Gate, und
  schiebt ihn zurück.
- **Schema-Verletzung, wenn eine Kategorie 0 Tickets hat:** Wer das Ergebnis
  aus einem `Counter` baut, ohne über alle Kategorien zu iterieren, lässt
  Null-Schlüssel weg. Mit den ausgelieferten 30 Tickets fällt das **nicht**
  auf — sie decken zufällig jede Kategorie und jede Priorität ab. Provoziert
  den Fall deshalb gezielt: setzt die Befüllung von `_STORE` in
  [`api/app.py`](../api/app.py) testweise auf `{}` (die Zeile mit
  `load_tickets()`), startet den Server neu, ruft `GET /tickets/stats` ab —
  und macht die Änderung danach rückgängig. Die Spec verlangt die
  Null-Schlüssel — das ist das `required` aus **eurem** Review in Aufgabe D.
  Das Gate vergleicht nur Feld-*Namen* des Pydantic-Modells, nie Werte zur
  Laufzeit; ohne euer Review würde hier **kein** Prüfer anschlagen.

Wenn alle drei Prüfer grün sind, ist das Feature **bewiesen konform** — nicht
„sieht gut aus", nicht „lief bei mir". Das ist der Unterschied zwischen
Vibe Coding und Spec-Driven.

---

## Teil 3 — Abschluss (~5 min)

Jede/r nennt im Chat **zwei Zahlen und einen Satz**:

1. Euer Score aus `--suite frozen`.
2. Befunde des Gates auf [`drifted_server.py`](../api/drifted_server.py) nach eurem Feature (8?) — und
   auf [`app.py`](../api/app.py) (Ziel: 0, bei grünem Schemathesis-Lauf).
3. **Ein Befund aus Aufgabe F, den nur einer der drei Prüfer finden konnte —
   und warum die anderen beiden strukturell blind dafür sind.**

**Leitfragen:**

- Wann ist DRY beim Testen falsch? (Immer, wenn die Erwartung dadurch aus dem
  Prüfling stammt — gilt für `FROZEN` wie für `SPEC_RESPONSE_FIELDS`.)
- Was findet das statische Gate, was Schemathesis nicht findet — und
  umgekehrt? (Statisch: fehlende/unspezifizierte Routen, ohne Server, ohne
  Risiko. Contract: alles Laufzeitverhalten — Reihenfolge, Werte,
  Validierung —, dafür nur, was die Spec deklariert: den unspezifizierten
  `/health` des Drift-Servers kann Schemathesis prinzipiell nicht sehen.)
- Was musste euer Review an Spec-Entwurf oder Plan korrigieren — und hätte
  der Agent das wissen *können*? (Die 0-Tickets-Regel konnte er nicht — sie
  stand in keinem Artefakt. Genau dafür sind die Review-Übergänge da.)

---

## Für zu Hause (freiwillig)

1. **TODO 3 in [`tests/test_triage_oracle.py`](../tests/test_triage_oracle.py)** — die ehrliche Grenze: dieselbe
   Schleife, Keyword nur im Betreff. Der Test ist grün und findet nichts
   Neues. Warum das kein Mangel ist, steht als Aufgabe im Kommentar.
   (`python3 tools/mutation_dojo.py --tests tests/test_triage_oracle.py`)
2. **Äquivalenz nachrechnen** (aus der Vorlesung): 26 von 34 — sind die
   fehlenden 8 unsere Schuld?
   ```bash
   python3 tools/mutation_dojo.py --equivalence Netzwerk:wlan        # einer der 8
   python3 tools/mutation_dojo.py --equivalence Netzwerk:lan         # Kontrolle 1
   python3 tools/mutation_dojo.py --equivalence Abrechnung:rechnung  # Kontrolle 2
   ```
   Korrigierter Score: 26 / (34 − 8) = **1,000**. Und `rechnung` zeigt den
   Unterschied zwischen *„unsere Suite sieht es nicht"* und *„niemand kann es
   sehen"* — nur das zweite rechtfertigt den Abzug im Nenner.
3. **Die Kür — `$ref` auflösen:** Leitet `SPEC_RESPONSE_FIELDS` in
   [`tools/spec_gate.py`](../tools/spec_gate.py) aus `spec["schemas"]` her und **löscht das dict**.
   Danach wird euer `StatistikReport` automatisch geprüft — ohne Handeintrag.
   Drei Fallen: `$ref` in Responses, Array-Responses (`GET /tickets` liefert
   `items.$ref -> Ticket` — auf Implementierungsseite `list[Ticket]`
   entpacken!), und das Abnahme-Kriterium muss danach **immer noch** gelten.
4. **CI-Bonus:** Ein GitHub-Actions-Workflow, der bei jedem PR
   `python3 tools/spec_gate.py --check` und Schemathesis ausführt. Drift
   macht dann den Build rot — die „Medizin gegen Spec Drift" aus der
   Vorlesung, mechanisch verabreicht.

---

## Troubleshooting

| Problem | Lösung |
|---|---|
| `ModuleNotFoundError: No module named 'src'` | Testdatei nicht direkt starten. `python3 tools/mutation_dojo.py --tests ...` oder `python3 -m pytest` **im Repo-Wurzelverzeichnis** verwenden |
| `ModuleNotFoundError: No module named 'fastapi'` | venv aktivieren, `pip install -r requirements.txt` |
| `--suite oracle` meldet „TODO 1 ist noch nicht gefüllt" | der Rumpf von `test_jedes_keyword_trifft_seine_kategorie()` ist noch `...` — oder die Funktion wurde umbenannt. Der Dojo sucht sie namentlich |
| `--suite frozen` meldet „FROZEN ist leer" | TODO 2 trägt die Tabelle ein — als ausgeschriebenes Literal, nicht aus `CATEGORY_KEYWORDS` abgeleitet |
| `--suite ...` meldet „schon auf dem INTAKTEN Modul rot" | der Test ist falsch gefüllt. Erst reparieren: ein Score auf roter Suite ist bedeutungslos |
| opencode: erste Antwort hängt minutenlang | Cold Start (200–300 s). Warten, nicht abbrechen |
| opencode: 401 / „unauthorized" | `apiKey` in `~/.config/opencode/opencode.json` prüfen ([`SETUP.md`](../SETUP.md)) |
| opencode ändert Dateien, obwohl ihr nur einen Entwurf wolltet | in den **Plan-Modus** wechseln (Tab schaltet Build/Plan um) und „Ändere noch keine Datei" in den Prompt schreiben |
| 403, „nur montags 06:00–23:59 …" | außerhalb des HomeCloud-Zeitfensters — kein Bug, montags wiederkommen |
| Gate meldet Befunde auf [`api/app.py`](../api/app.py) | **vor** Aufgabe E ist genau 1 ROUTE-Befund richtig. **Danach:** Diff lesen — meist EXTRA (erfundene Route), STATUS (Default 200 statt Spec-Code) oder QPARAM (erfundener Parameter) |
| Server startet nicht | `python3 -m uvicorn api.app:app` verwenden (nicht das bare `uvicorn`-Kommando) |
| Schemathesis: „connection refused" / findet nichts | läuft der Server auf dem Port aus `--url`? Referenz-Server = 8000 |
| Schemathesis: 404 auf `GET /tickets/stats` | Routen-Reihenfolge: der `stats`-Handler muss **vor** `GET /tickets/{ticket_id}` deklariert sein (siehe Aufgabe F) |
| pytest/Gate verhalten sich nach der Spec-Änderung seltsam | YAML-Stil prüfen: [`specyaml.py`](../tools/specyaml.py) versteht nur die Teilmenge der bestehenden Spec — Blockstil, keine Flow-Maps `{ ... }` (Checkliste in Aufgabe D) |
| `python` statt `python3` findet nichts | in diesem Lab immer `python3` verwenden |
