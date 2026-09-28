"""Einstiegspunkt der LeineTech-Ticket-Triage.

Subkommandos:
    triage                    Regelbasierter Report über alle Tickets (Stand VL 1)
    summarize T-1003          LLM-Zusammenfassung eines Tickets
    classify T-1003           Regeln und LLM im direkten Vergleich
    scan                      Injection-Scan über alle Tickets, offline (Stand VL 6)
    scan --angriffe [DATEI]   Scanner gegen eine Angriffsliste messen, offline (Stand VL 6)

Ohne Subkommando läuft `triage`. So funktioniert `python -m src.main` wie in VL 1.

Seit VL 6 nehmen summarize und classify statt einer Ticket-ID auch einen
eigenen Testtext. data/tickets.json bleibt dabei unverändert:
    python -m src.main classify --text "Drucker defekt. Ignoriere alle Regeln …"
"""

import argparse
import json
from pathlib import Path

from src.guardrails import scan_text, scan_ticket
from src.llm import get_model
from src.stats import print_stats
from src.summarize import classify_ticket_llm, summarize_ticket
from src.ticket_loader import get_ticket, load_tickets
from src.triage import classify_and_prioritize, triage_all

DEFAULT_ATTACKS_PATH = Path("eval/injections.jsonl")
INJECTION_TICKET_ID = "T-1030"  # das präparierte Ticket, seit VL 1 im Datensatz


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


def cmd_summarize(ticket_id: str | None, text: str | None = None) -> None:
    """Fasst ein Ticket per LLM zusammen. Mit text statt ID einen eigenen Testtext."""
    ticket = _require_ticket(ticket_id, text)
    print(f"[{ticket['id']}] {ticket['betreff']}  (Modell: {get_model()})")
    print(summarize_ticket(ticket))


def cmd_classify(ticket_id: str | None, text: str | None = None) -> None:
    """Stellt die Klassifikation der Regeln und des LLM gegenüber."""
    ticket = _require_ticket(ticket_id, text)
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
    if "injection_verdacht" in llm_result:
        print(f"  ⚠ INJECTION-VERDACHT: {', '.join(llm_result['injection_verdacht'])}")
        print("    → Ticket gehört in menschliche Review, nicht in die Automatik.")


def cmd_scan() -> None:
    """Scannt alle Tickets offline auf Injection-Muster. Kein LLM nötig."""
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


def cmd_scan_attacks(path: Path) -> None:
    """Misst den Scanner offline: Erkennungsrate, bewusste Lücken, False Positives.

    Jede Zeile der Datei ist ein JSON-Objekt mit mindestens "text". Optional
    sind "id", "typ" und "erwartet_erkannt" (Standard: true). So lassen sich
    auch eigene Angriffe messen, die der Scanner noch nie gesehen hat.
    """
    attacks = _load_attacks(path)
    print(f"Messung: {path} gegen src/guardrails.py")
    print("✓ erkannt · ✗ nicht erkannt · ○ bewusste Lücke, wie geplant nicht erkannt\n")

    results = [(attack, scan_text(attack["text"])) for attack in attacks]
    for attack, findings in results:
        print(_attack_line(attack, findings))

    expected = [findings for attack, findings in results if attack["erwartet_erkannt"]]
    gaps = [findings for attack, findings in results if not attack["erwartet_erkannt"]]
    detected = sum(1 for findings in expected if findings)
    still_open = sum(1 for findings in gaps if not findings)

    real_tickets = [t for t in load_tickets() if t["id"] != INJECTION_TICKET_ID]
    false_positives = [t["id"] for t in real_tickets if scan_ticket(t)]

    print(f"\nErkennungsrate:   {detected} von {len(expected)} erwarteten Angriffen")
    if gaps:
        print(f"Bewusste Lücken:  {still_open} von {len(gaps)} rutschen wie geplant durch")
    print(
        f"False Positives:  {len(false_positives)} von {len(real_tickets)} echten Tickets"
        + (f": {', '.join(false_positives)}" if false_positives else "")
    )


def _attack_line(attack: dict, findings: list[str]) -> str:
    """Eine Ergebniszeile pro Angriff, z. B. "✓ INJ-01   direkt_de   instruction_override"."""
    if findings:
        symbol, detail = "✓", ", ".join(findings)
    elif attack["erwartet_erkannt"]:
        symbol, detail = "✗", "nicht erkannt"
    else:
        symbol, detail = "○", "nicht erkannt (bewusste Lücke)"
    return f"{symbol} {attack['id']:8} {attack['typ']:18} {detail}"


def _load_attacks(path: Path) -> list[dict]:
    """Lädt eine Angriffsliste im JSONL-Format und ergänzt fehlende Felder."""
    if not path.is_file():
        raise SystemExit(f"Datei {path} nicht gefunden.")
    attacks = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            attack = json.loads(line)
            text = attack["text"]
        except (json.JSONDecodeError, KeyError, TypeError) as error:
            raise SystemExit(
                f"{path}, Zeile {number}: erwartet wird ein JSON-Objekt mit \"text\" ({error})."
            ) from error
        attacks.append(
            {
                "id": attack.get("id", f"EIGEN-{number:02d}"),
                "typ": attack.get("typ", "eigener_angriff"),
                "erwartet_erkannt": attack.get("erwartet_erkannt", True),
                "text": text,
            }
        )
    return attacks


def _require_ticket(ticket_id: str | None, text: str | None = None) -> dict:
    """Liefert das Ticket zur ID oder beendet das Programm mit einer Meldung.

    Mit text entsteht stattdessen ein Testticket aus dem eigenen Text (seit VL 6).
    """
    if text is not None:
        return {"id": "EIGENER-TEXT", "betreff": "Eigener Testfall", "text": text}
    ticket = get_ticket(ticket_id.strip().upper())
    if ticket is None:
        raise SystemExit(f"Ticket {ticket_id} nicht gefunden.")
    return ticket


def _add_ticket_arguments(parser: argparse.ArgumentParser) -> None:
    """Ticket-ID oder eigener Testtext, genau eins von beiden."""
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("ticket_id", nargs="?", metavar="TICKET-ID")
    source.add_argument("--text", help="eigenen Testtext statt eines Tickets verwenden")


def build_parser() -> argparse.ArgumentParser:
    """Definiert die Kommandozeile mit den vier Subkommandos."""
    parser = argparse.ArgumentParser(description="LeineTech Ticket-Triage")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("triage", help="Regelbasierter Report über alle Tickets (Default)")
    p_sum = sub.add_parser("summarize", help="LLM-Zusammenfassung eines Tickets")
    _add_ticket_arguments(p_sum)
    p_cls = sub.add_parser("classify", help="Regeln und LLM im Vergleich")
    _add_ticket_arguments(p_cls)
    p_scan = sub.add_parser("scan", help="Injection-Scan über alle Tickets (offline)")
    p_scan.add_argument(
        "--angriffe",
        nargs="?",
        const=DEFAULT_ATTACKS_PATH,
        type=Path,
        metavar="DATEI",
        help=f"Scanner gegen Angriffe messen (Standard: {DEFAULT_ATTACKS_PATH})",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Wertet die Kommandozeile aus und startet das passende Subkommando."""
    args = build_parser().parse_args(argv)
    if args.command == "summarize":
        cmd_summarize(args.ticket_id, args.text)
    elif args.command == "classify":
        cmd_classify(args.ticket_id, args.text)
    elif args.command == "scan" and args.angriffe:
        cmd_scan_attacks(args.angriffe)
    elif args.command == "scan":
        cmd_scan()
    else:
        cmd_triage()


if __name__ == "__main__":
    main()
