"""Mutation-Testing-Werkzeug fuer src/triage.py — reine Standardbibliothek.

Kein pytest, kein coverage, kein pip install, kein Netz. Laeuft mit nichts
ausser CPython:

    python3 tools/mutation_dojo.py --suite shipped
    python3 tools/mutation_dojo.py --suite oracle
    python3 tools/mutation_dojo.py --suite frozen
    python3 tools/mutation_dojo.py --equivalence Netzwerk:wlan
    python3 tools/mutation_dojo.py --list

Mutantenklasse: **ein Keyword aus einer Liste loeschen**. Warum diese und
nicht `<` -> `<=` wie im Lehrbuch? Weil das Verhalten von src/triage.py in
*Daten* steckt (zwei dicts), nicht in Verzweigungen. Operator-Mutationen
finden dort fast nichts.

Der Mutant wird **im Speicher** gesetzt (dict-Eintrag entfernen, im finally
zuruecksetzen) — es wird **keine Datei geschrieben**. Ein Abbruch mitten im
Lauf kann den Arbeitsbaum also nicht verdrecken.
"""

from __future__ import annotations

import argparse
import importlib
import itertools
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src import triage  # noqa: E402


# ---------------------------------------------------------------------------
# Test-Suiten
#
# Drei Suiten, ein Unterschied: **woher die Erwartung kommt.** Genau das ist
# das Thema des Labs.
# ---------------------------------------------------------------------------

def _ticket(betreff: str, text: str) -> dict:
    return {"id": "T-9999", "von": "test@leinetech.de", "betreff": betreff,
            "text": text, "erstellt": "2026-05-01"}


def suite_shipped() -> list[str]:
    """Die 5 ausgelieferten Tests aus tests/test_triage.py, 1:1 nachgebaut.

    Nachgebaut statt importiert, damit die Suite ohne pytest laeuft. Die
    Assertions sind identisch — wer mag, vergleicht mit tests/test_triage.py.
    """
    fails = []
    cap = triage.classify_and_prioritize

    if cap(_ticket("Laptop startet nicht", "Mein Laptop bleibt beim Boot haengen.")) \
            != ("Hardware", "mittel"):
        fails.append("test_hardware_ticket")
    if cap(_ticket("VPN down", "Das VPN faellt dauernd aus, Ausfall betrifft "
                               "das ganze Team. Dringend!")) != ("Netzwerk", "hoch"):
        fails.append("test_netzwerk_ticket_hohe_prioritaet")
    if cap(_ticket("Kein Zugriff", "Ich habe keinen Zugriff auf das WLAN-Portal."))[0] \
            != "Zugang":
        fails.append("test_zugang_vor_netzwerk")
    if cap(_ticket("Alles seltsam", "Irgendwas stimmt hier nicht.")) \
            != ("Software", "mittel"):
        fails.append("test_default_kategorie_software")

    ergebnisse = triage.triage_all([
        _ticket("Drucker kaputt", "Der Drucker im 2. OG druckt nicht."),
        _ticket("Frage zur Rechnung", "Ich habe eine Frage zu den Kosten."),
    ])
    ok = (len(ergebnisse) == 2
          and ergebnisse[0]["kategorie"] == "Hardware"
          and ergebnisse[1]["kategorie"] == "Abrechnung"
          and ergebnisse[1]["prioritaet"] == "niedrig")
    if not ok:
        fails.append("test_triage_all_liefert_alle_tickets")
    return fails


def suite_oracle() -> list[str]:
    """Datengetrieben — Erwartung wird aus dem PRUEFLING importiert.

    Die naheliegende, DRY-konforme Refaktorierung: nicht 5 handgeschriebene
    Faelle, sondern eine Schleife ueber CATEGORY_KEYWORDS. Sieht gruendlicher
    aus. Ist es nicht. Warum — das ist die Pointe von Teil 1.
    """
    fails = []
    for kategorie, keywords in triage.CATEGORY_KEYWORDS.items():
        for kw in keywords:
            got = triage.classify_and_prioritize(_ticket(kw, kw))[0]
            if got != kategorie:
                fails.append(f"oracle[{kategorie}/{kw}]")
    return fails


# Eingefrorene Kopie der Tabelle: einmal beim Import aus dem intakten Modul
# gezogen und danach unveraenderlich. Das ist die *unabhaengige* Erwartung.
FROZEN_CATEGORIES: dict[str, tuple[str, ...]] = {
    kategorie: tuple(keywords)
    for kategorie, keywords in triage.CATEGORY_KEYWORDS.items()
}


def suite_frozen() -> list[str]:
    """Dieselbe Schleife — aber gegen die eingefrorene Kopie.

    Identische Struktur, identischer Code unter Test, ein einziger
    Unterschied: die Erwartung liegt ausserhalb des Prueflings.
    """
    fails = []
    for kategorie, keywords in FROZEN_CATEGORIES.items():
        for kw in keywords:
            got = triage.classify_and_prioritize(_ticket(kw, kw))[0]
            if got != kategorie:
                fails.append(f"frozen[{kategorie}/{kw}]")
    return fails


SUITES = {"shipped": suite_shipped, "oracle": suite_oracle, "frozen": suite_frozen}


# ---------------------------------------------------------------------------
# Mutanten
# ---------------------------------------------------------------------------

def category_mutants() -> list[tuple[str, str]]:
    """Alle Kategorie-Keywords als (Zeile, Keyword)."""
    return [(row, kw) for row, kws in triage.CATEGORY_KEYWORDS.items() for kw in kws]


def all_mutants() -> list[tuple[str, str]]:
    """Kategorie- UND Prioritaets-Keywords."""
    out = category_mutants()
    out += [(row, kw) for row, kws in triage.PRIORITY_KEYWORDS.items() for kw in kws]
    return out


class mutant:
    """Context-Manager: entfernt ein Keyword im Speicher, setzt es zurueck."""

    def __init__(self, row: str, kw: str):
        self.row, self.kw = row, kw
        self.table = (triage.CATEGORY_KEYWORDS
                      if row in triage.CATEGORY_KEYWORDS else triage.PRIORITY_KEYWORDS)

    def __enter__(self):
        self.original = list(self.table[self.row])
        self.table[self.row] = [k for k in self.original if k != self.kw]
        return self

    def __exit__(self, *exc):
        self.table[self.row] = self.original
        return False


# ---------------------------------------------------------------------------
# Aequivalenz-Suche
# ---------------------------------------------------------------------------

def find_distinguishing_input(row: str, kw: str, extra: list[str] | None = None):
    """Sucht eine Eingabe, fuer die Original und Mutant sich unterscheiden.

    Durchsucht: leerer Text, jedes einzelne Keyword, jedes Keyword-Paar, plus
    optionale Zusatzkandidaten. Findet sie **nichts**, ist der Mutant nach
    dieser Suche nicht unterscheidbar — ein Aequivalenz-*Indiz*, kein Beweis.
    Den Beweis liefert das Argument, nicht die Suche (siehe Lab-Sheet).
    """
    keywords = [kw for _, kw in all_mutants()]
    candidates = [""] + keywords + list(extra or [])
    candidates += [f"{a} {b}" for a, b in itertools.combinations(keywords, 2)]

    def classify(text: str) -> str:
        return triage.classify_and_prioritize(_ticket("", text))[0]

    for cand in candidates:
        before = classify(cand)
        with mutant(row, kw):
            after = classify(cand)
        if before != after:
            return cand, before, after, len(candidates)
    return None, None, None, len(candidates)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def run_suite(name: str, scope: str) -> None:
    suite = SUITES[name]
    mutants = category_mutants() if scope == "category" else all_mutants()

    baseline = suite()
    if baseline:
        print(f"WARNUNG: Suite '{name}' ist schon auf dem INTAKTEN Modul rot: {baseline}")
        print("         Ein Mutations-Score ist damit bedeutungslos. Erst reparieren.")
        return

    killed, survived = [], []
    for row, kw in mutants:
        with mutant(row, kw):
            (killed if suite() else survived).append(f"{row}/{kw}")

    total = len(mutants)
    print(f"Suite '{name}' — Mutantenklasse: ein Keyword loeschen ({scope})")
    print(f"  auf dem intakten Modul : gruen")
    print(f"  Mutanten               : {total}")
    print(f"  getoetet               : {len(killed)}")
    print(f"  ueberlebt              : {len(survived)}")
    print(f"  Mutation Score (roh)   : {len(killed)}/{total} = {len(killed)/total:.3f}")
    if killed:
        print(f"  getoetet im Detail     : {', '.join(sorted(killed))}")
    print()
    print("  Hinweis: 'roh' heisst OHNE Abzug aequivalenter Mutanten. Wie viele davon")
    print("           es gibt und warum der Abzug den Score VERBESSERT: --equivalence")


def cmd_equivalence(target: str) -> None:
    row, _, kw = target.partition(":")
    if not kw:
        print("Format: --equivalence Zeile:keyword    z. B. Netzwerk:wlan")
        return
    table = (triage.CATEGORY_KEYWORDS
             if row in triage.CATEGORY_KEYWORDS else triage.PRIORITY_KEYWORDS)
    if row not in table or kw not in table[row]:
        print(f"'{kw}' steht nicht in Zeile '{row}'.")
        return

    extra = ["wlan-portal", "Planung", "Balance", "Atlantik", "rechnung"]
    cand, before, after, n = find_distinguishing_input(row, kw, extra)
    print(f"Aequivalenz-Suche fuer {row}/{kw}   ({n} Kandidaten geprueft)")
    if cand is None:
        print("  KEINE unterscheidende Eingabe gefunden.")
        print("  -> Kein Test kann diesen Mutanten toeten. Er gehoert NICHT in den")
        print("     Nenner des Mutation Score.")
    else:
        print(f"  unterscheidende Eingabe: {cand!r}")
        print(f"    Original -> {before}    Mutant -> {after}")
        print("  -> Der Mutant IST toetbar. Wenn die Suite ihn nicht toetet, ist das")
        print("     ein Mangel der Suite, kein Naturgesetz.")


def cmd_list() -> None:
    print("Mutanten (Index: Zeile/Keyword) — bare Diffs, keine Beschreibungen:")
    for i, (row, kw) in enumerate(all_mutants(), 1):
        print(f"  M{i:02d}  CATEGORY_KEYWORDS/PRIORITY_KEYWORDS['{row}'] -= '{kw}'")
    print(f"\n{len(all_mutants())} Mutanten. Wie viele ueberleben die Suite? Erst schaetzen.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--suite", choices=sorted(SUITES), help="Suite messen")
    p.add_argument("--scope", choices=["category", "all"], default="category",
                   help="nur Kategorie-Keywords (34) oder auch Prioritaet (45)")
    p.add_argument("--equivalence", metavar="Zeile:keyword",
                   help="unterscheidende Eingabe fuer einen Mutanten suchen")
    p.add_argument("--list", action="store_true", help="Mutanten auflisten")
    args = p.parse_args()

    if args.list:
        cmd_list()
    elif args.equivalence:
        cmd_equivalence(args.equivalence)
    elif args.suite:
        run_suite(args.suite, args.scope)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
