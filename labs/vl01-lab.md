# Lab VL 1 — Software-Assistenten in Aktion

**Ziel:** Linter, KI-Assistent und Artefakt-Scanner auf ein echtes (schlechtes)
Projekt loslassen — und die Ergebnisse **kritisch bewerten**.

**Dauer:** ~45 Minuten geführt + ~35 Minuten offene Übung.

---

## Schritt 0 — Setup (10 min)

**A) Kursprojekt holen & starten**

```bash
git clone https://github.com/HFM254SE/code.git leinetech
cd leinetech
git checkout vl01-start
pip install -r requirements.txt

python -m src.main      # → Triage-Report über 30 Tickets
python -m pytest        # → alle Tests grün
```

Wenn beides läuft, ist das Projekt startklar. **Merkt euch: Die Tests sind euer
Sicherheitsnetz** — nach jedem (KI-)Refactoring müssen sie wieder grün sein.

**B) KI-Assistent einrichten — VS Code + Continue.dev gegen die HomeCloud**

Wir nutzen den **kostenlosen Kurs-Endpunkt (Nirk HomeCloud)** — kein Student
Pack, kein Cursor-Abo, keine ID-Verifikation. Vollständige Anleitung mit der
fertigen Config: **`SETUP.md`** im Repo-Root. Kurzfassung:

1. **VS Code** + die Extension **Continue** (continue.dev) installieren.
2. **Ollama** installieren und das Autocomplete-Modell ziehen (einmalig, ~1 GB,
   läuft auch auf der CPU):
   ```bash
   ollama run qwen2.5-coder:1.5b
   ```
3. **API-Key vom Dozenten** holen und `~/.continue/config.yaml` anlegen (Vorlage
   in `SETUP.md`): Chat/Edit läuft über die HomeCloud (`provider: vllm`),
   Tab-Completion lokal über Ollama.
4. **Smoke-Test:** Continue-Chat öffnen, „Sag Moin." schicken → es antwortet.
   (Erste Antwort kann beim *Cold Start* bis ~200 s dauern — einmal warten.)

> **Datenschutz:** Prompts und Antworten am Kurs-Endpunkt werden geloggt und sind
> eurem Key zuordenbar. Keine Passwörter, Secrets oder echten Personendaten in
> Prompts — im Zweifel anonymisieren.

---

## Schritt 1 — Linter laufen lassen (~10 min)

```bash
pylint src/
flake8 src/ --max-line-length 120
```

**Aufgaben:**
1. Notiert die **Anzahl Findings pro Pylint-Kategorie** (C / W / E / R).
2. Sucht je ein Beispiel für:
   - eine reine Stil-Konvention (C),
   - einen möglichen Bug (W),
   - einen Code-Smell / Refactoring-Kandidaten (R).
3. **Entscheidet selbst:** Welche 3 Findings sind die **gefährlichsten**? Notiert eure Begründung.
   (Tipp: `except:` ohne Exception-Typ, `== None`, veränderbare
   Default-Argumente, globaler Zustand …)

---

## Schritt 2 — KI-Assistent fixen lassen (~15 min)

Öffnet das Projekt in **VS Code** und nutzt **Continue.dev** (Chat bzw. die
„Edit"-Funktion, gegen die HomeCloud). Gebt dem Assistenten einen Auftrag, z. B.:

> Behebe alle pylint- und flake8-Findings in src/. Halte dich an PEP 8 und
> Clean-Code-Prinzipien: sprechende Namen, Type Hints, Docstrings, keine
> Duplikation, kein globaler Zustand. Verändere das Verhalten nicht —
> `python -m pytest` muss grün bleiben.

**Danach kritisch prüfen:**
1. `python -m pytest` — noch grün? `python -m src.main` — gleicher Output?
2. `pylint src/` — wie viele Findings sind übrig? Was hat die KI ignoriert?
3. Lest den Diff (`git diff`) **vollständig**:
   - Was hat die KI gut gelöst?
   - Wo hat sie nur Symptome kosmetisch beseitigt (z. B. Variable umbenannt
     statt Duplikation entfernt)?
   - Hat sie irgendwo Verhalten verändert, ohne es zu sagen?
4. Würdet ihr diesen Diff als Pull Request **approven**? Warum (nicht)?

---

## Schritt 3 — Trivy: Abhängigkeiten scannen (~10 min)

```bash
trivy fs .
```

Trivy prüft `requirements.txt` gegen CVE-Datenbanken. Die gepinnten Versionen
sind veraltet — ihr werdet fündig.

**Aufgaben:**
1. Wie viele CVEs findet Trivy? Wie viele davon **HIGH/CRITICAL**?
2. Sucht euch eine CVE aus und schaut sie auf nvd.nist.gov an:
   Was ist das Problem? Ab welcher Version ist es behoben?
3. Was müsste laut der CVSS-Faustregel (> 7.0 → sofort fixen) **heute noch**
   passieren?
4. Bonus: Lasst den KI-Assistenten die `requirements.txt` aktualisieren und
   prüft mit `trivy fs .` + `python -m pytest` nach.

---

## Offene Übung — Eigener Code unter der Lupe (~35 min)

Nehmt euren **eigenen Code** (Job, Studium, Hobbyprojekt) — wer nichts dabei
hat, arbeitet weiter im LeineTech-Repo:

1. **Linter:** `pylint` / `flake8` laufen lassen → 3 interessante Findings notieren.
2. **KI-Fix:** Continue.dev die Findings beheben lassen.
3. **Kritische Bewertung:** War der Vorschlag gut? Was war richtig / falsch / fehlt?
4. **Bonus:** Eine Funktion mit einem detaillierten Clean-Code-Prompt komplett
   neu schreiben lassen und mit dem Original vergleichen.

**Ergebnisrunde:** Jede Person zeigt einen besonders **guten** und einen
besonders **schlechten** KI-Vorschlag.

---

## Troubleshooting

| Problem | Lösung |
|---|---|
| `ModuleNotFoundError: src` | Aus dem Repo-Root starten: `python -m src.main` |
| `pylint: command not found` | `pip install -r requirements.txt` (oder `pipx install pylint`) |
| Trivy nicht installiert | macOS: `brew install trivy` · Windows: `winget install trivy` · sonst: [aquasecurity.github.io/trivy](https://aquasecurity.github.io/trivy/) |
| Continue antwortet nicht / Timeout | Cold Start (bis ~200 s) abwarten; sonst Endpunkt-Status prüfen oder **Plan B (Groq)** — s. `SETUP.md` |
| HTTP 401 in Continue | `apiKey` in `~/.continue/config.yaml` prüfen — s. `SETUP.md` |
| Tab-Completion fehlt | Läuft Ollama? `ollama list` / `ollama run qwen2.5-coder:1.5b` (Autocomplete ist lokal) |
| KI-Setup noch nicht fertig | Zu zweit arbeiten (Pairing ist eh erwünscht) — Setup in der Pause nachziehen |

**Musterlösung:** `git checkout vl01-solution` (erst nach dem Lab anschauen!)
