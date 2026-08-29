"""Datengetriebene Tests fuer die Triage-Keywords — GERUEST, drei TODOs.

Wird in Teil 1 des Labs gemeinsam gefuellt. Absichtlich eine schlichte
Schleife statt `@pytest.mark.parametrize`: so laeuft dieselbe Datei unter
pytest UND unter tools/mutation_dojo.py, und beide zeigen dieselbe Zahl.

Ausfuehren:
    python3 tools/mutation_dojo.py --suite oracle     # TODO 1
    python3 tools/mutation_dojo.py --suite frozen     # TODO 2
"""

from src.triage import CATEGORY_KEYWORDS, classify_and_prioritize


def _ticket(betreff: str, text: str) -> dict:
    return {"id": "T-9999", "von": "test@leinetech.de", "betreff": betreff,
            "text": text, "erstellt": "2026-05-01"}


# ---------------------------------------------------------------------------
# TODO 1 — Der naheliegende Weg
#
# Schreibt EINEN Test, der ueber alle Keywords laeuft und prueft, dass jedes
# Keyword seiner Kategorie zugeordnet wird. Nutzt dafuer CATEGORY_KEYWORDS —
# also die Tabelle aus dem Modul. Keine Magic Strings, kein Duplikat: die
# Refaktorierung, die man in jedem Review vorschlagen wuerde.
#
# Anforderungen:
#   1. eine Schleife ueber CATEGORY_KEYWORDS.items()
#   2. pro Keyword ein Ticket bauen (betreff = text = Keyword)
#   3. assert kategorie == erwartete Kategorie
#
# NOTIERT DIE ZAHL, die --suite oracle danach ausgibt, BEVOR ihr weiterlest.
# ---------------------------------------------------------------------------

def test_jedes_keyword_trifft_seine_kategorie():
    ...


# ---------------------------------------------------------------------------
# TODO 2 — Derselbe Test, eine Zeile anders
#
# Kopiert den Test von oben. Aendert genau EINE Sache: die Erwartung kommt
# nicht mehr aus dem Modul, sondern aus einer eingefrorenen Kopie der Tabelle,
# die HIER in dieser Datei steht.
#
# Anforderungen:
#   1. FROZEN als dict[str, tuple[str, ...]] hier im Testmodul anlegen
#   2. sonst identische Schleife und identische Assertion
#   3. Zahl aus --suite frozen mit der aus TODO 1 vergleichen
#
# Ja, das durpliziert Daten. Notiert im Kommentar, WARUM das hier richtig ist.
# ---------------------------------------------------------------------------

FROZEN: dict[str, tuple[str, ...]] = {}


def test_jedes_keyword_trifft_seine_kategorie_eingefroren():
    ...


# ---------------------------------------------------------------------------
# TODO 3 — Die ehrliche Grenze
#
# Beide Tests oben setzen betreff UND text auf dasselbe Keyword. Baut einen
# Test, der das Keyword NUR in den Betreff schreibt und den Text leer laesst
# ("kein inhalt"). Was passiert — und was sagt das ueber die Eingabemenge,
# gegen die wir gemessen haben?
# ---------------------------------------------------------------------------

def test_keyword_nur_im_betreff():
    ...
