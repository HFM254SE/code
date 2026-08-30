"""Mutation-Testing-Werkzeug für src/triage.py — reine Standardbibliothek.

Kein pytest, kein coverage, kein pip install, kein Netz. Läuft mit nichts
außer CPython:

    python3 tools/mutation_dojo.py --suite shipped
    python3 tools/mutation_dojo.py --suite oracle
    python3 tools/mutation_dojo.py --suite frozen
    python3 tools/mutation_dojo.py --equivalence Netzwerk:wlan
    python3 tools/mutation_dojo.py --list
    python3 tools/mutation_dojo.py --bruecke
    python3 tools/mutation_dojo.py --tests tests/test_triage_oracle.py

Mutantenklasse: **ein Keyword aus einer Liste löschen**. Warum diese und
nicht `<` -> `<=` wie im Lehrbuch? Weil das Verhalten von src/triage.py in
*Daten* steckt (zwei dicts), nicht in Verzweigungen. Operator-Mutationen
finden dort fast nichts.

Dieses Werkzeug enthält **keine eigenen Tests**. Jede Suite führt die
echten Dateien unter tests/ aus — `--suite oracle` und `--suite frozen`
messen also genau das, was ihr in tests/test_triage_oracle.py schreibt.
Ein Werkzeug, das seine eigene Erwartung mitbringt, wäre in einem Lab
über Orakel eine schlechte Pointe.

Der Mutant wird **im Speicher** gesetzt (dict-Eintrag entfernen, im finally
zurücksetzen) — es wird **keine Datei geschrieben**. Ein Abbruch mitten im
Lauf kann den Arbeitsbaum also nicht verdrecken.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import itertools
import sys
from pathlib import Path
from types import ModuleType

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from src import triage  # noqa: E402


# ---------------------------------------------------------------------------
# Mini-Test-Runner
#
# Genug pytest für dieses Lab: Modul laden, alle test_*-Funktionen rufen,
# AssertionError = rot. Mehr braucht keine der Dateien unter tests/ — keine
# Fixtures, kein parametrize, kein conftest.
# ---------------------------------------------------------------------------

TEST_TRIAGE = REPO / "tests" / "test_triage.py"
TEST_ORACLE = REPO / "tests" / "test_triage_oracle.py"
TEST_SPEC = REPO / "tests" / "test_openapi_spec.py"


def load_test_module(path: Path) -> ModuleType:
    """Lädt eine Testdatei als Modul — ohne pytest, ohne Installation."""
    spec = importlib.util.spec_from_file_location(f"vl09_{path.stem}", path)
    if spec is None or spec.loader is None:  # nur bei kaputtem Pfad erreichbar
        raise ImportError(f"Testdatei nicht als Modul ladbar: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_names(module) -> list[str]:
    """Alle test_*-Funktionen in Definitionsreihenfolge."""
    return [name for name, value in vars(module).items()
            if name.startswith("test_") and callable(value)]


def run_tests(module, names: list[str] | None = None) -> list[str]:
    """Führt Testfunktionen aus. Rückgabe: die fehlgeschlagenen."""
    fails = []
    for name in (names if names is not None else test_names(module)):
        try:
            getattr(module, name)()
        except AssertionError:
            fails.append(name)
        except Exception as exc:  # kaputter Test, kein Mutanten-Fund
            fails.append(f"{name} [{type(exc).__name__}: {exc}]")
    return fails


# ---------------------------------------------------------------------------
# Test-Suiten
#
# Drei Suiten, ein Unterschied: **woher die Erwartung kommt.** Genau das ist
# das Thema des Labs.
#
#   shipped  tests/test_triage.py        — 5 handgeschriebene Fälle
#   oracle   tests/test_triage_oracle.py — TODO 1: Erwartung aus dem Prüfling
#   frozen   tests/test_triage_oracle.py — TODO 2: Erwartung eingefroren
# ---------------------------------------------------------------------------

STUDENT_SUITES = {
    "oracle": ("test_jedes_keyword_trifft_seine_kategorie", "TODO 1"),
    "frozen": ("test_jedes_keyword_trifft_seine_kategorie_eingefroren", "TODO 2"),
}
SUITE_NAMES = ("shipped", "oracle", "frozen")


def _leerer_rumpf(node: ast.FunctionDef) -> bool:
    """True, wenn die Funktion nur aus Docstring, `pass` oder `...` besteht."""
    body = [stmt for stmt in node.body
            if not (isinstance(stmt, ast.Expr)
                    and isinstance(stmt.value, ast.Constant)
                    and isinstance(stmt.value.value, str))]
    return all(isinstance(stmt, ast.Pass)
               or (isinstance(stmt, ast.Expr)
                   and isinstance(stmt.value, ast.Constant)
                   and stmt.value.value is Ellipsis)
               for stmt in body)


def leerer_test(pfad: Path, fn_name: str) -> bool:
    """Steht die Testfunktion im Quelltext noch leer da (`...`, `pass`)?

    Statisch geprüft, nicht durch Ausführen: ein leerer Test BESTEHT und
    lässt sich am Ergebnis nicht von einem fertigen unterscheiden. Genau
    deshalb wäre ein Score auf einem leeren Test die nächste Orakel-Falle —
    0/34, und die Zahl sähe aus wie ein Messergebnis.
    """
    tree = ast.parse(pfad.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            return _leerer_rumpf(node)
    return True  # gar nicht vorhanden


def build_suite(name: str):
    """Liefert (suite_callable, Fehlermeldung). Genau eines von beiden ist None."""
    if name == "shipped":
        module = load_test_module(TEST_TRIAGE)
        return (lambda: run_tests(module)), None

    fn_name, todo = STUDENT_SUITES[name]
    if leerer_test(TEST_ORACLE, fn_name):
        return None, (
            f"{todo} ist noch nicht gefüllt: {fn_name}()\n"
            f"  in tests/test_triage_oracle.py hat einen leeren Rumpf.\n"
            f"  Ein Test ohne Assertion ist immer grün und eliminiert keinen Mutanten.\n"
            f"  Der Score wäre 0/34 — und sähe aus wie ein Messergebnis."
        )

    module = load_test_module(TEST_ORACLE)
    if name == "frozen" and not getattr(module, "FROZEN", None):
        return None, (
            "FROZEN ist leer (oder fehlt) in tests/test_triage_oracle.py.\n"
            "  TODO 2 trägt die eingefrorene Kopie der Tabelle dort ein.\n"
            "  Eine Schleife über ein leeres dict prüft null Keywords."
        )
    return (lambda: run_tests(module, [fn_name])), None


# ---------------------------------------------------------------------------
# Mutanten
# ---------------------------------------------------------------------------

def category_mutants() -> list[tuple[str, str]]:
    """Alle Kategorie-Keywords als (Zeile, Keyword)."""
    return [(row, kw) for row, kws in triage.CATEGORY_KEYWORDS.items() for kw in kws]


def all_mutants() -> list[tuple[str, str]]:
    """Kategorie- UND Prioritäts-Keywords."""
    out = category_mutants()
    out += [(row, kw) for row, kws in triage.PRIORITY_KEYWORDS.items() for kw in kws]
    return out


def mutants_for(scope: str) -> list[tuple[str, str]]:
    return category_mutants() if scope == "category" else all_mutants()


def table_name(row: str) -> str:
    return ("CATEGORY_KEYWORDS" if row in triage.CATEGORY_KEYWORDS
            else "PRIORITY_KEYWORDS")


class mutant:
    """Context-Manager: entfernt ein Keyword im Speicher, setzt es zurück."""

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


class key_mutant:
    """Context-Manager: entfernt eine ganze Kategorie-ZEILE (Aufgabe E).

    Nicht ein Keyword, sondern der Schlüssel. Die Reihenfolge der Zeilen ist
    Teil des Verhaltens (first match wins), deshalb wird das ganze dict
    gesichert und in Originalreihenfolge zurückgeschrieben.
    """

    def __init__(self, row: str):
        self.row = row

    def __enter__(self):
        self.snapshot = dict(triage.CATEGORY_KEYWORDS)
        del triage.CATEGORY_KEYWORDS[self.row]
        return self

    def __exit__(self, *exc):
        triage.CATEGORY_KEYWORDS.clear()
        triage.CATEGORY_KEYWORDS.update(self.snapshot)
        return False


# ---------------------------------------------------------------------------
# Äquivalenz-Suche
# ---------------------------------------------------------------------------

def find_distinguishing_input(row: str, kw: str, extra: list[str] | None = None):
    """Sucht eine Eingabe, für die Original und Mutant sich unterscheiden.

    Durchsucht: leerer Text, jedes einzelne Keyword, jedes Keyword-Paar, plus
    optionale Zusatzkandidaten. Findet sie **nichts**, ist der Mutant nach
    dieser Suche nicht unterscheidbar — ein Äquivalenz-*Indiz*, kein Beweis.
    Den Beweis liefert das Argument, nicht die Suche (siehe Lab-Sheet).
    """
    keywords = [kw for _, kw in all_mutants()]
    candidates = [""] + keywords + list(extra or [])
    candidates += [f"{a} {b}" for a, b in itertools.combinations(keywords, 2)]

    def classify(text: str) -> str:
        return triage.classify_and_prioritize(
            {"betreff": "", "text": text})[0]

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
    suite, fehler = build_suite(name)
    if suite is None:
        print(f"Suite '{name}' kann noch nicht gemessen werden:")
        print(f"  {fehler}")
        return

    mutants = mutants_for(scope)
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
    print(f"Suite '{name}' — Mutantenklasse: ein Keyword löschen ({scope})")
    print("  auf dem intakten Modul : grün")
    print(f"  Mutanten               : {total}")
    print(f"  eliminiert             : {len(killed)}")
    print(f"  überlebt               : {len(survived)}")
    print(f"  Mutation Score (roh)   : {len(killed)}/{total} = {len(killed)/total:.3f}")
    if killed:
        print(f"  eliminiert im Detail   : {', '.join(sorted(killed))}")
    print()
    print("  Hinweis: 'roh' heißt OHNE Abzug äquivalenter Mutanten. Wie viele davon")
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
    print(f"Äquivalenz-Suche für {row}/{kw}   ({n} Kandidaten geprüft)")
    if cand is None:
        print("  KEINE unterscheidende Eingabe gefunden.")
        print("  -> Kein Test kann diesen Mutanten eliminieren. Er gehört NICHT in den")
        print("     Nenner des Mutation Score.")
    else:
        print(f"  unterscheidende Eingabe: {cand!r}")
        print(f"    Original -> {before}    Mutant -> {after}")
        print("  -> Der Mutant IST eliminierbar. Wenn die Suite ihn nicht eliminiert, ist das")
        print("     ein Mangel der Suite, kein Naturgesetz.")


def cmd_list(scope: str) -> None:
    mutants = mutants_for(scope)
    print(f"Mutanten (Index: Zeile/Keyword) — bare Diffs, keine Beschreibungen"
          f"   [--scope {scope}]")
    for i, (row, kw) in enumerate(mutants, 1):
        print(f"  M{i:02d}  {table_name(row)}['{row}'] -= '{kw}'")
    print(f"\n{len(mutants)} Mutanten. Wie viele überleben die Suite? Erst schätzen.")
    if scope == "category":
        print("(Nur die Kategorie-Keywords. Mit --scope all kommen die "
              "Prioritäts-Keywords dazu.)")


def cmd_tests(pfad: Path) -> None:
    """Eine Testdatei einmal laufen lassen — der Ersatz für `pytest datei.py`.

    Ohne Mutant, ohne Score: nur grün/rot. Damit lässt sich auch TODO 3
    ausprobieren, das in keiner der drei Suiten steckt.
    """
    if not pfad.is_absolute():
        pfad = REPO / pfad
    if not pfad.exists():
        print(f"Datei nicht gefunden: {pfad}")
        return
    module = load_test_module(pfad)
    alle = test_names(module)
    fails = run_tests(module)
    leer = [n for n in alle if leerer_test(pfad, n)]
    print(f"{pfad.relative_to(REPO)} — {len(alle) - len(fails) - len(leer)}/{len(alle)} "
          f"grün, {len(fails)} rot, {len(leer)} leer")
    for name in alle:
        treffer = [f for f in fails if f.split(" [")[0] == name]
        if name in leer:
            status = "LEER"
        elif treffer:
            status = "ROT "
        else:
            status = "grün"
        print(f"  {status}  {name}")
        for f in treffer:
            if " [" in f:
                print(f"           {f.split(' [', 1)[1].rstrip(']')}")
    if leer:
        print()
        print("  LEER heißt: die Funktion hat keinen Rumpf. Sie BESTEHT — und sagt")
        print("  damit genau nichts. Am Ergebnis allein ist das nicht zu sehen.")


def cmd_bruecke() -> None:
    """Brücke zu Teil 2: nicht ein Keyword löschen, sondern den SCHLÜSSEL
    'Software'. (In der Vorlesung lief das als Aufgabe E — daher der Alias.)

    Zeigt ohne pytest, was das Lab behauptet: die Unit-Tests bleiben grün,
    der Spec-Test wird rot. Der Unterschied ist nicht die Sorgfalt der Tests,
    sondern wo ihre Erwartung liegt.
    """
    dateien = [TEST_TRIAGE, TEST_SPEC]
    module = [(p.relative_to(REPO), load_test_module(p)) for p in dateien]

    def bericht(titel: str) -> None:
        print(f"  {titel}")
        for name, mod in module:
            alle = test_names(mod)
            fails = run_tests(mod)
            status = "grün" if not fails else "ROT"
            print(f"    {str(name):32s} {len(alle) - len(fails)}/{len(alle)} {status}")
            for f in fails:
                print(f"      fehlgeschlagen: {f}")

    print("Brücke zu Teil 2 — Mutant: der SCHLÜSSEL 'Software' fällt aus "
          "CATEGORY_KEYWORDS.")
    print("(im Speicher, keine Datei wird verändert)")
    print()
    bericht("vorher, intaktes Modul:")
    print()
    with key_mutant("Software"):
        bericht("nachher, mit Mutant:")
    print()
    print("  DEFAULT_CATEGORY ist weiterhin 'Software' — deshalb liefert die")
    print("  Triage für jeden Text dasselbe wie vorher, und die Unit-Tests")
    print("  merken nichts. Der Spec-Test vergleicht das Kategorie-Enum aus")
    print("  api/openapi.yaml mit CATEGORY_KEYWORDS: eine Erwartung, die")
    print("  AUSSERHALB des Prüflings liegt. Nur sie sieht den Mutanten.")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--suite", choices=SUITE_NAMES, help="Suite messen")
    p.add_argument("--scope", choices=["category", "all"], default="category",
                   help="nur Kategorie-Keywords (34) oder auch Priorität (45)")
    p.add_argument("--equivalence", metavar="Zeile:keyword",
                   help="unterscheidende Eingabe für einen Mutanten suchen")
    p.add_argument("--list", action="store_true", help="Mutanten auflisten")
    p.add_argument("--bruecke", "--aufgabe-e", action="store_true",
                   help="Schlüssel 'Software' löschen und beide Testdateien laufen lassen")
    p.add_argument("--tests", metavar="DATEI",
                   help="eine Testdatei einmal laufen lassen (ohne pytest, ohne Mutant)")
    args = p.parse_args()

    if args.tests:
        cmd_tests(Path(args.tests))
    elif args.list:
        cmd_list(args.scope)
    elif args.equivalence:
        cmd_equivalence(args.equivalence)
    elif args.bruecke:
        cmd_bruecke()
    elif args.suite:
        run_suite(args.suite, args.scope)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
