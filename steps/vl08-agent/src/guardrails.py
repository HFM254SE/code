"""Guardrails für die LeineTech-Ticket-Pipeline (Stand VL 6).

Zwei der fünf Schichten aus der Vorlesung stecken in diesem Modul:

  Schicht 1, Input-Scan:    bekannte Injection-Muster im Ticket erkennen
  Schicht 3, Output-Filter: PII und Secrets in LLM-Antworten maskieren

Wichtig und im Lab messbar: Pattern-Matching ist UNVOLLSTÄNDIG.
Umschreibungen und fremde Sprachen rutschen durch. Deshalb ist das hier
eine Schicht von mehreren und keine Lösung. In eval/injections.jsonl
sind zwei Angriffe absichtlich als "nicht erkennbar" markiert.

Messen:  python -m src.main scan             (30 echte Tickets)
         python -m src.main scan --angriffe  (Angriffe aus eval/injections.jsonl)
"""

import re

# Schicht 1: bekannte Injection-Muster (Deutsch und Englisch). Jedes Muster
# hat einen sprechenden Namen. So erklären Logs und Reports, was anschlug.
INJECTION_PATTERNS: dict[str, str] = {
    "instruction_override": (
        r"ignor\w*\s+(?:alle?s?|all|previous|vorherig\w*|bisherig\w*)"
        r"[\s\S]{0,40}?(?:anweisung\w*|instruktion\w*|instruction\w*|regel\w*|rules?)"
    ),
    "forget_rules": r"vergiss\s+(?:alles|alle|deine)",
    "system_tag": r"\[\s*system\s*[:\]]",
    "fake_delimiter": r"#{2,}\s*(?:ende?|end)\s*(?:of\s*)?(?:system|prompt)",
    # Gefälschte Datenmarkierung aus src/summarize.py. Ein echtes Ticket
    # enthält diese Zeichenfolgen nie, ein Treffer ist also ein starkes Signal.
    "delimiter_spoofing": r"<<<\s*TICKET|TICKET\s*>>>",
    "prompt_leak": r"system\s*-?\s*prompt",
    "completion_trick": r"(?:anweisung\w*|instruktion\w*|regel\w*)\s+(?:lauten|beginnen)",
    "role_injection": r"du\s+bist\s+(?:jetzt|ab\s+sofort)\s",
    "do_anything_now": r"do\s+anything\s+now",
    # Base64-Heuristik: mindestens 32 zusammenhängende Base64-Zeichen mit
    # mindestens einer Ziffer. Ohne die Ziffer träfe das Muster lange
    # deutsche Komposita.
    "base64_blob": r"(?=[A-Za-z0-9+/=]*\d)[A-Za-z0-9+/]{32,}={0,2}",
    "markdown_exfil": r"!\[[^\]]*\]\(\s*https?://",
}

# Schicht 3: PII- und Secret-Muster für den Output-Filter. Aus dem Namen
# wird das Maskierungs-Label, z. B. "api_key" → "[API_KEY ENTFERNT]".
OUTPUT_PATTERNS: dict[str, str] = {
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    # Länderkürzel, Prüfziffern, 3 bis 7 Vierergruppen und ein kurzer Rest.
    # Ohne den Rest bliebe bei einer deutschen IBAN (22 Zeichen) "00" stehen.
    # Der Rest besteht nur aus Ziffern. Sonst würde ein folgendes kurzes Wort
    # wie "BIC" mitmaskiert.
    "iban": r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){3,7}(?:\s?\d{1,3})?\b",
    "api_key": r"\b(?:sk-|pk_|ghp_|Bearer\s+)[A-Za-z0-9_\-]{16,}\b",
}


def scan_text(text: str) -> list[str]:
    """Prüft einen Text gegen alle Injection-Muster (Schicht 1).

    Liefert die Namen der Muster, die anschlagen. Eine leere Liste heißt
    unauffällig, nicht sicher.
    """
    return [
        name
        for name, pattern in INJECTION_PATTERNS.items()
        if re.search(pattern, text, re.IGNORECASE)
    ]


def scan_ticket(ticket: dict) -> list[str]:
    """Prüft Betreff und Text eines Tickets auf Injection-Muster."""
    return scan_text(f"{ticket.get('betreff', '')}\n{ticket.get('text', '')}")


def filter_output(response: str) -> str:
    """Maskiert PII und Secrets in einer LLM-Antwort (Schicht 3).

    LLM-Output ist Untrusted Input für alles, was danach kommt, auch für die
    Anzeige. Maskieren statt verwerfen: So bleibt die Antwort nutzbar.
    """
    for label, pattern in OUTPUT_PATTERNS.items():
        response = re.sub(pattern, f"[{label.upper()} ENTFERNT]", response)
    return response
