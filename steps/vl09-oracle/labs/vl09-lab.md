# Lab VL 9: Orakel und Spec-Driven Development

**Leitfrage:** Woher weiß ein Prüfer, was richtig ist, wenn KI den Code schreibt?

**Ziel:** In Teil 1 messt ihr an eurem eigenen Triage-Modul, dass eine grüne
Test-Suite fast nichts prüft. Ihr findet heraus, warum: Die Erwartung kommt aus
dem Code, den der Test prüfen soll. In Teil 2 dreht ihr den Spieß um. Ihr baut
ein Feature spec-first mit dem Coding-Agenten **opencode**. Der Agent entwirft
Spec und Plan, ihr seid das Review-Gate an jedem Übergang, der Agent
implementiert. Am Ende prüft ihr das Ergebnis mit drei Werkzeugen, die
verschiedene Dinge sehen, und vergleicht, wofür jedes davon blind ist.

Die Anleitung ist zum Nacharbeiten gedacht. Alle Befehle und erwarteten
Ausgaben stehen hier, die Aufholpunkte für Teil 1 ebenfalls. **Aufholpunkte und
Lösungen für Teil 2 stehen absichtlich nicht im Repo.** In Teil 2 durchsucht der
Agent das Repo und fände sie sonst. `vl09-loesungen.md` ist Dozenten-Material und
liegt nicht im Repo. Der Dozent zeigt Aufholpunkte und Auflösungen an den
Zeitchecks am Beamer.

## Lernziele

Nach dem Lab könnt ihr …

1. den Mutation Score einer Test-Suite messen und erklären, warum ein Test,
   der seine Erwartung aus dem Prüfling liest, kein Orakel ist.
2. eine eingefrorene Erwartung als unabhängiges Orakel schreiben und
   begründen, wann DRY beim Testen falsch ist.
3. eine Kontext-Datei (`AGENTS.md`) für das Repo entwerfen und jede Zeile mit
   dem Lackmustest aus der Vorlesung begründen.
4. ein Feature spec-first mit einem Coding-Agenten bauen und dabei Spec und
   Plan reviewen, bevor Code entsteht.
5. an konkreten Fehlern begründen, welcher Prüfer (Offline-Tests, statisches
   Gate, Contract-Test, Mensch mit Soll) was sieht und wofür er blind ist.

## Voraussetzungen

- [ ] Kurs-Repo `leinetech` geklont. Dieses Lab startet auf dem
      Checkpoint-Branch **`vl09-oracle`** (Befehle in Schritt 0).
- [ ] Python 3.12 oder 3.13 wie in VL 1 (`python3 --version`).
- [ ] Für Teil 2: das venv aus den früheren Vorlesungen (`.venv`) mit den
      Paketen aus `requirements.txt` **dieses** Branches. Neu sind fastapi,
      uvicorn, schemathesis, email-validator und pytest-cov. Bitte vor dem
      Termin installieren, das spart im Lab 10 Minuten.
- [ ] Für Teil 2: opencode installiert (`opencode --version`) und eingerichtet
      (Schritt 0). Installation: [opencode.ai/docs](https://opencode.ai/docs/).
- [ ] Für Teil 2: euer persönlicher HomeCloud-Key. Er funktioniert **nur
      montags 06:00 bis 23:59** (Europe/Berlin).
- [ ] Aus der Vorlesung: Orakel, Mutation Score, der Vier-Schritt von
      Spec-Driven Development, EARS, Kontext-Dateien mit Lackmustest.

Ohne Agent oder Key könnt ihr trotzdem alles machen. Teil 1 braucht weder
Installation noch Netz. Für Teil 2 gibt es in Aufgabe D und E einen Weg von
Hand.

## Zeitplan (90 Minuten)

| Schritt | Inhalt | Minuten | Uhr im Lab |
|---|---|---|---|
| 0 | Setup und Smoke-Tests | 8 | 0:00 bis 0:08 |
| A | Teil 1: Werkzeug kennenlernen | 5 | 0:08 bis 0:13 |
| B | Teil 1: die naheliegende Refaktorierung | 10 | 0:13 bis 0:23 |
| C | Teil 1: eine Zeile Unterschied | 8 | 0:23 bis 0:31 |
| Brücke | Teil 1: Unit-Test gegen Spec-Test | 2 | 0:31 bis 0:33 |
| D0 | Teil 2: Kontext zuerst (`AGENTS.md`) | 7 | 0:33 bis 0:40 |
| D | Teil 2: Specify, der Agent entwirft die Spec | 13 | 0:40 bis 0:53 |
| E | Teil 2: Plan prüfen, dann implementieren | 13 | 0:53 bis 1:06 |
| F | Teil 2: dreifach prüfen | 14 | 1:06 bis 1:20 |
| Abschluss | Prüfer-Matrix, zwei Zahlen und ein Satz | 10 | 1:20 bis 1:30 |

Drei Zeitchecks helfen euch beim Aufholen: **0:33** Teil 1 ist fertig.
**0:53** Die Spec ist freigegeben. **1:06** Der Handler ist implementiert. Wer
an einem Zeitcheck hinten liegt, übernimmt den Aufholpunkt der jeweiligen
Aufgabe und macht mit der nächsten weiter. Für Teil 1 steht er hier
eingeklappt, für Teil 2 zeigt ihn der Dozent am Beamer.

---

## Schritt 0: Setup (8 min)

**Branch holen.** Habt ihr aus VL 8 noch lokale Änderungen, sichert sie zuerst.
Das `-u` nimmt auch ungetrackte Dateien mit, etwa das in VL 8 per `cp` angelegte
`src/agent.py`. Ohne `-u` bricht der Checkout ab, weil `vl09-oracle` diese Datei
enthält. Zurück an euren alten Stand kommt ihr später mit
`git checkout <alter-branch>` und `git stash pop`.

```bash
cd leinetech
git status                          # zeigt lokale Änderungen aus VL 8
git stash push -u -m "stand-vl08"   # nur nötig, wenn git status Änderungen zeigt
git fetch origin
git checkout vl09-oracle
python3 --version                   # 3.12 oder 3.13
```

**Smoke-Tests für Teil 1** (ohne Installation, ohne Netz):

```bash
python3 tools/mutation_dojo.py --suite shipped
python3 tools/mutation_dojo.py --tests tests/test_openapi_spec.py
```

Erwartete Ausgabe (gekürzt):

```text
Suite 'shipped' · Mutantenklasse: ein Keyword löschen (Scope: category)
  auf dem intakten Modul : grün
  Mutanten               : 34
  eliminiert             : 4
  ...
tests/test_openapi_spec.py: 4/4 grün, 0 rot, 0 leer
```

**Smoke-Tests für Teil 2** (venv und opencode):

```bash
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt     # nur, falls noch nicht geschehen
python3 -c "import fastapi, uvicorn, schemathesis" && echo "venv ok"
opencode --version
```

**opencode einrichten.** Die Datei `~/.config/opencode/opencode.json` liest den
Key aus einer Umgebungsvariable. So steht er in keiner Datei im Klartext.

```jsonc
// ~/.config/opencode/opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "homecloud/qwen3.6-35B-A3B-FP8",
  "provider": {
    "homecloud": {
      "npm": "@ai-sdk/openai-compatible",
      "options": {
        "baseURL": "https://llm.homecloud.ee/v1",
        "apiKey": "{env:HOMECLOUD_API_KEY}"
      },
      "models": {
        "qwen3.6-35B-A3B-FP8": { "limit": { "context": 131072, "output": 8192 } }
      }
    }
  }
}
```

```bash
export HOMECLOUD_API_KEY="<euer-key>"   # im Terminal, in dem ihr opencode startet
```

Details zum Kurs-Endpunkt stehen in [`SETUP.md`](../SETUP.md).

> **Achtung:** Der Key funktioniert nur montags 06:00 bis 23:59. Die erste
> Antwort kann 200 bis 300 Sekunden dauern (Kaltstart), danach geht es schnell.
> Prompts werden geloggt. Gebt deshalb keine Secrets und keine echten
> Personendaten ein.

**Modell aufwärmen.** Schickt im selben Terminal sofort einen ersten Aufruf ab.
Er darf dauern. Währenddessen arbeitet ihr in einem zweiten Terminal an Teil 1.

```bash
opencode run --agent plan "Antworte nur mit OK"
```

Kommt eine kurze Antwort, funktionieren Key und Config, und der Kaltstart liegt
hinter euch. In Aufgabe D antwortet der Agent dann ohne lange Wartezeit. Der
Dozent schickt zu Lab-Beginn ebenfalls einen Aufruf ab.

**✓ Checkpoint Setup:** Beide Dojo-Aufrufe zeigen die Ausgabe oben. Für Teil 2
meldet Python `venv ok`, `opencode --version` zeigt eine Versionsnummer, und
der Aufwärm-Aufruf läuft oder hat schon geantwortet. Wenn nicht:
[Troubleshooting](#troubleshooting).

---

## Teil 1: Das Orakel (25 min)

[`src/triage.py`](../src/triage.py) ordnet Tickets per Keyword-Listen ein. Das
ganze Verhalten steckt in zwei dicts: `CATEGORY_KEYWORDS` und
`PRIORITY_KEYWORDS`. [`tests/test_triage.py`](../tests/test_triage.py) hat
5 Tests, alle grün, mit 96 % Zeilen-Coverage.

Die Mutantenklasse heute: **ein Keyword aus einer Liste löschen.** Der
Mutation-Dojo setzt jeden Mutanten nur im Speicher und verändert keine Datei.

### Aufgabe A: Das Werkzeug kennenlernen (5 min)

```bash
python3 tools/mutation_dojo.py --list
python3 tools/mutation_dojo.py --suite shipped
```

`--list` zeigt die 34 Mutanten (`M01` bis `M34`). `--suite shipped` misst die
ausgelieferte Suite. Erwartete Ausgabe:

```text
Suite 'shipped' · Mutantenklasse: ein Keyword löschen (Scope: category)
  auf dem intakten Modul : grün
  Mutanten               : 34
  eliminiert             : 4
  überlebt               : 30
  Mutation Score (roh)   : 4/34 = 0.118
  eliminiert im Detail   : Hardware/drucker, Hardware/laptop, Netzwerk/vpn, Zugang/zugriff
```

In der Vorlesung lief dieselbe Messung mit `--scope all` (45 Mutanten, 5
eliminiert). Das ist ein anderer Nenner und deshalb ein anderer Score. Ein
Score ohne Mutantenklasse und Nenner ist bedeutungslos.

**Überlegt kurz:** Was haben genau diese vier Keywords gemeinsam?

<details>
<summary>Antwort</summary>

Sie sind die einzigen Keywords, die für eine Assertion **allein entscheidend**
sind. Wörtlich in den Testtexten stehen acht. Aber `rechnung` und `kosten`
stehen im selben Ticket und decken sich gegenseitig: Löscht man eins, matcht
das andere weiter. `wlan` und `lan` stehen in einem Ticket, dessen Kategorie
`Zugang` schon durch `zugriff` entschieden wird (first match wins). Coverage
kann das nicht unterscheiden. Die Keyword-Listen sind Daten, die beim Import
ausgeführt werden. Für Coverage ist jedes Keyword „abgedeckt“, auch wenn kein
Test es prüft.
</details>

### Aufgabe B: Die naheliegende Refaktorierung (10 min)

Öffnet [`tests/test_triage_oracle.py`](../tests/test_triage_oracle.py).
**TODO 1** dort ist der Test, den man in jedem Review vorschlagen würde: keine
Magic Strings, eine Schleife über `CATEGORY_KEYWORDS`.

**Bevor ihr ihn schreibt, schätzt im Chat:** Der neue Test prüft alle 34
Keywords statt 5 handgeschriebener Fälle. Wie viele der 34 Mutanten wird er
eliminieren?

Probiert vorher einmal den leeren Zustand:

```bash
python3 tools/mutation_dojo.py --suite oracle
```

```text
Suite 'oracle' kann noch nicht gemessen werden:
  TODO 1 ist noch nicht gefüllt: test_jedes_keyword_trifft_seine_kategorie()
  ...
```

> **Dieselbe Falle im Werkzeug:** `python3 -m pytest tests/test_triage_oracle.py`
> meldet jetzt „3 passed“, obwohl alle drei Tests leer sind. Ein Test ohne
> Assertion besteht immer. Der Dojo prüft deshalb den Quelltext und meldet
> „leer“ statt „grün“.

Schreibt jetzt TODO 1 und messt erneut:

```bash
python3 tools/mutation_dojo.py --suite oracle
```

**Notiert die Zahl, bevor ihr weiterlest.** Vergleicht sie mit eurer Schätzung.

<details>
<summary>Erwartetes Ergebnis und Erklärung</summary>

```text
  Mutanten               : 34
  eliminiert             : 0
  überlebt               : 34
  Mutation Score (roh)   : 0/34 = 0.000
```

Der Score geht **runter**, nicht rauf. Der Test importiert seine Erwartung aus
dem Modul, das er prüft. Löscht der Mutant ein Keyword, verschwindet der
zugehörige Testfall **mitsamt der Erwartung**. Es bleibt nichts, was
fehlschlagen könnte. Das ist die Orakel-Falle aus der Vorlesung mit einem
Orakel, das sich mitbewegt.

Vergleicht mit dem ACH-Filter aus der Theorie: Ein Test taugt nur, wenn er auf
dem Mutanten FEHLSCHLÄGT **und** auf dem Original BESTEHT. Diese Suite erfüllt
nur die zweite Hälfte.
</details>

<details>
<summary>Aufholpunkt: TODO 1</summary>

```python
def test_jedes_keyword_trifft_seine_kategorie():
    for kategorie, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            assert classify_and_prioritize(_ticket(keyword, keyword))[0] == kategorie
```
</details>

### Aufgabe C: Eine Zeile Unterschied (8 min)

**TODO 2** in derselben Datei: derselbe Test, aber die Erwartung steht als
eingefrorene Kopie `FROZEN` **in der Testdatei**. Schreibt `FROZEN` als
ausgeschriebenes Literal. Ihr dürft die Listen aus `src/triage.py` kopieren.
Leitet sie aber nicht per Code aus `CATEGORY_KEYWORDS` ab. Eine Ableitung wäre
dasselbe mitwandernde Orakel wie in TODO 1, nur besser getarnt. Der Dojo zeigt
das auch: Mit `FROZEN = {k: tuple(v) for k, v in CATEGORY_KEYWORDS.items()}`
meldet `--suite frozen` 0 von 34, weil er die Testdatei pro Mutant neu lädt.

```bash
python3 tools/mutation_dojo.py --suite frozen
```

Erwartete Ausgabe (gekürzt):

```text
  Mutanten               : 34
  eliminiert             : 26
  überlebt               : 8
  Mutation Score (roh)   : 26/34 = 0.765
```

Ja, das dupliziert Daten. **Schreibt als Kommentar über `FROZEN`, warum das hier
richtig ist und wofür die Kopie blind bleibt.** DRY gilt für Produktionscode,
nicht für Orakel.

<details>
<summary>Wofür bleibt FROZEN blind? (Tipp: T-1004 und „solange“)</summary>

`FROZEN` friert das Ist ein. Es fängt jede Änderung an den Keyword-Listen, aber
keinen Fehler, der schon im Original steckt. Das Keyword `lan` trifft zum
Beispiel auch „solange“ in T-1004. Das fällt heute nur nicht auf, weil `passwort`
vorher greift. Für ein Refactoring ist das eingefrorene Ist genau das richtige
Soll, für ein neues Feature nicht.
</details>

Welche 8 Mutanten überleben, und ist das eure Schuld? Der Dojo sucht für jeden
Mutanten eine Eingabe, die Original und Mutant unterscheidet:

```bash
python3 tools/mutation_dojo.py --equivalence alle
```

```text
Äquivalenz-Suche für alle 34 Mutanten (Scope: category), je 1041 Kandidaten
  ohne unterscheidende Eingabe : 8
    Netzwerk/wlan
    Software/absturz
    ...
    Software/anwendung
```

Genau die 8 Überlebenden sind Äquivalenz-Kandidaten. Das Argument dazu:
`Software` ist die letzte Kategorie **und** der Default. Ein gelöschtes
Software-Keyword landet deshalb trotzdem bei Software. Jeder Text mit `wlan`
enthält auch `lan`. Kein Test kann diese Mutanten eliminieren. Der korrigierte
Score ist 26 / (34 − 8) = **1,000**.

<details>
<summary>Aufholpunkt: TODO 2</summary>

```python
# Absichtlich dupliziert: DRY gilt für Produktionscode, nicht für Orakel.
# Diese Kopie wandert NICHT mit, wenn jemand src/triage.py ändert.
FROZEN: dict[str, tuple[str, ...]] = {
    "Abrechnung": ("rechnung", "kosten", "vertrag", "tarif", "zahlung", "buchhaltung"),
    "Zugang": ("passwort", "login", "anmelden", "konto", "gesperrt", "zugriff",
               "berechtigung"),
    "Netzwerk": ("wlan", "vpn", "internet", "netzwerk", "verbindung", "lan"),
    "Hardware": ("laptop", "drucker", "monitor", "tastatur", "maus", "docking",
                 "akku", "headset"),
    "Software": ("absturz", "fehlermeldung", "update", "installation", "lizenz",
                 "programm", "anwendung"),
}


def test_jedes_keyword_trifft_seine_kategorie_eingefroren():
    for kategorie, keywords in FROZEN.items():
        for keyword in keywords:
            assert classify_and_prioritize(_ticket(keyword, keyword))[0] == kategorie
```
</details>

### Die Brücke zu Teil 2 (2 min)

Jetzt löscht der Mutant nicht ein Keyword, sondern den ganzen **Schlüssel**
`"Software"`:

```bash
python3 tools/mutation_dojo.py --bruecke
```

Erwartete Ausgabe (gekürzt):

```text
  nachher, mit Mutant:
    tests/test_triage.py             5/5 grün
    tests/test_openapi_spec.py       3/4 ROT
      fehlgeschlagen: test_kategorie_enum_passt_zu_triage_regeln
  ...
    list(CATEGORY_KEYWORDS) = ['Abrechnung', 'Zugang', 'Netzwerk', 'Hardware']
```

[`tests/test_triage.py`](../tests/test_triage.py) bleibt grün, weil
`DEFAULT_CATEGORY` alles auffängt. Der Rückgabewert der Triage ändert sich nie.
[`tests/test_openapi_spec.py`](../tests/test_openapi_spec.py) wird rot. Er
vergleicht das `Kategorie`-Enum der Spec mit `CATEGORY_KEYWORDS`. Der
Unterschied zwischen den beiden Dateien ist nicht Sorgfalt, sondern **der Ort
ihrer Erwartung**.

Ist der rote Spec-Test ein Fehlalarm? Nein. Für den Rückgabewert der Triage ist
der Mutant äquivalent, für das System nicht. `src/summarize.py` bietet dem LLM
nur noch vier Kategorien an, und `api/app.py` startet nicht mehr. Äquivalenz
gilt immer relativ zu dem, was ein Prüfer beobachtet.

> **Merke:** Eine maschinenlesbare Spec ist ein Orakel, das außerhalb des Codes
> liegt, den es beurteilt. Genau dieses Orakel arbeitet in Teil 2 für euch.

**⏱ Zeitcheck 0:33:** Teil 1 ist fertig. Hängt ihr noch in C, nehmt den
Aufholpunkt und geht weiter.

---

## Teil 2: Spec-Driven Feature mit opencode (47 min)

Der Ablauf ist der Vier-Schritt aus der Vorlesung auf Lab-Größe:

> **Specify** (Aufgabe D: Der Agent entwirft die Spec, ihr reviewt) →
> **Plan** (Aufgabe E: Der Agent plant, ihr reviewt) → **Implement**
> (Aufgabe E: Der Agent setzt den freigegebenen Plan um) → **Prüfen**
> (Aufgabe F: drei Werkzeuge statt eines vierten Agent-Schritts).
> Den Schritt `Tasks` lassen wir weg, denn ein Endpunkt ist genau ein Task.
> An jedem Übergang steht ihr. **Der Agent bekommt nie den Gesamtauftrag.**

Die Rollen der Dateien:

| Datei | Rolle |
|---|---|
| [`api/openapi.yaml`](../api/openapi.yaml) | **Single Source of Truth.** Hier beginnt das Feature. |
| [`api/app.py`](../api/app.py) | Referenz-Server (FastAPI), spec-konform. Hier landet der neue Code. |
| [`api/drifted_server.py`](../api/drifted_server.py) | weicht absichtlich ab. Der Docstring listet alle Abweichungen. |
| [`tools/spec_gate.py`](../tools/spec_gate.py) | **fertiges** statisches Gate. Liest die Spec mit [`tools/specyaml.py`](../tools/specyaml.py) und den Server per `ast`, ohne ihn zu starten. |

Das Abnahme-Kriterium des Gates ist **zweiseitig**. Merkt euch die Zahlen:

```bash
python3 tools/spec_gate.py --check
```

```text
Abnahme-Kriterium (beide Zeilen müssen OK sein):
  grün auf api/app.py             : 0 Befund(e)  OK
  rot   auf api/drifted_server.py : 7 Befund(e)  OK

BESTANDEN
```

Ein Gate, das immer rot ist, ist von einem funktionierenden nicht zu
unterscheiden. Ein Gate, das immer grün ist, auch nicht.

### Aufgabe D0: Kontext zuerst (7 min)

Schreibt eine `AGENTS.md` für dieses Repo, **höchstens 15 Regelzeilen**
(Überschriften zählen nicht). opencode liest `AGENTS.md` im Repo-Wurzelverzeichnis
automatisch. Schreibt sie selbst und nicht mit `/init`. Es geht um eure Entscheidungen, nicht um eine
Zusammenfassung des Repos. Gliedert entlang der fünf Kategorien aus der
Vorlesung:

1. **Kommandos, die eine Änderung beweisen** (exakt und kopierbar)
2. **Grenzen**, die der Agent nicht erraten kann
3. **Konventionen**, aber nur die abweichenden
4. **Security und Commits**
5. **Ein bekannter Stolperstein**

Prüft jede Zeile mit dem Lackmustest: Würde ohne diese Zeile jemand die falsche
Datei, das falsche Kommando oder die falsche Grenze wählen? Wenn nein, streichen.

Eine Grenze bekommt ihr geschenkt, sie gehört in jede Datei:
`labs/ nicht lesen, das ist die Lab-Anleitung.` Sie besteht den Lackmustest.
Ohne sie liest der Agent die Aufgabe mit, die ihr gerade prüfen wollt.
Zusätzlich blendet die Datei `.ignore` im Repo den Ordner `labs/` für die
Such-Werkzeuge von opencode aus. Ein direkter Lesezugriff bleibt trotzdem
möglich, deshalb beides.

**Mini-Experiment:** Gruppen mit gerader Nummer speichern die Datei jetzt als
`AGENTS.md` im Repo-Wurzelverzeichnis. Gruppen mit ungerader Nummer speichern
sie als `labs/AGENTS.entwurf.md` (dort sucht der Agent nicht) und verschieben
sie erst nach Aufgabe E als `AGENTS.md` ins Wurzelverzeichnis. In Aufgabe E
zählt jede Gruppe, wie viele der vier Prüffragen der Plan des Agenten **ohne
Nachbessern** erfüllt. Wer allein nacharbeitet, wählt eine Variante und
probiert die andere später (Für zu Hause, Nr. 6).

Erst danach vergleichen: [`labs/AGENTS.beispiel.md`](AGENTS.beispiel.md) ist
eine mögliche Lösung.

### Aufgabe D: Specify, der Agent entwirft, ihr entscheidet (13 min)

**Das Feature kommt als Auftrag, nicht als YAML.** Startet opencode im
Repo-Wurzelverzeichnis (`opencode`) und wechselt mit **Tab** in den
**Plan-Modus**. Dort liest der Agent frei, fragt aber vor jeder Dateiänderung
und vor jedem Shell-Befehl nach. **Lehnt diese Rückfragen in Aufgabe D ab.** Wer
aus Gewohnheit zustimmt, lässt ihn schreiben. Dann:

```text
Wir erweitern die LeineTech Ticket-API spec-first. Feature-Wunsch:
"Als Teamlead möchte ich auf einen Blick sehen, wie viele Tickets in
jeder Kategorie und jeder Priorität liegen, um Engpässe zu erkennen."

Entwirf NUR die Änderung an api/openapi.yaml, noch keinen Code:
ein neuer GET-Endpunkt /tickets/stats. Übernimm Stil und Konventionen
der bestehenden Spec (operationId, tags, $ref auf ein Schema namens
StatistikReport unter components). Zeige das YAML als Entwurf und
begründe jede Entscheidung in einem Satz. Ändere noch keine Datei.
Lies nichts unter labs/, das ist die Lab-Anleitung.
```

**Während der Agent antwortet** (ohne Aufwärmen in Schritt 0 bis zu 5 Minuten):
Lest den Modul-Docstring und den Docstring von `gate()` in
[`tools/spec_gate.py`](../tools/spec_gate.py). Zwei Entscheidungen darin
braucht ihr gleich. (1) Das Gate verfolgt Aufrufe von Hilfsfunktionen
(`_raised_status_codes()`), weil `app.py` den 404 in `_require()` erhebt und
nicht im Handler. (2) `FRAMEWORK_CODES = {400, 422}` sind ausgenommen, weil
FastAPI sie selbst erzeugt. Sie zu fordern, würde den korrekten Server
anschwärzen. Ein Gate ist nie neutral: Jemand hat entschieden, was es sieht.

**Jetzt seid ihr das Review-Gate.** Checkliste gegen den Entwurf:

- [ ] `operationId` vorhanden? ([`tests/test_openapi_spec.py`](../tests/test_openapi_spec.py) erzwingt sie.)
- [ ] `$ref` auf ein Schema `StatistikReport` unter `components`, kein Inline-Schema?
- [ ] **Blockstil wie der Rest der Datei?** Flow-Maps wie `{ type: integer }`
      versteht [`specyaml.py`](../tools/specyaml.py) nicht. Gate und Tests
      brechen dann mit `SpecYamlFehler` und Zeilennummer ab. Inline-Listen wie
      `tags: [tickets]` sind erlaubt.
- [ ] Nichts erfunden? Keine Query-Parameter, keine weiteren Endpunkte, kein
      404 (der Endpunkt hat keinen Pfad-Parameter).
- [ ] **Feldnamen wie im restlichen Lab:** `StatistikReport` hat genau drei
      Felder, `gesamt` (integer), `kategorien` (object) und `prioritaeten`
      (object). Die Prüfschritte in Aufgabe F rechnen mit diesen Namen.
- [ ] **Die Regel, die der Agent nicht erraten kann:** Auch eine Kategorie mit
      **0 Tickets** muss als Schlüssel in der Antwort stehen. Sonst kann kein
      Dashboard sie anzeigen. Dasselbe gilt für die Prioritäten. Formuliert
      die Regel zuerst als EARS-Satz (WHEN … THE SYSTEM SHALL …) und übersetzt
      dann das SHALL in die Spec. Die übrigen Schemas in
      [`api/openapi.yaml`](../api/openapi.yaml) zeigen, wie ein Feld zur
      Pflicht wird und eine Untergrenze bekommt. Diese Geschäftsregel stand
      nicht im Feature-Wunsch. Sie kommt von euch. Lasst den Agenten
      nachbessern.

Erst wenn die Checkliste erfüllt ist: Freigabe geben und die Datei ändern
lassen (Tab zurück in den Build-Modus) oder das YAML von Hand übernehmen.

> **Warum das Review nicht optional ist:** In Teil 1 war der Test wertlos,
> dessen Erwartung aus dem Prüfling kam. Eine Spec, die derselbe Agent
> geschrieben hat, der gleich implementiert, und die niemand geprüft hat, wäre
> **dieselbe Falle eine Etage höher**: ein mitwanderndes Orakel. Erst euer
> Review macht den Entwurf zum Vertrag.

**Abnahme von Aufgabe D:**

```bash
python3 tools/mutation_dojo.py --tests tests/test_openapi_spec.py   # 4/4 grün
python3 tools/spec_gate.py api/app.py
```

```text
=== app.py: 1 Befund(e) ===
    ROUTE    GET /tickets/stats                     in der Implementierung nicht vorhanden
```

Dieser eine Befund ist der Punkt von Spec-first: **Das Gate ist jetzt die
Aufgabenbeschreibung.** Rot beginnt beim Gate, nicht beim Bugreport.

`python3 tools/spec_gate.py --check` meldet zwischen Aufgabe D und E absichtlich
`NICHT BESTANDEN`. Es misst das Endergebnis, nicht den Zwischenstand, und sagt
das auch:

```text
  grün auf api/app.py             : 1 Befund(e)  FEHLT: Befunde auf der Referenz
  rot   auf api/drifted_server.py : 8 Befund(e)  OK
  ...
  Nach Lab-Aufgabe D (Spec erweitert, Handler fehlt noch) ist genau
  1 ROUTE-Befund erwartet.
```

**Aufholpunkt:** Die fertige Spec-Erweiterung und den EARS-Satz zeigt der
Dozent am Zeitcheck 0:53 am Beamer.

**⏱ Zeitcheck 0:53:** Die Spec ist freigegeben. Wer noch nicht so weit ist,
übernimmt jetzt den Aufholpunkt.

### Aufgabe E: Plan prüfen, dann implementieren lassen (13 min)

**Erst der Plan, immer noch kein Code** (Plan-Modus):

```text
Die Spec deklariert jetzt GET /tickets/stats mit dem Schema
StatistikReport. Schreibe einen Umsetzungsplan für api/app.py in
maximal 10 Zeilen, noch keinen Code:
1. welche vorhandenen Module und Objekte du wiederverwendest,
2. wo in der Datei der neue Handler stehen muss und warum,
3. wie du das Ergebnis verifizierst.
```

**Plan-Review mit vier Prüffragen, je 30 Sekunden:**

1. Nennt er `_STORE` und `src.triage.classify_and_prioritize`, oder erfindet er
   eine eigene Datenhaltung? ([`src/stats.py`](../src/stats.py) enthält schon
   Zähl-Logik, gibt aber nur Text aus. Findet er sie?)
2. Plant er ein Pydantic-Modell mit `response_model` wie bei den übrigen
   Endpunkten? Ohne `response_model` prüft das Gate das Response-Schema stumm
   gar nicht.
3. Sagt er etwas Belastbares zur **Position** des Handlers in der Datei? Wenn
   nein: **nicht einsagen, nur notieren.** Aufgabe F kommt darauf zurück.
4. Steht echte Verifikation drin (`spec_gate.py`, pytest) oder nur „sieht dann
   gut aus“?

Notiert für das Mini-Experiment, wie viele der vier Fragen der Plan ohne
Nachbessern erfüllt. Fehlt Punkt 1, 2 oder 4, gebt den Plan zurück. Das ist der
zweite Review-Übergang, und er ist billiger als jedes Code-Review danach.

**Dann erst Implement** (Tab in den Build-Modus):

```text
Setz deinen Plan um. Ändere nur api/app.py, halte dich exakt an die
Spec, erfinde nichts dazu. Prüfe dein Ergebnis mit:
python3 tools/spec_gate.py api/app.py
```

**Danach den Diff lesen, bevor ihr validiert** (`git diff api/app.py`). Ihr seid
Auftraggeber und Prüfer, nicht Zuschauer. Notiert für den Abschluss: Was hat der
Agent stillschweigend entschieden, das weder in der Spec noch im Plan stand?

**Abnahme von Aufgabe E:**

```bash
python3 tools/spec_gate.py --check
```

```text
Abnahme-Kriterium (beide Zeilen müssen OK sein):
  grün auf api/app.py             : 0 Befund(e)  OK
  rot   auf api/drifted_server.py : 8 Befund(e)  OK

BESTANDEN
```

Der Drift-Server hat jetzt 8 Befunde: die 7 von vorher und euer neues Feature,
das dort fehlt.

> **Falls HomeCloud klemmt** (Zeitfenster, Kaltstart, Ausfall): Spec entlang der
> Checkliste aus Aufgabe D von Hand schreiben und den Endpunkt von Hand bauen.
> Es sind rund 15 Zeilen. Die Prüfung in Aufgabe F ist genau dieselbe. Das Lab
> hängt nicht am Agenten.

**Aufholpunkt:** Modell und Handler zeigt der Dozent am Zeitcheck 1:06 am
Beamer.

**⏱ Zeitcheck 1:06:** Der Handler ist implementiert, und `--check` ist grün.

### Aufgabe F: Dreifach prüfen (14 min)

Jetzt gilt das Muster des Tages: **stochastischer Generator, deterministische
Prüfer.** Drei Prüfer sehen verschiedene Dinge. F.1 bis F.3 machen alle. In F.4
bekommt jede Gruppe eine eigene Provokation und trägt das Ergebnis im Abschluss
in die Prüfer-Matrix ein.

**F.1 Das statische Gate** (Routen, Statuscodes, Query-Parameter, Feldnamen)

Das Gate prüft Response-Felder gegen `SPEC_RESPONSE_FIELDS` in
[`tools/spec_gate.py`](../tools/spec_gate.py). Schemas, die dort fehlen, prüft
es **stumm gar nicht**. Tragt die Zeile nach:

```python
    "StatistikReport": {"gesamt", "kategorien", "prioritaeten"},
```

`--check` bleibt bei 0 und 8. Eine korrekte Implementierung besteht mit und
ohne Eintrag. Dass der Eintrag trotzdem etwas tut, zeigt ihr in zwei Zeilen.
Benennt im Pydantic-Modell `gesamt` testweise in `total` um:

```bash
python3 tools/spec_gate.py api/app.py
```

```text
=== app.py: 1 Befund(e) ===
    SCHEMA   GET /tickets/stats                     Response-Felder ['kategorien', 'prioritaeten', 'total'] != Spec ['gesamt', 'kategorien', 'prioritaeten']
```

Ohne den Eintrag hätte das Gate hier 0 Befunde gemeldet. Benennt das Feld
zurück. Ein von Hand gepflegtes Orakel ignoriert lautlos, was es nicht kennt.

**F.2 Die Offline-Tests** (Spec in sich stimmig, Triage unverändert)

```bash
python3 -m pytest tests/test_openapi_spec.py tests/test_triage.py -q
```

Erwartet: `9 passed`.

**F.3 Der Contract-Test gegen den laufenden Server** (Verhalten)

Schemathesis erzeugt aus der Spec Hunderte Requests und prüft jede Antwort
gegen die Spec. Seit Schemathesis 4.0 laufen dabei auch Negativtests mit
ungültigen Eingaben (`--mode all` ist der Default, wir schreiben es aus).

```bash
# Terminal 1: Server starten. --reload lädt Änderungen an app.py automatisch.
python3 -m uvicorn api.app:app --reload

# Terminal 2: im selben Repo, venv aktiv
curl -s http://localhost:8000/tickets/stats
schemathesis run api/openapi.yaml --url http://localhost:8000 --checks all --mode all
```

Erwartete Antwort von `curl` (mit den 30 ausgelieferten Tickets):

```text
{"gesamt":30,"kategorien":{"Abrechnung":6,"Zugang":6,"Netzwerk":5,"Hardware":5,"Software":8},"prioritaeten":{"hoch":7,"mittel":18,"niedrig":5}}
```

Ohne `curl` geht es im Browser: `http://localhost:8000/tickets/stats` oder die
interaktive Doku unter `http://localhost:8000/docs`. Meldet Schemathesis auf
`app.py` einen Befund, lest ihn genau: Er ist entweder ein Fehler in eurem
Handler oder eine Lücke in der Spec. Ein bekannter Kandidat für die zweite Sorte
ist `POST /tickets` mit 422 (siehe [Troubleshooting](#troubleshooting)). Er hat
mit eurem Feature nichts zu tun.

**F.4 Gruppenpuzzle: je eine Provokation** (Server aus F.3 läuft weiter)

| Gruppe | Provokation | Beobachten | Danach |
|---|---|---|---|
| A | Handler testweise **hinter** `get_ticket` verschieben | `curl` auf `/tickets/stats` und `spec_gate.py api/app.py` | zurückschieben |
| B | Zeile `_STORE: dict[str, dict] = {t["id"]: t for t in load_tickets()}` testweise durch `_STORE: dict[str, dict] = {}` ersetzen | `curl` auf `/tickets/stats` | zurücksetzen |
| C | In der Spec die 0-Tickets-Regel für die Kategorie `Software` wieder entfernen (so sah vermutlich der erste Entwurf des Agenten aus) | `spec_gate.py --check`, Tests aus F.2, Schemathesis | zurücksetzen |

Notiert für den Abschluss: Welcher Prüfer hat angeschlagen, welcher nicht, und
warum? Die Auflösung für alle drei Gruppen bespricht der Dozent im Abschluss.

**Demo am Beamer** (zum Nacharbeiten selbst ausführen): derselbe Contract-Test
gegen den Drift-Server.

```bash
python3 -m uvicorn api.drifted_server:app --port 8001
schemathesis run api/openapi.yaml --url http://localhost:8001 --checks all --mode all
```

Wenn alle drei Prüfer grün sind, ist das Feature gegen die Spec geprüft. Nicht
„sieht gut aus“, nicht „lief bei mir“. Das ist der Unterschied zwischen Vibe
Coding und Spec-Driven Development. Beweisen kann ein Test nichts, er findet
nur Gegenbeispiele. Deshalb zählt, dass die drei Prüfer verschiedene
Gegenbeispiele suchen.

---

## Abschluss (10 min)

### Die Prüfer-Matrix

Jede Zeile ist ein Fehler aus Vorlesung oder Lab. Füllt gemeinsam aus, welcher
Prüfer ihn sieht (✓) und welcher nicht (✗). Die Gruppen aus F.4 bringen ihre
Zeile mit.

| Fehler | Offline-Tests | Gate | Schemathesis | Mensch mit Soll |
|---|---|---|---|---|
| `passwort` aus `Zugang` gelöscht (Hook der Vorlesung) | | | | |
| Schlüssel `Software` gelöscht (Brücke) | | | | |
| Drift: `/health` steht nicht in der Spec | | | | |
| Drift: 400 statt 404 bei unbekannter ID | | | | |
| Handler `stats` hinter `get_ticket` (Gruppe A) | | | | |
| 0-Tickets-Regel fehlt in der Spec (Gruppe C) | | | | |

„Mensch mit Soll“ heißt: jemand, der die eigene Aufgabe und ihr Soll kennt und
die eigenen Artefakte reviewt oder den eigenen Endpunkt aufruft. Die erwartete
Lösung mit Begründung je Zelle zeigt der Dozent im Plenum am Beamer.

### Zwei Zahlen und ein Satz (Chat)

1. Euer Score aus `--suite frozen` (roh und korrigiert).
2. Die Befunde des Gates auf `drifted_server.py` nach eurem Feature (8) und auf
   `app.py` (0).
3. **Ein Befund, den nur einer der Prüfer finden konnte, und warum die anderen
   strukturell blind dafür sind.**

Dazu aus dem Mini-Experiment: mit oder ohne `AGENTS.md`, und wie viele der vier
Prüffragen der Plan ohne Nachbessern erfüllt hat.

### Die Antwort auf die Leitfrage

1. Ein Orakel muss **außerhalb des Prüflings** liegen: Golden Dataset, `FROZEN`,
   die Spec.
2. **Maschinenlesbar** macht es billig, wiederholbar und CI-fähig. Das ist das
   eigentliche Argument für Spec-Driven Development.
3. **Was in keinem Artefakt steht, prüft keine Maschine.** Deshalb bleibt der
   Mensch an jedem Übergang Prüfer.

## Reflexionsfragen

1. Wann ist DRY beim Testen falsch?
2. Was findet das statische Gate, was Schemathesis nicht findet, und umgekehrt?
3. Was musste euer Review an Spec-Entwurf oder Plan korrigieren? Hätte der
   Agent das wissen können?
4. Welche Stufe der Eskalationsleiter waren eure `AGENTS.md`, euer Review-Gate
   und `spec_gate.py`?
5. Welche Zeile würdet ihr jetzt in eure `AGENTS.md` ergänzen?
6. Warum ist euer Mit-und-ohne-Vergleich aus dem Mini-Experiment kein Beleg?

Antworthinweise bespricht der Dozent im Plenum.

---

## Für zu Hause und Bonus für Schnelle

1. **TODO 3 in [`tests/test_triage_oracle.py`](../tests/test_triage_oracle.py):**
   dieselbe Schleife, das Keyword steht nur im Betreff.

   ```bash
   python3 tools/mutation_dojo.py --tests tests/test_triage_oracle.py
   ```

   Erwartet: `3/3 grün`. Der Test findet nichts Neues. Warum?

   <details>
   <summary>Antwort</summary>

   `_ticket_text()` fügt Betreff und Text zu einem String zusammen. Für die
   Triage ist es egal, in welchem Feld das Keyword steht. Mehr Testfälle sind
   nicht dasselbe wie mehr Orakel. Diese Variation ändert die Eingabe entlang
   einer Dimension, auf die der Prüfling gar nicht reagiert.
   </details>

2. **Äquivalenz nachrechnen.** Der Dojo findet Kandidaten, das Argument liefert
   ihr.

   ```bash
   python3 tools/mutation_dojo.py --equivalence Netzwerk:wlan        # einer der 8
   python3 tools/mutation_dojo.py --equivalence Netzwerk:lan         # Kontrolle: eliminierbar
   python3 tools/mutation_dojo.py --equivalence Abrechnung:rechnung  # Kontrolle: eliminierbar
   python3 tools/mutation_dojo.py --equivalence niedrig:frage        # Priorität: eliminierbar
   python3 tools/mutation_dojo.py --equivalence alle --scope all     # 8 von 45
   ```

   `rechnung` zeigt den Unterschied zwischen „unsere Suite sieht es nicht“ und
   „niemand kann es sehen“. Nur das zweite rechtfertigt den Abzug im Nenner.
   Mit `--scope all` ergibt sich der Wert aus der Vorlesung: 5 / (45 − 8) ≈ 0,135.

3. **Das Golden Dataset hätte T-1004 gesehen.** Braucht das venv, ruft aber kein LLM
   auf.

   ```bash
   python3 -m src.evaluate --all && cp eval/results.csv /tmp/vorher.csv
   # in src/triage.py in der Zeile "Zugang" das Keyword "passwort" löschen
   python3 -m src.evaluate --all
   diff <(cut -d, -f1-5 /tmp/vorher.csv) <(cut -d, -f1-5 eval/results.csv)
   git checkout -- src/triage.py
   ```

   Die Kategorie-Accuracy bleibt bei 70 %, weil T-1004 von richtig nach falsch
   und T-1026 von falsch nach richtig kippt. Der `diff` zeigt beide Tickets. Mit
   dem Default `--limit 10` fällt die Accuracy auf 60 %. Ein Orakel außerhalb
   des Codes nützt nur, wenn man es pro Fall auswertet und automatisch laufen
   lässt.

4. **Die Kür, `$ref` auflösen:** Leitet `SPEC_RESPONSE_FIELDS` in
   [`tools/spec_gate.py`](../tools/spec_gate.py) aus `spec["schemas"]` her und
   **löscht das dict**. Danach wird `StatistikReport` ohne Handeintrag geprüft.
   Drei Fallen: `$ref` in Responses, Array-Responses (`GET /tickets` liefert
   `items.$ref -> Ticket`, auf der Implementierungsseite also `list[Ticket]`
   entpacken) und das Abnahme-Kriterium, das danach **immer noch** gelten muss.
   `python3 -m pytest tests/test_vl09_werkzeuge.py -q` hilft beim Umbau.

5. **CI-Bonus:** Ein GitHub-Actions-Workflow, der bei jedem Pull Request
   `python3 tools/spec_gate.py --check` und Schemathesis ausführt. Drift macht
   dann den Build rot. Das ist die Medizin gegen Spec Drift aus der Vorlesung,
   mechanisch verabreicht.

6. **Mit und ohne `AGENTS.md`, diesmal sauberer:** Denselben Prompt aus
   Aufgabe E je dreimal mit und ohne `AGENTS.md` laufen lassen (neue Session je
   Lauf) und die vier Prüffragen zählen. Was müsstet ihr ändern, damit das
   Ergebnis etwas belegt?

7. **Alle Abweichungen des Drift-Servers:** Der Docstring von
   [`api/drifted_server.py`](../api/drifted_server.py) listet neun
   Abweichungen. Sechs davon sieht das Gate, sie ergeben 7 Befunde. Lasst
   Schemathesis gegen Port 8001 laufen und ordnet jeden Befund einer
   Abweichung zu. Welche bleiben für alle Werkzeuge unsichtbar?

---

## Troubleshooting

| Problem | Lösung |
|---|---|
| `git checkout` bricht ab: „Your local changes … would be overwritten“ oder „untracked working tree files would be overwritten by checkout: src/agent.py“ | Lokale Änderungen aus VL 8 sichern: `git stash push -u -m "stand-vl08"`, dann erneut `git checkout vl09-oracle`. Erst das `-u` nimmt ungetrackte Dateien mit, etwa das in VL 8 per `cp` angelegte `src/agent.py`. |
| `pathspec 'vl09-oracle' did not match` | Der Branch ist lokal noch unbekannt. Erst `git fetch origin`. |
| `ModuleNotFoundError: No module named 'src'` oder `'tools'` | Aus dem Repo-Wurzelverzeichnis arbeiten und Testdateien nicht direkt starten. `python3 tools/mutation_dojo.py --tests …` oder `python3 -m pytest` verwenden. |
| `python` statt `python3` findet nichts oder die falsche Version | In diesem Lab immer `python3` verwenden. |
| pytest meldet „3 passed“, der Dojo meldet „leer“ | Kein Widerspruch. Leere Tests bestehen immer. Der Dojo prüft den Quelltext (Aufgabe B). |
| `--suite oracle` meldet „TODO 1 ist noch nicht gefüllt“ | Der Rumpf von `test_jedes_keyword_trifft_seine_kategorie()` ist noch `...`, oder die Funktion wurde umbenannt. Der Dojo sucht sie namentlich. |
| `--suite frozen` meldet „FROZEN ist leer“ | TODO 2 trägt die Tabelle ein, als ausgeschriebenes Literal. |
| `--suite …` meldet „schon auf dem INTAKTEN Modul rot“ | Der Test ist falsch gefüllt. Erst reparieren. Ein Score auf einer roten Suite ist bedeutungslos. |
| `SpecYamlFehler: … Zeile N: Flow-Map … wird nicht unterstützt` | Die Spec enthält `{ … }`. Dieselbe Angabe im Blockstil schreiben, ein Schlüssel pro Zeile. |
| `ModuleNotFoundError: No module named 'fastapi'` oder `schemathesis: command not found` | venv aktivieren (`source .venv/bin/activate`) und `pip install -r requirements.txt`. |
| `opencode: command not found` | opencode ist nicht installiert oder nicht im PATH. Installation nach [opencode.ai/docs](https://opencode.ai/docs/), danach ein neues Terminal öffnen. |
| opencode: erste Antwort hängt minutenlang | Kaltstart (200 bis 300 s). Warten, nicht abbrechen. |
| opencode: 401 oder „unauthorized“ | Ist `HOMECLOUD_API_KEY` in **diesem** Terminal gesetzt (`echo $HOMECLOUD_API_KEY`)? Steht in der Config `{env:HOMECLOUD_API_KEY}`? |
| 403 mit Hinweis auf das Zeitfenster (nur montags) | Außerhalb des HomeCloud-Zeitfensters. Kein Bug. Montags wiederkommen oder Teil 2 von Hand machen. |
| opencode ändert Dateien, obwohl ihr nur einen Entwurf wolltet | Der Plan-Modus fragt vor jeder Dateiänderung nach. Wer zustimmt, lässt den Agenten schreiben. In Aufgabe D diese Rückfragen ablehnen, mit Tab prüfen, dass der **Plan-Modus** aktiv ist, und „Ändere noch keine Datei“ in den Prompt schreiben. Eine versehentliche Änderung nehmt ihr mit `git checkout -- <datei>` zurück. |
| Gate meldet Befunde auf `api/app.py` | **Zwischen Aufgabe D und E** ist genau 1 ROUTE-Befund richtig. **Nach Aufgabe E:** Diff lesen. Meist ist es EXTRA (erfundene Route), STATUS (Default 200 statt Spec-Code) oder QPARAM (erfundener Parameter). |
| Server startet nicht | `python3 -m uvicorn api.app:app` verwenden, nicht das bare `uvicorn`. Endet der Start mit `AssertionError: KategorieEnum weicht …`, weicht `src/triage.py` von der Spec ab. |
| `[Errno 48] Address already in use` | Auf dem Port läuft noch ein Server. Im alten Terminal mit Strg+C beenden oder einen anderen Port wählen (`--port 8002` und dieselbe Zahl in `--url`). |
| Änderungen an `app.py` wirken nicht | Der Server läuft ohne `--reload`. Neu starten oder mit `--reload` starten. |
| Schemathesis: „connection refused“ | Läuft der Server auf dem Port aus `--url`? Referenz-Server 8000, Drift-Server 8001. |
| Schemathesis: `positive_data_acceptance` auf `POST /tickets` mit 422 | `EmailStr` ist strenger als das Pattern der Spec. Adressen wie `a..b@x.com` oder `a@x.arpa` erfüllen das Pattern, `email-validator` lehnt sie ab. Das ist eine echte Spec-Lücke und kein Fehler in eurem Handler. |
| 404 auf `GET /tickets/stats` | Läuft der Server mit dem neuen Handler (`--reload`)? Wenn ja: Lest die Meldung im 404. Sie verrät, welcher Handler geantwortet hat. |
