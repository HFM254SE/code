# Lab VL 9 — Das Orakel: woher weiss ein Test, was richtig ist?

**Ziel:** Ihr messt an eurem eigenen Triage-Modul, dass eine gruene Test-Suite
fast nichts prueft, findet heraus warum (die Erwartung kommt aus dem
Prueflings-Code selbst), und baut danach ein Gate, das eine Implementierung
maschinell gegen die OpenAPI-Spec prueft — und das auf dem *korrekten* Server
gruen bleibt.

**Dauer:** ~90 Minuten (Setup: ~5 min · Teil 1: ~40 min · Teil 2: ~40 min · Abschluss: ~5 min)

---

## Schritt 0 — Setup (5 min)

```bash
cd leinetech
git checkout vl09-oracle
python3 --version            # 3.11+; mehr braucht ihr heute nicht
```

> **Keine Installation notwendig.** Das ganze Lab laeuft mit reiner
> Standardbibliothek: kein `pip install`, kein Server, kein API-Key, kein Netz.
> Falls ihr `pytest` in einem venv habt, koennt ihr es benutzen — muesst ihr
> aber nicht. Jede Zahl in diesem Lab ist ohne pytest erreichbar.

Smoke-Test — muss `getoetet 4` melden:

```bash
python3 tools/mutation_dojo.py --suite shipped
```

---

## Teil 1 — Das Orakel (~40 min)

`src/triage.py` ordnet Tickets per Keyword-Listen ein. 61 Zeilen, keine
Verzweigungen, das ganze Verhalten steckt in zwei dicts. `tests/test_triage.py`
hat 5 Tests, alle gruen.

### Aufgabe A — Schaetzen, dann messen (~10 min)

`src/triage.py` enthaelt **34 Kategorie-Keywords**. Mutantenklasse heute:
*ein Keyword aus einer Liste loeschen*.

```bash
python3 tools/mutation_dojo.py --list        # alle Mutanten, ohne Beschreibung
```

**Schreibt eure Schaetzung in den Chat, BEVOR ihr weitermacht:** Wie viele der
34 Mutanten toetet die ausgelieferte Suite?

```bash
python3 tools/mutation_dojo.py --suite shipped
```

**Erwartete Ausgabe:** `Mutanten 34 · getoetet 4 · Mutation Score (roh) 4/34 = 0.118`,
getoetet sind `laptop`, `drucker`, `vpn`, `zugriff`.

**Diskutiert:** Was haben genau diese vier gemeinsam? (Antwort: sie sind die
einzigen Keywords, die woertlich in den Texten der fuenf Tests vorkommen. Die
Keyword-Listen sind *Daten*, keine Verzweigungen — Coverage sieht sie beim
Import als abgedeckt und kann ein geprueftes Keyword nicht von einem
ungepruefte unterscheiden.)

### Aufgabe B — Die naheliegende Refaktorierung (~15 min)

Oeffnet `tests/test_triage_oracle.py`. **TODO 1** dort ist der Test, den man in
jedem Review vorschlagen wuerde: keine Magic Strings, eine Schleife ueber
`CATEGORY_KEYWORDS`.

Schreibt ihn. Dann:

```bash
python3 tools/mutation_dojo.py --suite oracle
```

**Notiert die Zahl, bevor ihr weiterliest.** Sie ueberrascht: 34 Testfaelle
statt 5, hoehere Coverage, und der Score geht **runter**, nicht rauf.

**Warum:** Der Test importiert seine Erwartung aus dem Modul, das er prueft.
Loescht der Mutant ein Keyword, verschwindet der zugehoerige Testfall
*mitsamt der Erwartung*. Es bleibt nichts, was fehlschlagen koennte. Das ist die
Orakel-Falle aus der Vorlesung — mit einem Orakel, das sich **mitbewegt**.

Vergleicht mit dem ACH-Filter aus der Theorie: ein Test taugt nur, wenn er auf
dem Mutanten FEHLSCHLAEGT **und** auf dem Original BESTEHT. Diese Suite
erfuellt genau die Haelfte davon.

### Aufgabe C — Eine Zeile Unterschied (~10 min)

**TODO 2** in derselben Datei: derselbe Test, aber die Erwartung steht als
eingefrorene Kopie **in der Testdatei**.

```bash
python3 tools/mutation_dojo.py --suite frozen
```

**Erwartete Ausgabe:** `getoetet 26 · Mutation Score (roh) 26/34 = 0.765`.

Ja, das dupliziert Daten. **Notiert im Code-Kommentar, warum das hier richtig
ist** — DRY gilt fuer Produktionscode, nicht fuer Orakel.

### Aufgabe D — Die 8, die uebrig bleiben (~5 min)

26 von 34, nicht 34 von 34. Welche 8 fehlen, und ist das unsere Schuld?

```bash
python3 tools/mutation_dojo.py --equivalence Netzwerk:wlan
python3 tools/mutation_dojo.py --equivalence Netzwerk:lan
python3 tools/mutation_dojo.py --equivalence Abrechnung:rechnung
```

Zwei **strukturell verschiedene** Aequivalenzen in 61 Zeilen:

- die 7 Keywords der `Software`-Zeile — `Software` wird als **letzte** Zeile
  geprueft **und** ist `DEFAULT_CATEGORY`; "getroffen" und "durchgefallen"
  liefern dasselbe Ergebnis. **Kontrollfluss.**
- `wlan` — `"lan"` ist ein Substring von `"wlan"` und steht in **derselben
  Zeile**. Jeder Text mit `wlan` enthaelt auch `lan`. **Matching-Primitive.**
  Die Asymmetrie ist die Pointe: `wlan` ist aequivalent, `lan` nicht.

Damit ist der korrigierte Score **26 / (34 − 8) = 26/26 = 1,000**, und die
Kontrolle sitzt bei `rechnung`: ueberlebt die ausgelieferte Suite, ist aber
**nicht** aequivalent. *"Unsere Suite kann es nicht sehen"* und *"niemand kann
es sehen"* sind zwei verschiedene Aussagen.

### Aufgabe E — Die Bruecke zu Teil 2 (~5 min, Dozent am Bildschirm)

Loescht nicht ein Keyword, sondern den **Schluessel** `"Software"`.
`tests/test_triage.py` bleibt gruen. `tests/test_openapi_spec.py` wird **rot**:
der Test vergleicht das `Kategorie`-Enum der Spec gegen `CATEGORY_KEYWORDS`.

> **Die maschinenlesbare Spec ist das einzige Orakel in diesem Repo, das
> ausserhalb des Codes liegt, den es beurteilt.** Genau so eines baut ihr jetzt
> fuer die API.

---

## Teil 2 — Das Gate (~40 min)

`api/drifted_server.py` weicht absichtlich von `api/openapi.yaml` ab. **Die
Abweichungen sind kein Geheimnis** — hier sind sie:

| # | Abweichung |
|---|---|
| 1 | `TicketEingabe`/`Ticket`: Pflichtfeld `von` fehlt |
| 2 | `POST /tickets/{id}/triage`: Response-Feld heisst `prio` statt `prioritaet` |
| 3 | `GET /tickets`: Query-Parameter `kategorie` fehlt |
| 4 | `GET /tickets/{id}`: liefert 400 statt 404 |
| 5 | `POST /tickets/{id}/escalate` fehlt ganz |
| 6 | `GET /health` existiert, steht aber in keiner Spec |

**Die Aufgabe ist nicht, sie zu finden. Die Aufgabe ist das Gate, das sie
findet — ohne auf dem korrekten Server Alarm zu schlagen.**

(Sechs Abweichungen, aber mehr als sechs Befunde: das fehlende `von` schlaegt
auf zwei Endpunkten zu. Ein Befund ist nicht dasselbe wie eine Ursache.)

### Abnahme-Kriterium — beide Zeilen muessen OK sein

```bash
python3 tools/spec_gate.py --check
```

```
gruen auf api/app.py            : 0 Befund(e)   OK
rot   auf api/drifted_server.py : >=5 Befund(e) OK
```

Ein Gate, das immer rot ist, ist von einem funktionierenden nicht zu
unterscheiden. Ein Gate, das immer gruen ist, auch nicht.

### Pflichtteil (~25 min)

Fuellt die **sechs TODOs** in `tools/spec_gate.py`. Fertig und getestet sind
schon: der Spec-Leser (`tools/specyaml.py`, Standardbibliothek), das
`ast`-Modell der Implementierung, die Aufrufverfolgung fuer erhobene
Statuscodes, und die Ausgabe. Ihr schreibt nur die Vergleiche.

Kein Server, kein Import des Prueflings — rein statische Analyse. Ein
kaputter Server kann euer Gate nicht beeinflussen.

**Zwei Fallen sind absichtlich eingebaut, und ihr wisst jetzt davon:**

1. In `api/app.py` wird der 404 nicht im Handler erhoben, sondern in der
   Hilfsfunktion `_require()`. Ein Gate, das nur den Funktionskoerper ansieht,
   erklaert den **korrekten** Server fuer kaputt. (Die Aufrufverfolgung ist
   fertig — versteht, *warum* sie noetig ist.)
2. `400` und `422` erzeugt FastAPI selbst, ohne `raise` im Handler. Fordert ihr
   sie, schlaegt das Gate wieder auf `app.py` an. Siehe `FRAMEWORK_CODES` —
   und entscheidet bewusst, welche Codes die *Anwendung* besitzt.

### Vertiefung (freiwillig, nur wenn der Pflichtteil steht)

`SPEC_RESPONSE_FIELDS` in `tools/spec_gate.py` ist von Hand eingetragen, weil
`tools/specyaml.py` **kein `$ref` aufloest**. Loest `$ref` gegen
`spec["schemas"]` auf, leitet die Response-Felder aus der Spec ab und
**loescht das hartcodierte dict**. Das Abnahme-Kriterium muss danach immer
noch gelten.

Das ist die Aufgabe mit dem groessten Ertrag: danach liest euer Gate die Spec
wirklich, statt sie teilweise nachzuerzaehlen.

---

## Teil 3 — Abschluss (~5 min)

Jede/r nennt im Chat **zwei Zahlen und einen Satz**:

1. Euer Score aus `--suite frozen`.
2. Wie viele Befunde euer Gate auf `drifted_server.py` findet — und wie viele
   auf `app.py` (Ziel: 0).
3. **Welche Abweichungsklasse euer Gate strukturell nicht finden kann.**

Zu 3: `tools/specyaml.py` sieht Pfade, Methoden, Statuscodes und
Query-Parameter-Namen. `requestBody`, `required`, `minimum`, `minLength`,
`pattern`, `enum` liegen ausserhalb seines Blickfelds — und Laufzeitverhalten
sowieso. Dafuer gibt es Contract-Testing-Werkzeuge wie Schemathesis, die gegen
einen **laufenden** Server feuern.

**Leitfragen:**

- Wann ist DRY beim Testen falsch? (Antwort: immer, wenn die Erwartung dadurch
  aus dem Pruefling stammt.)
- Was findet ein statisches Gate, was ein Contract Test nicht findet — und
  umgekehrt? (Statisch: fehlende Routen, Feldnamen, unspezifizierte Endpunkte,
  ohne Server. Contract: alles Laufzeitverhalten, dafuer nur was erreichbar ist.)
- Warum ist ein Mutation Score ohne Angabe der Mutantenklasse bedeutungslos?

---

## Troubleshooting

| Problem | Loesung |
|---|---|
| `ModuleNotFoundError: src` | aus dem Repo-Wurzelverzeichnis starten (`cd leinetech`), nicht aus `tools/` |
| `ModuleNotFoundError: tools` | dito — `python3 tools/spec_gate.py ...`, nicht `cd tools && python3 spec_gate.py` |
| `--suite oracle` meldet schon auf dem intakten Modul rot | TODO 1 ist noch nicht (oder falsch) gefuellt; ein Score auf roter Suite ist bedeutungslos |
| `--suite frozen` liefert 0/34 | `FROZEN` ist leer — TODO 2 traegt die Tabelle ein |
| Gate meldet Befunde auf `api/app.py` | eine der beiden Fallen: Aufrufverfolgung (404 in `_require`) oder `FRAMEWORK_CODES` (400/422) |
| Gate meldet 0 Befunde auf `drifted_server.py` | TODOs noch leer — `gate()` gibt eine leere Liste zurueck |
| `python` statt `python3` findet nichts | in diesem Lab immer `python3` verwenden |
| pytest fehlt | wird nicht gebraucht. Alle Zahlen kommen aus `tools/mutation_dojo.py` und `tools/spec_gate.py` |
| Musterloesung | `labs/loesung/` — erst nach dem Lab. **Vor dem Push an die Studierenden verschieben oder loeschen.** |
