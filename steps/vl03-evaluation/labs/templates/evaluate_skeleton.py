"""SKELETON für Lab VL 3, Teil 2 — nach src/evaluate.py kopieren und TODOs füllen.

Das Drumherum (Laden, CLI, CSV) ist fertig — eure Arbeit ist die Messlogik:
Klassifikation pro Ticket (Regeln + LLM) und die Accuracy-Berechnung.

    cp labs/templates/evaluate_skeleton.py src/evaluate.py
    python -m src.evaluate                 # nur Regeln, erste 10 Tickets
    python -m src.evaluate --llm           # + LLM
    python -m src.evaluate --llm --all     # alle 30 (Hausaufgabe, dauert!)
"""

import argparse
import csv
import json
import time
from pathlib import Path

from src.llm import get_model
from src.summarize import classify_ticket_llm
from src.ticket_loader import load_tickets
from src.triage import classify_and_prioritize

GOLDEN_PATH = Path("eval/golden.jsonl")
RESULTS_PATH = Path("eval/results.csv")


def load_golden(path: Path = GOLDEN_PATH) -> dict[str, dict]:
    """Lädt die Soll-Labels: Ticket-ID → {"kategorie", "prioritaet"}."""
    golden = {}
    with open(path, encoding="utf-8") as file:
        for line in file:
            if line.strip():
                entry = json.loads(line)
                golden[entry["id"]] = entry
    return golden


def evaluate(use_llm: bool = False, limit: int | None = 10) -> list[dict]:
    """Klassifiziert Tickets mit Regeln (und optional LLM) gegen die Soll-Labels.

    Liefert eine Liste von Zeilen-Dicts, z. B.:
    {"id": "T-1001", "gold_kategorie": ..., "regel_kategorie": ...,
     "regel_latenz_s": ..., "llm_kategorie": ..., "llm_latenz_s": ...}
    """
    golden = load_golden()
    tickets = [t for t in load_tickets() if t["id"] in golden]
    if limit:
        tickets = tickets[:limit]

    rows = []
    for ticket in tickets:
        gold = golden[ticket["id"]]
        row = {
            "id": ticket["id"],
            "gold_kategorie": gold["kategorie"],
            "gold_prioritaet": gold["prioritaet"],
        }

        # TODO 1: Regelbasierte Klassifikation (classify_and_prioritize)
        #   - Ergebnis in row["regel_kategorie"] / row["regel_prioritaet"]
        #   - Latenz messen (time.perf_counter) → row["regel_latenz_s"]

        # TODO 2: Wenn use_llm: LLM-Klassifikation (classify_ticket_llm)
        #   - Ergebnis in row["llm_kategorie"] / row["llm_prioritaet"]
        #   - Latenz → row["llm_latenz_s"]
        #   - Tipp: pro Ticket eine Fortschrittszeile printen, sonst wirkt es eingefroren

        rows.append(row)
    return rows


def accuracy(rows: list[dict], system: str, field: str) -> float:
    """Anteil korrekter Vorhersagen, z. B. accuracy(rows, "llm", "kategorie")."""
    # TODO 3: vergleiche row[f"{system}_{field}"] mit row[f"gold_{field}"]
    raise NotImplementedError


def print_report(rows: list[dict], use_llm: bool) -> None:
    print("\n" + "=" * 64)
    print(f"EVALUIERUNG auf {len(rows)} Tickets (Golden Dataset)")
    print("=" * 64)
    print(f"Regeln:  Kategorie {accuracy(rows, 'regel', 'kategorie'):.0%}  "
          f"Priorität {accuracy(rows, 'regel', 'prioritaet'):.0%}")
    if use_llm:
        print(f"LLM ({get_model()}):  Kategorie {accuracy(rows, 'llm', 'kategorie'):.0%}  "
              f"Priorität {accuracy(rows, 'llm', 'prioritaet'):.0%}")
    # TODO 4 (Bonus): durchschnittliche Latenz pro System ausgeben
    print("=" * 64)


def write_csv(rows: list[dict], path: Path = RESULTS_PATH) -> None:
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Details: {path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Triage-Evaluierung gegen Golden Dataset")
    parser.add_argument("--llm", action="store_true", help="zusätzlich das LLM evaluieren")
    parser.add_argument("--limit", type=int, default=10, help="nur die ersten N Tickets (Default: 10)")
    parser.add_argument("--all", action="store_true", help="alle Tickets evaluieren")
    args = parser.parse_args()

    rows = evaluate(use_llm=args.llm, limit=None if args.all else args.limit)
    print_report(rows, use_llm=args.llm)
    write_csv(rows)


if __name__ == "__main__":
    main()
