"""Statistik-Report über Triage-Ergebnisse."""

from collections import Counter

REPORT_WIDTH = 60


def print_stats(results: list[dict]) -> None:
    """Druckt eine Zusammenfassung der Kategorien und Prioritäten."""
    categories = Counter(result["kategorie"] for result in results)
    priorities = Counter(result["prioritaet"] for result in results)

    print("=" * REPORT_WIDTH)
    print("TICKET-STATISTIK LEINETECH SUPPORT")
    print("=" * REPORT_WIDTH)
    print(
        f"Hardware: {categories['Hardware']}  Software: {categories['Software']}  "
        f"Netzwerk: {categories['Netzwerk']}  Zugang: {categories['Zugang']}  "
        f"Abrechnung: {categories['Abrechnung']}"
    )
    print(
        f"Prioritaeten: hoch={priorities['hoch']} "
        f"mittel={priorities['mittel']} niedrig={priorities['niedrig']}"
    )
    print("=" * REPORT_WIDTH)
