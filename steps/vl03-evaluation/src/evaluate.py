"""Systematische Evaluierung: Keyword-Regeln vs. LLM auf dem Golden Dataset.

Genau das, was VL 3 (Teil 7) predigt: Standardbenchmarks sagen wenig über den
eigenen Use Case — also messen wir selbst. `eval/golden.jsonl` enthält die von
Menschen vergebenen Soll-Labels für alle 30 Tickets.

Beispiele:
    python -m src.evaluate                      # nur Regeln, erste 10 Tickets
    python -m src.evaluate --llm                # Regeln + LLM, erste 10 Tickets
    python -m src.evaluate --llm --all          # alle 30 (dauert auf CPU!)
    LLM_MODEL=qwen2.5:3b python -m src.evaluate --llm

Default ist --limit 10, damit eine LLM-Runde im Lab nur ~1 Minute dauert.
Der volle 30er-Lauf ist Hausaufgabe (--all).
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


def evaluate(use_llm: bool = False, limit: int | None = None) -> list[dict]:
    """Klassifiziert Tickets mit Regeln (und optional LLM) gegen die Soll-Labels."""
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

        start = time.perf_counter()
        regel_kategorie, regel_prioritaet = classify_and_prioritize(ticket)
        row["regel_kategorie"] = regel_kategorie
        row["regel_prioritaet"] = regel_prioritaet
        row["regel_latenz_s"] = round(time.perf_counter() - start, 4)

        if use_llm:
            start = time.perf_counter()
            llm_result = classify_ticket_llm(ticket)
            row["llm_kategorie"] = llm_result["kategorie"]
            row["llm_prioritaet"] = llm_result["prioritaet"]
            row["llm_latenz_s"] = round(time.perf_counter() - start, 2)
            print(
                f"{ticket['id']}: gold={gold['kategorie']:10} "
                f"regel={regel_kategorie:10} llm={llm_result['kategorie']:10} "
                f"({row['llm_latenz_s']}s)"
            )

        rows.append(row)
    return rows


def accuracy(rows: list[dict], system: str, field: str) -> float:
    """Anteil korrekter Vorhersagen, z. B. accuracy(rows, "llm", "kategorie")."""
    hits = sum(1 for r in rows if r.get(f"{system}_{field}") == r[f"gold_{field}"])
    return hits / len(rows) if rows else 0.0


def print_report(rows: list[dict], use_llm: bool) -> None:
    print("\n" + "=" * 64)
    print(f"EVALUIERUNG auf {len(rows)} Tickets (Golden Dataset)")
    print("=" * 64)
    print(f"{'':24}{'Kategorie':>12}{'Priorität':>12}{'Ø Latenz':>12}")
    regel_lat = sum(r["regel_latenz_s"] for r in rows) / len(rows)
    print(
        f"{'Keyword-Regeln (VL 1)':24}"
        f"{accuracy(rows, 'regel', 'kategorie'):>11.0%}"
        f"{accuracy(rows, 'regel', 'prioritaet'):>12.0%}"
        f"{regel_lat:>11.4f}s"
    )
    if use_llm:
        llm_lat = sum(r["llm_latenz_s"] for r in rows) / len(rows)
        print(
            f"{'LLM (' + get_model() + ')':24}"
            f"{accuracy(rows, 'llm', 'kategorie'):>11.0%}"
            f"{accuracy(rows, 'llm', 'prioritaet'):>12.0%}"
            f"{llm_lat:>11.2f}s"
        )
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
