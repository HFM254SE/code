"""Einstiegspunkt: Triage-Report über alle LeineTech-Tickets."""

from src.stats import print_stats
from src.ticket_loader import load_tickets
from src.triage import triage_all


def main() -> None:
    tickets = list(load_tickets())
    print("LeineTech Ticket-Triage")
    print(f"Anzahl Tickets: {len(tickets)}")

    results = triage_all(tickets)
    for result in results:
        print(
            f"{result['id']} | {result['prioritaet'].upper():7} | "
            f"{result['kategorie']:10} | {result['betreff']}"
        )
    print_stats(results)


if __name__ == "__main__":
    main()
