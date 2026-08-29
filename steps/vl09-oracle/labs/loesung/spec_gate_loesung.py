"""Musterloesung fuer die TODOs in tools/spec_gate.py.

Erst nach dem Lab anschauen. Importiert das gesamte Plumbing aus
tools/spec_gate.py und ersetzt nur `gate()`.

    python3 labs/loesung/spec_gate_loesung.py api/app.py api/drifted_server.py
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from tools.spec_gate import (  # noqa: E402
    FRAMEWORK_CODES,
    SPEC_RESPONSE_FIELDS,
    Befund,
    impl_model,
    response_fields,
    spec_model,
)


def gate(pyfile: Path) -> list[Befund]:
    spec = spec_model()
    impl = impl_model(pyfile)
    befunde: list[Befund] = []

    for key, soll in spec["ops"].items():
        method, path = key
        ort = f"{method} {path}"
        ist = impl["ops"].get(key)

        # TODO 1 — ROUTE
        if ist is None:
            befunde.append(Befund("ROUTE", ort, "in der Implementierung nicht vorhanden"))
            continue

        # TODO 3 — STATUS (FastAPI-Default ist 200)
        ist_status = ist["status"] if ist["status"] is not None else 200
        if soll["success"] is not None and ist_status != soll["success"]:
            befunde.append(Befund("STATUS", ort,
                                  f"Erfolgscode {ist_status}, Spec verlangt {soll['success']}"))

        # TODO 4 — ERRCODE
        # Nur Codes pruefen, die die ANWENDUNG entscheidet. 400 (nicht parsbarer
        # Body) und 422 (Schema-Validierung) erzeugt FastAPI selbst, ohne dass
        # im Handler ein `raise` steht — sie hier zu fordern schwaerzt den
        # korrekten Server an. Genau diese Grenze muss man selbst ziehen.
        pflicht = {c for c in soll["codes"] if c >= 400 and c not in FRAMEWORK_CODES}
        fehlend = sorted(pflicht - ist["raised"])
        if fehlend:
            befunde.append(Befund("ERRCODE", ort,
                                  f"Spec-Fehlercode(s) {fehlend} im Handler nicht erreichbar"))

        # TODO 5 — QPARAM, beide Richtungen
        fehlt = sorted(soll["qparams"] - ist["qparams"])
        extra = sorted(ist["qparams"] - soll["qparams"])
        if fehlt:
            befunde.append(Befund("QPARAM", ort, f"Spec-Parameter {fehlt} fehlen"))
        if extra:
            befunde.append(Befund("QPARAM", ort, f"nicht spezifizierte Parameter {extra}"))

        # TODO 6 — SCHEMA
        soll_name = soll["response_schema"]
        soll_felder = SPEC_RESPONSE_FIELDS.get(soll_name) if soll_name else None
        ist_felder = response_fields(ist["response_model"], impl["classes"])
        if soll_felder and ist_felder and soll_felder != ist_felder:
            befunde.append(Befund("SCHEMA", ort,
                                  f"Response-Felder {sorted(ist_felder)} "
                                  f"!= Spec {sorted(soll_felder)}"))

    # TODO 2 — EXTRA
    for key in impl["ops"]:
        if key not in spec["ops"]:
            befunde.append(Befund("EXTRA", f"{key[0]} {key[1]}",
                                  "nicht in der Spec deklariert"))

    return befunde


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    code = 0
    for name in sys.argv[1:]:
        path = Path(name)
        if not path.is_absolute():
            path = REPO / name
        befunde = gate(path)
        print(f"=== {path.name}: {len(befunde)} Befund(e) ===")
        for b in sorted(befunde, key=lambda x: (x.art, x.ort)):
            print(f"    {b}")
        if befunde:
            code = 1
    return code


if __name__ == "__main__":
    raise SystemExit(main())
