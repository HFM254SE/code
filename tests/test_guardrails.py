"""Tests für die Guardrails aus VL 6 — komplett offline, kein LLM nötig.

Zwei Seiten derselben Medaille:
  1. Erkennungsrate:    bekannte Angriffe (eval/injections.jsonl) anschlagen?
  2. False-Positive-Rate: echte Tickets dürfen NICHT anschlagen (außer T-1030).

Ein Scanner, der alles blockt, ist genauso nutzlos wie einer, der nichts blockt.
"""

import json
from pathlib import Path

from src.guardrails import filter_output, scan_text, scan_ticket

ROOT = Path(__file__).resolve().parent.parent


def _load_injections() -> list[dict]:
    path = ROOT / "eval" / "injections.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_tickets() -> list[dict]:
    return json.loads((ROOT / "data" / "tickets.json").read_text(encoding="utf-8"))


def test_bekannte_angriffe_werden_erkannt():
    for attack in _load_injections():
        if attack["erwartet_erkannt"]:
            assert scan_text(attack["text"]), f"{attack['id']} ({attack['typ']}) wurde nicht erkannt"


def test_grenzen_des_scanners_sind_dokumentiert():
    # Paraphrasen und Fremdsprachen rutschen durch — das ist der Punkt der
    # Vorlesung: Pattern-Matching ist eine Schicht, keine Lösung. Schlägt
    # dieser Test fehl, hat jemand die Patterns erweitert: dann auch
    # eval/injections.jsonl anpassen.
    for attack in _load_injections():
        if not attack["erwartet_erkannt"]:
            assert not scan_text(attack["text"]), (
                f"{attack['id']} ({attack['typ']}) wird jetzt erkannt — "
                "erwartet_erkannt in injections.jsonl aktualisieren"
            )


def test_keine_false_positives_auf_echten_tickets():
    for ticket in _load_tickets():
        findings = scan_ticket(ticket)
        if ticket["id"] == "T-1030":
            assert "instruction_override" in findings, "T-1030 muss erkannt werden"
        else:
            assert not findings, f"False Positive bei {ticket['id']}: {findings}"


def test_output_filter_maskiert_pii():
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
    text = "Der Drucker im 3. OG ist defekt und braucht neuen Toner."
    assert filter_output(text) == text
