# Lab VL 9 — Das Orakel: woher weiß ein Test, was richtig ist?

**Ziel:** Ihr messt an eurem eigenen Triage-Modul, dass eine grüne Test-Suite
fast nichts prüft, findet heraus warum (die Erwartung kommt aus dem
Prüflings-Code selbst), und baut danach ein Gate, das eine Implementierung
maschinell gegen die OpenAPI-Spec prüft — und das auf dem *korrekten* Server
grün bleibt.

**Dauer:** ~80 Minuten in 90 (Setup: ~5 · Teil 1: ~45 · Teil 2 Pflichtteil:
~25 · Abschluss: ~5 · Rest Puffer). Die **Vertiefung** in Teil 2 ist
freiwillig und braucht noch einmal ~30 min — realistisch eher für zu Hause
als für den Slot.

---

## Schritt 0 — Setup (5 min)

```bash
cd leinetech
git checkout vl09-oracle
python3 --version            # 3.11+; mehr braucht ihr heute nicht
```

> **Keine Installation notwendig.** Das ganze Lab läuft mit reiner
> Standardbibliothek: kein `pip install`, kein Server, kein API-Key, kein Netz.
> Falls ihr `pytest` in einem venv habt, könnt ihr es benutzen — müsst ihr
> aber nicht. Jede Zahl in diesem Lab ist ohne pytest erreichbar; wo ein
> Test-Runner nötig wäre, bringt [`tools/mutation_dojo.py`](../tools/mutation_dojo.py) einen mit
> (`--tests`, `--aufgabe-e`).

Smoke-Test — muss `eliminiert 4` melden:

```bash
python3 tools/mutation_dojo.py --suite shipped
```

---

## Teil 1 — Das Orakel (~45 min)

[`src/triage.py`](../src/triage.py) ordnet Tickets per Keyword-Listen ein. 61 Zeilen, keine
Verzweigungen, das ganze Verhalten steckt in zwei dicts. [`tests/test_triage.py`](../tests/test_triage.py)
hat 5 Tests, alle grün.

### Aufgabe A — Schätzen, dann messen (~10 min)

[`src/triage.py`](../src/triage.py) enthält **34 Kategorie-Keywords**. Mutantenklasse heute:
*ein Keyword aus einer Liste löschen*.

```bash
python3 tools/mutation_dojo.py --list        # die 34, ohne Beschreibung
```

`--list` zeigt genau die Mutantenklasse, um die es heute geht. Mit
`--scope all` kommen die 11 Prioritäts-Keywords dazu: **45** Mutanten,
anderer Nenner, anderer Score, dieselbe Implementierung. Merkt euch die
zwei Zahlen — Teil 3 fragt danach.

**Schreibt eure Schätzung in den Chat, BEVOR ihr weitermacht:** Wie viele der
34 Mutanten eliminiert die ausgelieferte Suite?

```bash
python3 tools/mutation_dojo.py --suite shipped
```

**Erwartete Ausgabe:** `Mutanten 34 · eliminiert 4 · Mutation Score (roh) 4/34 = 0.118`,
eliminiert werden `laptop`, `drucker`, `vpn`, `zugriff`.

**Diskutiert:** Was haben genau diese vier gemeinsam? (Antwort: sie sind die
einzigen Keywords, die wörtlich in den Texten der fünf Tests vorkommen. Die
Keyword-Listen sind *Daten*, keine Verzweigungen — Coverage sieht sie beim
Import als abgedeckt und kann ein geprüftes Keyword nicht von einem
ungeprüften unterscheiden.)

### Aufgabe B — Die naheliegende Refaktorierung (~15 min)

Öffnet [`tests/test_triage_oracle.py`](../tests/test_triage_oracle.py). **TODO 1** dort ist der Test, den man in
jedem Review vorschlagen würde: keine Magic Strings, eine Schleife über
`CATEGORY_KEYWORDS`.

Schreibt ihn. Dann:

```bash
python3 tools/mutation_dojo.py --suite oracle
```

> `--suite oracle` führt **eure** Funktion aus [`tests/test_triage_oracle.py`](../tests/test_triage_oracle.py)
> aus. Der Dojo hat keine eigene Kopie davon — was ihr schreibt, ist genau
> das, was gemessen wird. Solange TODO 1 leer ist, sagt er das und misst
> nichts: ein Score auf einem leeren Test wäre die nächste Orakel-Falle.

**Notiert die Zahl, bevor ihr weiterliest.** Sie überrascht: 34 geprüfte
Keywords statt 5 handgeschriebener Fälle — und der Score geht **runter**,
nicht rauf.

**Warum:** Der Test importiert seine Erwartung aus dem Modul, das er prüft.
Löscht der Mutant ein Keyword, verschwindet der zugehörige Testfall
*mitsamt der Erwartung*. Es bleibt nichts, was fehlschlagen könnte. Das ist die
Orakel-Falle aus der Vorlesung — mit einem Orakel, das sich **mitbewegt**.

Vergleicht mit dem ACH-Filter aus der Theorie: ein Test taugt nur, wenn er auf
dem Mutanten FEHLSCHLÄGT **und** auf dem Original BESTEHT. Diese Suite
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

**TODO 3** in derselben Datei ist die ehrliche Grenze: dieselbe Schleife, das
Keyword aber nur im Betreff. Kein Score, nur grün/rot:

```bash
python3 tools/mutation_dojo.py --tests tests/test_triage_oracle.py
```

Der Test besteht — und findet **nichts**, was die beiden Tests oben nicht
schon gefunden hätten. Warum das kein Mangel ist, sondern die Antwort auf
eine andere Frage, steht als Aufgabe im Kommentar.

### Aufgabe D — Die 8, die übrig bleiben (~5 min)

26 von 34, nicht 34 von 34. Welche 8 fehlen, und ist das unsere Schuld?

Nur das erste Kommando fragt nach einem der 8. Die anderen beiden sind
Kontrollen — sie zeigen, was Äquivalenz **nicht** ist:

```bash
python3 tools/mutation_dojo.py --equivalence Netzwerk:wlan        # einer der 8
python3 tools/mutation_dojo.py --equivalence Netzwerk:lan         # Kontrolle 1
python3 tools/mutation_dojo.py --equivalence Abrechnung:rechnung  # Kontrolle 2
```

Zwei **strukturell verschiedene** Äquivalenzen in 61 Zeilen:

- die 7 Keywords der `Software`-Zeile — `Software` wird als **letzte** Zeile
  geprüft **und** ist `DEFAULT_CATEGORY`; "getroffen" und "durchgefallen"
  liefern dasselbe Ergebnis. **Kontrollfluss.**
- `wlan` — `"lan"` ist ein Substring von `"wlan"` und steht in **derselben
  Zeile**. Jeder Text mit `wlan` enthält auch `lan`. **Matching-Primitive.**
  Die Asymmetrie ist die Pointe: `wlan` ist äquivalent, `lan` nicht.

Damit ist der korrigierte Score **26 / (34 − 8) = 26/26 = 1,000**.

Und die zweite Kontrolle: `rechnung` gehört gar nicht zu den 8 — `frozen`
eliminiert es. Es überlebt die *ausgelieferte* Suite aus Aufgabe A, und es ist
**nicht** äquivalent. *"Unsere Suite kann es nicht sehen"* und *"niemand kann
es sehen"* sind zwei verschiedene Aussagen; nur die zweite rechtfertigt einen
Abzug im Nenner.

### Aufgabe E — Die Brücke zu Teil 2 (~5 min)

Löscht nicht ein Keyword, sondern den **Schlüssel** `"Software"`:

```bash
python3 tools/mutation_dojo.py --aufgabe-e
```

Der Mutant wird im Speicher gesetzt, keine Datei ändert sich.

[`tests/test_triage.py`](../tests/test_triage.py) bleibt **grün (5/5)** — `DEFAULT_CATEGORY` ist
weiterhin `"Software"`, die Triage liefert für jeden Text also dasselbe wie
vorher. [`tests/test_openapi_spec.py`](../tests/test_openapi_spec.py) wird **rot (3/4)**: der Test vergleicht
das `Kategorie`-Enum der Spec gegen `CATEGORY_KEYWORDS`.

Der Unterschied zwischen den beiden Dateien ist nicht Sorgfalt, sondern
**wo ihre Erwartung liegt**.

> **Die maschinenlesbare Spec ist das einzige Orakel in diesem Repo, das
> außerhalb des Codes liegt, den es beurteilt.** Genau so eines baut ihr jetzt
> für die API.

---

## Teil 2 — Das Gate (~25 min Pflichtteil, Vertiefung freiwillig)

[`api/drifted_server.py`](../api/drifted_server.py) weicht absichtlich von [`api/openapi.yaml`](../api/openapi.yaml) ab. **Die
Abweichungen sind kein Geheimnis** — hier sind sie:

| # | Abweichung |
|---|---|
| 1 | `TicketEingabe`/`Ticket`: Pflichtfeld `von` fehlt |
| 2 | `POST /tickets/{id}/triage`: Response-Feld heißt `prio` statt `prioritaet` |
| 3 | `GET /tickets`: Query-Parameter `kategorie` fehlt |
| 4 | `GET /tickets/{id}`: liefert 400 statt 404 |
| 5 | `POST /tickets/{id}/escalate` fehlt ganz |
| 6 | `GET /health` existiert, steht aber in keiner Spec |

**Die Aufgabe ist nicht, sie zu finden. Die Aufgabe ist das Gate, das sie
findet — ohne auf dem korrekten Server Alarm zu schlagen.**

(Sechs Abweichungen, aber mehr als sechs Befunde: das fehlende `von` schlägt
auf zwei Endpunkten zu. Ein Befund ist nicht dasselbe wie eine Ursache.)

### Abnahme-Kriterium — beide Zeilen müssen OK sein

```bash
python3 tools/spec_gate.py --check
```

```
Abnahme-Kriterium (beide Zeilen müssen OK sein):
  grün auf api/app.py             : 0 Befund(e)  OK
  rot   auf api/drifted_server.py : 7 Befund(e)  OK

BESTANDEN
```

Die `7` ist *unsere* Zahl; verlangt sind `>= 5`. Die `0` in der ersten Zeile
ist dagegen keine Untergrenze, sondern exakt.

Ein Gate, das immer rot ist, ist von einem funktionierenden nicht zu
unterscheiden. Ein Gate, das immer grün ist, auch nicht.

### Pflichtteil (~25 min)

Füllt die **sechs TODOs** in [`tools/spec_gate.py`](../tools/spec_gate.py). Fertig und getestet sind
schon: der Spec-Leser ([`tools/specyaml.py`](../tools/specyaml.py), Standardbibliothek), das
`ast`-Modell der Implementierung, die Aufrufverfolgung für erhobene
Statuscodes, und die Ausgabe. Ihr schreibt nur die Vergleiche.

Kein Server, kein Import des Prüflings — rein statische Analyse. Ein
kaputter Server kann euer Gate nicht beeinflussen.

**Zwei Fallen sind absichtlich eingebaut, und ihr wisst jetzt davon:**

1. In [`api/app.py`](../api/app.py) wird der 404 nicht im Handler erhoben, sondern in der
   Hilfsfunktion `_require()`. Ein Gate, das nur den Funktionskörper ansieht,
   erklärt den **korrekten** Server für kaputt. (Die Aufrufverfolgung ist
   fertig — versteht, *warum* sie nötig ist.)
2. `400` und `422` erzeugt FastAPI selbst, ohne `raise` im Handler. Fordert ihr
   sie, schlägt das Gate wieder auf [`app.py`](../api/app.py) an. Siehe `FRAMEWORK_CODES` —
   und entscheidet bewusst, welche Codes die *Anwendung* besitzt.

### Vertiefung (freiwillig, ~30 min — nur wenn der Pflichtteil steht)

`SPEC_RESPONSE_FIELDS` in [`tools/spec_gate.py`](../tools/spec_gate.py) ist von Hand eingetragen, weil
[`tools/specyaml.py`](../tools/specyaml.py) **kein `$ref` auflöst**. Löst `$ref` gegen
`spec["schemas"]` auf, leitet die Response-Felder aus der Spec ab und
**löscht das hartcodierte dict**. Das Abnahme-Kriterium muss danach immer
noch gelten.

**Dritte Falle, gleiche Sorte wie die beiden oben:** `GET /tickets` liefert ein
**Array**. Sobald ihr `$ref` auflöst, seht ihr auch `items.$ref -> Ticket` —
und müsst auf der Implementierungsseite `list[Ticket]` entpacken. Sonst
erklärt euer Gate wieder den korrekten Server für kaputt, diesmal mit einem
`SCHEMA`-Befund auf `GET /tickets`.

Der Zeitbedarf ist ehrlich höher als er aussieht: `$ref` auflösen,
Array-Responses behandeln, `list[X]` entpacken. Plant das eher für zu Hause
ein als für die letzten Minuten des Slots.

Das ist die Aufgabe mit dem größten Ertrag: danach liest euer Gate die Spec
wirklich, statt sie teilweise nachzuerzählen.

---

## Teil 3 — Abschluss (~5 min)

Jede/r nennt im Chat **zwei Zahlen und einen Satz**:

1. Euer Score aus `--suite frozen`.
2. Wie viele Befunde euer Gate auf [`drifted_server.py`](../api/drifted_server.py) findet — und wie viele
   auf [`app.py`](../api/app.py) (Ziel: 0).
3. **Welche Abweichungsklasse euer Gate strukturell nicht finden kann.**

Zu 3: [`tools/specyaml.py`](../tools/specyaml.py) sieht Pfade, Methoden, Statuscodes und
Query-Parameter-Namen. `requestBody`, `required`, `minimum`, `minLength`,
`pattern`, `enum` liegen außerhalb seines Blickfelds — und Laufzeitverhalten
sowieso. Dafür gibt es Contract-Testing-Werkzeuge wie Schemathesis, die gegen
einen **laufenden** Server feuern.

**Leitfragen:**

- Wann ist DRY beim Testen falsch? (Antwort: immer, wenn die Erwartung dadurch
  aus dem Prüfling stammt.)
- Was findet ein statisches Gate, was ein Contract Test nicht findet — und
  umgekehrt? (Statisch: fehlende Routen, Feldnamen, unspezifizierte Endpunkte,
  ohne Server. Contract: alles Laufzeitverhalten, dafür nur was erreichbar ist.)
- Warum ist ein Mutation Score ohne Angabe der Mutantenklasse bedeutungslos?

---

## Troubleshooting

| Problem | Lösung |
|---|---|
| `ModuleNotFoundError: No module named 'src'` | ihr habt eine Testdatei direkt gestartet (`python3 tests/...`). Nehmt `python3 tools/mutation_dojo.py --tests tests/test_triage_oracle.py` — die Werkzeuge legen das Repo-Wurzelverzeichnis selbst in `sys.path`, eine einzeln gestartete Testdatei nicht |
| `--suite oracle` meldet „TODO 1 ist noch nicht gefüllt" | der Rumpf von `test_jedes_keyword_trifft_seine_kategorie()` ist noch `...` — oder die Funktion wurde umbenannt. Der Dojo sucht sie namentlich |
| `--suite frozen` meldet „FROZEN ist leer" | TODO 2 trägt die Tabelle ein — als ausgeschriebenes Literal, nicht aus `CATEGORY_KEYWORDS` abgeleitet |
| `--suite ...` meldet „schon auf dem INTAKTEN Modul rot" | der Test ist falsch gefüllt. Erst reparieren: ein Score auf roter Suite ist bedeutungslos |
| Gate meldet Befunde auf [`api/app.py`](../api/app.py) | eine der beiden Fallen: Aufrufverfolgung (404 in `_require`) oder `FRAMEWORK_CODES` (400/422). Nach der Vertiefung kommt eine dritte dazu: `list[Ticket]` bei `GET /tickets` |
| Gate meldet 0 Befunde auf [`drifted_server.py`](../api/drifted_server.py) | TODOs noch leer — `gate()` gibt eine leere Liste zurück |
| `python` statt `python3` findet nichts | in diesem Lab immer `python3` verwenden |
| pytest fehlt | wird nicht gebraucht. Jede Zahl kommt aus [`tools/mutation_dojo.py`](../tools/mutation_dojo.py) und [`tools/spec_gate.py`](../tools/spec_gate.py); `--tests` und `--aufgabe-e` ersetzen den Test-Runner |
| Musterlösung | [`labs/loesung/`](loesung/) — erst nach dem Lab. **Vor dem Push an die Studierenden verschieben oder löschen.** |
