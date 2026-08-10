"""Strukturtests für die OpenAPI-Spec — offline, kein Server nötig.

Prüft, dass die Spec self-consistent ist und zur Projektlogik passt
(z. B. dass die Kategorie-Enums mit den Triage-Regeln übereinstimmen).
Braucht PyYAML (steht in requirements.txt).
"""

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

from src.triage import CATEGORY_KEYWORDS  # noqa: E402

SPEC_PATH = Path(__file__).resolve().parent.parent / "api" / "openapi.yaml"


def _spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


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
    enum = set(_spec()["components"]["schemas"]["Kategorie"]["enum"])
    assert enum == set(CATEGORY_KEYWORDS), (
        "Kategorie-Enum der Spec weicht von den Triage-Kategorien ab — "
        "klassischer Spec-Drift (VL 9)!"
    )


def test_jede_operation_hat_operationid():
    for path, methods in _spec()["paths"].items():
        for method, op in methods.items():
            assert "operationId" in op, f"{method.upper()} {path} ohne operationId"
