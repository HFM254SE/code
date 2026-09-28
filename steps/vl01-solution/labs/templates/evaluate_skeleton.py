"""SKELETON für Lab VL 3, Teil 2: nach src/evaluate.py kopieren und TODOs füllen.

    cp labs/templates/evaluate_skeleton.py src/evaluate.py

Das Drumherum (Laden, CLI, CSV, Report) ist fertig. Eure Arbeit ist die
Messlogik: Regeln messen (TODO 2.1), Accuracy berechnen (TODO 2.2) und das
LLM robust messen (TODO 2.3). Fertig ist das Modul, wenn
`python -m pytest tests/test_evaluate.py` grün ist.

T-1001 bis T-1010 kennt ihr aus VL 2. Das sind die Entwicklungsdaten, an
denen ihr den Prompt verbessern dürft. Die übrigen 20 Tickets sind Testdaten.

Aus dem Repo-Root starten:
    python -m src.evaluate                            # nur Regeln, erste 10 Tickets
    python -m src.evaluate --llm                      # Regeln und LLM, erste 10 Tickets
    python -m src.evaluate --llm --all                # alle 30 Tickets, dauert Minuten
    python -m src.evaluate --llm --csv eval/lauf2.csv # Ergebnis in eigene Datei
"""

import argparse
import csv
import json
import os
import statistics
import time  # noqa: F401  (braucht ihr in TODO 2.1 und 2.3)
from collections import Counter
from pathlib import Path

from src.llm import get_model
from src.summarize import classify_ticket_llm  # noqa: F401  (TODO 2.3)
from src.ticket_loader import load_tickets
from src.triage import classify_and_prioritize  # noqa: F401  (TODO 2.1)

GOLDEN_PATH = Path("eval/golden.jsonl")
RESULTS_PATH = Path("eval/results.csv")
DEV_IDS = frozenset(f"T-{number}" for number in range(1001, 1011))  # aus VL 2 bekannt
MAX_ERRORS_IN_A_ROW = 3  # danach ist der Endpunkt vermutlich nicht erreichbar
REPORT_WIDTH = 74
SYSTEM_NAMES = {"regel": "Regeln", "llm": "LLM"}
# Aus diesen Paketen kommen die Fehler von Endpunkt und Netz (Timeout, 401, 403, 429).
ENDPOINT_ERROR_PACKAGES = frozenset({"litellm", "openai", "httpx", "httpcore"})


def load_golden(path: Path = GOLDEN_PATH) -> dict[str, dict]:
    """Lädt die Soll-Labels: Ticket-ID → {"kategorie", "prioritaet"}."""
    if not path.exists():
        raise SystemExit(f"{path} nicht gefunden. Startet den Befehl im Repo-Root.")
    golden = {}
    with open(path, encoding="utf-8") as file:
        for line in file:
            if line.strip():
                entry = json.loads(line)
                golden[entry["id"]] = entry
    return golden


# --- Messung -----------------------------------------------------------------


def evaluate(use_llm: bool = False, limit: int | None = None) -> list[dict]:
    """Klassifiziert Tickets mit den Regeln und optional per LLM.

    Liefert eine Zeile pro Ticket. Nach MAX_ERRORS_IN_A_ROW Endpunkt-Fehlern in
    Folge oder nach Strg+C endet der Lauf. Die bisherigen Zeilen bleiben erhalten.
    """
    golden = load_golden()
    tickets = [ticket for ticket in load_tickets() if ticket["id"] in golden]
    if limit is not None:
        tickets = tickets[:limit]

    rows: list[dict] = []
    errors_in_a_row = 0
    try:
        for ticket in tickets:
            row = evaluate_ticket(ticket, golden[ticket["id"]], use_llm)
            rows.append(row)
            if not use_llm:
                continue
            _print_progress(row)
            errors_in_a_row = errors_in_a_row + 1 if row.get("llm_fehler") else 0
            if errors_in_a_row >= MAX_ERRORS_IN_A_ROW:
                print(f"Abbruch nach {MAX_ERRORS_IN_A_ROW} Endpunkt-Fehlern in Folge.")
                break
    except KeyboardInterrupt:
        print(f"\nAbgebrochen. Ausgewertet werden die ersten {len(rows)} Tickets.")
    return rows


def evaluate_ticket(ticket: dict, gold: dict, use_llm: bool) -> dict:
    """Misst ein Ticket: die Regeln immer, das LLM nur mit use_llm."""
    row = {
        "id": ticket["id"],
        "gold_kategorie": gold["kategorie"],
        "gold_prioritaet": gold["prioritaet"],
    }

    # TODO 2.1: Regeln messen.
    #   - classify_and_prioritize(ticket) liefert (Kategorie, Priorität).
    #   - Ergebnis in row["regel_kategorie"] und row["regel_prioritaet"].
    #   - Latenz mit time.perf_counter() messen und in MILLISEKUNDEN auf drei
    #     Nachkommastellen in row["regel_latenz_ms"] schreiben. In Sekunden
    #     gerundet stünde dort 0, weil die Regeln nur Mikrosekunden brauchen.
    raise NotImplementedError("TODO 2.1 in src/evaluate.py: Regeln messen")

    if use_llm:
        # TODO 2.3: Das LLM messen, ohne dass ein Endpunkt-Fehler den Lauf beendet.
        #   - Zeit nehmen, classify_ticket_llm(ticket) aufrufen und das Ergebnis
        #     mit row.update(llm_columns(...)) übernehmen.
        #   - Schlägt der Aufruf fehl, die Exception abfangen. Kommt sie vom
        #     Endpunkt (is_endpoint_error(exc), z. B. Timeout, 429, 403), kurz
        #     ausgeben und row.update(error_columns(exc)) aufrufen.
        #   - Jede andere Exception mit `raise` weiterwerfen. Sie stammt aus dem
        #     eigenen Code (Prompt-Format, Parser) und soll sichtbar abbrechen.
        #   - Bei Erfolg und bei Endpunkt-Fehlern die Latenz in SEKUNDEN auf zwei
        #     Nachkommastellen in row["llm_latenz_s"] schreiben.
        raise NotImplementedError("TODO 2.3 in src/evaluate.py: LLM messen")
    return row


def is_endpoint_error(exc: BaseException) -> bool:
    """True für Fehler von Endpunkt oder Netz, False für Fehler im eigenen Code.

    litellm meldet Timeout, 401, 403 und 429 mit eigenen Exception-Klassen. Ein
    KeyError aus dem Prompt oder ein TypeError im Parser stammt dagegen aus dem
    eigenen Code. Er darf nicht als Endpunkt-Fehler in der Statistik verschwinden.
    """
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    return type(exc).__module__.split(".")[0] in ENDPOINT_ERROR_PACKAGES


def llm_columns(result: dict) -> dict:
    """Übernimmt das Ergebnis von classify_ticket_llm() in die CSV-Spalten.

    Ältere Varianten von classify_ticket_llm() liefern nur kategorie und
    prioritaet. Die Zusatzfelder werden deshalb mit .get() gelesen. Ein leerer
    Wert heißt „nicht erfasst“. False hieße „kein Parse-Fehler“ und wäre geraten.
    """
    parse_error = result.get("parse_fehler")
    return {
        "llm_kategorie": result["kategorie"],
        "llm_prioritaet": result["prioritaet"],
        "llm_parse_fehler": "" if parse_error is None else bool(parse_error),
        "llm_fehler": "",
        "llm_prompt_tokens": result.get("prompt_tokens", ""),
        "llm_completion_tokens": result.get("completion_tokens", ""),
    }


def error_columns(exc: Exception) -> dict:
    """CSV-Spalten für ein Ticket, bei dem die LLM-Anfrage gescheitert ist.

    Ohne Antwort gibt es nichts zu parsen. llm_parse_fehler bleibt deshalb leer.
    """
    return {
        "llm_kategorie": "",
        "llm_prioritaet": "",
        "llm_parse_fehler": "",
        "llm_fehler": type(exc).__name__,
        "llm_prompt_tokens": "",
        "llm_completion_tokens": "",
    }


def _print_progress(row: dict) -> None:
    """Eine Zeile pro Ticket, damit ein langer LLM-Lauf nicht eingefroren wirkt."""
    if row.get("llm_fehler"):
        return  # Die Fehlerzeile hat evaluate_ticket() schon gedruckt.
    llm = f"{row.get('llm_kategorie')}/{row.get('llm_prioritaet')}"
    if row.get("llm_parse_fehler"):
        llm += " (Parse-Fehler)"
    print(
        f"{row['id']}  gold {row['gold_kategorie']}/{row['gold_prioritaet']}  "
        f"Regeln {row.get('regel_kategorie')}/{row.get('regel_prioritaet')}  "
        f"LLM {llm}  {_decimal(row.get('llm_latenz_s', 0), 2)} s"
    )


# --- Auswertung --------------------------------------------------------------


def accuracy(rows: list[dict], system: str, field: str) -> float:
    """Anteil korrekter Vorhersagen, z. B. accuracy(rows, "llm", "kategorie").

    Fehlende Vorhersagen (Endpunkt-Fehler) zählen als falsch.
    """
    # TODO 2.2: Accuracy berechnen.
    #   - Vergleicht row.get(f"{system}_{field}") mit row[f"gold_{field}"].
    #   - Ergebnis: Anzahl Treffer geteilt durch Anzahl Zeilen.
    #   - Leere Liste: 0.0 zurückgeben statt durch null zu teilen.
    raise NotImplementedError("TODO 2.2 in src/evaluate.py: accuracy() implementieren")


def majority_label(rows: list[dict], field: str) -> str:
    """Häufigstes Gold-Label. So gut ist ein System, das immer dasselbe antwortet."""
    return Counter(row[f"gold_{field}"] for row in rows).most_common(1)[0][0]


def majority_accuracy(rows: list[dict], field: str) -> float:
    """Accuracy der Mehrheitsklasse: die dümmste sinnvolle Vergleichszahl."""
    label = majority_label(rows, field)
    return sum(1 for row in rows if row[f"gold_{field}"] == label) / len(rows)


def only_correct(rows: list[dict], system: str, other: str, field: str) -> list[str]:
    """IDs der Tickets, die `system` richtig und `other` falsch klassifiziert."""
    return [
        row["id"]
        for row in rows
        if row.get(f"{system}_{field}") == row[f"gold_{field}"]
        and row.get(f"{other}_{field}") != row[f"gold_{field}"]
    ]


def parse_error_hits(rows: list[dict], field: str) -> int:
    """Treffer des LLM, die nur der Rückfall bei einem Parse-Fehler erzeugt hat.

    Der Rückfall lautet Software / mittel, die häufigsten Gold-Labels. Diese
    Treffer zählen in der Accuracy mit, so wie im Betrieb. Sie sind aber Zufall.
    """
    return sum(
        1
        for row in rows
        if row.get("llm_parse_fehler") is True and row.get(f"llm_{field}") == row[f"gold_{field}"]
    )


def missed_urgent(rows: list[dict], system: str) -> list[str]:
    """IDs der dringenden Tickets (Gold: hoch), die `system` nicht als hoch einstuft."""
    return [
        row["id"]
        for row in rows
        if row["gold_prioritaet"] == "hoch" and row.get(f"{system}_prioritaet") != "hoch"
    ]


def _median(rows: list[dict], key: str) -> float | None:
    """Median einer Zahlenspalte. Leere Werte (z. B. nach Fehlern) fallen heraus."""
    values = [row[key] for row in rows if isinstance(row.get(key), (int, float))]
    return statistics.median(values) if values else None


def _ids(ids: list[str]) -> str:
    """Ticket-IDs als kommagetrennte Liste, für den Report."""
    return ", ".join(ids) if ids else "keine"


def _percent(value: float) -> str:
    """Anteil in deutscher Schreibweise, z. B. 0.7 → "70 %"."""
    return f"{value * 100:.0f} %"


def _decimal(value: float, digits: int) -> str:
    """Zahl mit Dezimalkomma, z. B. _decimal(3.333, 1) → "3,3". Die CSV behält den Punkt."""
    return f"{value:.{digits}f}".replace(".", ",")


def print_report(rows: list[dict], use_llm: bool) -> None:
    """Druckt Accuracy und Latenz je System und die Befunde für die Reflexion."""
    systems = ["regel", "llm"] if use_llm else ["regel"]
    print("\n" + "=" * REPORT_WIDTH)
    points = _decimal(100 / len(rows), 1)
    print(f"EVALUIERUNG auf {len(rows)} Tickets (1 Ticket = {points} Prozentpunkte)")
    print("=" * REPORT_WIDTH)
    _print_table(rows, systems)
    print("-" * REPORT_WIDTH)
    _print_findings(rows, systems)
    if use_llm:
        _print_llm_details(rows)
    print("=" * REPORT_WIDTH)


def _print_table(rows: list[dict], systems: list[str]) -> None:
    """Tabelle: Mehrheitsklasse als Vergleichswert, dann je System Accuracy und Latenz."""
    print(f"{'System':36}{'Kategorie':>10}{'Priorität':>11}{'Latenz (Median)':>17}")
    majority = (
        f"Mehrheitsklasse: {majority_label(rows, 'kategorie')} / "
        f"{majority_label(rows, 'prioritaet')}"
    )
    print(
        f"{majority:36}{_percent(majority_accuracy(rows, 'kategorie')):>10}"
        f"{_percent(majority_accuracy(rows, 'prioritaet')):>11}{'-':>17}"
    )
    for system in systems:
        label = "Keyword-Regeln (VL 1)" if system == "regel" else f"LLM ({get_model()})"
        print(
            f"{label:36}{_percent(accuracy(rows, system, 'kategorie')):>10}"
            f"{_percent(accuracy(rows, system, 'prioritaet')):>11}"
            f"{_median_latency(rows, system):>17}"
        )


def _median_latency(rows: list[dict], system: str) -> str:
    """Median der Latenz: Regeln in Millisekunden, LLM in Sekunden ohne Fehlerfälle."""
    if system == "regel":
        value = _median(rows, "regel_latenz_ms")
        return "-" if value is None else f"{_decimal(value, 3)} ms"
    value = _median([row for row in rows if not row.get("llm_fehler")], "llm_latenz_s")
    return "-" if value is None else f"{_decimal(value, 2)} s"


def _print_findings(rows: list[dict], systems: list[str]) -> None:
    """Testdaten getrennt, übersehene dringende Tickets und die Unterschiede je Ticket."""
    test_rows = [row for row in rows if row["id"] not in DEV_IDS]
    if test_rows and len(test_rows) < len(rows):
        parts = [
            f"{SYSTEM_NAMES[system]} {_percent(accuracy(test_rows, system, 'kategorie'))} / "
            f"{_percent(accuracy(test_rows, system, 'prioritaet'))}"
            for system in systems
        ]
        print(f"Nur Testdaten ({len(test_rows)} Tickets ab T-1011): {', '.join(parts)}")

    urgent = sum(1 for row in rows if row["gold_prioritaet"] == "hoch")
    for system in systems:
        missed = missed_urgent(rows, system)
        name = SYSTEM_NAMES[system]
        print(f"Dringend übersehen, {name}: {len(missed)} von {urgent} ({_ids(missed)})")

    if "llm" in systems:
        for field, name in (("kategorie", "Kategorie"), ("prioritaet", "Priorität")):
            print(f"{name} nur Regeln richtig: {_ids(only_correct(rows, 'regel', 'llm', field))}")
            print(f"{name} nur LLM richtig:    {_ids(only_correct(rows, 'llm', 'regel', field))}")


def _print_llm_details(rows: list[dict]) -> None:
    """Parse-Fehler, Endpunkt-Fehler und Tokens: das, was Accuracy allein verschweigt."""
    endpoint_errors = sum(1 for row in rows if row.get("llm_fehler"))
    thinking = os.environ.get("LLM_THINKING") or "Server-Default"
    answered = [row for row in rows if not row.get("llm_fehler")]
    # Ältere Varianten von classify_ticket_llm() melden keine Parse-Fehler. Dann
    # stünde hier sonst „0 Parse-Fehler“, und Zufallstreffer blieben unsichtbar.
    recorded = not answered or any(
        isinstance(row.get("llm_parse_fehler"), bool) for row in answered
    )
    if recorded:
        parse_errors = sum(1 for row in answered if row.get("llm_parse_fehler") is True)
        parse_info = f"{parse_errors} Parse-Fehler"
    else:
        parse_info = "Parse-Fehler nicht erfasst"
    print(f"LLM: {parse_info}, {endpoint_errors} Endpunkt-Fehler, Thinking: {thinking}")
    if recorded:
        print(
            f"Parse-Fehler zufällig richtig: Kategorie {parse_error_hits(rows, 'kategorie')}, "
            f"Priorität {parse_error_hits(rows, 'prioritaet')}"
        )
    prompt_tokens = _median(rows, "llm_prompt_tokens")
    completion_tokens = _median(rows, "llm_completion_tokens")
    if prompt_tokens is not None and completion_tokens is not None:
        print(
            f"LLM-Tokens pro Ticket (Median): {prompt_tokens:.0f} ein, "
            f"{completion_tokens:.0f} aus"
        )


def write_csv(rows: list[dict], path: Path = RESULTS_PATH) -> None:
    """Schreibt alle Zeilen als CSV, eine Spalte pro Messwert."""
    fieldnames = list(dict.fromkeys(key for row in rows for key in row))
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> None:
    """Kommandozeile: Tickets auswählen, messen, CSV schreiben, Report drucken."""
    parser = argparse.ArgumentParser(description="Triage-Evaluierung gegen das Golden Dataset")
    parser.add_argument("--llm", action="store_true", help="zusätzlich das LLM evaluieren")
    parser.add_argument(
        "--limit", type=int, default=10, help="nur die ersten N Tickets (Default: 10)"
    )
    parser.add_argument("--all", action="store_true", help="alle Tickets evaluieren")
    parser.add_argument("--csv", type=Path, default=RESULTS_PATH, help="Zieldatei für die Details")
    args = parser.parse_args(argv)

    rows = evaluate(use_llm=args.llm, limit=None if args.all else args.limit)
    if not rows:
        raise SystemExit("Keine Tickets ausgewertet. Prüft --limit.")
    write_csv(rows, args.csv)  # zuerst sichern, dann auswerten
    print_report(rows, use_llm=args.llm)
    print(f"Details: {args.csv}")


if __name__ == "__main__":
    main()
