"""Guardrails für die LeineTech-Ticket-Pipeline (Stand VL 6).

Zwei Verteidigungsschichten aus der Vorlesung:

  Schicht 1 — Input-Scan:    bekannte Injection-Muster im Tickettext erkennen
  Schicht 4 — Output-Filter: PII und Secrets aus LLM-Antworten maskieren

Wichtig (und im Lab messbar): Pattern-Matching ist UNVOLLSTÄNDIG.
Paraphrasen und Fremdsprachen rutschen durch — deshalb ist das hier eine
Schicht von mehreren, keine Lösung. Vgl. eval/injections.jsonl: zwei
Angriffe dort werden absichtlich NICHT erkannt.
"""

import re

# Bekannte Injection-Muster (Deutsch + Englisch). Jedes Muster hat einen
# sprechenden Namen, damit Logs und Reports erklären KÖNNEN, was anschlug.
INJECTION_PATTERNS: dict[str, str] = {
    "instruction_override": (
        r"ignor\w*\s+(?:alle?s?|all|previous|vorherig\w*|bisherig\w*)"
        r"[\s\S]{0,40}?(?:anweisung\w*|instruktion\w*|instruction\w*|regel\w*|rules?)"
    ),
    "forget_rules": r"vergiss\s+(?:alles|alle|deine)",
    "system_tag": r"\[\s*system\s*[:\]]",
    "fake_delimiter": r"#{2,}\s*(?:ende?|end)\s*(?:of\s*)?(?:system|prompt)",
    "prompt_leak": r"system\s*-?\s*prompt",
    "completion_trick": r"(?:anweisung\w*|instruktion\w*|regel\w*)\s+(?:lauten|beginnen)",
    "role_injection": r"du\s+bist\s+(?:jetzt|ab\s+sofort)\s",
    "do_anything_now": r"do\s+anything\s+now",
    # Base64-Heuristik: >=32 zusammenhaengende Base64-Zeichen MIT mindestens
    # einer Ziffer (sonst matchen lange deutsche Komposita).
    "base64_blob": r"(?=[A-Za-z0-9+/=]*\d)[A-Za-z0-9+/]{32,}={0,2}",
    "markdown_exfil": r"!\[[^\]]*\]\(\s*https?://",
}

# PII-/Secret-Muster fuer den Output-Filter (Schicht 4).
OUTPUT_PATTERNS: dict[str, str] = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    "iban": r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,8}\b",
    "api_key": r"\b(?:sk-|pk_|ghp_|Bearer\s+)[A-Za-z0-9_\-]{16,}\b",
}


def scan_text(text: str) -> list[str]:
    """Prüft einen Text gegen alle Injection-Muster.

    Liefert die Namen der angeschlagenen Muster (leer = unauffällig).
    """
    findings = []
    for name, pattern in INJECTION_PATTERNS.items():
        if re.search(pattern, text, re.IGNORECASE):
            findings.append(name)
    return findings


def scan_ticket(ticket: dict) -> list[str]:
    """Prüft Betreff + Text eines Tickets auf Injection-Muster."""
    return scan_text(f"{ticket.get('betreff', '')}\n{ticket.get('text', '')}")


def filter_output(response: str) -> str:
    """Maskiert PII und Secrets in einer LLM-Antwort (Schicht 4).

    LLM-Output ist Untrusted Input für alles, was danach kommt — auch für
    die Anzeige. Maskieren statt verwerfen, damit die Antwort nutzbar bleibt.
    """
    for label, pattern in OUTPUT_PATTERNS.items():
        response = re.sub(pattern, f"[{label.upper()} ENTFERNT]", response)
    return response
