# Lab VL 3: LLM anbinden und gegen die Regeln messen

**Leitfrage:** Schlägt ein LLM die Keyword-Regeln aus VL 1, und was kostet uns das?

Die Regeln aus VL 1 treffen bei der Kategorie 70 % und bei der Priorität 90 % der
30 Tickets. In diesem Lab bekommt das Triage-Tool einen LLM-Anschluss. Dann messt
ihr auf dem Golden Dataset, ob das LLM wirklich besser ist. Zum Schluss empfehlt
ihr mit euren eigenen Zahlen einen Betriebsort für LeineTech.

## Auf einen Blick

| Schritt | Inhalt | Minuten | Ergebnis | Checkpoint zum Aufholen |
|---|---|---|---|---|
| 0 | Setup: Branch, Umgebungsvariablen, Endpunkt | 10 | Endpunkt antwortet | `vl01-solution` |
| 1 | LLM-Anschluss bauen: `src/llm.py`, `src/summarize.py` | 25 | T-1003 per LLM klassifiziert | `vl03-llm-client` |
| 2 | Regeln gegen LLM messen: `src/evaluate.py` | 25 | eure Messwerte | `vl03-evaluation` |
| 3 | Betriebsort empfehlen (Einzelarbeit) | 20 | `labs/vl03-entscheidung.md` | |
| | Abschluss: Zahlen sammeln, Empfehlungen vorstellen | 10 | | |

**Lernziele.** Nach diesem Lab könnt ihr

1. einen LLM-Aufruf über eine OpenAI-kompatible API selbst bauen und ohne Endpunkt testen,
2. eine Modellantwort defensiv in strukturierte Daten überführen und Parse-Fehler sichtbar machen,
3. zwei Systeme auf einem Golden Dataset fair vergleichen und das Ergebnis interpretieren,
4. mit euren Messwerten einen Betriebsort (Cloud API, On-Premises, Edge) begründet empfehlen.

**Voraussetzungen**

- [ ] Python 3.12 oder 3.13 wie in VL 1, das Repo aus VL 1 (`leinetech`) mit aktivierter
      venv und ein Terminal im Repo-Root.
- [ ] Euer persönlicher HomeCloud-Key vom Dozenten (seit VL 1, siehe `SETUP.md`).
- [ ] Der Kurs-Endpunkt ist nur **montags von 06:00 bis 23:59** erreichbar. Außerhalb
      des Fensters funktionieren alle Tests und die Regel-Messung trotzdem.
- [ ] Die Befehle unten sind für macOS und Linux geschrieben. Wo PowerShell abweicht, steht
      die Windows-Variante direkt dabei. `cp` und `git` funktionieren auch in PowerShell.

**Spielregeln für eine faire Messung**

- **Entwicklungs- und Testdaten trennen.** T-1001 bis T-1010 kennt ihr aus VL 2. An diesen
  Tickets dürft ihr euren Prompt verbessern. T-1011 bis T-1030 sind eure Testdaten. Der
  Report weist sie getrennt aus.
- **Kein Ticket aus `data/tickets.json` als Few-Shot-Beispiel.** Sonst steht eine Testfrage
  samt Lösung im Prompt, und die Messung ist geschönt. Ein Test prüft, dass weder ein
  Betreff noch ein längerer Satz aus den Tickets im Prompt steht. Umformulierte Tickets
  findet er nicht. Denkt euch die Beispiele also wirklich aus.
- **Datenschutz.** Prompts und Antworten am Kurs-Endpunkt werden geloggt und sind eurem Key
  zuordenbar. Die LeineTech-Tickets sind fiktiv. Echte Daten gehören nicht in den Prompt.
- **Der Endpunkt ist geteilt.** Er verarbeitet sechs Anfragen gleichzeitig. Startet erst
  10 Tickets, dann alle 30. Lasst Thinking für die Hauptmessung aus (Schritt 0.2).

---

## Schritt 0: Setup (10 min)

### 0.1 Branch und Abhängigkeiten (3 min)

```bash
cd leinetech
git checkout vl01-solution
git pull
pip install -r requirements.txt
pip show litellm
python -m pytest -q
```

Erwartet: `pip show` meldet `Version: 1.89.2`. pytest meldet nur `passed` und kein `failed`.
Heißt euer Python-Befehl `python3`, nutzt ihn überall statt `python`.

Wer mit der eigenen VL-1-Lösung weitermacht, ersetzt `git checkout vl01-solution` und
`git pull` durch die zwei Befehle unten. Sie holen Anleitung, Vorlagen und Abhängigkeiten von
`vl01-solution`, und ihr bleibt auf eurem Branch. Die übrigen Befehle bleiben gleich.

```bash
git fetch
git checkout origin/vl01-solution -- labs/vl03-lab.md labs/templates requirements.txt
```

### 0.2 Umgebungsvariablen setzen (2 min)

```bash
export LLM_BASE_URL="https://llm.homecloud.ee/v1"
export LLM_API_KEY="<euer-key>"
export LLM_THINKING=off
```

Windows PowerShell:

```powershell
$env:LLM_BASE_URL = "https://llm.homecloud.ee/v1"
$env:LLM_API_KEY = "<euer-key>"
$env:LLM_THINKING = "off"
```

`LLM_THINKING=off` schaltet das Reasoning des Kursmodells ab. Die Antworten kommen dann in
wenigen Sekunden, und der geteilte Endpunkt bleibt entlastet. Die Variablen gelten nur im
aktuellen Terminal. In einem neuen Fenster setzt ihr sie erneut.

### 0.3 Vorlagen für Teil 1 kopieren und offline prüfen (2 min)

```bash
cp labs/templates/llm_skeleton.py src/llm.py
cp labs/templates/summarize_skeleton.py src/summarize.py
cp labs/templates/llm_tests.py tests/test_llm.py
cp labs/templates/summarize_tests.py tests/test_summarize.py
python -m src.llm
```

Erwartet (ohne Anfrage an den Endpunkt):

```
Endpunkt: https://llm.homecloud.ee/v1
Modell:   qwen3.6-35B-A3B-FP8
API-Key:  gesetzt
Thinking: aus
Timeout:  120 s
```

Steht dort `API-Key:  FEHLT`, fehlt die Variable aus 0.2 in diesem Terminal.

Die kopierten Tests schlagen fehl, bis ihr die TODOs in Teil 1 gefüllt habt. Das ist gewollt.
Ein `pytest`-Lauf an dieser Stelle meldet deshalb `19 failed, 13 passed`.

### 0.4 Endpunkt prüfen (3 min)

```bash
curl -s "$LLM_BASE_URL/models" -H "Authorization: Bearer $LLM_API_KEY" | head -c 300
```

Windows PowerShell:

```powershell
curl.exe -s "$env:LLM_BASE_URL/models" -H "Authorization: Bearer $env:LLM_API_KEY"
```

Erwartet ist eine JSON-Antwort, in der das Kursmodell steht, etwa
`{"data":[{"id":"qwen3.6-35B-A3B-FP8","object":"model",…`. Die Liste zeigt auch, welche
anderen Modelle der Gateway gerade anbietet.

**Fertig, wenn** pytest in 0.1 ohne `failed` endete, `python -m src.llm` einen gesetzten Key
zeigt und `/models` das Kursmodell listet. Antwortet der Endpunkt nicht, lest den Abschnitt
[Wenn der Endpunkt nicht erreichbar ist](#wenn-der-endpunkt-nicht-erreichbar-ist) und macht
trotzdem weiter: Teil 1 und die Regel-Messung in Teil 2 laufen ohne Endpunkt.

---

## Teil 1: Das Triage-Tool bekommt einen LLM-Anschluss (25 min)

**Ziel:** Ihr baut den API-Aufruf, einen Few-Shot-Prompt und einen robusten Parser. Am Ende
klassifiziert das LLM das Ticket T-1003, an dem die Regeln scheitern.

Die Vorlagen aus 0.3 laufen bis zum ersten TODO. Jedes TODO bricht mit einer klaren Meldung
ab (`NotImplementedError: TODO 1.1 …`), bis ihr es gefüllt habt. Die kopierten Tests sind
eure Abnahme. Sie laufen offline, weil sie den LLM-Aufruf durch eine Attrappe ersetzen.

### 1.1 Den API-Aufruf bauen: TODO 1.1 in `src/llm.py` (8 min)

Öffnet `src/llm.py` und lest zuerst die fertigen Hilfsfunktionen. Sie lesen die
Umgebungsvariablen, setzen das Provider-Präfix `hosted_vllm/` und bauen Timeout,
Längengrenze und Thinking-Schalter. Dann füllt ihr TODO 1.1 in `chat_with_usage()`: Ihr
schickt eine System- und eine User-Nachricht an `litellm.completion()` und gebt Text und
Token-Zahlen zurück.

Wir nutzen litellm und nicht das OpenAI-SDK. Die Firewall vor dem Gateway blockt den
User-Agent des OpenAI-SDK (HTTP 403 „Your request was blocked“).

```bash
python -m pytest -q tests/test_llm.py
```

Erwartet: `15 passed`. Warnungen aus litellm oder pydantic könnt ihr ignorieren. Dann der
erste echte Aufruf:

```bash
python -c "from src.llm import chat; print(chat('Sag nur: OK'))"
```

Erwartet: `OK` nach wenigen Sekunden. Im Kurs hat der Dozent das Modell vorher geladen.
Beim Nacharbeiten muss das Modell bei der ersten Anfrage oft erst in die GPUs geladen werden
(Cold Start, 200 bis 300 s). Der Default-Timeout von 120 s reicht dafür nicht. Startet die
erste Anfrage dann mit längerem Timeout:

```bash
LLM_TIMEOUT=360 python -c "from src.llm import chat; print(chat('Sag nur: OK'))"
```

Windows PowerShell (der Wert gilt danach für alle Befehle in diesem Terminal):

```powershell
$env:LLM_TIMEOUT = "360"
python -c "from src.llm import chat; print(chat('Sag nur: OK'))"
```

### 1.2 Den Few-Shot-Prompt schreiben: TODO 1.2 in `src/summarize.py` (5 min)

`CLASSIFY_PROMPT` nennt schon die erlaubten Kategorien, die Prioritäten und das JSON-Format.
Ergänzt mindestens zwei eigene Beispiele (Few-Shot aus VL 2). Habt ihr in VL 2 eigene
Beispiele geschrieben, übernehmt sie. Sonst denkt ihr euch neue aus. Gute Beispiele decken
verschiedene Kategorien und Prioritäten ab und zeigen ein Prinzip, zum Beispiel dass die
Kategorie vom betroffenen System abhängt und nicht von einem einzelnen Wort. Formuliert sie
so, dass sie keinem der 30 Tickets ähneln.

### 1.3 Die Antwort defensiv parsen: TODO 1.3 in `src/summarize.py` (8 min)

Modelle schreiben gern Text um das JSON herum, schreiben „software“ klein oder erfinden eine
Kategorie. `_parse_classification()` soll daraus trotzdem ein gültiges Ergebnis machen. Ist
die Antwort unbrauchbar, liefert die Funktion den Rückfall `_fallback()`. Er setzt
`"parse_fehler": True`. Warum das wichtig ist: Der Rückfall lautet Software und mittel, und
das sind zugleich die häufigsten Gold-Labels. Parse-Fehler zählen in Teil 2 weiter mit dem
Rückfallwert, so wie sich das System im Betrieb verhielte. Die Markierung zeigt euch, wie
viele Treffer davon nur Zufall sind.

```bash
python -m pytest -q tests/test_summarize.py
```

Erwartet: `12 passed`.

### 1.4 T-1003 im Vergleich (4 min)

T-1003 lautet „Rechnungsmodul in FinanzPro stürzt beim PDF-Export ab“. Das Soll-Label ist
Software und hoch.

```bash
python -c "from src.ticket_loader import get_ticket; from src.triage import classify_and_prioritize; print(classify_and_prioritize(get_ticket('T-1003')))"
python -c "from src.ticket_loader import get_ticket; from src.summarize import classify_ticket_llm; print(classify_ticket_llm(get_ticket('T-1003')))"
```

Erwartet: Die Regeln liefern `('Abrechnung', 'hoch')`, weil das Wort „Rechnung“ zuerst
greift. Das LLM liefert ein Dict der Form
`{'kategorie': '…', 'prioritaet': '…', 'parse_fehler': False, 'prompt_tokens': …, 'completion_tokens': …}`.
Die Token-Zahlen braucht ihr in Teil 2 und 3 für die Kosten.

**Fertig, wenn** `python -m pytest -q` ohne `failed` endet und T-1003 ein Dict mit
`'parse_fehler': False` liefert. Auf dem Checkpoint liegt zusätzlich `tests/test_main.py`
für die Kommandozeile.

**Aufholen:** Der Checkpoint `vl03-llm-client` enthält den fertigen Stand von Teil 1.
Sichert vorher euren eigenen Stand:

```bash
git switch -c vl03-mein-stand
git add -A
git commit -m "VL 3: mein Stand"
git checkout vl03-llm-client
```

**Bonus für Schnelle:** Baut `src/main.py` mit `argparse`-Subkommandos um, sodass
`python -m src.main classify T-1003` Regeln und LLM nebeneinander zeigt. Ohne Subkommando
soll weiterhin der Regel-Report aus VL 1 laufen. Vergleicht danach mit `src/main.py` auf dem
Checkpoint.

---

## Teil 2: Regeln gegen LLM messen (25 min)

**Ziel:** Ihr ersetzt das Bauchgefühl „das LLM ist bestimmt besser“ durch eine Messung auf
dem Golden Dataset `eval/golden.jsonl`. Es enthält die von Menschen vergebenen Soll-Labels
für alle 30 Tickets.

### 2.1 Vorlage kopieren (1 min)

```bash
cp labs/templates/evaluate_skeleton.py src/evaluate.py
cp labs/templates/evaluate_tests.py tests/test_evaluate.py
```

Das Drumherum ist fertig: Laden, Kommandozeile, CSV und Report. Eure Arbeit ist die
Messlogik in drei TODOs.

### 2.2 Die Regeln messen: TODO 2.1 und 2.2 (8 min)

TODO 2.1 misst pro Ticket die Regeln und ihre Latenz in Millisekunden. TODO 2.2 berechnet die
Accuracy, also den Anteil korrekter Vorhersagen. Danach läuft die Regel-Baseline ohne
Endpunkt:

```bash
python -m src.evaluate --all
```

Erwartet (die Latenz schwankt leicht):

```
==========================================================================
EVALUIERUNG auf 30 Tickets (1 Ticket = 3,3 Prozentpunkte)
==========================================================================
System                               Kategorie  Priorität  Latenz (Median)
Mehrheitsklasse: Software / mittel        30 %       60 %                -
Keyword-Regeln (VL 1)                     70 %       90 %         0,007 ms
--------------------------------------------------------------------------
Nur Testdaten (20 Tickets ab T-1011): Regeln 70 % / 90 %
Dringend übersehen, Regeln: 2 von 8 (T-1014, T-1024)
==========================================================================
Details: eval/results.csv
```

So lest ihr die Zeilen:

- **Mehrheitsklasse** ist der einfachste sinnvolle Vergleichswert: ein System, das immer das
  häufigste Label sagt. Bei der Priorität trifft „immer mittel“ schon 60 %.
- **Dringend übersehen** zählt Tickets mit Soll-Priorität hoch, die ein System nicht als hoch
  einstuft. Für eine Triage ist das der teuerste Fehler.
- **1 Ticket = 3,3 Prozentpunkte.** Auf 30 Tickets sagt ein Unterschied von ein oder zwei
  Tickets wenig aus.

Der Report schreibt Zahlen mit Dezimalkomma. Die CSV behält den Dezimalpunkt, damit Python
und andere Werkzeuge die Werte direkt als Zahlen lesen.

### 2.3 Das LLM robust messen: TODO 2.3 (4 min)

Bei 20 Personen am selben Endpunkt kommen Timeouts und Wartezeiten vor. TODO 2.3 fängt einen
Endpunkt-Fehler pro Ticket ab, markiert das Ticket und macht weiter. Nach drei Endpunkt-Fehlern
in Folge bricht der Lauf ab, weil der Endpunkt dann vermutlich weg ist. Auch Strg+C beendet
den Lauf, und die bisherigen Tickets werden trotzdem ausgewertet.

Ein Fehler im eigenen Code bricht dagegen sofort mit Traceback ab. Beispiele sind ein
`KeyError` durch eine einzelne geschweifte Klammer im Few-Shot-Prompt oder ein `TypeError`
im Parser. Sonst würde er als vermeintlicher Endpunkt-Fehler in der Statistik verschwinden.
Die Hilfsfunktion `is_endpoint_error()` in der Vorlage unterscheidet die beiden Fälle.

```bash
python -m pytest -q tests/test_evaluate.py
```

Erwartet: `16 passed`.

### 2.4 Messen (8 min)

```bash
python -m src.evaluate --llm
python -m src.evaluate --llm --all
```

Der erste Befehl misst die 10 Entwicklungstickets, der zweite alle 30. Pro Ticket erscheint
eine Fortschrittszeile. Rechnet je nach Last und Thinking mit 1 bis 10 Sekunden pro Ticket.
Der Report hat dann zusätzlich eine LLM-Zeile und diese Befunde:

```
LLM (qwen3.6-35B-A3B-FP8)                 xx %       xx %           x,xx s
--------------------------------------------------------------------------
Nur Testdaten (20 Tickets ab T-1011): Regeln 70 % / 90 %, LLM xx % / xx %
Dringend übersehen, Regeln: 2 von 8 (T-1014, T-1024)
Dringend übersehen, LLM: x von 8 (…)
Kategorie nur Regeln richtig: …
Kategorie nur LLM richtig:    …
Priorität nur Regeln richtig: …
Priorität nur LLM richtig:    …
LLM: x Parse-Fehler, x Endpunkt-Fehler, Thinking: off
Parse-Fehler zufällig richtig: Kategorie x, Priorität x
LLM-Tokens pro Ticket (Median): xxx ein, xx aus
```

Die Zeile „Parse-Fehler zufällig richtig“ zählt die Treffer, die nur der Rückfall
Software / mittel erzeugt hat. Sie stecken in der Accuracy oben mit drin.

Jedes Ticket steht mit allen Werten in `eval/results.csv`. Ein Lauf überschreibt die Datei.
Für Vergleiche schreibt ihr in eine eigene Datei, zum Beispiel `--csv eval/lauf-2.csv`.
Ein anderes Modell misst ihr mit demselben Code, indem ihr `LLM_MODEL` setzt:

```bash
LLM_MODEL=<modell> python -m src.evaluate --llm --csv eval/lauf-2.csv
```

### 2.5 Messwerte festhalten (4 min)

| System | Kategorie | Priorität | Test (20): Kat. / Prio. | dringend übersehen | Median-Latenz | Parse-Fehler | Token pro Ticket (ein / aus) |
|---|---|---|---|---|---|---|---|
| Mehrheitsklasse | 30 % | 60 % | 30 % / 70 % | 8 von 8 | - | - | - |
| Keyword-Regeln (VL 1) | 70 % | 90 % | 70 % / 90 % | 2 von 8 | < 0,1 ms | 0 | 0 |
| qwen3.6-35B, Thinking aus | | | | | | | |
| Bonus: Variante | | | | | | | |

Die Spalten Kategorie und Priorität gelten für alle 30 Tickets. Die Spalte „Test (20)“ übernehmt
ihr aus der Report-Zeile „Nur Testdaten“. Sie ist eure Hauptzahl, weil ihr den Prompt an den
Entwicklungstickets verbessern durftet. „-“ heißt „entfällt“.

Tragt eure LLM-Zeile auch in die Klassentabelle ein (Link vom Dozenten). So sehen wir
gemeinsam, wie stark die Ergebnisse zwischen euren Prompts streuen.

**Reflexionsfragen im Lab.** Die Fragen 1 bis 3 beantwortet ihr jetzt. Die Antworten stehen
direkt im Report.

1. Ist der Abstand belastbar? Zählt bei der Kategorie „nur LLM richtig“ gegen „nur Regeln
   richtig“. Erst ab etwa 6 zu 0 ist er mehr als Zufall. Auf den 20 Testtickets ist ein Ticket
   5 Prozentpunkte.
2. Welche Tickets hat nur das LLM richtig, welche nur die Regeln? Was haben die Tickets
   jeweils gemeinsam?
3. Wie viele dringende Tickets übersieht jedes System? Welcher Fehler wäre für LeineTech
   teurer: ein übersehener Ausfall oder ein zu hoch eingestuftes Ticket?

**Reflexionsfragen zum Nacharbeiten.** Die Fragen 4 bis 7 brauchen mehr Zeit, als das Lab
hergibt. Beantwortet sie bis zur nächsten Vorlesung.

4. Wie viele eurer LLM-Treffer sind Parse-Fehler, die zufällig auf Software oder mittel
   fielen? Die Zeile „Parse-Fehler zufällig richtig“ im Report zählt sie, die Spalte
   `llm_parse_fehler` der CSV zeigt die Tickets. Wie hoch wäre die Accuracy ohne diese
   Zufallstreffer?
5. Vergleicht euren Lauf auf den 10 Entwicklungstickets mit der Zeile „Nur Testdaten“. Wie
   groß ist der Abstand, und woran liegt er?
6. Bei welchen Fehlklassifikationen würdet ihr dem Gold-Label widersprechen? Vergleicht mit
   euren Notizen aus VL 2. Auch ein Golden Dataset ist nur so gut wie seine Labels.
7. Der Endpunkt bedient sechs Anfragen gleichzeitig. Wie lange brauchen 20 Personen mit je 30
   Tickets bei eurer Median-Latenz? Was heißt das für LeineTech mit rund 40 Tickets am Tag?

**Fertig, wenn** `python -m pytest -q` ohne `failed` endet, eure LLM-Zeile in eurer Tabelle und
in der Klassentabelle steht und ihr die Fragen 1 bis 3 beantwortet habt.

**Aufholen:** Der Checkpoint `vl03-evaluation` enthält den fertigen Stand von Teil 2.
Sichert vorher euren Stand. Der Branch bekommt einen neuen Namen, weil es
`vl03-mein-stand` aus Teil 1 vielleicht schon gibt:

```bash
git switch -c vl03-mein-stand-teil2
git add -A
git commit -m "VL 3: mein Stand Teil 2"
git checkout vl03-evaluation
```

**Bonus für Schnelle**

- **Thinking an gegen aus:** `LLM_THINKING=on python -m src.evaluate --llm --csv eval/thinking-an.csv`
  (PowerShell: erst `$env:LLM_THINKING = "on"`). Vergleicht Accuracy, Latenz und
  Output-Tokens mit eurem Lauf ohne Thinking. Nur 10 Tickets, der Endpunkt ist geteilt.
  Beachtet: Für den Thinking-Modus empfiehlt der Hersteller Sampling statt temperature 0.
- **Reproduzierbarkeit:** Setzt in `classify_ticket_llm()` den Parameter `temperature=0.7`
  beim Aufruf von `chat_with_usage()`. Lasst 10 Tickets zweimal laufen, jeweils mit eigener
  `--csv`-Datei, und zählt die Abweichungen. Wiederholt das mit temperature 0.
- **Kosten hochrechnen:** Token pro Ticket × 40 Tickets am Tag × 30 Tage ergibt die Token pro
  Monat. Rechnet mit einem Cloud-Preis aus der Vorlesung. Wie ändert sich das Ergebnis mit
  Thinking?

---

## Teil 3: Betriebsort empfehlen (20 min, Einzelarbeit)

**Ziel:** LeineTech will die LLM-Triage produktiv nehmen. Ihr gebt eine begründete Empfehlung
ab: Cloud API, On-Premises oder Edge. Dafür nutzt ihr die sechs Kriterien aus der Vorlesung
und eure Messwerte aus Teil 2.

Legt die Datei `labs/vl03-entscheidung.md` an und kopiert die Matrix unten hinein. Für
LeineTech füllt ihr die ganze Matrix aus. Beim Kontrastszenario reicht die Spalte Tendenz.

### 3.1 LeineTech (15 min)

Bearbeitet zuerst den Fall LeineTech. Diese Fragen helfen:

- Welche personenbezogenen Daten stehen in den Tickets (Namen, E-Mail-Adressen,
  Rechnernamen)? Gehören sie zu den besonderen Kategorien nach Art. 9 DSGVO?
- Lassen sich die Daten vor dem Prompt pseudonymisieren? Was bliebe dann übrig?
- Wäre die HomeCloud aus Sicht von LeineTech Self-Hosting oder ein externer Anbieter, mit dem
  ein Auftragsverarbeitungsvertrag (AVV) nötig ist?
- Rechtfertigt euer gemessener Abstand zu den Regeln den Aufwand? Wie viele dringende Tickets
  übersieht das LLM?
- Was kostet der Betrieb bei rund 40 Tickets am Tag mit euren Token-Zahlen?
- Falls ihr On-Premises empfehlt: Wie viel VRAM braucht das Kursmodell, und welche Karten
  reichen?

### 3.2 Kontrastszenario (5 min)

Der Dozent teilt euch eines der drei Szenarien zu. Beim Nacharbeiten wählt ihr selbst, auch
ein eigener Fall aus der Praxis ist möglich.

1. Internes Code-Review-Tool für eine Bank (Quellcode aus internen Systemen)
2. Termin-Chatbot für eine Arztpraxis (Termine, allgemeine Fragen)
3. QA-Assistent für Industrie-Roboter in einer Fertigungshalle ohne Internetzugang

Füllt für euer Szenario nur die Spalte Tendenz und schreibt einen Satz Empfehlung. Die
Begründungen besprechen wir im Abschluss gemeinsam.

### Entscheidungsmatrix

Bewertung: 1 heißt „spielt in diesem Szenario kaum eine Rolle“, 5 heißt „entscheidet den Fall“.
Jede Bewertung braucht eine Begründung.

| Kriterium | Bewertung (1 bis 5) | Begründung | Tendenz (Cloud / On-Prem / Edge) |
|---|---|---|---|
| Datensensitivität und DSGVO | | | |
| Anfragevolumen und Kosten | | | |
| Latenz und Konnektivität | | | |
| Modellqualität (eure Messwerte aus Teil 2) | | | |
| Team und Betriebsaufwand | | | |
| Budget und Lock-in | | | |

**Ergebnis für LeineTech:** die vollständige Matrix, eine Empfehlung mit drei Begründungen,
die wichtigsten DSGVO-Maßnahmen und ein Satz dazu, was sich ändern müsste, damit eure
Empfehlung kippt.

**Ergebnis für das Kontrastszenario:** die Spalte Tendenz und ein Satz Empfehlung.

---

## Abschluss (10 min)

- Wir sammeln die Klassentabelle aus Teil 2: Minimum, Median und Maximum der LLM-Accuracy.
- Zwei oder drei von euch stellen ihre Empfehlung für LeineTech vor.
- Wir vergleichen LeineTech mit den Kontrastszenarien: dieselben sechs Kriterien, andere
  Antwort. Je Szenario begründet eine Person ihre Tendenz mündlich.

### Vorbereitung auf VL 4

Sichert eure VL-3-Arbeit auf einem eigenen Branch, bevor ihr wechselt. `git add -A` nimmt auch
die aus den Vorlagen kopierten Dateien mit. Ohne Commit bricht der Checkout ab, weil der
VL-4-Branch `src/llm.py`, `src/summarize.py` und `src/evaluate.py` selbst enthält.

```bash
git switch -c lab-vl03
git add -A && git commit -m "VL 3: mein Stand"
git fetch origin
git checkout vl04-rag-ingestion-pipeline-start
pip install -r requirements.txt
```

Neu in `requirements.txt` ist ChromaDB, das einige Pakete nachlädt. Installiert es deshalb vor
dem Termin. Key und Endpunkt bleiben gleich.

---

## Wenn der Endpunkt nicht erreichbar ist

Der Kurs-Endpunkt hat kein SLA. Fällt er aus, oder arbeitet ihr außerhalb des
Montagsfensters, geht ihr so vor:

1. Im Kurs gebt ihr dem Dozenten Bescheid.
2. Teil 1 prüft ihr vollständig mit den Tests (`python -m pytest -q`). Sie brauchen keinen
   Endpunkt.
3. In Teil 2 messt ihr die Regel-Baseline (`python -m src.evaluate --all`) und wertet die
   Beispiel-Ergebnisse eines vollständigen LLM-Laufs des Dozenten aus. Sie liegen auf dem
   Branch `vl03-evaluation`: `eval/beispiel-dozent.txt` enthält den Report,
   `eval/beispiel-dozent.csv` alle Tickets. Ihr holt beide Dateien ohne Branchwechsel:

   ```bash
   git fetch
   git checkout origin/vl03-evaluation -- eval/beispiel-dozent.txt eval/beispiel-dozent.csv
   ```

   Fehlen die Dateien noch, fragt beim Dozenten nach. Für Teil 3 nutzt ihr dieselben Zahlen.
4. Den LLM-Lauf holt ihr am nächsten Montag nach.

Jedes andere OpenAI-kompatible Backend funktioniert mit demselben Code über `LLM_BASE_URL`,
`LLM_API_KEY` und `LLM_MODEL`. Im Kurs nutzen wir nur den Kurs-Endpunkt, damit alle dieselben
Datenschutzregeln haben.

## Troubleshooting

| Problem | Ursache und Lösung |
|---|---|
| `NotImplementedError: TODO …` | Gewollt. Das genannte TODO ist noch offen. |
| `API-Key:  FEHLT` bei `python -m src.llm` | Die Variablen gelten nur im Terminal, in dem ihr sie gesetzt habt. Schritt 0.2 wiederholen. |
| `AuthenticationError` oder HTTP 401 | Key falsch oder mit Leerzeichen kopiert. Key prüfen. |
| HTTP 403 „nur montags …“ | Außerhalb des Zeitfensters. Das ist Absicht und kein Fehler. |
| HTTP 403 „Your request was blocked“ | Der Aufruf lief über das OpenAI-SDK oder über eine andere litellm-Version als im Kurs. `pip show litellm` sollte 1.89.2 zeigen. |
| `RateLimitError` oder HTTP 429 | Zu viele Anfragen gleichzeitig. Kurz warten, erst 10 Tickets messen, `--all` später. |
| `Timeout` bei der ersten Anfrage | Cold Start. Den Timeout erhöhen und neu starten: `export LLM_TIMEOUT=360` (PowerShell: `$env:LLM_TIMEOUT = "360"`), siehe 1.1. |
| „Abbruch nach 3 Endpunkt-Fehlern in Folge“ | Der Endpunkt ist gerade nicht erreichbar. Die Fehlerzeilen darüber nennen die Art, etwa `Timeout`, `APIError` (keine Verbindung), `RateLimitError` oder `AuthenticationError`. Siehe Abschnitt oben. |
| `KeyError`, `TypeError` oder `ValueError` mit Traceback bei `--llm` | Der Fehler liegt im eigenen Code, nicht am Endpunkt. Häufig ist es eine einzelne geschweifte Klammer im Few-Shot-Prompt (im Beispiel-JSON `{{ }}` schreiben) oder ein Fehler im Parser. `python -m pytest -q` zeigt die Stelle meist genauer. |
| Viele Parse-Fehler | Die Antwort ist kein gültiges JSON. Lasst euch in `classify_ticket_llm()` vorübergehend die rohe Antwort ausgeben (`print(answer)`) und verbessert dann Prompt oder Parser. |
| `ModuleNotFoundError: No module named 'litellm'` | `pip install -r requirements.txt` im richtigen Python-Environment. |
| `ModuleNotFoundError: No module named 'src'` | Befehle im Repo-Root starten, dort wo `README.md` liegt. |
| `eval/golden.jsonl nicht gefunden` | Ebenfalls: Befehl im Repo-Root starten. |
| `git checkout` meldet „would be overwritten“ | Eigenen Stand erst sichern, siehe „Aufholen“ in Teil 1. |
