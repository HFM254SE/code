"""Strukturtests für die OpenAPI-Spec — offline, kein Server, keine Installation.

Prüft, dass die Spec self-consistent ist und zur Projektlogik passt (z. B.
dass das Kategorie-Enum mit den Triage-Regeln übereinstimmt).

Früher brauchte diese Datei PyYAML und benutzte `pytest.importorskip` —
ohne PyYAML wurde das Modul also stillschweigend ÜBERSPRUNGEN, und "grün"
hieß dann "nie gelaufen". Jetzt liest sie die Spec mit tools/specyaml.py aus
der Standardbibliothek: kein pip install, und ein Skip kann sich nicht mehr
als Erfolg tarnen.
"""

from pathlib import Path

from src.triage import CATEGORY_KEYWORDS
from tools import specyaml

SPEC_PATH = Path(__file__).resolve().parent.parent / "api" / "openapi.yaml"


def _spec() -> dict:
    return specyaml.load(SPEC_PATH)


def test_alle_erwarteten_pfade_vorhanden():
    paths = _spec()["paths"]
    for expected in [
        "/tickets",
        "/tickets/{ticket_id}",
        "/tickets/{ticket_id}/triage",
        "/tickets/{ticket_id}/escalate",
    ]:
        assert expected in paths, f"Pfad {expected} fehlt in der Spec"


def test_kategorie_enum_passt_zu_triage_regeln():
    """Der Test, der in Teil 1 des Labs die Pointe trägt.

    Er vergleicht zwei unabhängige Repräsentationen derselben Fachlichkeit:
    das Enum in der Spec und die Keyword-Tabelle im Code. Genau deshalb eliminiert
    er einen Mutanten, den keiner der Unit-Tests sieht.
    """
    enum = set(_spec()["components"]["schemas"]["Kategorie"]["enum"])
    assert enum == set(CATEGORY_KEYWORDS), (
        "Kategorie-Enum der Spec weicht von den Triage-Kategorien ab — "
        "klassischer Spec-Drift (VL 9)!"
    )


def test_jede_operation_hat_operationid():
    for path, methods in _spec()["paths"].items():
        for method, op in methods.items():
            assert "operationId" in op, f"{method.upper()} {path} ohne operationId"


def test_limit_hat_grenzen():
    """Die Spec sagt 1..100 — der drifted server lässt die Grenzen weg."""
    params = _spec()["paths"]["/tickets"]["get"]["parameters"]
    limit = next(p for p in params if p["name"] == "limit")
    assert limit["schema"]["minimum"] == 1
    assert limit["schema"]["maximum"] == 100
