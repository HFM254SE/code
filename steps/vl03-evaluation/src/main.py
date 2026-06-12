"""Einstiegspunkt der LeineTech-Ticket-Triage.

Subkommandos:
    triage              Regelbasierter Report über alle Tickets (Stand VL 1)
    summarize T-1003    LLM-Zusammenfassung eines Tickets
    classify T-1003     Regel- vs. LLM-Klassifikation im Vergleich
"""

import argparse

from src.llm import get_model
from src.stats import print_stats
from src.summarize import classify_ticket_llm, summarize_ticket
from src.ticket_loader import get_ticket, load_tickets
from src.triage import classify_and_prioritize, triage_all


def cmd_triage() -> None:
    tickets = list(load_tickets())
    print("LeineTech Ticket-Triage (regelbasiert)")
    print(f"Anzahl Tickets: {len(tickets)}")
    results = triage_all(tickets)
    for result in results:
        print(
            f"{result['id']} | {result['prioritaet'].upper():7} | "
            f"{result['kategorie']:10} | {result['betreff']}"
        )
    print_stats(results)


def cmd_summarize(ticket_id: str) -> None:
    ticket = _require_ticket(ticket_id)
    print(f"[{ticket['id']}] {ticket['betreff']}  (Modell: {get_model()})")
    print(summarize_ticket(ticket))


def cmd_classify(ticket_id: str) -> None:
    ticket = _require_ticket(ticket_id)
    regel_kategorie, regel_prioritaet = classify_and_prioritize(ticket)
    llm_result = classify_ticket_llm(ticket)
    print(f"[{ticket['id']}] {ticket['betreff']}")
    print(f"  Regeln (VL 1):       {regel_kategorie} / {regel_prioritaet}")
    print(
        f"  LLM ({get_model()}):  "
        f"{llm_result['kategorie']} / {llm_result['prioritaet']}"
    )


def _require_ticket(ticket_id: str) -> dict:
    ticket = get_ticket(ticket_id)
    if ticket is None:
        raise SystemExit(f"Ticket {ticket_id} nicht gefunden.")
    return ticket


def main() -> None:
    parser = argparse.ArgumentParser(description="LeineTech Ticket-Triage")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("triage", help="Regelbasierter Report über alle Tickets")
    p_sum = sub.add_parser("summarize", help="LLM-Zusammenfassung eines Tickets")
    p_sum.add_argument("ticket_id", metavar="TICKET-ID")
    p_cls = sub.add_parser("classify", help="Regel- vs. LLM-Klassifikation")
    p_cls.add_argument("ticket_id", metavar="TICKET-ID")

    args = parser.parse_args()
    if args.command == "triage":
        cmd_triage()
    elif args.command == "summarize":
        cmd_summarize(args.ticket_id)
    elif args.command == "classify":
        cmd_classify(args.ticket_id)


if __name__ == "__main__":
    main()
