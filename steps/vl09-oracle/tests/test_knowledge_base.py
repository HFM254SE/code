"""Tests für die KB-Suche (src/knowledge_base.py), offline und ohne LLM.

Die Suche ist bewusst einfach (Keyword-Überlappung). Diese Tests sichern nur
ab, dass die Lösungsabschnitte vollständig beim Agenten ankommen.
"""

from pathlib import Path

from src.knowledge_base import MAX_SECTION_CHARS, _split_sections, search_knowledge_base
from src.ticket_loader import get_ticket

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"


def _suche_zu_ticket(ticket_id: str) -> list[dict]:
    t = get_ticket(ticket_id, ROOT / "data" / "tickets.json")
    return search_knowledge_base(f"{t['betreff']} {t['text']}", docs_dir=DOCS)


def test_t1006_findet_den_loesungsabschnitt():
    top = _suche_zu_ticket("T-1006")[0]
    assert top["artikel"] == "vpn-zugang"
    assert top["abschnitt"].startswith("Tunnel steht, aber interne Ressourcen")
    assert "nslookup" in top["text"]  # die Lösungsschritte werden nicht abgeschnitten


def test_t1018_findet_die_split_tunneling_policy():
    top = _suche_zu_ticket("T-1018")[0]
    assert (top["artikel"], top["abschnitt"]) == ("vpn-zugang", "Split-Tunneling-Policy")


def test_unterabschnitte_sind_eigene_treffer():
    titel = [t for t, _ in _split_sections((DOCS / "vpn-zugang.md").read_text(encoding="utf-8"))]
    assert "Tunnel steht, aber interne Ressourcen (Laufwerke, DMS, Jira) nicht erreichbar" in titel
    # Die Sammelüberschrift ohne eigenen Text ist kein Treffer.
    assert "Häufige Fehler und Lösungen" not in titel


def test_kein_abschnitt_wird_abgeschnitten():
    for path in sorted(DOCS.glob("*.md")):
        for titel, text in _split_sections(path.read_text(encoding="utf-8")):
            assert len(text) <= MAX_SECTION_CHARS, f"{path.stem} › {titel}: {len(text)} Zeichen"
