# Lab VL 1: Das LeineTech-Triage-Tool retten

Das Ticket-Triage-Tool der LeineTech GmbH läuft, und alle Tests sind grün. Trotzdem würde es
niemand mergen. In diesem Lab lasst ihr Linter, KI-Assistent und Artefakt-Scanner auf den Code los.
Danach prüft ihr kritisch, ob der Code wirklich besser geworden ist.

**Leitfrage:** Macht der KI-Assistent den Code wirklich besser, und wie weist ihr das nach?

| | |
|---|---|
| **Dauer** | ca. 80 min in der Präsenz (50 min geführt, 30 min offene Übung) |
| **Sozialform** | 2er-Teams erwünscht, allein geht auch |
| **Start-Branch** | `vl01-start` |
| **Musterlösung** | `vl01-solution` (erst nach dem Lab ansehen) |
| **Werkzeuge** | pylint, flake8, pytest, VS Code mit Continue, Trivy |
| **Stand der Zahlen** | 25.09.2026 mit Python 3.12, pylint 3.3.1, flake8 7.1.1, Trivy 0.74.0 |

---

## Lernziele

Nach diesem Lab könnt ihr …

1. Befunde von pylint den Kategorien C, R, W und E **zuordnen**, flake8-Codes (E und W von pycodestyle,
   F von pyflakes) **einordnen** und beide nach Risiko **gewichten**.
2. einen KI-Assistenten Datei für Datei mit einem präzisen Auftrag **refaktorieren lassen**.
3. einen KI-Diff mit Tests, Report-Vergleich und Fehlerfall-Check **prüfen** und eine begründete
   Merge-Entscheidung **treffen**.
4. CVE-Befunde von Trivy mit der Kurs-Faustregel (ab CVSS 7.0 sofort handeln) **einordnen** und die
   beste Behebung **ableiten**.

---

## Voraussetzungen

**Wissen:** VL 1 Teil 1 bis 4 (Clean-Code-Prinzipien, Pylint-Kategorien, CVE und CVSS).
Wer nacharbeitet, liest vorher die Folien dieser Teile.

**Software:**

| Werkzeug | Version | Prüfen mit | Hinweis |
|---|---|---|---|
| Python | 3.12 oder 3.13 | `python3 --version` (Windows: `py --version`) | Nicht 3.14: Der Kurs pinnt pylint 3.3.1, Python 3.14 unterstützt pylint erst ab 4.0. |
| git | beliebig aktuell | `git --version` | |
| VS Code mit Extension **Continue** | aktuell | Erweiterungsansicht in VS Code | KI-Assistent für Schritt 2 |
| Ollama mit `qwen2.5-coder:1.5b` | aktuell | `ollama list` | lokales Modell für die Tab-Vervollständigung |
| Trivy | 0.70 oder neuer | `trivy --version` | macOS: `brew install trivy` · Windows: `winget install -e --id AquaSecurity.Trivy` |
| Kurs-API-Key | | | gibt der Dozent in VL 1 zu Beginn der zweiten Pause aus, ein Key pro Person, nicht teilen |

Unter Windows funktionieren alle Befehle in **Git Bash**. Abweichungen für PowerShell stehen im
Troubleshooting.

### Einmalig einrichten (vor dem Lab)

Startet diese Befehle zu Beginn der Vorlesung. Die Downloads laufen dann während der Theorie.

```bash
git clone https://github.com/HFM254SE/code.git leinetech
cd leinetech
git checkout vl01-start
python3 --version                      # 3.12 oder 3.13? Bei 3.14 unten python3.13 statt python3
python3 -m venv .venv                  # Windows: py -3.12 -m venv .venv
source .venv/bin/activate              # Windows Git Bash: source .venv/Scripts/activate
pip install -r requirements.txt
ollama pull qwen2.5-coder:1.5b         # ca. 1 GB, schwache Laptops: qwen2.5-coder:0.5b
trivy fs --download-db-only            # ca. 120 MB Download, ca. 1,3 GB auf der Platte
```

Den Kurs-Key bekommt ihr zu Beginn der zweiten Pause. In dieser Pause legt ihr die
Continue-Konfiguration `~/.continue/config.yaml` nach der Vorlage in `SETUP.md` an und ersetzt
`<euer-key>` durch euren Kurs-Key. Chat und Edit laufen über den Kurs-Endpunkt (HomeCloud), die
Tab-Vervollständigung lokal über Ollama.

**Smoke-Test (ebenfalls in der Pause):** Öffnet den Continue-Chat und schickt „Sag Moin.“. Die
erste Antwort kann beim Cold Start 200 bis 300 Sekunden dauern. Das ist kein Fehler. Wartet einmal ab.

> **Regeln für den Kurs-Endpunkt**
>
> - Er ist nur **montags von 06:00 bis 23:59 Uhr** (Europe/Berlin) freigeschaltet. Außerhalb dieses
>   Fensters antwortet er mit HTTP 403. Plant Schritt 2 in dieses Fenster.
> - **Prompts und Antworten werden geloggt** und sind eurem Key zuordenbar. Gebt keine Passwörter,
>   Secrets oder echten Personendaten ein.
> - Er ist für kurze, fokussierte Aufträge gedacht. Deshalb arbeitet ihr in Schritt 2 Datei für Datei.

### Checkpoint-Branches

| Branch | Inhalt |
|---|---|
| `vl01-start` | Ausgangszustand für dieses Lab |
| `vl01-solution` | Musterlösung, zugleich Startpunkt für VL 3 |

Wer eine Session verpasst hat, steigt am passenden Branch ein. Die Musterlösung könnt ihr euch als
Diff ansehen, ohne euren eigenen Stand zu verlieren:

```bash
git diff origin/vl01-start origin/vl01-solution -- src/    # was die Musterlösung geändert hat
git diff origin/vl01-solution -- src/                      # euer Stand im Vergleich zur Musterlösung
```

---

## Zeitplan

| Schritt | Inhalt | Minuten |
|---|---|---|
| 0 | Setup-Check und Ausgangsreport sichern | 5 |
| 1 | Linter laufen lassen und Befunde gewichten | 10 |
| 2 | KI-Assistent fixen lassen und den Diff reviewen (drei Runden) | 20 |
| 3 | Abhängigkeiten mit Trivy scannen | 10 |
| Debrief | Musterlösung und Befundtabelle im Plenum | 5 |
| Offene Übung | Eigener Code unter der Lupe | 22 |
| Ergebnisrunde | 3 bis 4 Teams stellen vor | 8 |
| **Summe** | | **80** |

Wer zu Hause nacharbeitet, rechnet mit etwa 90 Minuten, weil Setup-Probleme und Wartezeiten dazukommen.

---

## Das Sicherheitsnetz

Nach **jeder** Änderung am Code prüft ihr drei Dinge. Den Ausgangsreport `report-vorher.txt` legt ihr
in Schritt 0 an.

```bash
# Check 1: Tests
python -m pytest -q

# Check 2: Report-Vergleich, ein Characterization Test
python -m src.main > report-nachher.txt
git diff --no-index report-vorher.txt report-nachher.txt

# Check 3: Fehlerfall, also was passiert, wenn die Ticket-Datei fehlt
python -c "from src.ticket_loader import load_tickets; print(len(load_tickets('fehlt.json')))"
```

| Check | Erwartung auf `vl01-start` | Was ihr nach einer Änderung prüft |
|---|---|---|
| 1 Tests | `5 passed` | Weiterhin `5 passed`? |
| 2 Report | keine Ausgabe (die Reports sind gleich) | Weiterhin keine Ausgabe? Jede Zeile im Diff ist eine Verhaltensänderung. |
| 3 Fehlerfall | `0` | Gleiches Ergebnis? Wenn nicht: Ist die Änderung gewollt, und hat die KI sie erwähnt? |

Der Report-Vergleich ist ein **Characterization Test**: Er hält das Ist-Verhalten fest, bevor ihr
umbaut, auch wenn dieses Verhalten falsch ist. Check 3 wiederholt das Experiment vom Anfang der
Vorlesung: Fehlt die Datei, meldet `vl01-start` still null Tickets. Keiner der 5 Tests prüft dieses
Verhalten.

**Merke:** Grüne Checks sind notwendig, aber nicht hinreichend. Sie zeigen nur, was sie prüfen.

**Etwas kaputt?** `git restore src/stats.py` setzt eine Datei auf den letzten Commit zurück,
`git restore src/` alle Dateien in `src/`.

---

## Eure Befundtabelle

Diese Tabelle begleitet euch durch das Lab. Kopiert sie in eine eigene Notizdatei und füllt die
drei rechten Spalten nach und nach aus.

| Nr | Befund im Code | Prinzip | Gemeldet von (Schritt 1 und 3) | Von der KI behoben? (Schritt 2) | Review nötig? (Debrief) |
|---|---|---|---|---|---|
| 1 | `import requests`, `os`, `sys`, `re` werden nie benutzt | KISS, Kopplung | | | |
| 2 | `except:` fängt jeden Fehler ab | Fehlerhandling | | | |
| 3 | globaler `CACHE`: Ein zweiter Aufruf mit anderem Pfad liefert die alten Daten | Testbarkeit, Kopplung | | | |
| 4 | `classify_and_prioritize` mit 21 Verzweigungen | SRP, KISS | | | |
| 5 | acht fast identische Zählschleifen in `stats.py` | DRY | | | |
| 6 | Namen wie `TXT`, `h`, `s`, `z`, `found2` | sprechende Namen | | | |
| 7 | veraltete Abhängigkeiten in `requirements.txt` | Sicherheit | | | |
| 8 | fehlende Ticket-Datei ergibt „Anzahl Tickets: 0“ und Exit-Code 0 | Fehlerhandling | | | |
| 9 | T-1003 „Rechnungsmodul in FinanzPro stürzt beim PDF-Export ab“ landet in „Abrechnung“ | Fachlogik | | | |

<details>
<summary>Zur Selbstkontrolle: Spalte „Gemeldet von“</summary>

| Nr | Gemeldet von |
|---|---|
| 1 | pylint `W0611 unused-import`, zum Beispiel `src/ticket_loader.py:3:0: W0611` für `requests`. flake8 `F401`, zum Beispiel `src/ticket_loader.py:3:1: F401` |
| 2 | pylint `W0702 bare-except` (`src/ticket_loader.py:15:4: W0702`), flake8 `E722` (`src/ticket_loader.py:15:5: E722`) |
| 3 | pylint `W0603 global-statement` (`src/ticket_loader.py:9:4: W0603`) meldet das `global`. Die veralteten Daten meldet kein Linter. |
| 4 | pylint `R0912 too-many-branches` (`src/triage.py:6:0: R0912`, 21/12) |
| 5 | pylint `R0912` (`src/stats.py:1:0: R0912`, 16/12) meldet die Verzweigungen. Die Duplikation selbst meldet kein Linter direkt. |
| 6 | `TXT` meldet pylint als `C0103 invalid-name` (`src/triage.py:7:4: C0103`). `h`, `s`, `z` und `found2` sind formal gültiges snake_case. Das findet nur ein Mensch im Review. |
| 7 | Trivy (Schritt 3) |
| 8 | Kein statisches Werkzeug. Pylint meldet mit `W0702` die Ursache, aber nicht die Folge. Den Fehler findet nur ein Test oder ein Programmlauf ohne Datei. |
| 9 | Kein Werkzeug von heute. Ob die Fachlogik stimmt, prüfen Tests und Menschen. |

</details>

---

## Schritt 0: Setup-Check und Ausgangsreport (5 min)

```bash
cd leinetech
source .venv/bin/activate              # Windows Git Bash: source .venv/Scripts/activate
git switch -c lab-vl01                 # eigener Arbeitsbranch, vl01-start bleibt unberührt
python -m src.main
python -m pytest
trivy --version
python -m src.main > report-vorher.txt
```

**Erwartete Ausgabe:**

- `python -m src.main` druckt einen Report über 30 Tickets:
  ```text
  LeineTech Ticket-Triage
  Anzahl Tickets: 30
  T-1001 | HOCH    | Hardware   | Laptop fährt nicht mehr hoch
  …
  ============================================================
  TICKET-STATISTIK LEINETECH SUPPORT
  ============================================================
  Hardware: 5  Software: 8  Netzwerk: 5  Zugang: 6  Abrechnung: 6
  Prioritaeten: hoch=7 mittel=18 niedrig=5
  ============================================================
  ```
- `python -m pytest` endet mit `5 passed`.
- `trivy --version` zeigt `Version: 0.70.0` oder neuer und darunter `Vulnerability DB:` mit einem
  Datum. Fehlt der DB-Block, ist die Datenbank noch nicht geladen.
- `report-vorher.txt` liegt im Projektordner. Die Datei ist eine Arbeitsdatei, ihr müsst sie nicht committen.

**KI-Check:** Kam in der Pause auf „Sag Moin.“ im Continue-Chat eine Antwort? Dann ist Schritt 2
vorbereitet. Wer die Konfiguration in der Pause nicht geschafft hat, legt sie jetzt nach `SETUP.md`
an. Der Rest des Teams startet schon mit dem Setup-Check.

**Checkpoint 0:** Hängt ihr hier länger als 5 Minuten, arbeitet ihr mit einem Team zusammen, dessen
Setup läuft. Endpunkt-Probleme meldet ihr dem Dozenten. Das eigene Setup zieht ihr nach dem Lab oder
zu Hause nach.

---

## Schritt 1: Linter laufen lassen und Befunde gewichten (10 min)

```bash
pylint src/ --reports=y
flake8 src/ --max-line-length 120
```

So lest ihr eine Zeile der pylint-Ausgabe:

```text
src/stats.py:1:0: W0102: Dangerous default value [] as argument (dangerous-default-value)
```

| Datei | Zeile:Spalte | Meldungs-ID | Text | Name der Regel |
|---|---|---|---|---|
| `src/stats.py` | `1:0` | `W0102`: Kategorie W, Nummer 0102 | Dangerous default value [] as argument | `dangerous-default-value` |

**Gefährlich heißt:** Der Befund kann im Betrieb falsches Verhalten erzeugen oder einen Fehler
verstecken.

**Aufgaben:**

1. Zählt die Befunde pro Pylint-Kategorie: C (Convention), R (Refactor), W (Warning), E (Error).
   Mit `--reports=y` steht die Zählung unter „Messages by category“.
2. Sucht je ein Beispiel für eine reine Stilkonvention (C), einen möglichen Bug (W) und einen
   Refactoring-Kandidaten (R).
3. Wählt die **drei gefährlichsten** Befunde aus und begründet eure Wahl in je einem Satz.
4. Füllt in der Befundtabelle „Gemeldet von“ für die Zeilen 1 bis 6, 8 und 9 mit der konkreten
   Ausgabezeile (`Datei:Zeile: ID`). Wo schlägt kein Werkzeug an?

<details>
<summary>Zur Selbstkontrolle</summary>

- pylint meldet **38 Befunde**: 23 C, 12 W, 3 R, 0 E. Unter „Messages by category“ steht das als
  `convention 23`, `refactor 3`, `warning 12`, `error 0`. Die letzte Zeile lautet
  `Your code has been rated at 7.08/10`. Ab dem zweiten Lauf steht dahinter `(previous run: …)`.
- Der Exit-Code ist **28**. Er ist eine Bitmaske: 16 (C) + 8 (R) + 4 (W). Prüfen könnt ihr das mit
  `echo $?` direkt nach dem pylint-Aufruf (PowerShell: `echo $LASTEXITCODE`).
- flake8 meldet mit `--max-line-length 120` **17 Befunde**. Ohne die Option (Grenze 79 Zeichen) sind es 26.
- Beispiele: C `C0103 invalid-name` für `TXT`, `C0121` für `found == False`. W `W0702 bare-except`,
  `W0102 dangerous-default-value` für `extra=[]`, `W0622 redefined-builtin` für `filter`.
  R `R0912 too-many-branches`, `R1732 consider-using-with`.
- Kandidaten für die gefährlichsten Befunde sind `except:` ohne Typ, `== None`, veränderbare
  Default-Argumente und globaler Zustand.
- Ein guter Kandidat für die gefährlichsten drei: `W0702` (versteckt jeden Fehler, siehe Check 3),
  `W0603` (globaler Cache liefert veraltete Daten) und `W0611` für `requests` (der Import täuscht eine
  Nutzung vor, und das Paket bringt verwundbare Abhängigkeiten mit, siehe Schritt 3). `W0102` ist
  als Muster gefährlich, hier aber folgenlos, weil `extra` nie benutzt wird.
- Aufgabe 4: Die Ausgabezeilen für die Zeilen 1 bis 6 stehen in der Selbstkontrolle unter der
  Befundtabelle. Bei 8 und 9 schlägt kein Werkzeug an, bei 5 und 6 nur teilweise.

</details>

---

## Schritt 2: KI-Assistent fixen lassen und den Diff reviewen (20 min)

Ihr arbeitet in **drei Runden**, eine Datei pro Runde. So bleibt jeder Diff klein genug für ein
echtes Review, und der Kurs-Endpunkt bekommt nur kurze Aufträge.

### So geht es in Continue

1. Öffnet die Datei und markiert den gesamten Inhalt (Cmd/Ctrl + A).
2. Drückt **Cmd/Ctrl + I** (Edit-Modus), gebt den Auftrag ein und bestätigt mit Enter.
3. Continue zeigt die Änderungen als Diff direkt im Editor. Alle annehmen: **Cmd/Ctrl + Shift + Enter**.
   Alle ablehnen: Cmd + Shift + Delete (macOS) bzw. Ctrl + Shift + Backspace (Windows, Linux).
   Einzelne Blöcke nehmt ihr mit Cmd + Opt + Y bzw. Ctrl + Alt + Y an und lehnt sie mit
   Cmd + Opt + N bzw. Ctrl + Alt + N ab.
4. Tipp: Kopiert die Ausgabe von `pylint src/<datei>` in den Auftrag. Bietet eure Continue-Version im
   Chat `@Terminal` an, schickt das den letzten Terminal-Befehl samt Ausgabe mit.

Im Chat gibt es zusätzlich den Agent-Modus. Er ändert Dateien selbstständig und fragt vorher um
Erlaubnis. Für dieses Lab reicht der Edit-Modus.

### Der Auftrag

Nutzt in jeder Runde denselben Auftrag. Ihr tauscht nur den Dateinamen aus.

> Behebe alle pylint- und flake8-Findings in src/stats.py. Halte dich an PEP 8 und Clean Code:
> sprechende Namen, Type Hints, Docstrings, keine Duplikation, kein globaler Zustand.
> Verändere das Verhalten nicht. `python -m pytest` muss grün bleiben.

### Ablauf jeder Runde

1. Auftrag abschicken, Diff lesen, annehmen oder ablehnen.
2. Sicherheitsnetz laufen lassen (Check 1 bis 3).
3. `pylint src/<datei>` ausführen und die Review-Checkliste durchgehen.
4. Wenn ihr den Diff behalten wollt: `git commit -am "Runde A: stats.py"`. Jede Runde ist dann ein
   eigener Checkpoint. Wenn nicht: `git restore src/<datei>`.
5. Tragt in der Befundtabelle die Spalte „Von der KI behoben?“ ein.

### Review-Checkliste

- [ ] Sind alle drei Checks des Sicherheitsnetzes unverändert?
- [ ] Wie viele pylint-Befunde sind in der Datei übrig?
- [ ] Wurden Befunde behoben oder nur unterdrückt? `git grep -n -e "noqa" -e "pylint: disable" -- src/`
- [ ] Wo hat die KI nur kosmetisch umbenannt, statt die Duplikation zu entfernen?
- [ ] Hat sich eine Schnittstelle geändert, also Parameter, Rückgabetyp oder Funktionsname?
- [ ] Euer Auftrag verlangt zwei Dinge, die sich widersprechen können. Welches hat die KI geopfert,
      und hat sie es gesagt?
- [ ] Würdet ihr diesen Diff als Pull Request approven?

Der pylint-Score ist ein **Indiz, kein Nachweis**. Eine KI kann ihn auch mit `# pylint: disable`
oder inhaltsleeren Docstrings nach oben treiben.

### Runde A: `src/stats.py` (6 min)

Worauf ihr achtet: Entfernt die KI die acht Zählschleifen, zum Beispiel mit `collections.Counter`,
oder benennt sie nur `h`, `s` und `z` um? Bleibt die Beschriftung `Prioritaeten` exakt gleich?
Der Report-Vergleich zeigt jede Abweichung.

<details>
<summary>Zur Selbstkontrolle</summary>

Ein guter Diff zählt mit `collections.Counter` und druckt Zeichen für Zeichen denselben Report.
Check 1 bis 3 bleiben unverändert. Viele Assistenten entfernen dabei den ungenutzten Parameter
`extra`. Das ist eine Schnittstellenänderung, hier aber harmlos, weil niemand ihn übergibt.
„Verbessert“ die KI `Prioritaeten` zu `Prioritäten`, zeigt Check 2 eine Zeile Unterschied. Das ist
eine Verhaltensänderung, auch wenn sie gut gemeint ist.

</details>

### Runde B: `src/ticket_loader.py` (7 min)

Das ist die Datei mit dem stillen Fehlschlag vom Anfang der Vorlesung. Zwei Vorgaben eures Auftrags
widersprechen sich hier. Welche?

Zusatzcheck für diese Runde: Liefert ein zweiter Aufruf mit anderem Pfad noch die alten Daten?

```bash
python -c "from src.ticket_loader import load_tickets; load_tickets(); print(len(load_tickets('fehlt.json')))"
```

Auf `vl01-start` gibt das `30` aus, obwohl `fehlt.json` gar nicht existiert.

<details>
<summary>Zur Selbstkontrolle</summary>

Der Zielkonflikt liegt zwischen „kein globaler Zustand“ und „Verändere das Verhalten nicht“. Der
globale Cache liefert beim zweiten Aufruf mit anderem Pfad die alten Daten (Zusatzcheck: `30`).
Genau das ist heutiges Verhalten. Wer den Cache entfernt, ändert es. `W0702` allein lässt sich
dagegen ohne Verhaltensänderung beheben: gezielt abfangen und weiter `[]` liefern. Das Prinzip
Fehlerhandling zieht zusätzlich in Richtung Exception statt `[]`.

Beim Fehlerfall sind zwei Ergebnisse typisch:

- **Variante 1:** Die KI lässt den Fehler durch. Check 3 zeigt dann einen `FileNotFoundError`
  statt `0`. Tests und Report bleiben trotzdem gleich. **Das Verhalten hat sich geändert, und kein
  Test hat es bemerkt.**
- **Variante 2:** Die KI fängt gezielt `FileNotFoundError` und `json.JSONDecodeError` ab und liefert
  weiter `[]`. Check 3 bleibt bei `0`. Der Befund `W0702` ist weg, der stille Fehlschlag bleibt.

Außerdem häufig:

- Die KI ersetzt `global CACHE` durch `functools.lru_cache` oder entfernt den Cache ganz. Dann gibt
  der Zusatzcheck keine `30` mehr aus.
- Die KI entfernt den ungenutzten Parameter `filter` oder baut eine Filterfunktion ein, die niemand
  bestellt hat.

Welche Variante richtig ist, ist eine fachliche Entscheidung. Entscheidend ist, dass sie bewusst
fällt und im Pull Request steht. Die Musterlösung wählt Variante 1 und cacht pro Pfad. Ihr README
listet diese Verhaltensänderungen ausdrücklich auf.

</details>

### Runde C: `src/triage.py` (7 min)

Worauf ihr achtet: Die Reihenfolge der Regeln ist Verhalten, denn der erste Treffer gewinnt.
`test_zugang_vor_netzwerk` schützt genau einen Fall, der Report-Vergleich schützt den Rest.
Hat die KI Keywords, Reihenfolge oder die Suchlogik „verbessert“?

<details>
<summary>Zur Selbstkontrolle</summary>

Ein guter Diff legt die Keywords als Daten ab (ein Dict pro Regelart) und prüft sie mit einer
kleinen Hilfsfunktion in fester Reihenfolge. Die 21 Verzweigungen verschwinden, und Check 2 bleibt
leer. Ändert die KI die Suchlogik, zum Beispiel auf ganze Wörter, ändern sich einzelne Zeilen im
Report. Die 5 Tests bleiben dabei oft grün.

</details>

**Checkpoint 2:** Nach 20 Minuten geht es mit Schritt 3 weiter, auch wenn Runde C fehlt. Runde C holt
ihr zu Hause nach. Wer keinen KI-Zugang hatte, wendet die Review-Checkliste auf den Diff der
Musterlösung an: `git diff origin/vl01-start origin/vl01-solution -- src/stats.py`.

---

## Schritt 3: Abhängigkeiten mit Trivy scannen (10 min)

```bash
trivy fs --skip-dirs .venv .
```

Trivy gleicht `requirements.txt` mit CVE-Datenbanken ab. Standardmäßig sucht Trivy außerdem nach
Secrets. `--skip-dirs .venv` erspart ihm, dabei eure ganze virtuelle Umgebung zu durchsuchen.

Zur Erinnerung die Kurs-Faustregel:

| Schweregrad | CVSS | Reaktion im Projekt |
|---|---|---|
| Kritisch | 9.0 bis 10.0 | sofortiger Hotfix, Pipeline stoppt |
| Hoch | 7.0 bis 8.9 | sofortiger Hotfix, Pipeline stoppt |
| Mittel | 4.0 bis 6.9 | Fix im nächsten Sprint |
| Niedrig | 0.1 bis 3.9 | Backlog-Ticket |

CVSS misst den Schweregrad einer Lücke, nicht euer Risiko. Ob die Lücke bei euch überhaupt erreichbar
ist, prüft ihr in Aufgabe 4.

**Aufgaben:**

1. Wie viele Findings meldet Trivy, und wie viele davon sind HIGH oder CRITICAL?
2. Sucht euch eine CVE aus und lest sie über den Link in der Trivy-Ausgabe oder auf
   [nvd.nist.gov](https://nvd.nist.gov) nach. Was ist das Problem, und ab welcher Version ist es behoben?
3. Was muss laut Faustregel heute noch passieren?
4. Welche der betroffenen Pakete nutzt `src/` überhaupt? Prüft es mit
   `git grep -n -E "^(import|from) " -- src/`. Was ist hier die beste Behebung?
   Tragt Zeile 7 in die Befundtabelle ein.

<details>
<summary>Zur Selbstkontrolle</summary>

- Stand 25.09.2026 meldet Trivy **12 Findings: 4 HIGH, 8 MEDIUM, 0 CRITICAL.** Neue CVEs können
  hinzukommen, die Zahl kann also steigen.
- Betroffen sind `Jinja2` 3.1.4 (3 MEDIUM), `pytest` 8.3.3 (1 MEDIUM), `requests` 2.32.3 (2 MEDIUM) und
  `urllib3` 2.2.3 (4 HIGH, 2 MEDIUM).
- Den Schweregrad übernimmt Trivy meist aus der GitHub Advisory Database. Der Wert auf nvd.nist.gov
  kann davon abweichen.
- Faustregel: Die vier HIGH-Findings in `urllib3` verlangen einen sofortigen Fix, die Pipeline würde stoppen.
- Aufgabe 4: `src/` importiert nur `requests`, und zwar ungenutzt (`W0611`). `urllib3` kommt nur als
  Abhängigkeit von `requests` ins Projekt. `Jinja2` und `PyYAML` importiert niemand. `pytest` ist ein
  Entwicklungswerkzeug. Die beste Behebung ist deshalb: `import requests` löschen und `requests`,
  `urllib3`, `certifi`, `PyYAML`, `Jinja2` und `MarkupSafe` aus `requirements.txt` entfernen.
  Nur `pytest` braucht ein Update. **Die sicherste Abhängigkeit ist die, die ihr nicht habt.**
- Die Musterlösung aktualisiert die Versionen, lässt den Pin für `MarkupSafe` weg (Jinja2 bringt es
  selbst mit) und trägt `litellm` für VL 3 schon ein. So kommt sie auf 0 Findings. Ob das die bessere
  Wahl ist, diskutiert ihr in Reflexionsfrage 4.

</details>

---

## Debrief (5 min, im Plenum)

Der Dozent zeigt den Diff der Musterlösung und stoppt bei `ticket_loader.py`. Wer nacharbeitet,
führt den Befehl selbst aus:

```bash
git diff origin/vl01-start origin/vl01-solution -- src/ticket_loader.py
```

| | `vl01-start` | `vl01-solution` |
|---|---|---|
| Tests | 5 passed | 5 passed |
| pylint | 38 Befunde, 7.08/10 | 0 Befunde, 10.00/10 |
| Trivy | 12 Findings, davon 4 HIGH | 0 Findings (Stand 25.09.2026) |
| Fehlende Ticket-Datei | „Anzahl Tickets: 0“, Exit-Code 0 | `FileNotFoundError`, Exit-Code 1 |

Kein Test hat die Änderung in der letzten Zeile bemerkt. Füllt zum Abschluss die Spalte „Review nötig?“
der Befundtabelle aus.

**Merge-Runde:** Approve oder request changes für euren Runde-B-Diff? Nennt einen Grund aus
Sicherheitsnetz oder Review-Checkliste.

Schaut euch dann im Report die Zeile zu T-1003 an. Der Code ist jetzt sauber. Ist er auch richtig?

---

## Offene Übung: Eigener Code unter der Lupe (22 min + 8 min Ergebnisrunde)

Nehmt euren **eigenen Code** aus Job, Studium oder Hobby. Wer nichts dabeihat, arbeitet im
LeineTech-Repo weiter (zum Beispiel an `src/main.py`).

1. **Linter:** `pylint` und `flake8` laufen lassen und 3 interessante Befunde notieren.
2. **KI-Fix:** Continue die Befunde beheben lassen, Datei für Datei.
3. **Kritische Bewertung:** War der Vorschlag gut? Was war richtig, was falsch, was fehlt?
4. **Bonus:** Eine Funktion mit einem detaillierten Clean-Code-Auftrag neu schreiben lassen und mit
   dem Original vergleichen.

> **Datenschutz:** Nutzt nur Code, den ihr teilen dürft. Der Kurs-Endpunkt loggt alle Prompts.
> Im Zweifel arbeitet ihr im LeineTech-Repo weiter.

**Ergebnisrunde:** 3 bis 4 Teams zeigen je einen besonders **guten** und einen besonders
**schlechten** KI-Vorschlag. Leitfrage: Wann hilft der Assistent, und wann nicht?

---

## Reflexionsfragen

Beantwortet die Fragen nach dem Lab schriftlich, je zwei bis drei Sätze.

1. Welche Verhaltensänderung aus Schritt 2 hätte keiner der 5 Tests bemerkt? Wie hättet ihr sie
   ohne Check 3 gefunden?
2. Die Musterlösung wirft bei fehlender Datei einen Fehler, statt still eine leere Liste zu liefern.
   Ist das eine Verbesserung? Wo muss so eine Änderung stehen, damit ein Reviewer sie nicht übersieht?
3. Welche zwei Vorgaben eures Auftrags widersprechen sich in `ticket_loader.py`? Warum geht beides
   nicht gleichzeitig, und was hat die KI daraus gemacht?
4. `requests`, `PyYAML` und `Jinja2` werden nirgends benutzt. Was ist die beste Behebung ihrer CVEs?
   Welche Gründe könnte es geben, sie trotzdem zu behalten und nur zu aktualisieren?
5. Wie könntet ihr den pylint-Score auf 10/10 bringen, ohne den Code besser zu machen? Was folgt
   daraus für ein CI-Gate mit `--fail-under`?
6. Würdet ihr euren Diff mergen? Begründet eure Entscheidung mit den Ergebnissen des Sicherheitsnetzes
   und des Reviews.

---

## Bonus für Schnelle

**B1: CI-Gate simulieren.** Ein Gate lässt nur Code durch, dessen Score über der Schwelle liegt.

```bash
pylint src/ --fail-under=9
echo $?                                # PowerShell: echo $LASTEXITCODE
```

Auf `vl01-start` ist der Exit-Code 28, das Gate wäre rot. Mit `--fail-under=7` ist er 0, weil 7.08
über 7 liegt. Die Musterlösung besteht beide Schwellen mit Exit-Code 0.

**B2: Einen Test für den stillen Fehlschlag schreiben.** Legt `tests/test_ticket_loader.py` an. Schreibt
einen Test, der prüft, dass eine fehlende Datei einen `FileNotFoundError` auslöst, und einen zweiten,
der zwei verschiedene Dateien nacheinander lädt. Auf `vl01-start` müssen beide Tests rot sein. Mit
Variante 1 aus Runde B werden beide grün. Mit Variante 2 bleibt der erste Test rot, und genau diese
Entscheidung hält der Test dann fest.

<details>
<summary>Lösungsvorschlag</summary>

```python
"""Tests für das Laden der Tickets."""

import pytest

from src.ticket_loader import load_tickets


def test_fehlende_datei_wird_gemeldet(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_tickets(tmp_path / "fehlt.json")


def test_anderer_pfad_liefert_andere_daten(tmp_path):
    erste = tmp_path / "erste.json"
    zweite = tmp_path / "zweite.json"
    erste.write_text('[{"id": "T-1"}]', encoding="utf-8")
    zweite.write_text('[{"id": "T-2"}, {"id": "T-3"}]', encoding="utf-8")
    assert len(load_tickets(erste)) == 1
    assert len(load_tickets(zweite)) == 2
```

Auf `vl01-start` meldet `python -m pytest` damit `2 failed, 5 passed`, auf der Musterlösung `7 passed`.
Genau so hätte das Team den stillen Fehlschlag vor dem Refactoring festhalten können.

</details>

**B3: Abhängigkeiten aufräumen.** Setzt die beste Behebung aus Schritt 3 um oder lasst die KI
`requirements.txt` aktualisieren. Prüft jede vorgeschlagene Version, bevor ihr sie übernehmt:

```bash
pip index versions requests            # zeigt die neueste und alle verfügbaren Versionen
```

LLMs erfinden gelegentlich Versionen, die es nicht gibt. Danach `pip install -r requirements.txt`,
`python -m pytest` und `trivy fs --skip-dirs .venv .` ausführen.

**B4: `src/main.py`.** Lasst die KI auch die letzte Datei aufräumen und prüft sie mit dem Sicherheitsnetz.

---

## Troubleshooting

| Problem | Lösung |
|---|---|
| `python: command not found` | Die virtuelle Umgebung ist nicht aktiv. `source .venv/bin/activate` (macOS, Linux), `source .venv/Scripts/activate` (Git Bash), `.venv\Scripts\activate` (PowerShell, cmd). |
| `error: externally-managed-environment` bei `pip install` | Ihr installiert ohne virtuelle Umgebung (PEP 668). Legt die venv wie oben an und aktiviert sie. |
| PowerShell blockiert `Activate.ps1` | Einmalig `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` ausführen oder Git Bash nutzen. |
| pylint bricht ab oder meldet unerwartete Fehler | Wahrscheinlich Python 3.14. Legt die venv neu an: `rm -rf .venv && python3.13 -m venv .venv` (macOS, falls nötig vorher `brew install python@3.13`), Windows `py -3.13 -m venv .venv`. |
| `ModuleNotFoundError: No module named 'src'` | Aus dem Projektordner starten und immer `python -m src.main` statt `python src/main.py` verwenden. |
| `pylint: command not found` | venv aktiv? Alternativ `python -m pylint src/` und `python -m flake8 src/`. |
| Trivy nicht installiert | macOS: `brew install trivy` · Windows: `winget install -e --id AquaSecurity.Trivy` · sonst: [trivy.dev](https://trivy.dev) |
| Trivy lädt lange die Datenbank | Vorher `trivy fs --download-db-only` ausführen. Ohne Netz mit vorhandener DB: `trivy fs --skip-db-update --skip-dirs .venv .` |
| Trivy läuft sehr lange | `--skip-dirs .venv` vergessen? Nur Schwachstellen scannen: `trivy fs --scanners vuln .` |
| Continue antwortet nicht | Cold Start: Die erste Antwort kann 200 bis 300 Sekunden dauern. Einmal warten, nicht abbrechen. |
| HTTP 403 in Continue | Außerhalb des Montagsfensters (06:00 bis 23:59 Uhr). Das ist Absicht, kein Fehler. |
| HTTP 401 in Continue | `apiKey` in `~/.continue/config.yaml` prüfen, siehe `SETUP.md`. |
| HTTP 429 in Continue | Zu viele Anfragen. Kurz warten und langsamer arbeiten. |
| Endpunkt dauerhaft nicht erreichbar | Mit einem Team arbeiten, dessen Zugang läuft, oder Schritt 2 später nachholen. Den Ersatzweg klärt der Dozent vor Ort. |
| Tab-Vervollständigung fehlt | Läuft Ollama? `ollama list` zeigt die geladenen Modelle. Fehlt das Modell: `ollama pull qwen2.5-coder:1.5b`. Wer `qwen2.5-coder:0.5b` nutzt, trägt es in `~/.continue/config.yaml` bei der Tab-Rolle unter `model:` ein. |
| Report-Vergleich zeigt Unterschiede | Die KI hat das Verhalten geändert. Diff lesen, dann annehmen oder `git restore src/<datei>`. |
| Report-Vergleich zeigt `Binary files … differ` | PowerShell 5 schreibt Umleitungen als UTF-16. Beide Reports in derselben Shell erzeugen oder Git Bash nutzen. |
| `git commit` meldet „Please tell me who you are“ | Einmalig `git config --global user.name "Vorname Nachname"` und `git config --global user.email "adresse@example.org"` setzen. |
| `git checkout vl01-solution` verweigert den Wechsel | Ihr habt ungesicherte Änderungen. Erst `git commit -am "Mein Lab-Stand"`, dann wechseln. Oder die Musterlösung nur als Diff ansehen (siehe Checkpoint-Branches). |
| KI-Setup noch nicht fertig | Zu zweit arbeiten und das eigene Setup nach dem Lab oder zu Hause nachziehen. |

---

## Musterlösung und Weiterarbeit

- Die Musterlösung liegt auf `vl01-solution`. Ihr `README.md` listet alle bewussten Verhaltensänderungen auf.
- **Optionale Hausaufgabe:** Bringt das Lab zu Ende: `pylint src/` ohne Befunde, `trivy fs --skip-dirs .venv .`
  ohne Findings, Vergleich mit `git diff origin/vl01-solution -- src/`. Analysiert außerdem eigenen
  Code mit pylint und dokumentiert 5 Befunde mit eurer Bewertung.
- **Vorbereitung auf VL 2:** Bringt den Laptop mit dem Setup von heute mit: VS Code mit Continue und
  Kurs-Key, Ollama mit `qwen2.5-coder:1.5b` und das Repo mit Terminal. Notfalls reicht ein Browser
  mit einem LLM-Chat. `data/tickets.json` lest ihr im Repo, im Browser findet ihr die Datei auf
  GitHub im Branch `vl01-solution`. `eval/golden.jsonl` öffnet ihr erst, wenn VL 2 es sagt.
- In VL 3 startet ihr auf `vl01-solution`.
