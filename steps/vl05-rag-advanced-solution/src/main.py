"""Einstiegspunkt der LeineTech-Ticket-Triage.

Subkommandos:
    triage              Regelbasierter Report über alle Tickets (Stand VL 1)
    summarize T-1003    LLM-Zusammenfassung eines Tickets
    classify T-1003     Regeln und LLM im direkten Vergleich

Ohne Subkommando läuft `triage`. So funktioniert `python -m src.main` wie in VL 1.
"""

import argparse

from src.llm import get_model
from src.stats import print_stats
from src.summarize import classify_ticket_llm, summarize_ticket
from src.ticket_loader import get_ticket, load_tickets
from src.triage import classify_and_prioritize, triage_all


def cmd_triage() -> None:
    """Druckt den regelbasierten Report über alle Tickets."""
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
    """Fasst ein Ticket per LLM zusammen."""
    ticket = _require_ticket(ticket_id)
    print(f"[{ticket['id']}] {ticket['betreff']}  (Modell: {get_model()})")
    print(summarize_ticket(ticket))


def cmd_classify(ticket_id: str) -> None:
    """Stellt die Klassifikation der Regeln und des LLM gegenüber."""
    ticket = _require_ticket(ticket_id)
    regel_kategorie, regel_prioritaet = classify_and_prioritize(ticket)
    llm_result = classify_ticket_llm(ticket)
    print(f"[{ticket['id']}] {ticket['betreff']}")
    print(f"  Regeln (VL 1):  {regel_kategorie} / {regel_prioritaet}")
    print(f"  LLM ({get_model()}):  {llm_result['kategorie']} / {llm_result['prioritaet']}")
    if llm_result.get("parse_fehler"):
        print("  Achtung: Antwort nicht auswertbar, Rückfall auf die Defaults.")
    if "completion_tokens" in llm_result:
        print(
            f"  Tokens: {llm_result['prompt_tokens']} ein, "
            f"{llm_result['completion_tokens']} aus"
        )


def _require_ticket(ticket_id: str) -> dict:
    """Liefert das Ticket zur ID oder beendet das Programm mit einer Meldung."""
    ticket = get_ticket(ticket_id.strip().upper())
    if ticket is None:
        raise SystemExit(f"Ticket {ticket_id} nicht gefunden.")
    return ticket


def build_parser() -> argparse.ArgumentParser:
    """Definiert die Kommandozeile mit den drei Subkommandos."""
    parser = argparse.ArgumentParser(description="LeineTech Ticket-Triage")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("triage", help="Regelbasierter Report über alle Tickets (Default)")
    p_sum = sub.add_parser("summarize", help="LLM-Zusammenfassung eines Tickets")
    p_sum.add_argument("ticket_id", metavar="TICKET-ID")
    p_cls = sub.add_parser("classify", help="Regeln und LLM im Vergleich")
    p_cls.add_argument("ticket_id", metavar="TICKET-ID")
    return parser


def main(argv: list[str] | None = None) -> None:
    """Wertet die Kommandozeile aus und startet das passende Subkommando."""
    args = build_parser().parse_args(argv)
    if args.command == "summarize":
        cmd_summarize(args.ticket_id)
    elif args.command == "classify":
        cmd_classify(args.ticket_id)
    else:
        cmd_triage()


if __name__ == "__main__":
    main()
