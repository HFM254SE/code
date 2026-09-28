"""Tests für die Guardrails aus VL 6. Alle Tests laufen offline, ohne LLM.

Gemessen werden zwei Seiten derselben Medaille:
  1. Erkennungsrate: Schlagen die bekannten Angriffe aus eval/injections.jsonl an?
  2. False-Positive-Rate: Bleiben die echten Tickets unauffällig (außer T-1030)?
Ein Scanner, der alles meldet, ist genauso nutzlos wie einer, der nichts meldet.

Die Tests sammeln erst alle Fehlschläge und melden sie dann gemeinsam.
So seht ihr auf einen Blick, welche Angriffe oder Tickets noch fehlen.

Dieselben Tests gelten für die Musterlösung und für euer Lab-Gerüst.
Die zwei Angriffe mit erwartet_erkannt = false erscheinen als "xfailed":
Sie sind die bewusste Lücke des Scanners.
"""

import json
from pathlib import Path

import pytest

from src.guardrails import filter_output, scan_text, scan_ticket

ROOT = Path(__file__).resolve().parent.parent


def _load_injections() -> list[dict]:
    lines = (ROOT / "eval" / "injections.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _load_tickets() -> list[dict]:
    return json.loads((ROOT / "data" / "tickets.json").read_text(encoding="utf-8"))


BEWUSSTE_LUECKEN = [a for a in _load_injections() if not a["erwartet_erkannt"]]


# --- Schicht 1: Input-Scan ------------------------------------------------


def test_bekannte_angriffe_werden_erkannt():
    """Alle Angriffe mit erwartet_erkannt = true müssen anschlagen."""
    erwartet = [a for a in _load_injections() if a["erwartet_erkannt"]]
    nicht_erkannt = [f"{a['id']} ({a['typ']})" for a in erwartet if not scan_text(a["text"])]
    assert not nicht_erkannt, (
        f"{len(nicht_erkannt)} von {len(erwartet)} Angriffen nicht erkannt: "
        + ", ".join(nicht_erkannt)
    )


@pytest.mark.xfail(
    reason="Bewusste Lücke: Muster erkennen keine Umschreibungen und keine "
    "fremden Sprachen. Das ist der Befund des Labs, kein Bug.",
    strict=False,
)
@pytest.mark.parametrize("angriff", BEWUSSTE_LUECKEN, ids=lambda a: f"{a['id']}-{a['typ']}")
def test_scanner_erkennt_auch_unbekannte_formulierungen(angriff):
    """Erwartet fehlgeschlagen (xfail). Erkennt euer Scanner den Angriff doch,
    meldet pytest "xpassed". Prüft dann, ob euer Muster nur genau diesen Satz trifft."""
    assert scan_text(angriff["text"])


def test_t1030_wird_als_instruction_override_erkannt():
    """Das präparierte Ticket aus VL 1 muss mit dem vereinbarten Namen anschlagen."""
    t1030 = next(t for t in _load_tickets() if t["id"] == "T-1030")
    assert "instruction_override" in scan_ticket(t1030), "T-1030 muss erkannt werden"


def test_keine_false_positives_auf_echten_tickets():
    """Der entscheidende Test: Kein harmloses Ticket darf anschlagen."""
    echte_tickets = [t for t in _load_tickets() if t["id"] != "T-1030"]
    befunde = {t["id"]: scan_ticket(t) for t in echte_tickets}
    false_positives = {ticket_id: muster for ticket_id, muster in befunde.items() if muster}
    assert not false_positives, (
        f"{len(false_positives)} von {len(echte_tickets)} echten Tickets schlagen an: "
        f"{false_positives}"
    )


# --- Schicht 3: Output-Filter ---------------------------------------------


def test_output_filter_maskiert_email_und_api_key():
    """Mindestumfang aus TODO 3: E-Mail-Adressen und API-Keys."""
    text = (
        "Die Nutzerin vanessa.koch@leinetech.de meldet das Problem, "
        "API-Key sk-abcdef1234567890abcdef ist betroffen."
    )
    gefiltert = filter_output(text)
    assert "vanessa.koch@leinetech.de" not in gefiltert
    assert "sk-abcdef1234567890abcdef" not in gefiltert
    assert "[EMAIL ENTFERNT]" in gefiltert
    assert "[API_KEY ENTFERNT]" in gefiltert


def test_output_filter_laesst_normalen_text_durch():
    """Auch der Filter darf keine False Positives erzeugen."""
    text = "Der Drucker im 3. OG ist defekt und braucht neuen Toner."
    assert filter_output(text) == text
