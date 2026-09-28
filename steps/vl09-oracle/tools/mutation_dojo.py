"""Mutation-Testing-Werkzeug für src/triage.py, nur mit der Standardbibliothek.

Kein pytest, kein coverage, kein pip install, kein Netz. Es läuft mit nichts
außer CPython:

    python3 tools/mutation_dojo.py --list
    python3 tools/mutation_dojo.py --suite shipped
    python3 tools/mutation_dojo.py --suite oracle
    python3 tools/mutation_dojo.py --suite frozen
    python3 tools/mutation_dojo.py --suite shipped --scope all
    python3 tools/mutation_dojo.py --equivalence Netzwerk:wlan
    python3 tools/mutation_dojo.py --equivalence alle
    python3 tools/mutation_dojo.py --bruecke
    python3 tools/mutation_dojo.py --tests tests/test_triage_oracle.py

Mutantenklasse: **ein Keyword aus einer Liste löschen**. Warum diese und
nicht `<` -> `<=` wie im Lehrbuch? Das Verhalten von src/triage.py steckt in
*Daten* (zwei dicts), nicht in Verzweigungen. Operator-Mutationen finden dort
fast nichts.

Dieses Werkzeug enthält **keine eigenen Tests**. Jede Suite führt die echten
Dateien unter tests/ aus. `--suite oracle` und `--suite frozen` messen also
genau das, was ihr in tests/test_triage_oracle.py schreibt. Ein Werkzeug, das
seine eigene Erwartung mitbringt, wäre in einem Lab über Orakel eine
schlechte Pointe.

Der Mutant wird **im Speicher** gesetzt: Ein Context-Manager entfernt den
dict-Eintrag und setzt ihn beim Verlassen zurück, auch nach einer Exception.
Es wird **keine Datei geschrieben**. Ein Abbruch mitten im Lauf kann den
Arbeitsbaum also nicht verändern.

Die Testdatei wird **pro Mutant frisch geladen**, und zwar erst, wenn der
Mutant schon gesetzt ist. Dadurch sieht auch Code auf Modulebene der
Testdatei den Mutanten, zum Beispiel eine Ableitung wie
`FROZEN = {k: tuple(v) for k, v in CATEGORY_KEYWORDS.items()}`. Das Ergebnis
ist dasselbe wie bei einer echten Änderung in src/triage.py: Eine abgeleitete
Erwartung wandert mit. Nicht neu geladen werden andere Module, die beim
Import ableiten (etwa `CATEGORIES` in src/summarize.py). Keine der gemessenen
Testdateien braucht sie.
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
# Genug pytest für dieses Lab: Modul laden, alle test_*-Funktionen aufrufen,
# AssertionError heißt rot. Mehr braucht keine der Dateien, die der Dojo
# ausführt. Sie nutzen keine Fixtures, kein parametrize und kein conftest.
# ---------------------------------------------------------------------------

TEST_TRIAGE = REPO / "tests" / "test_triage.py"
TEST_ORACLE = REPO / "tests" / "test_triage_oracle.py"
TEST_SPEC = REPO / "tests" / "test_openapi_spec.py"


def load_test_module(path: Path) -> ModuleType:
    """Lädt eine Testdatei als Modul, ohne pytest und ohne Installation."""
    spec = importlib.util.spec_from_file_location(f"vl09_{path.stem}", path)
    if spec is None or spec.loader is None:  # nur bei kaputtem Pfad erreichbar
        raise ImportError(f"Testdatei nicht als Modul ladbar: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_names(module: ModuleType) -> list[str]:
    """Alle test_*-Funktionen in Definitionsreihenfolge."""
    return [name for name, value in vars(module).items()
            if name.startswith("test_") and callable(value)]


def run_tests(module: ModuleType, names: list[str] | None = None) -> list[str]:
    """Führt Testfunktionen aus und liefert die Namen der fehlgeschlagenen."""
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
# Drei Suiten mit einem einzigen Unterschied: **woher die Erwartung kommt.**
# Genau das ist das Thema des Labs.
#
#   shipped  tests/test_triage.py         5 handgeschriebene Fälle
#   oracle   tests/test_triage_oracle.py  TODO 1: Erwartung aus dem Prüfling
#   frozen   tests/test_triage_oracle.py  TODO 2: Erwartung eingefroren
# ---------------------------------------------------------------------------

STUDENT_SUITES = {
    "oracle": ("test_jedes_keyword_trifft_seine_kategorie", "TODO 1"),
    "frozen": ("test_jedes_keyword_trifft_seine_kategorie_eingefroren", "TODO 2"),
}
SUITE_NAMES = ("shipped", "oracle", "frozen")


def _ist_docstring(stmt: ast.stmt) -> bool:
    return (isinstance(stmt, ast.Expr)
            and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str))


def _leerer_rumpf(node: ast.FunctionDef) -> bool:
    """True, wenn die Funktion nur aus Docstring, `pass` oder `...` besteht."""
    body = [stmt for stmt in node.body if not _ist_docstring(stmt)]
    return all(isinstance(stmt, ast.Pass)
               or (isinstance(stmt, ast.Expr)
                   and isinstance(stmt.value, ast.Constant)
                   and stmt.value.value is Ellipsis)
               for stmt in body)


def leerer_test(pfad: Path, fn_name: str) -> bool:
    """Steht die Testfunktion im Quelltext noch leer da (`...`, `pass`)?

    Das wird statisch geprüft, nicht durch Ausführen. Ein leerer Test BESTEHT
    und lässt sich am Ergebnis nicht von einem fertigen unterscheiden. Ein
    Score auf einem leeren Test wäre deshalb die nächste Orakel-Falle: 0/34,
    und die Zahl sähe aus wie ein Messergebnis.
    """
    tree = ast.parse(pfad.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == fn_name:
            return _leerer_rumpf(node)
    return True  # gar nicht vorhanden


def suite_aus_datei(pfad: Path, namen: list[str] | None = None):
    """Eine Suite als Funktion: Jeder Aufruf lädt die Testdatei FRISCH.

    Rückgabe der Suite: Namen der fehlgeschlagenen Tests (leer heißt grün).
    Weil erst beim Aufruf geladen wird, läuft der Modul-Code der Testdatei
    innerhalb von `with mutant(...)`. Eine Erwartung, die dort aus
    CATEGORY_KEYWORDS abgeleitet wird, sieht also den Mutanten und wandert
    mit, genau wie bei einer echten Änderung im Quelltext.
    """
    def suite() -> list[str]:
        return run_tests(load_test_module(pfad), namen)
    return suite


def build_suite(name: str, oracle_pfad: Path = TEST_ORACLE):
    """Liefert (suite_callable, Fehlermeldung). Genau eines von beiden ist None."""
    if name == "shipped":
        return suite_aus_datei(TEST_TRIAGE), None

    fn_name, todo = STUDENT_SUITES[name]
    if leerer_test(oracle_pfad, fn_name):
        return None, (
            f"{todo} ist noch nicht gefüllt: {fn_name}()\n"
            f"  in tests/test_triage_oracle.py hat einen leeren Rumpf.\n"
            f"  Ein Test ohne Assertion ist immer grün und eliminiert keinen Mutanten.\n"
            f"  Der Score wäre 0 und sähe trotzdem aus wie ein Messergebnis."
        )

    # Einmal ohne Mutant laden, nur um FROZEN zu prüfen. Gemessen wird später
    # mit frisch geladenen Modulen (suite_aus_datei).
    if name == "frozen" and not getattr(load_test_module(oracle_pfad), "FROZEN", None):
        return None, (
            "FROZEN ist leer (oder fehlt) in tests/test_triage_oracle.py.\n"
            "  TODO 2 trägt die eingefrorene Kopie der Tabelle dort ein.\n"
            "  Eine Schleife über ein leeres dict prüft null Keywords."
        )
    return suite_aus_datei(oracle_pfad, [fn_name]), None


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
    """Mutanten für `--scope category` (34) oder `--scope all` (45)."""
    return category_mutants() if scope == "category" else all_mutants()


def table_for(row: str) -> dict[str, list[str]]:
    """Die Keyword-Tabelle, in der die Zeile `row` steht."""
    return (triage.CATEGORY_KEYWORDS if row in triage.CATEGORY_KEYWORDS
            else triage.PRIORITY_KEYWORDS)


def table_name(row: str) -> str:
    return ("CATEGORY_KEYWORDS" if row in triage.CATEGORY_KEYWORDS
            else "PRIORITY_KEYWORDS")


class mutant:
    """Context-Manager: entfernt ein Keyword im Speicher und setzt es zurück."""

    def __init__(self, row: str, kw: str):
        self.row, self.kw = row, kw
        self.table = table_for(row)
        self.original: list[str] = []

    def __enter__(self):
        self.original = list(self.table[self.row])
        self.table[self.row] = [k for k in self.original if k != self.kw]
        return self

    def __exit__(self, *exc):
        self.table[self.row] = self.original
        return False


class key_mutant:
    """Context-Manager: entfernt eine ganze Kategorie-ZEILE (für `--bruecke`).

    Gelöscht wird nicht ein Keyword, sondern der Schlüssel. Die Reihenfolge der
    Zeilen ist Teil des Verhaltens (first match wins). Deshalb wird das ganze
    dict gesichert und in Originalreihenfolge zurückgeschrieben.
    """

    def __init__(self, row: str):
        self.row = row
        self.snapshot: dict[str, list[str]] = {}

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

# Zusätzliche Eingaben, die gezielt Teilstring-Effekte provozieren
# ("lan" steckt in "wlan", "Planung", "Balance", "Atlantik").
ZUSATZ_KANDIDATEN = ["wlan-portal", "Planung", "Balance", "Atlantik", "rechnung"]


def find_distinguishing_input(row: str, kw: str, extra: list[str] | None = None):
    """Sucht eine Eingabe, für die Original und Mutant sich unterscheiden.

    Verglichen wird das ganze Ergebnis (Kategorie, Priorität). Ein Mutant in
    PRIORITY_KEYWORDS ändert nur die Priorität, deshalb reicht die Kategorie
    allein nicht.

    Durchsucht werden: leerer Text, jedes einzelne Keyword, jedes Keyword-Paar
    und optionale Zusatzkandidaten. Findet die Suche **nichts**, ist das ein
    Äquivalenz-*Indiz*, kein Beweis. Den Beweis liefert ein Argument (siehe
    Lab: `wlan` gegen `lan`).

    Rückgabe: (Eingabe, Ergebnis Original, Ergebnis Mutant, Anzahl Kandidaten).
    Die ersten drei sind None, wenn nichts gefunden wurde.
    """
    keywords = [keyword for _, keyword in all_mutants()]
    candidates = [""] + keywords + list(extra or [])
    candidates += [f"{a} {b}" for a, b in itertools.combinations(keywords, 2)]

    def classify(text: str) -> tuple[str, str]:
        return triage.classify_and_prioritize({"betreff": "", "text": text})

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

def messen(suite, mutants: list[tuple[str, str]]) -> tuple[list[str], list[str]]:
    """Führt die Suite unter jedem Mutanten aus. Rückgabe: (eliminiert, überlebt).

    Die Suite lädt ihre Testdatei bei jedem Aufruf neu (suite_aus_datei), also
    erst innerhalb des Mutanten.
    """
    killed, survived = [], []
    for row, kw in mutants:
        with mutant(row, kw):
            fails = suite()
        (killed if fails else survived).append(f"{row}/{kw}")
    return killed, survived


def run_suite(name: str, scope: str) -> int:
    """Misst den Mutation Score einer Suite. Rückgabe: Exit-Code."""
    suite, fehler = build_suite(name)
    if suite is None:
        print(f"Suite '{name}' kann noch nicht gemessen werden:")
        print(f"  {fehler}")
        return 1

    mutants = mutants_for(scope)
    baseline = suite()  # frisch geladen, ohne Mutant
    if baseline:
        print(f"WARNUNG: Suite '{name}' ist schon auf dem INTAKTEN Modul rot: {baseline}")
        print("         Ein Mutation Score ist damit bedeutungslos. Erst reparieren.")
        return 1

    killed, survived = messen(suite, mutants)

    total = len(mutants)
    print(f"Suite '{name}' · Mutantenklasse: ein Keyword löschen (Scope: {scope})")
    print("  auf dem intakten Modul : grün")
    print(f"  Mutanten               : {total}")
    print(f"  eliminiert             : {len(killed)}")
    print(f"  überlebt               : {len(survived)}")
    print(f"  Mutation Score (roh)   : {len(killed)}/{total} = {len(killed)/total:.3f}")
    if killed:
        print(f"  eliminiert im Detail   : {', '.join(sorted(killed))}")
    print()
    print("  Hinweis: 'roh' heißt OHNE Abzug äquivalenter Mutanten. Wie viele es gibt")
    print("           und warum der Abzug den Score VERBESSERT: --equivalence alle")
    return 0


def _ergebnis(paar: tuple[str, str]) -> str:
    return f"{paar[0]}/{paar[1]}"


def cmd_equivalence(target: str) -> int:
    """Sucht für EINEN Mutanten eine unterscheidende Eingabe."""
    row, _, kw = target.partition(":")
    if not kw:
        print("Format: --equivalence Zeile:keyword    z. B. Netzwerk:wlan")
        print("        --equivalence alle             alle Mutanten des Scopes")
        return 2
    table = table_for(row)
    if row not in table or kw not in table[row]:
        print(f"'{kw}' steht nicht in Zeile '{row}'.")
        return 2

    cand, before, after, n = find_distinguishing_input(row, kw, ZUSATZ_KANDIDATEN)
    print(f"Äquivalenz-Suche für {row}/{kw}   ({n} Kandidaten geprüft)")
    if cand is None:
        print(f"  Die Suche über {n} Kandidaten fand keine unterscheidende Eingabe.")
        print("  -> Äquivalenz-KANDIDAT. Beweisen müsst ihr es mit einem Argument")
        print("     (siehe Lab: 'wlan' gegen 'lan'). Erst dann gehört er aus dem Nenner.")
    else:
        print(f"  unterscheidende Eingabe: {cand!r}")
        print(f"    Original -> {_ergebnis(before)}    Mutant -> {_ergebnis(after)}")
        print("  -> Der Mutant IST eliminierbar. Wenn die Suite ihn nicht eliminiert, ist")
        print("     das ein Mangel der Suite, kein Naturgesetz.")
    return 0


def cmd_equivalence_scan(scope: str) -> int:
    """Sucht für ALLE Mutanten des Scopes und listet die Äquivalenz-Kandidaten."""
    mutants = mutants_for(scope)
    kandidaten, n = [], 0
    for row, kw in mutants:
        cand, _, _, n = find_distinguishing_input(row, kw, ZUSATZ_KANDIDATEN)
        if cand is None:
            kandidaten.append(f"{row}/{kw}")
    print(f"Äquivalenz-Suche für alle {len(mutants)} Mutanten (Scope: {scope}), "
          f"je {n} Kandidaten")
    print(f"  ohne unterscheidende Eingabe : {len(kandidaten)}")
    for name in kandidaten:
        print(f"    {name}")
    print()
    print("  Das sind Kandidaten, keine Beweise. Das Argument liefert ihr selbst:")
    print("  Warum kann KEINE Eingabe den Unterschied zeigen? (Lab: 'wlan' und 'Software')")
    return 0


def cmd_list(scope: str) -> int:
    mutants = mutants_for(scope)
    print(f"Mutanten (Index: Zeile/Keyword), nackte Diffs ohne Beschreibung"
          f"   [--scope {scope}]")
    for i, (row, kw) in enumerate(mutants, 1):
        print(f"  M{i:02d}  {table_name(row)}['{row}'] -= '{kw}'")
    print(f"\n{len(mutants)} Mutanten. Wie viele überleben die Suite? Erst schätzen.")
    if scope == "category":
        print("(Nur die Kategorie-Keywords. Mit --scope all kommen die "
              "Prioritäts-Keywords dazu.)")
    return 0


def cmd_tests(pfad: Path) -> int:
    """Eine Testdatei einmal laufen lassen, als Ersatz für `pytest datei.py`.

    Ohne Mutant, ohne Score: nur grün, rot oder leer. Damit lässt sich auch
    TODO 3 ausprobieren, das in keiner der drei Suiten steckt.
    """
    if not pfad.is_absolute():
        pfad = REPO / pfad
    if not pfad.exists():
        print(f"Datei nicht gefunden: {pfad}")
        return 2
    module = load_test_module(pfad)
    alle = test_names(module)
    fails = run_tests(module)
    leer = [n for n in alle if leerer_test(pfad, n)]
    print(f"{pfad.relative_to(REPO)}: {len(alle) - len(fails) - len(leer)}/{len(alle)} "
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
        print("  LEER heißt: Die Funktion hat keinen Rumpf. pytest meldet sie als")
        print("  'passed', sie sagt aber nichts. Am Ergebnis allein ist das nicht zu sehen.")
    return 1 if fails else 0


def cmd_bruecke() -> int:
    """Brücke zu Teil 2: nicht ein Keyword löschen, sondern den SCHLÜSSEL 'Software'.

    Zeigt ohne pytest, was das Lab behauptet: Die Unit-Tests bleiben grün, der
    Spec-Test wird rot. Der Unterschied ist nicht die Sorgfalt der Tests,
    sondern der Ort ihrer Erwartung.
    """
    dateien = [TEST_TRIAGE, TEST_SPEC]

    def bericht(titel: str) -> None:
        print(f"  {titel}")
        for pfad in dateien:
            name = pfad.relative_to(REPO)
            mod = load_test_module(pfad)  # frisch, damit auch Modul-Code den Mutanten sieht
            alle = test_names(mod)
            fails = run_tests(mod)
            status = "grün" if not fails else "ROT"
            print(f"    {str(name):32s} {len(alle) - len(fails)}/{len(alle)} {status}")
            for f in fails:
                print(f"      fehlgeschlagen: {f}")

    print("Brücke zu Teil 2 · Mutant: der SCHLÜSSEL 'Software' fällt aus "
          "CATEGORY_KEYWORDS.")
    print("(im Speicher, keine Datei wird verändert)")
    print()
    bericht("vorher, intaktes Modul:")
    print()
    with key_mutant("Software"):
        bericht("nachher, mit Mutant:")
        kategorien_mit_mutant = list(triage.CATEGORY_KEYWORDS)
    print()
    print("  DEFAULT_CATEGORY ist weiterhin 'Software'. Deshalb liefert die Triage")
    print("  für jeden Text dasselbe wie vorher, und die Unit-Tests merken nichts.")
    print("  Der Spec-Test vergleicht das Kategorie-Enum aus api/openapi.yaml mit")
    print("  CATEGORY_KEYWORDS: eine Erwartung AUSSERHALB des Prüflings. Nur sie")
    print("  sieht den Mutanten.")
    print()
    print("  Äquivalent ist der Mutant nur für den Rückgabewert der Triage. Wer die")
    print("  Liste der Kategorien liest, sieht ihn sofort:")
    print(f"    list(CATEGORY_KEYWORDS) = {kategorien_mit_mutant}")
    print("  Genau diese Liste bietet src/summarize.py dem LLM als Kategorien an, und")
    print("  api/app.py bricht beim Import ab (Zusicherung gegen KategorieEnum).")
    print("  Äquivalenz gilt immer relativ zu dem, was ein Prüfer beobachtet.")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--suite", choices=SUITE_NAMES, help="Suite messen")
    p.add_argument("--scope", choices=["category", "all"], default="category",
                   help="nur Kategorie-Keywords (34) oder auch Priorität (45)")
    p.add_argument("--equivalence", metavar="Zeile:keyword|alle",
                   help="unterscheidende Eingabe für einen Mutanten suchen "
                        "('alle': für jeden Mutanten des Scopes)")
    p.add_argument("--list", action="store_true", help="Mutanten auflisten")
    p.add_argument("--bruecke", action="store_true",
                   help="Schlüssel 'Software' löschen und beide Testdateien laufen lassen")
    p.add_argument("--tests", metavar="DATEI",
                   help="eine Testdatei einmal laufen lassen (ohne pytest, ohne Mutant)")
    args = p.parse_args()

    if args.tests:
        return cmd_tests(Path(args.tests))
    if args.list:
        return cmd_list(args.scope)
    if args.equivalence == "alle":
        return cmd_equivalence_scan(args.scope)
    if args.equivalence:
        return cmd_equivalence(args.equivalence)
    if args.bruecke:
        return cmd_bruecke()
    if args.suite:
        return run_suite(args.suite, args.scope)
    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
