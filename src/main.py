"""Einstiegspunkt der LeineTech-Ticket-Triage.

Subkommandos:
    triage              Regelbasierter Report über alle Tickets (Stand VL 1)
    summarize T-1003    LLM-Zusammenfassung eines Tickets
    classify T-1003     Regel- vs. LLM-Klassifikation im Vergleich
    scan                Injection-Scan über alle Tickets (Stand VL 6)
"""

import argparse

from src.guardrails import scan_ticket
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
    if "injection_verdacht" in llm_result:
        print(f"  ⚠ INJECTION-VERDACHT: {', '.join(llm_result['injection_verdacht'])}")
        print("    → Ticket gehört in menschliche Review, nicht in die Automatik.")


def cmd_scan() -> None:
    """Offline-Scan aller Tickets auf Injection-Muster — kein LLM nötig."""
    tickets = list(load_tickets())
    verdaechtig = 0
    for ticket in tickets:
        findings = scan_ticket(ticket)
        if findings:
            verdaechtig += 1
            print(f"⚠ {ticket['id']} | {ticket['betreff']}")
            print(f"   Muster: {', '.join(findings)}")
    print(f"\n{verdaechtig} von {len(tickets)} Tickets auffällig.")
    if verdaechtig == 0:
        print("Keine bekannten Injection-Muster gefunden.")


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
    sub.add_parser("scan", help="Injection-Scan über alle Tickets (offline)")

    args = parser.parse_args()
    if args.command == "triage":
        cmd_triage()
    elif args.command == "summarize":
        cmd_summarize(args.ticket_id)
    elif args.command == "classify":
        cmd_classify(args.ticket_id)
    elif args.command == "scan":
        cmd_scan()


if __name__ == "__main__":
    main()
