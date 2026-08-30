"""Konformitäts-Gate: prüft eine Implementierung gegen api/openapi.yaml.

    python3 tools/spec_gate.py api/app.py              # Referenz  -> soll 0 Befunde
    python3 tools/spec_gate.py api/drifted_server.py   # Drift     -> soll >=5 Befunde

Kein Server, kein Import des Prüflings, keine Abhängigkeiten: die
Implementierung wird mit `ast` **statisch** gelesen. Ein kaputter oder
bösartiger Server kann dieses Gate also nicht beeinflussen.

Zwei-Seiten-Kriterium — beides muss gelten:

    rot  auf api/drifted_server.py    (sonst prüft das Gate nichts)
    grün auf api/app.py               (sonst prüft es das Falsche)

Ein Gate, das immer rot ist, ist von einem funktionierenden Gate nicht zu
unterscheiden. Ein Gate, das immer grün ist, auch nicht.

Dieses Gate ist FERTIG — im Lab benutzt ihr es als Prüfwerkzeug. Lesenswert
sind trotzdem zwei Entscheidungen darin: die Aufrufverfolgung in
`_raised_status_codes()` (warum app.py grün ist, obwohl der 404 in
`_require()` steckt) und `FRAMEWORK_CODES` (welche Statuscodes der Anwendung
gehören und welche dem Framework). Ein Gate ist nie neutral.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools import specyaml  # noqa: E402

SPEC_PATH = REPO / "api" / "openapi.yaml"


# ---------------------------------------------------------------------------
# Befunde
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Befund:
    art: str          # ROUTE | EXTRA | STATUS | ERRCODE | QPARAM | SCHEMA
    ort: str          # "GET /tickets"
    text: str

    def __str__(self) -> str:
        return f"{self.art:8s} {self.ort:38s} {self.text}"


# ---------------------------------------------------------------------------
# Spec-Modell (fertig)
# ---------------------------------------------------------------------------

def spec_model() -> dict:
    """Liest aus der Spec, was dieses Gate vergleichen kann."""
    spec = specyaml.load(SPEC_PATH)
    ops: dict[tuple[str, str], dict] = {}
    for path, methods in spec["paths"].items():
        for method, op in methods.items():
            codes = {int(c) for c in op.get("responses", {}) if str(c).isdigit()}
            qparams = {p["name"] for p in op.get("parameters", [])
                       if p.get("in") == "query"}
            ops[(method.upper(), path)] = {
                "codes": codes,
                "success": min(c for c in codes if c < 300) if codes else None,
                "qparams": qparams,
                "response_schema": _response_schema_name(op),
            }
    return {"ops": ops, "schemas": spec.get("components", {}).get("schemas", {})}


def _response_schema_name(op: dict) -> str | None:
    """Name des Response-Schemas der Erfolgsantwort, falls per $ref benannt."""
    for code, body in op.get("responses", {}).items():
        if not (str(code).isdigit() and int(code) < 300):
            continue
        schema = (body.get("content", {})
                      .get("application/json", {})
                      .get("schema", {}))
        ref = schema.get("$ref") if isinstance(schema, dict) else None
        if isinstance(ref, str):
            return ref.rsplit("/", 1)[-1]
    return None


# ---------------------------------------------------------------------------
# Implementierungs-Modell (fertig)
# ---------------------------------------------------------------------------

HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def impl_model(pyfile: Path) -> dict:
    """Liest Routen, Statuscodes, Query-Parameter und Response-Modelle per ast."""
    tree = ast.parse(pyfile.read_text(encoding="utf-8"))
    functions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    classes = {n.name: n for n in tree.body if isinstance(n, ast.ClassDef)}

    ops: dict[tuple[str, str], dict] = {}
    for node in tree.body:
        if not isinstance(node, ast.FunctionDef):
            continue
        for deco in node.decorator_list:
            route = _route_from_decorator(deco)
            if route is None:
                continue
            method, path, status, response_model = route
            ops[(method, path)] = {
                "status": status,
                "response_model": response_model,
                "qparams": _query_params(node),
                "raised": _raised_status_codes(node, functions, set()),
                "lineno": node.lineno,
            }
    return {"ops": ops, "classes": classes, "functions": functions}


def _route_from_decorator(deco: ast.expr) -> tuple[str, str, int | None, str | None] | None:
    """(METHODE, Pfad, status_code, response_model) aus `@app.get("/x", ...)`.

    None, sobald der Dekorator keine Route ist — das ist der Normalfall, denn
    `decorator_list` enthält auch alles andere (@dataclass, @field_validator).
    """
    if not isinstance(deco, ast.Call) or not isinstance(deco.func, ast.Attribute):
        return None
    method = deco.func.attr.lower()
    if method not in HTTP_METHODS:
        return None
    if not deco.args:
        return None
    # Erst binden, dann prüfen: der Pfad muss ein String-Literal sein. Ein
    # `@app.get(PFAD)` mit Variable ist für ein statisches Gate nicht lesbar.
    pfad_knoten = deco.args[0]
    if not isinstance(pfad_knoten, ast.Constant) or not isinstance(pfad_knoten.value, str):
        return None
    status: int | None = None
    response_model: str | None = None
    for kw in deco.keywords:
        # `ast.Constant.value` ist alles, was ein Literal sein kann (str, None,
        # Ellipsis ...). Ein Statuscode ist davon nur der int-Fall.
        if (kw.arg == "status_code" and isinstance(kw.value, ast.Constant)
                and isinstance(kw.value.value, int)):
            status = kw.value.value
        if kw.arg == "response_model":
            response_model = ast.unparse(kw.value)
    return method.upper(), pfad_knoten.value, status, response_model


NICHT_QUERY = {"request", "self"}


def _query_params(fn: ast.FunctionDef) -> set[str]:
    """Query-Parameter = Funktionsargumente, die nicht im Pfad stehen.

    `request: Request` ist ein Framework-Objekt, kein Query-Parameter — es
    steht deshalb in NICHT_QUERY. Genau solche Ausnahmen sind der Grund,
    warum ein naives Gate auf dem *korrekten* Server anschlägt.
    """
    path_params: set[str] = set()
    for deco in fn.decorator_list:
        route = _route_from_decorator(deco)
        if route:
            path_params |= set(_path_placeholders(route[1]))
    out = set()
    for arg in fn.args.args:
        if arg.arg in path_params or arg.arg in NICHT_QUERY:
            continue
        annot = ast.unparse(arg.annotation) if arg.annotation else ""
        if annot.endswith("Request"):
            continue
        if _is_body_model(annot):
            continue
        out.add(arg.arg)
    return out


def _is_body_model(annot: str) -> bool:
    """Pydantic-Body-Modelle sind keine Query-Parameter."""
    return annot in {"TicketEingabe", "Eskalation"}


def _path_placeholders(path: str) -> list[str]:
    import re
    return re.findall(r"\{([^}]+)\}", path)


def _raised_status_codes(fn: ast.FunctionDef, functions: dict, seen: set) -> set[int]:
    """Alle Statuscodes, die in dieser Funktion ODER in von ihr gerufenen
    modul-eigenen Hilfsfunktionen erhoben werden.

    Die Rekursion ist der Grund, warum das Gate `api/app.py` grün bekommt:
    dort wirft `_require()` den 404, nicht der Handler selbst. Ohne
    Aufrufverfolgung würde das Gate den KORREKTEN Server anschwärzen.
    """
    if fn.name in seen:
        return set()
    seen = seen | {fn.name}
    codes: set[int] = set()
    for node in ast.walk(fn):
        if isinstance(node, ast.Call):
            target = getattr(node.func, "id", None)
            if isinstance(node.func, ast.Name) and target == "HTTPException":
                for kw in node.keywords:
                    if (kw.arg == "status_code" and isinstance(kw.value, ast.Constant)
                            and isinstance(kw.value.value, int)):
                        codes.add(kw.value.value)
            elif isinstance(node.func, ast.Name) and target in functions:
                codes |= _raised_status_codes(functions[target], functions, seen)
    return codes


def response_fields(model_name: str | None, classes: dict) -> set[str] | None:
    """Feldnamen eines Pydantic-Modells, inklusive geerbter Felder."""
    if not model_name or model_name not in classes:
        return None
    fields: set[str] = set()
    node = classes[model_name]
    for base in node.bases:
        if isinstance(base, ast.Name) and base.id in classes:
            inherited = response_fields(base.id, classes)
            if inherited:
                fields |= inherited
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            fields.add(stmt.target.id)
    return fields


# ---------------------------------------------------------------------------
# Entscheidungen & Vergleiche
# ---------------------------------------------------------------------------

# Statuscodes, die FastAPI SELBST erzeugt: 400 bei nicht parsbarem Body, 422
# bei Schema-Verletzung. Im Handler steht dafür kein `raise` — sie hier zu
# fordern würde den KORREKTEN Server anschwärzen. Welche Codes die Anwendung
# besitzt und welche das Framework, muss man selbst entscheiden.
FRAMEWORK_CODES = {400, 422}

# Die Response-Felder aus components/schemas — hier VORLÄUFIG fest verdrahtet.
# specyaml löst `$ref` nicht auf, deshalb steht das hier von Hand.
#
# -> Vertiefung: aus spec["schemas"] herleiten und dieses dict löschen.
#    Achtung, dritte Falle: `GET /tickets` liefert ein ARRAY. Sobald ihr
#    `$ref` auflöst, seht ihr auch `items.$ref -> Ticket` — und müsst auf
#    der Implementierungsseite `list[Ticket]` entpacken. Sonst erklärt das
#    Gate wieder den korrekten Server für kaputt.
SPEC_RESPONSE_FIELDS = {
    "Ticket": {"id", "von", "betreff", "text", "erstellt"},
    "TriageErgebnis": {"id", "kategorie", "prioritaet"},
    "EskalationErgebnis": {"id", "status", "grund"},
}


def gate(pyfile: Path) -> list[Befund]:
    """Vergleicht die Implementierung mit der Spec und liefert alle Befunde.

    Sechs Prüfungen:

      1. ROUTE   Jede in der Spec deklarierte (Methode, Pfad)-Kombination
                 existiert in der Implementierung.
      2. EXTRA   Die Implementierung hat keine Route, die die Spec nicht kennt.
      3. STATUS  Der Erfolgs-Statuscode stimmt. Achtung: FastAPI-Default ist
                 200 — steht `status_code=` nicht am Dekorator, ist es 200.
      4. ERRCODE Jeder in der Spec deklarierte Fehlercode >= 400 ist im Handler
                 erreichbar (nutzt `impl["ops"][key]["raised"]`) — außer den
                 FRAMEWORK_CODES, die FastAPI selbst erzeugt.
      5. QPARAM  Die Query-Parameter-Namen stimmen (Spec vs. Implementierung),
                 in beide Richtungen: fehlende UND unspezifizierte.
      6. SCHEMA  Die Feldnamen des Response-Modells stimmen mit
                 SPEC_RESPONSE_FIELDS überein (nutzt `response_fields(...)`).
                 Schemas ohne Eintrag dort werden STUMM übersprungen — ein von
                 Hand gepflegtes Orakel ignoriert, was es nicht kennt.
    """
    spec = spec_model()
    impl = impl_model(pyfile)
    befunde: list[Befund] = []

    for key, soll in spec["ops"].items():
        method, path = key
        ort = f"{method} {path}"
        ist = impl["ops"].get(key)

        # 1 — ROUTE: fehlt die Route ganz? Dann Befund und weiter.
        if ist is None:
            befunde.append(Befund("ROUTE", ort, "in der Implementierung nicht vorhanden"))
            continue

        # 3 — STATUS: Erfolgscode vergleichen (FastAPI-Default ist 200).
        ist_status = ist["status"] if ist["status"] is not None else 200
        if soll["success"] is not None and ist_status != soll["success"]:
            befunde.append(Befund("STATUS", ort,
                                  f"Erfolgscode {ist_status}, Spec verlangt {soll['success']}"))

        # 4 — ERRCODE: nur Codes prüfen, die die ANWENDUNG entscheidet.
        #     400/422 erzeugt FastAPI selbst, ohne `raise` im Handler — sie zu
        #     fordern würde den korrekten Server anschwärzen.
        pflicht = {c for c in soll["codes"] if c >= 400 and c not in FRAMEWORK_CODES}
        fehlend = sorted(pflicht - ist["raised"])
        if fehlend:
            befunde.append(Befund("ERRCODE", ort,
                                  f"Spec-Fehlercode(s) {fehlend} im Handler nicht erreichbar"))

        # 5 — QPARAM: Namen in beide Richtungen vergleichen.
        fehlt = sorted(soll["qparams"] - ist["qparams"])
        extra = sorted(ist["qparams"] - soll["qparams"])
        if fehlt:
            befunde.append(Befund("QPARAM", ort, f"Spec-Parameter {fehlt} fehlen"))
        if extra:
            befunde.append(Befund("QPARAM", ort, f"nicht spezifizierte Parameter {extra}"))

        # 6 — SCHEMA: Response-Feldnamen vergleichen (nur bekannte Schemas).
        soll_name = soll["response_schema"]
        soll_felder = SPEC_RESPONSE_FIELDS.get(soll_name) if soll_name else None
        ist_felder = response_fields(ist["response_model"], impl["classes"])
        if soll_felder and ist_felder and soll_felder != ist_felder:
            befunde.append(Befund("SCHEMA", ort,
                                  f"Response-Felder {sorted(ist_felder)} "
                                  f"!= Spec {sorted(soll_felder)}"))

    # 2 — EXTRA: Routen der Implementierung, die die Spec nicht deklariert.
    for key in impl["ops"]:
        if key not in spec["ops"]:
            befunde.append(Befund("EXTRA", f"{key[0]} {key[1]}",
                                  "nicht in der Spec deklariert"))

    return befunde


# ---------------------------------------------------------------------------
# CLI (fertig)
# ---------------------------------------------------------------------------

def check_two_sided() -> int:
    """Das Abnahme-Kriterium — ohne pytest, nur Standardbibliothek.

        python3 tools/spec_gate.py --check

    Beides muss gelten. Ein Gate, das nur eine Seite erfüllt, ist nicht fertig.
    """
    referenz = gate(REPO / "api" / "app.py")
    drift = gate(REPO / "api" / "drifted_server.py")

    ok_gruen = len(referenz) == 0
    ok_rot = len(drift) >= 5

    print("Abnahme-Kriterium (beide Zeilen müssen OK sein):")
    print(f"  grün auf api/app.py             : {len(referenz)} Befund(e)  "
          f"{'OK' if ok_gruen else 'FEHLT — das Gate prüft das Falsche'}")
    print(f"  rot   auf api/drifted_server.py : {len(drift)} Befund(e)  "
          f"{'OK' if ok_rot else 'FEHLT — das Gate prüft nichts'}")
    if not ok_gruen:
        print("\n  Falsch-Positive auf der Referenz:")
        for b in sorted(referenz, key=lambda x: (x.art, x.ort)):
            print(f"    {b}")
    print()
    print("BESTANDEN" if (ok_gruen and ok_rot) else "NICHT BESTANDEN")
    return 0 if (ok_gruen and ok_rot) else 1


def main() -> int:
    p = argparse.ArgumentParser(description="Spec-Konformitäts-Gate")
    p.add_argument("pyfile", nargs="*", help="zu prüfende Implementierung(en)")
    p.add_argument("--check", action="store_true",
                   help="Zwei-Seiten-Kriterium prüfen (app.py grün, drifted rot)")
    args = p.parse_args()

    if args.check:
        return check_two_sided()
    if not args.pyfile:
        p.print_help()
        return 2

    exit_code = 0
    for name in args.pyfile:
        path = Path(name)
        if not path.is_absolute():
            path = REPO / name
        befunde = gate(path)
        print(f"=== {path.name}: {len(befunde)} Befund(e) ===")
        for b in sorted(befunde, key=lambda x: (x.art, x.ort)):
            print(f"    {b}")
        if befunde:
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
