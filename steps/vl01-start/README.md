# LeineTech Ticket-Triage: `vl01-start`

Ausgangszustand für das Lab in **VL 1 (Software-Assistenten)**.

Dies ist das interne Ticket-Triage-Tool der LeineTech GmbH. Es liest Support-Tickets aus
`data/tickets.json`, ordnet sie per **Keyword-Regeln** einer Kategorie und Priorität zu und druckt
einen Report. Der Code **funktioniert**, aber er ist in schlechtem Zustand. Ein Kollege hat ihn
„mal schnell“ gebaut.

**Eure Aufgabe in VL 1:** den Zustand mit Linter, KI-Assistent und Artefakt-Scanner sichtbar machen
und verbessern. Die Anleitung steht in `labs/vl01-lab.md`. Als KI-Assistent nutzen wir
**VS Code mit Continue.dev** gegen den Kurs-Endpunkt (HomeCloud). Das Setup steht in `SETUP.md`.

## Voraussetzungen

- Python 3.12 oder 3.13. Python 3.14 funktioniert nicht, weil der Kurs pylint 3.3.1 pinnt.
- git
- Für das Lab zusätzlich VS Code mit Continue, Ollama und Trivy 0.70 oder neuer.
  Details stehen in `labs/vl01-lab.md`.

## Virtual Environment

In Python würden dependencies global installiert werden, dies würde dafür sorgen dass man viele verschiedene Versionen im globalen Namespace installiert, dies ist ein Anti-Pattern und eine der Lösungen dafür in Python ist das "Virtual Environment". Mit diesem Befehl:

```bash
# Könnte auch python3 auf eurem System sein
python -m venv .venv && source .venv/bin/activate
```

Wird ein Ordner `.venv` in eurem Projekt erstellt, in diesem befindet sich dann ein komplettes Python Environment, mit executables wie `pip`, `python` selbst und anderen. Funfact, ihr könnte dann auch `𝜋thon` benutzen als `python` alternative.

## Ausführen

```bash
python3 -m venv .venv              # bei Python 3.14: python3.13, Windows: py -3.12 -m venv .venv
source .venv/bin/activate          # Windows Git Bash: source .venv/Scripts/activate, PowerShell: .venv\Scripts\activate
pip install -r requirements.txt

python -m src.main                 # Triage-Report über alle 30 Tickets
python -m pytest                   # 5 Tests, vor und nach dem Refactoring grün
```

## Struktur

```
data/tickets.json   30 Support-Tickets (Mai 2026)
docs/               Knowledge-Base der LeineTech-IT (wird ab VL 4 wichtig)
eval/golden.jsonl   Von Menschen vergebene Soll-Labels (erst öffnen, wenn VL 2 es sagt)
src/                Das Triage-Tool (bewusst in schlechtem Zustand)
tests/              pytest-Tests, euer Sicherheitsnetz beim Refactoring
labs/vl01-lab.md    Schritt-für-Schritt-Anleitung für das Lab
```

Die Musterlösung liegt auf dem Branch `vl01-solution`. Schaut sie erst nach dem Lab an.
